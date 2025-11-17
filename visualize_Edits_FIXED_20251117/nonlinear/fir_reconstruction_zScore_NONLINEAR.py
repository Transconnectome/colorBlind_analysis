#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UNIFIED_fir_reconstruction_zScore.py
--------------------------------------------
Z-Score based Universal HRF reconstruction with ALL THREE CHANGES INTEGRATED:

**KEY DIFFERENCE**: Uses Z-scores instead of Betas for all analyses

CHANGE 1: Output directory structure (using OutputManager)
CHANGE 2: PCA with leave-one-run-out CV (already in original)
CHANGE 3: Accurate Lab→RGB color conversion for figures

Two-stage approach:
1. Fit FIR to estimate HRF shape averaged across all ROI voxels
2. Find optimal delay from universal HRF
3. Extract betas at that single optimal delay for all voxels

Features:
- Universal HRF estimation (B&H 2009 method)
- Correct Lab hue values (from pilot data)
- ACCURATE Lab→RGB color conversion for visualization
- Diagonal LDA classification (paper method)
- B&H forward model for reconstruction
- Optional PCA dimensionality reduction
- Reorganized output structure: logs/{timestamp}/{method}_{ROI}/sub-{ID}_...

Usage:
    python UNIFIED_fir_reconstruction_zScore.py --roi V2 --use-pca --n-components 20
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

# CHANGE 3: Actual stimulus colors in CIELab for ACCURATE RGB conversion
# These Lab values define the ACTUAL colors shown to subjects
COLOR_LAB_TEST = {
    'color_1': [75, 40.0, 0.0],        # 0°: Red
    'color_2': [75, 28.28, 28.28],     # 45°: Orange
    'color_3': [75, 0.0, 40.0],        # 90°: Yellow
    'color_4': [75, -28.28, 28.28],    # 135°: Green
    'color_5': [75, -40.0, 0.0],       # 180°: Cyan
    'color_6': [75, -28.28, -28.28],   # 225°: Blue
    'color_7': [75, 0.0, -40.0],       # 270°: Violet
    'color_8': [75, 28.28, -28.28],    # 315°: Pinkish
}

# Pilot colors (computed from pilot hue angles with L=75, C=40)
COLOR_LAB_PILOT = {}
for i in range(1, 9):
    color_name = f'color_{i}'
    hue_deg = LABEL2HUE_DEG_PILOT[color_name]
    hue_rad = np.deg2rad(hue_deg)
    # Convert hue to Lab a, b with C=40
    a = 40.0 * np.cos(hue_rad)
    b = 40.0 * np.sin(hue_rad)
    COLOR_LAB_PILOT[color_name] = [75, a, b]

# Experiment parameters
TR = 1.5
N_RUNS = 6
N_COLORS = 8

# FIR parameters
FIR_DELAYS = range(10)  # 0-15 seconds (10 TRs × 1.5s)
PEAK_DELAY = 3  # ~4.5s post-onset (typical HRF peak)

# ============================================================================
# CHANGE 3: Accurate Lab to RGB Conversion
# ============================================================================

def lab_to_rgb(L, a, b):
    """
    Convert CIELab to RGB using proper color space conversion

    Parameters:
    -----------
    L : float (0-100)
        Lightness
    a : float (-128 to 127)
        Green-Red axis
    b : float (-128 to 127)
        Blue-Yellow axis

    Returns:
    --------
    rgb : tuple (R, G, B) in range [0, 1]
    """
    try:
        from skimage.color import lab2rgb
        # skimage expects Lab in shape (1, 1, 3) with L in [0, 100]
        lab_array = np.array([[[L, a, b]]])
        rgb_array = lab2rgb(lab_array)
        rgb = rgb_array[0, 0, :]
        # Clip to valid range
        rgb = np.clip(rgb, 0, 1)
        return tuple(rgb)
    except ImportError:
        # Fallback: use simplified conversion if skimage not available
        print("Warning: skimage not available, using HSV approximation")
        hue_deg = np.rad2deg(np.arctan2(b, a)) % 360
        h = hue_deg / 360.0
        s = 0.8
        v = 0.9
        from matplotlib.colors import hsv_to_rgb
        return tuple(hsv_to_rgb([h, s, v]))

