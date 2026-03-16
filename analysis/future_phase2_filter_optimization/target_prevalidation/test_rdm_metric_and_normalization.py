#!/usr/bin/env python3
"""
Test RDM Metric and Normalization Sensitivity

Tests two critical methodological choices:
1. RDM distance metric: Correlation vs Crossnobis (in SRM space)
2. Z-normalization: Raw vs Within-subject vs Pooled normalization

Addresses user questions:
- Q1: Does crossnobis method in SRM space give same results as correlation?
- Q2: Does z-normalization of RDM values change FDR results?

Usage:
  python test_rdm_metric_and_normalization.py [--output_dir PATH]
"""

import numpy as np
import json
import sys
from pathlib import Path
from datetime import datetime
from scipy.spatial.distance import pdist, squareform
from scipy.stats import spearmanr
import warnings
warnings.filterwarnings('ignore')

# Add utils to path
SCRIPT_DIR = Path(__file__).parent
VALIDATION_DIR = SCRIPT_DIR.parent.parent / 'validation/scripts'
sys.path.insert(0, str(VALIDATION_DIR))

try:
    from utils.crossnobis_ldw import compute_rdm_crossnobis
except ImportError:
    print(f"ERROR: Cannot import crossnobis_ldw")
    print(f"Searched in: {VALIDATION_DIR}")
    print(f"sys.path: {sys.path[:3]}")
    raise

# ============================================================================
# CONFIG
# ============================================================================

HC_SUBJECTS = [f'sub-{i:02d}' for i in range(1, 8)]
CVD_SUBJECTS = [f'sub-{i:02d}' for i in range(8, 11)]
ROIS = ['V1', 'V2', 'V3', 'hV4']
ROI_DIRS = {'V1': 'V1', 'V2': 'V2', 'V3': 'V3', 'hV4': 'V4'}

COLOR_NAMES = ['red', 'orange', 'yellow', 'green', 'cyan', 'blue', 'purple', 'magenta']
N_COLORS = 8

# Color pair indices
PAIR_INDICES = [(i, j) for i in range(N_COLORS) for j in range(i + 1, N_COLORS)]
PAIR_LABELS = [f"{COLOR_NAMES[i]}-{COLOR_NAMES[j]}" for i, j in PAIR_INDICES]
N_PAIRS = len(PAIR_LABELS)  # 28

SCRIPT_PATH = Path(__file__).resolve()
# Script is in: analysis/future_phase2_filter_optimization/pre_validation/
# Data is in:   analysis/phase1_preprocess_decoding/results/full_dataset_C010/
DATA_DIR = SCRIPT_PATH.parent.parent.parent / 'phase1_preprocess_decoding/results/full_dataset_C010'

# Load FDR results for comparison
FDR_PATH = Path(__file__).parent / 'results/fdr_corrected/filter_pre_validation_fdr_corrected.json'

# ============================================================================
# RDM COMPUTATION
# ============================================================================

def compute_rdm_correlation(amplitudes):
    """
    Compute RDM using correlation distance (current method).

    Parameters
    ----------
    amplitudes : np.ndarray, shape (6, 8, n_voxels)
        Amplitudes in SRM space

    Returns
    -------
    rdm : np.ndarray, shape (28,)
        Upper triangle of 8x8 RDM (correlation distance)
    """
    patterns = amplitudes.mean(axis=0)  # (8, n_voxels)
    rdm_full = squareform(pdist(patterns, metric='correlation'))

    # Extract upper triangle
    triu_idx = np.triu_indices(N_COLORS, k=1)
    rdm = rdm_full[triu_idx]

    return rdm


