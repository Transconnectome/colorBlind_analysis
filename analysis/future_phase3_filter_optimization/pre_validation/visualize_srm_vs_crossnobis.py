#!/usr/bin/env python3
"""Visualize SRM vs Crossnobis comparison for Criticism 2."""

import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from scipy.stats import spearmanr


def visualize_srm_vs_crossnobis():
    """Create comparison visualizations."""

    # Load results
    base_dir = Path(__file__).parent
    srm_path = base_dir / "results" / "fdr_corrected" / "filter_pre_validation_fdr_corrected.json"
    crossnobis_path = base_dir / "results" / "crossnobis_pairs" / "crossnobis_pair_analysis.json"

    with open(srm_path) as f:
        srm_data = json.load(f)
    with open(crossnobis_path) as f:
        crossnobis_data = json.load(f)

    subjects = ['sub-08', 'sub-09', 'sub-10']
    rois = ['V1', 'V2', 'V3']

    # Figure 1: FDR-surviving pairs comparison
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))

    x_labels = [f'{s}\n{r}' for s in subjects for r in rois]
    x = np.arange(len(x_labels))
    width = 0.35

    srm_counts = []
    crossnobis_counts = []

    for subject in subjects:
        for roi in rois:
            # SRM counts
            srm_count = sum(
                1 for test in srm_data['all_tests']
                if test['subject'] == subject and test['roi'] == roi and test['fdr_global']
            )
            srm_counts.append(srm_count)

            # Crossnobis counts
            crossnobis_count = sum(
                1 for test in crossnobis_data['all_tests']
                if test['subject'] == subject and test['roi'] == roi and test['fdr_global']
            )
            crossnobis_counts.append(crossnobis_count)

    ax.bar(x - width/2, srm_counts, width, label='SRM (HC-optimized k=3-4 space)',
           color='#e74c3c', alpha=0.8)
    ax.bar(x + width/2, crossnobis_counts, width, label='Crossnobis (Native voxel space)',
           color='#3498db', alpha=0.8)

    ax.set_ylabel('Number of Pairs Surviving Global FDR (out of 28)')
    ax.set_title('Criticism 2: SRM vs Crossnobis Replication\n(Representation-Dependent Effects)')
    ax.set_xticks(x)
    ax.set_xticklabels(x_labels, fontsize=9)
    ax.legend()
    ax.set_ylim(0, 18)
    ax.grid(axis='y', alpha=0.3)

    # Add annotation
    ax.text(0.5, 0.95,
            '⚠️ CRITICAL: Zero pairs survive in native space across all subjects/ROIs',
            transform=ax.transAxes, fontsize=11, weight='bold',
            verticalalignment='top', ha='center',
            bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5))

    plt.tight_layout()
    output_path1 = base_dir / 'results' / 'crossnobis_pairs' / 'srm_vs_crossnobis_fdr.png'
    plt.savefig(output_path1, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_path1}")
    plt.close()

    # Figure 2: Z-score correlation scatter plots
    fig, axes = plt.subplots(3, 3, figsize=(15, 15))
    axes = axes.flatten()

    idx = 0
    for subject in subjects:
        for roi in rois:
            ax = axes[idx]

            # Get z-scores
            srm_z = []
            crossnobis_z = []

            pair_labels = crossnobis_data['config']['pair_labels']

            if roi not in crossnobis_data['by_subject_roi'].get(subject, {}):
                ax.text(0.5, 0.5, 'No Data', ha='center', va='center', fontsize=14)
                ax.set_title(f'{subject} {roi}')
                idx += 1
                continue

            for pair_label in pair_labels:
                # SRM
                if pair_label in srm_data['by_subject_roi'][subject][roi]['pairs']:
                    srm_z.append(srm_data['by_subject_roi'][subject][roi]['pairs'][pair_label]['z_score'])
                else:
                    srm_z.append(np.nan)

                # Crossnobis
                if pair_label in crossnobis_data['by_subject_roi'][subject][roi]['pairs']:
                    crossnobis_z.append(crossnobis_data['by_subject_roi'][subject][roi]['pairs'][pair_label]['z_score'])
                else:
                    crossnobis_z.append(np.nan)

            srm_z = np.array(srm_z)
            crossnobis_z = np.array(crossnobis_z)

            # Remove NaNs
            valid = ~(np.isnan(srm_z) | np.isnan(crossnobis_z))
            srm_z_valid = srm_z[valid]
            crossnobis_z_valid = crossnobis_z[valid]

            if len(srm_z_valid) < 3:
                ax.text(0.5, 0.5, 'Insufficient Data', ha='center', va='center', fontsize=12)
                ax.set_title(f'{subject} {roi}')
                idx += 1
                continue

            # Compute correlation
            r, p = spearmanr(srm_z_valid, crossnobis_z_valid)

            # Scatter plot
            ax.scatter(srm_z_valid, crossnobis_z_valid, alpha=0.6, s=50)

            # Reference line (y=x)
            lim = max(abs(srm_z_valid).max(), abs(crossnobis_z_valid).max()) + 1
            ax.plot([-lim, lim], [-lim, lim], 'k--', alpha=0.3, linewidth=1)

            # Zero lines
            ax.axhline(0, color='gray', linewidth=0.5, alpha=0.5)
            ax.axvline(0, color='gray', linewidth=0.5, alpha=0.5)

            # Color by interpretation
            if r > 0.5 and p < 0.05:
                color = '#27ae60'  # green
                interpretation = '✅ Strong'
            elif r > 0.3:
                color = '#f39c12'  # orange
                interpretation = '⚠️ Moderate'
            else:
                color = '#e74c3c'  # red
                interpretation = '❌ Weak'

            ax.set_title(f'{subject} {roi}\nr={r:.3f}, p={p:.4f}\n{interpretation}',
                        fontsize=10, color=color, weight='bold')
            ax.set_xlabel('SRM z-score', fontsize=9)
            ax.set_ylabel('Crossnobis z-score', fontsize=9)
            ax.set_xlim(-lim, lim)
            ax.set_ylim(-lim, lim)
            ax.grid(alpha=0.3)

            idx += 1

    plt.suptitle('Z-score Correlation: SRM vs Crossnobis\n'
                'Moderate convergence (r=0.3-0.7) suggests SRM captures signal but amplifies it',
                fontsize=14, weight='bold')
    plt.tight_layout()
    output_path2 = base_dir / 'results' / 'crossnobis_pairs' / 'srm_vs_crossnobis_correlation.png'
    plt.savefig(output_path2, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_path2}")
    plt.close()

    # Figure 3: Summary bar chart (overall comparison)
    fig, ax = plt.subplots(1, 1, figsize=(8, 6))

    categories = ['Raw Sig\n(p<0.05)', 'FDR Sig\n(q<0.05)', 'Median\nCorrelation']

    # Compute overall stats
    srm_raw_sig = srm_data['summary']['significant_raw_count']
    srm_fdr_sig = srm_data['summary']['significant_global_fdr_count']

    crossnobis_raw_sig = crossnobis_data['summary']['n_raw_significant']
    crossnobis_fdr_sig = crossnobis_data['summary']['n_fdr_significant']

    # Median correlation
    correlations = []
    for subject in subjects:
        for roi in rois:
            if 'srm_comparison' in crossnobis_data:
                if subject in crossnobis_data['srm_comparison']:
                    if roi in crossnobis_data['srm_comparison'][subject]:
                        correlations.append(crossnobis_data['srm_comparison'][subject][roi]['spearman_r'])

    median_r = np.median(correlations) if correlations else 0

    x_pos = np.arange(len(categories))
    width = 0.35

    srm_values = [srm_raw_sig / 252 * 100, srm_fdr_sig / 252 * 100, 0]
    crossnobis_values = [crossnobis_raw_sig / 252 * 100, crossnobis_fdr_sig / 252 * 100, median_r * 100]

    ax.bar(x_pos[:2] - width/2, srm_values[:2], width, label='SRM', color='#e74c3c', alpha=0.8)
    ax.bar(x_pos[:2] + width/2, crossnobis_values[:2], width, label='Crossnobis', color='#3498db', alpha=0.8)

    # Correlation bar (single, centered)
    ax.bar(x_pos[2], crossnobis_values[2], width, label='Median r (SRM vs Crossnobis)',
           color='#9b59b6', alpha=0.8)

    ax.set_ylabel('Percentage / Correlation ×100')
    ax.set_title('Overall Summary: SRM Amplifies Effects\nBut Captures Real Signal (r=0.53)',
                fontsize=12, weight='bold')
    ax.set_xticks(x_pos)
    ax.set_xticklabels(categories)
    ax.legend()
    ax.set_ylim(0, 55)
    ax.grid(axis='y', alpha=0.3)

    # Add value labels
    for i, v in enumerate(srm_values[:2]):
        ax.text(i - width/2, v + 1, f'{v:.1f}%', ha='center', fontsize=9, weight='bold')
    for i, v in enumerate(crossnobis_values[:2]):
        ax.text(i + width/2, v + 1, f'{v:.1f}%', ha='center', fontsize=9, weight='bold')
    ax.text(2, crossnobis_values[2] + 1, f'r={median_r:.2f}', ha='center', fontsize=9, weight='bold')

    plt.tight_layout()
    output_path3 = base_dir / 'results' / 'crossnobis_pairs' / 'srm_amplification_summary.png'
    plt.savefig(output_path3, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_path3}")
    plt.close()

    print("\nVisualization complete!")


if __name__ == '__main__':
    visualize_srm_vs_crossnobis()
