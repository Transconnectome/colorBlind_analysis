#!/usr/bin/env python3
"""
Validate extended encoding models for §9h prior failure investigation.

Models (all use inner LOCO for hyperparameter selection):
  ridge_gcv        — baseline, GCV alpha selection
  prior_finetune   — (C'C + lam*I)^{-1}(C'X + lam*W0), inner LORO lam
  mixed_ridge_prior — (C'C + (a+l)*I)^{-1}(C'X + l*W0), inner LOCO a×l
  bayes_prior      — per-voxel precision from HC var, inner LOCO gamma
  smooth_tikh      — (C'C + a*I + b*D'D)^{-1}C'X, inner LOCO a×b
  smooth_prior     — (C'C + a*D'D + l*I)^{-1}(C'X + l*W0), inner LOCO a×l

Evaluation: LOCO (8-fold), with per-fold clean W0/var_W recomputation.

Usage:
    python validate_extended_models.py --subject 01 --rois V1 V2 V3 V4 \
        --baseline_dir /path/to/C010 --output_dir results/validation_extended
"""

import argparse
import json
import pickle
import numpy as np
from pathlib import Path
from scipy.stats import spearmanr

from utils_forward_model import (
    ROIS, N_RUNS, N_COLORS, N_CHANNELS, ALPHA_GRID, LAMBDA_GRID,
    HUE_ANGLES, HC_SUBJECTS, CVD_SUBJECTS,
    load_amplitudes, create_basis_matrix, create_basis_full,
    fit_W_ols, fit_W_ridge, fit_W_prior_ridge,
    fit_W_mixed_ridge_prior, fit_W_bayes_prior,
    fit_W_smooth_ridge, fit_W_smooth_prior,
    compute_prior_precision,
    predict_patterns, decode_hue, circular_distance,
    voxel_pattern_correlation, explained_variance,
    compute_rdm, rdm_upper_tri, gcv_select_alpha,
    save_config, get_subject_group, project_new_subject,
    DEFAULT_BASELINE_DIR,
)

# ============================================================================
# Hyperparameter grids for extended models
# ============================================================================

ALPHA_GRID_2D = [0.01, 0.1, 1, 10, 100]
LAMBDA_GRID_2D = [0, 0.01, 0.1, 1, 10, 100]
BETA_GRID = [0.01, 0.1, 1, 10, 100]
GAMMA_GRID = [0.01, 0.1, 1, 10, 100]

# Reduced grid for smooth_prior (3×3 to limit compute)
ALPHA_GRID_SP = [0.1, 1, 10]
LAMBDA_GRID_SP = [0.1, 1, 10]

EXTENDED_MODELS = ['mixed_ridge_prior', 'bayes_prior',
                   'smooth_tikh', 'smooth_prior']


# ============================================================================
# LOCO-safe prior reconstruction with variance
# ============================================================================

def recompute_W0_var_excluding_colors(
    subj, roi, train_colors, baseline_dir, srm_dir, lambda_A=0.0,
):
    """Recompute W0 and var_W from HC group prior excluding held-out colors.

    Extends recompute_W0_excluding_colors to also return per-element
    variance across HC subjects, needed for bayes_prior.

    Args:
        subj: target subject ID
        roi: ROI name
        train_colors: list of colour indices included in training
        baseline_dir: path to C010 data
        srm_dir: directory with sub-{ID}_R.npy and srm_model.pkl
        lambda_A: regularisation for A_i fitting (0 = OLS)

    Returns:
        W0: (K, V_s) prior weight matrix
        var_W: (K, V_s) prior variance (floored at 1e-6)
    """
    roi_srm = Path(srm_dir) / roi
    C_full = create_basis_matrix(HUE_ANGLES)       # (8, K)
    C_train = C_full[train_colors]                  # (n_train, K)
    K = C_full.shape[1]

    CtC_inv = np.linalg.inv(C_train.T @ C_train + lambda_A * np.eye(K))

    # Rebuild A_i per HC using only train_colors
    A_list = []
    for hc in HC_SUBJECTS:
        R_i = np.load(roi_srm / f'sub-{hc}_R.npy')
        amp_i = load_amplitudes(baseline_dir, hc, roi)
        beta_i = amp_i.mean(axis=0)
        Z_i = R_i.T @ beta_i.T
        Z_train = Z_i[:, train_colors]
        A_i = Z_train @ C_train @ CtC_inv
        A_list.append(A_i)

    # Get R_s for target subject
    if subj in HC_SUBJECTS:
        R_s = np.load(roi_srm / f'sub-{subj}_R.npy')
    else:
        with open(roi_srm / 'srm_model.pkl', 'rb') as f:
            srm_model = pickle.load(f)
        amp_s = load_amplitudes(baseline_dir, subj, roi)
        beta_s = amp_s.mean(axis=0)
        R_s = project_new_subject(srm_model, beta_s.T)

    W0, var_W = compute_prior_precision(A_list, R_s)
    return W0, var_W


