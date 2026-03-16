#!/usr/bin/env python3
"""
Apply FDR correction to B3 bootstrap results from filter pre-validation.

Addresses Reviewer #2 Criticism 1: Multiple comparisons correction across
28 color pairs × 4 ROIs × 3 CVD subjects = 336 tests.

Method:
- Benjamini-Hochberg FDR correction (q=0.05)
- Applied separately for each subject-ROI combination (28 pairs per test)
- Also applied globally across all 336 tests for conservative estimate
"""

import json
import numpy as np
from pathlib import Path
from scipy.stats import false_discovery_control
from datetime import datetime


def apply_fdr_correction(results_path, output_dir, q=0.05):
    """
    Apply FDR correction to B3 bootstrap results.

    Parameters
    ----------
    results_path : Path
        Path to filter_pre_validation_results.json
    output_dir : Path
        Output directory for corrected results
    q : float
        FDR threshold (default 0.05)
    """
    print(f"Loading results from {results_path}...")
    with open(results_path, 'r') as f:
        results = json.load(f)

    # Extract all ROIs and subjects
    rois = ['V1', 'V2', 'V3', 'V4']
    cvd_subjects = ['sub-08', 'sub-09', 'sub-10']

    # Storage for FDR-corrected results
    fdr_results = {
        'config': {
            'original_results': str(results_path),
            'fdr_method': 'Benjamini-Hochberg',
            'fdr_threshold': q,
            'timestamp': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'correction_levels': [
                'within_subject_roi (28 pairs per test)',
                'global_all_tests (336 total tests)'
            ]
        },
        'method_explanation': {
            'problem': 'Testing 28 color pairs × 4 ROIs × 3 CVD subjects = 336 comparisons without correction leads to ~17 false positives by chance (336 × 0.05)',
            'solution': 'Benjamini-Hochberg FDR correction controls the expected proportion of false discoveries among all rejected hypotheses',
            'implementation': 'Applied at two levels: (1) within each subject-ROI (28 tests), (2) globally across all 336 tests',
            'reference': 'Benjamini & Hochberg (1995). Journal of the Royal Statistical Society, Series B.'
        },
        'summary': {
            'total_tests': 0,
            'significant_raw_count': 0,
            'significant_within_roi_fdr_count': 0,
            'significant_global_fdr_count': 0
        },
        'by_subject_roi': {}
    }

    # Collect all p-values for global FDR
    all_pvalues = []
    all_test_ids = []

    # Process each subject and ROI
    for subject in cvd_subjects:
        fdr_results['by_subject_roi'][subject] = {}

        for roi in rois:
            # Get B3 bootstrap results
            try:
                b3_data = results['results'][roi]['B3_bootstrap']['per_subject'][subject]
            except KeyError:
                print(f"Warning: No B3 data for {subject} {roi}")
                continue

            pair_labels = results['config']['pair_labels']
            n_pairs = len(pair_labels)

            # Extract z-scores and CIs
            z_scores = np.array(b3_data['z_mean'])
            ci_lower = np.array(b3_data['ci_lower'])
            ci_upper = np.array(b3_data['ci_upper'])

            # Determine which CIs exclude zero
            ci_exclude_zero = ~((ci_lower <= 0) & (ci_upper >= 0))

            # Convert "CI excludes zero" to p-values (approximate)
            # For bootstrap CI, if CI excludes zero, approximate p-value is related to
            # the proportion of bootstrap samples on the wrong side of zero
            # Here we use a conservative approach: if CI excludes zero, p = 0.05/2 = 0.025
            # (one-tailed), otherwise p = 1.0
            #
            # More accurate: use the bootstrap distribution to compute exact p-values
            # But this requires the full bootstrap samples, not just CIs
            #
            # Alternative: treat as two-sample t-test with normal approximation
            # p-value from z-score: 2 * (1 - norm.cdf(abs(z)))
            from scipy.stats import norm
            pvalues = 2 * (1 - norm.cdf(np.abs(z_scores)))

            # Within-ROI FDR correction (28 pairs)
            pvalues_adjusted_within_roi = false_discovery_control(pvalues, method='bh')
            reject_within_roi = pvalues_adjusted_within_roi < q

            # Store for global FDR
            for i, pair_label in enumerate(pair_labels):
                all_pvalues.append(pvalues[i])
                all_test_ids.append({
                    'subject': subject,
                    'roi': roi,
                    'pair': pair_label,
                    'z_score': float(z_scores[i]),
                    'p_value': float(pvalues[i]),
                    'ci_lower': float(ci_lower[i]),
                    'ci_upper': float(ci_upper[i]),
                    'raw_significant': bool(ci_exclude_zero[i]),
                    'fdr_within_roi': bool(reject_within_roi[i])
                })

            # Store results for this subject-ROI
            fdr_results['by_subject_roi'][subject][roi] = {
                'n_pairs': n_pairs,
                'n_significant_raw': int(np.sum(ci_exclude_zero)),
                'n_significant_fdr_within_roi': int(np.sum(reject_within_roi)),
                'pairs': {}
            }

            for i, pair_label in enumerate(pair_labels):
                fdr_results['by_subject_roi'][subject][roi]['pairs'][pair_label] = {
                    'z_score': float(z_scores[i]),
                    'p_value': float(pvalues[i]),
                    'ci_lower': float(ci_lower[i]),
                    'ci_upper': float(ci_upper[i]),
                    'significant_raw': bool(ci_exclude_zero[i]),
                    'significant_fdr_within_roi': bool(reject_within_roi[i])
                }

            # Update summary counts
            fdr_results['summary']['total_tests'] += n_pairs
            fdr_results['summary']['significant_raw_count'] += int(np.sum(ci_exclude_zero))
            fdr_results['summary']['significant_within_roi_fdr_count'] += int(np.sum(reject_within_roi))

            print(f"{subject} {roi}: {n_pairs} pairs, "
                  f"{int(np.sum(ci_exclude_zero))} raw sig, "
                  f"{int(np.sum(reject_within_roi))} FDR sig (within-ROI)")

    # Global FDR correction across all 336 tests
    print(f"\nApplying global FDR correction across all {len(all_pvalues)} tests...")
    all_pvalues = np.array(all_pvalues)
    pvalues_adjusted_global = false_discovery_control(all_pvalues, method='bh')
    reject_global = pvalues_adjusted_global < q

    # Update test records with global FDR results
    for i, test_record in enumerate(all_test_ids):
        test_record['fdr_global'] = bool(reject_global[i])
        if reject_global[i]:
            fdr_results['summary']['significant_global_fdr_count'] += 1

    # Store all test results
    fdr_results['all_tests'] = all_test_ids

    # Identify high-priority pairs that survive global FDR
    print("\nIdentifying filter targets that survive global FDR correction...")
    priority_pairs_original = {
        'HIGH': ['red-orange', 'orange-yellow', 'cyan-blue'],
        'MEDIUM': ['red-magenta', 'blue-purple', 'red-green']
    }

    fdr_results['filter_targets'] = {
        'original_priority_pairs': priority_pairs_original,
        'fdr_surviving_by_subject': {}
    }

    for subject in cvd_subjects:
        surviving_high = []
        surviving_medium = []
        surviving_other = []

        for test_record in all_test_ids:
            if test_record['subject'] == subject and test_record['fdr_global']:
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
                elif abs(test_record['z_score']) > 1.5:  # Other extreme pairs
                    surviving_other.append({
                        'pair': pair,
                        'roi': test_record['roi'],
                        'z_score': test_record['z_score'],
                        'p_value': test_record['p_value']
                    })

        fdr_results['filter_targets']['fdr_surviving_by_subject'][subject] = {
            'HIGH_priority': surviving_high,
            'MEDIUM_priority': surviving_medium,
            'OTHER_extreme': surviving_other,
            'total_surviving': len(surviving_high) + len(surviving_medium) + len(surviving_other)
        }

        print(f"\n{subject}: {len(surviving_high)} HIGH, {len(surviving_medium)} MEDIUM, "
              f"{len(surviving_other)} OTHER pairs survive global FDR")

    # Save results
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / 'filter_pre_validation_fdr_corrected.json'

    with open(output_path, 'w') as f:
        json.dump(fdr_results, f, indent=2)

    print(f"\nFDR-corrected results saved to {output_path}")

    # Generate summary report
    generate_summary_report(fdr_results, output_dir)

    return fdr_results


