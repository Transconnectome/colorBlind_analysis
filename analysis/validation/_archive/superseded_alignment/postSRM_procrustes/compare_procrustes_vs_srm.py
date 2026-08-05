#!/usr/bin/env python3
"""
Compare Procrustes-PCA vs SRM Results

Direct comparison of geometric metrics between two methods:
- ISC (Inter-Subject Correlation)
- Deviation from HC norm
- Circularity
- Split-half reliability
- MDS stress

Usage:
    python compare_procrustes_vs_srm.py --roi V1
"""

import argparse
import json
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import sys


def load_metrics(procrustes_dir, srm_dir, roi):
    """
    Load metrics from both methods.

    Returns:
        dict with keys 'procrustes' and 'srm', each containing:
            - metrics: per-subject metrics
            - statistics: HC vs CVD statistics
    """
    results = {}

    # Procrustes
    procrustes_metrics_path = procrustes_dir / roi / "geometric_metrics.json"
    procrustes_stats_path = procrustes_dir / roi / "hc_vs_cvd_statistics.json"

    if procrustes_metrics_path.exists() and procrustes_stats_path.exists():
        with open(procrustes_metrics_path, 'r') as f:
            procrustes_metrics = json.load(f)
        with open(procrustes_stats_path, 'r') as f:
            procrustes_stats = json.load(f)

        results['procrustes'] = {
            'metrics': procrustes_metrics,
            'statistics': procrustes_stats,
        }
        print(f"✓ Loaded Procrustes metrics: {len(procrustes_metrics)} subjects")
    else:
        print(f"✗ Procrustes metrics not found for {roi}")
        results['procrustes'] = None

    # SRM
    srm_metrics_path = srm_dir / roi / "geometric_metrics_srm.json"
    srm_stats_path = srm_dir / roi / "hc_vs_cvd_statistics_srm.json"

    if srm_metrics_path.exists() and srm_stats_path.exists():
        with open(srm_metrics_path, 'r') as f:
            srm_metrics = json.load(f)
        with open(srm_stats_path, 'r') as f:
            srm_stats = json.load(f)

        results['srm'] = {
            'metrics': srm_metrics,
            'statistics': srm_stats,
        }
        print(f"✓ Loaded SRM metrics: {len(srm_metrics)} subjects")
    else:
        print(f"✗ SRM metrics not found for {roi}")
        results['srm'] = None

    return results


