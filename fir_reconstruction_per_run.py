#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fir_reconstruction_per_run.py
----------------------------------
Per-run FIR GLM without any HRF averaging

KEY APPROACH:
- Each run gets its own independent FIR GLM
- NO averaging across runs for HRF estimation
- NO ROI-level HRF computation
- Direct extraction: amplitude[run, color, voxel, delay]

PIPELINE:
Step 1: Per-run color-specific FIR GLM
  For each run independently:
    - Build design matrix: 8 colors × 8 delays = 64 regressors
    - Fit GLM: β = pinv(X) @ y per voxel
    - Store: amplitude[run, color, voxel, delay]

Step 2: Voxel selection
  - Option A: Select by variance across colors
  - Option B: Select by max amplitude
  - Option C: No selection (use all)

Step 3: Dimension reduction strategies
  - Strategy 1: Use all (run, color, voxel, delay) → flatten
  - Strategy 2: Select optimal delay per voxel
  - Strategy 3: Average across delays (per run)
  - Strategy 4: Use specific delays (e.g., 3-5)

Step 4: Classification & Reconstruction
  - Leave-one-run-out CV
  - Compare different strategies

Usage:
    python fir_reconstruction_per_run.py --roi V1 --subject P01

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

def circular_diff_deg(a, b):
    """Circular difference"""
    diff = np.abs(a - b)
    return np.where(diff > 180, 360 - diff, diff)

def build_color_fir_design(events, n_scans, tr, fir_delays, n_colors=8):
    """
    Build color-specific FIR design matrix

    Returns: (n_scans, n_colors × n_delays) array
    Column order: [C1_D0, C1_D1, ..., C1_D7, C2_D0, ..., C8_D7]
    """
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
parser.add_argument('--strategy', type=str, default='all',
                    choices=['all', 'optimal', 'average', 'range'],
                    help='Dimension reduction strategy')
parser.add_argument('--delay-range', type=str, default='3,4,5',
                    help='Delays to use if strategy=range (comma-separated)')
parser.add_argument('--timestamp', type=str, default=None)
args = parser.parse_args()

SUBJECT_ID = args.subject
ROI_NAME = args.roi
STRATEGY = args.strategy
DELAY_RANGE = [int(x) for x in args.delay_range.split(',')]

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
output_dir = Path(f"derivatives/per_run/{DERIVATIVE_PREFIX}/{timestamp}_{ROI_NAME}_{STRATEGY}")
output_dir.mkdir(parents=True, exist_ok=True)
fig_dir = output_dir / 'figures'
fig_dir.mkdir(exist_ok=True)

print("="*70)
print("Per-Run FIR GLM (No HRF Averaging)")
print("="*70)
print(f"Subject: {SUBJECT_ID}")
print(f"ROI: {ROI_NAME}")
print(f"Strategy: {STRATEGY}")
if STRATEGY == 'range':
    print(f"Delay range: {DELAY_RANGE}")
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

    # Load and clean
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

    # Events
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
print(f"  Extracting: (runs={N_RUNS}, colors={N_COLORS}, voxels={n_voxels}, delays={len(FIR_DELAYS)})")

amplitudes = np.zeros((N_RUNS, N_COLORS, n_voxels, len(FIR_DELAYS)))

for run_idx in range(N_RUNS):
    print(f"\n  Run {run_idx+1}/{N_RUNS}...")

    y = all_func_data[run_idx]
    n_scans = y.shape[0]

    # Build design
    X = build_color_fir_design(events_list[run_idx], n_scans, TR, FIR_DELAYS, N_COLORS)

    print(f"    Design: {X.shape}, non-zero: {np.sum(X>0)}/{X.size} ({100*np.sum(X>0)/X.size:.2f}%)")
    print(f"    Rank: {np.linalg.matrix_rank(X)}/{X.shape[1]}")

    # Fit: β = pinv(X) @ y
    betas = np.linalg.pinv(X) @ y  # (n_colors × n_delays, n_voxels)

    # Reshape to (n_colors, n_delays, n_voxels) then transpose
    betas_reshaped = betas.reshape(N_COLORS, len(FIR_DELAYS), n_voxels)
    amplitudes[run_idx] = np.transpose(betas_reshaped, (0, 2, 1))  # (colors, voxels, delays)

    print(f"    Beta shape: {betas.shape} → {amplitudes[run_idx].shape}")
    print(f"    Mean: {np.mean(amplitudes[run_idx]):.4f}, Std: {np.std(amplitudes[run_idx]):.4f}")

print(f"\n  Final: {amplitudes.shape} (runs, colors, voxels, delays)")
print()

# ============================================================================
# Step 2: Apply Dimension Reduction Strategy
# ============================================================================

print(f"[4/5] Applying strategy: {STRATEGY}")

if STRATEGY == 'all':
    # Flatten: (runs, colors, voxels × delays)
    features = amplitudes.reshape(N_RUNS, N_COLORS, -1)
    print(f"  Flattened to: {features.shape}")

