#!/usr/bin/env python3
"""
Comprehensive Evaluation with Noise Ceiling Analysis

Extends baseline evaluation with:
1. Split-half reliability (within-subject noise ceiling)
2. LOSO inter-subject noise ceiling
3. Performance as % of ceiling
4. Comprehensive visualizations

Usage:
    python evaluate_with_noise_ceiling.py

Inputs:
    ../../phase1_preprocess_decoding/results/baseline/sub-{ID}/{ROI}/amplitudes_*.npy

Outputs:
    results/noise_ceiling/evaluation_with_ceiling.json
    results/noise_ceiling/visualizations/*.png

Date: 2026-01-30
"""

import numpy as np
from pathlib import Path
import json
import sys
from scipy.stats import spearmanr
import matplotlib.pyplot as plt

# Add utils to path
script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(script_dir / 'utils'))

from noise_ceiling import (
    compute_split_half_reliability,
    compute_split_half_odd_even,
    compute_loso_noise_ceiling,
    visualize_noise_ceiling,
    visualize_split_half_distribution,
    visualize_odd_even_rdms
)
from crossnobis_ldw import compute_crossnobis_rdms_per_run

# Configuration
SUBJECTS = [f"{i:02d}" for i in range(1, 11)]
ROIS = ['V1', 'V2', 'V3', 'hV4']
BASE_DIR = Path(__file__).parent.parent.parent / "phase1_preprocess_decoding" / "results" / "baseline"
OUTPUT_DIR = Path(__file__).parent / "results" / "noise_ceiling"


def compute_rdm_correlation_per_run(amplitudes):
    """
    Compute RDM per run using Pearson correlation

    Args:
        amplitudes: (n_runs, n_colors, n_voxels)

    Returns:
        rdms: (n_runs, n_colors, n_colors) - RDM per run
    """
    n_runs, n_colors, n_voxels = amplitudes.shape

    rdms = np.zeros((n_runs, n_colors, n_colors))

    for r in range(n_runs):
        patterns = amplitudes[r]  # (n_colors, n_voxels)
        corr_matrix = np.corrcoef(patterns)
        rdm = 1 - corr_matrix
        rdms[r] = rdm

    return rdms


def rdm_reliability_spearman(rdms):
    """
    Compute RDM reliability as mean Spearman correlation across run pairs

    Args:
        rdms: (n_runs, n_colors, n_colors)

    Returns:
        reliability: float - Mean pairwise correlation
    """
    n_runs, n_colors, _ = rdms.shape

    # Upper triangle indices
    triu_idx = np.triu_indices(n_colors, k=1)

    # Pairwise correlations
    correlations = []
    for i in range(n_runs):
        for j in range(i+1, n_runs):
            vec_i = rdms[i][triu_idx]
            vec_j = rdms[j][triu_idx]

            r, _ = spearmanr(vec_i, vec_j)
            correlations.append(r)

    return np.mean(correlations)


def decode_loro(amplitudes):
    """
    Leave-one-run-out decoding

    Args:
        amplitudes: (n_runs, n_colors, n_voxels)

    Returns:
        accuracy: float - Classification accuracy
    """
    n_runs, n_colors, n_voxels = amplitudes.shape

    correct = 0
    total = 0

    for test_run in range(n_runs):
        # Training runs
        train_runs = [r for r in range(n_runs) if r != test_run]
        train_mean = amplitudes[train_runs].mean(axis=0)  # (n_colors, n_voxels)

        # Test patterns
        test_patterns = amplitudes[test_run]

        # Classify each color
        for true_color in range(n_colors):
            test_pattern = test_patterns[true_color]

            # Compute distances to all training templates
            distances = np.linalg.norm(train_mean - test_pattern, axis=1)

            # Predict
            predicted_color = np.argmin(distances)

            if predicted_color == true_color:
                correct += 1
            total += 1

    accuracy = correct / total
    return accuracy


