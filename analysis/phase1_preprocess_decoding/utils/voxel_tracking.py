"""
Voxel coordinate extraction and correspondence validation.

Provides functions to extract MNI coordinates for selected voxels and
validate that voxel indices correspond to identical physical locations
across runs.
"""

import numpy as np


def extract_voxel_coordinates(mask_img, voxel_indices):
    """
    Extract MNI coordinates for selected voxels.

    Parameters
    ----------
    mask_img : NiftiImage
        ROI mask (defines affine transformation)
    voxel_indices : np.ndarray
        Linear indices of selected voxels in the flattened mask

    Returns
    -------
    coords : np.ndarray, shape (n_voxels, 3)
        MNI (x, y, z) coordinates for each voxel
    grid_indices : np.ndarray, shape (n_voxels,)
        Linear indices in 3D grid (same as input for verification)

    Examples
    --------
    >>> mask = nib.load('V1_mask.nii.gz')
    >>> selected_voxels = np.array([10, 25, 42, ...])  # From voxel selection
    >>> coords, grid_idx = extract_voxel_coordinates(mask, selected_voxels)
    >>> print(f"First voxel MNI: {coords[0]}")
    First voxel MNI: [-12.5  -95.3   8.2]
    """
    affine = mask_img.affine
    mask_data = mask_img.get_fdata()
    shape = mask_data.shape

    # Convert linear indices to 3D subscripts
    i, j, k = np.unravel_index(voxel_indices, shape)

    # Convert to MNI coordinates using affine transformation
    # Affine maps from voxel (i,j,k) to world (x,y,z):
    # [x, y, z, 1]^T = affine @ [i, j, k, 1]^T
    voxel_coords_homogeneous = np.vstack([i, j, k, np.ones(len(i))]).T  # (n_voxels, 4)
    mni_coords_homogeneous = (affine @ voxel_coords_homogeneous.T).T  # (n_voxels, 4)
    mni_coords = mni_coords_homogeneous[:, :3]  # Drop homogeneous coordinate

    return mni_coords, voxel_indices


def validate_voxel_correspondence(coords_per_run, tolerance=1e-6):
    """
    Check if voxels are exactly aligned across runs.

    If grid resampling was applied correctly, all runs should have
    identical voxel coordinates (variance ~ 0).

    Parameters
    ----------
    coords_per_run : list of np.ndarray
        List of coordinate arrays, one per run
        Each array: shape (n_voxels, 3)
    tolerance : float, default=1e-6
        Tolerance for considering coordinates "exactly aligned"

    Returns
    -------
    mean_variance : float
        Mean coordinate variance across all voxels and dimensions
        (Should be ~0 if grid-resampled)
    max_variance : float
        Maximum coordinate variance across any voxel/dimension
    is_aligned : bool
        True if max_variance < tolerance (exactly aligned)

    Examples
    --------
    >>> coords_run1 = np.array([[-12.5, -95.3, 8.2], ...])
    >>> coords_run2 = np.array([[-12.5, -95.3, 8.2], ...])  # Same if resampled
    >>> coords_run3 = np.array([[-12.6, -95.1, 8.3], ...])  # Different if not
    >>> mean_var, max_var, aligned = validate_voxel_correspondence([coords_run1, coords_run2, coords_run3])
    >>> print(f"Max variance: {max_var:.2e}, Aligned: {aligned}")
    Max variance: 2.34e-02, Aligned: False
    """
    if len(coords_per_run) < 2:
        # Single run: trivially aligned
        return 0.0, 0.0, True

    # Stack coordinates: (n_runs, n_voxels, 3)
    coords_stack = np.array(coords_per_run)

    # Variance across runs for each voxel and dimension
    coord_variance = np.var(coords_stack, axis=0)  # (n_voxels, 3)

    mean_var = np.mean(coord_variance)
    max_var = np.max(coord_variance)

    is_aligned = (max_var < tolerance)

    return mean_var, max_var, is_aligned


def compute_voxel_displacement(coords_run1, coords_run2):
    """
    Compute displacement between corresponding voxels in two runs.

    Useful for diagnosing voxel mismatch when grid resampling is not applied.

    Parameters
    ----------
    coords_run1 : np.ndarray, shape (n_voxels, 3)
        MNI coordinates for run 1
    coords_run2 : np.ndarray, shape (n_voxels, 3)
        MNI coordinates for run 2 (must have same n_voxels)

    Returns
    -------
    displacements : np.ndarray, shape (n_voxels,)
        Euclidean distance between corresponding voxels (mm)
    stats : dict
        Displacement statistics:
        - mean: Mean displacement
        - median: Median displacement
        - max: Maximum displacement
        - std: Standard deviation

    Examples
    --------
    >>> displacements, stats = compute_voxel_displacement(coords_run1, coords_run2)
    >>> print(f"Mean displacement: {stats['mean']:.2f} mm")
    Mean displacement: 1.24 mm
    """
    if coords_run1.shape != coords_run2.shape:
        raise ValueError(f"Shape mismatch: {coords_run1.shape} != {coords_run2.shape}")

    # Euclidean distance for each voxel
    displacements = np.linalg.norm(coords_run1 - coords_run2, axis=1)

    stats = {
        'mean': float(np.mean(displacements)),
        'median': float(np.median(displacements)),
        'max': float(np.max(displacements)),
        'std': float(np.std(displacements))
    }

    return displacements, stats


def extract_roi_center(mask_img):
    """
    Extract center of mass of ROI in MNI space.

    Useful for validating that ROI location is consistent across runs.

    Parameters
    ----------
    mask_img : NiftiImage
        ROI mask

    Returns
    -------
    center_mni : np.ndarray, shape (3,)
        MNI coordinates of ROI center of mass
    """
    from scipy import ndimage

    mask_data = mask_img.get_fdata()
    affine = mask_img.affine

    # Compute center of mass in voxel coordinates
    center_voxel = ndimage.center_of_mass(mask_data)

    # Convert to MNI
    center_voxel_homogeneous = np.array([*center_voxel, 1])
    center_mni_homogeneous = affine @ center_voxel_homogeneous
    center_mni = center_mni_homogeneous[:3]

    return center_mni
