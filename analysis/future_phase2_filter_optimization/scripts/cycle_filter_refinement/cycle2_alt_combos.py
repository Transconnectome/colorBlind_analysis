#!/usr/bin/env python3
"""cycle2_alt_combos.py — Plan 04 Cycle 2: 대체 결합 + 부호 보정.

Cycle 1 비판 → 도입 항목:
  (a) Mahalanobis ROI 결합 (HC null covariance 가중)
  (b) V2 부호-flip / 절대값 합 (V2 z direction 문제 해결)
  (c) blend α 확장 (0.0..1.0 step 0.1, 11 점)
  (d) 대체 metric L_rds (ranked-depth signed)
  (e) C1 secondary-min ratio + grid 변동 강건성 metric (best-arg variance)

Reuses cycle1 landscape json files in
  results/cycles/sub-{ID}_{ROI}_landscape.json

Output: results/cycles/cycle2_aggregate.json
"""
import json
import sys
import time
from itertools import combinations
from pathlib import Path
import numpy as np
from scipy.stats import pearsonr

_HERE = Path(__file__).resolve().parent
_PHASE2 = _HERE.parent.parent
_RESULTS = _PHASE2 / 'results' / 'cycles'

ROIS = ['V1', 'V2', 'V4']
HC_SUBS = ['01', '02', '03', '04', '05', '06']
CVD_SUBS = ['08', '09']
SANITY_SUBS = ['10']
ALL_SUBS = HC_SUBS + CVD_SUBS + SANITY_SUBS

# Family info
CVD_TYPE = {'08': 'deutan', '09': 'protan', '10': 'normal'}


def load_landscape(subj, roi):
    p = _RESULTS / f'sub-{subj}_{roi}_landscape.json'
    if not p.exists():
        return None
    with open(p) as f:
        d = json.load(f)
    out = {k: np.array(v, dtype=float) for k, v in d.items()}
    return out


def load_cycle1():
    with open(_RESULTS / 'cycle1_aggregate.json') as f:
        return json.load(f)


# Reconstruct vuln_baseline from cell_results (need these for L_rds)
def get_baseline_vuln(c1, subj, roi):
    cell = c1['cell_results'].get(roi, {}).get(subj)
    if cell is None:
        return None
    return None  # vuln stored only in cycle4_extended jsons


# --------------------------------------------------------------------------
# C1 — uniqueness & sharpness
# --------------------------------------------------------------------------
def secondary_min_ratio(grid_2d, exclusion_radius=4):
    flat = grid_2d.flatten()
    idx_min = int(np.argmin(flat))
    i_min, j_min = np.unravel_index(idx_min, grid_2d.shape)
    mask = np.ones_like(grid_2d, dtype=bool)
    for i in range(max(0, i_min - exclusion_radius),
                   min(grid_2d.shape[0], i_min + exclusion_radius + 1)):
        for j in range(max(0, j_min - exclusion_radius),
                       min(grid_2d.shape[1], j_min + exclusion_radius + 1)):
            mask[i, j] = False
    if mask.sum() == 0 or grid_2d[mask].min() <= 1e-12:
        return 1.0
    return float(grid_2d.min() / grid_2d[mask].min())


def n_global_minima(grid_2d, atol=1e-6):
    """Count grid points equal (within atol) to global min."""
    return int(np.sum(np.abs(grid_2d - grid_2d.min()) <= atol))


def best_arg_pos(grid_2d):
    """(i,j) of best."""
    return np.unravel_index(int(np.argmin(grid_2d)), grid_2d.shape)


def best_arg_centroid(grid_2d, atol=1e-6):
    """Centroid (i,j) over all global minima."""
    mask = np.abs(grid_2d - grid_2d.min()) <= atol
    ii, jj = np.where(mask)
    return float(ii.mean()), float(jj.mean())