# ============================================================================
# Inner CV: LOCO over colors (the key methodological change)
# ============================================================================

def _inner_cv_loco_color(amp, W0, var_W, outer_train_colors,
                         model_name, param_grid):
    """Inner LOCO CV (color-held-out) for hyperparameter selection.

    Outer LOCO holds out 1 of 8 colors → 7 train colors.
    Inner LOCO holds out 1 of 7 → 6 train colors.
    Training: 6 runs × 6 colors = 36 samples, K=6 → well-determined.
    Validation: predict held-out inner color (run-averaged), voxel_corr.

    Args:
        amp: (6, 8, V_s)
        W0: (K, V_s) prior (from outer train colors)
        var_W: (K, V_s) or None (for bayes_prior)
        outer_train_colors: list of 7 color indices
        model_name: which model to fit
        param_grid: list of param tuples to search

    Returns:
        best_params: tuple of best hyperparameters
    """
    C_full = create_basis_matrix(HUE_ANGLES)
    V_s = amp.shape[2]

    scores = {p: [] for p in param_grid}

    for inner_held_color in outer_train_colors:
        inner_train = [c for c in outer_train_colors if c != inner_held_color]
        C_inner = C_full[inner_train]  # (6, K)

        # Pool all runs for inner training colors
        X_inner = amp[:, inner_train, :].reshape(-1, V_s)  # (36, V_s)
        C_inner_tiled = np.tile(C_inner, (N_RUNS, 1))       # (36, K)

        # Validation: run-averaged pattern for held-out inner color
        X_val = amp[:, inner_held_color, :].mean(axis=0, keepdims=True)  # (1, V_s)
        C_val = C_full[inner_held_color:inner_held_color + 1]             # (1, K)

        for params in param_grid:
            W = _fit_extended(model_name, C_inner_tiled, X_inner,
                              W0, var_W, params)
            Y_hat = predict_patterns(W, C_val)
            r = voxel_pattern_correlation(Y_hat, X_val)
            scores[params].append(float(np.mean(r)))

    means = {p: np.mean(s) for p, s in scores.items()}
    return max(means, key=means.get)


def _fit_extended(model_name, C, X, W0, var_W, params):
    """Dispatch fitting for extended models.

    Args:
        model_name: model identifier
        C: (n, K) design matrix
        X: (n, V_s) data
        W0: (K, V_s) prior
        var_W: (K, V_s) or None
        params: tuple of hyperparameters

    Returns:
        W: (K, V_s)
    """
    if model_name == 'mixed_ridge_prior':
        alpha, lam = params
        if alpha == 0 and lam == 0:
            return fit_W_ols(C, X)
        return fit_W_mixed_ridge_prior(C, X, W0, alpha, lam)

    elif model_name == 'bayes_prior':
        (gamma,) = params
        return fit_W_bayes_prior(C, X, W0, var_W, gamma)

    elif model_name == 'smooth_tikh':
        alpha, beta = params
        return fit_W_smooth_ridge(C, X, alpha, beta)

    elif model_name == 'smooth_prior':
        alpha, lam = params
        if lam == 0:
            return fit_W_smooth_ridge(C, X, alpha, 0.0)
        return fit_W_smooth_prior(C, X, W0, alpha, lam)

    else:
        raise ValueError(f'Unknown extended model: {model_name}')


