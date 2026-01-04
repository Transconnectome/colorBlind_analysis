#!/usr/bin/env python3
"""
Re-test Statistical Significance without sub-02

This script re-runs robustness tests on Option 2D results WITHOUT sub-02
to determine if the reduced systematic difference (T) is still statistically significant.

Tests:
1. Reference robustness (CV across 4 possible references: 03, 05, 06, 07)
2. Group-level permutation test (10,000 permutations)
3. Group-level bootstrap confidence intervals for T
4. Individual-level bootstrap test (each CVD vs HC mean)

Expected Results:
- CV: Should be < 50% (improved from 102-117%)
- Group p-value: May NOT be significant (previous p=0.046 was marginal)
- Individual CI: Check if each CVD individual differs from HC

Usage:
    python retest_significance_no_sub02.py --roi V1 --n-perm 10000
    python retest_significance_no_sub02.py --roi all --n-perm 10000
"""

import argparse
import json
import numpy as np
from pathlib import Path
from scipy.stats import spearmanr
from scipy.spatial.distance import pdist, squareform
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

# Configuration
HC_SUBJECTS = ['03', '05', '06', '07']  # WITHOUT sub-02!
CVD_SUBJECTS = ['08', '09', '10']
ROIS = ['V1', 'V2']
COLOR_NAMES = ['Color1', 'Color2', 'Color3', 'Color4', 'Color5', 'Color6', 'Color7', 'Color8']

def load_subject_amplitudes(subject_id, roi, timestamp='baseline81_deob_determin', dataset='deoblique_v2'):
    """Load subject data - same method as Option 2D"""
    base_dir = Path('/scratch/connectome/haba6030/colorBlind')
    dataset_dir = base_dir / 'derivatives' / f'BH2009_{dataset}' / timestamp

    pattern = f'*_sub-{subject_id}_{roi}_*'
    matches = sorted(dataset_dir.glob(pattern))

    if not matches:
        raise FileNotFoundError(f"No data found for sub-{subject_id}, ROI {roi}")

    subj_dir = matches[0]

    # Load amplitudes_z.npy
    amp_file = subj_dir / 'amplitudes_z.npy'
    if not amp_file.exists():
        raise FileNotFoundError(f"amplitudes_z.npy not found in {subj_dir}")

    amplitudes = np.load(amp_file)  # (n_runs, n_colors, n_voxels)

    # Average across runs
    pattern = amplitudes.mean(axis=0)  # (n_colors, n_voxels)

    print(f"  sub-{subject_id}: {pattern.shape}")
    return pattern

def load_all_subjects(subjects, roi, timestamp, dataset):
    """Load data for all subjects in a group"""
    patterns = []
    for subj in subjects:
        try:
            pattern = load_subject_amplitudes(subj, roi, timestamp, dataset)
            patterns.append(pattern)
        except FileNotFoundError as e:
            print(f"  ⚠️  Skipping sub-{subj}: {e}")
            continue

    if not patterns:
        raise ValueError(f"No valid data found for any subject in {subjects}")

    return patterns

def procrustes_align(X, Y):
    """
    Align Y to X using orthogonal Procrustes

    Returns:
        Y_aligned: Aligned Y
        disparity: Remaining difference after alignment
    """
    # Center
    X_mean = X.mean(axis=0, keepdims=True)
    Y_mean = Y.mean(axis=0, keepdims=True)
    X_centered = X - X_mean
    Y_centered = Y - Y_mean

    # Compute optimal rotation
    U, _, Vt = np.linalg.svd(Y_centered.T @ X_centered)
    R = U @ Vt

    # Apply transformation
    Y_aligned = Y_centered @ R + X_mean

    # Compute disparity
    diff = X - Y_aligned
    disparity = np.sqrt(np.sum(diff**2) / np.sum(X**2))

    return Y_aligned, disparity