# --------------------------------------------------------------------------
# Mahalanobis ROI combination
# --------------------------------------------------------------------------
def mahalanobis_combine(cvd_vec, hc_matrix, ridge=1e-3):
    """Compute Mahalanobis distance of cvd vec from HC null using HC cov.

    Args:
        cvd_vec: (n_roi,) values for one CVD subject
        hc_matrix: (n_hc, n_roi) HC null pool
        ridge: regularization (added to diag if singular)
    Returns:
        (mahal_dist, p_emp_against_HC_distances)
    """
    mu = hc_matrix.mean(axis=0)
    cov = np.cov(hc_matrix, rowvar=False)
    if cov.ndim == 0:
        cov = cov.reshape(1, 1)
    n = cov.shape[0]
    cov_reg = cov + ridge * np.eye(n)
    inv = np.linalg.inv(cov_reg)
    diff = cvd_vec - mu
    d_cvd = float(np.sqrt(diff @ inv @ diff))
    # HC null distances
    hc_dists = []
    for i in range(hc_matrix.shape[0]):
        di = hc_matrix[i] - mu
        hc_dists.append(np.sqrt(di @ inv @ di))
    hc_dists = np.array(hc_dists)
    # one-sided: CVD large = significant
    p = float((np.sum(hc_dists >= d_cvd) + 1) / (len(hc_dists) + 1))
    return d_cvd, hc_dists, p


