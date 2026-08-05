#!/usr/bin/env python3
"""
Step 1: Run GLMsingle and Save Residuals

This script runs GLMsingle on a subject-ROI pair and saves:
1. Single-trial betas (for decoding)
2. 1st-level residuals (for whitening)
3. Model diagnostics (R², HRF indices, etc.)

Usage:
    python 01_glmsingle_with_residuals.py --subject 01 --roi V1
    python 01_glmsingle_with_residuals.py --subject 01 --roi V1 --config conservative

Expected runtime: 20-40 minutes per subject-ROI
"""

import argparse
import json
import numpy as np
import nibabel as nib
from pathlib import Path
from datetime import datetime
import sys

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent / 'utils'))

from glmsingle_interface import (
    load_event_files,
    build_design_matrices,
    load_bold_data,
    load_roi_mask,
    run_glmsingle_with_residuals
)
from glmsingle_config import (
    get_config_full,
    get_config_conservative,
    print_config_summary
)


# ===== Configuration =====

# Server paths
EVENT_DIR = Path('/storage/connectome/haba6030/bids_editted')
FMRIPREP_DIR = Path('/storage/connectome/haba6030/fmriprep_out_method3_header_mi')
DERIVATIVES_DIR = Path('/scratch/connectome/haba6030/colorBlind/derivatives')

# Local paths (for testing)
LOCAL_EVENT_DIR = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_data/logs')
LOCAL_FMRIPREP_DIR = Path('/Volumes/T7/fmriprep_out_method3_header_mi')  # External drive

# ROI definitions (based on FIR reconstruction pipeline)
# Pattern: analysis/roi_masks/{dataset}/sub-{ID}/roi_pipeline/{ROI}_mask_*.nii.gz
def get_roi_mask_path(subject_id, roi_name, dataset='method3_header_mi'):
    """Get ROI mask path using FIR pipeline convention."""
    base_dir = Path(__file__).parent.parent.parent.parent.parent

    # Primary path (exact match)
    primary_path = (
        base_dir / 'analysis' / 'roi_masks' / dataset /
        f'sub-{subject_id}' / 'roi_pipeline' /
        f'{roi_name}_mask_thr50_intnearest_binTrue_masknone_gmTrue_subjTrue.nii.gz'
    )

    if primary_path.exists():
        return primary_path

    # Fallback: search with wildcards
    import glob
    pattern = str(
        base_dir / 'analysis' / 'roi_masks' / dataset /
        f'sub-{subject_id}' / 'roi_pipeline' /
        f'{roi_name}_mask_*.nii.gz'
    )
    matches = glob.glob(pattern)

    if matches:
        return Path(matches[0])

    return None

ROI_MASKS = {
    'V1': lambda sub: get_roi_mask_path(sub, 'V1'),
    'V2': lambda sub: get_roi_mask_path(sub, 'V2'),
    'V3': lambda sub: get_roi_mask_path(sub, 'V3'),
    'V4': lambda sub: get_roi_mask_path(sub, 'V4'),
}

# Experiment parameters
TR = 1.5
STIMDUR = 1.5
N_RUNS = 6
N_SCANS_PER_RUN = 240


def parse_args():
    parser = argparse.ArgumentParser(
        description='Run GLMsingle with residual extraction'
    )
    parser.add_argument(
        '--subject',
        type=str,
        required=True,
        help='Subject ID (e.g., 01, 02, ...)'
    )
    parser.add_argument(
        '--roi',
        type=str,
        required=True,
        choices=list(ROI_MASKS.keys()),
        help='ROI name'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='full',
        choices=['full', 'conservative'],
        help='GLMsingle configuration preset'
    )
    parser.add_argument(
        '--n-pcs',
        type=int,
        default=10,
        help='Number of noise PCs for GLMdenoise'
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=None,
        help='Output directory (default: derivatives/GLMsingle/{timestamp})'
    )
    parser.add_argument(
        '--local',
        action='store_true',
        help='Use local paths (for testing on laptop)'
    )
    parser.add_argument(
        '--skip-roi-mask',
        action='store_true',
        help='Skip ROI masking (use whole brain - not recommended)'
    )

    return parser.parse_args()


