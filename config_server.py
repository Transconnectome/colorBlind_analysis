#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
config_server.py
----------------
Server-specific configuration for node2
Use this on the server by renaming to config.py or importing as config
"""

import os
import glob
from pathlib import Path

class Config:
    # Project paths on server
    PROJECT_DIR = '/scratch/connectome/haba6030/colorBlind'
    DERIVATIVES_DIR = os.path.join(PROJECT_DIR, 'derivatives')

    # Subject info
    SUB_ID = '01'

    # fMRI parameters
    TR = 1.5  # TR (seconds)
    N_RUNS = 6  # Total number of runs
    VOLS_TO_DROP = 4  # Volumes to discard at start
    N_COLORS = 8  # Number of color conditions

    # ROI settings
    ROI_Z_THRESH = 3.1
    MIN_CLUSTER_SIZE = 50

    # Derived paths
    @property
    def output_dir(self):
        return os.path.join(self.PROJECT_DIR, f'output/pilot/sub-{self.SUB_ID}')

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

    # Check if derivatives exist
    def check_derivatives_exist(self):
        """Check if design matrix files exist"""
        pattern = os.path.join(self.DERIVATIVES_DIR, f'sub-{self.SUB_ID}',
                             f'*task-rsvp_run-*_space-*_design_ready_HRF-*.csv')
        return len(glob.glob(pattern)) > 0

# Global config instance
cfg = Config()
