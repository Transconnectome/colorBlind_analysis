#!/usr/bin/env python3
"""
Test different centering methods to diagnose shrinkage=0 issue.

Question: Why does run-wise centering lead to shrinkage ≈ 0?
Hypothesis: Run-wise centering removes too much structure, making covariance "too clean".

Test 3 methods:
1. No centering (baseline)
2. Global centering only (mean across all timepoints)
3. Run-wise centering (current method)

Expected:
- No centering: High shrinkage (noisy covariance)
- Global centering: Medium shrinkage (removes global drift only)
- Run-wise centering: Low shrinkage (removes too much, including signal)

Author: Claude Code
Date: 2026-02-08
"""

import numpy as np
from pathlib import Path
import sys

# Add utils to path
script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(script_dir / 'utils'))

from sklearn.covariance import LedoitWolf
from whitening import compute_temporal_autocorrelation

# Test configuration
SUBJECT = "01"
ROI = "V1"
BASE_DIR = Path(__file__).parent.parent.parent.parent / "phase1_preprocess_decoding" / "results" / "baseline_residuals"

def test_centering_method(residuals, n_runs, method='none', verbose=True):
    """
    Test shrinkage with different centering methods.

    Args:
        residuals: (n_samples, n_voxels) - Raw residuals
        n_runs: Number of runs
        method: 'none', 'global', 'run-wise'

    Returns:
        shrinkage, acf_metrics, residuals_processed
    """
    n_samples, n_voxels = residuals.shape
    samples_per_run = n_samples // n_runs

    if method == 'none':
        # No centering (baseline)
        residuals_processed = residuals.copy()

    elif method == 'global':
        # Global centering (remove overall mean per voxel)
        residuals_processed = residuals - residuals.mean(axis=0, keepdims=True)

    elif method == 'run-wise':
        # Run-wise centering (current method)
        residuals_processed = residuals.copy()
        for run_idx in range(n_runs):
            start_idx = run_idx * samples_per_run
            end_idx = start_idx + samples_per_run if run_idx < n_runs - 1 else n_samples
            run_residuals = residuals[start_idx:end_idx]
            residuals_processed[start_idx:end_idx] = run_residuals - run_residuals.mean(axis=0, keepdims=True)
    else:
        raise ValueError(f"Unknown method: {method}")

    # Compute ACF
    acf_metrics = compute_temporal_autocorrelation(residuals_processed)

    # Estimate shrinkage
    lw = LedoitWolf(assume_centered=False)
    lw.fit(residuals_processed)
    shrinkage = lw.shrinkage_

    # Compute voxel correlation statistics
    corr_matrix = np.corrcoef(residuals_processed.T)
    n = corr_matrix.shape[0]
    off_diag_mask = ~np.eye(n, dtype=bool)
    mean_corr = corr_matrix[off_diag_mask].mean()
    std_corr = corr_matrix[off_diag_mask].std()

    if verbose:
        print(f"\n{'='*60}")
        print(f"Method: {method.upper()}")
        print(f"{'='*60}")
        print(f"Preprocessing:")
        print(f"  Global mean: {residuals_processed.mean():.3f}")
        print(f"  Per-voxel mean: {residuals_processed.mean(axis=0).mean():.3f}")
        print(f"\nVoxel correlation:")
        print(f"  Mean off-diagonal: {mean_corr:.4f} ± {std_corr:.4f}")
        print(f"\nTemporal autocorrelation (ACF-1):")
        print(f"  Mean: {acf_metrics['acf1_mean']:.3f} ± {acf_metrics['acf1_std']:.3f}")
        print(f"  Effective n: {acf_metrics['n_effective']:.1f} / {acf_metrics['n_raw']}")
        print(f"\nLedoit-Wolf shrinkage:")
        print(f"  Raw: {shrinkage:.4f}")
        print(f"  Interpretation: ", end="")
        if shrinkage < 0.1:
            print("Very low (covariance is well-conditioned)")
        elif shrinkage < 0.3:
            print("Low (modest regularization)")
        elif shrinkage < 0.5:
            print("Medium (moderate regularization)")
        else:
            print("High (strong regularization needed)")

    return {
        'shrinkage': shrinkage,
        'acf_metrics': acf_metrics,
        'mean_corr': mean_corr,
        'std_corr': std_corr,
        'global_mean': residuals_processed.mean(),
        'residuals': residuals_processed
    }

