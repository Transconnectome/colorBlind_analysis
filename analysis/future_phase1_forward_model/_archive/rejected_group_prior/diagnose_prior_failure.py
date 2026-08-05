#!/usr/bin/env python3
"""
Diagnose prior failure: shape vs magnitude + A_i variance analysis.

Runs locally using C010 data and existing group_prior A_i files.

Analysis 1 — Shape vs Magnitude (§9h-1):
  For each LOCO fold × HC subject:
  - Fit ridge W on 7 training colors
  - Compare W0 and W_ridge predictions against ground truth
  - Cosine similarity (shape) and magnitude ratio (scale)
  → Answers: does W0 fail on shape, scale, or both?

Analysis 2 — A_i Variance (§9h-2):
  - Load per-HC A_i from group_prior results
  - Compute per-element variance across HC
  - For each held-out color: prior_var(c) = Σ_j (C[c,j])² · Var(A_i[j,:])
  - Correlate prior_var with LOCO error
  → Answers: do high-variance prior colors have worse LOCO performance?

Usage:
    python diagnose_prior_failure.py \
        --baseline_dir ../../phase1_preprocess_decoding/results/full_dataset_C010 \
        --prior_dir ../results/subject_weights \
        --group_prior_dir ../results/group_prior \
        --validation_dir ../results/validation \
        --output_dir ../results/diagnostics
"""

import argparse
import json
import numpy as np
from pathlib import Path

# Import from utils — adjust path for local execution
import sys
sys.path.insert(0, str(Path(__file__).parent))

from utils_forward_model import (
    HC_SUBJECTS, ALL_SUBJECTS, ROIS, N_RUNS, N_COLORS, N_CHANNELS,
    HUE_ANGLES, ALPHA_GRID,
    load_amplitudes, create_basis_matrix,
    fit_W_ridge, gcv_select_alpha,
    predict_patterns, voxel_pattern_correlation,
    save_config, get_subject_group,
)


# ============================================================================
# Analysis 1: Shape vs Magnitude
# ============================================================================

def analyze_shape_vs_magnitude(subj, roi, amp, W0, baseline_dir):
    """Compare W0 vs ridge predictions: shape (cosine) and scale (magnitude).

    For each LOCO fold:
    - Fit ridge on 7 training colors (all runs pooled)
    - Predict held-out color with W0 and W_ridge
    - Compare both predictions against ground truth (run-averaged)

    Returns:
        list of dicts, one per LOCO fold
    """
    C = create_basis_matrix(HUE_ANGLES)
    V_s = amp.shape[2]
    results = []

    for test_color in range(N_COLORS):
        train_colors = [c for c in range(N_COLORS) if c != test_color]
        C_train = C[train_colors]
        X_train = amp[:, train_colors, :].reshape(-1, V_s)
        C_train_tiled = np.tile(C_train, (N_RUNS, 1))

        # Fit ridge
        best_alpha, _ = gcv_select_alpha(C_train_tiled, X_train)
        W_ridge = fit_W_ridge(C_train_tiled, X_train, best_alpha)

        # Ground truth: run-averaged pattern for held-out color
        X_true = amp[:, test_color, :].mean(axis=0)  # (V_s,)

        # Predictions
        C_test = C[test_color]  # (K,)
        pred_W0 = C_test @ W0        # (V_s,)
        pred_ridge = C_test @ W_ridge  # (V_s,)

        # Cosine similarity (shape)
        def cosine_sim(a, b):
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            if norm_a == 0 or norm_b == 0:
                return 0.0
            return float(np.dot(a, b) / (norm_a * norm_b))

        cos_W0 = cosine_sim(pred_W0, X_true)
        cos_ridge = cosine_sim(pred_ridge, X_true)

        # Magnitude ratio (pred / true)
        mag_true = np.linalg.norm(X_true)
        mag_W0 = np.linalg.norm(pred_W0) / mag_true if mag_true > 0 else 0.0
        mag_ridge = np.linalg.norm(pred_ridge) / mag_true if mag_true > 0 else 0.0

        # Voxel pattern correlation
        corr_W0 = float(np.corrcoef(pred_W0, X_true)[0, 1])
        corr_ridge = float(np.corrcoef(pred_ridge, X_true)[0, 1])
        if not np.isfinite(corr_W0):
            corr_W0 = 0.0
        if not np.isfinite(corr_ridge):
            corr_ridge = 0.0

        results.append({
            'test_color': int(test_color),
            'true_hue': int(HUE_ANGLES[test_color]),
            'cosine_W0': cos_W0,
            'cosine_ridge': cos_ridge,
            'cosine_delta': cos_ridge - cos_W0,
            'mag_ratio_W0': float(mag_W0),
            'mag_ratio_ridge': float(mag_ridge),
            'corr_W0': corr_W0,
            'corr_ridge': corr_ridge,
            'alpha': float(best_alpha),
        })

    return results


# ============================================================================
# Analysis 2: A_i Variance vs LOCO Error
# ============================================================================

