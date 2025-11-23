#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fir_reconstruction_BH2009_config26.py
----------------------------------
BH2009 pipeline with Config 26 preprocessing from grid search optimization

PREPROCESSING (Config 26 - Best from grid search):
- Spatial smoothing: 8mm FWHM Gaussian kernel
- Motion confound regression: 6 parameters (3 translation + 3 rotation)
- NO high-pass filtering (found to be detrimental)
- Drift modeling: Polynomial (constant + linear) in design matrix

GRID SEARCH RESULTS:
Config 26 achieved:
- Best config: smooth=8mm + motion_6, NO high-pass

DIFFERENCES FROM ORIGINAL BH2009:
1. Spatial smoothing applied (8mm FWHM)
2. Motion confound regression using 6 parameters
3. NO high-pass filtering (removed based on grid search findings)
4. Drift regressors in FIR design matrix

Usage:
    python fir_reconstruction_BH2009_config26.py --roi V1 --subject P01

Created: 2025-01-22
Based on: fir_reconstruction_BH2009.py + grid_search_preprocessing.py Config 26
"""

import sys
import os
import argparse
import numpy as np
import pandas as pd
import nibabel as nib
from pathlib import Path
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

# ============================================================================
# Configuration
# ============================================================================

# Config 26 Preprocessing Parameters
SMOOTHING_FWHM = 8  # mm - From grid search Config 26
USE_MOTION_CONFOUNDS = True  # 6 parameters
USE_HIGH_PASS = False  # Grid search showed this is DETRIMENTAL
DRIFT_MODEL = 'polynomial'  # constant + linear in design matrix

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

def load_motion_confounds(confounds_path):
    """
    Load motion confounds (6 parameters: 3 translation + 3 rotation)
    From fMRIPrep confounds TSV file
    """
    confounds_df = pd.read_csv(confounds_path, sep='\t')

    # Extract 6 motion parameters
    motion_cols = ['trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z']

    # Check if columns exist
    missing_cols = [col for col in motion_cols if col not in confounds_df.columns]
    if missing_cols:
        print(f"    ⚠️  WARNING: Missing motion columns: {missing_cols}")
        print(f"    Available columns: {confounds_df.columns.tolist()}")
        return None

    motion_confounds = confounds_df[motion_cols].values

    # Handle NaN values (fill with 0)
    if np.any(np.isnan(motion_confounds)):
        print(f"    ⚠️  WARNING: NaN values in motion confounds, filling with 0")
        motion_confounds = np.nan_to_num(motion_confounds, nan=0.0)

    return motion_confounds

def regress_confounds(data, confounds):
    """
    Regress out confounds from data using OLS

    Parameters:
    -----------
    data : ndarray, shape (n_scans, n_voxels)
        Functional data
    confounds : ndarray, shape (n_scans, n_confounds)
        Confound regressors

    Returns:
    --------
    data_clean : ndarray, shape (n_scans, n_voxels)
        Cleaned data
    """
    # Add constant term
    X = np.hstack([confounds, np.ones((confounds.shape[0], 1))])

    # Estimate betas: beta = pinv(X) @ data
    betas = np.linalg.pinv(X) @ data

    # Predict confound signal
    confound_signal = X @ betas

    # Remove confound signal
    data_clean = data - confound_signal

    return data_clean

def build_fir_design_matrix(onsets, n_scans, tr, fir_delays, run_idx=None, n_runs=None):
    """
    Build FIR design matrix with drift regressors (Config 26 style)

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
    run_idx : int, optional
        Run index (0-based). If provided, creates per-run drift regressors
    n_runs : int, optional
        Total number of runs. Required if run_idx is provided

    Returns:
    --------
    X : ndarray
        FIR design matrix with drift regressors
    """
    n_delays = len(fir_delays)

    # FIR regressors: each onsets with delays
    X_fir = np.zeros((n_scans, n_delays))
    for onset in onsets:
        onset_tr = int(np.round(onset / tr))
        for i, delay in enumerate(fir_delays):
            tr_idx = onset_tr + delay
            if 0 <= tr_idx < n_scans:
                X_fir[tr_idx, i] = 1.0

    # Drift regressors (polynomial: constant + linear)
    if DRIFT_MODEL == 'polynomial':
        if run_idx is not None and n_runs is not None:
            # Per-run drift regressors
            drift_cols = np.zeros((n_scans, 2 * n_runs))

            # This run's linear drift column
            linear_col_idx = run_idx * 2
            drift_cols[:, linear_col_idx] = np.linspace(-1, 1, n_scans)

            # This run's constant column
            const_col_idx = run_idx * 2 + 1
            drift_cols[:, const_col_idx] = 1.0

            X = np.hstack([X_fir, drift_cols])
        else:
            # Global drift (backward compatibility)
            linear_drift = np.linspace(-1, 1, n_scans).reshape(-1, 1)
            constant = np.ones((n_scans, 1))
            X = np.hstack([X_fir, linear_drift, constant])
    else:
        # No drift regressors
        X = X_fir

    return X

def build_2nd_level_design_matrix(events, n_scans, tr, roi_hrf, roi_hrf_deriv):
    """
    Build 2nd-level GLM design matrix with HRF and derivative regressors
    Following B&H (2009) exactly: 16 columns, NO drift regressors

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

    Returns:
    --------
    X : ndarray, shape (n_scans, 16)
        Design matrix [color_1⊗h, ..., color_8⊗h, color_1⊗h', ..., color_8⊗h']
    """
    n_colors = 8
    X = np.zeros((n_scans, 2 * n_colors))  # 16 columns

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

    return X

def compute_r2(y_true, y_pred):
    """Compute R² (coefficient of determination)"""
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)

    if ss_tot == 0:
        return 0.0

    r2 = 1 - (ss_res / ss_tot)

    if np.isnan(r2) or np.isinf(r2):
        return -np.inf

    return r2

# ============================================================================
# Parse Arguments
# ============================================================================

def parse_args():
    parser = argparse.ArgumentParser(description='B&H 2009 with Config 26 preprocessing')
    parser.add_argument('--subject', type=str, default='P01',
                        help='Subject ID (P01 for pilot, 01-04 for test subjects)')
    parser.add_argument('--roi', type=str, default='V1',
                        help='ROI name (e.g., V1, V2, V3, V4, hV4)')
    parser.add_argument('--timestamp', type=str, default=None,
                        help='Timestamp for output directory (default: auto-generated)')
    parser.add_argument('--use-pca', action='store_true',
                        help='Use PCA dimensionality reduction')
    parser.add_argument('--n-components', type=int, default=6,
                        help='Number of PCA components (only if --use-pca)')
    parser.add_argument('--output-dir', type=str, default=None,
                        help='Output directory (default: derivatives/BH2009_config26/timestamp/)')
    return parser.parse_args()

args = parse_args()

SUBJECT_ID = args.subject
ROI_NAME = args.roi
USE_PCA = args.use_pca
N_PCA_COMPONENTS = args.n_components

# Determine pilot vs test
IS_PILOT = (SUBJECT_ID == 'P01')
LABEL2HUE_DEG = LABEL2HUE_DEG_PILOT if IS_PILOT else LABEL2HUE_DEG_TEST

# ============================================================================
# Path Configuration
# ============================================================================

FMRIPREP_BASE = "/storage/connectome/haba6030/fmriprep_out"
EVENT_DIR = "/storage/connectome/haba6030/colorBlind_dataOct"

if SUBJECT_ID == 'P01':
    FMRIPREP_DIR = f"{FMRIPREP_BASE}/pilot/sub-01"
    FILE_PREFIX = "sub-01"
    DERIVATIVE_PREFIX = "sub-01"
    EVENTS_DIR = f"{EVENT_DIR}/pilot/sub-01/func"
else:
    FMRIPREP_DIR = f"{FMRIPREP_BASE}/sub-{SUBJECT_ID}"
    FILE_PREFIX = f"sub-{SUBJECT_ID}"
    DERIVATIVE_PREFIX = f"sub-{SUBJECT_ID}"
    EVENTS_DIR = f"{EVENT_DIR}/sub-{SUBJECT_ID}/func"

# ============================================================================
# Setup Output Directory
# ============================================================================

from datetime import datetime

if args.timestamp:
    timestamp = args.timestamp
    print(f"Using provided timestamp: {timestamp}")
else:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"Generated new timestamp: {timestamp}")

if args.output_dir:
    output_dir = Path(args.output_dir)
else:
    if SUBJECT_ID == 'P01':
        output_dir = Path(f"derivatives/BH2009_config26/pilot/{timestamp}_{DERIVATIVE_PREFIX}_{ROI_NAME}")
    else:
        output_dir = Path(f"derivatives/BH2009_config26/{timestamp}_{DERIVATIVE_PREFIX}_{ROI_NAME}")
output_dir.mkdir(parents=True, exist_ok=True)

fig_dir = output_dir / 'figures'
fig_dir.mkdir(exist_ok=True)

print("="*70)
print("B&H (2009) Pipeline with Config 26 Preprocessing")
print("="*70)
print(f"Subject: {SUBJECT_ID}")
print(f"ROI: {ROI_NAME}")
print()
print("Config 26 Preprocessing:")
print(f"  - Spatial smoothing: {SMOOTHING_FWHM}mm FWHM")
print(f"  - Motion confounds: {'6 parameters (trans_x/y/z, rot_x/y/z)' if USE_MOTION_CONFOUNDS else 'None'}")
print(f"  - High-pass filtering: {'Yes' if USE_HIGH_PASS else 'No (DETRIMENTAL per grid search)'}")
print(f"  - Drift modeling: {DRIFT_MODEL} in design matrix")
print()
print(f"FIR delays: {len(FIR_DELAYS)} (0-{len(FIR_DELAYS)-1}, matching B&H 2009)")
print(f"Use PCA: {USE_PCA}")
if USE_PCA:
    print(f"PCA components: {N_PCA_COMPONENTS}")
print(f"Output directory: {output_dir}")
print()
sys.stdout.flush()

# ============================================================================
# Load ROI Mask
# ============================================================================

print(f"[1/9] Loading ROI mask")
sys.stdout.flush()

# Determine ROI path based on subject
if SUBJECT_ID == 'P01':
    roi_path = f"derivatives/pilot/{DERIVATIVE_PREFIX}/roi_pipeline_20251111_010954/{ROI_NAME}_mask_thr50_intnearest_binTrue_masknone_gmTrue_subjFalse.nii.gz"
else:
    roi_path = f"derivatives/{DERIVATIVE_PREFIX}/roi_pipeline/{ROI_NAME}_mask_thr50_intnearest_binTrue_masknone_gmTrue_subjFalse.nii.gz"

print(f"  ROI mask path: {roi_path}")

if not os.path.exists(roi_path):
    print(f"\n❌ ERROR: ROI mask file not found!")
    print(f"  Expected path: {roi_path}")
    sys.exit(1)

roi_img = nib.load(roi_path)
roi_data = roi_img.get_fdata()

print(f"  ROI: {ROI_NAME}")
print(f"  ROI mask shape: {roi_img.shape}")
print(f"  ROI value range: [{roi_data.min():.4f}, {roi_data.max():.4f}]")

# Count voxels
n_voxels_any = np.sum(roi_data > 0)
print(f"  Voxels > 0: {n_voxels_any}")

if n_voxels_any == 0:
    print(f"\n❌ ERROR: ROI mask is completely empty!")
    sys.exit(1)

# Create binary mask
roi_mask = roi_data > 0
n_voxels_total = n_voxels_any

# Initialize masker
masker = NiftiMasker(mask_img=roi_img, standardize=False)
masker.fit()

print()
sys.stdout.flush()

# ============================================================================
# Load Functional Data with Config 26 Preprocessing
# ============================================================================

print(f"[2/9] Loading functional data with Config 26 preprocessing ({N_RUNS} runs)")
sys.stdout.flush()

func_imgs = []
events_list = []
all_func_data = []

for run in range(1, N_RUNS + 1):
    # Functional image
    func_path = f"{FMRIPREP_DIR}/func/{FILE_PREFIX}_task-rsvp_run-{run}_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz"

    if not os.path.exists(func_path):
        print(f"ERROR: Functional image not found: {func_path}")
        sys.exit(1)

    func_img = nib.load(func_path)

    if VOLS_TO_DROP > 0:
        func_img = nimg.index_img(func_img, slice(VOLS_TO_DROP, None))

    # === CONFIG 26 PREPROCESSING: Spatial Smoothing ===
    if SMOOTHING_FWHM > 0:
        print(f"  Run {run}: Applying {SMOOTHING_FWHM}mm smoothing...")
        func_img = nimg.smooth_img(func_img, fwhm=SMOOTHING_FWHM)

    func_imgs.append(func_img)

    # Extract data for this run (masked)
    func_data = masker.transform(func_img)  # (n_scans, n_voxels)

    if func_data.shape[1] == 0:
        print(f"\n❌ ERROR: Masker extracted 0 voxels from run {run}!")
        sys.exit(1)

    # === CONFIG 26 PREPROCESSING: Motion Confound Regression ===
    if USE_MOTION_CONFOUNDS:
        confounds_path = f"{FMRIPREP_DIR}/func/{FILE_PREFIX}_task-rsvp_run-{run}_desc-confounds_timeseries.tsv"

        if os.path.exists(confounds_path):
            # Load confounds (first VOLS_TO_DROP rows already removed by index_img)
            confounds = load_motion_confounds(confounds_path)

            if confounds is not None:
                # Drop first VOLS_TO_DROP rows from confounds
                if VOLS_TO_DROP > 0:
                    confounds = confounds[VOLS_TO_DROP:, :]

                # Verify dimensions match
                if confounds.shape[0] != func_data.shape[0]:
                    print(f"    ⚠️  WARNING: Confounds shape mismatch!")
                    print(f"       func_data: {func_data.shape[0]} scans")
                    print(f"       confounds: {confounds.shape[0]} scans")
                    print(f"       Skipping confound regression for run {run}")
                else:
                    print(f"  Run {run}: Regressing 6 motion parameters...")
                    func_data = regress_confounds(func_data, confounds)
        else:
            print(f"    ⚠️  WARNING: Confounds file not found: {confounds_path}")

    all_func_data.append(func_data)

    # Events
    events_path = f"{EVENTS_DIR}/{FILE_PREFIX}_task-rsvp_run-{run}_events.tsv"

    if not os.path.exists(events_path):
        print(f"ERROR: Events file not found: {events_path}")
        sys.exit(1)

    events = pd.read_csv(events_path, sep='\t')

    # Adjust onset times for dropped volumes
    if VOLS_TO_DROP > 0:
        events['onset'] = events['onset'] - (VOLS_TO_DROP * TR)
        events = events[events['onset'] >= 0].reset_index(drop=True)

    events_list.append(events)

    # Summary
    func_duration = func_data.shape[0] * TR
    print(f"  Run {run}: {func_data.shape[0]} scans = {func_duration:.1f}s | Voxels: {func_data.shape[1]}")
    print(f"    Preprocessing: smooth={SMOOTHING_FWHM}mm, motion_confounds={'yes' if USE_MOTION_CONFOUNDS else 'no'}")

print(f"\n  Total: {len(func_imgs)} runs loaded with Config 26 preprocessing")

# Final voxel count verification
n_voxels_extracted = all_func_data[0].shape[1]
print(f"  Voxels extracted: {n_voxels_extracted}")

print()
sys.stdout.flush()

# ============================================================================
# Step 1: Voxel-wise FIR HRF Estimation
# ============================================================================

print(f"[3/9] Step 1: Voxel-wise FIR HRF estimation")
print(f"  Estimating HRF for {n_voxels_extracted} voxels using pseudo-inverse")
sys.stdout.flush()

n_voxels_total = n_voxels_extracted

# ============================================================================
# Build Design Matrix ONCE (same for all voxels)
# ============================================================================
print(f"  Building design matrix...")
X_fir_all = []

for run_idx in range(N_RUNS):
    # CRITICAL FIX: Get COLOR onsets only (exclude blank)
    # Blank trials serve as implicit baseline (not modeled)
    events = events_list[run_idx]
    color_events = events[events['trial_type'].str.startswith('color_')]
    all_onsets = color_events['onset'].values

    # Build FIR design matrix for this run
    # CHANGED: Use global drift (like grid search) instead of per-run drift
    # Grid search showed similar results with global drift (simpler, fewer parameters)
    n_scans = all_func_data[run_idx].shape[0]
    X_fir = build_fir_design_matrix(all_onsets, n_scans, TR, FIR_DELAYS,
                                    run_idx=None, n_runs=None)  # Global drift
    X_fir_all.append(X_fir)

# Concatenate design matrices
X_fir_all = np.vstack(X_fir_all)
print(f"  Design matrix shape: {X_fir_all.shape}")
print()

# ============================================================================
# Voxel-wise HRF Estimation
# ============================================================================
HRF_voxel = np.zeros((n_voxels_total, len(FIR_DELAYS)))
r2_voxel = np.zeros(n_voxels_total)

for voxel_idx in range(n_voxels_total):
    # Concatenate data across all runs for this voxel
    y_voxel = []
    for run_idx in range(N_RUNS):
        y_run = all_func_data[run_idx][:, voxel_idx]
        y_voxel.append(y_run)
    y_voxel = np.concatenate(y_voxel)

    # Estimate HRF using pseudo-inverse with fallback
    try:
        beta_full = np.linalg.pinv(X_fir_all) @ y_voxel
    except np.linalg.LinAlgError:
        # Fallback to lstsq if SVD doesn't converge
        beta_full, _, _, _ = np.linalg.lstsq(X_fir_all, y_voxel, rcond=None)

    # Extract HRF (first 8 elements, excluding drift regressors)
    h_v = beta_full[:len(FIR_DELAYS)]
    HRF_voxel[voxel_idx] = h_v

    # Compute R²
    y_pred = X_fir_all @ beta_full
    r2_voxel[voxel_idx] = compute_r2(y_voxel, y_pred)

    if (voxel_idx + 1) % 100 == 0:
        print(f"  Processed {voxel_idx + 1}/{n_voxels_total} voxels", end='\r')

print(f"  Processed {n_voxels_total}/{n_voxels_total} voxels")

# Quality check: can each voxel's FIR explain original voxel HRF?
n_valid_hrfs = np.sum(~np.all(HRF_voxel == 0, axis=1))
n_valid_r2 = np.sum(~np.isinf(r2_voxel))

print(f"\n  Quality check:")
print(f"    Voxels with non-zero HRF: {n_valid_hrfs}/{n_voxels_total}")
print(f"    Voxels with valid R²: {n_valid_r2}/{n_voxels_total}")

if n_valid_r2 == 0:
    print(f"\n❌ ERROR: All voxels have invalid R²!")
    sys.exit(1)

print()

# R² statistics
print(f"  === R² Distribution : can each voxel's FIR explain original voxel HRF? ===")
r2_mean = np.mean(r2_voxel)
r2_median = np.median(r2_voxel)
r2_std = np.std(r2_voxel)

print(f"  Mean:   {r2_mean:.4f}")
print(f"  Median: {r2_median:.4f}")
print(f"  Std:    {r2_std:.4f}")
print()
sys.stdout.flush()

# ============================================================================
# Step 2: Voxel Selection (Top 50% by R²)
# ============================================================================

print(f"[4/9] Step 2: Voxel selection (top 50% by R²)")
sys.stdout.flush()

valid_r2_mask = ~(np.isnan(r2_voxel) | np.isinf(r2_voxel))
n_valid_r2 = np.sum(valid_r2_mask)

print(f"  Valid R² values: {n_valid_r2}/{n_voxels_total}")

if n_valid_r2 < 100:
    print(f"  ⚠️  WARNING: Very few valid voxels, using all")
    selected_voxels_mask = valid_r2_mask
    r2_threshold = np.min(r2_voxel[valid_r2_mask])
else:
    r2_threshold = np.median(r2_voxel[valid_r2_mask])
    selected_voxels_mask = (r2_voxel >= r2_threshold) & valid_r2_mask

n_voxels_selected = np.sum(selected_voxels_mask)

print(f"  R² threshold: {r2_threshold:.3f}")
print(f"  Selected voxels: {n_voxels_selected}/{n_voxels_total} ({100*n_voxels_selected/n_voxels_total:.1f}%)")
print()
sys.stdout.flush()

# ============================================================================
# Step 3: ROI Average HRF and Derivative
# ============================================================================

print(f"[5/9] Step 3: Computing ROI average HRF")
sys.stdout.flush()

# Average HRF across selected voxels
ROI_HRF = np.mean(HRF_voxel[selected_voxels_mask], axis=0)
ROI_HRF_deriv = np.gradient(ROI_HRF)

print(f"  ROI HRF shape: {ROI_HRF.shape}")
print(f"  Peak delay: {np.argmax(np.abs(ROI_HRF))} (time={np.argmax(np.abs(ROI_HRF))*TR:.1f}s)")
print()
sys.stdout.flush()

# HRF Variability Analysis: can ROI HRF represent individual voxel HRFs?
print(f"  === HRF Variability Analysis: can ROI HRF represent individual voxel HRFs? ===")

HRF_selected = HRF_voxel[selected_voxels_mask]
hrf_correlations = np.zeros(n_voxels_selected)

for i in range(n_voxels_selected):
    try:
        hrf_correlations[i] = np.corrcoef(HRF_selected[i], ROI_HRF)[0, 1]
    except:
        hrf_correlations[i] = np.nan

# Remove NaN
valid_mask = ~np.isnan(hrf_correlations)
hrf_correlations = hrf_correlations[valid_mask]

if len(hrf_correlations) > 0:
    print(f"  Correlation with ROI HRF:")
    print(f"    Mean: {np.mean(hrf_correlations):.4f}")
    print(f"    Median: {np.median(hrf_correlations):.4f}")
    print(f"    Std: {np.std(hrf_correlations):.4f}")

    high_corr = np.sum(hrf_correlations > 0.8)
    print(f"    Voxels with r > 0.8: {high_corr}/{n_voxels_selected} ({100*high_corr/n_voxels_selected:.1f}%)")

    if np.mean(hrf_correlations) > 0.85:
        print(f"  ✅ High HRF homogeneity > 0.85 (mean r = {np.mean(hrf_correlations):.3f})")
        print(f"     → Config 26 preprocessing successfully improved HRF consistency!")
    else:
        print(f"  ⚠️  Moderate HRF homogeneity < 0.85 (mean r = {np.mean(hrf_correlations):.3f})")

print()
sys.stdout.flush()

# ============================================================================
# Continue with 2nd-level GLM, Classification, and Reconstruction
# (Same as original BH2009 pipeline from line 1086 onwards)
# ============================================================================

print(f"[6/9] Step 4: 2nd-level GLM for amplitude estimation")
sys.stdout.flush()

amplitudes_raw = np.zeros((N_RUNS, N_COLORS, n_voxels_selected))

for run_idx in range(N_RUNS):
    y_run = all_func_data[run_idx][:, selected_voxels_mask]
    n_scans = y_run.shape[0]

    X_2nd = build_2nd_level_design_matrix(events_list[run_idx], n_scans, TR,
                                          ROI_HRF, ROI_HRF_deriv)

    X_pinv = np.linalg.pinv(X_2nd)
    betas = X_pinv @ y_run

    amplitudes_raw[run_idx] = betas[:N_COLORS, :]

print(f"  Amplitude array shape: {amplitudes_raw.shape}")
print()
sys.stdout.flush()

# ============================================================================
# Step 5: Z-score Normalization
# ============================================================================

print(f"[7/9] Step 5: Z-score normalization")
sys.stdout.flush()

amplitudes_z = np.zeros_like(amplitudes_raw)
n_nan_voxels = 0

for run_idx in range(N_RUNS):
    for voxel_idx in range(n_voxels_selected):
        amp = amplitudes_raw[run_idx, :, voxel_idx]

        if np.std(amp) == 0 or np.any(np.isnan(amp)):
            amplitudes_z[run_idx, :, voxel_idx] = 0
            n_nan_voxels += 1
        else:
            amplitudes_z[run_idx, :, voxel_idx] = zscore(amp)

print(f"  Z-scored amplitudes shape: {amplitudes_z.shape}")
if n_nan_voxels > 0:
    print(f"  ⚠️  {n_nan_voxels} run-voxel pairs had zero variance")

# Replace any remaining NaN
amplitudes_z = np.nan_to_num(amplitudes_z, nan=0.0)

print()
sys.stdout.flush()

# ============================================================================
# Step 6: Classification
# ============================================================================

print(f"[8/9] Classification with leave-one-run-out CV")
if USE_PCA:
    print(f"  Using PCA: {N_PCA_COMPONENTS} components")
sys.stdout.flush()

classification_results = []

for test_run in range(N_RUNS):
    train_runs = [r for r in range(N_RUNS) if r != test_run]

    X_train = amplitudes_z[train_runs].reshape(-1, n_voxels_selected)
    y_train = np.tile(np.arange(N_COLORS), len(train_runs))

    X_test = amplitudes_z[test_run]
    y_test = np.arange(N_COLORS)

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    if USE_PCA:
        pca = PCA(n_components=N_PCA_COMPONENTS)
        X_train_final = pca.fit_transform(X_train_scaled)
        X_test_final = pca.transform(X_test_scaled)
    else:
        X_train_final = X_train_scaled
        X_test_final = X_test_scaled

    y_pred = diag_linear_predict(X_train_final, y_train, X_test_final)
    acc = (y_pred == y_test).mean()

    classification_results.append({
        'test_run': test_run + 1,
        'accuracy': acc
    })

    print(f"  Test run {test_run+1}: {acc:.3f} ({acc*100:.1f}%)")

mean_classification_acc = np.mean([r['accuracy'] for r in classification_results])
print()
print(f"Mean classification accuracy: {mean_classification_acc:.3f} ({mean_classification_acc*100:.1f}%)")
print(f"Baseline (chance): {1/N_COLORS:.3f} ({100/N_COLORS:.1f}%)")
print()
sys.stdout.flush()

# ============================================================================
# Step 7: Reconstruction
# ============================================================================

print(f"[9/9] Reconstruction with B&H forward model")
sys.stdout.flush()

def create_basis_functions(n_channels=6):
    """Create 6 idealized color channels"""
    hues = np.linspace(0, 360, n_channels, endpoint=False)
    basis = np.zeros((360, n_channels))

    for i, center_hue in enumerate(hues):
        for h in range(360):
            dist = np.abs(h - center_hue)
            if dist > 180:
                dist = 360 - dist

            response = np.cos(np.deg2rad(dist))
            if response > 0:
                basis[h, i] = response ** 2
            else:
                basis[h, i] = 0

    return basis

basis_functions = create_basis_functions(n_channels=6)

def hue_to_channels(hue_deg):
    """Convert hue to 6 channel outputs"""
    hue_idx = int(np.round(hue_deg)) % 360
    return basis_functions[hue_idx]

reconstruction_results = []

for test_run in range(N_RUNS):
    train_runs = [r for r in range(N_RUNS) if r != test_run]

    X_train = amplitudes_z[train_runs].reshape(-1, n_voxels_selected)
    y_train = np.tile(np.arange(N_COLORS), len(train_runs))

    X_test = amplitudes_z[test_run]
    y_test = np.arange(N_COLORS)

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    if USE_PCA:
        pca = PCA(n_components=N_PCA_COMPONENTS)
        X_train_final = pca.fit_transform(X_train_scaled)
        X_test_final = pca.transform(X_test_scaled)
    else:
        X_train_final = X_train_scaled
        X_test_final = X_test_scaled

    C_train = []
    for color_idx in y_train:
        color_name = f'color_{color_idx+1}'
        hue_deg = LABEL2HUE_DEG[color_name]
        channels = hue_to_channels(hue_deg)
        C_train.append(channels)
    C_train = np.array(C_train).T

    W = X_train_final.T @ C_train.T @ np.linalg.inv(C_train @ C_train.T)
    C_test_est = np.linalg.pinv(W.T @ W) @ W.T @ X_test_final.T

    reconstructed_hues = []
    true_hues = []

    for test_idx, color_idx in enumerate(y_test):
        estimated_channels = C_test_est[:, test_idx]

        correlations = []
        for h in range(360):
            template_channels = basis_functions[h]
            corr = np.corrcoef(estimated_channels, template_channels)[0, 1]
            correlations.append(corr)

        correlations = np.array(correlations)
        reconstructed_hue = np.argmax(correlations)

        color_name = f'color_{color_idx+1}'
        true_hue = LABEL2HUE_DEG[color_name]

        reconstructed_hues.append(reconstructed_hue)
        true_hues.append(true_hue)

    errors = circular_diff_deg(np.array(reconstructed_hues), np.array(true_hues))
    mean_error = errors.mean()

    reconstruction_results.append({
        'test_run': test_run + 1,
        'mean_error': mean_error
    })

    print(f"  Test run {test_run+1}: Mean error = {mean_error:.1f}°")

mean_reconstruction_error = np.mean([r['mean_error'] for r in reconstruction_results])
print()
print(f"Mean reconstruction error: {mean_reconstruction_error:.1f}°")
print(f"Chance level: 90.0°")
print()
sys.stdout.flush()

# ============================================================================
# Save Results
# ============================================================================

print(f"Saving results to: {output_dir}")

# Run-to-run reliability
run_correlations = []
for i in range(N_RUNS):
    for j in range(i+1, N_RUNS):
        amp_i = amplitudes_raw[i].flatten()
        amp_j = amplitudes_raw[j].flatten()
        corr = np.corrcoef(amp_i, amp_j)[0, 1]
        run_correlations.append(corr)

run_correlations = np.array(run_correlations)

results_summary = {
    'subject': SUBJECT_ID,
    'roi': ROI_NAME,
    'preprocessing_config': 'Config 26',
    'smoothing_fwhm': SMOOTHING_FWHM,
    'motion_confounds': USE_MOTION_CONFOUNDS,
    'high_pass_filter': USE_HIGH_PASS,
    'drift_model': DRIFT_MODEL,

    'n_voxels_total': int(n_voxels_total),
    'n_voxels_selected': int(n_voxels_selected),

    'r2_mean': float(r2_mean),
    'r2_median': float(r2_median),

    'hrf_correlation_mean': float(np.mean(hrf_correlations)),
    'hrf_correlation_median': float(np.median(hrf_correlations)),

    'run_correlation_mean': float(np.mean(run_correlations)),

    'classification_accuracy': float(mean_classification_acc),
    'reconstruction_error': float(mean_reconstruction_error),
}

import json
with open(output_dir / 'analysis_summary.json', 'w') as f:
    json.dump(results_summary, f, indent=2)

np.save(output_dir / 'roi_hrf.npy', ROI_HRF)
np.save(output_dir / 'amplitudes_z.npy', amplitudes_z)

print()
print("="*70)
print("Analysis Complete!")
print("="*70)
print(f"\nKey Results:")
print(f"  - HRF homogeneity (mean r): {np.mean(hrf_correlations):.3f}")
print(f"  - Run-to-run reliability: {np.mean(run_correlations):.3f}")
print(f"  - Classification: {mean_classification_acc:.1%}")
print(f"  - Reconstruction: {mean_reconstruction_error:.1f}°")
print()

if np.mean(hrf_correlations) > 0.85:
    print("✅ Config 26 preprocessing achieved high HRF homogeneity!")
    print("   Grid search optimization successfully improved voxel consistency.")
else:
    print("⚠️  HRF homogeneity is moderate. Consider investigating further.")

print()
sys.stdout.flush()
