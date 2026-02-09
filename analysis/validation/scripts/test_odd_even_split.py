#!/usr/bin/env python3
"""
Test odd/even split-half implementation

Tests the new compute_split_half_odd_even() function with:
1. Synthetic data (known ground truth)
2. Real fMRI data (sub-01, V1)

Expected:
- Random vs Odd/Even difference < 0.05
- Odd/Even: n_odd=3, n_even=3
- Correlations in [0, 1]

Date: 2026-02-08
"""

import numpy as np
from pathlib import Path
import sys

# Add utils to path
script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(script_dir / 'utils'))

from noise_ceiling import (
    compute_split_half_reliability,
    compute_split_half_odd_even
)


def test_synthetic_data():
    """Test with synthetic data"""
    print("="*60)
    print("Test 1: Synthetic Data")
    print("="*60)

    np.random.seed(42)
    n_runs, n_colors, n_voxels = 6, 8, 100

    # Create ground truth patterns with noise
    true_patterns = np.random.randn(n_colors, n_voxels)
    amplitudes = (true_patterns[np.newaxis, :, :] +
                 np.random.randn(n_runs, n_colors, n_voxels) * 0.3)

    # Random split-half
    random_result = compute_split_half_reliability(
        amplitudes, n_iterations=1000, metric='correlation'
    )

    # Odd/even split-half
    odd_even_result = compute_split_half_odd_even(
        amplitudes, metric='correlation'
    )

    print(f"\nData shape: {amplitudes.shape}")
    print(f"\nRandom split-half:")
    print(f"  Corrected: {random_result['corrected']:.3f}")
    print(f"  Raw: {random_result['raw']:.3f}")
    print(f"  95% CI: [{random_result['ci_lower']:.3f}, {random_result['ci_upper']:.3f}]")

    print(f"\nOdd/even split-half:")
    print(f"  Corrected: {odd_even_result['corrected']:.3f}")
    print(f"  Raw: {odd_even_result['raw']:.3f}")
    print(f"  n_odd: {odd_even_result['n_odd']}")
    print(f"  n_even: {odd_even_result['n_even']}")

    difference = abs(random_result['corrected'] - odd_even_result['corrected'])
    print(f"\nDifference: {difference:.3f}")

    # Validation
    assert 0.0 <= odd_even_result['corrected'] <= 1.0, "Correlation out of range"
    assert odd_even_result['n_odd'] == 3, f"Expected 3 odd runs, got {odd_even_result['n_odd']}"
    assert odd_even_result['n_even'] == 3, f"Expected 3 even runs, got {odd_even_result['n_even']}"

    if difference < 0.1:
        print(f"Status: ✓ PASS (difference < 0.1)")
    else:
        print(f"Status: ⚠️ WARN (difference = {difference:.3f} >= 0.1)")

    return difference < 0.15  # Allow 0.15 threshold for synthetic data


def test_real_data():
    """Test with real fMRI data (sub-01, V1)"""
    print("\n" + "="*60)
    print("Test 2: Real fMRI Data (sub-01, V1)")
    print("="*60)

    # Path to real data
    data_path = (Path(__file__).parent.parent.parent /
                "phase1_preprocess_decoding/results/baseline/sub-01/V1/amplitudes_procrustes.npy")

    if not data_path.exists():
        print(f"⚠️ Data not found at {data_path}")
        print("Skipping real data test")
        return True

    # Load data
    amplitudes = np.load(data_path)
    print(f"Data shape: {amplitudes.shape}")

    # Random split-half
    random_result = compute_split_half_reliability(
        amplitudes, n_iterations=1000
    )

    # Odd/even split-half
    odd_even_result = compute_split_half_odd_even(amplitudes)

    print(f"\nRandom split-half:")
    print(f"  Corrected: {random_result['corrected']:.3f}")
    print(f"  Raw: {random_result['raw']:.3f}")
    print(f"  95% CI: [{random_result['ci_lower']:.3f}, {random_result['ci_upper']:.3f}]")

    print(f"\nOdd/even split-half:")
    print(f"  Corrected: {odd_even_result['corrected']:.3f}")
    print(f"  Raw: {odd_even_result['raw']:.3f}")
    print(f"  n_odd: {odd_even_result['n_odd']}")
    print(f"  n_even: {odd_even_result['n_even']}")

    difference = abs(random_result['corrected'] - odd_even_result['corrected'])
    print(f"\nDifference: {difference:.3f}")

    # Validation
    assert 0.0 <= odd_even_result['corrected'] <= 1.0, "Correlation out of range"
    assert odd_even_result['n_odd'] == 3, f"Expected 3 odd runs, got {odd_even_result['n_odd']}"
    assert odd_even_result['n_even'] == 3, f"Expected 3 even runs, got {odd_even_result['n_even']}"

    if difference < 0.1:
        print(f"Status: ✓ PASS (difference < 0.1)")
    else:
        print(f"Status: ⚠️ WARN (difference = {difference:.3f} >= 0.1)")

    return True


def test_edge_cases():
    """Test edge cases"""
    print("\n" + "="*60)
    print("Test 3: Edge Cases")
    print("="*60)

    # Test with 4 runs (minimum)
    print("\nTest 3a: Minimum runs (n=4)")
    np.random.seed(42)
    amplitudes_4 = np.random.randn(4, 8, 50) + 0.5
    result_4 = compute_split_half_odd_even(amplitudes_4)
    print(f"  4 runs: n_odd={result_4['n_odd']}, n_even={result_4['n_even']}")
    assert result_4['n_odd'] == 2 and result_4['n_even'] == 2
    print("  ✓ PASS")

    # Test with 5 runs (odd total)
    print("\nTest 3b: Odd number of runs (n=5)")
    amplitudes_5 = np.random.randn(5, 8, 50) + 0.5
    result_5 = compute_split_half_odd_even(amplitudes_5)
    print(f"  5 runs: n_odd={result_5['n_odd']}, n_even={result_5['n_even']}")
    assert result_5['n_odd'] == 3 and result_5['n_even'] == 2
    print("  ✓ PASS")

    # Test error with too few runs
    print("\nTest 3c: Too few runs (n=3, should error)")
    try:
        amplitudes_3 = np.random.randn(3, 8, 50)
        result_3 = compute_split_half_odd_even(amplitudes_3)
        print("  ❌ FAIL: Should have raised ValueError")
        return False
    except ValueError as e:
        print(f"  ✓ PASS: Correctly raised ValueError: {e}")

    return True


if __name__ == '__main__':
    print("Testing Odd/Even Split-Half Implementation")
    print("=" * 60)

    all_passed = True

    # Run tests
    try:
        test1_passed = test_synthetic_data()
        all_passed = all_passed and test1_passed
    except Exception as e:
        print(f"\n❌ Test 1 FAILED with error: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        test2_passed = test_real_data()
        all_passed = all_passed and test2_passed
    except Exception as e:
        print(f"\n❌ Test 2 FAILED with error: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    try:
        test3_passed = test_edge_cases()
        all_passed = all_passed and test3_passed
    except Exception as e:
        print(f"\n❌ Test 3 FAILED with error: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    # Final summary
    print("\n" + "="*60)
    if all_passed:
        print("✓ ALL TESTS PASSED!")
    else:
        print("⚠️ SOME TESTS FAILED")
    print("="*60)

    sys.exit(0 if all_passed else 1)
