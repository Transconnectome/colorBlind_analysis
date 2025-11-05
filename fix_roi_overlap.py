#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_roi_overlap.py
------------------
Fix ROI overlap problem by creating intersection-masked ROIs

Strategy: Keep only ROI voxels that have non-zero functional signal

This solves the problem where Wang atlas ROIs include voxels
outside the functional coverage area.
"""

import os
import numpy as np
import nibabel as nib
from nilearn import image
from config import cfg


def create_functional_mask(func_img_path, threshold=0):
    """
    Create binary mask of voxels with functional signal

    Parameters
    ----------
    func_img_path : str
        Path to functional image
    threshold : float
        Minimum mean signal value (default: 0, i.e., non-zero)

    Returns
    -------
    mask_img : Nifti1Image
        Binary mask image
    """
    print(f"\nCreating functional mask from:")
    print(f"  {os.path.basename(func_img_path)}")

    # Load functional image
    func_img = nib.load(func_img_path)
    func_data = func_img.get_fdata()

    # Compute mean across time
    mean_func = func_data.mean(axis=-1)

    # Create binary mask
    func_mask = mean_func > threshold

    # Count active voxels
    n_active = np.sum(func_mask)
    n_total = np.prod(func_mask.shape)

    print(f"  Active voxels: {n_active} / {n_total} ({100*n_active/n_total:.1f}%)")

    # Create NIfTI image
    mask_img = nib.Nifti1Image(
        func_mask.astype(np.uint8),
        affine=func_img.affine,
        header=func_img.header
    )

    return mask_img


def fix_roi_mask(roi_path, func_mask_img, output_path=None):
    """
    Fix ROI by intersecting with functional mask

    Parameters
    ----------
    roi_path : str
        Path to ROI mask
    func_mask_img : Nifti1Image
        Functional mask image
    output_path : str, optional
        Path to save fixed ROI (default: adds '_fixed' suffix)

    Returns
    -------
    fixed_roi_img : Nifti1Image
        Fixed ROI image
    stats : dict
        Statistics about the fix
    """
    roi_name = os.path.basename(roi_path).replace('_mask.nii.gz', '')
    print(f"\nProcessing ROI: {roi_name}")

    # Load ROI
    roi_img = nib.load(roi_path)
    roi_data = roi_img.get_fdata().astype(bool)

    # Load functional mask
    func_mask_data = func_mask_img.get_fdata().astype(bool)

    # Check alignment
    if roi_data.shape != func_mask_data.shape:
        print(f"  ⚠️  Shape mismatch, resampling ROI...")
        roi_img = image.resample_to_img(
            roi_img,
            func_mask_img,
            interpolation='nearest'
        )
        roi_data = roi_img.get_fdata().astype(bool)

    # Compute intersection
    fixed_roi_data = roi_data & func_mask_data

    # Statistics
    n_original = np.sum(roi_data)
    n_active = np.sum(fixed_roi_data)
    n_removed = n_original - n_active

    stats = {
        'original_voxels': int(n_original),
        'active_voxels': int(n_active),
        'removed_voxels': int(n_removed),
        'overlap_pct': 100 * n_active / n_original if n_original > 0 else 0
    }

    print(f"  Original voxels: {n_original}")
    print(f"  Active voxels: {n_active} ({stats['overlap_pct']:.1f}%)")
    print(f"  Removed (inactive): {n_removed}")

    if n_active == 0:
        print(f"  ❌ ERROR: No active voxels remaining!")
    elif n_active < 100:
        print(f"  ⚠️  WARNING: Very few voxels ({n_active})")
    else:
        print(f"  ✅ OK")

    # Create fixed ROI image
    fixed_roi_img = nib.Nifti1Image(
        fixed_roi_data.astype(np.uint8),
        affine=func_mask_img.affine,
        header=func_mask_img.header
    )

    # Save if output path specified
    if output_path is None:
        output_path = roi_path.replace('_mask.nii.gz', '_fixed_mask.nii.gz')

    nib.save(fixed_roi_img, output_path)
    print(f"  Saved: {output_path}")

    return fixed_roi_img, stats


def create_combined_rois(func_mask_img, output_dir):
    """
    Create combined ROIs for more robust analysis

    Creates:
    - EarlyVisual: V1 + V2
    - Ventral: V3 + hV4
    """
    print(f"\n{'='*60}")
    print("Creating Combined ROIs")
    print(f"{'='*60}")

    func_mask = func_mask_img.get_fdata().astype(bool)

    # Early Visual (V1 + V2)
    v1_path = os.path.join(cfg.roi_dir, f'sub-{cfg.SUB_ID}_V1_mask.nii.gz')
    v2_path = os.path.join(cfg.roi_dir, f'sub-{cfg.SUB_ID}_V2_mask.nii.gz')

    if os.path.exists(v1_path) and os.path.exists(v2_path):
        v1_data = nib.load(v1_path).get_fdata().astype(bool)
        v2_data = nib.load(v2_path).get_fdata().astype(bool)

        early_visual = (v1_data | v2_data) & func_mask
        n_voxels = np.sum(early_visual)

        print(f"\nEarly Visual (V1 + V2):")
        print(f"  Total voxels: {n_voxels}")

        early_img = nib.Nifti1Image(
            early_visual.astype(np.uint8),
            affine=func_mask_img.affine,
            header=func_mask_img.header
        )

        out_path = os.path.join(output_dir, f'sub-{cfg.SUB_ID}_EarlyVisual_fixed_mask.nii.gz')
        nib.save(early_img, out_path)
        print(f"  Saved: {out_path}")

    # Ventral (V3 + hV4)
    v3_path = os.path.join(cfg.roi_dir, f'sub-{cfg.SUB_ID}_V3_mask.nii.gz')
    v4_path = os.path.join(cfg.roi_dir, f'sub-{cfg.SUB_ID}_hV4_mask.nii.gz')

    if os.path.exists(v3_path) and os.path.exists(v4_path):
        v3_data = nib.load(v3_path).get_fdata().astype(bool)
        v4_data = nib.load(v4_path).get_fdata().astype(bool)

        ventral = (v3_data | v4_data) & func_mask
        n_voxels = np.sum(ventral)

        print(f"\nVentral (V3 + hV4):")
        print(f"  Total voxels: {n_voxels}")

        ventral_img = nib.Nifti1Image(
            ventral.astype(np.uint8),
            affine=func_mask_img.affine,
            header=func_mask_img.header
        )

        out_path = os.path.join(output_dir, f'sub-{cfg.SUB_ID}_Ventral_fixed_mask.nii.gz')
        nib.save(ventral_img, out_path)
        print(f"  Saved: {out_path}")


def main():
    """Fix all ROI masks"""
    print("="*60)
    print("FIX ROI OVERLAP PROBLEM")
    print("="*60)
    print(f"Subject: sub-{cfg.SUB_ID}")

    # Create functional mask from first run
    func_img_path = cfg.get_func_img_path(run=1)
    func_mask_img = create_functional_mask(func_img_path)

    # Save functional mask
    func_mask_path = os.path.join(
        cfg.roi_dir,
        f'sub-{cfg.SUB_ID}_functional_mask.nii.gz'
    )
    nib.save(func_mask_img, func_mask_path)
    print(f"\nSaved functional mask: {func_mask_path}")

    # Fix each ROI
    print(f"\n{'='*60}")
    print("Fixing Individual ROIs")
    print(f"{'='*60}")

    roi_names = ['V1', 'V2', 'V3', 'hV4', 'BrainMask']
    all_stats = {}

    for roi_name in roi_names:
        roi_path = os.path.join(
            cfg.roi_dir,
            f'sub-{cfg.SUB_ID}_{roi_name}_mask.nii.gz'
        )

        if os.path.exists(roi_path):
            fixed_img, stats = fix_roi_mask(roi_path, func_mask_img)
            all_stats[roi_name] = stats
        else:
            print(f"\n⚠️  ROI not found: {roi_name}")

    # Create combined ROIs
    create_combined_rois(func_mask_img, cfg.roi_dir)

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")

    print(f"\n{'ROI':<15} {'Original':<12} {'Active':<12} {'Removed':<12} {'Overlap %':<12}")
    print("-" * 60)

    for roi_name, stats in all_stats.items():
        print(f"{roi_name:<15} {stats['original_voxels']:<12} "
              f"{stats['active_voxels']:<12} {stats['removed_voxels']:<12} "
              f"{stats['overlap_pct']:<12.1f}")

    print(f"\n{'='*60}")
    print("NEXT STEPS")
    print(f"{'='*60}")
    print("\n1. Re-run diagnostic analysis:")
    print("   python diagnostic_analysis.py")
    print("\n2. Check if classification accuracy improves")
    print("\n3. If accuracy > 25%, ROI was the main problem!")
    print(f"\n{'='*60}")


if __name__ == '__main__':
    main()
