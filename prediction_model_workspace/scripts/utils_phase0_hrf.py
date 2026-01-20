#!/usr/bin/env python3
"""
Utilities for loading Phase 0 HRF and voxel selection results

Phase 0 baseline decoding (analysis/phase1_preprocess_decoding) uses:
1. FIR-based data-driven HRF estimation (8 delays, 12s window)
2. Voxel selection (top 50% by FIR R²)
3. ROI-specific HRF (per subject, per ROI)

This module loads those results for reuse in trial-wise GLM.

Created: 2026-01-11
"""

import numpy as np
import nibabel as nib
from pathlib import Path
import glob


def find_phase0_result_dir(subject_id, roi, derivatives_dir,
                           dataset='original_v3',
                           timestamp='baseline32_original_v3'):
    """
    Find Phase 0 result directory matching subject and ROI

    Phase 0 directory structure (from comprehensive analysis):
    derivatives/V3_Comprehensive/BH2009_{dataset}/{timestamp}/sub-{ID}/{ROI}/

    Reference: analysis/comprehensive/phase0_parallel_node4_mem45.sbatch
    - DATASET="original_v3"
    - TIMESTAMP="baseline32_original_v3"

    Parameters
    ----------
    subject_id : str
        Subject ID (e.g., '01')
    roi : str
        ROI name (e.g., 'V1', 'V2', 'V3', 'hV4')
    derivatives_dir : str or Path
        Base derivatives directory
    dataset : str
        Dataset name (default: 'original_v3')
    timestamp : str
        Analysis timestamp (default: 'baseline32_original_v3')

    Returns
    -------
    Path
        Path to Phase 0 result directory

    Raises
    ------
    FileNotFoundError
        If no matching directory found
    ValueError
        If multiple directories match
    """
    # Phase 0 output structure from fir_reconstruction_BH2009_system_clean.py line 532:
    # derivatives/V3_Comprehensive/BH2009_{DATASET}/{timestamp}/sub-{SUBJECT_ID}/{ROI_NAME}
    result_dir = Path(derivatives_dir) / 'V3_Comprehensive' / f'BH2009_{dataset}' / timestamp / f'sub-{subject_id}' / roi

    if not result_dir.exists():
        raise FileNotFoundError(
            f"No Phase 0 result found for sub-{subject_id} {roi}\n"
            f"Expected: {result_dir}\n"
            f"Make sure Phase 0 baseline has been run with:\n"
            f"  --dataset {dataset}\n"
            f"  --timestamp {timestamp}"
        )

    return result_dir


def load_phase0_hrf(subject_id, roi, derivatives_dir,
                   dataset='original_v3',
                   timestamp='baseline32_original_v3'):
    """
    Load Phase 0 data-driven HRF for subject and ROI

    Phase 0 HRF estimation (fir_reconstruction_BH2009_system_clean.py):
    1. Voxel-wise FIR estimation (8 delays, pseudo-inverse)
    2. R² calculation and top 50% voxel selection
    3. ROI average HRF = mean(HRF_voxel[selected])
    4. Numerical derivative computation

    Parameters
    ----------
    subject_id : str
        Subject ID (e.g., '01')
    roi : str
        ROI name (e.g., 'V1')
    derivatives_dir : str or Path
        Base derivatives directory
    dataset : str
        Dataset name (default: 'original_v3')
    timestamp : str
        Analysis timestamp (default: 'baseline32_original_v3')

    Returns
    -------
    roi_hrf : ndarray
        ROI average HRF (n_delays,)
    roi_hrf_deriv : ndarray
        HRF numerical derivative (n_delays,)

    Raises
    ------
    FileNotFoundError
        If HRF files not found

    Notes
    -----
    Reference implementation:
    /Users/jinilkim/.../analysis/phase1_preprocess_decoding/fir_reconstruction_BH2009_system_clean.py

    Phase 0 saves:
    - roi_hrf.npy: (8,) ROI average HRF
    - roi_hrf_deriv.npy: (8,) numerical derivative
    """
    result_dir = find_phase0_result_dir(
        subject_id, roi, derivatives_dir, dataset, timestamp
    )

    hrf_file = result_dir / 'roi_hrf.npy'
    deriv_file = result_dir / 'roi_hrf_deriv.npy'

    if not hrf_file.exists():
        raise FileNotFoundError(
            f"Phase 0 HRF not found: {hrf_file}\n"
            f"Directory exists but missing roi_hrf.npy"
        )

    roi_hrf = np.load(hrf_file)
    roi_hrf_deriv = np.load(deriv_file)

    return roi_hrf, roi_hrf_deriv


