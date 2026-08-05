#!/usr/bin/env python3
"""
Pre-check data quality for all subjects
========================================
RDM reliability 분석 전 모든 subject 데이터 품질 확인

Check:
1. NaN/Inf 존재 여부
2. Zero variance 여부
3. Color discriminability (색깔 간 구분 가능 여부)

Output:
- Console report of problematic subjects
- JSON file with quality metrics
"""

import argparse
import json
from pathlib import Path
import numpy as np
from scipy.spatial.distance import pdist


def check_subject_data(subject, roi, baseline_dir):
    """
    Check data quality for a subject-ROI

    Returns:
        dict with quality metrics or None if file not found
    """
    amp_path = baseline_dir / subject / roi / 'amplitudes_z.npy'

    if not amp_path.exists():
        return None

    amplitudes_z = np.load(amp_path)
    n_runs, n_colors, n_voxels = amplitudes_z.shape

    # Check 1: NaN/Inf
    has_nan = np.isnan(amplitudes_z).any()
    has_inf = np.isinf(amplitudes_z).any()

    # Check 2: Variance per run
    run_variances = [float(np.var(amplitudes_z[i])) for i in range(n_runs)]
    min_variance = min(run_variances)

    # Check 3: Color discriminability per run
    run_min_distances = []
    run_mean_distances = []

    for run_idx in range(n_runs):
        pattern = amplitudes_z[run_idx]  # (n_colors, n_voxels)
        distances = pdist(pattern)
        run_min_distances.append(float(np.min(distances)))
        run_mean_distances.append(float(np.mean(distances)))

    min_color_distance = min(run_min_distances)
    mean_color_distance = np.mean(run_mean_distances)

    # Quality flags
    quality_ok = True
    issues = []

    if has_nan or has_inf:
        quality_ok = False
        issues.append("NaN/Inf detected")

    if min_variance < 1e-10:
        quality_ok = False
        issues.append(f"Zero variance detected (min={min_variance:.2e})")

    if min_color_distance < 1e-6:
        quality_ok = False
        issues.append(f"No color discriminability (min_dist={min_color_distance:.2e})")
    elif min_color_distance < 0.1:
        issues.append(f"Low color discriminability (min_dist={min_color_distance:.3f})")

    return {
        'shape': amplitudes_z.shape,
        'has_nan': bool(has_nan),
        'has_inf': bool(has_inf),
        'run_variances': run_variances,
        'min_variance': min_variance,
        'run_min_distances': run_min_distances,
        'run_mean_distances': run_mean_distances,
        'min_color_distance': min_color_distance,
        'mean_color_distance': mean_color_distance,
        'quality_ok': quality_ok,
        'issues': issues
    }


def main():
    parser = argparse.ArgumentParser(description='Pre-check data quality')
    parser.add_argument('--baseline-timestamp', type=str, required=True)
    parser.add_argument('--subjects', nargs='+',
                       default=[f'sub-{i:02d}' for i in range(1, 11)])
    parser.add_argument('--rois', nargs='+',
                       default=['V1', 'V2', 'V3', 'hV4'])

    args = parser.parse_args()

    baseline_dir = Path('/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/method3_header_mi/results/baseline_decoding') / args.baseline_timestamp

    print("="*70)
    print("Data Quality Check")
    print("="*70)
    print(f"Baseline: {args.baseline_timestamp}")
    print()

    # Storage
    results = {}
    problem_count = 0

    for subject in args.subjects:
        results[subject] = {}

        for roi in args.rois:
            quality = check_subject_data(subject, roi, baseline_dir)

            if quality is None:
                print(f"✗ {subject} {roi}: FILE NOT FOUND")
                continue

            results[subject][roi] = quality

            if quality['quality_ok']:
                status = "✓"
            else:
                status = "✗"
                problem_count += 1

            print(f"{status} {subject} {roi}:")
            print(f"  Shape: {quality['shape']}")
            print(f"  Min color distance: {quality['min_color_distance']:.4f}")
            print(f"  Mean color distance: {quality['mean_color_distance']:.4f}")

            if quality['issues']:
                for issue in quality['issues']:
                    print(f"  ⚠️  {issue}")

    # Save results
    output_path = Path('/scratch/connectome/haba6030/colorBlind/analysis/validation/results/data_quality_check.json')
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    print()
    print("="*70)
    print(f"Summary: {problem_count} problematic subject-ROI pairs found")
    print(f"Results saved to: {output_path}")
    print("="*70)


if __name__ == '__main__':
    main()
