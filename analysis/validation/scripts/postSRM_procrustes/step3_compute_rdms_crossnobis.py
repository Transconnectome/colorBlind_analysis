#!/usr/bin/env python3
"""
Step 3: Compute Crossnobis RDMs

Computes noise-corrected RDMs using cross-validated Mahalanobis distance
with Ledoit-Wolf shrinkage covariance estimation.

Usage:
    python step3_compute_rdms_crossnobis.py --subject 01 --roi V1 --method pca
"""

import argparse
import json
import numpy as np
from pathlib import Path
from scipy.stats import spearmanr
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Import existing crossnobis utilities
from utils.crossnobis_ldw import compute_rdm_crossnobis


def compute_rdm_from_split_halves(odd_pattern, even_pattern, use_shrinkage=True):
    """
    Compute Crossnobis RDM using odd/even split.

    Args:
        odd_pattern: (8, k) averaged odd runs
        even_pattern: (8, k) averaged even runs
        use_shrinkage: Use Ledoit-Wolf shrinkage (default: True)

    Returns:
        rdm_crossnobis: (8, 8) Mahalanobis-based RDM
        rdm_odd: (8, 8) correlation-based RDM (odd)
        rdm_even: (8, 8) correlation-based RDM (even)
        reliability: Split-half correlation
        shrinkage: Ledoit-Wolf shrinkage parameter (or None)
    """
    # Stack as 2 "runs" for crossnobis
    amplitudes = np.stack([odd_pattern, even_pattern], axis=0)  # (2, 8, k)

    # Compute crossnobis RDM (LORO cross-validation)
    rdm_crossnobis, shrinkage = compute_rdm_crossnobis(amplitudes, use_shrinkage=use_shrinkage)

    # Compute reliability (correlation-based RDMs)
    rdm_odd = 1 - np.corrcoef(odd_pattern)
    rdm_even = 1 - np.corrcoef(even_pattern)

    # Upper triangle (excluding diagonal)
    mask = np.triu_indices(8, k=1)
    reliability, _ = spearmanr(rdm_odd[mask], rdm_even[mask])

    return rdm_crossnobis, rdm_odd, rdm_even, reliability, shrinkage


def validate_rdm(rdm, name="RDM"):
    """
    Validate RDM properties.

    Returns:
        dict: Validation metrics
    """
    validation = {
        'symmetric': np.allclose(rdm, rdm.T, atol=1e-6),
        'diagonal_near_zero': np.allclose(np.diag(rdm), 0, atol=1e-3),
        'no_nan': not np.any(np.isnan(rdm)),
        'no_inf': not np.any(np.isinf(rdm)),
        'min_value': float(np.min(rdm)),
        'max_value': float(np.max(rdm)),
    }

    print(f"\n=== {name} Validation ===")
    print(f"  Symmetric: {validation['symmetric']}")
    print(f"  Diagonal ≈ 0: {validation['diagonal_near_zero']}")
    print(f"  No NaN: {validation['no_nan']}")
    print(f"  No Inf: {validation['no_inf']}")
    print(f"  Range: [{validation['min_value']:.4f}, {validation['max_value']:.4f}]")

    return validation


