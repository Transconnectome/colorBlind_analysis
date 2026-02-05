"""
Visualize between-subject Procrustes alignment results.

Creates:
1. Disparity comparison: HC vs CVD by ROI
2. RDM correlation comparison: HC vs CVD by ROI
3. Per-subject disparity distributions

Usage:
    python scripts/visualize_between_subject_results.py \
        --input-file results/between_subject_procrustes/alignment_summary.json \
        --output-dir results/between_subject_procrustes/visualizations
"""

import numpy as np
import json
import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib

# Use non-interactive backend
matplotlib.use('Agg')


def create_disparity_comparison(results, output_dir):
    """
    Create barplot comparing HC vs CVD disparities by ROI.
    """
    rois = ['V1', 'V2', 'V3', 'hV4']

    hc_means = []
    hc_stds = []
    cvd_means = []
    cvd_stds = []

    for roi in rois:
        if roi in results:
            hc_means.append(results[roi]['summary']['hc']['disparity']['mean'])
            hc_stds.append(results[roi]['summary']['hc']['disparity']['std'])
            cvd_means.append(results[roi]['summary']['cvd']['disparity']['mean'])
            cvd_stds.append(results[roi]['summary']['cvd']['disparity']['std'])
        else:
            hc_means.append(0)
            hc_stds.append(0)
            cvd_means.append(0)
            cvd_stds.append(0)

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))

    x = np.arange(len(rois))
    width = 0.35

    # Plot bars
    ax.bar(x - width/2, hc_means, width, yerr=hc_stds,
           label='HC', color='#4CAF50', alpha=0.8, capsize=5)
    ax.bar(x + width/2, cvd_means, width, yerr=cvd_stds,
           label='CVD', color='#FF5722', alpha=0.8, capsize=5)

    # Styling
    ax.set_xlabel('ROI', fontsize=12)
    ax.set_ylabel('Procrustes Disparity (to HC reference)', fontsize=12)
    ax.set_title('Between-Subject Procrustes Disparity: HC vs CVD', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(rois)
    ax.legend(fontsize=11)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    plt.tight_layout()
    plt.savefig(output_dir / 'disparity_comparison_hc_cvd.png', dpi=150, bbox_inches='tight')
    plt.close()

    print(f"Saved: {output_dir / 'disparity_comparison_hc_cvd.png'}")


def create_rdm_correlation_comparison(results, output_dir):
    """
    Create barplot comparing HC vs CVD RDM correlations by ROI.
    """
    rois = ['V1', 'V2', 'V3', 'hV4']

    hc_means = []
    hc_stds = []
    cvd_means = []
    cvd_stds = []

    for roi in rois:
        if roi in results:
            hc_mean = results[roi]['summary']['hc']['rdm_correlation']['mean']
            hc_std = results[roi]['summary']['hc']['rdm_correlation']['std']
            cvd_mean = results[roi]['summary']['cvd']['rdm_correlation']['mean']
            cvd_std = results[roi]['summary']['cvd']['rdm_correlation']['std']

            # Handle NaN values
            hc_means.append(0 if np.isnan(hc_mean) else hc_mean)
            hc_stds.append(0 if np.isnan(hc_std) else hc_std)
            cvd_means.append(0 if np.isnan(cvd_mean) else cvd_mean)
            cvd_stds.append(0 if np.isnan(cvd_std) else cvd_std)
        else:
            hc_means.append(0)
            hc_stds.append(0)
            cvd_means.append(0)
            cvd_stds.append(0)

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))

    x = np.arange(len(rois))
    width = 0.35

    # Plot bars
    ax.bar(x - width/2, hc_means, width, yerr=hc_stds,
           label='HC', color='#2196F3', alpha=0.8, capsize=5)
    ax.bar(x + width/2, cvd_means, width, yerr=cvd_stds,
           label='CVD', color='#9C27B0', alpha=0.8, capsize=5)

    # Styling
    ax.set_xlabel('ROI', fontsize=12)
    ax.set_ylabel('RDM Correlation (with HC reference)', fontsize=12)
    ax.set_title('Between-Subject RDM Similarity: HC vs CVD', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(rois)
    ax.legend(fontsize=11)
    ax.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    plt.tight_layout()
    plt.savefig(output_dir / 'rdm_correlation_comparison_hc_cvd.png', dpi=150, bbox_inches='tight')
    plt.close()

    print(f"Saved: {output_dir / 'rdm_correlation_comparison_hc_cvd.png'}")


def create_per_subject_disparity_plot(results, output_dir):
    """
    Create scatter plot showing per-subject disparities by ROI.
    """
    rois = ['V1', 'V2', 'V3', 'hV4']

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()

    for i, roi in enumerate(rois):
        ax = axes[i]

        if roi not in results:
            ax.text(0.5, 0.5, f'{roi}\nNo data', ha='center', va='center',
                    fontsize=14, transform=ax.transAxes)
            ax.set_xticks([])
            ax.set_yticks([])
            continue

        subjects = results[roi]['subjects']

        # Separate HC and CVD
        hc_subjects = []
        hc_disparities = []
        cvd_subjects = []
        cvd_disparities = []

        for subj_id, data in subjects.items():
            if data['group'] == 'HC':
                hc_subjects.append(subj_id)
                hc_disparities.append(data['disparity'])
            else:
                cvd_subjects.append(subj_id)
                cvd_disparities.append(data['disparity'])

        # Plot
        x_hc = np.arange(len(hc_subjects))
        x_cvd = np.arange(len(cvd_subjects)) + len(hc_subjects) + 0.5

        ax.scatter(x_hc, hc_disparities, s=100, c='#4CAF50', alpha=0.7,
                   label='HC', edgecolors='black', linewidths=1)
        ax.scatter(x_cvd, cvd_disparities, s=100, c='#FF5722', alpha=0.7,
                   label='CVD', edgecolors='black', linewidths=1)

        # Add mean lines
        if hc_disparities:
            ax.axhline(y=np.mean(hc_disparities), color='#4CAF50', linestyle='--',
                       linewidth=2, alpha=0.5, label=f'HC mean: {np.mean(hc_disparities):.1f}')
        if cvd_disparities:
            ax.axhline(y=np.mean(cvd_disparities), color='#FF5722', linestyle='--',
                       linewidth=2, alpha=0.5, label=f'CVD mean: {np.mean(cvd_disparities):.1f}')

        # Styling
        ax.set_title(roi, fontsize=14, fontweight='bold')
        ax.set_ylabel('Procrustes Disparity', fontsize=11)
        ax.set_xlabel('Subject', fontsize=11)

        # X-axis labels
        all_subjects = hc_subjects + cvd_subjects
        ax.set_xticks(list(x_hc) + list(x_cvd))
        ax.set_xticklabels([s.replace('sub-', '') for s in all_subjects], rotation=45)

        ax.legend(fontsize=9)
        ax.grid(axis='y', alpha=0.3, linestyle='--')

    plt.tight_layout()
    plt.savefig(output_dir / 'per_subject_disparity_distribution.png', dpi=150, bbox_inches='tight')
    plt.close()

    print(f"Saved: {output_dir / 'per_subject_disparity_distribution.png'}")


def print_summary_table(results):
    """
    Print summary table of results.
    """
    print("\n" + "="*80)
    print("Between-Subject Procrustes Alignment Summary")
    print("="*80)

    print("\nProcrustes Disparity (to HC reference):")
    print("-"*80)
    print(f"{'ROI':<8} {'HC Mean':<12} {'HC Std':<12} {'CVD Mean':<12} {'CVD Std':<12}")
    print("-"*80)

    for roi in ['V1', 'V2', 'V3', 'hV4']:
        if roi in results:
            hc_mean = results[roi]['summary']['hc']['disparity']['mean']
            hc_std = results[roi]['summary']['hc']['disparity']['std']
            cvd_mean = results[roi]['summary']['cvd']['disparity']['mean']
            cvd_std = results[roi]['summary']['cvd']['disparity']['std']

            print(f"{roi:<8} {hc_mean:<12.4f} {hc_std:<12.4f} {cvd_mean:<12.4f} {cvd_std:<12.4f}")

    print("\nRDM Correlation (with HC reference):")
    print("-"*80)
    print(f"{'ROI':<8} {'HC Mean':<12} {'HC Std':<12} {'CVD Mean':<12} {'CVD Std':<12}")
    print("-"*80)

    for roi in ['V1', 'V2', 'V3', 'hV4']:
        if roi in results:
            hc_mean = results[roi]['summary']['hc']['rdm_correlation']['mean']
            hc_std = results[roi]['summary']['hc']['rdm_correlation']['std']
            cvd_mean = results[roi]['summary']['cvd']['rdm_correlation']['mean']
            cvd_std = results[roi]['summary']['cvd']['rdm_correlation']['std']

            hc_mean_str = f"{hc_mean:.4f}" if not np.isnan(hc_mean) else "NaN"
            hc_std_str = f"{hc_std:.4f}" if not np.isnan(hc_std) else "NaN"
            cvd_mean_str = f"{cvd_mean:.4f}" if not np.isnan(cvd_mean) else "NaN"
            cvd_std_str = f"{cvd_std:.4f}" if not np.isnan(cvd_std) else "NaN"

            print(f"{roi:<8} {hc_mean_str:<12} {hc_std_str:<12} {cvd_mean_str:<12} {cvd_std_str:<12}")

    print("="*80)


def main():
    parser = argparse.ArgumentParser(
        description='Visualize between-subject Procrustes results'
    )
    parser.add_argument('--input-file', type=str, required=True,
                        help='Input JSON file with alignment results')
    parser.add_argument('--output-dir', type=str, required=True,
                        help='Output directory for visualizations')

    args = parser.parse_args()

    # Load results
    with open(args.input_file) as f:
        results = json.load(f)

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Creating visualizations...")

    # Create visualizations
    create_disparity_comparison(results, output_dir)
    create_rdm_correlation_comparison(results, output_dir)
    create_per_subject_disparity_plot(results, output_dir)

    # Print summary table
    print_summary_table(results)

    print(f"\n✅ All visualizations saved to: {output_dir}")


if __name__ == '__main__':
    main()
