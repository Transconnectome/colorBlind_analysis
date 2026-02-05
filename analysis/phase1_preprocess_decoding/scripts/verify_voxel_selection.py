"""
Verify ANOVA voxel selection results.

This script:
1. Loads selected amplitudes from all subjects
2. Verifies all subjects have exactly k voxels per ROI
3. Computes statistics on F-score thresholds
4. Checks if voxel counts are now uniform (ready for between-subject Procrustes)

Usage:
    python scripts/verify_voxel_selection.py \
        --input-dir results/baseline_anova_selected
"""

import numpy as np
import json
import argparse
from pathlib import Path


def verify_subject_roi(input_dir, subject, roi):
    """
    Verify one subject-ROI pair.

    Returns
    -------
    stats : dict or None
        Statistics if successful, None if missing
    """
    subj_roi_dir = input_dir / f"sub-{subject}" / roi

    # Check required files
    amp_path = subj_roi_dir / "amplitudes.npy"
    idx_path = subj_roi_dir / "voxel_indices.npy"
    meta_path = subj_roi_dir / "selection_metadata.json"

    if not all([amp_path.exists(), idx_path.exists(), meta_path.exists()]):
        return None

    # Load data
    amplitudes = np.load(amp_path)
    indices = np.load(idx_path)
    with open(meta_path) as f:
        metadata = json.load(f)

    # Verify shapes
    n_runs, n_colors, n_voxels = amplitudes.shape
    assert n_runs == 6, f"Expected 6 runs, got {n_runs}"
    assert n_colors == 8, f"Expected 8 colors, got {n_colors}"
    assert n_voxels == len(indices), f"Voxel count mismatch: {n_voxels} != {len(indices)}"
    assert n_voxels == metadata['n_voxels_selected'], "Metadata mismatch"

    return {
        'subject': subject,
        'roi': roi,
        'n_voxels': n_voxels,
        'f_threshold': metadata['f_score_threshold'],
        'f_mean': metadata['f_score_mean_selected'],
        'f_median': metadata['f_score_median_selected'],
        'shape': amplitudes.shape
    }


def main():
    parser = argparse.ArgumentParser(
        description='Verify ANOVA voxel selection results'
    )
    parser.add_argument('--input-dir', type=str, required=True,
                        help='Directory with selected results')
    parser.add_argument('--subjects', type=str, default='01,02,03,04,05,06,07,08,09,10',
                        help='Subject IDs to verify (comma-separated)')

    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    subjects = args.subjects.split(',')

    print("="*80)
    print("Verifying ANOVA Voxel Selection Results")
    print("="*80)
    print(f"Input directory: {input_dir}")
    print(f"Subjects: {subjects}")
    print("="*80)

    # Collect all stats
    all_stats = {}

    for subject in subjects:
        for roi in ['V1', 'V2', 'V3', 'hV4']:
            stats = verify_subject_roi(input_dir, subject, roi)
            if stats:
                key = f"sub-{subject}_{roi}"
                all_stats[key] = stats

    # Group by ROI
    print("\nVoxel Count Verification (Between-Subject Procrustes Readiness):")
    print("-"*80)

    for roi in ['V1', 'V2', 'V3', 'hV4']:
        roi_stats = [s for k, s in all_stats.items() if k.endswith(f"_{roi}")]

        if not roi_stats:
            print(f"\n{roi}: No data found ❌")
            continue

        voxel_counts = [s['n_voxels'] for s in roi_stats]
        f_thresholds = [s['f_threshold'] for s in roi_stats]
        f_means = [s['f_mean'] for s in roi_stats]

        # Check uniformity
        is_uniform = len(set(voxel_counts)) == 1
        status = "✅ READY" if is_uniform else "❌ NOT UNIFORM"

        print(f"\n{roi}: {status}")
        print(f"  Subjects processed: {len(roi_stats)}")
        print(f"  Voxel count: {voxel_counts[0] if is_uniform else voxel_counts}")
        print(f"  F-score threshold:")
        print(f"    Range: [{min(f_thresholds):.2f}, {max(f_thresholds):.2f}]")
        print(f"    Mean: {np.mean(f_thresholds):.2f} ± {np.std(f_thresholds):.2f}")
        print(f"  F-score (selected voxels):")
        print(f"    Mean: {np.mean(f_means):.2f} ± {np.std(f_means):.2f}")

        # List subjects with counts
        if not is_uniform:
            print(f"  Voxel counts by subject:")
            for s in roi_stats:
                print(f"    sub-{s['subject']}: {s['n_voxels']}")

    # Overall summary
    print("\n" + "="*80)
    total_pairs = len(all_stats)
    expected_pairs = len(subjects) * 4

    if total_pairs == expected_pairs:
        print(f"✅ All {total_pairs} subject-ROI pairs verified successfully")
    else:
        print(f"⚠️  {total_pairs}/{expected_pairs} subject-ROI pairs found")

    # Check readiness for between-subject Procrustes
    ready_rois = []
    for roi in ['V1', 'V2', 'V3', 'hV4']:
        roi_stats = [s for k, s in all_stats.items() if k.endswith(f"_{roi}")]
        if roi_stats:
            voxel_counts = [s['n_voxels'] for s in roi_stats]
            if len(set(voxel_counts)) == 1:
                ready_rois.append(roi)

    if len(ready_rois) == 4:
        print("\n🎉 All ROIs ready for between-subject Procrustes alignment!")
    else:
        print(f"\n⚠️  Only {len(ready_rois)}/4 ROIs ready: {ready_rois}")

    print("="*80)


if __name__ == '__main__':
    main()