def compute_rdm_crossnobis_srm(amplitudes):
    """
    Compute RDM using crossnobis method in SRM space.

    Parameters
    ----------
    amplitudes : np.ndarray, shape (6, 8, n_voxels)
        Amplitudes in SRM space

    Returns
    -------
    rdm : np.ndarray, shape (28,)
        Upper triangle of 8x8 RDM (Mahalanobis distance)
    shrinkage : float
        Ledoit-Wolf shrinkage parameter
    """
    rdm_full, shrinkage = compute_rdm_crossnobis(amplitudes, use_shrinkage=True)

    # Extract upper triangle
    triu_idx = np.triu_indices(N_COLORS, k=1)
    rdm = rdm_full[triu_idx]

    return rdm, shrinkage


# ============================================================================
# NORMALIZATION METHODS
# ============================================================================

def normalize_rdm_none(rdm):
    """No normalization (current method)."""
    return rdm


def normalize_rdm_within(rdm):
    """Within-subject z-normalization."""
    return (rdm - rdm.mean()) / rdm.std()


def normalize_rdm_pooled(rdm, pooled_mean, pooled_std):
    """Pooled z-normalization using HC pooled statistics."""
    return (rdm - pooled_mean) / pooled_std


# ============================================================================
# CRAWFORD & HOWELL TEST
# ============================================================================

def crawford_howell_test(cvd_value, hc_values):
    """
    Crawford & Howell (1998) modified t-test for single-case comparison.

    Returns z-score and p-value (one-tailed).
    """
    n = len(hc_values)
    hc_mean = np.mean(hc_values)
    hc_std = np.std(hc_values, ddof=1)

    if hc_std == 0:
        return np.nan, np.nan

    # Modified t-statistic
    t_stat = (cvd_value - hc_mean) / (hc_std * np.sqrt((n + 1) / n))

    # Convert to z-score (approximation for reporting)
    z_score = t_stat

    # Two-tailed p-value (convert from t-distribution with df=n-1)
    from scipy.stats import t as t_dist
    p_value = 2 * (1 - t_dist.cdf(abs(t_stat), df=n-1))

    return z_score, p_value


def apply_fdr_correction(p_values, alpha=0.05):
    """
    Benjamini-Hochberg FDR correction.

    Returns boolean array of significant tests.
    """
    # Filter out NaNs
    valid_mask = ~np.isnan(p_values)
    if not valid_mask.any():
        return np.zeros_like(p_values, dtype=bool)

    # Benjamini-Hochberg procedure
    valid_p = p_values[valid_mask]
    n = len(valid_p)

    # Sort p-values and get sorted indices
    sorted_idx = np.argsort(valid_p)
    sorted_p = valid_p[sorted_idx]

    # Find largest i where p[i] <= (i+1)/n * alpha
    thresh = np.arange(1, n+1) / n * alpha
    reject_sorted = sorted_p <= thresh

    if reject_sorted.any():
        # Find largest i where condition holds
        max_i = np.where(reject_sorted)[0].max()
        # All tests up to and including max_i are rejected
        reject_sorted = np.arange(n) <= max_i
    else:
        reject_sorted = np.zeros(n, dtype=bool)

    # Unsort to original order
    reject_valid = np.zeros(n, dtype=bool)
    reject_valid[sorted_idx] = reject_sorted

    # Map back to full array
    reject = np.zeros_like(p_values, dtype=bool)
    reject[valid_mask] = reject_valid

    return reject


# ============================================================================
# MAIN ANALYSIS
# ============================================================================

