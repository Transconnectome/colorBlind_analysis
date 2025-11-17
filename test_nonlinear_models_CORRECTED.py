#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_nonlinear_models_CORRECTED.py
===================================
Corrected version - matching visualize_Edits baseline structure

Purpose:
- Test nonlinear forward models (RF, MLP) vs Linear baseline
- Based on visualize_Edits/fir_reconstruction_zScore.py
- Uses correct output structure: derivatives/{timestamp}/sub-{ID}/...
- Default PCA=6 (as per CLAUDE.md and current baseline)

Baseline reference:
- visualize_Edits/fir_reconstruction_zScore.py
- ANALYSIS_SUMMARY_20251117.md (PCA=6, zscore method)

Usage:
    python test_nonlinear_models_CORRECTED.py \
        --subject 01 \
        --roi V2 \
        --n-components 6 \
        --models linear rf mlp
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
# Parse Arguments
# ============================================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description='Test nonlinear forward models (CORRECTED for visualize_Edits baseline)')

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

    # Output (matching visualize_Edits structure)
    parser.add_argument('--timestamp', type=str, default=None,
                        help='Timestamp for output directory (auto-generated if not provided)')

    return parser.parse_args()

args = parse_args()

# ============================================================================
# Setup (matching visualize_Edits structure)
# ============================================================================

print("="*70)
print("Nonlinear Forward Model Test (CORRECTED)")
print("="*70)
print(f"Subject: {'P01' if args.subject == 'P01' else f'sub-{args.subject}'}")
print(f"ROI: {args.roi}")
print(f"PCA components: {args.n_components}")
print(f"Models: {', '.join(args.models)}")
print(f"Save z-maps: {args.save_zmaps}")
print()

# Generate timestamp
if args.timestamp:
    timestamp = args.timestamp
else:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# Output directory matching visualize_Edits structure
# derivatives/{timestamp}/sub-{ID}/zScore_NONLINEAR/{ROI}_universal_hrf/
if args.subject == 'P01':
    output_dir = Path(f"derivatives/{timestamp}/pilot/sub-01/zScore_NONLINEAR/{args.roi}_universal_hrf")
    LABEL2HUE_DEG = LABEL2HUE_DEG_PILOT
else:
    output_dir = Path(f"derivatives/{timestamp}/sub-{args.subject}/zScore_NONLINEAR/{args.roi}_universal_hrf")
    LABEL2HUE_DEG = LABEL2HUE_DEG_TEST

output_dir.mkdir(parents=True, exist_ok=True)

fig_dir = output_dir / "figures"
fig_dir.mkdir(exist_ok=True)

print(f"Output: {output_dir}")
print(f"Timestamp: {timestamp}")
print()

# ============================================================================
# Path Configuration (matching visualize_Edits)
# ============================================================================

FMRIPREP_BASE = "/storage/connectome/haba6030/fmriprep_out"
EVENT_DIR = "/storage/connectome/haba6030/colorBlind_dataOct"

if args.subject == 'P01':
    FMRIPREP_DIR = f"{FMRIPREP_BASE}/pilot/sub-01"
    FILE_PREFIX = "sub-01"
    EVENT_DIR = f"{EVENT_DIR}/pilot/sub-01/func"
else:
    FMRIPREP_DIR = f"{FMRIPREP_BASE}/sub-{args.subject}"
    FILE_PREFIX = f"sub-{args.subject}"
    EVENT_DIR = f"{EVENT_DIR}/sub-{args.subject}/func"

# ROI path (matching CLAUDE.md structure)
if args.subject == 'P01':
    roi_path = f"derivatives/pilot/sub-01/roi_pipeline/{args.roi}_mask_thr50_intnearest_binTrue_masknone_gmTrue_subjFalse.nii.gz"
else:
    roi_path = f"derivatives/sub-{args.subject}/roi_pipeline/{args.roi}_mask_thr50_intnearest_binTrue_masknone_gmTrue_subjFalse.nii.gz"

if not os.path.exists(roi_path):
    print(f"ERROR: ROI mask not found: {roi_path}")
    sys.exit(1)

# ============================================================================
# Load ROI Mask
# ============================================================================

print(f"[1/6] Loading ROI mask: {args.roi}")
roi_img = nib.load(roi_path)
masker = NiftiMasker(mask_img=roi_path, standardize=False)
masker.fit()
n_voxels = np.sum(roi_img.get_fdata() > 0)
print(f"  Voxels: {n_voxels}")
print()

