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
import argparse
import numpy as np
import pandas as pd
import nibabel as nib
from pathlib import Path
from nilearn import image as nimg
from nilearn.maskers import NiftiMasker
from nilearn.signal import clean
from scipy.signal import detrend
import warnings
warnings.filterwarnings('ignore')

# Constants
N_RUNS = 6
TR = 1.5
VOLS_TO_DROP = 4
FIR_DELAYS = np.arange(8)

# Grid Search Parameters (36 combinations)
GRID_PARAMS = {
    'smoothing_fwhm': [0, 6, 8],  # mm
    'temporal_filter': [
        {'high_pass': None, 'drift_model': None},
        {'high_pass': None, 'drift_model': 'polynomial'},
        {'high_pass': 1/128, 'drift_model': None},
    ],
    'confounds': [None, 'motion_6'],
    'voxel_norm': [None, 'demean'],
}

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Preprocessing Grid Search for B&H (2009) Pipeline'
    )
    parser.add_argument('--subject', type=str, required=True,
                        help='Subject ID (e.g., 01, 02, ..., 10)')
    parser.add_argument('--roi', type=str, required=True,
                        help='ROI name (e.g., V1, V2, V3, hV4)')
    parser.add_argument('--dataset', type=str, default='method3_header_mi',
                        choices=['original_v3', 'method3_header_mi', 'deoblique_v2'],
                        help='Dataset to use (default: method3_header_mi)')
    return parser.parse_args()

def generate_configs():
    """Generate all parameter combinations"""
    configs = []
    config_id = 0

    for smooth in GRID_PARAMS['smoothing_fwhm']:
        for temp_filter in GRID_PARAMS['temporal_filter']:
            for confounds in GRID_PARAMS['confounds']:
                for voxel_norm in GRID_PARAMS['voxel_norm']:
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

def load_and_preprocess_data(config, subject_id, roi_name, dataset='method3_header_mi'):
    """Load and preprocess functional data according to config"""

    print(f"  Loading data with config {config['id']}...")

    # Dataset configuration
    dataset_paths = {
        'original_v3': '/storage/connectome/haba6030/fmriprep_out_original_v3',
        'method3_header_mi': '/storage/connectome/haba6030/fmriprep_out_method3_header_mi',
        'deoblique_v2': '/storage/connectome/haba6030/fmriprep_out_deoblique_v2'
    }

    # Set paths
    fmriprep_dir = f"{dataset_paths[dataset]}/sub-{subject_id}"
    events_dir = f"/storage/connectome/haba6030/colorBlind_data_deoblique/sub-{subject_id}/func"
    roi_path = f"derivatives/sub-{subject_id}/roi_pipeline/{roi_name}_mask_thr50_intnearest_binTrue_masknone_gmTrue_subjFalse.nii.gz"

    # Load ROI mask
    roi_img = nib.load(roi_path)
    masker = NiftiMasker(mask_img=roi_img, standardize=False)
    masker.fit()

    all_func_data = []
    all_events = []

    for run in range(1, N_RUNS + 1):
        # Load functional image
        func_path = f"{fmriprep_dir}/func/sub-{subject_id}_task-rsvp_run-{run}_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz"
        func_img = nib.load(func_path)

        # Drop initial volumes
        if VOLS_TO_DROP > 0:
            func_img = nimg.index_img(func_img, slice(VOLS_TO_DROP, None))

        # SMOOTHING
        if config['smoothing_fwhm'] > 0:
            func_img = nimg.smooth_img(func_img, fwhm=config['smoothing_fwhm'])

        # Extract with masker
        func_data = masker.transform(func_img)

        # CONFOUNDS
        confounds_mat = None
        if config['confounds'] == 'motion_6':
            confounds_path = f"{fmriprep_dir}/func/sub-{subject_id}_task-rsvp_run-{run}_desc-confounds_timeseries.tsv"
            confounds_df = pd.read_csv(confounds_path, sep='\t')
            motion_cols = ['trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z']
            confounds_mat = confounds_df[motion_cols].iloc[VOLS_TO_DROP:].values

        # HIGH-PASS FILTERING + CONFOUNDS
        if config['high_pass'] is not None or confounds_mat is not None:
            func_data = clean(
                func_data,
                detrend=False,
                standardize=False,
                high_pass=config['high_pass'],
                t_r=TR,
                confounds=confounds_mat
            )

        all_func_data.append(func_data)

        # Load events
        events_path = f"{events_dir}/sub-{subject_id}_task-rsvp_run-{run}_events.tsv"
        events = pd.read_csv(events_path, sep='\t')
        events['onset'] = events['onset'] - (VOLS_TO_DROP * TR)
        events = events[events['onset'] >= 0].reset_index(drop=True)
        all_events.append(events)

    return all_func_data, all_events, masker

