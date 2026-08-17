#!/usr/bin/env python3
"""
intercept_permutation_test.py — Test whether explicit intercept model
resolves the voxel covariance problem in V1/V2 permutation tests.

Model: Y = W_color @ C + b @ 1'  (b absorbs shared spatial pattern)
Metric: corr(C_test @ W_color, Y_real - b)  (deviation-only evaluation)

Compares:
  (A) Standard model (Y = WC), standard metric (voxel_corr)
  (B) Intercept model (Y = W_color @ C + b), deviation metric
  (C) Standard model, but evaluate with mean-subtracted metric

Tests FE-6 baseline and per-ROI optimal basis.
10K permutations, HC subjects.
"""

import numpy as np
import json
from pathlib import Path
from scipy import stats as sp_stats

import sys
sys.path.insert(0, str(Path(__file__).parent))
from utils_forward_model import (
    HC_SUBJECTS, CVD_SUBJECTS, ROIS, HUE_ANGLES, N_RUNS, N_COLORS,
    ALPHA_GRID, load_amplitudes, create_basis_matrix,
    fit_W_ridge, gcv_select_alpha, voxel_pattern_correlation,
)

# ============================================================================
# Configuration
# ============================================================================

SERVER_BASELINE_DIR = Path('/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010')
LOCAL_BASELINE_DIR = Path(__file__).resolve().parents[3] / \
    'analysis' / 'phase1_preprocess_decoding' / 'results' / 'full_dataset_C010'
BASELINE_DIR = SERVER_BASELINE_DIR if SERVER_BASELINE_DIR.exists() else LOCAL_BASELINE_DIR

OUTPUT_DIR = Path(__file__).resolve().parents[1] / 'results' / 'basis_comparison'

N_PERM = 10000
RNG_SEED = 42

# Per-ROI: (label, type, K)
ROI_BASES = {
    'V1': ('FE-6', 'fe', 6),
    'V2': ('FE-6', 'fe', 6),
    'V3': ('FE-8', 'fe', 8),
    'V4': ('FE-3', 'fe', 3),
}


# ============================================================================
# Intercept model fitting
# ============================================================================

def fit_intercept_ridge(C, X, alpha):
    """Fit Y = W_color @ C + b with unregularized intercept.

    Standard approach: center C and X, fit ridge on centered data,
    then recover intercept from means.

    Args:
        C: (n, K) design matrix
        X: (n, V_s) voxel patterns
        alpha: ridge penalty (applied to W_color only, not b)

    Returns:
        W_color: (K, V_s) color-specific weights
        b: (V_s,) intercept (shared spatial pattern)
    """
    n = C.shape[0]
    K = C.shape[1]

    # Center
    C_mean = C.mean(axis=0, keepdims=True)  # (1, K)
    X_mean = X.mean(axis=0, keepdims=True)  # (1, V_s)
    C_c = C - C_mean
    X_c = X - X_mean

    # Ridge on centered data
    W_color = np.linalg.solve(C_c.T @ C_c + alpha * np.eye(K), C_c.T @ X_c)

    # Recover intercept: b = X_mean - C_mean @ W_color
    b = (X_mean - C_mean @ W_color).ravel()  # (V_s,)

    return W_color, b


# ============================================================================
# LOCO variants
# ============================================================================

def loco_standard(amp, C_full, alpha):
    """Standard LOCO: Y = WC, metric = voxel_corr(Y_hat, Y_real)."""
    corrs = []
    for tc in range(N_COLORS):
        train = [c for c in range(N_COLORS) if c != tc]
        X_train = amp[:, train, :].reshape(-1, amp.shape[2])
        C_train = np.tile(C_full[train], (N_RUNS, 1))
        X_test = amp[:, tc, :].mean(axis=0, keepdims=True)
        C_test = C_full[tc:tc+1]

        W = fit_W_ridge(C_train, X_train, alpha)
        Y_hat = C_test @ W
        r = voxel_pattern_correlation(Y_hat, X_test)
        corrs.append(r[0])
    return float(np.mean(corrs))


def loco_intercept_deviation(amp, C_full, alpha):
    """Intercept model LOCO: metric = corr(C_test @ W_color, Y_real - b).

    b absorbs shared spatial pattern.
    Evaluation uses only color-specific prediction component.
    """
    corrs = []
    for tc in range(N_COLORS):
        train = [c for c in range(N_COLORS) if c != tc]
        X_train = amp[:, train, :].reshape(-1, amp.shape[2])
        C_train = np.tile(C_full[train], (N_RUNS, 1))
        X_test = amp[:, tc, :].mean(axis=0, keepdims=True)  # (1, V_s)
        C_test = C_full[tc:tc+1]  # (1, K)

        W_color, b = fit_intercept_ridge(C_train, X_train, alpha)

        # Color-specific prediction (deviation from intercept)
        Y_hat_color = C_test @ W_color  # (1, V_s)

        # Actual deviation from intercept
        Y_dev = X_test - b[np.newaxis, :]  # (1, V_s)

        r = voxel_pattern_correlation(Y_hat_color, Y_dev)
        corrs.append(r[0])
    return float(np.mean(corrs))


