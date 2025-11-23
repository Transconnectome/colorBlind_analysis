#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fir_per_run_simple.py
----------------------------------
Per-run FIR GLM → use amplitudes directly for classification

APPROACH:
1. Per-run FIR GLM: β[run, color, voxel, delay]
   - These β values ARE the amplitudes
2. Use amplitudes directly (with different strategies)
3. Z-score and classify

PIPELINE:
Step 1: Per-run FIR GLM
  For each run:
    X_FIR = design matrix (8 colors × 8 delays = 64 columns)
    β = pinv(X_FIR) @ y
    Store: β[run, color, voxel, delay]

Step 2: Use amplitudes
  Strategy A: Flatten all delays → features = [run, color, voxel×delay]
  Strategy B: Average across delays → features = [run, color, voxel]
  Strategy C: Use specific delay range

Step 3: Z-score per run per voxel

Step 4: Classification with leave-one-run-out CV

Usage:
    python fir_per_run_simple.py --roi V1 --subject P01 --strategy flatten

Created: 2025-01-20
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
from nilearn.signal import clean

try:
    from nilearn.maskers import NiftiMasker
except ImportError:
    from nilearn.input_data import NiftiMasker

from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from scipy.stats import zscore

# ============================================================================
# Configuration
# ============================================================================

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

TR = 1.5
N_RUNS = 6
N_COLORS = 8
VOLS_TO_DROP = 4
FIR_DELAYS = np.arange(8)  # 0-10.5s

# ============================================================================
# Helper Functions
# ============================================================================

def diag_linear_predict(train_X, train_y, test_X):
    """Diagonal LDA"""
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
    return classes[ll.argmax(axis=1)]

def build_color_fir_design(events, n_scans, tr, fir_delays, n_colors=8):
    """Build color-specific FIR design matrix"""
    n_delays = len(fir_delays)
    X = np.zeros((n_scans, n_colors * n_delays))

    for color_idx in range(1, n_colors + 1):
        color_name = f'color_{color_idx}'
        color_events = events[events['trial_type'] == color_name]

        for onset in color_events['onset'].values:
            onset_tr = int(np.round(onset / tr))
            for i, delay in enumerate(fir_delays):
                tr_idx = onset_tr + delay
                if 0 <= tr_idx < n_scans:
                    col_idx = (color_idx - 1) * n_delays + i
                    X[tr_idx, col_idx] = 1.0
    return X

# ============================================================================
# Parse Arguments
# ============================================================================

parser = argparse.ArgumentParser()
parser.add_argument('--subject', type=str, default='P01')
parser.add_argument('--roi', type=str, default='V1')
parser.add_argument('--strategy', type=str, default='flatten',
                    choices=['flatten', 'average', 'delay3', 'delay4', 'delay5'],
                    help='How to use FIR amplitudes')
parser.add_argument('--use-pca', action='store_true')
parser.add_argument('--n-components', type=int, default=6)
parser.add_argument('--timestamp', type=str, default=None)
args = parser.parse_args()

SUBJECT_ID = args.subject
ROI_NAME = args.roi
STRATEGY = args.strategy
USE_PCA = args.use_pca
N_PCA_COMPONENTS = args.n_components

IS_PILOT = (SUBJECT_ID == 'P01')
LABEL2HUE_DEG = LABEL2HUE_DEG_PILOT if IS_PILOT else LABEL2HUE_DEG_TEST

# ============================================================================
# Paths
# ============================================================================

FMRIPREP_BASE = "/storage/connectome/haba6030/fmriprep_out"
EVENT_DIR = "/storage/connectome/haba6030/colorBlind_dataOct"

if IS_PILOT:
    FMRIPREP_DIR = f"{FMRIPREP_BASE}/pilot/sub-01"
    FILE_PREFIX = "sub-01"
    EVENTS_DIR = f"{EVENT_DIR}/pilot/sub-01/func"
    DERIVATIVE_PREFIX = "pilot/sub-01"
