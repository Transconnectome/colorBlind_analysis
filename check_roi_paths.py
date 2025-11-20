#!/usr/bin/env python3
"""
Quick script to check ROI mask paths and find actual file locations
"""

import os
import glob
from pathlib import Path

SUBJECTS = ['01', '02', '03', '04']
ROIS = ['V1', 'V2', 'V3', 'hV4']

print("="*80)
print("ROI Mask Path Checker")
print("="*80)
print()

for subject in SUBJECTS:
    print(f"Subject: {subject}")
    print("-" * 40)

    # Expected path (from code)
    expected_path = f"derivatives/sub-{subject}/roi_pipeline/{ROIS[0]}_mask_thr50_intnearest_binTrue_masknone_gmTrue_subjFalse.nii.gz"
    print(f"  Expected pattern: derivatives/sub-{subject}/roi_pipeline/ROI_mask_*.nii.gz")

    # Check if derivatives dir exists
    deriv_dir = f"derivatives/sub-{subject}"
    if not os.path.exists(deriv_dir):
        print(f"  ❌ Directory not found: {deriv_dir}")
        print()
        continue

    print(f"  ✅ Directory exists: {deriv_dir}")

    # Search for ROI mask files
    search_patterns = [
        f"derivatives/sub-{subject}/roi_pipeline/*.nii.gz",
        f"derivatives/sub-{subject}/roi_pipeline_*/*.nii.gz",
        f"derivatives/sub-{subject}/**/roi_pipeline*/*.nii.gz",
        f"derivatives/sub-{subject}/**/*mask*.nii.gz",
    ]

    found_files = set()
    for pattern in search_patterns:
        files = glob.glob(pattern, recursive=True)
        found_files.update(files)

    if not found_files:
        print(f"  ❌ No ROI mask files found!")
    else:
        print(f"  ✅ Found {len(found_files)} mask files:")
        for f in sorted(found_files):
            # Check if it's one of our ROIs
            is_target_roi = any(roi in f for roi in ROIS)
            marker = "  🎯" if is_target_roi else "    "
            print(f"{marker} {f}")

    print()

print("="*80)
print("Legend:")
print("  🎯 = Target ROI (V1, V2, V3, or hV4)")
print("  ✅ = Found")
print("  ❌ = Not found")
print("="*80)
