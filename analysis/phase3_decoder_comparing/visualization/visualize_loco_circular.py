#!/usr/bin/env python3
"""
Circular visualization of LOCO (Leave-One-Color-Out) interpolation performance
Shows per-color MAE for HC subjects vs CVD subjects across 8 hue conditions

Each color positioned at 45° intervals (0°=Red at top, clockwise)
HC shown as mean ± SD region, CVD as individual subject lines
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import gridspec
from pathlib import Path
import json

# Configuration
BASE_DIR = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis')
LOCO_DIR = BASE_DIR / 'analysis' / 'phase2_decoder_comparing' / 'results' / 'loco'
OUTPUT_DIR = LOCO_DIR / 'circular_plots'
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

# Subject groups
HC_SUBJECTS = [f'{i:02d}' for i in range(1, 8)]  # sub-01 to sub-07
CVD_SUBJECTS = ['08', '09', '10']
CVD_TYPES = {'08': 'Deutan', '09': 'Protan', '10': 'Deutan'}
CVD_COLORS = {'08': '#FF6B6B', '09': '#FFA07A', '10': '#FFB6C1'}
CVD_MARKERS = {'08': 's', '09': '^', '10': 'D'}

# Color configuration (8 colors at 45° intervals)
COLOR_NAMES = ['Red', 'Orange', 'Yellow', 'Green', 'Cyan', 'Blue', 'Purple', 'Magenta']
COLOR_ANGLES = np.array([0, 45, 90, 135, 180, 225, 270, 315])  # degrees
COLOR_RGB = [
    '#FF0000',  # Red
    '#FF7F00',  # Orange
    '#FFFF00',  # Yellow
    '#00FF00',  # Green
    '#00FFFF',  # Cyan
    '#0000FF',  # Blue
    '#8000FF',  # Purple
    '#FF00FF',  # Magenta
]

ROIS = ['V1', 'V2', 'V3', 'V4']


def load_loco_results(loco_dir, subjects, roi, model='ForwardEncoding'):
    """
    Load per-color MAE from LOCO JSON files

    Args:
        loco_dir: Path to LOCO results directory
        subjects: List of subject IDs (e.g., ['01', '02', ...])
        roi: ROI name ('V1', 'V2', 'V3', 'V4')
        model: Model name (default 'ForwardEncoding')

    Returns:
        dict: {subject_id: [8 MAE values]}
    """
    color_mae = {}

    for subj_id in subjects:
        json_path = loco_dir / f'sub-{subj_id}_loco.json'
        if not json_path.exists():
            print(f"Warning: {json_path} not found, skipping")
            continue

        with open(json_path, 'r') as f:
            data = json.load(f)

        # Extract fold_results for this ROI and model
        if roi not in data['results']:
            print(f"Warning: {roi} not found for sub-{subj_id}, skipping")
            continue

        if model not in data['results'][roi]:
            print(f"Warning: {model} not found for sub-{subj_id} {roi}, skipping")
            continue

        fold_results = data['results'][roi][model]['fold_results']

        # Extract MAE for each fold (8 colors)
        mae_per_color = []
        for fold in fold_results:
            mae_per_color.append(fold['mae'])

        color_mae[subj_id] = np.array(mae_per_color)

    return color_mae


def create_loco_circular_plot(hc_data, cvd_data, roi, model, output_path):
    """
    Create polar plot showing per-color LOCO performance

    Args:
        hc_data: dict of {subject_id: [8 MAE values]} for HC
        cvd_data: dict of {subject_id: [8 MAE values]} for CVD
        roi: ROI name
        model: Model name
        output_path: Path to save figure
    """
    fig = plt.figure(figsize=(16, 16))
    ax = fig.add_subplot(111, projection='polar')

    # Convert angles to radians
    angles_rad = np.deg2rad(COLOR_ANGLES)
    angles_plot = np.concatenate([angles_rad, [angles_rad[0]]])

    # ========================================================================
    # Compute HC statistics
    # ========================================================================
    hc_matrix = np.array(list(hc_data.values()))  # Shape: (n_hc, 8)
    hc_mean = np.mean(hc_matrix, axis=0)  # Shape: (8,)
    hc_std = np.std(hc_matrix, axis=0)

    hc_mean_plot = np.concatenate([hc_mean, [hc_mean[0]]])
    hc_std_plot = np.concatenate([hc_std, [hc_std[0]]])

    # ========================================================================
    # Plot HC pattern (blue line + shaded region)
    # ========================================================================
    ax.plot(angles_plot, hc_mean_plot, 'o-', color='steelblue',
            linewidth=3, markersize=12, label='HC Mean', zorder=3, alpha=0.8)

    ax.fill_between(angles_plot,
                     hc_mean_plot - hc_std_plot,
                     hc_mean_plot + hc_std_plot,
                     color='lightblue', alpha=0.3, label='HC ±1SD', zorder=1)

    # ========================================================================
    # Plot each CVD subject with distinct markers/colors
    # ========================================================================
    for cvd_id in sorted(cvd_data.keys()):
        mae_values = cvd_data[cvd_id]
        mae_plot = np.concatenate([mae_values, [mae_values[0]]])

        ax.plot(angles_plot, mae_plot,
                marker=CVD_MARKERS[cvd_id],
                linestyle='--', linewidth=2.5, markersize=10,
                color=CVD_COLORS[cvd_id], alpha=0.9,
                label=f'Sub-{cvd_id} ({CVD_TYPES[cvd_id]})', zorder=4)

    # ========================================================================
    # Add color labels at perimeter
    # ========================================================================
    max_radius = max(hc_mean_plot.max(),
                     max([max(v) for v in cvd_data.values()]))
    label_radius = max_radius * 1.15

    for angle, name, rgb in zip(angles_rad, COLOR_NAMES, COLOR_RGB):
        ax.text(angle, label_radius, name, ha='center', va='center',
                fontsize=11, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.5', facecolor=rgb,
                         edgecolor='black', linewidth=2, alpha=0.7))

    # ========================================================================
    # Configuration
    # ========================================================================
    ax.set_ylim(0, max_radius * 1.35)
    ax.set_theta_zero_location('N')  # 0° at top
    ax.set_theta_direction(-1)  # Clockwise
    ax.set_yticklabels([])  # Remove radial labels
    ax.set_xticks(angles_rad)
    ax.set_xticklabels([f'{int(a)}°' for a in COLOR_ANGLES])
    ax.grid(True, linestyle=':', alpha=0.3)

    # Legend
    ax.legend(loc='upper left', bbox_to_anchor=(1.05, 1), fontsize=11)

    # Title
    ax.set_title(f'{roi} LOCO Interpolation Performance\n' +
                 f'{model} Model (MAE per color, lower = better)',
                 fontsize=16, fontweight='bold', pad=20)

    # Add performance note
    note_text = (f"HC Mean MAE: {hc_mean.mean():.1f}° ± {hc_std.mean():.1f}°\n"
                 f"CVD Range: {min([v.mean() for v in cvd_data.values()]):.1f}° - "
                 f"{max([v.mean() for v in cvd_data.values()]):.1f}°")

    fig.text(0.5, 0.02, note_text, ha='center', fontsize=12,
             bbox=dict(boxstyle='round,pad=0.8', facecolor='lightyellow',
                      edgecolor='black', linewidth=1.5, alpha=0.9))

    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved: {output_path}")


def create_multi_roi_grid(hc_data_all, cvd_data_all, model, output_path):
    """
    Create 2×2 grid with all ROIs

    Args:
        hc_data_all: dict of {roi: {subject: [8 MAE]}}
        cvd_data_all: dict of {roi: {subject: [8 MAE]}}
        model: Model name
        output_path: Path to save figure
    """
    fig = plt.figure(figsize=(20, 20))

    for idx, roi in enumerate(ROIS):
        ax = fig.add_subplot(2, 2, idx+1, projection='polar')

        hc_data = hc_data_all[roi]
        cvd_data = cvd_data_all[roi]

        # Convert angles to radians
        angles_rad = np.deg2rad(COLOR_ANGLES)
        angles_plot = np.concatenate([angles_rad, [angles_rad[0]]])

        # HC statistics
        hc_matrix = np.array(list(hc_data.values()))
        hc_mean = np.mean(hc_matrix, axis=0)
        hc_std = np.std(hc_matrix, axis=0)

        hc_mean_plot = np.concatenate([hc_mean, [hc_mean[0]]])
        hc_std_plot = np.concatenate([hc_std, [hc_std[0]]])

        # Plot HC
        ax.plot(angles_plot, hc_mean_plot, 'o-', color='steelblue',
                linewidth=2.5, markersize=10, label='HC Mean', zorder=3, alpha=0.8)
        ax.fill_between(angles_plot,
                         hc_mean_plot - hc_std_plot,
                         hc_mean_plot + hc_std_plot,
                         color='lightblue', alpha=0.3, zorder=1)

        # Plot CVD
        for cvd_id in sorted(cvd_data.keys()):
            mae_values = cvd_data[cvd_id]
            mae_plot = np.concatenate([mae_values, [mae_values[0]]])

            ax.plot(angles_plot, mae_plot,
                    marker=CVD_MARKERS[cvd_id],
                    linestyle='--', linewidth=2, markersize=8,
                    color=CVD_COLORS[cvd_id], alpha=0.9,
                    label=f'Sub-{cvd_id}', zorder=4)

        # Add color labels
        max_radius = max(hc_mean_plot.max(),
                         max([max(v) for v in cvd_data.values()]))
        label_radius = max_radius * 1.15

        for angle, name, rgb in zip(angles_rad, COLOR_NAMES, COLOR_RGB):
            ax.text(angle, label_radius, name, ha='center', va='center',
                    fontsize=9, fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.4', facecolor=rgb,
                             edgecolor='black', linewidth=1.5, alpha=0.7))

        # Configuration
        ax.set_ylim(0, max_radius * 1.35)
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)
        ax.set_yticklabels([])
        ax.set_xticks(angles_rad)
        ax.set_xticklabels([f'{int(a)}°' for a in COLOR_ANGLES], fontsize=9)
        ax.grid(True, linestyle=':', alpha=0.3)

        # Legend (only for first panel)
        if idx == 0:
            ax.legend(loc='upper left', bbox_to_anchor=(1.05, 1), fontsize=10)

        # Title
        ax.set_title(f'{roi}: MAE={hc_mean.mean():.1f}° (HC)',
                     fontsize=14, fontweight='bold', pad=15)

    # Overall title
    fig.suptitle(f'LOCO Interpolation Performance Across ROIs\n{model} Model',
                 fontsize=18, fontweight='bold', y=0.98)

    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved: {output_path}")


def main():
    """Main execution function"""

    model = 'ForwardEncoding'  # Best performing model from LOCO analysis

    # Load data for all ROIs
    hc_data_all = {}
    cvd_data_all = {}

    for roi in ROIS:
        print(f"\nProcessing {roi}...")

        # Load HC data
        hc_data = load_loco_results(LOCO_DIR, HC_SUBJECTS, roi, model)
        print(f"  Loaded {len(hc_data)} HC subjects")

        # Load CVD data
        cvd_data = load_loco_results(LOCO_DIR, CVD_SUBJECTS, roi, model)
        print(f"  Loaded {len(cvd_data)} CVD subjects")

        hc_data_all[roi] = hc_data
        cvd_data_all[roi] = cvd_data

        # Create individual plot
        output_file = OUTPUT_DIR / f'loco_circular_{roi}.png'
        create_loco_circular_plot(hc_data, cvd_data, roi, model, output_file)

    # Create combined grid
    print("\nCreating combined grid...")
    combined_output = OUTPUT_DIR / 'loco_circular_combined.png'
    create_multi_roi_grid(hc_data_all, cvd_data_all, model, combined_output)

    print("\n✓ LOCO circular visualization complete!")
    print(f"  Output directory: {OUTPUT_DIR}")


if __name__ == '__main__':
    main()