def main():
    parser = argparse.ArgumentParser(description='Step 3: Compute Crossnobis RDMs')
    parser.add_argument('--subject', type=str, required=True, help='Subject ID (e.g., 01)')
    parser.add_argument('--roi', type=str, required=True, help='ROI name (V1, V2, V3, hV4)')
    parser.add_argument('--method', type=str, default='pca', choices=['pca', 'anova'],
                        help='Dimension reduction method (default: pca)')
    parser.add_argument('--no-shrinkage', action='store_true', help='Disable Ledoit-Wolf shrinkage')
    parser.add_argument('--input-dir', type=str,
                        default='/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/validation/scripts/postSRM_procrus/results/step2_procrustes',
                        help='Input directory from Step 2')
    parser.add_argument('--output-dir', type=str,
                        default='/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/validation/scripts/postSRM_procrus/results/step3_rdms',
                        help='Output directory')

    args = parser.parse_args()

    # Paths
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    roi = args.roi
    subject_id = f"sub-{args.subject}"
    use_shrinkage = not args.no_shrinkage

    print(f"\n=== Step 3: Compute Crossnobis RDMs ===")
    print(f"Subject: {subject_id}, ROI: {roi}")
    print(f"Method: {args.method}")
    print(f"Shrinkage: {use_shrinkage}")

    # Load aligned patterns from Step 2
    odd_path = input_dir / roi / f"{subject_id}_aligned_odd.npy"
    even_path = input_dir / roi / f"{subject_id}_aligned_even.npy"

    if not odd_path.exists():
        print(f"ERROR: Aligned patterns not found: {odd_path}")
        sys.exit(1)

    print(f"\nLoading:")
    print(f"  Odd: {odd_path}")
    print(f"  Even: {even_path}")

    odd_pattern = np.load(odd_path)  # (8, k)
    even_pattern = np.load(even_path)  # (8, k)

    print(f"  Shapes: odd={odd_pattern.shape}, even={even_pattern.shape}")

    # Compute Crossnobis RDM
    print(f"\nComputing Crossnobis RDM...")
    rdm_crossnobis, rdm_odd, rdm_even, reliability, shrinkage = compute_rdm_from_split_halves(
        odd_pattern, even_pattern, use_shrinkage=use_shrinkage
    )

    print(f"\n✓ Crossnobis RDM computed")
    print(f"  Shape: {rdm_crossnobis.shape}")
    if shrinkage is not None:
        print(f"  Shrinkage λ: {shrinkage:.4f}")
    print(f"  Split-half reliability: {reliability:.4f}")

    # Validation
    validation_crossnobis = validate_rdm(rdm_crossnobis, "Crossnobis RDM")
    validation_odd = validate_rdm(rdm_odd, "Odd RDM")
    validation_even = validate_rdm(rdm_even, "Even RDM")

    # Save outputs
    output_roi_dir = output_dir / roi
    output_roi_dir.mkdir(parents=True, exist_ok=True)

    rdm_crossnobis_path = output_roi_dir / f"{subject_id}_rdm_crossnobis.npy"
    rdm_odd_path = output_roi_dir / f"{subject_id}_rdm_odd.npy"
    rdm_even_path = output_roi_dir / f"{subject_id}_rdm_even.npy"

    np.save(rdm_crossnobis_path, rdm_crossnobis)
    np.save(rdm_odd_path, rdm_odd)
    np.save(rdm_even_path, rdm_even)

    # Save metadata
    metadata = {
        'subject': subject_id,
        'roi': roi,
        'method': args.method,
        'use_shrinkage': use_shrinkage,
        'shrinkage_lambda': float(shrinkage) if shrinkage is not None else None,
        'split_half_reliability': float(reliability),
        'validation': {
            'crossnobis': validation_crossnobis,
            'odd': validation_odd,
            'even': validation_even,
        },
    }

    metadata_path = output_roi_dir / f"{subject_id}_split_half_reliability.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    # Save shrinkage info separately for easy access
    if shrinkage is not None:
        shrinkage_path = output_roi_dir / f"{subject_id}_shrinkage.json"
        with open(shrinkage_path, 'w') as f:
            json.dump({'shrinkage_lambda': float(shrinkage)}, f, indent=2)

    print(f"\n=== Outputs Saved ===")
    print(f"  Crossnobis RDM: {rdm_crossnobis_path}")
    print(f"  Odd RDM: {rdm_odd_path}")
    print(f"  Even RDM: {rdm_even_path}")
    print(f"  Metadata: {metadata_path}")
    if shrinkage is not None:
        print(f"  Shrinkage: {shrinkage_path}")

    print(f"\n✓ Step 3 complete for {subject_id} {roi}")


if __name__ == '__main__':
    main()
