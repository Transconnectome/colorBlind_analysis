"""
Save grid coordinates for ANOVA-selected voxels.

This script:
1. Loads the ROI mask used during FIR reconstruction
2. Extracts grid coordinates for the selected voxels
3. Saves both the mask and coordinates to results directory

This enables proper voxel correspondence checking across subjects.
"""

import numpy as np
import nibabel as nib
from pathlib import Path
import json
import sys


def find_roi_mask(subject, roi, dataset="method3_header_mi"):
    """
    Find ROI mask file for a subject.

    The mask could be in several locations depending on how it was created.
    """
    # Possible locations (server paths)
    possible_paths = [
        # Native space ROIs
        Path(f"/scratch/connectome/haba6030/colorBlind/derivatives/rois/sub-{subject}/native/{roi}_mask.nii.gz"),
        Path(f"/scratch/connectome/haba6030/colorBlind/derivatives/rois/sub-{subject}/{roi}.nii.gz"),

        # MNI space ROIs
        Path(f"/scratch/connectome/haba6030/colorBlind/derivatives/rois/sub-{subject}/MNI/{roi}_mask.nii.gz"),

        # FreeSurfer-based ROIs
        Path(f"/scratch/connectome/haba6030/colorBlind/derivatives/freesurfer/sub-{subject}/mri/ROIs/{roi}.nii.gz"),
    ]

    for path in possible_paths:
        if path.exists():
            print(f"    Found mask: {path}")
            return path

    return None


def load_roi_mask_and_coords(mask_path):
    """
    Load ROI mask and extract grid coordinates of all voxels.

    Returns
    -------
    mask_img : nibabel image
    grid_coords : np.ndarray, shape (n_voxels, 3)
        Grid coordinates (i, j, k) of all voxels where mask > 0
    affine : np.ndarray
        Affine transformation matrix
    """
    mask_img = nib.load(mask_path)
    mask_data = mask_img.get_fdata()

    # Get grid coordinates of all non-zero voxels
    indices = np.where(mask_data > 0)
    grid_coords = np.array(indices).T  # Shape: (n_voxels, 3)

    return mask_img, grid_coords, mask_img.affine


def save_selected_voxel_info(results_dir, subject, roi, voxel_indices, mask_img, all_grid_coords):
    """
    Save mask, grid coordinates, and selected voxel information.

    Parameters
    ----------
    results_dir : Path
        Base results directory (e.g., results/baseline_anova_selected)
    subject : str
        Subject ID
    roi : str
        ROI name
    voxel_indices : np.ndarray
        Relative indices of selected voxels (within mask)
    mask_img : nibabel image
        ROI mask image
    all_grid_coords : np.ndarray, shape (n_voxels_in_mask, 3)
        Grid coordinates of all voxels in mask
    """
    output_dir = results_dir / f"sub-{subject}" / roi
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Save ROI mask
    mask_output = output_dir / "roi_mask.nii.gz"
    nib.save(mask_img, mask_output)
    print(f"    Saved mask: {mask_output}")

    # 2. Get grid coordinates of selected voxels
    selected_grid_coords = all_grid_coords[voxel_indices]

    # 3. Save grid coordinates (both all and selected)
    np.save(output_dir / "all_grid_coords.npy", all_grid_coords)
    np.save(output_dir / "selected_grid_coords.npy", selected_grid_coords)
    print(f"    Saved coordinates: selected {len(selected_grid_coords)} out of {len(all_grid_coords)} voxels")

    # 4. Save metadata
    metadata = {
        'subject': subject,
        'roi': roi,
        'n_voxels_in_mask': len(all_grid_coords),
        'n_voxels_selected': len(selected_grid_coords),
        'mask_shape': list(mask_img.shape),
        'affine': mask_img.affine.tolist(),
        'selected_indices_relative': voxel_indices.tolist(),
        'grid_coord_ranges': {
            'i': [int(all_grid_coords[:, 0].min()), int(all_grid_coords[:, 0].max())],
            'j': [int(all_grid_coords[:, 1].min()), int(all_grid_coords[:, 1].max())],
            'k': [int(all_grid_coords[:, 2].min()), int(all_grid_coords[:, 2].max())]
        },
        'selected_coord_ranges': {
            'i': [int(selected_grid_coords[:, 0].min()), int(selected_grid_coords[:, 0].max())],
            'j': [int(selected_grid_coords[:, 1].min()), int(selected_grid_coords[:, 1].max())],
            'k': [int(selected_grid_coords[:, 2].min()), int(selected_grid_coords[:, 2].max())]
        }
    }

    with open(output_dir / "voxel_grid_info.json", 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"    Grid coord ranges:")
    print(f"      All:      i={metadata['grid_coord_ranges']['i']}, j={metadata['grid_coord_ranges']['j']}, k={metadata['grid_coord_ranges']['k']}")
    print(f"      Selected: i={metadata['selected_coord_ranges']['i']}, j={metadata['selected_coord_ranges']['j']}, k={metadata['selected_coord_ranges']['k']}")


def process_all_subjects(results_dir, subjects, rois):
    """
    Process all subject-ROI pairs and save grid coordinate information.
    """
    print("="*80)
    print("Saving Grid Coordinates for ANOVA-Selected Voxels")
    print("="*80)

    success_count = 0
    fail_count = 0

    for subject in subjects:
        for roi in rois:
            print(f"\nProcessing sub-{subject}/{roi}:")

            # Check if ANOVA selection results exist
            subj_roi_dir = results_dir / f"sub-{subject}" / roi
            voxel_idx_path = subj_roi_dir / "voxel_indices.npy"

            if not voxel_idx_path.exists():
                print(f"  ⚠️  ANOVA results not found, skipping")
                fail_count += 1
                continue

            # Load selected voxel indices
            voxel_indices = np.load(voxel_idx_path)

            # Find and load ROI mask
            mask_path = find_roi_mask(subject, roi)

            if mask_path is None:
                print(f"  ❌ ROI mask not found, skipping")
                fail_count += 1
                continue

            try:
                # Load mask and get coordinates
                mask_img, all_grid_coords, affine = load_roi_mask_and_coords(mask_path)

                # Save everything
                save_selected_voxel_info(
                    results_dir, subject, roi, voxel_indices, mask_img, all_grid_coords
                )

                success_count += 1

            except Exception as e:
                print(f"  ❌ Error: {e}")
                fail_count += 1

    print("\n" + "="*80)
    print(f"Summary: {success_count} successful, {fail_count} failed")
    print("="*80)


def main():
    # Configuration
    results_dir = Path("/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/results/baseline_anova_selected")

    subjects = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10']
    rois = ['V1', 'V2', 'V3', 'hV4']

    # Check if we're on the server
    if not results_dir.exists():
        print("❌ Results directory not found!")
        print(f"   Expected: {results_dir}")
        print("\n   This script should be run on the server (node2).")
        print("   Please run:")
        print("   ssh haba6030@node2")
        print("   cd /scratch/connectome/haba6030/colorBlind")
        print("   conda activate nilearn")
        print(f"   python analysis/phase1_preprocess_decoding/scripts/save_voxel_grid_coords.py")
        return

    # Process all subjects
    process_all_subjects(results_dir, subjects, rois)


if __name__ == '__main__':
    main()
