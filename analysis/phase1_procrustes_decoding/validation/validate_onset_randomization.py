#!/usr/bin/env python3
"""
Onset Randomization Validation Script

Verify FIR estimation robustness by shuffling trial order.

Expected outcomes:
- Proper FIR: Original convex → Randomized random/flat
- Drift contamination: Original linear ramp → Randomized linear ramp (persists)

Test subjects: sub-01, V1 and V2

Author: Claude Code
Date: 2026-02-16
"""

import numpy as np
import pandas as pd
import nibabel as nib
from pathlib import Path
from scipy.stats import spearmanr
import matplotlib.pyplot as plt
import json
import sys
import argparse

# ============================================================================
# Configuration
# ============================================================================

# Paths (server)
BASE_DIR = Path("/scratch/connectome/haba6030/colorBlind")
FMRIPREP_DIR = Path("/storage/connectome/haba6030/fmriprep_out_method3_header_mi")
EVENT_DIR = Path("/storage/connectome/haba6030/bids_editted")
ROI_MASKS_DIR = BASE_DIR / "analysis" / "roi_masks" / "method3_header_mi"
OUTPUT_DIR = BASE_DIR / "derivatives" / "onset_validation"

# Pipeline settings
TR = 1.5
N_SCANS = 288
N_RUNS = 6
N_COLORS = 8
FIR_DELAYS = np.arange(8) * TR

print(f"Onset Randomization Validation")
print(f"  Test: Original onsets vs Randomized onsets")
print(f"  Subjects: sub-01 only")
print(f"  ROIs: V1, V2")
print()


# ============================================================================
# Utility Functions
# ============================================================================

def get_roi_mask_path(subject_id, roi_name):
    """Get ROI mask path (server)"""
    roi_map = {'V1': 'V1', 'V2': 'V2', 'V3': 'V3', 'V4': 'hV4'}
    roi_prefix = roi_map.get(roi_name)
    if roi_prefix is None:
        raise ValueError(f"Unknown ROI: {roi_name}")

    mask_filename = f"{roi_prefix}_mask_thr50_intnearest_binTrue_maskfunc_gmTrue_subjFalse.nii.gz"
    mask_path = ROI_MASKS_DIR / f"sub-{subject_id}" / "roi_pipeline" / mask_filename
    return mask_path


def load_bold_data(subject_id, roi_name, run_idx):
    """Load BOLD data for single run"""
    roi_mask_path = get_roi_mask_path(subject_id, roi_name)
    if not roi_mask_path.exists():
        raise FileNotFoundError(f"ROI mask not found: {roi_mask_path}")

    func_file = FMRIPREP_DIR / f"sub-{subject_id}" / "func" / \
                f"sub-{subject_id}_task-rsvp_run-{run_idx}_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz"

    if not func_file.exists():
        raise FileNotFoundError(f"BOLD file not found: {func_file}")

    func_img = nib.load(func_file)
    roi_mask_img = nib.load(roi_mask_path)

    func_data_4d = func_img.get_fdata()
    roi_mask = roi_mask_img.get_fdata() > 0

    func_data = func_data_4d[roi_mask].T  # (n_scans, n_voxels)

    events_file = EVENT_DIR / f"sub-{subject_id}" / "func" / \
                  f"sub-{subject_id}_task-rsvp_run-{run_idx}_events.tsv"

    if not events_file.exists():
        raise FileNotFoundError(f"Events file not found: {events_file}")

    events = pd.read_csv(events_file, sep='\t')
    events['onset'] = events['onset'] - (3 * TR)

    return func_data, events


def randomize_onsets(events_df, seed):
    """
    Shuffle onset times while preserving trial structure

    Args:
        events_df: Original events DataFrame
        seed: Random seed for reproducibility

    Returns:
        DataFrame with shuffled onsets
    """
    np.random.seed(seed)
    events_randomized = events_df.copy()

    # Extract color trial onsets
    color_mask = events_df['trial_type'].str.contains('color', na=False)
    onset_times = events_df.loc[color_mask, 'onset'].values

    # Shuffle and reassign
    shuffled_onsets = np.random.permutation(onset_times)
    events_randomized.loc[color_mask, 'onset'] = shuffled_onsets

    return events_randomized


