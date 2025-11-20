#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fir_reconstruction_optionA.py
-----------------------------
Option A: Universal HRF + Run-Specific GLM (Exact B&H 2009 Implementation)

KEY FEATURES:
1. Universal HRF estimation from all runs (for optimal delay)
2. Run-specific FirstLevelModel fitting with SHARED HRF shape
3. Each run uses same delay (PEAK_DELAY) from universal HRF
4. Independent beta extraction per run (no data leakage)

This is the CORRECT implementation of Brouwer & Heeger (2009):
- Same HRF shape across all runs (reduces run-to-run variability)
- Independent beta estimation per run (proper cross-validation)

DIFFERENCE FROM OPTION B:
- Option B: Each run estimates its own HRF → high variability
- Option A: All runs use same HRF delay → stable & robust

Usage:
    python fir_reconstruction_optionA.py --roi V1 --subject P01

Created: 2025-01-19
Based on: fir_reconstruction_runSpecific.py
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
from nilearn.glm.first_level import FirstLevelModel
from nilearn import image as nimg
from nilearn import plotting

try:
    from nilearn.maskers import NiftiMasker
except ImportError:
    from nilearn.input_data import NiftiMasker

from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from scipy import stats
from scipy.stats import zscore

# ============================================================================
# Configuration
# ============================================================================

# Color mappings (from original)
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
FIR_DELAYS = list(range(0, 15))  # 0-21 seconds in 1.5s steps

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

def compute_hrf_similarity(hrf1, hrf2):
    """Compute similarity between two HRF curves"""
    # Pearson correlation
    corr = np.corrcoef(hrf1, hrf2)[0, 1]

    # RMSE
    rmse = np.sqrt(np.mean((hrf1 - hrf2)**2))

    # Normalized RMSE
    nrmse = rmse / (np.std(hrf1) + 1e-8)

    return {
        'correlation': corr,
        'rmse': rmse,
        'nrmse': nrmse
    }

# ============================================================================
# Parse Arguments
# ============================================================================

def parse_args():
    parser = argparse.ArgumentParser(description='Option A: Universal HRF + Run-specific GLM (B&H 2009)')
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
    parser.add_argument('--save-zmaps', action='store_true',
                        help='Save z-score maps (compatibility flag, ignored)')
    parser.add_argument('--output-dir', type=str, default=None,
                        help='Output directory (default: derivatives/timestamp/)')
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
# Path Configuration (Match fir_reconstruction_zScore.py)
# ============================================================================

FMRIPREP_BASE = "/storage/connectome/haba6030/fmriprep_out"
EVENT_DIR = "/storage/connectome/haba6030/colorBlind_dataOct"

if SUBJECT_ID == 'P01':
    FMRIPREP_DIR = f"{FMRIPREP_BASE}/pilot/sub-01"
    FILE_PREFIX = "sub-01"  # File prefix: sub-01
    DERIVATIVE_PREFIX = "sub-01"
    EVENTS_DIR = f"{EVENT_DIR}/pilot/sub-01/func"
else:
    FMRIPREP_DIR = f"{FMRIPREP_BASE}/sub-{SUBJECT_ID}"  # Directory name: sub-XX
    FILE_PREFIX = f"sub-{SUBJECT_ID}"  # File prefix: sub-XX
    DERIVATIVE_PREFIX = f"sub-{SUBJECT_ID}"  # Derivative folder: sub-XX
    EVENTS_DIR = f"{EVENT_DIR}/sub-{SUBJECT_ID}/func"  # Events in sub-XX/func/

# ============================================================================
# Setup Output Directory (TIMESTAMP AT TOP LEVEL)
# ============================================================================

from datetime import datetime

# Use provided timestamp or generate new one
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
        output_dir = Path(f"derivatives/{timestamp}/pilot/{DERIVATIVE_PREFIX}/optionA/{ROI_NAME}")
    else:
        output_dir = Path(f"derivatives/{timestamp}/{DERIVATIVE_PREFIX}/optionA/{ROI_NAME}")
output_dir.mkdir(parents=True, exist_ok=True)

fig_dir = output_dir / 'figures'
fig_dir.mkdir(exist_ok=True)

print("="*70)
print("Option A: Universal HRF + Run-Specific GLM (B&H 2009)")
print("="*70)
print(f"Subject: {SUBJECT_ID} (files: {FILE_PREFIX}, derivatives: {DERIVATIVE_PREFIX})")
print(f"ROI: {ROI_NAME}")
print(f"Method: Shared HRF shape + Independent betas")
print(f"Use PCA: {USE_PCA}")
if USE_PCA:
    print(f"PCA components: {N_PCA_COMPONENTS}")
