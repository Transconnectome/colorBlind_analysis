#!/usr/bin/env python3
"""
Comprehensive Preprocessing Grid Search for B&H (2009) Pipeline
================================================================

Tests all preprocessing combinations to find optimal settings for:
- Spatial SNR (smoothing)
- Temporal SNR (filtering, confounds)
- HRF quality (voxel normalization)
- Run-to-run reliability

Author: Claude + User
Date: 2025-11-20
"""

import os
import sys
import json
import time
import numpy as np
import pandas as pd
import nibabel as nib
from pathlib import Path
from nilearn import image as nimg
from nilearn.maskers import NiftiMasker
from nilearn.signal import clean
from nilearn.glm.first_level import make_first_level_design_matrix
from scipy.signal import detrend
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

SUBJECT_ID = '01'
ROI_NAME = 'V1'
N_RUNS = 6              # Number of functional runs
TR = 1.5                # Repetition time in seconds
VOLS_TO_DROP = 4        # Drop first 4 volumes for signal stabilization
FIR_DELAYS = np.arange(8)  # [0, 1, 2, 3, 4, 5, 6, 7] - 8 time points for HRF

# Paths
FMRIPREP_DIR = f"/storage/connectome/haba6030/fmriprep_out/sub-{SUBJECT_ID}"
EVENTS_DIR = f"/storage/connectome/haba6030/colorBlind_dataOct/sub-{SUBJECT_ID}/func"
ROI_PATH = f"derivatives/sub-{SUBJECT_ID}/roi_pipeline/{ROI_NAME}_mask_thr50_intnearest_binTrue_masknone_gmTrue_subjFalse.nii.gz"

# Output
OUTPUT_DIR = Path(f"derivatives/grid_search_{SUBJECT_ID}_{ROI_NAME}")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# GRID SEARCH PARAMETERS
# ============================================================================
# Total combinations: 3 × 3 × 2 × 2 = 36

GRID_PARAMS = {
    # Spatial smoothing with Gaussian kernel
    'smoothing_fwhm': [0, 6, 8],  # mm - Full Width at Half Maximum

    # Temporal filtering options
    'temporal_filter': [
        {'high_pass': None, 'drift_model': None},           # No filtering
        {'high_pass': None, 'drift_model': 'polynomial'},   # Polynomial detrending
        {'high_pass': 1/128, 'drift_model': None},          # High-pass at 128s (0.0078 Hz)
    ],

    # Motion confound regression
    'confounds': [None, 'motion_6'],  # None or 6-parameter motion

    # Voxel-wise HRF normalization
    'voxel_norm': [None, 'demean'],  # None or mean-centering
}


# ============================================================================
# FUNCTION 1: Generate all preprocessing configurations
# ============================================================================

def generate_configs():
    """
    Generate all parameter combinations

    Returns:
        configs: List of 36 dictionaries, each containing one configuration

    Example output:
        [
            {'id': 0, 'smoothing_fwhm': 0, 'high_pass': None, 'drift_model': None,
             'confounds': None, 'voxel_norm': None},
            {'id': 1, 'smoothing_fwhm': 0, 'high_pass': None, 'drift_model': None,
             'confounds': None, 'voxel_norm': 'demean'},
            ...
        ]
    """
    configs = []
    config_id = 0

    # Nested loops create all combinations (Cartesian product)
    for smooth in GRID_PARAMS['smoothing_fwhm']:
        for temp_filter in GRID_PARAMS['temporal_filter']:
            for confounds in GRID_PARAMS['confounds']:
                for voxel_norm in GRID_PARAMS['voxel_norm']:
                    # Create one configuration dictionary
                    configs.append({
                        'id': config_id,
                        'smoothing_fwhm': smooth,
                        'high_pass': temp_filter['high_pass'],
                        'drift_model': temp_filter['drift_model'],
                        'confounds': confounds,
                        'voxel_norm': voxel_norm,
                    })
                    config_id += 1

    return configs


