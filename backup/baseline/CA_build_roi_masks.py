#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_roi_masks.py
------------------
Build ROI masks for a specific subject using Wang atlas
Handles both pilot (sub-01) and test (sub-02-04) data structures

Usage:
    python build_roi_masks.py --subject 01
"""

import argparse
import sys
import os
import glob
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

import nibabel as nib
import numpy as np
from nilearn import image


# Wang atlas ROI mapping
WANG_ROI_MAP = {
    'V1': ['perc_VTPM_vol_roi1_', 'perc_VTPM_vol_roi2_'],
    'V2': ['perc_VTPM_vol_roi3_', 'perc_VTPM_vol_roi4_'],
    'V3': ['perc_VTPM_vol_roi5_', 'perc_VTPM_vol_roi6_'],
    'hV4': ['perc_VTPM_vol_roi7_'],
}

HEMISPHERES = ('lh', 'rh')


def parse_args():
    parser = argparse.ArgumentParser(description='Build ROI masks for a subject')
    parser.add_argument('--subject', type=str, required=True,
                        help='Subject ID (e.g., 01, 02, 03, 04)')
    return parser.parse_args()


def find_reference_image(subject_id, fmriprep_base):
    """Find a reference functional image for resampling"""

    # Try fMRIPrep output structure
    func_dir = f"{fmriprep_base}/sub-{subject_id}/func"

    if os.path.exists(func_dir):
        # Look for any preprocessed bold file
        pattern = f"{func_dir}/sub-{subject_id}_task-*_run-*_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz"
        candidates = glob.glob(pattern)

        if candidates:
            print(f"  ✓ Found reference image: {os.path.basename(candidates[0])}")
            return candidates[0]

    # If not found, raise error
    raise FileNotFoundError(
        f"No reference functional image found for sub-{subject_id}\n"
        f"  Searched in: {func_dir}\n"
        f"  Pattern: sub-{subject_id}_task-*_run-*_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz"
    )


def find_brain_mask(subject_id, fmriprep_base):
    """Find brain mask for intersection (optional)"""

    # Try fMRIPrep output structure
    anat_dir = f"{fmriprep_base}/sub-{subject_id}/anat"

    if os.path.exists(anat_dir):
        # Look for brain mask
        pattern = f"{anat_dir}/sub-{subject_id}_*_space-MNI152NLin2009cAsym_res-2_desc-brain_mask.nii.gz"
        candidates = glob.glob(pattern)

        if candidates:
            print(f"  ✓ Found brain mask: {os.path.basename(candidates[0])}")
            return candidates[0]

    print(f"  ⚠ No brain mask found (will skip intersection)")
    return None


def build_roi_mask(roi_name, roi_parts, project_dir, ref_img, brain_mask_path, output_path):
    """Build a single ROI mask from Wang atlas"""

    atlas_dir = os.path.join(project_dir, 'ProbAtlas_v4/subj_vol_all')

    roi_mask = None
    part_img = None

    # Combine all parts and hemispheres
    for hemi in HEMISPHERES:
        for part in roi_parts:
            roi_file = os.path.join(atlas_dir, f'{part}{hemi}.nii.gz')

            if not os.path.exists(roi_file):
                print(f"    [WARN] Atlas file not found: {os.path.basename(roi_file)}")
                continue

            part_img = nib.load(roi_file)
            part_data = part_img.get_fdata()
            part_mask = part_data > 50  # Threshold at 50%

            if roi_mask is None:
                roi_mask = part_mask
            else:
                roi_mask = np.logical_or(roi_mask, part_mask)

    if roi_mask is None:
        raise ValueError(f"Could not create mask for {roi_name} - no atlas files found")

    # Convert to NIfTI
    roi_nii = nib.Nifti1Image(roi_mask.astype(np.int16), part_img.affine)

    # Resample to functional space
    roi_resampled = image.resample_img(
        roi_nii,
        target_affine=ref_img.affine,
        target_shape=ref_img.shape[:3],
        interpolation='nearest'
    )

    # Apply brain mask intersection if available
    if brain_mask_path and os.path.exists(brain_mask_path):
        try:
            brain_img = nib.load(brain_mask_path)
            brain_resampled = image.resample_img(
                brain_img,
                target_affine=roi_resampled.affine,
                target_shape=roi_resampled.shape[:3],
                interpolation='nearest'
            )

            roi_bool = roi_resampled.get_fdata().astype(bool)
            brain_bool = brain_resampled.get_fdata().astype(bool)
            combined = np.logical_and(roi_bool, brain_bool).astype(np.int16)

            roi_resampled = nib.Nifti1Image(combined, roi_resampled.affine, roi_resampled.header)
            print(f"    ✓ Applied brain mask intersection")
        except Exception as e:
            print(f"    ⚠ Could not apply brain mask: {e}")

    # Save
    roi_resampled.to_filename(output_path)

    # Count voxels
    n_voxels = int(np.sum(roi_resampled.get_fdata() > 0))

    return n_voxels


def main():
    args = parse_args()
    subject_id = args.subject

    # Project directory (current directory)
    project_dir = os.path.abspath(os.path.dirname(__file__))

    # fMRIPrep base directory
    fmriprep_base = "/storage/connectome/haba6030/fmriprep_out"

    print("=" * 60)
    print(f"Building ROI masks for sub-{subject_id}")
    print("=" * 60)
    print()

    # Check if fMRIPrep data exists
    fmriprep_dir = f"{fmriprep_base}/sub-{subject_id}"
    if not os.path.exists(fmriprep_dir):
        print(f"ERROR: fMRIPrep data not found at {fmriprep_dir}")
        sys.exit(1)

    # Check if atlas exists
    atlas_dir = os.path.join(project_dir, "ProbAtlas_v4/subj_vol_all")
    if not os.path.exists(atlas_dir):
        print(f"ERROR: Wang atlas not found at {atlas_dir}")
        sys.exit(1)

    print(f"fMRIPrep data: {fmriprep_dir}")
    print(f"Atlas directory: {atlas_dir}")
    print()

    # Find reference image and brain mask
    print("Finding reference images...")
    try:
        ref_img_path = find_reference_image(subject_id, fmriprep_base)
        ref_img = nib.load(ref_img_path)
        print(f"  Reference shape: {ref_img.shape[:3]}")
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    brain_mask_path = find_brain_mask(subject_id, fmriprep_base)
    print()

    # Create output directory
    output_dir = os.path.join(project_dir, f"derivatives/sub-{subject_id}/roi")
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output directory: {output_dir}")
    print()

    # Build each ROI
    created_rois = {}

    for roi_name, roi_parts in WANG_ROI_MAP.items():
        output_path = os.path.join(output_dir, f"sub-{subject_id}_{roi_name}_mask.nii.gz")

        print(f"Building {roi_name}...")

        try:
            n_voxels = build_roi_mask(
                roi_name, roi_parts, project_dir,
                ref_img, brain_mask_path, output_path
            )

            print(f"  ✓ Created {roi_name}: {n_voxels} voxels")
            print(f"    Saved to: {output_path}")
            created_rois[roi_name] = output_path

        except Exception as e:
            print(f"  ✗ Failed to create {roi_name}: {e}")

        print()

    # Summary
    print("=" * 60)
    if created_rois:
        print(f"SUCCESS: Created {len(created_rois)}/{len(WANG_ROI_MAP)} ROI masks")
        print("=" * 60)
        for roi_name, roi_path in created_rois.items():
            print(f"  ✓ {roi_name}: {roi_path}")
        print()
        sys.exit(0)
    else:
        print("ERROR: No ROI masks were created")
        print("=" * 60)
        print()
        sys.exit(1)


if __name__ == '__main__':
    main()
