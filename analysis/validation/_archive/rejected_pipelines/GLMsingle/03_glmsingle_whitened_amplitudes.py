#!/usr/bin/env python3
"""
Step 3: Compute Whitened Amplitudes

This script:
1. Loads GLMsingle single-trial betas
2. Applies whitening transformation
3. Computes per-color amplitudes (averaged trials)
4. Z-scores amplitudes per run
5. Saves in format compatible with existing pipeline

Usage:
    python 03_glmsingle_whitened_amplitudes.py --subject 01 --roi V1
    python 03_glmsingle_whitened_amplitudes.py --input-dir results/{timestamp}/sub-01_V1

Expected runtime: 2-5 minutes per subject-ROI
"""

import argparse
import json
import numpy as np
from pathlib import Path
from datetime import datetime
import sys

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent / 'utils'))

from whitening_from_residuals import apply_whitening


def parse_args():
    parser = argparse.ArgumentParser(
        description='Compute whitened amplitudes from GLMsingle betas'
    )
    parser.add_argument(
        '--subject',
        type=str,
        help='Subject ID (e.g., 01)'
    )
    parser.add_argument(
        '--roi',
        type=str,
        help='ROI name (e.g., V1)'
    )
    parser.add_argument(
        '--input-dir',
        type=Path,
        help='Input directory from Step 1 & 2 (overrides --subject/--roi)'
    )
    parser.add_argument(
        '--save-whitened-betas',
        action='store_true',
        help='Save whitened single-trial betas (large file)'
    )

    return parser.parse_args()


def find_latest_results(subject, roi, base_dir='./results'):
    """Find most recent GLMsingle results for subject-ROI."""
    base_path = Path(base_dir) / 'GLMsingle'

    if not base_path.exists():
        raise FileNotFoundError(f"Results directory not found: {base_path}")

    # Find all directories for this subject-ROI
    pattern = f"sub-{subject}_{roi}"
    matching_dirs = []

    for timestamp_dir in sorted(base_path.glob('*'), reverse=True):
        subject_roi_dir = timestamp_dir / pattern
        if subject_roi_dir.exists():
            matching_dirs.append(subject_roi_dir)

    if not matching_dirs:
        raise FileNotFoundError(
            f"No results found for sub-{subject} {roi} in {base_path}"
        )

    return matching_dirs[0]


def compute_whitened_amplitudes(
    betas_single_trial,
    whitening_matrix,
    trial_labels_list,
    n_colors=8
):
    """
    Apply whitening and compute per-color amplitudes.

    Args:
        betas_single_trial: (n_runs, n_trials, n_voxels) single-trial betas
        whitening_matrix: (n_voxels, n_voxels) W = Σ^(-1/2)
        trial_labels_list: List of trial labels (1-8) per run
        n_colors: Number of colors (default: 8)

    Returns:
        amplitudes_glmsingle: (n_runs, n_colors, n_voxels) - GLMsingle only
        amplitudes_whitened: (n_runs, n_colors, n_voxels) - GLMsingle + Whitening
        amplitudes_z_glmsingle: (n_runs, n_colors, n_voxels) - z-scored
        amplitudes_z_whitened: (n_runs, n_colors, n_voxels) - z-scored
    """
    n_runs = len(betas_single_trial)
    n_voxels = betas_single_trial[0].shape[1]

    # Initialize amplitude arrays
    amplitudes_glmsingle = np.zeros((n_runs, n_colors, n_voxels))
    amplitudes_whitened = np.zeros((n_runs, n_colors, n_voxels))

    for run_idx in range(n_runs):
        # Original betas (GLMsingle only)
        betas_run = betas_single_trial[run_idx]  # (n_trials, n_voxels)

        # Whitened betas
        betas_white = apply_whitening(betas_run, whitening_matrix, axis=-1)

        # Average by color
        labels_run = trial_labels_list[run_idx]
        for color_id in range(1, n_colors + 1):
            trials_this_color = (labels_run == color_id)
            n_trials_color = trials_this_color.sum()

            if n_trials_color > 0:
                # GLMsingle amplitudes
                amplitudes_glmsingle[run_idx, color_id - 1] = \
                    betas_run[trials_this_color].mean(axis=0)

                # Whitened amplitudes
                amplitudes_whitened[run_idx, color_id - 1] = \
                    betas_white[trials_this_color].mean(axis=0)

    # Z-score per run per voxel
    amplitudes_z_glmsingle = np.zeros_like(amplitudes_glmsingle)
    amplitudes_z_whitened = np.zeros_like(amplitudes_whitened)

    for run_idx in range(n_runs):
        for voxel_idx in range(n_voxels):
            # Z-score GLMsingle
            amps_glm = amplitudes_glmsingle[run_idx, :, voxel_idx]
            mean_glm = amps_glm.mean()
            std_glm = amps_glm.std()
            if std_glm > 0:
                amplitudes_z_glmsingle[run_idx, :, voxel_idx] = \
                    (amps_glm - mean_glm) / std_glm

            # Z-score whitened
            amps_white = amplitudes_whitened[run_idx, :, voxel_idx]
            mean_white = amps_white.mean()
            std_white = amps_white.std()
            if std_white > 0:
                amplitudes_z_whitened[run_idx, :, voxel_idx] = \
                    (amps_white - mean_white) / std_white

    return (amplitudes_glmsingle, amplitudes_whitened,
            amplitudes_z_glmsingle, amplitudes_z_whitened)


