#!/usr/bin/env python3
"""
CRITICAL TEST: Single run vs Multi-run analysis

Tests if combining all 6 runs gives much higher R² due to:
1. More events per color (8 → 48 per color)
2. Better statistical power
3. More stable HRF estimates

Expected: Multi-run should give R² > 0.15
"""

import numpy as np
import pandas as pd
import nibabel as nib
from nilearn.maskers import NiftiMasker
from nilearn.glm.first_level import make_first_level_design_matrix

# Configuration
SUBJECT_ID = '01'
ROI_NAME = 'V1'
TR = 1.5
VOLS_TO_DROP = 4
N_RUNS = 6

# Paths
FMRIPREP_DIR = f"/storage/connectome/haba6030/fmriprep_out/sub-{SUBJECT_ID}"
EVENTS_DIR = f"/storage/connectome/haba6030/colorBlind_dataOct/sub-{SUBJECT_ID}/func"

roi_path = f"derivatives/sub-{SUBJECT_ID}/roi_pipeline/{ROI_NAME}_mask_thr50_intnearest_binTrue_masknone_gmTrue_subjFalse.nii.gz"

print("="*80)
print("SINGLE RUN vs MULTI-RUN ANALYSIS TEST")
print("="*80)
print(f"Subject: {SUBJECT_ID}, ROI: {ROI_NAME}")
print()

# Load ROI mask
print("[1/3] Loading ROI mask...")
roi_img = nib.load(roi_path)
masker = NiftiMasker(mask_img=roi_img, standardize=False)
masker.fit()
print(f"  ✓ ROI voxels: {np.sum(roi_img.get_fdata() > 0)}")
print()

# Test 1: Single run (baseline)
print("="*80)
print("TEST 1: SINGLE RUN ANALYSIS (Run 1 only)")
print("="*80)

run = 1
func_path = f"{FMRIPREP_DIR}/func/sub-{SUBJECT_ID}_task-rsvp_run-{run}_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz"
events_path = f"{EVENTS_DIR}/sub-{SUBJECT_ID}_task-rsvp_run-{run}_events.tsv"

func_img = nib.load(func_path)
func_img = func_img.slicer[..., VOLS_TO_DROP:]
func_data = masker.transform(func_img)

events = pd.read_csv(events_path, sep='\t')
events['onset'] = events['onset'] - (VOLS_TO_DROP * TR)
frame_times = np.arange(func_data.shape[0]) * TR
events = events[events['onset'] >= 0].reset_index(drop=True)

print(f"  Data shape: {func_data.shape}")
print(f"  Events: {len(events)}")
print(f"  Events per color: {events['trial_type'].value_counts().to_dict()}")

# Build design matrix
paradigm = events[['trial_type', 'onset', 'duration']].copy()

X = make_first_level_design_matrix(
    frame_times=frame_times,
    events=paradigm,
    drift_model='polynomial',
    drift_order=1,
    hrf_model='spm'
)

print(f"  Design matrix: {X.shape}")

X_model = X.values
n_test_voxels = min(100, func_data.shape[1])
r2_single = []

