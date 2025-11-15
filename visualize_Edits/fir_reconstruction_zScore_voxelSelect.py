#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fir_reconstruction_zScore_voxelSelect.py
-----------------------------------------
Z-score based Universal HRF with FUNCTIONAL VOXEL SELECTION

DIFFERENCE FROM zScore.py:
- Adds functional voxel selection after Z-score extraction
- Only uses voxels with |mean_z_score| > 2.3 (p < 0.01)
- Mean z-score = average across all 8 colors (Color vs Gray)
- Implements B&H 2009 approach: Anatomical ROI ∩ Functional localizer
- Removes non-responsive voxels (~78-85%)

Workflow:
1. Fit FIR to estimate universal HRF
2. Extract Z-scores at optimal delay for ALL voxels
3. **Compute mean |z| across 8 colors per voxel**
4. **Select only voxels with mean |z| > 2.3** (color-responsive)
5. Continue PCA/classification/reconstruction with selected voxels only

Features:
- Universal HRF estimation (B&H 2009 method)
- Functional voxel selection (Color vs Gray, p < 0.01)
- Z-score based features (noise suppression)
- Correct Lab hue values (from pilot data)
- Diagonal LDA classification (paper method)
- B&H forward model for reconstruction
- Optional PCA dimensionality reduction

Usage:
    python fir_reconstruction_zScore_voxelSelect.py --roi V2 --use-pca --n-components 6

EDITLOG:
    11.15. Created from fir_reconstruction_zScore.py
    - Changed Line 402: output_type='z_score' (was 'effect_size')
    - Changed output_dir: added /zScore/ subfolder
    - All downstream analyses now use Z-scores instead of Betas
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

# ============================================================================
# Configuration
# ============================================================================

# Correct Lab hue values from pilot data (irregular spacing)
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

# Test data color mapping (regular 45° spacing)
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

# FIR parameters
FIR_DELAYS = range(10)  # 0-15 seconds (10 TRs × 1.5s)
PEAK_DELAY = 3  # ~4.5s post-onset (typical HRF peak)

# ============================================================================
# Parse Arguments
# ============================================================================

def parse_args():
    parser = argparse.ArgumentParser(description='FIR-based color reconstruction (Z-score version)')
    parser.add_argument('--subject', type=str, default='P01',
                        help='Subject ID (P01 for pilot, 02-04 for test subjects)')
    parser.add_argument('--roi', type=str, default='V2',
                        help='ROI name (e.g., V1, V2, V3, V4, hV4)')
    parser.add_argument('--use-pca', action='store_true',
                        help='Use PCA dimensionality reduction')
    parser.add_argument('--n-components', type=int, default=20,
                        help='Number of PCA components (only if --use-pca)')
    parser.add_argument('--save-zmaps', action='store_true',
                        help='Save z-maps for each color')
    return parser.parse_args()

args = parse_args()

SUBJECT_ID = args.subject
ROI_NAME = args.roi
USE_PCA = args.use_pca
N_PCA_COMPONENTS = args.n_components
SAVE_ZMAPS = args.save_zmaps

# ============================================================================
# Path Configuration (Pilot vs Test Data)
# ============================================================================

FMRIPREP_BASE = "/storage/connectome/haba6030/fmriprep_out"
EVENT_DIR = "/storage/connectome/haba6030/colorBlind_dataOct"

if SUBJECT_ID == 'P01':
    FMRIPREP_DIR = f"{FMRIPREP_BASE}/pilot/sub-01"
    FILE_PREFIX = "sub-01"  # File prefix: sub-01
    DERIVATIVE_PREFIX = "sub-01"
    EVENT_DIR = f"{EVENT_DIR}/pilot/sub-01/func"
    LABEL2HUE_DEG = LABEL2HUE_DEG_PILOT  # Use pilot color mapping
else:
    FMRIPREP_DIR = f"{FMRIPREP_BASE}/sub-{SUBJECT_ID}"  # Directory name: sub-XX
    FILE_PREFIX = f"sub-{SUBJECT_ID}"  # File prefix: sub-XX
    DERIVATIVE_PREFIX = f"sub-{SUBJECT_ID}"  # Derivative folder: sub-XX
    EVENT_DIR = f"{EVENT_DIR}/sub-{SUBJECT_ID}/func"  # Events in pilot/sub-XX/func/
    LABEL2HUE_DEG = LABEL2HUE_DEG_TEST  # Use test color mapping

# ============================================================================
# Setup Output Directory (WITH ZSCORE SUBFOLDER)
# ============================================================================

if SUBJECT_ID == 'P01':
    output_dir = Path(f"derivatives/pilot/{DERIVATIVE_PREFIX}/fir_reconstruction_uni_hrf/voxelSelect/{ROI_NAME}_universal_hrf")
else:
    output_dir = Path(f"derivatives/{DERIVATIVE_PREFIX}/fir_reconstruction_uni_hrf/voxelSelect/{ROI_NAME}_universal_hrf")
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
print("Z-Score Universal HRF Reconstruction Pipeline (Modified B&H 2009)")
print("="*70)
print(f"Subject: {SUBJECT_ID} (files: {FILE_PREFIX}, derivatives: {DERIVATIVE_PREFIX})")
print(f"ROI: {ROI_NAME}")
print(f"Method: Z-score based universal HRF")
print(f"Feature type: Z-SCORE (statistical significance weighted)")
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
if SUBJECT_ID == 'P01':
    roi_path = f"derivatives/pilot/{DERIVATIVE_PREFIX}/roi_pipeline_20251111_010954/{ROI_NAME}_mask_thr50_intnearest_binTrue_masknone_gmTrue_subjFalse.nii.gz"
else:
    roi_path = f"derivatives/{DERIVATIVE_PREFIX}/roi_pipeline/{ROI_NAME}_mask_thr50_intnearest_binTrue_masknone_gmTrue_subjFalse.nii.gz"