def check_fir_convexity(fir_estimate):
    """
    Classify FIR shape: 'convex', 'linear_ramp', or 'random'

    Returns:
        shape_type: str
        convexity_score: float (0-2)
    """
    delays_idx = np.arange(len(fir_estimate))

    # Fit quadratic: check for negative curvature + peak at delays 2-5
    coeffs_quad = np.polyfit(delays_idx, fir_estimate, 2)
    a, b, c = coeffs_quad

    # Check curvature (negative = concave down = convex shape)
    has_negative_curvature = a < 0

    # Check peak location (should be at delays 2-5)
    peak_idx = np.argmax(fir_estimate)
    has_central_peak = 2 <= peak_idx <= 5

    # Fit linear: check R² > 0.7 for linear ramp (drift contamination)
    coeffs_lin = np.polyfit(delays_idx, fir_estimate, 1)
    fir_pred_lin = np.polyval(coeffs_lin, delays_idx)
    ss_res = np.sum((fir_estimate - fir_pred_lin) ** 2)
    ss_tot = np.sum((fir_estimate - np.mean(fir_estimate)) ** 2)
    r2_linear = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

    # Classify shape
    if has_negative_curvature and has_central_peak:
        shape_type = 'convex'
        convexity_score = 2.0
    elif r2_linear > 0.7:
        shape_type = 'linear_ramp'
        convexity_score = 0.0
    else:
        shape_type = 'random'
        convexity_score = 0.5

    return {
        'shape_type': shape_type,
        'convexity_score': convexity_score,
        'has_negative_curvature': bool(has_negative_curvature),
        'has_central_peak': bool(has_central_peak),
        'peak_idx': int(peak_idx),
        'r2_linear': float(r2_linear),
        'quadratic_a': float(a)
    }


def analyze_hrf_variability(voxel_hrfs, roi_hrf):
    """
    Analyze HRF variability across voxels

    (From run_C010_with_hrf_analysis.py lines 304-343)
    """
    n_voxels, n_timepoints = voxel_hrfs.shape

    # 1. Correlation with ROI mean
    hrf_correlations = np.zeros(n_voxels)
    for voxel_idx in range(n_voxels):
        r, _ = spearmanr(voxel_hrfs[voxel_idx], roi_hrf)
        hrf_correlations[voxel_idx] = r if np.isfinite(r) else 0.0

    # 2. RMSE from ROI mean
    hrf_rmse = np.sqrt(np.mean((voxel_hrfs - roi_hrf[None, :]) ** 2, axis=1))

    # 3. Per-timepoint variability
    hrf_std_per_timepoint = np.std(voxel_hrfs, axis=0)

    # 4. Find best and worst fitting voxels
    best_voxels = np.argsort(hrf_correlations)[-5:][::-1]  # Top 5
    worst_voxels = np.argsort(hrf_correlations)[:5]  # Bottom 5

    return {
        'hrf_correlations': hrf_correlations,
        'hrf_rmse': hrf_rmse,
        'hrf_std_per_timepoint': hrf_std_per_timepoint,
        'best_voxels': best_voxels,
        'worst_voxels': worst_voxels,
        'mean_correlation': np.mean(hrf_correlations),
        'median_correlation': np.median(hrf_correlations),
        'mean_rmse': np.mean(hrf_rmse),
        'median_rmse': np.median(hrf_rmse)
    }


