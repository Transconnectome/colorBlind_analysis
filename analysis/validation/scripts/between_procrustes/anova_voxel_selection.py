#!/usr/bin/env python3
"""
anova_voxel_selection.py
------------------------
ANOVA-based voxel selection for between-subject analysis

Purpose:
- Compute per-subject ANOVA F-statistics for color discrimination
- Aggregate rankings across subjects using mean rank (Borda count)
- Select top-k consistently discriminative voxels

Key Functions:
- compute_per_subject_anova(): F-test per subject
- aggregate_rankings_mean_rank(): Aggregate rankings
- select_top_k_voxels(): Select top-k by mean rank
"""

import numpy as np
from typing import Dict, Tuple
from sklearn.feature_selection import f_classif


def compute_per_subject_anova(amplitudes_dict: Dict[str, np.ndarray]) -> Dict:
    """
    Compute ANOVA F-test per subject

    Parameters
    ----------
    amplitudes_dict : Dict[str, np.ndarray]
        Dictionary mapping subject -> (n_runs, n_colors, n_voxels) amplitudes

    Returns
    -------
    anova_results : Dict
        Dictionary mapping subject -> {'f_values', 'p_values', 'ranks'}
        - f_values: (n_voxels,) F-statistic per voxel
        - p_values: (n_voxels,) p-value per voxel
        - ranks: (n_voxels,) rank per voxel (0 = best discriminative)
    """
    print("Computing per-subject ANOVA F-statistics...")

    anova_results = {}

    for subject, amplitudes in amplitudes_dict.items():
        n_runs, n_colors, n_voxels = amplitudes.shape

        # Reshape: (n_runs*n_colors, n_voxels)
        X = amplitudes.reshape(n_runs * n_colors, n_voxels)

        # Create labels: [0,1,2,...,7, 0,1,2,...,7, ...]
        y = np.tile(np.arange(n_colors), n_runs)

        # Compute ANOVA F-statistic
        f_values, p_values = f_classif(X, y)

        # Compute ranks (0 = highest F-value)
        # argsort twice gives ranks
        ranks = np.argsort(np.argsort(f_values)[::-1])

        anova_results[subject] = {
            'f_values': f_values,
            'p_values': p_values,
            'ranks': ranks
        }

        print(f"  {subject}: F-values range [{f_values.min():.2f}, {f_values.max():.2f}], mean rank {ranks.mean():.1f}")

    return anova_results


def aggregate_rankings_mean_rank(anova_results: Dict) -> Tuple[np.ndarray, np.ndarray]:
    """
    Aggregate voxel rankings across subjects using Borda count (mean rank)

    Parameters
    ----------
    anova_results : Dict
        Dictionary mapping subject -> {'f_values', 'p_values', 'ranks'}

    Returns
    -------
    mean_ranks : np.ndarray
        (n_voxels,) mean rank per voxel across subjects
        Lower mean rank = more consistently discriminative
    std_ranks : np.ndarray
        (n_voxels,) standard deviation of ranks
        Lower std = more consistent across subjects
    """
    print("\nAggregating rankings across subjects...")

    # Stack rank arrays: (n_subjects, n_voxels)
    ranks_array = np.stack([res['ranks'] for res in anova_results.values()], axis=0)

    # Compute mean and std
    mean_ranks = np.mean(ranks_array, axis=0)
    std_ranks = np.std(ranks_array, axis=0)

    print(f"  Mean rank range: [{mean_ranks.min():.1f}, {mean_ranks.max():.1f}]")
    print(f"  Rank std range: [{std_ranks.min():.1f}, {std_ranks.max():.1f}]")

    # Report consistency
    n_voxels = len(mean_ranks)
    n_consistent = np.sum(std_ranks < n_voxels * 0.2)  # Low variance voxels
    print(f"  Consistent voxels (std < 20% range): {n_consistent}/{n_voxels} ({100*n_consistent/n_voxels:.1f}%)")

    return mean_ranks, std_ranks


