#!/usr/bin/env python3
"""
Step 1.2: Reliability Comparison (Color-averaged vs Trial-wise)

목적:
1. Color-averaged reliability (기존 방법, baseline)
2. Trial-wise reliability (LS-S, 새 방법)
3. 두 방법 비교 및 의사결정

사용법:
    python 01_reliability_comparison.py --subject 02 --roi V1

Author: Neuroimaging Team
Date: 2025-12-28
"""

import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from nilearn import image
from nilearn.glm.first_level import FirstLevelModel
from nilearn.maskers import NiftiMasker
import json


def parse_args():
    """커맨드라인 인자 파싱"""
    parser = argparse.ArgumentParser(
        description='Reliability comparison: Color-averaged vs Trial-wise'
    )
    parser.add_argument(
        '--subject',
        type=str,
        required=True,
        help='Subject ID (e.g., 02)'
    )
    parser.add_argument(
        '--roi',
        type=str,
        required=True,
        help='ROI name (e.g., V1, V2, V3, hV4)'
    )
    parser.add_argument(
        '--fmriprep_dir',
        type=str,
        default='/storage/connectome/haba6030/fmriprep_out_deoblique_v2',
        help='fMRIPrep output directory'
    )
    parser.add_argument(
        '--bids_dir',
        type=str,
        default='/storage/connectome/haba6030/colorBlind_data_deoblique',
        help='BIDS data directory'
    )
    parser.add_argument(
        '--output_dir',
        type=str,
        default='../results/reliability_check',
        help='Output directory'
    )
    parser.add_argument(
        '--smoothing_fwhm',
        type=float,
        default=6.0,
        help='Smoothing FWHM in mm (default: 6.0)'
    )
    parser.add_argument(
        '--confounds_strategy',
        type=str,
        default='motion',
        choices=['motion', 'motion_compcor', 'motion_compcor_scrub'],
        help='Confounds strategy'
    )

    return parser.parse_args()


def load_roi_mask(roi_name, derivatives_dir='/scratch/connectome/haba6030/colorBlind/derivatives'):
    """
    ROI mask 로드

    Parameters
    ----------
    roi_name : str
        ROI 이름 (V1, V2, V3, hV4)
    derivatives_dir : str
        Derivatives directory

    Returns
    -------
    roi_mask_img : Nifti1Image
        ROI mask image
    """
    # 기존 분석에서 사용한 ROI mask 찾기
    # 예: derivatives/BH2009_deoblique_v2/baseline81_deob_determin/sm6.0_*_V1_*/roi_mask.nii.gz

    roi_mask_pattern = f"*_{roi_name}_*/roi_mask.nii.gz"

    # Search in derivatives
    from glob import glob
    matches = glob(str(Path(derivatives_dir) / "BH2009_deoblique_v2" / "baseline81_deob_determin" / roi_mask_pattern))

    if not matches:
        raise FileNotFoundError(f"ROI mask for {roi_name} not found in {derivatives_dir}")

    roi_mask_file = matches[0]
    print(f"Loading ROI mask: {roi_mask_file}")

    roi_mask_img = image.load_img(roi_mask_file)
    return roi_mask_img


def load_confounds(subject_id, run_id, fmriprep_dir, strategy='motion'):
    """
    Confounds 로드

    Parameters
    ----------
    subject_id : str
        Subject ID
    run_id : int
        Run number (1-6)
    fmriprep_dir : str
        fMRIPrep output directory
    strategy : str
        Confounds strategy ('motion', 'motion_compcor', 'motion_compcor_scrub')

    Returns
    -------
    confounds : DataFrame
        Confounds dataframe
    """
    confounds_file = Path(fmriprep_dir) / f'sub-{subject_id}' / 'func' / \
                     f'sub-{subject_id}_task-rsvp_run-{run_id}_desc-confounds_timeseries.tsv'

    if not confounds_file.exists():
        raise FileNotFoundError(f"Confounds file not found: {confounds_file}")

    confounds_df = pd.read_csv(confounds_file, sep='\t')

    # Select confounds based on strategy
    if strategy == 'motion':
        confound_cols = [col for col in confounds_df.columns
                        if col.startswith('trans_') or col.startswith('rot_')]
    elif strategy == 'motion_compcor':
        motion_cols = [col for col in confounds_df.columns
                      if col.startswith('trans_') or col.startswith('rot_')]
        compcor_cols = [col for col in confounds_df.columns
                       if col.startswith('a_comp_cor_')][:5]  # First 5 aCompCor
        confound_cols = motion_cols + compcor_cols
    elif strategy == 'motion_compcor_scrub':
        motion_cols = [col for col in confounds_df.columns
                      if col.startswith('trans_') or col.startswith('rot_')]
        compcor_cols = [col for col in confounds_df.columns
                       if col.startswith('a_comp_cor_')][:5]
        framewise_displacement = ['framewise_displacement']
        confound_cols = motion_cols + compcor_cols + framewise_displacement

    confounds = confounds_df[confound_cols].fillna(0)
    return confounds


