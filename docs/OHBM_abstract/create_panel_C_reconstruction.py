#!/usr/bin/env python3
"""
Create Panel C: Color Reconstruction Examples
2x4 grid showing circular reconstruction plots for HC (sub-06) and CVD (sub-08)
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch
from pathlib import Path

# Color definitions
LABEL2HUE_DEG = {
    'color_1': 0.0,
    'color_2': 45.0,
    'color_3': 90.0,
    'color_4': 135.0,
    'color_5': 180.0,
    'color_6': 225.0,
    'color_7': 270.0,
    'color_8': 315.0,
}

COLOR_LAB = {
    'color_1': [59.90, 62.69, 3.78],
    'color_2': [64.20, 49.20, 45.58],
    'color_3': [57.27, 13.06, 41.69],
    'color_4': [69.08, -55.02, 47.38],
    'color_5': [74.61, -41.33, -4.89],
    'color_6': [69.14, -11.45, -40.91],
    'color_7': [60.68, 19.18, -54.13],
    'color_8': [60.17, 46.82, -40.31],
}

def lab2rgb_accurate(L, a, b, clip=True):
    """CIELab → RGB conversion"""
    L, a, b = float(L), float(a), float(b)

    y = (L + 16) / 116
    x = a / 500 + y
    z = y - b / 200

    xyz = np.array([x, y, z])
    xyz = np.where(xyz > 0.206893, xyz**3, (xyz - 16/116) / 7.787)
    xyz *= [0.95047, 1., 1.08883]

    rgb = np.dot([[3.2406, -1.5372, -0.4986],
                  [-0.9689, 1.8758, 0.0415],
                  [0.0557, -0.2040, 1.0570]], xyz)

    rgb = np.where(rgb <= 0.0031308, 12.92 * rgb, 1.055 * rgb**(1/2.4) - 0.055)

    if clip:
        rgb = np.clip(rgb, 0, 1)

    return tuple(rgb)

def circular_diff_deg(a, b):
    """Calculate circular distance in degrees"""
    diff = np.abs(a - b)
    diff = np.where(diff > 180, 360 - diff, diff)
    return diff

def load_reconstruction_data(subject, roi, base_path):
    """Load reconstruction trial data from CSV"""
    csv_path = base_path / f"anova_results_config32_determin_sub-{subject}_{roi}.csv"

    df = pd.read_csv(csv_path)

    # Get reconstruction trials
    trials = df[df['method'] == 'reconstruction_trial'].copy()

    if len(trials) == 0:
        return None, None, None

    # Calculate error for each trial
    trials['error'] = circular_diff_deg(trials['true_hue'], trials['reconstructed_hue'])

    # Calculate mean error
    mean_error = trials['error'].mean()

    # Get classification accuracy
    acc_rows = df[df['method'] == 'classification']
    if len(acc_rows) > 0:
        accuracy = acc_rows['accuracy'].mean() * 100
    else:
        accuracy = None

    return trials, mean_error, accuracy

def plot_circular_reconstruction(ax, trials, mean_error, accuracy, title, border_color):
    """Plot circular reconstruction on polar axis"""

    # Clear and setup polar axis
    ax.clear()
    ax.set_theta_zero_location("E")
    ax.set_theta_direction(1)
    ax.set_ylim(0, 1.2)
    ax.set_yticks([])
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.8)

    # Draw chance performance circle (90° error = random)
    chance_circle = Circle((0, 0), 0.5, transform=ax.transData._b,
                          fill=False, edgecolor='gray', linestyle='--',
                          linewidth=1.5, alpha=0.5, zorder=1)
    ax.add_patch(chance_circle)

    # Plot each color trial
    for _, trial in trials.iterrows():
        color_name = trial['color']
        true_hue = trial['true_hue']
        recon_hue = trial['reconstructed_hue']

        # Get RGB color
        if color_name in COLOR_LAB:
            L, a, b = COLOR_LAB[color_name]
            rgb = lab2rgb_accurate(L, a, b)
        else:
            rgb = (0.5, 0.5, 0.5)

        # Convert to radians
        true_rad = np.deg2rad(true_hue)
        recon_rad = np.deg2rad(recon_hue)

        # Plot presented color (filled circle at perimeter)
        ax.plot([true_rad], [1.0], 'o', markersize=10,
               color=rgb, markeredgecolor='black', markeredgewidth=1.5, zorder=5)

        # Plot reconstructed color (open circle)
        ax.plot([recon_rad], [0.85], 'o', markersize=8,
               markerfacecolor='white', markeredgecolor=rgb,
               markeredgewidth=2, zorder=4)

        # Draw arrow from reconstructed to presented
        arrow = FancyArrowPatch((recon_rad, 0.85), (true_rad, 1.0),
                               arrowstyle='->', mutation_scale=12,
                               linewidth=1.2, color=rgb, alpha=0.6, zorder=3)
        ax.add_patch(arrow)

    # Title
    ax.set_title(title, fontsize=11, fontweight='bold', pad=10)

    # Add error and accuracy text
    if mean_error is not None:
        error_text = f'Error: {mean_error:.1f}°'
    else:
        error_text = 'Error: N/A'

    if accuracy is not None:
        acc_text = f'Acc: {accuracy:.1f}%'
    else:
        acc_text = 'Acc: N/A'

    # Position text at bottom
    ax.text(0.5, -0.15, f'{error_text}\n{acc_text}',
           transform=ax.transAxes, ha='center', va='top',
           fontsize=9, bbox=dict(boxstyle='round,pad=0.4',
                                facecolor='white', edgecolor='gray',
                                alpha=0.9))

    # Add border color to indicate group
    for spine in ax.spines.values():
        spine.set_edgecolor(border_color)
        spine.set_linewidth(3)

def create_panel_C():
    """Create Panel C figure"""

    # Data path
    base_path = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/logs/permutation_analysis/roi_specific/anova_config32_determin')

    # Subjects
    hc_subject = '06'
    cvd_subject = '08'

    # ROIs
    rois = ['V1', 'V2', 'V3', 'hV4']

    # Create figure: 2 rows (HC, CVD) x 4 columns (ROIs)
    fig, axes = plt.subplots(2, 4, figsize=(16, 8),
                             subplot_kw=dict(projection='polar'))

    # Plot HC (row 0)
    for col, roi in enumerate(rois):
        trials, mean_error, accuracy = load_reconstruction_data(hc_subject, roi, base_path)

        if trials is not None:
            plot_circular_reconstruction(axes[0, col], trials, mean_error, accuracy,
                                        f'{roi}', border_color='#1f77b4')  # Blue
        else:
            axes[0, col].text(0.5, 0.5, 'No data', transform=axes[0, col].transAxes,
                            ha='center', va='center')

    # Plot CVD (row 1)
    for col, roi in enumerate(rois):
        trials, mean_error, accuracy = load_reconstruction_data(cvd_subject, roi, base_path)

        if trials is not None:
            plot_circular_reconstruction(axes[1, col], trials, mean_error, accuracy,
                                        f'{roi}', border_color='#ff7f0e')  # Orange
        else:
            axes[1, col].text(0.5, 0.5, 'No data', transform=axes[1, col].transAxes,
                            ha='center', va='center')

    # Add row labels
    fig.text(0.02, 0.75, 'HC\n(sub-06)', ha='center', va='center',
            fontsize=12, fontweight='bold', rotation=0,
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#1f77b4',
                     edgecolor='black', alpha=0.3))

    fig.text(0.02, 0.25, 'CVD\n(sub-08)', ha='center', va='center',
            fontsize=12, fontweight='bold', rotation=0,
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#ff7f0e',
                     edgecolor='black', alpha=0.3))

    # Overall title
    fig.suptitle('Panel C: Color Reconstruction - Representative Subjects',
                fontsize=16, fontweight='bold', y=0.98)

    plt.tight_layout(rect=[0.04, 0, 1, 0.96])

    # Save
    output_png = 'Panel_C_Reconstruction.png'
    output_pdf = 'Panel_C_Reconstruction.pdf'

    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    plt.savefig(output_pdf, bbox_inches='tight')

    print(f"✓ Figure saved:")
    print(f"  - {output_png}")
    print(f"  - {output_pdf}")

    return fig

if __name__ == '__main__':
    create_panel_C()
    plt.show()
