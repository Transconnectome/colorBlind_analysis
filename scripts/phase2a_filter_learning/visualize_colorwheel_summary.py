#!/usr/bin/env python3
"""
Color Wheel Transformation Summary

Extracts color wheel transformations from RGB display filter results
and displays all 6 (3 subjects × 2 ROIs) in a single figure.
"""

import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

# Configuration
BASE_DIR = Path("/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis")
PATTERN_DIR = BASE_DIR / "results/group_level/phase2a_data/patterns"
FILTER_DIR = BASE_DIR / "results/filters/models/optionD/20251219_122240"
W_MATRIX_DIR = BASE_DIR / "results/group_level/procrustes_reconstruction_baseline32"
OUTPUT_DIR = BASE_DIR / "results/filters/analysis/rgb_display_filter"

CVD_SUBJECTS = ['08', '09', '10']
ROIS = ['V1', 'V2']
COLOR_NAMES = ['Red', 'Orange', 'Yellow', 'Chartreuse',
               'Green', 'Cyan', 'Blue', 'Magenta']

# Original RGB stimuli
RGB_ORIGINAL = np.array([
    [1.0, 0.0, 0.0],  # Red (0°)
    [1.0, 0.5, 0.0],  # Orange (30°)
    [1.0, 1.0, 0.0],  # Yellow (60°)
    [0.5, 1.0, 0.0],  # Chartreuse (90°)
    [0.0, 1.0, 0.0],  # Green (120°)
    [0.0, 1.0, 1.0],  # Cyan (180°)
    [0.0, 0.0, 1.0],  # Blue (240°)
    [1.0, 0.0, 1.0],  # Magenta (300°)
])


def create_basis_functions(n_channels=6):
    """Create 6 idealized color channel basis functions"""
    hues = np.linspace(0, 360, n_channels, endpoint=False)
    basis = np.zeros((360, n_channels))

    for i, center_hue in enumerate(hues):
        for h in range(360):
            dist = np.abs(h - center_hue)
            if dist > 180:
                dist = 360 - dist
            response = np.cos(np.deg2rad(dist))
            if response > 0:
                basis[h, i] = response ** 2
            else:
                basis[h, i] = 0

    return basis


def channels_to_hue(channels, basis):
    """Convert channel responses to hue using correlation matching"""
    n_colors = channels.shape[0]
    hue = np.zeros(n_colors, dtype=int)

    for i in range(n_colors):
        correlations = []
        for h in range(360):
            template_channels = basis[h]
            corr = np.corrcoef(channels[i], template_channels)[0, 1]
            correlations.append(corr)
        hue[i] = np.argmax(correlations)

    return hue


def procrustes_align(source, target):
    """Align source pattern to target using Full Pattern Procrustes"""
    from scipy.spatial import procrustes
    mtx1, mtx2, disparity = procrustes(target, source)
    return mtx2, disparity


def rgb_to_hue(rgb):
    """Convert RGB to hue angle"""
    hues = []
    for r, g, b in rgb:
        max_c = max(r, g, b)
        min_c = min(r, g, b)
        delta = max_c - min_c

        if delta == 0:
            h = 0
        elif max_c == r:
            h = 60 * (((g - b) / delta) % 6)
        elif max_c == g:
            h = 60 * (((b - r) / delta) + 2)
        else:
            h = 60 * (((r - g) / delta) + 4)

        hues.append(h)

    return np.array(hues)


def hsv_to_rgb(h, s, v):
    """Convert HSV to RGB"""
    h = h / 60.0
    c = v * s
    x = c * (1 - abs((h % 2) - 1))
    m = v - c

    if 0 <= h < 1:
        r, g, b = c, x, 0
    elif 1 <= h < 2:
        r, g, b = x, c, 0
    elif 2 <= h < 3:
        r, g, b = 0, c, x
    elif 3 <= h < 4:
        r, g, b = 0, x, c
    elif 4 <= h < 5:
        r, g, b = x, 0, c
    else:
        r, g, b = c, 0, x

    return np.array([r + m, g + m, b + m])


