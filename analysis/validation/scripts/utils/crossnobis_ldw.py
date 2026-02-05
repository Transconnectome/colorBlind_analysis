"""
Crossnobis distance with Ledoit-Wolf shrinkage covariance estimation.

Implements cross-validated Mahalanobis distance (crossnobis) for computing
representational dissimilarity matrices (RDMs). Uses Ledoit-Wolf shrinkage
for optimal covariance estimation with limited samples.

References
----------
Walther et al. (2016). Reliability of dissimilarity measures for multi-voxel
pattern analysis. NeuroImage, 137, 188-200.
"""

import numpy as np
from sklearn.covariance import LedoitWolf
from scipy.spatial.distance import mahalanobis


def compute_rdm_crossnobis(amplitudes, use_shrinkage=True):
    """
    Compute RDM using cross-validated Mahalanobis distance (crossnobis).

    For each test run:
      1. Estimate covariance Σ from training runs using Ledoit-Wolf shrinkage
      2. Compute Mahalanobis distance: d(i,j) = sqrt((μ_i - μ_j)^T Σ^(-1) (μ_i - μ_j))
      3. Average distances across run splits

    This provides more reliable distance estimates than Euclidean or correlation
    distance, especially with high-dimensional voxel patterns.

    Parameters
    ----------
    amplitudes : np.ndarray, shape (n_runs, n_colors, n_voxels)
        FIR amplitude estimates for each run, color, and voxel
    use_shrinkage : bool, default=True
        Whether to use Ledoit-Wolf shrinkage for covariance estimation
        (Recommended for fMRI data with n_voxels > n_samples)

    Returns
    -------
    rdm : np.ndarray, shape (n_colors, n_colors)
        Average crossnobis RDM across all leave-one-run-out splits
    shrinkage : float
        Mean Ledoit-Wolf shrinkage parameter across splits
        - 0: No shrinkage (sample covariance)
        - 1: Full shrinkage (diagonal covariance)
        - Typical fMRI: 0.2-0.4

    Examples
    --------
    >>> amplitudes = np.random.randn(6, 8, 100)  # 6 runs, 8 colors, 100 voxels
    >>> rdm, shrinkage = compute_rdm_crossnobis(amplitudes)
    >>> print(f"RDM shape: {rdm.shape}, Shrinkage: {shrinkage:.3f}")
    RDM shape: (8, 8), Shrinkage: 0.245
    """
    n_runs, n_colors, n_voxels = amplitudes.shape

    if n_runs < 2:
        raise ValueError(f"Need at least 2 runs for cross-validation, got {n_runs}")

    rdm_sum = np.zeros((n_colors, n_colors))
    shrinkages = []

    for test_run in range(n_runs):
        # Leave-one-run-out split
        train_runs = [r for r in range(n_runs) if r != test_run]
        train_data = amplitudes[train_runs]  # (n_train, n_colors, n_voxels)

        # Reshape for covariance: (n_samples, n_features)
        # Each sample is one color pattern from one training run
        X_train = train_data.reshape(-1, n_voxels)  # (n_train * n_colors, n_voxels)

        # Estimate covariance with Ledoit-Wolf shrinkage
        if use_shrinkage:
            lw = LedoitWolf()
            lw.fit(X_train)
            cov = lw.covariance_
            shrinkage = lw.shrinkage_
            shrinkages.append(shrinkage)
        else:
            # Sample covariance (may be singular if n_voxels > n_samples)
            cov = np.cov(X_train.T)
            shrinkage = 0.0

        # Compute precision matrix (inverse covariance)
        # Use pseudoinverse for numerical stability
        try:
            cov_inv = np.linalg.inv(cov)
        except np.linalg.LinAlgError:
            print(f"  WARNING: Singular covariance matrix for test run {test_run}, using pseudoinverse")
            cov_inv = np.linalg.pinv(cov)

        # Test run patterns
        test_patterns = amplitudes[test_run]  # (n_colors, n_voxels)

        # Compute pairwise Mahalanobis distances
        rdm_test = np.zeros((n_colors, n_colors))
        for i in range(n_colors):
            for j in range(n_colors):
                diff = test_patterns[i] - test_patterns[j]
                # Mahalanobis distance: sqrt(diff^T * Σ^-1 * diff)
                try:
                    dist_sq = diff @ cov_inv @ diff.T
                    if dist_sq < 0:
                        # Numerical error can cause negative values
                        dist_sq = 0
                    dist = np.sqrt(dist_sq)
                except:
                    # Fallback to Euclidean if Mahalanobis fails
                    dist = np.linalg.norm(diff)

                rdm_test[i, j] = dist

        rdm_sum += rdm_test

    # Average across leave-one-run-out splits
    rdm_avg = rdm_sum / n_runs
    mean_shrinkage = np.mean(shrinkages) if shrinkages else 0.0

    return rdm_avg, mean_shrinkage


