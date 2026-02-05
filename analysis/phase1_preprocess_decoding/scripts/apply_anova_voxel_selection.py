"""
Apply ANOVA-based top-k voxel selection to create common voxel space.

This script:
1. Loads raw amplitudes for each subject-ROI pair
2. Computes ANOVA F-scores for each voxel
3. Selects top-k voxels (k determined per ROI from section 3.1.1.a)
4. Saves selected amplitudes and voxel indices

Usage:
    python scripts/apply_anova_voxel_selection.py \
        --input-dir results/baseline \
        --output-dir results/baseline_anova_selected \
        --k-values V1:129,V2:103,V3:50,hV4:57
"""

import numpy as np
import json
import argparse
from pathlib import Path
from scipy.stats import f_oneway


def compute_voxel_f_scores(amplitudes):
    """
    Compute ANOVA F-score for each voxel.

    Parameters
    ----------
    amplitudes : np.ndarray, shape (n_runs, n_colors, n_voxels)
        FIR amplitude estimates

    Returns
    -------
    f_scores : np.ndarray, shape (n_voxels,)
        F-score for each voxel
    p_values : np.ndarray, shape (n_voxels,)
        P-value for each voxel
    """
    n_runs, n_colors, n_voxels = amplitudes.shape

    # Reshape: (n_voxels, n_runs, n_colors)
    amps_per_voxel = np.transpose(amplitudes, (2, 0, 1))

    f_scores = np.zeros(n_voxels)
    p_values = np.zeros(n_voxels)

    for v in range(n_voxels):
        # For this voxel, get responses across 6 runs for each color
        voxel_data = amps_per_voxel[v]  # (n_runs, n_colors)

        # Create groups: one per color
        groups = [voxel_data[:, c] for c in range(n_colors)]

        # One-way ANOVA: H0 = all colors have same mean
        f_stat, p_val = f_oneway(*groups)

        f_scores[v] = f_stat
        p_values[v] = p_val

    return f_scores, p_values


def select_top_k_voxels(amplitudes, k, return_indices=True):
    """
    Select top-k voxels by ANOVA F-score.

    Parameters
    ----------
    amplitudes : np.ndarray, shape (n_runs, n_colors, n_voxels)
        Full amplitude estimates
    k : int
        Number of voxels to select
    return_indices : bool
        If True, also return selected voxel indices

    Returns
    -------
    selected_amplitudes : np.ndarray, shape (n_runs, n_colors, k)
        Amplitudes for top-k voxels
    selected_indices : np.ndarray, shape (k,)
        Indices of selected voxels (if return_indices=True)
    f_scores : np.ndarray, shape (n_voxels,)
        F-scores for all voxels
    """
    n_runs, n_colors, n_voxels = amplitudes.shape

    # Compute F-scores
    f_scores, p_values = compute_voxel_f_scores(amplitudes)

    # Check if k is valid
    if k > n_voxels:
        print(f"Warning: k={k} exceeds n_voxels={n_voxels}. Using all voxels.")
        k = n_voxels

    # Get top-k indices (highest F-scores)
    top_k_indices = np.argsort(f_scores)[::-1][:k]

    # Sort indices for consistent ordering
    top_k_indices = np.sort(top_k_indices)

    # Select amplitudes
    selected_amplitudes = amplitudes[:, :, top_k_indices]

    if return_indices:
        return selected_amplitudes, top_k_indices, f_scores
    else:
        return selected_amplitudes