# ============================================================================
# FUNCTION 2: Load and preprocess functional data
# ============================================================================

def load_and_preprocess_data(config):
    """
    Load and preprocess functional data according to configuration

    Args:
        config: Dictionary with preprocessing parameters
            - smoothing_fwhm: Spatial smoothing kernel size (mm)
            - high_pass: High-pass filter cutoff (Hz)
            - confounds: Type of confound regression ('motion_6' or None)
            - voxel_norm: Voxel normalization method ('demean' or None)

    Returns:
        all_func_data: List of 6 arrays, each (284 scans × n_voxels)
        all_events: List of 6 DataFrames with event timing
        masker: NiftiMasker object used for extraction

    Data flow:
        4D NIfTI (97×115×97×288)
          → Drop 4 volumes → (97×115×97×284)
          → Smoothing (optional) → (97×115×97×284)
          → Masker extraction → (284×n_voxels)
          → High-pass + confounds (optional) → (284×n_voxels)
    """
    print(f"  Loading data with config {config['id']}...")

    # ========================================================================
    # STEP 1: Load ROI mask
    # ========================================================================
    # ROI mask is a 3D binary/probabilistic image (97×115×97)
    # For V1, this contains ~481 voxels
    roi_img = nib.load(ROI_PATH)
    masker = NiftiMasker(mask_img=roi_img, standardize=False)
    masker.fit()  # Prepare masker for transformation

    all_func_data = []  # Will store (284, n_voxels) arrays for each run
    all_events = []     # Will store event DataFrames for each run

    # ========================================================================
    # STEP 2: Loop through 6 runs
    # ========================================================================
    for run in range(1, N_RUNS + 1):
        # --------------------------------------------------------------------
        # 2a. Load functional 4D image (X × Y × Z × Time)
        # --------------------------------------------------------------------
        func_path = f"{FMRIPREP_DIR}/func/sub-{SUBJECT_ID}_task-rsvp_run-{run}_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz"
        func_img = nib.load(func_path)
        # Shape: (97, 115, 97, 288) - includes 4 initial volumes to drop

        # --------------------------------------------------------------------
        # 2b. Drop initial volumes for signal stabilization
        # --------------------------------------------------------------------
        if VOLS_TO_DROP > 0:
            func_img = nimg.index_img(func_img, slice(VOLS_TO_DROP, None))
            # Shape: (97, 115, 97, 284) - first 4 volumes removed

        # --------------------------------------------------------------------
        # 2c. PREPROCESSING STEP 1: Spatial smoothing (optional)
        # --------------------------------------------------------------------
        # Gaussian kernel smoothing reduces spatial noise
        # FWHM = 6mm means kernel width at half maximum is 6mm
        if config['smoothing_fwhm'] > 0:
            func_img = nimg.smooth_img(func_img, fwhm=config['smoothing_fwhm'])
            # Shape: (97, 115, 97, 284) - spatially smoothed

        # --------------------------------------------------------------------
        # 2d. Extract voxel timeseries using ROI mask
        # --------------------------------------------------------------------
        # Convert 4D image to 2D matrix (time × voxels)
        func_data = masker.transform(func_img)
        # Shape: (284, 481) for V1 - 284 timepoints, 481 voxels in ROI

        # --------------------------------------------------------------------
        # 2e. PREPROCESSING STEP 2: Load motion confounds (optional)
        # --------------------------------------------------------------------
        confounds_mat = None
        if config['confounds'] == 'motion_6':
            # Load confounds file (contains motion params, physio, etc.)
            confounds_path = f"{FMRIPREP_DIR}/func/sub-{SUBJECT_ID}_task-rsvp_run-{run}_desc-confounds_timeseries.tsv"
            confounds_df = pd.read_csv(confounds_path, sep='\t')

            # Extract 6 motion parameters: 3 translations + 3 rotations
            motion_cols = ['trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z']
            confounds_mat = confounds_df[motion_cols].iloc[VOLS_TO_DROP:].values
            # Shape: (284, 6) - must match functional data timepoints

        # --------------------------------------------------------------------
        # 2f. PREPROCESSING STEP 3: Temporal filtering + confound regression
        # --------------------------------------------------------------------
        # nilearn.signal.clean() performs:
        #   1. Confound regression (if provided)
        #   2. High-pass filtering (if provided)
        if config['high_pass'] is not None or confounds_mat is not None:
            func_data = clean(
                func_data,              # Input: (284, 481)
                detrend=False,          # Don't use linear detrending
                standardize=False,      # Don't z-score
                high_pass=config['high_pass'],  # e.g., 1/128 Hz
                t_r=TR,                 # Needed for frequency conversion
                confounds=confounds_mat # Motion parameters to regress out
            )
            # Output: (284, 481) - cleaned timeseries

        all_func_data.append(func_data)

        # --------------------------------------------------------------------
        # 2g. Load event timing file
        # --------------------------------------------------------------------
        events_path = f"{EVENTS_DIR}/sub-{SUBJECT_ID}_task-rsvp_run-{run}_events.tsv"
        events = pd.read_csv(events_path, sep='\t')
        # Columns: onset, duration, trial_type (e.g., 'color_1', 'color_2', ...)

        # Adjust onset times to account for dropped volumes
        # If we dropped 4 volumes (6 seconds), subtract 6s from all onsets
        events['onset'] = events['onset'] - (VOLS_TO_DROP * TR)

        # Remove events that now occur before time 0
        events = events[events['onset'] >= 0].reset_index(drop=True)
        # Typically removes 1 event per run (the one that was during dropped volumes)

        all_events.append(events)

    return all_func_data, all_events, masker