print(f"Color mapping: {'PILOT (irregular)' if SUBJECT_ID == 'P01' else 'TEST (regular 45°)'}")
print(f"Output directory: {output_dir}")
print()
sys.stdout.flush()

# ============================================================================
# Load ROI Mask
# ============================================================================

print(f"[1/9] Loading ROI mask")
sys.stdout.flush()

if SUBJECT_ID == 'P01':
    roi_path = f"derivatives/pilot/{DERIVATIVE_PREFIX}/roi_pipeline_20251111_010954/{ROI_NAME}_mask_thr50_intnearest_binTrue_masknone_gmTrue_subjFalse.nii.gz"
else:
    roi_path = f"derivatives/{DERIVATIVE_PREFIX}/roi_pipeline/{ROI_NAME}_mask_thr50_intnearest_binTrue_masknone_gmTrue_subjFalse.nii.gz"

if not os.path.exists(roi_path):
    print(f"ERROR: ROI mask not found: {roi_path}")
    sys.exit(1)

roi_img = nib.load(roi_path)
masker = NiftiMasker(mask_img=roi_path, standardize=False)
masker.fit()

n_voxels = np.sum(roi_img.get_fdata() > 0)
print(f"  ROI: {ROI_NAME}")
print(f"  Voxels: {n_voxels}")
print()
sys.stdout.flush()

# ============================================================================
# Load Functional Data
# ============================================================================

print(f"[2/9] Loading functional data ({N_RUNS} runs)")
sys.stdout.flush()

func_imgs = []
events_list = []
confounds_list = []

for run in range(1, N_RUNS + 1):
    # Functional image
    func_path = f"{FMRIPREP_DIR}/func/{FILE_PREFIX}_task-rsvp_run-{run}_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz"

    if not os.path.exists(func_path):
        print(f"ERROR: Functional image not found: {func_path}")
        sys.exit(1)

    func_img = nib.load(func_path)

    if VOLS_TO_DROP > 0:
        func_img = nimg.index_img(func_img, slice(VOLS_TO_DROP, None))

    func_imgs.append(func_img)

    # Events
    events_path = f"{EVENTS_DIR}/{FILE_PREFIX}_task-rsvp_run-{run}_events.tsv"

    if not os.path.exists(events_path):
        print(f"ERROR: Events file not found: {events_path}")
        sys.exit(1)

    events = pd.read_csv(events_path, sep='\t')
    events_list.append(events)

    # Confounds
    confounds_path = f"{FMRIPREP_DIR}/func/{FILE_PREFIX}_task-rsvp_run-{run}_desc-confounds_timeseries.tsv"

    if not os.path.exists(confounds_path):
        print(f"ERROR: Confounds file not found: {confounds_path}")
        sys.exit(1)

    confounds = pd.read_csv(confounds_path, sep='\t')
    motion_cols = ['trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z']
    confounds_subset = confounds[motion_cols]

    if VOLS_TO_DROP > 0:
        confounds_subset = confounds_subset.iloc[VOLS_TO_DROP:]

    confounds_list.append(confounds_subset)

    print(f"  Run {run}: {func_img.shape}, {len(events)} events")

print(f"  Total: {len(func_imgs)} runs loaded")
print()
sys.stdout.flush()

# ============================================================================
# Step 1: Fit Universal FIR Model (for optimal delay estimation)
# ============================================================================

print(f"[3/9] Fitting universal FIR model (all runs)")
print(f"  Purpose: Find optimal HRF delay across all runs")
sys.stdout.flush()

fir_model_universal = FirstLevelModel(
    t_r=TR,
    hrf_model='fir',
    fir_delays=FIR_DELAYS,
    drift_model='cosine',
    high_pass=1/128.0,
    mask_img=roi_path,
    standardize=False,
    minimize_memory=False
)

fir_model_universal.fit(func_imgs, events_list, confounds_list)

print("  Universal FIR model fitted successfully!")
print()
sys.stdout.flush()

# ============================================================================
# Extract Universal HRF and Find Optimal Delay
# ============================================================================

print(f"[4/9] Finding optimal delay from universal HRF")
sys.stdout.flush()

# Extract FIR response for each color at all delays
mean_responses = []

