#!/usr/bin/env python3
"""
Test script for CVD distortion figure generation.

Validates data availability and creates a test figure for one subject-ROI.
"""

import numpy as np
from pathlib import Path
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from create_cvd_distortion_figure import (
    load_subject_data,
    compute_rdm_from_amplitudes,
    compute_hc_mean_rdm,
    CVD_SUBJECTS,
    HC_SUBJECTS,
    C010_DIR,
    MASK_DIR
)


def test_data_availability():
    """Check that all required data files exist."""
    print("\n" + "="*70)
    print("TESTING DATA AVAILABILITY")
    print("="*70 + "\n")

    all_subjects = list(CVD_SUBJECTS.keys()) + HC_SUBJECTS
    rois = ['V1', 'V2', 'V3', 'hV4']
    roi_dir_map = {'V1': 'V1', 'V2': 'V2', 'V3': 'V3', 'hV4': 'V4'}

    missing_files = []

    for subject in all_subjects:
        for roi in rois:
            roi_dir = roi_dir_map[roi]

            # Check amplitudes
            amps_path = C010_DIR / subject / roi_dir / 'amplitudes_procrustes.npy'
            if not amps_path.exists():
                missing_files.append(f"❌ {subject} {roi}: amplitudes")
                print(f"❌ {subject} {roi}: amplitudes missing")
            else:
                # Check shape
                amps = np.load(amps_path)
                if amps.shape[0] != 6 or amps.shape[1] != 8:
                    print(f"⚠️  {subject} {roi}: amplitudes shape {amps.shape} (expected (6, 8, n_voxels))")
                else:
                    print(f"✓  {subject} {roi}: amplitudes OK (shape {amps.shape})")

            # Check mask (use roi name as-is, not roi_dir)
            mask_file = f'{roi}_mask_thr50_intnearest_binTrue_maskfunc_gmTrue_subjFalse.nii.gz'
            mask_path = MASK_DIR / subject / 'roi_pipeline' / mask_file
            if not mask_path.exists():
                missing_files.append(f"❌ {subject} {roi}: mask")
                print(f"❌ {subject} {roi}: mask missing")

    print(f"\n{'='*70}")
    if len(missing_files) == 0:
        print("✓ ALL DATA FILES PRESENT")
    else:
        print(f"⚠️  {len(missing_files)} MISSING FILES")
        for f in missing_files[:10]:  # Show first 10
            print(f"  {f}")
        if len(missing_files) > 10:
            print(f"  ... and {len(missing_files) - 10} more")
    print(f"{'='*70}\n")

    return len(missing_files) == 0


def test_rdm_computation():
    """Test RDM computation for one subject."""
    print("\n" + "="*70)
    print("TESTING RDM COMPUTATION")
    print("="*70 + "\n")

    subject = 'sub-08'
    roi = 'V2'

    try:
        # Load data
        print(f"Loading {subject} {roi}...")
        data = load_subject_data(subject, roi)

        # Compute RDM
        print("Computing RDM...")
        rdm = compute_rdm_from_amplitudes(data['amplitudes'])

        # Validate
        print(f"\nRDM validation:")
        print(f"  Shape: {rdm.shape} (expected (8, 8))")
        print(f"  Symmetric: {np.allclose(rdm, rdm.T)}")
        print(f"  Diagonal: {np.diag(rdm)} (should be ~0)")
        print(f"  Range: [{rdm.min():.3f}, {rdm.max():.3f}]")

        # Check for NaN/Inf
        if np.any(np.isnan(rdm)):
            print("  ⚠️  WARNING: RDM contains NaN values!")
        if np.any(np.isinf(rdm)):
            print("  ⚠️  WARNING: RDM contains Inf values!")

        # Compute HC mean
        print(f"\nComputing HC mean RDM for {roi}...")
        hc_rdm = compute_hc_mean_rdm(roi)
        print(f"  HC mean RDM range: [{hc_rdm.min():.3f}, {hc_rdm.max():.3f}]")

        # Compute difference
        diff_rdm = rdm - hc_rdm
        print(f"\nDifference (CVD - HC):")
        print(f"  Range: [{diff_rdm.min():.3f}, {diff_rdm.max():.3f}]")
        print(f"  Mean: {diff_rdm.mean():.3f}")

        print(f"\n{'='*70}")
        print("✓ RDM COMPUTATION SUCCESSFUL")
        print(f"{'='*70}\n")

        return True

    except Exception as e:
        print(f"\n{'='*70}")
        print(f"❌ RDM COMPUTATION FAILED: {e}")
        print(f"{'='*70}\n")
        import traceback
        traceback.print_exc()
        return False


def test_figure_creation():
    """Test figure creation for V2 (quick test)."""
    print("\n" + "="*70)
    print("TESTING FIGURE CREATION (V2 only)")
    print("="*70 + "\n")

    try:
        from create_cvd_distortion_figure import create_cvd_distortion_figure

        # Create test figure
        print("Creating test figure for V2...")
        output_path = create_cvd_distortion_figure('V2')

        print(f"\n{'='*70}")
        print(f"✓ FIGURE CREATED SUCCESSFULLY")
        print(f"  Output: {output_path}")
        print(f"  Size: {output_path.stat().st_size / 1e6:.1f} MB")
        print(f"{'='*70}\n")

        return True

    except Exception as e:
        print(f"\n{'='*70}")
        print(f"❌ FIGURE CREATION FAILED: {e}")
        print(f"{'='*70}\n")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Test CVD distortion figure pipeline')
    parser.add_argument('--data-check', action='store_true', help='Check data availability only')
    parser.add_argument('--rdm-test', action='store_true', help='Test RDM computation only')
    parser.add_argument('--full-test', action='store_true', help='Run full test including figure creation')
    args = parser.parse_args()

    if not any([args.data_check, args.rdm_test, args.full_test]):
        # Default: run all tests
        args.full_test = True

    success = True

    if args.data_check or args.full_test:
        success = test_data_availability() and success

    if args.rdm_test or args.full_test:
        success = test_rdm_computation() and success

    if args.full_test:
        success = test_figure_creation() and success

    # Exit code
    sys.exit(0 if success else 1)
