#!/usr/bin/env python3
"""
Drift Processing Debugging Script

Purpose: Identify why drift processing (HPF/cosine) destroys run-to-run reliability

Key Questions:
1. Does HPF remove event-locked signal along with drift?
2. Is there collinearity between drift regressors and condition regressors?
3. How do time-series statistics change after HPF?

Usage:
    python debug_drift_processing.py --subject 01 --roi V1
"""

import argparse
import numpy as np
import pandas as pd
import nibabel as nib
import matplotlib.pyplot as plt
from pathlib import Path
from nilearn import signal, masking
from scipy import stats
from sklearn.linear_model import LinearRegression

# Configuration
FMRIPREP_DIR = Path("/storage/connectome/haba6030/fmriprep_out_method3_header_mi")
EVENT_DIR = Path("/storage/connectome/haba6030/bids_editted")
ROI_DIR = Path("/scratch/connectome/haba6030/colorBlind/analysis/roi_masks/method3_header_mi")
OUTPUT_DIR = Path("analysis/phase1_preprocess_decoding/drift_debug")

TR = 1.5


def load_functional_data(subject, run_num, roi_mask, apply_hpf=False):
    """Load functional data with optional HPF"""
    func_file = FMRIPREP_DIR / f"sub-{subject}" / "func" / \
                f"sub-{subject}_task-rsvp_run-{run_num}_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz"

    if not func_file.exists():
        raise FileNotFoundError(f"Functional file not found: {func_file}")

    # Load and mask
    func_img = nib.load(func_file)
    func_data = masking.apply_mask(func_img, roi_mask)  # (n_scans, n_voxels)

    # Apply HPF if requested
    if apply_hpf:
        func_data_hpf = signal.clean(
            func_data,
            high_pass=0.01,
            t_r=TR,
            standardize=False,
            detrend=False
        )
        return func_data, func_data_hpf
    else:
        return func_data, None


def load_events(subject, run_num):
    """Load event file"""
    event_file = EVENT_DIR / f"sub-{subject}" / "func" / \
                 f"sub-{subject}_task-rsvp_run-{run_num}_events.tsv"

    if not event_file.exists():
        raise FileNotFoundError(f"Event file not found: {event_file}")

    events_df = pd.read_csv(event_file, sep='\t')
    return events_df


def create_cosine_regressors(n_scans, t_r, highpass_cutoff=0.01):
    """Create cosine drift regressors (manual implementation)"""
    # Manual implementation of cosine drift basis
    # Based on SPM/nilearn standard approach

    frame_times = np.arange(n_scans) * t_r
    duration = frame_times[-1] - frame_times[0]

    # Number of basis functions
    n_times = len(frame_times)
    n_basis = int(np.floor(2 * duration * highpass_cutoff + 1))

    # Create cosine basis
    cosine_drift = np.zeros((n_times, n_basis))
    normalizer = np.sqrt(2.0 / n_times)

    for k in range(n_basis):
        cosine_drift[:, k] = normalizer * np.cos(
            (np.pi / duration) * (k + 1) * (frame_times - frame_times[0])
        )

    return cosine_drift


def compute_event_locked_averages(func_data, events_df, n_scans):
    """Compute event-locked averages for each color"""
    # Get color trials only
    color_events = events_df[events_df['trial_type'].str.startswith('color_')]

    # Window: 0-12s post-onset (8 TRs)
    window_trs = 8

    color_averages = {}

    for color_id in range(1, 9):
        color_name = f'color_{color_id}'
        color_trials = color_events[color_events['trial_type'] == color_name]

        if len(color_trials) == 0:
            continue

        # Collect windows
        windows = []
        for onset in color_trials['onset'].values:
            onset_tr = int(np.round(onset / TR))

            # Check bounds
            if onset_tr + window_trs <= n_scans:
                window = func_data[onset_tr:onset_tr + window_trs, :]  # (8, n_voxels)
                windows.append(window)

        if len(windows) > 0:
            # Average across trials
            color_averages[color_name] = np.mean(windows, axis=0)  # (8, n_voxels)

    return color_averages