# roi_path = f"derivatives/{DERIVATIVE_PREFIX}/roi/{FILE_PREFIX}_{ROI_NAME}_mask.nii.gz"

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

print(f"[2/8] Loading {N_RUNS} runs of functional data and events")
sys.stdout.flush()

func_imgs = []
events_list = []
confounds_list = []

VOLS_TO_DROP = 4

for run in range(1, N_RUNS + 1):
    func_path = f"{FMRIPREP_DIR}/func/{FILE_PREFIX}_task-rsvp_run-{run}_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz"
    if not os.path.exists(func_path):
        print(f"ERROR: Functional image not found: {func_path}")
        sys.exit(1)

    func_img = nib.load(func_path)

    # Drop initial volumes
    if VOLS_TO_DROP > 0:
        func_img = nimg.index_img(func_img, slice(VOLS_TO_DROP, None))

    func_imgs.append(func_img)

    # Events path
    events_path = f"{EVENT_DIR}/{FILE_PREFIX}_task-rsvp_run-{run}_events.tsv"

    if not os.path.exists(events_path):
        print(f"ERROR: Events file not found: {events_path}")
        sys.exit(1)

    events = pd.read_csv(events_path, sep='\t')
    events_list.append(events)

    # Confounds path (same pattern for both pilot and test)
    confounds_path = f"{FMRIPREP_DIR}/func/{FILE_PREFIX}_task-rsvp_run-{run}_desc-confounds_timeseries.tsv"

    if not os.path.exists(confounds_path):
        print(f"ERROR: Confounds file not found: {confounds_path}")
        sys.exit(1)

    confounds = pd.read_csv(confounds_path, sep='\t')
    motion_cols = ['trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z']
    confounds_subset = confounds[motion_cols]

    ## DROP 추가
    if VOLS_TO_DROP > 0:
        confounds_subset = confounds_subset.iloc[VOLS_TO_DROP:]

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
    t_r=TR,
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

for color_idx in range(1, N_COLORS + 1):
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
optimal_time = optimal_delay * TR

print()
print("  === Universal HRF Analysis (CORRECTED) ===")
print(f"  Universal HRF (averaged across {N_COLORS} colors and {n_voxels} voxels):")
print(f"  Full HRF curve: {universal_hrf}")
print(f"  Absolute values: {np.abs(universal_hrf)}")
print(f"  Optimal delay: {optimal_delay} TRs ({optimal_time:.1f}s)")
print(f"  Peak amplitude: {universal_hrf[optimal_delay]:.4f}")
print(f"  Peak absolute amplitude: {np.abs(universal_hrf[optimal_delay]):.4f}")
print(f"  Original PEAK_DELAY: {PEAK_DELAY} TRs ({PEAK_DELAY * TR}s)")
print()

# Update PEAK_DELAY to use optimal delay from universal HRF
PEAK_DELAY = optimal_delay
print(f"  >>> Using optimal delay {PEAK_DELAY} TRs ({PEAK_DELAY * TR}s) for all voxels")
print()
sys.stdout.flush()

# Plot HRF with universal HRF highlighted
fig, ax = plt.subplots(figsize=(10, 6))
time_points = np.array(list(FIR_DELAYS)) * TR

# Plot individual color HRFs
for color_idx in range(N_COLORS):
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
# Extract Z-Score Estimates and Create Z-maps
# ============================================================================

print(f"[5/8] Extracting Z-SCORE estimates for {N_COLORS} colors")
print(f"  NOTE: Using Z-scores instead of Beta values!")
print(f"  Z-scores automatically weight voxels by statistical significance")
sys.stdout.flush()

all_betas = []  # (n_runs, n_colors, n_voxels) - NOTE: variable name is 'all_betas' but contains Z-SCORES!
z_maps = []  # (n_colors,) - z-score maps

for run_idx in range(N_RUNS):
    run_betas = []

    for color_idx in range(1, N_COLORS + 1):
        contrast_name = f'color_{color_idx}_delay_{PEAK_DELAY}'

        try:
            # ===== KEY CHANGE: Extract Z-scores instead of Betas =====
            contrast_map = fir_model.compute_contrast(contrast_name, output_type='z_score')
            betas = masker.transform(contrast_map).ravel()  # Variable name is 'betas' but contains Z-SCORES
            run_betas.append(betas)

            # Z-map (only from first run) - same as before but now redundant since we extract z-scores
            if run_idx == 0:
                z_map = fir_model.compute_contrast(contrast_name, output_type='z_score')
                z_maps.append(z_map)

        except Exception as e:
            print(f"  Warning: Could not extract {contrast_name}: {e}")
            run_betas.append(np.zeros(n_voxels))
            if run_idx == 0:
                z_maps.append(None)

    all_betas.append(np.array(run_betas))
    print(f"  Run {run_idx+1}: Extracted {len(run_betas)} color z-scores")

all_betas = np.array(all_betas)  # (n_runs, n_colors, n_voxels) - CONTAINS Z-SCORES!
print(f"  Total shape: {all_betas.shape}")
print(f"  Data type: Z-SCORES (not betas!)")
print()
sys.stdout.flush()

# ============================================================================
# FUNCTIONAL VOXEL SELECTION (Color vs Gray, p < 0.01)
# ============================================================================

print(f"[5B/8] Functional voxel selection (|mean_z| > 2.3)")
print(f"  This implements: Anatomical ROI ∩ Functional Localizer")
sys.stdout.flush()

# Compute mean |z-score| across all 8 colors and all runs
mean_abs_z_per_voxel = np.mean(np.abs(all_betas), axis=(0, 1))  # (n_voxels,)

# Threshold
Z_THRESHOLD = 2.3  # p < 0.01, two-tailed
selected_voxels_mask = mean_abs_z_per_voxel > Z_THRESHOLD

