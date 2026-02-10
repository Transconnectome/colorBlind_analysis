#!/usr/bin/env python3
"""
Visualize SRM vs Procrustes Comparison Results

Creates publication-ready figures from aggregated SRM evaluation results.

Usage:
    python visualize_srm_comparison.py --summary-dir results/srm_evaluation/TIMESTAMP/

Input:
    - summary_by_roi.json
    - optimal_k_recommendations.json
    - Individual result files (*_srm_results.json)

Output:
    visualizations/
    ├── srm_vs_procrustes_performance_by_roi.png
    ├── feature_tuning_curves_all_rois.png
    ├── improvement_distribution_by_roi.png
    ├── optimal_k_recommendations.png
    └── srm_winner_summary.png
"""

import sys
import argparse
import json
from pathlib import Path
from typing import Dict, List

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ============================================================================
# PLOTTING FUNCTIONS
# ============================================================================

def plot_performance_comparison(roi_summary: Dict, output_dir: Path):
    """
    Side-by-side comparison of Procrustes vs SRM performance.
    """
    rois = sorted(roi_summary.keys())
    n_rois = len(rois)

    # Extract data
    procrustes_rdm = [roi_summary[roi]['procrustes']['rdm_correlation_mean'] for roi in rois]
    procrustes_rdm_std = [roi_summary[roi]['procrustes']['rdm_correlation_std'] for roi in rois]
    srm_rdm = [roi_summary[roi]['srm']['rdm_correlation_mean'] for roi in rois]
    srm_rdm_std = [roi_summary[roi]['srm']['rdm_correlation_std'] for roi in rois]

    procrustes_acc = [roi_summary[roi]['procrustes']['decoding_accuracy_mean']*100 for roi in rois]
    procrustes_acc_std = [roi_summary[roi]['procrustes']['decoding_accuracy_std']*100 for roi in rois]
    srm_acc = [roi_summary[roi]['srm']['decoding_accuracy_mean']*100 for roi in rois]
    srm_acc_std = [roi_summary[roi]['srm']['decoding_accuracy_std']*100 for roi in rois]

    # Create figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    x = np.arange(n_rois)
    width = 0.35

    # RDM Correlation
    bars1 = ax1.bar(x - width/2, procrustes_rdm, width, yerr=procrustes_rdm_std,
                    label='Procrustes', color='steelblue', alpha=0.8, capsize=5)
    bars2 = ax1.bar(x + width/2, srm_rdm, width, yerr=srm_rdm_std,
                    label='SRM', color='coral', alpha=0.8, capsize=5)

    ax1.set_xlabel('ROI', fontsize=12, fontweight='bold')
    ax1.set_ylabel('RDM Correlation (Spearman r)', fontsize=12, fontweight='bold')
    ax1.set_title('RDM Reliability: Procrustes vs SRM', fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(rois, fontsize=11)
    ax1.legend(fontsize=11)
    ax1.grid(alpha=0.3, axis='y', linestyle=':')
    ax1.set_ylim(0, max(max(srm_rdm), max(procrustes_rdm)) * 1.2)

    # Add significance stars
    for i, roi in enumerate(rois):
        if roi_summary[roi]['statistical_test']['rdm_significant']:
            y_pos = max(procrustes_rdm[i], srm_rdm[i]) + max(procrustes_rdm_std[i], srm_rdm_std[i]) + 0.02
            ax1.text(i, y_pos, '*', ha='center', va='bottom', fontsize=16, fontweight='bold')

    # Decoding Accuracy
    bars3 = ax2.bar(x - width/2, procrustes_acc, width, yerr=procrustes_acc_std,
                    label='Procrustes', color='steelblue', alpha=0.8, capsize=5)
    bars4 = ax2.bar(x + width/2, srm_acc, width, yerr=srm_acc_std,
                    label='SRM', color='coral', alpha=0.8, capsize=5)

    ax2.set_xlabel('ROI', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Decoding Accuracy (%)', fontsize=12, fontweight='bold')
    ax2.set_title('8-Class Decoding: Procrustes vs SRM', fontsize=14, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(rois, fontsize=11)
    ax2.legend(fontsize=11)
    ax2.grid(alpha=0.3, axis='y', linestyle=':')
    ax2.axhline(12.5, color='red', linestyle='--', linewidth=1.5, alpha=0.5, label='Chance (12.5%)')

    # Add significance stars
    for i, roi in enumerate(rois):
        if roi_summary[roi]['statistical_test']['accuracy_significant']:
            y_pos = max(procrustes_acc[i], srm_acc[i]) + max(procrustes_acc_std[i], srm_acc_std[i]) + 2
            ax2.text(i, y_pos, '*', ha='center', va='bottom', fontsize=16, fontweight='bold')

    plt.tight_layout()

    output_file = output_dir / "srm_vs_procrustes_performance_by_roi.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"  Saved performance comparison to {output_file}")


def plot_feature_tuning_curves(results_dir: Path, output_dir: Path):
    """
    Feature tuning curves for all ROIs (k vs performance).
    """
    result_files = sorted(results_dir.glob("*_srm_results.json"))

    # Group by ROI
    by_roi = {}
    for file in result_files:
        with open(file, 'r') as f:
            data = json.load(f)

        roi = data['roi']
        if roi not in by_roi:
            by_roi[roi] = []

        # Extract k values and performance
        results_by_k = data['srm_tuning']['results_by_k']
        for k_str, metrics in results_by_k.items():
            if 'rdm_correlation_mean' in metrics and np.isfinite(metrics['rdm_correlation_mean']):
                by_roi[roi].append({
                    'k': int(k_str),
                    'rdm': metrics['rdm_correlation_mean'],
                    'subject': data['subject']
                })

    # Create figure
    rois = sorted(by_roi.keys())
    n_rois = len(rois)

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()

    for idx, roi in enumerate(rois):
        if idx >= len(axes):
            break

        ax = axes[idx]

        # Group by k
        k_values = sorted(set([d['k'] for d in by_roi[roi]]))
        k_means = []
        k_stds = []

        for k in k_values:
            rdms = [d['rdm'] for d in by_roi[roi] if d['k'] == k]
            k_means.append(np.mean(rdms))
            k_stds.append(np.std(rdms))

        # Plot mean with error bars
        ax.errorbar(k_values, k_means, yerr=k_stds, marker='o', markersize=8,
                   linewidth=2, capsize=5, color='steelblue', label='Mean ± SD')

        # Plot individual subjects (transparent)
        for subject in set([d['subject'] for d in by_roi[roi]]):
            subj_data = [d for d in by_roi[roi] if d['subject'] == subject]
            subj_k = [d['k'] for d in subj_data]
            subj_rdm = [d['rdm'] for d in subj_data]
            ax.plot(subj_k, subj_rdm, 'o-', alpha=0.2, linewidth=1, markersize=4)

        # Highlight optimal k
        best_k_idx = np.argmax(k_means)
        ax.scatter([k_values[best_k_idx]], [k_means[best_k_idx]],
                  s=300, marker='*', color='red', zorder=10,
                  label=f'Optimal k={k_values[best_k_idx]}')

        ax.set_xlabel('Number of Features (k)', fontsize=11, fontweight='bold')
        ax.set_ylabel('RDM Correlation', fontsize=11, fontweight='bold')
        ax.set_title(f'{roi} Feature Tuning', fontsize=12, fontweight='bold')
        ax.legend(fontsize=9)
        ax.grid(alpha=0.3, linestyle=':')

    # Remove unused subplots
    for idx in range(len(rois), len(axes)):
        fig.delaxes(axes[idx])

    plt.tight_layout()

    output_file = output_dir / "feature_tuning_curves_all_rois.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"  Saved feature tuning curves to {output_file}")


def plot_improvement_distribution(roi_summary: Dict, output_dir: Path):
    """
    Distribution of improvements across subjects for each ROI.
    """
    rois = sorted(roi_summary.keys())

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # RDM improvement
    improvement_data = []
    roi_labels = []

    for roi in rois:
        improvement_pct = roi_summary[roi]['improvement']['rdm_relative_pct']
        improvement_data.append(improvement_pct)
        roi_labels.append(roi)

    # Bar plot with colors based on threshold
    colors = ['green' if x > 5 else 'orange' if x > 2 else 'red' for x in improvement_data]

    bars = ax1.barh(roi_labels, improvement_data, color=colors, alpha=0.7)
    ax1.axvline(5, color='green', linestyle='--', linewidth=2, alpha=0.5, label='Threshold (5%)')
    ax1.axvline(0, color='black', linestyle='-', linewidth=1)

    ax1.set_xlabel('RDM Improvement (%)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('ROI', fontsize=12, fontweight='bold')
    ax1.set_title('SRM Improvement over Procrustes (RDM)', fontsize=14, fontweight='bold')
    ax1.legend(fontsize=10)
    ax1.grid(alpha=0.3, axis='x', linestyle=':')

    # Add value labels
    for i, (bar, val) in enumerate(zip(bars, improvement_data)):
        ax1.text(val + 0.5, i, f'{val:+.1f}%', va='center', fontsize=10, fontweight='bold')

    # Winner counts
    winner_data = {
        'SRM': [roi_summary[roi]['winner_counts']['SRM'] for roi in rois],
        'Procrustes': [roi_summary[roi]['winner_counts']['Procrustes'] for roi in rois]
    }

    x = np.arange(len(rois))
    width = 0.35

    bars1 = ax2.bar(x - width/2, winner_data['SRM'], width, label='SRM', color='coral', alpha=0.8)
    bars2 = ax2.bar(x + width/2, winner_data['Procrustes'], width, label='Procrustes', color='steelblue', alpha=0.8)

    ax2.set_xlabel('ROI', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Number of Subjects', fontsize=12, fontweight='bold')
    ax2.set_title('Winner Counts by ROI', fontsize=14, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(rois, fontsize=11)
    ax2.legend(fontsize=11)
    ax2.grid(alpha=0.3, axis='y', linestyle=':')

    plt.tight_layout()

    output_file = output_dir / "improvement_distribution_by_roi.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"  Saved improvement distribution to {output_file}")


def plot_optimal_k_recommendations(recommendations: Dict, roi_summary: Dict, output_dir: Path):
    """
    Optimal k recommendations with confidence intervals.
    """
    rois = sorted(recommendations.keys())

    optimal_k_means = [recommendations[roi]['optimal_k_mean'] for roi in rois]
    optimal_k_stds = [recommendations[roi]['optimal_k_std'] for roi in rois]
    recommended_k = [recommendations[roi]['recommended_k'] for roi in rois]
    improvements = [recommendations[roi]['rdm_improvement_pct'] for roi in rois]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))

    # Optimal k with error bars
    x = np.arange(len(rois))

    ax1.errorbar(x, optimal_k_means, yerr=optimal_k_stds, fmt='o',
                markersize=10, linewidth=2, capsize=5, color='steelblue',
                label='Optimal k (mean ± SD)')

    # Recommended k (rounded)
    ax1.scatter(x, recommended_k, s=300, marker='*', color='red',
               zorder=10, label='Recommended k')

    # Add k ranges
    for i, roi in enumerate(rois):
        k_range = recommendations[roi]['optimal_k_range']
        ax1.plot([i, i], k_range, 'k-', linewidth=2, alpha=0.3)

    ax1.set_xticks(x)
    ax1.set_xticklabels(rois, fontsize=11)
    ax1.set_ylabel('Number of Features (k)', fontsize=12, fontweight='bold')
    ax1.set_title('Optimal k Recommendations by ROI', fontsize=14, fontweight='bold')
    ax1.legend(fontsize=11)
    ax1.grid(alpha=0.3, axis='y', linestyle=':')

    # Improvement vs k
    sc = ax2.scatter(recommended_k, improvements, s=200, c=improvements,
                    cmap='RdYlGn', vmin=-5, vmax=15, edgecolors='black', linewidth=2)

    # Add ROI labels
    for i, roi in enumerate(rois):
        ax2.annotate(roi, (recommended_k[i], improvements[i]),
                    xytext=(5, 5), textcoords='offset points',
                    fontsize=10, fontweight='bold')

    # Threshold line
    ax2.axhline(5, color='green', linestyle='--', linewidth=2, alpha=0.5,
               label='Worthwhile threshold (5%)')
    ax2.axhline(0, color='black', linestyle='-', linewidth=1)

    ax2.set_xlabel('Recommended k', fontsize=12, fontweight='bold')
    ax2.set_ylabel('RDM Improvement (%)', fontsize=12, fontweight='bold')
    ax2.set_title('SRM Improvement vs Feature Count', fontsize=14, fontweight='bold')
    ax2.legend(fontsize=11)
    ax2.grid(alpha=0.3, linestyle=':')

    plt.colorbar(sc, ax=ax2, label='Improvement (%)')

    plt.tight_layout()

    output_file = output_dir / "optimal_k_recommendations.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"  Saved optimal k recommendations to {output_file}")


def plot_winner_summary(recommendations: Dict, roi_summary: Dict, output_dir: Path):
    """
    Overall summary of SRM vs Procrustes decision.
    """
    fig, ax = plt.subplots(figsize=(10, 8))

    rois = sorted(recommendations.keys())
    decisions = [recommendations[roi]['decision'] for roi in rois]
    improvements = [recommendations[roi]['rdm_improvement_pct'] for roi in rois]

    # Color code by decision
    colors = ['green' if 'SRM' in d else 'red' for d in decisions]

    y_pos = np.arange(len(rois))

    bars = ax.barh(y_pos, improvements, color=colors, alpha=0.7, edgecolor='black', linewidth=2)

    # Add threshold line
    ax.axvline(5, color='green', linestyle='--', linewidth=2, alpha=0.5,
              label='Worthwhile threshold (5%)')
    ax.axvline(0, color='black', linestyle='-', linewidth=1)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(rois, fontsize=12, fontweight='bold')
    ax.set_xlabel('RDM Improvement (%)', fontsize=12, fontweight='bold')
    ax.set_title('SRM vs Procrustes: Final Recommendations', fontsize=14, fontweight='bold')
    ax.grid(alpha=0.3, axis='x', linestyle=':')

    # Add decision labels
    for i, (bar, val, decision) in enumerate(zip(bars, improvements, decisions)):
        label = '✓ SRM' if 'SRM' in decision else '✗ Procrustes'
        ax.text(val + 0.5, i, f'{val:+.1f}% {label}',
               va='center', fontsize=10, fontweight='bold')

    # Legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='green', alpha=0.7, label='Use SRM (improvement > 5%)'),
        Patch(facecolor='red', alpha=0.7, label='Use Procrustes (improvement < 5%)')
    ]
    ax.legend(handles=legend_elements, fontsize=11, loc='lower right')

    plt.tight_layout()

    output_file = output_dir / "srm_winner_summary.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"  Saved winner summary to {output_file}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Visualize SRM comparison results')
    parser.add_argument('--summary-dir', type=str, required=True,
                       help='Directory containing summary JSON files')
    parser.add_argument('--output-dir', type=str,
                       help='Output directory for visualizations (default: summary-dir/visualizations)')

    args = parser.parse_args()

    summary_dir = Path(args.summary_dir)
    output_dir = Path(args.output_dir) if args.output_dir else summary_dir / "visualizations"

    if not summary_dir.exists():
        print(f"ERROR: Summary directory not found: {summary_dir}")
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*80}")
    print("Visualizing SRM Comparison Results")
    print(f"{'='*80}")
    print(f"Summary directory: {summary_dir}")
    print(f"Output directory: {output_dir}")

    # Load summary files
    print("\n[1/6] Loading summary files...")

    with open(summary_dir / "summary_by_roi.json", 'r') as f:
        roi_summary = json.load(f)

    with open(summary_dir / "optimal_k_recommendations.json", 'r') as f:
        recommendations = json.load(f)

    print(f"  Loaded summaries for {len(roi_summary)} ROIs")

    # Generate plots
    print("\n[2/6] Creating performance comparison plot...")
    plot_performance_comparison(roi_summary, output_dir)

    print("\n[3/6] Creating feature tuning curves...")
    plot_feature_tuning_curves(summary_dir, output_dir)

    print("\n[4/6] Creating improvement distribution plot...")
    plot_improvement_distribution(roi_summary, output_dir)

    print("\n[5/6] Creating optimal k recommendations plot...")
    plot_optimal_k_recommendations(recommendations, roi_summary, output_dir)

    print("\n[6/6] Creating winner summary plot...")
    plot_winner_summary(recommendations, roi_summary, output_dir)

    print(f"\n{'='*80}")
    print(f"Visualization completed. Figures saved to {output_dir}")
    print(f"{'='*80}")


if __name__ == '__main__':
    main()