def option_a_with_custom_reference(hc_patterns, cvd_patterns, ref_idx):
    """
    Run Option A with specified HC subject as reference

    Args:
        hc_patterns: List of HC patterns
        cvd_patterns: List of CVD patterns
        ref_idx: Index of HC subject to use as reference (0-3)

    Returns:
        T_pattern: Systematic difference (8, n_voxels)
        hc_mean: Aligned HC mean
        cvd_mean: Aligned CVD mean
        hc_disparities: List of HC disparities
        cvd_disparities: List of CVD disparities
    """
    n_hc = len(hc_patterns)
    n_cvd = len(cvd_patterns)

    reference = hc_patterns[ref_idx]
    n_colors, n_voxels = reference.shape

    # Align other HC subjects to reference
    hc_aligned = [reference]
    hc_disparities = [0.0]

    for i in range(n_hc):
        if i == ref_idx:
            continue
        aligned, disp = procrustes_align(reference, hc_patterns[i])
        hc_aligned.append(aligned)
        hc_disparities.append(disp)

    # Compute HC mean
    hc_mean = np.mean(hc_aligned, axis=0)

    # Align CVD subjects to reference
    cvd_aligned = []
    cvd_disparities = []

    for cvd_pattern in cvd_patterns:
        aligned, disp = procrustes_align(reference, cvd_pattern)
        cvd_aligned.append(aligned)
        cvd_disparities.append(disp)

    # Compute CVD mean
    cvd_mean = np.mean(cvd_aligned, axis=0)

    # Compute systematic difference
    T_pattern = cvd_mean - hc_mean

    return T_pattern, hc_mean, cvd_mean, hc_disparities, cvd_disparities

def test_reference_robustness(hc_patterns, cvd_patterns, roi):
    """
    Test robustness across all 4 possible references

    Returns:
        results: Dict with CV, T magnitudes, etc.
    """
    n_hc = len(hc_patterns)
    n_colors = hc_patterns[0].shape[0]

    t_rms_list = []
    hc_disp_list = []
    cvd_disp_list = []

    color_rms_matrix = np.zeros((n_hc, n_colors))

    print(f"\nTesting {n_hc} possible references...")

    for ref_idx in range(n_hc):
        ref_subject = HC_SUBJECTS[ref_idx]

        T, hc_mean, cvd_mean, hc_disp, cvd_disp = option_a_with_custom_reference(
            hc_patterns, cvd_patterns, ref_idx
        )

        # Overall RMS
        t_rms = np.sqrt(np.mean(T**2))
        t_rms_list.append(t_rms)

        # Per-color RMS
        for c in range(n_colors):
            color_rms = np.sqrt(np.mean(T[c]**2))
            color_rms_matrix[ref_idx, c] = color_rms

        # Disparities
        hc_disp_mean = np.mean(hc_disp)
        cvd_disp_mean = np.mean(cvd_disp)
        hc_disp_list.append(hc_disp_mean)
        cvd_disp_list.append(cvd_disp_mean)

        print(f"  Reference {ref_idx} (sub-{ref_subject}): T RMS = {t_rms:.4f}, "
              f"HC disp = {hc_disp_mean:.4f}, CVD disp = {cvd_disp_mean:.4f}")

    # Calculate CV (coefficient of variation)
    t_rms_array = np.array(t_rms_list)
    cv = (np.std(t_rms_array) / np.mean(t_rms_array)) * 100

    print(f"\nReference Robustness Summary:")
    print(f"  T RMS range: {t_rms_array.min():.4f} - {t_rms_array.max():.4f}")
    print(f"  T RMS mean: {t_rms_array.mean():.4f}")
    print(f"  T RMS std: {t_rms_array.std():.4f}")
    print(f"  CV: {cv:.1f}%")

    if cv < 50:
        print(f"  ✅ CV < 50% - Reference choice is stable!")
    else:
        print(f"  ⚠️  CV > 50% - Results still sensitive to reference choice")

    results = {
        'roi': roi,
        'n_references': n_hc,
        'reference_subjects': HC_SUBJECTS,
        't_rms_list': t_rms_list,
        't_rms_mean': float(t_rms_array.mean()),
        't_rms_std': float(t_rms_array.std()),
        't_rms_min': float(t_rms_array.min()),
        't_rms_max': float(t_rms_array.max()),
        'cv_percent': float(cv),
        'hc_disparity_mean': float(np.mean(hc_disp_list)),
        'cvd_disparity_mean': float(np.mean(cvd_disp_list)),
        'color_rms_matrix': color_rms_matrix.tolist()
    }

    return results

