"""S6': HC subset resample bootstrap (Nili-faithful, Spearman primary).

Re-fits R+C 1-DOF and 2-Component to L4 RDM cosine/Spearman loss across
all C(7,k) for k∈{4,5,6} HC subsets per (subject, ROI). Quantifies HC-pool
composition dependence of fit, with explicit sub-04 outlier tracking.

Design (PIPELINE_RESULT.md §S6'):
  For each subset S ⊂ HC_available:
    1) hc_W_S = ridge_gcv W per h∈S (using each HC's own runs)
    2) RDM_baseline_per_hc_S = RDM(C_baseline @ W_h)
    3) RDM_CVD = RDM(mean over runs) of CVD amp (constant across subsets)
    4) ΔRDM_obs_S = RDM_CVD − mean_{h∈S} RDM(amp_h.mean(axis=0))
    5) Grid-search:
       R+C:    g ∈ [0, 3] step 0.05 (61 pts), forward = (2-g)·δθ_Machado(Δλ_DPS)
       2-Comp: (β_s, β_c) ∈ [-50,50]² step 2 (51×51 = 2601 pts) — symmetric β_s grid
    6) Loss = 1 - Spearman ρ(ΔRDM_sim, ΔRDM_obs_S); cosine recorded.

Notes:
  - V4 already excludes sub-07 (16 voxels) via load_hc_pool → effective n=6 HCs
    → C(6,k) subsets: 15+6+1 = 22, NOT 63. Reported per cell.
  - V1 has full n=7 → 35+21+7 = 63 subsets.
  - Δλ_DPS only: sub-08=6, sub-09=10.
  - σ=21° not directly used (L4 is δθ-only forward).
  - C_baseline = create_basis_full(K, 'fe')[HUE_ANGLES.astype(int)], matching
    s5_all_paths_fit.py L4 implementation (§A12 nuance noted in transcript).

Outputs:
  results/s6p_hc_subset/{subject}_{roi}_{model}.json (8 files)
"""
import sys
import json
import time
import itertools
from pathlib import Path
import numpy as np
from scipy.stats import spearmanr

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from rc_1dof import forward_rc, g_grid
from two_comp import forward_2comp
from neural_loss import (
    load_amplitudes, load_hc_pool, ROI_K, design_from_delta,
)
from diagnostic_delta_rdm import (
    precompute_hc_W, compute_rdm_correlation, cosine_similarity,
)
from utils_forward_model import create_basis_full, HUE_ANGLES

# ---- Settings ----
DELTA_LAMBDA_DPS = {'sub-08': 6.0, 'sub-09': 10.0}
CVD_FAMILY = {'sub-08': 'deutan', 'sub-09': 'protan'}

# Symmetric 2-Comp grid (task-specified, NOT module BS_GRID which is asymmetric ≥0)
BS_GRID_SYM = np.arange(-50.0, 50.0 + 1e-9, 2.0)   # 51 points
BC_GRID_SYM = np.arange(-50.0, 50.0 + 1e-9, 2.0)   # 51 points

OUT_DIR = SCRIPT_DIR.parent / "results" / "s6p_hc_subset"


# ============================================================================
# Per-subset re-fit helpers
# ============================================================================

