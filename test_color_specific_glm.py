#!/usr/bin/env python3
"""
CRITICAL TEST: Color-specific vs Color-ignored GLM

This tests the hypothesis that color-ignored GLM causes signal cancellation
due to opponent color coding in V1.

Color-specific GLM should give MUCH higher R² if this hypothesis is correct.
"""

import numpy as np
import pandas as pd
import nibabel as nib
from nilearn.maskers import NiftiMasker
from nilearn.glm.first_level import make_first_level_design_matrix

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
print("COLOR-SPECIFIC vs COLOR-IGNORED GLM TEST")
print("="*80)
print(f"Subject: {SUBJECT_ID}, ROI: {ROI_NAME}, Run: {RUN}")
print()

# Load data
print("[1/3] Loading data...")
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

# Check color labels
print("[2/3] Analyzing color labels...")
if 'trial_type' in events.columns:
    color_labels = events['trial_type'].unique()
    print(f"  ✓ Found 'trial_type' column")
    print(f"  Unique values: {sorted(color_labels)}")
    print(f"  Number of unique colors: {len(color_labels)}")

    # Count per color
    print(f"\n  Events per color:")
    for color in sorted(color_labels):
        count = np.sum(events['trial_type'] == color)
        print(f"    {color}: {count} events")

    use_trial_type = True
else:
    print(f"  ✗ No 'trial_type' column found")
    print(f"  Available columns: {events.columns.tolist()}")
    use_trial_type = False

print()

# Test configurations
print("[3/3] Testing GLM approaches...")
print()

results = {}

# Test 1: Color-ignored (current approach)
print("="*80)
print("TEST 1: COLOR-IGNORED GLM (current approach)")
print("="*80)

paradigm_ignored = pd.DataFrame({
    'trial_type': ['stim'] * len(events),
    'onset': events['onset'].values,
    'duration': events['duration'].values if 'duration' in events.columns else [1.5] * len(events)
})

X_ignored = make_first_level_design_matrix(
    frame_times=frame_times,
    events=paradigm_ignored,
    drift_model='polynomial',
    drift_order=1,
    hrf_model='spm'
)

print(f"  Design matrix shape: {X_ignored.shape}")
print(f"  Columns: {X_ignored.columns.tolist()}")

X_model = X_ignored.values
n_test_voxels = min(100, func_data.shape[1])
r2_values = []

