#!/usr/bin/env python3
"""
PCA Feature Selection for Color Decoding
=========================================

이 스크립트는 PCA를 사용하여 voxel 간 공유된 정보를 압축하고 색상 구분 성능을 평가합니다.

원리:
-----
PCA는 voxel 간 상관관계를 활용하여 차원을 축소합니다:
1. 모든 voxel의 공분산 행렬 계산
2. 주성분(Principal Components) 추출
3. 상위 k개 성분으로 데이터 변환
4. 변환된 성분으로 classification 및 reconstruction 수행

ANOVA/RFE와의 차이:
- ANOVA: Univariate (각 voxel 독립적 평가)
- RFE: Multivariate (중요한 voxel subset 선택)
- PCA: Multivariate (voxel 간 공유 정보 압축)

장점:
- Voxel 간 redundancy 제거
- Noise reduction via dimensionality reduction
- 적은 feature로 높은 설명력

단점:
- Interpretability 낮음 (voxel → component 변환)
- Overfitting 위험 (training set에서만 PCA fit)

CRITICAL (CLAUDE.md):
---------------------
- amplitudes_z.npy는 이미 z-scored되어 있음 (per run-voxel across 8 colors)
- PCA는 각 fold의 training set에서만 fit하고, test set에 transform 적용
- 중복 정규화 방지: StandardScaler 사용 금지

Input:
------
- Baseline preprocessing 결과
- Amplitudes: (n_runs, n_colors, n_voxels) Z-scored array

Output:
-------
- PCA components for each n_components
- Classification accuracy vs n_components
- Reconstruction error vs n_components
- Explained variance ratio
- Component loadings (top voxels per component)
- Circular color space visualization
- CSV: pca_results_sub-{ID}_{ROI}.csv

Author: Claude Code
Date: 2025-12-01
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.decomposition import PCA
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
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
    parser = argparse.ArgumentParser(description='PCA Feature Selection for Color Decoding')

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
print(f"PCA Feature Selection for Color Decoding")
print(f"Subject: sub-{SUBJECT}, ROI: {ROI}")
print(f"Dataset: {DATASET}")
print(f"Baseline Timestamp: {TIMESTAMP}")
print(f"================================================================")

# Feature selection parameters
N_COMPONENTS_VALUES = [5, 10, 20, 50, 100, 200]  # Number of PCA components to test
N_COLORS = 8
N_RUNS = 6

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

# Paths
BASE_DIR = Path('/scratch/connectome/haba6030/colorBlind')
OUTPUT_DIR = BASE_DIR / 'derivatives' / 'feature_selection' / f'pca_{CONFIG_NAME}'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print(f"Config: {CONFIG_NAME}")
print(f"Output directory: {OUTPUT_DIR}")

# ============================================================================
# Load Data
# ============================================================================

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

    print(f"\n[1/5] Loaded amplitudes:")
    print(f"  Shape: {amplitudes_z.shape} (runs × colors × voxels)")
    print(f"  Path: {amplitudes_path}")
    print(f"  Already z-scored: YES (per run-voxel across colors)")

    return amplitudes_z, str(result_dir)

# ============================================================================
# PCA Feature Selection
# ============================================================================

def classify_with_lda(X_train, y_train, X_test, y_test):
    """
    Diagonal LDA classification (wrapper for diag_linear_predict)

    Args:
        X_train: (n_train, n_features)
        y_train: (n_train,)
        X_test: (n_test, n_features)
        y_test: (n_test,)

    Returns:
        accuracy: float
    """
    y_pred = diag_linear_predict(X_train, y_train, X_test)
    accuracy = np.mean(y_pred == y_test)
    return accuracy


def evaluate_pca(amplitudes_z, n_components_values):
    """
    PCA feature selection with leave-one-run-out cross-validation

    CRITICAL: PCA는 각 fold의 training set에서만 fit하고, test set에 적용

    Args:
        amplitudes_z: (n_runs, n_colors, n_voxels) Z-scored amplitudes
        n_components_values: List of n_components to test

    Returns:
        results_df: DataFrame with results
        pca_models: Dict of fitted PCA models (for visualization)
    """
    n_runs, n_colors, n_voxels = amplitudes_z.shape

    print(f"\n[2/5] Running PCA feature selection...")
    print(f"  n_components to test: {n_components_values}")
    print(f"  Cross-validation: Leave-one-run-out (6-fold)")

    # Calculate max possible n_components for leave-one-run-out CV
    # Training set size: (n_runs - 1) * n_colors
    n_train_samples = (n_runs - 1) * n_colors  # 5 runs × 8 colors = 40
    max_n_components = min(n_train_samples, n_voxels)

    print(f"  Training set size per fold: {n_train_samples} samples")
    print(f"  Max n_components: {max_n_components} (min of {n_train_samples} samples, {n_voxels} voxels)")

    # Filter n_components > max_n_components
    n_components_values = [n for n in n_components_values if n <= max_n_components]
    print(f"  Valid n_components (≤ {max_n_components}): {n_components_values}")

    if len(n_components_values) == 0:
        raise ValueError(f"No valid n_components values! Max allowed is {max_n_components}")

    results = []
    pca_models = {}  # Store PCA models for later visualization

    for n_comp in n_components_values:
        print(f"\n  Testing n_components = {n_comp}...")

        fold_accuracies = []
        fold_explained_var = []

        # ========================================
        # Classification with leave-one-run-out CV
        # ========================================
        for test_run in range(n_runs):
            # Split train/test
            train_runs = [r for r in range(n_runs) if r != test_run]

            X_train_raw = amplitudes_z[train_runs].reshape(-1, n_voxels)  # (40, n_voxels)
            y_train = np.tile(np.arange(n_colors), len(train_runs))

            X_test_raw = amplitudes_z[test_run].reshape(-1, n_voxels)  # (8, n_voxels)
            y_test = np.arange(n_colors)

            # Fit PCA on training set ONLY
            pca = PCA(n_components=n_comp)
            pca.fit(X_train_raw)

            # Transform both train and test
            X_train = pca.transform(X_train_raw)  # (40, n_comp)
            X_test = pca.transform(X_test_raw)    # (8, n_comp)

            # Classify
            acc = classify_with_lda(X_train, y_train, X_test, y_test)
            fold_accuracies.append(acc)

            # Store explained variance
            fold_explained_var.append(pca.explained_variance_ratio_.sum())

            # Store first fold's PCA model for visualization
            if test_run == 0:
                pca_models[n_comp] = pca

            results.append({
                'n_components': n_comp,
                'fold': test_run + 1,
                'accuracy': acc,
                'explained_variance': pca.explained_variance_ratio_.sum(),
                'method': 'classification'
            })

        mean_acc = np.mean(fold_accuracies)
        std_acc = np.std(fold_accuracies)
        mean_var = np.mean(fold_explained_var)

        print(f"    Classification: {mean_acc:.1%} ± {std_acc:.1%}")
        print(f"    Explained variance: {mean_var:.1%}")

        # ========================================
        # Reconstruction evaluation
        # ========================================
        # Use first fold's PCA transformation for reconstruction
        try:
            pca = pca_models[n_comp]

            # Transform all data with the first fold's PCA
            amplitudes_pca = np.zeros((n_runs, n_colors, n_comp))
            for run in range(n_runs):
                X_run = amplitudes_z[run].reshape(n_colors, n_voxels)  # (8, n_voxels)
                amplitudes_pca[run] = pca.transform(X_run)  # (8, n_comp)

            # Evaluate reconstruction
            recon_results, mean_recon_error, per_color_stats = evaluate_reconstruction(
                amplitudes_pca
            )

            # Calculate mean hit rates across folds
            mean_hit_rate_22_5 = np.mean([r['hit_rate_22_5'] for r in recon_results])
            mean_hit_rate_45 = np.mean([r['hit_rate_45'] for r in recon_results])

            for recon_res in recon_results:
                results.append({
                    'n_components': n_comp,
                    'fold': recon_res['test_run'],
                    'reconstruction_error': recon_res['mean_error'],
                    'hit_rate_22_5': recon_res['hit_rate_22_5'],
                    'hit_rate_45': recon_res['hit_rate_45'],
                    'method': 'reconstruction'
                })

            print(f"    Reconstruction: {mean_recon_error:.1f}° error, Hit@22.5°: {mean_hit_rate_22_5:.1%}, Hit@45°: {mean_hit_rate_45:.1%}")

        except Exception as e:
            print(f"    ⚠️  Reconstruction failed for n_components={n_comp}: {e}")

    results_df = pd.DataFrame(results)
    return results_df, pca_models


# ============================================================================
# Visualization
# ============================================================================

def visualize_results(results_df, pca_models, amplitudes_z, output_dir):
    """
    결과 시각화:
    1. Explained variance vs n_components
    2. Classification accuracy vs n_components
    3. Reconstruction error vs n_components
    4. Component loadings (top components)

    Args:
        results_df: DataFrame with results
        pca_models: Dict of fitted PCA models
        amplitudes_z: (n_runs, n_colors, n_voxels) Original amplitudes
        output_dir: Output directory
    """
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # ========================================
    # Plot 1: Explained variance vs n_components
    # ========================================
    ax = axes[0, 0]

    var_data = results_df[results_df['method'] == 'classification'].groupby('n_components')['explained_variance'].agg(['mean', 'std']).reset_index()

    ax.errorbar(var_data['n_components'], var_data['mean'] * 100, yerr=var_data['std'] * 100,
                marker='o', markersize=8, linewidth=2, capsize=5, capthick=2,
                color='steelblue', label='Explained Variance')

    ax.set_xlabel('Number of Components', fontsize=12)
    ax.set_ylabel('Explained Variance (%)', fontsize=12)
    ax.set_title('PCA Explained Variance', fontsize=12, fontweight='bold')
    ax.grid(alpha=0.3)
    ax.legend()

    # ========================================
    # Plot 2: Classification accuracy vs n_components
    # ========================================
    ax = axes[0, 1]

    class_data = results_df[results_df['method'] == 'classification']
    summary = class_data.groupby('n_components')['accuracy'].agg(['mean', 'std']).reset_index()

    ax.errorbar(summary['n_components'], summary['mean'] * 100, yerr=summary['std'] * 100,
                marker='o', markersize=8, linewidth=2, capsize=5, capthick=2,
                label='PCA + LDA')

    ax.axhline(100/N_COLORS, color='gray', linestyle='--', linewidth=1,
               label=f'Chance ({100/N_COLORS:.1f}%)')

    # Mark best performance
    best_idx = summary['mean'].idxmax()
    best_n = summary.loc[best_idx, 'n_components']
    best_acc = summary.loc[best_idx, 'mean']
    ax.scatter([best_n], [best_acc * 100], s=200, color='red', marker='*', zorder=5,
               label=f'Best: n={int(best_n)}, {best_acc:.1%}')

    ax.set_xlabel('Number of Components', fontsize=12)
    ax.set_ylabel('Classification Accuracy (%)', fontsize=12)
    ax.set_title('PCA Classification Performance', fontsize=12, fontweight='bold')
    ax.legend()
    ax.grid(alpha=0.3)

    # ========================================
    # Plot 3: Reconstruction error vs n_components
    # ========================================
    ax = axes[1, 0]

    recon_data = results_df[results_df['method'] == 'reconstruction']
    if len(recon_data) > 0:
        summary_recon = recon_data.groupby('n_components')['reconstruction_error'].agg(['mean', 'std']).reset_index()

        ax.errorbar(summary_recon['n_components'], summary_recon['mean'], yerr=summary_recon['std'],
                    marker='s', markersize=8, linewidth=2, capsize=5, capthick=2,
                    color='orange', label='PCA Reconstruction')

        # Mark best (lowest error)
        best_idx = summary_recon['mean'].idxmin()
        best_n = summary_recon.loc[best_idx, 'n_components']
        best_err = summary_recon.loc[best_idx, 'mean']
        ax.scatter([best_n], [best_err], s=200, color='red', marker='*', zorder=5,
                   label=f'Best: n={int(best_n)}, {best_err:.1f}°')

        ax.set_xlabel('Number of Components', fontsize=12)
        ax.set_ylabel('Reconstruction Error (degrees)', fontsize=12)
        ax.set_title('PCA Reconstruction Performance', fontsize=12, fontweight='bold')
        ax.legend()
        ax.grid(alpha=0.3)
    else:
        ax.text(0.5, 0.5, 'No reconstruction data', ha='center', va='center',
                transform=ax.transAxes, fontsize=14)
        ax.set_title('Reconstruction Error (Failed)', fontsize=12, fontweight='bold')

    # ========================================
    # Plot 4: Component loadings heatmap (top 3 components)
    # ========================================
    ax = axes[1, 1]

    # Use the model with most components
    max_n_comp = max(pca_models.keys())
    pca = pca_models[max_n_comp]

    # Get top 3 components
    n_comp_to_show = min(3, max_n_comp)
    components = pca.components_[:n_comp_to_show]  # (3, n_voxels)

    # Show loadings heatmap
    im = ax.imshow(components, aspect='auto', cmap='RdBu_r', vmin=-0.2, vmax=0.2)
    ax.set_xlabel('Voxel Index', fontsize=12)
    ax.set_ylabel('Component', fontsize=12)
    ax.set_title(f'Top {n_comp_to_show} Component Loadings\n(n_components={max_n_comp})',
                 fontsize=12, fontweight='bold')
    ax.set_yticks(range(n_comp_to_show))
    ax.set_yticklabels([f'PC{i+1}' for i in range(n_comp_to_show)])

    plt.colorbar(im, ax=ax, label='Loading Weight')

    plt.tight_layout()
    fig_path = output_dir / f'pca_feature_selection_{CONFIG_NAME}_sub-{SUBJECT}_{ROI}.png'
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    print(f"\n  Saved figure: {fig_path}")
    plt.close()


# ============================================================================
# Main Execution
# ============================================================================

def main():
    """Main execution pipeline"""

    # Load data
    amplitudes_z, result_dir = load_baseline_amplitudes(SUBJECT, ROI, TIMESTAMP, DATASET)
    n_runs, n_colors, n_voxels = amplitudes_z.shape

    # Compute SNR for all voxels (for reference)
    print(f"\n[3/5] Computing voxel SNR...")
    snr_all = compute_voxel_snr(amplitudes_z)
    print(f"  Mean SNR (all voxels): {snr_all.mean():.2f} ± {snr_all.std():.2f}")

    # PCA feature selection
    results_df, pca_models = evaluate_pca(amplitudes_z, N_COMPONENTS_VALUES)

    # Save results
    print(f"\n[4/5] Saving results...")
    csv_path = OUTPUT_DIR / f'pca_results_{CONFIG_NAME}_sub-{SUBJECT}_{ROI}.csv'
    results_df.to_csv(csv_path, index=False)
    print(f"  Saved CSV: {csv_path}")

    # Visualization
    print(f"\n[5/5] Creating visualizations...")
    visualize_results(results_df, pca_models, amplitudes_z, OUTPUT_DIR)

    # Summary
    print(f"\n" + "="*64)
    print(f"PCA Feature Selection Complete!")
    print(f"="*64)

    # Best classification
    class_data = results_df[results_df['method'] == 'classification']
    summary = class_data.groupby('n_components')['accuracy'].mean()
    best_n_comp = summary.idxmax()
    best_acc = summary.max()

    print(f"\n🏆 Best Classification:")
    print(f"  n_components: {int(best_n_comp)}")
    print(f"  Accuracy: {best_acc:.1%}")

    # Best reconstruction
    recon_data = results_df[results_df['method'] == 'reconstruction']
    if len(recon_data) > 0:
        summary_recon = recon_data.groupby('n_components')['reconstruction_error'].mean()
        summary_hit_22_5 = recon_data.groupby('n_components')['hit_rate_22_5'].mean()
        summary_hit_45 = recon_data.groupby('n_components')['hit_rate_45'].mean()
        best_n_recon = summary_recon.idxmin()
        best_err = summary_recon.min()
        best_hit_22_5 = summary_hit_22_5.loc[best_n_recon]
        best_hit_45 = summary_hit_45.loc[best_n_recon]

        print(f"\n🏆 Best Reconstruction:")
        print(f"  n_components: {int(best_n_recon)}")
        print(f"  Error: {best_err:.1f}°")
        print(f"  Hit Rate @22.5°: {best_hit_22_5:.1%}")
        print(f"  Hit Rate @45°: {best_hit_45:.1%}")

    print(f"\n✓ All outputs saved to: {OUTPUT_DIR}")
    print(f"="*64)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