def permutation_test(hc_patterns, cvd_patterns, roi, n_perm=10000):
    """
    Permutation test for statistical significance

    Shuffle HC/CVD labels and compute null distribution of T magnitude
    """
    print(f"\nRunning permutation test ({n_perm} permutations)...")

    # Observed T (using first HC as reference)
    T_obs, _, _, _, _ = option_a_with_custom_reference(hc_patterns, cvd_patterns, ref_idx=0)
    rms_obs = np.sqrt(np.mean(T_obs**2))

    print(f"  Observed T RMS: {rms_obs:.4f}")

    # Combine all subjects
    all_patterns = hc_patterns + cvd_patterns
    n_hc = len(hc_patterns)
    n_total = len(all_patterns)

    # Permutation test
    null_rms = []

    for perm_idx in range(n_perm):
        if (perm_idx + 1) % 1000 == 0:
            print(f"    Permutation {perm_idx + 1}/{n_perm}...")

        # Shuffle labels
        perm_indices = np.random.permutation(n_total)
        hc_perm_idx = perm_indices[:n_hc]
        cvd_perm_idx = perm_indices[n_hc:]

        hc_perm = [all_patterns[i] for i in hc_perm_idx]
        cvd_perm = [all_patterns[i] for i in cvd_perm_idx]

        # Compute T for permuted data
        T_perm, _, _, _, _ = option_a_with_custom_reference(hc_perm, cvd_perm, ref_idx=0)
        rms_perm = np.sqrt(np.mean(T_perm**2))
        null_rms.append(rms_perm)

    null_rms = np.array(null_rms)

    # Compute p-value
    p_value = np.sum(null_rms >= rms_obs) / n_perm

    print(f"\n  Null distribution:")
    print(f"    Mean: {null_rms.mean():.4f}")
    print(f"    Std: {null_rms.std():.4f}")
    print(f"    95th percentile: {np.percentile(null_rms, 95):.4f}")
    print(f"    99th percentile: {np.percentile(null_rms, 99):.4f}")
    print(f"\n  P-value: {p_value:.4f}")

    if p_value < 0.05:
        print(f"  ✅ Significant at p < 0.05")
    else:
        print(f"  ❌ NOT significant at p < 0.05")

    results = {
        'roi': roi,
        'n_permutations': n_perm,
        'rms_observed': float(rms_obs),
        'rms_null_mean': float(null_rms.mean()),
        'rms_null_std': float(null_rms.std()),
        'rms_null_95': float(np.percentile(null_rms, 95)),
        'rms_null_99': float(np.percentile(null_rms, 99)),
        'p_value': float(p_value),
        'significant': bool(p_value < 0.05),
        'null_distribution': null_rms.tolist()
    }

    return results

