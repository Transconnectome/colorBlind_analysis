#!/usr/bin/env python3
"""
Test FIR estimation WITH drift model in design matrix

This is the correct approach for fMRI GLM:
- FIR regressors explain task-related signal
- Drift regressors (constant + linear) explain baseline and slow drift
- No need for aggressive detrending

Expected: R² should be much higher (>0.15)
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

roi_path = f"derivatives/sub-{SUBJECT_ID}/roi_pipeline/{ROI_NAME}_mask_thr50_intnearest_binTrue_masknone_gmTrue_subjFalse.nii.gz"
func_path = f"{FMRIPREP_DIR}/func/sub-{SUBJECT_ID}_task-rsvp_run-{RUN}_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz"
events_path = f"{EVENTS_DIR}/sub-{SUBJECT_ID}_task-rsvp_run-{RUN}_events.tsv"
confounds_path = f"{FMRIPREP_DIR}/func/sub-{SUBJECT_ID}_task-rsvp_run-{RUN}_desc-confounds_timeseries.tsv"

print("="*80)
print("FIR ESTIMATION WITH DRIFT MODEL TEST")
print("="*80)
print(f"Subject: {SUBJECT_ID}, ROI: {ROI_NAME}, Run: {RUN}")
print()

# Load data
print("[1/5] Loading data...")
roi_img = nib.load(roi_path)
masker = NiftiMasker(mask_img=roi_img, standardize=False)
masker.fit()

func_img = nib.load(func_path)
func_img = func_img.slicer[..., VOLS_TO_DROP:]
func_data_raw = masker.transform(func_img)

confounds = pd.read_csv(confounds_path, sep='\t')
motion_cols = ['trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z']
confounds_subset = confounds[motion_cols].iloc[VOLS_TO_DROP:]

events = pd.read_csv(events_path, sep='\t')
events['onset'] = events['onset'] - (VOLS_TO_DROP * TR)
frame_times = np.arange(func_data_raw.shape[0]) * TR
events = events[events['onset'] >= 0].reset_index(drop=True)

print(f"  ✓ Functional data: {func_data_raw.shape}")
print(f"  ✓ Events: {len(events)}")
print(f"  ✓ ROI voxels: {func_data_raw.shape[1]}")
print()

# Prepare preprocessing options
print("[2/5] Testing preprocessing options...")
print()

preprocessing_options = {
    'RAW': func_data_raw.copy(),
    'MOTION_ONLY': clean(
        func_data_raw,
        confounds=confounds_subset.values,
        detrend=False,
        standardize=False,
        standardize_confounds=True,
        high_pass=None,
        t_r=TR
    )
}

# Test both drift model options
drift_options = {
    'NO_DRIFT': None,
    'POLYNOMIAL_1': 'polynomial'
}

FIR_DELAYS = np.arange(8)
all_onsets = events['onset'].values
paradigm = pd.DataFrame({
    'trial_type': ['stim'] * len(all_onsets),
    'onset': all_onsets,
    'duration': [0] * len(all_onsets)
})

results = {}

for preproc_name, func_data in preprocessing_options.items():
    for drift_name, drift_model in drift_options.items():

        print(f"\n{'='*80}")
        print(f"Testing: {preproc_name} + {drift_name}")
        print(f"{'='*80}")

        # Build design matrix
        if drift_model is None:
            X = make_first_level_design_matrix(
                frame_times=frame_times,
                events=paradigm,
                drift_model=None,
                hrf_model='fir',
                fir_delays=FIR_DELAYS
            )
            # Extract only FIR columns
            X_model = X[['stim_delay_' + str(d) for d in FIR_DELAYS]].values
        else:
            X = make_first_level_design_matrix(
                frame_times=frame_times,
                events=paradigm,
                drift_model=drift_model,
                drift_order=1,  # constant + linear
                hrf_model='fir',
                fir_delays=FIR_DELAYS
            )
            # All columns (FIR + drift)
            X_model = X.values

        print(f"  Design matrix shape: {X_model.shape}")
        print(f"  Design matrix rank: {np.linalg.matrix_rank(X_model)}")

        # Fit model to first 100 voxels
        n_test_voxels = min(100, func_data.shape[1])
        r2_values = []
        hrf_estimates = []

        for v in range(n_test_voxels):
            y_voxel = func_data[:, v]

            # Fit model
            beta = np.linalg.pinv(X_model) @ y_voxel
            y_pred = X_model @ beta

            # Calculate R²
            ss_res = np.sum((y_voxel - y_pred)**2)
            ss_tot = np.sum((y_voxel - np.mean(y_voxel))**2)
            r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else np.nan
            r2_values.append(r2)

            # Extract HRF (first 8 betas)
            hrf_estimates.append(beta[:8])

        r2_values = np.array(r2_values)
        valid_r2 = r2_values[~np.isnan(r2_values)]
        hrf_estimates = np.array(hrf_estimates)

        print(f"\n  Signal statistics:")
        print(f"    Mean: {np.mean(np.mean(func_data, axis=0)):.2f}")
        print(f"    Std (mean across voxels): {np.mean(np.std(func_data, axis=0)):.2f}")

        print(f"\n  R² statistics (n={len(valid_r2)} voxels):")
        print(f"    Mean:   {np.mean(valid_r2):.4f}")
        print(f"    Median: {np.median(valid_r2):.4f}")
        print(f"    Std:    {np.std(valid_r2):.4f}")
        print(f"    Range:  [{np.min(valid_r2):.4f}, {np.max(valid_r2):.4f}]")

        # Percentiles
        print(f"\n  R² percentiles:")
        for p in [10, 25, 50, 75, 90, 95]:
            val = np.percentile(valid_r2, p)
            print(f"    {p:2d}th: {val:.4f}")

        # Good fit voxels
        good_fit_counts = {
            'R² > 0.1': np.sum(valid_r2 > 0.1),
            'R² > 0.2': np.sum(valid_r2 > 0.2),
            'R² > 0.3': np.sum(valid_r2 > 0.3),
        }
        print(f"\n  Good fit voxels:")
        for label, count in good_fit_counts.items():
            pct = 100 * count / len(valid_r2)
            print(f"    {label}: {count}/{len(valid_r2)} ({pct:.1f}%)")

        # Average HRF shape
        mean_hrf = np.mean(hrf_estimates, axis=0)
        peak_delay = np.argmax(np.abs(mean_hrf))
        peak_time = peak_delay * TR

        print(f"\n  HRF characteristics:")
        print(f"    Peak delay: {peak_delay} ({peak_time:.1f}s)")
        print(f"    Peak amplitude: {mean_hrf[peak_delay]:.2f}")
        print(f"    Mean HRF: {mean_hrf}")

        # Store results
        key = f"{preproc_name}_{drift_name}"
        results[key] = {
            'r2_mean': np.mean(valid_r2),
            'r2_median': np.median(valid_r2),
            'r2_std': np.std(valid_r2),
            'good_fit_pct': 100 * np.sum(valid_r2 > 0.1) / len(valid_r2),
            'peak_delay': peak_delay,
            'peak_time': peak_time
        }

# Summary
print("\n" + "="*80)
print("SUMMARY COMPARISON")
print("="*80)
print(f"{'Method':<25} {'R² Mean':<12} {'R² Median':<12} {'Good Fit %':<12} {'Peak (s)':<10}")
print("-"*80)
for key, vals in results.items():
    print(f"{key:<25} {vals['r2_mean']:>11.4f} {vals['r2_median']:>11.4f} "
          f"{vals['good_fit_pct']:>11.1f} {vals['peak_time']:>9.1f}")

print("\n" + "="*80)
print("RECOMMENDATION:")
best_method = max(results.items(), key=lambda x: x[1]['r2_mean'])[0]
print(f"  ✓ Best approach: {best_method}")
print(f"  R² Mean: {results[best_method]['r2_mean']:.4f}")
print(f"  Good fit voxels: {results[best_method]['good_fit_pct']:.1f}%")
print(f"  Peak time: {results[best_method]['peak_time']:.1f}s")
print("="*80)
