#!/usr/bin/env python3
"""
Procrustes Brain Metrics Computation

Purpose: Compute voxel-wise metrics showing spatial distribution of Procrustes improvement
Metrics:
1. Correspondence: Per-voxel correlation between HC reference and CVD (8-color profile)
2. Disparity: Per-voxel L2 distance between HC and CVD
3. Profile reliability: Run-to-run stability of voxel's 8-color profile (NOT RDM noise ceiling)

Key Correction: "Voxel-level noise ceiling" renamed to "profile reliability"
- RDM noise ceiling is ROI-level representational geometry reliability
- Voxel-level profile reliability measures run-to-run stability of individual voxels
- These are conceptually different metrics

Usage:
    corr_raw, corr_proc, improvement = compute_voxelwise_correspondence(
        hc_patterns, cvd_raw, cvd_proc
    )
"""

import numpy as np
from scipy.stats import pearsonr, spearmanr
from sklearn.metrics.pairwise import euclidean_distances


def compute_voxelwise_correspondence(hc_reference, cvd_raw, cvd_proc):
    """
    Compute per-voxel correspondence between HC reference and CVD.

    Correspondence = correlation of 8-color profiles per voxel.

    Parameters
    ----------
    hc_reference : np.ndarray
        HC reference patterns (6 runs, 8 colors, n_voxels)
        Using sub-01 as single stable reference
    cvd_raw : np.ndarray
        CVD raw patterns (6 runs, 8 colors, n_voxels)
    cvd_proc : np.ndarray
        CVD Procrustes-aligned patterns (6 runs, 8 colors, n_voxels)

    All inputs must be coordinate-matched (same n_voxels, same spatial locations)

    Returns
    -------
    corr_raw : np.ndarray
        Per-voxel correlation before Procrustes (n_voxels,)
    corr_proc : np.ndarray
        Per-voxel correlation after Procrustes (n_voxels,)
    improvement : np.ndarray
        Correlation improvement (proc - raw) (n_voxels,)
    """
    n_runs, n_colors, n_voxels = hc_reference.shape

    print(f"\nComputing voxel-wise correspondence...")
    print(f"  Shape: ({n_runs} runs, {n_colors} colors, {n_voxels} voxels)")

    # Average across runs to get stable profiles
    hc_profile = np.mean(hc_reference, axis=0)  # (8, n_voxels)
    cvd_raw_profile = np.mean(cvd_raw, axis=0)
    cvd_proc_profile = np.mean(cvd_proc, axis=0)

    # Compute per-voxel correlation
    corr_raw = np.zeros(n_voxels)
    corr_proc = np.zeros(n_voxels)

    for v in range(n_voxels):
        # 8-color profile correlation
        if np.std(hc_profile[:, v]) > 1e-8 and np.std(cvd_raw_profile[:, v]) > 1e-8:
            corr_raw[v], _ = pearsonr(hc_profile[:, v], cvd_raw_profile[:, v])
        else:
            corr_raw[v] = 0.0

        if np.std(hc_profile[:, v]) > 1e-8 and np.std(cvd_proc_profile[:, v]) > 1e-8:
            corr_proc[v], _ = pearsonr(hc_profile[:, v], cvd_proc_profile[:, v])
        else:
            corr_proc[v] = 0.0

    improvement = corr_proc - corr_raw

    # Summary statistics
    print(f"  Raw correlation: {np.mean(corr_raw):.3f} ± {np.std(corr_raw):.3f}")
    print(f"  Procrustes correlation: {np.mean(corr_proc):.3f} ± {np.std(corr_proc):.3f}")
    print(f"  Improvement: {np.mean(improvement):.3f} ± {np.std(improvement):.3f}")
    print(f"  % voxels improved: {100 * np.mean(improvement > 0):.1f}%")

    return corr_raw, corr_proc, improvement


