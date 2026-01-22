#!/usr/bin/env python3
"""
Output Path Management for colorBlind Analysis Pipeline

Provides standardized output directory structure:
- analysis/roi_masks/{dataset}/          - Shared ROI masks (used by all phases)
- analysis/{phase}/{dataset}/results/    - Phase-specific results
- analysis/{phase}/{dataset}/logs/       - Phase-specific logs

Usage:
    from utils.output_paths import get_roi_paths, get_phase_paths

    # Shared ROI masks
    roi_paths = get_roi_paths(dataset='method3_header_mi', subject_id='01')
    # Returns: analysis/roi_masks/method3_header_mi/sub-01/

    # Phase-specific results
    phase_paths = get_phase_paths(phase='phase1_preprocess_decoding', dataset='method3_header_mi')
    # Returns: analysis/phase1_preprocess_decoding/method3_header_mi/results/
    #          analysis/phase1_preprocess_decoding/method3_header_mi/logs/
"""

from pathlib import Path
from typing import Dict, Optional


# Base directory (server path)
BASE_DIR = Path('/scratch/connectome/haba6030/colorBlind')


def get_roi_paths(
    dataset: str,
    subject_id: str,
    create: bool = True
) -> Dict[str, Path]:
    """
    Get paths for ROI masks (SHARED RESOURCE - used by all phases).

    Args:
        dataset: Dataset name (e.g., 'method3_header_mi', 'original_v3')
        subject_id: Subject ID (e.g., '01', '02')
        create: Create directories if they don't exist

    Returns:
        Dictionary with 'roi_dir', 'subject_dir' paths

    Example:
        >>> paths = get_roi_paths('method3_header_mi', '01')
        >>> paths['subject_dir']
        PosixPath('/scratch/connectome/haba6030/colorBlind/analysis/roi_masks/method3_header_mi/sub-01')
    """
    roi_base_dir = BASE_DIR / 'analysis' / 'roi_masks' / dataset
    subject_dir = roi_base_dir / f'sub-{subject_id}'

    if create:
        subject_dir.mkdir(parents=True, exist_ok=True)

    return {
        'roi_dir': roi_base_dir,
        'subject_dir': subject_dir
    }


def get_phase_paths(
    phase: str,
    dataset: str,
    subdir: Optional[str] = None,
    create: bool = True
) -> Dict[str, Path]:
    """
    Get standardized output paths for a phase and dataset.

    Args:
        phase: Phase name (e.g., 'phase1_preprocess_decoding', 'phase2_procrustes_cvd_hc')
        dataset: Dataset name (e.g., 'method3_header_mi')
        subdir: Optional subdirectory under results/ (e.g., 'baseline_decoding')
        create: Create directories if they don't exist

    Returns:
        Dictionary with 'results', 'logs', 'phase_dir' Path objects

    Example:
        >>> paths = get_phase_paths('phase1_preprocess_decoding', 'method3_header_mi')
        >>> paths['results']
        PosixPath('/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/method3_header_mi/results')
    """
    phase_dir = BASE_DIR / 'analysis' / phase / dataset
    results_dir = phase_dir / 'results'

    if subdir:
        results_dir = results_dir / subdir

    logs_dir = phase_dir / 'logs'

    if create:
        results_dir.mkdir(parents=True, exist_ok=True)
        logs_dir.mkdir(parents=True, exist_ok=True)

    return {
        'results': results_dir,
        'logs': logs_dir,
        'phase_dir': phase_dir
    }


def get_baseline_paths(
    dataset: str,
    subject_id: str,
    roi: str,
    timestamp: Optional[str] = None,
    create: bool = True
) -> Dict[str, Path]:
    """
    Get output paths for baseline decoding (Phase 1).

    Args:
        dataset: Dataset name
        subject_id: Subject ID (e.g., '01', '02')
        roi: ROI name (e.g., 'V1', 'V2')
        timestamp: Optional timestamp for run
        create: Create directories if they don't exist

    Returns:
        Dictionary with baseline decoding paths

    Example:
        >>> paths = get_baseline_paths('method3_header_mi', '01', 'V1', '20260122_120000')
        >>> paths['results']
        PosixPath('.../phase1_preprocess_decoding/method3_header_mi/results/baseline_decoding/20260122_120000/sub-01/V1')
    """
    if timestamp:
        subdir = f'baseline_decoding/{timestamp}/sub-{subject_id}/{roi}'
    else:
        subdir = f'baseline_decoding/sub-{subject_id}/{roi}'

    paths = get_phase_paths(
        phase='phase1_preprocess_decoding',
        dataset=dataset,
        subdir=subdir,
        create=create
    )
    return paths


