#!/usr/bin/env python3
"""
Diagnose Filter + W Matrix Issue

Tests:
1. CVD raw + W (no filter) - Baseline voxel compatibility
2. CVD raw + Filter + W (current) - Current pipeline
3. CVD raw + Filter + Procrustes + W - Proposed fix

Usage:
    python scripts/diagnose_filter_issue.py --subject 08 --roi V1
"""

import numpy as np
import pickle
from pathlib import Path
import argparse
from scipy.spatial import procrustes

# ============================================================================
# Configuration
# ============================================================================

BASE_DIR = Path.cwd()
DERIVATIVES_DIR = BASE_DIR / "derivatives/BH2009_deoblique_v2/baseline32_deob_determin"
FILTER_DIR = BASE_DIR / "results/group_level/phase2a_data/models_optionA"
W_DIR = BASE_DIR / "results/group_level/procrustes_reconstruction_baseline32"

LABEL2HUE_DEG = {
    'color_1': 0.0, 'color_2': 45.0, 'color_3': 90.0, 'color_4': 135.0,
    'color_5': 180.0, 'color_6': 225.0, 'color_7': 270.0, 'color_8': 315.0,
}

COLOR_NAMES = ['Red', 'Orange', 'Yellow', 'Chartreuse',
               'Green', 'Cyan', 'Blue', 'Magenta']

# ============================================================================
# Helper Functions
# ============================================================================

def create_basis_functions(n_channels=6):
    """Create 6-channel color basis functions"""
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


def circular_diff_deg(a, b):
    """Circular distance in degrees"""
    diff = np.abs(a - b)
    diff = np.where(diff > 180, 360 - diff, diff)
    return diff


def reconstruct_hues(C_estimated, basis):
    """Reconstruct hues from channels"""
    n_colors = C_estimated.shape[0]
    reconstructed_hues = []
    errors = []

    for color_idx in range(n_colors):
        channels = C_estimated[color_idx, :]

        # Find best matching hue
        correlations = []
        for h in range(360):
            template = basis[h, :]
            corr = np.corrcoef(channels, template)[0, 1]
            correlations.append(corr)

        best_hue = np.argmax(correlations)
        reconstructed_hues.append(best_hue)

        # Compute error
        true_hue = LABEL2HUE_DEG[f'color_{color_idx + 1}']
        error = circular_diff_deg(best_hue, true_hue)
        errors.append(error)

    return np.array(reconstructed_hues), np.array(errors)


# ============================================================================
# Load Functions
# ============================================================================

def load_cvd_raw(subject_id, roi):
    """Load CVD raw voxel pattern"""
    pattern_glob = list(DERIVATIVES_DIR.glob(f"*sub-{subject_id}_{roi}_*"))
    if not pattern_glob:
        raise FileNotFoundError(f"No baseline results for sub-{subject_id} {roi}")

    result_dir = pattern_glob[0]
    amp_file = result_dir / "amplitudes_z.npy"
    amplitudes_z = np.load(amp_file)
    pattern = np.mean(amplitudes_z, axis=0)  # (8, n_voxels)

    return pattern


def load_filter(subject_id, roi):
    """Load Phase 2A filter"""
    filter_path = FILTER_DIR / f"sub-{subject_id}" / roi
    A = np.load(filter_path / "A_matrix.npy")
    b = np.load(filter_path / "b_vector.npy")
    return A, b


def load_w_matrix(roi):
    """Load Procrustes W matrix and HC reference"""
    model_path = W_DIR / roi / "procrustes_model.pkl"
    with open(model_path, 'rb') as f:
        model_data = pickle.load(f)

    W = model_data['W_common']
    basis = model_data['basis_functions']
    hc_reference = model_data['hc_reference']

    return W, basis, hc_reference


# ============================================================================
# Test Functions
# ============================================================================

def test_raw_with_w(CVD_raw, W, basis, min_voxels):
    """Test 1: CVD raw + W (no filter)"""
    print("\n" + "="*70)
    print("TEST 1: CVD raw + W (no filter)")
    print("="*70)

    X = CVD_raw[:, :min_voxels]
    W_trunc = W[:min_voxels, :]

    C = np.linalg.pinv(W_trunc.T @ W_trunc) @ W_trunc.T @ X.T
    C = C.T  # (8, 6)

    hues, errors = reconstruct_hues(C, basis)

    print(f"\nResults:")
    for i, (name, hue, err) in enumerate(zip(COLOR_NAMES, hues, errors)):
        true_hue = LABEL2HUE_DEG[f'color_{i+1}']
        print(f"  {name:12s}: {true_hue:6.1f}° → {hue:6.1f}° (error: {err:5.1f}°)")

    mean_error = np.mean(errors)
    print(f"\n  Mean error: {mean_error:.1f}°")
    print(f"  Interpretation: ", end="")
    if mean_error < 45:
        print("✅ Good - voxel truncation OK")
    elif mean_error < 90:
        print("⚠️  Moderate - voxel truncation may be issue")
    else:
        print("❌ Bad - voxel mismatch problem")

    return mean_error


