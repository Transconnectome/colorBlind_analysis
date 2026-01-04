#!/usr/bin/env python3
"""
Topology-focused visualization for the colorblind analysis
Emphasizes manifold structure, geometric alignment, and topological invariants
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Circle, FancyBboxPatch
from mpl_toolkits.mplot3d import proj3d
from pathlib import Path
import json

class Arrow3D(FancyArrowPatch):
    def __init__(self, xs, ys, zs, *args, **kwargs):
        FancyArrowPatch.__init__(self, (0, 0), (0, 0), *args, **kwargs)
        self._verts3d = xs, ys, zs

    def draw(self, renderer):
        xs3d, ys3d, zs3d = self._verts3d
        xs, ys, zs = proj3d.proj_transform(xs3d, ys3d, zs3d, renderer.M)
        self.set_positions((xs[0], ys[0]), (xs[1], ys[1]))
        FancyArrowPatch.draw(self, renderer)

# Create figure
fig = plt.figure(figsize=(20, 14))

# ============================================================================
# Panel 1: Manifold Perspective - Color Space as Embedded Manifolds
# ============================================================================
ax1 = plt.subplot(2, 3, 1, projection='3d')

# Generate example manifolds (8 colors as points on manifolds)
theta = np.linspace(0, 2*np.pi, 8, endpoint=False)

# HC manifold (roughly circular)
hc_x = np.cos(theta)
hc_y = np.sin(theta)
hc_z = np.zeros(8)

# CVD manifold (distorted - red-green axis compressed)
cvd_scale_rg = 0.5  # Red-green compression
cvd_x = cvd_scale_rg * np.cos(theta)
cvd_y = np.sin(theta)
cvd_z = 0.3 * np.sin(2*theta)  # Some warping

# Plot manifolds
ax1.scatter(hc_x, hc_y, hc_z, c='blue', s=100, alpha=0.7, label='HC Manifold', depthshade=True)
ax1.scatter(cvd_x, cvd_y, cvd_z, c='red', s=100, alpha=0.7, label='CVD Manifold', depthshade=True)

# Connect points to show structure
for i in range(8):
    ax1.plot([hc_x[i], hc_x[(i+1)%8]], [hc_y[i], hc_y[(i+1)%8]], [hc_z[i], hc_z[(i+1)%8]],
             'b-', alpha=0.3, linewidth=1)
    ax1.plot([cvd_x[i], cvd_x[(i+1)%8]], [cvd_y[i], cvd_y[(i+1)%8]], [cvd_z[i], cvd_z[(i+1)%8]],
             'r-', alpha=0.3, linewidth=1)

# Highlight compression
ax1.plot([0, 1], [0, 0], [0, 0], 'b--', linewidth=2, alpha=0.5)
ax1.plot([0, 0.5], [0, 0], [0, 0], 'r--', linewidth=2, alpha=0.5)
ax1.text(0.75, 0, 0.3, 'R-G axis\ncompressed', fontsize=10, color='red', fontweight='bold')

ax1.set_xlabel('Red-Green Axis', fontsize=10, fontweight='bold')
ax1.set_ylabel('Blue-Yellow Axis', fontsize=10, fontweight='bold')
ax1.set_zlabel('Higher-order', fontsize=10, fontweight='bold')
ax1.set_title('A. Color Manifolds in Neural Space\n(Intrinsic Geometry Differs)',
              fontsize=12, fontweight='bold')
ax1.legend(loc='upper right', fontsize=10)
ax1.view_init(elev=20, azim=45)

# ============================================================================
# Panel 2: Procrustes as Manifold Isometry
# ============================================================================
ax2 = plt.subplot(2, 3, 2)

# Original HC and CVD in different coordinate systems
hc_original = np.array([[np.cos(t), np.sin(t)] for t in theta])
cvd_original_offset = np.array([[np.cos(t) + 2, np.sin(t) + 1.5] for t in theta])

# After Procrustes (aligned)
rotation_angle = np.pi/6
R = np.array([[np.cos(rotation_angle), -np.sin(rotation_angle)],
              [np.sin(rotation_angle), np.cos(rotation_angle)]])
cvd_aligned = (cvd_original_offset - cvd_original_offset.mean(axis=0)) @ R.T

# Plot before
ax2.scatter(hc_original[:, 0], hc_original[:, 1], c='blue', s=100, alpha=0.5,
            label='HC (Reference)', edgecolors='black', linewidths=1.5)
ax2.scatter(cvd_original_offset[:, 0], cvd_original_offset[:, 1], c='lightcoral', s=100,
            alpha=0.5, marker='s', label='CVD (Original)', edgecolors='black', linewidths=1.5)

# Arrow showing transformation
ax2.annotate('', xy=(0, 0), xytext=(2, 1.5),
            arrowprops=dict(arrowstyle='->', lw=3, color='purple', alpha=0.7))
ax2.text(1, 0.75, 'Procrustes\nTransform', fontsize=11, color='purple',
         fontweight='bold', ha='center',
         bbox=dict(boxstyle='round', facecolor='lavender', alpha=0.7))

# Plot after (smaller, in corner)
inset_ax = ax2.inset_axes([0.6, 0.6, 0.35, 0.35])
inset_ax.scatter(hc_original[:, 0], hc_original[:, 1], c='blue', s=50, alpha=0.7, edgecolors='black')
inset_ax.scatter(cvd_aligned[:, 0], cvd_aligned[:, 1], c='red', s=50, alpha=0.7,
                marker='s', edgecolors='black')
inset_ax.set_title('After Alignment', fontsize=9, fontweight='bold')
inset_ax.set_xticks([])
inset_ax.set_yticks([])
inset_ax.spines['top'].set_visible(True)
inset_ax.spines['right'].set_visible(True)

ax2.set_xlabel('Dimension 1', fontsize=11, fontweight='bold')
ax2.set_ylabel('Dimension 2', fontsize=11, fontweight='bold')
ax2.set_title('B. Procrustes: Finding Optimal Isometry\n(Rotation + Translation + Scaling)',
              fontsize=12, fontweight='bold')
ax2.legend(loc='upper left', fontsize=10)
ax2.grid(True, alpha=0.3)
ax2.set_aspect('equal')
ax2.set_xlim(-1.5, 3.5)
ax2.set_ylim(-1.5, 3)

# ============================================================================
# Panel 3: Disparity as Geometric Distance
# ============================================================================
ax3 = plt.subplot(2, 3, 3)

# After alignment, show remaining distance
hc_points = np.array([[np.cos(t), np.sin(t)] for t in theta])
cvd_points = hc_points * 0.7 + np.random.randn(8, 2) * 0.1  # Distorted

ax3.scatter(hc_points[:, 0], hc_points[:, 1], c='blue', s=150, alpha=0.7,
            label='HC Manifold', edgecolors='black', linewidths=2, zorder=3)
ax3.scatter(cvd_points[:, 0], cvd_points[:, 1], c='red', s=150, alpha=0.7,
            label='CVD Manifold', edgecolors='black', linewidths=2, marker='s', zorder=3)

# Draw correspondence lines
for i in range(8):
    ax3.plot([hc_points[i, 0], cvd_points[i, 0]],
             [hc_points[i, 1], cvd_points[i, 1]],
             'gray', linestyle='--', linewidth=1.5, alpha=0.6, zorder=1)

    # Calculate distance
    dist = np.linalg.norm(hc_points[i] - cvd_points[i])
    mid_x = (hc_points[i, 0] + cvd_points[i, 0]) / 2
    mid_y = (hc_points[i, 1] + cvd_points[i, 1]) / 2
    if i % 2 == 0:  # Label every other point to avoid clutter
        ax3.text(mid_x, mid_y, f'd={dist:.2f}', fontsize=8, ha='center',
                bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5))

# Overall disparity
overall_disparity = 0.32  # Example
ax3.text(0.05, 0.95, f'Disparity = {overall_disparity:.3f}\n(Frobenius norm)',
         transform=ax3.transAxes, fontsize=11, va='top', fontweight='bold',
         bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

ax3.set_xlabel('Dimension 1', fontsize=11, fontweight='bold')
ax3.set_ylabel('Dimension 2', fontsize=11, fontweight='bold')
ax3.set_title('C. Disparity: Remaining Geometric Distance\nAfter Optimal Alignment',
              fontsize=12, fontweight='bold')
ax3.legend(loc='lower right', fontsize=10)
ax3.grid(True, alpha=0.3)
ax3.set_aspect('equal')
ax3.set_xlim(-1.3, 1.3)
ax3.set_ylim(-1.3, 1.3)

# ============================================================================
# Panel 4: Individual Coordinate Systems (Fiber Bundle View)
# ============================================================================
ax4 = plt.subplot(2, 3, 4)

# Base space (abstract color space - 1D for simplicity)
base_x = np.linspace(0, 1, 8)
base_y = np.zeros(8)

# Fibers (individual representations)
fiber_height = 1.5
subjects = ['HC1', 'HC2', 'CVD1', 'CVD2']
colors = ['steelblue', 'steelblue', 'salmon', 'lightcoral']
offsets = [-0.15, -0.05, 0.05, 0.15]

for subj, color, offset in zip(subjects, colors, offsets):
    # Each subject's representation
    fiber_x = base_x + offset
    fiber_y = np.random.randn(8) * 0.2 + fiber_height

    ax4.scatter(fiber_x, fiber_y, c=color, s=80, alpha=0.7, label=subj, edgecolors='black')

    # Connections to base
    for i in range(8):
        ax4.plot([base_x[i], fiber_x[i]], [base_y[i], fiber_y[i]],
                color=color, linestyle=':', linewidth=1, alpha=0.3)

# Base space
ax4.scatter(base_x, base_y, c='gold', s=150, marker='*', label='Abstract\nColor Space',
           edgecolors='black', linewidths=2, zorder=10)

# Annotations
ax4.text(0.5, -0.3, 'Abstract Color Manifold\n(Common Base Space)',
         ha='center', fontsize=10, fontweight='bold',
         bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.7))
ax4.text(0.5, fiber_height + 0.4, 'Individual Neural Representations\n(Different Coordinate Systems)',
         ha='center', fontsize=10, fontweight='bold',
         bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.7))

ax4.set_xlabel('Color Dimension', fontsize=11, fontweight='bold')
ax4.set_ylabel('Representation Space', fontsize=11, fontweight='bold')
ax4.set_title('D. Fiber Bundle View: Abstract Structure\nvs Individual Embeddings',
              fontsize=12, fontweight='bold')
ax4.legend(loc='upper left', fontsize=9, ncol=2)
ax4.set_xlim(-0.3, 1.3)
ax4.set_ylim(-0.5, 2.2)
ax4.grid(True, alpha=0.3)

# ============================================================================
# Panel 5: Topological Invariants - Why Group Fails, Individual Succeeds
# ============================================================================
ax5 = plt.subplot(2, 3, 5)

# Schematic showing averaging destroys structure
n_points = 8
angles = np.linspace(0, 2*np.pi, n_points, endpoint=False)

# Three CVD subjects with different distortions
cvd1_r = 1 + 0.3 * np.cos(2*angles)  # Elongated
cvd2_r = 1 + 0.2 * np.sin(3*angles)  # Different distortion
cvd3_r = 1 - 0.2 * np.cos(angles)     # Yet another

cvd1_x = cvd1_r * np.cos(angles)
cvd1_y = cvd1_r * np.sin(angles)
cvd2_x = cvd2_r * np.cos(angles + np.pi/4)
cvd2_y = cvd2_r * np.sin(angles + np.pi/4)
cvd3_x = cvd3_r * np.cos(angles - np.pi/6)
cvd3_y = cvd3_r * np.sin(angles - np.pi/6)

# Individual shapes
ax5.plot(cvd1_x, cvd1_y, 'o-', color='red', linewidth=2, markersize=8,
         alpha=0.7, label='CVD-1 (Deut)')
ax5.plot(cvd2_x, cvd2_y, 's-', color='orange', linewidth=2, markersize=8,
         alpha=0.7, label='CVD-2 (Deut)')
ax5.plot(cvd3_x, cvd3_y, '^-', color='pink', linewidth=2, markersize=8,
         alpha=0.7, label='CVD-3 (Prot)')

# Average (circle)
avg_x = (cvd1_x + cvd2_x + cvd3_x) / 3
avg_y = (cvd1_y + cvd2_y + cvd3_y) / 3
ax5.plot(avg_x, avg_y, 'ko-', linewidth=3, markersize=10,
         label='Group Average', alpha=0.8)

# HC reference (perfect circle)
hc_x = np.cos(angles)
hc_y = np.sin(angles)
ax5.plot(hc_x, hc_y, 'b--', linewidth=2, alpha=0.5, label='HC Reference')

ax5.text(0, 0, 'Averaging\nDestroys\nStructure!', ha='center', fontsize=11,
         fontweight='bold', color='darkred',
         bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))

ax5.set_xlabel('Dimension 1', fontsize=11, fontweight='bold')
ax5.set_ylabel('Dimension 2', fontsize=11, fontweight='bold')
ax5.set_title('E. Topology: Why Averaging Fails\n(Different Intrinsic Geometries)',
              fontsize=12, fontweight='bold')
ax5.legend(loc='upper right', fontsize=9)
ax5.grid(True, alpha=0.3)
ax5.set_aspect('equal')
ax5.set_xlim(-1.8, 1.8)
ax5.set_ylim(-1.8, 1.8)

# ============================================================================
# Panel 6: The Topological Story - Summary
# ============================================================================
ax6 = plt.subplot(2, 3, 6)
ax6.axis('off')

summary_text = """
╔════════════════════════════════════════════════════════════╗
║        THE TOPOLOGICAL PERSPECTIVE                         ║
╚════════════════════════════════════════════════════════════╝

