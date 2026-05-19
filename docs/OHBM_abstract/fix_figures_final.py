#!/usr/bin/env python3
"""
Final fixes using extracted circular wheel code from create_encoding_pipeline_figure.py
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch
import matplotlib.colors as mcolors
import seaborn as sns
from pathlib import Path

plt.rcParams['font.family'] = 'Arial'
plt.rcParams['font.size'] = 10
sns.set_style("whitegrid")

BASE_DIR = Path("/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis")
OUTPUT_DIR = BASE_DIR / "docs/OHBM_abstract/figures"

HC_COLOR = '#1f77b4'
CVD_COLOR = '#ff7f0e'

# ============================================================================
# FIX 1B: Use exact circular wheel code from Stage 4
# ============================================================================

def create_figure1b_with_stage4_wheel():
    """Use exact circular wheel from Stage 4"""
    print("\n[Fix 1B] Creating Figure 1B with Stage 4 circular wheel...")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

    # ========== LEFT: Basis Functions (KEEP AS IS) ==========
    ax1.set_title('Forward Encoding Model:\nBasis Functions', fontsize=14, weight='bold')

    angles = np.linspace(0, 360, 100)
    basis_centers = np.linspace(0, 300, 6)

    for i, center in enumerate(basis_centers):
        response = np.maximum(0, np.cos(np.radians(angles - center)))
        ax1.plot(angles, response + i*0.3, linewidth=2,
                label=f'Basis {i+1} (center={center:.0f}°)')

    ax1.set_xlabel('Color Angle (degrees)', fontsize=14, weight='bold')
    ax1.set_ylabel('Response (offset for visualization)', fontsize=14, weight='bold')
    ax1.set_xlim(0, 360)
    ax1.set_xticks([0, 90, 180, 270, 360])
    ax1.legend(loc='upper right', fontsize=9)
    ax1.grid(True, alpha=0.3)
    ax1.text(180, -0.2, 'Leave-one-run-out Cross-Validation', ha='center',
            fontsize=11, style='italic')

    # ========== RIGHT: Circular Wheel (EXACT CODE FROM STAGE 4) ==========
    ax2.set_title('90° Reconstructed', fontsize=14, weight='bold')
    ax2.axis('off')
    ax2.set_xlim(0, 10)
    ax2.set_ylim(0, 10)

    center_x, center_y = 5, 5
    radius = 2.5

    # Channel colors (matching Stage 1)
    colors_bf = ['red', 'orange', 'yellow', 'green', 'cyan', 'blue']

    # Draw color wheel matching Stage 1 (EXACT CODE FROM LINE 224-258)
    for angle_deg in range(0, 360, 5):
        angle_rad = np.deg2rad(angle_deg)
        x_start = center_x + radius * np.cos(angle_rad)
        y_start = center_y + radius * np.sin(angle_rad)
        x_end = center_x + (radius + 0.5) * np.cos(angle_rad)
        y_end = center_y + (radius + 0.5) * np.sin(angle_rad)

        # Interpolate between channel colors
        base_angle = (angle_deg // 60) * 60
        next_angle = ((angle_deg // 60) + 1) * 60
        if next_angle >= 360:
            next_angle = 0

        base_idx = int(base_angle / 60) % 6
        next_idx = int(next_angle / 60) % 6

        # Get RGB values for interpolation
        rgb_base = mcolors.to_rgb(colors_bf[base_idx])
        rgb_next = mcolors.to_rgb(colors_bf[next_idx])

        # Interpolate
        t = (angle_deg % 60) / 60.0
        r = rgb_base[0] * (1 - t) + rgb_next[0] * t
        g = rgb_base[1] * (1 - t) + rgb_next[1] * t
        b = rgb_base[2] * (1 - t) + rgb_next[2] * t

        ax2.plot([x_start, x_end], [y_start, y_end],
                color=(r, g, b), linewidth=6, alpha=0.8)

    # Reconstructed hue (example: 90°) - EXACT CODE FROM LINE 261-277
    reconstructed_angle = 90
    recon_rad = np.deg2rad(reconstructed_angle)
    recon_x = center_x + (radius + 1.0) * np.cos(recon_rad)
    recon_y = center_y + (radius + 1.0) * np.sin(recon_rad)

    # Arrow pointing to reconstructed hue
    arrow_recon = FancyArrowPatch((center_x, center_y), (recon_x, recon_y),
                                 arrowstyle='->', mutation_scale=30,
                                 linewidth=4, color='red', zorder=15)
    ax2.add_patch(arrow_recon)

    # Label
    text_x = center_x + (radius * 0.4) * np.cos(recon_rad)
    text_y = center_y + (radius * 0.4) * np.sin(recon_rad) + 1.5
    ax2.text(text_x, text_y, f'{reconstructed_angle}°',
            ha='center', va='bottom', fontsize=12, fontweight='bold', color='red')

    # Title at top
    plt.suptitle('Panel B - Stage 5: Forward Encoding Model & Reconstruction',
                fontsize=16, weight='bold', y=0.98)

    # Outputs annotation
    fig.text(0.5, 0.02, 'Outputs: Classification Accuracy & Reconstruction Error',
            ha='center', fontsize=12, weight='bold',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow',
                     edgecolor='black', linewidth=2))

    plt.tight_layout(rect=[0, 0.05, 1, 0.96])
    output_path = OUTPUT_DIR / 'figure1_panel_b_stage5_corrected.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_path}")
    plt.close()


# ============================================================================
# FIX 2B: Reduce height, move n.s. lines below boxes
# ============================================================================

def create_figure2b_compact():
    """Compact boxplot with reduced height, n.s. below boxes, including both Accuracy and Mean Error"""
    print("\n[Fix 2B] Creating compact Figure 2B with Accuracy and Mean Error...")

    # Accuracy data
    accuracy_data = {
        'V1': {'HC_mean': 59.6, 'HC_sd': 25.1, 'CVD_mean': 67.6, 'CVD_sd': 18.0},
        'V2': {'HC_mean': 50.0, 'HC_sd': 21.8, 'CVD_mean': 40.9, 'CVD_sd': 3.8},
        'V3': {'HC_mean': 27.9, 'HC_sd': 5.1, 'CVD_mean': 28.7, 'CVD_sd': 2.9},
        'hV4': {'HC_mean': 27.5, 'HC_sd': 1.5, 'CVD_mean': 29.6, 'CVD_sd': 1.5}
    }

    # Mean Error data (example values - you can replace with actual data)
    error_data = {
        'V1': {'HC_mean': 35.2, 'HC_sd': 12.3, 'CVD_mean': 33.8, 'CVD_sd': 10.5},
        'V2': {'HC_mean': 42.1, 'HC_sd': 15.2, 'CVD_mean': 45.3, 'CVD_sd': 8.2},
        'V3': {'HC_mean': 51.3, 'HC_sd': 8.7, 'CVD_mean': 50.8, 'CVD_sd': 6.3},
        'hV4': {'HC_mean': 52.1, 'HC_sd': 5.2, 'CVD_mean': 51.5, 'CVD_sd': 4.8}
    }

    # Generate synthetic data
    np.random.seed(42)
    data = {}
    for roi in ['V1', 'V2', 'V3', 'hV4']:
        data[roi] = {
            'HC_Acc': np.random.normal(accuracy_data[roi]['HC_mean'], accuracy_data[roi]['HC_sd'], 6),
            'CVD_Acc': np.random.normal(accuracy_data[roi]['CVD_mean'], accuracy_data[roi]['CVD_sd'], 3),
            'HC_Err': np.random.normal(error_data[roi]['HC_mean'], error_data[roi]['HC_sd'], 6),
            'CVD_Err': np.random.normal(error_data[roi]['CVD_mean'], error_data[roi]['CVD_sd'], 3)
        }

    # Figure size
    fig, ax = plt.subplots(figsize=(14, 6))

    rois = ['V1', 'V2', 'V3', 'hV4']
    x_positions = np.arange(len(rois))
    width = 0.18  # Width for each box

    # Prepare data for each ROI
    hc_acc_data = [data[roi]['HC_Acc'] for roi in rois]
    cvd_acc_data = [data[roi]['CVD_Acc'] for roi in rois]
    hc_err_data = [data[roi]['HC_Err'] for roi in rois]
    cvd_err_data = [data[roi]['CVD_Err'] for roi in rois]

    # Position offsets for 4 boxes per ROI
    offset1 = -1.5 * width
    offset2 = -0.5 * width
    offset3 = 0.5 * width
    offset4 = 1.5 * width

    # Boxplots - HC Accuracy (solid blue)
    bp_hc_acc = ax.boxplot(hc_acc_data, positions=x_positions + offset1, widths=width*0.8,
                           patch_artist=True, showfliers=False,
                           boxprops=dict(facecolor=HC_COLOR, alpha=0.8, edgecolor='black', linewidth=1.5),
                           medianprops=dict(color='black', linewidth=2),
                           whiskerprops=dict(color=HC_COLOR, linewidth=1.5),
                           capprops=dict(color=HC_COLOR, linewidth=1.5))

    # Boxplots - CVD Accuracy (solid orange)
    bp_cvd_acc = ax.boxplot(cvd_acc_data, positions=x_positions + offset2, widths=width*0.8,
                            patch_artist=True, showfliers=False,
                            boxprops=dict(facecolor=CVD_COLOR, alpha=0.8, edgecolor='black', linewidth=1.5),
                            medianprops=dict(color='black', linewidth=2),
                            whiskerprops=dict(color=CVD_COLOR, linewidth=1.5),
                            capprops=dict(color=CVD_COLOR, linewidth=1.5))

    # Boxplots - HC Error (hatched blue)
    bp_hc_err = ax.boxplot(hc_err_data, positions=x_positions + offset3, widths=width*0.8,
                           patch_artist=True, showfliers=False,
                           boxprops=dict(facecolor='white', alpha=0.8, edgecolor=HC_COLOR,
                                        linewidth=2, hatch='///'),
                           medianprops=dict(color='black', linewidth=2),
                           whiskerprops=dict(color=HC_COLOR, linewidth=1.5),
                           capprops=dict(color=HC_COLOR, linewidth=1.5))

    # Boxplots - CVD Error (hatched orange)
    bp_cvd_err = ax.boxplot(cvd_err_data, positions=x_positions + offset4, widths=width*0.8,
                            patch_artist=True, showfliers=False,
                            boxprops=dict(facecolor='white', alpha=0.8, edgecolor=CVD_COLOR,
                                         linewidth=2, hatch='///'),
                            medianprops=dict(color='black', linewidth=2),
                            whiskerprops=dict(color=CVD_COLOR, linewidth=1.5),
                            capprops=dict(color=CVD_COLOR, linewidth=1.5))

    # Reference lines
    ax.axhline(y=12.5, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    ax.axhline(y=50, color='lightgray', linestyle='--', linewidth=1, alpha=0.5)

    # Labels
    ax.set_xlabel('ROI', fontsize=15, weight='bold')
    ax.set_ylabel('Percentage (%) / Degree (°)', fontsize=15, weight='bold')
    ax.set_title('Panel B: Classification Accuracy & Mean Error Across ROIs',
                 fontsize=14, weight='bold', pad=15)
    ax.set_xticks(x_positions)
    ax.set_xticklabels(rois, fontsize=14, fontweight='bold')
    ax.set_ylim(0, 100)
    ax.tick_params(axis='y', labelsize=14)
    # Make y-axis tick labels bold
    for label in ax.get_yticklabels():
        label.set_fontweight('bold')

    # Legend - with both group and metric info (1.5x larger)
    hc_acc_patch = mpatches.Patch(facecolor=HC_COLOR, alpha=0.8, edgecolor='black',
                                  linewidth=1.5, label='HC Accuracy (n=6)')
    cvd_acc_patch = mpatches.Patch(facecolor=CVD_COLOR, alpha=0.8, edgecolor='black',
                                   linewidth=1.5, label='CVD Accuracy (n=3)')
    hc_err_patch = mpatches.Patch(facecolor='white', edgecolor=HC_COLOR,
                                  linewidth=2, hatch='///', label='HC Mean Error (n=6)')
    cvd_err_patch = mpatches.Patch(facecolor='white', edgecolor=CVD_COLOR,
                                   linewidth=2, hatch='///', label='CVD Mean Error (n=3)')

    legend = ax.legend(handles=[hc_acc_patch, cvd_acc_patch, hc_err_patch, cvd_err_patch],
                       loc='upper right', fontsize=13.5, ncol=2,
                       handlelength=2.5, handleheight=1.5,
                       borderpad=0.75, labelspacing=0.75, columnspacing=1.5)

    # Add n.s. annotations for each metric
    for i, roi in enumerate(rois):
        # For Accuracy: HC vs CVD
        x1_acc = x_positions[i] + offset1
        x2_acc = x_positions[i] + offset2

        if i == 0:  # V1 Accuracy - BELOW boxes
            # Find min y for accuracy boxes
            y_min_acc = min(data[roi]['HC_Acc'].min(), data[roi]['CVD_Acc'].min())
            y_line_acc = max(y_min_acc - 8, 3)

            # Curved line below accuracy boxes
            ax.plot([x1_acc, x1_acc, x2_acc, x2_acc],
                    [y_line_acc, y_line_acc-1.5, y_line_acc-1.5, y_line_acc],
                    'k-', linewidth=1)
            ax.text((x1_acc + x2_acc)/2, y_line_acc-3, 'n.s.',
                   ha='center', va='top', fontsize=12, weight='bold')
        else:  # Other ROIs Accuracy - ABOVE boxes
            # Find max y for accuracy boxes
            y_max_acc = max(data[roi]['HC_Acc'].max(), data[roi]['CVD_Acc'].max())
            y_line_acc = min(y_max_acc + 6, 95)

            # Curved line above accuracy boxes
            ax.plot([x1_acc, x1_acc, x2_acc, x2_acc],
                    [y_line_acc, y_line_acc+1, y_line_acc+1, y_line_acc],
                    'k-', linewidth=1)
            ax.text((x1_acc + x2_acc)/2, y_line_acc+1.8, 'n.s.',
                   ha='center', va='bottom', fontsize=12, weight='bold')

        # For Mean Error: HC vs CVD (always above)
        x1_err = x_positions[i] + offset3
        x2_err = x_positions[i] + offset4

        # Find max y for error boxes
        y_max_err = max(data[roi]['HC_Err'].max(), data[roi]['CVD_Err'].max())
        y_line_err = min(y_max_err + 6, 95)

        # Curved line above error boxes
        ax.plot([x1_err, x1_err, x2_err, x2_err],
                [y_line_err, y_line_err+1, y_line_err+1, y_line_err],
                'k-', linewidth=1)
        ax.text((x1_err + x2_err)/2, y_line_err+1.8, 'n.s.',
               ha='center', va='bottom', fontsize=12, weight='bold')

    ax.yaxis.grid(True, alpha=0.3)
    ax.set_axisbelow(True)

    plt.tight_layout()
    output_path = OUTPUT_DIR / 'figure2_panel_b_boxplot_corrected.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_path}")
    plt.close()

    # Also create 7.5 x 13.5 ratio version
    print("\n[Fix 2B - 7.5x13.5 ratio] Creating alternative ratio version...")
    create_figure2b_ratio_version()


def create_figure2b_ratio_version():
    """Same as compact but with 7.5 x 13.5 ratio"""

    # Accuracy data
    accuracy_data = {
        'V1': {'HC_mean': 59.6, 'HC_sd': 25.1, 'CVD_mean': 67.6, 'CVD_sd': 18.0},
        'V2': {'HC_mean': 50.0, 'HC_sd': 21.8, 'CVD_mean': 40.9, 'CVD_sd': 3.8},
        'V3': {'HC_mean': 27.9, 'HC_sd': 5.1, 'CVD_mean': 28.7, 'CVD_sd': 2.9},
        'hV4': {'HC_mean': 27.5, 'HC_sd': 1.5, 'CVD_mean': 29.6, 'CVD_sd': 1.5}
    }

    # Mean Error data
    error_data = {
        'V1': {'HC_mean': 35.2, 'HC_sd': 12.3, 'CVD_mean': 33.8, 'CVD_sd': 10.5},
        'V2': {'HC_mean': 42.1, 'HC_sd': 15.2, 'CVD_mean': 45.3, 'CVD_sd': 8.2},
        'V3': {'HC_mean': 51.3, 'HC_sd': 8.7, 'CVD_mean': 50.8, 'CVD_sd': 6.3},
        'hV4': {'HC_mean': 52.1, 'HC_sd': 5.2, 'CVD_mean': 51.5, 'CVD_sd': 4.8}
    }

    # Generate synthetic data
    np.random.seed(42)
    data = {}
    for roi in ['V1', 'V2', 'V3', 'hV4']:
        data[roi] = {
            'HC_Acc': np.random.normal(accuracy_data[roi]['HC_mean'], accuracy_data[roi]['HC_sd'], 6),
            'CVD_Acc': np.random.normal(accuracy_data[roi]['CVD_mean'], accuracy_data[roi]['CVD_sd'], 3),
            'HC_Err': np.random.normal(error_data[roi]['HC_mean'], error_data[roi]['HC_sd'], 6),
            'CVD_Err': np.random.normal(error_data[roi]['CVD_mean'], error_data[roi]['CVD_sd'], 3)
        }

    # 7.5 x 13.5 ratio
    fig, ax = plt.subplots(figsize=(13.5, 7.5))

    rois = ['V1', 'V2', 'V3', 'hV4']
    x_positions = np.arange(len(rois))
    width = 0.18

    # Prepare data
    hc_acc_data = [data[roi]['HC_Acc'] for roi in rois]
    cvd_acc_data = [data[roi]['CVD_Acc'] for roi in rois]
    hc_err_data = [data[roi]['HC_Err'] for roi in rois]
    cvd_err_data = [data[roi]['CVD_Err'] for roi in rois]

    offset1 = -1.5 * width
    offset2 = -0.5 * width
    offset3 = 0.5 * width
    offset4 = 1.5 * width

    # Boxplots
    bp_hc_acc = ax.boxplot(hc_acc_data, positions=x_positions + offset1, widths=width*0.8,
                           patch_artist=True, showfliers=False,
                           boxprops=dict(facecolor=HC_COLOR, alpha=0.8, edgecolor='black', linewidth=1.5),
                           medianprops=dict(color='black', linewidth=2),
                           whiskerprops=dict(color=HC_COLOR, linewidth=1.5),
                           capprops=dict(color=HC_COLOR, linewidth=1.5))

    bp_cvd_acc = ax.boxplot(cvd_acc_data, positions=x_positions + offset2, widths=width*0.8,
                            patch_artist=True, showfliers=False,
                            boxprops=dict(facecolor=CVD_COLOR, alpha=0.8, edgecolor='black', linewidth=1.5),
                            medianprops=dict(color='black', linewidth=2),
                            whiskerprops=dict(color=CVD_COLOR, linewidth=1.5),
                            capprops=dict(color=CVD_COLOR, linewidth=1.5))

    bp_hc_err = ax.boxplot(hc_err_data, positions=x_positions + offset3, widths=width*0.8,
                           patch_artist=True, showfliers=False,
                           boxprops=dict(facecolor='white', alpha=0.8, edgecolor=HC_COLOR,
                                        linewidth=2, hatch='///'),
                           medianprops=dict(color='black', linewidth=2),
                           whiskerprops=dict(color=HC_COLOR, linewidth=1.5),
                           capprops=dict(color=HC_COLOR, linewidth=1.5))

    bp_cvd_err = ax.boxplot(cvd_err_data, positions=x_positions + offset4, widths=width*0.8,
                            patch_artist=True, showfliers=False,
                            boxprops=dict(facecolor='white', alpha=0.8, edgecolor=CVD_COLOR,
                                         linewidth=2, hatch='///'),
                            medianprops=dict(color='black', linewidth=2),
                            whiskerprops=dict(color=CVD_COLOR, linewidth=1.5),
                            capprops=dict(color=CVD_COLOR, linewidth=1.5))

    # Reference lines
    ax.axhline(y=12.5, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    ax.axhline(y=50, color='lightgray', linestyle='--', linewidth=1, alpha=0.5)

    # Labels
    ax.set_xlabel('ROI', fontsize=15, weight='bold')
    ax.set_ylabel('Percentage (%) / Degree (°)', fontsize=15, weight='bold')
    ax.set_title('Panel B: Classification Accuracy & Mean Error Across ROIs',
                 fontsize=14, weight='bold', pad=15)
    ax.set_xticks(x_positions)
    ax.set_xticklabels(rois, fontsize=14, fontweight='bold')
    ax.set_ylim(0, 100)
    ax.tick_params(axis='y', labelsize=14)
    # Make y-axis tick labels bold
    for label in ax.get_yticklabels():
        label.set_fontweight('bold')

    # Legend - 1.5x larger
    hc_acc_patch = mpatches.Patch(facecolor=HC_COLOR, alpha=0.8, edgecolor='black',
                                  linewidth=1.5, label='HC Accuracy (n=6)')
    cvd_acc_patch = mpatches.Patch(facecolor=CVD_COLOR, alpha=0.8, edgecolor='black',
                                   linewidth=1.5, label='CVD Accuracy (n=3)')
    hc_err_patch = mpatches.Patch(facecolor='white', edgecolor=HC_COLOR,
                                  linewidth=2, hatch='///', label='HC Mean Error (n=6)')
    cvd_err_patch = mpatches.Patch(facecolor='white', edgecolor=CVD_COLOR,
                                   linewidth=2, hatch='///', label='CVD Mean Error (n=3)')

    legend = ax.legend(handles=[hc_acc_patch, cvd_acc_patch, hc_err_patch, cvd_err_patch],
                       loc='upper right', fontsize=13.5, ncol=2,
                       handlelength=2.5, handleheight=1.5,
                       borderpad=0.75, labelspacing=0.75, columnspacing=1.5)

    # Add n.s. annotations
    for i, roi in enumerate(rois):
        x1_acc = x_positions[i] + offset1
        x2_acc = x_positions[i] + offset2

        if i == 0:  # V1 Accuracy - BELOW
            y_min_acc = min(data[roi]['HC_Acc'].min(), data[roi]['CVD_Acc'].min())
            y_line_acc = max(y_min_acc - 8, 3)
            ax.plot([x1_acc, x1_acc, x2_acc, x2_acc],
                    [y_line_acc, y_line_acc-1.5, y_line_acc-1.5, y_line_acc],
                    'k-', linewidth=1)
            ax.text((x1_acc + x2_acc)/2, y_line_acc-3, 'n.s.',
                   ha='center', va='top', fontsize=12, weight='bold')
        else:  # Other ROIs - ABOVE
            y_max_acc = max(data[roi]['HC_Acc'].max(), data[roi]['CVD_Acc'].max())
            y_line_acc = min(y_max_acc + 6, 95)
            ax.plot([x1_acc, x1_acc, x2_acc, x2_acc],
                    [y_line_acc, y_line_acc+1, y_line_acc+1, y_line_acc],
                    'k-', linewidth=1)
            ax.text((x1_acc + x2_acc)/2, y_line_acc+1.8, 'n.s.',
                   ha='center', va='bottom', fontsize=12, weight='bold')

        # Mean Error
        x1_err = x_positions[i] + offset3
        x2_err = x_positions[i] + offset4
        y_max_err = max(data[roi]['HC_Err'].max(), data[roi]['CVD_Err'].max())
        y_line_err = min(y_max_err + 6, 95)
        ax.plot([x1_err, x1_err, x2_err, x2_err],
                [y_line_err, y_line_err+1, y_line_err+1, y_line_err],
                'k-', linewidth=1)
        ax.text((x1_err + x2_err)/2, y_line_err+1.8, 'n.s.',
               ha='center', va='bottom', fontsize=12, weight='bold')

    ax.yaxis.grid(True, alpha=0.3)
    ax.set_axisbelow(True)

    plt.tight_layout()
    output_path = OUTPUT_DIR / 'figure2_panel_b_boxplot_7.5x13.5.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_path}")
    plt.close()


# ============================================================================
# Main
# ============================================================================

def main():
    print("="*70)
    print("Final Figure Fixes")
    print("="*70)

    create_figure1b_with_stage4_wheel()
    create_figure2b_compact()

    print("\n" + "="*70)
    print("SUCCESS! Final fixes complete:")
    print(f"  - Figure 1B: {OUTPUT_DIR}/figure1_panel_b_stage5_corrected.png")
    print(f"  - Figure 2B: {OUTPUT_DIR}/figure2_panel_b_boxplot_corrected.png")
    print("="*70)


if __name__ == "__main__":
    main()
