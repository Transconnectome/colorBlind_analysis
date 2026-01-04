#!/usr/bin/env python3
"""
Functional sanity check for ROI in native BOLD space.

This script performs basic functional analysis to verify that:
1. ROI contains valid BOLD signal
2. Signal has reasonable variance across trials
3. Trial-wise responses are distinguishable
4. Simple decoding is possible

Usage:
    python sanity_check_native_roi.py --subject 02 --roi V1 --run 1

Author: Created for native space ROI validation
Date: 2025-01-04
"""

import argparse
import numpy as np
import pandas as pd
import nibabel as nib
import matplotlib.pyplot as plt
from pathlib import Path
from nilearn.maskers import NiftiMasker
from scipy import stats


def load_bold_data(bold_file, roi_mask):
    """
    Extract BOLD timeseries from ROI.

    Parameters
    ----------
    bold_file : str or Path
        Path to preprocessed BOLD file
    roi_mask : str or Path
        Path to ROI mask

    Returns
    -------
    np.ndarray
        Timeseries data (timepoints x voxels)
    """
    print("  Loading BOLD data...")

    masker = NiftiMasker(
        mask_img=roi_mask,
        standardize=False,
        detrend=False
    )

    timeseries = masker.fit_transform(bold_file)

    print(f"  ✓ Extracted {timeseries.shape[0]} timepoints × {timeseries.shape[1]} voxels")

    return timeseries


def load_events(events_file):
    """
    Load trial events from TSV file.

    Parameters
    ----------
    events_file : str or Path
        Path to events TSV file

    Returns
    -------
    pd.DataFrame
        Events dataframe
    """
    print("  Loading events...")

    events = pd.read_csv(events_file, sep='\t')

    # Filter for color trials only
    color_events = events[events['trial_type'].str.startswith('color_')]

    print(f"  ✓ Found {len(color_events)} color trials")

    return color_events


def extract_trial_averages(timeseries, events, tr=1.5, window_trs=8):
    """
    Extract trial-averaged responses.

    Parameters
    ----------
    timeseries : np.ndarray
        BOLD timeseries (timepoints x voxels)
    events : pd.DataFrame
        Trial events
    tr : float
        Repetition time in seconds
    window_trs : int
        Number of TRs to average per trial

    Returns
    -------
    dict
        Trial-averaged responses per color
    """
    print("  Extracting trial averages...")

    # Get unique colors
    colors = sorted(events['trial_type'].unique())

    trial_responses = {color: [] for color in colors}

    for idx, row in events.iterrows():
        onset_tr = int(row['onset'] / tr)
        color = row['trial_type']

        # Extract window of TRs after stimulus onset
        end_tr = min(onset_tr + window_trs, timeseries.shape[0])
        trial_data = timeseries[onset_tr:end_tr, :]

        # Average across time window
        trial_avg = np.mean(trial_data, axis=0)

        trial_responses[color].append(trial_avg)

    # Convert to arrays
    trial_responses = {
        color: np.array(trials)
        for color, trials in trial_responses.items()
    }

    print(f"  ✓ Extracted responses for {len(colors)} colors")

    return trial_responses


def compute_signal_statistics(timeseries, trial_responses):
    """
    Compute basic signal statistics.

    Parameters
    ----------
    timeseries : np.ndarray
        Full timeseries (timepoints x voxels)
    trial_responses : dict
        Trial-averaged responses per color

    Returns
    -------
    dict
        Signal statistics
    """
    print("  Computing signal statistics...")

    # Overall statistics
    mean_signal = np.mean(timeseries, axis=0)
    std_signal = np.std(timeseries, axis=0)
    tsnr = mean_signal / (std_signal + 1e-10)

    # Trial variance
    all_trials = np.vstack([trials for trials in trial_responses.values()])
    trial_variance = np.var(all_trials, axis=0)

    # Voxel-wise SNR
    within_color_var = []
    for color, trials in trial_responses.items():
        within_color_var.append(np.var(trials, axis=0))
    within_color_var = np.mean(within_color_var, axis=0)

    between_color_var = np.var([np.mean(trials, axis=0) for trials in trial_responses.values()], axis=0)

    snr_ratio = between_color_var / (within_color_var + 1e-10)

    stats_dict = {
        'mean_signal': mean_signal,
        'tsnr': tsnr,
        'trial_variance': trial_variance,
        'snr_ratio': snr_ratio,
        'mean_tsnr': np.mean(tsnr),
        'mean_snr_ratio': np.mean(snr_ratio)
    }

    print(f"  ✓ Mean tSNR: {stats_dict['mean_tsnr']:.2f}")
    print(f"  ✓ Mean SNR ratio: {stats_dict['mean_snr_ratio']:.4f}")

    return stats_dict