def compute_temporal_snr(func_data):
    """Compute temporal SNR for each voxel"""
    n_scans, n_voxels = func_data.shape
    tsnr = np.zeros(n_voxels)

    for v in range(n_voxels):
        timeseries = func_data[:, v]
        detrended = detrend(timeseries)

        # tSNR = mean / std(detrended)
        mean_signal = np.mean(timeseries)
        std_noise = np.std(detrended)

        if std_noise > 0:
            tsnr[v] = mean_signal / std_noise
        else:
            tsnr[v] = 0

    return tsnr

def build_fir_design_matrix(events, n_scans, tr, fir_delays, drift_model=None):
    """Build FIR design matrix with optional drift regressors

    CRITICAL FIX: Only use COLOR events, exclude BLANK trials
    Blank trials serve as implicit baseline (not modeled)
    """

    # FIX: Filter for color events only (exclude blank)
    color_events = events[events['trial_type'].str.startswith('color_')]
    all_onsets = color_events['onset'].values

    # ========================================================================
    # STEP 1: Build FIR regressors manually
    # ========================================================================
    n_fir = len(fir_delays)
    X_fir = np.zeros((n_scans, n_fir))

    for onset in all_onsets:
        onset_tr = int(np.round(onset / tr))
        for i, delay in enumerate(fir_delays):
            tr_idx = onset_tr + delay
            if 0 <= tr_idx < n_scans:
                X_fir[tr_idx, i] = 1.0

    # ========================================================================
    # STEP 2: Add drift regressors if requested
    # ========================================================================
    if drift_model == 'polynomial':
        # Create polynomial drift regressors
        # Order 1 = constant + linear trend

        # Constant (intercept)
        constant = np.ones((n_scans, 1))

        # Linear drift (normalized to [-1, 1])
        time_axis = np.linspace(-1, 1, n_scans).reshape(-1, 1)

        # Combine: [FIR columns, constant, drift]
        X = np.hstack([X_fir, constant, time_axis])
        # Shape: (n_scans, n_fir + 2) = (284, 10)

    else:
        # No drift regressors, just FIR
        X = X_fir
        # Shape: (n_scans, n_fir) = (284, 8)

    # ========================================================================
    # STEP 3: Validation
    # ========================================================================
    if X.shape[0] != n_scans:
        raise ValueError(f"Design matrix has {X.shape[0]} rows but expected {n_scans}")

    return X

