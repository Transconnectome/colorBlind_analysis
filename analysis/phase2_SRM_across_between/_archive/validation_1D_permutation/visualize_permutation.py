"""
Visualize permutation test results
"""

import numpy as np
import json
import matplotlib.pyplot as plt
from pathlib import Path


def visualize_permutation_results(results_dir: Path):
    """
    Create histogram visualizations for permutation test results.

    Parameters
    ----------
    results_dir : Path
        Directory containing permutation test results
    """
    # Load full results (with null distributions)
    results_file = results_dir / 'permutation_results_full.json'
    if not results_file.exists():
        raise FileNotFoundError(f"Results not found: {results_file}")

    with open(results_file, 'r') as f:
        results = json.load(f)

    rois = list(results.keys())
    n_rois = len(rois)

    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()

    for i, roi in enumerate(rois):
        ax = axes[i]
        roi_results = results[roi]

        # Extract data
        null_dist = np.array(roi_results['null_distribution'])
        t_obs = roi_results['observed_t']
        p_value = roi_results['p_value']
        percentile = roi_results['percentile']

        # Plot null distribution
        ax.hist(null_dist, bins=50, color='lightblue', edgecolor='black', alpha=0.7, density=True)

        # Add observed t-statistic line
        ymin, ymax = ax.get_ylim()
        ax.axvline(t_obs, color='red', linewidth=3, linestyle='--',
                  label=f'Observed t={t_obs:.2f}')

        # Add critical values (±1.96 for two-tailed α=0.05 if normal)
        # But we use empirical distribution, so mark 95th percentile
        critical_pos = np.percentile(np.abs(null_dist), 95)
        ax.axvline(critical_pos, color='orange', linewidth=2, linestyle=':',
                  label=f'95th percentile={critical_pos:.2f}', alpha=0.7)
        ax.axvline(-critical_pos, color='orange', linewidth=2, linestyle=':', alpha=0.7)

        # Styling
        ax.set_xlabel('t-statistic', fontsize=12, fontweight='bold')
        ax.set_ylabel('Density', fontsize=12, fontweight='bold')
        ax.set_title(f'{roi}: p={p_value:.4f} ({percentile:.1f}%ile)',
                    fontsize=13, fontweight='bold',
                    color='green' if p_value < 0.05 else 'red')
        ax.legend(fontsize=10, loc='upper right')
        ax.grid(alpha=0.3, linestyle=':')

        # Add text box with results
        textstr = f'CVD > HC\nt={t_obs:.2f}\np={p_value:.4f}\n'
        textstr += '✅ Significant' if p_value < 0.05 else '❌ Not sig.'
        props = dict(boxstyle='round', facecolor='wheat' if p_value < 0.05 else 'lightgray', alpha=0.8)
        ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=10,
               verticalalignment='top', bbox=props, fontweight='bold')

    plt.suptitle('Permutation Test Results: CVD-HC vs HC-HC Disparity',
                fontsize=16, fontweight='bold', y=0.995)
    plt.tight_layout()

    # Save
    output_file = results_dir / 'permutation_histograms.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved permutation histograms to: {output_file}")

    # Create summary barplot
    fig, ax = plt.subplots(figsize=(10, 6))

    roi_names = list(results.keys())
    p_values = [results[roi]['p_value'] for roi in roi_names]
    colors = ['green' if p < 0.05 else 'red' for p in p_values]

    bars = ax.bar(range(len(roi_names)), p_values, color=colors, alpha=0.7, edgecolor='black')

    # Add significance threshold line
    ax.axhline(0.05, color='black', linewidth=2, linestyle='--', label='α=0.05')

    # Styling
    ax.set_xticks(range(len(roi_names)))
    ax.set_xticklabels(roi_names, fontsize=12, fontweight='bold')
    ax.set_ylabel('P-value', fontsize=13, fontweight='bold')
    ax.set_title('Permutation Test P-values by ROI', fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(alpha=0.3, linestyle=':', axis='y')

    # Add p-value labels on bars
    for i, (bar, p) in enumerate(zip(bars, p_values)):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
               f'p={p:.4f}',
               ha='center', va='bottom', fontsize=10, fontweight='bold')

    plt.tight_layout()

    # Save
    output_file = results_dir / 'permutation_p_values_barplot.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved p-value barplot to: {output_file}")


if __name__ == '__main__':
    # Find most recent results
    base_dir = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis')
    results_root = base_dir / 'analysis' / 'phase2_SRM_across_between' / 'validation' / '1D_permutation' / 'results'

    results_dirs = sorted([d for d in results_root.iterdir() if d.is_dir()], reverse=True)

    if not results_dirs:
        raise FileNotFoundError(f"No permutation results found in {results_root}")

    results_dir = results_dirs[0]
    print(f"Visualizing results from: {results_dir}")

    visualize_permutation_results(results_dir)

    print("\n✅ Visualization completed!")