def load_phase0_voxel_mask(subject_id, roi, derivatives_dir,
                           dataset='original_v3',
                           timestamp='baseline32_original_v3',
                           return_r2=False):
    """
    Load Phase 0 selected voxels mask (top 50% by FIR R²)

    Phase 0 voxel selection:
    1. Voxel-wise FIR R² calculation
    2. Select top 50% voxels by R²
    3. Save boolean mask

    Parameters
    ----------
    subject_id : str
        Subject ID
    roi : str
        ROI name
    derivatives_dir : str or Path
        Base derivatives directory
    dataset : str
        Dataset name (default: 'original_v3')
    timestamp : str
        Analysis timestamp (default: 'baseline32_original_v3')
    return_r2 : bool
        If True, also return R² values for all voxels

    Returns
    -------
    selected_voxels_mask : ndarray
        Boolean mask (n_voxels,), True for selected voxels
    r2_voxel : ndarray, optional
        R² values for all voxels (n_voxels,), if return_r2=True

    Notes
    -----
    Reference: fir_reconstruction_BH2009_system_clean.py lines 1090-1142

    Voxel selection ensures high SNR voxels are used, improving reliability.
    """
    result_dir = find_phase0_result_dir(
        subject_id, roi, derivatives_dir, dataset, timestamp
    )

    mask_file = result_dir / 'selected_voxels_mask.npy'

    if not mask_file.exists():
        raise FileNotFoundError(
            f"Phase 0 voxel mask not found: {mask_file}\n"
            f"Directory exists but missing selected_voxels_mask.npy"
        )

    selected_voxels_mask = np.load(mask_file)

    if return_r2:
        r2_file = result_dir / 'r2_voxel.npy'
        if not r2_file.exists():
            raise FileNotFoundError(f"R² file not found: {r2_file}")
        r2_voxel = np.load(r2_file)
        return selected_voxels_mask, r2_voxel

    return selected_voxels_mask


def create_selected_voxels_mask_img(selected_voxels_mask, roi_mask_file):
    """
    Create NIfTI mask image for selected voxels (for nilearn masker)

    Parameters
    ----------
    selected_voxels_mask : ndarray
        Boolean mask (n_voxels,) from Phase 0
    roi_mask_file : str or Path
        Path to full ROI mask NIfTI file

    Returns
    -------
    selected_mask_img : Nifti1Image
        NIfTI image with selected voxels only

    Notes
    -----
    This converts the 1D boolean mask back to 3D brain space for use
    with nilearn's NiftiMasker.
    """
    # Load full ROI mask
    roi_mask_img = nib.load(str(roi_mask_file))
    roi_mask_data = roi_mask_img.get_fdata()

    # Create new mask: roi_mask AND selected_voxels
    # Get indices of ROI voxels
    roi_voxel_indices = np.where(roi_mask_data.ravel() > 0)[0]

    if len(roi_voxel_indices) != len(selected_voxels_mask):
        raise ValueError(
            f"Mismatch: ROI has {len(roi_voxel_indices)} voxels, "
            f"but Phase 0 mask has {len(selected_voxels_mask)}"
        )

    # Create new 3D mask
    selected_mask_data = np.zeros_like(roi_mask_data)
    selected_roi_indices = roi_voxel_indices[selected_voxels_mask]

    # Unravel indices and set to 1
    coords = np.unravel_index(selected_roi_indices, roi_mask_data.shape)
    selected_mask_data[coords] = 1

    # Create new NIfTI image
    selected_mask_img = nib.Nifti1Image(
        selected_mask_data,
        roi_mask_img.affine,
        roi_mask_img.header
    )

    return selected_mask_img


