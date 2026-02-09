"""
GLMsingle Interface for RSVP Color Experiment

Handles:
1. Loading BIDS event files
2. Building design matrices for GLMsingle
3. Loading fMRIPrep BOLD data with ROI masking
4. Running GLMsingle and extracting residuals
"""

import numpy as np
import pandas as pd
import nibabel as nib
from pathlib import Path
from typing import List, Tuple, Dict, Optional
import warnings


def load_event_files(
    subject_id: str,
    event_dir: Path,
    n_runs: int = 6
) -> List[pd.DataFrame]:
    """
    Load BIDS event files for all runs.

    Args:
        subject_id: Subject ID (e.g., '01')
        event_dir: Path to BIDS events directory
        n_runs: Number of runs (default: 6)

    Returns:
        events_list: List of DataFrames, one per run
            Columns: onset, duration, trial_type, block, trial, target_presented
    """
    events_list = []
    sub_str = f"sub-{subject_id}"

    for run_idx in range(1, n_runs + 1):
        event_file = (
            event_dir / sub_str / "func" /
            f"{sub_str}_task-rsvp_run-{run_idx}_events.tsv"
        )

        if not event_file.exists():
            raise FileNotFoundError(f"Event file not found: {event_file}")

        events_df = pd.read_csv(event_file, sep='\t')

        # Validate required columns
        required_cols = ['onset', 'duration', 'trial_type']
        missing_cols = [col for col in required_cols if col not in events_df.columns]
        if missing_cols:
            raise ValueError(f"Missing columns in {event_file}: {missing_cols}")

        events_list.append(events_df)

    print(f"Loaded events for sub-{subject_id}: {n_runs} runs")
    return events_list


