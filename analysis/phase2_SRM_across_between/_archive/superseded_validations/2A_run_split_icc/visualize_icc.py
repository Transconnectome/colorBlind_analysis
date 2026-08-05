"""
Visualize run-split ICC results
"""

import numpy as np
import json
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path


def visualize_icc_results(results_dir: Path):
    """
    Create heatmap visualization for ICC results.

    Parameters
    ----------
    results_dir : Path
        Directory containing ICC results
    """
    # Load results
    results_file = results_dir / 'icc_results.json'
    if not results_file.exists():
        raise FileNotFoundError(f"Results not found: {results_file}")

    with open(results_file, 'r') as f:
        results = json.load(f)

    rois = list(results.keys())
    subjects = ['sub-08', 'sub-09', 'sub-10']

    # Create correlation matrix (3 subjects × 4 ROIs)
    correlation_matrix = np.zeros((len(subjects), len(rois)))
    classification_matrix = np.empty((len(subjects), len(rois)), dtype=object)

    for i, roi in enumerate(rois):
        for j, subject in enumerate(subjects):
            if subject in results[roi]:
                correlation_matrix[j, i] = results[roi][subject]['split_half_correlation']
                classification_matrix[j, i] = results[roi][subject]['classification']
            else:
                correlation_matrix[j, i] = np.nan
                classification_matrix[j, i] = 'missing'

    # Create heatmap
    fig, ax = plt.subplots(figsize=(10, 6))

    # Use seaborn heatmap
    sns.heatmap(correlation_matrix, annot=True, fmt='.3f', cmap='RdYlGn',
                vmin=0, vmax=1, cbar_kws={'label': 'Split-Half Correlation'},
                xticklabels=rois, yticklabels=subjects,
                linewidths=2, linecolor='black', ax=ax)

    ax.set_xlabel('ROI', fontsize=13, fontweight='bold')
    ax.set_ylabel('CVD Subject', fontsize=13, fontweight='bold')
    ax.set_title('Within-Subject Split-Half Reliability by CVD Subject and ROI\n(Runs 1-3 vs Runs 4-6)',
                fontsize=14, fontweight='bold')

    # Add classification text to cells
    for i in range(len(subjects)):
        for j in range(len(rois)):
            cls = classification_matrix[i, j]
            if cls != 'missing':
                # Add classification label
                cls_abbrev = {'excellent': 'E', 'good': 'G', 'moderate': 'M', 'poor': 'P'}.get(cls, '?')
                ax.text(j + 0.5, i + 0.75, cls_abbrev, ha='center', va='bottom',
                       fontsize=8, fontweight='bold', color='black')

    plt.tight_layout()

    # Save
    output_file = results_dir / 'icc_heatmap.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved ICC heatmap to: {output_file}")

    # Create barplot by ROI
    fig, ax = plt.subplots(figsize=(10, 6))

    roi_means = []
    roi_stds = []
    for roi in rois:
        correlations = [results[roi][subj]['split_half_correlation']
                        for subj in subjects if subj in results[roi]]
        roi_means.append(np.mean(correlations))
        roi_stds.append(np.std(correlations))

    x = np.arange(len(rois))
    bars = ax.bar(x, roi_means, yerr=roi_stds, capsize=5,
                 color='skyblue', edgecolor='black', alpha=0.7)

    # Add threshold lines
    ax.axhline(0.75, color='green', linestyle='--', linewidth=2, label='Excellent (>0.75)', alpha=0.7)
    ax.axhline(0.60, color='orange', linestyle='--', linewidth=2, label='Good (>0.60)', alpha=0.7)

    ax.set_xticks(x)
    ax.set_xticklabels(rois, fontsize=12, fontweight='bold')
    ax.set_ylabel('Mean Split-Half Correlation', fontsize=13, fontweight='bold')
    ax.set_title('Within-Subject Split-Half Reliability by ROI\n(Mean ± SD across CVD subjects)',
                fontsize=14, fontweight='bold')
    ax.set_ylim([0, 1])
    ax.legend(fontsize=10)
    ax.grid(alpha=0.3, linestyle=':', axis='y')

    # Add value labels on bars
    for i, (bar, mean, std) in enumerate(zip(bars, roi_means, roi_stds)):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + std + 0.02,
               f'{mean:.3f}',
               ha='center', va='bottom', fontsize=10, fontweight='bold')

    plt.tight_layout()

    # Save
    output_file = results_dir / 'icc_barplot_by_roi.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved ICC barplot to: {output_file}")

    # Create individual subject comparison
    fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=True)

    for idx, subject in enumerate(subjects):
        ax = axes[idx]

        subject_correlations = []
        for roi in rois:
            if subject in results[roi]:
                subject_correlations.append(results[roi][subject]['split_half_correlation'])
            else:
                subject_correlations.append(0)

        colors = ['green' if c > 0.75 else 'orange' if c > 0.60 else 'red'
                 for c in subject_correlations]

        bars = ax.bar(range(len(rois)), subject_correlations, color=colors,
                     edgecolor='black', alpha=0.7)

        ax.axhline(0.75, color='green', linestyle='--', linewidth=1.5, alpha=0.5)
        ax.axhline(0.60, color='orange', linestyle='--', linewidth=1.5, alpha=0.5)

        ax.set_xticks(range(len(rois)))
        ax.set_xticklabels(rois, fontsize=11, fontweight='bold')
        ax.set_title(subject, fontsize=12, fontweight='bold')
        ax.set_ylim([0, 1])
        ax.grid(alpha=0.3, linestyle=':', axis='y')

        # Add value labels
        for i, (bar, val) in enumerate(zip(bars, subject_correlations)):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width()/2., val + 0.03,
                       f'{val:.2f}',
                       ha='center', va='bottom', fontsize=9, fontweight='bold')

    axes[0].set_ylabel('Split-Half Correlation', fontsize=13, fontweight='bold')
    fig.suptitle('Within-Subject Split-Half Reliability by CVD Subject',
                fontsize=14, fontweight='bold')

    plt.tight_layout()

    # Save
    output_file = results_dir / 'icc_by_subject.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved subject comparison to: {output_file}")


if __name__ == '__main__':
    # Find most recent results
    base_dir = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis')
    results_root = base_dir / 'analysis' / 'phase2_SRM_across_between' / 'validation' / '2A_run_split_icc' / 'results'

    results_dirs = sorted([d for d in results_root.iterdir() if d.is_dir()], reverse=True)

    if not results_dirs:
        raise FileNotFoundError(f"No ICC results found in {results_root}")

    results_dir = results_dirs[0]
    print(f"Visualizing results from: {results_dir}")

    visualize_icc_results(results_dir)

    print("\n✅ Visualization completed!")
