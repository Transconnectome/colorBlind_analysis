#!/usr/bin/env python3
"""
permutation_test_centered.py — Re-Optimized Permutation Test for smooth_tikh.

Fixes the key problem in the original smooth_tikh permutation test:
  The original test used FIXED hyperparameters (alpha=0.01, beta=100) selected
  on real data for all 10K permutations. This biases the null distribution
  because beta=100 was chosen to match real color structure. On shuffled data,
  the optimal beta should be lower (smoothness doesn't help random labels).

Fix: Re-select (alpha, beta) via inner LOCO-CV within EACH permutation.
  On shuffled data, inner CV should select lower beta → null predictions lose
  the spatial covariance boost → proper null distribution.

Models tested:
  1. ridge_gcv: Baseline (GCV alpha, no smoothness). Already validated (hV4 p=0.044).
  2. smooth_fixed: smooth_tikh with fixed (alpha=0.01, beta=100). Original test (replication).
  3. smooth_reopt: smooth_tikh with per-permutation re-optimized (alpha, beta). THE FIX.

Diagnostic output:
  - Per-permutation selected (alpha, beta) for smooth_reopt
  - Distribution of selected beta under null → expected: beta lower than 100

Algorithm per permutation:
  1. For each HC subject: perm = rng.permutation(8) -> amp_shuffled = amp[:, perm, :]
  2. LOCO on shuffled data:
     - For smooth_reopt: run inner LOCO-CV to select best (alpha, beta)
     - For smooth_fixed: use provided (alpha, beta)
     - For ridge_gcv: use GCV alpha
  3. Mean voxel_corr across 8 folds -> subject-level null LOCO_r
  4. Mean across HC subjects -> group-level null statistic
  5. After N perms: p_perm = (sum(null >= observed) + 1) / (N + 1)

Computational cost:
  K=6 → 6x6 matrix inverse per solve (negligible).
  smooth_reopt: 10K perms × 7 subjects × 8 LOCO folds × 25 grid × 7 inner folds
              = ~98M tiny solves per ROI. Each is O(K^3 + K^2 * V_s) ≈ microseconds.
  Estimated: 30-60 min per ROI (dominated by Python overhead).

Usage:
    python permutation_test_centered.py \
        --baseline_dir /path/to/full_dataset_C010 \
        --output_dir ../results/permutation_reopt \
        --n_perms 10000 --seed 42

    # Quick test:
    python permutation_test_centered.py \
        --baseline_dir /path/to/full_dataset_C010 \
        --output_dir ../results/permutation_reopt \
        --n_perms 100 --seed 42 --quick
"""

import argparse
import json
import time
import numpy as np
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from utils_forward_model import (
    HC_SUBJECTS, ROIS, N_RUNS, N_COLORS, N_CHANNELS,
    HUE_ANGLES, ALPHA_GRID,
    load_amplitudes, create_basis_matrix,
    fit_W_ridge, fit_W_smooth_ridge, gcv_select_alpha,
    predict_patterns, voxel_pattern_correlation,
    select_smooth_tikh_params,
    save_config,
)

ROI_DISPLAY = {'V1': 'V1', 'V2': 'V2', 'V3': 'V3', 'V4': 'hV4'}

# Default smooth_tikh params (from original analysis)
DEFAULT_ALPHA = 0.01
DEFAULT_BETA = 100.0

# Grid for re-optimization (5 × 5 = 25 points)
REOPT_ALPHA_GRID = [0.001, 0.01, 0.1, 1.0, 10.0]
REOPT_BETA_GRID = [0, 1, 10, 100, 1000]


# ============================================================================
# LOCO procedures
# ============================================================================

