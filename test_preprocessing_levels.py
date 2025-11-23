#!/usr/bin/env python3
"""
Test different preprocessing levels to diagnose R² issue

This script tests three preprocessing approaches:
1. NO_CLEAN: Raw fMRIPrep output (already has motion correction, normalization)
2. MOTION_ONLY: Motion confounds regression without detrending
3. MOTION_DETREND: Motion confounds + detrending (current approach)

Expected outcome: Identify which preprocessing preserves task signal best
"""

import numpy as np
import pandas as pd
import nibabel as nib
from nilearn.maskers import NiftiMasker
from nilearn.signal import clean
from nilearn.glm.first_level import make_first_level_design_matrix
import matplotlib.pyplot as plt

# Configuration
SUBJECT_ID = '01'
ROI_NAME = 'V1'
RUN = 1
TR = 1.5
VOLS_TO_DROP = 4

# Paths
FMRIPREP_DIR = f"/storage/connectome/haba6030/fmriprep_out/sub-{SUBJECT_ID}"
EVENTS_DIR = f"/storage/connectome/haba6030/colorBlind_dataOct/sub-{SUBJECT_ID}/func"

# Build ROI mask path
roi_path = f"derivatives/sub-{SUBJECT_ID}/roi_pipeline/{ROI_NAME}_mask_thr50_intnearest_binTrue_masknone_gmTrue_subjFalse.nii.gz"

# Build functional data path
func_path = f"{FMRIPREP_DIR}/func/sub-{SUBJECT_ID}_task-rsvp_run-{RUN}_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz"

# Build events path
events_path = f"{EVENTS_DIR}/sub-{SUBJECT_ID}_task-rsvp_run-{RUN}_events.tsv"

# Build confounds path
confounds_path = f"{FMRIPREP_DIR}/func/sub-{SUBJECT_ID}_task-rsvp_run-{RUN}_desc-confounds_timeseries.tsv"

print("="*80)
print("PREPROCESSING LEVEL COMPARISON TEST")
print("="*80)
print(f"Subject: {SUBJECT_ID}")
print(f"ROI: {ROI_NAME}")
print(f"Run: {RUN}")
print()

# Load ROI mask
print("[1/6] Loading ROI mask...")
roi_img = nib.load(roi_path)
masker = NiftiMasker(mask_img=roi_img, standardize=False)
masker.fit()
print(f"  ✓ Loaded {roi_path}")
print(f"  Total voxels in ROI: {np.sum(roi_img.get_fdata() > 0)}")
print()

# Load functional data
print("[2/6] Loading functional data...")
func_img = nib.load(func_path)
func_img = func_img.slicer[..., VOLS_TO_DROP:]  # Drop initial volumes
func_data_raw = masker.transform(func_img)
print(f"  ✓ Loaded {func_path}")
print(f"  Shape after dropping {VOLS_TO_DROP} vols: {func_data_raw.shape}")
print()

# Load confounds
print("[3/6] Loading confounds...")
confounds = pd.read_csv(confounds_path, sep='\t')
motion_cols = ['trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z']
confounds_subset = confounds[motion_cols].iloc[VOLS_TO_DROP:]
print(f"  ✓ Loaded {len(motion_cols)} motion parameters")
print(f"  Shape: {confounds_subset.shape}")
print()

# Load events
print("[4/6] Loading events...")
events = pd.read_csv(events_path, sep='\t')
# Adjust onset times for dropped volumes
events['onset'] = events['onset'] - (VOLS_TO_DROP * TR)
# Filter events that are still within the valid time range
frame_times = np.arange(func_data_raw.shape[0]) * TR
events = events[events['onset'] >= 0].reset_index(drop=True)
print(f"  ✓ Loaded {len(events)} events")
print()

# Build FIR design matrix (color-ignored)
print("[5/6] Building FIR design matrix...")
FIR_DELAYS = np.arange(8)
all_onsets = events['onset'].values
paradigm = pd.DataFrame({
    'trial_type': ['stim'] * len(all_onsets),
    'onset': all_onsets,
    'duration': [0] * len(all_onsets)
})

X_fir = make_first_level_design_matrix(
    frame_times=frame_times,
    events=paradigm,
    drift_model=None,
    hrf_model='fir',
    fir_delays=FIR_DELAYS
)
X_fir = X_fir[['stim_delay_' + str(d) for d in FIR_DELAYS]].values
print(f"  ✓ Design matrix shape: {X_fir.shape}")
print(f"  ✓ Rank: {np.linalg.matrix_rank(X_fir)}")
print()

# Test 3 preprocessing levels
print("[6/6] Testing preprocessing levels...")
print("="*80)

results = {}

# Level 1: NO CLEANING
print("\n1. NO_CLEAN (raw fMRIPrep output)")
print("-"*40)
func_data_test = func_data_raw.copy()

# Calculate statistics
print(f"  Signal std (mean across voxels): {np.mean(np.std(func_data_test, axis=0)):.2f}")
print(f"  Signal mean (mean across voxels): {np.mean(np.mean(func_data_test, axis=0)):.2f}")