def build_design_matrices(
    events_list: List[pd.DataFrame],
    tr: float,
    n_scans_per_run: int = None,
    exclude_blank: bool = True,
    verbose: bool = False
) -> Tuple[List[np.ndarray], List[np.ndarray]]:
    """
    Build design matrices for GLMsingle (Color-wise approach).

    Creates one column per color (8 total), merging all trials of the same color.
    This allows GLMsingle to optimize HRF while providing single-trial betas.

    Args:
        events_list: List of event DataFrames per run
        tr: Repetition time in seconds (1.5s)
        n_scans_per_run: Number of volumes per run (if None, auto-detect from events)
        exclude_blank: Exclude 'blank' trials (default: True)
        verbose: Print warnings for trials outside run range

    Returns:
        design_list: List of (n_scans, 8) design matrices (one column per color)
        trial_labels_list: List of arrays with color IDs (1-8) per trial
            e.g., [3, 1, 5, 2, ...] indicating which color each trial belongs to
    """
    design_list = []
    trial_labels_list = []

    color_trials = [f'color_{i}' for i in range(1, 9)]

    # Auto-detect n_scans_per_run if not provided
    if n_scans_per_run is None:
        # Estimate from maximum onset across all runs
        max_onset = max([df['onset'].max() for df in events_list])
        n_scans_per_run = int(np.ceil(max_onset / tr)) + 10  # +10 for safety buffer
        print(f"Auto-detected n_scans_per_run: {n_scans_per_run} (from max onset {max_onset:.1f}s)")

    # For GLMsingle: Use COLOR-WISE design (repeated conditions)
    # Each color = 1 condition (8 total), repeated multiple times per run
    # GLMsingle uses repetition info for GLMdenoise, Fracridge, and HRF optimization
    # Output: GLMsingle automatically returns single-trial betas
    n_conditions = 8  # 8 colors

    print(f"\nDesign matrix approach: COLOR-WISE (repeated conditions)")
    print(f"  Each run will have {n_conditions} conditions (one per color)")
    print(f"  GLMsingle will use repetition info and return single-trial betas")
    print()

    # Build color-wise design matrices (one column per color)
    for run_idx, events_df in enumerate(events_list):
        # Filter trials
        if exclude_blank:
            events_df = events_df[events_df['trial_type'] != 'blank'].copy()

        # Check color trials
        trial_types = events_df['trial_type'].unique()
        non_color = [t for t in trial_types if t not in color_trials]
        if non_color:
            warnings.warn(f"Run {run_idx + 1}: Non-color trials found: {non_color}")

        n_trials = len(events_df)

        # Initialize design matrix: (n_scans, n_conditions)
        # n_conditions = 8 colors (repeated conditions)
        design_matrix = np.zeros((n_scans_per_run, n_conditions))

        # Count trials per color for this run
        trials_per_color = []

        # Extract trial labels (which color each trial belongs to)
        # This will be used to reorganize GLMsingle's single-trial betas
        # IMPORTANT: Only include trials with valid onsets (within run range)
        color_ids = events_df['trial_type'].str.extract(r'color_(\d+)')[0].astype(int)
        onsets = events_df['onset'].values

        # Filter trials: only keep those with valid onsets
        valid_trial_mask = []
        for onset in onsets:
            scan_idx = int(np.round(onset / tr))
            valid_trial_mask.append(0 <= scan_idx < n_scans_per_run)

        valid_trial_mask = np.array(valid_trial_mask)
        trial_labels = color_ids.values[valid_trial_mask]  # Only valid trials

        n_invalid = (~valid_trial_mask).sum()
        if n_invalid > 0 and verbose:
            print(f"  Run {run_idx + 1}: {n_invalid} trials excluded (onset outside range)")

        # Process each color (merge all trials of same color into one column)
        for color_idx in range(1, n_conditions + 1):
            color_name = f'color_{color_idx}'
            color_events = events_df[events_df['trial_type'] == color_name]
            n_trials_color = len(color_events)
            trials_per_color.append(n_trials_color)

            # Place delta functions for all onsets of this color
            for onset in color_events['onset'].values:
                scan_idx = int(np.round(onset / tr))
                if 0 <= scan_idx < n_scans_per_run:
                    design_matrix[scan_idx, color_idx - 1] = 1
                # else: Trial outside run range - already counted above

        design_list.append(design_matrix)
        trial_labels_list.append(trial_labels)

        # Check for zero columns (colors with no valid trials)
        zero_cols = np.where(design_matrix.sum(axis=0) == 0)[0]
        if len(zero_cols) > 0:
            zero_colors = [f'color_{i+1}' for i in zero_cols]
            warnings.warn(
                f"Run {run_idx + 1}: {len(zero_cols)} colors have no valid trials: {zero_colors}. "
                f"All onsets were outside [0, {n_scans_per_run * tr:.1f}]s range."
            )

        # Detailed logging
        onset_min = events_df['onset'].min()
        onset_max = events_df['onset'].max()
        trials_range = f"{min(trials_per_color)}-{max(trials_per_color)}"

        print(f"  Run {run_idx + 1}: {n_trials} trials total, "
              f"{trials_range} per color, onset [{onset_min:.1f}, {onset_max:.1f}]s")

    return design_list, trial_labels_list


