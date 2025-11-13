#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_and_fix_rois.py
-------------------------
Validate ROI masks and fix overlap issues by removing zero-signal voxels.

This is a CRITICAL step that was part of the successful analysis!

Strategy:
1. Create functional mask from BOLD data (voxels with non-zero signal)
2. Intersect ROI masks with functional mask
3. Remove voxels with zero/no signal
4. Validate alignment and coverage

Usage:
    python validate_and_fix_rois.py
    python validate_and_fix_rois.py --subject 02
"""

import sys
import os
from pathlib import Path
import argparse
import numpy as np
import pandas as pd
import nibabel as nib
from nilearn import image

# Add parent directory for config import
sys.path.insert(0, str(Path(__file__).parent.parent))
from reproduction_pipeline.config_reproduction import cfg


def parse_args():
    parser = argparse.ArgumentParser(
        description='Validate and fix ROI masks'
    )
    parser.add_argument(
        '--subject',
        type=str,
        default=cfg.SUB_ID,
        help=f'Subject ID (default: {cfg.SUB_ID})'
    )
    return parser.parse_args()


def create_functional_mask(func_img_path, threshold=0):
    """
    Create binary mask of voxels with functional signal.

    This identifies voxels that actually have BOLD signal,
    removing zero-valued voxels outside the brain or
    in areas with no coverage.
    """
    print(f"\n  Creating functional mask from:")
    print(f"  {Path(func_img_path).name}")

    # Load functional image
    func_img = nib.load(func_img_path)
    func_data = func_img.get_fdata()

    # Compute mean across time
    mean_func = func_data.mean(axis=-1)

    # Create binary mask (voxels with signal > threshold)
    func_mask = mean_func > threshold

    # Count active voxels
    n_active = int(np.sum(func_mask))
    n_total = int(np.prod(func_mask.shape))

    print(f"  Active voxels: {n_active:,} / {n_total:,} ({100*n_active/n_total:.1f}%)")

    # Create NIfTI image
    mask_img = nib.Nifti1Image(
        func_mask.astype(np.uint8),
        affine=func_img.affine,
        header=func_img.header
    )

    return mask_img


def validate_roi_alignment(roi_path, func_img_path):
    """
    Validate ROI-functional alignment and coverage.

    Checks:
    1. Shape match
    2. Affine match
    3. Overlap with functional signal
    """
    roi_name = Path(roi_path).stem.replace('_mask', '')
    print(f"\n{'='*70}")
    print(f"Validating: {roi_name}")
    print(f"{'='*70}")

    # Load functional
    func_img = nib.load(func_img_path)
    func_data = func_img.get_fdata()
    func_mean = func_data.mean(axis=-1)
    func_active = func_mean > 0

    print(f"\n  Functional:")
    print(f"    Shape: {func_img.shape[:3]}")
    print(f"    Active voxels: {int(np.sum(func_active)):,}")

    # Load ROI
    roi_img = nib.load(roi_path)
    roi_data = roi_img.get_fdata().astype(bool)

    print(f"\n  ROI:")
    print(f"    Shape: {roi_img.shape}")
    print(f"    Total voxels: {int(np.sum(roi_data)):,}")

    # Check shape match
    if func_img.shape[:3] != roi_img.shape:
        print(f"\n  ❌ ERROR: Shape mismatch!")
        print(f"     Functional: {func_img.shape[:3]}")
        print(f"     ROI: {roi_img.shape}")
        return False
    else:
        print(f"\n  ✅ Shapes match")

    # Check affine match
    affine_diff = np.abs(func_img.affine - roi_img.affine).max()
    if not np.allclose(func_img.affine, roi_img.affine, atol=1e-4):
        print(f"\n  ⚠ WARNING: Affines don't match exactly")
        print(f"    Max difference: {affine_diff:.6f}")
    else:
        print(f"  ✅ Affines match")

    # Check overlap
    overlap = int(np.sum(roi_data & func_active))
    roi_size = int(np.sum(roi_data))
    overlap_pct = 100 * overlap / roi_size if roi_size > 0 else 0

    print(f"\n  Overlap with functional signal:")
    print(f"    Overlapping voxels: {overlap:,} / {roi_size:,} ({overlap_pct:.1f}%)")

    if overlap_pct < 50:
        print(f"    ❌ ERROR: Less than 50% overlap!")
        return False
    elif overlap_pct < 80:
        print(f"    ⚠ WARNING: Less than 80% overlap")
        print(f"    This ROI will be fixed to remove zero-signal voxels")
        return True
    else:
        print(f"    ✅ Good overlap (≥80%)")
        return True


def fix_roi_mask(roi_path, func_mask_img, output_path):
    """
    Fix ROI by intersecting with functional mask.

    **CRITICAL STEP**: Removes voxels with zero functional signal.

    This was part of the successful analysis that achieved:
    - V2: 52.4° novel error
    - V1: 64.1° novel error
    - hV4: 75.0° novel error
    """
    roi_name = Path(roi_path).stem.replace('_mask', '')

    print(f"\n  Processing: {roi_name}")

    # Load ROI
    roi_img = nib.load(roi_path)
    roi_data = roi_img.get_fdata().astype(bool)

    # Load functional mask
    func_mask_data = func_mask_img.get_fdata().astype(bool)

    # Check alignment
    if roi_data.shape != func_mask_data.shape:
        print(f"    ⚠ Shape mismatch, resampling ROI...")
        roi_img = image.resample_to_img(
            roi_img,
            func_mask_img,
            interpolation='nearest'
        )
        roi_data = roi_img.get_fdata().astype(bool)

    # Compute intersection *** THIS IS THE KEY STEP ***
    fixed_roi_data = roi_data & func_mask_data

    # Statistics
    n_original = int(np.sum(roi_data))
    n_active = int(np.sum(fixed_roi_data))
    n_removed = n_original - n_active
    overlap_pct = 100 * n_active / n_original if n_original > 0 else 0

    stats = {
        'roi_name': roi_name,
        'original_voxels': n_original,
        'active_voxels': n_active,
        'removed_voxels': n_removed,
        'overlap_pct': overlap_pct
    }

    print(f"    Original voxels: {n_original:,}")
    print(f"    Active voxels: {n_active:,} ({overlap_pct:.1f}%)")
    print(f"    Removed (zero signal): {n_removed:,}")

    if n_active == 0:
        print(f"    ❌ ERROR: No active voxels remaining!")
        raise ValueError(f"ROI {roi_name} has no active voxels")
    elif n_active < 50:
        print(f"    ⚠ WARNING: Very few voxels ({n_active})")
    else:
        print(f"    ✅ OK")

    # Create fixed ROI image
    fixed_roi_img = nib.Nifti1Image(
        fixed_roi_data.astype(np.uint8),
        affine=func_mask_img.affine,
        header=func_mask_img.header
    )

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    nib.save(fixed_roi_img, output_path)
    print(f"    Saved: {output_path}")

    return fixed_roi_img, stats


def main():
    args = parse_args()
    subject_id = args.subject

    print("="*70)
    print("ROI Validation and Fixing Pipeline")
    print("="*70)
    print(f"Subject: sub-{subject_id}")
    print()

    # ========================================================================
    # Step 1: Create Functional Mask
    # ========================================================================

    print("[Step 1/3] Creating functional mask")
    print("-" * 70)

    # Use first run
    func_img_path = cfg.get_func_img_path(1, subject_id)
    if not func_img_path.exists():
        print(f"ERROR: Functional image not found: {func_img_path}")
        sys.exit(1)

    func_mask_img = create_functional_mask(func_img_path)

    # Save functional mask
    roi_dir = cfg.get_roi_dir(subject_id)
    func_mask_path = roi_dir / f"sub-{subject_id}_functional_mask.nii.gz"
    nib.save(func_mask_img, func_mask_path)
    print(f"\n  ✓ Saved functional mask: {func_mask_path}")

    # ========================================================================
    # Step 2: Validate ROI Alignment
    # ========================================================================

    print(f"\n[Step 2/3] Validating ROI alignment")
    print("-" * 70)

    validation_passed = True
    for roi_name in cfg.WANG_ROI_MAP.keys():
        roi_path = cfg.get_roi_mask_path(roi_name, subject_id)

        if not roi_path.exists():
            print(f"\n⚠ ROI not found, skipping: {roi_name}")
            continue

        is_valid = validate_roi_alignment(roi_path, func_img_path)
        validation_passed = validation_passed and is_valid

    # ========================================================================
    # Step 3: Fix ROI Masks
    # ========================================================================

    print(f"\n[Step 3/3] Fixing ROI masks")
    print("-" * 70)
    print("\nRemoving zero-signal voxels from ROI masks...")

    all_stats = []

    for roi_name in cfg.WANG_ROI_MAP.keys():
        roi_path = cfg.get_roi_mask_path(roi_name, subject_id)

        if not roi_path.exists():
            print(f"\n⚠ ROI not found, skipping: {roi_name}")
            continue

        # Output path with '_fixed' suffix
        output_path = roi_path.parent / roi_path.name.replace('_mask.nii.gz', '_fixed_mask.nii.gz')

        try:
            fixed_img, stats = fix_roi_mask(roi_path, func_mask_img, output_path)
            all_stats.append(stats)
        except Exception as e:
            print(f"\n✗ Failed to fix {roi_name}: {e}")
            import traceback
            traceback.print_exc()

    # ========================================================================
    # Summary
    # ========================================================================

    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")

    if all_stats:
        print(f"\n{'ROI':<10} {'Original':<12} {'Active':<12} {'Removed':<12} {'Overlap %':<12}")
        print("-" * 70)

        for stats in all_stats:
            print(f"{stats['roi_name']:<10} "
                  f"{stats['original_voxels']:<12,} "
                  f"{stats['active_voxels']:<12,} "
                  f"{stats['removed_voxels']:<12,} "
                  f"{stats['overlap_pct']:<12.1f}")

        print()
        print("✓ Fixed ROI masks saved with '_fixed_mask.nii.gz' suffix")
        print()
        print("IMPORTANT NOTES:")
        print("  - Fixed masks have zero-signal voxels removed")
        print("  - This improves classification and reconstruction quality")
        print("  - Use the fixed masks for analysis!")
        print()
        print("Next step:")
        print("  python run_reconstruction_reproduction.py --roi V2 --use-fixed-rois")
        print()
    else:
        print("✗ No ROI masks were processed")

    print("="*70)


if __name__ == '__main__':
    main()