def loco_standard_meansubt(amp, C_full, alpha):
    """Standard model but evaluate after subtracting training-set mean prediction.

    This is a control: if this gives same p as standard, confirms centering commutes.
    """
    corrs = []
    for tc in range(N_COLORS):
        train = [c for c in range(N_COLORS) if c != tc]
        X_train = amp[:, train, :].reshape(-1, amp.shape[2])
        C_train = np.tile(C_full[train], (N_RUNS, 1))
        X_test = amp[:, tc, :].mean(axis=0, keepdims=True)
        C_test = C_full[tc:tc+1]

        W = fit_W_ridge(C_train, X_train, alpha)

        # Predict all training colors and compute mean prediction
        Y_hat_train = C_full[train] @ W  # (7, V_s)
        mean_pred = Y_hat_train.mean(axis=0, keepdims=True)  # (1, V_s)

        # Mean actual training pattern
        mean_actual = amp[:, train, :].mean(axis=(0, 1), keepdims=False)[np.newaxis, :]

        # Deviation evaluation
        Y_hat_dev = (C_test @ W) - mean_pred
        Y_real_dev = X_test - mean_actual

        r = voxel_pattern_correlation(Y_hat_dev, Y_real_dev)
        corrs.append(r[0])
    return float(np.mean(corrs))


# ============================================================================
# Permutation engine
# ============================================================================

def run_perm_test(amp, C_full, alpha, loco_func, n_perm, rng):
    """Run permutation test for a given LOCO function."""
    observed = loco_func(amp, C_full, alpha)

    null_dist = np.zeros(n_perm)
    for i in range(n_perm):
        perm = rng.permutation(N_COLORS)
        amp_perm = amp[:, perm, :]
        null_dist[i] = loco_func(amp_perm, C_full, alpha)

    p = float(np.mean(null_dist >= observed))
    return {
        'observed': float(observed),
        'null_mean': float(np.mean(null_dist)),
        'null_sd': float(np.std(null_dist)),
        'p_perm': p,
    }


# ============================================================================
# Main
# ============================================================================

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(RNG_SEED)

    methods = [
        ('standard',    loco_standard),
        ('intercept',   loco_intercept_deviation),
        ('mean_subt',   loco_standard_meansubt),
    ]

    print(f'Intercept permutation test: {N_PERM} shuffles')
    print(f'Methods: {[m[0] for m in methods]}')
    print()

    all_results = {}

    for roi in ROIS:
        basis_label, basis_type, n_channels = ROI_BASES[roi]
        C_full = create_basis_matrix(HUE_ANGLES, n_channels, basis_type)

        all_results[roi] = {'basis': basis_label}
        print(f'=== {roi} ({basis_label}) ===')

        for method_name, loco_func in methods:
            all_results[roi][method_name] = {}

            subj_results = []
            for subj in HC_SUBJECTS:
                amp = load_amplitudes(BASELINE_DIR, subj, roi)

                # Select alpha on full data (same for all methods)
                X_all = amp.reshape(-1, amp.shape[2])
                C_all = np.tile(C_full, (N_RUNS, 1))
                alpha, _ = gcv_select_alpha(C_all, X_all)

                res = run_perm_test(amp, C_full, alpha, loco_func, N_PERM, rng)
                all_results[roi][method_name][subj] = res
                subj_results.append(res)

            # Stouffer combined p
            p_vals = [r['p_perm'] for r in subj_results]
            z_scores = [sp_stats.norm.ppf(1 - p) if 0 < p < 1 else
                        (3.5 if p == 0 else -3.5) for p in p_vals]
            z_stouffer = np.sum(z_scores) / np.sqrt(len(z_scores))
            p_stouffer = 1 - sp_stats.norm.cdf(z_stouffer)

            obs_mean = np.mean([r['observed'] for r in subj_results])
            null_mean = np.mean([r['null_mean'] for r in subj_results])
            delta = obs_mean - null_mean

            sig = '***' if p_stouffer < 0.001 else '**' if p_stouffer < 0.01 else \
                  '*' if p_stouffer < 0.05 else '†' if p_stouffer < 0.1 else ''

            print(f'  {method_name:<12}: obs={obs_mean:+.3f}  null={null_mean:+.3f}  '
                  f'Δ={delta:+.3f}  p_stouffer={p_stouffer:.4f} {sig}')

        print()

    # Save
    out_path = OUTPUT_DIR / 'intercept_permutation_10K.json'
    with open(out_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f'Saved to {out_path}')

    # === Summary ===
    print('\n' + '=' * 80)
    print('SUMMARY')
    print('=' * 80)
    print(f'{"ROI":<5} {"Basis":<7} {"Method":<12} {"Obs":>7} {"Null":>7} '
          f'{"Δ":>7} {"p_stouf":>8}')

    for roi in ROIS:
        basis = all_results[roi]['basis']
        for method_name, _ in methods:
            obs = np.mean([all_results[roi][method_name][s]['observed']
                           for s in HC_SUBJECTS])
            null = np.mean([all_results[roi][method_name][s]['null_mean']
                            for s in HC_SUBJECTS])
            p_vals = [all_results[roi][method_name][s]['p_perm']
                      for s in HC_SUBJECTS]
            z_scores = [sp_stats.norm.ppf(1 - p) if 0 < p < 1 else
                        (3.5 if p == 0 else -3.5) for p in p_vals]
            z_stouffer = np.sum(z_scores) / np.sqrt(len(z_scores))
            p_stouffer = 1 - sp_stats.norm.cdf(z_stouffer)
            delta = obs - null
            sig = '***' if p_stouffer < 0.001 else '**' if p_stouffer < 0.01 else \
                  '*' if p_stouffer < 0.05 else '†' if p_stouffer < 0.1 else ''
            print(f'{roi:<5} {basis:<7} {method_name:<12} {obs:>+7.3f} {null:>+7.3f} '
                  f'{delta:>+7.3f} {p_stouffer:>8.4f} {sig}')
        print()


if __name__ == '__main__':
    main()