def get_color_rgb(color_name, color_lab_dict):
    """
    Get RGB color for a given color name

    Parameters:
    -----------
    color_name : str
        Color name (e.g., 'color_1')
    color_lab_dict : dict
        Dictionary mapping color names to Lab values

    Returns:
    --------
    rgb : tuple (R, G, B) in range [0, 1]
    """
    L, a, b = color_lab_dict[color_name]
    return lab_to_rgb(L, a, b)

# ============================================================================
# Parse Arguments
# ============================================================================

def parse_args():
    parser = argparse.ArgumentParser(description='FIR-based color reconstruction (UNIFIED)')
    parser.add_argument('--subject', type=str, default='P01',
                        help='Subject ID (P01 for pilot, 01-04 for test subjects)')
    parser.add_argument('--roi', type=str, default='V2',
                        help='ROI name (e.g., V1, V2, V3, V4, hV4)')
    parser.add_argument('--use-pca', action='store_true',
                        help='Use PCA dimensionality reduction')
    parser.add_argument('--n-components', type=int, default=20,
                        help='Number of PCA components (only if --use-pca)')
    parser.add_argument('--save-zmaps', action='store_true',
                        help='Save z-maps for each color')
    parser.add_argument('--timestamp', type=str, default=None,
                        help='Timestamp for output directory (e.g., 20251117_143022). '
                             'If not specified, generates automatically.')
    return parser.parse_args()

args = parse_args()

SUBJECT_ID = args.subject
ROI_NAME = args.roi
USE_PCA = args.use_pca
N_PCA_COMPONENTS = args.n_components
SAVE_ZMAPS = args.save_zmaps
TIMESTAMP_ARG = args.timestamp

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
    COLOR_LAB = COLOR_LAB_PILOT
else:
    FMRIPREP_DIR = f"{FMRIPREP_BASE}/sub-{SUBJECT_ID}"  # Directory name: sub-XX
    FILE_PREFIX = f"sub-{SUBJECT_ID}"  # File prefix: sub-XX
    DERIVATIVE_PREFIX = f"sub-{SUBJECT_ID}"  # Derivative folder: sub-XX
    EVENT_DIR = f"{EVENT_DIR}/sub-{SUBJECT_ID}/func"  # Events in pilot/sub-XX/func/
    LABEL2HUE_DEG = LABEL2HUE_DEG_TEST  # Use test color mapping
    COLOR_LAB = COLOR_LAB_TEST

# ============================================================================
# CHANGE 1: Setup Output Directory with OutputManager
# ============================================================================

from datetime import datetime

# Simple OutputManager class (inline to avoid dependency)
class OutputManager:
    """Manages reorganized output structure: logs/{timestamp}/{method}_{ROI}/sub-{ID}_..."""
    def __init__(self, subject_id, roi_name, method_name, base_dir='logs', timestamp=None):
        self.subject_id = subject_id
        self.roi_name = roi_name
        self.method_name = method_name
        self.base_dir = Path(base_dir)

        if timestamp is None:
            self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        else:
            self.timestamp = timestamp

        # Create method-ROI directory
        self.method_roi_dir = self.base_dir / self.timestamp / f"{method_name}_{roi_name}"
        self.method_roi_dir.mkdir(parents=True, exist_ok=True)

        self.subject_prefix = f"sub-{subject_id}"

    def get_path(self, filename):
        """Get full path with subject prefix"""
        return self.method_roi_dir / f"{self.subject_prefix}_{filename}"

    def get_log_path(self):
        return self.get_path('log.txt')

    def get_results_path(self):
        return self.get_path('results.pkl')

    def get_summary_path(self):
        return self.get_path('summary.csv')

    def get_figure_path(self, figure_type):
        if not figure_type.endswith('.png'):
            figure_type += '.png'
        return self.get_path(figure_type)

# Use provided timestamp or generate new one
if TIMESTAMP_ARG:
    timestamp = TIMESTAMP_ARG
    print(f"Using provided timestamp: {timestamp}")
else:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"Generated new timestamp: {timestamp}")

