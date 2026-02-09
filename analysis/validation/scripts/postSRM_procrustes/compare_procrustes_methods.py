#!/usr/bin/env python3
"""
Compare Procrustes-PCA vs Procrustes-ANOVA

Compares geometric metrics between PCA and ANOVA dimension reduction methods.

Usage:
    python compare_procrustes_methods.py --roi V1
"""

import argparse
import json
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from scipy.stats import ttest_ind, pearsonr


def load_metrics(metrics_dir, roi):
    """Load geometric metrics from step4 results."""
    metrics_file = metrics_dir / roi / "geometric_metrics.json"
    stats_file = metrics_dir / roi / "hc_vs_cvd_statistics.json"

    if not metrics_file.exists():
        print(f"WARNING: Metrics file not found: {metrics_file}")
        return None, None

    with open(metrics_file) as f:
        metrics = json.load(f)

    stats = None
    if stats_file.exists():
        with open(stats_file) as f:
            stats = json.load(f)

    return metrics, stats


def plot_method_comparison(pca_metrics, anova_metrics, pca_stats, anova_stats, roi, output_dir):
    """
    Create comparison plots between PCA and ANOVA methods.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Prepare data for plotting
    metric_names = ['isc', 'deviation', 'circularity', 'reliability']
    metric_labels = ['ISC', 'Deviation from HC', 'Circularity', 'RDM Reliability']

    # Extract HC and CVD values
    hc_subjects = ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05', 'sub-06']
    cvd_subjects = ['sub-08', 'sub-09', 'sub-10']

    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    axes = axes.flatten()

    for idx, (metric, label) in enumerate(zip(metric_names, metric_labels)):
        ax = axes[idx]

        # Extract values
        pca_hc = [pca_metrics[s][metric] for s in hc_subjects if s in pca_metrics and metric in pca_metrics[s]]
        pca_cvd = [pca_metrics[s][metric] for s in cvd_subjects if s in pca_metrics and metric in pca_metrics[s]]

        anova_hc = [anova_metrics[s][metric] for s in hc_subjects if s in anova_metrics and metric in anova_metrics[s]]
        anova_cvd = [anova_metrics[s][metric] for s in cvd_subjects if s in anova_metrics and metric in anova_metrics[s]]

        # Box plots
        positions = [1, 2, 4, 5]
        data = [pca_hc, pca_cvd, anova_hc, anova_cvd]
        labels_box = ['PCA\nHC', 'PCA\nCVD', 'ANOVA\nHC', 'ANOVA\nCVD']

        bp = ax.boxplot(data, positions=positions, widths=0.6, patch_artist=True,
                        labels=labels_box)

        # Color boxes
        colors = ['#3498db', '#e74c3c', '#3498db', '#e74c3c']
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.6)

        # Add individual points
        for i, (d, pos) in enumerate(zip(data, positions)):
            x = np.random.normal(pos, 0.04, size=len(d))
            ax.scatter(x, d, alpha=0.8, s=50, c='black', zorder=3)

        ax.set_ylabel(label, fontsize=12)
        ax.set_title(f'{label} - {roi}', fontsize=14, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)

        # Add horizontal line between methods
        ax.axvline(3, color='gray', linestyle='--', alpha=0.5)

    plt.tight_layout()
    plt.savefig(output_dir / f"{roi}_method_comparison_boxplots.png", dpi=300, bbox_inches='tight')
    plt.close()

    print(f"  ✓ Saved: {roi}_method_comparison_boxplots.png")

    # Scatter plot: Per-subject correlation
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    axes = axes.flatten()

    all_subjects = hc_subjects + cvd_subjects

    for idx, (metric, label) in enumerate(zip(metric_names, metric_labels)):
        ax = axes[idx]

        pca_values = [pca_metrics[s][metric] for s in all_subjects if s in pca_metrics and metric in pca_metrics[s]]
        anova_values = [anova_metrics[s][metric] for s in all_subjects if s in anova_metrics and metric in anova_metrics[s]]

        if len(pca_values) != len(anova_values):
            print(f"  WARNING: Mismatched subject counts for {metric}")
            continue

        # Scatter plot
        ax.scatter(pca_values, anova_values, s=100, alpha=0.7, c=['blue']*len(hc_subjects) + ['red']*len(cvd_subjects))

        # Diagonal line
        all_vals = pca_values + anova_values
        min_val, max_val = min(all_vals), max(all_vals)
        ax.plot([min_val, max_val], [min_val, max_val], 'k--', alpha=0.5, label='Identity')

        # Correlation
        if len(pca_values) > 2:
            r, p = pearsonr(pca_values, anova_values)
            ax.text(0.05, 0.95, f'r = {r:.3f}, p = {p:.3f}',
                   transform=ax.transAxes, fontsize=11,
                   verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        ax.set_xlabel(f'PCA {label}', fontsize=12)
        ax.set_ylabel(f'ANOVA {label}', fontsize=12)
        ax.set_title(f'{label} Correlation - {roi}', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_dir / f"{roi}_method_correlation_scatter.png", dpi=300, bbox_inches='tight')
    plt.close()

    print(f"  ✓ Saved: {roi}_method_correlation_scatter.png")


def compute_comparison_statistics(pca_metrics, anova_metrics, pca_stats, anova_stats, roi):
    """
    Compute statistical comparisons between PCA and ANOVA methods.
    """
    hc_subjects = ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05', 'sub-06']
    cvd_subjects = ['sub-08', 'sub-09', 'sub-10']

    comparison = {
        'roi': roi,
        'pca_vs_anova': {},
        'hc_cvd_effect_comparison': {}
    }

    # Compare HC group metrics between methods
    metric_names = ['isc', 'deviation', 'circularity', 'reliability']

    for metric in metric_names:
        pca_hc = [pca_metrics[s][metric] for s in hc_subjects if s in pca_metrics and metric in pca_metrics[s]]
        anova_hc = [anova_metrics[s][metric] for s in hc_subjects if s in anova_metrics and metric in anova_metrics[s]]

        if len(pca_hc) > 0 and len(anova_hc) > 0:
            # Paired t-test (same subjects)
            if len(pca_hc) == len(anova_hc):
                from scipy.stats import ttest_rel
                t_stat, p_val = ttest_rel(pca_hc, anova_hc)
            else:
                t_stat, p_val = ttest_ind(pca_hc, anova_hc)

            comparison['pca_vs_anova'][f'hc_{metric}'] = {
                'pca_mean': float(np.mean(pca_hc)),
                'anova_mean': float(np.mean(anova_hc)),
                'difference': float(np.mean(pca_hc) - np.mean(anova_hc)),
                't_statistic': float(t_stat),
                'p_value': float(p_val),
                'significant': p_val < 0.05
            }

    # Compare HC-CVD effect sizes
    if pca_stats and anova_stats:
        for metric in metric_names:
            if metric in pca_stats and metric in anova_stats:
                pca_effect = pca_stats[metric].get('cohens_d', np.nan)
                anova_effect = anova_stats[metric].get('cohens_d', np.nan)

                comparison['hc_cvd_effect_comparison'][metric] = {
                    'pca_effect_size': pca_effect,
                    'anova_effect_size': anova_effect,
                    'difference': pca_effect - anova_effect if not np.isnan(pca_effect) and not np.isnan(anova_effect) else np.nan
                }

    return comparison


def main():
    parser = argparse.ArgumentParser(description='Compare Procrustes-PCA vs Procrustes-ANOVA')
    parser.add_argument('--roi', type=str, required=True, help='ROI name (V1, V2, V3, hV4)')
    parser.add_argument('--pca-dir', type=str,
                        default='results/step4_metrics_pca_optimal',
                        help='PCA metrics directory')
    parser.add_argument('--anova-dir', type=str,
                        default='results/step4_metrics_anova_optimal',
                        help='ANOVA metrics directory')
    parser.add_argument('--output-dir', type=str,
                        default='results/method_comparison',
                        help='Output directory')

    args = parser.parse_args()

    pca_dir = Path(args.pca_dir)
    anova_dir = Path(args.anova_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    roi = args.roi

    print(f"\n=== Compare PCA vs ANOVA: {roi} ===")

    # Load metrics
    print("Loading metrics...")
    pca_metrics, pca_stats = load_metrics(pca_dir, roi)
    anova_metrics, anova_stats = load_metrics(anova_dir, roi)

    if pca_metrics is None or anova_metrics is None:
        print("ERROR: Failed to load metrics")
        return

    print(f"  ✓ PCA metrics: {len(pca_metrics)} subjects")
    print(f"  ✓ ANOVA metrics: {len(anova_metrics)} subjects")

    # Compute comparison statistics
    print("\nComputing comparison statistics...")
    comparison = compute_comparison_statistics(pca_metrics, anova_metrics, pca_stats, anova_stats, roi)

    # Save comparison
    comparison_file = output_dir / f"{roi}_pca_vs_anova_comparison.json"
    with open(comparison_file, 'w') as f:
        json.dump(comparison, f, indent=2)

    print(f"  ✓ Saved: {comparison_file}")

    # Create visualizations
    print("\nCreating visualizations...")
    plot_method_comparison(pca_metrics, anova_metrics, pca_stats, anova_stats, roi, output_dir)

    # Summary
    print("\n=== Comparison Summary ===")
    print(f"ROI: {roi}")
    print("\nPCA vs ANOVA (HC group):")

    for metric_key, stats in comparison['pca_vs_anova'].items():
        print(f"\n  {metric_key}:")
        print(f"    PCA mean:   {stats['pca_mean']:.4f}")
        print(f"    ANOVA mean: {stats['anova_mean']:.4f}")
        print(f"    Difference: {stats['difference']:.4f}")
        print(f"    p-value:    {stats['p_value']:.4f} {'***' if stats['significant'] else 'n.s.'}")

    print("\nHC-CVD Effect Size Comparison:")
    for metric, effects in comparison['hc_cvd_effect_comparison'].items():
        print(f"\n  {metric}:")
        print(f"    PCA effect size:   {effects['pca_effect_size']:.4f}")
        print(f"    ANOVA effect size: {effects['anova_effect_size']:.4f}")
        print(f"    Difference:        {effects['difference']:.4f}")

    print(f"\n✓ Comparison complete for {roi}")


if __name__ == '__main__':
    main()
