#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_data_paths.py
-------------------
Verify all required data files exist before running reconstruction
"""

import os
from config import cfg

print("="*70)
print("Data Path Verification")
print("="*70)
print()

# Check directories
print("=== Directory Paths ===")
print(f"fMRIPrep output: {cfg.output_dir}")
print(f"Functional data: {cfg.fmriprep_dir}")
print(f"Analysis output: {cfg.analysis_dir}")
print(f"ROI directory:   {cfg.roi_dir}")
print()

# Check if directories exist
print("=== Directory Existence ===")
dirs_to_check = [
    ("fMRIPrep output", cfg.output_dir),
    ("Functional data", cfg.fmriprep_dir),
    ("ROI directory", cfg.roi_dir),
]

all_dirs_exist = True
for name, path in dirs_to_check:
    exists = os.path.isdir(path)
    status = "✅" if exists else "❌"
    print(f"{status} {name}: {path}")
    if not exists:
        all_dirs_exist = False

print()

# Check BOLD files
print("=== BOLD Files (preprocessed functional data) ===")
bold_files = []
for run in range(1, cfg.N_RUNS + 1):
    path = cfg.get_func_img_path(run)
    exists = os.path.exists(path)
    status = "✅" if exists else "❌"
    print(f"{status} Run {run}: {os.path.basename(path)}")
    if exists:
        bold_files.append(path)
        # Show file size
        size_mb = os.path.getsize(path) / (1024 * 1024)
        print(f"      Size: {size_mb:.1f} MB")

print(f"\nFound {len(bold_files)}/{cfg.N_RUNS} BOLD files")
print()

# Check confounds files
print("=== Confounds Files (motion parameters) ===")
confound_files = []
for run in range(1, cfg.N_RUNS + 1):
    path = cfg.get_confound_file_path(run)
    exists = os.path.exists(path)
    status = "✅" if exists else "❌"
    print(f"{status} Run {run}: {os.path.basename(path)}")
    if exists:
        confound_files.append(path)

print(f"\nFound {len(confound_files)}/{cfg.N_RUNS} confounds files")
print()

# Check event files
print("=== Event Files (stimulus timing) ===")
event_files = []
for run in range(1, cfg.N_RUNS + 1):
    path = cfg.get_event_file_path(run)
    exists = os.path.exists(path)
    status = "✅" if exists else "❌"
    print(f"{status} Run {run}: {os.path.basename(path)}")
    if exists:
        event_files.append(path)

print(f"\nFound {len(event_files)}/{cfg.N_RUNS} event files")
print()

# Check ROI masks
print("=== ROI Masks ===")
roi_masks = []
if os.path.isdir(cfg.roi_dir):
    for roi_file in sorted(os.listdir(cfg.roi_dir)):
        if roi_file.endswith('_mask.nii.gz'):
            roi_name = roi_file.split('_')[1]  # Extract ROI name
            print(f"✅ {roi_name}: {roi_file}")
            roi_masks.append(roi_name)

    if len(roi_masks) == 0:
        print("❌ No ROI masks found")
else:
    print(f"❌ ROI directory does not exist: {cfg.roi_dir}")

print(f"\nFound {len(roi_masks)} ROI masks")
if roi_masks:
    print(f"Available ROIs: {', '.join(roi_masks)}")
print()

# Summary
print("="*70)
print("SUMMARY")
print("="*70)

ready = (len(bold_files) == cfg.N_RUNS and
         len(confound_files) == cfg.N_RUNS and
         len(event_files) == cfg.N_RUNS and
         len(roi_masks) > 0)

if ready:
    print("✅ All required files found!")
    print()
    print("Ready to run reconstruction:")
    print("  sbatch --export=ROI=V2,USE_PCA=1,N_COMPONENTS=20 run_fir_reconstruction_single.sbatch")
    print()
    print(f"Available ROIs: {', '.join(roi_masks)}")
else:
    print("❌ Missing required files:")
    print()

    if len(bold_files) < cfg.N_RUNS:
        print(f"  - BOLD files: {len(bold_files)}/{cfg.N_RUNS}")
        print(f"    Location: {cfg.fmriprep_dir}")
        print(f"    Check: ls {cfg.fmriprep_dir}/*bold.nii.gz")

    if len(confound_files) < cfg.N_RUNS:
        print(f"  - Confounds files: {len(confound_files)}/{cfg.N_RUNS}")
        print(f"    Location: {cfg.fmriprep_dir}")
        print(f"    Check: ls {cfg.fmriprep_dir}/*confounds*.tsv")

    if len(event_files) < cfg.N_RUNS:
        print(f"  - Event files: {len(event_files)}/{cfg.N_RUNS}")
        event_dir = os.path.dirname(cfg.get_event_file_path(1))
        print(f"    Location: {event_dir}")
        print(f"    Check: ls {event_dir}/*events.tsv")

    if len(roi_masks) == 0:
        print(f"  - ROI masks: 0")
        print(f"    Location: {cfg.roi_dir}")
        print(f"    Run roi_build.py first to create ROI masks")

print("="*70)
