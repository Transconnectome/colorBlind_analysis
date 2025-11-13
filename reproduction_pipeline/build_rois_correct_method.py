#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_rois_correct_method.py
-----------------------------
Build ROI masks using the CORRECT method from build_atlas.py

This uses:
1. maxprob_vol_lh.nii.gz + maxprob_vol_rh.nii.gz (NOT individual prob maps!)
2. 30% probability threshold for fallback (NOT 50%!)
3. Regex matching for ROI extraction

Usage:
    python build_rois_correct_method.py
"""

import sys
import os
from pathlib import Path
import re
import argparse
import numpy as np
import nibabel as nib
from nilearn import image
from nilearn.masking import compute_epi_mask

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from reproduction_pipeline.config_reproduction_output import cfg


def parse_args():
    parser = argparse.ArgumentParser(
        description='Build ROI masks using correct method (maxprob volumes)'
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

    pattern = f"sub-*_task-rsvp_run-*_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz"
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


def resample_and_mask(bin_img, ref_img, epi_mask_img):
    """Resample to functional grid and intersect with EPI mask"""
    rs = image.resample_to_img(
        bin_img, ref_img,
        interpolation='nearest',
        force_resample=True,
        copy_header=True
    )
    return image.math_img("a * (b > 0)", a=rs, b=epi_mask_img)


def main():
    args = parse_args()
    subject_id = args.subject

    print("="*70)
    print("ROI Mask Creation - CORRECT METHOD (maxprob volumes)")
    print("="*70)
    print(f"Subject: sub-{subject_id}")
    print(f"Atlas: Wang et al. (2015) maxprob volumes")
    print(f"Data source: {cfg.OUTPUT_DIR}")
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

    # Load reference and compute EPI mask
    print("\nComputing EPI mask from functional data...")
    ref_img = nib.load(ref_img_path)
    epi_mask_img = compute_epi_mask(ref_img)
    n_epi_voxels = int(np.sum(epi_mask_img.get_fdata() > 0))
    print(f"  EPI mask: {n_epi_voxels:,} voxels")

    # Save EPI mask
    roi_dir = cfg.get_roi_dir(subject_id)
    roi_dir.mkdir(parents=True, exist_ok=True)
    epi_mask_path = roi_dir / f"sub-{subject_id}_epi_mask.nii.gz"
    nib.save(epi_mask_img, epi_mask_path)
    print(f"  ✓ Saved EPI mask: {epi_mask_path}")
    print()

    # ========================================================================
    # METHOD 1: Try maxprob volumes first (ORIGINAL SUCCESSFUL METHOD)
    # ========================================================================

    print("="*70)
    print("METHOD 1: Using maxprob volumes (RECOMMENDED)")
    print("="*70)
    print()

    maxprob_lh = cfg.ATLAS_DIR / "maxprob_vol_lh.nii.gz"
    maxprob_rh = cfg.ATLAS_DIR / "maxprob_vol_rh.nii.gz"

    roi_counts = {}

    if maxprob_lh.exists() and maxprob_rh.exists():
        print(f"Found maxprob volumes:")
        print(f"  LH: {maxprob_lh.name}")
        print(f"  RH: {maxprob_rh.name}")
        print()

        # Load and combine hemispheres
        lh_atlas = nib.load(maxprob_lh)
        rh_atlas = nib.load(maxprob_rh)
        lh_data = lh_atlas.get_fdata()
        rh_data = rh_atlas.get_fdata()

        # Combine (labels are disjoint, so simple sum works)
        combined_data = lh_data + rh_data
        combined_atlas = nib.Nifti1Image(combined_data, lh_atlas.affine, lh_atlas.header)

        print(f"Combined atlas unique labels: {np.unique(combined_data.astype(int))[:20]}...")
        print()

        # Define ROI label patterns (adjust based on actual LUT)
        # Common Wang atlas labels:
        # V1v=1, V1d=2, V2v=3, V2d=4, V3v=5, V3d=6, hV4=7 (approximately)
        roi_label_map = {
            'V1': [1, 2],      # V1v + V1d
            'V2': [3, 4],      # V2v + V2d
            'V3': [5, 6],      # V3v + V3d
            'hV4': [7],        # hV4
        }

        print("Building ROIs from maxprob labels...")
        for roi_name, label_ids in roi_label_map.items():
            print(f"\n  Building {roi_name} (labels: {label_ids})...")

            # Extract voxels matching these labels
            roi_data = np.isin(combined_data, label_ids).astype(np.uint8)
            n_before = int(np.sum(roi_data))

            if n_before == 0:
                print(f"    ⚠ No voxels found with labels {label_ids}")
                continue

            # Create NIfTI
            bin_img = nib.Nifti1Image(roi_data, combined_atlas.affine, combined_atlas.header)

            # Resample and mask
            roi_final = resample_and_mask(bin_img, ref_img, epi_mask_img)
            roi_final_data = roi_final.get_fdata()
            n_after = int(np.sum(roi_final_data > 0))

            print(f"    Before resample+mask: {n_before:,} voxels")
            print(f"    After resample+mask: {n_after:,} voxels")

            if n_after == 0:
                print(f"    ⚠ WARNING: No voxels after masking!")
                continue

            # Save
            output_path = cfg.get_roi_mask_path(roi_name, subject_id)
            nib.save(roi_final, output_path)
            print(f"    ✓ Saved: {output_path}")

            roi_counts[roi_name] = n_after

    else:
        print("⚠ WARNING: maxprob volumes not found!")
        print(f"  Looking for:")
        print(f"    {maxprob_lh}")
        print(f"    {maxprob_rh}")
        print()
        print("Falling back to probability maps method...")
        print()

        # ====================================================================
        # METHOD 2: Fallback to probability maps with 30% threshold
        # ====================================================================

        print("="*70)
        print("METHOD 2: Using probability maps (FALLBACK)")
        print("="*70)
        print()

        # Probability threshold from original build_atlas.py
        PROB_THRESHOLD = 30  # 30% not 50%!

        roi_keywords = {
            'V1':  ['roi1_', 'roi2_'],   # V1v + V1d
            'V2':  ['roi3_', 'roi4_'],   # V2v + V2d
            'V3':  ['roi5_', 'roi6_'],   # V3v + V3d
            'hV4': ['roi7_'],            # hV4
        }

        for roi_name, keywords in roi_keywords.items():
            print(f"\n  Building {roi_name} from probability maps...")

            # Accumulate probability across all parts
            acc = None
            for keyword in keywords:
                for hemi in ['lh', 'rh']:
                    # Try different file patterns
                    patterns = [
                        f"perc_VTPM_vol_{keyword}{hemi}.nii.gz",
                        f"*{keyword}*{hemi}.nii.gz",
                    ]

                    found = False
                    for pattern in patterns:
                        files = list(cfg.ATLAS_DIR.glob(pattern))
                        if files:
                            atlas_file = files[0]
                            found = True
                            break

                    if not found:
                        print(f"    [WARN] Not found: {keyword}{hemi}")
                        continue

                    # Load and accumulate
                    img = nib.load(atlas_file)
                    dat = img.get_fdata()

                    if acc is None:
                        acc = np.zeros_like(dat, dtype=np.float32)
                        atlas_affine = img.affine

                    acc += dat

            if acc is None:
                print(f"    ✗ Failed to build {roi_name}")
                continue

            # Threshold at 30%
            bin_data = (acc > PROB_THRESHOLD).astype(np.uint8)
            n_before = int(np.sum(bin_data))

            print(f"    Probability maps combined: {n_before:,} voxels (>{PROB_THRESHOLD}% threshold)")

            # Create NIfTI and resample
            bin_img = nib.Nifti1Image(bin_data, atlas_affine)
            roi_final = resample_and_mask(bin_img, ref_img, epi_mask_img)

            n_after = int(np.sum(roi_final.get_fdata() > 0))
            print(f"    After resample+mask: {n_after:,} voxels")

            # Save
            output_path = cfg.get_roi_mask_path(roi_name, subject_id)
            nib.save(roi_final, output_path)
            print(f"    ✓ Saved: {output_path}")

            roi_counts[roi_name] = n_after

    # ========================================================================
    # Validation
    # ========================================================================

    print()
    print("="*70)
    print("ROI Validation")
    print("="*70)

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

    print("="*70)
    print()

    if roi_counts:
        print(f"✓ SUCCESS: Created {len(roi_counts)}/{len(roi_keywords)} ROI masks")
        print(f"\nNext step: Run run_reconstruction_reproduction_output.py")
    else:
        print("✗ ERROR: No ROI masks were created")
        sys.exit(1)


if __name__ == '__main__':
    main()
