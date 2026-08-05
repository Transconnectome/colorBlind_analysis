#!/usr/bin/env python3
"""
3.1.1d Across-run RDM Reliability (ANOVA + Procrustes Alignment)
=================================================================
ANOVA F-test feature selection + Procrustes alignment 후 RDM reliability 계산

Combines:
- ANOVA F-test: Color-selective voxel selection
- Procrustes alignment: Run-to-run geometric alignment

비교:
- Before alignment: ANOVA-selected voxels, original amplitudes
- After alignment: ANOVA-selected voxels, Procrustes-aligned amplitudes

Input:
- Baseline amplitudes: {BASELINE_RESULTS}/sub-{ID}/{ROI}/amplitudes_z.npy
  - Shape: (n_runs=6, n_colors=8, n_voxels)

Output:
- {VALIDATION_OUT}/rdm_reliability_anova_aligned/{TIMESTAMP}/
  - reliability_by_k.json (k별 before/after reliability)
  - rdm_reliability_comparison.png (before vs after, k별)
"""

import argparse
import json
from pathlib import Path
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import spearmanr
from scipy.spatial import procrustes
from sklearn.feature_selection import f_classif
from itertools import combinations
from tqdm import tqdm

plt.rcParams['figure.dpi'] = 150
plt.style.use('default')


def select_voxels_anova(amplitudes_z, k):
    """
    Select top-k color-discriminative voxels using ANOVA F-test

    Args:
        amplitudes_z: (n_runs, n_colors, n_voxels)
        k: number of voxels to select

    Returns:
        selected_amplitudes: (n_runs, n_colors, k)
        selected_indices: (k,) voxel indices
        f_values: (n_voxels,) F-statistic for all voxels
    """
    n_runs, n_colors, n_voxels = amplitudes_z.shape

    # Prepare data for ANOVA F-test
    X = amplitudes_z.reshape(-1, n_voxels)
    y = np.tile(np.arange(n_colors), n_runs)

    # Compute F-statistic
    f_values, p_values = f_classif(X, y)

    # Handle NaN F-values
    valid_mask = ~np.isnan(f_values)
    f_values[~valid_mask] = -np.inf

    # Select top-k voxels
    k_actual = min(k, np.sum(valid_mask))
    selected_indices = np.argsort(f_values)[-k_actual:]

    selected_amplitudes = amplitudes_z[:, :, selected_indices]

    return selected_amplitudes, selected_indices, f_values


def remove_constant_voxels(amplitudes_z):
    """
    Remove voxels that have zero variance across colors in any run.

    Args:
        amplitudes_z: (n_runs, n_colors, n_voxels)

    Returns:
        cleaned_amplitudes: (n_runs, n_colors, n_valid_voxels)
        n_removed: number of voxels removed
        valid_mask: boolean mask of valid voxels
    """
    n_runs, n_colors, n_voxels = amplitudes_z.shape

    invalid_voxels = set()

    for run_idx in range(n_runs):
        pattern = amplitudes_z[run_idx]
        voxel_stds = np.std(pattern, axis=0)
        constant_voxels = np.where(voxel_stds < 1e-10)[0]
        invalid_voxels.update(constant_voxels)

    valid_mask = np.ones(n_voxels, dtype=bool)
    if len(invalid_voxels) > 0:
        valid_mask[list(invalid_voxels)] = False

    n_valid = np.sum(valid_mask)
    n_removed = len(invalid_voxels)

    cleaned_amplitudes = amplitudes_z[:, :, valid_mask]

    return cleaned_amplitudes, n_removed, valid_mask


