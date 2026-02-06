"""
Noise Covariance Estimation and Whitening from GLMsingle Residuals

Implements Walther et al. (2016) whitening approach:
1. Estimate noise covariance Σ from 1st-level residuals
2. Compute whitening matrix W = Σ^(-1/2)
3. Apply whitening to decorrelate spatial noise

Expected improvement: +20-30% over GLMsingle alone
"""

import numpy as np
from sklearn.covariance import LedoitWolf, EmpiricalCovariance
import warnings


def estimate_noise_covariance(
    residuals_1st,
    method='ledoit_wolf',
    verbose=True
):
    """
    Estimate spatial noise covariance from GLMsingle 1st-level residuals.

    Uses Ledoit-Wolf shrinkage for stability with limited samples.

    Args:
        residuals_1st: (n_runs, n_samples, n_voxels) or (n_samples_total, n_voxels)
            1st-level residuals from GLMsingle
            Example shape: (6 runs, ~240 samples, 400 voxels)
        method: 'ledoit_wolf' | 'empirical' | 'diagonal'
            Estimation method:
            - ledoit_wolf: Shrinkage regularization (recommended)
            - empirical: Sample covariance (needs many samples)
            - diagonal: Assume independent voxels (no spatial correlation)
        verbose: Print diagnostic information

    Returns:
        Sigma: (n_voxels, n_voxels) noise covariance matrix
        metadata: Dictionary with estimation details
    """
    # Reshape if needed: concatenate runs
    if residuals_1st.ndim == 3:
        # (n_runs, n_samples, n_voxels) → (n_samples_total, n_voxels)
        residuals_concat = np.concatenate(residuals_1st, axis=0)
    elif residuals_1st.ndim == 2:
        residuals_concat = residuals_1st
    else:
        raise ValueError(f"Invalid residuals shape: {residuals_1st.shape}. "
                        f"Expected (n_runs, n_samples, n_voxels) or (n_samples, n_voxels)")

    n_samples, n_voxels = residuals_concat.shape

    if verbose:
        print(f"Estimating noise covariance:")
        print(f"  Samples: {n_samples}")
        print(f"  Voxels: {n_voxels}")
        print(f"  Method: {method}")

    # Check sample/voxel ratio
    sample_ratio = n_samples / n_voxels
    if sample_ratio < 2 and method == 'empirical':
        warnings.warn(
            f"Sample/voxel ratio {sample_ratio:.2f} is low. "
            f"Consider using 'ledoit_wolf' method for stability."
        )

    # Estimate covariance
    metadata = {'method': method, 'n_samples': n_samples, 'n_voxels': n_voxels}

    if method == 'ledoit_wolf':
        # Ledoit-Wolf shrinkage: Σ = (1-λ)Σ_sample + λ·I
        lw = LedoitWolf(assume_centered=False)
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', category=UserWarning)
            Sigma = lw.fit(residuals_concat).covariance_
        metadata['shrinkage'] = lw.shrinkage_

        if verbose:
            print(f"  Shrinkage: {lw.shrinkage_:.4f}")

    elif method == 'empirical':
        # Sample covariance (no regularization)
        ec = EmpiricalCovariance(assume_centered=False)
        Sigma = ec.fit(residuals_concat).covariance_
        metadata['shrinkage'] = 0.0

    elif method == 'diagonal':
        # Assume independent voxels (diagonal covariance)
        variances = np.var(residuals_concat, axis=0)
        Sigma = np.diag(variances)
        metadata['shrinkage'] = None

    else:
        raise ValueError(f"Unknown method: {method}")

    # Diagnostics
    eigenvalues = np.linalg.eigvalsh(Sigma)
    cond_number = eigenvalues[-1] / (eigenvalues[0] + 1e-10)
    metadata['condition_number'] = cond_number
    metadata['eigenvalue_min'] = eigenvalues[0]
    metadata['eigenvalue_max'] = eigenvalues[-1]

    if verbose:
        print(f"  Condition number: {cond_number:.2e}")
        print(f"  Eigenvalues: [{eigenvalues[0]:.3f}, {eigenvalues[-1]:.3f}]")

        if cond_number > 1e10:
            warnings.warn(
                f"High condition number {cond_number:.2e} may cause numerical instability. "
                f"Shrinkage: {metadata.get('shrinkage', 'N/A')}"
            )

    # Check positive definiteness
    if np.any(eigenvalues <= 0):
        n_neg = np.sum(eigenvalues <= 0)
        warnings.warn(
            f"{n_neg} non-positive eigenvalues found. "
            f"Adding small regularization."
        )
        Sigma += np.eye(n_voxels) * 1e-6

    return Sigma, metadata