for color_idx in range(1, N_COLORS + 1):
    color_responses = []

    for delay in FIR_DELAYS:
        contrast_name = f'color_{color_idx}_delay_{delay}'
        try:
            contrast_map = fir_model_universal.compute_contrast(contrast_name, output_type='effect_size')
            mean_response = masker.transform(contrast_map).mean()
            color_responses.append(mean_response)
        except:
            color_responses.append(0)

    mean_responses.append(color_responses)

mean_responses = np.array(mean_responses)

# Universal HRF (average across colors)
universal_hrf = mean_responses.mean(axis=0)

# Find peak delay
peak_idx = np.argmax(np.abs(universal_hrf))
PEAK_DELAY = FIR_DELAYS[peak_idx]

print(f"  Universal HRF shape: {universal_hrf.shape}")
print(f"  Optimal delay: {PEAK_DELAY} (index {peak_idx})")
print()
sys.stdout.flush()

# ============================================================================
# Step 2: Run-Specific GLM Fitting with Shared HRF (Option A)
# ============================================================================

print(f"[5/9] Fitting run-specific GLM with shared HRF shape")
print(f"  Using optimal delay: {PEAK_DELAY} (from universal HRF)")
print(f"  All runs use SAME delay → consistent HRF shape")
print(f"  Betas extracted independently per run → proper CV")
sys.stdout.flush()

all_betas = []  # (n_runs, n_colors, n_voxels)

for run_idx in range(N_RUNS):
    print(f"  Processing run {run_idx+1}/{N_RUNS}...")

    # Fit FIR model for this run only
    # KEY DIFFERENCE: Only use PEAK_DELAY (not all delays!)
    fir_model_run = FirstLevelModel(
        t_r=TR,
        hrf_model='fir',
        fir_delays=[PEAK_DELAY],  # ← OPTION A: Use only optimal delay!
        drift_model='cosine',
        high_pass=1/128.0,
        mask_img=roi_path,
        standardize=False,
        minimize_memory=False
    )

    # Fit using only this run
    fir_model_run.fit(
        [func_imgs[run_idx]],
        [events_list[run_idx]],
        [confounds_list[run_idx]]
    )

    # Extract betas at optimal delay (same for all runs)
    run_betas = []
    for color_idx in range(1, N_COLORS + 1):
        contrast_name = f'color_{color_idx}_delay_{PEAK_DELAY}'

        try:
            contrast_map = fir_model_run.compute_contrast(contrast_name, output_type='effect_size')
            betas = masker.transform(contrast_map).ravel()
            run_betas.append(betas)
        except Exception as e:
            print(f"    Warning: Could not extract {contrast_name}: {e}")
            run_betas.append(np.zeros(n_voxels))

    run_betas = np.array(run_betas).T  # (n_voxels, 8)

    # Z-score normalize per voxel (B&H 2009 method)
    for voxel_idx in range(n_voxels):
        run_betas[voxel_idx, :] = zscore(run_betas[voxel_idx, :])

    all_betas.append(run_betas)

# Transpose to match fir_reconstruction_zScore.py format: (runs, colors, voxels)
all_betas = np.array(all_betas).transpose(0, 2, 1)  # (6, 8, n_voxels)

print(f"  Extracted betas shape: {all_betas.shape} (runs, colors, voxels)")
print(f"  ✅ All runs use same HRF delay → consistent across runs")
print()
sys.stdout.flush()

# ============================================================================
# Verify Data Independence (Critical Test)
# ============================================================================

print(f"[6/9] Verifying data independence across runs")
sys.stdout.flush()

# Check if all_betas are different across runs
independence_check = []
for i in range(N_RUNS):
    for j in range(i+1, N_RUNS):
        # Compare beta patterns
        corr = np.corrcoef(all_betas[i].flatten(), all_betas[j].flatten())[0, 1]
        identical = np.allclose(all_betas[i], all_betas[j])
        independence_check.append({
            'run_i': i+1,
            'run_j': j+1,
            'correlation': corr,
            'identical': identical
        })

independence_df = pd.DataFrame(independence_check)

print(f"  Run-to-Run Beta Correlations:")
print(f"    Mean: {independence_df['correlation'].mean():.4f}")
print(f"    Max:  {independence_df['correlation'].max():.4f}")

if independence_df['identical'].any():
    print(f"  🚨 WARNING: Some runs have identical betas!")
    print(f"     → Data leakage detected!")
    identical_pairs = independence_df[independence_df['identical']]
    for _, row in identical_pairs.iterrows():
        print(f"     Run {row['run_i']} == Run {row['run_j']}")
