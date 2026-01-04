#!/usr/bin/env python3
"""
reconstruction_with_SRM.py
==========================

SRM 기반 group-level reconstruction with HC common W matrix

**Pipeline:**
1. HC subjects: 각자의 amplitudes_z 로드 (baseline 결과)
2. SRM으로 HC shared space 학습
3. HC shared space에서 common W matrix 학습
4. CVD subjects:
   - Baseline amplitudes_z 로드
   - SRM으로 HC shared space로 project
   - HC의 common W 적용하여 reconstruction
5. Compare: CVD (with HC W) vs HC (with HC W) vs CVD (with own W)

Usage:
    # Train HC model
    python analysis/group_level/reconstruction_with_SRM.py \
        --mode train \
        --roi V1 \
        --hc-subjects 02 03 05 06 07 \
        --timestamp baseline81_deob_determin \
        --output-dir results/group_level/srm_reconstruction/

    # Test CVD subjects
    python analysis/group_level/reconstruction_with_SRM.py \
        --mode test \
        --roi V1 \
        --cvd-subjects 08 09 10 \
        --model-path results/group_level/srm_reconstruction/V1/srm_model.pkl \
        --output-dir results/group_level/srm_reconstruction/

Author: Claude Code
Date: 2025-12-19
"""

import sys
from pathlib import Path
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import argparse
import glob
import pickle
from sklearn.preprocessing import StandardScaler
from scipy.stats import zscore

# Try to import BrainIAK
try:
    from brainiak.funcalign.srm import SRM
    BRAINIAK_AVAILABLE = True
except ImportError:
    print("WARNING: BrainIAK not available. SRM will not work.")
    BRAINIAK_AVAILABLE = False

# ============================================================================
# Configuration
# ============================================================================

def parse_args():
    parser = argparse.ArgumentParser(description='SRM-based Group Reconstruction')
    parser.add_argument('--mode', type=str, required=True, choices=['train', 'test'],
                        help='Train HC model or test CVD subjects')
    parser.add_argument('--roi', type=str, required=True)
    parser.add_argument('--timestamp', type=str, default='baseline81_deob_determin')
    parser.add_argument('--dataset', type=str, default='deoblique_v2')

    # HC subjects for training
    parser.add_argument('--hc-subjects', type=str, nargs='+',
                        default=['02', '03', '05', '06', '07'])

    # CVD subjects for testing
    parser.add_argument('--cvd-subjects', type=str, nargs='+',
                        default=['08', '09', '10'])

    # SRM parameters
    parser.add_argument('--n-iter', type=int, default=10,
                        help='SRM iterations')
    parser.add_argument('--k-features', type=int, default=20,
                        help='SRM latent features')

    # I/O
    parser.add_argument('--model-path', type=str, default=None,
                        help='Path to saved SRM model (for test mode)')
    parser.add_argument('--output-dir', type=str, required=True)

    return parser.parse_args()

# ============================================================================
# Helper Functions (from BH2009 code)
# ============================================================================

def create_basis_functions(n_channels=6):
    """Create 6 idealized color channels"""
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
    """Convert hue (0-360) to 6 channel outputs"""
    hue_idx = int(np.round(hue_deg)) % 360
    return basis_functions[hue_idx]

def circular_diff_deg(a, b):
    """Circular difference in degrees"""
    diff = np.abs(a - b)
    diff = np.where(diff > 180, 360 - diff, diff)
    return diff

# Test hue mapping (uniform 0-315 deg)
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

# ============================================================================
# Data Loading
# ============================================================================

def load_subject_amplitudes(subject_id, roi, timestamp, dataset='deoblique_v2'):
    """
    Load amplitudes_z from baseline results

    Returns:
    --------
    amplitudes_z : ndarray, shape (n_runs, n_colors, n_voxels)
    """
    base_path = Path(f'derivatives/BH2009_{dataset}/{timestamp}')
    pattern = str(base_path / f'sm*_sub-{subject_id}_{roi}_*')
    matches = glob.glob(pattern)

    if len(matches) == 0:
        raise FileNotFoundError(f"No results found for sub-{subject_id} {roi}")

    result_dir = Path(matches[0])
    amp_file = result_dir / 'amplitudes_z.npy'

    if not amp_file.exists():
        raise FileNotFoundError(f"amplitudes_z.npy not found in {result_dir}")

    amplitudes_z = np.load(amp_file)
    print(f"  Loaded sub-{subject_id}: {amplitudes_z.shape}")

    return amplitudes_z

# ============================================================================
# Mode 1: Train HC Model
# ============================================================================

