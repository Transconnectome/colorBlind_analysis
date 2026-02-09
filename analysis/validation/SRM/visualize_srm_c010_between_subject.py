#!/usr/bin/env python3
"""
Visualize C010 Between-Subject SRM Results (Dual Pipeline)

Creates visualizations comparing Raw-Averaged vs Procrustes-Averaged SRM:
1. Dual pipeline comparison (side-by-side)
2. HC-CVD disparity boxplots (3-group comparison)
3. Summary comparison across ROIs

Usage:
    python visualize_srm_c010_between_subject.py --results-dir results/c010/TIMESTAMP/

Output:
    results/c010/TIMESTAMP/visualizations/
    ├── {ROI}_dual_disparity_comparison.png
    ├── {ROI}_hc_cvd_boxplot.png
    ├── summary_raw_vs_procrustes.png
    └── summary_hc_cvd_separation.png
"""

import sys
import argparse
import json
from pathlib import Path
from typing import Dict, List

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server
import matplotlib.pyplot as plt
import seaborn as sns

# ============================================================================
# PLOTTING FUNCTIONS
# ============================================================================

def plot_dual_disparity_comparison(raw_results: Dict, proc_results: Dict,
                                   roi: str, output_dir: Path):
    """
    Side-by-side comparison of Raw vs Procrustes SRM disparities.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Extract data
    raw_hc = raw_results['disparities']['hc_to_hc_reference']['values']
    raw_cvd = raw_results['disparities']['cvd_to_hc_reference']['values']

    proc_hc = proc_results['disparities']['hc_to_hc_reference']['values']
    proc_cvd = proc_results['disparities']['cvd_to_hc_reference']['values']

    # Raw SRM
    bp1 = ax1.boxplot([raw_hc, raw_cvd], positions=[1, 2], widths=0.5,
                       patch_artist=True, showfliers=True,
                       labels=['HC-to-HC', 'CVD-to-HC'])

    for patch, color in zip(bp1['boxes'], ['skyblue', 'salmon']):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    ax1.set_ylabel('Procrustes Disparity', fontsize=12, fontweight='bold')
    ax1.set_title(f'Raw-Averaged SRM: {roi}', fontsize=14, fontweight='bold')
    ax1.grid(alpha=0.3, axis='y', linestyle=':')

    # Add p-value
    p_raw = raw_results['statistical_tests']['hc_vs_cvd']['p_value']
    d_raw = raw_results['statistical_tests']['hc_vs_cvd']['cohens_d']
    ax1.text(0.5, 0.95, f"p={p_raw:.4f}, d={d_raw:.2f}",
            transform=ax1.transAxes, ha='center', va='top',
            fontsize=10, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    # Procrustes SRM
    bp2 = ax2.boxplot([proc_hc, proc_cvd], positions=[1, 2], widths=0.5,
                       patch_artist=True, showfliers=True,
                       labels=['HC-to-HC', 'CVD-to-HC'])

    for patch, color in zip(bp2['boxes'], ['skyblue', 'salmon']):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    ax2.set_ylabel('Procrustes Disparity', fontsize=12, fontweight='bold')
    ax2.set_title(f'Procrustes-Averaged SRM: {roi}', fontsize=14, fontweight='bold')
    ax2.grid(alpha=0.3, axis='y', linestyle=':')

    # Add p-value
    p_proc = proc_results['statistical_tests']['hc_vs_cvd']['p_value']
    d_proc = proc_results['statistical_tests']['hc_vs_cvd']['cohens_d']
    ax2.text(0.5, 0.95, f"p={p_proc:.4f}, d={d_proc:.2f}",
            transform=ax2.transAxes, ha='center', va='top',
            fontsize=10, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()

    output_file = output_dir / f"{roi}_dual_disparity_comparison.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"  Saved dual disparity comparison to {output_file}")


def plot_hc_cvd_boxplot_3group(raw_results: Dict, proc_results: Dict,
                                roi: str, output_dir: Path):
    """
    3-group comparison: HC-HC vs CVD-CVD vs CVD-HC for both methods.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Raw SRM
    raw_hc_hc = raw_results['disparities']['hc_to_hc_reference']['values']
    raw_cvd_hc = raw_results['disparities']['cvd_to_hc_reference']['values']
    raw_cvd_cvd = raw_results['disparities']['cvd_to_cvd_pairwise']['values']

    if raw_cvd_cvd and not any(np.isnan(raw_cvd_cvd)):
        data_raw = [raw_hc_hc, raw_cvd_hc, raw_cvd_cvd]
        labels_raw = ['HC-to-HC', 'CVD-to-HC', 'CVD-to-CVD']
        colors_raw = ['skyblue', 'salmon', 'orchid']
    else:
        data_raw = [raw_hc_hc, raw_cvd_hc]
        labels_raw = ['HC-to-HC', 'CVD-to-HC']
        colors_raw = ['skyblue', 'salmon']

    bp1 = ax1.boxplot(data_raw, widths=0.5, patch_artist=True,
                      showfliers=True, labels=labels_raw)

    for patch, color in zip(bp1['boxes'], colors_raw):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    ax1.set_ylabel('Procrustes Disparity', fontsize=12, fontweight='bold')
    ax1.set_title(f'Raw SRM - Group Comparison: {roi}', fontsize=14, fontweight='bold')
    ax1.grid(alpha=0.3, axis='y', linestyle=':')

    # Procrustes SRM
    proc_hc_hc = proc_results['disparities']['hc_to_hc_reference']['values']
    proc_cvd_hc = proc_results['disparities']['cvd_to_hc_reference']['values']
    proc_cvd_cvd = proc_results['disparities']['cvd_to_cvd_pairwise']['values']

    if proc_cvd_cvd and not any(np.isnan(proc_cvd_cvd)):
        data_proc = [proc_hc_hc, proc_cvd_hc, proc_cvd_cvd]
        labels_proc = ['HC-to-HC', 'CVD-to-HC', 'CVD-to-CVD']
        colors_proc = ['skyblue', 'salmon', 'orchid']
    else:
        data_proc = [proc_hc_hc, proc_cvd_hc]
        labels_proc = ['HC-to-HC', 'CVD-to-HC']
        colors_proc = ['skyblue', 'salmon']

    bp2 = ax2.boxplot(data_proc, widths=0.5, patch_artist=True,
                      showfliers=True, labels=labels_proc)

    for patch, color in zip(bp2['boxes'], colors_proc):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    ax2.set_ylabel('Procrustes Disparity', fontsize=12, fontweight='bold')
    ax2.set_title(f'Procrustes SRM - Group Comparison: {roi}', fontsize=14, fontweight='bold')
    ax2.grid(alpha=0.3, axis='y', linestyle=':')

    plt.tight_layout()

    output_file = output_dir / f"{roi}_hc_cvd_boxplot.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"  Saved HC-CVD boxplot to {output_file}")


