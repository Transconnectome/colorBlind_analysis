#!/usr/bin/env python3
"""
Drift Removal Validation Script

Compare 1st+2nd order drift (quadratic+linear+constant) vs 2nd-only drift (linear+constant)
to determine if adding quadratic drift improves HRF estimation quality.

Test subjects: sub-01, V1 and V2

Key metrics:
- HRF voxel correlation (mean, median)
- FIR convexity score (0-2 scale)
- RDM reliability: raw (odd/even split-half)
- RDM reliability: Procrustes aligned
- Procrustes disparity

Author: Claude Code
Date: 2026-02-16
"""

import numpy as np
import pandas as pd
import nibabel as nib
from pathlib import Path
from scipy.stats import spearmanr
from scipy.linalg import orthogonal_procrustes
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
OUTPUT_DIR = BASE_DIR / "derivatives" / "drift_validation"

# Pipeline settings
TR = 1.5
N_SCANS = 288
N_RUNS = 6
N_COLORS = 8
FIR_DELAYS = np.arange(8) * TR

print(f"Drift Removal Validation")
print(f"  Test: 1st+2nd drift vs 2nd-only drift")
print(f"  Subjects: sub-01 only")
print(f"  ROIs: V1, V2")
print()


# ============================================================================
# Utility Functions (from run_C010_with_hrf_analysis.py)
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


# ============================================================================
# Drift Regressor Functions (KEY COMPARISON)
# ============================================================================

def create_drift_regressors_2nd_only(n_scans, run_idx, n_runs):
    """
    Current method: linear + constant per run (2nd order only)

    From run_C010_with_hrf_analysis.py lines 107-112
    """
    drift_cols = np.zeros((n_scans, n_runs * 2))
    drift_cols[:, run_idx - 1] = np.linspace(-0.5, 0.5, n_scans)  # Linear
    drift_cols[:, n_runs + run_idx - 1] = 1.0                      # Constant
    return drift_cols


def create_drift_regressors_1st_2nd(n_scans, run_idx, n_runs):
    """
    Test method: quadratic + linear + constant per run (1st+2nd order)

    Centered quadratic to reduce collinearity with linear drift
    """
    drift_cols = np.zeros((n_scans, n_runs * 3))
    t = np.linspace(-0.5, 0.5, n_scans)

    # Quadratic (centered to reduce collinearity)
    t_squared = t ** 2
    drift_cols[:, run_idx - 1] = t_squared - np.mean(t_squared)

    # Linear
    drift_cols[:, n_runs + run_idx - 1] = t

    # Constant
    drift_cols[:, 2 * n_runs + run_idx - 1] = 1.0

    return drift_cols


# ============================================================================
# Pipeline Functions
# ============================================================================

def convolve_hrf_with_events(events, n_scans, tr, hrf, hrf_deriv):
    """Convolve HRF with event onsets"""
    frame_times = np.arange(n_scans) * tr
    X_hrf = np.zeros((n_scans, N_COLORS * 2))

    for color_idx in range(N_COLORS):
        color_name = f'color_{color_idx + 1}'
        color_events = events[events['trial_type'] == color_name]

        if len(color_events) == 0:
            continue

        for _, event in color_events.iterrows():
            onset = event['onset']
            hrf_signal = np.interp(frame_times - onset, np.arange(len(hrf)) * tr, hrf, left=0, right=0)
            X_hrf[:, color_idx] += hrf_signal

            deriv_signal = np.interp(frame_times - onset, np.arange(len(hrf_deriv)) * tr, hrf_deriv, left=0, right=0)
            X_hrf[:, N_COLORS + color_idx] += deriv_signal

    return X_hrf


def build_2nd_level_design_matrix(events, n_scans, tr, hrf, hrf_deriv, run_idx, n_runs, drift_method='2nd_only'):
    """
    Build 2nd-level design matrix with specified drift method

    Args:
        drift_method: '2nd_only' or '1st_2nd'
    """
    X_components = []

    X_hrf = convolve_hrf_with_events(events, n_scans, tr, hrf, hrf_deriv)
    X_components.append(X_hrf[:, :N_COLORS])
    X_components.append(X_hrf[:, N_COLORS:])

    # Apply drift removal based on method
    if drift_method == '2nd_only':
        drift_cols = create_drift_regressors_2nd_only(n_scans, run_idx, n_runs)
    elif drift_method == '1st_2nd':
        drift_cols = create_drift_regressors_1st_2nd(n_scans, run_idx, n_runs)
    else:
        raise ValueError(f"Unknown drift method: {drift_method}")

    X_components.append(drift_cols)

    X = np.hstack(X_components)
    return X


