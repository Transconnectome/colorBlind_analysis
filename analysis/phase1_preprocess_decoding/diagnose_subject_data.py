#!/usr/bin/env python3
"""
Diagnose why Sub-02 HRF fitting fails while Sub-01 succeeds

Focus: Voxel-wise temporal characteristics
"""

import numpy as np
import nibabel as nib
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from nilearn import masking

# Paths
FMRIPREP_DIR = Path("/storage/connectome/haba6030/fmriprep_out_method3_header_mi")
EVENT_DIR = Path("/storage/connectome/haba6030/bids_editted")
ROI_DIR = Path("/scratch/connectome/haba6030/colorBlind/analysis/roi_masks/method3_header_mi")
OUTPUT_DIR = Path("analysis/phase1_preprocess_decoding/subject_diagnosis")

TR = 1.5

def load_functional_and_events(subject, run_num, roi_mask):
    """Load functional data and events"""
    # Functional
    func_file = FMRIPREP_DIR / f"sub-{subject}" / "func" / \
                f"sub-{subject}_task-rsvp_run-{run_num}_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz"

    func_img = nib.load(func_file)
    func_data = masking.apply_mask(func_img, roi_mask)  # (n_scans, n_voxels)

    # Events
    event_file = EVENT_DIR / f"sub-{subject}" / "func" / \
                 f"sub-{subject}_task-rsvp_run-{run_num}_events.tsv"
    events_df = pd.read_csv(event_file, sep='\t')

    return func_data, events_df


def compute_voxel_stats(func_data):
    """Compute voxel-wise temporal statistics"""
    n_scans, n_voxels = func_data.shape

    stats = {
        'temporal_mean': np.mean(func_data, axis=0),  # (n_voxels,)
        'temporal_std': np.std(func_data, axis=0),
        'temporal_min': np.min(func_data, axis=0),
        'temporal_max': np.max(func_data, axis=0),
        'temporal_range': np.max(func_data, axis=0) - np.min(func_data, axis=0)
    }

    return stats


def compute_event_locked_response(func_data, events_df, window_trs=8):
    """Compute event-locked average response per voxel"""
    color_events = events_df[events_df['trial_type'].str.startswith('color_')]

    if len(color_events) == 0:
        return None

    # Collect all event-locked windows
    n_scans, n_voxels = func_data.shape
    event_responses = []

    for onset in color_events['onset'].values:
        onset_tr = int(np.round(onset / TR))

        if onset_tr + window_trs <= n_scans:
            window = func_data[onset_tr:onset_tr + window_trs, :]  # (8, n_voxels)
            event_responses.append(window)

    if len(event_responses) == 0:
        return None

    # Average across events: (8, n_voxels)
    avg_response = np.mean(event_responses, axis=0)

    # Compute response strength per voxel (peak - baseline)
    baseline = avg_response[0, :]  # First TR
    peak = np.max(avg_response, axis=0)  # Max across TRs

    response_strength = peak - baseline

    return {
        'avg_response': avg_response,
        'response_strength': response_strength,
        'baseline': baseline,
        'peak': peak
    }


