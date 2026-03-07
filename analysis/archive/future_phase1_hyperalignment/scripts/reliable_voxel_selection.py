#!/usr/bin/env python3
"""
Reliable Voxel Selection for Hyperalignment
============================================

User's insight: "Color decoding이 되는데 run마다 유의미한 애들만 뽑아서"

Strategy:
1. Select voxels that are:
   - Discriminative (good for color decoding)
   - Reliable (consistent across runs)
2. Use only these voxels for hyperalignment

This should solve the run consistency problem!

Author: Based on user's insight
Date: 2025-12-18
"""

import numpy as np
import sys
from pathlib import Path
from scipy.stats import f_oneway, pearsonr
from sklearn.feature_selection import f_classif

sys.path.insert(0, str(Path(__file__).parent))
from hyperalignment_core import load_amplitudes


def compute_voxel_discriminability(amplitudes):
    """
    Measure how well each voxel discriminates colors.

    Args:
        amplitudes: (n_runs, n_colors, n_voxels)

    Returns:
        F_scores: (n_voxels,) - higher = more discriminative
    """
    n_runs, n_colors, n_voxels = amplitudes.shape

    # Reshape to (n_samples, n_voxels) for ANOVA
    data = amplitudes.transpose(1, 0, 2).reshape(n_colors * n_runs, n_voxels)
    labels = np.repeat(range(n_colors), n_runs)

    # One-way ANOVA F-scores
    F_scores, p_values = f_classif(data, labels)

    return F_scores, p_values


