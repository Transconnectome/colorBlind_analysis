#!/usr/bin/env python3
"""
ROI Quality Comparison: deoblique_v2 vs original_v3

Checks if the same subjects show problems in both versions:
- sub-01: voxel count outlier
- sub-04: V1 signal dropout

Usage:
    python check_roi_quality_comparison.py
"""

import nibabel as nib
import numpy as np
from pathlib import Path
import sys

def check_subject_roi_quality(fmriprep_dir, subject_id, roi_name='V1'):
    """
    Check ROI signal quality for a subject

    Returns:
        dict with metrics: mean_signal, std_signal, nonzero_voxels, etc.
    """
    sub_id = subject_id.zfill(2)

    # BOLD file (using run-1 as example)
    bold_pattern = list(Path(fmriprep_dir).glob(
        f'sub-{sub_id}/func/*run-1*space-MNI*desc-preproc_bold.nii.gz'
    ))

    if not bold_pattern:
        return {'error': 'BOLD file not found'}

    bold_file = bold_pattern[0]

    try:
        bold_img = nib.load(bold_file)
        bold_data = bold_img.get_fdata()

        # Basic metrics
        metrics = {
            'shape': bold_data.shape,
            'mean_signal': np.mean(bold_data[bold_data > 0]),
            'std_signal': np.std(bold_data[bold_data > 0]),
            'nonzero_voxels': np.sum(bold_data[:,:,:,0] > 0),  # First volume
            'min_signal': np.min(bold_data[bold_data > 0]),
            'max_signal': np.max(bold_data),
        }

        # Check for zero-signal regions (like sub-04 V1 issue)
        # Sample posterior region (rough V1 location)
        # MNI coordinates roughly y < -70 for occipital
        if bold_data.shape[1] > 20:  # Has enough slices
            # Check occipital region signal
            posterior_slice = bold_data[:, :20, :, 0]  # Posterior slices
            occipital_nonzero = np.sum(posterior_slice > 0)
            occipital_mean = np.mean(posterior_slice[posterior_slice > 0]) if occipital_nonzero > 0 else 0

            metrics['occipital_nonzero_voxels'] = occipital_nonzero
            metrics['occipital_mean_signal'] = occipital_mean

        return metrics

    except Exception as e:
        return {'error': str(e)}

def compare_versions(subjects=['01', '04', '08']):
    """
    Compare ROI quality between versions

    Focus on:
    - sub-01: Check if voxel count is low
    - sub-04: Check if V1 region has signal
    - sub-08: Control (CVD, should be normal)
    """

    versions = {
        'deoblique_v2': '/storage/connectome/haba6030/fmriprep_out_deoblique_v2',
        'original_v3': '/storage/connectome/haba6030/fmriprep_out_original_v3'
    }

    print("=" * 80)
    print("ROI Quality Comparison: deoblique_v2 vs original_v3")
    print("=" * 80)
    print()

    for subject_id in subjects:
        print(f"{'=' * 80}")
        print(f"Subject: sub-{subject_id}")
        print(f"{'=' * 80}")
        print()

        results = {}
        for version_name, version_path in versions.items():
            print(f"Checking {version_name}...")
            metrics = check_subject_roi_quality(version_path, subject_id)
            results[version_name] = metrics

            if 'error' in metrics:
                print(f"  ❌ Error: {metrics['error']}")
            else:
                print(f"  ✅ Loaded successfully")
                print(f"     Shape: {metrics['shape']}")
                print(f"     Non-zero voxels: {metrics['nonzero_voxels']}")
                print(f"     Mean signal: {metrics['mean_signal']:.2f}")
                if 'occipital_nonzero_voxels' in metrics:
                    print(f"     Occipital non-zero voxels: {metrics['occipital_nonzero_voxels']}")
                    print(f"     Occipital mean signal: {metrics['occipital_mean_signal']:.2f}")
            print()

        # Compare
        if all('error' not in r for r in results.values()):
            print("Comparison:")

            # Voxel count
            v2_voxels = results['deoblique_v2']['nonzero_voxels']
            v3_voxels = results['original_v3']['nonzero_voxels']
            diff_pct = abs(v2_voxels - v3_voxels) / v2_voxels * 100

            print(f"  Non-zero voxels:")
            print(f"    deoblique_v2: {v2_voxels}")
            print(f"    original_v3:  {v3_voxels}")
            print(f"    Difference:   {diff_pct:.1f}%")

            if diff_pct < 1:
                print(f"    → ✅ Very similar")
            elif diff_pct < 5:
                print(f"    → ⚠️  Small difference")
            else:
                print(f"    → ❌ Significant difference")

            # Signal quality
            v2_signal = results['deoblique_v2']['mean_signal']
            v3_signal = results['original_v3']['mean_signal']
            signal_diff_pct = abs(v2_signal - v3_signal) / v2_signal * 100

            print(f"  Mean signal:")
            print(f"    deoblique_v2: {v2_signal:.2f}")
            print(f"    original_v3:  {v3_signal:.2f}")
            print(f"    Difference:   {signal_diff_pct:.1f}%")

            # Occipital region (critical for sub-04)
            if 'occipital_nonzero_voxels' in results['deoblique_v2']:
                v2_occ = results['deoblique_v2']['occipital_nonzero_voxels']
                v3_occ = results['original_v3']['occipital_nonzero_voxels']

                print(f"  Occipital region (V1 area):")
                print(f"    deoblique_v2: {v2_occ} voxels")
                print(f"    original_v3:  {v3_occ} voxels")

                if subject_id == '04':
                    if v2_occ == 0 and v3_occ > 0:
                        print(f"    → ✅ original_v3 has signal in V1!")
                    elif v2_occ == 0 and v3_occ == 0:
                        print(f"    → ❌ Both versions lack V1 signal")
                    else:
                        print(f"    → ✅ Both have V1 signal")

        print()

def main():
    print("Checking if fMRIPrep directories are accessible...")
    print()

    # Test paths
    v2_path = Path('/storage/connectome/haba6030/fmriprep_out_deoblique_v2')
    v3_path = Path('/storage/connectome/haba6030/fmriprep_out_original_v3')

    if not v2_path.exists():
        print(f"❌ deoblique_v2 not found: {v2_path}")
        print("   (This script must run on the server)")
        sys.exit(1)

    if not v3_path.exists():
        print(f"❌ original_v3 not found: {v3_path}")
        sys.exit(1)

    print("✅ Both directories found")
    print()

    # Compare critical subjects
    subjects = ['01', '04', '08']
    compare_versions(subjects)

    print()
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print()
    print("Key questions answered:")
    print("1. Does original_v3 fix sub-04 V1 signal dropout?")
    print("2. Does original_v3 have better voxel count for sub-01?")
    print("3. Is signal quality similar across versions?")
    print()
    print("See detailed comparison above.")
    print()

if __name__ == '__main__':
    main()
