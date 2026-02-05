"""
CORRECTED Procrustes Analysis with Issue 1-3 fixes.

Fixes applied:
1. Correct disparity calculation: ||A @ R - B||_F^2 (not scale from scipy)
2. Correct rotation space: Voxel space (V×V), not color space (8×8)
3. Common voxel correspondence: Use intersection of voxels across subjects

Usage:
    python scripts/corrected_procrustes_analysis.py \
        --input-dir results/baseline_anova_selected \
        --output-dir results/corrected_procrustes \
        --hc-subjects 01,02,03,04,05,06,07 \
        --cvd-subjects 08,09,10
"""

import numpy as np
import json
import argparse
from pathlib import Path
from scipy.linalg import orthogonal_procrustes
from scipy.stats import spearmanr, mannwhitneyu
import sys

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'utils'))
from procrustes_normalized import procrustes_normalized


def load_subject_data(input_dir, subject, roi):
    """
    Load amplitudes and voxel indices for one subject.

    Returns
    -------
    amplitudes : np.ndarray, shape (n_runs, n_colors, n_voxels)
    voxel_indices : np.ndarray, shape (n_voxels,)
    """
    subj_roi_dir = input_dir / f"sub-{subject}" / roi

    amplitudes = np.load(subj_roi_dir / "amplitudes.npy")
    voxel_indices = np.load(subj_roi_dir / "voxel_indices.npy")

    return amplitudes, voxel_indices


def find_common_voxels(input_dir, roi, subjects):
    """
    Find voxels that are common (intersection) across all subjects.

    Returns
    -------
    common_indices : set
        Set of voxel indices present in all subjects
    """
    print(f"\nFinding common voxels for {roi}:")

    # Load voxel indices for all subjects
    all_indices = []
    for subject in subjects:
        try:
            _, voxel_indices = load_subject_data(input_dir, subject, roi)
            all_indices.append(set(voxel_indices))
            print(f"  sub-{subject}: {len(voxel_indices)} voxels")
        except Exception as e:
            print(f"  Warning: Failed to load sub-{subject}: {e}")

    if len(all_indices) < 2:
        print("  Error: Need at least 2 subjects")
        return None

    # Compute intersection
    common_indices = all_indices[0]
    for indices in all_indices[1:]:
        common_indices = common_indices & indices

    print(f"\n  Common voxels (intersection): {len(common_indices)}")
    print(f"  Percentage of original: {len(common_indices) / len(all_indices[0]) * 100:.1f}%")

    return sorted(common_indices)


def extract_common_voxel_data(amplitudes, voxel_indices, common_indices):
    """
    Extract amplitudes for only common voxels.

    Parameters
    ----------
    amplitudes : np.ndarray, shape (n_runs, n_colors, n_voxels_subject)
    voxel_indices : np.ndarray, shape (n_voxels_subject,)
    common_indices : list
        Common voxel indices

    Returns
    -------
    common_amplitudes : np.ndarray, shape (n_runs, n_colors, n_common_voxels)
    """
    # Find which positions in voxel_indices correspond to common_indices
    common_set = set(common_indices)
    mask = np.array([idx in common_set for idx in voxel_indices])

    # Extract amplitudes
    common_amplitudes = amplitudes[:, :, mask]

    # Sort by voxel index to ensure consistent ordering
    voxel_order = np.argsort(voxel_indices[mask])
    common_amplitudes = common_amplitudes[:, :, voxel_order]

    return common_amplitudes


def compute_subject_pattern(amplitudes):
    """
    Compute subject pattern from amplitudes using within-subject Procrustes.

    Parameters
    ----------
    amplitudes : np.ndarray, shape (n_runs, n_colors, n_voxels)

    Returns
    -------
    pattern : np.ndarray, shape (n_colors, n_voxels)
        Subject's average pattern after within-subject alignment
    """
    # Within-subject Procrustes
    aligned, _ = procrustes_normalized(amplitudes, reference='mean')

    # Average across runs
    pattern = np.mean(aligned, axis=0)

    return pattern


