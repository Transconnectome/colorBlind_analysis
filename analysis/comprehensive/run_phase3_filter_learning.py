#!/usr/bin/env python3
"""
Phase 3: Linear Filter Learning (Adapted for New Pipeline)

Learns linear transformation filters: CVD patterns → HC-like patterns
Uses Procrustes-aligned data from Phase 2 as targets.
"""

import argparse
import numpy as np
from pathlib import Path
import json
from scipy.linalg import lstsq
from datetime import datetime
import sys

def load_aligned_patterns(timestamp, roi, dataset='method3_header_mi'):
    """Load Procrustes-aligned patterns from Phase 2"""
    base_dir = Path('/scratch/connectome/haba6030/colorBlind')

    # Phase 2 results location
    phase2_dir = base_dir / 'analysis' / 'comprehensive' / 'results' / timestamp / roi

    if not phase2_dir.exists():
        raise FileNotFoundError(f"Phase 2 results not found: {phase2_dir}")

    # Load aligned patterns
    aligned_file = phase2_dir / 'aligned_patterns.npz'
    if not aligned_file.exists():
        raise FileNotFoundError(f"Aligned patterns not found: {aligned_file}")

    data = np.load(aligned_file, allow_pickle=True)
    aligned_patterns = {
        'aligned_patterns': data['aligned_patterns'],
        'group_template': data['group_template'],
        'disparities': data['disparities']
    }

    return aligned_patterns, phase2_dir

def load_cvd_original_patterns(subject_id, roi, timestamp, dataset='method3_header_mi'):
    """Load original (unaligned) CVD patterns"""
    base_dir = Path('/scratch/connectome/haba6030/colorBlind')

    # Load amplitudes from baseline results
    result_dir = base_dir / 'analysis' / 'phase1_preprocess_decoding' / dataset / 'results' / 'baseline_decoding' / timestamp / f'sub-{subject_id}' / roi

    if not result_dir.exists():
        raise FileNotFoundError(f"Baseline results not found: {result_dir}")

    amp_file = result_dir / 'amplitudes_z.npy'
    if not amp_file.exists():
        raise FileNotFoundError(f"Amplitudes not found: {amp_file}")

    amplitudes = np.load(amp_file)  # (n_runs, n_colors, n_voxels)

    # Average across runs to get (n_colors, n_voxels) pattern
    pattern = amplitudes.mean(axis=0)

    return pattern

def train_linear_filter(X_cvd, Y_target):
    """
    Train linear filter: Y = A @ X + b

    Args:
        X_cvd: (n_samples, n_features) - CVD patterns
        Y_target: (n_samples, n_features) - Target HC-like patterns

    Returns:
        A: (n_features, n_features) - Transformation matrix
        b: (n_features,) - Bias vector
    """
    n_samples, n_features = X_cvd.shape

    # Add bias term: X_aug = [X, 1]
    X_aug = np.column_stack([X_cvd, np.ones(n_samples)])

    # Solve: Y = [A, b] @ [X; 1]
    # Using least squares: [A, b]^T = (X_aug^T @ X_aug)^(-1) @ X_aug^T @ Y
    Ab, residuals, rank, s = lstsq(X_aug, Y_target)

    A = Ab[:-1, :].T  # (n_features, n_features)
    b = Ab[-1, :]     # (n_features,)

    # Compute training error
    Y_pred = (A @ X_cvd.T).T + b
    train_error = np.mean((Y_pred - Y_target) ** 2)

    return A, b, train_error

def apply_filter(X, A, b):
    """Apply learned filter: Y = A @ X + b"""
    if X.ndim == 1:
        return A @ X + b
    else:
        return (A @ X.T).T + b

