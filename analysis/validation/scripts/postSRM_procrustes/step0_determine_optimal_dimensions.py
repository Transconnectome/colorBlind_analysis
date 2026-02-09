#!/usr/bin/env python3
"""
Step 0: Determine Optimal Dimensions via Grid Search

Tests multiple dimension reduction configurations and selects optimal based on
RDM reliability (split-half correlation).

Supports:
- PCA: n_components grid [5, 8, 10, 12, 15, 16]
- ANOVA: k_voxels grid based on min voxel count per ROI

Usage:
    # PCA grid search
    python step0_determine_optimal_dimensions.py --roi V1 --method pca

    # ANOVA grid search
    python step0_determine_optimal_dimensions.py --roi V1 --method anova

    # Both methods
    python step0_determine_optimal_dimensions.py --roi V1 --method both
"""

import argparse
import json
import numpy as np
from pathlib import Path
import subprocess
import sys
from datetime import datetime

# ROI-specific configurations
MIN_VOXEL_COUNTS = {
    'V1': 300,   # sub-03
    'V2': 234,   # sub-03
    'V3': 50,    # sub-02
    'hV4': 57,   # sub-01
}

# Grid search candidates
PCA_CANDIDATES = [5, 8, 10, 12, 15, 16]  # Max 16 due to n_samples constraint

ANOVA_CANDIDATES = {
    'V1': [50, 100, 150, 200, 250, 300],
    'V2': [50, 100, 150, 200, 234],
    'V3': [20, 30, 40, 50],
    'hV4': [30, 40, 50, 57],
}

# Subject groups
HC_SUBJECTS = ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05', 'sub-06']
CVD_SUBJECTS = ['sub-08', 'sub-09', 'sub-10']
ALL_SUBJECTS = HC_SUBJECTS + CVD_SUBJECTS


def run_step1_pca(subject, roi, n_components, baseline_dir, output_dir):
    """Run Step 1a: PCA dimension reduction for single subject."""
    cmd = [
        'python', 'step1a_dimension_reduction_pca.py',
        '--subject', subject.split('-')[1],
        '--roi', roi,
        '--n-components', str(n_components),
        '--baseline-dir', str(baseline_dir),
        '--output-dir', str(output_dir)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"    ERROR: {subject} Step 1 failed")
        print(f"    {result.stderr}")
        return False

    return True


def run_step1_anova(subject, roi, k_voxels, baseline_dir, output_dir):
    """Run Step 1b: ANOVA voxel selection for single subject."""
    cmd = [
        'python', 'step1b_voxel_selection_anova.py',
        '--subject', subject.split('-')[1],
        '--roi', roi,
        '--k', str(k_voxels),
        '--baseline-dir', str(baseline_dir),
        '--output-dir', str(output_dir)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"    ERROR: {subject} Step 1b failed")
        print(f"    {result.stderr}")
        return False

    return True


def run_step2_procrustes(roi, method, input_dir, output_dir, max_iter=10):
    """Run Step 2: Iterative Procrustes."""
    cmd = [
        'python', 'step2_iterative_procrustes.py',
        '--roi', roi,
        '--method', method,
        '--max-iter', str(max_iter),
        '--input-dir', str(input_dir),
        '--output-dir', str(output_dir)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"    ERROR: Step 2 Procrustes failed")
        print(f"    {result.stderr}")
        return False

    return True


def run_step3_rdms(subject, roi, method, input_dir, output_dir):
    """Run Step 3: Compute Crossnobis RDMs."""
    cmd = [
        'python', 'step3_compute_rdms_crossnobis.py',
        '--subject', subject.split('-')[1],
        '--roi', roi,
        '--method', method,
        '--input-dir', str(input_dir),
        '--output-dir', str(output_dir)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"    ERROR: {subject} Step 3 failed")
        return False

    return True


def evaluate_rdm_reliability(roi, method, rdm_dir):
    """
    Evaluate RDM reliability (split-half correlation) for HC subjects.

    Returns:
        dict: {
            'hc_mean_reliability': float,
            'hc_std_reliability': float,
            'per_subject_reliability': {subject: float}
        }
    """
    reliabilities = {}

    for subj_id in HC_SUBJECTS:
        reliability_file = rdm_dir / roi / f"{subj_id}_split_half_reliability.json"

        if not reliability_file.exists():
            print(f"    WARNING: Missing reliability file for {subj_id}")
            continue

        with open(reliability_file) as f:
            data = json.load(f)
            reliabilities[subj_id] = data.get('split_half_correlation', np.nan)

    if not reliabilities:
        return {
            'hc_mean_reliability': np.nan,
            'hc_std_reliability': np.nan,
            'per_subject_reliability': {}
        }

    reliability_values = list(reliabilities.values())

    return {
        'hc_mean_reliability': float(np.nanmean(reliability_values)),
        'hc_std_reliability': float(np.nanstd(reliability_values)),
        'per_subject_reliability': reliabilities
    }


