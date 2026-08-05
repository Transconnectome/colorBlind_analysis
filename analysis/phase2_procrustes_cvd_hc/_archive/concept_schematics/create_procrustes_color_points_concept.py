#!/usr/bin/env python3
"""
Procrustes Concept: Color-labeled Points Visualization
======================================================

HC subjects끼리 정렬하는 과정을 8개 color points로 시각화
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch
from mpl_toolkits.mplot3d import proj3d

# Set up matplotlib
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

# 8 colors for visualization
COLORS_RGB = [
    '#FF0000',  # Red (0°)
    '#FF8000',  # Orange (45°)
    '#FFFF00',  # Yellow (90°)
    '#80FF00',  # Lime (135°)
    '#00FFFF',  # Cyan (180°)
    '#0080FF',  # Blue (225°)
    '#8000FF',  # Purple (270°)
    '#FF00FF',  # Magenta (315°)
]

COLOR_NAMES = ['Red', 'Orange', 'Yellow', 'Lime', 'Cyan', 'Blue', 'Purple', 'Magenta']


def create_synthetic_color_pattern(seed=42, noise_level=0.1):
    """Create synthetic 8-color pattern in 2D space"""
    np.random.seed(seed)

    # Create circular arrangement of 8 colors
    angles = np.linspace(0, 2*np.pi, 9)[:-1]  # 8 points

    # Base pattern (unit circle)
    x = np.cos(angles)
    y = np.sin(angles)

    # Add slight noise
    x += np.random.randn(8) * noise_level
    y += np.random.randn(8) * noise_level

    pattern = np.column_stack([x, y])

    return pattern


def transform_pattern(pattern, translation=(0, 0), rotation=0, scale=1.0):
    """Apply geometric transformation to pattern"""
    # Scale
    pattern_scaled = pattern * scale

    # Rotate
    theta = np.radians(rotation)
    R = np.array([
        [np.cos(theta), -np.sin(theta)],
        [np.sin(theta), np.cos(theta)]
    ])
    pattern_rotated = pattern_scaled @ R.T

    # Translate
    pattern_transformed = pattern_rotated + np.array(translation)

    return pattern_transformed


def procrustes_align_2d(reference, target):
    """Procrustes alignment in 2D"""
    # Center
    ref_center = reference.mean(axis=0)
    tgt_center = target.mean(axis=0)

    ref_centered = reference - ref_center
    tgt_centered = target - tgt_center

    # Scale
    ref_scale = np.linalg.norm(ref_centered)
    tgt_scale = np.linalg.norm(tgt_centered)

    ref_normalized = ref_centered / ref_scale
    tgt_normalized = tgt_centered / tgt_scale

    # Rotation (SVD)
    H = tgt_normalized.T @ ref_normalized
    U, S, Vt = np.linalg.svd(H)
    R = U @ Vt

    # Apply to get aligned version
    tgt_aligned = tgt_normalized @ R

    # Scale back to reference scale
    tgt_aligned = tgt_aligned * ref_scale + ref_center

    # Calculate disparity
    disparity = np.sqrt(np.sum((ref_normalized - tgt_normalized @ R)**2) / np.sum(ref_normalized**2))

    return tgt_aligned, disparity


def plot_color_points(ax, pattern, colors, labels=True, alpha=1.0, s=200, linewidths=2):
    """Plot 8 color points"""
    for i in range(8):
        ax.scatter(pattern[i, 0], pattern[i, 1],
                  c=colors[i], s=s, alpha=alpha,
                  edgecolors='black', linewidths=linewidths, zorder=5)

        if labels:
            ax.text(pattern[i, 0], pattern[i, 1] + 0.15,
                   COLOR_NAMES[i],
                   ha='center', va='bottom', fontsize=8, fontweight='bold')


def create_hc_alignment_concept_figure():
    """Create comprehensive HC-HC alignment concept figure"""

    fig = plt.figure(figsize=(20, 14))
    fig.suptitle('Procrustes Alignment: HC Subjects with Color-Labeled Points',
                 fontsize=18, fontweight='bold', y=0.98)

    # Create synthetic data
    # Subject 1 (Reference)
    subj1 = create_synthetic_color_pattern(seed=42, noise_level=0.05)

    # Subject 2 (different coordinate system)
    subj2_base = create_synthetic_color_pattern(seed=43, noise_level=0.08)
    subj2_original = transform_pattern(subj2_base,
                                       translation=(3, 2),
                                       rotation=45,
                                       scale=0.7)

    # Subject 3 (another different system)
    subj3_base = create_synthetic_color_pattern(seed=44, noise_level=0.06)
    subj3_original = transform_pattern(subj3_base,
                                       translation=(-2, 3),
                                       rotation=-30,
                                       scale=1.2)

    # Align subjects
    subj2_aligned, disp2 = procrustes_align_2d(subj1, subj2_original)
    subj3_aligned, disp3 = procrustes_align_2d(subj1, subj3_original)

    # === Row 1: Individual subjects in their own coordinate systems ===

    # Panel 1: Subject 1 (Reference)
    ax1 = plt.subplot(3, 4, 1)
    plot_color_points(ax1, subj1, COLORS_RGB, labels=True)
    ax1.axhline(0, color='gray', linestyle='--', alpha=0.3, linewidth=1)
    ax1.axvline(0, color='gray', linestyle='--', alpha=0.3, linewidth=1)
    ax1.set_xlim(-2, 2)
    ax1.set_ylim(-2, 2)
    ax1.set_aspect('equal')
    ax1.set_title('Subject 1 (Reference HC)\nOriginal Coordinate System',
                  fontsize=13, fontweight='bold')
    ax1.set_xlabel('Dimension 1')
    ax1.set_ylabel('Dimension 2')
    ax1.grid(True, alpha=0.2)

    # Panel 2: Subject 2 (Original)
    ax2 = plt.subplot(3, 4, 2)
    plot_color_points(ax2, subj2_original, COLORS_RGB, labels=True)
    ax2.axhline(0, color='gray', linestyle='--', alpha=0.3, linewidth=1)
    ax2.axvline(0, color='gray', linestyle='--', alpha=0.3, linewidth=1)
    ax2.set_xlim(-2, 6)
    ax2.set_ylim(-2, 5)
    ax2.set_aspect('equal')
    ax2.set_title('Subject 2 (HC)\nDifferent Coordinate System',
                  fontsize=13, fontweight='bold', color='darkred')
    ax2.set_xlabel('Dimension 1')
    ax2.set_ylabel('Dimension 2')
    ax2.grid(True, alpha=0.2)

    # Panel 3: Subject 3 (Original)
    ax3 = plt.subplot(3, 4, 3)
    plot_color_points(ax3, subj3_original, COLORS_RGB, labels=True)
    ax3.axhline(0, color='gray', linestyle='--', alpha=0.3, linewidth=1)
    ax3.axvline(0, color='gray', linestyle='--', alpha=0.3, linewidth=1)
    ax3.set_xlim(-4, 2)
    ax3.set_ylim(-2, 5)
    ax3.set_aspect('equal')
    ax3.set_title('Subject 3 (HC)\nDifferent Coordinate System',
                  fontsize=13, fontweight='bold', color='darkred')
    ax3.set_xlabel('Dimension 1')
    ax3.set_ylabel('Dimension 2')
    ax3.grid(True, alpha=0.2)

    # Panel 4: Problem statement
    ax4 = plt.subplot(3, 4, 4)
    ax4.axis('off')

    problem_text = """
    Problem:

    • Each HC subject has color
      representations in their own
      coordinate system

    • Same colors (Red, Blue, etc.)
      at different locations

    • Cannot directly compare:
      - Different centers
      - Different scales
      - Different orientations

    Solution:

    • Use Procrustes alignment
    • Align all to Subject 1
      (reference coordinate system)
    """

    ax4.text(0.1, 0.95, problem_text, transform=ax4.transAxes,
            fontsize=11, verticalalignment='top', family='monospace',
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

    # === Row 2: Alignment process ===

    # Panel 5: Overlay before alignment
    ax5 = plt.subplot(3, 4, 5)

    # Plot all three subjects
    for i in range(8):
        ax5.scatter(subj1[i, 0], subj1[i, 1],
                   c=COLORS_RGB[i], s=200, alpha=0.7,
                   edgecolors='blue', linewidths=3, zorder=5,
                   label='Subj 1' if i == 0 else '')
        ax5.scatter(subj2_original[i, 0], subj2_original[i, 1],
                   c=COLORS_RGB[i], s=200, alpha=0.5,
                   edgecolors='red', linewidths=2, zorder=4,
                   label='Subj 2' if i == 0 else '')
        ax5.scatter(subj3_original[i, 0], subj3_original[i, 1],
                   c=COLORS_RGB[i], s=200, alpha=0.5,
                   edgecolors='green', linewidths=2, zorder=4,
                   label='Subj 3' if i == 0 else '')

    ax5.axhline(0, color='gray', linestyle='--', alpha=0.3, linewidth=1)
    ax5.axvline(0, color='gray', linestyle='--', alpha=0.3, linewidth=1)
    ax5.set_xlim(-4, 6)
    ax5.set_ylim(-2, 5)
    ax5.set_aspect('equal')
    ax5.set_title('Before Alignment\n(All subjects overlaid)',
                  fontsize=13, fontweight='bold', color='red')
    ax5.set_xlabel('Dimension 1')
    ax5.set_ylabel('Dimension 2')
    ax5.legend(loc='upper left', fontsize=9)
    ax5.grid(True, alpha=0.2)

    # Add text annotation
    ax5.text(0.5, 0.02, 'Large misalignment!', transform=ax5.transAxes,
            ha='center', fontsize=11, fontweight='bold', color='red',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    # Panel 6: Procrustes transformation
    ax6 = plt.subplot(3, 4, 6)
    ax6.axis('off')

    transform_text = """
    Procrustes Transformation:

    For each subject (2, 3, ...):

    1. Translation:
       Center = mean(8 color points)
       Shift to origin

    2. Scaling:
       Scale = ||centered points||
       Normalize to unit scale

    3. Rotation:
       Find R via SVD to minimize:
       ||Reference - Subject × R||²

    4. Apply:
       Aligned = Normalized × R
       Scale back to reference

    Result:
       • All subjects in Subject 1's
         coordinate system
       • Remaining difference =
         Disparity (d)
    """

    ax6.text(0.05, 0.95, transform_text, transform=ax6.transAxes,
            fontsize=10, verticalalignment='top', family='monospace',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))

    # Panel 7: Alignment step-by-step for Subject 2
    ax7 = plt.subplot(3, 4, 7)

    # Show intermediate steps
    subj2_centered = subj2_original - subj2_original.mean(axis=0)
    subj2_scaled = subj2_centered / np.linalg.norm(subj2_centered)

    # Plot
    plot_color_points(ax7, subj2_centered, COLORS_RGB, labels=False, alpha=0.4, s=100, linewidths=1)
    plot_color_points(ax7, subj2_scaled, COLORS_RGB, labels=False, alpha=0.7, s=150, linewidths=2)

    # Draw arrows
    for i in range(8):
        ax7.annotate('', xy=(subj2_scaled[i, 0], subj2_scaled[i, 1]),
                    xytext=(subj2_centered[i, 0], subj2_centered[i, 1]),
                    arrowprops=dict(arrowstyle='->', color='gray', lw=1.5, alpha=0.5))

    ax7.axhline(0, color='gray', linestyle='--', alpha=0.3, linewidth=1)
    ax7.axvline(0, color='gray', linestyle='--', alpha=0.3, linewidth=1)
    ax7.set_xlim(-1.5, 1.5)
    ax7.set_ylim(-1.5, 1.5)
    ax7.set_aspect('equal')
    ax7.set_title('Subject 2: Translation + Scaling',
                  fontsize=12, fontweight='bold')
    ax7.set_xlabel('Normalized Dimension 1')
    ax7.set_ylabel('Normalized Dimension 2')
    ax7.grid(True, alpha=0.2)

    # Panel 8: After rotation
    ax8 = plt.subplot(3, 4, 8)

    # Rotation visualization
    subj1_normalized = (subj1 - subj1.mean(axis=0)) / np.linalg.norm(subj1 - subj1.mean(axis=0))
    subj2_normalized = (subj2_original - subj2_original.mean(axis=0)) / np.linalg.norm(subj2_original - subj2_original.mean(axis=0))

    H = subj2_normalized.T @ subj1_normalized
    U, S, Vt = np.linalg.svd(H)
    R = U @ Vt
    subj2_rotated = subj2_normalized @ R

    # Plot
    plot_color_points(ax8, subj1_normalized, COLORS_RGB, labels=False, alpha=0.5, s=150, linewidths=2)
    plot_color_points(ax8, subj2_rotated, COLORS_RGB, labels=False, alpha=0.7, s=150, linewidths=2)

    # Draw correspondence lines
    for i in range(8):
        ax8.plot([subj1_normalized[i, 0], subj2_rotated[i, 0]],
                [subj1_normalized[i, 1], subj2_rotated[i, 1]],
                'k--', alpha=0.3, linewidth=1)

    ax8.axhline(0, color='gray', linestyle='--', alpha=0.3, linewidth=1)
    ax8.axvline(0, color='gray', linestyle='--', alpha=0.3, linewidth=1)
    ax8.set_xlim(-1.5, 1.5)
    ax8.set_ylim(-1.5, 1.5)
    ax8.set_aspect('equal')
    ax8.set_title('After Rotation (Aligned)',
                  fontsize=12, fontweight='bold', color='green')
    ax8.set_xlabel('Normalized Dimension 1')
    ax8.set_ylabel('Normalized Dimension 2')
    ax8.grid(True, alpha=0.2)

    # === Row 3: Final aligned results ===

    # Panel 9: All aligned subjects
    ax9 = plt.subplot(3, 4, 9)

    # Plot all three subjects (aligned)
    for i in range(8):
        ax9.scatter(subj1[i, 0], subj1[i, 1],
                   c=COLORS_RGB[i], s=200, alpha=0.8,
                   edgecolors='blue', linewidths=3, zorder=5,
                   marker='o', label='Subj 1' if i == 0 else '')
        ax9.scatter(subj2_aligned[i, 0], subj2_aligned[i, 1],
                   c=COLORS_RGB[i], s=150, alpha=0.6,
                   edgecolors='red', linewidths=2, zorder=4,
                   marker='s', label='Subj 2' if i == 0 else '')
        ax9.scatter(subj3_aligned[i, 0], subj3_aligned[i, 1],
                   c=COLORS_RGB[i], s=150, alpha=0.6,
                   edgecolors='green', linewidths=2, zorder=4,
                   marker='^', label='Subj 3' if i == 0 else '')

        # Draw correspondence lines
        ax9.plot([subj1[i, 0], subj2_aligned[i, 0]],
                [subj1[i, 1], subj2_aligned[i, 1]],
                'r--', alpha=0.2, linewidth=1)
        ax9.plot([subj1[i, 0], subj3_aligned[i, 0]],
                [subj1[i, 1], subj3_aligned[i, 1]],
                'g--', alpha=0.2, linewidth=1)

    ax9.axhline(0, color='gray', linestyle='--', alpha=0.3, linewidth=1)
    ax9.axvline(0, color='gray', linestyle='--', alpha=0.3, linewidth=1)
    ax9.set_xlim(-2, 2)
    ax9.set_ylim(-2, 2)
    ax9.set_aspect('equal')
    ax9.set_title('After Procrustes Alignment\n(All in Subject 1 coordinate system)',
                  fontsize=13, fontweight='bold', color='green')
    ax9.set_xlabel('Dimension 1')
    ax9.set_ylabel('Dimension 2')
    ax9.legend(loc='upper left', fontsize=9)
    ax9.grid(True, alpha=0.2)

    # Add text annotation
    ax9.text(0.5, 0.02, f'Disparities: Subj2={disp2:.3f}, Subj3={disp3:.3f}',
            transform=ax9.transAxes,
            ha='center', fontsize=10, fontweight='bold', color='green',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    # Panel 10: Color-specific comparison
    ax10 = plt.subplot(3, 4, 10)

    # Calculate distances for each color
    distances_subj2 = np.sqrt(np.sum((subj1 - subj2_aligned)**2, axis=1))
    distances_subj3 = np.sqrt(np.sum((subj1 - subj3_aligned)**2, axis=1))

    x = np.arange(8)
    width = 0.35

    bars1 = ax10.bar(x - width/2, distances_subj2, width,
                     color='red', alpha=0.7, label='Subj 2')
    bars2 = ax10.bar(x + width/2, distances_subj3, width,
                     color='green', alpha=0.7, label='Subj 3')

    ax10.set_xlabel('Color', fontsize=11)
    ax10.set_ylabel('Distance to Reference', fontsize=11)
    ax10.set_title('Color-specific Alignment Quality', fontsize=12, fontweight='bold')
    ax10.set_xticks(x)
    ax10.set_xticklabels([c[:3] for c in COLOR_NAMES], rotation=45)
    ax10.legend()
    ax10.grid(axis='y', alpha=0.3)

    # Panel 11: Disparity interpretation
    ax11 = plt.subplot(3, 4, 11)

    # Create color patches for legend
    for i, (color, name) in enumerate(zip(COLORS_RGB, COLOR_NAMES)):
        y_pos = 0.9 - i * 0.1

        # Color patch
        circle = mpatches.Circle((0.15, y_pos), 0.04,
                                transform=ax11.transAxes,
                                facecolor=color, edgecolor='black', linewidth=2)
        ax11.add_patch(circle)

        # Label
        ax11.text(0.25, y_pos, name, transform=ax11.transAxes,
                 va='center', fontsize=10, fontweight='bold')

    ax11.set_xlim(0, 1)
    ax11.set_ylim(0, 1)
    ax11.axis('off')
    ax11.set_title('Color Legend', fontsize=12, fontweight='bold')

    # Panel 12: Summary
    ax12 = plt.subplot(3, 4, 12)
    ax12.axis('off')

    summary_text = f"""
    Summary:

    ✓ Alignment Success
      • Subject 2: d = {disp2:.3f}
      • Subject 3: d = {disp3:.3f}

    Key Insights:

    1. Each HC subject has
       same 8 colors but in
       different coordinate
       systems

    2. Procrustes removes:
       • Position differences
       • Scale differences
       • Orientation differences

    3. Remaining disparity
       reflects true pattern
       differences

    4. Small disparity =
       Similar color structure

    Next Step:

    • Calculate HC mean
    • Compare CVD to HC mean
    • Find systematic
      difference (T)
    """

    ax12.text(0.05, 0.95, summary_text, transform=ax12.transAxes,
             fontsize=9.5, verticalalignment='top', family='monospace',
             bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))

    plt.tight_layout(rect=[0, 0, 1, 0.97])

    # Save
    output_path = '/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/results/group_level/procrustes_color_points_concept.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_path}")
    plt.close()


if __name__ == '__main__':
    print("Creating Procrustes color points concept figure...")
    create_hc_alignment_concept_figure()
    print("\n✓ Done!")
