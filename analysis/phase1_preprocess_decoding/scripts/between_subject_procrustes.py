"""
Between-subject Procrustes alignment with HC reference.

This script:
1. Loads ANOVA-selected amplitudes for all subjects
2. Computes HC reference (mean of HC subjects)
3. Aligns each subject to HC reference using Procrustes
4. Computes disparities and RDM correlations
5. Compares HC-to-HC reliability vs CVD disparities

Usage:
    python scripts/between_subject_procrustes.py \
        --input-dir results/baseline_anova_selected \
        --output-dir results/between_subject_procrustes \
        --hc-subjects 01,02,03,04,05,06,07 \
        --cvd-subjects 08,09,10
"""

import numpy as np
import json
import argparse
from pathlib import Path
from scipy.linalg import orthogonal_procrustes
from scipy.stats import spearmanr
import sys

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'utils'))
from procrustes_normalized import procrustes_normalized


def load_subject_amplitudes(input_dir, subject, roi):
    """
    Load amplitudes for one subject-ROI pair.

    Returns
    -------
    amplitudes : np.ndarray, shape (n_runs, n_colors, n_voxels)
        Selected amplitudes
    metadata : dict
        Selection metadata
    """
    subj_roi_dir = input_dir / f"sub-{subject}" / roi

    # Load data
    amplitudes = np.load(subj_roi_dir / "amplitudes.npy")

    with open(subj_roi_dir / "selection_metadata.json") as f:
        metadata = json.load(f)

    return amplitudes, metadata


def compute_rdm_correlation(amplitudes):
    """
    Compute RDM from amplitudes (Pearson correlation-based).

    Parameters
    ----------
    amplitudes : np.ndarray, shape (n_runs, n_colors, n_voxels)
        Amplitudes (after within-subject Procrustes)

    Returns
    -------
    rdm : np.ndarray, shape (n_colors, n_colors)
        Average RDM across runs (1 - correlation)
    """
    n_runs, n_colors, n_voxels = amplitudes.shape

    rdms = []
    for r in range(n_runs):
        # Correlation distance: 1 - corr
        corr_matrix = np.corrcoef(amplitudes[r])
        rdm = 1 - corr_matrix
        rdms.append(rdm)

    # Average across runs
    rdm_avg = np.mean(rdms, axis=0)

    return rdm_avg


def align_subject_to_reference(subject_amps, reference_pattern):
    """
    Align subject's average pattern to reference using Procrustes.

    Parameters
    ----------
    subject_amps : np.ndarray, shape (n_runs, n_colors, n_voxels)
        Subject amplitudes
    reference_pattern : np.ndarray, shape (n_colors, n_voxels)
        Reference pattern (HC mean)

    Returns
    -------
    aligned_pattern : np.ndarray, shape (n_colors, n_voxels)
        Aligned subject pattern
    disparity : float
        Procrustes disparity
    transformation : np.ndarray, shape (n_voxels, n_voxels)
        Orthogonal transformation matrix
    """
    # Average across runs (within-subject first)
    subject_pattern = np.mean(subject_amps, axis=0)  # (n_colors, n_voxels)

    # Center both patterns
    subject_centered = subject_pattern - subject_pattern.mean()
    ref_centered = reference_pattern - reference_pattern.mean()

    # Scale both patterns
    subject_scale = np.std(subject_centered)
    ref_scale = np.std(ref_centered)

    if subject_scale > 1e-10:
        subject_normalized = subject_centered / subject_scale
    else:
        subject_normalized = subject_centered

    if ref_scale > 1e-10:
        ref_normalized = ref_centered / ref_scale
    else:
        ref_normalized = ref_centered

    # Procrustes alignment
    R, disparity = orthogonal_procrustes(subject_normalized.T, ref_normalized.T)

    # Apply transformation
    aligned_pattern = (subject_normalized.T @ R).T

    return aligned_pattern, disparity, R


