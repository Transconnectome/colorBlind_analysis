#!/usr/bin/env python3
"""
Prepare surface-projected data for MATLAB interactive viewer.

Projects volume data (ROI masks and functional activation) to fsaverage5
surface and exports as .mat files for MATLAB.

Usage:
    python prepare_matlab_surface_data.py --subject sub-08 --roi V2
    python prepare_matlab_surface_data.py --all-cvd --roi V2
    python prepare_matlab_surface_data.py --export-surfaces
"""

import numpy as np
from scipy.io import savemat
from nilearn import surface, datasets
import nibabel as nib
from pathlib import Path
import argparse
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from phase2_SRM_across_between.brain_mapping_utils import VoxelToBrainMapper

# Configuration
BASE_DIR = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis')
C010_DIR = BASE_DIR / 'analysis/phase1_preprocess_decoding/results/full_dataset_C010'
MASK_DIR = BASE_DIR / 'analysis/roi_masks/method3_header_mi/method3_header_mi'
OUTPUT_DIR = BASE_DIR / 'analysis/matlab_viewers'

ROI_DIR_MAP = {'V1': 'V1', 'V2': 'V2', 'V3': 'V3', 'hV4': 'V4'}
CVD_SUBJECTS = ['sub-08', 'sub-09', 'sub-10']


def export_fsaverage_surfaces():
    """
    Export fsaverage5 surfaces as GIFTI for MATLAB.

    Downloads fsaverage5 and converts to GIFTI format if needed.
    """
    print("\n" + "="*70)
    print("Exporting fsaverage5 surfaces to GIFTI")
    print("="*70 + "\n")

    # Fetch fsaverage5
    print("Downloading fsaverage5 surfaces...")
    fsaverage = datasets.fetch_surf_fsaverage('fsaverage5')

    # Output directory
    surf_dir = OUTPUT_DIR / 'freesurfer_surfaces' / 'fsaverage5'
    surf_dir.mkdir(parents=True, exist_ok=True)

    # Export left hemisphere inflated surface
    print("\nExporting left hemisphere inflated surface...")

    # Load surface
    coords, faces = surface.load_surf_mesh(fsaverage['infl_left'])

    # Create GIFTI
    # Note: nilearn surfaces are already in memory, we need to save them
    # Unfortunately, nilearn doesn't directly support GIFTI export
    # We'll save as FreeSurfer format and provide conversion instructions

    print("\nWARNING: Direct GIFTI export not implemented.")
    print("To use MATLAB viewer, you have two options:")
    print("\n1. Use FreeSurfer's mris_convert:")
    print(f"   mris_convert {fsaverage['infl_left']} {surf_dir}/lh.inflated.gii")
    print("\n2. Use nibabel to create GIFTI manually (see code comments)")

    # Alternative: Create basic .mat file with surface data
    surf_mat_path = surf_dir / 'lh_inflated.mat'
    savemat(surf_mat_path, {
        'vertices': coords,
        'faces': faces + 1  # MATLAB uses 1-based indexing
    })
    print(f"\nAlternative: Saved surface as .mat file:")
    print(f"  {surf_mat_path}")
    print(f"  Load in MATLAB with: load('{surf_mat_path}')")

    return surf_dir


