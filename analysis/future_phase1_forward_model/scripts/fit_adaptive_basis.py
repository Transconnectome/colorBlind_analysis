#!/usr/bin/env python3
"""
fit_adaptive_basis.py — Optimize FE basis centers per subject x ROI.

Maximizes LOCO voxel_corr by adjusting the angular centers of the
half-wave rectified cosine basis functions (Section 9k-1 of PLAN.md).

Key design:
  - Fix center[0]=0 for rotation invariance
  - Regularize toward uniform spacing (lambda_spacing)
  - Multi-start optimization (L-BFGS-B)
  - Uses per-ROI optimal n_channels from Phase 1b

Usage:
    python fit_adaptive_basis.py --subject 01 --roi V1 \
        --output_dir results/adaptive_basis \
        [--baseline_dir /path/to/C010] \
        [--n_channels 6] [--n_restarts 10] [--lambda_spacing 0.1]
"""

import argparse
import numpy as np
import json
from pathlib import Path
from scipy.optimize import minimize

from utils_forward_model import (
    load_amplitudes, fit_W_ridge, gcv_select_alpha,
    voxel_pattern_correlation, predict_patterns,
    HUE_ANGLES, DEFAULT_BASELINE_DIR,
    ROIS, save_config, ALPHA_GRID
)

# Per-ROI optimal n_channels from Phase 1b (FE channel count ablation)
OPTIMAL_N_CHANNELS = {'V1': 2, 'V2': 3, 'V3': 8, 'V4': 3}


def create_basis_adaptive(hue_angles, centers):
    """Create FE design matrix with custom centers.

    Half-wave rectified cos^2, same as Brouwer & Heeger 2009,
    but with freely placed centers.

    Args:
        hue_angles: (n,) stimulus hue angles in degrees
        centers: (K,) basis function center angles in degrees

    Returns:
        C: (n, K) design matrix
    """
    hue_angles = np.asarray(hue_angles, dtype=float)
    centers = np.asarray(centers, dtype=float)
    K = len(centers)
    n = len(hue_angles)
    C = np.zeros((n, K))
    for i, c in enumerate(centers):
        dist = np.abs(hue_angles - c)
        dist = np.minimum(dist, 360 - dist)
        resp = np.cos(np.deg2rad(dist))
        C[:, i] = np.where(resp > 0, resp ** 2, 0.0)
    return C


def loco_score_with_centers(centers, amp_mean):
    """Compute mean LOCO voxel_corr for given basis centers.

    Args:
        centers: (K,) basis centers in degrees
        amp_mean: (8, V_s) run-averaged amplitudes

    Returns:
        mean_corr: float
        per_color: (8,) per-color correlations
    """
    C_full = create_basis_adaptive(HUE_ANGLES, centers)
    n_colors = len(HUE_ANGLES)
    fold_corrs = np.zeros(n_colors)

    for test_color in range(n_colors):
        train_idx = [c for c in range(n_colors) if c != test_color]
        C_train = C_full[train_idx]
        X_train = amp_mean[train_idx]

        if np.linalg.matrix_rank(C_train) < min(C_train.shape):
            fold_corrs[test_color] = 0.0
            continue

        alpha, _ = gcv_select_alpha(C_train, X_train, alpha_grid=ALPHA_GRID)
        W = fit_W_ridge(C_train, X_train, alpha)

        C_test = C_full[test_color:test_color + 1]
        Y_hat = predict_patterns(W, C_test)
        Y_real = amp_mean[test_color:test_color + 1]

        r = voxel_pattern_correlation(Y_hat, Y_real)
        fold_corrs[test_color] = r[0]

    return float(np.mean(fold_corrs)), fold_corrs


def loco_objective(centers_free, fixed_center0, amp_mean, lambda_spacing,
                   n_channels):
    """Negative mean LOCO voxel_corr + uniform spacing penalty.

    Args:
        centers_free: (K-1,) free center parameters [degrees]
        fixed_center0: float, fixed first center
        amp_mean: (8, V_s) run-averaged amplitudes
        lambda_spacing: regularization weight
        n_channels: total number of channels

    Returns:
        loss: float
    """
    centers = np.concatenate([[fixed_center0], centers_free])
    centers = np.sort(centers % 360)

    C_full = create_basis_adaptive(HUE_ANGLES, centers)

    # Degenerate check
    if np.any(C_full.sum(axis=0) < 1e-10):
        return 1e6

    n_colors = len(HUE_ANGLES)
    fold_corrs = np.zeros(n_colors)

    for test_color in range(n_colors):
        train_idx = [c for c in range(n_colors) if c != test_color]
        C_train = C_full[train_idx]
        X_train = amp_mean[train_idx]

        if np.linalg.matrix_rank(C_train) < min(C_train.shape):
            fold_corrs[test_color] = 0.0
            continue

        alpha, _ = gcv_select_alpha(C_train, X_train, alpha_grid=ALPHA_GRID)
        W = fit_W_ridge(C_train, X_train, alpha)

        C_test = C_full[test_color:test_color + 1]
        Y_hat = predict_patterns(W, C_test)
        Y_real = amp_mean[test_color:test_color + 1]

        r = voxel_pattern_correlation(Y_hat, Y_real)
        fold_corrs[test_color] = r[0]

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