def procrustes_align_runs(amplitudes_z, reference_run=0):
    """
    Procrustes alignment of all runs to a reference run

    Args:
        amplitudes_z: (n_runs, n_colors, n_voxels)
        reference_run: Index of reference run (default: 0)

    Returns:
        aligned_amplitudes: (n_runs, n_colors, n_voxels) aligned data
        disparities: (n_runs,) disparity values

    Raises:
        ValueError: If alignment fails
    """
    n_runs, n_colors, n_voxels = amplitudes_z.shape

    # Check for NaN/Inf
    if np.isnan(amplitudes_z).any() or np.isinf(amplitudes_z).any():
        raise ValueError("Input data contains NaN or Inf values")

    # Remove constant voxels
    cleaned_amplitudes, n_removed, valid_mask = remove_constant_voxels(amplitudes_z)
    n_valid_voxels = cleaned_amplitudes.shape[2]

    if n_removed > 0:
        print(f"      Removed {n_removed} constant voxels, {n_valid_voxels} remain")

    if n_valid_voxels < 5:
        raise ValueError(f"Too few valid voxels ({n_valid_voxels}) after removing constant voxels")

    amplitudes_z = cleaned_amplitudes

    # Check variance
    for run_idx in range(n_runs):
        var = np.var(amplitudes_z[run_idx])
        if var < 1e-10:
            raise ValueError(f"Run {run_idx} has zero variance")

    # Reference pattern
    reference = amplitudes_z[reference_run]

    aligned_amplitudes = np.zeros_like(amplitudes_z)
    disparities = np.zeros(n_runs)

    aligned_amplitudes[reference_run] = reference
    disparities[reference_run] = 0.0

    # Align other runs
    for run_idx in range(n_runs):
        if run_idx == reference_run:
            continue

        pattern = amplitudes_z[run_idx]

        try:
            mtx1, mtx2, disparity = procrustes(reference, pattern)
            aligned_amplitudes[run_idx] = mtx2
            disparities[run_idx] = disparity
        except ValueError as e:
            raise ValueError(f"Procrustes alignment failed for run {run_idx}: {e}")

    return aligned_amplitudes, disparities


def compute_rdm(amplitudes):
    """
    Compute RDM (Representational Dissimilarity Matrix)

    Args:
        amplitudes: (n_colors, n_voxels) array

    Returns:
        rdm: (n_colors, n_colors) dissimilarity matrix
    """
    corr_matrix = np.corrcoef(amplitudes)
    rdm = 1 - corr_matrix
    return rdm


def compute_rdm_reliability(amplitudes_z):
    """
    Compute run-pair RDM correlation (reliability)

    Args:
        amplitudes_z: (n_runs, n_colors, n_voxels)

    Returns:
        dict with reliability metrics
    """
    n_runs, n_colors, n_voxels = amplitudes_z.shape

    # Compute RDM for each run
    run_rdms = []
    for run_idx in range(n_runs):
        rdm = compute_rdm(amplitudes_z[run_idx])
        run_rdms.append(rdm)

    # Compute pairwise correlations
    pairwise_correlations = []

    for run_i, run_j in combinations(range(n_runs), 2):
        rdm_i = run_rdms[run_i]
        rdm_j = run_rdms[run_j]

        triu_indices = np.triu_indices(n_colors, k=1)
        vec_i = rdm_i[triu_indices]
        vec_j = rdm_j[triu_indices]

        r, p = spearmanr(vec_i, vec_j)
        pairwise_correlations.append(r)

    return {
        'pairwise_correlations': pairwise_correlations,
        'mean_correlation': float(np.mean(pairwise_correlations)),
        'std_correlation': float(np.std(pairwise_correlations)),
        'median_correlation': float(np.median(pairwise_correlations))
    }