def load_bold_data(
    subject_id: str,
    fmriprep_dir: Path,
    roi_mask: Optional[np.ndarray] = None,
    n_runs: int = 6,
    confounds_strategy: Optional[str] = None
) -> List[np.ndarray]:
    """
    Load fMRIPrep BOLD data with optional ROI masking.

    Args:
        subject_id: Subject ID (e.g., '01')
        fmriprep_dir: Path to fMRIPrep output directory
        roi_mask: Boolean mask (x, y, z) for ROI selection
            If None, loads whole brain
        n_runs: Number of runs (default: 6)
        confounds_strategy: Confound regression strategy
            None: No confound regression (GLMsingle handles it)
            'minimal': Remove motion parameters
            'full': Remove motion + derivatives + CSF/WM

    Returns:
        data_list: List of (n_scans, n_voxels) arrays per run
    """
    data_list = []
    sub_str = f"sub-{subject_id}"

    for run_idx in range(1, n_runs + 1):
        # Load BOLD
        bold_file = (
            fmriprep_dir / sub_str / "func" /
            f"{sub_str}_task-rsvp_run-{run_idx}_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz"
        )

        if not bold_file.exists():
            raise FileNotFoundError(f"BOLD file not found: {bold_file}")

        bold_img = nib.load(bold_file)
        bold_data = bold_img.get_fdata()  # (x, y, z, n_scans)

        # Apply ROI mask
        if roi_mask is not None:
            if roi_mask.shape != bold_data.shape[:3]:
                raise ValueError(
                    f"ROI mask shape {roi_mask.shape} does not match "
                    f"BOLD shape {bold_data.shape[:3]}"
                )
            # Extract voxels: (n_scans, n_voxels)
            # Reshape bold_data to (n_voxels_total, n_scans)
            n_scans = bold_data.shape[-1]
            bold_reshaped = bold_data.reshape(-1, n_scans)  # (x*y*z, n_scans)
            roi_mask_flat = roi_mask.flatten()
            bold_masked = bold_reshaped[roi_mask_flat, :].T  # (n_scans, n_voxels_in_roi)
        else:
            # Flatten: (n_scans, n_voxels)
            bold_masked = bold_data.reshape(-1, bold_data.shape[-1]).T

        # Optional confound regression
        if confounds_strategy is not None:
            confounds_file = (
                fmriprep_dir / sub_str / "func" /
                f"{sub_str}_task-rsvp_run-{run_idx}_desc-confounds_timeseries.tsv"
            )
            bold_masked = regress_confounds(
                bold_masked,
                confounds_file,
                strategy=confounds_strategy
            )

        data_list.append(bold_masked)

        print(f"  Run {run_idx}: {bold_masked.shape[0]} scans, "
              f"{bold_masked.shape[1]} voxels")

    return data_list


def regress_confounds(
    data: np.ndarray,
    confounds_file: Path,
    strategy: str = 'minimal'
) -> np.ndarray:
    """
    Regress out confounds from BOLD data.

    Note: GLMsingle has GLMdenoise for noise removal.
    Only use this for basic motion correction if needed.

    Args:
        data: (n_scans, n_voxels) BOLD data
        confounds_file: Path to fMRIPrep confounds TSV
        strategy: 'minimal' | 'full'
            - minimal: 6 motion parameters
            - full: motion + derivatives + CSF + WM

    Returns:
        data_cleaned: (n_scans, n_voxels) residuals after confound regression
    """
    confounds_df = pd.read_csv(confounds_file, sep='\t')

    if strategy == 'minimal':
        # 6 motion parameters
        confound_cols = [
            'trans_x', 'trans_y', 'trans_z',
            'rot_x', 'rot_y', 'rot_z'
        ]
    elif strategy == 'full':
        # Motion + derivatives + CSF + WM
        confound_cols = [
            'trans_x', 'trans_y', 'trans_z',
            'rot_x', 'rot_y', 'rot_z',
            'trans_x_derivative1', 'trans_y_derivative1', 'trans_z_derivative1',
            'rot_x_derivative1', 'rot_y_derivative1', 'rot_z_derivative1',
            'csf', 'white_matter'
        ]
    else:
        raise ValueError(f"Unknown strategy: {strategy}")

    # Check available confounds
    missing_cols = [col for col in confound_cols if col not in confounds_df.columns]
    if missing_cols:
        warnings.warn(f"Missing confounds: {missing_cols}. Using available only.")
        confound_cols = [col for col in confound_cols if col in confounds_df.columns]

    confounds = confounds_df[confound_cols].values

    # Handle NaN (first row often has NaN for derivatives)
    confounds = np.nan_to_num(confounds, nan=0.0)

    # Regress out: residuals = data - X @ (X^T X)^-1 X^T @ data
    from sklearn.linear_model import LinearRegression
    lr = LinearRegression(fit_intercept=True)
    lr.fit(confounds, data)
    data_cleaned = data - lr.predict(confounds)

    return data_cleaned