def compute_pattern_similarity(patterns_before, patterns_after):
    """Compute correlation between color patterns before/after HPF"""
    colors = sorted(patterns_before.keys())

    if len(colors) != 8:
        return None

    # Flatten patterns: (8 colors × 8 TRs, n_voxels)
    before_matrix = np.vstack([patterns_before[c] for c in colors])  # (64, n_voxels)
    after_matrix = np.vstack([patterns_after[c] for c in colors])   # (64, n_voxels)

    # Compute correlation across voxels (for each timepoint)
    correlations = []
    for i in range(before_matrix.shape[0]):
        r = np.corrcoef(before_matrix[i, :], after_matrix[i, :])[0, 1]
        correlations.append(r)

    return np.array(correlations)


def compute_design_collinearity(events_df, n_scans, cosine_regressors=None):
    """Compute collinearity between condition regressors and drift regressors"""
    # Create simple condition regressors (boxcar)
    n_voxels = 1  # Dummy, we only care about design
    X_conditions = np.zeros((n_scans, 8))  # 8 colors

    for color_id in range(1, 9):
        color_name = f'color_{color_id}'
        color_trials = events_df[events_df['trial_type'] == color_name]

        for onset in color_trials['onset'].values:
            onset_tr = int(np.round(onset / TR))
            if onset_tr < n_scans:
                X_conditions[onset_tr, color_id - 1] = 1

    # Compute condition number of X_conditions alone
    cond_num_alone = np.linalg.cond(X_conditions)

    if cosine_regressors is not None:
        # Combined design
        X_combined = np.hstack([X_conditions, cosine_regressors])
        cond_num_combined = np.linalg.cond(X_combined)

        # Max correlation between conditions and cosines
        correlations = []
        for i in range(X_conditions.shape[1]):
            for j in range(cosine_regressors.shape[1]):
                r = np.corrcoef(X_conditions[:, i], cosine_regressors[:, j])[0, 1]
                correlations.append(abs(r))

        max_corr = np.max(correlations)
        mean_corr = np.mean(correlations)
    else:
        cond_num_combined = None
        max_corr = None
        mean_corr = None

    return {
        'cond_num_alone': cond_num_alone,
        'cond_num_combined': cond_num_combined,
        'max_corr_with_cosine': max_corr,
        'mean_corr_with_cosine': mean_corr
    }


