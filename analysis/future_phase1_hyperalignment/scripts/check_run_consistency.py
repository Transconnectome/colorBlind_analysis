#!/usr/bin/env python3
"""
Check Run-to-Run Consistency
=============================

CRITICAL VALIDATION: Before using any multi-subject alignment,
we MUST check if run-averaging is justified.

Questions:
1. Are patterns consistent across runs within subject?
2. Is between-run variance << between-color variance?
3. Should we average across runs or treat separately?

Author: Response to critical feedback
Date: 2025-12-18
"""

import numpy as np
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import pearsonr
from scipy.spatial.distance import pdist, squareform

sys.path.insert(0, str(Path(__file__).parent))
from hyperalignment_core import load_amplitudes


def check_run_consistency(subject_id, roi='V1'):
    """
    Check within-subject run-to-run consistency for each color.
    """

    print(f"\n{'='*70}")
    print(f"Run Consistency Analysis: sub-{subject_id} {roi}")
    print(f"{'='*70}")

    # Load data
    amplitudes = load_amplitudes(subject_id, roi)  # (6, 8, p)
    n_runs, n_colors, n_voxels = amplitudes.shape

    colors = ['Red', 'Orange', 'Yellow', 'Chartreuse',
              'Green', 'Cyan', 'Blue', 'Magenta']

    # ========== Color-wise Analysis ==========
    print("\n--- Within-Color, Between-Run Correlations ---\n")

    color_correlations = []

    for color_idx, color_name in enumerate(colors):
        patterns = amplitudes[:, color_idx, :]  # (6 runs, p voxels)

        # Pairwise correlations between runs
        corrs = []
        for i in range(n_runs):
            for j in range(i+1, n_runs):
                r, p = pearsonr(patterns[i], patterns[j])
                corrs.append(r)

        mean_corr = np.mean(corrs)
        std_corr = np.std(corrs)
        min_corr = np.min(corrs)
        max_corr = np.max(corrs)

        color_correlations.append(mean_corr)

        print(f"{color_name:12s}: mean={mean_corr:.3f}, std={std_corr:.3f}, "
              f"range=[{min_corr:.3f}, {max_corr:.3f}]")

    # ========== Between-Color vs Within-Color Variance ==========
    print("\n--- Between-Color vs Within-Color Variance ---\n")

    # Run-averaged patterns
    patterns_avg = amplitudes.mean(axis=0)  # (8, p)

    # Between-color distances
    between_color_dist = pdist(patterns_avg, metric='correlation')

    # Within-color, between-run distances
    within_color_dists = []
    for color_idx in range(n_colors):
        patterns = amplitudes[:, color_idx, :]  # (6, p)
        within_dist = pdist(patterns, metric='correlation')
        within_color_dists.extend(within_dist)

    print(f"Between-color distance: {np.mean(between_color_dist):.3f} ± {np.std(between_color_dist):.3f}")
    print(f"Within-color distance:  {np.mean(within_color_dists):.3f} ± {np.std(within_color_dists):.3f}")

    ratio = np.mean(within_color_dists) / np.mean(between_color_dist)
    print(f"\nRatio (within/between): {ratio:.3f}")

    if ratio < 0.3:
        print("✅ Within-color variance << between-color variance")
        print("   → Run averaging is JUSTIFIED")
    elif ratio < 0.5:
        print("⚠️ Within-color variance moderate")
        print("   → Run averaging OK but some information loss")
    else:
        print("❌ Within-color variance high!")
        print("   → Run averaging may obscure important structure")

    # ========== Visualization ==========
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))

    # Plot 1: Run-to-run correlations by color
    ax = axes[0, 0]
    x = np.arange(len(colors))
    ax.bar(x, color_correlations, alpha=0.7, color='steelblue')
    ax.axhline(np.mean(color_correlations), color='red', linestyle='--',
               label=f'Mean: {np.mean(color_correlations):.3f}')
    ax.set_xlabel('Color', fontsize=12)
    ax.set_ylabel('Mean Correlation Across Runs', fontsize=12)
    ax.set_title(f'Run-to-Run Consistency (sub-{subject_id} {roi})',
                 fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(colors, rotation=45, ha='right')
    ax.set_ylim([0, 1])
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

    # Plot 2: Correlation matrices for a few colors
    ax = axes[0, 1]
    sample_colors = [0, 4, 7]  # Red, Green, Magenta
    all_corr_mats = []

    for color_idx in sample_colors:
        patterns = amplitudes[:, color_idx, :]
        corr_mat = np.corrcoef(patterns)
        all_corr_mats.append(corr_mat)

    avg_corr_mat = np.mean(all_corr_mats, axis=0)

    im = ax.imshow(avg_corr_mat, cmap='RdYlGn', vmin=0, vmax=1)
    ax.set_xlabel('Run', fontsize=12)
    ax.set_ylabel('Run', fontsize=12)
    ax.set_title('Average Run-Run Correlation\n(Red, Green, Magenta)',
                 fontsize=12, fontweight='bold')
    ax.set_xticks(range(6))
    ax.set_yticks(range(6))
    ax.set_xticklabels([f'R{i+1}' for i in range(6)])
    ax.set_yticklabels([f'R{i+1}' for i in range(6)])

    for i in range(6):
        for j in range(6):
            text = ax.text(j, i, f'{avg_corr_mat[i, j]:.2f}',
                          ha="center", va="center", color="black", fontsize=9)

    plt.colorbar(im, ax=ax)

    # Plot 3: Distribution comparison
    ax = axes[1, 0]
    ax.hist(between_color_dist, bins=30, alpha=0.5, label='Between-color',
            color='red', density=True)
    ax.hist(within_color_dists, bins=30, alpha=0.5, label='Within-color (across runs)',
            color='blue', density=True)
    ax.set_xlabel('Correlation Distance', fontsize=12)
    ax.set_ylabel('Density', fontsize=12)
    ax.set_title('Between-Color vs Within-Color Distances',
                 fontsize=12, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    # Plot 4: Run means and SEM
    ax = axes[1, 1]

    # For each color, show mean pattern magnitude across runs
    magnitudes = np.zeros((n_colors, n_runs))
    for color_idx in range(n_colors):
        for run_idx in range(n_runs):
            magnitudes[color_idx, run_idx] = np.linalg.norm(amplitudes[run_idx, color_idx, :])

    x = np.arange(n_colors)
    means = magnitudes.mean(axis=1)
    sems = magnitudes.std(axis=1) / np.sqrt(n_runs)

    ax.bar(x, means, yerr=sems, alpha=0.7, capsize=5, color='coral')
    ax.set_xlabel('Color', fontsize=12)
    ax.set_ylabel('Pattern Magnitude (L2 norm)', fontsize=12)
    ax.set_title('Pattern Magnitude Across Runs\n(mean ± SEM)',
                 fontsize=12, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(colors, rotation=45, ha='right')
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()

    return {
        'color_correlations': color_correlations,
        'mean_correlation': np.mean(color_correlations),
        'between_color_dist': np.mean(between_color_dist),
        'within_color_dist': np.mean(within_color_dists),
        'ratio': ratio,
        'figure': fig
    }


def check_all_subjects(subjects, roi='V1'):
    """
    Check run consistency for all subjects.
    """

    print("\n" + "="*70)
    print(" Run Consistency Check: All Subjects")
    print("="*70)

    OUTPUT_DIR = Path('analysis/hyperalignment/results')
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    FIGURES_DIR = Path('analysis/hyperalignment/figures')
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    all_results = {}

    for sub_id in subjects:
        try:
            results = check_run_consistency(sub_id, roi)
            all_results[f'sub-{sub_id}'] = results

            # Save figure
            fig_path = FIGURES_DIR / f'run_consistency_sub-{sub_id}_{roi}.png'
            results['figure'].savefig(fig_path, dpi=300, bbox_inches='tight')
            print(f"\n💾 Saved: {fig_path}")
            plt.close(results['figure'])

        except Exception as e:
            print(f"\n❌ Error for sub-{sub_id}: {e}")

    # Summary across subjects
    print("\n" + "="*70)
    print(" Summary Across All Subjects")
    print("="*70)

    print("\nSubject    Mean Corr  Within/Between Ratio  Assessment")
    print("-" * 70)

    for sub_id, results in all_results.items():
        mean_corr = results['mean_correlation']
        ratio = results['ratio']

        if ratio < 0.3 and mean_corr > 0.5:
            assessment = "✅ Averaging justified"
        elif ratio < 0.5 and mean_corr > 0.3:
            assessment = "⚠️ Averaging OK"
        else:
            assessment = "❌ Averaging problematic"

        print(f"{sub_id:10s} {mean_corr:.3f}      {ratio:.3f}                 {assessment}")

    # Overall recommendation
    print("\n" + "="*70)
    print(" Recommendation")
    print("="*70)

    mean_corrs = [r['mean_correlation'] for r in all_results.values()]
    ratios = [r['ratio'] for r in all_results.values()]

    overall_corr = np.mean(mean_corrs)
    overall_ratio = np.mean(ratios)

    print(f"\nOverall mean run-to-run correlation: {overall_corr:.3f}")
    print(f"Overall within/between ratio: {overall_ratio:.3f}")

    if overall_ratio < 0.3 and overall_corr > 0.5:
        print("\n✅ RUN AVERAGING IS JUSTIFIED")
        print("   → Can safely average across runs for each color")
        print("   → Between-color variance dominates within-color variance")
    elif overall_ratio < 0.5:
        print("\n⚠️ RUN AVERAGING IS ACCEPTABLE")
        print("   → Some information loss but reasonable")
        print("   → Consider modeling run effects if critical")
    else:
        print("\n❌ RUN AVERAGING IS PROBLEMATIC")
        print("   → High run-to-run variability")
        print("   → Should model run effects explicitly")
        print("   → Or use run as blocking factor")

    print("\n" + "="*70)
    print(" Implications for Alignment Methods")
    print("="*70)

    if overall_ratio < 0.5:
        print("\n✅ Procrustes on run-averaged patterns: VALID")
        print("   - Average (6, 8, p) → (8, p)")
        print("   - Align 8 color patterns")
        print("   - Clear interpretation")

        print("\n❌ Hyperalignment on flattened patterns: INVALID")
        print("   - (6, 8, p) → (48, p) violates assumptions")
        print("   - No temporal correspondence")
        print("   - Ignores run structure")
    else:
        print("\n⚠️ Need hierarchical model")
        print("   - Model: pattern = color_mean + run_effect + noise")
        print("   - Use residuals or mixed effects")

    return all_results


if __name__ == '__main__':
    HC_SUBJECTS = ['02', '03', '05', '06', '07']
    CVD_SUBJECTS = ['08', '09', '10']

    # Check HC subjects
    hc_results = check_all_subjects(HC_SUBJECTS, roi='V1')

    # Check CVD subjects
    cvd_results = check_all_subjects(CVD_SUBJECTS, roi='V1')
