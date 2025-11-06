#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
diagnose_roi_alignment.py
--------------------------
Diagnose ROI-functional data alignment issues

This script checks:
1. ROI mask and functional data coordinate spaces
2. Overlap between ROI and functional data
3. Quality of extracted voxel data
4. Visualization of ROI overlay on functional data

Usage:
    python diagnose_roi_alignment.py
"""

import os
import sys
import numpy as np
import nibabel as nib
import matplotlib.pyplot as plt
from pathlib import Path
import glob

# Try different nilearn import versions
try:
    from nilearn.maskers import NiftiMasker
    from nilearn import plotting
    from nilearn import image as nimg
except ImportError:
    from nilearn.input_data import NiftiMasker
    from nilearn import plotting
    from nilearn import image as nimg

from config import cfg


# ============================================================================
# Configuration
# ============================================================================

SUB_ID = cfg.SUB_ID
FMRIPREP_DIR = cfg.fmriprep_dir
DERIVATIVES_DIR = cfg.analysis_dir

print("="*70)
print("ROI-Functional Alignment Diagnostic")
print("="*70)
print(f"Subject: sub-{SUB_ID}")
print(f"fMRIPrep directory: {FMRIPREP_DIR}")
print(f"Derivatives directory: {DERIVATIVES_DIR}")
print()
sys.stdout.flush()


# ============================================================================
# Step 1: Find and Load Files
# ============================================================================

def find_functional_data():
    """Find a representative functional run"""
    func_pattern = os.path.join(
        FMRIPREP_DIR,
        f"sub-{SUB_ID}_*_space-MNI152NLin2009cAsym_*_bold.nii.gz"
    )
    func_files = sorted(glob.glob(func_pattern))

    if not func_files:
        print(f"ERROR: No functional files found with pattern: {func_pattern}")
        return None

    # Use first run as representative
    func_file = func_files[0]
    print(f"[1/6] Found functional data:")
    print(f"  {func_file}")

    # Load and get info
    func_img = nib.load(func_file)
    print(f"  Shape: {func_img.shape}")
    print(f"  Affine:\n{func_img.affine}")
    print(f"  Voxel size: {func_img.header.get_zooms()[:3]} mm")
    print()
    sys.stdout.flush()

    return func_img


def find_roi_masks():
    """Find all available ROI masks"""
    roi_dir = cfg.roi_dir

    if not os.path.exists(roi_dir):
        print(f"ERROR: ROI directory not found: {roi_dir}")
        return []

    roi_pattern = os.path.join(roi_dir, "*.nii*")
    roi_files = sorted(glob.glob(roi_pattern))

    print(f"[2/6] Found {len(roi_files)} ROI masks:")

    roi_info = []
    for roi_file in roi_files:
        roi_name = Path(roi_file).stem.replace(".nii", "")
        roi_img = nib.load(roi_file)
        n_voxels = np.sum(nib.load(roi_file).get_fdata() > 0)

        roi_info.append({
            'name': roi_name,
            'path': roi_file,
            'img': roi_img,
            'n_voxels': n_voxels
        })

        print(f"  {roi_name}:")
        print(f"    Path: {roi_file}")
        print(f"    Shape: {roi_img.shape}")
        print(f"    Voxels: {n_voxels}")
        print(f"    Voxel size: {roi_img.header.get_zooms()[:3]} mm")

    print()
    sys.stdout.flush()
    return roi_info


# ============================================================================
# Step 2: Check Coordinate Space Compatibility
# ============================================================================

def check_coordinate_spaces(func_img, roi_info):
    """Check if ROI and functional data are in same space"""
    print("[3/6] Checking coordinate space compatibility:")

    func_affine = func_img.affine
    func_shape = func_img.shape[:3]

    print(f"  Functional data:")
    print(f"    Shape: {func_shape}")
    print(f"    Affine:\n{func_affine}")
    print()

    compatible = []
    incompatible = []

    for roi in roi_info:
        roi_img = roi['img']
        roi_affine = roi_img.affine
        roi_shape = roi_img.shape[:3]

        # Check if affines match (within tolerance)
        affine_match = np.allclose(func_affine, roi_affine, atol=1e-3)

        # Check if shapes match
        shape_match = func_shape == roi_shape

        status = "✅ COMPATIBLE" if (affine_match and shape_match) else "❌ INCOMPATIBLE"

        print(f"  {roi['name']}: {status}")
        print(f"    Shape match: {shape_match} (ROI: {roi_shape})")
        print(f"    Affine match: {affine_match}")

        if not affine_match:
            print(f"    ROI affine:\n{roi_affine}")
            print(f"    Difference:\n{np.abs(func_affine - roi_affine).max()}")

        if affine_match and shape_match:
            compatible.append(roi)
        else:
            incompatible.append(roi)

        print()

    print(f"Summary: {len(compatible)} compatible, {len(incompatible)} incompatible")
    print()
    sys.stdout.flush()

    return compatible, incompatible


# ============================================================================
# Step 3: Check Spatial Overlap
# ============================================================================

def check_spatial_overlap(func_img, roi_info):
    """Check spatial overlap between functional data and ROI"""
    print("[4/6] Checking spatial overlap:")

    # Get mean functional image (across time)
    if len(func_img.shape) == 4:
        func_data = func_img.get_fdata()
        mean_func = np.mean(func_data, axis=3)
    else:
        mean_func = func_img.get_fdata()

    # Get brain mask (non-zero voxels in functional data)
    brain_mask = mean_func > 0
    n_brain_voxels = np.sum(brain_mask)

    print(f"  Functional brain mask: {n_brain_voxels} non-zero voxels")
    print()

    for roi in roi_info:
        roi_data = roi['img'].get_fdata()
        roi_mask = roi_data > 0

        # Check overlap
        overlap = np.logical_and(roi_mask, brain_mask)
        n_overlap = np.sum(overlap)

        overlap_pct = (n_overlap / roi['n_voxels'] * 100) if roi['n_voxels'] > 0 else 0

        # Check if ROI voxels have functional data
        roi_func_values = mean_func[roi_mask]
        n_nonzero = np.sum(roi_func_values != 0)
        n_zero = np.sum(roi_func_values == 0)

        status = "✅ GOOD" if overlap_pct > 80 else "⚠️ POOR" if overlap_pct > 50 else "❌ BAD"

        print(f"  {roi['name']}: {status}")
        print(f"    ROI voxels: {roi['n_voxels']}")
        print(f"    Overlap with brain: {n_overlap} ({overlap_pct:.1f}%)")
        print(f"    Functional values: {n_nonzero} non-zero, {n_zero} zero")
        print(f"    Value range: [{roi_func_values.min():.2f}, {roi_func_values.max():.2f}]")
        print(f"    Mean value: {roi_func_values.mean():.2f}")
        print()

    sys.stdout.flush()


# ============================================================================
# Step 4: Test Voxel Extraction
# ============================================================================

def test_voxel_extraction(func_img, roi_info):
    """Test if NiftiMasker can extract valid data"""
    print("[5/6] Testing voxel extraction with NiftiMasker:")

    # Get first 10 volumes for testing
    if len(func_img.shape) == 4:
        test_img = nimg.index_img(func_img, slice(0, min(10, func_img.shape[3])))
    else:
        test_img = func_img

    print(f"  Test data shape: {test_img.shape}")
    print()

    for roi in roi_info:
        try:
            masker = NiftiMasker(mask_img=roi['path'], standardize=False)
            masker.fit()

            # Extract data
            extracted = masker.transform(test_img)

            print(f"  {roi['name']}: ✅ Extraction successful")
            print(f"    Extracted shape: {extracted.shape}")
            print(f"    Expected: ({test_img.shape[3] if len(test_img.shape)==4 else 1}, {roi['n_voxels']})")
            print(f"    Value range: [{extracted.min():.2f}, {extracted.max():.2f}]")
            print(f"    Mean: {extracted.mean():.2f}, Std: {extracted.std():.2f}")
            print(f"    Contains NaN: {np.any(np.isnan(extracted))}")
            print(f"    All zeros: {np.all(extracted == 0)}")
            print()

        except Exception as e:
            print(f"  {roi['name']}: ❌ Extraction failed")
            print(f"    Error: {e}")
            print()

    sys.stdout.flush()


# ============================================================================
# Step 5: Visualize ROI Overlay
# ============================================================================

def visualize_roi_overlay(func_img, roi_info, output_dir="roi_diagnostics"):
    """Create visualization of ROI overlaid on functional data"""
    print("[6/6] Creating visualizations:")

    os.makedirs(output_dir, exist_ok=True)

    # Get mean functional image
    if len(func_img.shape) == 4:
        mean_func_img = nimg.mean_img(func_img)
    else:
        mean_func_img = func_img

    for roi in roi_info:
        try:
            fig, axes = plt.subplots(3, 1, figsize=(12, 12))

            # Sagittal view
            plotting.plot_roi(
                roi['img'],
                bg_img=mean_func_img,
                display_mode='x',
                cut_coords=5,
                axes=axes[0],
                title=f"{roi['name']} - Sagittal"
            )

            # Coronal view
            plotting.plot_roi(
                roi['img'],
                bg_img=mean_func_img,
                display_mode='y',
                cut_coords=5,
                axes=axes[1],
                title=f"{roi['name']} - Coronal"
            )

            # Axial view
            plotting.plot_roi(
                roi['img'],
                bg_img=mean_func_img,
                display_mode='z',
                cut_coords=5,
                axes=axes[2],
                title=f"{roi['name']} - Axial"
            )

            plt.tight_layout()

            output_file = os.path.join(output_dir, f"{roi['name']}_overlay.png")
            plt.savefig(output_file, dpi=150, bbox_inches='tight')
            plt.close()

            print(f"  ✅ {roi['name']}: {output_file}")

        except Exception as e:
            print(f"  ❌ {roi['name']}: Failed to create visualization")
            print(f"     Error: {e}")

    print()
    print(f"Visualizations saved to: {output_dir}/")
    print()
    sys.stdout.flush()


# ============================================================================
# Step 6: Generate Report
# ============================================================================

def generate_report(func_img, roi_info, compatible, incompatible):
    """Generate diagnostic report"""
    print("="*70)
    print("DIAGNOSTIC REPORT")
    print("="*70)
    print()

    if not roi_info:
        print("❌ CRITICAL: No ROI masks found!")
        print()
        print("Possible causes:")
        print("  1. ROI masks not created yet (run roi_build.py)")
        print("  2. ROI directory incorrect")
        print("  3. Wrong subject ID")
        print()
        return

    if not compatible:
        print("❌ CRITICAL: No ROI masks are compatible with functional data!")
        print()
        print("Possible causes:")
        print("  1. ROI masks in wrong coordinate space (native vs MNI)")
        print("  2. ROI masks from different subject")
        print("  3. Registration/alignment failed")
        print()
        print("Solutions:")
        print("  1. Check roi_build.py - ensure it uses correct space")
        print("  2. Re-run ROI construction with correct template")
        print("  3. Verify fMRIPrep output space")
        print()
        return

    print(f"✅ Found {len(compatible)} compatible ROI masks")
    print()

    # Check for potential issues
    issues = []

    for roi in compatible:
        roi_data = roi['img'].get_fdata()
        roi_mask = roi_data > 0

        if len(func_img.shape) == 4:
            mean_func = np.mean(func_img.get_fdata(), axis=3)
        else:
            mean_func = func_img.get_fdata()

        brain_mask = mean_func > 0
        overlap = np.logical_and(roi_mask, brain_mask)
        overlap_pct = (np.sum(overlap) / roi['n_voxels'] * 100) if roi['n_voxels'] > 0 else 0

        if overlap_pct < 80:
            issues.append(f"  ⚠️ {roi['name']}: Low overlap ({overlap_pct:.1f}%)")

        roi_func_values = mean_func[roi_mask]
        if np.all(roi_func_values == 0):
            issues.append(f"  ❌ {roi['name']}: All functional values are zero!")
        elif np.mean(roi_func_values == 0) > 0.5:
            issues.append(f"  ⚠️ {roi['name']}: >50% of voxels are zero")

    if issues:
        print("⚠️ Potential Issues Detected:")
        for issue in issues:
            print(issue)
        print()
        print("Recommendations:")
        print("  1. Check registration quality in fMRIPrep QC reports")
        print("  2. Verify ROI construction used correct template")
        print("  3. Consider using different probability threshold for ROI masks")
        print()
    else:
        print("✅ All checks passed!")
        print()
        print("ROI-functional alignment looks good.")
        print("If analysis still fails, check:")
        print("  1. GLM design matrix (event timing)")
        print("  2. Data quality (motion, artifacts)")
        print("  3. Model parameters (lambda, threshold)")
        print()

    sys.stdout.flush()


# ============================================================================
# Main
# ============================================================================

def main():
    # Step 1: Find files
    func_img = find_functional_data()
    if func_img is None:
        print("ERROR: Cannot proceed without functional data")
        return

    roi_info = find_roi_masks()
    if not roi_info:
        print("ERROR: No ROI masks found")
        return

    # Step 2: Check coordinate spaces
    compatible, incompatible = check_coordinate_spaces(func_img, roi_info)

    if not compatible:
        print("ERROR: No compatible ROI masks found!")
        print("Cannot proceed with further checks.")
        generate_report(func_img, roi_info, compatible, incompatible)
        return

    # Step 3-4: Check overlap and extraction (only for compatible masks)
    check_spatial_overlap(func_img, compatible)
    test_voxel_extraction(func_img, compatible)

    # Step 5: Visualize
    visualize_roi_overlay(func_img, compatible)

    # Step 6: Generate report
    generate_report(func_img, roi_info, compatible, incompatible)

    print("="*70)
    print("Diagnostic complete!")
    print("="*70)
    print()
    print("Next steps:")
    print("  1. Review visualizations in roi_diagnostics/")
    print("  2. Check report above for issues")
    print("  3. If issues found, fix and re-run ROI construction")
    print("  4. If all good, investigate GLM/model issues")
    print()
    sys.stdout.flush()


if __name__ == '__main__':
    main()