def process_single_subject_roi(input_dir, output_dir, subject, roi, k):
    """
    Process one subject-ROI pair.

    Parameters
    ----------
    input_dir : Path
        Directory containing original amplitudes_raw.npy
    output_dir : Path
        Directory to save selected outputs
    subject : str
        Subject ID (e.g., '01')
    roi : str
        ROI name (e.g., 'V1')
    k : int
        Number of voxels to select
    """
    # Load original amplitudes (use raw, not procrustes-aligned)
    amp_path = input_dir / f"sub-{subject}" / roi / "amplitudes_raw.npy"

    if not amp_path.exists():
        print(f"Skipping sub-{subject}/{roi}: File not found")
        return None

    amplitudes = np.load(amp_path)
    n_runs, n_colors, n_voxels = amplitudes.shape

    print(f"\nProcessing sub-{subject}/{roi}:")
    print(f"  Original voxels: {n_voxels}")
    print(f"  Target k: {k}")

    # Select top-k voxels
    selected_amps, selected_indices, f_scores = select_top_k_voxels(
        amplitudes, k, return_indices=True
    )

    # Create output directory
    out_subj_roi_dir = output_dir / f"sub-{subject}" / roi
    out_subj_roi_dir.mkdir(parents=True, exist_ok=True)

    # Save selected amplitudes
    np.save(out_subj_roi_dir / "amplitudes.npy", selected_amps)

    # Save selected indices
    np.save(out_subj_roi_dir / "voxel_indices.npy", selected_indices)

    # Save all F-scores (for verification)
    np.save(out_subj_roi_dir / "f_scores_all_voxels.npy", f_scores)

    # Save metadata
    metadata = {
        'subject': subject,
        'roi': roi,
        'n_voxels_original': int(n_voxels),
        'n_voxels_selected': int(len(selected_indices)),
        'k_target': int(k),
        'f_score_threshold': float(f_scores[selected_indices[-1]]),  # Minimum F in top-k
        'f_score_mean_selected': float(np.mean(f_scores[selected_indices])),
        'f_score_median_selected': float(np.median(f_scores[selected_indices])),
        'selection_method': 'anova_top_k',
        'selection_percentile': float(k / n_voxels * 100)
    }

    with open(out_subj_roi_dir / "selection_metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"  Selected voxels: {len(selected_indices)}")
    print(f"  F-score range: [{f_scores[selected_indices].min():.2f}, {f_scores[selected_indices].max():.2f}]")
    print(f"  F-score threshold: {metadata['f_score_threshold']:.2f}")
    print(f"  Saved to: {out_subj_roi_dir}")

    return metadata


def main():
    parser = argparse.ArgumentParser(
        description='Apply ANOVA-based top-k voxel selection'
    )
    parser.add_argument('--input-dir', type=str, required=True,
                        help='Input directory with original results')
    parser.add_argument('--output-dir', type=str, required=True,
                        help='Output directory for selected results')
    parser.add_argument('--k-values', type=str, required=True,
                        help='K values per ROI (format: V1:129,V2:103,V3:50,hV4:57)')
    parser.add_argument('--subjects', type=str, default='01,02,03,04,05,06,07,08,09,10',
                        help='Subject IDs to process (comma-separated)')

    args = parser.parse_args()

    # Parse paths
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Parse k values
    k_dict = {}
    for pair in args.k_values.split(','):
        roi, k = pair.split(':')
        k_dict[roi] = int(k)

    # Parse subjects
    subjects = args.subjects.split(',')

    print("="*80)
    print("ANOVA-based Top-k Voxel Selection")
    print("="*80)
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    print(f"K values: {k_dict}")
    print(f"Subjects: {subjects}")
    print("="*80)

    # Process all subject-ROI pairs
    all_metadata = {}

    for subject in subjects:
        for roi in ['V1', 'V2', 'V3', 'hV4']:
            if roi not in k_dict:
                print(f"\nSkipping {roi}: No k value specified")
                continue

            k = k_dict[roi]

            metadata = process_single_subject_roi(
                input_dir, output_dir, subject, roi, k
            )

            if metadata:
                key = f"sub-{subject}_{roi}"
                all_metadata[key] = metadata

    # Save summary
    summary_path = output_dir / "selection_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(all_metadata, f, indent=2)

    print("\n" + "="*80)
    print(f"✅ Completed: {len(all_metadata)} subject-ROI pairs processed")
    print(f"Summary saved to: {summary_path}")
    print("="*80)

    # Print statistics per ROI
    print("\nVoxel Selection Statistics by ROI:")
    print("-"*80)
    for roi in ['V1', 'V2', 'V3', 'hV4']:
        roi_data = [v for k, v in all_metadata.items() if k.endswith(f"_{roi}")]
        if roi_data:
            n_subjects = len(roi_data)
            k_target = roi_data[0]['k_target']
            f_thresholds = [d['f_score_threshold'] for d in roi_data]

            print(f"\n{roi}:")
            print(f"  Subjects processed: {n_subjects}")
            print(f"  Target k: {k_target}")
            print(f"  F-score threshold range: [{min(f_thresholds):.2f}, {max(f_thresholds):.2f}]")
            print(f"  F-score threshold mean: {np.mean(f_thresholds):.2f}")


if __name__ == '__main__':
    main()
