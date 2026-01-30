"""
Grid resampling utilities for ensuring voxel correspondence across runs.

This module provides functions to resample all runs within a subject to a
common reference grid, ensuring that voxel indices correspond to identical
physical brain locations.
"""

import numpy as np
from nilearn import image as nimg


def resample_runs_to_common_grid(
    run_imgs,
    reference_idx=0,
    interpolation='continuous'
):
    """
    Resample all runs to the grid of a reference run.

    This ensures exact voxel correspondence across runs by resampling all
    BOLD images to match the affine transformation and grid shape of the
    reference run.

    Parameters
    ----------
    run_imgs : list of NiftiImage
        List of BOLD images (one per run)
    reference_idx : int, default=0
        Index of the run to use as reference grid (typically run 0)
    interpolation : str, default='continuous'
        Interpolation method for resampling ('continuous', 'linear', or 'nearest')
        Use 'continuous' for BOLD data

    Returns
    -------
    resampled_imgs : list of NiftiImage
        BOLD images resampled to common grid
    reference_affine : np.ndarray, shape (4, 4)
        Common affine transformation matrix
    reference_shape : tuple
        Common 3D grid shape

    Examples
    --------
    >>> run_imgs = [nib.load(f'run{i}_bold.nii.gz') for i in range(6)]
    >>> resampled, affine, shape = resample_runs_to_common_grid(run_imgs)
    >>> # All resampled images now have identical affine and shape
    >>> assert all(np.allclose(img.affine, affine) for img in resampled)
    """
    if not run_imgs:
        raise ValueError("run_imgs cannot be empty")

    if reference_idx < 0 or reference_idx >= len(run_imgs):
        raise ValueError(f"reference_idx {reference_idx} out of range [0, {len(run_imgs)})")

    # Get reference grid properties
    ref_img = run_imgs[reference_idx]
    target_affine = ref_img.affine.copy()
    target_shape = ref_img.shape[:3]

    print(f"  Reference grid (run {reference_idx}):")
    print(f"    Shape: {target_shape}")
    print(f"    Affine diagonal: {np.diag(target_affine)[:3]}")

    resampled_imgs = []

    for i, img in enumerate(run_imgs):
        if i == reference_idx:
            # Reference run: use as-is
            resampled_imgs.append(img)
            print(f"  Run {i}: Using as reference")
        else:
            # Other runs: resample to reference grid
            print(f"  Run {i}: Resampling to reference grid...")

            resampled = nimg.resample_img(
                img,
                target_affine=target_affine,
                target_shape=target_shape,
                interpolation=interpolation,
                force_resample=True
            )

            # Validate exact alignment
            affine_match = np.allclose(resampled.affine, target_affine, atol=1e-6)
            shape_match = resampled.shape[:3] == target_shape

            if not affine_match:
                print(f"    WARNING: Affine mismatch (max diff: {np.max(np.abs(resampled.affine - target_affine))})")
            if not shape_match:
                raise ValueError(f"    ERROR: Shape mismatch {resampled.shape[:3]} != {target_shape}")

            print(f"    Resampled shape: {resampled.shape[:3]}, affine match: {affine_match}")

            resampled_imgs.append(resampled)

    print(f"  ✓ All {len(run_imgs)} runs resampled to common grid")

    return resampled_imgs, target_affine, target_shape


def resample_mask_to_grid(
    mask_img,
    target_affine,
    target_shape,
    interpolation='nearest'
):
    """
    Resample ROI mask to match BOLD grid.

    Parameters
    ----------
    mask_img : NiftiImage
        ROI mask to resample
    target_affine : np.ndarray, shape (4, 4)
        Target affine transformation
    target_shape : tuple
        Target 3D grid shape
    interpolation : str, default='nearest'
        Interpolation method ('nearest' for binary masks, 'continuous' for probabilistic)

    Returns
    -------
    resampled_mask : NiftiImage
        Mask resampled to target grid

    Examples
    --------
    >>> mask = nib.load('V1_mask.nii.gz')
    >>> bold_affine = bold_img.affine
    >>> bold_shape = bold_img.shape[:3]
    >>> resampled_mask = resample_mask_to_grid(mask, bold_affine, bold_shape)
    """
    resampled_mask = nimg.resample_img(
        mask_img,
        target_affine=target_affine,
        target_shape=target_shape,
        interpolation=interpolation,
        force_resample=True
    )

    # Validate alignment
    affine_match = np.allclose(resampled_mask.affine, target_affine, atol=1e-6)
    shape_match = resampled_mask.shape[:3] == target_shape

    if not affine_match:
        print(f"  WARNING: Mask affine mismatch (max diff: {np.max(np.abs(resampled_mask.affine - target_affine))})")
    if not shape_match:
        raise ValueError(f"  ERROR: Mask shape mismatch {resampled_mask.shape[:3]} != {target_shape}")

    # For binary masks, ensure values remain binary after resampling
    if interpolation == 'nearest':
        mask_data = resampled_mask.get_fdata()
        unique_vals = np.unique(mask_data)
        print(f"  Mask unique values after resampling: {unique_vals}")
        if not np.all(np.isin(unique_vals, [0, 1])):
            print(f"  WARNING: Non-binary values in mask after nearest-neighbor resampling")

    return resampled_mask


def verify_grid_alignment(imgs, tolerance=1e-6):
    """
    Verify that multiple images have identical grid properties.

    Parameters
    ----------
    imgs : list of NiftiImage
        Images to verify
    tolerance : float, default=1e-6
        Tolerance for affine comparison

    Returns
    -------
    is_aligned : bool
        True if all images have identical affine and shape
    report : dict
        Alignment diagnostics
    """
    if len(imgs) < 2:
        return True, {'status': 'single_image'}

    ref_affine = imgs[0].affine
    ref_shape = imgs[0].shape[:3]

    max_affine_diff = 0
    shape_mismatches = []

    for i, img in enumerate(imgs[1:], start=1):
        affine_diff = np.max(np.abs(img.affine - ref_affine))
        max_affine_diff = max(max_affine_diff, affine_diff)

        if img.shape[:3] != ref_shape:
            shape_mismatches.append((i, img.shape[:3]))

    is_aligned = (max_affine_diff < tolerance) and (len(shape_mismatches) == 0)

    report = {
        'is_aligned': is_aligned,
        'max_affine_diff': float(max_affine_diff),
        'tolerance': tolerance,
        'shape_mismatches': shape_mismatches,
        'reference_shape': ref_shape
    }

    return is_aligned, report
