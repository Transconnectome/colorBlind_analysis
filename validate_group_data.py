#!/usr/bin/env python3
"""
validate_group_data.py
======================

Group-level analysis 실행 전 데이터 검증 스크립트

검증 항목:
1. 모든 subjects의 amplitudes_z.npy 파일 존재 확인
2. Shape 일치 여부 (n_runs, n_colors, n_voxels)
3. MNI space 일치 여부 (ROI mask affine 비교)
4. 데이터 품질 (NaN, Inf 체크)

Usage:
    # 로컬에서 실행 (다운로드된 데이터 검증)
    python validate_group_data.py --roi V1 --timestamp baseline32_deob

    # 서버에서 실행
    ssh haba6030@node2
    cd /scratch/connectome/haba6030/colorBlind
    python validate_group_data.py --roi V1 --timestamp baseline32_deob --dataset deoblique_v2

Output:
    - 터미널에 검증 결과 출력
    - validation_report_{roi}_{timestamp}.txt 저장
    - 문제 발견 시 exit code 1 반환

Author: Claude Code
Date: 2025-12-13
"""

import numpy as np
import pandas as pd
import nibabel as nib
from pathlib import Path
import argparse
import glob
import sys

# ============================================================================
# Configuration
# ============================================================================

def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description='Validate group-level analysis data before execution'
    )

    parser.add_argument('--roi', type=str, required=True,
                        help='ROI name (V1, V2, V3, hV4)')
    parser.add_argument('--timestamp', type=str, required=True,
                        help='Baseline timestamp (e.g., baseline32_deob)')
    parser.add_argument('--dataset', type=str, default='deoblique_v2',
                        help='Dataset name (default: deoblique_v2)')
    parser.add_argument('--subjects', type=str, nargs='+',
                        default=['01', '02', '03', '05', '06', '07'],
                        help='Subject IDs to validate')
    parser.add_argument('--output-file', type=str, default=None,
                        help='Output validation report file')

    return parser.parse_args()


# ============================================================================
# Data Loading
# ============================================================================

def find_subject_amplitudes(subject_id, roi, timestamp, dataset='deoblique_v2'):
    """
    Find amplitudes_z.npy file for a subject

    Returns:
        (amplitudes_path, roi_mask_path, result_dir) or (None, None, None) if not found
    """
    base_path = Path(f'derivatives/BH2009_{dataset}/{timestamp}')
    pattern = str(base_path / f'sm*_sub-{subject_id}_{roi}_*')

    matches = glob.glob(pattern)

    if len(matches) == 0:
        return None, None, None

    # Filter by directories that contain amplitudes_z.npy
    valid_matches = [m for m in matches if Path(m).joinpath('amplitudes_z.npy').exists()]

    if not valid_matches:
        return None, None, None

    # Prefer directories ending with '_None'
    none_matches = [m for m in valid_matches if m.endswith('_None')]

    if len(none_matches) > 0:
        none_matches_sorted = sorted(none_matches, key=lambda x: Path(x).stat().st_mtime, reverse=True)
        result_dir = Path(none_matches_sorted[0])
    else:
        result_dir = Path(valid_matches[0])

    amplitudes_path = result_dir / 'amplitudes_z.npy'

    # Find ROI mask
    roi_mask_candidates = [
        f'derivatives/sub-{subject_id}/roi_pipeline/{roi}_mask_thr50_intnearest_binTrue_masknone_gmTrue_subjFalse.nii.gz',
        f'derivatives/BH2009_{dataset}/{timestamp}/sub-{subject_id}_{roi}_mask.nii.gz',
        f'derivatives/roi_masks/sub-{subject_id}_{roi}_mask.nii.gz'
    ]

    roi_mask_path = None
    for candidate in roi_mask_candidates:
        if Path(candidate).exists():
            roi_mask_path = candidate
            break

    return str(amplitudes_path), roi_mask_path, str(result_dir)


# ============================================================================
# Validation Functions
# ============================================================================