# CHANGE 1: Create OutputManager
om = OutputManager(
    subject_id=SUBJECT_ID,
    roi_name=ROI_NAME,
    method_name='zScore',
    timestamp=timestamp
)

output_dir = om.method_roi_dir
fig_dir = output_dir  # Figures in same directory as logs

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

log_file = om.get_log_path()
sys.stdout = DualLogger(log_file)
sys.stderr = sys.stdout

print("="*70)
print("UNIFIED Universal HRF Reconstruction Pipeline")
print("="*70)
print(f"Subject: {SUBJECT_ID} (files: {FILE_PREFIX}, derivatives: {DERIVATIVE_PREFIX})")
print(f"ROI: {ROI_NAME}")
print(f"Method: Two-stage universal HRF")
print(f"Use PCA: {USE_PCA}")
if USE_PCA:
    print(f"PCA components: {N_PCA_COMPONENTS}")
print(f"Color mapping: {'PILOT (irregular)' if SUBJECT_ID == 'P01' else 'TEST (regular 45°)'}")
print(f"Output directory: {output_dir}")
print()
print("CHANGES INTEGRATED:")
print("  [1] Output structure: logs/{timestamp}/{method}_{ROI}/sub-{ID}_...")
print("  [2] PCA: Leave-one-run-out CV (no data leakage)")
print("  [3] Colors: Accurate Lab→RGB conversion for figures")
print()
sys.stdout.flush()

# ============================================================================
# Load ROI Mask
# ============================================================================
if SUBJECT_ID == 'P01':
    roi_path = f"derivatives/pilot/{DERIVATIVE_PREFIX}/roi_pipeline_20251111_010954/{ROI_NAME}_mask_thr50_intnearest_binTrue_masknone_gmTrue_subjFalse.nii.gz"
else:
    roi_path = f"derivatives/{DERIVATIVE_PREFIX}/roi_pipeline/{ROI_NAME}_mask_thr50_intnearest_binTrue_masknone_gmTrue_subjFalse.nii.gz"

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

    # Confounds path
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
            contrast_map = fir_model.compute_contrast(contrast_name, output_type='z_score')  # CHANGE: Use Z-scores instead of Betas
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

# Find peak using absolute value (handles negative baseline)
optimal_delay = np.argmax(np.abs(universal_hrf))
optimal_time = optimal_delay * TR

print()
print("  === Universal HRF Analysis ===")
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

hrf_fig_path = om.get_figure_path('universal_hrf.png')
plt.tight_layout()
plt.savefig(hrf_fig_path, dpi=150, bbox_inches='tight')
plt.close()

print(f"  Saved: {hrf_fig_path}")
print()
sys.stdout.flush()

# ============================================================================
# Extract Beta Estimates and Create Z-maps
# ============================================================================

print(f"[5/8] Extracting Z-scores for {N_COLORS} colors (statistical weighting)")
sys.stdout.flush()

all_betas = []  # (n_runs, n_colors, n_voxels)
z_maps = []  # (n_colors,) - z-score maps

for run_idx in range(N_RUNS):
    run_betas = []

    for color_idx in range(1, N_COLORS + 1):
        contrast_name = f'color_{color_idx}_delay_{PEAK_DELAY}'

        try:
            contrast_map = fir_model.compute_contrast(contrast_name, output_type='z_score')  # CHANGE: Use Z-scores instead of Betas
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
    print(f"  Run {run_idx+1}: Extracted {len(run_betas)} color Z-scores")

all_betas = np.array(all_betas)  # (n_runs, n_colors, n_voxels)
print(f"  Total shape: {all_betas.shape}")
print()
sys.stdout.flush()

# Save z-maps (if requested)
if SAVE_ZMAPS:
    print("  Saving z-maps for each color...")
    zmaps_dir = output_dir / "zmaps"
    zmaps_dir.mkdir(exist_ok=True)

    for color_idx, z_map in enumerate(z_maps, start=1):
        if z_map is not None:
            zmap_path = zmaps_dir / f"{om.subject_prefix}_color_{color_idx}_zmap.nii.gz"
            nib.save(z_map, zmap_path)

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
# Classification (Leave-One-Run-Out)
# ============================================================================

