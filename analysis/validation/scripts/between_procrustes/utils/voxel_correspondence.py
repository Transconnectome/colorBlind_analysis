#!/usr/bin/env python3
"""
voxel_correspondence.py
-----------------------
Utilities for finding spatially corresponding voxels across subjects

Purpose:
- Load ROI masks and extract MNI coordinates
- Find voxels that exist in ALL subjects (intersection)
- Extract amplitudes for common voxels from unfiltered baseline results

Key Functions:
- load_roi_mask_for_subject(): Load ROI mask and get coordinates
- find_common_voxels_across_subjects(): Find voxel intersection
- extract_common_voxel_amplitudes(): Get amplitudes for common voxels
"""

import numpy as np
import nibabel as nib
from pathlib import Path
from typing import List, Tuple, Dict


def load_roi_mask_for_subject(subject: str, roi: str, baseline_dir: Path) -> Tuple[nib.Nifti1Image, np.ndarray]:
    """
    Load ROI mask and extract nonzero voxel coordinates in MNI space

    Parameters
    ----------
    subject : str
        Subject ID (e.g., 'sub-01')
    roi : str
        ROI name (e.g., 'V1')
    baseline_dir : Path
        Path to baseline results directory

    Returns
    -------
    mask_img : nib.Nifti1Image
        ROI mask image
    coords : np.ndarray
        (n_voxels, 3) array of (x, y, z) coordinates in MNI space
    """
    # Find mask file in baseline directory
    mask_pattern = f"{baseline_dir}/*/sub-{subject}/{roi}/roi_mask.nii.gz"
    mask_files = list(Path(baseline_dir).glob(f"*/sub-{subject}/{roi}/roi_mask.nii.gz"))

    if len(mask_files) == 0:
        # Try alternative pattern (direct path without timestamp)
        mask_path = baseline_dir / f"sub-{subject}" / roi / "roi_mask.nii.gz"
        if not mask_path.exists():
            raise FileNotFoundError(f"ROI mask not found for {subject} {roi} in {baseline_dir}")
        mask_files = [mask_path]

    # Use the first (or only) match
    mask_path = mask_files[0]

    # Load mask
    mask_img = nib.load(str(mask_path))
    mask_data = mask_img.get_fdata()

    # Extract coordinates of nonzero voxels
    nonzero_indices = np.nonzero(mask_data > 0)
    coords = np.array(nonzero_indices).T  # (n_voxels, 3)

    return mask_img, coords


def find_common_voxels_across_subjects(subjects: List[str], roi: str, baseline_dir: Path) -> np.ndarray:
    """
    Find voxels that exist in ALL subjects

    Parameters
    ----------
    subjects : List[str]
        List of subject IDs (e.g., ['sub-01', 'sub-02'])
    roi : str
        ROI name (e.g., 'V1')
    baseline_dir : Path
        Path to baseline results directory

    Returns
    -------
    common_coords : np.ndarray
        (n_common, 3) array of (x, y, z) coordinates that exist in all subjects
    """
    print(f"Finding common voxels across {len(subjects)} subjects for ROI {roi}...")

    # Load coordinates for each subject
    coord_sets = []
    for subject in subjects:
        try:
            _, coords = load_roi_mask_for_subject(subject, roi, baseline_dir)
            # Convert to set of tuples for intersection
            coord_set = set(tuple(c) for c in coords)
            coord_sets.append(coord_set)
            print(f"  {subject}: {len(coord_set)} voxels")
        except FileNotFoundError as e:
            print(f"  Warning: {e}")
            continue

    if len(coord_sets) == 0:
        raise ValueError(f"No valid masks found for ROI {roi}")

    # Compute intersection
    common_coord_set = coord_sets[0]
    for coord_set in coord_sets[1:]:
        common_coord_set = common_coord_set & coord_set

    # Convert back to array and sort for reproducibility
    common_coords = np.array(sorted(list(common_coord_set)))

    print(f"  Common voxels: {len(common_coords)}")

    if len(common_coords) < 20:
        print(f"  ⚠️ WARNING: Very few common voxels ({len(common_coords)})")
        print(f"     This may indicate inconsistent ROI masks or misalignment")

    return common_coords


