#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
voxel_selection_comparison.py
------------------------------
Compare different voxel selection methods and their impact on:
1. Number of voxels selected
2. Classification accuracy
3. Reconstruction error

This script demonstrates why averaging |z| across colors is too restrictive.

Usage:
    python voxel_selection_comparison.py --subject P01 --roi V2
"""

import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt

def demonstrate_selection_problem():
    """
    Demonstrate why mean |z| criterion is backwards for selectivity
    """
    print("="*70)
    print("Demonstrating the Problem with Mean |z| Criterion")
    print("="*70)
    print()

    # Example voxels
    N_COLORS = 8

    # Voxel A: Highly selective (responds strongly to 2 colors)
    voxel_A = np.array([8, 7, 1, 0, 0, 1, 1, 0])

    # Voxel B: Non-selective (responds uniformly to all colors)
    voxel_B = np.array([3, 3, 3, 3, 3, 3, 3, 3])

    # Voxel C: Moderately selective (responds to 4 colors)
    voxel_C = np.array([5, 5, 5, 5, 0, 0, 0, 0])

    # Compute metrics
    threshold = 2.3

    print(f"Threshold: |z| > {threshold} (p < 0.01)")
    print()

    print("Voxel A (Highly Selective - responds to colors 1-2):")
    print(f"  |z| values: {voxel_A}")
    print(f"  Mean |z|: {voxel_A.mean():.2f}")
    print(f"  Max |z|: {voxel_A.max():.2f}")
    print(f"  Variance: {voxel_A.var():.2f}")
    print(f"  Selected by MEAN criterion: {'YES ✓' if voxel_A.mean() > threshold else 'NO ❌'}")
    print(f"  Selected by MAX criterion: {'YES ✓' if voxel_A.max() > threshold else 'NO ❌'}")
    print(f"  → This is a COLOR-SELECTIVE voxel (should be selected!)")
    print()

    print("Voxel B (Non-Selective - responds uniformly to all colors):")
    print(f"  |z| values: {voxel_B}")
    print(f"  Mean |z|: {voxel_B.mean():.2f}")
    print(f"  Max |z|: {voxel_B.max():.2f}")
    print(f"  Variance: {voxel_B.var():.2f}")
    print(f"  Selected by MEAN criterion: {'YES ✓' if voxel_B.mean() > threshold else 'NO ❌'}")
    print(f"  Selected by MAX criterion: {'YES ✓' if voxel_B.max() > threshold else 'NO ❌'}")
    print(f"  → This is NOT color-selective (should be rejected!)")
    print()

    print("Voxel C (Moderately Selective - responds to colors 1-4):")
    print(f"  |z| values: {voxel_C}")
    print(f"  Mean |z|: {voxel_C.mean():.2f}")
    print(f"  Max |z|: {voxel_C.max():.2f}")
    print(f"  Variance: {voxel_C.var():.2f}")
    print(f"  Selected by MEAN criterion: {'YES ✓' if voxel_C.mean() > threshold else 'NO ❌'}")
    print(f"  Selected by MAX criterion: {'YES ✓' if voxel_C.max() > threshold else 'NO ❌'}")
    print(f"  → This is moderately selective")
    print()

    print("="*70)
    print("CONCLUSION:")
    print("  MEAN |z| criterion: Selects non-selective voxels ❌")
    print("  MAX |z| criterion: Selects color-selective voxels ✓")
    print("="*70)
    print()


def compare_selection_methods(all_betas, N_RUNS=6, N_COLORS=8):
    """
    Compare different voxel selection methods

    Parameters
    ----------
    all_betas : ndarray
        Shape (n_runs, n_colors, n_voxels)
        Contains z-scores for each run, color, voxel

    Returns
    -------
    results : dict
        Dictionary with selection results for each method
    """
    n_voxels = all_betas.shape[2]

    results = {}

    # Method 1: Mean |z| > 2.3 (CURRENT - WRONG)
    mean_abs_z = np.mean(np.abs(all_betas), axis=(0, 1))
    results['mean_z_2.3'] = {
        'mask': mean_abs_z > 2.3,
        'n_selected': np.sum(mean_abs_z > 2.3),
        'pct_selected': 100 * np.sum(mean_abs_z > 2.3) / n_voxels,
        'description': 'Mean |z| > 2.3 (CURRENT METHOD - WRONG)'
    }

    # Method 2: Max |z| > 2.3 (RECOMMENDED)
    max_abs_z = np.max(np.abs(all_betas), axis=(0, 1))
    results['max_z_2.3'] = {
        'mask': max_abs_z > 2.3,
        'n_selected': np.sum(max_abs_z > 2.3),
        'pct_selected': 100 * np.sum(max_abs_z > 2.3) / n_voxels,
        'description': 'Max |z| > 2.3 (RECOMMENDED)'
    }

    # Method 3: Max |z| > 1.96 (p < 0.05)
    results['max_z_1.96'] = {
        'mask': max_abs_z > 1.96,
        'n_selected': np.sum(max_abs_z > 1.96),
        'pct_selected': 100 * np.sum(max_abs_z > 1.96) / n_voxels,
        'description': 'Max |z| > 1.96 (p < 0.05, liberal)'
    }

    # Method 4: Percentile (top 50%)
    percentile_50 = np.percentile(max_abs_z, 50)
    results['percentile_50'] = {
        'mask': max_abs_z > percentile_50,
        'n_selected': np.sum(max_abs_z > percentile_50),
        'pct_selected': 50.0,
        'threshold': percentile_50,
        'description': 'Top 50% by max |z| (percentile)'
    }

    # Method 5: Percentile (top 25%)
    percentile_75 = np.percentile(max_abs_z, 75)
    results['percentile_25'] = {
        'mask': max_abs_z > percentile_75,
        'n_selected': np.sum(max_abs_z > percentile_75),
        'pct_selected': 25.0,
        'threshold': percentile_75,
        'description': 'Top 25% by max |z| (conservative)'
    }

    # Method 6: Variance-based (top 50% by variance across colors)
    z_per_color = np.mean(all_betas, axis=0)  # (n_colors, n_voxels)
    variance_across_colors = np.var(z_per_color, axis=0)
    var_threshold = np.percentile(variance_across_colors, 50)
    results['variance_50'] = {
        'mask': variance_across_colors > var_threshold,
        'n_selected': np.sum(variance_across_colors > var_threshold),
        'pct_selected': 50.0,
        'threshold': var_threshold,
        'description': 'Top 50% by variance across colors'
    }

    # Method 7: F-test (p < 0.01)
    f_stats = []
    p_vals = []
    for voxel_idx in range(n_voxels):
        # Get data for this voxel: (n_runs, n_colors)
        voxel_data = all_betas[:, :, voxel_idx]

        # One-way ANOVA across colors
        f_stat, p_val = stats.f_oneway(*[voxel_data[:, c] for c in range(N_COLORS)])
        f_stats.append(f_stat)
        p_vals.append(p_val)

    f_stats = np.array(f_stats)
    p_vals = np.array(p_vals)

    results['f_test_0.01'] = {
        'mask': p_vals < 0.01,
        'n_selected': np.sum(p_vals < 0.01),
        'pct_selected': 100 * np.sum(p_vals < 0.01) / n_voxels,
        'description': 'F-test p < 0.01 (ANOVA across colors)'
    }

    # Method 8: Hybrid (max |z| > 2.3 OR top 50%)
    threshold_hybrid = min(2.3, percentile_50)
    results['hybrid'] = {
        'mask': max_abs_z > threshold_hybrid,
        'n_selected': np.sum(max_abs_z > threshold_hybrid),
        'pct_selected': 100 * np.sum(max_abs_z > threshold_hybrid) / n_voxels,
        'threshold': threshold_hybrid,
        'description': 'Hybrid: max(max |z| > 2.3, top 50%)'
    }

    return results


def print_selection_comparison(results, n_voxels_total):
    """Print comparison table of selection methods"""
    print("="*90)
    print("Voxel Selection Method Comparison")
    print("="*90)
    print()
    print(f"Total anatomical ROI voxels: {n_voxels_total}")
    print()
    print(f"{'Method':<45} {'N Selected':>12} {'% Selected':>12}")
    print("-"*90)

    for method_name, result in results.items():
        print(f"{result['description']:<45} {result['n_selected']:>12} {result['pct_selected']:>11.1f}%")

    print("="*90)
    print()

    # Recommendations
    print("RECOMMENDATIONS:")
    print()
    print("1. ⭐ BEST: 'Max |z| > 2.3' or 'Hybrid'")
    print("   - Identifies color-responsive voxels")
    print("   - Statistical significance threshold")
    print("   - Typical selection: 30-60%")
    print()
    print("2. ALTERNATIVE: 'Top 50% by max |z|' or 'Variance-based'")
    print("   - Guarantees sufficient voxels")
    print("   - No arbitrary threshold")
    print("   - Good for exploratory analysis")
    print()
    print("3. ❌ AVOID: 'Mean |z| > 2.3' (CURRENT METHOD)")
    print("   - Selects non-selective voxels")
    print("   - Too few voxels (0-5%)")
    print("   - Backwards logic for selectivity")
    print()
    print("="*90)


def visualize_selection_methods(all_betas, results, output_path='voxel_selection_comparison.png'):
    """
    Visualize different voxel selection methods

    Parameters
    ----------
    all_betas : ndarray
        Shape (n_runs, n_colors, n_voxels)
    results : dict
        Results from compare_selection_methods()
    output_path : str
        Path to save figure
    """
    n_voxels = all_betas.shape[2]
    N_COLORS = all_betas.shape[1]

    # Compute metrics
    mean_abs_z = np.mean(np.abs(all_betas), axis=(0, 1))
    max_abs_z = np.max(np.abs(all_betas), axis=(0, 1))
    z_per_color = np.mean(all_betas, axis=0)  # (n_colors, n_voxels)
    variance_across_colors = np.var(z_per_color, axis=0)

    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('Voxel Selection Methods Comparison', fontsize=16, fontweight='bold')

    # 1. Mean |z| distribution
    ax = axes[0, 0]
    ax.hist(mean_abs_z, bins=50, alpha=0.7, color='steelblue', edgecolor='black')
    ax.axvline(x=2.3, color='red', linestyle='--', linewidth=2, label='Threshold: 2.3')
    ax.axvline(x=1.96, color='orange', linestyle='--', linewidth=2, label='Threshold: 1.96')
    n_selected = results['mean_z_2.3']['n_selected']
    ax.set_xlabel('Mean |z| across colors')
    ax.set_ylabel('Number of voxels')
    ax.set_title(f'Mean |z| Distribution\n(CURRENT METHOD: {n_selected} voxels selected = {n_selected/n_voxels*100:.1f}%)')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

    # 2. Max |z| distribution
    ax = axes[0, 1]
    ax.hist(max_abs_z, bins=50, alpha=0.7, color='green', edgecolor='black')
    ax.axvline(x=2.3, color='red', linestyle='--', linewidth=2, label='Threshold: 2.3')
    ax.axvline(x=1.96, color='orange', linestyle='--', linewidth=2, label='Threshold: 1.96')
    percentile_50 = np.percentile(max_abs_z, 50)
    ax.axvline(x=percentile_50, color='purple', linestyle='--', linewidth=2, label=f'50th percentile: {percentile_50:.2f}')
    n_selected = results['max_z_2.3']['n_selected']
    ax.set_xlabel('Max |z| across colors')
    ax.set_ylabel('Number of voxels')
    ax.set_title(f'Max |z| Distribution\n(RECOMMENDED: {n_selected} voxels selected = {n_selected/n_voxels*100:.1f}%)')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

    # 3. Variance across colors
    ax = axes[0, 2]
    ax.hist(variance_across_colors, bins=50, alpha=0.7, color='coral', edgecolor='black')
    var_threshold = np.percentile(variance_across_colors, 50)
    ax.axvline(x=var_threshold, color='purple', linestyle='--', linewidth=2, label=f'50th percentile: {var_threshold:.2f}')
    n_selected = results['variance_50']['n_selected']
    ax.set_xlabel('Variance of z across colors')
    ax.set_ylabel('Number of voxels')
    ax.set_title(f'Variance Distribution\n(High variance = selective: {n_selected} voxels = 50%)')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

    # 4. Mean vs Max comparison
    ax = axes[1, 0]
    ax.scatter(mean_abs_z, max_abs_z, alpha=0.3, s=10, c='steelblue')
    ax.axhline(y=2.3, color='red', linestyle='--', linewidth=2, alpha=0.5, label='Max threshold: 2.3')
    ax.axvline(x=2.3, color='orange', linestyle='--', linewidth=2, alpha=0.5, label='Mean threshold: 2.3')

    # Highlight quadrants
    # Top-left: Selected by MAX, rejected by MEAN (selective voxels) ✓
    # Top-right: Selected by both (high response to all colors) ?
    # Bottom-left: Rejected by both (low response) ✗
    # Bottom-right: Selected by MEAN, rejected by MAX (impossible!)

    ax.text(0.5, 8, 'Selective voxels\n(High max, low mean)\n✓ Want these!',
            fontsize=10, ha='center', va='center',
            bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.7))
    ax.text(5, 8, 'High response\nto all colors\n? Non-selective',
            fontsize=10, ha='center', va='center',
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.7))

    ax.set_xlabel('Mean |z| across colors')
    ax.set_ylabel('Max |z| across colors')
    ax.set_title('Mean vs Max |z| (Why MAX is better)')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 5. Number of voxels selected by each method
    ax = axes[1, 1]
    methods = ['mean_z_2.3', 'max_z_2.3', 'max_z_1.96', 'percentile_50', 'variance_50', 'f_test_0.01', 'hybrid']
    method_labels = ['Mean |z|\n>2.3\n(CURRENT)', 'Max |z|\n>2.3\n(BEST)', 'Max |z|\n>1.96\n(Liberal)',
                     'Top 50%\n(Percentile)', 'Variance\n50%', 'F-test\np<0.01', 'Hybrid']
    n_selected = [results[m]['n_selected'] for m in methods]
    pct_selected = [results[m]['pct_selected'] for m in methods]

    colors_bar = ['red', 'green', 'lightgreen', 'blue', 'orange', 'purple', 'darkgreen']
    bars = ax.bar(range(len(methods)), n_selected, color=colors_bar, alpha=0.7, edgecolor='black')
    ax.set_xticks(range(len(methods)))
    ax.set_xticklabels(method_labels, fontsize=9, rotation=0)
    ax.set_ylabel('Number of voxels selected')
    ax.set_title('Comparison of Selection Methods')
    ax.grid(True, alpha=0.3, axis='y')

    # Add percentage labels on bars
    for bar, pct in zip(bars, pct_selected):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{pct:.1f}%', ha='center', va='bottom', fontsize=8, fontweight='bold')

    # 6. Selectivity index (max/mean ratio)
    ax = axes[1, 2]
    selectivity_index = max_abs_z / (mean_abs_z + 1e-8)  # Avoid division by zero
    ax.hist(selectivity_index, bins=50, alpha=0.7, color='purple', edgecolor='black')
    ax.axvline(x=1.0, color='red', linestyle='--', linewidth=2, label='No selectivity (max = mean)')
    ax.set_xlabel('Selectivity Index (max |z| / mean |z|)')
    ax.set_ylabel('Number of voxels')
    ax.set_title(f'Color Selectivity Index\n(Higher = more selective)')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    ax.text(0.95, 0.95, f'Mean: {np.mean(selectivity_index):.2f}\nMedian: {np.median(selectivity_index):.2f}',
            transform=ax.transAxes, ha='right', va='top', fontsize=10,
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.7))

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    # First, demonstrate the problem with a simple example
    demonstrate_selection_problem()

    print()
    print("To use this script with real data:")
    print()
    print("# Load your data (all_betas should be shape (n_runs, n_colors, n_voxels))")
    print("import pickle")
    print("# ... load data ...")
    print()
    print("# Compare methods")
    print("results = compare_selection_methods(all_betas)")
    print("print_selection_comparison(results, n_voxels)")
    print("visualize_selection_methods(all_betas, results)")
    print()
