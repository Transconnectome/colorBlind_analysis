#!/usr/bin/env python3
"""
Generate detailed QC visualizations for Sub-06/07 analysis
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Read QC data
qc_file = Path('derivatives/QC/qc_classified.tsv')
df = pd.read_csv(qc_file, sep='\t')

# Calculate subject-level mean Dice
subject_dice = df.groupby('sub')['dice'].agg(['mean', 'std', 'min', 'max']).reset_index()
subject_dice.columns = ['subject', 'mean_dice', 'std_dice', 'min_dice', 'max_dice']

# Set up the figure with multiple subplots
fig = plt.figure(figsize=(20, 12))
gs = fig.add_gridspec(3, 3, hspace=0.4, wspace=0.3)

# ========================================
# Panel 1: Subject-level Dice distribution (Boxplot)
# ========================================
ax1 = fig.add_subplot(gs[0, :2])

subject_order = sorted(df['sub'].unique())
data_by_subject = [df[df['sub'] == s]['dice'].values for s in subject_order]

bp = ax1.boxplot(data_by_subject,
                 labels=[f'Sub-{s:02d}' for s in subject_order],
                 patch_artist=True,
                 showfliers=True)

# Color by tier
colors = []
for i, sub in enumerate(subject_order):
    mean = subject_dice[subject_dice['subject'] == sub]['mean_dice'].values[0]
    if mean >= 0.90:
        colors.append('#2ecc71')  # Green (Tier 1)
    elif mean >= 0.80:
        colors.append('#f39c12')  # Orange (Tier 2)
    else:
        colors.append('#e74c3c')  # Red (Tier 3)

for patch, color in zip(bp['boxes'], colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)

# Add threshold lines
ax1.axhline(y=0.90, color='green', linestyle='--', linewidth=2, alpha=0.5, label='Excellent (≥0.90)')
ax1.axhline(y=0.80, color='orange', linestyle='--', linewidth=2, alpha=0.5, label='Acceptable (≥0.80)')

ax1.set_xlabel('Subject', fontsize=12, fontweight='bold')
ax1.set_ylabel('Dice Coefficient', fontsize=12, fontweight='bold')
ax1.set_title('Panel 1: Dice Coefficient Distribution by Subject', fontsize=14, fontweight='bold')
ax1.legend(loc='lower left')
ax1.grid(axis='y', alpha=0.3)
ax1.set_ylim([0.5, 1.0])

# ========================================
# Panel 2: Sub-06 Run-level Dice
# ========================================
ax2 = fig.add_subplot(gs[0, 2])

sub06_runs = df[df['sub'] == 6].groupby('run')['dice'].mean().reset_index()
sub06_runs = sub06_runs.sort_values('run')

colors_06 = ['red' if d < 0.80 else 'green' for d in sub06_runs['dice']]
bars = ax2.bar(sub06_runs['run'], sub06_runs['dice'], color=colors_06, alpha=0.7, edgecolor='black')

# Add value labels
for i, (run, dice) in enumerate(zip(sub06_runs['run'], sub06_runs['dice'])):
    ax2.text(run, dice + 0.02, f'{dice:.3f}', ha='center', va='bottom', fontsize=10, fontweight='bold')

ax2.axhline(y=0.80, color='orange', linestyle='--', linewidth=2, label='Threshold (0.80)')
ax2.set_xlabel('Run', fontsize=12, fontweight='bold')
ax2.set_ylabel('Dice Coefficient', fontsize=12, fontweight='bold')
ax2.set_title('Panel 2: Sub-06 Run-level Quality', fontsize=14, fontweight='bold')
ax2.set_ylim([0.5, 1.0])
ax2.legend()
ax2.grid(axis='y', alpha=0.3)

# ========================================
# Panel 3: Sub-07 Run-level Dice
# ========================================
ax3 = fig.add_subplot(gs[1, 0])

sub07_runs = df[df['sub'] == 7].groupby('run')['dice'].mean().reset_index()
sub07_runs = sub07_runs.sort_values('run')

colors_07 = ['red' if d < 0.80 else 'green' for d in sub07_runs['dice']]
bars = ax3.bar(sub07_runs['run'], sub07_runs['dice'], color=colors_07, alpha=0.7, edgecolor='black')

# Add value labels
for i, (run, dice) in enumerate(zip(sub07_runs['run'], sub07_runs['dice'])):
    ax3.text(run, dice + 0.02, f'{dice:.3f}', ha='center', va='bottom', fontsize=10, fontweight='bold')

ax3.axhline(y=0.80, color='orange', linestyle='--', linewidth=2, label='Threshold (0.80)')
ax3.set_xlabel('Run', fontsize=12, fontweight='bold')
ax3.set_ylabel('Dice Coefficient', fontsize=12, fontweight='bold')
ax3.set_title('Panel 3: Sub-07 Run-level Quality', fontsize=14, fontweight='bold')
ax3.set_ylim([0.5, 1.0])
ax3.legend()
ax3.grid(axis='y', alpha=0.3)

# ========================================
# Panel 4: Quality Tier Summary (Pie chart)
# ========================================
ax4 = fig.add_subplot(gs[1, 1])

tier_counts = [
    (subject_dice['mean_dice'] >= 0.90).sum(),  # Tier 1
    ((subject_dice['mean_dice'] >= 0.80) & (subject_dice['mean_dice'] < 0.90)).sum(),  # Tier 2
    (subject_dice['mean_dice'] < 0.80).sum()   # Tier 3
]

colors_pie = ['#2ecc71', '#f39c12', '#e74c3c']
labels_pie = [f'Tier 1: Excellent\n(n={tier_counts[0]})',
              f'Tier 2: Good\n(n={tier_counts[1]})',
              f'Tier 3: Poor\n(n={tier_counts[2]})']

wedges, texts, autotexts = ax4.pie(tier_counts, labels=labels_pie, colors=colors_pie,
                                     autopct='%1.0f%%', startangle=90, textprops={'fontsize': 11})
for autotext in autotexts:
    autotext.set_color('white')
    autotext.set_fontweight('bold')

ax4.set_title('Panel 4: Subject Quality Distribution', fontsize=14, fontweight='bold')

# ========================================
# Panel 5: Contamination Illustration (Dice 0.73 vs 0.95)
# ========================================
ax5 = fig.add_subplot(gs[1, 2])

dice_values = [0.95, 0.73]
correct_pct = [95, 73]
contamination_pct = [5, 27]

x = np.arange(len(dice_values))
width = 0.35

p1 = ax5.bar(x, correct_pct, width, label='Correct ROI', color='green', alpha=0.7)
p2 = ax5.bar(x, contamination_pct, width, bottom=correct_pct, label='Contamination', color='red', alpha=0.7)

ax5.set_ylabel('Percentage (%)', fontsize=12, fontweight='bold')
ax5.set_title('Panel 5: ROI Quality Comparison', fontsize=14, fontweight='bold')
ax5.set_xticks(x)
ax5.set_xticklabels(['Tier 1\n(Dice 0.95)', 'Tier 3\n(Dice 0.73)'])
ax5.legend()
ax5.set_ylim([0, 100])

# Add percentage labels
for i, (c, cont) in enumerate(zip(correct_pct, contamination_pct)):
    ax5.text(i, c/2, f'{c}%', ha='center', va='center', fontweight='bold', fontsize=12, color='white')
    ax5.text(i, c + cont/2, f'{cont}%', ha='center', va='center', fontweight='bold', fontsize=12, color='white')

# ========================================
# Panel 6: Pass Rate by Subject
# ========================================
ax6 = fig.add_subplot(gs[2, 0])

pass_rate_by_sub = df.groupby('sub').apply(lambda x: (x['dice'] >= 0.80).mean() * 100).reset_index()
pass_rate_by_sub.columns = ['subject', 'pass_rate']

colors_pass = ['green' if p == 100 else 'orange' if p >= 75 else 'red' for p in pass_rate_by_sub['pass_rate']]
bars = ax6.bar(pass_rate_by_sub['subject'], pass_rate_by_sub['pass_rate'], color=colors_pass, alpha=0.7, edgecolor='black')

ax6.axhline(y=80, color='orange', linestyle='--', linewidth=2, label='80% threshold')
ax6.set_xlabel('Subject', fontsize=12, fontweight='bold')
ax6.set_ylabel('Pass Rate (%)', fontsize=12, fontweight='bold')
ax6.set_title('Panel 6: Pass Rate (Dice ≥ 0.80) by Subject', fontsize=14, fontweight='bold')
ax6.set_xticks(pass_rate_by_sub['subject'])
ax6.set_xticklabels([f'{s:02d}' for s in pass_rate_by_sub['subject']])
ax6.legend()
ax6.grid(axis='y', alpha=0.3)

# ========================================
# Panel 7: T1/BOLD Mask Ratio (over-extraction detection)
# ========================================
ax7 = fig.add_subplot(gs[2, 1])

# Calculate mask ratio per subject
mask_ratio = df.groupby('sub').apply(lambda x: (x['t1mask_vox'] / x['bmask_vox']).mean()).reset_index()
mask_ratio.columns = ['subject', 'ratio']

colors_ratio = ['red' if r > 2.0 else 'orange' if r > 1.5 else 'green' for r in mask_ratio['ratio']]
bars = ax7.bar(mask_ratio['subject'], mask_ratio['ratio'], color=colors_ratio, alpha=0.7, edgecolor='black')

ax7.axhline(y=1.5, color='orange', linestyle='--', linewidth=2, label='Caution (>1.5)')
ax7.axhline(y=2.0, color='red', linestyle='--', linewidth=2, label='Over-extraction (>2.0)')
ax7.set_xlabel('Subject', fontsize=12, fontweight='bold')
ax7.set_ylabel('T1/BOLD Mask Ratio', fontsize=12, fontweight='bold')
ax7.set_title('Panel 7: T1 Mask Over-extraction Detection', fontsize=14, fontweight='bold')
ax7.set_xticks(mask_ratio['subject'])
ax7.set_xticklabels([f'{s:02d}' for s in mask_ratio['subject']])
ax7.legend()
ax7.grid(axis='y', alpha=0.3)

# ========================================
# Panel 8: Usable Runs per Subject
# ========================================
ax8 = fig.add_subplot(gs[2, 2])

usable_runs = df.groupby('sub').apply(lambda x: (x['dice'] >= 0.80).sum() / 4).reset_index()  # 4 ROIs per run
usable_runs.columns = ['subject', 'n_runs']

colors_runs = ['green' if n == 6 else 'orange' if n >= 5 else 'red' for n in usable_runs['n_runs']]
bars = ax8.bar(usable_runs['subject'], usable_runs['n_runs'], color=colors_runs, alpha=0.7, edgecolor='black')

# Add value labels
for sub, n in zip(usable_runs['subject'], usable_runs['n_runs']):
    ax8.text(sub, n + 0.1, f'{n:.0f}', ha='center', va='bottom', fontsize=10, fontweight='bold')

ax8.set_xlabel('Subject', fontsize=12, fontweight='bold')
ax8.set_ylabel('Usable Runs (Dice ≥ 0.80)', fontsize=12, fontweight='bold')
ax8.set_title('Panel 8: Usable Runs per Subject', fontsize=14, fontweight='bold')
ax8.set_xticks(usable_runs['subject'])
ax8.set_xticklabels([f'{s:02d}' for s in usable_runs['subject']])
ax8.set_ylim([0, 7])
ax8.grid(axis='y', alpha=0.3)

# Add overall title
fig.suptitle('Detailed QC Analysis: Sub-06/07 Quality Assessment',
             fontsize=18, fontweight='bold', y=0.995)

# Save figure
output_file = Path('derivatives/QC/qc_detailed_analysis.png')
output_file.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(output_file, dpi=150, bbox_inches='tight')
print(f"✅ Saved detailed QC visualization: {output_file}")

plt.close()

# ========================================
# Generate summary statistics
# ========================================
print("\n📊 Summary Statistics:")
print(f"\nSubject-level Dice:")
print(subject_dice.to_string(index=False))

print(f"\nQuality Tiers:")
print(f"  Tier 1 (Dice ≥ 0.90): {tier_counts[0]} subjects")
print(f"  Tier 2 (Dice 0.80-0.89): {tier_counts[1]} subjects")
print(f"  Tier 3 (Dice < 0.80): {tier_counts[2]} subjects")

print(f"\nSub-06 run-level Dice:")
print(sub06_runs.to_string(index=False))

print(f"\nSub-07 run-level Dice:")
print(sub07_runs.to_string(index=False))

print("\n✅ Done!")