def main():
    args = parse_args()

    print("=" * 80)
    print("Whitened Amplitudes Computation - Step 3")
    print("=" * 80)

    # Determine input directory
    if args.input_dir is not None:
        input_dir = args.input_dir
    elif args.subject and args.roi:
        input_dir = find_latest_results(args.subject, args.roi)
    else:
        print("ERROR: Must specify either --input-dir or --subject and --roi")
        return 1

    if not input_dir.exists():
        print(f"ERROR: Input directory not found: {input_dir}")
        return 1

    print(f"Input: {input_dir}")
    print()

    # ===== Step 1: Load Betas =====
    print("=" * 80)
    print("Step 1: Loading GLMsingle Betas")
    print("=" * 80)

    betas_file = input_dir / 'betas_single_trial.npz'

    if not betas_file.exists():
        print(f"ERROR: Betas file not found: {betas_file}")
        return 1

    # Load betas (variable length per run)
    betas_npz = np.load(betas_file)
    betas = [betas_npz[f'run{i+1}'] for i in range(len(betas_npz.files))]
    print(f"✓ Loaded betas: {len(betas)} runs")
    for i, b in enumerate(betas):
        print(f"    Run {i+1}: {b.shape} (trials, voxels)")

    # ===== Step 2: Load Whitening Matrix =====
    print("\n" + "=" * 80)
    print("Step 2: Loading Whitening Matrix")
    print("=" * 80)

    white_file = input_dir / 'whitening_matrix.npy'

    if not white_file.exists():
        print(f"ERROR: Whitening matrix not found: {white_file}")
        print("Run Step 2 (02_estimate_noise_covariance.py) first")
        return 1

    W = np.load(white_file)
    print(f"✓ Loaded whitening matrix: {W.shape}")

    # Check compatibility (betas is list of arrays)
    n_voxels_betas = betas[0].shape[1]  # (trials, voxels)
    if W.shape[0] != n_voxels_betas:
        print(f"ERROR: Whitening matrix voxels ({W.shape[0]}) != betas voxels ({n_voxels_betas})")
        return 1

    # ===== Step 3: Load Trial Labels =====
    print("\n" + "=" * 80)
    print("Step 3: Loading Trial Labels")
    print("=" * 80)

    design_file = input_dir / 'design_matrices.npz'

    if not design_file.exists():
        print(f"ERROR: Design matrices not found: {design_file}")
        return 1

    design_data = np.load(design_file)
    n_runs = betas.shape[0]

    trial_labels_list = [design_data[f'labels_run{i+1}'] for i in range(n_runs)]
    print(f"✓ Loaded trial labels for {n_runs} runs")

    # Verify shapes match and filter out padding (label=0)
    trial_labels_filtered = []
    for run_idx, labels in enumerate(trial_labels_list):
        # Remove padding (label=0) from labels to match betas
        labels_filtered = labels[labels > 0]
        trial_labels_filtered.append(labels_filtered)

        n_trials_betas = betas[run_idx].shape[0]
        if len(labels_filtered) != n_trials_betas:
            print(f"WARNING: Run {run_idx + 1} label count mismatch: "
                  f"{len(labels_filtered)} labels vs {n_trials_betas} trials")

    trial_labels_list = trial_labels_filtered

    # ===== Step 4: Compute Amplitudes =====
    print("\n" + "=" * 80)
    print("Step 4: Computing Amplitudes")
    print("=" * 80)

    # Betas is already a list of variable-length arrays
    betas_per_run = betas

    print("Computing amplitudes...")
    (amps_glm, amps_white,
     amps_z_glm, amps_z_white) = compute_whitened_amplitudes(
        betas_per_run,
        W,
        trial_labels_list
    )

    print(f"✓ Amplitudes computed")
    print(f"  GLMsingle: {amps_glm.shape}")
    print(f"  Whitened: {amps_white.shape}")

    # ===== Step 5: Save Amplitudes =====
    print("\n" + "=" * 80)
    print("Step 5: Saving Amplitudes")
    print("=" * 80)

    # Save GLMsingle amplitudes (raw)
    amps_glm_file = input_dir / 'amplitudes_glmsingle.npy'
    np.save(amps_glm_file, amps_glm)
    print(f"✓ GLMsingle amplitudes: {amps_glm_file}")

    # Save GLMsingle amplitudes (z-scored) - compatible with existing pipeline
    amps_z_glm_file = input_dir / 'amplitudes_z_glmsingle.npy'
    np.save(amps_z_glm_file, amps_z_glm)
    print(f"✓ GLMsingle amplitudes (z): {amps_z_glm_file}")

    # Save whitened amplitudes (raw)
    amps_white_file = input_dir / 'amplitudes_whitened.npy'
    np.save(amps_white_file, amps_white)
    print(f"✓ Whitened amplitudes: {amps_white_file}")

    # Save whitened amplitudes (z-scored) - main output
    amps_z_white_file = input_dir / 'amplitudes_z_whitened.npy'
    np.save(amps_z_white_file, amps_z_white)
    print(f"✓ Whitened amplitudes (z): {amps_z_white_file}")

    # Optionally save whitened betas (large file)
    if args.save_whitened_betas:
        print("\nSaving whitened single-trial betas (large file)...")
        betas_white_all = []
        for betas_run in betas_per_run:
            betas_white_run = apply_whitening(betas_run, W, axis=-1)
            betas_white_all.append(betas_white_run)

        betas_white_file = input_dir / 'betas_whitened.npy'
        np.save(betas_white_file, np.array(betas_white_all))
        print(f"✓ Whitened betas: {betas_white_file}")
        print(f"  Size: {np.array(betas_white_all).nbytes / 1e6:.2f} MB")

    # ===== Step 6: Compute Statistics =====
    print("\n" + "=" * 80)
    print("Step 6: Computing Statistics")
    print("=" * 80)

    # Correlation between GLMsingle and whitened amplitudes
    corr = np.corrcoef(
        amps_z_glm.flatten(),
        amps_z_white.flatten()
    )[0, 1]

    print(f"Correlation (GLMsingle vs Whitened): {corr:.3f}")

    # Expected: 0.8-0.95 (high correlation but not identical)
    if corr < 0.7:
        print("WARNING: Low correlation - check whitening quality")
    elif corr > 0.95:
        print("WARNING: Very high correlation - whitening may have little effect")

    # SNR comparison (rough estimate)
    snr_glm = amps_z_glm.std(axis=1).mean()  # Across colors, averaged over runs
    snr_white = amps_z_white.std(axis=1).mean()

    print(f"\nAmplitude variability (across colors):")
    print(f"  GLMsingle: {snr_glm:.3f}")
    print(f"  Whitened: {snr_white:.3f}")
    print(f"  Ratio: {snr_white / snr_glm:.3f}")

    # ===== Step 7: Save Metadata =====
    print("\n" + "=" * 80)
    print("Step 7: Saving Metadata")
    print("=" * 80)

    metadata = {
        'timestamp': datetime.now().isoformat(),
        'input_dir': str(input_dir),

        # Statistics
        'correlation_glm_vs_whitened': float(corr),
        'amplitude_variability': {
            'glmsingle': float(snr_glm),
            'whitened': float(snr_white),
            'ratio': float(snr_white / snr_glm)
        },

        # Files
        'files': {
            'amplitudes_glmsingle': str(amps_glm_file),
            'amplitudes_z_glmsingle': str(amps_z_glm_file),
            'amplitudes_whitened': str(amps_white_file),
            'amplitudes_z_whitened': str(amps_z_white_file)
        }
    }

    meta_file = input_dir / 'amplitudes_metadata.json'
    with open(meta_file, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"✓ Metadata: {meta_file}")

    # ===== Done =====
    print("\n" + "=" * 80)
    print("Whitened Amplitudes Computation Completed!")
    print("=" * 80)
    print(f"Output directory: {input_dir}")
    print()
    print("Files created:")
    print(f"  - amplitudes_z_glmsingle.npy (GLMsingle only)")
    print(f"  - amplitudes_z_whitened.npy (GLMsingle + Whitening)")
    print()
    print("Next step:")
    print("  Run 04_evaluate_glmsingle_vs_fir.py to compare with FIR baseline")
    print()

    return 0


if __name__ == '__main__':
    exit(main())
