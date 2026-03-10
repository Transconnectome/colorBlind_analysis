#!/usr/bin/env python3
"""Validate improved encoding methods: RRR + Channel-Smoothness.

Runs LOCO evaluation with additional encoding methods and metrics.
Compares: ridge_gcv (baseline), ridge_rrr (r=2,3,4), ridge_smooth (beta grid).
Additional metrics: RDM prediction correlation, identification accuracy.

Usage:
    python validate_improved_encoding.py --subject 01 \
        --baseline_dir /path/to/C010 --output_dir results/improved_encoding
"""

import argparse
import json
import numpy as np
from pathlib import Path
from scipy.spatial.distance import pdist, squareform
from scipy.stats import spearmanr

from utils_forward_model import (
    load_amplitudes, create_basis_matrix, create_basis_full,
    fit_W_ridge, fit_W_ridge_rrr, fit_W_smooth_ridge,
    gcv_select_alpha, predict_patterns, voxel_pattern_correlation,
    explained_variance, decode_hue, circular_distance, compute_rdm,
    rdm_upper_tri, save_config,
    HUE_ANGLES, N_RUNS, N_COLORS, N_CHANNELS, ROIS, ALPHA_GRID
)


# ============================================================================
# Additional Metrics
# ============================================================================

def rdm_prediction_correlation(W, C, X_mean):
    """Compute correlation between predicted and actual RDMs.

    Args:
        W: (K, V_s) encoding weights
        C: (8, K) full basis matrix (all 8 colors)
        X_mean: (8, V_s) run-averaged actual patterns

    Returns:
        r_pearson, r_spearman: RDM correlation values
    """
    Y_hat = C @ W  # (8, V_s) predicted patterns
    rdm_pred = squareform(pdist(Y_hat, 'correlation'))
    rdm_real = squareform(pdist(X_mean, 'correlation'))

    # Upper triangle
    mask = np.triu(np.ones(rdm_pred.shape, dtype=bool), k=1)
    v_pred = rdm_pred[mask]
    v_real = rdm_real[mask]

    r_pearson = float(np.corrcoef(v_pred, v_real)[0, 1])
    r_spearman = float(spearmanr(v_pred, v_real).correlation)
    return r_pearson, r_spearman


def identification_accuracy(W, C, X_test_runs, test_color_idx):
    """Prediction identification: is the predicted pattern closest to the correct color?

    For each run, predict pattern for the held-out color, compare against
    all 8 actual run patterns. Correct if held-out color is nearest neighbor.

    Args:
        W: (K, V_s) encoding weights
        C: (8, K) full basis matrix
        X_test_runs: (6, V_s) actual patterns for held-out color (all runs)
        test_color_idx: int, index of held-out color

    Returns:
        accuracy: float, fraction of runs correctly identified (chance = 1/8)
    """
    Y_hat = C @ W  # (8, V_s) predicted for all 8 colors
    pred_held = Y_hat[test_color_idx]  # (V_s,) predicted for held-out

    correct = 0
    for run_pattern in X_test_runs:
        # Correlate predicted held-out pattern with each actual color prediction
        sims = np.array([np.corrcoef(pred_held, Y_hat[c])[0, 1]
                         for c in range(N_COLORS)])
        # But we should compare against ACTUAL patterns, not predicted ones.
        # The question: does the predicted held-out pattern look most like
        # the actual held-out run data?
        # Compare run_pattern against all 8 predicted patterns
        sims = np.array([np.corrcoef(run_pattern, Y_hat[c])[0, 1]
                         for c in range(N_COLORS)])
        if np.nanargmax(sims) == test_color_idx:
            correct += 1
    return correct / len(X_test_runs)