def get_phase0_summary(subject_id, roi, derivatives_dir,
                      dataset='original_v3',
                      timestamp='baseline32_original_v3'):
    """
    Get summary of Phase 0 results for this subject/ROI

    Returns
    -------
    summary : dict
        Dictionary with:
        - result_dir: Path to Phase 0 results
        - n_voxels_total: Total voxels in ROI
        - n_voxels_selected: Selected voxels (top 50%)
        - selection_rate: Fraction selected
        - hrf_peak_delay: Delay index of HRF peak
        - hrf_peak_value: Peak HRF amplitude
    """
    result_dir = find_phase0_result_dir(
        subject_id, roi, derivatives_dir, dataset, timestamp
    )

    roi_hrf, _ = load_phase0_hrf(
        subject_id, roi, derivatives_dir, dataset, timestamp
    )

    selected_mask, r2_voxel = load_phase0_voxel_mask(
        subject_id, roi, derivatives_dir, dataset, timestamp,
        return_r2=True
    )

    summary = {
        'result_dir': str(result_dir),
        'n_voxels_total': len(selected_mask),
        'n_voxels_selected': int(selected_mask.sum()),
        'selection_rate': float(selected_mask.sum() / len(selected_mask)),
        'hrf_peak_delay': int(np.argmax(roi_hrf)),
        'hrf_peak_value': float(np.max(roi_hrf)),
        'mean_r2_selected': float(r2_voxel[selected_mask].mean()),
        'mean_r2_all': float(r2_voxel.mean()),
    }

    return summary


# Example usage and testing
if __name__ == '__main__':
    import sys

    if len(sys.argv) < 3:
        print("Usage: python utils_phase0_hrf.py <subject_id> <roi>")
        print("Example: python utils_phase0_hrf.py 01 V1")
        sys.exit(1)

    subject_id = sys.argv[1]
    roi = sys.argv[2]

    derivatives_dir = '/scratch/connectome/haba6030/colorBlind/derivatives'

    print(f"\n{'='*70}")
    print(f"Phase 0 HRF Loader Test: sub-{subject_id} {roi}")
    print(f"{'='*70}\n")

    try:
        # Test 1: Find directory
        print("Test 1: Finding Phase 0 result directory...")
        result_dir = find_phase0_result_dir(subject_id, roi, derivatives_dir)
        print(f"✓ Found: {result_dir.name}\n")

        # Test 2: Load HRF
        print("Test 2: Loading Phase 0 HRF...")
        roi_hrf, roi_hrf_deriv = load_phase0_hrf(subject_id, roi, derivatives_dir)
        print(f"✓ HRF shape: {roi_hrf.shape}")
        print(f"  HRF peak: delay {np.argmax(roi_hrf)}, value {np.max(roi_hrf):.4f}")
        print(f"  HRF derivative shape: {roi_hrf_deriv.shape}\n")

        # Test 3: Load voxel mask
        print("Test 3: Loading voxel selection mask...")
        selected_mask, r2 = load_phase0_voxel_mask(
            subject_id, roi, derivatives_dir, return_r2=True
        )
        print(f"✓ Total voxels: {len(selected_mask)}")
        print(f"  Selected voxels: {selected_mask.sum()} ({selected_mask.sum()/len(selected_mask)*100:.1f}%)")
        print(f"  Mean R² (selected): {r2[selected_mask].mean():.4f}")
        print(f"  Mean R² (all): {r2.mean():.4f}\n")

        # Test 4: Summary
        print("Test 4: Getting summary...")
        summary = get_phase0_summary(subject_id, roi, derivatives_dir)
        print("✓ Summary:")
        for key, value in summary.items():
            if key == 'result_dir':
                print(f"  {key}: .../{Path(value).name}")
            else:
                print(f"  {key}: {value}")

        print(f"\n{'='*70}")
        print("All tests passed! ✓")
        print(f"{'='*70}\n")

    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