def compute_voxel_reliability(amplitudes):
    """
    Measure run-to-run consistency for each voxel.

    Args:
        amplitudes: (n_runs, n_colors, n_voxels)

    Returns:
        reliability: (n_voxels,) - higher = more reliable
    """
    n_runs, n_colors, n_voxels = amplitudes.shape

    reliability = np.zeros(n_voxels)

    for voxel_idx in range(n_voxels):
        # For this voxel, get responses to each color across runs
        voxel_responses = amplitudes[:, :, voxel_idx]  # (n_runs, n_colors)

        # Compute run-to-run correlation (averaged across colors)
        correlations = []
        for color_idx in range(n_colors):
            color_pattern = voxel_responses[:, color_idx]  # (n_runs,)

            # Split-half reliability
            # Run 1-3 vs Run 4-6
            half1 = color_pattern[:n_runs//2].mean()
            half2 = color_pattern[n_runs//2:].mean()

            # Simplified: use variance across runs (inverse)
            variance = color_pattern.var()
            correlations.append(1.0 / (1.0 + variance))  # Higher variance = lower reliability

        # Average across colors
        reliability[voxel_idx] = np.mean(correlations)

    return reliability


def compute_voxel_reliability_advanced(amplitudes):
    """
    Better reliability measure: ICC or split-half correlation.

    Args:
        amplitudes: (n_runs, n_colors, n_voxels)

    Returns:
        reliability: (n_voxels,) - correlation-based reliability
    """
    n_runs, n_colors, n_voxels = amplitudes.shape

    reliability = np.zeros(n_voxels)

    for voxel_idx in range(n_voxels):
        # For this voxel, compute pattern similarity across runs
        patterns = amplitudes[:, :, voxel_idx]  # (n_runs, n_colors)

        # Compute all pairwise correlations between runs
        from scipy.spatial.distance import pdist, squareform

        # Correlation distance
        corr_dist = pdist(patterns, metric='correlation')
        correlations = 1 - corr_dist  # Convert distance to correlation

        # Mean correlation across all run pairs
        reliability[voxel_idx] = correlations.mean()

    return reliability


def select_reliable_discriminative_voxels(amplitudes, n_voxels=100,
                                         discriminability_weight=0.5,
                                         reliability_weight=0.5):
    """
    Select voxels that are both discriminative AND reliable.

    User's insight: "Run마다 유의미한 애들만 뽑아서"

    Args:
        amplitudes: (n_runs, n_colors, n_voxels)
        n_voxels: Number of voxels to select
        discriminability_weight: Weight for F-score
        reliability_weight: Weight for reliability

    Returns:
        selected_voxels: Indices of selected voxels
        scores: Combined scores
    """
    print(f"\n{'='*70}")
    print("Reliable & Discriminative Voxel Selection")
    print(f"{'='*70}")

    # 1. Discriminability
    F_scores, p_values = compute_voxel_discriminability(amplitudes)
    F_scores_norm = (F_scores - F_scores.min()) / (F_scores.max() - F_scores.min())

    print(f"\nDiscriminability (F-scores):")
    print(f"  Range: [{F_scores.min():.2f}, {F_scores.max():.2f}]")
    print(f"  Mean: {F_scores.mean():.2f}")
    print(f"  Voxels with p<0.05: {(p_values < 0.05).sum()}/{len(p_values)}")

    # 2. Reliability
    reliability = compute_voxel_reliability_advanced(amplitudes)
    reliability_norm = (reliability - reliability.min()) / (reliability.max() - reliability.min())

    print(f"\nReliability (run-to-run correlation):")
    print(f"  Range: [{reliability.min():.3f}, {reliability.max():.3f}]")
    print(f"  Mean: {reliability.mean():.3f}")
    print(f"  Voxels with r>0.3: {(reliability > 0.3).sum()}/{len(reliability)}")

    # 3. Combined score
    combined_score = (discriminability_weight * F_scores_norm +
                     reliability_weight * reliability_norm)

    # 4. Select top-n
    selected_voxels = np.argsort(combined_score)[-n_voxels:]

    print(f"\nSelected {n_voxels} voxels:")
    print(f"  Mean discriminability: {F_scores[selected_voxels].mean():.2f}")
    print(f"  Mean reliability: {reliability[selected_voxels].mean():.3f}")
    print(f"  Mean combined score: {combined_score[selected_voxels].mean():.3f}")

    # Compare with standard selection (discriminability only)
    standard_voxels = np.argsort(F_scores)[-n_voxels:]

    print(f"\nComparison with standard selection (discriminability only):")
    print(f"  Standard: discriminability={F_scores[standard_voxels].mean():.2f}, "
          f"reliability={reliability[standard_voxels].mean():.3f}")
    print(f"  Ours: discriminability={F_scores[selected_voxels].mean():.2f}, "
          f"reliability={reliability[selected_voxels].mean():.3f}")

    reliability_improvement = (reliability[selected_voxels].mean() -
                               reliability[standard_voxels].mean())

    if reliability_improvement > 0.05:
        print(f"\n✅ Our method improves reliability by {reliability_improvement:.3f}!")
    else:
        print(f"\n⚠️ Reliability improvement modest: {reliability_improvement:.3f}")

    return selected_voxels, {
        'F_scores': F_scores,
        'reliability': reliability,
        'combined_score': combined_score,
        'F_scores_norm': F_scores_norm,
        'reliability_norm': reliability_norm
    }


def test_run_consistency_improvement(subject_id, roi='V1', n_voxels=100):
    """
    Test if reliable voxel selection improves run-to-run consistency.
    """
    print(f"\n{'='*70}")
    print(f"Testing Reliable Voxel Selection: sub-{subject_id} {roi}")
    print(f"{'='*70}")

    amplitudes = load_amplitudes(subject_id, roi)
    n_runs, n_colors, n_voxels_total = amplitudes.shape

    # Method 1: Standard feature selection (discriminability only)
    F_scores, _ = compute_voxel_discriminability(amplitudes)
    standard_voxels = np.argsort(F_scores)[-n_voxels:]

    # Method 2: Reliable + discriminative
    reliable_voxels, scores = select_reliable_discriminative_voxels(
        amplitudes, n_voxels=n_voxels
    )

    # Compare run-to-run consistency
    print(f"\n{'='*70}")
    print("Run-to-Run Consistency Comparison")
    print(f"{'='*70}")

    colors = ['Red', 'Orange', 'Yellow', 'Chartreuse',
              'Green', 'Cyan', 'Blue', 'Magenta']

    # Standard voxels
    print(f"\n--- Standard Selection (discriminability only) ---")
    amp_standard = amplitudes[:, :, standard_voxels]

    corrs_standard = []
    for color_idx in range(n_colors):
        patterns = amp_standard[:, color_idx, :]  # (6, 100)

        # Pairwise correlations
        from scipy.spatial.distance import pdist
        corr_dist = pdist(patterns, metric='correlation')
        correlations = 1 - corr_dist
        mean_corr = correlations.mean()
        corrs_standard.append(mean_corr)

        print(f"  {colors[color_idx]:12s}: r={mean_corr:.3f}")

    print(f"  Mean: {np.mean(corrs_standard):.3f}")

    # Reliable voxels
    print(f"\n--- Reliable + Discriminative Selection ---")
    amp_reliable = amplitudes[:, :, reliable_voxels]

    corrs_reliable = []
    for color_idx in range(n_colors):
        patterns = amp_reliable[:, color_idx, :]

        corr_dist = pdist(patterns, metric='correlation')
        correlations = 1 - corr_dist
        mean_corr = correlations.mean()
        corrs_reliable.append(mean_corr)

        print(f"  {colors[color_idx]:12s}: r={mean_corr:.3f}")

    print(f"  Mean: {np.mean(corrs_reliable):.3f}")

    # Improvement
    improvement = np.mean(corrs_reliable) - np.mean(corrs_standard)
    improvement_pct = improvement / np.mean(corrs_standard) * 100

    print(f"\n{'='*70}")
    print("Result")
    print(f"{'='*70}")

    print(f"\nRun-to-run correlation:")
    print(f"  Standard: {np.mean(corrs_standard):.3f}")
    print(f"  Reliable: {np.mean(corrs_reliable):.3f}")
    print(f"  Improvement: {improvement:+.3f} ({improvement_pct:+.1f}%)")

    if improvement > 0.1:
        print(f"\n✅ SIGNIFICANT IMPROVEMENT!")
        print(f"   Reliable voxel selection increases consistency!")
        print(f"   → Hyperalignment now more feasible")
        verdict = "SUCCESS"
    elif improvement > 0.05:
        print(f"\n⚠️ MODERATE IMPROVEMENT")
        print(f"   Some benefit but modest")
        verdict = "MODEST"
    else:
        print(f"\n❌ MINIMAL IMPROVEMENT")
        print(f"   Reliable selection doesn't help much")
        verdict = "MINIMAL"

    return {
        'corrs_standard': corrs_standard,
        'corrs_reliable': corrs_reliable,
        'improvement': improvement,
        'verdict': verdict,
        'reliable_voxels': reliable_voxels,
        'scores': scores
    }


def run_all_subjects(subjects, roi='V1', n_voxels=100):
    """
    Test reliable voxel selection on all subjects.
    """
    print("\n" + "="*70)
    print(" RELIABLE VOXEL SELECTION: ALL SUBJECTS")
    print("="*70)

    all_results = {}

    for sub_id in subjects:
        try:
            results = test_run_consistency_improvement(sub_id, roi, n_voxels)
            all_results[f'sub-{sub_id}'] = results
        except Exception as e:
            print(f"\n❌ Error for sub-{sub_id}: {e}")

    # Summary
    print("\n" + "="*70)
    print(" SUMMARY")
    print("="*70)

    print("\nSubject    Standard    Reliable    Improvement    Verdict")
    print("-" * 70)

    for sub_id, results in all_results.items():
        std_corr = np.mean(results['corrs_standard'])
        rel_corr = np.mean(results['corrs_reliable'])
        improvement = results['improvement']
        verdict = results['verdict']

        print(f"{sub_id:10s} {std_corr:.3f}       {rel_corr:.3f}       "
              f"{improvement:+.3f}         {verdict}")

    # Overall
    all_improvements = [r['improvement'] for r in all_results.values()]
    mean_improvement = np.mean(all_improvements)

    print(f"\n{'='*70}")
    print("OVERALL ASSESSMENT")
    print(f"{'='*70}")

    print(f"\nMean improvement across subjects: {mean_improvement:+.3f}")

    if mean_improvement > 0.1:
        print(f"\n✅ RELIABLE VOXEL SELECTION WORKS!")
        print(f"   → Run-to-run consistency significantly improved")
        print(f"   → User's insight was correct!")
        print(f"   → Hyperalignment with reliable voxels should work")
    elif mean_improvement > 0.05:
        print(f"\n⚠️ MODERATE BENEFIT")
        print(f"   → Some improvement but not dramatic")
    else:
        print(f"\n❌ MINIMAL BENEFIT")
        print(f"   → Reliable selection doesn't solve the problem")

    return all_results


if __name__ == '__main__':
    HC_SUBJECTS = ['02', '03', '05', '06', '07']

    results = run_all_subjects(HC_SUBJECTS, roi='V1', n_voxels=100)