def simple_decoding_test(trial_responses):
    """
    Perform simple leave-one-out decoding test.

    Parameters
    ----------
    trial_responses : dict
        Trial-averaged responses per color

    Returns
    -------
    float
        Classification accuracy
    """
    print("  Running simple decoding test...")

    from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
    from sklearn.model_selection import LeaveOneOut

    # Prepare data
    X = []
    y = []

    for color_idx, (color, trials) in enumerate(trial_responses.items()):
        X.append(trials)
        y.extend([color_idx] * len(trials))

    X = np.vstack(X)
    y = np.array(y)

    # Leave-one-out cross-validation
    loo = LeaveOneOut()
    clf = LinearDiscriminantAnalysis()

    correct = 0
    total = 0

    for train_idx, test_idx in loo.split(X):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        clf.fit(X_train, y_train)
        pred = clf.predict(X_test)

        if pred[0] == y_test[0]:
            correct += 1
        total += 1

    accuracy = correct / total

    print(f"  ✓ Classification accuracy: {accuracy:.2%} ({correct}/{total})")

    return accuracy


def create_diagnostic_plots(stats_dict, trial_responses, output_dir, subject, roi, run):
    """
    Create diagnostic plots.

    Parameters
    ----------
    stats_dict : dict
        Signal statistics
    trial_responses : dict
        Trial-averaged responses
    output_dir : Path
        Output directory
    subject : str
        Subject ID
    roi : str
        ROI name
    run : int
        Run number
    """
    print("  Creating diagnostic plots...")

    # Figure 1: Signal quality metrics
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # tSNR distribution
    axes[0, 0].hist(stats_dict['tsnr'], bins=30, edgecolor='black', alpha=0.7)
    axes[0, 0].axvline(stats_dict['mean_tsnr'], color='red', linestyle='--',
                       label=f"Mean: {stats_dict['mean_tsnr']:.2f}")
    axes[0, 0].set_xlabel('tSNR')
    axes[0, 0].set_ylabel('Voxel Count')
    axes[0, 0].set_title('Temporal SNR Distribution')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)

    # SNR ratio distribution
    axes[0, 1].hist(stats_dict['snr_ratio'], bins=30, edgecolor='black', alpha=0.7)
    axes[0, 1].axvline(stats_dict['mean_snr_ratio'], color='red', linestyle='--',
                       label=f"Mean: {stats_dict['mean_snr_ratio']:.4f}")
    axes[0, 1].set_xlabel('Between/Within Color Variance Ratio')
    axes[0, 1].set_ylabel('Voxel Count')
    axes[0, 1].set_title('Color Discriminability (SNR Ratio)')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)

    # Trial variance
    axes[1, 0].hist(stats_dict['trial_variance'], bins=30, edgecolor='black', alpha=0.7)
    axes[1, 0].set_xlabel('Variance')
    axes[1, 0].set_ylabel('Voxel Count')
    axes[1, 0].set_title('Trial Response Variance')
    axes[1, 0].grid(True, alpha=0.3)

    # Response patterns (first 10 voxels)
    for color, trials in trial_responses.items():
        avg_response = np.mean(trials, axis=0)[:10]
        axes[1, 1].plot(avg_response, marker='o', label=color.replace('color_', 'C'))

    axes[1, 1].set_xlabel('Voxel Index')
    axes[1, 1].set_ylabel('Response Amplitude')
    axes[1, 1].set_title('Average Response Patterns (First 10 Voxels)')
    axes[1, 1].legend(ncol=2, fontsize=8)
    axes[1, 1].grid(True, alpha=0.3)

    fig.suptitle(f'sub-{subject} {roi} Functional Diagnostics (Run {run})',
                 fontsize=14, fontweight='bold')
    plt.tight_layout()

    output_path = output_dir / f"sanity_check_sub-{subject}_{roi}_run-{run}.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"  ✓ Saved diagnostic plot: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Functional sanity check for native space ROI'
    )
    parser.add_argument('--subject', type=str, required=True,
                        help='Subject ID (e.g., 02, 03, 05)')
    parser.add_argument('--roi', type=str, required=True,
                        help='ROI name (V1, V2, V3, hV4)')
    parser.add_argument('--run', type=int, default=1,
                        help='Run number (default: 1)')
    parser.add_argument('--fmriprep', type=str,
                        default='/storage/connectome/haba6030/fmriprep_out_original_v3',
                        help='Path to fMRIPrep output directory')
    parser.add_argument('--bids-root', type=str,
                        default='/storage/connectome/haba6030/colorBlind_data_original',
                        help='Path to BIDS root directory')
    parser.add_argument('--derivatives', type=str,
                        default='/scratch/connectome/haba6030/colorBlind/derivatives/native_space_roi',
                        help='Path to derivatives directory')

    args = parser.parse_args()

    # Construct paths
    fmriprep_func_dir = Path(args.fmriprep) / f"sub-{args.subject}" / "func"
    bids_func_dir = Path(args.bids_root) / f"sub-{args.subject}" / "func"
    deriv_dir = Path(args.derivatives) / f"sub-{args.subject}"

    # Input files - try multiple BOLD file options
    bold_file_t1w = fmriprep_func_dir / f"sub-{args.subject}_task-rsvp_run-{args.run}_space-T1w_desc-preproc_bold.nii.gz"
    bold_file_orig = bids_func_dir / f"sub-{args.subject}_task-rsvp_run-{args.run}_bold.nii.gz"

    # Use T1w space if available, otherwise use original BIDS data
    if bold_file_t1w.exists():
        bold_file = bold_file_t1w
        print(f"Using T1w space BOLD: {bold_file}")
    elif bold_file_orig.exists():
        bold_file = bold_file_orig
        print(f"Using original BOLD (no preprocessing): {bold_file}")
        print("⚠ Warning: Using unpreprocessed BOLD - results may be less reliable")
    else:
        print(f"❌ BOLD file not found:")
        print(f"   Tried: {bold_file_t1w}")
        print(f"   Tried: {bold_file_orig}")
        return 1

    roi_mask = deriv_dir / f"sub-{args.subject}_{args.roi}_space-bold_run-{args.run}_mask.nii.gz"
    events_file = bids_func_dir / f"sub-{args.subject}_task-rsvp_run-{args.run}_events.tsv"

    # Check files exist
    for file, name in [(roi_mask, "ROI mask"), (events_file, "Events")]:
        if not file.exists():
            print(f"❌ {name} file not found: {file}")
            return 1

    print("=" * 80)
    print("Functional Sanity Check - Native Space ROI")
    print("=" * 80)
    print(f"Subject: sub-{args.subject}")
    print(f"ROI: {args.roi}")
    print(f"Run: {args.run}")
    print()

    # Step 1: Load data
    print("📥 Step 1: Loading data...")
    timeseries = load_bold_data(bold_file, roi_mask)
    events = load_events(events_file)
    print()

    # Step 2: Extract trial averages
    print("🧮 Step 2: Extracting trial averages...")
    trial_responses = extract_trial_averages(timeseries, events)
    print()

    # Step 3: Compute statistics
    print("📊 Step 3: Computing signal statistics...")
    stats_dict = compute_signal_statistics(timeseries, trial_responses)
    print()

    # Step 4: Simple decoding test
    print("🔬 Step 4: Running decoding test...")
    accuracy = simple_decoding_test(trial_responses)
    print()

    # Step 5: Create diagnostic plots
    print("📈 Step 5: Creating diagnostic plots...")
    create_diagnostic_plots(stats_dict, trial_responses, deriv_dir,
                           args.subject, args.roi, args.run)
    print()

    # Summary and interpretation
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Subject: sub-{args.subject}")
    print(f"ROI: {args.roi} ({timeseries.shape[1]} voxels)")
    print()
    print("Signal Quality:")
    print(f"  Mean tSNR: {stats_dict['mean_tsnr']:.2f}")
    print(f"  Mean SNR ratio: {stats_dict['mean_snr_ratio']:.4f}")
    print()
    print("Functional Response:")
    print(f"  Classification accuracy: {accuracy:.2%}")
    print(f"  Chance level: {100/8:.2%} (8 colors)")
    print()

    # Interpretation
    print("Interpretation:")
    if stats_dict['mean_tsnr'] < 20:
        print("  ⚠ Low tSNR - may indicate noisy data or poor coverage")
    elif stats_dict['mean_tsnr'] < 40:
        print("  ✓ Acceptable tSNR")
    else:
        print("  ✅ Good tSNR")

    if accuracy > 0.20:  # Better than chance (12.5%)
        print(f"  ✅ Decoding successful ({accuracy:.2%} > chance)")
        print("  → ROI contains color-discriminative information")
    else:
        print(f"  ⚠ Decoding at chance level ({accuracy:.2%})")
        print("  → May need more trials or voxels")

    if stats_dict['mean_snr_ratio'] > 0.01:
        print("  ✅ Detectable between-color variance")
    else:
        print("  ⚠ Low between-color variance")

    print()
    print("=" * 80)
    print("CONCLUSION")
    print("=" * 80)

    if (stats_dict['mean_tsnr'] > 20 and
        accuracy > 0.20 and
        stats_dict['mean_snr_ratio'] > 0.01):
        print("✅ ROI passes functional sanity check")
        print("   → Native space analysis can proceed")
        print("   → ROI shows color-discriminative responses")
    else:
        print("⚠ ROI shows suboptimal functional properties")
        print("   → Review diagnostic plots and signal quality")
        print("   → Consider alternative preprocessing or ROI definition")

    print()

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
