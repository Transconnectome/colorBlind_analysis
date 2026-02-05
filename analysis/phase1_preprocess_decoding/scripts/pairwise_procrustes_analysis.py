"""
Pairwise Procrustes analysis with individual HC references.

Instead of using mean HC as reference, this script:
1. Uses each HC subject as an individual reference
2. Aligns all other subjects to each HC reference
3. Forms distributions of HC-to-HC vs CVD-to-HC disparities
4. Compares distributions statistically

Usage:
    python scripts/pairwise_procrustes_analysis.py \
        --input-dir results/baseline_anova_selected \
        --output-dir results/pairwise_procrustes \
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


def load_subject_pattern(input_dir, subject, roi):
    """
    Load and compute subject pattern (averaged across runs after within-subject Procrustes).

    Returns
    -------
    pattern : np.ndarray, shape (n_colors, n_voxels)
        Subject's average pattern
    """
    subj_roi_dir = input_dir / f"sub-{subject}" / roi

    # Load selected amplitudes
    amplitudes = np.load(subj_roi_dir / "amplitudes.npy")  # (n_runs, n_colors, n_voxels)

    # Within-subject Procrustes
    aligned, disparities = procrustes_normalized(amplitudes, reference='mean')

    # Average across runs
    pattern = np.mean(aligned, axis=0)  # (n_colors, n_voxels)

    return pattern


def align_to_reference(source_pattern, reference_pattern):
    """
    Align source pattern to reference using normalized Procrustes.

    Parameters
    ----------
    source_pattern : np.ndarray, shape (n_colors, n_voxels)
        Pattern to align
    reference_pattern : np.ndarray, shape (n_colors, n_voxels)
        Reference pattern

    Returns
    -------
    aligned_pattern : np.ndarray, shape (n_colors, n_voxels)
        Aligned source pattern
    disparity : float
        Procrustes disparity
    R : np.ndarray, shape (n_voxels, n_voxels)
        Rotation matrix
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

    # Procrustes alignment
    R, disparity = orthogonal_procrustes(source_normalized.T, ref_normalized.T)

    # Apply transformation
    aligned_pattern = (source_normalized.T @ R).T

    return aligned_pattern, disparity, R


def compute_pairwise_disparities(input_dir, roi, all_subjects, hc_subjects, cvd_subjects, exclude_subjects=None):
    """
    Compute pairwise disparities with each HC as reference.

    Parameters
    ----------
    input_dir : Path
        Directory with ANOVA-selected amplitudes
    roi : str
        ROI name
    all_subjects : list of str
        All subject IDs to load
    hc_subjects : list of str
        HC subject IDs (potential references)
    cvd_subjects : list of str
        CVD subject IDs
    exclude_subjects : list of str, optional
        Subjects to exclude

    Returns
    -------
    results : dict
        Pairwise disparity results with distributions
    """
    if exclude_subjects is None:
        exclude_subjects = []

    print(f"\nProcessing {roi}:")
    print(f"  HC subjects (references): {hc_subjects}")
    print(f"  CVD subjects: {cvd_subjects}")
    print(f"  Excluded: {exclude_subjects}")

    # Load all subject patterns
    patterns = {}
    for subject in all_subjects:
        if subject in exclude_subjects:
            continue

        try:
            pattern = load_subject_pattern(input_dir, subject, roi)
            patterns[subject] = pattern
            print(f"  Loaded sub-{subject}: {pattern.shape}")
        except Exception as e:
            print(f"  Warning: Failed to load sub-{subject}: {e}")

    # Compute pairwise disparities: each HC as reference
    hc_to_hc_disparities = []  # HC reference -> other HC
    cvd_to_hc_disparities = []  # HC reference -> CVD

    disparity_matrix = {}  # {(ref_subject, target_subject): disparity}

    for ref_subject in hc_subjects:
        if ref_subject not in patterns:
            continue

        ref_pattern = patterns[ref_subject]

        # Align all other subjects to this HC reference
        for target_subject, target_pattern in patterns.items():
            if target_subject == ref_subject:
                continue  # Skip self-alignment

            # Align target to reference
            aligned, disparity, R = align_to_reference(target_pattern, ref_pattern)

            # Store in matrix
            disparity_matrix[(ref_subject, target_subject)] = disparity

            # Categorize
            if target_subject in hc_subjects:
                hc_to_hc_disparities.append(disparity)
            elif target_subject in cvd_subjects:
                cvd_to_hc_disparities.append(disparity)

    # Convert to arrays
    hc_to_hc_disparities = np.array(hc_to_hc_disparities)
    cvd_to_hc_disparities = np.array(cvd_to_hc_disparities)

    print(f"\n  HC-to-HC disparities: n={len(hc_to_hc_disparities)}")
    print(f"  CVD-to-HC disparities: n={len(cvd_to_hc_disparities)}")

    # Statistical comparison
    if len(hc_to_hc_disparities) > 0 and len(cvd_to_hc_disparities) > 0:
        u_stat, p_value = mannwhitneyu(hc_to_hc_disparities, cvd_to_hc_disparities, alternative='two-sided')
    else:
        u_stat, p_value = np.nan, np.nan

    # Aggregate results
    results = {
        'roi': roi,
        'n_hc_subjects': len([s for s in hc_subjects if s in patterns]),
        'n_cvd_subjects': len([s for s in cvd_subjects if s in patterns]),
        'disparity_matrix': {f"{k[0]}->{k[1]}": float(v) for k, v in disparity_matrix.items()},
        'hc_to_hc': {
            'disparities': hc_to_hc_disparities.tolist(),
            'n': len(hc_to_hc_disparities),
            'mean': float(np.mean(hc_to_hc_disparities)),
            'std': float(np.std(hc_to_hc_disparities)),
            'median': float(np.median(hc_to_hc_disparities)),
            'min': float(np.min(hc_to_hc_disparities)),
            'max': float(np.max(hc_to_hc_disparities)),
            'percentiles': {
                '25': float(np.percentile(hc_to_hc_disparities, 25)),
                '50': float(np.percentile(hc_to_hc_disparities, 50)),
                '75': float(np.percentile(hc_to_hc_disparities, 75))
            }
        },
        'cvd_to_hc': {
            'disparities': cvd_to_hc_disparities.tolist(),
            'n': len(cvd_to_hc_disparities),
            'mean': float(np.mean(cvd_to_hc_disparities)),
            'std': float(np.std(cvd_to_hc_disparities)),
            'median': float(np.median(cvd_to_hc_disparities)),
            'min': float(np.min(cvd_to_hc_disparities)),
            'max': float(np.max(cvd_to_hc_disparities)),
            'percentiles': {
                '25': float(np.percentile(cvd_to_hc_disparities, 25)),
                '50': float(np.percentile(cvd_to_hc_disparities, 50)),
                '75': float(np.percentile(cvd_to_hc_disparities, 75))
            }
        },
        'statistical_test': {
            'test': 'Mann-Whitney U',
            'u_statistic': float(u_stat) if not np.isnan(u_stat) else None,
            'p_value': float(p_value) if not np.isnan(p_value) else None,
            'effect_size': float((np.mean(cvd_to_hc_disparities) - np.mean(hc_to_hc_disparities)) /
                                 np.sqrt((np.std(hc_to_hc_disparities)**2 + np.std(cvd_to_hc_disparities)**2) / 2))
        }
    }

    # Print summary
    print(f"\n  Results:")
    print(f"    HC-to-HC:  {results['hc_to_hc']['mean']:.4f} ± {results['hc_to_hc']['std']:.4f}")
    print(f"    CVD-to-HC: {results['cvd_to_hc']['mean']:.4f} ± {results['cvd_to_hc']['std']:.4f}")
    print(f"    Difference: {results['cvd_to_hc']['mean'] - results['hc_to_hc']['mean']:.4f}")
    print(f"    Effect size (Cohen's d): {results['statistical_test']['effect_size']:.4f}")
    if results['statistical_test']['p_value'] is not None:
        print(f"    p-value: {results['statistical_test']['p_value']:.4f}")

    return results


