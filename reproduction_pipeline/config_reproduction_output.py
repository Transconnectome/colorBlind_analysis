#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
config_reproduction_output.py
-----------------------------
Configuration for reproduction using OLD data structure in /output directory.
This uses the data from before reorganization.

Exact configuration used to achieve documented results:
- V2: 52.4° novel error (BEST)
- V1: 64.1° novel error
- hV4: 75.0° novel error

DO NOT MODIFY unless you want to deviate from documented results!
"""

import os
from pathlib import Path

class ReproductionConfigOutput:
    """
    Configuration for OLD output directory structure.

    This uses data from /scratch/connectome/haba6030/colorBlind/output
    which was the structure before data reorganization.
    """

    # ========================================================================
    # Subject Configuration
    # ========================================================================

    SUB_ID = "01"  # Subject in output directory

    # For file naming: files are named sub-01
    FILE_PRE = "01"  # Prefix used in filenames (sub-01_task-rsvp...)

    # ========================================================================
    # fMRI Parameters (CRITICAL - do not change!)
    # ========================================================================

    TR = 1.5  # Repetition time in seconds
    N_RUNS = 6  # Total number of runs
    N_COLORS = 8  # Number of color stimuli
    VOLS_TO_DROP = 4  # Volumes to discard at start of each run

    # ========================================================================
    # FIR Configuration (Universal HRF Method)
    # ========================================================================

    # FIR delays: 0-9 TRs = 0-13.5 seconds
    # This samples the full HRF time course
    FIR_DELAYS = list(range(10))

    # ========================================================================
    # Color Hue Values (Lab Space - CRITICAL!)
    # ========================================================================

    # These are the EXACT Lab hue values from pilot data
    # DO NOT MODIFY - must match actual stimulus presentation
    LABEL2HUE_DEG_PILOT = {
        'color_1': 182.142053052572436,
        'color_2': 287.979026187069735,
        'color_3': 305.226546308759566,
        'color_4': 330.204721787408289,
        'color_5': 35.269500805260478,
        'color_6': 73.365061454288877,
        'color_7': 125.585145639335096,
        'color_8': 143.909094545652778,
    }

    # ========================================================================
    # Analysis Parameters
    # ========================================================================

    # PCA dimensionality reduction
    USE_PCA = True
    N_PCA_COMPONENTS = 20  # Reduces from ~310 voxels to 20 components

    # Forward model
    N_CHANNELS = 6  # Six idealized color channels (B&H 2009)

    # ROI parameters
    ROI_PROB_THRESHOLD = 30  # Wang atlas probability threshold (%) - CRITICAL: Original used 30%, not 50%!

    # ========================================================================
    # File Paths (OLD OUTPUT STRUCTURE)
    # ========================================================================

    # Project root (on server)
    PROJECT_DIR = Path("/scratch/connectome/haba6030/colorBlind")

    # OLD OUTPUT DIRECTORY (before reorganization)
    OUTPUT_DIR = Path("/scratch/connectome/haba6030/colorBlind/output")

    # Use output directory data (as requested)
    FMRIPREP_BASE = OUTPUT_DIR

    # Alternative: if you want to use storage instead
    # FMRIPREP_BASE = Path("/storage/connectome/haba6030/fmriprep_out")

    # Atlas directory (should be same)
    ATLAS_DIR = PROJECT_DIR / "ProbAtlas_v4/subj_vol_all"

    # Derivatives - use separate directory to not overwrite new structure
    DERIVATIVES_DIR = OUTPUT_DIR / "derivatives_reproduction"

    # ========================================================================
    # Wang Atlas ROI Mapping
    # ========================================================================

    WANG_ROI_MAP = {
        'V1': ['perc_VTPM_vol_roi1_', 'perc_VTPM_vol_roi2_'],  # V1v + V1d
        'V2': ['perc_VTPM_vol_roi3_', 'perc_VTPM_vol_roi4_'],  # V2v + V2d
        'V3': ['perc_VTPM_vol_roi5_', 'perc_VTPM_vol_roi6_'],  # V3v + V3d
        'hV4': ['perc_VTPM_vol_roi7_'],  # hV4
    }

    HEMISPHERES = ['lh', 'rh']

    # ========================================================================
    # Expected Results (for validation)
    # ========================================================================

    # These are the documented results we're trying to reproduce
    EXPECTED_RESULTS = {
        'V2': {
            'n_voxels': 310,
            'optimal_delay_TRs': 5,  # 7.5s
            'classification_accuracy': 1.000,  # 100%
            'training_error_deg': 4.1,
            'novel_error_deg': 52.4,
        },
        'V1': {
            'n_voxels': 511,  # From ALL_ROIS_RESULTS_SUMMARY.md (not 344!)
            'optimal_delay_TRs': 5,  # 7.5s (was 5 TRs, not 4!)
            'classification_accuracy': 1.000,  # 100%
            'training_error_deg': 6.2,
            'novel_error_deg': 64.1,
        },
        'hV4': {
            'n_voxels': 55,
            'optimal_delay_TRs': 5,  # 7.5s (same as V1/V2, from ALL_ROIS_RESULTS)
            'classification_accuracy': 1.000,  # 100%
            'training_error_deg': 5.0,
            'novel_error_deg': 75.0,
        },
    }

    # ========================================================================
    # Helper Methods
    # ========================================================================

    @classmethod
    def get_fmriprep_dir(cls, subject_id=None):
        """Get fMRIPrep directory for subject"""
        sub = subject_id or cls.SUB_ID
        file_pre = cls.FILE_PRE if subject_id is None else subject_id

        # Try multiple possible locations in OUTPUT directory
        possible_paths = [
            cls.OUTPUT_DIR / "pilot" / f"sub-{file_pre}",  # output/pilot/sub-01
            cls.OUTPUT_DIR / "pilot" / f"sub-{sub}",  # output/pilot/sub-01
            cls.OUTPUT_DIR / f"sub-{file_pre}",  # output/sub-01
            cls.OUTPUT_DIR / f"sub-{sub}",
            cls.FMRIPREP_BASE / "pilot" / f"sub-{file_pre}",
            cls.FMRIPREP_BASE / "pilot" / f"sub-{sub}",
            cls.FMRIPREP_BASE / f"sub-{file_pre}",
            cls.FMRIPREP_BASE / f"sub-{sub}",
        ]

        for path in possible_paths:
            if path.exists():
                return path

        # Default to pilot structure
        return cls.OUTPUT_DIR / "pilot" / f"sub-{file_pre}"

    @classmethod
    def get_func_img_path(cls, run, subject_id=None):
        """Get path to preprocessed functional image"""
        sub = subject_id or cls.SUB_ID
        file_pre = cls.FILE_PRE if subject_id is None else subject_id
        func_dir = cls.get_fmriprep_dir(sub) / "func"

        # Try with FILE_PRE first (for pilot compatibility)
        func_path = func_dir / f"sub-{file_pre}_task-rsvp_run-{run}_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz"

        return func_path

    @classmethod
    def get_event_file_path(cls, run, subject_id=None):
        """Get path to event file"""
        sub = subject_id or cls.SUB_ID
        file_pre = cls.FILE_PRE if subject_id is None else subject_id

        # Try multiple possible locations
        possible_paths = [
            # In output directory
            cls.OUTPUT_DIR / f"sub-{sub}/func/sub-{file_pre}_task-rsvp_run-{run}_events.tsv",
            cls.OUTPUT_DIR / f"sub-{file_pre}/func/sub-{file_pre}_task-rsvp_run-{run}_events.tsv",
            # In old event directory structure
            Path("/storage/connectome/haba6030/colorBlind_dataOct") / f"sub-{sub}/func/sub-{file_pre}_task-rsvp_run-{run}_events.tsv",
            # In project pilot directory
            cls.PROJECT_DIR / f"pilot/sub-{sub}/func/sub-{file_pre}_task-rsvp_run-{run}_events.tsv",
        ]

        for path in possible_paths:
            if path.exists():
                return path

        # Default to first option
        return possible_paths[0]

    @classmethod
    def get_confound_file_path(cls, run, subject_id=None):
        """Get path to confounds file"""
        sub = subject_id or cls.SUB_ID
        file_pre = cls.FILE_PRE if subject_id is None else subject_id
        func_dir = cls.get_fmriprep_dir(sub) / "func"
        return func_dir / f"sub-{file_pre}_task-rsvp_run-{run}_desc-confounds_timeseries.tsv"

    @classmethod
    def get_roi_dir(cls, subject_id=None):
        """Get ROI output directory"""
        sub = subject_id or cls.SUB_ID
        return cls.DERIVATIVES_DIR / f"sub-{sub}" / "roi"

    @classmethod
    def get_roi_mask_path(cls, roi_name, subject_id=None):
        """Get path to ROI mask file"""
        sub = subject_id or cls.SUB_ID
        roi_dir = cls.get_roi_dir(sub)
        return roi_dir / f"sub-{sub}_{roi_name}_mask.nii.gz"

    @classmethod
    def get_analysis_output_dir(cls, roi_name, subject_id=None):
        """Get analysis output directory for specific ROI"""
        sub = subject_id or cls.SUB_ID
        return cls.DERIVATIVES_DIR / f"sub-{sub}" / "fir_reconstruction_reproduction" / f"{roi_name}_universal_hrf"

    @classmethod
    def validate_setup(cls):
        """Validate that all required paths exist"""
        errors = []

        # Check fMRIPrep data
        fmriprep_dir = cls.get_fmriprep_dir()
        if not fmriprep_dir.exists():
            errors.append(f"fMRIPrep directory not found: {fmriprep_dir}")

        # Check atlas
        if not cls.ATLAS_DIR.exists():
            errors.append(f"Atlas directory not found: {cls.ATLAS_DIR}")

        # Check event files
        for run in range(1, cls.N_RUNS + 1):
            event_path = cls.get_event_file_path(run)
            if not event_path.exists():
                errors.append(f"Event file not found: {event_path}")

        # Check functional files
        for run in range(1, cls.N_RUNS + 1):
            func_path = cls.get_func_img_path(run)
            if not func_path.exists():
                errors.append(f"Functional file not found: {func_path}")

        return errors


# Create global instance
cfg = ReproductionConfigOutput()


# ========================================================================
# Path Discovery Helper
# ========================================================================

def discover_data_paths(base_dir="/scratch/connectome/haba6030/colorBlind/output"):
    """
    Helper function to discover actual data paths in output directory.
    Run this on the server to find where files actually are.

    Usage on server:
        from config_reproduction_output import discover_data_paths
        discover_data_paths()
    """
    import os

    base_path = Path(base_dir)
    print(f"Searching in: {base_path}")
    print("="*70)

    if not base_path.exists():
        print(f"ERROR: {base_path} does not exist!")
        return

    # Find subject directories
    print("\n1. Subject directories:")
    for item in sorted(base_path.iterdir()):
        if item.is_dir() and item.name.startswith('sub-'):
            print(f"   {item}")

            # Check for func directory
            func_dir = item / "func"
            if func_dir.exists():
                print(f"     → func/")

                # Count BOLD files
                bold_files = list(func_dir.glob("*_bold.nii.gz"))
                print(f"        BOLD files: {len(bold_files)}")
                if bold_files:
                    print(f"        Example: {bold_files[0].name}")

                # Count event files
                event_files = list(func_dir.glob("*_events.tsv"))
                print(f"        Event files: {len(event_files)}")
                if event_files:
                    print(f"        Example: {event_files[0].name}")

    print("\n" + "="*70)
    print("Copy the actual paths above and update config_reproduction_output.py")


# ========================================================================
# Critical Implementation Notes
# ========================================================================

"""
CRITICAL BUG FIXES TO PRESERVE:

1. Optimal Delay Selection:
   WRONG:  optimal_delay = np.argmax(universal_hrf)
   RIGHT:  optimal_delay = np.argmax(np.abs(universal_hrf))

   Impact: V2 novel error 77.8° → 52.4° (35% improvement!)

2. Reconstruction Inverse:
   WRONG:  C_test_est = np.linalg.inv(W.T @ W) @ W.T @ X_test_final.T
   RIGHT:  C_test_est = np.linalg.pinv(W.T @ W) @ W.T @ X_test_final.T

   Reason: W.T @ W may not be full rank with 7 training colors

3. Lab Hue Values:
   MUST use exact values from LABEL2HUE_DEG_PILOT
   DO NOT round or approximate!

4. PCA Components:
   20 components is optimal (tested: 10, 20, 30, 50)

5. ROI Probability Threshold:
   CRITICAL: Original build_atlas.py used 30% threshold, NOT 50%!
   WRONG:  ROI_PROB_THRESHOLD = 50  # Gives V1: 354, V2: 306
   RIGHT:  ROI_PROB_THRESHOLD = 30  # Gives V1: 511, V2: 310

   Discovered: 2025-11-09 - Explains voxel count discrepancy!
"""