def main():
    print("="*80)
    print("CENTERING METHOD COMPARISON")
    print("="*80)
    print(f"Testing on: sub-{SUBJECT}/{ROI}")
    print("\nHypothesis: Run-wise centering removes too much structure")
    print("")

    # Load data
    result_dir = BASE_DIR / f"sub-{SUBJECT}" / ROI
    amplitudes_raw = np.load(result_dir / "amplitudes_raw.npy")
    residuals_path = result_dir / "residuals_1st_level.npy"

    if not residuals_path.exists():
        print("❌ Residuals not found. Cannot test.")
        return

    residuals = np.load(residuals_path, allow_pickle=True)
    if isinstance(residuals, np.ndarray) and residuals.dtype == object:
        residuals = residuals.item()
        residuals = np.vstack([residuals[run] for run in sorted(residuals.keys())])

    # Filter residuals to selected voxels
    voxel_mask_path = result_dir / "selected_voxels_mask.npy"
    if voxel_mask_path.exists():
        voxel_mask = np.load(voxel_mask_path)
        if residuals.shape[1] != amplitudes_raw.shape[2]:
            residuals = residuals[:, voxel_mask]

    n_runs, n_colors, n_voxels = amplitudes_raw.shape
    print(f"Shape: {n_runs} runs × {n_colors} colors × {n_voxels} voxels")
    print(f"Residuals: {residuals.shape}")
    print("")

    # Test 3 methods
    results = {}
    for method in ['none', 'global', 'run-wise']:
        results[method] = test_centering_method(residuals, n_runs, method, verbose=True)

    # Summary comparison
    print("\n" + "="*80)
    print("SUMMARY COMPARISON")
    print("="*80)

    print(f"\n{'Method':<15} {'Shrinkage':>10} {'Mean Corr':>12} {'ACF-1':>10} {'Eff n/Raw n':>15}")
    print("-"*80)

    for method in ['none', 'global', 'run-wise']:
        r = results[method]
        print(f"{method:<15} {r['shrinkage']:>10.4f} {r['mean_corr']:>12.4f} {r['acf_metrics']['acf1_mean']:>10.3f} "
              f"{r['acf_metrics']['n_effective']:>7.0f}/{r['acf_metrics']['n_raw']:<4.0f}")

    # Analysis
    print("\n" + "="*80)
    print("ANALYSIS")
    print("="*80)

    shrink_none = results['none']['shrinkage']
    shrink_global = results['global']['shrinkage']
    shrink_runwise = results['run-wise']['shrinkage']

    corr_none = results['none']['mean_corr']
    corr_global = results['global']['mean_corr']
    corr_runwise = results['run-wise']['mean_corr']

    print(f"\n1. Shrinkage progression:")
    print(f"   No centering:   {shrink_none:.4f}")
    print(f"   Global:         {shrink_global:.4f} ({(shrink_global-shrink_none)*100:+.1f}%)")
    print(f"   Run-wise:       {shrink_runwise:.4f} ({(shrink_runwise-shrink_none)*100:+.1f}%)")

    print(f"\n2. Voxel correlation:")
    print(f"   No centering:   {corr_none:.4f}")
    print(f"   Global:         {corr_global:.4f} ({(corr_global-corr_none)*100:+.1f}%)")
    print(f"   Run-wise:       {corr_runwise:.4f} ({(corr_runwise-corr_none)*100:+.1f}%)")

    print(f"\n3. Interpretation:")
    if shrink_runwise < shrink_global < shrink_none:
        print("   ✓ Run-wise centering reduces shrinkage (removes structure)")
        print("   → Covariance becomes 'cleaner' but may lose signal information")

    if abs(corr_runwise) < abs(corr_global) < abs(corr_none):
        print("   ✓ Run-wise centering reduces voxel correlation")
        print("   → May be removing shared signal across runs")

    print(f"\n4. Recommendation:")
    if shrink_global > 0.15:
        print("   → Use GLOBAL centering (preserves more structure)")
        print("   → Expected shrinkage with n_effective subsampling: ~0.20-0.40")
    else:
        print("   → Even global centering gives low shrinkage")
        print("   → May need stronger regularization (force minimum 0.3-0.5)")
        print("   → Or whitening may not be beneficial for this data")

    print("\n" + "="*80)

if __name__ == '__main__':
    main()
