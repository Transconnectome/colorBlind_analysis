#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_nonlinear_models.py
========================
Simplified script to test nonlinear forward models (RF, MLP) vs Linear baseline

Purpose:
- Quick comparison of Linear, RF, and MLP forward models
- Focus on core functionality (reconstruction error)
- Based on current baseline: PCA=6, zscore method
- Test on best ROI (V2) with Non-CVD subjects (sub-01, sub-02)

Usage:
    python test_nonlinear_models.py --subject 01 --roi V2 --models linear rf mlp
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

# nilearn imports
from nilearn.glm.first_level import FirstLevelModel
from nilearn import image as nimg
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
# Configuration
# ============================================================================

# Test data color mapping (regular 45° spacing)
LABEL2HUE_DEG = {
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
FIR_DELAYS = range(10)
VOLS_TO_DROP = 4

# ============================================================================
# Parse Arguments
# ============================================================================

def parse_args():
    parser = argparse.ArgumentParser(description='Test nonlinear forward models')

    # Data selection
    parser.add_argument('--subject', type=str, default='01',
                        help='Subject ID (01-04)')
    parser.add_argument('--roi', type=str, default='V2',
                        help='ROI name (V1, V2, V3, hV4)')
    parser.add_argument('--n-components', type=int, default=6,
                        help='Number of PCA components (default: 6, current baseline)')

    # Model selection
    parser.add_argument('--models', type=str, nargs='+',
                        default=['linear', 'rf', 'mlp'],
                        choices=['linear', 'rf', 'mlp'],
                        help='Models to compare')

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
    parser.add_argument('--output-dir', type=str, default='test_results_nonlinear',
                        help='Output directory')

    return parser.parse_args()

args = parse_args()

# ============================================================================
# Setup
# ============================================================================

print("="*70)
print("Nonlinear Forward Model Test")
print("="*70)
print(f"Subject: sub-{args.subject}")
print(f"ROI: {args.roi}")
print(f"PCA components: {args.n_components}")
print(f"Models: {', '.join(args.models)}")
print()

output_dir = Path(args.output_dir) / f"sub-{args.subject}_{args.roi}"
output_dir.mkdir(parents=True, exist_ok=True)

# ============================================================================
# Path Configuration
# ============================================================================

FMRIPREP_BASE = "/storage/connectome/haba6030/fmriprep_out"
EVENT_DIR = "/storage/connectome/haba6030/colorBlind_dataOct"

FMRIPREP_DIR = f"{FMRIPREP_BASE}/sub-{args.subject}"
FILE_PREFIX = f"sub-{args.subject}"
EVENT_DIR = f"{EVENT_DIR}/sub-{args.subject}/func"

# ROI path
roi_path = f"derivatives/sub-{args.subject}/roi_pipeline/{args.roi}_mask_thr50_intnearest_binTrue_masknone_gmTrue_subjFalse.nii.gz"

if not os.path.exists(roi_path):
    print(f"ERROR: ROI mask not found: {roi_path}")
    sys.exit(1)

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

for run_idx in range(N_RUNS):
    run_zscores = []
    for color_idx in range(1, N_COLORS + 1):
        contrast_name = f'color_{color_idx}_delay_{optimal_delay}'
        try:
            contrast_map = fir_model.compute_contrast(contrast_name, output_type='z_score')
            zscores = masker.transform(contrast_map).ravel()
            run_zscores.append(zscores)
        except Exception as e:
            print(f"  Warning: {contrast_name} failed: {e}")
            run_zscores.append(np.zeros(n_voxels))
    all_zscores.append(np.array(run_zscores))

all_zscores = np.array(all_zscores)  # (n_runs, n_colors, n_voxels)
print(f"  Extracted shape: {all_zscores.shape}")
print()

# ============================================================================
# Helper Functions
# ============================================================================

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

basis_functions = create_basis_functions(n_channels=6)

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

        # === Train forward model ===
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

    all_model_results[model_type] = {
        'mean_error': mean_error,
        'std_error': std_error,
        'per_run': reconstruction_results
    }

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
# Visualization
# ============================================================================

print("Creating visualizations...")

# Plot 1: Mean error comparison
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Bar plot
ax1 = axes[0]
model_names = list(all_model_results.keys())
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

# ============================================================================
# Save Results
# ============================================================================

print("Saving results...")

# Summary CSV
summary_data = []
for model_name in model_names:
    summary_data.append({
        'Subject': f'sub-{args.subject}',
        'ROI': args.roi,
        'Model': model_name,
        'N_voxels': n_voxels,
        'PCA_components': args.n_components,
        'Mean_error': all_model_results[model_name]['mean_error'],
        'Std_error': all_model_results[model_name]['std_error']
    })

summary_df = pd.DataFrame(summary_data)
summary_df.to_csv(output_dir / 'summary.csv', index=False)

print(f"  Saved: {output_dir}/summary.csv")

# Detailed results (pickle)
import pickle
with open(output_dir / 'results.pkl', 'wb') as f:
    pickle.dump(all_model_results, f)

print(f"  Saved: {output_dir}/results.pkl")
print()

# ============================================================================
# Final Summary
# ============================================================================

print("="*70)
print("Results Summary")
print("="*70)
print(f"Subject: sub-{args.subject}")
print(f"ROI: {args.roi} ({n_voxels} voxels)")
print(f"PCA: {args.n_components} components")
print()

for model_name in model_names:
    mean_err = all_model_results[model_name]['mean_error']
    std_err = all_model_results[model_name]['std_error']
    print(f"{model_name.upper():8s}: {mean_err:6.2f}° ± {std_err:5.2f}°")

print()
print(f"Output: {output_dir}")
print("="*70)