def analyze_Ai_variance(roi, group_prior_dir, validation_dir):
    """Correlate prior variance per color with LOCO error.

    For each held-out color c:
      prior_var(c) = Σ_j (C[c,j])² · Var(A_i[j,:])_across_HC
    where the variance is over channels and elements of A_i.

    Returns:
        dict with per-color prior_var, per-subject LOCO errors, correlation
    """
    C = create_basis_matrix(HUE_ANGLES)  # (8, K)

    # Load all HC A_i
    roi_gp_dir = Path(group_prior_dir) / roi
    A_list = []
    for hc in HC_SUBJECTS:
        A_path = roi_gp_dir / f'sub-{hc}_A.npy'
        if A_path.exists():
            A_list.append(np.load(A_path))  # (k, K)

    if len(A_list) < 2:
        return {'error': f'Insufficient A_i files for {roi}'}

    A_stack = np.stack(A_list)  # (n_hc, k, K)
    A_var = A_stack.var(axis=0, ddof=1)  # (k, K) per-element variance

    # Per-color prior variance: how uncertain is the prior for color c?
    # prior_var(c) = Σ_j (C[c,j])² · mean_k(Var(A_i[k,j]))
    # We sum over channels K and average across SRM dimensions k
    A_var_mean_k = A_var.mean(axis=0)  # (K,) mean variance across k dims
    prior_var_per_color = np.array([
        np.sum(C[c] ** 2 * A_var_mean_k) for c in range(N_COLORS)
    ])

    # Load per-subject LOCO errors from validation results
    val_dir = Path(validation_dir)
    per_subject_errors = {}
    for subj in ALL_SUBJECTS:
        loco_path = val_dir / f'sub-{subj}_loco.json'
        if not loco_path.exists():
            continue
        with open(loco_path) as f:
            loco_data = json.load(f)
        if roi not in loco_data:
            continue

        # Get per-fold voxel_corr for ridge_gcv and prior_finetune
        for model in ('ridge_gcv', 'prior_finetune'):
            if model not in loco_data[roi]:
                continue
            folds = loco_data[roi][model].get('folds', [])
            per_color_corr = []
            for fold in folds:
                per_color_corr.append(fold.get('voxel_corr', np.nan))
            per_subject_errors[f'{subj}_{model}'] = per_color_corr

    # Correlate prior_var with per-color error (1 - voxel_corr)
    correlations = {}
    for key, corrs in per_subject_errors.items():
        if len(corrs) != N_COLORS:
            continue
        errors = 1 - np.array(corrs)
        valid = np.isfinite(errors)
        if valid.sum() >= 4:
            r = float(np.corrcoef(prior_var_per_color[valid], errors[valid])[0, 1])
            correlations[key] = r if np.isfinite(r) else 0.0

    return {
        'prior_var_per_color': [float(v) for v in prior_var_per_color],
        'color_hues': [int(h) for h in HUE_ANGLES],
        'A_var_mean': float(A_var.mean()),
        'A_var_max': float(A_var.max()),
        'per_subject_correlations': correlations,
        'mean_corr_ridge': float(np.mean([
            v for k, v in correlations.items() if 'ridge_gcv' in k
        ])) if any('ridge_gcv' in k for k in correlations) else None,
        'mean_corr_prior': float(np.mean([
            v for k, v in correlations.items() if 'prior_finetune' in k
        ])) if any('prior_finetune' in k for k in correlations) else None,
    }


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Diagnose prior failure: shape/magnitude + A_i variance')
    parser.add_argument('--baseline_dir', type=str,
                        default='../../phase1_preprocess_decoding/results/'
                                'full_dataset_C010')
    parser.add_argument('--prior_dir', type=str,
                        default='../results/subject_weights')
    parser.add_argument('--group_prior_dir', type=str,
                        default='../results/group_prior')
    parser.add_argument('--validation_dir', type=str,
                        default='../results/validation')
    parser.add_argument('--output_dir', type=str,
                        default='../results/diagnostics')
    parser.add_argument('--rois', nargs='+', default=ROIS)
    parser.add_argument('--subjects', nargs='+', default=None,
                        help='Subjects for shape analysis (default: HC only)')
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    subjects = args.subjects if args.subjects else HC_SUBJECTS

    # ==================================================================
    # Analysis 1: Shape vs Magnitude
    # ==================================================================
    print('=' * 70)
    print('ANALYSIS 1: Shape vs Magnitude')
    print('=' * 70)

    shape_results = {}
    for roi in args.rois:
        print(f'\n--- {roi} ---')
        roi_results = {}

        for subj in subjects:
            try:
                amp = load_amplitudes(args.baseline_dir, subj, roi)
            except FileNotFoundError:
                print(f'  sub-{subj}: data not found, skipping')
                continue

            W0_path = Path(args.prior_dir) / roi / f'sub-{subj}_W0.npy'
            if not W0_path.exists():
                print(f'  sub-{subj}: W0 not found, skipping')
                continue
            W0 = np.load(W0_path)

            fold_results = analyze_shape_vs_magnitude(
                subj, roi, amp, W0, args.baseline_dir)
            roi_results[subj] = fold_results

            # Summary for this subject
            cos_W0 = np.mean([f['cosine_W0'] for f in fold_results])
            cos_ridge = np.mean([f['cosine_ridge'] for f in fold_results])
            mag_W0 = np.mean([f['mag_ratio_W0'] for f in fold_results])
            mag_ridge = np.mean([f['mag_ratio_ridge'] for f in fold_results])
            print(f'  sub-{subj}: cos(W0)={cos_W0:.3f} cos(ridge)={cos_ridge:.3f} '
                  f'|W0|/|true|={mag_W0:.3f} |ridge|/|true|={mag_ridge:.3f}')

        shape_results[roi] = roi_results

    # Summary table
    print(f'\n{"="*70}')
    print('Shape vs Magnitude Summary (mean across folds)')
    print(f'{"="*70}')
    for roi in args.rois:
        if roi not in shape_results:
            continue
        print(f'\n  {roi}:')
        print(f'  {"Subject":>8}  {"cos_W0":>8}  {"cos_ridge":>10}  '
              f'{"mag_W0":>8}  {"mag_ridge":>10}  {"cos_delta":>10}')
        print(f'  {"-"*60}')
        for subj, folds in shape_results[roi].items():
            cos_W0 = np.mean([f['cosine_W0'] for f in folds])
            cos_ridge = np.mean([f['cosine_ridge'] for f in folds])
            mag_W0 = np.mean([f['mag_ratio_W0'] for f in folds])
            mag_ridge = np.mean([f['mag_ratio_ridge'] for f in folds])
            delta = np.mean([f['cosine_delta'] for f in folds])
            print(f'  sub-{subj:>3}  {cos_W0:>8.4f}  {cos_ridge:>10.4f}  '
                  f'{mag_W0:>8.3f}  {mag_ridge:>10.3f}  {delta:>+10.4f}')

    # Save
    with open(output_dir / 'shape_vs_magnitude.json', 'w') as f:
        json.dump(shape_results, f, indent=2)

    # ==================================================================
    # Analysis 2: A_i Variance
    # ==================================================================
    print(f'\n{"="*70}')
    print('ANALYSIS 2: A_i Variance vs LOCO Error')
    print(f'{"="*70}')

    variance_results = {}
    for roi in args.rois:
        print(f'\n--- {roi} ---')
        result = analyze_Ai_variance(roi, args.group_prior_dir,
                                     args.validation_dir)
        variance_results[roi] = result

        if 'error' in result:
            print(f'  {result["error"]}')
            continue

        print(f'  prior_var per color: '
              f'{[f"{v:.4f}" for v in result["prior_var_per_color"]]}')
        print(f'  A_var mean={result["A_var_mean"]:.6f}, '
              f'max={result["A_var_max"]:.6f}')

        if result['mean_corr_ridge'] is not None:
            print(f'  Mean corr(prior_var, error) — '
                  f'ridge: {result["mean_corr_ridge"]:.3f}, '
                  f'prior: {result["mean_corr_prior"]:.3f}')

        # Per-subject breakdown
        for key, r in result.get('per_subject_correlations', {}).items():
            print(f'    {key}: r = {r:+.3f}')

    with open(output_dir / 'Ai_variance.json', 'w') as f:
        json.dump(variance_results, f, indent=2)

    # ==================================================================
    # Decision summary
    # ==================================================================
    print(f'\n{"="*70}')
    print('DIAGNOSTIC SUMMARY')
    print(f'{"="*70}')

    for roi in args.rois:
        if roi not in shape_results:
            continue
        print(f'\n  {roi}:')

        # Shape: mean cosine delta across subjects
        cos_deltas = []
        mag_ratios_W0 = []
        for subj, folds in shape_results[roi].items():
            cos_deltas.append(np.mean([f['cosine_delta'] for f in folds]))
            mag_ratios_W0.append(np.mean([f['mag_ratio_W0'] for f in folds]))

        mean_cos_delta = np.mean(cos_deltas)
        mean_mag_W0 = np.mean(mag_ratios_W0)

        shape_ok = mean_cos_delta < 0.05
        scale_ok = 0.8 < mean_mag_W0 < 1.2

        print(f'    Shape: cos_delta={mean_cos_delta:+.4f} '
              f'-> {"OK" if shape_ok else "PROBLEM (W0 shape differs)"}')
        print(f'    Scale: |W0|/|true|={mean_mag_W0:.3f} '
              f'-> {"OK" if scale_ok else "PROBLEM (scale mismatch)"}')

        # Variance
        if roi in variance_results and 'mean_corr_prior' in variance_results[roi]:
            var_corr = variance_results[roi]['mean_corr_prior']
            if var_corr is not None:
                var_significant = abs(var_corr) > 0.3
                print(f'    Variance: r(prior_var, error)={var_corr:+.3f} '
                      f'-> {"SIGNIFICANT" if var_significant else "weak"}')

    save_config(output_dir,
                step='diagnose_prior_failure',
                rois=args.rois,
                subjects=subjects,
                baseline_dir=args.baseline_dir,
                prior_dir=args.prior_dir,
                group_prior_dir=args.group_prior_dir,
                validation_dir=args.validation_dir)

    print('\nDiagnostics complete.')


if __name__ == '__main__':
    main()