def evaluate_single_roi_with_ceiling(subject, roi, verbose=True):
    """
    Evaluate single subject-ROI pair with noise ceiling

    Returns:
        dict or None: Metrics if successful, None if failed
    """
    result_dir = BASE_DIR / f"sub-{subject}" / roi

    # Check files exist
    raw_path = result_dir / "amplitudes_raw.npy"
    procrustes_path = result_dir / "amplitudes_procrustes.npy"
    disparity_path = result_dir / "procrustes_disparities.npy"

    if not raw_path.exists():
        if verbose:
            print(f"⚠️  Skip: sub-{subject}/{roi} (amplitudes_raw.npy missing)")
        return None

    if not procrustes_path.exists():
        if verbose:
            print(f"⚠️  Skip: sub-{subject}/{roi} (amplitudes_procrustes.npy missing)")
        return None

    try:
        # Load data
        amplitudes_raw = np.load(raw_path)
        amplitudes_aligned = np.load(procrustes_path)

        n_runs, n_colors, n_voxels = amplitudes_raw.shape

        # === BEFORE Procrustes ===
        rdms_corr_before = compute_rdm_correlation_per_run(amplitudes_raw)
        rdm_corr_reliability_before = rdm_reliability_spearman(rdms_corr_before)

        rdms_crossnobis_before, shrinkages = compute_crossnobis_rdms_per_run(amplitudes_raw)
        rdm_crossnobis_reliability_before = rdm_reliability_spearman(rdms_crossnobis_before)

        decoding_accuracy_before = decode_loro(amplitudes_raw)

        # === Procrustes Disparity ===
        if disparity_path.exists():
            disparities = np.load(disparity_path)
            mean_disparity = float(np.mean(disparities))
        else:
            mean_disparity = np.nan

        # === AFTER Procrustes ===
        rdms_corr_after = compute_rdm_correlation_per_run(amplitudes_aligned)
        rdm_corr_reliability_after = rdm_reliability_spearman(rdms_corr_after)

        rdms_crossnobis_after, _ = compute_crossnobis_rdms_per_run(amplitudes_aligned)
        rdm_crossnobis_reliability_after = rdm_reliability_spearman(rdms_crossnobis_after)

        decoding_accuracy_after = decode_loro(amplitudes_aligned)

        # === NOISE CEILING (Split-Half) ===
        # Compute on Procrustes-aligned data (best estimate)

        # Random split-half (1000 iterations)
        split_half_results = compute_split_half_reliability(
            amplitudes_aligned,
            n_iterations=1000,
            metric='correlation'
        )

        # Odd/even split-half (deterministic)
        odd_even_results = compute_split_half_odd_even(
            amplitudes_aligned,
            metric='correlation'
        )

        noise_ceiling_upper = split_half_results['corrected']
        noise_ceiling_ci_lower = split_half_results['ci_lower']
        noise_ceiling_ci_upper = split_half_results['ci_upper']

        # Performance as % of ceiling
        pct_of_ceiling_before = (rdm_corr_reliability_before / noise_ceiling_upper * 100) if noise_ceiling_upper > 0 else 0
        pct_of_ceiling_after = (rdm_corr_reliability_after / noise_ceiling_upper * 100) if noise_ceiling_upper > 0 else 0

        # === Improvements ===
        rdm_corr_improvement = rdm_corr_reliability_after - rdm_corr_reliability_before
        rdm_crossnobis_improvement = rdm_crossnobis_reliability_after - rdm_crossnobis_reliability_before
        decoding_improvement = decoding_accuracy_after - decoding_accuracy_before

        # Compile results
        results = {
            # Metadata
            'subject': subject,
            'roi': roi,
            'n_voxels': int(n_voxels),
            'n_runs': int(n_runs),

            # Before Procrustes
            'rdm_correlation_before': float(rdm_corr_reliability_before),
            'rdm_crossnobis_before': float(rdm_crossnobis_reliability_before),
            'decoding_accuracy_before': float(decoding_accuracy_before),

            # Procrustes
            'procrustes_disparity': float(mean_disparity),
            'shrinkage': float(np.mean(shrinkages)),

            # After Procrustes
            'rdm_correlation_after': float(rdm_corr_reliability_after),
            'rdm_crossnobis_after': float(rdm_crossnobis_reliability_after),
            'decoding_accuracy_after': float(decoding_accuracy_after),

            # Improvements
            'rdm_correlation_improvement': float(rdm_corr_improvement),
            'rdm_crossnobis_improvement': float(rdm_crossnobis_improvement),
            'decoding_improvement': float(decoding_improvement),

            # Noise Ceiling - Random Split
            'noise_ceiling_upper': float(noise_ceiling_upper),
            'noise_ceiling_ci_lower': float(noise_ceiling_ci_lower),
            'noise_ceiling_ci_upper': float(noise_ceiling_ci_upper),
            'split_half_raw': float(split_half_results['raw']),

            # Noise Ceiling - Odd/Even Split (NEW)
            'noise_ceiling_odd_even': float(odd_even_results['corrected']),
            'split_half_odd_even_raw': float(odd_even_results['raw']),
            'n_odd_runs': int(odd_even_results['n_odd']),
            'n_even_runs': int(odd_even_results['n_even']),
            'split_half_method_difference': float(abs(
                split_half_results['corrected'] - odd_even_results['corrected']
            )),

            # Performance relative to ceiling
            'pct_of_ceiling_before': float(pct_of_ceiling_before),
            'pct_of_ceiling_after': float(pct_of_ceiling_after),

            # Split-half correlations for visualization
            'split_half_correlations': split_half_results['all_correlations'],
            'odd_even_rdms': {
                'odd': odd_even_results['rdm_odd'].tolist(),
                'even': odd_even_results['rdm_even'].tolist()
            }
        }

        if verbose:
            print(f"✓ sub-{subject}/{roi}: "
                  f"RDM {rdm_corr_reliability_before:.3f}→{rdm_corr_reliability_after:.3f} "
                  f"({pct_of_ceiling_after:.1f}% of ceiling {noise_ceiling_upper:.3f})")

        return results

    except Exception as e:
        print(f"❌ sub-{subject}/{roi}: {e}")
        import traceback
        traceback.print_exc()
        return None


