#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
compare_subjects_cvd.py
-----------------------
Compare CVD discrimination metrics across multiple subjects.

This script loads metrics from all subjects and creates comparison visualizations:
1. Red-Green compression ratio comparison
2. Novel color reconstruction bias patterns
3. Color space structure comparison (MDS plots)
4. Statistical tests for CVD vs Non-CVD differences

Usage:
    python compare_subjects_cvd.py --cvd-subjects P01 --non-cvd-subjects 01 02 03 04
    python compare_subjects_cvd.py --subjects P01 01 02 03 04 --output-dir comparison/
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import argparse
from scipy import stats
from sklearn.manifold import MDS
import sys

# ============================================================================
# Configuration
# ============================================================================

ROIS = ['V1', 'V2', 'V3', 'hV4']

# ============================================================================
# Comparison Functions
# ============================================================================

def compare_red_green_compression(cvd_subjects, non_cvd_subjects, metrics_dir='cvd_metrics'):
    """
    Compare red-green compression ratios between CVD and Non-CVD groups
    """
    metrics_dir = Path(metrics_dir)

    # Load data
    all_data = []
    for subject in cvd_subjects + non_cvd_subjects:
        file_path = metrics_dir / f"{subject}_red_green_metrics.csv"
        if not file_path.exists():
            print(f"Warning: {file_path} not found")
            continue

        df = pd.read_csv(file_path)
        df['Group'] = 'CVD' if subject in cvd_subjects else 'Non-CVD'
        df['Subject'] = subject
        all_data.append(df)

    if not all_data:
        print("Error: No data found")
        return

    combined = pd.concat(all_data, ignore_index=True)

    # Create comparison plot
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Red-Green Compression Comparison: CVD vs Non-CVD', fontsize=16, fontweight='bold')

    for idx, roi in enumerate(ROIS):
        ax = axes[idx // 2, idx % 2]

        roi_data = combined[combined['ROI'] == roi]

        if roi_data.empty:
            ax.text(0.5, 0.5, f'No data for {roi}', ha='center', va='center')
            ax.set_title(roi)
            continue

        # Box plot
        sns.boxplot(data=roi_data, x='Group', y='Compression_Ratio', ax=ax)
        sns.stripplot(data=roi_data, x='Group', y='Compression_Ratio', ax=ax,
                     color='black', alpha=0.5, size=8)

        # Add reference line at 1.0 (no compression)
        ax.axhline(y=1.0, color='red', linestyle='--', alpha=0.5, label='No compression')

        # Statistical test
        cvd_values = roi_data[roi_data['Group'] == 'CVD']['Compression_Ratio']
        non_cvd_values = roi_data[roi_data['Group'] == 'Non-CVD']['Compression_Ratio']

        if len(cvd_values) > 0 and len(non_cvd_values) > 0:
            t_stat, p_value = stats.ttest_ind(cvd_values, non_cvd_values)
            ax.text(0.5, 0.95, f'p = {p_value:.4f}', transform=ax.transAxes,
                   ha='center', va='top', fontsize=10,
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        ax.set_ylabel('Compression Ratio')
        ax.set_title(f'{roi}')
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    return fig, combined

def compare_novel_color_biases(cvd_subjects, non_cvd_subjects, metrics_dir='cvd_metrics'):
    """
    Compare systematic biases in novel color reconstruction
    """
    metrics_dir = Path(metrics_dir)

    # Load data
    all_data = []
    for subject in cvd_subjects + non_cvd_subjects:
        file_path = metrics_dir / f"{subject}_novel_color_angles.csv"
        if not file_path.exists():
            continue

        df = pd.read_csv(file_path)
        df['Group'] = 'CVD' if subject in cvd_subjects else 'Non-CVD'
        df['Subject'] = subject

        # Compute bias (signed error)
        df['Bias'] = df['Mean_Reconstructed_Hue'] - df['True_Hue']
        # Wrap to [-180, 180]
        df['Bias'] = (df['Bias'] + 180) % 360 - 180

        all_data.append(df)

    if not all_data:
        print("Error: No data found")
        return

    combined = pd.concat(all_data, ignore_index=True)

    # Create polar bias plot
    fig = plt.figure(figsize=(16, 12))

    for idx, roi in enumerate(ROIS, 1):
        ax = fig.add_subplot(2, 2, idx, projection='polar')

        roi_data = combined[combined['ROI'] == roi]

        if roi_data.empty:
            continue

        # Plot CVD subjects
        cvd_data = roi_data[roi_data['Group'] == 'CVD']
        for _, row in cvd_data.iterrows():
            true_angle = np.deg2rad(row['True_Hue'])
            bias = row['Bias']
            # Plot as arrow from true position, length = bias magnitude
            ax.arrow(true_angle, 0, 0, bias,
                    head_width=0.1, head_length=5, fc='red', ec='red',
                    alpha=0.6, linewidth=2, label='CVD' if _ == cvd_data.index[0] else '')

        # Plot Non-CVD subjects
        non_cvd_data = roi_data[roi_data['Group'] == 'Non-CVD']
        for _, row in non_cvd_data.iterrows():
            true_angle = np.deg2rad(row['True_Hue'])
            bias = row['Bias']
            ax.arrow(true_angle, 0, 0, bias,
                    head_width=0.1, head_length=5, fc='blue', ec='blue',
                    alpha=0.4, linewidth=1, label='Non-CVD' if _ == non_cvd_data.index[0] else '')

        ax.set_theta_zero_location("E")
        ax.set_theta_direction(-1)
        ax.set_ylim([-90, 90])
        ax.set_title(f'{roi}: Reconstruction Bias\n(Red=CVD, Blue=Non-CVD)',
                    fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)

    plt.suptitle('Novel Color Reconstruction Bias Patterns', fontsize=16, fontweight='bold')
    plt.tight_layout()
    return fig, combined

def compare_color_space_structure(cvd_subjects, non_cvd_subjects, metrics_dir='cvd_metrics'):
    """
    Compare color space structure using MDS on reconstruction distances
    """
    metrics_dir = Path(metrics_dir)

    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    fig.suptitle('Color Space Structure (MDS): CVD vs Non-CVD', fontsize=16, fontweight='bold')

    for idx, roi in enumerate(ROIS):
        ax = axes[idx // 2, idx % 2]

        # For each subject, create distance matrix and apply MDS
        for subject in cvd_subjects + non_cvd_subjects:
            file_path = metrics_dir / f"{subject}_color_pair_distances.csv"
            if not file_path.exists():
                continue

            df = pd.read_csv(file_path)
            roi_data = df[df['ROI'] == roi]

            if roi_data.empty:
                continue

            # Build distance matrix
            colors = sorted(set(roi_data['Color1'].tolist() + roi_data['Color2'].tolist()))
            n_colors = len(colors)
            color_to_idx = {c: i for i, c in enumerate(colors)}

            dist_matrix = np.zeros((n_colors, n_colors))
            for _, row in roi_data.iterrows():
                i = color_to_idx[row['Color1']]
                j = color_to_idx[row['Color2']]
                dist = row['Reconstructed_Angle_Distance']
                dist_matrix[i, j] = dist
                dist_matrix[j, i] = dist

            # Apply MDS
            mds = MDS(n_components=2, dissimilarity='precomputed', random_state=42)
            coords = mds.fit_transform(dist_matrix)

            # Plot
            is_cvd = subject in cvd_subjects
            color = 'red' if is_cvd else 'blue'
            marker = 'o' if is_cvd else 's'
            alpha = 0.7 if is_cvd else 0.4
            label = f'{subject} (CVD)' if is_cvd else f'{subject} (Non-CVD)'

            ax.scatter(coords[:, 0], coords[:, 1], c=color, marker=marker,
                      s=100, alpha=alpha, edgecolors='black', linewidths=0.5,
                      label=label)

            # Annotate colors
            if is_cvd:  # Only annotate for CVD subjects to avoid clutter
                for i, color_name in enumerate(colors):
                    ax.annotate(color_name.replace('color_', 'c'),
                              coords[i], fontsize=8, ha='center', va='center')

        ax.set_xlabel('MDS Dimension 1')
        ax.set_ylabel('MDS Dimension 2')
        ax.set_title(f'{roi}')
        ax.legend(fontsize=8, loc='best')
        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color='k', linestyle='--', alpha=0.3)
        ax.axvline(x=0, color='k', linestyle='--', alpha=0.3)

    plt.tight_layout()
    return fig

def generate_statistical_comparison(cvd_subjects, non_cvd_subjects, metrics_dir='cvd_metrics', output_dir='comparison'):
    """
    Generate statistical comparison report
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "statistical_comparison.txt"

    with open(output_file, 'w') as f:
        f.write("="*80 + "\n")
        f.write("Statistical Comparison: CVD vs Non-CVD\n")
        f.write("="*80 + "\n\n")

        f.write(f"CVD subjects: {', '.join(cvd_subjects)}\n")
        f.write(f"Non-CVD subjects: {', '.join(non_cvd_subjects)}\n\n")

        # 1. Red-Green Compression
        f.write("1. RED-GREEN COMPRESSION RATIO\n")
        f.write("-"*80 + "\n")

        metrics_dir_path = Path(metrics_dir)
        all_rg_data = []
        for subject in cvd_subjects + non_cvd_subjects:
            file_path = metrics_dir_path / f"{subject}_red_green_metrics.csv"
            if file_path.exists():
                df = pd.read_csv(file_path)
                df['Group'] = 'CVD' if subject in cvd_subjects else 'Non-CVD'
                df['Subject'] = subject
                all_rg_data.append(df)

        if all_rg_data:
            combined_rg = pd.concat(all_rg_data, ignore_index=True)

            for roi in ROIS:
                roi_data = combined_rg[combined_rg['ROI'] == roi]
                if roi_data.empty:
                    continue

                cvd_values = roi_data[roi_data['Group'] == 'CVD']['Compression_Ratio']
                non_cvd_values = roi_data[roi_data['Group'] == 'Non-CVD']['Compression_Ratio']

                f.write(f"\n{roi}:\n")
                f.write(f"  CVD:     mean = {cvd_values.mean():.3f}, std = {cvd_values.std():.3f}, n = {len(cvd_values)}\n")
                f.write(f"  Non-CVD: mean = {non_cvd_values.mean():.3f}, std = {non_cvd_values.std():.3f}, n = {len(non_cvd_values)}\n")

                if len(cvd_values) > 0 and len(non_cvd_values) > 0:
                    t_stat, p_value = stats.ttest_ind(cvd_values, non_cvd_values)
                    f.write(f"  t-test: t = {t_stat:.3f}, p = {p_value:.4f}")
                    if p_value < 0.05:
                        f.write(" ***SIGNIFICANT***")
                    f.write("\n")

        f.write("\n\n")

        # 2. Novel Color Reconstruction Error
        f.write("2. NOVEL COLOR RECONSTRUCTION ERROR\n")
        f.write("-"*80 + "\n")

        all_novel_data = []
        for subject in cvd_subjects + non_cvd_subjects:
            file_path = metrics_dir_path / f"{subject}_novel_color_angles.csv"
            if file_path.exists():
                df = pd.read_csv(file_path)
                df['Group'] = 'CVD' if subject in cvd_subjects else 'Non-CVD'
                df['Subject'] = subject
                all_novel_data.append(df)

        if all_novel_data:
            combined_novel = pd.concat(all_novel_data, ignore_index=True)

            for roi in ROIS:
                roi_data = combined_novel[combined_novel['ROI'] == roi]
                if roi_data.empty:
                    continue

                cvd_values = roi_data[roi_data['Group'] == 'CVD']['Mean_Error']
                non_cvd_values = roi_data[roi_data['Group'] == 'Non-CVD']['Mean_Error']

                f.write(f"\n{roi}:\n")
                f.write(f"  CVD:     mean = {cvd_values.mean():.2f}°, std = {cvd_values.std():.2f}°, n = {len(cvd_values)}\n")
                f.write(f"  Non-CVD: mean = {non_cvd_values.mean():.2f}°, std = {non_cvd_values.std():.2f}°, n = {len(non_cvd_values)}\n")

                if len(cvd_values) > 0 and len(non_cvd_values) > 0:
                    t_stat, p_value = stats.ttest_ind(cvd_values, non_cvd_values)
                    f.write(f"  t-test: t = {t_stat:.3f}, p = {p_value:.4f}")
                    if p_value < 0.05:
                        f.write(" ***SIGNIFICANT***")
                    f.write("\n")

        f.write("\n\n")
        f.write("="*80 + "\n")

    return output_file

# ============================================================================
# Main Function
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Compare CVD metrics across subjects')
    parser.add_argument('--cvd-subjects', type=str, nargs='+', default=['P01'],
                       help='CVD subject IDs')
    parser.add_argument('--non-cvd-subjects', type=str, nargs='+', default=['01', '02', '03', '04'],
                       help='Non-CVD subject IDs')
    parser.add_argument('--metrics-dir', type=str, default='cvd_metrics',
                       help='Directory containing individual subject metrics')
    parser.add_argument('--output-dir', type=str, default='cvd_comparison',
                       help='Output directory for comparison results')

    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("="*80)
    print("Comparing CVD Metrics Across Subjects")
    print("="*80)
    print(f"CVD subjects: {args.cvd_subjects}")
    print(f"Non-CVD subjects: {args.non_cvd_subjects}")
    print(f"Output directory: {output_dir}")
    print()

    # 1. Compare red-green compression
    print("[1/4] Comparing red-green compression ratios...")
    fig1, data1 = compare_red_green_compression(args.cvd_subjects, args.non_cvd_subjects, args.metrics_dir)
    if fig1:
        fig1.savefig(output_dir / "red_green_compression_comparison.png", dpi=150, bbox_inches='tight')
        print(f"  Saved: {output_dir / 'red_green_compression_comparison.png'}")
        plt.close(fig1)
    print()

    # 2. Compare novel color biases
    print("[2/4] Comparing novel color reconstruction biases...")
    fig2, data2 = compare_novel_color_biases(args.cvd_subjects, args.non_cvd_subjects, args.metrics_dir)
    if fig2:
        fig2.savefig(output_dir / "novel_color_bias_comparison.png", dpi=150, bbox_inches='tight')
        print(f"  Saved: {output_dir / 'novel_color_bias_comparison.png'}")
        plt.close(fig2)
    print()

    # 3. Compare color space structure
    print("[3/4] Comparing color space structure (MDS)...")
    fig3 = compare_color_space_structure(args.cvd_subjects, args.non_cvd_subjects, args.metrics_dir)
    if fig3:
        fig3.savefig(output_dir / "color_space_structure_comparison.png", dpi=150, bbox_inches='tight')
        print(f"  Saved: {output_dir / 'color_space_structure_comparison.png'}")
        plt.close(fig3)
    print()

    # 4. Generate statistical comparison
    print("[4/4] Generating statistical comparison report...")
    stats_file = generate_statistical_comparison(args.cvd_subjects, args.non_cvd_subjects,
                                                 args.metrics_dir, output_dir)
    print(f"  Saved: {stats_file}")
    print()

    print("="*80)
    print("Comparison Complete!")
    print("="*80)
    print()
    print("Output files:")
    print(f"  1. red_green_compression_comparison.png")
    print(f"  2. novel_color_bias_comparison.png")
    print(f"  3. color_space_structure_comparison.png")
    print(f"  4. statistical_comparison.txt")
    print()

if __name__ == "__main__":
    main()