def analyze_subject_roi(subject, roi, rdm_metric='correlation', norm_method='none',
                        pooled_stats=None):
    """
    Analyze one subject-ROI combination.

    Parameters
    ----------
    subject : str
        Subject ID (e.g., 'sub-08')
    roi : str
        ROI name ('V1', 'V2', 'V3', 'hV4')
    rdm_metric : str
        'correlation' or 'crossnobis'
    norm_method : str
        'none', 'within', or 'pooled'
    pooled_stats : dict or None
        {'mean': float, 'std': float} for pooled normalization

    Returns
    -------
    results : dict
        Per-pair z-scores, p-values, RDM values
    """
    try:
        roi_dir = ROI_DIRS[roi]

        # Load CVD amplitudes
        cvd_path = DATA_DIR / subject / roi_dir / 'amplitudes_procrustes.npy'
        if not cvd_path.exists():
            print(f"    DEBUG: Path does not exist: {cvd_path}")
            return None
    except Exception as e:
        print(f"    DEBUG: Exception in analyze_subject_roi init: {e}")
        import traceback
        traceback.print_exc()
        return None

    cvd_amps = np.load(cvd_path)  # (6, 8, n_voxels)

    # Compute CVD RDM
    if rdm_metric == 'correlation':
        cvd_rdm = compute_rdm_correlation(cvd_amps)
        shrinkage = None
    elif rdm_metric == 'crossnobis':
        cvd_rdm, shrinkage = compute_rdm_crossnobis_srm(cvd_amps)
    else:
        raise ValueError(f"Unknown metric: {rdm_metric}")

    # Load HC RDMs
    hc_rdms = []
    for hc_subj in HC_SUBJECTS:
        hc_path = DATA_DIR / hc_subj / roi_dir / 'amplitudes_procrustes.npy'
        if not hc_path.exists():
            continue

        hc_amps = np.load(hc_path)

        if rdm_metric == 'correlation':
            hc_rdm = compute_rdm_correlation(hc_amps)
        elif rdm_metric == 'crossnobis':
            hc_rdm, _ = compute_rdm_crossnobis_srm(hc_amps)

        hc_rdms.append(hc_rdm)

    hc_rdms = np.array(hc_rdms)  # (n_hc, 28)

    # Apply normalization
    if norm_method == 'none':
        cvd_rdm_norm = normalize_rdm_none(cvd_rdm)
        hc_rdms_norm = np.array([normalize_rdm_none(rdm) for rdm in hc_rdms])
    elif norm_method == 'within':
        cvd_rdm_norm = normalize_rdm_within(cvd_rdm)
        hc_rdms_norm = np.array([normalize_rdm_within(rdm) for rdm in hc_rdms])
    elif norm_method == 'pooled':
        if pooled_stats is None:
            raise ValueError("Pooled stats required for pooled normalization")
        cvd_rdm_norm = normalize_rdm_pooled(cvd_rdm, pooled_stats['mean'], pooled_stats['std'])
        hc_rdms_norm = np.array([normalize_rdm_pooled(rdm, pooled_stats['mean'], pooled_stats['std'])
                                  for rdm in hc_rdms])
    else:
        raise ValueError(f"Unknown norm method: {norm_method}")

    # Crawford & Howell test for each pair
    z_scores = []
    p_values = []

    for pair_idx in range(N_PAIRS):
        cvd_val = cvd_rdm_norm[pair_idx]
        hc_vals = hc_rdms_norm[:, pair_idx]

        z, p = crawford_howell_test(cvd_val, hc_vals)
        z_scores.append(z)
        p_values.append(p)

    return {
        'subject': subject,
        'roi': roi,
        'rdm_metric': rdm_metric,
        'norm_method': norm_method,
        'shrinkage': shrinkage,
        'rdm_raw': cvd_rdm.tolist(),
        'rdm_normalized': cvd_rdm_norm.tolist(),
        'z_scores': z_scores,
        'p_values': p_values,
        'hc_mean': hc_rdms.mean(axis=0).tolist(),
        'hc_std': hc_rdms.std(axis=0, ddof=1).tolist()
    }


def compute_pooled_stats(roi, rdm_metric='correlation'):
    """Compute pooled mean/std across all HC subjects for one ROI."""
    roi_dir = ROI_DIRS[roi]
    all_rdms = []

    for hc_subj in HC_SUBJECTS:
        hc_path = DATA_DIR / hc_subj / roi_dir / 'amplitudes_procrustes.npy'
        if not hc_path.exists():
            continue

        hc_amps = np.load(hc_path)

        if rdm_metric == 'correlation':
            rdm = compute_rdm_correlation(hc_amps)
        elif rdm_metric == 'crossnobis':
            rdm, _ = compute_rdm_crossnobis_srm(hc_amps)

        all_rdms.extend(rdm)

    all_rdms = np.array(all_rdms)

    return {
        'mean': all_rdms.mean(),
        'std': all_rdms.std(ddof=1)
    }