def compute_group_loso_ceiling(all_results, roi):
    """
    Compute LOSO noise ceiling across subjects for a given ROI

    Args:
        all_results: dict of results keyed by 'sub-XX_ROI'
        roi: ROI name

    Returns:
        loso_results: dict with lower/upper bounds and per-subject scores
    """
    # Collect amplitudes for all subjects in this ROI
    amplitudes_dict = {}

    for subject in SUBJECTS:
        key = f"sub-{subject}_{roi}"
        if key not in all_results:
            continue

        # Load amplitudes
        result_dir = BASE_DIR / f"sub-{subject}" / roi
        procrustes_path = result_dir / "amplitudes_procrustes.npy"

        if procrustes_path.exists():
            amplitudes = np.load(procrustes_path)
            amplitudes_dict[subject] = amplitudes

    if len(amplitudes_dict) < 3:
        print(f"⚠️  Not enough subjects for LOSO in {roi} ({len(amplitudes_dict)} < 3)")
        return None

    # Compute LOSO
    loso_results = compute_loso_noise_ceiling(amplitudes_dict, metric='correlation')

    print(f"✓ {roi} LOSO: Lower bound = {loso_results['lower_bound']:.3f}, "
          f"Upper bound = {loso_results['upper_bound']:.3f}")

    return loso_results