else:
    FMRIPREP_DIR = f"{FMRIPREP_BASE}/sub-{SUBJECT_ID}"
    FILE_PREFIX = f"sub-{SUBJECT_ID}"
    EVENTS_DIR = f"{EVENT_DIR}/sub-{SUBJECT_ID}/func"
    DERIVATIVE_PREFIX = f"sub-{SUBJECT_ID}"

# Output
from datetime import datetime
timestamp = args.timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")

pca_suffix = f"_pca{N_PCA_COMPONENTS}" if USE_PCA else ""
output_dir = Path(f"derivatives/fir_simple/{DERIVATIVE_PREFIX}/{timestamp}_{ROI_NAME}_{STRATEGY}{pca_suffix}")
output_dir.mkdir(parents=True, exist_ok=True)
fig_dir = output_dir / 'figures'
fig_dir.mkdir(exist_ok=True)

print("="*70)
print("Per-Run FIR GLM (Simple)")
print("="*70)
print(f"Subject: {SUBJECT_ID}")
print(f"ROI: {ROI_NAME}")
print(f"Strategy: {STRATEGY}")
print(f"Use PCA: {USE_PCA}" + (f" (n={N_PCA_COMPONENTS})" if USE_PCA else ""))
print(f"Output: {output_dir}")
print()
sys.stdout.flush()

# ============================================================================
# Load ROI Mask
# ============================================================================

print(f"[1/5] Loading ROI mask")

if IS_PILOT:
    roi_path = f"derivatives/pilot/sub-01/roi_pipeline_20251111_010954/{ROI_NAME}_mask_thr50_intnearest_binTrue_masknone_gmTrue_subjFalse.nii.gz"
else:
    roi_path = f"derivatives/sub-{SUBJECT_ID}/roi_pipeline/{ROI_NAME}_mask_thr50_intnearest_binTrue_masknone_gmTrue_subjFalse.nii.gz"

if not os.path.exists(roi_path):
    print(f"ERROR: {roi_path} not found")
    sys.exit(1)

roi_img = nib.load(roi_path)
n_voxels = int(np.sum(roi_img.get_fdata() > 0))
print(f"  ROI voxels: {n_voxels}")

masker = NiftiMasker(mask_img=roi_img, standardize=False)
masker.fit()
print()

# ============================================================================
# Load Data
# ============================================================================

print(f"[2/5] Loading {N_RUNS} runs")

all_func_data = []
events_list = []

for run in range(1, N_RUNS + 1):
    func_path = f"{FMRIPREP_DIR}/func/{FILE_PREFIX}_task-rsvp_run-{run}_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz"
    confounds_path = f"{FMRIPREP_DIR}/func/{FILE_PREFIX}_task-rsvp_run-{run}_desc-confounds_timeseries.tsv"
    events_path = f"{EVENTS_DIR}/{FILE_PREFIX}_task-rsvp_run-{run}_events.tsv"

    func_img = nib.load(func_path)
    if VOLS_TO_DROP > 0:
        func_img = nimg.index_img(func_img, slice(VOLS_TO_DROP, None))

    confounds = pd.read_csv(confounds_path, sep='\t')
    motion = confounds[['trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z']]
    if VOLS_TO_DROP > 0:
        motion = motion.iloc[VOLS_TO_DROP:]

    func_data = masker.transform(func_img)
    func_clean = clean(func_data, confounds=motion.values, detrend=True,
                      standardize=False, standardize_confounds=True,
                      high_pass=None, t_r=TR)
    all_func_data.append(func_clean)

    events = pd.read_csv(events_path, sep='\t')
    if VOLS_TO_DROP > 0:
        events['onset'] = events['onset'] - (VOLS_TO_DROP * TR)
        events = events[events['onset'] >= 0].reset_index(drop=True)
    events_list.append(events)

    print(f"  Run {run}: {func_clean.shape[0]} scans, {len(events)} events")

print()

# ============================================================================
# Step 1: Per-Run FIR GLM
# ============================================================================

print(f"[3/5] Per-run FIR GLM")
print(f"  Extracting FIR amplitudes: (runs={N_RUNS}, colors={N_COLORS}, voxels={n_voxels}, delays={len(FIR_DELAYS)})")

