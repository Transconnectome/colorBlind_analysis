#!/usr/bin/env python3
"""
simple_build_rois.py
--------------------
Simple script to build ROI masks without dependencies
"""

from roi_build import build_wang_rois
from config import cfg

print("="*60)
print("Building ROI Masks")
print("="*60)
print(f"Subject: sub-{cfg.SUB_ID}")
print(f"Output dir: {cfg.output_dir}")
print(f"ROI dir: {cfg.roi_dir}")
print("")

# Build ROI masks
created = build_wang_rois(cfg, skip_existing=True)

print("")
print("="*60)
print("ROI masks created!")
print("="*60)

# Check voxel counts
import nibabel as nib
import glob
import os

masks = sorted(glob.glob(os.path.join(cfg.roi_dir, "*.nii.gz")))
if masks:
    print("\nVoxel counts:")
    for m in masks:
        img = nib.load(m)
        n_vox = int((img.get_fdata() > 0).sum())
        print(f"  {os.path.basename(m)}: {n_vox} voxels")
else:
    print("\nNo masks found!")