def create_summary_visualizations(all_results, loso_by_roi, output_dir):
    """
    Generate comprehensive visualizations

    Args:
        all_results: dict of all subject-ROI results
        loso_by_roi: dict of LOSO results per ROI
        output_dir: Path to save figures
    """
    viz_dir = output_dir / "visualizations"
    viz_dir.mkdir(parents=True, exist_ok=True)

    # 1. Noise ceiling bar plot per ROI
    for roi in ROIS:
        roi_results = {k: v for k, v in all_results.items() if v['roi'] == roi}

        if not roi_results:
            continue

        # Average metrics across subjects
        rdm_before = np.mean([v['rdm_correlation_before'] for v in roi_results.values()])
        rdm_after = np.mean([v['rdm_correlation_after'] for v in roi_results.values()])
        ceiling_upper = np.mean([v['noise_ceiling_upper'] for v in roi_results.values()])

        # LOSO bounds
        if roi in loso_by_roi and loso_by_roi[roi] is not None:
            ceiling_lower = loso_by_roi[roi]['lower_bound']
        else:
            ceiling_lower = ceiling_upper * 0.7  # Placeholder

        # Create visualization
        viz_data = {
            'baseline': rdm_before,
            'procrustes': rdm_after,
            'noise_ceiling_lower': ceiling_lower,
            'noise_ceiling_upper': ceiling_upper
        }

        visualize_noise_ceiling(
            viz_data,
            str(viz_dir / f"noise_ceiling_{roi}.png"),
            figsize=(10, 6)
        )

    # 2. Split-half distribution for representative subject-ROI
    # Pick first available
    example_plotted = False
    for key, result in all_results.items():
        if 'split_half_correlations' in result and not example_plotted:
            # Random split-half distribution
            visualize_split_half_distribution(
                result['split_half_correlations'],
                result['noise_ceiling_upper'],
                str(viz_dir / f"split_half_dist_{result['subject']}_{result['roi']}.png")
            )

            # Odd/even RDM visualization
            if 'odd_even_rdms' in result:
                rdm_odd = np.array(result['odd_even_rdms']['odd'])
                rdm_even = np.array(result['odd_even_rdms']['even'])
                visualize_odd_even_rdms(
                    rdm_odd,
                    rdm_even,
                    result['split_half_odd_even_raw'],
                    str(viz_dir / f"odd_even_rdms_{result['subject']}_{result['roi']}.png"),
                    color_labels=[f'C{i+1}' for i in range(8)]
                )

            example_plotted = True

    # 3. Summary scatter plot: Performance vs Ceiling
    fig, ax = plt.subplots(figsize=(10, 8))

    for roi, color in zip(ROIS, ['red', 'orange', 'green', 'blue']):
        roi_results = [v for v in all_results.values() if v['roi'] == roi]

        if not roi_results:
            continue

        ceiling_vals = [v['noise_ceiling_upper'] for v in roi_results]
        perf_vals = [v['rdm_correlation_after'] for v in roi_results]

        ax.scatter(ceiling_vals, perf_vals, label=roi, alpha=0.7, s=100, color=color)

    # Diagonal line (perfect performance = ceiling)
    max_val = max([v['noise_ceiling_upper'] for v in all_results.values()])
    ax.plot([0, max_val], [0, max_val], 'k--', linewidth=2, label='Perfect (100% ceiling)')

    # 50% line
    ax.plot([0, max_val], [0, max_val*0.5], 'gray', linestyle=':', linewidth=2, label='50% ceiling')

    ax.set_xlabel('Noise Ceiling (Split-Half)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Observed Performance (Procrustes)', fontsize=12, fontweight='bold')
    ax.set_title('Performance vs Noise Ceiling', fontsize=14, fontweight='bold')
    ax.legend(loc='upper left', fontsize=11)
    ax.grid(alpha=0.3, linestyle=':')
    ax.set_aspect('equal', adjustable='box')

    plt.tight_layout()
    plt.savefig(viz_dir / "performance_vs_ceiling_scatter.png", dpi=300, bbox_inches='tight')
    plt.close()

    print(f"✓ Saved visualizations to {viz_dir}")


