"""
Test 1D (CORRECTED): Color Label Permutation Test

Purpose: Test if the observed patterns (CVD-HC disparity, within-group consistency)
         depend on the actual color labels or just the model structure.

Method:
1. Load existing SRM-aligned patterns
2. For each permutation:
   - Randomly shuffle color labels (1-8) within each subject
   - Recompute CVD-HC Procrustes disparity
   - Recompute within-group RDM correlations
3. Compare observed metrics to null distribution

Expected: If patterns depend on true color structure, permuted labels should
          yield lower CVD-HC disparity and lower within-group consistency.

Interpretation: "빨강" 레이블이 실제로 의미가 있는지, 아니면 단순히
                모델 구조/voxel 패턴에서 나온 artifact인지 테스트
"""

import numpy as np
import json
import sys
from pathlib import Path
from datetime import datetime
from scipy.linalg import orthogonal_procrustes
from scipy.spatial.distance import squareform, pdist
from scipy.stats import spearmanr

# Add parent directories to path
script_dir = Path(__file__).parent
sys.path.append(str(script_dir.parent))

HC_SUBJECTS = ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05', 'sub-06', 'sub-07']
CVD_SUBJECTS = ['sub-08', 'sub-09', 'sub-10']
ROIS = ['V1', 'V2', 'V3', 'hV4']


def compute_procrustes_disparity(X: np.ndarray, Y: np.ndarray) -> float:
    """Compute Procrustes disparity."""
    X_centered = X - X.mean(axis=0)
    Y_centered = Y - Y.mean(axis=0)
    X_norm = X_centered / np.linalg.norm(X_centered, 'fro')
    Y_norm = Y_centered / np.linalg.norm(Y_centered, 'fro')
    R, _ = orthogonal_procrustes(X_norm, Y_norm)
    disparity = np.linalg.norm(X_norm @ R - Y_norm, 'fro')
    return disparity


def compute_rdm(patterns: np.ndarray) -> np.ndarray:
    """Compute RDM from patterns (8, k)."""
    rdm = squareform(pdist(patterns, metric='correlation'))
    return rdm


def compute_metrics_from_patterns(hc_patterns: list, cvd_patterns: list) -> dict:
    """
    Compute all validation metrics from aligned patterns.

    Parameters
    ----------
    hc_patterns : list
        List of HC patterns, each (8, k)
    cvd_patterns : list
        List of CVD patterns, each (8, k)

    Returns
    -------
    metrics : dict
        Contains disparities, RDM correlations, etc.
    """
    # HC reference
    hc_reference = np.mean(hc_patterns, axis=0)  # (8, k)

    # Compute disparities
    hc_disparities = [compute_procrustes_disparity(p, hc_reference) for p in hc_patterns]
    cvd_disparities = [compute_procrustes_disparity(p, hc_reference) for p in cvd_patterns]

    hc_disparity_mean = np.mean(hc_disparities)
    cvd_disparity_mean = np.mean(cvd_disparities)
    disparity_difference = cvd_disparity_mean - hc_disparity_mean

    # Compute RDMs
    hc_rdms = [compute_rdm(p) for p in hc_patterns]
    cvd_rdms = [compute_rdm(p) for p in cvd_patterns]

    # Within-HC RDM correlations
    hc_rdm_correlations = []
    for i in range(len(hc_rdms)):
        for j in range(i+1, len(hc_rdms)):
            mask = np.triu(np.ones_like(hc_rdms[i], dtype=bool), k=1)
            r, _ = spearmanr(hc_rdms[i][mask], hc_rdms[j][mask])
            if np.isfinite(r):
                hc_rdm_correlations.append(r)

    # Within-CVD RDM correlations
    cvd_rdm_correlations = []
    for i in range(len(cvd_rdms)):
        for j in range(i+1, len(cvd_rdms)):
            mask = np.triu(np.ones_like(cvd_rdms[i], dtype=bool), k=1)
            r, _ = spearmanr(cvd_rdms[i][mask], cvd_rdms[j][mask])
            if np.isfinite(r):
                cvd_rdm_correlations.append(r)

    return {
        'hc_disparity_mean': float(hc_disparity_mean),
        'cvd_disparity_mean': float(cvd_disparity_mean),
        'disparity_difference': float(disparity_difference),
        'hc_rdm_correlation_mean': float(np.mean(hc_rdm_correlations)) if hc_rdm_correlations else 0.0,
        'cvd_rdm_correlation_mean': float(np.mean(cvd_rdm_correlations)) if cvd_rdm_correlations else 0.0
    }


