#!/usr/bin/env python3
"""cycle9_signed_jaccard.py — l_signed_jaccard를 fitting loss에 추가.

기존 l_topk_jaccard는 top-k 색 집합이 일치하는지만 본다.
l_signed_jaccard는 top-k 관측 색 각각의 confusion DIRECTION(CW/CCW)이
시뮬레이터 예측과 일치하는지를 추가로 패널티한다.

  l_signed_jaccard = mean over c in top3_obs of max(0, -sign_obs[c]*sign_sim[c])
                   = 0  if all directions match
                   = 1  if all directions wrong

  sim_bias[c] = β_s·cos(θ_c−90°) + β_c·cos(θ_c−θ_conf)   [analytic, no LOCO rerun]
  obs_bias[c] = mean_signed_bias from confusion_bias_summary.csv

새 fitting loss:
  l_fit_new = l_topk_jaccard + l_signed_jaccard + 0.2·Tikh

출력:
  results/cycle_filter_refinement/cycle9_signed_jaccard.json
    - per subject/ROI: old optimum vs new optimum (β_s, β_c, l_fit)
    - HC LOO: z_set change with new loss
    - direction match fraction at old/new optimum
"""

import json
import sys
import numpy as np
from pathlib import Path
from scipy.stats import norm

_HERE   = Path(__file__).resolve().parent
_PHASE2 = _HERE.parent.parent
_PROJ   = _PHASE2.parent.parent
sys.path.insert(0, str(_PHASE2 / 'scripts'))
sys.path.insert(0, str(_PROJ  / 'analysis' / 'future_phase1_forward_model' / 'scripts'))

from step1_fit_loco_v2 import load_cvd_loco_target

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
RES_DIR   = _PHASE2 / 'results' / 'cycle_filter_refinement'
BIAS_CSV  = _PHASE2 / 'results' / 'loco_confusion_direction' / 'confusion_bias_summary.csv'
OUT_JSON  = RES_DIR / 'cycle9_signed_jaccard.json'

# ---------------------------------------------------------------------------
# Grid (same as existing Cycle 4 / Cycle 7 landscape)
# ---------------------------------------------------------------------------
_bs = np.arange(0.0, 81.0, 2.0)   # shape (41,)
_bc = np.arange(-60.0, 61.0, 2.0) # shape (61,)
_BS, _BC = np.meshgrid(_bs, _bc, indexing='ij')  # (41, 61)
NORM_GRID = (_BS / 80.0) ** 2 + (_BC / 60.0) ** 2

# ---------------------------------------------------------------------------
# Subjects
# ---------------------------------------------------------------------------
HC_SUBJECTS  = ['01', '02', '03', '04', '05', '06']
CVD_SUBJECTS = ['08', '09']
ALL_SUBJECTS = HC_SUBJECTS + CVD_SUBJECTS

CVD_TYPE  = {'08': 'deutan', '09': 'protan'}
CONF_AXIS = {'deutan': 150.0, 'protan': 16.0}

ROIS = ['V1', 'V2', 'V4']
K    = 3  # same as existing l_topk_jaccard
LAM  = 0.2  # Tikhonov weight, same as existing

COLOR_NAMES = ['red', 'orange', 'yellow', 'green', 'cyan', 'blue', 'purple', 'magenta']
HUE_8 = np.array([0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0])  # stimulus angles

# ---------------------------------------------------------------------------
# Load obs_signed_bias from CSV
# ---------------------------------------------------------------------------
def load_obs_bias_csv(csv_path: Path) -> dict:
    """Return dict[subject][ROI][color_idx] = mean_signed_bias."""
    import csv
    out: dict = {}
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            subj = row['subject'].replace('sub-', '')
            roi  = row['ROI']
            cidx = int(row['true_color'])
            bias = float(row['mean_signed_bias'])
            out.setdefault(subj, {}).setdefault(roi, {})[cidx] = bias
    return out


OBS_BIAS = load_obs_bias_csv(BIAS_CSV)


def get_obs_bias_vec(subj: str, roi: str) -> np.ndarray:
    """Return (8,) obs_signed_bias for subj/roi. NaN if missing."""
    b = np.full(8, np.nan)
    d = OBS_BIAS.get(subj, {}).get(roi, {})
    for cidx, val in d.items():
        b[cidx] = val
    return b