def compute_color_averaged_reliability(subject_id, roi_mask_img, fmriprep_dir,
                                       bids_dir, smoothing_fwhm=6.0,
                                       confounds_strategy='motion'):
    """
    Color-averaged reliability (기존 방법)

    Parameters
    ----------
    subject_id : str
        Subject ID
    roi_mask_img : Nifti1Image
        ROI mask
    fmriprep_dir : str
        fMRIPrep directory
    bids_dir : str
        BIDS directory
    smoothing_fwhm : float
        Smoothing FWHM
    confounds_strategy : str
        Confounds strategy

    Returns
    -------
    mean_reliability : float
        Mean split-half reliability
    correlations : dict
        Per-color correlations
    """
    print("\n" + "="*60)
    print("Computing Color-averaged Reliability (Baseline)")
    print("="*60)

    # Color names (8 colors)
    color_names = ['red', 'orange', 'yellow', 'green', 'cyan', 'blue', 'purple', 'magenta']

    # Store color betas per run
    color_betas = {color: [] for color in color_names}

    # Masker
    masker = NiftiMasker(mask_img=roi_mask_img, smoothing_fwhm=smoothing_fwhm,
                        standardize=True, detrend=True)

    for run_id in range(1, 7):
        print(f"\nProcessing run {run_id}...")

        # Load BOLD
        bold_file = Path(fmriprep_dir) / f'sub-{subject_id}' / 'func' / \
                    f'sub-{subject_id}_task-rsvp_run-{run_id}_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz'

        if not bold_file.exists():
            print(f"  Warning: BOLD file not found: {bold_file}")
            continue

        # Load events
        events_file = Path(bids_dir) / f'sub-{subject_id}' / 'func' / \
                     f'sub-{subject_id}_task-rsvp_run-{run_id}_events.tsv'

        if not events_file.exists():
            print(f"  Warning: Events file not found: {events_file}")
            continue

        events = pd.read_csv(events_file, sep='\t')

        # Load confounds
        confounds = load_confounds(subject_id, run_id, fmriprep_dir, confounds_strategy)

        # Fit GLM (standard, not LS-S)
        glm = FirstLevelModel(
            t_r=2.0,
            slice_time_ref=0.5,
            hrf_model='spm',
            drift_model='cosine',
            high_pass=1/128,
            smoothing_fwhm=None,  # Already smoothed by masker
            mask_img=roi_mask_img,
            minimize_memory=False
        )

        glm.fit(bold_file, events=events, confounds=confounds)

        # Extract beta for each color
        for color in color_names:
            try:
                beta_map = glm.compute_contrast(color, output_type='effect_size')
                beta_voxels = masker.fit_transform(beta_map).ravel()
                color_betas[color].append(beta_voxels)
            except Exception as e:
                print(f"  Warning: Failed to compute contrast for {color}: {e}")
                continue

    # Compute split-half reliability
    correlations = {}

    for color in color_names:
        if len(color_betas[color]) < 6:
            print(f"  Warning: {color} has only {len(color_betas[color])} runs")
            correlations[color] = np.nan
            continue

        betas_array = np.array(color_betas[color])  # (6, n_voxels)

        # Odd runs (1,3,5) vs Even runs (2,4,6)
        odd_runs = betas_array[[0, 2, 4]].mean(axis=0)
        even_runs = betas_array[[1, 3, 5]].mean(axis=0)

        corr = np.corrcoef(odd_runs, even_runs)[0, 1]
        correlations[color] = corr

        print(f"  {color:8s}: r = {corr:.3f}")

    # Mean reliability
    valid_corrs = [v for v in correlations.values() if not np.isnan(v)]
    mean_reliability = np.mean(valid_corrs) if valid_corrs else np.nan

    print(f"\n  Mean reliability: {mean_reliability:.3f}")

    return mean_reliability, correlations


