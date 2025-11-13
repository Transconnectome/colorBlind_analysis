#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
config_reproduction.py
----------------------
Exact configuration used to achieve documented results:
- V2: 52.4° novel error (BEST)
- V1: 64.1° novel error
- hV4: 75.0° novel error

This configuration reproduces the "Quick Fix" method that achieved
these results through:
1. Universal HRF estimation across all voxels
2. Optimal delay selection using ABSOLUTE VALUE (critical bug fix!)
3. Beta extraction at single optimal delay
4. Diagonal LDA classification
5. B&H 2009 forward model reconstruction

DO NOT MODIFY unless you want to deviate from documented results!
"""

import os
from pathlib import Path

class ReproductionConfig:
    """
    Exact configuration from successful analysis session.

    This configuration is frozen to reproduce documented results.
    Any changes will likely result in different performance.
    """

    # ========================================================================
    # Subject Configuration
    # ========================================================================

    SUB_ID = "01"  # Test subject (NOT pilot P01)

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
    ROI_PROB_THRESHOLD = 50  # Wang atlas probability threshold (%)

    # ========================================================================
    # File Paths (Server Paths)
    # ========================================================================

    # Project root (on server)
    PROJECT_DIR = Path("/scratch/connectome/haba6030/colorBlind")

    # fMRIPrep output (storage location)
    FMRIPREP_BASE = Path("/storage/connectome/haba6030/fmriprep_out")

    # Atlas directory
    ATLAS_DIR = PROJECT_DIR / "ProbAtlas_v4/subj_vol_all"

    # Derivatives
    DERIVATIVES_DIR = PROJECT_DIR / "derivatives"

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
            'n_voxels': 344,
            'optimal_delay_TRs': 4,  # 6.0s
            'classification_accuracy': 1.000,  # 100%
            'training_error_deg': 6.2,
            'novel_error_deg': 64.1,
        },
        'hV4': {
            'n_voxels': 55,
            'optimal_delay_TRs': 6,  # 9.0s
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
        return cls.FMRIPREP_BASE / f"sub-{sub}"

    @classmethod
    def get_func_img_path(cls, run, subject_id=None):
        """Get path to preprocessed functional image"""
        sub = subject_id or cls.SUB_ID
        func_dir = cls.get_fmriprep_dir(sub) / "func"
        return func_dir / f"sub-{sub}_task-rsvp_run-{run}_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz"

    @classmethod
    def get_event_file_path(cls, run, subject_id=None):
        """Get path to event file"""
        sub = subject_id or cls.SUB_ID
        # Event files are in BIDS structure under project directory
        return cls.PROJECT_DIR / f"pilot/sub-{sub}/func/sub-{sub}_task-rsvp_run-{run}_events.tsv"

    @classmethod
    def get_confound_file_path(cls, run, subject_id=None):
        """Get path to confounds file"""
        sub = subject_id or cls.SUB_ID
        func_dir = cls.get_fmriprep_dir(sub) / "func"
        return func_dir / f"sub-{sub}_task-rsvp_run-{run}_desc-confounds_timeseries.tsv"

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

        return errors


# Create global instance
cfg = ReproductionConfig()


# ========================================================================
# Critical Implementation Notes
# ========================================================================

"""
CRITICAL BUG FIXES TO PRESERVE:

1. Optimal Delay Selection (Lines 265-266 in original):
   WRONG:  optimal_delay = np.argmax(universal_hrf)
   RIGHT:  optimal_delay = np.argmax(np.abs(universal_hrf))

   Rationale: HRF can be all negative. Using absolute value finds
   the peak magnitude regardless of sign. This bug fix improved
   V2 novel error from 77.8° → 52.4° (35% improvement!)

2. Reconstruction Inverse (Lines 752, 908 in original):
   WRONG:  C_test_est = np.linalg.inv(W.T @ W) @ W.T @ X_test_final.T
   RIGHT:  C_test_est = np.linalg.pinv(W.T @ W) @ W.T @ X_test_final.T

   Rationale: With 7 training colors and 6 basis functions,
   W.T @ W may not be full rank. Pseudoinverse handles this.

3. Cross-Validation Structure:
   - Training colors: Leave-one-run-out (train on 5 runs, test on 1)
   - Novel colors: Leave-one-color-out (train on 7 colors, test on 1)

   These are DIFFERENT validation schemes testing different things:
   - Leave-one-run-out: Generalization across time
   - Leave-one-color-out: Generalization in color space

4. Color Hue Values:
   MUST use exact values from LABEL2HUE_DEG_PILOT.
   These match the actual stimulus Lab coordinates.
   DO NOT round or approximate!

5. PCA Components:
   20 components was optimal. More components = overfitting risk.
   Fewer components = information loss.

6. FIR Delays:
   range(10) = 0-13.5s captures full HRF time course.
   DO NOT reduce unless you want to miss late responses.
"""