def voxel_reliability_weighted_corr(Y_pred, Y_real, amp):
    """Voxel-reliability-weighted pattern correlation.

    Weight each voxel by its split-half reliability before computing
    pattern correlation.

    Args:
        Y_pred: (1, V_s) predicted pattern
        Y_real: (1, V_s) actual pattern (run-averaged)
        amp: (6, 8, V_s) full amplitude data

    Returns:
        r_weighted: reliability-weighted correlation
    """
    V_s = amp.shape[2]
    # Split-half reliability per voxel: corr(odd_runs_mean, even_runs_mean)
    odd_mean = amp[::2].mean(axis=0)    # (8, V_s) mean of runs 0,2,4
    even_mean = amp[1::2].mean(axis=0)  # (8, V_s) mean of runs 1,3,5

    # Per-voxel reliability: correlation across 8 colors
    rel = np.zeros(V_s)
    for v in range(V_s):
        c = np.corrcoef(odd_mean[:, v], even_mean[:, v])
        rel[v] = max(c[0, 1], 0) if np.isfinite(c[0, 1]) else 0

    # Weighted correlation
    w = rel / (rel.sum() + 1e-10)
    p = Y_pred.ravel()
    r = Y_real.ravel()
    p_w = p - np.sum(w * p)
    r_w = r - np.sum(w * r)
    cov = np.sum(w * p_w * r_w)
    std_p = np.sqrt(np.sum(w * p_w ** 2))
    std_r = np.sqrt(np.sum(w * r_w ** 2))
    return float(cov / (std_p * std_r)) if std_p * std_r > 0 else 0.0


# ============================================================================
# LOCO Evaluation
# ============================================================================

