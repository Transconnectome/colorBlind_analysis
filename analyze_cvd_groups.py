#!/usr/bin/env python3
"""
CVD vs Non-CVD Group Comparison Analysis
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from scipy import stats

# Load summary data
df = pd.read_csv('logs/all_subjects_summary/all_subjects_summary.csv')

# Define groups (as integers)
NON_CVD = [1, 2]  # Normal color vision
CVD = [3, 4]      # Color vision deficiency

df['Group'] = df['Subject'].apply(lambda x: 'Non-CVD' if x in NON_CVD else 'CVD')

# Group statistics
print("="*80)
print("CVD vs Non-CVD GROUP COMPARISON")
print("="*80)
print()

# 1. Overall comparison
print("### OVERALL STATISTICS BY GROUP ###")
group_stats = df.groupby('Group').agg({
    'N_voxels': ['mean', 'std'],
    'Classification_accuracy': ['mean', 'std'],
    'Reconstruction_error_deg': ['mean', 'std'],
    'Novel_color_error_deg': ['mean', 'std']
}).round(2)
print(group_stats)
print()

# 2. By ROI
print("### BY ROI ###")
for roi in ['V1', 'V2', 'V3', 'hV4']:
    roi_data = df[df['ROI'] == roi]
    
    non_cvd = roi_data[roi_data['Group'] == 'Non-CVD']['Novel_color_error_deg']
    cvd = roi_data[roi_data['Group'] == 'CVD']['Novel_color_error_deg']
    
    # T-test (only if both groups have data)
    if len(non_cvd) > 1 and len(cvd) > 1:
        t_stat, p_value = stats.ttest_ind(non_cvd, cvd)
    else:
        t_stat, p_value = np.nan, np.nan
    
    print(f"\n{roi}:")
    print(f"  Non-CVD: {non_cvd.mean():.1f}° ± {non_cvd.std():.1f}° (n={len(non_cvd)})")
    print(f"  CVD:     {cvd.mean():.1f}° ± {cvd.std():.1f}° (n={len(cvd)})")
    print(f"  Difference: {cvd.mean() - non_cvd.mean():.1f}° (CVD - Non-CVD)")
    if not np.isnan(p_value):
        print(f"  t-statistic: {t_stat:.3f}, p-value: {p_value:.3f}")
        
        if p_value < 0.05:
            direction = "higher" if cvd.mean() > non_cvd.mean() else "lower"
            print(f"  *** SIGNIFICANT: CVD {direction} than Non-CVD (p < 0.05) ***")
        else:
            print(f"  No significant difference")

print()

# 3. Per-subject breakdown
print("="*80)
print("PER-SUBJECT BREAKDOWN")
print("="*80)
print()
for subj in [1, 2, 3, 4]:
    group = 'Non-CVD' if subj in NON_CVD else 'CVD'
    subj_data = df[df['Subject'] == subj]
    
    print(f"Subject {subj:02d} ({group}):")
    for _, row in subj_data.iterrows():
        print(f"  {row['ROI']:4s}: Recon={row['Reconstruction_error_deg']:4.1f}°, Novel={row['Novel_color_error_deg']:6.1f}°, Voxels={int(row['N_voxels']):4d}")
    print()

# Create visualizations
output_dir = Path('logs/cvd_group_analysis')
output_dir.mkdir(parents=True, exist_ok=True)

# Figure 1: Novel Error by Group and ROI
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Box plot
ax1 = axes[0]
sns.boxplot(data=df, x='ROI', y='Novel_color_error_deg', hue='Group', 
            palette={'Non-CVD': 'skyblue', 'CVD': 'salmon'}, ax=ax1)
ax1.axhline(y=90, color='red', linestyle='--', linewidth=2, alpha=0.7, label='Chance (90°)')
ax1.set_xlabel('ROI', fontsize=12, fontweight='bold')
ax1.set_ylabel('Novel Color Error (degrees)', fontsize=12, fontweight='bold')
ax1.set_title('Novel Color Error: Non-CVD vs CVD', fontsize=14, fontweight='bold')
ax1.legend(fontsize=10)
ax1.grid(True, alpha=0.3, axis='y')

# Bar plot with error bars
ax2 = axes[1]
group_roi_stats = df.groupby(['ROI', 'Group'])['Novel_color_error_deg'].agg(['mean', 'std']).reset_index()

rois = ['V1', 'V2', 'V3', 'hV4']
x = np.arange(len(rois))
width = 0.35

non_cvd_stats = group_roi_stats[group_roi_stats['Group'] == 'Non-CVD']
cvd_stats = group_roi_stats[group_roi_stats['Group'] == 'CVD']

non_cvd_means = [non_cvd_stats[non_cvd_stats['ROI'] == roi]['mean'].values[0] for roi in rois]
non_cvd_stds = [non_cvd_stats[non_cvd_stats['ROI'] == roi]['std'].values[0] for roi in rois]
cvd_means = [cvd_stats[cvd_stats['ROI'] == roi]['mean'].values[0] for roi in rois]
cvd_stds = [cvd_stats[cvd_stats['ROI'] == roi]['std'].values[0] for roi in rois]

ax2.bar(x - width/2, non_cvd_means, width, yerr=non_cvd_stds, 
        label='Non-CVD', color='skyblue', alpha=0.8, capsize=5)
ax2.bar(x + width/2, cvd_means, width, yerr=cvd_stds,
        label='CVD', color='salmon', alpha=0.8, capsize=5)

ax2.axhline(y=90, color='red', linestyle='--', linewidth=2, alpha=0.7)
ax2.set_xlabel('ROI', fontsize=12, fontweight='bold')
ax2.set_ylabel('Novel Color Error (degrees)', fontsize=12, fontweight='bold')
ax2.set_title('Mean Novel Error with Std Dev', fontsize=14, fontweight='bold')
ax2.set_xticks(x)
ax2.set_xticklabels(rois)
ax2.legend(fontsize=10)
ax2.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig(output_dir / 'cvd_vs_noncvd_novel_error.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"✓ Saved: {output_dir / 'cvd_vs_noncvd_novel_error.png'}")

# Figure 2: Training vs Novel Error by Group
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Training vs Novel Error: Non-CVD vs CVD', fontsize=16, fontweight='bold')

for idx, roi in enumerate(['V1', 'V2', 'V3', 'hV4']):
    ax = axes[idx // 2, idx % 2]
    roi_data = df[df['ROI'] == roi].sort_values('Subject')
    
    x = np.arange(len(roi_data))
    width = 0.35
    
    colors = ['skyblue' if g == 'Non-CVD' else 'salmon' for g in roi_data['Group']]
    
    ax.bar(x - width/2, roi_data['Reconstruction_error_deg'], width,
           label='Training Error', color=colors, alpha=0.6, edgecolor='black')
    ax.bar(x + width/2, roi_data['Novel_color_error_deg'], width,
           label='Novel Error', color=colors, alpha=1.0, edgecolor='black', linewidth=1.5)
    
    ax.axhline(y=90, color='red', linestyle='--', linewidth=1.5, alpha=0.5)
    ax.set_xlabel('Subject', fontweight='bold')
    ax.set_ylabel('Error (degrees)', fontweight='bold')
    ax.set_xticks(x)
    labels = [f"sub-{s:02d}\n({g})" for s, g in zip(roi_data['Subject'], roi_data['Group'])]
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_title(f'{roi}', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')
    ax.set_ylim([0, 130])
    
    if idx == 0:
        ax.legend(fontsize=9)

plt.tight_layout()
plt.savefig(output_dir / 'training_vs_novel_by_group.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"✓ Saved: {output_dir / 'training_vs_novel_by_group.png'}")

# Figure 3: Heatmap comparison
fig, axes = plt.subplots(1, 2, figsize=(16, 5))

# Non-CVD heatmap
non_cvd_data = df[df['Group'] == 'Non-CVD'].pivot(index='ROI', columns='Subject', values='Novel_color_error_deg')
sns.heatmap(non_cvd_data, annot=True, fmt='.1f', cmap='RdYlGn_r',
            center=90, vmin=40, vmax=130, ax=axes[0], 
            cbar_kws={'label': 'Error (degrees)'})
axes[0].set_title('Non-CVD (Normal Vision)', fontsize=14, fontweight='bold')
axes[0].set_xlabel('Subject', fontsize=12, fontweight='bold')
axes[0].set_ylabel('ROI', fontsize=12, fontweight='bold')

# CVD heatmap
cvd_data = df[df['Group'] == 'CVD'].pivot(index='ROI', columns='Subject', values='Novel_color_error_deg')
sns.heatmap(cvd_data, annot=True, fmt='.1f', cmap='RdYlGn_r',
            center=90, vmin=40, vmax=130, ax=axes[1],
            cbar_kws={'label': 'Error (degrees)'})
axes[1].set_title('CVD (Color Vision Deficiency)', fontsize=14, fontweight='bold')
axes[1].set_xlabel('Subject', fontsize=12, fontweight='bold')
axes[1].set_ylabel('ROI', fontsize=12, fontweight='bold')

plt.tight_layout()
plt.savefig(output_dir / 'heatmap_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"✓ Saved: {output_dir / 'heatmap_comparison.png'}")

print(f"\n✓ All visualizations saved to: {output_dir}")
print()

# Statistical summary for markdown
with open(output_dir / 'group_statistics.txt', 'w') as f:
    f.write("CVD vs Non-CVD Statistical Summary\n")
    f.write("="*80 + "\n\n")
    
    f.write("OVERALL:\n")
    f.write(f"Non-CVD (n=8): Novel error = {df[df['Group']=='Non-CVD']['Novel_color_error_deg'].mean():.1f}° ± {df[df['Group']=='Non-CVD']['Novel_color_error_deg'].std():.1f}°\n")
    f.write(f"CVD (n=8):     Novel error = {df[df['Group']=='CVD']['Novel_color_error_deg'].mean():.1f}° ± {df[df['Group']=='CVD']['Novel_color_error_deg'].std():.1f}°\n\n")
    
    f.write("BY ROI:\n")
    for roi in ['V1', 'V2', 'V3', 'hV4']:
        roi_data = df[df['ROI'] == roi]
        non_cvd = roi_data[roi_data['Group'] == 'Non-CVD']['Novel_color_error_deg']
        cvd = roi_data[roi_data['Group'] == 'CVD']['Novel_color_error_deg']
        
        if len(non_cvd) > 1 and len(cvd) > 1:
            t_stat, p_value = stats.ttest_ind(non_cvd, cvd)
        else:
            t_stat, p_value = np.nan, np.nan
        
        f.write(f"\n{roi}:\n")
        f.write(f"  Non-CVD: {non_cvd.mean():.1f}° ± {non_cvd.std():.1f}°\n")
        f.write(f"  CVD:     {cvd.mean():.1f}° ± {cvd.std():.1f}°\n")
        f.write(f"  Difference: {cvd.mean() - non_cvd.mean():.1f}°\n")
        if not np.isnan(p_value):
            f.write(f"  p-value: {p_value:.3f}\n")

print("✓ Analysis complete!")
