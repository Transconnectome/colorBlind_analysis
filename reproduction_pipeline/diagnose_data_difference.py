#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
diagnose_data_difference.py
----------------------------
Diagnose why voxel counts are different from expected.

Usage (on server):
    python diagnose_data_difference.py
"""

import sys
from pathlib import Path
import numpy as np
import nibabel as nib
from nilearn import image
from nilearn.masking import compute_epi_mask

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from reproduction_pipeline.config_reproduction_output import cfg

print("="*70)
print("Data Difference Diagnostic")
print("="*70)
print()

# Get paths
func_dir = cfg.get_fmriprep_dir() / "func"
print(f"Functional data directory: {func_dir}")
print(f"Exists: {func_dir.exists()}")
print()

# Find functional files
func_files = list(func_dir.glob("*task-rsvp_run-1*bold.nii.gz"))
if not func_files:
    print("ERROR: No functional files found!")
    sys.exit(1)

ref_path = func_files[0]
print(f"Reference functional file:")
print(f"  {ref_path}")
print()

# Load functional data
print("Loading functional data...")
ref_img = nib.load(ref_path)
ref_data = ref_img.get_fdata()

print(f"Functional data shape: {ref_img.shape}")
print(f"Voxel dimensions: {ref_img.header.get_zooms()[:3]} mm")
print()

# Compute different masks
print("="*70)
print("Mask Comparison")
print("="*70)
print()

# Method 1: nilearn compute_epi_mask (what we're using)
print("Method 1: nilearn compute_epi_mask()")
epi_mask_nilearn = compute_epi_mask(ref_img)
n_nilearn = int(np.sum(epi_mask_nilearn.get_fdata() > 0))
print(f"  Active voxels: {n_nilearn:,}")
print()

# Method 2: Simple threshold (mean > 0)
print("Method 2: Simple threshold (mean > 0)")
mean_func = ref_data.mean(axis=-1)
simple_mask = mean_func > 0
n_simple = int(np.sum(simple_mask))
print(f"  Active voxels: {n_simple:,}")
print()

# Method 3: More permissive threshold (mean > small value)
print("Method 3: Permissive threshold (mean > 10)")
permissive_mask = mean_func > 10
n_permissive = int(np.sum(permissive_mask))
print(f"  Active voxels: {n_permissive:,}")
print()

# Method 4: STD-based mask
print("Method 4: STD-based (std > 10)")
std_func = ref_data.std(axis=-1)
std_mask = std_func > 10
n_std = int(np.sum(std_mask))
print(f"  Active voxels: {n_std:,}")
print()

# Compare masks
print("="*70)
print("Mask Overlap Analysis")
print("="*70)
print()

epi_data = epi_mask_nilearn.get_fdata().astype(bool)
overlap_simple = int(np.sum(epi_data & simple_mask))
overlap_permissive = int(np.sum(epi_data & permissive_mask))
overlap_std = int(np.sum(epi_data & std_mask))

print(f"EPI mask ∩ Simple mask: {overlap_simple:,} voxels ({100*overlap_simple/n_nilearn:.1f}% of EPI)")
print(f"EPI mask ∩ Permissive mask: {overlap_permissive:,} voxels ({100*overlap_permissive/n_nilearn:.1f}% of EPI)")
print(f"EPI mask ∩ STD mask: {overlap_std:,} voxels ({100*overlap_std/n_nilearn:.1f}% of EPI)")
print()

# Check atlas without any mask
print("="*70)
print("Atlas Voxel Counts (NO MASK)")
print("="*70)
print()

atlas_dir = cfg.ATLAS_DIR

for roi_name, roi_parts in cfg.WANG_ROI_MAP.items():
    combined_mask = None
    atlas_affine = None

    for hemi in cfg.HEMISPHERES:
        for part in roi_parts:
            atlas_file = atlas_dir / f"{part}{hemi}.nii.gz"

            if not atlas_file.exists():
                continue

            atlas_img = nib.load(atlas_file)
            atlas_data = atlas_img.get_fdata()
            part_mask = atlas_data > cfg.ROI_PROB_THRESHOLD

            if combined_mask is None:
                combined_mask = part_mask
                atlas_affine = atlas_img.affine
            else:
                combined_mask = np.logical_or(combined_mask, part_mask)

    if combined_mask is None:
        continue

    # Resample to functional space
    mask_img = nib.Nifti1Image(combined_mask.astype(np.int16), atlas_affine)
    mask_resampled = image.resample_img(
        mask_img,
        target_affine=ref_img.affine,
        target_shape=ref_img.shape[:3],
        interpolation='nearest'
    )

    roi_data = mask_resampled.get_fdata().astype(bool)
    n_atlas = int(np.sum(roi_data))

    # Intersect with different masks
    n_with_nilearn = int(np.sum(roi_data & epi_data))
    n_with_simple = int(np.sum(roi_data & simple_mask))
    n_with_permissive = int(np.sum(roi_data & permissive_mask))
    n_with_std = int(np.sum(roi_data & std_mask))

    print(f"{roi_name}:")
    print(f"  Atlas only (resampled): {n_atlas:,} voxels")
    print(f"  With nilearn EPI mask: {n_with_nilearn:,} voxels ({100*n_with_nilearn/n_atlas:.1f}% retained)")
    print(f"  With simple mask: {n_with_simple:,} voxels ({100*n_with_simple/n_atlas:.1f}% retained)")
    print(f"  With permissive mask: {n_with_permissive:,} voxels ({100*n_with_permissive/n_atlas:.1f}% retained)")
    print(f"  With std mask: {n_with_std:,} voxels ({100*n_with_std/n_atlas:.1f}% retained)")
    print()

print("="*70)
print("Expected vs Actual")
print("="*70)
print()

for roi_name in ['V1', 'V2', 'hV4']:
    if roi_name in cfg.EXPECTED_RESULTS:
        expected = cfg.EXPECTED_RESULTS[roi_name]['n_voxels']
        print(f"{roi_name}: Expected {expected:,} voxels")

print()
print("="*70)
print("Recommendation")
print("="*70)
print()

if n_nilearn < 100000:
    print("⚠ WARNING: Functional data has very low brain coverage!")
    print(f"  Current EPI mask: {n_nilearn:,} voxels")
    print(f"  Expected: ~200,000-250,000 voxels for full brain")
    print()
    print("Possible causes:")
    print("  1. Functional data in /output is a subset or test data")
    print("  2. Preprocessing used different settings")
    print("  3. Data was cropped/masked for storage")
    print()
    print("Options:")
    print("  A. Accept different results with current data")
    print("  B. Use more permissive mask (try 'simple' or 'permissive')")
    print("  C. Find original full-coverage data")
else:
    print("✓ Functional data has reasonable brain coverage")
    print("  Results should be reproducible")