def main():
    parser = argparse.ArgumentParser(
        description='Pairwise Procrustes analysis with individual HC references'
    )
    parser.add_argument('--input-dir', type=str, required=True,
                        help='Directory with ANOVA-selected amplitudes')
    parser.add_argument('--output-dir', type=str, required=True,
                        help='Output directory for results')
    parser.add_argument('--hc-subjects', type=str, default='01,02,03,04,05,06,07',
                        help='HC subject IDs (comma-separated)')
    parser.add_argument('--cvd-subjects', type=str, default='08,09,10',
                        help='CVD subject IDs (comma-separated)')
    parser.add_argument('--exclude-v3', type=str, default='07',
                        help='Subjects to exclude from V3 (comma-separated)')

    args = parser.parse_args()

    # Parse arguments
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    hc_subjects = args.hc_subjects.split(',')
    cvd_subjects = args.cvd_subjects.split(',')
    exclude_v3 = args.exclude_v3.split(',') if args.exclude_v3 else []

    all_subjects = hc_subjects + cvd_subjects

    print("="*80)
    print("Pairwise Procrustes Analysis with Individual HC References")
    print("="*80)
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    print(f"HC subjects: {hc_subjects}")
    print(f"CVD subjects: {cvd_subjects}")
    print(f"V3 exclusions: {exclude_v3}")
    print("="*80)

    # Process all ROIs
    all_results = {}

    for roi in ['V1', 'V2', 'V3', 'hV4']:
        exclude = exclude_v3 if roi == 'V3' else []

        results = compute_pairwise_disparities(
            input_dir, roi, all_subjects, hc_subjects, cvd_subjects,
            exclude_subjects=exclude
        )

        all_results[roi] = results

        # Save ROI-specific results
        roi_output = output_dir / f"{roi}_pairwise_results.json"
        with open(roi_output, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\n  Saved: {roi_output}")

    # Save summary
    summary_path = output_dir / "pairwise_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(all_results, f, indent=2)

    # Print overall summary
    print("\n" + "="*80)
    print("Summary: HC-to-HC vs CVD-to-HC Disparities")
    print("="*80)
    print(f"{'ROI':<8} {'HC→HC Mean':<15} {'CVD→HC Mean':<15} {'Diff':<12} {'Effect Size':<12} {'p-value':<10}")
    print("-"*80)

    for roi in ['V1', 'V2', 'V3', 'hV4']:
        if roi in all_results:
            hc_mean = all_results[roi]['hc_to_hc']['mean']
            cvd_mean = all_results[roi]['cvd_to_hc']['mean']
            diff = cvd_mean - hc_mean
            effect = all_results[roi]['statistical_test']['effect_size']
            p_val = all_results[roi]['statistical_test']['p_value']
            p_str = f"{p_val:.4f}" if p_val is not None else "N/A"

            print(f"{roi:<8} {hc_mean:<15.4f} {cvd_mean:<15.4f} {diff:<12.4f} {effect:<12.4f} {p_str:<10}")

    print("="*80)
    print(f"\n✅ Results saved to: {summary_path}")
    print("="*80)


if __name__ == '__main__':
    main()
