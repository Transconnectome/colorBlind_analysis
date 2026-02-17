#!/usr/bin/env python3
"""
Brain Mapping Utilities for Procrustes Visualization

Purpose: Map voxel activation values to 3D brain volumes for spatial visualization
Key Feature: Coordinate-based voxel matching (NOT index-based) to ensure spatial correspondence

Usage:
    mapper = VoxelToBrainMapper('V2', '/path/to/mask.nii.gz')
    brain_volume = mapper.create_brain_volume(voxel_values, voxel_indices)

    # Coordinate-based matching
    hc_indices, cvd_indices, coords = match_voxels_by_coordinates(
        hc_mapper, hc_mask, cvd_mapper, cvd_mask
    )
"""

import numpy as np
import nibabel as nib
from scipy.spatial import cKDTree
from pathlib import Path


class VoxelToBrainMapper:
    """Maps voxel values to 3D MNI brain volumes."""

    def __init__(self, roi_name, mask_path, threshold=0.25):
        """
        Initialize brain mapper with ROI mask.

        Parameters
        ----------
        roi_name : str
            ROI name (V1, V2, V3, V4)
        mask_path : str or Path
            Path to ROI mask file (.nii.gz)
        threshold : float
            Probability threshold for binary mask (default: 0.25)
        """
        self.roi_name = roi_name
        self.mask_path = Path(mask_path)
        self.threshold = threshold

        if not self.mask_path.exists():
            raise FileNotFoundError(f"Mask not found: {self.mask_path}")

        # Load mask
        self.mask_img = nib.load(self.mask_path)
        self.mask_data = self.mask_img.get_fdata()
        self.affine = self.mask_img.affine
        self.shape = self.mask_data.shape

        # Create binary mask
        self.binary_mask = self.mask_data > threshold

        # Get active voxel positions (i, j, k)
        self.active_voxels_ijk = np.argwhere(self.binary_mask)
        self.n_voxels = len(self.active_voxels_ijk)

        print(f"Loaded {roi_name} mask: {self.n_voxels} voxels > {threshold}")
        print(f"  Shape: {self.shape}")
        print(f"  Affine: {self.affine[0, 0]:.1f}mm resolution")

    def create_brain_volume(self, voxel_values, voxel_indices=None):
        """
        Map voxel values to 3D MNI brain volume.

        Parameters
        ----------
        voxel_values : np.ndarray
            1D array of values per voxel (n_voxels,)
        voxel_indices : np.ndarray, optional
            Indices into active voxels (if subset used)
            If None, assumes voxel_values correspond to first N active voxels

        Returns
        -------
        brain_img : nib.Nifti1Image
            3D brain volume with values mapped to voxel positions
        """
        # Initialize volume with NaN (for transparency in visualization)
        volume = np.full(self.shape, np.nan, dtype=np.float32)

        # Get positions to fill
        if voxel_indices is None:
            # Assume voxel_values correspond to first N active voxels
            n_values = len(voxel_values)
            if n_values > self.n_voxels:
                raise ValueError(f"Too many voxel values ({n_values}) for mask ({self.n_voxels})")
            positions = self.active_voxels_ijk[:n_values]
        else:
            positions = self.active_voxels_ijk[voxel_indices]

        # Fill volume at positions
        for idx, (i, j, k) in enumerate(positions):
            volume[i, j, k] = voxel_values[idx]

        # Create Nifti image
        brain_img = nib.Nifti1Image(volume, self.affine)

        return brain_img

    def get_mni_coordinates(self, voxel_indices=None):
        """
        Extract MNI (x, y, z) coordinates for voxels.

        Parameters
        ----------
        voxel_indices : np.ndarray, optional
            Indices into active voxels (if subset used)
            If None, returns all active voxels

        Returns
        -------
        mni_coords : np.ndarray
            (n_voxels, 3) array of MNI coordinates
        """
        if voxel_indices is None:
            ijk = self.active_voxels_ijk
        else:
            ijk = self.active_voxels_ijk[voxel_indices]

        # Convert to homogeneous coordinates
        ijk_homog = np.hstack([ijk, np.ones((len(ijk), 1))])

        # Apply affine transformation
        mni_homog = (self.affine @ ijk_homog.T).T

        # Drop homogeneous coordinate
        mni_coords = mni_homog[:, :3]

        return mni_coords