def run_glmsingle_with_residuals(
    design_list: List[np.ndarray],
    data_list: List[np.ndarray],
    trial_labels_list: List[np.ndarray],
    config: Dict,
    stimdur: float = 1.5,
    tr: float = 1.5,
    verbose: bool = True
) -> Tuple[np.ndarray, Optional[np.ndarray], Dict]:
    """
    Run GLMsingle and extract residuals for whitening.

    Args:
        design_list: List of (n_scans, n_trials) design matrices (may be padded)
        data_list: List of (n_scans, n_voxels) BOLD data
        trial_labels_list: List of trial labels (1-8 for colors) for valid trials only
        config: GLMsingle configuration dictionary
        stimdur: Stimulus duration in seconds (1.5s)
        tr: Repetition time in seconds (1.5s)
        verbose: Print progress

    Returns:
        betas: List of (n_trials_actual, n_voxels) per run (padding removed)
        residuals: (n_runs, n_scans, n_voxels) 1st-level residuals
            None if GLMsingle doesn't provide residuals
        results_dict: Dictionary with all GLMsingle outputs
    """
    try:
        from glmsingle.glmsingle import GLM_single
    except ImportError:
        raise ImportError(
            "GLMsingle not installed. Install with:\n"
            "  pip install glmsingle"
        )

    if verbose:
        print("Running GLMsingle...")
        print(f"  Design matrices: {len(design_list)} runs")
        print(f"  Data: {len(data_list)} runs")
        print(f"  Stimulus duration: {stimdur}s")
        print(f"  TR: {tr}s")

    # Initialize GLMsingle
    glm = GLM_single(config)

    # Fit model
    results = glm.fit(
        design=design_list,
        data=data_list,
        stimdur=stimdur,
        tr=tr
    )

    if verbose:
        print("GLMsingle completed.")
        print(f"  Available outputs: {list(results.keys())}")

    # Extract betas from GLMsingle results
    # GLMsingle returns different types: typea, typeb, typec, typed
    # We want 'typed' (GLMdenoise + Fracridge) which has the best estimates
    if 'typed' in results:
        # typed contains: 'betasmd', 'R2', 'FRACvalue', etc.
        betas_single = results['typed']['betasmd']
        if verbose:
            print(f"  Using 'typed' (GLMdenoise + Fracridge) betas")
            print(f"  Raw betas shape: {betas_single.shape}")
            print(f"  Raw betas type: {type(betas_single)}")
            if isinstance(betas_single, list):
                print(f"  Betas is a list with {len(betas_single)} elements")
                for i, b in enumerate(betas_single[:3]):  # First 3
                    print(f"    Element {i}: shape {b.shape if hasattr(b, 'shape') else type(b)}")
    elif 'typec' in results:
        # typec is GLMdenoise without Fracridge
        betas_single = results['typec']['betasmd']
        if verbose:
            print(f"  Using 'typec' (GLMdenoise) betas")
            print(f"  Raw betas shape: {betas_single.shape}")
    elif 'betasmd' in results:
        # Direct betasmd (older GLMsingle versions)
        betas_single = results['betasmd']
    elif 'betas' in results:
        betas_single = results['betas']
    else:
        raise ValueError(
            f"No betas found in GLMsingle results. "
            f"Available keys: {list(results.keys())}"
        )

    # Reshape betas based on GLMsingle output format
    # NOTE: GLMsingle may return different formats depending on configuration:
    #   - Single-trial betas: (n_voxels, total_trials) if each repetition is separate
    #   - Condition betas: (n_voxels, n_conditions) if averaged across repetitions

    n_runs = len(design_list)
    n_voxels = data_list[0].shape[1]

    # Debug: print actual shape and expected shapes
    print(f"\n=== DEBUG: Beta shape analysis ===")
    print(f"  GLMsingle output shape: {betas_single.shape}")
    print(f"  Expected n_voxels: {n_voxels}")
    print(f"  Expected total trials: {sum(len(labels) for labels in trial_labels_list)}")

    # Handle GLMsingle output format
    # GLMsingle returns 4D array: (n_voxels, 1, 1, n_trials)
    # We need 2D array: (n_voxels, n_trials)
    if betas_single.ndim == 4:
        print(f"  Detected 4D output: {betas_single.shape}")
        print(f"  Squeezing to 2D...")
        betas_single = betas_single.squeeze()  # Remove singleton dimensions
        print(f"  After squeeze: {betas_single.shape}")
    elif betas_single.ndim == 3:
        print(f"  Detected 3D output: {betas_single.shape}")
        print(f"  Squeezing to 2D...")
        betas_single = betas_single.squeeze()
        print(f"  After squeeze: {betas_single.shape}")
    elif betas_single.ndim != 2:
        raise ValueError(
            f"Unexpected betas dimensionality: {betas_single.ndim}D. "
            f"Shape: {betas_single.shape}"
        )

    # Now betas_single should be 2D: (n_voxels, n_trials)
    if betas_single.ndim != 2:
        raise ValueError(
            f"Failed to reshape betas to 2D. Current shape: {betas_single.shape}"
        )

    # Verify dimensions
    actual_n_voxels, actual_n_trials = betas_single.shape
    print(f"  Final 2D shape: ({actual_n_voxels}, {actual_n_trials})")
    print(f"  Expected: ({n_voxels}, {sum(len(labels) for labels in trial_labels_list)})")

    if actual_n_voxels != n_voxels:
        warnings.warn(
            f"Voxel count mismatch: betas has {actual_n_voxels} voxels, "
            f"but data has {n_voxels} voxels"
        )

    if verbose:
        print(f"  Betas ready for processing: {betas_single.shape}")

    # Transpose to (total_trials, n_voxels)
    betas_all_trials = betas_single.T  # (total_trials, n_voxels)

    if verbose:
        print(f"  Transposed betas: {betas_all_trials.shape}")

    # Now reorganize into (n_runs, n_colors, n_voxels) using trial labels
    # Use the trial_labels_list that was passed in (already filtered for valid trials)
    trial_labels_per_run = trial_labels_list

    # Verify total trial count
    total_trials = sum(len(labels) for labels in trial_labels_per_run)
    if verbose:
        print(f"  Total valid trials from trial_labels_list: {total_trials}")
        for run_idx, labels in enumerate(trial_labels_per_run):
            print(f"    Run {run_idx + 1}: {len(labels)} trials")

    if betas_all_trials.shape[0] != total_trials:
        raise ValueError(
            f"Trial count mismatch: GLMsingle returned {betas_all_trials.shape[0]} trials, "
            f"but trial_labels_list has {total_trials} valid trials. "
            f"This may indicate an issue with design matrix construction."
        )

    # Reorganize into (n_runs, n_colors, n_voxels)
    n_colors = 8
    betas_reshaped = np.zeros((n_runs, n_colors, n_voxels))

    trial_idx = 0
    for run_idx, labels in enumerate(trial_labels_per_run):
        n_trials_run = len(labels)

        # Get betas for this run
        betas_run = betas_all_trials[trial_idx:trial_idx + n_trials_run, :]  # (n_trials, n_voxels)

        # Average by color
        for color_id in range(1, n_colors + 1):
            trials_this_color = (labels == color_id)
            n_trials_color = trials_this_color.sum()

            if n_trials_color > 0:
                # Average all trials of this color
                betas_reshaped[run_idx, color_id - 1, :] = betas_run[trials_this_color, :].mean(axis=0)
            else:
                # No trials for this color in this run (shouldn't happen)
                warnings.warn(f"Run {run_idx + 1} has no trials for color {color_id}")

        if verbose:
            print(f"    Run {run_idx + 1}: {n_trials_run} trials → {n_colors} colors")
            # Show trial distribution
            color_counts = {i: (labels == i).sum() for i in range(1, n_colors + 1)}
            print(f"      Color distribution: {color_counts}")

        trial_idx += n_trials_run

    betas = betas_reshaped

    if verbose:
        print(f"  Final betas shape: {betas.shape} (runs, colors, voxels)")

    # Extract residuals (CRITICAL for whitening)
    # GLMsingle does NOT return residuals in output
    # Always compute manually
    if verbose:
        print("\n  Computing residuals manually...")

    residuals = compute_residuals_manual(
        data_list, design_list, betas_all_trials, trial_labels_per_run,
        stimdur, tr, verbose=verbose
    )

    if verbose:
        print(f"  Residuals computed: {residuals.shape if residuals is not None else 'None'}")

    # Store all results
    results_dict = {
        'betas': betas,
        'residuals': residuals,
        'R2': results.get('R2', None),
        'HRFindex': results.get('HRFindex', None),
        'FRACvalue': results.get('FRACvalue', None),
        'glm_results': results
    }

    return betas, residuals, results_dict


