#!/usr/bin/env python3
"""
Recursive Feature Elimination (RFE) for Color Decoding
=======================================================

이 스크립트는 RFE를 사용하여 multivariate color discriminability가 높은 voxel을 선택합니다.

원리:
-----
1. 모든 voxel로 classifier (Linear SVM) 학습
2. Classifier weight 절댓값 기준으로 voxel 중요도 계산
3. 가장 중요도가 낮은 voxel 제거
4. k개 voxel이 남을 때까지 반복

ANOVA와의 차이:
- ANOVA: Univariate (각 voxel 독립적으로 평가)
- RFE: Multivariate (voxel 간 상호작용 고려)

장점: Voxel redundancy 제거, multivariate pattern 포착
단점: 계산 비용 높음, overfitting 위험

Input:
------
- Baseline preprocessing 결과
- Amplitudes: (n_runs, n_colors, n_voxels) array

Output:
-------
- Selected voxel indices for each k
- Classification accuracy vs k
- Reconstruction error vs k
- SNR for selected voxels
- Brain visualization of selected voxels
- Circular color space visualization
- CSV: feature_selection_rfe_results.csv

Author: Claude Code
Date: 2025-11-29 (Rewritten using utils_color_decoding.py)
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.feature_selection import RFE
from sklearn.svm import LinearSVC
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from scipy.stats import f as f_dist
import json
import sys
import time
import argparse

# Import common utilities
from utils_color_decoding import (
    LABEL2HUE_DEG, COLOR_LAB,
    evaluate_reconstruction,
    compute_voxel_snr,
    visualize_circular_color_space,
    visualize_selected_voxels_brain,
    get_roi_mask_path
)

# ============================================================================
# Argument Parsing
# ============================================================================

def parse_args():
    """Command-line argument parser for RFE feature selection"""
    parser = argparse.ArgumentParser(description='RFE Feature Selection for Color Decoding')

    # Subject and ROI
    parser.add_argument('--subject', type=str, required=True,
                        help='Subject ID (01, 02, ..., 10)')
    parser.add_argument('--roi', type=str, required=True,
                        help='ROI name (V1, V2, V3, hV4)')
    parser.add_argument('--timestamp', type=str, required=True,
                        help='Baseline timestamp (e.g., baseline32_deob, baseline81_deob_prob)')
    parser.add_argument('--dataset', type=str, default='deoblique_v2',
                        help='Dataset name (default: deoblique_v2)')

    return parser.parse_args()

# ============================================================================
# Configuration
# ============================================================================

# Parse command-line arguments
args = parse_args()

SUBJECT = args.subject
ROI = args.roi
TIMESTAMP = args.timestamp
DATASET = args.dataset

# Parse timestamp to config name
def parse_timestamp_to_config_name(timestamp):
    """
    Timestamp를 config 이름과 ROI type으로 변환

    Args:
        timestamp: e.g., 'baseline32_deob', 'baseline32_deob_probability',
                        'baseline81_deob', 'baseline81_deob_probability',
                        'baseline32_origin_determin', 'baseline32_origin_probability'

    Returns:
        config_name: e.g., 'config32_determin', 'config32_probability',
                          'config81_determin', 'config81_probability',
                          'config32_origin_determin', 'config32_origin_probability'
    """
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

    return f"{config_num}_{roi_type}"

CONFIG_NAME = parse_timestamp_to_config_name(TIMESTAMP)

# RFE parameters
K_VALUES = [50, 100, 200, 500]  # Target number of features
# Note: RFE is slow, so we test fewer k values than ANOVA

# RFE algorithm parameters
STEP = 50  # Number of features to remove per iteration
# Smaller step = more accurate but slower
# Larger step = faster but may skip optimal subset

# SVM parameters (base estimator for RFE)
SVM_C = 1.0  # Regularization parameter
# Higher C = less regularization = more complex boundary

# Cross-validation
N_RUNS = 6  # Leave-one-run-out CV

# ============================================================================
# Helper Functions
# ============================================================================

def load_baseline_amplitudes(subject, roi, timestamp, dataset='deoblique_v2'):
    """
    Baseline preprocessing 결과에서 amplitude 데이터 로드

    Args:
        subject: Subject ID (e.g., '01')
        roi: ROI name (e.g., 'V1')
        timestamp: Baseline timestamp (e.g., 'baseline32_deob', 'baseline81_deob_prob')
        dataset: Dataset name (default: 'deoblique_v2')

    Returns:
        amplitudes_z: (n_runs, n_colors, n_voxels) Z-scored amplitudes
        n_runs, n_colors, n_voxels: Data dimensions
        result_dir: Path to the baseline result directory
    """
    import glob

    # Find baseline result directory
    base_path = Path(f'derivatives/BH2009_{dataset}/{timestamp}')
    pattern = str(base_path / f'sm*_sub-{subject}_{roi}_*')
    matches = glob.glob(pattern)

    if not matches:
        raise FileNotFoundError(
            f"No baseline results found for:\n"
            f"  Subject: {subject}\n"
            f"  ROI: {roi}\n"
            f"  Timestamp: {timestamp}\n"
            f"  Dataset: {dataset}\n"
            f"  Pattern: {pattern}\n"
            f"Please ensure baseline preprocessing has been completed."
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

    # PRIORITY 2: Prefer directories with analysis_summary.json (indicates complete analysis)
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

    print(f"  Loading from: {result_dir.name}")

    # Load amplitudes_z.npy
    amplitudes_path = result_dir / 'amplitudes_z.npy'

    amplitudes_z = np.load(amplitudes_path)
    n_runs, n_colors, n_voxels = amplitudes_z.shape

    print(f"  ✓ Loaded amplitudes: {amplitudes_z.shape}")
    print(f"    n_runs={n_runs}, n_colors={n_colors}, n_voxels={n_voxels}")

    return amplitudes_z, n_runs, n_colors, n_voxels, str(result_dir)


def run_rfe_selection(X, y, k, step, C):
    """
    RFE를 사용하여 상위 k개 feature 선택

    Args:
        X: (n_samples, n_features) Feature matrix
        y: (n_samples,) Labels
        k: Number of features to select
        step: Number of features to remove per iteration
        C: SVM regularization parameter

    Returns:
        selected_indices: (k,) Indices of selected features
        ranking: (n_features,) Feature ranking (1=best)
    """
    # Base estimator: Linear SVM
    # LinearSVC is faster than SVC(kernel='linear')
    estimator = LinearSVC(C=C, max_iter=10000, random_state=42)

    # RFE selector
    selector = RFE(
        estimator=estimator,
        n_features_to_select=k,
        step=step,
        verbose=0
    )

    # Fit RFE
    selector.fit(X, y)

    # Get selected feature indices
    selected_indices = np.where(selector.support_)[0]

    # Get feature ranking (1=best, 2=second best, etc.)
    ranking = selector.ranking_

    return selected_indices, ranking


def classify_with_lda(X_train, y_train, X_test, y_test):
    """
    Diagonal LDA로 classification accuracy 계산

    Args:
        X_train, y_train: Training data and labels
        X_test, y_test: Test data and labels

    Returns:
        accuracy: Classification accuracy (0-1)
    """
    clf = LinearDiscriminantAnalysis(solver='lsqr', shrinkage='auto')
    clf.fit(X_train, y_train)
    accuracy = clf.score(X_test, y_test)

    return accuracy


def evaluate_feature_selection(amplitudes_z, selected_indices, k):
    """
    선택된 voxel에 대해 classification + reconstruction 평가

    Args:
        amplitudes_z: (n_runs, n_colors, n_voxels) Full amplitudes
        selected_indices: (k,) Selected voxel indices
        k: Number of selected voxels

    Returns:
        results: List of dicts with [k, fold, accuracy, reconstruction_error, method]
    """
    n_runs, n_colors, _ = amplitudes_z.shape

    # Safety check: ensure selected_indices is not empty
    if len(selected_indices) == 0:
        raise ValueError(f"No voxels selected (k={k}). Cannot proceed with empty selection.")

    # Extract selected voxels
    amplitudes_selected = amplitudes_z[:, :, selected_indices]  # (n_runs, n_colors, k)

    # Additional safety check
    if amplitudes_selected.size == 0:
        raise ValueError(f"Selected amplitudes is empty (k={k}, indices={len(selected_indices)})")

    results = []

    # ========================================
    # Classification with leave-one-run-out CV
    # ========================================
    for test_run in range(n_runs):
        # Split train/test
        train_runs = [r for r in range(n_runs) if r != test_run]

        X_train = amplitudes_selected[train_runs].reshape(-1, k)
        y_train = np.tile(np.arange(n_colors), len(train_runs))

        X_test = amplitudes_selected[test_run].reshape(-1, k)
        y_test = np.arange(n_colors)

        # Classify
        acc = classify_with_lda(X_train, y_train, X_test, y_test)

        results.append({
            'k': k,
            'fold': test_run + 1,
            'accuracy': acc,
            'method': 'classification'
        })

    # ========================================
    # Reconstruction evaluation
    # ========================================
    try:
        # Note: amplitudes_selected is already z-scored (from amplitudes_z.npy)
        # evaluate_reconstruction handles the forward encoding model internally
        recon_results, mean_recon_error = evaluate_reconstruction(
            amplitudes_selected,
            selected_indices=selected_indices,
            label2hue_deg=LABEL2HUE_DEG
        )

        # Add reconstruction results to output
        for recon_res in recon_results:
            results.append({
                'k': k,
                'fold': recon_res['test_run'],
                'reconstruction_error': recon_res['mean_error'],
                'method': 'reconstruction'
            })

        print(f"    Reconstruction error: {mean_recon_error:.1f}° (mean across folds)")

    except Exception as e:
        print(f"    ⚠️  Reconstruction failed for k={k}: {e}")
        # Continue without reconstruction results

    return results


def evaluate_rfe(amplitudes_z, k_values, step, C, output_dir):
    """
    각 k에 대해 RFE feature selection + classification + reconstruction 수행

    Args:
        amplitudes_z: (n_runs, n_colors, n_voxels) Amplitudes
        k_values: List of k values to test
        step: RFE step size
        C: SVM C parameter
        output_dir: Output directory for visualizations

    Returns:
        results_df: DataFrame with results
        rankings_dict: Dict {k: ranking array}
        selections_dict: Dict {k: selected_indices}
    """
    n_runs, n_colors, n_voxels = amplitudes_z.shape

    # Reshape for sklearn: (n_samples, n_features)
    X_all = amplitudes_z.reshape(-1, n_voxels)  # (48, n_voxels)
    y_all = np.tile(np.arange(n_colors), n_runs)  # (48,)

    # ============================================================
    # Step 1: Compute p-values for significant voxel threshold
    # ============================================================
    # Even though RFE is multivariate, we compute univariate p-values
    # to automatically add n_significant to k_values
    # This ensures we test all significant voxels even if few exist
    # ============================================================
    print("\n  Computing univariate p-values to find significant voxels...")

    # Compute F-statistic per voxel
    group_means = []
    for color in range(n_colors):
        color_data = amplitudes_z[:, color, :]  # (n_runs, n_voxels)
        group_means.append(color_data.mean(axis=0))  # (n_voxels,)
    group_means = np.array(group_means)  # (n_colors, n_voxels)

    # Between-group variance
    grand_mean = group_means.mean(axis=0)  # (n_voxels,)
    ssb = n_runs * np.sum((group_means - grand_mean)**2, axis=0)  # (n_voxels,)
    msb = ssb / (n_colors - 1)

    # Within-group variance
    # For each color, compute deviation from its mean across all runs
    ssw = np.zeros(n_voxels)
    for color in range(n_colors):
        color_data = amplitudes_z[:, color, :]  # (n_runs, n_voxels)
        color_mean = group_means[color]  # (n_voxels,)
        ssw += np.sum((color_data - color_mean)**2, axis=0)  # (n_voxels,)
    msw = ssw / (n_runs * n_colors - n_colors)

    # F-statistic
    f_values = msb / (msw + 1e-10)

    # P-values
    dfn = n_colors - 1  # Between-group df
    dfd = n_runs * n_colors - n_colors  # Within-group df
    p_values = 1 - f_dist.cdf(f_values, dfn, dfd)

    n_significant = np.sum(p_values < 0.05)
    print(f"  ✓ Significant voxels (p < 0.05): {n_significant}/{n_voxels}")

    # ============================================================
    # Step 2: Adjust K_VALUES with significant voxel count
    # ============================================================
    # Add n_significant to k_values to ensure we test it
    # Filter out k > n_voxels or k <= 0 to prevent errors
    # ============================================================
    k_values_adjusted = sorted(list(set(k_values + [n_significant])))
    k_values_final = [k for k in k_values_adjusted if 0 < k <= n_voxels]

    if len(k_values_final) < len(k_values_adjusted):
        print(f"\n  ⚠️  Some k values are invalid (k<=0 or k>n_voxels={n_voxels}), removing:")
        removed_k = [k for k in k_values_adjusted if k <= 0 or k > n_voxels]
        print(f"      Removed: {removed_k}")

    if not k_values_final:
        print(f"\n  ⚠️  WARNING: No valid k values to test!")
        print(f"    n_voxels={n_voxels}, n_significant={n_significant}")
        print(f"    Original k_values: {k_values}")
        print(f"    Skipping RFE for this ROI (insufficient voxels)")
        # Return empty results
        return pd.DataFrame(), {}, {}

    print(f"  Testing k values: {k_values_final}")

    # ============================================================
    # Step 3: RFE feature selection and evaluation
    # ============================================================
    results = []
    rankings_dict = {}
    selections_dict = {}

    for k in k_values_final:
        if k > n_voxels:
            print(f"\n  ⚠️  Skipping k={k} (exceeds n_voxels={n_voxels})")
            continue

        print(f"\n  Testing k={k} voxels...")
        print(f"    RFE parameters: step={step}, C={C}")

        # ========================================
        # RFE feature selection (on all data)
        # ========================================
        start_time = time.time()

        selected_indices, ranking = run_rfe_selection(X_all, y_all, k, step, C)
        rankings_dict[k] = ranking
        selections_dict[k] = selected_indices

        rfe_time = time.time() - start_time
        print(f"    RFE completed in {rfe_time:.1f}s")
        print(f"    Selected voxel indices (first 10): {selected_indices[:10]}")

        # Safety check
        k_actual = len(selected_indices)

        if k_actual == 0:
            print(f"    ⚠️  Skipping k={k}: RFE returned 0 features")
            continue

        if k_actual != k:
            print(f"    ⚠️  Warning: RFE returned {k_actual} features (expected {k})")
            k = k_actual

        # ========================================
        # Evaluate with classification + reconstruction
        # ========================================
        try:
            fold_results = evaluate_feature_selection(amplitudes_z, selected_indices, k)
        except ValueError as e:
            print(f"    ⚠️  Evaluation failed for k={k}: {e}")
            continue
        results.extend(fold_results)

        # Compute mean classification accuracy
        classification_results = [r for r in fold_results if r['method'] == 'classification']
        mean_acc = np.mean([r['accuracy'] for r in classification_results])
        std_acc = np.std([r['accuracy'] for r in classification_results])
        print(f"    Mean accuracy: {mean_acc:.1%} ± {std_acc:.1%}")

        # ========================================
        # Compute SNR for selected voxels
        # ========================================
        amplitudes_selected = amplitudes_z[:, :, selected_indices]
        snr_values = compute_voxel_snr(amplitudes_selected)
        mean_snr = np.mean(snr_values)
        median_snr = np.median(snr_values)
        print(f"    SNR (selected voxels): mean={mean_snr:.2f}, median={median_snr:.2f}")

        # ========================================
        # Visualize circular color space for this k
        # ========================================
        try:
            recon_results = [r for r in fold_results if r['method'] == 'reconstruction']
            if recon_results:
                # Convert to format expected by visualization function
                recon_results_formatted = []
                for r in recon_results:
                    recon_results_formatted.append({
                        'test_run': r['fold'],
                        'mean_error': r['reconstruction_error']
                    })

                # Need to re-run reconstruction to get detailed results for visualization
                # This is already done in evaluate_feature_selection, but we need the full output
                recon_full, mean_error = evaluate_reconstruction(
                    amplitudes_selected,
                    selected_indices=selected_indices,
                    label2hue_deg=LABEL2HUE_DEG
                )

                visualize_circular_color_space(
                    recon_full,
                    mean_error,
                    method_name='RFE',
                    k=k,
                    roi=ROI,
                    subject=SUBJECT,
                    output_dir=output_dir
                )
                print(f"    ✓ Circular color space visualization saved")

        except Exception as e:
            print(f"    ⚠️  Circular visualization failed: {e}")

    results_df = pd.DataFrame(results)
    return results_df, rankings_dict, selections_dict


def visualize_results(results_df, rankings_dict, n_voxels, output_dir):
    """
    결과 시각화:
    1. Classification accuracy vs k
    2. Reconstruction error vs k
    3. Voxel ranking distribution (for best k)

    Args:
        results_df: DataFrame with results
        rankings_dict: Dict {k: ranking array}
        n_voxels: Total number of voxels
        output_dir: Output directory path
    """
    fig, axes = plt.subplots(1, 3, figsize=(20, 5))

    # ========================================
    # Plot 1: Classification accuracy vs k
    # ========================================
    ax = axes[0]

    classification_df = results_df[results_df['method'] == 'classification']
    summary = classification_df.groupby('k')['accuracy'].agg(['mean', 'std']).reset_index()

    ax.errorbar(summary['k'], summary['mean'] * 100, yerr=summary['std'] * 100,
                marker='o', markersize=8, linewidth=2, capsize=5, capthick=2,
                label='RFE + LDA', color='blue')

    ax.set_xlabel('Number of Selected Voxels (k)', fontsize=12)
    ax.set_ylabel('Classification Accuracy (%)', fontsize=12)
    ax.set_title('RFE: Classification Performance vs k',
                 fontsize=12, fontweight='bold')
    ax.set_xscale('log')
    ax.grid(alpha=0.3)
    ax.legend()

    # Annotate best k
    if not summary.empty:
        best_k = summary.loc[summary['mean'].idxmax(), 'k']
        best_acc = summary.loc[summary['mean'].idxmax(), 'mean']
        ax.annotate(f'Best: k={int(best_k)}\n{best_acc:.1%}',
                    xy=(best_k, best_acc * 100),
                    xytext=(best_k * 0.5, best_acc * 100 + 3),
                    arrowprops=dict(arrowstyle='->', lw=2),
                    fontsize=10, fontweight='bold')

    # ========================================
    # Plot 2: Reconstruction error vs k
    # ========================================
    ax = axes[1]

    reconstruction_df = results_df[results_df['method'] == 'reconstruction']
    if not reconstruction_df.empty:
        recon_summary = reconstruction_df.groupby('k')['reconstruction_error'].agg(['mean', 'std']).reset_index()

        ax.errorbar(recon_summary['k'], recon_summary['mean'], yerr=recon_summary['std'],
                    marker='s', markersize=8, linewidth=2, capsize=5, capthick=2,
                    label='RFE Reconstruction', color='red')

        ax.set_xlabel('Number of Selected Voxels (k)', fontsize=12)
        ax.set_ylabel('Reconstruction Error (degrees)', fontsize=12)
        ax.set_title('RFE: Reconstruction Error vs k',
                     fontsize=12, fontweight='bold')
        ax.set_xscale('log')
        ax.grid(alpha=0.3)
        ax.legend()

        # Annotate best k
        best_k_recon = recon_summary.loc[recon_summary['mean'].idxmin(), 'k']
        best_error = recon_summary.loc[recon_summary['mean'].idxmin(), 'mean']
        ax.annotate(f'Best: k={int(best_k_recon)}\n{best_error:.1f}°',
                    xy=(best_k_recon, best_error),
                    xytext=(best_k_recon * 1.5, best_error + 5),
                    arrowprops=dict(arrowstyle='->', lw=2),
                    fontsize=10, fontweight='bold')
    else:
        ax.text(0.5, 0.5, 'No reconstruction data available',
                ha='center', va='center', transform=ax.transAxes, fontsize=12)

    # ========================================
    # Plot 3: Voxel ranking distribution (best k)
    # ========================================
    ax = axes[2]

    if not summary.empty:
        # Use ranking from best k (classification)
        best_k = summary.loc[summary['mean'].idxmax(), 'k']
        best_ranking = rankings_dict[best_k]

        # Histogram of rankings
        ax.hist(best_ranking, bins=50, alpha=0.7, edgecolor='black')
        ax.axvline(best_k, color='red', linestyle='--', linewidth=2,
                   label=f'Selected: rank ≤ {int(best_k)}')
        ax.axvline(n_voxels, color='gray', linestyle='--', linewidth=2,
                   label=f'Total voxels: {n_voxels}')

        ax.set_xlabel('Voxel Rank (1=best)', fontsize=12)
        ax.set_ylabel('Number of Voxels', fontsize=12)
        ax.set_title(f'Voxel Ranking Distribution\n(RFE with k={int(best_k)})',
                     fontsize=12, fontweight='bold')
        ax.legend()
        ax.grid(alpha=0.3)

    plt.tight_layout()

    # Save figure
    fig_path = output_dir / f'rfe_feature_selection_sub-{SUBJECT}_{ROI}.png'
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    print(f"\n✓ Figure saved: {fig_path}")

    plt.close()


# ============================================================================
# Main Analysis
# ============================================================================

def main():
    print("="*80)
    print("Recursive Feature Elimination (RFE) Analysis")
    print("="*80)
    print(f"Subject: {SUBJECT}")
    print(f"ROI: {ROI}")
    print(f"Timestamp: {TIMESTAMP}")
    print(f"Config: {CONFIG_NAME}")
    print(f"Dataset: {DATASET}")
    print(f"RFE step size: {STEP}")
    print(f"SVM C parameter: {SVM_C}")
    print()

    # ========================================
    # Step 1: Load baseline amplitudes
    # ========================================
    print("[1/7] Loading baseline amplitudes...")
    amplitudes_z, n_runs, n_colors, n_voxels, result_dir = load_baseline_amplitudes(
        SUBJECT, ROI, TIMESTAMP, DATASET
    )
    print(f"  Amplitudes shape: {amplitudes_z.shape}")
    print(f"  n_runs={n_runs}, n_colors={n_colors}, n_voxels={n_voxels}")

    # Create output directory
    output_dir = Path(f'derivatives/feature_selection/rfe_{CONFIG_NAME}')
    output_dir.mkdir(parents=True, exist_ok=True)

    # ========================================
    # Step 2: Run RFE evaluation
    # ========================================
    print("\n[2/7] Running RFE feature selection with classification + reconstruction...")
    print(f"  K values to test: {K_VALUES}")
    print(f"  ⚠️  This may take several minutes...")

    start_time = time.time()
    results_df, rankings_dict, selections_dict = evaluate_rfe(
        amplitudes_z, K_VALUES, STEP, SVM_C, output_dir
    )
    total_time = time.time() - start_time

    print(f"\n  Total computation time: {total_time:.1f}s ({total_time/60:.1f} min)")

    # ========================================
    # Check if results are empty (no valid k values)
    # ========================================
    if results_df.empty:
        print("\n⚠️  RFE analysis skipped: No valid k values for this ROI")
        print(f"  Subject: {SUBJECT}, ROI: {ROI}")
        print(f"  This may happen when n_voxels is very small or n_significant=0")
        print("\n✓ Analysis complete (no results generated)")
        return

    # ========================================
    # Step 3: Save results
    # ========================================
    print("\n[3/7] Saving results...")

    # Save classification + reconstruction results
    csv_path = output_dir / f'rfe_results_{CONFIG_NAME}_sub-{SUBJECT}_{ROI}.csv'
    results_df.to_csv(csv_path, index=False)
    print(f"  ✓ Results saved: {csv_path}")

    # Save rankings for each k
    for k, ranking in rankings_dict.items():
        ranking_df = pd.DataFrame({
            'voxel_idx': np.arange(n_voxels),
            'rank': ranking,
            'selected': ranking <= k
        })
        ranking_path = output_dir / f'rfe_rankings_{CONFIG_NAME}_k{k}_sub-{SUBJECT}_{ROI}.csv'
        ranking_df.to_csv(ranking_path, index=False)
        print(f"  ✓ Rankings (k={k}) saved: {ranking_path}")

    # ========================================
    # Step 4: Visualize accuracy/error vs k
    # ========================================
    print("\n[4/7] Creating accuracy/error visualizations...")
    visualize_results(results_df, rankings_dict, n_voxels, output_dir)

    # ========================================
    # Step 5: Compute SNR for best k
    # ========================================
    print("\n[5/7] Computing SNR for best k configuration...")

    # Find best k (lowest reconstruction error)
    reconstruction_df = results_df[results_df['method'] == 'reconstruction']
    if not reconstruction_df.empty:
        summary = reconstruction_df.groupby('k')['reconstruction_error'].mean()
        best_k = summary.idxmin()  # Minimize reconstruction error
        print(f"  Best k = {best_k} (lowest reconstruction error)")
    else:
        # Fallback to classification if no reconstruction data
        classification_df = results_df[results_df['method'] == 'classification']
        summary = classification_df.groupby('k')['accuracy'].mean()
        best_k = summary.idxmax()
        print(f"  Best k = {best_k} (highest classification accuracy - fallback)")

    # Compute SNR for best k
    selected_indices = selections_dict[best_k]
    amplitudes_selected = amplitudes_z[:, :, selected_indices]
    snr_values = compute_voxel_snr(amplitudes_selected)

    # Save SNR values
    snr_df = pd.DataFrame({
        'voxel_idx': selected_indices,
        'snr': snr_values
    })
    snr_path = output_dir / f'rfe_snr_{CONFIG_NAME}_k{best_k}_sub-{SUBJECT}_{ROI}.csv'
    snr_df.to_csv(snr_path, index=False)
    print(f"  ✓ SNR values saved: {snr_path}")

    # Summary stats
    print(f"  SNR statistics (k={best_k}):")
    print(f"    Mean: {np.mean(snr_values):.2f}")
    print(f"    Median: {np.median(snr_values):.2f}")
    print(f"    Min: {np.min(snr_values):.2f}")
    print(f"    Max: {np.max(snr_values):.2f}")

    # ========================================
    # Step 6: Visualize selected voxels in brain
    # ========================================
    print("\n[6/7] Creating brain visualization of selected voxels...")

    try:
        # Get ROI mask path
        roi_mask_path = get_roi_mask_path(SUBJECT, ROI)

        # Use ranking as feature values (lower rank = more important)
        # Invert so higher value = more important for visualization
        ranking = rankings_dict[best_k]
        feature_values = n_voxels - ranking[selected_indices] + 1

        visualize_selected_voxels_brain(
            selected_indices,
            roi_mask_path,
            feature_values,
            method_name='RFE',
            k=best_k,
            roi=ROI,
            subject=SUBJECT,
            output_dir=output_dir
        )
        print(f"  ✓ Brain visualization saved")

    except Exception as e:
        print(f"  ⚠️  Brain visualization failed: {e}")

    # ========================================
    # Step 7: Summary
    # ========================================
    print("\n[7/7] Analysis summary...")
    print("\n" + "="*80)
    print("RFE Analysis Complete!")
    print("="*80)

    # Best k
    best_acc = summary.max()

    print(f"\nBest Configuration:")
    print(f"  k = {best_k} voxels")
    print(f"  Classification accuracy = {best_acc:.1%}")

    # Reconstruction performance
    reconstruction_df = results_df[results_df['method'] == 'reconstruction']
    if not reconstruction_df.empty:
        recon_at_best_k = reconstruction_df[reconstruction_df['k'] == best_k]['reconstruction_error'].mean()
        print(f"  Reconstruction error = {recon_at_best_k:.1f}°")

    print(f"\nComputational Cost:")
    print(f"  Total time: {total_time:.1f}s ({total_time/60:.1f} min)")
    print(f"  Average per k: {total_time/len(K_VALUES):.1f}s")

    print(f"\nOutput files:")
    print(f"  - {csv_path}")
    for k in rankings_dict.keys():
        print(f"  - {output_dir / f'rfe_rankings_{CONFIG_NAME}_k{k}_sub-{SUBJECT}_{ROI}.csv'}")
    print(f"  - {output_dir / f'rfe_feature_selection_sub-{SUBJECT}_{ROI}.png'}")
    print(f"  - {snr_path}")
    print()


if __name__ == '__main__':
    main()
