#!/usr/bin/env python3
"""
Create Figure 2C - Permutation Methodology Visualization
Shows original labels vs permuted labels (Red/Green swap)
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

plt.rcParams['font.family'] = 'Arial'
plt.rcParams['font.size'] = 10

BASE_DIR = Path("/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis")
OUTPUT_DIR = BASE_DIR / "docs/OHBM_abstract/figures"

# CIELab color definitions from actual experiment
COLOR_LAB = {
    'color_1': [59.90, 62.69, 3.78],    # 0°: Red/Pink
    'color_2': [64.20, 49.20, 45.58],   # 45°: Orange
    'color_3': [57.27, 13.06, 41.69],   # 90°: Brown/Yellow
    'color_4': [69.08, -55.02, 47.38],  # 135°: Green
    'color_5': [74.61, -41.33, -4.89],  # 180°: Cyan
    'color_6': [69.14, -11.45, -40.91], # 225°: Blue
    'color_7': [60.68, 19.18, -54.13],  # 270°: Dark Blue
    'color_8': [60.17, 46.82, -40.31],  # 315°: Purple/Pink
}

def lab2rgb_accurate(L, a, b, clip=True):
    """
    CIELab → RGB accurate color space conversion
    """
    L, a, b = float(L), float(a), float(b)

    # Lab to XYZ
    y = (L + 16) / 116
    x = a / 500 + y
    z = y - b / 200

    xyz = np.array([x, y, z])
    xyz = np.where(xyz > 0.206893, xyz**3, (xyz - 16/116) / 7.787)
    xyz *= [0.95047, 1., 1.08883]  # D65 white point

    # XYZ to RGB (sRGB matrix)
    rgb = np.dot([[3.2406, -1.5372, -0.4986],
                  [-0.9689, 1.8758, 0.0415],
                  [0.0557, -0.2040, 1.0570]], xyz)

    # Gamma correction
    rgb = np.where(rgb <= 0.0031308, 12.92 * rgb, 1.055 * rgb**(1/2.4) - 0.055)

    if clip:
        rgb = np.clip(rgb, 0, 1)

    return tuple(rgb)

# Convert LAB colors to RGB
stimulus_colors = {}
color_names = ['Red', 'Orange', 'Yellow', 'Green', 'Cyan', 'Blue', 'DarkBlue', 'Purple']
for i, name in enumerate(color_names, 1):
    L, a, b = COLOR_LAB[f'color_{i}']
    stimulus_colors[name] = lab2rgb_accurate(L, a, b)

def create_permutation_methodology():
    """
    Create permutation methodology visualization
    - Left: Original predictions (matching ground truth)
    - Center: Ground truth labels
    - Right: Permuted predictions (Red <-> Green swapped)
    """
    print("\n[Figure 2C] Creating permutation methodology visualization...")

    # Create example trial sequence (10 trials)
    # Only Red and Green - show that HALF get permuted
    original_sequence = ['Red', 'Red', 'Green', 'Green', 'Red',
                        'Green', 'Red', 'Red', 'Green', 'Green']

    # Ground truth is same as original
    ground_truth = original_sequence.copy()

    # Permuted: swap Red <-> Green for HALF of trials (indices 0, 2, 4, 6, 8)
    # This shows that permutation is PARTIAL, not complete
    permuted_sequence = []
    swap_indices = [0, 2, 4, 6, 8]  # Half of the 10 trials
    for i, color in enumerate(original_sequence):
        if i in swap_indices:
            # Swap this trial
            if color == 'Red':
                permuted_sequence.append('Green')
            elif color == 'Green':
                permuted_sequence.append('Red')
        else:
            # Keep original
            permuted_sequence.append(color)

    n_trials = len(original_sequence)

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, n_trials + 2)
    ax.axis('off')

    # Column positions
    left_x = 2.0
    center_x = 5.0
    right_x = 8.0

    block_width = 0.8
    block_height = 0.8

    # Draw column titles
    ax.text(left_x, n_trials + 1.2, 'Original\nLabels',
            ha='center', va='center', fontsize=14, weight='bold')
    ax.text(center_x, n_trials + 1.2, 'Ground Truth\n(y)',
            ha='center', va='center', fontsize=14, weight='bold')
    ax.text(right_x, n_trials + 1.2, 'Permuted\nLabels',
            ha='center', va='center', fontsize=14, weight='bold')

    # Add mathematical notation above
    ax.text(left_x, n_trials + 0.3, r'$\hat{y}$',
            ha='center', va='center', fontsize=16, style='italic')
    ax.text(right_x, n_trials + 0.3, r'$\hat{y}^*$',
            ha='center', va='center', fontsize=16, style='italic')

    # Draw blocks for each trial
    for i in range(n_trials):
        y_pos = n_trials - i - 0.5

        # Left column - Original
        color_name = original_sequence[i]
        color_rgb = stimulus_colors[color_name]
        rect_left = mpatches.Rectangle((left_x - block_width/2, y_pos - block_height/2),
                                       block_width, block_height,
                                       facecolor=color_rgb, edgecolor='black', linewidth=2)
        ax.add_patch(rect_left)

        # Center column - Ground truth
        rect_center = mpatches.Rectangle((center_x - block_width/2, y_pos - block_height/2),
                                         block_width, block_height,
                                         facecolor=color_rgb, edgecolor='black', linewidth=3)
        ax.add_patch(rect_center)

        # Right column - Permuted
        color_name_perm = permuted_sequence[i]
        color_rgb_perm = stimulus_colors[color_name_perm]
        rect_right = mpatches.Rectangle((right_x - block_width/2, y_pos - block_height/2),
                                        block_width, block_height,
                                        facecolor=color_rgb_perm, edgecolor='black', linewidth=2)
        ax.add_patch(rect_right)

        # Draw arrows (left <-> center, center <-> right)
        arrow_y = y_pos

        # Left to center arrow
        ax.annotate('', xy=(center_x - block_width/2 - 0.05, arrow_y),
                   xytext=(left_x + block_width/2 + 0.05, arrow_y),
                   arrowprops=dict(arrowstyle='<->', color='black', lw=1.5))

        # Center to right arrow
        ax.annotate('', xy=(right_x - block_width/2 - 0.05, arrow_y),
                   xytext=(center_x + block_width/2 + 0.05, arrow_y),
                   arrowprops=dict(arrowstyle='<->', color='black', lw=1.5))

    # Add annotations for Red/Green swap (or kept)
    for i in range(n_trials):
        y_pos = n_trials - i - 0.5

        if original_sequence[i] != permuted_sequence[i]:
            # Swapped
            if original_sequence[i] == 'Red':
                ax.text(right_x + block_width/2 + 0.5, y_pos, 'SWAP',
                       ha='left', va='center', fontsize=8, color='red', weight='bold')
            else:
                ax.text(right_x + block_width/2 + 0.5, y_pos, 'SWAP',
                       ha='left', va='center', fontsize=8, color='red', weight='bold')
        else:
            # Kept original
            ax.text(right_x + block_width/2 + 0.5, y_pos, 'KEEP',
                   ha='left', va='center', fontsize=8, color='gray', style='italic')

    # Add formula at bottom
    formula_text = r'$\delta^* = |M(\mathbf{y}, \hat{\mathbf{y}}) - M(\mathbf{y}, \hat{\mathbf{y}}^*)|$'
    ax.text(5.0, -0.8, formula_text,
            ha='center', va='center', fontsize=16,
            bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow',
                     edgecolor='black', linewidth=2))

    # Add description
    ax.text(5.0, -1.5, 'Permutation: 50% of Red/Green labels randomly swapped',
            ha='center', va='center', fontsize=11, style='italic')

    plt.title('Panel C: Permutation Test Methodology',
              fontsize=14, weight='bold', pad=20)

    plt.tight_layout()
    output_path = OUTPUT_DIR / 'figure2_panel_c_permutation_corrected.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_path}")
    plt.close()


def main():
    print("="*70)
    print("Creating Figure 2C - Permutation Methodology")
    print("="*70)

    create_permutation_methodology()

    print("\n" + "="*70)
    print("SUCCESS! Figure 2C created:")
    print(f"  - {OUTPUT_DIR}/figure2_panel_c_permutation_corrected.png")
    print("="*70)


if __name__ == "__main__":
    main()
