#!/usr/bin/env python3
"""
Step 5: Visualization & Reporting

Generates comprehensive visualizations:
- PCA diagnostic plots (PC1-PC2 color wheel, scree plots)
- RDM heatmaps (HC vs CVD)
- MDS embeddings
- Geometric metrics comparison
- Procrustes convergence

Usage:
    python step5_visualize_report.py --roi V1 --method pca
"""

import argparse
import json
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))
from utils.rdm_visualization import plot_rdm_matrices, plot_color_embedding_mds


def plot_pca_diagnostics(roi, input_dir, output_dir, subjects):
    """
    Plot PCA diagnostic plots:
    - PC1 vs PC2 scatter (color wheel structure)
    - Scree plot (explained variance per component)
    - Cumulative variance
    """
    print(f"\n=== Generating PCA Diagnostic Plots ===")

    # Color mapping (8 colors)
    color_names = ['Red', 'Orange', 'Yellow', 'Green', 'Cyan', 'Blue', 'Purple', 'Magenta']
    color_values = ['#FF0000', '#FF8000', '#FFFF00', '#00FF00', '#00FFFF', '#0000FF', '#8000FF', '#FF00FF']

    fig, axes = plt.subplots(2, 2, figsize=(14, 12))

    # 1. PC1-PC2 for HC average
    ax = axes[0, 0]
    hc_subjects = ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05', 'sub-06']
    hc_pc_all = []

    for subj_id in hc_subjects:
        odd_pc_path = input_dir / roi / f"{subj_id}_odd_pc.npy"
        if odd_pc_path.exists():
            odd_pc = np.load(odd_pc_path)  # (8, n_components)
            hc_pc_all.append(odd_pc)

    if hc_pc_all:
        hc_pc_mean = np.mean(hc_pc_all, axis=0)  # (8, n_components)
        pc1 = hc_pc_mean[:, 0]
        pc2 = hc_pc_mean[:, 1]

        for i, (name, color) in enumerate(zip(color_names, color_values)):
            ax.scatter(pc1[i], pc2[i], c=color, s=200, edgecolors='black', linewidths=2, label=name)

        ax.set_xlabel('PC1', fontsize=12)
        ax.set_ylabel('PC2', fontsize=12)
        ax.set_title(f'{roi} - HC Average: PC1 vs PC2\n(Expected: Circular Color Wheel)', fontsize=13, fontweight='bold')
        ax.legend(fontsize=9, loc='best')
        ax.grid(True, alpha=0.3)
        ax.axhline(0, color='k', linewidth=0.5)
        ax.axvline(0, color='k', linewidth=0.5)

    # 2. PC1-PC2 for CVD average
    ax = axes[0, 1]
    cvd_subjects = ['sub-08', 'sub-09', 'sub-10']
    cvd_pc_all = []

    for subj_id in cvd_subjects:
        odd_pc_path = input_dir / roi / f"{subj_id}_odd_pc.npy"
        if odd_pc_path.exists():
            odd_pc = np.load(odd_pc_path)
            cvd_pc_all.append(odd_pc)

    if cvd_pc_all:
        cvd_pc_mean = np.mean(cvd_pc_all, axis=0)  # (8, n_components)
        pc1 = cvd_pc_mean[:, 0]
        pc2 = cvd_pc_mean[:, 1]

        for i, (name, color) in enumerate(zip(color_names, color_values)):
            ax.scatter(pc1[i], pc2[i], c=color, s=200, edgecolors='black', linewidths=2, label=name)

        ax.set_xlabel('PC1', fontsize=12)
        ax.set_ylabel('PC2', fontsize=12)
        ax.set_title(f'{roi} - CVD Average: PC1 vs PC2\n(Check for Distortions)', fontsize=13, fontweight='bold')
        ax.legend(fontsize=9, loc='best')
        ax.grid(True, alpha=0.3)
        ax.axhline(0, color='k', linewidth=0.5)
        ax.axvline(0, color='k', linewidth=0.5)

    # 3. Scree plot (first subject as example)
    ax = axes[1, 0]
    example_subj = subjects[0] if subjects else 'sub-01'
    explained_var_path = input_dir / roi / f"{example_subj}_explained_variance.npy"

    if explained_var_path.exists():
        explained_var = np.load(explained_var_path)
        n_components = len(explained_var)

        ax.plot(range(1, n_components + 1), explained_var, 'o-', linewidth=2, markersize=6)
        ax.set_xlabel('Principal Component', fontsize=12)
        ax.set_ylabel('Explained Variance Ratio', fontsize=12)
        ax.set_title(f'{roi} - Scree Plot ({example_subj})', fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3)

        # Highlight first 10 PCs
        if n_components >= 10:
            ax.axvline(10, color='r', linestyle='--', linewidth=1.5, label='First 10 PCs')
            ax.legend(fontsize=10)

    # 4. Cumulative variance
    ax = axes[1, 1]
    if explained_var_path.exists():
        cumulative_var = np.cumsum(explained_var)

        ax.plot(range(1, n_components + 1), cumulative_var, 'o-', linewidth=2, markersize=6, color='green')
        ax.axhline(0.8, color='r', linestyle='--', linewidth=1.5, label='80% Threshold')
        ax.set_xlabel('Number of Components', fontsize=12)
        ax.set_ylabel('Cumulative Explained Variance', fontsize=12)
        ax.set_title(f'{roi} - Cumulative Variance ({example_subj})', fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=10)

    plt.tight_layout()

    output_path = output_dir / f"{roi}_pca_diagnostics.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"  ✓ Saved: {output_path}")


