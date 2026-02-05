"""
Multivariate Noise Normalization (Whitening) for fMRI Data

Implements noise covariance estimation from GLM residuals and whitening
transformation to decorrelate voxel noise. This improves RDM reliability by
removing shared noise structure across voxels.

References:
- Walther et al. (2016). Reliability of dissimilarity measures for multi-voxel pattern analysis. NeuroImage.
- Ledoit & Wolf (2004). A well-conditioned estimator for large-dimensional covariance matrices. Journal of Multivariate Analysis.
- Diedrichsen et al. (2011). Detecting and adjusting for artifacts in fMRI time series data. NeuroImage.

Key concepts:
1. **Noise covariance**: Spatial correlation structure of noise across voxels
2. **Whitening**: Transform X_white = X @ Σ^(-1/2) to decorrelate noise
3. **Shrinkage estimation**: Ledoit-Wolf regularization for n_voxels > n_samples

When whitening helps:
- High spatial noise correlation (neighboring voxels)
- Low SNR data (noise dominates signal)
- Small sample size (n_samples < n_voxels)
"""

import numpy as np
from typing import Dict, Tuple, Optional, List
from scipy.stats import spearmanr
from scipy.spatial.distance import squareform, pdist
from sklearn.covariance import LedoitWolf
import matplotlib.pyplot as plt


def estimate_noise_covariance(residuals: np.ndarray,
                              method: str = 'ledoit_wolf',
                              return_shrinkage: bool = True) -> Tuple[np.ndarray, Optional[float]]:
    """
    Estimate noise covariance matrix from GLM residuals.

    Args:
        residuals: (n_samples, n_voxels) - GLM residuals
        method: Covariance estimation method
            - 'ledoit_wolf': Shrinkage estimator (default, handles n < p)
            - 'empirical': Sample covariance (requires n > p)
            - 'diagonal': Assumes independent voxels (Σ = diag)
        return_shrinkage: Return shrinkage parameter (for ledoit_wolf)

    Returns:
        cov_matrix: (n_voxels, n_voxels) - Noise covariance estimate
        shrinkage: float or None - Shrinkage parameter (0=empirical, 1=diagonal)
    """
    n_samples, n_voxels = residuals.shape

    if method == 'ledoit_wolf':
        # Ledoit-Wolf shrinkage estimator
        lw = LedoitWolf(assume_centered=False)
        lw.fit(residuals)
        cov_matrix = lw.covariance_
        shrinkage = lw.shrinkage_ if return_shrinkage else None

        print(f"Ledoit-Wolf covariance estimated: shrinkage = {shrinkage:.3f}")

    elif method == 'empirical':
        if n_samples <= n_voxels:
            print(f"Warning: n_samples ({n_samples}) <= n_voxels ({n_voxels}). "
                  f"Consider using 'ledoit_wolf' instead.")
        # Empirical covariance
        cov_matrix = np.cov(residuals, rowvar=False)
        shrinkage = None

    elif method == 'diagonal':
        # Diagonal covariance (assume independent voxels)
        variances = np.var(residuals, axis=0)
        cov_matrix = np.diag(variances)
        shrinkage = 1.0  # Full shrinkage to diagonal

    else:
        raise ValueError(f"Unknown method: {method}. Use 'ledoit_wolf', 'empirical', or 'diagonal'.")

    return cov_matrix, shrinkage


