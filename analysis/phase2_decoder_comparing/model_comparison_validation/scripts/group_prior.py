#!/usr/bin/env python3
"""
Group Prior (GP) for Forward Encoding: LOCO and LORO.

W_combined = lambda * W_individual + (1-lambda) * W_group

- W_group: mean of other HC subjects' pooled W
- W_individual: target subject's pooled W from training data
  - LOCO: 7 training colors x 6 runs = 42 samples
  - LORO: 8 colors x 5 train runs = 40 samples

Modes:
  --mode fixed  : test a grid of lambda values on outer test set
  --mode nested : nested CV (inner folds) to select lambda per outer fold

CV protocols:
  --cv loco : Leave-One-Color-Out (8 outer folds)
  --cv loro : Leave-One-Run-Out (6 outer folds)

Usage:
    python group_prior.py --cv loco --mode fixed --subjects 01 02 --rois V1 V2
    python group_prior.py --cv loro --mode nested --subjects 01 --rois V1
    python group_prior.py --cv loco --mode fixed --subjects 01 --rois V1 \
        --lambda_values 0.0,0.5,1.0
"""
import sys
import argparse
import json
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from loco_baseline import (
    load_amplitudes, create_basis_functions, circular_distance,
    HUE_ANGLES,
)

baseline = Path(__file__).resolve().parents[4] / \
    "derivatives/full_dataset_C010"

HC_SUBJECTS = [f"{i:02d}" for i in range(1, 8)]
CVD_SUBJECTS = [f"{i:02d}" for i in range(8, 11)]


# ============================================================================
# Shared Functions
# ============================================================================

def fit_W(X, hues, n_channels=6, alpha=0):
    """Fit encoding weights W from pooled trials.

    Args:
        X: (n_samples, n_voxels) - pooled brain patterns
        hues: (n_samples,) - hue angle (0-359) for each trial
        n_channels: Number of basis function channels
        alpha: Ridge regularization (0 = OLS)

    Returns:
        W: (n_channels, n_voxels) encoding weights
        basis_full: (360, n_channels) for prediction
    """
    basis_full = create_basis_functions(n_channels=n_channels)
    C = basis_full[hues]  # (n_samples, n_channels)

    if alpha > 0:
        W = np.linalg.solve(
            C.T @ C + alpha * np.eye(n_channels),
            C.T @ X
        )
    else:
        W = np.linalg.pinv(C) @ X

    return W, basis_full


def decode_with_W(W, basis_full, X_test):
    """Predict hue using correlation template matching."""
    channel_responses = W @ X_test.T
    n_samples = X_test.shape[0]
    pred_hues = np.zeros(n_samples)
    for i in range(n_samples):
        resp = channel_responses[:, i]
        corrs = np.array([np.corrcoef(resp, basis_full[h])[0, 1] for h in range(360)])
        pred_hues[i] = np.nanargmax(corrs)
    return pred_hues


def compute_group_W(other_amps_dict):
    """Compute group W from other subjects' pooled data.

    Args:
        other_amps_dict: {subj_id: (n_runs, n_colors, n_voxels)}

    Returns:
        W_group: (n_channels, n_voxels)
        basis_full: (360, n_channels)
    """
    all_hues = np.array(HUE_ANGLES)
    W_others = []
    for s, amp in other_amps_dict.items():
        n_r, n_c, n_v = amp.shape
        X_pooled = amp.reshape(-1, n_v)
        hues_pooled = np.tile(all_hues, n_r)
        W_s, _ = fit_W(X_pooled, hues_pooled)
        W_others.append(W_s)
    W_group = np.mean(W_others, axis=0)
    basis_full = create_basis_functions(n_channels=6)
    return W_group, basis_full