def plot_summary_comparison(comparisons: Dict[str, Dict], output_dir: Path):
    """
    Summary comparison across all ROIs: Raw vs Procrustes SRM.
    """
    rois = sorted(comparisons.keys())

    # Extract data
    raw_sep = [comparisons[roi]['raw_srm']['hc_cvd_separation'] for roi in rois]
    proc_sep = [comparisons[roi]['procrustes_srm']['hc_cvd_separation'] for roi in rois]
    improvements = [comparisons[roi]['comparison']['improvement_percent'] for roi in rois]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # HC-CVD separation comparison
    x = np.arange(len(rois))
    width = 0.35

    bars1 = ax1.bar(x - width/2, raw_sep, width, label='Raw SRM', color='steelblue', alpha=0.8)
    bars2 = ax1.bar(x + width/2, proc_sep, width, label='Procrustes SRM', color='coral', alpha=0.8)

    ax1.set_xlabel('ROI', fontsize=12, fontweight='bold')
    ax1.set_ylabel('HC-CVD Separation', fontsize=12, fontweight='bold')
    ax1.set_title('HC-CVD Separation: Raw vs Procrustes SRM', fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(rois, fontsize=11)
    ax1.legend(fontsize=11)
    ax1.grid(alpha=0.3, axis='y', linestyle=':')

    # Improvement percentage
    colors = ['green' if imp > 0 else 'red' for imp in improvements]

    bars = ax2.barh(rois, improvements, color=colors, alpha=0.7, edgecolor='black', linewidth=2)

    ax2.axvline(0, color='black', linestyle='-', linewidth=1)
    ax2.set_xlabel('Improvement (%)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('ROI', fontsize=12, fontweight='bold')
    ax2.set_title('Procrustes SRM Improvement over Raw SRM', fontsize=14, fontweight='bold')
    ax2.grid(alpha=0.3, axis='x', linestyle=':')

    # Add value labels
    for i, (bar, val) in enumerate(zip(bars, improvements)):
        ax2.text(val + 0.5 if val > 0 else val - 0.5, i,
                f'{val:+.2f}%', va='center', ha='left' if val > 0 else 'right',
                fontsize=10, fontweight='bold')

    plt.tight_layout()

    output_file = output_dir / "summary_raw_vs_procrustes.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"  Saved summary comparison to {output_file}")


def plot_summary_hc_cvd_separation(comparisons: Dict[str, Dict], output_dir: Path):
    """
    Summary of HC-CVD separation with statistical significance.
    """
    rois = sorted(comparisons.keys())

    # Extract data
    proc_sep = [comparisons[roi]['procrustes_srm']['hc_cvd_separation'] for roi in rois]
    proc_p = [comparisons[roi]['procrustes_srm']['p_value'] for roi in rois]
    proc_d = [comparisons[roi]['procrustes_srm']['cohens_d'] for roi in rois]

    fig, ax = plt.subplots(figsize=(10, 6))

    x = np.arange(len(rois))

    # Color by significance
    colors = ['green' if p < 0.05 else 'orange' for p in proc_p]

    bars = ax.bar(x, proc_sep, color=colors, alpha=0.7, edgecolor='black', linewidth=2)

    ax.set_xlabel('ROI', fontsize=12, fontweight='bold')
    ax.set_ylabel('HC-CVD Separation (Procrustes SRM)', fontsize=12, fontweight='bold')
    ax.set_title('HC vs CVD Group Differences (Procrustes-Averaged SRM)',
                fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(rois, fontsize=11)
    ax.grid(alpha=0.3, axis='y', linestyle=':')

    # Add significance annotations
    for i, (sep, p, d) in enumerate(zip(proc_sep, proc_p, proc_d)):
        sig_marker = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else 'n.s.'
        ax.text(i, sep + 0.01, f'{sig_marker}\nd={d:.2f}',
               ha='center', va='bottom', fontsize=9, fontweight='bold')

    # Legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='green', alpha=0.7, label='Significant (p < 0.05)'),
        Patch(facecolor='orange', alpha=0.7, label='Not significant')
    ]
    ax.legend(handles=legend_elements, fontsize=10)

    plt.tight_layout()

    output_file = output_dir / "summary_hc_cvd_separation.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"  Saved HC-CVD separation summary to {output_file}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Visualize C010 Between-Subject SRM Results'
    )
    parser.add_argument('--results-dir', type=str, required=True,
                       help='Results directory (e.g., results/c010/TIMESTAMP/)')

    args = parser.parse_args()

    results_dir = Path(args.results_dir)

    if not results_dir.exists():
        print(f"ERROR: Results directory not found: {results_dir}")
        sys.exit(1)

    output_dir = results_dir / "visualizations"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*80}")
    print("Visualizing C010 Between-Subject SRM Results")
    print(f"{'='*80}")
    print(f"Results: {results_dir}")
    print(f"Output: {output_dir}")

    # Find all result files
    raw_files = sorted(results_dir.glob("*_raw_srm_results.json"))
    proc_files = sorted(results_dir.glob("*_procrustes_srm_results.json"))
    comp_files = sorted(results_dir.glob("*_dual_comparison.json"))

    if len(raw_files) == 0:
        print("\nERROR: No result files found")
        sys.exit(1)

    print(f"\nFound {len(raw_files)} ROIs")

    # Load all comparisons
    comparisons = {}
    for comp_file in comp_files:
        with open(comp_file, 'r') as f:
            comp_data = json.load(f)
        roi = comp_data['roi']
        comparisons[roi] = comp_data

    # Generate plots for each ROI
    print("\n[1/3] Creating per-ROI visualizations...")

    for raw_file, proc_file in zip(raw_files, proc_files):
        with open(raw_file, 'r') as f:
            raw_results = json.load(f)
        with open(proc_file, 'r') as f:
            proc_results = json.load(f)

        roi = raw_results['roi']
        print(f"\n  Processing {roi}...")

        # Dual disparity comparison
        plot_dual_disparity_comparison(
            raw_results['results'],
            proc_results['results'],
            roi, output_dir
        )

        # HC-CVD boxplot
        plot_hc_cvd_boxplot_3group(
            raw_results['results'],
            proc_results['results'],
            roi, output_dir
        )

    # Summary plots
    print("\n[2/3] Creating summary visualizations...")
    plot_summary_comparison(comparisons, output_dir)

    print("\n[3/3] Creating HC-CVD separation summary...")
    plot_summary_hc_cvd_separation(comparisons, output_dir)

    print(f"\n{'='*80}")
    print(f"Visualization completed!")
    print(f"{'='*80}")
    print(f"\nOutputs saved to: {output_dir}")


if __name__ == '__main__':
    main()