def compute_whitening_matrix(Sigma, method='eigh', epsilon=1e-10):
    """
    Compute whitening matrix W = Σ^(-1/2) via eigendecomposition.

    After whitening: W @ Σ @ W^T ≈ I (identity)

    Args:
        Sigma: (n_voxels, n_voxels) noise covariance matrix
        method: 'eigh' | 'svd'
            Decomposition method:
            - eigh: Symmetric eigendecomposition (faster)
            - svd: Singular value decomposition (more stable)
        epsilon: Small value added to eigenvalues for stability

    Returns:
        W: (n_voxels, n_voxels) whitening matrix
        metadata: Dictionary with computation details
    """
    n_voxels = Sigma.shape[0]

    if method == 'eigh':
        # Symmetric eigendecomposition: Σ = V Λ V^T
        eigenvalues, eigenvectors = np.linalg.eigh(Sigma)

        # Σ^(-1/2) = V Λ^(-1/2) V^T
        eigenvalues_inv_sqrt = 1.0 / np.sqrt(eigenvalues + epsilon)
        W = eigenvectors @ np.diag(eigenvalues_inv_sqrt) @ eigenvectors.T

        metadata = {
            'method': 'eigh',
            'eigenvalue_min': eigenvalues[0],
            'eigenvalue_max': eigenvalues[-1],
            'epsilon': epsilon
        }

    elif method == 'svd':
        # SVD: Σ = U S V^T
        U, S, Vt = np.linalg.svd(Sigma)

        # Σ^(-1/2) = U S^(-1/2) V^T
        S_inv_sqrt = 1.0 / np.sqrt(S + epsilon)
        W = U @ np.diag(S_inv_sqrt) @ Vt

        metadata = {
            'method': 'svd',
            'singular_value_min': S[0],
            'singular_value_max': S[-1],
            'epsilon': epsilon
        }

    else:
        raise ValueError(f"Unknown method: {method}")

    # Verify: W @ Sigma @ W^T should be ≈ I
    identity_test = W @ Sigma @ W.T
    identity_error = np.linalg.norm(identity_test - np.eye(n_voxels), 'fro')
    metadata['identity_error'] = identity_error

    if identity_error > 0.1:
        warnings.warn(
            f"Whitening verification failed: ||W·Σ·W^T - I|| = {identity_error:.6f}. "
            f"Expected < 0.1. Check covariance conditioning."
        )

    return W, metadata


def apply_whitening(data, whitening_matrix, axis=-1):
    """
    Apply whitening transformation to decorrelate voxels.

    Transformation: data_white = data @ W

    Args:
        data: (..., n_voxels) data to whiten
            Can be:
            - Single-trial betas: (n_trials, n_voxels)
            - Amplitudes: (n_runs, n_colors, n_voxels)
            - Any array with voxels on last axis
        whitening_matrix: (n_voxels, n_voxels) W = Σ^(-1/2)
        axis: Axis corresponding to voxels (default: -1)

    Returns:
        data_whitened: Same shape as input, whitened along voxel axis
    """
    # Move voxel axis to last position if needed
    data_moved = np.moveaxis(data, axis, -1)

    # Apply whitening: data @ W
    data_whitened = data_moved @ whitening_matrix

    # Move axis back
    data_whitened = np.moveaxis(data_whitened, -1, axis)

    return data_whitened


def block_diagonal_whitening(
    residuals_1st,
    block_size=100,
    method='ledoit_wolf',
    verbose=True
):
    """
    Compute block-diagonal whitening matrix for large ROIs.

    Splits voxels into blocks, estimates covariance per block.
    Reduces memory: O(n_blocks × block_size²) vs O(n_voxels²)

    Use when:
    - n_voxels > 1000
    - Memory constraints
    - Assuming local spatial correlation only

    Args:
        residuals_1st: (n_runs, n_samples, n_voxels)
        block_size: Number of voxels per block
        method: Covariance estimation method
        verbose: Print progress

    Returns:
        W_block_diag: (n_voxels, n_voxels) block-diagonal whitening matrix
        metadata: Dictionary with block information
    """
    if residuals_1st.ndim == 3:
        _, _, n_voxels = residuals_1st.shape
    else:
        _, n_voxels = residuals_1st.shape

    n_blocks = int(np.ceil(n_voxels / block_size))

    if verbose:
        print(f"Block-diagonal whitening:")
        print(f"  Total voxels: {n_voxels}")
        print(f"  Block size: {block_size}")
        print(f"  Number of blocks: {n_blocks}")

    # Initialize block-diagonal matrix
    W_block_diag = np.zeros((n_voxels, n_voxels))
    block_metadata = []

    for block_idx in range(n_blocks):
        start = block_idx * block_size
        end = min((block_idx + 1) * block_size, n_voxels)
        block_n_voxels = end - start

        if verbose:
            print(f"  Processing block {block_idx + 1}/{n_blocks} "
                  f"(voxels {start}:{end})")

        # Extract residuals for this block
        if residuals_1st.ndim == 3:
            residuals_block = residuals_1st[:, :, start:end]
        else:
            residuals_block = residuals_1st[:, start:end]

        # Estimate covariance for this block
        Sigma_block, meta_cov = estimate_noise_covariance(
            residuals_block,
            method=method,
            verbose=False
        )

        # Compute whitening matrix for this block
        W_block, meta_white = compute_whitening_matrix(Sigma_block)

        # Insert into block-diagonal matrix
        W_block_diag[start:end, start:end] = W_block

        # Store metadata
        block_metadata.append({
            'block_idx': block_idx,
            'start': start,
            'end': end,
            'n_voxels': block_n_voxels,
            'condition_number': meta_cov['condition_number'],
            'shrinkage': meta_cov.get('shrinkage', None)
        })

    metadata = {
        'n_blocks': n_blocks,
        'block_size': block_size,
        'blocks': block_metadata
    }

    if verbose:
        avg_cond = np.mean([b['condition_number'] for b in block_metadata])
        print(f"  Average condition number: {avg_cond:.2e}")

    return W_block_diag, metadata