def plot_hrf_variability(voxel_hrfs, roi_hrf, hrf_analysis, output_dir, roi_name, condition_name):
    """
    Generate HRF variability visualization (6-panel figure)

    (From run_C010_with_hrf_analysis.py lines 346-484)
    """
    fig = plt.figure(figsize=(20, 12))
    gs = fig.add_gridspec(2, 3, hspace=0.3, wspace=0.3)

    n_voxels = voxel_hrfs.shape[0]
    timepoints = FIR_DELAYS

    # Title
    fig.suptitle(f'{roi_name}: HRF Variability Analysis ({condition_name}) - ROI vs Individual Voxels',
                 fontsize=16, fontweight='bold')

    # 1. Individual Voxel HRFs (top-left)
    ax = fig.add_subplot(gs[0, 0])

    # Plot subset of individual voxels (100 random)
    n_show = min(100, n_voxels)
    np.random.seed(42)
    show_indices = np.random.choice(n_voxels, n_show, replace=False)

    for idx in show_indices:
        ax.plot(timepoints, voxel_hrfs[idx], color='gray', alpha=0.15, linewidth=0.5)

    # ROI mean HRF
    ax.plot(timepoints, roi_hrf, 'r-', linewidth=2.5, label='ROI Mean HRF', zorder=10)

    # ±1 SD
    hrf_std = hrf_analysis['hrf_std_per_timepoint']
    ax.fill_between(timepoints, roi_hrf - hrf_std, roi_hrf + hrf_std,
                    color='blue', alpha=0.3, label='±1 SD')

    ax.axhline(0, color='black', linestyle=':', linewidth=1, alpha=0.5)
    ax.set_xlabel('Time (seconds)', fontsize=11, fontweight='bold')
    ax.set_ylabel('Response Amplitude', fontsize=11, fontweight='bold')
    ax.set_title(f'Individual Voxel HRFs (n={n_show} shown)', fontsize=12, fontweight='bold')
    ax.legend(fontsize=9, loc='upper right')
    ax.grid(True, alpha=0.3)

    # 2. HRF Correlation Distribution (top-middle)
    ax = fig.add_subplot(gs[0, 1])

    hrf_corr = hrf_analysis['hrf_correlations']
    mean_corr = hrf_analysis['mean_correlation']
    median_corr = hrf_analysis['median_correlation']

    ax.hist(hrf_corr, bins=50, edgecolor='black', alpha=0.7, color='steelblue')
    ax.axvline(mean_corr, color='red', linestyle='--', linewidth=2,
               label=f'Mean = {mean_corr:.3f}')
    ax.axvline(median_corr, color='orange', linestyle='--', linewidth=2,
               label=f'Median = {median_corr:.3f}')

    ax.set_xlabel('Correlation with ROI HRF', fontsize=11, fontweight='bold')
    ax.set_ylabel('Number of voxels', fontsize=11, fontweight='bold')
    ax.set_title('HRF Correlation Distribution', fontsize=12, fontweight='bold')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # 3. HRF RMSE Distribution (top-right)
    ax = fig.add_subplot(gs[0, 2])

    hrf_rmse = hrf_analysis['hrf_rmse']
    mean_rmse = hrf_analysis['mean_rmse']

    ax.hist(hrf_rmse, bins=50, edgecolor='black', alpha=0.7, color='coral')
    ax.axvline(mean_rmse, color='red', linestyle='--', linewidth=2,
               label=f'Mean = {mean_rmse:.3f}')

    ax.set_xlabel('RMSE from ROI HRF', fontsize=11, fontweight='bold')
    ax.set_ylabel('Number of voxels', fontsize=11, fontweight='bold')
    ax.set_title('HRF RMSE Distribution', fontsize=12, fontweight='bold')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # 4. HRF Variability Per Timepoint (bottom-left)
    ax = fig.add_subplot(gs[1, 0])

    ax.errorbar(timepoints, roi_hrf, yerr=hrf_std, fmt='o-', color='steelblue',
                linewidth=2, markersize=6, capsize=5, capthick=2,
                label='ROI HRF', ecolor='steelblue', alpha=0.7)
    ax.plot(timepoints, roi_hrf, 'o-', color='red', linewidth=2, markersize=6,
            label='Mean ± SD', zorder=10)

    ax.axhline(0, color='black', linestyle=':', linewidth=1, alpha=0.5)
    ax.set_xlabel('Time (seconds)', fontsize=11, fontweight='bold')
    ax.set_ylabel('Response Amplitude', fontsize=11, fontweight='bold')
    ax.set_title('HRF Variability Per Timepoint', fontsize=12, fontweight='bold')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # 5. Best vs Worst Fitting Voxels (bottom-middle and bottom-right combined)
    ax = fig.add_subplot(gs[1, 1:])

    # Plot best fitting voxels (green)
    best_voxels = hrf_analysis['best_voxels']
    for idx, voxel_idx in enumerate(best_voxels):
        corr = hrf_corr[voxel_idx]
        ax.plot(timepoints, voxel_hrfs[voxel_idx], color='green', alpha=0.7,
                linewidth=2, label=f'Best: r = {corr:.3f}' if idx == 0 else '')

    # Plot worst fitting voxels (red)
    worst_voxels = hrf_analysis['worst_voxels']
    for idx, voxel_idx in enumerate(worst_voxels):
        corr = hrf_corr[voxel_idx]
        ax.plot(timepoints, voxel_hrfs[voxel_idx], color='red', alpha=0.7,
                linewidth=2, label=f'Worst: r = {corr:.3f}' if idx == 0 else '')

    # Plot ROI mean
    ax.plot(timepoints, roi_hrf, 'b-', linewidth=3, label='ROI HRF', zorder=10)

    ax.axhline(0, color='black', linestyle=':', linewidth=1, alpha=0.5)
    ax.set_xlabel('Time (seconds)', fontsize=11, fontweight='bold')
    ax.set_ylabel('Response Amplitude', fontsize=11, fontweight='bold')
    ax.set_title('Best (green) vs Worst (red) Fitting Voxels', fontsize=12, fontweight='bold')

    # Create legend text box
    best_corr = hrf_corr[best_voxels[0]]
    worst_corr = hrf_corr[worst_voxels[0]]
    legend_text = f'Best 5: r = {best_corr:.3f}\nWorst 5: r = {worst_corr:.3f}'
    ax.text(0.02, 0.98, legend_text,
            transform=ax.transAxes, ha='left', va='top',
            fontsize=10, family='monospace',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='wheat',
                     edgecolor='black', alpha=0.8))

    ax.grid(True, alpha=0.3)

    plt.savefig(output_dir / 'hrf_variability.png', dpi=300, bbox_inches='tight')
    plt.close()

    print(f"  ✓ Saved: hrf_variability.png")


# ============================================================================
# Main Pipeline
# ============================================================================

