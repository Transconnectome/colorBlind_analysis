"""
Find common voxels using actual grid coordinates, not relative indices.

CRITICAL FIX: voxel_indices from ANOVA selection are RELATIVE positions
within each subject's ROI mask, NOT absolute grid coordinates!

We need to map these back to actual 3D grid positions.
"""

import numpy as np
import nibabel as nib
from pathlib import Path
import json


def load_roi_mask_and_get_grid_coords(subject, roi, dataset="method3_header_mi"):
    """
    Load ROI mask and get grid coordinates of all voxels in the mask.

    Returns
    -------
    grid_coords : np.ndarray, shape (n_voxels_in_mask, 3)
        Grid coordinates (i, j, k) of all voxels in ROI mask
    mask_img : nibabel.Nifti1Image
        ROI mask image
    """
    # Path to ROI mask on local machine
    # Assuming masks are downloaded from server
    roi_dir = Path(f"/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_data/rois/sub-{subject}")

    # Try different possible filenames
    possible_files = [
        roi_dir / f"sub-{subject}_{roi}_mask.nii.gz",
        roi_dir / f"{roi}_mask.nii.gz",
        roi_dir / f"sub-{subject}_{roi}.nii.gz",
    ]

    mask_path = None
    for path in possible_files:
        if path.exists():
            mask_path = path
            break

    if mask_path is None:
        raise FileNotFoundError(f"ROI mask not found for sub-{subject}/{roi}")

    # Load mask
    mask_img = nib.load(mask_path)
    mask_data = mask_img.get_fdata()

    # Get grid coordinates of all voxels in mask
    grid_coords = np.array(np.where(mask_data > 0)).T  # (n_voxels, 3)

    return grid_coords, mask_img


def map_relative_to_absolute_coords(voxel_indices, grid_coords):
    """
    Map relative indices (within mask) to absolute grid coordinates.

    Parameters
    ----------
    voxel_indices : np.ndarray, shape (n_selected,)
        Relative indices within ROI mask (from ANOVA selection)
    grid_coords : np.ndarray, shape (n_voxels_in_mask, 3)
        Grid coordinates of all voxels in mask

    Returns
    -------
    selected_coords : np.ndarray, shape (n_selected, 3)
        Absolute grid coordinates of selected voxels
    """
    # voxel_indices are positions in the flattened mask
    # grid_coords[voxel_indices] gives the actual grid positions
    selected_coords = grid_coords[voxel_indices]

    return selected_coords


def find_common_voxels_by_coords(input_dir, roi, subjects):
    """
    Find common voxels using actual grid coordinates.

    Returns
    -------
    common_coords : set of tuples
        Set of (i, j, k) grid coordinates that are common across all subjects
    subject_coord_maps : dict
        Mapping from subject to their selected voxel coordinates
    """
    print(f"\nFinding common voxels for {roi} using GRID COORDINATES:")

    subject_coord_maps = {}

    for subject in subjects:
        try:
            # Load ANOVA-selected voxel indices (relative)
            subj_roi_dir = input_dir / f"sub-{subject}" / roi
            voxel_indices = np.load(subj_roi_dir / "voxel_indices.npy")

            # Load ROI mask and get all grid coordinates
            grid_coords, mask_img = load_roi_mask_and_get_grid_coords(subject, roi)

            # Map relative indices to absolute coordinates
            selected_coords = map_relative_to_absolute_coords(voxel_indices, grid_coords)

            # Convert to set of tuples for intersection
            coord_set = set(map(tuple, selected_coords))
            subject_coord_maps[subject] = coord_set

            print(f"  sub-{subject}: {len(voxel_indices)} voxels")
            print(f"    Grid coord range: i=[{selected_coords[:,0].min():.0f},{selected_coords[:,0].max():.0f}], "
                  f"j=[{selected_coords[:,1].min():.0f},{selected_coords[:,1].max():.0f}], "
                  f"k=[{selected_coords[:,2].min():.0f},{selected_coords[:,2].max():.0f}]")

        except Exception as e:
            print(f"  Warning: Failed to process sub-{subject}: {e}")

    if len(subject_coord_maps) < 2:
        print("  Error: Need at least 2 subjects")
        return None, None

    # Compute intersection of coordinates
    subjects_list = sorted(subject_coord_maps.keys())
    common_coords = subject_coord_maps[subjects_list[0]]

    for subject in subjects_list[1:]:
        common_coords = common_coords & subject_coord_maps[subject]

    print(f"\n  Common voxels (by grid coordinates): {len(common_coords)}")

    if len(common_coords) > 0:
        common_array = np.array(list(common_coords))
        print(f"  Common coord range: i=[{common_array[:,0].min():.0f},{common_array[:,0].max():.0f}], "
              f"j=[{common_array[:,1].min():.0f},{common_array[:,1].max():.0f}], "
              f"k=[{common_array[:,2].min():.0f},{common_array[:,2].max():.0f}]")

    return common_coords, subject_coord_maps


def test_with_example():
    """
    Test with a small example to understand the issue.
    """
    print("="*80)
    print("EXAMPLE: Why relative indices don't work")
    print("="*80)

    print("\nSubject 1:")
    print("  ROI mask: [T, F, T, T, F, T, F, F, T, T]  (6 True voxels)")
    print("  Grid positions of True: [0, 2, 3, 5, 8, 9]")
    print("  Relative indices (ANOVA selection): [0, 2, 4]  (select 3 voxels)")
    print("  → Actual grid positions: [0, 3, 8]")

    print("\nSubject 2:")
    print("  ROI mask: [F, T, F, T, T, F, T, T, F, T]  (6 True voxels)")
    print("  Grid positions of True: [1, 3, 4, 6, 7, 9]")
    print("  Relative indices (ANOVA selection): [0, 2, 4]  (select 3 voxels)")
    print("  → Actual grid positions: [1, 4, 7]")

    print("\nCurrent WRONG method (comparing relative indices):")
    print("  Subject 1 indices: {0, 2, 4}")
    print("  Subject 2 indices: {0, 2, 4}")
    print("  Intersection: {0, 2, 4}  ✓ Perfect overlap!")
    print("  BUT these refer to DIFFERENT grid positions!")

    print("\nCORRECT method (comparing grid coordinates):")
    print("  Subject 1 grid coords: {0, 3, 8}")
    print("  Subject 2 grid coords: {1, 4, 7}")
    print("  Intersection: {}  ← NO common voxels!")
    print("  This is the TRUE overlap!")

    print("\n" + "="*80)


def main():
    # First show the example
    test_with_example()

    # Now test with actual data
    input_dir = Path("results/baseline_anova_selected")

    hc_subjects = ['01', '02', '03', '04', '05', '06', '07']
    cvd_subjects = ['08', '09', '10']

    print("\n" + "="*80)
    print("Testing with actual data")
    print("="*80)

    # Note: This will fail if ROI masks are not available locally
    # We need to download them from server first

    print("\n⚠️  To run this analysis, we need ROI masks from the server:")
    print("  Server path: /scratch/connectome/haba6030/colorBlind/derivatives/rois/")
    print("  Local path:  ~/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_data/rois/")
    print("\n  Please run:")
    print("  scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/rois/ \\")
    print("      ~/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_data/")


if __name__ == '__main__':
    main()
