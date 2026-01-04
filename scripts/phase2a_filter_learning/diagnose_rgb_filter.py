#!/usr/bin/env python3
"""
RGB Display Filter Diagnosis

Tests 3 different Procrustes alignment methods:
1. Color-wise Procrustes (current implementation)
2. Full pattern Procrustes (entire 8×n at once)
3. Learned Procrustes model (from Phase 1)
"""

import numpy as np
import pickle
from pathlib import Path
from scipy.spatial import procrustes

# Configuration
BASE_DIR = Path("/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis")
PATTERN_DIR = BASE_DIR / "results/group_level/phase2a_data/patterns"
FILTER_DIR = BASE_DIR / "results/filters/models/optionD/20251219_122240"
W_MATRIX_DIR = BASE_DIR / "results/group_level/procrustes_reconstruction_baseline32"

CVD_SUBJECTS = ['08', '09', '10']
ROIS = ['V1', 'V2']


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


# Original RGB (8 colors)
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


def method_1_colorwise(filtered_voxels, hc_reference):
    """Method 1: Color-wise Procrustes (current)"""
    aligned = np.zeros_like(filtered_voxels)
    disparities = []

    for i in range(filtered_voxels.shape[0]):
        mtx1, mtx2, disparity = procrustes(
            hc_reference[i].reshape(-1, 1),
            filtered_voxels[i].reshape(-1, 1)
        )
        aligned[i] = mtx2.flatten()
        disparities.append(disparity)

    mean_disparity = np.mean(disparities)
    return aligned, mean_disparity


def method_2_full_pattern(filtered_voxels, hc_reference):
    """Method 2: Full pattern Procrustes"""
    mtx1, mtx2, disparity = procrustes(hc_reference, filtered_voxels)
    aligned = mtx2
    return aligned, disparity


def method_3_learned_model(filtered_voxels, roi):
    """Method 3: Use Phase 1 learned Procrustes model"""
    model_path = W_MATRIX_DIR / roi / "procrustes_model.pkl"

    with open(model_path, 'rb') as f:
        model = pickle.load(f)

    # Check what's in the model
    print(f"    Procrustes model keys: {model.keys() if isinstance(model, dict) else type(model)}")

    # Try to apply transformation
    # Model structure depends on how it was saved
    if isinstance(model, dict):
        if 'R' in model and 's' in model and 'T' in model:
            # Manual application: aligned = s * filtered @ R + T
            R = model['R']
            s = model['s']
            T = model['T']
            aligned = s * (filtered_voxels @ R) + T
            disparity = np.linalg.norm(aligned - hc_reference, 'fro') / np.sqrt(aligned.size)
        else:
            print(f"    ⚠️ Unknown model structure: {model.keys()}")
            aligned = filtered_voxels
            disparity = np.nan
    else:
        # Assume it's a fitted object with transform method
        try:
            aligned = model.transform(filtered_voxels)
            disparity = np.linalg.norm(aligned - hc_reference, 'fro') / np.sqrt(aligned.size)
        except:
            print(f"    ⚠️ Cannot transform with model type: {type(model)}")
            aligned = filtered_voxels
            disparity = np.nan

    return aligned, disparity