🎯 MANIFOLD STRUCTURE

   Each subject's color representation = embedded manifold M
   in high-dimensional neural space ℝⁿ (n = # voxels)

   • HC subjects: {M₁ᴴᶜ, M₂ᴴᶜ, M₃ᴴᶜ, M₄ᴴᶜ}
   • CVD subjects: {M₁ᶜⱽᴰ, M₂ᶜⱽᴰ, M₃ᶜⱽᴰ}

🔄 PROCRUSTES = ISOMETRY SEARCH

   Find rigid transformation T: ℝⁿ → ℝⁿ such that:

   d(T(Mᵢᶜⱽᴰ), M̄ᴴᶜ) is minimized

   where T preserves:
   • Inner products (angles)
   • Distances (after scaling)
   • Orientation

📏 DISPARITY = GEOMETRIC DISTANCE

   After optimal alignment:

   Disparity = ||T(Mᶜⱽᴰ) - Mᴴᶜ||_F / ||Mᴴᶜ||_F

   HC-HC: ~0.1  (small) → Same topology ✓
   HC-CVD: ~0.3-0.5 (large) → Different topology!

🌀 WHY GROUP-LEVEL FAILS

   Each CVD has different intrinsic geometry:

   M₁ᶜⱽᴰ: Red-green axis compressed by 0.5
   M₂ᶜⱽᴰ: Red-green axis compressed by 0.7
   M₃ᶜⱽᴰ: Red-green axis compressed by 0.8

   Average manifold ≠ preserves individual structure
   → Topological features cancel out!

✅ WHY INDIVIDUAL-LEVEL SUCCEEDS

   Each Mᵢᶜⱽᴰ has consistent, measurable distortion
   from M̄ᴴᶜ:

   • Systematic compression of color subspace
   • Reproducible geometric transformation
   • Topological signature preserved

🎓 MATHEMATICAL INSIGHT

   Color representations are NOT in a common
   coordinate system, but each embeds an abstract
   color manifold differently.

   Like different charts on a manifold:
   Individual charts well-defined ✓
   Global atlas ill-defined ✗

╔════════════════════════════════════════════════════════════╗
║  Key: Individual manifolds have distinct topological       ║
║       signatures. Averaging destroys this structure!       ║
╚════════════════════════════════════════════════════════════╝
"""

ax6.text(0.05, 0.98, summary_text, transform=ax6.transAxes,
         fontsize=9, va='top', ha='left', family='monospace',
         bbox=dict(boxstyle='round', facecolor='lavender', alpha=0.3))

# ============================================================================
# Overall title
# ============================================================================
fig.suptitle('Topological Perspective on Color Vision Deficiency Analysis\n' +
             'Manifolds, Isometries, and Individual Geometric Signatures',
             fontsize=16, fontweight='bold', y=0.995)

plt.tight_layout(rect=[0, 0, 1, 0.99])

# Save
output_dir = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/results/group_level')
output_file = output_dir / 'topology_perspective.png'
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print(f"\n✅ Topology visualization saved: {output_file}")

plt.close()

print("\n" + "="*70)
print("TOPOLOGY VISUALIZATION COMPLETE!")
print("="*70)
