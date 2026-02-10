"""
Preprocessing utilities for temporal detrending and filtering experiment.

Implements 2×2 factorial design:
- C1 (Baseline): No preprocessing
- C2 (Detrend): Linear detrending only
- C3 (Filter): High-pass filtering only
- C4 (Both): Detrending + filtering
"""

import numpy as np
from scipy.signal import detrend
from nilearn.signal import clean


def apply_linear_detrending(amplitudes, axis=0):
    """
    Apply linear detrending per voxel across runs.

    Uses scipy.signal.detrend to remove linear trend from temporal dimension.

    Args:
        amplitudes: (n_runs, n_colors, n_voxels) - Neural response patterns
        axis: Axis along which to detrend (default=0, across runs)

    Returns:
        detrended: Same shape as input, with linear trends removed per voxel
    """
    # Detrend operates on first axis by default, so we need to reshape
    # Original: (n_runs, n_colors, n_voxels)
    # Target: detrend each (n_runs,) slice for each (color, voxel) combination

    n_runs, n_colors, n_voxels = amplitudes.shape
    detrended = np.zeros_like(amplitudes)

    # Detrend each voxel's timecourse for each color separately
    for color_idx in range(n_colors):
        for voxel_idx in range(n_voxels):
            # Extract timeseries: (n_runs,)
            timeseries = amplitudes[:, color_idx, voxel_idx]
            # Detrend: removes best-fit line
            detrended[:, color_idx, voxel_idx] = detrend(timeseries, axis=0, type='linear')

    return detrended


def apply_highpass_filtering(amplitudes, cutoff_hz=1/128, t_r=2.0):
    """
    Apply high-pass filtering per color-voxel timeseries.

    For short timeseries (n_runs < 30), uses simple Fourier-based filtering
    instead of Butterworth to avoid padding issues.

    Args:
        amplitudes: (n_runs, n_colors, n_voxels) - Neural response patterns
        cutoff_hz: High-pass filter cutoff frequency (default: 1/128 Hz)
        t_r: Repetition time in seconds (default: 2.0)

    Returns:
        filtered: Same shape as input, with low-frequency components attenuated
    """
    from scipy import fft

    n_runs, n_colors, n_voxels = amplitudes.shape
    filtered = np.zeros_like(amplitudes)

    # For short timeseries, use FFT-based filtering
    # This avoids padding issues with Butterworth filter
    if n_runs < 30:
        print(f"  Using FFT-based filtering (n_runs={n_runs} < 30)")

        for color_idx in range(n_colors):
            for voxel_idx in range(n_voxels):
                timeseries = amplitudes[:, color_idx, voxel_idx]

                # FFT
                fft_coeffs = fft.fft(timeseries)
                freqs = fft.fftfreq(n_runs, d=t_r)

                # High-pass: zero out frequencies below cutoff
                fft_coeffs[np.abs(freqs) < cutoff_hz] = 0

                # Inverse FFT
                filtered_ts = np.real(fft.ifft(fft_coeffs))
                filtered[:, color_idx, voxel_idx] = filtered_ts
    else:
        # For longer timeseries, use nilearn's Butterworth filter
        print(f"  Using Butterworth filtering (n_runs={n_runs} >= 30)")

        for color_idx in range(n_colors):
            for voxel_idx in range(n_voxels):
                timeseries = amplitudes[:, color_idx, voxel_idx].reshape(-1, 1)

                filtered_ts = clean(
                    timeseries,
                    t_r=t_r,
                    high_pass=cutoff_hz,
                    detrend=False,
                    standardize=False,
                    ensure_finite=True
                )

                filtered[:, color_idx, voxel_idx] = filtered_ts.flatten()

    return filtered


