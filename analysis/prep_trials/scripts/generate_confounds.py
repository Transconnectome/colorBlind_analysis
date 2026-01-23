#!/usr/bin/env python3
"""
Generate confounds file for custom preprocessing pipeline

Creates fMRIPrep-compatible confounds file including:
- Motion parameters (6 DOF from registration)
- Tissue-based regressors (CSF, WM signals)
- Framewise displacement
- Cosine drift regressors

Usage:
    python generate_confounds.py --subject 01 --run 1 --method method3_header_mi
"""

import argparse
import numpy as np
import pandas as pd
import nibabel as nib
from pathlib import Path
from scipy import signal as scipy_signal
from nilearn import image
from nilearn.maskers import NiftiMasker


def extract_motion_from_lta(lta_file):
    """
    Extract 6 motion parameters from FreeSurfer LTA file

    LTA file format:
    # comments
    type = 1
    nxforms = 1
    mean = ...
    sigma = ...
    1 4 4          <- matrix size indicator
    [4x4 matrix]   <- transformation matrix
    """
    with open(lta_file, 'r') as f:
        lines = f.readlines()

    # Find the line with "1 4 4" (indicates 4x4 matrix follows)
    matrix_start = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Skip comments and empty lines
        if stripped.startswith('#') or not stripped:
            continue
        # Look for "1 4 4" pattern
        if stripped == '1 4 4':
            matrix_start = i + 1
            break

    if matrix_start is None:
        # Fallback: look for lines that look like matrix rows
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('#') or not stripped:
                continue
            # Try to parse as matrix row (4 floats)
            try:
                parts = stripped.split()
                if len(parts) == 4:
                    # Check if all are numbers
                    [float(x) for x in parts]
                    matrix_start = i
                    break
            except ValueError:
                continue

    if matrix_start is None:
        raise ValueError("Could not find transformation matrix in LTA file")

    # Parse 4x4 transformation matrix (skip comment lines)
    matrix = []
    current_line = matrix_start
    while len(matrix) < 4 and current_line < len(lines):
        line = lines[current_line].strip()
        # Skip comments and empty lines
        if line.startswith('#') or not line:
            current_line += 1
            continue

        try:
            parts = line.split()
            if len(parts) >= 4:
                row = [float(x) for x in parts[:4]]
                matrix.append(row)
        except ValueError as e:
            # Skip lines that can't be parsed as floats
            pass

        current_line += 1

    if len(matrix) != 4:
        raise ValueError(f"Could not parse 4x4 matrix, only got {len(matrix)} rows")

    matrix = np.array(matrix)

    # Extract translation (last column, first 3 rows)
    trans_x = matrix[0, 3]
    trans_y = matrix[1, 3]
    trans_z = matrix[2, 3]

    # Extract rotation from rotation matrix (upper-left 3x3)
    # Using Euler angles extraction (XYZ convention)
    R = matrix[:3, :3]

    # Rotation around X axis
    rot_x = np.arctan2(R[2, 1], R[2, 2])

    # Rotation around Y axis
    rot_y = np.arctan2(-R[2, 0], np.sqrt(R[2, 1]**2 + R[2, 2]**2))

    # Rotation around Z axis
    rot_z = np.arctan2(R[1, 0], R[0, 0])

    # Convert to degrees
    rot_x_deg = np.degrees(rot_x)
    rot_y_deg = np.degrees(rot_y)
    rot_z_deg = np.degrees(rot_z)

    motion_params = {
        'trans_x': trans_x,
        'trans_y': trans_y,
        'trans_z': trans_z,
        'rot_x': rot_x_deg,
        'rot_y': rot_y_deg,
        'rot_z': rot_z_deg
    }

    return motion_params


def compute_framewise_displacement(motion_df, radius=50):
    """
    Compute framewise displacement (FD) from motion parameters

    FD = sum of absolute derivatives of motion parameters
    Rotations converted to mm using radius (default 50mm)
    """
    # Convert rotations to mm (arc length = angle * radius)
    motion_mm = motion_df.copy()
    motion_mm['rot_x'] = np.deg2rad(motion_mm['rot_x']) * radius
    motion_mm['rot_y'] = np.deg2rad(motion_mm['rot_y']) * radius
    motion_mm['rot_z'] = np.deg2rad(motion_mm['rot_z']) * radius

    # Compute derivatives
    motion_deriv = motion_mm.diff().fillna(0)

    # FD = sum of absolute values
    fd = motion_deriv.abs().sum(axis=1)

    return fd


