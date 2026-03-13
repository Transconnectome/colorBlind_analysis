#!/usr/bin/env python3
"""
validate_nested_adaptive_loco.py — Unbiased nested LOCO for adaptive basis.

Resolves circularity in fit_adaptive_basis.py: center optimization used the
full 8-color LOCO as objective, so the test color indirectly influenced
center selection. This script implements a nested (double) LOCO:

  Outer fold (8-fold): hold out 1 color for evaluation
    Inner optimization: optimize centers using only 7 remaining colors
      Inner LOCO (7-fold): hold out 1 of 7 for inner evaluation
        Train on 6 colors → predict 1
      → select best centers via mean inner LOCO
    Outer evaluation: best centers + 7-color pooled-run W → predict held-out

Three conditions compared:
  1. fixed_fe6: Standard FE-6 uniform basis
  2. fixed_optimal: Per-ROI optimal K, uniform centers
  3. nested_adaptive: Per-ROI optimal K, nested-optimized centers

Usage:
    python validate_nested_adaptive_loco.py --subject 01 --roi V1 \
        --output_dir results/nested_adaptive \
        [--baseline_dir /path/to/C010] \
        [--n_restarts 5] [--lambda_spacing 0.1]
"""

import argparse
import numpy as np
import json
from pathlib import Path
from scipy.optimize import minimize

from utils_forward_model import (
    load_amplitudes, fit_W_ridge, gcv_select_alpha,
    voxel_pattern_correlation, predict_patterns,
    create_basis_matrix,
    HUE_ANGLES, DEFAULT_BASELINE_DIR,
    ROIS, ALPHA_GRID, N_RUNS, save_config
)

from fit_adaptive_basis import (
    create_basis_adaptive, OPTIMAL_N_CHANNELS
)

N_CHANNELS_FE6 = 6


# ============================================================================
# Inner LOCO objective (7-color)
# ============================================================================

def inner_loco_objective(centers_free, fixed_center0, amp_mean_7,
                         hue_angles_7, lambda_spacing, n_channels):
    """Negative mean inner LOCO (7-fold) + spacing penalty.

    Args:
        centers_free: (K-1,) free center parameters
        fixed_center0: float, fixed first center
        amp_mean_7: (7, V_s) run-averaged amplitudes for 7 training colors
        hue_angles_7: (7,) hue angles for training colors
        lambda_spacing: spacing regularization weight
        n_channels: total number of channels

    Returns:
        loss: float (negative correlation + penalty)
    """
    centers = np.concatenate([[fixed_center0], centers_free])
    centers = np.sort(centers % 360)

    C_full_7 = create_basis_adaptive(hue_angles_7, centers)

    # Degenerate check
    if np.any(C_full_7.sum(axis=0) < 1e-10):
        return 1e6

    n_inner = len(hue_angles_7)
    fold_corrs = np.zeros(n_inner)

    for inner_test in range(n_inner):
        inner_train = [c for c in range(n_inner) if c != inner_test]
        C_train = C_full_7[inner_train]
        X_train = amp_mean_7[inner_train]

        if np.linalg.matrix_rank(C_train) < min(C_train.shape):
            fold_corrs[inner_test] = 0.0
            continue

        alpha, _ = gcv_select_alpha(C_train, X_train, alpha_grid=ALPHA_GRID)
        W = fit_W_ridge(C_train, X_train, alpha)

        C_test = C_full_7[inner_test:inner_test + 1]
        Y_hat = predict_patterns(W, C_test)
        Y_real = amp_mean_7[inner_test:inner_test + 1]

        r = voxel_pattern_correlation(Y_hat, Y_real)
        fold_corrs[inner_test] = r[0]

    mean_corr = np.mean(fold_corrs)

    # Spacing regularization
    c_sorted = np.sort(centers)
    spacings = np.diff(c_sorted)
    spacings = np.append(spacings, (c_sorted[0] + 360) - c_sorted[-1])
    ideal_spacing = 360.0 / n_channels
    spacing_penalty = lambda_spacing * np.mean(
        (spacings - ideal_spacing) ** 2
    ) / ideal_spacing ** 2

    return -mean_corr + spacing_penalty


