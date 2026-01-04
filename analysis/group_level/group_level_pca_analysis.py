#!/usr/bin/env python3
"""
group_level_pca_analysis.py
===========================

Group-level PCA analysis with high-loading voxel visualization.

Approach:
---------
1. Load group amplitudes from common voxel analysis
2. Fit PCA on group data (concatenated subjects & runs)
3. Evaluate performance with leave-one-subject-out CV
4. Visualize high-loading voxels for top components
5. Classification & reconstruction performance

High-loading voxels: Voxels with highest absolute loading on each PC

Usage:
    python group_level_pca_analysis.py --roi V1 --timestamp baseline32_deob \
        --dataset deoblique_v2 --n-components 50 --use-common-voxels

Output:
    derivatives/group_level/{timestamp}/{roi}/pca/
    ├── pca_model.pkl                     # Fitted PCA model
    ├── pca_loadings.npy                  # (n_voxels, n_components)
    ├── high_loading_voxels.npz           # Top voxels per component
    ├── group_performance.csv             # Performance metrics
    ├── per_subject_performance.csv       # Subject-level metrics
    └── figures/
        ├── pca_loadings_heatmap.png      # Loadings visualization
        ├── high_loading_voxels_PC*.png   # Brain visualization per PC
        ├── explained_variance.png
        ├── classification_performance.png
        └── reconstruction_performance.png

Author: Claude Code
Date: 2025-12-13
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.decomposition import PCA
import pickle
import argparse
import sys
import warnings
warnings.filterwarnings('ignore')

# Import utilities
from utils_color_decoding import (
    LABEL2HUE_DEG, N_COLORS, N_RUNS,
    diag_linear_predict, evaluate_reconstruction,
    visualize_circular_color_space, compute_voxel_snr
)

import nibabel as nib
from nilearn import plotting as niplot

# ============================================================================
# Configuration
# ============================================================================

def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description='Group-level PCA analysis'
    )

    # Required arguments
    parser.add_argument('--roi', type=str, required=True,
                        help='ROI name (V1, V2, V3, hV4)')
    parser.add_argument('--timestamp', type=str, required=True,
                        help='Baseline timestamp (e.g., baseline32_deob)')
    parser.add_argument('--dataset', type=str, default='deoblique_v2',
                        help='Dataset name (default: deoblique_v2)')

    # PCA parameters
    parser.add_argument('--n-components', type=int, default=50,
                        help='Number of PCA components (default: 50)')
    parser.add_argument('--use-common-voxels', action='store_true',
                        help='Use only common voxels from group analysis')

    # Visualization parameters
    parser.add_argument('--top-k-voxels', type=int, default=100,
                        help='Number of top-loading voxels to visualize per PC (default: 100)')
    parser.add_argument('--n-pcs-visualize', type=int, default=5,
                        help='Number of top PCs to visualize (default: 5)')

    # Non-CVD subjects (default)
    parser.add_argument('--subjects', type=str, nargs='+',
                        default=['01', '02', '03', '05', '06', '07'],
                        help='Subject IDs (default: non-CVD subjects)')

    # Output directory
    parser.add_argument('--output-dir', type=str, default=None,
                        help='Output directory')

    return parser.parse_args()


# ============================================================================
# Data Loading
# ============================================================================

def load_group_data(roi, timestamp, use_common_voxels=True):
    """
    Load group amplitudes and optionally filter to common voxels

    Args:
        roi: ROI name
        timestamp: Baseline timestamp
        use_common_voxels: If True, use only common voxels

    Returns:
        group_amplitudes: (n_subjects, n_runs, n_colors, n_voxels) array
        voxel_mask: Boolean mask (n_voxels,) or None
    """
    common_voxel_dir = Path(f"derivatives/group_level/{timestamp}/{roi}/common_voxels")

    # Load group amplitudes
    amp_file = common_voxel_dir / 'group_amplitudes_z.npy'
    if not amp_file.exists():
        raise FileNotFoundError(
            f"Group amplitudes not found!\n"
            f"  Expected: {amp_file}\n"
            f"  Please run group_level_common_voxels.py first"
        )

    group_amplitudes = np.load(amp_file)
    print(f"  Loaded group amplitudes: {group_amplitudes.shape}")

    # Validate shape
    if group_amplitudes.ndim != 4:
        raise ValueError(
            f"Expected 4D array (n_subjects, n_runs, n_colors, n_voxels), "
            f"got {group_amplitudes.ndim}D array with shape {group_amplitudes.shape}"
        )

    voxel_mask = None
    if use_common_voxels:
        # Load common voxel mask
        mask_file = common_voxel_dir / 'significant_voxels.npy'
        if not mask_file.exists():
            raise FileNotFoundError(
                f"Common voxel mask not found: {mask_file}\n"
                f"  Please run group_level_common_voxels.py first"
            )

        voxel_mask = np.load(mask_file)
        group_amplitudes = group_amplitudes[:, :, :, voxel_mask]

        print(f"  Using common voxels: {voxel_mask.sum()}/{len(voxel_mask)}")
        print(f"  Filtered amplitudes: {group_amplitudes.shape}")

    return group_amplitudes, voxel_mask


# ============================================================================
# PCA Analysis
# ============================================================================

def fit_group_pca(group_amplitudes, n_components):
    """
    Fit PCA on group data (all subjects, all runs concatenated)

    Args:
        group_amplitudes: (n_subjects, n_runs, n_colors, n_voxels) array
        n_components: Number of PCA components

    Returns:
        pca: Fitted PCA model
        X_all_pca: Transformed data (n_samples, n_components)
        y_all: Labels (n_samples,)
    """
    n_subjects, n_runs, n_colors, n_voxels = group_amplitudes.shape

    # Concatenate all subjects and runs
    X_all = group_amplitudes.reshape(-1, n_voxels)  # (n_subjects*n_runs*n_colors, n_voxels)
    y_all = np.tile(np.arange(n_colors), n_subjects * n_runs)

    print(f"\n  Fitting PCA on group data:")
    print(f"    Data shape: {X_all.shape}")
    print(f"    n_components: {n_components}")

    # Fit PCA
    pca = PCA(n_components=n_components, random_state=42)
    X_all_pca = pca.fit_transform(X_all)

    print(f"    Explained variance: {pca.explained_variance_ratio_.sum():.2%}")
    print(f"    Transformed shape: {X_all_pca.shape}")

    return pca, X_all_pca, y_all


def evaluate_pca_leave_one_subject_out(group_amplitudes, n_components):
    """
    Evaluate PCA with leave-one-subject-out cross-validation

    CRITICAL: PCA는 각 fold의 training set에서만 fit!

    Args:
        group_amplitudes: (n_subjects, n_runs, n_colors, n_voxels) array
        n_components: Number of PCA components

    Returns:
        results_df: DataFrame with per-subject results
        detailed_results: Dict with reconstruction/classification results for visualization
    """
    n_subjects, n_runs, n_colors, n_voxels = group_amplitudes.shape

    print(f"\n{'='*80}")
    print(f"Leave-One-Subject-Out Cross-Validation")
    print(f"{'='*80}")

    results = []
    all_y_true = []
    all_y_pred = []
    all_recon_results = []

    for test_subject_idx in range(n_subjects):
        train_subjects = [i for i in range(n_subjects) if i != test_subject_idx]

        # Training data: all other subjects
        X_train_raw = group_amplitudes[train_subjects].reshape(-1, n_voxels)
        y_train = np.tile(np.arange(n_colors), len(train_subjects) * n_runs)

        # Test data: held-out subject
        X_test_raw = group_amplitudes[test_subject_idx].reshape(-1, n_voxels)
        y_test = np.tile(np.arange(n_colors), n_runs)

        # Fit PCA on training data
        pca = PCA(n_components=n_components, random_state=42)
        X_train_pca = pca.fit_transform(X_train_raw)

        # Transform test data
        X_test_pca = pca.transform(X_test_raw)

        # Classification
        y_pred = diag_linear_predict(X_train_pca, y_train, X_test_pca)
        accuracy = np.mean(y_pred == y_test)

        all_y_true.extend(y_test)
        all_y_pred.extend(y_pred)

        # Reconstruction
        # Reshape for evaluate_reconstruction: (n_runs, n_colors, n_components)
        X_test_pca_reshaped = X_test_pca.reshape(n_runs, n_colors, n_components)

        recon_results, mean_recon_error, per_color_stats = evaluate_reconstruction(
            X_test_pca_reshaped
        )

        all_recon_results.extend(recon_results)

        # SNR (on PCA components)
        snr_values = compute_voxel_snr(X_test_pca_reshaped)
        mean_snr = np.mean(snr_values)

        results.append({
            'test_subject': test_subject_idx + 1,
            'classification_accuracy': accuracy,
            'reconstruction_error': mean_recon_error,
            'mean_snr': mean_snr,
            'explained_variance': pca.explained_variance_ratio_.sum()
        })

        print(f"  Subject {test_subject_idx+1}: "
              f"Acc={accuracy:.2%}, Recon={mean_recon_error:.1f}°, SNR={mean_snr:.2f}")

    results_df = pd.DataFrame(results)

    print(f"\n  Mean performance:")
    print(f"    Classification: {results_df['classification_accuracy'].mean():.2%} ± "
          f"{results_df['classification_accuracy'].std():.2%}")
    print(f"    Reconstruction: {results_df['reconstruction_error'].mean():.1f}° ± "
          f"{results_df['reconstruction_error'].std():.1f}°")
    print(f"    SNR: {results_df['mean_snr'].mean():.2f} ± {results_df['mean_snr'].std():.2f}")

    # Package detailed results for visualization
    detailed_results = {
        'y_true': np.array(all_y_true),
        'y_pred': np.array(all_y_pred),
        'recon_results': all_recon_results
    }

    return results_df, detailed_results


# ============================================================================
# High-Loading Voxel Analysis
# ============================================================================

def identify_high_loading_voxels(pca, top_k=100):
    """
    Identify voxels with highest absolute loading on each PC

    Args:
        pca: Fitted PCA model
        top_k: Number of top voxels per component

    Returns:
        high_loading_dict: Dict with PC index -> voxel indices and loadings
    """
    loadings = pca.components_  # (n_components, n_voxels)
    n_components, n_voxels = loadings.shape

    print(f"\n{'='*80}")
    print(f"Identifying High-Loading Voxels")
    print(f"{'='*80}")
    print(f"  n_components: {n_components}")
    print(f"  n_voxels: {n_voxels}")
    print(f"  top_k: {top_k}")

    high_loading_dict = {}

    for pc_idx in range(n_components):
        # Absolute loadings
        abs_loadings = np.abs(loadings[pc_idx, :])

        # Top k voxel indices
        top_indices = np.argsort(abs_loadings)[-top_k:][::-1]

        # Loadings for top voxels
        top_loadings = loadings[pc_idx, top_indices]

        high_loading_dict[pc_idx] = {
            'voxel_indices': top_indices,
            'loadings': top_loadings,
            'abs_loadings': abs_loadings[top_indices]
        }

    return high_loading_dict


# ============================================================================
# Visualization
# ============================================================================

def visualize_pca_loadings(pca, high_loading_dict, n_pcs_visualize, output_dir):
    """
    Visualize PCA loadings as heatmap

    Args:
        pca: Fitted PCA model
        high_loading_dict: Dict with high-loading voxels
        n_pcs_visualize: Number of PCs to show
        output_dir: Output directory
    """
    loadings = pca.components_[:n_pcs_visualize, :]  # (n_pcs, n_voxels)

    fig, axes = plt.subplots(2, 2, figsize=(16, 10))

    # 1. Loadings heatmap (top PCs × all voxels - subsampled)
    ax = axes[0, 0]
    # Subsample voxels for visualization
    step = max(1, loadings.shape[1] // 500)
    loadings_sub = loadings[:, ::step]
    im = ax.imshow(loadings_sub, aspect='auto', cmap='RdBu_r',
                   vmin=-0.5, vmax=0.5, interpolation='nearest')
    ax.set_xlabel('Voxel Index (subsampled)')
    ax.set_ylabel('Principal Component')
    ax.set_title(f'PCA Loadings (Top {n_pcs_visualize} PCs)')
    ax.set_yticks(range(n_pcs_visualize))
    ax.set_yticklabels([f'PC{i+1}' for i in range(n_pcs_visualize)])
    plt.colorbar(im, ax=ax, label='Loading')

    # 2. Explained variance
    ax = axes[0, 1]
    variance_ratio = pca.explained_variance_ratio_
    cumsum_variance = np.cumsum(variance_ratio)
    x = np.arange(1, len(variance_ratio) + 1)
    ax.bar(x[:n_pcs_visualize], variance_ratio[:n_pcs_visualize],
           alpha=0.7, edgecolor='black', label='Individual')
    ax.plot(x[:n_pcs_visualize], cumsum_variance[:n_pcs_visualize],
            'ro-', linewidth=2, label='Cumulative')
    ax.set_xlabel('Principal Component')
    ax.set_ylabel('Explained Variance Ratio')
    ax.set_title('Explained Variance')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    # 3. Top loading distribution per PC
    ax = axes[1, 0]
    for pc_idx in range(min(5, n_pcs_visualize)):
        abs_loadings = high_loading_dict[pc_idx]['abs_loadings']
        ax.plot(abs_loadings, label=f'PC{pc_idx+1}', alpha=0.7)
    ax.set_xlabel('Voxel Rank (Top voxels)')
    ax.set_ylabel('Absolute Loading')
    ax.set_title('Top Loadings per PC')
    ax.legend()
    ax.grid(alpha=0.3)

    # 4. Loading statistics
    ax = axes[1, 1]
    ax.axis('off')

    stats_text = f"""
