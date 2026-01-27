#!/usr/bin/env python3
"""
1.1 tSNR Analysis
=================
ROI별 tSNR 분포 계산 및 시각화

Input:
- fMRIPrep outputs: {FMRIPREP_OUT}/sub-{ID}/func/*_desc-preproc_bold.nii.gz
- ROI masks: {BASELINE_RESULTS}/sub-{ID}/{ROI}/roi_mask.nii.gz

Output:
- {VALIDATION_OUT}/tsnr/{TIMESTAMP}/tsnr_values.json
- Figures: tsnr_violin_by_roi.png, tsnr_boxplot_by_subject.png
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
import numpy as np
import nibabel as nib
import matplotlib.pyplot as plt
from tqdm import tqdm

# Set style
plt.rcParams['figure.dpi'] = 150
plt.style.use('default')


def compute_tsnr_and_drift(bold_img, mask_img):
    """
    Compute tSNR and drift/movement indicators for ROI voxels

    Drift Analysis:
    - Linear trend in mean ROI signal over time
    - drift_ratio > 0.01 (1% per TR) → severe drift (movement/heating)
    - drift_ratio > 0.005 (0.5% per TR) → moderate drift
    - Positive slope → signal increase (movement into slice, heating)
    - Negative slope → signal decrease (movement out, saturation)

    Args:
        bold_img: 4D fMRI data
        mask_img: 3D binary mask

    Returns:
        dict with:
            - tsnr_median: Median tSNR across ROI voxels
            - drift_ratio: Absolute linear trend relative to mean signal
            - drift_direction: 'increase' or 'decrease' or 'stable'
            - percent_change: Total signal change from first to last timepoint (%)
    """
    bold_data = bold_img.get_fdata()  # (x, y, z, time)
    mask_data = mask_img.get_fdata().astype(bool)

    # Extract ROI timeseries (n_voxels, n_timepoints)
    roi_timeseries = bold_data[mask_data]  # (n_voxels, n_timepoints)

    # Compute tSNR per voxel
    mean_signal = np.mean(roi_timeseries, axis=1)
    std_signal = np.std(roi_timeseries, axis=1)

    # Avoid division by zero
    tsnr_voxels = np.divide(mean_signal, std_signal,
                           where=std_signal > 0,
                           out=np.zeros_like(mean_signal))

    tsnr_median = np.median(tsnr_voxels)

    # === Drift/Movement Analysis ===
    # Average timeseries across all voxels in ROI
    roi_mean_timeseries = np.mean(roi_timeseries, axis=0)  # (n_timepoints,)
    n_timepoints = len(roi_mean_timeseries)

    # Linear regression: signal = slope * time + intercept
    time_points = np.arange(n_timepoints)
    slope, intercept = np.polyfit(time_points, roi_mean_timeseries, deg=1)

    # Drift ratio: |slope| / mean(signal)
    # Interpretation: drift per timepoint as % of mean signal
    mean_roi_signal = np.mean(roi_mean_timeseries)
    drift_ratio = abs(slope) / mean_roi_signal if mean_roi_signal > 0 else 0

    # Drift direction
    if abs(slope) < 0.001 * mean_roi_signal:  # < 0.1% per TR
        drift_direction = 'stable'
    elif slope > 0:
        drift_direction = 'increase'
    else:
        drift_direction = 'decrease'

    # Percent change from first to last timepoint
    first_value = roi_mean_timeseries[0]
    last_value = roi_mean_timeseries[-1]
    percent_change = ((last_value - first_value) / first_value * 100) if first_value > 0 else 0

    return {
        'tsnr_median': float(tsnr_median),
        'drift_ratio': float(drift_ratio),
        'drift_direction': drift_direction,
        'percent_change': float(percent_change),
        'mean_signal': float(mean_roi_signal),
        'slope': float(slope)
    }


def main():
    parser = argparse.ArgumentParser(description='Compute tSNR for validation')
    parser.add_argument('--baseline-timestamp', type=str, required=True,
                       help='Timestamp of baseline results (e.g., 20260122_143000)')
    parser.add_argument('--subjects', nargs='+',
                       default=[f'sub-{i:02d}' for i in range(1, 11)],
                       help='List of subjects (default: sub-01 to sub-10)')
    parser.add_argument('--rois', nargs='+',
                       default=['V1', 'V2', 'V3', 'hV4'],
                       help='List of ROIs')
    parser.add_argument('--n-runs', type=int, default=6,
                       help='Number of runs per subject')

    args = parser.parse_args()

    # Paths
    fmriprep_dir = Path('/storage/connectome/haba6030/fmriprep_out_method3_header_mi')
    baseline_dir = Path('/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/method3_header_mi/results/baseline_decoding') / args.baseline_timestamp
    output_dir = Path('/scratch/connectome/haba6030/colorBlind/analysis/validation/results/tsnr')

    # Create timestamp for this run
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    run_dir = output_dir / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"Output directory: {run_dir}")

    # Storage for results
    tsnr_data = {
        'subjects': args.subjects,
        'rois': args.rois,
        'n_runs': args.n_runs,
        'values': {}  # subject -> roi -> run -> tsnr
    }

    # ROI mask directory
    roi_mask_dir = Path('/scratch/connectome/haba6030/colorBlind/analysis/roi_masks/method3_header_mi')

    # Compute tSNR for each subject-roi-run
    print("\nComputing tSNR...")
    for subject in tqdm(args.subjects, desc='Subjects'):
        tsnr_data['values'][subject] = {}

        for roi in args.rois:
            tsnr_data['values'][subject][roi] = {}

            # Load ROI mask from roi_masks directory
            # Find mask file (pattern: {ROI}_mask_*.nii.gz)
            import glob
            mask_pattern = str(roi_mask_dir / subject / 'roi_pipeline' / f'{roi}_mask_*.nii.gz')
            mask_files = glob.glob(mask_pattern)

            if not mask_files:
                print(f"Warning: Mask not found for {subject} {roi} (pattern: {mask_pattern})")
                continue

            mask_path = mask_files[0]  # Use first match
            mask_img = nib.load(mask_path)

            for run in range(1, args.n_runs + 1):
                # Load BOLD data
                bold_pattern = f"{subject}_task-rsvp_run-{run}_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz"
                bold_path = fmriprep_dir / subject / 'func' / bold_pattern

                if not bold_path.exists():
                    print(f"Warning: BOLD not found for {subject} run-{run}")
                    continue

                bold_img = nib.load(bold_path)

                # Compute tSNR and drift
                metrics = compute_tsnr_and_drift(bold_img, mask_img)
                tsnr_data['values'][subject][roi][f'run-{run}'] = metrics

    # Save tSNR values
    json_path = run_dir / 'tsnr_values.json'
    with open(json_path, 'w') as f:
        json.dump(tsnr_data, f, indent=2)
    print(f"\nSaved tSNR values to {json_path}")

    # Prepare data for plotting
    plot_data = []
    drift_data = []
    for subject in args.subjects:
        for roi in args.rois:
            if subject not in tsnr_data['values'] or roi not in tsnr_data['values'][subject]:
                continue
            for run_key, metrics in tsnr_data['values'][subject][roi].items():
                plot_data.append({
                    'subject': subject,
                    'roi': roi,
                    'run': run_key,
                    'tsnr': metrics['tsnr_median']
                })
                drift_data.append({
                    'subject': subject,
                    'roi': roi,
                    'run': run_key,
                    'drift_ratio': metrics['drift_ratio'],
                    'drift_direction': metrics['drift_direction'],
                    'percent_change': metrics['percent_change']
                })

    import pandas as pd
    df = pd.DataFrame(plot_data)
    df_drift = pd.DataFrame(drift_data)

    # Figure 1: Violin plot by ROI
    fig, ax = plt.subplots(figsize=(10, 6))

    # Create violin plot manually using matplotlib
    roi_positions = {roi: i for i, roi in enumerate(args.rois)}
    colors = plt.cm.Set2(np.linspace(0, 1, args.n_runs))

    for run_idx in range(1, args.n_runs + 1):
        run_key = f'run-{run_idx}'
        run_data = df[df['run'] == run_key]

        for roi in args.rois:
            roi_run_data = run_data[run_data['roi'] == roi]['tsnr'].values
            if len(roi_run_data) > 0:
                pos = roi_positions[roi] + (run_idx - 3.5) * 0.12  # Offset for multiple runs
                parts = ax.violinplot([roi_run_data], positions=[pos], widths=0.1,
                                     showmeans=True, showmedians=False)
                for pc in parts['bodies']:
                    pc.set_facecolor(colors[run_idx - 1])
                    pc.set_alpha(0.6)

    ax.axhline(y=50, color='green', linestyle='--', label='Good (tSNR>50)', linewidth=2)
    ax.axhline(y=30, color='orange', linestyle='--', label='Acceptable (tSNR>30)', linewidth=2)
    ax.set_xticks(list(roi_positions.values()))
    ax.set_xticklabels(list(roi_positions.keys()))
    ax.set_xlabel('ROI', fontsize=12)
    ax.set_ylabel('tSNR', fontsize=12)
    ax.set_title('tSNR Distribution by ROI (across runs)', fontsize=14)
    ax.legend(loc='upper right', fontsize=8)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    fig_path1 = run_dir / 'tsnr_violin_by_roi.png'
    plt.savefig(fig_path1)
    print(f"Saved violin plot to {fig_path1}")
    plt.close()

    # Figure 2: Boxplot by subject
    fig, ax = plt.subplots(figsize=(12, 6))

    # Organize data by subject and ROI
    subject_positions = {subj: i for i, subj in enumerate(args.subjects)}
    colors_roi = plt.cm.Set1(np.linspace(0, 1, len(args.rois)))

    for roi_idx, roi in enumerate(args.rois):
        roi_data = df[df['roi'] == roi]

        for subject in args.subjects:
            subj_roi_data = roi_data[roi_data['subject'] == subject]['tsnr'].values
            if len(subj_roi_data) > 0:
                pos = subject_positions[subject] + (roi_idx - 1.5) * 0.15
                bp = ax.boxplot([subj_roi_data], positions=[pos], widths=0.12,
                               patch_artist=True, showfliers=False)
                for patch in bp['boxes']:
                    patch.set_facecolor(colors_roi[roi_idx])
                    patch.set_alpha(0.6)

    # Add legend manually
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor=colors_roi[i], alpha=0.6, label=roi)
                      for i, roi in enumerate(args.rois)]

    ax.axhline(y=50, color='green', linestyle='--', alpha=0.5, linewidth=2)
    ax.axhline(y=30, color='orange', linestyle='--', alpha=0.5, linewidth=2)
    ax.set_xticks(list(subject_positions.values()))
    ax.set_xticklabels(list(subject_positions.keys()), rotation=45)
    ax.set_xlabel('Subject', fontsize=12)
    ax.set_ylabel('tSNR', fontsize=12)
    ax.set_title('tSNR Distribution by Subject (across ROIs)', fontsize=14)
    ax.legend(handles=legend_elements, loc='upper right', fontsize=10)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    fig_path2 = run_dir / 'tsnr_boxplot_by_subject.png'
    plt.savefig(fig_path2)
    print(f"Saved boxplot to {fig_path2}")
    plt.close()

    # Figure 3: Drift analysis
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # 3A: Drift ratio by subject
    ax = axes[0]
    subject_positions = {subj: i for i, subj in enumerate(args.subjects)}

    for subject in args.subjects:
        subj_drift = df_drift[df_drift['subject'] == subject]['drift_ratio'].values
        if len(subj_drift) > 0:
            pos = subject_positions[subject]
            bp = ax.boxplot([subj_drift * 100], positions=[pos], widths=0.5,
                           patch_artist=True, showfliers=True)
            for patch in bp['boxes']:
                patch.set_facecolor('lightcoral')
                patch.set_alpha(0.6)

    ax.axhline(y=1.0, color='red', linestyle='--', label='Severe (>1%/TR)', linewidth=2)
    ax.axhline(y=0.5, color='orange', linestyle='--', label='Moderate (>0.5%/TR)', linewidth=2)
    ax.set_xticks(list(subject_positions.values()))
    ax.set_xticklabels(list(subject_positions.keys()), rotation=45)
    ax.set_xlabel('Subject', fontsize=12)
    ax.set_ylabel('Drift Ratio (%/TR)', fontsize=12)
    ax.set_title('Signal Drift by Subject\n(Movement/Scanner Drift Indicator)', fontsize=14)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    # 3B: Percent change distribution
    ax = axes[1]
    roi_positions = {roi: i for i, roi in enumerate(args.rois)}

    for roi in args.rois:
        roi_pct = df_drift[df_drift['roi'] == roi]['percent_change'].values
        if len(roi_pct) > 0:
            pos = roi_positions[roi]
            bp = ax.boxplot([roi_pct], positions=[pos], widths=0.5,
                           patch_artist=True, showfliers=True)
            for patch in bp['boxes']:
                patch.set_facecolor('lightblue')
                patch.set_alpha(0.6)

    ax.axhline(y=5.0, color='red', linestyle='--', label='Large change (>5%)', linewidth=2)
    ax.axhline(y=2.0, color='orange', linestyle='--', label='Moderate (>2%)', linewidth=2)
    ax.set_xticks(list(roi_positions.values()))
    ax.set_xticklabels(list(roi_positions.keys()))
    ax.set_xlabel('ROI', fontsize=12)
    ax.set_ylabel('Total Signal Change (%)', fontsize=12)
    ax.set_title('Signal Change (First to Last Timepoint)', fontsize=14)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    fig_path3 = run_dir / 'tsnr_drift_analysis.png'
    plt.savefig(fig_path3)
    print(f"Saved drift analysis to {fig_path3}")
    plt.close()

    # Compute summary statistics
    summary = {
        'overall_mean': float(df['tsnr'].mean()),
        'overall_std': float(df['tsnr'].std()),
        'overall_median': float(df['tsnr'].median()),
        'drift_mean': float(df_drift['drift_ratio'].mean() * 100),  # as %
        'drift_median': float(df_drift['drift_ratio'].median() * 100),
        'percent_change_mean': float(df_drift['percent_change'].mean()),
        'by_roi': {},
        'by_subject': {},
        'quality_check': {
            'good_count': int((df['tsnr'] > 50).sum()),
            'acceptable_count': int(((df['tsnr'] > 30) & (df['tsnr'] <= 50)).sum()),
            'poor_count': int((df['tsnr'] <= 30).sum()),
            'total_count': len(df)
        },
        'drift_check': {
            'severe_drift_count': int((df_drift['drift_ratio'] > 0.01).sum()),  # >1%/TR
            'moderate_drift_count': int(((df_drift['drift_ratio'] > 0.005) & (df_drift['drift_ratio'] <= 0.01)).sum()),
            'stable_count': int((df_drift['drift_ratio'] <= 0.005).sum()),
            'total_count': len(df_drift)
        }
    }

    for roi in args.rois:
        roi_data = df[df['roi'] == roi]['tsnr']
        roi_drift = df_drift[df_drift['roi'] == roi]['drift_ratio']
        summary['by_roi'][roi] = {
            'mean': float(roi_data.mean()),
            'std': float(roi_data.std()),
            'median': float(roi_data.median()),
            'drift_mean': float(roi_drift.mean() * 100),
            'drift_median': float(roi_drift.median() * 100)
        }

    for subject in args.subjects:
        subj_data = df[df['subject'] == subject]['tsnr']
        subj_drift = df_drift[df_drift['subject'] == subject]['drift_ratio']
        if len(subj_data) > 0:
            summary['by_subject'][subject] = {
                'mean': float(subj_data.mean()),
                'std': float(subj_data.std()),
                'median': float(subj_data.median()),
                'drift_mean': float(subj_drift.mean() * 100) if len(subj_drift) > 0 else 0,
                'drift_median': float(subj_drift.median() * 100) if len(subj_drift) > 0 else 0
            }

    # Save results
    results_path = run_dir / 'results.json'
    with open(results_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"Saved summary to {results_path}")

    # Save settings
    settings = {
        'script': '01_tsnr_analysis.py',
        'baseline_timestamp': args.baseline_timestamp,
        'subjects': args.subjects,
        'rois': args.rois,
        'n_runs': args.n_runs,
        'fmriprep_dir': str(fmriprep_dir),
        'baseline_dir': str(baseline_dir),
        'timestamp': timestamp
    }
    settings_path = run_dir / 'settings.json'
    with open(settings_path, 'w') as f:
        json.dump(settings, f, indent=2)
    print(f"Saved settings to {settings_path}")

    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Overall tSNR: {summary['overall_mean']:.2f} ± {summary['overall_std']:.2f}")
    print(f"  Good (>50): {summary['quality_check']['good_count']}/{summary['quality_check']['total_count']}")
    print(f"  Acceptable (30-50): {summary['quality_check']['acceptable_count']}/{summary['quality_check']['total_count']}")
    print(f"  Poor (<30): {summary['quality_check']['poor_count']}/{summary['quality_check']['total_count']}")
    print(f"\nDrift Analysis:")
    print(f"  Mean drift: {summary['drift_mean']:.3f}%/TR")
    print(f"  Mean signal change: {summary['percent_change_mean']:.2f}%")
    print(f"  Severe drift (>1%/TR): {summary['drift_check']['severe_drift_count']}/{summary['drift_check']['total_count']}")
    print(f"  Moderate drift (0.5-1%/TR): {summary['drift_check']['moderate_drift_count']}/{summary['drift_check']['total_count']}")
    print(f"  Stable (<0.5%/TR): {summary['drift_check']['stable_count']}/{summary['drift_check']['total_count']}")
    print("="*70)


if __name__ == '__main__':
    main()
