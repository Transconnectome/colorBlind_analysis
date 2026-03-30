#!/usr/bin/env python3
"""
Generate confounds file from mcflirt motion parameters

Creates fMRIPrep-compatible confounds file including:
- Motion parameters (6 DOF from mcflirt .par file)
- Framewise displacement
- Tissue-based regressors (CSF, WM signals)
- Cosine drift regressors

Usage:
    python generate_confounds_mcflirt.py --subject 01 --run 1
"""

import argparse
import numpy as np
import pandas as pd
import nibabel as nib
from pathlib import Path
from nilearn.maskers import NiftiMasker


def read_mcflirt_par(par_file):
    """
    Read mcflirt motion parameters from .par file

    Format: 6 columns per timepoint
    - Columns 1-3: Rotation (radians) around x, y, z
    - Columns 4-6: Translation (mm) along x, y, z

    Returns motion_df with columns:
    - trans_x, trans_y, trans_z (mm)
    - rot_x, rot_y, rot_z (degrees)
    """
    # Read .par file (space-separated)
    motion_data = np.loadtxt(par_file)

    # mcflirt format: rot_x rot_y rot_z trans_x trans_y trans_z
    # Rotations in radians, translations in mm

    motion_df = pd.DataFrame({
        'trans_x': motion_data[:, 3],
        'trans_y': motion_data[:, 4],
        'trans_z': motion_data[:, 5],
        'rot_x': np.degrees(motion_data[:, 0]),  # Convert to degrees
        'rot_y': np.degrees(motion_data[:, 1]),
        'rot_z': np.degrees(motion_data[:, 2])
    })

    return motion_df


def compute_framewise_displacement(motion_df, radius=50):
    """
    Compute framewise displacement (FD) from motion parameters

    FD = sum of absolute derivatives of motion parameters
    Rotations converted to mm using radius (default 50mm)

    Following Power et al. 2012 formula
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


def extract_tissue_signals(bold_4d, brain_mask):
    """
    Extract CSF and WM signals from BOLD data

    Uses intensity-based segmentation (rough approximation)
    Proper segmentation would require T1w tissue probability maps
    """
    bold_data = bold_4d.get_fdata()
    mask_data = brain_mask.get_fdata()

    # Compute mean image
    mean_img = bold_data.mean(axis=3)

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

    Matches fMRIPrep's cosine regressors for high-pass filtering
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


def generate_confounds(subject, run, tr=1.5, output_dir=None):
    """
    Generate complete confounds file from mcflirt motion parameters
    """
    print(f"="*80)
    print(f"Generating Confounds: sub-{subject} run-{run}")
    print(f"="*80)
    print()

    # Paths
    base_dir = Path('/storage/connectome/haba6030/fmriprep_out_method3_header_mi')
    subject_dir = base_dir / f'sub-{subject}'

    # Input files
    bold_file = subject_dir / 'func' / f'sub-{subject}_task-rsvp_run-{run}_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz'
    mask_file = subject_dir / 'func' / f'sub-{subject}_task-rsvp_run-{run}_space-MNI152NLin2009cAsym_res-2_desc-brain_mask.nii.gz'
    motion_par = subject_dir / 'func' / f'sub-{subject}_task-rsvp_run-{run}_desc-motion.par'

    # Check files exist
    if not bold_file.exists():
        raise FileNotFoundError(f"BOLD file not found: {bold_file}")
    if not mask_file.exists():
        raise FileNotFoundError(f"Mask file not found: {mask_file}")
    if not motion_par.exists():
        raise FileNotFoundError(f"Motion .par file not found: {motion_par}\n"
                              f"Run add_motion_correction.sbatch first!")

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

    # 1. Motion parameters from mcflirt .par file
    print("Reading mcflirt motion parameters...")
    motion_df = read_mcflirt_par(motion_par)

    # Verify number of timepoints matches
    if len(motion_df) != n_timepoints:
        raise ValueError(f"Motion parameters ({len(motion_df)} timepoints) "
                       f"don't match BOLD ({n_timepoints} timepoints)")

    # Add to confounds
    for col in motion_df.columns:
        confounds[col] = motion_df[col].values

    print(f"  ✅ Motion parameters extracted ({len(motion_df)} timepoints)")
    print(f"     Translation range: ({motion_df['trans_x'].min():.2f}, {motion_df['trans_x'].max():.2f}) mm")
    print(f"     Rotation range: ({motion_df['rot_x'].min():.2f}, {motion_df['rot_x'].max():.2f}) deg")
    print()

    # 2. Framewise displacement
    print("Computing framewise displacement...")
    fd = compute_framewise_displacement(motion_df)
    confounds['framewise_displacement'] = fd
    print(f"  ✅ FD computed")
    print(f"     Mean: {fd.mean():.4f} mm")
    print(f"     Max: {fd.max():.4f} mm")
    print(f"     Timepoints > 0.5mm: {np.sum(fd > 0.5)} ({np.sum(fd > 0.5)/len(fd)*100:.1f}%)")
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
    print(f"Std FD: {fd.std():.4f} mm")
    print(f"Timepoints with FD > 0.5mm: {np.sum(fd > 0.5)} ({np.sum(fd > 0.5)/len(fd)*100:.1f}%)")
    print(f"Timepoints with FD > 0.9mm: {np.sum(fd > 0.9)} ({np.sum(fd > 0.9)/len(fd)*100:.1f}%)")
    print()

    return confounds_df, output_file


def main():
    parser = argparse.ArgumentParser(
        description='Generate confounds file from mcflirt motion parameters')
    parser.add_argument('--subject', type=str, required=True,
                       help='Subject ID (e.g., 01)')
    parser.add_argument('--run', type=int, required=True,
                       help='Run number')
    parser.add_argument('--tr', type=float, default=1.5,
                       help='TR in seconds (default: 1.5)')
    parser.add_argument('--output-dir', type=str, default=None,
                       help='Output directory (default: same as BOLD file)')

    args = parser.parse_args()

    try:
        confounds_df, output_file = generate_confounds(
            args.subject,
            args.run,
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