def _safe_spearman(a: np.ndarray, b: np.ndarray) -> float:
    """Return Spearman ρ; 0.0 on degenerate (constant) inputs."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if np.std(a) < 1e-15 or np.std(b) < 1e-15:
        return 0.0
    rho, _ = spearmanr(a, b)
    return float(rho) if np.isfinite(rho) else 0.0


def _safe_cosine(a: np.ndarray, b: np.ndarray) -> float:
    """Return cosine similarity; 0.0 on degenerate inputs."""
    val = cosine_similarity(a, b)
    return val if np.isfinite(val) else 0.0


def precompute_subset_caches(cvd_amp: np.ndarray,
                              hc_amps_subset: dict,
                              C_baseline: np.ndarray):
    """Cache things that depend on subset but are δθ-invariant.

    Returns:
      rdm_cvd:                 (28,) RDM of CVD mean pattern
      delta_rdm_obs_S:         (28,) RDM_CVD - mean_{h∈S} RDM(mean amp_h)
      hc_W_S:                  dict {h: (K, V_s)}
      rdm_baseline_per_hc_S:   dict {h: (28,)}
    """
    rdm_cvd = compute_rdm_correlation(cvd_amp.mean(axis=0))
    rdm_hc_individual = {
        h: compute_rdm_correlation(amp.mean(axis=0))
        for h, amp in hc_amps_subset.items()
    }
    rdm_hc_mean = np.mean(list(rdm_hc_individual.values()), axis=0)
    delta_rdm_obs_S = rdm_cvd - rdm_hc_mean

    hc_W_S, _ = precompute_hc_W(hc_amps_subset, C_baseline)

    rdm_baseline_per_hc_S = {}
    for h, W in hc_W_S.items():
        Y_b = C_baseline @ W
        rdm_baseline_per_hc_S[h] = compute_rdm_correlation(Y_b)

    return rdm_cvd, delta_rdm_obs_S, hc_W_S, rdm_baseline_per_hc_S


def compute_delta_rdm_sim(delta_8vec: np.ndarray, n_channels: int,
                            hc_W_S: dict, rdm_baseline_per_hc_S: dict) -> np.ndarray:
    """Compute mean ΔRDM_sim across subset HCs given δθ."""
    C_shifted = design_from_delta(delta_8vec, n_channels=n_channels)
    delta_rdm_per_hc = []
    for h, W in hc_W_S.items():
        Y_s = C_shifted @ W
        rdm_s = compute_rdm_correlation(Y_s)
        delta_rdm_per_hc.append(rdm_s - rdm_baseline_per_hc_S[h])
    return np.mean(delta_rdm_per_hc, axis=0)


def fit_rc_subset(delta_lambda: float, cvd_family: str,
                  delta_rdm_obs_S: np.ndarray, n_channels: int,
                  hc_W_S: dict, rdm_baseline_per_hc_S: dict) -> dict:
    """R+C 1-DOF grid search: g ∈ [0,3] step 0.05.
    Loss = 1 - Spearman ρ (primary); cosine recorded.
    """
    grid = g_grid()  # 61 pts
    spear_arr = np.zeros_like(grid)
    cos_arr = np.zeros_like(grid)
    for i, g in enumerate(grid):
        delta_rc = forward_rc(delta_lambda, g, cvd_family)
        delta_sim = compute_delta_rdm_sim(delta_rc, n_channels,
                                            hc_W_S, rdm_baseline_per_hc_S)
        spear_arr[i] = _safe_spearman(delta_sim, delta_rdm_obs_S)
        cos_arr[i] = _safe_cosine(delta_sim, delta_rdm_obs_S)

    # Primary: maximize Spearman ρ
    best_idx = int(np.argmax(spear_arr))
    g_best = float(grid[best_idx])
    return {
        'g_best': g_best,
        'spearman_rho_best': float(spear_arr[best_idx]),
        'cosine_at_spearman_best': float(cos_arr[best_idx]),
        'loss_spearman_best': float(1.0 - spear_arr[best_idx]),
        'cosine_max': float(np.max(cos_arr)),
        'g_at_cosine_max': float(grid[int(np.argmax(cos_arr))]),
        'boundary_low': bool(best_idx == 0),
        'boundary_high': bool(best_idx == len(grid) - 1),
    }


def fit_2comp_subset(cvd_family: str, delta_rdm_obs_S: np.ndarray,
                      n_channels: int, hc_W_S: dict,
                      rdm_baseline_per_hc_S: dict) -> dict:
    """2-Comp grid search over symmetric β_s ∈ [-50,50], β_c ∈ [-50,50] step 2.
    Loss = 1 - Spearman ρ (primary); cosine recorded.
    """
    n_bs = len(BS_GRID_SYM)
    n_bc = len(BC_GRID_SYM)
    spear_grid = np.zeros((n_bs, n_bc))
    cos_grid = np.zeros((n_bs, n_bc))

    for i, bs in enumerate(BS_GRID_SYM):
        for j, bc in enumerate(BC_GRID_SYM):
            delta_tc = forward_2comp(bs, bc, cvd_family)
            delta_sim = compute_delta_rdm_sim(delta_tc, n_channels,
                                               hc_W_S, rdm_baseline_per_hc_S)
            spear_grid[i, j] = _safe_spearman(delta_sim, delta_rdm_obs_S)
            cos_grid[i, j] = _safe_cosine(delta_sim, delta_rdm_obs_S)

    best_idx = np.unravel_index(np.argmax(spear_grid), spear_grid.shape)
    bs_best = float(BS_GRID_SYM[best_idx[0]])
    bc_best = float(BC_GRID_SYM[best_idx[1]])

    # Independent cosine max
    cos_idx = np.unravel_index(np.argmax(cos_grid), cos_grid.shape)

    return {
        'beta_s_best': bs_best,
        'beta_c_best': bc_best,
        'spearman_rho_best': float(spear_grid[best_idx]),
        'cosine_at_spearman_best': float(cos_grid[best_idx]),
        'loss_spearman_best': float(1.0 - spear_grid[best_idx]),
        'cosine_max': float(np.max(cos_grid)),
        'beta_s_at_cosine_max': float(BS_GRID_SYM[cos_idx[0]]),
        'beta_c_at_cosine_max': float(BC_GRID_SYM[cos_idx[1]]),
        'boundary_bs': bool(best_idx[0] == 0 or best_idx[0] == n_bs - 1),
        'boundary_bc': bool(best_idx[1] == 0 or best_idx[1] == n_bc - 1),
    }


# ============================================================================
# Subset enumeration & main loop
# ============================================================================

def enumerate_subsets(hc_available: list) -> list:
    """Enumerate all C(n,k) for k∈{4,5,6}. Returns list of (k, members tuple)."""
    subsets = []
    for k in (4, 5, 6):
        if k > len(hc_available):
            continue
        for combo in itertools.combinations(sorted(hc_available), k):
            subsets.append((k, combo))
    return subsets


def run_cell(subject: str, roi: str) -> dict:
    """Process one (subject, ROI) cell across all subsets and both models."""
    cvd_family = CVD_FAMILY[subject]
    delta_lambda = DELTA_LAMBDA_DPS[subject]
    K = ROI_K[roi]

    print(f"\n=== Cell: {subject} {roi} (Δλ={delta_lambda}nm, family={cvd_family}) ===")
    t0 = time.time()

    cvd_amp = load_amplitudes(subject, roi)
    hc_amps_full = load_hc_pool(roi)  # already drops sub-07 V4 if sparse
    hc_available = sorted(hc_amps_full.keys())
    print(f"  HCs available for {roi}: {hc_available} (n={len(hc_available)})")

    C_baseline = create_basis_full(K, basis_type='fe')[HUE_ANGLES.astype(int)]

    subsets = enumerate_subsets(hc_available)
    n_subsets = len(subsets)
    print(f"  Subsets to evaluate: {n_subsets} "
          f"(k=4:{len([s for s in subsets if s[0]==4])}, "
          f"k=5:{len([s for s in subsets if s[0]==5])}, "
          f"k=6:{len([s for s in subsets if s[0]==6])})")

    rc_records = []
    tc_records = []

    for idx, (k, members) in enumerate(subsets):
        hc_amps_S = {h: hc_amps_full[h] for h in members}
        rdm_cvd, delta_rdm_obs_S, hc_W_S, rdm_base_S = \
            precompute_subset_caches(cvd_amp, hc_amps_S, C_baseline)

        # --- R+C ---
        rc_fit = fit_rc_subset(delta_lambda, cvd_family, delta_rdm_obs_S,
                                 K, hc_W_S, rdm_base_S)
        rc_records.append({
            'k': k, 'members': list(members),
            'includes_sub04': 'sub-04' in members,
            'fit': rc_fit,
        })

        # --- 2-Comp ---
        tc_fit = fit_2comp_subset(cvd_family, delta_rdm_obs_S,
                                    K, hc_W_S, rdm_base_S)
        tc_records.append({
            'k': k, 'members': list(members),
            'includes_sub04': 'sub-04' in members,
            'fit': tc_fit,
        })

        if (idx + 1) % 10 == 0 or idx == n_subsets - 1:
            elapsed = time.time() - t0
            rate = (idx + 1) / elapsed
            eta = (n_subsets - idx - 1) / rate
            print(f"    [{idx+1}/{n_subsets}] elapsed={elapsed:.1f}s "
                  f"rate={rate:.2f}/s eta={eta:.1f}s")

    elapsed = time.time() - t0
    print(f"  Cell done in {elapsed:.1f}s ({n_subsets} subsets × 2 models)")

    return {
        'subject': subject,
        'roi': roi,
        'cvd_family': cvd_family,
        'delta_lambda_nm': delta_lambda,
        'K': K,
        'n_hc_available': len(hc_available),
        'hc_available': hc_available,
        'n_subsets': n_subsets,
        'sub07_excluded_a_priori': (roi == 'V4'),  # by load_hc_pool
        'rc_subsets': rc_records,
        'tc_subsets': tc_records,
        'wall_time_s': round(elapsed, 1),
    }


# ============================================================================
# Summary statistics
# ============================================================================

def summarize_model(records: list, key_param: str) -> dict:
    """Compute distribution stats + sub-04 dependence for one model's records."""
    spear = np.array([r['fit']['spearman_rho_best'] for r in records])
    cos = np.array([r['fit']['cosine_at_spearman_best'] for r in records])
    params = np.array([r['fit'][key_param] for r in records])

    with04 = np.array([r['includes_sub04'] for r in records])
    n_with = int(with04.sum())
    n_without = int((~with04).sum())

    def _qstats(x):
        return {
            'median': float(np.median(x)),
            'mean': float(np.mean(x)),
            'sd': float(np.std(x, ddof=1)) if len(x) > 1 else 0.0,
            'q025': float(np.quantile(x, 0.025)),
            'q975': float(np.quantile(x, 0.975)),
            'min': float(x.min()),
            'max': float(x.max()),
        }

    summary = {
        'spearman_distribution': _qstats(spear),
        'cosine_distribution': _qstats(cos),
        f'{key_param}_distribution': _qstats(params),
        'param_name': key_param,
        'n_subsets': len(records),
        'n_with_sub04': n_with,
        'n_without_sub04': n_without,
    }
    if n_with > 0 and n_without > 0:
        summary['sub04_dependence'] = {
            'with_sub04_median_spearman': float(np.median(spear[with04])),
            'without_sub04_median_spearman': float(np.median(spear[~with04])),
            'delta_spearman': float(np.median(spear[with04]) - np.median(spear[~with04])),
            'with_sub04_median_cosine': float(np.median(cos[with04])),
            'without_sub04_median_cosine': float(np.median(cos[~with04])),
            'with_sub04_median_param': float(np.median(params[with04])),
            'without_sub04_median_param': float(np.median(params[~with04])),
        }
    else:
        summary['sub04_dependence'] = None
    return summary