def bootstrap_confidence_interval(hc_patterns, cvd_patterns, roi, n_bootstrap=10000):
    """
    Bootstrap confidence interval for T magnitude (group-level)
    """
    print(f"\nRunning group-level bootstrap ({n_bootstrap} iterations)...")

    n_hc = len(hc_patterns)
    n_cvd = len(cvd_patterns)

    bootstrap_rms = []

    for boot_idx in range(n_bootstrap):
        if (boot_idx + 1) % 1000 == 0:
            print(f"    Bootstrap {boot_idx + 1}/{n_bootstrap}...")

        # Resample with replacement
        hc_boot_idx = np.random.choice(n_hc, size=n_hc, replace=True)
        cvd_boot_idx = np.random.choice(n_cvd, size=n_cvd, replace=True)

        hc_boot = [hc_patterns[i] for i in hc_boot_idx]
        cvd_boot = [cvd_patterns[i] for i in cvd_boot_idx]

        # Compute T
        T_boot, _, _, _, _ = option_a_with_custom_reference(hc_boot, cvd_boot, ref_idx=0)
        rms_boot = np.sqrt(np.mean(T_boot**2))
        bootstrap_rms.append(rms_boot)

    bootstrap_rms = np.array(bootstrap_rms)

    # Compute confidence interval
    ci_lower = np.percentile(bootstrap_rms, 2.5)
    ci_upper = np.percentile(bootstrap_rms, 97.5)

    print(f"\n  Bootstrap distribution:")
    print(f"    Mean: {bootstrap_rms.mean():.4f}")
    print(f"    Std: {bootstrap_rms.std():.4f}")
    print(f"    95% CI: [{ci_lower:.4f}, {ci_upper:.4f}]")

    if ci_lower > 0:
        print(f"  ✅ CI excludes zero - T is reliably non-zero")
    else:
        print(f"  ⚠️  CI includes zero - T may not be reliable")

    results = {
        'roi': roi,
        'n_bootstrap': n_bootstrap,
        'rms_mean': float(bootstrap_rms.mean()),
        'rms_std': float(bootstrap_rms.std()),
        'ci_lower': float(ci_lower),
        'ci_upper': float(ci_upper),
        'excludes_zero': bool(ci_lower > 0),
        'bootstrap_distribution': bootstrap_rms.tolist()
    }

    return results

def test_individual_cvd_significance(hc_patterns, cvd_patterns, roi, n_bootstrap=10000):
    """
    Individual-level test: Each CVD subject vs HC mean

    This is critical for personalized filter creation!
    Tests whether each individual CVD differs from HC mean.
    """
    print(f"\n" + "="*80)
    print(f"INDIVIDUAL-LEVEL TEST: Each CVD vs HC mean")
    print("="*80)
    print(f"Purpose: Determine if individual CVD filters can be created")
    print(f"Method: Bootstrap CI for each CVD individual vs HC mean")
    print()

    # Use first HC as reference
    reference = hc_patterns[0]
    n_hc = len(hc_patterns)

    # Align all HC to reference and compute mean
    hc_aligned = [reference]
    for i in range(1, n_hc):
        aligned, _ = procrustes_align(reference, hc_patterns[i])
        hc_aligned.append(aligned)
    hc_mean = np.mean(hc_aligned, axis=0)

    results = {}

    for cvd_idx, cvd_pattern in enumerate(cvd_patterns):
        cvd_subject = CVD_SUBJECTS[cvd_idx]

        print(f"\nTesting sub-{cvd_subject} vs HC mean...")

        # Align CVD to reference
        cvd_aligned, disparity = procrustes_align(reference, cvd_pattern)

        # Observed difference
        T_obs = cvd_aligned - hc_mean
        rms_obs = np.sqrt(np.mean(T_obs**2))

        # Per-color RMS
        color_rms = []
        for c in range(T_obs.shape[0]):
            color_rms.append(np.sqrt(np.mean(T_obs[c]**2)))

        # Bootstrap CI
        bootstrap_rms = []

        print(f"  Running {n_bootstrap} bootstrap iterations...")
        for boot_idx in range(n_bootstrap):
            if (boot_idx + 1) % 2000 == 0:
                print(f"    Bootstrap {boot_idx + 1}/{n_bootstrap}...")

            # Resample HC with replacement
            hc_boot_idx = np.random.choice(n_hc, size=n_hc, replace=True)
            hc_boot = [hc_patterns[i] for i in hc_boot_idx]

            # Align HC_boot to first subject and compute mean
            hc_boot_ref = hc_boot[0]
            hc_boot_aligned = [hc_boot_ref]
            for i in range(1, len(hc_boot)):
                aligned, _ = procrustes_align(hc_boot_ref, hc_boot[i])
                hc_boot_aligned.append(aligned)
            hc_boot_mean = np.mean(hc_boot_aligned, axis=0)

            # Align CVD to HC_boot reference
            cvd_boot_aligned, _ = procrustes_align(hc_boot_ref, cvd_pattern)

            # Compute T_boot
            T_boot = cvd_boot_aligned - hc_boot_mean
            rms_boot = np.sqrt(np.mean(T_boot**2))
            bootstrap_rms.append(rms_boot)

        bootstrap_rms = np.array(bootstrap_rms)
        ci_lower = np.percentile(bootstrap_rms, 2.5)
        ci_upper = np.percentile(bootstrap_rms, 97.5)

        excludes_zero = ci_lower > 0

        print(f"\n  Results for sub-{cvd_subject}:")
        print(f"    Observed T RMS: {rms_obs:.4f}")
        print(f"    Disparity: {disparity:.4f}")
        print(f"    Bootstrap mean: {bootstrap_rms.mean():.4f}")
        print(f"    Bootstrap std: {bootstrap_rms.std():.4f}")
        print(f"    95% CI: [{ci_lower:.4f}, {ci_upper:.4f}]")

        if excludes_zero:
            print(f"    ✅ SIGNIFICANT - CI excludes zero")
            print(f"    → Individual filter for sub-{cvd_subject} is feasible!")
        else:
            print(f"    ❌ NOT SIGNIFICANT - CI includes zero")
            print(f"    → Individual filter for sub-{cvd_subject} may be unreliable")

        results[cvd_subject] = {
            'rms_observed': float(rms_obs),
            'disparity': float(disparity),
            'color_rms': [float(x) for x in color_rms],
            'bootstrap_mean': float(bootstrap_rms.mean()),
            'bootstrap_std': float(bootstrap_rms.std()),
            'ci_lower': float(ci_lower),
            'ci_upper': float(ci_upper),
            'excludes_zero': bool(excludes_zero),
            'bootstrap_distribution': bootstrap_rms.tolist()
        }

    # Summary
    print(f"\n" + "="*80)
    print("INDIVIDUAL-LEVEL SUMMARY")
    print("="*80)
    significant_count = sum(1 for r in results.values() if r['excludes_zero'])
    print(f"Significant CVD individuals: {significant_count}/{len(CVD_SUBJECTS)}")

    for cvd_subj, res in results.items():
        status = "✅ Filter feasible" if res['excludes_zero'] else "❌ Filter unreliable"
        print(f"  sub-{cvd_subj}: T = {res['rms_observed']:.4f}, CI = [{res['ci_lower']:.4f}, {res['ci_upper']:.4f}] - {status}")

    return results