def evaluate_explained_variance(roi, method, step1_dir):
    """
    Evaluate explained variance for PCA method.

    Returns:
        dict: {
            'hc_mean_cumulative_variance': float,
            'per_subject_variance': {subject: float}
        }
    """
    if method != 'pca':
        return {}

    variances = {}

    for subj_id in HC_SUBJECTS:
        metadata_file = step1_dir / roi / f"{subj_id}_metadata.json"

        if not metadata_file.exists():
            continue

        with open(metadata_file) as f:
            data = json.load(f)
            variances[subj_id] = data.get('cumulative_variance', np.nan)

    if not variances:
        return {}

    variance_values = list(variances.values())

    return {
        'hc_mean_cumulative_variance': float(np.nanmean(variance_values)),
        'per_subject_variance': variances
    }


def run_single_configuration(roi, method, param_value, baseline_dir, output_base_dir):
    """
    Run full pipeline (Steps 1-3) for a single configuration.

    Args:
        roi: ROI name
        method: 'pca' or 'anova'
        param_value: n_components (PCA) or k_voxels (ANOVA)
        baseline_dir: Path to baseline results
        output_base_dir: Base output directory

    Returns:
        dict: Evaluation metrics
    """
    print(f"\n  Testing {method.upper()} {roi} with {param_value}...")

    # Create output directories
    step1_dir = output_base_dir / f"step1_{method}" / f"{method}_{param_value}"
    step2_dir = output_base_dir / f"step2_procrustes_{method}" / f"{method}_{param_value}"
    step3_dir = output_base_dir / f"step3_rdms_{method}" / f"{method}_{param_value}"

    step1_dir.mkdir(parents=True, exist_ok=True)
    step2_dir.mkdir(parents=True, exist_ok=True)
    step3_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Dimension reduction for all subjects
    print(f"    Step 1: Dimension reduction ({len(ALL_SUBJECTS)} subjects)...")
    for subj_id in ALL_SUBJECTS:
        if method == 'pca':
            success = run_step1_pca(subj_id, roi, param_value, baseline_dir, step1_dir)
        else:
            success = run_step1_anova(subj_id, roi, param_value, baseline_dir, step1_dir)

        if not success:
            return None

    # Step 2: Procrustes alignment
    print(f"    Step 2: Procrustes alignment...")
    success = run_step2_procrustes(roi, method, step1_dir, step2_dir)
    if not success:
        return None

    # Step 3: RDMs for all subjects
    print(f"    Step 3: Crossnobis RDMs ({len(ALL_SUBJECTS)} subjects)...")
    for subj_id in ALL_SUBJECTS:
        success = run_step3_rdms(subj_id, roi, method, step2_dir, step3_dir)
        if not success:
            return None

    # Evaluate metrics
    print(f"    Evaluating metrics...")
    reliability_metrics = evaluate_rdm_reliability(roi, method, step3_dir)
    variance_metrics = evaluate_explained_variance(roi, method, step1_dir)

    # Combine metrics
    result = {
        'roi': roi,
        'method': method,
        'parameter': param_value,
        'hc_mean_rdm_reliability': reliability_metrics['hc_mean_reliability'],
        'hc_std_rdm_reliability': reliability_metrics['hc_std_reliability'],
        'per_subject_reliability': reliability_metrics['per_subject_reliability'],
    }

    if variance_metrics:
        result['hc_mean_explained_variance'] = variance_metrics['hc_mean_cumulative_variance']
        result['per_subject_variance'] = variance_metrics['per_subject_variance']

    print(f"    ✓ Mean RDM reliability: {reliability_metrics['hc_mean_reliability']:.4f}")
    if variance_metrics:
        print(f"    ✓ Mean explained variance: {variance_metrics['hc_mean_cumulative_variance']:.4f}")

    return result


def select_optimal_configuration(results, method):
    """
    Select optimal configuration based on RDM reliability.

    Args:
        results: List of result dicts
        method: 'pca' or 'anova'

    Returns:
        dict: Optimal configuration with metrics
    """
    valid_results = [r for r in results if r is not None and not np.isnan(r['hc_mean_rdm_reliability'])]

    if not valid_results:
        return None

    # Select based on highest mean RDM reliability
    optimal = max(valid_results, key=lambda x: x['hc_mean_rdm_reliability'])

    return optimal


