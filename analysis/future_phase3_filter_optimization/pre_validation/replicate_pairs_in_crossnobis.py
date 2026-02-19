#!/usr/bin/env python3
"""
Replicate color-pair distance analysis in native voxel space using crossnobis distances.

Addresses Reviewer #2 Criticism 2: SRM circularity.

This script computes the same 28-pair CVD-HC difference analysis as B3, but using
cross-validated Mahalanobis distances (crossnobis) in native voxel space instead of
SRM-projected distances. If the same L-M axis deficits and S-cone compensations emerge,
the finding is SRM-independent.

Method:
1. Compute crossnobis RDM for each subject-ROI (Walther et al. 2016)
2. Extract 28 pairwise distances
3. Compute CVD z-scores relative to HC distribution (same as B3)
4. Apply global FDR correction
5. Compare to SRM-based results

Key difference from SRM analysis:
- SRM: distances measured in k=3-4 dimensional HC-optimized subspace
- Crossnobis: distances measured in full native voxel space with cross-validated noise covariance
"""

import numpy as np
import json
import time
from pathlib import Path
from itertools import combinations
from scipy.stats import norm, false_discovery_control, spearmanr
from sklearn.covariance import LedoitWolf


# ============================================================================
# CONFIG
# ============================================================================

HC_SUBJECTS = ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05', 'sub-06', 'sub-07']
CVD_SUBJECTS = ['sub-08', 'sub-09', 'sub-10']
ROIS = ['V1', 'V2', 'V3']  # V4/hV4 data incomplete
ROI_DIR_MAP = {'V1': 'V1', 'V2': 'V2', 'V3': 'V3'}

COLOR_LABELS = ['red', 'orange', 'yellow', 'green', 'cyan', 'blue', 'purple', 'magenta']
PAIR_LABELS = [f"{COLOR_LABELS[i]}-{COLOR_LABELS[j]}" for i in range(8) for j in range(i+1, 8)]

DATA_DIR = Path("/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis"
                "/analysis/phase1_preprocess_decoding/results/full_dataset_C010")

OUTPUT_DIR = Path(__file__).parent / "results" / "crossnobis_pairs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# CROSSNOBIS FUNCTIONS
# ============================================================================

def load_subject_data(subject, roi):
    """Load amplitudes_procrustes.npy → (6, 8, n_voxels)"""
    roi_dir = ROI_DIR_MAP.get(roi, roi)
    path = DATA_DIR / subject / roi_dir / "amplitudes_procrustes.npy"
    if not path.exists():
        print(f"  WARNING: {path} does not exist")
        return None
    return np.load(path)


def compute_crossnobis_rdm(data):
    """
    Compute cross-validated Mahalanobis (crossnobis) distance matrix.

    Parameters
    ----------
    data : ndarray, shape (n_runs, n_conditions, n_voxels)
        e.g. (6, 8, n_voxels)

    Returns
    -------
    rdm : ndarray, shape (n_conditions, n_conditions)
        Crossnobis distance matrix (symmetric, zero diagonal).
    """
    n_runs, n_cond, n_vox = data.shape

    if n_vox < 20:
        print(f"    WARNING: n_voxels={n_vox} < 20, Ledoit-Wolf may be imprecise")

    # Compute residuals for noise covariance estimation
    residuals = []
    for r in range(n_runs):
        run_mean = data[r].mean(axis=0, keepdims=True)  # (1, n_vox)
        residuals.append(data[r] - run_mean)  # (n_cond, n_vox)
    residuals = np.vstack(residuals)  # (n_runs * n_cond, n_vox)

    # Estimate noise covariance with Ledoit-Wolf shrinkage
    lw = LedoitWolf()
    lw.fit(residuals)
    sigma_inv = np.linalg.inv(lw.covariance_)  # (n_vox, n_vox)

    # Cross-validated Mahalanobis distance over all C(6,2)=15 run pairs
    rdm = np.zeros((n_cond, n_cond))
    n_pairs = 0

    for r1, r2 in combinations(range(n_runs), 2):
        for i in range(n_cond):
            for j in range(i + 1, n_cond):
                # Cross-validated: use difference from run1 × difference from run2
                diff_r1 = data[r1, i] - data[r1, j]  # (n_vox,)
                diff_r2 = data[r2, i] - data[r2, j]  # (n_vox,)
                # Crossnobis = diff1 @ sigma_inv @ diff2
                d = diff_r1 @ sigma_inv @ diff_r2
                rdm[i, j] += d
                rdm[j, i] += d
        n_pairs += 1

    rdm /= n_pairs  # Average over run pairs
    return rdm