def _build_param_grid(model_name):
    """Build parameter grid for a model.

    Returns:
        list of tuples
    """
    if model_name == 'mixed_ridge_prior':
        return [(a, l) for a in ALPHA_GRID_2D for l in LAMBDA_GRID_2D]
    elif model_name == 'bayes_prior':
        return [(g,) for g in GAMMA_GRID]
    elif model_name == 'smooth_tikh':
        return [(a, b) for a in ALPHA_GRID_2D for b in BETA_GRID]
    elif model_name == 'smooth_prior':
        return [(a, l) for a in ALPHA_GRID_SP for l in LAMBDA_GRID_SP]
    else:
        raise ValueError(f'Unknown model: {model_name}')


# ============================================================================
# Fold-level evaluation (reuse from validate_loro_loco_loso.py)
# ============================================================================

def evaluate_fold_loco(W, basis_full, C_test, X_test, true_hue):
    """Evaluate a single LOCO fold."""
    Y_hat_mean = predict_patterns(W, C_test)
    X_mean = X_test.mean(axis=0, keepdims=True)
    r = voxel_pattern_correlation(Y_hat_mean, X_mean)
    r2 = explained_variance(Y_hat_mean, X_mean)

    pred_hues = decode_hue(W, basis_full, X_test)
    errors = circular_distance(np.full(len(pred_hues), true_hue), pred_hues)

    return {
        'voxel_corr': float(np.mean(r)),
        'R2': float(np.mean(r2)),
        'mae': float(np.nanmean(errors)),
        'pred_hues': [float(h) for h in pred_hues],
        'errors': [float(e) for e in errors],
    }


# ============================================================================
# Main LOCO loop for extended models
# ============================================================================

