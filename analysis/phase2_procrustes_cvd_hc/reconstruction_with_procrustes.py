#!/usr/bin/env python3
"""
reconstruction_with_procrustes.py
==================================

Procrustes 기반 voxel pattern alignment + common W matrix

**Pipeline:**
1. HC subjects: 각자의 amplitudes_z 로드
2. HC 평균 color pattern 계산 (reference)
3. 각 HC를 reference에 Procrustes 정렬
4. 정렬된 HC들로 common W 학습
5. CVD subjects:
   - Amplitudes_z 로드
   - Procrustes로 HC reference에 정렬
   - HC common W 적용

**장점:**
- SRM보다 빠름 (no iterative fitting)
- 해석 쉬움 (직접적인 좌표 변환)

**단점:**
- SRM보다 alignment 능력 낮을 수 있음
- 각 subject 독립적으로 정렬 (global structure 고려 안함)

Usage:
    # Train HC model
    python analysis/group_level/reconstruction_with_procrustes.py \
        --mode train \
        --roi V1 \
        --hc-subjects 02 03 05 06 07

    # Test CVD
    python analysis/group_level/reconstruction_with_procrustes.py \
        --mode test \
        --roi V1 \
        --cvd-subjects 08 09 10

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
from scipy.spatial import procrustes
from sklearn.preprocessing import StandardScaler

# ============================================================================
# Configuration
# ============================================================================

def parse_args():
    parser = argparse.ArgumentParser(description='Procrustes-based Reconstruction')
    parser.add_argument('--mode', type=str, required=True, choices=['train', 'test'])
    parser.add_argument('--roi', type=str, required=True)
    parser.add_argument('--timestamp', type=str, default='baseline81_deob_determin')
    parser.add_argument('--dataset', type=str, default='deoblique_v2')
    parser.add_argument('--hc-subjects', type=str, nargs='+',
                        default=['03', '05', '06', '07'])
    parser.add_argument('--cvd-subjects', type=str, nargs='+',
                        default=['08', '09', '10'])
    parser.add_argument('--output-dir', type=str,
                        default='results/group_level/procrustes_reconstruction/')
    parser.add_argument('--model-path', type=str, default=None)
    return parser.parse_args()

# ============================================================================
# Helper Functions (same as SRM version)
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
    hue_idx = int(np.round(hue_deg)) % 360
    return basis_functions[hue_idx]

def circular_diff_deg(a, b):
    diff = np.abs(a - b)
    diff = np.where(diff > 180, 360 - diff, diff)
    return diff

LABEL2HUE_DEG = {
    'color_1': 0.0, 'color_2': 45.0, 'color_3': 90.0, 'color_4': 135.0,
    'color_5': 180.0, 'color_6': 225.0, 'color_7': 270.0, 'color_8': 315.0,
}

def load_subject_amplitudes(subject_id, roi, timestamp, dataset='deoblique_v2'):
    base_path = Path(f'derivatives/BH2009_{dataset}/{timestamp}')
    pattern = str(base_path / f'sm*_sub-{subject_id}_{roi}_*')
    matches = glob.glob(pattern)

    if len(matches) == 0:
        raise FileNotFoundError(f"No results for sub-{subject_id} {roi}")

    result_dir = Path(matches[0])
    amp_file = result_dir / 'amplitudes_z.npy'

    if not amp_file.exists():
        raise FileNotFoundError(f"amplitudes_z.npy not found")

    amplitudes_z = np.load(amp_file)
    print(f"  Loaded sub-{subject_id}: {amplitudes_z.shape}")
    return amplitudes_z

# ============================================================================
# Procrustes Alignment Function
# ============================================================================

def align_to_reference(subject_pattern, reference_pattern):
    """
    Align subject's color pattern to reference using Procrustes

    Parameters:
    -----------
    subject_pattern : ndarray, (n_colors, n_voxels)
    reference_pattern : ndarray, (n_colors, n_voxels)

    Returns:
    --------
    aligned_pattern : ndarray, (n_colors, n_voxels)
    disparity : float
    """
    _, aligned, disparity = procrustes(reference_pattern, subject_pattern)
    return aligned, disparity

# ============================================================================
# Mode 1: Train HC Model
# ============================================================================

def train_hc_model(args):
    print(f"\n{'='*70}")
    print(f"MODE 1: TRAIN HC MODEL (Procrustes)")
    print(f"{'='*70}\n")

    roi = args.roi
    hc_subjects = args.hc_subjects

    print(f"ROI: {roi}")
    print(f"HC subjects: {hc_subjects}\n")

    # ========================================================================
    # Step 1: Load HC amplitudes
    # ========================================================================
    print(f"[1/5] Loading HC baseline results...")

    hc_amplitudes = []
    for sub_id in hc_subjects:
        amp = load_subject_amplitudes(sub_id, roi, args.timestamp, args.dataset)
        hc_amplitudes.append(amp)

    # Check consistency
    voxel_counts = [amp.shape[2] for amp in hc_amplitudes]
    if len(set(voxel_counts)) > 1:
        print(f"\n  ⚠️  Inconsistent voxel counts: {voxel_counts}")
        min_voxels = min(voxel_counts)
        hc_amplitudes = [amp[:, :, :min_voxels] for amp in hc_amplitudes]
        print(f"     Using minimum: {min_voxels}")

    n_runs, n_colors, n_voxels = hc_amplitudes[0].shape
    print(f"\n  Final shape: ({n_runs}, {n_colors}, {n_voxels})")

    # ========================================================================
    # Step 2: Compute HC reference (grand mean across subjects and runs)
    # ========================================================================
    print(f"\n[2/5] Computing HC reference pattern...")

    # Average across runs for each subject (excluding zero-variance runs)
    hc_mean_patterns = []
    for sub_idx, amp in enumerate(hc_amplitudes):
        valid_runs = []
        for run_idx in range(n_runs):
            pattern = amp[run_idx]
            if np.var(pattern) >= 1e-10:  # Valid run
                valid_runs.append(pattern)

        if len(valid_runs) > 0:
            mean_pattern = np.mean(valid_runs, axis=0)  # (n_colors, n_voxels)
            hc_mean_patterns.append(mean_pattern)
            print(f"  sub-{hc_subjects[sub_idx]}: {len(valid_runs)}/{n_runs} valid runs")
        else:
            print(f"  sub-{hc_subjects[sub_idx]}: WARNING - no valid runs!")

    if len(hc_mean_patterns) == 0:
        raise ValueError("No valid HC patterns to create reference!")

    # Grand mean across subjects
    hc_reference = np.mean(hc_mean_patterns, axis=0)  # (n_colors, n_voxels)

    print(f"  HC reference: {hc_reference.shape}")
    print(f"  Used {len(hc_mean_patterns)} subjects for reference")

    # ========================================================================
    # Step 3: Align each HC subject to reference
    # ========================================================================
    print(f"\n[3/5] Aligning HC subjects to reference...")

    hc_aligned = []
    disparities = []
    total_valid_runs = 0
    total_skipped_runs = 0

    for sub_idx, sub_id in enumerate(hc_subjects):
        print(f"\n  sub-{sub_id}:")

        amp = hc_amplitudes[sub_idx]  # (n_runs, n_colors, n_voxels)

        aligned_runs = []
        valid_run_count = 0

        for run_idx in range(n_runs):
            pattern = amp[run_idx]  # (n_colors, n_voxels)

            # Check if run has valid data (non-zero variance)
            pattern_var = np.var(pattern)
            if pattern_var < 1e-10:
                print(f"    Run {run_idx+1}: SKIPPED (zero variance - all values same)")
                total_skipped_runs += 1
                continue

            # Align to reference
            try:
                aligned, disparity = align_to_reference(pattern, hc_reference)
                aligned_runs.append(aligned)
                disparities.append(disparity)
                valid_run_count += 1
                total_valid_runs += 1
            except ValueError as e:
                print(f"    Run {run_idx+1}: SKIPPED (Procrustes error: {e})")
                total_skipped_runs += 1
                continue

        if len(aligned_runs) == 0:
            print(f"    WARNING: No valid runs for sub-{sub_id}!")
            continue

        aligned_runs = np.array(aligned_runs)  # (n_valid_runs, n_colors, n_voxels)
        hc_aligned.append(aligned_runs)

        mean_disparity = np.mean([d for d in disparities[-valid_run_count:]])
        print(f"    Valid runs: {valid_run_count}/{n_runs}")
        print(f"    Mean disparity: {mean_disparity:.4f} (stability: {1-mean_disparity:.4f})")

    print(f"\n  Total valid runs: {total_valid_runs}")
    print(f"  Total skipped runs: {total_skipped_runs}")

    if len(hc_aligned) == 0:
        raise ValueError("No valid subjects after alignment! Check baseline data quality.")

    # ========================================================================
    # Step 4: Learn common W matrix
    # ========================================================================
    print(f"\n[4/5] Learning common W matrix...")

    basis_functions = create_basis_functions(n_channels=6)

    # Concatenate all aligned HC data
    X_train_all = []
    C_train_all = []

    for sub_idx in range(len(hc_subjects)):
        amp_aligned = hc_aligned[sub_idx]  # (n_runs, n_colors, n_voxels)

        for run_idx in range(n_runs):
            for color_idx in range(n_colors):
                voxel_pattern = amp_aligned[run_idx, color_idx, :]

                X_train_all.append(voxel_pattern)

                color_name = f'color_{color_idx + 1}'
                hue_deg = LABEL2HUE_DEG[color_name]
                channels = hue_to_channels(hue_deg, basis_functions)
                C_train_all.append(channels)

    X_train_all = np.array(X_train_all)  # (n_subjects*n_runs*n_colors, n_voxels)
    C_train_all = np.array(C_train_all).T  # (6, n_subjects*n_runs*n_colors)

    print(f"  X_train: {X_train_all.shape}")
    print(f"  C_train: {C_train_all.shape}")

    # Estimate W
    W_common = X_train_all.T @ C_train_all.T @ np.linalg.inv(C_train_all @ C_train_all.T)

    print(f"  W_common: {W_common.shape} (n_voxels × 6)")

    # ========================================================================
    # Step 5: Evaluate HC Reconstruction (CRITICAL for quality check)
    # ========================================================================
    print(f"\n[5/7] Evaluating HC reconstruction with common W...")
    print(f"  Purpose: Verify common W quality before applying to CVD")
    print(f"  Testing BOTH aligned and no-alignment versions")

    hc_reconstruction_results = []

    for sub_idx, sub_id in enumerate(hc_subjects):
        if sub_idx >= len(hc_aligned):
            continue

        print(f"\n  sub-{sub_id}:")
        amp_aligned = hc_aligned[sub_idx]  # (n_valid_runs, n_colors, n_voxels)
        amp_original = hc_amplitudes[sub_idx]  # Original data (no alignment)
        n_valid_runs = amp_aligned.shape[0]

        if n_valid_runs < 2:
            print(f"    SKIPPED: Need at least 2 runs for LORO-CV")
            continue

        # Leave-one-run-out cross-validation (WITH alignment)
        reconstruction_errors = []
        reconstructed_hues = []
        true_hues = []
        predictions = []
        true_labels = []

        # Also test WITHOUT alignment
        reconstruction_errors_noalign = []
        reconstructed_hues_noalign = []
        predictions_noalign = []
        true_labels_noalign = []

        for test_run_idx in range(n_valid_runs):
            # Train on all runs except test_run_idx (proper LORO-CV)
            train_runs = [r for r in range(n_valid_runs) if r != test_run_idx]

            # Re-train W using only train runs
            X_train_loro = []
            C_train_loro = []

            for train_run_idx in train_runs:
                for color_idx in range(n_colors):
                    voxel_pattern = amp_aligned[train_run_idx, color_idx, :]
                    X_train_loro.append(voxel_pattern)

                    color_name = f'color_{color_idx + 1}'
                    hue_deg = LABEL2HUE_DEG[color_name]
                    channels = hue_to_channels(hue_deg, basis_functions)
                    C_train_loro.append(channels)

            X_train_loro = np.array(X_train_loro)  # (n_train_runs*n_colors, n_voxels)
            C_train_loro = np.array(C_train_loro).T  # (6, n_train_runs*n_colors)

            # Learn W from train runs only
            W_loro = X_train_loro.T @ C_train_loro.T @ np.linalg.inv(C_train_loro @ C_train_loro.T)

            # Test data
            X_test = amp_aligned[test_run_idx]  # (n_colors, n_voxels)

            # Estimate channels with LORO W
            C_est = np.linalg.pinv(W_loro.T @ W_loro) @ W_loro.T @ X_test.T
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

                # Store hues for visualization
                reconstructed_hues.append(reconstructed_hue)
                true_hues.append(true_hue)

                # For classification - determine which color bin the reconstructed hue falls into
                # Each color bin covers 45° centered on its true hue
                min_dist = 360
                predicted_color = 0
                for c_idx in range(n_colors):
                    c_name = f'color_{c_idx + 1}'
                    c_hue = LABEL2HUE_DEG[c_name]
                    dist = circular_diff_deg(reconstructed_hue, c_hue)
                    if dist < min_dist:
                        min_dist = dist
                        predicted_color = c_idx

                predictions.append(predicted_color)
                true_labels.append(color_idx)

            # ================================================================
            # Test WITHOUT alignment (using original data)
            # ================================================================
            X_test_noalign = amp_original[test_run_idx]  # (n_colors, n_voxels)

            # Estimate channels with W_loro (same W as aligned version)
            C_est_noalign = np.linalg.pinv(W_loro.T @ W_loro) @ W_loro.T @ X_test_noalign.T

            for color_idx in range(n_colors):
                estimated_channels_noalign = C_est_noalign[:, color_idx]

                # Find best hue
                correlations_noalign = []
                for h in range(360):
                    template = basis_functions[h]
                    corr = np.corrcoef(estimated_channels_noalign, template)[0, 1]
                    correlations_noalign.append(corr)

                reconstructed_hue_noalign = np.argmax(correlations_noalign)

                color_name = f'color_{color_idx + 1}'
                true_hue = LABEL2HUE_DEG[color_name]

                error_noalign = circular_diff_deg(reconstructed_hue_noalign, true_hue)
                reconstruction_errors_noalign.append(error_noalign)

                # Store for comparison
                reconstructed_hues_noalign.append(reconstructed_hue_noalign)

                # Classification
                min_dist_noalign = 360
                predicted_color_noalign = 0
                for c_idx in range(n_colors):
                    c_name = f'color_{c_idx + 1}'
                    c_hue = LABEL2HUE_DEG[c_name]
                    dist = circular_diff_deg(reconstructed_hue_noalign, c_hue)
                    if dist < min_dist_noalign:
                        min_dist_noalign = dist
                        predicted_color_noalign = c_idx

                predictions_noalign.append(predicted_color_noalign)
                true_labels_noalign.append(color_idx)

        mean_error = np.mean(reconstruction_errors)
        accuracy = np.mean(np.array(predictions) == np.array(true_labels))

        mean_error_noalign = np.mean(reconstruction_errors_noalign)
        accuracy_noalign = np.mean(np.array(predictions_noalign) == np.array(true_labels_noalign))

        print(f"    Runs used: {n_valid_runs}")
        print(f"    With alignment:")
        print(f"      Mean error: {mean_error:.1f}°")
        print(f"      Accuracy: {accuracy*100:.1f}%")
        print(f"    Without alignment:")
        print(f"      Mean error: {mean_error_noalign:.1f}°")
        print(f"      Accuracy: {accuracy_noalign*100:.1f}%")
        print(f"    Alignment benefit: {mean_error_noalign - mean_error:.1f}°")

        hc_reconstruction_results.append({
            'subject_id': sub_id,
            'mean_error': mean_error,
            'mean_error_noalign': mean_error_noalign,
            'accuracy': accuracy,
            'accuracy_noalign': accuracy_noalign,
            'n_runs': n_valid_runs,
            'all_errors': reconstruction_errors,
            'all_errors_noalign': reconstruction_errors_noalign,
            'reconstructed_hues': reconstructed_hues,
            'reconstructed_hues_noalign': reconstructed_hues_noalign,
            'true_hues': true_hues,
        })

    # Summary statistics
    if len(hc_reconstruction_results) > 0:
        all_errors = [r['mean_error'] for r in hc_reconstruction_results]
        all_errors_noalign = [r['mean_error_noalign'] for r in hc_reconstruction_results]
        all_accs = [r['accuracy'] for r in hc_reconstruction_results]
        all_accs_noalign = [r['accuracy_noalign'] for r in hc_reconstruction_results]

        print(f"\n  ========================================")
        print(f"  HC Reconstruction Summary (Common W)")
        print(f"  ========================================")
        print(f"  WITH ALIGNMENT:")
        print(f"    Mean error: {np.mean(all_errors):.1f}° ± {np.std(all_errors):.1f}°")
        print(f"    Accuracy: {np.mean(all_accs)*100:.1f}% ± {np.std(all_accs)*100:.1f}%")
        print(f"  WITHOUT ALIGNMENT:")
        print(f"    Mean error: {np.mean(all_errors_noalign):.1f}° ± {np.std(all_errors_noalign):.1f}°")
        print(f"    Accuracy: {np.mean(all_accs_noalign)*100:.1f}% ± {np.std(all_accs_noalign)*100:.1f}%")
        print(f"  Chance level: 90.0° (error), 12.5% (accuracy)")
        print(f"  Mean alignment benefit: {np.mean(all_errors_noalign) - np.mean(all_errors):.1f}°")

        # Quality check
        if np.mean(all_errors) < 90.0:
            print(f"  ✅ Aligned: Common W is better than chance!")
        else:
            print(f"  ⚠️  WARNING: Aligned version not better than chance!")

        if np.mean(all_errors_noalign) < 90.0:
            print(f"  ✅ No-align: Better than chance!")
        else:
            print(f"  ⚠️  No-align: At or worse than chance level!")

    # ========================================================================
    # Step 6: Visualization
    # ========================================================================
    print(f"\n[6/7] Creating visualizations...")

    output_dir = Path(args.output_dir) / roi
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create comparison plot
    if len(hc_reconstruction_results) > 0:
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))

        # Left: Error bars
        ax = axes[0]
        subjects = [r['subject_id'] for r in hc_reconstruction_results]
        errors = [r['mean_error'] for r in hc_reconstruction_results]

        x = np.arange(len(subjects))
        bars = ax.bar(x, errors, color='steelblue', edgecolor='black', alpha=0.7)

        # Chance level line
        ax.axhline(90.0, color='red', linestyle='--', linewidth=2, label='Chance (90°)')

        ax.set_xticks(x)
        ax.set_xticklabels([f'sub-{s}' for s in subjects])
        ax.set_ylabel('Reconstruction Error (°)', fontsize=12)
        ax.set_title(f'{roi}: HC Reconstruction Error\n(with Common W)', fontsize=13, fontweight='bold')
        ax.legend()
        ax.grid(axis='y', alpha=0.3)

        # Right: Accuracy bars
        ax = axes[1]
        accs = [r['accuracy']*100 for r in hc_reconstruction_results]
        bars = ax.bar(x, accs, color='coral', edgecolor='black', alpha=0.7)

        # Chance level line
        ax.axhline(12.5, color='red', linestyle='--', linewidth=2, label='Chance (12.5%)')

        ax.set_xticks(x)
        ax.set_xticklabels([f'sub-{s}' for s in subjects])
        ax.set_ylabel('Classification Accuracy (%)', fontsize=12)
        ax.set_title(f'{roi}: HC Classification Accuracy\n(with Common W)', fontsize=13, fontweight='bold')
        ax.set_ylim([0, 100])
        ax.legend()
        ax.grid(axis='y', alpha=0.3)

        plt.tight_layout()
        fig_path = output_dir / 'hc_reconstruction_evaluation.png'
        plt.savefig(fig_path, dpi=150, bbox_inches='tight')
        plt.close()

        print(f"  Saved: {fig_path}")

        # ====================================================================
        # Circular Color Wheel Visualization (per subject)
        # ====================================================================
        print(f"  Creating circular color wheel plots...")

        for r_idx, result in enumerate(hc_reconstruction_results):
            fig, ax = plt.subplots(figsize=(10, 10), subplot_kw={'projection': 'polar'})
            ax.set_theta_zero_location("E")
            ax.set_theta_direction(1)

            # Get stored hues
            true_hues = result['true_hues']
            reconstructed_hues = result['reconstructed_hues']
            n_samples = len(true_hues)
            n_colors_actual = 8

            # Define colors for each color condition (8 colors)
            color_palette = plt.cm.hsv(np.linspace(0, 1, n_colors_actual + 1)[:n_colors_actual])

            # Plot each trial
            for sample_idx in range(n_samples):
                true_hue_deg = true_hues[sample_idx]
                recon_hue_deg = reconstructed_hues[sample_idx]

                true_rad = np.deg2rad(true_hue_deg)
                recon_rad = np.deg2rad(recon_hue_deg)

                # Determine which color this trial belongs to
                color_idx = sample_idx % n_colors_actual
                trial_color = color_palette[color_idx]

                # Draw connecting line (error)
                ax.plot([true_rad, recon_rad], [1.0, 0.7],
                       color=trial_color, alpha=0.3, linewidth=1, zorder=1)

                # Reconstructed position (inner circle)
                ax.scatter([recon_rad], [0.7], s=50, color=trial_color,
                          edgecolor='white', linewidth=0.5, alpha=0.6, zorder=3)

            # Draw true color positions (outer circle, larger)
            for color_idx in range(n_colors_actual):
                color_name = f'color_{color_idx + 1}'
                true_hue = LABEL2HUE_DEG[color_name]
                true_rad = np.deg2rad(true_hue)
                trial_color = color_palette[color_idx]

                # True position (outer circle)
                ax.scatter([true_rad], [1.0], s=300, color='black',
                          edgecolor='white', linewidth=3, zorder=5)

                # Add color label
                ax.text(true_rad, 1.18, f'C{color_idx+1}',
                       ha='center', va='center', fontsize=11, fontweight='bold')

            # Summary statistics in center
            ax.text(0, 0, f"sub-{result['subject_id']}\n"
                          f"Error: {result['mean_error']:.1f}°\n"
                          f"Acc: {result['accuracy']*100:.1f}%\n"
                          f"n={result['n_runs']} runs",
                   ha='center', va='center', fontsize=12, fontweight='bold',
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.9, edgecolor='black', linewidth=2))

            # Legend
            ax.scatter([], [], s=300, color='black', edgecolor='white', linewidth=2,
                      label='True color')
            ax.scatter([], [], s=50, color='gray', edgecolor='white', linewidth=0.5,
                      label='Reconstructed')
            ax.plot([], [], color='gray', alpha=0.5, linewidth=1, label='Error')
            ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=10)

            ax.set_ylim([0, 1.25])
            ax.set_yticks([])
            ax.grid(True, alpha=0.3)
            ax.set_title(f'{roi}: HC Reconstruction (Common W)\nsub-{result["subject_id"]}',
                        fontsize=14, fontweight='bold', pad=20)

            plt.tight_layout()
            wheel_path = output_dir / f'hc_circular_wheel_sub-{result["subject_id"]}.png'
            plt.savefig(wheel_path, dpi=150, bbox_inches='tight')
            plt.close()

        print(f"  Saved {len(hc_reconstruction_results)} circular wheel plots")

    # ========================================================================
    # Step 7: Save model and results
    # ========================================================================
    print(f"\n[7/7] Saving model and results...")

    output_dir = Path(args.output_dir) / roi
    output_dir.mkdir(parents=True, exist_ok=True)

    model_data = {
        'hc_reference': hc_reference,
        'W_common': W_common,
        'basis_functions': basis_functions,
        'hc_subjects': hc_subjects,
        'roi': roi,
        'n_voxels': n_voxels,
        'hc_reconstruction_results': hc_reconstruction_results,  # NEW!
    }

    model_path = output_dir / 'procrustes_model.pkl'
    with open(model_path, 'wb') as f:
        pickle.dump(model_data, f)

    print(f"  Saved: {model_path}")

    np.save(output_dir / 'W_common.npy', W_common)
    np.save(output_dir / 'hc_reference.npy', hc_reference)

    print(f"  Saved: {output_dir / 'W_common.npy'}")
    print(f"  Saved: {output_dir / 'hc_reference.npy'}")

    # Save HC reconstruction results as CSV
    if len(hc_reconstruction_results) > 0:
        df = pd.DataFrame([
            {
                'subject_id': r['subject_id'],
                'mean_error_aligned': r['mean_error'],
                'mean_error_noalign': r['mean_error_noalign'],
                'accuracy_aligned': r['accuracy'],
                'accuracy_noalign': r['accuracy_noalign'],
                'alignment_benefit': r['mean_error_noalign'] - r['mean_error'],
                'n_runs': r['n_runs']
            }
            for r in hc_reconstruction_results
        ])
        csv_path = output_dir / 'hc_reconstruction_summary.csv'
        df.to_csv(csv_path, index=False)
        print(f"  Saved: {csv_path}")

        # Save detailed results
        results_path = output_dir / 'hc_reconstruction_detailed.pkl'
        with open(results_path, 'wb') as f:
            pickle.dump(hc_reconstruction_results, f)
        print(f"  Saved: {results_path}")

    print(f"\n{'='*70}")
    print(f"HC MODEL TRAINING COMPLETE!")
    print(f"{'='*70}")

    # Print final summary
    if len(hc_reconstruction_results) > 0:
        print(f"\nFinal Summary:")
        print(f"  HC subjects: {len(hc_reconstruction_results)}")
        print(f"  Mean error: {np.mean([r['mean_error'] for r in hc_reconstruction_results]):.1f}°")
        print(f"  Mean accuracy: {np.mean([r['accuracy'] for r in hc_reconstruction_results])*100:.1f}%")
        if np.mean([r['mean_error'] for r in hc_reconstruction_results]) < 90.0:
            print(f"  ✅ Ready to apply to CVD!")
        else:
            print(f"  ⚠️  WARNING: Common W quality may be insufficient")
    print()

# ============================================================================
# Mode 2: Test CVD
# ============================================================================

def test_cvd_subjects(args):
    print(f"\n{'='*70}")
    print(f"MODE 2: TEST CVD SUBJECTS (Procrustes)")
    print(f"{'='*70}\n")

    roi = args.roi
    cvd_subjects = args.cvd_subjects

    print(f"ROI: {roi}")
    print(f"CVD subjects: {cvd_subjects}")

    # Load model
    print(f"\n[1/3] Loading HC model...")

    if args.model_path is None:
        model_path = Path(args.output_dir) / roi / 'procrustes_model.pkl'
    else:
        model_path = Path(args.model_path)

    with open(model_path, 'rb') as f:
        model_data = pickle.load(f)

    hc_reference = model_data['hc_reference']
    W_common = model_data['W_common']
    basis_functions = model_data['basis_functions']

    print(f"  Loaded: {model_path}")
    print(f"  HC reference: {hc_reference.shape}")
    print(f"  W_common: {W_common.shape}")

    # Load CVD
    print(f"\n[2/3] Loading and aligning CVD subjects...")

    # Get HC reference voxel count
    n_voxels_hc = hc_reference.shape[1]
    print(f"  HC reference voxels: {n_voxels_hc}")

    cvd_results = []

    for sub_id in cvd_subjects:
        print(f"\n  sub-{sub_id}:")

        amp = load_subject_amplitudes(sub_id, roi, args.timestamp, args.dataset)
        n_runs, n_colors, n_voxels_cvd = amp.shape

        # Handle voxel count mismatch
        if n_voxels_cvd != n_voxels_hc:
            min_voxels = min(n_voxels_cvd, n_voxels_hc)
            print(f"    Voxel mismatch: CVD={n_voxels_cvd}, HC={n_voxels_hc}")
            print(f"    Using minimum: {min_voxels}")
            amp = amp[:, :, :min_voxels]
            hc_ref_truncated = hc_reference[:, :min_voxels]
            W_truncated = W_common[:min_voxels, :]  # (min_voxels, 6)
        else:
            hc_ref_truncated = hc_reference
            W_truncated = W_common

        # Align and reconstruct
        reconstruction_errors = []
        reconstruction_errors_noalign = []  # NEW: without alignment
        reconstructed_hues = []
        true_hues = []
        disparities = []  # Track disparities
        valid_runs = 0
        skipped_runs = 0

        for run_idx in range(n_runs):
            pattern = amp[run_idx]  # (n_colors, min_voxels)

            # Check if run has valid data
            pattern_var = np.var(pattern)
            if pattern_var < 1e-10:
                print(f"    Run {run_idx+1}: SKIPPED (zero variance)")
                skipped_runs += 1
                continue

            # Align to HC reference (both now have same voxel count)
            try:
                aligned, disparity = align_to_reference(pattern, hc_ref_truncated)
                disparities.append(disparity)
                print(f"    Run {run_idx+1}: disparity={disparity:.4f}")
            except ValueError as e:
                print(f"    Run {run_idx+1}: SKIPPED (alignment error: {e})")
                skipped_runs += 1
                continue

            # Reconstruct WITH alignment
            X_test_aligned = aligned  # (n_colors, min_voxels)

            # Estimate channels using truncated W
            C_est_aligned = np.linalg.pinv(W_truncated.T @ W_truncated) @ W_truncated.T @ X_test_aligned.T
            # C_est_aligned: (6, n_colors)

            # Also reconstruct WITHOUT alignment for comparison
            X_test_noalign = pattern  # (n_colors, min_voxels)
            C_est_noalign = np.linalg.pinv(W_truncated.T @ W_truncated) @ W_truncated.T @ X_test_noalign.T

            for color_idx in range(n_colors):
                # WITH alignment
                estimated_channels_aligned = C_est_aligned[:, color_idx]

                correlations_aligned = []
                for h in range(360):
                    template = basis_functions[h]
                    corr = np.corrcoef(estimated_channels_aligned, template)[0, 1]
                    correlations_aligned.append(corr)

                reconstructed_hue_aligned = np.argmax(correlations_aligned)

                color_name = f'color_{color_idx + 1}'
                true_hue = LABEL2HUE_DEG[color_name]

                error_aligned = circular_diff_deg(reconstructed_hue_aligned, true_hue)
                reconstruction_errors.append(error_aligned)

                # Store for visualization
                reconstructed_hues.append(reconstructed_hue_aligned)
                true_hues.append(true_hue)

                # WITHOUT alignment
                estimated_channels_noalign = C_est_noalign[:, color_idx]

                correlations_noalign = []
                for h in range(360):
                    template = basis_functions[h]
                    corr = np.corrcoef(estimated_channels_noalign, template)[0, 1]
                    correlations_noalign.append(corr)

                reconstructed_hue_noalign = np.argmax(correlations_noalign)
                error_noalign = circular_diff_deg(reconstructed_hue_noalign, true_hue)
                reconstruction_errors_noalign.append(error_noalign)

            valid_runs += 1

        if len(reconstruction_errors) == 0:
            print(f"    WARNING: No valid runs for sub-{sub_id}!")
            mean_error = np.nan
            mean_error_noalign = np.nan
            mean_disparity = np.nan
        else:
            mean_error = np.mean(reconstruction_errors)
            mean_error_noalign = np.mean(reconstruction_errors_noalign)
            mean_disparity = np.mean(disparities)

            print(f"    Valid runs: {valid_runs}/{n_runs}")
            print(f"    Mean disparity: {mean_disparity:.4f}")
            print(f"    Error (with alignment): {mean_error:.1f}°")
            print(f"    Error (without alignment): {mean_error_noalign:.1f}°")
            print(f"    Alignment benefit: {mean_error_noalign - mean_error:.1f}°")

        cvd_results.append({
            'subject_id': sub_id,
            'mean_error': mean_error,
            'mean_error_noalign': mean_error_noalign,
            'mean_disparity': mean_disparity,
            'all_errors': reconstruction_errors,
            'all_errors_noalign': reconstruction_errors_noalign,
            'reconstructed_hues': reconstructed_hues,
            'true_hues': true_hues,
            'valid_runs': valid_runs,
            'skipped_runs': skipped_runs,
        })

    # Save
    print(f"\n[3/3] Saving results and visualizations...")

    output_dir = Path(args.output_dir) / roi
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save CSV with comparison
    df_comparison = pd.DataFrame([
        {
            'subject_id': r['subject_id'],
            'mean_error_aligned': r['mean_error'],
            'mean_error_noalign': r['mean_error_noalign'],
            'mean_disparity': r['mean_disparity'],
            'alignment_benefit': r['mean_error_noalign'] - r['mean_error'],
        }
        for r in cvd_results
    ])

    csv_comparison_path = output_dir / 'cvd_reconstruction_comparison.csv'
    df_comparison.to_csv(csv_comparison_path, index=False)
    print(f"  Saved: {csv_comparison_path}")

    # Also save simple version (for backward compatibility)
    df_simple = pd.DataFrame([
        {'subject_id': r['subject_id'], 'mean_error': r['mean_error']}
        for r in cvd_results
    ])

    csv_simple_path = output_dir / 'cvd_reconstruction_errors.csv'
    df_simple.to_csv(csv_simple_path, index=False)
    print(f"  Saved: {csv_simple_path} (backward compatible)")

    # Create circular wheel visualizations for CVD
    print(f"  Creating circular color wheel plots...")

    for result in cvd_results:
        if len(result['all_errors']) == 0:
            continue  # Skip subjects with no valid data

        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw={'projection': 'polar'})
        ax.set_theta_zero_location("E")
        ax.set_theta_direction(1)

        # Get stored hues
        true_hues = result['true_hues']
        reconstructed_hues = result['reconstructed_hues']
        n_samples = len(true_hues)
        n_colors_actual = 8

        # Define colors for each color condition (8 colors)
        color_palette = plt.cm.hsv(np.linspace(0, 1, n_colors_actual + 1)[:n_colors_actual])

        # Plot each trial
        for sample_idx in range(n_samples):
            true_hue_deg = true_hues[sample_idx]
            recon_hue_deg = reconstructed_hues[sample_idx]

            true_rad = np.deg2rad(true_hue_deg)
            recon_rad = np.deg2rad(recon_hue_deg)

            # Determine which color this trial belongs to
            color_idx = sample_idx % n_colors_actual
            trial_color = color_palette[color_idx]

            # Draw connecting line (error)
            ax.plot([true_rad, recon_rad], [1.0, 0.7],
                   color=trial_color, alpha=0.3, linewidth=1, zorder=1)

            # Reconstructed position (inner circle)
            ax.scatter([recon_rad], [0.7], s=50, color=trial_color,
                      edgecolor='white', linewidth=0.5, alpha=0.6, zorder=3)

        # Draw true color positions (outer circle, larger)
        for color_idx in range(n_colors_actual):
            color_name = f'color_{color_idx + 1}'
            true_hue = LABEL2HUE_DEG[color_name]
            true_rad = np.deg2rad(true_hue)
            trial_color = color_palette[color_idx]

            # True position (outer circle)
            ax.scatter([true_rad], [1.0], s=300, color='black',
                      edgecolor='white', linewidth=3, zorder=5)

            # Add color label
            ax.text(true_rad, 1.18, f'C{color_idx+1}',
                   ha='center', va='center', fontsize=11, fontweight='bold')

        # Summary statistics in center
        ax.text(0, 0, f"CVD sub-{result['subject_id']}\n"
                      f"Error: {result['mean_error']:.1f}°\n"
                      f"n={result['valid_runs']} runs\n"
                      f"(HC Common W)",
               ha='center', va='center', fontsize=12, fontweight='bold',
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.9, edgecolor='black', linewidth=2))

        # Legend
        ax.scatter([], [], s=300, color='black', edgecolor='white', linewidth=2,
                  label='True color')
        ax.scatter([], [], s=50, color='gray', edgecolor='white', linewidth=0.5,
                  label='Reconstructed')
        ax.plot([], [], color='gray', alpha=0.5, linewidth=1, label='Error')
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=10)

        ax.set_ylim([0, 1.25])
        ax.set_yticks([])
        ax.grid(True, alpha=0.3)
        ax.set_title(f'{roi}: CVD Reconstruction (HC Common W)\nsub-{result["subject_id"]}',
                    fontsize=14, fontweight='bold', pad=20)

        plt.tight_layout()
        wheel_path = output_dir / f'cvd_circular_wheel_sub-{result["subject_id"]}.png'
        plt.savefig(wheel_path, dpi=150, bbox_inches='tight')
        plt.close()

    print(f"  Saved {len([r for r in cvd_results if len(r['all_errors']) > 0])} circular wheel plots")

    print(f"\n{'='*70}")
    print(f"CVD TESTING COMPLETE!")
    print(f"{'='*70}\n")

    print(f"\nSummary:")
    print(f"{'Subject':<10} {'Disparity':<12} {'Error (align)':<15} {'Error (no-align)':<18} {'Benefit':<10}")
    print(f"{'-'*70}")
    for r in cvd_results:
        if not np.isnan(r['mean_error']):
            print(f"sub-{r['subject_id']:<6} {r['mean_disparity']:>10.4f}  {r['mean_error']:>13.1f}°  {r['mean_error_noalign']:>16.1f}°  {r['mean_error_noalign'] - r['mean_error']:>8.1f}°")

    print(f"\n{'='*70}")
    print(f"KEY FINDING:")
    print(f"  If 'Benefit' is large → Alignment is essential")
    print(f"  If 'Benefit' is small → Alignment doesn't help much")
    print(f"    → Suggests CVD already has HC-like structure!")
    print(f"{'='*70}")

# ============================================================================
# Main
# ============================================================================

if __name__ == '__main__':
    args = parse_args()

    if args.mode == 'train':
        train_hc_model(args)
    elif args.mode == 'test':
        test_cvd_subjects(args)
