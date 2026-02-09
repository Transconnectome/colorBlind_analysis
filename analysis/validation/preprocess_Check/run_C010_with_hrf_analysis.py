#!/usr/bin/env python3
"""
C010 Pipeline with Individual Voxel HRF Analysis

Modified from run_full_dataset_C010.py to save individual voxel HRFs
for HRF variability analysis and visualization.

Key additions:
1. Save individual voxel HRFs (voxel × timepoints)
2. Compute HRF correlation with ROI mean
3. Compute HRF RMSE from ROI mean
4. Generate HRF variability visualizations

Author: Claude Code
Date: 2026-02-09
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
OUTPUT_DIR = BASE_DIR / "derivatives" / "full_dataset_C010_hrf_analysis"

# Pipeline settings
TR = 1.5
N_SCANS = 288
N_RUNS = 6
N_COLORS = 8
FIR_DELAYS = np.arange(8) * TR

# C010 Configuration: Drift Only
MOTION_TISSUE = False
WM_ACOMPCOR = False

print(f"Pipeline Configuration: C010 with HRF Analysis")
print(f"  2nd-level drift: YES")
print(f"  Motion/Tissue confounds: NO")
print(f"  WM aCompCor: NO")
print(f"  Individual voxel HRF: YES (NEW)")
print()


# ============================================================================
# Functions (same as run_full_dataset_C010.py)
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


def create_drift_regressors(n_scans, run_idx, n_runs):
    """Create per-run linear + constant drift"""
    drift_cols = np.zeros((n_scans, n_runs * 2))
    drift_cols[:, run_idx - 1] = np.linspace(-0.5, 0.5, n_scans)
    drift_cols[:, n_runs + run_idx - 1] = 1.0
    return drift_cols


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


def build_2nd_level_design_matrix(events, n_scans, tr, hrf, hrf_deriv, run_idx, n_runs, confounds=None):
    """Build 2nd-level design matrix"""
    X_components = []

    X_hrf = convolve_hrf_with_events(events, n_scans, tr, hrf, hrf_deriv)
    X_components.append(X_hrf[:, :N_COLORS])
    X_components.append(X_hrf[:, N_COLORS:])

    drift_cols = create_drift_regressors(n_scans, run_idx, n_runs)
    X_components.append(drift_cols)

    if confounds is not None:
        X_components.append(confounds)

    X = np.hstack(X_components)
    return X


def compute_split_half_reliability(amplitudes, n_iterations=100):
    """Compute random split-half reliability"""
    n_runs, n_colors, n_voxels = amplitudes.shape

    if n_runs < 4:
        return {'corrected': np.nan, 'raw': np.nan}

    correlations = []
    np.random.seed(42)

    for _ in range(n_iterations):
        run_indices = np.random.permutation(n_runs)
        split_point = n_runs // 2

        half1_runs = run_indices[:split_point]
        half2_runs = run_indices[split_point:2*split_point]

        half1_patterns = amplitudes[half1_runs].mean(axis=0)
        half2_patterns = amplitudes[half2_runs].mean(axis=0)

        rdm1 = 1 - np.corrcoef(half1_patterns)
        rdm2 = 1 - np.corrcoef(half2_patterns)

        mask = np.triu(np.ones_like(rdm1, dtype=bool), k=1)
        rdm1_vec = rdm1[mask]
        rdm2_vec = rdm2[mask]

        r, _ = spearmanr(rdm1_vec, rdm2_vec)
        correlations.append(r)

    correlations = np.array(correlations)
    correlations = correlations[np.isfinite(correlations)]

    r_half = np.mean(correlations)
    r_corrected = 2 * r_half / (1 + r_half) if r_half < 1 else 1.0

    return {'corrected': r_corrected, 'raw': r_half}


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


def compute_metrics(amplitudes_raw, amplitudes_proc, disparities):
    """Compute all metrics"""
    results_raw_random = compute_split_half_reliability(amplitudes_raw, n_iterations=100)
    results_raw_oddeven = compute_split_half_odd_even(amplitudes_raw)

    results_proc_random = compute_split_half_reliability(amplitudes_proc, n_iterations=100)
    results_proc_oddeven = compute_split_half_odd_even(amplitudes_proc)

    raw_method_diff = abs(results_raw_random['corrected'] - results_raw_oddeven['corrected'])
    proc_method_diff = abs(results_proc_random['corrected'] - results_proc_oddeven['corrected'])

    raw_rdm_reliability = (results_raw_random['raw'] + results_raw_oddeven['raw']) / 2
    proc_rdm_reliability = (results_proc_random['raw'] + results_proc_oddeven['raw']) / 2

    n_runs, n_colors, n_voxels = amplitudes_raw.shape
    autocorr_values = []
    for voxel_idx in range(min(100, n_voxels)):
        voxel_timecourse = amplitudes_raw[:, :, voxel_idx].flatten()
        for run_idx in range(n_runs - 1):
            start = run_idx * n_colors
            end = start + n_colors
            next_start = (run_idx + 1) * n_colors
            next_end = next_start + n_colors

            r = np.corrcoef(voxel_timecourse[start:end], voxel_timecourse[next_start:next_end])[0, 1]
            if np.isfinite(r):
                autocorr_values.append(r)

    temporal_autocorr = np.mean(autocorr_values) if autocorr_values else 0.0

    drift_magnitudes = []
    for voxel_idx in range(n_voxels):
        voxel_means = amplitudes_raw[:, :, voxel_idx].mean(axis=1)
        slope = np.polyfit(np.arange(n_runs), voxel_means, 1)[0]
        drift_magnitudes.append(abs(slope))
    drift_magnitude = np.mean(drift_magnitudes)

    procrustes_disparity = disparities.mean()

    return {
        'raw_noise_ceiling': {
            'random': results_raw_random['corrected'],
            'oddeven': results_raw_oddeven['corrected'],
            'method_diff': raw_method_diff
        },
        'procrustes_noise_ceiling': {
            'random': results_proc_random['corrected'],
            'oddeven': results_proc_oddeven['corrected'],
            'method_diff': proc_method_diff
        },
        'raw_rdm_reliability': raw_rdm_reliability,
        'procrustes_rdm_reliability': proc_rdm_reliability,
        'temporal_autocorrelation': temporal_autocorr,
        'drift_magnitude': drift_magnitude,
        'procrustes_disparity': procrustes_disparity
    }


# ============================================================================
# NEW: HRF Variability Analysis Functions
# ============================================================================

def analyze_hrf_variability(voxel_hrfs, roi_hrf):
    """
    Analyze HRF variability across voxels

    Args:
        voxel_hrfs: (n_voxels, n_timepoints) - individual voxel HRFs
        roi_hrf: (n_timepoints,) - ROI mean HRF

    Returns:
        Dictionary with HRF variability metrics
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


