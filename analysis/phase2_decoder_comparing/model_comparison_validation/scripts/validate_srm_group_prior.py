#!/usr/bin/env python3
"""
SRM GroupPrior validation: Nested LOCO for lambda selection.

Design:
  - Outer LOCO: hold out 1 test color (8 folds)
  - Inner LOCO: hold out 1 validation color from remaining 7 (7 sub-folds)
  - Lambda grid search on validation set
  - Test on outer held-out color with best lambda

Models:
  1. SRM Baseline (single W from 6-run mean)
  2. SRM Ensemble (per-run W, no shrinkage)
  3. SRM GroupPrior (single W + shrinkage)
  4. SRM GroupPrior_Ensemble (per-run W + shrinkage)
"""
import sys
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_loco_comparison import (
    load_amplitudes, create_basis_functions, circular_distance,
    HUE_ANGLES,
)

baseline = Path(__file__).resolve().parents[4] / \
    "analysis/phase1_preprocess_decoding/results/full_dataset_C010"


def fit_W(mean_patterns, train_hues, n_channels=6, alpha=0):
    """Fit encoding weights W from mean patterns."""
    basis_full = create_basis_functions(n_channels=n_channels)
    C = basis_full[train_hues]
    if alpha > 0:
        W = np.linalg.solve(C.T @ C + alpha * np.eye(n_channels), C.T @ mean_patterns)
    else:
        W = np.linalg.pinv(C) @ mean_patterns
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


def circular_mean_deg(angles_deg):
    """Circular mean of angles in degrees."""
    rads = np.deg2rad(angles_deg)
    mean_sin = np.mean(np.sin(rads))
    mean_cos = np.mean(np.cos(rads))
    return np.rad2deg(np.arctan2(mean_sin, mean_cos)) % 360


def nested_loco_lambda_search(target_amp, other_amps_dict, lambda_grid, use_ensemble=False):
    """
    Nested LOCO for lambda selection.

    Returns: best_lambda, outer_fold_maes
    """
    n_runs, n_colors, n_voxels = target_amp.shape
    all_hues = np.array(HUE_ANGLES)

    # Precompute group W from other subjects (all 8 colors)
    W_others = []
    for s, amp in other_amps_dict.items():
        mean_patt = amp.mean(axis=0)
        W_s, _ = fit_W(mean_patt, all_hues)
        W_others.append(W_s)
    W_group = np.mean(W_others, axis=0)
    _, basis_full = fit_W(target_amp.mean(axis=0), all_hues)

    outer_fold_maes = []
    selected_lambdas = []

    # Outer LOCO: 8 folds
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
                if use_ensemble:
                    # Per-run W + shrinkage
                    all_run_preds = []
                    for r in range(n_runs):
                        run_patterns = target_amp[r, inner_train_colors, :]
                        W_r, _ = fit_W(run_patterns, inner_train_hues)
                        W_r_combined = lam * W_r + (1 - lam) * W_group
                        pred_hues_r = decode_with_W(W_r_combined, basis_full, X_val)
                        all_run_preds.append(pred_hues_r)
                    all_run_preds = np.array(all_run_preds)
                    final_preds = np.array([circular_mean_deg(all_run_preds[:, i])
                                           for i in range(n_runs)])
                else:
                    # Single W + shrinkage
                    mean_patterns = target_amp[:, inner_train_colors, :].mean(axis=0)
                    W_ind, _ = fit_W(mean_patterns, inner_train_hues)
                    W_combined = lam * W_ind + (1 - lam) * W_group
                    final_preds = decode_with_W(W_combined, basis_full, X_val)

                errors = circular_distance(np.full(n_runs, inner_val_hue), final_preds)
                lambda_scores[lam].append(np.mean(errors))

        # Select best lambda (min mean MAE across 7 inner folds)
        lambda_means = {lam: np.mean(scores) for lam, scores in lambda_scores.items()}
        best_lambda = min(lambda_means, key=lambda_means.get)
        selected_lambdas.append(best_lambda)

        # Test on outer held-out color with best lambda
        outer_train_hues = np.array([HUE_ANGLES[c] for c in outer_train_colors])
        outer_test_hue = HUE_ANGLES[outer_test_color]
        X_test = target_amp[:, outer_test_color, :]

        if use_ensemble:
            all_run_preds = []
            for r in range(n_runs):
                run_patterns = target_amp[r, outer_train_colors, :]
                W_r, _ = fit_W(run_patterns, outer_train_hues)
                W_r_combined = best_lambda * W_r + (1 - best_lambda) * W_group
                pred_hues_r = decode_with_W(W_r_combined, basis_full, X_test)
                all_run_preds.append(pred_hues_r)
            all_run_preds = np.array(all_run_preds)
            final_preds = np.array([circular_mean_deg(all_run_preds[:, i]) for i in range(n_runs)])
        else:
            mean_patterns = target_amp[:, outer_train_colors, :].mean(axis=0)
            W_ind, _ = fit_W(mean_patterns, outer_train_hues)
            W_combined = best_lambda * W_ind + (1 - best_lambda) * W_group
            final_preds = decode_with_W(W_combined, basis_full, X_test)

        errors = circular_distance(np.full(n_runs, outer_test_hue), final_preds)
        outer_fold_maes.append(np.mean(errors))

    # Return most frequent lambda and MAEs
    best_lambda_overall = max(set(selected_lambdas), key=selected_lambdas.count)
    return best_lambda_overall, outer_fold_maes, selected_lambdas