def validate_file_existence(subjects, roi, timestamp, dataset):
    """
    Validate that amplitudes_z.npy files exist for all subjects

    Returns:
        dict with validation results
    """
    print(f"\n{'='*80}")
    print(f"[1/5] File Existence Validation")
    print(f"{'='*80}")

    results = {
        'passed': True,
        'subjects_found': [],
        'subjects_missing': [],
        'file_paths': {}
    }

    for subject_id in subjects:
        amp_path, roi_mask_path, result_dir = find_subject_amplitudes(
            subject_id, roi, timestamp, dataset
        )

        if amp_path is None:
            print(f"  ❌ sub-{subject_id}: amplitudes_z.npy NOT FOUND")
            results['subjects_missing'].append(subject_id)
            results['passed'] = False
        else:
            print(f"  ✅ sub-{subject_id}: {amp_path}")
            results['subjects_found'].append(subject_id)
            results['file_paths'][subject_id] = {
                'amplitudes': amp_path,
                'roi_mask': roi_mask_path,
                'result_dir': result_dir
            }

    print(f"\nSummary:")
    print(f"  Found: {len(results['subjects_found'])}/{len(subjects)}")
    print(f"  Missing: {len(results['subjects_missing'])}/{len(subjects)}")

    if results['subjects_missing']:
        print(f"\n  ⚠️  Missing subjects: {', '.join(results['subjects_missing'])}")

    return results


def validate_shape_consistency(file_existence_results):
    """
    Validate that all subjects have consistent shape

    Returns:
        dict with validation results
    """
    print(f"\n{'='*80}")
    print(f"[2/5] Shape Consistency Validation")
    print(f"{'='*80}")

    results = {
        'passed': True,
        'shapes': {},
        'n_runs': None,
        'n_colors': None,
        'n_voxels': None,
        'inconsistent_subjects': []
    }

    file_paths = file_existence_results['file_paths']

    # Load all shapes
    for subject_id, paths in file_paths.items():
        amp_path = paths['amplitudes']
        amplitudes = np.load(amp_path)
        shape = amplitudes.shape

        results['shapes'][subject_id] = shape
        print(f"  sub-{subject_id}: {shape} (runs × colors × voxels)")

    # Check consistency
    all_shapes = list(results['shapes'].values())

    if len(all_shapes) == 0:
        print(f"\n  ❌ No data loaded")
        results['passed'] = False
        return results

    # Extract dimensions
    n_runs_list = [s[0] for s in all_shapes]
    n_colors_list = [s[1] for s in all_shapes]
    n_voxels_list = [s[2] for s in all_shapes]

    # Check n_runs consistency
    if len(set(n_runs_list)) > 1:
        print(f"\n  ❌ INCONSISTENT n_runs across subjects!")
        print(f"     n_runs: {dict(zip(file_paths.keys(), n_runs_list))}")
        results['passed'] = False
        results['inconsistent_subjects'].append('n_runs')
    else:
        results['n_runs'] = n_runs_list[0]
        print(f"\n  ✅ n_runs consistent: {results['n_runs']}")

    # Check n_colors consistency
    if len(set(n_colors_list)) > 1:
        print(f"  ❌ INCONSISTENT n_colors across subjects!")
        print(f"     n_colors: {dict(zip(file_paths.keys(), n_colors_list))}")
        results['passed'] = False
        results['inconsistent_subjects'].append('n_colors')
    else:
        results['n_colors'] = n_colors_list[0]
        print(f"  ✅ n_colors consistent: {results['n_colors']}")

    # Check n_voxels consistency
    if len(set(n_voxels_list)) > 1:
        print(f"  ❌ INCONSISTENT n_voxels across subjects!")
        print(f"     n_voxels: {dict(zip(file_paths.keys(), n_voxels_list))}")

        # Show details
        for subject_id, n_voxels in zip(file_paths.keys(), n_voxels_list):
            print(f"       sub-{subject_id}: {n_voxels} voxels")

        results['passed'] = False
        results['inconsistent_subjects'].append('n_voxels')

        print(f"\n  ⚠️  CRITICAL ERROR: Cannot proceed with inconsistent voxel counts")
        print(f"      See docs/grouplevel_execution.md for solutions:")
        print(f"        - Option 1: MNI coordinate intersection (recommended)")
        print(f"        - Option 2: Zero padding (not recommended)")
    else:
        results['n_voxels'] = n_voxels_list[0]
        print(f"  ✅ n_voxels consistent: {results['n_voxels']}")

    return results