def create_visualization(ref_results, perm_results, boot_results, indiv_results, roi, output_dir):
    """Create comprehensive visualization including individual-level results"""
    fig = plt.figure(figsize=(20, 16))
    gs = fig.add_gridspec(3, 4, hspace=0.3, wspace=0.3)

    fig.suptitle(f'{roi}: Statistical Significance Tests (WITHOUT sub-02)',
                 fontsize=16, fontweight='bold', y=0.995)

    # --- Row 1: Reference Robustness ---

    # Panel 1: Reference Robustness (T RMS)
    ax = fig.add_subplot(gs[0, 0])
    refs = ref_results['reference_subjects']
    t_rms_list = ref_results['t_rms_list']

    ax.bar(range(len(refs)), t_rms_list, color='steelblue', alpha=0.7)
    ax.axhline(y=ref_results['t_rms_mean'], color='red', linestyle='--',
               label=f"Mean = {ref_results['t_rms_mean']:.4f}")
    ax.set_xlabel('Reference Subject')
    ax.set_ylabel('T RMS')
    ax.set_title(f"Reference Robustness\nCV = {ref_results['cv_percent']:.1f}%")
    ax.set_xticks(range(len(refs)))
    ax.set_xticklabels([f"sub-{s}" for s in refs], rotation=45)
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Panel 2: Color-specific RMS heatmap
    ax = fig.add_subplot(gs[0, 1])
    color_matrix = np.array(ref_results['color_rms_matrix'])

    im = ax.imshow(color_matrix.T, aspect='auto', cmap='YlOrRd', interpolation='nearest')

    # Add text annotations
    for i in range(len(COLOR_NAMES)):
        for j in range(len(refs)):
            text = ax.text(j, i, f'{color_matrix[j, i]:.3f}',
                          ha="center", va="center", color="black", fontsize=8)

    ax.set_xlabel('Reference Subject')
    ax.set_ylabel('Color')
    ax.set_title('Color-Specific T RMS')
    ax.set_xticks(range(len(refs)))
    ax.set_xticklabels([f"sub-{s}" for s in refs], rotation=45)
    ax.set_yticks(range(len(COLOR_NAMES)))
    ax.set_yticklabels(COLOR_NAMES)
    plt.colorbar(im, ax=ax, label='RMS')

    # Panel 3: Disparity comparison
    ax = fig.add_subplot(gs[0, 2])
    hc_disp = ref_results['hc_disparity_mean']
    cvd_disp = ref_results['cvd_disparity_mean']

    ax.bar(['HC', 'CVD'], [hc_disp, cvd_disp], color=['steelblue', 'coral'], alpha=0.7)
    ax.set_ylabel('Mean Disparity')
    ax.set_title('Procrustes Alignment Quality')
    ax.axhline(y=0.3, color='red', linestyle='--', alpha=0.5, label='Normal range (<0.3)')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

    # Panel 4: Summary statistics (top right)
    ax = fig.add_subplot(gs[0, 3])
    ax.axis('off')

    summary_text = f"""
GROUP-LEVEL SUMMARY
═══════════════════

Reference Robustness:
  • T RMS mean: {ref_results['t_rms_mean']:.4f}
  • CV: {ref_results['cv_percent']:.1f}%
  • Status: {'✅ Stable' if ref_results['cv_percent'] < 50 else '⚠️ Unstable'}

Permutation Test:
  • Observed: {perm_results['rms_observed']:.4f}
  • P-value: {perm_results['p_value']:.4f}
  • Result: {'✅ Significant' if perm_results['significant'] else '❌ Not significant'}

Bootstrap CI:
  • Mean: {boot_results['rms_mean']:.4f}
  • 95% CI: [{boot_results['ci_lower']:.4f}, {boot_results['ci_upper']:.4f}]
  • Result: {'✅ Excludes 0' if boot_results['excludes_zero'] else '❌ Includes 0'}
    """

    ax.text(0.05, 0.5, summary_text, transform=ax.transAxes,
            fontsize=9, verticalalignment='center', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.3))

    # --- Row 2: Group-level tests ---

    # Panel 5: Permutation test histogram
    ax = fig.add_subplot(gs[1, 0:2])
    null_dist = np.array(perm_results['null_distribution'])
    rms_obs = perm_results['rms_observed']
    p_val = perm_results['p_value']

    ax.hist(null_dist, bins=50, color='gray', alpha=0.7, edgecolor='black', label='Null distribution')
    ax.axvline(x=rms_obs, color='red', linestyle='--', linewidth=2,
               label=f'Observed = {rms_obs:.4f}')
    ax.axvline(x=np.percentile(null_dist, 95), color='orange', linestyle=':',
               label=f'95th percentile = {np.percentile(null_dist, 95):.4f}')

    ax.set_xlabel('T RMS')
    ax.set_ylabel('Frequency')
    ax.set_title(f'Group-Level Permutation Test\np = {p_val:.4f}')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

    # Panel 6: Group-level bootstrap CI
    ax = fig.add_subplot(gs[1, 2:4])
    boot_dist = np.array(boot_results['bootstrap_distribution'])
    ci_lower = boot_results['ci_lower']
    ci_upper = boot_results['ci_upper']

    ax.hist(boot_dist, bins=50, color='steelblue', alpha=0.7, edgecolor='black',
            label='Bootstrap distribution')
    ax.axvline(x=ci_lower, color='red', linestyle='--', linewidth=2,
               label=f'95% CI: [{ci_lower:.4f}, {ci_upper:.4f}]')
    ax.axvline(x=ci_upper, color='red', linestyle='--', linewidth=2)
    ax.axvline(x=boot_results['rms_mean'], color='darkred', linestyle='-', linewidth=2,
               label=f"Mean = {boot_results['rms_mean']:.4f}")

    ax.set_xlabel('T RMS')
    ax.set_ylabel('Frequency')
    ax.set_title('Group-Level Bootstrap CI')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

    # --- Row 3: Individual-level tests ---

    # Panel 7: Individual T RMS comparison
    ax = fig.add_subplot(gs[2, 0])
    cvd_subjects = list(indiv_results.keys())
    rms_values = [indiv_results[s]['rms_observed'] for s in cvd_subjects]
    ci_lowers = [indiv_results[s]['ci_lower'] for s in cvd_subjects]
    ci_uppers = [indiv_results[s]['ci_upper'] for s in cvd_subjects]
    colors_bar = ['green' if indiv_results[s]['excludes_zero'] else 'red' for s in cvd_subjects]

    x_pos = range(len(cvd_subjects))
    ax.bar(x_pos, rms_values, color=colors_bar, alpha=0.7)

    # Add error bars for CI
    yerr_lower = [rms_values[i] - ci_lowers[i] for i in range(len(cvd_subjects))]
    yerr_upper = [ci_uppers[i] - rms_values[i] for i in range(len(cvd_subjects))]
    ax.errorbar(x_pos, rms_values, yerr=[yerr_lower, yerr_upper],
                fmt='none', ecolor='black', capsize=5, linewidth=2)

    ax.axhline(y=0, color='gray', linestyle=':', linewidth=1)
    ax.set_xlabel('CVD Subject')
    ax.set_ylabel('T RMS (Individual vs HC mean)')
    ax.set_title('Individual CVD vs HC Mean\n(Green = Significant, Red = Not significant)')
    ax.set_xticks(x_pos)
    ax.set_xticklabels([f"sub-{s}" for s in cvd_subjects])
    ax.grid(True, alpha=0.3, axis='y')

    # Panel 8-10: Individual bootstrap distributions
    for idx, cvd_subject in enumerate(cvd_subjects):
        ax = fig.add_subplot(gs[2, idx+1])

        boot_dist_indiv = np.array(indiv_results[cvd_subject]['bootstrap_distribution'])
        ci_low = indiv_results[cvd_subject]['ci_lower']
        ci_high = indiv_results[cvd_subject]['ci_upper']
        rms_indiv = indiv_results[cvd_subject]['rms_observed']

        color_fill = 'green' if indiv_results[cvd_subject]['excludes_zero'] else 'red'

        ax.hist(boot_dist_indiv, bins=30, color=color_fill, alpha=0.5, edgecolor='black')
        ax.axvline(x=ci_low, color='red', linestyle='--', linewidth=1.5)
        ax.axvline(x=ci_high, color='red', linestyle='--', linewidth=1.5)
        ax.axvline(x=rms_indiv, color='darkred', linestyle='-', linewidth=2)
        ax.axvline(x=0, color='gray', linestyle=':', linewidth=1)

        ax.set_xlabel('T RMS')
        ax.set_ylabel('Frequency')
        status = '✅' if indiv_results[cvd_subject]['excludes_zero'] else '❌'
        ax.set_title(f'sub-{cvd_subject} {status}\nCI: [{ci_low:.3f}, {ci_high:.3f}]', fontsize=9)
        ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()

    fig_path = output_dir / f'statistical_tests_{roi}.png'
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"\n✓ Figure saved: {fig_path}")

