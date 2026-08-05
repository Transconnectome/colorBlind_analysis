#!/usr/bin/env python3
"""
Prepare Procrustes-aligned amplitudes for test_zscore_FINAL baseline

This script applies Procrustes alignment to the test_zscore_FINAL baseline,
which is the target baseline for decoder model comparison.

Modified from: analysis/phase2_procrustes_cvd_hc/option2b_procrustes_alignment.py
"""

import os
import sys
import json
import argparse
from pathlib import Path
import numpy as np
from scipy.spatial import procrustes
from datetime import datetime

# Add project root to path
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root / "analysis"))

from utils.utils_common import create_output_directory


def load_subject_amplitudes(subject, roi, timestamp, dataset, base_dir):
    """
    Load amplitudes_z.npy for a subject-ROI combination

    Args:
        subject: Subject ID (e.g., '01')
        roi: ROI name (e.g., 'V1')
        timestamp: Baseline timestamp (e.g., 'test_zscore_FINAL')
        dataset: Dataset name (e.g., 'method3_header_mi')
        base_dir: Base directory path

    Returns:
        amplitudes: (n_runs, n_colors, n_voxels) array
        path: Path to the loaded file
    """
    # Construct path to baseline results
    baseline_dir = Path(base_dir) / "analysis" / "phase1_preprocess_decoding" / dataset / "results" / "baseline_decoding" / timestamp
    subject_dir = baseline_dir / f"sub-{subject}" / roi

    amplitudes_path = subject_dir / "amplitudes_z.npy"

    if not amplitudes_path.exists():
        raise FileNotFoundError(f"Amplitudes not found: {amplitudes_path}")

    amplitudes = np.load(amplitudes_path)
    print(f"Loaded {subject} {roi}: shape={amplitudes.shape}")

    return amplitudes, amplitudes_path


def align_to_reference_procrustes(target_data, reference_data):
    """
    Align target data to reference data using Procrustes

    Args:
        target_data: (n_runs, n_colors, n_voxels) - data to be aligned
        reference_data: (n_runs, n_colors, n_voxels) - reference data

    Returns:
        aligned_data: (n_runs, n_colors, n_voxels) - aligned target data
        disparity: Procrustes disparity (lower = better alignment)
    """
    n_runs, n_colors, n_voxels = target_data.shape

    # Reshape to 2D for Procrustes (conditions × voxels)
    target_2d = target_data.reshape(n_runs * n_colors, n_voxels)
    reference_2d = reference_data.reshape(n_runs * n_colors, n_voxels)

    # Apply Procrustes alignment
    # procrustes returns: (mtx1_aligned, mtx2, disparity)
    # We want to align target to reference
    _, aligned_2d, disparity = procrustes(reference_2d, target_2d)

    # Reshape back to original shape
    aligned_data = aligned_2d.reshape(n_runs, n_colors, n_voxels)

    return aligned_data, disparity