def validate_mni_space(file_existence_results):
    """
    Validate that all ROI masks are in same MNI space (same affine)

    Returns:
        dict with validation results
    """
    print(f"\n{'='*80}")
    print(f"[3/5] MNI Space Consistency Validation")
    print(f"{'='*80}")

    results = {
        'passed': True,
        'affines': {},
        'reference_affine': None,
        'inconsistent_subjects': []
    }

    file_paths = file_existence_results['file_paths']

    # Load affines
    reference_affine = None
    reference_subject = None

    for subject_id, paths in file_paths.items():
        roi_mask_path = paths['roi_mask']

        if roi_mask_path is None:
            print(f"  ⚠️  sub-{subject_id}: ROI mask not found, skipping")
            continue

        try:
            mask_img = nib.load(roi_mask_path)
            affine = mask_img.affine

            results['affines'][subject_id] = affine

            if reference_affine is None:
                reference_affine = affine
                reference_subject = subject_id
                print(f"  ✅ sub-{subject_id}: Loaded as reference")
            else:
                # Compare affine matrices
                if np.allclose(affine, reference_affine, atol=1e-5):
                    print(f"  ✅ sub-{subject_id}: Affine matches reference")
                else:
                    print(f"  ❌ sub-{subject_id}: Affine DIFFERS from reference")
                    print(f"     Max difference: {np.abs(affine - reference_affine).max():.6f}")
                    results['passed'] = False
                    results['inconsistent_subjects'].append(subject_id)

        except Exception as e:
            print(f"  ❌ sub-{subject_id}: Error loading ROI mask: {e}")
            results['passed'] = False

    results['reference_affine'] = reference_affine
    results['reference_subject'] = reference_subject

    if results['inconsistent_subjects']:
        print(f"\n  ⚠️  WARNING: {len(results['inconsistent_subjects'])} subjects have different affine matrices")
        print(f"      This may indicate different MNI spaces or preprocessing issues")
        print(f"      Subjects: {', '.join(results['inconsistent_subjects'])}")

    return results


def validate_data_quality(file_existence_results):
    """
    Validate data quality (NaN, Inf, range)

    Returns:
        dict with validation results
    """
    print(f"\n{'='*80}")
    print(f"[4/5] Data Quality Validation")
    print(f"{'='*80}")

    results = {
        'passed': True,
        'subjects_with_nan': [],
        'subjects_with_inf': [],
        'value_ranges': {}
    }

    file_paths = file_existence_results['file_paths']

    for subject_id, paths in file_paths.items():
        amp_path = paths['amplitudes']
        amplitudes = np.load(amp_path)

        # Check for NaN
        if np.isnan(amplitudes).any():
            n_nan = np.isnan(amplitudes).sum()
            print(f"  ❌ sub-{subject_id}: Contains {n_nan} NaN values")
            results['subjects_with_nan'].append(subject_id)
            results['passed'] = False
        else:
            print(f"  ✅ sub-{subject_id}: No NaN values")

        # Check for Inf
        if np.isinf(amplitudes).any():
            n_inf = np.isinf(amplitudes).sum()
            print(f"  ❌ sub-{subject_id}: Contains {n_inf} Inf values")
            results['subjects_with_inf'].append(subject_id)
            results['passed'] = False
        else:
            print(f"  ✅ sub-{subject_id}: No Inf values")

        # Value range (z-scored data should be roughly [-5, 5])
        value_min = amplitudes.min()
        value_max = amplitudes.max()
        value_mean = amplitudes.mean()
        value_std = amplitudes.std()

        results['value_ranges'][subject_id] = {
            'min': value_min,
            'max': value_max,
            'mean': value_mean,
            'std': value_std
        }

        # Warning for extreme values
        if abs(value_min) > 10 or abs(value_max) > 10:
            print(f"  ⚠️  sub-{subject_id}: Extreme values detected")
            print(f"     Range: [{value_min:.2f}, {value_max:.2f}]")
            print(f"     (z-scored data should typically be in [-5, 5])")

    print(f"\nValue Range Summary:")
    for subject_id, ranges in results['value_ranges'].items():
        print(f"  sub-{subject_id}: "
              f"[{ranges['min']:7.2f}, {ranges['max']:7.2f}], "
              f"mean={ranges['mean']:6.2f}, std={ranges['std']:6.2f}")

    return results