def load_unfiltered_amplitudes(subject: str, roi: str, baseline_dir: Path) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load amplitudes from modified preprocessing (no filtering applied)

    Parameters
    ----------
    subject : str
        Subject ID (e.g., 'sub-01')
    roi : str
        ROI name (e.g., 'V1')
    baseline_dir : Path
        Path to baseline results directory

    Returns
    -------
    amplitudes_z : np.ndarray
        (n_runs, n_colors, n_voxels) z-scored amplitudes
    coords : np.ndarray
        (n_voxels, 3) array of voxel coordinates
    """
    # Find amplitudes file
    amp_pattern = f"{baseline_dir}/*/sub-{subject}/{roi}/amplitudes_z.npy"
    amp_files = list(Path(baseline_dir).glob(f"*/sub-{subject}/{roi}/amplitudes_z.npy"))

    if len(amp_files) == 0:
        # Try alternative pattern (direct path without timestamp)
        amp_path = baseline_dir / f"sub-{subject}" / roi / "amplitudes_z.npy"
        if not amp_path.exists():
            raise FileNotFoundError(f"Amplitudes not found for {subject} {roi} in {baseline_dir}")
        amp_files = [amp_path]

    # Load amplitudes
    amp_path = amp_files[0]
    amplitudes_z = np.load(str(amp_path))

    # Load corresponding ROI mask to get coordinates
    _, coords = load_roi_mask_for_subject(subject, roi, baseline_dir)

    # Verify shape consistency
    if amplitudes_z.shape[2] != len(coords):
        print(f"  ⚠️ WARNING: Amplitude voxels ({amplitudes_z.shape[2]}) != mask voxels ({len(coords)})")
        print(f"     This may indicate R² filtering reduced voxel count")
        # In this case, we need to load the selected_voxels_mask to map correctly
        mask_path = amp_path.parent / "selected_voxels_mask.npy"
        if mask_path.exists():
            selected_mask = np.load(str(mask_path))
            coords = coords[selected_mask]
            print(f"     Applied R² selection mask: {len(coords)} voxels")
        else:
            raise ValueError(f"Cannot map amplitudes to coordinates for {subject} {roi}")

    return amplitudes_z, coords


def extract_common_voxel_amplitudes(subject: str, roi: str, common_coords: np.ndarray,
                                   baseline_dir: Path) -> np.ndarray:
    """
    Extract amplitudes for common voxels only

    Parameters
    ----------
    subject : str
        Subject ID (e.g., 'sub-01')
    roi : str
        ROI name (e.g., 'V1')
    common_coords : np.ndarray
        (n_common, 3) array of common voxel coordinates
    baseline_dir : Path
        Path to baseline results directory

    Returns
    -------
    amplitudes_common : np.ndarray
        (n_runs, n_colors, n_common) amplitudes for common voxels
    """
    # Load all amplitudes and coordinates for subject
    amplitudes_z, coords = load_unfiltered_amplitudes(subject, roi, baseline_dir)

    # Find indices of common_coords in subject's coords
    # Convert to sets of tuples for fast lookup
    coord_set = {tuple(c): i for i, c in enumerate(coords)}
    common_indices = []

    for common_coord in common_coords:
        coord_tuple = tuple(common_coord)
        if coord_tuple in coord_set:
            common_indices.append(coord_set[coord_tuple])
        else:
            # This shouldn't happen if common_coords was computed correctly
            raise ValueError(f"Common coordinate {common_coord} not found in {subject} {roi}")

    common_indices = np.array(common_indices)

    # Extract amplitudes at common indices
    amplitudes_common = amplitudes_z[:, :, common_indices]

    return amplitudes_common


def load_all_subjects_common_amplitudes(subjects: List[str], roi: str,
                                       baseline_dir: Path) -> Tuple[Dict[str, np.ndarray], np.ndarray]:
    """
    Load amplitudes for common voxels across all subjects

    Parameters
    ----------
    subjects : List[str]
        List of subject IDs
    roi : str
        ROI name
    baseline_dir : Path
        Path to baseline results directory

    Returns
    -------
    amplitudes_dict : Dict[str, np.ndarray]
        Dictionary mapping subject -> (n_runs, n_colors, n_common) amplitudes
    common_coords : np.ndarray
        (n_common, 3) array of common voxel coordinates
    """
    # Step 1: Find common voxels
    common_coords = find_common_voxels_across_subjects(subjects, roi, baseline_dir)

    # Step 2: Extract amplitudes for each subject
    amplitudes_dict = {}
    print(f"\nExtracting common voxel amplitudes...")
    for subject in subjects:
        try:
            amplitudes_common = extract_common_voxel_amplitudes(subject, roi, common_coords, baseline_dir)
            amplitudes_dict[subject] = amplitudes_common
            print(f"  {subject}: {amplitudes_common.shape}")
        except (FileNotFoundError, ValueError) as e:
            print(f"  Warning: {subject} - {e}")
            continue

    return amplitudes_dict, common_coords


if __name__ == '__main__':
    # Test script
    import sys

    # Example usage
    baseline_dir = Path("analysis/phase1_preprocess_decoding/deoblique_v2/results/baseline_decoding/fixed_perRun_unfiltered")
    subjects = ['sub-01', 'sub-02']
    roi = 'V1'

    print("="*70)
    print("Testing voxel correspondence utilities")
    print("="*70)

    # Test 1: Find common voxels
    common_coords = find_common_voxels_across_subjects(subjects, roi, baseline_dir)
    print(f"\nCommon voxels found: {len(common_coords)}")

    # Test 2: Load amplitudes
    amplitudes_dict, _ = load_all_subjects_common_amplitudes(subjects, roi, baseline_dir)
    print(f"\nAmplitudes loaded for {len(amplitudes_dict)} subjects")

    for subject, amp in amplitudes_dict.items():
        print(f"  {subject}: {amp.shape}")
