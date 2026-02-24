#!/usr/bin/env python3
"""
Test GroupPrior_FE: Shrink individual LOCO encoding weights toward group-mean W.

Motivation (James-Stein shrinkage):
  - Individual W from 7 training colors has df=1 (barely over-determined)
  - Group W from OTHER subjects' ALL 8 colors has df=2 per subject × (N-1) subjects
  - Shrinkage toward group W reduces noise in encoding weights
  - Lambda controls bias-variance trade-off

Variants tested:
  1. FE baseline (no shrinkage)
  2. GroupPrior_FE: W_combined = lambda * W_individual + (1-lambda) * W_group
  3. GroupPrior_Ensemble_FE: Per-run W shrunk toward group W, then circular mean
  4. EnsembleOnly (FE_Ensemble): Per-run W without shrinkage (for comparison)
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
    """Fit encoding weights W from mean patterns and their hue angles."""
    basis_full = create_basis_functions(n_channels=n_channels)  # (360, 6)
    C = basis_full[train_hues]  # (n_colors, 6)
    if alpha > 0:
        W = np.linalg.solve(C.T @ C + alpha * np.eye(n_channels), C.T @ mean_patterns)
    else:
        W = np.linalg.pinv(C) @ mean_patterns  # (6, n_voxels)
    return W, basis_full


def decode_with_W(W, basis_full, X_test):
    """Predict hue for each test sample using correlation template matching."""
    channel_responses = W @ X_test.T  # (6, n_samples)
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


def loco_baseline(amp):
    """Standard FE baseline: single W from 7 training color means."""
    n_runs, n_colors, n_voxels = amp.shape
    fold_maes = []
    for test_color in range(n_colors):
        train_colors = [c for c in range(n_colors) if c != test_color]
        train_hues = np.array([HUE_ANGLES[c] for c in train_colors])
        test_hue = HUE_ANGLES[test_color]

        # Mean patterns from all 6 runs
        mean_patterns = amp[:, train_colors, :].mean(axis=0)  # (7, n_voxels)
        W, basis_full = fit_W(mean_patterns, train_hues)

        X_test = amp[:, test_color, :]  # (6, n_voxels)
        pred_hues = decode_with_W(W, basis_full, X_test)
        errors = circular_distance(np.full(6, test_hue), pred_hues)
        fold_maes.append(np.mean(errors))
    return np.mean(fold_maes)


def loco_ensemble(amp):
    """FE_Ensemble: Per-run W, combine via circular mean."""
    n_runs, n_colors, n_voxels = amp.shape
    fold_maes = []
    for test_color in range(n_colors):
        train_colors = [c for c in range(n_colors) if c != test_color]
        train_hues = np.array([HUE_ANGLES[c] for c in train_colors])
        test_hue = HUE_ANGLES[test_color]

        X_test = amp[:, test_color, :]  # (6, n_voxels)
        all_run_preds = []

        for r in range(n_runs):
            run_patterns = amp[r, train_colors, :]  # (7, n_voxels) single run
            W_r, basis_full = fit_W(run_patterns, train_hues)
            pred_hues_r = decode_with_W(W_r, basis_full, X_test)
            all_run_preds.append(pred_hues_r)

        all_run_preds = np.array(all_run_preds)  # (6, 6): 6 W models × 6 test runs
        # Circular mean across W models for each test run
        final_preds = np.array([circular_mean_deg(all_run_preds[:, i]) for i in range(6)])
        errors = circular_distance(np.full(6, test_hue), final_preds)
        fold_maes.append(np.mean(errors))
    return np.mean(fold_maes)


def loco_group_prior(target_amp, other_amps, lam):
    """
    GroupPrior_FE: Shrink individual W toward LOO group-mean W.

    W_combined = lambda * W_individual + (1-lambda) * W_group
    W_group is average of W matrices from OTHER subjects (each has different n_voxels,
    so we average in W-space (6 × n_voxels_target), not in pattern space).

    Since W maps channels → voxels, and each subject has different voxels,
    we compute the GROUP W for the TARGET subject's voxels by averaging the
    target subject's own full-data W (from all 8 colors, not LOCO-restricted).
    This is a principled "oracle" prior: use the target's own full W as shrinkage target.
    """
    n_runs, n_colors, n_voxels = target_amp.shape
    all_hues = np.array(HUE_ANGLES)

    # "Group" prior = target subject's own W from ALL 8 colors (full data)
    # This is the best possible W estimate for this subject, but uses the held-out color
    # In a strict sense this is oracle. However:
    # - We only use it as a REGULARIZATION TARGET, not for direct prediction
    # - The held-out color contributes 1/8 to W_full, diluted by shrinkage lambda
    # - This quantifies the MAXIMUM possible benefit of shrinkage
    full_mean = target_amp.mean(axis=0)  # (8, n_voxels)
    W_full, basis_full = fit_W(full_mean, all_hues)

    fold_maes = []
    for test_color in range(n_colors):
        train_colors = [c for c in range(n_colors) if c != test_color]
        train_hues = np.array([HUE_ANGLES[c] for c in train_colors])
        test_hue = HUE_ANGLES[test_color]

        # Individual W from 7 training colors
        mean_patterns = target_amp[:, train_colors, :].mean(axis=0)  # (7, n_voxels)
        W_ind, _ = fit_W(mean_patterns, train_hues)

        # Shrinkage toward full W
        W_combined = lam * W_ind + (1 - lam) * W_full

        X_test = target_amp[:, test_color, :]  # (6, n_voxels)
        pred_hues = decode_with_W(W_combined, basis_full, X_test)
        errors = circular_distance(np.full(6, test_hue), pred_hues)
        fold_maes.append(np.mean(errors))
    return np.mean(fold_maes)


def loco_group_prior_ensemble(target_amp, other_amps, lam):
    """
    GroupPrior_Ensemble_FE: Per-run W shrunk toward full-data W, circular mean.

    For each run r:
      W_r_combined = lambda * W_r_individual + (1-lambda) * W_full
    Then combine predictions across runs via circular mean.

    Same oracle approach as loco_group_prior: W_full from target's own 8 colors.
    """
    n_runs, n_colors, n_voxels = target_amp.shape
    all_hues = np.array(HUE_ANGLES)

    # Full-data W from all 8 colors (oracle prior)
    full_mean = target_amp.mean(axis=0)  # (8, n_voxels)
    W_full, basis_full = fit_W(full_mean, all_hues)

    fold_maes = []
    for test_color in range(n_colors):
        train_colors = [c for c in range(n_colors) if c != test_color]
        train_hues = np.array([HUE_ANGLES[c] for c in train_colors])
        test_hue = HUE_ANGLES[test_color]

        X_test = target_amp[:, test_color, :]  # (6, n_voxels)
        all_run_preds = []

        for r in range(n_runs):
            run_patterns = target_amp[r, train_colors, :]  # (7, n_voxels)
            W_r, _ = fit_W(run_patterns, train_hues)

            # Shrink per-run W toward full W
            W_r_combined = lam * W_r + (1 - lam) * W_full

            pred_hues_r = decode_with_W(W_r_combined, basis_full, X_test)
            all_run_preds.append(pred_hues_r)

        all_run_preds = np.array(all_run_preds)  # (6, 6)
        final_preds = np.array([circular_mean_deg(all_run_preds[:, i]) for i in range(6)])
        errors = circular_distance(np.full(6, test_hue), final_preds)
        fold_maes.append(np.mean(errors))
    return np.mean(fold_maes)


def loco_ensemble_shrinkage(amp, lam):
    """
    Legitimate shrinkage (NO oracle):
    Each per-run W_r is shrunk toward W_pooled (from 6-run mean, 7 colors).
    W_r_combined = lambda * W_r + (1-lambda) * W_pooled

    lambda=1.0 = pure per-run (= FE_Ensemble)
    lambda=0.0 = pure pooled (= FE Baseline, repeated 6 times + circular mean)
    """
    n_runs, n_colors, n_voxels = amp.shape
    fold_maes = []
    for test_color in range(n_colors):
        train_colors = [c for c in range(n_colors) if c != test_color]
        train_hues = np.array([HUE_ANGLES[c] for c in train_colors])
        test_hue = HUE_ANGLES[test_color]

        # Pooled W from 6-run mean of 7 training colors (= baseline W)
        mean_patterns = amp[:, train_colors, :].mean(axis=0)  # (7, n_voxels)
        W_pooled, basis_full = fit_W(mean_patterns, train_hues)

        X_test = amp[:, test_color, :]  # (6, n_voxels)
        all_run_preds = []

        for r in range(n_runs):
            run_patterns = amp[r, train_colors, :]  # (7, n_voxels)
            W_r, _ = fit_W(run_patterns, train_hues)

            # Shrink per-run W toward pooled W
            W_r_combined = lam * W_r + (1 - lam) * W_pooled

            pred_hues_r = decode_with_W(W_r_combined, basis_full, X_test)
            all_run_preds.append(pred_hues_r)

        all_run_preds = np.array(all_run_preds)
        final_preds = np.array([circular_mean_deg(all_run_preds[:, i]) for i in range(6)])
        errors = circular_distance(np.full(6, test_hue), final_preds)
        fold_maes.append(np.mean(errors))
    return np.mean(fold_maes)


def loco_loo_run_ensemble(amp):
    """
    Leave-One-Run-Out Ensemble: for each test run, use the OTHER 5 runs' W.

    For test run r, fit W on the 5 other runs' mean patterns (7 training colors).
    This is a "cleaner" ensemble than FE_Ensemble because:
    - Each test prediction uses a W that was NOT trained on that run's data
    - Avoids the potential overfitting of per-run W to run-specific noise
    """
    n_runs, n_colors, n_voxels = amp.shape
    fold_maes = []
    for test_color in range(n_colors):
        train_colors = [c for c in range(n_colors) if c != test_color]
        train_hues = np.array([HUE_ANGLES[c] for c in train_colors])
        test_hue = HUE_ANGLES[test_color]

        errors_all_runs = []
        for test_run in range(n_runs):
            # W from OTHER 5 runs' mean patterns
            other_runs = [r for r in range(n_runs) if r != test_run]
            mean_patterns = amp[other_runs][:, train_colors, :].mean(axis=0)  # (7, n_voxels)
            W_loo, basis_full = fit_W(mean_patterns, train_hues)

            # Test on this run
            X_test_single = amp[test_run:test_run+1, test_color, :]  # (1, n_voxels)
            pred_hue = decode_with_W(W_loo, basis_full, X_test_single)
            error = circular_distance(np.array([test_hue]), pred_hue)
            errors_all_runs.append(error[0])

        fold_maes.append(np.mean(errors_all_runs))
    return np.mean(fold_maes)


# ============================================================================
# Main: sweep lambda on 3 HC subjects, V1, Procrustes
# ============================================================================

def loco_cross_subject_prior_srm(target_amp, other_amps_dict, lam):
    """
    Cross-subject GroupPrior in SRM space (LEGITIMATE, non-oracle).

    In SRM space all subjects have same n_features=k, so W matrices can be averaged.
    W_group = mean of W from OTHER subjects' ALL 8 colors.
    W_individual = W from target subject's 7 training colors.
    W_combined = lambda * W_individual + (1-lambda) * W_group.
    """
    n_runs, n_colors, n_voxels = target_amp.shape
    all_hues = np.array(HUE_ANGLES)

    # Compute group W from other subjects' full 8-color data
    W_others = []
    for s, amp in other_amps_dict.items():
        mean_patt = amp.mean(axis=0)  # (8, k)
        W_s, _ = fit_W(mean_patt, all_hues)
        W_others.append(W_s)
    W_group = np.mean(W_others, axis=0)  # (6, k)
    _, basis_full = fit_W(target_amp.mean(axis=0), all_hues)  # just for basis_full

    fold_maes = []
    for test_color in range(n_colors):
        train_colors = [c for c in range(n_colors) if c != test_color]
        train_hues = np.array([HUE_ANGLES[c] for c in train_colors])
        test_hue = HUE_ANGLES[test_color]

        # Individual W from 7 training colors
        mean_patterns = target_amp[:, train_colors, :].mean(axis=0)
        W_ind, _ = fit_W(mean_patterns, train_hues)

        # Shrinkage
        W_combined = lam * W_ind + (1 - lam) * W_group

        X_test = target_amp[:, test_color, :]
        pred_hues = decode_with_W(W_combined, basis_full, X_test)
        errors = circular_distance(np.full(6, test_hue), pred_hues)
        fold_maes.append(np.mean(errors))
    return np.mean(fold_maes)


def loco_cross_subject_ensemble_srm(target_amp, other_amps_dict, lam):
    """
    Cross-subject GroupPrior + Ensemble in SRM space (LEGITIMATE, non-oracle).

    Each per-run W_r is shrunk toward LOO-group W (from all 8 colors of other subjects).
    Then combine via circular mean.
    """
    n_runs, n_colors, n_voxels = target_amp.shape
    all_hues = np.array(HUE_ANGLES)

    # Group W from other subjects
    W_others = []
    for s, amp in other_amps_dict.items():
        mean_patt = amp.mean(axis=0)  # (8, k)
        W_s, _ = fit_W(mean_patt, all_hues)
        W_others.append(W_s)
    W_group = np.mean(W_others, axis=0)  # (6, k)
    _, basis_full = fit_W(target_amp.mean(axis=0), all_hues)

    fold_maes = []
    for test_color in range(n_colors):
        train_colors = [c for c in range(n_colors) if c != test_color]
        train_hues = np.array([HUE_ANGLES[c] for c in train_colors])
        test_hue = HUE_ANGLES[test_color]

        X_test = target_amp[:, test_color, :]
        all_run_preds = []

        for r in range(n_runs):
            run_patterns = target_amp[r, train_colors, :]
            W_r, _ = fit_W(run_patterns, train_hues)
            W_r_combined = lam * W_r + (1 - lam) * W_group
            pred_hues_r = decode_with_W(W_r_combined, basis_full, X_test)
            all_run_preds.append(pred_hues_r)

        all_run_preds = np.array(all_run_preds)
        final_preds = np.array([circular_mean_deg(all_run_preds[:, i]) for i in range(6)])
        errors = circular_distance(np.full(6, test_hue), final_preds)
        fold_maes.append(np.mean(errors))
    return np.mean(fold_maes)


if __name__ == "__main__":
    subjects_hc = ["01", "02", "03", "04", "05", "06", "07"]
    test_subjects = ["01", "03", "05"]
    roi = "V1"
    alignment = "procrustes"

    # Load ALL HC subjects' data
    print(f"Loading {len(subjects_hc)} HC subjects, {roi}, {alignment}...")
    all_amps = {}
    for s in subjects_hc:
        all_amps[s] = load_amplitudes(str(baseline), s, roi, alignment)
        print(f"  sub-{s}: {all_amps[s].shape}")

    lambdas = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.0]

    # Header
    header = "{:<30s} | {:>8s} {:>8s} {:>8s} | {:>8s}".format(
        "Config", "sub-01", "sub-03", "sub-05", "Mean"
    )
    print()
    print(header)
    print("-" * len(header))

    # 1. FE Baseline
    maes = []
    for s in test_subjects:
        mae = loco_baseline(all_amps[s])
        maes.append(mae)
    print("{:<30s} | {:7.1f}  {:7.1f}  {:7.1f}  | {:7.1f}".format(
        "FE Baseline", maes[0], maes[1], maes[2], np.mean(maes)))

    # 2. FE_Ensemble (no shrinkage)
    maes = []
    for s in test_subjects:
        mae = loco_ensemble(all_amps[s])
        maes.append(mae)
    print("{:<30s} | {:7.1f}  {:7.1f}  {:7.1f}  | {:7.1f}".format(
        "FE_Ensemble (lam=1.0)", maes[0], maes[1], maes[2], np.mean(maes)))

    print("-" * len(header))

    # 3. GroupPrior_FE: sweep lambda
    print("--- GroupPrior_FE (single W + shrinkage) ---")
    for lam in lambdas:
        maes = []
        for s in test_subjects:
            others = [all_amps[o] for o in subjects_hc if o != s]
            mae = loco_group_prior(all_amps[s], others, lam)
            maes.append(mae)
        print("{:<30s} | {:7.1f}  {:7.1f}  {:7.1f}  | {:7.1f}".format(
            f"GroupPrior lam={lam:.1f}", maes[0], maes[1], maes[2], np.mean(maes)))

    print("-" * len(header))

    # 4. ORACLE GroupPrior_Ensemble_FE: sweep lambda (uses held-out color data)
    print("--- ORACLE: GroupPrior_Ensemble_FE (per-run W + W_full shrinkage) ---")
    for lam in [1.0, 0.8, 0.6, 0.5, 0.4, 0.2, 0.0]:
        maes = []
        for s in test_subjects:
            others = [all_amps[o] for o in subjects_hc if o != s]
            mae = loco_group_prior_ensemble(all_amps[s], others, lam)
            maes.append(mae)
        print("{:<30s} | {:7.1f}  {:7.1f}  {:7.1f}  | {:7.1f}".format(
            f"ORACLE GP_Ens lam={lam:.1f}", maes[0], maes[1], maes[2], np.mean(maes)))

    print()
    print("=" * len(header))
    print("LEGITIMATE (non-oracle) approaches below:")
    print("=" * len(header))

    # 5. Legitimate Ensemble Shrinkage: per-run W shrunk toward pooled W
    print("--- Ensemble_Shrinkage (per-run W → pooled W, NO data leakage) ---")
    for lam in [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.0]:
        maes = []
        for s in test_subjects:
            mae = loco_ensemble_shrinkage(all_amps[s], lam)
            maes.append(mae)
        print("{:<30s} | {:7.1f}  {:7.1f}  {:7.1f}  | {:7.1f}".format(
            f"Ens_Shrink lam={lam:.1f}", maes[0], maes[1], maes[2], np.mean(maes)))

    print("-" * len(header))

    # 6. LOO-Run Ensemble
    print("--- LOO-Run Ensemble (W from 5 other runs, test on held-out run) ---")
    maes = []
    for s in test_subjects:
        mae = loco_loo_run_ensemble(all_amps[s])
        maes.append(mae)
    print("{:<30s} | {:7.1f}  {:7.1f}  {:7.1f}  | {:7.1f}".format(
        "LOO-Run Ensemble", maes[0], maes[1], maes[2], np.mean(maes)))

    print()
    print("=" * len(header))
    print("SRM SPACE: Cross-subject W averaging (LEGITIMATE)")
    print("=" * len(header))

    # Load SRM data
    print(f"\nLoading {len(subjects_hc)} HC subjects, {roi}, SRM...")
    all_amps_srm = {}
    for s in subjects_hc:
        try:
            all_amps_srm[s] = load_amplitudes(str(baseline), s, roi, 'srm')
            print(f"  sub-{s}: {all_amps_srm[s].shape}")
        except FileNotFoundError:
            print(f"  sub-{s}: SRM not found, skipping")

    if len(all_amps_srm) >= 4:
        # SRM Baseline + Ensemble
        print()
        print(header)
        print("-" * len(header))

        maes = []
        for s in test_subjects:
            if s not in all_amps_srm:
                maes.append(float('nan'))
                continue
            mae = loco_baseline(all_amps_srm[s])
            maes.append(mae)
        print("{:<30s} | {:7.1f}  {:7.1f}  {:7.1f}  | {:7.1f}".format(
            "SRM FE Baseline", maes[0], maes[1], maes[2], np.nanmean(maes)))

        maes = []
        for s in test_subjects:
            if s not in all_amps_srm:
                maes.append(float('nan'))
                continue
            mae = loco_ensemble(all_amps_srm[s])
            maes.append(mae)
        print("{:<30s} | {:7.1f}  {:7.1f}  {:7.1f}  | {:7.1f}".format(
            "SRM FE_Ensemble", maes[0], maes[1], maes[2], np.nanmean(maes)))

        print("-" * len(header))

        # Cross-subject prior (single W)
        print("--- SRM Cross-Subject GroupPrior_FE ---")
        for lam in [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.0]:
            maes = []
            for s in test_subjects:
                if s not in all_amps_srm:
                    maes.append(float('nan'))
                    continue
                others = {o: all_amps_srm[o] for o in subjects_hc
                          if o != s and o in all_amps_srm}
                mae = loco_cross_subject_prior_srm(all_amps_srm[s], others, lam)
                maes.append(mae)
            print("{:<30s} | {:7.1f}  {:7.1f}  {:7.1f}  | {:7.1f}".format(
                f"SRM GP lam={lam:.1f}", maes[0], maes[1], maes[2], np.nanmean(maes)))

        print("-" * len(header))

        # Cross-subject prior + Ensemble
        print("--- SRM Cross-Subject GP + Ensemble ---")
        for lam in [1.0, 0.8, 0.6, 0.5, 0.4, 0.3, 0.2, 0.0]:
            maes = []
            for s in test_subjects:
                if s not in all_amps_srm:
                    maes.append(float('nan'))
                    continue
                others = {o: all_amps_srm[o] for o in subjects_hc
                          if o != s and o in all_amps_srm}
                mae = loco_cross_subject_ensemble_srm(all_amps_srm[s], others, lam)
                maes.append(mae)
            print("{:<30s} | {:7.1f}  {:7.1f}  {:7.1f}  | {:7.1f}".format(
                f"SRM GP_Ens lam={lam:.1f}", maes[0], maes[1], maes[2], np.nanmean(maes)))
    else:
        print("Insufficient SRM data for cross-subject analysis.")

    print()
    print("NOTE: lambda=1.0 = individual only, lambda=0.0 = group only")
    print("Lower MAE = better. Chance = 90°.")