def main():
    parser = argparse.ArgumentParser(description='Re-test statistical significance without sub-02')
    parser.add_argument('--roi', type=str, default='V1', choices=['V1', 'V2', 'all'],
                        help='ROI to analyze')
    parser.add_argument('--n-perm', type=int, default=10000,
                        help='Number of permutations')
    parser.add_argument('--n-boot', type=int, default=10000,
                        help='Number of bootstrap iterations')
    parser.add_argument('--timestamp', type=str, default='baseline81_deob_determin',
                        help='Timestamp directory')
    parser.add_argument('--dataset', type=str, default='deoblique_v2',
                        help='Dataset name')

    args = parser.parse_args()

    # Set ROIs to process
    rois_to_process = ROIS if args.roi == 'all' else [args.roi]

    # Output directory
    base_dir = Path('/scratch/connectome/haba6030/colorBlind')
    output_dir = base_dir / 'results' / 'group_level' / 'significance_tests_no_sub02'
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("Statistical Significance Re-testing (WITHOUT sub-02)")
    print("=" * 80)
    print(f"HC subjects: {HC_SUBJECTS} (n={len(HC_SUBJECTS)})")
    print(f"CVD subjects: {CVD_SUBJECTS} (n={len(CVD_SUBJECTS)})")
    print(f"ROIs: {rois_to_process}")
    print(f"N permutations: {args.n_perm}")
    print(f"N bootstrap: {args.n_boot}")
    print()

    for roi in rois_to_process:
        print("=" * 80)
        print(f"ROI: {roi}")
        print("=" * 80)

        # Load data
        print(f"\nLoading {roi} data for {len(HC_SUBJECTS)} HC subjects...")
        hc_patterns = load_all_subjects(HC_SUBJECTS, roi, args.timestamp, args.dataset)

        print(f"\nLoading {roi} data for {len(CVD_SUBJECTS)} CVD subjects...")
        cvd_patterns = load_all_subjects(CVD_SUBJECTS, roi, args.timestamp, args.dataset)

        # Unify voxel count (handle different voxel numbers across subjects)
        hc_voxels = [p.shape[1] for p in hc_patterns]
        cvd_voxels = [p.shape[1] for p in cvd_patterns]
        all_voxels = hc_voxels + cvd_voxels

        min_voxels = min(all_voxels)
        max_voxels = max(all_voxels)

        if min_voxels != max_voxels:
            print(f"\n⚠️  Unifying voxels: HC {max(hc_voxels)}, CVD {min(cvd_voxels)} → {min_voxels}")
            hc_patterns = [p[:, :min_voxels] for p in hc_patterns]
            cvd_patterns = [p[:, :min_voxels] for p in cvd_patterns]
            print(f"  Unified shape: {hc_patterns[0].shape}")

        # Run tests
        print("\n" + "="*80)
        print("PART 1: GROUP-LEVEL TESTS")
        print("="*80)

        ref_results = test_reference_robustness(hc_patterns, cvd_patterns, roi)
        perm_results = permutation_test(hc_patterns, cvd_patterns, roi, n_perm=args.n_perm)
        boot_results = bootstrap_confidence_interval(hc_patterns, cvd_patterns, roi, n_bootstrap=args.n_boot)

        print("\n" + "="*80)
        print("PART 2: INDIVIDUAL-LEVEL TESTS")
        print("="*80)

        indiv_results = test_individual_cvd_significance(hc_patterns, cvd_patterns, roi, n_bootstrap=args.n_boot)

        # Save results
        results = {
            'roi': roi,
            'hc_subjects': HC_SUBJECTS,
            'cvd_subjects': CVD_SUBJECTS,
            'group_level': {
                'reference_robustness': ref_results,
                'permutation_test': perm_results,
                'bootstrap_ci': boot_results
            },
            'individual_level': indiv_results
        }

        json_path = output_dir / f'significance_tests_{roi}.json'
        with open(json_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n✓ Results saved: {json_path}")

        # Create visualization
        create_visualization(ref_results, perm_results, boot_results, indiv_results, roi, output_dir)

    print("\n" + "=" * 80)
    print("Statistical significance re-testing complete!")
    print("=" * 80)
    print(f"\nResults saved to: {output_dir}")
    print("\nDownload with:")
    print(f"  scp -r haba6030@node2:{output_dir} results/group_level/")
    print()
    print("Key findings to check:")
    print("  1. GROUP-LEVEL: Is CVD common pattern significant?")
    print("  2. INDIVIDUAL-LEVEL: Can we create filters for each CVD?")
    print("  3. Decision: Proceed with filters OR need more data")

if __name__ == '__main__':
    main()
