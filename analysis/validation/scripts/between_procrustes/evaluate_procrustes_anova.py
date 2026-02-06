#!/usr/bin/env python3
"""
evaluate_procrustes_anova.py
-----------------------------
Between-subject Procrustes evaluation with ANOVA voxel selection

Pipeline:
1. Load common voxel amplitudes for all subjects
2. Compute ANOVA rankings and select top-k voxels
3. Apply between-subject Procrustes (HC reference)
4. Compute disparities (HC-HC vs CVD-HC)
5. Compute RDM similarities and statistical tests
6. Generate visualizations
"""

import numpy as np
import json
from pathlib import Path
from typing import Dict, Tuple, List
from scipy.stats import ttest_ind, spearmanr
from scipy.spatial.distance import pdist, squareform
from scipy.linalg import orthogonal_procrustes


def compute_rdm_from_amplitudes(amplitudes: np.ndarray) -> np.ndarray:
    """
    Compute RDM from amplitudes (averaged across runs)

    Parameters
    ----------
    amplitudes : np.ndarray
        (n_runs, n_colors, n_voxels)

    Returns
    -------
    rdm : np.ndarray
        (n_colors, n_colors) dissimilarity matrix using Pearson correlation
    """
    # Average across runs
    mean_patterns = np.mean(amplitudes, axis=0)  # (n_colors, n_voxels)

    # Pearson dissimilarity
    rdm = 1 - np.corrcoef(mean_patterns)

    return rdm


def compute_procrustes_disparity_between_subjects(X: np.ndarray, Y: np.ndarray) -> float:
    """
    Compute Procrustes disparity between two subjects' pattern sets

    Parameters
    ----------
    X, Y : np.ndarray
        (n_colors, n_voxels) pattern matrices (averaged across runs)

    Returns
    -------
    disparity : float
        Frobenius norm of residual after alignment
    """
    # Center and scale
    X_centered = X - X.mean(axis=0)
    Y_centered = Y - Y.mean(axis=0)

    X_scaled = X_centered / np.linalg.norm(X_centered, 'fro')
    Y_scaled = Y_centered / np.linalg.norm(Y_centered, 'fro')

    # Find optimal rotation
    R, scale = orthogonal_procrustes(X_scaled, Y_scaled)

    # Compute disparity
    Y_aligned = X_scaled @ R
    disparity = np.linalg.norm(Y_aligned - Y_scaled, 'fro')

    return disparity