# ============================================================================
# Load Data
# ============================================================================

print(f"[2/6] Loading functional data")

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
    events = pd.read_csv(events_path, sep='\t')
    events_list.append(events)

    confounds_path = f"{FMRIPREP_DIR}/func/{FILE_PREFIX}_task-rsvp_run-{run}_desc-confounds_timeseries.tsv"
    confounds = pd.read_csv(confounds_path, sep='\t')
    motion_cols = ['trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z']
    confounds_subset = confounds[motion_cols]

    if VOLS_TO_DROP > 0:
        confounds_subset = confounds_subset.iloc[VOLS_TO_DROP:]

    confounds_list.append(confounds_subset)

print(f"  Loaded {len(func_imgs)} runs")
print()

# ============================================================================
# Fit FIR Model
# ============================================================================

print(f"[3/6] Fitting FIR model")

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
print("  FIR model fitted")
print()

# ============================================================================
# Find Optimal Delay
# ============================================================================

print(f"[4/6] Finding optimal delay from universal HRF")

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
universal_hrf = mean_responses.mean(axis=0)
optimal_delay = np.argmax(np.abs(universal_hrf))

print(f"  Optimal delay: {optimal_delay} TRs ({optimal_delay * TR:.1f}s)")
print()

# ============================================================================
# Extract Z-Scores
# ============================================================================

print(f"[5/6] Extracting Z-scores at optimal delay")

all_zscores = []  # (n_runs, n_colors, n_voxels)
z_maps = []  # (n_colors,) - store z-maps from first run

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
            print(f"  Warning: {contrast_name} failed: {e}")
            run_zscores.append(np.zeros(n_voxels))
            if run_idx == 0:
                z_maps.append(None)

    all_zscores.append(np.array(run_zscores))
    print(f"  Run {run_idx+1}: Extracted {len(run_zscores)} color z-scores")

all_zscores = np.array(all_zscores)  # (n_runs, n_colors, n_voxels)
print(f"  Total shape: {all_zscores.shape}")
print()

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

def circular_diff_deg(a, b):
    """Circular difference in degrees"""
    diff = np.abs(a - b)
    return np.minimum(diff, 360 - diff)

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
# Z-Map Visualization (if save_zmaps enabled)
# ============================================================================

