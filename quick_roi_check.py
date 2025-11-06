#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
quick_roi_check.py
------------------
Quick visual check of ROI-functional overlap

Usage:
    python quick_roi_check.py
"""

import os
import sys
import numpy as np
import nibabel as nib
import matplotlib.pyplot as plt
import glob
from pathlib import Path

try:
    from nilearn import plotting, image as nimg
except ImportError:
    print("Error: nilearn not available")
    sys.exit(1)

from config import cfg

# ============================================================================
# Quick Check
# ============================================================================

def quick_check():
    """Quick visual and numerical check"""

    print("Quick ROI-Functional Check")
    print("="*60)

    # Find functional data
    func_pattern = os.path.join(
        cfg.fmriprep_dir,
        f"sub-{cfg.SUB_ID}_*_space-MNI152NLin2009cAsym_*_bold.nii.gz"
    )
    func_files = sorted(glob.glob(func_pattern))

    if not func_files:
        print(f"ERROR: No functional files found")
        return

    func_img = nib.load(func_files[0])
    print(f"Functional: {Path(func_files[0]).name}")
    print(f"  Shape: {func_img.shape}")
    print(f"  Affine diagonal: {np.diag(func_img.affine)}")
    print()

    # Find ROI masks
    roi_dir = cfg.roi_dir
    roi_files = sorted(glob.glob(os.path.join(roi_dir, "*V*.nii*")))

    if not roi_files:
        print(f"ERROR: No V1-V4 ROI masks found in {roi_dir}")
        return

    print(f"Found {len(roi_files)} ROI masks:")
    print()

    # Check each ROI
    for roi_file in roi_files:
        roi_name = Path(roi_file).stem.replace(".nii", "")

        # Extract simple ROI name (V1, V2, etc.)
        if "_desc-" in roi_name:
            simple_name = roi_name.split("_desc-")[1].split("_")[0]
        elif "_V" in roi_name:
            parts = roi_name.split("_")
            for part in parts:
                if part in ["V1", "V2", "V3", "hV4"]:
                    simple_name = part
                    break
            else:
                simple_name = roi_name
        else:
            simple_name = roi_name

        roi_img = nib.load(roi_file)
        roi_data = roi_img.get_fdata()
        roi_mask = roi_data > 0

        # Get mean functional
        if len(func_img.shape) == 4:
            mean_func = np.mean(func_img.get_fdata(), axis=3)
        else:
            mean_func = func_img.get_fdata()

        # Check alignment
        affine_match = np.allclose(func_img.affine, roi_img.affine, atol=1e-3)
        shape_match = func_img.shape[:3] == roi_img.shape[:3]

        # Check overlap
        brain_mask = mean_func > 0
        overlap = np.logical_and(roi_mask, brain_mask)
        n_roi = np.sum(roi_mask)
        n_overlap = np.sum(overlap)
        overlap_pct = (n_overlap / n_roi * 100) if n_roi > 0 else 0

        # Check functional values in ROI
        roi_values = mean_func[roi_mask]
        n_nonzero = np.sum(roi_values != 0)
        pct_nonzero = (n_nonzero / n_roi * 100) if n_roi > 0 else 0

        # Status
        if not affine_match or not shape_match:
            status = "❌ MISALIGNED"
        elif overlap_pct < 50:
            status = "❌ POOR OVERLAP"
        elif pct_nonzero < 50:
            status = "❌ MOSTLY ZEROS"
        elif overlap_pct < 80 or pct_nonzero < 80:
            status = "⚠️ SUBOPTIMAL"
        else:
            status = "✅ GOOD"

        print(f"{simple_name}: {status}")
        print(f"  Voxels: {n_roi}")
        print(f"  Alignment: affine={affine_match}, shape={shape_match}")
        print(f"  Overlap: {n_overlap}/{n_roi} ({overlap_pct:.1f}%)")
        print(f"  Non-zero: {n_nonzero}/{n_roi} ({pct_nonzero:.1f}%)")
        print(f"  Value range: [{roi_values.min():.1f}, {roi_values.max():.1f}]")
        print()

    # Create quick visualization
    print("Creating visualization...")
    fig = plt.figure(figsize=(15, 10))

    mean_func_img = nimg.mean_img(func_img) if len(func_img.shape) == 4 else func_img

    for idx, roi_file in enumerate(roi_files[:4]):  # First 4 ROIs
        roi_name = Path(roi_file).stem.replace(".nii", "")
        if "_desc-" in roi_name:
            simple_name = roi_name.split("_desc-")[1].split("_")[0]
        else:
            simple_name = roi_name

        ax = plt.subplot(2, 2, idx+1)
        plotting.plot_roi(
            roi_file,
            bg_img=mean_func_img,
            display_mode='z',
            cut_coords=3,
            axes=ax,
            title=simple_name,
            colorbar=False
        )

    plt.tight_layout()
    plt.savefig("roi_quick_check.png", dpi=150, bbox_inches='tight')
    print("Saved: roi_quick_check.png")
    print()

    print("="*60)
    print("If you see misalignment or poor overlap:")
    print("  1. Run: python diagnose_roi_alignment.py (detailed check)")
    print("  2. Check ROI construction in roi_build.py")
    print("  3. Verify fMRIPrep output space (MNI vs native)")
    print("="*60)


if __name__ == '__main__':
    quick_check()
