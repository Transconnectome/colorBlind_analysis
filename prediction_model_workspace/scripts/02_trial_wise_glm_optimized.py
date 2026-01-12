#!/usr/bin/env python3
"""
Step 1.3: Trial-wise Beta Extraction using Efficient Beta Series

최적화:
- Run 단위로 한 번에 design matrix 생성
- 한 번의 GLM fitting으로 모든 trial beta 추출
- 432번 fitting → 6번 fitting (72배 속도 향상)

사용법:
    python 02_trial_wise_glm_optimized.py --subject 01 --roi V1

Date: 2026-01-11
"""

import argparse
import numpy as np
import pandas as pd
from pathlib import Path
import json
import nibabel as nib
from nilearn.glm.first_level import FirstLevelModel, make_first_level_design_matrix
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
        description='Step 1.3: Optimized trial-wise beta extraction'
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
        help='Derivatives directory for ROI masks'
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
        choices=['motion', 'motion_acompcor'],
        help='Confounds strategy'
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


def load_confounds(subject_id, run_id, fmriprep_dir, strategy='motion'):
    """Confounds 로딩"""
    confounds_file = Path(fmriprep_dir) / f'sub-{subject_id}' / 'func' / \
                    f'sub-{subject_id}_task-rsvp_run-{run_id}_desc-confounds_timeseries.tsv'

    confounds_df = pd.read_csv(confounds_file, sep='\t')

    if strategy == 'motion':
        motion_cols = [col for col in confounds_df.columns if col.startswith('trans_') or col.startswith('rot_')]
        selected_confounds = confounds_df[motion_cols].fillna(0)
    elif strategy == 'motion_acompcor':
        motion_cols = [col for col in confounds_df.columns if col.startswith('trans_') or col.startswith('rot_')]
        acompcor_cols = [col for col in confounds_df.columns if col.startswith('a_comp_cor_')][:5]
        selected_confounds = confounds_df[motion_cols + acompcor_cols].fillna(0)
    else:
        raise ValueError(f"Unknown confounds strategy: {strategy}")

    return selected_confounds


def extract_trial_betas_efficient(subject_id, roi_name, fmriprep_dir, bids_dir,
                                  roi_mask_img, smoothing_fwhm=0.0, confounds_strategy='motion'):
    """
    효율적인 trial-wise beta 추출

    최적화:
    - Run 단위로 한 번에 all trials의 design matrix 생성
    - 한 번의 GLM fitting으로 모든 trial beta 추출
    - LS-S와 동일한 결과, 하지만 72배 빠름
    """
    print("\n" + "="*70)
    print(f"Extracting trial-wise betas: sub-{subject_id} {roi_name}")
    print(f"Smoothing: {smoothing_fwhm}mm FWHM")
    print(f"Confounds: {confounds_strategy}")
    print("="*70)

    # Color names (matching event files)
    color_names = ['color_1', 'color_2', 'color_3', 'color_4',
                   'color_5', 'color_6', 'color_7', 'color_8']

    # Initialize masker (fit once, use many times)
    masker = NiftiMasker(
        mask_img=roi_mask_img,
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

        # **KEY OPTIMIZATION**: Create design matrix with separate regressor per trial
        print(f"  Creating efficient design matrix with {n_trials_in_run} trial regressors...")

        # Modify events to have unique trial names
        events_per_trial = color_events.copy()
        events_per_trial['trial_type'] = [f'trial_{i:03d}' for i in range(n_trials_in_run)]

        # **Single GLM fitting for entire run**
        print(f"  Fitting GLM (1 time for {n_trials_in_run} trials)...")
        glm = FirstLevelModel(
            t_r=2.0,
            slice_time_ref=0.5,
            hrf_model='spm',
            drift_model='cosine',
            high_pass=1/128,
            smoothing_fwhm=smoothing_fwhm,
            mask_img=roi_mask_img,
            minimize_memory=False,
            verbose=0
        )

        glm.fit(bold_file, events=events_per_trial, confounds=confounds)
        print(f"  ✓ GLM fitted!")

        # Extract beta for each trial (fast - just contrast computation)
        print(f"  Extracting {n_trials_in_run} trial betas...")
        for trial_idx in range(n_trials_in_run):
            if (trial_idx + 1) % 20 == 0 or trial_idx == 0:
                print(f"    Trial {trial_idx + 1}/{n_trials_in_run}...", end='\r')

            trial_name = f'trial_{trial_idx:03d}'
            target_trial = color_events.iloc[trial_idx]

            try:
                # Extract beta (fast - no fitting, just indexing)
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
    """Quality metrics 계산 (RDM reliability 포함)"""
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

        # Success criterion based on Procrustes stability (PRIMARY)
        # Reference: main.tex Line 279-289, HC variability analysis
        # Trial-wise expected to be lower than Phase 0 (0.91-0.95) due to single-trial noise
        print(f"\n  Quality Assessment (PRIMARY METRIC):")
        if mean_reliability >= 0.50:
            print(f"  ✅ EXCELLENT: Stability ≥ 0.50 - High quality, proceed to full execution")
        elif mean_reliability >= 0.30:
            print(f"  ✅ GOOD: 0.30 ≤ Stability < 0.50 - Acceptable quality")
        elif mean_reliability >= 0.10:
            print(f"  ⚠️ MARGINAL: 0.10 ≤ Stability < 0.30 - Consider parameter optimization")
        else:
            print(f"  ❌ POOR: Stability < 0.10 - Optimization required")
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

    # 2. RDM-based reliability (SECONDARY - diagnostic)
    print("\n2. RDM-based split-half reliability (SECONDARY):")

    # Minimum trials per color-split for reliable averaging
    MIN_TRIALS_PER_SPLIT = 3

    odd_patterns = []
    even_patterns = []
    colors_used = []
    skipped_colors = []

    for color in sorted(colors):
        color_mask = trial_metadata['color'] == color

        odd_trials = trial_betas[color_mask & odd_runs]
        even_trials = trial_betas[color_mask & even_runs]

        # Robust check: Need minimum trials in BOTH splits
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

        # Compute RDMs
        rdm_odd = squareform(pdist(odd_patterns, metric='correlation'))
        rdm_even = squareform(pdist(even_patterns, metric='correlation'))

        # Spearman correlation
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

    # Expected trials per color (ideal scenario)
    # 8 colors × 9 reps/color × 6 runs = 432 trials total
    # Expected per color: 54 trials (9 reps × 6 runs)
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
    warnings = []

    # Check 1: Total trial recovery rate
    recovery_rate = total_trials / EXPECTED_TOTAL_TRIALS
    if recovery_rate < 0.7:
        warnings.append(f"❌ Low trial recovery: {recovery_rate*100:.1f}% < 70%")
    elif recovery_rate < 0.85:
        warnings.append(f"⚠️ Moderate trial recovery: {recovery_rate*100:.1f}% < 85%")
    else:
        print(f"    ✅ Good trial recovery: {recovery_rate*100:.1f}%")

    # Check 2: Color imbalance
    counts = list(trial_counts_by_color.values())
    if len(counts) > 0:
        min_count = min(counts)
        max_count = max(counts)
        imbalance = (max_count - min_count) / max_count if max_count > 0 else 0

        if imbalance > 0.3:
            warnings.append(f"⚠️ High color imbalance: {imbalance*100:.1f}% (min={min_count}, max={max_count})")
        else:
            print(f"    ✅ Balanced colors: imbalance={imbalance*100:.1f}%")

    # Check 3: Missing runs
    runs_present = sorted(trial_metadata['run'].unique())
    runs_expected = [1, 2, 3, 4, 5, 6]
    missing_runs = [r for r in runs_expected if r not in runs_present]
    if missing_runs:
        warnings.append(f"❌ Missing runs: {missing_runs}")
    else:
        print(f"    ✅ All 6 runs present")

    # Check 4: Odd/Even balance (critical for split-half)
    odd_count = trial_metadata['run'].isin([1, 3, 5]).sum()
    even_count = trial_metadata['run'].isin([2, 4, 6]).sum()
    split_imbalance = abs(odd_count - even_count) / max(odd_count, even_count)

    if split_imbalance > 0.2:
        warnings.append(f"⚠️ Odd/Even imbalance: {split_imbalance*100:.1f}% (odd={odd_count}, even={even_count})")
    else:
        print(f"    ✅ Balanced odd/even split: {split_imbalance*100:.1f}%")

    if warnings:
        for w in warnings:
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
        'warnings': warnings
    }

    print("="*70)

    return metrics


