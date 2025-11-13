#!/usr/bin/env python3
"""
Check voxel count in ROI mask files
Usage: python check_voxel_count.py <mask_file.nii.gz>
       python check_voxel_count.py derivatives/sub-P01/roi/*.nii.gz
"""

import sys
import nibabel as nib
import numpy as np
from pathlib import Path

if len(sys.argv) < 2:
    print("Usage: python check_voxel_count.py <mask_file.nii.gz> [<mask2.nii.gz> ...]")
    print("\nExample:")
    print("  python check_voxel_count.py derivatives/sub-P01/roi/sub-01_V2_mask.nii.gz")
    print("  python check_voxel_count.py derivatives/sub-P01/roi/*.nii.gz")
    sys.exit(1)

print("=" * 70)
print("ROI Mask Voxel Count Check")
print("=" * 70)

for mask_path in sys.argv[1:]:
    try:
        # Load mask
        mask_img = nib.load(mask_path)
        mask_data = mask_img.get_fdata()

        # Count non-zero voxels
        n_voxels = int(np.sum(mask_data > 0))

        # Get shape
        shape = mask_img.shape[:3]

        # Get file info
        file_size = Path(mask_path).stat().st_size / 1024  # KB

        print(f"\n{Path(mask_path).name}")
        print(f"  Shape: {shape}")
        print(f"  Voxels: {n_voxels}")
        print(f"  File size: {file_size:.1f} KB")

    except Exception as e:
        print(f"\n{Path(mask_path).name}")
        print(f"  ERROR: {e}")

print("\n" + "=" * 70)
