#!/usr/bin/env python3
"""
Step 1.3: Trial-wise Beta Extraction using LS-S GLM

목적:
- Stimulus-wise beta 추출 (384 trials per subject-ROI)
- LS-S (Least-Squares Separate) 방법으로 각 trial 독립적으로 추정
- Trial metadata 및 quality metrics 저장

사용법:
    python 02_trial_wise_glm.py --subject 01 --roi V1

Date: 2026-01-08
"""

import argparse
import numpy as np
import pandas as pd
from pathlib import Path
import json
import nibabel as nib
from nilearn.glm.first_level import FirstLevelModel
from nilearn.maskers import NiftiMasker
from nilearn import image
from scipy.spatial import procrustes
from scipy.spatial.distance import pdist, squareform
from scipy.stats import spearmanr
import warnings
warnings.filterwarnings('ignore', category=UserWarning)


def parse_args():
    """커맨드라인 인자 파싱"""
    parser = argparse.ArgumentParser(
        description='Step 1.3: Trial-wise beta extraction (LS-S GLM)'
    )
    parser.add_argument(
        '--subject',
        type=str,
        required=True,
        help='Subject ID (e.g., 01)'
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
        default='/storage/connectome/haba6030/fmriprep_out_original_v3',
        help='fMRIPrep output directory'
    )
    parser.add_argument(
        '--bids_dir',
        type=str,
        default='/storage/connectome/haba6030/bids_editted',
        help='BIDS data directory'
    )
    parser.add_argument(
        '--derivatives_dir',
        type=str,
        default='/scratch/connectome/haba6030/colorBlind/derivatives',
        help='Derivatives directory (for ROI masks)'
    )
    parser.add_argument(
        '--output_dir',
        type=str,
        default='/scratch/connectome/haba6030/colorBlind/prediction_model_workspace/results/trial_wise_glm',
        help='Output directory'
    )
    parser.add_argument(
        '--smoothing_fwhm',
        type=float,
        default=0.0,
        help='Smoothing FWHM in mm (default: 0.0, matching Phase 0)'
    )
    parser.add_argument(
        '--confounds_strategy',
        type=str,
        default='motion',
        choices=['motion', 'motion_compcor'],
        help='Confounds strategy'
    )

    return parser.parse_args()


def load_roi_mask(subject_id, roi_name, derivatives_dir):
    """
    ROI mask 로드 (V3_Comprehensive 구조)

    Parameters
    ----------
    subject_id : str
        Subject ID
    roi_name : str
        ROI name
    derivatives_dir : str
        Derivatives directory

    Returns
    -------
    roi_mask_img : Nifti1Image
        ROI mask image
    """
    roi_mask_file = Path(derivatives_dir) / "V3_Comprehensive" / "ROI_mask" / \
                    f"sub-{subject_id}" / "roi_pipeline" / \
                    f"{roi_name}_mask_thr50_intnearest_binTrue_maskfunc_gmTrue_subjFalse.nii.gz"

    if not roi_mask_file.exists():
        raise FileNotFoundError(
            f"ROI mask not found: {roi_mask_file}\n"
            f"Expected: derivatives/V3_Comprehensive/ROI_mask/sub-{subject_id}/roi_pipeline/"
        )

    print(f"Loading ROI mask: {roi_mask_file}")
    roi_mask_img = image.load_img(str(roi_mask_file))

    # Get voxel count
    mask_data = roi_mask_img.get_fdata()
    n_voxels = int(np.sum(mask_data > 0))
    print(f"  Number of voxels in ROI: {n_voxels}")

    return roi_mask_img, n_voxels


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
        fMRIPrep directory
    strategy : str
        Confounds strategy

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
        acomp_cols = [col for col in confounds_df.columns
                     if col.startswith('a_comp_cor_')][:5]  # First 5 aCompCor
        confound_cols = motion_cols + acomp_cols

    confounds = confounds_df[confound_cols].fillna(0)
    return confounds


