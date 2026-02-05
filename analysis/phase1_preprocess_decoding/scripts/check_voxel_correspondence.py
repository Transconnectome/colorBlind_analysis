"""
Check if selected voxels actually correspond across subjects.

CRITICAL: We selected top-k voxels per subject by F-score.
But are these the SAME physical voxels, or just the same NUMBER of voxels?

If voxel indices differ across subjects, we're comparing unrelated voxels!
"""

import numpy as np
import json
from pathlib import Path


def load_voxel_indices(input_dir, subject, roi):
    """
    Load voxel indices for one subject-ROI.
    """
    voxel_idx_path = input_dir / f"sub-{subject}" / roi / "voxel_indices.npy"

    if not voxel_idx_path.exists():
        return None

    indices = np.load(voxel_idx_path)
    return indices


def check_voxel_overlap(input_dir, roi, subjects):
    """
    Check how many voxels overlap across subjects.
    """
    print(f"\n{'='*80}")
    print(f"Checking Voxel Correspondence: {roi}")
    print(f"{'='*80}")

    # Load indices for all subjects
    all_indices = {}
    for subject in subjects:
        indices = load_voxel_indices(input_dir, subject, roi)
        if indices is not None:
            all_indices[subject] = set(indices)
            print(f"  sub-{subject}: {len(indices)} voxels, indices range [{np.min(indices)}, {np.max(indices)}]")

    if len(all_indices) < 2:
        print("  Not enough subjects to compare")
        return None

    # Compute pairwise overlaps
    subjects_list = sorted(all_indices.keys())
    n_subjects = len(subjects_list)

    print(f"\n{'Pairwise Voxel Overlap:'}")
    print(f"{'-'*80}")

    overlap_matrix = np.zeros((n_subjects, n_subjects))

    for i, subj_i in enumerate(subjects_list):
        for j, subj_j in enumerate(subjects_list):
            if i >= j:
                continue

            indices_i = all_indices[subj_i]
            indices_j = all_indices[subj_j]

            overlap = len(indices_i & indices_j)
            total = len(indices_i | indices_j)
            jaccard = overlap / total if total > 0 else 0

            overlap_matrix[i, j] = overlap
            overlap_matrix[j, i] = overlap

            print(f"  sub-{subj_i} vs sub-{subj_j}: {overlap}/{len(indices_i)} overlap ({overlap/len(indices_i)*100:.1f}%), Jaccard={jaccard:.3f}")

    # Compute statistics
    overlaps = []
    jaccards = []

    for i in range(n_subjects):
        for j in range(i+1, n_subjects):
            subj_i = subjects_list[i]
            subj_j = subjects_list[j]

            indices_i = all_indices[subj_i]
            indices_j = all_indices[subj_j]

            overlap = len(indices_i & indices_j)
            k = len(indices_i)  # Assume all have same k
            total = len(indices_i | indices_j)

            overlaps.append(overlap / k)  # Fraction of overlap
            jaccards.append(overlap / total)

    print(f"\n{'Summary Statistics:'}")
    print(f"{'-'*80}")
    print(f"  Mean overlap fraction: {np.mean(overlaps):.3f} ± {np.std(overlaps):.3f}")
    print(f"  Median overlap fraction: {np.median(overlaps):.3f}")
    print(f"  Range: [{np.min(overlaps):.3f}, {np.max(overlaps):.3f}]")
    print(f"  Mean Jaccard index: {np.mean(jaccards):.3f} ± {np.std(jaccards):.3f}")

    # Interpretation
    print(f"\n{'Interpretation:'}")
    print(f"{'-'*80}")

    mean_overlap = np.mean(overlaps)

    if mean_overlap > 0.8:
        status = "EXCELLENT - Voxels are mostly the same"
    elif mean_overlap > 0.5:
        status = "GOOD - Moderate overlap"
    elif mean_overlap > 0.3:
        status = "MODERATE - Some overlap"
    elif mean_overlap > 0.1:
        status = "POOR - Little overlap"
    else:
        status = "CRITICAL - Almost no overlap! Voxels are different!"

    print(f"  Status: {status}")

    if mean_overlap < 0.5:
        print(f"\n  ⚠️  WARNING:")
        print(f"  Voxels selected for each subject are DIFFERENT!")
        print(f"  We're aligning patterns from UNRELATED voxels!")
        print(f"  This makes Procrustes alignment meaningless!")

    return {
        'roi': roi,
        'n_subjects': n_subjects,
        'mean_overlap_fraction': float(np.mean(overlaps)),
        'std_overlap_fraction': float(np.std(overlaps)),
        'mean_jaccard': float(np.mean(jaccards)),
        'overlap_matrix': overlap_matrix.tolist(),
        'subjects': subjects_list
    }


def main():
    input_dir = Path("results/baseline_anova_selected")

    hc_subjects = ['01', '02', '03', '04', '05', '06', '07']
    cvd_subjects = ['08', '09', '10']
    all_subjects = hc_subjects + cvd_subjects

    print("="*80)
    print("Voxel Correspondence Check")
    print("="*80)
    print("\nQuestion: Are the selected top-k voxels the SAME physical voxels")
    print("          across subjects, or just the same NUMBER of voxels?")
    print("="*80)

    results = {}

    for roi in ['V1', 'V2', 'V3', 'hV4']:
        exclude = ['07'] if roi == 'V3' else []
        subjects = [s for s in all_subjects if s not in exclude]

        result = check_voxel_overlap(input_dir, roi, subjects)

        if result:
            results[roi] = result

    # Save results
    output_dir = Path("results/voxel_correspondence_check")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "voxel_overlap_analysis.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*80}")
    print(f"Overall Summary")
    print(f"{'='*80}")

    for roi in ['V1', 'V2', 'V3', 'hV4']:
        if roi in results:
            mean_overlap = results[roi]['mean_overlap_fraction']
            print(f"{roi}: {mean_overlap:.1%} mean overlap")

    print(f"\n✅ Results saved to: {output_file}")
    print("="*80)


if __name__ == '__main__':
    main()