def run_full_analysis():
    """Run all combinations of metric × normalization."""

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = Path(__file__).parent / 'results/metric_norm_test'
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("RDM Metric and Normalization Sensitivity Test")
    print("=" * 80)
    print()

    # Load FDR results for comparison (baseline: correlation + no norm)
    with open(FDR_PATH) as f:
        fdr_baseline = json.load(f)

    baseline_fdr_pairs = {}
    for test in fdr_baseline.get('all_tests', []):
        key = (test['subject'], test['roi'], test['pair'])
        baseline_fdr_pairs[key] = test.get('fdr_within_roi', False)

    results = {
        'timestamp': timestamp,
        'n_hc': len(HC_SUBJECTS),
        'n_cvd': len(CVD_SUBJECTS),
        'rois': ROIS,
        'tests': []
    }

    # Test conditions
    conditions = [
        ('correlation', 'none'),      # Baseline (current method)
        ('correlation', 'within'),    # Correlation + within-subject z-norm
        ('correlation', 'pooled'),    # Correlation + pooled z-norm
        ('crossnobis', 'none'),       # Crossnobis + no norm
        ('crossnobis', 'within'),     # Crossnobis + within-subject z-norm
        ('crossnobis', 'pooled'),     # Crossnobis + pooled z-norm
    ]

    for metric, norm in conditions:
        print(f"\n{'='*80}")
        print(f"Condition: {metric.upper()} + {norm.upper()} normalization")
        print(f"{'='*80}")

        condition_results = []

        for roi in ROIS:
            print(f"\n{roi}:")

            # Compute pooled stats if needed
            if norm == 'pooled':
                pooled_stats = compute_pooled_stats(roi, rdm_metric=metric)
                print(f"  Pooled stats: mean={pooled_stats['mean']:.4f}, std={pooled_stats['std']:.4f}")
            else:
                pooled_stats = None

            for subject in CVD_SUBJECTS:
                result = analyze_subject_roi(subject, roi, rdm_metric=metric,
                                             norm_method=norm, pooled_stats=pooled_stats)

                if result is None:
                    print(f"  {subject}: ERROR - analyze_subject_roi returned None")
                    continue

                # Apply within-ROI FDR correction
                p_values = np.array(result['p_values'])
                fdr_sig = apply_fdr_correction(p_values, alpha=0.05)

                result['fdr_within_roi'] = fdr_sig.tolist()
                result['n_fdr_sig'] = int(fdr_sig.sum())

                # Store per-pair results
                result['pairs'] = []
                for pair_idx, pair_label in enumerate(PAIR_LABELS):
                    pair_result = {
                        'pair': pair_label,
                        'z_score': result['z_scores'][pair_idx],
                        'p_value': result['p_values'][pair_idx],
                        'fdr_sig': bool(fdr_sig[pair_idx]),
                        'rdm_value': result['rdm_raw'][pair_idx],
                        'rdm_normalized': result['rdm_normalized'][pair_idx]
                    }

                    # Check if this pair was significant in baseline
                    baseline_key = (subject, roi, pair_label)
                    baseline_fdr = baseline_fdr_pairs.get(baseline_key, False)
                    pair_result['baseline_fdr_sig'] = baseline_fdr

                    result['pairs'].append(pair_result)

                condition_results.append(result)

                print(f"  {subject}: {result['n_fdr_sig']} FDR-sig pairs (shrinkage={result.get('shrinkage', 'N/A')})")

        results['tests'].append({
            'metric': metric,
            'normalization': norm,
            'results': condition_results
        })

    # Save results
    output_file = output_dir / f'metric_norm_test_{timestamp}.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*80}")
    print(f"Results saved: {output_file}")
    print(f"{'='*80}")

    # Generate comparison report
    generate_comparison_report(results, output_dir, timestamp)

    return results