def test_filter_with_w(CVD_raw, A, b, W, basis, min_voxels):
    """Test 2: CVD raw + Filter + W (current pipeline)"""
    print("\n" + "="*70)
    print("TEST 2: CVD raw + Filter + W (current pipeline)")
    print("="*70)

    X_filtered = CVD_raw @ A + b
    X_filtered = X_filtered[:, :min_voxels]
    W_trunc = W[:min_voxels, :]

    C = np.linalg.pinv(W_trunc.T @ W_trunc) @ W_trunc.T @ X_filtered.T
    C = C.T

    hues, errors = reconstruct_hues(C, basis)

    print(f"\nResults:")
    for i, (name, hue, err) in enumerate(zip(COLOR_NAMES, hues, errors)):
        true_hue = LABEL2HUE_DEG[f'color_{i+1}']
        print(f"  {name:12s}: {true_hue:6.1f}° → {hue:6.1f}° (error: {err:5.1f}°)")

    mean_error = np.mean(errors)
    print(f"\n  Mean error: {mean_error:.1f}°")
    print(f"  Interpretation: ", end="")
    if mean_error < 45:
        print("✅ Good - filter compatible with W")
    elif mean_error < 90:
        print("⚠️  Moderate - filter partially compatible")
    else:
        print("❌ Bad - filter incompatible with W space")

    return mean_error


def test_filter_procrustes_w(CVD_raw, A, b, W, basis, hc_reference, min_voxels):
    """Test 3: CVD raw + Filter + Procrustes + W (proposed fix)"""
    print("\n" + "="*70)
    print("TEST 3: CVD raw + Filter + Procrustes + W (proposed fix)")
    print("="*70)

    # Apply filter
    X_filtered = CVD_raw @ A + b
    X_filtered = X_filtered[:, :min_voxels]

    # Procrustes alignment
    hc_ref_trunc = hc_reference[:, :min_voxels]
    _, X_aligned, disparity = procrustes(hc_ref_trunc, X_filtered)

    print(f"  Procrustes disparity: {disparity:.4f}")

    # Apply W
    W_trunc = W[:min_voxels, :]
    C = np.linalg.pinv(W_trunc.T @ W_trunc) @ W_trunc.T @ X_aligned.T
    C = C.T

    hues, errors = reconstruct_hues(C, basis)

    print(f"\nResults:")
    for i, (name, hue, err) in enumerate(zip(COLOR_NAMES, hues, errors)):
        true_hue = LABEL2HUE_DEG[f'color_{i+1}']
        print(f"  {name:12s}: {true_hue:6.1f}° → {hue:6.1f}° (error: {err:5.1f}°)")

    mean_error = np.mean(errors)
    print(f"\n  Mean error: {mean_error:.1f}°")
    print(f"  Interpretation: ", end="")
    if mean_error < 45:
        print("✅ Excellent - Procrustes fixes the issue!")
    elif mean_error < 90:
        print("⚠️  Moderate - partial improvement")
    else:
        print("❌ Still bad - other issues present")

    return mean_error


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Diagnose filter + W matrix issue')
    parser.add_argument('--subject', type=str, required=True)
    parser.add_argument('--roi', type=str, required=True)
    args = parser.parse_args()

    print(f"\n{'='*70}")
    print(f"Diagnostic Analysis: sub-{args.subject} {args.roi}")
    print(f"{'='*70}")

    # Load data
    print("\nLoading data...")
    CVD_raw = load_cvd_raw(args.subject, args.roi)
    A, b = load_filter(args.subject, args.roi)
    W, basis, hc_reference = load_w_matrix(args.roi)

    print(f"  CVD raw: {CVD_raw.shape}")
    print(f"  Filter A: {A.shape}")
    print(f"  W matrix: {W.shape}")
    print(f"  HC reference: {hc_reference.shape}")

    min_voxels = min(CVD_raw.shape[1], W.shape[0])
    print(f"  Using min voxels: {min_voxels}")

    # Run tests
    error1 = test_raw_with_w(CVD_raw, W, basis, min_voxels)
    error2 = test_filter_with_w(CVD_raw, A, b, W, basis, min_voxels)
    error3 = test_filter_procrustes_w(CVD_raw, A, b, W, basis, hc_reference, min_voxels)

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Test 1 (Raw + W):                {error1:6.1f}°")
    print(f"Test 2 (Filter + W):             {error2:6.1f}°")
    print(f"Test 3 (Filter + Procrustes + W): {error3:6.1f}°")
    print(f"\nFilter impact:      {error2 - error1:+6.1f}° (negative = worse)")
    print(f"Procrustes benefit: {error2 - error3:+6.1f}° (positive = improvement)")

    print("\n" + "="*70)
    print("RECOMMENDATION")
    print("="*70)

    if error3 < error2 and error3 < 45:
        print("✅ Use Procrustes alignment after filter!")
        print("   Filter + Procrustes + W is the best approach.")
    elif error1 < error2:
        print("⚠️  Filter makes things worse!")
        print("   Consider using raw voxels without filter.")
    else:
        print("❌ Multiple issues present - further investigation needed")


if __name__ == '__main__':
    main()