def baseline_loco(amp, use_ensemble=False):
    """Standard LOCO (no group prior)."""
    n_runs, n_colors, n_voxels = amp.shape
    all_hues = np.array(HUE_ANGLES)
    fold_maes = []

    for test_color in range(n_colors):
        train_colors = [c for c in range(n_colors) if c != test_color]
        train_hues = np.array([HUE_ANGLES[c] for c in train_colors])
        test_hue = HUE_ANGLES[test_color]
        X_test = amp[:, test_color, :]

        if use_ensemble:
            all_run_preds = []
            for r in range(n_runs):
                run_patterns = amp[r, train_colors, :]
                W_r, basis_full = fit_W(run_patterns, train_hues)
                pred_hues_r = decode_with_W(W_r, basis_full, X_test)
                all_run_preds.append(pred_hues_r)
            all_run_preds = np.array(all_run_preds)
            final_preds = np.array([circular_mean_deg(all_run_preds[:, i]) for i in range(n_runs)])
        else:
            mean_patterns = amp[:, train_colors, :].mean(axis=0)
            W, basis_full = fit_W(mean_patterns, train_hues)
            final_preds = decode_with_W(W, basis_full, X_test)

        errors = circular_distance(np.full(n_runs, test_hue), final_preds)
        fold_maes.append(np.mean(errors))

    return np.mean(fold_maes)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--subjects', nargs='+', default=None,
                       help='Subject IDs (default: all HC 01-07)')
    parser.add_argument('--rois', nargs='+', default=['V1', 'V2', 'V3', 'V4'])
    parser.add_argument('--lambda_grid', type=str, default='0.0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0')
    args = parser.parse_args()

    subjects_hc = args.subjects if args.subjects else ["01", "02", "03", "04", "05", "06", "07"]
    lambda_grid = [float(x) for x in args.lambda_grid.split(',')]

    print(f"SRM GroupPrior Validation")
    print(f"Subjects: {subjects_hc}")
    print(f"ROIs: {args.rois}")
    print(f"Lambda grid: {lambda_grid}")
    print()

    # Load SRM data
    all_amps_srm = {}
    for s in subjects_hc:
        try:
            all_amps_srm[s] = load_amplitudes(str(baseline), s, args.rois[0], 'srm')
        except FileNotFoundError:
            print(f"WARNING: sub-{s} SRM not found, skipping")

    if len(all_amps_srm) < 3:
        print("ERROR: Insufficient SRM data (need >=3 subjects)")
        sys.exit(1)

    for roi in args.rois:
        print(f"\n{'='*70}")
        print(f"ROI: {roi}")
        print(f"{'='*70}")

        # Reload for this ROI
        all_amps_srm = {}
        for s in subjects_hc:
            try:
                all_amps_srm[s] = load_amplitudes(str(baseline), s, roi, 'srm')
            except FileNotFoundError:
                continue

        print(f"Loaded {len(all_amps_srm)} subjects: {list(all_amps_srm.keys())}")
        print(f"Shape: {list(all_amps_srm.values())[0].shape}")
        print()

        results = {}

        # Baseline methods
        for subj in all_amps_srm:
            mae_base = baseline_loco(all_amps_srm[subj], use_ensemble=False)
            mae_ens = baseline_loco(all_amps_srm[subj], use_ensemble=True)
            results[subj] = {
                'Baseline': mae_base,
                'Ensemble': mae_ens,
            }

        # GroupPrior with nested lambda
        for subj in all_amps_srm:
            others = {s: all_amps_srm[s] for s in all_amps_srm if s != subj}

            print(f"sub-{subj}: Nested LOCO lambda search (single W)...")
            best_lam_single, maes_single, lams_single = nested_loco_lambda_search(
                all_amps_srm[subj], others, lambda_grid, use_ensemble=False
            )
            results[subj]['GP_single'] = np.mean(maes_single)
            results[subj]['GP_single_lambda'] = best_lam_single

            print(f"sub-{subj}: Nested LOCO lambda search (ensemble)...")
            best_lam_ens, maes_ens, lams_ens = nested_loco_lambda_search(
                all_amps_srm[subj], others, lambda_grid, use_ensemble=True
            )
            results[subj]['GP_ensemble'] = np.mean(maes_ens)
            results[subj]['GP_ensemble_lambda'] = best_lam_ens

        # Print results
        print()
        print(f"{'Subject':<10} {'Baseline':>10} {'Ensemble':>10} {'GP_single':>10} {'λ_s':>6} {'GP_ens':>10} {'λ_e':>6}")
        print("-" * 70)
        for subj in sorted(all_amps_srm.keys()):
            r = results[subj]
            print(f"sub-{subj:<6} {r['Baseline']:>10.1f} {r['Ensemble']:>10.1f} "
                  f"{r['GP_single']:>10.1f} {r['GP_single_lambda']:>6.2f} "
                  f"{r['GP_ensemble']:>10.1f} {r['GP_ensemble_lambda']:>6.2f}")

        # Group means
        base_mean = np.mean([r['Baseline'] for r in results.values()])
        ens_mean = np.mean([r['Ensemble'] for r in results.values()])
        gp_single_mean = np.mean([r['GP_single'] for r in results.values()])
        gp_ens_mean = np.mean([r['GP_ensemble'] for r in results.values()])

        print("-" * 70)
        print(f"{'MEAN':<10} {base_mean:>10.1f} {ens_mean:>10.1f} "
              f"{gp_single_mean:>10.1f} {'':>6} {gp_ens_mean:>10.1f}")
        print()

        # Deltas
        print(f"Δ vs Baseline:")
        print(f"  Ensemble:     {ens_mean - base_mean:+.1f}°")
        print(f"  GP_single:    {gp_single_mean - base_mean:+.1f}°")
        print(f"  GP_ensemble:  {gp_ens_mean - base_mean:+.1f}°")

    print(f"\n{'='*70}")
    print("Validation complete. Chance = 90°, lower MAE = better.")
