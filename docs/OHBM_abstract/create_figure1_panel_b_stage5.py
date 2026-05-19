#!/usr/bin/env python3
"""
Create Figure 1 Panel B - Stage 5: Forward Encoding Model with Circular Color Space
Shows the circular reconstruction visualization matching stimulus display style
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch
from matplotlib.collections import PatchCollection
import matplotlib.patches as mpatches
from pathlib import Path

# Set style
plt.rcParams['font.family'] = 'Arial'
plt.rcParams['font.size'] = 10

# Directories
BASE_DIR = Path("/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis")
OUTPUT_DIR = BASE_DIR / "docs/OHBM_abstract/figures"
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

# 8 stimulus colors (evenly spaced around color wheel)
stimulus_angles = np.array([0, 45, 90, 135, 180, 225, 270, 315])  # degrees
stimulus_colors_rgb = [
    '#FF0000',  # Red (0°)
    '#FF7F00',  # Orange (45°)
    '#FFFF00',  # Yellow (90°)
    '#7FFF00',  # Yellow-green (135°)
    '#00FF00',  # Green (180°)
    '#00FFFF',  # Cyan (225°)
    '#0000FF',  # Blue (270°)
    '#FF00FF',  # Magenta (315°)
]

def create_circular_reconstruction_example():
    """
    Create circular color space showing reconstruction example
    - Outer perimeter: Filled circles (presented colors)
    - Inner region: Open circles (predicted colors)
    - Arrows showing reconstruction error
    - Example: 90° predicted error
    """
    print("\n[Stage 5] Creating circular reconstruction visualization...")

    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(-1.5, 1.5)

    # Draw outer circle (perimeter)
    outer_circle = Circle((0, 0), 1.0, fill=False, edgecolor='black', linewidth=2)
    ax.add_patch(outer_circle)

    # Add degree labels
    degree_labels = [0, 45, 90, 135, 180, 225, 270, 315]
    for angle in degree_labels:
        rad = np.radians(angle)
        x = 1.15 * np.cos(rad)
        y = 1.15 * np.sin(rad)
        ax.text(x, y, f'{angle}°', ha='center', va='center',
                fontsize=10, weight='bold')

    # Example reconstruction errors (simulate some predictions)
    # For demonstration, we'll show some with good reconstruction,
    # some with moderate error, and highlight one with ~90° error
    np.random.seed(42)
    prediction_errors = np.array([15, 10, 90, 20, 12, 15, 18, 25])  # degrees

    # Calculate predicted angles
    predicted_angles = stimulus_angles + prediction_errors

    # Plot each stimulus and its prediction
    for i, (stim_angle, pred_angle, color) in enumerate(
        zip(stimulus_angles, predicted_angles, stimulus_colors_rgb)):

        # Convert to radians
        stim_rad = np.radians(stim_angle)
        pred_rad = np.radians(pred_angle)

        # Stimulus position (on perimeter, radius=1.0)
        stim_x = 1.0 * np.cos(stim_rad)
        stim_y = 1.0 * np.sin(stim_rad)

        # Prediction position (inner, radius=0.6-0.8 depending on error)
        pred_radius = 0.7 - (prediction_errors[i] / 180) * 0.2  # Smaller radius for larger error
        pred_x = pred_radius * np.cos(pred_rad)
        pred_y = pred_radius * np.sin(pred_rad)

        # Draw stimulus (filled circle on perimeter)
        stim_circle = Circle((stim_x, stim_y), 0.08, facecolor=color,
                            edgecolor='black', linewidth=2, zorder=3)
        ax.add_patch(stim_circle)

        # Draw prediction (open circle inside)
        pred_circle = Circle((pred_x, pred_y), 0.06, facecolor='white',
                            edgecolor=color, linewidth=2.5, zorder=2)
        ax.add_patch(pred_circle)

        # Draw arrow from stimulus to prediction
        arrow = FancyArrowPatch((stim_x, stim_y), (pred_x, pred_y),
                               arrowstyle='->', mutation_scale=15,
                               linewidth=1.5, color='gray', alpha=0.7,
                               zorder=1)
        ax.add_patch(arrow)

        # Highlight the 90° error example (index 2, at 90° stimulus)
        if i == 2:
            # Larger arrow
            highlight_arrow = FancyArrowPatch((stim_x, stim_y), (pred_x, pred_y),
                                             arrowstyle='->', mutation_scale=20,
                                             linewidth=3, color='red',
                                             zorder=4)
            ax.add_patch(highlight_arrow)

            # Annotation
            mid_x = (stim_x + pred_x) / 2
            mid_y = (stim_y + pred_y) / 2
            ax.annotate('90° predicted\nerror',
                       xy=(pred_x, pred_y), xytext=(mid_x - 0.4, mid_y + 0.3),
                       fontsize=11, weight='bold', color='red',
                       arrowprops=dict(arrowstyle='->', color='red', lw=2),
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                                edgecolor='red', linewidth=2))

    # Add legend
    legend_elements = [
        mpatches.Patch(facecolor='lightblue', edgecolor='black', linewidth=2,
                      label='Presented color (perimeter)'),
        mpatches.Patch(facecolor='white', edgecolor='gray', linewidth=2,
                      label='Predicted color (inner)'),
        mpatches.FancyArrow(0, 0, 0.1, 0, width=0.05, head_width=0.1,
                           head_length=0.05, fc='gray', ec='gray',
                           label='Reconstruction error')
    ]

    # Title
    ax.set_title('Forward Encoding Model:\nCircular Color Space Reconstruction',
                fontsize=14, weight='bold', pad=20)

    # Add outputs annotation
    fig.text(0.5, 0.05, 'Outputs: Classification Accuracy & Reconstruction Error',
            ha='center', fontsize=12, weight='bold',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow',
                     edgecolor='black', linewidth=2))

    plt.tight_layout(rect=[0, 0.08, 1, 1])
    output_path = OUTPUT_DIR / 'figure1_panel_b_stage5_circular.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_path}")
    plt.close()


def create_side_by_side_comparison():
    """
    Create comparison showing:
    - Left: Basis functions (6 half-wave rectified sinusoids)
    - Right: Circular reconstruction example
    """
    print("\n[Stage 5] Creating complete Stage 5 visualization...")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

    # ========== LEFT: Basis Functions ==========
    ax1.set_title('Forward Encoding Model:\nBasis Functions', fontsize=14, weight='bold')

    # 6 basis functions (half-wave rectified sinusoids)
    angles = np.linspace(0, 360, 100)
    basis_centers = np.linspace(0, 300, 6)

    for i, center in enumerate(basis_centers):
        # Half-wave rectified sinusoid
        response = np.maximum(0, np.cos(np.radians(angles - center)))
        ax1.plot(angles, response + i*0.3, linewidth=2, label=f'Basis {i+1} (center={center:.0f}°)')

    ax1.set_xlabel('Color Angle (degrees)', fontsize=12, weight='bold')
    ax1.set_ylabel('Response (offset for visualization)', fontsize=12, weight='bold')
    ax1.set_xlim(0, 360)
    ax1.set_xticks([0, 90, 180, 270, 360])
    ax1.legend(loc='upper right', fontsize=9)
    ax1.grid(True, alpha=0.3)
    ax1.text(180, -0.2, 'Leave-one-run-out Cross-Validation', ha='center',
            fontsize=11, style='italic')

    # ========== RIGHT: Circular Reconstruction ==========
    ax2.set_aspect('equal')
    ax2.axis('off')
    ax2.set_xlim(-1.5, 1.5)
    ax2.set_ylim(-1.5, 1.5)
    ax2.set_title('Circular Color Space\nReconstruction Example', fontsize=14, weight='bold')

    # Draw outer circle
    outer_circle = Circle((0, 0), 1.0, fill=False, edgecolor='black', linewidth=2)
    ax2.add_patch(outer_circle)

    # Degree labels
    for angle in [0, 45, 90, 135, 180, 225, 270, 315]:
        rad = np.radians(angle)
        x = 1.15 * np.cos(rad)
        y = 1.15 * np.sin(rad)
        ax2.text(x, y, f'{angle}°', ha='center', va='center',
                fontsize=10, weight='bold')

    # Example predictions
    np.random.seed(42)
    prediction_errors = np.array([15, 10, 90, 20, 12, 15, 18, 25])
    predicted_angles = stimulus_angles + prediction_errors

    for i, (stim_angle, pred_angle, color) in enumerate(
        zip(stimulus_angles, predicted_angles, stimulus_colors_rgb)):

        stim_rad = np.radians(stim_angle)
        pred_rad = np.radians(pred_angle)

        stim_x = 1.0 * np.cos(stim_rad)
        stim_y = 1.0 * np.sin(stim_rad)

        pred_radius = 0.7 - (prediction_errors[i] / 180) * 0.2
        pred_x = pred_radius * np.cos(pred_rad)
        pred_y = pred_radius * np.sin(pred_rad)

        # Stimulus (filled)
        stim_circle = Circle((stim_x, stim_y), 0.08, facecolor=color,
                            edgecolor='black', linewidth=2, zorder=3)
        ax2.add_patch(stim_circle)

        # Prediction (open)
        pred_circle = Circle((pred_x, pred_y), 0.06, facecolor='white',
                            edgecolor=color, linewidth=2.5, zorder=2)
        ax2.add_patch(pred_circle)

        # Arrow
        arrow = FancyArrowPatch((stim_x, stim_y), (pred_x, pred_y),
                               arrowstyle='->', mutation_scale=15,
                               linewidth=1.5, color='gray', alpha=0.7,
                               zorder=1)
        ax2.add_patch(arrow)

        # Highlight 90° error
        if i == 2:
            highlight_arrow = FancyArrowPatch((stim_x, stim_y), (pred_x, pred_y),
                                             arrowstyle='->', mutation_scale=20,
                                             linewidth=3, color='red', zorder=4)
            ax2.add_patch(highlight_arrow)

            mid_x = (stim_x + pred_x) / 2
            mid_y = (stim_y + pred_y) / 2
            ax2.annotate('90° error\nexample',
                       xy=(pred_x, pred_y), xytext=(mid_x - 0.4, mid_y + 0.3),
                       fontsize=11, weight='bold', color='red',
                       arrowprops=dict(arrowstyle='->', color='red', lw=2),
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                                edgecolor='red', linewidth=2))

    plt.suptitle('Panel B - Stage 5: Forward Encoding Model & Reconstruction',
                fontsize=16, weight='bold', y=0.98)

    # Add outputs
    fig.text(0.5, 0.02, 'Outputs: Classification Accuracy & Reconstruction Error',
            ha='center', fontsize=12, weight='bold',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow',
                     edgecolor='black', linewidth=2))

    plt.tight_layout(rect=[0, 0.05, 1, 0.96])
    output_path = OUTPUT_DIR / 'figure1_panel_b_stage5_complete.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_path}")
    plt.close()


def main():
    print("="*70)
    print("Creating Figure 1 Panel B - Stage 5 Visualization")
    print("="*70)

    # Create both versions
    create_circular_reconstruction_example()
    create_side_by_side_comparison()

    print("\n" + "="*70)
    print("SUCCESS! Figure 1 Panel B Stage 5 created:")
    print(f"  - Circular only: {OUTPUT_DIR}/figure1_panel_b_stage5_circular.png")
    print(f"  - Complete:      {OUTPUT_DIR}/figure1_panel_b_stage5_complete.png")
    print("="*70)


if __name__ == "__main__":
    main()
