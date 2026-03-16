#!/usr/bin/env python3
"""
Test RDM Metric and Normalization Sensitivity (SERVER VERSION)

Tests two critical methodological choices:
1. RDM distance metric: Correlation vs Crossnobis (in SRM space)
2. Z-normalization: Raw vs Within-subject vs Pooled normalization

Addresses user questions:
- Q1: Does crossnobis method in SRM space give same results as correlation?
- Q2: Does z-normalization of RDM values change FDR results?

Usage:
  python test_rdm_metric_and_normalization_server.py [--output_dir PATH]
"""

import numpy as np
import json
import sys
import socket
from pathlib import Path
from datetime import datetime
from scipy.spatial.distance import pdist, squareform
from scipy.stats import spearmanr
import warnings
warnings.filterwarnings('ignore')

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

# Data paths (server vs local)
SCRIPT_DIR = Path(__file__).resolve().parent

if socket.gethostname().startswith('node'):
    DATA_DIR = Path("/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010")
    # Output to same folder as script (logs/ and results/ subdirs)
    OUTPUT_BASE = SCRIPT_DIR / 'results'
    LOG_BASE = SCRIPT_DIR / 'logs'
else:
    DATA_DIR = SCRIPT_DIR.parent.parent / 'phase1_preprocess_decoding/results/full_dataset_C010'
    OUTPUT_BASE = SCRIPT_DIR / 'results'
    LOG_BASE = SCRIPT_DIR / 'logs'

print(f"Running on: {socket.gethostname()}")
print(f"Data dir: {DATA_DIR}")
print(f"Output base: {OUTPUT_BASE}")
print(f"Log base: {LOG_BASE}")

# ============================================================================
# CROSSNOBIS IMPLEMENTATION (inline to avoid import issues)
# ============================================================================

def compute_rdm_crossnobis(amplitudes, use_shrinkage=True):
    """
    Compute RDM using cross-validated Mahalanobis distance (crossnobis).

    Inline implementation to avoid import issues on server.
    """
    from sklearn.covariance import LedoitWolf

    n_runs, n_colors, n_voxels = amplitudes.shape

    if n_runs < 2:
        raise ValueError(f"Need at least 2 runs for cross-validation, got {n_runs}")

    rdm_sum = np.zeros((n_colors, n_colors))
    shrinkages = []

    for test_run in range(n_runs):
        # Leave-one-run-out split
        train_runs = [r for r in range(n_runs) if r != test_run]
        train_data = amplitudes[train_runs]

        # Reshape for covariance
        X_train = train_data.reshape(-1, n_voxels)

        # Estimate covariance with Ledoit-Wolf shrinkage
        if use_shrinkage:
            lw = LedoitWolf()
            lw.fit(X_train)
            cov = lw.covariance_
            shrinkages.append(lw.shrinkage_)
        else:
            cov = np.cov(X_train.T)

        # Compute precision matrix
        try:
            cov_inv = np.linalg.inv(cov)
        except np.linalg.LinAlgError:
            cov_inv = np.linalg.pinv(cov)

        # Test run patterns
        test_patterns = amplitudes[test_run]

        # Compute pairwise Mahalanobis distances
        rdm_test = np.zeros((n_colors, n_colors))
        for i in range(n_colors):
            for j in range(n_colors):
                diff = test_patterns[i] - test_patterns[j]
                try:
                    dist_sq = diff @ cov_inv @ diff.T
                    if dist_sq < 0:
                        dist_sq = 0
                    dist = np.sqrt(dist_sq)
                except:
                    dist = np.linalg.norm(diff)

                rdm_test[i, j] = dist

        rdm_sum += rdm_test

    # Average across leave-one-run-out splits
    rdm_avg = rdm_sum / n_runs
    mean_shrinkage = np.mean(shrinkages) if shrinkages else 0.0

    return rdm_avg, mean_shrinkage


# ============================================================================
# RDM COMPUTATION
# ============================================================================

