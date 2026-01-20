#!/usr/bin/env python3
"""
Step 1.3: Trial-wise Beta Extraction using Phase 0 Methodology

KEY CHANGE: Uses Phase 0 data-driven HRF and voxel selection
----------------------------------------------------------
Phase 0 baseline method (analysis/phase1_preprocess_decoding/):
1. FIR-based data-driven HRF estimation (8 delays, 12s window)
2. Voxel selection: top 50% by FIR R²
3. ROI-specific HRF (per subject, per ROI)
4. 2nd-level GLM with HRF + derivative

This script applies Phase 0's methodology to trial-wise extraction:
- Uses ROI-specific data-driven HRF from Phase 0
- Applies voxel selection mask from Phase 0
- Matches Phase 0 preprocessing (high_pass=0.01, HRF+derivative)

Expected improvement: 0.004 → 0.3~0.5 Procrustes stability

Usage:
    python 02_trial_wise_glm_phase0hrf.py --subject 01 --roi V1

Date: 2026-01-11
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

# Import Phase 0 HRF loader
from utils_phase0_hrf import (
    load_phase0_hrf,
    load_phase0_voxel_mask,
    create_selected_voxels_mask_img,
    get_phase0_summary
)


def parse_args():
    """커맨드라인 인자 파싱"""
    parser = argparse.ArgumentParser(
        description='Step 1.3: Trial-wise GLM with Phase 0 methodology'
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
        help='BIDS directory with event files'
    )
    parser.add_argument(
        '--derivatives_dir',
        type=str,
        default='/scratch/connectome/haba6030/colorBlind/derivatives',
        help='Derivatives directory (for both ROI masks and Phase 0 results)'
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
        default='cosine',
        choices=['cosine', 'motion', 'motion_acompcor'],
        help='Confounds strategy (default: cosine, matching Phase 0)'
    )
    parser.add_argument(
        '--phase0_dataset',
        type=str,
        default='original_v3',
        help='Phase 0 dataset name (default: original_v3, from comprehensive analysis)'
    )
    parser.add_argument(
        '--phase0_timestamp',
        type=str,
        default='baseline32_original_v3',
        help='Phase 0 timestamp (default: baseline32_original_v3, from comprehensive analysis)'
    )

    return parser.parse_args()


def load_roi_mask(subject_id, roi_name, derivatives_dir):
    """ROI mask 로딩"""
    roi_mask_file = Path(derivatives_dir) / "V3_Comprehensive" / "ROI_mask" / \
                    f"sub-{subject_id}" / "roi_pipeline" / \
                    f"{roi_name}_mask_thr50_intnearest_binTrue_maskfunc_gmTrue_subjFalse.nii.gz"

    if not roi_mask_file.exists():
        raise FileNotFoundError(f"ROI mask not found: {roi_mask_file}")

    return str(roi_mask_file)


def load_confounds(subject_id, run_id, fmriprep_dir, strategy='cosine'):
    """
    Confounds 로딩

    Strategies:
    - 'cosine': Cosine basis functions for drift removal (matches Phase 0)
    - 'motion': 6 motion parameters (trans_x/y/z, rot_x/y/z)
    - 'motion_acompcor': Motion + 5 aCompCor components

    Reference Phase 0: analysis/phase1_preprocess_decoding/fir_reconstruction_BH2009_system_clean.py
    - motion='cosine' → cosine basis functions (cosine00~cosine04)
    """
    confounds_file = Path(fmriprep_dir) / f'sub-{subject_id}' / 'func' / \
                    f'sub-{subject_id}_task-rsvp_run-{run_id}_desc-confounds_timeseries.tsv'

    confounds_df = pd.read_csv(confounds_file, sep='\t')

    if strategy == 'cosine':
        # ✅ Match Phase 0: cosine basis functions for drift removal
        # Phase 0 uses 5 cosine basis functions (cosine00~cosine04)
        cosine_cols = [f'cosine{i:02d}' for i in range(5)]
        available_cols = [col for col in cosine_cols if col in confounds_df.columns]

        if len(available_cols) == 0:
            # Fallback: try different naming
            cosine_cols_alt = [col for col in confounds_df.columns if col.startswith('cosine')]
            if len(cosine_cols_alt) > 0:
                available_cols = sorted(cosine_cols_alt)[:5]  # Take first 5

        if len(available_cols) == 0:
            raise ValueError(f"No cosine basis functions found in confounds file: {confounds_file}")

        selected_confounds = confounds_df[available_cols].fillna(0)

    elif strategy == 'motion':
        motion_cols = [col for col in confounds_df.columns if col.startswith('trans_') or col.startswith('rot_')]
        selected_confounds = confounds_df[motion_cols].fillna(0)

    elif strategy == 'motion_acompcor':
        motion_cols = [col for col in confounds_df.columns if col.startswith('trans_') or col.startswith('rot_')]
        acompcor_cols = [col for col in confounds_df.columns if col.startswith('a_comp_cor_')][:5]
        selected_confounds = confounds_df[motion_cols + acompcor_cols].fillna(0)

    else:
        raise ValueError(f"Unknown confounds strategy: {strategy}")

    return selected_confounds


def extract_trial_betas_phase0method(
    subject_id, roi_name, fmriprep_dir, bids_dir,
    selected_voxels_mask_img, smoothing_fwhm=0.0, confounds_strategy='motion'
):
    """
    Trial-wise beta extraction using Phase 0 methodology

    Key differences from previous version:
    1. Uses selected voxels only (top 50% by FIR R² from Phase 0)
    2. Uses HRF + derivative (matching Phase 0's 2nd-level GLM)
    3. high_pass = 0.01 Hz (matching Phase 0)

    Reference: analysis/phase1_preprocess_decoding/fir_reconstruction_BH2009_system_clean.py
    """
    print("\n" + "="*70)
    print(f"Extracting trial-wise betas: sub-{subject_id} {roi_name}")
    print(f"Method: Phase 0 methodology (HRF+derivative, selected voxels)")
    print(f"Smoothing: {smoothing_fwhm}mm FWHM")
    print(f"Confounds: {confounds_strategy}")
    print("="*70)

    # Color names (matching event files)
    color_names = ['color_1', 'color_2', 'color_3', 'color_4',
                   'color_5', 'color_6', 'color_7', 'color_8']

    # Initialize masker with selected voxels mask
    masker = NiftiMasker(
        mask_img=selected_voxels_mask_img,
        smoothing_fwhm=None,
        standardize=False,
        detrend=False
    )
    masker.fit()

    all_trial_betas = []
    all_trial_metadata = []

    # Process each run
    for run_id in range(1, 7):
        print(f"\n[Run {run_id}/6]")

        # BOLD file
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

        # Filter color trials only
        color_events = events[events['trial_type'].isin(color_names)].reset_index(drop=True)
        n_trials_in_run = len(color_events)

        print(f"  Color trials in run: {n_trials_in_run}")

        if n_trials_in_run == 0:
            print(f"  ⚠️ No color trials found in run {run_id}")
            continue

        # Load confounds
        confounds = load_confounds(subject_id, run_id, fmriprep_dir, confounds_strategy)
        print(f"  Confounds loaded: {confounds.shape[1]} regressors")

        # Create design matrix with separate regressor per trial
        print(f"  Creating design matrix with {n_trials_in_run} trial regressors...")

        # Modify events to have unique trial names
        events_per_trial = color_events.copy()
        events_per_trial['trial_type'] = [f'trial_{i:03d}' for i in range(n_trials_in_run)]

        # **GLM with Phase 0 settings**
        print(f"  Fitting GLM (Phase 0 method: HRF+derivative, high_pass=0.01)...")
        glm = FirstLevelModel(
            t_r=2.0,
            slice_time_ref=0.5,
            hrf_model='spm + derivative',  # ✅ Match Phase 0 (HRF + derivative)
            drift_model='cosine',
            high_pass=0.01,  # ✅ Match Phase 0 (was 1/128=0.0078)
            smoothing_fwhm=smoothing_fwhm,
            mask_img=selected_voxels_mask_img,  # ✅ Selected voxels only
            minimize_memory=False,
            verbose=0
        )

        glm.fit(bold_file, events=events_per_trial, confounds=confounds)
        print(f"  ✓ GLM fitted!")

        # Extract beta for each trial
        print(f"  Extracting {n_trials_in_run} trial betas...")
        for trial_idx in range(n_trials_in_run):
            if (trial_idx + 1) % 20 == 0 or trial_idx == 0:
                print(f"    Trial {trial_idx + 1}/{n_trials_in_run}...", end='\r')

            trial_name = f'trial_{trial_idx:03d}'
            target_trial = color_events.iloc[trial_idx]

            try:
                # Extract beta (HRF regressor only, not derivative)
                beta_map = glm.compute_contrast(trial_name, output_type='effect_size')
                beta_voxels = masker.transform(beta_map).ravel()

                # Store beta
                all_trial_betas.append(beta_voxels)

                # Store metadata
                metadata = {
                    'trial_idx': len(all_trial_betas) - 1,
                    'run': run_id,
                    'trial_in_run': trial_idx,
                    'color': target_trial['trial_type'],
                    'onset': target_trial['onset'],
                    'duration': target_trial['duration']
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
    print(f"  Unique colors: {len(trial_metadata['color'].unique())}")
    print(f"  Beta shape: {trial_betas.shape}")
    print(f"  Voxels used: {trial_betas.shape[1]} (Phase 0 selected voxels)")

    # Diagnostic: Check trial distribution
    print(f"\n📊 Trial Distribution Diagnostic:")
    if len(trial_metadata) > 0:
        # By color
        print(f"  By color:")
        for color in sorted(trial_metadata['color'].unique()):
            count = (trial_metadata['color'] == color).sum()
            print(f"    {color:10s}: {count:3d} trials")

        # By run
        print(f"  By run:")
        for run in sorted(trial_metadata['run'].unique()):
            count = (trial_metadata['run'] == run).sum()
            print(f"    Run {run}: {count:2d} trials")

        # Odd/Even split balance
        odd_count = trial_metadata['run'].isin([1, 3, 5]).sum()
        even_count = trial_metadata['run'].isin([2, 4, 6]).sum()
        print(f"  Split balance:")
        print(f"    Odd runs (1,3,5):  {odd_count:3d} trials")
        print(f"    Even runs (2,4,6): {even_count:3d} trials")
        print(f"    Balance ratio: {min(odd_count, even_count)/max(odd_count, even_count):.2f}")

    print("="*70)

    return trial_betas, trial_metadata


def compute_quality_metrics(trial_betas, trial_metadata):
    """Quality metrics 계산 (identical to original)"""
    print("\n" + "="*70)
    print("Computing Quality Metrics")
    print("="*70)

    if len(trial_metadata) == 0 or len(trial_betas) == 0:
        print("❌ ERROR: No trials extracted. Cannot compute metrics.")
        return None

    metrics = {}

    # 1. Procrustes-based split-half reliability (PRIMARY METRIC)
    print("\n1. Procrustes-based split-half reliability (PRIMARY):")

    odd_runs = trial_metadata['run'].isin([1, 3, 5])
    even_runs = trial_metadata['run'].isin([2, 4, 6])

    color_reliabilities = {}
    colors = trial_metadata['color'].unique()

    colors_with_both_splits = 0
    for color in sorted(colors):
        color_mask = trial_metadata['color'] == color

        odd_trials = trial_betas[color_mask & odd_runs]
        even_trials = trial_betas[color_mask & even_runs]

        if len(odd_trials) > 0 and len(even_trials) > 0:
            colors_with_both_splits += 1
            odd_avg = odd_trials.mean(axis=0)
            even_avg = even_trials.mean(axis=0)

            _, _, disparity = procrustes(
                odd_avg.reshape(-1, 1),
                even_avg.reshape(-1, 1)
            )
            stability = 1.0 - disparity
            color_reliabilities[color] = float(stability)

            print(f"  {color:10s}: {stability:.3f} (odd={len(odd_trials):2d}, even={len(even_trials):2d})")
        else:
            print(f"  {color:10s}: SKIPPED (odd={len(odd_trials):2d}, even={len(even_trials):2d})")

    if len(color_reliabilities) > 0:
        mean_reliability = np.mean(list(color_reliabilities.values()))
        print(f"  {'Mean':10s}: {mean_reliability:.3f} ({colors_with_both_splits}/{len(colors)} colors)")

        # Success criterion
        print(f"\n  Quality Assessment (PRIMARY METRIC):")
        if mean_reliability >= 0.50:
            print(f"  ✅ EXCELLENT: Stability ≥ 0.50 - High quality, proceed to full execution")
        elif mean_reliability >= 0.30:
            print(f"  ✅ GOOD: 0.30 ≤ Stability < 0.50 - Acceptable quality, proceed to full execution")
        elif mean_reliability >= 0.10:
            print(f"  ⚠️ MARGINAL: 0.10 ≤ Stability < 0.30 - Consider further parameter optimization")
        else:
            print(f"  ❌ POOR: Stability < 0.10 - Further optimization required")
    else:
        mean_reliability = 0.0
        print(f"  ⚠️ WARNING: No colors have both odd and even trials!")
        print(f"  ❌ POOR: Cannot compute reliability")

    metrics['split_half_reliability'] = {
        'by_color': color_reliabilities,
        'mean': float(mean_reliability),
        'n_colors_valid': colors_with_both_splits,
        'n_colors_total': len(colors)
    }

    # 2. RDM-based reliability (SECONDARY)
    print("\n2. RDM-based split-half reliability (SECONDARY):")

    MIN_TRIALS_PER_SPLIT = 3

    odd_patterns = []
    even_patterns = []
    colors_used = []
    skipped_colors = []

    for color in sorted(colors):
        color_mask = trial_metadata['color'] == color

        odd_trials = trial_betas[color_mask & odd_runs]
        even_trials = trial_betas[color_mask & even_runs]

        if len(odd_trials) >= MIN_TRIALS_PER_SPLIT and len(even_trials) >= MIN_TRIALS_PER_SPLIT:
            odd_patterns.append(odd_trials.mean(axis=0))
            even_patterns.append(even_trials.mean(axis=0))
            colors_used.append(color)
            print(f"  {color:10s}: USED (odd={len(odd_trials):2d}, even={len(even_trials):2d})")
        else:
            skipped_colors.append(color)
            print(f"  {color:10s}: SKIPPED (odd={len(odd_trials):2d}, even={len(even_trials):2d}, min={MIN_TRIALS_PER_SPLIT})")

    print(f"\n  Summary: {len(colors_used)}/{len(colors)} colors usable for RDM")

    if len(odd_patterns) >= 2 and len(even_patterns) >= 2:
        odd_patterns = np.array(odd_patterns)
        even_patterns = np.array(even_patterns)

        rdm_odd = squareform(pdist(odd_patterns, metric='correlation'))
        rdm_even = squareform(pdist(even_patterns, metric='correlation'))

        triu_idx = np.triu_indices_from(rdm_odd, k=1)
        rdm_odd_vec = rdm_odd[triu_idx]
        rdm_even_vec = rdm_even[triu_idx]

        rdm_corr, rdm_pval = spearmanr(rdm_odd_vec, rdm_even_vec)

        print(f"\n  RDM Spearman r: {rdm_corr:.3f} (p={rdm_pval:.3e})")
        print(f"  RDM pairs: {len(rdm_odd_vec)} (from {len(colors_used)}×{len(colors_used)} matrix)")
        print(f"  Note: RDM is secondary metric for local structure diagnosis")

        metrics['rdm_reliability'] = {
            'spearman_r': float(rdm_corr),
            'p_value': float(rdm_pval),
            'n_colors_used': len(colors_used),
            'n_colors_skipped': len(skipped_colors),
            'colors_used': colors_used,
            'colors_skipped': skipped_colors,
            'min_trials_threshold': MIN_TRIALS_PER_SPLIT
        }
    else:
        print(f"\n  ❌ ERROR: Insufficient colors for RDM computation")
        print(f"     Need at least 2 colors with ≥{MIN_TRIALS_PER_SPLIT} trials in both splits")
        print(f"     Got: {len(colors_used)} usable colors")
        metrics['rdm_reliability'] = {
            'spearman_r': None,
            'p_value': None,
            'n_colors_used': len(colors_used),
            'n_colors_skipped': len(skipped_colors),
            'colors_used': colors_used,
            'colors_skipped': skipped_colors,
            'error': 'insufficient_colors',
            'min_trials_threshold': MIN_TRIALS_PER_SPLIT
        }

    # 3. SNR estimation
    print("\n3. Temporal SNR:")
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

    # 4. Trial counts and data quality check
    print("\n4. Trial counts and data quality:")

    EXPECTED_TRIALS_PER_COLOR = 54
    EXPECTED_TOTAL_TRIALS = 432

    total_trials = len(trial_metadata)
    trial_counts_by_color = {}

    print(f"  Total trials: {total_trials}/{EXPECTED_TOTAL_TRIALS} ({total_trials/EXPECTED_TOTAL_TRIALS*100:.1f}%)")

    for color in sorted(colors):
        count = (trial_metadata['color'] == color).sum()
        trial_counts_by_color[color] = count
        pct = count / EXPECTED_TRIALS_PER_COLOR * 100
        status = "✅" if count >= 40 else "⚠️" if count >= 30 else "❌"
        print(f"  {color:10s}: {count:2d}/{EXPECTED_TRIALS_PER_COLOR} trials ({pct:5.1f}%) {status}")

    # Data quality warnings
    print(f"\n  Data Quality Warnings:")
    warnings_list = []

    recovery_rate = total_trials / EXPECTED_TOTAL_TRIALS
    if recovery_rate < 0.7:
        warnings_list.append(f"❌ Low trial recovery: {recovery_rate*100:.1f}% < 70%")
    elif recovery_rate < 0.85:
        warnings_list.append(f"⚠️ Moderate trial recovery: {recovery_rate*100:.1f}% < 85%")
    else:
        print(f"    ✅ Good trial recovery: {recovery_rate*100:.1f}%")

    counts = list(trial_counts_by_color.values())
    if len(counts) > 0:
        min_count = min(counts)
        max_count = max(counts)
        imbalance = (max_count - min_count) / max_count if max_count > 0 else 0

        if imbalance > 0.3:
            warnings_list.append(f"⚠️ High color imbalance: {imbalance*100:.1f}% (min={min_count}, max={max_count})")
        else:
            print(f"    ✅ Balanced colors: imbalance={imbalance*100:.1f}%")

    runs_present = sorted(trial_metadata['run'].unique())
    runs_expected = [1, 2, 3, 4, 5, 6]
    missing_runs = [r for r in runs_expected if r not in runs_present]
    if missing_runs:
        warnings_list.append(f"❌ Missing runs: {missing_runs}")
    else:
        print(f"    ✅ All 6 runs present")

    odd_count = trial_metadata['run'].isin([1, 3, 5]).sum()
    even_count = trial_metadata['run'].isin([2, 4, 6]).sum()
    split_imbalance = abs(odd_count - even_count) / max(odd_count, even_count)

    if split_imbalance > 0.2:
        warnings_list.append(f"⚠️ Odd/Even imbalance: {split_imbalance*100:.1f}% (odd={odd_count}, even={even_count})")
    else:
        print(f"    ✅ Balanced odd/even split: {split_imbalance*100:.1f}%")

    if warnings_list:
        for w in warnings_list:
            print(f"    {w}")

    metrics['trial_counts'] = trial_counts_by_color
    metrics['data_quality'] = {
        'total_trials': total_trials,
        'expected_trials': EXPECTED_TOTAL_TRIALS,
        'recovery_rate': float(recovery_rate),
        'color_imbalance': float(imbalance) if len(counts) > 0 else None,
        'runs_present': runs_present,
        'missing_runs': missing_runs,
        'odd_even_imbalance': float(split_imbalance),
        'warnings': warnings_list
    }

    print("="*70)

    return metrics


def main():
    """Main execution"""
    args = parse_args()

    print("\n" + "="*70)
    print("Step 1.3: Trial-wise GLM with Phase 0 Methodology")
    print("="*70)
    print(f"Subject: sub-{args.subject}")
    print(f"ROI: {args.roi}")
    print(f"Method: Phase 0 HRF+derivative + selected voxels")
    print(f"Smoothing: {args.smoothing_fwhm}mm FWHM")
    print(f"Confounds: {args.confounds_strategy}")
    print("="*70)

    # Load Phase 0 results
    print("\n📦 Loading Phase 0 results...")
    try:
        # Get Phase 0 summary
        phase0_summary = get_phase0_summary(
            args.subject, args.roi, args.derivatives_dir,
            args.phase0_dataset, args.phase0_timestamp
        )

        print(f"✓ Phase 0 found: .../{Path(phase0_summary['result_dir']).name}")
        print(f"  Total voxels: {phase0_summary['n_voxels_total']}")
        print(f"  Selected voxels: {phase0_summary['n_voxels_selected']} ({phase0_summary['selection_rate']*100:.1f}%)")
        print(f"  Mean R² (selected): {phase0_summary['mean_r2_selected']:.4f}")
        print(f"  HRF peak: delay {phase0_summary['hrf_peak_delay']}, value {phase0_summary['hrf_peak_value']:.4f}")

        # Load voxel mask
        selected_voxels_mask = load_phase0_voxel_mask(
            args.subject, args.roi, args.derivatives_dir,
            args.phase0_dataset, args.phase0_timestamp
        )

        # Get full ROI mask for creating mask image
        full_roi_mask_file = load_roi_mask(args.subject, args.roi, args.derivatives_dir)

        # Create selected voxels mask image
        selected_voxels_mask_img = create_selected_voxels_mask_img(
            selected_voxels_mask, full_roi_mask_file
        )
        print(f"✓ Selected voxels mask created")

    except Exception as e:
        print(f"\n❌ ERROR loading Phase 0 results: {e}")
        print(f"\nPhase 0 baseline must be run first!")
        print(f"See: /Users/jinilkim/.../analysis/phase1_preprocess_decoding/")
        return 1

    # Extract trial betas with Phase 0 method
    trial_betas, trial_metadata = extract_trial_betas_phase0method(
        args.subject,
        args.roi,
        args.fmriprep_dir,
        args.bids_dir,
        selected_voxels_mask_img,
        args.smoothing_fwhm,
        args.confounds_strategy
    )

    if len(trial_metadata) == 0 or len(trial_betas) == 0:
        print("\n❌ ERROR: No trials extracted. Cannot save results.")
        return 1

    # Compute quality metrics
    metrics = compute_quality_metrics(trial_betas, trial_metadata)

    if metrics is None:
        print("\n❌ ERROR: Quality metrics computation failed.")
        return 1

    # Save results
    output_subdir = Path(args.output_dir) / 'original_v3_phase0hrf' / f'sub-{args.subject}_{args.roi}'
    output_subdir.mkdir(parents=True, exist_ok=True)

    print(f"\nSaving results to: {output_subdir}")

    # Save betas
    np.save(output_subdir / 'trial_betas.npy', trial_betas)
    print(f"  ✓ Saved: trial_betas.npy {trial_betas.shape}")

    # Save metadata
    trial_metadata.to_csv(output_subdir / 'trial_metadata.csv', index=False)
    print(f"  ✓ Saved: trial_metadata.csv")

    # Save metrics (with Phase 0 info)
    metrics['subject_id'] = args.subject
    metrics['roi'] = args.roi
    metrics['method'] = 'phase0_hrf'
    metrics['smoothing_fwhm'] = float(args.smoothing_fwhm)
    metrics['confounds_strategy'] = args.confounds_strategy
    metrics['n_trials'] = int(len(trial_betas))
    metrics['n_voxels'] = int(trial_betas.shape[1])
    metrics['phase0_n_voxels_selected'] = phase0_summary['n_voxels_selected']
    metrics['phase0_n_voxels_total'] = phase0_summary['n_voxels_total']
    metrics['phase0_selection_rate'] = phase0_summary['selection_rate']
    metrics['phase0_mean_r2_selected'] = phase0_summary['mean_r2_selected']

    with open(output_subdir / 'quality_metrics.json', 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"  ✓ Saved: quality_metrics.json")

    # Summary
    print("\n" + "="*70)
    print("✅ DONE!")
    print("="*70)
    print(f"Subject: sub-{args.subject}")
    print(f"ROI: {args.roi}")
    print(f"Method: Phase 0 HRF+derivative + selected voxels")
    print(f"Trials extracted: {len(trial_betas)}")
    print(f"Voxels used: {trial_betas.shape[1]} (Phase 0 selected)")

    # PRIMARY: Procrustes stability
    procrustes_stability = metrics['split_half_reliability']['mean']
    print(f"\nProcrustes stability (PRIMARY): {procrustes_stability:.3f}")

    # SECONDARY: RDM correlation
    rdm_r = metrics['rdm_reliability']['spearman_r'] if metrics['rdm_reliability']['spearman_r'] is not None else 0.0
    print(f"RDM Spearman r (SECONDARY): {rdm_r:.3f}")

    # Final assessment based on PRIMARY metric
    print(f"\nFinal Assessment:")
    if procrustes_stability >= 0.50:
        print("✅ EXCELLENT (≥0.50) - Proceed to full execution")
    elif procrustes_stability >= 0.30:
        print("✅ GOOD (0.30-0.50) - Proceed to full execution")
    elif procrustes_stability >= 0.10:
        print("⚠️ MARGINAL (0.10-0.30) - Consider parameter optimization")
    else:
        print("❌ POOR (<0.10) - Further optimization required")

    print("\nComparison with previous result:")
    print("  Previous (generic SPM HRF): ~0.004")
    print(f"  Current (Phase 0 method): {procrustes_stability:.3f}")
    if procrustes_stability > 0.004:
        improvement = (procrustes_stability - 0.004) / 0.004 * 100
        print(f"  Improvement: +{improvement:.1f}%")

    print("="*70)

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
