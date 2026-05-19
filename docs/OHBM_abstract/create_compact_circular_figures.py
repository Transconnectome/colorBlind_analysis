"""
Create compact circular reconstruction figures for sub-06 and sub-08
with optimal k-values based on reconstruction error
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from pathlib import Path

def plot_compact_circular(ax, df_recon, title, label2hue_deg, radius=0.35):
    """
    Plot compact circular color reconstruction

    Parameters:
    -----------
    ax : matplotlib axis
    df_recon : DataFrame with reconstruction results
    title : str
    label2hue_deg : dict mapping color labels to hue degrees
    radius : float, radius of the circle (default 0.35, smaller than original ~0.5)
    """
    # Extract data
    true_hues = []
    pred_hues = []
    errors = []

    for idx, row in df_recon.iterrows():
        if pd.notna(row['true_hue']) and pd.notna(row['reconstructed_hue']):
            true_hues.append(row['true_hue'])
            pred_hues.append(row['reconstructed_hue'])
            errors.append(row['reconstruction_error'])

    true_hues = np.array(true_hues)
    pred_hues = np.array(pred_hues)
    errors = np.array(errors)

    # Convert to radians
    true_rads = np.deg2rad(true_hues)
    pred_rads = np.deg2rad(pred_hues)

    # Plot circle
    circle = plt.Circle((0, 0), radius, fill=False, color='black', linewidth=1.5)
    ax.add_patch(circle)

    # Plot true hues (filled circles on the circle)
    true_x = radius * np.cos(true_rads)
    true_y = radius * np.sin(true_rads)

    # Color map for hue
    def hue_to_rgb(hue_deg):
        """Convert hue (0-360) to RGB"""
        import colorsys
        return colorsys.hsv_to_rgb(hue_deg/360, 0.8, 0.9)

    # Plot true positions
    for i, (x, y, hue) in enumerate(zip(true_x, true_y, true_hues)):
        color = hue_to_rgb(hue)
        ax.plot(x, y, 'o', markersize=8, color=color,
               markeredgecolor='black', markeredgewidth=1.5, zorder=3)

    # Plot predicted positions (smaller, semi-transparent)
    pred_x = radius * np.cos(pred_rads)
    pred_y = radius * np.sin(pred_rads)

    for i, (x, y, hue, err) in enumerate(zip(pred_x, pred_y, pred_hues, errors)):
        color = hue_to_rgb(hue)
        # Connect true to predicted
        ax.plot([true_x[i], x], [true_y[i], y], 'k-', linewidth=0.5, alpha=0.3, zorder=1)
        # Plot predicted
        ax.plot(x, y, 's', markersize=5, color=color, alpha=0.6,
               markeredgecolor='gray', markeredgewidth=0.5, zorder=2)

    # Add cardinal directions with smaller font
    ax.text(0, radius*1.15, '0°', ha='center', va='bottom', fontsize=9)
    ax.text(radius*1.15, 0, '90°', ha='left', va='center', fontsize=9)
    ax.text(0, -radius*1.15, '180°', ha='center', va='top', fontsize=9)
    ax.text(-radius*1.15, 0, '270°', ha='right', va='center', fontsize=9)

    # Set equal aspect and limits
    lim = radius * 1.3
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_aspect('equal')
    ax.axis('off')

    # Add title with stats
    mean_error = np.mean(errors)
    acc_22_5 = (errors <= 22.5).mean() * 100
    acc_45 = (errors <= 45).mean() * 100

    title_text = f'{title}\nError: {mean_error:.1f}° | Acc@22.5°: {acc_22_5:.1f}% | Acc@45°: {acc_45:.1f}%'
    ax.set_title(title_text, fontsize=10, weight='bold', pad=8)

    # Add legend (compact)
    true_patch = mpatches.Patch(color='gray', label='True hue (circle)')
    pred_patch = mpatches.Patch(color='lightgray', label='Predicted (square)')
    ax.legend(handles=[true_patch, pred_patch], loc='upper right',
             fontsize=7, framealpha=0.9, bbox_to_anchor=(1.0, 1.0))

# Define color mapping (from utils_color_decoding.py)
LABEL2HUE_DEG = {
    'color_1': 0, 'color_2': 45, 'color_3': 90, 'color_4': 135,
    'color_5': 180, 'color_6': 225, 'color_7': 270, 'color_8': 315
}

# ============================================================================
# Figure 1: sub-06 All ROIs (k=5)
# ============================================================================

fig1, axes = plt.subplots(2, 2, figsize=(12, 12))
fig1.suptitle('sub-06: k=5 ANOVA Feature Selection\nCircular Color Reconstruction (All ROIs)',
             fontsize=14, weight='bold', y=0.98)

rois = ['V1', 'V2', 'V3', 'hV4']
roi_positions = [(0, 0), (0, 1), (1, 0), (1, 1)]

for roi, (row, col) in zip(rois, roi_positions):
    csv_file = f'logs/permutation_analysis/k5/anova_config32_determin/anova_results_config32_determin_sub-06_{roi}.csv'

    if Path(csv_file).exists():
        df = pd.read_csv(csv_file)
        df_recon = df[df['method'] == 'reconstruction_trial'].copy()

        if len(df_recon) > 0:
            ax = axes[row, col]
            title = f'sub-06 {roi} (k=5)'
            plot_compact_circular(ax, df_recon, title, LABEL2HUE_DEG, radius=0.35)
        else:
            axes[row, col].text(0.5, 0.5, 'No data', ha='center', va='center')
            axes[row, col].axis('off')
    else:
        axes[row, col].text(0.5, 0.5, 'File not found', ha='center', va='center')
        axes[row, col].axis('off')

plt.tight_layout()
output_file1 = 'logs/permutation_failes/k5_ridge_analysis/sub06_k5_compact_circular.png'
plt.savefig(output_file1, dpi=150, bbox_inches='tight', facecolor='white')
print(f'✓ Figure 1 saved: {output_file1}')
plt.close()

# ============================================================================
# Figure 2: sub-08 All ROIs (k=5)
# ============================================================================

fig2, axes = plt.subplots(2, 2, figsize=(12, 12))
fig2.suptitle('sub-08 (CVD): k=5 ANOVA Feature Selection\nCircular Color Reconstruction (All ROIs)',
             fontsize=14, weight='bold', y=0.98)

for roi, (row, col) in zip(rois, roi_positions):
    csv_file = f'logs/permutation_analysis/k5/anova_config32_determin/anova_results_config32_determin_sub-08_{roi}.csv'

    if Path(csv_file).exists():
        df = pd.read_csv(csv_file)
        df_recon = df[df['method'] == 'reconstruction_trial'].copy()

        if len(df_recon) > 0:
            ax = axes[row, col]
            title = f'sub-08 {roi} (k=5)'
            plot_compact_circular(ax, df_recon, title, LABEL2HUE_DEG, radius=0.35)
        else:
            axes[row, col].text(0.5, 0.5, 'No data', ha='center', va='center')
            axes[row, col].axis('off')
    else:
        axes[row, col].text(0.5, 0.5, 'File not found', ha='center', va='center')
        axes[row, col].axis('off')

plt.tight_layout()
output_file2 = 'logs/permutation_failes/k5_ridge_analysis/sub08_k5_compact_circular.png'
plt.savefig(output_file2, dpi=150, bbox_inches='tight', facecolor='white')
print(f'✓ Figure 2 saved: {output_file2}')
plt.close()

# ============================================================================
# Figure 3: Best ROIs comparison (sub-06 V2 vs sub-08 V3)
# ============================================================================

fig3, axes = plt.subplots(1, 2, figsize=(12, 6))
fig3.suptitle('Optimal ROIs: sub-06 V2 (67.8°) vs sub-08 V3 (71.4°) - k=5',
             fontsize=14, weight='bold')

# sub-06 V2
csv_file = 'logs/permutation_analysis/k5/anova_config32_determin/anova_results_config32_determin_sub-06_V2.csv'
df = pd.read_csv(csv_file)
df_recon = df[df['method'] == 'reconstruction_trial'].copy()
plot_compact_circular(axes[0], df_recon, 'sub-06 V2 (HC)\nBest reconstruction',
                     LABEL2HUE_DEG, radius=0.4)

# sub-08 V3
csv_file = 'logs/permutation_analysis/k5/anova_config32_determin/anova_results_config32_determin_sub-08_V3.csv'
df = pd.read_csv(csv_file)
df_recon = df[df['method'] == 'reconstruction_trial'].copy()
plot_compact_circular(axes[1], df_recon, 'sub-08 V3 (CVD)\nBest reconstruction',
                     LABEL2HUE_DEG, radius=0.4)

plt.tight_layout()
output_file3 = 'logs/permutation_failes/k5_ridge_analysis/sub06_sub08_best_comparison.png'
plt.savefig(output_file3, dpi=150, bbox_inches='tight', facecolor='white')
print(f'✓ Figure 3 saved: {output_file3}')
plt.close()

print('\n' + '='*80)
print('✅ All compact circular figures created!')
print('='*80)
print(f'1. sub-06 all ROIs: {output_file1}')
print(f'2. sub-08 all ROIs: {output_file2}')
print(f'3. Best ROI comparison: {output_file3}')
print('\nSummary:')
print('  sub-06 (HC): V2 best (67.8°)')
print('  sub-08 (CVD): V3 best (71.4°)')