def main():
    parser = argparse.ArgumentParser(description='Debug drift processing')
    parser.add_argument('--subject', type=str, required=True, help='Subject ID (e.g., 01)')
    parser.add_argument('--roi', type=str, required=True, help='ROI name (e.g., V1)')
    parser.add_argument('--run', type=int, default=1, help='Run number to analyze (default: 1)')
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

    print("=" * 80)
    print("Drift Processing Debugging")
    print("=" * 80)
    print(f"Subject: sub-{args.subject}")
    print(f"ROI: {args.roi}")
    print(f"Run: {args.run}")
    print()

    # Load ROI mask
    roi_file = ROI_DIR / f"sub-{args.subject}" / "roi_pipeline" / \
               f"{args.roi}_mask_thr50_intnearest_binTrue_masknone_gmTrue_subjTrue.nii.gz"

    if not roi_file.exists():
        raise FileNotFoundError(f"ROI mask not found: {roi_file}")

    roi_mask = nib.load(roi_file)
    print(f"✓ Loaded ROI mask: {roi_file}")

    # Load functional data (with and without HPF)
    print("\n[1/5] Loading functional data...")
    func_raw, func_hpf = load_functional_data(args.subject, args.run, roi_mask, apply_hpf=True)
    n_scans, n_voxels = func_raw.shape
    print(f"  Functional data shape: {func_raw.shape} (scans × voxels)")

    # Load events
    print("\n[2/5] Loading events...")
    events_df = load_events(args.subject, args.run)
    n_color_trials = len(events_df[events_df['trial_type'].str.startswith('color_')])
    print(f"  Total color trials: {n_color_trials}")

    # Analysis 1: Time-series statistics before/after HPF
    print("\n[3/5] Analyzing time-series statistics...")

    stats_before = {
        'mean_per_voxel': np.mean(func_raw, axis=0),
        'std_per_voxel': np.std(func_raw, axis=0),
        'temporal_mean': np.mean(func_raw),
        'temporal_std': np.mean(np.std(func_raw, axis=0))
    }

    stats_after = {
        'mean_per_voxel': np.mean(func_hpf, axis=0),
        'std_per_voxel': np.std(func_hpf, axis=0),
        'temporal_mean': np.mean(func_hpf),
        'temporal_std': np.mean(np.std(func_hpf, axis=0))
    }

    print(f"\n  Before HPF:")
    print(f"    Mean (across all): {stats_before['temporal_mean']:.2f}")
    print(f"    Std (mean across voxels): {stats_before['temporal_std']:.2f}")

    print(f"\n  After HPF:")
    print(f"    Mean (across all): {stats_after['temporal_mean']:.2f}")
    print(f"    Std (mean across voxels): {stats_after['temporal_std']:.2f}")

    # Analysis 2: Event-locked patterns
    print("\n[4/5] Computing event-locked patterns...")

    patterns_before = compute_event_locked_averages(func_raw, events_df, n_scans)
    patterns_after = compute_event_locked_averages(func_hpf, events_df, n_scans)

    print(f"  Patterns extracted for {len(patterns_before)} colors")

    # Compute pattern similarity
    pattern_correlations = compute_pattern_similarity(patterns_before, patterns_after)

    if pattern_correlations is not None:
        print(f"\n  Pattern preservation after HPF:")
        print(f"    Mean correlation: {np.mean(pattern_correlations):.4f}")
        print(f"    Min correlation:  {np.min(pattern_correlations):.4f}")
        print(f"    Max correlation:  {np.max(pattern_correlations):.4f}")

        if np.mean(pattern_correlations) < 0.5:
            print(f"    ⚠️  WARNING: Event-locked patterns heavily distorted by HPF!")

    # Analysis 3: Design matrix collinearity
    print("\n[5/5] Analyzing design matrix collinearity...")

    try:
        # Create cosine regressors
        cosine_regressors = create_cosine_regressors(n_scans, TR, highpass_cutoff=0.01)
        print(f"  Cosine regressors: {cosine_regressors.shape[1]} basis functions")

        collinearity = compute_design_collinearity(events_df, n_scans, cosine_regressors)

        print(f"\n  Condition number:")
        print(f"    Conditions alone: {collinearity['cond_num_alone']:.2f}")
        print(f"    With cosine drift: {collinearity['cond_num_combined']:.2f}")

        if collinearity['max_corr_with_cosine'] is not None:
            print(f"\n  Correlation between conditions and cosine:")
            print(f"    Max correlation: {collinearity['max_corr_with_cosine']:.4f}")
            print(f"    Mean correlation: {collinearity['mean_corr_with_cosine']:.4f}")

            if collinearity['max_corr_with_cosine'] > 0.5:
                print(f"    🚨 CRITICAL: High collinearity detected!")
                print(f"       → Cosine regressors likely removing condition signal")
    except Exception as e:
        print(f"  ⚠️  Collinearity analysis failed: {e}")
        print(f"  → Skipping this analysis, but other results are still valid")
        cosine_regressors = None
        collinearity = {
            'cond_num_alone': None,
            'cond_num_combined': None,
            'max_corr_with_cosine': None,
            'mean_corr_with_cosine': None
        }

    # Visualization
    print("\n[6/6] Generating diagnostic plots...")

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # 1. Voxel mean distribution
    ax = axes[0, 0]
    ax.hist(stats_before['mean_per_voxel'], bins=30, alpha=0.5, label='Before HPF')
    ax.hist(stats_after['mean_per_voxel'], bins=30, alpha=0.5, label='After HPF')
    ax.set_xlabel('Voxel Mean')
    ax.set_ylabel('Count')
    ax.set_title('Distribution of Voxel Means')
    ax.legend()

    # 2. Voxel std distribution
    ax = axes[0, 1]
    ax.hist(stats_before['std_per_voxel'], bins=30, alpha=0.5, label='Before HPF')
    ax.hist(stats_after['std_per_voxel'], bins=30, alpha=0.5, label='After HPF')
    ax.set_xlabel('Voxel Std')
    ax.set_ylabel('Count')
    ax.set_title('Distribution of Voxel Std')
    ax.legend()

    # 3. Pattern correlation over time
    ax = axes[1, 0]
    if pattern_correlations is not None:
        ax.plot(pattern_correlations)
        ax.axhline(0.5, color='red', linestyle='--', label='Threshold (0.5)')
        ax.set_xlabel('Timepoint (within event window)')
        ax.set_ylabel('Correlation')
        ax.set_title('Event Pattern Preservation After HPF')
        ax.legend()
        ax.set_ylim(-0.2, 1.1)

    # 4. Cosine basis visualization
    ax = axes[1, 1]
    if cosine_regressors is not None:
        for i in range(min(5, cosine_regressors.shape[1])):
            ax.plot(cosine_regressors[:, i], alpha=0.7, label=f'Cosine {i+1}')
        ax.set_xlabel('Scan')
        ax.set_ylabel('Amplitude')
        ax.set_title(f'Cosine Drift Regressors (first 5 of {cosine_regressors.shape[1]})')
        ax.legend()
    else:
        ax.text(0.5, 0.5, 'Cosine regressors\nnot available',
                ha='center', va='center', transform=ax.transAxes)
        ax.set_title('Cosine Drift Regressors (N/A)')

    plt.tight_layout()
    plot_file = OUTPUT_DIR / f"drift_debug_sub-{args.subject}_{args.roi}_run{args.run}.png"
    plt.savefig(plot_file, dpi=150, bbox_inches='tight')
    print(f"✓ Saved: {plot_file}")

    # Save numerical results
    results = {
        'subject': args.subject,
        'roi': args.roi,
        'run': args.run,
        'n_scans': n_scans,
        'n_voxels': n_voxels,
        'mean_before_hpf': stats_before['temporal_mean'],
        'mean_after_hpf': stats_after['temporal_mean'],
        'std_before_hpf': stats_before['temporal_std'],
        'std_after_hpf': stats_after['temporal_std'],
        'pattern_corr_mean': np.mean(pattern_correlations) if pattern_correlations is not None else None,
        'pattern_corr_min': np.min(pattern_correlations) if pattern_correlations is not None else None,
        'cond_num_alone': collinearity['cond_num_alone'],
        'cond_num_combined': collinearity['cond_num_combined'],
        'max_corr_with_cosine': collinearity['max_corr_with_cosine'],
        'mean_corr_with_cosine': collinearity['mean_corr_with_cosine']
    }

    results_df = pd.DataFrame([results])
    csv_file = OUTPUT_DIR / f"drift_debug_sub-{args.subject}_{args.roi}_run{args.run}.csv"
    results_df.to_csv(csv_file, index=False)
    print(f"✓ Saved: {csv_file}")

    print("\n" + "=" * 80)
    print("Debugging complete!")
    print("=" * 80)

    # Summary diagnosis
    print("\n🔍 Diagnosis:")

    if pattern_correlations is not None and np.mean(pattern_correlations) < 0.5:
        print("  🚨 HPF severely distorts event-locked patterns")
        print("     → HPF is removing condition signal, not just drift")

    if collinearity['max_corr_with_cosine'] and collinearity['max_corr_with_cosine'] > 0.5:
        print("  🚨 High collinearity between cosine and condition regressors")
        print("     → Cosine basis overlaps with condition signal")

    if collinearity['cond_num_combined'] and collinearity['cond_num_combined'] > collinearity['cond_num_alone'] * 2:
        print("  ⚠️  Design matrix becomes ill-conditioned with drift regressors")
        print("     → GLM may have numerical issues")

    print("\nNext steps:")
    print("  1. Run this analysis on multiple runs to confirm pattern")
    print("  2. Try different HPF cutoffs (0.005, 0.008, 0.015)")
    print("  3. Try alternative detrending (linear, quadratic per run)")
    print("  4. Check if event timing creates low-frequency structure")


if __name__ == "__main__":
    main()