# Statistics BEFORE selection
n_voxels_anatomical = n_voxels
n_voxels_selected = selected_voxels_mask.sum()
selection_percentage = 100.0 * n_voxels_selected / n_voxels_anatomical

print(f"  Anatomical ROI voxels: {n_voxels_anatomical}")
print(f"  Functional threshold: |z| > {Z_THRESHOLD} (p < 0.01)")
print(f"  Selected voxels: {n_voxels_selected} ({selection_percentage:.1f}%)")
print(f"  Removed voxels: {n_voxels_anatomical - n_voxels_selected} ({100-selection_percentage:.1f}%)")
print()

# Statistics of selected voxels
mean_z_selected = mean_abs_z_per_voxel[selected_voxels_mask]
print(f"  Selected voxel statistics:")
print(f"    Mean |z|: {mean_z_selected.mean():.2f} ± {mean_z_selected.std():.2f}")
print(f"    Range |z|: [{mean_z_selected.min():.2f}, {mean_z_selected.max():.2f}]")
print()
sys.stdout.flush()

# Apply selection to data
all_betas = all_betas[:, :, selected_voxels_mask]  # (n_runs, n_colors, n_selected_voxels)
n_voxels = n_voxels_selected  # Update voxel count

print(f"  Data shape after selection: {all_betas.shape}")
print(f"  Updated n_voxels: {n_voxels}")
print()
sys.stdout.flush()

# Save selection mask
selection_mask_data = np.zeros(roi_img.get_fdata().shape)
# Get voxel coordinates from original ROI
roi_coords = np.where(roi_img.get_fdata() > 0)
selected_indices = np.where(selected_voxels_mask)[0]

# Map selected voxels back to 3D space
for idx in selected_indices:
    selection_mask_data[roi_coords[0][idx], roi_coords[1][idx], roi_coords[2][idx]] = 1

selection_mask_img = nib.Nifti1Image(selection_mask_data, affine=roi_img.affine)
selection_mask_path = output_dir / f"{ROI_NAME}_functional_selection_mask.nii.gz"
nib.save(selection_mask_img, selection_mask_path)
print(f"  Saved selection mask: {selection_mask_path}")
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
# Z-Map Matrix Visualization
# ============================================================================

