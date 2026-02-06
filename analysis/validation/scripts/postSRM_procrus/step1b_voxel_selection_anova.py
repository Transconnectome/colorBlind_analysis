#!/usr/bin/env python3
"""
Step 1b: ANOVA Voxel Selection (ALTERNATIVE)

Implements ANOVA-based top-k voxel selection as an alternative to PCA.
- Selects voxels with highest F-statistic (color discrimination)
- Averages runs into odd/even splits
- Note: PCA is recommended; use this for comparison

Usage:
    python step1b_voxel_selection_anova.py --subject 01 --roi V1 --k 500
"""

import argparse
import json
import numpy as np
from pathlib import Path
from sklearn.feature_selection import f_classif
import sys


def select_and_average_runs(amplitudes_z, k=500):
    """
    Select top-k voxels by ANOVA and average runs.

    Args:
        amplitudes_z: (6, 8, n_voxels) z-scored amplitudes
        k: Number of voxels to select

    Returns:
        odd_pattern: (8, k) averaged odd runs
        even_pattern: (8, k) averaged even runs
        selected_idx: (k,) indices of selected voxels
        f_values: (k,) F-statistics of selected voxels
    """
    from sklearn.feature_selection import f_classif

    n_runs, n_colors, n_voxels = amplitudes_z.shape

    print(f"  Input shape: {amplitudes_z.shape}")
    print(f"  n_voxels: {n_voxels}, target k: {k}")

    # Reshape for ANOVA: (n_samples, n_features) with labels
    X = amplitudes_z.reshape(n_runs * n_colors, n_voxels)  # (48, n_voxels)
    y = np.repeat(np.arange(n_colors), n_runs)  # Color labels (0-7, each repeated 6 times)

    # Compute F-statistics
    print(f"  Computing ANOVA F-statistics...")
    F, p_values = f_classif(X, y)

    # Handle NaN from constant voxels
    valid_mask = ~np.isnan(F)
    n_valid = valid_mask.sum()
    print(f"  Valid voxels (non-NaN F): {n_valid}/{n_voxels}")

    if n_valid < k:
        print(f"  WARNING: Only {n_valid} valid voxels, adjusting k from {k} to {n_valid}")
        k = n_valid

    F[~valid_mask] = -np.inf  # Set invalid to -inf so they're not selected

    # Select top k
    selected_idx = np.argsort(F)[-k:]
    f_values = F[selected_idx]

    print(f"  Selected {k} voxels")
    print(f"  F-value range: [{f_values.min():.2f}, {f_values.max():.2f}]")

    # Extract selected voxels
    amplitudes_selected = amplitudes_z[:, :, selected_idx]  # (6, 8, k)

    # Split and average runs
    odd_runs = amplitudes_selected[[0, 2, 4], :, :]  # runs 1,3,5
    even_runs = amplitudes_selected[[1, 3, 5], :, :]  # runs 2,4,6

    odd_pattern = odd_runs.mean(axis=0)  # (8, k)
    even_pattern = even_runs.mean(axis=0)  # (8, k)

    print(f"  Output patterns: odd={odd_pattern.shape}, even={even_pattern.shape}")

    return odd_pattern, even_pattern, selected_idx, f_values


def validate_anova_output(odd_pattern, even_pattern, f_values, k):
    """
    Validate ANOVA selection output.

    Returns:
        dict: Validation metrics
    """
    validation = {
        'shape_valid': odd_pattern.shape == even_pattern.shape,
        'n_voxels_selected': odd_pattern.shape[1],
        'f_values_positive': np.all(f_values > 0),
        'f_values_min': float(f_values.min()),
        'f_values_max': float(f_values.max()),
        'f_values_mean': float(f_values.mean()),
        'no_nan': not np.any(np.isnan(odd_pattern)) and not np.any(np.isnan(even_pattern)),
    }

    print("\n=== ANOVA Validation ===")
    print(f"  Shape valid: {validation['shape_valid']}")
    print(f"  Voxels selected: {validation['n_voxels_selected']}/{k} (requested)")
    print(f"  F-values positive: {validation['f_values_positive']}")
    print(f"  F-value range: [{validation['f_values_min']:.2f}, {validation['f_values_max']:.2f}]")
    print(f"  F-value mean: {validation['f_values_mean']:.2f}")
    print(f"  No NaN in patterns: {validation['no_nan']}")

    return validation