def prepare_aligned_amplitudes(subjects, rois, reference_subject, timestamp, dataset,
                               base_dir, output_dir):
    """
    Main function to prepare Procrustes-aligned amplitudes

    Args:
        subjects: List of subject IDs
        rois: List of ROI names
        reference_subject: Subject ID to use as reference
        timestamp: Baseline timestamp
        dataset: Dataset name
        base_dir: Base directory path
        output_dir: Output directory path
    """
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Track alignment results
    alignment_summary = {
        'reference_subject': reference_subject,
        'timestamp': timestamp,
        'dataset': dataset,
        'subjects': subjects,
        'rois': rois,
        'disparities': {}
    }

    print(f"\n{'='*80}")
    print(f"Procrustes Alignment Preparation")
    print(f"{'='*80}")
    print(f"Reference subject: sub-{reference_subject}")
    print(f"Timestamp: {timestamp}")
    print(f"Dataset: {dataset}")
    print(f"Output directory: {output_dir}")
    print(f"{'='*80}\n")

    # Process each ROI
    for roi in rois:
        print(f"\n{'='*60}")
        print(f"Processing ROI: {roi}")
        print(f"{'='*60}")

        # Load reference subject data
        print(f"\nLoading reference subject: sub-{reference_subject}")
        reference_data, reference_path = load_subject_amplitudes(
            reference_subject, roi, timestamp, dataset, base_dir
        )

        alignment_summary['disparities'][roi] = {}

        # Align each subject to reference
        for subject in subjects:
            print(f"\n--- Processing sub-{subject} ---")

            # Create output directory for this subject-ROI
            subject_output_dir = output_path / f"sub-{subject}" / roi
            subject_output_dir.mkdir(parents=True, exist_ok=True)

            # Load target subject data
            target_data, target_path = load_subject_amplitudes(
                subject, roi, timestamp, dataset, base_dir
            )

            # Save original data as backup
            original_save_path = subject_output_dir / "amplitudes_z_original.npy"
            np.save(original_save_path, target_data)
            print(f"Saved original: {original_save_path}")

            if subject == reference_subject:
                # Reference subject: just copy without alignment
                aligned_data = target_data.copy()
                disparity = 0.0
                print(f"Reference subject - no alignment needed")
            else:
                # Align to reference
                print(f"Aligning to reference...")
                aligned_data, disparity = align_to_reference_procrustes(target_data, reference_data)
                print(f"Procrustes disparity: {disparity:.6f}")

            # Save aligned data
            aligned_save_path = subject_output_dir / "amplitudes_z.npy"
            np.save(aligned_save_path, aligned_data)
            print(f"Saved aligned: {aligned_save_path}")

            # Save alignment info
            alignment_info = {
                'subject': subject,
                'roi': roi,
                'reference_subject': reference_subject,
                'disparity': float(disparity),
                'original_path': str(target_path),
                'aligned_path': str(aligned_save_path),
                'original_shape': target_data.shape,
                'aligned_shape': aligned_data.shape
            }

            info_save_path = subject_output_dir / "procrustes_info.json"
            with open(info_save_path, 'w') as f:
                json.dump(alignment_info, f, indent=2)
            print(f"Saved info: {info_save_path}")

            # Track disparity
            alignment_summary['disparities'][roi][subject] = float(disparity)

    # Save overall alignment summary
    summary_path = output_path / "alignment_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(alignment_summary, f, indent=2)
    print(f"\n{'='*80}")
    print(f"Alignment Summary saved: {summary_path}")
    print(f"{'='*80}\n")

    # Print disparity statistics
    print(f"\n{'='*60}")
    print(f"Disparity Statistics")
    print(f"{'='*60}")
    for roi in rois:
        disparities = [d for s, d in alignment_summary['disparities'][roi].items()
                      if s != reference_subject]
        if disparities:
            print(f"\n{roi}:")
            print(f"  Mean: {np.mean(disparities):.6f}")
            print(f"  Std:  {np.std(disparities):.6f}")
            print(f"  Min:  {np.min(disparities):.6f}")
            print(f"  Max:  {np.max(disparities):.6f}")

    print(f"\n{'='*80}")
    print(f"Procrustes alignment completed successfully!")
    print(f"{'='*80}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Prepare Procrustes-aligned amplitudes for decoder comparison"
    )
    parser.add_argument('--timestamp', type=str, required=True,
                       help='Baseline timestamp (e.g., test_zscore_FINAL)')
    parser.add_argument('--dataset', type=str, default='method3_header_mi',
                       help='Dataset name')
    parser.add_argument('--subjects', nargs='+', required=True,
                       help='Subject IDs (e.g., 01 02 03)')
    parser.add_argument('--reference_subject', type=str, required=True,
                       help='Reference subject ID (e.g., 02)')
    parser.add_argument('--rois', nargs='+', required=True,
                       help='ROI names (e.g., V1 V2 V3 hV4)')
    parser.add_argument('--base_dir', type=str,
                       default='/scratch/connectome/haba6030/colorBlind',
                       help='Base directory path')
    parser.add_argument('--output_dir', type=str, required=True,
                       help='Output directory path')

    args = parser.parse_args()

    # Prepare aligned amplitudes
    prepare_aligned_amplitudes(
        subjects=args.subjects,
        rois=args.rois,
        reference_subject=args.reference_subject,
        timestamp=args.timestamp,
        dataset=args.dataset,
        base_dir=args.base_dir,
        output_dir=args.output_dir
    )


if __name__ == '__main__':
    main()
