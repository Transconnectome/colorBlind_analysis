#!/usr/bin/env python3
"""
Procrustes 개념 설명 Figure 생성
================================

Procrustes analysis의 핵심 개념을 시각적으로 설명하는 figure 생성
- Translation (평행이동)
- Scaling (크기 조정)
- Rotation (회전)
- Before/After 비교
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyArrowPatch
from mpl_toolkits.mplot3d import Axes3D

# Set up matplotlib with English fonts
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False


def create_shape_data():
    """Create two simple shapes for demonstration"""
    # Shape 1: Original "L" shape
    shape1 = np.array([
        [0, 0],
        [3, 0],
        [3, 1],
        [1, 1],
        [1, 3],
        [0, 3]
    ])

    # Shape 2: Same L shape but translated, scaled, and rotated
    # First translate
    shape2 = shape1 + np.array([5, 2])

    # Then scale
    shape2 = shape2 * 0.7

    # Then rotate by 30 degrees
    theta = np.radians(30)
    rotation_matrix = np.array([
        [np.cos(theta), -np.sin(theta)],
        [np.sin(theta), np.cos(theta)]
    ])
    center = shape2.mean(axis=0)
    shape2 = (shape2 - center) @ rotation_matrix.T + center + np.array([2, -1])

    return shape1, shape2


def procrustes_simple(X, Y):
    """
    Simple Procrustes alignment

    Returns aligned Y to match X
    """
    # 1. Center both shapes (Translation)
    X_center = X.mean(axis=0)
    Y_center = Y.mean(axis=0)

    X_centered = X - X_center
    Y_centered = Y - Y_center

    # 2. Normalize (Scaling)
    X_norm = np.linalg.norm(X_centered)
    Y_norm = np.linalg.norm(Y_centered)

    X_normalized = X_centered / X_norm
    Y_normalized = Y_centered / Y_norm

    # 3. Find optimal rotation (SVD)
    U, S, Vt = np.linalg.svd(Y_normalized.T @ X_normalized)
    R = U @ Vt

    # 4. Apply transformation
    Y_aligned = Y_normalized @ R

    # Scale back to X's scale
    Y_aligned = Y_aligned * X_norm + X_center

    return Y_aligned, X_centered, Y_centered, X_normalized, Y_normalized


def create_procrustes_concept_figure():
    """Create comprehensive Procrustes concept explanation figure"""

    fig = plt.figure(figsize=(20, 12))

    # Main title
    fig.suptitle('Procrustes Analysis Concept',
                 fontsize=20, fontweight='bold', y=0.98)

    # Create shape data
    shape_X, shape_Y_original = create_shape_data()
    shape_Y_aligned, X_cent, Y_cent, X_norm, Y_norm = procrustes_simple(shape_X, shape_Y_original)

    # === Row 1: Original Shapes ===
    ax1 = plt.subplot(2, 4, 1)
    ax1.plot(shape_X[:, 0], shape_X[:, 1], 'bo-', linewidth=2, markersize=8, label='Shape X (HC)')
    ax1.fill(shape_X[:, 0], shape_X[:, 1], 'blue', alpha=0.2)
    ax1.set_title('Reference Shape (HC Group)', fontsize=13, fontweight='bold')
    ax1.set_xlabel('Dimension 1')
    ax1.set_ylabel('Dimension 2')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.axis('equal')

    ax2 = plt.subplot(2, 4, 2)
    ax2.plot(shape_Y_original[:, 0], shape_Y_original[:, 1], 'ro-',
             linewidth=2, markersize=8, label='Shape Y (CVD Subject)')
    ax2.fill(shape_Y_original[:, 0], shape_Y_original[:, 1], 'red', alpha=0.2)
    ax2.set_title('Target Shape (CVD Subject)', fontsize=13, fontweight='bold')
    ax2.set_xlabel('Dimension 1')
    ax2.set_ylabel('Dimension 2')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.axis('equal')

    # === Overlay: Before alignment ===
    ax3 = plt.subplot(2, 4, 3)
    ax3.plot(shape_X[:, 0], shape_X[:, 1], 'bo-', linewidth=2, markersize=8, label='HC (Reference)')
    ax3.fill(shape_X[:, 0], shape_X[:, 1], 'blue', alpha=0.2)
    ax3.plot(shape_Y_original[:, 0], shape_Y_original[:, 1], 'ro-',
             linewidth=2, markersize=8, label='CVD (Original)')
    ax3.fill(shape_Y_original[:, 0], shape_Y_original[:, 1], 'red', alpha=0.2)
    ax3.set_title('Before Alignment', fontsize=13, fontweight='bold', color='red')
    ax3.set_xlabel('Dimension 1')
    ax3.set_ylabel('Dimension 2')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    ax3.axis('equal')

    # Add arrow showing misalignment
    ax3.annotate('', xy=(shape_X[0, 0], shape_X[0, 1]),
                xytext=(shape_Y_original[0, 0], shape_Y_original[0, 1]),
                arrowprops=dict(arrowstyle='<->', color='purple', lw=2, linestyle='dashed'))
    ax3.text((shape_X[0, 0] + shape_Y_original[0, 0])/2,
            (shape_X[0, 1] + shape_Y_original[0, 1])/2 + 0.5,
            'Large\nMismatch', ha='center', fontsize=10, color='purple', fontweight='bold')

    # === Overlay: After alignment ===
    ax4 = plt.subplot(2, 4, 4)
    ax4.plot(shape_X[:, 0], shape_X[:, 1], 'bo-', linewidth=2, markersize=8, label='HC (Reference)')
    ax4.fill(shape_X[:, 0], shape_X[:, 1], 'blue', alpha=0.2)
    ax4.plot(shape_Y_aligned[:, 0], shape_Y_aligned[:, 1], 'go-',
             linewidth=2, markersize=8, label='CVD (Aligned)')
    ax4.fill(shape_Y_aligned[:, 0], shape_Y_aligned[:, 1], 'green', alpha=0.2)
    ax4.set_title('After Procrustes Alignment', fontsize=13, fontweight='bold', color='green')
    ax4.set_xlabel('Dimension 1')
    ax4.set_ylabel('Dimension 2')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    ax4.axis('equal')

    # Add arrow showing remaining difference
    dist = np.linalg.norm(shape_X[0] - shape_Y_aligned[0])
    ax4.annotate('', xy=(shape_X[0, 0], shape_X[0, 1]),
                xytext=(shape_Y_aligned[0, 0], shape_Y_aligned[0, 1]),
                arrowprops=dict(arrowstyle='<->', color='orange', lw=2))
    ax4.text((shape_X[0, 0] + shape_Y_aligned[0, 0])/2,
            (shape_X[0, 1] + shape_Y_aligned[0, 1])/2 + 0.3,
            'Disparity\n(Remaining)', ha='center', fontsize=9,
            color='orange', fontweight='bold')

    # === Row 2: Step-by-step transformation ===

    # Step 1: Translation
    ax5 = plt.subplot(2, 4, 5)
    Y_translated = shape_Y_original - shape_Y_original.mean(axis=0)
    ax5.plot(Y_translated[:, 0], Y_translated[:, 1], 'ro-', linewidth=2, markersize=8)
    ax5.fill(Y_translated[:, 0], Y_translated[:, 1], 'red', alpha=0.2)
    ax5.axhline(0, color='k', linestyle='--', alpha=0.3)
    ax5.axvline(0, color='k', linestyle='--', alpha=0.3)
    ax5.scatter([0], [0], s=200, c='gold', marker='*', edgecolors='black', linewidths=2,
               label='Centroid', zorder=5)
    ax5.set_title('Step 1: Translation\n(Center to Origin)', fontsize=12, fontweight='bold')
    ax5.set_xlabel('Dimension 1')
    ax5.set_ylabel('Dimension 2')
    ax5.legend()
    ax5.grid(True, alpha=0.3)
    ax5.axis('equal')

    # Step 2: Scaling
    ax6 = plt.subplot(2, 4, 6)
    # Show both original and scaled
    ax6.plot(Y_cent[:, 0], Y_cent[:, 1], 'r--o', linewidth=1.5, markersize=6,
            alpha=0.5, label='Before Scaling')
    ax6.plot(Y_norm[:, 0], Y_norm[:, 1], 'ro-', linewidth=2, markersize=8,
            label='After Scaling')
    ax6.fill(Y_norm[:, 0], Y_norm[:, 1], 'red', alpha=0.2)
    ax6.set_title('Step 2: Scaling\n(Normalize Frobenius Norm)', fontsize=12, fontweight='bold')
    ax6.set_xlabel('Dimension 1')
    ax6.set_ylabel('Dimension 2')
    ax6.legend()
    ax6.grid(True, alpha=0.3)
    ax6.axis('equal')

    # Step 3: Rotation
    ax7 = plt.subplot(2, 4, 7)
    # Show target shape (X) and Y before/after rotation
    ax7.plot(X_norm[:, 0], X_norm[:, 1], 'bo-', linewidth=2, markersize=8,
            label='Target (HC)', alpha=0.5)
    ax7.fill(X_norm[:, 0], X_norm[:, 1], 'blue', alpha=0.1)

    ax7.plot(Y_norm[:, 0], Y_norm[:, 1], 'r--o', linewidth=1.5, markersize=6,
            alpha=0.5, label='Before Rotation')

    # Get aligned version in normalized space
    U, S, Vt = np.linalg.svd(Y_norm.T @ X_norm)
    R = U @ Vt
    Y_rotated = Y_norm @ R

    ax7.plot(Y_rotated[:, 0], Y_rotated[:, 1], 'go-', linewidth=2, markersize=8,
            label='After Rotation (SVD)')
    ax7.fill(Y_rotated[:, 0], Y_rotated[:, 1], 'green', alpha=0.2)

    ax7.set_title('Step 3: Rotation\n(SVD-based Optimal Rotation)', fontsize=12, fontweight='bold')
    ax7.set_xlabel('Dimension 1')
    ax7.set_ylabel('Dimension 2')
    ax7.legend()
    ax7.grid(True, alpha=0.3)
    ax7.axis('equal')

    # Step 4: Formula and interpretation
    ax8 = plt.subplot(2, 4, 8)
    ax8.axis('off')

    formula_text = """
    Procrustes Algorithm:

    1. Translation:
       X' = X - mean(X)
       Y' = Y - mean(Y)

    2. Scaling:
       X" = X' / ||X'||_F
       Y" = Y' / ||Y'||_F

    3. Rotation (SVD):
       U, Σ, V^T = SVD(Y"^T X")
       R = U V^T

    4. Apply:
       Y_aligned = Y" R

    5. Disparity:
       d = ||X" - Y_aligned||_F

    Interpretation:
    • d = 0: Perfect match
    • d < 0.1: Very similar
    • d > 0.5: Large difference

    Stability: s = 1 - d
    """

    ax8.text(0.05, 0.95, formula_text, transform=ax8.transAxes,
            fontsize=10, verticalalignment='top', family='monospace',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout(rect=[0, 0, 1, 0.97])

    # Save
    output_path = '/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/results/group_level/procrustes_concept.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_path}")
    plt.close()


def create_simple_procrustes_diagram():
    """Create a simpler, more intuitive diagram"""

    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('Procrustes Analysis: Simple Explanation',
                 fontsize=18, fontweight='bold')

    # Row 1: Conceptual explanation with simple shapes
    # Panel 1: Two different "brains"
    ax = axes[0, 0]
    brain1_x = [0, 1, 2, 2.5, 2, 1, 0]
    brain1_y = [0, 0.5, 0.8, 1, 1.2, 1.2, 0.8]

    brain2_x = np.array([3, 4, 5, 5.5, 5, 4, 3]) + 2
    brain2_y = np.array([0, 0.5, 0.8, 1, 1.2, 1.2, 0.8]) * 0.7 + 1.5

    ax.plot(brain1_x, brain1_y, 'b-o', linewidth=3, markersize=10, label='HC Brain')
    ax.fill(brain1_x, brain1_y, 'blue', alpha=0.2)

    ax.plot(brain2_x, brain2_y, 'r-o', linewidth=3, markersize=10, label='CVD Brain')
    ax.fill(brain2_x, brain2_y, 'red', alpha=0.2)

    ax.set_title('Problem: Different Position/Size/Orientation',
                fontsize=14, fontweight='bold')
    ax.legend(fontsize=12)
    ax.axis('equal')
    ax.set_xlim(-1, 9)
    ax.set_ylim(-1, 4)
    ax.grid(True, alpha=0.3)

    # Panel 2: Arrow showing transformation
    ax = axes[0, 1]
    # Removed textbox per user request

    ax.annotate('', xy=(0.5, 0.3), xytext=(0.5, 0.8),
               arrowprops=dict(arrowstyle='->', lw=5, color='darkblue'))

    ax.text(0.5, 0.15, '1. Move to same center\n2. Resize to same scale\n3. Rotate to match',
           ha='center', va='center', fontsize=14,
           bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')

    # Panel 3: Aligned result
    ax = axes[0, 2]
    # Show both overlapping
    ax.plot(brain1_x, brain1_y, 'b-o', linewidth=3, markersize=10, label='HC Brain', alpha=0.7)
    ax.fill(brain1_x, brain1_y, 'blue', alpha=0.2)

    # Aligned CVD (approximately)
    brain2_aligned_x = np.array([3, 4, 5, 5.5, 5, 4, 3]) - 3.75
    brain2_aligned_y = np.array([0, 0.5, 0.8, 1, 1.2, 1.2, 0.8]) - 0.1

    ax.plot(brain2_aligned_x, brain2_aligned_y, 'g-o', linewidth=3, markersize=10,
           label='CVD Brain (Aligned)', alpha=0.7)
    ax.fill(brain2_aligned_x, brain2_aligned_y, 'green', alpha=0.2)

    ax.set_title('Result: Same Coordinate System',
                fontsize=14, fontweight='bold', color='green')
    ax.legend(fontsize=12)
    ax.axis('equal')
    ax.set_xlim(-1, 3)
    ax.set_ylim(-1, 2)
    ax.grid(True, alpha=0.3)

    # Row 2: Application to our study
    # Panel 4: Color representation
    ax = axes[1, 0]

    # Draw color wheel representation
    angles = np.linspace(0, 2*np.pi, 9)
    x_circle = np.cos(angles)
    y_circle = np.sin(angles)

    colors_hc = ['red', 'orange', 'yellow', 'lime', 'cyan', 'blue', 'purple', 'magenta']
    for i in range(8):
        ax.plot([0, x_circle[i]], [0, y_circle[i]], 'b-', linewidth=2, alpha=0.5)
        ax.scatter(x_circle[i], y_circle[i], s=300, c=colors_hc[i],
                  edgecolors='blue', linewidths=3, zorder=5)

    ax.scatter(0, 0, s=500, c='white', marker='o', edgecolors='black', linewidths=3)
    ax.text(0, 0, 'HC', ha='center', va='center', fontsize=14, fontweight='bold')

    ax.set_title('HC Color Representation\n(8 colors in brain space)',
                fontsize=13, fontweight='bold')
    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(-1.5, 1.5)
    ax.axis('equal')
    ax.grid(True, alpha=0.3)

    # Panel 5: CVD representation (distorted)
    ax = axes[1, 1]

    # Distort the circle (compress red-green axis)
    x_circle_cvd = x_circle * np.array([1, 0.9, 0.7, 0.6, 0.7, 0.9, 1, 1, 1])
    y_circle_cvd = y_circle * np.array([0.6, 0.7, 0.9, 1, 1.1, 1.1, 1, 0.8, 0.6])

    # Also shift it
    x_circle_cvd = x_circle_cvd + 0.3
    y_circle_cvd = y_circle_cvd - 0.2

    for i in range(8):
        ax.plot([0.3, x_circle_cvd[i]], [-0.2, y_circle_cvd[i]], 'r-', linewidth=2, alpha=0.5)
        ax.scatter(x_circle_cvd[i], y_circle_cvd[i], s=300, c=colors_hc[i],
                  edgecolors='red', linewidths=3, zorder=5)

    ax.scatter(0.3, -0.2, s=500, c='white', marker='o', edgecolors='black', linewidths=3)
    ax.text(0.3, -0.2, 'CVD', ha='center', va='center', fontsize=14, fontweight='bold')

    ax.set_title('CVD Color Representation\n(Distorted + Shifted)',
                fontsize=13, fontweight='bold')
    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(-1.5, 1.5)
    ax.axis('equal')
    ax.grid(True, alpha=0.3)

    # Panel 6: Aligned and systematic difference
    ax = axes[1, 2]

    # After alignment, CVD should be close to HC but with systematic pattern
    x_circle_cvd_aligned = x_circle_cvd - 0.3
    y_circle_cvd_aligned = y_circle_cvd + 0.2

    for i in range(8):
        # Draw HC
        ax.plot([0, x_circle[i]], [0, y_circle[i]], 'b-', linewidth=2, alpha=0.3)
        ax.scatter(x_circle[i], y_circle[i], s=300, c=colors_hc[i],
                  edgecolors='blue', linewidths=2, alpha=0.5, zorder=3)

        # Draw CVD aligned
        ax.plot([0, x_circle_cvd_aligned[i]], [0, y_circle_cvd_aligned[i]],
               'g-', linewidth=2, alpha=0.5)
        ax.scatter(x_circle_cvd_aligned[i], y_circle_cvd_aligned[i], s=300, c=colors_hc[i],
                  edgecolors='green', linewidths=3, zorder=5)

        # Draw difference arrow
        ax.annotate('', xy=(x_circle[i], y_circle[i]),
                   xytext=(x_circle_cvd_aligned[i], y_circle_cvd_aligned[i]),
                   arrowprops=dict(arrowstyle='->', lw=2, color='purple', alpha=0.7))

    ax.scatter(0, 0, s=500, c='white', marker='o', edgecolors='black', linewidths=3)
    ax.text(0, 0, 'Aligned', ha='center', va='center', fontsize=11, fontweight='bold')

    ax.set_title('After Alignment:\nSystematic Difference (T) Visible',
                fontsize=13, fontweight='bold', color='purple')
    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(-1.5, 1.5)
    ax.axis('equal')
    ax.grid(True, alpha=0.3)

    plt.tight_layout(rect=[0, 0, 1, 0.97])

    # Save
    output_path = '/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/results/group_level/procrustes_concept_simple.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_path}")
    plt.close()


if __name__ == '__main__':
    print("Creating Procrustes concept figures...")
    print("\n1. Technical version...")
    create_procrustes_concept_figure()

    print("\n2. Simple explanation version...")
    create_simple_procrustes_diagram()

    print("\n✓ Done! Figures saved to results/group_level/")
