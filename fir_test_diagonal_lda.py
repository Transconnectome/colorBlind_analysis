#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fir_test_diagonal_lda.py
-------------------------
FIR test with DIAGONAL LDA (+ optional PCA) (Option B+C)

Addresses overfitting by:
1. Using diagonal Linear Discriminant Analysis (paper method)
   - Assumes independent voxels (diagonal covariance)
   - More parameter-efficient than multinomial logistic regression
2. Optional PCA dimensionality reduction (set USE_PCA=True)

This matches Brouwer & Heeger (2009) methodology more closely.
"""

import sys
import os
import numpy as np
import pandas as pd
import nibabel as nib
from nilearn.glm.first_level import FirstLevelModel
from nilearn import image as nimg

# Try different nilearn import versions
try:
    from nilearn.maskers import NiftiMasker
except ImportError:
    from nilearn.input_data import NiftiMasker

from config import cfg

# ============================================================================
# Configuration
# ============================================================================

USE_PCA = True  # Set to True to use PCA dimensionality reduction
N_PCA_COMPONENTS = 20  # Only used if USE_PCA=True

print("="*70)
print("FIR Test with Diagonal LDA (Option B+C)")
print("="*70)
print(f"Subject: sub-{cfg.SUB_ID}")
print()
print("Overfitting mitigation:")
print("  1. Diagonal Linear Discriminant (paper method)")
print("     - Assumes independent voxels (diagonal covariance)")
print("     - More parameter-efficient than logistic regression")
if USE_PCA:
    print(f"  2. PCA dimensionality reduction: {N_PCA_COMPONENTS} components")
print()
sys.stdout.flush()

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
        # Get contrast for this color at typical HRF peak
        contrast_name = f'color_{color_idx}_delay_3'  # ~4.5s post-onset

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
# Diagonal Linear Discriminant Classifier (Paper Method)
# ============================================================================

def diag_linear_predict(train_X, train_y, test_X):
    """
    Diagonal Linear Discriminant Analysis

    Assumes diagonal covariance (independent features/voxels).
    This is more parameter-efficient than full LDA or logistic regression.

    Parameters per class: D means + D variances = 2D
    Total for C classes: 2*C*D
    But the diagonal assumption constrains the model significantly.

    From Brouwer & Heeger (2009):
    "We used a maximum likelihood classifier that assumed
    each voxel's responses were independent (diagonal covariance)."
    """
    # train_X: (N, D), train_y: (N,), test_X: (M, D)
    classes = np.unique(train_y)
    means = np.stack([train_X[train_y==c].mean(axis=0) for c in classes])  # (C, D)
    vars_  = np.stack([train_X[train_y==c].var(axis=0) + 1e-8 for c in classes])   # (C, D)

    # Log-likelihood under diagonal Gaussians
    # ll_c(x) = -0.5 * [ sum log(2πσ²) + sum (x-μ)²/σ² ]
    ll = []
    for k in range(len(classes)):
        ll_k = -0.5 * (
            np.log(2*np.pi*vars_[k]).sum() +
            ((test_X - means[k])**2 / vars_[k]).sum(axis=1)
        )
        ll.append(ll_k)
    ll = np.stack(ll, axis=1)  # (M, C)
    preds = classes[ll.argmax(axis=1)]
    return preds

print(f"[5/5] Classification with diagonal LDA")
if USE_PCA:
    print(f"  PCA: Reducing to {N_PCA_COMPONENTS} components")
print(f"  Classifier: Diagonal Linear Discriminant (paper method)")
sys.stdout.flush()

from sklearn.preprocessing import StandardScaler
if USE_PCA:
    from sklearn.decomposition import PCA

accuracies = []

for test_run in range(N_RUNS):
    # Split train/test
    train_runs = [r for r in range(N_RUNS) if r != test_run]

    X_train = all_betas[train_runs].reshape(-1, all_betas.shape[2])  # (n_train_samples, n_voxels)
    y_train = np.tile(np.arange(N_COLORS), len(train_runs))

    X_test = all_betas[test_run]  # (n_colors, n_voxels)
    y_test = np.arange(N_COLORS)

    # Standardize (important for both PCA and diagonal LDA)
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

    # Diagonal LDA classification
    y_pred = diag_linear_predict(X_train_final, y_train, X_test_final)
    acc = (y_pred == y_test).mean()
    accuracies.append(acc)

    print(f"  Test run {test_run+1}: {acc:.3f} ({acc*100:.1f}%)")

mean_acc = np.mean(accuracies)
print()
print(f"Mean accuracy: {mean_acc:.3f} ({mean_acc*100:.1f}%)")
print(f"Baseline (chance): {1/N_COLORS:.3f} ({100/N_COLORS:.1f}%)")
print()

# Parameter analysis
n_features = N_PCA_COMPONENTS if USE_PCA else all_betas.shape[2]
params_per_class = 2 * n_features  # mean + variance per feature
total_params = N_COLORS * params_per_class
train_samples = len(train_runs) * N_COLORS

print(f"Model parameters:")
print(f"  Features: {n_features}")
print(f"  Parameters per class: {params_per_class} (mean + variance)")
print(f"  Total parameters: {total_params}")
print(f"  Training samples: {train_samples}")
print(f"  Samples per parameter: {train_samples/total_params:.3f}")
print()
sys.stdout.flush()

# ============================================================================
# Summary
# ============================================================================

print("="*70)
print("FIR Test with Diagonal LDA Complete")
print("="*70)
print()

if mean_acc > 1.5 / N_COLORS:  # Better than 1.5x chance
    print("✅ SUCCESS: FIR with diagonal LDA shows above-chance classification!")
    print(f"   Accuracy: {mean_acc*100:.1f}% vs chance {100/N_COLORS:.1f}%")
    print()
    print("This suggests:")
    print("  1. FIR captures real signal better than canonical HRF")
    print("  2. Diagonal LDA provides good parameter efficiency")
    print("  3. Can proceed with full reconstruction pipeline")
    print()
    if not USE_PCA:
        print("Next steps:")
        print("  - Try with PCA (set USE_PCA=True) to see if it improves")
        print("  - Proceed to build complete B&H reconstruction pipeline")
else:
    print("❌ POOR: Classification still at chance level")
    print(f"   Accuracy: {mean_acc*100:.1f}% vs chance {100/N_COLORS:.1f}%")
    print()
    print("This suggests:")
    print("  1. FIR may not help (problem is deeper)")
    print("  2. Need to investigate event timing or data quality")
    if not USE_PCA:
        print("  3. Try with PCA dimensionality reduction")

print("="*70)
sys.stdout.flush()
