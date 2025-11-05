#!/usr/bin/env python
"""
Quick check: Shows current ROI configuration and available ROI masks
Run this before starting analysis to verify setup.
"""

import os
import sys
import glob
from pathlib import Path

print("=" * 80)
print("ROI SETUP CHECKER")
print("=" * 80)
print()

# Read ROI_SELECTION from naive_analysis.py
print("Reading naive_analysis.py configuration...")
try:
    with open('naive_analysis.py', 'r') as f:
        lines = f.readlines()

    roi_selection = None
    for i, line in enumerate(lines):
        if line.strip().startswith('ROI_SELECTION = '):
            roi_selection = line.strip()
            line_num = i + 1
            break

    if roi_selection:
        print(f"✅ Found ROI_SELECTION at line {line_num}:")
        print(f"   {roi_selection}")
        print()
    else:
        print("❌ Could not find ROI_SELECTION in naive_analysis.py")
        sys.exit(1)

except FileNotFoundError:
    print("❌ naive_analysis.py not found in current directory")
    print(f"   Current directory: {os.getcwd()}")
    sys.exit(1)

# Extract the actual value
import re
match = re.search(r'ROI_SELECTION\s*=\s*\[(.*?)\]', roi_selection)
if match:
    roi_list_str = match.group(1)
    current_rois = [r.strip().strip('"').strip("'") for r in roi_list_str.split(',') if r.strip()]
    print(f"Current ROI selection: {current_rois}")
else:
    print("⚠️  Could not parse ROI_SELECTION value")
    current_rois = []

print()
print("-" * 80)
print()

# Check what ROI masks are available
print("Checking available ROI masks...")
print()

SUB = "sub-01"
SPACE = "MNI152NLin2009cAsym"

# Search locations
search_dirs = [
    f"derivatives/{SUB}/roi",
    "analysis/roi",
    f"output/pilot/{SUB}/roi",
]

# Brain mask
brain_mask = f"output/pilot/{SUB}/anat/{SUB}_acq-mprage_space-{SPACE}_res-2_desc-brain_mask.nii.gz"

available_masks = {}

if os.path.exists(brain_mask):
    available_masks["brain"] = brain_mask
    print(f"✅ brain: {brain_mask}")
else:
    print(f"❌ brain: {brain_mask} (NOT FOUND)")

print()

# Search for ROI masks
found_any = False
for search_dir in search_dirs:
    if not os.path.isdir(search_dir):
        continue

    print(f"Searching in: {search_dir}")
    masks = sorted(glob.glob(os.path.join(search_dir, "*.nii*")))

    if masks:
        found_any = True
        for mask_path in masks:
            filename = Path(mask_path).name

            # Extract ROI name (same logic as naive_analysis.py)
            roi_name = None
            if "_desc-" in filename:
                roi_name = filename.split("_desc-")[1].split("_")[0]
            elif "_mask" in filename:
                # Extract from pattern like "sub-01_V2_mask.nii.gz"
                base = filename.replace("_fixed_mask", "_mask").split("_mask")[0]
                parts = base.split("_")
                # Look for common ROI names
                for part in reversed(parts):
                    if part in ["V1", "V2", "V3", "V4", "hV4", "EarlyVisual", "Ventral", "BrainMask"]:
                        roi_name = part
                        break

            if not roi_name:
                roi_name = Path(mask_path).stem.replace('.nii', '')

            available_masks[roi_name] = mask_path
            print(f"  ✅ {roi_name}: {mask_path}")
    else:
        print(f"  (no masks found)")

    print()

if not found_any and "brain" not in available_masks:
    print("❌ No ROI masks found!")
    print()
    print("To create Wang atlas ROI masks:")
    print("  1. Check if roi_build.py exists: ls -l roi_build.py")
    print("  2. Run it: python roi_build.py")
    print("  3. This should create V1, V2, V3, hV4 in derivatives/sub-01/roi/")
    print()

print("-" * 80)
print()

# Validate current selection
print("Validating current ROI selection...")
print()

all_valid = True
for roi in current_rois:
    if roi in available_masks:
        print(f"✅ '{roi}' - FOUND at {available_masks[roi]}")
    else:
        print(f"❌ '{roi}' - NOT FOUND!")
        all_valid = False

print()

if all_valid and current_rois:
    print("=" * 80)
    print("✅ CONFIGURATION VALID!")
    print("=" * 80)
    print()
    print(f"You are ready to run analysis with: {current_rois}")
    print()
    print("Next steps:")
    print(f"  1. Upload: scp naive_analysis.py node2:/scratch/connectome/haba6030/colorBlind/")
    print(f"  2. Delete cache: rm -f hrf_test_outputs/cache_{current_rois[0]}/*")
    print(f"  3. Run: sbatch sbatch_naive.sub")
    print()
elif current_rois:
    print("=" * 80)
    print("❌ CONFIGURATION ERROR!")
    print("=" * 80)
    print()
    print(f"Selected ROIs not found: {[r for r in current_rois if r not in available_masks]}")
    print()
    print("Available ROIs:")
    for roi_name in available_masks.keys():
        print(f"  - {roi_name}")
    print()
    print("Fix by editing naive_analysis.py line 87:")
    print(f"  ROI_SELECTION = [\"{list(available_masks.keys())[0]}\"]")
    print()
else:
    print("=" * 80)
    print("⚠️  NO ROIs SELECTED!")
    print("=" * 80)
    print()
    print("Edit naive_analysis.py line 87 to select an ROI")
    print()

# Summary table
print("=" * 80)
print("AVAILABLE ROI SUMMARY")
print("=" * 80)
print()
print(f"{'ROI Name':<15} {'Status':<10} {'Path'}")
print("-" * 80)

recommended_roi = None
for roi_name, roi_path in sorted(available_masks.items()):
    is_selected = roi_name in current_rois
    status = "✅ SELECTED" if is_selected else "Available"

    # Mark V2 as recommended
    if roi_name == "V2":
        status += " ⭐"
        recommended_roi = roi_name

    print(f"{roi_name:<15} {status:<10} {roi_path}")

print()

if recommended_roi and recommended_roi not in current_rois:
    print("💡 TIP: V2 has the best overlap (58%) - consider testing it first!")
    print(f"   Change line 87 to: ROI_SELECTION = [\"{recommended_roi}\"]")
    print()

print("=" * 80)
