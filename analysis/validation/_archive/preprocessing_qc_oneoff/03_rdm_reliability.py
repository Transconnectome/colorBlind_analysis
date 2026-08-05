#!/usr/bin/env python3
"""
3.1.1 Across-run RDM Reliability
================================
동일 피험자 내에서 run 간 RDM 일관성 검증

RDM (Representational Dissimilarity Matrix):
- 8개 색깔 간의 신경 표현 거리 행렬 (8×8)
- 1 - correlation(pattern_A, pattern_B)
- 값이 작을수록 유사한 표현

Run 간 RDM 상관관계:
- r > 0.6 → Good (표현 일관적)
- r > 0.4 → Acceptable
- r < 0.4 → Poor (노이즈 많거나 불안정)

Input:
- Baseline amplitudes: {BASELINE_RESULTS}/sub-{ID}/{ROI}/amplitudes_z.npy
  - Shape: (n_runs=6, n_colors=8, n_voxels)

Output:
- {VALIDATION_OUT}/rdm_reliability/{TIMESTAMP}/within_subject_reliability.json
- Figures:
  - rdm_reliability_distribution.png (ROI별 violin plot)
  - rdm_matrices_per_run.png (예시 subject의 run별 RDM)
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import spearmanr
from itertools import combinations
from tqdm import tqdm

plt.rcParams['figure.dpi'] = 150
plt.style.use('default')


def compute_rdm(amplitudes):
    """
    Compute RDM (Representational Dissimilarity Matrix)

    Args:
        amplitudes: (n_colors, n_voxels) array

    Returns:
        rdm: (n_colors, n_colors) dissimilarity matrix
    """
    # Correlation matrix between colors
    corr_matrix = np.corrcoef(amplitudes)

    # Dissimilarity = 1 - correlation
    rdm = 1 - corr_matrix

    return rdm


def remove_constant_voxels(amplitudes_z):
    """
    Remove voxels that have zero variance across colors in any run.

    Args:
        amplitudes_z: (n_runs, n_colors, n_voxels)

    Returns:
        cleaned_amplitudes: (n_runs, n_colors, n_valid_voxels)
        n_removed: number of voxels removed
        valid_mask: boolean mask of valid voxels
    """
    n_runs, n_colors, n_voxels = amplitudes_z.shape

    # Track voxels that are constant in any run
    invalid_voxels = set()

    for run_idx in range(n_runs):
        pattern = amplitudes_z[run_idx]  # (n_colors, n_voxels)

        # Compute std across colors for each voxel
        voxel_stds = np.std(pattern, axis=0)  # (n_voxels,)

        # Mark voxels with zero variance
        constant_voxels = np.where(voxel_stds < 1e-10)[0]
        invalid_voxels.update(constant_voxels)

    # Create valid voxel mask
    valid_mask = np.ones(n_voxels, dtype=bool)
    if len(invalid_voxels) > 0:
        valid_mask[list(invalid_voxels)] = False

    n_valid = np.sum(valid_mask)
    n_removed = len(invalid_voxels)

    # Filter amplitudes
    cleaned_amplitudes = amplitudes_z[:, :, valid_mask]

    return cleaned_amplitudes, n_removed, valid_mask


def compute_rdm_reliability(amplitudes_z):
    """
    Compute run-pair RDM correlation (reliability)

    Args:
        amplitudes_z: (n_runs, n_colors, n_voxels)

    Returns:
        dict with:
            - pairwise_correlations: list of r values for all run pairs
            - mean_correlation: mean reliability
            - std_correlation: std of reliability
            - run_rdms: list of RDM matrices (for visualization)

    Raises:
        ValueError: If data has zero variance or contains NaN/Inf
    """
    n_runs, n_colors, n_voxels = amplitudes_z.shape

    # Check for NaN/Inf
    if np.isnan(amplitudes_z).any() or np.isinf(amplitudes_z).any():
        raise ValueError("Input data contains NaN or Inf values")

    # Remove constant voxels (zero std across colors in any run)
    cleaned_amplitudes, n_removed, valid_mask = remove_constant_voxels(amplitudes_z)
    n_valid_voxels = cleaned_amplitudes.shape[2]

    if n_removed > 0:
        print(f"    Removed {n_removed} constant voxels, {n_valid_voxels} remain")

    # Check if enough voxels remain
    if n_valid_voxels < 5:
        raise ValueError(f"Too few valid voxels ({n_valid_voxels}) after removing constant voxels. "
                       f"Removed {n_removed}/{n_voxels} constant voxels.")

    # Use cleaned data
    amplitudes_z = cleaned_amplitudes

    # Check for zero variance (overall)
    for run_idx in range(n_runs):
        var = np.var(amplitudes_z[run_idx])
        if var < 1e-10:
            raise ValueError(f"Run {run_idx} has zero or near-zero variance (var={var:.2e})")

    # Compute RDM for each run
    run_rdms = []
    for run_idx in range(n_runs):
        rdm = compute_rdm(amplitudes_z[run_idx])  # (n_colors, n_colors)

        # Check if RDM contains NaN/Inf
        if np.isnan(rdm).any() or np.isinf(rdm).any():
            raise ValueError(f"RDM for run {run_idx} contains NaN or Inf")

        run_rdms.append(rdm)

    # Compute pairwise correlations between runs
    pairwise_correlations = []

    for run_i, run_j in combinations(range(n_runs), 2):
        rdm_i = run_rdms[run_i]
        rdm_j = run_rdms[run_j]

        # Vectorize upper triangle (exclude diagonal)
        triu_indices = np.triu_indices(n_colors, k=1)
        vec_i = rdm_i[triu_indices]
        vec_j = rdm_j[triu_indices]

        # Spearman correlation
        r, p = spearmanr(vec_i, vec_j)
        pairwise_correlations.append(r)

    return {
        'pairwise_correlations': pairwise_correlations,
        'mean_correlation': float(np.mean(pairwise_correlations)),
        'std_correlation': float(np.std(pairwise_correlations)),
        'median_correlation': float(np.median(pairwise_correlations)),
        'min_correlation': float(np.min(pairwise_correlations)),
        'max_correlation': float(np.max(pairwise_correlations)),
        'run_rdms': run_rdms  # For visualization
    }


def main():
    parser = argparse.ArgumentParser(description='Compute across-run RDM reliability')
    parser.add_argument('--baseline-timestamp', type=str, required=True,
                       help='Timestamp of baseline results')
    parser.add_argument('--subjects', nargs='+',
                       default=[f'sub-{i:02d}' for i in range(1, 11)],
                       help='List of subjects')
    parser.add_argument('--rois', nargs='+',
                       default=['V1', 'V2', 'V3', 'hV4'],
                       help='List of ROIs')

    args = parser.parse_args()

    # Paths
    baseline_dir = Path('/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/method3_header_mi/results/baseline_decoding') / args.baseline_timestamp
    output_dir = Path('/scratch/connectome/haba6030/colorBlind/analysis/validation/results/rdm_reliability')

    # Create timestamp for this run
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    run_dir = output_dir / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"Output directory: {run_dir}")

    # Storage for results
    reliability_data = {
        'baseline_timestamp': args.baseline_timestamp,
        'subjects': args.subjects,
        'rois': args.rois,
        'results': {}
    }

    # Analyze each subject-roi
    print("\nComputing RDM reliability...")
    for subject in tqdm(args.subjects, desc='Subjects'):
        reliability_data['results'][subject] = {}

        for roi in args.rois:
            # Load amplitudes
            amp_path = baseline_dir / subject / roi / 'amplitudes_z.npy'

            if not amp_path.exists():
                print(f"Warning: No data for {subject} {roi}")
                continue

            amplitudes_z = np.load(amp_path)  # (n_runs, n_colors, n_voxels)

            try:
                # Compute reliability
                reliability = compute_rdm_reliability(amplitudes_z)

                # Store (exclude run_rdms from JSON)
                reliability_data['results'][subject][roi] = {
                    'pairwise_correlations': reliability['pairwise_correlations'],
                    'mean_correlation': reliability['mean_correlation'],
                    'std_correlation': reliability['std_correlation'],
                    'median_correlation': reliability['median_correlation'],
                    'min_correlation': reliability['min_correlation'],
                    'max_correlation': reliability['max_correlation']
                }

            except ValueError as e:
                print(f"Error: {subject} {roi} - {e}")
                print(f"  Skipping {subject} {roi} (likely data quality issue)")
                continue

    # Save detailed results
    json_path = run_dir / 'within_subject_reliability.json'
    with open(json_path, 'w') as f:
        json.dump(reliability_data, f, indent=2)
    print(f"\nSaved detailed results to {json_path}")

    # ========================================================================
    # Visualization
    # ========================================================================

    print("\nGenerating visualizations...")

    # Prepare data for plotting
    plot_data = []
    for subject in args.subjects:
        for roi in args.rois:
            if subject not in reliability_data['results']:
                continue
            if roi not in reliability_data['results'][subject]:
                continue

            data = reliability_data['results'][subject][roi]
            plot_data.append({
                'subject': subject,
                'roi': roi,
                'mean_correlation': data['mean_correlation']
            })

    import pandas as pd
    df = pd.DataFrame(plot_data)

    if len(df) == 0:
        print("No data available for visualization")
        return

    # Figure 1: RDM Reliability Distribution
    fig, ax = plt.subplots(figsize=(10, 6))

    roi_positions = {roi: i for i, roi in enumerate(args.rois)}
    colors_roi = plt.cm.Set1(np.linspace(0, 1, len(args.rois)))

    for roi_idx, roi in enumerate(args.rois):
        roi_data = df[df['roi'] == roi]['mean_correlation'].values
        if len(roi_data) > 0:
            parts = ax.violinplot([roi_data], positions=[roi_positions[roi]],
                                 widths=0.5, showmeans=True, showmedians=True)
            for pc in parts['bodies']:
                pc.set_facecolor(colors_roi[roi_idx])
                pc.set_alpha(0.6)

    ax.axhline(y=0.6, color='green', linestyle='--', label='Good (r>0.6)', linewidth=2)
    ax.axhline(y=0.4, color='orange', linestyle='--', label='Acceptable (r>0.4)', linewidth=2)
    ax.set_xticks(list(roi_positions.values()))
    ax.set_xticklabels(list(roi_positions.keys()))
    ax.set_xlabel('ROI', fontsize=12)
    ax.set_ylabel('Mean RDM Correlation (across run pairs)', fontsize=12)
    ax.set_title('Within-Subject RDM Reliability', fontsize=14)
    ax.set_ylim([0, 1])
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    fig_path1 = run_dir / 'rdm_reliability_distribution.png'
    plt.savefig(fig_path1)
    print(f"Saved reliability distribution to {fig_path1}")
    plt.close()

    # Figure 2: Example RDM Matrices (sub-01, V1)
    example_subject = 'sub-01'
    example_roi = 'V1'

    if example_subject in args.subjects and example_roi in args.rois:
        amp_path = baseline_dir / example_subject / example_roi / 'amplitudes_z.npy'

        if amp_path.exists():
            amplitudes_z = np.load(amp_path)
            reliability = compute_rdm_reliability(amplitudes_z)
            run_rdms = reliability['run_rdms']

            fig, axes = plt.subplots(2, 3, figsize=(15, 10))
            axes = axes.flatten()

            color_names = ['Red', 'Orange', 'Yellow', 'Green', 'Cyan', 'Blue', 'Purple', 'Magenta']

            for run_idx, rdm in enumerate(run_rdms):
                ax = axes[run_idx]
                im = ax.imshow(rdm, cmap='viridis', vmin=0, vmax=2)
                ax.set_title(f'Run {run_idx+1}', fontsize=12)
                ax.set_xticks(range(8))
                ax.set_yticks(range(8))
                ax.set_xticklabels(color_names, rotation=45, ha='right', fontsize=9)
                ax.set_yticklabels(color_names, fontsize=9)

                # Add colorbar
                plt.colorbar(im, ax=ax, fraction=0.046)

            plt.suptitle(f'RDM Matrices per Run: {example_subject}, {example_roi}',
                        fontsize=14, fontweight='bold')
            plt.tight_layout()

            fig_path2 = run_dir / f'rdm_matrices_per_run_{example_subject}_{example_roi}.png'
            plt.savefig(fig_path2)
            print(f"Saved example RDM matrices to {fig_path2}")
            plt.close()

    # Compute summary statistics
    summary = {
        'overall': {
            'mean_reliability': float(df['mean_correlation'].mean()),
            'std_reliability': float(df['mean_correlation'].std()),
            'median_reliability': float(df['mean_correlation'].median())
        },
        'by_roi': {},
        'quality_check': {
            'good_count': int((df['mean_correlation'] > 0.6).sum()),
            'acceptable_count': int(((df['mean_correlation'] > 0.4) & (df['mean_correlation'] <= 0.6)).sum()),
            'poor_count': int((df['mean_correlation'] <= 0.4).sum()),
            'total_count': len(df)
        }
    }

    for roi in args.rois:
        roi_data = df[df['roi'] == roi]['mean_correlation']
        if len(roi_data) > 0:
            summary['by_roi'][roi] = {
                'mean': float(roi_data.mean()),
                'std': float(roi_data.std()),
                'median': float(roi_data.median())
            }

    # Save results summary
    results_path = run_dir / 'results.json'
    with open(results_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"Saved summary to {results_path}")

    # Save settings
    settings = {
        'script': '03_rdm_reliability.py',
        'baseline_timestamp': args.baseline_timestamp,
        'subjects': args.subjects,
        'rois': args.rois,
        'timestamp': timestamp
    }
    settings_path = run_dir / 'settings.json'
    with open(settings_path, 'w') as f:
        json.dump(settings, f, indent=2)
    print(f"Saved settings to {settings_path}")

    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Overall RDM reliability: {summary['overall']['mean_reliability']:.3f} ± {summary['overall']['std_reliability']:.3f}")
    print(f"Good (>0.6): {summary['quality_check']['good_count']}/{summary['quality_check']['total_count']}")
    print(f"Acceptable (>0.4): {summary['quality_check']['acceptable_count']}/{summary['quality_check']['total_count']}")
    print(f"Poor (<0.4): {summary['quality_check']['poor_count']}/{summary['quality_check']['total_count']}")
    print("="*70)


if __name__ == '__main__':
    main()