def baseline_cv(amp, cv_type='loco'):
    """Standard CV baseline (no group prior).

    Args:
        amp: (n_runs, n_colors, n_voxels)
        cv_type: 'loco' or 'loro'

    Returns:
        mean_mae: float
    """
    n_runs, n_colors, n_voxels = amp.shape
    all_hues = np.array(HUE_ANGLES)
    fold_maes = []

    if cv_type == 'loco':
        for test_color in range(n_colors):
            train_colors = [c for c in range(n_colors) if c != test_color]
            train_hues = np.array([HUE_ANGLES[c] for c in train_colors])
            test_hue = HUE_ANGLES[test_color]
            X_test = amp[:, test_color, :]

            X_train = amp[:, train_colors, :].reshape(-1, n_voxels)
            hues_train = np.tile(train_hues, n_runs)
            W, basis_full = fit_W(X_train, hues_train)
            final_preds = decode_with_W(W, basis_full, X_test)

            errors = circular_distance(np.full(n_runs, test_hue), final_preds)
            fold_maes.append(np.mean(errors))
    else:  # loro
        for test_run in range(n_runs):
            train_runs = [r for r in range(n_runs) if r != test_run]
            X_train = amp[train_runs].reshape(-1, n_voxels)
            hues_train = np.tile(all_hues, len(train_runs))
            W, basis_full = fit_W(X_train, hues_train)

            X_test = amp[test_run]
            final_preds = decode_with_W(W, basis_full, X_test)

            errors = circular_distance(all_hues, final_preds)
            fold_maes.append(np.mean(errors))

    return np.mean(fold_maes)


# ============================================================================
# LOCO Group Prior
# ============================================================================

def loco_with_fixed_lambda(target_amp, other_amps_dict, lambda_fixed):
    """LOCO with FIXED lambda (single pooled W, no ensemble)."""
    n_runs, n_colors, n_voxels = target_amp.shape
    all_hues = np.array(HUE_ANGLES)

    W_group, basis_full = compute_group_W(other_amps_dict)

    fold_maes = []
    for test_color in range(n_colors):
        train_colors = [c for c in range(n_colors) if c != test_color]
        train_hues = np.array([HUE_ANGLES[c] for c in train_colors])
        test_hue = HUE_ANGLES[test_color]
        X_test = target_amp[:, test_color, :]

        X_train = target_amp[:, train_colors, :].reshape(-1, n_voxels)
        hues_train = np.tile(train_hues, n_runs)
        W_ind, _ = fit_W(X_train, hues_train)
        W_combined = lambda_fixed * W_ind + (1 - lambda_fixed) * W_group
        final_preds = decode_with_W(W_combined, basis_full, X_test)

        errors = circular_distance(np.full(n_runs, test_hue), final_preds)
        fold_maes.append(np.mean(errors))

    return np.mean(fold_maes), fold_maes


def nested_loco_lambda_search(target_amp, other_amps_dict, lambda_grid):
    """Nested LOCO for lambda selection (single pooled W only)."""
    n_runs, n_colors, n_voxels = target_amp.shape
    all_hues = np.array(HUE_ANGLES)

    W_group, basis_full = compute_group_W(other_amps_dict)

    outer_fold_maes = []
    selected_lambdas = []

    for outer_test_color in range(n_colors):
        outer_train_colors = [c for c in range(n_colors) if c != outer_test_color]

        # Inner LOCO for lambda selection (on 7 training colors)
        lambda_scores = {lam: [] for lam in lambda_grid}

        for inner_val_color in outer_train_colors:
            inner_train_colors = [c for c in outer_train_colors if c != inner_val_color]
            inner_train_hues = np.array([HUE_ANGLES[c] for c in inner_train_colors])
            inner_val_hue = HUE_ANGLES[inner_val_color]
            X_val = target_amp[:, inner_val_color, :]

            for lam in lambda_grid:
                X_train = target_amp[:, inner_train_colors, :].reshape(-1, n_voxels)
                hues_train = np.tile(inner_train_hues, n_runs)
                W_ind, _ = fit_W(X_train, hues_train)
                W_combined = lam * W_ind + (1 - lam) * W_group
                final_preds = decode_with_W(W_combined, basis_full, X_val)

                errors = circular_distance(np.full(n_runs, inner_val_hue), final_preds)
                lambda_scores[lam].append(np.mean(errors))

        # Select best lambda
        lambda_means = {lam: np.mean(scores) for lam, scores in lambda_scores.items()}
        best_lambda = min(lambda_means, key=lambda_means.get)
        selected_lambdas.append(best_lambda)

        # Test on outer held-out color with best lambda
        outer_train_hues = np.array([HUE_ANGLES[c] for c in outer_train_colors])
        outer_test_hue = HUE_ANGLES[outer_test_color]
        X_test = target_amp[:, outer_test_color, :]

        X_train = target_amp[:, outer_train_colors, :].reshape(-1, n_voxels)
        hues_train = np.tile(outer_train_hues, n_runs)
        W_ind, _ = fit_W(X_train, hues_train)
        W_combined = best_lambda * W_ind + (1 - best_lambda) * W_group
        final_preds = decode_with_W(W_combined, basis_full, X_test)

        errors = circular_distance(np.full(n_runs, outer_test_hue), final_preds)
        outer_fold_maes.append(np.mean(errors))

    best_lambda_overall = max(set(selected_lambdas), key=selected_lambdas.count)
    return best_lambda_overall, outer_fold_maes, selected_lambdas