# ============================================================================
# FUNCTION 3: Compute temporal SNR for each voxel
# ============================================================================

def compute_temporal_snr(func_data):
    """
    Compute temporal SNR for each voxel

    Args:
        func_data: Array (n_scans, n_voxels) - functional timeseries

    Returns:
        tsnr: Array (n_voxels,) - temporal SNR for each voxel

    Formula:
        tSNR = mean(timeseries) / std(detrended_timeseries)

    Interpretation:
        - tSNR > 50: Good quality
        - tSNR = 20-50: Moderate quality
        - tSNR < 20: Low quality (high noise)
    """
    n_scans, n_voxels = func_data.shape
    tsnr = np.zeros(n_voxels)

    for v in range(n_voxels):
        timeseries = func_data[:, v]  # (284,) - one voxel's timeseries

        # Remove linear trend to isolate noise
        detrended = detrend(timeseries)

        # tSNR = mean signal / noise standard deviation
        mean_signal = np.mean(timeseries)
        std_noise = np.std(detrended)

        if std_noise > 0:
            tsnr[v] = mean_signal / std_noise
        else:
            tsnr[v] = 0  # Avoid division by zero

    return tsnr


# ============================================================================
# FUNCTION 4: Build FIR design matrix for one run
# ============================================================================

def build_fir_design_matrix(events, n_scans, tr, fir_delays, drift_model=None):
    """
    Build FIR design matrix with optional drift regressors

    Args:
        events: DataFrame with columns ['onset', 'trial_type', 'duration']
                Example: onset=[5.9, 11.2, 16.8, ...] in seconds
        n_scans: Number of timepoints (e.g., 284)
        tr: Repetition time (1.5 seconds)
        fir_delays: Array of delays [0, 1, 2, 3, 4, 5, 6, 7] - TRs after event
        drift_model: 'polynomial' or None

    Returns:
        X: Design matrix array (n_scans, n_columns)
           - If drift_model=None: (284, 8) - 8 FIR columns
           - If drift_model='polynomial': (284, 10) - 8 FIR + constant + drift

    Design matrix structure:
        Columns: [fir_0, fir_1, fir_2, ..., fir_7, constant, drift_1]

        Each FIR column is a "stick function" = impulse at specific delay

        Example for one event at onset=5.9s:
            onset_tr = round(5.9 / 1.5) = 4

            TR    fir_0  fir_1  fir_2  ...  fir_7
            0       0      0      0           0
            1       0      0      0           0
            2       0      0      0           0
            3       0      0      0           0
            4       1      0      0           0    ← Event onset
            5       0      1      0           0    ← +1 TR (1.5s after)
            6       0      0      1           0    ← +2 TR (3.0s after)
            ...
            11      0      0      0           1    ← +7 TR (10.5s after)
    """
    # ========================================================================
    # STEP 1: Create paradigm dataframe for nilearn
    # ========================================================================
    all_onsets = events['onset'].values  # e.g., [5.9, 11.2, 16.8, ...]

    # nilearn expects specific format: trial_type, onset, duration
    paradigm = pd.DataFrame({
        'trial_type': ['stim'] * len(all_onsets),  # All events labeled 'stim'
        'onset': all_onsets,
        'duration': [0] * len(all_onsets)  # Impulse events (duration=0)
    })

    # Create frame times: [0, 1.5, 3.0, 4.5, ..., 424.5] seconds
    frame_times = np.arange(n_scans) * tr

    # ========================================================================
    # STEP 2: Use nilearn to create base design matrix
    # ========================================================================
    # This creates 'stim' column (which we'll replace) + drift columns
    X = make_first_level_design_matrix(
        frame_times=frame_times,
        events=paradigm,
        hrf_model=None,           # Don't convolve with HRF (we do FIR manually)
        drift_model=drift_model,  # 'polynomial' or None
        drift_order=1 if drift_model == 'polynomial' else None,
        high_pass=None            # Already applied in preprocessing
    )
    # Output columns: ['stim', 'constant', 'drift_1'] if drift_model='polynomial'
    # Output columns: ['stim'] if drift_model=None

    # ========================================================================
    # STEP 3: Build FIR regressors manually as stick functions
    # ========================================================================
    X_fir = np.zeros((n_scans, len(fir_delays)))  # (284, 8)

    for onset in all_onsets:  # For each event
        # Convert onset time to TR index
        onset_tr = int(np.round(onset / tr))  # e.g., 5.9s / 1.5 = 3.93 → 4

        # Create stick at each delay
        for i, delay in enumerate(fir_delays):  # delay = 0, 1, 2, ..., 7
            tr_idx = onset_tr + delay
            if 0 <= tr_idx < n_scans:  # Check bounds
                X_fir[tr_idx, i] = 1.0  # Set impulse

    # ========================================================================
    # STEP 4: Replace 'stim' column with FIR columns
    # ========================================================================
    # Before: X = ['stim', 'constant', 'drift_1']
    # After:  X = ['fir_0', 'fir_1', ..., 'fir_7', 'constant', 'drift_1']

    if 'stim' in X.columns:
        stim_idx = X.columns.get_loc('stim')
        X_before = X.iloc[:, :stim_idx]      # Columns before 'stim' (usually none)
        X_after = X.iloc[:, stim_idx+1:]     # Columns after 'stim' (drift regressors)
        X_fir_df = pd.DataFrame(X_fir, columns=[f'fir_{i}' for i in range(len(fir_delays))])
        X = pd.concat([X_before, X_fir_df, X_after], axis=1)
    else:
        # If no 'stim' column (shouldn't happen), just prepend FIR
        X_fir_df = pd.DataFrame(X_fir, columns=[f'fir_{i}' for i in range(len(fir_delays))])
        X = pd.concat([X_fir_df, X], axis=1)

    return X.values  # Convert DataFrame to numpy array