# Estimate HRF for each voxel using multi-run FIR
def estimate_voxel_hrf(func_data_list, events_list, config):
    """Estimate HRF for each voxel using multi-run FIR"""
    # 1. Concatenate all runs' data
    # Number of voxels
    n_voxels = func_data_list[0].shape[1]

    # Concatenate runs: structured as (total_scans(1704), n_voxels(481))
    y_all = np.vstack(func_data_list)
    n_scans_total = y_all.shape[0]

    # Build combined design matrix
    X_all_list = []

    # DEBUG: Print shapes
    print(f"  DEBUG: Building design matrices...")
    for run_idx in range(N_RUNS):
        n_scans_run = func_data_list[run_idx].shape[0]
        print(f"    Run {run_idx+1}: func_data shape = {func_data_list[run_idx].shape}, n_scans = {n_scans_run}")

    # 2. Make design matrices for each run and stack
    for run_idx in range(N_RUNS):
        events = events_list[run_idx].copy()
        # Don't adjust onset - each run's events are already in that run's time frame

        n_scans_run = func_data_list[run_idx].shape[0]
        X_run = build_fir_design_matrix(events, n_scans_run, TR, FIR_DELAYS, config['drift_model'])
        print(f"    Run {run_idx+1}: X_run shape = {X_run.shape}")
        X_all_list.append(X_run)

    X_all = np.vstack(X_all_list)
    print(f"  DEBUG: X_all shape = {X_all.shape}, y_all shape = {y_all.shape}")

    n_fir = len(FIR_DELAYS)

    # 3. Estimate HRF(FIR) per voxel
    HRF_voxels = np.zeros((n_voxels, n_fir))
    r2_voxels = np.zeros(n_voxels)

    for v in range(n_voxels):
        y_voxel = y_all[:, v]

        # FIX: Use FULL design matrix (FIR + drift) for fitting
        # Then extract only HRF betas
        try:
            beta_full = np.linalg.pinv(X_all) @ y_voxel
        except np.linalg.LinAlgError:
            # Fallback to least squares if SVD doesn't converge
            beta_full, _, _, _ = np.linalg.lstsq(X_all, y_voxel, rcond=None)

        # Extract FIR part (first n_fir elements)
        h_v = beta_full[:n_fir]
        HRF_voxels[v] = h_v

        # Compute R² using FULL model prediction (includes drift)
        y_pred = X_all @ beta_full
        ss_res = np.sum((y_voxel - y_pred)**2)
        ss_tot = np.sum((y_voxel - np.mean(y_voxel))**2)
        r2_voxels[v] = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

    # VOXEL NORMALIZATION
    if config['voxel_norm'] == 'demean':
        HRF_voxels = HRF_voxels - np.mean(HRF_voxels, axis=1, keepdims=True)
    elif config['voxel_norm'] == 'standardize':
        mean = np.mean(HRF_voxels, axis=1, keepdims=True)
        std = np.std(HRF_voxels, axis=1, keepdims=True)
        HRF_voxels = (HRF_voxels - mean) / (std + 1e-10)

    return HRF_voxels, r2_voxels

def compute_metrics(func_data_list, HRF_voxels, r2_voxels, config):
    """Compute all quality metrics"""

    metrics = {}

    # R² metrics: can each voxel's HRF be well explained by FIR model?
    r2_valid = r2_voxels[r2_voxels > 0]
    if len(r2_valid) > 0:
        metrics['r2_mean'] = float(np.mean(r2_valid))
        metrics['r2_median'] = float(np.median(r2_valid))
        metrics['r2_std'] = float(np.std(r2_valid))
    else:
        # All R² <= 0 (very bad fit)
        metrics['r2_mean'] = float(np.mean(r2_voxels))
        metrics['r2_median'] = float(np.median(r2_voxels))
        metrics['r2_std'] = float(np.std(r2_voxels))

    # Voxel selection (top 50%)
    r2_threshold = np.median(r2_voxels)
    selected_mask = r2_voxels >= r2_threshold
    n_selected = np.sum(selected_mask)
    metrics['n_voxels_selected'] = int(n_selected)

    # ROI HRF quality - calculated on selected voxels (as in actual pipeline)
    # NOTE: Multi-run concatenation makes HRF estimation stable, so correlation is high
    ROI_HRF = np.mean(HRF_voxels[selected_mask], axis=0)
    hrf_corrs = []
    for v in np.where(selected_mask)[0]:
        r = np.corrcoef(HRF_voxels[v], ROI_HRF)[0, 1]
        if not np.isnan(r):
            hrf_corrs.append(r)

    metrics['hrf_variability'] = float(np.mean(hrf_corrs)) if hrf_corrs else 0.0
    metrics['hrf_representativeness'] = float(np.sum(np.array(hrf_corrs) > 0.8)) / len(hrf_corrs) if hrf_corrs else 0.0

    # Temporal SNR (on first run)
    tsnr = compute_temporal_snr(func_data_list[0])
    metrics['temporal_snr_mean'] = float(np.mean(tsnr))
    metrics['temporal_snr_median'] = float(np.median(tsnr))
    metrics['temporal_snr_max'] = float(np.max(tsnr))

    # Spatial SNR (placeholder - would need amplitude estimation)
    metrics['spatial_snr_mean'] = 0.0
    metrics['spatial_snr_max'] = 0.0

    # Run-to-run reliability (placeholder - would need full pipeline)
    metrics['run_to_run_reliability'] = 0.0
    metrics['zero_variance_pct'] = 0.0

    return metrics