def estimate_fir_from_events(subject_id, roi_name, events_list):
    """
    Estimate FIR from provided events

    Args:
        events_list: List of events DataFrames (one per run)

    Returns:
        dict with voxel HRFs, ROI HRF, and HRF analysis
    """
    all_func_data = []
    all_design_matrices = []

    for run_idx in range(1, N_RUNS + 1):
        func_data, _ = load_bold_data(subject_id, roi_name, run_idx)
        events = events_list[run_idx - 1]

        n_scans = func_data.shape[0]

        X_fir = np.zeros((n_scans, len(FIR_DELAYS) * N_COLORS))

        for color_idx in range(N_COLORS):
            color_name = f'color_{color_idx + 1}'
            color_events = events[events['trial_type'] == color_name]

            for delay_idx, delay in enumerate(FIR_DELAYS):
                regressor_idx = color_idx * len(FIR_DELAYS) + delay_idx
                regressor = np.zeros(n_scans)

                for _, event in color_events.iterrows():
                    onset_tr = int(np.round(event['onset'] / TR))
                    target_tr = onset_tr + delay_idx

                    if 0 <= target_tr < n_scans:
                        regressor[target_tr] = 1.0

                X_fir[:, regressor_idx] = regressor

        all_func_data.append(func_data)
        all_design_matrices.append(X_fir)

    # Concatenate and estimate FIR
    Y_concat = np.vstack(all_func_data)
    X_concat = np.vstack(all_design_matrices)

    betas_fir = np.linalg.lstsq(X_concat, Y_concat, rcond=None)[0]

    # Extract individual voxel HRFs
    n_voxels = betas_fir.shape[1]
    voxel_hrfs = np.zeros((n_voxels, len(FIR_DELAYS)))

    for voxel_idx in range(n_voxels):
        voxel_fir = betas_fir[:, voxel_idx].reshape(N_COLORS, len(FIR_DELAYS))
        voxel_hrfs[voxel_idx] = voxel_fir.mean(axis=0)

    # ROI HRF (average across voxels)
    roi_hrf_fir = betas_fir.mean(axis=1).reshape(N_COLORS, len(FIR_DELAYS))
    roi_hrf = roi_hrf_fir.mean(axis=0)

    # HRF variability analysis
    hrf_analysis = analyze_hrf_variability(voxel_hrfs, roi_hrf)

    # FIR quality
    fir_quality = check_fir_convexity(roi_hrf)

    return {
        'roi_hrf': roi_hrf,
        'voxel_hrfs': voxel_hrfs,
        'hrf_analysis': hrf_analysis,
        'fir_quality': fir_quality
    }