def run_loco_extended(amp, subj, roi, baseline_dir, srm_dir, models=None):
    """8-fold LOCO for extended models with per-fold clean W0/var_W.

    Args:
        amp: (6, 8, V_s)
        subj: subject ID
        roi: ROI name
        baseline_dir: path to C010 data
        srm_dir: path to SRM projections
        models: list of model names (default: all extended + baselines)

    Returns:
        results: {model_name: {mean_voxel_corr, mean_mae, folds, ...}}
    """
    if models is None:
        models = ['ridge_gcv', 'prior_finetune'] + EXTENDED_MODELS

    C = create_basis_matrix(HUE_ANGLES)
    basis_full = create_basis_full()
    V_s = amp.shape[2]
    results = {}

    for model in models:
        print(f'    Model: {model}')
        folds = []
        selected_params_all = []

        for test_color in range(N_COLORS):
            train_colors = [c for c in range(N_COLORS) if c != test_color]

            # === Baseline models ===
            if model == 'ridge_gcv':
                C_train = C[train_colors]
                X_train = amp[:, train_colors, :].reshape(-1, V_s)
                C_train_tiled = np.tile(C_train, (N_RUNS, 1))
                best_alpha, _ = gcv_select_alpha(C_train_tiled, X_train)
                W = fit_W_ridge(C_train_tiled, X_train, best_alpha)
                meta = {'alpha': float(best_alpha)}

            elif model == 'prior_finetune':
                # Per-fold W0 (no leakage), inner LORO for lambda
                W0_fold, _ = recompute_W0_var_excluding_colors(
                    subj, roi, train_colors, baseline_dir, srm_dir)
                C_train = C[train_colors]
                X_train = amp[:, train_colors, :].reshape(-1, V_s)
                C_train_tiled = np.tile(C_train, (N_RUNS, 1))

                best_lam = _inner_cv_lambda_loro(
                    amp, W0_fold, train_colors, LAMBDA_GRID)
                if best_lam == 0:
                    W = fit_W_ols(C_train_tiled, X_train)
                else:
                    W = fit_W_prior_ridge(C_train_tiled, X_train, W0_fold, best_lam)
                meta = {'lambda': float(best_lam)}

            # === Extended models ===
            elif model in EXTENDED_MODELS:
                # Per-fold W0 + var_W (no leakage)
                needs_prior = model in ('mixed_ridge_prior', 'bayes_prior',
                                        'smooth_prior')
                if needs_prior:
                    W0_fold, var_W_fold = recompute_W0_var_excluding_colors(
                        subj, roi, train_colors, baseline_dir, srm_dir)
                else:
                    W0_fold, var_W_fold = None, None

                # Inner LOCO (color-held-out) for hyperparameter selection
                param_grid = _build_param_grid(model)
                best_params = _inner_cv_loco_color(
                    amp, W0_fold, var_W_fold, train_colors, model, param_grid)

                # Fit on full outer training set
                C_train = C[train_colors]
                X_train = amp[:, train_colors, :].reshape(-1, V_s)
                C_train_tiled = np.tile(C_train, (N_RUNS, 1))

                W = _fit_extended(model, C_train_tiled, X_train,
                                  W0_fold, var_W_fold, best_params)

                meta = {'best_params': [float(p) for p in best_params]}
                selected_params_all.append(best_params)
            else:
                raise ValueError(f'Unknown model: {model}')

            # Evaluate
            C_test = C[test_color:test_color + 1]
            X_test = amp[:, test_color, :]
            true_hue = HUE_ANGLES[test_color]

            fold_result = evaluate_fold_loco(
                W, basis_full, C_test, X_test, true_hue)
            fold_result.update(meta)
            fold_result['test_color'] = int(test_color)
            fold_result['true_hue'] = int(true_hue)
            folds.append(fold_result)

        # Aggregate
        result = {
            'mean_voxel_corr': float(np.mean([f['voxel_corr'] for f in folds])),
            'mean_R2': float(np.mean([f['R2'] for f in folds])),
            'mean_mae': float(np.mean([f['mae'] for f in folds])),
            'folds': folds,
        }

        # For extended models, summarize selected hyperparameters
        if selected_params_all:
            result['selected_params'] = [
                [float(p) for p in sp] for sp in selected_params_all
            ]
            # For mixed model: report lambda/(alpha+lambda) ratio
            if model == 'mixed_ridge_prior':
                ratios = []
                for sp in selected_params_all:
                    a, l = sp
                    ratio = l / (a + l) if (a + l) > 0 else 0.0
                    ratios.append(ratio)
                result['lambda_ratio_mean'] = float(np.mean(ratios))
                result['lambda_ratio_std'] = float(np.std(ratios))

        results[model] = result
        print(f'      voxel_corr={result["mean_voxel_corr"]:.4f}  '
              f'MAE={result["mean_mae"]:.1f}  R2={result["mean_R2"]:.4f}')

    return results