def compute_residuals_manual(
    data_list: List[np.ndarray],
    design_list: List[np.ndarray],
    betas_all_trials: np.ndarray,
    trial_labels_per_run: List[np.ndarray],
    stimdur: float,
    tr: float,
    verbose: bool = False
) -> np.ndarray:
    """
    Manually compute 1st-level residuals from GLMsingle outputs.

    Uses color-averaged betas for residual estimation (simpler and more robust).
    Residuals = data - (design_colors @ betas_colors)

    Args:
        data_list: List of (n_scans, n_voxels) BOLD data per run
        design_list: List of (n_scans, n_colors=8) design matrices per run
        betas_all_trials: (total_trials, n_voxels) single-trial betas
        trial_labels_per_run: List of arrays with color labels (1-8) per trial
        stimdur: Stimulus duration
        tr: Repetition time
        verbose: Print progress

    Returns:
        residuals: (n_runs, n_scans, n_voxels) residuals
    """
    n_runs = len(data_list)
    n_colors = 8
    residuals = []

    # Compute color-averaged betas from single-trial betas
    trial_idx = 0
    for run_idx in range(n_runs):
        n_trials_run = len(trial_labels_per_run[run_idx])
        n_voxels = data_list[run_idx].shape[1]

        # Get data for this run
        y = data_list[run_idx]  # (n_scans, n_voxels)
        X = design_list[run_idx]  # (n_scans, 8 colors)

        # Get single-trial betas for this run
        betas_run = betas_all_trials[trial_idx:trial_idx + n_trials_run, :]  # (n_trials, n_voxels)
        labels = trial_labels_per_run[run_idx]  # (n_trials,) with values 1-8

        # Average betas by color
        betas_colors = np.zeros((n_colors, n_voxels))
        for color_id in range(1, n_colors + 1):
            trials_this_color = (labels == color_id)
            if trials_this_color.sum() > 0:
                betas_colors[color_id - 1, :] = betas_run[trials_this_color, :].mean(axis=0)

        # Predict using color-wise model: y_pred = X @ beta_colors
        y_pred = X @ betas_colors

        # Residuals
        residual = y - y_pred
        residuals.append(residual)

        if verbose:
            print(f"    Run {run_idx + 1}: residuals shape {residual.shape}")
            print(f"      Residual mean: {residual.mean():.6f}, std: {residual.std():.3f}")

        trial_idx += n_trials_run

    residuals = np.array(residuals)  # (n_runs, n_scans, n_voxels)
    return residuals