def select_top_k_voxels(mean_ranks: np.ndarray, k: int) -> np.ndarray:
    """
    Select top-k voxels by mean rank

    Parameters
    ----------
    mean_ranks : np.ndarray
        (n_voxels,) mean rank per voxel
    k : int
        Number of voxels to select

    Returns
    -------
    selected_indices : np.ndarray
        (k,) indices of selected voxels
    """
    # Sort by mean rank (ascending = best first)
    selected_indices = np.argsort(mean_ranks)[:k]

    print(f"\nSelected top {k} voxels")
    print(f"  Mean rank of selected voxels: [{mean_ranks[selected_indices].min():.1f}, {mean_ranks[selected_indices].max():.1f}]")

    return selected_indices


def compute_anova_selection_quality(anova_results: Dict, selected_indices: np.ndarray) -> Dict:
    """
    Compute quality metrics for selected voxels

    Parameters
    ----------
    anova_results : Dict
        Dictionary mapping subject -> {'f_values', 'p_values', 'ranks'}
    selected_indices : np.ndarray
        Indices of selected voxels

    Returns
    -------
    quality_metrics : Dict
        - mean_f_per_subject: Mean F-value of selected voxels per subject
        - selection_confidence: 1 / (1 + rank_std) - higher = more consistent
        - per_subject_coverage: % of subjects where selected voxels rank in top 50%
    """
    n_subjects = len(anova_results)
    n_selected = len(selected_indices)

    mean_f_per_subject = {}
    rank_coverage = []

    for subject, results in anova_results.items():
        # Mean F-value of selected voxels
        f_values = results['f_values'][selected_indices]
        mean_f_per_subject[subject] = np.mean(f_values)

        # How many selected voxels rank in top 50% for this subject?
        ranks = results['ranks'][selected_indices]
        n_voxels_total = len(results['ranks'])
        n_top_half = np.sum(ranks < n_voxels_total / 2)
        rank_coverage.append(n_top_half / n_selected)

    quality_metrics = {
        'mean_f_per_subject': mean_f_per_subject,
        'mean_rank_coverage': np.mean(rank_coverage),
        'min_rank_coverage': np.min(rank_coverage),
        'n_selected': n_selected
    }

    print("\nSelection quality metrics:")
    print(f"  Mean F-values per subject:")
    for subject, mean_f in mean_f_per_subject.items():
        print(f"    {subject}: {mean_f:.2f}")
    print(f"  Rank coverage (top 50%): mean={100*quality_metrics['mean_rank_coverage']:.1f}%, min={100*quality_metrics['min_rank_coverage']:.1f}%")

    return quality_metrics


if __name__ == '__main__':
    # Test script with synthetic data
    print("="*70)
    print("Testing ANOVA voxel selection")
    print("="*70)

    # Create synthetic data
    n_subjects = 3
    n_runs = 6
    n_colors = 8
    n_voxels = 100

    print(f"\nSynthetic data: {n_subjects} subjects, {n_runs} runs, {n_colors} colors, {n_voxels} voxels")

    # Create data with known discriminative voxels (first 10 voxels)
    amplitudes_dict = {}
    for i in range(n_subjects):
        amplitudes = np.random.randn(n_runs, n_colors, n_voxels) * 0.5

        # Add color-specific signal to first 10 voxels
        for color_idx in range(n_colors):
            amplitudes[:, color_idx, :10] += color_idx * 0.5

        amplitudes_dict[f'sub-{i+1:02d}'] = amplitudes

    # Test 1: Compute ANOVA
    anova_results = compute_per_subject_anova(amplitudes_dict)

    # Test 2: Aggregate rankings
    mean_ranks, std_ranks = aggregate_rankings_mean_rank(anova_results)

    # Test 3: Select top-k voxels
    k = 20
    selected_indices = select_top_k_voxels(mean_ranks, k)

    print(f"\nSelected voxel indices: {selected_indices[:10]}...")
    print(f"Expected: First 10 voxels should be selected (have lowest mean ranks)")

    # Test 4: Quality metrics
    quality_metrics = compute_anova_selection_quality(anova_results, selected_indices)

    # Verify that first 10 voxels have low mean ranks
    first_10_mean_ranks = mean_ranks[:10]
    print(f"\nMean ranks of first 10 voxels (should be low): {first_10_mean_ranks}")
    print(f"Mean ranks of last 10 voxels (should be high): {mean_ranks[-10:]}")