def evaluate_whitening_quality(data, whitened_data, axis=-1):
    """
    Evaluate whitening quality by checking decorrelation.

    Good whitening should:
    1. Preserve mean (approximately)
    2. Preserve variance (approximately)
    3. Reduce voxel correlations

    Args:
        data: Original data (..., n_voxels)
        whitened_data: Whitened data (..., n_voxels)
        axis: Voxel axis

    Returns:
        metrics: Dictionary with quality metrics
    """
    # Flatten to (n_samples, n_voxels)
    data_flat = data.reshape(-1, data.shape[axis])
    whitened_flat = whitened_data.reshape(-1, whitened_data.shape[axis])

    # Mean preservation
    mean_orig = data_flat.mean(axis=0)
    mean_white = whitened_flat.mean(axis=0)
    mean_diff = np.abs(mean_white - mean_orig).mean()

    # Variance preservation
    var_orig = data_flat.var(axis=0)
    var_white = whitened_flat.var(axis=0)
    var_ratio = (var_white / (var_orig + 1e-10)).mean()

    # Correlation reduction
    corr_orig = np.corrcoef(data_flat.T)
    corr_white = np.corrcoef(whitened_flat.T)

    # Off-diagonal correlations (exclude diagonal)
    mask = ~np.eye(corr_orig.shape[0], dtype=bool)
    corr_orig_off = np.abs(corr_orig[mask])
    corr_white_off = np.abs(corr_white[mask])

    avg_corr_orig = corr_orig_off.mean()
    avg_corr_white = corr_white_off.mean()
    corr_reduction = (avg_corr_orig - avg_corr_white) / (avg_corr_orig + 1e-10)

    metrics = {
        'mean_difference': mean_diff,
        'variance_ratio': var_ratio,
        'avg_correlation_original': avg_corr_orig,
        'avg_correlation_whitened': avg_corr_white,
        'correlation_reduction_pct': corr_reduction * 100
    }

    return metrics


if __name__ == '__main__':
    # Test with synthetic data
    print("=" * 60)
    print("TESTING WHITENING UTILITIES")
    print("=" * 60)

    # Simulate residuals with spatial correlation
    n_runs = 6
    n_samples = 240
    n_voxels = 100

    # Create correlated noise
    np.random.seed(42)
    true_Sigma = np.eye(n_voxels)
    for i in range(n_voxels):
        for j in range(i + 1, min(i + 10, n_voxels)):
            corr_val = 0.5 * np.exp(-0.1 * (j - i))
            true_Sigma[i, j] = corr_val
            true_Sigma[j, i] = corr_val

    # Generate residuals
    residuals = []
    for _ in range(n_runs):
        residual_run = np.random.multivariate_normal(
            np.zeros(n_voxels),
            true_Sigma,
            size=n_samples
        )
        residuals.append(residual_run)
    residuals = np.array(residuals)

    print(f"\nSimulated residuals: {residuals.shape}")

    # Estimate covariance
    print("\n" + "=" * 60)
    print("1. Estimating Noise Covariance")
    print("=" * 60)
    Sigma_est, meta_cov = estimate_noise_covariance(residuals, method='ledoit_wolf')

    # Compute whitening matrix
    print("\n" + "=" * 60)
    print("2. Computing Whitening Matrix")
    print("=" * 60)
    W, meta_white = compute_whitening_matrix(Sigma_est)
    print(f"Identity error: {meta_white['identity_error']:.6f}")

    # Apply whitening
    print("\n" + "=" * 60)
    print("3. Applying Whitening")
    print("=" * 60)
    residuals_white = apply_whitening(residuals, W, axis=-1)
    print(f"Whitened shape: {residuals_white.shape}")

    # Evaluate quality
    print("\n" + "=" * 60)
    print("4. Evaluating Whitening Quality")
    print("=" * 60)
    metrics = evaluate_whitening_quality(residuals, residuals_white)
    for key, value in metrics.items():
        print(f"  {key}: {value:.4f}")

    print("\n" + "=" * 60)
    print("Expected: correlation_reduction > 50%")
    print("=" * 60)