def compute_voxelwise_disparity(hc_reference, cvd_raw, cvd_proc):
    """
    Compute per-voxel disparity (L2 distance) between HC and CVD.

    Parameters
    ----------
    hc_reference : np.ndarray
        HC reference patterns (6 runs, 8 colors, n_voxels)
    cvd_raw : np.ndarray
        CVD raw patterns (6 runs, 8 colors, n_voxels)
    cvd_proc : np.ndarray
        CVD Procrustes-aligned patterns (6 runs, 8 colors, n_voxels)

    Returns
    -------
    disp_raw : np.ndarray
        Per-voxel disparity before Procrustes (n_voxels,)
    disp_proc : np.ndarray
        Per-voxel disparity after Procrustes (n_voxels,)
    reduction_pct : np.ndarray
        Percent reduction in disparity (n_voxels,)
    """
    n_runs, n_colors, n_voxels = hc_reference.shape

    print(f"\nComputing voxel-wise disparity...")

    # Average across runs
    hc_profile = np.mean(hc_reference, axis=0)  # (8, n_voxels)
    cvd_raw_profile = np.mean(cvd_raw, axis=0)
    cvd_proc_profile = np.mean(cvd_proc, axis=0)

    # Compute L2 distance per voxel (across 8 colors)
    disp_raw = np.linalg.norm(hc_profile - cvd_raw_profile, axis=0)  # (n_voxels,)
    disp_proc = np.linalg.norm(hc_profile - cvd_proc_profile, axis=0)

    # Percent reduction
    reduction_pct = 100 * (disp_raw - disp_proc) / (disp_raw + 1e-8)

    # Summary statistics
    print(f"  Raw disparity: {np.mean(disp_raw):.3f} ± {np.std(disp_raw):.3f}")
    print(f"  Procrustes disparity: {np.mean(disp_proc):.3f} ± {np.std(disp_proc):.3f}")
    print(f"  Reduction: {np.mean(reduction_pct):.1f}% ± {np.std(reduction_pct):.1f}%")
    print(f"  % voxels reduced: {100 * np.mean(reduction_pct > 0):.1f}%")

    return disp_raw, disp_proc, reduction_pct


def compute_voxelwise_profile_reliability(patterns, n_splits=50):
    """
    Compute voxel-level run-to-run profile reliability.

    IMPORTANT NAMING CLARIFICATION:
    - This is NOT "voxel-level noise ceiling"
    - RDM noise ceiling is ROI-level representational geometry reliability
    - This metric measures: run-to-run stability of individual voxel's 8-color profile

    What we compute:
    - Split runs randomly (odd/even: e.g., [0,2,4] vs [1,3,5])
    - Average 8-color profile within each split
    - Correlate profiles between splits, per voxel
    - Average correlation over n_splits

    Interpretation:
    - High reliability: Voxel has stable color selectivity across runs
    - Low reliability: Voxel response dominated by geometric run variability
    - Procrustes should improve this by reducing geometric variance

    Parameters
    ----------
    patterns : np.ndarray
        Voxel patterns (6 runs, 8 colors, n_voxels)
    n_splits : int
        Number of random splits for reliability estimation

    Returns
    -------
    reliability : np.ndarray
        Per-voxel profile reliability (n_voxels,)
    """
    n_runs, n_colors, n_voxels = patterns.shape

    print(f"\nComputing voxel-level profile reliability (run-to-run stability)...")
    print(f"  NOTE: This is NOT RDM noise ceiling (which is ROI-level)")
    print(f"  Measuring: run-to-run stability of 8-color profiles")
    print(f"  N splits: {n_splits}")

    if n_runs < 4:
        print("  WARNING: Too few runs for reliable split-half estimation")

    reliability = np.zeros(n_voxels)

    for split_idx in range(n_splits):
        # Random split
        run_order = np.random.permutation(n_runs)
        n_half = n_runs // 2

        split1_runs = run_order[:n_half]
        split2_runs = run_order[n_half:]

        # Average within splits
        split1_profile = np.mean(patterns[split1_runs], axis=0)  # (8, n_voxels)
        split2_profile = np.mean(patterns[split2_runs], axis=0)

        # Correlate per voxel
        for v in range(n_voxels):
            if np.std(split1_profile[:, v]) > 1e-8 and np.std(split2_profile[:, v]) > 1e-8:
                corr, _ = pearsonr(split1_profile[:, v], split2_profile[:, v])
                reliability[v] += corr
            # else: contribute 0

    # Average over splits
    reliability /= n_splits

    # Summary statistics
    print(f"  Mean reliability: {np.mean(reliability):.3f} ± {np.std(reliability):.3f}")
    print(f"  Range: [{np.min(reliability):.3f}, {np.max(reliability):.3f}]")
    print(f"  % voxels positive: {100 * np.mean(reliability > 0):.1f}%")

    return reliability


