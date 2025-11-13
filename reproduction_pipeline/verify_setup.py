#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_setup.py
---------------
Verify that all required data and paths exist before running reproduction pipeline.

Usage:
    python verify_setup.py
"""

import sys
from pathlib import Path

# Add parent directory for config import
sys.path.insert(0, str(Path(__file__).parent.parent))
from reproduction_pipeline.config_reproduction import cfg


def check_file(path, description):
    """Check if a file exists"""
    if path.exists():
        print(f"  ✓ {description}")
        return True
    else:
        print(f"  ✗ {description}")
        print(f"    Missing: {path}")
        return False


def check_directory(path, description):
    """Check if a directory exists"""
    if path.exists() and path.is_dir():
        print(f"  ✓ {description}")
        return True
    else:
        print(f"  ✗ {description}")
        print(f"    Missing: {path}")
        return False


def main():
    print("="*70)
    print("Reproduction Pipeline Setup Verification")
    print("="*70)
    print()

    all_ok = True

    # Check project directory
    print("1. Project Structure")
    all_ok &= check_directory(cfg.PROJECT_DIR, "Project directory")
    all_ok &= check_directory(cfg.ATLAS_DIR, "Wang atlas directory")
    print()

    # Check fMRIPrep data
    print("2. fMRIPrep Data (sub-01)")
    fmriprep_dir = cfg.get_fmriprep_dir()
    all_ok &= check_directory(fmriprep_dir, "fMRIPrep directory")

    if fmriprep_dir.exists():
        func_dir = fmriprep_dir / "func"
        all_ok &= check_directory(func_dir, "Functional data directory")

        # Check at least one functional file exists
        func_pattern = f"sub-{cfg.SUB_ID}_task-rsvp_run-*_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz"
        func_files = list(func_dir.glob(func_pattern))
        if func_files:
            print(f"  ✓ Found {len(func_files)} functional runs")
        else:
            print(f"  ✗ No functional files found")
            print(f"    Pattern: {func_pattern}")
            all_ok = False
    print()

    # Check event files
    print("3. Event Files")
    event_files_ok = True
    for run in range(1, cfg.N_RUNS + 1):
        event_path = cfg.get_event_file_path(run)
        if not event_path.exists():
            print(f"  ✗ Run {run}: {event_path}")
            event_files_ok = False
            all_ok = False

    if event_files_ok:
        print(f"  ✓ All {cfg.N_RUNS} event files found")
    print()

    # Check confounds files
    print("4. Confounds Files")
    confounds_ok = True
    for run in range(1, cfg.N_RUNS + 1):
        confound_path = cfg.get_confound_file_path(run)
        if not confound_path.exists():
            print(f"  ✗ Run {run}: {confound_path}")
            confounds_ok = False
            all_ok = False

    if confounds_ok:
        print(f"  ✓ All {cfg.N_RUNS} confounds files found")
    print()

    # Check atlas files
    print("5. Wang Atlas Files")
    atlas_files_ok = True
    for roi_name, roi_parts in cfg.WANG_ROI_MAP.items():
        for hemi in cfg.HEMISPHERES:
            for part in roi_parts:
                atlas_file = cfg.ATLAS_DIR / f"{part}{hemi}.nii.gz"
                if not atlas_file.exists():
                    print(f"  ✗ {roi_name} {hemi}: {atlas_file.name}")
                    atlas_files_ok = False
                    all_ok = False

    if atlas_files_ok:
        total_parts = sum(len(parts) * len(cfg.HEMISPHERES) for parts in cfg.WANG_ROI_MAP.values())
        print(f"  ✓ All {total_parts} atlas files found")
    print()

    # Check Python dependencies
    print("6. Python Dependencies")
    try:
        import numpy
        print(f"  ✓ numpy {numpy.__version__}")
    except ImportError:
        print(f"  ✗ numpy not installed")
        all_ok = False

    try:
        import pandas
        print(f"  ✓ pandas {pandas.__version__}")
    except ImportError:
        print(f"  ✗ pandas not installed")
        all_ok = False

    try:
        import nibabel
        print(f"  ✓ nibabel {nibabel.__version__}")
    except ImportError:
        print(f"  ✗ nibabel not installed")
        all_ok = False

    try:
        import nilearn
        print(f"  ✓ nilearn {nilearn.__version__}")
    except ImportError:
        print(f"  ✗ nilearn not installed")
        all_ok = False

    try:
        import sklearn
        print(f"  ✓ scikit-learn {sklearn.__version__}")
    except ImportError:
        print(f"  ✗ scikit-learn not installed")
        all_ok = False

    try:
        import scipy
        print(f"  ✓ scipy {scipy.__version__}")
    except ImportError:
        print(f"  ✗ scipy not installed")
        all_ok = False

    try:
        import matplotlib
        print(f"  ✓ matplotlib {matplotlib.__version__}")
    except ImportError:
        print(f"  ✗ matplotlib not installed")
        all_ok = False

    print()

    # Summary
    print("="*70)
    if all_ok:
        print("✓✓✓ ALL CHECKS PASSED")
        print()
        print("You are ready to run the reproduction pipeline!")
        print()
        print("Next steps:")
        print("  1. Build ROI masks:")
        print("     python build_rois_reproduction.py")
        print()
        print("  2. Run reconstruction:")
        print("     python run_reconstruction_reproduction.py --roi V2")
        print()
        print("  Or run everything with SLURM:")
        print("     sbatch run_reproduction.sbatch")
        print("="*70)
        sys.exit(0)
    else:
        print("✗✗✗ SOME CHECKS FAILED")
        print()
        print("Please fix the issues above before running the pipeline.")
        print()
        print("Common fixes:")
        print("  - Check that you're on the correct server (node2)")
        print("  - Verify fMRIPrep data location")
        print("  - Ensure conda environment is activated (conda activate nilearn)")
        print("  - Check that atlas directory exists")
        print("="*70)
        sys.exit(1)


if __name__ == '__main__':
    main()
