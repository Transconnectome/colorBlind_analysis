#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_group_level_glm.py
----------------------
Group-level (2nd level) analysis for Non-CVD subjects

Combines individual-level beta maps to:
1. Create common beta-map across subjects
2. Identify voxels with consistent color encoding
3. Evaluate group-level reconstruction performance

Non-CVD subjects: 01, 02, 05, 06, 07

Usage:
    python run_group_level_glm.py --roi V1 \
        --baseline-dirs derivatives/BH2009_deoblique/*/sub-{01,02,05,06,07}/*/V1

Output:
    derivatives/group_level/non_cvd/ROI/
    ├── group_beta_map.npy          # (n_colors, n_voxels)
    ├── group_amplitudes_z.npy      # (n_subjects, n_runs, n_colors, n_voxels)
    ├── consistency_map.npy         # Voxel consistency scores
    ├── selected_voxels.npy         # Common voxels indices
    └── group_results.csv
"""

import sys
import os
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import stats

# Import utils
try:
    from utils_color_decoding import (
        evaluate_reconstruction,
        compute_voxel_snr,
        visualize_circular_color_space
    )
except ImportError:
    print("ERROR: Cannot import utils_color_decoding.py")
    sys.exit(1)


def parse_args():
    parser = argparse.ArgumentParser(description='Group-level GLM analysis')
    parser.add_argument('--roi', type=str, required=True,
                        help='ROI name (V1, V2, V3, hV4)')
    parser.add_argument('--subjects', type=str, nargs='+',
                        default=['01', '02', '05', '06', '07'],
                        help='Non-CVD subject IDs')
    parser.add_argument('--baseline-pattern', type=str, required=True,
                        help='Pattern to find baseline directories (use {subject} placeholder)')
    parser.add_argument('--output-dir', type=str, default=None,
                        help='Output directory')
    parser.add_argument('--consistency-threshold', type=float, default=0.7,
                        help='Consistency threshold for voxel selection (0-1)')
    return parser.parse_args()


def load_subject_data(subject_id, baseline_pattern):
    """Load amplitudes_z.npy for a subject"""
    pattern = baseline_pattern.replace('{subject}', subject_id)
    search_path = Path(pattern).parent

    # Find matching directory
    amp_file = None
    for path in search_path.glob('**/amplitudes_z.npy'):
        if subject_id in str(path):
            amp_file = path
            break

    if amp_file is None or not amp_file.exists():
        raise FileNotFoundError(f"Cannot find amplitudes_z.npy for subject {subject_id}")

    amplitudes_z = np.load(amp_file)
    print(f"  sub-{subject_id}: {amplitudes_z.shape}")

    return amplitudes_z


def compute_consistency(amplitudes_group):
    """
    Compute voxel consistency across subjects

    Consistency = correlation of color preference across subjects

    Returns:
        consistency_scores: (n_voxels,) consistency score per voxel
    """
    n_subjects, n_runs, n_colors, n_voxels = amplitudes_group.shape

    # Average across runs for each subject
    amplitudes_avg = amplitudes_group.mean(axis=1)  # (n_subjects, n_colors, n_voxels)

    consistency_scores = np.zeros(n_voxels)

    for voxel_idx in range(n_voxels):
        # Color response pattern for this voxel across subjects
        voxel_patterns = amplitudes_avg[:, :, voxel_idx]  # (n_subjects, n_colors)

        # Compute pairwise correlations
        correlations = []
        for i in range(n_subjects):
            for j in range(i+1, n_subjects):
                corr, _ = stats.pearsonr(voxel_patterns[i], voxel_patterns[j])
                if not np.isnan(corr):
                    correlations.append(corr)

        # Mean correlation = consistency
        if len(correlations) > 0:
            consistency_scores[voxel_idx] = np.mean(correlations)
        else:
            consistency_scores[voxel_idx] = 0.0

    return consistency_scores


def select_consistent_voxels(consistency_scores, threshold):
    """Select voxels with consistency above threshold"""
    selected_mask = consistency_scores >= threshold
    selected_indices = np.where(selected_mask)[0]

    print(f"\n  Consistency threshold: {threshold:.2f}")
    print(f"  Selected voxels: {len(selected_indices)} / {len(consistency_scores)}")
    print(f"  Consistency range: [{consistency_scores.min():.3f}, {consistency_scores.max():.3f}]")
    print(f"  Mean consistency (selected): {consistency_scores[selected_indices].mean():.3f}")

    return selected_indices, selected_mask


def create_group_beta_map(amplitudes_group):
    """
    Create group-level beta map (average across subjects and runs)

    Returns:
        group_beta: (n_colors, n_voxels)
    """
    # Average across subjects and runs
    group_beta = amplitudes_group.mean(axis=(0, 1))  # (n_colors, n_voxels)

    return group_beta


def evaluate_group_level(amplitudes_group, selected_indices=None):
    """Evaluate group-level reconstruction"""
    n_subjects, n_runs, n_colors, n_voxels = amplitudes_group.shape

    if selected_indices is not None:
        amplitudes_group = amplitudes_group[:, :, :, selected_indices]
        print(f"  Using {len(selected_indices)} selected voxels")

    # Evaluate each subject
    subject_results = []

    for subj_idx in range(n_subjects):
        amplitudes_subj = amplitudes_group[subj_idx]  # (n_runs, n_colors, n_voxels)

        # Reconstruction
        recon_errors, _, _ = evaluate_reconstruction(amplitudes_subj)
        mean_recon_error = np.mean(recon_errors)

        # SNR
        snr_values = compute_voxel_snr(amplitudes_subj)
        mean_snr = np.mean(snr_values)

        subject_results.append({
            'reconstruction_error': mean_recon_error,
            'mean_snr': mean_snr
        })

    # Average across subjects
    mean_reconstruction_error = np.mean([r['reconstruction_error'] for r in subject_results])
    mean_snr = np.mean([r['mean_snr'] for r in subject_results])

    print(f"\n  Group-level Performance:")
    print(f"    Reconstruction: {mean_reconstruction_error:.1f}°")
    print(f"    Mean SNR: {mean_snr:.2f}")

    return {
        'reconstruction_error': mean_reconstruction_error,
        'mean_snr': mean_snr,
        'subject_results': subject_results
    }


def main():
    args = parse_args()

    print("=" * 80)
    print("Group-level GLM Analysis (Non-CVD Subjects)")
    print("=" * 80)
    print(f"ROI: {args.roi}")
    print(f"Subjects: {', '.join(args.subjects)}")
    print()

    # Output directory
    if args.output_dir is None:
        output_dir = Path(f"derivatives/group_level/non_cvd/{args.roi}")
    else:
        output_dir = Path(args.output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {output_dir}")
    print()

    # ========================================================================
    # Load data from all subjects
    # ========================================================================
    print("Loading data from subjects...")

    amplitudes_list = []

    for subject_id in args.subjects:
        try:
            amplitudes_z = load_subject_data(subject_id, args.baseline_pattern)
            amplitudes_list.append(amplitudes_z)
        except FileNotFoundError as e:
            print(f"  ⚠️  Warning: {e}")
            continue

    if len(amplitudes_list) == 0:
        print("❌ ERROR: No subject data loaded")
        sys.exit(1)

    # Stack into group array
    amplitudes_group = np.array(amplitudes_list)  # (n_subjects, n_runs, n_colors, n_voxels)
    n_subjects, n_runs, n_colors, n_voxels = amplitudes_group.shape

    print(f"\n✅ Loaded {n_subjects} subjects")
    print(f"   Shape: (subjects={n_subjects}, runs={n_runs}, colors={n_colors}, voxels={n_voxels})")
    print()

    # ========================================================================
    # Compute consistency and select voxels
    # ========================================================================
    print("Computing voxel consistency across subjects...")

    consistency_scores = compute_consistency(amplitudes_group)

    # Select consistent voxels
    selected_indices, selected_mask = select_consistent_voxels(
        consistency_scores, args.consistency_threshold
    )

    # ========================================================================
    # Create group beta map
    # ========================================================================
    print("\nCreating group-level beta map...")

    group_beta = create_group_beta_map(amplitudes_group)
    print(f"  Group beta map shape: {group_beta.shape}")

    # ========================================================================
    # Evaluate group-level performance
    # ========================================================================
    print("\n" + "=" * 80)
    print("Evaluating Group-level Performance")
    print("=" * 80)

    # Baseline (all voxels)
    print("\n[Baseline] All voxels:")
    baseline_results = evaluate_group_level(amplitudes_group, selected_indices=None)

    # With voxel selection
    print(f"\n[Selected] Consistent voxels (threshold={args.consistency_threshold}):")
    selected_results = evaluate_group_level(amplitudes_group, selected_indices=selected_indices)

    # ========================================================================
    # Save results
    # ========================================================================
    print("\nSaving results...")

    # Save arrays
    np.save(output_dir / 'group_beta_map.npy', group_beta)
    np.save(output_dir / 'group_amplitudes_z.npy', amplitudes_group)
    np.save(output_dir / 'consistency_map.npy', consistency_scores)
    np.save(output_dir / 'selected_voxels.npy', selected_indices)

    # Save summary
    summary_df = pd.DataFrame({
        'Condition': ['Baseline (all voxels)', f'Selected (consistency >= {args.consistency_threshold})'],
        'N_Voxels': [n_voxels, len(selected_indices)],
        'Reconstruction_Error': [
            baseline_results['reconstruction_error'],
            selected_results['reconstruction_error']
        ],
        'Mean_SNR': [
            baseline_results['mean_snr'],
            selected_results['mean_snr']
        ]
    })

    print("\n", summary_df.to_string(index=False))
    summary_df.to_csv(output_dir / 'group_results.csv', index=False)

    # Visualization: consistency distribution
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    # Histogram
    axes[0].hist(consistency_scores, bins=50, alpha=0.7, edgecolor='black')
    axes[0].axvline(args.consistency_threshold, color='r', linestyle='--',
                    label=f'Threshold = {args.consistency_threshold}')
    axes[0].set_xlabel('Consistency Score')
    axes[0].set_ylabel('Number of Voxels')
    axes[0].set_title('Voxel Consistency Distribution')
    axes[0].legend()

    # Selected vs rejected
    axes[1].hist(consistency_scores[~selected_mask], bins=30, alpha=0.5,
                 label='Rejected', color='gray')
    axes[1].hist(consistency_scores[selected_mask], bins=30, alpha=0.7,
                 label='Selected', color='blue')
    axes[1].set_xlabel('Consistency Score')
    axes[1].set_ylabel('Number of Voxels')
    axes[1].set_title('Selected vs. Rejected Voxels')
    axes[1].legend()

    plt.tight_layout()
    plt.savefig(output_dir / 'consistency_distribution.png', dpi=150, bbox_inches='tight')
    plt.close()

    print("\n" + "=" * 80)
    print("Group-level Analysis Complete!")
    print("=" * 80)
    print(f"Results saved to: {output_dir}")
    print(f"\nKey files:")
    print(f"  - group_beta_map.npy: {group_beta.shape}")
    print(f"  - selected_voxels.npy: {len(selected_indices)} voxels")
    print(f"  - group_results.csv: performance summary")


if __name__ == '__main__':
    main()
