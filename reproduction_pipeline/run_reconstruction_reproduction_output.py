#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_reconstruction_reproduction.py
----------------------------------
Complete color reconstruction pipeline for reproducing documented results.

This script implements the exact "Quick Fix" method that achieved:
- V2: 52.4° novel error (BEST)
- V1: 64.1° novel error
- hV4: 75.0° novel error

CRITICAL: This code preserves all bug fixes from the successful session!

Usage:
    python run_reconstruction_reproduction.py --roi V2
    python run_reconstruction_reproduction.py --roi V1 --subject 02
"""

import sys
import os
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import nibabel as nib
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt

from nilearn.glm.first_level import FirstLevelModel
from nilearn import image as nimg

# Try different nilearn versions
try:
    from nilearn.maskers import NiftiMasker
except ImportError:
    from nilearn.input_data import NiftiMasker

from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from scipy import stats

# Add parent directory for config import
sys.path.insert(0, str(Path(__file__).parent.parent))
from reproduction_pipeline.config_reproduction_output import cfg  # CHANGED: Use output config


# ============================================================================
# Parse Arguments
# ============================================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description='Color reconstruction reproduction pipeline'
    )
    parser.add_argument(
        '--roi',
        type=str,
        required=True,
        choices=list(cfg.WANG_ROI_MAP.keys()),
        help='ROI name (V1, V2, V3, or hV4)'
    )
    parser.add_argument(
        '--subject',
        type=str,
        default=cfg.SUB_ID,
        help=f'Subject ID (default: {cfg.SUB_ID})'
    )
    return parser.parse_args()


# ============================================================================
# Helper Functions
# ============================================================================

def diag_linear_predict(train_X, train_y, test_X):
    """
    Diagonal Linear Discriminant Analysis (B&H 2009 method).

    Assumes diagonal covariance (features are independent).
    """
    classes = np.unique(train_y)
    means = np.stack([train_X[train_y==c].mean(axis=0) for c in classes])
    vars_  = np.stack([train_X[train_y==c].var(axis=0) + 1e-8 for c in classes])

    # Log-likelihood for each class
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


def create_basis_functions(n_channels=6):
    """
    Create 6 idealized color channels (B&H 2009).

    Half-wave rectified squared cosine tuning curves.
    """
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


def hue_to_channels(hue_deg, basis_functions):
    """Convert hue (0-360) to 6 channel outputs"""
    hue_idx = int(np.round(hue_deg)) % 360
    return basis_functions[hue_idx]


# ============================================================================
# Main Pipeline
# ============================================================================

def main():
    args = parse_args()
    roi_name = args.roi
    subject_id = args.subject

    # Setup output directory
    output_dir = cfg.get_analysis_output_dir(roi_name, subject_id)
    output_dir.mkdir(parents=True, exist_ok=True)

    fig_dir = output_dir / "figures"
    fig_dir.mkdir(exist_ok=True)

    # Setup logging
    log_file = output_dir / "log.txt"

    print("="*70)
    print("Color Reconstruction Reproduction Pipeline")
    print("="*70)
    print(f"Subject: sub-{subject_id}")
    print(f"ROI: {roi_name}")
    print(f"Method: Universal HRF (Quick Fix)")
    print(f"PCA: {cfg.N_PCA_COMPONENTS} components")
    print(f"Output: {output_dir}")
    print("="*70)
    print()

    # ========================================================================
    # [1/8] Load ROI Mask
    # ========================================================================

    print(f"[1/8] Loading ROI mask")
    roi_path = cfg.get_roi_mask_path(roi_name, subject_id)

    if not roi_path.exists():
        print(f"ERROR: ROI mask not found: {roi_path}")
        print("Run build_rois_reproduction.py first!")
        sys.exit(1)

    roi_img = nib.load(roi_path)
    masker = NiftiMasker(mask_img=str(roi_path), standardize=False)
    masker.fit()

    n_voxels = int(np.sum(roi_img.get_fdata() > 0))
    print(f"  Voxels: {n_voxels}")

    # Validate voxel count
    if roi_name in cfg.EXPECTED_RESULTS:
        expected = cfg.EXPECTED_RESULTS[roi_name]['n_voxels']
        diff_pct = ((n_voxels - expected) / expected) * 100
        print(f"  Expected: {expected} voxels")
        print(f"  Difference: {diff_pct:+.1f}%")
        if abs(diff_pct) >= 5:
            print(f"  [!] WARNING: Large deviation - results may differ!")
    print()

    # ========================================================================
    # [2/8] Load Functional Data and Events
    # ========================================================================

    print(f"[2/8] Loading {cfg.N_RUNS} runs of functional data")

    func_imgs = []
    events_list = []
    confounds_list = []

    for run in range(1, cfg.N_RUNS + 1):
        # Functional data
        func_path = cfg.get_func_img_path(run, subject_id)
        if not func_path.exists():
            print(f"ERROR: Functional image not found: {func_path}")
            sys.exit(1)

        func_img = nib.load(func_path)

        # Drop initial volumes
        if cfg.VOLS_TO_DROP > 0:
            func_img = nimg.index_img(func_img, slice(cfg.VOLS_TO_DROP, None))

        func_imgs.append(func_img)

        # Events
        event_path = cfg.get_event_file_path(run, subject_id)
        if not event_path.exists():
            print(f"ERROR: Event file not found: {event_path}")
            sys.exit(1)

        events = pd.read_csv(event_path, sep='\t')
        events_list.append(events)

        # Confounds
        confound_path = cfg.get_confound_file_path(run, subject_id)
        confounds = pd.read_csv(confound_path, sep='\t')
        motion_cols = ['trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z']
        confounds_subset = confounds[motion_cols]

        if cfg.VOLS_TO_DROP > 0:
            confounds_subset = confounds_subset.iloc[cfg.VOLS_TO_DROP:]

        confounds_list.append(confounds_subset)

        print(f"  Run {run}: {func_img.shape}, {len(events)} events")

    print(f"  Total: {len(func_imgs)} runs loaded")
    print()

    # ========================================================================
    # [3/8] Fit FIR Model
    # ========================================================================

    print(f"[3/8] Fitting FIR model")
    print(f"  FIR delays: {len(cfg.FIR_DELAYS)} time bins (0-{max(cfg.FIR_DELAYS)*cfg.TR:.1f}s)")

    fir_model = FirstLevelModel(
        t_r=cfg.TR,
        hrf_model='fir',
        fir_delays=cfg.FIR_DELAYS,
        drift_model='cosine',
        high_pass=1/128.0,
        mask_img=str(roi_path),
        standardize=False,
        minimize_memory=False
    )

    fir_model.fit(func_imgs, events_list, confounds_list)
    print(f"  ✓ FIR model fitted")
    print()

    # ========================================================================
    # [4/8] Universal HRF and Optimal Delay
    # ========================================================================

    print(f"[4/8] Estimating universal HRF and optimal delay")

    # Extract FIR responses for all colors at all delays
    mean_responses = []

    for color_idx in range(1, cfg.N_COLORS + 1):
        color_responses = []

        for delay in cfg.FIR_DELAYS:
            contrast_name = f'color_{color_idx}_delay_{delay}'
            try:
                contrast_map = fir_model.compute_contrast(
                    contrast_name,
                    output_type='effect_size'
                )
                mean_response = masker.transform(contrast_map).mean()
                color_responses.append(mean_response)
            except:
                color_responses.append(0)

        mean_responses.append(color_responses)

    mean_responses = np.array(mean_responses)

    # Universal HRF (average across colors)
    universal_hrf = mean_responses.mean(axis=0)

    # *** CRITICAL BUG FIX ***
    # Use absolute value to handle negative HRF values!
    optimal_delay = np.argmax(np.abs(universal_hrf))
    optimal_time = optimal_delay * cfg.TR

    print(f"  Universal HRF: {universal_hrf}")
    print(f"  Absolute values: {np.abs(universal_hrf)}")
    print(f"  *** Optimal delay: {optimal_delay} TRs ({optimal_time:.1f}s) ***")
    print(f"  Peak amplitude: {universal_hrf[optimal_delay]:.4f}")

    # Validate optimal delay
    if roi_name in cfg.EXPECTED_RESULTS:
        expected_delay = cfg.EXPECTED_RESULTS[roi_name]['optimal_delay_TRs']
        print(f"  Expected delay: {expected_delay} TRs ({expected_delay*cfg.TR:.1f}s)")
        if optimal_delay != expected_delay:
            print(f"  [!] WARNING: Delay mismatch - may affect results!")
    print()

    # ========================================================================
    # [5/8] Extract Betas at Optimal Delay
    # ========================================================================

    print(f"[5/8] Extracting betas at delay {optimal_delay}")

    all_betas = []

    for run_idx in range(cfg.N_RUNS):
        run_betas = []

        for color_idx in range(1, cfg.N_COLORS + 1):
            contrast_name = f'color_{color_idx}_delay_{optimal_delay}'

            try:
                contrast_map = fir_model.compute_contrast(
                    contrast_name,
                    output_type='effect_size'
                )
                betas = masker.transform(contrast_map).ravel()
                run_betas.append(betas)
            except Exception as e:
                print(f"  ERROR extracting {contrast_name}: {e}")
                run_betas.append(np.zeros(n_voxels))

        all_betas.append(np.array(run_betas))
        print(f"  Run {run_idx+1}: {len(run_betas)} colors extracted")

    all_betas = np.array(all_betas)  # (n_runs, n_colors, n_voxels)
    print(f"  Shape: {all_betas.shape}")
    print()

    # ========================================================================
    # [6/8] Classification (Leave-One-Run-Out)
    # ========================================================================

    print(f"[6/8] Classification with diagonal LDA")

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

        # PCA
        if cfg.USE_PCA:
            pca = PCA(n_components=cfg.N_PCA_COMPONENTS)
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

        print(f"  Run {test_run+1}: {acc*100:.1f}%")

    mean_acc = np.mean([r['accuracy'] for r in classification_results])
    print(f"  Mean accuracy: {mean_acc*100:.1f}%")

    # Validate
    if roi_name in cfg.EXPECTED_RESULTS:
        expected_acc = cfg.EXPECTED_RESULTS[roi_name]['classification_accuracy']
        print(f"  Expected accuracy: {expected_acc*100:.1f}%")
        if abs(mean_acc - expected_acc) > 0.01:
            print(f"  [!] WARNING: Accuracy mismatch!")
    print()

    # ========================================================================
    # [7/8] Reconstruction (Leave-One-Run-Out)
    # ========================================================================

    print(f"[7/8] Reconstruction with forward model")

    # Create basis functions
    basis_functions = create_basis_functions(n_channels=cfg.N_CHANNELS)

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

        # PCA
        if cfg.USE_PCA:
            pca = PCA(n_components=cfg.N_PCA_COMPONENTS)
            X_train_final = pca.fit_transform(X_train_scaled)
            X_test_final = pca.transform(X_test_scaled)
        else:
            X_train_final = X_train_scaled
            X_test_final = X_test_scaled

        # Train forward model: B = W × C
        C_train = []
        for color_idx in y_train:
            color_name = f'color_{color_idx+1}'
            hue_deg = cfg.LABEL2HUE_DEG_PILOT[color_name]
            channels = hue_to_channels(hue_deg, basis_functions)
            C_train.append(channels)
        C_train = np.array(C_train).T  # (6, n_train)

        # Estimate weights
        W = X_train_final.T @ C_train.T @ np.linalg.inv(C_train @ C_train.T)

        # *** CRITICAL BUG FIX ***
        # Use pseudoinverse to avoid singular matrix errors!
        C_test_est = np.linalg.pinv(W.T @ W) @ W.T @ X_test_final.T

        # Reconstruct hues
        reconstructed_hues = []
        true_hues = []

        for test_idx, color_idx in enumerate(y_test):
            estimated_channels = C_test_est[:, test_idx]

            # Find best matching hue
            correlations = []
            for h in range(360):
                template_channels = basis_functions[h]
                corr = np.corrcoef(estimated_channels, template_channels)[0, 1]
                correlations.append(corr)

            reconstructed_hue = np.argmax(correlations)

            color_name = f'color_{color_idx+1}'
            true_hue = cfg.LABEL2HUE_DEG_PILOT[color_name]

            reconstructed_hues.append(reconstructed_hue)
            true_hues.append(true_hue)

        # Calculate errors
        errors = circular_diff_deg(
            np.array(reconstructed_hues),
            np.array(true_hues)
        )
        mean_error = errors.mean()

        reconstruction_results.append({
            'test_run': test_run + 1,
            'mean_error': mean_error,
            'reconstructed_hues': reconstructed_hues,
            'true_hues': true_hues,
            'errors': errors
        })

        print(f"  Run {test_run+1}: {mean_error:.1f}°")

    mean_recon_error = np.mean([r['mean_error'] for r in reconstruction_results])
    print(f"  Mean error: {mean_recon_error:.1f}°")

    # Validate
    if roi_name in cfg.EXPECTED_RESULTS:
        expected_error = cfg.EXPECTED_RESULTS[roi_name]['training_error_deg']
        print(f"  Expected error: {expected_error:.1f}°")
        diff = abs(mean_recon_error - expected_error)
        if diff > 2.0:
            print(f"  [!] WARNING: Error mismatch ({diff:.1f}° difference)!")
    print()

    # ========================================================================
    # [8/8] Leave-One-Color-Out (Novel Colors)
    # ========================================================================

    print(f"[8/8] Leave-one-color-out (novel colors)")

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

            # Standardize
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)

            # PCA
            if cfg.USE_PCA:
                pca = PCA(n_components=min(cfg.N_PCA_COMPONENTS, len(X_train)))
                X_train_final = pca.fit_transform(X_train_scaled)
                X_test_final = pca.transform(X_test_scaled)
            else:
                X_train_final = X_train_scaled
                X_test_final = X_test_scaled

            # Train forward model
            C_train = []
            for color_idx in y_train:
                color_name = f'color_{color_idx+1}'
                hue_deg = cfg.LABEL2HUE_DEG_PILOT[color_name]
                channels = hue_to_channels(hue_deg, basis_functions)
                C_train.append(channels)
            C_train = np.array(C_train).T

            W = X_train_final.T @ C_train.T @ np.linalg.inv(C_train @ C_train.T)

            # *** CRITICAL BUG FIX ***
            C_test_est = np.linalg.pinv(W.T @ W) @ W.T @ X_test_final.T

            estimated_channels = C_test_est[:, 0]

            correlations = []
            for h in range(360):
                template_channels = basis_functions[h]
                corr = np.corrcoef(estimated_channels, template_channels)[0, 1]
                correlations.append(corr)

            reconstructed_hue = np.argmax(correlations)

            color_name = f'color_{held_out_color+1}'
            true_hue = cfg.LABEL2HUE_DEG_PILOT[color_name]

            error = circular_diff_deg(reconstructed_hue, true_hue)
            all_errors_this_color.append(error)

        mean_error_this_color = np.mean(all_errors_this_color)
        color_name = f'color_{held_out_color+1}'

        novel_color_results.append({
            'color': color_name,
            'mean_error': mean_error_this_color,
            'errors': all_errors_this_color
        })

        print(f"  {color_name}: {mean_error_this_color:.1f}°")

    mean_novel_error = np.mean([r['mean_error'] for r in novel_color_results])
    print(f"  Mean novel error: {mean_novel_error:.1f}°")
    print(f"  Chance level: 90.0°")

    # Validate (MOST CRITICAL!)
    if roi_name in cfg.EXPECTED_RESULTS:
        expected_novel = cfg.EXPECTED_RESULTS[roi_name]['novel_error_deg']
        print(f"  Expected novel error: {expected_novel:.1f}°")
        diff = abs(mean_novel_error - expected_novel)
        if diff > 3.0:
            print(f"  [!] WARNING: Large mismatch ({diff:.1f}° difference)!")
        else:
            print(f"  ✓ Results match expected! (Δ = {diff:.1f}°)")
    print()

    # ========================================================================
    # Save Results
    # ========================================================================

    print("Saving results...")

    # Save summary
    summary_data = {
        'ROI': [roi_name],
        'Subject': [subject_id],
        'N_voxels': [n_voxels],
        'Optimal_delay_TRs': [optimal_delay],
        'Optimal_delay_sec': [optimal_time],
        'Classification_accuracy': [mean_acc],
        'Training_error_deg': [mean_recon_error],
        'Novel_error_deg': [mean_novel_error],
    }

    if roi_name in cfg.EXPECTED_RESULTS:
        exp = cfg.EXPECTED_RESULTS[roi_name]
        summary_data.update({
            'Expected_voxels': [exp['n_voxels']],
            'Expected_delay_TRs': [exp['optimal_delay_TRs']],
            'Expected_classification': [exp['classification_accuracy']],
            'Expected_training_error': [exp['training_error_deg']],
            'Expected_novel_error': [exp['novel_error_deg']],
        })

    summary_df = pd.DataFrame(summary_data)
    summary_csv = output_dir / "summary.csv"
    summary_df.to_csv(summary_csv, index=False)
    print(f"  ✓ Saved: {summary_csv}")

    # ========================================================================
    # Final Summary
    # ========================================================================

    print()
    print("="*70)
    print("REPRODUCTION RESULTS")
    print("="*70)
    print(f"ROI: {roi_name}")
    print(f"Voxels: {n_voxels}")
    print(f"Optimal delay: {optimal_delay} TRs ({optimal_time:.1f}s)")
    print(f"Classification: {mean_acc*100:.1f}%")
    print(f"Training error: {mean_recon_error:.1f}°")
    print(f"Novel error: {mean_novel_error:.1f}°")
    print()

    if roi_name in cfg.EXPECTED_RESULTS:
        exp = cfg.EXPECTED_RESULTS[roi_name]
        print("COMPARISON WITH DOCUMENTED RESULTS:")
        print(f"  Voxels: {n_voxels} vs {exp['n_voxels']} (expected)")
        print(f"  Delay: {optimal_delay} vs {exp['optimal_delay_TRs']} TRs (expected)")
        print(f"  Classification: {mean_acc*100:.1f}% vs {exp['classification_accuracy']*100:.1f}% (expected)")
        print(f"  Training: {mean_recon_error:.1f}° vs {exp['training_error_deg']:.1f}° (expected)")
        print(f"  Novel: {mean_novel_error:.1f}° vs {exp['novel_error_deg']:.1f}° (expected)")
        print()

        # Overall match score
        novel_diff = abs(mean_novel_error - exp['novel_error_deg'])
        if novel_diff < 2.0:
            print("✓✓✓ EXCELLENT MATCH - Results successfully reproduced!")
        elif novel_diff < 5.0:
            print("✓✓ GOOD MATCH - Minor differences within tolerance")
        else:
            print("⚠ PARTIAL MATCH - Investigate differences")

    print("="*70)
    print()
    print(f"Results saved to: {output_dir}")
    print()


if __name__ == '__main__':
    main()
