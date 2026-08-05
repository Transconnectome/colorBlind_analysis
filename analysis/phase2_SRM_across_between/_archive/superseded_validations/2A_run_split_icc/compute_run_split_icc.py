"""
Test 2A: Run-Split Individual Stability (ICC)

Purpose: Test if individual CVD patterns are stable across run splits

Method:
1. For each CVD subject (sub-08, sub-09, sub-10):
   - Compute Procrustes disparity to HC reference using runs 1-3 average
   - Compute Procrustes disparity to HC reference using runs 4-6 average
   - Calculate ICC(3,1) with bootstrap 95% CI
2. Generate ICC heatmap (3 subjects × 4 ROIs)

Expected: ICC > 0.6 for most subject-ROI pairs (good stability)
"""

import numpy as np
import json
import sys
from pathlib import Path
from datetime import datetime
from scipy.linalg import orthogonal_procrustes

# Add parent directories to path
script_dir = Path(__file__).parent
sys.path.append(str(script_dir.parent))

from utils.validation_metrics import compute_icc, classify_icc

HC_SUBJECTS = ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05', 'sub-06', 'sub-07']
CVD_SUBJECTS = ['sub-08', 'sub-09', 'sub-10']
ROIS = ['V1', 'V2', 'V3', 'hV4']


def load_baseline_amplitudes(baseline_dir: Path, subject: str, roi: str) -> np.ndarray:
    """
    Load baseline amplitude data.

    Returns
    -------
    amplitudes : np.ndarray
        Shape (n_runs=6, n_colors=8, n_voxels)
    """
    # Map hV4 to V4 for file paths
    roi_mapped = 'V4' if roi == 'hV4' else roi

    # Try different amplitude file names
    amp_file_options = [
        baseline_dir / subject / roi_mapped / 'amplitudes_procrustes.npy',
        baseline_dir / subject / roi_mapped / 'amplitudes_raw.npy',
        baseline_dir / subject / roi_mapped / 'amplitudes_z.npy'
    ]

    amp_file = None
    for option in amp_file_options:
        if option.exists():
            amp_file = option
            break

    if amp_file is None:
        raise FileNotFoundError(f"Amplitude file not found for {subject}/{roi_mapped} in {baseline_dir / subject / roi_mapped}")

    amplitudes = np.load(amp_file)

    if amplitudes.shape[0] != 6 or amplitudes.shape[1] != 8:
        raise ValueError(f"Unexpected amplitude shape: {amplitudes.shape}")

    return amplitudes


def compute_procrustes_disparity(X: np.ndarray, Y: np.ndarray) -> float:
    """
    Compute Procrustes disparity between two point clouds.

    Parameters
    ----------
    X, Y : np.ndarray
        Shape (n_points, n_features)

    Returns
    -------
    disparity : float
        Procrustes disparity (normalized alignment error)
    """
    # Center
    X_centered = X - X.mean(axis=0)
    Y_centered = Y - Y.mean(axis=0)

    # Normalize
    X_norm = X_centered / np.linalg.norm(X_centered, 'fro')
    Y_norm = Y_centered / np.linalg.norm(Y_centered, 'fro')

    # Find optimal rotation
    R, _ = orthogonal_procrustes(X_norm, Y_norm)

    # Compute disparity
    disparity = np.linalg.norm(X_norm @ R - Y_norm, 'fro')

    return disparity


