#!/usr/bin/env python3
"""
Phase 2: Ridge-Regularized LOCO Forward Encoding

Stabilizes W estimation via Ridge penalty while keeping 6 channels.

Modes:
  fixed    : Test alpha grid on outer folds (diagnostic landscape, no selection)
  gcv      : GCV-based alpha selection per outer fold (proper evaluation)
  combined : GCV for alpha + leave-one-run-out for lambda (Ridge + Group Prior)

Usage (server):
    python loco_ridge.py --subject 01 --rois V1 V2 V3 V4 --mode fixed
    python loco_ridge.py --subject 01 --rois V1 V2 V3 V4 --mode gcv
    python loco_ridge.py --subject 01 --rois V1 V2 V3 V4 --mode combined

Output:
    results/ridge/sub-{ID}_ridge_{mode}.json
"""

import sys
import argparse
import json
import numpy as np
from pathlib import Path
from datetime import datetime
from collections import Counter

# Resolve paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
RESULTS_DIR = PROJECT_DIR / 'results' / 'ridge'
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Import shared utilities from model_comparison_validation
MCV_DIR = SCRIPT_DIR.parents[1] / 'model_comparison_validation' / 'scripts'
sys.path.insert(0, str(MCV_DIR))
from loco_baseline import (
    load_amplitudes, circular_distance, HUE_ANGLES,
)

