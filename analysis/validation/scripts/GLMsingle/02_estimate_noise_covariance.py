#!/usr/bin/env python3
"""
Step 2: Estimate Noise Covariance from Residuals

This script:
1. Loads GLMsingle 1st-level residuals
2. Estimates spatial noise covariance Σ using Ledoit-Wolf shrinkage
3. Computes whitening matrix W = Σ^(-1/2)
4. Saves matrices for Step 3 (whitening)

Usage:
    python 02_estimate_noise_covariance.py --subject 01 --roi V1
    python 02_estimate_noise_covariance.py --input-dir results/{timestamp}/sub-01_V1

Expected runtime: 5-10 minutes per subject-ROI
"""

import argparse
import json
import numpy as np
from pathlib import Path
from datetime import datetime
import sys

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent / 'utils'))

from whitening_from_residuals import (
    estimate_noise_covariance,
    compute_whitening_matrix,
    evaluate_whitening_quality
)


def parse_args():
    parser = argparse.ArgumentParser(
        description='Estimate noise covariance and compute whitening matrix'
    )
    parser.add_argument(
        '--subject',
        type=str,
        help='Subject ID (e.g., 01)'
    )
    parser.add_argument(
        '--roi',
        type=str,
        help='ROI name (e.g., V1)'
    )
    parser.add_argument(
        '--input-dir',
        type=Path,
        help='Input directory from Step 1 (overrides --subject/--roi)'
    )
    parser.add_argument(
        '--method',
        type=str,
        default='ledoit_wolf',
        choices=['ledoit_wolf', 'empirical', 'diagonal'],
        help='Covariance estimation method'
    )
    parser.add_argument(
        '--block-size',
        type=int,
        default=None,
        help='Block size for block-diagonal approximation (optional)'
    )

    return parser.parse_args()


def find_latest_results(subject, roi, base_dir='./results'):
    """Find most recent GLMsingle results for subject-ROI."""
    base_path = Path(base_dir) / 'GLMsingle'

    if not base_path.exists():
        raise FileNotFoundError(f"Results directory not found: {base_path}")

    # Find all directories for this subject-ROI
    pattern = f"sub-{subject}_{roi}"
    matching_dirs = []

    for timestamp_dir in sorted(base_path.glob('*'), reverse=True):
        subject_roi_dir = timestamp_dir / pattern
        if subject_roi_dir.exists():
            matching_dirs.append(subject_roi_dir)

    if not matching_dirs:
        raise FileNotFoundError(
            f"No results found for sub-{subject} {roi} in {base_path}"
        )

    return matching_dirs[0]