def diagnose_subject(subject_id, roi):
    """Run diagnosis for one subject/ROI"""
    print(f"\n{'='*70}")
    print(f"DIAGNOSIS: sub-{subject_id} {roi}")
    print(f"{'='*70}")

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

    print(f"Voxels: CVD {cvd_pattern.shape[1]} → aligned {n_voxels}")

    # Apply filter
    filtered_voxels = cvd_aligned @ A[:n_voxels, :n_voxels] + b[:n_voxels]
    print(f"Filtered voxels: {filtered_voxels.shape}")

    # Basis functions
    basis = create_basis_functions(6)
    original_hue = rgb_to_hue(RGB_ORIGINAL)

    results = {}

    # =========================================================================
    # Method 1: Color-wise Procrustes
    # =========================================================================
    print(f"\n[Method 1] Color-wise Procrustes")
    aligned_1, disparity_1 = method_1_colorwise(filtered_voxels, hc_ref_aligned)
    channels_1 = aligned_1 @ W_aligned
    hue_1 = channels_to_hue(channels_1, basis)
    shift_1 = hue_1 - original_hue
    shift_1 = np.where(shift_1 > 180, shift_1 - 360, shift_1)
    shift_1 = np.where(shift_1 < -180, shift_1 + 360, shift_1)
    mean_shift_1 = np.mean(np.abs(shift_1))

    print(f"  Procrustes disparity: {disparity_1:.6f}")
    print(f"  Channels range: [{channels_1.min():.2f}, {channels_1.max():.2f}]")
    print(f"  Channels mean: {channels_1.mean(axis=0)}")
    print(f"  Target hue: {hue_1}")
    print(f"  Mean |shift|: {mean_shift_1:.1f}°")

    results['method_1'] = {
        'disparity': disparity_1,
        'channels': channels_1,
        'hue': hue_1,
        'shift': shift_1,
        'mean_shift': mean_shift_1
    }

    # =========================================================================
    # Method 2: Full pattern Procrustes
    # =========================================================================
    print(f"\n[Method 2] Full pattern Procrustes")
    aligned_2, disparity_2 = method_2_full_pattern(filtered_voxels, hc_ref_aligned)
    channels_2 = aligned_2 @ W_aligned
    hue_2 = channels_to_hue(channels_2, basis)
    shift_2 = hue_2 - original_hue
    shift_2 = np.where(shift_2 > 180, shift_2 - 360, shift_2)
    shift_2 = np.where(shift_2 < -180, shift_2 + 360, shift_2)
    mean_shift_2 = np.mean(np.abs(shift_2))

    print(f"  Procrustes disparity: {disparity_2:.6f}")
    print(f"  Channels range: [{channels_2.min():.2f}, {channels_2.max():.2f}]")
    print(f"  Channels mean: {channels_2.mean(axis=0)}")
    print(f"  Target hue: {hue_2}")
    print(f"  Mean |shift|: {mean_shift_2:.1f}°")

    results['method_2'] = {
        'disparity': disparity_2,
        'channels': channels_2,
        'hue': hue_2,
        'shift': shift_2,
        'mean_shift': mean_shift_2
    }

    # =========================================================================
    # Method 3: Learned Procrustes model
    # =========================================================================
    print(f"\n[Method 3] Learned Procrustes model")
    try:
        aligned_3, disparity_3 = method_3_learned_model(filtered_voxels, roi)
        channels_3 = aligned_3 @ W_aligned
        hue_3 = channels_to_hue(channels_3, basis)
        shift_3 = hue_3 - original_hue
        shift_3 = np.where(shift_3 > 180, shift_3 - 360, shift_3)
        shift_3 = np.where(shift_3 < -180, shift_3 + 360, shift_3)
        mean_shift_3 = np.mean(np.abs(shift_3))

        print(f"  Procrustes disparity: {disparity_3:.6f}")
        print(f"  Channels range: [{channels_3.min():.2f}, {channels_3.max():.2f}]")
        print(f"  Channels mean: {channels_3.mean(axis=0)}")
        print(f"  Target hue: {hue_3}")
        print(f"  Mean |shift|: {mean_shift_3:.1f}°")

        results['method_3'] = {
            'disparity': disparity_3,
            'channels': channels_3,
            'hue': hue_3,
            'shift': shift_3,
            'mean_shift': mean_shift_3
        }
    except Exception as e:
        print(f"  ❌ Error: {e}")
        results['method_3'] = {'error': str(e)}

    # =========================================================================
    # Summary comparison
    # =========================================================================
    print(f"\n{'='*70}")
    print(f"COMPARISON")
    print(f"{'='*70}")
    print(f"Method 1 (Color-wise):     {mean_shift_1:.1f}° (disparity {disparity_1:.6f})")
    print(f"Method 2 (Full pattern):   {mean_shift_2:.1f}° (disparity {disparity_2:.6f})")
    if 'error' not in results['method_3']:
        print(f"Method 3 (Learned model):  {mean_shift_3:.1f}° (disparity {disparity_3:.6f})")
    else:
        print(f"Method 3 (Learned model):  ERROR")

    return results


def main():
    """Run diagnosis for all subjects/ROIs"""
    print("=" * 70)
    print("RGB Display Filter Diagnosis")
    print("Testing 3 Procrustes alignment methods")
    print("=" * 70)

    all_results = {}

    # Test one subject first
    for roi in ROIS:
        for subject_id in CVD_SUBJECTS:
            key = f"sub-{subject_id}_{roi}"
            results = diagnose_subject(subject_id, roi)
            all_results[key] = results

    # Overall summary
    print(f"\n\n{'='*70}")
    print(f"OVERALL SUMMARY")
    print(f"{'='*70}")

    for roi in ROIS:
        print(f"\n{roi}:")
        for subject_id in CVD_SUBJECTS:
            key = f"sub-{subject_id}_{roi}"
            r = all_results[key]

            m1 = r['method_1']['mean_shift']
            m2 = r['method_2']['mean_shift']

            if 'error' not in r['method_3']:
                m3 = r['method_3']['mean_shift']
                print(f"  sub-{subject_id}: M1={m1:.1f}°  M2={m2:.1f}°  M3={m3:.1f}°")
            else:
                print(f"  sub-{subject_id}: M1={m1:.1f}°  M2={m2:.1f}°  M3=ERROR")


if __name__ == "__main__":
    main()