def load_bilateral_mask(roi_name, atlas_dir, threshold=0.25):
    """
    Load and combine left and right hemisphere masks.

    Parameters
    ----------
    roi_name : str
        ROI name (V1, V2, V3, V4)
    atlas_dir : str or Path
        Path to Wang atlas directory
    threshold : float
        Probability threshold for binary mask

    Returns
    -------
    mapper : VoxelToBrainMapper
        Mapper with bilateral mask
    """
    atlas_dir = Path(atlas_dir)

    # ROI number mapping
    roi_numbers = {'V1': 'roi1', 'V2': 'roi2', 'V3': 'roi3', 'V4': 'roi13'}
    roi_num = roi_numbers.get(roi_name)

    if roi_num is None:
        raise ValueError(f"Unknown ROI: {roi_name}. Choose from {list(roi_numbers.keys())}")

    # Load left and right hemisphere masks
    lh_path = atlas_dir / f'perc_VTPM_vol_{roi_num}_lh.nii.gz'
    rh_path = atlas_dir / f'perc_VTPM_vol_{roi_num}_rh.nii.gz'

    if not lh_path.exists() or not rh_path.exists():
        raise FileNotFoundError(f"Hemisphere masks not found for {roi_name}")

    lh_img = nib.load(lh_path)
    rh_img = nib.load(rh_path)

    # Combine masks (element-wise maximum)
    combined_data = np.maximum(lh_img.get_fdata(), rh_img.get_fdata())

    # Create combined image
    combined_img = nib.Nifti1Image(combined_data, lh_img.affine)

    # Save to temporary file (for consistency)
    temp_path = atlas_dir / f'temp_{roi_num}_bilateral.nii.gz'
    nib.save(combined_img, temp_path)

    # Create mapper
    mapper = VoxelToBrainMapper(roi_name, temp_path, threshold=threshold)

    return mapper


def match_voxels_by_coordinates(hc_mapper, cvd_mapper, tolerance_mm=0.5):
    """
    Find coordinate-based intersection between HC and CVD voxel sets.

    CRITICAL: This ensures we compare SAME spatial locations, not just indices.
    Different subjects may have slightly different n_voxels, so index-based
    matching (using min(n_hc, n_cvd)) would compare DIFFERENT brain locations.

    Parameters
    ----------
    hc_mapper : VoxelToBrainMapper
        Mapper for HC reference subject
    cvd_mapper : VoxelToBrainMapper
        Mapper for CVD subject
    tolerance_mm : float
        Spatial tolerance for coordinate matching (default: 0.5mm)

    Returns
    -------
    hc_indices : np.ndarray
        Indices into HC voxel array (matched subset)
    cvd_indices : np.ndarray
        Indices into CVD voxel array (matched subset)
    common_coords : np.ndarray
        MNI coordinates of matched voxels (n_matched, 3)
    """
    print(f"\nMatching voxels by spatial coordinates...")
    print(f"  HC voxels: {hc_mapper.n_voxels}")
    print(f"  CVD voxels: {cvd_mapper.n_voxels}")
    print(f"  Tolerance: {tolerance_mm}mm")

    # Get MNI coordinates for all active voxels
    hc_mni = hc_mapper.get_mni_coordinates()
    cvd_mni = cvd_mapper.get_mni_coordinates()

    # Build KD-tree for efficient spatial search
    tree_cvd = cKDTree(cvd_mni)

    # For each HC voxel, find nearest CVD voxel
    distances, cvd_nearest_idx = tree_cvd.query(hc_mni)

    # Keep only matches within tolerance
    valid_matches = distances < tolerance_mm
    hc_indices = np.where(valid_matches)[0]
    cvd_indices = cvd_nearest_idx[valid_matches]

    # Get common coordinates (use HC as reference)
    common_coords = hc_mni[hc_indices]

    n_matched = len(hc_indices)
    match_rate_hc = 100 * n_matched / hc_mapper.n_voxels
    match_rate_cvd = 100 * n_matched / cvd_mapper.n_voxels

    print(f"  Matched voxels: {n_matched}")
    print(f"  Match rate (HC): {match_rate_hc:.1f}%")
    print(f"  Match rate (CVD): {match_rate_cvd:.1f}%")

    if n_matched == 0:
        raise ValueError("No matching voxels found! Check masks and tolerance.")

    if match_rate_hc < 50 or match_rate_cvd < 50:
        print("  WARNING: Low match rate - check mask alignment")

    return hc_indices, cvd_indices, common_coords