def loco_ridge_gcv(amp, C_full):
    """Standard 8-fold LOCO with GCV-ridge.

    Args:
        amp: (6, 8, V_s) amplitudes (raw or shuffled)
        C_full: (8, K) design matrix

    Returns:
        mean_voxel_corr: float
    """
    V_s = amp.shape[2]
    fold_corrs = np.zeros(N_COLORS)

    for test_color in range(N_COLORS):
        train_colors = [c for c in range(N_COLORS) if c != test_color]
        C_train_row = C_full[train_colors]
        X_train = amp[:, train_colors, :].reshape(-1, V_s)
        C_train = np.tile(C_train_row, (N_RUNS, 1))

        best_alpha, _ = gcv_select_alpha(C_train, X_train, ALPHA_GRID)
        W = fit_W_ridge(C_train, X_train, best_alpha)

        C_test = C_full[test_color:test_color + 1]
        Y_hat = predict_patterns(W, C_test)
        X_test_mean = amp[:, test_color, :].mean(axis=0, keepdims=True)

        r = voxel_pattern_correlation(Y_hat, X_test_mean)
        fold_corrs[test_color] = r[0]

    return float(np.mean(fold_corrs))


def loco_smooth_fixed(amp, C_full, alpha, beta):
    """LOCO with smooth_tikh (fixed params).

    Args:
        amp: (6, 8, V_s) amplitudes
        C_full: (8, K) design matrix
        alpha, beta: fixed hyperparameters

    Returns:
        mean_voxel_corr: float
    """
    V_s = amp.shape[2]
    fold_corrs = np.zeros(N_COLORS)

    for test_color in range(N_COLORS):
        train_colors = [c for c in range(N_COLORS) if c != test_color]
        C_train_row = C_full[train_colors]
        X_train = amp[:, train_colors, :].reshape(-1, V_s)
        C_train = np.tile(C_train_row, (N_RUNS, 1))

        W = fit_W_smooth_ridge(C_train, X_train, alpha, beta)

        C_test = C_full[test_color:test_color + 1]
        Y_hat = predict_patterns(W, C_test)
        X_test_mean = amp[:, test_color, :].mean(axis=0, keepdims=True)

        r = voxel_pattern_correlation(Y_hat, X_test_mean)
        fold_corrs[test_color] = r[0]

    return float(np.mean(fold_corrs))


def loco_smooth_reopt(amp, C_full, alpha_grid, beta_grid):
    """LOCO with smooth_tikh (re-optimized params per subject).

    For each LOCO fold, selects best (alpha, beta) via inner LOCO-CV
    on the run-averaged 7 training colors.

    Args:
        amp: (6, 8, V_s) amplitudes
        C_full: (8, K) design matrix
        alpha_grid, beta_grid: grids for hyperparameter selection

    Returns:
        mean_voxel_corr: float
        selected_params: list of (alpha, beta) per fold
    """
    V_s = amp.shape[2]
    fold_corrs = np.zeros(N_COLORS)
    selected_params = []

    amp_mean = amp.mean(axis=0)  # (8, V_s) for inner CV

    for test_color in range(N_COLORS):
        train_colors = [c for c in range(N_COLORS) if c != test_color]
        C_train_row = C_full[train_colors]

        # Inner CV: select (alpha, beta) on run-averaged 7-color data
        amp_mean_train = amp_mean[train_colors]
        best_alpha, best_beta, _, _ = select_smooth_tikh_params(
            C_train_row, amp_mean_train,
            alpha_grid=alpha_grid, beta_grid=beta_grid,
            center=False
        )
        selected_params.append((best_alpha, best_beta))

        # Fit on full (all runs) training data with selected params
        X_train = amp[:, train_colors, :].reshape(-1, V_s)
        C_train = np.tile(C_train_row, (N_RUNS, 1))
        W = fit_W_smooth_ridge(C_train, X_train, best_alpha, best_beta)

        C_test = C_full[test_color:test_color + 1]
        Y_hat = predict_patterns(W, C_test)
        X_test_mean = amp[:, test_color, :].mean(axis=0, keepdims=True)

        r = voxel_pattern_correlation(Y_hat, X_test_mean)
        fold_corrs[test_color] = r[0]

    return float(np.mean(fold_corrs)), selected_params


# ============================================================================
# Permutation test
# ============================================================================

