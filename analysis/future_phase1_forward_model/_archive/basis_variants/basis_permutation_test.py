#!/usr/bin/env python3
"""
basis_permutation_test.py — Permutation test for optimal bases per ROI.

Tests whether LOCO voxel_corr exceeds color-label-shuffled null.
Fixed alpha (from real data) per subject, 10K permutations.

Bases tested:
  V1: FE-2, FE-6 (baseline)
  V2: FE-3, FE-6
  V3: FE-8, FE-6
  V4: FE-3, FE-6
"""

import numpy as np
import json
from pathlib import Path
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent))
from utils_forward_model import (
    HC_SUBJECTS, ROIS, HUE_ANGLES, N_RUNS, N_COLORS, ALPHA_GRID,
    load_amplitudes, create_basis_matrix, create_basis_full,
    fit_W_ridge, gcv_select_alpha, predict_patterns,
    voxel_pattern_correlation,
)

# ============================================================================
# Configuration
# ============================================================================

LOCAL_BASELINE_DIR = Path(__file__).resolve().parents[3] / \
    'analysis' / 'phase1_preprocess_decoding' / 'results' / 'full_dataset_C010'

OUTPUT_DIR = Path(__file__).resolve().parents[1] / 'results' / 'basis_comparison'

N_PERM = 10000
RNG_SEED = 42

# ROI → bases to test
ROI_BASES = {
    'V1': [('FE-2', 'fe', 2), ('FE-6', 'fe', 6)],
    'V2': [('FE-3', 'fe', 3), ('FE-6', 'fe', 6)],
    'V3': [('FE-8', 'fe', 8), ('FE-6', 'fe', 6)],
    'V4': [('FE-3', 'fe', 3), ('FE-6', 'fe', 6)],
}


# ============================================================================
# LOCO with fixed alpha (fast path for permutation)
# ============================================================================

def loco_fixed_alpha(amp, C_full, alpha):
    """Run LOCO with pre-selected alpha. Returns mean voxel_corr across 8 colors.

    Args:
        amp: (6, 8, V_s)
        C_full: (8, K) design matrix
        alpha: fixed ridge alpha

    Returns:
        mean_voxel_corr: float
    """
    color_corrs = []

    for test_color in range(N_COLORS):
        train_colors = [c for c in range(N_COLORS) if c != test_color]

        X_train = amp[:, train_colors, :].reshape(-1, amp.shape[2])  # (42, V_s)
        C_train = np.tile(C_full[train_colors], (N_RUNS, 1))        # (42, K)

        X_test = amp[:, test_color, :].mean(axis=0, keepdims=True)   # (1, V_s)
        C_test = C_full[test_color:test_color+1]                     # (1, K)

        W = fit_W_ridge(C_train, X_train, alpha)
        Y_hat = predict_patterns(W, C_test)
        r = voxel_pattern_correlation(Y_hat, X_test)
        color_corrs.append(r[0])

    return float(np.mean(color_corrs))


def select_alpha_for_loco(amp, C_full):
    """Select best alpha via GCV on full (non-held-out) data."""
    X_all = amp.reshape(-1, amp.shape[2])          # (48, V_s)
    C_all = np.tile(C_full, (N_RUNS, 1))           # (48, K)
    best_alpha, _ = gcv_select_alpha(C_all, X_all)
    return best_alpha


# ============================================================================
# Permutation test
# ============================================================================

def run_permutation_test(amp, basis_label, basis_type, n_channels, n_perm, rng):
    """Run permutation test for one subject × one ROI × one basis.

    Shuffles color labels (axis=1 of amp), recomputes LOCO.

    Returns:
        dict with observed, null_mean, null_sd, p_perm, null_95ci
    """
    C_full = create_basis_matrix(HUE_ANGLES, n_channels, basis_type)

    # Select alpha on real data
    alpha = select_alpha_for_loco(amp, C_full)

    # Observed LOCO
    observed = loco_fixed_alpha(amp, C_full, alpha)

    # Null distribution
    null_dist = np.zeros(n_perm)
    for i in range(n_perm):
        # Shuffle color labels: permute axis=1 independently per run?
        # Standard: same permutation across all runs (preserves run structure)
        perm = rng.permutation(N_COLORS)
        amp_perm = amp[:, perm, :]
        null_dist[i] = loco_fixed_alpha(amp_perm, C_full, alpha)

    p_perm = float(np.mean(null_dist >= observed))
    null_mean = float(np.mean(null_dist))
    null_sd = float(np.std(null_dist))
    null_95 = [float(np.percentile(null_dist, 2.5)),
               float(np.percentile(null_dist, 97.5))]

    return {
        'observed': observed,
        'null_mean': null_mean,
        'null_sd': null_sd,
        'null_95ci': null_95,
        'p_perm': p_perm,
        'alpha_used': alpha,
        'basis': basis_label,
        'n_perm': n_perm,
    }