def optimize_centers_inner(amp_mean_7, hue_angles_7, n_channels,
                           lambda_spacing=0.1, n_restarts=5, seed=42):
    """Multi-start optimization of basis centers using 7-color inner LOCO.

    Args:
        amp_mean_7: (7, V_s) run-averaged amplitudes for 7 colors
        hue_angles_7: (7,) hue angles for 7 colors
        n_channels: number of basis channels
        lambda_spacing: spacing regularization
        n_restarts: number of random restarts
        seed: random seed

    Returns:
        best_centers: (K,) optimized centers
        best_inner_score: float (inner 7-fold LOCO score, no penalty)
    """
    rng = np.random.RandomState(seed)
    fixed_center0 = 0.0

    best_loss = np.inf
    best_centers = None

    for restart in range(n_restarts):
        if restart == 0:
            init = np.linspace(0, 360, n_channels, endpoint=False)
        else:
            uniform = np.linspace(0, 360, n_channels, endpoint=False)
            perturbation = rng.uniform(-30, 30, n_channels)
            init = (uniform + perturbation) % 360
            init[0] = 0.0

        centers_free_init = np.sort(init[1:])
        bounds = [(1, 359)] * (n_channels - 1)

        try:
            result = minimize(
                inner_loco_objective,
                centers_free_init,
                args=(fixed_center0, amp_mean_7, hue_angles_7,
                      lambda_spacing, n_channels),
                method='L-BFGS-B',
                bounds=bounds,
                options={'maxiter': 200, 'ftol': 1e-8}
            )

            loss = result.fun
            centers = np.concatenate([[fixed_center0], result.x])
            centers = np.sort(centers % 360)

            if loss < best_loss:
                best_loss = loss
                best_centers = centers.copy()

        except Exception:
            pass

    # Evaluate inner score without penalty
    if best_centers is not None:
        C_7 = create_basis_adaptive(hue_angles_7, best_centers)
        n_inner = len(hue_angles_7)
        fold_corrs = np.zeros(n_inner)
        for i in range(n_inner):
            train = [c for c in range(n_inner) if c != i]
            C_t = C_7[train]
            X_t = amp_mean_7[train]
            if np.linalg.matrix_rank(C_t) < min(C_t.shape):
                fold_corrs[i] = 0.0
                continue
            a, _ = gcv_select_alpha(C_t, X_t, alpha_grid=ALPHA_GRID)
            W = fit_W_ridge(C_t, X_t, a)
            Y_hat = predict_patterns(W, C_7[i:i+1])
            r = voxel_pattern_correlation(Y_hat, amp_mean_7[i:i+1])
            fold_corrs[i] = r[0]
        best_inner_score = float(np.mean(fold_corrs))
    else:
        # Fallback to uniform
        best_centers = np.linspace(0, 360, n_channels, endpoint=False)
        best_inner_score = 0.0

    return best_centers, best_inner_score


# ============================================================================
# LOCO evaluation (fixed or adaptive basis)
# ============================================================================

def loco_pooled_run(amp, centers, n_channels):
    """Standard pooled-run LOCO with given basis centers.

    Uses pooled runs (N_RUNS × 7 train colors = 42 samples) for W fitting,
    matching the permutation baseline for fair comparison.

    Args:
        amp: (6, 8, V_s) full amplitudes
        centers: (K,) basis centers in degrees
        n_channels: number of channels

    Returns:
        mean_corr: float
        per_color: (8,) per-color voxel_corr
    """
    C_full = create_basis_adaptive(HUE_ANGLES, centers)
    n_colors = len(HUE_ANGLES)
    V_s = amp.shape[2]
    fold_corrs = np.zeros(n_colors)

    for test_color in range(n_colors):
        train_idx = [c for c in range(n_colors) if c != test_color]
        C_train = C_full[train_idx]

        # Pool all runs
        X_train = amp[:, train_idx, :].reshape(-1, V_s)
        C_train_tiled = np.tile(C_train, (N_RUNS, 1))

        alpha, _ = gcv_select_alpha(C_train_tiled, X_train,
                                     alpha_grid=ALPHA_GRID)
        W = fit_W_ridge(C_train_tiled, X_train, alpha)

        C_test = C_full[test_color:test_color + 1]
        Y_hat = predict_patterns(W, C_test)
        Y_real = amp[:, test_color, :].mean(axis=0, keepdims=True)

        r = voxel_pattern_correlation(Y_hat, Y_real)
        fold_corrs[test_color] = r[0]

    return float(np.mean(fold_corrs)), fold_corrs


