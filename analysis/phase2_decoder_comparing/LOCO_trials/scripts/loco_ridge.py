#!/usr/bin/env python3
"""
Phase 2: Ridge-Regularized LOCO Forward Encoding

Stabilizes W estimation via Ridge penalty while keeping 6 channels.
Effectively shrinks df from (7 colors - 6 channels = 1) to a regularized solution.

Modes:
  fixed    : Test alpha grid [0.001, 0.01, 0.1, 1, 10, 100, 1000] on outer folds
  nested   : Outer LOCO 8-fold, inner CV selects alpha
  combined : Ridge(alpha) + Group Prior(lambda) joint optimization

Usage (server):
    python loco_ridge.py --subject 01 --rois V1 V2 V3 V4 --mode fixed
    python loco_ridge.py --subject 01 --rois V1 V2 V3 V4 --mode nested
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
# Core Functions (reused from group_prior.py with Ridge support)
# ============================================================================

def fit_W(X, hues, n_channels=6, alpha=0):
    """Fit encoding weights W with optional Ridge regularization.

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
# Mode 1: Fixed Alpha Grid
# ============================================================================

def loco_fixed_alpha(amp, alpha_grid):
    """LOCO with fixed alpha grid. No group prior.

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
# Mode 2: Nested CV for Alpha Selection
# ============================================================================

def loco_nested_alpha(amp, alpha_grid):
    """Nested LOCO: outer 8-fold (color), inner LOCO for alpha selection.

    Inner loop: 7 training colors -> leave-one-out -> 6 training colors.
    Ridge is essential in inner loop (6 colors - 6 channels = df=0).

    Returns:
        best_alpha: most-selected alpha across outer folds
        outer_fold_maes: list of MAE per outer fold
        selected_alphas: list of selected alpha per outer fold
    """
    n_runs, n_colors, n_voxels = amp.shape
    outer_fold_maes = []
    selected_alphas = []

    for outer_test_color in range(n_colors):
        outer_train_colors = [c for c in range(n_colors) if c != outer_test_color]

        # Inner LOCO: select alpha on 7 training colors
        alpha_scores = {a: [] for a in alpha_grid}

        for inner_val_color in outer_train_colors:
            inner_train_colors = [c for c in outer_train_colors if c != inner_val_color]
            inner_train_hues = np.array([HUE_ANGLES[c] for c in inner_train_colors])
            inner_val_hue = HUE_ANGLES[inner_val_color]
            X_val = amp[:, inner_val_color, :]

            for alpha in alpha_grid:
                X_train = amp[:, inner_train_colors, :].reshape(-1, n_voxels)
                hues_train = np.tile(inner_train_hues, n_runs)
                W, basis_full = fit_W(X_train, hues_train, alpha=alpha)
                pred_hues = decode_with_W(W, basis_full, X_val)
                errors = circular_distance(np.full(n_runs, inner_val_hue), pred_hues)
                alpha_scores[alpha].append(float(np.mean(errors)))

        # Select best alpha (lowest inner MAE)
        alpha_means = {a: np.mean(s) for a, s in alpha_scores.items()}
        best_alpha = min(alpha_means, key=alpha_means.get)
        selected_alphas.append(best_alpha)

        # Test outer fold with best alpha
        outer_train_hues = np.array([HUE_ANGLES[c] for c in outer_train_colors])
        outer_test_hue = HUE_ANGLES[outer_test_color]
        X_train = amp[:, outer_train_colors, :].reshape(-1, n_voxels)
        hues_train = np.tile(outer_train_hues, n_runs)
        X_test = amp[:, outer_test_color, :]

        W, basis_full = fit_W(X_train, hues_train, alpha=best_alpha)
        pred_hues = decode_with_W(W, basis_full, X_test)
        errors = circular_distance(np.full(n_runs, outer_test_hue), pred_hues)
        outer_fold_maes.append(float(np.mean(errors)))

    # Most frequent alpha
    from collections import Counter
    best_alpha_overall = Counter(selected_alphas).most_common(1)[0][0]

    return best_alpha_overall, outer_fold_maes, selected_alphas


# ============================================================================
# Mode 3: Combined Ridge + Group Prior
# ============================================================================

def loco_combined(target_amp, other_amps_dict, alpha_grid, lambda_grid):
    """Joint optimization of Ridge alpha + Group Prior lambda.

    Nested LOCO: outer 8-fold, inner LOCO searches (alpha, lambda) grid.

    Returns:
        best_params: (best_alpha, best_lambda)
        outer_fold_maes: list
        selected_params: list of (alpha, lambda) per fold
    """
    n_runs, n_colors, n_voxels = target_amp.shape
    outer_fold_maes = []
    selected_params = []

    for outer_test_color in range(n_colors):
        outer_train_colors = [c for c in range(n_colors) if c != outer_test_color]

        # Group W (excludes outer test color)
        W_group, basis_full = compute_group_W(
            other_amps_dict, exclude_color_idx=outer_test_color
        )

        # Inner LOCO: grid search (alpha, lambda)
        param_scores = {}

        for inner_val_color in outer_train_colors:
            inner_train_colors = [c for c in outer_train_colors if c != inner_val_color]
            inner_train_hues = np.array([HUE_ANGLES[c] for c in inner_train_colors])
            inner_val_hue = HUE_ANGLES[inner_val_color]
            X_val = target_amp[:, inner_val_color, :]

            for alpha in alpha_grid:
                X_train = target_amp[:, inner_train_colors, :].reshape(-1, n_voxels)
                hues_train = np.tile(inner_train_hues, n_runs)
                W_ind, _ = fit_W(X_train, hues_train, alpha=alpha)

                for lam in lambda_grid:
                    W_combined = lam * W_ind + (1 - lam) * W_group
                    pred_hues = decode_with_W(W_combined, basis_full, X_val)
                    errors = circular_distance(np.full(n_runs, inner_val_hue), pred_hues)
                    key = (alpha, lam)
                    param_scores.setdefault(key, []).append(float(np.mean(errors)))

        # Select best (alpha, lambda)
        param_means = {k: np.mean(v) for k, v in param_scores.items()}
        best_key = min(param_means, key=param_means.get)
        best_alpha, best_lambda = best_key
        selected_params.append(best_key)

        # Test outer fold
        outer_train_hues = np.array([HUE_ANGLES[c] for c in outer_train_colors])
        outer_test_hue = HUE_ANGLES[outer_test_color]
        X_train = target_amp[:, outer_train_colors, :].reshape(-1, n_voxels)
        hues_train = np.tile(outer_train_hues, n_runs)
        X_test = target_amp[:, outer_test_color, :]

        W_ind, _ = fit_W(X_train, hues_train, alpha=best_alpha)
        W_combined = best_lambda * W_ind + (1 - best_lambda) * W_group
        pred_hues = decode_with_W(W_combined, basis_full, X_test)
        errors = circular_distance(np.full(n_runs, outer_test_hue), pred_hues)
        outer_fold_maes.append(float(np.mean(errors)))

    return selected_params, outer_fold_maes


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
    parser.add_argument('--mode', type=str, default='fixed',
                        choices=['fixed', 'nested', 'combined'])
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

        elif args.mode == 'nested':
            best_alpha, fold_maes, sel_alphas = loco_nested_alpha(amp, ALPHA_GRID)
            nested_mae = float(np.mean(fold_maes))
            delta = nested_mae - ols['mean_mae']
            roi_result['nested'] = {
                'best_alpha': float(best_alpha),
                'mean_mae': nested_mae,
                'fold_maes': fold_maes,
                'selected_alphas': [float(a) for a in sel_alphas],
            }
            print(f'  Nested: MAE={nested_mae:.1f} (best_alpha={best_alpha}, '
                  f'delta={delta:+.1f})')

        elif args.mode == 'combined':
            if roi not in other_amps or not other_amps[roi]:
                print(f'  No group data for combined mode, skipping')
                continue
            sel_params, fold_maes = loco_combined(
                amp, other_amps[roi], ALPHA_GRID, LAMBDA_GRID)
            combined_mae = float(np.mean(fold_maes))
            delta = combined_mae - ols['mean_mae']

            # Aggregate selected params
            from collections import Counter
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
        elif args.mode == 'nested' and 'nested' in r:
            print(f' | Nested: MAE={r["nested"]["mean_mae"]:.1f}, '
                  f'alpha={r["nested"]["best_alpha"]}', end='')
        elif args.mode == 'combined' and 'combined' in r:
            p = r['combined']['most_common_params']
            print(f' | Combined: MAE={r["combined"]["mean_mae"]:.1f}, '
                  f'alpha={p["alpha"]}, lambda={p["lambda"]}', end='')
        print()


if __name__ == '__main__':
    main()