def save_model_records(cell: dict, model: str, key_param: str):
    """Save per-subset records + summary for one (subject, roi, model)."""
    records = cell['rc_subsets'] if model == 'R+C' else cell['tc_subsets']
    out = {
        'subject': cell['subject'],
        'roi': cell['roi'],
        'cvd_family': cell['cvd_family'],
        'model': model,
        'delta_lambda_nm': cell['delta_lambda_nm'],
        'K': cell['K'],
        'n_hc_available': cell['n_hc_available'],
        'hc_available': cell['hc_available'],
        'sub07_excluded_a_priori': cell['sub07_excluded_a_priori'],
        'n_subsets': cell['n_subsets'],
        'subsets': records,
        'summary': summarize_model(records, key_param),
    }
    model_tag = 'RC' if model == 'R+C' else '2Comp'
    out_path = OUT_DIR / f"{cell['subject']}_{cell['roi']}_{model_tag}.json"
    with open(out_path, 'w') as f:
        json.dump(out, f, indent=2, default=str)
    print(f"  Saved: {out_path}")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 78)
    print("S6': HC subset resample (Nili-faithful, Spearman primary)")
    print("=" * 78)

    t_start = time.time()
    cells = []
    for subject in ('sub-08', 'sub-09'):
        for roi in ('V1', 'V4'):
            cell = run_cell(subject, roi)
            cells.append(cell)
            save_model_records(cell, 'R+C', key_param='g_best')
            save_model_records(cell, '2-Comp', key_param='beta_s_best')

    # Master summary
    master = {
        'cells': [
            {
                'subject': c['subject'], 'roi': c['roi'],
                'delta_lambda_nm': c['delta_lambda_nm'],
                'n_subsets': c['n_subsets'],
                'n_hc_available': c['n_hc_available'],
                'wall_time_s': c['wall_time_s'],
            }
            for c in cells
        ],
        'total_wall_time_s': round(time.time() - t_start, 1),
    }
    with open(OUT_DIR / "master_summary.json", 'w') as f:
        json.dump(master, f, indent=2)
    print(f"\nTotal: {master['total_wall_time_s']:.1f}s")
    print(f"Master summary: {OUT_DIR / 'master_summary.json'}")


if __name__ == "__main__":
    main()