if args.save_zmaps:
    print("="*70)
    print("Creating detailed z-map visualizations...")
    print("="*70)

    # Save z-maps
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

    # Z-Map Matrix Visualization (FROM visualize_Edits lines 649-822)
    print("Creating z-map matrix visualization...")

    # Extract z-scores for each voxel × color
    zscores_matrix = np.zeros((n_voxels, N_COLORS))

    for color_idx in range(N_COLORS):
        if z_maps[color_idx] is not None:
            z_data = masker.transform(z_maps[color_idx]).ravel()
            zscores_matrix[:, color_idx] = z_data

    # 1. Full Z-Score Matrix Heatmap (4-panel visualization)
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle(f'{args.roi}: Z-Score Matrix Visualization', fontsize=16, fontweight='bold')

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
    zmatrix_plot_path = fig_dir / f"{args.roi}_zscores_matrix.png"
    plt.savefig(zmatrix_plot_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {zmatrix_plot_path}")

    # 2. Detailed per-color z-score heatmaps (top 100 voxels)
    fig, axes = plt.subplots(2, 4, figsize=(16, 8))
    fig.suptitle(f'{args.roi}: Top Voxels per Color (Highest |z|)', fontsize=14, fontweight='bold')

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
    top_voxels_plot_path = fig_dir / f"{args.roi}_top_voxels_per_color.png"
    plt.savefig(top_voxels_plot_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {top_voxels_plot_path}")

    # 3. Voxel-wise color preference wheel (FROM visualize_Edits lines 764-810)
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
    ax.set_theta_zero_location("E")        # 0° at right (middle-right)
    ax.set_theta_direction(1)              # Anticlockwise positive (counterclockwise)

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
    ax.set_title(f'{args.roi}: Voxel Color Preferences\n(Red=excitatory, Blue=inhibitory)',
                 fontsize=14, fontweight='bold', pad=20)

    plt.tight_layout()
    wheel_plot_path = fig_dir / f"{args.roi}_color_preference_wheel.png"
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

basis_functions = create_basis_functions(n_channels=6)

# ============================================================================
# PCA Explained Variance Visualization (if save_zmaps)
# ============================================================================

if args.save_zmaps:
    print("="*70)
    print("Creating PCA explained variance visualization...")
    print("="*70)

    # Fit PCA on first fold to get explained variance
    X_sample = all_zscores[[0,1,2,3,4]].reshape(-1, n_voxels)  # First 5 runs
    scaler_sample = StandardScaler()
    X_sample_scaled = scaler_sample.fit_transform(X_sample)

    # Fit PCA with more components to see full variance curve
    pca_full = PCA(n_components=min(50, n_voxels, X_sample.shape[0]))
    pca_full.fit(X_sample_scaled)

    explained_var = pca_full.explained_variance_ratio_
    cumsum_var = np.cumsum(explained_var)

    # Create visualization
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Left: Individual explained variance
    ax1 = axes[0]
    n_show = min(20, len(explained_var))
    ax1.bar(range(n_show), explained_var[:n_show], alpha=0.7,
            edgecolor='black', color='steelblue')
    ax1.axvline(x=args.n_components-0.5, color='red', linestyle='--',
                linewidth=2, label=f'Using {args.n_components} components')
    ax1.set_xlabel('PCA Component')
    ax1.set_ylabel('Explained Variance Ratio')
    ax1.set_title(f'Individual Component Variance (First {n_show} components)')
    ax1.legend()
    ax1.grid(True, alpha=0.3, axis='y')

    # Right: Cumulative explained variance
    ax2 = axes[1]
    ax2.plot(range(len(cumsum_var)), cumsum_var, 'bo-', linewidth=2, markersize=4)
    ax2.axhline(y=0.9, color='green', linestyle='--', alpha=0.5, label='90%')
    ax2.axhline(y=0.95, color='orange', linestyle='--', alpha=0.5, label='95%')
    ax2.axvline(x=args.n_components-1, color='red', linestyle='--',
                linewidth=2, label=f'Using {args.n_components} (={cumsum_var[args.n_components-1]:.1%})')
    ax2.set_xlabel('Number of Components')
    ax2.set_ylabel('Cumulative Explained Variance')
    ax2.set_title(f'Cumulative Variance: {args.n_components} components = {cumsum_var[args.n_components-1]:.1%}')
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim([-0.5, min(30, len(cumsum_var))-0.5])

    plt.tight_layout()
    pca_var_path = fig_dir / f"{args.roi}_pca_explained_variance.png"
    plt.savefig(pca_var_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {pca_var_path}")
    print(f"  Using {args.n_components} components: {cumsum_var[args.n_components-1]:.1%} variance")
    print()
    sys.stdout.flush()

# ============================================================================
# Model Comparison
# ============================================================================

print(f"[6/6] Testing forward models")
print()

all_model_results = {}

for model_type in args.models:
    print(f"{'='*70}")
    print(f"Model: {model_type.upper()}")
    print(f"{'='*70}")

    reconstruction_results = []

    for test_run in range(N_RUNS):
        train_runs = [r for r in range(N_RUNS) if r != test_run]

        # Prepare data
        X_train = all_zscores[train_runs].reshape(-1, n_voxels)
        y_train = np.tile(np.arange(N_COLORS), len(train_runs))
        X_test = all_zscores[test_run]
        y_test = np.arange(N_COLORS)

        # Standardize
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        # PCA
        pca = PCA(n_components=args.n_components)
        X_train_final = pca.fit_transform(X_train_scaled)
        X_test_final = pca.transform(X_test_scaled)

        # Get channel outputs for training colors
        C_train = []
        for color_idx in y_train:
            color_name = f'color_{color_idx+1}'
            hue_deg = LABEL2HUE_DEG[color_name]
            channels = hue_to_channels(hue_deg, basis_functions)
            C_train.append(channels)
        C_train = np.array(C_train).T  # (6, n_train)

        # === Train forward model (KEY CHANGE) ===
        forward_model = create_forward_model(model_type, args)
        forward_model.fit(X_train_final, C_train)
        C_test_est = forward_model.predict(X_test_final)

        # Reconstruct hues
        reconstructed_hues = []
        true_hues = []

        for test_idx, color_idx in enumerate(y_test):
            estimated_channels = C_test_est[:, test_idx]

            # Template matching
            correlations = []
            for h in range(360):
                template_channels = basis_functions[h]
                corr = np.corrcoef(estimated_channels, template_channels)[0, 1]
                correlations.append(corr)

            reconstructed_hue = np.argmax(correlations)

            color_name = f'color_{color_idx+1}'
            true_hue = LABEL2HUE_DEG[color_name]

            reconstructed_hues.append(reconstructed_hue)
            true_hues.append(true_hue)

        # Calculate errors
        errors = circular_diff_deg(np.array(reconstructed_hues), np.array(true_hues))
        mean_error = errors.mean()

        reconstruction_results.append({
            'test_run': test_run + 1,
            'mean_error': mean_error,
            'errors': errors,
            'reconstructed_hues': reconstructed_hues,
            'true_hues': true_hues
        })

        print(f"  Run {test_run+1}: {mean_error:.2f}°")

    mean_error = np.mean([r['mean_error'] for r in reconstruction_results])
    std_error = np.std([r['mean_error'] for r in reconstruction_results])

    print(f"  Mean ± Std: {mean_error:.2f}° ± {std_error:.2f}°")
    print()

    # Leave-one-color-out reconstruction (novel colors)
    print(f"  Computing novel color reconstruction (leave-one-color-out)...")
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
                        X_train_list.append(all_zscores[r, c])
                        y_train_list.append(c)

            X_train = np.array(X_train_list)
            y_train = np.array(y_train_list)

            X_test = all_zscores[test_run, held_out_color:held_out_color+1]
            y_test = np.array([held_out_color])

            # Standardize
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)

            # PCA
            pca = PCA(n_components=min(args.n_components, len(X_train)))
            X_train_final = pca.fit_transform(X_train_scaled)
            X_test_final = pca.transform(X_test_scaled)

            # Train forward model
            C_train = []
            for color_idx in y_train:
                color_name = f'color_{color_idx+1}'
                hue_deg = LABEL2HUE_DEG[color_name]
                channels = hue_to_channels(hue_deg, basis_functions)
                C_train.append(channels)
            C_train = np.array(C_train).T

            # Train model
            forward_model_novel = create_forward_model(model_type, args)
            forward_model_novel.fit(X_train_final, C_train)

            # Reconstruct held-out color
            C_test_est = forward_model_novel.predict(X_test_final)
            estimated_channels = C_test_est[:, 0]

            # Template matching
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
            'color_idx': held_out_color,
            'reconstructed_hue': mean_reconstructed_hue,
            'reconstructed_hues': all_reconstructed_hues,
            'mean_error': mean_error_this_color,
            'errors': all_errors_this_color
        })

        print(f"    {color_name}: {mean_error_this_color:.1f}°")

    mean_novel_error = np.mean([r['mean_error'] for r in novel_color_results])
    print(f"  Novel color mean error: {mean_novel_error:.1f}°")
    print()

    all_model_results[model_type] = {
        'mean_error': mean_error,
        'std_error': std_error,
        'per_run': reconstruction_results,
        'novel_color_error': mean_novel_error,
        'novel_colors': novel_color_results
    }

    # Create model-specific visualizations (if save_zmaps)
    if args.save_zmaps:
        print()
        print(f"  Creating visualizations for {model_type.upper()} model...")

        # 1. Per-run reconstruction scatter plots (6 subplots)
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        fig.suptitle(f'{args.roi}: {model_type.upper()} Reconstruction Results (Leave-One-Run-Out)',
                     fontsize=16, fontweight='bold')

        for idx, result in enumerate(reconstruction_results):
            ax = axes[idx // 3, idx % 3]

            true_hues = result['true_hues']
            reconstructed_hues = result['reconstructed_hues']
            errors = result['errors']

            # Scatter plot with actual stimulus colors
            for i, (true_h, recon_h) in enumerate(zip(true_hues, reconstructed_hues)):
                color_name = f'color_{i+1}'
                color_rgb = get_stimulus_color_rgb(color_name)
                ax.scatter([true_h], [recon_h], s=150, alpha=0.8,
                          color=color_rgb, edgecolors='black', linewidths=1.5)
                ax.text(true_h, recon_h+8, f'c{i+1}', fontsize=8, ha='center', va='bottom', fontweight='bold')

            # Perfect reconstruction line
            ax.plot([0, 360], [0, 360], 'k--', alpha=0.3, linewidth=2, label='Perfect')

            ax.set_xlabel('True Hue (°)')
            ax.set_ylabel('Reconstructed Hue (°)')
            ax.set_title(f'Run {result["test_run"]}: {result["mean_error"]:.1f}° error')
            ax.set_xlim([0, 360])
            ax.set_ylim([0, 360])
            ax.grid(True, alpha=0.3)
            ax.legend()

        plt.tight_layout()
        recon_scatter_path = fig_dir / f"{args.roi}_{model_type}_reconstruction_per_run.png"
        plt.savefig(recon_scatter_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"    Saved: {recon_scatter_path}")

        # 2. Circular color space visualization (FROM visualize_Edits lines 1692-1781)
        fig = plt.figure(figsize=(14, 6))

        # Left: Training colors reconstruction
        ax1 = fig.add_subplot(1, 2, 1, projection='polar')
        ax1.set_theta_zero_location("E")        # 0° at right
        ax1.set_theta_direction(1)              # Anticlockwise
        ax1.set_rticks([])
        ax1.grid(alpha=0.25)

        rng = np.random.default_rng(42)
        r_center = 1.0
        r_pred_base = 0.85

        # Plot true colors at border and predictions inside
        for color_idx in range(N_COLORS):
            color_name = f'color_{color_idx + 1}'
            true_hue = LABEL2HUE_DEG[color_name]
            true_rgb = get_stimulus_color_rgb(color_name)

            # True color at border (large, solid)
            ax1.scatter([np.deg2rad(true_hue)], [r_center], s=110,
                       color=true_rgb, edgecolor='k', linewidths=0.8, zorder=4)

            # All predictions for this color
            for result in reconstruction_results:
                pred_hue = result['reconstructed_hues'][color_idx]

                # Jitter radius slightly to avoid overlap
                r_jit = r_pred_base + rng.uniform(-0.03, 0.03)
                ax1.scatter([np.deg2rad(pred_hue)], [r_jit], s=28,
                           color=true_rgb, alpha=0.65, zorder=3)

        ax1.set_ylim([0, 1.1])
        ax1.set_title(f'{model_type.upper()}: Training Colors\nMean error: {mean_error:.1f}°',
                     fontsize=12, fontweight='bold')

        # Right: Novel colors (leave-one-color-out)
        ax2 = fig.add_subplot(1, 2, 2, projection='polar')
        ax2.set_theta_zero_location("E")
        ax2.set_theta_direction(1)
        ax2.set_rticks([])
        ax2.grid(alpha=0.25)

        # Plot true colors at border and predictions inside
        for novel_result in novel_color_results:
            color_idx = novel_result['color_idx']
            color_name = novel_result['color']
            true_hue = LABEL2HUE_DEG[color_name]
            true_rgb = get_stimulus_color_rgb(color_name)

            # True color at border (large, solid)
            ax2.scatter([np.deg2rad(true_hue)], [r_center], s=110,
                       color=true_rgb, edgecolor='k', linewidths=0.8, zorder=4)

            # All predictions for this novel color (from 6 runs)
            for pred_hue in novel_result['reconstructed_hues']:
                # Jitter radius slightly to avoid overlap
                r_jit = r_pred_base + rng.uniform(-0.03, 0.03)
                ax2.scatter([np.deg2rad(pred_hue)], [r_jit], s=28,
                           color=true_rgb, alpha=0.65, zorder=3)

        ax2.set_ylim([0, 1.1])
        ax2.set_title(f'{model_type.upper()}: Novel Colors (Leave-One-Color-Out)\nMean error: {mean_novel_error:.1f}°',
                     fontsize=12, fontweight='bold')

        # Add legend
        from matplotlib.lines import Line2D
        legend_elems = [
            Line2D([0],[0], marker='o', color='w', markerfacecolor='gray', markeredgecolor='k',
                   label='True hue', markersize=10),
            Line2D([0],[0], marker='o', color='w', markerfacecolor='gray', alpha=0.65,
                   label='Predictions', markersize=6),
        ]
        ax1.legend(handles=legend_elems, loc='upper right', bbox_to_anchor=(1.25, 1.15), fontsize=9)

        plt.suptitle(f'{args.roi}: {model_type.upper()} Circular Color Space',
                     fontsize=14, fontweight='bold')
        plt.tight_layout()
        circular_plot_path = fig_dir / f"{args.roi}_{model_type}_circular_color_space.png"
        plt.savefig(circular_plot_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"    Saved: {circular_plot_path}")

        print()

# ============================================================================
# Statistical Comparison
# ============================================================================

print("="*70)
print("Statistical Comparison (Paired t-test)")
print("="*70)

model_names = list(all_model_results.keys())

for i in range(len(model_names)):
    for j in range(i+1, len(model_names)):
        model1 = model_names[i]
        model2 = model_names[j]

        errors1 = [r['mean_error'] for r in all_model_results[model1]['per_run']]
        errors2 = [r['mean_error'] for r in all_model_results[model2]['per_run']]

        t_stat, p_value = stats.ttest_rel(errors1, errors2)

        mean1 = np.mean(errors1)
        mean2 = np.mean(errors2)
        diff = mean1 - mean2

        print(f"\n{model1.upper()} vs {model2.upper()}:")
        print(f"  {mean1:.2f}° vs {mean2:.2f}° (diff: {diff:+.2f}°)")
        print(f"  t={t_stat:.3f}, p={p_value:.4f}", end="")

        if p_value < 0.05:
            winner = model1 if mean1 < mean2 else model2
            print(f" → {winner.upper()} significantly better")
        else:
            print(f" → No significant difference")

print()

# ============================================================================
# Save Results (matching visualize_Edits structure)
# ============================================================================

print("Saving results...")

# Summary CSV
summary_data = []
for model_name in model_names:
    summary_data.append({
        'Subject': f"sub-{args.subject}" if args.subject != 'P01' else 'P01',
        'ROI': args.roi,
        'Model': model_name,
        'N_voxels': n_voxels,
        'PCA_components': args.n_components,
        'Optimal_delay_TRs': optimal_delay,
        'Mean_error': all_model_results[model_name]['mean_error'],
        'Std_error': all_model_results[model_name]['std_error'],
        'Novel_color_error': all_model_results[model_name]['novel_color_error']
    })

summary_df = pd.DataFrame(summary_data)
summary_df.to_csv(output_dir / 'summary.csv', index=False)

print(f"  Saved: {output_dir}/summary.csv")

# Detailed results (pickle)
import pickle
with open(output_dir / 'results.pkl', 'wb') as f:
    pickle.dump(all_model_results, f)

print(f"  Saved: {output_dir}/results.pkl")

# ============================================================================
# Visualization
# ============================================================================

print("Creating visualization...")

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Bar plot
ax1 = axes[0]
mean_errors = [all_model_results[m]['mean_error'] for m in model_names]
std_errors = [all_model_results[m]['std_error'] for m in model_names]

bars = ax1.bar(model_names, mean_errors, yerr=std_errors,
               alpha=0.7, edgecolor='black', capsize=5)
ax1.axhline(y=90, color='red', linestyle='--', alpha=0.5, label='Chance (90°)')
ax1.set_ylabel('Mean Reconstruction Error (°)')
ax1.set_title(f'{args.roi}: Model Comparison')
ax1.legend()
ax1.grid(True, alpha=0.3, axis='y')

for bar, err in zip(bars, mean_errors):
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height + 2,
            f'{err:.1f}°', ha='center', va='bottom', fontweight='bold')