def rdm_to_pairs(rdm):
    """Extract 28 pairwise distances from 8×8 RDM."""
    pairs = []
    for i in range(8):
        for j in range(i+1, 8):
            pairs.append(rdm[i, j])
    return np.array(pairs)


# ============================================================================
# MAIN ANALYSIS
# ============================================================================

def main():
    print("=" * 80)
    print("CROSSNOBIS COLOR-PAIR ANALYSIS (SRM-independent replication)")
    print("=" * 80)

    start_time = time.time()

    # Storage for results
    results = {
        'config': {
            'method': 'crossnobis_pair_distances',
            'description': 'SRM-independent replication of color-pair CVD-HC differences',
            'reference': 'Walther et al. (2016). Reliability of dissimilarity measures for RSA',
            'hc_subjects': HC_SUBJECTS,
            'cvd_subjects': CVD_SUBJECTS,
            'rois': ROIS,
            'pair_labels': PAIR_LABELS
        },
        'by_subject_roi': {}
    }

    # Step 1: Compute crossnobis RDMs for all subjects
    print("\nStep 1: Computing crossnobis RDMs in native voxel space...")
    crossnobis_rdms = {}

    for roi in ROIS:
        print(f"\n{roi}:")
        crossnobis_rdms[roi] = {}

        for subject in HC_SUBJECTS + CVD_SUBJECTS:
            data = load_subject_data(subject, roi)
            if data is None:
                continue

            n_runs, n_cond, n_vox = data.shape
            print(f"  {subject}: {n_vox} voxels, {n_runs} runs, {n_cond} conditions")

            rdm = compute_crossnobis_rdm(data)
            crossnobis_rdms[roi][subject] = rdm

    # Step 2: Extract 28-pair distances and compute z-scores
    print("\nStep 2: Computing CVD z-scores relative to HC distribution...")
    all_pvalues = []
    all_test_ids = []

    for cvd_subject in CVD_SUBJECTS:
        results['by_subject_roi'][cvd_subject] = {}

        for roi in ROIS:
            print(f"\n{cvd_subject} {roi}:")

            # HC pairwise distances
            hc_pair_dists = []
            for hc_subject in HC_SUBJECTS:
                if hc_subject in crossnobis_rdms[roi]:
                    pairs = rdm_to_pairs(crossnobis_rdms[roi][hc_subject])
                    hc_pair_dists.append(pairs)

            if len(hc_pair_dists) < 3:
                print(f"  SKIP: Insufficient HC data ({len(hc_pair_dists)} subjects)")
                continue

            hc_pair_dists = np.array(hc_pair_dists)  # (n_hc, 28)
            hc_mean = hc_pair_dists.mean(axis=0)  # (28,)
            hc_std = hc_pair_dists.std(axis=0, ddof=1)  # (28,)

            # CVD pairwise distances
            if cvd_subject not in crossnobis_rdms[roi]:
                print(f"  SKIP: No CVD data")
                continue

            cvd_pairs = rdm_to_pairs(crossnobis_rdms[roi][cvd_subject])  # (28,)

            # Z-scores
            z_scores = (cvd_pairs - hc_mean) / (hc_std + 1e-10)

            # P-values from z-scores
            pvalues = 2 * (1 - norm.cdf(np.abs(z_scores)))

            # Store results
            results['by_subject_roi'][cvd_subject][roi] = {
                'hc_mean': hc_mean.tolist(),
                'hc_std': hc_std.tolist(),
                'cvd_distances': cvd_pairs.tolist(),
                'z_scores': z_scores.tolist(),
                'p_values': pvalues.tolist(),
                'pairs': {}
            }

            for i, pair_label in enumerate(PAIR_LABELS):
                results['by_subject_roi'][cvd_subject][roi]['pairs'][pair_label] = {
                    'hc_mean': float(hc_mean[i]),
                    'hc_std': float(hc_std[i]),
                    'cvd_distance': float(cvd_pairs[i]),
                    'z_score': float(z_scores[i]),
                    'p_value': float(pvalues[i])
                }

                all_pvalues.append(pvalues[i])
                all_test_ids.append({
                    'subject': cvd_subject,
                    'roi': roi,
                    'pair': pair_label,
                    'z_score': float(z_scores[i]),
                    'p_value': float(pvalues[i])
                })

            # Report extreme pairs
            extreme_idx = np.where(np.abs(z_scores) > 1.5)[0]
            print(f"  {len(extreme_idx)}/28 pairs with |z| > 1.5")
            for idx in extreme_idx[:5]:
                print(f"    {PAIR_LABELS[idx]}: z={z_scores[idx]:.2f}, p={pvalues[idx]:.4f}")

    # Step 3: Apply global FDR correction
    print("\nStep 3: Applying global FDR correction...")
    all_pvalues = np.array(all_pvalues)
    pvalues_adjusted_global = false_discovery_control(all_pvalues, method='bh')
    reject_global = pvalues_adjusted_global < 0.05

    n_total = len(all_pvalues)
    n_raw_sig = np.sum(all_pvalues < 0.05)
    n_fdr_sig = np.sum(reject_global)

    print(f"  Total tests: {n_total}")
    print(f"  Raw significant (p<0.05): {n_raw_sig} ({100*n_raw_sig/n_total:.1f}%)")
    print(f"  FDR significant (q<0.05): {n_fdr_sig} ({100*n_fdr_sig/n_total:.1f}%)")

    # Add FDR results to test records
    for i, test_record in enumerate(all_test_ids):
        test_record['fdr_global'] = bool(reject_global[i])
        test_record['p_adjusted'] = float(pvalues_adjusted_global[i])

    results['all_tests'] = all_test_ids
    results['summary'] = {
        'total_tests': n_total,
        'n_raw_significant': int(n_raw_sig),
        'n_fdr_significant': int(n_fdr_sig)
    }

    # Step 4: Identify filter targets surviving FDR
    print("\nStep 4: Filter targets surviving global FDR correction...")
    priority_pairs_original = {
        'HIGH': ['red-orange', 'orange-yellow', 'cyan-blue'],
        'MEDIUM': ['red-magenta', 'blue-purple', 'red-green']
    }

    results['filter_targets'] = {
        'original_priority_pairs': priority_pairs_original,
        'fdr_surviving_by_subject': {}
    }

    for cvd_subject in CVD_SUBJECTS:
        surviving_high = []
        surviving_medium = []
        surviving_other = []

        for test_record in all_test_ids:
            if test_record['subject'] == cvd_subject and test_record['fdr_global']:
                pair = test_record['pair']
                if pair in priority_pairs_original['HIGH']:
                    surviving_high.append({
                        'pair': pair,
                        'roi': test_record['roi'],
                        'z_score': test_record['z_score'],
                        'p_value': test_record['p_value']
                    })
                elif pair in priority_pairs_original['MEDIUM']:
                    surviving_medium.append({
                        'pair': pair,
                        'roi': test_record['roi'],
                        'z_score': test_record['z_score'],
                        'p_value': test_record['p_value']
                    })
                elif abs(test_record['z_score']) > 1.5:
                    surviving_other.append({
                        'pair': pair,
                        'roi': test_record['roi'],
                        'z_score': test_record['z_score'],
                        'p_value': test_record['p_value']
                    })

        results['filter_targets']['fdr_surviving_by_subject'][cvd_subject] = {
            'HIGH_priority': surviving_high,
            'MEDIUM_priority': surviving_medium,
            'OTHER_extreme': surviving_other,
            'total_surviving': len(surviving_high) + len(surviving_medium) + len(surviving_other)
        }

        print(f"\n{cvd_subject}: {len(surviving_high)} HIGH, {len(surviving_medium)} MEDIUM, "
              f"{len(surviving_other)} OTHER pairs survive global FDR")

    # Step 5: Load SRM-based results for comparison
    print("\nStep 5: Loading SRM-based results for comparison...")
    srm_results_path = Path(__file__).parent / "results" / "fdr_corrected" / "filter_pre_validation_fdr_corrected.json"

    if srm_results_path.exists():
        with open(srm_results_path) as f:
            srm_data = json.load(f)

        # Compare z-score correlation between SRM and crossnobis
        comparison = {}

        for cvd_subject in CVD_SUBJECTS:
            comparison[cvd_subject] = {}

            for roi in ROIS:
                if roi not in results['by_subject_roi'].get(cvd_subject, {}):
                    continue
                if roi not in srm_data['by_subject_roi'].get(cvd_subject, {}):
                    continue

                crossnobis_z = np.array(results['by_subject_roi'][cvd_subject][roi]['z_scores'])
                srm_z = []

                for pair_label in PAIR_LABELS:
                    if pair_label in srm_data['by_subject_roi'][cvd_subject][roi]['pairs']:
                        srm_z.append(srm_data['by_subject_roi'][cvd_subject][roi]['pairs'][pair_label]['z_score'])
                    else:
                        srm_z.append(np.nan)

                srm_z = np.array(srm_z)

                # Correlation (excluding NaNs)
                valid = ~np.isnan(srm_z)
                if np.sum(valid) > 5:
                    r, p = spearmanr(crossnobis_z[valid], srm_z[valid])
                    comparison[cvd_subject][roi] = {
                        'spearman_r': float(r),
                        'p_value': float(p),
                        'n_pairs': int(np.sum(valid))
                    }
                    print(f"  {cvd_subject} {roi}: r={r:.3f}, p={p:.4f} (n={np.sum(valid)} pairs)")

        results['srm_comparison'] = comparison
    else:
        print("  SRM results not found for comparison")

    # Save results
    results['elapsed_sec'] = time.time() - start_time
    output_path = OUTPUT_DIR / 'crossnobis_pair_analysis.json'

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to {output_path}")
    print(f"Total time: {results['elapsed_sec']:.1f} sec")

    # Generate summary report
    generate_summary_report(results, OUTPUT_DIR)


