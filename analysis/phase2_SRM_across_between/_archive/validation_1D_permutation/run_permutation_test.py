"""
Test 1D: Label Permutation Test

Purpose: Test if observed CVD-HC disparity difference is larger than chance

Method:
1. Load existing disparity results from Test 1A
2. Compute observed t-statistic: (CVD-HC - HC-HC) / SE
3. Permutation loop (n=10,000): shuffle group labels and recompute t-stat
4. P-value: P(t_null >= t_obs)

Expected: V1/V2 survive permutation test (p<0.05)
"""

import numpy as np
import json
import sys
from pathlib import Path
from datetime import datetime

# Add parent directories to path
script_dir = Path(__file__).parent
sys.path.append(str(script_dir.parent))

from utils.validation_metrics import permutation_test
from utils.statistical_tests import effect_size_cohens_d

ROIS = ['V1', 'V2', 'V3', 'hV4']


def run_permutation_test_for_roi(hc_disparities: np.ndarray,
                                  cvd_disparities: np.ndarray,
                                  n_permutations: int = 10000,
                                  seed: int = 42) -> dict:
    """
    Run permutation test comparing CVD-HC vs HC-HC disparities.

    Parameters
    ----------
    hc_disparities : np.ndarray
        HC-to-HC-reference disparities (n_hc=7)
    cvd_disparities : np.ndarray
        CVD-to-HC-reference disparities (n_cvd=3)
    n_permutations : int
        Number of permutation iterations
    seed : int
        Random seed

    Returns
    -------
    results : dict
        Contains observed statistic, p-value, null distribution, effect size
    """
    # Run permutation test (using t-statistic)
    t_obs, p_value, null_dist = permutation_test(
        cvd_disparities, hc_disparities,
        n_permutations=n_permutations,
        statistic='t',
        seed=seed
    )

    # Compute effect size
    cohens_d = effect_size_cohens_d(cvd_disparities, hc_disparities)

    # Compute means and SEs
    hc_mean = np.mean(hc_disparities)
    cvd_mean = np.mean(cvd_disparities)
    hc_se = np.std(hc_disparities, ddof=1) / np.sqrt(len(hc_disparities))
    cvd_se = np.std(cvd_disparities, ddof=1) / np.sqrt(len(cvd_disparities))
    mean_diff = cvd_mean - hc_mean

    # Compute percentile of observed in null distribution
    percentile = np.mean(np.abs(null_dist) <= np.abs(t_obs)) * 100

    return {
        'observed_t': float(t_obs),
        'p_value': float(p_value),
        'p_value_interpretation': 'significant' if p_value < 0.05 else 'non-significant',
        'null_distribution': null_dist.tolist(),
        'null_mean': float(np.mean(null_dist)),
        'null_std': float(np.std(null_dist)),
        'percentile': float(percentile),
        'effect_size_cohens_d': float(cohens_d),
        'hc_mean': float(hc_mean),
        'hc_se': float(hc_se),
        'cvd_mean': float(cvd_mean),
        'cvd_se': float(cvd_se),
        'mean_difference': float(mean_diff),
        'n_hc': len(hc_disparities),
        'n_cvd': len(cvd_disparities),
        'n_permutations': n_permutations
    }


