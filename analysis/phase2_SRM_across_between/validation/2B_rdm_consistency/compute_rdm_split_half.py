"""
Test 2B: RDM Consistency (Split-Half Correlation)

Purpose: Test if color RDMs are consistent within subjects across run splits
         CRITICAL TEST for validating "scattered but parallel" pattern

Method:
1. For each subject (all 10: 7 HC + 3 CVD):
   - Compute RDM from runs 1-3
   - Compute RDM from runs 4-6
   - Spearman correlation between upper triangles (28 values)
2. Compare HC vs CVD split-half reliability

Expected: CVD split-half r should be COMPARABLE or HIGHER than HC in V1/V2
         (this validates the "parallel" aspect of CVD pattern)
"""

import numpy as np
import json
import sys
from pathlib import Path
from datetime import datetime
from scipy.stats import spearmanr, ttest_ind
from scipy.spatial.distance import squareform, pdist

# Add parent directories to path
script_dir = Path(__file__).parent
sys.path.append(str(script_dir.parent))

from utils.validation_metrics import bootstrap_correlation

HC_SUBJECTS = ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05', 'sub-06', 'sub-07']
CVD_SUBJECTS = ['sub-08', 'sub-09', 'sub-10']
ALL_SUBJECTS = HC_SUBJECTS + CVD_SUBJECTS
ROIS = ['V1', 'V2', 'V3', 'hV4']


def load_baseline_amplitudes(baseline_dir: Path, subject: str, roi: str) -> np.ndarray:
    """Load baseline amplitude data."""
    # Map hV4 to V4
    roi_mapped = 'V4' if roi == 'hV4' else roi

    amp_file_options = [
        baseline_dir / subject / roi_mapped / 'amplitudes_procrustes.npy',
        baseline_dir / subject / roi_mapped / 'amplitudes_raw.npy'
    ]

    for amp_file in amp_file_options:
        if amp_file.exists():
            amplitudes = np.load(amp_file)
            if amplitudes.shape[0] != 6 or amplitudes.shape[1] != 8:
                raise ValueError(f"Unexpected amplitude shape: {amplitudes.shape}")
            return amplitudes

    raise FileNotFoundError(f"Amplitude file not found for {subject}/{roi_mapped}")


def compute_rdm(patterns: np.ndarray) -> np.ndarray:
    """
    Compute RDM from pattern matrix.

    Parameters
    ----------
    patterns : np.ndarray
        Shape (n_colors=8, n_voxels)

    Returns
    -------
    rdm : np.ndarray
        Shape (8, 8) dissimilarity matrix using correlation distance
    """
    rdm = squareform(pdist(patterns, metric='correlation'))
    return rdm


def compute_split_half_rdm_correlation(subject: str, roi: str, baseline_dir: Path) -> dict:
    """
    Compute split-half RDM correlation for a single subject.

    Parameters
    ----------
    subject : str
        Subject ID
    roi : str
        ROI name
    baseline_dir : Path
        Directory containing baseline amplitudes

    Returns
    -------
    results : dict
        Contains split-half correlation, CI, RDMs
    """
    # Load amplitudes
    amplitudes = load_baseline_amplitudes(baseline_dir, subject, roi)  # (6, 8, n_voxels)

    # Split runs
    runs_a = amplitudes[:3, :, :]  # Runs 1-3
    runs_b = amplitudes[3:, :, :]  # Runs 4-6

    # Average each split
    pattern_a = runs_a.mean(axis=0)  # (8, n_voxels)
    pattern_b = runs_b.mean(axis=0)  # (8, n_voxels)

    # Compute RDMs
    rdm_a = compute_rdm(pattern_a)  # (8, 8)
    rdm_b = compute_rdm(pattern_b)  # (8, 8)

    # Extract upper triangle (28 unique values)
    mask = np.triu(np.ones_like(rdm_a, dtype=bool), k=1)
    rdm_a_vec = rdm_a[mask]
    rdm_b_vec = rdm_b[mask]

    # Spearman correlation
    r, p_value = spearmanr(rdm_a_vec, rdm_b_vec)

    # Bootstrap CI
    _, (ci_lower, ci_upper) = bootstrap_correlation(
        rdm_a_vec, rdm_b_vec,
        n_bootstrap=1000,
        method='spearman',
        seed=42
    )

    # Spearman-Brown correction for split-half reliability
    from utils.statistical_tests import spearman_brown_correction
    corrected_reliability = spearman_brown_correction(r)

    return {
        'subject': subject,
        'roi': roi,
        'split_half_correlation': float(r),
        'p_value': float(p_value),
        'corrected_reliability': float(corrected_reliability),
        'ci_lower': float(ci_lower),
        'ci_upper': float(ci_upper),
        'rdm_a_vec': rdm_a_vec.tolist(),
        'rdm_b_vec': rdm_b_vec.tolist()
    }