def validate_coordinate_matching(hc_coords, cvd_coords, matched_hc_indices, matched_cvd_indices):
    """
    Validate that matched voxels correspond to same spatial locations.

    Parameters
    ----------
    hc_coords : np.ndarray
        All HC MNI coordinates (n_hc, 3)
    cvd_coords : np.ndarray
        All CVD MNI coordinates (n_cvd, 3)
    matched_hc_indices : np.ndarray
        HC indices that were matched
    matched_cvd_indices : np.ndarray
        CVD indices that were matched

    Returns
    -------
    validation : dict
        Validation metrics
    """
    # Extract matched coordinates
    hc_matched = hc_coords[matched_hc_indices]
    cvd_matched = cvd_coords[matched_cvd_indices]

    # Compute spatial displacement
    displacements = np.linalg.norm(hc_matched - cvd_matched, axis=1)

    validation = {
        'mean_displacement_mm': float(np.mean(displacements)),
        'median_displacement_mm': float(np.median(displacements)),
        'max_displacement_mm': float(np.max(displacements)),
        'std_displacement_mm': float(np.std(displacements)),
        'within_1mm': float(np.mean(displacements < 1.0) * 100),
        'within_2mm': float(np.mean(displacements < 2.0) * 100)
    }

    print("\nCoordinate matching validation:")
    print(f"  Mean displacement: {validation['mean_displacement_mm']:.2f}mm")
    print(f"  Max displacement: {validation['max_displacement_mm']:.2f}mm")
    print(f"  Within 1mm: {validation['within_1mm']:.1f}%")
    print(f"  Within 2mm: {validation['within_2mm']:.1f}%")

    return validation


if __name__ == '__main__':
    """Quick test of brain mapping utilities."""

    # Test paths (adjust to your setup)
    atlas_dir = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/ProbAtlas_v4/subj_vol_all')

    print("Testing VoxelToBrainMapper...")
    print("="*80)

    # Test single hemisphere
    v2_lh_path = atlas_dir / 'perc_VTPM_vol_roi2_lh.nii.gz'
    if v2_lh_path.exists():
        mapper = VoxelToBrainMapper('V2', v2_lh_path)

        # Test volume creation
        test_values = np.random.rand(mapper.n_voxels)
        brain_img = mapper.create_brain_volume(test_values)
        print(f"\nCreated brain volume: {brain_img.shape}")

        # Test MNI coordinates
        mni = mapper.get_mni_coordinates()
        print(f"MNI coordinates: {mni.shape}")
        print(f"  Range X: [{mni[:, 0].min():.1f}, {mni[:, 0].max():.1f}]")
        print(f"  Range Y: [{mni[:, 1].min():.1f}, {mni[:, 1].max():.1f}]")
        print(f"  Range Z: [{mni[:, 2].min():.1f}, {mni[:, 2].max():.1f}]")

    # Test bilateral loading
    print("\n" + "="*80)
    print("Testing bilateral mask loading...")
    try:
        bilateral_mapper = load_bilateral_mask('V2', atlas_dir)
        print(f"✓ Bilateral mask created: {bilateral_mapper.n_voxels} voxels")
    except Exception as e:
        print(f"✗ Bilateral mask failed: {e}")

    print("\n" + "="*80)
    print("✓ Brain mapping utilities test complete")