def run_loco_improved(amp, method_name, method_params):
    """Run LOCO for a single method.

    Args:
        amp: (6, 8, V_s)
        method_name: str
        method_params: dict of method-specific parameters

    Returns:
        results: dict with metrics
    """
    C = create_basis_matrix(HUE_ANGLES, N_CHANNELS, 'fe')
    basis_full = create_basis_full(N_CHANNELS, 'fe')
    X_mean_all = amp.mean(axis=0)  # (8, V_s) run-averaged

    fold_corrs = []
    fold_r2s = []
    fold_maes = []
    fold_ids = []
    fold_weighted = []

    for test_color in range(N_COLORS):
        train_colors = [c for c in range(N_COLORS) if c != test_color]
        C_train = C[train_colors]

        # Pool all runs for training
        X_train = amp[:, train_colors, :].reshape(-1, amp.shape[2])
        C_train_tiled = np.tile(C_train, (N_RUNS, 1))

        # Fit W
        if method_name == 'ridge_gcv':
            alpha, _ = gcv_select_alpha(C_train_tiled, X_train)
            W = fit_W_ridge(C_train_tiled, X_train, alpha)

        elif method_name.startswith('ridge_rrr_r'):
            rank = int(method_name.split('_r')[-1])
            alpha, _ = gcv_select_alpha(C_train_tiled, X_train)
            W = fit_W_ridge_rrr(C_train_tiled, X_train, alpha, rank)

        elif method_name == 'ridge_smooth':
            alpha, _ = gcv_select_alpha(C_train_tiled, X_train)
            beta = method_params.get('beta', 1.0)
            W = fit_W_smooth_ridge(C_train_tiled, X_train, alpha, beta)

        elif method_name == 'ridge_rrr_smooth':
            alpha, _ = gcv_select_alpha(C_train_tiled, X_train)
            beta = method_params.get('beta', 1.0)
            rank = method_params.get('rank', 3)
            W_smooth = fit_W_smooth_ridge(C_train_tiled, X_train, alpha, beta)
            # SVD truncation on smooth solution
            U, s, Vt = np.linalg.svd(W_smooth, full_matrices=False)
            r = min(rank, len(s))
            W = (U[:, :r] * s[:r][np.newaxis, :]) @ Vt[:r, :]

        else:
            raise ValueError(f'Unknown method: {method_name}')

        # Evaluate held-out color
        C_test = C[test_color:test_color + 1]
        X_test = amp[:, test_color, :]   # (6, V_s)
        X_mean = X_test.mean(axis=0, keepdims=True)  # (1, V_s)
        Y_hat = predict_patterns(W, C_test)  # (1, V_s)

        # Standard metrics
        r = voxel_pattern_correlation(Y_hat, X_mean)
        r2 = explained_variance(Y_hat, X_mean)
        fold_corrs.append(float(np.mean(r)))
        fold_r2s.append(float(np.mean(r2)))

        # MAE
        pred_hues = decode_hue(W, basis_full, X_test)
        true_hue = HUE_ANGLES[test_color]
        errors = circular_distance(
            np.full(len(pred_hues), true_hue), pred_hues)
        fold_maes.append(float(np.nanmean(errors)))

        # Identification accuracy
        acc = identification_accuracy(W, C, X_test, test_color)
        fold_ids.append(acc)

        # Reliability-weighted correlation
        rw = voxel_reliability_weighted_corr(Y_hat, X_mean, amp)
        fold_weighted.append(rw)

    # RDM prediction (using W fit on ALL 8 colors for holistic RDM metric)
    X_train_full = amp.reshape(-1, amp.shape[2])
    C_full_tiled = np.tile(C, (N_RUNS, 1))
    if method_name == 'ridge_gcv':
        alpha_full, _ = gcv_select_alpha(C_full_tiled, X_train_full)
        W_full = fit_W_ridge(C_full_tiled, X_train_full, alpha_full)
    elif method_name.startswith('ridge_rrr_r'):
        rank = int(method_name.split('_r')[-1])
        alpha_full, _ = gcv_select_alpha(C_full_tiled, X_train_full)
        W_full = fit_W_ridge_rrr(C_full_tiled, X_train_full, alpha_full, rank)
    elif method_name == 'ridge_smooth':
        alpha_full, _ = gcv_select_alpha(C_full_tiled, X_train_full)
        beta = method_params.get('beta', 1.0)
        W_full = fit_W_smooth_ridge(C_full_tiled, X_train_full, alpha_full, beta)
    elif method_name == 'ridge_rrr_smooth':
        alpha_full, _ = gcv_select_alpha(C_full_tiled, X_train_full)
        beta = method_params.get('beta', 1.0)
        rank = method_params.get('rank', 3)
        W_s = fit_W_smooth_ridge(C_full_tiled, X_train_full, alpha_full, beta)
        U, s, Vt = np.linalg.svd(W_s, full_matrices=False)
        r = min(rank, len(s))
        W_full = (U[:, :r] * s[:r][np.newaxis, :]) @ Vt[:r, :]
    else:
        W_full = fit_W_ridge(C_full_tiled, X_train_full, 1.0)

    rdm_r, rdm_rho = rdm_prediction_correlation(W_full, C, X_mean_all)

    return {
        'mean_voxel_corr': float(np.mean(fold_corrs)),
        'mean_R2': float(np.mean(fold_r2s)),
        'mean_mae': float(np.mean(fold_maes)),
        'mean_id_accuracy': float(np.mean(fold_ids)),
        'mean_weighted_corr': float(np.mean(fold_weighted)),
        'rdm_pred_pearson': rdm_r,
        'rdm_pred_spearman': rdm_rho,
        'per_color_corr': fold_corrs,
        'per_color_mae': fold_maes,
        'per_color_id_accuracy': fold_ids,
    }


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Validate improved encoding methods (LOCO)')
    parser.add_argument('--subject', required=True)
    parser.add_argument('--baseline_dir', required=True)
    parser.add_argument('--output_dir', default='results/improved_encoding')
    parser.add_argument('--rois', nargs='+', default=ROIS)
    parser.add_argument('--beta_grid', nargs='+', type=float,
                        default=[0.01, 0.1, 1.0, 10.0, 100.0])
    parser.add_argument('--ranks', nargs='+', type=int, default=[2, 3, 4])
    args = parser.parse_args()

    subj = args.subject.zfill(2)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Methods to evaluate
    methods = {}
    # Baseline
    methods['ridge_gcv'] = {}
    # RRR variants
    for r in args.ranks:
        methods[f'ridge_rrr_r{r}'] = {}
    # Smoothness: best beta via internal comparison
    for beta in args.beta_grid:
        methods[f'ridge_smooth_b{beta}'] = {'beta': beta}

    print(f'Subject: sub-{subj}')
    print(f'Methods: {list(methods.keys())}')
    print(f'ROIs: {args.rois}')

    all_results = {}

    for roi in args.rois:
        print(f'\n{"="*50} {roi} {"="*50}')

        try:
            amp = load_amplitudes(args.baseline_dir, subj, roi)
        except FileNotFoundError as e:
            print(f'  ERROR: {e}')
            continue

        V_s = amp.shape[2]
        print(f'  V_s = {V_s}')

        roi_results = {}

        for method_name, params in methods.items():
            # For smooth methods, extract beta
            if method_name.startswith('ridge_smooth_b'):
                actual_name = 'ridge_smooth'
                beta_val = float(method_name.split('_b')[-1])
                actual_params = {'beta': beta_val}
            else:
                actual_name = method_name
                actual_params = params

            result = run_loco_improved(amp, actual_name, actual_params)
            roi_results[method_name] = result

            print(f'  {method_name:25s}: voxel_r={result["mean_voxel_corr"]:+.4f}  '
                  f'MAE={result["mean_mae"]:5.1f}  '
                  f'id_acc={result["mean_id_accuracy"]:.3f}  '
                  f'w_corr={result["mean_weighted_corr"]:+.4f}  '
                  f'rdm_r={result["rdm_pred_pearson"]:.3f}')

        # Pick best smoothness beta
        smooth_methods = {k: v for k, v in roi_results.items()
                         if k.startswith('ridge_smooth_b')}
        if smooth_methods:
            best_smooth = max(smooth_methods, key=lambda k:
                              smooth_methods[k]['mean_voxel_corr'])
            best_beta = float(best_smooth.split('_b')[-1])
            print(f'\n  Best smooth beta for {roi}: {best_beta} '
                  f'(r={smooth_methods[best_smooth]["mean_voxel_corr"]:+.4f})')
            # Store best smooth as 'ridge_smooth_best'
            roi_results['ridge_smooth_best'] = roi_results[best_smooth].copy()
            roi_results['ridge_smooth_best']['best_beta'] = best_beta

            # Try combined: best_smooth + best RRR rank
            rrr_methods = {k: v for k, v in roi_results.items()
                           if k.startswith('ridge_rrr_r')}
            if rrr_methods:
                best_rrr = max(rrr_methods, key=lambda k:
                               rrr_methods[k]['mean_voxel_corr'])
                best_rank = int(best_rrr.split('_r')[-1])

                combo_result = run_loco_improved(
                    amp, 'ridge_rrr_smooth',
                    {'beta': best_beta, 'rank': best_rank})
                combo_name = f'ridge_rrr_r{best_rank}_smooth_b{best_beta}'
                roi_results[combo_name] = combo_result
                print(f'  Combined (r={best_rank}, β={best_beta}): '
                      f'voxel_r={combo_result["mean_voxel_corr"]:+.4f}  '
                      f'MAE={combo_result["mean_mae"]:5.1f}')

        all_results[roi] = roi_results

    # Save
    out_path = output_dir / f'sub-{subj}_improved.json'
    with open(out_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f'\nSaved: {out_path}')

    # Summary table
    print(f'\n{"="*70}')
    print(f'SUMMARY: sub-{subj} LOCO voxel_corr')
    print(f'{"="*70}')
    key_methods = ['ridge_gcv'] + [f'ridge_rrr_r{r}' for r in args.ranks]
    if any(roi_results.get('ridge_smooth_best') for roi_results in all_results.values()):
        key_methods.append('ridge_smooth_best')

    header = f'{"Method":>28}'
    for roi in args.rois:
        if roi in all_results:
            header += f'  {roi:>8}'
    print(header)
    print('-' * 70)

    for method in key_methods:
        line = f'{method:>28}'
        for roi in args.rois:
            if roi in all_results and method in all_results[roi]:
                v = all_results[roi][method]['mean_voxel_corr']
                line += f'  {v:>+8.4f}'
            else:
                line += f'  {"N/A":>8}'
        print(line)

    save_config(output_dir,
                step='validate_improved_encoding',
                subject=subj,
                methods=list(methods.keys()),
                rois=args.rois,
                beta_grid=args.beta_grid,
                ranks=args.ranks,
                baseline_dir=str(args.baseline_dir))


if __name__ == '__main__':
    main()