def main():
    parser = argparse.ArgumentParser(description='Step 1b: ANOVA Voxel Selection')
    parser.add_argument('--subject', type=str, required=True, help='Subject ID (e.g., 01)')
    parser.add_argument('--roi', type=str, required=True, help='ROI name (V1, V2, V3, hV4)')
    parser.add_argument('--k', type=int, default=500, help='Number of voxels to select (default: 500)')
    parser.add_argument('--baseline-dir', type=str,
                        default='/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase1_preprocess_decoding/results/baseline',
                        help='Path to baseline results directory')
    parser.add_argument('--output-dir', type=str,
                        default='/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/validation/scripts/postSRM_procrus/results/step1_anova',
                        help='Output directory')

    args = parser.parse_args()

    # Paths
    baseline_dir = Path(args.baseline_dir)
    output_dir = Path(args.output_dir)
    roi = args.roi
    subject_id = f"sub-{args.subject}"

    print(f"\n=== Step 1b: ANOVA Voxel Selection ===")
    print(f"Subject: {subject_id}, ROI: {roi}")
    print(f"k (voxels to select): {args.k}")

    # Load baseline amplitudes
    amplitudes_path = baseline_dir / subject_id / roi / "amplitudes_z.npy"

    if not amplitudes_path.exists():
        print(f"ERROR: Amplitudes file not found: {amplitudes_path}")
        sys.exit(1)

    print(f"\nLoading: {amplitudes_path}")
    amplitudes_z = np.load(amplitudes_path)  # (6, 8, n_voxels)

    # ANOVA selection
    odd_pattern, even_pattern, selected_idx, f_values = select_and_average_runs(
        amplitudes_z, k=args.k
    )

    # Validation
    validation = validate_anova_output(odd_pattern, even_pattern, f_values, args.k)

    # Save outputs
    output_roi_dir = output_dir / roi
    output_roi_dir.mkdir(parents=True, exist_ok=True)

    odd_pattern_path = output_roi_dir / f"{subject_id}_odd_patterns.npy"
    even_pattern_path = output_roi_dir / f"{subject_id}_even_patterns.npy"
    selected_idx_path = output_roi_dir / f"{subject_id}_selected_voxels_idx.npy"
    f_values_path = output_roi_dir / f"{subject_id}_f_values.npy"
    metadata_path = output_roi_dir / f"{subject_id}_metadata.json"

    np.save(odd_pattern_path, odd_pattern)
    np.save(even_pattern_path, even_pattern)
    np.save(selected_idx_path, selected_idx)
    np.save(f_values_path, f_values)

    # Save metadata
    metadata = {
        'subject': subject_id,
        'roi': roi,
        'k_requested': args.k,
        'k_actual': int(odd_pattern.shape[1]),
        'n_voxels_original': int(amplitudes_z.shape[2]),
        'odd_pattern_shape': list(odd_pattern.shape),
        'even_pattern_shape': list(even_pattern.shape),
        'validation': validation,
        'f_value_statistics': {
            'min': float(f_values.min()),
            'max': float(f_values.max()),
            'mean': float(f_values.mean()),
            'median': float(np.median(f_values)),
        },
    }

    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"\n=== Outputs Saved ===")
    print(f"  Odd patterns: {odd_pattern_path}")
    print(f"  Even patterns: {even_pattern_path}")
    print(f"  Selected voxel indices: {selected_idx_path}")
    print(f"  F-values: {f_values_path}")
    print(f"  Metadata: {metadata_path}")

    print(f"\n✓ Step 1b complete for {subject_id} {roi}")


if __name__ == '__main__':
    main()