def _inner_cv_lambda_loro(amp, W0, train_colors, lambda_grid):
    """Inner LORO (over runs) for lambda selection in prior_finetune.

    Mirrors _inner_cv_lambda_loco from validate_loro_loco_loso.py.
    """
    C_full = create_basis_matrix(HUE_ANGLES)
    C_train_row = C_full[train_colors]
    inner_scores = {lam: [] for lam in lambda_grid}

    for val_run in range(N_RUNS):
        inner_train = [r for r in range(N_RUNS) if r != val_run]
        X_tr = amp[inner_train][:, train_colors, :].reshape(-1, amp.shape[2])
        C_tr = np.tile(C_train_row, (len(inner_train), 1))
        X_val = amp[val_run, train_colors, :]

        for lam in lambda_grid:
            if lam == 0:
                W = fit_W_ols(C_tr, X_tr)
            else:
                W = fit_W_prior_ridge(C_tr, X_tr, W0, lam)
            Y_hat = predict_patterns(W, C_train_row)
            r = voxel_pattern_correlation(Y_hat, X_val)
            inner_scores[lam].append(float(np.mean(r)))

    inner_means = {l: np.mean(s) for l, s in inner_scores.items()}
    return max(inner_means, key=inner_means.get)


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Validate extended models — §9h prior failure investigation')
    parser.add_argument('--subject', type=str, required=True)
    parser.add_argument('--rois', nargs='+', default=ROIS)
    parser.add_argument('--baseline_dir', type=str,
                        default=str(DEFAULT_BASELINE_DIR))
    parser.add_argument('--srm_dir', type=str,
                        default='results/srm_projections')
    parser.add_argument('--output_dir', type=str,
                        default='results/validation_extended')
    parser.add_argument('--models', nargs='+', default=None,
                        help='Models to evaluate (default: all 6)')
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    subj = args.subject.zfill(2)
    group = get_subject_group(subj)

    active_models = (args.models if args.models
                     else ['ridge_gcv', 'prior_finetune'] + EXTENDED_MODELS)

    print('=' * 60)
    print(f'Extended Validation: sub-{subj} ({group})')
    print(f'ROIs: {args.rois}')
    print(f'Models: {active_models}')
    print('=' * 60)

    all_results = {}

    for roi in args.rois:
        print(f'\n{"="*40} {roi} {"="*40}')

        try:
            amp = load_amplitudes(args.baseline_dir, subj, roi)
        except FileNotFoundError as e:
            print(f'  ERROR: {e}')
            continue

        V_s = amp.shape[2]
        print(f'  V_s = {V_s}')
        if V_s < 20:
            print(f'  WARNING: V_s={V_s} < 20 voxels — results may be noisy')

        roi_results = run_loco_extended(
            amp, subj, roi, args.baseline_dir, args.srm_dir,
            models=active_models)
        all_results[roi] = roi_results

    # Save
    loco_output = {
        'subject': subj,
        'subject_group': group,
    }
    loco_output.update(all_results)

    out_path = output_dir / f'sub-{subj}_loco.json'
    with open(out_path, 'w') as f:
        json.dump(loco_output, f, indent=2)
    print(f'\nSaved: {out_path}')

    # Summary table
    print(f'\n{"="*70}')
    print(f'SUMMARY: sub-{subj} LOCO voxel_corr')
    print(f'{"="*70}')
    header = f'{"Model":>22}'
    for roi in args.rois:
        if roi in all_results:
            header += f'  {roi:>8}'
    print(header)
    print('-' * 70)

    for model in active_models:
        line = f'{model:>22}'
        for roi in args.rois:
            if roi in all_results and model in all_results[roi]:
                v = all_results[roi][model]['mean_voxel_corr']
                line += f'  {v:>+8.4f}'
            else:
                line += f'  {"N/A":>8}'
        print(line)

    # Highlight improvements over prior_finetune
    if 'prior_finetune' in active_models:
        print(f'\nDelta vs prior_finetune:')
        for model in EXTENDED_MODELS:
            if model not in active_models:
                continue
            line = f'  {model:>22}'
            for roi in args.rois:
                if (roi in all_results
                        and model in all_results[roi]
                        and 'prior_finetune' in all_results[roi]):
                    d = (all_results[roi][model]['mean_voxel_corr']
                         - all_results[roi]['prior_finetune']['mean_voxel_corr'])
                    line += f'  {d:>+8.4f}'
                else:
                    line += f'  {"N/A":>8}'
            print(line)

    save_config(output_dir,
                step='validate_extended_models',
                subject=subj,
                subject_group=group,
                rois=args.rois,
                models=active_models,
                baseline_dir=args.baseline_dir,
                srm_dir=args.srm_dir,
                grids={
                    'alpha_2d': ALPHA_GRID_2D,
                    'lambda_2d': LAMBDA_GRID_2D,
                    'beta': BETA_GRID,
                    'gamma': GAMMA_GRID,
                    'alpha_sp': ALPHA_GRID_SP,
                    'lambda_sp': LAMBDA_GRID_SP,
                })

    print('\nDone.')


if __name__ == '__main__':
    main()