# Boxplot
ax2 = axes[1]
data_for_boxplot = []
for model_name in model_names:
    errors_per_run = [r['mean_error'] for r in all_model_results[model_name]['per_run']]
    data_for_boxplot.append(errors_per_run)

bp = ax2.boxplot(data_for_boxplot, labels=model_names, patch_artist=True)
for patch in bp['boxes']:
    patch.set_facecolor('lightblue')
ax2.axhline(y=90, color='red', linestyle='--', alpha=0.5, label='Chance')
ax2.set_ylabel('Reconstruction Error (°)')
ax2.set_title('Per-Run Variability')
ax2.legend()
ax2.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig(output_dir / 'model_comparison.png', dpi=150, bbox_inches='tight')
plt.close()

print(f"  Saved: {output_dir}/model_comparison.png")
print()

# ============================================================================
# Final Summary
# ============================================================================

print("="*70)
print("Results Summary")
print("="*70)
print(f"Subject: {'P01' if args.subject == 'P01' else f'sub-{args.subject}'}")
print(f"ROI: {args.roi} ({n_voxels} voxels)")
print(f"PCA: {args.n_components} components")
print(f"Optimal delay: {optimal_delay} TRs")
print()

print("Training Colors (Leave-One-Run-Out):")
for model_name in model_names:
    mean_err = all_model_results[model_name]['mean_error']
    std_err = all_model_results[model_name]['std_error']
    print(f"  {model_name.upper():8s}: {mean_err:6.2f}° ± {std_err:5.2f}°")

print()
print("Novel Colors (Leave-One-Color-Out):")
for model_name in model_names:
    novel_err = all_model_results[model_name]['novel_color_error']
    print(f"  {model_name.upper():8s}: {novel_err:6.2f}°")

print()
print(f"Output: {output_dir}")
print(f"Timestamp: {timestamp}")
print("="*70)