def loco_fixed_baseline(amp, n_channels, basis_type='fe'):
    """Fixed uniform-center LOCO (FE-6 or FE-K).

    Args:
        amp: (6, 8, V_s)
        n_channels: number of channels
        basis_type: 'fe' (only fe supported here)

    Returns:
        mean_corr, per_color
    """
    centers = np.linspace(0, 360, n_channels, endpoint=False)
    return loco_pooled_run(amp, centers, n_channels)


# ============================================================================
# Nested adaptive LOCO
# ============================================================================

def nested_adaptive_loco(amp, n_channels, lambda_spacing=0.1,
                         n_restarts=5, seed=42):
    """Full nested LOCO: outer 8-fold × inner center optimization.

    Args:
        amp: (6, 8, V_s) full amplitudes
        n_channels: number of basis channels
        lambda_spacing: spacing regularization
        n_restarts: restarts per inner optimization
        seed: base random seed

    Returns:
        mean_corr: float
        per_color: (8,) per-color voxel_corr
        per_fold_centers: list of (K,) center arrays
        per_fold_inner_score: (8,) inner LOCO scores
    """
    n_colors = len(HUE_ANGLES)
    V_s = amp.shape[2]
    fold_corrs = np.zeros(n_colors)
    per_fold_centers = []
    per_fold_inner_score = np.zeros(n_colors)

    amp_mean = amp.mean(axis=0)  # (8, V_s) for inner optimization

    for outer_test in range(n_colors):
        outer_train = [c for c in range(n_colors) if c != outer_test]
        hue_angles_7 = HUE_ANGLES[outer_train]
        amp_mean_7 = amp_mean[outer_train]  # (7, V_s)

        # Inner optimization: find best centers using 7-color inner LOCO
        fold_seed = seed + outer_test * 100
        best_centers, inner_score = optimize_centers_inner(
            amp_mean_7, hue_angles_7, n_channels,
            lambda_spacing=lambda_spacing,
            n_restarts=n_restarts,
            seed=fold_seed
        )

        per_fold_centers.append(best_centers.tolist())
        per_fold_inner_score[outer_test] = inner_score

        # Outer evaluation: pooled runs with best centers
        C_full = create_basis_adaptive(HUE_ANGLES, best_centers)
        C_train = C_full[outer_train]
        X_train = amp[:, outer_train, :].reshape(-1, V_s)
        C_train_tiled = np.tile(C_train, (N_RUNS, 1))

        alpha, _ = gcv_select_alpha(C_train_tiled, X_train,
                                     alpha_grid=ALPHA_GRID)
        W = fit_W_ridge(C_train_tiled, X_train, alpha)

        C_test = C_full[outer_test:outer_test + 1]
        Y_hat = predict_patterns(W, C_test)
        Y_real = amp[:, outer_test, :].mean(axis=0, keepdims=True)

        r = voxel_pattern_correlation(Y_hat, Y_real)
        fold_corrs[outer_test] = r[0]

    return (float(np.mean(fold_corrs)), fold_corrs,
            per_fold_centers, per_fold_inner_score)


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Nested LOCO validation for adaptive basis (Section 4b)')
    parser.add_argument('--subject', required=True,
                        help='Subject ID (e.g., 01)')
    parser.add_argument('--roi', required=True, choices=ROIS,
                        help='ROI name')
    parser.add_argument('--output_dir', required=True,
                        help='Output directory')
    parser.add_argument('--baseline_dir', type=str,
                        default=str(DEFAULT_BASELINE_DIR),
                        help='Path to full_dataset_C010')
    parser.add_argument('--n_restarts', type=int, default=5,
                        help='Optimization restarts per inner fold')
    parser.add_argument('--lambda_spacing', type=float, default=0.1,
                        help='Uniform spacing regularization weight')
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()

    n_channels = OPTIMAL_N_CHANNELS.get(args.roi, 6)

    print(f"sub-{args.subject} | {args.roi} | K={n_channels} | "
          f"restarts={args.n_restarts} | lambda={args.lambda_spacing}")

    # Load data
    amp = load_amplitudes(args.baseline_dir, args.subject, args.roi)
    print(f"  amplitudes: {amp.shape}")

    # --- Condition 1: Fixed FE-6 ---
    print("  [1/3] Fixed FE-6...")
    fe6_mean, fe6_per_color = loco_fixed_baseline(amp, N_CHANNELS_FE6)
    print(f"    FE-6 LOCO: {fe6_mean:.4f}")

    # --- Condition 2: Fixed FE-K (per-ROI optimal K, uniform centers) ---
    print(f"  [2/3] Fixed FE-{n_channels}...")
    fek_mean, fek_per_color = loco_fixed_baseline(amp, n_channels)
    print(f"    FE-{n_channels} LOCO: {fek_mean:.4f}")

    # --- Condition 3: Nested adaptive ---
    print(f"  [3/3] Nested adaptive (K={n_channels})...")
    nest_mean, nest_per_color, fold_centers, fold_inner = \
        nested_adaptive_loco(
            amp, n_channels,
            lambda_spacing=args.lambda_spacing,
            n_restarts=args.n_restarts,
            seed=args.seed
        )
    print(f"    Nested adaptive LOCO: {nest_mean:.4f}")

    # Deltas
    delta_vs_fe6 = nest_mean - fe6_mean
    delta_vs_fek = nest_mean - fek_mean
    print(f"    Delta vs FE-6: {delta_vs_fe6:+.4f}")
    print(f"    Delta vs FE-{n_channels}: {delta_vs_fek:+.4f}")

    # Per-fold centers summary
    for fold_idx in range(len(HUE_ANGLES)):
        c = np.array(fold_centers[fold_idx])
        print(f"    Fold {fold_idx} (test={HUE_ANGLES[fold_idx]}°): "
              f"centers={np.array2string(c, precision=1)}, "
              f"inner={fold_inner[fold_idx]:.3f}, "
              f"outer={nest_per_color[fold_idx]:.3f}")

    # Save
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    result = {
        'subject': args.subject,
        'roi': args.roi,
        'n_channels': n_channels,
        'lambda_spacing': args.lambda_spacing,
        'n_restarts': args.n_restarts,
        'seed': args.seed,
        'n_voxels': int(amp.shape[2]),
        'fixed_fe6': {
            'n_channels': N_CHANNELS_FE6,
            'loco_mean': fe6_mean,
            'loco_per_color': fe6_per_color.tolist()
        },
        'fixed_optimal': {
            'n_channels': n_channels,
            'loco_mean': fek_mean,
            'loco_per_color': fek_per_color.tolist()
        },
        'nested_adaptive': {
            'n_channels': n_channels,
            'loco_mean': nest_mean,
            'loco_per_color': nest_per_color.tolist(),
            'per_fold_centers': fold_centers,
            'per_fold_inner_score': fold_inner.tolist()
        },
        'delta_vs_fe6': delta_vs_fe6,
        'delta_vs_fixed_optimal': delta_vs_fek
    }

    out_file = output_dir / f'sub-{args.subject}_{args.roi}_nested_adaptive.json'
    with open(out_file, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"  -> {out_file}")

    save_config(output_dir,
                script='validate_nested_adaptive_loco.py',
                baseline_dir=str(args.baseline_dir),
                n_channels_map={k: v for k, v in OPTIMAL_N_CHANNELS.items()},
                n_restarts=args.n_restarts,
                lambda_spacing=args.lambda_spacing)


if __name__ == '__main__':
    main()