def run_filter_learning(timestamp, roi, cvd_subjects, hc_subjects, dataset='method3_header_mi'):
    """Main filter learning pipeline"""

    print(f"\n{'='*70}")
    print(f"Phase 3: Filter Learning - ROI {roi}")
    print(f"{'='*70}")
    print(f"CVD subjects: {cvd_subjects}")
    print(f"HC subjects: {hc_subjects}")
    print("")

    base_dir = Path('/scratch/connectome/haba6030/colorBlind')
    output_dir = base_dir / 'analysis' / 'comprehensive' / 'results' / timestamp / roi / 'filter_learning'
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load Phase 2 aligned patterns
    try:
        aligned_patterns, phase2_dir = load_aligned_patterns(timestamp, roi, dataset)
        print(f"✓ Loaded aligned patterns from Phase 2")
    except FileNotFoundError as e:
        print(f"✗ Error: {e}")
        print(f"  Skipping filter learning for {roi}")
        return False

    # Get HC group template as target
    if 'group_template' not in aligned_patterns:
        print(f"✗ Error: No group_template found in aligned patterns")
        return False

    group_template = aligned_patterns['group_template']  # (n_colors, n_voxels)
    print(f"  HC group template shape: {group_template.shape}")

    # Train filter for each CVD subject
    filters = {}

    for cvd_id in cvd_subjects:
        print(f"\n--- Training filter for CVD sub-{cvd_id} ---")

        try:
            # Load CVD original patterns
            cvd_pattern = load_cvd_original_patterns(cvd_id, roi, timestamp, dataset)
            print(f"  Original CVD pattern shape: {cvd_pattern.shape}")

            # Ensure same number of voxels (truncate to minimum)
            min_voxels = min(cvd_pattern.shape[1], group_template.shape[1])
            X_cvd = cvd_pattern[:, :min_voxels]  # (n_colors, n_voxels)
            Y_target = group_template[:, :min_voxels]

            print(f"  Training with {min_voxels} voxels, {X_cvd.shape[0]} colors")

            # Train filter
            A, b, train_error = train_linear_filter(X_cvd, Y_target)

            print(f"  ✓ Filter trained")
            print(f"    Training MSE: {train_error:.4f}")
            print(f"    Matrix A shape: {A.shape}")
            print(f"    Bias b shape: {b.shape}")

            # Save filter
            filter_data = {
                'A': A,
                'b': b,
                'train_error': train_error,
                'n_voxels': min_voxels,
                'n_colors': X_cvd.shape[0],
                'cvd_subject': cvd_id,
                'roi': roi,
                'timestamp': timestamp
            }

            filter_file = output_dir / f'filter_cvd-{cvd_id}.npz'
            np.savez(filter_file, **filter_data)
            print(f"  ✓ Filter saved: {filter_file}")

            filters[cvd_id] = filter_data

        except Exception as e:
            print(f"  ✗ Error training filter for sub-{cvd_id}: {e}")
            continue

    # Save summary
    summary = {
        'roi': roi,
        'timestamp': timestamp,
        'dataset': dataset,
        'cvd_subjects': cvd_subjects,
        'hc_subjects': hc_subjects,
        'n_filters_trained': len(filters),
        'filters': {
            cvd_id: {
                'train_error': float(f['train_error']),
                'n_voxels': int(f['n_voxels']),
                'n_colors': int(f['n_colors'])
            }
            for cvd_id, f in filters.items()
        },
        'generated': datetime.now().isoformat()
    }

    summary_file = output_dir / 'filter_summary.json'
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\n✓ Filter learning complete for {roi}")
    print(f"  Filters trained: {len(filters)}/{len(cvd_subjects)}")
    print(f"  Results saved to: {output_dir}")

    return len(filters) > 0

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Phase 3: Filter Learning')
    parser.add_argument('--timestamp', type=str, required=True)
    parser.add_argument('--roi', type=str, required=True)
    parser.add_argument('--cvd-subjects', nargs='+', required=True)
    parser.add_argument('--hc-subjects', nargs='+', required=True)
    parser.add_argument('--dataset', type=str, default='method3_header_mi')

    args = parser.parse_args()

    success = run_filter_learning(
        args.timestamp,
        args.roi,
        args.cvd_subjects,
        args.hc_subjects,
        args.dataset
    )

    sys.exit(0 if success else 1)
