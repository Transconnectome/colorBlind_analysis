#!/usr/bin/env python3
"""
Compute Geometric Metrics for SRM Results

Applies the same geometric analysis pipeline to SRM-aligned patterns
for direct comparison with Procrustes-PCA approach.

Usage:
    python compute_srm_metrics.py --roi V1 --srm-dir /path/to/srm/results
"""

import argparse
import json
import numpy as np
from pathlib import Path
from scipy.stats import spearmanr
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))
from utils.geometric_analysis import (
    compute_all_geometric_metrics,
    compute_leave_one_out_isc,
    compute_group_statistics
)


def load_srm_patterns(srm_dir, roi, subject_id):
    """
    Load SRM-aligned patterns for a subject.

    Expected SRM output structure:
    srm_dir/{ROI}/sub-{ID}_aligned_patterns.npy  (n_runs, n_colors, k_srm)
    or
    srm_dir/{ROI}/sub-{ID}_srm_transformed.npy

    Args:
        srm_dir: Path to SRM results directory
        roi: ROI name
        subject_id: Subject ID (e.g., 'sub-01')

    Returns:
        odd_pattern: (8, k) averaged odd runs
        even_pattern: (8, k) averaged even runs
    """
    # Try different possible filenames
    possible_paths = [
        srm_dir / roi / f"{subject_id}_aligned_patterns.npy",
        srm_dir / roi / f"{subject_id}_srm_transformed.npy",
        srm_dir / roi / f"{subject_id}_transformed.npy",
    ]

    for path in possible_paths:
        if path.exists():
            print(f"  Loading: {path}")
            patterns = np.load(path)

            # Assume shape: (n_runs, n_colors, k_srm)
            if patterns.ndim == 3:
                n_runs, n_colors, k = patterns.shape

                # Split into odd/even
                odd_runs = patterns[[0, 2, 4], :, :]  # runs 1,3,5
                even_runs = patterns[[1, 3, 5], :, :]  # runs 2,4,6

                odd_pattern = odd_runs.mean(axis=0)  # (8, k)
                even_pattern = even_runs.mean(axis=0)

                print(f"  Loaded patterns: shape={patterns.shape}, k_srm={k}")
                return odd_pattern, even_pattern
            else:
                print(f"  WARNING: Unexpected shape {patterns.shape}, expected 3D")
                return None, None

    print(f"  ERROR: No SRM patterns found for {subject_id} {roi}")
    return None, None


def compute_rdm_from_patterns(odd_pattern, even_pattern):
    """
    Compute correlation-based RDM from patterns.

    Args:
        odd_pattern: (8, k) averaged odd runs
        even_pattern: (8, k) averaged even runs

    Returns:
        rdm_combined: (8, 8) RDM from averaged odd+even
        rdm_odd: (8, 8) RDM from odd only
        rdm_even: (8, 8) RDM from even only
        reliability: Split-half correlation
    """
    # Combined RDM (average odd and even first)
    pattern_combined = (odd_pattern + even_pattern) / 2  # (8, k)
    rdm_combined = 1 - np.corrcoef(pattern_combined)

    # Separate RDMs for reliability
    rdm_odd = 1 - np.corrcoef(odd_pattern)
    rdm_even = 1 - np.corrcoef(even_pattern)

    # Split-half reliability
    mask = np.triu_indices(8, k=1)
    reliability, _ = spearmanr(rdm_odd[mask], rdm_even[mask])

    return rdm_combined, rdm_odd, rdm_even, reliability


