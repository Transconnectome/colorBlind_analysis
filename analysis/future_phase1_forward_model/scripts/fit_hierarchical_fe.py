#!/usr/bin/env python3
"""
fit_hierarchical_fe.py — B3: Hierarchical FE with HC group prior.

HC group prior regularises CVD (and HC-LOO) encoding via
prior-centred ridge: min ||X - CW||^2 + lam*||W - W_bar_HC||^2.

Nested 8-fold LOCO: outer holds out 1 color, inner 7-fold selects lambda,
outer evaluates with pooled runs.

HC prior: LOO for HC subjects (6 remaining HC), full 7 HC for CVD.

Usage:
    python fit_hierarchical_fe.py \
        --baseline_dir /path/to/C010 \
        --output_dir results/hierarchical_fe \
        [--rois V1 V2 V3 V4] [--subjects 01 02 ...]
"""

import argparse
import numpy as np
import json
from pathlib import Path

from utils_forward_model import (
    load_amplitudes, fit_W_ridge, fit_W_prior_ridge, gcv_select_alpha,
    voxel_pattern_correlation, predict_patterns,
    decode_hue, circular_distance,
    compute_rdm, rdm_upper_tri,
    HUE_ANGLES, N_RUNS, ALPHA_GRID,
    HC_SUBJECTS, CVD_SUBJECTS, ALL_SUBJECTS, ROIS,
    save_config, DEFAULT_BASELINE_DIR, get_subject_group,
)
from fit_adaptive_basis import create_basis_adaptive, OPTIMAL_N_CHANNELS

LAMBDA_GRID = [0.001, 0.01, 0.1, 1, 10, 100, 1000]


def precompute_hc_weights(baseline_dir, roi, K):
    """Compute per-HC weight matrices using all 8 colors x 6 runs.

    Returns:
        w_hc_dict: {subject_id: W (K, V_s)}
        Note: V_s varies by subject, so we compute per-subject.
    """
    w_hc_dict = {}
    centers = np.linspace(0, 360, K, endpoint=False)
    C_full = create_basis_adaptive(HUE_ANGLES, centers)
    C_tiled = np.tile(C_full, (N_RUNS, 1))  # (48, K)

    for subj in HC_SUBJECTS:
        try:
            amp = load_amplitudes(baseline_dir, subj, roi)
        except FileNotFoundError:
            continue
        V_s = amp.shape[2]
        X_pooled = amp.reshape(-1, V_s)  # (48, V_s)
        alpha, _ = gcv_select_alpha(C_tiled, X_pooled, alpha_grid=ALPHA_GRID)
        W = fit_W_ridge(C_tiled, X_pooled, alpha)
        w_hc_dict[subj] = W

    return w_hc_dict


def compute_hc_prior(w_hc_dict, exclude_subj=None, target_V_s=None):
    """Compute mean HC weight matrix, optionally excluding one subject.

    Since V_s varies across HC subjects but we need a (K, V_s_target)
    prior, we can only average subjects with the SAME V_s. For simplicity,
    we compute the prior in shared-space coordinates:
    W_bar = mean of W_hc for subjects with matching V_s.

    In practice, since the target subject's V_s determines prediction,
    the prior is only meaningful for the target's own voxel space.
    We handle this by computing a scalar prior strength and direction
    per channel (mean across voxels).

    ALTERNATIVE (used here): Since prior-centred ridge requires W_bar
    with same shape as target W, we compute W_bar only from subjects
    whose V_s matches the target. If none match, fall back to channel-
    mean direction.

    Actually, the correct approach: the prior W_bar should be fitted
    per-target-subject in the target's voxel space. Since each subject
    has different voxels, we cannot simply average W matrices across
    subjects. Instead, we average the LOCO performance metric.

    REVISED APPROACH: We compute W_bar for the TARGET subject's V_s
    by re-fitting HC subjects' W in a shared representational space.
    But that requires SRM which adds complexity.

    SIMPLEST CORRECT APPROACH: Since all subjects share the same
    stimulus space (8 colors x K channels), the prior operates on
    the CHANNEL x VOXEL weights. But each subject has different voxels.
    The hierarchical prior must be per-subject: we use the target
    subject's OWN data to compute both W and regularize toward W_bar.

    For CVD subjects: W_bar = mean of HC Ws projected into CVD voxel space.
    But HC and CVD have different V_s.

    PRACTICAL SOLUTION: Compute W_bar as a function of channel profiles
    only (ignoring voxel identity). This means W_bar[k, :] = mean
    weight magnitude for channel k. But this loses spatial structure.

    FINAL APPROACH: The hierarchical prior here operates per-subject.
    W_bar_HC is computed from the target subject's own HC-like baseline
    using LOO. For HC subjects, W_bar = mean of 6 other HCs' own Ws
    (each in their own voxel space) — but this doesn't work cross-subject.

    ACTUAL IMPLEMENTATION: We use the SAME subject's own data to compute
    W_bar from a subset (e.g., inner CV), then regularize toward it.
    This is "self-regularization" — but doesn't leverage HC group info.

    === CORRECT IMPLEMENTATION ===
    The HC prior should be computed in the TARGET subject's voxel space.
    For HC subjects: use LOO W_bar computed from 6 HCs — but each HC has
    different voxels, so we fit each HC's weight matrix using the TARGET
    subject's amplitudes space. This is not possible directly.

    The PLAN specifies W_bar = mean(W_hc_list). This only works if all
    subjects share the same voxel space (e.g., after SRM/Procrustes).
    Since our amplitudes_procrustes.npy IS Procrustes-aligned, the voxel
    counts may still differ.

    SIMPLIFICATION: If V_s differs, truncate/pad to common size.
    But this is lossy. Instead, let's use a CHANNEL-LEVEL prior:
    W_bar has shape (K,) — mean weight per channel across HC subjects
    and their voxels. Then broadcast to (K, V_s).

    Let's implement the PLAN as specified, noting that it works when
    V_s is the same (or we take channel-level prior).
    """
    subjects = [s for s in w_hc_dict if s != exclude_subj]
    if not subjects:
        return None

    # Channel-level prior: mean absolute weight per channel
    K = next(iter(w_hc_dict.values())).shape[0]
    channel_means = np.zeros(K)
    channel_counts = 0
    for s in subjects:
        W = w_hc_dict[s]
        channel_means += np.mean(W, axis=1)  # mean across voxels per channel
        channel_counts += 1
    channel_means /= channel_counts
    return channel_means  # (K,)


