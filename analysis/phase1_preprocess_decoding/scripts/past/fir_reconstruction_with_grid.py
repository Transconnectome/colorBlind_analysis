#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fir_reconstruction_BH2009_system_clean.py
----------------------------------
Systematic preprocessing review - 144 configurations

KEY DIFFERENCES FROM PREVIOUS IMPLEMENTATIONS:
1. Uses 8 FIR delays (not 10) - matching B&H's 12s window at 1.5s TR
2. Voxel-wise FIR HRF estimation via pseudo-inverse (not optimal delay selection)
3. R² threshold: top 50% voxels only (SNR-based voxel selection)
4. 2nd-level GLM with HRF + derivative regressors (16 columns total)
5. Per-run, per-voxel amplitude estimation (full pipeline)

PIPELINE:
Step 1: Voxel-wise FIR deconvolution
  - Build FIR design matrix (8 delays, color-ignored)
  - h_v = pinv(X_fir) @ y_voxel for each voxel

Step 2: R² calculation and voxel selection (Voxels whose FIR model fits best)
  - r2[v] = 1 - SS_residual / SS_total
  - Select top 50% voxels by r²

Step 3: ROI average HRF
  - ROI_HRF = mean(h_v for v in selected_voxels)
  - ROI_HRF_deriv = numerical_derivative(ROI_HRF)

Step 4: 2nd-level GLM (amplitude estimation)
  - Design: [color_1⊗h, ..., color_8⊗h, color_1⊗h', ..., color_8⊗h']
  - β = pinv(X) @ y per voxel per run
  - Extract first 8 betas as color amplitudes

Step 5: Z-score normalization
  - Z-score per voxel per run (across 8 colors)

Step 6: Classification and reconstruction
  - Leave-one-run-out cross-validation
  - 6-channel forward encoding model

Usage:
    python fir_reconstruction_BH2009_system_clean.py --roi V1 --subject P01

