#!/usr/bin/env python3
"""
QC 결과 시각화

사용법:
  python visualize_qc.py derivatives/QC/qc_classified.tsv
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sys
import numpy as np

if len(sys.argv) < 2:
    print("Usage: python visualize_qc.py <qc_classified.tsv>")
    sys.exit(1)

# Load data
df = pd.read_csv(sys.argv[1], sep='\t')

# Create figure
fig = plt.figure(figsize=(16, 12))

# ============================================================================
# 1. Dice by Subject and Run
# ============================================================================
ax1 = plt.subplot(3, 3, 1)
for sub in sorted(df['sub'].unique()):
    sub_df = df[df['sub'] == sub].groupby('run')['dice'].mean()
    ax1.plot(sub_df.index, sub_df.values, marker='o', label=f'Sub-{sub:02.0f}')

ax1.axhline(0.85, color='green', linestyle='--', label='Excellent (0.85)', alpha=0.5)
ax1.axhline(0.80, color='orange', linestyle='--', label='Acceptable (0.80)', alpha=0.5)
ax1.set_xlabel('Run')
ax1.set_ylabel('Dice Coefficient')
ax1.set_title('Dice by Subject and Run')
ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
ax1.grid(True, alpha=0.3)

# ============================================================================
# 2. Dice Distribution (Histogram)
# ============================================================================
ax2 = plt.subplot(3, 3, 2)
dice_valid = df['dice'].dropna()
ax2.hist(dice_valid, bins=30, edgecolor='black', alpha=0.7)
ax2.axvline(dice_valid.mean(), color='red', linestyle='--', label=f'Mean: {dice_valid.mean():.3f}')
ax2.axvline(0.85, color='green', linestyle='--', label='Target: 0.85', alpha=0.5)
ax2.set_xlabel('Dice Coefficient')
ax2.set_ylabel('Count')
ax2.set_title(f'Dice Distribution (n={len(dice_valid)})')
ax2.legend()
ax2.grid(True, alpha=0.3, axis='y')

# ============================================================================
# 3. Overlap Fraction vs Dice
# ============================================================================
ax3 = plt.subplot(3, 3, 3)
scatter = ax3.scatter(df['overlap_frac'], df['dice'],
                     c=df['sub'], cmap='tab10', alpha=0.6, s=20)
ax3.plot([0, 1], [0, 1], 'k--', alpha=0.3, label='y=x')
ax3.axhline(0.80, color='orange', linestyle='--', alpha=0.5)
ax3.axvline(0.80, color='orange', linestyle='--', alpha=0.5)
ax3.set_xlabel('Overlap Fraction')
ax3.set_ylabel('Dice Coefficient')
ax3.set_title('Overlap Frac vs Dice')
plt.colorbar(scatter, ax=ax3, label='Subject')
ax3.grid(True, alpha=0.3)

# ============================================================================
# 4. T1/BOLD Mask Ratio by Subject
# ============================================================================
ax4 = plt.subplot(3, 3, 4)
df['mask_ratio'] = df['t1mask_vox'] / df['bmask_vox']
mask_ratio_by_sub = df.groupby('sub')['mask_ratio'].mean().sort_values()
ax4.barh(range(len(mask_ratio_by_sub)), mask_ratio_by_sub.values)
ax4.set_yticks(range(len(mask_ratio_by_sub)))
ax4.set_yticklabels([f'Sub-{int(s):02d}' for s in mask_ratio_by_sub.index])
ax4.axvline(1.0, color='green', linestyle='--', label='Equal size', alpha=0.5)
ax4.set_xlabel('T1 mask / BOLD mask ratio')
ax4.set_title('Mask Size Ratio by Subject')
ax4.legend()
ax4.grid(True, alpha=0.3, axis='x')

# ============================================================================
# 5. Status Distribution by Subject
# ============================================================================
ax5 = plt.subplot(3, 3, 5)
status_counts = df.groupby(['sub', 'status']).size().unstack(fill_value=0)
status_counts.plot(kind='bar', stacked=True, ax=ax5,
                   color=['red', 'orange', 'yellow', 'lightgreen', 'green'])
ax5.set_xlabel('Subject')
ax5.set_ylabel('Count')
ax5.set_title('QC Status Distribution')
ax5.legend(title='Status', bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
ax5.set_xticklabels([f'{int(x):02d}' for x in status_counts.index], rotation=0)
ax5.grid(True, alpha=0.3, axis='y')

# ============================================================================
# 6. ROI Voxel Count by Subject
# ============================================================================
ax6 = plt.subplot(3, 3, 6)
for roi in ['V1', 'V2', 'V3', 'V4']:
    roi_df = df[df['roi'] == roi].groupby('sub')['roi_vox'].mean()
    ax6.plot(roi_df.index, roi_df.values, marker='o', label=roi)
ax6.set_xlabel('Subject')
ax6.set_ylabel('Mean ROI Voxels')
ax6.set_title('ROI Size by Subject')
ax6.legend()
ax6.grid(True, alpha=0.3)

# ============================================================================
# 7. Dropout Metrics
# ============================================================================
ax7 = plt.subplot(3, 3, 7)
df_with_roi = df[df['roi_vox'] > 0]  # Only runs with ROI
if len(df_with_roi) > 0:
    ax7.scatter(df_with_roi['dropout_metric1'], df_with_roi['dropout_metric2'],
               c=df_with_roi['sub'], cmap='tab10', alpha=0.6, s=20)
    ax7.axhline(0.70, color='orange', linestyle='--', alpha=0.5, label='Moderate (0.70)')
    ax7.axhline(0.50, color='red', linestyle='--', alpha=0.5, label='Severe (0.50)')
    ax7.axvline(0.70, color='orange', linestyle='--', alpha=0.5)
    ax7.axvline(0.50, color='red', linestyle='--', alpha=0.5)
ax7.set_xlabel('Dropout Metric 1 (p10/median_brain)')
ax7.set_ylabel('Dropout Metric 2 (median/median_brain)')
ax7.set_title('Dropout Metrics (ROI_vox > 0 only)')
ax7.legend(fontsize=8)
ax7.grid(True, alpha=0.3)

# ============================================================================
# 8. Motion (FD) by Subject
# ============================================================================
ax8 = plt.subplot(3, 3, 8)
fd_by_sub = df.groupby('sub')['FD_mean'].mean().sort_values()
ax8.barh(range(len(fd_by_sub)), fd_by_sub.values)
ax8.set_yticks(range(len(fd_by_sub)))
ax8.set_yticklabels([f'Sub-{int(s):02d}' for s in fd_by_sub.index])
ax8.axvline(0.5, color='red', linestyle='--', label='Threshold (0.5mm)', alpha=0.5)
ax8.set_xlabel('Mean FD (mm)')
ax8.set_title('Motion by Subject')
ax8.legend()
ax8.grid(True, alpha=0.3, axis='x')

# ============================================================================
# 9. Summary Statistics Table
# ============================================================================
ax9 = plt.subplot(3, 3, 9)
ax9.axis('off')

summary_stats = []
for sub in sorted(df['sub'].unique()):
    sub_df = df[df['sub'] == sub]
    dice_mean = sub_df['dice'].mean()
    roi_zero_pct = 100 * (sub_df['roi_vox'] == 0).sum() / len(sub_df)
    coreg_poor_pct = 100 * (sub_df['dice'] < 0.80).sum() / len(sub_df)

    summary_stats.append({
        'Sub': f'{int(sub):02d}',
        'Dice': f'{dice_mean:.2f}',
        'ROI_0%': f'{roi_zero_pct:.0f}',
        'Coreg%': f'{coreg_poor_pct:.0f}'
    })

summary_df = pd.DataFrame(summary_stats)
table = ax9.table(cellText=summary_df.values, colLabels=summary_df.columns,
                 cellLoc='center', loc='center', bbox=[0, 0, 1, 1])
table.auto_set_font_size(False)
table.set_fontsize(9)
table.scale(1, 2)

# Color code by Dice
for i in range(1, len(summary_df) + 1):
    dice_val = float(summary_df.iloc[i-1]['Dice'])
    if dice_val < 0.30:
        color = 'lightcoral'
    elif dice_val < 0.50:
        color = 'lightyellow'
    elif dice_val < 0.70:
        color = 'lightgreen'
    else:
        color = 'palegreen'
    table[(i, 1)].set_facecolor(color)

ax9.set_title('Summary by Subject', fontsize=10, pad=20)

# ============================================================================
# Overall title and layout
# ============================================================================
fig.suptitle(f'QC Diagnostic Report\n{len(df)} ROI measurements from {df["sub"].nunique()} subjects',
            fontsize=14, fontweight='bold', y=0.995)
plt.tight_layout(rect=[0, 0, 1, 0.99])

# Save
output_file = sys.argv[1].replace('.tsv', '_report.png')
plt.savefig(output_file, dpi=150, bbox_inches='tight')
print(f"\n✅ Report saved to: {output_file}\n")

plt.show()