def run_validation(subject_id, roi_name, n_seeds=5):
    """Run onset randomization validation"""

    print(f"\n{'='*80}")
    print(f"ONSET RANDOMIZATION VALIDATION: sub-{subject_id} {roi_name}")
    print(f"{'='*80}\n")

    # Create output directory
    output_dir = OUTPUT_DIR / f"sub-{subject_id}" / roi_name
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load original events
    print("Loading original events...")
    original_events = []
    for run_idx in range(1, N_RUNS + 1):
        _, events = load_bold_data(subject_id, roi_name, run_idx)
        original_events.append(events)

    # Estimate FIR with original onsets
    print("\nEstimating FIR with ORIGINAL onsets...")
    results_original = estimate_fir_from_events(subject_id, roi_name, original_events)

    print(f"  ✓ ROI HRF shape: {results_original['roi_hrf'].shape}")
    print(f"  ✓ FIR shape type: {results_original['fir_quality']['shape_type']}")
    print(f"  ✓ Convexity score: {results_original['fir_quality']['convexity_score']:.1f}/2.0")
    print(f"  ✓ HRF correlation (mean): {results_original['hrf_analysis']['mean_correlation']:.3f}")

    # Save original outputs
    dir_original = output_dir / "original"
    dir_original.mkdir(exist_ok=True)

    np.save(dir_original / 'roi_hrf.npy', results_original['roi_hrf'])
    np.save(dir_original / 'voxel_hrfs.npy', results_original['voxel_hrfs'])
    np.save(dir_original / 'hrf_correlations.npy', results_original['hrf_analysis']['hrf_correlations'])

    with open(dir_original / 'fir_quality.json', 'w') as f:
        json.dump(results_original['fir_quality'], f, indent=2)

    with open(dir_original / 'metrics.json', 'w') as f:
        json.dump({
            'hrf_mean_correlation': float(results_original['hrf_analysis']['mean_correlation']),
            'hrf_median_correlation': float(results_original['hrf_analysis']['median_correlation']),
            'hrf_mean_rmse': float(results_original['hrf_analysis']['mean_rmse'])
        }, f, indent=2)

    # Generate HRF variability plot
    plot_hrf_variability(results_original['voxel_hrfs'], results_original['roi_hrf'],
                        results_original['hrf_analysis'], dir_original, roi_name, 'Original')

    # Run randomizations
    randomized_results = []
    seeds = list(range(42, 42 + n_seeds))

    for seed in seeds:
        print(f"\nEstimating FIR with RANDOMIZED onsets (seed={seed})...")

        # Randomize onsets
        randomized_events = []
        for events in original_events:
            randomized = randomize_onsets(events, seed)
            randomized_events.append(randomized)

        # Estimate FIR
        results_random = estimate_fir_from_events(subject_id, roi_name, randomized_events)

        print(f"  ✓ FIR shape type: {results_random['fir_quality']['shape_type']}")
        print(f"  ✓ Convexity score: {results_random['fir_quality']['convexity_score']:.1f}/2.0")

        # Save outputs
        dir_random = output_dir / f"random_seed{seed}"
        dir_random.mkdir(exist_ok=True)

        np.save(dir_random / 'roi_hrf.npy', results_random['roi_hrf'])
        np.save(dir_random / 'voxel_hrfs.npy', results_random['voxel_hrfs'])
        np.save(dir_random / 'hrf_correlations.npy', results_random['hrf_analysis']['hrf_correlations'])

        with open(dir_random / 'fir_quality.json', 'w') as f:
            json.dump(results_random['fir_quality'], f, indent=2)

        with open(dir_random / 'metrics.json', 'w') as f:
            json.dump({
                'hrf_mean_correlation': float(results_random['hrf_analysis']['mean_correlation']),
                'hrf_median_correlation': float(results_random['hrf_analysis']['median_correlation']),
                'hrf_mean_rmse': float(results_random['hrf_analysis']['mean_rmse'])
            }, f, indent=2)

        # Generate HRF variability plot
        plot_hrf_variability(results_random['voxel_hrfs'], results_random['roi_hrf'],
                            results_random['hrf_analysis'], dir_random, roi_name, f'Random seed{seed}')

        randomized_results.append(results_random)

    # Generate comparison plot
    print(f"\nGenerating comparison plot...")
    plot_onset_validation(results_original, randomized_results, seeds, output_dir, roi_name)

    # Save validation summary
    orig_mean_corr = results_original['hrf_analysis']['mean_correlation']
    random_mean_corrs = [r['hrf_analysis']['mean_correlation'] for r in randomized_results]
    corr_drop = orig_mean_corr - np.mean(random_mean_corrs)

    validation_summary = {
        'original': {
            'shape_type': results_original['fir_quality']['shape_type'],
            'convexity_score': float(results_original['fir_quality']['convexity_score']),
            'has_negative_curvature': results_original['fir_quality']['has_negative_curvature'],
            'has_central_peak': results_original['fir_quality']['has_central_peak'],
            'peak_idx': results_original['fir_quality']['peak_idx'],
            'hrf_mean_correlation': float(orig_mean_corr),
            'hrf_median_correlation': float(results_original['hrf_analysis']['median_correlation'])
        },
        'randomized': []
    }

    for seed, result in zip(seeds, randomized_results):
        validation_summary['randomized'].append({
            'seed': seed,
            'shape_type': result['fir_quality']['shape_type'],
            'convexity_score': float(result['fir_quality']['convexity_score']),
            'has_negative_curvature': result['fir_quality']['has_negative_curvature'],
            'has_central_peak': result['fir_quality']['has_central_peak'],
            'peak_idx': result['fir_quality']['peak_idx'],
            'hrf_mean_correlation': float(result['hrf_analysis']['mean_correlation']),
            'hrf_median_correlation': float(result['hrf_analysis']['median_correlation'])
        })

    # Count shape types
    shape_counts = {'convex': 0, 'linear_ramp': 0, 'random': 0}
    for result in randomized_results:
        shape_type = result['fir_quality']['shape_type']
        shape_counts[shape_type] += 1

    validation_summary['shape_distribution'] = shape_counts
    validation_summary['hrf_correlation_analysis'] = {
        'original_mean': float(orig_mean_corr),
        'randomized_mean': float(np.mean(random_mean_corrs)),
        'randomized_std': float(np.std(random_mean_corrs)),
        'correlation_drop': float(corr_drop),
        'is_robust': bool(corr_drop > 0.5)
    }

    with open(output_dir / 'onset_validation.json', 'w') as f:
        json.dump(validation_summary, f, indent=2)

    print(f"\n✓ All outputs saved to: {output_dir}")
    print(f"\n{'='*80}")
    print(f"VALIDATION COMPLETE: sub-{subject_id} {roi_name}")
    print(f"{'='*80}\n")

    return validation_summary