def extract_tissue_signals(bold_4d, brain_mask, method='simple'):
    """
    Extract CSF and WM signals from BOLD data

    Parameters:
    -----------
    bold_4d : nib.Nifti1Image
        4D BOLD image
    brain_mask : nib.Nifti1Image
        Brain mask
    method : str
        'simple': Use intensity thresholds
        'template': Use tissue probability maps (requires additional data)

    Returns:
    --------
    csf_signal, wm_signal : np.array
        Mean signals in CSF and WM compartments
    """
    bold_data = bold_4d.get_fdata()
    mask_data = brain_mask.get_fdata()

    # Compute mean image
    mean_img = bold_data.mean(axis=3)

    # Simple tissue segmentation based on intensity
    # This is a rough approximation - proper segmentation would use T1w

    # CSF: darkest voxels in brain mask (bottom 10% intensity)
    masked_mean = mean_img[mask_data > 0]
    csf_threshold = np.percentile(masked_mean, 10)
    csf_mask = (mean_img < csf_threshold) & (mask_data > 0)

    # WM: brightest voxels (top 20% intensity)
    wm_threshold = np.percentile(masked_mean, 80)
    wm_mask = (mean_img > wm_threshold) & (mask_data > 0)

    # Extract mean timeseries
    n_timepoints = bold_data.shape[3]
    csf_signal = np.zeros(n_timepoints)
    wm_signal = np.zeros(n_timepoints)

    for t in range(n_timepoints):
        if np.any(csf_mask):
            csf_signal[t] = bold_data[csf_mask, t].mean()
        if np.any(wm_mask):
            wm_signal[t] = bold_data[wm_mask, t].mean()

    return csf_signal, wm_signal


def create_cosine_regressors(n_timepoints, tr, high_pass=0.01):
    """
    Create discrete cosine transform (DCT) basis for drift removal

    This matches fMRIPrep's cosine regressors for high-pass filtering
    """
    frame_times = np.arange(n_timepoints) * tr
    duration = frame_times[-1]

    # Frequency cutoff
    cutoff_hz = high_pass
    period = 1.0 / cutoff_hz

    # Number of cosine bases
    n_bases = int(np.floor(duration / period))

    # Create cosine bases
    cosine_regressors = {}
    for k in range(n_bases):
        freq = (k + 1) / duration
        cosine_regressors[f'cosine{k:02d}'] = np.cos(2 * np.pi * freq * frame_times)

    return pd.DataFrame(cosine_regressors)