# ============================================================================
# Main
# ============================================================================

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(RNG_SEED)

    print(f'Permutation test: {N_PERM} shuffles, seed={RNG_SEED}')
    print(f'Data: {LOCAL_BASELINE_DIR}')
    print()

    all_results = {}

    for roi in ROIS:
        all_results[roi] = {}
        bases = ROI_BASES[roi]

        for basis_label, basis_type, n_channels in bases:
            all_results[roi][basis_label] = {}
            print(f'--- {roi} / {basis_label} ---')

            subj_observed = []
            subj_null_means = []
            subj_p_perms = []

            for subj in HC_SUBJECTS:
                amp = load_amplitudes(LOCAL_BASELINE_DIR, subj, roi)

                res = run_permutation_test(
                    amp, basis_label, basis_type, n_channels, N_PERM, rng
                )
                all_results[roi][basis_label][subj] = res

                subj_observed.append(res['observed'])
                subj_null_means.append(res['null_mean'])
                subj_p_perms.append(res['p_perm'])

                print(f'  sub-{subj}: obs={res["observed"]:.3f}  '
                      f'null={res["null_mean"]:.3f}±{res["null_sd"]:.3f}  '
                      f'p={res["p_perm"]:.4f}')

            # HC group summary
            hc_obs = np.mean(subj_observed)
            hc_null = np.mean(subj_null_means)
            # Group-level p: fraction of group-mean null >= group-mean observed
            # Recompute from per-subject null distributions
            print(f'  HC mean: obs={hc_obs:.3f}  null_mean={hc_null:.3f}  '
                  f'individual p range: [{min(subj_p_perms):.4f}, {max(subj_p_perms):.4f}]')
            print()

    # Save
    out_path = OUTPUT_DIR / 'basis_permutation_10K.json'
    with open(out_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f'Results saved to {out_path}')

    # === Summary table ===
    print('\n' + '=' * 80)
    print('SUMMARY: Permutation Test Results (HC, 10K shuffles)')
    print('=' * 80)
    print(f'{"ROI":<5} {"Basis":<8} {"HC Obs":>8} {"Null M":>8} {"Δ":>8} {"p_group":>8}')

    for roi in ROIS:
        for basis_label in all_results[roi]:
            obs_vals = [all_results[roi][basis_label][s]['observed']
                        for s in HC_SUBJECTS]
            null_vals = [all_results[roi][basis_label][s]['null_mean']
                         for s in HC_SUBJECTS]
            p_vals = [all_results[roi][basis_label][s]['p_perm']
                      for s in HC_SUBJECTS]

            # Stouffer's method for combining p-values
            from scipy import stats
            z_scores = [stats.norm.ppf(1 - p) if p < 1 else 0 for p in p_vals]
            z_combined = np.mean(z_scores) / (1.0 / np.sqrt(len(z_scores)))
            # Actually, Stouffer: Z = sum(z_i) / sqrt(n)
            z_stouffer = np.sum(z_scores) / np.sqrt(len(z_scores))
            p_stouffer = 1 - stats.norm.cdf(z_stouffer)

            hc_obs = np.mean(obs_vals)
            hc_null = np.mean(null_vals)
            delta = hc_obs - hc_null

            sig = '***' if p_stouffer < 0.001 else '**' if p_stouffer < 0.01 else '*' if p_stouffer < 0.05 else '†' if p_stouffer < 0.1 else ''

            print(f'{roi:<5} {basis_label:<8} {hc_obs:>+8.3f} {hc_null:>+8.3f} '
                  f'{delta:>+8.3f} {p_stouffer:>8.4f} {sig}')


if __name__ == '__main__':
    main()
