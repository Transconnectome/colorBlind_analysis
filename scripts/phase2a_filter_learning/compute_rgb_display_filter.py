#!/usr/bin/env python3
"""
RGB Display Filter: CVD Color Correction via Brain Pattern Transformation

Transforms RGB stimuli to induce HC-like brain responses in CVD individuals
Using Phase 2A filter + W matrix reconstruction
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
COLOR_NAMES = ['Red', 'Orange', 'Yellow', 'Chartreuse',
               'Green', 'Cyan', 'Blue', 'Magenta']

# Original RGB stimuli (8 circular colors)
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
    """
    Create 6 idealized color channel basis functions

    Channels tuned to: 0°, 60°, 120°, 180°, 240°, 300°
    Response: cos²(hue - center) if cos > 0, else 0

    Returns:
        basis: (360, 6) array
    """
    center_hues = np.linspace(0, 360, n_channels, endpoint=False)
    basis = np.zeros((360, n_channels))

    for i, center_hue in enumerate(center_hues):
        for h in range(360):
            # Circular distance
            dist = np.abs(h - center_hue)
            if dist > 180:
                dist = 360 - dist

            # Cosine tuning
            response = np.cos(np.deg2rad(dist))
            if response > 0:
                basis[h, i] = response ** 2
            else:
                basis[h, i] = 0

    return basis


def rgb_to_hue(rgb):
    """
    Convert RGB to hue angle (HSV color space)

    Args:
        rgb: (n_colors, 3) array in [0, 1]

    Returns:
        hue: (n_colors,) array in [0, 360]
    """
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
    """
    Convert HSV to RGB

    Args:
        h: hue (0-360 degrees)
        s: saturation (0-1)
        v: value (0-1)

    Returns:
        rgb: (r, g, b) in [0, 1]
    """
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


def channels_to_hue(channels, basis):
    """
    Convert channel responses to hue angles using correlation matching

    Searches 360-degree continuous spectrum for best-matching hue
    based on cosine similarity with basis functions

    Args:
        channels: (n_colors, 6) - channel responses
        basis: (360, 6) - basis functions

    Returns:
        hue: (n_colors,) - hue angles in degrees
    """
    n_colors = channels.shape[0]
    hue = np.zeros(n_colors, dtype=int)

    for i in range(n_colors):
        # Find best matching hue from 360-degree spectrum
        correlations = []
        for h in range(360):
            template_channels = basis[h]  # (6,)
            corr = np.corrcoef(channels[i], template_channels)[0, 1]
            correlations.append(corr)

        # Best match = highest correlation
        hue[i] = np.argmax(correlations)

    return hue


def procrustes_align(source, target):
    """
    Align source pattern to target using Full Pattern Procrustes

    Applies single unified transformation to entire pattern,
    preserving relative relationships between colors.

    Args:
        source: (n_colors, n_voxels) - pattern to align
        target: (n_colors, n_voxels) - reference pattern

    Returns:
        aligned: (n_colors, n_voxels) - aligned pattern
        disparity: float - Procrustes disparity
    """
    from scipy.spatial import procrustes

    # Full pattern Procrustes: align entire (8, n_voxels) at once
    mtx1, mtx2, disparity = procrustes(target, source)

    return mtx2, disparity


def compute_rgb_filter(subject_id, roi):
    """
    Compute RGB display filter for one subject/ROI

    Pipeline:
    1. Load CVD voxel pattern
    2. Apply Phase 2A filter (A, b) → filtered voxels
    3. Procrustes alignment → target voxels (HC reference space)
    4. Convert to channels using W matrix
    5. Channels → Hue (360° spectrum, correlation-based)
    6. Hue → RGB

    Args:
        subject_id: '08', '09', or '10'
        roi: 'V1' or 'V2'

    Returns:
        RGB_original: (8, 3)
        RGB_modified: (8, 3)
        results: dict with intermediate values
    """
    print(f"\n[RGB Filter] sub-{subject_id} {roi}")

    # 1. Load CVD voxel pattern
    cvd_pattern = np.load(PATTERN_DIR / f"sub-{subject_id}" / f"{roi}_pattern.npy")
    print(f"  CVD pattern: {cvd_pattern.shape}")

    # 2. Load Phase 2A filter
    A = np.load(FILTER_DIR / f"sub-{subject_id}" / roi / "A_matrix.npy")
    b = np.load(FILTER_DIR / f"sub-{subject_id}" / roi / "b_vector.npy")
    print(f"  Filter: A {A.shape}, b {b.shape}")

    # Voxel alignment (W matrix might have different voxel count)
    W = np.load(W_MATRIX_DIR / roi / "W_common.npy")
    print(f"  W matrix: {W.shape}")

    n_voxels = min(cvd_pattern.shape[1], W.shape[0])
    cvd_aligned = cvd_pattern[:, :n_voxels]
    W_aligned = W[:n_voxels, :]

    if n_voxels < cvd_pattern.shape[1]:
        print(f"  ⚠ Voxel alignment: {cvd_pattern.shape[1]} → {n_voxels}")

    # 3. Apply brain filter
    filtered_voxels = cvd_aligned @ A[:n_voxels, :n_voxels] + b[:n_voxels]
    print(f"  Filtered voxels: {filtered_voxels.shape}")

    # 3.5. Procrustes alignment (KEY: aligns to HC reference space)
    hc_reference = np.load(W_MATRIX_DIR / roi / "hc_reference.npy")
    hc_ref_aligned = hc_reference[:, :n_voxels]
    print(f"  HC reference: {hc_ref_aligned.shape}")

    target_voxels, disparity = procrustes_align(filtered_voxels, hc_ref_aligned)
    print(f"  Procrustes-aligned voxels: {target_voxels.shape}")
    print(f"  Procrustes disparity: {disparity:.6f}")

    # 4. Convert to channels
    target_channels = target_voxels @ W_aligned
    print(f"  Target channels: {target_channels.shape}")

    # 5. Channels → Hue
    basis = create_basis_functions(6)
    target_hue = channels_to_hue(target_channels, basis)
    print(f"  Target hue: {target_hue}")

    # 6. Hue → RGB
    RGB_modified = np.zeros((8, 3))
    for i in range(8):
        RGB_modified[i] = hsv_to_rgb(target_hue[i], s=1.0, v=1.0)

    # Compute hue shifts
    original_hue = rgb_to_hue(RGB_ORIGINAL)
    hue_shift = target_hue - original_hue

    # Wrap to [-180, 180]
    hue_shift = np.where(hue_shift > 180, hue_shift - 360, hue_shift)
    hue_shift = np.where(hue_shift < -180, hue_shift + 360, hue_shift)

    print(f"  Hue shifts (°): {hue_shift}")
    print(f"  Mean |shift|: {np.mean(np.abs(hue_shift)):.1f}°")
    print(f"  Channels range: [{target_channels.min():.3f}, {target_channels.max():.3f}]")

    results = {
        'cvd_pattern': cvd_aligned,
        'filtered_voxels': filtered_voxels,
        'target_voxels': target_voxels,
        'target_channels': target_channels,
        'procrustes_disparity': disparity,
        'original_hue': original_hue,
        'target_hue': target_hue,
        'hue_shift': hue_shift,
        'subject_id': subject_id,
        'roi': roi,
    }

    return RGB_ORIGINAL, RGB_modified, results


def visualize_rgb_comparison(RGB_original, RGB_modified, results):
    """
    Visualize Before/After RGB comparison

    Creates:
    1. Color swatches (Before | After)
    2. Hue shift bar chart
    3. Color wheel transformation
    """
    subject_id = results['subject_id']
    roi = results['roi']
    hue_shift = results['hue_shift']

    fig = plt.figure(figsize=(16, 10))
    gs = gridspec.GridSpec(2, 2, hspace=0.3, wspace=0.3)

    # =====================================================================
    # Panel 1: Color Swatches (Before | After)
    # =====================================================================
    ax1 = plt.subplot(gs[0, 0])

    for i in range(8):
        # Before (left half)
        ax1.add_patch(plt.Rectangle((i, 0), 0.45, 1,
                                     facecolor=RGB_original[i], edgecolor='black'))

        # After (right half)
        ax1.add_patch(plt.Rectangle((i + 0.5, 0), 0.45, 1,
                                     facecolor=RGB_modified[i], edgecolor='black'))

        # Label
        ax1.text(i + 0.5, -0.2, COLOR_NAMES[i],
                ha='center', va='top', fontsize=10, rotation=45)

    ax1.set_xlim(-0.2, 8.2)
    ax1.set_ylim(-0.5, 1.2)
    ax1.set_aspect('equal')
    ax1.axis('off')
    ax1.set_title(f'sub-{subject_id} {roi}: RGB Transformation\n'
                  f'Left = Original | Right = Modified',
                  fontsize=12, fontweight='bold')

    # =====================================================================
    # Panel 2: Hue Shift Bar Chart
    # =====================================================================
    ax2 = plt.subplot(gs[0, 1])

    colors_for_bars = [RGB_original[i] for i in range(8)]
    bars = ax2.bar(range(8), hue_shift, color=colors_for_bars,
                   edgecolor='black', linewidth=1.5)

    ax2.axhline(0, color='black', linestyle='--', linewidth=1)
    ax2.set_xticks(range(8))
    ax2.set_xticklabels(COLOR_NAMES, rotation=45, ha='right')
    ax2.set_ylabel('Hue Shift (degrees)', fontsize=11, fontweight='bold')
    ax2.set_title(f'Hue Shifts: Mean |shift| = {np.mean(np.abs(hue_shift)):.1f}°',
                  fontsize=12, fontweight='bold')
    ax2.grid(axis='y', alpha=0.3)

    # =====================================================================
    # Panel 3: Color Wheel (Before)
    # =====================================================================
    ax3 = plt.subplot(gs[1, 0], projection='polar')

    original_hue = results['original_hue']
    theta_orig = np.deg2rad(original_hue)

    for i in range(8):
        ax3.scatter(theta_orig[i], 1, s=500, c=[RGB_original[i]],
                   edgecolor='black', linewidth=2, zorder=3)
        ax3.text(theta_orig[i], 1.15, COLOR_NAMES[i],
                ha='center', va='center', fontsize=9, fontweight='bold')

    ax3.set_ylim(0, 1.3)
    ax3.set_theta_zero_location('E')
    ax3.set_theta_direction(1)
    ax3.set_title('Original Colors (CVD Input)',
                  fontsize=12, fontweight='bold', pad=20)

    # =====================================================================
    # Panel 4: Color Wheel (After)
    # =====================================================================
    ax4 = plt.subplot(gs[1, 1], projection='polar')

    target_hue = results['target_hue']
    theta_target = np.deg2rad(target_hue)

    # Draw arrows showing transformation
    for i in range(8):
        # Original position (faint)
        ax4.scatter(theta_orig[i], 1, s=300, c=[RGB_original[i]],
                   alpha=0.3, edgecolor='gray', linewidth=1, zorder=2)

        # Target position (solid)
        ax4.scatter(theta_target[i], 1, s=500, c=[RGB_modified[i]],
                   edgecolor='black', linewidth=2, zorder=3)

        # Arrow
        ax4.annotate('', xy=(theta_target[i], 1), xytext=(theta_orig[i], 1),
                    arrowprops=dict(arrowstyle='->', lw=2, color='black'))

        ax4.text(theta_target[i], 1.15, COLOR_NAMES[i],
                ha='center', va='center', fontsize=9, fontweight='bold')

    ax4.set_ylim(0, 1.3)
    ax4.set_theta_zero_location('E')
    ax4.set_theta_direction(1)
    ax4.set_title('Modified Colors (HC-like Target)',
                  fontsize=12, fontweight='bold', pad=20)

    # =====================================================================
    # Overall title
    # =====================================================================
    disparity = results['procrustes_disparity']
    mean_shift = np.mean(np.abs(hue_shift))

    plt.suptitle(f'RGB Display Filter: sub-{subject_id} {roi}\n'
                 f'CVD Input → Brain Filter → Procrustes Alignment → HC-like Output\n'
                 f'Disparity: {disparity:.6f} | Mean Hue Shift: {mean_shift:.1f}°',
                 fontsize=13, fontweight='bold', y=0.98)

    # Save
    output_file = OUTPUT_DIR / f"rgb_filter_sub{subject_id}_{roi}.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  Saved: {output_file}")
    plt.close()


def main():
    """Main execution"""
    print("=" * 70)
    print("RGB Display Filter Computation (baseline32)")
    print("=" * 70)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_results = {}

    for roi in ['V1', 'V2']:
        for subject_id in CVD_SUBJECTS:
            # Compute filter
            RGB_orig, RGB_mod, results = compute_rgb_filter(subject_id, roi)

            # Visualize
            visualize_rgb_comparison(RGB_orig, RGB_mod, results)

            # Store
            all_results[f"sub-{subject_id}_{roi}"] = results

    print("\n" + "=" * 70)
    print("RGB Display Filter Complete!")
    print(f"Output: {OUTPUT_DIR}")
    print("  - rgb_filter_sub08_V1.png")
    print("  - rgb_filter_sub08_V2.png")
    print("  - ... (6 files total)")
    print("=" * 70)

    # Summary statistics
    print("\nSummary: Mean |Hue Shift| (degrees)")
    print("-" * 40)
    for roi in ['V1', 'V2']:
        print(f"\n{roi}:")
        for subject_id in CVD_SUBJECTS:
            key = f"sub-{subject_id}_{roi}"
            mean_shift = np.mean(np.abs(all_results[key]['hue_shift']))
            print(f"  sub-{subject_id}: {mean_shift:.1f}°")


if __name__ == "__main__":
    main()