def generate_summary_report(fdr_results, output_dir):
    """Generate human-readable summary report."""

    report_path = output_dir / 'FDR_CORRECTION_REPORT.md'

    with open(report_path, 'w') as f:
        f.write("# FDR Correction Report: Filter Pre-Validation B3 Bootstrap Results\n\n")
        f.write(f"**Generated**: {fdr_results['config']['timestamp']}\n\n")
        f.write("**Addresses**: Reviewer #2 Criticism 1 (Multiple comparisons catastrophe)\n\n")
        f.write("---\n\n")

        # Method explanation
        f.write("## Method: Benjamini-Hochberg FDR Correction\n\n")
        f.write("### Problem\n\n")
        f.write(f"{fdr_results['method_explanation']['problem']}\n\n")
        f.write("### Solution\n\n")
        f.write(f"{fdr_results['method_explanation']['solution']}\n\n")
        f.write("**Reference**: Benjamini, Y., & Hochberg, Y. (1995). Controlling the false discovery rate: "
                "a practical and powerful approach to multiple testing. *Journal of the Royal Statistical Society: "
                "Series B (Methodological)*, 57(1), 289-300.\n\n")

        f.write("### Implementation Details\n\n")
        f.write("1. **P-value derivation**: Converted bootstrap z-scores to p-values using normal approximation: "
                "`p = 2 × (1 - Φ(|z|))` where Φ is the standard normal CDF.\n\n")
        f.write("2. **FDR correction levels**:\n")
        f.write("   - **Within subject-ROI**: 28 pairs per test (less conservative, detects ROI-specific effects)\n")
        f.write("   - **Global**: All 336 tests combined (most conservative, controls family-wise FDR)\n\n")
        f.write(f"3. **FDR threshold**: q = {fdr_results['config']['fdr_threshold']}\n\n")

        # Overall summary
        f.write("---\n\n")
        f.write("## Overall Summary\n\n")
        f.write("| Metric | Count | Percentage |\n")
        f.write("|--------|-------|------------|\n")
        f.write(f"| Total tests | {fdr_results['summary']['total_tests']} | 100% |\n")
        f.write(f"| Significant (raw, no correction) | {fdr_results['summary']['significant_raw_count']} | "
                f"{100 * fdr_results['summary']['significant_raw_count'] / fdr_results['summary']['total_tests']:.1f}% |\n")
        f.write(f"| Significant (FDR within-ROI) | {fdr_results['summary']['significant_within_roi_fdr_count']} | "
                f"{100 * fdr_results['summary']['significant_within_roi_fdr_count'] / fdr_results['summary']['total_tests']:.1f}% |\n")
        f.write(f"| Significant (FDR global) | {fdr_results['summary']['significant_global_fdr_count']} | "
                f"{100 * fdr_results['summary']['significant_global_fdr_count'] / fdr_results['summary']['total_tests']:.1f}% |\n\n")

        f.write(f"**Key finding**: After global FDR correction, "
                f"{fdr_results['summary']['significant_global_fdr_count']} out of "
                f"{fdr_results['summary']['total_tests']} tests survive "
                f"({100 * fdr_results['summary']['significant_global_fdr_count'] / fdr_results['summary']['total_tests']:.1f}%), "
                f"down from {fdr_results['summary']['significant_raw_count']} raw significant "
                f"({100 * fdr_results['summary']['significant_raw_count'] / fdr_results['summary']['total_tests']:.1f}%).\n\n")

        # Per-subject summary
        f.write("---\n\n")
        f.write("## Per-Subject Summary\n\n")

        for subject in ['sub-08', 'sub-09', 'sub-10']:
            f.write(f"### {subject}\n\n")
            f.write("| ROI | Raw Sig | FDR Within-ROI | FDR Global |\n")
            f.write("|-----|---------|----------------|------------|\n")

            for roi in ['V1', 'V2', 'V3', 'V4']:
                if roi in fdr_results['by_subject_roi'][subject]:
                    data = fdr_results['by_subject_roi'][subject][roi]
                    # Count global FDR sig for this subject-ROI
                    global_sig = sum(1 for test in fdr_results['all_tests']
                                   if test['subject'] == subject and test['roi'] == roi and test['fdr_global'])
                    f.write(f"| {roi} | {data['n_significant_raw']}/28 | "
                           f"{data['n_significant_fdr_within_roi']}/28 | {global_sig}/28 |\n")
            f.write("\n")

        # Filter targets that survive FDR
        f.write("---\n\n")
        f.write("## Filter Targets: Pairs Surviving Global FDR Correction\n\n")
        f.write("Original priority pairs from filter_design_plan.md section 4.3:\n")
        f.write("- **HIGH**: red-orange, orange-yellow, cyan-blue\n")
        f.write("- **MEDIUM**: red-magenta, blue-purple, red-green\n\n")

        for subject in ['sub-08', 'sub-09', 'sub-10']:
            targets = fdr_results['filter_targets']['fdr_surviving_by_subject'][subject]
            f.write(f"### {subject}: {targets['total_surviving']} total pairs survive global FDR\n\n")

            if targets['HIGH_priority']:
                f.write("**HIGH priority pairs (surviving)**:\n\n")
                f.write("| Pair | ROI | z-score | p-value |\n")
                f.write("|------|-----|---------|----------|\n")
                for item in targets['HIGH_priority']:
                    f.write(f"| {item['pair']} | {item['roi']} | {item['z_score']:.2f} | {item['p_value']:.4f} |\n")
                f.write("\n")
            else:
                f.write("**HIGH priority pairs**: None survive global FDR ❌\n\n")

            if targets['MEDIUM_priority']:
                f.write("**MEDIUM priority pairs (surviving)**:\n\n")
                f.write("| Pair | ROI | z-score | p-value |\n")
                f.write("|------|-----|---------|----------|\n")
                for item in targets['MEDIUM_priority']:
                    f.write(f"| {item['pair']} | {item['roi']} | {item['z_score']:.2f} | {item['p_value']:.4f} |\n")
                f.write("\n")
            else:
                f.write("**MEDIUM priority pairs**: None survive global FDR ❌\n\n")

            if targets['OTHER_extreme']:
                f.write("**OTHER extreme pairs** (|z| > 1.5, surviving global FDR):\n\n")
                f.write("| Pair | ROI | z-score | p-value |\n")
                f.write("|------|-----|---------|----------|\n")
                for item in sorted(targets['OTHER_extreme'], key=lambda x: abs(x['z_score']), reverse=True)[:10]:
                    f.write(f"| {item['pair']} | {item['roi']} | {item['z_score']:.2f} | {item['p_value']:.4f} |\n")
                if len(targets['OTHER_extreme']) > 10:
                    f.write(f"\n*({len(targets['OTHER_extreme']) - 10} more pairs not shown)*\n")
                f.write("\n")

        # Interpretation
        f.write("---\n\n")
        f.write("## Interpretation & Implications for Filter Design\n\n")

        total_surviving = sum(fdr_results['filter_targets']['fdr_surviving_by_subject'][s]['total_surviving']
                            for s in ['sub-08', 'sub-09', 'sub-10'])

        if total_surviving >= 10:
            f.write(f"✅ **Sufficient statistical basis**: {total_surviving} pairs survive global FDR across 3 subjects. "
                   "Filter design can proceed with FDR-surviving pairs as targets.\n\n")
        elif total_surviving >= 5:
            f.write(f"⚠️ **Marginal statistical basis**: {total_surviving} pairs survive global FDR. "
                   "Filter design should focus on most robust pairs and include sensitivity analysis.\n\n")
        else:
            f.write(f"❌ **Insufficient statistical basis**: Only {total_surviving} pairs survive global FDR. "
                   "Filter design lacks sufficient evidence. Consider:\n"
                   "- Reframe as exploratory/pilot study\n"
                   "- Use within-ROI FDR (less conservative) with explicit justification\n"
                   "- Collect additional subjects before filter implementation\n\n")

        f.write("**Recommendation**: Update filter pair weights (filter_design_plan.md section 4.3) to reflect "
               "only FDR-surviving pairs. Any pairs not surviving global FDR should be downweighted to w=1.0 "
               "(preserve) rather than 2.0-3.0 (target for correction).\n\n")

        f.write("---\n\n")
        f.write("## Method Comparison: Within-ROI vs Global FDR\n\n")
        f.write("| Approach | Pros | Cons | Use Case |\n")
        f.write("|----------|------|------|----------|\n")
        f.write("| **Within-ROI FDR** | Detects ROI-specific effects; More power; "
               "Appropriate if ROIs are independent questions | May miss familywise error control; "
               "Not appropriate for filter design across all ROIs | Characterization paper focusing on per-ROI patterns |\n")
        f.write("| **Global FDR** | Controls false discoveries across all tests; "
               "Most conservative; Appropriate for filter design | Lower power; "
               "May be overly conservative if ROIs truly independent | Filter design paper making translational claims |\n\n")

        f.write("**For this project**: Use **global FDR** for filter target selection (translational claims require "
               "stringent control). Report within-ROI FDR in supplementary materials for characterization purposes.\n\n")

    print(f"Summary report saved to {report_path}")


if __name__ == '__main__':
    # Paths
    base_dir = Path(__file__).parent
    results_path = base_dir / 'results' / 'filter_pre_validation_results.json'
    output_dir = base_dir / 'results' / 'fdr_corrected'

    # Apply FDR correction
    fdr_results = apply_fdr_correction(results_path, output_dir, q=0.05)

    print("\n" + "="*80)
    print("FDR CORRECTION COMPLETE")
    print("="*80)
    print(f"\nRaw significant: {fdr_results['summary']['significant_raw_count']}/{fdr_results['summary']['total_tests']}")
    print(f"FDR within-ROI significant: {fdr_results['summary']['significant_within_roi_fdr_count']}/{fdr_results['summary']['total_tests']}")
    print(f"FDR global significant: {fdr_results['summary']['significant_global_fdr_count']}/{fdr_results['summary']['total_tests']}")
    print("\nSee results/fdr_corrected/FDR_CORRECTION_REPORT.md for full report.")