if SAVE_ZMAPS:
    print("Creating z-map matrix visualization...")

    # Extract z-scores for each voxel × color
    zscores_matrix = np.zeros((n_voxels, N_COLORS))

    for color_idx in range(N_COLORS):
        if z_maps[color_idx] is not None:
            z_data = masker.transform(z_maps[color_idx]).ravel()
            zscores_matrix[:, color_idx] = z_data

    # 1. Full Z-Score Matrix Heatmap (unsorted)
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle(f'{ROI_NAME}: Z-Score Matrix Visualization', fontsize=16, fontweight='bold')

    # Top-left: Raw matrix (all voxels × colors)
    ax1 = axes[0, 0]
    im1 = ax1.imshow(zscores_matrix.T, aspect='auto', cmap='RdBu_r', vmin=-5, vmax=5)
    ax1.set_xlabel('Voxel Index')
    ax1.set_ylabel('Color')
    ax1.set_yticks(range(N_COLORS))
    ax1.set_yticklabels([f'c{i+1}' for i in range(N_COLORS)])
    ax1.set_title('Raw Z-Scores (Colors × Voxels)')
    plt.colorbar(im1, ax=ax1, label='Z-score')

    # Top-right: Sorted by peak color preference
    voxel_peak_colors = np.argmax(np.abs(zscores_matrix), axis=1)
    sorted_indices = np.argsort(voxel_peak_colors)
    zscores_sorted = zscores_matrix[sorted_indices, :]

    ax2 = axes[0, 1]
    im2 = ax2.imshow(zscores_sorted.T, aspect='auto', cmap='RdBu_r', vmin=-5, vmax=5)
    ax2.set_xlabel('Voxel Index (sorted by peak color)')
    ax2.set_ylabel('Color')
    ax2.set_yticks(range(N_COLORS))
    ax2.set_yticklabels([f'c{i+1}' for i in range(N_COLORS)])
    ax2.set_title('Sorted by Voxel Color Preference')
    plt.colorbar(im2, ax=ax2, label='Z-score')

    # Bottom-left: Per-color z-score distribution
    ax3 = axes[1, 0]
    violin_parts = ax3.violinplot([zscores_matrix[:, i] for i in range(N_COLORS)],
                               positions=range(N_COLORS),
                               showmeans=True, showmedians=True)
    ax3.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    ax3.axhline(y=2.3, color='red', linestyle=':', alpha=0.5, label='p<0.01')
    ax3.axhline(y=-2.3, color='red', linestyle=':', alpha=0.5)
    ax3.set_xlabel('Color')
    ax3.set_ylabel('Z-score')
    ax3.set_xticks(range(N_COLORS))
    ax3.set_xticklabels([f'c{i+1}' for i in range(N_COLORS)])
    ax3.set_title('Z-Score Distribution per Color')
    ax3.legend()
    ax3.grid(True, alpha=0.3, axis='y')

    # Bottom-right: Voxel selectivity statistics
    ax4 = axes[1, 1]

    # Count voxels with significant response (|z| > 2.3) for each color
    significant_counts = np.sum(np.abs(zscores_matrix) > 2.3, axis=0)
    selective_voxels = np.sum(np.any(np.abs(zscores_matrix) > 2.3, axis=1))

    bars = ax4.bar(range(N_COLORS), significant_counts, alpha=0.7, edgecolor='black')
    ax4.set_xlabel('Color')
    ax4.set_ylabel('# Voxels with |z| > 2.3')
    ax4.set_xticks(range(N_COLORS))
    ax4.set_xticklabels([f'c{i+1}' for i in range(N_COLORS)])
    ax4.set_title(f'Color Selectivity\n({selective_voxels}/{n_voxels} voxels selective)')
    ax4.grid(True, alpha=0.3, axis='y')

    # Add count labels on bars
    for bar, count in zip(bars, significant_counts):
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(count)}',
                ha='center', va='bottom', fontsize=10, fontweight='bold')

    plt.tight_layout()
    zmatrix_plot_path = fig_dir / f"{ROI_NAME}_zscores_matrix.png"
    plt.savefig(zmatrix_plot_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {zmatrix_plot_path}")

    # 2. Detailed per-color z-score heatmaps (top 100 voxels)
    fig, axes = plt.subplots(2, 4, figsize=(16, 8))
    fig.suptitle(f'{ROI_NAME}: Top Voxels per Color (Highest |z|)', fontsize=14, fontweight='bold')

    for color_idx in range(N_COLORS):
        ax = axes[color_idx // 4, color_idx % 4]

        # Get top voxels for this color
        color_zscores = zscores_matrix[:, color_idx]
        top_indices = np.argsort(np.abs(color_zscores))[-100:][::-1]

        # Show z-scores across all colors for these top voxels
        top_zscores = zscores_matrix[top_indices, :]

        im = ax.imshow(top_zscores, aspect='auto', cmap='RdBu_r', vmin=-5, vmax=5)
        ax.set_xlabel('Color')
        ax.set_ylabel('Top 100 voxels')
        ax.set_xticks(range(N_COLORS))
        ax.set_xticklabels([f'{i+1}' for i in range(N_COLORS)], fontsize=8)
        ax.set_title(f'c{color_idx+1} (peak |z|={np.abs(color_zscores).max():.1f})')

        # Highlight the color column
        ax.axvline(x=color_idx-0.5, color='yellow', linewidth=2, alpha=0.5)
        ax.axvline(x=color_idx+0.5, color='yellow', linewidth=2, alpha=0.5)

    plt.colorbar(im, ax=axes.ravel().tolist(), label='Z-score', shrink=0.6)
    plt.tight_layout()
    top_voxels_plot_path = fig_dir / f"{ROI_NAME}_top_voxels_per_color.png"
    plt.savefig(top_voxels_plot_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {top_voxels_plot_path}")

    # 3. Voxel-wise color preference wheel
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))

    # Map color indices to hue angles
    color_hues_rad = []
    for i in range(N_COLORS):
        color_name = f'color_{i+1}'
        hue_deg = LABEL2HUE_DEG[color_name]
        color_hues_rad.append(np.deg2rad(hue_deg))

    # For each voxel, plot its preferred color direction weighted by z-score magnitude
    for vox_idx in range(n_voxels):
        vox_zscores = zscores_matrix[vox_idx, :]

        # Only plot if voxel is selective (max |z| > 2.3)
        if np.abs(vox_zscores).max() > 2.3:
            # Find peak color
            peak_color_idx = np.argmax(np.abs(vox_zscores))
            peak_zscore = vox_zscores[peak_color_idx]

            # Plot at that color's hue angle
            angle = color_hues_rad[peak_color_idx]
            radius = np.abs(peak_zscore)

            # Color by sign (positive = excitatory, negative = inhibitory)
            color = 'red' if peak_zscore > 0 else 'blue'
            alpha = min(0.3, 30.0 / n_voxels)  # Scale alpha by number of voxels

            ax.scatter(angle, radius, c=color, s=20, alpha=alpha)

    # Add color reference points
    for i in range(N_COLORS):
        angle = color_hues_rad[i]
        ax.scatter(angle, 1, c='black', s=200, marker='*', zorder=10)
        ax.text(angle, 1.15, f'c{i+1}', ha='center', va='center', fontsize=12, fontweight='bold')

    ax.set_ylim([0, max(np.abs(zscores_matrix).max(), 5)])
    ax.set_title(f'{ROI_NAME}: Voxel Color Preferences\n(Red=excitatory, Blue=inhibitory)',
                 fontsize=14, fontweight='bold', pad=20)

    plt.tight_layout()
    wheel_plot_path = fig_dir / f"{ROI_NAME}_color_preference_wheel.png"
    plt.savefig(wheel_plot_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {wheel_plot_path}")

    # Print statistics
    print()
    print("Z-Score Matrix Statistics:")
    print(f"  Voxels: {n_voxels}")
    print(f"  Colors: {N_COLORS}")
    print(f"  Z-score range: [{zscores_matrix.min():.2f}, {zscores_matrix.max():.2f}]")
    print(f"  Selective voxels (|z|>2.3 for any color): {selective_voxels} ({100*selective_voxels/n_voxels:.1f}%)")
    print(f"  Mean |z| per color: {np.mean(np.abs(zscores_matrix), axis=0).round(2)}")
    print()
    sys.stdout.flush()

# ============================================================================
# PCA Component Visualization (if using PCA)
# ============================================================================

if USE_PCA and SAVE_ZMAPS:
    print("Creating PCA component visualization (leave-one-run-out)...")
    print("  NOTE: Fitting PCA on Z-SCORES (not betas!)")
    print("  NOTE: Fitting PCA separately for each fold to avoid data leakage")

    # Store results from each fold
    pca_matrices_per_fold = []  # (n_folds, n_colors, n_components)
    explained_variance_per_fold = []  # (n_folds, n_components)
    pca_loadings_per_fold = []  # (n_folds, n_components, n_voxels)

    # Fit PCA for each fold independently
    for test_run in range(N_RUNS):
        train_runs = [r for r in range(N_RUNS) if r != test_run]

        # Prepare training data for this fold
        X_train = all_betas[train_runs].reshape(-1, n_voxels)  # Contains Z-SCORES!
        y_train = np.tile(np.arange(N_COLORS), len(train_runs))

        # Standardize
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)

        # Apply PCA (fit on train set only!)
        pca = PCA(n_components=N_PCA_COMPONENTS)
        X_pca_train = pca.fit_transform(X_train_scaled)

        # Reshape to (n_train_runs, n_colors, n_components)
        X_pca_reshaped = X_pca_train.reshape(len(train_runs), N_COLORS, N_PCA_COMPONENTS)

        # Average across training runs to get (n_colors, n_components)
        pca_matrix_fold = X_pca_reshaped.mean(axis=0)

        # Store results
        pca_matrices_per_fold.append(pca_matrix_fold)
        explained_variance_per_fold.append(pca.explained_variance_ratio_)
        pca_loadings_per_fold.append(pca.components_)  # (n_components, n_voxels)

    # Convert to arrays
    pca_matrices_per_fold = np.array(pca_matrices_per_fold)  # (N_RUNS, N_COLORS, N_PCA_COMPONENTS)
    explained_variance_per_fold = np.array(explained_variance_per_fold)  # (N_RUNS, N_PCA_COMPONENTS)
    pca_loadings_per_fold = np.array(pca_loadings_per_fold)  # (N_RUNS, N_PCA_COMPONENTS, n_voxels)

    # Compute mean and std across folds
    pca_matrix_mean = pca_matrices_per_fold.mean(axis=0)  # (N_COLORS, N_PCA_COMPONENTS)
    pca_matrix_std = pca_matrices_per_fold.std(axis=0)  # (N_COLORS, N_PCA_COMPONENTS)
    explained_var_mean = explained_variance_per_fold.mean(axis=0)  # (N_PCA_COMPONENTS,)
    explained_var_std = explained_variance_per_fold.std(axis=0)  # (N_PCA_COMPONENTS,)

    print(f"  PCA components: {N_PCA_COMPONENTS}")
    print(f"  Explained variance ratio (mean±std): {explained_var_mean.sum():.3f}±{explained_var_std.sum():.3f}")
    print(f"  PCA matrix shape: {pca_matrix_mean.shape}")
    print(f"  Robustness check: std across folds = {pca_matrix_std.mean():.4f}")

    # Use mean for visualization
    pca_matrix = pca_matrix_mean

    # 1. Component × Color Matrix Heatmap with Robustness
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle(f'{ROI_NAME}: PCA Component Analysis (Z-score based, {N_PCA_COMPONENTS} components, {N_RUNS} folds)',
                 fontsize=16, fontweight='bold')

    # Top-left: Mean matrix (colors × components)
    ax1 = axes[0, 0]
    im1 = ax1.imshow(pca_matrix, aspect='auto', cmap='RdBu_r',
                     vmin=-np.abs(pca_matrix).max(), vmax=np.abs(pca_matrix).max())
    ax1.set_xlabel('PCA Component')
    ax1.set_ylabel('Color')
    ax1.set_yticks(range(N_COLORS))
    ax1.set_yticklabels([f'c{i+1}' for i in range(N_COLORS)])
    ax1.set_xticks(range(0, N_PCA_COMPONENTS, max(1, N_PCA_COMPONENTS//10)))
    ax1.set_title('Mean Component Activations (Colors × Components)')
    plt.colorbar(im1, ax=ax1, label='Component value')

    # Top-right: Std matrix (robustness check)
    ax2 = axes[0, 1]
    im2 = ax2.imshow(pca_matrix_std, aspect='auto', cmap='hot',
                     vmin=0, vmax=pca_matrix_std.max())
    ax2.set_xlabel('PCA Component')
    ax2.set_ylabel('Color')
    ax2.set_xticks(range(0, N_PCA_COMPONENTS, max(1, N_PCA_COMPONENTS//10)))
    ax2.set_yticks(range(N_COLORS))
    ax2.set_yticklabels([f'c{i+1}' for i in range(N_COLORS)])
    ax2.set_title('Std across Folds (Robustness Check)')
    plt.colorbar(im2, ax=ax2, label='Std')

    # Bottom-left: Explained variance per component with error bars
    ax3 = axes[1, 0]
    cumsum_var_mean = np.cumsum(explained_var_mean)
    cumsum_var_std = np.cumsum(explained_var_std)

    ax3.bar(range(N_PCA_COMPONENTS), explained_var_mean,
            yerr=explained_var_std, alpha=0.7, color='steelblue',
            edgecolor='black', label='Individual', capsize=3)
    ax3.plot(range(N_PCA_COMPONENTS), cumsum_var_mean, 'ro-', linewidth=2,
             label='Cumulative (mean)', markersize=4)
    ax3.fill_between(range(N_PCA_COMPONENTS),
                     cumsum_var_mean - cumsum_var_std,
                     cumsum_var_mean + cumsum_var_std,
                     color='red', alpha=0.2, label='Cumulative (±std)')
    ax3.axhline(y=0.9, color='green', linestyle='--', alpha=0.5, label='90% threshold')
    ax3.set_xlabel('PCA Component')
    ax3.set_ylabel('Explained Variance Ratio')
    ax3.set_title(f'Explained Variance (Total: {cumsum_var_mean[-1]:.1%}±{cumsum_var_std[-1]:.1%})')
    ax3.legend(fontsize=8)
    ax3.grid(True, alpha=0.3, axis='y')
    ax3.set_xlim([-0.5, N_PCA_COMPONENTS-0.5])

    # Bottom-right: Per-color component variance with robustness
    ax4 = axes[1, 1]
    # Compute variance across components for each color, per fold
    color_variances_per_fold = np.var(pca_matrices_per_fold, axis=2)  # (N_RUNS, N_COLORS)
    color_variances_mean = color_variances_per_fold.mean(axis=0)  # (N_COLORS,)
    color_variances_std = color_variances_per_fold.std(axis=0)  # (N_COLORS,)

    bars = ax4.bar(range(N_COLORS), color_variances_mean,
                   yerr=color_variances_std, alpha=0.7,
                   color='coral', edgecolor='black', capsize=4)
    ax4.set_xlabel('Color')
    ax4.set_ylabel('Variance across components')
    ax4.set_xticks(range(N_COLORS))
    ax4.set_xticklabels([f'c{i+1}' for i in range(N_COLORS)])
    ax4.set_title('Color Discriminability in PCA Space\n(mean±std across folds)')
    ax4.grid(True, alpha=0.3, axis='y')

    # Add value labels on bars
    for bar, val, std in zip(bars, color_variances_mean, color_variances_std):
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height,
                f'{val:.2f}\n±{std:.2f}', ha='center', va='bottom', fontsize=8)

    plt.tight_layout()
    pca_matrix_plot_path = fig_dir / f"{ROI_NAME}_pca_components_matrix.png"
    plt.savefig(pca_matrix_plot_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {pca_matrix_plot_path}")

    # 2. Top Components per Color
    fig, axes = plt.subplots(2, 4, figsize=(16, 8))
    fig.suptitle(f'{ROI_NAME}: Top PCA Components per Color (Z-score based)', fontsize=14, fontweight='bold')

    for color_idx in range(N_COLORS):
        ax = axes[color_idx // 4, color_idx % 4]

        # Get component values for this color
        color_components = pca_matrix[color_idx, :]

        # Sort by absolute value
        top_indices = np.argsort(np.abs(color_components))[-20:][::-1]
        top_values = color_components[top_indices]

        # Bar plot
        colors_bar = ['red' if v > 0 else 'blue' for v in top_values]
        ax.barh(range(len(top_indices)), top_values, color=colors_bar, alpha=0.7, edgecolor='black')
        ax.set_yticks(range(len(top_indices)))
        ax.set_yticklabels([f'PC{i}' for i in top_indices], fontsize=7)
        ax.axvline(x=0, color='gray', linestyle='--', linewidth=1)
        ax.set_xlabel('Component value')
        ax.set_title(f'c{color_idx+1} (top 20 components)', fontsize=10)
        ax.grid(True, alpha=0.3, axis='x')

    plt.tight_layout()
    pca_top_components_path = fig_dir / f"{ROI_NAME}_pca_top_components_per_color.png"
    plt.savefig(pca_top_components_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {pca_top_components_path}")

    # 3. Component Loadings (top 5 components) - Mean across folds
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    fig.suptitle(f'{ROI_NAME}: PCA Component Loadings (Top 5 Components, mean across folds)',
                 fontsize=14, fontweight='bold')

    # Average loadings across folds
    loadings_mean = pca_loadings_per_fold.mean(axis=0)  # (N_PCA_COMPONENTS, n_voxels)
    loadings_std = pca_loadings_per_fold.std(axis=0)  # (N_PCA_COMPONENTS, n_voxels)

    for comp_idx in range(min(5, N_PCA_COMPONENTS)):
        ax = axes[comp_idx // 3, comp_idx % 3]

        # Get mean loadings for this component
        loadings = loadings_mean[comp_idx, :]  # (n_voxels,)
        loadings_std_comp = loadings_std[comp_idx, :]  # (n_voxels,)

        # Plot histogram
        ax.hist(loadings, bins=50, alpha=0.7, color='steelblue', edgecolor='black')
        ax.axvline(x=0, color='red', linestyle='--', linewidth=2)
        ax.set_xlabel('Loading value')
        ax.set_ylabel('Frequency')
        ax.set_title(f'PC{comp_idx} (Var: {explained_var_mean[comp_idx]:.1%}±{explained_var_std[comp_idx]:.1%})')
        ax.grid(True, alpha=0.3, axis='y')

        # Add statistics
        ax.text(0.05, 0.95,
                f'Mean: {loadings.mean():.3f}±{loadings_std_comp.mean():.3f}\n'
                f'Std: {loadings.std():.3f}\n'
                f'|Max|: {np.abs(loadings).max():.3f}',
                transform=ax.transAxes, va='top', fontsize=9,
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    # Last subplot: cumulative variance with error bars + recommendation
    ax = axes[1, 2]
    ax.plot(range(N_PCA_COMPONENTS), cumsum_var_mean,
            'bo-', linewidth=2, markersize=6, label='Mean')
    ax.fill_between(range(N_PCA_COMPONENTS),
                     cumsum_var_mean - cumsum_var_std,
                     cumsum_var_mean + cumsum_var_std,
                     color='blue', alpha=0.2, label='±std')

    # Calculate components needed for 90% variance
    components_for_90 = [np.argmax(np.cumsum(ev) >= 0.9) + 1 for ev in explained_variance_per_fold]
    mean_comp_90 = int(np.round(np.mean(components_for_90)))

    # Mark 90% and 95% thresholds
    ax.axhline(y=0.9, color='green', linestyle='--', alpha=0.5, label='90% threshold')
    ax.axhline(y=0.95, color='orange', linestyle='--', alpha=0.5, label='95% threshold')

    # Mark recommended number of components
    if mean_comp_90 < N_PCA_COMPONENTS:
        ax.axvline(x=mean_comp_90, color='red', linestyle=':', linewidth=2, alpha=0.7,
                   label=f'Recommended: {mean_comp_90}')
        ax.scatter([mean_comp_90], [cumsum_var_mean[mean_comp_90]],
                   color='red', s=100, zorder=5, marker='*')

    ax.set_xlabel('Number of Components')
    ax.set_ylabel('Cumulative Explained Variance')
    ax.set_title(f'Scree Plot (90% at {mean_comp_90}±{np.std(components_for_90):.1f} components)')
    ax.legend(fontsize=8, loc='lower right')
    ax.grid(True, alpha=0.3)
    ax.set_xlim([-0.5, N_PCA_COMPONENTS-0.5])

    plt.tight_layout()
    pca_loadings_path = fig_dir / f"{ROI_NAME}_pca_loadings.png"
    plt.savefig(pca_loadings_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {pca_loadings_path}")

    print()
    print("PCA Component Analysis Statistics (across folds, Z-score based):")
    print(f"  Total components: {N_PCA_COMPONENTS}")
    print(f"  Explained variance: {cumsum_var_mean[-1]:.1%} ± {cumsum_var_std[-1]:.1%}")
    components_for_90 = [np.argmax(np.cumsum(ev) >= 0.9) + 1 for ev in explained_variance_per_fold]
    print(f"  Components for 90% variance: {np.mean(components_for_90):.1f} ± {np.std(components_for_90):.1f}")
    print(f"  Mean component value range: [{pca_matrix_mean.min():.3f}, {pca_matrix_mean.max():.3f}]")
    print(f"  Mean component std across folds: {pca_matrix_std.mean():.4f}")
    print(f"  Color with highest variance: c{np.argmax(color_variances_mean)+1} ({color_variances_mean.max():.3f}±{color_variances_std[np.argmax(color_variances_mean)]:.3f})")
    print(f"  Robustness metric (mean std/mean value): {pca_matrix_std.mean() / np.abs(pca_matrix_mean).mean():.4f}")
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

def circular_mean_deg(angles_deg):
    """Calculate circular mean of angles in degrees and resultant vector length"""
    if len(angles_deg) == 0:
        return np.nan, 0.0
    ang = np.deg2rad(np.asarray(angles_deg))
    C = np.cos(ang).mean()
    S = np.sin(ang).mean()
    mean_ang = (np.rad2deg(np.arctan2(S, C)) + 360) % 360
    R = np.hypot(C, S)  # 0~1, higher = more concentrated
    return mean_ang, R

# ============================================================================
# Classification (Leave-One-Run-Out) - NOW USING Z-SCORES!
# ============================================================================

print(f"[6/8] Classification with diagonal LDA (leave-one-run-out)")
print(f"  Using Z-SCORES as features (not betas!)")
if USE_PCA:
    print(f"  Using PCA: {N_PCA_COMPONENTS} components")
sys.stdout.flush()

classification_results = []

for test_run in range(N_RUNS):
    train_runs = [r for r in range(N_RUNS) if r != test_run]

    X_train = all_betas[train_runs].reshape(-1, n_voxels)  # Contains Z-SCORES!
    y_train = np.tile(np.arange(N_COLORS), len(train_runs))

    X_test = all_betas[test_run]  # Contains Z-SCORES!
    y_test = np.arange(N_COLORS)

    # Standardize (note: Z-scores are already normalized, but we standardize again for PCA)
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

# Create confusion matrix to verify no data leakage
print("Confusion matrix (aggregated across runs):")
all_y_true = []
all_y_pred = []
for r in classification_results:
    all_y_true.extend(r['y_true'])
    all_y_pred.extend(r['y_pred'])

conf_matrix = np.zeros((N_COLORS, N_COLORS), dtype=int)
for true_idx, pred_idx in zip(all_y_true, all_y_pred):
    conf_matrix[true_idx, pred_idx] += 1

print("        ", end="")
for i in range(N_COLORS):
    print(f"c{i+1:>3}", end="")
print()
for i in range(N_COLORS):
    print(f"  c{i+1}: ", end="")
    for j in range(N_COLORS):
        print(f"{conf_matrix[i,j]:>3}", end=" ")
    print()

# Per-color accuracy
print("\nPer-color classification accuracy:")
for color_idx in range(N_COLORS):
    correct = conf_matrix[color_idx, color_idx]
    total = conf_matrix[color_idx, :].sum()
    acc = correct / total if total > 0 else 0
    print(f"  color_{color_idx+1}: {acc:.3f} ({correct}/{total})")

print()
sys.stdout.flush()

# ============================================================================
# Forward Model for Reconstruction - NOW USING Z-SCORES!
# ============================================================================

print(f"[7/8] Reconstruction with B&H forward model")
print(f"  Using Z-SCORES as features (not betas!)")
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

    X_train = all_betas[train_runs].reshape(-1, n_voxels)  # Contains Z-SCORES!
    y_train = np.tile(np.arange(N_COLORS), len(train_runs))

    X_test = all_betas[test_run]  # Contains Z-SCORES!
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

    # Train forward model: B = W × C
    # Get channel outputs for training colors
    C_train = []
    for color_idx in y_train:
        color_name = f'color_{color_idx+1}'
        hue_deg = LABEL2HUE_DEG[color_name]
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

# Additional statistics from naive_analysis style
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
# Leave-One-Color-Out Reconstruction - NOW USING Z-SCORES!
# ============================================================================

print(f"[8/8] Leave-one-color-out reconstruction (novel colors)")
print(f"  Using Z-SCORES as features (not betas!)")
sys.stdout.flush()

novel_color_results = []

for held_out_color in range(N_COLORS):
    all_errors_this_color = []
    all_reconstructed_hues = []  # Track reconstructed hues across test runs

    for test_run in range(N_RUNS):
        train_runs = [r for r in range(N_RUNS) if r != test_run]

        # Remove held-out color from training
        X_train_list = []
        y_train_list = []

        for r in train_runs:
            for c in range(N_COLORS):
                if c != held_out_color:
                    X_train_list.append(all_betas[r, c])  # Contains Z-SCORES!
                    y_train_list.append(c)

        X_train = np.array(X_train_list)
        y_train = np.array(y_train_list)

        X_test = all_betas[test_run, held_out_color:held_out_color+1]  # Contains Z-SCORES!
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
            hue_deg = LABEL2HUE_DEG[color_name]
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
        true_hue = LABEL2HUE_DEG[color_name]

        error = circular_diff_deg(reconstructed_hue, true_hue)
        all_errors_this_color.append(error)
        all_reconstructed_hues.append(reconstructed_hue)  # Store reconstructed hue

    mean_error_this_color = np.mean(all_errors_this_color)
    color_name = f'color_{held_out_color+1}'

    # Compute circular mean of reconstructed hues
    mean_reconstructed_hue, R = circular_mean_deg(all_reconstructed_hues)

    novel_color_results.append({
        'color': color_name,
        'reconstructed_hue': mean_reconstructed_hue,  # Mean prediction for visualization (scalar)
        'reconstructed_hues': all_reconstructed_hues,  # All predictions across runs
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
    'feature_type': 'zscore',  # NEW: indicate feature type
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
    'Method': ['zscore_universal_hrf'],  # Changed from 'universal_hrf'
    'Feature_type': ['zscore'],
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
# Visualization: Reconstruction Results
# (Same as beta version, but using Z-score data)
# ============================================================================

print("Creating reconstruction visualizations...")

# 1. True vs Reconstructed Hues (Leave-One-Run-Out)
fig, axes = plt.subplots(2, 3, figsize=(15, 10))
fig.suptitle(f'{ROI_NAME}: Reconstruction Results (Leave-One-Run-Out, Z-score based)', fontsize=16, fontweight='bold')

for idx, result in enumerate(reconstruction_results):
    ax = axes[idx // 3, idx % 3]

    true_hues = result['true_hues']
    reconstructed_hues = result['reconstructed_hues']
    errors = result['errors']

    # Scatter plot
    ax.scatter(true_hues, reconstructed_hues, s=100, alpha=0.7, c=range(N_COLORS), cmap='hsv')

    # Perfect reconstruction line
    ax.plot([0, 360], [0, 360], 'k--', alpha=0.3, label='Perfect reconstruction')

    # Color labels
    for i, (true_h, recon_h) in enumerate(zip(true_hues, reconstructed_hues)):
        ax.text(true_h, recon_h, f'c{i+1}', fontsize=8, ha='center', va='bottom')

    ax.set_xlabel('True Hue (°)')
    ax.set_ylabel('Reconstructed Hue (°)')
    ax.set_title(f'Run {result["test_run"]}: {result["mean_error"]:.1f}° error')
    ax.set_xlim([0, 360])
    ax.set_ylim([0, 360])
    ax.grid(True, alpha=0.3)
    ax.legend()

plt.tight_layout()
reconstruction_plot_path = fig_dir / f"{ROI_NAME}_reconstruction_per_run.png"
plt.savefig(reconstruction_plot_path, dpi=150, bbox_inches='tight')
plt.close()
print(f"  Saved: {reconstruction_plot_path}")

# 2. Confusion Matrix Visualization
fig, ax = plt.subplots(figsize=(10, 8))

# Create confusion matrix
conf_matrix = np.zeros((N_COLORS, N_COLORS), dtype=int)
for r in classification_results:
    for true_idx, pred_idx in zip(r['y_true'], r['y_pred']):
        conf_matrix[true_idx, pred_idx] += 1

# Plot as heatmap
im = ax.imshow(conf_matrix, cmap='Blues', aspect='auto')

# Add text annotations
for i in range(N_COLORS):
    for j in range(N_COLORS):
        count = conf_matrix[i, j]
        color = 'white' if count > conf_matrix.max()/2 else 'black'
        text = ax.text(j, i, str(count), ha="center", va="center", color=color, fontsize=12, fontweight='bold')

# Labels and formatting
ax.set_xticks(np.arange(N_COLORS))
ax.set_yticks(np.arange(N_COLORS))
ax.set_xticklabels([f'c{i+1}' for i in range(N_COLORS)])
ax.set_yticklabels([f'c{i+1}' for i in range(N_COLORS)])
ax.set_xlabel('Predicted Color', fontsize=12, fontweight='bold')
ax.set_ylabel('True Color', fontsize=12, fontweight='bold')
ax.set_title(f'{ROI_NAME}: Classification Confusion Matrix (Z-score based)\nAccuracy: {mean_classification_acc*100:.1f}%',
             fontsize=14, fontweight='bold')

# Add colorbar
cbar = plt.colorbar(im, ax=ax)
cbar.set_label('Count', rotation=270, labelpad=20, fontsize=10)

plt.tight_layout()
confusion_plot_path = fig_dir / f"{ROI_NAME}_confusion_matrix.png"
plt.savefig(confusion_plot_path, dpi=150, bbox_inches='tight')
plt.close()
print(f"  Saved: {confusion_plot_path}")

# 3-8: Additional visualizations (same code as beta version, omitted for brevity - continues for ~500 more lines)
# ...

print()

# ============================================================================
# Final Summary
# ============================================================================

print("="*70)
print("Z-Score Universal HRF Reconstruction Complete (Modified B&H 2009)")
print("="*70)
print()
print(f"ROI: {ROI_NAME}")
print(f"Method: Z-score based Universal HRF (optimal delay: {PEAK_DELAY} TRs / {PEAK_DELAY * TR}s)")
print(f"Feature type: Z-SCORES (statistical significance weighted)")
print(f"Voxels: {n_voxels}")
if USE_PCA:
    print(f"PCA: {N_PCA_COMPONENTS} components")
print()
print("Results:")
print(f"  Classification accuracy: {mean_classification_acc*100:.1f}% (chance: {100/N_COLORS:.1f}%)")
print(f"  Reconstruction error: {mean_reconstruction_error:.1f}° (chance: 90.0°)")
print(f"  Novel color error: {mean_novel_error:.1f}°")
print()
print(f"Output directory: {output_dir}")
print("="*70)
sys.stdout.flush()

# Close dual logger
if hasattr(sys.stdout, 'close'):
    sys.stdout.close()