# ============================================================================
# FUNCTION 5: Estimate HRF for each voxel using multi-run FIR
# ============================================================================

def estimate_voxel_hrf(func_data_list, events_list, config):
    """
    Estimate HRF for each voxel using multi-run concatenated FIR deconvolution

    Args:
        func_data_list: List of 6 arrays, each (284, n_voxels)
        events_list: List of 6 DataFrames with event timing
        config: Dictionary with 'drift_model' and 'voxel_norm'

    Returns:
        HRF_voxels: Array (n_voxels, 8) - HRF at 8 delays for each voxel
        r2_voxels: Array (n_voxels,) - R² goodness of fit for each voxel

    Mathematical model:
        y_voxel(t) = Σ[delay] h_v[delay] × X_fir[t, delay] + noise

        Where:
            y_voxel: Observed timeseries (1704 timepoints across 6 runs)
            h_v: Voxel-specific HRF (8 values)
            X_fir: FIR design matrix (1704 × 8)

        Solution:
            h_v = pinv(X_fir) @ y_voxel

    Data flow:
        func_data_list: 6 × (284, 481)
          → Concatenate → (1704, 481)

        events_list: 6 DataFrames
          → Build design matrices → 6 × (284, 8 or 10)
          → Stack → (1704, 8 or 10)
          → Extract FIR columns → (1704, 8)

        For each voxel:
          y_voxel (1704,) and X_fir (1704, 8)
          → Solve h_v = pinv(X_fir) @ y_voxel
          → h_v (8,) - HRF at delays 0-7
    """
    n_voxels = func_data_list[0].shape[1]  # e.g., 481 for V1

    # ========================================================================
    # STEP 1: Concatenate all runs vertically (time axis)
    # ========================================================================
    # Stack functional data across runs
    y_all = np.vstack(func_data_list)
    # Shape: (1704, 481) = 6 runs × 284 scans
    # Each voxel now has 1704-timepoint timeseries

    n_scans_total = y_all.shape[0]  # 1704

    # ========================================================================
    # STEP 2: Build design matrix for each run separately
    # ========================================================================
    # CRITICAL: Each run's events must be processed in that run's time frame
    # We do NOT adjust onset times - they are already correct for each run

    X_all_list = []

    for run_idx in range(N_RUNS):  # 0 to 5
        events = events_list[run_idx].copy()
        # Events for this run only, with onset in 0-426s range

        # IMPORTANT: Don't adjust onset times!
        # Each run's events are already in that run's time frame (0-426s)
        # When we stack design matrices, the time axis aligns automatically

        n_scans_run = func_data_list[run_idx].shape[0]  # 284

        # Build design matrix for this run
        X_run = build_fir_design_matrix(events, n_scans_run, TR, FIR_DELAYS,
                                        config['drift_model'])
        # Shape: (284, 8) if no drift
        #        (284, 10) if polynomial drift [8 FIR + constant + drift]

        X_all_list.append(X_run)

    # Stack design matrices vertically
    X_all = np.vstack(X_all_list)
    # Shape: (1704, 8) or (1704, 10) depending on drift model

    # ========================================================================
    # STEP 3: Extract FIR columns only (discard drift regressors)
    # ========================================================================
    # We only want to estimate HRF from FIR regressors
    # Drift regressors help fitting but we don't use them for HRF
    n_fir = len(FIR_DELAYS)  # 8
    X_fir = X_all[:, :n_fir]  # (1704, 8) - first 8 columns only

    # ========================================================================
    # STEP 4: Estimate HRF for each voxel independently
    # ========================================================================
    HRF_voxels = np.zeros((n_voxels, n_fir))  # (481, 8)
    r2_voxels = np.zeros(n_voxels)            # (481,)

    for v in range(n_voxels):
        # Get this voxel's timeseries across all runs
        y_voxel = y_all[:, v]  # (1704,)

        # --------------------------------------------------------------------
        # Solve linear system: X_fir @ h_v = y_voxel
        # Using pseudo-inverse: h_v = pinv(X_fir) @ y_voxel
        # --------------------------------------------------------------------
        try:
            # Pseudo-inverse solution (SVD-based)
            h_v = np.linalg.pinv(X_fir) @ y_voxel  # (8,)
        except np.linalg.LinAlgError:
            # Fallback to least squares if SVD doesn't converge
            # This is more robust but slightly slower
            h_v, _, _, _ = np.linalg.lstsq(X_fir, y_voxel, rcond=None)

        HRF_voxels[v] = h_v

        # --------------------------------------------------------------------
        # Compute R² (goodness of fit)
        # --------------------------------------------------------------------
        # Predicted timeseries
        y_pred = X_fir @ h_v  # (1704,)

        # Sum of squared residuals
        ss_res = np.sum((y_voxel - y_pred)**2)

        # Total sum of squares
        ss_tot = np.sum((y_voxel - np.mean(y_voxel))**2)

        # R² = 1 - (residual variance / total variance)
        r2_voxels[v] = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        # R² = 1.0 means perfect fit
        # R² = 0.0 means no better than mean
        # R² < 0 means worse than mean (shouldn't happen with proper fitting)

    # ========================================================================
    # STEP 5: Optional voxel normalization
    # ========================================================================
    # This removes baseline differences between voxels
    # Helps when comparing HRF shapes across voxels

    if config['voxel_norm'] == 'demean':
        # Subtract mean across delays for each voxel
        # Before: voxel A = [-1.5, -6.8, -1.1, 0.07, 3.8, 4.6, 4.3, 2.2]
        # After:  voxel A = [0.52, -4.78, 0.92, 2.09, 5.82, 6.62, 6.32, 4.22]
        HRF_voxels = HRF_voxels - np.mean(HRF_voxels, axis=1, keepdims=True)

    elif config['voxel_norm'] == 'standardize':
        # Z-score normalization: (HRF - mean) / std
        mean = np.mean(HRF_voxels, axis=1, keepdims=True)
        std = np.std(HRF_voxels, axis=1, keepdims=True)
        HRF_voxels = (HRF_voxels - mean) / (std + 1e-10)  # Add epsilon to avoid div by 0

    return HRF_voxels, r2_voxels