def run_permutation_test(baseline_dir, output_dir, n_perms, seed, rois,
                          models=None):
    """Run permutation test for specified models.

    Args:
        baseline_dir: path to full_dataset_C010
        output_dir: output directory
        n_perms: number of permutations
        seed: random seed
        rois: list of ROI keys
        models: list of model names. Default: all three.
    """
    if models is None:
        models = ['ridge_gcv', 'smooth_fixed', 'smooth_reopt']

    rng = np.random.default_rng(seed)
    C_full = create_basis_matrix(HUE_ANGLES, N_CHANNELS, 'fe')

    all_results = {}

    for roi in rois:
        roi_disp = ROI_DISPLAY[roi]
        print(f'\n{"=" * 60}')
        print(f'  ROI: {roi_disp}')
        print(f'{"=" * 60}')

        # Load HC amplitudes
        hc_amps = {}
        for subj in HC_SUBJECTS:
            try:
                amp = load_amplitudes(baseline_dir, subj, roi)
                hc_amps[subj] = amp
            except FileNotFoundError:
                print(f'  Warning: missing sub-{subj} {roi}')

        available_subjects = list(hc_amps.keys())
        n_subj = len(available_subjects)
        print(f'  Loaded {n_subj} HC subjects')

        if n_subj == 0:
            continue

        roi_results = {}

        for model_name in models:
            print(f'\n  --- Model: {model_name} ---')

            # ---- Compute observed statistic ----
            obs_subj_corrs = np.zeros(n_subj)
            obs_params = {}

            for s_idx, subj in enumerate(available_subjects):
                amp = hc_amps[subj]

                if model_name == 'ridge_gcv':
                    obs_subj_corrs[s_idx] = loco_ridge_gcv(amp, C_full)
                elif model_name == 'smooth_fixed':
                    obs_subj_corrs[s_idx] = loco_smooth_fixed(
                        amp, C_full, DEFAULT_ALPHA, DEFAULT_BETA)
                elif model_name == 'smooth_reopt':
                    score, params = loco_smooth_reopt(
                        amp, C_full, REOPT_ALPHA_GRID, REOPT_BETA_GRID)
                    obs_subj_corrs[s_idx] = score
                    obs_params[subj] = [(float(a), float(b)) for a, b in params]

            observed = float(np.mean(obs_subj_corrs))
            print(f'  Observed HC mean: {observed:.4f}')
            print(f'  Per-subject: '
                  + ', '.join(f'{subj}={obs_subj_corrs[i]:.4f}'
                              for i, subj in enumerate(available_subjects)))

            # ---- Permutation loop ----
            null_dist = np.zeros(n_perms)
            # Track selected betas for diagnostic (smooth_reopt only)
            if model_name == 'smooth_reopt':
                perm_betas = []
            t0 = time.time()

            for perm_i in range(n_perms):
                subj_corrs = np.zeros(n_subj)

                for s_idx, subj in enumerate(available_subjects):
                    amp = hc_amps[subj]
                    perm = rng.permutation(N_COLORS)
                    amp_shuffled = amp[:, perm, :]

                    if model_name == 'ridge_gcv':
                        subj_corrs[s_idx] = loco_ridge_gcv(
                            amp_shuffled, C_full)
                    elif model_name == 'smooth_fixed':
                        subj_corrs[s_idx] = loco_smooth_fixed(
                            amp_shuffled, C_full, DEFAULT_ALPHA, DEFAULT_BETA)
                    elif model_name == 'smooth_reopt':
                        score, params = loco_smooth_reopt(
                            amp_shuffled, C_full,
                            REOPT_ALPHA_GRID, REOPT_BETA_GRID)
                        subj_corrs[s_idx] = score
                        # Track beta selections (first permutation only, for speed)
                        if perm_i < 10:
                            perm_betas.append([p[1] for p in params])

                null_dist[perm_i] = np.mean(subj_corrs)

                if (perm_i + 1) % 200 == 0:
                    elapsed = time.time() - t0
                    rate = (perm_i + 1) / elapsed
                    eta = (n_perms - perm_i - 1) / rate
                    current_null_mean = np.mean(null_dist[:perm_i + 1])
                    print(f'    [{perm_i+1:>5}/{n_perms}] '
                          f'null_mean={current_null_mean:.4f}, '
                          f'{rate:.1f} perm/s, ETA {eta:.0f}s')

            elapsed = time.time() - t0

            # p-value (conservative: +1 in numerator and denominator)
            p_perm = float((np.sum(null_dist >= observed) + 1) / (n_perms + 1))
            null_mean = float(np.mean(null_dist))
            null_sd = float(np.std(null_dist))
            null_ci = (float(np.percentile(null_dist, 2.5)),
                       float(np.percentile(null_dist, 97.5)))

            sig = '*' if p_perm < 0.05 else ''
            print(f'  p_perm = {p_perm:.4f}{sig} ({elapsed:.1f}s)')
            print(f'  Null: mean={null_mean:.4f}, SD={null_sd:.4f}, '
                  f'95%CI=[{null_ci[0]:.4f}, {null_ci[1]:.4f}]')
            print(f'  delta(obs - null_mean) = {observed - null_mean:+.4f}')

            # Save null distribution
            np.save(output_dir / f'null_{model_name}_{roi_disp}.npy', null_dist)

            # Plot
            plot_permutation(null_dist, observed, p_perm, roi_disp,
                             model_name, output_dir)

            result_entry = {
                'model': model_name,
                'observed': observed,
                'per_subject_observed': {
                    subj: float(obs_subj_corrs[i])
                    for i, subj in enumerate(available_subjects)
                },
                'p_perm': p_perm,
                'n_perms': n_perms,
                'null_mean': null_mean,
                'null_sd': null_sd,
                'null_ci_95': null_ci,
                'delta_obs_null': float(observed - null_mean),
                'n_subjects': n_subj,
                'elapsed_s': round(elapsed, 1),
            }

            if model_name == 'smooth_fixed':
                result_entry['params'] = {
                    'alpha': DEFAULT_ALPHA, 'beta': DEFAULT_BETA}
            elif model_name == 'smooth_reopt':
                result_entry['param_grid'] = {
                    'alpha': REOPT_ALPHA_GRID, 'beta': REOPT_BETA_GRID}
                result_entry['observed_selected_params'] = obs_params
                if perm_betas:
                    # Diagnostic: what beta values are selected on shuffled data?
                    all_betas = [b for fold_betas in perm_betas
                                 for b in fold_betas]
                    beta_dist = {}
                    for b in set(all_betas):
                        beta_dist[str(b)] = all_betas.count(b)
                    result_entry['null_beta_distribution_sample'] = beta_dist
                    print(f'  Null beta distribution (first 10 perms): {beta_dist}')

            roi_results[model_name] = result_entry

        all_results[roi_disp] = roi_results

    return all_results


