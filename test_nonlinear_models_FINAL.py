#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_nonlinear_models_FINAL.py
==============================
Complete nonlinear forward model testing with FULL visualizations

Purpose:
- Test nonlinear forward models (RF, MLP) vs Linear baseline
- Based on visualize_Edits/fir_reconstruction_zScore.py
- Includes ALL visualizations from baseline + model comparisons
- Default PCA=6 (as per CLAUDE.md and current baseline)

Baseline reference:
- visualize_Edits/fir_reconstruction_zScore.py (ALL 1813 lines)
- ANALYSIS_SUMMARY_20251117.md (PCA=6, zscore method)

Usage:
    python test_nonlinear_models_FINAL.py \
        --subject 01 \
        --roi V2 \
        --n-components 6 \
        --models linear rf mlp \
        --save-zmaps
"""

import sys
import os
import argparse
import numpy as np
import pandas as pd
import nibabel as nib
from pathlib import Path
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# nilearn imports
from nilearn.glm.first_level import FirstLevelModel
from nilearn import image as nimg
from nilearn import plotting
try:
    from nilearn.maskers import NiftiMasker
except ImportError:
    from nilearn.input_data import NiftiMasker

# sklearn imports
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from scipy import stats

# Import forward models
sys.path.insert(0, str(Path(__file__).parent))
from forward_models import LinearForwardModel, RFForwardModel, MLPForwardModel

# ============================================================================
# Configuration (from visualize_Edits baseline)
# ============================================================================

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

# Pilot data (irregular spacing)
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

# Actual stimulus colors in CIELab (for accurate RGB conversion)
COLOR_LAB = {
    'color_1': [75, 40.0, 0.0],        # 0°: Red
    'color_2': [75, 28.28, 28.28],     # 45°: Orange
    'color_3': [75, 0.0, 40.0],        # 90°: Yellow
    'color_4': [75, -28.28, 28.28],    # 135°: Green
    'color_5': [75, -40.0, 0.0],       # 180°: Cyan
    'color_6': [75, -28.28, -28.28],   # 225°: Blue
    'color_7': [75, 0.0, -40.0],       # 270°: Violet
    'color_8': [75, 28.28, -28.28],    # 315°: Pinkish
    'blank': [75, 0.0, 0.0]            # Neutral Gray
}

TR = 1.5
N_RUNS = 6
N_COLORS = 8
FIR_DELAYS = range(10)
VOLS_TO_DROP = 4

# ============================================================================
# Helper Functions (from visualize_Edits)
# ============================================================================

def lab2rgb_accurate(L, a, b, clip=True):
    """Convert CIELab to RGB using proper color space conversion"""
    L, a, b = float(L), float(a), float(b)

    # Lab to XYZ
    y = (L + 16) / 116
    x = a / 500 + y
    z = y - b / 200

    xyz = np.array([x, y, z])
    xyz = np.where(xyz > 0.206893, xyz**3, (xyz - 16/116) / 7.787)
    xyz *= [0.95047, 1., 1.08883]  # D65 white point

    # XYZ to RGB (sRGB matrix)
    rgb = np.dot([[3.2406, -1.5372, -0.4986],
                  [-0.9689, 1.8758, 0.0415],
                  [0.0557, -0.2040, 1.0570]], xyz)

    # Gamma correction
    rgb = np.where(rgb <= 0.0031308, 12.92 * rgb, 1.055 * rgb**(1/2.4) - 0.055)

    if clip:
        rgb = np.clip(rgb, 0, 1)

    return tuple(rgb)

def get_stimulus_color_rgb(color_name):
    """Get actual stimulus RGB color for visualization"""
    if color_name in COLOR_LAB:
        L, a, b = COLOR_LAB[color_name]
        return lab2rgb_accurate(L, a, b)
    else:
        from matplotlib.colors import hsv_to_rgb
        hue_deg = LABEL2HUE_DEG[color_name]
        h = (hue_deg % 360) / 360.0
        return hsv_to_rgb([h, 0.8, 0.9])

def lab_hue_to_rgb(hue_deg, L=70, C=60):
    """Convert Lab hue to RGB color for visualization"""
    from matplotlib.colors import hsv_to_rgb
    h = (hue_deg % 360) / 360.0
    s = 0.8
    v = 0.9
    rgb = hsv_to_rgb([h, s, v])
    return rgb

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
    R = np.hypot(C, S)
    return mean_ang, R

def create_basis_functions(n_channels=6):
    """Create 6-channel basis functions"""
    hues = np.linspace(0, 360, n_channels, endpoint=False)
    basis = np.zeros((360, n_channels))

    for i, center_hue in enumerate(hues):
        for h in range(360):
            dist = np.abs(h - center_hue)
            if dist > 180:
                dist = 360 - dist
            response = np.cos(np.deg2rad(dist))
            if response > 0:
                basis[h, i] = response ** 2
            else:
                basis[h, i] = 0

    return basis

def hue_to_channels(hue_deg, basis_functions):
    """Convert hue to 6 channel outputs"""
    hue_idx = int(np.round(hue_deg)) % 360
    return basis_functions[hue_idx]

def create_forward_model(model_type, args):
    """Factory function to create forward model"""
    if model_type == 'linear':
        return LinearForwardModel()

    elif model_type == 'rf':
        return RFForwardModel(
            n_estimators=args.rf_n_estimators,
            max_depth=args.rf_max_depth,
            min_samples_leaf=args.rf_min_samples_leaf
        )

    elif model_type == 'mlp':
        return MLPForwardModel(
            n_hidden=args.mlp_n_hidden,
            learning_rate=args.mlp_learning_rate,
            weight_decay=args.mlp_weight_decay,
            dropout=args.mlp_dropout,
            n_epochs=args.mlp_n_epochs,
            verbose=False
        )

    else:
        raise ValueError(f"Unknown model type: {model_type}")

# ============================================================================
# Parse Arguments
# ============================================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description='Test nonlinear forward models with FULL visualizations')

    # Data selection
    parser.add_argument('--subject', type=str, default='01',
                        help='Subject ID (01-04 for test, P01 for pilot)')
    parser.add_argument('--roi', type=str, default='V2',
                        help='ROI name (V1, V2, V3, hV4)')
    parser.add_argument('--n-components', type=int, default=6,
                        help='Number of PCA components (default: 6, current baseline)')

    # Model selection
    parser.add_argument('--models', type=str, nargs='+',
                        default=['linear', 'rf', 'mlp'],
                        choices=['linear', 'rf', 'mlp'],
                        help='Models to compare')

    # Visualization options
    parser.add_argument('--save-zmaps', action='store_true',
                        help='Save z-maps and create detailed visualizations')

    # RF hyperparameters
    parser.add_argument('--rf-n-estimators', type=int, default=100)
    parser.add_argument('--rf-max-depth', type=int, default=5)
    parser.add_argument('--rf-min-samples-leaf', type=int, default=3)

    # MLP hyperparameters
    parser.add_argument('--mlp-n-hidden', type=int, default=12)
    parser.add_argument('--mlp-learning-rate', type=float, default=0.001)
    parser.add_argument('--mlp-weight-decay', type=float, default=0.05)
    parser.add_argument('--mlp-dropout', type=float, default=0.3)
    parser.add_argument('--mlp-n-epochs', type=int, default=100)

    # Output
    parser.add_argument('--timestamp', type=str, default=None,
                        help='Timestamp for output directory (auto-generated if not provided)')

    return parser.parse_args()

args = parse_args()

# ============================================================================
# Setup (matching visualize_Edits structure)
# ============================================================================

# Dual logging class
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

# Generate timestamp
if args.timestamp:
    timestamp = args.timestamp
else:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# Output directory matching visualize_Edits structure
if args.subject == 'P01':
    output_dir = Path(f"derivatives/{timestamp}/pilot/sub-01/zScore_NONLINEAR/{args.roi}_universal_hrf")
    LABEL2HUE_DEG = LABEL2HUE_DEG_PILOT
    FILE_PREFIX = "sub-01"
    DERIVATIVE_PREFIX = "sub-01"
else:
    output_dir = Path(f"derivatives/{timestamp}/sub-{args.subject}/zScore_NONLINEAR/{args.roi}_universal_hrf")
    LABEL2HUE_DEG = LABEL2HUE_DEG_TEST
    FILE_PREFIX = f"sub-{args.subject}"
    DERIVATIVE_PREFIX = f"sub-{args.subject}"

output_dir.mkdir(parents=True, exist_ok=True)

fig_dir = output_dir / "figures"
fig_dir.mkdir(exist_ok=True)

# Setup dual logging
log_file = output_dir / "log.txt"
sys.stdout = DualLogger(log_file)
sys.stderr = sys.stdout

print("="*80)
print("Nonlinear Forward Model Testing (FULL VISUALIZATION VERSION)")
print("="*80)
print(f"Subject: {'P01' if args.subject == 'P01' else f'sub-{args.subject}'}")
print(f"ROI: {args.roi}")
print(f"PCA components: {args.n_components}")
print(f"Models: {', '.join(args.models)}")
print(f"Save z-maps: {args.save_zmaps}")
print(f"Output: {output_dir}")
print(f"Timestamp: {timestamp}")
print()
sys.stdout.flush()

# ============================================================================
# Path Configuration
# ============================================================================

FMRIPREP_BASE = "/storage/connectome/haba6030/fmriprep_out"
EVENT_DIR = "/storage/connectome/haba6030/colorBlind_dataOct"

if args.subject == 'P01':
    FMRIPREP_DIR = f"{FMRIPREP_BASE}/pilot/sub-01"
    EVENT_DIR = f"{EVENT_DIR}/pilot/sub-01/func"
    roi_path = f"derivatives/pilot/{DERIVATIVE_PREFIX}/roi_pipeline/{args.roi}_mask_thr50_intnearest_binTrue_masknone_gmTrue_subjFalse.nii.gz"
else:
    FMRIPREP_DIR = f"{FMRIPREP_BASE}/sub-{args.subject}"
    EVENT_DIR = f"{EVENT_DIR}/sub-{args.subject}/func"
    roi_path = f"derivatives/{DERIVATIVE_PREFIX}/roi_pipeline/{args.roi}_mask_thr50_intnearest_binTrue_masknone_gmTrue_subjFalse.nii.gz"

if not os.path.exists(roi_path):
    print(f"ERROR: ROI mask not found: {roi_path}")
    sys.exit(1)

# ============================================================================
# Load ROI Mask
# ============================================================================

print(f"[1/8] Loading ROI mask: {args.roi}")
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

for run in range(1, N_RUNS + 1):
    func_path = f"{FMRIPREP_DIR}/func/{FILE_PREFIX}_task-rsvp_run-{run}_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz"

    if not os.path.exists(func_path):
        print(f"ERROR: Functional image not found: {func_path}")
        sys.exit(1)

    func_img = nib.load(func_path)

    if VOLS_TO_DROP > 0:
        func_img = nimg.index_img(func_img, slice(VOLS_TO_DROP, None))

    func_imgs.append(func_img)

    events_path = f"{EVENT_DIR}/{FILE_PREFIX}_task-rsvp_run-{run}_events.tsv"

    if not os.path.exists(events_path):
        print(f"ERROR: Events file not found: {events_path}")
        sys.exit(1)

    events = pd.read_csv(events_path, sep='\t')
    events_list.append(events)

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
mean_responses = []

for color_idx in range(1, N_COLORS + 1):
    color_responses = []

    for delay in FIR_DELAYS:
        contrast_name = f'color_{color_idx}_delay_{delay}'
        try:
            contrast_map = fir_model.compute_contrast(contrast_name, output_type='effect_size')
            mean_response = masker.transform(contrast_map).mean()
            color_responses.append(mean_response)
        except:
            color_responses.append(0)

    mean_responses.append(color_responses)

mean_responses = np.array(mean_responses)

# Compute universal HRF
universal_hrf = mean_responses.mean(axis=0)
optimal_delay = np.argmax(np.abs(universal_hrf))
optimal_time = optimal_delay * TR

print()
print("  === Universal HRF Analysis ===")
print(f"  Optimal delay: {optimal_delay} TRs ({optimal_time:.1f}s)")
print(f"  Peak amplitude: {universal_hrf[optimal_delay]:.4f}")
print()
sys.stdout.flush()

# Plot HRF (FROM visualize_Edits lines 541-567)
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
ax.set_title(f'Universal HRF from FIR estimation - {args.roi}')
ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
ax.grid(True, alpha=0.3)

hrf_fig_path = fig_dir / f"{args.roi}_universal_hrf.png"
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
print(f"  Using Z-scores at optimal delay: {optimal_delay} TRs")
sys.stdout.flush()

all_zscores = []  # (n_runs, n_colors, n_voxels)
z_maps = []  # (n_colors,)

for run_idx in range(N_RUNS):
    run_zscores = []

    for color_idx in range(1, N_COLORS + 1):
        contrast_name = f'color_{color_idx}_delay_{optimal_delay}'

        try:
            contrast_map = fir_model.compute_contrast(contrast_name, output_type='z_score')
            zscores = masker.transform(contrast_map).ravel()
            run_zscores.append(zscores)

            # Z-map (only from first run)
            if run_idx == 0:
                z_map = fir_model.compute_contrast(contrast_name, output_type='z_score')
                z_maps.append(z_map)

        except Exception as e:
            print(f"  Warning: Could not extract {contrast_name}: {e}")
            run_zscores.append(np.zeros(n_voxels))
            if run_idx == 0:
                z_maps.append(None)

    all_zscores.append(np.array(run_zscores))
    print(f"  Run {run_idx+1}: Extracted {len(run_zscores)} color z-scores")

all_zscores = np.array(all_zscores)
print(f"  Total shape: {all_zscores.shape}")
print()
sys.stdout.flush()

# Save z-maps (FROM visualize_Edits lines 617-643)
if args.save_zmaps:
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
                threshold=2.3,
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

# (Continue in next part due to length...)