# Import basis functions
import importlib.util
_spec = importlib.util.spec_from_file_location(
    'utils_color_decoding',
    SCRIPT_DIR.parents[2] / 'utils' / 'utils_color_decoding.py'
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
create_basis_functions = _mod.create_basis_functions

# Constants
HC_SUBJECTS = [f'{i:02d}' for i in range(1, 8)]
CVD_SUBJECTS = [f'{i:02d}' for i in range(8, 11)]
ROIS = ['V1', 'V2', 'V3', 'V4']
ALPHA_GRID = [0.001, 0.01, 0.1, 1.0, 10.0, 100.0, 1000.0]
LAMBDA_GRID = [0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0]

# Default data path (server)
BASELINE_DIR = Path('/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010')


# ============================================================================
# Core Functions
# ============================================================================

def fit_W(X, hues, n_channels=6, alpha=0):
    """Fit encoding weights W with optional Ridge regularization.

    W = (C^T C + alpha I)^{-1} C^T X

    Args:
        X: (n_samples, n_voxels) pooled brain patterns
        hues: (n_samples,) hue angles in degrees
        n_channels: number of basis channels
        alpha: Ridge penalty (0 = OLS)

    Returns:
        W: (n_channels, n_voxels)
        basis_full: (360, n_channels)
    """
    basis_full = create_basis_functions(n_channels=n_channels)
    C = basis_full[hues.astype(int)]  # (n_samples, n_channels)

    if alpha > 0:
        W = np.linalg.solve(
            C.T @ C + alpha * np.eye(n_channels),
            C.T @ X
        )
    else:
        W = np.linalg.pinv(C) @ X

    return W, basis_full


def decode_with_W(W, basis_full, X_test):
    """Decode hue using correlation template matching."""
    channel_responses = W @ X_test.T  # (n_channels, n_samples)
    n_samples = X_test.shape[0]
    pred_hues = np.zeros(n_samples)

    for i in range(n_samples):
        resp = channel_responses[:, i]
        corrs = np.array([np.corrcoef(resp, basis_full[h])[0, 1] for h in range(360)])
        pred_hues[i] = np.nanargmax(corrs)

    return pred_hues


def compute_group_W(other_amps_dict, exclude_color_idx=None, alpha=0):
    """Compute group W from other subjects' pooled data.

    Args:
        other_amps_dict: {subj_id: (n_runs, n_colors, n_voxels)}
        exclude_color_idx: color index to exclude (LOCO leakage fix)
        alpha: Ridge penalty for group W

    Returns:
        W_group: (n_channels, n_voxels)
        basis_full: (360, n_channels)
    """
    W_others = []
    for s, amp in other_amps_dict.items():
        n_r, n_c, n_v = amp.shape
        if exclude_color_idx is not None:
            train_colors = [c for c in range(n_c) if c != exclude_color_idx]
            amp_train = amp[:, train_colors, :]
            hues_train = np.array([HUE_ANGLES[c] for c in train_colors])
            X_pooled = amp_train.reshape(-1, n_v)
            hues_pooled = np.tile(hues_train, n_r)
        else:
            X_pooled = amp.reshape(-1, n_v)
            hues_pooled = np.tile(np.array(HUE_ANGLES), n_r)
        W_s, _ = fit_W(X_pooled, hues_pooled, alpha=alpha)
        W_others.append(W_s)

    W_group = np.mean(W_others, axis=0)
    basis_full = create_basis_functions(n_channels=6)
    return W_group, basis_full


# ============================================================================
# GCV Utility
# ============================================================================

def gcv_select_alpha(C, Y, alpha_grid):
    """Select Ridge alpha via Generalized Cross-Validation.

    GCV(alpha) = mean(||Y - H Y||^2) / (1 - tr(H)/n)^2

    where H = C (C^T C + alpha I)^{-1} C^T.

    Computed efficiently via SVD of C:
      H = U diag(s^2 / (s^2 + alpha)) U^T

    Args:
        C: (n_samples, n_channels) design matrix
        Y: (n_samples, n_voxels) response matrix
        alpha_grid: list of candidate alphas

    Returns:
        best_alpha: alpha with lowest GCV score
        gcv_scores: dict of alpha -> gcv_score
    """
    n = C.shape[0]
    U, s, Vt = np.linalg.svd(C, full_matrices=False)

    gcv_scores = {}
    for alpha in alpha_grid:
        d = s**2 / (s**2 + alpha)
        Y_hat = (U * d[np.newaxis, :]) @ (U.T @ Y)
        residuals = Y - Y_hat
        tr_H = np.sum(d)
        gcv = np.mean(residuals**2) / (1 - tr_H / n)**2
        gcv_scores[alpha] = float(gcv)

    best_alpha = min(gcv_scores, key=gcv_scores.get)
    return best_alpha, gcv_scores


# ============================================================================
# Mode 1: Fixed Alpha Grid (diagnostic)
# ============================================================================

def loco_fixed_alpha(amp, alpha_grid):
    """LOCO with fixed alpha grid. No group prior.

    Diagnostic tool: shows how each alpha affects LOCO MAE.
    Not for alpha selection (that would be test-set selection bias).

    Returns:
        results: dict mapping alpha -> {'mean_mae', 'fold_maes'}
    """
    n_runs, n_colors, n_voxels = amp.shape
    results = {}

    for alpha in alpha_grid:
        fold_maes = []
        for test_color in range(n_colors):
            train_colors = [c for c in range(n_colors) if c != test_color]
            train_hues = np.array([HUE_ANGLES[c] for c in train_colors])
            test_hue = HUE_ANGLES[test_color]

            X_train = amp[:, train_colors, :].reshape(-1, n_voxels)
            hues_train = np.tile(train_hues, n_runs)
            X_test = amp[:, test_color, :]

            W, basis_full = fit_W(X_train, hues_train, alpha=alpha)
            pred_hues = decode_with_W(W, basis_full, X_test)
            errors = circular_distance(np.full(n_runs, test_hue), pred_hues)
            fold_maes.append(float(np.mean(errors)))

        results[alpha] = {
            'mean_mae': float(np.mean(fold_maes)),
            'fold_maes': fold_maes,
        }

    return results


# ============================================================================
# Mode 2: GCV-based LOCO
# ============================================================================

def loco_gcv(amp, alpha_grid):
    """LOCO with GCV-based alpha selection per fold.

    For each outer LOCO fold (8-fold):
      1. GCV on 7 training colors (42 samples, overdetermined) -> select alpha
      2. Fit W with selected alpha on all 42 training samples
      3. Predict held-out color (6 samples) -> MAE

    Returns:
        dict with mean_mae, fold_maes, selected_alphas, gcv_details
    """
    n_runs, n_colors, n_voxels = amp.shape
    basis_full = create_basis_functions(n_channels=6)

    fold_maes = []
    selected_alphas = []
    gcv_details = []

    for test_color in range(n_colors):
        train_colors = [c for c in range(n_colors) if c != test_color]
        train_hues = np.array([HUE_ANGLES[c] for c in train_colors])
        test_hue = HUE_ANGLES[test_color]

        X_train = amp[:, train_colors, :].reshape(-1, n_voxels)
        hues_train = np.tile(train_hues, n_runs)
        C_train = basis_full[hues_train.astype(int)]

        # GCV alpha selection on training data only
        best_alpha, gcv_scores = gcv_select_alpha(C_train, X_train, alpha_grid)
        selected_alphas.append(best_alpha)
        gcv_details.append(gcv_scores)

        # Fit and predict
        W, _ = fit_W(X_train, hues_train, alpha=best_alpha)
        X_test = amp[:, test_color, :]
        pred_hues = decode_with_W(W, basis_full, X_test)
        errors = circular_distance(np.full(n_runs, test_hue), pred_hues)
        fold_maes.append(float(np.mean(errors)))

    return {
        'mean_mae': float(np.mean(fold_maes)),
        'fold_maes': fold_maes,
        'selected_alphas': [float(a) for a in selected_alphas],
        'gcv_details': gcv_details,
    }


# ============================================================================
# Mode 3: Combined Ridge + Group Prior (GCV + leave-one-run-out)
# ============================================================================

def loco_combined_gcv(target_amp, other_amps_dict, alpha_grid, lambda_grid):
    """Joint optimization: GCV for alpha, leave-one-run-out for lambda.

    For each outer LOCO fold:
      1. GCV on training data (7 colors x 6 runs = 42 samples) -> best alpha
      2. W_group from other HC subjects (exclude test color, OLS)
      3. Leave-one-run-out (6-fold over runs) -> select lambda
         Each run-fold: 5 runs x 7 colors = 35 train, 1 run x 7 colors = 7 val
         (7 unique hue conditions > 6 channels -> overdetermined)
      4. Final prediction with (best_alpha, best_lambda)

    Returns:
        selected_params: list of (alpha, lambda) per fold
        fold_maes: list of MAE per fold
    """
    n_runs, n_colors, n_voxels = target_amp.shape
    basis_full = create_basis_functions(n_channels=6)

    fold_maes = []
    selected_params = []

    for test_color in range(n_colors):
        train_colors = [c for c in range(n_colors) if c != test_color]
        train_hues = np.array([HUE_ANGLES[c] for c in train_colors])
        test_hue = HUE_ANGLES[test_color]

        # Full training data
        X_train_full = target_amp[:, train_colors, :].reshape(-1, n_voxels)
        hues_train_full = np.tile(train_hues, n_runs)
        C_train_full = basis_full[hues_train_full.astype(int)]

        # Step 1: GCV for alpha on full training data
        best_alpha, _ = gcv_select_alpha(C_train_full, X_train_full, alpha_grid)

        # Step 2: Group W (exclude test color, OLS)
        W_group, _ = compute_group_W(
            other_amps_dict, exclude_color_idx=test_color
        )

        # Step 3: Leave-one-run-out for lambda selection
        lambda_scores = {lam: [] for lam in lambda_grid}

        for val_run in range(n_runs):
            train_runs = [r for r in range(n_runs) if r != val_run]

            # W_ind from (n_runs-1) runs
            X_lr_train = target_amp[train_runs][:, train_colors, :].reshape(-1, n_voxels)
            hues_lr_train = np.tile(train_hues, len(train_runs))
            W_ind_lr, _ = fit_W(X_lr_train, hues_lr_train, alpha=best_alpha)

            # Validation: val_run's training colors
            X_lr_val = target_amp[val_run, train_colors, :]  # (7, n_voxels)

            for lam in lambda_grid:
                W_combined = lam * W_ind_lr + (1 - lam) * W_group
                pred = decode_with_W(W_combined, basis_full, X_lr_val)
                errors = circular_distance(train_hues, pred)
                lambda_scores[lam].append(float(np.mean(errors)))

        # Select best lambda
        lambda_means = {l: np.mean(s) for l, s in lambda_scores.items()}
        best_lambda = min(lambda_means, key=lambda_means.get)
        selected_params.append((best_alpha, best_lambda))

        # Step 4: Final prediction with best (alpha, lambda)
        W_ind_full, _ = fit_W(X_train_full, hues_train_full, alpha=best_alpha)
        W_combined = best_lambda * W_ind_full + (1 - best_lambda) * W_group
        X_test = target_amp[:, test_color, :]
        pred_hues = decode_with_W(W_combined, basis_full, X_test)
        errors = circular_distance(np.full(n_runs, test_hue), pred_hues)
        fold_maes.append(float(np.mean(errors)))

    return selected_params, fold_maes


# ============================================================================
# OLS Baseline
# ============================================================================

def loco_ols_baseline(amp):
    """Standard LOCO with OLS (alpha=0) for comparison."""
    return loco_fixed_alpha(amp, [0.0])[0.0]


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Phase 2: Ridge LOCO')
    parser.add_argument('--subject', type=str, required=True,
                        help='Subject ID (e.g., 01)')
    parser.add_argument('--rois', nargs='+', default=ROIS)
    parser.add_argument('--mode', type=str, default='gcv',
                        choices=['fixed', 'gcv', 'combined'])
    parser.add_argument('--alignment', type=str, default='srm',
                        choices=['raw', 'procrustes', 'srm'])
    parser.add_argument('--baseline_dir', type=str, default=str(BASELINE_DIR))
    parser.add_argument('--output_dir', type=str, default=str(RESULTS_DIR))
    args = parser.parse_args()

    baseline_dir = Path(args.baseline_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print('=' * 70)
    print(f'Phase 2: Ridge LOCO (mode={args.mode})')
    print(f'Subject: sub-{args.subject}')
    print(f'ROIs: {args.rois}')
    print(f'Alignment: {args.alignment}')
    print('=' * 70)

    # Load other HC subjects for combined mode
    other_amps = {}
    if args.mode == 'combined':
        hc_pool = [s for s in HC_SUBJECTS if s != args.subject]
        for s in hc_pool:
            for roi in args.rois:
                try:
                    other_amps.setdefault(roi, {})[s] = load_amplitudes(
                        str(baseline_dir), s, roi, args.alignment)
                except FileNotFoundError:
                    print(f'  WARNING: sub-{s} {roi} not found')

    all_results = {}

    for roi in args.rois:
        print(f'\n--- {roi} ---')

        try:
            amp = load_amplitudes(str(baseline_dir), args.subject, roi, args.alignment)
            print(f'  Loaded: {amp.shape}')
        except FileNotFoundError as e:
            print(f'  ERROR: {e}')
            continue

        roi_result = {}

        # OLS baseline
        ols = loco_ols_baseline(amp)
        roi_result['OLS_baseline'] = ols
        print(f'  OLS baseline MAE: {ols["mean_mae"]:.1f}')

        if args.mode == 'fixed':
            fixed_results = loco_fixed_alpha(amp, ALPHA_GRID)
            roi_result['fixed_alpha'] = {}
            for alpha, res in fixed_results.items():
                roi_result['fixed_alpha'][str(alpha)] = res
                delta = res['mean_mae'] - ols['mean_mae']
                print(f'  alpha={alpha:>8.3f}: MAE={res["mean_mae"]:.1f} '
                      f'(delta={delta:+.1f})')

        elif args.mode == 'gcv':
            gcv_result = loco_gcv(amp, ALPHA_GRID)
            delta = gcv_result['mean_mae'] - ols['mean_mae']
            roi_result['gcv'] = gcv_result
            print(f'  GCV: MAE={gcv_result["mean_mae"]:.1f} '
                  f'(alphas={gcv_result["selected_alphas"]}, '
                  f'delta={delta:+.1f})')

        elif args.mode == 'combined':
            if roi not in other_amps or not other_amps[roi]:
                print(f'  No group data for combined mode, skipping')
                continue
            sel_params, fold_maes = loco_combined_gcv(
                amp, other_amps[roi], ALPHA_GRID, LAMBDA_GRID)
            combined_mae = float(np.mean(fold_maes))
            delta = combined_mae - ols['mean_mae']

            param_counts = Counter(sel_params)
            most_common = param_counts.most_common(1)[0]

            roi_result['combined'] = {
                'mean_mae': combined_mae,
                'fold_maes': fold_maes,
                'selected_params': [(float(a), float(l)) for a, l in sel_params],
                'most_common_params': {
                    'alpha': float(most_common[0][0]),
                    'lambda': float(most_common[0][1]),
                    'count': most_common[1],
                },
            }
            print(f'  Combined: MAE={combined_mae:.1f} '
                  f'(alpha={most_common[0][0]}, lambda={most_common[0][1]}, '
                  f'delta={delta:+.1f})')

        all_results[roi] = roi_result

    # Save
    output_file = output_dir / f'sub-{args.subject}_ridge_{args.mode}.json'
    save_data = {
        'subject': args.subject,
        'subject_group': 'HC' if args.subject in HC_SUBJECTS else 'CVD',
        'mode': args.mode,
        'alignment': args.alignment,
        'rois': args.rois,
        'alpha_grid': ALPHA_GRID,
        'lambda_grid': LAMBDA_GRID if args.mode == 'combined' else None,
        'results': all_results,
        'timestamp': datetime.now().isoformat(),
    }
    with open(output_file, 'w') as f:
        json.dump(save_data, f, indent=2)
    print(f'\nSaved: {output_file}')

    # Summary
    print(f'\n{"=" * 70}')
    print('SUMMARY')
    print(f'{"=" * 70}')
    for roi in args.rois:
        if roi not in all_results:
            continue
        r = all_results[roi]
        ols_mae = r['OLS_baseline']['mean_mae']
        print(f'\n{roi}: OLS={ols_mae:.1f}', end='')

        if args.mode == 'fixed' and 'fixed_alpha' in r:
            best_a = min(r['fixed_alpha'].items(),
                        key=lambda x: x[1]['mean_mae'])
            print(f' | Best Ridge: alpha={best_a[0]}, MAE={best_a[1]["mean_mae"]:.1f}',
                  end='')
        elif args.mode == 'gcv' and 'gcv' in r:
            alpha_counts = Counter(r['gcv']['selected_alphas'])
            mode_alpha = alpha_counts.most_common(1)[0]
            print(f' | GCV: MAE={r["gcv"]["mean_mae"]:.1f}, '
                  f'modal_alpha={mode_alpha[0]} ({mode_alpha[1]}/8 folds)',
                  end='')
        elif args.mode == 'combined' and 'combined' in r:
            p = r['combined']['most_common_params']
            print(f' | Combined: MAE={r["combined"]["mean_mae"]:.1f}, '
                  f'alpha={p["alpha"]}, lambda={p["lambda"]}', end='')
        print()


if __name__ == '__main__':
    main()
