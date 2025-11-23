#!/usr/bin/env python3
"""
Critical diagnostic test: Canonical HRF vs FIR

This will determine if the problem is:
1. FIR model (too many parameters for weak signal)
2. Data quality (low SNR, weak task signal)

Also tests different event durations to find optimal setting.
"""

import numpy as np
import pandas as pd
import nibabel as nib
from nilearn.maskers import NiftiMasker
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

print("="*80)
print("CANONICAL HRF vs FIR DIAGNOSTIC TEST")
print("="*80)
print(f"Subject: {SUBJECT_ID}, ROI: {ROI_NAME}, Run: {RUN}")
print()

# Load data
print("[1/4] Loading data...")
roi_img = nib.load(roi_path)
masker = NiftiMasker(mask_img=roi_img, standardize=False)
masker.fit()

func_img = nib.load(func_path)
func_img = func_img.slicer[..., VOLS_TO_DROP:]
func_data = masker.transform(func_img)

events = pd.read_csv(events_path, sep='\t')
events['onset'] = events['onset'] - (VOLS_TO_DROP * TR)
frame_times = np.arange(func_data.shape[0]) * TR
events = events[events['onset'] >= 0].reset_index(drop=True)

print(f"  ✓ Functional data: {func_data.shape}")
print(f"  ✓ Events: {len(events)}")
print()

# Check actual duration in events.tsv
print("[2/4] Checking events.tsv...")
if 'duration' in events.columns:
    print(f"  Duration column exists!")
    print(f"  Unique durations: {events['duration'].unique()}")
    print(f"  Mean duration: {events['duration'].mean():.2f}s")
    actual_duration = events['duration'].iloc[0]
else:
    print(f"  No duration column found, using 1.5s (stimulus duration from IRB)")
    actual_duration = 1.5

print()

# Test configurations
all_onsets = events['onset'].values

test_configs = {
    # HRF model, duration, description
    'CANONICAL_DUR0': ('spm', 0, 'Canonical SPM HRF, impulse events'),
    'CANONICAL_DUR1.5': ('spm', 1.5, 'Canonical SPM HRF, 1.5s duration'),
    'GLOVER_DUR0': ('glover', 0, 'Glover HRF, impulse events'),
    'GLOVER_DUR1.5': ('glover', 1.5, 'Glover HRF, 1.5s duration'),
    'FIR_DUR0': ('fir', 0, 'FIR (8 delays), impulse events'),
    'FIR_DUR1.5': ('fir', 1.5, 'FIR (8 delays), 1.5s duration'),
}

results = {}

print("[3/4] Testing HRF models...")
print()

for config_name, (hrf_model, duration, description) in test_configs.items():

    print(f"\n{'='*80}")
    print(f"{config_name}: {description}")
    print(f"{'='*80}")

    # Build paradigm
    paradigm = pd.DataFrame({
        'trial_type': ['stim'] * len(all_onsets),
        'onset': all_onsets,
        'duration': [duration] * len(all_onsets)
    })

    # Build design matrix
    if hrf_model == 'fir':
        fir_delays = np.arange(8)
        X = make_first_level_design_matrix(
            frame_times=frame_times,
            events=paradigm,
            drift_model='polynomial',
            drift_order=1,
            hrf_model='fir',
            fir_delays=fir_delays
        )
    else:
        X = make_first_level_design_matrix(
            frame_times=frame_times,
            events=paradigm,
            drift_model='polynomial',
            drift_order=1,
            hrf_model=hrf_model
        )

    X_model = X.values

    print(f"  Design matrix shape: {X_model.shape}")
    print(f"  Design matrix rank: {np.linalg.matrix_rank(X_model)}")

    # Calculate condition number for multicollinearity check
    condition_number = np.linalg.cond(X_model)
    print(f"  Condition number: {condition_number:.2f}", end="")
    if condition_number > 30:
        print(" ⚠️ High multicollinearity!")
    elif condition_number > 15:
        print(" ⚠️ Moderate multicollinearity")
    else:
        print(" ✓ Good conditioning")

    # Fit model to first 100 voxels
    n_test_voxels = min(100, func_data.shape[1])
    r2_values = []

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

    r2_values = np.array(r2_values)
    valid_r2 = r2_values[~np.isnan(r2_values)]

    print(f"\n  R² statistics (n={len(valid_r2)} voxels):")
    print(f"    Mean:   {np.mean(valid_r2):.4f}")
    print(f"    Median: {np.median(valid_r2):.4f}")
    print(f"    Std:    {np.std(valid_r2):.4f}")
    print(f"    Range:  [{np.min(valid_r2):.4f}, {np.max(valid_r2):.4f}]")

    # Percentiles
    print(f"\n  R² percentiles:")
    for p in [25, 50, 75, 90, 95]:
        val = np.percentile(valid_r2, p)
        print(f"    {p:2d}th: {val:.4f}")

    # Good fit voxels
    good_fit = {
        'R² > 0.05': np.sum(valid_r2 > 0.05),
        'R² > 0.10': np.sum(valid_r2 > 0.10),
        'R² > 0.20': np.sum(valid_r2 > 0.20),
        'R² > 0.30': np.sum(valid_r2 > 0.30),
    }
    print(f"\n  Good fit voxels:")
    for label, count in good_fit.items():
        pct = 100 * count / len(valid_r2)
        print(f"    {label}: {count:3d}/{len(valid_r2)} ({pct:5.1f}%)")

    # Store results
    results[config_name] = {
        'r2_mean': np.mean(valid_r2),
        'r2_median': np.median(valid_r2),
        'r2_std': np.std(valid_r2),
        'r2_95th': np.percentile(valid_r2, 95),
        'good_fit_pct': 100 * np.sum(valid_r2 > 0.10) / len(valid_r2),
        'condition_number': condition_number,
        'hrf_model': hrf_model,
        'duration': duration
    }

