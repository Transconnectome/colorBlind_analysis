#!/usr/bin/env python3
"""
group_level_analysis_comprehensive.py
=====================================

Comprehensive group-level analysis with three statistical approaches:
  1. Option A: One-sample t-test vs 0 (activation exists?)
  2. Option B-1: Each color vs others (color selectivity)
  3. Option B-2: Pairwise color contrasts (color discrimination - 중요 for 적록색맹)

Then:
  - Create UNION of significant voxels from all three methods
  - Run classification & reconstruction on union voxels
  - Visualize pairwise contrasts (28 pairs for 8 colors)

Usage:
    python group_level_analysis_comprehensive.py \
        --roi V1 \
        --timestamp baseline32_deob_determin \
        --dataset deoblique_v2 \
        --subjects 03 05 06 07

Output:
    derivatives/group_level/{timestamp}/{roi}/comprehensive/
    ├── statistics/
    │   ├── option_a_vs_zero.npz
    │   ├── option_b1_selectivity.npz
    │   ├── option_b2_pairwise.npz
    │   └── union_voxels.npz
    ├── figures/
    │   ├── pairwise_contrasts_grid.png
    │   ├── union_voxels_breakdown.png
    │   ├── circular_color_space_union.png
    │   └── confusion_matrix_union.png
    └── performance/
        ├── classification_results.csv
        └── reconstruction_results.csv

Author: Claude Code
Date: 2025-12-13
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from scipy import stats
from statsmodels.stats.multitest import multipletests
import argparse
import warnings
warnings.filterwarnings('ignore')

# Import utilities
from utils_color_decoding import (
    LABEL2HUE_DEG, N_COLORS, N_RUNS,
    diag_linear_predict, evaluate_reconstruction,
    visualize_circular_color_space, compute_voxel_snr,
    circular_diff_deg, get_stimulus_color_rgb
)

from sklearn.metrics import confusion_matrix
from sklearn.decomposition import PCA

# ============================================================================
# Configuration
# ============================================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description='Comprehensive group-level analysis'
    )

    parser.add_argument('--roi', type=str, required=True)
    parser.add_argument('--timestamp', type=str, required=True)
    parser.add_argument('--dataset', type=str, default='deoblique_v2')
    parser.add_argument('--subjects', type=str, nargs='+',
                        default=['01', '02', '03', '05', '06', '07'])
    parser.add_argument('--fdr-alpha', type=float, default=0.05,
                        help='FDR alpha level (not used if --use-t-threshold is set)')
    parser.add_argument('--use-t-threshold', action='store_true',
                        help='Use absolute t-value threshold instead of FDR correction')
    parser.add_argument('--t-threshold', type=float, default=5.0,
                        help='Absolute t-value threshold (default: 5.0)')
    parser.add_argument('--output-dir', type=str, default=None)

    return parser.parse_args()


# ============================================================================
# Data Loading
# ============================================================================

def load_group_amplitudes(roi, timestamp, dataset='deoblique_v2'):
    """Load pre-computed group_amplitudes_z.npy from common_voxels step"""

    common_voxel_dir = Path(f"derivatives/group_level/{timestamp}/{roi}/common_voxels")
    amp_file = common_voxel_dir / 'group_amplitudes_z.npy'

    if not amp_file.exists():
        raise FileNotFoundError(
            f"Group amplitudes not found!\n"
            f"  Expected: {amp_file}\n"
            f"  Please run group_level_common_voxels.py first"
        )

    group_amplitudes = np.load(amp_file)
    print(f"  Loaded: {group_amplitudes.shape}")
    print(f"  (n_subjects={group_amplitudes.shape[0]}, n_runs={group_amplitudes.shape[1]}, "
          f"n_colors={group_amplitudes.shape[2]}, n_voxels={group_amplitudes.shape[3]})")

    return group_amplitudes


# ============================================================================
# Statistical Tests
# ============================================================================

def compute_three_statistical_tests(group_amplitudes):
    """
    Compute three types of statistical tests

    Returns:
        stats_dict: Dictionary with results from all three tests
    """
    n_subjects, n_runs, n_colors, n_voxels = group_amplitudes.shape

    print(f"\n{'='*80}")
    print(f"Computing Three Statistical Tests")
    print(f"{'='*80}")

    # Average across runs
    amplitudes_avg = group_amplitudes.mean(axis=1)  # (n_subjects, n_colors, n_voxels)

    stats_dict = {}

    # ========================================================================
    # Option A: One-sample t-test vs 0
    # ========================================================================
    print(f"\n[1/3] Option A: One-sample t-test vs 0")

    t_vs0 = np.zeros((n_colors, n_voxels))
    p_vs0 = np.zeros((n_colors, n_voxels))

    for c in range(n_colors):
        t_vs0[c, :], p_vs0[c, :] = stats.ttest_1samp(amplitudes_avg[:, c, :], 0, axis=0)

    stats_dict['vs_zero'] = {'t_values': t_vs0, 'p_values': p_vs0}
    print(f"  Computed {n_colors} colors × {n_voxels} voxels = {n_colors * n_voxels} tests")

    # ========================================================================
    # Option B-1: Each color vs others (Selectivity)
    # ========================================================================
    print(f"\n[2/3] Option B-1: Each color vs others (selectivity)")

    t_sel = np.zeros((n_colors, n_voxels))
    p_sel = np.zeros((n_colors, n_voxels))

    for c in range(n_colors):
        this_color = amplitudes_avg[:, c, :]
        other_mask = np.ones(n_colors, dtype=bool)
        other_mask[c] = False
        other_colors = amplitudes_avg[:, other_mask, :].mean(axis=1)

        t_sel[c, :], p_sel[c, :] = stats.ttest_rel(this_color, other_colors, axis=0)

    stats_dict['selectivity'] = {'t_values': t_sel, 'p_values': p_sel}
    print(f"  Computed {n_colors} colors × {n_voxels} voxels = {n_colors * n_voxels} tests")

    # ========================================================================
    # Option B-2: Pairwise contrasts (Discrimination)
    # ========================================================================
    print(f"\n[3/3] Option B-2: Pairwise color contrasts (discrimination)")

    pairwise = []
    for c1 in range(n_colors):
        for c2 in range(c1 + 1, n_colors):
            t_vals, p_vals = stats.ttest_rel(
                amplitudes_avg[:, c1, :],
                amplitudes_avg[:, c2, :],
                axis=0
            )

            pairwise.append({
                'color1': c1,
                'color2': c2,
                'pair_name': f'C{c1+1}_vs_C{c2+1}',
                't_values': t_vals,
                'p_values': p_vals
            })

    stats_dict['pairwise'] = pairwise
    print(f"  Computed {len(pairwise)} pairs × {n_voxels} voxels = {len(pairwise) * n_voxels} tests")

    return stats_dict


def apply_fdr_correction(stats_dict, alpha=0.05):
    """Apply FDR correction to all tests"""

    print(f"\n{'='*80}")
    print(f"FDR Correction (alpha={alpha})")
    print(f"{'='*80}")

    corrected = {}

    # Option A
    print(f"\n[1/3] Option A (vs 0):")
    p_flat = stats_dict['vs_zero']['p_values'].flatten()
    reject, p_corr, _, _ = multipletests(p_flat, alpha=alpha, method='fdr_bh')

    n_colors, n_voxels = stats_dict['vs_zero']['p_values'].shape
    sig_mask = reject.reshape((n_colors, n_voxels))

    corrected['vs_zero'] = {
        't_values': stats_dict['vs_zero']['t_values'],
        'p_values': stats_dict['vs_zero']['p_values'],
        'p_corrected': p_corr.reshape((n_colors, n_voxels)),
        'significant_mask': sig_mask
    }
    print(f"  Significant: {sig_mask.sum():,} / {sig_mask.size:,} ({100*sig_mask.sum()/sig_mask.size:.2f}%)")

    # Option B-1
    print(f"\n[2/3] Option B-1 (selectivity):")
    p_flat = stats_dict['selectivity']['p_values'].flatten()
    reject, p_corr, _, _ = multipletests(p_flat, alpha=alpha, method='fdr_bh')

    sig_mask = reject.reshape((n_colors, n_voxels))

    corrected['selectivity'] = {
        't_values': stats_dict['selectivity']['t_values'],
        'p_values': stats_dict['selectivity']['p_values'],
        'p_corrected': p_corr.reshape((n_colors, n_voxels)),
        'significant_mask': sig_mask
    }
    print(f"  Significant: {sig_mask.sum():,} / {sig_mask.size:,} ({100*sig_mask.sum()/sig_mask.size:.2f}%)")

    # Option B-2
    print(f"\n[3/3] Option B-2 (pairwise):")
    pairwise_corrected = []
    total_sig = 0

    for pair in stats_dict['pairwise']:
        reject, p_corr, _, _ = multipletests(pair['p_values'], alpha=alpha, method='fdr_bh')

        pairwise_corrected.append({
            'color1': pair['color1'],
            'color2': pair['color2'],
            'pair_name': pair['pair_name'],
            't_values': pair['t_values'],
            'p_values': pair['p_values'],
            'p_corrected': p_corr,
            'significant_mask': reject
        })

        total_sig += reject.sum()

    corrected['pairwise'] = pairwise_corrected
    total_tests = len(pairwise_corrected) * n_voxels
    print(f"  Significant: {total_sig:,} / {total_tests:,} ({100*total_sig/total_tests:.2f}%)")

    return corrected


def apply_t_threshold(stats_dict, threshold=5.0):
    """Apply absolute t-value threshold instead of FDR correction"""

    print(f"\n{'='*80}")
    print(f"T-value Threshold Selection (|t| > {threshold})")
    print(f"{'='*80}")
    print(f"  Note: Using absolute t-value threshold instead of FDR correction")
    print(f"  Rationale: Small sample size (N subjects) may have insufficient power for FDR")

    corrected = {}

    # Option A
    print(f"\n[1/3] Option A (vs 0):")
    t_values = stats_dict['vs_zero']['t_values']
    sig_mask = np.abs(t_values) > threshold

    n_colors, n_voxels = t_values.shape

    corrected['vs_zero'] = {
        't_values': t_values,
        'p_values': stats_dict['vs_zero']['p_values'],
        'p_corrected': None,  # Not applicable for t-threshold
        'significant_mask': sig_mask
    }
    print(f"  Significant: {sig_mask.sum():,} / {sig_mask.size:,} ({100*sig_mask.sum()/sig_mask.size:.2f}%)")
    print(f"  Max |t|: {np.abs(t_values).max():.2f}")

    # Option B-1
    print(f"\n[2/3] Option B-1 (selectivity):")
    t_values = stats_dict['selectivity']['t_values']
    sig_mask = np.abs(t_values) > threshold

    corrected['selectivity'] = {
        't_values': t_values,
        'p_values': stats_dict['selectivity']['p_values'],
        'p_corrected': None,
        'significant_mask': sig_mask
    }
    print(f"  Significant: {sig_mask.sum():,} / {sig_mask.size:,} ({100*sig_mask.sum()/sig_mask.size:.2f}%)")
    print(f"  Max |t|: {np.abs(t_values).max():.2f}")

    # Option B-2
    print(f"\n[3/3] Option B-2 (pairwise):")
    pairwise_corrected = []
    total_sig = 0
    max_t_overall = 0

    for pair in stats_dict['pairwise']:
        t_values = pair['t_values']
        sig_mask = np.abs(t_values) > threshold

        pairwise_corrected.append({
            'color1': pair['color1'],
            'color2': pair['color2'],
            'pair_name': pair['pair_name'],
            't_values': t_values,
            'p_values': pair['p_values'],
            'p_corrected': None,
            'significant_mask': sig_mask
        })

        total_sig += sig_mask.sum()
        max_t_overall = max(max_t_overall, np.abs(t_values).max())

    corrected['pairwise'] = pairwise_corrected
    total_tests = len(pairwise_corrected) * n_voxels
    print(f"  Significant: {total_sig:,} / {total_tests:,} ({100*total_sig/total_tests:.2f}%)")
    print(f"  Max |t|: {max_t_overall:.2f}")

    return corrected


def create_union_mask(corrected_stats):
    """Create union of significant voxels from all three methods"""

    print(f"\n{'='*80}")
    print(f"Creating Union of Significant Voxels")
    print(f"{'='*80}")

    # Get voxel count
    n_voxels = corrected_stats['vs_zero']['significant_mask'].shape[1]

    # Option A: any color significant
    mask_a = corrected_stats['vs_zero']['significant_mask'].any(axis=0)
    print(f"  Option A: {mask_a.sum():,} / {n_voxels:,} voxels")

    # Option B-1: any color selective
    mask_b1 = corrected_stats['selectivity']['significant_mask'].any(axis=0)
    print(f"  Option B-1: {mask_b1.sum():,} / {n_voxels:,} voxels")

    # Option B-2: any pair significant
    mask_b2 = np.zeros(n_voxels, dtype=bool)
    for pair in corrected_stats['pairwise']:
        mask_b2 |= pair['significant_mask']
    print(f"  Option B-2: {mask_b2.sum():,} / {n_voxels:,} voxels")

    # Union
    union_mask = mask_a | mask_b1 | mask_b2
    print(f"\n  ✅ UNION: {union_mask.sum():,} / {n_voxels:,} voxels ({100*union_mask.sum()/n_voxels:.1f}%)")

    # Overlap
    print(f"\n  Overlap:")
    all_three = mask_a & mask_b1 & mask_b2
    print(f"    All 3 methods: {all_three.sum():,} voxels")
    print(f"    A only: {(mask_a & ~mask_b1 & ~mask_b2).sum():,} voxels")
    print(f"    B-1 only: {(~mask_a & mask_b1 & ~mask_b2).sum():,} voxels")
    print(f"    B-2 only: {(~mask_a & ~mask_b1 & mask_b2).sum():,} voxels")

    return union_mask, {'vs_zero': mask_a, 'selectivity': mask_b1, 'pairwise': mask_b2}


# ============================================================================
# Classification & Reconstruction
# ============================================================================

def evaluate_union_voxels(group_amplitudes, union_mask):
    """
    Classification & reconstruction using union voxels
    Leave-one-subject-out CV
    """
    n_subjects, n_runs, n_colors, n_voxels = group_amplitudes.shape

    # Extract union voxels
    amplitudes_union = group_amplitudes[:, :, :, union_mask]
    n_union = amplitudes_union.shape[3]

    print(f"\n{'='*80}")
    print(f"Evaluating Union Voxels (Leave-One-Subject-Out CV)")
    print(f"{'='*80}")
    print(f"  Using {n_union} union voxels")

    results = []
    all_y_true = []
    all_y_pred = []
    all_recon_results = []

    for test_subj in range(n_subjects):
        train_subjs = [i for i in range(n_subjects) if i != test_subj]

        # Training
        X_train = amplitudes_union[train_subjs].reshape(-1, n_union)
        y_train = np.tile(np.arange(n_colors), len(train_subjs) * n_runs)

        # Test
        X_test = amplitudes_union[test_subj].reshape(-1, n_union)
        y_test = np.tile(np.arange(n_colors), n_runs)

        # Classification
        y_pred = diag_linear_predict(X_train, y_train, X_test)
        acc = np.mean(y_pred == y_test)

        all_y_true.extend(y_test)
        all_y_pred.extend(y_pred)

        # Reconstruction
        X_test_reshaped = X_test.reshape(n_runs, n_colors, n_union)
        recon_results, mean_error, _ = evaluate_reconstruction(X_test_reshaped)

        all_recon_results.extend(recon_results)

        # SNR
        snr_values = compute_voxel_snr(X_test_reshaped)
        mean_snr = np.mean(snr_values)

        results.append({
            'test_subject': test_subj + 1,
            'n_voxels': n_union,
            'classification_acc': acc,
            'reconstruction_error': mean_error,
            'mean_snr': mean_snr
        })

        print(f"  Subject {test_subj+1}: Acc={acc:.2%}, Recon={mean_error:.1f}°, SNR={mean_snr:.2f}")

    results_df = pd.DataFrame(results)

    print(f"\n  Mean Performance:")
    print(f"    Classification: {results_df['classification_acc'].mean():.2%} ± {results_df['classification_acc'].std():.2%}")
    print(f"    Reconstruction: {results_df['reconstruction_error'].mean():.1f}° ± {results_df['reconstruction_error'].std():.1f}°")

    detailed_results = {
        'y_true': np.array(all_y_true),
        'y_pred': np.array(all_y_pred),
        'recon_results': all_recon_results
    }

    return results_df, detailed_results


def evaluate_option_a_voxels(group_amplitudes, option_a_mask):
    """
    Classification & reconstruction using Option A voxels only
    Leave-one-subject-out CV
    """
    n_subjects, n_runs, n_colors, n_voxels = group_amplitudes.shape

    # Extract Option A voxels
    amplitudes_option_a = group_amplitudes[:, :, :, option_a_mask]
    n_option_a = amplitudes_option_a.shape[3]

    print(f"\n{'='*80}")
    print(f"Evaluating Option A Voxels Only (Leave-One-Subject-Out CV)")
    print(f"{'='*80}")
    print(f"  Using {n_option_a} Option A voxels")

    results = []
    all_y_true = []
    all_y_pred = []
    all_recon_results = []

    for test_subj in range(n_subjects):
        train_subjs = [i for i in range(n_subjects) if i != test_subj]

        # Training
        X_train = amplitudes_option_a[train_subjs].reshape(-1, n_option_a)
        y_train = np.tile(np.arange(n_colors), len(train_subjs) * n_runs)

        # Test
        X_test = amplitudes_option_a[test_subj].reshape(-1, n_option_a)
        y_test = np.tile(np.arange(n_colors), n_runs)

        # Classification
        y_pred = diag_linear_predict(X_train, y_train, X_test)
        acc = np.mean(y_pred == y_test)

        all_y_true.extend(y_test)
        all_y_pred.extend(y_pred)

        # Reconstruction
        X_test_reshaped = X_test.reshape(n_runs, n_colors, n_option_a)
        recon_results, mean_error, _ = evaluate_reconstruction(X_test_reshaped)

        all_recon_results.extend(recon_results)

        # SNR
        snr_values = compute_voxel_snr(X_test_reshaped)
        mean_snr = np.mean(snr_values)

        results.append({
            'test_subject': test_subj + 1,
            'n_voxels': n_option_a,
            'classification_acc': acc,
            'reconstruction_error': mean_error,
            'mean_snr': mean_snr
        })

        print(f"  Subject {test_subj+1}: Acc={acc:.2%}, Recon={mean_error:.1f}°, SNR={mean_snr:.2f}")

    results_df = pd.DataFrame(results)

    print(f"\n  Mean Performance:")
    print(f"    Classification: {results_df['classification_acc'].mean():.2%} ± {results_df['classification_acc'].std():.2%}")
    print(f"    Reconstruction: {results_df['reconstruction_error'].mean():.1f}° ± {results_df['reconstruction_error'].std():.1f}°")

    detailed_results = {
        'y_true': np.array(all_y_true),
        'y_pred': np.array(all_y_pred),
        'recon_results': all_recon_results
    }

    return results_df, detailed_results


def perform_pca_analysis(group_amplitudes, union_mask, n_components=50):
    """
    PCA analysis on union voxels

    Returns:
        pca_results: dict with PCA model, loadings, explained variance
    """
    n_subjects, n_runs, n_colors, n_voxels = group_amplitudes.shape

    # Extract union voxels
    amplitudes_union = group_amplitudes[:, :, :, union_mask]
    n_union = amplitudes_union.shape[3]

    print(f"\n{'='*80}")
    print(f"PCA Analysis on Union Voxels")
    print(f"{'='*80}")
    print(f"  Union voxels: {n_union}")
    print(f"  PCA components: {min(n_components, n_union)}")

    # Fit PCA on all data
    X_all = amplitudes_union.reshape(-1, n_union)  # (n_subjects * n_runs * n_colors, n_union)

    # Adjust n_components if needed
    n_components = min(n_components, n_union, X_all.shape[0])

    pca = PCA(n_components=n_components)
    X_transformed = pca.fit_transform(X_all)

    print(f"  Actual components fitted: {pca.n_components_}")
    print(f"  Explained variance (top 5): {pca.explained_variance_ratio_[:5]}")
    print(f"  Cumulative variance (top 5): {pca.explained_variance_ratio_[:5].sum():.2%}")

    # Evaluate with LOSO-CV
    print(f"\n  Evaluating with Leave-One-Subject-Out CV...")

    results = []

    for test_subj in range(n_subjects):
        train_subjs = [i for i in range(n_subjects) if i != test_subj]

        # Training
        X_train = amplitudes_union[train_subjs].reshape(-1, n_union)
        y_train = np.tile(np.arange(n_colors), len(train_subjs) * n_runs)

        # Fit PCA on training data
        pca_train = PCA(n_components=n_components)
        X_train_pca = pca_train.fit_transform(X_train)

        # Test
        X_test = amplitudes_union[test_subj].reshape(-1, n_union)
        y_test = np.tile(np.arange(n_colors), n_runs)
        X_test_pca = pca_train.transform(X_test)

        # Classification
        y_pred = diag_linear_predict(X_train_pca, y_train, X_test_pca)
        acc = np.mean(y_pred == y_test)

        results.append({
            'test_subject': test_subj + 1,
            'n_components': n_components,
            'classification_acc': acc
        })

        print(f"    Subject {test_subj+1}: Acc={acc:.2%}")

    results_df = pd.DataFrame(results)

    print(f"\n  Mean PCA Performance:")
    print(f"    Classification: {results_df['classification_acc'].mean():.2%} ± {results_df['classification_acc'].std():.2%}")

    pca_results = {
        'pca_model': pca,
        'loadings': pca.components_.T,  # (n_union, n_components)
        'explained_variance': pca.explained_variance_,
        'explained_variance_ratio': pca.explained_variance_ratio_,
        'cumulative_variance': np.cumsum(pca.explained_variance_ratio_),
        'performance_df': results_df
    }

    return pca_results


# ============================================================================
# Visualization
# ============================================================================

def visualize_pairwise_contrasts(corrected_stats, output_dir):
    """Visualize pairwise contrast grid (28 pairs for 8 colors)"""

    print(f"\n  Creating pairwise contrast grid...")

    pairwise = corrected_stats['pairwise']
    n_pairs = len(pairwise)
    n_voxels = pairwise[0]['t_values'].shape[0]

    # Create grid: 7 rows × 4 columns = 28 pairs
    ncols = 4
    nrows = int(np.ceil(n_pairs / ncols))

    fig, axes = plt.subplots(nrows, ncols, figsize=(16, nrows * 3))
    axes = axes.flatten()

    for idx, pair in enumerate(pairwise):
        ax = axes[idx]

        # Plot t-values
        voxel_indices = np.arange(n_voxels)
        colors = ['red' if sig else 'gray' for sig in pair['significant_mask']]

        ax.bar(voxel_indices, pair['t_values'], color=colors, alpha=0.7, edgecolor='none')
        ax.axhline(0, color='black', linewidth=0.5)
        ax.set_title(f"{pair['pair_name']}\n{pair['significant_mask'].sum()} sig voxels",
                     fontsize=10)
        ax.set_xlabel('Voxel', fontsize=8)
        ax.set_ylabel('t-value', fontsize=8)
        ax.tick_params(labelsize=7)
        ax.grid(axis='y', alpha=0.3)

    # Hide unused subplots
    for idx in range(n_pairs, len(axes)):
        axes[idx].axis('off')

    plt.suptitle('Pairwise Color Contrasts (Red = FDR-significant)',
                 fontsize=14, fontweight='bold')
    plt.tight_layout()

    fig_path = output_dir / 'figures' / 'pairwise_contrasts_grid.png'
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"  ✓ Saved: {fig_path}")


def visualize_union_breakdown(union_mask, breakdown, output_dir):
    """Visualize union voxel breakdown"""

    print(f"\n  Creating union breakdown plot...")

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Venn-like breakdown
    ax = axes[0, 0]
    labels = ['vs_zero', 'selectivity', 'pairwise', 'union']
    counts = [breakdown['vs_zero'].sum(),
              breakdown['selectivity'].sum(),
              breakdown['pairwise'].sum(),
              union_mask.sum()]

    ax.bar(labels, counts, alpha=0.7, edgecolor='black')
    ax.set_ylabel('Number of Voxels')
    ax.set_title('Significant Voxels per Method')
    ax.grid(axis='y', alpha=0.3)

    # Union voxel indices
    ax = axes[0, 1]
    union_indices = np.where(union_mask)[0]
    ax.scatter(union_indices, np.ones_like(union_indices), alpha=0.5, s=50)
    ax.set_xlabel('Voxel Index')
    ax.set_yticks([])
    ax.set_title(f'Union Voxels (N={len(union_indices)})')
    ax.grid(axis='x', alpha=0.3)

    # Overlap matrix
    ax = axes[1, 0]
    methods = ['A', 'B-1', 'B-2']
    masks = [breakdown['vs_zero'], breakdown['selectivity'], breakdown['pairwise']]
    overlap_matrix = np.zeros((3, 3))

    for i in range(3):
        for j in range(3):
            overlap_matrix[i, j] = (masks[i] & masks[j]).sum()

    im = ax.imshow(overlap_matrix, cmap='YlOrRd', aspect='auto')
    ax.set_xticks(range(3))
    ax.set_yticks(range(3))
    ax.set_xticklabels(methods)
    ax.set_yticklabels(methods)
    ax.set_title('Voxel Overlap Between Methods')

    for i in range(3):
        for j in range(3):
            ax.text(j, i, f'{int(overlap_matrix[i, j])}',
                   ha='center', va='center', fontsize=12)

    plt.colorbar(im, ax=ax)

    # Summary text
    ax = axes[1, 1]
    ax.axis('off')

    all_three = breakdown['vs_zero'] & breakdown['selectivity'] & breakdown['pairwise']
    a_only = breakdown['vs_zero'] & ~breakdown['selectivity'] & ~breakdown['pairwise']
    b1_only = ~breakdown['vs_zero'] & breakdown['selectivity'] & ~breakdown['pairwise']
    b2_only = ~breakdown['vs_zero'] & ~breakdown['selectivity'] & breakdown['pairwise']

    summary_text = f"""