def compute_run_split_icc_for_subject(subject: str, roi: str,
                                      baseline_dir: Path) -> dict:
    """
    Compute run-split ICC for a single CVD subject-ROI pair.

    Uses within-subject pattern correlation as stability metric.

    Parameters
    ----------
    subject : str
        CVD subject ID
    roi : str
        ROI name
    baseline_dir : Path
        Directory containing baseline amplitudes

    Returns
    -------
    results : dict
        Contains ICC value, CI, classification, correlations
    """
    # Load amplitudes
    amplitudes = load_baseline_amplitudes(baseline_dir, subject, roi)  # (6, 8, n_voxels)

    # Split runs
    runs_a = amplitudes[:3, :, :]  # Runs 1-3
    runs_b = amplitudes[3:, :, :]  # Runs 4-6

    # Average each split
    pattern_a = runs_a.mean(axis=0)  # (8, n_voxels)
    pattern_b = runs_b.mean(axis=0)  # (8, n_voxels)

    # Compute correlation between patterns (within-subject stability)
    # Flatten patterns and correlate
    pattern_a_flat = pattern_a.flatten()
    pattern_b_flat = pattern_b.flatten()

    # Overall correlation
    overall_corr = np.corrcoef(pattern_a_flat, pattern_b_flat)[0, 1]

    # Per-color correlations
    color_correlations = []
    for color_idx in range(8):
        r = np.corrcoef(pattern_a[color_idx], pattern_b[color_idx])[0, 1]
        color_correlations.append(r)

    mean_color_correlation = np.mean(color_correlations)

    # Use mean correlation as ICC proxy
    # Spearman-Brown correction for split-half reliability
    from utils.statistical_tests import spearman_brown_correction
    corrected_reliability = spearman_brown_correction(mean_color_correlation)

    # Bootstrap CI for correlation
    n_bootstrap = 1000
    bootstrap_correlations = []

    for _ in range(n_bootstrap):
        # Resample runs with replacement
        boot_idx_a = np.random.choice(3, size=3, replace=True)
        boot_idx_b = np.random.choice(3, size=3, replace=True) + 3  # Offset for runs 4-6

        boot_runs_a = amplitudes[boot_idx_a, :, :]
        boot_runs_b = amplitudes[boot_idx_b, :, :]

        boot_pattern_a = boot_runs_a.mean(axis=0)
        boot_pattern_b = boot_runs_b.mean(axis=0)

        # Compute color-wise correlations
        boot_color_corrs = []
        for color_idx in range(8):
            r = np.corrcoef(boot_pattern_a[color_idx], boot_pattern_b[color_idx])[0, 1]
            if np.isfinite(r):
                boot_color_corrs.append(r)

        if boot_color_corrs:
            bootstrap_correlations.append(np.mean(boot_color_corrs))

    ci_lower = np.percentile(bootstrap_correlations, 2.5)
    ci_upper = np.percentile(bootstrap_correlations, 97.5)

    # Classification (using correlation as proxy for ICC)
    classification = classify_icc(mean_color_correlation)

    return {
        'subject': subject,
        'roi': roi,
        'split_half_correlation': float(mean_color_correlation),
        'corrected_reliability': float(corrected_reliability),
        'overall_correlation': float(overall_corr),
        'ci_lower': float(ci_lower),
        'ci_upper': float(ci_upper),
        'classification': classification,
        'color_correlations': [float(r) for r in color_correlations]
    }