def main(baseline_dir: Path, output_dir: Path):
    """
    Main function for RDM split-half consistency analysis.

    Parameters
    ----------
    baseline_dir : Path
        Directory containing baseline amplitudes
    output_dir : Path
        Output directory
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_dir = output_dir / timestamp
    results_dir.mkdir(parents=True, exist_ok=True)

    # Settings
    settings = {
        'timestamp': timestamp,
        'baseline_dir': str(baseline_dir),
        'hc_subjects': HC_SUBJECTS,
        'cvd_subjects': CVD_SUBJECTS,
        'rois': ROIS,
        'run_split': 'runs_1-3 vs runs_4-6',
        'metric': 'rdm_spearman_correlation'
    }

    with open(results_dir / 'settings.json', 'w') as f:
        json.dump(settings, f, indent=2)

    # Results storage
    rdm_results = {}
    report_lines = []

    report_lines.append("=" * 80)
    report_lines.append("Test 2B: RDM Consistency (Split-Half Correlation)")
    report_lines.append("=" * 80)
    report_lines.append(f"Timestamp: {timestamp}")
    report_lines.append(f"Run split: 1-3 vs 4-6")
    report_lines.append("")
    report_lines.append("CRITICAL TEST: CVD split-half r should be ≥ HC in V1/V2")
    report_lines.append("               (validates 'parallel' aspect of CVD pattern)")
    report_lines.append("")

    print(f"\n=== Computing RDM Split-Half Correlations ===\n")

    for roi in ROIS:
        print(f"=== {roi} ===")
        report_lines.append(f"\n{'='*80}")
        report_lines.append(f"ROI: {roi}")
        report_lines.append(f"{'='*80}")

        rdm_results[roi] = {}

        hc_correlations = []
        cvd_correlations = []

        # Process all subjects
        for subject in ALL_SUBJECTS:
            group = 'HC' if subject in HC_SUBJECTS else 'CVD'
            print(f"  Computing RDM correlation for {subject} ({group})...")

            try:
                result = compute_split_half_rdm_correlation(subject, roi, baseline_dir)
                rdm_results[roi][subject] = result

                # Store by group
                if subject in HC_SUBJECTS:
                    hc_correlations.append(result['split_half_correlation'])
                else:
                    cvd_correlations.append(result['split_half_correlation'])

                print(f"    r = {result['split_half_correlation']:.3f} [{result['ci_lower']:.3f}, {result['ci_upper']:.3f}]")

            except Exception as e:
                print(f"    ERROR: {e}")
                continue

        # Group comparison
        if hc_correlations and cvd_correlations:
            hc_mean = np.mean(hc_correlations)
            hc_std = np.std(hc_correlations, ddof=1)
            cvd_mean = np.mean(cvd_correlations)
            cvd_std = np.std(cvd_correlations, ddof=1)

            # t-test
            t_stat, p_value = ttest_ind(cvd_correlations, hc_correlations)

            report_lines.append(f"\nGroup Comparison:")
            report_lines.append(f"  HC (n={len(hc_correlations)}): {hc_mean:.3f} ± {hc_std:.3f}")
            report_lines.append(f"  CVD (n={len(cvd_correlations)}): {cvd_mean:.3f} ± {cvd_std:.3f}")
            report_lines.append(f"  Difference: {cvd_mean - hc_mean:+.3f}")
            report_lines.append(f"  t-test: t={t_stat:.3f}, p={p_value:.4f}")

            # Critical check for V1/V2
            if roi in ['V1', 'V2']:
                if cvd_mean >= hc_mean:
                    report_lines.append(f"  ✅ CRITICAL: CVD ≥ HC (validates 'parallel' pattern)")
                    print(f"  ✅ CRITICAL CHECK PASSED: CVD ({cvd_mean:.3f}) ≥ HC ({hc_mean:.3f})")
                else:
                    report_lines.append(f"  ⚠️  WARNING: CVD < HC (challenges 'parallel' pattern)")
                    print(f"  ⚠️  WARNING: CVD ({cvd_mean:.3f}) < HC ({hc_mean:.3f})")
            else:
                report_lines.append(f"  ℹ️  Note: {roi} not critical for 'parallel' validation")

            # Store group stats
            rdm_results[roi]['group_stats'] = {
                'hc_mean': float(hc_mean),
                'hc_std': float(hc_std),
                'hc_values': [float(r) for r in hc_correlations],
                'cvd_mean': float(cvd_mean),
                'cvd_std': float(cvd_std),
                'cvd_values': [float(r) for r in cvd_correlations],
                't_statistic': float(t_stat),
                'p_value': float(p_value),
                'cvd_higher_than_hc': bool(cvd_mean >= hc_mean)
            }

        print()

    # Overall summary
    report_lines.append(f"\n{'='*80}")
    report_lines.append("OVERALL SUMMARY")
    report_lines.append(f"{'='*80}")

    critical_rois_pass = []
    for roi in ['V1', 'V2']:
        if roi in rdm_results and 'group_stats' in rdm_results[roi]:
            if rdm_results[roi]['group_stats']['cvd_higher_than_hc']:
                critical_rois_pass.append(roi)

    report_lines.append(f"\nCritical ROIs (V1/V2) with CVD ≥ HC: {len(critical_rois_pass)}/2")
    for roi in critical_rois_pass:
        stats = rdm_results[roi]['group_stats']
        report_lines.append(f"  ✅ {roi}: CVD={stats['cvd_mean']:.3f} ≥ HC={stats['hc_mean']:.3f}")

    if len(critical_rois_pass) == 2:
        report_lines.append(f"\n✅ VALIDATION SUCCESSFUL: 'Parallel' pattern confirmed in V1/V2")
    elif len(critical_rois_pass) == 1:
        report_lines.append(f"\n⚠️  PARTIAL VALIDATION: 'Parallel' pattern confirmed in {critical_rois_pass[0]} only")
    else:
        report_lines.append(f"\n❌ VALIDATION FAILED: 'Parallel' pattern NOT confirmed")

    # Save results
    with open(results_dir / 'rdm_split_half_results.json', 'w') as f:
        json.dump(rdm_results, f, indent=2)

    with open(results_dir / 'rdm_consistency_report.txt', 'w') as f:
        f.write('\n'.join(report_lines))

    print(f"{'='*80}")
    print(f"Results saved to: {results_dir}")
    print(f"{'='*80}")

    # Print report
    print('\n'.join(report_lines))

    return rdm_results


if __name__ == '__main__':
    # Paths
    base_dir = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis')

    # Baseline results
    baseline_dir = base_dir / 'analysis' / 'phase1_preprocess_decoding' / 'results' / 'full_dataset_C010'

    if not baseline_dir.exists():
        raise FileNotFoundError(f"Baseline results not found: {baseline_dir}")

    print(f"Using baseline results: {baseline_dir}")

    # Output directory
    output_dir = base_dir / 'analysis' / 'phase2_SRM_across_between' / 'validation' / '2B_rdm_consistency' / 'results'

    # Run RDM consistency analysis
    results = main(baseline_dir, output_dir)

    print("\n✅ RDM consistency analysis completed!")