def main():
    parser = argparse.ArgumentParser(description='Compute Geometric Metrics for SRM Results')
    parser.add_argument('--roi', type=str, required=True, help='ROI name (V1, V2, V3, hV4)')
    parser.add_argument('--srm-dir', type=str, required=True,
                        help='Path to SRM results directory')
    parser.add_argument('--output-dir', type=str,
                        default='/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/validation/scripts/postSRM_procrus/results/srm_metrics',
                        help='Output directory')

    args = parser.parse_args()

    # Paths
    srm_dir = Path(args.srm_dir)
    output_dir = Path(args.output_dir)
    roi = args.roi

    print(f"\n=== Compute Geometric Metrics for SRM ===")
    print(f"ROI: {roi}")
    print(f"SRM directory: {srm_dir}")

    # Subject groups
    hc_subjects = ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05', 'sub-06']
    cvd_subjects = ['sub-08', 'sub-09', 'sub-10']
    all_subjects = hc_subjects + cvd_subjects

    print(f"\nHC subjects: {hc_subjects}")
    print(f"CVD subjects: {cvd_subjects}")

    # Load SRM patterns and compute RDMs
    print(f"\n=== Loading SRM Patterns ===")
    rdms = {}
    reliabilities = {}
    subject_groups = {}

    for subj_id in all_subjects:
        odd_pattern, even_pattern = load_srm_patterns(srm_dir, roi, subj_id)

        if odd_pattern is None:
            print(f"  WARNING: Skipping {subj_id} (patterns not found)")
            continue

        # Compute RDM
        rdm_combined, rdm_odd, rdm_even, reliability = compute_rdm_from_patterns(
            odd_pattern, even_pattern
        )

        rdms[subj_id] = rdm_combined
        reliabilities[subj_id] = reliability
        subject_groups[subj_id] = 'HC' if subj_id in hc_subjects else 'CVD'

        print(f"  {subj_id}: RDM shape={rdm_combined.shape}, reliability={reliability:.4f}")

    if len(rdms) == 0:
        print("\nERROR: No SRM patterns found")
        sys.exit(1)

    # Compute HC mean RDM
    print(f"\n=== Computing HC Mean RDM ===")
    hc_subject_ids = [sid for sid in hc_subjects if sid in rdms]
    hc_rdms = [rdms[sid] for sid in hc_subject_ids]

    if len(hc_rdms) == 0:
        print("ERROR: No HC RDMs found")
        sys.exit(1)

    rdm_hc_mean = np.mean(hc_rdms, axis=0)
    print(f"  HC mean RDM shape: {rdm_hc_mean.shape}")
    print(f"  n_hc_subjects: {len(hc_rdms)}")

    # Compute leave-one-out ISC for HC
    print(f"\n=== Computing Leave-One-Out ISC (HC) ===")
    isc_hc_loo = compute_leave_one_out_isc(hc_rdms, hc_subject_ids)

    for subj_id, isc_val in isc_hc_loo.items():
        print(f"  {subj_id}: ISC = {isc_val:.4f}")

    # Compute metrics for all subjects
    print(f"\n=== Computing Geometric Metrics ===")
    all_metrics = {}

    for subj_id in rdms.keys():
        rdm_subject = rdms[subj_id]
        group = subject_groups[subj_id]

        # For HC, use leave-one-out mean; for CVD, use full HC mean
        if group == 'HC':
            rdms_others = [rdms[sid] for sid in hc_subject_ids if sid != subj_id]
            rdm_reference = np.mean(rdms_others, axis=0)
        else:
            rdm_reference = rdm_hc_mean

        metrics = compute_all_geometric_metrics(
            rdm_subject,
            rdm_reference,
            subj_id,
            group
        )

        # Add reliability
        metrics['split_half_reliability'] = float(reliabilities[subj_id])

        all_metrics[subj_id] = metrics

        print(f"  {subj_id} ({group}): ISC={metrics['isc']:.4f}, "
              f"deviation={metrics['deviation_from_hc']:.4f}, "
              f"circularity={metrics['circularity']:.4f}, "
              f"reliability={metrics['split_half_reliability']:.4f}")

    # Statistical comparison: HC vs CVD
    print(f"\n=== Statistical Comparison: HC vs CVD ===")

    cvd_subject_ids = [sid for sid in cvd_subjects if sid in rdms]

    hc_isc = [all_metrics[sid]['isc'] for sid in hc_subject_ids]
    cvd_isc = [all_metrics[sid]['isc'] for sid in cvd_subject_ids]

    hc_deviation = [all_metrics[sid]['deviation_from_hc'] for sid in hc_subject_ids]
    cvd_deviation = [all_metrics[sid]['deviation_from_hc'] for sid in cvd_subject_ids]

    hc_circularity = [all_metrics[sid]['circularity'] for sid in hc_subject_ids
                      if not np.isnan(all_metrics[sid]['circularity'])]
    cvd_circularity = [all_metrics[sid]['circularity'] for sid in cvd_subject_ids
                       if not np.isnan(all_metrics[sid]['circularity'])]

    hc_stress = [all_metrics[sid]['mds_stress'] for sid in hc_subject_ids]
    cvd_stress = [all_metrics[sid]['mds_stress'] for sid in cvd_subject_ids]

    hc_reliability = [all_metrics[sid]['split_half_reliability'] for sid in hc_subject_ids]
    cvd_reliability = [all_metrics[sid]['split_half_reliability'] for sid in cvd_subject_ids]

    # Compute statistics
    stats = {}

    if len(hc_isc) > 0 and len(cvd_isc) > 0:
        stats['isc'] = compute_group_statistics(hc_isc, cvd_isc, 'isc')
        print(f"\nISC:")
        print(f"  HC: {stats['isc']['hc_mean']:.4f} ± {stats['isc']['hc_std']:.4f}")
        print(f"  CVD: {stats['isc']['cvd_mean']:.4f} ± {stats['isc']['cvd_std']:.4f}")
        print(f"  t={stats['isc']['t_statistic']:.3f}, p={stats['isc']['p_value']:.4f}, "
              f"d={stats['isc']['cohens_d']:.3f}")
        print(f"  Significant: {stats['isc']['significant']}")

    if len(hc_deviation) > 0 and len(cvd_deviation) > 0:
        stats['deviation'] = compute_group_statistics(hc_deviation, cvd_deviation, 'deviation_from_hc')
        print(f"\nDeviation from HC:")
        print(f"  HC: {stats['deviation']['hc_mean']:.4f} ± {stats['deviation']['hc_std']:.4f}")
        print(f"  CVD: {stats['deviation']['cvd_mean']:.4f} ± {stats['deviation']['cvd_std']:.4f}")
        print(f"  t={stats['deviation']['t_statistic']:.3f}, p={stats['deviation']['p_value']:.4f}, "
              f"d={stats['deviation']['cohens_d']:.3f}")
        print(f"  Significant: {stats['deviation']['significant']}")

    if len(hc_circularity) > 0 and len(cvd_circularity) > 0:
        stats['circularity'] = compute_group_statistics(hc_circularity, cvd_circularity, 'circularity')
        print(f"\nCircularity:")
        print(f"  HC: {stats['circularity']['hc_mean']:.4f} ± {stats['circularity']['hc_std']:.4f}")
        print(f"  CVD: {stats['circularity']['cvd_mean']:.4f} ± {stats['circularity']['cvd_std']:.4f}")
        print(f"  t={stats['circularity']['t_statistic']:.3f}, p={stats['circularity']['p_value']:.4f}, "
              f"d={stats['circularity']['cohens_d']:.3f}")
        print(f"  Significant: {stats['circularity']['significant']}")

    if len(hc_reliability) > 0 and len(cvd_reliability) > 0:
        stats['reliability'] = compute_group_statistics(hc_reliability, cvd_reliability, 'split_half_reliability')
        print(f"\nSplit-half Reliability:")
        print(f"  HC: {stats['reliability']['hc_mean']:.4f} ± {stats['reliability']['hc_std']:.4f}")
        print(f"  CVD: {stats['reliability']['cvd_mean']:.4f} ± {stats['reliability']['cvd_std']:.4f}")
        print(f"  t={stats['reliability']['t_statistic']:.3f}, p={stats['reliability']['p_value']:.4f}, "
              f"d={stats['reliability']['cohens_d']:.3f}")
        print(f"  Significant: {stats['reliability']['significant']}")

    # Save outputs
    output_roi_dir = output_dir / roi
    output_roi_dir.mkdir(parents=True, exist_ok=True)

    # Save all metrics
    metrics_path = output_roi_dir / "geometric_metrics_srm.json"
    with open(metrics_path, 'w') as f:
        json.dump(all_metrics, f, indent=2)

    # Save statistics
    stats_path = output_roi_dir / "hc_vs_cvd_statistics_srm.json"
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2)

    # Save RDMs
    for subj_id, rdm in rdms.items():
        rdm_path = output_roi_dir / f"{subj_id}_rdm_srm.npy"
        np.save(rdm_path, rdm)

    # Save HC mean RDM
    rdm_hc_mean_path = output_roi_dir / "rdm_hc_mean_srm.npy"
    np.save(rdm_hc_mean_path, rdm_hc_mean)

    print(f"\n=== Outputs Saved ===")
    print(f"  Metrics: {metrics_path}")
    print(f"  Statistics: {stats_path}")
    print(f"  RDMs: {output_roi_dir}/sub-*_rdm_srm.npy")
    print(f"  HC mean RDM: {rdm_hc_mean_path}")

    print(f"\n✓ SRM geometric metrics complete for {roi}")


if __name__ == '__main__':
    main()