def validate_voxel_coordinates(file_existence_results):
    """
    Optional: Validate voxel coordinates overlap

    Returns:
        dict with validation results
    """
    print(f"\n{'='*80}")
    print(f"[5/5] Voxel Coordinate Overlap Validation (Optional)")
    print(f"{'='*80}")

    results = {
        'passed': True,
        'n_voxels_per_subject': {},
        'n_common_voxels': None,
        'overlap_percentage': None
    }

    file_paths = file_existence_results['file_paths']

    # Load all ROI masks
    masks = {}
    for subject_id, paths in file_paths.items():
        roi_mask_path = paths['roi_mask']

        if roi_mask_path is None:
            print(f"  ⚠️  sub-{subject_id}: ROI mask not found, skipping")
            continue

        try:
            mask_img = nib.load(roi_mask_path)
            mask_data = mask_img.get_fdata() > 0
            masks[subject_id] = mask_data

            n_voxels = mask_data.sum()
            results['n_voxels_per_subject'][subject_id] = n_voxels
            print(f"  ✅ sub-{subject_id}: {n_voxels} voxels in ROI mask")

        except Exception as e:
            print(f"  ❌ sub-{subject_id}: Error loading mask: {e}")

    if len(masks) == 0:
        print(f"\n  ⚠️  No masks loaded, skipping overlap validation")
        return results

    # Find intersection
    common_mask = np.logical_and.reduce(list(masks.values()))
    n_common_voxels = common_mask.sum()

    results['n_common_voxels'] = n_common_voxels

    # Calculate overlap percentage
    mean_n_voxels = np.mean(list(results['n_voxels_per_subject'].values()))
    overlap_percentage = 100 * n_common_voxels / mean_n_voxels

    results['overlap_percentage'] = overlap_percentage

    print(f"\nVoxel Overlap:")
    print(f"  Common voxels (intersection): {n_common_voxels}")
    print(f"  Mean voxels per subject: {mean_n_voxels:.0f}")
    print(f"  Overlap percentage: {overlap_percentage:.1f}%")

    if overlap_percentage < 90:
        print(f"\n  ⚠️  WARNING: Low voxel overlap ({overlap_percentage:.1f}%)")
        print(f"      This suggests subjects may have different ROI coverage")
        print(f"      Consider using MNI coordinate intersection approach")
        print(f"      See docs/grouplevel_execution.md for details")

    return results


# ============================================================================
# Report Generation
# ============================================================================