def compute_whitening_matrix(cov_matrix: np.ndarray,
                             epsilon: float = 1e-8) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute whitening matrix: Σ^(-1/2) via eigendecomposition.

    Args:
        cov_matrix: (n_voxels, n_voxels) - Noise covariance
        epsilon: Regularization for numerical stability

    Returns:
        whitening_matrix: (n_voxels, n_voxels) - Σ^(-1/2)
        dewhitening_matrix: (n_voxels, n_voxels) - Σ^(1/2) for reconstruction
    """
    # Eigendecomposition: Σ = Q Λ Q^T
    eigvals, eigvecs = np.linalg.eigh(cov_matrix)

    # Handle negative eigenvalues (numerical errors)
    eigvals = np.maximum(eigvals, epsilon)

    # Σ^(-1/2) = Q Λ^(-1/2) Q^T
    eigvals_inv_sqrt = 1.0 / np.sqrt(eigvals)
    whitening_matrix = eigvecs @ np.diag(eigvals_inv_sqrt) @ eigvecs.T

    # Σ^(1/2) = Q Λ^(1/2) Q^T (for reconstruction)
    eigvals_sqrt = np.sqrt(eigvals)
    dewhitening_matrix = eigvecs @ np.diag(eigvals_sqrt) @ eigvecs.T

    return whitening_matrix, dewhitening_matrix


def whiten_amplitudes(amplitudes: np.ndarray,
                     noise_cov: np.ndarray,
                     epsilon: float = 1e-8) -> Tuple[np.ndarray, np.ndarray]:
    """
    Apply whitening transformation to amplitudes.

    X_white = X @ Σ^(-1/2)

    This decorrelates noise across voxels, improving RDM reliability.

    Args:
        amplitudes: (n_runs, n_colors, n_voxels) or (n_colors, n_voxels)
        noise_cov: (n_voxels, n_voxels) - Noise covariance matrix
        epsilon: Regularization for numerical stability

    Returns:
        amplitudes_whitened: Same shape as input - Whitened amplitudes
        whitening_matrix: (n_voxels, n_voxels) - Transformation matrix
    """
    # Compute whitening matrix
    whitening_matrix, _ = compute_whitening_matrix(noise_cov, epsilon)

    # Apply whitening
    if amplitudes.ndim == 3:
        # (n_runs, n_colors, n_voxels) @ (n_voxels, n_voxels)
        amplitudes_whitened = amplitudes @ whitening_matrix
    elif amplitudes.ndim == 2:
        # (n_colors, n_voxels) @ (n_voxels, n_voxels)
        amplitudes_whitened = amplitudes @ whitening_matrix
    else:
        raise ValueError(f"Amplitudes must be 2D or 3D, got shape {amplitudes.shape}")

    return amplitudes_whitened, whitening_matrix


def evaluate_whitening_effect(amplitudes_raw: np.ndarray,
                              residuals: np.ndarray,
                              metric: str = 'correlation') -> Dict:
    """
    Compare RDM reliability before and after whitening.

    Args:
        amplitudes_raw: (n_runs, n_colors, n_voxels) - Raw amplitudes
        residuals: (n_samples, n_voxels) - GLM residuals for noise estimation
        metric: Distance metric for RDM

    Returns:
        results: Dict with keys:
            - 'raw_reliability': RDM reliability before whitening
            - 'whitened_reliability': RDM reliability after whitening
            - 'improvement': Absolute improvement
            - 'improvement_pct': Relative improvement percentage
            - 'noise_cov': Noise covariance matrix
            - 'shrinkage': Shrinkage parameter
    """
    n_runs, n_colors, n_voxels = amplitudes_raw.shape

    # Estimate noise covariance
    noise_cov, shrinkage = estimate_noise_covariance(residuals, method='ledoit_wolf')

    # Apply whitening
    amplitudes_whitened, whitening_matrix = whiten_amplitudes(amplitudes_raw, noise_cov)

    # Compute RDM reliability (inter-run correlation)
    def compute_rdm_reliability(amplitudes):
        rdms = []
        for run in range(n_runs):
            patterns = amplitudes[run]  # (n_colors, n_voxels or n_features)
            if metric == 'correlation':
                rdm = 1 - np.corrcoef(patterns)
            else:
                rdm = squareform(pdist(patterns, metric=metric))
            rdms.append(rdm)

        # Pairwise run correlations
        correlations = []
        for i in range(n_runs):
            for j in range(i+1, n_runs):
                mask = np.triu(np.ones_like(rdms[i], dtype=bool), k=1)
                r, _ = spearmanr(rdms[i][mask], rdms[j][mask])
                if np.isfinite(r):
                    correlations.append(r)

        return np.mean(correlations) if correlations else 0.0

    raw_reliability = compute_rdm_reliability(amplitudes_raw)
    whitened_reliability = compute_rdm_reliability(amplitudes_whitened)

    improvement = whitened_reliability - raw_reliability
    improvement_pct = (improvement / raw_reliability * 100) if raw_reliability > 0 else 0

    results = {
        'raw_reliability': raw_reliability,
        'whitened_reliability': whitened_reliability,
        'improvement': improvement,
        'improvement_pct': improvement_pct,
        'noise_cov': noise_cov,
        'shrinkage': shrinkage,
        'whitening_matrix': whitening_matrix
    }

    print(f"\n=== Whitening Effect ===")
    print(f"Raw RDM reliability: {raw_reliability:.3f}")
    print(f"Whitened RDM reliability: {whitened_reliability:.3f}")
    print(f"Improvement: {improvement:+.3f} ({improvement_pct:+.1f}%)")
    print(f"Shrinkage parameter: {shrinkage:.3f}")

    return results


def visualize_noise_covariance(noise_cov: np.ndarray,
                               output_path: str,
                               figsize: Tuple[int, int] = (10, 8),
                               vmin: Optional[float] = None,
                               vmax: Optional[float] = None) -> None:
    """
    Visualize noise covariance matrix.

    Args:
        noise_cov: (n_voxels, n_voxels) - Noise covariance
        output_path: Path to save figure
        figsize: Figure size
        vmin, vmax: Color scale limits
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

    # Covariance matrix heatmap
    im1 = ax1.imshow(noise_cov, cmap='RdBu_r', aspect='auto', vmin=vmin, vmax=vmax)
    ax1.set_title('Noise Covariance Matrix', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Voxel Index', fontsize=12)
    ax1.set_ylabel('Voxel Index', fontsize=12)
    plt.colorbar(im1, ax=ax1, label='Covariance')

    # Correlation matrix (normalized covariance)
    std_dev = np.sqrt(np.diag(noise_cov))
    noise_corr = noise_cov / np.outer(std_dev, std_dev)

    im2 = ax2.imshow(noise_corr, cmap='RdBu_r', aspect='auto', vmin=-1, vmax=1)
    ax2.set_title('Noise Correlation Matrix', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Voxel Index', fontsize=12)
    ax2.set_ylabel('Voxel Index', fontsize=12)
    plt.colorbar(im2, ax=ax2, label='Correlation')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved noise covariance visualization to {output_path}")


def visualize_whitening_effect(amplitudes_raw: np.ndarray,
                               amplitudes_whitened: np.ndarray,
                               output_path: str,
                               color_labels: Optional[List[str]] = None,
                               figsize: Tuple[int, int] = (12, 5)) -> None:
    """
    Visualize effect of whitening on voxel correlations.

    Shows:
    1. Voxel correlation before whitening
    2. Voxel correlation after whitening (should be identity)

    Args:
        amplitudes_raw: (n_runs, n_colors, n_voxels) - Before whitening
        amplitudes_whitened: (n_runs, n_colors, n_voxels) - After whitening
        output_path: Path to save figure
        color_labels: Optional labels for colors
        figsize: Figure size
    """
    # Average across runs and colors to get voxel activity patterns
    raw_voxels = amplitudes_raw.reshape(-1, amplitudes_raw.shape[2])  # (n_runs*n_colors, n_voxels)
    whitened_voxels = amplitudes_whitened.reshape(-1, amplitudes_whitened.shape[2])

    # Compute voxel correlation matrices
    raw_voxel_corr = np.corrcoef(raw_voxels.T)
    whitened_voxel_corr = np.corrcoef(whitened_voxels.T)

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=figsize)

    # Raw correlation
    im1 = ax1.imshow(raw_voxel_corr, cmap='RdBu_r', aspect='auto', vmin=-1, vmax=1)
    ax1.set_title('Before Whitening\n(Voxel Correlations)', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Voxel Index', fontsize=10)
    ax1.set_ylabel('Voxel Index', fontsize=10)
    plt.colorbar(im1, ax=ax1, label='Correlation', fraction=0.046, pad=0.04)

    # Whitened correlation (should be ~identity)
    im2 = ax2.imshow(whitened_voxel_corr, cmap='RdBu_r', aspect='auto', vmin=-1, vmax=1)
    ax2.set_title('After Whitening\n(Should be Identity)', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Voxel Index', fontsize=10)
    ax2.set_ylabel('Voxel Index', fontsize=10)
    plt.colorbar(im2, ax=ax2, label='Correlation', fraction=0.046, pad=0.04)

    # Difference (should be small off-diagonal)
    diff = whitened_voxel_corr - np.eye(whitened_voxel_corr.shape[0])
    im3 = ax3.imshow(diff, cmap='RdBu_r', aspect='auto', vmin=-0.5, vmax=0.5)
    ax3.set_title('Difference from Identity\n(Residual Correlation)', fontsize=12, fontweight='bold')
    ax3.set_xlabel('Voxel Index', fontsize=10)
    ax3.set_ylabel('Voxel Index', fontsize=10)
    plt.colorbar(im3, ax=ax3, label='Residual', fraction=0.046, pad=0.04)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved whitening effect visualization to {output_path}")

    # Print diagnostics
    off_diag_raw = raw_voxel_corr[~np.eye(raw_voxel_corr.shape[0], dtype=bool)]
    off_diag_whitened = whitened_voxel_corr[~np.eye(whitened_voxel_corr.shape[0], dtype=bool)]

    print(f"\nVoxel correlation diagnostics:")
    print(f"Raw - Mean off-diagonal: {np.mean(off_diag_raw):.3f} (±{np.std(off_diag_raw):.3f})")
    print(f"Whitened - Mean off-diagonal: {np.mean(off_diag_whitened):.3f} (±{np.std(off_diag_whitened):.3f})")
    print(f"Reduction: {(1 - np.abs(np.mean(off_diag_whitened)) / np.abs(np.mean(off_diag_raw))) * 100:.1f}%")


def compute_pattern_snr(amplitudes: np.ndarray) -> Dict[str, float]:
    """
    Compute pattern SNR: between-condition variance / within-condition variance.

    This measures how distinct the neural patterns are relative to noise.

    Args:
        amplitudes: (n_runs, n_colors, n_voxels) - Neural response patterns

    Returns:
        snr_metrics: Dict with:
            - 'pattern_snr': Overall pattern SNR
            - 'between_var': Between-condition variance
            - 'within_var': Within-condition variance (noise)
            - 'snr_db': SNR in decibels (10*log10)
    """
    n_runs, n_colors, n_voxels = amplitudes.shape

    # Grand mean pattern (across all runs and colors)
    grand_mean = amplitudes.mean(axis=(0, 1))  # (n_voxels,)

    # Between-condition variance (signal)
    # Mean pattern per color (averaged across runs)
    color_means = amplitudes.mean(axis=0)  # (n_colors, n_voxels)
    between_var = np.mean(np.var(color_means, axis=0))  # Variance across colors

    # Within-condition variance (noise)
    # Variance within each color across runs
    within_vars = []
    for color in range(n_colors):
        color_patterns = amplitudes[:, color, :]  # (n_runs, n_voxels)
        within_vars.append(np.var(color_patterns, axis=0))  # (n_voxels,)

    within_var = np.mean(within_vars)  # Average across colors and voxels

    # Pattern SNR
    pattern_snr = between_var / (within_var + 1e-10)

    # SNR in decibels
    snr_db = 10 * np.log10(pattern_snr + 1e-10)

    return {
        'pattern_snr': float(pattern_snr),
        'between_var': float(between_var),
        'within_var': float(within_var),
        'snr_db': float(snr_db)
    }


def compute_glm_snr(amplitudes: np.ndarray, residuals: np.ndarray) -> Dict[str, float]:
    """
    Compute GLM-based SNR: signal variance / noise variance.

    Signal variance: Variance of beta estimates (amplitudes)
    Noise variance: Residual variance from GLM

    Args:
        amplitudes: (n_runs, n_colors, n_voxels) - Beta estimates
        residuals: (n_samples, n_voxels) - GLM residuals

    Returns:
        snr_metrics: Dict with:
            - 'glm_snr': GLM-based SNR
            - 'signal_var': Variance of beta estimates
            - 'noise_var': Residual variance
            - 'snr_db': SNR in decibels
    """
    # Signal variance: Variance of amplitudes across runs and colors
    signal_var = np.var(amplitudes, axis=(0, 1)).mean()  # Average across voxels

    # Noise variance: Residual variance
    noise_var = np.var(residuals, axis=0).mean()  # Average across voxels

    # GLM SNR
    glm_snr = signal_var / (noise_var + 1e-10)

    # SNR in decibels
    snr_db = 10 * np.log10(glm_snr + 1e-10)

    return {
        'glm_snr': float(glm_snr),
        'signal_var': float(signal_var),
        'noise_var': float(noise_var),
        'snr_db': float(snr_db)
    }


def compute_effective_snr(amplitudes: np.ndarray,
                         noise_cov: np.ndarray) -> Dict[str, float]:
    """
    Compute effective SNR considering noise covariance structure.

    Effective SNR = SNR_raw / sqrt(mean_noise_correlation)

    High noise correlation → Lower effective SNR
    Whitening decorrelates noise → Higher effective SNR

    Args:
        amplitudes: (n_runs, n_colors, n_voxels) - Neural patterns
        noise_cov: (n_voxels, n_voxels) - Noise covariance matrix

    Returns:
        snr_metrics: Dict with:
            - 'effective_snr': Effective SNR accounting for noise correlation
            - 'raw_snr': Raw pattern SNR
            - 'noise_correlation': Mean off-diagonal noise correlation
            - 'snr_db': Effective SNR in decibels
    """
    # Raw pattern SNR
    raw_snr_metrics = compute_pattern_snr(amplitudes)
    raw_snr = raw_snr_metrics['pattern_snr']

    # Noise correlation structure
    # Convert covariance to correlation
    std_dev = np.sqrt(np.diag(noise_cov))
    noise_corr_matrix = noise_cov / np.outer(std_dev, std_dev)

    # Mean off-diagonal correlation
    n_voxels = noise_corr_matrix.shape[0]
    mask = ~np.eye(n_voxels, dtype=bool)
    mean_noise_corr = np.abs(noise_corr_matrix[mask]).mean()

    # Effective SNR
    effective_snr = raw_snr / np.sqrt(mean_noise_corr + 1e-10)

    # SNR in decibels
    snr_db = 10 * np.log10(effective_snr + 1e-10)

    return {
        'effective_snr': float(effective_snr),
        'raw_snr': float(raw_snr),
        'noise_correlation': float(mean_noise_corr),
        'snr_db': float(snr_db)
    }


def compare_snr_before_after_whitening(amplitudes_raw: np.ndarray,
                                       amplitudes_whitened: np.ndarray,
                                       residuals: Optional[np.ndarray],
                                       noise_cov: np.ndarray) -> Dict:
    """
    Comprehensive SNR comparison: raw vs whitened data.

    Args:
        amplitudes_raw: (n_runs, n_colors, n_voxels) - Before whitening
        amplitudes_whitened: (n_runs, n_colors, n_voxels) - After whitening
        residuals: (n_samples, n_voxels) or None - GLM residuals (optional)
        noise_cov: (n_voxels, n_voxels) - Noise covariance

    Returns:
        comparison: Dict with SNR metrics before/after and improvements
    """
    # Pattern SNR (always computable)
    pattern_snr_raw = compute_pattern_snr(amplitudes_raw)
    pattern_snr_whitened = compute_pattern_snr(amplitudes_whitened)

    # GLM SNR (only if residuals available)
    if residuals is not None:
        glm_snr_raw = compute_glm_snr(amplitudes_raw, residuals)
        # For whitened data, residuals should also be whitened
        # But we use raw residuals as reference
        glm_snr_whitened = compute_glm_snr(amplitudes_whitened, residuals)
    else:
        glm_snr_raw = None
        glm_snr_whitened = None

    # Effective SNR
    effective_snr_raw = compute_effective_snr(amplitudes_raw, noise_cov)

    # After whitening, noise should be decorrelated (identity covariance)
    n_voxels = amplitudes_whitened.shape[2]
    noise_cov_whitened = np.eye(n_voxels)  # Theoretical identity after whitening
    effective_snr_whitened = compute_effective_snr(amplitudes_whitened, noise_cov_whitened)

    comparison = {
        'pattern_snr': {
            'raw': pattern_snr_raw,
            'whitened': pattern_snr_whitened,
            'improvement': pattern_snr_whitened['pattern_snr'] - pattern_snr_raw['pattern_snr'],
            'improvement_pct': (pattern_snr_whitened['pattern_snr'] / pattern_snr_raw['pattern_snr'] - 1) * 100
        },
        'effective_snr': {
            'raw': effective_snr_raw,
            'whitened': effective_snr_whitened,
            'improvement': effective_snr_whitened['effective_snr'] - effective_snr_raw['effective_snr'],
            'improvement_pct': (effective_snr_whitened['effective_snr'] / effective_snr_raw['effective_snr'] - 1) * 100
        }
    }

    # Add GLM SNR only if residuals available
    if glm_snr_raw is not None:
        comparison['glm_snr'] = {
            'raw': glm_snr_raw,
            'whitened': glm_snr_whitened,
            'improvement': glm_snr_whitened['glm_snr'] - glm_snr_raw['glm_snr'],
            'improvement_pct': (glm_snr_whitened['glm_snr'] / glm_snr_raw['glm_snr'] - 1) * 100
        }

    print("\n=== SNR Comparison: Raw vs Whitened ===")
    print(f"Pattern SNR:    {pattern_snr_raw['pattern_snr']:.3f} → {pattern_snr_whitened['pattern_snr']:.3f} "
          f"({comparison['pattern_snr']['improvement_pct']:+.1f}%)")
    if glm_snr_raw is not None:
        print(f"GLM SNR:        {glm_snr_raw['glm_snr']:.3f} → {glm_snr_whitened['glm_snr']:.3f} "
              f"({comparison['glm_snr']['improvement_pct']:+.1f}%)")
    else:
        print(f"GLM SNR:        N/A (residuals not available)")
    print(f"Effective SNR:  {effective_snr_raw['effective_snr']:.3f} → {effective_snr_whitened['effective_snr']:.3f} "
          f"({comparison['effective_snr']['improvement_pct']:+.1f}%)")

    return comparison


def visualize_snr_comparison(snr_comparison: Dict,
                             output_path: str,
                             figsize: Tuple[int, int] = (12, 5)) -> None:
    """
    Visualize SNR comparison before/after whitening.

    Args:
        snr_comparison: Output from compare_snr_before_after_whitening()
        output_path: Path to save figure
        figsize: Figure size
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

    # SNR values
    snr_types = ['Pattern\nSNR', 'GLM\nSNR', 'Effective\nSNR']
    raw_values = [
        snr_comparison['pattern_snr']['raw']['pattern_snr'],
        snr_comparison['glm_snr']['raw']['glm_snr'],
        snr_comparison['effective_snr']['raw']['effective_snr']
    ]
    whitened_values = [
        snr_comparison['pattern_snr']['whitened']['pattern_snr'],
        snr_comparison['glm_snr']['whitened']['glm_snr'],
        snr_comparison['effective_snr']['whitened']['effective_snr']
    ]

    x = np.arange(len(snr_types))
    width = 0.35

    # Bar plot
    bars1 = ax1.bar(x - width/2, raw_values, width, label='Raw', color='coral', alpha=0.8)
    bars2 = ax1.bar(x + width/2, whitened_values, width, label='Whitened', color='steelblue', alpha=0.8)

    ax1.set_xlabel('SNR Metric', fontsize=12, fontweight='bold')
    ax1.set_ylabel('SNR (ratio)', fontsize=12, fontweight='bold')
    ax1.set_title('SNR Comparison: Raw vs Whitened', fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(snr_types)
    ax1.legend(loc='upper left', fontsize=11)
    ax1.grid(axis='y', alpha=0.3, linestyle=':')

    # Annotate improvement percentages
    for i, (raw, whitened) in enumerate(zip(raw_values, whitened_values)):
        improvement_pct = (whitened / raw - 1) * 100
        ax1.text(i, max(raw, whitened) * 1.05, f'+{improvement_pct:.1f}%',
                ha='center', va='bottom', fontsize=10, fontweight='bold', color='green')

    # Improvement percentages
    improvements = [
        snr_comparison['pattern_snr']['improvement_pct'],
        snr_comparison['glm_snr']['improvement_pct'],
        snr_comparison['effective_snr']['improvement_pct']
    ]

    colors = ['green' if imp > 0 else 'red' for imp in improvements]
    bars = ax2.barh(snr_types, improvements, color=colors, alpha=0.7)

    ax2.set_xlabel('SNR Improvement (%)', fontsize=12, fontweight='bold')
    ax2.set_title('Whitening Effect on SNR', fontsize=14, fontweight='bold')
    ax2.axvline(0, color='black', linewidth=1)
    ax2.grid(axis='x', alpha=0.3, linestyle=':')

    # Annotate values
    for i, (bar, val) in enumerate(zip(bars, improvements)):
        ax2.text(val + 1 if val > 0 else val - 1, i,
                f'{val:+.1f}%',
                ha='left' if val > 0 else 'right',
                va='center', fontsize=10, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved SNR comparison visualization to {output_path}")


def load_residuals_from_baseline(baseline_dir: str,
                                 residual_type: str = '2nd_level') -> np.ndarray:
    """
    Load GLM residuals from baseline reconstruction output.

    Args:
        baseline_dir: Path to baseline output directory
        residual_type: '1st_level' or '2nd_level'

    Returns:
        residuals: (n_samples, n_voxels) - GLM residuals
    """
    import os

    if residual_type == '1st_level':
        residuals_path = os.path.join(baseline_dir, 'residuals_1st_level.npy')
    elif residual_type == '2nd_level':
        residuals_path = os.path.join(baseline_dir, 'residuals_2nd_level.npy')
    else:
        raise ValueError(f"Unknown residual_type: {residual_type}")

    if not os.path.exists(residuals_path):
        raise FileNotFoundError(f"Residuals not found: {residuals_path}\n"
                               f"Re-run baseline pipeline with residual saving enabled.")

    residuals = np.load(residuals_path, allow_pickle=True)

    # Handle dictionary format (2nd level, per-run)
    if isinstance(residuals, np.ndarray) and residuals.dtype == object:
        residuals = residuals.item()  # Convert to dict
        # Concatenate all runs
        residuals = np.vstack([residuals[run] for run in sorted(residuals.keys())])

    print(f"Loaded residuals from {residuals_path}: shape = {residuals.shape}")

    return residuals


if __name__ == '__main__':
    # Test with synthetic data
    print("Testing whitening with synthetic data...")

    np.random.seed(42)
    n_runs = 6
    n_colors = 8
    n_voxels = 50

    # Simulate correlated noise structure
    # Create spatial correlation (neighboring voxels correlated)
    noise_cov_true = np.eye(n_voxels)
    for i in range(n_voxels):
        for j in range(n_voxels):
            # Exponential decay with distance
            noise_cov_true[i, j] = 0.7 ** abs(i - j)

    # Generate noisy amplitudes
    true_patterns = np.random.randn(n_colors, n_voxels)
    amplitudes_raw = np.zeros((n_runs, n_colors, n_voxels))

    for run in range(n_runs):
        # Add correlated noise
        noise = np.random.multivariate_normal(np.zeros(n_voxels), noise_cov_true, size=n_colors)
        amplitudes_raw[run] = true_patterns + noise * 0.5

    # Generate residuals for covariance estimation
    n_samples = 200
    residuals = np.random.multivariate_normal(np.zeros(n_voxels), noise_cov_true, size=n_samples)

    print(f"\nSynthetic data: {n_runs} runs, {n_colors} colors, {n_voxels} voxels")
    print(f"Residuals for noise estimation: {n_samples} samples")

    # Evaluate whitening effect
    results = evaluate_whitening_effect(amplitudes_raw, residuals, metric='correlation')

    print(f"\n=== Test Results ===")
    print(f"True noise structure: Spatial autocorrelation (exponential decay)")
    print(f"Estimated shrinkage: {results['shrinkage']:.3f}")
    print(f"RDM reliability improvement: {results['improvement']:+.3f} ({results['improvement_pct']:+.1f}%)")

    print("\nTest completed successfully!")