def align_to_reference_CORRECTED(source_pattern, reference_pattern):
    """
    CORRECTED Procrustes alignment.

    Fixes:
    1. No transpose - align in voxel space (V×V rotation)
    2. Compute actual disparity (Frobenius norm)

    Parameters
    ----------
    source_pattern : np.ndarray, shape (n_colors, n_voxels)
    reference_pattern : np.ndarray, shape (n_colors, n_voxels)

    Returns
    -------
    aligned_pattern : np.ndarray, shape (n_colors, n_voxels)
    disparity : float
        Correct Procrustes disparity: ||source @ R - reference||_F^2
    R : np.ndarray, shape (n_voxels, n_voxels)
        Rotation matrix in voxel space
    """
    # Center both patterns
    source_centered = source_pattern - source_pattern.mean()
    ref_centered = reference_pattern - reference_pattern.mean()

    # Scale both patterns
    source_scale = np.std(source_centered)
    ref_scale = np.std(ref_centered)

    if source_scale > 1e-10:
        source_normalized = source_centered / source_scale
    else:
        source_normalized = source_centered

    if ref_scale > 1e-10:
        ref_normalized = ref_centered / ref_scale
    else:
        ref_normalized = ref_centered

    # CORRECTED: No transpose! Align in voxel space
    # Input: (n_colors, n_voxels)
    # Output: R of shape (n_voxels, n_voxels)
    R, scale_from_scipy = orthogonal_procrustes(source_normalized, ref_normalized)

    # Apply transformation
    aligned_pattern = source_normalized @ R

    # CORRECTED: Compute actual disparity (Frobenius norm squared)
    residual = aligned_pattern - ref_normalized
    disparity = np.linalg.norm(residual, 'fro')**2

    return aligned_pattern, disparity, R