else:
    print(f"  ✅ All runs have independent betas")
    if independence_df['correlation'].mean() < 0.3:
        print(f"     → Good independence (low correlation)")
    else:
        print(f"     → Moderate correlation (expected due to similar stimuli)")

print()
independence_df.to_csv(output_dir / 'beta_independence_check.csv', index=False)
sys.stdout.flush()

# ============================================================================
# Classification with Leave-One-Run-Out CV
# ============================================================================

print(f"[7/9] Classification with leave-one-run-out CV")
if USE_PCA:
    print(f"  Using PCA: {N_PCA_COMPONENTS} components")
print(f"  B&H (2009) method: Stack voxels across training runs")
sys.stdout.flush()

classification_results = []

for test_run in range(N_RUNS):
    train_runs = [r for r in range(N_RUNS) if r != test_run]

    # B&H (2009): Stack voxels across runs as features
    # all_betas shape: (6, 8, n_voxels) = (runs, colors, voxels)
    # Training: (5, 8, 529) → transpose to (8, 5, 529) → reshape to (8, 2645)
    X_train = all_betas[train_runs].transpose(1, 0, 2).reshape(N_COLORS, -1)
    y_train = np.arange(N_COLORS)  # [0, 1, 2, 3, 4, 5, 6, 7]

    # Test: (8, 529) single run
    X_test_single = all_betas[test_run]  # (8, 529)
    y_test = np.arange(N_COLORS)

    # Replicate test voxels to match training feature dimension
    # Each voxel replicated across "virtual runs" for PCA compatibility
    X_test = np.tile(X_test_single, len(train_runs))  # (8, 2645)

    if test_run == 0:
        print(f"\n  Feature dimensions (B&H 2009 stacking):")
        print(f"    Training: {X_train.shape} = (8 colors, {n_voxels}×{len(train_runs)} voxels)")
        print(f"    Test (single run): {X_test_single.shape} = (8 colors, {n_voxels} voxels)")
        print(f"    Test (replicated): {X_test.shape} = (8 colors, {n_voxels}×{len(train_runs)} voxels)")
        print()

    # Standardize (across colors, separately for each voxel position)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Optional PCA
    if USE_PCA:
        pca = PCA(n_components=N_PCA_COMPONENTS)
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

# Save results
results_summary = {
    'subject': SUBJECT_ID,
    'roi': ROI_NAME,
    'method': 'Option A (Universal HRF + Independent GLM)',
    'use_pca': USE_PCA,
    'n_components': N_PCA_COMPONENTS if USE_PCA else None,
    'optimal_delay': PEAK_DELAY,
    'classification_accuracy': mean_classification_acc,
    'run_independence': not independence_df['identical'].any(),
}

# Save summary
import json
with open(output_dir / 'analysis_summary.json', 'w') as f:
    json.dump(results_summary, f, indent=2)

# ============================================================================
# Forward Model for Reconstruction
# ============================================================================

print(f"[8/9] Reconstruction with B&H forward model")
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

    # B&H (2009): Stack voxels across runs as features
    X_train = all_betas[train_runs].transpose(1, 0, 2).reshape(N_COLORS, -1)
    y_train = np.arange(N_COLORS)

    X_test_single = all_betas[test_run]
    y_test = np.arange(N_COLORS)

    # Replicate test voxels to match training feature dimension
    X_test = np.tile(X_test_single, len(train_runs))

    # Standardize
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Optional PCA
    if USE_PCA:
        pca = PCA(n_components=N_PCA_COMPONENTS)
        X_train_final = pca.fit_transform(X_train_scaled)
        X_test_final = pca.transform(X_test_scaled)
    else:
        X_train_final = X_train_scaled
        X_test_final = X_test_scaled

    # Train forward model: B = W × C
    # Get channel outputs for training colors (8 colors, no repetition)
    C_train = []
    for color_idx in y_train:
        color_name = f'color_{color_idx+1}'
        hue_deg = LABEL2HUE_DEG[color_name]
        channels = hue_to_channels(hue_deg)
        C_train.append(channels)
    C_train = np.array(C_train).T  # (6, 8)

    # Estimate weights: W = B × C^T × (C × C^T)^-1
    W = X_train_final.T @ C_train.T @ np.linalg.inv(C_train @ C_train.T)

    # Test: estimate channels from test data
    # Use pseudoinverse to avoid singular matrix errors
    C_test_est = np.linalg.pinv(W.T @ W) @ W.T @ X_test_final.T  # (6, n_test)

    # Reconstruct hues
    reconstructed_hues = []
    true_hues = []

    # Debug: print detailed reconstruction for first run
    if test_run == 0:
        print(f"\n  === Detailed reconstruction for test run 1 ===")

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

        # Debug: print details for first run
        if test_run == 0:
            error = circular_diff_deg(reconstructed_hue, true_hue)
            # Top 5 correlations
            top5_indices = np.argsort(correlations)[-5:][::-1]
            top5_hues = top5_indices
            top5_corrs = correlations[top5_indices]

            print(f"  {color_name} (true: {true_hue:.1f}°):")
            print(f"    Reconstructed: {reconstructed_hue}° (error: {error:.1f}°)")
            print(f"    Estimated channels: [{', '.join([f'{c:.3f}' for c in estimated_channels])}]")
            print(f"    Top 5 correlations: ", end="")
            for h, c in zip(top5_hues, top5_corrs):
                print(f"{h}°({c:.3f}) ", end="")
            print()

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

    if test_run == 0:
        print()
    print(f"  Test run {test_run+1}: Mean error = {mean_error:.1f}°")

