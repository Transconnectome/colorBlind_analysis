"""
Residual quality analysis utilities.

Computes metrics to assess temporal drift and residual quality:
1. Temporal autocorrelation (lag-1): High values indicate drift
2. Mean squared residuals: Overall quality check
3. Drift magnitude: Linear trend slope per voxel
4. Residual variance per run: Session stability
"""

import numpy as np
from scipy.stats import pearsonr


def compute_temporal_autocorrelation(amplitudes):
    """
    Compute lag-1 autocorrelation per voxel-color combination.

    High autocorrelation indicates temporal drift (successive runs are similar).
    Low autocorrelation indicates better temporal independence.

    Args:
        amplitudes: (n_runs, n_colors, n_voxels) - Neural response patterns

    Returns:
        results: Dict with keys:
            - 'mean': Mean autocorrelation across all voxel-color combinations
            - 'std': Standard deviation
            - 'per_color': (n_colors,) - Mean autocorr per color
            - 'distribution': (n_colors * n_voxels,) - All autocorrelations
    """
    n_runs, n_colors, n_voxels = amplitudes.shape

    if n_runs < 3:
        raise ValueError(f"Need at least 3 runs for autocorrelation, got {n_runs}")

    autocorrs = []
    per_color_autocorrs = np.zeros(n_colors)

    for color_idx in range(n_colors):
        color_autocorrs = []
        for voxel_idx in range(n_voxels):
            # Extract timeseries: (n_runs,)
            timeseries = amplitudes[:, color_idx, voxel_idx]

            # Lag-1 autocorrelation: corr(t, t+1)
            if len(timeseries) > 1:
                # Pearson correlation between t[:-1] and t[1:]
                r, _ = pearsonr(timeseries[:-1], timeseries[1:])
                autocorrs.append(r)
                color_autocorrs.append(r)

        per_color_autocorrs[color_idx] = np.mean(color_autocorrs)

    autocorrs = np.array(autocorrs)
    autocorrs = autocorrs[np.isfinite(autocorrs)]  # Remove NaN/Inf

    return {
        'mean': np.mean(autocorrs),
        'std': np.std(autocorrs),
        'per_color': per_color_autocorrs,
        'distribution': autocorrs
    }


def compute_mse_residuals(amplitudes):
    """
    Compute mean squared residuals from grand mean.

    MSE = mean((amplitudes - grand_mean)^2)

    Lower MSE indicates more consistent patterns across runs.

    Args:
        amplitudes: (n_runs, n_colors, n_voxels) - Neural response patterns

    Returns:
        results: Dict with keys:
            - 'overall': Overall MSE
            - 'per_run': (n_runs,) - MSE per run
            - 'per_color': (n_colors,) - MSE per color
    """
    # Grand mean across all runs
    grand_mean = amplitudes.mean(axis=0)  # (n_colors, n_voxels)

    # Residuals
    residuals = amplitudes - grand_mean[None, :, :]

    # MSE
    mse_overall = np.mean(residuals ** 2)
    mse_per_run = np.mean(residuals ** 2, axis=(1, 2))  # (n_runs,)
    mse_per_color = np.mean(residuals ** 2, axis=(0, 2))  # (n_colors,)

    return {
        'overall': mse_overall,
        'per_run': mse_per_run,
        'per_color': mse_per_color
    }


def compute_drift_magnitude(amplitudes):
    """
    Compute linear drift magnitude per voxel-color combination.

    Fits linear trend to each timeseries and computes slope magnitude.
    Higher magnitude indicates stronger temporal drift.

    Args:
        amplitudes: (n_runs, n_colors, n_voxels) - Neural response patterns

    Returns:
        results: Dict with keys:
            - 'mean_abs_slope': Mean absolute slope across all voxel-color combinations
            - 'std_abs_slope': Standard deviation
            - 'per_color': (n_colors,) - Mean abs slope per color
            - 'distribution': (n_colors * n_voxels,) - All slopes
    """
    n_runs, n_colors, n_voxels = amplitudes.shape

    x = np.arange(n_runs)
    slopes = []
    per_color_slopes = np.zeros(n_colors)

    for color_idx in range(n_colors):
        color_slopes = []
        for voxel_idx in range(n_voxels):
            # Extract timeseries: (n_runs,)
            timeseries = amplitudes[:, color_idx, voxel_idx]

            # Fit linear trend: y = slope * x + intercept
            slope, _ = np.polyfit(x, timeseries, 1)
            slopes.append(abs(slope))
            color_slopes.append(abs(slope))

        per_color_slopes[color_idx] = np.mean(color_slopes)

    slopes = np.array(slopes)

    return {
        'mean_abs_slope': np.mean(slopes),
        'std_abs_slope': np.std(slopes),
        'per_color': per_color_slopes,
        'distribution': slopes
    }