# ============================================================================
# FUNCTION 6: Compute quality metrics
# ============================================================================

def compute_metrics(func_data_list, HRF_voxels, r2_voxels, config):
    """
    Compute all quality metrics for this preprocessing configuration

    Args:
        func_data_list: List of 6 arrays (284, n_voxels)
        HRF_voxels: Array (n_voxels, 8) - estimated HRF for each voxel
        r2_voxels: Array (n_voxels,) - R² for each voxel
        config: Dictionary with preprocessing settings

    Returns:
        metrics: Dictionary with quality metrics

    Key metrics:
        - r2_mean/median: How well FIR model fits data
        - hrf_variability: Mean correlation of voxel HRFs with ROI average
                          (GOAL: maximize this - want homogeneous HRFs)
        - hrf_representativeness: % of voxels with correlation > 0.8
        - temporal_snr_mean: Data quality metric
    """
    metrics = {}

    # ========================================================================
    # METRIC 1: R² statistics
    # ========================================================================
    # R² measures how well the FIR model explains the data
    r2_valid = r2_voxels[r2_voxels > 0]  # Remove any zeros
    metrics['r2_mean'] = float(np.mean(r2_valid))
    metrics['r2_median'] = float(np.median(r2_valid))
    metrics['r2_std'] = float(np.std(r2_valid))

    # ========================================================================
    # METRIC 2: Voxel selection (top 50% by R²)
    # ========================================================================
    # Select voxels with good model fit for HRF analysis
    r2_threshold = np.median(r2_voxels)  # Median as threshold
    selected_mask = r2_voxels >= r2_threshold  # Boolean mask
    n_selected = np.sum(selected_mask)
    metrics['n_voxels_selected'] = int(n_selected)

    # ========================================================================
    # METRIC 3: HRF variability (KEY METRIC)
    # ========================================================================
    # This is what we want to MAXIMIZE through preprocessing
    # High HRF variability means voxels have similar HRF shapes

    # Compute ROI average HRF from selected voxels
    ROI_HRF = np.mean(HRF_voxels[selected_mask], axis=0)  # (8,)
    # Example: [-1.5, -6.8, -1.1, 0.07, 3.8, 4.6, 4.3, 2.2]

    # Compute correlation of each voxel's HRF with ROI average
    hrf_corrs = []
    for v in np.where(selected_mask)[0]:  # Iterate over selected voxels
        voxel_hrf = HRF_voxels[v]  # (8,)

        # Pearson correlation between this voxel and ROI average
        r = np.corrcoef(voxel_hrf, ROI_HRF)[0, 1]

        if not np.isnan(r):  # Skip if correlation undefined
            hrf_corrs.append(r)

    # Mean correlation = HRF homogeneity
    metrics['hrf_variability'] = float(np.mean(hrf_corrs)) if hrf_corrs else 0.0
    # Goal: Close to 1.0 (all voxels have similar HRF)
    # Current problem: ~0.066 (voxels have very different HRFs)

    # Representativeness = fraction with high correlation
    metrics['hrf_representativeness'] = float(np.sum(np.array(hrf_corrs) > 0.8)) / len(hrf_corrs) if hrf_corrs else 0.0
    # Goal: Close to 1.0 (most voxels well-represented by ROI HRF)

    # ========================================================================
    # METRIC 4: Temporal SNR
    # ========================================================================
    # Measures data quality (signal-to-noise ratio in time)
    tsnr = compute_temporal_snr(func_data_list[0])  # Use first run
    metrics['temporal_snr_mean'] = float(np.mean(tsnr))
    metrics['temporal_snr_median'] = float(np.median(tsnr))
    metrics['temporal_snr_max'] = float(np.max(tsnr))

    # ========================================================================
    # Placeholder metrics (would need full pipeline)
    # ========================================================================
    metrics['spatial_snr_mean'] = 0.0
    metrics['spatial_snr_max'] = 0.0
    metrics['run_to_run_reliability'] = 0.0
    metrics['zero_variance_pct'] = 0.0

    return metrics