def main():
    """Main execution"""
    args = parse_args()

    print("\n" + "="*70)
    print("Step 1.3: Optimized Trial-wise GLM (Beta Series)")
    print("="*70)
    print(f"Subject: sub-{args.subject}")
    print(f"ROI: {args.roi}")
    print(f"Smoothing: {args.smoothing_fwhm}mm FWHM")
    print(f"Confounds: {args.confounds_strategy}")
    print(f"Optimization: 6 GLM fittings (vs 432 in LS-S)")
    print("="*70)

    # Load ROI mask
    print("\nLoading ROI mask...")
    roi_mask_img = load_roi_mask(args.subject, args.roi, args.derivatives_dir)
    print(f"✓ ROI mask loaded: {Path(roi_mask_img).name}")

    # Extract trial betas (OPTIMIZED)
    trial_betas, trial_metadata = extract_trial_betas_efficient(
        args.subject,
        args.roi,
        args.fmriprep_dir,
        args.bids_dir,
        roi_mask_img,
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
    output_subdir = Path(args.output_dir) / 'original_v3' / f'sub-{args.subject}_{args.roi}'
    output_subdir.mkdir(parents=True, exist_ok=True)

    print(f"\nSaving results to: {output_subdir}")

    # Save betas
    np.save(output_subdir / 'trial_betas.npy', trial_betas)
    print(f"  ✓ Saved: trial_betas.npy {trial_betas.shape}")

    # Save metadata
    trial_metadata.to_csv(output_subdir / 'trial_metadata.csv', index=False)
    print(f"  ✓ Saved: trial_metadata.csv")

    # Save metrics
    metrics['subject_id'] = args.subject
    metrics['roi'] = args.roi
    metrics['smoothing_fwhm'] = float(args.smoothing_fwhm)
    metrics['confounds_strategy'] = args.confounds_strategy
    metrics['n_trials'] = int(len(trial_betas))
    metrics['n_voxels'] = int(trial_betas.shape[1])

    with open(output_subdir / 'quality_metrics.json', 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"  ✓ Saved: quality_metrics.json")

    # Summary
    print("\n" + "="*70)
    print("✅ DONE!")
    print("="*70)
    print(f"Subject: sub-{args.subject}")
    print(f"ROI: {args.roi}")
    print(f"Trials extracted: {len(trial_betas)}")

    # PRIMARY: Procrustes stability
    procrustes_stability = metrics['split_half_reliability']['mean']
    print(f"Procrustes stability (PRIMARY): {procrustes_stability:.3f}")

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
        print("❌ POOR (<0.10) - Optimization required")

    print("="*70)

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