def train_hc_model(args):
    """
    Train SRM on HC subjects and learn common W matrix
    """
    print(f"\n{'='*70}")
    print(f"MODE 1: TRAIN HC MODEL")
    print(f"{'='*70}\n")

    roi = args.roi
    hc_subjects = args.hc_subjects
    n_subjects = len(hc_subjects)

    print(f"ROI: {roi}")
    print(f"HC subjects: {hc_subjects}")
    print(f"Dataset: {args.dataset}")
    print(f"Timestamp: {args.timestamp}\n")

    # ========================================================================
    # Step 1: Load HC amplitudes
    # ========================================================================
    print(f"[1/5] Loading HC baseline results...")

    hc_amplitudes = []
    for sub_id in hc_subjects:
        amp = load_subject_amplitudes(sub_id, roi, args.timestamp, args.dataset)
        hc_amplitudes.append(amp)

    # Check shapes
    shapes = [amp.shape for amp in hc_amplitudes]
    print(f"\n  Shapes: {shapes}")

    # Ensure consistent voxel counts
    voxel_counts = [amp.shape[2] for amp in hc_amplitudes]
    if len(set(voxel_counts)) > 1:
        print(f"\n  ⚠️  WARNING: Inconsistent voxel counts: {voxel_counts}")
        print(f"     Using minimum: {min(voxel_counts)}")

        # Truncate to minimum
        min_voxels = min(voxel_counts)
        hc_amplitudes = [amp[:, :, :min_voxels] for amp in hc_amplitudes]

    n_runs, n_colors, n_voxels = hc_amplitudes[0].shape
    print(f"\n  Final shape: ({n_runs}, {n_colors}, {n_voxels})")

    # ========================================================================
    # Step 2: Prepare data for SRM
    # ========================================================================
    print(f"\n[2/5] Preparing data for SRM...")

    # SRM expects: list of (n_timepoints, n_voxels) arrays
    # We have: (n_runs, n_colors, n_voxels)
    # → Reshape to (n_runs * n_colors, n_voxels)

    srm_data = []
    for amp in hc_amplitudes:
        # Flatten runs and colors
        amp_2d = amp.reshape(-1, n_voxels)  # (n_runs*n_colors, n_voxels)
        srm_data.append(amp_2d)

    print(f"  SRM input shapes: {[d.shape for d in srm_data]}")

    # ========================================================================
    # Step 3: Fit SRM
    # ========================================================================
    print(f"\n[3/5] Fitting SRM (k={args.k_features}, iter={args.n_iter})...")

    if not BRAINIAK_AVAILABLE:
        raise ImportError("BrainIAK is required for SRM. Install: pip install brainiak")

    srm = SRM(n_iter=args.n_iter, features=args.k_features)
    srm.fit(srm_data)

    print(f"  SRM fitted successfully!")
    print(f"  Shared space: ({n_runs * n_colors}, {args.k_features})")

    # Transform to shared space
    hc_shared = srm.transform(srm_data)  # List of (n_timepoints, k_features)

    # Average across subjects to get group representation
    hc_shared_mean = np.mean(hc_shared, axis=0)  # (n_runs*n_colors, k_features)

    # Reshape back to (n_runs, n_colors, k_features)
    hc_shared_mean = hc_shared_mean.reshape(n_runs, n_colors, args.k_features)

    print(f"  HC shared space (mean): {hc_shared_mean.shape}")

    # ========================================================================
    # Step 4: Learn common W matrix in shared space
    # ========================================================================
    print(f"\n[4/5] Learning common W matrix...")

    basis_functions = create_basis_functions(n_channels=6)

    # Prepare training data (all HC runs combined)
    X_train_all = []
    C_train_all = []

    for run_idx in range(n_runs):
        for color_idx in range(n_colors):
            # Voxel pattern in shared space
            voxel_pattern = hc_shared_mean[run_idx, color_idx, :]  # (k_features,)
            X_train_all.append(voxel_pattern)

            # Channel response
            color_name = f'color_{color_idx + 1}'
            hue_deg = LABEL2HUE_DEG[color_name]
            channels = hue_to_channels(hue_deg, basis_functions)
            C_train_all.append(channels)

    X_train_all = np.array(X_train_all)  # (n_runs*n_colors, k_features)
    C_train_all = np.array(C_train_all).T  # (6, n_runs*n_colors)

    print(f"  X_train: {X_train_all.shape}")
    print(f"  C_train: {C_train_all.shape}")

    # Estimate W: X = W × C → W = X × C^T × (C × C^T)^-1
    W_common = X_train_all.T @ C_train_all.T @ np.linalg.inv(C_train_all @ C_train_all.T)

    print(f"  W_common: {W_common.shape} (k_features × 6)")

    # ========================================================================
    # Step 5: Save model
    # ========================================================================
    print(f"\n[5/5] Saving model...")

    output_dir = Path(args.output_dir) / roi
    output_dir.mkdir(parents=True, exist_ok=True)

    model_data = {
        'srm': srm,
        'W_common': W_common,
        'basis_functions': basis_functions,
        'hc_subjects': hc_subjects,
        'roi': roi,
        'n_voxels': n_voxels,
        'k_features': args.k_features,
        'n_iter': args.n_iter,
    }

    model_path = output_dir / 'srm_model.pkl'
    with open(model_path, 'wb') as f:
        pickle.dump(model_data, f)

    print(f"  Saved: {model_path}")

    # Save W_common separately for easy access
    np.save(output_dir / 'W_common.npy', W_common)
    print(f"  Saved: {output_dir / 'W_common.npy'}")

    print(f"\n{'='*70}")
    print(f"HC MODEL TRAINING COMPLETE!")
    print(f"{'='*70}\n")