def main():
    import sys

    if len(sys.argv) < 3:
        print("Usage: python diagnose_subject_data.py <subject> <roi>")
        print("Example: python diagnose_subject_data.py 01 V1")
        sys.exit(1)

    subject = sys.argv[1]
    roi = sys.argv[2]

    OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

    print("=" * 80)
    print(f"Subject Data Diagnosis: sub-{subject}, ROI={roi}")
    print("=" * 80)

    # Load ROI mask
    roi_file = ROI_DIR / f"sub-{subject}" / "roi_pipeline" / \
               f"{roi}_mask_thr50_intnearest_binTrue_masknone_gmTrue_subjTrue.nii.gz"

    if not roi_file.exists():
        print(f"ERROR: ROI mask not found: {roi_file}")
        sys.exit(1)

    roi_mask = nib.load(roi_file)
    print(f"✓ Loaded ROI mask: {roi_file}")

    # Load run 1 data
    print("\n[1/3] Loading functional data (run 1)...")
    func_data, events_df = load_functional_and_events(subject, 1, roi_mask)
    n_scans, n_voxels = func_data.shape
    print(f"  Shape: {func_data.shape} (scans × voxels)")

    # Compute voxel statistics
    print("\n[2/3] Computing voxel-wise statistics...")
    stats = compute_voxel_stats(func_data)

    print(f"\n  Temporal Mean:")
    print(f"    Range: [{np.min(stats['temporal_mean']):.2f}, {np.max(stats['temporal_mean']):.2f}]")
    print(f"    Mean:  {np.mean(stats['temporal_mean']):.2f}")

    print(f"\n  Temporal Std:")
    print(f"    Range: [{np.min(stats['temporal_std']):.2f}, {np.max(stats['temporal_std']):.2f}]")
    print(f"    Mean:  {np.mean(stats['temporal_std']):.2f}")
    print(f"    Median: {np.median(stats['temporal_std']):.2f}")

    # Check for problematic voxels
    low_variance_voxels = np.sum(stats['temporal_std'] < 1.0)
    zero_variance_voxels = np.sum(stats['temporal_std'] == 0)

    print(f"\n  Problematic voxels:")
    print(f"    Temporal std < 1.0: {low_variance_voxels}/{n_voxels} ({100*low_variance_voxels/n_voxels:.1f}%)")
    print(f"    Temporal std = 0:   {zero_variance_voxels}/{n_voxels} ({100*zero_variance_voxels/n_voxels:.1f}%)")

    if low_variance_voxels > n_voxels * 0.3:
        print(f"    🚨 WARNING: >30% of voxels have low temporal variance!")

    # Event-locked response
    print("\n[3/3] Computing event-locked responses...")
    event_response = compute_event_locked_response(func_data, events_df)

    if event_response is not None:
        response_strength = event_response['response_strength']

        print(f"\n  Event-locked response strength:")
        print(f"    Range: [{np.min(response_strength):.2f}, {np.max(response_strength):.2f}]")
        print(f"    Mean:  {np.mean(response_strength):.2f}")
        print(f"    Median: {np.median(response_strength):.2f}")

        # Voxels with positive response
        positive_response = np.sum(response_strength > 0)
        strong_response = np.sum(response_strength > 5.0)

        print(f"\n  Response characteristics:")
        print(f"    Voxels with positive response (>0): {positive_response}/{n_voxels} ({100*positive_response/n_voxels:.1f}%)")
        print(f"    Voxels with strong response (>5):  {strong_response}/{n_voxels} ({100*strong_response/n_voxels:.1f}%)")

        if positive_response < n_voxels * 0.5:
            print(f"    🚨 WARNING: <50% of voxels show positive event-locked response!")

    # Visualization
    print("\n[4/4] Generating diagnostic plots...")

    fig, axes = plt.subplots(2, 3, figsize=(15, 10))

    # 1. Temporal mean distribution
    ax = axes[0, 0]
    ax.hist(stats['temporal_mean'], bins=50, alpha=0.7)
    ax.set_xlabel('Temporal Mean (BOLD signal)')
    ax.set_ylabel('Count')
    ax.set_title(f'Sub-{subject} {roi}: Temporal Mean')
    ax.axvline(np.mean(stats['temporal_mean']), color='red', linestyle='--', label='Mean')
    ax.legend()

    # 2. Temporal std distribution
    ax = axes[0, 1]
    ax.hist(stats['temporal_std'], bins=50, alpha=0.7)
    ax.set_xlabel('Temporal Std')
    ax.set_ylabel('Count')
    ax.set_title(f'Temporal Std Distribution')
    ax.axvline(1.0, color='red', linestyle='--', label='Threshold (1.0)')
    ax.legend()

    # 3. Mean vs Std scatter
    ax = axes[0, 2]
    ax.scatter(stats['temporal_mean'], stats['temporal_std'], alpha=0.3, s=1)
    ax.set_xlabel('Temporal Mean')
    ax.set_ylabel('Temporal Std')
    ax.set_title('Mean vs Std')
    ax.axhline(1.0, color='red', linestyle='--', alpha=0.5)

    if event_response is not None:
        # 4. Response strength distribution
        ax = axes[1, 0]
        ax.hist(response_strength, bins=50, alpha=0.7)
        ax.set_xlabel('Response Strength (peak - baseline)')
        ax.set_ylabel('Count')
        ax.set_title('Event-locked Response Strength')
        ax.axvline(0, color='red', linestyle='--', label='Zero')
        ax.legend()

        # 5. Average event-locked response
        ax = axes[1, 1]
        avg_response = event_response['avg_response']
        # Plot median response across voxels
        median_response = np.median(avg_response, axis=1)
        q25_response = np.percentile(avg_response, 25, axis=1)
        q75_response = np.percentile(avg_response, 75, axis=1)

        time_points = np.arange(len(median_response)) * TR
        ax.plot(time_points, median_response, 'b-', linewidth=2, label='Median')
        ax.fill_between(time_points, q25_response, q75_response, alpha=0.3)
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('BOLD signal')
        ax.set_title('Event-locked Response (median ± IQR)')
        ax.legend()
        ax.grid(True, alpha=0.3)

        # 6. Std vs Response strength
        ax = axes[1, 2]
        ax.scatter(stats['temporal_std'], response_strength, alpha=0.3, s=1)
        ax.set_xlabel('Temporal Std')
        ax.set_ylabel('Response Strength')
        ax.set_title('Variance vs Response')
        ax.axhline(0, color='red', linestyle='--', alpha=0.5)
        ax.axvline(1.0, color='red', linestyle='--', alpha=0.5)

    plt.tight_layout()
    plot_file = OUTPUT_DIR / f"diagnosis_sub-{subject}_{roi}.png"
    plt.savefig(plot_file, dpi=150, bbox_inches='tight')
    print(f"✓ Saved: {plot_file}")

    # Save numerical results
    results = {
        'subject': subject,
        'roi': roi,
        'n_voxels': n_voxels,
        'temporal_mean_mean': np.mean(stats['temporal_mean']),
        'temporal_mean_std': np.std(stats['temporal_mean']),
        'temporal_std_mean': np.mean(stats['temporal_std']),
        'temporal_std_median': np.median(stats['temporal_std']),
        'temporal_std_min': np.min(stats['temporal_std']),
        'low_variance_voxels': low_variance_voxels,
        'zero_variance_voxels': zero_variance_voxels,
    }

    if event_response is not None:
        results.update({
            'response_strength_mean': np.mean(response_strength),
            'response_strength_median': np.median(response_strength),
            'positive_response_voxels': positive_response,
            'strong_response_voxels': strong_response,
        })

    results_df = pd.DataFrame([results])
    csv_file = OUTPUT_DIR / f"diagnosis_sub-{subject}_{roi}.csv"
    results_df.to_csv(csv_file, index=False)
    print(f"✓ Saved: {csv_file}")

    print("\n" + "=" * 80)
    print("Diagnosis complete!")
    print("=" * 80)

    # Summary
    print("\n📊 Summary:")
    if zero_variance_voxels > 0:
        print(f"  🚨 Found {zero_variance_voxels} voxels with ZERO temporal variance")
    if low_variance_voxels > n_voxels * 0.3:
        print(f"  ⚠️  {100*low_variance_voxels/n_voxels:.1f}% voxels have low variance (<1.0)")
    if event_response and positive_response < n_voxels * 0.5:
        print(f"  ⚠️  Only {100*positive_response/n_voxels:.1f}% voxels show positive event response")

    if zero_variance_voxels == 0 and low_variance_voxels < n_voxels * 0.1:
        print(f"  ✅ Temporal variance looks normal")

    print("\nNext steps:")
    print("  1. Compare sub-01 vs sub-02 using this script")
    print("  2. Check if sub-02 has excessive low-variance voxels")
    print("  3. Investigate functional data quality (tSNR, motion)")


if __name__ == "__main__":
    main()