def compute_all_metrics(hc_reference, cvd_raw, cvd_proc, n_splits=50):
    """
    Compute all voxel-wise metrics.

    Parameters
    ----------
    hc_reference : np.ndarray
        HC reference patterns (6 runs, 8 colors, n_voxels)
    cvd_raw : np.ndarray
        CVD raw patterns (6 runs, 8 colors, n_voxels)
    cvd_proc : np.ndarray
        CVD Procrustes-aligned patterns (6 runs, 8 colors, n_voxels)
    n_splits : int
        Number of splits for reliability estimation

    Returns
    -------
    metrics : dict
        All computed metrics with summary statistics
    """
    print("="*80)
    print("Computing all voxel-wise metrics")
    print("="*80)

    # 1. Correspondence
    corr_raw, corr_proc, corr_improvement = compute_voxelwise_correspondence(
        hc_reference, cvd_raw, cvd_proc
    )

    # 2. Disparity
    disp_raw, disp_proc, disp_reduction = compute_voxelwise_disparity(
        hc_reference, cvd_raw, cvd_proc
    )

    # 3. Profile reliability (NOT noise ceiling)
    reliability_raw = compute_voxelwise_profile_reliability(cvd_raw, n_splits)
    reliability_proc = compute_voxelwise_profile_reliability(cvd_proc, n_splits)
    reliability_improvement = reliability_proc - reliability_raw

    # Package results
    metrics = {
        'correspondence': {
            'raw': corr_raw,
            'procrustes': corr_proc,
            'improvement': corr_improvement,
            'summary': {
                'raw_mean': float(np.mean(corr_raw)),
                'raw_std': float(np.std(corr_raw)),
                'proc_mean': float(np.mean(corr_proc)),
                'proc_std': float(np.std(corr_proc)),
                'improvement_mean': float(np.mean(corr_improvement)),
                'improvement_std': float(np.std(corr_improvement)),
                'pct_improved': float(100 * np.mean(corr_improvement > 0))
            }
        },
        'disparity': {
            'raw': disp_raw,
            'procrustes': disp_proc,
            'reduction_pct': disp_reduction,
            'summary': {
                'raw_mean': float(np.mean(disp_raw)),
                'raw_std': float(np.std(disp_raw)),
                'proc_mean': float(np.mean(disp_proc)),
                'proc_std': float(np.std(disp_proc)),
                'reduction_pct_mean': float(np.mean(disp_reduction)),
                'reduction_pct_std': float(np.std(disp_reduction)),
                'pct_reduced': float(100 * np.mean(disp_reduction > 0))
            }
        },
        'profile_reliability': {
            'note': 'Voxel-level run-to-run stability, NOT RDM noise ceiling',
            'raw': reliability_raw,
            'procrustes': reliability_proc,
            'improvement': reliability_improvement,
            'summary': {
                'raw_mean': float(np.mean(reliability_raw)),
                'raw_std': float(np.std(reliability_raw)),
                'proc_mean': float(np.mean(reliability_proc)),
                'proc_std': float(np.std(reliability_proc)),
                'improvement_mean': float(np.mean(reliability_improvement)),
                'improvement_std': float(np.std(reliability_improvement)),
                'pct_improved': float(100 * np.mean(reliability_improvement > 0))
            }
        }
    }

    print("\n" + "="*80)
    print("Metrics computation complete")
    print("="*80)

    return metrics


if __name__ == '__main__':
    """Test metrics computation with synthetic data."""

    print("Testing procrustes brain metrics computation...")
    print("="*80)

    # Create synthetic data
    n_runs = 6
    n_colors = 8
    n_voxels = 100

    print(f"Creating synthetic data: ({n_runs}, {n_colors}, {n_voxels})")

    # HC reference (ground truth)
    np.random.seed(42)
    hc_reference = np.random.randn(n_runs, n_colors, n_voxels)

    # CVD raw (with geometric rotation + noise)
    rotation_angle = 0.3
    rotation_matrix = np.array([
        [np.cos(rotation_angle), -np.sin(rotation_angle)],
        [np.sin(rotation_angle), np.cos(rotation_angle)]
    ])

    cvd_raw = np.copy(hc_reference)
    for r in range(n_runs):
        for v in range(n_voxels):
            # Apply rotation to first 2 colors
            rotated = rotation_matrix @ cvd_raw[r, :2, v]
            cvd_raw[r, :2, v] = rotated

    # Add noise
    cvd_raw += np.random.randn(n_runs, n_colors, n_voxels) * 0.5

    # CVD procrustes (closer to HC)
    cvd_proc = 0.7 * hc_reference + 0.3 * cvd_raw + np.random.randn(n_runs, n_colors, n_voxels) * 0.2

    # Compute metrics
    metrics = compute_all_metrics(hc_reference, cvd_raw, cvd_proc, n_splits=20)

    # Print summary
    print("\n" + "="*80)
    print("Summary Statistics:")
    print("="*80)

    print("\n1. Correspondence:")
    print(f"  Raw: {metrics['correspondence']['summary']['raw_mean']:.3f}")
    print(f"  Procrustes: {metrics['correspondence']['summary']['proc_mean']:.3f}")
    print(f"  Improvement: {metrics['correspondence']['summary']['improvement_mean']:.3f}")

    print("\n2. Disparity:")
    print(f"  Raw: {metrics['disparity']['summary']['raw_mean']:.3f}")
    print(f"  Procrustes: {metrics['disparity']['summary']['proc_mean']:.3f}")
    print(f"  Reduction: {metrics['disparity']['summary']['reduction_pct_mean']:.1f}%")

    print("\n3. Profile Reliability:")
    print(f"  Raw: {metrics['profile_reliability']['summary']['raw_mean']:.3f}")
    print(f"  Procrustes: {metrics['profile_reliability']['summary']['proc_mean']:.3f}")
    print(f"  Improvement: {metrics['profile_reliability']['summary']['improvement_mean']:.3f}")

    print("\n✓ Metrics computation test complete")
