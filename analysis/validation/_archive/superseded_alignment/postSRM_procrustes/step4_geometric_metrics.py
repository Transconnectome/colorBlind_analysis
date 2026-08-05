#!/usr/bin/env python3
"""
Step 4: Geometric Metrics

Computes geometric metrics for quantifying:
- HC representational consistency (ISC)
- CVD deviations from HC norm
- Color space structure (circularity, MDS stress)

Usage:
    python step4_geometric_metrics.py --roi V1 --method pca
"""

import argparse
import json
import numpy as np
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))
from utils.geometric_analysis import (
    compute_all_geometric_metrics,
    compute_leave_one_out_isc,
    compute_group_statistics
)


def main():
    parser = argparse.ArgumentParser(description='Step 4: Compute Geometric Metrics')
    parser.add_argument('--roi', type=str, required=True, help='ROI name (V1, V2, V3, hV4)')
    parser.add_argument('--method', type=str, default='pca', choices=['pca', 'anova'],
                        help='Dimension reduction method (default: pca)')
    parser.add_argument('--input-dir', type=str,
                        default='/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/validation/scripts/postSRM_procrus/results/step3_rdms',
                        help='Input directory from Step 3')
    parser.add_argument('--output-dir', type=str,
                        default='/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/validation/scripts/postSRM_procrus/results/step4_metrics',
                        help='Output directory')

    args = parser.parse_args()

    # Paths
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    roi = args.roi

    print(f"\n=== Step 4: Geometric Metrics ===")
    print(f"ROI: {roi}")
    print(f"Method: {args.method}")

    # Subject groups
    hc_subjects = ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05', 'sub-06']
    cvd_subjects = ['sub-08', 'sub-09', 'sub-10']
    all_subjects = hc_subjects + cvd_subjects

    print(f"\nHC subjects: {hc_subjects}")
    print(f"CVD subjects: {cvd_subjects}")

    # Load all RDMs
    print(f"\n=== Loading RDMs from {input_dir / roi} ===")
    rdms = {}
    subject_groups = {}

    for subj_id in all_subjects:
        rdm_path = input_dir / roi / f"{subj_id}_rdm_crossnobis.npy"

        if not rdm_path.exists():
            print(f"  WARNING: Missing {subj_id}, skipping")
            continue

        rdm = np.load(rdm_path)
        rdms[subj_id] = rdm
        subject_groups[subj_id] = 'HC' if subj_id in hc_subjects else 'CVD'

        print(f"  {subj_id}: shape={rdm.shape}, group={subject_groups[subj_id]}")

    if len(rdms) == 0:
        print("ERROR: No RDMs found")
        sys.exit(1)

    # Compute HC mean RDM (for deviation metric)
    print(f"\n=== Computing HC Mean RDM ===")
    hc_rdms = [rdms[subj_id] for subj_id in hc_subjects if subj_id in rdms]

    if len(hc_rdms) == 0:
        print("ERROR: No HC RDMs found")
        sys.exit(1)

    rdm_hc_mean = np.mean(hc_rdms, axis=0)
    print(f"  HC mean RDM shape: {rdm_hc_mean.shape}")
    print(f"  n_hc_subjects: {len(hc_rdms)}")

    # Compute leave-one-out ISC for HC
    print(f"\n=== Computing Leave-One-Out ISC (HC) ===")
    hc_subject_ids = [sid for sid in hc_subjects if sid in rdms]
    hc_rdm_list = [rdms[sid] for sid in hc_subject_ids]

    isc_hc_loo = compute_leave_one_out_isc(hc_rdm_list, hc_subject_ids)

    for subj_id, isc_val in isc_hc_loo.items():
        print(f"  {subj_id}: ISC = {isc_val:.4f}")

    # Compute metrics for all subjects
    print(f"\n=== Computing Geometric Metrics for All Subjects ===")
    all_metrics = {}

    for subj_id in rdms.keys():
        rdm_subject = rdms[subj_id]
        group = subject_groups[subj_id]

        # For HC, use leave-one-out mean; for CVD, use full HC mean
        if group == 'HC':
            # Leave-one-out mean
            rdms_others = [rdms[sid] for sid in hc_subject_ids if sid != subj_id]
            rdm_reference = np.mean(rdms_others, axis=0)
        else:
            # Full HC mean
            rdm_reference = rdm_hc_mean

        metrics = compute_all_geometric_metrics(
            rdm_subject,
            rdm_reference,
            subj_id,
            group
        )

        all_metrics[subj_id] = metrics

        print(f"  {subj_id} ({group}): ISC={metrics['isc']:.4f}, "
              f"deviation={metrics['deviation_from_hc']:.4f}, "
              f"circularity={metrics['circularity']:.4f}, "
              f"stress={metrics['mds_stress']:.4f}")

    # Statistical comparison: HC vs CVD
    print(f"\n=== Statistical Comparison: HC vs CVD ===")

    # Extract values by group
    hc_isc = [all_metrics[sid]['isc'] for sid in hc_subject_ids]
    cvd_isc = [all_metrics[sid]['isc'] for sid in cvd_subjects if sid in all_metrics]

    hc_deviation = [all_metrics[sid]['deviation_from_hc'] for sid in hc_subject_ids]
    cvd_deviation = [all_metrics[sid]['deviation_from_hc'] for sid in cvd_subjects if sid in all_metrics]

    hc_circularity = [all_metrics[sid]['circularity'] for sid in hc_subject_ids if not np.isnan(all_metrics[sid]['circularity'])]
    cvd_circularity = [all_metrics[sid]['circularity'] for sid in cvd_subjects if sid in all_metrics and not np.isnan(all_metrics[sid]['circularity'])]

    hc_stress = [all_metrics[sid]['mds_stress'] for sid in hc_subject_ids]
    cvd_stress = [all_metrics[sid]['mds_stress'] for sid in cvd_subjects if sid in all_metrics]

    # Compute statistics
    stats = {}

    if len(hc_isc) > 0 and len(cvd_isc) > 0:
        stats['isc'] = compute_group_statistics(hc_isc, cvd_isc, 'isc')
        print(f"\nISC:")
        print(f"  HC: {stats['isc']['hc_mean']:.4f} ± {stats['isc']['hc_std']:.4f}")
        print(f"  CVD: {stats['isc']['cvd_mean']:.4f} ± {stats['isc']['cvd_std']:.4f}")
        print(f"  t={stats['isc']['t_statistic']:.3f}, p={stats['isc']['p_value']:.4f}, d={stats['isc']['cohens_d']:.3f}")
        print(f"  Significant: {stats['isc']['significant']}")

    if len(hc_deviation) > 0 and len(cvd_deviation) > 0:
        stats['deviation'] = compute_group_statistics(hc_deviation, cvd_deviation, 'deviation_from_hc')
        print(f"\nDeviation from HC:")
        print(f"  HC: {stats['deviation']['hc_mean']:.4f} ± {stats['deviation']['hc_std']:.4f}")
        print(f"  CVD: {stats['deviation']['cvd_mean']:.4f} ± {stats['deviation']['cvd_std']:.4f}")
        print(f"  t={stats['deviation']['t_statistic']:.3f}, p={stats['deviation']['p_value']:.4f}, d={stats['deviation']['cohens_d']:.3f}")
        print(f"  Significant: {stats['deviation']['significant']}")

    if len(hc_circularity) > 0 and len(cvd_circularity) > 0:
        stats['circularity'] = compute_group_statistics(hc_circularity, cvd_circularity, 'circularity')
        print(f"\nCircularity:")
        print(f"  HC: {stats['circularity']['hc_mean']:.4f} ± {stats['circularity']['hc_std']:.4f}")
        print(f"  CVD: {stats['circularity']['cvd_mean']:.4f} ± {stats['circularity']['cvd_std']:.4f}")
        print(f"  t={stats['circularity']['t_statistic']:.3f}, p={stats['circularity']['p_value']:.4f}, d={stats['circularity']['cohens_d']:.3f}")
        print(f"  Significant: {stats['circularity']['significant']}")

    if len(hc_stress) > 0 and len(cvd_stress) > 0:
        stats['mds_stress'] = compute_group_statistics(hc_stress, cvd_stress, 'mds_stress')
        print(f"\nMDS Stress:")
        print(f"  HC: {stats['mds_stress']['hc_mean']:.4f} ± {stats['mds_stress']['hc_std']:.4f}")
        print(f"  CVD: {stats['mds_stress']['cvd_mean']:.4f} ± {stats['mds_stress']['cvd_std']:.4f}")
        print(f"  t={stats['mds_stress']['t_statistic']:.3f}, p={stats['mds_stress']['p_value']:.4f}, d={stats['mds_stress']['cohens_d']:.3f}")
        print(f"  Significant: {stats['mds_stress']['significant']}")

    # Save outputs
    output_roi_dir = output_dir / roi
    output_roi_dir.mkdir(parents=True, exist_ok=True)

    # Save all metrics
    metrics_path = output_roi_dir / "geometric_metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump(all_metrics, f, indent=2)

    # Save statistics
    stats_path = output_roi_dir / "hc_vs_cvd_statistics.json"
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2)

    # Save HC mean RDM
    rdm_hc_mean_path = output_roi_dir / "rdm_hc_mean.npy"
    np.save(rdm_hc_mean_path, rdm_hc_mean)

    print(f"\n=== Outputs Saved ===")
    print(f"  Metrics: {metrics_path}")
    print(f"  Statistics: {stats_path}")
    print(f"  HC mean RDM: {rdm_hc_mean_path}")

    print(f"\n✓ Step 4 complete for {roi}")


if __name__ == '__main__':
    main()
