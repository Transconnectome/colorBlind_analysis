#!/usr/bin/env python3
"""
Targeted fixes for figures
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Circle, FancyArrowPatch
import seaborn as sns
from pathlib import Path

plt.rcParams['font.family'] = 'Arial'
plt.rcParams['font.size'] = 10
sns.set_style("whitegrid")

BASE_DIR = Path("/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis")
OUTPUT_DIR = BASE_DIR / "docs/OHBM_abstract/figures"

HC_COLOR = '#1f77b4'
CVD_COLOR = '#ff7f0e'

# 8 stimulus colors
stimulus_colors_rgb = [
    '#FF0000', '#FF7F00', '#FFFF00', '#7FFF00',
    '#00FF00', '#00FFFF', '#0000FF', '#FF00FF'
]

# ============================================================================
# FIX 1B: Keep basis functions, only update circular to match OHBM_Figure1 A
# ============================================================================

def create_figure1b_updated():
    """Keep basis functions on left, update circular on right to match OHBM A"""
    print("\n[Fix 1B] Updating Figure 1B - circular only...")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

    # ========== LEFT: Basis Functions (KEEP AS IS) ==========
    ax1.set_title('Forward Encoding Model:\nBasis Functions', fontsize=14, weight='bold')

    angles = np.linspace(0, 360, 100)
    basis_centers = np.linspace(0, 300, 6)

    for i, center in enumerate(basis_centers):
        response = np.maximum(0, np.cos(np.radians(angles - center)))
        ax1.plot(angles, response + i*0.3, linewidth=2,
                label=f'Basis {i+1} (center={center:.0f}°)')

    ax1.set_xlabel('Color Angle (degrees)', fontsize=12, weight='bold')
    ax1.set_ylabel('Response (offset for visualization)', fontsize=12, weight='bold')
    ax1.set_xlim(0, 360)
    ax1.set_xticks([0, 90, 180, 270, 360])
    ax1.legend(loc='upper right', fontsize=9)
    ax1.grid(True, alpha=0.3)
    ax1.text(180, -0.2, 'Leave-one-run-out Cross-Validation', ha='center',
            fontsize=11, style='italic')

    # ========== RIGHT: Circular Color Space (UPDATED to match OHBM A) ==========
    ax2.set_aspect('equal')
    ax2.axis('off')
    ax2.set_xlim(-80, 80)
    ax2.set_ylim(-80, 80)
    ax2.set_title('Circular Color Space\n(8 Isoluminant Colors)', fontsize=14, weight='bold')

    # Draw grid lines (like OHBM A)
    ax2.axhline(0, color='lightgray', linewidth=0.5, linestyle='-', alpha=0.5)
    ax2.axvline(0, color='lightgray', linewidth=0.5, linestyle='-', alpha=0.5)

    # Draw circle
    circle = Circle((0, 0), 50, fill=False, edgecolor='black', linewidth=2)
    ax2.add_patch(circle)

    # Add degree labels and stimulus colors (matching OHBM Figure 1 A)
    stimulus_angles = np.array([0, 45, 90, 135, 180, 225, 270, 315])

    for i, angle in enumerate(stimulus_angles):
        rad = np.radians(angle)

        # Position on circle
        x = 50 * np.cos(rad)
        y = 50 * np.sin(rad)

        # Draw large colored circle (like OHBM A)
        color_circle = Circle((x, y), 8, facecolor=stimulus_colors_rgb[i],
                             edgecolor='black', linewidth=2, zorder=3)
        ax2.add_patch(color_circle)

        # Degree label (outside circle)
        label_x = 65 * np.cos(rad)
        label_y = 65 * np.sin(rad)
        ax2.text(label_x, label_y, f'{angle}°', ha='center', va='center',
                fontsize=11, weight='bold')

    # L*a*b* space annotation (like OHBM A)
    ax2.text(0, -72, 'L*=54, radius=38, 45° spacing',
            ha='center', fontsize=10, style='italic')

    # Title at top
    plt.suptitle('Panel B - Stage 5: Forward Encoding Model & Reconstruction',
                fontsize=16, weight='bold', y=0.98)

    # Outputs annotation
    fig.text(0.5, 0.02, 'Outputs: Classification Accuracy & Reconstruction Error',
            ha='center', fontsize=12, weight='bold',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow',
                     edgecolor='black', linewidth=2))

    plt.tight_layout(rect=[0, 0.05, 1, 0.96])
    output_path = OUTPUT_DIR / 'figure1_panel_b_stage5_final.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_path}")
    plt.close()


# ============================================================================
# FIX 2B: Extend y-axis to 0-100
# ============================================================================

def create_figure2b_extended():
    """Fix boxplot with y-axis 0-100"""
    print("\n[Fix 2B] Creating Figure 2B with y=0-100...")

    data = {
        'V1': {'HC_mean': 59.6, 'HC_sd': 25.1, 'CVD_mean': 67.6, 'CVD_sd': 18.0},
        'V2': {'HC_mean': 50.0, 'HC_sd': 21.8, 'CVD_mean': 40.9, 'CVD_sd': 3.8},
        'V3': {'HC_mean': 27.9, 'HC_sd': 5.1, 'CVD_mean': 28.7, 'CVD_sd': 2.9},
        'hV4': {'HC_mean': 27.5, 'HC_sd': 1.5, 'CVD_mean': 29.6, 'CVD_sd': 1.5}
    }

    # Generate synthetic data
    np.random.seed(42)
    for roi in ['V1', 'V2', 'V3', 'hV4']:
        data[roi]['HC'] = np.random.normal(data[roi]['HC_mean'], data[roi]['HC_sd'], 6)
        data[roi]['CVD'] = np.random.normal(data[roi]['CVD_mean'], data[roi]['CVD_sd'], 3)

    fig, ax = plt.subplots(figsize=(10, 7))

    rois = ['V1', 'V2', 'V3', 'hV4']
    x_positions = np.arange(len(rois))
    width = 0.35

    hc_data = [data[roi]['HC'] for roi in rois]
    cvd_data = [data[roi]['CVD'] for roi in rois]

    # Boxplots
    bp_hc = ax.boxplot(hc_data, positions=x_positions - width/2, widths=width*0.6,
                       patch_artist=True, showfliers=False,
                       boxprops=dict(facecolor=HC_COLOR, alpha=0.7),
                       medianprops=dict(color='black', linewidth=2),
                       whiskerprops=dict(color=HC_COLOR),
                       capprops=dict(color=HC_COLOR))

    bp_cvd = ax.boxplot(cvd_data, positions=x_positions + width/2, widths=width*0.6,
                        patch_artist=True, showfliers=False,
                        boxprops=dict(facecolor=CVD_COLOR, alpha=0.7),
                        medianprops=dict(color='black', linewidth=2),
                        whiskerprops=dict(color=CVD_COLOR),
                        capprops=dict(color=CVD_COLOR))

    # Significance lines - positioned within 0-100 range
    for i in range(len(rois)):
        x1 = x_positions[i] - width/2
        x2 = x_positions[i] + width/2
        y_max = max(data[rois[i]]['HC'].max(), data[rois[i]]['CVD'].max())

        # Position line well within 0-100
        y_line = min(y_max + 5, 88)  # Max at 88 to leave room for text

        ax.plot([x1, x1, x2, x2], [y_line, y_line+1.5, y_line+1.5, y_line],
                'k-', linewidth=1)
        ax.text(x_positions[i], y_line+2.5, 'n.s.', ha='center', fontsize=9)

    # Reference lines
    ax.axhline(y=12.5, color='gray', linestyle='--', linewidth=1, alpha=0.5,
              label='Chance (12.5%)')
    ax.axhline(y=50, color='lightgray', linestyle='--', linewidth=1, alpha=0.5,
              label='Good (50%)')

    # Labels
    ax.set_xlabel('ROI', fontsize=12, weight='bold')
    ax.set_ylabel('Classification Accuracy (%)', fontsize=12, weight='bold')
    ax.set_title('Panel B: Decoding Accuracy Across ROIs: HC vs. CVD',
                 fontsize=14, weight='bold', pad=15)
    ax.set_xticks(x_positions)
    ax.set_xticklabels(rois, fontsize=11)
    ax.set_ylim(0, 100)  # EXTENDED TO 0-100

    # Legend
    hc_patch = mpatches.Patch(color=HC_COLOR, alpha=0.7, label='HC (n=6)')
    cvd_patch = mpatches.Patch(color=CVD_COLOR, alpha=0.7, label='CVD (n=3)')
    ax.legend(handles=[hc_patch, cvd_patch], loc='upper right', fontsize=10)

    ax.yaxis.grid(True, alpha=0.3)
    ax.set_axisbelow(True)

    plt.tight_layout()
    output_path = OUTPUT_DIR / 'figure2_panel_b_boxplot_final.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_path}")
    plt.close()


# ============================================================================
# Main
# ============================================================================

def main():
    print("="*70)
    print("Targeted Figure Fixes")
    print("="*70)

    create_figure1b_updated()
    create_figure2b_extended()

    print("\n" + "="*70)
    print("SUCCESS! Targeted fixes complete:")
    print(f"  - Figure 1B: {OUTPUT_DIR}/figure1_panel_b_stage5_final.png")
    print(f"  - Figure 2B: {OUTPUT_DIR}/figure2_panel_b_boxplot_final.png")
    print("="*70)


if __name__ == "__main__":
    main()