def compute_residual_variance_per_run(amplitudes):
    """
    Compute residual variance per run (stability across session).

    Variance of residuals from grand mean, computed per run.
    Increasing variance across runs indicates instability.

    Args:
        amplitudes: (n_runs, n_colors, n_voxels) - Neural response patterns

    Returns:
        results: Dict with keys:
            - 'per_run': (n_runs,) - Variance per run
            - 'mean': Mean variance across runs
            - 'std': Standard deviation
            - 'trend_slope': Slope of variance trend (positive = increasing instability)
    """
    grand_mean = amplitudes.mean(axis=0)  # (n_colors, n_voxels)
    residuals = amplitudes - grand_mean[None, :, :]

    # Variance per run
    var_per_run = np.var(residuals, axis=(1, 2))  # (n_runs,)

    # Trend in variance
    n_runs = len(var_per_run)
    x = np.arange(n_runs)
    trend_slope, _ = np.polyfit(x, var_per_run, 1)

    return {
        'per_run': var_per_run,
        'mean': np.mean(var_per_run),
        'std': np.std(var_per_run),
        'trend_slope': trend_slope
    }


def compute_residual_metrics(amplitudes):
    """
    Comprehensive wrapper for all residual quality metrics.

    Args:
        amplitudes: (n_runs, n_colors, n_voxels) - Neural response patterns

    Returns:
        metrics: Dict with all residual quality metrics:
            - 'temporal_autocorrelation': Lag-1 autocorr results
            - 'mse_residuals': MSE results
            - 'drift_magnitude': Linear slope results
            - 'residual_variance': Variance stability results
    """
    return {
        'temporal_autocorrelation': compute_temporal_autocorrelation(amplitudes),
        'mse_residuals': compute_mse_residuals(amplitudes),
        'drift_magnitude': compute_drift_magnitude(amplitudes),
        'residual_variance': compute_residual_variance_per_run(amplitudes)
    }


if __name__ == '__main__':
    # Test with synthetic data
    print("Testing residual analysis utilities...")

    np.random.seed(42)
    n_runs, n_colors, n_voxels = 6, 8, 10

    # Create synthetic data with drift
    base_patterns = np.random.randn(n_colors, n_voxels)
    drift = np.linspace(0, 1, n_runs)[:, None, None]
    amplitudes = base_patterns[None, :, :] + drift + np.random.randn(n_runs, n_colors, n_voxels) * 0.1

    print(f"\nAmplitudes shape: {amplitudes.shape}")
    print(f"Run means (expect increasing): {amplitudes.mean(axis=(1,2))}")

    # Test all metrics
    print("\n=== Temporal Autocorrelation ===")
    autocorr = compute_temporal_autocorrelation(amplitudes)
    print(f"Mean: {autocorr['mean']:.3f} (high = drift)")
    print(f"Std: {autocorr['std']:.3f}")
    print(f"Per color: {autocorr['per_color']}")

    print("\n=== MSE Residuals ===")
    mse = compute_mse_residuals(amplitudes)
    print(f"Overall: {mse['overall']:.3f}")
    print(f"Per run: {mse['per_run']}")

    print("\n=== Drift Magnitude ===")
    drift_mag = compute_drift_magnitude(amplitudes)
    print(f"Mean abs slope: {drift_mag['mean_abs_slope']:.3f} (high = drift)")
    print(f"Per color: {drift_mag['per_color']}")

    print("\n=== Residual Variance ===")
    var = compute_residual_variance_per_run(amplitudes)
    print(f"Per run: {var['per_run']}")
    print(f"Trend slope: {var['trend_slope']:.4f} (positive = instability)")

    print("\n=== Comprehensive Metrics ===")
    metrics = compute_residual_metrics(amplitudes)
    print(f"Autocorr mean: {metrics['temporal_autocorrelation']['mean']:.3f}")
    print(f"MSE overall: {metrics['mse_residuals']['overall']:.3f}")
    print(f"Drift magnitude: {metrics['drift_magnitude']['mean_abs_slope']:.3f}")
    print(f"Variance trend: {metrics['residual_variance']['trend_slope']:.4f}")

    print("\nResidual analysis utilities test completed!")