def prepare_subject_surface_data(subject_id, roi):
    """
    Project subject's ROI mask and functional data to surface.

    Parameters
    ----------
    subject_id : str
        Subject ID (e.g., 'sub-08')
    roi : str
        ROI name (V1, V2, V3, hV4)

    Returns
    -------
    output_files : dict
        Paths to created .mat files
    """
    print(f"\n{'='*70}")
    print(f"Preparing surface data: {subject_id} {roi}")
    print(f"{'='*70}\n")

    roi_dir = ROI_DIR_MAP[roi]

    # -------------------------------------------------------------------------
    # Load volume data
    # -------------------------------------------------------------------------
    print("Loading volume data...")

    # Load mask (use roi name as-is, not roi_dir)
    mask_file = f'{roi}_mask_thr50_intnearest_binTrue_maskfunc_gmTrue_subjFalse.nii.gz'
    mask_path = MASK_DIR / subject_id / 'roi_pipeline' / mask_file

    if not mask_path.exists():
        raise FileNotFoundError(f"Mask not found: {mask_path}")

    mask_img = nib.load(mask_path)
    print(f"  Mask: {mask_path.name}")

    # Load amplitudes and compute RMS
    amps_path = C010_DIR / subject_id / roi_dir / 'amplitudes_procrustes.npy'
    if not amps_path.exists():
        raise FileNotFoundError(f"Amplitudes not found: {amps_path}")

    amps = np.load(amps_path)
    amps_mean = amps.mean(axis=0)  # (8, n_voxels)
    rms = np.sqrt(np.mean(amps_mean**2, axis=0))  # (n_voxels,)
    print(f"  Amplitudes: shape {amps.shape}, RMS range [{rms.min():.3f}, {rms.max():.3f}]")

    # Create brain volume with RMS activation
    mapper = VoxelToBrainMapper(roi, str(mask_path))
    rms_img = mapper.create_brain_volume(rms)

    # -------------------------------------------------------------------------
    # Fetch fsaverage surface
    # -------------------------------------------------------------------------
    print("\nFetching fsaverage5 surfaces...")
    fsaverage = datasets.fetch_surf_fsaverage('fsaverage5')

    # -------------------------------------------------------------------------
    # Project to surface (left hemisphere)
    # -------------------------------------------------------------------------
    print("Projecting data to left hemisphere surface...")

    # Project ROI mask
    roi_label_lh = surface.vol_to_surf(
        mask_img,
        fsaverage['pial_left'],
        radius=3.0,
        interpolation='nearest',
        kind='line'
    )
    # Binarize (threshold at 0.5 for probabilistic masks)
    roi_label_lh = (roi_label_lh > 0.5).astype(np.int32)
    print(f"  ROI vertices: {roi_label_lh.sum()} ({100*roi_label_lh.mean():.1f}%)")

    # Project RMS activation
    rms_lh = surface.vol_to_surf(
        rms_img,
        fsaverage['pial_left'],
        radius=3.0,
        interpolation='linear',
        kind='line'
    )
    # Replace NaN with 0 (areas outside brain)
    rms_lh = np.nan_to_num(rms_lh, nan=0.0)
    print(f"  RMS activation: range [{rms_lh.min():.3f}, {rms_lh.max():.3f}]")

    # -------------------------------------------------------------------------
    # Save as .mat files for MATLAB
    # -------------------------------------------------------------------------
    print("\nSaving .mat files...")

    # Create output directories
    label_dir = OUTPUT_DIR / 'surface_labels' / subject_id
    data_dir = OUTPUT_DIR / 'surface_data' / subject_id
    label_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    # Save ROI label
    label_path = label_dir / f'{roi}_lh_label.mat'
    savemat(label_path, {'roi_label': roi_label_lh})
    print(f"  ROI label: {label_path}")

    # Save functional data
    data_path = data_dir / f'{roi}_rms.mat'
    savemat(data_path, {'rms_activation': rms_lh})
    print(f"  RMS data: {data_path}")

    print(f"\n{'='*70}")
    print("SUCCESS: Surface data prepared for MATLAB")
    print(f"{'='*70}\n")

    return {
        'roi_label': label_path,
        'rms_data': data_path
    }


# =============================================================================
# CLI Entry Point
# =============================================================================

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Prepare surface data for MATLAB interactive viewer'
    )

    parser.add_argument(
        '--subject',
        type=str,
        help='Subject ID (e.g., sub-08)'
    )
    parser.add_argument(
        '--roi',
        type=str,
        choices=['V1', 'V2', 'V3', 'hV4'],
        help='ROI name'
    )
    parser.add_argument(
        '--all-cvd',
        action='store_true',
        help='Process all CVD subjects (sub-08, sub-09, sub-10)'
    )
    parser.add_argument(
        '--export-surfaces',
        action='store_true',
        help='Export fsaverage5 surfaces to GIFTI'
    )

    args = parser.parse_args()

    # Validate arguments
    if args.export_surfaces:
        export_fsaverage_surfaces()
    elif args.all_cvd:
        if not args.roi:
            parser.error("--roi is required when using --all-cvd")
        for subject in CVD_SUBJECTS:
            try:
                prepare_subject_surface_data(subject, args.roi)
            except Exception as e:
                print(f"\nERROR processing {subject}: {e}\n")
                continue
    elif args.subject and args.roi:
        prepare_subject_surface_data(args.subject, args.roi)
    else:
        parser.error("Specify either (--subject and --roi), --all-cvd, or --export-surfaces")

    print("\nUsage in MATLAB:")
    print("  >> interactive_surface_viewer('sub-08', 'V2')")