def main():
    parser = argparse.ArgumentParser(description='Step 0: Determine Optimal Dimensions')
    parser.add_argument('--roi', type=str, required=True,
                        choices=['V1', 'V2', 'V3', 'hV4'],
                        help='ROI name')
    parser.add_argument('--method', type=str, required=True,
                        choices=['pca', 'anova', 'both'],
                        help='Dimension reduction method')
    parser.add_argument('--baseline-dir', type=str,
                        default='/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase1_preprocess_decoding/results/baseline',
                        help='Path to baseline results')
    parser.add_argument('--output-dir', type=str,
                        default='./results/step0_grid_search',
                        help='Output directory for grid search results')

    args = parser.parse_args()

    baseline_dir = Path(args.baseline_dir)
    output_base_dir = Path(args.output_dir)
    output_base_dir.mkdir(parents=True, exist_ok=True)

    roi = args.roi
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print(f"\n{'='*80}")
    print(f"Step 0: Grid Search for Optimal Dimensions")
    print(f"{'='*80}")
    print(f"ROI: {roi}")
    print(f"Method: {args.method}")
    print(f"Timestamp: {timestamp}")
    print(f"Output: {output_base_dir}")

    # Run grid search
    all_results = []

    if args.method in ['pca', 'both']:
        print(f"\n{'='*80}")
        print(f"PCA Grid Search")
        print(f"{'='*80}")
        print(f"Candidates: {PCA_CANDIDATES}")

        pca_results = []
        for n_components in PCA_CANDIDATES:
            result = run_single_configuration(
                roi, 'pca', n_components, baseline_dir, output_base_dir
            )
            if result:
                pca_results.append(result)
                all_results.append(result)

        # Select optimal PCA
        optimal_pca = select_optimal_configuration(pca_results, 'pca')

        if optimal_pca:
            print(f"\n{'='*80}")
            print(f"PCA Optimal Configuration")
            print(f"{'='*80}")
            print(f"  n_components: {optimal_pca['parameter']}")
            print(f"  Mean RDM reliability: {optimal_pca['hc_mean_rdm_reliability']:.4f} ± {optimal_pca['hc_std_rdm_reliability']:.4f}")
            if 'hc_mean_explained_variance' in optimal_pca:
                print(f"  Mean explained variance: {optimal_pca['hc_mean_explained_variance']:.4f}")

    if args.method in ['anova', 'both']:
        print(f"\n{'='*80}")
        print(f"ANOVA Grid Search")
        print(f"{'='*80}")
        anova_candidates = ANOVA_CANDIDATES[roi]
        print(f"Candidates: {anova_candidates}")

        anova_results = []
        for k_voxels in anova_candidates:
            result = run_single_configuration(
                roi, 'anova', k_voxels, baseline_dir, output_base_dir
            )
            if result:
                anova_results.append(result)
                all_results.append(result)

        # Select optimal ANOVA
        optimal_anova = select_optimal_configuration(anova_results, 'anova')

        if optimal_anova:
            print(f"\n{'='*80}")
            print(f"ANOVA Optimal Configuration")
            print(f"{'='*80}")
            print(f"  k_voxels: {optimal_anova['parameter']}")
            print(f"  Mean RDM reliability: {optimal_anova['hc_mean_rdm_reliability']:.4f} ± {optimal_anova['hc_std_rdm_reliability']:.4f}")

    # Save all results
    results_file = output_base_dir / f"{roi}_{args.method}_grid_search_{timestamp}.json"

    summary = {
        'roi': roi,
        'method': args.method,
        'timestamp': timestamp,
        'all_results': all_results,
    }

    if args.method in ['pca', 'both'] and 'optimal_pca' in locals() and optimal_pca:
        summary['optimal_pca'] = optimal_pca

    if args.method in ['anova', 'both'] and 'optimal_anova' in locals() and optimal_anova:
        summary['optimal_anova'] = optimal_anova

    with open(results_file, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\n✓ Results saved: {results_file}")

    # Create optimal dimensions config file
    if args.method in ['pca', 'both'] and 'optimal_pca' in locals() and optimal_pca:
        optimal_config = output_base_dir / 'optimal_dimensions.json'

        if optimal_config.exists():
            with open(optimal_config) as f:
                config = json.load(f)
        else:
            config = {}

        if 'pca' not in config:
            config['pca'] = {}

        config['pca'][roi] = {
            'n_components': optimal_pca['parameter'],
            'rdm_reliability': optimal_pca['hc_mean_rdm_reliability'],
            'explained_variance': optimal_pca.get('hc_mean_explained_variance', None)
        }

        with open(optimal_config, 'w') as f:
            json.dump(config, f, indent=2)

        print(f"✓ Updated optimal config: {optimal_config}")

    if args.method in ['anova', 'both'] and 'optimal_anova' in locals() and optimal_anova:
        optimal_config = output_base_dir / 'optimal_dimensions.json'

        if optimal_config.exists():
            with open(optimal_config) as f:
                config = json.load(f)
        else:
            config = {}

        if 'anova' not in config:
            config['anova'] = {}

        config['anova'][roi] = {
            'k_voxels': optimal_anova['parameter'],
            'rdm_reliability': optimal_anova['hc_mean_rdm_reliability']
        }

        with open(optimal_config, 'w') as f:
            json.dump(config, f, indent=2)

        print(f"✓ Updated optimal config: {optimal_config}")

    print(f"\n{'='*80}")
    print(f"Grid Search Complete!")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    main()