def load_roi_mask(
    roi_file: Path,
    fmriprep_reference: Optional[Path] = None
) -> np.ndarray:
    """
    Load ROI mask from NIfTI file.

    Args:
        roi_file: Path to ROI mask (binary or integer labels)
        fmriprep_reference: Optional BOLD file for resampling

    Returns:
        mask: Boolean (x, y, z) array
    """
    roi_img = nib.load(roi_file)
    roi_data = roi_img.get_fdata()

    # Convert to boolean mask
    mask = roi_data > 0

    # TODO: Check/resample to match fMRIPrep reference if needed

    n_voxels = mask.sum()
    print(f"ROI mask loaded: {n_voxels} voxels")

    return mask


if __name__ == '__main__':
    # Test with example paths
    print("=" * 60)
    print("TESTING GLMSINGLE INTERFACE")
    print("=" * 60)

    # These paths are examples - adjust for actual testing
    subject_id = '01'
    event_dir = Path('/storage/connectome/haba6030/bids_editted')
    fmriprep_dir = Path('/storage/connectome/haba6030/fmriprep_out_method3_header_mi')

    print("\n1. Loading event files...")
    try:
        events_list = load_event_files(subject_id, event_dir)
        print(f"   ✓ Loaded {len(events_list)} runs")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    print("\n2. Building design matrices...")
    try:
        design_list, trial_labels_list = build_design_matrices(
            events_list,
            tr=1.5,
            n_scans_per_run=240
        )
        print(f"   ✓ Built {len(design_list)} design matrices")
        print(f"   Design shape example: {design_list[0].shape}")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    print("\n3. Loading BOLD data (requires actual files)...")
    print("   Skipping in test mode")

    print("\n" + "=" * 60)
    print("Interface functions ready for use")
    print("=" * 60)