def compute_transformation(subject_id, roi):
    """Compute RGB transformation for one subject/ROI"""
    # Load data
    cvd_pattern = np.load(PATTERN_DIR / f"sub-{subject_id}" / f"{roi}_pattern.npy")
    A = np.load(FILTER_DIR / f"sub-{subject_id}" / roi / "A_matrix.npy")
    b = np.load(FILTER_DIR / f"sub-{subject_id}" / roi / "b_vector.npy")
    W = np.load(W_MATRIX_DIR / roi / "W_common.npy")
    hc_reference = np.load(W_MATRIX_DIR / roi / "hc_reference.npy")

    # Voxel alignment
    n_voxels = min(cvd_pattern.shape[1], W.shape[0], hc_reference.shape[1])
    cvd_aligned = cvd_pattern[:, :n_voxels]
    W_aligned = W[:n_voxels, :]
    hc_ref_aligned = hc_reference[:, :n_voxels]

    # Apply filter
    filtered_voxels = cvd_aligned @ A[:n_voxels, :n_voxels] + b[:n_voxels]

    # Procrustes alignment
    target_voxels, disparity = procrustes_align(filtered_voxels, hc_ref_aligned)

    # Convert to channels
    target_channels = target_voxels @ W_aligned

    # Channels → Hue
    basis = create_basis_functions(6)
    target_hue = channels_to_hue(target_channels, basis)

    # Hue → RGB
    RGB_modified = np.zeros((8, 3))
    for i in range(8):
        RGB_modified[i] = hsv_to_rgb(target_hue[i], s=1.0, v=1.0)

    # Compute shifts
    original_hue = rgb_to_hue(RGB_ORIGINAL)
    hue_shift = target_hue - original_hue
    hue_shift = np.where(hue_shift > 180, hue_shift - 360, hue_shift)
    hue_shift = np.where(hue_shift < -180, hue_shift + 360, hue_shift)

    return {
        'original_hue': original_hue,
        'target_hue': target_hue,
        'RGB_original': RGB_ORIGINAL,
        'RGB_modified': RGB_modified,
        'hue_shift': hue_shift,
        'mean_shift': np.mean(np.abs(hue_shift)),
        'disparity': disparity,
    }


def main():
    """Create summary figure with all 6 color wheel transformations"""
    print("=" * 70)
    print("Color Wheel Transformation Summary")
    print("=" * 70)

    # Compute all transformations
    all_results = {}
    for subject_id in CVD_SUBJECTS:
        for roi in ROIS:
            print(f"\nProcessing sub-{subject_id} {roi}...")
            results = compute_transformation(subject_id, roi)
            all_results[f"sub-{subject_id}_{roi}"] = results
            print(f"  Mean shift: {results['mean_shift']:.1f}°")
            print(f"  Disparity: {results['disparity']:.6f}")

    # Create figure: 2 rows (V1, V2) × 3 columns (sub-08, 09, 10)
    fig = plt.figure(figsize=(18, 12))
    gs = gridspec.GridSpec(2, 3, hspace=0.25, wspace=0.2)

    # Plot each transformation
    for row, roi in enumerate(ROIS):
        for col, subject_id in enumerate(CVD_SUBJECTS):
            key = f"sub-{subject_id}_{roi}"
            results = all_results[key]

            # Create polar subplot
            ax = plt.subplot(gs[row, col], projection='polar')

            original_hue = results['original_hue']
            target_hue = results['target_hue']
            RGB_original = results['RGB_original']
            RGB_modified = results['RGB_modified']
            mean_shift = results['mean_shift']
            disparity = results['disparity']

            theta_orig = np.deg2rad(original_hue)
            theta_target = np.deg2rad(target_hue)

            # Draw transformation arrows
            for i in range(8):
                # Original position (faint)
                ax.scatter(theta_orig[i], 1, s=300, c=[RGB_original[i]],
                          alpha=0.3, edgecolor='gray', linewidth=1, zorder=2)

                # Target position (solid)
                ax.scatter(theta_target[i], 1, s=500, c=[RGB_modified[i]],
                          edgecolor='black', linewidth=2, zorder=3)

                # Arrow showing transformation
                ax.annotate('', xy=(theta_target[i], 1), xytext=(theta_orig[i], 1),
                           arrowprops=dict(arrowstyle='->', lw=2, color='black'))

                # Color labels
                ax.text(theta_target[i], 1.15, COLOR_NAMES[i],
                       ha='center', va='center', fontsize=9, fontweight='bold')

            ax.set_ylim(0, 1.3)
            ax.set_theta_zero_location('E')
            ax.set_theta_direction(1)

            # Title with subject/ROI only
            ax.set_title(f'sub-{subject_id} {roi}',
                        fontsize=12, fontweight='bold', pad=15)

    # Save
    output_file = OUTPUT_DIR / "colorwheel_summary_all.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\n{'='*70}")
    print(f"Saved: {output_file}")
    print(f"{'='*70}")

    # Summary statistics
    print("\nSummary Statistics:")
    print("-" * 70)
    for roi in ROIS:
        print(f"\n{roi}:")
        shifts = []
        disparities = []
        for subject_id in CVD_SUBJECTS:
            key = f"sub-{subject_id}_{roi}"
            results = all_results[key]
            shifts.append(results['mean_shift'])
            disparities.append(results['disparity'])
            print(f"  sub-{subject_id}: {results['mean_shift']:.1f}° shift, "
                  f"{results['disparity']:.6f} disparity")

        print(f"  Average: {np.mean(shifts):.1f}° shift (SD={np.std(shifts):.1f}°)")
        print(f"  Average disparity: {np.mean(disparities):.6f}")


if __name__ == "__main__":
    main()
