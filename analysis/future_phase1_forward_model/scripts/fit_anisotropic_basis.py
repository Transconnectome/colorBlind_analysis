#!/usr/bin/env python3
"""
fit_anisotropic_basis.py — B2: Parametric channel shift (anisotropic basis).

Low-DOF parametric warping of FE channel centers via sin/cos modulation.
Nested 8-fold LOCO: outer holds out 1 color, inner 7-fold selects (a, b)
on run-averaged data, outer evaluates with pooled runs.

shift_centers(uniform, a, b):
    delta = a * sin(2*theta) + b * cos(2*theta)
    return (uniform + rad2deg(delta)) % 360

Usage:
    python fit_anisotropic_basis.py \
        --baseline_dir /path/to/C010 \
        --output_dir results/anisotropic_basis \
        [--rois V1 V2 V3 V4] [--subjects 01 02 ...]
"""

import argparse
import numpy as np
import json
from pathlib import Path

from utils_forward_model import (
    load_amplitudes, fit_W_ridge, gcv_select_alpha,
    voxel_pattern_correlation, predict_patterns,
    decode_hue, circular_distance,
    compute_rdm, rdm_upper_tri,
    HUE_ANGLES, N_RUNS, ALPHA_GRID,
    ALL_SUBJECTS, ROIS, save_config, DEFAULT_BASELINE_DIR,
)
from fit_adaptive_basis import create_basis_adaptive, OPTIMAL_N_CHANNELS


def shift_centers(centers_uniform, a, b):
    """Apply parametric sin/cos shift to uniform centers.

    Args:
        centers_uniform: (K,) uniform center angles in degrees
        a: sin(2*theta) coefficient (radians)
        b: cos(2*theta) coefficient (radians)

    Returns:
        shifted: (K,) shifted center angles in degrees
    """
    theta_rad = np.deg2rad(centers_uniform)
    delta = a * np.sin(2 * theta_rad) + b * np.cos(2 * theta_rad)
    return (centers_uniform + np.rad2deg(delta)) % 360


def inner_7fold_score(amp_mean_7, hue_7, centers_shifted):
    """7-fold inner LOCO on run-averaged data.

    Args:
        amp_mean_7: (7, V_s) run-averaged amplitudes for 7 training colors
        hue_7: (7,) hue angles for 7 training colors
        centers_shifted: (K,) shifted basis centers

    Returns:
        mean_corr: float
    """
    C_7 = create_basis_adaptive(hue_7, centers_shifted)
    n_inner = len(hue_7)
    inner_corrs = np.zeros(n_inner)

    for inner_test in range(n_inner):
        inner_train = [i for i in range(n_inner) if i != inner_test]
        C_train = C_7[inner_train]
        X_train = amp_mean_7[inner_train]

        if np.linalg.matrix_rank(C_train) < min(C_train.shape):
            inner_corrs[inner_test] = 0.0
            continue

        alpha, _ = gcv_select_alpha(C_train, X_train, alpha_grid=ALPHA_GRID)
        W = fit_W_ridge(C_train, X_train, alpha)

        C_test = C_7[inner_test:inner_test + 1]
        Y_hat = predict_patterns(W, C_test)
        Y_real = amp_mean_7[inner_test:inner_test + 1]

        r = voxel_pattern_correlation(Y_hat, Y_real)
        inner_corrs[inner_test] = r[0]

    return float(np.mean(inner_corrs))