# ---------------------------------------------------------------------------
# Simulator bias: analytic from 2-component model
# ---------------------------------------------------------------------------
def sim_bias_grid(cvd_type: str) -> np.ndarray:
    """Return (41, 61, 8) array of sim_bias[bs_idx, bc_idx, color].

    sim_bias[c] = β_s·cos(θ_c−90°) + β_c·cos(θ_c−θ_conf)
    Uses stimulus hue angles θ_c = [0,45,90,...,315]°.
    This matches cycle8_preimage.py convention (obs_bias is also in stimulus space).
    """
    theta_conf = CONF_AXIS[cvd_type]

    cos_s = np.cos(np.radians(HUE_8 - 90.0))        # (8,)
    cos_c = np.cos(np.radians(HUE_8 - theta_conf))  # (8,)

    # broadcast: BS(41,61,1) * cos_s(1,1,8) + BC(41,61,1) * cos_c(1,1,8)
    sim = (_BS[:, :, None] * cos_s[None, None, :]
           + _BC[:, :, None] * cos_c[None, None, :])  # (41, 61, 8)
    return sim


# Precompute for both families (HC uses deutan by convention)
SIM_BIAS = {
    'deutan': sim_bias_grid('deutan'),
    'protan': sim_bias_grid('protan'),
}


# ---------------------------------------------------------------------------
# l_signed_jaccard per grid point
# ---------------------------------------------------------------------------
MIN_SIM_BIAS = 5.0  # degrees — below this sim_bias is treated as "no prediction"


def compute_l_signed_grid(obs_bias: np.ndarray, vuln_cvd: np.ndarray,
                           cvd_type: str, k: int = K) -> np.ndarray:
    """Return (41, 61) l_signed_jaccard grid.

    For each grid point: penalise direction mismatches for top-k observed colors.
    "No prediction" (|sim_bias| < MIN_SIM_BIAS) is treated as a mismatch —
    this avoids the trivial l_signed=0 at (β_s=0, β_c=0) where sign(0)=0.

    obs_bias : (8,) mean_signed_bias per color for this subj/ROI
    vuln_cvd : (8,) LOCO vulnerability (lower = more confused)
    Returns:  0 = all directions predicted correctly,  1 = all wrong/unpredicted.
    """
    top_k_obs = list(np.argsort(vuln_cvd)[:k])

    sim = SIM_BIAS[cvd_type]  # (41, 61, 8)

    penalties = np.zeros(_BS.shape)  # (41, 61)
    n_valid = 0
    for cidx in top_k_obs:
        if np.isnan(obs_bias[cidx]):
            continue
        n_valid += 1
        sign_obs = np.sign(obs_bias[cidx])   # scalar ±1

        abs_sim  = np.abs(sim[:, :, cidx])   # (41, 61)
        sign_sim = np.sign(sim[:, :, cidx])  # (41, 61)

        # 1 if wrong direction, 1 if |sim|<threshold (no meaningful prediction)
        # "no prediction" treated as mismatch: prevents trivial 0 at (bs=0, bc=0)
        wrong_dir = (sign_obs * sign_sim < 0).astype(float)
        no_pred   = (abs_sim < MIN_SIM_BIAS).astype(float)
        penalties += np.maximum(wrong_dir, no_pred)

    if n_valid == 0:
        return np.zeros(_BS.shape)
    return penalties / n_valid  # [0, 1]


# ---------------------------------------------------------------------------
# Load existing landscape JSON
# ---------------------------------------------------------------------------
def load_landscape(subj: str, roi: str):
    """Return (41, 61) l_topk_jaccard grid or None."""
    p = RES_DIR / f'sub-{subj}_{roi}_landscape.json'
    if not p.exists():
        return None
    with open(p) as f:
        d = json.load(f)
    return np.array(d['l_topk_jaccard'])


# ---------------------------------------------------------------------------
# Optimum extraction
# ---------------------------------------------------------------------------
def find_optimum(loss_grid: np.ndarray) -> dict:
    """Return best (bs, bc, loss) from (41, 61) grid."""
    idx = np.unravel_index(np.argmin(loss_grid), loss_grid.shape)
    return {
        'bs': float(_bs[idx[0]]),
        'bc': float(_bc[idx[1]]),
        'loss': float(loss_grid[idx]),
    }