def compute_between_subject_disparities(amplitudes_dict: Dict[str, np.ndarray],
                                       subjects_hc: List[str],
                                       subjects_cvd: List[str]) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute HC-HC and CVD-HC Procrustes disparities

    Strategy:
    1. Compute HC reference: mean of HC subjects' averaged patterns
    2. Align each HC subject to HC reference → HC-HC disparities
    3. Align each CVD subject to HC reference → CVD-HC disparities

    Parameters
    ----------
    amplitudes_dict : Dict[str, np.ndarray]
        Dictionary mapping subject -> (n_runs, n_colors, n_voxels)
    subjects_hc : List[str]
        HC subject IDs
    subjects_cvd : List[str]
        CVD subject IDs

    Returns
    -------
    hc_disparities : np.ndarray
        (n_hc,) disparities for HC subjects
    cvd_disparities : np.ndarray
        (n_cvd,) disparities for CVD subjects
    """
    print("\nComputing between-subject Procrustes disparities...")

    # Step 1: Compute HC reference (mean of HC averaged patterns)
    hc_patterns = []
    for subject in subjects_hc:
        if subject in amplitudes_dict:
            # Average across runs
            mean_pattern = np.mean(amplitudes_dict[subject], axis=0)  # (n_colors, n_voxels)
            hc_patterns.append(mean_pattern)

    if len(hc_patterns) == 0:
        raise ValueError("No HC subjects found in amplitudes_dict")

    hc_reference = np.mean(hc_patterns, axis=0)  # (n_colors, n_voxels)
    print(f"  HC reference computed from {len(hc_patterns)} subjects")

    # Step 2: Compute HC-HC disparities
    hc_disparities = []
    for subject in subjects_hc:
        if subject in amplitudes_dict:
            mean_pattern = np.mean(amplitudes_dict[subject], axis=0)
            disparity = compute_procrustes_disparity_between_subjects(mean_pattern, hc_reference)
            hc_disparities.append(disparity)
            print(f"  {subject} (HC): disparity = {disparity:.4f}")

    # Step 3: Compute CVD-HC disparities
    cvd_disparities = []
    for subject in subjects_cvd:
        if subject in amplitudes_dict:
            mean_pattern = np.mean(amplitudes_dict[subject], axis=0)
            disparity = compute_procrustes_disparity_between_subjects(mean_pattern, hc_reference)
            cvd_disparities.append(disparity)
            print(f"  {subject} (CVD): disparity = {disparity:.4f}")

    hc_disparities = np.array(hc_disparities)
    cvd_disparities = np.array(cvd_disparities)

    print(f"\n  HC disparities: mean={hc_disparities.mean():.4f}, std={hc_disparities.std():.4f}")
    print(f"  CVD disparities: mean={cvd_disparities.mean():.4f}, std={cvd_disparities.std():.4f}")

    return hc_disparities, cvd_disparities


def compute_rdm_similarities(amplitudes_dict: Dict[str, np.ndarray],
                             subjects_hc: List[str],
                             subjects_cvd: List[str]) -> Dict:
    """
    Compute pairwise RDM correlations within and between groups

    Parameters
    ----------
    amplitudes_dict : Dict[str, np.ndarray]
        Dictionary mapping subject -> (n_runs, n_colors, n_voxels)
    subjects_hc : List[str]
        HC subject IDs
    subjects_cvd : List[str]
        CVD subject IDs

    Returns
    -------
    rdm_corr : Dict
        - 'hc_hc': List of within-HC RDM correlations
        - 'cvd_cvd': List of within-CVD RDM correlations
        - 'hc_cvd': List of between-group RDM correlations
    """
    print("\nComputing RDM similarities...")

    # Compute RDMs for all subjects
    rdms = {}
    for subject in subjects_hc + subjects_cvd:
        if subject in amplitudes_dict:
            rdm = compute_rdm_from_amplitudes(amplitudes_dict[subject])
            # Vectorize upper triangle (excluding diagonal)
            rdm_vec = rdm[np.triu_indices_from(rdm, k=1)]
            rdms[subject] = rdm_vec

    # Compute pairwise correlations
    hc_hc_corr = []
    cvd_cvd_corr = []
    hc_cvd_corr = []

    # HC-HC pairs
    for i, subj1 in enumerate(subjects_hc):
        if subj1 not in rdms:
            continue
        for subj2 in subjects_hc[i+1:]:
            if subj2 not in rdms:
                continue
            corr, _ = spearmanr(rdms[subj1], rdms[subj2])
            hc_hc_corr.append(corr)

    # CVD-CVD pairs
    for i, subj1 in enumerate(subjects_cvd):
        if subj1 not in rdms:
            continue
        for subj2 in subjects_cvd[i+1:]:
            if subj2 not in rdms:
                continue
            corr, _ = spearmanr(rdms[subj1], rdms[subj2])
            cvd_cvd_corr.append(corr)

    # HC-CVD pairs
    for subj1 in subjects_hc:
        if subj1 not in rdms:
            continue
        for subj2 in subjects_cvd:
            if subj2 not in rdms:
                continue
            corr, _ = spearmanr(rdms[subj1], rdms[subj2])
            hc_cvd_corr.append(corr)

    rdm_corr = {
        'hc_hc': hc_hc_corr,
        'cvd_cvd': cvd_cvd_corr,
        'hc_cvd': hc_cvd_corr
    }

    print(f"  HC-HC correlations: n={len(hc_hc_corr)}, mean={np.mean(hc_hc_corr):.3f}")
    print(f"  CVD-CVD correlations: n={len(cvd_cvd_corr)}, mean={np.mean(cvd_cvd_corr):.3f}")
    print(f"  HC-CVD correlations: n={len(hc_cvd_corr)}, mean={np.mean(hc_cvd_corr):.3f}")

    return rdm_corr


def evaluate_procrustes_anova(amplitudes_dict: Dict[str, np.ndarray],
                              subjects_hc: List[str],
                              subjects_cvd: List[str],
                              k_values: List[int],
                              roi: str,
                              output_dir: Path) -> Dict:
    """
    Main evaluation function for between-subject Procrustes with ANOVA selection

    Parameters
    ----------
    amplitudes_dict : Dict[str, np.ndarray]
        Dictionary mapping subject -> (n_runs, n_colors, n_voxels)
    subjects_hc : List[str]
        HC subject IDs
    subjects_cvd : List[str]
        CVD subject IDs
    k_values : List[int]
        List of k values to test for voxel selection
    roi : str
        ROI name
    output_dir : Path
        Output directory

    Returns
    -------
    results : Dict
        Results dictionary with disparities, RDM correlations, statistics
    """
    from anova_voxel_selection import (
        compute_per_subject_anova,
        aggregate_rankings_mean_rank,
        select_top_k_voxels,
        compute_anova_selection_quality
    )

    print("="*70)
    print(f"Between-Subject Procrustes Evaluation - {roi}")
    print("="*70)

    # Step 1: Compute ANOVA rankings
    print("\n[1/4] Computing ANOVA rankings...")
    anova_results = compute_per_subject_anova(amplitudes_dict)
    mean_ranks, std_ranks = aggregate_rankings_mean_rank(anova_results)

    # Step 2: Evaluate for each k value
    print(f"\n[2/4] Evaluating for k values: {k_values}")
    results = {}

    for k in k_values:
        print(f"\n{'='*70}")
        print(f"k = {k} voxels")
        print(f"{'='*70}")

        # Select top-k voxels
        selected_indices = select_top_k_voxels(mean_ranks, k)

        # Compute selection quality
        quality_metrics = compute_anova_selection_quality(anova_results, selected_indices)

        # Extract selected voxels
        amplitudes_selected = {
            subj: amp[:, :, selected_indices]
            for subj, amp in amplitudes_dict.items()
        }

        # Compute disparities
        hc_disp, cvd_disp = compute_between_subject_disparities(
            amplitudes_selected, subjects_hc, subjects_cvd
        )

        # Statistical test
        t_stat, p_value = ttest_ind(hc_disp, cvd_disp)
        cohens_d = (np.mean(cvd_disp) - np.mean(hc_disp)) / \
                   np.sqrt((np.std(cvd_disp)**2 + np.std(hc_disp)**2) / 2)

        print(f"\n  Statistical comparison:")
        print(f"    t-test: t={t_stat:.3f}, p={p_value:.4f}")
        print(f"    Cohen's d: {cohens_d:.3f}")

        # RDM similarities
        rdm_corr = compute_rdm_similarities(amplitudes_selected, subjects_hc, subjects_cvd)

        # Store results
        results[k] = {
            'hc_disparities': hc_disp.tolist(),
            'cvd_disparities': cvd_disp.tolist(),
            'disparity_stats': {
                'hc_mean': float(np.mean(hc_disp)),
                'hc_std': float(np.std(hc_disp)),
                'cvd_mean': float(np.mean(cvd_disp)),
                'cvd_std': float(np.std(cvd_disp))
            },
            'ttest': {
                't': float(t_stat),
                'p': float(p_value),
                'cohens_d': float(cohens_d)
            },
            'rdm_correlations': {
                'hc_hc': rdm_corr['hc_hc'],
                'cvd_cvd': rdm_corr['cvd_cvd'],
                'hc_cvd': rdm_corr['hc_cvd'],
                'hc_hc_mean': float(np.mean(rdm_corr['hc_hc'])) if rdm_corr['hc_hc'] else None,
                'cvd_cvd_mean': float(np.mean(rdm_corr['cvd_cvd'])) if rdm_corr['cvd_cvd'] else None,
                'hc_cvd_mean': float(np.mean(rdm_corr['hc_cvd'])) if rdm_corr['hc_cvd'] else None
            },
            'selection_quality': {
                'mean_f_per_subject': {k: float(v) for k, v in quality_metrics['mean_f_per_subject'].items()},
                'mean_rank_coverage': float(quality_metrics['mean_rank_coverage']),
                'min_rank_coverage': float(quality_metrics['min_rank_coverage'])
            },
            'selected_voxel_indices': selected_indices.tolist()
        }

    # Step 3: Save results
    print(f"\n[3/4] Saving results to {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    results_file = output_dir / f"{roi}_procrustes_anova_results.json"
    with open(results_file, 'w') as f:
        json.dump({
            'roi': roi,
            'n_subjects_hc': len(subjects_hc),
            'n_subjects_cvd': len(subjects_cvd),
            'k_values': k_values,
            'results': results
        }, f, indent=2)

    print(f"  Saved to {results_file}")

    return results


if __name__ == '__main__':
    # Test script
    print("This script should be run via run_pipeline_local.py")
    print("For testing, use synthetic data:")

    # Create synthetic data
    n_subjects_hc = 3
    n_subjects_cvd = 2
    n_runs = 6
    n_colors = 8
    n_voxels = 50

    amplitudes_dict = {}
    subjects_hc = [f'sub-{i+1:02d}' for i in range(n_subjects_hc)]
    subjects_cvd = [f'sub-{i+8:02d}' for i in range(n_subjects_cvd)]

    # HC subjects: similar patterns
    for subject in subjects_hc:
        amplitudes_dict[subject] = np.random.randn(n_runs, n_colors, n_voxels) * 0.5 + 1.0

    # CVD subjects: different patterns
    for subject in subjects_cvd:
        amplitudes_dict[subject] = np.random.randn(n_runs, n_colors, n_voxels) * 0.8 + 0.5

    # Run evaluation
    output_dir = Path("test_output")
    results = evaluate_procrustes_anova(
        amplitudes_dict=amplitudes_dict,
        subjects_hc=subjects_hc,
        subjects_cvd=subjects_cvd,
        k_values=[20, 30],
        roi='V1_test',
        output_dir=output_dir
    )

    print("\nTest completed!")