Created: 2025-01-20
Based on: Brouwer & Heeger (2009, J. Neurosci.)
"""

import sys
import os
import glob
import argparse
import numpy as np
import pandas as pd
import nibabel as nib
from pathlib import Path

# Get absolute paths for robust file access
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))  # colorBlind directory
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from nilearn import image as nimg

try:
    from nilearn.maskers import NiftiMasker
except ImportError:
    from nilearn.input_data import NiftiMasker

from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from scipy import stats
from scipy.stats import zscore
from scipy.ndimage import convolve1d

# Import actual stimulus colors from utils module
sys.path.insert(0, str(Path(__file__).parent.parent / 'utils'))
from utils_color_decoding import COLOR_LAB, get_stimulus_color_rgb, lab2rgb_accurate

# Import grid resampling utilities (for --grid-resample option)
sys.path.insert(0, str(Path(__file__).parent / 'utils'))
from grid_resampling import resample_runs_to_common_grid, resample_mask_to_grid
from voxel_tracking import extract_voxel_coordinates

# ============================================================================
# Configuration
# ============================================================================

# Color mappings
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

LABEL2HUE_DEG_TEST = {
    'color_1': 0.0,
    'color_2': 45.0,
    'color_3': 90.0,
    'color_4': 135.0,
    'color_5': 180.0,
    'color_6': 225.0,
    'color_7': 270.0,
    'color_8': 315.0,
}

# Note: COLOR_LAB, lab2rgb_accurate, and get_stimulus_color_rgb are now imported from utils_color_decoding.py

# Experiment parameters
TR = 1.5
N_RUNS = 6
N_COLORS = 8
VOLS_TO_DROP = 4
FIR_DELAYS = np.arange(8)  # 0-7: matching B&H 2009 (12s window at 1.5s TR)

# ============================================================================
# Helper Functions
# ============================================================================

def diag_linear_predict(train_X, train_y, test_X):
    """Diagonal Linear Discriminant Analysis (B&H 2009 method)"""
    classes = np.unique(train_y)
    means = np.stack([train_X[train_y==c].mean(axis=0) for c in classes])
    vars_  = np.stack([train_X[train_y==c].var(axis=0) + 1e-8 for c in classes])

    ll = []
    for k in range(len(classes)):
        ll_k = -0.5 * (
            np.log(2*np.pi*vars_[k]).sum() +
            ((test_X - means[k])**2 / vars_[k]).sum(axis=1)
        )
        ll.append(ll_k)
    ll = np.stack(ll, axis=1)
    preds = classes[ll.argmax(axis=1)]
    return preds

def circular_diff_deg(a, b):
    """Circular difference in degrees"""
    diff = np.abs(a - b)
    diff = np.where(diff > 180, 360 - diff, diff)
    return diff

def circular_mean_deg(angles_deg):
    """Calculate circular mean of angles in degrees and resultant vector length"""
    if len(angles_deg) == 0:
        return np.nan, 0.0
    ang = np.deg2rad(np.asarray(angles_deg))
    C = np.cos(ang).mean()
    S = np.sin(ang).mean()
    mean_ang = (np.rad2deg(np.arctan2(S, C)) + 360) % 360
    R = np.hypot(C, S)  # 0~1, higher = more concentrated
    return mean_ang, R

# Note: lab2rgb_accurate() and get_stimulus_color_rgb() are now imported from utils_color_decoding.py

# ============================================================================
# Preprocessing Functions (for systematic review)
# ============================================================================

def load_motion_confounds(confounds_path, motion_type='none', compcor_n=None):
    """
    Load motion and/or CompCor confounds from fMRIPrep TSV

    Parameters
    ----------
    confounds_path : str
        Path to fMRIPrep confounds TSV file
    motion_type : str
        'none', 'cosine', 'standard', or 'extended'
        - 'cosine': Drift regressors only (Baseline32)
        - 'standard': Motion (6 DOF) + tissue (WM, CSF) + drift (Method3 recommended)
    compcor_n : int or None
        Number of aCompCor components

    Returns
    -------
    confounds : ndarray or None
        Confound regressors (n_scans, n_params)
    n_conf : int
        Number of confounds
    """
    if motion_type == 'none' and compcor_n is None:
        return None, 0

    confounds_df = pd.read_csv(confounds_path, sep='\t')
    all_confound_cols = []

    # Add motion parameters
    if motion_type == 'cosine':
        # Cosine basis for high-pass filtering (Baseline32)
        cosine_cols = [col for col in confounds_df.columns if col.startswith('cosine')]
        all_confound_cols.extend(cosine_cols)
    elif motion_type == 'standard':
        # Standard confound regression for Method3 pipeline
        # Motion (6 DOF) + tissue signals + cosine drift
        motion_cols = ['trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z']
        tissue_cols = ['white_matter', 'csf']
        cosine_cols = [col for col in confounds_df.columns if col.startswith('cosine')]
        all_confound_cols.extend(motion_cols + tissue_cols + cosine_cols)
    elif motion_type == 'extended':
        # Friston 24 parameters
        motion_cols = ['trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z']
        derivative_cols = [f'{col}_derivative1' for col in motion_cols]
        squared_cols = [f'{col}_power2' for col in motion_cols]
        derivative_squared_cols = [f'{col}_derivative1_power2' for col in motion_cols]
        all_confound_cols.extend(motion_cols + derivative_cols + squared_cols + derivative_squared_cols)

    # Add aCompCor
    if compcor_n is not None and compcor_n > 0:
        compcor_cols = [f'a_comp_cor_{i:02d}' for i in range(compcor_n)]
        all_confound_cols.extend(compcor_cols)

    # Check which columns exist
    available_cols = [col for col in all_confound_cols if col in confounds_df.columns]

    if len(available_cols) == 0:
        return None, 0

    confounds = confounds_df[available_cols].values

    # Handle NaN values
    if np.any(np.isnan(confounds)):
        confounds = np.nan_to_num(confounds, nan=0.0)

    return confounds, confounds.shape[1]

def regress_confounds(data, confounds):
    """
    Regress out confounds using OLS

    Parameters
    ----------
    data : ndarray, shape (n_scans, n_voxels)
        Functional data
    confounds : ndarray, shape (n_scans, n_confounds)
        Confound regressors

    Returns
    -------
    data_clean : ndarray, shape (n_scans, n_voxels)
        Data with confounds regressed out
    """
    # Add intercept
    X = np.hstack([confounds, np.ones((confounds.shape[0], 1))])

    # OLS regression: beta = (X'X)^-1 X'y
    betas = np.linalg.pinv(X) @ data

    # Predicted confound signal
    confound_signal = X @ betas

    # Remove confound signal
    data_clean = data - confound_signal

    return data_clean

def build_fir_design_matrix(onsets, n_scans, tr, fir_delays, drift_model='per_run', run_idx=None, n_runs=None):
    """
    Build FIR design matrix (color-ignored, single regressor per delay)
    Optionally includes per-run drift regressors to model baseline and drift

    Parameters:
    -----------
    onsets : array-like
        Event onset times in seconds
    n_scans : int
        Total number of TRs for THIS run
    tr : float
        Repetition time
    fir_delays : array-like
        FIR delay indices (e.g., [0,1,2,3,4,5,6,7])
    drift_model : str, optional
        'per_run' to include per-run drift, 'none' to exclude drift
        Default: 'per_run' (B&H 2009 behavior)
    run_idx : int, optional
        Run index (0-based). Required if drift_model='per_run'
    n_runs : int, optional
        Total number of runs. Required if drift_model='per_run'

    Returns:
    --------
    X : ndarray
        FIR design matrix

        If drift_model='per_run':
            shape (n_scans, len(fir_delays) + 2*n_runs)
            Columns: [FIR_0, ..., FIR_7, run0_linear, run0_const, ..., run5_linear, run5_const]
            Only this run's drift columns are non-zero

        If drift_model='none':
            shape (n_scans, len(fir_delays))
            Columns: [FIR_0, ..., FIR_7]
    """
    n_delays = len(fir_delays)

    # FIR regressors
    X_fir = np.zeros((n_scans, n_delays))
    for onset in onsets:
        onset_tr = int(np.round(onset / tr))
        for i, delay in enumerate(fir_delays):
            tr_idx = onset_tr + delay
            if 0 <= tr_idx < n_scans:
                X_fir[tr_idx, i] += 1.0  # FIX: Accumulate (not overwrite)

    # Drift regressors (controlled by drift_model parameter)
    if drift_model == 'per_run':
        if run_idx is None or n_runs is None:
            raise ValueError("run_idx and n_runs are required when drift_model='per_run'")

        # Per-run drift regressors
        # Create drift columns for ALL runs, but only fill this run's columns
        drift_cols = np.zeros((n_scans, 2 * n_runs))

        # This run's linear drift column
        linear_col_idx = run_idx * 2
        drift_cols[:, linear_col_idx] = np.linspace(-1, 1, n_scans)

        # This run's constant column
        const_col_idx = run_idx * 2 + 1
        drift_cols[:, const_col_idx] = 1.0

        X = np.hstack([X_fir, drift_cols])
    elif drift_model == 'none':
        # No drift regressors
        X = X_fir
    else:
        raise ValueError(f"Unknown drift_model: {drift_model}. Use 'per_run' or 'none'")

    return X

def build_2nd_level_design_matrix(events, n_scans, tr, roi_hrf, roi_hrf_deriv, add_intercept=False):
    """
    Build 2nd-level GLM design matrix with HRF and derivative regressors

    Original B&H (2009): 16 columns, NO drift regressors
    Modified: Optional intercept to remove run baseline shifts (when highpass=0)

    Parameters:
    -----------
    events : DataFrame
        Events with 'onset' and 'trial_type' columns
    n_scans : int
        Total number of TRs
    tr : float
        Repetition time
    roi_hrf : array-like, shape (8,)
        ROI average HRF
    roi_hrf_deriv : array-like, shape (8,)
        Numerical derivative of ROI HRF
    add_intercept : bool, default=False
        If True, add intercept column (17 columns total)
        Recommended when highpass=0 to absorb DC offset

    Returns:
    --------
    X : ndarray, shape (n_scans, 16 or 17)
        Design matrix [color_1⊗h, ..., color_8⊗h, color_1⊗h', ..., color_8⊗h', intercept?]
        - 16 columns (default): 8 HRF + 8 derivative
        - 17 columns (if add_intercept): 8 HRF + 8 derivative + 1 intercept
    """
    n_colors = 8
    n_cols = 2 * n_colors + (1 if add_intercept else 0)
    X = np.zeros((n_scans, n_cols))

    # Process each color
    for color_idx in range(1, n_colors + 1):
        color_name = f'color_{color_idx}'
        color_events = events[events['trial_type'] == color_name]

        # Create stick function
        stick = np.zeros(n_scans)
        for onset in color_events['onset'].values:
            onset_tr = int(np.round(onset / tr))
            if 0 <= onset_tr < n_scans:
                stick[onset_tr] = 1.0

        # Convolve with HRF
        hrf_response = np.convolve(stick, roi_hrf, mode='full')[:n_scans]
        X[:, color_idx - 1] = hrf_response

        # Convolve with derivative
        deriv_response = np.convolve(stick, roi_hrf_deriv, mode='full')[:n_scans]
        X[:, n_colors + color_idx - 1] = deriv_response

    # Add intercept if requested
    if add_intercept:
        X[:, -1] = 1.0  # Last column is constant intercept

    return X

def compute_r2(y_true, y_pred):
    """Compute R² (coefficient of determination)"""
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)

    # Avoid division by zero
    if ss_tot == 0:
        # If total variance is 0, the data is constant
        # Perfect prediction would give R² = 1, but we return 0 for safety
        return 0.0

    r2 = 1 - (ss_res / ss_tot)

    # R² can be negative if model is worse than mean
    # But shouldn't be NaN unless there's numerical issues
    if np.isnan(r2) or np.isinf(r2):
        return -np.inf

    return r2

# ============================================================================
# Parse Arguments
# ============================================================================

def parse_args():
    parser = argparse.ArgumentParser(description='B&H 2009 systematic preprocessing review')
    parser.add_argument('--subject', type=str, default='P01',
                        help='Subject ID (P01 for pilot, 01-04 for test subjects)')
    parser.add_argument('--roi', type=str, default='V1',
                        help='ROI name (e.g., V1, V2, V3, V4, hV4)')
    parser.add_argument('--dataset', type=str, default='method3_header_mi',
                        choices=['afni_deoblique_v3', 'deoblique_v2', 'deoblique', 'original', 'original_v3', 'method3_header_mi'],
                        help='Dataset version (method3_header_mi: MI-based registration [CURRENT], afni_deoblique_v3: AFNI deoblique, original_v3: FreeSurfer removed, deoblique_v2: header-only [DEPRECATED])')
    parser.add_argument('--roi-mask', type=str, default=None,
                        help='ROI mask file path (if None, auto-detect from derivatives/sub-XX/roi_pipeline/)')
    parser.add_argument('--roi-pipeline-dir', type=str, default='roi_pipeline',
                        help='ROI pipeline directory name (default: roi_pipeline)')
    parser.add_argument('--roi-config', type=str, default=None,
                        help='ROI mask configuration name (if None, auto-detect based on roi-pipeline-dir)')
    parser.add_argument('--timestamp', type=str, default=None,
                        help='Timestamp for output directory (default: auto-generated)')
    parser.add_argument('--use-pca', action='store_true',
                        help='Use PCA dimensionality reduction')
    parser.add_argument('--n-components', type=int, default=6,
                        help='Number of PCA components (only if --use-pca)')
    parser.add_argument('--output-dir', type=str, default=None,
                        help='Output directory (default: derivatives/V3_Comprehensive/BH2009_{dataset}/timestamp/)')

    # Preprocessing options
    parser.add_argument('--smooth', type=float, default=0.0,
                        help='Spatial smoothing FWHM in mm (0, 6, 8)')
    parser.add_argument('--highpass', type=float, default=None,
                        help='High-pass filter cutoff in Hz (None or 0.01)')
    parser.add_argument('--motion', type=str, default='none',
                        choices=['none', 'cosine', 'standard', 'extended'],
                        help='Motion confounds: cosine=Baseline32, standard=Method3+confounds')
    parser.add_argument('--compcor', type=int, default=None,
                        help='Number of aCompCor components (None or 5)')
    parser.add_argument('--drift', type=str, default='per_run',
                        choices=['none', 'per_run'],
                        help='Drift model (per_run or none)')
    parser.add_argument('--standardize', action='store_true',
                        help='Standardize voxels (z-score)')
    parser.add_argument('--normalize-level', type=str, default='1st_only',
                        choices=['1st_only', 'both', 'none'],
                        help='Normalization strategy: 1st_only (original, problematic), both (E1: consistent), none (E2: all original)')
    parser.add_argument('--2nd-level-intercept', action='store_true',
                        help='Add intercept to 2nd-level GLM (removes run baseline shifts when highpass=0)')
    parser.add_argument('--grid-resample', type=str, default='no',
                        choices=['no', 'yes'],
                        help='Resample all runs to common grid (run-1 reference) to ensure voxel correspondence')

    return parser.parse_args()

args = parse_args()

SUBJECT_ID = args.subject
ROI_NAME = args.roi
DATASET = args.dataset
USE_PCA = args.use_pca
N_PCA_COMPONENTS = args.n_components

# Preprocessing configuration
SMOOTH_FWHM = args.smooth
HIGHPASS_HZ = args.highpass
MOTION_TYPE = args.motion
COMPCOR_N = args.compcor
DRIFT_MODEL = args.drift
STANDARDIZE = args.standardize
NORMALIZE_LEVEL = args.normalize_level
ADD_2ND_LEVEL_INTERCEPT = args.__dict__['2nd_level_intercept']  # Use __dict__ for hyphenated arg
GRID_RESAMPLE = args.__dict__['grid_resample']  # Use __dict__ for hyphenated arg

# Generate config name for figures
def config_to_name(smooth, highpass, motion, compcor, drift, standardize, normalize_level):
    """Convert config parameters to initials format"""
    sm = f"sm{smooth}"
    hp = "hpYe" if highpass else "hpNo"
    mo = {'none': 'moNo', 'cosine': 'moCo', 'standard': 'moSt', 'extended': 'moEx'}[motion]
    cc = "ccYe" if compcor else "ccNo"
    dr = "drPr" if drift == 'per_run' else "drNo"
    st = "stTr" if standardize else "stFa"
    nz = {'1st_only': 'nz1st', 'both': 'nzBoth', 'none': 'nzNone'}[normalize_level]
    return f"{sm}_{hp}_{mo}_{cc}_{dr}_{st}_{nz}"

CONFIG_NAME = config_to_name(SMOOTH_FWHM, HIGHPASS_HZ, MOTION_TYPE, COMPCOR_N, DRIFT_MODEL, STANDARDIZE, NORMALIZE_LEVEL)

# Determine pilot vs test
IS_PILOT = (SUBJECT_ID == 'P01')
LABEL2HUE_DEG = LABEL2HUE_DEG_PILOT if IS_PILOT else LABEL2HUE_DEG_TEST

# ============================================================================
# Path Configuration
# ============================================================================

# Dataset-specific paths
DATASET_CONFIGS = {
    'deoblique_v2': {
        'fmriprep': '/storage/connectome/haba6030/fmriprep_out_deoblique_v2',
        'events': '/storage/connectome/haba6030/colorBlind_data_deoblique',
        'description': 'v2: fieldmap applied, DOF 9, BBR forced (DEPRECATED - use v3)'
    },
    'original': {
        'fmriprep': '/storage/connectome/haba6030/fmriprep_out_new',
        'events': '/storage/connectome/haba6030/colorBlind_dataOct',
        'description': 'Original fmriprep output (new version)'
    },
    'original_v3': {
        'fmriprep': '/storage/connectome/haba6030/fmriprep_out_original_v3',
        'events': '/storage/connectome/haba6030/bids_editted',
        'description': 'v3: Original data with FreeSurfer removed (--fs-no-reconall)'
    },
    'method3_header_mi': {
        'fmriprep': '/storage/connectome/haba6030/fmriprep_out_method3_header_mi',
        'events': '/storage/connectome/haba6030/bids_editted',
        'description': 'Method3: Header→MI registration (mri_coreg), MNI152NLin2009cAsym'
    }
}

# Get paths for selected dataset
dataset_config = DATASET_CONFIGS[DATASET]
FMRIPREP_BASE = dataset_config['fmriprep']
EVENT_DIR = dataset_config['events']

# All subjects use standard structure (no pilot folder in deoblique data)
# Subject IDs: 01-07 (Non-CVD), 08-10 (CVD)
FMRIPREP_DIR = f"{FMRIPREP_BASE}/sub-{SUBJECT_ID}"
FILE_PREFIX = f"sub-{SUBJECT_ID}"
DERIVATIVE_PREFIX = f"sub-{SUBJECT_ID}"
EVENTS_DIR = f"{EVENT_DIR}/sub-{SUBJECT_ID}/func"

# ============================================================================
# Setup Output Directory
# ============================================================================

from datetime import datetime

# Generate timestamp for settings.json
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

if args.output_dir:
    # Systematic review mode: use provided directory directly (no timestamp)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_dir = str(output_dir)
    fig_dir = str(output_dir) + '/figures_'
else:
    # Special case: drift='per_run' with fixed bugs → save to baseline_decoding/fixed_perRun
    if DRIFT_MODEL == 'per_run':
        output_dir = Path(f"analysis/phase1_preprocess_decoding/{DATASET}/results/baseline_decoding/fixed_perRun/sub-{SUBJECT_ID}/{ROI_NAME}")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_dir = str(output_dir)
        fig_dir = str(output_dir) + '/figures_'
        print("🔧 FIXED VERSION: Using drift='per_run' (intercept + linear drift)")
    else:
        # Standard mode: organized by normalization level and motion type
        # Structure: analysis/phase1_preprocess_decoding/{dataset}/results/factorial_experiment/{normalize}_{motion}/sub-{subject}/{roi}
        nz_short = {'1st_only': 'nz1st', 'both': 'nzBoth', 'none': 'nzNone'}[NORMALIZE_LEVEL]
        mo_short = {'none': 'moNo', 'cosine': 'moCo', 'standard': 'moSt', 'extended': 'moEx'}[MOTION_TYPE]
        condition_name = f"{nz_short}_{mo_short}"
        output_dir = Path(f"analysis/phase1_preprocess_decoding/{DATASET}/results/factorial_experiment/{condition_name}/sub-{SUBJECT_ID}/{ROI_NAME}")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_dir = str(output_dir)
        fig_dir = str(output_dir) + '/figures_'

# Logs directory
logs_dir = Path(f"analysis/phase1_preprocess_decoding/{DATASET}/logs")
logs_dir.mkdir(parents=True, exist_ok=True)

print("="*70)
print(f"Dataset: {DATASET} - {dataset_config['description']}")
print(f"Subject: {SUBJECT_ID}")
print(f"ROI: {ROI_NAME}")
print(f"FIR delays: {len(FIR_DELAYS)} (0-{len(FIR_DELAYS)-1}, matching B&H 2009)")
print(f"Use PCA: {USE_PCA}")
if USE_PCA:
    print(f"PCA components: {N_PCA_COMPONENTS}")
print()
print(f"Preprocessing Configuration:")
print(f"  Smooth FWHM: {SMOOTH_FWHM} mm")
print(f"  Highpass: {HIGHPASS_HZ} Hz" if HIGHPASS_HZ else "  Highpass: None")
print(f"  Motion confounds: {MOTION_TYPE}")
print(f"  CompCor: {COMPCOR_N}" if COMPCOR_N else "  CompCor: None")
print(f"  Drift model: {DRIFT_MODEL}")
print(f"  Normalization level: {NORMALIZE_LEVEL} ← FACTORIAL EXPERIMENT")
print()
print(f"fMRIPrep: {FMRIPREP_BASE}")
print(f"Events: {EVENT_DIR}")
print(f"Output directory: {output_dir}")
print()
sys.stdout.flush()

# ============================================================================
# Load ROI Mask
# ============================================================================

print(f"[1/9] Loading ROI mask")
sys.stdout.flush()

# Determine ROI path: use command-line arg if provided, otherwise auto-detect
if args.roi_mask:
    roi_path = args.roi_mask
    print(f"  Using provided ROI mask: {roi_path}")
else:
    # Auto-detect ROI mask
    # Priority 1: Check new shared location - analysis/roi_masks/{dataset}/sub-{ID}/roi_pipeline/
    shared_roi_path = os.path.join(BASE_DIR, f"analysis/roi_masks/{DATASET}/sub-{SUBJECT_ID}/roi_pipeline/{ROI_NAME}_mask_thr50_intnearest_binTrue_masknone_gmTrue_subjTrue.nii.gz")
    print(f"  Searching shared ROI path: {shared_roi_path}")

    if os.path.exists(shared_roi_path):
        roi_path = shared_roi_path
        print(f"  ✓ Found ROI mask in shared location")
        print(f"  {roi_path}")

if not os.path.exists(roi_path):
    # Try alternative patterns
    print(f"\n⚠️  Primary ROI mask not found: {roi_path}")
    print(f"  Trying alternative patterns...")

    # Alternative 1: Try shared location with glob pattern (any parameter combination)
    shared_search_pattern = os.path.join(BASE_DIR, f"analysis/roi_masks/{DATASET}/sub-{SUBJECT_ID}/roi_pipeline/{ROI_NAME}_mask_*.nii.gz")
    shared_matches = glob.glob(shared_search_pattern)

    if shared_matches:
        # Prefer binTrue masks
        preferred = [f for f in shared_matches if 'binTrue' in f]
        roi_path = preferred[0] if preferred else shared_matches[0]
        print(f"  ✓ Found shared location ROI mask: {roi_path}")
    else:
        print(f"\n❌ ERROR: No ROI mask file found!")
        print(f"  Searched in:")
        print(f"    - analysis/roi_masks/{DATASET}/sub-{SUBJECT_ID}/roi_pipeline/")
        print(f"\n  Please check:")
        print(f"  1. ROI masks have been created with roi_pipeline")
        print(f"  2. Path structure matches expected format")
        print(f"  3. ROI name '{ROI_NAME}' is correct")

        sys.exit(1)

roi_img = nib.load(roi_path)
roi_data = roi_img.get_fdata()

print(f"  ROI: {ROI_NAME}")
print(f"  ROI mask path: {roi_path}")
print(f"  ROI mask shape: {roi_img.shape}")
print(f"  ROI data type: {roi_data.dtype}")
print(f"  ROI value range: [{roi_data.min():.4f}, {roi_data.max():.4f}]")

# Count voxels with different thresholds
n_voxels_any = np.sum(roi_data > 0)
n_voxels_0p5 = np.sum(roi_data > 0.5)
n_voxels_1 = np.sum(roi_data > 1)

print(f"  Voxels > 0:   {n_voxels_any}")
print(f"  Voxels > 0.5: {n_voxels_0p5}")
print(f"  Voxels > 1:   {n_voxels_1}")

# Use the appropriate threshold
if n_voxels_any > 0:
    # Create binary mask
    roi_mask = roi_data > 0
    n_voxels_total = n_voxels_any
    print(f"  Using threshold > 0: {n_voxels_total} voxels")
else:
    print(f"\n❌ ERROR: ROI mask is completely empty (all zeros)!")
    print(f"  File exists but contains no voxels.")
    print(f"  Please check roi_pipeline output for this subject/ROI.")
    sys.exit(1)

# Initialize masker with the loaded mask image
# Use config-based standardization
masker = NiftiMasker(mask_img=roi_img, standardize=STANDARDIZE)
masker.fit()

print()
sys.stdout.flush()

# ============================================================================
# Load Functional Data
# ============================================================================

print(f"[2/9] Loading functional data ({N_RUNS} runs)")
sys.stdout.flush()

func_imgs = []
events_list = []
all_func_data = []  # Store as numpy arrays for voxel-wise processing

# Grid resampling: initialize reference grid variables
reference_affine = None
reference_shape = None

for run in range(1, N_RUNS + 1):
    # Functional image
    func_path = f"{FMRIPREP_DIR}/func/{FILE_PREFIX}_task-rsvp_run-{run}_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz"

    if not os.path.exists(func_path):
        print(f"ERROR: Functional image not found: {func_path}")
        sys.exit(1)

    func_img = nib.load(func_path)

    # PREPROCESSING STEP 1: Spatial smoothing
    if SMOOTH_FWHM > 0:
        func_img = nimg.smooth_img(func_img, fwhm=SMOOTH_FWHM)

    if VOLS_TO_DROP > 0:
        func_img = nimg.index_img(func_img, slice(VOLS_TO_DROP, None))

    # GRID RESAMPLING: Ensure all runs use identical voxel grid
    if GRID_RESAMPLE == 'yes':
        if run == 1:
            # First run: save as reference grid
            reference_affine = func_img.affine.copy()
            reference_shape = func_img.shape[:3]
            print(f"  Grid resampling: Using run {run} as reference")
            print(f"    Reference shape: {reference_shape}")
            print(f"    Reference affine diagonal: {np.diag(reference_affine)[:3]}")

            # Resample mask to match run-1 BOLD grid
            roi_img_resampled = resample_mask_to_grid(
                roi_img,
                target_affine=reference_affine,
                target_shape=reference_shape,
                interpolation='nearest'
            )

            # Reinitialize masker with resampled mask
            masker = NiftiMasker(mask_img=roi_img_resampled, standardize=STANDARDIZE)
            masker.fit()
            print(f"    Mask resampled and masker reinitialized")
        else:
            # Subsequent runs: resample to reference grid
            print(f"  Grid resampling: Resampling run {run} to reference grid...")
            func_img_list = [func_img]
            resampled_list, _, _ = resample_runs_to_common_grid(
                func_img_list,
                reference_idx=0,
                interpolation='continuous'
            )
            func_img = resampled_list[0]

            # Verify alignment
            affine_match = np.allclose(func_img.affine, reference_affine, atol=1e-6)
            shape_match = func_img.shape[:3] == reference_shape
            print(f"    Resampled: affine_match={affine_match}, shape_match={shape_match}")

    func_imgs.append(func_img)

    # Extract data for this run (masked)
    func_data = masker.transform(func_img)  # (n_scans, n_voxels)

    # Safety check for masker output
    if func_data.shape[1] == 0:
        print(f"\n❌ ERROR: Masker extracted 0 voxels from run {run}!")
        print(f"  Functional image shape: {func_img.shape}")
        print(f"  Masked data shape: {func_data.shape}")
        print(f"  This means the ROI mask and functional data don't align properly.")
        sys.exit(1)

    # PREPROCESSING STEP 2: High-pass filtering
    # Skip if using cosine confounds (they already perform high-pass filtering)
    if HIGHPASS_HZ is not None and HIGHPASS_HZ > 0 and MOTION_TYPE != 'cosine':
        from nilearn import signal
        func_data = signal.clean(func_data, detrend=False, standardize=False,
                                high_pass=HIGHPASS_HZ, t_r=TR)
        print(f"    Applied {HIGHPASS_HZ} Hz high-pass filter")
    elif HIGHPASS_HZ is not None and HIGHPASS_HZ > 0 and MOTION_TYPE == 'cosine':
        print(f"    Skipping high-pass filter (using cosine regressors for drift removal)")
    elif HIGHPASS_HZ == 0:
        print(f"    No high-pass filter (highpass=0, preserving all frequencies)")

    # PREPROCESSING STEP 3: Confounds regression
    if MOTION_TYPE != 'none' or COMPCOR_N is not None:
        confounds_path = func_path.replace('_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz', '_desc-confounds_timeseries.tsv')

        if not os.path.exists(confounds_path):
            print(f"\n⚠️  WARNING: Confounds file not found: {confounds_path}")
            print(f"  Skipping confounds regression for run {run}")
        else:
            confounds, n_conf = load_motion_confounds(
                confounds_path,
                motion_type=MOTION_TYPE,
                compcor_n=COMPCOR_N
            )

            if confounds is not None:
                # Drop first volumes to match func_data
                if VOLS_TO_DROP > 0:
                    confounds = confounds[VOLS_TO_DROP:, :]

                # Regress confounds
                func_data = regress_confounds(func_data, confounds)

    all_func_data.append(func_data)

    # Events
    events_path = f"{EVENTS_DIR}/{FILE_PREFIX}_task-rsvp_run-{run}_events.tsv"

    if not os.path.exists(events_path):
        print(f"ERROR: Events file not found: {events_path}")
        sys.exit(1)

    events = pd.read_csv(events_path, sep='\t')

    # DEBUG: Check events before adjustment
    n_events_original = len(events)
    onset_min_original = events['onset'].min()
    onset_max_original = events['onset'].max()

    # Adjust onset times for dropped volumes
    if VOLS_TO_DROP > 0:
        events['onset'] = events['onset'] - (VOLS_TO_DROP * TR)
        events = events[events['onset'] >= 0].reset_index(drop=True)

    events_list.append(events)

    # DEBUG: Detailed event and functional data info
    n_events_after = len(events)
    n_events_removed = n_events_original - n_events_after
    func_duration = func_data.shape[0] * TR

    # Build preprocessing summary
    preproc_steps = []
    if SMOOTH_FWHM > 0:
        preproc_steps.append(f"smooth={SMOOTH_FWHM}mm")
    if HIGHPASS_HZ is not None:
        preproc_steps.append(f"highpass={HIGHPASS_HZ}Hz")
    if MOTION_TYPE != 'none':
        preproc_steps.append(f"motion={MOTION_TYPE}")
    if COMPCOR_N is not None:
        preproc_steps.append(f"compcor={COMPCOR_N}")
    if DRIFT_MODEL == 'per_run':
        preproc_steps.append("drift=per_run")
    if STANDARDIZE:
        preproc_steps.append("standardize=True")

    preproc_summary = ", ".join(preproc_steps) if preproc_steps else "None"

    print(f"  Run {run}:")
    print(f"    Functional: {func_data.shape[0]} scans = {func_duration:.1f}초 | Voxels: {func_data.shape[1]}")
    print(f"    Preprocessing: {preproc_summary}")
    print(f"    Events: {n_events_original} → {n_events_after} ({n_events_removed} removed)")
    print(f"    Onset range: original [{onset_min_original:.1f}, {onset_max_original:.1f}]초")
    if n_events_after > 0:
        print(f"                adjusted [{events['onset'].min():.1f}, {events['onset'].max():.1f}]초")
    else:
        print(f"                ⚠️  WARNING: All events were removed!")

print(f"  Total: {len(func_imgs)} runs loaded")

# Final voxel count verification
if len(all_func_data) > 0:
    n_voxels_extracted = all_func_data[0].shape[1]
    print(f"\n  Summary:")
    print(f"    Voxels in mask file: {n_voxels_total}")
    print(f"    Voxels extracted by masker: {n_voxels_extracted}")

    if n_voxels_extracted != n_voxels_total:
        print(f"    ⚠️  WARNING: Mismatch between mask voxels and extracted voxels!")
        print(f"       This might indicate coordinate system issues.")

    if n_voxels_extracted == 0:
        print(f"\n❌ ERROR: Masker extracted 0 voxels!")
        print(f"  Possible causes:")
        print(f"  1. ROI mask and functional data have different coordinate systems")
        print(f"  2. ROI mask needs resampling to functional space")
        print(f"  3. Affine matrices don't match")
        sys.exit(1)

print()
sys.stdout.flush()

# ============================================================================
# Step 1: Voxel-wise FIR HRF Estimation
# ============================================================================

print(f"[3/9] Step 1: Voxel-wise FIR HRF estimation")
print(f"  Estimating HRF for {n_voxels_extracted} voxels using pseudo-inverse")
print(f"  FIR delays: {len(FIR_DELAYS)} time points")
sys.stdout.flush()

# Use the actual extracted voxel count
n_voxels_total = n_voxels_extracted

# Combine all runs for voxel-wise HRF estimation
HRF_voxel = np.zeros((n_voxels_total, len(FIR_DELAYS)))
r2_voxel = np.zeros(n_voxels_total)

# Store normalization statistics for 2nd-level consistency (if NORMALIZE_LEVEL == 'both')
voxel_norm_stats = {'mean': np.zeros(n_voxels_total), 'std': np.zeros(n_voxels_total)}

for voxel_idx in range(n_voxels_total):
    # Concatenate data across all runs
    y_voxel = []
    X_fir_all = []

    for run_idx in range(N_RUNS):
        y_run = all_func_data[run_idx][:, voxel_idx]
        y_voxel.append(y_run)

        # Get all onsets (color-ignored)
        events = events_list[run_idx]
        all_onsets = events['onset'].values

        # Build FIR design matrix for this run (drift controlled by DRIFT_MODEL)
        n_scans = all_func_data[run_idx].shape[0]
        X_fir = build_fir_design_matrix(all_onsets, n_scans, TR, FIR_DELAYS,
                                        drift_model=DRIFT_MODEL,
                                        run_idx=run_idx, n_runs=N_RUNS)
        X_fir_all.append(X_fir)

        # DEBUG: Check first run's design matrix
        if voxel_idx == 0 and run_idx == 0:
            print(f"\n  Design Matrix Debug (Run 1):")
            print(f"    Events in this run: {len(all_onsets)}")
            print(f"    Onset range: [{all_onsets.min():.1f}, {all_onsets.max():.1f}]초")
            print(f"    Expected onset TRs: [{int(all_onsets.min()/TR)}, {int(all_onsets.max()/TR)}]")
            print(f"    Functional scans: {n_scans} (indices 0-{n_scans-1})")
            print(f"    X_fir shape: {X_fir.shape}")
            print(f"    X_fir non-zero: {np.sum(X_fir > 0)} (expected: ~{len(all_onsets) * len(FIR_DELAYS)})")
            print(f"    X_fir density: {np.sum(X_fir > 0) / X_fir.size * 100:.2f}%")

    # Concatenate across runs
    y_voxel = np.concatenate(y_voxel)
    X_fir_all = np.vstack(X_fir_all)

    # Debug: Check first voxel in detail (BEFORE normalization)
    if voxel_idx == 0:
        print(f"\n  Combined Design Matrix Debug (All runs):")
        print(f"    y_voxel shape: {y_voxel.shape} (all runs concatenated)")
        print(f"    X_fir_all shape: {X_fir_all.shape}")
        print(f"    y_voxel range (raw): [{np.min(y_voxel):.2f}, {np.max(y_voxel):.2f}]")
        print(f"    y_voxel mean (raw): {np.mean(y_voxel):.2f}, std: {np.std(y_voxel):.2f}")
        print(f"    X_fir_all non-zero entries: {np.sum(X_fir_all > 0)}/{X_fir_all.size}")
        print(f"    X_fir_all density: {np.sum(X_fir_all > 0) / X_fir_all.size * 100:.2f}%")

        # Check if design matrix is valid
        rank = np.linalg.matrix_rank(X_fir_all)
        print(f"    X_fir_all rank: {rank}/{X_fir_all.shape[1]} (should be {X_fir_all.shape[1]})")

        if rank < X_fir_all.shape[1]:
            print(f"    ⚠️  WARNING: Design matrix is rank deficient!")

    # ============================================================================
    # Z-SCORE NORMALIZATION (Conditional on NORMALIZE_LEVEL)
    # ============================================================================
    # NORMALIZE_LEVEL options:
    #   'none': No normalization (E2: all original)
    #   '1st_only': Normalize 1st level only (original, problematic)
    #   'both': Normalize both levels consistently (E1: consistent)

    if NORMALIZE_LEVEL == 'none':
        # E2: All original - no normalization
        y_voxel_for_estimation = y_voxel
        voxel_norm_stats['mean'][voxel_idx] = 0.0  # Not used
        voxel_norm_stats['std'][voxel_idx] = 1.0   # Not used

        if voxel_idx == 0:
            print(f"\n  1st-level Normalization: NONE (E2: all original)")
            print(f"    y_voxel range: [{np.min(y_voxel):.2f}, {np.max(y_voxel):.2f}]")
            print(f"    y_voxel mean: {np.mean(y_voxel):.2f}, std: {np.std(y_voxel):.2f}")

    else:
        # '1st_only' or 'both': Normalize 1st level
        y_voxel_mean = np.mean(y_voxel)
        y_voxel_std = np.std(y_voxel)

        # Store for potential 2nd-level use
        voxel_norm_stats['mean'][voxel_idx] = y_voxel_mean
        voxel_norm_stats['std'][voxel_idx] = y_voxel_std

        if y_voxel_std > 1e-10:  # Avoid division by zero
            y_voxel_normalized = (y_voxel - y_voxel_mean) / y_voxel_std
        else:
            # This voxel has zero variance (constant signal)
            y_voxel_normalized = y_voxel

        y_voxel_for_estimation = y_voxel_normalized

        if voxel_idx == 0:
            mode_str = "1st-level ONLY (original, scale mismatch)" if NORMALIZE_LEVEL == '1st_only' else "BOTH levels (E1: consistent)"
            print(f"\n  1st-level Normalization: {mode_str}")
            print(f"    y_voxel range (normalized): [{np.min(y_voxel_normalized):.2f}, {np.max(y_voxel_normalized):.2f}]")
            print(f"    y_voxel mean (normalized): {np.mean(y_voxel_normalized):.4f}, std: {np.std(y_voxel_normalized):.4f}")
            print(f"    Original baseline: {y_voxel_mean:.2f}")
            print(f"    Original scale: {y_voxel_std:.2f}")

    # Estimate HRF using pseudo-inverse: beta = pinv(X) @ y
    # beta includes: [FIR_0, ..., FIR_7, linear_drift, constant]
    try:
        beta_full = np.linalg.pinv(X_fir_all) @ y_voxel_for_estimation

        # Extract HRF (first 8 elements, excluding drift regressors)
        h_v = beta_full[:len(FIR_DELAYS)]
        HRF_voxel[voxel_idx] = h_v

        # Compute R² using full model (including drift) on NORMALIZED data
        y_pred = X_fir_all @ beta_full
        r2_voxel[voxel_idx] = compute_r2(y_voxel_for_estimation, y_pred)

        # Debug first voxel R²
        if voxel_idx == 0:
            ss_res = np.sum((y_voxel_for_estimation - y_pred) ** 2)
            ss_tot = np.sum((y_voxel_for_estimation - np.mean(y_voxel_for_estimation)) ** 2)

            # Also compute correlation for comparison
            y_true_centered = y_voxel_for_estimation - np.mean(y_voxel_for_estimation)
            y_pred_centered = y_pred - np.mean(y_pred)
            correlation = np.sum(y_true_centered * y_pred_centered) / (
                np.sqrt(np.sum(y_true_centered**2)) * np.sqrt(np.sum(y_pred_centered**2))
            )

            print(f"\n  R² Calculation Debug (on normalized data):")
            print(f"    y_pred range: [{np.min(y_pred):.2f}, {np.max(y_pred):.2f}]")
            print(f"    y_pred mean: {np.mean(y_pred):.4f}, std: {np.std(y_pred):.4f}")
            print(f"    SS_res (residual sum of squares): {ss_res:.4f}")
            print(f"    SS_tot (total sum of squares): {ss_tot:.4f}")
            print(f"    Ratio (SS_res/SS_tot): {ss_res/ss_tot:.4f}")
            print(f"    R² = 1 - (SS_res/SS_tot) = {r2_voxel[voxel_idx]:.4f}")
            print(f"    Correlation (for comparison): {correlation:.4f}")
            print(f"    R² should ≈ correlation² = {correlation**2:.4f}")
            print(f"    HRF peak value: {np.max(np.abs(h_v)):.4f}")
            print(f"    HRF peak delay: {np.argmax(np.abs(h_v))} TRs")

            # Diagnostic: Check design matrix condition
            cond_number = np.linalg.cond(X_fir_all)
            print(f"\n  Design Matrix Diagnostics:")
            print(f"    Condition number: {cond_number:.2f}")
            if cond_number > 30:
                print(f"    ⚠️  WARNING: High multicollinearity (>30)")
            elif cond_number > 100:
                print(f"    🚨 CRITICAL: Severe multicollinearity (>100)")
    except Exception as e:
        if voxel_idx == 0:
            print(f"    ❌ ERROR in HRF estimation: {e}")
        HRF_voxel[voxel_idx] = 0
        r2_voxel[voxel_idx] = -np.inf

    if (voxel_idx + 1) % 100 == 0:
        print(f"  Processed {voxel_idx + 1}/{n_voxels_total} voxels", end='\r')

print(f"  Processed {n_voxels_total}/{n_voxels_total} voxels")

# Check for issues in HRF estimation
n_valid_hrfs = np.sum(~np.all(HRF_voxel == 0, axis=1))
n_valid_r2 = np.sum(~np.isinf(r2_voxel))

print(f"\n  Quality check:")
print(f"    Voxels with non-zero HRF: {n_valid_hrfs}/{n_voxels_total}")
print(f"    Voxels with valid R²: {n_valid_r2}/{n_voxels_total}")

if n_valid_r2 == 0:
    print(f"\n❌ ERROR: All voxels have invalid R²!")
    print(f"  This indicates a problem with the FIR design matrix or data.")
    print(f"  Please check:")
    print(f"  1. Event onset times are correct")
    print(f"  2. Functional data is not all zeros")
    print(f"  3. FIR delays are appropriate")
    sys.exit(1)

print()

# ============================================================================
# Enhanced R² Analysis and Visualization
# ============================================================================

print(f"  === R² Distribution Analysis ===")

# Basic statistics
r2_mean = np.mean(r2_voxel)
r2_median = np.median(r2_voxel)
r2_std = np.std(r2_voxel)
r2_min = np.min(r2_voxel)
r2_max = np.max(r2_voxel)

print(f"  Mean:   {r2_mean:.4f}")
print(f"  Median: {r2_median:.4f} (will be used as threshold)")
print(f"  Std:    {r2_std:.4f}")
print(f"  Min:    {r2_min:.4f}")
print(f"  Max:    {r2_max:.4f}")

# Percentile analysis
percentiles = [10, 25, 50, 75, 90, 95, 99]
r2_percentiles = np.percentile(r2_voxel, percentiles)

print(f"\n  Percentiles:")
for p, val in zip(percentiles, r2_percentiles):
    print(f"    {p:2d}th: {val:.4f}")

# Count voxels with good fit
good_fit_counts = {
    'R² > 0.1': np.sum(r2_voxel > 0.1),
    'R² > 0.2': np.sum(r2_voxel > 0.2),
    'R² > 0.3': np.sum(r2_voxel > 0.3),
    'R² > 0.5': np.sum(r2_voxel > 0.5),
}

print(f"\n  Voxels with good fit:")
for criterion, count in good_fit_counts.items():
    pct = 100 * count / n_voxels_total
    print(f"    {criterion}: {count}/{n_voxels_total} ({pct:.1f}%)")

print()

# Additional QC for drift_model='per_run'
if DRIFT_MODEL == 'per_run':
    print(f"🔍 DRIFT MODEL VERIFICATION:")
    print(f"   Design matrix shape: {X_fir_all.shape}")
    print(f"   Expected: ({X_fir_all.shape[0]}, {len(FIR_DELAYS) + 2 * N_RUNS})")

    # Check if intercept columns are all 1.0 for each run
    n_scans_per_run = X_fir_all.shape[0] // N_RUNS
    all_runs_ok = True

    for run_idx in range(N_RUNS):
        start = run_idx * n_scans_per_run
        end = (run_idx + 1) * n_scans_per_run

        # This run's intercept column
        const_col_idx = len(FIR_DELAYS) + run_idx * 2 + 1
        run_const_col = X_fir_all[start:end, const_col_idx]

        is_constant_ones = np.allclose(run_const_col, 1.0)
        print(f"   Run {run_idx+1}: Intercept column = {is_constant_ones}")

        if not is_constant_ones:
            print(f"     ⚠️  WARNING: Run {run_idx+1} intercept may be wrong!")
            all_runs_ok = False

    if all_runs_ok:
        print(f"\n   ✅ All runs have correct intercept implementation!")
    else:
        print(f"\n   ❌ Some runs have incorrect intercept!")

    print()

sys.stdout.flush()

# Visualize R² distribution
fig_r2, axes = plt.subplots(2, 2, figsize=(14, 10))
fig_r2.suptitle(f'{ROI_NAME}: R² Distribution Analysis', fontsize=16, fontweight='bold')

# Top-left: Histogram
ax1 = axes[0, 0]
ax1.hist(r2_voxel, bins=50, edgecolor='black', alpha=0.7, color='steelblue')
ax1.axvline(r2_median, color='red', linestyle='--', linewidth=2, label=f'Median (threshold) = {r2_median:.3f}')
ax1.axvline(r2_mean, color='orange', linestyle='--', linewidth=2, label=f'Mean = {r2_mean:.3f}')
ax1.set_xlabel('R² value')
ax1.set_ylabel('Number of voxels')
ax1.set_title('R² Distribution (Histogram)')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Top-right: Cumulative distribution
ax2 = axes[0, 1]
sorted_r2 = np.sort(r2_voxel)
cumulative = np.arange(1, len(sorted_r2) + 1) / len(sorted_r2) * 100
ax2.plot(sorted_r2, cumulative, linewidth=2, color='steelblue')
ax2.axvline(r2_median, color='red', linestyle='--', linewidth=2, label='Median (50%)')
ax2.axhline(50, color='red', linestyle=':', alpha=0.5)
ax2.set_xlabel('R² value')
ax2.set_ylabel('Cumulative percentage (%)')
ax2.set_title('Cumulative R² Distribution')
ax2.legend()
ax2.grid(True, alpha=0.3)

# Bottom-left: Box plot with percentiles
ax3 = axes[1, 0]
bp = ax3.boxplot([r2_voxel], vert=True, patch_artist=True, widths=0.5)
bp['boxes'][0].set_facecolor('lightblue')
bp['boxes'][0].set_edgecolor('black')
bp['medians'][0].set_color('red')
bp['medians'][0].set_linewidth(2)
ax3.set_ylabel('R² value')
ax3.set_title('R² Box Plot')
ax3.grid(True, alpha=0.3, axis='y')
ax3.set_xticklabels([f'{ROI_NAME}\n(n={n_voxels_total})'])

# Add percentile annotations
for p, val in zip([25, 50, 75], [np.percentile(r2_voxel, p) for p in [25, 50, 75]]):
    ax3.text(1.15, val, f'{p}th: {val:.3f}', va='center', fontsize=9)

# Bottom-right: Good fit threshold analysis
ax4 = axes[1, 1]
thresholds = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
voxel_counts = [np.sum(r2_voxel > t) for t in thresholds]
voxel_pcts = [100 * c / n_voxels_total for c in voxel_counts]

bars = ax4.bar(range(len(thresholds)), voxel_pcts, edgecolor='black', alpha=0.7, color='steelblue')

# Highlight median threshold
median_idx = np.argmin(np.abs(np.array(thresholds) - r2_median))
bars[median_idx].set_color('red')
bars[median_idx].set_alpha(0.9)

ax4.set_xlabel('R² threshold')
ax4.set_ylabel('Percentage of voxels (%)')
ax4.set_title('Voxels Above R² Threshold')
ax4.set_xticks(range(len(thresholds)))
ax4.set_xticklabels([f'{t:.1f}' for t in thresholds])
ax4.grid(True, alpha=0.3, axis='y')

# Add value labels on bars
for i, (count, pct) in enumerate(zip(voxel_counts, voxel_pcts)):
    ax4.text(i, pct + 2, f'{count}\n({pct:.1f}%)', ha='center', va='bottom', fontsize=8)

plt.tight_layout()
plt.savefig(fig_dir + 'r2_distribution_analysis.png', dpi=300, bbox_inches='tight')
plt.close()

print(f"  Saved: {fig_dir + 'r2_distribution_analysis.png'}")
print()
sys.stdout.flush()

# ============================================================================
# Step 2: Voxel Selection (Top 50% by R²)
# ============================================================================

print(f"[4/9] Step 2: Voxel selection (top 50% by R²)")
sys.stdout.flush()

# Get top 50% voxels by R²
# First, filter out invalid R² values
valid_r2_mask = ~(np.isnan(r2_voxel) | np.isinf(r2_voxel))
n_valid_r2 = np.sum(valid_r2_mask)

print(f"  Valid R² values: {n_valid_r2}/{n_voxels_total}")

if n_valid_r2 == 0:
    print(f"\n❌ ERROR: No voxels with valid R²!")
    print(f"  This means FIR HRF estimation failed for all voxels.")
    print(f"  Possible causes:")
    print(f"  1. Event onsets are incorrect or missing")
    print(f"  2. Functional data is problematic")
    print(f"  3. Design matrix rank deficiency")
    sys.exit(1)

if n_valid_r2 < 100:
    print(f"  ⚠️  WARNING: Very few voxels ({n_valid_r2}) have valid R²")
    print(f"     Using all valid voxels instead of top 50%")
    selected_voxels_mask = valid_r2_mask
    r2_threshold = np.min(r2_voxel[valid_r2_mask])
else:
    # Normal case: use median as threshold
    r2_threshold = np.median(r2_voxel[valid_r2_mask])
    selected_voxels_mask = (r2_voxel >= r2_threshold) & valid_r2_mask

n_voxels_selected = np.sum(selected_voxels_mask)

print(f"  R² threshold: {r2_threshold:.3f}")
print(f"  Selected voxels: {n_voxels_selected}/{n_voxels_total} ({100*n_voxels_selected/n_voxels_total:.1f}%)")

if n_voxels_selected == 0:
    print(f"\n❌ ERROR: No voxels selected even with valid R² filtering!")
    print(f"  This should not happen. Please check the data.")
    sys.exit(1)

print()
sys.stdout.flush()

# ============================================================================
# Step 3: ROI Average HRF and Derivative
# ============================================================================

print(f"[5/9] Step 3: Computing ROI average HRF")
sys.stdout.flush()

# Average HRF across selected voxels
ROI_HRF = np.mean(HRF_voxel[selected_voxels_mask], axis=0)

# Filter normalization statistics to selected voxels only (for 2nd-level)
voxel_norm_mean_selected = voxel_norm_stats['mean'][selected_voxels_mask]
voxel_norm_std_selected = voxel_norm_stats['std'][selected_voxels_mask]

# Compute numerical derivative
ROI_HRF_deriv = np.gradient(ROI_HRF)

print(f"  ROI HRF shape: {ROI_HRF.shape}")
print(f"  Peak delay: {np.argmax(np.abs(ROI_HRF))} (time={np.argmax(np.abs(ROI_HRF))*TR:.1f}s)")
print()
sys.stdout.flush()

# Visualize ROI HRF
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
times = FIR_DELAYS * TR

axes[0].plot(times, ROI_HRF, 'b-', linewidth=2, marker='o', label='ROI HRF')
axes[0].axhline(y=0, color='gray', linestyle=':', alpha=0.5)
axes[0].axvline(x=np.argmax(np.abs(ROI_HRF))*TR, color='red', linestyle='--',
                alpha=0.5, label=f'Peak ({np.argmax(np.abs(ROI_HRF))*TR:.1f}s)')
axes[0].set_xlabel('Time (seconds)')
axes[0].set_ylabel('Response Amplitude')
axes[0].set_title(f'{ROI_NAME}: ROI Average HRF (top 50% voxels by R²)')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

axes[1].plot(times, ROI_HRF_deriv, 'r-', linewidth=2, marker='s', label='HRF Derivative')
axes[1].axhline(y=0, color='gray', linestyle=':', alpha=0.5)
axes[1].set_xlabel('Time (seconds)')
axes[1].set_ylabel('Derivative')
axes[1].set_title(f'{ROI_NAME}: HRF Derivative')
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(fig_dir + 'roi_hrf.png', dpi=300, bbox_inches='tight')
plt.close()
print(f"  Saved: {fig_dir + 'roi_hrf.png'}")
print()
sys.stdout.flush()

# ============================================================================
# Enhanced HRF Variability Analysis
# ============================================================================

print(f"  === HRF Variability Analysis ===")
print(f"  Analyzing how well ROI HRF represents individual voxels...")

# Safety check
if n_voxels_selected == 0:
    print(f"\n⚠️  WARNING: No voxels selected (R² threshold too high?)")
    print(f"  Skipping HRF variability analysis...")
    # Create dummy arrays to avoid errors downstream
    hrf_correlations = np.array([])
    hrf_rmse = np.array([])
    hrf_nrmse = np.array([])
    high_corr = 0
    very_high_corr = 0
else:
    # Get HRFs from selected voxels only
    HRF_selected = HRF_voxel[selected_voxels_mask]  # (n_voxels_selected, 8)

    # Compute voxel-wise correlation with ROI HRF
    hrf_correlations = np.zeros(n_voxels_selected)
    hrf_rmse = np.zeros(n_voxels_selected)
    hrf_nrmse = np.zeros(n_voxels_selected)

    for i in range(n_voxels_selected):
        # Correlation
        try:
            hrf_correlations[i] = np.corrcoef(HRF_selected[i], ROI_HRF)[0, 1]
        except:
            hrf_correlations[i] = np.nan

        # RMSE
        hrf_rmse[i] = np.sqrt(np.mean((HRF_selected[i] - ROI_HRF)**2))

        # Normalized RMSE
        hrf_nrmse[i] = hrf_rmse[i] / (np.std(HRF_selected[i]) + 1e-8)

    # Remove NaN values
    valid_mask = ~np.isnan(hrf_correlations)
    hrf_correlations = hrf_correlations[valid_mask]
    hrf_rmse = hrf_rmse[valid_mask]
    hrf_nrmse = hrf_nrmse[valid_mask]

    if len(hrf_correlations) > 0:
        pass
        # print(f"\n  Correlation with ROI HRF:")
        # print(f"    Mean: {np.mean(hrf_correlations):.4f}")
        # print(f"    Median: {np.median(hrf_correlations):.4f}")
        # print(f"    Std: {np.std(hrf_correlations):.4f}")
        # print(f"    Min: {np.min(hrf_correlations):.4f}")
        # print(f"    Max: {np.max(hrf_correlations):.4f}")
    else:
        print(f"\n  ⚠️  No valid correlations computed")

    # Check representativeness
    high_corr = np.sum(hrf_correlations > 0.8)
    very_high_corr = np.sum(hrf_correlations > 0.9)

print(f"\n  RMSE from ROI HRF:")
print(f"    Mean: {np.mean(hrf_rmse):.4f}")
print(f"    Median: {np.median(hrf_rmse):.4f}")

print(f"\n  Normalized RMSE:")
print(f"    Mean: {np.mean(hrf_nrmse):.4f}")
print(f"    Median: {np.median(hrf_nrmse):.4f}")

# Check representativeness
high_corr = np.sum(hrf_correlations > 0.8)
very_high_corr = np.sum(hrf_correlations > 0.9)

print(f"\n  Representativeness:")
print(f"    Voxels with r > 0.8: {high_corr}/{n_voxels_selected} ({100*high_corr/n_voxels_selected:.1f}%)")
print(f"    Voxels with r > 0.9: {very_high_corr}/{n_voxels_selected} ({100*very_high_corr/n_voxels_selected:.1f}%)")

if np.mean(hrf_correlations) > 0.85:
    print(f"  ✅ ROI HRF is highly representative (mean r = {np.mean(hrf_correlations):.3f})")
elif np.mean(hrf_correlations) > 0.70:
    print(f"  ⚠️  ROI HRF is moderately representative (mean r = {np.mean(hrf_correlations):.3f})")
else:
    print(f"  🚨 ROI HRF has low representativeness (mean r = {np.mean(hrf_correlations):.3f})")
    print(f"     → High voxel-to-voxel HRF variability")

print()
sys.stdout.flush()

# Visualize HRF variability
fig_hrf_var, axes = plt.subplots(2, 3, figsize=(18, 10))
fig_hrf_var.suptitle(f'{ROI_NAME}: HRF Variability Analysis (ROI vs Individual Voxels)',
                     fontsize=16, fontweight='bold')

# Top-left: Individual HRFs + ROI mean
ax1 = axes[0, 0]
# Plot subset of individual voxel HRFs (semi-transparent)
n_plot = min(100, n_voxels_selected)
plot_indices = np.random.choice(n_voxels_selected, n_plot, replace=False)
for idx in plot_indices:
    ax1.plot(times, HRF_selected[idx], 'gray', alpha=0.1, linewidth=0.5)

# Plot ROI mean HRF (bold)
ax1.plot(times, ROI_HRF, 'r-', linewidth=3, label='ROI Mean HRF', zorder=10)

# Plot ±1 std envelope
hrf_mean_per_time = np.mean(HRF_selected, axis=0)
hrf_std_per_time = np.std(HRF_selected, axis=0)
ax1.fill_between(times, hrf_mean_per_time - hrf_std_per_time,
                 hrf_mean_per_time + hrf_std_per_time,
                 alpha=0.3, color='blue', label='±1 SD')

ax1.axhline(y=0, color='black', linestyle=':', alpha=0.5)
ax1.set_xlabel('Time (seconds)')
ax1.set_ylabel('Response Amplitude')
ax1.set_title(f'Individual Voxel HRFs (n={n_plot} shown)')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Top-middle: Correlation distribution
ax2 = axes[0, 1]
ax2.hist(hrf_correlations, bins=30, edgecolor='black', alpha=0.7, color='steelblue')
ax2.axvline(np.mean(hrf_correlations), color='red', linestyle='--', linewidth=2,
            label=f'Mean = {np.mean(hrf_correlations):.3f}')
ax2.axvline(np.median(hrf_correlations), color='orange', linestyle='--', linewidth=2,
            label=f'Median = {np.median(hrf_correlations):.3f}')
ax2.set_xlabel('Correlation with ROI HRF')
ax2.set_ylabel('Number of voxels')
ax2.set_title('HRF Correlation Distribution')
ax2.legend()
ax2.grid(True, alpha=0.3)

# Top-right: RMSE distribution
ax3 = axes[0, 2]
ax3.hist(hrf_rmse, bins=30, edgecolor='black', alpha=0.7, color='coral')
ax3.axvline(np.mean(hrf_rmse), color='red', linestyle='--', linewidth=2,
            label=f'Mean = {np.mean(hrf_rmse):.3f}')
ax3.set_xlabel('RMSE from ROI HRF')
ax3.set_ylabel('Number of voxels')
ax3.set_title('HRF RMSE Distribution')
ax3.legend()
ax3.grid(True, alpha=0.3)

# Bottom-left: Per-timepoint variability
ax4 = axes[1, 0]
hrf_std_per_time = np.std(HRF_selected, axis=0)
hrf_sem_per_time = hrf_std_per_time / np.sqrt(n_voxels_selected)

ax4.errorbar(times, hrf_mean_per_time, yerr=hrf_std_per_time,
             fmt='o-', linewidth=2, capsize=5, capthick=2,
             label='Mean ± SD', color='steelblue')
ax4.plot(times, ROI_HRF, 'r--', linewidth=2, marker='s',
         label='ROI HRF', alpha=0.7)
ax4.axhline(y=0, color='black', linestyle=':', alpha=0.5)
ax4.set_xlabel('Time (seconds)')
ax4.set_ylabel('Response Amplitude')
ax4.set_title('HRF Variability Per Timepoint')
ax4.legend()
ax4.grid(True, alpha=0.3)

# Bottom-middle: Correlation vs R²
# ax5 = axes[1, 1]
# r2_selected = r2_voxel[selected_voxels_mask]
# scatter = ax5.scatter(r2_selected, hrf_correlations, c=hrf_rmse,
#                      cmap='viridis', alpha=0.6, s=20, edgecolors='black', linewidths=0.5)
# ax5.set_xlabel('R² (model fit)')
# ax5.set_ylabel('Correlation with ROI HRF')
# ax5.set_title('HRF Similarity vs Model Quality')
# ax5.grid(True, alpha=0.3)
# cbar = plt.colorbar(scatter, ax=ax5)
# cbar.set_label('RMSE', rotation=270, labelpad=15)

# # Add correlation coefficient
# overall_corr = np.corrcoef(r2_selected, hrf_correlations)[0, 1]
# ax5.text(0.05, 0.95, f'r = {overall_corr:.3f}',
#          transform=ax5.transAxes, va='top',
#          bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# Bottom-right: Best and worst fitting voxels
ax6 = axes[1, 2]

# Best 5 voxels (highest correlation)
best_indices = np.argsort(hrf_correlations)[-5:]
for idx in best_indices:
    ax6.plot(times, HRF_selected[idx], 'g-', alpha=0.5, linewidth=1.5)

# Worst 5 voxels (lowest correlation)
worst_indices = np.argsort(hrf_correlations)[:5]
for idx in worst_indices:
    ax6.plot(times, HRF_selected[idx], 'r-', alpha=0.5, linewidth=1.5)

# ROI HRF
ax6.plot(times, ROI_HRF, 'b-', linewidth=3, label='ROI HRF', zorder=10)

ax6.axhline(y=0, color='black', linestyle=':', alpha=0.5)
ax6.set_xlabel('Time (seconds)')
ax6.set_ylabel('Response Amplitude')
ax6.set_title('Best (green) vs Worst (red) Fitting Voxels')
ax6.legend()
ax6.grid(True, alpha=0.3)

# Add text annotations
best_mean_r = np.mean(hrf_correlations[best_indices])
worst_mean_r = np.mean(hrf_correlations[worst_indices])
ax6.text(0.05, 0.95, f'Best 5: r = {best_mean_r:.3f}\nWorst 5: r = {worst_mean_r:.3f}',
         transform=ax6.transAxes, va='top', fontsize=9,
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.tight_layout()
plt.savefig(fig_dir + 'hrf_variability_analysis.png', dpi=300, bbox_inches='tight')
plt.close()

print(f"  Saved: {fig_dir + 'hrf_variability_analysis.png'}")
print()
sys.stdout.flush()

# ============================================================================
# Step 4: 2nd-level GLM (Amplitude Estimation per Run)
# ============================================================================

print(f"[6/9] Step 4: 2nd-level GLM for amplitude estimation")
print(f"  Design: 16 columns [8 colors ⊗ HRF, 8 colors ⊗ HRF']")
sys.stdout.flush()

# Storage: (n_runs, n_colors, n_voxels_selected)
amplitudes_raw = np.zeros((N_RUNS, N_COLORS, n_voxels_selected))

# NORMALIZE_LEVEL-dependent data preparation:
#   'none' or '1st_only': Use ORIGINAL data (scale mismatch if 1st_only)
#   'both': Use NORMALIZED data (consistent with 1st-level)

if NORMALIZE_LEVEL == 'both':
    print(f"  2nd-level Normalization: BOTH levels (E1: consistent scale)")
    print(f"    Using same normalization as 1st-level (mean/std from all runs)")
else:
    if NORMALIZE_LEVEL == '1st_only':
        print(f"  2nd-level Normalization: NONE (original code, scale mismatch)")
    else:
        print(f"  2nd-level Normalization: NONE (E2: all original)")
    print(f"    Using ORIGINAL data")
print()

for run_idx in range(N_RUNS):
    print(f"  Processing run {run_idx + 1}/{N_RUNS}...")

    # Get functional data for this run (selected voxels only)
    y_run = all_func_data[run_idx][:, selected_voxels_mask]  # (n_scans, n_voxels_selected)
    n_scans = y_run.shape[0]

    # Apply normalization if NORMALIZE_LEVEL == 'both'
    if NORMALIZE_LEVEL == 'both':
        # Use same mean/std as 1st-level (consistent scale)
        y_run_normalized = np.zeros_like(y_run)
        for voxel_idx in range(n_voxels_selected):
            mean = voxel_norm_mean_selected[voxel_idx]
            std = voxel_norm_std_selected[voxel_idx]
            if std > 1e-10:
                y_run_normalized[:, voxel_idx] = (y_run[:, voxel_idx] - mean) / std
            else:
                y_run_normalized[:, voxel_idx] = y_run[:, voxel_idx]
        y_run_for_amplitude = y_run_normalized

        if run_idx == 0:
            print(f"    Applied 1st-level normalization to run {run_idx+1}")
            print(f"      y_run range (normalized): [{np.min(y_run_normalized):.2f}, {np.max(y_run_normalized):.2f}]")
    else:
        # Use original data
        y_run_for_amplitude = y_run

    # Build 2nd-level design matrix
    X_2nd = build_2nd_level_design_matrix(events_list[run_idx], n_scans, TR,
                                          ROI_HRF, ROI_HRF_deriv,
                                          add_intercept=ADD_2ND_LEVEL_INTERCEPT)

    # QC: Validate 2nd-level intercept implementation (first run only)
    if run_idx == 0 and ADD_2ND_LEVEL_INTERCEPT:
        print(f"\n  ✅ 2nd-level GLM QC (--2nd-level-intercept enabled):")
        print(f"     Design matrix shape:  {X_2nd.shape} (expected: {n_scans} × 17)")

        # Check intercept column exists and is constant 1.0
        intercept_col = X_2nd[:, -1]
        is_constant = np.allclose(intercept_col, intercept_col[0])
        is_ones = np.allclose(intercept_col[0], 1.0)

        if is_constant and is_ones:
            print(f"     ✅ PASS: Intercept column verified (last column = 1.0)")
        else:
            print(f"     ❌ FAIL: Intercept column NOT constant 1.0!")
            print(f"        is_constant: {is_constant}, is_ones: {is_ones}")
            print(f"        Column values: min={np.min(intercept_col):.3f}, max={np.max(intercept_col):.3f}")

        # Check design matrix conditioning
        cond_number = np.linalg.cond(X_2nd)
        print(f"     Condition number:     {cond_number:.2f} (lower is better)")

        if cond_number < 30:
            print(f"     ✅ Design matrix well-conditioned")
        else:
            print(f"     ⚠️  High condition number (may have collinearity issues)")
        print()

    # Estimate amplitudes per voxel: β = pinv(X) @ y
    X_pinv = np.linalg.pinv(X_2nd)
    betas = X_pinv @ y_run_for_amplitude

    # Extract first 8 betas (HRF regressors only, discard derivative betas)
    amplitudes_raw[run_idx] = betas[:N_COLORS, :]

print(f"  Amplitude array shape: {amplitudes_raw.shape} (runs, colors, voxels)")
print()
sys.stdout.flush()

# ============================================================================
# Step 5: Z-score Normalization
# ============================================================================

print(f"[7/9] Step 5: Z-score normalization (per voxel, per run)")
sys.stdout.flush()

# Create backup before filtering (for fallback if all voxels filtered)
amplitudes_raw_backup = amplitudes_raw.copy()
if len(hrf_correlations) > 0:
    hrf_correlations_backup = hrf_correlations.copy()
    hrf_rmse_backup = hrf_rmse.copy()
    hrf_nrmse_backup = hrf_nrmse.copy()

# Z-score: (runs, colors, voxels) → normalize across colors for each run-voxel pair
amplitudes_z = np.zeros_like(amplitudes_raw)

# First pass: identify problematic voxels (zero variance or NaN)
problematic_voxels = set()
for run_idx in range(N_RUNS):
    for voxel_idx in range(n_voxels_selected):
        amp = amplitudes_raw[run_idx, :, voxel_idx]

        # Check for NaN or zero variance
        if np.any(np.isnan(amp)) or np.std(amp) == 0:
            problematic_voxels.add(voxel_idx)

# Report problematic voxels
if len(problematic_voxels) > 0:
    print(f"  Problematic voxels (zero variance or NaN): {len(problematic_voxels)}/{n_voxels_selected}")

# Second pass: compute z-scores only for valid voxels
for run_idx in range(N_RUNS):
    for voxel_idx in range(n_voxels_selected):
        if voxel_idx not in problematic_voxels:
            amp = amplitudes_raw[run_idx, :, voxel_idx]
            amplitudes_z[run_idx, :, voxel_idx] = zscore(amp)

# Create mask for valid voxels
valid_voxels_mask = np.ones(n_voxels_selected, dtype=bool)
valid_voxels_mask[list(problematic_voxels)] = False
n_valid_voxels = np.sum(valid_voxels_mask)

# Filter to keep only valid voxels
amplitudes_raw = amplitudes_raw[:, :, valid_voxels_mask]
amplitudes_z = amplitudes_z[:, :, valid_voxels_mask]

# Note: HRF arrays (hrf_correlations, hrf_rmse, hrf_nrmse) were already filtered
# for NaN values at lines 1169-1172, so they don't need additional filtering here.
# They are used only for summary statistics reporting.

n_voxels_selected = n_valid_voxels

print(f"  Valid voxels after Z-score filtering: {n_voxels_selected}")
print(f"  Z-scored amplitudes shape: {amplitudes_z.shape}")

# Safety check: ensure we have voxels left
# If all voxels filtered, use raw amplitudes as fallback
if n_voxels_selected == 0:
    print(f"  ⚠️  WARNING: All voxels were filtered out (zero variance/NaN)")
    print(f"     Using FALLBACK: proceeding with raw amplitudes (no z-scoring)")
    print(f"     This may indicate issues with GLM fitting or data quality")

    # Restore original data
    amplitudes_raw = amplitudes_raw_backup  # Need to create backup earlier
    amplitudes_z = amplitudes_raw.copy()  # Use raw as "z-scored"
    n_voxels_selected = amplitudes_raw.shape[2]

    # Restore HRF arrays if they exist
    if 'hrf_correlations_backup' in locals():
        hrf_correlations = hrf_correlations_backup
        hrf_rmse = hrf_rmse_backup
        hrf_nrmse = hrf_nrmse_backup

    print(f"     Restored {n_voxels_selected} voxels for analysis")

print()
sys.stdout.flush()

# ============================================================================
# Enhanced Amplitude SNR Analysis
# ============================================================================

print(f"  === Amplitude SNR Analysis ===")
print(f"  Evaluating signal quality of color amplitudes...")

# Compute SNR metrics for amplitudes

print(f"1. Signal-to-Noise Ratio (SNR) per voxel per run")
print(f"   SNR = mean(signal) / std(noise)")
print(f"   For each voxel: signal = amplitude variation across colors")
print(f"                   noise = residual from 2nd-level GLM")

print(f"2. Effect size (Cohen's d) for color discrimination")
print(f"   How well do colors separate in amplitude space?")

print(f"3. Reliability across runs")
print(f"   Correlation of amplitude patterns between runs")

### Average amplitude across voxels in not needed here, focus on voxel-wise stats ###
# print(f"\n  1. Raw Amplitude Statistics:")
# print(f"     Mean amplitude (across all): {np.mean(amplitudes_raw):.4f}")
# print(f"     Std amplitude:  {np.std(amplitudes_raw):.4f}")
# print(f"     Min amplitude:  {np.min(amplitudes_raw):.4f}")
# print(f"     Max amplitude:  {np.max(amplitudes_raw):.4f}")

# Per-run statistics
# print(f"\n  2. Per-Run Amplitude Variability:")
# for run_idx in range(N_RUNS):
#     run_mean = np.mean(amplitudes_raw[run_idx])
#     run_std = np.std(amplitudes_raw[run_idx])
#     run_snr = run_mean / (run_std + 1e-8)
#     print(f"     Run {run_idx+1}: mean={run_mean:7.4f}, std={run_std:.4f}, SNR={run_snr:.4f}")

# # Per-color statistics
# print(f"\n  3. Per-Color Amplitude Statistics:")
# for color_idx in range(N_COLORS):
#     color_mean = np.mean(amplitudes_raw[:, color_idx, :])
#     color_std = np.std(amplitudes_raw[:, color_idx, :])
#     print(f"     Color {color_idx+1}: mean={color_mean:7.4f}, std={color_std:.4f}")

# # Z-scored amplitude statistics
# print(f"\n  4. Z-Scored Amplitude Statistics:")
# print(f"     Mean (should be ~0): {np.mean(amplitudes_z):.6f}")
# print(f"     Std (should be ~1):  {np.std(amplitudes_z):.6f}")

# Voxel-wise SNR (across colors)
# For each voxel, compute SNR = std(mean_amplitude_per_color) / mean(std_amplitude_per_color_across_runs)
voxel_snr = np.zeros(n_voxels_selected)

for voxel_idx in range(n_voxels_selected):
    # Mean amplitude per color (across runs)
    mean_per_color = np.mean(amplitudes_raw[:, :, voxel_idx], axis=0)  # (8,)

    # Std amplitude per color (across runs)
    std_per_color = np.std(amplitudes_raw[:, :, voxel_idx], axis=0)    # (8,)

    # Signal = variability across colors
    signal = np.std(mean_per_color)

    # Noise = average within-color variability
    noise = np.mean(std_per_color)

    voxel_snr[voxel_idx] = signal / (noise + 1e-8)

print(f"\n  1. Voxel-wise SNR (color discrimination):")
print(f"     Mean:   {np.mean(voxel_snr):.4f}")
print(f"     Median: {np.median(voxel_snr):.4f}")
print(f"     Std:    {np.std(voxel_snr):.4f}")
print(f"     Min:    {np.min(voxel_snr):.4f}")
print(f"     Max:    {np.max(voxel_snr):.4f}")

# High SNR voxels
high_snr = np.sum(voxel_snr > 1.0)
very_high_snr = np.sum(voxel_snr > 2.0)

print(f"\n     Voxels with SNR > 1.0: {high_snr}/{n_voxels_selected} ({100*high_snr/n_voxels_selected:.1f}%)")
print(f"     Voxels with SNR > 2.0: {very_high_snr}/{n_voxels_selected} ({100*very_high_snr/n_voxels_selected:.1f}%)")

# Run-to-run reliability (correlation of amplitude patterns)
print(f"\n  2. Run-to-Run Reliability:")

run_correlations = []
for i in range(N_RUNS):
    for j in range(i+1, N_RUNS):
        # Flatten amplitudes for correlation
        amp_i = amplitudes_raw[i].flatten()  # (8 × n_voxels,)
        amp_j = amplitudes_raw[j].flatten()

        corr = np.corrcoef(amp_i, amp_j)[0, 1]
        run_correlations.append(corr)

run_correlations = np.array(run_correlations)

print(f"     Mean correlation: {np.mean(run_correlations):.4f}")
print(f"     Min correlation:  {np.min(run_correlations):.4f}")
print(f"     Max correlation:  {np.max(run_correlations):.4f}")

if np.mean(run_correlations) > 0.7:
    print(f"  ✅ High run-to-run reliability (r = {np.mean(run_correlations):.3f})")
elif np.mean(run_correlations) > 0.5:
    print(f"  ⚠️  Moderate run-to-run reliability (r = {np.mean(run_correlations):.3f})")
else:
    print(f"  🚨 Low run-to-run reliability (r = {np.mean(run_correlations):.3f})")

print()
sys.stdout.flush()

# Visualize Amplitude SNR
fig_snr, axes = plt.subplots(2, 2, figsize=(18, 10))
fig_snr.suptitle(f'{ROI_NAME}: Amplitude SNR Analysis', fontsize=16, fontweight='bold')

# # Top-left: Amplitude distribution (raw)
# ax1 = axes[0, 0]
# ax1.hist(amplitudes_raw.flatten(), bins=50, edgecolor='black', alpha=0.7, color='steelblue')
# ax1.axvline(0, color='red', linestyle='--', linewidth=2, label='Zero')
# ax1.axvline(np.mean(amplitudes_raw), color='orange', linestyle='--', linewidth=2,
#             label=f'Mean = {np.mean(amplitudes_raw):.3f}')
# ax1.set_xlabel('Raw Amplitude')
# ax1.set_ylabel('Frequency')
# ax1.set_title('Raw Amplitude Distribution')
# ax1.legend()
# ax1.grid(True, alpha=0.3)

# # Top-middle: Amplitude distribution (z-scored)
# ax2 = axes[0, 1]
# ax2.hist(amplitudes_z.flatten(), bins=50, edgecolor='black', alpha=0.7, color='coral')
# ax2.axvline(0, color='red', linestyle='--', linewidth=2, label='Zero')
# ax2.set_xlabel('Z-Scored Amplitude')
# ax2.set_ylabel('Frequency')
# ax2.set_title('Z-Scored Amplitude Distribution')
# ax2.legend()
# ax2.grid(True, alpha=0.3)

# # Add Gaussian overlay
# from scipy.stats import norm
# x = np.linspace(-4, 4, 100)
# y = norm.pdf(x, 0, 1)
# y_scaled = y * len(amplitudes_z.flatten()) * (x[1] - x[0]) * 12  # Scale to histogram
# ax2.plot(x, y_scaled, 'r-', linewidth=2, label='N(0,1)', alpha=0.7)

# Top-right: Voxel SNR distribution
ax1 = axes[0, 0]
ax1.hist(voxel_snr, bins=30, edgecolor='black', alpha=0.7, color='green')
ax1.axvline(np.mean(voxel_snr), color='red', linestyle='--', linewidth=2,
            label=f'Mean = {np.mean(voxel_snr):.3f}')
ax1.axvline(np.median(voxel_snr), color='orange', linestyle='--', linewidth=2,
            label=f'Median = {np.median(voxel_snr):.3f}')
ax1.axvline(1.0, color='black', linestyle=':', linewidth=2, label='SNR = 1.0')
ax1.set_xlabel('SNR (color discrimination)')
ax1.set_ylabel('Number of voxels')
ax1.set_title('Voxel-wise SNR Distribution')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Bottom-left: Per-color amplitude (mean ± SEM across runs and voxels)
ax2 = axes[1, 0]
color_means = np.mean(amplitudes_raw, axis=(0, 2))  # (8,)
color_sems = np.std(amplitudes_raw, axis=(0, 2)) / np.sqrt(N_RUNS * n_voxels_selected)

colors_x = np.arange(1, N_COLORS + 1)
ax2.bar(colors_x, color_means, yerr=color_sems, capsize=5,
        edgecolor='black', alpha=0.7, color='steelblue')
ax2.axhline(0, color='black', linestyle='-', linewidth=1)
ax2.set_xlabel('Color Index')
ax2.set_ylabel('Mean Amplitude')
ax2.set_title('Mean Amplitude Per Color (±SEM)')
ax2.set_xticks(colors_x)
ax2.grid(True, alpha=0.3, axis='y')

# Bottom-middle: Run-to-run correlation matrix
ax3 = axes[0, 1]
corr_matrix = np.zeros((N_RUNS, N_RUNS))

for i in range(N_RUNS):
    for j in range(N_RUNS):
        amp_i = amplitudes_raw[i].flatten()
        amp_j = amplitudes_raw[j].flatten()
        corr_matrix[i, j] = np.corrcoef(amp_i, amp_j)[0, 1]

im = ax3.imshow(corr_matrix, cmap='RdBu_r', vmin=0, vmax=1, aspect='auto')
ax3.set_xticks(range(N_RUNS))
ax3.set_yticks(range(N_RUNS))
ax3.set_xticklabels([f'R{i+1}' for i in range(N_RUNS)])
ax3.set_yticklabels([f'R{i+1}' for i in range(N_RUNS)])
ax3.set_title(f'Run-to-Run Amplitude Correlation\n(Mean = {np.mean(run_correlations):.3f})')
plt.colorbar(im, ax=ax3, label='Correlation')

# Annotate cells
for i in range(N_RUNS):
    for j in range(N_RUNS):
        text = ax3.text(j, i, f'{corr_matrix[i, j]:.2f}',
                       ha="center", va="center",
                       color="white" if corr_matrix[i, j] > 0.5 else "black",
                       fontsize=9)

# Bottom-right: SNR vs R² (quality check)
# ax4 = axes[1, 1]
# r2_selected = r2_voxel[selected_voxels_mask]
# scatter = ax4.scatter(r2_selected, voxel_snr, c=hrf_correlations,
#                      cmap='viridis', alpha=0.6, s=20, edgecolors='black', linewidths=0.5)
# ax4.set_xlabel('R² (HRF fit quality)')
# ax4.set_ylabel('SNR (color discrimination)')
# ax4.set_title('Amplitude SNR vs HRF Quality (Unnecessary Check)')
# ax4.grid(True, alpha=0.3)
# cbar = plt.colorbar(scatter, ax=ax4)
# cbar.set_label('HRF Correlation', rotation=270, labelpad=15)

# # Add correlation
# snr_r2_corr = np.corrcoef(r2_selected, voxel_snr)[0, 1]
# ax4.text(0.05, 0.95, f'r = {snr_r2_corr:.3f}',
#          transform=ax4.transAxes, va='top',
#          bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.tight_layout()
plt.savefig(fig_dir + 'amplitude_snr_analysis.png', dpi=300, bbox_inches='tight')
plt.close()

print(f"  Saved: {fig_dir + 'amplitude_snr_analysis.png'}")
print()
sys.stdout.flush()

# ============================================================================
# Step 6: Classification with Leave-One-Run-Out CV
# ============================================================================

print(f"[8/9] Classification with leave-one-run-out CV")
if USE_PCA:
    print(f"  Using PCA: {N_PCA_COMPONENTS} components")
sys.stdout.flush()

classification_results = []

for test_run in range(N_RUNS):
    train_runs = [r for r in range(N_RUNS) if r != test_run]

    # Prepare training data: (n_train_samples, n_voxels_selected)
    X_train = amplitudes_z[train_runs].reshape(-1, n_voxels_selected)
    y_train = np.tile(np.arange(N_COLORS), len(train_runs))

    X_test = amplitudes_z[test_run]  # (8, n_voxels_selected)
    y_test = np.arange(N_COLORS)

    # Standardize
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Optional PCA
    if USE_PCA:
        # Ensure n_components doesn't exceed available dimensions
        n_samples, n_features = X_train_scaled.shape
        max_components = min(n_samples - 1, n_features - 1)
        n_components_actual = min(N_PCA_COMPONENTS, max_components)

        if n_components_actual < N_PCA_COMPONENTS:
            print(f"  WARNING: Reducing PCA components from {N_PCA_COMPONENTS} to {n_components_actual}")
            print(f"           (n_samples={n_samples}, n_features={n_features})")

        pca = PCA(n_components=n_components_actual)
        X_train_final = pca.fit_transform(X_train_scaled)
        X_test_final = pca.transform(X_test_scaled)
    else:
        X_train_final = X_train_scaled
        X_test_final = X_test_scaled

    # Classify
    y_pred = diag_linear_predict(X_train_final, y_train, X_test_final)
    acc = (y_pred == y_test).mean()

    classification_results.append({
        'test_run': test_run + 1,
        'accuracy': acc,
        'y_true': y_test,
        'y_pred': y_pred
    })

    print(f"  Test run {test_run+1}: {acc:.3f} ({acc*100:.1f}%)")

mean_classification_acc = np.mean([r['accuracy'] for r in classification_results])
print()
print(f"Mean classification accuracy: {mean_classification_acc:.3f} ({mean_classification_acc*100:.1f}%)")
print(f"Baseline (chance): {1/N_COLORS:.3f} ({100/N_COLORS:.1f}%)")
print()
sys.stdout.flush()

# Visualization: Classification Confusion Matrix
print("Generating classification confusion matrix...")
fig, ax = plt.subplots(figsize=(10, 8))

# Create confusion matrix
conf_matrix = np.zeros((N_COLORS, N_COLORS), dtype=int)
for r in classification_results:
    for true_idx, pred_idx in zip(r['y_true'], r['y_pred']):
        conf_matrix[true_idx, pred_idx] += 1

# Plot as heatmap
im = ax.imshow(conf_matrix, cmap='Blues', aspect='auto')

# Add text annotations
for i in range(N_COLORS):
    for j in range(N_COLORS):
        count = conf_matrix[i, j]
        color = 'white' if count > conf_matrix.max()/2 else 'black'
        text = ax.text(j, i, str(count), ha="center", va="center", color=color, fontsize=12, fontweight='bold')

# Labels and formatting
ax.set_xticks(np.arange(N_COLORS))
ax.set_yticks(np.arange(N_COLORS))
ax.set_xticklabels([f'c{i+1}' for i in range(N_COLORS)])
ax.set_yticklabels([f'c{i+1}' for i in range(N_COLORS)])
ax.set_xlabel('Predicted Color', fontsize=12, fontweight='bold')
ax.set_ylabel('True Color', fontsize=12, fontweight='bold')
ax.set_title(f'{ROI_NAME}: Classification Confusion Matrix (BH2009)\nAccuracy: {mean_classification_acc*100:.1f}%',
             fontsize=14, fontweight='bold')

# Add colorbar
cbar = plt.colorbar(im, ax=ax)
cbar.set_label('Count', rotation=270, labelpad=20, fontsize=10)

plt.tight_layout()
confusion_plot_path = fig_dir + f"{ROI_NAME}_confusion_matrix.png"
plt.savefig(confusion_plot_path, dpi=150, bbox_inches='tight')
plt.close()
print(f"  Saved: {confusion_plot_path}")
sys.stdout.flush()

# ============================================================================
# Step 7: Forward Model for Reconstruction
# ============================================================================

print(f"[9/9] Reconstruction with B&H forward model")
sys.stdout.flush()

# Create 6-channel basis functions (half-wave rectified squared sinusoids)
def create_basis_functions(n_channels=6):
    """Create 6 idealized color channels"""
    hues = np.linspace(0, 360, n_channels, endpoint=False)
    basis = np.zeros((360, n_channels))

    for i, center_hue in enumerate(hues):
        for h in range(360):
            # Circular distance
            dist = np.abs(h - center_hue)
            if dist > 180:
                dist = 360 - dist

            # Half-wave rectified cosine, squared
            response = np.cos(np.deg2rad(dist))
            if response > 0:
                basis[h, i] = response ** 2
            else:
                basis[h, i] = 0

    return basis

basis_functions = create_basis_functions(n_channels=6)

# Get channel outputs for each color
def hue_to_channels(hue_deg):
    """Convert hue (0-360) to 6 channel outputs"""
    hue_idx = int(np.round(hue_deg)) % 360
    return basis_functions[hue_idx]

# Reconstruction: leave-one-run-out
reconstruction_results = []

for test_run in range(N_RUNS):
    train_runs = [r for r in range(N_RUNS) if r != test_run]

    # Prepare data
    X_train = amplitudes_z[train_runs].reshape(-1, n_voxels_selected)
    y_train = np.tile(np.arange(N_COLORS), len(train_runs))

    X_test = amplitudes_z[test_run]
    y_test = np.arange(N_COLORS)

    # Standardize
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Optional PCA
    if USE_PCA:
        # Ensure n_components doesn't exceed available dimensions
        n_samples, n_features = X_train_scaled.shape
        max_components = min(n_samples - 1, n_features - 1)
        n_components_actual = min(N_PCA_COMPONENTS, max_components)

        if n_components_actual < N_PCA_COMPONENTS:
            print(f"  WARNING: Reducing PCA components from {N_PCA_COMPONENTS} to {n_components_actual}")
            print(f"           (n_samples={n_samples}, n_features={n_features})")

        pca = PCA(n_components=n_components_actual)
        X_train_final = pca.fit_transform(X_train_scaled)
        X_test_final = pca.transform(X_test_scaled)
    else:
        X_train_final = X_train_scaled
        X_test_final = X_test_scaled

    # Train forward model: B = W × C
    C_train = []
    for color_idx in y_train:
        color_name = f'color_{color_idx+1}'
        hue_deg = LABEL2HUE_DEG[color_name]
        channels = hue_to_channels(hue_deg)
        C_train.append(channels)
    C_train = np.array(C_train).T  # (6, n_train)

    # Estimate weights: W = B × C^T × (C × C^T)^-1
    W = X_train_final.T @ C_train.T @ np.linalg.inv(C_train @ C_train.T)

    # Test: estimate channels from test data
    C_test_est = np.linalg.pinv(W.T @ W) @ W.T @ X_test_final.T  # (6, n_test)

    # Reconstruct hues
    reconstructed_hues = []
    true_hues = []

    for test_idx, color_idx in enumerate(y_test):
        # Estimated channels
        estimated_channels = C_test_est[:, test_idx]

        # Find best matching hue (0-360)
        correlations = []
        for h in range(360):
            template_channels = basis_functions[h]
            corr = np.corrcoef(estimated_channels, template_channels)[0, 1]
            correlations.append(corr)

        correlations = np.array(correlations)
        reconstructed_hue = np.argmax(correlations)

        # True hue
        color_name = f'color_{color_idx+1}'
        true_hue = LABEL2HUE_DEG[color_name]

        reconstructed_hues.append(reconstructed_hue)
        true_hues.append(true_hue)

    # Calculate reconstruction error
    errors = circular_diff_deg(np.array(reconstructed_hues), np.array(true_hues))
    mean_error = errors.mean()

    reconstruction_results.append({
        'test_run': test_run + 1,
        'mean_error': mean_error,
        'reconstructed_hues': reconstructed_hues,
        'true_hues': true_hues,
        'errors': errors
    })

    print(f"  Test run {test_run+1}: Mean error = {mean_error:.1f}°")

mean_reconstruction_error = np.mean([r['mean_error'] for r in reconstruction_results])
print()
print(f"Mean reconstruction error: {mean_reconstruction_error:.1f}°")
print(f"Chance level (expected): 90.0° (uniform circular distribution)")
print()
sys.stdout.flush()

# Visualization: Circular Color Space
print("Generating circular color space visualization...")
fig = plt.figure(figsize=(14, 6))

# Left: Training colors reconstruction
ax1 = fig.add_subplot(1, 2, 1, projection='polar')
ax1.set_theta_zero_location("E")        # 0° at right (middle-right)
ax1.set_theta_direction(1)              # Anticlockwise positive (counterclockwise)
ax1.set_rticks([])                      # Hide radial ticks
ax1.grid(alpha=0.25)

rng = np.random.default_rng(42)
r_center = 1.0
r_pred_base = 0.85

# Plot true colors at border and predictions inside
for color_idx in range(N_COLORS):
    color_name = f'color_{color_idx + 1}'
    true_hue = LABEL2HUE_DEG[color_name]
    true_rgb = get_stimulus_color_rgb(color_name)  # Use actual stimulus color

    # True color at border (large, solid)
    ax1.scatter([np.deg2rad(true_hue)], [r_center], s=110,
               color=true_rgb, edgecolor='k', linewidths=0.8, zorder=4)

    # All predictions for this color (position=predicted angle, color=TRUE stimulus color)
    for result in reconstruction_results:
        pred_hue = result['reconstructed_hues'][color_idx]

        # Jitter radius slightly to avoid overlap
        r_jit = r_pred_base + rng.uniform(-0.03, 0.03)
        ax1.scatter([np.deg2rad(pred_hue)], [r_jit], s=28,
                   color=true_rgb, alpha=0.65, zorder=3)

ax1.set_ylim([0, 1.1])
ax1.set_title(f'Training Colors\nMean error: {mean_reconstruction_error:.1f}°', fontsize=12, fontweight='bold')

# Right: Show legend and summary
ax2 = fig.add_subplot(1, 2, 2)
ax2.axis('off')

# Add legend
from matplotlib.lines import Line2D
legend_elems = [
    Line2D([0],[0], marker='o', color='w', markerfacecolor='gray', markeredgecolor='k',
           label='True hue (stimulus)', markersize=10),
    Line2D([0],[0], marker='o', color='w', markerfacecolor='gray', alpha=0.65,
           label='Predictions (position=angle, color=truth)', markersize=6),
]
ax2.legend(handles=legend_elems, loc='center', fontsize=12, frameon=False)

# Add text summary
summary_text = f"""
BH2009 Original Pipeline