PCA Analysis Summary
{'='*40}

Total components: {len(variance_ratio)}
Total variance explained: {cumsum_variance[-1]:.2%}

Top {n_pcs_visualize} components:
  Explained variance: {cumsum_variance[n_pcs_visualize-1]:.2%}

Per-component statistics:
"""
    for pc_idx in range(min(5, n_pcs_visualize)):
        stats_text += (f"\nPC{pc_idx+1}:"
                      f"\n  Variance: {variance_ratio[pc_idx]:.2%}"
                      f"\n  Cumulative: {cumsum_variance[pc_idx]:.2%}")

    ax.text(0.1, 0.5, stats_text, transform=ax.transAxes,
            fontsize=10, verticalalignment='center',
            family='monospace',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

    plt.tight_layout()

    fig_path = output_dir / 'figures' / 'pca_loadings_heatmap.png'
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"  ✓ PCA loadings heatmap saved: {fig_path}")
    return fig_path


def visualize_reconstruction_circular_pca(detailed_results, n_components, output_dir):
    """
    Visualize PCA reconstruction in circular color space

    Args:
        detailed_results: Dict with reconstruction results
        n_components: Number of PCA components
        output_dir: Output directory
    """
    from utils_color_decoding import circular_diff_deg, get_stimulus_color_rgb

    recon_results_all = detailed_results['recon_results']

    # Aggregate all reconstruction results across subjects
    all_reconstructed_hues = []
    all_true_hues = []

    for fold_result in recon_results_all:
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
    ax.set_title(f'PCA (n={n_components})\nMean error: {mean_error:.1f}°',
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

    fig_path = output_dir / 'figures' / f'circular_color_space_pca.png'
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"  ✓ Circular color space saved: {fig_path}")


def visualize_confusion_matrix_pca(detailed_results, n_components, output_dir):
    """
    Visualize PCA classification confusion matrix

    Args:
        detailed_results: Dict with classification results
        n_components: Number of PCA components
        output_dir: Output directory
    """
    from sklearn.metrics import confusion_matrix

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
    ax.set_title(f'Confusion Matrix (PCA n={n_components})\nAccuracy: {accuracy:.2%}')
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
    ax.set_title(f'Normalized Confusion Matrix (PCA n={n_components})')
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

    fig_path = output_dir / 'figures' / f'confusion_matrix_pca.png'
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"  ✓ Confusion matrix saved: {fig_path}")


def visualize_high_loading_voxels_brain(high_loading_dict, voxel_mask, roi,
                                        roi_mask_path, n_pcs_visualize, output_dir):
    """
    Visualize high-loading voxels in brain space for each PC

    Args:
        high_loading_dict: Dict with high-loading voxels
        voxel_mask: Boolean mask (n_voxels_original,) or None
        roi: ROI name
        roi_mask_path: Path to ROI mask
        n_pcs_visualize: Number of PCs to visualize
        output_dir: Output directory
    """
    try:
        # Load ROI mask
        if not Path(roi_mask_path).exists():
            print(f"  ⚠️  ROI mask not found: {roi_mask_path}")
            return None

        mask_img = nib.load(roi_mask_path)
        mask_data = mask_img.get_fdata()

        # Get all voxel coordinates in ROI
        all_voxel_coords = np.argwhere(mask_data > 0)

        # If using common voxels, map indices back
        if voxel_mask is not None:
            # voxel_mask: (n_voxels_original,) boolean
            # high_loading voxel indices are relative to common voxels
            common_voxel_indices = np.where(voxel_mask)[0]
        else:
            common_voxel_indices = np.arange(len(all_voxel_coords))

        fig_paths = []

        for pc_idx in range(min(n_pcs_visualize, len(high_loading_dict))):
            # Get high-loading voxels for this PC
            high_voxel_indices_relative = high_loading_dict[pc_idx]['voxel_indices']
            loadings = high_loading_dict[pc_idx]['loadings']

            # Map back to original voxel space
            high_voxel_indices_original = common_voxel_indices[high_voxel_indices_relative]

            # Create brain volume
            highlight_data = np.zeros_like(mask_data)

            for i, orig_idx in enumerate(high_voxel_indices_original):
                if orig_idx < len(all_voxel_coords):
                    coord = all_voxel_coords[orig_idx]
                    # Use absolute loading as intensity
                    highlight_data[coord[0], coord[1], coord[2]] = np.abs(loadings[i])

            highlight_img = nib.Nifti1Image(highlight_data, mask_img.affine, mask_img.header)

            # Plot
            fig, axes = plt.subplots(2, 2, figsize=(14, 12))

            niplot.plot_stat_map(highlight_img, display_mode='z', cut_coords=5,
                                title=f'PC{pc_idx+1} High-Loading Voxels - Axial',
                                axes=axes[0, 0], colorbar=True, cmap='hot',
                                threshold=0.01)

            niplot.plot_stat_map(highlight_img, display_mode='x', cut_coords=5,
                                title=f'PC{pc_idx+1} High-Loading Voxels - Sagittal',
                                axes=axes[0, 1], colorbar=True, cmap='hot',
                                threshold=0.01)

            niplot.plot_stat_map(highlight_img, display_mode='y', cut_coords=5,
                                title=f'PC{pc_idx+1} High-Loading Voxels - Coronal',
                                axes=axes[1, 0], colorbar=True, cmap='hot',
                                threshold=0.01)

            niplot.plot_glass_brain(highlight_img,
                                   title=f'PC{pc_idx+1} High-Loading Voxels - Glass Brain',
                                   axes=axes[1, 1], colorbar=True, cmap='hot',
                                   threshold=0.01)

            plt.suptitle(f'{roi}: PC{pc_idx+1} High-Loading Voxels\n'
                        f'(Top {len(high_voxel_indices_relative)} voxels)',
                        fontsize=16, fontweight='bold')
            plt.tight_layout()

            fig_path = output_dir / 'figures' / f'high_loading_voxels_PC{pc_idx+1}.png'
            plt.savefig(fig_path, dpi=150, bbox_inches='tight')
            plt.close()

            fig_paths.append(fig_path)
            print(f"  ✓ PC{pc_idx+1} brain visualization saved: {fig_path}")

        return fig_paths

    except Exception as e:
        print(f"  ⚠️  Brain visualization failed: {e}")
        return None


# ============================================================================
# Main
# ============================================================================

def main():
    args = parse_args()

    print(f"\n{'='*80}")
    print(f"Group-level PCA Analysis")
    print(f"{'='*80}")
    print(f"ROI: {args.roi}")
    print(f"Dataset: {args.dataset}")
    print(f"Timestamp: {args.timestamp}")
    print(f"n_components: {args.n_components}")
    print(f"Use common voxels: {args.use_common_voxels}")
    print(f"Top k voxels: {args.top_k_voxels}")
    print(f"n_pcs visualize: {args.n_pcs_visualize}")

    # Output directory
    if args.output_dir is None:
        output_dir = Path(f"derivatives/group_level/{args.timestamp}/{args.roi}/pca")
    else:
        output_dir = Path(args.output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / 'figures').mkdir(exist_ok=True)

    print(f"Output directory: {output_dir}")

    # ========================================================================
    # Load data
    # ========================================================================
    print(f"\n{'='*80}")
    print(f"Loading group data...")
    print(f"{'='*80}")

    group_amplitudes, voxel_mask = load_group_data(
        args.roi, args.timestamp, args.use_common_voxels
    )

    # ========================================================================
    # Fit group-level PCA
    # ========================================================================
    print(f"\n{'='*80}")
    print(f"Fitting Group-level PCA")
    print(f"{'='*80}")

    pca, X_all_pca, y_all = fit_group_pca(group_amplitudes, args.n_components)

    # ========================================================================
    # Leave-one-subject-out evaluation
    # ========================================================================
    results_df, detailed_results = evaluate_pca_leave_one_subject_out(
        group_amplitudes, args.n_components
    )

    # ========================================================================
    # Identify high-loading voxels
    # ========================================================================
    high_loading_dict = identify_high_loading_voxels(pca, args.top_k_voxels)

    # ========================================================================
    # Save results
    # ========================================================================
    print(f"\n{'='*80}")
    print(f"Saving results...")
    print(f"{'='*80}")

    # Save PCA model
    with open(output_dir / 'pca_model.pkl', 'wb') as f:
        pickle.dump(pca, f)
    print(f"  ✓ PCA model saved")

    # Save loadings
    np.save(output_dir / 'pca_loadings.npy', pca.components_)
    print(f"  ✓ PCA loadings saved")

    # Save high-loading voxels
    np.savez(output_dir / 'high_loading_voxels.npz', **high_loading_dict)
    print(f"  ✓ High-loading voxels saved")

    # Save performance
    results_df.to_csv(output_dir / 'per_subject_performance.csv', index=False)
    print(f"  ✓ Per-subject performance saved")

    # Group performance summary
    group_summary = pd.DataFrame([{
        'metric': 'classification_accuracy',
        'mean': results_df['classification_accuracy'].mean(),
        'std': results_df['classification_accuracy'].std()
    }, {
        'metric': 'reconstruction_error',
        'mean': results_df['reconstruction_error'].mean(),
        'std': results_df['reconstruction_error'].std()
    }, {
        'metric': 'mean_snr',
        'mean': results_df['mean_snr'].mean(),
        'std': results_df['mean_snr'].std()
    }])
    group_summary.to_csv(output_dir / 'group_performance.csv', index=False)
    print(f"  ✓ Group performance summary saved")

    # ========================================================================
    # Visualizations
    # ========================================================================
    print(f"\n{'='*80}")
    print(f"Creating visualizations...")
    print(f"{'='*80}")

    visualize_pca_loadings(pca, high_loading_dict, args.n_pcs_visualize, output_dir)

    # Circular color space & confusion matrix
    from sklearn.metrics import confusion_matrix
    from utils_color_decoding import circular_diff_deg, get_stimulus_color_rgb

    visualize_reconstruction_circular_pca(detailed_results, args.n_components, output_dir)
    visualize_confusion_matrix_pca(detailed_results, args.n_components, output_dir)

    # Get ROI mask path
    first_subject = args.subjects[0]
    roi_mask_candidates = [
        f'derivatives/sub-{first_subject}/roi_pipeline/{args.roi}_mask_thr50_intnearest_binTrue_masknone_gmTrue_subjFalse.nii.gz',
        f'derivatives/BH2009_{args.dataset}/{args.timestamp}/sub-{first_subject}_{args.roi}_mask.nii.gz',
        f'derivatives/roi_masks/sub-{first_subject}_{args.roi}_mask.nii.gz'
    ]

    roi_mask_path = None
    for candidate in roi_mask_candidates:
        if Path(candidate).exists():
            roi_mask_path = candidate
            break

    if roi_mask_path:
        visualize_high_loading_voxels_brain(
            high_loading_dict, voxel_mask, args.roi, roi_mask_path,
            args.n_pcs_visualize, output_dir
        )
    else:
        print(f"  ⚠️  ROI mask not found, skipping brain visualization")

    # ========================================================================
    # Final summary
    # ========================================================================
    print(f"\n{'='*80}")
    print(f"Group-level PCA Analysis Complete!")
    print(f"{'='*80}")
    print(f"Results saved to: {output_dir}")
    print(f"\nKey results:")
    print(f"  - n_components: {args.n_components}")
    print(f"  - Explained variance: {pca.explained_variance_ratio_.sum():.2%}")
    print(f"  - Mean classification: {results_df['classification_accuracy'].mean():.2%}")
    print(f"  - Mean reconstruction: {results_df['reconstruction_error'].mean():.1f}°")
    print(f"  - High-loading voxels per PC: {args.top_k_voxels}")


if __name__ == '__main__':
    main()