# --------------------------------------------------------------------------
# Main analysis
# --------------------------------------------------------------------------
def main():
    t0 = time.time()
    c1 = load_cycle1()
    print('Loaded cycle1 aggregate.')

    # Load all landscapes
    land = {}  # land[subj][roi] = dict of metric grids
    for s in ALL_SUBS:
        land[s] = {}
        for r in ROIS:
            d = load_landscape(s, r)
            if d is not None:
                land[s][r] = d
    n_pairs = sum(len(v) for v in land.values())
    print(f'Landscapes loaded: {n_pairs} (subj, roi) pairs')

    # ----------------------------------------------------------------
    # 1) C1 enhanced metrics: n_global_minima, secondary_min ratio
    # ----------------------------------------------------------------
    c1_metrics = {}
    for L in ['l_topk_jaccard', 'mw_jaccard_loss', 'l_rank', 'l_dir']:
        c1_metrics[L] = {}
        for r in ROIS:
            c1_metrics[L][r] = {}
            for s in land:
                if r not in land[s]:
                    continue
                g = land[s][r][L]
                c1_metrics[L][r][s] = {
                    'sec_min_ratio': secondary_min_ratio(g),
                    'n_global_minima': n_global_minima(g),
                    'best_centroid_idx': list(best_arg_centroid(g)),
                }

    # ----------------------------------------------------------------
    # 2) Blend α sweep (0.0..1.0 step 0.1)
    # ----------------------------------------------------------------
    alphas = np.linspace(0.0, 1.0, 11)
    blend_results = {}
    for r in ROIS:
        blend_results[r] = {}
        for a in alphas:
            key = f'a{a:.1f}'
            best_per_subj = {}
            for s in land:
                if r not in land[s]:
                    continue
                g1 = land[s][r]['l_topk_jaccard']
                g2 = land[s][r]['mw_jaccard_loss']
                blend = a * g1 + (1 - a) * g2
                best_per_subj[s] = float(blend.min())
            # specificity
            hc_vals = np.array([best_per_subj[s] for s in HC_SUBS
                                if s in best_per_subj])
            cvd_dict = {}
            for cs in CVD_SUBS + SANITY_SUBS:
                if cs not in best_per_subj:
                    continue
                cv = best_per_subj[cs]
                p = float((np.sum(hc_vals <= cv) + 1)
                          / (len(hc_vals) + 1))
                z = (cv - hc_vals.mean()) / hc_vals.std() \
                    if hc_vals.std() > 0 else 0.0
                cvd_dict[cs] = {'value': float(cv), 'p_emp': p, 'z': float(z)}
            blend_results[r][key] = {
                'alpha': float(a),
                'hc_mean': float(hc_vals.mean()),
                'hc_std': float(hc_vals.std()),
                'cvd': cvd_dict,
            }

    # Identify best alpha per ROI by max sub-08 |z| (most-separated)
    best_alpha_per_roi = {}
    for r in ROIS:
        best_a = None
        best_score = 0.0
        for k, ent in blend_results[r].items():
            if '08' in ent['cvd']:
                z08 = -ent['cvd']['08']['z']  # negative z = good for CVD
                if z08 > best_score:
                    best_score = z08
                    best_a = ent['alpha']
        best_alpha_per_roi[r] = {'alpha': best_a, 'sub-08_z': -best_score}

    # ----------------------------------------------------------------
    # 3) Sign correction for V2 + Mahalanobis combos
    # ----------------------------------------------------------------
    # Use blend_a50 (0.5/0.5) for combo evaluation per Cycle 1 design
    target_L = 'a0.5'

    def get_per_roi_z(s, roi, alpha_key):
        ent = blend_results[roi][alpha_key]
        if s not in ent['cvd']:
            return None
        return ent['cvd'][s]['z']

    # Build combo z matrix per CVD/HC subject and ROI subset
    combo_results = {}
    roi_combos = []
    for k in [2, 3]:
        for c in combinations(ROIS, k):
            roi_combos.append(c)

    for combo in roi_combos:
        ckey = '+'.join(combo)
        combo_results[ckey] = {}
        # per-ROI HC pool
        hc_mat = []
        hc_subs_in = []
        for s in HC_SUBS:
            row = []
            ok = True
            for r in combo:
                if s not in land or r not in land[s]:
                    ok = False
                    break
                g1 = land[s][r]['l_topk_jaccard']
                g2 = land[s][r]['mw_jaccard_loss']
                blend = 0.5 * g1 + 0.5 * g2
                row.append(float(blend.min()))
            if ok:
                hc_mat.append(row)
                hc_subs_in.append(s)
        hc_mat = np.array(hc_mat)
        hc_mean = hc_mat.mean(axis=0)
        hc_std = hc_mat.std(axis=0)
        # CVD
        cvd_dict = {}
        for cs in CVD_SUBS + SANITY_SUBS:
            if cs not in land:
                continue
            row = []
            ok = True
            for r in combo:
                if r not in land[cs]:
                    ok = False
                    break
                g1 = land[cs][r]['l_topk_jaccard']
                g2 = land[cs][r]['mw_jaccard_loss']
                blend = 0.5 * g1 + 0.5 * g2
                row.append(float(blend.min()))
            if not ok:
                continue
            cvd_vec = np.array(row)

            # ----- Method A: z_sum (unsigned sum) -----
            z_per_roi = (cvd_vec - hc_mean) / np.where(hc_std > 0, hc_std, 1.0)
            zsum = float(z_per_roi.sum())

            # ----- Method B: V2 sign-flip (use |z| if V2 in combo) -----
            z_signed = z_per_roi.copy()
            if 'V2' in combo:
                idx_v2 = list(combo).index('V2')
                # if positive z (CVD worse than HC) at V2, flip — this enables
                # "V2 is different from HC in either direction"
                z_signed[idx_v2] = -abs(z_signed[idx_v2])
            zsum_signed = float(z_signed.sum())

            # ----- Method C: Mahalanobis -----
            try:
                d_cvd, hc_d, p_maha = mahalanobis_combine(cvd_vec, hc_mat)
            except np.linalg.LinAlgError:
                d_cvd, hc_d, p_maha = (float('nan'), [], 1.0)

            # HC null for z_sum and z_sum_signed
            hc_z = (hc_mat - hc_mean) / np.where(hc_std > 0, hc_std, 1.0)
            hc_zsum = hc_z.sum(axis=1)

            # signed HC: same sign-flip rule
            if 'V2' in combo:
                hc_z_signed = hc_z.copy()
                idx_v2 = list(combo).index('V2')
                hc_z_signed[:, idx_v2] = -np.abs(hc_z_signed[:, idx_v2])
            else:
                hc_z_signed = hc_z
            hc_zsum_signed = hc_z_signed.sum(axis=1)

            cvd_dict[cs] = {
                'cvd_vec': cvd_vec.tolist(),
                'z_per_roi': z_per_roi.tolist(),
                'z_sum': zsum,
                'p_zsum': float((np.sum(hc_zsum <= zsum) + 1)
                                / (len(hc_zsum) + 1)),
                'z_sum_signed': zsum_signed,
                'p_zsum_signed': float((np.sum(hc_zsum_signed <= zsum_signed) + 1)
                                       / (len(hc_zsum_signed) + 1)),
                'mahal': float(d_cvd),
                'p_mahal': float(p_maha),
            }
        combo_results[ckey] = {
            'rois': combo,
            'hc_subjects': hc_subs_in,
            'hc_mat': hc_mat.tolist(),
            'cvd': cvd_dict,
            'hc_mean': hc_mean.tolist(),
            'hc_std': hc_std.tolist(),
        }

    # ----------------------------------------------------------------
    # 4) Save and print
    # ----------------------------------------------------------------
    out = {
        'config': {
            'cycle': 2,
            'description': 'Mahalanobis combo + V2 sign-flip + α sweep + C1',
        },
        'C1_enhanced': c1_metrics,
        'blend_alpha_sweep': blend_results,
        'best_alpha_per_roi': best_alpha_per_roi,
        'combo_results': combo_results,
    }
    out_path = _RESULTS / 'cycle2_aggregate.json'
    with open(out_path, 'w') as f:
        json.dump(out, f, indent=2, default=str)
    print(f'Wrote {out_path}')

    # ---------- Print summary ----------
    print('\n=== Best α per ROI (by sub-08 |z|) ===')
    for r, ent in best_alpha_per_roi.items():
        print(f'  {r}: α* = {ent["alpha"]} → sub-08 z = {ent["sub-08_z"]:+.2f}')

    print('\n=== α sweep specificity for sub-08, sub-09 ===')
    for r in ROIS:
        print(f'\n[{r}]')
        for k in sorted(blend_results[r].keys()):
            ent = blend_results[r][k]
            line = f'  α={ent["alpha"]:.1f}  HCμ={ent["hc_mean"]:.3f}±{ent["hc_std"]:.3f}'
            for cs in ['08', '09']:
                if cs in ent['cvd']:
                    cv = ent['cvd'][cs]
                    line += f'  s{cs}: z={cv["z"]:+.2f} p={cv["p_emp"]:.2f}'
            print(line)

    print('\n=== Combo specificity (3 methods) at blend α=0.5 ===')
    for ckey, ent in combo_results.items():
        print(f'\n[{ckey}]')
        for cs, cv in ent['cvd'].items():
            print(f'  sub-{cs}:  z_sum={cv["z_sum"]:+.2f}(p={cv["p_zsum"]:.2f})  '
                  f'z_sum_signed={cv["z_sum_signed"]:+.2f}(p={cv["p_zsum_signed"]:.2f})  '
                  f'maha={cv["mahal"]:.2f}(p={cv["p_mahal"]:.2f})')

    print('\n=== C1 enhanced (n_global_minima @ blend50 grid by ROI) ===')
    for L in ['l_topk_jaccard', 'mw_jaccard_loss', 'l_rank']:
        for r in ROIS:
            n_mins = [c1_metrics[L][r][s]['n_global_minima']
                      for s in c1_metrics[L][r]]
            print(f'  {L} {r}: median n_min={int(np.median(n_mins))} '
                  f'range=[{min(n_mins)}, {max(n_mins)}]')

    print(f'\n[Done] elapsed={time.time()-t0:.1f}s')


if __name__ == '__main__':
    main()