# ============================================================================
# LORO Group Prior
# ============================================================================

def loro_with_fixed_lambda(target_amp, other_amps_dict, lambda_fixed):
    """LORO with FIXED lambda (single pooled W, no ensemble).

    W_individual: target's 8 colors x (n_runs-1) train runs pooled
    W_group: mean of other HC subjects' pooled W (all 6 runs x 8 colors)
    """
    n_runs, n_colors, n_voxels = target_amp.shape
    all_hues = np.array(HUE_ANGLES)

    W_group, basis_full = compute_group_W(other_amps_dict)

    fold_maes = []
    for test_run in range(n_runs):
        train_runs = [r for r in range(n_runs) if r != test_run]

        X_train = target_amp[train_runs].reshape(-1, n_voxels)
        hues_train = np.tile(all_hues, len(train_runs))
        W_ind, _ = fit_W(X_train, hues_train)
        W_combined = lambda_fixed * W_ind + (1 - lambda_fixed) * W_group

        X_test = target_amp[test_run]
        final_preds = decode_with_W(W_combined, basis_full, X_test)

        errors = circular_distance(all_hues, final_preds)
        fold_maes.append(np.mean(errors))

    return np.mean(fold_maes), fold_maes


def nested_loro_lambda_search(target_amp, other_amps_dict, lambda_grid):
    """Nested LORO for lambda selection (single pooled W only).

    Outer: leave 1 run out (6 folds)
    Inner: leave 1 run out from (n_runs-1) train runs
    """
    n_runs, n_colors, n_voxels = target_amp.shape
    all_hues = np.array(HUE_ANGLES)

    W_group, basis_full = compute_group_W(other_amps_dict)

    outer_fold_maes = []
    selected_lambdas = []

    for outer_test_run in range(n_runs):
        outer_train_runs = [r for r in range(n_runs) if r != outer_test_run]

        # Inner LORO for lambda selection (on train runs)
        lambda_scores = {lam: [] for lam in lambda_grid}

        for inner_val_run in outer_train_runs:
            inner_train_runs = [r for r in outer_train_runs if r != inner_val_run]

            X_inner_train = target_amp[inner_train_runs].reshape(-1, n_voxels)
            hues_inner_train = np.tile(all_hues, len(inner_train_runs))
            X_inner_val = target_amp[inner_val_run]

            for lam in lambda_grid:
                W_ind, _ = fit_W(X_inner_train, hues_inner_train)
                W_combined = lam * W_ind + (1 - lam) * W_group
                pred_hues = decode_with_W(W_combined, basis_full, X_inner_val)
                errors = circular_distance(all_hues, pred_hues)
                lambda_scores[lam].append(np.mean(errors))

        # Select best lambda
        lambda_means = {lam: np.mean(scores) for lam, scores in lambda_scores.items()}
        best_lambda = min(lambda_means, key=lambda_means.get)
        selected_lambdas.append(best_lambda)

        # Test on outer held-out run with best lambda
        X_outer_train = target_amp[outer_train_runs].reshape(-1, n_voxels)
        hues_outer_train = np.tile(all_hues, len(outer_train_runs))
        W_ind, _ = fit_W(X_outer_train, hues_outer_train)
        W_combined = best_lambda * W_ind + (1 - best_lambda) * W_group

        X_test = target_amp[outer_test_run]
        pred_hues = decode_with_W(W_combined, basis_full, X_test)
        errors = circular_distance(all_hues, pred_hues)
        outer_fold_maes.append(np.mean(errors))

    best_lambda_overall = max(set(selected_lambdas), key=selected_lambdas.count)
    return best_lambda_overall, outer_fold_maes, selected_lambdas


