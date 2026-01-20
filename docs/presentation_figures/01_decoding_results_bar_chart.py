#!/usr/bin/env python3
"""
Generate bar chart comparing HC vs CVD decoding performance across ROIs.
For Slide 3: Decoding Results - Neural-Behavioral Dissociation
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.patches import Rectangle

# Set style
plt.style.use('seaborn-v0_8-paper')
sns.set_palette("husl")
plt.rcParams['font.size'] = 11
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 13
plt.rcParams['figure.dpi'] = 150

# Data from FULL_STATISTICS_SUMMARY.md
rois = ['V1', 'V2', 'V3', 'hV4']

# Classification Accuracy (8-way, %)
hc_acc = [56.6, 43.8, 23.3, 24.3]
hc_acc_std = [18.6, 17.2, 9.1, 9.5]
cvd_acc = [55.6, 43.0, 27.8, 26.4]
cvd_acc_std = [2.4, 13.9, 8.4, 9.6]
p_values_acc = [0.930, 0.951, 0.496, 0.768]

# Reconstruction Error (mean angular error, degrees)
hc_err = [46.7, 56.9, 82.8, 82.1]
hc_err_std = [17.0, 16.8, 14.1, 4.6]
cvd_err = [42.4, 55.3, 78.9, 76.3]
cvd_err_std = [4.9, 5.1, 7.5, 3.9]
p_values_err = [0.694, 0.876, 0.675, 0.105]

# Create figure with two subplots
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

# ===== Panel A: Classification Accuracy =====
x = np.arange(len(rois))
width = 0.35

bars1 = ax1.bar(x - width/2, hc_acc, width, yerr=hc_acc_std,
                label='HC', color='#3498db', alpha=0.85,
                capsize=5, error_kw={'linewidth': 1.5})
bars2 = ax1.bar(x + width/2, cvd_acc, width, yerr=cvd_acc_std,
                label='CVD', color='#e74c3c', alpha=0.85,
                capsize=5, error_kw={'linewidth': 1.5})

# Chance level
ax1.axhline(y=12.5, color='gray', linestyle='--', linewidth=1.5,
            label='Chance (12.5%)', alpha=0.7)

# Significance annotations
for i, (p, hc, cvd) in enumerate(zip(p_values_acc, hc_acc, cvd_acc)):
    max_y = max(hc + hc_acc_std[i], cvd + cvd_acc_std[i])
    if p > 0.05:
        ax1.text(i, max_y + 3, 'n.s.', ha='center', va='bottom',
                fontsize=10, color='gray')

ax1.set_xlabel('ROI', fontweight='bold')
ax1.set_ylabel('Classification Accuracy (%)', fontweight='bold')
ax1.set_title('A. 8-way Color Classification', fontweight='bold', pad=10)
ax1.set_xticks(x)
ax1.set_xticklabels(rois)
ax1.legend(loc='upper right', framealpha=0.9)
ax1.set_ylim(0, 80)
ax1.grid(axis='y', alpha=0.3, linestyle=':')

# Add text box with key message
textstr = 'No significant CVD-HC differences\n(all p > 0.05)'
props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
ax1.text(0.05, 0.95, textstr, transform=ax1.transAxes, fontsize=9,
         verticalalignment='top', bbox=props)

# ===== Panel B: Reconstruction Error =====
bars3 = ax2.bar(x - width/2, hc_err, width, yerr=hc_err_std,
                label='HC', color='#3498db', alpha=0.85,
                capsize=5, error_kw={'linewidth': 1.5})
bars4 = ax2.bar(x + width/2, cvd_err, width, yerr=cvd_err_std,
                label='CVD', color='#e74c3c', alpha=0.85,
                capsize=5, error_kw={'linewidth': 1.5})

# Chance level (90 degrees for uniform distribution)
ax2.axhline(y=90, color='gray', linestyle='--', linewidth=1.5,
            label='Chance (90°)', alpha=0.7)

# Significance annotations
for i, (p, hc, cvd) in enumerate(zip(p_values_err, hc_err, cvd_err)):
    max_y = max(hc + hc_err_std[i], cvd + cvd_err_std[i])
    if p > 0.05:
        ax2.text(i, max_y + 5, 'n.s.', ha='center', va='bottom',
                fontsize=10, color='gray')
    elif p < 0.15:  # Trend for hV4
        ax2.text(i, max_y + 5, 'p=0.105', ha='center', va='bottom',
                fontsize=9, color='orange')

ax2.set_xlabel('ROI', fontweight='bold')
ax2.set_ylabel('Reconstruction Error (degrees)', fontweight='bold')
ax2.set_title('B. Hue Reconstruction Error', fontweight='bold', pad=10)
ax2.set_xticks(x)
ax2.set_xticklabels(rois)
ax2.legend(loc='upper left', framealpha=0.9)
ax2.set_ylim(0, 110)
ax2.grid(axis='y', alpha=0.3, linestyle=':')

# Add text box with key message
textstr = 'Above-chance performance in V1/V2\nNo CVD impairment (p > 0.10)'
props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
ax2.text(0.05, 0.95, textstr, transform=ax2.transAxes, fontsize=9,
         verticalalignment='top', bbox=props)

# Overall title
fig.suptitle('Neural Color Decoding: HC vs CVD Comparison',
             fontsize=14, fontweight='bold', y=0.98)

plt.tight_layout(rect=[0, 0, 1, 0.96])

# Save figure
output_path = '/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/docs/presentation_figures/01_decoding_results.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
print(f"✅ Saved: {output_path}")

# Also save as PDF for presentations
output_pdf = output_path.replace('.png', '.pdf')
plt.savefig(output_pdf, bbox_inches='tight', facecolor='white')
print(f"✅ Saved: {output_pdf}")

plt.show()

print("\n" + "="*60)
print("KEY FINDINGS:")
print("="*60)
print("\n📊 Classification Accuracy:")
for i, roi in enumerate(rois):
    print(f"  {roi}: HC {hc_acc[i]:.1f}±{hc_acc_std[i]:.1f}% vs CVD {cvd_acc[i]:.1f}±{cvd_acc_std[i]:.1f}% (p={p_values_acc[i]:.3f})")

print("\n📐 Reconstruction Error:")
for i, roi in enumerate(rois):
    print(f"  {roi}: HC {hc_err[i]:.1f}±{hc_err_std[i]:.1f}° vs CVD {cvd_err[i]:.1f}±{cvd_err_std[i]:.1f}° (p={p_values_err[i]:.3f})")

print("\n✅ CONCLUSION: No significant CVD-HC differences (all p > 0.05)")
print("   → Neural representations preserved despite retinal deficits (RQ1)")
print("="*60)