def generate_confounds(subject, run, method, tr=1.5, output_dir=None):
    """
    Generate complete confounds file
    """
    print(f"="*80)
    print(f"Generating Confounds: sub-{subject} run-{run} ({method})")
    print(f"="*80)
    print()

    # Paths
    if method == 'method3_header_mi':
        base_dir = Path('/storage/connectome/haba6030/fmriprep_out_method3_header_mi')
    else:
        raise ValueError(f"Unknown method: {method}")

    subject_dir = base_dir / f'sub-{subject}'

    # Input files
    bold_file = subject_dir / 'func' / f'sub-{subject}_task-rsvp_run-{run}_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz'
    mask_file = subject_dir / 'func' / f'sub-{subject}_task-rsvp_run-{run}_space-MNI152NLin2009cAsym_res-2_desc-brain_mask.nii.gz'
    lta_file = subject_dir / 'transforms' / f'sub-{subject}_run-{run}_bold_to_t1w.lta'

    # Check files exist
    if not bold_file.exists():
        raise FileNotFoundError(f"BOLD file not found: {bold_file}")
    if not mask_file.exists():
        raise FileNotFoundError(f"Mask file not found: {mask_file}")

    # Load BOLD data
    print("Loading BOLD data...")
    bold_4d = nib.load(bold_file)
    n_timepoints = bold_4d.shape[3]
    print(f"  Shape: {bold_4d.shape}")
    print(f"  Timepoints: {n_timepoints}")
    print()

    # Load brain mask
    print("Loading brain mask...")
    brain_mask = nib.load(mask_file)
    print("  ✅ Brain mask loaded")
    print()

    # Initialize confounds dataframe
    confounds = {}

    # 1. Motion parameters (constant across timepoints for mri_coreg)
    print("Extracting motion parameters...")
    if lta_file.exists():
        try:
            motion_params = extract_motion_from_lta(lta_file)

            # Replicate across timepoints (mri_coreg gives single transform)
            for param, value in motion_params.items():
                confounds[param] = np.full(n_timepoints, value)

            print(f"  ✅ Motion parameters extracted")
            print(f"     Translation: ({motion_params['trans_x']:.2f}, {motion_params['trans_y']:.2f}, {motion_params['trans_z']:.2f}) mm")
            print(f"     Rotation: ({motion_params['rot_x']:.2f}, {motion_params['rot_y']:.2f}, {motion_params['rot_z']:.2f}) deg")
        except Exception as e:
            print(f"  ⚠️  Could not extract motion from LTA: {e}")
            print(f"     Setting motion parameters to zero")
            for param in ['trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z']:
                confounds[param] = np.zeros(n_timepoints)
    else:
        print(f"  ⚠️  LTA file not found: {lta_file}")
        print(f"     Setting motion parameters to zero")
        for param in ['trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z']:
            confounds[param] = np.zeros(n_timepoints)
    print()

    # 2. Framewise displacement
    print("Computing framewise displacement...")
    motion_df = pd.DataFrame({
        'trans_x': confounds['trans_x'],
        'trans_y': confounds['trans_y'],
        'trans_z': confounds['trans_z'],
        'rot_x': confounds['rot_x'],
        'rot_y': confounds['rot_y'],
        'rot_z': confounds['rot_z']
    })
    fd = compute_framewise_displacement(motion_df)
    confounds['framewise_displacement'] = fd
    print(f"  ✅ FD computed (mean: {fd.mean():.4f} mm)")
    print()

    # 3. Tissue-based regressors
    print("Extracting tissue signals...")
    try:
        csf_signal, wm_signal = extract_tissue_signals(bold_4d, brain_mask)
        confounds['csf'] = csf_signal
        confounds['white_matter'] = wm_signal
        print(f"  ✅ CSF signal extracted")
        print(f"  ✅ WM signal extracted")
    except Exception as e:
        print(f"  ⚠️  Could not extract tissue signals: {e}")
        confounds['csf'] = np.zeros(n_timepoints)
        confounds['white_matter'] = np.zeros(n_timepoints)
    print()

    # 4. Global signal
    print("Computing global signal...")
    try:
        masker = NiftiMasker(mask_img=brain_mask)
        global_signal = masker.fit_transform(bold_4d).mean(axis=1)
        confounds['global_signal'] = global_signal
        print(f"  ✅ Global signal computed")
    except Exception as e:
        print(f"  ⚠️  Could not compute global signal: {e}")
        confounds['global_signal'] = np.zeros(n_timepoints)
    print()

    # 5. Cosine drift regressors
    print("Creating cosine drift regressors...")
    cosine_df = create_cosine_regressors(n_timepoints, tr, high_pass=0.01)
    for col in cosine_df.columns:
        confounds[col] = cosine_df[col].values
    print(f"  ✅ {len(cosine_df.columns)} cosine regressors created")
    print()

    # Create final dataframe
    confounds_df = pd.DataFrame(confounds)

    # Save confounds file
    if output_dir is None:
        output_dir = subject_dir / 'func'
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f'sub-{subject}_task-rsvp_run-{run}_desc-confounds_timeseries.tsv'
    confounds_df.to_csv(output_file, sep='\t', index=False)

    print(f"✅ Confounds file saved: {output_file}")
    print(f"   Columns: {list(confounds_df.columns)}")
    print(f"   Shape: {confounds_df.shape}")
    print()

    # Summary statistics
    print("="*80)
    print("Summary Statistics")
    print("="*80)
    print(f"Mean FD: {fd.mean():.4f} mm")
    print(f"Max FD: {fd.max():.4f} mm")
    print(f"Timepoints with FD > 0.5mm: {np.sum(fd > 0.5)} ({np.sum(fd > 0.5)/len(fd)*100:.1f}%)")
    print()

    return confounds_df, output_file


def main():
    parser = argparse.ArgumentParser(description='Generate confounds file')
    parser.add_argument('--subject', type=str, required=True, help='Subject ID (e.g., 01)')
    parser.add_argument('--run', type=int, required=True, help='Run number')
    parser.add_argument('--method', type=str, default='method3_header_mi',
                        help='Preprocessing method')
    parser.add_argument('--tr', type=float, default=1.5, help='TR in seconds (default: 1.5)')
    parser.add_argument('--output-dir', type=str, default=None,
                        help='Output directory (default: same as BOLD file)')

    args = parser.parse_args()

    try:
        confounds_df, output_file = generate_confounds(
            args.subject,
            args.run,
            args.method,
            tr=args.tr,
            output_dir=args.output_dir
        )
        print("="*80)
        print("✅ SUCCESS")
        print("="*80)
    except Exception as e:
        print("="*80)
        print(f"❌ ERROR: {e}")
        print("="*80)
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