for v in range(n_test_voxels):
    y_voxel = func_data[:, v]
    beta = np.linalg.pinv(X_model) @ y_voxel
    y_pred = X_model @ beta
    ss_res = np.sum((y_voxel - y_pred)**2)
    ss_tot = np.sum((y_voxel - np.mean(y_voxel))**2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else np.nan
    r2_single.append(r2)

r2_single = np.array(r2_single)
r2_single = r2_single[~np.isnan(r2_single)]

print(f"\n  R² (n={len(r2_single)} voxels):")
print(f"    Mean:   {np.mean(r2_single):.4f}")
print(f"    Median: {np.median(r2_single):.4f}")
print(f"    95th:   {np.percentile(r2_single, 95):.4f}")
print(f"    Good fit (R²>0.1): {np.sum(r2_single > 0.1)}/{len(r2_single)} ({100*np.sum(r2_single > 0.1)/len(r2_single):.1f}%)")

# Test 2: Multi-run (combining all 6 runs)
print("\n" + "="*80)
print("TEST 2: MULTI-RUN ANALYSIS (All 6 runs combined)")
print("="*80)

all_func_data = []
all_events = []
cumulative_time = 0

for run in range(1, N_RUNS + 1):
    func_path = f"{FMRIPREP_DIR}/func/sub-{SUBJECT_ID}_task-rsvp_run-{run}_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz"
    events_path = f"{EVENTS_DIR}/sub-{SUBJECT_ID}_task-rsvp_run-{run}_events.tsv"

    # Load functional data
    func_img = nib.load(func_path)
    func_img = func_img.slicer[..., VOLS_TO_DROP:]
    func_data = masker.transform(func_img)
    all_func_data.append(func_data)

    # Load events and adjust timing
    events = pd.read_csv(events_path, sep='\t')
    events['onset'] = events['onset'] - (VOLS_TO_DROP * TR) + cumulative_time
    events = events[events['onset'] >= 0].reset_index(drop=True)
    all_events.append(events)

    # Update cumulative time
    cumulative_time += func_data.shape[0] * TR

    print(f"  Run {run}: {func_data.shape[0]} TRs, {len(events)} events")

# Concatenate all runs
func_data_multi = np.vstack(all_func_data)
events_multi = pd.concat(all_events, ignore_index=True)
frame_times_multi = np.arange(func_data_multi.shape[0]) * TR

print(f"\n  Combined data shape: {func_data_multi.shape}")
print(f"  Total events: {len(events_multi)}")
print(f"  Events per color: {events_multi['trial_type'].value_counts().to_dict()}")

# Build design matrix for multi-run
paradigm_multi = events_multi[['trial_type', 'onset', 'duration']].copy()

X_multi = make_first_level_design_matrix(
    frame_times=frame_times_multi,
    events=paradigm_multi,
    drift_model='polynomial',
    drift_order=1,
    hrf_model='spm'
)

print(f"  Design matrix: {X_multi.shape}")

X_model_multi = X_multi.values
r2_multi = []

for v in range(n_test_voxels):
    y_voxel = func_data_multi[:, v]
    beta = np.linalg.pinv(X_model_multi) @ y_voxel
    y_pred = X_model_multi @ beta
    ss_res = np.sum((y_voxel - y_pred)**2)
    ss_tot = np.sum((y_voxel - np.mean(y_voxel))**2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else np.nan
    r2_multi.append(r2)

r2_multi = np.array(r2_multi)
r2_multi = r2_multi[~np.isnan(r2_multi)]

print(f"\n  R² (n={len(r2_multi)} voxels):")
print(f"    Mean:   {np.mean(r2_multi):.4f}")
print(f"    Median: {np.median(r2_multi):.4f}")
print(f"    95th:   {np.percentile(r2_multi, 95):.4f}")
print(f"    Good fit (R²>0.1): {np.sum(r2_multi > 0.1)}/{len(r2_multi)} ({100*np.sum(r2_multi > 0.1)/len(r2_multi):.1f}%)")

# Summary
print("\n" + "="*80)
print("COMPARISON")
print("="*80)

print(f"\n{'Method':<20} {'R² Mean':<12} {'R² Median':<12} {'R² 95th':<12} {'Good>0.1%':<12}")
print("-"*80)
print(f"{'Single Run':<20} {np.mean(r2_single):>11.4f} {np.median(r2_single):>11.4f} "
      f"{np.percentile(r2_single, 95):>11.4f} {100*np.sum(r2_single > 0.1)/len(r2_single):>11.1f}")
print(f"{'Multi-Run (6)':<20} {np.mean(r2_multi):>11.4f} {np.median(r2_multi):>11.4f} "
      f"{np.percentile(r2_multi, 95):>11.4f} {100*np.sum(r2_multi > 0.1)/len(r2_multi):>11.1f}")

improvement = np.mean(r2_multi) / np.mean(r2_single)

print("\n" + "="*80)
print("DIAGNOSIS:")
print("="*80)

print(f"\nMulti-run improvement: {improvement:.1f}x")

if improvement > 2.0:
    print(f"  ✅ HUGE improvement with multi-run!")
    print(f"  → Single run has insufficient events per color")
    print(f"  → MUST use all 6 runs combined for HRF estimation")
elif improvement > 1.5:
    print(f"  ✓ Good improvement with multi-run")
    print(f"  → Recommend using all 6 runs")
else:
    print(f"  ⚠️  Modest improvement")
    print(f"  → Multi-run helps but doesn't solve the problem")

if np.mean(r2_multi) > 0.15:
    print(f"\n  ✅ Multi-run R² = {np.mean(r2_multi):.4f}")
    print(f"  → This is acceptable for B&H 2009 pipeline!")
    print(f"  → Proceed with multi-run approach")
elif np.mean(r2_multi) > 0.10:
    print(f"\n  ⚠️  Multi-run R² = {np.mean(r2_multi):.4f}")
    print(f"  → Borderline acceptable")
    print(f"  → May need additional optimization")
else:
    print(f"\n  🚨 Multi-run R² = {np.mean(r2_multi):.4f}")
    print(f"  → Still too low even with all 6 runs")
    print(f"  → May indicate fundamental data quality issues")

print("="*80)