# These ARE the amplitudes (no further deconvolution needed)
amplitudes = np.zeros((N_RUNS, N_COLORS, n_voxels, len(FIR_DELAYS)))

for run_idx in range(N_RUNS):
    print(f"  Run {run_idx+1}/{N_RUNS}...", end='')

    y = all_func_data[run_idx]
    n_scans = y.shape[0]

    X = build_color_fir_design(events_list[run_idx], n_scans, TR, FIR_DELAYS, N_COLORS)

    # FIR deconvolution: β = pinv(X) @ y
    # These β values ARE the amplitudes at each delay
    betas = np.linalg.pinv(X) @ y  # (n_colors × n_delays, n_voxels)

    # Reshape to (colors, delays, voxels) then transpose to (colors, voxels, delays)
    betas_reshaped = betas.reshape(N_COLORS, len(FIR_DELAYS), n_voxels)
    amplitudes[run_idx] = np.transpose(betas_reshaped, (0, 2, 1))

    print(f" mean={np.mean(amplitudes[run_idx]):.4f}, std={np.std(amplitudes[run_idx]):.4f}")

print(f"\n  FIR amplitudes shape: {amplitudes.shape}")
print()

# ============================================================================
# Step 2: Apply Strategy
# ============================================================================

print(f"[4/5] Applying strategy: {STRATEGY}")

if STRATEGY == 'flatten':
    # Use all delays: flatten to (runs, colors, voxels × delays)
    features = amplitudes.reshape(N_RUNS, N_COLORS, -1)
    print(f"  Flattened all delays: {features.shape}")

elif STRATEGY == 'average':
    # Average across all delays
    features = np.mean(amplitudes, axis=3)
    print(f"  Averaged across delays: {features.shape}")

elif STRATEGY.startswith('delay'):
    # Use specific delay
    delay_idx = int(STRATEGY[-1])
    features = amplitudes[:, :, :, delay_idx]
    print(f"  Using delay {delay_idx} ({delay_idx*TR:.1f}s): {features.shape}")

print()

# ============================================================================
# Step 3: Z-score
# ============================================================================

print(f"  Z-scoring per run per voxel...")

if STRATEGY == 'flatten':
    # For flattened, we need to z-score carefully
    # Z-score across colors only (not across voxels×delays)
    # Actually for flatten, we do z-score per (run, voxel, delay) across colors
    z_features = np.zeros_like(features)

    n_voxels_delays = features.shape[2]
    n_voxels_orig = n_voxels
    n_delays = len(FIR_DELAYS)

    for run_idx in range(N_RUNS):
        for vd_idx in range(n_voxels_delays):
            # Each vd_idx represents a (voxel, delay) pair
            vals = features[run_idx, :, vd_idx]  # 8 colors
            if np.std(vals) > 0:
                z_features[run_idx, :, vd_idx] = zscore(vals)
            else:
                z_features[run_idx, :, vd_idx] = 0
else:
    # For non-flatten, z-score per (run, voxel) across colors
    z_features = np.zeros_like(features)

    for run_idx in range(N_RUNS):
        for voxel_idx in range(n_voxels):
            vals = features[run_idx, :, voxel_idx]  # 8 colors
            if np.std(vals) > 0:
                z_features[run_idx, :, voxel_idx] = zscore(vals)
            else:
                z_features[run_idx, :, voxel_idx] = 0

print(f"  Z-scored features: {z_features.shape}")
print(f"  Mean: {np.mean(z_features):.6f}, Std: {np.std(z_features):.6f}")
print()

# ============================================================================
# Step 4: Classification
# ============================================================================

print(f"[5/5] Classification (leave-one-run-out)")

results = []

for test_run in range(N_RUNS):
    train_runs = [r for r in range(N_RUNS) if r != test_run]

    # Prepare data
    X_train = z_features[train_runs].reshape(-1, z_features.shape[2])
    y_train = np.tile(np.arange(N_COLORS), len(train_runs))

    X_test = z_features[test_run]
    y_test = np.arange(N_COLORS)

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

    # Classify
    y_pred = diag_linear_predict(X_train_final, y_train, X_test_final)
    acc = (y_pred == y_test).mean()

    results.append({'test_run': test_run+1, 'accuracy': acc})
    print(f"  Test run {test_run+1}: {acc:.3f} ({acc*100:.1f}%)")