# ============================================================================
# FUNCTION 7: Run single configuration
# ============================================================================

def run_single_config(config):
    """
    Run complete analysis pipeline for one configuration

    Args:
        config: Dictionary with preprocessing parameters

    Returns:
        result: Dictionary with config + metrics (or error info)

    Pipeline:
        1. Load and preprocess data
        2. Estimate voxel HRFs
        3. Compute quality metrics
        4. Return results
    """
    print(f"\n{'='*80}")
    print(f"Config {config['id']:02d}/{len(generate_configs())-1}")
    print(f"{'='*80}")
    print(f"  Smoothing: {config['smoothing_fwhm']} mm")
    print(f"  High-pass: {config['high_pass']}")
    print(f"  Drift model: {config['drift_model']}")
    print(f"  Confounds: {config['confounds']}")
    print(f"  Voxel norm: {config['voxel_norm']}")

    start_time = time.time()

    try:
        # ====================================================================
        # STEP 1: Load and preprocess
        # ====================================================================
        func_data_list, events_list, masker = load_and_preprocess_data(config)
        # func_data_list: 6 × (284, 481)
        # events_list: 6 DataFrames

        # ====================================================================
        # STEP 2: Estimate HRF
        # ====================================================================
        print(f"  Estimating HRF...")
        HRF_voxels, r2_voxels = estimate_voxel_hrf(func_data_list, events_list, config)
        # HRF_voxels: (481, 8)
        # r2_voxels: (481,)

        # ====================================================================
        # STEP 3: Compute metrics
        # ====================================================================
        print(f"  Computing metrics...")
        metrics = compute_metrics(func_data_list, HRF_voxels, r2_voxels, config)

        # ====================================================================
        # Success!
        # ====================================================================
        elapsed = time.time() - start_time
        metrics['elapsed_time'] = elapsed
        metrics['status'] = 'success'

        print(f"  ✓ Completed in {elapsed:.1f}s")
        print(f"  R²: {metrics['r2_mean']:.4f}, tSNR: {metrics['temporal_snr_mean']:.1f}, HRF corr: {metrics['hrf_variability']:.3f}")

    except Exception as e:
        # ====================================================================
        # Error handling
        # ====================================================================
        import traceback
        print(f"  ✗ Failed: {str(e)}")
        print(f"  Full traceback:")
        traceback.print_exc()  # Print full error trace for debugging

        metrics = {
            'status': 'failed',
            'error': str(e),
            'traceback': traceback.format_exc(),
            'elapsed_time': time.time() - start_time
        }

    # Merge config and metrics into single result dictionary
    result = {**config, **metrics}

    return result