def plot_hrf_variability(voxel_hrfs, roi_hrf, hrf_analysis, output_dir, roi_name):
    """
    Generate HRF variability visualization (matching the reference image)

    6-panel figure:
    1. Individual Voxel HRFs (n=100 shown) + ROI Mean ±1 SD
    2. HRF Correlation Distribution
    3. HRF RMSE Distribution
    4. HRF Variability Per Timepoint
    5. Best (green) vs Worst (red) Fitting Voxels
    """
    fig = plt.figure(figsize=(20, 12))
    gs = fig.add_gridspec(2, 3, hspace=0.3, wspace=0.3)

    n_voxels = voxel_hrfs.shape[0]
    timepoints = FIR_DELAYS

    # Title
    fig.suptitle(f'{roi_name}: HRF Variability Analysis (ROI vs Individual Voxels)',
                 fontsize=16, fontweight='bold')

    # 1. Individual Voxel HRFs (top-left)
    ax = fig.add_subplot(gs[0, 0])

    # Plot subset of individual voxels (100 random)
    n_show = min(100, n_voxels)
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

    plt.savefig(output_dir / f'figures_hrf_variability_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()

    print(f"  ✓ Saved: figures_hrf_variability_analysis.png")


# ============================================================================
# Main Pipeline
# ============================================================================

def run_subject_roi(subject_id, roi_name):
    """Run C010 pipeline with HRF analysis for one subject-ROI pair"""

    print(f"\n{'='*80}")
    print(f"Processing: sub-{subject_id} {roi_name} (C010 + HRF Analysis)")
    print(f"{'='*80}\n")

    # Create output directory
    output_dir = OUTPUT_DIR / f"sub-{subject_id}" / roi_name
    output_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: 1st-level HRF estimation
    print("Step 1: 1st-level HRF estimation...")

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

    # NEW: Extract individual voxel HRFs
    # betas_fir shape: (64, n_voxels) = (8 colors × 8 delays, n_voxels)
    n_voxels = betas_fir.shape[1]
    voxel_hrfs = np.zeros((n_voxels, len(FIR_DELAYS)))

    # Average across colors to get voxel-specific HRF
    for voxel_idx in range(n_voxels):
        voxel_fir = betas_fir[:, voxel_idx].reshape(N_COLORS, len(FIR_DELAYS))
        voxel_hrfs[voxel_idx] = voxel_fir.mean(axis=0)  # Average across colors

    # ROI HRF (average across voxels)
    roi_hrf_fir = betas_fir.mean(axis=1).reshape(N_COLORS, len(FIR_DELAYS))
    roi_hrf = roi_hrf_fir.mean(axis=0)
    roi_hrf_deriv = np.gradient(roi_hrf)

    print(f"  ✓ ROI HRF estimated: shape {roi_hrf.shape}")
    print(f"  ✓ Individual voxel HRFs: shape {voxel_hrfs.shape}")

    # Step 2: 2nd-level amplitude estimation (same as before)
    print("\nStep 2: 2nd-level amplitude estimation...")

    amplitudes_raw = []
    all_residuals = []

    for run_idx in range(1, N_RUNS + 1):
        print(f"  Run {run_idx}...")
        func_data, events = load_bold_data(subject_id, roi_name, run_idx)
        n_scans = func_data.shape[0]

        X = build_2nd_level_design_matrix(
            events, n_scans, TR, roi_hrf, roi_hrf_deriv,
            run_idx, N_RUNS, confounds=None
        )

        print(f"    Design matrix: {X.shape}")

        betas, _, _, _ = np.linalg.lstsq(X, func_data, rcond=None)
        amplitudes = betas[:N_COLORS, :]
        amplitudes_raw.append(amplitudes)

        Y_hat = X @ betas
        residuals = func_data - Y_hat
        all_residuals.append(residuals)
        print(f"    Residuals: {residuals.shape}")

    amplitudes_raw = np.array(amplitudes_raw)
    all_residuals = np.vstack(all_residuals)
    print(f"\n✓ Amplitudes computed: {amplitudes_raw.shape}")
    print(f"✓ Residuals computed: {all_residuals.shape}")

    # Step 3: Procrustes alignment
    print("\nStep 3: Procrustes alignment...")
    amplitudes_proc, disparities = apply_procrustes_alignment(amplitudes_raw)
    print(f"  ✓ Mean disparity: {disparities.mean():.6f}")

    # Step 4: Compute metrics
    print("\nStep 4: Computing metrics...")
    metrics = compute_metrics(amplitudes_raw, amplitudes_proc, disparities)

    print(f"\n  RDM Reliability:")
    print(f"    Raw: {metrics['raw_rdm_reliability']:.4f}")
    print(f"    Procrustes: {metrics['procrustes_rdm_reliability']:.4f}")

    # Step 5: NEW - HRF Variability Analysis
    print("\nStep 5: HRF Variability Analysis...")
    hrf_analysis = analyze_hrf_variability(voxel_hrfs, roi_hrf)

    print(f"  Mean HRF correlation: {hrf_analysis['mean_correlation']:.3f}")
    print(f"  Median HRF correlation: {hrf_analysis['median_correlation']:.3f}")
    print(f"  Mean HRF RMSE: {hrf_analysis['mean_rmse']:.3f}")

    # Generate HRF variability visualization
    print("\nStep 6: Generating HRF variability visualization...")
    plot_hrf_variability(voxel_hrfs, roi_hrf, hrf_analysis, output_dir, roi_name)

    # Step 7: Save outputs
    print("\nStep 7: Saving outputs...")

    np.save(output_dir / 'amplitudes_raw.npy', amplitudes_raw)
    np.save(output_dir / 'amplitudes_procrustes.npy', amplitudes_proc)
    np.save(output_dir / 'procrustes_disparities.npy', disparities)
    np.save(output_dir / 'roi_hrf.npy', roi_hrf)
    np.save(output_dir / 'roi_hrf_deriv.npy', roi_hrf_deriv)
    np.save(output_dir / 'residuals_2nd_level.npy', all_residuals)

    # NEW: Save individual voxel HRFs and analysis
    np.save(output_dir / 'voxel_hrfs.npy', voxel_hrfs)
    np.save(output_dir / 'hrf_correlations.npy', hrf_analysis['hrf_correlations'])
    np.save(output_dir / 'hrf_rmse.npy', hrf_analysis['hrf_rmse'])

    # Save metrics (including HRF analysis)
    metrics['hrf_analysis'] = {
        'mean_correlation': float(hrf_analysis['mean_correlation']),
        'median_correlation': float(hrf_analysis['median_correlation']),
        'mean_rmse': float(hrf_analysis['mean_rmse']),
        'median_rmse': float(hrf_analysis['median_rmse'])
    }

    with open(output_dir / 'metrics.json', 'w') as f:
        json.dump(metrics, f, indent=2)

    config = {
        'subject': subject_id,
        'roi': roi_name,
        'n_voxels': amplitudes_raw.shape[2],
        'pipeline': 'C010_HRF_Analysis',
        'motion_tissue': MOTION_TISSUE,
        'wm_acompcor': WM_ACOMPCOR,
        'hrf_analysis': True
    }

    with open(output_dir / 'config.json', 'w') as f:
        json.dump(config, f, indent=2)

    print(f"\n✓ Outputs saved to: {output_dir}")
    print(f"\n{'='*80}")
    print(f"COMPLETED: sub-{subject_id} {roi_name}")
    print(f"{'='*80}\n")

    return metrics


def main():
    parser = argparse.ArgumentParser(description='C010 Pipeline with HRF Analysis')
    parser.add_argument('--subject', required=True, help='Subject ID (e.g., 02)')
    parser.add_argument('--roi', required=True, choices=['V1', 'V2', 'V3', 'V4'], help='ROI name')

    args = parser.parse_args()

    try:
        metrics = run_subject_roi(args.subject, args.roi)
        sys.exit(0)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
