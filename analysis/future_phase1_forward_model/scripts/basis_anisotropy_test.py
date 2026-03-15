#!/usr/bin/env python3
"""
basis_anisotropy_test.py — A2: Basis anisotropy test.

Does non-uniform channel spacing (cool-dense vs warm-dense) improve LOCO?
Tests whether concentrating channels in cool (S-axis) or warm hue regions
yields better encoding than uniform spacing.

Three modes per subject x ROI:
  - uniform: linspace(0, 360, K, endpoint=False)
  - cool_dense: ~60% channels in [180, 315] (cool/S-axis)
  - warm_dense: ~60% channels in [0, 135] (mirror)

Usage:
    python basis_anisotropy_test.py \
        --baseline_dir /path/to/C010 \
        --output_dir results/basis_anisotropy \
        [--rois V1 V2 V3 V4] [--subjects 01 02 ...]
"""

import argparse
import numpy as np
import json
from pathlib import Path
from math import ceil

from utils_forward_model import (
    load_amplitudes, fit_W_ridge, gcv_select_alpha,
    voxel_pattern_correlation, predict_patterns,
    HUE_ANGLES, N_RUNS, ALPHA_GRID,
    ALL_SUBJECTS, ROIS, save_config, DEFAULT_BASELINE_DIR,
)
from fit_adaptive_basis import create_basis_adaptive, OPTIMAL_N_CHANNELS


def create_anisotropic_centers(K, mode):
    """Create non-uniform channel centers.

    Args:
        K: number of channels
        mode: 'uniform', 'cool_dense', or 'warm_dense'

    Returns:
        centers: (K,) sorted center angles in degrees
    """
    if mode == 'uniform':
        return np.linspace(0, 360, K, endpoint=False)
    elif mode == 'cool_dense':
        # ~60% channels in [180, 315] (cool/S-axis)
        n_cool = max(1, ceil(0.6 * K))
        n_warm = K - n_cool
        cool = np.linspace(180, 315, n_cool, endpoint=True)
        if n_warm > 0:
            warm = np.linspace(0, 135, n_warm, endpoint=True)
            return np.sort(np.concatenate([warm, cool]))
        return np.sort(cool)
    elif mode == 'warm_dense':
        # Mirror: ~60% in [0, 135]
        n_warm = max(1, ceil(0.6 * K))
        n_cool = K - n_warm
        warm = np.linspace(0, 135, n_warm, endpoint=True)
        if n_cool > 0:
            cool = np.linspace(180, 315, n_cool, endpoint=True)
            return np.sort(np.concatenate([warm, cool]))
        return np.sort(warm)
    else:
        raise ValueError(f"Unknown mode: {mode}")


def pooled_run_loco(amp, centers):
    """Pooled-run 8-fold LOCO with given basis centers.

    Returns:
        mean_corr, per_color (8,)
    """
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


def main():
    parser = argparse.ArgumentParser(
        description='A2: Basis anisotropy test — uniform vs cool/warm-dense')
    parser.add_argument('--baseline_dir', type=str,
                        default=str(DEFAULT_BASELINE_DIR))
    parser.add_argument('--output_dir', type=str, required=True)
    parser.add_argument('--rois', nargs='+', default=ROIS, choices=ROIS)
    parser.add_argument('--subjects', nargs='+', default=ALL_SUBJECTS)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    MODES = ['uniform', 'cool_dense', 'warm_dense']

    print("=" * 70)
    print("A2: Basis Anisotropy Test")
    print("Modes: uniform, cool_dense (~60% in 180-315), "
          "warm_dense (~60% in 0-135)")
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

            mode_results = {}
            for mode in MODES:
                centers = create_anisotropic_centers(K, mode)
                mean_corr, per_color = pooled_run_loco(amp, centers)
                mode_results[mode] = {
                    'centers': centers.tolist(),
                    'loco_mean': mean_corr,
                    'loco_per_color': per_color.tolist(),
                }
                print(f"  {mode:12s}: LOCO={mean_corr:.4f}  "
                      f"centers={np.array2string(centers, precision=1)}")

            uni_loco = mode_results['uniform']['loco_mean']
            delta_cool = mode_results['cool_dense']['loco_mean'] - uni_loco
            delta_warm = mode_results['warm_dense']['loco_mean'] - uni_loco

            result = {
                'subject': subj,
                'roi': roi,
                'n_channels': K,
                'n_voxels': n_voxels,
            }
            result.update(mode_results)
            result['delta_cool_vs_uniform'] = delta_cool
            result['delta_warm_vs_uniform'] = delta_warm

            print(f"  delta cool: {delta_cool:+.4f}, "
                  f"delta warm: {delta_warm:+.4f}")

            out_file = output_dir / f'sub-{subj}_{roi}_basis_anisotropy.json'
            with open(out_file, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"  -> {out_file}")

    save_config(output_dir,
                script='basis_anisotropy_test.py',
                baseline_dir=str(args.baseline_dir),
                modes=MODES,
                optimal_k_map=dict(OPTIMAL_N_CHANNELS))

    print("\nDone.")


if __name__ == '__main__':
    main()
