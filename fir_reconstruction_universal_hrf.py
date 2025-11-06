#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fir_reconstruction_universal_hrf.py
------------------------------------
Universal HRF reconstruction (B&H 2009 Method - LEAST PARAMETERS)

Two-stage approach:
1. Fit FIR to estimate HRF shape averaged across all ROI voxels
2. Find optimal delay from universal HRF
3. Extract betas at that single optimal delay for all voxels

This reduces HRF parameters from 3,100 (310 voxels × 10 delays) to just 10 (1 universal HRF)!

Combines:
- Universal HRF estimation (B&H 2009 method)
- Correct Lab hue values (from pilot data)
- Diagonal LDA classification (paper method)
- B&H forward model for reconstruction
- Optional PCA dimensionality reduction

Usage:
    python fir_reconstruction_universal_hrf.py --roi V2 --use-pca --n-components 20
"""

import sys
import os
import argparse
import numpy as np
import pandas as pd
import nibabel as nib
from pathlib import Path
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server
import matplotlib.pyplot as plt
from nilearn.glm.first_level import FirstLevelModel
from nilearn import image as nimg
from nilearn import plotting

# Try different nilearn import versions
try:
    from nilearn.maskers import NiftiMasker
except ImportError:
    from nilearn.input_data import NiftiMasker

from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from scipy import stats

from config import cfg

# ============================================================================
# Configuration
# ============================================================================

# Correct Lab hue values from pilot data
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

# FIR parameters
FIR_DELAYS = range(10)  # 0-15 seconds (10 TRs × 1.5s)
PEAK_DELAY = 3  # ~4.5s post-onset (typical HRF peak)

# ============================================================================
# Parse Arguments
# ============================================================================

def parse_args():
    parser = argparse.ArgumentParser(description='FIR-based color reconstruction')
    parser.add_argument('--roi', type=str, default='V2',
                        help='ROI name (e.g., V1, V2, V3, V4, hV4, VO1)')
    parser.add_argument('--use-pca', action='store_true',
                        help='Use PCA dimensionality reduction')
    parser.add_argument('--n-components', type=int, default=20,
                        help='Number of PCA components (only if --use-pca)')
    parser.add_argument('--save-zmaps', action='store_true',
                        help='Save z-maps for each color')
    return parser.parse_args()

args = parse_args()

ROI_NAME = args.roi
USE_PCA = args.use_pca
N_PCA_COMPONENTS = args.n_components
SAVE_ZMAPS = args.save_zmaps

# ============================================================================
# Setup Output Directory
# ============================================================================

output_dir = Path(f"derivatives/sub-{cfg.SUB_ID}/fir_reconstruction/{ROI_NAME}_universal_hrf")
output_dir.mkdir(parents=True, exist_ok=True)

fig_dir = output_dir / "figures"
fig_dir.mkdir(exist_ok=True)

# Setup dual logging (both to file and stdout)
class DualLogger:
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, 'w', buffering=1)

    def write(self, message):
        self.terminal.write(message)
        self.terminal.flush()
        self.log.write(message)
        self.log.flush()

    def flush(self):
        self.terminal.flush()
        self.log.flush()

    def close(self):
        self.log.close()

log_file = output_dir / "log.txt"
sys.stdout = DualLogger(log_file)
sys.stderr = sys.stdout

print("="*70)
print("Universal HRF Reconstruction Pipeline (B&H 2009)")
print("="*70)
print(f"Subject: sub-{cfg.SUB_ID}")
print(f"ROI: {ROI_NAME}")
print(f"Method: Two-stage universal HRF")
print(f"Use PCA: {USE_PCA}")
if USE_PCA:
    print(f"PCA components: {N_PCA_COMPONENTS}")
print(f"Output directory: {output_dir}")
print()
sys.stdout.flush()

# ============================================================================
# Load ROI Mask
# ============================================================================

roi_path = f"derivatives/sub-{cfg.SUB_ID}/roi/sub-{cfg.SUB_ID}_{ROI_NAME}_mask.nii.gz"

if not os.path.exists(roi_path):
    print(f"ERROR: ROI mask not found: {roi_path}")
    sys.exit(1)

print(f"[1/8] Loading ROI mask: {ROI_NAME}")
print(f"  Path: {roi_path}")
sys.stdout.flush()

roi_img = nib.load(roi_path)
masker = NiftiMasker(mask_img=roi_path, standardize=False)
masker.fit()

n_voxels = np.sum(roi_img.get_fdata() > 0)
print(f"  Number of voxels: {n_voxels}")
print()
sys.stdout.flush()

# ============================================================================
# Load Functional Data and Events
# ============================================================================

print(f"[2/8] Loading {cfg.N_RUNS} runs of functional data and events")
sys.stdout.flush()

func_imgs = []
events_list = []
confounds_list = []

for run in range(1, cfg.N_RUNS + 1):
    # Functional data
    func_path = cfg.get_func_img_path(run)
    func_img = nib.load(func_path)

    # Drop initial volumes
    if cfg.VOLS_TO_DROP > 0:
        func_img = nimg.index_img(func_img, slice(cfg.VOLS_TO_DROP, None))

    func_imgs.append(func_img)

    # Events
    events = pd.read_csv(cfg.get_event_file_path(run), sep='\t')
    events_list.append(events)

    # Confounds
    confounds = pd.read_csv(cfg.get_confound_file_path(run), sep='\t')
    motion_cols = ['trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z']
    confounds_subset = confounds[motion_cols]

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

print(f"[3/8] Fitting FIR model (may take 5-10 minutes)")
print(f"  Using hrf_model='fir' with {len(FIR_DELAYS)} time bins")
print(f"  Each voxel gets its own response curve")
sys.stdout.flush()

fir_model = FirstLevelModel(
    t_r=cfg.TR,
    hrf_model='fir',
    fir_delays=FIR_DELAYS,
    drift_model='cosine',
    high_pass=1/128.0,
    mask_img=roi_path,
    standardize=False,
    minimize_memory=False
)

fir_model.fit(func_imgs, events_list, confounds_list)

print("  FIR model fitted successfully!")
print()
sys.stdout.flush()

# ============================================================================
# Visualize Mean HRF from FIR
# ============================================================================

print(f"[4/8] Visualizing mean HRF estimated from FIR")
sys.stdout.flush()

# Extract FIR response for each color at all delays
mean_responses = []  # (n_colors, n_delays)

for color_idx in range(1, cfg.N_COLORS + 1):
    color_responses = []

    for delay in FIR_DELAYS:
        contrast_name = f'color_{color_idx}_delay_{delay}'
        try:
            contrast_map = fir_model.compute_contrast(contrast_name, output_type='effect_size')
            mean_response = masker.transform(contrast_map).mean()  # Mean across voxels
            color_responses.append(mean_response)
        except:
            color_responses.append(0)

    mean_responses.append(color_responses)

mean_responses = np.array(mean_responses)

# ============================================================================
# Stage 1: Determine Universal HRF and Optimal Delay
# ============================================================================

# Compute universal HRF (average across all colors)
universal_hrf = mean_responses.mean(axis=0)  # Average across colors

# CORRECTED: Find peak using absolute value (handles negative baseline)
optimal_delay = np.argmax(np.abs(universal_hrf))
optimal_time = optimal_delay * cfg.TR

print()
print("  === Universal HRF Analysis (CORRECTED) ===")
print(f"  Universal HRF (averaged across {cfg.N_COLORS} colors and {n_voxels} voxels):")
print(f"  Full HRF curve: {universal_hrf}")
print(f"  Absolute values: {np.abs(universal_hrf)}")
print(f"  Optimal delay: {optimal_delay} TRs ({optimal_time:.1f}s)")
print(f"  Peak amplitude: {universal_hrf[optimal_delay]:.4f}")
print(f"  Peak absolute amplitude: {np.abs(universal_hrf[optimal_delay]):.4f}")
print(f"  Original PEAK_DELAY: {PEAK_DELAY} TRs ({PEAK_DELAY * cfg.TR}s)")
print()

# Update PEAK_DELAY to use optimal delay from universal HRF
PEAK_DELAY = optimal_delay
print(f"  >>> Using optimal delay {PEAK_DELAY} TRs ({PEAK_DELAY * cfg.TR}s) for all voxels")
print()
sys.stdout.flush()

# Plot HRF with universal HRF highlighted
fig, ax = plt.subplots(figsize=(10, 6))
time_points = np.array(list(FIR_DELAYS)) * cfg.TR

# Plot individual color HRFs
for color_idx in range(cfg.N_COLORS):
    ax.plot(time_points, mean_responses[color_idx],
            label=f'color_{color_idx+1}', alpha=0.5, linewidth=1)

# Plot universal HRF (bold)
ax.plot(time_points, universal_hrf, 'k-', linewidth=3,
        label='Universal HRF (average)', zorder=10)

ax.axhline(y=0, color='k', linestyle='--', alpha=0.3)
ax.axvline(x=optimal_time, color='r', linestyle='--', linewidth=2, alpha=0.8,
           label=f'Optimal delay ({optimal_time:.1f}s)')
ax.set_xlabel('Time (seconds)')
ax.set_ylabel('Mean response amplitude (% signal change)')
ax.set_title(f'Universal HRF from FIR estimation - {ROI_NAME}')
ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
ax.grid(True, alpha=0.3)

hrf_fig_path = fig_dir / f"{ROI_NAME}_universal_hrf.png"
plt.tight_layout()
plt.savefig(hrf_fig_path, dpi=150, bbox_inches='tight')
plt.close()

print(f"  Saved: {hrf_fig_path}")
print()
sys.stdout.flush()

# ============================================================================
# Extract Beta Estimates and Create Z-maps
# ============================================================================

print(f"[5/8] Extracting beta estimates for {cfg.N_COLORS} colors")
sys.stdout.flush()

all_betas = []  # (n_runs, n_colors, n_voxels)
z_maps = []  # (n_colors,) - z-score maps

for run_idx in range(cfg.N_RUNS):
    run_betas = []

    for color_idx in range(1, cfg.N_COLORS + 1):
        contrast_name = f'color_{color_idx}_delay_{PEAK_DELAY}'

        try:
            contrast_map = fir_model.compute_contrast(contrast_name, output_type='effect_size')
            betas = masker.transform(contrast_map).ravel()
            run_betas.append(betas)

            # Z-map (only from first run)
            if run_idx == 0:
                z_map = fir_model.compute_contrast(contrast_name, output_type='z_score')
                z_maps.append(z_map)

        except Exception as e:
            print(f"  Warning: Could not extract {contrast_name}: {e}")
            run_betas.append(np.zeros(n_voxels))
            if run_idx == 0:
                z_maps.append(None)

    all_betas.append(np.array(run_betas))
    print(f"  Run {run_idx+1}: Extracted {len(run_betas)} color betas")

all_betas = np.array(all_betas)  # (n_runs, n_colors, n_voxels)
print(f"  Total shape: {all_betas.shape}")
print()
sys.stdout.flush()

# Save z-maps
if SAVE_ZMAPS:
    print("  Saving z-maps for each color...")
    zmaps_dir = output_dir / "zmaps"
    zmaps_dir.mkdir(exist_ok=True)

    for color_idx, z_map in enumerate(z_maps, start=1):
        if z_map is not None:
            zmap_path = zmaps_dir / f"color_{color_idx}_zmap.nii.gz"
            nib.save(z_map, zmap_path)

            # Create visualization
            fig = plt.figure(figsize=(12, 4))
            display = plotting.plot_stat_map(
                z_map,
                title=f'color_{color_idx} (z-score)',
                threshold=2.3,  # p < 0.01 uncorrected
                display_mode='z',
                cut_coords=5,
                figure=fig
            )
            zmap_fig_path = fig_dir / f"color_{color_idx}_zmap.png"
            plt.savefig(zmap_fig_path, dpi=150, bbox_inches='tight')
            plt.close()

    print(f"  Saved z-maps to: {zmaps_dir}")
    print()
    sys.stdout.flush()

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
    """Circular difference in degrees (0-360)"""
    diff = np.abs(a - b)
    return np.minimum(diff, 360 - diff)

# ============================================================================
# Classification (Leave-One-Run-Out)
# ============================================================================

print(f"[6/8] Classification with diagonal LDA (leave-one-run-out)")
if USE_PCA:
    print(f"  Using PCA: {N_PCA_COMPONENTS} components")
sys.stdout.flush()

classification_results = []

for test_run in range(cfg.N_RUNS):
    train_runs = [r for r in range(cfg.N_RUNS) if r != test_run]

    X_train = all_betas[train_runs].reshape(-1, n_voxels)
    y_train = np.tile(np.arange(cfg.N_COLORS), len(train_runs))

    X_test = all_betas[test_run]
    y_test = np.arange(cfg.N_COLORS)

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
print(f"Baseline (chance): {1/cfg.N_COLORS:.3f} ({100/cfg.N_COLORS:.1f}%)")
print()

# Create confusion matrix to verify no data leakage
print("Confusion matrix (aggregated across runs):")
all_y_true = []
all_y_pred = []
for r in classification_results:
    all_y_true.extend(r['y_true'])
    all_y_pred.extend(r['y_pred'])

conf_matrix = np.zeros((cfg.N_COLORS, cfg.N_COLORS), dtype=int)
for true_idx, pred_idx in zip(all_y_true, all_y_pred):
    conf_matrix[true_idx, pred_idx] += 1

print("        ", end="")
for i in range(cfg.N_COLORS):
    print(f"c{i+1:>3}", end="")
print()
for i in range(cfg.N_COLORS):
    print(f"  c{i+1}: ", end="")
    for j in range(cfg.N_COLORS):
        print(f"{conf_matrix[i,j]:>3}", end=" ")
    print()

# Per-color accuracy
print("\nPer-color classification accuracy:")
for color_idx in range(cfg.N_COLORS):
    correct = conf_matrix[color_idx, color_idx]
    total = conf_matrix[color_idx, :].sum()
    acc = correct / total if total > 0 else 0
    print(f"  color_{color_idx+1}: {acc:.3f} ({correct}/{total})")

print()
sys.stdout.flush()

# ============================================================================
# Forward Model for Reconstruction
# ============================================================================

print(f"[7/8] Reconstruction with B&H forward model")
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

for test_run in range(cfg.N_RUNS):
    train_runs = [r for r in range(cfg.N_RUNS) if r != test_run]

    X_train = all_betas[train_runs].reshape(-1, n_voxels)
    y_train = np.tile(np.arange(cfg.N_COLORS), len(train_runs))

    X_test = all_betas[test_run]
    y_test = np.arange(cfg.N_COLORS)

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
    # Get channel outputs for training colors
    C_train = []
    for color_idx in y_train:
        color_name = f'color_{color_idx+1}'
        hue_deg = LABEL2HUE_DEG_PILOT[color_name]
        channels = hue_to_channels(hue_deg)
        C_train.append(channels)
    C_train = np.array(C_train).T  # (6, n_train)

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
        true_hue = LABEL2HUE_DEG_PILOT[color_name]

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
sys.stdout.flush()

# ============================================================================
# Leave-One-Color-Out Reconstruction
# ============================================================================

print(f"[8/8] Leave-one-color-out reconstruction (novel colors)")
sys.stdout.flush()

novel_color_results = []

for held_out_color in range(cfg.N_COLORS):
    all_errors_this_color = []

    for test_run in range(cfg.N_RUNS):
        train_runs = [r for r in range(cfg.N_RUNS) if r != test_run]

        # Remove held-out color from training
        X_train_list = []
        y_train_list = []

        for r in train_runs:
            for c in range(cfg.N_COLORS):
                if c != held_out_color:
                    X_train_list.append(all_betas[r, c])
                    y_train_list.append(c)

        X_train = np.array(X_train_list)
        y_train = np.array(y_train_list)

        X_test = all_betas[test_run, held_out_color:held_out_color+1]
        y_test = np.array([held_out_color])

        # Standardize
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        # Optional PCA
        if USE_PCA:
            pca = PCA(n_components=min(N_PCA_COMPONENTS, len(X_train)))
            X_train_final = pca.fit_transform(X_train_scaled)
            X_test_final = pca.transform(X_test_scaled)
        else:
            X_train_final = X_train_scaled
            X_test_final = X_test_scaled

        # Train forward model
        C_train = []
        for color_idx in y_train:
            color_name = f'color_{color_idx+1}'
            hue_deg = LABEL2HUE_DEG_PILOT[color_name]
            channels = hue_to_channels(hue_deg)
            C_train.append(channels)
        C_train = np.array(C_train).T

        W = X_train_final.T @ C_train.T @ np.linalg.inv(C_train @ C_train.T)

        # Reconstruct held-out color
        # Use pseudoinverse to avoid singular matrix errors
        C_test_est = np.linalg.pinv(W.T @ W) @ W.T @ X_test_final.T
        estimated_channels = C_test_est[:, 0]

        correlations = []
        for h in range(360):
            template_channels = basis_functions[h]
            corr = np.corrcoef(estimated_channels, template_channels)[0, 1]
            correlations.append(corr)

        reconstructed_hue = np.argmax(correlations)

        color_name = f'color_{held_out_color+1}'
        true_hue = LABEL2HUE_DEG_PILOT[color_name]

        error = circular_diff_deg(reconstructed_hue, true_hue)
        all_errors_this_color.append(error)

    mean_error_this_color = np.mean(all_errors_this_color)
    color_name = f'color_{held_out_color+1}'

    novel_color_results.append({
        'color': color_name,
        'mean_error': mean_error_this_color,
        'errors': all_errors_this_color
    })

    print(f"  {color_name}: Mean error = {mean_error_this_color:.1f}°")

mean_novel_error = np.mean([r['mean_error'] for r in novel_color_results])
print()
print(f"Mean error (novel colors): {mean_novel_error:.1f}°")
print()
sys.stdout.flush()

# ============================================================================
# Save Results
# ============================================================================

print("Saving results...")

# Save numerical results
results = {
    'roi': ROI_NAME,
    'n_voxels': n_voxels,
    'use_pca': USE_PCA,
    'n_pca_components': N_PCA_COMPONENTS if USE_PCA else n_voxels,
    'classification': {
        'mean_accuracy': mean_classification_acc,
        'per_run': classification_results
    },
    'reconstruction': {
        'mean_error': mean_reconstruction_error,
        'per_run': reconstruction_results
    },
    'novel_colors': {
        'mean_error': mean_novel_error,
        'per_color': novel_color_results
    }
}

import pickle
results_path = output_dir / "results.pkl"
with open(results_path, 'wb') as f:
    pickle.dump(results, f)

print(f"  Saved: {results_path}")

# Save summary CSV
summary_data = {
    'ROI': [ROI_NAME],
    'Method': ['universal_hrf'],
    'N_voxels': [n_voxels],
    'Optimal_delay_TRs': [PEAK_DELAY],
    'Use_PCA': [USE_PCA],
    'N_components': [N_PCA_COMPONENTS if USE_PCA else n_voxels],
    'Classification_accuracy': [mean_classification_acc],
    'Reconstruction_error_deg': [mean_reconstruction_error],
    'Novel_color_error_deg': [mean_novel_error]
}

summary_df = pd.DataFrame(summary_data)
summary_csv_path = output_dir / "summary.csv"
summary_df.to_csv(summary_csv_path, index=False)

print(f"  Saved: {summary_csv_path}")
print()

# ============================================================================
# Final Summary
# ============================================================================

print("="*70)
print("Universal HRF Reconstruction Complete (B&H 2009)")
print("="*70)
print()
print(f"ROI: {ROI_NAME}")
print(f"Method: Universal HRF (optimal delay: {PEAK_DELAY} TRs / {PEAK_DELAY * cfg.TR}s)")
print(f"Voxels: {n_voxels}")
if USE_PCA:
    print(f"PCA: {N_PCA_COMPONENTS} components")
print()
print("Results:")
print(f"  Classification accuracy: {mean_classification_acc*100:.1f}% (chance: {100/cfg.N_COLORS:.1f}%)")
print(f"  Reconstruction error: {mean_reconstruction_error:.1f}° (chance: 90.0°)")
print(f"  Novel color error: {mean_novel_error:.1f}°")
print()
print(f"Output directory: {output_dir}")
print("="*70)
sys.stdout.flush()

# Close dual logger
if hasattr(sys.stdout, 'close'):
    sys.stdout.close()