def plot_method_comparison(results, roi, output_dir):
    """
    Create comparison plots: Procrustes-PCA vs SRM.

    Generates:
    1. Bar plot: HC vs CVD for each metric (side-by-side methods)
    2. Scatter plot: Per-subject correlation between methods
    3. Reliability comparison
    """
    if results['procrustes'] is None or results['srm'] is None:
        print("WARNING: Missing data for comparison")
        return

    # Extract data
    proc_stats = results['procrustes']['statistics']
    srm_stats = results['srm']['statistics']

    proc_metrics = results['procrustes']['metrics']
    srm_metrics = results['srm']['metrics']

    # Metrics to compare
    metric_names = ['isc', 'deviation', 'circularity']
    metric_labels = ['ISC', 'Deviation from HC', 'Circularity']

    # Figure 1: Bar plot comparison (HC vs CVD, Procrustes vs SRM)
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    for ax, metric, label in zip(axes, metric_names, metric_labels):
        if metric not in proc_stats or metric not in srm_stats:
            ax.text(0.5, 0.5, 'Data not available', ha='center', va='center')
            ax.set_title(label)
            continue

        proc_s = proc_stats[metric]
        srm_s = srm_stats[metric]

        # Bar positions
        x = np.arange(2)  # HC, CVD
        width = 0.35

        # HC bars
        hc_means = [proc_s['hc_mean'], srm_s['hc_mean']]
        hc_stds = [proc_s['hc_std'], srm_s['hc_std']]

        # CVD bars
        cvd_means = [proc_s['cvd_mean'], srm_s['cvd_mean']]
        cvd_stds = [proc_s['cvd_std'], srm_s['cvd_std']]

        # Plot
        ax.bar(x - width/2, [hc_means[0], cvd_means[0]], width,
               yerr=[hc_stds[0], cvd_stds[0]], capsize=5,
               label='Procrustes-PCA', color='steelblue', alpha=0.8, edgecolor='black')

        ax.bar(x + width/2, [hc_means[1], cvd_means[1]], width,
               yerr=[hc_stds[1], cvd_stds[1]], capsize=5,
               label='SRM', color='coral', alpha=0.8, edgecolor='black')

        ax.set_ylabel(label, fontsize=12)
        ax.set_xticks(x)
        ax.set_xticklabels(['HC', 'CVD'], fontsize=11)
        ax.set_title(f'{label}\n(Procrustes p={proc_s["p_value"]:.4f}, SRM p={srm_s["p_value"]:.4f})',
                     fontsize=12, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(axis='y', alpha=0.3)

        # Add significance stars
        if proc_s['significant']:
            y_max = max(hc_means[0] + hc_stds[0], cvd_means[0] + cvd_stds[0])
            ax.text(0, y_max * 1.1, '*', ha='center', fontsize=20, color='steelblue')

        if srm_s['significant']:
            y_max = max(hc_means[1] + hc_stds[1], cvd_means[1] + cvd_stds[1])
            ax.text(1, y_max * 1.1, '*', ha='center', fontsize=20, color='coral')

    plt.suptitle(f'{roi} - Method Comparison: Procrustes-PCA vs SRM', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()

    output_path = output_dir / f"{roi}_method_comparison_barplot.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"✓ Saved: {output_path}")

    # Figure 2: Per-subject correlation (scatter plots)
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    # Get common subjects
    common_subjects = set(proc_metrics.keys()) & set(srm_metrics.keys())
    hc_subjects = [s for s in common_subjects if proc_metrics[s]['group'] == 'HC']
    cvd_subjects = [s for s in common_subjects if proc_metrics[s]['group'] == 'CVD']

    for ax, metric, label in zip(axes, metric_names, metric_labels):
        # Extract values for common subjects
        proc_values = [proc_metrics[s][metric] for s in common_subjects
                       if not np.isnan(proc_metrics[s][metric])]
        srm_values = [srm_metrics[s][metric] for s in common_subjects
                      if not np.isnan(srm_metrics[s][metric])]

        if len(proc_values) == 0 or len(srm_values) == 0:
            ax.text(0.5, 0.5, 'Data not available', ha='center', va='center')
            ax.set_title(label)
            continue

        # HC points
        proc_hc = [proc_metrics[s][metric] for s in hc_subjects]
        srm_hc = [srm_metrics[s][metric] for s in hc_subjects]

        # CVD points
        proc_cvd = [proc_metrics[s][metric] for s in cvd_subjects]
        srm_cvd = [srm_metrics[s][metric] for s in cvd_subjects]

        # Scatter
        ax.scatter(proc_hc, srm_hc, c='blue', s=100, alpha=0.7, edgecolors='black',
                   linewidths=1.5, label='HC')
        ax.scatter(proc_cvd, srm_cvd, c='red', s=100, alpha=0.7, edgecolors='black',
                   linewidths=1.5, label='CVD')

        # Diagonal line
        all_vals = proc_values + srm_values
        min_val, max_val = min(all_vals), max(all_vals)
        ax.plot([min_val, max_val], [min_val, max_val], 'k--', linewidth=1, alpha=0.5)

        # Correlation
        from scipy.stats import pearsonr
        if len(proc_values) > 2 and len(srm_values) > 2:
            r, p = pearsonr(proc_values, srm_values)
            ax.text(0.05, 0.95, f'r={r:.3f}, p={p:.4f}',
                    transform=ax.transAxes, fontsize=10, va='top',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        ax.set_xlabel(f'{label} (Procrustes-PCA)', fontsize=11)
        ax.set_ylabel(f'{label} (SRM)', fontsize=11)
        ax.set_title(f'{label} - Subject Correlation', fontsize=12, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)

    plt.suptitle(f'{roi} - Per-Subject Correlation: Procrustes vs SRM', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()

    output_path = output_dir / f"{roi}_method_correlation_scatter.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"✓ Saved: {output_path}")

    # Figure 3: Reliability comparison
    if 'reliability' in srm_stats:
        fig, ax = plt.subplots(1, 1, figsize=(8, 6))

        proc_rel = [proc_metrics[s]['isc'] for s in common_subjects]  # Using ISC as proxy for Procrustes
        srm_rel = [srm_metrics[s]['split_half_reliability'] for s in common_subjects]

        x = np.arange(2)
        width = 0.35

        hc_rel_proc = [proc_metrics[s]['isc'] for s in hc_subjects]
        hc_rel_srm = [srm_metrics[s]['split_half_reliability'] for s in hc_subjects]

        cvd_rel_proc = [proc_metrics[s]['isc'] for s in cvd_subjects]
        cvd_rel_srm = [srm_metrics[s]['split_half_reliability'] for s in cvd_subjects]

        proc_hc_mean, proc_hc_std = np.mean(hc_rel_proc), np.std(hc_rel_proc)
        proc_cvd_mean, proc_cvd_std = np.mean(cvd_rel_proc), np.std(cvd_rel_proc)

        srm_hc_mean, srm_hc_std = np.mean(hc_rel_srm), np.std(hc_rel_srm)
        srm_cvd_mean, srm_cvd_std = np.mean(cvd_rel_srm), np.std(cvd_rel_srm)

        ax.bar(x - width/2, [proc_hc_mean, proc_cvd_mean], width,
               yerr=[proc_hc_std, proc_cvd_std], capsize=5,
               label='Procrustes-PCA', color='steelblue', alpha=0.8, edgecolor='black')

        ax.bar(x + width/2, [srm_hc_mean, srm_cvd_mean], width,
               yerr=[srm_hc_std, srm_cvd_std], capsize=5,
               label='SRM', color='coral', alpha=0.8, edgecolor='black')

        ax.set_ylabel('Split-Half Reliability', fontsize=12)
        ax.set_xticks(x)
        ax.set_xticklabels(['HC', 'CVD'], fontsize=11)
        ax.set_title(f'{roi} - Reliability Comparison', fontsize=13, fontweight='bold')
        ax.legend(fontsize=11)
        ax.grid(axis='y', alpha=0.3)
        ax.axhline(0.5, color='green', linestyle='--', linewidth=1.5, alpha=0.7, label='Good threshold')

        plt.tight_layout()

        output_path = output_dir / f"{roi}_reliability_comparison.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"✓ Saved: {output_path}")


def print_summary_table(results, roi):
    """
    Print summary table comparing methods.
    """
    if results['procrustes'] is None or results['srm'] is None:
        print("WARNING: Missing data for summary")
        return

    proc_stats = results['procrustes']['statistics']
    srm_stats = results['srm']['statistics']

    print(f"\n{'='*80}")
    print(f"SUMMARY TABLE: {roi} - Procrustes-PCA vs SRM")
    print(f"{'='*80}")

    print(f"\n{'Metric':<20} {'Group':<8} {'Procrustes-PCA':<20} {'SRM':<20} {'Winner':<10}")
    print(f"{'-'*80}")

    metrics = ['isc', 'deviation', 'circularity']
    metric_labels = ['ISC', 'Deviation', 'Circularity']

    for metric, label in zip(metrics, metric_labels):
        if metric not in proc_stats or metric not in srm_stats:
            continue

        proc = proc_stats[metric]
        srm = srm_stats[metric]

        # HC
        proc_hc = f"{proc['hc_mean']:.3f} ± {proc['hc_std']:.3f}"
        srm_hc = f"{srm['hc_mean']:.3f} ± {srm['hc_std']:.3f}"

        # Determine winner (for ISC: higher is better, for deviation: lower is better)
        if metric == 'isc' or metric == 'circularity':
            winner_hc = 'Procrustes' if proc['hc_mean'] > srm['hc_mean'] else 'SRM'
        else:
            winner_hc = 'Procrustes' if proc['hc_mean'] < srm['hc_mean'] else 'SRM'

        print(f"{label:<20} {'HC':<8} {proc_hc:<20} {srm_hc:<20} {winner_hc:<10}")

        # CVD
        proc_cvd = f"{proc['cvd_mean']:.3f} ± {proc['cvd_std']:.3f}"
        srm_cvd = f"{srm['cvd_mean']:.3f} ± {srm['cvd_std']:.3f}"

        if metric == 'isc' or metric == 'circularity':
            winner_cvd = 'Procrustes' if proc['cvd_mean'] > srm['cvd_mean'] else 'SRM'
        else:
            winner_cvd = 'Procrustes' if proc['cvd_mean'] < srm['cvd_mean'] else 'SRM'

        print(f"{'':<20} {'CVD':<8} {proc_cvd:<20} {srm_cvd:<20} {winner_cvd:<10}")

        # Significance
        proc_sig = '✓' if proc['significant'] else '✗'
        srm_sig = '✓' if srm['significant'] else '✗'

        print(f"{'':<20} {'p-value':<8} {proc['p_value']:.4f} ({proc_sig})"
              f"{'':>8} {srm['p_value']:.4f} ({srm_sig}){'':>8}")

        print(f"{'':<20} {'Cohen d':<8} {proc['cohens_d']:.3f}"
              f"{'':>12} {srm['cohens_d']:.3f}{'':>12}")

        print(f"{'-'*80}")

    # Reliability comparison
    if 'reliability' in srm_stats:
        srm_rel = srm_stats['reliability']
        print(f"\n{'Reliability':<20} {'HC':<8} {'N/A':<20} "
              f"{srm_rel['hc_mean']:.3f} ± {srm_rel['hc_std']:.3f}{'':>10}")
        print(f"{'':<20} {'CVD':<8} {'N/A':<20} "
              f"{srm_rel['cvd_mean']:.3f} ± {srm_rel['cvd_std']:.3f}{'':>10}")

    print(f"{'='*80}\n")


def main():
    parser = argparse.ArgumentParser(description='Compare Procrustes-PCA vs SRM')
    parser.add_argument('--roi', type=str, required=True, help='ROI name (V1, V2, V3, hV4)')
    parser.add_argument('--procrustes-dir', type=str,
                        default=str(Path(__file__).parent / 'results' / 'step4_metrics'),
                        help='Procrustes metrics directory')
    parser.add_argument('--srm-dir', type=str,
                        default=str(Path(__file__).parent / 'results' / 'srm_metrics'),
                        help='SRM metrics directory')
    parser.add_argument('--output-dir', type=str,
                        default=str(Path(__file__).parent / 'results' / 'comparison'),
                        help='Output directory')

    args = parser.parse_args()

    # Paths
    procrustes_dir = Path(args.procrustes_dir)
    srm_dir = Path(args.srm_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    roi = args.roi

    print(f"\n=== Compare Procrustes-PCA vs SRM ===")
    print(f"ROI: {roi}")

    # Load metrics
    print(f"\n=== Loading Metrics ===")
    results = load_metrics(procrustes_dir, srm_dir, roi)

    # Print summary table
    print_summary_table(results, roi)

    # Generate comparison plots
    print(f"\n=== Generating Comparison Plots ===")
    plot_method_comparison(results, roi, output_dir)

    print(f"\n✓ Comparison complete for {roi}")
    print(f"  Outputs: {output_dir}/{roi}_*.png")


if __name__ == '__main__':
    main()