def extract_trial_wise_betas(subject_id, roi_mask_img, fmriprep_dir, bids_dir,
                             smoothing_fwhm=6.0, confounds_strategy='motion'):
    """
    LS-S GLM으로 trial-wise beta 추출

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
    trial_betas : ndarray
        (n_trials, n_voxels) trial-wise betas
    trial_metadata : DataFrame
        Trial metadata (trial_idx, color, run, stimulus_id, onset, duration)
    """
    print("\n" + "="*70)
    print("LS-S GLM: Extracting Trial-wise Betas")
    print("="*70)

    # Masker setup (extraction only, no preprocessing)
    masker = NiftiMasker(
        mask_img=roi_mask_img,
        smoothing_fwhm=None,  # Smoothing done by GLM
        standardize=False,
        detrend=False
    )
    masker.fit()
    print("✓ Masker initialized")

    # Storage
    all_trial_betas = []
    all_trial_metadata = []

    # Color trial types (CRITICAL: use color_1 to color_8, NOT red/orange/etc)
    color_names = ['color_1', 'color_2', 'color_3', 'color_4',
                   'color_5', 'color_6', 'color_7', 'color_8']

    # Process each run
    for run_id in range(1, 7):
        print(f"\n{'─'*70}")
        print(f"Processing Run {run_id}/6")
        print(f"{'─'*70}")

        # Load BOLD data
        bold_file = Path(fmriprep_dir) / f'sub-{subject_id}' / 'func' / \
                    f'sub-{subject_id}_task-rsvp_run-{run_id}_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz'

        if not bold_file.exists():
            print(f"  ⚠️ BOLD file not found: {bold_file}")
            continue

        print(f"  Loading BOLD: {bold_file.name}")

        # Load events
        events_file = Path(bids_dir) / f'sub-{subject_id}' / 'func' / \
                     f'sub-{subject_id}_task-rsvp_run-{run_id}_events.tsv'

        if not events_file.exists():
            print(f"  ⚠️ Events file not found: {events_file}")
            continue

        events = pd.read_csv(events_file, sep='\t')

        # Filter color trials only (exclude gray)
        color_events = events[events['trial_type'].isin(color_names)].reset_index(drop=True)
        n_trials_in_run = len(color_events)

        print(f"  Color trials in run: {n_trials_in_run}")

        # Load confounds
        confounds = load_confounds(subject_id, run_id, fmriprep_dir, confounds_strategy)
        print(f"  Confounds loaded: {confounds.shape[1]} regressors")

        # LS-S: Process each trial separately
        print(f"  Starting LS-S GLM for {n_trials_in_run} trials...")

        for trial_idx in range(n_trials_in_run):
            if (trial_idx + 1) % 10 == 0 or trial_idx == 0:
                print(f"    Trial {trial_idx + 1}/{n_trials_in_run}...", end='\r')

            # Get target trial info
            target_trial = color_events.iloc[trial_idx]
            target_color = target_trial['trial_type']
            target_onset = target_trial['onset']
            target_duration = target_trial['duration']

            # Create LS-S design matrix
            # Key: Target trial separate, all others grouped as "nuisance"
            lss_events = color_events.copy()
            lss_events['trial_type_original'] = lss_events['trial_type']

            # Mark target trial
            lss_events['trial_type'] = 'nuisance'
            lss_events.loc[trial_idx, 'trial_type'] = 'target'

            # Keep only necessary columns for GLM
            lss_events_glm = lss_events[['onset', 'duration', 'trial_type']].copy()

            # Fit GLM with LS-S design
            glm = FirstLevelModel(
                t_r=2.0,
                slice_time_ref=0.5,
                hrf_model='spm',
                drift_model='cosine',
                high_pass=1/128,  # 128s high-pass filter
                smoothing_fwhm=smoothing_fwhm,
                mask_img=roi_mask_img,
                minimize_memory=False,
                verbose=0
            )

            glm.fit(bold_file, events=lss_events_glm, confounds=confounds)

            # Extract beta for target trial
            try:
                beta_map = glm.compute_contrast('target', output_type='effect_size')
                beta_voxels = masker.transform(beta_map).ravel()

                # Store beta
                all_trial_betas.append(beta_voxels)

                # Store metadata
                metadata = {
                    'trial_idx': len(all_trial_betas) - 1,  # Global trial index
                    'run': run_id,
                    'trial_in_run': trial_idx,
                    'color': target_color,
                    'onset': target_onset,
                    'duration': target_duration
                }
                all_trial_metadata.append(metadata)

            except Exception as e:
                print(f"\n    ⚠️ Failed for trial {trial_idx}: {e}")
                continue

        print(f"    Trial {n_trials_in_run}/{n_trials_in_run}... Done!")
        print(f"  ✓ Run {run_id} completed: {n_trials_in_run} trials extracted")

    # Convert to arrays
    trial_betas = np.array(all_trial_betas)
    trial_metadata = pd.DataFrame(all_trial_metadata)

    print(f"\n{'='*70}")
    print(f"✓ Extraction complete!")
    print(f"  Total trials: {len(trial_betas)}")
    print(f"  Shape: {trial_betas.shape}")
    print(f"{'='*70}")

    return trial_betas, trial_metadata