def permute_color_labels(patterns: np.ndarray, seed: int = None) -> np.ndarray:
    """
    Randomly permute color labels within a pattern.

    Parameters
    ----------
    patterns : np.ndarray
        Shape (8, k) - 8 colors, k features
    seed : int
        Random seed

    Returns
    -------
    permuted : np.ndarray
        Shape (8, k) with rows shuffled
    """
    if seed is not None:
        np.random.seed(seed)

    perm_idx = np.random.permutation(8)
    return patterns[perm_idx, :]


def run_color_permutation_test(srm_results_dir: Path, output_dir: Path,
                                n_permutations: int = 1000):
    """
    Run color label permutation test for all ROIs.

    Parameters
    ----------
    srm_results_dir : Path
        Directory containing SRM aligned amplitudes
    output_dir : Path
        Output directory
    n_permutations : int
        Number of permutation iterations
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_dir = output_dir / timestamp
    results_dir.mkdir(parents=True, exist_ok=True)

    # Settings
    settings = {
        'timestamp': timestamp,
        'srm_results_dir': str(srm_results_dir),
        'n_permutations': n_permutations,
        'seed_base': 42,
        'rois': ROIS,
        'test_type': 'color_label_permutation',
        'hypothesis': 'Observed patterns should disappear when color labels are shuffled'
    }

    with open(results_dir / 'settings.json', 'w') as f:
        json.dump(settings, f, indent=2)

    # Results storage
    permutation_results = {}
    report_lines = []

    report_lines.append("=" * 80)
    report_lines.append("Test 1D (CORRECTED): Color Label Permutation Test")
    report_lines.append("=" * 80)
    report_lines.append(f"Timestamp: {timestamp}")
    report_lines.append(f"Permutations: {n_permutations:,}")
    report_lines.append("")
    report_lines.append("Purpose: Test if patterns depend on true color labels")
    report_lines.append("Method: Shuffle color labels (1-8) within each subject")
    report_lines.append("Expected: Shuffled labels → lower disparity difference & RDM correlations")
    report_lines.append("")

    print(f"\n=== Running Color Label Permutation Tests ({n_permutations:,} iterations) ===\n")

    for roi in ROIS:
        print(f"=== {roi} ===")
        report_lines.append(f"\n{'='*80}")
        report_lines.append(f"ROI: {roi}")
        report_lines.append(f"{'='*80}")

        # Load SRM-aligned patterns
        roi_mapped = 'V4' if roi == 'hV4' else roi
        aligned_file = srm_results_dir / f"{roi_mapped}_procrustes_aligned_amplitudes.npy"

        if not aligned_file.exists():
            print(f"  WARNING: Aligned amplitudes not found: {aligned_file}")
            report_lines.append("  ⚠️  Aligned amplitudes not found")
            continue

        aligned_dict = np.load(aligned_file, allow_pickle=True).item()

        # Extract HC and CVD patterns
        hc_patterns_original = [aligned_dict[f'sub-{s:02d}'] for s in range(1, 8)
                               if f'sub-{s:02d}' in aligned_dict]
        cvd_patterns_original = [aligned_dict[f'sub-{s:02d}'] for s in range(8, 11)
                                if f'sub-{s:02d}' in aligned_dict]

        if len(hc_patterns_original) < 6 or len(cvd_patterns_original) < 2:
            print(f"  ERROR: Insufficient data (HC={len(hc_patterns_original)}, CVD={len(cvd_patterns_original)})")
            report_lines.append(f"  ❌ Insufficient data")
            continue

        print(f"  Loaded: {len(hc_patterns_original)} HC + {len(cvd_patterns_original)} CVD patterns")
        print(f"  Pattern shape: {hc_patterns_original[0].shape}")

        # Compute observed metrics
        print(f"  Computing observed metrics...")
        observed = compute_metrics_from_patterns(hc_patterns_original, cvd_patterns_original)

        print(f"    Observed disparity difference: {observed['disparity_difference']:.4f}")
        print(f"    Observed HC RDM correlation: {observed['hc_rdm_correlation_mean']:.3f}")
        print(f"    Observed CVD RDM correlation: {observed['cvd_rdm_correlation_mean']:.3f}")

        # Permutation test
        print(f"  Running permutation test...")
        null_disparity_diff = []
        null_hc_rdm_corr = []
        null_cvd_rdm_corr = []

        for perm_i in range(n_permutations):
            if (perm_i + 1) % 100 == 0:
                print(f"    Permutation {perm_i + 1}/{n_permutations}")

            # Permute color labels for each subject independently
            hc_patterns_perm = [permute_color_labels(p, seed=42 + perm_i * 1000 + i)
                               for i, p in enumerate(hc_patterns_original)]
            cvd_patterns_perm = [permute_color_labels(p, seed=42 + perm_i * 1000 + 100 + i)
                                for i, p in enumerate(cvd_patterns_original)]

            # Compute metrics with permuted labels
            perm_metrics = compute_metrics_from_patterns(hc_patterns_perm, cvd_patterns_perm)

            null_disparity_diff.append(perm_metrics['disparity_difference'])
            null_hc_rdm_corr.append(perm_metrics['hc_rdm_correlation_mean'])
            null_cvd_rdm_corr.append(perm_metrics['cvd_rdm_correlation_mean'])

        null_disparity_diff = np.array(null_disparity_diff)
        null_hc_rdm_corr = np.array(null_hc_rdm_corr)
        null_cvd_rdm_corr = np.array(null_cvd_rdm_corr)

        # Compute p-values (one-tailed: observed > null)
        p_disparity = np.mean(null_disparity_diff >= observed['disparity_difference'])
        p_hc_rdm = np.mean(null_hc_rdm_corr >= observed['hc_rdm_correlation_mean'])
        p_cvd_rdm = np.mean(null_cvd_rdm_corr >= observed['cvd_rdm_correlation_mean'])

        # Percentiles
        percentile_disparity = np.mean(null_disparity_diff <= observed['disparity_difference']) * 100
        percentile_hc_rdm = np.mean(null_hc_rdm_corr <= observed['hc_rdm_correlation_mean']) * 100
        percentile_cvd_rdm = np.mean(null_cvd_rdm_corr <= observed['cvd_rdm_correlation_mean']) * 100

        # Store results
        permutation_results[roi] = {
            'observed': observed,
            'null_distributions': {
                'disparity_difference': null_disparity_diff.tolist(),
                'hc_rdm_correlation': null_hc_rdm_corr.tolist(),
                'cvd_rdm_correlation': null_cvd_rdm_corr.tolist()
            },
            'p_values': {
                'disparity_difference': float(p_disparity),
                'hc_rdm_correlation': float(p_hc_rdm),
                'cvd_rdm_correlation': float(p_cvd_rdm)
            },
            'percentiles': {
                'disparity_difference': float(percentile_disparity),
                'hc_rdm_correlation': float(percentile_hc_rdm),
                'cvd_rdm_correlation': float(percentile_cvd_rdm)
            },
            'null_means': {
                'disparity_difference': float(np.mean(null_disparity_diff)),
                'hc_rdm_correlation': float(np.mean(null_hc_rdm_corr)),
                'cvd_rdm_correlation': float(np.mean(null_cvd_rdm_corr))
            }
        }

        # Report
        report_lines.append(f"\nObserved Metrics:")
        report_lines.append(f"  CVD-HC disparity difference: {observed['disparity_difference']:.4f}")
        report_lines.append(f"  HC RDM correlation: {observed['hc_rdm_correlation_mean']:.3f}")
        report_lines.append(f"  CVD RDM correlation: {observed['cvd_rdm_correlation_mean']:.3f}")

        report_lines.append(f"\nNull Distribution (Permuted Color Labels):")
        report_lines.append(f"  Disparity difference: mean={np.mean(null_disparity_diff):.4f}, std={np.std(null_disparity_diff):.4f}")
        report_lines.append(f"  HC RDM correlation: mean={np.mean(null_hc_rdm_corr):.3f}, std={np.std(null_hc_rdm_corr):.3f}")
        report_lines.append(f"  CVD RDM correlation: mean={np.mean(null_cvd_rdm_corr):.3f}, std={np.std(null_cvd_rdm_corr):.3f}")

        report_lines.append(f"\nPermutation Test Results:")
        report_lines.append(f"  Disparity difference: p={p_disparity:.4f} ({percentile_disparity:.1f}%ile)")
        report_lines.append(f"  HC RDM correlation: p={p_hc_rdm:.4f} ({percentile_hc_rdm:.1f}%ile)")
        report_lines.append(f"  CVD RDM correlation: p={p_cvd_rdm:.4f} ({percentile_cvd_rdm:.1f}%ile)")

        # Interpretation
        if p_disparity < 0.05 and p_hc_rdm < 0.05:
            report_lines.append(f"  ✅ PASS: Patterns depend on true color labels (not model artifact)")
            print(f"  ✅ PASS: Disparity p={p_disparity:.4f}, HC RDM p={p_hc_rdm:.4f}")
        else:
            report_lines.append(f"  ⚠️  WARNING: Patterns may be model artifact")
            print(f"  ⚠️  Disparity p={p_disparity:.4f}, HC RDM p={p_hc_rdm:.4f}")

    # Overall summary
    report_lines.append(f"\n{'='*80}")
    report_lines.append("OVERALL SUMMARY")
    report_lines.append(f"{'='*80}")

    significant_rois = []
    for roi, res in permutation_results.items():
        if res['p_values']['disparity_difference'] < 0.05 and res['p_values']['hc_rdm_correlation'] < 0.05:
            significant_rois.append(roi)

    report_lines.append(f"\nROIs with significant color label dependency: {len(significant_rois)}/{len(permutation_results)}")
    for roi in significant_rois:
        res = permutation_results[roi]
        report_lines.append(f"  ✅ {roi}: Disparity p={res['p_values']['disparity_difference']:.4f}, "
                          f"HC RDM p={res['p_values']['hc_rdm_correlation']:.4f}")

    report_lines.append(f"\nInterpretation:")
    report_lines.append(f"  - p < 0.05: Observed patterns REQUIRE true color labels")
    report_lines.append(f"  - p > 0.05: Patterns may be model structure artifact")

    if len(significant_rois) >= 2 and 'V1' in significant_rois and 'V2' in significant_rois:
        report_lines.append(f"\n✅ VALIDATION SUCCESSFUL: Patterns depend on color structure (not artifact)")
    else:
        report_lines.append(f"\n⚠️  VALIDATION UNCLEAR: Some ROIs may show artifacts")

    # Save results
    with open(results_dir / 'color_permutation_results.json', 'w') as f:
        json.dump(permutation_results, f, indent=2)

    with open(results_dir / 'color_permutation_report.txt', 'w') as f:
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

    # Load SRM-aligned patterns (use combined_with_aligned directory)
    srm_results_dir = base_dir / 'analysis' / 'phase2_SRM_across_between' / 'results' / 'c010' / 'combined_with_aligned'

    if not srm_results_dir.exists():
        raise FileNotFoundError(f"SRM results not found: {srm_results_dir}")

    print(f"Using SRM results: {srm_results_dir}")

    # Output directory
    output_dir = base_dir / 'analysis' / 'phase2_SRM_across_between' / 'validation' / '1D_permutation' / 'results'

    # Run color permutation test
    results = run_color_permutation_test(srm_results_dir, output_dir, n_permutations=1000)

    print("\n✅ Color label permutation testing completed!")
