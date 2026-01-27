#!/usr/bin/env python3
"""
Diagnose Procrustes Error - Check for Constant Voxels
======================================================
Procrustes 내부에서 standardization 시 stddev로 나누는데,
어떤 voxel이 8개 색깔 전부에 대해 동일한 값을 가지면 stddev=0 → division by zero

이 스크립트는:
1. 각 subject-ROI의 amplitudes_z.npy 로드
2. Run별로 constant voxel (std=0 across 8 colors) 확인
3. 문제 있는 subject-ROI 리스트 출력
"""

import argparse
from pathlib import Path
import numpy as np


def check_constant_voxels(amplitudes_z):
    """
    Check for voxels with zero variance across colors (constant voxels)

    Args:
        amplitudes_z: (n_runs, n_colors=8, n_voxels)

    Returns:
        dict with per-run constant voxel info
    """
    n_runs, n_colors, n_voxels = amplitudes_z.shape

    results = {
        'has_constant_voxels': False,
        'runs': {}
    }

    for run_idx in range(n_runs):
        pattern = amplitudes_z[run_idx]  # (8 colors, n_voxels)

        # Compute std across colors for each voxel (column)
        voxel_stds = np.std(pattern, axis=0)  # (n_voxels,)

        # Find constant voxels
        constant_mask = voxel_stds < 1e-10
        n_constant = np.sum(constant_mask)

        results['runs'][f'run_{run_idx+1}'] = {
            'n_constant_voxels': int(n_constant),
            'constant_voxel_indices': np.where(constant_mask)[0].tolist() if n_constant > 0 else [],
            'min_std': float(np.min(voxel_stds)),
            'max_std': float(np.max(voxel_stds)),
            'mean_std': float(np.mean(voxel_stds))
        }

        if n_constant > 0:
            results['has_constant_voxels'] = True

    return results


def main():
    parser = argparse.ArgumentParser(description='Diagnose Procrustes error - check for constant voxels')
    parser.add_argument('--baseline-timestamp', type=str, required=True)
    parser.add_argument('--subjects', nargs='+',
                       default=[f'sub-{i:02d}' for i in range(1, 11)])
    parser.add_argument('--rois', nargs='+',
                       default=['V1', 'V2', 'V3', 'hV4'])

    args = parser.parse_args()

    baseline_dir = Path('/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/method3_header_mi/results/baseline_decoding') / args.baseline_timestamp

    print("="*70)
    print("Constant Voxel Diagnosis (Procrustes Error)")
    print("="*70)
    print(f"Baseline: {args.baseline_timestamp}")
    print()

    problem_found = False

    for subject in args.subjects:
        for roi in args.rois:
            amp_path = baseline_dir / subject / roi / 'amplitudes_z.npy'

            if not amp_path.exists():
                continue

            amplitudes_z = np.load(amp_path)
            results = check_constant_voxels(amplitudes_z)

            if results['has_constant_voxels']:
                problem_found = True
                print(f"⚠️  {subject} {roi}: CONSTANT VOXELS FOUND")
                print(f"   Shape: {amplitudes_z.shape}")

                for run_name, run_info in results['runs'].items():
                    if run_info['n_constant_voxels'] > 0:
                        print(f"   {run_name}: {run_info['n_constant_voxels']} constant voxels")
                        print(f"      Min std: {run_info['min_std']:.2e}")
                        print(f"      Indices: {run_info['constant_voxel_indices'][:10]}..." if len(run_info['constant_voxel_indices']) > 10 else f"      Indices: {run_info['constant_voxel_indices']}")
                print()

    if not problem_found:
        print("✓ No constant voxels found in any subject-ROI")

    print("="*70)
    print("Diagnosis complete")
    print("="*70)


if __name__ == '__main__':
    main()