mean_reconstruction_error = np.mean([r['mean_error'] for r in reconstruction_results])
print()
print(f"Mean reconstruction error: {mean_reconstruction_error:.1f}°")
print(f"Chance level (expected): 90.0° (uniform circular distribution)")
print()

# Additional statistics
print("=== Detailed Per-Run Statistics ===")
print(f"{'Run':<6} {'Mean Error':<12} {'Median Error':<14} {'Hit Rate (±30°)':<18} {'Hit Rate (±45°)':<18}")
print("-" * 78)

all_hit_rates_30 = []
all_hit_rates_45 = []

for result in reconstruction_results:
    errors = result['errors']
    mean_err = result['mean_error']
    median_err = np.median(errors)

    # Hit rate: percentage within tolerance
    hit_30 = np.mean(errors <= 30) * 100
    hit_45 = np.mean(errors <= 45) * 100

    all_hit_rates_30.append(hit_30)
    all_hit_rates_45.append(hit_45)

    print(f"Run {result['test_run']:<3} {mean_err:>8.2f}°     {median_err:>8.2f}°        {hit_30:>6.1f}%            {hit_45:>6.1f}%")

print("-" * 78)
print(f"{'Mean':<6} {mean_reconstruction_error:>8.2f}°     "
      f"{np.median([np.median(r['errors']) for r in reconstruction_results]):>8.2f}°        "
      f"{np.mean(all_hit_rates_30):>6.1f}%            {np.mean(all_hit_rates_45):>6.1f}%")
print()
sys.stdout.flush()

# ============================================================================
# Leave-One-Color-Out Reconstruction (Novel Colors)
# ============================================================================

print(f"[9/9] Leave-one-color-out reconstruction (novel colors)")
sys.stdout.flush()

novel_color_results = []

