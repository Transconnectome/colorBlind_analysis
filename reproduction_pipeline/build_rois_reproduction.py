#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_rois_reproduction.py
--------------------------
Build ROI masks for reproducing documented results.

This script creates ROI masks from the Wang et al. (2015) atlas
exactly as they were created in the successful analysis session.

Expected voxel counts (for validation):
- V1: 344 voxels
- V2: 310 voxels
- V3: 89 voxels
- hV4: 55 voxels

Usage:
    python build_rois_reproduction.py
    python build_rois_reproduction.py --subject 02  # For other subjects
"""

import sys
import os
from pathlib import Path
import argparse
import numpy as np
import nibabel as nib
from nilearn import image
from nilearn.masking import compute_epi_mask

# Add parent directory to path for config import
sys.path.insert(0, str(Path(__file__).parent.parent))
from reproduction_pipeline.config_reproduction import cfg


def parse_args():
    parser = argparse.ArgumentParser(
        description='Build ROI masks for reproduction pipeline'
    )
    parser.add_argument(
        '--subject',
        type=str,
        default=cfg.SUB_ID,
        help=f'Subject ID (default: {cfg.SUB_ID})'
    )
    return parser.parse_args()


def find_reference_image(subject_id):
    """Find reference functional image for resampling"""
    func_dir = cfg.get_fmriprep_dir(subject_id) / "func"

    if not func_dir.exists():
        raise FileNotFoundError(f"Functional directory not found: {func_dir}")

    # Look for any preprocessed bold file with res-2
    pattern = f"sub-{subject_id}_task-rsvp_run-*_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz"
    candidates = list(func_dir.glob(pattern))

    if not candidates:
        raise FileNotFoundError(
            f"No reference functional image found in {func_dir}\n"
            f"  Expected pattern: {pattern}"
        )

    ref_path = candidates[0]
    print(f"  ✓ Found reference image: {ref_path.name}")
    print(f"    Resolution: {nib.load(ref_path).shape[:3]}")

    return ref_path


def build_roi_mask(roi_name, roi_parts, ref_img_path, epi_mask_img, output_path):
    """
    Build a single ROI mask from Wang atlas.

    Exactly replicates the procedure from successful analysis:
    1. Combine atlas parts (V1v+V1d, etc.)
    2. Threshold at 50% probability
    3. Resample to functional MNI space
    4. Intersect with EPI mask (CRITICAL!)
    """

    print(f"\n  Building {roi_name}...")

    # Load reference image
    ref_img = nib.load(ref_img_path)

    # Initialize combined mask
    combined_mask = None
    atlas_affine = None

    # Combine all parts and hemispheres
    for hemi in cfg.HEMISPHERES:
        for part in roi_parts:
            atlas_file = cfg.ATLAS_DIR / f"{part}{hemi}.nii.gz"

            if not atlas_file.exists():
                print(f"    [WARN] Atlas file not found: {atlas_file.name}")
                continue

            # Load atlas
            atlas_img = nib.load(atlas_file)
            atlas_data = atlas_img.get_fdata()

            # Threshold at 50% probability
            part_mask = atlas_data > cfg.ROI_PROB_THRESHOLD

            if combined_mask is None:
                combined_mask = part_mask
                atlas_affine = atlas_img.affine
            else:
                combined_mask = np.logical_or(combined_mask, part_mask)

    if combined_mask is None:
        raise ValueError(f"Could not create mask for {roi_name} - no atlas files found")

    # Convert to NIfTI
    mask_img = nib.Nifti1Image(combined_mask.astype(np.int16), atlas_affine)

    # Resample to functional space (res-2: 97×115×97)
    mask_resampled = image.resample_img(
        mask_img,
        target_affine=ref_img.affine,
        target_shape=ref_img.shape[:3],
        interpolation='nearest'
    )

    # *** CRITICAL STEP: Intersect with EPI mask ***
    # This removes voxels outside functional brain coverage
    roi_data = mask_resampled.get_fdata().astype(bool)
    epi_data = epi_mask_img.get_fdata().astype(bool)
    roi_masked = roi_data & epi_data

    # Count voxels before and after EPI mask
    n_before = int(np.sum(roi_data))
    n_after = int(np.sum(roi_masked))
    n_removed = n_before - n_after

    print(f"    Before EPI mask: {n_before:,} voxels")
    print(f"    After EPI mask: {n_after:,} voxels")
    if n_removed > 0:
        print(f"    Removed: {n_removed:,} voxels outside brain ({100*n_removed/n_before:.1f}%)")

    # Create final masked ROI
    roi_final = nib.Nifti1Image(
        roi_masked.astype(np.uint8),
        affine=ref_img.affine,
        header=ref_img.header
    )

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    nib.save(roi_final, output_path)

    print(f"    ✓ Saved to: {output_path}")

    return n_after


def validate_roi_counts(roi_counts):
    """
    Validate ROI voxel counts against expected values.

    Small deviations (<5%) are acceptable due to resampling differences.
    """

    print("\n" + "="*70)
    print("ROI Validation")
    print("="*70)

    all_ok = True

    for roi_name, actual_count in roi_counts.items():
        if roi_name not in cfg.EXPECTED_RESULTS:
            print(f"{roi_name}: {actual_count} voxels (no expected value)")
            continue

        expected_count = cfg.EXPECTED_RESULTS[roi_name]['n_voxels']
        diff = actual_count - expected_count
        pct_diff = (diff / expected_count) * 100

        status = "✓ OK" if abs(pct_diff) < 5 else "⚠ WARNING"

        print(f"{roi_name}:")
        print(f"  Expected: {expected_count} voxels")
        print(f"  Actual:   {actual_count} voxels")
        print(f"  Difference: {diff:+d} voxels ({pct_diff:+.1f}%)")
        print(f"  Status: {status}")

        if abs(pct_diff) >= 5:
            all_ok = False
            print(f"  [!] Large deviation detected. Results may differ from documented values.")

    print("="*70)

    return all_ok


def main():
    args = parse_args()
    subject_id = args.subject

    print("="*70)
    print("ROI Mask Creation for Reproduction Pipeline")
    print("="*70)
    print(f"Subject: sub-{subject_id}")
    print(f"Atlas: Wang et al. (2015)")
    print(f"Threshold: {cfg.ROI_PROB_THRESHOLD}%")
    print()

    # Validate setup
    print("Validating setup...")
    errors = cfg.validate_setup()
    if errors:
        print("\nERROR: Setup validation failed:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    print("  ✓ All required paths exist")

    # Find reference image
    print("\nFinding reference functional image...")
    try:
        ref_img_path = find_reference_image(subject_id)
    except FileNotFoundError as e:
        print(f"\nERROR: {e}")
        sys.exit(1)

    # Compute EPI mask from reference functional image
    print("\nComputing EPI mask from functional data...")
    ref_img = nib.load(ref_img_path)
    epi_mask_img = compute_epi_mask(ref_img)
    n_epi_voxels = int(np.sum(epi_mask_img.get_fdata() > 0))
    print(f"  EPI mask: {n_epi_voxels:,} voxels")
    print(f"  This defines the functional brain coverage")

    # Save EPI mask for reference
    roi_dir = cfg.get_roi_dir(subject_id)
    roi_dir.mkdir(parents=True, exist_ok=True)
    epi_mask_path = roi_dir / f"sub-{subject_id}_epi_mask.nii.gz"
    nib.save(epi_mask_img, epi_mask_path)
    print(f"  ✓ Saved EPI mask: {epi_mask_path}")

    print(f"\nOutput directory: {roi_dir}")

    # Build each ROI
    print("\nBuilding ROI masks...")
    roi_counts = {}

    for roi_name, roi_parts in cfg.WANG_ROI_MAP.items():
        output_path = cfg.get_roi_mask_path(roi_name, subject_id)

        try:
            n_voxels = build_roi_mask(
                roi_name,
                roi_parts,
                ref_img_path,
                epi_mask_img,  # ← Pass EPI mask
                output_path
            )
            roi_counts[roi_name] = n_voxels

        except Exception as e:
            print(f"    ✗ Failed to create {roi_name}: {e}")
            import traceback
            traceback.print_exc()

    # Validate results
    if roi_counts:
        validate_roi_counts(roi_counts)

        print(f"\n✓ SUCCESS: Created {len(roi_counts)}/{len(cfg.WANG_ROI_MAP)} ROI masks")
        print(f"\nROI masks are ready for analysis.")
        print(f"Next step: Run run_reconstruction_reproduction.py")

        sys.exit(0)
    else:
        print("\n✗ ERROR: No ROI masks were created")
        sys.exit(1)


if __name__ == '__main__':
    main()