def compute_pairwise_disparities_CORRECTED(input_dir, roi, all_subjects, hc_subjects, cvd_subjects):
    """
    Compute pairwise disparities with CORRECTED Procrustes.

    Returns
    -------
    results : dict
    """
    print(f"\n{'='*80}")
    print(f"Processing {roi} with CORRECTED Procrustes")
    print(f"{'='*80}")

    # Find common voxels
    common_indices = find_common_voxels(input_dir, roi, all_subjects)

    if common_indices is None or len(common_indices) < 5:
        print(f"  Error: Not enough common voxels ({len(common_indices) if common_indices else 0})")
        return None

    # Load data for all subjects with common voxels only
    patterns = {}
    for subject in all_subjects:
        try:
            amplitudes, voxel_indices = load_subject_data(input_dir, subject, roi)

            # Extract common voxels
            common_amplitudes = extract_common_voxel_data(amplitudes, voxel_indices, common_indices)

            # Compute subject pattern
            pattern = compute_subject_pattern(common_amplitudes)

            patterns[subject] = pattern
            print(f"  Loaded sub-{subject}: pattern shape {pattern.shape}")

        except Exception as e:
            print(f"  Warning: Failed to load sub-{subject}: {e}")

    if len(patterns) < 2:
        print("  Error: Not enough subjects loaded")
        return None

    # Compute pairwise disparities
    hc_to_hc_disparities = []
    cvd_to_hc_disparities = []
    disparity_matrix = {}

    for ref_subject in hc_subjects:
        if ref_subject not in patterns:
            continue

        ref_pattern = patterns[ref_subject]

        for target_subject, target_pattern in patterns.items():
            if target_subject == ref_subject:
                continue

            # CORRECTED alignment
            aligned, disparity, R = align_to_reference_CORRECTED(target_pattern, ref_pattern)

            # Store
            disparity_matrix[(ref_subject, target_subject)] = disparity

            # Categorize
            if target_subject in hc_subjects:
                hc_to_hc_disparities.append(disparity)
            elif target_subject in cvd_subjects:
                cvd_to_hc_disparities.append(disparity)

    # Convert to arrays
    hc_to_hc_disparities = np.array(hc_to_hc_disparities)
    cvd_to_hc_disparities = np.array(cvd_to_hc_disparities)

    print(f"\n  HC→HC disparities: n={len(hc_to_hc_disparities)}")
    print(f"  CVD→HC disparities: n={len(cvd_to_hc_disparities)}")

    # Statistical test
    if len(hc_to_hc_disparities) > 0 and len(cvd_to_hc_disparities) > 0:
        u_stat, p_value = mannwhitneyu(hc_to_hc_disparities, cvd_to_hc_disparities, alternative='two-sided')
        effect_size = (np.mean(cvd_to_hc_disparities) - np.mean(hc_to_hc_disparities)) / \
                      np.sqrt((np.std(hc_to_hc_disparities)**2 + np.std(cvd_to_hc_disparities)**2) / 2)
    else:
        u_stat, p_value = np.nan, np.nan
        effect_size = np.nan

    # Normalized disparities
    n_colors = 8
    n_voxels = len(common_indices)
    norm_factor = n_colors * n_voxels

    hc_norm = hc_to_hc_disparities / norm_factor
    cvd_norm = cvd_to_hc_disparities / norm_factor

    # Results
    results = {
        'roi': roi,
        'n_common_voxels': len(common_indices),
        'n_hc_subjects': len([s for s in hc_subjects if s in patterns]),
        'n_cvd_subjects': len([s for s in cvd_subjects if s in patterns]),
        'common_voxel_indices': [int(x) for x in common_indices],  # Convert to int for JSON
        'disparity_matrix': {f"{k[0]}->{k[1]}": float(v) for k, v in disparity_matrix.items()},
        'hc_to_hc': {
            'raw': {
                'disparities': hc_to_hc_disparities.tolist(),
                'mean': float(np.mean(hc_to_hc_disparities)),
                'std': float(np.std(hc_to_hc_disparities)),
                'median': float(np.median(hc_to_hc_disparities)),
                'min': float(np.min(hc_to_hc_disparities)),
                'max': float(np.max(hc_to_hc_disparities))
            },
            'normalized': {
                'disparities': hc_norm.tolist(),
                'mean': float(np.mean(hc_norm)),
                'std': float(np.std(hc_norm)),
                'median': float(np.median(hc_norm)),
                'min': float(np.min(hc_norm)),
                'max': float(np.max(hc_norm))
            }
        },
        'cvd_to_hc': {
            'raw': {
                'disparities': cvd_to_hc_disparities.tolist(),
                'mean': float(np.mean(cvd_to_hc_disparities)),
                'std': float(np.std(cvd_to_hc_disparities)),
                'median': float(np.median(cvd_to_hc_disparities)),
                'min': float(np.min(cvd_to_hc_disparities)),
                'max': float(np.max(cvd_to_hc_disparities))
            },
            'normalized': {
                'disparities': cvd_norm.tolist(),
                'mean': float(np.mean(cvd_norm)),
                'std': float(np.std(cvd_norm)),
                'median': float(np.median(cvd_norm)),
                'min': float(np.min(cvd_norm)),
                'max': float(np.max(cvd_norm))
            }
        },
        'statistical_test': {
            'test': 'Mann-Whitney U',
            'u_statistic': float(u_stat) if not np.isnan(u_stat) else None,
            'p_value': float(p_value) if not np.isnan(p_value) else None,
            'effect_size_cohens_d': float(effect_size) if not np.isnan(effect_size) else None
        }
    }

    # Print summary
    print(f"\n  Results (Raw Disparity):")
    print(f"    HC→HC:  {results['hc_to_hc']['raw']['mean']:.4f} ± {results['hc_to_hc']['raw']['std']:.4f}")
    print(f"    CVD→HC: {results['cvd_to_hc']['raw']['mean']:.4f} ± {results['cvd_to_hc']['raw']['std']:.4f}")
    print(f"    Difference: {results['cvd_to_hc']['raw']['mean'] - results['hc_to_hc']['raw']['mean']:.4f}")

    print(f"\n  Results (Normalized Disparity):")
    print(f"    HC→HC:  {results['hc_to_hc']['normalized']['mean']:.4f} ± {results['hc_to_hc']['normalized']['std']:.4f}")
    print(f"    CVD→HC: {results['cvd_to_hc']['normalized']['mean']:.4f} ± {results['cvd_to_hc']['normalized']['std']:.4f}")

    print(f"\n  Statistics:")
    print(f"    Effect size (Cohen's d): {results['statistical_test']['effect_size_cohens_d']:.4f}")
    if results['statistical_test']['p_value'] is not None:
        print(f"    p-value: {results['statistical_test']['p_value']:.4f}")

    return results


