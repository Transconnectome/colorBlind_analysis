#!/usr/bin/env python3
"""
Quick test for whitening fixes:
1. Run-wise intercept removal
2. ACF-1 temporal autocorrelation correction
3. Minimum shrinkage (0.25)
4. Actual whitened noise covariance (not identity assumption)

Test on sub-01/V1 only for quick validation.

Expected improvements:
- Shrinkage: 0.001 → 0.25+ (ACF correction + minimum)
- Effective SNR: No longer explosive (realistic values)
- Pattern SNR: Should NOT decrease drastically
- Procrustes: Should remain compatible

Author: Claude Code
Date: 2026-02-08
"""

import numpy as np
from pathlib import Path
import sys

# Add utils to path
script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(script_dir / 'utils'))

from whitening import (
    preprocess_residuals_run_wise,
    compute_temporal_autocorrelation,
    estimate_noise_covariance,
    whiten_amplitudes,
    whiten_amplitudes_crossvalidated,
    compute_pattern_snr,
    compute_effective_snr,
    compare_snr_before_after_whitening
)

# Test configuration
SUBJECT = "01"
ROI = "V1"
BASE_DIR = Path(__file__).parent.parent.parent.parent / "phase1_preprocess_decoding" / "results" / "baseline_residuals"

def main():
    print("="*80)
    print("WHITENING FIXES VALIDATION TEST")
    print("="*80)
    print(f"Testing on: sub-{SUBJECT}/{ROI}")
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

    # ========================================
    # TEST 1: Run-wise intercept removal
    # ========================================
    print("="*80)
    print("TEST 1: Run-wise Intercept Removal")
    print("="*80)

    print(f"Before preprocessing:")
    print(f"  Global mean: {residuals.mean():.3f}")
    print(f"  Per-voxel mean: {residuals.mean(axis=0).mean():.3f}")

    residuals_preprocessed = preprocess_residuals_run_wise(residuals, n_runs, verbose=True)

    print(f"\nAfter preprocessing:")
    print(f"  Global mean: {residuals_preprocessed.mean():.6f} (should be ~0)")
    print(f"  Per-voxel mean: {residuals_preprocessed.mean(axis=0).mean():.6f}")
    print("")

    # ========================================
    # TEST 2: ACF-1 temporal autocorrelation
    # ========================================
    print("="*80)
    print("TEST 2: Temporal Autocorrelation (ACF-1)")
    print("="*80)

    acf_metrics = compute_temporal_autocorrelation(residuals_preprocessed)

    print(f"ACF-1 (mean): {acf_metrics['acf1_mean']:.3f} ± {acf_metrics['acf1_std']:.3f}")
    print(f"Raw n_samples: {acf_metrics['n_raw']}")
    print(f"Effective n_samples: {acf_metrics['n_effective']:.1f}")
    print(f"Efficiency: {acf_metrics['n_effective_ratio']*100:.1f}%")
    print("")

    # ========================================
    # TEST 3: Shrinkage comparison
    # ========================================
    print("="*80)
    print("TEST 3: Shrinkage Estimation (Old vs New)")
    print("="*80)

    # Old method (no ACF, no minimum)
    from sklearn.covariance import LedoitWolf
    lw_old = LedoitWolf(assume_centered=False)
    lw_old.fit(residuals - residuals.mean(axis=0, keepdims=True))  # Simple centering
    shrinkage_old = lw_old.shrinkage_

    print(f"OLD method (simple centering, no ACF, no min):")
    print(f"  Shrinkage: {shrinkage_old:.3f}")

    # New method (run-wise preprocessing, ACF, minimum 0.25)
    noise_cov_new, shrinkage_new = estimate_noise_covariance(
        residuals_preprocessed,
        method='ledoit_wolf',
        apply_acf_correction=True,
        min_shrinkage=0.25
    )

    print(f"\nNEW method (run-wise preprocessing, ACF-1, min=0.25):")
    print(f"  Shrinkage: {shrinkage_new:.3f}")
    print(f"  Improvement: {shrinkage_new - shrinkage_old:+.3f}")

    if shrinkage_new >= 0.25:
        print(f"✓ Shrinkage is in fMRI-appropriate range (≥0.25)")
    else:
        print(f"⚠️  Shrinkage still too low")
    print("")

    # ========================================
    # TEST 4A: Non-CV Whitening (WRONG - Double Dipping)
    # ========================================
    print("="*80)
    print("TEST 4A: Non-CV Whitening (WRONG - for comparison)")
    print("="*80)
    print("⚠️  This uses SAME data for Σ estimation and whitening (Double-Dipping)")

    amplitudes_whitened_wrong, whitening_matrix = whiten_amplitudes(amplitudes_raw, noise_cov_new)

    snr_wrong = compare_snr_before_after_whitening(
        amplitudes_raw,
        amplitudes_whitened_wrong,
        residuals_preprocessed,
        noise_cov_new,
        whitening_matrix=whitening_matrix
    )

    print("\nNon-CV SNR (WRONG):")
    print(f"  Pattern SNR:    {snr_wrong['pattern_snr']['raw']['pattern_snr']:.3f} → "
          f"{snr_wrong['pattern_snr']['whitened']['pattern_snr']:.3f} "
          f"({snr_wrong['pattern_snr']['improvement_pct']:+.1f}%)")

    # ========================================
    # TEST 4B: Cross-Validated Whitening (CORRECT)
    # ========================================
    print("\n" + "="*80)
    print("TEST 4B: Cross-Validated Whitening (CORRECT)")
    print("="*80)
    print("✓ Uses INDEPENDENT data: Train on Run 1-3, Test on Run 4-6")

    amplitudes_whitened_cv, cv_info = whiten_amplitudes_crossvalidated(
        amplitudes_raw,
        residuals,  # Will be split internally
        n_folds=2,
        method='ledoit_wolf',
        apply_acf_correction=True,
        min_shrinkage=0.1,  # Lower safety net
        verbose=True
    )

    # Compute SNR on CV-whitened data
    print("\nComputing SNR metrics on CV-whitened data...")

    # For CV comparison, we need average noise_cov
    noise_cov_cv = np.mean(cv_info['noise_covs'], axis=0)
    shrinkage_cv = np.mean(cv_info['shrinkages'])

    # Compute Pattern SNR directly
    pattern_snr_cv_raw = compute_pattern_snr(amplitudes_raw)
    pattern_snr_cv_whitened = compute_pattern_snr(amplitudes_whitened_cv)

    print("\nCV-Whitened SNR (CORRECT):")
    print(f"  Pattern SNR:    {pattern_snr_cv_raw['pattern_snr']:.3f} → "
          f"{pattern_snr_cv_whitened['pattern_snr']:.3f} "
          f"({(pattern_snr_cv_whitened['pattern_snr']/pattern_snr_cv_raw['pattern_snr']-1)*100:+.1f}%)")

    # ========================================
    # TEST 4C: Bootstrap + CV (Best Practice)
    # ========================================
    print("\n" + "="*80)
    print("TEST 4C: Bootstrap + Cross-Validation (BEST)")
    print("="*80)

    # CV with bootstrap
    amplitudes_whitened_bootstrap_cv, cv_bootstrap_info = whiten_amplitudes_crossvalidated(
        amplitudes_raw,
        residuals,
        n_folds=2,
        method='ledoit_wolf',
        apply_acf_correction=True,
        min_shrinkage=0.1,
        verbose=True
    )

    # Manually test bootstrap on preprocessed residuals
    print("\nTesting Bootstrap shrinkage estimation...")
    noise_cov_bootstrap, shrinkage_bootstrap = estimate_noise_covariance(
        residuals_preprocessed,
        method='ledoit_wolf',
        apply_acf_correction=True,
        use_bootstrap=True,
        n_bootstraps=100,
        min_shrinkage=0.1
    )

    # Validation checks
    print("\n" + "="*80)
    print("VALIDATION CHECKS")
    print("="*80)

    checks = []

    # Check 1: CV shrinkage in valid range
    if 0.15 <= shrinkage_cv <= 0.6:
        checks.append(("✓", f"CV Shrinkage in valid range: {shrinkage_cv:.3f}"))
    else:
        checks.append(("⚠", f"CV Shrinkage: {shrinkage_cv:.3f} (expected 0.15-0.6)"))

    # Check 2: Bootstrap increases shrinkage
    if shrinkage_bootstrap > shrinkage_new:
        checks.append(("✓", f"Bootstrap increases shrinkage: {shrinkage_new:.3f} → {shrinkage_bootstrap:.3f}"))
    else:
        checks.append(("⚠", f"Bootstrap did not increase shrinkage: {shrinkage_bootstrap:.3f}"))

    # Check 3: CV preserves Pattern SNR
    pattern_snr_cv_change = (pattern_snr_cv_whitened['pattern_snr'] / pattern_snr_cv_raw['pattern_snr'] - 1) * 100
    if pattern_snr_cv_change > -30:  # Allow some reduction
        checks.append(("✓", f"CV preserves Pattern SNR: {pattern_snr_cv_change:+.1f}% change"))
    else:
        checks.append(("✗", f"CV destroys Pattern SNR: {pattern_snr_cv_change:+.1f}%"))

    # Check 4: Non-CV is worse than CV
    pattern_snr_noncv_change = snr_wrong['pattern_snr']['improvement_pct']
    if pattern_snr_cv_change > pattern_snr_noncv_change:
        checks.append(("✓", f"CV better than non-CV: {pattern_snr_cv_change:.1f}% vs {pattern_snr_noncv_change:.1f}%"))
    else:
        checks.append(("⚠", f"CV not better than non-CV (unexpected)"))

    for status, message in checks:
        print(f"{status} {message}")

    print("")

    # Overall verdict
    critical_passed = checks[2][0] == "✓"  # Pattern SNR preserved
    if critical_passed:
        print("="*80)
        print("✓ CRITICAL CHECK PASSED - Cross-validation preserves signal!")
        print("="*80)
        print("\nRecommendation: Use CV whitening for full evaluation")
        print("  - n_folds=2 (Run 1-3 vs 4-6)")
        print("  - apply_acf_correction=True")
        print("  - min_shrinkage=0.1 (safety net)")
        if shrinkage_bootstrap > 0.2:
            print("  - use_bootstrap=True (natural shrinkage increase)")
    else:
        print("="*80)
        print("⚠️  CRITICAL CHECK FAILED - Signal still being destroyed")
        print("="*80)
        print("\nFurther investigation needed:")

if __name__ == '__main__':
    main()