# Summary
print("\n" + "="*80)
print("SUMMARY COMPARISON")
print("="*80)
print(f"{'Method':<25} {'R² Mean':<12} {'R² Median':<12} {'R² 95th':<12} {'Good>0.1%':<12}")
print("-"*80)

# Sort by R² mean
sorted_results = sorted(results.items(), key=lambda x: x[1]['r2_mean'], reverse=True)
for key, vals in sorted_results:
    print(f"{key:<25} {vals['r2_mean']:>11.4f} {vals['r2_median']:>11.4f} "
          f"{vals['r2_95th']:>11.4f} {vals['good_fit_pct']:>11.1f}")

print("\n" + "="*80)
print("ANALYSIS:")
print("="*80)

# Find best overall
best_overall = sorted_results[0]
print(f"\n1. Best overall method: {best_overall[0]}")
print(f"   R² Mean: {best_overall[1]['r2_mean']:.4f}")
print(f"   Good fit voxels (R²>0.1): {best_overall[1]['good_fit_pct']:.1f}%")

# Compare canonical vs FIR
canonical_r2 = [v['r2_mean'] for k, v in results.items() if v['hrf_model'] in ['spm', 'glover']]
fir_r2 = [v['r2_mean'] for k, v in results.items() if v['hrf_model'] == 'fir']

print(f"\n2. Canonical HRF models:")
print(f"   Mean R²: {np.mean(canonical_r2):.4f}")
print(f"   Best canonical R²: {np.max(canonical_r2):.4f}")

print(f"\n3. FIR model:")
print(f"   Mean R²: {np.mean(fir_r2):.4f}")
print(f"   Best FIR R²: {np.max(fir_r2):.4f}")

# Diagnosis
print(f"\n4. DIAGNOSIS:")
if np.max(canonical_r2) > 0.20:
    if np.max(fir_r2) < 0.10:
        print("   ⚠️  FIR model is underfitting!")
        print("   → Canonical HRF works well, but FIR doesn't")
        print("   → Consider: fewer FIR delays, or use canonical HRF")
    else:
        print("   ✓ Both models work well")
        print("   → Data quality is good")
elif np.max(canonical_r2) < 0.10:
    print("   🚨 Low signal quality!")
    print("   → Even canonical HRF gives low R²")
    print("   → Possible issues:")
    print("      - Weak task-related BOLD response")
    print("      - Wrong event timing")
    print("      - ROI doesn't respond to this task")
    print("      - Need more aggressive voxel selection")
else:
    print("   ⚠️  Moderate signal quality")
    print("   → Canonical HRF shows some signal (R² = 0.10-0.20)")
    print("   → Consider using canonical HRF instead of FIR")

# Duration comparison
dur0_r2 = [v['r2_mean'] for k, v in results.items() if v['duration'] == 0]
dur15_r2 = [v['r2_mean'] for k, v in results.items() if v['duration'] == 1.5]

print(f"\n5. Duration effect:")
print(f"   Duration=0 (impulse):    Mean R² = {np.mean(dur0_r2):.4f}")
print(f"   Duration=1.5s (boxcar):  Mean R² = {np.mean(dur15_r2):.4f}")
if np.mean(dur15_r2) > np.mean(dur0_r2) * 1.1:
    print("   → Use duration=1.5s (better fit)")
elif np.mean(dur0_r2) > np.mean(dur15_r2) * 1.1:
    print("   → Use duration=0 (better fit)")
else:
    print("   → Duration has minimal effect")

print("="*80)