def plot_rdm_heatmaps(roi, rdms_dir, metrics_dir, output_dir, hc_subjects, cvd_subjects):
    """
    Plot RDM heatmaps: HC mean vs CVD mean, and difference map.
    """
    print(f"\n=== Generating RDM Heatmaps ===")

    # Load HC and CVD RDMs
    hc_rdms = []
    cvd_rdms = []

    for subj_id in hc_subjects:
        rdm_path = rdms_dir / roi / f"{subj_id}_rdm_crossnobis.npy"
        if rdm_path.exists():
            hc_rdms.append(np.load(rdm_path))

    for subj_id in cvd_subjects:
        rdm_path = rdms_dir / roi / f"{subj_id}_rdm_crossnobis.npy"
        if rdm_path.exists():
            cvd_rdms.append(np.load(rdm_path))

    if not hc_rdms or not cvd_rdms:
        print("  WARNING: Missing RDMs, skipping heatmap")
        return

    rdm_hc_mean = np.mean(hc_rdms, axis=0)
    rdm_cvd_mean = np.mean(cvd_rdms, axis=0)
    rdm_diff = rdm_cvd_mean - rdm_hc_mean

    # Plot
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    color_labels = ['R', 'O', 'Y', 'G', 'C', 'B', 'P', 'M']

    # HC mean
    sns.heatmap(rdm_hc_mean, annot=True, fmt='.2f', cmap='viridis', cbar_kws={'label': 'Dissimilarity'},
                xticklabels=color_labels, yticklabels=color_labels, ax=axes[0])
    axes[0].set_title(f'{roi} - HC Mean RDM (n={len(hc_rdms)})', fontsize=13, fontweight='bold')

    # CVD mean
    sns.heatmap(rdm_cvd_mean, annot=True, fmt='.2f', cmap='viridis', cbar_kws={'label': 'Dissimilarity'},
                xticklabels=color_labels, yticklabels=color_labels, ax=axes[1])
    axes[1].set_title(f'{roi} - CVD Mean RDM (n={len(cvd_rdms)})', fontsize=13, fontweight='bold')

    # Difference
    sns.heatmap(rdm_diff, annot=True, fmt='.2f', cmap='RdBu_r', center=0, cbar_kws={'label': 'Difference (CVD - HC)'},
                xticklabels=color_labels, yticklabels=color_labels, ax=axes[2])
    axes[2].set_title(f'{roi} - Difference (CVD - HC)', fontsize=13, fontweight='bold')

    plt.tight_layout()

    output_path = output_dir / f"{roi}_rdm_heatmaps.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"  ✓ Saved: {output_path}")


