#!/usr/bin/env python3
"""
Step 1a: PCA Dimension Reduction (RECOMMENDED)

Implements PCA-based dimension reduction following Brouwer & Heeger (2009).
- Preserves representational geometry (orthogonal transformation)
- All voxels contribute via weighted sum
- Uniform dimensionality across subjects

Usage:
    python step1a_dimension_reduction_pca.py --subject 01 --roi V1 --n-components 50
"""

import argparse
import json
import numpy as np
from pathlib import Path
from sklearn.decomposition import PCA
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))


def pca_dimension_reduction(amplitudes_z, n_components=50):
    """
    PCA-based dimension reduction following Brouwer & Heeger (2009).

    Args:
        amplitudes_z: (6, 8, n_voxels) z-scored amplitudes
        n_components: Number of principal components (default 50)

    Returns:
        odd_pc: (8, n_components) odd runs in PC space
        even_pc: (8, n_components) even runs in PC space
        pca_model: Fitted PCA object
        explained_variance_ratio: (n_components,) variance explained
    """
    n_runs, n_colors, n_voxels = amplitudes_z.shape

    print(f"  Input shape: {amplitudes_z.shape}")
    print(f"  n_voxels: {n_voxels}, target n_components: {n_components}")

    # Step 1: Run averaging (denoise before PCA)
    odd_runs = amplitudes_z[[0, 2, 4], :, :]  # runs 1,3,5 → (3, 8, n_voxels)
    even_runs = amplitudes_z[[1, 3, 5], :, :]  # runs 2,4,6 → (3, 8, n_voxels)

    odd_pattern = odd_runs.mean(axis=0)  # (8, n_voxels)
    even_pattern = even_runs.mean(axis=0)  # (8, n_voxels)

    print(f"  Run-averaged patterns: odd={odd_pattern.shape}, even={even_pattern.shape}")

    # Step 2: Fit PCA on concatenated patterns
    patterns_all = np.vstack([odd_pattern, even_pattern])  # (16, n_voxels)

    # Ensure n_components doesn't exceed available dimensions
    n_components_actual = min(n_components, n_voxels, patterns_all.shape[0])

    print(f"  Fitting PCA with {n_components_actual} components...")
    pca = PCA(n_components=n_components_actual)
    pca.fit(patterns_all)

    # Step 3: Transform to PC space
    odd_pc = pca.transform(odd_pattern)  # (8, n_components_actual)
    even_pc = pca.transform(even_pattern)  # (8, n_components_actual)

    print(f"  Output PC shape: {odd_pc.shape}")
    print(f"  Explained variance (first 5 PCs): {pca.explained_variance_ratio_[:5]}")
    print(f"  Cumulative variance (all PCs): {pca.explained_variance_ratio_.sum():.4f}")

    return odd_pc, even_pc, pca, pca.explained_variance_ratio_


def validate_pca_output(odd_pc, even_pc, explained_variance_ratio, n_components):
    """
    Validate PCA output quality.

    Returns:
        dict: Validation metrics
    """
    validation = {
        'shape_valid': odd_pc.shape == even_pc.shape,
        'n_components_actual': odd_pc.shape[1],
        'cumulative_variance': float(explained_variance_ratio.sum()),
        'first_pc_variance': float(explained_variance_ratio[0]),
        'variance_threshold_80pct': float(explained_variance_ratio.sum()) > 0.8,
        'no_negative_eigenvalues': np.all(explained_variance_ratio >= 0),
    }

    print("\n=== PCA Validation ===")
    print(f"  Shape valid: {validation['shape_valid']}")
    print(f"  Components: {validation['n_components_actual']}/{n_components} (requested)")
    print(f"  Cumulative variance: {validation['cumulative_variance']:.4f}")
    print(f"  First PC variance: {validation['first_pc_variance']:.4f}")
    print(f"  >80% variance: {validation['variance_threshold_80pct']}")
    print(f"  No negative eigenvalues: {validation['no_negative_eigenvalues']}")

    return validation


def main():
    parser = argparse.ArgumentParser(description='Step 1a: PCA Dimension Reduction')
    parser.add_argument('--subject', type=str, required=True, help='Subject ID (e.g., 01)')
    parser.add_argument('--roi', type=str, required=True, help='ROI name (V1, V2, V3, hV4)')
    parser.add_argument('--n-components', type=int, default=50, help='Number of PCs (default: 50)')
    parser.add_argument('--baseline-dir', type=str,
                        default='/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase1_preprocess_decoding/results/baseline',
                        help='Path to baseline results directory')
    parser.add_argument('--output-dir', type=str,
                        default='/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/validation/scripts/postSRM_procrus/results/step1_pca',
                        help='Output directory')

    args = parser.parse_args()

    # Paths
    baseline_dir = Path(args.baseline_dir)
    output_dir = Path(args.output_dir)
    roi = args.roi
    subject_id = f"sub-{args.subject}"

    print(f"\n=== Step 1a: PCA Dimension Reduction ===")
    print(f"Subject: {subject_id}, ROI: {roi}")
    print(f"n_components: {args.n_components}")

    # Load baseline amplitudes
    amplitudes_path = baseline_dir / subject_id / roi / "amplitudes_z.npy"

    if not amplitudes_path.exists():
        print(f"ERROR: Amplitudes file not found: {amplitudes_path}")
        sys.exit(1)

    print(f"\nLoading: {amplitudes_path}")
    amplitudes_z = np.load(amplitudes_path)  # (6, 8, n_voxels)

    # PCA dimension reduction
    odd_pc, even_pc, pca_model, explained_variance = pca_dimension_reduction(
        amplitudes_z, n_components=args.n_components
    )

    # Validation
    validation = validate_pca_output(odd_pc, even_pc, explained_variance, args.n_components)

    # Save outputs
    output_roi_dir = output_dir / roi
    output_roi_dir.mkdir(parents=True, exist_ok=True)

    odd_pc_path = output_roi_dir / f"{subject_id}_odd_pc.npy"
    even_pc_path = output_roi_dir / f"{subject_id}_even_pc.npy"
    explained_var_path = output_roi_dir / f"{subject_id}_explained_variance.npy"
    metadata_path = output_roi_dir / f"{subject_id}_metadata.json"

    np.save(odd_pc_path, odd_pc)
    np.save(even_pc_path, even_pc)
    np.save(explained_var_path, explained_variance)

    # Save metadata
    metadata = {
        'subject': subject_id,
        'roi': roi,
        'n_components_requested': args.n_components,
        'n_components_actual': int(odd_pc.shape[1]),
        'n_voxels_original': int(amplitudes_z.shape[2]),
        'odd_pc_shape': list(odd_pc.shape),
        'even_pc_shape': list(even_pc.shape),
        'validation': validation,
        'explained_variance_cumulative': float(explained_variance.sum()),
        'explained_variance_first5': explained_variance[:5].tolist(),
    }

    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"\n=== Outputs Saved ===")
    print(f"  Odd PC: {odd_pc_path}")
    print(f"  Even PC: {even_pc_path}")
    print(f"  Explained variance: {explained_var_path}")
    print(f"  Metadata: {metadata_path}")

    print(f"\n✓ Step 1a complete for {subject_id} {roi}")


if __name__ == '__main__':
    main()