def compute_rdm_correlation(amplitudes):
    """Compute RDM using correlation distance (current method)."""
    patterns = amplitudes.mean(axis=0)  # (8, n_voxels)
    rdm_full = squareform(pdist(patterns, metric='correlation'))

    # Extract upper triangle
    triu_idx = np.triu_indices(N_COLORS, k=1)
    rdm = rdm_full[triu_idx]

    return rdm


def compute_rdm_crossnobis_srm(amplitudes):
    """Compute RDM using crossnobis method in SRM space."""
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
    """Crawford & Howell (1998) modified t-test for single-case comparison."""
    from scipy.stats import t as t_dist

    n = len(hc_values)
    hc_mean = np.mean(hc_values)
    hc_std = np.std(hc_values, ddof=1)

    if hc_std == 0:
        return np.nan, np.nan

    # Modified t-statistic
    t_stat = (cvd_value - hc_mean) / (hc_std * np.sqrt((n + 1) / n))

    # Convert to z-score
    z_score = t_stat

    # Two-tailed p-value
    p_value = 2 * (1 - t_dist.cdf(abs(t_stat), df=n-1))

    return z_score, p_value


def apply_fdr_correction(p_values, alpha=0.05):
    """Benjamini-Hochberg FDR correction."""
    # Filter out NaNs
    valid_mask = ~np.isnan(p_values)
    if not valid_mask.any():
        return np.zeros_like(p_values, dtype=bool)

    # Benjamini-Hochberg procedure
    valid_p = p_values[valid_mask]
    n = len(valid_p)

    # Sort p-values
    sorted_idx = np.argsort(valid_p)
    sorted_p = valid_p[sorted_idx]

    # Find largest i where p[i] <= (i+1)/n * alpha
    thresh = np.arange(1, n+1) / n * alpha
    reject_sorted = sorted_p <= thresh

    if reject_sorted.any():
        max_i = np.where(reject_sorted)[0].max()
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
    """Analyze one subject-ROI combination."""
    roi_dir = ROI_DIRS[roi]

    # Load CVD amplitudes
    cvd_path = DATA_DIR / subject / roi_dir / 'amplitudes_procrustes.npy'
    if not cvd_path.exists():
        return None

    cvd_amps = np.load(cvd_path)

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

    hc_rdms = np.array(hc_rdms)

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