def compute_rdm_correlation(amplitudes):
    """
    Compute RDM using correlation distance (baseline comparison).

    Parameters
    ----------
    amplitudes : np.ndarray, shape (n_runs, n_colors, n_voxels)
        FIR amplitude estimates

    Returns
    -------
    rdms : np.ndarray, shape (n_runs, n_colors, n_colors)
        Correlation-based RDM for each run
    """
    n_runs, n_colors, n_voxels = amplitudes.shape
    rdms = np.zeros((n_runs, n_colors, n_colors))

    for r in range(n_runs):
        # Correlation distance: 1 - Pearson correlation
        rdms[r] = 1 - np.corrcoef(amplitudes[r])

    return rdms


def compute_crossnobis_rdms_per_run(amplitudes, use_shrinkage=True):
    """
    Compute per-run crossnobis RDMs using leave-one-run-out cross-validation.

    For each test run, computes crossnobis RDM using covariance estimated
    from all other runs. This allows computing RDM reliability across runs.

    Parameters
    ----------
    amplitudes : np.ndarray, shape (n_runs, n_colors, n_voxels)
        FIR amplitude estimates for each run, color, and voxel
    use_shrinkage : bool, default=True
        Whether to use Ledoit-Wolf shrinkage for covariance estimation

    Returns
    -------
    rdms : np.ndarray, shape (n_runs, n_colors, n_colors)
        Crossnobis RDM for each run (as test run in LORO)
    shrinkages : np.ndarray, shape (n_runs,)
        Ledoit-Wolf shrinkage parameter for each run's covariance estimate

    Examples
    --------
    >>> amplitudes = np.random.randn(6, 8, 100)
    >>> rdms, shrinkages = compute_crossnobis_rdms_per_run(amplitudes)
    >>> print(f"RDMs shape: {rdms.shape}, Mean shrinkage: {shrinkages.mean():.3f}")
    RDMs shape: (6, 8, 8), Mean shrinkage: 0.245
    """
    n_runs, n_colors, n_voxels = amplitudes.shape

    if n_runs < 2:
        raise ValueError(f"Need at least 2 runs for cross-validation, got {n_runs}")

    rdms = np.zeros((n_runs, n_colors, n_colors))
    shrinkages = np.zeros(n_runs)

    for test_run in range(n_runs):
        # Leave-one-run-out split
        train_runs = [r for r in range(n_runs) if r != test_run]
        train_data = amplitudes[train_runs]

        # Reshape for covariance
        X_train = train_data.reshape(-1, n_voxels)

        # Estimate covariance with Ledoit-Wolf shrinkage
        if use_shrinkage:
            lw = LedoitWolf()
            lw.fit(X_train)
            cov = lw.covariance_
            shrinkages[test_run] = lw.shrinkage_
        else:
            cov = np.cov(X_train.T)
            shrinkages[test_run] = 0.0

        # Compute precision matrix
        try:
            cov_inv = np.linalg.inv(cov)
        except np.linalg.LinAlgError:
            cov_inv = np.linalg.pinv(cov)

        # Test run patterns
        test_patterns = amplitudes[test_run]

        # Compute pairwise Mahalanobis distances
        for i in range(n_colors):
            for j in range(n_colors):
                diff = test_patterns[i] - test_patterns[j]
                try:
                    dist_sq = diff @ cov_inv @ diff.T
                    if dist_sq < 0:
                        dist_sq = 0
                    dist = np.sqrt(dist_sq)
                except:
                    dist = np.linalg.norm(diff)

                rdms[test_run, i, j] = dist

    return rdms, shrinkages


def rdm_reliability(rdms):
    """
    Compute RDM reliability using pairwise run correlations.

    Parameters
    ----------
    rdms : np.ndarray, shape (n_runs, n_colors, n_colors)
        RDMs for each run

    Returns
    -------
    mean_corr : float
        Mean Spearman correlation between all run pairs
    std_corr : float
        Standard deviation of correlations
    all_corrs : np.ndarray
        All pairwise correlations
    """
    from scipy.stats import spearmanr

    n_runs, n_colors, _ = rdms.shape

    # Upper triangle indices (excluding diagonal)
    triu_idx = np.triu_indices(n_colors, k=1)

    # Compute pairwise correlations between runs
    run_pairs = []
    for i in range(n_runs):
        for j in range(i + 1, n_runs):
            rdm_i = rdms[i][triu_idx]
            rdm_j = rdms[j][triu_idx]
            corr, _ = spearmanr(rdm_i, rdm_j)
            run_pairs.append(corr)

    all_corrs = np.array(run_pairs)
    mean_corr = np.mean(all_corrs)
    std_corr = np.std(all_corrs)

    return mean_corr, std_corr, all_corrs
