#!/usr/bin/env python3
"""
Generate 3-panel diagram illustrating three-dimensional loss function components.
For Slide 6: Three-Dimensional Loss Function
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.spatial.distance import pdist, squareform
from scipy.stats import pearsonr

# Set style
plt.style.use('seaborn-v0_8-paper')
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['figure.dpi'] = 150

# Simulate 8-color patterns for visualization
np.random.seed(42)
n_colors = 8
n_voxels = 100

color_names = ['Red', 'Orange', 'Yellow', 'Green', 'Cyan', 'Blue', 'Purple', 'Magenta']
color_hex = ['#FF0000', '#FF8000', '#FFFF00', '#00FF00',
             '#00FFFF', '#0000FF', '#8000FF', '#FF00FF']

# HC pattern (target)
hc_pattern = np.random.randn(n_colors, n_voxels) * 0.5 + np.arange(n_colors)[:, None]

# CVD pattern (before correction)
cvd_before = hc_pattern.copy()
cvd_before *= np.array([0.7, 0.8, 0.9, 0.6, 1.1, 1.0, 1.2, 0.85])[:, None]  # Magnitude distortion
cvd_before += np.array([-0.5, -0.3, 0.1, -0.8, 0.4, 0.2, 0.6, 0.0])[:, None]  # Baseline shift
cvd_before += np.random.randn(n_colors, n_voxels) * 0.3  # Add noise

# CVD pattern (after correction) - much closer to HC
cvd_after = hc_pattern + np.random.randn(n_colors, n_voxels) * 0.1

# Create figure with 3 rows (Before/After) and 3 columns (3 loss components)
fig = plt.figure(figsize=(16, 10))
gs = fig.add_gridspec(3, 3, hspace=0.35, wspace=0.3)

# ===== COLUMN 1: MAGNITUDE LOSS =====
ax_mag_before = fig.add_subplot(gs[0, 0])
ax_mag_after = fig.add_subplot(gs[1, 0])
ax_mag_formula = fig.add_subplot(gs[2, 0])

# Before: Magnitude comparison
hc_norms = np.linalg.norm(hc_pattern, axis=1)
cvd_before_norms = np.linalg.norm(cvd_before, axis=1)
cvd_after_norms = np.linalg.norm(cvd_after, axis=1)

x_pos = np.arange(n_colors)
width = 0.35

ax_mag_before.bar(x_pos - width/2, hc_norms, width, label='HC (target)',
                  color='gray', alpha=0.7, edgecolor='black')
ax_mag_before.bar(x_pos + width/2, cvd_before_norms, width, label='CVD (before)',
                  color='#e74c3c', alpha=0.7, edgecolor='black')
ax_mag_before.set_ylabel('L2 Norm (Pattern Magnitude)', fontweight='bold')
ax_mag_before.set_title('Before Correction', fontweight='bold', fontsize=12)
ax_mag_before.set_xticks(x_pos)
ax_mag_before.set_xticklabels(color_names, rotation=45, ha='right', fontsize=9)
ax_mag_before.legend(loc='upper left', fontsize=9)
ax_mag_before.grid(axis='y', alpha=0.3, linestyle=':')

# Calculate loss
loss_before = np.mean((hc_norms - cvd_before_norms)**2)
textstr = f'L_magnitude = {loss_before:.3f}'
props = dict(boxstyle='round', facecolor='wheat', alpha=0.7)
ax_mag_before.text(0.95, 0.95, textstr, transform=ax_mag_before.transAxes,
                   fontsize=10, verticalalignment='top', horizontalalignment='right',
                   bbox=props)

# After: Much closer
ax_mag_after.bar(x_pos - width/2, hc_norms, width, label='HC (target)',
                color='gray', alpha=0.7, edgecolor='black')
ax_mag_after.bar(x_pos + width/2, cvd_after_norms, width, label='CVD (after)',
                color='#2ecc71', alpha=0.7, edgecolor='black')
ax_mag_after.set_ylabel('L2 Norm (Pattern Magnitude)', fontweight='bold')
ax_mag_after.set_title('After Correction', fontweight='bold', fontsize=12, color='green')
ax_mag_after.set_xticks(x_pos)
ax_mag_after.set_xticklabels(color_names, rotation=45, ha='right', fontsize=9)
ax_mag_after.legend(loc='upper left', fontsize=9)
ax_mag_after.grid(axis='y', alpha=0.3, linestyle=':')

loss_after = np.mean((hc_norms - cvd_after_norms)**2)
textstr = f'L_magnitude = {loss_after:.3f}\n({(1-loss_after/loss_before)*100:.1f}% reduction)'
props = dict(boxstyle='round', facecolor='lightgreen', alpha=0.7)
ax_mag_after.text(0.95, 0.95, textstr, transform=ax_mag_after.transAxes,
                  fontsize=10, verticalalignment='top', horizontalalignment='right',
                  bbox=props)

# Formula panel
ax_mag_formula.axis('off')
ax_mag_formula.text(0.5, 0.75, 'Magnitude Loss', ha='center', va='center',
                    fontsize=14, fontweight='bold', transform=ax_mag_formula.transAxes)
ax_mag_formula.text(0.5, 0.55, r'$L_{magnitude} = \frac{1}{C} \sum_{c=1}^{C} (||F_c|| - ||H_c||)^2$',
                    ha='center', va='center', fontsize=12, transform=ax_mag_formula.transAxes,
                    bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
ax_mag_formula.text(0.5, 0.35, 'Matches overall pattern strength\nfor each color', ha='center', va='center',
                    fontsize=10, style='italic', transform=ax_mag_formula.transAxes)
ax_mag_formula.text(0.5, 0.15, '🎯 Corrects under/over-activation', ha='center', va='center',
                    fontsize=10, transform=ax_mag_formula.transAxes,
                    bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.3))

# ===== COLUMN 2: BASELINE LOSS =====
ax_base_before = fig.add_subplot(gs[0, 1])
ax_base_after = fig.add_subplot(gs[1, 1])
ax_base_formula = fig.add_subplot(gs[2, 1])

# Before: Mean activation comparison
hc_means = np.mean(hc_pattern, axis=1)
cvd_before_means = np.mean(cvd_before, axis=1)
cvd_after_means = np.mean(cvd_after, axis=1)

ax_base_before.bar(x_pos - width/2, hc_means, width, label='HC (target)',
                   color='gray', alpha=0.7, edgecolor='black')
ax_base_before.bar(x_pos + width/2, cvd_before_means, width, label='CVD (before)',
                   color='#e74c3c', alpha=0.7, edgecolor='black')
ax_base_before.axhline(y=0, color='black', linestyle='-', linewidth=0.8, alpha=0.5)
ax_base_before.set_ylabel('Mean Activation (Baseline)', fontweight='bold')
ax_base_before.set_title('Before Correction', fontweight='bold', fontsize=12)
ax_base_before.set_xticks(x_pos)
ax_base_before.set_xticklabels(color_names, rotation=45, ha='right', fontsize=9)
ax_base_before.legend(loc='upper left', fontsize=9)
ax_base_before.grid(axis='y', alpha=0.3, linestyle=':')

loss_base_before = np.mean((hc_means - cvd_before_means)**2)
textstr = f'L_baseline = {loss_base_before:.3f}'
props = dict(boxstyle='round', facecolor='wheat', alpha=0.7)
ax_base_before.text(0.95, 0.95, textstr, transform=ax_base_before.transAxes,
                    fontsize=10, verticalalignment='top', horizontalalignment='right',
                    bbox=props)

# After
ax_base_after.bar(x_pos - width/2, hc_means, width, label='HC (target)',
                  color='gray', alpha=0.7, edgecolor='black')
ax_base_after.bar(x_pos + width/2, cvd_after_means, width, label='CVD (after)',
                  color='#2ecc71', alpha=0.7, edgecolor='black')
ax_base_after.axhline(y=0, color='black', linestyle='-', linewidth=0.8, alpha=0.5)
ax_base_after.set_ylabel('Mean Activation (Baseline)', fontweight='bold')
ax_base_after.set_title('After Correction', fontweight='bold', fontsize=12, color='green')
ax_base_after.set_xticks(x_pos)
ax_base_after.set_xticklabels(color_names, rotation=45, ha='right', fontsize=9)
ax_base_after.legend(loc='upper left', fontsize=9)
ax_base_after.grid(axis='y', alpha=0.3, linestyle=':')

loss_base_after = np.mean((hc_means - cvd_after_means)**2)
textstr = f'L_baseline = {loss_base_after:.3f}\n({(1-loss_base_after/loss_base_before)*100:.1f}% reduction)'
props = dict(boxstyle='round', facecolor='lightgreen', alpha=0.7)
ax_base_after.text(0.95, 0.95, textstr, transform=ax_base_after.transAxes,
                   fontsize=10, verticalalignment='top', horizontalalignment='right',
                   bbox=props)

# Formula panel
ax_base_formula.axis('off')
ax_base_formula.text(0.5, 0.75, 'Baseline Loss', ha='center', va='center',
                     fontsize=14, fontweight='bold', transform=ax_base_formula.transAxes)
ax_base_formula.text(0.5, 0.55, r'$L_{baseline} = \frac{1}{C} \sum_{c=1}^{C} (\bar{F}_c - \bar{H}_c)^2$',
                     ha='center', va='center', fontsize=12, transform=ax_base_formula.transAxes,
                     bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
ax_base_formula.text(0.5, 0.35, 'Matches mean activation level\nfor each color', ha='center', va='center',
                     fontsize=10, style='italic', transform=ax_base_formula.transAxes)
ax_base_formula.text(0.5, 0.15, '🎯 Corrects DC offset shifts', ha='center', va='center',
                     fontsize=10, transform=ax_base_formula.transAxes,
                     bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.3))

# ===== COLUMN 3: STRUCTURE LOSS (RDM) =====
ax_rdm_before = fig.add_subplot(gs[0, 2])
ax_rdm_after = fig.add_subplot(gs[1, 2])
ax_rdm_formula = fig.add_subplot(gs[2, 2])

# Compute RDMs
def compute_rdm(patterns):
    rdm = np.zeros((n_colors, n_colors))
    for i in range(n_colors):
        for j in range(n_colors):
            if i != j:
                rdm[i, j] = 1 - pearsonr(patterns[i], patterns[j])[0]
    return rdm

rdm_hc = compute_rdm(hc_pattern)
rdm_cvd_before = compute_rdm(cvd_before)
rdm_cvd_after = compute_rdm(cvd_after)

# Before
im1 = ax_rdm_before.imshow(rdm_cvd_before, cmap='RdYlBu_r', vmin=0, vmax=2)
ax_rdm_before.set_xticks(range(n_colors))
ax_rdm_before.set_yticks(range(n_colors))
ax_rdm_before.set_xticklabels(color_names, rotation=45, ha='right', fontsize=8)
ax_rdm_before.set_yticklabels(color_names, fontsize=8)
ax_rdm_before.set_title('CVD RDM (Before)', fontweight='bold', fontsize=12)
plt.colorbar(im1, ax=ax_rdm_before, fraction=0.046, pad=0.04)

# Correlation with HC
rdm_hc_upper = rdm_hc[np.triu_indices(n_colors, k=1)]
rdm_cvd_before_upper = rdm_cvd_before[np.triu_indices(n_colors, k=1)]
corr_before = pearsonr(rdm_hc_upper, rdm_cvd_before_upper)[0]

textstr = f'RDM corr with HC:\nr = {corr_before:.3f}'
props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
ax_rdm_before.text(0.05, 0.95, textstr, transform=ax_rdm_before.transAxes,
                   fontsize=10, verticalalignment='top', bbox=props)

# After
im2 = ax_rdm_after.imshow(rdm_cvd_after, cmap='RdYlBu_r', vmin=0, vmax=2)
ax_rdm_after.set_xticks(range(n_colors))
ax_rdm_after.set_yticks(range(n_colors))
ax_rdm_after.set_xticklabels(color_names, rotation=45, ha='right', fontsize=8)
ax_rdm_after.set_yticklabels(color_names, fontsize=8)
ax_rdm_after.set_title('CVD RDM (After)', fontweight='bold', fontsize=12, color='green')
plt.colorbar(im2, ax=ax_rdm_after, fraction=0.046, pad=0.04)

rdm_cvd_after_upper = rdm_cvd_after[np.triu_indices(n_colors, k=1)]
corr_after = pearsonr(rdm_hc_upper, rdm_cvd_after_upper)[0]

textstr = f'RDM corr with HC:\nr = {corr_after:.3f}\n({(corr_after - corr_before):.3f} improvement)'
props = dict(boxstyle='round', facecolor='lightgreen', alpha=0.8)
ax_rdm_after.text(0.05, 0.95, textstr, transform=ax_rdm_after.transAxes,
                  fontsize=10, verticalalignment='top', bbox=props)

# Formula panel
ax_rdm_formula.axis('off')
ax_rdm_formula.text(0.5, 0.75, 'Structure Loss (RDM)', ha='center', va='center',
                    fontsize=14, fontweight='bold', transform=ax_rdm_formula.transAxes)
ax_rdm_formula.text(0.5, 0.55, r'$L_{structure} = ||RDM(F) - RDM(H)||^2$',
                    ha='center', va='center', fontsize=12, transform=ax_rdm_formula.transAxes,
                    bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
ax_rdm_formula.text(0.5, 0.40, r'$RDM_{ij} = 1 - r(pattern_i, pattern_j)$',
                    ha='center', va='center', fontsize=10, style='italic',
                    transform=ax_rdm_formula.transAxes)
ax_rdm_formula.text(0.5, 0.25, 'Matches pairwise color similarity\ngeometry (8×8 structure)', ha='center', va='center',
                    fontsize=10, style='italic', transform=ax_rdm_formula.transAxes)
ax_rdm_formula.text(0.5, 0.10, '🎯 Preserves perceptual relationships', ha='center', va='center',
                    fontsize=10, transform=ax_rdm_formula.transAxes,
                    bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.3))

# Overall title
fig.suptitle('Three-Dimensional Loss Function: Magnitude + Baseline + Structure',
             fontsize=16, fontweight='bold', y=0.98)

# Add column labels
fig.text(0.18, 0.96, '(1) Magnitude Loss', ha='center', fontsize=13,
         fontweight='bold', color='#3498db')
fig.text(0.50, 0.96, '(2) Baseline Loss', ha='center', fontsize=13,
         fontweight='bold', color='#3498db')
fig.text(0.82, 0.96, '(3) Structure Loss', ha='center', fontsize=13,
         fontweight='bold', color='#3498db')

# Save figure
output_path = '/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/docs/presentation_figures/03_loss_function_3d.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
print(f"✅ Saved: {output_path}")

output_pdf = output_path.replace('.png', '.pdf')
plt.savefig(output_pdf, bbox_inches='tight', facecolor='white')
print(f"✅ Saved: {output_pdf}")

plt.show()

print("\n" + "="*60)
print("THREE-DIMENSIONAL LOSS FUNCTION:")
print("="*60)
print("\n📊 Component 1: Magnitude Loss")
print(f"   Before: {loss_before:.3f}")
print(f"   After:  {loss_after:.3f}")
print(f"   Reduction: {(1-loss_after/loss_before)*100:.1f}%")
print("\n📊 Component 2: Baseline Loss")
print(f"   Before: {loss_base_before:.3f}")
print(f"   After:  {loss_base_after:.3f}")
print(f"   Reduction: {(1-loss_base_after/loss_base_before)*100:.1f}%")
print("\n📊 Component 3: Structure Loss (RDM)")
print(f"   RDM correlation before: {corr_before:.3f}")
print(f"   RDM correlation after:  {corr_after:.3f}")
print(f"   Improvement: {(corr_after - corr_before):.3f}")
print("\n✅ All three dimensions corrected simultaneously")
print("   → Subject-specific weights (λ_mag, λ_base, λ_struct)")
print("   → Personalized filter design (RQ3)")
print("="*60)