def main():
    """Evaluate all subject-ROI pairs with noise ceiling"""

    print("="*80)
    print("Evaluation with Noise Ceiling Analysis")
    print("="*80)
    print(f"Subjects: {len(SUBJECTS)} (sub-01 ~ sub-10)")
    print(f"ROIs: {len(ROIS)} (V1, V2, V3, hV4)")
    print(f"Total: {len(SUBJECTS) * len(ROIS)} pairs")
    print("")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_results = {}

    # Evaluate each subject-ROI
    for subject in SUBJECTS:
        for roi in ROIS:
            result = evaluate_single_roi_with_ceiling(subject, roi, verbose=True)

            if result is not None:
                key = f"sub-{subject}_{roi}"
                all_results[key] = result

    print(f"\n✓ Completed {len(all_results)} / {len(SUBJECTS) * len(ROIS)} pairs")

    # Compute LOSO noise ceiling per ROI (group-level)
    print("\n" + "="*80)
    print("Computing LOSO Noise Ceiling (Inter-Subject)")
    print("="*80)

    loso_by_roi = {}
    for roi in ROIS:
        loso_results = compute_group_loso_ceiling(all_results, roi)
        if loso_results is not None:
            loso_by_roi[roi] = loso_results

            # Add to results
            for subject in SUBJECTS:
                key = f"sub-{subject}_{roi}"
                if key in all_results:
                    all_results[key]['noise_ceiling_lower_loso'] = loso_results['lower_bound']
                    all_results[key]['noise_ceiling_upper_loso'] = loso_results['upper_bound']

                    # Per-subject LOSO score
                    if subject in loso_results['per_subject']:
                        all_results[key]['loso_score'] = loso_results['per_subject'][subject]

    # Summary statistics
    print("\n" + "="*80)
    print("Summary Statistics")
    print("="*80)

    summary = {}
    for roi in ROIS:
        roi_results = [v for v in all_results.values() if v['roi'] == roi]

        if not roi_results:
            continue

        summary[roi] = {
            'n_subjects': len(roi_results),
            'rdm_correlation_before': {
                'mean': float(np.mean([v['rdm_correlation_before'] for v in roi_results])),
                'std': float(np.std([v['rdm_correlation_before'] for v in roi_results]))
            },
            'rdm_correlation_after': {
                'mean': float(np.mean([v['rdm_correlation_after'] for v in roi_results])),
                'std': float(np.std([v['rdm_correlation_after'] for v in roi_results]))
            },
            'noise_ceiling_upper': {
                'mean': float(np.mean([v['noise_ceiling_upper'] for v in roi_results])),
                'std': float(np.std([v['noise_ceiling_upper'] for v in roi_results]))
            },
            'noise_ceiling_odd_even': {
                'mean': float(np.mean([v['noise_ceiling_odd_even'] for v in roi_results])),
                'std': float(np.std([v['noise_ceiling_odd_even'] for v in roi_results]))
            },
            'split_half_method_comparison': {
                'mean_difference': float(np.mean([v['split_half_method_difference']
                                                 for v in roi_results])),
                'max_difference': float(np.max([v['split_half_method_difference']
                                                for v in roi_results])),
                'std_difference': float(np.std([v['split_half_method_difference']
                                                for v in roi_results]))
            },
            'pct_of_ceiling_after': {
                'mean': float(np.mean([v['pct_of_ceiling_after'] for v in roi_results])),
                'std': float(np.std([v['pct_of_ceiling_after'] for v in roi_results]))
            }
        }

        if roi in loso_by_roi:
            summary[roi]['loso_lower_bound'] = float(loso_by_roi[roi]['lower_bound'])
            summary[roi]['loso_upper_bound'] = float(loso_by_roi[roi]['upper_bound'])

        print(f"\n{roi}:")
        print(f"  RDM (before): {summary[roi]['rdm_correlation_before']['mean']:.3f} ± {summary[roi]['rdm_correlation_before']['std']:.3f}")
        print(f"  RDM (after):  {summary[roi]['rdm_correlation_after']['mean']:.3f} ± {summary[roi]['rdm_correlation_after']['std']:.3f}")
        print(f"  Ceiling (random):  {summary[roi]['noise_ceiling_upper']['mean']:.3f} ± {summary[roi]['noise_ceiling_upper']['std']:.3f}")
        print(f"  Ceiling (odd/even): {summary[roi]['noise_ceiling_odd_even']['mean']:.3f} ± {summary[roi]['noise_ceiling_odd_even']['std']:.3f}")
        print(f"  Method difference: {summary[roi]['split_half_method_comparison']['mean_difference']:.3f} ± {summary[roi]['split_half_method_comparison']['std_difference']:.3f}")
        print(f"  % of ceiling: {summary[roi]['pct_of_ceiling_after']['mean']:.1f}% ± {summary[roi]['pct_of_ceiling_after']['std']:.1f}%")

        if roi in loso_by_roi:
            print(f"  LOSO bounds:  [{summary[roi]['loso_lower_bound']:.3f}, {summary[roi]['loso_upper_bound']:.3f}]")

    # Save results
    output_file = OUTPUT_DIR / "evaluation_with_ceiling.json"
    output_data = {
        'individual_results': all_results,
        'summary_by_roi': summary,
        'loso_by_roi': {roi: {k: v for k, v in results.items() if k != 'per_subject'}
                       for roi, results in loso_by_roi.items()}
    }

    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"\n✓ Results saved to {output_file}")

    # Generate visualizations
    print("\n" + "="*80)
    print("Generating Visualizations")
    print("="*80)

    create_summary_visualizations(all_results, loso_by_roi, OUTPUT_DIR)

    print("\n" + "="*80)
    print("✓ Evaluation Complete")
    print("="*80)


if __name__ == '__main__':
    main()