def main():
    parser = argparse.ArgumentParser(description='RDM reliability with ANOVA + Procrustes alignment')
    parser.add_argument('--baseline-timestamp', type=str, required=True)
    parser.add_argument('--subjects', nargs='+',
                       default=[f'sub-{i:02d}' for i in range(1, 11)])
    parser.add_argument('--rois', nargs='+',
                       default=['V1', 'V2', 'V3', 'hV4'])
    parser.add_argument('--k-values', nargs='+', type=int,
                       default=[10, 30, 50, 100, 200],
                       help='Number of voxels to select')

    args = parser.parse_args()

    # Paths
    baseline_dir = Path('/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/method3_header_mi/results/baseline_decoding') / args.baseline_timestamp
    output_dir = Path('/scratch/connectome/haba6030/colorBlind/analysis/validation/results/rdm_reliability_anova_aligned')

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    run_dir = output_dir / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"Output directory: {run_dir}")
    print(f"K values: {args.k_values}")

    # Storage
    results = {
        'baseline_timestamp': args.baseline_timestamp,
        'subjects': args.subjects,
        'rois': args.rois,
        'k_values': args.k_values,
        'by_k': {k: {'before': {}, 'after': {}} for k in args.k_values}
    }

    # Analyze each k value
    for k in args.k_values:
        print(f"\n{'='*70}")
        print(f"Testing k = {k}")
        print(f"{'='*70}")

        for subject in tqdm(args.subjects, desc=f'k={k}'):
            for roi in args.rois:
                amp_path = baseline_dir / subject / roi / 'amplitudes_z.npy'

                if not amp_path.exists():
                    continue

                amplitudes_z = np.load(amp_path)
                n_runs, n_colors, n_voxels = amplitudes_z.shape

                # Skip if not enough voxels
                if n_voxels < k:
                    # print(f"  {subject} {roi}: Only {n_voxels} voxels (< k={k}), skipping")
                    continue

                try:
                    # ANOVA feature selection
                    selected_amplitudes, selected_indices, f_values = select_voxels_anova(amplitudes_z, k)

                    # Before alignment
                    reliability_before = compute_rdm_reliability(selected_amplitudes)

                    if subject not in results['by_k'][k]['before']:
                        results['by_k'][k]['before'][subject] = {}

                    results['by_k'][k]['before'][subject][roi] = {
                        'n_voxels_total': int(n_voxels),
                        'n_voxels_selected': int(len(selected_indices)),
                        'mean_correlation': reliability_before['mean_correlation'],
                        'std_correlation': reliability_before['std_correlation'],
                        'median_correlation': reliability_before['median_correlation']
                    }

                    # After Procrustes alignment
                    try:
                        aligned_amplitudes, disparities = procrustes_align_runs(selected_amplitudes)
                        reliability_after = compute_rdm_reliability(aligned_amplitudes)

                        if subject not in results['by_k'][k]['after']:
                            results['by_k'][k]['after'][subject] = {}

                        results['by_k'][k]['after'][subject][roi] = {
                            'n_voxels_total': int(n_voxels),
                            'n_voxels_selected': int(len(selected_indices)),
                            'mean_correlation': reliability_after['mean_correlation'],
                            'std_correlation': reliability_after['std_correlation'],
                            'median_correlation': reliability_after['median_correlation'],
                            'mean_disparity': float(np.mean(disparities))
                        }

                    except ValueError as e:
                        print(f"    Alignment failed for {subject} {roi}: {e}")
                        continue

                except Exception as e:
                    print(f"  Error: {subject} {roi} - {e}")
                    continue

    # Save detailed results
    json_path = run_dir / 'reliability_by_k.json'
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved detailed results to {json_path}")

    # Compute summary statistics
    summary = {
        'by_k': {}
    }

    for k in args.k_values:
        # Before alignment
        corrs_before = []
        for subject in args.subjects:
            if subject not in results['by_k'][k]['before']:
                continue
            for roi in args.rois:
                if roi not in results['by_k'][k]['before'][subject]:
                    continue
                corrs_before.append(results['by_k'][k]['before'][subject][roi]['mean_correlation'])

        # After alignment
        corrs_after = []
        for subject in args.subjects:
            if subject not in results['by_k'][k]['after']:
                continue
            for roi in args.rois:
                if roi not in results['by_k'][k]['after'][subject]:
                    continue
                corrs_after.append(results['by_k'][k]['after'][subject][roi]['mean_correlation'])

        if len(corrs_before) > 0:
            summary['by_k'][k] = {
                'before': {
                    'mean_reliability': float(np.mean(corrs_before)),
                    'std_reliability': float(np.std(corrs_before)),
                    'median_reliability': float(np.median(corrs_before)),
                    'n_subjects_rois': len(corrs_before),
                    'good_count': int(np.sum(np.array(corrs_before) > 0.6)),
                    'acceptable_count': int(np.sum((np.array(corrs_before) > 0.4) & (np.array(corrs_before) <= 0.6))),
                    'poor_count': int(np.sum(np.array(corrs_before) <= 0.4))
                },
                'after': {
                    'mean_reliability': float(np.mean(corrs_after)) if len(corrs_after) > 0 else 0.0,
                    'std_reliability': float(np.std(corrs_after)) if len(corrs_after) > 0 else 0.0,
                    'median_reliability': float(np.median(corrs_after)) if len(corrs_after) > 0 else 0.0,
                    'n_subjects_rois': len(corrs_after),
                    'good_count': int(np.sum(np.array(corrs_after) > 0.6)) if len(corrs_after) > 0 else 0,
                    'acceptable_count': int(np.sum((np.array(corrs_after) > 0.4) & (np.array(corrs_after) <= 0.6))) if len(corrs_after) > 0 else 0,
                    'poor_count': int(np.sum(np.array(corrs_after) <= 0.4)) if len(corrs_after) > 0 else 0
                }
            }

            if len(corrs_after) > 0:
                improvement = np.array(corrs_after) - np.array(corrs_before[:len(corrs_after)])
                summary['by_k'][k]['improvement'] = {
                    'mean': float(np.mean(improvement)),
                    'std': float(np.std(improvement)),
                    'median': float(np.median(improvement))
                }

    # Save summary
    summary_path = run_dir / 'results.json'
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

    # Visualization
    print("\nGenerating visualization...")

    fig, ax = plt.subplots(figsize=(12, 6))

    k_list = []
    before_mean = []
    before_std = []
    after_mean = []
    after_std = []

    for k in args.k_values:
        if k in summary['by_k']:
            k_list.append(k)
            before_mean.append(summary['by_k'][k]['before']['mean_reliability'])
            before_std.append(summary['by_k'][k]['before']['std_reliability'])
            after_mean.append(summary['by_k'][k]['after']['mean_reliability'])
            after_std.append(summary['by_k'][k]['after']['std_reliability'])

    x = np.arange(len(k_list))
    width = 0.35

    ax.errorbar(x - width/2, before_mean, yerr=before_std, fmt='o-',
                markersize=8, linewidth=2, capsize=5, label='Before Alignment', color='steelblue')
    ax.errorbar(x + width/2, after_mean, yerr=after_std, fmt='s-',
                markersize=8, linewidth=2, capsize=5, label='After Alignment', color='coral')

    ax.axhline(y=0.6, color='green', linestyle='--', label='Good (r>0.6)', linewidth=2, alpha=0.7)
    ax.axhline(y=0.4, color='orange', linestyle='--', label='Acceptable (r>0.4)', linewidth=2, alpha=0.7)

    ax.set_xlabel('Number of Selected Voxels (k)', fontsize=12)
    ax.set_ylabel('Mean RDM Correlation', fontsize=12)
    ax.set_title('RDM Reliability: ANOVA Feature Selection + Procrustes Alignment', fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels(k_list)
    ax.set_ylim([0, 1])
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    fig_path = run_dir / 'rdm_reliability_comparison.png'
    plt.savefig(fig_path)
    print(f"Saved figure to {fig_path}")
    plt.close()

    # Print summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    for k in args.k_values:
        if k in summary['by_k']:
            b = summary['by_k'][k]['before']
            a = summary['by_k'][k]['after']
            imp = summary['by_k'][k].get('improvement', {'mean': 0})
            print(f"k={k}:")
            print(f"  Before: r={b['mean_reliability']:.3f}±{b['std_reliability']:.3f} "
                  f"(Good: {b['good_count']}, Acceptable: {b['acceptable_count']}, Poor: {b['poor_count']})")
            print(f"  After:  r={a['mean_reliability']:.3f}±{a['std_reliability']:.3f} "
                  f"(Good: {a['good_count']}, Acceptable: {a['acceptable_count']}, Poor: {a['poor_count']})")
            print(f"  Improvement: Δr={imp['mean']:.3f}")
    print("="*70)

    # Save settings
    settings = {
        'script': '03d_rdm_reliability_anova_aligned.py',
        'baseline_timestamp': args.baseline_timestamp,
        'subjects': args.subjects,
        'rois': args.rois,
        'k_values': args.k_values,
        'timestamp': timestamp
    }
    settings_path = run_dir / 'settings.json'
    with open(settings_path, 'w') as f:
        json.dump(settings, f, indent=2)


if __name__ == '__main__':
    main()