def main():
    args = parse_args()

    print("=" * 80)
    print("GLMsingle with Residuals - Step 1")
    print("=" * 80)
    print(f"Subject: sub-{args.subject}")
    print(f"ROI: {args.roi}")
    print(f"Config: {args.config}")
    print(f"N PCs: {args.n_pcs}")
    print()

    # Set paths based on local/server
    if args.local:
        event_dir = LOCAL_EVENT_DIR
        fmriprep_dir = LOCAL_FMRIPREP_DIR
        derivatives_dir = Path('./results')  # Local output
        print("Using LOCAL paths")
    else:
        event_dir = EVENT_DIR
        fmriprep_dir = FMRIPREP_DIR
        derivatives_dir = DERIVATIVES_DIR
        print("Using SERVER paths")

    # Create output directory
    if args.output_dir is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = derivatives_dir / f'GLMsingle/{timestamp}'
    else:
        output_dir = args.output_dir

    output_dir.mkdir(parents=True, exist_ok=True)
    subject_roi_dir = output_dir / f"sub-{args.subject}_{args.roi}"
    subject_roi_dir.mkdir(exist_ok=True)

    print(f"Output: {subject_roi_dir}")
    print()

    # ===== Step 1: Load Event Files =====
    print("=" * 80)
    print("Step 1: Loading Event Files")
    print("=" * 80)

    try:
        events_list = load_event_files(
            subject_id=args.subject,
            event_dir=event_dir,
            n_runs=N_RUNS
        )
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        print("Check paths and subject ID")
        return 1

    # ===== Step 2: Load ROI Mask =====
    print("\n" + "=" * 80)
    print("Step 2: Loading ROI Mask")
    print("=" * 80)

    if args.skip_roi_mask:
        print("WARNING: Skipping ROI mask - using whole brain")
        print("This will be VERY slow and memory-intensive!")
        roi_mask = None
    else:
        print(f"Loading ROI mask: {args.roi}")

        # Get ROI mask path using FIR pipeline convention
        roi_mask_path = ROI_MASKS[args.roi](args.subject)

        if roi_mask_path is None or not roi_mask_path.exists():
            print(f"ERROR: ROI mask not found for sub-{args.subject} {args.roi}")
            print(f"Searched in: analysis/roi_masks/original_v3/sub-{args.subject}/roi_pipeline/")
            print()
            print("Options:")
            print("  1. Create ROI masks using roi_pipeline first")
            print("  2. Use --skip-roi-mask to process whole brain (slow)")
            return 1

        print(f"  Found: {roi_mask_path}")

        # Load ROI mask
        import nibabel as nib
        roi_img = nib.load(roi_mask_path)
        roi_mask = roi_img.get_fdata() > 0

        n_voxels_mask = roi_mask.sum()
        print(f"  ROI voxels: {n_voxels_mask}")

    # ===== Step 3: Load BOLD Data =====
    print("\n" + "=" * 80)
    print("Step 3: Loading BOLD Data")
    print("=" * 80)

    try:
        data_list = load_bold_data(
            subject_id=args.subject,
            fmriprep_dir=fmriprep_dir,
            roi_mask=roi_mask,
            n_runs=N_RUNS,
            confounds_strategy=None  # GLMsingle handles denoising
        )
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        print("Check fMRIPrep directory and subject ID")
        return 1

    n_voxels = data_list[0].shape[1]
    n_scans_actual = data_list[0].shape[0]  # Get actual scan count from BOLD

    # Detailed per-run info (FIR style)
    print(f"\nBOLD data loaded:")
    scan_counts = []
    for run_idx, data in enumerate(data_list):
        n_scans_run = data.shape[0]
        scan_counts.append(n_scans_run)
        duration_sec = n_scans_run * TR
        print(f"  Run {run_idx + 1}: {n_scans_run} scans ({duration_sec:.1f}s), {data.shape[1]} voxels")

    # Check for variable scan counts
    if len(set(scan_counts)) > 1:
        print(f"\n⚠️  WARNING: Variable scan counts across runs: {scan_counts}")
        print(f"  Using minimum: {min(scan_counts)} scans")
        n_scans_actual = min(scan_counts)
    else:
        n_scans_actual = scan_counts[0]

    print(f"\nSummary:")
    print(f"  Total voxels: {n_voxels}")
    print(f"  Scans per run: {n_scans_actual} ({n_scans_actual * TR:.1f}s)")

    if n_voxels > 10000:
        print("WARNING: Large number of voxels - consider using ROI mask")
        print("Runtime may be very long (>2 hours)")

    # ===== Step 4: Build Design Matrices =====
    print("\n" + "=" * 80)
    print("Step 4: Building Design Matrices")
    print("=" * 80)

    # Use actual scan count from BOLD data (not auto-detect)
    design_list, trial_labels_list = build_design_matrices(
        events_list=events_list,
        tr=TR,
        n_scans_per_run=n_scans_actual,  # Use actual BOLD scan count
        exclude_blank=True
    )

    # Save design matrices
    design_file = subject_roi_dir / 'design_matrices.npz'
    np.savez(
        design_file,
        **{f'design_run{i+1}': d for i, d in enumerate(design_list)},
        **{f'labels_run{i+1}': l for i, l in enumerate(trial_labels_list)}
    )
    print(f"\nSaved design matrices: {design_file}")

    # ===== Step 5: Configure GLMsingle =====
    print("\n" + "=" * 80)
    print("Step 5: Configuring GLMsingle")
    print("=" * 80)

    if args.config == 'full':
        config = get_config_full(n_pcs=args.n_pcs)
    elif args.config == 'conservative':
        config = get_config_conservative(n_pcs=args.n_pcs)

    print_config_summary(config)

    # ===== Step 6: Run GLMsingle =====
    print("=" * 80)
    print("Step 6: Running GLMsingle")
    print("=" * 80)
    print("This may take 20-40 minutes...")
    print()

    try:
        betas, residuals, results_dict = run_glmsingle_with_residuals(
            design_list=design_list,
            data_list=data_list,
            trial_labels_list=trial_labels_list,  # Valid trials only (filtered by build_design_matrices)
            config=config,
            stimdur=STIMDUR,
            tr=TR,
            verbose=True
        )
    except Exception as e:
        print(f"ERROR during GLMsingle: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # ===== Step 7: Save Results =====
    print("\n" + "=" * 80)
    print("Step 7: Saving Results")
    print("=" * 80)

    # Save betas (color-wise: already in amplitude format!)
    if isinstance(betas, list):
        # Variable shapes per run - save as npz
        betas_file = subject_roi_dir / 'betas_colorwise.npz'
        np.savez(betas_file, **{f'run{i+1}': b for i, b in enumerate(betas)})
        print(f"✓ Betas (color-wise): {betas_file}")
        print(f"  Format: npz with {len(betas)} runs (variable shapes)")
        for i, b in enumerate(betas):
            print(f"    Run {i+1}: {b.shape} (conditions, voxels)")
    else:
        # Regular array - save as npy
        betas_file = subject_roi_dir / 'betas_colorwise.npy'
        np.save(betas_file, betas)
        print(f"✓ Betas (color-wise): {betas_file}")
        print(f"  Shape: {betas.shape} (runs, colors, voxels)")

    print(f"  Note: These are already color amplitudes, not single-trial betas")

    # Save residuals
    if residuals is not None:
        residuals_file = subject_roi_dir / 'residuals_1st_level.npy'
        np.save(residuals_file, residuals)
        print(f"✓ Residuals: {residuals_file}")
        print(f"  Shape: {residuals.shape}")
    else:
        print("✗ Residuals: Not available")
        print("  Whitening will not be possible")

    # Save R²
    if results_dict['R2'] is not None:
        r2_file = subject_roi_dir / 'R2_voxelwise.npy'
        np.save(r2_file, results_dict['R2'])
        print(f"✓ R²: {r2_file}")
        print(f"  Shape: {results_dict['R2'].shape}")
        print(f"  Mean R²: {results_dict['R2'].mean():.3f}")
        print(f"  Median R²: {np.median(results_dict['R2']):.3f}")

    # Save HRF indices (if available)
    if results_dict['HRFindex'] is not None:
        hrf_file = subject_roi_dir / 'HRFindex.npy'
        np.save(hrf_file, results_dict['HRFindex'])
        print(f"✓ HRF indices: {hrf_file}")

    # Save Fracridge values (if available)
    if results_dict['FRACvalue'] is not None:
        frac_file = subject_roi_dir / 'FRACvalue.npy'
        np.save(frac_file, results_dict['FRACvalue'])
        print(f"✓ Fracridge values: {frac_file}")

    # ===== Step 8: Save Diagnostics =====
    print("\n" + "=" * 80)
    print("Step 8: Computing Diagnostics")
    print("=" * 80)

    diagnostics = {
        'subject': args.subject,
        'roi': args.roi,
        'config': args.config,
        'n_pcs': args.n_pcs,
        'timestamp': datetime.now().isoformat(),

        # Data dimensions
        'n_runs': N_RUNS,
        'n_voxels': n_voxels,
        'n_trials_total': sum([len(labels) for labels in trial_labels_list]),

        # Model quality
        'r2_mean': float(results_dict['R2'].mean()) if results_dict['R2'] is not None else None,
        'r2_median': float(np.median(results_dict['R2'])) if results_dict['R2'] is not None else None,
        'r2_voxels_above_0.2': int(np.sum(results_dict['R2'] > 0.2)) if results_dict['R2'] is not None else None,
        'r2_voxels_above_0.5': int(np.sum(results_dict['R2'] > 0.5)) if results_dict['R2'] is not None else None,

        # Residuals
        'residuals_available': residuals is not None,
        'residuals_shape': residuals.shape if residuals is not None else None,

        # HRF
        'hrf_available': results_dict['HRFindex'] is not None,

        # Paths
        'event_dir': str(event_dir),
        'fmriprep_dir': str(fmriprep_dir),
        'output_dir': str(subject_roi_dir)
    }

    # Save diagnostics
    diag_file = subject_roi_dir / 'glmsingle_diagnostics.json'
    with open(diag_file, 'w') as f:
        json.dump(diagnostics, f, indent=2)

    print(f"✓ Diagnostics: {diag_file}")
    print()
    print("Summary:")
    print(f"  Mean R²: {diagnostics['r2_mean']:.3f}")
    print(f"  Voxels R² > 0.2: {diagnostics['r2_voxels_above_0.2']} / {n_voxels} "
          f"({100*diagnostics['r2_voxels_above_0.2']/n_voxels:.1f}%)")
    print(f"  Residuals: {'Available' if residuals is not None else 'Not available'}")

    # ===== Step 9: Create Diagnostic Visualizations =====
    print("\n" + "=" * 80)
    print("Step 9: Creating Diagnostic Visualizations")
    print("=" * 80)

    try:
        from visualization import (
            plot_design_matrices,
            plot_color_distribution,
            plot_glmsingle_outputs,
            create_text_summary
        )

        # Create figures directory
        figures_dir = subject_roi_dir / 'figures'
        figures_dir.mkdir(exist_ok=True)

        print(f"\nSaving visualizations to: {figures_dir}")

        # 1. Design matrices
        print("\n[1/4] Design matrices...")
        plot_design_matrices(
            design_list, trial_labels_list, figures_dir,
            runs_to_plot=[0, 1]  # First 2 runs
        )

        # 2. Color distribution
        print("\n[2/4] Color distribution...")
        plot_color_distribution(trial_labels_list, figures_dir)

        # 3. GLMsingle outputs
        print("\n[3/4] GLMsingle outputs...")
        plot_glmsingle_outputs(
            results_dict, figures_dir,
            roi_mask=roi_mask
        )

        # 4. Text summary
        print("\n[4/4] Summary report...")
        create_text_summary(results_dict, design_list, figures_dir)

        print("\n✓ All visualizations created successfully!")

    except Exception as e:
        print(f"\n⚠ Visualization creation failed: {e}")
        print("  Continuing without visualizations...")

    # ===== Done =====
    print("\n" + "=" * 80)
    print("GLMsingle Completed Successfully!")
    print("=" * 80)
    print(f"Output directory: {subject_roi_dir}")
    print(f"Visualizations: {subject_roi_dir / 'figures'}")
    print()
    print("Next steps:")
    print("  1. Run 02_estimate_noise_covariance.py to estimate Σ")
    print("  2. Run 03_glmsingle_whitened_amplitudes.py to whiten betas")
    print("  3. Run 04_evaluate_glmsingle_vs_fir.py to compare with baseline")
    print()

    return 0


if __name__ == '__main__':
    exit(main())