def compute_quality_metrics(trial_betas, trial_metadata):
    """
    Quality metrics 계산

    Parameters
    ----------
    trial_betas : ndarray
        (n_trials, n_voxels)
    trial_metadata : DataFrame
        Trial metadata

    Returns
    -------
    metrics : dict
        Quality metrics
    """
    print("\n" + "="*70)
    print("Computing Quality Metrics")
    print("="*70)

    # Check if any trials were extracted
    if len(trial_metadata) == 0 or len(trial_betas) == 0:
        print("❌ ERROR: No trials extracted. Cannot compute metrics.")
        return None

    metrics = {}

    # 1. Split-half reliability (run-based)
    print("\n1. Split-half reliability (Procrustes):")

    odd_runs = trial_metadata['run'].isin([1, 3, 5])
    even_runs = trial_metadata['run'].isin([2, 4, 6])

    # Per-color reliability
    color_reliabilities = {}
    colors = trial_metadata['color'].unique()

    for color in sorted(colors):
        color_mask = trial_metadata['color'] == color

        # Odd runs for this color
        odd_trials = trial_betas[color_mask & odd_runs]
        even_trials = trial_betas[color_mask & even_runs]

        if len(odd_trials) > 0 and len(even_trials) > 0:
            # Average across trials
            odd_avg = odd_trials.mean(axis=0)
            even_avg = even_trials.mean(axis=0)

            # Procrustes stability
            _, _, disparity = procrustes(
                odd_avg.reshape(-1, 1),
                even_avg.reshape(-1, 1)
            )
            stability = 1.0 - disparity
            color_reliabilities[color] = float(stability)

            print(f"  {color:10s}: {stability:.3f}")

    mean_reliability = np.mean(list(color_reliabilities.values()))
    print(f"  {'Mean':10s}: {mean_reliability:.3f}")

    metrics['split_half_reliability'] = {
        'by_color': color_reliabilities,
        'mean': float(mean_reliability)
    }

    # 1b. RDM-based reliability (more robust for single trials)
    print("\n1b. RDM-based split-half reliability:")

    # Compute color-averaged patterns for odd and even runs
    odd_patterns = []
    even_patterns = []
    for color in sorted(colors):
        color_mask = trial_metadata['color'] == color

        odd_trials = trial_betas[color_mask & odd_runs]
        even_trials = trial_betas[color_mask & even_runs]

        if len(odd_trials) > 0 and len(even_trials) > 0:
            odd_patterns.append(odd_trials.mean(axis=0))
            even_patterns.append(even_trials.mean(axis=0))

    if len(odd_patterns) >= 2 and len(even_patterns) >= 2:
        odd_patterns = np.array(odd_patterns)  # (n_colors, n_voxels)
        even_patterns = np.array(even_patterns)

        # Compute RDMs (correlation distance)
        rdm_odd = squareform(pdist(odd_patterns, metric='correlation'))
        rdm_even = squareform(pdist(even_patterns, metric='correlation'))

        # Get upper triangle indices (excluding diagonal)
        triu_idx = np.triu_indices_from(rdm_odd, k=1)
        rdm_odd_vec = rdm_odd[triu_idx]
        rdm_even_vec = rdm_even[triu_idx]

        # Spearman correlation between RDMs
        rdm_corr, rdm_pval = spearmanr(rdm_odd_vec, rdm_even_vec)

        print(f"  RDM Spearman r: {rdm_corr:.3f} (p={rdm_pval:.3e})")
        print(f"  Colors used: {len(odd_patterns)}")

        metrics['rdm_reliability'] = {
            'spearman_r': float(rdm_corr),
            'p_value': float(rdm_pval),
            'n_colors': len(odd_patterns)
        }
    else:
        print("  ❌ Insufficient colors for RDM computation")
        metrics['rdm_reliability'] = None

    # 2. SNR estimation (temporal SNR)
    print("\n2. Temporal SNR:")
    temporal_snr = trial_betas.mean(axis=0) / (trial_betas.std(axis=0) + 1e-10)
    mean_snr = float(np.mean(temporal_snr))
    median_snr = float(np.median(temporal_snr))

    print(f"  Mean tSNR: {mean_snr:.2f}")
    print(f"  Median tSNR: {median_snr:.2f}")

    metrics['temporal_snr'] = {
        'mean': mean_snr,
        'median': median_snr,
        'std': float(np.std(temporal_snr))
    }

    # 3. Trial count per color
    print("\n3. Trial counts per color:")
    trial_counts = trial_metadata['color'].value_counts().to_dict()
    for color, count in sorted(trial_counts.items()):
        print(f"  {color:10s}: {count}")

    metrics['trial_counts'] = trial_counts
    metrics['total_trials'] = len(trial_betas)

    print(f"\n{'='*70}")

    return metrics


