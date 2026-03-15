#!/usr/bin/env python3
"""
subject_k_selection.py — B1: Subject-specific K selection.

For each subject x ROI, sweep K in [2,3,4,5,6,8,10,12] and report
optimal K via pooled-run 8-fold LOCO voxel_corr. Descriptive (not
predictive): no nested CV needed.

Additional metrics per K for 5-axis comparison:
  - decoded_hues, mae_degrees, loco_predicted_rdm_ut

Usage:
    python subject_k_selection.py \
        --baseline_dir /path/to/C010 \
        --output_dir results/subject_k \
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

K_SWEEP = [2, 3, 4, 5, 6, 8, 10, 12]


def run_loco_for_k(amp, K):
    """Pooled-run 8-fold LOCO for a given K.

    Returns:
        mean_corr, per_color (8,), decoded_hues (8,), mae_degrees, rdm_ut (28,)
    """
    centers = np.linspace(0, 360, K, endpoint=False)
    C_full = create_basis_adaptive(HUE_ANGLES, centers)
    basis_full = create_basis_adaptive(np.arange(360), centers)

    n_colors = len(HUE_ANGLES)
    V_s = amp.shape[2]
    fold_corrs = np.zeros(n_colors)
    decoded_hues = np.zeros(n_colors)
    predicted_patterns = np.zeros((n_colors, V_s))

    for test_color in range(n_colors):
        train_idx = [c for c in range(n_colors) if c != test_color]
        C_train = C_full[train_idx]

        # Pool all runs
        X_train = amp[:, train_idx, :].reshape(-1, V_s)
        C_train_tiled = np.tile(C_train, (N_RUNS, 1))

        alpha, _ = gcv_select_alpha(C_train_tiled, X_train,
                                     alpha_grid=ALPHA_GRID)
        W = fit_W_ridge(C_train_tiled, X_train, alpha)

        # Predict
        C_test = C_full[test_color:test_color + 1]
        Y_hat = predict_patterns(W, C_test)
        Y_real = amp[:, test_color, :].mean(axis=0, keepdims=True)

        r = voxel_pattern_correlation(Y_hat, Y_real)
        fold_corrs[test_color] = r[0]
        predicted_patterns[test_color] = Y_hat[0]

        # Decode hue
        pred = decode_hue(W, basis_full, Y_real)
        decoded_hues[test_color] = pred[0]

    # MAE
    mae = float(np.nanmean(circular_distance(HUE_ANGLES, decoded_hues)))

    # RDM from predicted patterns
    rdm = compute_rdm(predicted_patterns, metric='correlation')
    rdm_ut = rdm_upper_tri(rdm)

    return (float(np.mean(fold_corrs)), fold_corrs, decoded_hues,
            mae, rdm_ut)


def main():
    parser = argparse.ArgumentParser(
        description='B1: Subject-specific K selection via LOCO sweep')
    parser.add_argument('--baseline_dir', type=str,
                        default=str(DEFAULT_BASELINE_DIR))
    parser.add_argument('--output_dir', type=str, required=True)
    parser.add_argument('--rois', nargs='+', default=ROIS,
                        choices=ROIS)
    parser.add_argument('--subjects', nargs='+', default=ALL_SUBJECTS)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("B1: Subject-Specific K Selection")
    print("=" * 70)

    for subj in args.subjects:
        for roi in args.rois:
            print(f"\nsub-{subj} | {roi}")

            try:
                amp = load_amplitudes(args.baseline_dir, subj, roi)
            except FileNotFoundError as e:
                print(f"  SKIP: {e}")
                continue

            n_voxels = amp.shape[2]
            print(f"  voxels: {n_voxels}")

            group_k = OPTIMAL_N_CHANNELS.get(roi, 6)
            per_k = {}
            best_k = None
            best_loco = -np.inf

            for K in K_SWEEP:
                if K > n_voxels:
                    print(f"  K={K}: SKIP (K > n_voxels={n_voxels})")
                    continue

                mean_corr, per_color, dec_hues, mae, rdm_ut = \
                    run_loco_for_k(amp, K)

                per_k[str(K)] = {
                    'loco_mean': mean_corr,
                    'loco_per_color': per_color.tolist(),
                    'mae_degrees': mae,
                    'decoded_hues': dec_hues.tolist(),
                    'loco_predicted_rdm_ut': rdm_ut.tolist(),
                }

                tag = " *" if mean_corr > best_loco else ""
                print(f"  K={K:2d}: LOCO={mean_corr:.4f}  "
                      f"MAE={mae:.1f}{tag}")

                if mean_corr > best_loco:
                    best_loco = mean_corr
                    best_k = K

            # Group-K LOCO
            group_k_loco = per_k.get(str(group_k), {}).get('loco_mean', None)

            result = {
                'subject': subj,
                'roi': roi,
                'n_voxels': n_voxels,
                'k_values': [k for k in K_SWEEP if str(k) in per_k],
                'per_k': per_k,
                'optimal_k': best_k,
                'optimal_loco': best_loco,
                'group_k': group_k,
                'group_k_loco': group_k_loco,
            }

            out_file = output_dir / f'sub-{subj}_{roi}_subject_k.json'
            with open(out_file, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"  K*={best_k} (LOCO={best_loco:.4f}), "
                  f"group_K={group_k} (LOCO={group_k_loco:.4f})")
            print(f"  -> {out_file}")

    save_config(output_dir,
                script='subject_k_selection.py',
                baseline_dir=str(args.baseline_dir),
                k_sweep=K_SWEEP,
                group_k_map=dict(OPTIMAL_N_CHANNELS))

    print("\nDone.")


if __name__ == '__main__':
    main()