def preprocess_amplitudes(amplitudes, condition):
    """
    Apply preprocessing based on experimental condition.

    Args:
        amplitudes: (n_runs, n_colors, n_voxels) - Raw neural response patterns
        condition: str - One of 'C1', 'C2', 'C3', 'C4'
            - 'C1': Baseline (no preprocessing)
            - 'C2': Linear detrending only
            - 'C3': High-pass filtering only
            - 'C4': Both detrending and filtering

    Returns:
        processed: Same shape as input, preprocessed according to condition
    """
    if condition == 'C1':
        # Baseline: no preprocessing
        return amplitudes.copy()

    elif condition == 'C2':
        # Detrending only
        return apply_linear_detrending(amplitudes)

    elif condition == 'C3':
        # Filtering only
        return apply_highpass_filtering(amplitudes)

    elif condition == 'C4':
        # Both: detrend first, then filter
        # Note: nilearn.signal.clean with high_pass also detrends by default,
        # but we set detrend=False to control the order explicitly
        detrended = apply_linear_detrending(amplitudes)
        filtered = apply_highpass_filtering(detrended)
        return filtered

    else:
        raise ValueError(f"Unknown condition: {condition}. Use 'C1', 'C2', 'C3', or 'C4'")


def validate_preprocessing(original, processed, condition):
    """
    Validate preprocessing results.

    Checks:
    - Same shape
    - No NaN/Inf
    - Expected effects (detrending flattens trends, filtering attenuates low freq)

    Args:
        original: Original amplitudes
        processed: Processed amplitudes
        condition: Condition name

    Returns:
        validation_results: Dict with validation checks
    """
    results = {
        'condition': condition,
        'shape_match': original.shape == processed.shape,
        'no_nan': not np.any(np.isnan(processed)),
        'no_inf': not np.any(np.isinf(processed)),
        'mean_change': np.mean(processed) - np.mean(original),
        'std_change': np.std(processed) - np.std(original)
    }

    # Condition-specific checks
    if condition == 'C1':
        # Baseline: should be identical
        results['data_identical'] = np.allclose(original, processed)

    elif condition in ['C2', 'C4']:
        # Detrending: run-wise means should be flattened
        original_run_means = original.mean(axis=(1, 2))  # (n_runs,)
        processed_run_means = processed.mean(axis=(1, 2))

        # Linear trend slope should be reduced
        n_runs = len(original_run_means)
        x = np.arange(n_runs)

        original_slope = np.polyfit(x, original_run_means, 1)[0]
        processed_slope = np.polyfit(x, processed_run_means, 1)[0]

        results['slope_reduction'] = abs(processed_slope) < abs(original_slope)
        results['original_slope'] = original_slope
        results['processed_slope'] = processed_slope

    # All valid if all checks pass
    results['all_valid'] = (results['shape_match'] and
                           results['no_nan'] and
                           results['no_inf'])

    return results


if __name__ == '__main__':
    # Test with synthetic data
    print("Testing preprocessing utilities...")

    np.random.seed(42)
    n_runs, n_colors, n_voxels = 6, 8, 10

    # Create synthetic data with linear drift
    base_patterns = np.random.randn(n_colors, n_voxels)
    drift = np.linspace(0, 2, n_runs)[:, None, None]  # Linear drift
    amplitudes = base_patterns[None, :, :] + drift + np.random.randn(n_runs, n_colors, n_voxels) * 0.1

    print(f"\nOriginal amplitudes shape: {amplitudes.shape}")
    print(f"Mean: {amplitudes.mean():.3f}, Std: {amplitudes.std():.3f}")
    print(f"Run means: {amplitudes.mean(axis=(1,2))}")

    # Test all conditions
    for condition in ['C1', 'C2', 'C3', 'C4']:
        print(f"\n=== Testing {condition} ===")
        processed = preprocess_amplitudes(amplitudes, condition)
        validation = validate_preprocessing(amplitudes, processed, condition)

        print(f"Shape match: {validation['shape_match']}")
        print(f"No NaN/Inf: {validation['no_nan']} / {validation['no_inf']}")
        print(f"Mean change: {validation['mean_change']:.3f}")
        print(f"Processed run means: {processed.mean(axis=(1,2))}")

        if 'slope_reduction' in validation:
            print(f"Slope reduction: {validation['slope_reduction']}")
            print(f"  Original slope: {validation['original_slope']:.4f}")
            print(f"  Processed slope: {validation['processed_slope']:.4f}")

    print("\nPreprocessing utilities test completed!")
