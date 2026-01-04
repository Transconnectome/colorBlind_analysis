#!/usr/bin/env python3
"""
group_level_anova_selection.py
==============================

ANOVA-based feature selection on group-level common voxels.

Approach:
---------
1. Load common voxels from group_level_common_voxels.py
2. Apply ANOVA F-test to select voxels with highest color discrimination
3. Evaluate classification & reconstruction with selected voxels
4. Visualize selected voxels in brain space
5. **Full reconstruction & classification results (circular color space, confusion matrix)**

Usage:
    python group_level_anova_selection.py --roi V1 --timestamp baseline32_deob \
        --dataset deoblique_v2 --k-features 100

Output:
    derivatives/group_level/{timestamp}/{roi}/anova/
    ├── anova_f_values.npy               # F-values for each voxel
    ├── anova_p_values.npy               # P-values
    ├── selected_voxel_indices_k*.npy    # Top-k voxel indices
    ├── group_performance.csv
    ├── per_subject_performance.csv
    └── figures/
        ├── anova_f_distribution.png
        ├── selected_voxels_brain_k*.png
        ├── performance_vs_k.png
        ├── circular_color_space_k*.png     # Reconstruction visualization
        ├── confusion_matrix_k*.png         # Classification visualization
        └── reconstruction_error_k*.png     # Per-color reconstruction

Author: Claude Code
Date: 2025-12-13
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.feature_selection import f_classif
from sklearn.metrics import confusion_matrix
import argparse
import warnings
warnings.filterwarnings('ignore')

# Import utilities
from utils_color_decoding import (
    LABEL2HUE_DEG, N_COLORS, N_RUNS,
    diag_linear_predict, evaluate_reconstruction,
    compute_voxel_snr, visualize_circular_color_space,
    circular_diff_deg, get_stimulus_color_rgb
)

import nibabel as nib
from nilearn import plotting as niplot

# ============================================================================
# Configuration
# ============================================================================

def parse_args():
    parser = argparse.ArgumentParser(description='Group-level ANOVA feature selection')

    parser.add_argument('--roi', type=str, required=True)
    parser.add_argument('--timestamp', type=str, required=True)
    parser.add_argument('--dataset', type=str, default='deoblique_v2')
    parser.add_argument('--k-features', type=int, nargs='+', default=[50, 100, 200],
                        help='Number of features to select (can specify multiple)')
    parser.add_argument('--subjects', type=str, nargs='+',
                        default=['01', '02', '03', '05', '06', '07'])
    parser.add_argument('--output-dir', type=str, default=None)

    return parser.parse_args()

# ============================================================================
# Data Loading & ANOVA
# ============================================================================

def load_group_common_voxels(roi, timestamp):
    """Load common voxels from group analysis"""
    common_dir = Path(f"derivatives/group_level/{timestamp}/{roi}/common_voxels")

    group_amp = np.load(common_dir / 'group_amplitudes_z.npy')
    common_mask = np.load(common_dir / 'significant_voxels.npy')

    # Validate shape
    if group_amp.ndim != 4:
        raise ValueError(
            f"Expected 4D array (n_subjects, n_runs, n_colors, n_voxels), "
            f"got {group_amp.ndim}D array with shape {group_amp.shape}"
        )

    # Filter to common voxels
    group_amp_common = group_amp[:, :, :, common_mask]

    print(f"  Loaded group amplitudes: {group_amp.shape}")
    print(f"  Common voxels: {common_mask.sum()}/{len(common_mask)}")
    print(f"  Filtered: {group_amp_common.shape}")

    return group_amp_common, common_mask


def compute_anova_f_values(group_amplitudes):
    """
    Compute ANOVA F-values for each voxel

    H0: Color labels do not affect voxel response
    H1: At least one color has different mean response

    Args:
        group_amplitudes: (n_subjects, n_runs, n_colors, n_voxels)

    Returns:
        f_values: (n_voxels,) F-statistics
        p_values: (n_voxels,) p-values
    """
    n_subjects, n_runs, n_colors, n_voxels = group_amplitudes.shape

    # Reshape: (n_subjects*n_runs*n_colors, n_voxels)
    X_all = group_amplitudes.reshape(-1, n_voxels)
    y_all = np.tile(np.arange(n_colors), n_subjects * n_runs)

    # ANOVA F-test
    f_values, p_values = f_classif(X_all, y_all)

    print(f"\n  ANOVA F-test:")
    print(f"    F-values range: [{f_values.min():.2f}, {f_values.max():.2f}]")
    print(f"    p-values range: [{p_values.min():.6f}, {p_values.max():.6f}]")
    print(f"    Significant (p<0.05): {(p_values < 0.05).sum()}/{n_voxels}")

    return f_values, p_values


def select_top_k_voxels(f_values, k):
    """Select top-k voxels by F-value"""
    top_indices = np.argsort(f_values)[-k:][::-1]
    return top_indices


# ============================================================================
# Evaluation (with full reconstruction results)
# ============================================================================

def evaluate_anova_selection(group_amplitudes, f_values, k_values):
    """
    Evaluate ANOVA selection with leave-one-subject-out CV

    Returns full reconstruction results for visualization

    Args:
        group_amplitudes: (n_subjects, n_runs, n_colors, n_voxels)
        f_values: (n_voxels,) F-values
        k_values: List of k values to test

    Returns:
        results_df: DataFrame with performance results
        detailed_results: Dict with full reconstruction/classification results per k
    """
    n_subjects, n_runs, n_colors, n_voxels = group_amplitudes.shape

    print(f"\n{'='*80}")
    print(f"Evaluating ANOVA Selection (Leave-One-Subject-Out)")
    print(f"{'='*80}")

    all_results = []
    detailed_results = {}  # Store full results for visualization

    for k in k_values:
        if k > n_voxels:
            print(f"  ⚠️  k={k} > n_voxels={n_voxels}, skipping")
            continue

        # Select top-k voxels
        selected_indices = select_top_k_voxels(f_values, k)
        amplitudes_selected = group_amplitudes[:, :, :, selected_indices]

        print(f"\n  k={k}:")

        # Store detailed results for this k
        subject_reconstruction_results = []
        all_y_true = []
        all_y_pred = []

        for test_subj_idx in range(n_subjects):
            train_subjs = [i for i in range(n_subjects) if i != test_subj_idx]

            # Training data
            X_train = amplitudes_selected[train_subjs].reshape(-1, k)
            y_train = np.tile(np.arange(n_colors), len(train_subjs) * n_runs)

            # Test data
            X_test = amplitudes_selected[test_subj_idx].reshape(-1, k)
            y_test = np.tile(np.arange(n_colors), n_runs)

            # Classification
            y_pred = diag_linear_predict(X_train, y_train, X_test)
            accuracy = np.mean(y_pred == y_test)

            all_y_true.extend(y_test)
            all_y_pred.extend(y_pred)

            # Reconstruction
            X_test_reshaped = X_test.reshape(n_runs, n_colors, k)
            recon_results, mean_recon_error, per_color_stats = evaluate_reconstruction(X_test_reshaped)

            subject_reconstruction_results.append({
                'subject_idx': test_subj_idx,
                'recon_results': recon_results,
                'per_color_stats': per_color_stats
            })

            # SNR
            snr_values = compute_voxel_snr(X_test_reshaped)
            mean_snr = np.mean(snr_values)

            all_results.append({
                'k': k,
                'test_subject': test_subj_idx + 1,
                'classification_accuracy': accuracy,
                'reconstruction_error': mean_recon_error,
                'mean_snr': mean_snr
            })

        # Store detailed results
        detailed_results[k] = {
            'reconstruction_results': subject_reconstruction_results,
            'y_true': np.array(all_y_true),
            'y_pred': np.array(all_y_pred),
            'selected_indices': selected_indices
        }

        # Print summary
        k_results = [r for r in all_results if r['k'] == k]
        mean_acc = np.mean([r['classification_accuracy'] for r in k_results])
        mean_recon = np.mean([r['reconstruction_error'] for r in k_results])
        mean_snr = np.mean([r['mean_snr'] for r in k_results])

        print(f"    Acc={mean_acc:.2%}, Recon={mean_recon:.1f}°, SNR={mean_snr:.2f}")

    results_df = pd.DataFrame(all_results)
    return results_df, detailed_results


# ============================================================================
# Visualization - Circular Color Space & Confusion Matrix
# ============================================================================

def visualize_reconstruction_circular(detailed_results, k, output_dir):
    """
    Visualize reconstruction in circular color space (all subjects combined)

    Args:
        detailed_results: Dict with reconstruction results for this k
        k: Number of features
        output_dir: Output directory
    """
    recon_results_all = detailed_results['reconstruction_results']

    # Aggregate all reconstruction results across subjects
    all_reconstructed_hues = []
    all_true_hues = []

    for subj_result in recon_results_all:
        for fold_result in subj_result['recon_results']:
            all_reconstructed_hues.extend(fold_result['reconstructed_hues'])
            all_true_hues.extend(fold_result['true_hues'])

    all_reconstructed_hues = np.array(all_reconstructed_hues)
    all_true_hues = np.array(all_true_hues)

    # Calculate errors
    errors = circular_diff_deg(all_reconstructed_hues, all_true_hues)
    mean_error = errors.mean()

    # Plot circular color space
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Left: Circular reconstruction plot
    ax = axes[0]
    ax = plt.subplot(1, 2, 1, projection='polar')
    ax.set_theta_zero_location("E")
    ax.set_theta_direction(1)
    ax.set_rticks([])
    ax.grid(alpha=0.25)

    rng = np.random.default_rng(42)
    r_center = 1.0
    r_pred_base = 0.85

    n_colors = 8
    for color_idx in range(n_colors):
        color_name = f'color_{color_idx + 1}'
        true_hue = LABEL2HUE_DEG[color_name]
        true_rgb = get_stimulus_color_rgb(color_name)

        # True color at border
        ax.scatter([np.deg2rad(true_hue)], [r_center], s=110,
                   color=true_rgb, edgecolor='k', linewidths=0.8, zorder=4)

        # Predictions for this color
        mask = all_true_hues == true_hue
        pred_hues = all_reconstructed_hues[mask]

        for pred_hue in pred_hues:
            r_jit = r_pred_base + rng.uniform(-0.03, 0.03)
            ax.scatter([np.deg2rad(pred_hue)], [r_jit], s=28,
                       color=true_rgb, alpha=0.65, zorder=3)

    ax.set_ylim([0, 1.1])
    ax.set_title(f'ANOVA (k={k})\nMean error: {mean_error:.1f}°',
                 fontsize=12, fontweight='bold')

    # Right: Per-color error bar plot
    ax = axes[1]
    per_color_errors = []
    color_names = []

    for color_idx in range(n_colors):
        color_name = f'color_{color_idx + 1}'
        true_hue = LABEL2HUE_DEG[color_name]

        mask = all_true_hues == true_hue
        color_errors = errors[mask]

        per_color_errors.append(color_errors.mean())
        color_names.append(f'C{color_idx+1}')

    ax.bar(color_names, per_color_errors, alpha=0.7, edgecolor='black')
    ax.axhline(90, color='r', linestyle='--', label='Chance (90°)', linewidth=1.5)
    ax.axhline(mean_error, color='blue', linestyle='--', label=f'Mean ({mean_error:.1f}°)')
    ax.set_xlabel('Color')
    ax.set_ylabel('Reconstruction Error (degrees)')
    ax.set_title('Per-Color Reconstruction Error')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()

    fig_path = output_dir / 'figures' / f'circular_color_space_k{k}.png'
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"  ✓ Circular color space saved: {fig_path}")


def visualize_confusion_matrix(detailed_results, k, output_dir):
    """
    Visualize classification confusion matrix

    Args:
        detailed_results: Dict with classification results for this k
        k: Number of features
        output_dir: Output directory
    """
    y_true = detailed_results['y_true']
    y_pred = detailed_results['y_pred']

    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred)
    accuracy = np.mean(y_true == y_pred)

    # Normalize
    cm_norm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Left: Raw counts
    ax = axes[0]
    im = ax.imshow(cm, cmap='Blues', interpolation='nearest')
    ax.set_xlabel('Predicted Color')
    ax.set_ylabel('True Color')
    ax.set_title(f'Confusion Matrix (k={k})\nAccuracy: {accuracy:.2%}')
    ax.set_xticks(range(8))
    ax.set_yticks(range(8))
    ax.set_xticklabels([f'C{i+1}' for i in range(8)])
    ax.set_yticklabels([f'C{i+1}' for i in range(8)])

    # Add counts
    for i in range(8):
        for j in range(8):
            ax.text(j, i, f'{cm[i, j]}', ha='center', va='center',
                   color='white' if cm[i, j] > cm.max()/2 else 'black')

    plt.colorbar(im, ax=ax, label='Count')

    # Right: Normalized
    ax = axes[1]
    im = ax.imshow(cm_norm, cmap='Blues', vmin=0, vmax=1, interpolation='nearest')
    ax.set_xlabel('Predicted Color')
    ax.set_ylabel('True Color')
    ax.set_title(f'Normalized Confusion Matrix (k={k})')
    ax.set_xticks(range(8))
    ax.set_yticks(range(8))
    ax.set_xticklabels([f'C{i+1}' for i in range(8)])
    ax.set_yticklabels([f'C{i+1}' for i in range(8)])

    # Add proportions
    for i in range(8):
        for j in range(8):
            ax.text(j, i, f'{cm_norm[i, j]:.2f}', ha='center', va='center',
                   color='white' if cm_norm[i, j] > 0.5 else 'black', fontsize=9)

    plt.colorbar(im, ax=ax, label='Proportion')

    plt.tight_layout()

    fig_path = output_dir / 'figures' / f'confusion_matrix_k{k}.png'
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"  ✓ Confusion matrix saved: {fig_path}")


# ============================================================================
# Other Visualizations
# ============================================================================

def visualize_anova_f_distribution(f_values, p_values, k_values, output_dir):
    """Visualize ANOVA F-value distribution"""
    fig, axes = plt.subplots(1, 3, figsize=(16, 4))

    # F-values histogram
    ax = axes[0]
    ax.hist(f_values, bins=50, alpha=0.7, edgecolor='black')
    for k in k_values:
        if k <= len(f_values):
            threshold = np.sort(f_values)[-k]
            ax.axvline(threshold, linestyle='--', label=f'k={k}')
    ax.set_xlabel('F-value')
    ax.set_ylabel('Count')
    ax.set_title('ANOVA F-value Distribution')
    ax.legend()
    ax.grid(alpha=0.3)

    # P-values
    ax = axes[1]
    ax.hist(-np.log10(p_values + 1e-300), bins=50, alpha=0.7,
            edgecolor='black', color='orange')
    ax.axvline(-np.log10(0.05), color='r', linestyle='--', label='p=0.05')
    ax.set_xlabel('-log10(p-value)')
    ax.set_ylabel('Count')
    ax.set_title('Significance Distribution')
    ax.legend()
    ax.grid(alpha=0.3)

    # F-value rank plot
    ax = axes[2]
    f_sorted = np.sort(f_values)[::-1]
    ax.plot(f_sorted, linewidth=2)
    for k in k_values:
        if k <= len(f_values):
            ax.axvline(k, linestyle='--', label=f'k={k}')
            ax.axhline(f_sorted[k-1], linestyle=':', alpha=0.5)
    ax.set_xlabel('Voxel Rank')
    ax.set_ylabel('F-value')
    ax.set_title('F-values by Rank')
    ax.legend()
    ax.grid(alpha=0.3)

    plt.tight_layout()
    fig_path = output_dir / 'figures' / 'anova_f_distribution.png'
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"  ✓ F-distribution plot saved: {fig_path}")


def visualize_performance_vs_k(results_df, output_dir):
    """Visualize performance vs k"""
    fig, axes = plt.subplots(1, 3, figsize=(16, 4))

    k_values = sorted(results_df['k'].unique())

    # Group by k
    grouped = results_df.groupby('k')

    # Classification
    ax = axes[0]
    means = [grouped.get_group(k)['classification_accuracy'].mean() for k in k_values]
    stds = [grouped.get_group(k)['classification_accuracy'].std() for k in k_values]
    ax.errorbar(k_values, means, yerr=stds, marker='o', capsize=5, linewidth=2)
    ax.axhline(0.125, color='r', linestyle='--', label='Chance (12.5%)')
    ax.set_xlabel('Number of Features (k)')
    ax.set_ylabel('Classification Accuracy')
    ax.set_title('Classification Performance vs k')
    ax.legend()
    ax.grid(alpha=0.3)

    # Reconstruction
    ax = axes[1]
    means = [grouped.get_group(k)['reconstruction_error'].mean() for k in k_values]
    stds = [grouped.get_group(k)['reconstruction_error'].std() for k in k_values]
    ax.errorbar(k_values, means, yerr=stds, marker='o', capsize=5,
                linewidth=2, color='orange')
    ax.axhline(90, color='r', linestyle='--', label='Chance (90°)')
    ax.set_xlabel('Number of Features (k)')
    ax.set_ylabel('Reconstruction Error (degrees)')
    ax.set_title('Reconstruction Performance vs k')
    ax.legend()
    ax.grid(alpha=0.3)

    # SNR
    ax = axes[2]
    means = [grouped.get_group(k)['mean_snr'].mean() for k in k_values]
    stds = [grouped.get_group(k)['mean_snr'].std() for k in k_values]
    ax.errorbar(k_values, means, yerr=stds, marker='o', capsize=5,
                linewidth=2, color='green')
    ax.set_xlabel('Number of Features (k)')
    ax.set_ylabel('Mean SNR')
    ax.set_title('SNR vs k')
    ax.grid(alpha=0.3)

    plt.tight_layout()
    fig_path = output_dir / 'figures' / 'performance_vs_k.png'
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"  ✓ Performance vs k plot saved: {fig_path}")


# ============================================================================
# Main
# ============================================================================

def main():
    args = parse_args()

    print(f"\n{'='*80}")
    print(f"Group-level ANOVA Feature Selection")
    print(f"{'='*80}")
    print(f"ROI: {args.roi}")
    print(f"Timestamp: {args.timestamp}")
    print(f"k values: {args.k_features}")

    # Output directory
    if args.output_dir is None:
        output_dir = Path(f"derivatives/group_level/{args.timestamp}/{args.roi}/anova")
    else:
        output_dir = Path(args.output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / 'figures').mkdir(exist_ok=True)

    # Load data
    print(f"\n{'='*80}")
    print(f"Loading common voxels...")
    print(f"{'='*80}")
    group_amplitudes, common_mask = load_group_common_voxels(args.roi, args.timestamp)

    # Compute ANOVA F-values
    print(f"\n{'='*80}")
    print(f"Computing ANOVA F-values...")
    print(f"{'='*80}")
    f_values, p_values = compute_anova_f_values(group_amplitudes)

    # Evaluate (with detailed results)
    results_df, detailed_results = evaluate_anova_selection(
        group_amplitudes, f_values, args.k_features
    )

    # Save
    print(f"\n{'='*80}")
    print(f"Saving results...")
    print(f"{'='*80}")

    np.save(output_dir / 'anova_f_values.npy', f_values)
    np.save(output_dir / 'anova_p_values.npy', p_values)

    for k in args.k_features:
        if k in detailed_results:
            selected_indices = detailed_results[k]['selected_indices']
            np.save(output_dir / f'selected_voxel_indices_k{k}.npy', selected_indices)

    results_df.to_csv(output_dir / 'per_subject_performance.csv', index=False)

    # Group summary
    summary = results_df.groupby('k').agg({
        'classification_accuracy': ['mean', 'std'],
        'reconstruction_error': ['mean', 'std'],
        'mean_snr': ['mean', 'std']
    }).reset_index()
    summary.to_csv(output_dir / 'group_performance.csv', index=False)

    print(f"  ✓ Results saved")

    # Visualize
    print(f"\n{'='*80}")
    print(f"Creating visualizations...")
    print(f"{'='*80}")

    visualize_anova_f_distribution(f_values, p_values, args.k_features, output_dir)
    visualize_performance_vs_k(results_df, output_dir)

    # Circular color space & confusion matrix for each k
    for k in args.k_features:
        if k in detailed_results:
            print(f"\n  Creating detailed visualizations for k={k}...")
            visualize_reconstruction_circular(detailed_results[k], k, output_dir)
            visualize_confusion_matrix(detailed_results[k], k, output_dir)

    print(f"\n{'='*80}")
    print(f"ANOVA Feature Selection Complete!")
    print(f"{'='*80}")
    print(f"Results saved to: {output_dir}")


if __name__ == '__main__':
    main()
