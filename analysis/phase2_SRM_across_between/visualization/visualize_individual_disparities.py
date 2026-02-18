#!/usr/bin/env python3
"""
Visualize Individual Subject Disparities

Create comprehensive visualizations of per-subject disparity values.

Author: Claude Code
Date: 2026-02-10
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Paths
RESULTS_DIR = Path("/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/validation/SRM/results/c010")
OUTPUT_DIR = RESULTS_DIR / "visualizations"

# Load data
df_wide = pd.read_csv(RESULTS_DIR / 'individual_disparities_wide.csv')
df_long = pd.read_csv(RESULTS_DIR / 'individual_disparities_long.csv')
df_avg = pd.read_csv(RESULTS_DIR / 'subject_average_disparities.csv')

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Color scheme
HC_COLOR = '#4472C4'
CVD_COLOR = '#ED7D31'
CVD_COLORS = {
    'sub-08': '#E74C3C',  # Red
    'sub-09': '#F39C12',  # Orange
    'sub-10': '#27AE60'   # Green
}


def plot_disparity_by_roi():
    """Plot disparity values for each ROI, showing all subjects"""

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    axes = axes.flatten()

    rois = ['V1', 'V2', 'V3', 'V4']

    for ax, roi in zip(axes, rois):
        # Separate HC and CVD
        df_roi = df_long[df_long['roi'] == roi].copy()
        df_hc = df_roi[df_roi['group'] == 'HC']
        df_cvd = df_roi[df_roi['group'] == 'CVD']

        # Plot HC subjects
        x_hc = np.arange(len(df_hc))
        ax.bar(x_hc, df_hc['disparity'].values, color=HC_COLOR, alpha=0.7,
               label='HC', edgecolor='black', linewidth=1.5)

        # Plot CVD subjects
        x_cvd = np.arange(len(df_hc), len(df_hc) + len(df_cvd))
        colors_cvd = [CVD_COLORS[sid] for sid in df_cvd['subject_id'].values]
        ax.bar(x_cvd, df_cvd['disparity'].values, color=colors_cvd, alpha=0.7,
               edgecolor='black', linewidth=1.5)

        # Add individual CVD labels
        for i, (idx, row) in enumerate(df_cvd.iterrows()):
            ax.text(x_cvd[i], row['disparity'] + 0.02, row['subject_id'],
                   ha='center', va='bottom', fontsize=9, fontweight='bold',
                   color=CVD_COLORS[row['subject_id']])

        # HC mean line
        hc_mean = df_hc['disparity'].mean()
        ax.axhline(hc_mean, color='black', linestyle='--', linewidth=2,
                  label=f'HC mean: {hc_mean:.3f}', alpha=0.7)

        # Format
        ax.set_xticks(list(x_hc) + list(x_cvd))
        ax.set_xticklabels([s.replace('sub-', '') for s in df_roi['subject_id'].values],
                          rotation=0, fontsize=10)
        ax.set_ylabel('Disparity to HC Reference', fontsize=12, fontweight='bold')
        ax.set_title(f'{roi} - Individual Disparities', fontsize=14, fontweight='bold')
        ax.legend(loc='upper left', fontsize=10)
        ax.grid(axis='y', alpha=0.3)

        # Add vertical line to separate HC and CVD
        ax.axvline(x=len(df_hc) - 0.5, color='gray', linestyle=':', linewidth=2, alpha=0.5)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'individual_disparities_by_roi.png', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {OUTPUT_DIR / 'individual_disparities_by_roi.png'}")
    plt.close()


def plot_cvd_profile():
    """Plot CVD subject profiles across ROIs"""

    fig, axes = plt.subplots(1, 2, figsize=(18, 6))

    # Panel A: Individual CVD profiles
    ax = axes[0]

    df_cvd = df_wide[df_wide['group'] == 'CVD']
    rois = ['V1', 'V2', 'V3', 'V4']
    x = np.arange(len(rois))

    # Plot each CVD subject
    for idx, row in df_cvd.iterrows():
        subject_id = row['subject_id']
        values = [row[roi] for roi in rois]

        ax.plot(x, values, marker='o', markersize=10, linewidth=2.5,
               color=CVD_COLORS[subject_id], label=subject_id, alpha=0.8)

        # Add value labels
        for i, (roi, val) in enumerate(zip(rois, values)):
            ax.text(i, val + 0.02, f'{val:.3f}', ha='center', va='bottom',
                   fontsize=9, color=CVD_COLORS[subject_id], fontweight='bold')

    # HC mean line
    df_hc = df_wide[df_wide['group'] == 'HC']
    hc_means = [df_hc[roi].mean() for roi in rois]
    ax.plot(x, hc_means, 'k--', linewidth=3, label='HC mean', alpha=0.7)

    # HC range (±1 SD)
    hc_stds = [df_hc[roi].std() for roi in rois]
    ax.fill_between(x,
                    [m - s for m, s in zip(hc_means, hc_stds)],
                    [m + s for m, s in zip(hc_means, hc_stds)],
                    color='gray', alpha=0.2, label='HC ±1 SD')

    ax.set_xticks(x)
    ax.set_xticklabels(rois, fontsize=12)
    ax.set_ylabel('Disparity to HC Reference', fontsize=13, fontweight='bold')
    ax.set_title('A. CVD Subject Profiles Across ROIs', fontsize=14, fontweight='bold')
    ax.legend(fontsize=11, loc='upper left')
    ax.grid(alpha=0.3)

    # Panel B: Average disparity across all ROIs
    ax = axes[1]

    df_cvd_avg = df_avg[df_avg['group'] == 'CVD'].sort_values('mean_disparity_across_rois')
    df_hc_avg = df_avg[df_avg['group'] == 'HC']

    # Plot HC distribution
    x_hc = np.arange(len(df_hc_avg))
    ax.bar(x_hc, df_hc_avg['mean_disparity_across_rois'].values,
          color=HC_COLOR, alpha=0.7, label='HC', edgecolor='black', linewidth=1.5)

    # Plot CVD subjects
    x_cvd = np.arange(len(df_hc_avg), len(df_hc_avg) + len(df_cvd_avg))
    colors_cvd = [CVD_COLORS[sid] for sid in df_cvd_avg['subject_id'].values]
    bars_cvd = ax.bar(x_cvd, df_cvd_avg['mean_disparity_across_rois'].values,
                     color=colors_cvd, alpha=0.7, edgecolor='black', linewidth=1.5)

    # Add CVD labels
    for i, (idx, row) in enumerate(df_cvd_avg.iterrows()):
        val = row['mean_disparity_across_rois']
        ax.text(x_cvd[i], val + 0.01, f"{row['subject_id']}\n{val:.3f}",
               ha='center', va='bottom', fontsize=10, fontweight='bold',
               color=CVD_COLORS[row['subject_id']])

    # HC mean line
    hc_mean = df_hc_avg['mean_disparity_across_rois'].mean()
    ax.axhline(hc_mean, color='black', linestyle='--', linewidth=2,
              label=f'HC mean: {hc_mean:.3f}', alpha=0.7)

    ax.set_xticks(list(x_hc) + list(x_cvd))
    ax.set_xticklabels([s.replace('sub-', '') for s in pd.concat([df_hc_avg, df_cvd_avg])['subject_id'].values],
                      rotation=0, fontsize=10)
    ax.set_ylabel('Mean Disparity (across all ROIs)', fontsize=13, fontweight='bold')
    ax.set_title('B. Average Disparity Across All ROIs', fontsize=14, fontweight='bold')
    ax.legend(fontsize=11, loc='upper left')
    ax.grid(axis='y', alpha=0.3)

    # Add vertical separator
    ax.axvline(x=len(df_hc_avg) - 0.5, color='gray', linestyle=':', linewidth=2, alpha=0.5)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'cvd_subject_profiles.png', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {OUTPUT_DIR / 'cvd_subject_profiles.png'}")
    plt.close()


def plot_heatmap():
    """Create heatmap of disparities"""

    fig, ax = plt.subplots(figsize=(10, 12))

    # Prepare data
    df_plot = df_wide.copy()
    df_plot['subject_num_int'] = df_plot['subject_num'].astype(int)
    df_plot = df_plot.sort_values('subject_num_int')

    rois = ['V1', 'V2', 'V3', 'V4']
    data = df_plot[rois].values

    # Create heatmap
    im = ax.imshow(data, cmap='YlOrRd', aspect='auto', vmin=0.2, vmax=0.9)

    # Set ticks
    ax.set_xticks(np.arange(len(rois)))
    ax.set_yticks(np.arange(len(df_plot)))
    ax.set_xticklabels(rois, fontsize=12, fontweight='bold')
    ax.set_yticklabels(df_plot['subject_id'].values, fontsize=11)

    # Add values
    for i in range(len(df_plot)):
        for j in range(len(rois)):
            text = ax.text(j, i, f'{data[i, j]:.3f}',
                         ha="center", va="center", color="black",
                         fontsize=10, fontweight='bold')

    # Color code subject labels by group
    for i, (idx, row) in enumerate(df_plot.iterrows()):
        if row['group'] == 'CVD':
            ax.get_yticklabels()[i].set_color(CVD_COLORS[row['subject_id']])
            ax.get_yticklabels()[i].set_fontweight('bold')
        else:
            ax.get_yticklabels()[i].set_color(HC_COLOR)

    # Add colorbar
    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label('Disparity to HC Reference', fontsize=12, fontweight='bold')

    # Add horizontal line to separate HC and CVD
    n_hc = len(df_plot[df_plot['group'] == 'HC'])
    ax.axhline(y=n_hc - 0.5, color='black', linewidth=3, linestyle='-')

    # Add group labels
    ax.text(-0.8, n_hc / 2 - 0.5, 'HC', fontsize=14, fontweight='bold',
           rotation=90, va='center', ha='center', color=HC_COLOR)
    ax.text(-0.8, n_hc + 1, 'CVD', fontsize=14, fontweight='bold',
           rotation=90, va='center', ha='center', color=CVD_COLOR)

    ax.set_title('Individual Disparity Heatmap\n(Darker = Higher Disparity)',
                fontsize=14, fontweight='bold', pad=20)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'disparity_heatmap.png', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {OUTPUT_DIR / 'disparity_heatmap.png'}")
    plt.close()


def main():
    """Main execution"""

    print(f"\n{'='*80}")
    print("Visualizing Individual Subject Disparities")
    print(f"{'='*80}\n")

    print("Generating visualizations...")

    print("\n1. Individual disparities by ROI...")
    plot_disparity_by_roi()

    print("\n2. CVD subject profiles...")
    plot_cvd_profile()

    print("\n3. Disparity heatmap...")
    plot_heatmap()

    print(f"\n{'='*80}")
    print("✅ All visualizations complete!")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    main()