mean_acc = np.mean([r['accuracy'] for r in results])
print(f"\n  Mean accuracy: {mean_acc:.3f} ({mean_acc*100:.1f}%)")
print(f"  Chance: {1/N_COLORS:.3f} ({100/N_COLORS:.1f}%)")
print()

# ============================================================================
# Visualization
# ============================================================================

print("Creating visualizations...")

# Plot 1: Mean FIR per color
fig, axes = plt.subplots(2, 4, figsize=(20, 10))
fig.suptitle(f'{ROI_NAME}: Mean FIR Amplitude Per Color (Strategy: {STRATEGY})',
             fontsize=16, fontweight='bold')

times = FIR_DELAYS * TR

for c in range(N_COLORS):
    ax = axes[c // 4, c % 4]

    # Mean across runs and voxels
    mean_amp = np.mean(amplitudes[:, c, :, :], axis=(0, 1))
    sem_amp = np.std(amplitudes[:, c, :, :], axis=(0, 1)) / np.sqrt(N_RUNS * n_voxels)

    ax.errorbar(times, mean_amp, yerr=sem_amp, fmt='o-', capsize=5, linewidth=2)
    ax.axhline(0, color='gray', linestyle=':', alpha=0.5)

    # Mark strategy
    if STRATEGY.startswith('delay'):
        delay_idx = int(STRATEGY[-1])
        ax.axvline(delay_idx * TR, color='red', linestyle='--', alpha=0.7,
                   label=f'Used ({delay_idx*TR:.1f}s)')
        ax.legend()

    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Amplitude')
    ax.set_title(f'Color {c+1}')
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(fig_dir / 'fir_per_color.png', dpi=300)
plt.close()

# Plot 2: Classification results
fig, ax = plt.subplots(figsize=(10, 6))

runs = [r['test_run'] for r in results]
accs = [r['accuracy'] for r in results]

bars = ax.bar(runs, accs, edgecolor='black', alpha=0.7, color='steelblue')
ax.axhline(mean_acc, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_acc:.3f}')
ax.axhline(1/N_COLORS, color='gray', linestyle=':', linewidth=2, label='Chance')
ax.set_xlabel('Test Run')
ax.set_ylabel('Classification Accuracy')
ax.set_title(f'{ROI_NAME}: Classification Performance\nStrategy: {STRATEGY}')
ax.set_ylim([0, 1])
ax.legend()
ax.grid(True, alpha=0.3, axis='y')

for bar, acc in zip(bars, accs):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + 0.02,
            f'{acc:.3f}', ha='center', va='bottom', fontweight='bold')

plt.tight_layout()
plt.savefig(fig_dir / 'classification_results.png', dpi=300)
plt.close()

print(f"  Saved to: {fig_dir}")
print()

# ============================================================================
# Save Results
# ============================================================================

print("Saving results...")

import json
summary = {
    'subject': SUBJECT_ID,
    'roi': ROI_NAME,
    'strategy': STRATEGY,
    'use_pca': USE_PCA,
    'n_pca_components': N_PCA_COMPONENTS if USE_PCA else None,
    'n_voxels': int(n_voxels),
    'n_delays': len(FIR_DELAYS),
    'mean_accuracy': float(mean_acc),
    'per_run_results': results,
}

with open(output_dir / 'summary.json', 'w') as f:
    json.dump(summary, f, indent=2)

np.save(output_dir / 'amplitudes.npy', amplitudes)
np.save(output_dir / 'z_features.npy', z_features)

print()
print("="*70)
print("Complete!")
print("="*70)
print(f"\nResults:")
print(f"  Strategy: {STRATEGY}")
print(f"  Classification: {mean_acc:.1%}")
print(f"  Saved to: {output_dir}")
print()