def compute_split_half_odd_even(amplitudes):
    """Compute odd/even split-half reliability"""
    n_runs, n_colors, n_voxels = amplitudes.shape

    if n_runs < 4:
        return {'corrected': np.nan, 'raw': np.nan}

    odd_indices = np.arange(0, n_runs, 2)
    even_indices = np.arange(1, n_runs, 2)

    odd_patterns = amplitudes[odd_indices].mean(axis=0)
    even_patterns = amplitudes[even_indices].mean(axis=0)

    rdm_odd = 1 - np.corrcoef(odd_patterns)
    rdm_even = 1 - np.corrcoef(even_patterns)

    mask = np.triu(np.ones_like(rdm_odd, dtype=bool), k=1)
    rdm_odd_vec = rdm_odd[mask]
    rdm_even_vec = rdm_even[mask]

    r_half, _ = spearmanr(rdm_odd_vec, rdm_even_vec)
    r_corrected = 2 * r_half / (1 + r_half) if r_half < 1 else 1.0

    return {'corrected': r_corrected, 'raw': r_half}


def apply_procrustes_alignment(amplitudes_raw):
    """Apply Procrustes alignment"""
    n_runs, n_colors, n_voxels = amplitudes_raw.shape

    reference = amplitudes_raw[0]
    aligned = np.zeros_like(amplitudes_raw)
    aligned[0] = reference

    disparities = np.zeros(n_runs)

    for run_idx in range(1, n_runs):
        target = amplitudes_raw[run_idx]
        R, scale = orthogonal_procrustes(target.T, reference.T)
        aligned_run = (target.T @ R).T
        disparity = np.sum((aligned_run - reference) ** 2) / n_voxels
        disparities[run_idx] = disparity
        aligned[run_idx] = aligned_run

    return aligned, disparities


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


