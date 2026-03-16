#!/usr/bin/env python3
"""Visualize the impact of FDR correction on B3 bootstrap results."""

import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path


def visualize_fdr_impact(fdr_results_path, output_dir):
    """Create visualization comparing raw vs FDR-corrected significance."""

    with open(fdr_results_path, 'r') as f:
        fdr_data = json.load(f)

    # Prepare data for visualization
    subjects = ['sub-08', 'sub-09', 'sub-10']
    rois = ['V1', 'V2', 'V3']

    # Data arrays
    raw_counts = np.zeros((len(subjects), len(rois)))
    fdr_within_counts = np.zeros((len(subjects), len(rois)))
    fdr_global_counts = np.zeros((len(subjects), len(rois)))

    for i, subject in enumerate(subjects):
        for j, roi in enumerate(rois):
            if roi in fdr_data['by_subject_roi'][subject]:
                data = fdr_data['by_subject_roi'][subject][roi]
                raw_counts[i, j] = data['n_significant_raw']
                fdr_within_counts[i, j] = data['n_significant_fdr_within_roi']

                # Count global FDR for this subject-ROI
                fdr_global_counts[i, j] = sum(
                    1 for test in fdr_data['all_tests']
                    if test['subject'] == subject and test['roi'] == roi and test['fdr_global']
                )

    # Create figure
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    # Plot 1: Raw vs FDR (within-ROI)
    ax = axes[0]
    x = np.arange(len(subjects) * len(rois))
    width = 0.35

    labels = [f'{s}\n{r}' for s in subjects for r in rois]
    raw_flat = raw_counts.flatten()
    fdr_within_flat = fdr_within_counts.flatten()

    ax.bar(x - width/2, raw_flat, width, label='Raw (no correction)', color='#e74c3c', alpha=0.8)
    ax.bar(x + width/2, fdr_within_flat, width, label='FDR within-ROI', color='#3498db', alpha=0.8)
    ax.axhline(y=28*0.05, color='gray', linestyle='--', linewidth=1, label='Chance (5% of 28)')
    ax.set_ylabel('Number of Significant Pairs (out of 28)')
    ax.set_title('Raw vs Within-ROI FDR Correction')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)
    ax.legend()
    ax.set_ylim(0, 30)
    ax.grid(axis='y', alpha=0.3)

    # Plot 2: Raw vs FDR (global)
    ax = axes[1]
    fdr_global_flat = fdr_global_counts.flatten()

    ax.bar(x - width/2, raw_flat, width, label='Raw (no correction)', color='#e74c3c', alpha=0.8)
    ax.bar(x + width/2, fdr_global_flat, width, label='FDR global', color='#27ae60', alpha=0.8)
    ax.axhline(y=28*0.05, color='gray', linestyle='--', linewidth=1, label='Chance (5% of 28)')
    ax.set_ylabel('Number of Significant Pairs (out of 28)')
    ax.set_title('Raw vs Global FDR Correction (Most Conservative)')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)
    ax.legend()
    ax.set_ylim(0, 30)
    ax.grid(axis='y', alpha=0.3)

    # Plot 3: Reduction in significance
    ax = axes[2]
    reduction_within = (raw_flat - fdr_within_flat) / raw_flat * 100
    reduction_global = (raw_flat - fdr_global_flat) / raw_flat * 100

    # Handle division by zero
    reduction_within[raw_flat == 0] = 0
    reduction_global[raw_flat == 0] = 0

    ax.bar(x - width/2, reduction_within, width, label='Within-ROI reduction', color='#3498db', alpha=0.8)
    ax.bar(x + width/2, reduction_global, width, label='Global reduction', color='#27ae60', alpha=0.8)
    ax.set_ylabel('% Reduction in Significant Pairs')
    ax.set_title('Impact of FDR Correction')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)
    ax.legend()
    ax.set_ylim(-10, 110)
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    output_path = output_dir / 'fdr_correction_impact.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Impact visualization saved to {output_path}")
    plt.close()

    # Create second figure: Filter targets surviving
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))

    # Count HIGH/MEDIUM/OTHER for each subject
    categories = ['HIGH\npriority', 'MEDIUM\npriority', 'OTHER\nextreme']
    x_pos = np.arange(len(categories))
    width = 0.25

    sub08_counts = [
        len(fdr_data['filter_targets']['fdr_surviving_by_subject']['sub-08']['HIGH_priority']),
        len(fdr_data['filter_targets']['fdr_surviving_by_subject']['sub-08']['MEDIUM_priority']),
        len(fdr_data['filter_targets']['fdr_surviving_by_subject']['sub-08']['OTHER_extreme'])
    ]

    sub09_counts = [
        len(fdr_data['filter_targets']['fdr_surviving_by_subject']['sub-09']['HIGH_priority']),
        len(fdr_data['filter_targets']['fdr_surviving_by_subject']['sub-09']['MEDIUM_priority']),
        len(fdr_data['filter_targets']['fdr_surviving_by_subject']['sub-09']['OTHER_extreme'])
    ]

    sub10_counts = [
        len(fdr_data['filter_targets']['fdr_surviving_by_subject']['sub-10']['HIGH_priority']),
        len(fdr_data['filter_targets']['fdr_surviving_by_subject']['sub-10']['MEDIUM_priority']),
        len(fdr_data['filter_targets']['fdr_surviving_by_subject']['sub-10']['OTHER_extreme'])
    ]

    ax.bar(x_pos - width, sub08_counts, width, label='sub-08 (Deutan)', color='#e74c3c', alpha=0.8)
    ax.bar(x_pos, sub09_counts, width, label='sub-09 (Protan)', color='#3498db', alpha=0.8)
    ax.bar(x_pos + width, sub10_counts, width, label='sub-10 (Deutan)', color='#95a5a6', alpha=0.8)

    ax.set_ylabel('Number of Pairs Surviving Global FDR')
    ax.set_title('Filter Targets After Global FDR Correction (q=0.05)')
    ax.set_xticks(x_pos)
    ax.set_xticklabels(categories)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    # Add text annotations
    original_high = ['red-orange', 'orange-yellow', 'cyan-blue']
    original_medium = ['red-magenta', 'blue-purple', 'red-green']

    ax.text(0.5, 0.95, f'Original HIGH targets: {", ".join(original_high)}',
           transform=ax.transAxes, fontsize=8, verticalalignment='top',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
    ax.text(0.5, 0.88, f'Original MEDIUM targets: {", ".join(original_medium)}',
           transform=ax.transAxes, fontsize=8, verticalalignment='top',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

    plt.tight_layout()
    output_path = output_dir / 'filter_targets_fdr_surviving.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Filter targets visualization saved to {output_path}")
    plt.close()


if __name__ == '__main__':
    base_dir = Path(__file__).parent
    fdr_results_path = base_dir / 'results' / 'fdr_corrected' / 'filter_pre_validation_fdr_corrected.json'
    output_dir = base_dir / 'results' / 'fdr_corrected'

    visualize_fdr_impact(fdr_results_path, output_dir)