for v in range(n_test_voxels):
    y_voxel = func_data[:, v]
    beta = np.linalg.pinv(X_model) @ y_voxel
    y_pred = X_model @ beta
    ss_res = np.sum((y_voxel - y_pred)**2)
    ss_tot = np.sum((y_voxel - np.mean(y_voxel))**2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else np.nan
    r2_values.append(r2)

r2_ignored = np.array(r2_values)
r2_ignored = r2_ignored[~np.isnan(r2_ignored)]

print(f"\n  R² statistics (n={len(r2_ignored)} voxels):")
print(f"    Mean:   {np.mean(r2_ignored):.4f}")
print(f"    Median: {np.median(r2_ignored):.4f}")
print(f"    95th:   {np.percentile(r2_ignored, 95):.4f}")
print(f"    Good fit (R²>0.1): {np.sum(r2_ignored > 0.1)}/{len(r2_ignored)} ({100*np.sum(r2_ignored > 0.1)/len(r2_ignored):.1f}%)")

results['COLOR_IGNORED'] = {
    'r2_mean': np.mean(r2_ignored),
    'r2_median': np.median(r2_ignored),
    'r2_95th': np.percentile(r2_ignored, 95),
    'good_fit_pct': 100 * np.sum(r2_ignored > 0.1) / len(r2_ignored)
}

# Test 2: Color-specific (if trial_type exists)
if use_trial_type:
    print("\n" + "="*80)
    print("TEST 2: COLOR-SPECIFIC GLM (separate regressors per color)")
    print("="*80)

    paradigm_specific = pd.DataFrame({
        'trial_type': events['trial_type'].values,
        'onset': events['onset'].values,
        'duration': events['duration'].values if 'duration' in events.columns else [1.5] * len(events)
    })

    X_specific = make_first_level_design_matrix(
        frame_times=frame_times,
        events=paradigm_specific,
        drift_model='polynomial',
        drift_order=1,
        hrf_model='spm'
    )

    print(f"  Design matrix shape: {X_specific.shape}")
    print(f"  Task regressors: {X_specific.shape[1] - 2} (expecting 8-9 colors)")
    print(f"  Columns: {X_specific.columns.tolist()}")

    X_model = X_specific.values
    r2_values = []

    for v in range(n_test_voxels):
        y_voxel = func_data[:, v]
        beta = np.linalg.pinv(X_model) @ y_voxel
        y_pred = X_model @ beta
        ss_res = np.sum((y_voxel - y_pred)**2)
        ss_tot = np.sum((y_voxel - np.mean(y_voxel))**2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else np.nan
        r2_values.append(r2)

    r2_specific = np.array(r2_values)
    r2_specific = r2_specific[~np.isnan(r2_specific)]

    print(f"\n  R² statistics (n={len(r2_specific)} voxels):")
    print(f"    Mean:   {np.mean(r2_specific):.4f}")
    print(f"    Median: {np.median(r2_specific):.4f}")
    print(f"    95th:   {np.percentile(r2_specific, 95):.4f}")
    print(f"    Good fit (R²>0.1): {np.sum(r2_specific > 0.1)}/{len(r2_specific)} ({100*np.sum(r2_specific > 0.1)/len(r2_specific):.1f}%)")

    results['COLOR_SPECIFIC'] = {
        'r2_mean': np.mean(r2_specific),
        'r2_median': np.median(r2_specific),
        'r2_95th': np.percentile(r2_specific, 95),
        'good_fit_pct': 100 * np.sum(r2_specific > 0.1) / len(r2_specific)
    }

# Summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)

if use_trial_type:
    print(f"\n{'Method':<20} {'R² Mean':<12} {'R² Median':<12} {'R² 95th':<12} {'Good>0.1%':<12}")
    print("-"*80)
    for method, vals in results.items():
        print(f"{method:<20} {vals['r2_mean']:>11.4f} {vals['r2_median']:>11.4f} "
              f"{vals['r2_95th']:>11.4f} {vals['good_fit_pct']:>11.1f}")

    # Calculate improvement
    improvement = results['COLOR_SPECIFIC']['r2_mean'] / results['COLOR_IGNORED']['r2_mean']

    print("\n" + "="*80)
    print("DIAGNOSIS:")
    print("="*80)

    if improvement > 2.0:
        print(f"\n  ✅ COLOR-SPECIFIC GLM is MUCH better! ({improvement:.1f}x improvement)")
        print(f"  → Color-ignored GLM was causing signal cancellation")
        print(f"  → MUST use color-specific GLM for B&H 2009 pipeline")
    elif improvement > 1.3:
        print(f"\n  ✓ COLOR-SPECIFIC GLM is better ({improvement:.1f}x improvement)")
        print(f"  → Moderate benefit from separating colors")
        print(f"  → Recommend using color-specific GLM")
    elif improvement < 0.8:
        print(f"\n  ⚠️  COLOR-SPECIFIC GLM is WORSE ({improvement:.1f}x)")
        print(f"  → This is unexpected - may indicate overfitting")
        print(f"  → Or colors truly don't elicit different responses")
    else:
        print(f"\n  → Similar performance ({improvement:.1f}x)")
        print(f"  → Color separation has minimal effect")

    if results['COLOR_SPECIFIC']['r2_mean'] > 0.15:
        print(f"\n  ✅ With color-specific GLM, R² = {results['COLOR_SPECIFIC']['r2_mean']:.4f}")
        print(f"  → This is acceptable for B&H 2009 pipeline")
    else:
        print(f"\n  🚨 Even with color-specific GLM, R² = {results['COLOR_SPECIFIC']['r2_mean']:.4f}")
        print(f"  → Signal is still weak")
        print(f"  → Additional investigation needed")
else:
    print("\n  ✗ Cannot test color-specific GLM without trial_type column")
    print(f"  → Need to check events.tsv format")

print("="*80)