def generate_report(args, validation_results, output_file=None):
    """
    Generate validation report

    Args:
        args: Command-line arguments
        validation_results: Dict with all validation results
        output_file: Output file path (optional)
    """
    print(f"\n{'='*80}")
    print(f"VALIDATION REPORT SUMMARY")
    print(f"{'='*80}")

    # Overall status
    all_passed = all([
        validation_results['file_existence']['passed'],
        validation_results['shape_consistency']['passed'],
        validation_results['mni_space']['passed'],
        validation_results['data_quality']['passed']
    ])

    print(f"\nROI: {args.roi}")
    print(f"Timestamp: {args.timestamp}")
    print(f"Dataset: {args.dataset}")
    print(f"Subjects: {', '.join(args.subjects)}")

    print(f"\nValidation Results:")
    print(f"  [1] File Existence:     {'✅ PASSED' if validation_results['file_existence']['passed'] else '❌ FAILED'}")
    print(f"  [2] Shape Consistency:  {'✅ PASSED' if validation_results['shape_consistency']['passed'] else '❌ FAILED'}")
    print(f"  [3] MNI Space:          {'✅ PASSED' if validation_results['mni_space']['passed'] else '❌ FAILED'}")
    print(f"  [4] Data Quality:       {'✅ PASSED' if validation_results['data_quality']['passed'] else '❌ FAILED'}")
    print(f"  [5] Voxel Overlap:      {'ℹ️  INFO' if validation_results['voxel_overlap']['passed'] else '⚠️  WARNING'}")

    print(f"\n{'='*80}")
    if all_passed:
        print(f"✅ ALL CRITICAL VALIDATIONS PASSED")
        print(f"   Ready to proceed with group-level analysis")
        print(f"\n   Next step:")
        print(f"     sbatch run_group_level_analysis.sbatch")
    else:
        print(f"❌ VALIDATION FAILED")
        print(f"   Cannot proceed with group-level analysis")
        print(f"\n   Please fix the issues above and re-run validation")
        print(f"   See docs/grouplevel_execution.md for troubleshooting")
    print(f"{'='*80}")

    # Save to file
    if output_file is None:
        output_file = f"validation_report_{args.roi}_{args.timestamp}.txt"

    output_path = Path(output_file)

    with open(output_path, 'w') as f:
        f.write(f"Group-Level Analysis Data Validation Report\n")
        f.write(f"{'='*80}\n")
        f.write(f"Generated: {pd.Timestamp.now()}\n")
        f.write(f"\n")
        f.write(f"ROI: {args.roi}\n")
        f.write(f"Timestamp: {args.timestamp}\n")
        f.write(f"Dataset: {args.dataset}\n")
        f.write(f"Subjects: {', '.join(args.subjects)}\n")
        f.write(f"\n")
        f.write(f"{'='*80}\n")
        f.write(f"VALIDATION RESULTS\n")
        f.write(f"{'='*80}\n")
        f.write(f"\n")
        f.write(f"[1] File Existence: {'PASSED' if validation_results['file_existence']['passed'] else 'FAILED'}\n")
        f.write(f"    Found: {len(validation_results['file_existence']['subjects_found'])}\n")
        f.write(f"    Missing: {len(validation_results['file_existence']['subjects_missing'])}\n")
        if validation_results['file_existence']['subjects_missing']:
            f.write(f"    Missing subjects: {', '.join(validation_results['file_existence']['subjects_missing'])}\n")
        f.write(f"\n")

        f.write(f"[2] Shape Consistency: {'PASSED' if validation_results['shape_consistency']['passed'] else 'FAILED'}\n")
        f.write(f"    n_runs: {validation_results['shape_consistency']['n_runs']}\n")
        f.write(f"    n_colors: {validation_results['shape_consistency']['n_colors']}\n")
        f.write(f"    n_voxels: {validation_results['shape_consistency']['n_voxels']}\n")
        if validation_results['shape_consistency']['inconsistent_subjects']:
            f.write(f"    Inconsistent dimensions: {', '.join(validation_results['shape_consistency']['inconsistent_subjects'])}\n")
        f.write(f"\n")

        f.write(f"[3] MNI Space: {'PASSED' if validation_results['mni_space']['passed'] else 'FAILED'}\n")
        if validation_results['mni_space']['inconsistent_subjects']:
            f.write(f"    Inconsistent subjects: {', '.join(validation_results['mni_space']['inconsistent_subjects'])}\n")
        f.write(f"\n")

        f.write(f"[4] Data Quality: {'PASSED' if validation_results['data_quality']['passed'] else 'FAILED'}\n")
        if validation_results['data_quality']['subjects_with_nan']:
            f.write(f"    Subjects with NaN: {', '.join(validation_results['data_quality']['subjects_with_nan'])}\n")
        if validation_results['data_quality']['subjects_with_inf']:
            f.write(f"    Subjects with Inf: {', '.join(validation_results['data_quality']['subjects_with_inf'])}\n")
        f.write(f"\n")

        f.write(f"[5] Voxel Overlap: INFO\n")
        f.write(f"    Common voxels: {validation_results['voxel_overlap']['n_common_voxels']}\n")
        f.write(f"    Overlap percentage: {validation_results['voxel_overlap']['overlap_percentage']:.1f}%\n")
        f.write(f"\n")

        f.write(f"{'='*80}\n")
        f.write(f"OVERALL: {'PASSED' if all_passed else 'FAILED'}\n")
        f.write(f"{'='*80}\n")

    print(f"\n✅ Validation report saved to: {output_path}")

    return all_passed


# ============================================================================
# Main
# ============================================================================

def main():
    args = parse_args()

    print(f"\n{'='*80}")
    print(f"Group-Level Analysis Data Validation")
    print(f"{'='*80}")
    print(f"ROI: {args.roi}")
    print(f"Timestamp: {args.timestamp}")
    print(f"Dataset: {args.dataset}")
    print(f"Subjects: {', '.join(args.subjects)}")
    print(f"{'='*80}")

    # Run validations
    validation_results = {}

    # [1] File existence
    validation_results['file_existence'] = validate_file_existence(
        args.subjects, args.roi, args.timestamp, args.dataset
    )

    if not validation_results['file_existence']['passed']:
        print(f"\n❌ Critical validation failed: File existence")
        print(f"   Cannot proceed with further validations")
        sys.exit(1)

    # [2] Shape consistency
    validation_results['shape_consistency'] = validate_shape_consistency(
        validation_results['file_existence']
    )

    # [3] MNI space
    validation_results['mni_space'] = validate_mni_space(
        validation_results['file_existence']
    )

    # [4] Data quality
    validation_results['data_quality'] = validate_data_quality(
        validation_results['file_existence']
    )

    # [5] Voxel overlap
    validation_results['voxel_overlap'] = validate_voxel_coordinates(
        validation_results['file_existence']
    )

    # Generate report
    all_passed = generate_report(args, validation_results, args.output_file)

    # Exit with appropriate code
    if all_passed:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