def run_single_config(config, subject_id, roi_name):
    """Run analysis for single configuration"""

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
        # Load and preprocess
        func_data_list, events_list, masker = load_and_preprocess_data(config, subject_id, roi_name, dataset=args.dataset)

        # Estimate HRF
        print(f"  Estimating HRF...")
        HRF_voxels, r2_voxels = estimate_voxel_hrf(func_data_list, events_list, config)

        # Compute metrics
        print(f"  Computing metrics...")
        metrics = compute_metrics(func_data_list, HRF_voxels, r2_voxels, config)

        elapsed = time.time() - start_time
        metrics['elapsed_time'] = elapsed
        metrics['status'] = 'success'

        print(f"  ✓ Completed in {elapsed:.1f}s")
        print(f"  R²: {metrics['r2_mean']:.4f}, tSNR: {metrics['temporal_snr_mean']:.1f}, HRF corr: {metrics['hrf_variability']:.3f}")

    except Exception as e:
        import traceback
        print(f"  ✗ Failed: {str(e)}")
        print(f"  Full traceback:")
        traceback.print_exc()
        metrics = {
            'status': 'failed',
            'error': str(e),
            'traceback': traceback.format_exc(),
            'elapsed_time': time.time() - start_time
        }

    # Save result
    result = {**config, **metrics}

    return result

def main():
    """Main grid search loop"""

    # Parse arguments
    args = parse_args()
    subject_id = args.subject
    roi_name = args.roi

    # Create output directory
    output_dir = Path(f"derivatives/grid_search_{subject_id}_{roi_name}")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("="*80)
    print("COMPREHENSIVE PREPROCESSING GRID SEARCH")
    print("="*80)
    print(f"Subject: {subject_id}")
    print(f"ROI: {roi_name}")
    print(f"Total configurations: {len(generate_configs())}")
    print(f"Output: {output_dir}")
    print()

    configs = generate_configs()
    results = []

    for config in configs:
        result = run_single_config(config, subject_id, roi_name)
        results.append(result)

        # Save incremental results
        results_df = pd.DataFrame(results)
        results_df.to_csv(output_dir / 'grid_search_results.csv', index=False)

    # Final summary
    print("\n" + "="*80)
    print("GRID SEARCH COMPLETE")
    print("="*80)

    results_df = pd.DataFrame(results)
    successful = results_df[results_df['status'] == 'success']

    if len(successful) > 0:
        # Best configuration by HRF variability (correlation with ROI HRF)
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

        # Save best config
        best_config_dict = best_config.to_dict()
        with open(output_dir / 'best_config.json', 'w') as f:
            json.dump(best_config_dict, f, indent=2)

    print(f"\nResults saved to: {output_dir}")
    print("="*80)

if __name__ == '__main__':
    main()