def run_full_analysis(output_dir=None, test_mode=False, test_subjects=None,
                      test_rois=None, test_conditions=None):
    """Run all combinations of metric × normalization.

    Parameters
    ----------
    output_dir : str or Path, optional
        Output directory (default: SCRIPT_DIR/results)
    test_mode : bool
        If True, run minimal test (faster for validation)
    test_subjects : list of str, optional
        CVD subjects to test (default: all CVD subjects)
    test_rois : list of str, optional
        ROIs to test (default: all ROIs)
    test_conditions : list of str, optional
        Conditions to test, formatted as "metric_norm" (e.g., "correlation_none")
        (default: all 6 conditions)
    """

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    if output_dir is None:
        output_dir = OUTPUT_BASE
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    # Test mode configuration
    if test_mode:
        cvd_subjects = test_subjects if test_subjects else ['sub-08']
        rois = test_rois if test_rois else ['V1', 'V2']
        if test_conditions:
            # Parse "metric_norm" format
            conditions = [tuple(c.split('_')) for c in test_conditions]
        else:
            conditions = [('correlation', 'none'), ('crossnobis', 'none')]

        print("=" * 80)
        print("RDM Metric and Normalization Sensitivity Test - TEST MODE")
        print("=" * 80)
        print(f"Test subjects: {cvd_subjects}")
        print(f"Test ROIs: {rois}")
        print(f"Test conditions: {conditions}")
        print()
    else:
        cvd_subjects = CVD_SUBJECTS
        rois = ROIS
        conditions = [
            ('correlation', 'none'),      # Baseline (current method)
            ('correlation', 'within'),    # Correlation + within-subject z-norm
            ('correlation', 'pooled'),    # Correlation + pooled z-norm
            ('crossnobis', 'none'),       # Crossnobis + no norm
            ('crossnobis', 'within'),     # Crossnobis + within-subject z-norm
            ('crossnobis', 'pooled'),     # Crossnobis + pooled z-norm
        ]

        print("=" * 80)
        print("RDM Metric and Normalization Sensitivity Test - FULL MODE")
        print("=" * 80)
        print()

    results = {
        'timestamp': timestamp,
        'hostname': socket.gethostname(),
        'test_mode': test_mode,
        'n_hc': len(HC_SUBJECTS),
        'n_cvd': len(cvd_subjects),
        'cvd_subjects': cvd_subjects,
        'rois': rois,
        'conditions': [f"{m}_{n}" for m, n in conditions],
        'tests': []
    }

    for metric, norm in conditions:
        print(f"\n{'='*80}")
        print(f"Condition: {metric.upper()} + {norm.upper()} normalization")
        print(f"{'='*80}")

        condition_results = []

        for roi in rois:  # Use test-mode variable, not global ROIS
            print(f"\n{roi}:")

            # Compute pooled stats if needed
            if norm == 'pooled':
                pooled_stats = compute_pooled_stats(roi, rdm_metric=metric)
                print(f"  Pooled stats: mean={pooled_stats['mean']:.4f}, std={pooled_stats['std']:.4f}")
            else:
                pooled_stats = None

            for subject in cvd_subjects:
                result = analyze_subject_roi(subject, roi, rdm_metric=metric,
                                             norm_method=norm, pooled_stats=pooled_stats)

                if result is None:
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
                    result['pairs'].append(pair_result)

                condition_results.append(result)

                shrinkage_str = f"{result.get('shrinkage', 0):.3f}" if result.get('shrinkage') is not None else "N/A"
                print(f"  {subject}: {result['n_fdr_sig']} FDR-sig pairs (shrinkage={shrinkage_str})")

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

    return results, output_file


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Test RDM metric and normalization sensitivity',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full analysis (all subjects, ROIs, conditions)
  python test_rdm_metric_and_normalization_server.py

  # Test mode (quick validation)
  python test_rdm_metric_and_normalization_server.py --test_mode

  # Custom test (specific subjects and ROIs)
  python test_rdm_metric_and_normalization_server.py --test_mode \\
      --test_subjects sub-08 sub-09 --test_rois V1 V2 \\
      --test_conditions correlation_none crossnobis_none
        """
    )

    parser.add_argument('--output_dir', type=str, default=None,
                        help='Output directory (default: SCRIPT_DIR/results)')
    parser.add_argument('--test_mode', action='store_true',
                        help='Run minimal test for validation (faster)')
    parser.add_argument('--test_subjects', type=str, nargs='+', default=None,
                        help='CVD subjects for test mode (default: sub-08)')
    parser.add_argument('--test_rois', type=str, nargs='+', default=None,
                        help='ROIs for test mode (default: V1 V2)')
    parser.add_argument('--test_conditions', type=str, nargs='+', default=None,
                        help='Conditions for test mode, format: metric_norm (e.g., correlation_none)')

    args = parser.parse_args()

    # Create log directory
    LOG_BASE.mkdir(parents=True, exist_ok=True)

    results, output_file = run_full_analysis(
        output_dir=args.output_dir,
        test_mode=args.test_mode,
        test_subjects=args.test_subjects,
        test_rois=args.test_rois,
        test_conditions=args.test_conditions
    )

    print("\n" + "="*80)
    print("Analysis complete!")
    print(f"Results: {output_file}")
    print("="*80)

    if socket.gethostname().startswith('node'):
        print("\nDownload results with:")
        print(f"scp haba6030@node3:{output_file} .")
    else:
        print(f"\nResults saved locally: {output_file}")