def main():
    args = parse_args()

    print("=" * 80)
    print("Noise Covariance Estimation - Step 2")
    print("=" * 80)

    # Determine input directory
    if args.input_dir is not None:
        input_dir = args.input_dir
    elif args.subject and args.roi:
        input_dir = find_latest_results(args.subject, args.roi)
    else:
        print("ERROR: Must specify either --input-dir or --subject and --roi")
        return 1

    if not input_dir.exists():
        print(f"ERROR: Input directory not found: {input_dir}")
        return 1

    print(f"Input: {input_dir}")
    print(f"Method: {args.method}")
    print()

    # ===== Step 1: Load Residuals =====
    print("=" * 80)
    print("Step 1: Loading GLMsingle Residuals")
    print("=" * 80)

    residuals_file = input_dir / 'residuals_1st_level.npy'

    if not residuals_file.exists():
        print(f"ERROR: Residuals file not found: {residuals_file}")
        print("Make sure Step 1 (01_glmsingle_with_residuals.py) completed successfully")
        print("and that residuals were saved.")
        return 1

    residuals = np.load(residuals_file)
    print(f"✓ Loaded residuals: {residuals.shape}")
    print(f"  Shape: (n_runs={residuals.shape[0]}, "
          f"n_scans={residuals.shape[1]}, "
          f"n_voxels={residuals.shape[2]})")

    # Basic checks
    print(f"\nResiduals statistics:")
    print(f"  Mean: {residuals.mean():.6f} (should be ≈ 0)")
    print(f"  Std: {residuals.std():.3f}")
    print(f"  Min: {residuals.min():.3f}")
    print(f"  Max: {residuals.max():.3f}")

    if abs(residuals.mean()) > 1.0:
        print("WARNING: Residuals mean is large - check data quality")

    # ===== Step 2: Estimate Noise Covariance =====
    print("\n" + "=" * 80)
    print("Step 2: Estimating Noise Covariance")
    print("=" * 80)

    if args.block_size is not None:
        # Block-diagonal approximation
        print(f"Using block-diagonal approximation (block_size={args.block_size})")
        from whitening_from_residuals import block_diagonal_whitening

        Sigma_full, metadata_cov = block_diagonal_whitening(
            residuals,
            block_size=args.block_size,
            method=args.method,
            verbose=True
        )

        # For block-diagonal, Sigma_full is actually the whitening matrix
        # Rename for clarity
        W = Sigma_full
        metadata_white = {'method': 'block_diagonal'}

    else:
        # Full covariance matrix
        Sigma, metadata_cov = estimate_noise_covariance(
            residuals,
            method=args.method,
            verbose=True
        )

        # Save covariance matrix
        cov_file = input_dir / 'noise_covariance.npy'
        np.save(cov_file, Sigma)
        print(f"\n✓ Saved covariance: {cov_file}")
        print(f"  Shape: {Sigma.shape}")
        print(f"  Size: {Sigma.nbytes / 1e6:.2f} MB")

        # ===== Step 3: Compute Whitening Matrix =====
        print("\n" + "=" * 80)
        print("Step 3: Computing Whitening Matrix")
        print("=" * 80)

        W, metadata_white = compute_whitening_matrix(Sigma)
        print(f"✓ Whitening matrix computed: {W.shape}")
        print(f"  Identity error: {metadata_white['identity_error']:.6f}")

        if metadata_white['identity_error'] > 0.1:
            print("WARNING: High identity error - whitening may be unstable")

    # Save whitening matrix
    white_file = input_dir / 'whitening_matrix.npy'
    np.save(white_file, W)
    print(f"\n✓ Saved whitening matrix: {white_file}")
    print(f"  Shape: {W.shape}")
    print(f"  Size: {W.nbytes / 1e6:.2f} MB")

    # ===== Step 4: Test Whitening Quality =====
    print("\n" + "=" * 80)
    print("Step 4: Testing Whitening Quality")
    print("=" * 80)

    # Apply whitening to residuals (test)
    from whitening_from_residuals import apply_whitening
    residuals_whitened = apply_whitening(residuals, W, axis=-1)

    # Evaluate quality
    metrics = evaluate_whitening_quality(
        residuals,
        residuals_whitened,
        axis=-1
    )

    print("Whitening quality metrics:")
    for key, value in metrics.items():
        print(f"  {key}: {value:.4f}")

    if metrics['correlation_reduction_pct'] < 10:
        print("\nWARNING: Low correlation reduction (<10%)")
        print("Whitening may not improve results significantly")
    elif metrics['correlation_reduction_pct'] > 50:
        print("\n✓ Good correlation reduction (>50%)")
        print("Whitening should improve results")

    # ===== Step 5: Save Metadata =====
    print("\n" + "=" * 80)
    print("Step 5: Saving Metadata")
    print("=" * 80)

    metadata = {
        'timestamp': datetime.now().isoformat(),
        'input_dir': str(input_dir),
        'method': args.method,
        'block_size': args.block_size,

        # Covariance estimation
        'covariance': metadata_cov,

        # Whitening
        'whitening': metadata_white,

        # Quality metrics
        'whitening_quality': {k: float(v) for k, v in metrics.items()},

        # Files
        'files': {
            'residuals': str(residuals_file),
            'covariance': str(cov_file) if args.block_size is None else None,
            'whitening_matrix': str(white_file)
        }
    }

    meta_file = input_dir / 'whitening_metadata.json'
    with open(meta_file, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"✓ Metadata: {meta_file}")

    # ===== Done =====
    print("\n" + "=" * 80)
    print("Noise Covariance Estimation Completed!")
    print("=" * 80)
    print(f"Output directory: {input_dir}")
    print()
    print("Files created:")
    if args.block_size is None:
        print(f"  - noise_covariance.npy ({Sigma.nbytes/1e6:.2f} MB)")
    print(f"  - whitening_matrix.npy ({W.nbytes/1e6:.2f} MB)")
    print(f"  - whitening_metadata.json")
    print()
    print("Next step:")
    print("  Run 03_glmsingle_whitened_amplitudes.py to apply whitening")
    print()

    return 0


if __name__ == '__main__':
    exit(main())
