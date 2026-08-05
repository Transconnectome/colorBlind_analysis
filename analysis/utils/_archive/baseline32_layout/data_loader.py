#!/usr/bin/env python3
"""
Common Data Loading Utilities for colorBlind Analysis Pipeline

Provides standardized functions to load baseline decoding results across phases.
Handles both new and legacy directory structures for backward compatibility.
"""

import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional


# Base directory
BASE_DIR = Path('/scratch/connectome/haba6030/colorBlind')


def load_baseline_amplitudes(
    subject_id: str,
    roi: str,
    timestamp: str,
    dataset: str = 'method3_header_mi'
) -> Tuple[np.ndarray, Path]:
    """
    Load baseline decoding amplitudes for a subject-ROI.

    Args:
        subject_id: Subject ID (e.g., '01', '02')
        roi: ROI name (e.g., 'V1', 'V2')
        timestamp: Timestamp of baseline run (e.g., '20260122_120000')
        dataset: Dataset name (default: 'method3_header_mi')

    Returns:
        amplitudes: numpy array of shape (n_runs, n_colors, n_voxels)
        result_dir: Path to result directory

    Raises:
        FileNotFoundError: If amplitudes file not found in any location
    """
    # Priority 1: New structure
    result_dir = (BASE_DIR / 'analysis' / 'phase1_preprocess_decoding' / dataset /
                  'results' / 'baseline_decoding' / timestamp / f'sub-{subject_id}' / roi)

    amp_file = result_dir / 'amplitudes_z.npy'

    if amp_file.exists():
        amplitudes = np.load(amp_file)
        return amplitudes, result_dir

    # Priority 2: Legacy structure (backward compatibility)
    legacy_dir = (BASE_DIR / 'derivatives' / 'V3_Comprehensive' /
                  f'BH2009_{dataset}' / timestamp / f'sub-{subject_id}' / roi)

    legacy_amp_file = legacy_dir / 'amplitudes_z.npy'

    if legacy_amp_file.exists():
        print(f"  ⚠️  Using legacy location: {legacy_dir}")
        amplitudes = np.load(legacy_amp_file)
        return amplitudes, legacy_dir

    # Not found in either location
    raise FileNotFoundError(
        f"Amplitudes not found for sub-{subject_id}, ROI {roi}\n"
        f"  Checked new: {result_dir}\n"
        f"  Checked legacy: {legacy_dir}"
    )


def load_all_subjects_amplitudes(
    subjects: List[str],
    roi: str,
    timestamp: str,
    dataset: str = 'method3_header_mi',
    verbose: bool = True
) -> Tuple[List[np.ndarray], List[Dict]]:
    """
    Load baseline amplitudes for multiple subjects.

    Args:
        subjects: List of subject IDs
        roi: ROI name
        timestamp: Timestamp of baseline run
        dataset: Dataset name
        verbose: Print loading info

    Returns:
        amplitudes_all: List of amplitude arrays
        subjects_info: List of subject info dictionaries

    Raises:
        FileNotFoundError: If any subject's data not found
    """
    if verbose:
        print(f"Loading {roi} data for {len(subjects)} subjects...")

    amplitudes_all = []
    subjects_info = []

    for subject_id in subjects:
        try:
            amplitudes, result_dir = load_baseline_amplitudes(
                subject_id, roi, timestamp, dataset
            )

            n_runs, n_colors, n_voxels = amplitudes.shape

            amplitudes_all.append(amplitudes)
            subjects_info.append({
                'subject': subject_id,
                'n_runs': n_runs,
                'n_colors': n_colors,
                'n_voxels': n_voxels,
                'result_dir': result_dir
            })

            if verbose:
                print(f"  sub-{subject_id}: {amplitudes.shape}")

        except FileNotFoundError as e:
            print(f"  ✗ sub-{subject_id}: {e}")
            raise

    if verbose:
        print(f"✓ Loaded {len(amplitudes_all)} subjects")

    return amplitudes_all, subjects_info


def load_roi_mask(
    subject_id: str,
    roi: str,
    dataset: str = 'method3_header_mi',
    mask_config: str = 'thr50_intnearest_binTrue_maskfunc_gmTrue_subjTrue'
) -> Path:
    """
    Get path to ROI mask file.

    Args:
        subject_id: Subject ID
        roi: ROI name
        dataset: Dataset name
        mask_config: ROI mask configuration string

    Returns:
        Path to ROI mask file

    Raises:
        FileNotFoundError: If mask not found
    """
    # Priority 1: Shared location
    roi_mask_path = (BASE_DIR / 'analysis' / 'roi_masks' / dataset /
                     f'sub-{subject_id}' / f'{roi}_mask_{mask_config}.nii.gz')

    if roi_mask_path.exists():
        return roi_mask_path

    # Priority 2: Legacy location
    legacy_mask_path = (BASE_DIR / 'derivatives' / 'V3_Comprehensive' / 'ROI_mask' /
                        f'sub-{subject_id}' / 'roi_pipeline' /
                        f'{roi}_mask_{mask_config}.nii.gz')

    if legacy_mask_path.exists():
        print(f"  ⚠️  Using legacy ROI mask: {legacy_mask_path}")
        return legacy_mask_path

    raise FileNotFoundError(
        f"ROI mask not found for sub-{subject_id}, ROI {roi}\n"
        f"  Checked new: {roi_mask_path}\n"
        f"  Checked legacy: {legacy_mask_path}"
    )


def get_output_directory(
    phase: str,
    dataset: str,
    subdir: Optional[str] = None
) -> Path:
    """
    Get and create output directory for a phase.

    Args:
        phase: Phase name (e.g., 'phase2_procrustes_cvd_hc')
        dataset: Dataset name
        subdir: Optional subdirectory under results/

    Returns:
        Path to results directory
    """
    phase_dir = BASE_DIR / 'analysis' / phase / dataset
    results_dir = phase_dir / 'results'

    if subdir:
        results_dir = results_dir / subdir

    results_dir.mkdir(parents=True, exist_ok=True)

    # Also create logs directory
    logs_dir = phase_dir / 'logs'
    logs_dir.mkdir(parents=True, exist_ok=True)

    return results_dir


if __name__ == '__main__':
    # Test the functions
    print("="*70)
    print("Testing Data Loading Functions")
    print("="*70)

    dataset = 'method3_header_mi'
    subject = '01'
    roi = 'V1'
    timestamp = '20260122_120000'

    print("\n1. Test load_baseline_amplitudes:")
    print("-" * 70)
    try:
        amps, result_dir = load_baseline_amplitudes(subject, roi, timestamp, dataset)
        print(f"  ✓ Loaded: {amps.shape}")
        print(f"  Location: {result_dir}")
    except FileNotFoundError as e:
        print(f"  ✗ {e}")

    print("\n2. Test load_roi_mask:")
    print("-" * 70)
    try:
        mask_path = load_roi_mask(subject, roi, dataset)
        print(f"  ✓ Found: {mask_path}")
    except FileNotFoundError as e:
        print(f"  ✗ {e}")

    print("\n3. Test get_output_directory:")
    print("-" * 70)
    output_dir = get_output_directory('phase2_procrustes_cvd_hc', dataset)
    print(f"  ✓ Created: {output_dir}")

    print("\n" + "="*70)