def main():
    parser = argparse.ArgumentParser(
        description='CORRECTED Procrustes analysis with Issue 1-3 fixes'
    )
    parser.add_argument('--input-dir', type=str, required=True)
    parser.add_argument('--output-dir', type=str, required=True)
    parser.add_argument('--hc-subjects', type=str, default='01,02,03,04,05,06,07')
    parser.add_argument('--cvd-subjects', type=str, default='08,09,10')
    parser.add_argument('--exclude-v3', type=str, default='07')

    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    hc_subjects = args.hc_subjects.split(',')
    cvd_subjects = args.cvd_subjects.split(',')
    exclude_v3 = args.exclude_v3.split(',') if args.exclude_v3 else []

    print("="*80)
    print("CORRECTED Procrustes Analysis")
    print("="*80)
    print("\nFixes applied:")
    print("  1. Correct disparity: ||A @ R - B||_F^2")
    print("  2. Correct rotation: Voxel space (no transpose)")
    print("  3. Common voxels: Intersection across subjects")
    print("="*80)

    all_results = {}

    for roi in ['V1', 'V2', 'V3', 'hV4']:
        exclude = exclude_v3 if roi == 'V3' else []
        all_subjects = [s for s in hc_subjects + cvd_subjects if s not in exclude]

        results = compute_pairwise_disparities_CORRECTED(
            input_dir, roi, all_subjects, hc_subjects, cvd_subjects
        )

        if results:
            all_results[roi] = results

            # Save per-ROI
            roi_output = output_dir / f"{roi}_corrected_results.json"
            with open(roi_output, 'w') as f:
                json.dump(results, f, indent=2)

            print(f"\n  Saved: {roi_output}")

    # Save summary
    summary_path = output_dir / "corrected_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(all_results, f, indent=2)

    # Print final summary
    print("\n" + "="*80)
    print("CORRECTED Results Summary")
    print("="*80)
    print(f"\n{'ROI':<8} {'#Voxels':<10} {'HC→HC (norm)':<20} {'CVD→HC (norm)':<20} {'Diff':<12} {'p-value':<10}")
    print("-"*80)

    for roi in ['V1', 'V2', 'V3', 'hV4']:
        if roi in all_results:
            n_vox = all_results[roi]['n_common_voxels']
            hc = all_results[roi]['hc_to_hc']['normalized']['mean']
            cvd = all_results[roi]['cvd_to_hc']['normalized']['mean']
            diff = cvd - hc
            p = all_results[roi]['statistical_test']['p_value']
            p_str = f"{p:.4f}" if p is not None else "N/A"

            print(f"{roi:<8} {n_vox:<10} {hc:<20.4f} {cvd:<20.4f} {diff:<12.4f} {p_str:<10}")

    print("="*80)
    print(f"\n✅ Results saved to: {summary_path}")


if __name__ == '__main__':
    main()