def compute_trial_wise_reliability(subject_id, roi_mask_img, fmriprep_dir,
                                   bids_dir, smoothing_fwhm=6.0,
                                   confounds_strategy='motion'):
    """
    Trial-wise reliability (LS-S)

    Parameters
    ----------
    subject_id : str
        Subject ID
    roi_mask_img : Nifti1Image
        ROI mask
    fmriprep_dir : str
        fMRIPrep directory
    bids_dir : str
        BIDS directory
    smoothing_fwhm : float
        Smoothing FWHM
    confounds_strategy : str
        Confounds strategy

    Returns
    -------
    mean_reliability : float
        Mean split-half reliability
    correlations : dict
        Per-color correlations
    """
    print("\n" + "="*60)
    print("Computing Trial-wise Reliability (LS-S)")
    print("="*60)

    # Masker
    masker = NiftiMasker(mask_img=roi_mask_img, smoothing_fwhm=smoothing_fwhm,
                        standardize=True, detrend=True)

    # Store all trials
    all_trial_betas = []
    all_trial_labels = []
    all_trial_runs = []

    for run_id in range(1, 7):
        print(f"\nProcessing run {run_id}...")

        # Load BOLD
        bold_file = Path(fmriprep_dir) / f'sub-{subject_id}' / 'func' / \
                    f'sub-{subject_id}_task-rsvp_run-{run_id}_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz'

        if not bold_file.exists():
            print(f"  Warning: BOLD file not found")
            continue

        # Load events
        events_file = Path(bids_dir) / f'sub-{subject_id}' / 'func' / \
                     f'sub-{subject_id}_task-rsvp_run-{run_id}_events.tsv'

        if not events_file.exists():
            print(f"  Warning: Events file not found")
            continue

        events = pd.read_csv(events_file, sep='\t')

        # Filter color trials only
        color_events = events[events['trial_type'] != 'gray'].reset_index(drop=True)
        n_trials = len(color_events)

        print(f"  Found {n_trials} color trials")

        # Load confounds
        confounds = load_confounds(subject_id, run_id, fmriprep_dir, confounds_strategy)

        # LS-S GLM: Each trial separately
        for trial_idx in range(n_trials):
            # Create trial-specific design
            trial_events = color_events.copy()

            # Mark target trial
            trial_events['trial_type_lss'] = 'other'
            trial_events.loc[trial_idx, 'trial_type_lss'] = 'target'

            # Keep original trial_type for nuisance modeling
            target_color = trial_events.loc[trial_idx, 'trial_type']

            # Separate nuisances
            # 1. Target trial
            # 2. Same color trials (nuisance)
            # 3. Different color trials (nuisance)
            trial_events['trial_type_nuisance'] = trial_events['trial_type']
            trial_events.loc[trial_idx, 'trial_type_nuisance'] = 'target'

            # Create events for GLM
            lss_events = trial_events[['onset', 'duration', 'trial_type_lss']].copy()
            lss_events.columns = ['onset', 'duration', 'trial_type']

            # Fit GLM
            glm = FirstLevelModel(
                t_r=2.0,
                slice_time_ref=0.5,
                hrf_model='spm',
                drift_model='cosine',
                high_pass=1/128,
                smoothing_fwhm=None,
                mask_img=roi_mask_img,
                minimize_memory=False
            )

            glm.fit(bold_file, events=lss_events, confounds=confounds)

            # Extract beta for target trial
            try:
                beta_map = glm.compute_contrast('target', output_type='effect_size')
                beta_voxels = masker.fit_transform(beta_map).ravel()

                all_trial_betas.append(beta_voxels)
                all_trial_labels.append(target_color)
                all_trial_runs.append(run_id)
            except Exception as e:
                print(f"  Warning: Failed for trial {trial_idx}: {e}")
                continue

        print(f"  Extracted {len([r for r in all_trial_runs if r == run_id])} trials")

    # Convert to arrays
    trial_betas = np.array(all_trial_betas)  # (n_trials, n_voxels)
    trial_labels = np.array(all_trial_labels)
    trial_runs = np.array(all_trial_runs)

    print(f"\nTotal trials extracted: {len(trial_betas)}")
    print(f"Shape: {trial_betas.shape}")

    # Compute split-half reliability per color
    unique_colors = np.unique(trial_labels)
    correlations = {}

    for color in unique_colors:
        color_mask = trial_labels == color
        color_betas = trial_betas[color_mask]
        color_runs = trial_runs[color_mask]

        # Odd runs vs Even runs
        odd_mask = np.isin(color_runs, [1, 3, 5])
        even_mask = np.isin(color_runs, [2, 4, 6])

        if odd_mask.sum() == 0 or even_mask.sum() == 0:
            print(f"  {color:8s}: Insufficient data")
            correlations[color] = np.nan
            continue

        odd_avg = color_betas[odd_mask].mean(axis=0)
        even_avg = color_betas[even_mask].mean(axis=0)

        corr = np.corrcoef(odd_avg, even_avg)[0, 1]
        correlations[color] = corr

        print(f"  {color:8s}: r = {corr:.3f} (n_odd={odd_mask.sum()}, n_even={even_mask.sum()})")

    # Mean reliability
    valid_corrs = [v for v in correlations.values() if not np.isnan(v)]
    mean_reliability = np.mean(valid_corrs) if valid_corrs else np.nan

    print(f"\n  Mean reliability: {mean_reliability:.3f}")

    return mean_reliability, correlations