def plot_geometric_metrics_comparison(roi, metrics_path, output_dir):
    """
    Plot bar charts comparing HC vs CVD on geometric metrics.
    """
    print(f"\n=== Generating Geometric Metrics Comparison ===")

    # Load statistics
    with open(metrics_path, 'r') as f:
        stats = json.load(f)

    metrics = ['isc', 'deviation', 'circularity', 'mds_stress']
    metric_labels = ['ISC', 'Deviation from HC', 'Circularity', 'MDS Stress']

    fig, axes = plt.subplots(1, 4, figsize=(18, 4))

    for ax, metric, label in zip(axes, metrics, metric_labels):
        if metric not in stats:
            ax.text(0.5, 0.5, 'Data not available', ha='center', va='center')
            ax.set_title(label)
            continue

        s = stats[metric]

        # Bar plot
        x = [0, 1]
        means = [s['hc_mean'], s['cvd_mean']]
        stds = [s['hc_std'], s['cvd_std']]

        ax.bar(x, means, yerr=stds, capsize=5, color=['blue', 'red'], alpha=0.7, edgecolor='black', linewidth=1.5)
        ax.set_xticks(x)
        ax.set_xticklabels(['HC', 'CVD'], fontsize=11)
        ax.set_ylabel(label, fontsize=11)

        # Add significance
        if s['significant']:
            max_y = max(means) + max(stds) * 1.2
            ax.plot([0, 1], [max_y, max_y], 'k-', linewidth=1.5)
            ax.text(0.5, max_y * 1.05, f"p={s['p_value']:.4f}", ha='center', fontsize=10, fontweight='bold')

        ax.set_title(f"{label}\n(d={s['cohens_d']:.2f})", fontsize=12, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()

    output_path = output_dir / f"{roi}_geometric_metrics_barplot.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"  ✓ Saved: {output_path}")


def plot_procrustes_convergence(roi, procrustes_dir, output_dir):
    """
    Plot Procrustes convergence: disparity and template change vs iteration.
    """
    print(f"\n=== Generating Procrustes Convergence Plot ===")

    history_path = procrustes_dir / roi / "convergence_history.json"

    if not history_path.exists():
        print("  WARNING: Convergence history not found, skipping")
        return

    with open(history_path, 'r') as f:
        history = json.load(f)

    iterations = [h['iteration'] for h in history]
    mean_disparities = [h['mean_disparity'] for h in history]
    template_changes = [h['template_change'] for h in history]

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    # Mean disparity
    axes[0].plot(iterations, mean_disparities, 'o-', linewidth=2, markersize=8, color='blue')
    axes[0].set_xlabel('Iteration', fontsize=12)
    axes[0].set_ylabel('Mean Disparity', fontsize=12)
    axes[0].set_title(f'{roi} - Procrustes Mean Disparity', fontsize=13, fontweight='bold')
    axes[0].grid(True, alpha=0.3)

    # Template change
    axes[1].plot(iterations, template_changes, 'o-', linewidth=2, markersize=8, color='red')
    axes[1].set_xlabel('Iteration', fontsize=12)
    axes[1].set_ylabel('Template Change (Relative)', fontsize=12)
    axes[1].set_title(f'{roi} - Template Convergence', fontsize=13, fontweight='bold')
    axes[1].axhline(0.001, color='green', linestyle='--', linewidth=1.5, label='Convergence Threshold')
    axes[1].legend(fontsize=10)
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()

    output_path = output_dir / f"{roi}_procrustes_convergence.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"  ✓ Saved: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Step 5: Visualization & Reporting')
    parser.add_argument('--roi', type=str, required=True, help='ROI name (V1, V2, V3, hV4)')
    parser.add_argument('--method', type=str, default='pca', choices=['pca', 'anova'],
                        help='Dimension reduction method (default: pca)')
    parser.add_argument('--results-root', type=str,
                        default='/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/validation/scripts/postSRM_procrus/results',
                        help='Root results directory')

    args = parser.parse_args()

    results_root = Path(args.results_root)
    roi = args.roi

    # Directories
    if args.method == 'pca':
        step1_dir = results_root / 'step1_pca'
    else:
        step1_dir = results_root / 'step1_anova'

    step2_dir = results_root / 'step2_procrustes'
    step3_dir = results_root / 'step3_rdms'
    step4_dir = results_root / 'step4_metrics'
    output_dir = results_root / 'step5_visualizations'
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n=== Step 5: Visualization & Reporting ===")
    print(f"ROI: {roi}")
    print(f"Method: {args.method}")

    hc_subjects = ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05', 'sub-06']
    cvd_subjects = ['sub-08', 'sub-09', 'sub-10']
    all_subjects = hc_subjects + cvd_subjects

    # 1. PCA diagnostics (only for PCA method)
    if args.method == 'pca':
        plot_pca_diagnostics(roi, step1_dir, output_dir, all_subjects)

    # 2. RDM heatmaps
    plot_rdm_heatmaps(roi, step3_dir, step4_dir, output_dir, hc_subjects, cvd_subjects)

    # 3. Geometric metrics comparison
    stats_path = step4_dir / roi / "hc_vs_cvd_statistics.json"
    if stats_path.exists():
        plot_geometric_metrics_comparison(roi, stats_path, output_dir)

    # 4. Procrustes convergence
    plot_procrustes_convergence(roi, step2_dir, output_dir)

    print(f"\n✓ Step 5 complete for {roi}")
    print(f"  All visualizations saved to: {output_dir}")


if __name__ == '__main__':
    main()