def make_W_bar(channel_prior, V_s):
    """Broadcast channel-level prior to (K, V_s).

    Each voxel gets the same channel-level prior weight.
    """
    return np.tile(channel_prior[:, np.newaxis], (1, V_s))


def standard_ridge_loco(amp, K):
    """Standard pooled-run LOCO (no prior). Baseline.

    Returns:
        mean_corr, per_color (8,)
    """
    centers = np.linspace(0, 360, K, endpoint=False)
    C_full = create_basis_adaptive(HUE_ANGLES, centers)
    n_colors = len(HUE_ANGLES)
    V_s = amp.shape[2]
    fold_corrs = np.zeros(n_colors)

    for test_color in range(n_colors):
        train_idx = [c for c in range(n_colors) if c != test_color]
        C_train = C_full[train_idx]
        X_train = amp[:, train_idx, :].reshape(-1, V_s)
        C_tiled = np.tile(C_train, (N_RUNS, 1))

        alpha, _ = gcv_select_alpha(C_tiled, X_train, alpha_grid=ALPHA_GRID)
        W = fit_W_ridge(C_tiled, X_train, alpha)

        C_test = C_full[test_color:test_color + 1]
        Y_hat = predict_patterns(W, C_test)
        Y_real = amp[:, test_color, :].mean(axis=0, keepdims=True)

        r = voxel_pattern_correlation(Y_hat, Y_real)
        fold_corrs[test_color] = r[0]

    return float(np.mean(fold_corrs)), fold_corrs


def hierarchical_nested_loco(amp, K, W_bar, lambda_grid):
    """Nested LOCO with prior-centred ridge.

    Outer: 8-fold (pooled runs)
    Inner: 7-fold on run-averaged data to select lambda

    Returns:
        mean_corr, per_color (8,), per_fold_lambda, decoded_hues (8,),
        mae_degrees, rdm_ut (28,)
    """
    centers = np.linspace(0, 360, K, endpoint=False)
    C_full = create_basis_adaptive(HUE_ANGLES, centers)
    basis_full = create_basis_adaptive(np.arange(360), centers)
    n_colors = len(HUE_ANGLES)
    V_s = amp.shape[2]
    amp_mean = amp.mean(axis=0)  # (8, V_s)

    fold_corrs = np.zeros(n_colors)
    per_fold_lambda = []
    decoded_hues = np.zeros(n_colors)
    predicted_patterns = np.zeros((n_colors, V_s))

    for outer_test in range(n_colors):
        train_idx = [c for c in range(n_colors) if c != outer_test]

        # Inner 7-fold LOCO to select lambda
        amp_mean_7 = amp_mean[train_idx]  # (7, V_s)
        C_train_7 = C_full[train_idx]

        best_lam = lambda_grid[0]
        best_inner = -np.inf

        for lam in lambda_grid:
            inner_corrs = np.zeros(7)
            for inner_test in range(7):
                inner_train = [i for i in range(7) if i != inner_test]
                C_t = C_train_7[inner_train]
                X_t = amp_mean_7[inner_train]

                W = fit_W_prior_ridge(C_t, X_t, W_bar, lam)

                C_te = C_train_7[inner_test:inner_test + 1]
                Y_hat = predict_patterns(W, C_te)
                Y_real = amp_mean_7[inner_test:inner_test + 1]

                r = voxel_pattern_correlation(Y_hat, Y_real)
                inner_corrs[inner_test] = r[0]

            mean_inner = float(np.mean(inner_corrs))
            if mean_inner > best_inner:
                best_inner = mean_inner
                best_lam = lam

        per_fold_lambda.append(float(best_lam))

        # Outer evaluation: pooled runs + best lambda
        C_train = C_full[train_idx]
        X_train = amp[:, train_idx, :].reshape(-1, V_s)
        C_tiled = np.tile(C_train, (N_RUNS, 1))

        W = fit_W_prior_ridge(C_tiled, X_train, W_bar, best_lam)

        C_test = C_full[outer_test:outer_test + 1]
        Y_hat = predict_patterns(W, C_test)
        Y_real = amp[:, outer_test, :].mean(axis=0, keepdims=True)

        r = voxel_pattern_correlation(Y_hat, Y_real)
        fold_corrs[outer_test] = r[0]
        predicted_patterns[outer_test] = Y_hat[0]

        # Decode hue
        pred = decode_hue(W, basis_full, Y_real)
        decoded_hues[outer_test] = pred[0]

    # MAE
    mae = float(np.nanmean(circular_distance(HUE_ANGLES, decoded_hues)))

    # RDM
    rdm = compute_rdm(predicted_patterns, metric='correlation')
    rdm_ut = rdm_upper_tri(rdm)

    return (float(np.mean(fold_corrs)), fold_corrs, per_fold_lambda,
            decoded_hues, mae, rdm_ut)