def optimize_centers(amp_mean, n_channels, lambda_spacing=0.1, n_restarts=10,
                     seed=42):
    """Multi-start optimization of basis centers.

    Args:
        amp_mean: (8, V_s) run-averaged amplitudes
        n_channels: number of basis channels
        lambda_spacing: spacing regularization weight
        n_restarts: number of random restarts
        seed: random seed

    Returns:
        best_centers: (K,) optimized centers
        best_score: float (LOCO voxel_corr, without penalty)
        history: list of dicts
        per_color: (8,) per-color correlations at optimum
    """
    rng = np.random.RandomState(seed)
    fixed_center0 = 0.0

    best_loss = np.inf
    best_centers = None
    history = []

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
                loco_objective,
                centers_free_init,
                args=(fixed_center0, amp_mean, lambda_spacing, n_channels),
                method='L-BFGS-B',
                bounds=bounds,
                options={'maxiter': 200, 'ftol': 1e-8}
            )

            loss = result.fun
            centers = np.concatenate([[fixed_center0], result.x])
            centers = np.sort(centers % 360)

            history.append({
                'restart': restart,
                'loss': float(loss),
                'centers': centers.tolist(),
                'success': bool(result.success),
                'nit': int(result.nit)
            })

            if loss < best_loss:
                best_loss = loss
                best_centers = centers.copy()

        except Exception as e:
            history.append({'restart': restart, 'error': str(e)})

    # Evaluate best centers without penalty
    best_score, per_color = loco_score_with_centers(best_centers, amp_mean)
    return best_centers, best_score, history, per_color


def main():
    parser = argparse.ArgumentParser(
        description='Optimize FE basis centers per subject x ROI (Section 9k-1)')
    parser.add_argument('--subject', required=True,
                        help='Subject ID (e.g., 01)')
    parser.add_argument('--roi', required=True, choices=ROIS,
                        help='ROI name')
    parser.add_argument('--output_dir', required=True,
                        help='Output directory')
    parser.add_argument('--baseline_dir', type=str,
                        default=str(DEFAULT_BASELINE_DIR),
                        help='Path to full_dataset_C010')
    parser.add_argument('--n_channels', type=int, default=None,
                        help='Number of basis channels (default: per-ROI optimal)')
    parser.add_argument('--n_restarts', type=int, default=10,
                        help='Number of optimization restarts')
    parser.add_argument('--lambda_spacing', type=float, default=0.1,
                        help='Uniform spacing regularization weight')
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()

    n_channels = args.n_channels or OPTIMAL_N_CHANNELS.get(args.roi, 6)

    print(f"sub-{args.subject} | {args.roi} | K={n_channels} | "
          f"restarts={args.n_restarts} | lambda={args.lambda_spacing}")

    # Load data
    amp = load_amplitudes(args.baseline_dir, args.subject, args.roi)
    amp_mean = amp.mean(axis=0)  # (8, V_s)
    print(f"  amplitudes: {amp.shape} -> mean {amp_mean.shape}")

    # Fixed baseline (uniform FE-K)
    uniform_centers = np.linspace(0, 360, n_channels, endpoint=False)
    fixed_score, fixed_per_color = loco_score_with_centers(
        uniform_centers, amp_mean)
    print(f"  Fixed  FE-{n_channels} LOCO: {fixed_score:.4f}")

    # Adaptive optimization
    opt_centers, opt_score, history, opt_per_color = optimize_centers(
        amp_mean, n_channels,
        lambda_spacing=args.lambda_spacing,
        n_restarts=args.n_restarts,
        seed=args.seed
    )

    # Spacing stats
    c_sorted = np.sort(opt_centers)
    spacings = np.diff(c_sorted)
    spacings = np.append(spacings, (c_sorted[0] + 360) - c_sorted[-1])

    delta = opt_score - fixed_score
    print(f"  Adapt  FE-{n_channels} LOCO: {opt_score:.4f}  "
          f"(delta={delta:+.4f})")
    print(f"    centers: {np.array2string(opt_centers, precision=1)}")
    print(f"    spacings: {np.array2string(spacings, precision=1)}")

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
        'n_voxels': int(amp_mean.shape[1]),
        'fixed': {
            'centers': uniform_centers.tolist(),
            'loco_mean': fixed_score,
            'loco_per_color': fixed_per_color.tolist()
        },
        'adaptive': {
            'centers': opt_centers.tolist(),
            'spacings': spacings.tolist(),
            'loco_mean': opt_score,
            'loco_per_color': opt_per_color.tolist(),
            'delta': delta
        },
        'optimization_history': history
    }

    out_file = output_dir / f'sub-{args.subject}_{args.roi}_adaptive.json'
    with open(out_file, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"  -> {out_file}")

    save_config(output_dir,
                script='fit_adaptive_basis.py',
                baseline_dir=str(args.baseline_dir),
                n_channels_map={k: v for k, v in OPTIMAL_N_CHANNELS.items()},
                n_restarts=args.n_restarts,
                lambda_spacing=args.lambda_spacing)


if __name__ == '__main__':
    main()
