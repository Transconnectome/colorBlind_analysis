#!/usr/bin/env python3
"""
Test Global Signal Regression (GSR) to reduce voxel correlation.

Problem: Voxel correlation = 0.98 (too high!)
Cause: Shared physiological noise across all voxels

Solution: Remove mean signal across voxels (GSR)
Expected: Correlation drops to 0.3-0.5, shrinkage increases to 0.2-0.4

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
from whitening import (
    compute_temporal_autocorrelation,
    whiten_amplitudes,
    compute_pattern_snr
)

# Test configuration
SUBJECT = "01"
ROI = "V1"
BASE_DIR = Path(__file__).parent.parent.parent.parent / "phase1_preprocess_decoding" / "results" / "baseline_residuals"

def apply_global_signal_regression(residuals, verbose=True):
    """
    Remove global signal (mean across voxels at each timepoint).

    This removes shared physiological artifacts (breathing, heartbeat, drift).

    Args:
        residuals: (n_samples, n_voxels)

    Returns:
        residuals_gsr: (n_samples, n_voxels) - After GSR
    """
    # Compute global signal (mean across voxels)
    global_signal = residuals.mean(axis=1, keepdims=True)  # (n_samples, 1)

    # Regress out global signal from each voxel
    residuals_gsr = np.zeros_like(residuals)

    for v in range(residuals.shape[1]):
        voxel_ts = residuals[:, v]

        # Linear regression: voxel_ts = β * global_signal + ε
        beta = np.dot(voxel_ts, global_signal.flatten()) / np.dot(global_signal.flatten(), global_signal.flatten())

        # Remove global signal component
        residuals_gsr[:, v] = voxel_ts - beta * global_signal.flatten()

    if verbose:
        print("Global Signal Regression applied:")
        print(f"  Global signal variance: {global_signal.var():.3f}")
        print(f"  Residuals variance before GSR: {residuals.var():.3f}")
        print(f"  Residuals variance after GSR: {residuals_gsr.var():.3f}")
        print(f"  Variance reduction: {(1 - residuals_gsr.var()/residuals.var())*100:.1f}%")

    return residuals_gsr

def test_gsr_effect(residuals, n_runs, verbose=True):
    """Test effect of GSR on voxel correlation and shrinkage."""

    n_samples, n_voxels = residuals.shape

    # Test 1: Without GSR
    print("\n" + "="*80)
    print("WITHOUT GSR (Current)")
    print("="*80)

    corr_before = np.corrcoef(residuals.T)
    off_diag_mask = ~np.eye(n_voxels, dtype=bool)
    mean_corr_before = corr_before[off_diag_mask].mean()
    std_corr_before = corr_before[off_diag_mask].std()

    lw_before = LedoitWolf(assume_centered=False)
    lw_before.fit(residuals)
    shrinkage_before = lw_before.shrinkage_

    print(f"Voxel correlation: {mean_corr_before:.4f} ± {std_corr_before:.4f}")
    print(f"Shrinkage: {shrinkage_before:.4f}")

    # Test 2: With GSR
    print("\n" + "="*80)
    print("WITH GSR (Proposed)")
    print("="*80)

    residuals_gsr = apply_global_signal_regression(residuals, verbose=True)

    corr_after = np.corrcoef(residuals_gsr.T)
    mean_corr_after = corr_after[off_diag_mask].mean()
    std_corr_after = corr_after[off_diag_mask].std()

    lw_after = LedoitWolf(assume_centered=False)
    lw_after.fit(residuals_gsr)
    shrinkage_after = lw_after.shrinkage_

    print(f"\nVoxel correlation: {mean_corr_after:.4f} ± {std_corr_after:.4f}")
    print(f"Shrinkage: {shrinkage_after:.4f}")

    # Compute eigenvalue spectrum
    eigenvals_before = np.linalg.eigvalsh(np.cov(residuals.T))[::-1]
    eigenvals_after = np.linalg.eigvalsh(np.cov(residuals_gsr.T))[::-1]

    print(f"\nEigenvalue spectrum (top 5):")
    print(f"  Before GSR: {eigenvals_before[:5]}")
    print(f"  After GSR:  {eigenvals_after[:5]}")
    print(f"  Dominant eigenvalue ratio:")
    print(f"    Before: λ₁/λ₂ = {eigenvals_before[0]/eigenvals_before[1]:.1f}")
    print(f"    After:  λ₁/λ₂ = {eigenvals_after[0]/eigenvals_after[1]:.1f}")

    # Test with ACF-corrected subsampling
    print("\n" + "="*80)
    print("GSR + ACF-1 Subsampling")
    print("="*80)

    acf_metrics = compute_temporal_autocorrelation(residuals_gsr)
    n_effective = int(acf_metrics['n_effective'])

    print(f"ACF-1: {acf_metrics['acf1_mean']:.3f}")
    print(f"Effective n: {n_effective} / {n_samples}")

    # Bootstrap estimate with n_effective
    print(f"\nBootstrap with n_effective={n_effective} (100 iterations)...")
    shrinkage_bootstrap = []

    for _ in range(100):
        idx = np.random.choice(n_samples, size=n_effective, replace=False)
        residuals_sub = residuals_gsr[idx]

        lw_sub = LedoitWolf(assume_centered=False)
        lw_sub.fit(residuals_sub)
        shrinkage_bootstrap.append(lw_sub.shrinkage_)

    shrinkage_bootstrap_mean = np.mean(shrinkage_bootstrap)
    shrinkage_bootstrap_std = np.std(shrinkage_bootstrap)

    print(f"Bootstrap shrinkage: {shrinkage_bootstrap_mean:.4f} ± {shrinkage_bootstrap_std:.4f}")

    return {
        'corr_before': mean_corr_before,
        'corr_after': mean_corr_after,
        'shrinkage_before': shrinkage_before,
        'shrinkage_after': shrinkage_after,
        'shrinkage_bootstrap': shrinkage_bootstrap_mean,
        'residuals_gsr': residuals_gsr
    }

def main():
    print("="*80)
    print("GLOBAL SIGNAL REGRESSION TEST")
    print("="*80)
    print(f"Testing on: sub-{SUBJECT}/{ROI}")
    print("\nGoal: Reduce voxel correlation from 0.98 to 0.3-0.5")
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

    # Test GSR effect
    gsr_results = test_gsr_effect(residuals, n_runs, verbose=True)

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    print(f"\nVoxel correlation:")
    print(f"  Before GSR: {gsr_results['corr_before']:.4f}")
    print(f"  After GSR:  {gsr_results['corr_after']:.4f} ({(gsr_results['corr_after']-gsr_results['corr_before'])*100:+.1f}%)")

    print(f"\nShrinkage:")
    print(f"  Before GSR:           {gsr_results['shrinkage_before']:.4f}")
    print(f"  After GSR:            {gsr_results['shrinkage_after']:.4f}")
    print(f"  After GSR + Bootstrap: {gsr_results['shrinkage_bootstrap']:.4f}")

    print(f"\n" + "="*80)
    print("RECOMMENDATION")
    print("="*80)

    if gsr_results['corr_after'] < 0.7 and gsr_results['shrinkage_bootstrap'] > 0.15:
        print("✓ GSR successfully reduces correlation and increases shrinkage")
        print("\nNext steps:")
        print("  1. Apply GSR before covariance estimation")
        print("  2. Use bootstrap with n_effective")
        print("  3. Expected shrinkage: 0.15-0.40")
        print("  4. Re-test cross-validated whitening")
    elif gsr_results['corr_after'] < gsr_results['corr_before']:
        print("⚠ GSR reduces correlation but shrinkage still low")
        print("\nOptions:")
        print("  1. Force higher minimum shrinkage (0.4-0.6)")
        print("  2. Consider that whitening may not be suitable for this data")
    else:
        print("❌ GSR does not reduce correlation")
        print("\nProblem is elsewhere:")
        print("  - Check voxel selection (too homogeneous?)")
        print("  - Check for scanner artifacts")
        print("  - Whitening may not be appropriate")

    print("\n" + "="*80)

if __name__ == '__main__':
    main()