# ---------------------------------------------------------------------------
# Direction match fraction at a given (bs, bc)
# ---------------------------------------------------------------------------
def direction_match_at(bs: float, bc: float,
                       obs_bias: np.ndarray, vuln_cvd: np.ndarray,
                       cvd_type: str, k: int = K) -> dict:
    """Compute direction agreement stats at a specific grid point."""
    bs_idx = int(round(bs / 2.0))
    bc_idx = int(round((bc + 60.0) / 2.0))
    bs_idx = np.clip(bs_idx, 0, len(_bs) - 1)
    bc_idx = np.clip(bc_idx, 0, len(_bc) - 1)

    sim = SIM_BIAS[cvd_type]
    top_k_obs = np.argsort(vuln_cvd)[:k].tolist()

    matches, mismatches = [], []
    for cidx in top_k_obs:
        if np.isnan(obs_bias[cidx]):
            continue
        so = np.sign(obs_bias[cidx])
        sb = float(sim[bs_idx, bc_idx, cidx])
        match = (so * sb > 0) and (abs(sb) >= MIN_SIM_BIAS)
        info = {'color': COLOR_NAMES[cidx],
                'obs_bias': round(float(obs_bias[cidx]), 1),
                'sim_bias': round(sb, 1),
                'match': bool(match)}
        (matches if match else mismatches).append(info)

    return {
        'n_match': len(matches),
        'n_mismatch': len(mismatches),
        'match_frac': len(matches) / max(1, len(matches) + len(mismatches)),
        'details': matches + mismatches,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    results = {'per_cell': {}, 'hc_loo': {}, 'meta': {}}

    # -----------------------------------------------------------------------
    # Per subject × ROI
    # -----------------------------------------------------------------------
    for subj in ALL_SUBJECTS:
        cvd_type = CVD_TYPE.get(subj, 'deutan')  # HC uses deutan by convention
        results['per_cell'][subj] = {}

        for roi in ROIS:
            topk_grid = load_landscape(subj, roi)
            if topk_grid is None:
                print(f'  MISSING landscape: sub-{subj} {roi}')
                continue

            try:
                vuln_cvd = load_cvd_loco_target(subj, roi)
            except Exception as e:
                print(f'  LOCO load fail sub-{subj} {roi}: {e}')
                continue

            obs_bias = get_obs_bias_vec(subj, roi)

            # Old loss: l_topk + Tikh
            old_loss = topk_grid + LAM * NORM_GRID
            old_opt  = find_optimum(old_loss)

            # l_signed_jaccard grid
            l_signed = compute_l_signed_grid(obs_bias, vuln_cvd, cvd_type)

            # New loss: l_topk + l_signed + Tikh
            new_loss = topk_grid + l_signed + LAM * NORM_GRID
            new_opt  = find_optimum(new_loss)

            # Direction match at old and new optima
            dm_old = direction_match_at(old_opt['bs'], old_opt['bc'],
                                        obs_bias, vuln_cvd, cvd_type)
            dm_new = direction_match_at(new_opt['bs'], new_opt['bc'],
                                        obs_bias, vuln_cvd, cvd_type)

            top3_colors = [COLOR_NAMES[c] for c in np.argsort(vuln_cvd)[:K].tolist()]

            cell = {
                'cvd_type': cvd_type,
                'top3_observed': top3_colors,
                'old_opt': {**old_opt, 'l_signed_at': round(float(l_signed[
                    int(round(old_opt['bs']/2)), int(round((old_opt['bc']+60)/2))]), 3)},
                'new_opt': {**new_opt, 'l_signed_at': round(float(l_signed[
                    int(round(new_opt['bs']/2)), int(round((new_opt['bc']+60)/2))]), 3)},
                'bs_shift': round(new_opt['bs'] - old_opt['bs'], 1),
                'bc_shift': round(new_opt['bc'] - old_opt['bc'], 1),
                'dir_match_old': dm_old,
                'dir_match_new': dm_new,
                # raw grids for HC LOO z_set computation
                '_old_min': float(old_loss.min()),
                '_new_min': float(new_loss.min()),
            }
            results['per_cell'][subj][roi] = cell

            status = 'CVD' if subj in CVD_SUBJECTS else 'HC'
            print(f'sub-{subj} ({status}) {roi}: '
                  f'old→({old_opt["bs"]:.0f},{old_opt["bc"]:.0f}) '
                  f'new→({new_opt["bs"]:.0f},{new_opt["bc"]:.0f})  '
                  f'dir_old={dm_old["match_frac"]:.2f} dir_new={dm_new["match_frac"]:.2f}')

    # -----------------------------------------------------------------------
    # HC LOO z_set comparison: old loss vs new loss
    # -----------------------------------------------------------------------
    print('\n=== HC LOO z_set (FP check: z < -2 = false positive) ===')
    for subj in HC_SUBJECTS:
        results['hc_loo'][subj] = {}
        others = [h for h in HC_SUBJECTS if h != subj]

        for roi in ROIS:
            if roi not in results['per_cell'].get(subj, {}):
                continue
            own_old = results['per_cell'][subj][roi]['_old_min']
            own_new = results['per_cell'][subj][roi]['_new_min']

            pool_old = [results['per_cell'][h][roi]['_old_min']
                        for h in others if roi in results['per_cell'].get(h, {})]
            pool_new = [results['per_cell'][h][roi]['_new_min']
                        for h in others if roi in results['per_cell'].get(h, {})]

            if len(pool_old) < 2:
                continue

            mu_old, sd_old = np.mean(pool_old), np.std(pool_old, ddof=1)
            mu_new, sd_new = np.mean(pool_new), np.std(pool_new, ddof=1)

            z_old = (own_old - mu_old) / sd_old if sd_old > 0 else np.nan
            z_new = (own_new - mu_new) / sd_new if sd_new > 0 else np.nan

            results['hc_loo'][subj][roi] = {
                'z_set_old': round(float(z_old), 3) if np.isfinite(z_old) else None,
                'z_set_new': round(float(z_new), 3) if np.isfinite(z_new) else None,
            }
            fp_old = '** FP' if np.isfinite(z_old) and z_old < -2 else ''
            fp_new = '** FP' if np.isfinite(z_new) and z_new < -2 else ''
            print(f'  sub-{subj} {roi}: z_old={z_old:+.2f}{fp_old}  z_new={z_new:+.2f}{fp_new}')

    # -----------------------------------------------------------------------
    # CVD subjects: z_set vs HC pool
    # -----------------------------------------------------------------------
    print('\n=== CVD z_set vs full HC pool (n=6) ===')
    results['cvd_z_set'] = {}
    for subj in CVD_SUBJECTS:
        results['cvd_z_set'][subj] = {}
        for roi in ROIS:
            if roi not in results['per_cell'].get(subj, {}):
                continue
            own_old = results['per_cell'][subj][roi]['_old_min']
            own_new = results['per_cell'][subj][roi]['_new_min']

            pool_old = [results['per_cell'][h][roi]['_old_min']
                        for h in HC_SUBJECTS if roi in results['per_cell'].get(h, {})]
            pool_new = [results['per_cell'][h][roi]['_new_min']
                        for h in HC_SUBJECTS if roi in results['per_cell'].get(h, {})]

            if len(pool_old) < 2:
                continue

            mu_old, sd_old = np.mean(pool_old), np.std(pool_old, ddof=1)
            mu_new, sd_new = np.mean(pool_new), np.std(pool_new, ddof=1)

            z_old = (own_old - mu_old) / sd_old if sd_old > 0 else np.nan
            z_new = (own_new - mu_new) / sd_new if sd_new > 0 else np.nan

            results['cvd_z_set'][subj][roi] = {
                'z_old': round(float(z_old), 3) if np.isfinite(z_old) else None,
                'z_new': round(float(z_new), 3) if np.isfinite(z_new) else None,
            }
            print(f'  sub-{subj} {roi}: z_old={z_old:.3f}  z_new={z_new:.3f}')

    # -----------------------------------------------------------------------
    # Clean up internal grids before saving
    # -----------------------------------------------------------------------
    for subj in results['per_cell']:
        for roi in results['per_cell'][subj]:
            results['per_cell'][subj][roi].pop('_old_min', None)
            results['per_cell'][subj][roi].pop('_new_min', None)

    results['meta'] = {
        'k': K, 'lam': LAM,
        'grid_bs': _bs.tolist(), 'grid_bc': _bc.tolist(),
        'loss_formula': 'l_topk_jaccard + l_signed_jaccard + 0.2*Tikh',
        'l_signed_formula': 'mean_top3(max(0, -sign_obs[c]*sign_sim[c]))',
        'sim_bias_formula': 'bs*cos(theta_c-90) + bc*cos(theta_c-theta_conf), theta_c=stimulus angles [0,45,...,315]',
        'obs_bias_source': 'confusion_bias_summary.csv (mean_signed_bias per subj/ROI/color)',
    }

    with open(OUT_JSON, 'w') as f:
        json.dump(results, f, indent=2)
    print(f'\nSaved: {OUT_JSON}')


if __name__ == '__main__':
    main()
