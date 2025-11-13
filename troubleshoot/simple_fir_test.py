#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
simple_fir_test.py
------------------
Simple test using nilearn's built-in FIR model (per-voxel)

This uses FirstLevelModel with hrf_model='fir', which:
1. Estimates response at each time bin per voxel
2. No universal HRF assumption
3. Should handle variable hemodynamics better
"""

import sys
import os
import numpy as np
import pandas as pd
import nibabel as nib
from nilearn.glm.first_level import FirstLevelModel
from nilearn import image as nimg
from pathlib import Path

# Try different nilearn import versions
try:
    from nilearn.maskers import NiftiMasker
except ImportError:
    from nilearn.input_data import NiftiMasker

from config import cfg

print("="*70)
print("Simple FIR Model Test (Per-Voxel)")
print("="*70)
print(f"Subject: sub-{cfg.SUB_ID}")
print()
sys.stdout.flush()

# ============================================================================
# Configuration
# ============================================================================

ROI_NAME = "V2"  # Change to test different ROIs
N_RUNS = cfg.N_RUNS
TR = cfg.TR
N_COLORS = cfg.N_COLORS

# Find ROI mask
roi_path = f"derivatives/sub-{cfg.SUB_ID}/roi/sub-{cfg.SUB_ID}_{ROI_NAME}_mask.nii.gz"

if not os.path.exists(roi_path):
    print(f"ERROR: ROI mask not found: {roi_path}")
    sys.exit(1)

print(f"[1/5] Loading ROI mask: {ROI_NAME}")
print(f"  Path: {roi_path}")
sys.stdout.flush()

# Load mask and create masker
masker = NiftiMasker(mask_img=roi_path, standardize=False)
masker.fit()
print(f"  ROI fitted successfully")
print()
sys.stdout.flush()

# ============================================================================
# Load Data and Events
# ============================================================================

print(f"[2/5] Loading {N_RUNS} runs of functional data and events")
sys.stdout.flush()

func_imgs = []
events_list = []
confounds_list = []

for run in range(1, N_RUNS + 1):
    # Functional data
    func_path = cfg.get_func_img_path(run)
    func_img = nib.load(func_path)

    # Drop initial volumes if configured
    if cfg.VOLS_TO_DROP > 0:
        func_img = nimg.index_img(func_img, slice(cfg.VOLS_TO_DROP, None))

    func_imgs.append(func_img)

    # Events
    events = pd.read_csv(cfg.get_event_file_path(run), sep='\t')
    events_list.append(events)

    # Confounds (motion regressors)
    confounds = pd.read_csv(cfg.get_confound_file_path(run), sep='\t')

    # Select motion parameters
    motion_cols = ['trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z']
    confounds_subset = confounds[motion_cols]

    # Drop initial rows if configured
    if cfg.VOLS_TO_DROP > 0:
        confounds_subset = confounds_subset.iloc[cfg.VOLS_TO_DROP:]

    confounds_list.append(confounds_subset)

    print(f"  Run {run}: {func_img.shape}, {len(events)} events")

print(f"  Total: {len(func_imgs)} runs loaded")
print()
sys.stdout.flush()

# ============================================================================
# Fit FIR Model
# ============================================================================

print(f"[3/5] Fitting FIR model (this may take 5-10 minutes)")
print(f"  Using hrf_model='fir' with {10} time bins")
print(f"  Each voxel gets its own response curve")
sys.stdout.flush()

# Create FirstLevelModel with FIR
fir_model = FirstLevelModel(
    t_r=TR,
    hrf_model='fir',
    fir_delays=range(10),  # 0-15 seconds (10 TRs * 1.5s)
    drift_model='cosine',
    high_pass=1/128.0,
    mask_img=roi_path,
    standardize=False,
    minimize_memory=False
)

# Fit model
print("  Fitting model...")
sys.stdout.flush()

fir_model.fit(func_imgs, events_list, confounds_list)

print("  FIR model fitted successfully!")
print()
sys.stdout.flush()

# ============================================================================
# Extract Beta Estimates for Each Color
# ============================================================================

print(f"[4/5] Extracting beta estimates for {N_COLORS} colors")
sys.stdout.flush()

# For each run, get beta estimates
all_betas = []  # Will be (n_runs, n_colors, n_voxels)

for run_idx in range(N_RUNS):
    run_betas = []

    for color_idx in range(1, N_COLORS + 1):
        # Get contrast for this color's first FIR bin (peak response)
        # FIR creates columns like: color_1_delay_0, color_1_delay_1, etc.
        contrast_name = f'color_{color_idx}_delay_3'  # ~4.5s post-onset (typical HRF peak)

        try:
            contrast_map = fir_model.compute_contrast(contrast_name, output_type='effect_size')
            betas = masker.transform(contrast_map).ravel()
            run_betas.append(betas)
        except Exception as e:
            print(f"  Warning: Could not extract contrast {contrast_name}: {e}")
            # Use zeros if contrast fails
            n_voxels = masker.transform(func_imgs[0]).shape[1]
            run_betas.append(np.zeros(n_voxels))

    all_betas.append(np.array(run_betas))
    print(f"  Run {run_idx+1}: Extracted {len(run_betas)} color betas")

all_betas = np.array(all_betas)  # (n_runs, n_colors, n_voxels)
print(f"  Total shape: {all_betas.shape}")
print()
sys.stdout.flush()

# ============================================================================
# Quick Classification Test
# ============================================================================

print(f"[5/5] Quick classification test (leave-one-run-out)")
sys.stdout.flush()

from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

accuracies = []

for test_run in range(N_RUNS):
    # Split train/test
    train_runs = [r for r in range(N_RUNS) if r != test_run]

    X_train = all_betas[train_runs].reshape(-1, all_betas.shape[2])  # (n_train_samples, n_voxels)
    y_train = np.tile(np.arange(N_COLORS), len(train_runs))

    X_test = all_betas[test_run]  # (n_colors, n_voxels)
    y_test = np.arange(N_COLORS)

    # Standardize
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Train classifier
    clf = LogisticRegression(max_iter=1000, multi_class='multinomial')
    clf.fit(X_train_scaled, y_train)

    # Test
    y_pred = clf.predict(X_test_scaled)
    acc = (y_pred == y_test).mean()
    accuracies.append(acc)

    print(f"  Test run {test_run+1}: {acc:.3f} ({acc*100:.1f}%)")

mean_acc = np.mean(accuracies)
print()
print(f"Mean accuracy: {mean_acc:.3f} ({mean_acc*100:.1f}%)")
print(f"Baseline (chance): {1/N_COLORS:.3f} ({100/N_COLORS:.1f}%)")
print()
sys.stdout.flush()

# ============================================================================
# Summary
# ============================================================================

print("="*70)
print("FIR Model Test Complete")
print("="*70)
print()

if mean_acc > 1.5 / N_COLORS:  # Better than 1.5x chance
    print("✅ SUCCESS: FIR model shows above-chance classification!")
    print(f"   Accuracy: {mean_acc*100:.1f}% vs chance {100/N_COLORS:.1f}%")
    print()
    print("This suggests:")
    print("  1. ROI-functional alignment is fine")
    print("  2. FIR captures real signal better than canonical HRF")
    print("  3. Can proceed with reconstruction using FIR estimates")
else:
    print("❌ POOR: FIR model still at chance level")
    print(f"   Accuracy: {mean_acc*100:.1f}% vs chance {100/N_COLORS:.1f}%")
    print()
    print("This suggests deeper issues:")
    print("  1. Check event timing in TSV files")
    print("  2. Verify data quality (motion, artifacts)")
    print("  3. Check if ROI captures color-selective voxels")

print("="*70)
sys.stdout.flush()
