#!/usr/bin/env python3
"""
3.1.1c Across-run RDM Reliability (With ANOVA Feature Selection)
=================================================================
ANOVA F-test로 color-selective voxels 선택 후 RDM reliability 계산

Motivation:
- R² selection만으로는 color discriminability 보장 안 됨
- ANOVA F-test: MSB/MSW (색상 간 분산 / 색상 내 분산)
- Color-selective voxels만 사용하여 reliability 향상 기대

Input:
- Baseline amplitudes: {BASELINE_RESULTS}/sub-{ID}/{ROI}/amplitudes_z.npy
  - Shape: (n_runs=6, n_colors=8, n_voxels)

Output:
- {VALIDATION_OUT}/rdm_reliability_anova/{TIMESTAMP}/
  - reliability_by_k.json (k별 reliability)
  - rdm_reliability_vs_k.png (k에 따른 reliability 변화)
"""

import argparse
import json
from pathlib import Path
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import spearmanr
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
    # X: (n_runs * n_colors, n_voxels) - samples × features
    # y: (n_runs * n_colors,) - color labels
    X = amplitudes_z.reshape(-1, n_voxels)  # Flatten runs and colors
    y = np.tile(np.arange(n_colors), n_runs)  # Color labels repeated for each run

    # Compute F-statistic for each voxel
    f_values, p_values = f_classif(X, y)

    # Handle NaN F-values (constant voxels)
    valid_mask = ~np.isnan(f_values)
    f_values[~valid_mask] = -np.inf  # Assign lowest priority to NaN

    # Select top-k voxels by F-value
    k_actual = min(k, np.sum(valid_mask))  # Don't select more than valid voxels
    selected_indices = np.argsort(f_values)[-k_actual:]

    # Filter amplitudes
    selected_amplitudes = amplitudes_z[:, :, selected_indices]

    return selected_amplitudes, selected_indices, f_values


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

    # Compute pairwise correlations between runs
    pairwise_correlations = []

    for run_i, run_j in combinations(range(n_runs), 2):
        rdm_i = run_rdms[run_i]
        rdm_j = run_rdms[run_j]

        # Vectorize upper triangle (exclude diagonal)
        triu_indices = np.triu_indices(n_colors, k=1)
        vec_i = rdm_i[triu_indices]
        vec_j = rdm_j[triu_indices]

        # Spearman correlation
        r, p = spearmanr(vec_i, vec_j)
        pairwise_correlations.append(r)

    return {
        'pairwise_correlations': pairwise_correlations,
        'mean_correlation': float(np.mean(pairwise_correlations)),
        'std_correlation': float(np.std(pairwise_correlations)),
        'median_correlation': float(np.median(pairwise_correlations)),
        'min_correlation': float(np.min(pairwise_correlations)),
        'max_correlation': float(np.max(pairwise_correlations))
    }


def main():
    parser = argparse.ArgumentParser(description='RDM reliability with ANOVA feature selection')
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
    output_dir = Path('/scratch/connectome/haba6030/colorBlind/analysis/validation/results/rdm_reliability_anova')

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
        'by_k': {k: {} for k in args.k_values}
    }

    # Analyze each k value
    for k in args.k_values:
        print(f"\n{'='*70}")
        print(f"Testing k = {k}")
        print(f"{'='*70}")

        for subject in tqdm(args.subjects, desc=f'k={k}'):
            results['by_k'][k][subject] = {}

            for roi in args.rois:
                amp_path = baseline_dir / subject / roi / 'amplitudes_z.npy'

                if not amp_path.exists():
                    continue

                amplitudes_z = np.load(amp_path)
                n_runs, n_colors, n_voxels = amplitudes_z.shape

                # Skip if not enough voxels
                if n_voxels < k:
                    print(f"  {subject} {roi}: Only {n_voxels} voxels (< k={k}), skipping")
                    continue

                try:
                    # ANOVA feature selection
                    selected_amplitudes, selected_indices, f_values = select_voxels_anova(amplitudes_z, k)

                    # Compute reliability on selected voxels
                    reliability = compute_rdm_reliability(selected_amplitudes)

                    results['by_k'][k][subject][roi] = {
                        'n_voxels_total': int(n_voxels),
                        'n_voxels_selected': int(len(selected_indices)),
                        'mean_f_value': float(np.mean(f_values[selected_indices])),
                        'mean_correlation': reliability['mean_correlation'],
                        'std_correlation': reliability['std_correlation'],
                        'median_correlation': reliability['median_correlation']
                    }

                except Exception as e:
                    print(f"  Error: {subject} {roi} - {e}")
                    continue

    # Save results
    json_path = run_dir / 'reliability_by_k.json'
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved results to {json_path}")

    # Compute summary statistics
    summary = {
        'by_k': {}
    }

    for k in args.k_values:
        all_correlations = []
        for subject in args.subjects:
            if subject not in results['by_k'][k]:
                continue
            for roi in args.rois:
                if roi not in results['by_k'][k][subject]:
                    continue
                data = results['by_k'][k][subject][roi]
                all_correlations.append(data['mean_correlation'])

        if len(all_correlations) > 0:
            summary['by_k'][k] = {
                'mean_reliability': float(np.mean(all_correlations)),
                'std_reliability': float(np.std(all_correlations)),
                'median_reliability': float(np.median(all_correlations)),
                'n_subjects_rois': len(all_correlations),
                'good_count': int(np.sum(np.array(all_correlations) > 0.6)),
                'acceptable_count': int(np.sum((np.array(all_correlations) > 0.4) & (np.array(all_correlations) <= 0.6))),
                'poor_count': int(np.sum(np.array(all_correlations) <= 0.4))
            }

    # Save summary
    summary_path = run_dir / 'results.json'
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

    # Visualization
    print("\nGenerating visualization...")

    fig, ax = plt.subplots(figsize=(10, 6))

    k_list = []
    mean_list = []
    std_list = []

    for k in args.k_values:
        if k in summary['by_k']:
            k_list.append(k)
            mean_list.append(summary['by_k'][k]['mean_reliability'])
            std_list.append(summary['by_k'][k]['std_reliability'])

    ax.errorbar(k_list, mean_list, yerr=std_list, marker='o', markersize=8,
                linewidth=2, capsize=5, label='Mean ± SD')
    ax.axhline(y=0.6, color='green', linestyle='--', label='Good (r>0.6)', linewidth=2)
    ax.axhline(y=0.4, color='orange', linestyle='--', label='Acceptable (r>0.4)', linewidth=2)

    ax.set_xlabel('Number of Selected Voxels (k)', fontsize=12)
    ax.set_ylabel('Mean RDM Correlation', fontsize=12)
    ax.set_title('RDM Reliability vs Feature Selection (ANOVA F-test)', fontsize=14)
    ax.set_ylim([0, 1])
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    fig_path = run_dir / 'rdm_reliability_vs_k.png'
    plt.savefig(fig_path)
    print(f"Saved figure to {fig_path}")
    plt.close()

    # Print summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    for k in args.k_values:
        if k in summary['by_k']:
            s = summary['by_k'][k]
            print(f"k={k}: r={s['mean_reliability']:.3f}±{s['std_reliability']:.3f} "
                  f"(Good: {s['good_count']}, Acceptable: {s['acceptable_count']}, Poor: {s['poor_count']})")
    print("="*70)

    # Save settings
    settings = {
        'script': '03c_rdm_reliability_anova.py',
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