# ============================================================================
# Mode 2: Test CVD Subjects
# ============================================================================

def test_cvd_subjects(args):
    """
    Test CVD subjects using HC model
    """
    print(f"\n{'='*70}")
    print(f"MODE 2: TEST CVD SUBJECTS")
    print(f"{'='*70}\n")

    roi = args.roi
    cvd_subjects = args.cvd_subjects

    print(f"ROI: {roi}")
    print(f"CVD subjects: {cvd_subjects}")

    # ========================================================================
    # Step 1: Load HC model
    # ========================================================================
    print(f"\n[1/4] Loading HC model...")

    if args.model_path is None:
        model_path = Path(args.output_dir) / roi / 'srm_model.pkl'
    else:
        model_path = Path(args.model_path)

    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")

    with open(model_path, 'rb') as f:
        model_data = pickle.load(f)

    srm = model_data['srm']
    W_common = model_data['W_common']
    basis_functions = model_data['basis_functions']

    print(f"  Loaded: {model_path}")
    print(f"  W_common: {W_common.shape}")
    print(f"  SRM features: {model_data['k_features']}")

    # ========================================================================
    # Step 2: Load CVD amplitudes
    # ========================================================================
    print(f"\n[2/4] Loading CVD baseline results...")

    cvd_amplitudes = []
    for sub_id in cvd_subjects:
        amp = load_subject_amplitudes(sub_id, roi, args.timestamp, args.dataset)
        cvd_amplitudes.append(amp)

    n_runs, n_colors, n_voxels = cvd_amplitudes[0].shape

    # ========================================================================
    # Step 3: Project CVD to HC shared space
    # ========================================================================
    print(f"\n[3/4] Projecting CVD to HC shared space...")

    cvd_results = []

    for sub_idx, sub_id in enumerate(cvd_subjects):
        print(f"\n  sub-{sub_id}:")

        amp = cvd_amplitudes[sub_idx]

        # Prepare for SRM transform
        amp_2d = amp.reshape(-1, n_voxels)  # (n_runs*n_colors, n_voxels)

        # Transform to shared space
        amp_shared = srm.transform([amp_2d])[0]  # (n_runs*n_colors, k_features)

        # Reshape back
        amp_shared = amp_shared.reshape(n_runs, n_colors, -1)

        print(f"    Shared space: {amp_shared.shape}")

        # ========================================================================
        # Step 4: Reconstruction with HC W
        # ========================================================================

        reconstruction_errors = []

        for test_run in range(n_runs):
            # Test data in shared space
            X_test = amp_shared[test_run]  # (n_colors, k_features)

            # Estimate channels: C = (W^T W)^-1 W^T X^T
            C_est = np.linalg.pinv(W_common.T @ W_common) @ W_common.T @ X_test.T
            # C_est: (6, n_colors)

            # Reconstruct hues
            for color_idx in range(n_colors):
                estimated_channels = C_est[:, color_idx]

                # Find best matching hue
                correlations = []
                for h in range(360):
                    template = basis_functions[h]
                    corr = np.corrcoef(estimated_channels, template)[0, 1]
                    correlations.append(corr)

                reconstructed_hue = np.argmax(correlations)

                # True hue
                color_name = f'color_{color_idx + 1}'
                true_hue = LABEL2HUE_DEG[color_name]

                # Error
                error = circular_diff_deg(reconstructed_hue, true_hue)
                reconstruction_errors.append(error)

        mean_error = np.mean(reconstruction_errors)

        print(f"    Reconstruction error (with HC W): {mean_error:.1f}°")

        cvd_results.append({
            'subject_id': sub_id,
            'mean_error': mean_error,
            'all_errors': reconstruction_errors,
        })

    # ========================================================================
    # Step 5: Save results
    # ========================================================================
    print(f"\n[4/4] Saving results...")

    output_dir = Path(args.output_dir) / roi
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save as CSV
    df = pd.DataFrame([
        {'subject_id': r['subject_id'], 'mean_error': r['mean_error']}
        for r in cvd_results
    ])

    csv_path = output_dir / 'cvd_reconstruction_errors.csv'
    df.to_csv(csv_path, index=False)

    print(f"  Saved: {csv_path}")

    # Save detailed results
    results_path = output_dir / 'cvd_results_detailed.pkl'
    with open(results_path, 'wb') as f:
        pickle.dump(cvd_results, f)

    print(f"  Saved: {results_path}")

    print(f"\n{'='*70}")
    print(f"CVD TESTING COMPLETE!")
    print(f"{'='*70}\n")

    # Summary
    print(f"\nSummary:")
    for r in cvd_results:
        print(f"  sub-{r['subject_id']}: {r['mean_error']:.1f}°")

# ============================================================================
# Main
# ============================================================================

if __name__ == '__main__':
    args = parse_args()

    if args.mode == 'train':
        train_hc_model(args)
    elif args.mode == 'test':
        test_cvd_subjects(args)