print(f"[6/8] Classification with diagonal LDA (leave-one-run-out)")
if USE_PCA:
    print(f"  Using PCA: {N_PCA_COMPONENTS} components")
sys.stdout.flush()

classification_results = []

for test_run in range(N_RUNS):
    train_runs = [r for r in range(N_RUNS) if r != test_run]

    X_train = all_betas[train_runs].reshape(-1, n_voxels)
    y_train = np.tile(np.arange(N_COLORS), len(train_runs))

    X_test = all_betas[test_run]
    y_test = np.arange(N_COLORS)

    # Standardize
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Optional PCA (CHANGE 2: fit on train set only!)
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

for test_run in range(N_RUNS):
    train_runs = [r for r in range(N_RUNS) if r != test_run]

    X_train = all_betas[train_runs].reshape(-1, n_voxels)
    y_train = np.tile(np.arange(N_COLORS), len(train_runs))

    X_test = all_betas[test_run]
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

for held_out_color in range(N_COLORS):
    all_errors_this_color = []
    all_reconstructed_hues = []

    for test_run in range(N_RUNS):
        train_runs = [r for r in range(N_RUNS) if r != test_run]

        # Remove held-out color from training
        X_train_list = []
        y_train_list = []

        for r in train_runs:
            for c in range(N_COLORS):
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

        reconstructed_hue = np.argmax(correlations)

        color_name = f'color_{held_out_color+1}'
        true_hue = LABEL2HUE_DEG[color_name]

        error = circular_diff_deg(reconstructed_hue, true_hue)
        all_errors_this_color.append(error)
        all_reconstructed_hues.append(reconstructed_hue)

    mean_error_this_color = np.mean(all_errors_this_color)
    color_name = f'color_{held_out_color+1}'

    # Compute circular mean of reconstructed hues
    mean_reconstructed_hue, R = circular_mean_deg(all_reconstructed_hues)

    novel_color_results.append({
        'color': color_name,
        'reconstructed_hue': mean_reconstructed_hue,
        'reconstructed_hues': all_reconstructed_hues,
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
results_path = om.get_results_path()
with open(results_path, 'wb') as f:
    pickle.dump(results, f)

print(f"  Saved: {results_path}")

# Save summary CSV
summary_data = {
    'ROI': [ROI_NAME],
    'Method': ['zScore'],
    'N_voxels': [n_voxels],
    'Optimal_delay_TRs': [PEAK_DELAY],
    'Use_PCA': [USE_PCA],
    'N_components': [N_PCA_COMPONENTS if USE_PCA else n_voxels],
    'Classification_accuracy': [mean_classification_acc],
    'Reconstruction_error_deg': [mean_reconstruction_error],
    'Novel_color_error_deg': [mean_novel_error]
}

summary_df = pd.DataFrame(summary_data)
summary_csv_path = om.get_summary_path()
summary_df.to_csv(summary_csv_path, index=False)

print(f"  Saved: {summary_csv_path}")
print()

# ============================================================================
# CHANGE 3: Visualization with ACCURATE Lab→RGB Colors
# ============================================================================

print("Creating reconstruction visualizations with ACCURATE colors...")
print()

# 1. Confusion Matrix
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
        text = ax.text(j, i, str(count), ha="center", va="center",
                      color=color, fontsize=12, fontweight='bold')

# Labels and formatting
ax.set_xticks(np.arange(N_COLORS))
ax.set_yticks(np.arange(N_COLORS))
ax.set_xticklabels([f'c{i+1}' for i in range(N_COLORS)])
ax.set_yticklabels([f'c{i+1}' for i in range(N_COLORS)])
ax.set_xlabel('Predicted Color', fontsize=12, fontweight='bold')
ax.set_ylabel('True Color', fontsize=12, fontweight='bold')
ax.set_title(f'{ROI_NAME}: Classification Confusion Matrix\nAccuracy: {mean_classification_acc*100:.1f}%',
             fontsize=14, fontweight='bold')

# Add colorbar
cbar = plt.colorbar(im, ax=ax)
cbar.set_label('Count', rotation=270, labelpad=20, fontsize=10)

plt.tight_layout()
confusion_plot_path = om.get_figure_path('confusion_matrix.png')
plt.savefig(confusion_plot_path, dpi=150, bbox_inches='tight')
plt.close()
print(f"  Saved: {confusion_plot_path}")

# 2. CHANGE 3: Polar plot with ACCURATE Lab→RGB colors
fig = plt.figure(figsize=(7, 7))
ax = plt.subplot(111, projection='polar')
ax.set_title("All runs: True hues and prediction clusters\n(ACCURATE Lab colors)", pad=18)
ax.set_rticks([])
ax.set_theta_zero_location("E")
ax.set_theta_direction(-1)
ax.grid(alpha=0.25)

rng = np.random.default_rng(3)
r_center = 1.0
r_pred_base = 0.92

# Plot each color with ACCURATE Lab→RGB conversion
for color_idx in range(N_COLORS):
    color_name = f'color_{color_idx+1}'
    true_hue = LABEL2HUE_DEG[color_name]
    theta_true = np.deg2rad(true_hue)

    # CHANGE 3: Get ACCURATE stimulus RGB color from Lab
    stim_rgb = get_color_rgb(color_name, COLOR_LAB)

    # Center point (true hue with accurate stimulus color)
    ax.scatter([theta_true], [r_center], s=110, color=stim_rgb,
               edgecolor='k', linewidths=0.8, zorder=4)

    # Prediction points: POSITION = predicted angle, COLOR = true stimulus
    preds = []
    for result in reconstruction_results:
        preds.append(result['reconstructed_hues'][color_idx])

    if len(preds):
        thetas = np.deg2rad(np.array(preds))
        r_jit = r_pred_base + rng.uniform(-0.05, 0.05, size=len(thetas))
        ax.scatter(thetas, r_jit, s=28, color=stim_rgb, alpha=0.65, zorder=3)

        # Circular mean vector
        mu_deg, R = circular_mean_deg(preds)
        if not np.isnan(mu_deg):
            mu = np.deg2rad(mu_deg)
            r0, r1 = 0.70, 0.70 + 0.20*R
            ax.plot([mu, mu], [r0, r1], color=stim_rgb,
                    linewidth=2.0, alpha=0.9, zorder=2)

# Legend
from matplotlib.lines import Line2D
legend_elems = [
    Line2D([0],[0], marker='o', color='w', markerfacecolor='gray',
           markeredgecolor='k', label='True hue (accurate Lab color)', markersize=10),
    Line2D([0],[0], marker='o', color='w', markerfacecolor='gray',
           alpha=0.65, label='Predictions (all runs)', markersize=6),
    Line2D([0],[0], color='gray', lw=2, label='Circular mean vector')
]
ax.legend(handles=legend_elems, loc='upper right', bbox_to_anchor=(1.25, 1.2))

plt.tight_layout()
polar_recon_plot_path = om.get_figure_path('polar_reconstruction.png')
plt.savefig(polar_recon_plot_path, dpi=150, bbox_inches='tight')
plt.close()
print(f"  Saved: {polar_recon_plot_path}")

# 3. CHANGE 3: Circular Color Space with ACCURATE colors
fig = plt.figure(figsize=(14, 6))

# Left: Training colors reconstruction
ax1 = fig.add_subplot(1, 2, 1, projection='polar')
ax1.set_theta_zero_location("E")
ax1.set_theta_direction(-1)
ax1.set_rticks([])
ax1.grid(alpha=0.25)

rng = np.random.default_rng(42)
r_center = 1.0
r_pred_base = 0.85

# Plot with ACCURATE Lab colors
for color_idx in range(N_COLORS):
    color_name = f'color_{color_idx + 1}'
    true_hue = LABEL2HUE_DEG[color_name]
    true_rgb = get_color_rgb(color_name, COLOR_LAB)  # CHANGE 3

    # True color at border
    ax1.scatter([np.deg2rad(true_hue)], [r_center], s=110,
               color=true_rgb, edgecolor='k', linewidths=0.8, zorder=4)

    # Predictions
    for result in reconstruction_results:
        pred_hue = result['reconstructed_hues'][color_idx]
        r_jit = r_pred_base + rng.uniform(-0.03, 0.03)
        ax1.scatter([np.deg2rad(pred_hue)], [r_jit], s=28,
                   color=true_rgb, alpha=0.65, zorder=3)

ax1.set_ylim([0, 1.1])
ax1.set_title(f'Training Colors (ACCURATE Lab→RGB)\nMean error: {mean_reconstruction_error:.1f}°',
             fontsize=12, fontweight='bold')

# Right: Novel colors reconstruction
ax2 = fig.add_subplot(1, 2, 2, projection='polar')
ax2.set_theta_zero_location("E")
ax2.set_theta_direction(-1)
ax2.set_rticks([])
ax2.grid(alpha=0.25)

for result in novel_color_results:
    color_name = result['color']
    true_hue = LABEL2HUE_DEG[color_name]
    true_rgb = get_color_rgb(color_name, COLOR_LAB)  # CHANGE 3

    # True color at border
    ax2.scatter([np.deg2rad(true_hue)], [r_center], s=110,
               color=true_rgb, edgecolor='k', linewidths=0.8, zorder=4)

    # All predictions
    all_pred_hues = result['reconstructed_hues']
    for pred_hue in all_pred_hues:
        r_jit = r_pred_base + rng.uniform(-0.03, 0.03)
        ax2.scatter([np.deg2rad(pred_hue)], [r_jit], s=28,
                   color=true_rgb, alpha=0.65, zorder=3)

    # Mean vector
    mean_pred_hue, R = circular_mean_deg(all_pred_hues)
    ax2.arrow(np.deg2rad(mean_pred_hue), 0, 0, r_pred_base * R,
             head_width=0.1, head_length=0.05, fc=true_rgb, ec='k',
             linewidth=1.5, alpha=0.35, zorder=2)

ax2.set_ylim([0, 1.1])
ax2.set_title(f'Novel Colors (Leave-One-Out)\nMean error: {mean_novel_error:.1f}°',
             fontsize=12, fontweight='bold')

# Legend
legend_elems = [
    Line2D([0],[0], marker='o', color='w', markerfacecolor='gray', markeredgecolor='k',
           label='True hue (accurate Lab)', markersize=10),
    Line2D([0],[0], marker='o', color='w', markerfacecolor='gray', alpha=0.65,
           label='Predictions', markersize=6),
    Line2D([0],[0], color='gray', lw=1, label='Mean vector (novel)')
]
ax2.legend(handles=legend_elems, loc='upper right', bbox_to_anchor=(1.28, 1.15), fontsize=9)

plt.suptitle(f'{ROI_NAME}: Circular Color Space (ACCURATE Lab colors)',
            fontsize=14, fontweight='bold')
plt.tight_layout()
circular_plot_path = om.get_figure_path('circular_color_space.png')
plt.savefig(circular_plot_path, dpi=150, bbox_inches='tight')
plt.close()
print(f"  Saved: {circular_plot_path}")

print()

# ============================================================================
# PCA 3D Colorspace Visualization
# ============================================================================

if USE_PCA and N_PCA_COMPONENTS >= 3:
    print("Creating PCA 3D colorspace visualization (PC1, PC2, PC3)...")
    
    # Compute mean PCA-transformed data for each color across all runs
    pca_3d_data = []  # (N_COLORS, 3) - PC1, PC2, PC3 coordinates
    
    for color_idx in range(N_COLORS):
        # Use leave-one-run-out to get PCA-transformed test data
        color_pca_coords = []
        
        for test_run in range(N_RUNS):
            train_runs = [r for r in range(N_RUNS) if r != test_run]
            
            X_train = all_betas[train_runs].reshape(-1, n_voxels)
            X_test = all_betas[test_run]
            
            # Standardize
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # PCA (need at least 3 components for 3D plot)
            pca = PCA(n_components=max(N_PCA_COMPONENTS, 3))
            pca.fit(X_train_scaled)
            X_test_pca = pca.transform(X_test_scaled)
            
            # Get this color's coordinates (first 3 PCs)
            color_pca_coords.append(X_test_pca[color_idx, :3])
        
        # Average across runs
        mean_coords = np.mean(color_pca_coords, axis=0)
        pca_3d_data.append(mean_coords)
    
    pca_3d_data = np.array(pca_3d_data)  # (N_COLORS, 3)
    
    # Create 3D scatter plot
    from mpl_toolkits.mplot3d import Axes3D
    
    fig = plt.figure(figsize=(16, 7))
    
    # Left plot: 3D scatter with accurate Lab colors
    ax1 = fig.add_subplot(121, projection='3d')
    
    for color_idx in range(N_COLORS):
        color_name = f'color_{color_idx+1}'
        color_rgb = get_color_rgb(color_name, COLOR_LAB)
        
        pc1, pc2, pc3 = pca_3d_data[color_idx]
        
        # Plot point
        ax1.scatter(pc1, pc2, pc3, c=[color_rgb], s=300, 
                   edgecolor='k', linewidths=2.5, alpha=0.9, depthshade=True)
        
        # Add label with offset
        ax1.text(pc1*1.1, pc2*1.1, pc3*1.1, f'c{color_idx+1}', 
                fontsize=11, fontweight='bold', ha='center', va='center')
    
    ax1.set_xlabel('PC1 (1st Principal Component)', fontsize=12, fontweight='bold', labelpad=10)
    ax1.set_ylabel('PC2 (2nd Principal Component)', fontsize=12, fontweight='bold', labelpad=10)
    ax1.set_zlabel('PC3 (3rd Principal Component)', fontsize=12, fontweight='bold', labelpad=10)
    ax1.set_title(f'{ROI_NAME}: Colors in PCA Space (3D)\nAccurate Lab Colors', 
                  fontsize=13, fontweight='bold', pad=15)
    ax1.grid(True, alpha=0.3)
    
    # Set viewing angle for better visualization
    ax1.view_init(elev=20, azim=45)
    
    # Right plot: 2D projection (PC1 vs PC2)
    ax2 = fig.add_subplot(122)
    
    for color_idx in range(N_COLORS):
        color_name = f'color_{color_idx+1}'
        color_rgb = get_color_rgb(color_name, COLOR_LAB)
        
        pc1, pc2, _ = pca_3d_data[color_idx]
        
        # Plot point
        ax2.scatter(pc1, pc2, c=[color_rgb], s=300, 
                   edgecolor='k', linewidths=2.5, alpha=0.9, zorder=3)
        
        # Add label
        ax2.text(pc1*1.05, pc2*1.05, f'c{color_idx+1}', 
                fontsize=11, fontweight='bold', ha='center', va='center', zorder=4)
    
    ax2.set_xlabel('PC1 (1st Principal Component)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('PC2 (2nd Principal Component)', fontsize=12, fontweight='bold')
    ax2.set_title(f'{ROI_NAME}: Colors in PCA Space (2D Projection)\nAccurate Lab Colors', 
                  fontsize=13, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.axhline(y=0, color='k', linestyle='--', alpha=0.3, linewidth=1)
    ax2.axvline(x=0, color='k', linestyle='--', alpha=0.3, linewidth=1)
    ax2.set_aspect('equal', adjustable='box')
    
    plt.tight_layout()
    pca_3d_plot_path = om.get_figure_path('pca_colorspace_3d.png')
    plt.savefig(pca_3d_plot_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {pca_3d_plot_path}")
    print()
    sys.stdout.flush()
elif USE_PCA:
    print(f"  Skipping PCA 3D visualization (need >=3 components, have {N_PCA_COMPONENTS})")
    print()

# ============================================================================
# Final Summary
# ============================================================================

print("="*70)
print("UNIFIED Z-Score Universal HRF Reconstruction Complete")
print("="*70)
print()
print(f"ROI: {ROI_NAME}")
print(f"Method: Universal HRF (optimal delay: {PEAK_DELAY} TRs / {PEAK_DELAY * TR}s)")
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

# Close dual logger and restore original stdout
if isinstance(sys.stdout, DualLogger):
    logger = sys.stdout
    sys.stdout = logger.terminal
    sys.stderr = sys.__stderr__
    logger.close()