def plot_onset_validation(results_original, randomized_results, seeds, output_dir, roi_name):
    """
    Generate onset validation visualization (2×3 grid figure)

    KEY VALIDATION: HRF correlation should drop from high (original) to low (randomized)
    if the high correlations are due to real temporal structure, not drift.
    """
    fig = plt.figure(figsize=(20, 12))
    gs = fig.add_gridspec(2, 3, hspace=0.35, wspace=0.3)

    fig.suptitle(f'{roi_name}: Onset Randomization Validation (Original vs Randomized)',
                 fontsize=16, fontweight='bold')

    timepoints = FIR_DELAYS

    # 1. FIR comparison (top-left, larger)
    ax = fig.add_subplot(gs[0, 0])

    # Plot randomized FIRs (gray, thin)
    for seed, result in zip(seeds, randomized_results):
        ax.plot(timepoints, result['roi_hrf'], color='gray', alpha=0.4,
                linewidth=1.5, label='Randomized' if seed == seeds[0] else '')

    # Plot original FIR (red, thick)
    ax.plot(timepoints, results_original['roi_hrf'], 'r-', linewidth=3.5,
            marker='o', markersize=8, label='Original', zorder=10)

    ax.axhline(0, color='black', linestyle=':', linewidth=1, alpha=0.5)
    ax.set_xlabel('Time (seconds)', fontsize=11, fontweight='bold')
    ax.set_ylabel('Response Amplitude', fontsize=11, fontweight='bold')
    ax.set_title(f'ROI HRF: Original vs {len(seeds)} Randomizations', fontsize=12, fontweight='bold')
    ax.legend(fontsize=10, loc='upper right')
    ax.grid(True, alpha=0.3)

    # Add text box with original FIR quality
    orig_quality = results_original['fir_quality']
    info_text = f"Original:\n  Shape: {orig_quality['shape_type']}\n  Score: {orig_quality['convexity_score']:.1f}/2.0"
    ax.text(0.02, 0.02, info_text,
            transform=ax.transAxes, ha='left', va='bottom',
            fontsize=9, family='monospace',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='lightcoral',
                     edgecolor='black', alpha=0.9))

    # 2. HRF Correlation Distributions (top-middle) - KEY VALIDATION METRIC
    ax = fig.add_subplot(gs[0, 1])

    # Get HRF correlations
    orig_corr = results_original['hrf_analysis']['hrf_correlations']
    random_corrs_all = np.concatenate([r['hrf_analysis']['hrf_correlations'] for r in randomized_results])

    # Plot histograms
    ax.hist(orig_corr, bins=50, alpha=0.7, color='red', edgecolor='black',
            label=f"Original (μ={np.mean(orig_corr):.3f})", density=True)
    ax.hist(random_corrs_all, bins=50, alpha=0.6, color='gray', edgecolor='black',
            label=f"Randomized (μ={np.mean(random_corrs_all):.3f})", density=True)

    ax.axvline(np.mean(orig_corr), color='red', linestyle='--', linewidth=2, alpha=0.8)
    ax.axvline(np.mean(random_corrs_all), color='gray', linestyle='--', linewidth=2, alpha=0.8)

    ax.set_xlabel('Voxel-ROI HRF Correlation', fontsize=11, fontweight='bold')
    ax.set_ylabel('Density', fontsize=11, fontweight='bold')
    ax.set_title('HRF Correlation: Original vs Randomized', fontsize=12, fontweight='bold')
    ax.legend(fontsize=9, loc='upper left')
    ax.grid(True, alpha=0.3)

    # Add validation text
    corr_drop = np.mean(orig_corr) - np.mean(random_corrs_all)
    validation_text = f"Correlation drop: {corr_drop:.3f}\n"
    if corr_drop > 0.5:
        validation_text += "✓ ROBUST: High → Low"
    elif corr_drop < 0.1:
        validation_text += "⚠ WARNING: No drop!"
    else:
        validation_text += "? Moderate drop"

    ax.text(0.98, 0.98, validation_text,
            transform=ax.transAxes, ha='right', va='top',
            fontsize=9, family='monospace',
            bbox=dict(boxstyle='round,pad=0.5',
                     facecolor='lightgreen' if corr_drop > 0.5 else 'yellow',
                     edgecolor='black', alpha=0.9))

    # 3. HRF Correlation Boxplot (top-right) - Quantitative comparison
    ax = fig.add_subplot(gs[0, 2])

    # Collect mean correlations per condition
    random_mean_corrs = [r['hrf_analysis']['mean_correlation'] for r in randomized_results]
    orig_mean_corr = results_original['hrf_analysis']['mean_correlation']

    # Boxplot
    bp = ax.boxplot([random_mean_corrs], positions=[1], widths=0.6,
                    patch_artist=True, showmeans=True,
                    boxprops=dict(facecolor='lightgray', alpha=0.7, edgecolor='black', linewidth=1.5),
                    medianprops=dict(color='darkgray', linewidth=2),
                    meanprops=dict(marker='D', markerfacecolor='gray', markeredgecolor='black', markersize=8))

    # Plot original as separate point
    ax.plot(0.5, orig_mean_corr, 'ro', markersize=14, label='Original', zorder=10)

    ax.set_xticks([0.5, 1])
    ax.set_xticklabels(['Original', 'Randomized\n(n=5)'])
    ax.set_ylabel('Mean HRF Correlation', fontsize=11, fontweight='bold')
    ax.set_title('Mean Voxel-ROI HRF Correlation', fontsize=12, fontweight='bold')
    ax.set_ylim([-0.1, 1.0])
    ax.grid(True, alpha=0.3, axis='y')
    ax.legend(fontsize=9)

    # Add values
    summary_text = f"Original: {orig_mean_corr:.3f}\n" \
                   f"Random: {np.mean(random_mean_corrs):.3f} ± {np.std(random_mean_corrs):.3f}\n" \
                   f"Drop: {corr_drop:.3f}"
    ax.text(0.02, 0.98, summary_text,
            transform=ax.transAxes, ha='left', va='top',
            fontsize=9, family='monospace',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='wheat',
                     edgecolor='black', alpha=0.8))

    # 4. Shape classification distribution (bottom-left)
    ax = fig.add_subplot(gs[1, 0])

    # Count shape types
    shape_counts = {'convex': 0, 'linear_ramp': 0, 'random': 0}
    for result in randomized_results:
        shape_type = result['fir_quality']['shape_type']
        shape_counts[shape_type] += 1

    # Add original shape
    orig_shape = results_original['fir_quality']['shape_type']

    labels = ['Convex', 'Linear Ramp', 'Random']
    counts = [shape_counts['convex'], shape_counts['linear_ramp'], shape_counts['random']]
    colors = ['green', 'orange', 'steelblue']

    bars = ax.bar(labels, counts, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
    ax.set_ylabel('Count (out of 5 randomizations)', fontsize=11, fontweight='bold')
    ax.set_title('FIR Shape Distribution (Randomized)', fontsize=12, fontweight='bold')
    ax.set_ylim([0, max(counts) + 1])
    ax.grid(True, alpha=0.3, axis='y')

    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        if height > 0:
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{int(height)}', ha='center', va='bottom',
                    fontsize=11, fontweight='bold')

    # Add text box with original shape
    ax.text(0.98, 0.98, f'Original: {orig_shape}',
            transform=ax.transAxes, ha='right', va='top',
            fontsize=9, family='monospace',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='lightcoral',
                     edgecolor='black', alpha=0.9))

    # 5. Convexity score comparison (bottom-middle)
    ax = fig.add_subplot(gs[1, 1])

    # Collect convexity scores
    random_scores = [result['fir_quality']['convexity_score'] for result in randomized_results]
    orig_score = results_original['fir_quality']['convexity_score']

    # Boxplot of randomized scores
    bp = ax.boxplot([random_scores], positions=[1], widths=0.6,
                    patch_artist=True, showmeans=True,
                    boxprops=dict(facecolor='lightblue', alpha=0.7, edgecolor='black', linewidth=1.5),
                    medianprops=dict(color='red', linewidth=2),
                    meanprops=dict(marker='D', markerfacecolor='green', markeredgecolor='black', markersize=8))

    # Plot original score as separate point
    ax.plot(0.5, orig_score, 'ro', markersize=12, label='Original', zorder=10)

    ax.set_xticks([0.5, 1])
    ax.set_xticklabels(['Original', 'Randomized\n(n=5)'])
    ax.set_ylabel('Convexity Score (0-2)', fontsize=11, fontweight='bold')
    ax.set_title('FIR Convexity Score Comparison', fontsize=12, fontweight='bold')
    ax.set_ylim([-0.2, 2.2])
    ax.grid(True, alpha=0.3, axis='y')
    ax.legend(fontsize=10)

    # Add summary text
    summary_text = f"Original: {orig_score:.1f}\n" \
                   f"Random: {np.mean(random_scores):.1f} ± {np.std(random_scores):.1f}"
    ax.text(0.02, 0.98, summary_text,
            transform=ax.transAxes, ha='left', va='top',
            fontsize=9, family='monospace',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='wheat',
                     edgecolor='black', alpha=0.8))

    # 6. Validation Summary (bottom-right)
    ax = fig.add_subplot(gs[1, 2])
    ax.axis('off')

    # Calculate key validation metrics
    orig_mean_corr = results_original['hrf_analysis']['mean_correlation']
    random_mean_corrs = [r['hrf_analysis']['mean_correlation'] for r in randomized_results]
    corr_drop = orig_mean_corr - np.mean(random_mean_corrs)

    # Determine validation status
    hrf_robust = corr_drop > 0.5
    fir_robust = orig_quality['shape_type'] == 'convex' and np.mean(random_scores) < 1.0

    # Create summary text
    summary_lines = [
        "VALIDATION SUMMARY",
        "=" * 40,
        "",
        "KEY METRICS:",
        f"  HRF Correlation Drop: {corr_drop:.3f}",
        f"    Original: {orig_mean_corr:.3f}",
        f"    Randomized: {np.mean(random_mean_corrs):.3f}",
        "",
        f"  FIR Shape:",
        f"    Original: {orig_quality['shape_type']}",
        f"    Random: {np.mean(random_scores):.2f} (convexity)",
        "",
        "VALIDATION RESULTS:",
        ""
    ]

    if hrf_robust and fir_robust:
        summary_lines.extend([
            "  ✓ ROBUST FIR ESTIMATION",
            "    • High HRF correlation destroyed",
            "    • Convex shape destroyed",
            "    • Temporal structure is REAL",
            "",
            "  CONCLUSION: No drift contamination"
        ])
        bg_color = 'lightgreen'
    elif not hrf_robust and corr_drop < 0.1:
        summary_lines.extend([
            "  ⚠ WARNING: DRIFT CONTAMINATION",
            "    • HRF correlation persists",
            "    • High corr even after shuffle",
            "",
            "  CONCLUSION: Investigate drift removal"
        ])
        bg_color = 'lightyellow'
    else:
        summary_lines.extend([
            "  ? MIXED RESULTS",
            "    • Partial correlation drop",
            "    • Unclear validation",
            "",
            "  CONCLUSION: Review individual metrics"
        ])
        bg_color = 'lightblue'

    summary_text_full = '\n'.join(summary_lines)

    ax.text(0.5, 0.5, summary_text_full,
            transform=ax.transAxes, ha='center', va='center',
            fontsize=9, family='monospace',
            bbox=dict(boxstyle='round,pad=1.0', facecolor=bg_color,
                     edgecolor='black', linewidth=2, alpha=0.9))

    ax.set_title('Interpretation', fontsize=12, fontweight='bold', pad=20)

    plt.savefig(output_dir / 'onset_validation.png', dpi=300, bbox_inches='tight')
    plt.close()

    print(f"  ✓ Saved: onset_validation.png")