# ============================================================================
# Main
# ============================================================================

def run_group_prior(subjects, rois, lambda_values, cv_type, mode, output_dir):
    """Run group prior analysis.

    Args:
        subjects: list of target subject IDs
        rois: list of ROI names
        lambda_values: list of float lambda values
        cv_type: 'loco' or 'loro'
        mode: 'fixed' or 'nested'
        output_dir: Path for output
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    all_results = {}

    for roi in rois:
        print(f"\n{'='*70}")
        print(f"ROI: {roi}")
        print(f"{'='*70}")

        # Load SRM data for all subjects needed
        subjects_to_load = set(HC_SUBJECTS)
        for s in subjects:
            subjects_to_load.add(s)

        all_amps = {}
        for s in subjects_to_load:
            try:
                all_amps[s] = load_amplitudes(str(baseline), s, roi, 'srm')
            except FileNotFoundError:
                print(f"WARNING: sub-{s} {roi} not found, skipping")

        hc_loaded = [s for s in HC_SUBJECTS if s in all_amps]
        print(f"Loaded {len(all_amps)} subjects ({len(hc_loaded)} HC): {sorted(all_amps.keys())}")
        if all_amps:
            print(f"Shape: {list(all_amps.values())[0].shape}")
        print()

        roi_results = {}

        for subj in subjects:
            if subj not in all_amps:
                print(f"WARNING: sub-{subj} not available for {roi}, skipping")
                continue

            # Group prior: HC LOO for HC, all HC for CVD
            if subj in HC_SUBJECTS:
                others = {s: all_amps[s] for s in HC_SUBJECTS
                          if s != subj and s in all_amps}
                print(f"sub-{subj} (HC): Using {len(others)} other HC as group prior")
            else:
                others = {s: all_amps[s] for s in HC_SUBJECTS if s in all_amps}
                print(f"sub-{subj} (CVD): Using {len(others)} HC as group prior")

            # Baseline (no GP)
            mae_base = baseline_cv(all_amps[subj], cv_type=cv_type)

            subj_results = {'baseline': float(mae_base)}

            if mode == 'fixed':
                for lam in lambda_values:
                    if cv_type == 'loco':
                        mae, folds = loco_with_fixed_lambda(
                            all_amps[subj], others, lam)
                    else:
                        mae, folds = loro_with_fixed_lambda(
                            all_amps[subj], others, lam)

                    subj_results[f'lambda_{lam}'] = {
                        'mean_mae': float(mae),
                        'fold_maes': [float(x) for x in folds]
                    }
                    print(f"  sub-{subj} lambda={lam:.2f}: {mae:.1f} deg")

            elif mode == 'nested':
                if cv_type == 'loco':
                    best_lam, maes, lams = nested_loco_lambda_search(
                        all_amps[subj], others, lambda_values)
                else:
                    best_lam, maes, lams = nested_loro_lambda_search(
                        all_amps[subj], others, lambda_values)

                subj_results['GP_nested'] = {
                    'mean_mae': float(np.mean(maes)),
                    'best_lambda': float(best_lam),
                    'per_fold_lambdas': [float(x) for x in lams],
                    'fold_maes': [float(x) for x in maes]
                }
                print(f"  sub-{subj} nested: {np.mean(maes):.1f} deg (best_lambda={best_lam:.2f})")

            roi_results[f'sub-{subj}'] = subj_results

        all_results[roi] = roi_results

    # Save results
    if len(subjects) == 1:
        output_file = output_dir / f'gp_{cv_type}_{mode}_sub-{subjects[0]}.json'
    else:
        output_file = output_dir / f'gp_{cv_type}_{mode}_results.json'

    with open(output_file, 'w') as f:
        json.dump({
            'metadata': {
                'analysis': f'GroupPrior_{cv_type.upper()}_{mode}',
                'cv_type': cv_type,
                'mode': mode,
                'lambda_values': lambda_values,
                'subjects': subjects,
                'rois': rois,
            },
            'results': all_results
        }, f, indent=2)

    print(f"\nResults saved to {output_file}")

    # Print summary
    print(f"\n{'='*70}")
    print(f"SUMMARY ({cv_type.upper()} / {mode})")
    print(f"{'='*70}")

    for roi in rois:
        if roi not in all_results:
            continue
        print(f"\n{roi}:")

        hc_bases, cvd_bases = [], []
        for subj in subjects:
            key = f'sub-{subj}'
            if key not in all_results[roi]:
                continue
            r = all_results[roi][key]
            base = r['baseline']
            group = 'HC' if subj in HC_SUBJECTS else 'CVD'

            if mode == 'nested' and 'GP_nested' in r:
                gp_mae = r['GP_nested']['mean_mae']
                gp_lam = r['GP_nested']['best_lambda']
                delta = gp_mae - base
                print(f"  sub-{subj} ({group}): baseline={base:.1f} GP={gp_mae:.1f} (lambda={gp_lam:.2f}) delta={delta:+.1f}")
            else:
                print(f"  sub-{subj} ({group}): baseline={base:.1f}")

            if group == 'HC':
                hc_bases.append(base)
            else:
                cvd_bases.append(base)

        if hc_bases:
            print(f"  HC mean baseline: {np.mean(hc_bases):.1f}")
        if cvd_bases:
            print(f"  CVD mean baseline: {np.mean(cvd_bases):.1f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Group Prior for Forward Encoding (LOCO/LORO)")
    parser.add_argument('--cv', type=str, default='loco',
                        choices=['loco', 'loro'],
                        help='CV protocol: loco or loro')
    parser.add_argument('--mode', type=str, default='fixed',
                        choices=['fixed', 'nested'],
                        help='Lambda selection: fixed grid or nested CV')
    parser.add_argument('--subjects', nargs='+', default=None,
                        help='Target subjects (default: all 10)')
    parser.add_argument('--rois', nargs='+', default=['V1', 'V2', 'V3', 'V4'])
    parser.add_argument('--lambda_values', type=str,
                        default='0.0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0',
                        help='Comma-separated lambda values')
    parser.add_argument('--output_dir', type=str, default=None,
                        help='Output directory')
    args = parser.parse_args()

    # Parse lambda values
    lambda_values = [float(x) for x in args.lambda_values.split(',')]

    # Default subjects
    if args.subjects is None:
        args.subjects = [f"{i:02d}" for i in range(1, 11)]

    # Default output dir
    if args.output_dir is None:
        args.output_dir = str(
            Path(__file__).resolve().parents[1] /
            f'results/FE_group_prior/{args.cv}_{args.mode}'
        )

    print(f"Group Prior Validation")
    print(f"  CV: {args.cv.upper()}")
    print(f"  Mode: {args.mode}")
    print(f"  Subjects: {args.subjects}")
    print(f"  ROIs: {args.rois}")
    print(f"  Lambda: {lambda_values}")
    print()

    run_group_prior(
        subjects=args.subjects,
        rois=args.rois,
        lambda_values=lambda_values,
        cv_type=args.cv,
        mode=args.mode,
        output_dir=args.output_dir,
    )