def make_decision(rel_color_avg, rel_trial_wise):
    """
    의사결정 로직

    Parameters
    ----------
    rel_color_avg : float
        Color-averaged reliability
    rel_trial_wise : float
        Trial-wise reliability

    Returns
    -------
    decision : str
        Decision code
    message : str
        Decision message
    """
    print("\n" + "="*60)
    print("Decision")
    print("="*60)
    print(f"Color-averaged: {rel_color_avg:.3f}")
    print(f"Trial-wise:     {rel_trial_wise:.3f}")
    print(f"Difference:     {rel_trial_wise - rel_color_avg:+.3f}")
    print("-" * 60)

    if np.isnan(rel_color_avg) or np.isnan(rel_trial_wise):
        decision = "ERROR"
        message = "❌ ERROR: Failed to compute reliability"

    elif rel_color_avg < 0.3:
        decision = "STOP"
        message = """❌ CRITICAL: Color-averaged reliability < 0.3
   → Data quality 자체 문제
   → Action: Check preprocessing (alignment, smoothing, confounds)
   → DO NOT proceed to hyperalignment"""

    elif rel_color_avg >= 0.5 and rel_trial_wise < 0.3:
        decision = "IMPROVE_GLM"
        message = """⚠️ WARNING: Color-averaged good BUT trial-wise poor
   → SNR 문제 (single-trial estimation unreliable)
   → Action:
      1. Increase smoothing (6mm → 8mm)
      2. Add more confounds (motion + CompCor)
      3. Regularization in GLM
   → Re-run trial-wise GLM with adjustments"""

    elif rel_trial_wise >= 0.3 and rel_trial_wise < (rel_color_avg - 0.1):
        decision = "PROCEED_WITH_CAUTION"
        message = f"""⚠️ CAUTION: Trial-wise lower than color-averaged (expected)
   → Color-averaged: {rel_color_avg:.3f}
   → Trial-wise:     {rel_trial_wise:.3f}
   → Drop: {rel_color_avg - rel_trial_wise:.3f}
   → This is normal (single-trial has more noise)
   → Action: Proceed to pilot GPA with regularization"""

    elif rel_trial_wise >= 0.4:
        decision = "PROCEED"
        message = f"""✅ EXCELLENT: Trial-wise reliability high
   → Trial-wise: {rel_trial_wise:.3f}
   → Action: Proceed to pilot hyperalignment"""

    else:
        decision = "PROCEED_WITH_CAUTION"
        message = f"""⚠️ BORDERLINE: Trial-wise reliability marginal
   → Trial-wise: {rel_trial_wise:.3f}
   → Action: Proceed to pilot, monitor closely"""

    print(message)
    print(f"\n✨ Recommendation: {decision}")
    print("="*60 + "\n")

    return decision, message


def main():
    """메인 함수"""
    args = parse_args()

    print("\n" + "="*80)
    print("Step 1.2: Reliability Comparison")
    print("="*80)
    print(f"Subject: {args.subject}")
    print(f"ROI: {args.roi}")
    print(f"Smoothing: {args.smoothing_fwhm} mm")
    print(f"Confounds: {args.confounds_strategy}")
    print("="*80)

    # Output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load ROI mask
    try:
        roi_mask_img = load_roi_mask(args.roi)
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("Please create ROI mask first (from baseline analysis)")
        return

    # Part A: Color-averaged reliability
    rel_color_avg, corrs_color_avg = compute_color_averaged_reliability(
        args.subject,
        roi_mask_img,
        args.fmriprep_dir,
        args.bids_dir,
        args.smoothing_fwhm,
        args.confounds_strategy
    )

    # Part B: Trial-wise reliability
    rel_trial_wise, corrs_trial_wise = compute_trial_wise_reliability(
        args.subject,
        roi_mask_img,
        args.fmriprep_dir,
        args.bids_dir,
        args.smoothing_fwhm,
        args.confounds_strategy
    )

    # Part C: Decision
    decision, message = make_decision(rel_color_avg, rel_trial_wise)

    # Save results
    results = {
        'subject': args.subject,
        'roi': args.roi,
        'smoothing_fwhm': args.smoothing_fwhm,
        'confounds_strategy': args.confounds_strategy,
        'color_averaged': {
            'mean_reliability': float(rel_color_avg) if not np.isnan(rel_color_avg) else None,
            'per_color': {k: float(v) if not np.isnan(v) else None
                         for k, v in corrs_color_avg.items()}
        },
        'trial_wise': {
            'mean_reliability': float(rel_trial_wise) if not np.isnan(rel_trial_wise) else None,
            'per_color': {k: float(v) if not np.isnan(v) else None
                         for k, v in corrs_trial_wise.items()}
        },
        'decision': decision,
        'decision_message': message
    }

    output_file = output_dir / f'reliability_sub-{args.subject}_{args.roi}.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n✅ Results saved: {output_file}")


if __name__ == '__main__':
    main()