# ============================================================================
# FUNCTION 8: Main grid search loop
# ============================================================================

def main():
    """
    Main grid search loop

    Process:
        1. Generate 36 configurations
        2. Run each configuration
        3. Save results incrementally
        4. Find and save best configuration
    """
    print("="*80)
    print("COMPREHENSIVE PREPROCESSING GRID SEARCH")
    print("="*80)
    print(f"Subject: {SUBJECT_ID}")
    print(f"ROI: {ROI_NAME}")
    print(f"Total configurations: {len(generate_configs())}")
    print()

    # ========================================================================
    # STEP 1: Generate all configurations
    # ========================================================================
    configs = generate_configs()  # List of 36 config dictionaries
    results = []

    # ========================================================================
    # STEP 2: Loop through configurations
    # ========================================================================
    for config in configs:
        # Run complete pipeline for this config
        result = run_single_config(config)
        results.append(result)

        # Save results incrementally (in case of crash)
        results_df = pd.DataFrame(results)
        results_df.to_csv(OUTPUT_DIR / 'grid_search_results.csv', index=False)

    # ========================================================================
    # STEP 3: Final summary
    # ========================================================================
    print("\n" + "="*80)
    print("GRID SEARCH COMPLETE")
    print("="*80)

    results_df = pd.DataFrame(results)
    successful = results_df[results_df['status'] == 'success']

    if len(successful) > 0:
        # ====================================================================
        # Find best configuration by HRF variability
        # ====================================================================
        # Goal: Maximize hrf_variability (homogeneous HRF shapes)
        best_idx = successful['hrf_variability'].idxmax()
        best_config = successful.loc[best_idx]

        print("\nBest Configuration (by HRF correlation):")
        print(f"  Config ID: {best_config['id']}")
        print(f"  Smoothing: {best_config['smoothing_fwhm']} mm")
        print(f"  High-pass: {best_config['high_pass']}")
        print(f"  Drift model: {best_config['drift_model']}")
        print(f"  Confounds: {best_config['confounds']}")
        print(f"  Voxel norm: {best_config['voxel_norm']}")
        print(f"  Metrics:")
        print(f"    R²: {best_config['r2_mean']:.4f}")
        print(f"    tSNR: {best_config['temporal_snr_mean']:.1f}")
        print(f"    HRF correlation: {best_config['hrf_variability']:.3f}")

        # Save best configuration as JSON
        best_config_dict = best_config.to_dict()
        with open(OUTPUT_DIR / 'best_config.json', 'w') as f:
            json.dump(best_config_dict, f, indent=2)

    print(f"\nResults saved to: {OUTPUT_DIR}")
    print("="*80)


if __name__ == '__main__':
    main()
