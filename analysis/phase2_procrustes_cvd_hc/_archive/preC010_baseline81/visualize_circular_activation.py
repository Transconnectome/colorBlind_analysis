#!/usr/bin/env python3
"""
Circular visualization of color-specific ACTIVATION patterns (not disparity)
Shows actual activation magnitude for HC and CVD, enabling direct comparison
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Load data
base_dir = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis')
data_dir = base_dir / 'derivatives' / 'BH2009_deoblique_v2' / 'baseline81_deob'
results_dir = base_dir / 'results' / 'group_level'
results_dir.mkdir(parents=True, exist_ok=True)

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

# ============================================================================
# Helper Functions
# ============================================================================

def load_activation_pattern(subject_id, roi):
    """Load activation pattern and compute color-specific RMS"""
    # Find file matching pattern (use gmFalse_subjFalse version)
    pattern = f'*_sub-{subject_id}_{roi}_*_gmFalse_subjFalse'
    matches = list(data_dir.glob(pattern))

    if not matches:
        raise FileNotFoundError(f"No data found for sub-{subject_id}, {roi}")

    data_file = matches[0]

    # Load amplitudes_z.npy
    amp_file = data_file / 'amplitudes_z.npy'
    if not amp_file.exists():
        raise FileNotFoundError(f"amplitudes_z.npy not found in {data_file}")

    amplitudes_z = np.load(amp_file)  # (n_runs, n_colors, n_voxels)

    # Average across runs
    pattern_data = amplitudes_z.mean(axis=0)  # (8, n_voxels)

    # Compute activation RMS for each color
    color_activation = []
    for c in range(8):
        # RMS of activation across all voxels for this color
        activation_rms = np.sqrt(np.mean(pattern_data[c]**2))
        color_activation.append(activation_rms)

    return np.array(color_activation)

# ============================================================================
# Main Visualization
# ============================================================================

for ROI in ROIS:
    print(f"\nProcessing {ROI}...")

    # Load HC activation patterns
    hc_activations = []
    for hc_id in HC_SUBJECTS:
        activation = load_activation_pattern(hc_id, ROI)
        hc_activations.append(activation)
        print(f"  HC sub-{hc_id}: {activation.shape}")

    hc_activations = np.array(hc_activations)  # (n_hc, 8)
    hc_mean = hc_activations.mean(axis=0)  # (8,)
    hc_std = hc_activations.std(axis=0)  # (8,)

    # Load CVD activation patterns
    cvd_activations = {}
    for cvd_id in CVD_SUBJECTS:
        activation = load_activation_pattern(cvd_id, ROI)
        cvd_activations[cvd_id] = activation
        print(f"  CVD sub-{cvd_id}: {activation.shape}")

    # ========================================================================
    # Create individual polar plots
    # ========================================================================

    fig = plt.figure(figsize=(16, 16))
    ax = fig.add_subplot(111, projection='polar')

    # Convert angles to radians
    angles_rad = np.deg2rad(COLOR_ANGLES)

    # Close the plot by repeating first point
    angles_plot = np.concatenate([angles_rad, [angles_rad[0]]])
    hc_mean_plot = np.concatenate([hc_mean, [hc_mean[0]]])
    hc_std_plot = np.concatenate([hc_std, [hc_std[0]]])

    # Plot HC mean
    ax.plot(angles_plot, hc_mean_plot, 'o-', color='steelblue', linewidth=3,
            markersize=12, label='HC Mean', zorder=3, alpha=0.8)

    # Plot HC uncertainty (shaded region)
    ax.fill_between(angles_plot,
                     hc_mean_plot - hc_std_plot,
                     hc_mean_plot + hc_std_plot,
                     color='lightblue', alpha=0.3, label='HC Variability (±1 SD)', zorder=1)

    # Plot each CVD's activation pattern
    markers = ['s', '^', 'D']  # Different markers for each CVD

    for i, cvd_id in enumerate(CVD_SUBJECTS):
        cvd_activation = cvd_activations[cvd_id]
        cvd_activation_plot = np.concatenate([cvd_activation, [cvd_activation[0]]])

        ax.plot(angles_plot, cvd_activation_plot,
                marker=markers[i], linestyle='--', linewidth=2.5, markersize=10,
                color=CVD_COLORS[cvd_id], alpha=0.9,
                label=f'Sub-{cvd_id} ({CVD_TYPES[cvd_id][:5]})',
                zorder=4)

    # Add connection lines from HC to CVD (showing difference)
    for color_idx in range(8):
        angle = angles_rad[color_idx]
        hc_val = hc_mean[color_idx]

        for cvd_id in CVD_SUBJECTS:
            cvd_val = cvd_activations[cvd_id][color_idx]

            # Color line based on whether CVD is higher or lower
            if cvd_val > hc_val:
                line_color = 'red'  # Over-activation
                alpha = 0.3
            else:
                line_color = 'blue'  # Under-activation
                alpha = 0.3

            # Draw line from HC to CVD
            ax.plot([angle, angle], [hc_val, cvd_val],
                   color=line_color, linestyle=':', linewidth=1.5, alpha=alpha, zorder=2)

    # Add color labels at each angle
    max_radius = max(hc_mean_plot.max(),
                     max([cvd_activations[cid].max() for cid in CVD_SUBJECTS]))
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

    # Highlight red-green axis
    rg_angles = [0, np.pi]
    rg_radius = max_radius * 1.3

    for rg_angle in rg_angles:
        ax.plot([rg_angle, rg_angle], [0, rg_radius],
               color='red', linestyle='--', linewidth=2, alpha=0.3, zorder=0)

    ax.text(0, rg_radius * 0.5, 'R-G Axis', rotation=90, ha='center', va='center',
           fontsize=10, color='red', fontweight='bold', alpha=0.5)
    ax.text(np.pi, rg_radius * 0.5, 'R-G Axis', rotation=-90, ha='center', va='center',
           fontsize=10, color='red', fontweight='bold', alpha=0.5)

    # Blue-Yellow axis
    by_angles = [np.pi/2, 3*np.pi/2]

    for by_angle in by_angles:
        ax.plot([by_angle, by_angle], [0, rg_radius],
               color='blue', linestyle='--', linewidth=2, alpha=0.3, zorder=0)

    ax.text(np.pi/2, rg_radius * 0.5, 'B-Y Axis', rotation=0, ha='center', va='center',
           fontsize=10, color='blue', fontweight='bold', alpha=0.5)
    ax.text(3*np.pi/2, rg_radius * 0.5, 'B-Y Axis', rotation=0, ha='center', va='center',
           fontsize=10, color='blue', fontweight='bold', alpha=0.5)

    # Center text
    ax.text(0, 0, f'{ROI}\nActivation\nPattern',
           ha='center', va='center', fontsize=14, fontweight='bold',
           bbox=dict(boxstyle='round,pad=0.8', facecolor='lightyellow',
                    edgecolor='black', linewidth=2, alpha=0.8),
           zorder=10)

    # Calculate statistics
    over_activation = {}
    under_activation = {}

    for cvd_id in CVD_SUBJECTS:
        over_colors = []
        under_colors = []

        for c_idx in range(8):
            diff = cvd_activations[cvd_id][c_idx] - hc_mean[c_idx]
            diff_pct = (diff / hc_mean[c_idx]) * 100

            if diff > 0:
                over_colors.append((COLOR_NAMES[c_idx], diff_pct))
            else:
                under_colors.append((COLOR_NAMES[c_idx], diff_pct))

        # Find max over/under
        if over_colors:
            max_over = max(over_colors, key=lambda x: x[1])
            over_activation[cvd_id] = max_over
        else:
            over_activation[cvd_id] = ('None', 0)

        if under_colors:
            max_under = min(under_colors, key=lambda x: x[1])
            under_activation[cvd_id] = max_under
        else:
            under_activation[cvd_id] = ('None', 0)

    # Add statistics box
    stats_text = f"""
    Activation Pattern Analysis:

    HC Mean: {hc_mean.mean():.3f} ± {hc_mean.std():.3f}

    CVD vs HC:
    """

    for cvd_id in CVD_SUBJECTS:
        cvd_mean = cvd_activations[cvd_id].mean()
        diff_pct = ((cvd_mean - hc_mean.mean()) / hc_mean.mean()) * 100

        over_color, over_pct = over_activation[cvd_id]
        under_color, under_pct = under_activation[cvd_id]

        stats_text += f"""
    Sub-{cvd_id} ({CVD_TYPES[cvd_id][:5]}):
      Mean: {cvd_mean:.3f} ({diff_pct:+.1f}%)
      Max over: {over_color} ({over_pct:+.1f}%)
      Max under: {under_color} ({under_pct:+.1f}%)
    """

    ax.text(0.02, 0.98, stats_text.strip(), transform=ax.transAxes,
           fontsize=9, va='top', ha='left', family='monospace',
           bbox=dict(boxstyle='round', facecolor='white', alpha=0.8,
                    edgecolor='black', linewidth=1))

    # Configuration
    ax.set_ylim(0, max_radius * 1.35)
    ax.set_theta_zero_location('N')  # 0° at top
    ax.set_theta_direction(-1)  # Clockwise
    ax.set_yticklabels([])
    ax.set_xticks(angles_rad)
    ax.set_xticklabels([f'{int(a)}°' for a in COLOR_ANGLES], fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.3, linewidth=1)

    # Legend
    ax.legend(loc='upper left', bbox_to_anchor=(1.05, 1), fontsize=11,
             framealpha=0.9, edgecolor='black', fancybox=True)

    # Title
    ax.set_title(f'Circular Activation Pattern ({ROI})\n' +
                f'Color-Specific Activation Magnitude (RMS)',
                fontsize=16, fontweight='bold', pad=20)

    # Save
    output_file = results_dir / f'circular_activation_{ROI}.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✅ Saved: {output_file}")

    plt.close()

# ============================================================================
# Create combined figure (V1 and V2 side by side)
# ============================================================================

fig = plt.figure(figsize=(20, 10))

for roi_idx, ROI in enumerate(ROIS):
    print(f"\nCreating combined plot for {ROI}...")

    # Load HC activation patterns
    hc_activations = []
    for hc_id in HC_SUBJECTS:
        activation = load_activation_pattern(hc_id, ROI)
        hc_activations.append(activation)

    hc_activations = np.array(hc_activations)
    hc_mean = hc_activations.mean(axis=0)
    hc_std = hc_activations.std(axis=0)

    # Load CVD activation patterns
    cvd_activations = {}
    for cvd_id in CVD_SUBJECTS:
        activation = load_activation_pattern(cvd_id, ROI)
        cvd_activations[cvd_id] = activation

    # Create subplot
    ax = fig.add_subplot(1, 2, roi_idx + 1, projection='polar')

    # Angles
    angles_rad = np.deg2rad(COLOR_ANGLES)
    angles_plot = np.concatenate([angles_rad, [angles_rad[0]]])
    hc_mean_plot = np.concatenate([hc_mean, [hc_mean[0]]])
    hc_std_plot = np.concatenate([hc_std, [hc_std[0]]])

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
        cvd_activation = cvd_activations[cvd_id]
        cvd_activation_plot = np.concatenate([cvd_activation, [cvd_activation[0]]])

        ax.plot(angles_plot, cvd_activation_plot,
                marker=markers[i], linestyle='--', linewidth=2.5, markersize=10,
                color=CVD_COLORS[cvd_id], alpha=0.9,
                label=f'Sub-{cvd_id} ({CVD_TYPES[cvd_id][:5]})',
                zorder=4)

    # Connection lines
    for color_idx in range(8):
        angle = angles_rad[color_idx]
        hc_val = hc_mean[color_idx]

        for cvd_id in CVD_SUBJECTS:
            cvd_val = cvd_activations[cvd_id][color_idx]

            if cvd_val > hc_val:
                line_color = 'red'
            else:
                line_color = 'blue'

            ax.plot([angle, angle], [hc_val, cvd_val],
                   color=line_color, linestyle=':', linewidth=1.5, alpha=0.3, zorder=2)

    # Color labels
    max_radius = max(hc_mean_plot.max(),
                     max([cvd_activations[cid].max() for cid in CVD_SUBJECTS]))
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

    ax.set_title(f'{ROI} Activation Pattern', fontsize=14, fontweight='bold', pad=15)

fig.suptitle('Circular Color-Space Activation: HC vs CVD\n(Red lines = over-activation, Blue lines = under-activation)',
            fontsize=18, fontweight='bold', y=0.98)

plt.tight_layout(rect=[0, 0, 1, 0.96])

output_file = results_dir / 'circular_activation_combined.png'
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print(f"\n✅ Combined figure saved: {output_file}")

plt.close()

print("\n" + "="*70)
print("CIRCULAR ACTIVATION VISUALIZATION COMPLETE!")
print("="*70)
print("\nGenerated files:")
print(f"  - circular_activation_V1.png")
print(f"  - circular_activation_V2.png")
print(f"  - circular_activation_combined.png")
print("\nKey difference from previous version:")
print("  - Now shows ACTUAL ACTIVATION magnitude (not disparity)")
print("  - HC and CVD directly comparable")
print("  - Red lines = CVD over-activation")
print("  - Blue lines = CVD under-activation")
