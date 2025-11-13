#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
config_GOOD.py
--------------
Configuration pointing to GOOD preprocessing (output/pilot/sub-01)
This produces 310 voxels for V2 and 52° novel error

Usage on server:
  cp config_GOOD.py config.py
"""

import os
import glob
from pathlib import Path

class Config:
    # Project base path (on server)
    PROJECT_DIR = os.path.abspath(os.path.dirname(__file__))
    DERIVATIVES_DIR = os.path.join(PROJECT_DIR, 'derivatives')

    # Subject info
    SUB_ID = '01'  # Keep as '01' even for pilot

    # fMRI parameters
    TR = 1.5
    N_RUNS = 6
    VOLS_TO_DROP = 4
    N_COLORS = 8

    # ROI settings
    ROI_Z_THRESH = 3.1
    MIN_CLUSTER_SIZE = 50

    # CRITICAL: Point to GOOD preprocessing location
    @property
    def output_dir(self):
        # ✅ GOOD data location (310 voxels, 52° error)
        return os.path.join(self.PROJECT_DIR, 'output', 'pilot', f'sub-{self.SUB_ID}')

    @property
    def fmriprep_dir(self):
        return os.path.join(self.output_dir, 'func')

    @property
    def analysis_dir(self):
        return os.path.join(self.DERIVATIVES_DIR, f'sub-{self.SUB_ID}')

    @property
    def roi_dir(self):
        return os.path.join(self.analysis_dir, 'roi')

    # File path methods
    def get_func_img_path(self, run):
        return os.path.join(
            self.fmriprep_dir,
            f'sub-{self.SUB_ID}_task-rsvp_run-{run}_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz'
        )

    def get_event_file_path(self, run):
        return os.path.join(
            self.PROJECT_DIR,
            f'pilot/sub-{self.SUB_ID}/func/sub-{self.SUB_ID}_task-rsvp_run-{run}_events.tsv'
        )

    def get_confound_file_path(self, run):
        return os.path.join(
            self.fmriprep_dir,
            f'sub-{self.SUB_ID}_task-rsvp_run-{run}_desc-confounds_timeseries.tsv'
        )

    # Cache check method
    def check_derivatives_exist(self):
        """Check if design matrix files exist"""
        pattern = os.path.join(self.DERIVATIVES_DIR, f'sub-{self.SUB_ID}',
                             f'*task-rsvp_run-*_space-*_design_ready_HRF-*.csv')
        return len(glob.glob(pattern)) > 0

# Global config instance
cfg = Config()