def main():
    parser = argparse.ArgumentParser(
        description='B3: Hierarchical FE — HC prior + CVD deviation')
    parser.add_argument('--baseline_dir', type=str,
                        default=str(DEFAULT_BASELINE_DIR))
    parser.add_argument('--output_dir', type=str, required=True)
    parser.add_argument('--rois', nargs='+', default=ROIS, choices=ROIS)
    parser.add_argument('--subjects', nargs='+', default=ALL_SUBJECTS)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("B3: Hierarchical FE — HC Prior + CVD Deviation")
    print(f"Lambda grid: {LAMBDA_GRID}")
    print("=" * 70)

    for roi in args.rois:
        K = OPTIMAL_N_CHANNELS.get(roi, 6)
        print(f"\n--- ROI: {roi} | K={K} ---")

        # Precompute HC weight matrices
        print("  Precomputing HC weight matrices...")
        w_hc_dict = precompute_hc_weights(args.baseline_dir, roi, K)
        print(f"  HC subjects with data: {list(w_hc_dict.keys())}")

        for subj in args.subjects:
            if subj not in [s for s in args.subjects]:
                continue

            print(f"\n  sub-{subj} | {roi} | K={K}")

            try:
                amp = load_amplitudes(args.baseline_dir, subj, roi)
            except FileNotFoundError as e:
                print(f"    SKIP: {e}")
                continue

            V_s = amp.shape[2]
            group = get_subject_group(subj)
            print(f"    voxels: {V_s}, group: {group}")

            # Compute W_bar_HC (LOO for HC, all HC for CVD)
            exclude = subj if group == 'HC' else None
            channel_prior = compute_hc_prior(w_hc_dict, exclude_subj=exclude)

            if channel_prior is None:
                print("    SKIP: no HC prior available")
                continue

            W_bar = make_W_bar(channel_prior, V_s)

            # Standard ridge baseline
            std_mean, std_per_color = standard_ridge_loco(amp, K)
            print(f"    Standard ridge LOCO: {std_mean:.4f}")

            # Hierarchical nested LOCO
            (hier_mean, hier_per_color, fold_lam,
             dec_hues, mae, rdm_ut) = \
                hierarchical_nested_loco(amp, K, W_bar, LAMBDA_GRID)

            delta = hier_mean - std_mean
            mean_lam = float(np.mean(fold_lam))
            print(f"    Hierarchical LOCO: {hier_mean:.4f}  "
                  f"(delta={delta:+.4f})")
            print(f"    mean lambda: {mean_lam:.2f}")
            print(f"    MAE: {mae:.1f} deg")

            result = {
                'subject': subj,
                'roi': roi,
                'group': group,
                'n_channels': K,
                'n_voxels': V_s,
                'standard_ridge': {
                    'loco_mean': std_mean,
                    'loco_per_color': std_per_color.tolist(),
                },
                'hierarchical': {
                    'loco_mean': hier_mean,
                    'loco_per_color': hier_per_color.tolist(),
                    'per_fold_lambda': fold_lam,
                    'mean_lambda': mean_lam,
                    'decoded_hues': dec_hues.tolist(),
                    'mae_degrees': mae,
                    'loco_predicted_rdm_ut': rdm_ut.tolist(),
                },
                'delta_vs_standard': delta,
            }

            out_file = output_dir / f'sub-{subj}_{roi}_hierarchical.json'
            with open(out_file, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"    -> {out_file}")

    save_config(output_dir,
                script='fit_hierarchical_fe.py',
                baseline_dir=str(args.baseline_dir),
                lambda_grid=LAMBDA_GRID,
                optimal_k_map=dict(OPTIMAL_N_CHANNELS))

    print("\nDone.")


if __name__ == '__main__':
    main()