# Fit FIR model to first 100 voxels
n_test_voxels = min(100, func_data_test.shape[1])
r2_values = []
for v in range(n_test_voxels):
    y_voxel = func_data_test[:, v]
    h_v = np.linalg.pinv(X_fir) @ y_voxel
    y_pred = X_fir @ h_v
    ss_res = np.sum((y_voxel - y_pred)**2)
    ss_tot = np.sum((y_voxel - np.mean(y_voxel))**2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else np.nan
    r2_values.append(r2)

r2_values = np.array(r2_values)
r2_values = r2_values[~np.isnan(r2_values)]
print(f"  R² (n={len(r2_values)} voxels):")
print(f"    Mean: {np.mean(r2_values):.4f}")
print(f"    Median: {np.median(r2_values):.4f}")
print(f"    Std: {np.std(r2_values):.4f}")
print(f"    Range: [{np.min(r2_values):.4f}, {np.max(r2_values):.4f}]")

results['NO_CLEAN'] = {
    'signal_std': np.mean(np.std(func_data_test, axis=0)),
    'r2_mean': np.mean(r2_values),
    'r2_median': np.median(r2_values)
}

# Level 2: MOTION ONLY
print("\n2. MOTION_ONLY (confounds regression, no detrending)")
print("-"*40)
func_data_test = clean(
    func_data_raw,
    confounds=confounds_subset.values,
    detrend=False,  # NO detrending
    standardize=False,
    standardize_confounds=True,
    high_pass=None,
    t_r=TR
)

print(f"  Signal std (mean across voxels): {np.mean(np.std(func_data_test, axis=0)):.2f}")
print(f"  Signal mean (mean across voxels): {np.mean(np.mean(func_data_test, axis=0)):.2f}")

# Fit FIR model
r2_values = []
for v in range(n_test_voxels):
    y_voxel = func_data_test[:, v]
    h_v = np.linalg.pinv(X_fir) @ y_voxel
    y_pred = X_fir @ h_v
    ss_res = np.sum((y_voxel - y_pred)**2)
    ss_tot = np.sum((y_voxel - np.mean(y_voxel))**2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else np.nan
    r2_values.append(r2)

r2_values = np.array(r2_values)
r2_values = r2_values[~np.isnan(r2_values)]
print(f"  R² (n={len(r2_values)} voxels):")
print(f"    Mean: {np.mean(r2_values):.4f}")
print(f"    Median: {np.median(r2_values):.4f}")
print(f"    Std: {np.std(r2_values):.4f}")
print(f"    Range: [{np.min(r2_values):.4f}, {np.max(r2_values):.4f}]")

results['MOTION_ONLY'] = {
    'signal_std': np.mean(np.std(func_data_test, axis=0)),
    'r2_mean': np.mean(r2_values),
    'r2_median': np.median(r2_values)
}

# Level 3: MOTION + DETREND
print("\n3. MOTION_DETREND (current approach)")
print("-"*40)
func_data_test = clean(
    func_data_raw,
    confounds=confounds_subset.values,
    detrend=True,  # WITH detrending
    standardize=False,
    standardize_confounds=True,
    high_pass=None,
    t_r=TR
)

print(f"  Signal std (mean across voxels): {np.mean(np.std(func_data_test, axis=0)):.2f}")
print(f"  Signal mean (mean across voxels): {np.mean(np.mean(func_data_test, axis=0)):.2f}")

# Fit FIR model
r2_values = []
for v in range(n_test_voxels):
    y_voxel = func_data_test[:, v]
    h_v = np.linalg.pinv(X_fir) @ y_voxel
    y_pred = X_fir @ h_v
    ss_res = np.sum((y_voxel - y_pred)**2)
    ss_tot = np.sum((y_voxel - np.mean(y_voxel))**2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else np.nan
    r2_values.append(r2)

r2_values = np.array(r2_values)
r2_values = r2_values[~np.isnan(r2_values)]
print(f"  R² (n={len(r2_values)} voxels):")
print(f"    Mean: {np.mean(r2_values):.4f}")
print(f"    Median: {np.median(r2_values):.4f}")
print(f"    Std: {np.std(r2_values):.4f}")
print(f"    Range: [{np.min(r2_values):.4f}, {np.max(r2_values):.4f}]")

results['MOTION_DETREND'] = {
    'signal_std': np.mean(np.std(func_data_test, axis=0)),
    'r2_mean': np.mean(r2_values),
    'r2_median': np.median(r2_values)
}

# Summary comparison
print("\n" + "="*80)
print("SUMMARY COMPARISON")
print("="*80)
print(f"{'Method':<20} {'Signal Std':<15} {'R² Mean':<15} {'R² Median':<15}")
print("-"*80)
for method, vals in results.items():
    print(f"{method:<20} {vals['signal_std']:>14.2f} {vals['r2_mean']:>14.4f} {vals['r2_median']:>14.4f}")

print("\n" + "="*80)
print("RECOMMENDATION:")
best_method = max(results.items(), key=lambda x: x[1]['r2_mean'])[0]
print(f"  ✓ Best preprocessing: {best_method}")
print(f"  R² Mean: {results[best_method]['r2_mean']:.4f}")
print("="*80)