def main():
    parser = argparse.ArgumentParser(description='Onset Randomization Validation')
    parser.add_argument('--subject', required=True, help='Subject ID (e.g., 01)')
    parser.add_argument('--roi', required=True, choices=['V1', 'V2'], help='ROI name')
    parser.add_argument('--n-seeds', type=int, default=5, help='Number of randomization seeds (default: 5)')

    args = parser.parse_args()

    try:
        validation_summary = run_validation(args.subject, args.roi, args.n_seeds)

        # Print summary
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)

        # HRF Correlation Analysis (KEY METRIC)
        print(f"\n╔══ HRF CORRELATION ANALYSIS (KEY VALIDATION) ══╗")
        hrf_corr = validation_summary['hrf_correlation_analysis']
        print(f"  Original HRF correlation:    {hrf_corr['original_mean']:.3f}")
        print(f"  Randomized HRF correlation:  {hrf_corr['randomized_mean']:.3f} ± {hrf_corr['randomized_std']:.3f}")
        print(f"  Correlation drop:            {hrf_corr['correlation_drop']:.3f}")
        print(f"  ")
        if hrf_corr['is_robust']:
            print(f"  ✓ ROBUST: High correlation destroyed by randomization")
            print(f"    → HRF correlations are due to REAL temporal structure")
        else:
            print(f"  ⚠ WARNING: HRF correlation persists after randomization")
            print(f"    → Possible drift contamination")
        print(f"╚══════════════════════════════════════════════╝")

        print(f"\nOriginal FIR:")
        print(f"  Shape type: {validation_summary['original']['shape_type']}")
        print(f"  Convexity score: {validation_summary['original']['convexity_score']:.1f}/2.0")
        print(f"  HRF correlation: {validation_summary['original']['hrf_mean_correlation']:.3f}")

        print(f"\nRandomized FIRs (n={args.n_seeds}):")
        print(f"  Shape distribution:")
        print(f"    Convex: {validation_summary['shape_distribution']['convex']}")
        print(f"    Linear ramp: {validation_summary['shape_distribution']['linear_ramp']}")
        print(f"    Random/flat: {validation_summary['shape_distribution']['random']}")
        print(f"  HRF correlation: {hrf_corr['randomized_mean']:.3f} ± {hrf_corr['randomized_std']:.3f}")

        # Overall Interpretation
        print(f"\n" + "="*80)
        print("OVERALL INTERPRETATION")
        print("="*80)

        fir_robust = (validation_summary['original']['shape_type'] == 'convex' and
                     validation_summary['shape_distribution']['convex'] == 0)
        hrf_robust = hrf_corr['is_robust']

        if hrf_robust and fir_robust:
            print("  ✓✓ VALIDATION PASSED")
            print("     • HRF correlations destroyed by randomization")
            print("     • Convex FIR shape destroyed by randomization")
            print("     • CONCLUSION: No drift contamination detected")
            print("     • Current pipeline (C010) is validated ✓")
        elif not hrf_robust:
            print("  ⚠⚠ VALIDATION FAILED")
            print("     • HRF correlations persist after randomization")
            print("     • CONCLUSION: Drift contamination likely present")
            print("     • ACTION: Investigate drift removal methodology")
        else:
            print("  ? MIXED RESULTS")
            print("     • HRF correlations destroyed (GOOD)")
            print("     • FIR shape results unclear")
            print("     • CONCLUSION: Review individual metrics")

        sys.exit(0)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