def generate_comparison_report(results, output_dir, timestamp):
    """Generate markdown report comparing all conditions."""

    report_lines = [
        "# RDM Metric and Normalization Sensitivity Report",
        "",
        f"**Date**: {timestamp}",
        f"**HC subjects**: {results['n_hc']}",
        f"**CVD subjects**: {results['n_cvd']}",
        "",
        "---",
        "",
        "## Summary: FDR-Significant Pairs by Condition",
        ""
    ]

    # Table header
    report_lines.append("| Condition | V1 | V2 | V3 | hV4 | Total | Change from Baseline |")
    report_lines.append("|-----------|----|----|----|----|-------|---------------------|")

    baseline_total = None

    for test in results['tests']:
        metric = test['metric']
        norm = test['normalization']
        condition_name = f"{metric.capitalize()} + {norm}"

        # Count FDR-sig pairs by ROI
        roi_counts = {roi: 0 for roi in results['rois']}

        for res in test['results']:
            roi_counts[res['roi']] += res['n_fdr_sig']

        total = sum(roi_counts.values())

        if metric == 'correlation' and norm == 'none':
            baseline_total = total
            change_str = "(baseline)"
        else:
            change = total - baseline_total if baseline_total is not None else 0
            sign = '+' if change > 0 else ''
            change_str = f"{sign}{change}"

        row = f"| {condition_name} | {roi_counts['V1']} | {roi_counts['V2']} | {roi_counts['V3']} | {roi_counts['hV4']} | {total} | {change_str} |"
        report_lines.append(row)

    report_lines.extend([
        "",
        "---",
        "",
        "## Convergence: Correlation Between Conditions",
        "",
        "Spearman correlation of z-scores between each condition and baseline (correlation + none):",
        ""
    ])

    # Compute convergence
    baseline_test = results['tests'][0]  # correlation + none
    baseline_zscores = {}

    for res in baseline_test['results']:
        key = (res['subject'], res['roi'])
        baseline_zscores[key] = np.array(res['z_scores'])

    report_lines.append("| Condition | V1 r | V2 r | V3 r | hV4 r | Mean r | Interpretation |")
    report_lines.append("|-----------|------|------|------|-------|--------|----------------|")

    for test in results['tests'][1:]:  # Skip baseline
        metric = test['metric']
        norm = test['normalization']
        condition_name = f"{metric.capitalize()} + {norm}"

        roi_corrs = {roi: [] for roi in results['rois']}

        for res in test['results']:
            key = (res['subject'], res['roi'])
            if key not in baseline_zscores:
                continue

            baseline_z = baseline_zscores[key]
            test_z = np.array(res['z_scores'])

            # Remove NaN pairs
            valid = ~(np.isnan(baseline_z) | np.isnan(test_z))
            if valid.sum() < 3:
                continue

            r, p = spearmanr(baseline_z[valid], test_z[valid])
            roi_corrs[res['roi']].append(r)

        # Mean correlation per ROI
        roi_mean_r = {roi: (np.mean(roi_corrs[roi]) if roi_corrs[roi] else np.nan)
                      for roi in results['rois']}

        overall_mean = np.nanmean(list(roi_mean_r.values()))

        if overall_mean > 0.9:
            interp = "✅ Very high (robust)"
        elif overall_mean > 0.7:
            interp = "✅ High (stable)"
        elif overall_mean > 0.5:
            interp = "⚠️ Moderate (some sensitivity)"
        elif overall_mean > 0.3:
            interp = "⚠️ Low (metric-dependent)"
        else:
            interp = "❌ Very low (unreliable)"

        row = f"| {condition_name} | {roi_mean_r['V1']:.3f} | {roi_mean_r['V2']:.3f} | {roi_mean_r['V3']:.3f} | {roi_mean_r['hV4']:.3f} | {overall_mean:.3f} | {interp} |"
        report_lines.append(row)

    report_lines.extend([
        "",
        "---",
        "",
        "## Pair Agreement: Baseline vs Alternative Conditions",
        "",
        "Agreement rate: percentage of pairs with same FDR significance status (within-ROI q<0.05).",
        ""
    ])

    baseline_fdr = {}
    for res in baseline_test['results']:
        for pair in res['pairs']:
            key = (res['subject'], res['roi'], pair['pair'])
            baseline_fdr[key] = pair['fdr_sig']

    report_lines.append("| Condition | Agreement | Disagreement | Rate | Interpretation |")
    report_lines.append("|-----------|-----------|--------------|------|----------------|")

    for test in results['tests'][1:]:
        metric = test['metric']
        norm = test['normalization']
        condition_name = f"{metric.capitalize()} + {norm}"

        agree = 0
        disagree = 0

        for res in test['results']:
            for pair in res['pairs']:
                key = (res['subject'], res['roi'], pair['pair'])
                if key not in baseline_fdr:
                    continue

                if baseline_fdr[key] == pair['fdr_sig']:
                    agree += 1
                else:
                    disagree += 1

        total = agree + disagree
        rate = agree / total if total > 0 else 0

        if rate > 0.95:
            interp = "✅ Excellent agreement"
        elif rate > 0.9:
            interp = "✅ High agreement"
        elif rate > 0.8:
            interp = "⚠️ Moderate agreement"
        else:
            interp = "❌ Low agreement (results change)"

        row = f"| {condition_name} | {agree} | {disagree} | {rate:.1%} | {interp} |"
        report_lines.append(row)

    report_lines.extend([
        "",
        "---",
        "",
        "## Key Findings",
        "",
        "### Q1: Does crossnobis method affect results?",
        "",
        "**To be determined from results above:**",
        "- If correlation r > 0.9 and agreement > 95%: Metric choice does NOT matter (robust)",
        "- If correlation r = 0.7-0.9 and agreement 80-95%: Moderate sensitivity (report both)",
        "- If correlation r < 0.7 or agreement < 80%: High sensitivity (metric choice matters)",
        "",
        "### Q2: Does z-normalization affect results?",
        "",
        "**To be determined from results above:**",
        "- If within/pooled norm has similar total FDR pairs ±10%: Normalization does NOT matter",
        "- If within/pooled norm differs >20%: Normalization affects results (variance matters)",
        "",
        "---",
        "",
        "## Recommendations",
        "",
        "**Based on convergence analysis:**",
        "",
        "1. **If crossnobis r > 0.9**: Use correlation distance (simpler, current method validated)",
        "2. **If crossnobis r < 0.7**: Report both metrics or prefer crossnobis (more principled for fMRI)",
        "3. **If z-norm changes FDR survivors >20%**: Use within-subject z-norm (accounts for baseline variance)",
        "4. **If z-norm robust (agreement >95%)**: Keep current method (no norm, simpler to interpret)",
        "",
        f"**Full results**: `metric_norm_test_{timestamp}.json`",
        ""
    ])

    # Save report
    report_file = output_dir / f'METRIC_NORM_REPORT_{timestamp}.md'
    with open(report_file, 'w') as f:
        f.write('\n'.join(report_lines))

    print(f"Report saved: {report_file}")

    return report_file


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Test RDM metric and normalization sensitivity')
    parser.add_argument('--output_dir', type=str, default=None,
                        help='Output directory (default: results/metric_norm_test)')

    args = parser.parse_args()

    results = run_full_analysis()

    print("\n" + "="*80)
    print("Analysis complete!")
    print("="*80)