def plot_permutation(null_dist, observed, p_perm, roi_display,
                     model_name, output_dir):
    """Histogram of null distribution with observed line."""
    fig, ax = plt.subplots(figsize=(8, 5))

    ax.hist(null_dist, bins=80, color='steelblue', alpha=0.7,
            edgecolor='white', linewidth=0.3, density=True,
            label='Null distribution')
    ax.axvline(observed, color='red', linewidth=2, linestyle='--',
               label=f'Observed = {observed:.4f}')

    ax.set_xlabel('Mean HC LOCO voxel correlation (r)', fontsize=11)
    ax.set_ylabel('Density', fontsize=11)

    model_label = model_name.replace('_', ' ').title()
    ax.set_title(f'{roi_display} — {model_label}\n'
                 f'Permutation p = {p_perm:.4f} (n={len(null_dist):,})',
                 fontsize=13, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(alpha=0.3)

    plt.tight_layout()
    out_path = output_dir / f'perm_{model_name}_{roi_display}.png'
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'  Saved: {out_path}')


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Re-optimized permutation test for smooth_tikh')
    parser.add_argument('--baseline_dir', type=str, required=True,
                        help='Path to full_dataset_C010')
    parser.add_argument('--output_dir', type=str, required=True,
                        help='Output directory for results')
    parser.add_argument('--n_perms', type=int, default=10000,
                        help='Number of permutations (default: 10000)')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed')
    parser.add_argument('--rois', nargs='+', default=['V1', 'V2', 'V3', 'V4'],
                        help='ROIs to test')
    parser.add_argument('--models', nargs='+', default=None,
                        choices=['ridge_gcv', 'smooth_fixed', 'smooth_reopt'],
                        help='Models to test (default: all)')
    parser.add_argument('--quick', action='store_true',
                        help='Quick mode: only smooth_reopt')
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    models = args.models
    if args.quick:
        models = ['smooth_reopt']

    print('=' * 60)
    print('Re-Optimized Permutation Test (Section 9i-2)')
    print(f'  n_perms = {args.n_perms}, seed = {args.seed}')
    print(f'  Models: {models or "all (ridge_gcv, smooth_fixed, smooth_reopt)"}')
    print(f'  ROIs: {args.rois}')
    print(f'  Reopt grid: alpha={REOPT_ALPHA_GRID}, beta={REOPT_BETA_GRID}')
    print('=' * 60)

    all_results = run_permutation_test(
        baseline_dir=Path(args.baseline_dir),
        output_dir=output_dir,
        n_perms=args.n_perms,
        seed=args.seed,
        rois=args.rois,
        models=models,
    )

    # Save results JSON
    output = {
        'description': 'Re-optimized permutation test for smooth_tikh (Section 9i-2)',
        'fix_applied': ('Re-select (alpha, beta) via inner LOCO-CV within each '
                        'permutation instead of using fixed params from real data'),
        'rationale': ('Original test used fixed beta=100 for all shuffles. '
                      'This inflates the null because beta=100 captures spatial '
                      'covariance structure that persists under label shuffle. '
                      'Re-optimization should select lower beta on shuffled data.'),
        'n_perms': args.n_perms,
        'seed': args.seed,
        'default_smooth_params': {
            'alpha': DEFAULT_ALPHA, 'beta': DEFAULT_BETA},
        'reopt_grid': {
            'alpha': REOPT_ALPHA_GRID, 'beta': REOPT_BETA_GRID},
        'results': all_results,
    }
    out_path = output_dir / 'permutation_test_reopt.json'
    with open(out_path, 'w') as f:
        json.dump(output, f, indent=2)
    print(f'\nSaved: {out_path}')

    # Config
    save_config(output_dir,
                step='permutation_test_reopt',
                n_perms=args.n_perms,
                seed=args.seed,
                baseline_dir=str(args.baseline_dir),
                rois=args.rois,
                models=models)

    # Summary table
    print('\n' + '=' * 60)
    print('SUMMARY')
    print('=' * 60)
    print(f'{"ROI":<6} {"Model":<18} {"Observed":>9} {"Null Mean":>10} '
          f'{"Delta":>8} {"p_perm":>8}')
    print('-' * 62)

    for roi_disp, roi_res in all_results.items():
        for model_name, res in roi_res.items():
            sig = '*' if res['p_perm'] < 0.05 else ' '
            delta = res['observed'] - res['null_mean']
            print(f'{roi_disp:<6} {model_name:<18} '
                  f'{res["observed"]:>9.4f} {res["null_mean"]:>10.4f} '
                  f'{delta:>+8.4f} {res["p_perm"]:>7.4f}{sig}')

    # Comparison with original (uncentered fixed) results
    print('\n' + '-' * 62)
    print('Reference: Original smooth_tikh (fixed alpha=0.01, beta=100)')
    print('  V1: obs=0.189, null=0.187, p=0.331')
    print('  V2: obs=0.216, null=0.212, p=0.188')
    print('  V3: obs=0.125, null=0.128, p=0.613')
    print('  hV4: obs=0.239, null=0.241, p=0.613')

    print('\nDone.')


if __name__ == '__main__':
    main()