Union Breakdown:

Total union voxels: {union_mask.sum()}

Exclusive contributions:
  - Option A only: {a_only.sum()}
  - Option B-1 only: {b1_only.sum()}
  - Option B-2 only: {b2_only.sum()}

Shared:
  - All 3 methods: {all_three.sum()}
  - A & B-1: {(breakdown['vs_zero'] & breakdown['selectivity'] & ~breakdown['pairwise']).sum()}
  - A & B-2: {(breakdown['vs_zero'] & ~breakdown['selectivity'] & breakdown['pairwise']).sum()}
  - B-1 & B-2: {(~breakdown['vs_zero'] & breakdown['selectivity'] & breakdown['pairwise']).sum()}
"""

    ax.text(0.1, 0.5, summary_text, fontsize=11, family='monospace',
           verticalalignment='center')

    plt.suptitle('Union Voxel Analysis', fontsize=14, fontweight='bold')
    plt.tight_layout()

    fig_path = output_dir / 'figures' / 'union_voxels_breakdown.png'
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"  ✓ Saved: {fig_path}")


def visualize_classification_reconstruction(detailed_results, output_dir, voxel_type='union'):
    """Create circular color space and confusion matrix"""

    print(f"\n  Creating classification & reconstruction plots ({voxel_type} voxels)...")

    # Circular color space - Custom visualization for group-level
    all_reconstructed_hues = []
    all_true_hues = []

    for result in detailed_results['recon_results']:
        # Each result contains arrays of reconstructed/true hues
        all_reconstructed_hues.extend(result['reconstructed_hues'])
        all_true_hues.extend(result['true_hues'])

    all_reconstructed_hues = np.array(all_reconstructed_hues)
    all_true_hues = np.array(all_true_hues)

    # Calculate reconstruction error
    errors = circular_diff_deg(all_reconstructed_hues, all_true_hues)
    mean_error = errors.mean()
    hit_rate_22_5 = np.mean(errors <= 22.5)
    hit_rate_45 = np.mean(errors <= 45.0)

    # Create circular plot
    fig = plt.figure(figsize=(12, 6))

    # Left: Circular color space
    ax1 = fig.add_subplot(1, 2, 1, projection='polar')
    ax1.set_theta_zero_location("E")
    ax1.set_theta_direction(1)
    ax1.set_rticks([])
    ax1.grid(alpha=0.25)

    r_true = 1.0
    r_pred = 0.75

    # Plot by color
    for color_idx in range(N_COLORS):
        color_name = f'color_{color_idx + 1}'
        true_hue = LABEL2HUE_DEG[color_name]
        true_rgb = get_stimulus_color_rgb(color_name)

        # True color at border
        ax1.scatter([np.deg2rad(true_hue)], [r_true], s=150,
                   color=true_rgb, edgecolor='k', linewidths=1.5, zorder=4)

        # Predictions for this color
        mask = all_true_hues == true_hue
        pred_hues = all_reconstructed_hues[mask]

        for pred_hue in pred_hues:
            ax1.scatter([np.deg2rad(pred_hue)], [r_pred], s=30,
                       color=true_rgb, alpha=0.5, zorder=3)

    ax1.set_ylim([0, 1.1])
    voxel_label = voxel_type.replace('_', ' ').title()
    ax1.set_title(f'{voxel_label} Voxels: Color Reconstruction\nMean error: {mean_error:.1f}°',
                  fontsize=12, fontweight='bold')

    # Right: Summary statistics
    ax2 = fig.add_subplot(1, 2, 2)
    ax2.axis('off')

    summary_text = f"""
    RECONSTRUCTION PERFORMANCE
    ═══════════════════════════

    Mean Error:     {mean_error:.1f}°
    Std Error:      {errors.std():.1f}°

    Hit Rates:
      ± 22.5°:      {hit_rate_22_5:.1%}
      ± 45.0°:      {hit_rate_45:.1%}

    Trials:         {len(errors):,}
    """

    ax2.text(0.1, 0.5, summary_text, fontsize=11, family='monospace',
             verticalalignment='center')

    plt.tight_layout()

    fig_path = output_dir / 'figures' / f'circular_color_space_{voxel_type}.png'
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"  ✓ Saved: {fig_path}")

    # Confusion matrix
    cm = confusion_matrix(detailed_results['y_true'], detailed_results['y_pred'])
    cm_normalized = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Raw counts
    ax = axes[0]
    im = ax.imshow(cm, cmap='Blues', aspect='auto')
    ax.set_xlabel('Predicted Color')
    ax.set_ylabel('True Color')
    ax.set_title('Confusion Matrix (Counts)')
    ax.set_xticks(range(8))
    ax.set_yticks(range(8))
    ax.set_xticklabels([f'C{i+1}' for i in range(8)])
    ax.set_yticklabels([f'C{i+1}' for i in range(8)])

    for i in range(8):
        for j in range(8):
            ax.text(j, i, f'{cm[i, j]}', ha='center', va='center',
                   color='white' if cm[i, j] > cm.max()/2 else 'black', fontsize=9)

    plt.colorbar(im, ax=ax)

    # Normalized
    ax = axes[1]
    im = ax.imshow(cm_normalized, cmap='Blues', aspect='auto', vmin=0, vmax=1)
    ax.set_xlabel('Predicted Color')
    ax.set_ylabel('True Color')
    ax.set_title('Confusion Matrix (Normalized)')
    ax.set_xticks(range(8))
    ax.set_yticks(range(8))
    ax.set_xticklabels([f'C{i+1}' for i in range(8)])
    ax.set_yticklabels([f'C{i+1}' for i in range(8)])

    for i in range(8):
        for j in range(8):
            ax.text(j, i, f'{cm_normalized[i, j]:.2f}', ha='center', va='center',
                   color='white' if cm_normalized[i, j] > 0.5 else 'black', fontsize=9)

    plt.colorbar(im, ax=ax)

    plt.suptitle(f'{voxel_label} Voxels: Classification Performance', fontsize=14, fontweight='bold')
    plt.tight_layout()

    fig_path = output_dir / 'figures' / f'confusion_matrix_{voxel_type}.png'
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"  ✓ Saved: {fig_path}")


def visualize_pca_results(pca_results, output_dir):
    """Visualize PCA results"""

    print(f"\n  Creating PCA visualizations...")

    # Figure 1: Explained variance
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Scree plot
    ax = axes[0]
    n_show = min(20, len(pca_results['explained_variance_ratio']))
    ax.bar(range(1, n_show + 1), pca_results['explained_variance_ratio'][:n_show],
           alpha=0.7, edgecolor='black')
    ax.set_xlabel('Principal Component')
    ax.set_ylabel('Explained Variance Ratio')
    ax.set_title('Scree Plot (Top 20 PCs)')
    ax.grid(axis='y', alpha=0.3)

    # Cumulative variance
    ax = axes[1]
    ax.plot(range(1, n_show + 1), pca_results['cumulative_variance'][:n_show],
            marker='o', linewidth=2)
    ax.axhline(0.9, color='r', linestyle='--', label='90% variance')
    ax.axhline(0.95, color='orange', linestyle='--', label='95% variance')
    ax.set_xlabel('Number of Components')
    ax.set_ylabel('Cumulative Explained Variance')
    ax.set_title('Cumulative Variance Explained')
    ax.legend()
    ax.grid(alpha=0.3)

    plt.suptitle('PCA: Explained Variance Analysis', fontsize=14, fontweight='bold')
    plt.tight_layout()

    fig_path = output_dir / 'figures' / 'pca_explained_variance.png'
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"  ✓ Saved: {fig_path}")

    # Figure 2: Loadings heatmap (top 10 PCs)
    n_pcs_show = min(10, pca_results['loadings'].shape[1])
    loadings_subset = pca_results['loadings'][:, :n_pcs_show]

    fig, ax = plt.subplots(figsize=(12, 8))

    im = ax.imshow(loadings_subset.T, aspect='auto', cmap='RdBu_r',
                   vmin=-np.abs(loadings_subset).max(),
                   vmax=np.abs(loadings_subset).max())

    ax.set_xlabel('Voxel Index')
    ax.set_ylabel('Principal Component')
    ax.set_title(f'PCA Loadings Heatmap (Top {n_pcs_show} PCs)')
    ax.set_yticks(range(n_pcs_show))
    ax.set_yticklabels([f'PC{i+1}' for i in range(n_pcs_show)])

    plt.colorbar(im, ax=ax, label='Loading')
    plt.tight_layout()

    fig_path = output_dir / 'figures' / 'pca_loadings_heatmap.png'
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"  ✓ Saved: {fig_path}")

    # Figure 3: Performance comparison
    perf_df = pca_results['performance_df']

    fig, ax = plt.subplots(figsize=(10, 6))

    subjects = perf_df['test_subject'].values
    acc = perf_df['classification_acc'].values

    ax.bar(subjects, acc, alpha=0.7, edgecolor='black')
    ax.axhline(acc.mean(), color='red', linestyle='--',
               label=f'Mean: {acc.mean():.2%}')
    ax.set_xlabel('Test Subject')
    ax.set_ylabel('Classification Accuracy')
    ax.set_title(f'PCA Classification Performance (N components = {perf_df["n_components"].iloc[0]})')
    ax.set_xticks(subjects)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()

    fig_path = output_dir / 'figures' / 'pca_classification_performance.png'
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"  ✓ Saved: {fig_path}")


# ============================================================================
# Main
# ============================================================================

def main():
    args = parse_args()

    print(f"\n{'='*80}")
    print(f"Comprehensive Group-Level Analysis")
    print(f"{'='*80}")
    print(f"ROI: {args.roi}")
    print(f"Timestamp: {args.timestamp}")
    print(f"Dataset: {args.dataset}")
    print(f"Subjects: {', '.join(args.subjects)} (N={len(args.subjects)})")

    if args.use_t_threshold:
        print(f"Selection method: |t| > {args.t_threshold}")
    else:
        print(f"Selection method: FDR correction (alpha={args.fdr_alpha})")

    # Output directory
    if args.output_dir is None:
        output_dir = Path(f"derivatives/group_level/{args.timestamp}/{args.roi}/comprehensive")
    else:
        output_dir = Path(args.output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / 'statistics').mkdir(exist_ok=True)
    (output_dir / 'figures').mkdir(exist_ok=True)
    (output_dir / 'performance').mkdir(exist_ok=True)

    print(f"Output: {output_dir}")

    # ========================================================================
    # Load data
    # ========================================================================
    print(f"\n{'='*80}")
    print(f"Loading Data")
    print(f"{'='*80}")

    group_amplitudes = load_group_amplitudes(args.roi, args.timestamp, args.dataset)

    # ========================================================================
    # Compute statistics
    # ========================================================================
    stats_dict = compute_three_statistical_tests(group_amplitudes)

    # ========================================================================
    # Voxel selection: FDR correction OR t-threshold
    # ========================================================================
    if args.use_t_threshold:
        corrected_stats = apply_t_threshold(stats_dict, threshold=args.t_threshold)
    else:
        corrected_stats = apply_fdr_correction(stats_dict, alpha=args.fdr_alpha)

    # ========================================================================
    # Create union mask
    # ========================================================================
    union_mask, breakdown = create_union_mask(corrected_stats)

    # ========================================================================
    # Classification & Reconstruction on union voxels
    # ========================================================================
    results_df_union, detailed_results_union = evaluate_union_voxels(group_amplitudes, union_mask)

    # ========================================================================
    # Classification & Reconstruction on Option A voxels only
    # ========================================================================
    option_a_mask = breakdown['vs_zero']
    results_df_option_a, detailed_results_option_a = evaluate_option_a_voxels(group_amplitudes, option_a_mask)

    # ========================================================================
    # PCA Analysis on union voxels
    # ========================================================================
    pca_results = perform_pca_analysis(group_amplitudes, union_mask, n_components=50)

    # ========================================================================
    # Save results
    # ========================================================================
    print(f"\n{'='*80}")
    print(f"Saving Results")
    print(f"{'='*80}")

    # Statistics
    np.savez(output_dir / 'statistics' / 'option_a_vs_zero.npz', **corrected_stats['vs_zero'])
    np.savez(output_dir / 'statistics' / 'option_b1_selectivity.npz', **corrected_stats['selectivity'])

    # Pairwise (save each pair)
    pairwise_dir = output_dir / 'statistics' / 'pairwise'
    pairwise_dir.mkdir(exist_ok=True)
    for pair in corrected_stats['pairwise']:
        np.savez(pairwise_dir / f"{pair['pair_name']}.npz",
                 color1=pair['color1'],
                 color2=pair['color2'],
                 t_values=pair['t_values'],
                 p_values=pair['p_values'],
                 p_corrected=pair['p_corrected'],
                 significant_mask=pair['significant_mask'])

    # Union mask
    np.savez(output_dir / 'statistics' / 'union_voxels.npz',
             union_mask=union_mask,
             **breakdown)

    # Performance - Union voxels
    results_df_union.to_csv(output_dir / 'performance' / 'classification_results_union.csv', index=False)

    # Performance - Option A voxels only
    results_df_option_a.to_csv(output_dir / 'performance' / 'classification_results_option_a.csv', index=False)

    # PCA performance
    pca_results['performance_df'].to_csv(output_dir / 'performance' / 'pca_performance.csv', index=False)

    # PCA results
    pca_dir = output_dir / 'pca'
    pca_dir.mkdir(exist_ok=True)
    np.savez(pca_dir / 'pca_results.npz',
             loadings=pca_results['loadings'],
             explained_variance=pca_results['explained_variance'],
             explained_variance_ratio=pca_results['explained_variance_ratio'],
             cumulative_variance=pca_results['cumulative_variance'])

    print(f"  ✓ Statistics saved")
    print(f"  ✓ Performance saved")
    print(f"  ✓ PCA results saved")

    # ========================================================================
    # Visualizations
    # ========================================================================
    print(f"\n{'='*80}")
    print(f"Creating Visualizations")
    print(f"{'='*80}")

    visualize_pairwise_contrasts(corrected_stats, output_dir)
    visualize_union_breakdown(union_mask, breakdown, output_dir)
    visualize_classification_reconstruction(detailed_results_union, output_dir, voxel_type='union')
    visualize_classification_reconstruction(detailed_results_option_a, output_dir, voxel_type='option_a')
    visualize_pca_results(pca_results, output_dir)

    # ========================================================================
    # Final summary
    # ========================================================================
    print(f"\n{'='*80}")
    print(f"Comprehensive Analysis Complete!")
    print(f"{'='*80}")
    print(f"\nKey Results:")
    print(f"  Union voxels: {union_mask.sum()} / {len(union_mask)} ({100*union_mask.sum()/len(union_mask):.1f}%)")
    print(f"  Option A voxels: {option_a_mask.sum()} / {len(option_a_mask)} ({100*option_a_mask.sum()/len(option_a_mask):.1f}%)")
    print(f"\n  Union Performance:")
    print(f"    Classification: {results_df_union['classification_acc'].mean():.2%} ± {results_df_union['classification_acc'].std():.2%}")
    print(f"    Reconstruction: {results_df_union['reconstruction_error'].mean():.1f}° ± {results_df_union['reconstruction_error'].std():.1f}°")
    print(f"\n  Option A Performance:")
    print(f"    Classification: {results_df_option_a['classification_acc'].mean():.2%} ± {results_df_option_a['classification_acc'].std():.2%}")
    print(f"    Reconstruction: {results_df_option_a['reconstruction_error'].mean():.1f}° ± {results_df_option_a['reconstruction_error'].std():.1f}°")
    print(f"\nOutput: {output_dir}")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    main()