def main(verification_results_dir: Path, output_dir: Path, n_permutations: int = 10000):
    """
    Main permutation test function.

    Loads results from Test 1A and performs permutation tests for all ROIs.

    Parameters
    ----------
    verification_results_dir : Path
        Directory containing Test 1A results
    output_dir : Path
        Output directory for permutation test results
    n_permutations : int
        Number of permutation iterations
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_dir = output_dir / timestamp
    results_dir.mkdir(parents=True, exist_ok=True)

    # Load Test 1A results
    results_file = verification_results_dir / 'results.json'
    if not results_file.exists():
        raise FileNotFoundError(f"Test 1A results not found: {results_file}")

    with open(results_file, 'r') as f:
        test_1a_results = json.load(f)

    # Settings
    settings = {
        'timestamp': timestamp,
        'test_1a_results_dir': str(verification_results_dir),
        'n_permutations': n_permutations,
        'seed': 42,
        'rois': ROIS,
        'alpha': 0.05
    }

    with open(results_dir / 'settings.json', 'w') as f:
        json.dump(settings, f, indent=2)

    # Results storage
    permutation_results = {}
    report_lines = []

    report_lines.append("=" * 80)
    report_lines.append("Test 1D: Label Permutation Test")
    report_lines.append("=" * 80)
    report_lines.append(f"Timestamp: {timestamp}")
    report_lines.append(f"Permutations: {n_permutations:,}")
    report_lines.append(f"Seed: 42")
    report_lines.append("")

    print(f"\n=== Running Permutation Tests ({n_permutations:,} iterations) ===\n")

    for roi in ROIS:
        print(f"=== {roi} ===")
        report_lines.append(f"\n{'='*80}")
        report_lines.append(f"ROI: {roi}")
        report_lines.append(f"{'='*80}")

        if roi not in test_1a_results:
            print(f"  WARNING: No Test 1A results for {roi}")
            report_lines.append("  ⚠️  No data available")
            continue

        roi_data = test_1a_results[roi]

        # Extract disparities
        hc_disparities = np.array(roi_data.get('hc_disparities', []))
        cvd_disparities = np.array(roi_data.get('cvd_disparities', []))

        if len(hc_disparities) == 0 or len(cvd_disparities) == 0:
            print(f"  WARNING: Missing disparity data for {roi}")
            report_lines.append("  ⚠️  Missing disparity data")
            continue

        print(f"  HC disparities: n={len(hc_disparities)}, mean={np.mean(hc_disparities):.4f}")
        print(f"  CVD disparities: n={len(cvd_disparities)}, mean={np.mean(cvd_disparities):.4f}")

        # Run permutation test
        print(f"  Running permutation test...")
        perm_results = run_permutation_test_for_roi(
            hc_disparities, cvd_disparities,
            n_permutations=n_permutations
        )

        permutation_results[roi] = perm_results

        # Report
        report_lines.append(f"\nObserved Statistics:")
        report_lines.append(f"  HC-HC disparity: {perm_results['hc_mean']:.4f} ± {perm_results['hc_se']:.4f} (n={perm_results['n_hc']})")
        report_lines.append(f"  CVD-HC disparity: {perm_results['cvd_mean']:.4f} ± {perm_results['cvd_se']:.4f} (n={perm_results['n_cvd']})")
        report_lines.append(f"  Mean difference: {perm_results['mean_difference']:.4f}")
        report_lines.append(f"  Observed t-statistic: {perm_results['observed_t']:.3f}")
        report_lines.append(f"  Cohen's d: {perm_results['effect_size_cohens_d']:.3f}")

        report_lines.append(f"\nPermutation Test Results:")
        report_lines.append(f"  Null distribution: mean={perm_results['null_mean']:.3f}, std={perm_results['null_std']:.3f}")
        report_lines.append(f"  Observed t percentile: {perm_results['percentile']:.1f}%")
        report_lines.append(f"  P-value: {perm_results['p_value']:.4f}")

        if perm_results['p_value'] < 0.05:
            report_lines.append(f"  ✅ SIGNIFICANT (p < 0.05)")
            print(f"  ✅ SIGNIFICANT: p={perm_results['p_value']:.4f}, t={perm_results['observed_t']:.3f}")
        else:
            report_lines.append(f"  ❌ NOT SIGNIFICANT (p ≥ 0.05)")
            print(f"  ❌ NOT SIGNIFICANT: p={perm_results['p_value']:.4f}, t={perm_results['observed_t']:.3f}")

        print(f"  Effect size (Cohen's d): {perm_results['effect_size_cohens_d']:.3f}")

    # Overall summary
    report_lines.append(f"\n{'='*80}")
    report_lines.append("OVERALL SUMMARY")
    report_lines.append(f"{'='*80}")

    significant_rois = [roi for roi, res in permutation_results.items()
                       if res['p_value'] < 0.05]

    report_lines.append(f"\nSignificant ROIs (p < 0.05): {len(significant_rois)}/{len(permutation_results)}")
    if significant_rois:
        for roi in significant_rois:
            res = permutation_results[roi]
            report_lines.append(f"  - {roi}: p={res['p_value']:.4f}, Cohen's d={res['effect_size_cohens_d']:.2f}")

    # Expected vs observed
    report_lines.append(f"\nExpected Results:")
    report_lines.append(f"  V1/V2: Should survive permutation test (p < 0.05)")
    report_lines.append(f"  V3/hV4: May not survive (underpowered with n_CVD=3)")

    report_lines.append(f"\nObserved Results:")
    for roi in ['V1', 'V2', 'V3', 'hV4']:
        if roi in permutation_results:
            res = permutation_results[roi]
            status = "✅ PASS" if res['p_value'] < 0.05 else "❌ FAIL"
            expected_pass = roi in ['V1', 'V2']
            match = (res['p_value'] < 0.05) == expected_pass
            match_str = "✅" if match else "⚠️"
            report_lines.append(f"  {roi}: p={res['p_value']:.4f} {status} {match_str}")

    # Save results
    # Save full results (with null distributions)
    with open(results_dir / 'permutation_results_full.json', 'w') as f:
        json.dump(permutation_results, f, indent=2)

    # Save summary (without null distributions to reduce file size)
    summary_results = {}
    for roi, res in permutation_results.items():
        summary_results[roi] = {k: v for k, v in res.items() if k != 'null_distribution'}

    with open(results_dir / 'permutation_results_summary.json', 'w') as f:
        json.dump(summary_results, f, indent=2)

    with open(results_dir / 'permutation_report.txt', 'w') as f:
        f.write('\n'.join(report_lines))

    print(f"\n{'='*80}")
    print(f"Results saved to: {results_dir}")
    print(f"{'='*80}")

    # Print report
    print('\n'.join(report_lines))

    return permutation_results


if __name__ == '__main__':
    # Paths
    base_dir = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis')

    # Load Test 1A results (find most recent)
    test_1a_dir = base_dir / 'analysis' / 'phase2_SRM_across_between' / 'validation' / '1A_verify_hc_only' / 'results'
    test_1a_results_dirs = sorted([d for d in test_1a_dir.iterdir() if d.is_dir()], reverse=True)

    if not test_1a_results_dirs:
        raise FileNotFoundError(f"No Test 1A results found in {test_1a_dir}")

    verification_results_dir = test_1a_results_dirs[0]
    print(f"Using Test 1A results: {verification_results_dir}")

    # Output directory
    output_dir = base_dir / 'analysis' / 'phase2_SRM_across_between' / 'validation' / '1D_permutation' / 'results'

    # Run permutation tests
    results = main(verification_results_dir, output_dir, n_permutations=10000)

    print("\n✅ Permutation testing completed!")
