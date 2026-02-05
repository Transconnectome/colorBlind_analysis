"""
Visualize pairwise Procrustes analysis results.

Creates:
1. Distribution comparison: HC-to-HC vs CVD-to-HC by ROI
2. Violin plots showing full distributions
3. Heatmap of pairwise disparity matrix

Usage:
    python scripts/visualize_pairwise_results.py \
        --input-file results/pairwise_procrustes/pairwise_summary.json \
        --output-dir results/pairwise_procrustes/visualizations
"""

import numpy as np
import json
import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib

# Use non-interactive backend
matplotlib.use('Agg')


def create_distribution_comparison(results, output_dir):
    """
    Create violin plot comparing HC-to-HC vs CVD-to-HC distributions.
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

        hc_disparities = np.array(results[roi]['hc_to_hc']['disparities'])
        cvd_disparities = np.array(results[roi]['cvd_to_hc']['disparities'])

        # Create violin plot
        parts = ax.violinplot([hc_disparities, cvd_disparities],
                              positions=[1, 2],
                              showmeans=True,
                              showmedians=True,
                              widths=0.7)

        # Color the violins
        colors = ['#4CAF50', '#FF5722']
        for patch, color in zip(parts['bodies'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)

        # Add individual points
        np.random.seed(42)
        x_hc = np.random.normal(1, 0.04, len(hc_disparities))
        x_cvd = np.random.normal(2, 0.04, len(cvd_disparities))

        ax.scatter(x_hc, hc_disparities, alpha=0.5, s=30, color='#2E7D32', edgecolors='black', linewidths=0.5)
        ax.scatter(x_cvd, cvd_disparities, alpha=0.5, s=30, color='#C62828', edgecolors='black', linewidths=0.5)

        # Statistics
        hc_mean = results[roi]['hc_to_hc']['mean']
        cvd_mean = results[roi]['cvd_to_hc']['mean']
        p_value = results[roi]['statistical_test']['p_value']
        effect_size = results[roi]['statistical_test']['effect_size']

        # Styling
        ax.set_xticks([1, 2])
        ax.set_xticklabels(['HC→HC', 'CVD→HC'])
        ax.set_ylabel('Procrustes Disparity', fontsize=11)
        ax.set_title(f'{roi}\nHC: {hc_mean:.2f} ± {results[roi]["hc_to_hc"]["std"]:.2f}, '
                     f'CVD: {cvd_mean:.2f} ± {results[roi]["cvd_to_hc"]["std"]:.2f}\n'
                     f'p={p_value:.4f}, d={effect_size:.2f}',
                     fontsize=11, fontweight='bold')
        ax.grid(axis='y', alpha=0.3, linestyle='--')

        # Add significance marker if p < 0.05
        if p_value is not None and p_value < 0.05:
            y_max = max(hc_disparities.max(), cvd_disparities.max())
            ax.plot([1, 2], [y_max * 1.05, y_max * 1.05], 'k-', linewidth=1.5)
            sig_text = '***' if p_value < 0.001 else ('**' if p_value < 0.01 else '*')
            ax.text(1.5, y_max * 1.08, sig_text, ha='center', fontsize=14, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_dir / 'distribution_comparison_violin.png', dpi=150, bbox_inches='tight')
    plt.close()

    print(f"Saved: {output_dir / 'distribution_comparison_violin.png'}")


def create_summary_barplot(results, output_dir):
    """
    Create barplot comparing mean disparities across ROIs.
    """
    rois = ['V1', 'V2', 'V3', 'hV4']

    hc_means = []
    hc_stds = []
    cvd_means = []
    cvd_stds = []

    for roi in rois:
        if roi in results:
            hc_means.append(results[roi]['hc_to_hc']['mean'])
            hc_stds.append(results[roi]['hc_to_hc']['std'])
            cvd_means.append(results[roi]['cvd_to_hc']['mean'])
            cvd_stds.append(results[roi]['cvd_to_hc']['std'])
        else:
            hc_means.append(0)
            hc_stds.append(0)
            cvd_means.append(0)
            cvd_stds.append(0)

    fig, ax = plt.subplots(figsize=(10, 6))

    x = np.arange(len(rois))
    width = 0.35

    # Plot bars
    ax.bar(x - width/2, hc_means, width, yerr=hc_stds,
           label='HC→HC', color='#4CAF50', alpha=0.8, capsize=5)
    ax.bar(x + width/2, cvd_means, width, yerr=cvd_stds,
           label='CVD→HC', color='#FF5722', alpha=0.8, capsize=5)

    # Add significance markers
    for i, roi in enumerate(rois):
        if roi in results:
            p_value = results[roi]['statistical_test']['p_value']
            if p_value is not None and p_value < 0.05:
                y_pos = max(hc_means[i] + hc_stds[i], cvd_means[i] + cvd_stds[i]) * 1.1
                sig_text = '***' if p_value < 0.001 else ('**' if p_value < 0.01 else '*')
                ax.text(i, y_pos, sig_text, ha='center', fontsize=14, fontweight='bold')

    # Styling
    ax.set_xlabel('ROI', fontsize=12)
    ax.set_ylabel('Procrustes Disparity', fontsize=12)
    ax.set_title('Pairwise Procrustes Disparities: HC-to-HC vs CVD-to-HC\n(Each HC as Individual Reference)',
                 fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(rois)
    ax.legend(fontsize=11)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    plt.tight_layout()
    plt.savefig(output_dir / 'summary_barplot_pairwise.png', dpi=150, bbox_inches='tight')
    plt.close()

    print(f"Saved: {output_dir / 'summary_barplot_pairwise.png'}")


def create_disparity_matrix_heatmap(results, output_dir, roi):
    """
    Create heatmap of pairwise disparity matrix for one ROI.
    """
    if roi not in results:
        print(f"Skipping heatmap for {roi}: No data")
        return

    disparity_matrix_dict = results[roi]['disparity_matrix']

    # Parse subject pairs
    all_subjects = set()
    for key in disparity_matrix_dict.keys():
        ref, target = key.split('->')
        all_subjects.add(ref)
        all_subjects.add(target)

    all_subjects = sorted(all_subjects)
    n = len(all_subjects)

    # Build matrix
    matrix = np.full((n, n), np.nan)
    for i, ref_subj in enumerate(all_subjects):
        for j, target_subj in enumerate(all_subjects):
            key = f"{ref_subj}->{target_subj}"
            if key in disparity_matrix_dict:
                matrix[i, j] = disparity_matrix_dict[key]

    # Create heatmap
    fig, ax = plt.subplots(figsize=(10, 8))

    im = ax.imshow(matrix, cmap='YlOrRd', aspect='auto', interpolation='nearest')

    # Colorbar
    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label('Procrustes Disparity', fontsize=11)

    # Labels
    ax.set_xticks(np.arange(n))
    ax.set_yticks(np.arange(n))
    ax.set_xticklabels(all_subjects, rotation=45, ha='right')
    ax.set_yticklabels(all_subjects)

    ax.set_xlabel('Target Subject', fontsize=12)
    ax.set_ylabel('Reference Subject', fontsize=12)
    ax.set_title(f'{roi}: Pairwise Procrustes Disparity Matrix\n(Row → Column alignment)',
                 fontsize=13, fontweight='bold')

    # Add grid
    ax.set_xticks(np.arange(n) - 0.5, minor=True)
    ax.set_yticks(np.arange(n) - 0.5, minor=True)
    ax.grid(which='minor', color='gray', linestyle='-', linewidth=0.5)

    # Mark HC/CVD regions
    hc_subjects_in_matrix = [s for s in all_subjects if int(s) <= 7]
    n_hc = len(hc_subjects_in_matrix)

    if n_hc > 0 and n_hc < n:
        # Draw lines separating HC and CVD
        ax.axhline(y=n_hc - 0.5, color='blue', linewidth=2, linestyle='--', alpha=0.7)
        ax.axvline(x=n_hc - 0.5, color='blue', linewidth=2, linestyle='--', alpha=0.7)

        # Add region labels
        ax.text(-0.5, n_hc/2, 'HC', fontsize=12, fontweight='bold', color='green',
                ha='right', va='center', rotation=90)
        ax.text(-0.5, n_hc + (n - n_hc)/2, 'CVD', fontsize=12, fontweight='bold', color='red',
                ha='right', va='center', rotation=90)

    plt.tight_layout()
    plt.savefig(output_dir / f'{roi}_disparity_matrix_heatmap.png', dpi=150, bbox_inches='tight')
    plt.close()

    print(f"Saved: {output_dir / f'{roi}_disparity_matrix_heatmap.png'}")


def print_detailed_statistics(results):
    """
    Print detailed statistics table.
    """
    print("\n" + "="*100)
    print("Detailed Pairwise Procrustes Statistics")
    print("="*100)

    for roi in ['V1', 'V2', 'V3', 'hV4']:
        if roi not in results:
            continue

        print(f"\n{roi}:")
        print("-"*100)

        hc = results[roi]['hc_to_hc']
        cvd = results[roi]['cvd_to_hc']
        stats = results[roi]['statistical_test']

        print(f"  HC→HC disparities (n={hc['n']}):")
        print(f"    Mean ± Std:     {hc['mean']:.4f} ± {hc['std']:.4f}")
        print(f"    Median:         {hc['median']:.4f}")
        print(f"    Range:          [{hc['min']:.4f}, {hc['max']:.4f}]")
        print(f"    IQR:            [{hc['percentiles']['25']:.4f}, {hc['percentiles']['75']:.4f}]")

        print(f"\n  CVD→HC disparities (n={cvd['n']}):")
        print(f"    Mean ± Std:     {cvd['mean']:.4f} ± {cvd['std']:.4f}")
        print(f"    Median:         {cvd['median']:.4f}")
        print(f"    Range:          [{cvd['min']:.4f}, {cvd['max']:.4f}]")
        print(f"    IQR:            [{cvd['percentiles']['25']:.4f}, {cvd['percentiles']['75']:.4f}]")

        print(f"\n  Statistical Test (Mann-Whitney U):")
        print(f"    Difference:     {cvd['mean'] - hc['mean']:.4f} (CVD - HC)")
        print(f"    Effect Size:    {stats['effect_size']:.4f} (Cohen's d)")
        print(f"    U-statistic:    {stats['u_statistic']:.4f}" if stats['u_statistic'] else "    U-statistic:    N/A")
        print(f"    p-value:        {stats['p_value']:.4f}" if stats['p_value'] else "    p-value:        N/A")

        if stats['p_value'] is not None:
            if stats['p_value'] < 0.001:
                sig = "*** (highly significant)"
            elif stats['p_value'] < 0.01:
                sig = "** (very significant)"
            elif stats['p_value'] < 0.05:
                sig = "* (significant)"
            else:
                sig = "n.s. (not significant)"
            print(f"    Significance:   {sig}")

    print("="*100)


def main():
    parser = argparse.ArgumentParser(
        description='Visualize pairwise Procrustes analysis results'
    )
    parser.add_argument('--input-file', type=str, required=True,
                        help='Input JSON file with pairwise results')
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
    create_distribution_comparison(results, output_dir)
    create_summary_barplot(results, output_dir)

    # Create heatmaps for each ROI
    for roi in ['V1', 'V2', 'V3', 'hV4']:
        create_disparity_matrix_heatmap(results, output_dir, roi)

    # Print detailed statistics
    print_detailed_statistics(results)

    print(f"\n✅ All visualizations saved to: {output_dir}")


if __name__ == '__main__':
    main()