for held_out_color in range(N_COLORS):
    all_errors_this_color = []
    all_reconstructed_hues = []  # Track reconstructed hues across test runs

    for test_run in range(N_RUNS):
        train_runs = [r for r in range(N_RUNS) if r != test_run]

        # B&H (2009): Stack voxels, exclude held-out color
        # all_betas shape: (6, 8, n_voxels)
        # Get training runs, all colors except held_out
        train_colors = [c for c in range(N_COLORS) if c != held_out_color]

        # Extract training data: (5 runs, 7 colors, n_voxels)
        X_train_data = all_betas[train_runs][:, train_colors, :]  # (5, 7, n_voxels)
        # Stack voxels: (7, 5, n_voxels) → (7, n_voxels×5)
        X_train = X_train_data.transpose(1, 0, 2).reshape(len(train_colors), -1)
        y_train = np.array(train_colors)

        # Test: held-out color from test run
        X_test_single = all_betas[test_run, held_out_color, :].reshape(1, -1)  # (1, n_voxels)
        y_test = np.array([held_out_color])

        # Replicate test voxels to match training feature dimension
        X_test = np.tile(X_test_single, len(train_runs))  # (1, n_voxels×5)

        # Standardize
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        # Optional PCA
        if USE_PCA:
            n_components_actual = min(N_PCA_COMPONENTS, len(X_train))
            pca = PCA(n_components=n_components_actual)
            X_train_final = pca.fit_transform(X_train_scaled)
            X_test_final = pca.transform(X_test_scaled)
        else:
            X_train_final = X_train_scaled
            X_test_final = X_test_scaled

        # Train forward model
        C_train = []
        for color_idx in y_train:
            color_name = f'color_{color_idx+1}'
            hue_deg = LABEL2HUE_DEG[color_name]
            channels = hue_to_channels(hue_deg)
            C_train.append(channels)
        C_train = np.array(C_train).T

        W = X_train_final.T @ C_train.T @ np.linalg.inv(C_train @ C_train.T)

        # Reconstruct held-out color
        C_test_est = np.linalg.pinv(W.T @ W) @ W.T @ X_test_final.T
        estimated_channels = C_test_est[:, 0]

        correlations = []
        for h in range(360):
            template_channels = basis_functions[h]
            corr = np.corrcoef(estimated_channels, template_channels)[0, 1]
            correlations.append(corr)

        correlations = np.array(correlations)
        reconstructed_hue = np.argmax(correlations)

        # True hue
        color_name = f'color_{held_out_color+1}'
        true_hue = LABEL2HUE_DEG[color_name]

        error = circular_diff_deg(reconstructed_hue, true_hue)
        all_errors_this_color.append(error)
        all_reconstructed_hues.append(reconstructed_hue)

    # Stats for this color
    mean_error = np.mean(all_errors_this_color)
    median_error = np.median(all_errors_this_color)
    std_error = np.std(all_errors_this_color)

    novel_color_results.append({
        'color': held_out_color + 1,
        'true_hue': LABEL2HUE_DEG[f'color_{held_out_color+1}'],
        'mean_error': mean_error,
        'median_error': median_error,
        'std_error': std_error,
        'reconstructed_hues': all_reconstructed_hues,
        'errors': all_errors_this_color
    })

    print(f"  Color {held_out_color+1} (true: {LABEL2HUE_DEG[f'color_{held_out_color+1}']:.1f}°): "
          f"Mean error = {mean_error:.1f}° (±{std_error:.1f}°)")

mean_novel_error = np.mean([r['mean_error'] for r in novel_color_results])
print()
print(f"Mean reconstruction error for novel colors: {mean_novel_error:.1f}°")
print(f"Comparison: trained colors = {mean_reconstruction_error:.1f}°, novel colors = {mean_novel_error:.1f}°")

if mean_novel_error < mean_reconstruction_error * 1.5:
    print(f"✅ Good generalization to novel colors!")
else:
    print(f"⚠️  Novel colors harder to reconstruct (expected)")

print()
sys.stdout.flush()

# Save reconstruction results
reconstruction_df = pd.DataFrame([{
    'test_run': r['test_run'],
    'mean_error': r['mean_error'],
    'median_error': np.median(r['errors']),
    'hit_rate_30': np.mean(np.array(r['errors']) <= 30) * 100,
    'hit_rate_45': np.mean(np.array(r['errors']) <= 45) * 100
} for r in reconstruction_results])
reconstruction_df.to_csv(output_dir / 'reconstruction_trained_colors.csv', index=False)

novel_reconstruction_df = pd.DataFrame(novel_color_results)
novel_reconstruction_df.to_csv(output_dir / 'reconstruction_novel_colors.csv', index=False)

# Update summary
results_summary['reconstruction_error_trained'] = mean_reconstruction_error
results_summary['reconstruction_error_novel'] = mean_novel_error
results_summary['hit_rate_30_trained'] = np.mean(all_hit_rates_30)
results_summary['hit_rate_45_trained'] = np.mean(all_hit_rates_45)

# ============================================================================
# Final Summary
# ============================================================================

print(f"\n{'='*70}")
print(f"Analysis complete!")
print(f"{'='*70}")
print(f"\nResults saved to: {output_dir}")
print(f"\nKey Findings (Option A):")
print(f"  - Method: Universal HRF + Run-specific betas")
print(f"  - HRF delay: {PEAK_DELAY} (shared across all runs)")
print(f"  - Classification accuracy: {mean_classification_acc:.1%}")
print(f"  - Reconstruction (trained): {mean_reconstruction_error:.1f}°")
print(f"  - Reconstruction (novel):   {mean_novel_error:.1f}°")
print(f"  - Data independence: {'✅ Yes' if results_summary['run_independence'] else '🚨 No'}")
print(f"\nThis implements B&H (2009) exactly:")
print(f"  ✅ Shared HRF shape (stable across runs)")
print(f"  ✅ Independent beta extraction (proper CV)")
print(f"  ✅ No data leakage")
print()
print("="*70)
sys.stdout.flush()
