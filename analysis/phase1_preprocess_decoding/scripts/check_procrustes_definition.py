"""
Check what scipy.linalg.orthogonal_procrustes actually returns.

The second return value is often misunderstood!
"""

import numpy as np
from scipy.linalg import orthogonal_procrustes


def test_procrustes_return_values():
    """
    Test what orthogonal_procrustes actually returns.
    """
    print("="*80)
    print("Testing scipy.linalg.orthogonal_procrustes Return Values")
    print("="*80)

    # Create simple test matrices
    np.random.seed(42)
    A = np.random.randn(10, 5)  # (M, N)
    B = np.random.randn(10, 5)  # (M, N)

    print(f"\nInput shapes: A={A.shape}, B={B.shape}")

    # Call orthogonal_procrustes
    R, scale = orthogonal_procrustes(A, B)

    print(f"\nReturned values:")
    print(f"  R shape: {R.shape}")
    print(f"  scale value: {scale:.4f}")

    # Check scipy documentation
    print("\n" + "-"*80)
    print("From scipy documentation:")
    print("-"*80)
    print("""
    orthogonal_procrustes(A, B)

    Returns
    -------
    R : (N, N) ndarray
        The matrix solution of the orthogonal Procrustes problem.
        Minimizes the Frobenius norm of (A @ R - B).
    scale : float
        Sum of the singular values of A.T @ B.

    NOTE: 'scale' is NOT the disparity!
    """)

    # Compute actual disparity (Frobenius norm squared)
    residual = A @ R - B
    disparity_fro_sq = np.linalg.norm(residual, 'fro')**2
    disparity_fro = np.linalg.norm(residual, 'fro')

    print("\n" + "-"*80)
    print("Actual Disparity Calculations:")
    print("-"*80)
    print(f"  Frobenius norm ||A@R - B||_F: {disparity_fro:.4f}")
    print(f"  Frobenius norm squared ||A@R - B||_F^2: {disparity_fro_sq:.4f}")
    print(f"  'scale' from scipy (sum of singular values): {scale:.4f}")

    # Check relationship
    u, s, vt = np.linalg.svd(A.T @ B, full_matrices=False)
    sum_singular_values = np.sum(s)

    print("\n" + "-"*80)
    print("Verification:")
    print("-"*80)
    print(f"  Sum of singular values of A.T @ B: {sum_singular_values:.4f}")
    print(f"  'scale' from scipy: {scale:.4f}")
    print(f"  Match: {np.allclose(scale, sum_singular_values)}")

    # Normalized Frobenius norm (common in Procrustes literature)
    norm_B = np.linalg.norm(B, 'fro')
    normalized_disparity = disparity_fro / norm_B

    print("\n" + "-"*80)
    print("Normalized Disparity (literature standard):")
    print("-"*80)
    print(f"  ||B||_F: {norm_B:.4f}")
    print(f"  Normalized disparity: {disparity_fro / norm_B:.4f}")
    print(f"  Normalized disparity squared: {disparity_fro_sq / (norm_B**2):.4f}")

    return {
        'scale_from_scipy': scale,
        'disparity_frobenius': disparity_fro,
        'disparity_frobenius_sq': disparity_fro_sq,
        'normalized_disparity': normalized_disparity
    }


def test_with_normalized_data():
    """
    Test with centered and scaled data (like our actual analysis).
    """
    print("\n" + "="*80)
    print("Testing with Centered & Scaled Data (Our Actual Case)")
    print("="*80)

    np.random.seed(42)

    # Simulate our data: (n_colors, n_voxels)
    n_colors = 8
    n_voxels = 129

    subject_pattern = np.random.randn(n_colors, n_voxels)
    ref_pattern = np.random.randn(n_colors, n_voxels)

    print(f"\nOriginal shapes: ({n_colors}, {n_voxels})")

    # Our normalization procedure
    subject_centered = subject_pattern - subject_pattern.mean()
    ref_centered = ref_pattern - ref_pattern.mean()

    subject_normalized = subject_centered / np.std(subject_centered)
    ref_normalized = ref_centered / np.std(ref_centered)

    print(f"\nAfter centering and scaling:")
    print(f"  Subject mean: {subject_normalized.mean():.6f}, std: {np.std(subject_normalized):.6f}")
    print(f"  Reference mean: {ref_normalized.mean():.6f}, std: {np.std(ref_normalized):.6f}")

    # Our current code (TRANSPOSED)
    R, scale = orthogonal_procrustes(subject_normalized.T, ref_normalized.T)

    print(f"\nWith transpose (current code):")
    print(f"  Input to scipy: ({n_voxels}, {n_colors})")
    print(f"  R shape: {R.shape}  # Rotation in color space!")
    print(f"  'scale' from scipy: {scale:.4f}")

    # Compute actual disparity
    residual = subject_normalized.T @ R - ref_normalized.T
    disparity_current = np.linalg.norm(residual, 'fro')**2

    print(f"  Actual disparity (Fro^2): {disparity_current:.4f}")

    # Without transpose (correct?)
    R_correct, scale_correct = orthogonal_procrustes(subject_normalized, ref_normalized)

    print(f"\nWithout transpose (voxel space rotation):")
    print(f"  Input to scipy: ({n_colors}, {n_voxels})")
    print(f"  R shape: {R_correct.shape}  # Rotation in voxel space!")
    print(f"  'scale' from scipy: {scale_correct:.4f}")

    # Compute actual disparity
    residual_correct = subject_normalized @ R_correct - ref_normalized
    disparity_correct = np.linalg.norm(residual_correct, 'fro')**2

    print(f"  Actual disparity (Fro^2): {disparity_correct:.4f}")

    print("\n" + "-"*80)
    print("CRITICAL FINDING:")
    print("-"*80)
    print(f"  We've been using 'scale' = {scale:.4f}")
    print(f"  Actual disparity should be = {disparity_current:.4f}")
    print(f"  Ratio (scale / disparity): {scale / disparity_current:.4f}")

    return {
        'scale_current': scale,
        'disparity_current': disparity_current,
        'scale_correct': scale_correct,
        'disparity_correct': disparity_correct
    }


if __name__ == '__main__':
    # Test 1: Basic understanding
    results1 = test_procrustes_return_values()

    # Test 2: Our actual case
    results2 = test_with_normalized_data()

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print("""
    CRITICAL ERROR IDENTIFIED:

    We've been using 'scale' (sum of singular values) as disparity!

    Correct disparity = ||A @ R - B||_F^2

    This could COMPLETELY change our results!
    """)
    print("="*80)