def plot_hrf_variability(voxel_hrfs, roi_hrf, hrf_analysis, output_dir, roi_name, drift_method):
    """
    Generate HRF variability visualization (6-panel figure)

    (From run_C010_with_hrf_analysis.py lines 346-484)
    """
    fig = plt.figure(figsize=(20, 12))
    gs = fig.add_gridspec(2, 3, hspace=0.3, wspace=0.3)

    n_voxels = voxel_hrfs.shape[0]
    timepoints = FIR_DELAYS

    # Title
    fig.suptitle(f'{roi_name}: HRF Variability Analysis ({drift_method}) - ROI vs Individual Voxels',
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


def compute_fir_convexity(roi_hrf):
    """
    Compute FIR convexity score (0-2)

    Score breakdown:
    - 1.0 if negative curvature (concave down)
    - 1.0 if peak is at delays 2-5 (3-7.5 seconds)

    Returns:
        convexity_score: float (0-2)
    """
    # Fit quadratic
    delays_idx = np.arange(len(roi_hrf))
    coeffs = np.polyfit(delays_idx, roi_hrf, 2)
    a, b, c = coeffs

    # Check curvature (negative = concave down = convex shape)
    has_negative_curvature = a < 0

    # Check peak location (should be at delays 2-5)
    peak_idx = np.argmax(roi_hrf)
    has_central_peak = 2 <= peak_idx <= 5

    convexity_score = 0.0
    if has_negative_curvature:
        convexity_score += 1.0
    if has_central_peak:
        convexity_score += 1.0

    return {
        'convexity_score': convexity_score,
        'has_negative_curvature': bool(has_negative_curvature),
        'has_central_peak': bool(has_central_peak),
        'peak_idx': int(peak_idx),
        'quadratic_a': float(a)
    }


# ============================================================================
# Main Pipeline
# ============================================================================

def run_single_method(subject_id, roi_name, drift_method):
    """
    Run pipeline with specified drift method

    Args:
        drift_method: '2nd_only' or '1st_2nd'

    Returns:
        dict with all results
    """
    print(f"\n{'='*80}")
    print(f"Running: sub-{subject_id} {roi_name} ({drift_method})")
    print(f"{'='*80}\n")

    # Step 1: 1st-level HRF estimation (SAME for both methods)
    print("Step 1: 1st-level HRF estimation (no drift)...")

    all_func_data = []
    all_design_matrices = []

    for run_idx in range(1, N_RUNS + 1):
        print(f"  Run {run_idx}...")
        func_data, events = load_bold_data(subject_id, roi_name, run_idx)
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
    roi_hrf_deriv = np.gradient(roi_hrf)

    print(f"  ✓ ROI HRF estimated: shape {roi_hrf.shape}")
    print(f"  ✓ Individual voxel HRFs: shape {voxel_hrfs.shape}")

    # Step 2: 2nd-level amplitude estimation (DIFFERENT for each method)
    print(f"\nStep 2: 2nd-level amplitude estimation ({drift_method})...")

    amplitudes_raw = []

    for run_idx in range(1, N_RUNS + 1):
        print(f"  Run {run_idx}...")
        func_data, events = load_bold_data(subject_id, roi_name, run_idx)
        n_scans = func_data.shape[0]

        X = build_2nd_level_design_matrix(
            events, n_scans, TR, roi_hrf, roi_hrf_deriv,
            run_idx, N_RUNS, drift_method=drift_method
        )

        print(f"    Design matrix: {X.shape}")

        betas, _, _, _ = np.linalg.lstsq(X, func_data, rcond=None)
        amplitudes = betas[:N_COLORS, :]
        amplitudes_raw.append(amplitudes)

    amplitudes_raw = np.array(amplitudes_raw)
    print(f"\n✓ Amplitudes computed: {amplitudes_raw.shape}")

    # Step 3: Procrustes alignment
    print("\nStep 3: Procrustes alignment...")
    amplitudes_proc, disparities = apply_procrustes_alignment(amplitudes_raw)
    print(f"  ✓ Mean disparity: {disparities.mean():.6f}")

    # Step 4: Compute metrics
    print("\nStep 4: Computing metrics...")

    # RDM reliability (odd/even split-half)
    rdm_raw = compute_split_half_odd_even(amplitudes_raw)
    rdm_proc = compute_split_half_odd_even(amplitudes_proc)

    # FIR convexity
    fir_quality = compute_fir_convexity(roi_hrf)

    # HRF variability
    hrf_analysis = analyze_hrf_variability(voxel_hrfs, roi_hrf)

    print(f"\n  RDM Reliability (raw): {rdm_raw['raw']:.4f}")
    print(f"  RDM Reliability (Procrustes): {rdm_proc['raw']:.4f}")
    print(f"  Procrustes disparity: {disparities.mean():.6f}")
    print(f"  FIR convexity score: {fir_quality['convexity_score']:.1f}/2.0")
    print(f"  HRF correlation (mean): {hrf_analysis['mean_correlation']:.3f}")

    return {
        'roi_hrf': roi_hrf,
        'roi_hrf_deriv': roi_hrf_deriv,
        'voxel_hrfs': voxel_hrfs,
        'amplitudes_raw': amplitudes_raw,
        'amplitudes_procrustes': amplitudes_proc,
        'procrustes_disparities': disparities,
        'hrf_analysis': hrf_analysis,
        'fir_quality': fir_quality,
        'metrics': {
            'rdm_reliability_raw': float(rdm_raw['raw']),
            'rdm_reliability_procrustes': float(rdm_proc['raw']),
            'procrustes_disparity': float(disparities.mean()),
            'fir_convexity_score': float(fir_quality['convexity_score']),
            'hrf_mean_correlation': float(hrf_analysis['mean_correlation']),
            'hrf_median_correlation': float(hrf_analysis['median_correlation']),
            'hrf_mean_rmse': float(hrf_analysis['mean_rmse']),
            'hrf_median_rmse': float(hrf_analysis['median_rmse'])
        }
    }


def plot_drift_comparison(results_2nd, results_1st2nd, output_dir, roi_name):
    """
    Generate drift comparison visualization (2×3 panel figure)
    """
    fig = plt.figure(figsize=(18, 12))
    gs = fig.add_gridspec(2, 3, hspace=0.35, wspace=0.3)

    fig.suptitle(f'{roi_name}: Drift Method Comparison (2nd-only vs 1st+2nd)',
                 fontsize=16, fontweight='bold')

    timepoints = FIR_DELAYS

    # 1. HRF shape comparison (top-left)
    ax = fig.add_subplot(gs[0, 0])
    ax.plot(timepoints, results_2nd['roi_hrf'], 'b-', linewidth=2.5,
            marker='o', markersize=6, label='2nd-only (current)')
    ax.plot(timepoints, results_1st2nd['roi_hrf'], 'r--', linewidth=2.5,
            marker='s', markersize=6, label='1st+2nd (test)')
    ax.axhline(0, color='black', linestyle=':', linewidth=1, alpha=0.5)
    ax.set_xlabel('Time (seconds)', fontsize=11, fontweight='bold')
    ax.set_ylabel('Response Amplitude', fontsize=11, fontweight='bold')
    ax.set_title('ROI HRF Shape Comparison', fontsize=12, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    # 2. HRF correlation distributions (top-middle)
    ax = fig.add_subplot(gs[0, 1])
    corr_2nd = results_2nd['hrf_analysis']['hrf_correlations']
    corr_1st2nd = results_1st2nd['hrf_analysis']['hrf_correlations']

    ax.hist(corr_2nd, bins=50, alpha=0.6, color='blue', edgecolor='black',
            label=f"2nd-only (μ={np.mean(corr_2nd):.3f})")
    ax.hist(corr_1st2nd, bins=50, alpha=0.6, color='red', edgecolor='black',
            label=f"1st+2nd (μ={np.mean(corr_1st2nd):.3f})")

    ax.set_xlabel('HRF Correlation with ROI', fontsize=11, fontweight='bold')
    ax.set_ylabel('Number of voxels', fontsize=11, fontweight='bold')
    ax.set_title('HRF Correlation Distribution', fontsize=12, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    # 3. FIR convexity comparison (top-right)
    ax = fig.add_subplot(gs[0, 2])
    convex_2nd = results_2nd['fir_quality']['convexity_score']
    convex_1st2nd = results_1st2nd['fir_quality']['convexity_score']

    bars = ax.bar(['2nd-only', '1st+2nd'], [convex_2nd, convex_1st2nd],
                  color=['blue', 'red'], alpha=0.7, edgecolor='black')
    ax.set_ylabel('Convexity Score (0-2)', fontsize=11, fontweight='bold')
    ax.set_title('FIR Convexity Score', fontsize=12, fontweight='bold')
    ax.set_ylim([0, 2.2])
    ax.grid(True, alpha=0.3, axis='y')

    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                f'{height:.1f}', ha='center', va='bottom', fontsize=11, fontweight='bold')

    # 4. RDM reliability comparison (bottom-left)
    ax = fig.add_subplot(gs[1, 0])

    methods = ['2nd-only', '1st+2nd']
    raw_vals = [results_2nd['metrics']['rdm_reliability_raw'],
                results_1st2nd['metrics']['rdm_reliability_raw']]
    proc_vals = [results_2nd['metrics']['rdm_reliability_procrustes'],
                 results_1st2nd['metrics']['rdm_reliability_procrustes']]

    x = np.arange(len(methods))
    width = 0.35

    ax.bar(x - width/2, raw_vals, width, label='Raw', color='steelblue',
           alpha=0.7, edgecolor='black')
    ax.bar(x + width/2, proc_vals, width, label='Procrustes', color='coral',
           alpha=0.7, edgecolor='black')

    ax.set_ylabel('RDM Reliability (Spearman r)', fontsize=11, fontweight='bold')
    ax.set_title('RDM Reliability Comparison', fontsize=12, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(methods)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3, axis='y')

    # 5. Procrustes disparity comparison (bottom-middle)
    ax = fig.add_subplot(gs[1, 1])
    disp_2nd = results_2nd['metrics']['procrustes_disparity']
    disp_1st2nd = results_1st2nd['metrics']['procrustes_disparity']

    bars = ax.bar(['2nd-only', '1st+2nd'], [disp_2nd, disp_1st2nd],
                  color=['blue', 'red'], alpha=0.7, edgecolor='black')
    ax.set_ylabel('Disparity (lower = better)', fontsize=11, fontweight='bold')
    ax.set_title('Procrustes Disparity', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')

    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + height*0.02,
                f'{height:.4f}', ha='center', va='bottom', fontsize=10)

    # 6. Summary metrics table (bottom-right)
    ax = fig.add_subplot(gs[1, 2])
    ax.axis('off')

    table_data = [
        ['Metric', '2nd-only', '1st+2nd', 'Δ'],
        ['HRF corr (mean)',
         f"{results_2nd['metrics']['hrf_mean_correlation']:.3f}",
         f"{results_1st2nd['metrics']['hrf_mean_correlation']:.3f}",
         f"{results_1st2nd['metrics']['hrf_mean_correlation'] - results_2nd['metrics']['hrf_mean_correlation']:+.3f}"],
        ['RDM rel (raw)',
         f"{results_2nd['metrics']['rdm_reliability_raw']:.3f}",
         f"{results_1st2nd['metrics']['rdm_reliability_raw']:.3f}",
         f"{results_1st2nd['metrics']['rdm_reliability_raw'] - results_2nd['metrics']['rdm_reliability_raw']:+.3f}"],
        ['RDM rel (Proc)',
         f"{results_2nd['metrics']['rdm_reliability_procrustes']:.3f}",
         f"{results_1st2nd['metrics']['rdm_reliability_procrustes']:.3f}",
         f"{results_1st2nd['metrics']['rdm_reliability_procrustes'] - results_2nd['metrics']['rdm_reliability_procrustes']:+.3f}"],
        ['Proc disparity',
         f"{results_2nd['metrics']['procrustes_disparity']:.4f}",
         f"{results_1st2nd['metrics']['procrustes_disparity']:.4f}",
         f"{results_1st2nd['metrics']['procrustes_disparity'] - results_2nd['metrics']['procrustes_disparity']:+.4f}"],
        ['FIR convexity',
         f"{results_2nd['metrics']['fir_convexity_score']:.1f}",
         f"{results_1st2nd['metrics']['fir_convexity_score']:.1f}",
         f"{results_1st2nd['metrics']['fir_convexity_score'] - results_2nd['metrics']['fir_convexity_score']:+.1f}"]
    ]

    table = ax.table(cellText=table_data, cellLoc='center', loc='center',
                     colWidths=[0.35, 0.2, 0.2, 0.15])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2.5)

    # Style header row
    for i in range(4):
        table[(0, i)].set_facecolor('#40466e')
        table[(0, i)].set_text_props(weight='bold', color='white')

    # Alternate row colors
    for i in range(1, len(table_data)):
        for j in range(4):
            if i % 2 == 0:
                table[(i, j)].set_facecolor('#f0f0f0')

    ax.set_title('Summary Metrics', fontsize=12, fontweight='bold', pad=20)

    plt.savefig(output_dir / 'drift_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()

    print(f"  ✓ Saved: drift_comparison.png")


def run_validation(subject_id, roi_name):
    """Run drift removal validation for one subject-ROI pair"""

    print(f"\n{'='*80}")
    print(f"DRIFT REMOVAL VALIDATION: sub-{subject_id} {roi_name}")
    print(f"{'='*80}\n")

    # Create output directories
    output_dir = OUTPUT_DIR / f"sub-{subject_id}" / roi_name
    output_dir.mkdir(parents=True, exist_ok=True)

    dir_2nd = output_dir / "2nd_only"
    dir_1st2nd = output_dir / "1st_2nd"
    dir_2nd.mkdir(exist_ok=True)
    dir_1st2nd.mkdir(exist_ok=True)

    # Run both methods
    results_2nd = run_single_method(subject_id, roi_name, '2nd_only')
    results_1st2nd = run_single_method(subject_id, roi_name, '1st_2nd')

    # Save outputs for 2nd-only
    print(f"\nSaving 2nd-only outputs to: {dir_2nd}")
    np.save(dir_2nd / 'amplitudes_raw.npy', results_2nd['amplitudes_raw'])
    np.save(dir_2nd / 'amplitudes_procrustes.npy', results_2nd['amplitudes_procrustes'])
    np.save(dir_2nd / 'roi_hrf.npy', results_2nd['roi_hrf'])
    np.save(dir_2nd / 'roi_hrf_deriv.npy', results_2nd['roi_hrf_deriv'])
    np.save(dir_2nd / 'voxel_hrfs.npy', results_2nd['voxel_hrfs'])
    np.save(dir_2nd / 'hrf_correlations.npy', results_2nd['hrf_analysis']['hrf_correlations'])
    np.save(dir_2nd / 'hrf_rmse.npy', results_2nd['hrf_analysis']['hrf_rmse'])

    with open(dir_2nd / 'metrics.json', 'w') as f:
        json.dump(results_2nd['metrics'], f, indent=2)

    # Generate HRF variability plot
    plot_hrf_variability(results_2nd['voxel_hrfs'], results_2nd['roi_hrf'],
                        results_2nd['hrf_analysis'], dir_2nd, roi_name, '2nd-only')

    # Save outputs for 1st+2nd
    print(f"\nSaving 1st+2nd outputs to: {dir_1st2nd}")
    np.save(dir_1st2nd / 'amplitudes_raw.npy', results_1st2nd['amplitudes_raw'])
    np.save(dir_1st2nd / 'amplitudes_procrustes.npy', results_1st2nd['amplitudes_procrustes'])
    np.save(dir_1st2nd / 'roi_hrf.npy', results_1st2nd['roi_hrf'])
    np.save(dir_1st2nd / 'roi_hrf_deriv.npy', results_1st2nd['roi_hrf_deriv'])
    np.save(dir_1st2nd / 'voxel_hrfs.npy', results_1st2nd['voxel_hrfs'])
    np.save(dir_1st2nd / 'hrf_correlations.npy', results_1st2nd['hrf_analysis']['hrf_correlations'])
    np.save(dir_1st2nd / 'hrf_rmse.npy', results_1st2nd['hrf_analysis']['hrf_rmse'])

    with open(dir_1st2nd / 'metrics.json', 'w') as f:
        json.dump(results_1st2nd['metrics'], f, indent=2)

    # Generate HRF variability plot
    plot_hrf_variability(results_1st2nd['voxel_hrfs'], results_1st2nd['roi_hrf'],
                        results_1st2nd['hrf_analysis'], dir_1st2nd, roi_name, '1st+2nd')

    # Generate comparison plot
    print(f"\nGenerating comparison plot...")
    plot_drift_comparison(results_2nd, results_1st2nd, output_dir, roi_name)

    # Save comparison metrics
    comparison_metrics = {
        '2nd_only': results_2nd['metrics'],
        '1st_2nd': results_1st2nd['metrics'],
        'differences': {
            'hrf_mean_correlation': results_1st2nd['metrics']['hrf_mean_correlation'] - results_2nd['metrics']['hrf_mean_correlation'],
            'rdm_reliability_raw': results_1st2nd['metrics']['rdm_reliability_raw'] - results_2nd['metrics']['rdm_reliability_raw'],
            'rdm_reliability_procrustes': results_1st2nd['metrics']['rdm_reliability_procrustes'] - results_2nd['metrics']['rdm_reliability_procrustes'],
            'procrustes_disparity': results_1st2nd['metrics']['procrustes_disparity'] - results_2nd['metrics']['procrustes_disparity'],
            'fir_convexity_score': results_1st2nd['metrics']['fir_convexity_score'] - results_2nd['metrics']['fir_convexity_score']
        }
    }

    with open(output_dir / 'drift_comparison.json', 'w') as f:
        json.dump(comparison_metrics, f, indent=2)

    print(f"\n✓ All outputs saved to: {output_dir}")
    print(f"\n{'='*80}")
    print(f"VALIDATION COMPLETE: sub-{subject_id} {roi_name}")
    print(f"{'='*80}\n")

    return comparison_metrics


def main():
    parser = argparse.ArgumentParser(description='Drift Removal Validation')
    parser.add_argument('--subject', required=True, help='Subject ID (e.g., 01)')
    parser.add_argument('--roi', required=True, choices=['V1', 'V2'], help='ROI name')

    args = parser.parse_args()

    try:
        comparison_metrics = run_validation(args.subject, args.roi)

        # Print summary
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print(f"\nHRF Correlation (mean):")
        print(f"  2nd-only: {comparison_metrics['2nd_only']['hrf_mean_correlation']:.3f}")
        print(f"  1st+2nd:  {comparison_metrics['1st_2nd']['hrf_mean_correlation']:.3f}")
        print(f"  Δ:        {comparison_metrics['differences']['hrf_mean_correlation']:+.3f}")

        print(f"\nRDM Reliability (raw):")
        print(f"  2nd-only: {comparison_metrics['2nd_only']['rdm_reliability_raw']:.3f}")
        print(f"  1st+2nd:  {comparison_metrics['1st_2nd']['rdm_reliability_raw']:.3f}")
        print(f"  Δ:        {comparison_metrics['differences']['rdm_reliability_raw']:+.3f}")

        print(f"\nRDM Reliability (Procrustes):")
        print(f"  2nd-only: {comparison_metrics['2nd_only']['rdm_reliability_procrustes']:.3f}")
        print(f"  1st+2nd:  {comparison_metrics['1st_2nd']['rdm_reliability_procrustes']:.3f}")
        print(f"  Δ:        {comparison_metrics['differences']['rdm_reliability_procrustes']:+.3f}")

        print(f"\nFIR Convexity Score:")
        print(f"  2nd-only: {comparison_metrics['2nd_only']['fir_convexity_score']:.1f}/2.0")
        print(f"  1st+2nd:  {comparison_metrics['1st_2nd']['fir_convexity_score']:.1f}/2.0")

        sys.exit(0)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