def uniform_baseline_loco(amp, K):
    """Standard pooled-run LOCO with uniform FE-K (a=0, b=0).

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


def nested_anisotropic_loco(amp, K, ab_grid):
    """Full nested LOCO with parametric (a, b) channel shift.

    Outer: 8-fold LOCO (pooled runs)
    Inner: 7-fold LOCO on run-averaged data to select (a*, b*)

    Returns:
        mean_corr, per_color (8,), per_fold_ab, per_fold_inner_score,
        decoded_hues (8,), mae_degrees, rdm_ut (28,)
    """
    centers_uniform = np.linspace(0, 360, K, endpoint=False)
    n_colors = len(HUE_ANGLES)
    V_s = amp.shape[2]
    amp_mean = amp.mean(axis=0)  # (8, V_s)

    fold_corrs = np.zeros(n_colors)
    per_fold_ab = []
    per_fold_inner = []
    decoded_hues = np.zeros(n_colors)
    predicted_patterns = np.zeros((n_colors, V_s))

    # Basis for decoding (use final best centers per fold — approximate
    # with uniform for global decode since centers vary per fold)
    all_fold_centers = []

    for outer_test in range(n_colors):
        train_idx = [c for c in range(n_colors) if c != outer_test]
        hue_7 = HUE_ANGLES[train_idx]
        amp_mean_7 = amp_mean[train_idx]  # (7, V_s)

        # Grid search for best (a, b)
        best_inner = -np.inf
        best_ab = (0.0, 0.0)

        for a in ab_grid:
            for b in ab_grid:
                shifted = shift_centers(centers_uniform, a, b)
                score = inner_7fold_score(amp_mean_7, hue_7, shifted)
                if score > best_inner:
                    best_inner = score
                    best_ab = (float(a), float(b))

        per_fold_ab.append(list(best_ab))
        per_fold_inner.append(float(best_inner))

        # Outer evaluation: pooled runs with best (a*, b*)
        shifted_best = shift_centers(centers_uniform, *best_ab)
        all_fold_centers.append(shifted_best.tolist())

        C_full = create_basis_adaptive(HUE_ANGLES, shifted_best)
        C_train = C_full[train_idx]
        X_train = amp[:, train_idx, :].reshape(-1, V_s)
        C_tiled = np.tile(C_train, (N_RUNS, 1))

        alpha, _ = gcv_select_alpha(C_tiled, X_train, alpha_grid=ALPHA_GRID)
        W = fit_W_ridge(C_tiled, X_train, alpha)

        C_test = C_full[outer_test:outer_test + 1]
        Y_hat = predict_patterns(W, C_test)
        Y_real = amp[:, outer_test, :].mean(axis=0, keepdims=True)

        r = voxel_pattern_correlation(Y_hat, Y_real)
        fold_corrs[outer_test] = r[0]
        predicted_patterns[outer_test] = Y_hat[0]

        # Decode hue
        basis_full = create_basis_adaptive(np.arange(360), shifted_best)
        pred = decode_hue(W, basis_full, Y_real)
        decoded_hues[outer_test] = pred[0]

    # MAE
    mae = float(np.nanmean(circular_distance(HUE_ANGLES, decoded_hues)))

    # RDM
    rdm = compute_rdm(predicted_patterns, metric='correlation')
    rdm_ut = rdm_upper_tri(rdm)

    # Mean (a, b)
    ab_arr = np.array(per_fold_ab)
    mean_a = float(np.mean(ab_arr[:, 0]))
    mean_b = float(np.mean(ab_arr[:, 1]))

    return (float(np.mean(fold_corrs)), fold_corrs, per_fold_ab,
            per_fold_inner, mean_a, mean_b, decoded_hues, mae, rdm_ut)


def main():
    parser = argparse.ArgumentParser(
        description='B2: Anisotropic basis — parametric channel shift')
    parser.add_argument('--baseline_dir', type=str,
                        default=str(DEFAULT_BASELINE_DIR))
    parser.add_argument('--output_dir', type=str, required=True)
    parser.add_argument('--rois', nargs='+', default=ROIS, choices=ROIS)
    parser.add_argument('--subjects', nargs='+', default=ALL_SUBJECTS)
    parser.add_argument('--ab_n_grid', type=int, default=21,
                        help='Grid points per axis for (a,b) search')
    parser.add_argument('--ab_range', type=float, default=0.5,
                        help='Range for (a,b) grid: [-range, +range]')
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    ab_grid = np.linspace(-args.ab_range, args.ab_range, args.ab_n_grid)

    print("=" * 70)
    print("B2: Anisotropic Basis — Parametric Channel Shift")
    print(f"Grid: {args.ab_n_grid}x{args.ab_n_grid} = "
          f"{args.ab_n_grid**2} (a,b) points")
    print("=" * 70)

    for subj in args.subjects:
        for roi in args.rois:
            K = OPTIMAL_N_CHANNELS.get(roi, 6)
            print(f"\nsub-{subj} | {roi} | K={K}")

            try:
                amp = load_amplitudes(args.baseline_dir, subj, roi)
            except FileNotFoundError as e:
                print(f"  SKIP: {e}")
                continue

            n_voxels = amp.shape[2]
            print(f"  voxels: {n_voxels}")

            # Uniform baseline
            uni_mean, uni_per_color = uniform_baseline_loco(amp, K)
            print(f"  Uniform LOCO: {uni_mean:.4f}")

            # Anisotropic nested LOCO
            (aniso_mean, aniso_per_color, fold_ab, fold_inner,
             mean_a, mean_b, dec_hues, mae, rdm_ut) = \
                nested_anisotropic_loco(amp, K, ab_grid)

            delta = aniso_mean - uni_mean
            print(f"  Anisotropic LOCO: {aniso_mean:.4f}  "
                  f"(delta={delta:+.4f})")
            print(f"  mean (a,b) = ({mean_a:.3f}, {mean_b:.3f})")
            print(f"  MAE = {mae:.1f} deg")

            result = {
                'subject': subj,
                'roi': roi,
                'n_channels': K,
                'n_voxels': n_voxels,
                'ab_grid_n': args.ab_n_grid,
                'ab_range': args.ab_range,
                'uniform_baseline': {
                    'loco_mean': uni_mean,
                    'loco_per_color': uni_per_color.tolist(),
                },
                'anisotropic': {
                    'loco_mean': aniso_mean,
                    'loco_per_color': aniso_per_color.tolist(),
                    'per_fold_ab': fold_ab,
                    'per_fold_inner_score': fold_inner,
                    'mean_a': mean_a,
                    'mean_b': mean_b,
                    'decoded_hues': dec_hues.tolist(),
                    'mae_degrees': mae,
                    'loco_predicted_rdm_ut': rdm_ut.tolist(),
                },
                'delta_vs_uniform': delta,
            }

            out_file = output_dir / f'sub-{subj}_{roi}_anisotropic.json'
            with open(out_file, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"  -> {out_file}")

    save_config(output_dir,
                script='fit_anisotropic_basis.py',
                baseline_dir=str(args.baseline_dir),
                ab_grid_n=args.ab_n_grid,
                ab_range=args.ab_range,
                optimal_k_map=dict(OPTIMAL_N_CHANNELS))

    print("\nDone.")


if __name__ == '__main__':
    main()