elif STRATEGY == 'optimal':
    # Find optimal delay per voxel (max abs amplitude averaged over runs and colors)
    avg_abs = np.mean(np.abs(amplitudes), axis=(0, 1))  # (voxels, delays)
    optimal_delays = np.argmax(avg_abs, axis=1)  # (voxels,)

    print(f"  Optimal delays: min={optimal_delays.min()}, max={optimal_delays.max()}")
    print(f"  Distribution: {np.bincount(optimal_delays, minlength=len(FIR_DELAYS))}")

    features = np.zeros((N_RUNS, N_COLORS, n_voxels))
    for v in range(n_voxels):
        features[:, :, v] = amplitudes[:, :, v, optimal_delays[v]]

    print(f"  Extracted at optimal delays: {features.shape}")

elif STRATEGY == 'average':
    # Average across all delays
    features = np.mean(amplitudes, axis=3)  # (runs, colors, voxels)
    print(f"  Averaged across delays: {features.shape}")

elif STRATEGY == 'range':
    # Use specific delay range
    print(f"  Using delays: {DELAY_RANGE}")
    features = amplitudes[:, :, :, DELAY_RANGE]  # (runs, colors, voxels, len(DELAY_RANGE))
    features = features.reshape(N_RUNS, N_COLORS, -1)  # flatten last two dims
    print(f"  Selected and flattened: {features.shape}")

print()

# ============================================================================
# Step 3: Classification
# ============================================================================

print(f"[5/5] Classification (leave-one-run-out)")

results = []

for test_run in range(N_RUNS):
    train_runs = [r for r in range(N_RUNS) if r != test_run]

    # Prepare data
    X_train = features[train_runs].reshape(-1, features.shape[2])
    y_train = np.tile(np.arange(N_COLORS), len(train_runs))

    X_test = features[test_run]
    y_test = np.arange(N_COLORS)

    # Standardize
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Classify
    y_pred = diag_linear_predict(X_train_scaled, y_train, X_test_scaled)
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

# Plot 1: Mean FIR response per color
fig, axes = plt.subplots(2, 4, figsize=(20, 10))
fig.suptitle(f'{ROI_NAME}: Mean FIR Amplitude Per Color (No Averaging)', fontsize=16, fontweight='bold')

times = FIR_DELAYS * TR

for c in range(N_COLORS):
    ax = axes[c // 4, c % 4]

    # Mean across runs and voxels
    mean_amp = np.mean(amplitudes[:, c, :, :], axis=(0, 1))
    sem_amp = np.std(amplitudes[:, c, :, :], axis=(0, 1)) / np.sqrt(N_RUNS * n_voxels)

    ax.errorbar(times, mean_amp, yerr=sem_amp, fmt='o-', capsize=5, linewidth=2)
    ax.axhline(0, color='gray', linestyle=':', alpha=0.5)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Amplitude')
    ax.set_title(f'Color {c+1}')
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(fig_dir / 'fir_amplitude_per_color.png', dpi=300)
plt.close()

# Plot 2: Classification result
fig, ax = plt.subplots(figsize=(8, 6))
runs = [r['test_run'] for r in results]
accs = [r['accuracy'] for r in results]

ax.bar(runs, accs, edgecolor='black', alpha=0.7, color='steelblue')
ax.axhline(mean_acc, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_acc:.3f}')
ax.axhline(1/N_COLORS, color='gray', linestyle=':', linewidth=2, label='Chance')
ax.set_xlabel('Test Run')
ax.set_ylabel('Classification Accuracy')
ax.set_title(f'{ROI_NAME}: Classification Performance\nStrategy: {STRATEGY}')
ax.legend()
ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig(fig_dir / 'classification_results.png', dpi=300)
plt.close()

print(f"  Saved figures to: {fig_dir}")
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
    'n_voxels': int(n_voxels),
    'n_runs': N_RUNS,
    'n_colors': N_COLORS,
    'n_delays': len(FIR_DELAYS),
    'feature_shape': list(features.shape),
    'mean_accuracy': float(mean_acc),
    'per_run_accuracy': results,
}

if STRATEGY == 'range':
    summary['delay_range'] = DELAY_RANGE
elif STRATEGY == 'optimal':
    summary['optimal_delays'] = {
        'mean': float(optimal_delays.mean()),
        'std': float(optimal_delays.std()),
        'distribution': np.bincount(optimal_delays, minlength=len(FIR_DELAYS)).tolist()
    }

with open(output_dir / 'summary.json', 'w') as f:
    json.dump(summary, f, indent=2)

np.save(output_dir / 'amplitudes.npy', amplitudes)
np.save(output_dir / 'features.npy', features)

print()
print("="*70)
print("Complete!")
print("="*70)
print(f"\nResults:")
print(f"  Strategy: {STRATEGY}")
print(f"  Classification: {mean_acc:.1%}")
print(f"  Saved to: {output_dir}")
print()