def generate_summary_report(results, output_dir):
    """Generate human-readable summary report."""

    report_path = output_dir / 'CROSSNOBIS_REPLICATION_REPORT.md'

    with open(report_path, 'w') as f:
        f.write("# Crossnobis Color-Pair Replication Report\n\n")
        f.write("**Addresses**: Reviewer #2 Criticism 2 (SRM circularity)\n\n")
        f.write("**Method**: Cross-validated Mahalanobis distances in native voxel space (SRM-independent)\n\n")
        f.write("**Reference**: Walther et al. (2016). Reliability of dissimilarity measures for RSA. *NeuroImage*.\n\n")
        f.write("---\n\n")

        # Overall summary
        f.write("## Overall Summary\n\n")
        f.write("| Metric | Count | Percentage |\n")
        f.write("|--------|-------|------------|\n")
        f.write(f"| Total tests | {results['summary']['total_tests']} | 100% |\n")
        f.write(f"| Raw significant (p<0.05) | {results['summary']['n_raw_significant']} | "
                f"{100 * results['summary']['n_raw_significant'] / results['summary']['total_tests']:.1f}% |\n")
        f.write(f"| FDR significant (q<0.05) | {results['summary']['n_fdr_significant']} | "
                f"{100 * results['summary']['n_fdr_significant'] / results['summary']['total_tests']:.1f}% |\n\n")

        # Filter targets
        f.write("## Filter Targets Surviving Global FDR\n\n")
        for subject in CVD_SUBJECTS:
            targets = results['filter_targets']['fdr_surviving_by_subject'][subject]
            f.write(f"### {subject}: {targets['total_surviving']} total pairs\n\n")

            if targets['HIGH_priority']:
                f.write("**HIGH priority pairs**:\n\n")
                f.write("| Pair | ROI | z-score | p-value |\n")
                f.write("|------|-----|---------|----------|\n")
                for item in targets['HIGH_priority']:
                    f.write(f"| {item['pair']} | {item['roi']} | {item['z_score']:.2f} | {item['p_value']:.4f} |\n")
                f.write("\n")
            else:
                f.write("**HIGH priority pairs**: None survive FDR ❌\n\n")

            if targets['MEDIUM_priority']:
                f.write("**MEDIUM priority pairs**:\n\n")
                f.write("| Pair | ROI | z-score | p-value |\n")
                f.write("|------|-----|---------|----------|\n")
                for item in targets['MEDIUM_priority']:
                    f.write(f"| {item['pair']} | {item['roi']} | {item['z_score']:.2f} | {item['p_value']:.4f} |\n")
                f.write("\n")

        # SRM comparison
        if 'srm_comparison' in results:
            f.write("---\n\n")
            f.write("## Comparison to SRM-Based Analysis\n\n")
            f.write("Correlation between crossnobis z-scores and SRM z-scores:\n\n")
            f.write("| Subject | ROI | Spearman r | p-value | Interpretation |\n")
            f.write("|---------|-----|------------|---------|----------------|\n")

            for subject in CVD_SUBJECTS:
                if subject in results['srm_comparison']:
                    for roi in ROIS:
                        if roi in results['srm_comparison'][subject]:
                            comp = results['srm_comparison'][subject][roi]
                            r = comp['spearman_r']
                            p = comp['p_value']

                            if r > 0.5 and p < 0.05:
                                interp = "✅ Strong convergence"
                            elif r > 0.3:
                                interp = "⚠️ Moderate convergence"
                            elif r < 0:
                                interp = "❌ Divergence (artifact?)"
                            else:
                                interp = "⚠️ Weak convergence"

                            f.write(f"| {subject} | {roi} | {r:.3f} | {p:.4f} | {interp} |\n")

            f.write("\n**Interpretation**: If r > 0.5, the same pair-distance patterns emerge in both "
                   "SRM-projected space and native voxel space, confirming that SRM is not creating artifacts.\n\n")

        f.write("---\n\n")
        f.write("## Method Details\n\n")
        f.write("### Crossnobis Distance (Walther et al. 2016)\n\n")
        f.write("Cross-validated Mahalanobis distance that controls for noise correlations:\n\n")
        f.write("1. Estimate noise covariance Σ from residuals (Ledoit-Wolf shrinkage)\n")
        f.write("2. For each pair of conditions (i,j), compute over all C(6,2)=15 run pairs:\n")
        f.write("   ```\n")
        f.write("   d_crossnobis(i,j) = (X_r1,i - X_r1,j)ᵀ Σ⁻¹ (X_r2,i - X_r2,j)\n")
        f.write("   ```\n")
        f.write("3. Average over run pairs → unbiased distance matrix\n\n")
        f.write("**Key advantage**: Computed in full native voxel space (no dimensionality reduction), "
               "completely independent of SRM.\n\n")

    print(f"Summary report saved to {report_path}")


if __name__ == '__main__':
    main()