Classification Accuracy: {mean_classification_acc*100:.1f}%
Reconstruction Error: {mean_reconstruction_error:.1f}°
Chance Level: 90.0°

Voxels: {n_voxels_selected} selected
PCA Components: {N_PCA_COMPONENTS if USE_PCA else 'None'}
"""
ax2.text(0.5, 0.3, summary_text, transform=ax2.transAxes,
         fontsize=11, verticalalignment='center', horizontalalignment='center',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

plt.suptitle(f'{ROI_NAME}: Circular Color Space (Reconstruction accuracy visualization)', fontsize=14, fontweight='bold')
plt.tight_layout()
circular_plot_path = fig_dir + f"{ROI_NAME}_circular_color_space.png"
plt.savefig(circular_plot_path, dpi=150, bbox_inches='tight')
plt.close()
print(f"  Saved: {circular_plot_path}")
sys.stdout.flush()

# ============================================================================
# Save Results
# ============================================================================

print(f"Saving results to: {output_dir}")

# Summary with enhanced metrics
results_summary = {
    # Metadata
    'timestamp': timestamp,
    'dataset': DATASET,
    'config': {
        'smooth_fwhm': SMOOTH_FWHM,
        'highpass_hz': HIGHPASS_HZ,
        'motion_type': MOTION_TYPE,
        'compcor_n': COMPCOR_N,
        'drift_model': DRIFT_MODEL,
        'standardize': STANDARDIZE,
        'normalize_level': NORMALIZE_LEVEL  # FACTORIAL EXPERIMENT
    },

    # Basic info
    'subject': SUBJECT_ID,
    'roi': ROI_NAME,
    'use_pca': USE_PCA,
    'n_components': N_PCA_COMPONENTS if USE_PCA else None,
    'fir_delays': len(FIR_DELAYS),

    # Voxel statistics
    'n_voxels_total': int(n_voxels_total),
    'n_voxels_selected': int(n_voxels_selected),
    'voxel_selection_pct': float(100 * n_voxels_selected / n_voxels_total),

    # R² statistics
    'r2_threshold': float(r2_threshold),
    'r2_mean': float(r2_mean),
    'r2_median': float(r2_median),
    'r2_std': float(r2_std),
    'r2_min': float(r2_min),
    'r2_max': float(r2_max),

    # HRF statistics
    'peak_delay': int(np.argmax(np.abs(ROI_HRF))),
    'peak_delay_seconds': float(np.argmax(np.abs(ROI_HRF)) * TR),

    # HRF variability
    'hrf_correlation_mean': float(np.mean(hrf_correlations)),
    'hrf_correlation_median': float(np.median(hrf_correlations)),
    'hrf_correlation_std': float(np.std(hrf_correlations)),
    'hrf_rmse_mean': float(np.mean(hrf_rmse)),
    'hrf_voxels_high_corr_pct': float(100 * high_corr / n_voxels_selected),

    # Amplitude SNR
    'amplitude_mean_raw': float(np.mean(amplitudes_raw)),
    'amplitude_std_raw': float(np.std(amplitudes_raw)),
    'voxel_snr_mean': float(np.mean(voxel_snr)),
    'voxel_snr_median': float(np.median(voxel_snr)),
    'voxel_snr_std': float(np.std(voxel_snr)),
    'voxels_snr_gt_1_pct': float(100 * high_snr / n_voxels_selected),
    'voxels_snr_gt_2_pct': float(100 * very_high_snr / n_voxels_selected),

    # Run-to-run reliability
    'run_correlation_mean': float(np.mean(run_correlations)),
    'run_correlation_min': float(np.min(run_correlations)),
    'run_correlation_max': float(np.max(run_correlations)),

    # Performance metrics
    'classification_accuracy': float(mean_classification_acc),
    'reconstruction_error': float(mean_reconstruction_error),
}

# Save summary as results.json (main results file)
import json
with open(f"{output_dir}/results.json", 'w') as f:
    json.dump(results_summary, f, indent=2)

# Also save as analysis_summary.json for backward compatibility
with open(f"{output_dir}/analysis_summary.json", 'w') as f:
    json.dump(results_summary, f, indent=2)

# Save ROI HRF
np.save(f"{output_dir}/roi_hrf.npy", ROI_HRF)
np.save(f"{output_dir}/roi_hrf_deriv.npy", ROI_HRF_deriv)

# Save voxel selection info
np.save(f"{output_dir}/selected_voxels_mask.npy", selected_voxels_mask)
np.save(f"{output_dir}/r2_voxel.npy", r2_voxel)

# Save HRF variability metrics
np.save(f"{output_dir}/hrf_correlations.npy", hrf_correlations)
np.save(f"{output_dir}/hrf_rmse.npy", hrf_rmse)

# Save amplitudes
np.save(f"{output_dir}/amplitudes_raw.npy", amplitudes_raw)
np.save(f"{output_dir}/amplitudes_z.npy", amplitudes_z)

# Save SNR metrics
np.save(f"{output_dir}/voxel_snr.npy", voxel_snr)

# Save voxel coordinates (for grid resampling verification)
# Extract indices of selected voxels
selected_voxels_indices = np.where(selected_voxels_mask)[0]

# Get mask image (resampled if grid_resample=yes)
mask_for_coords = masker.mask_img_

# Extract MNI coordinates
voxel_coords, grid_indices = extract_voxel_coordinates(mask_for_coords, selected_voxels_indices)
np.save(f"{output_dir}/voxel_coords.npy", voxel_coords)
np.save(f"{output_dir}/grid_index.npy", grid_indices)

# Save reference mask if grid resampling was used
if GRID_RESAMPLE == 'yes':
    nib.save(mask_for_coords, f"{output_dir}/roi_mask_ref.nii.gz")

# Save QC metrics including grid resampling info
qc_metrics = {
    'settings': {
        'grid_resample': GRID_RESAMPLE,
        'highpass': HIGHPASS_HZ,
        'motion': MOTION_TYPE,
        'drift': DRIFT_MODEL,
        'smooth_fwhm': SMOOTH_FWHM,
        'normalize_level': NORMALIZE_LEVEL,
        'add_2nd_level_intercept': ADD_2ND_LEVEL_INTERCEPT
    },
    'voxel_stats': {
        'n_voxels_selected': int(n_voxels_selected),
        'n_voxels_total': int(masker.mask_img_.get_fdata().sum()),
        'selection_rate': float(n_voxels_selected / masker.mask_img_.get_fdata().sum())
    },
    'tsnr': {
        'mean': float(np.mean(voxel_snr)),
        'median': float(np.median(voxel_snr)),
        'std': float(np.std(voxel_snr))
    }
}

if GRID_RESAMPLE == 'yes':
    qc_metrics['grid_resampling'] = {
        'reference_shape': list(reference_shape),
        'reference_affine_diag': list(np.diag(reference_affine)[:3])
    }

with open(f"{output_dir}/qc.json", 'w') as f:
    json.dump(qc_metrics, f, indent=2)

# Save classification results
classification_df = pd.DataFrame([{
    'test_run': r['test_run'],
    'accuracy': r['accuracy']
} for r in classification_results])
classification_df.to_csv(f"{output_dir}/classification_results.csv", index=False)

# Save reconstruction results
reconstruction_df = pd.DataFrame([{
    'test_run': r['test_run'],
    'mean_error': r['mean_error'],
    'median_error': np.median(r['errors']),
    'hit_rate_30': np.mean(np.array(r['errors']) <= 30) * 100,
    'hit_rate_45': np.mean(np.array(r['errors']) <= 45) * 100
} for r in reconstruction_results])
reconstruction_df.to_csv(f"{output_dir}/reconstruction_results.csv", index=False)

print()
print("="*70)
print("Analysis Complete!")
print("="*70)
print(f"\nKey Results:")
print(f"  - SNR (mean): {np.mean(voxel_snr):.3f}")
print(f"  - Classification: {mean_classification_acc:.1%}")
print(f"  - Reconstruction: {mean_reconstruction_error:.1f}°")
print()
sys.stdout.flush()