def process_roi(input_dir, roi, hc_subjects, cvd_subjects, exclude_subjects=None):
    """
    Process one ROI: align all subjects to HC reference.

    Parameters
    ----------
    input_dir : Path
        Directory with ANOVA-selected amplitudes
    roi : str
        ROI name
    hc_subjects : list of str
        HC subject IDs
    cvd_subjects : list of str
        CVD subject IDs
    exclude_subjects : list of str, optional
        Subjects to exclude (e.g., sub-07 for V3)

    Returns
    -------
    results : dict
        Alignment results with disparities and RDM correlations
    """
    if exclude_subjects is None:
        exclude_subjects = []

    print(f"\nProcessing {roi}:")
    print(f"  HC subjects: {hc_subjects}")
    print(f"  CVD subjects: {cvd_subjects}")
    print(f"  Excluded subjects: {exclude_subjects}")

    # Load HC subjects
    hc_patterns = []
    hc_subjects_loaded = []

    for subject in hc_subjects:
        if subject in exclude_subjects:
            print(f"  Skipping sub-{subject} (excluded)")
            continue

        try:
            amplitudes, metadata = load_subject_amplitudes(input_dir, subject, roi)

            # Apply within-subject Procrustes first
            aligned, disparities = procrustes_normalized(amplitudes, reference='mean')

            # Average across runs to get subject pattern
            pattern = np.mean(aligned, axis=0)  # (n_colors, n_voxels)

            hc_patterns.append(pattern)
            hc_subjects_loaded.append(subject)
        except Exception as e:
            print(f"  Warning: Failed to load sub-{subject}: {e}")

    if len(hc_patterns) < 2:
        print(f"  Error: Need at least 2 HC subjects, got {len(hc_patterns)}")
        return None

    # Compute HC reference (mean pattern)
    hc_patterns = np.array(hc_patterns)  # (n_hc, n_colors, n_voxels)
    hc_reference = np.mean(hc_patterns, axis=0)  # (n_colors, n_voxels)

    print(f"  HC reference computed from {len(hc_patterns)} subjects")
    print(f"  Reference shape: {hc_reference.shape}")

    # Compute HC reference RDM (from HC reference pattern)
    # Create fake "amplitudes" with single run for RDM computation
    hc_ref_amps = hc_reference[np.newaxis, :, :]  # (1, n_colors, n_voxels)
    hc_ref_rdm = 1 - np.corrcoef(hc_ref_amps[0])  # (n_colors, n_colors)

    print(f"  HC reference RDM computed: {hc_ref_rdm.shape}")

    # Align all HC subjects to HC reference
    hc_results = {}
    hc_disparities = []
    hc_rdm_correlations = []

    for i, subject in enumerate(hc_subjects_loaded):
        # Reload amplitudes to get full runs
        amplitudes, metadata = load_subject_amplitudes(input_dir, subject, roi)

        # Align to HC reference
        aligned_pattern, disparity, R = align_subject_to_reference(
            amplitudes, hc_reference
        )

        # Compute subject RDM
        rdm = compute_rdm_correlation(amplitudes)

        # Compute RDM correlation with HC reference RDM
        triu_idx = np.triu_indices(rdm.shape[0], k=1)
        rdm_corr, _ = spearmanr(rdm[triu_idx], hc_ref_rdm[triu_idx])

        hc_results[f"sub-{subject}"] = {
            'disparity': float(disparity),
            'rdm_correlation': float(rdm_corr),
            'group': 'HC'
        }

        hc_disparities.append(disparity)
        hc_rdm_correlations.append(rdm_corr)

    # Align all CVD subjects to HC reference
    cvd_results = {}
    cvd_disparities = []
    cvd_rdm_correlations = []

    for subject in cvd_subjects:
        if subject in exclude_subjects:
            print(f"  Skipping sub-{subject} (excluded)")
            continue

        try:
            amplitudes, metadata = load_subject_amplitudes(input_dir, subject, roi)

            # Align to HC reference
            aligned_pattern, disparity, R = align_subject_to_reference(
                amplitudes, hc_reference
            )

            # Compute subject RDM
            rdm = compute_rdm_correlation(amplitudes)

            # Compute RDM correlation with HC reference RDM
            triu_idx = np.triu_indices(rdm.shape[0], k=1)
            rdm_corr, _ = spearmanr(rdm[triu_idx], hc_ref_rdm[triu_idx])

            cvd_results[f"sub-{subject}"] = {
                'disparity': float(disparity),
                'rdm_correlation': float(rdm_corr),
                'group': 'CVD'
            }

            cvd_disparities.append(disparity)
            cvd_rdm_correlations.append(rdm_corr)

        except Exception as e:
            print(f"  Warning: Failed to load sub-{subject}: {e}")

    # Aggregate results
    results = {
        'roi': roi,
        'hc_subjects': hc_subjects_loaded,
        'cvd_subjects': [s for s in cvd_subjects if s not in exclude_subjects],
        'excluded_subjects': exclude_subjects,
        'hc_reference_shape': hc_reference.shape,
        'subjects': {**hc_results, **cvd_results},
        'summary': {
            'hc': {
                'n_subjects': len(hc_disparities),
                'disparity': {
                    'mean': float(np.mean(hc_disparities)),
                    'std': float(np.std(hc_disparities)),
                    'min': float(np.min(hc_disparities)),
                    'max': float(np.max(hc_disparities))
                },
                'rdm_correlation': {
                    'mean': float(np.mean(hc_rdm_correlations)),
                    'std': float(np.std(hc_rdm_correlations)),
                    'min': float(np.min(hc_rdm_correlations)),
                    'max': float(np.max(hc_rdm_correlations))
                }
            },
            'cvd': {
                'n_subjects': len(cvd_disparities),
                'disparity': {
                    'mean': float(np.mean(cvd_disparities)),
                    'std': float(np.std(cvd_disparities)),
                    'min': float(np.min(cvd_disparities)),
                    'max': float(np.max(cvd_disparities))
                },
                'rdm_correlation': {
                    'mean': float(np.mean(cvd_rdm_correlations)),
                    'std': float(np.std(cvd_rdm_correlations)),
                    'min': float(np.min(cvd_rdm_correlations)),
                    'max': float(np.max(cvd_rdm_correlations))
                }
            }
        }
    }

    print(f"\n  HC disparity: {results['summary']['hc']['disparity']['mean']:.4f} ± {results['summary']['hc']['disparity']['std']:.4f}")
    print(f"  CVD disparity: {results['summary']['cvd']['disparity']['mean']:.4f} ± {results['summary']['cvd']['disparity']['std']:.4f}")
    print(f"  HC RDM correlation: {results['summary']['hc']['rdm_correlation']['mean']:.4f} ± {results['summary']['hc']['rdm_correlation']['std']:.4f}")
    print(f"  CVD RDM correlation: {results['summary']['cvd']['rdm_correlation']['mean']:.4f} ± {results['summary']['cvd']['rdm_correlation']['std']:.4f}")

    return results


def main():
    parser = argparse.ArgumentParser(
        description='Between-subject Procrustes alignment with HC reference'
    )
    parser.add_argument('--input-dir', type=str, required=True,
                        help='Directory with ANOVA-selected amplitudes')
    parser.add_argument('--output-dir', type=str, required=True,
                        help='Output directory for alignment results')
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

    print("="*80)
    print("Between-Subject Procrustes Alignment with HC Reference")
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

        results = process_roi(
            input_dir, roi, hc_subjects, cvd_subjects, exclude_subjects=exclude
        )

        if results:
            all_results[roi] = results

            # Save ROI-specific results
            roi_output = output_dir / f"{roi}_alignment_results.json"
            with open(roi_output, 'w') as f:
                json.dump(results, f, indent=2)

            print(f"\n  Saved: {roi_output}")

    # Save summary
    summary_path = output_dir / "alignment_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(all_results, f, indent=2)

    print("\n" + "="*80)
    print(f"✅ Completed: {len(all_results)} ROIs processed")
    print(f"Summary saved to: {summary_path}")
    print("="*80)


if __name__ == '__main__':
    main()