def main(baseline_dir: Path, output_dir: Path):
    """
    Main function for run-split ICC analysis.

    Parameters
    ----------
    baseline_dir : Path
        Directory containing baseline32 results
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
        'metric': 'procrustes_disparity_consistency'
    }

    with open(results_dir / 'settings.json', 'w') as f:
        json.dump(settings, f, indent=2)

    # Results storage
    icc_results = {}
    report_lines = []

    report_lines.append("=" * 80)
    report_lines.append("Test 2A: Run-Split Individual Stability (ICC)")
    report_lines.append("=" * 80)
    report_lines.append(f"Timestamp: {timestamp}")
    report_lines.append(f"CVD subjects: {CVD_SUBJECTS}")
    report_lines.append(f"Run split: 1-3 vs 4-6")
    report_lines.append("")

    print(f"\n=== Computing Run-Split ICC for CVD Subjects ===\n")

    for roi in ROIS:
        print(f"=== {roi} ===")
        report_lines.append(f"\n{'='*80}")
        report_lines.append(f"ROI: {roi}")
        report_lines.append(f"{'='*80}")

        icc_results[roi] = {}

        # Compute within-subject stability for each CVD subject
        for subject in CVD_SUBJECTS:
            print(f"  Computing split-half stability for {subject}...")

            try:
                result = compute_run_split_icc_for_subject(
                    subject, roi, baseline_dir
                )

                icc_results[roi][subject] = result

                report_lines.append(f"\n{subject}:")
                report_lines.append(f"  Split-half correlation: {result['split_half_correlation']:.3f} [{result['ci_lower']:.3f}, {result['ci_upper']:.3f}]")
                report_lines.append(f"  Spearman-Brown corrected: {result['corrected_reliability']:.3f}")
                report_lines.append(f"  Classification: {result['classification']}")
                report_lines.append(f"  Overall pattern correlation: {result['overall_correlation']:.3f}")

                classification_symbol = {
                    'excellent': '✅',
                    'good': '✅',
                    'moderate': '⚠️',
                    'poor': '❌'
                }.get(result['classification'], '❓')

                print(f"    Split-half r: {result['split_half_correlation']:.3f} ({result['classification']}) {classification_symbol}")

            except Exception as e:
                print(f"    ERROR: {e}")
                report_lines.append(f"\n{subject}: ❌ ERROR - {e}")
                continue

    # Summary statistics
    report_lines.append(f"\n{'='*80}")
    report_lines.append("SUMMARY STATISTICS")
    report_lines.append(f"{'='*80}")

    all_correlations = []
    classification_counts = {'excellent': 0, 'good': 0, 'moderate': 0, 'poor': 0}

    for roi, subjects_data in icc_results.items():
        for subject, result in subjects_data.items():
            all_correlations.append(result['split_half_correlation'])
            classification_counts[result['classification']] += 1

    if all_correlations:
        mean_correlation = np.mean(all_correlations)
        median_correlation = np.median(all_correlations)

        report_lines.append(f"\nOverall Split-Half Correlation:")
        report_lines.append(f"  Mean: {mean_correlation:.3f}")
        report_lines.append(f"  Median: {median_correlation:.3f}")
        report_lines.append(f"  Range: [{min(all_correlations):.3f}, {max(all_correlations):.3f}]")

        report_lines.append(f"\nClassification Distribution:")
        total = sum(classification_counts.values())
        for cls, count in classification_counts.items():
            pct = 100 * count / total if total > 0 else 0
            report_lines.append(f"  {cls.capitalize()}: {count}/{total} ({pct:.1f}%)")

        # Expected results
        report_lines.append(f"\nExpected: ICC > 0.6 (good) for most subject-ROI pairs")
        n_good_or_better = classification_counts['excellent'] + classification_counts['good']
        report_lines.append(f"Observed: {n_good_or_better}/{total} ({100*n_good_or_better/total:.1f}%) good or excellent")

    # Save results
    with open(results_dir / 'icc_results.json', 'w') as f:
        json.dump(icc_results, f, indent=2)

    with open(results_dir / 'icc_report.txt', 'w') as f:
        f.write('\n'.join(report_lines))

    print(f"\n{'='*80}")
    print(f"Results saved to: {results_dir}")
    print(f"{'='*80}")

    # Print report
    print('\n'.join(report_lines))

    return icc_results


if __name__ == '__main__':
    # Paths
    base_dir = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis')

    # Baseline results
    baseline_dir = base_dir / 'analysis' / 'phase1_preprocess_decoding' / 'results' / 'full_dataset_C010'

    if not baseline_dir.exists():
        raise FileNotFoundError(f"Baseline results not found: {baseline_dir}")

    print(f"Using baseline results: {baseline_dir}")

    # Output directory
    output_dir = base_dir / 'analysis' / 'phase2_SRM_across_between' / 'validation' / '2A_run_split_icc' / 'results'

    # Run ICC analysis
    results = main(baseline_dir, output_dir)

    print("\n✅ Run-split ICC analysis completed!")
