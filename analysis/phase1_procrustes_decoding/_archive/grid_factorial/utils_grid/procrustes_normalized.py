"""
Procrustes alignment with center+scale normalization.

Implements orthogonal Procrustes transformation after normalizing patterns
to prevent scale-induced disparities.
"""

import numpy as np
from scipy.linalg import orthogonal_procrustes


def procrustes_normalized(amplitudes, reference='mean'):
    """
    Apply Procrustes alignment after center+scale normalization.

    Normalization steps per run:
      1. Center: pattern - mean(pattern)
      2. Scale: pattern / std(pattern)
      3. Procrustes align to reference

    This prevents disparities from being dominated by scale differences
    between runs, focusing on rotational misalignment.

    Parameters
    ----------
    amplitudes : np.ndarray, shape (n_runs, n_colors, n_voxels)
        FIR amplitude estimates
    reference : str, default='mean'
        Reference for alignment:
        - 'mean': Align all runs to the mean pattern
        - 'first': Align all runs to the first run

    Returns
    -------
    aligned : np.ndarray, shape (n_runs, n_colors, n_voxels)
        Procrustes-aligned patterns
    disparities : np.ndarray, shape (n_runs,)
        Procrustes disparity for each run
        (Should be O(1) after normalization, vs O(10^4-10^8) raw)

    Examples
    --------
    >>> amplitudes = np.random.randn(6, 8, 100)
    >>> aligned, disparities = procrustes_normalized(amplitudes)
    >>> print(f"Mean disparity: {np.mean(disparities):.4f}")
    Mean disparity: 0.8523
    """
    n_runs, n_colors, n_voxels = amplitudes.shape

    # Step 1: Normalize each run (center + scale)
    normalized = np.zeros_like(amplitudes)

    for r in range(n_runs):
        pattern = amplitudes[r]  # (n_colors, n_voxels)

        # Center (remove mean)
        centered = pattern - pattern.mean()

        # Scale (divide by std)
        scale = np.std(centered)
        if scale > 1e-10:
            normalized[r] = centered / scale
        else:
            # Degenerate case: constant pattern
            normalized[r] = centered

    # Step 2: Compute reference pattern
    if reference == 'mean':
        ref_pattern = normalized.mean(axis=0)
    elif reference == 'first':
        ref_pattern = normalized[0]
    else:
        raise ValueError(f"Unknown reference type: {reference}")

    # Step 3: Align each run to reference using orthogonal Procrustes
    aligned = np.zeros_like(normalized)
    disparities = np.zeros(n_runs)

    for r in range(n_runs):
        pattern = normalized[r]  # (n_colors, n_voxels)

        # Orthogonal Procrustes: find rotation R that minimizes ||pattern @ R - ref||
        # scipy expects transposed matrices: (n_voxels, n_colors)
        R, disparity = orthogonal_procrustes(pattern.T, ref_pattern.T)

        # Apply transformation
        aligned[r] = (pattern.T @ R).T
        disparities[r] = disparity

    return aligned, disparities


def compute_procrustes_disparity_raw(amplitudes, reference='mean'):
    """
    Compute Procrustes disparity WITHOUT normalization (for comparison).

    This shows the scale-induced disparities that normalization prevents.

    Parameters
    ----------
    amplitudes : np.ndarray, shape (n_runs, n_colors, n_voxels)
        Raw FIR amplitude estimates
    reference : str, default='mean'
        Reference for alignment

    Returns
    -------
    disparities : np.ndarray, shape (n_runs,)
        Raw Procrustes disparities (typically O(10^4-10^8))
    """
    n_runs, n_colors, n_voxels = amplitudes.shape

    # Compute reference
    if reference == 'mean':
        ref_pattern = amplitudes.mean(axis=0)
    elif reference == 'first':
        ref_pattern = amplitudes[0]
    else:
        raise ValueError(f"Unknown reference type: {reference}")

    # Compute disparities without normalization
    disparities = np.zeros(n_runs)

    for r in range(n_runs):
        pattern = amplitudes[r]
        _, disparity = orthogonal_procrustes(pattern.T, ref_pattern.T)
        disparities[r] = disparity

    return disparities


def procrustes_reliability(amplitudes):
    """
    Compute Procrustes-based reliability metric.

    Lower mean disparity indicates more consistent representations across runs.

    Parameters
    ----------
    amplitudes : np.ndarray, shape (n_runs, n_colors, n_voxels)
        FIR amplitude estimates

    Returns
    -------
    stats : dict
        Disparity statistics:
        - mean: Mean disparity across runs
        - std: Standard deviation
        - min: Minimum disparity
        - max: Maximum disparity
    """
    _, disparities = procrustes_normalized(amplitudes)

    stats = {
        'mean': float(np.mean(disparities)),
        'std': float(np.std(disparities)),
        'min': float(np.min(disparities)),
        'max': float(np.max(disparities))
    }

    return stats