def get_procrustes_paths(
    dataset: str,
    create: bool = True
) -> Dict[str, Path]:
    """
    Get output paths for Procrustes analysis (Phase 2).

    Args:
        dataset: Dataset name
        create: Create directories if they don't exist

    Returns:
        Dictionary with procrustes paths
    """
    paths = get_phase_paths(
        phase='phase2_procrustes_cvd_hc',
        dataset=dataset,
        create=create
    )
    return paths


def get_filter_paths(
    dataset: str,
    create: bool = True
) -> Dict[str, Path]:
    """
    Get output paths for filter learning (Phase 3).

    Args:
        dataset: Dataset name
        create: Create directories if they don't exist

    Returns:
        Dictionary with filter paths
    """
    paths = get_phase_paths(
        phase='phase3_procrustes_filter',
        dataset=dataset,
        create=create
    )
    return paths


def get_prep_trials_paths(
    dataset: str,
    create: bool = True
) -> Dict[str, Path]:
    """
    Get output paths for preprocessing trials.

    Args:
        dataset: Dataset name
        create: Create directories if they don't exist

    Returns:
        Dictionary with prep_trials paths
    """
    paths = get_phase_paths(
        phase='prep_trials',
        dataset=dataset,
        create=create
    )
    return paths


# Legacy compatibility wrapper
def get_legacy_output_dir(
    dataset: str,
    subject_id: str,
    roi: str,
    timestamp: str
) -> Path:
    """
    Get legacy output directory for backward compatibility.

    Maps OLD to NEW structure:
    OLD: derivatives/V3_Comprehensive/BH2009_{dataset}/{timestamp}/sub-{subject}/{roi}
    NEW: analysis/phase1_preprocess_decoding/{dataset}/results/baseline_decoding/{timestamp}/sub-{subject}/{roi}
    """
    paths = get_baseline_paths(
        dataset=dataset,
        subject_id=subject_id,
        roi=roi,
        timestamp=timestamp,
        create=True
    )
    return paths['results']


if __name__ == '__main__':
    # Test the functions
    print("="*70)
    print("Testing Output Path Functions")
    print("="*70)

    dataset = 'method3_header_mi'
    subject = '01'
    roi = 'V1'
    timestamp = '20260122_120000'

    print("\n1. SHARED RESOURCES - ROI Masks:")
    print("-" * 70)
    roi_paths = get_roi_paths(dataset, subject, create=False)
    for key, path in roi_paths.items():
        print(f"  {key:15s}: {path}")

    print("\n2. PHASE 1 - Baseline Decoding:")
    print("-" * 70)
    baseline_paths = get_baseline_paths(dataset, subject, roi, timestamp, create=False)
    for key, path in baseline_paths.items():
        print(f"  {key:15s}: {path}")

    print("\n3. PHASE 2 - Procrustes Analysis:")
    print("-" * 70)
    proc_paths = get_procrustes_paths(dataset, create=False)
    for key, path in proc_paths.items():
        print(f"  {key:15s}: {path}")

    print("\n4. PHASE 3 - Filter Learning:")
    print("-" * 70)
    filter_paths = get_filter_paths(dataset, create=False)
    for key, path in filter_paths.items():
        print(f"  {key:15s}: {path}")

    print("\n5. PREP TRIALS:")
    print("-" * 70)
    prep_paths = get_prep_trials_paths(dataset, create=False)
    for key, path in prep_paths.items():
        print(f"  {key:15s}: {path}")

    print("\n" + "="*70)
