#!/usr/bin/env python3
"""
Circular visualization of color-specific activation patterns and disparities
Each color positioned at 45° intervals, showing HC consistency and CVD disparity
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Wedge
from pathlib import Path
import json

# Load data
base_dir = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis')
results_dir = base_dir / 'results' / 'group_level' / 'significance_tests_no_sub02'

# ROIs to process
ROIS = ['V1', 'V2']
HC_SUBJECTS = ['03', '05', '06', '07']
CVD_SUBJECTS = ['08', '09', '10']
CVD_TYPES = {'08': 'Deuteranopia', '09': 'Deuteranopia', '10': 'Protanomaly'}
CVD_COLORS = {'08': '#FF6B6B', '09': '#FFA07A', '10': '#FFB6C1'}

# Color names and angles (8 colors at 45° intervals)
COLOR_NAMES = ['Red', 'Orange', 'Yellow', 'Chartreuse', 'Green', 'Cyan', 'Blue', 'Magenta']
COLOR_ANGLES = np.array([0, 45, 90, 135, 180, 225, 270, 315])  # degrees
COLOR_RGB = [
    '#FF0000',  # Red
    '#FF7F00',  # Orange
    '#FFFF00',  # Yellow
    '#7FFF00',  # Chartreuse
    '#00FF00',  # Green
    '#00FFFF',  # Cyan
    '#0000FF',  # Blue
    '#FF00FF',  # Magenta
]

for ROI in ROIS:
    # Load results
    results_file = results_dir / f'significance_tests_{ROI}.json'
    with open(results_file, 'r') as f:
        results = json.load(f)

    individual_level = results['individual_level']

    # Create figure with polar subplot
    fig = plt.figure(figsize=(16, 16))
    ax = fig.add_subplot(111, projection='polar')

    # ========================================================================
    # Extract color-specific RMS for each subject
    # ========================================================================

    # HC subjects (need to load from reference robustness or calculate)
    # For now, use color_rms from individual level as proxy
    # In real implementation, we'd load actual HC patterns

    # Get CVD color-specific RMS
    cvd_color_rms = {}
    for cvd_id in CVD_SUBJECTS:
        cvd_color_rms[cvd_id] = np.array(individual_level[cvd_id]['color_rms'])

    # Estimate HC mean (from the data structure)
    # Average the "baseline" from reference robustness
    ref_robustness = results['group_level']['reference_robustness']
    hc_color_rms_mean = np.mean(ref_robustness['color_rms_matrix'], axis=0)
    hc_color_rms_std = np.std(ref_robustness['color_rms_matrix'], axis=0)

    # ========================================================================
    # Plot HC activation patterns (mean ± std as shaded region)
    # ========================================================================

    # Convert angles to radians
    angles_rad = np.deg2rad(COLOR_ANGLES)

    # Close the plot by repeating first point
    angles_plot = np.concatenate([angles_rad, [angles_rad[0]]])
    hc_mean_plot = np.concatenate([hc_color_rms_mean, [hc_color_rms_mean[0]]])
    hc_std_plot = np.concatenate([hc_color_rms_std, [hc_color_rms_std[0]]])

    # Plot HC mean
    ax.plot(angles_plot, hc_mean_plot, 'o-', color='steelblue', linewidth=3,
            markersize=12, label='HC Mean', zorder=3, alpha=0.8)

    # Plot HC uncertainty (shaded region)
    ax.fill_between(angles_plot,
                     hc_mean_plot - hc_std_plot,
                     hc_mean_plot + hc_std_plot,
                     color='lightblue', alpha=0.3, label='HC Variability (±1 SD)', zorder=1)

    # ========================================================================
    # Plot each CVD's activation pattern
    # ========================================================================

    markers = ['s', '^', 'D']  # Different markers for each CVD

    for i, cvd_id in enumerate(CVD_SUBJECTS):
        cvd_rms = cvd_color_rms[cvd_id]
        cvd_rms_plot = np.concatenate([cvd_rms, [cvd_rms[0]]])

        ax.plot(angles_plot, cvd_rms_plot,
                marker=markers[i], linestyle='--', linewidth=2.5, markersize=10,
                color=CVD_COLORS[cvd_id], alpha=0.9,
                label=f'Sub-{cvd_id} ({CVD_TYPES[cvd_id][:5]})',
                zorder=4)

    # ========================================================================
    # Add disparity lines (connecting HC mean to each CVD)
    # ========================================================================

    for color_idx in range(8):
        angle = angles_rad[color_idx]
        hc_val = hc_color_rms_mean[color_idx]

        for cvd_id in CVD_SUBJECTS:
            cvd_val = cvd_color_rms[cvd_id][color_idx]

            # Draw line from HC to CVD
            ax.plot([angle, angle], [hc_val, cvd_val],
                   color='gray', linestyle=':', linewidth=1.5, alpha=0.4, zorder=2)

    # ========================================================================
    # Add color labels at each angle
    # ========================================================================

    # Find max radius for label placement
    max_radius = max(hc_mean_plot.max(),
                     max([cvd_color_rms[cid].max() for cid in CVD_SUBJECTS]))
    label_radius = max_radius * 1.15

    for i, (angle, color_name, color_rgb) in enumerate(zip(angles_rad, COLOR_NAMES, COLOR_RGB)):
        # Color name
        ax.text(angle, label_radius, color_name,
               ha='center', va='center', fontsize=11, fontweight='bold',
               bbox=dict(boxstyle='round,pad=0.5', facecolor=color_rgb,
                        edgecolor='black', linewidth=2, alpha=0.7))

        # Color index
        ax.text(angle, label_radius * 0.85, f'C{i+1}',
               ha='center', va='center', fontsize=9,
               bbox=dict(boxstyle='circle,pad=0.3', facecolor='white',
                        edgecolor='gray', linewidth=1, alpha=0.8))

    # ========================================================================
    # Highlight red-green axis (where CVD typically differs most)
    # ========================================================================

    # Red-Green axis (0° and 180°)
    rg_angles = [0, np.pi]
    rg_radius = max_radius * 1.3

    for rg_angle in rg_angles:
        ax.plot([rg_angle, rg_angle], [0, rg_radius],
               color='red', linestyle='--', linewidth=2, alpha=0.3, zorder=0)

    ax.text(0, rg_radius * 0.5, 'R-G Axis', rotation=90, ha='center', va='center',
           fontsize=10, color='red', fontweight='bold', alpha=0.5)
    ax.text(np.pi, rg_radius * 0.5, 'R-G Axis', rotation=-90, ha='center', va='center',
           fontsize=10, color='red', fontweight='bold', alpha=0.5)

    # Blue-Yellow axis (90° and 270°)
    by_angles = [np.pi/2, 3*np.pi/2]

    for by_angle in by_angles:
        ax.plot([by_angle, by_angle], [0, rg_radius],
               color='blue', linestyle='--', linewidth=2, alpha=0.3, zorder=0)

    ax.text(np.pi/2, rg_radius * 0.5, 'B-Y Axis', rotation=0, ha='center', va='center',
           fontsize=10, color='blue', fontweight='bold', alpha=0.5)
    ax.text(3*np.pi/2, rg_radius * 0.5, 'B-Y Axis', rotation=0, ha='center', va='center',
           fontsize=10, color='blue', fontweight='bold', alpha=0.5)

    # ========================================================================
    # Annotations and statistics
    # ========================================================================

    # Center text
    ax.text(0, 0, f'{ROI}\nColor-Specific\nDisparity',
           ha='center', va='center', fontsize=14, fontweight='bold',
           bbox=dict(boxstyle='round,pad=0.8', facecolor='lightyellow',
                    edgecolor='black', linewidth=2, alpha=0.8),
           zorder=10)

    # Calculate average disparity per CVD
    avg_disparity = {}
    max_disparity_color = {}

    for cvd_id in CVD_SUBJECTS:
        disparities = np.abs(cvd_color_rms[cvd_id] - hc_color_rms_mean)
        avg_disparity[cvd_id] = np.mean(disparities)
        max_disparity_color[cvd_id] = COLOR_NAMES[np.argmax(disparities)]

    # Add statistics box
    stats_text = f"""
    Average Disparity:
    • Sub-08: {avg_disparity['08']:.3f}
      Max: {max_disparity_color['08']}
    • Sub-09: {avg_disparity['09']:.3f}
      Max: {max_disparity_color['09']}
    • Sub-10: {avg_disparity['10']:.3f}
      Max: {max_disparity_color['10']}
    """

    ax.text(0.02, 0.98, stats_text.strip(), transform=ax.transAxes,
           fontsize=10, va='top', ha='left', family='monospace',
           bbox=dict(boxstyle='round', facecolor='white', alpha=0.8,
                    edgecolor='black', linewidth=1))

    # ========================================================================
    # Configuration
    # ========================================================================

    # Set radial limits
    ax.set_ylim(0, max_radius * 1.35)

    # Set theta direction (clockwise from top)
    ax.set_theta_zero_location('N')  # 0° at top
    ax.set_theta_direction(-1)  # Clockwise

    # Remove radial labels (too cluttered)
    ax.set_yticklabels([])

    # Set angular labels (show degrees)
    ax.set_xticks(angles_rad)
    ax.set_xticklabels([f'{int(a)}°' for a in COLOR_ANGLES], fontsize=10)

    # Grid
    ax.grid(True, linestyle=':', alpha=0.3, linewidth=1)

    # Legend
    ax.legend(loc='upper left', bbox_to_anchor=(1.05, 1), fontsize=11,
             framealpha=0.9, edgecolor='black', fancybox=True)

    # Title
    ax.set_title(f'Circular Color-Space Visualization ({ROI})\n' +
                f'HC Activation Pattern vs CVD Disparity',
                fontsize=16, fontweight='bold', pad=20)

    # ========================================================================
    # Save
    # ========================================================================

    output_file = results_dir.parent / f'circular_disparity_{ROI}.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✅ Saved: {output_file}")

    plt.close()

# ============================================================================
# Create combined figure (V1 and V2 side by side)
# ============================================================================

fig = plt.figure(figsize=(20, 10))

for roi_idx, ROI in enumerate(ROIS):
    # Load results
    results_file = results_dir / f'significance_tests_{ROI}.json'
    with open(results_file, 'r') as f:
        results = json.load(f)

    individual_level = results['individual_level']
    ref_robustness = results['group_level']['reference_robustness']

    # Extract data
    cvd_color_rms = {}
    for cvd_id in CVD_SUBJECTS:
        cvd_color_rms[cvd_id] = np.array(individual_level[cvd_id]['color_rms'])

    hc_color_rms_mean = np.mean(ref_robustness['color_rms_matrix'], axis=0)
    hc_color_rms_std = np.std(ref_robustness['color_rms_matrix'], axis=0)

    # Create subplot
    ax = fig.add_subplot(1, 2, roi_idx + 1, projection='polar')

    # Angles
    angles_rad = np.deg2rad(COLOR_ANGLES)
    angles_plot = np.concatenate([angles_rad, [angles_rad[0]]])
    hc_mean_plot = np.concatenate([hc_color_rms_mean, [hc_color_rms_mean[0]]])
    hc_std_plot = np.concatenate([hc_color_rms_std, [hc_color_rms_std[0]]])

    # Plot HC
    ax.plot(angles_plot, hc_mean_plot, 'o-', color='steelblue', linewidth=3,
            markersize=12, label='HC Mean', zorder=3, alpha=0.8)
    ax.fill_between(angles_plot,
                     hc_mean_plot - hc_std_plot,
                     hc_mean_plot + hc_std_plot,
                     color='lightblue', alpha=0.3, label='HC ±1SD', zorder=1)

    # Plot CVD
    markers = ['s', '^', 'D']
    for i, cvd_id in enumerate(CVD_SUBJECTS):
        cvd_rms = cvd_color_rms[cvd_id]
        cvd_rms_plot = np.concatenate([cvd_rms, [cvd_rms[0]]])

        ax.plot(angles_plot, cvd_rms_plot,
                marker=markers[i], linestyle='--', linewidth=2.5, markersize=10,
                color=CVD_COLORS[cvd_id], alpha=0.9,
                label=f'Sub-{cvd_id} ({CVD_TYPES[cvd_id][:5]})',
                zorder=4)

    # Disparity lines
    for color_idx in range(8):
        angle = angles_rad[color_idx]
        hc_val = hc_color_rms_mean[color_idx]

        for cvd_id in CVD_SUBJECTS:
            cvd_val = cvd_color_rms[cvd_id][color_idx]
            ax.plot([angle, angle], [hc_val, cvd_val],
                   color='gray', linestyle=':', linewidth=1.5, alpha=0.4, zorder=2)

    # Color labels
    max_radius = max(hc_mean_plot.max(),
                     max([cvd_color_rms[cid].max() for cid in CVD_SUBJECTS]))
    label_radius = max_radius * 1.12

    for i, (angle, color_name, color_rgb) in enumerate(zip(angles_rad, COLOR_NAMES, COLOR_RGB)):
        ax.text(angle, label_radius, f'{color_name}\nC{i+1}',
               ha='center', va='center', fontsize=9, fontweight='bold',
               bbox=dict(boxstyle='round,pad=0.4', facecolor=color_rgb,
                        edgecolor='black', linewidth=1.5, alpha=0.7))

    # Center label
    ax.text(0, 0, ROI, ha='center', va='center', fontsize=16, fontweight='bold',
           bbox=dict(boxstyle='circle,pad=0.8', facecolor='lightyellow',
                    edgecolor='black', linewidth=2, alpha=0.9),
           zorder=10)

    # Configuration
    ax.set_ylim(0, max_radius * 1.25)
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    ax.set_yticklabels([])
    ax.set_xticks(angles_rad)
    ax.set_xticklabels([f'{int(a)}°' for a in COLOR_ANGLES], fontsize=9)
    ax.grid(True, linestyle=':', alpha=0.3)

    if roi_idx == 0:
        ax.legend(loc='upper left', bbox_to_anchor=(-0.3, 1), fontsize=10,
                 framealpha=0.9, edgecolor='black')

    ax.set_title(f'{ROI} Color-Specific Disparity', fontsize=14, fontweight='bold', pad=15)

fig.suptitle('Circular Color-Space Visualization: HC Patterns vs CVD Disparity',
            fontsize=18, fontweight='bold', y=0.98)

plt.tight_layout(rect=[0, 0, 1, 0.96])

output_file = results_dir.parent / 'circular_disparity_combined.png'
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print(f"✅ Combined figure saved: {output_file}")

plt.close()

print("\n" + "="*70)
print("CIRCULAR DISPARITY VISUALIZATION COMPLETE!")
print("="*70)
print("\nGenerated files:")
print(f"  - circular_disparity_V1.png")
print(f"  - circular_disparity_V2.png")
print(f"  - circular_disparity_combined.png")