def main():
    """Main execution"""
    args = parse_args()

    print("\n" + "="*70)
    print("Step 1.3: Trial-wise Beta Extraction (LS-S GLM)")
    print("="*70)
    print(f"Subject: sub-{args.subject}")
    print(f"ROI: {args.roi}")
    print(f"Smoothing: {args.smoothing_fwhm}mm FWHM")
    print(f"Confounds: {args.confounds_strategy}")
    print("="*70)

    # Output directory
    output_dir = Path(args.output_dir) / 'original_v3' / f'sub-{args.subject}_{args.roi}'
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nOutput directory: {output_dir}")

    # Load ROI mask
    try:
        roi_mask_img, n_voxels = load_roi_mask(
            args.subject, args.roi, args.derivatives_dir
        )
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        return 1

    # Extract trial-wise betas
    try:
        trial_betas, trial_metadata = extract_trial_wise_betas(
            args.subject,
            roi_mask_img,
            args.fmriprep_dir,
            args.bids_dir,
            args.smoothing_fwhm,
            args.confounds_strategy
        )
    except Exception as e:
        print(f"\n❌ Error during extraction: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Compute quality metrics
    metrics = compute_quality_metrics(trial_betas, trial_metadata)

    if metrics is None:
        print(f"\n❌ ERROR: No trials extracted. Cannot save results.")
        return 1

    # Save results
    print(f"\n{'='*70}")
    print("Saving Results")
    print(f"{'='*70}")

    # 1. Trial-wise betas
    betas_file = output_dir / 'stimulus_wise_betas.npy'
    np.save(betas_file, trial_betas)
    print(f"✓ Saved: {betas_file.name}")
    print(f"  Shape: {trial_betas.shape}")

    # 2. Trial metadata
    metadata_file = output_dir / 'trial_metadata.csv'
    trial_metadata.to_csv(metadata_file, index=False)
    print(f"✓ Saved: {metadata_file.name}")
    print(f"  Rows: {len(trial_metadata)}")

    # 3. Quality metrics
    metrics['subject_id'] = args.subject
    metrics['roi'] = args.roi
    metrics['n_voxels'] = int(n_voxels)
    metrics['smoothing_fwhm'] = float(args.smoothing_fwhm)
    metrics['confounds_strategy'] = args.confounds_strategy

    metrics_file = output_dir / 'quality_metrics.json'
    with open(metrics_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"✓ Saved: {metrics_file.name}")

    print(f"\n{'='*70}")
    print("✓ Step 1.3 Complete!")
    print(f"{'='*70}")

    # Summary
    print("\n📊 Summary:")
    print(f"  Subject: sub-{args.subject}")
    print(f"  ROI: {args.roi}")
    print(f"  Trials extracted: {len(trial_betas)}")
    print(f"  Voxels: {n_voxels}")
    print(f"  Split-half reliability: {metrics['split_half_reliability']['mean']:.3f}")
    print(f"  Mean tSNR: {metrics['temporal_snr']['mean']:.2f}")

    # Decision
    reliability = metrics['split_half_reliability']['mean']
    print(f"\n🎯 Decision:")
    if reliability >= 0.50:
        print(f"  ✅ PROCEED to Step 1.4 (reliability = {reliability:.3f})")
    else:
        print(f"  ⚠️ LOW RELIABILITY (reliability = {reliability:.3f})")
        print(f"  → Consider increasing smoothing or adjusting preprocessing")

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
