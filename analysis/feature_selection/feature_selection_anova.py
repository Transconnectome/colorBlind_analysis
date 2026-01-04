#!/usr/bin/env python3
"""
ANOVA F-test Feature Selection for Color Decoding
==================================================

이 스크립트는 ANOVA F-test를 사용하여 color discriminability가 높은 voxel을 선택합니다.

원리:
-----
각 voxel에 대해 F-statistic을 계산합니다:
    F = MSB / MSW
    MSB (Mean Square Between) = 색상 간 분산 (signal)
    MSW (Mean Square Within) = 색상 내 분산 (noise)

높은 F-value를 가진 voxel은 색상을 잘 구분하는 voxel입니다.

새로운 기능 (2025-11-29 추가):
--------------------------------
1. Significant voxel 개수 자동 계산 및 K_VALUES에 추가
2. Forward encoding model을 통한 reconstruction evaluation
3. Circular color space visualization (B&H 2009 style)
4. Selected voxels의 brain 위치 시각화
5. Selected voxels의 SNR 계산 및 출력

Input:
------
- Baseline preprocessing 결과
- Amplitudes: (n_runs, n_colors, n_voxels) Z-scored array

Output:
-------
- Selected voxel indices for each k
- F-values for all voxels
- Classification accuracy vs k
- Reconstruction error vs k
- Circular color space plots
- Brain visualization plots
- SNR statistics
- CSV: anova_results_sub-{ID}_{ROI}.csv

Author: Claude Code
Date: 2025-11-26
Updated: 2025-11-29 (added reconstruction, visualization, SNR)
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.model_selection import LeaveOneOut
from scipy.stats import zscore, f_oneway
import json
import sys
import argparse
import warnings
warnings.filterwarnings('ignore')

# Import common utilities for color decoding
from utils_color_decoding import (
    # Constants
    LABEL2HUE_DEG, COLOR_LAB, N_COLORS, N_RUNS,
    # Color space utilities
    circular_diff_deg, get_stimulus_color_rgb,
    # Forward encoding model
    create_basis_functions, diag_linear_predict, evaluate_reconstruction,
    evaluate_reconstruction_leave_one_color_out,
    # SNR calculation
    compute_voxel_snr,
    # Visualization
    visualize_circular_color_space, visualize_selected_voxels_brain,
    get_roi_mask_path
)

# ============================================================================
# Argument Parsing
# ============================================================================

def parse_args():
    """Command-line argument parser"""
    parser = argparse.ArgumentParser(description='ANOVA Feature Selection for Color Decoding')

    # Subject and ROI
    parser.add_argument('--subject', type=str, required=True,
                        help='Subject ID (01, 02, ..., 10)')
    parser.add_argument('--roi', type=str, required=True,
                        help='ROI name (V1, V2, V3, hV4)')
    parser.add_argument('--timestamp', type=str, required=True,
                        help='Baseline timestamp (e.g., baseline32_deob, baseline81_deob_prob)')
    parser.add_argument('--dataset', type=str, default='deoblique_v2',
                        help='Dataset name (default: deoblique_v2)')
    parser.add_argument('--k_fixed', type=int, default=None,
                        help='Fixed k value (if provided, only this k will be used)')
    parser.add_argument('--output_subdir', type=str, default=None,
                        help='Output subdirectory (e.g., k5 for strict validation)')

    # Ridge regression arguments (NEW)
    parser.add_argument('--use_ridge', action='store_true',
                        help='Use Ridge regression instead of OLS (default: False)')
    parser.add_argument('--alpha', type=float, default=10.0,
                        help='Ridge regularization parameter (default: 10.0)')

    # ROI-specific parameters (NEW 2025-12-15)
    parser.add_argument('--roi_specific', action='store_true',
                        help='Use ROI-specific k and alpha values')

    # Visualization parameters
    parser.add_argument('--compact', action='store_true',
                        help='Use compact circular plot (smaller figure size)')

    return parser.parse_args()

# Parse arguments
args = parse_args()

SUBJECT = args.subject
ROI = args.roi
TIMESTAMP = args.timestamp
DATASET = args.dataset

# ============================================================================
# Configuration
# ============================================================================

print(f"================================================================")
print(f"ANOVA Feature Selection for Color Decoding")
print(f"Subject: sub-{SUBJECT}, ROI: {ROI}")
print(f"Dataset: {DATASET}")
print(f"Baseline Timestamp: {TIMESTAMP}")
print(f"================================================================")

# Feature selection parameters
K_VALUES = [50, 100, 200, 500, 1000, 2000]  # Initial k values to test

# ============================================================================
# ROI-Specific Parameters (NEW 2025-12-15)
# ============================================================================

def get_roi_specific_params(roi, n_significant):
    """
    Get ROI-specific k values and alpha based on voxel availability

    Strategy (based on empirical analysis):
    - V1, V2: k=5 (keep original), alpha=20 (stronger regularization)
    - V3: k=2-3 (reduce to avoid noise), alpha=2 (weak regularization)
    - hV4: k=3-5 (reduce to avoid noise), alpha=5 (weak regularization)

    Args:
        roi: ROI name (V1, V2, V3, hV4)
        n_significant: Number of significant voxels (p<0.05)

    Returns:
        k_values: List of k values to test
        default_k: Default k if --k_fixed not provided
        alpha: Ridge regularization parameter
    """
    if roi in ['V1', 'V2']:
        # V1, V2: Sufficient significant voxels (18-28 on average)
        # Increase k to utilize more color-selective voxels
        k_values = [10]  # Increased from k=5 to k=10
        default_k = 10
        alpha = 20.0  # Stronger regularization to prevent overfitting

    elif roi == 'V3':
        # V3: Very few significant voxels (~3.6 on average)
        # Reduce k to avoid noise voxels, use weak Ridge
        k_values = [1, 2, 3, min(n_significant, 5)]
        default_k = min(n_significant, 3)  # Usually 2-3
        alpha = 2.0  # Weak regularization (preserve weak signal)

    elif roi == 'hV4':
        # hV4: Few significant voxels (~4.8 on average)
        # Reduce k to avoid noise voxels, use weak Ridge
        k_values = [2, 3, 4, 5, min(n_significant, 7)]
        default_k = min(n_significant, 5)  # Usually 3-5
        alpha = 5.0  # Weak regularization (preserve weak signal)

    else:
        # Unknown ROI: use conservative defaults
        print(f"  ⚠️  Unknown ROI: {roi}, using conservative defaults")
        k_values = [5]
        default_k = 5
        alpha = 10.0

    return k_values, default_k, alpha

# ============================================================================
# Helper Functions
# ============================================================================

def parse_timestamp_to_config_name(timestamp):
    """
    Timestamp를 config 이름과 ROI type으로 변환

    Args:
        timestamp: e.g., 'baseline32_deob', 'baseline32_deob_probability',
                        'baseline81_deob', 'baseline81_deob_probability',
                        'baseline32_origin_determin', 'baseline32_origin_probability',
                        'baseline81_deob_determin_permuted_red_green_primary'

    Returns:
        config_name: e.g., 'config32_determin', 'config32_probability',
                          'config81_determin', 'config81_probability',
                          'config32_origin_determin', 'config32_origin_probability',
                          'config81_determin_permuted_red_green_primary'
    """
    # Extract config number (32 or 81)
    if 'baseline32' in timestamp:
        config_num = 'config32'
    elif 'baseline81' in timestamp:
        config_num = 'config81'
    else:
        config_num = 'unknown'

    # Check for origin dataset
    if 'origin' in timestamp:
        config_num += '_origin'

    # Extract ROI type (probability vs deterministic)
    if 'probability' in timestamp:
        roi_type = 'probability'
    else:
        roi_type = 'determin'

    config_name = f"{config_num}_{roi_type}"

    # Check for permutation scenario (NEW)
    if 'permuted_' in timestamp:
        # Extract scenario name after 'permuted_'
        scenario_part = timestamp.split('permuted_')[1]
        config_name = f"{config_name}_permuted_{scenario_part}"

    return config_name


def load_baseline_amplitudes(subject, roi, timestamp, dataset='deoblique_v2'):
    """
    Baseline preprocessing 결과에서 amplitude 데이터 로드

    Args:
        subject: Subject ID (e.g., '01')
        roi: ROI name (e.g., 'V1')
        timestamp: Preprocessing timestamp (e.g., 'baseline32_deob')
        dataset: Dataset name (default: 'deoblique_v2')

    Returns:
        amplitudes_z: (n_runs, n_colors, n_voxels) Z-scored amplitudes
        n_runs, n_colors, n_voxels: Data dimensions
        result_dir: Path to baseline result directory
    """
    import glob

    # Find baseline result directory (pattern: sm*_sub-{subject}_{roi}_*)
    base_path = Path(f'derivatives/BH2009_{dataset}/{timestamp}')
    pattern = str(base_path / f'sm*_sub-{subject}_{roi}_*')

    matches = glob.glob(pattern)

    if len(matches) == 0:
        raise FileNotFoundError(
            f"Baseline result not found!\n"
            f"  Pattern: {pattern}\n"
            f"  Please run baseline preprocessing first:\n"
            f"    Dataset: {dataset}\n"
            f"    Timestamp: {timestamp}\n"
            f"    Subject: {subject}, ROI: {roi}"
        )

    # CRITICAL FIX: Filter by directories that contain amplitudes_z.npy
    # Some baseline directories (gmTrue) may be empty, only keep valid ones
    valid_matches = [m for m in matches if Path(m).joinpath('amplitudes_z.npy').exists()]

    if not valid_matches:
        raise FileNotFoundError(
            f"No valid baseline results with amplitudes_z.npy found!\n"
            f"  Subject: {subject}, ROI: {roi}\n"
            f"  Pattern: {pattern}\n"
            f"  Found {len(matches)} directories but none contain amplitudes_z.npy"
        )

    # PRIORITY 1: Prefer directories ending with '_None' (auto-detected roi_config)
    none_matches = [m for m in valid_matches if m.endswith('_None')]

    # PRIORITY 2: Prefer directory with analysis_summary.json (indicates complete analysis)
    summary_matches = [m for m in valid_matches if Path(m).joinpath('analysis_summary.json').exists()]

    if len(none_matches) > 0:
        # Sort by modification time (most recent first) and pick the latest
        none_matches_sorted = sorted(none_matches, key=lambda x: Path(x).stat().st_mtime, reverse=True)
        result_dir = Path(none_matches_sorted[0])
        print(f"  Using latest auto-detected baseline: {result_dir.name}")
    elif len(summary_matches) > 0:
        result_dir = Path(summary_matches[0])
    else:
        # Use first valid match (has amplitudes_z.npy)
        result_dir = Path(valid_matches[0])

    amplitudes_path = result_dir / 'amplitudes_z.npy'

    amplitudes_z = np.load(amplitudes_path)
    n_runs, n_colors, n_voxels = amplitudes_z.shape

    print(f"  ✓ Loaded amplitudes: {amplitudes_z.shape}")
    print(f"    Path: {amplitudes_path}")

    return amplitudes_z, n_runs, n_colors, n_voxels, str(result_dir)


def compute_anova_f_statistic(amplitudes_z):
    """
    ANOVA F-statistic 계산 (각 voxel의 color discriminability)

    F-statistic이 높을수록 해당 voxel이 색상을 잘 구분함

    Args:
        amplitudes_z: (n_runs, n_colors, n_voxels) Z-scored amplitudes

    Returns:
        f_values: (n_voxels,) F-statistics for each voxel
        p_values: (n_voxels,) P-values for each voxel
    """
    n_runs, n_colors, n_voxels = amplitudes_z.shape

    # Reshape for sklearn: (n_samples, n_features)
    X = amplitudes_z.reshape(-1, n_voxels)  # (n_runs * n_colors, n_voxels)
    y = np.tile(np.arange(n_colors), n_runs)  # (n_runs * n_colors,)

    # Compute F-statistic using sklearn
    f_values, p_values = f_classif(X, y)

    return f_values, p_values


def select_top_k_voxels(f_values, k):
    """
    F-value 기준 상위 k개 voxel 선택

    Args:
        f_values: (n_voxels,) F-statistics
        k: Number of voxels to select

    Returns:
        selected_indices: (k,) Indices of selected voxels
    """
    sorted_indices = np.argsort(f_values)[::-1]  # Descending order
    selected_indices = sorted_indices[:k]
    return selected_indices


def classify_with_lda(X_train, y_train, X_test, y_test):
    """
    Diagonal LDA로 classification accuracy 계산

    Args:
        X_train: (n_train_samples, n_features) Training data
        y_train: (n_train_samples,) Training labels
        X_test: (n_test_samples, n_features) Test data
        y_test: (n_test_samples,) Test labels

    Returns:
        accuracy: Classification accuracy (0-1)
    """
    clf = LinearDiscriminantAnalysis(solver='lsqr', shrinkage='auto')
    clf.fit(X_train, y_train)
    accuracy = clf.score(X_test, y_test)
    return accuracy


def evaluate_feature_selection(amplitudes_z, f_values, k_values):
    """
    각 k에 대해 feature selection + classification + reconstruction 수행

    주요 변경사항:
    - Significant voxel 개수를 k_values에 자동 추가
    - 각 k에 대해 reconstruction도 수행
    - Try-catch로 에러 방지

    Args:
        amplitudes_z: (n_runs, n_colors, n_voxels) Amplitudes
        f_values: (n_voxels,) F-statistics
        k_values: List of k values to test

    Returns:
        results_df: DataFrame with [k, fold, accuracy, reconstruction_error]
    """
    n_runs, n_colors, n_voxels = amplitudes_z.shape

    results = []

    for k in k_values:
        # ============================================================
        # FIX: Skip k values that exceed available voxels
        # ============================================================
        # 문제: Some ROIs (e.g., V3, hV4) have fewer voxels than k=200 or k=500
        # 해결: k > n_voxels인 경우 skip하여 reshape error 방지
        # ============================================================
        if k > n_voxels:
            print(f"\n  ⚠️  Skipping k={k} (exceeds n_voxels={n_voxels})")
            continue

        print(f"\n  Testing k={k} voxels...")

        # Select top k voxels
        selected_indices = select_top_k_voxels(f_values, k)
        k_actual = len(selected_indices)

        # Safety check
        if k_actual == 0:
            print(f"    ⚠️  Skipping k={k}: No valid voxels selected (all F-values may be NaN/Inf)")
            continue

        if k_actual < k:
            print(f"    ⚠️  Warning: Only {k_actual} voxels available (requested {k})")
            k = k_actual

        # Extract selected voxels
        amplitudes_selected = amplitudes_z[:, :, selected_indices]  # (n_runs, n_colors, k)

        # Additional safety check for empty selection
        if amplitudes_selected.size == 0:
            print(f"    ⚠️  Skipping k={k}: Selected amplitudes is empty")
            continue

        # ========================================
        # Leave-one-run-out cross-validation
        # ========================================
        fold_accuracies = []

        for test_run in range(n_runs):
            # Split train/test
            train_runs = [r for r in range(n_runs) if r != test_run]

            X_train = amplitudes_selected[train_runs].reshape(-1, k)
            y_train = np.tile(np.arange(n_colors), len(train_runs))

            X_test = amplitudes_selected[test_run].reshape(-1, k)
            y_test = np.arange(n_colors)

            # Classify
            acc = classify_with_lda(X_train, y_train, X_test, y_test)
            fold_accuracies.append(acc)

            results.append({
                'k': k,
                'fold': test_run + 1,
                'accuracy': acc,
                'method': 'classification'
            })

        mean_acc = np.mean(fold_accuracies)
        std_acc = np.std(fold_accuracies)
        print(f"    Classification: {mean_acc:.1%} ± {std_acc:.1%}")

        # ========================================
        # Reconstruction evaluation (NEW)
        # ========================================
        try:
            # Pass alpha parameter for Ridge regression
            alpha_value = args.alpha if args.use_ridge else 0.0
            recon_results, mean_recon_error, per_color_stats = evaluate_reconstruction(
                amplitudes_selected,
                alpha=alpha_value
            )

            for recon_res in recon_results:
                results.append({
                    'k': k,
                    'fold': recon_res['test_run'],
                    'reconstruction_error': recon_res['mean_error'],
                    'hit_rate_22_5': recon_res['hit_rate_22_5'],
                    'hit_rate_45': recon_res['hit_rate_45'],
                    'method': 'reconstruction'
                })

                # Store trial-level reconstruction data (each color in each fold)
                reconstructed_hues = recon_res['reconstructed_hues']
                true_hues = recon_res['true_hues']
                errors = recon_res['errors']

                for color_idx in range(len(true_hues)):
                    color_name = f'color_{color_idx+1}'
                    results.append({
                        'k': k,
                        'fold': recon_res['test_run'],
                        'color': color_name,
                        'true_hue': true_hues[color_idx],
                        'reconstructed_hue': reconstructed_hues[color_idx],
                        'reconstruction_error': errors[color_idx],
                        'method': 'reconstruction_trial'
                    })

            # Also store per-color stats with true_hue
            for color_name, stats in per_color_stats.items():
                # Extract true_hue from LABEL2HUE_DEG
                color_idx = int(color_name.split('_')[1]) - 1
                true_hue = LABEL2HUE_DEG[color_name]

                results.append({
                    'k': k,
                    'color': color_name,
                    'true_hue': true_hue,
                    'mean_error': stats['mean_error'],
                    'std_error': stats['std_error'],
                    'hit_rate_22_5': stats['hit_rate_22_5'],
                    'hit_rate_45': stats['hit_rate_45'],
                    'method': 'per_color_stats'
                })

            print(f"    Reconstruction (one-run-out): {mean_recon_error:.1f}° error")

        except Exception as e:
            print(f"    ⚠️  Reconstruction (one-run-out) failed for k={k}: {e}")
            # Continue without reconstruction for this k

        # ========================================
        # One-color-out reconstruction (NEW)
        # ========================================
        try:
            # Pass alpha parameter for Ridge regression
            alpha_value = args.alpha if args.use_ridge else 0.0
            loco_results, loco_mean_error, loco_per_color = evaluate_reconstruction_leave_one_color_out(
                amplitudes_selected,
                alpha=alpha_value
            )

            for loco_res in loco_results:
                results.append({
                    'k': k,
                    'test_color': loco_res['test_color'],
                    'reconstruction_error': loco_res['mean_error'],
                    'std_error': loco_res['std_error'],
                    'hit_rate_22_5': loco_res['hit_rate_22_5'],
                    'hit_rate_45': loco_res['hit_rate_45'],
                    'method': 'loco_reconstruction'
                })

            print(f"    Reconstruction (one-color-out): {loco_mean_error:.1f}° error")

        except Exception as e:
            print(f"    ⚠️  Reconstruction (one-color-out) failed for k={k}: {e}")

    results_df = pd.DataFrame(results)
    return results_df


def visualize_results(results_df, f_values, p_values, output_dir, config_name, subject, roi):
    """
    결과 시각화:
    1. F-value distribution
    2. Classification accuracy vs k
    3. Reconstruction error vs k (NEW)

    Args:
        results_df: DataFrame with results
        f_values: (n_voxels,) F-values
        p_values: (n_voxels,) P-values
        output_dir: Output directory
        config_name: Config name (e.g., 'config32_nonprob')
        subject: Subject ID
        roi: ROI name
    """
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    # ========================================
    # Plot 1: F-value distribution
    # ========================================
    ax = axes[0]

    n_significant = np.sum(p_values < 0.05)
    n_voxels = len(f_values)

    ax.hist(f_values, bins=50, alpha=0.7, edgecolor='black')
    ax.axvline(np.median(f_values), color='red', linestyle='--', linewidth=2,
               label=f'Median: {np.median(f_values):.2f}')
    ax.set_xlabel('F-value', fontsize=12)
    ax.set_ylabel('Number of Voxels', fontsize=12)
    ax.set_title(f'F-value Distribution\nSignificant: {n_significant}/{n_voxels} (p<0.05)',
                 fontsize=12, fontweight='bold')
    ax.legend()
    ax.grid(alpha=0.3)

    # ========================================
    # Plot 2: Classification accuracy vs k
    # ========================================
    ax = axes[1]

    class_data = results_df[results_df['method'] == 'classification']
    if len(class_data) > 0:
        summary = class_data.groupby('k')['accuracy'].agg(['mean', 'std']).reset_index()

        ax.errorbar(summary['k'], summary['mean'] * 100, yerr=summary['std'] * 100,
                    marker='o', markersize=8, linewidth=2, capsize=5, capthick=2,
                    label='ANOVA + LDA')

        ax.axhline(100/N_COLORS, color='gray', linestyle='--', linewidth=1,
                   label=f'Chance ({100/N_COLORS:.1f}%)')

        ax.set_xlabel('Number of Selected Voxels (k)', fontsize=12)
        ax.set_ylabel('Classification Accuracy (%)', fontsize=12)
        ax.set_title('Classification Performance vs k',
                     fontsize=12, fontweight='bold')
        ax.set_xscale('log')
        ax.grid(alpha=0.3)
        ax.legend()

        # Annotate best k
        best_k = summary.loc[summary['mean'].idxmax(), 'k']
        best_acc = summary.loc[summary['mean'].idxmax(), 'mean']
        ax.annotate(f'Best: k={int(best_k)}\n{best_acc:.1%}',
                    xy=(best_k, best_acc * 100),
                    xytext=(best_k * 0.5, best_acc * 100 + 3),
                    arrowprops=dict(arrowstyle='->', lw=2),
                    fontsize=10, fontweight='bold')

    # ========================================
    # Plot 3: Reconstruction error vs k (NEW)
    # ========================================
    ax = axes[2]

    recon_data = results_df[results_df['method'] == 'reconstruction']
    if len(recon_data) > 0:
        summary = recon_data.groupby('k')['reconstruction_error'].agg(['mean', 'std']).reset_index()

        ax.errorbar(summary['k'], summary['mean'], yerr=summary['std'],
                    marker='s', markersize=8, linewidth=2, capsize=5, capthick=2,
                    color='green', label='ANOVA + Forward Model')

        ax.axhline(90, color='gray', linestyle='--', linewidth=1,
                   label='Chance (90°)')

        ax.set_xlabel('Number of Selected Voxels (k)', fontsize=12)
        ax.set_ylabel('Reconstruction Error (degrees)', fontsize=12)
        ax.set_title('Reconstruction Performance vs k',
                     fontsize=12, fontweight='bold')
        ax.set_xscale('log')
        ax.grid(alpha=0.3)
        ax.legend()

        # Annotate best k
        best_k = summary.loc[summary['mean'].idxmin(), 'k']
        best_err = summary.loc[summary['mean'].idxmin(), 'mean']
        ax.annotate(f'Best: k={int(best_k)}\n{best_err:.1f}°',
                    xy=(best_k, best_err),
                    xytext=(best_k * 0.5, best_err + 10),
                    arrowprops=dict(arrowstyle='->', lw=2),
                    fontsize=10, fontweight='bold')

    plt.tight_layout()

    fig_path = output_dir / f'anova_feature_selection_{config_name}_sub-{subject}_{roi}.png'
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    print(f"\n✓ Figure saved: {fig_path}")

    plt.close()


# ============================================================================
# Main Analysis
# ============================================================================

def main():
    print("="*80)
    print("ANOVA F-test Feature Selection Analysis")
    print("="*80)
    print(f"Subject: {SUBJECT}")
    print(f"ROI: {ROI}")
    print(f"Timestamp: {TIMESTAMP}")
    print(f"Dataset: {DATASET}")

    # Generate config name from timestamp
    CONFIG_NAME = parse_timestamp_to_config_name(TIMESTAMP)
    print(f"Config: {CONFIG_NAME}")
    print()

    # ========================================
    # Step 1: Load baseline amplitudes
    # ========================================
    print("[Step 1/7] Loading baseline amplitudes...")
    amplitudes_z, n_runs, n_colors, n_voxels, result_dir = load_baseline_amplitudes(
        SUBJECT, ROI, TIMESTAMP, DATASET
    )
    print(f"  Amplitudes shape: {amplitudes_z.shape}")
    print(f"  n_runs={n_runs}, n_colors={n_colors}, n_voxels={n_voxels}")

    # ========================================
    # Step 2: Compute ANOVA F-statistics
    # ========================================
    print("\n[Step 2/7] Computing ANOVA F-statistics...")
    f_values, p_values = compute_anova_f_statistic(amplitudes_z)
    print(f"  F-values shape: {f_values.shape}")
    print(f"  F-value range: [{np.min(f_values):.2f}, {np.max(f_values):.2f}]")
    print(f"  F-value mean: {np.mean(f_values):.2f} ± {np.std(f_values):.2f}")
    print(f"  F-value median: {np.median(f_values):.2f}")

    # Count significant voxels (p < 0.05)
    n_significant = np.sum(p_values < 0.05)
    print(f"  Significant voxels (p<0.05): {n_significant}/{n_voxels} ({100*n_significant/n_voxels:.1f}%)")

    # ========================================
    # Step 3: Adjust K_VALUES with significant voxels (or use fixed k)
    # ========================================
    print(f"\n[Step 3/7] Determining K values and alpha...")

    # Get ROI-specific parameters if requested
    if args.roi_specific:
        roi_k_values, roi_default_k, roi_alpha = get_roi_specific_params(ROI, n_significant)
        print(f"  Using ROI-specific parameters for {ROI}:")
        print(f"    K values: {roi_k_values}")
        print(f"    Default k: {roi_default_k}")
        print(f"    Alpha: {roi_alpha}")

        # Override alpha if using Ridge
        if args.use_ridge:
            args.alpha = roi_alpha
            print(f"  ✓ Ridge alpha set to {roi_alpha} (ROI-specific)")

        # Use ROI-specific k values (unless --k_fixed provided)
        if args.k_fixed is not None:
            print(f"  ⚠️  --k_fixed={args.k_fixed} overrides ROI-specific k")
            if args.k_fixed > n_voxels:
                print(f"  ⚠️  WARNING: k_fixed ({args.k_fixed}) > n_voxels ({n_voxels})")
                print(f"  → Adjusting to k={n_voxels}")
                k_values_final = [n_voxels]
            else:
                k_values_final = [args.k_fixed]
        else:
            # Use ROI-specific k values, filtered by n_voxels
            k_values_final = [k for k in roi_k_values if k <= n_voxels]
            print(f"  Final K_VALUES (ROI-specific, ≤ n_voxels): {k_values_final}")

    elif args.k_fixed is not None:
        # Use fixed k value only (non-ROI-specific mode)
        print(f"  Using fixed k={args.k_fixed} (from --k_fixed)")
        if args.k_fixed > n_voxels:
            print(f"  ⚠️  WARNING: k_fixed ({args.k_fixed}) > n_voxels ({n_voxels})")
            print(f"  → Adjusting to k={n_voxels}")
            k_values_final = [n_voxels]
        else:
            k_values_final = [args.k_fixed]
    else:
        # Auto-adjust K_VALUES with significant voxels (default mode)
        print(f"  Original K_VALUES: {K_VALUES}")

        # Add n_significant to K_VALUES
        k_values_adjusted = sorted(list(set(K_VALUES + [n_significant])))

        # Remove k values exceeding n_voxels
        k_values_final = [k for k in k_values_adjusted if k <= n_voxels]

        print(f"  After adding n_significant ({n_significant}): {k_values_adjusted}")
        print(f"  Final K_VALUES (≤ n_voxels): {k_values_final}")

    # Print Ridge status
    if args.use_ridge:
        print(f"  Ridge regression: ENABLED (alpha={args.alpha})")
    else:
        print(f"  Ridge regression: DISABLED (OLS)")

    # ========================================
    # Step 4: Evaluate feature selection
    # ========================================
    print(f"\n[Step 4/7] Evaluating feature selection with classification & reconstruction...")
    results_df = evaluate_feature_selection(amplitudes_z, f_values, k_values_final)

    # ========================================
    # Step 5: Compute SNR for selected voxels
    # ========================================
    print(f"\n[Step 5/7] Computing SNR for all voxels...")
    voxel_snr = compute_voxel_snr(amplitudes_z)
    print(f"  SNR range: [{np.min(voxel_snr):.2f}, {np.max(voxel_snr):.2f}]")
    print(f"  SNR mean: {np.mean(voxel_snr):.2f} ± {np.std(voxel_snr):.2f}")
    print(f"  SNR median: {np.median(voxel_snr):.2f}")

    # For each k, show SNR of selected voxels
    print(f"\n  SNR of selected voxels for each k:")
    for k in k_values_final:
        if k <= n_voxels:
            selected_indices = select_top_k_voxels(f_values, k)
            selected_snr = voxel_snr[selected_indices]
            print(f"    k={k:4d}: SNR = {np.mean(selected_snr):.2f} ± {np.std(selected_snr):.2f}")

    # ========================================
    # Step 6: Save results
    # ========================================
    print(f"\n[Step 6/7] Saving results...")

    # Determine output directory
    # For permutation analysis workflow, save everything to permutation_analysis subdirectory
    # This is controlled by an environment variable or config name check
    if 'permuted' in CONFIG_NAME or args.timestamp.startswith('baseline32_deob_determin'):
        # Save to permutation_analysis for consistency in permutation workflow
        if args.output_subdir:
            # Use custom subdirectory (e.g., 'k5' for strict validation)
            output_dir = Path(f'derivatives/feature_selection/permutation_analysis/{args.output_subdir}/anova_{CONFIG_NAME}')
        else:
            # Default permutation_analysis directory
            output_dir = Path(f'derivatives/feature_selection/permutation_analysis/anova_{CONFIG_NAME}')
    else:
        # Regular analysis (not part of permutation workflow)
        output_dir = Path(f'derivatives/feature_selection/anova_{CONFIG_NAME}')
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save classification & reconstruction results
    csv_path = output_dir / f'anova_results_{CONFIG_NAME}_sub-{SUBJECT}_{ROI}.csv'
    results_df.to_csv(csv_path, index=False)
    print(f"  ✓ Results saved: {csv_path}")

    # Save F-values and SNR for all voxels
    voxel_stats_df = pd.DataFrame({
        'voxel_idx': np.arange(n_voxels),
        'f_value': f_values,
        'p_value': p_values,
        'snr': voxel_snr,
        'rank': np.argsort(np.argsort(f_values)[::-1])  # Rank (0=best)
    })
    stats_path = output_dir / f'anova_voxel_stats_{CONFIG_NAME}_sub-{SUBJECT}_{ROI}.csv'
    voxel_stats_df.to_csv(stats_path, index=False)
    print(f"  ✓ Voxel statistics saved: {stats_path}")

    # ========================================
    # Step 7: Visualizations
    # ========================================
    print(f"\n[Step 7/7] Creating visualizations...")

    # Main results plot
    visualize_results(results_df, f_values, p_values, output_dir, CONFIG_NAME, SUBJECT, ROI)

    # Get best k for reconstruction (lowest error)
    recon_data = results_df[results_df['method'] == 'reconstruction']
    if len(recon_data) > 0:
        summary = recon_data.groupby('k')['reconstruction_error'].mean()
        best_k = summary.idxmin()  # Minimize reconstruction error
        print(f"\n  Creating detailed visualizations for best k={best_k} (reconstruction-based)...")
    else:
        # Fallback to classification if no reconstruction data
        class_data = results_df[results_df['method'] == 'classification']
        if len(class_data) > 0:
            summary = class_data.groupby('k')['accuracy'].mean()
            best_k = summary.idxmax()
            print(f"\n  Creating detailed visualizations for best k={best_k} (classification-based fallback)...")
        else:
            print("\n  ⚠️  No data available for visualization")
            best_k = None

    if best_k is not None:

        # Select voxels for best k
        selected_indices = select_top_k_voxels(f_values, best_k)
        amplitudes_selected = amplitudes_z[:, :, selected_indices]

        # Reconstruction for visualization
        try:
            # Pass alpha parameter for Ridge regression
            alpha_value = args.alpha if args.use_ridge else 0.0
            recon_results, mean_error, per_color_stats = evaluate_reconstruction(
                amplitudes_selected,  # Removed selected_indices - goes to **kwargs
                alpha=alpha_value
            )

            # Circular color space plot (include CONFIG_NAME for unique filenames)
            visualize_circular_color_space(
                recon_results, mean_error, 'ANOVA', best_k,
                ROI, SUBJECT, output_dir, per_color_stats=per_color_stats,
                config_suffix=CONFIG_NAME, compact=args.compact
            )

        except Exception as e:
            print(f"    ⚠️  Circular visualization failed: {e}")

        # Brain visualization
        try:
            roi_mask_path = get_roi_mask_path(SUBJECT, ROI, TIMESTAMP)
            visualize_selected_voxels_brain(
                selected_indices, roi_mask_path, f_values,
                'ANOVA', best_k, ROI, SUBJECT, output_dir,
                config_suffix=CONFIG_NAME
            )
        except Exception as e:
            print(f"    ⚠️  Brain visualization failed: {e}")

    # ========================================
    # Summary
    # ========================================
    print("\n" + "="*80)
    print("ANOVA Feature Selection Complete!")
    print("="*80)

    # Best classification k
    class_data = results_df[results_df['method'] == 'classification']
    if len(class_data) > 0:
        summary = class_data.groupby('k')['accuracy'].mean()
        best_k_class = summary.idxmax()
        best_acc = summary.max()

        print(f"\nBest Classification:")
        print(f"  k = {best_k_class} voxels")
        print(f"  Accuracy = {best_acc:.1%}")

    # Best reconstruction k
    recon_data = results_df[results_df['method'] == 'reconstruction']
    if len(recon_data) > 0:
        summary = recon_data.groupby('k')['reconstruction_error'].mean()
        best_k_recon = summary.idxmin()
        best_err = summary.min()

        print(f"\nBest Reconstruction:")
        print(f"  k = {best_k_recon} voxels")
        print(f"  Error = {best_err:.1f}°")

    print(f"\nSignificant voxels (p<0.05): {n_significant}")
    print(f"Tested k values: {k_values_final}")

    print(f"\nOutput files:")
    print(f"  - {csv_path}")
    print(f"  - {stats_path}")
    print(f"  - {output_dir / f'anova_feature_selection_{CONFIG_NAME}_sub-{SUBJECT}_{ROI}.png'}")
    print()


if __name__ == '__main__':
    main()
