"""
Visualize RDM consistency results (HC vs CVD comparison)
"""

import numpy as np
import json
import matplotlib.pyplot as plt
from pathlib import Path


def visualize_rdm_consistency(results_dir: Path):
    """
    Create visualization comparing HC vs CVD RDM consistency.

    Parameters
    ----------
    results_dir : Path
        Directory containing RDM consistency results
    """
    # Load results
    results_file = results_dir / 'rdm_split_half_results.json'
    if not results_file.exists():
        raise FileNotFoundError(f"Results not found: {results_file}")

    with open(results_file, 'r') as f:
        results = json.load(f)

    rois = [roi for roi in ['V1', 'V2', 'V3', 'hV4'] if roi in results]

    # Extract group stats
    hc_means = []
    hc_stds = []
    cvd_means = []
    cvd_stds = []

    for roi in rois:
        if 'group_stats' in results[roi]:
            stats = results[roi]['group_stats']
            hc_means.append(stats['hc_mean'])
            hc_stds.append(stats['hc_std'])
            cvd_means.append(stats['cvd_mean'])
            cvd_stds.append(stats['cvd_std'])
        else:
            hc_means.append(0)
            hc_stds.append(0)
            cvd_means.append(0)
            cvd_stds.append(0)

    # Create grouped barplot
    fig, ax = plt.subplots(figsize=(12, 7))

    x = np.arange(len(rois))
    width = 0.35

    bars_hc = ax.bar(x - width/2, hc_means, width, yerr=hc_stds,
                     label='HC', color='steelblue', alpha=0.7, capsize=5,
                     edgecolor='black')
    bars_cvd = ax.bar(x + width/2, cvd_means, width, yerr=cvd_stds,
                      label='CVD', color='coral', alpha=0.7, capsize=5,
                      edgecolor='black')

    # Add threshold line
    ax.axhline(0.5, color='gray', linestyle='--', linewidth=1.5, alpha=0.5,
              label='Moderate reliability (0.5)')

    ax.set_xticks(x)
    ax.set_xticklabels(rois, fontsize=12, fontweight='bold')
    ax.set_ylabel('Split-Half RDM Correlation', fontsize=13, fontweight='bold')
    ax.set_title('RDM Consistency: HC vs CVD by ROI\n(Runs 1-3 vs Runs 4-6)',
                fontsize=14, fontweight='bold')
    ax.set_ylim([0, 1])
    ax.legend(fontsize=11, loc='upper right')
    ax.grid(alpha=0.3, linestyle=':', axis='y')

    # Add value labels on bars
    for i, (bar_hc, bar_cvd, hc_mean, cvd_mean) in enumerate(zip(bars_hc, bars_cvd, hc_means, cvd_means)):
        # HC label
        ax.text(bar_hc.get_x() + bar_hc.get_width()/2., hc_mean + hc_stds[i] + 0.02,
               f'{hc_mean:.2f}',
               ha='center', va='bottom', fontsize=9, fontweight='bold')
        # CVD label
        ax.text(bar_cvd.get_x() + bar_cvd.get_width()/2., cvd_mean + cvd_stds[i] + 0.02,
               f'{cvd_mean:.2f}',
               ha='center', va='bottom', fontsize=9, fontweight='bold')

        # Add marker if CVD ≥ HC for critical ROIs
        roi = rois[i]
        if roi in ['V1', 'V2'] and cvd_mean >= hc_mean:
            ax.text(i, max(hc_mean, cvd_mean) + max(hc_stds[i], cvd_stds[i]) + 0.10,
                   '✓', ha='center', va='bottom', fontsize=20, color='green',
                   fontweight='bold')

    plt.tight_layout()

    # Save
    output_file = results_dir / 'rdm_consistency_comparison.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved RDM consistency comparison to: {output_file}")

    # Create individual subject boxplot
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), sharey=True)
    axes = axes.flatten()

    for idx, roi in enumerate(rois):
        ax = axes[idx]

        # Get individual correlations
        hc_values = []
        cvd_values = []

        for subject, data in results[roi].items():
            if subject.startswith('sub-'):
                corr = data['split_half_correlation']
                if subject in ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05', 'sub-06', 'sub-07']:
                    hc_values.append(corr)
                else:
                    cvd_values.append(corr)

        # Boxplot
        bp = ax.boxplot([hc_values, cvd_values], labels=['HC', 'CVD'],
                        patch_artist=True, widths=0.6)

        # Color boxes
        bp['boxes'][0].set_facecolor('steelblue')
        bp['boxes'][0].set_alpha(0.7)
        bp['boxes'][1].set_facecolor('coral')
        bp['boxes'][1].set_alpha(0.7)

        # Add individual points
        np.random.seed(42)
        x_hc = np.random.normal(1, 0.04, size=len(hc_values))
        x_cvd = np.random.normal(2, 0.04, size=len(cvd_values))
        ax.scatter(x_hc, hc_values, alpha=0.6, color='darkblue', s=50, zorder=3)
        ax.scatter(x_cvd, cvd_values, alpha=0.6, color='darkred', s=50, zorder=3)

        ax.axhline(0.5, color='gray', linestyle='--', linewidth=1, alpha=0.5)
        ax.set_title(f'{roi}', fontsize=13, fontweight='bold')
        ax.set_ylim([0, 1])
        ax.grid(alpha=0.3, linestyle=':', axis='y')

        # Add stats
        if 'group_stats' in results[roi]:
            stats = results[roi]['group_stats']
            p_val = stats['p_value']
            sig_str = '**' if p_val < 0.01 else '*' if p_val < 0.05 else 'ns'
            ax.text(1.5, 0.95, f'p={p_val:.3f} {sig_str}',
                   ha='center', fontsize=10, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    axes[0].set_ylabel('Split-Half RDM Correlation', fontsize=13, fontweight='bold')
    fig.suptitle('Individual Subject RDM Consistency by Group',
                fontsize=14, fontweight='bold')

    plt.tight_layout()

    # Save
    output_file = results_dir / 'rdm_consistency_boxplot.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved RDM consistency boxplot to: {output_file}")


if __name__ == '__main__':
    # Find most recent results
    base_dir = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis')
    results_root = base_dir / 'analysis' / 'phase2_SRM_across_between' / 'validation' / '2B_rdm_consistency' / 'results'

    results_dirs = sorted([d for d in results_root.iterdir() if d.is_dir()], reverse=True)

    if not results_dirs:
        raise FileNotFoundError(f"No RDM consistency results found in {results_root}")

    results_dir = results_dirs[0]
    print(f"Visualizing results from: {results_dir}")

    visualize_rdm_consistency(results_dir)

    print("\n✅ Visualization completed!")
