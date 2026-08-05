#!/usr/bin/env python3
"""
Generate confounds file for custom preprocessing pipeline

Creates fMRIPrep-compatible confounds file including:
- Motion parameters (6 DOF from registration)
- aCompCor (anatomical Component Correction) - 5 components each from CSF and WM
- Tissue-based regressors (CSF, WM mean signals)
- Framewise displacement
- Cosine drift regressors

Partial FOV handling:
- Uses ICBM152_2009 tissue probability maps (MNI space)
- Conservative thresholding (prob > 0.99) to avoid GM contamination
- Erosion for additional safety
- Validation and visualization of mask coverage

Usage:
    python generate_confounds.py --subject 01 --run 1 --method method3_header_mi
"""

import argparse
import numpy as np
import pandas as pd
import nibabel as nib
from pathlib import Path
from scipy import signal as scipy_signal
from scipy.ndimage import binary_erosion
from nilearn import image, datasets
from nilearn.maskers import NiftiMasker
from sklearn.decomposition import PCA
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


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


def load_tissue_probability_maps():
    """
    Load ICBM152_2009 tissue probability maps (MNI space)

    Returns:
    --------
    csf_prob_img, wm_prob_img, gm_prob_img : nib.Nifti1Image
        Tissue probability maps in MNI152NLin2009cAsym space
    """
    print("  Fetching ICBM152_2009 tissue probability maps...")
    try:
        icbm = datasets.fetch_icbm152_2009()
        csf_prob_img = nib.load(icbm['csf'])
        wm_prob_img = nib.load(icbm['wm'])
        gm_prob_img = nib.load(icbm['gm'])
        print("  ✅ ICBM tissue maps loaded")
        return csf_prob_img, wm_prob_img, gm_prob_img
    except Exception as e:
        print(f"  ⚠️  Failed to fetch ICBM maps: {e}")
        return None, None, None


def create_conservative_tissue_masks(bold_img, brain_mask, csf_prob_img, wm_prob_img,
                                     csf_threshold=0.99, wm_threshold=0.99, erode_voxels=1):
    """
    Create conservative CSF and WM masks for aCompCor

    Strategy to avoid GM contamination:
    1. Very high probability threshold (>0.99) - only pure CSF/WM
    2. Resample to BOLD space
    3. Morphological erosion (1 voxel) to remove boundaries
    4. Intersection with brain mask (partial FOV handling)

    Parameters:
    -----------
    bold_img : nib.Nifti1Image
        BOLD image (for target space)
    brain_mask : nib.Nifti1Image
        Brain mask (partial FOV)
    csf_prob_img, wm_prob_img : nib.Nifti1Image
        Tissue probability maps
    csf_threshold, wm_threshold : float
        Probability thresholds (default: 0.99 - very conservative)
    erode_voxels : int
        Number of erosion iterations (default: 1)

    Returns:
    --------
    csf_mask, wm_mask : np.ndarray (3D boolean)
        Conservative tissue masks
    stats : dict
        Coverage statistics for validation
    """
    print(f"  Creating conservative tissue masks (CSF prob > {csf_threshold}, WM prob > {wm_threshold})...")

    # Resample tissue probability maps to BOLD space
    csf_prob_resampled = image.resample_to_img(csf_prob_img, bold_img, interpolation='continuous')
    wm_prob_resampled = image.resample_to_img(wm_prob_img, bold_img, interpolation='continuous')

    csf_prob_data = csf_prob_resampled.get_fdata()
    wm_prob_data = wm_prob_resampled.get_fdata()
    brain_mask_data = brain_mask.get_fdata()

    # Create high-probability masks
    csf_mask = (csf_prob_data > csf_threshold) & (brain_mask_data > 0)
    wm_mask = (wm_prob_data > wm_threshold) & (brain_mask_data > 0)

    # Morphological erosion for additional safety
    if erode_voxels > 0:
        csf_mask = binary_erosion(csf_mask, iterations=erode_voxels)
        wm_mask = binary_erosion(wm_mask, iterations=erode_voxels)

    # Statistics for validation
    n_brain_voxels = np.sum(brain_mask_data > 0)
    n_csf_voxels = np.sum(csf_mask)
    n_wm_voxels = np.sum(wm_mask)

    # Convert numpy types to Python native types for JSON serialization
    stats = {
        'n_brain_voxels': int(n_brain_voxels),
        'n_csf_voxels': int(n_csf_voxels),
        'n_wm_voxels': int(n_wm_voxels),
        'csf_coverage': float(n_csf_voxels / n_brain_voxels * 100),
        'wm_coverage': float(n_wm_voxels / n_brain_voxels * 100)
    }

    print(f"  ✅ Tissue masks created:")
    print(f"     CSF: {n_csf_voxels} voxels ({stats['csf_coverage']:.2f}% of brain)")
    print(f"     WM:  {n_wm_voxels} voxels ({stats['wm_coverage']:.2f}% of brain)")

    if n_csf_voxels == 0:
        print(f"  ⚠️  WARNING: CSF mask is empty! Partial FOV may not include ventricles.")
    if n_wm_voxels == 0:
        print(f"  ⚠️  WARNING: WM mask is empty! Check tissue probability map alignment.")

    return csf_mask, wm_mask, stats


def compute_acompcor(bold_4d, tissue_mask, n_components=5, mask_name='tissue'):
    """
    Compute aCompCor components from tissue mask

    Parameters:
    -----------
    bold_4d : nib.Nifti1Image
        4D BOLD image
    tissue_mask : np.ndarray (3D boolean)
        Tissue mask (CSF or WM)
    n_components : int
        Number of principal components to extract (default: 5)
    mask_name : str
        Mask name for logging (e.g., 'CSF', 'WM')

    Returns:
    --------
    components : np.ndarray, shape (n_timepoints, n_components)
        aCompCor components
    variance_explained : np.ndarray, shape (n_components,)
        Fraction of variance explained by each component
    """
    if not np.any(tissue_mask):
        print(f"  ⚠️  {mask_name} mask is empty, returning zeros")
        n_timepoints = bold_4d.shape[3]
        return np.zeros((n_timepoints, n_components)), np.zeros(n_components)

    # Extract voxel timeseries
    bold_data = bold_4d.get_fdata()
    n_timepoints = bold_data.shape[3]

    # Reshape to (n_timepoints, n_voxels)
    voxel_timeseries = bold_data[tissue_mask].T  # (n_timepoints, n_voxels)

    # Standardize (mean-center and scale)
    voxel_timeseries = (voxel_timeseries - voxel_timeseries.mean(axis=0)) / (voxel_timeseries.std(axis=0) + 1e-10)

    # PCA to extract top components
    actual_components = min(n_components, voxel_timeseries.shape[1], n_timepoints)

    if actual_components < n_components:
        print(f"  ⚠️  {mask_name}: Only {actual_components} components available (requested {n_components})")

    pca = PCA(n_components=actual_components)
    components = pca.fit_transform(voxel_timeseries)

    # Pad with zeros if needed
    if actual_components < n_components:
        padding = np.zeros((n_timepoints, n_components - actual_components))
        components = np.hstack([components, padding])
        variance_explained = np.concatenate([pca.explained_variance_ratio_, np.zeros(n_components - actual_components)])
    else:
        variance_explained = pca.explained_variance_ratio_

    print(f"  ✅ {mask_name} aCompCor: {actual_components} components extracted")
    print(f"     Variance explained: {variance_explained[:3].sum()*100:.1f}% (top 3)")

    return components, variance_explained


def extract_tissue_signals(bold_4d, csf_mask, wm_mask):
    """
    Extract mean CSF and WM signals from BOLD data

    Parameters:
    -----------
    bold_4d : nib.Nifti1Image
        4D BOLD image
    csf_mask, wm_mask : np.ndarray (3D boolean)
        Tissue masks

    Returns:
    --------
    csf_signal, wm_signal : np.array
        Mean signals in CSF and WM compartments
    """
    bold_data = bold_4d.get_fdata()
    n_timepoints = bold_data.shape[3]

    csf_signal = np.zeros(n_timepoints)
    wm_signal = np.zeros(n_timepoints)

    for t in range(n_timepoints):
        if np.any(csf_mask):
            csf_signal[t] = bold_data[csf_mask, t].mean()
        if np.any(wm_mask):
            wm_signal[t] = bold_data[wm_mask, t].mean()

    return csf_signal, wm_signal


def visualize_tissue_masks(bold_img, brain_mask, csf_mask, wm_mask, output_path):
    """
    Visualize tissue masks overlaid on mean BOLD image

    Creates axial slice montage showing:
    - Brain mask (outline)
    - CSF mask (blue)
    - WM mask (red)

    Parameters:
    -----------
    bold_img : nib.Nifti1Image
        4D BOLD image
    brain_mask : nib.Nifti1Image
        Brain mask
    csf_mask, wm_mask : np.ndarray (3D boolean)
        Tissue masks
    output_path : Path
        Output PNG file path
    """
    print(f"  Creating mask visualization...")

    # Compute mean BOLD
    mean_bold = image.mean_img(bold_img)
    mean_bold_data = mean_bold.get_fdata()
    brain_mask_data = brain_mask.get_fdata()

    # Find slices with brain coverage
    brain_slices = np.where(brain_mask_data.sum(axis=(0, 1)) > 100)[0]

    if len(brain_slices) == 0:
        print(f"  ⚠️  No brain slices found, skipping visualization")
        return

    # Select 9 evenly spaced slices
    slice_indices = brain_slices[np.linspace(0, len(brain_slices)-1, 9, dtype=int)]

    # Create figure
    fig, axes = plt.subplots(3, 3, figsize=(12, 12))
    axes = axes.flatten()

    for idx, slice_z in enumerate(slice_indices):
        ax = axes[idx]

        # Plot mean BOLD (grayscale)
        ax.imshow(mean_bold_data[:, :, slice_z].T, cmap='gray', origin='lower', aspect='auto')

        # Overlay CSF mask (blue)
        csf_overlay = np.ma.masked_where(~csf_mask[:, :, slice_z], csf_mask[:, :, slice_z])
        ax.imshow(csf_overlay.T, cmap='Blues', alpha=0.5, origin='lower', aspect='auto')

        # Overlay WM mask (red)
        wm_overlay = np.ma.masked_where(~wm_mask[:, :, slice_z], wm_mask[:, :, slice_z])
        ax.imshow(wm_overlay.T, cmap='Reds', alpha=0.5, origin='lower', aspect='auto')

        ax.set_title(f'Slice {slice_z}', fontsize=10)
        ax.axis('off')

    # Legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='blue', alpha=0.5, label='CSF mask'),
        Patch(facecolor='red', alpha=0.5, label='WM mask')
    ]
    fig.legend(handles=legend_elements, loc='upper right', fontsize=12)

    plt.suptitle('Tissue Masks for aCompCor (Conservative: prob > 0.99, eroded 1 voxel)', fontsize=14, y=0.98)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"  ✅ Visualization saved: {output_path}")


def validate_acompcor_quality(csf_components, wm_components, csf_variance, wm_variance, output_path):
    """
    Create quality control plots for aCompCor components

    Plots:
    1. Component timeseries (first 3 components)
    2. Variance explained by each component

    Parameters:
    -----------
    csf_components, wm_components : np.ndarray (n_timepoints, n_components)
    csf_variance, wm_variance : np.ndarray (n_components,)
    output_path : Path
    """
    print(f"  Creating aCompCor QC plots...")

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    n_timepoints = csf_components.shape[0]
    timepoints = np.arange(n_timepoints)

    # CSF timeseries (top 3 components)
    ax = axes[0, 0]
    for i in range(min(3, csf_components.shape[1])):
        ax.plot(timepoints, csf_components[:, i], label=f'CSF comp {i}', alpha=0.7)
    ax.set_xlabel('Timepoint')
    ax.set_ylabel('Signal (standardized)')
    ax.set_title('CSF aCompCor Components (top 3)')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # WM timeseries (top 3 components)
    ax = axes[0, 1]
    for i in range(min(3, wm_components.shape[1])):
        ax.plot(timepoints, wm_components[:, i], label=f'WM comp {i}', alpha=0.7)
    ax.set_xlabel('Timepoint')
    ax.set_ylabel('Signal (standardized)')
    ax.set_title('WM aCompCor Components (top 3)')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # CSF variance explained
    ax = axes[1, 0]
    n_comp_csf = len(csf_variance)
    ax.bar(range(n_comp_csf), csf_variance * 100, color='steelblue', alpha=0.7)
    ax.set_xlabel('Component')
    ax.set_ylabel('Variance Explained (%)')
    ax.set_title('CSF aCompCor Variance Explained')
    ax.set_xticks(range(n_comp_csf))
    ax.grid(True, alpha=0.3, axis='y')

    # WM variance explained
    ax = axes[1, 1]
    n_comp_wm = len(wm_variance)
    ax.bar(range(n_comp_wm), wm_variance * 100, color='coral', alpha=0.7)
    ax.set_xlabel('Component')
    ax.set_ylabel('Variance Explained (%)')
    ax.set_title('WM aCompCor Variance Explained')
    ax.set_xticks(range(n_comp_wm))
    ax.grid(True, alpha=0.3, axis='y')

    plt.suptitle('aCompCor Quality Control', fontsize=14, y=0.995)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"  ✅ QC plots saved: {output_path}")


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

    # 3. Tissue probability maps and masks
    print("[1/2] Loading tissue probability maps...")
    csf_prob_img, wm_prob_img, gm_prob_img = load_tissue_probability_maps()
    print()

    if csf_prob_img is None or wm_prob_img is None:
        print("⚠️  WARNING: Could not load tissue probability maps")
        print("  Skipping aCompCor, using zeros for tissue signals")
        confounds['csf'] = np.zeros(n_timepoints)
        confounds['white_matter'] = np.zeros(n_timepoints)
        # Skip aCompCor
        for i in range(5):
            confounds[f'a_comp_cor_{i:02d}'] = np.zeros(n_timepoints)
        csf_mask = None
        wm_mask = None
        mask_stats = None
    else:
        print("[2/2] Creating conservative tissue masks for aCompCor...")
        csf_mask, wm_mask, mask_stats = create_conservative_tissue_masks(
            bold_4d, brain_mask, csf_prob_img, wm_prob_img,
            csf_threshold=0.99, wm_threshold=0.99, erode_voxels=1
        )
        print()

        # 3a. Mean tissue signals (for compatibility)
        print("Computing mean tissue signals...")
        csf_signal, wm_signal = extract_tissue_signals(bold_4d, csf_mask, wm_mask)
        confounds['csf'] = csf_signal
        confounds['white_matter'] = wm_signal
        print(f"  ✅ CSF mean signal extracted")
        print(f"  ✅ WM mean signal extracted")
        print()

        # 3b. aCompCor components (fMRIPrep standard: 5 components each)
        print("Computing aCompCor components...")
        csf_components, csf_variance = compute_acompcor(bold_4d, csf_mask, n_components=5, mask_name='CSF')
        wm_components, wm_variance = compute_acompcor(bold_4d, wm_mask, n_components=5, mask_name='WM')

        # Combine CSF and WM components (total 10 components)
        # fMRIPrep convention: a_comp_cor_00 ~ a_comp_cor_09
        for i in range(5):
            confounds[f'a_comp_cor_{i:02d}'] = csf_components[:, i]  # CSF comp 0-4
        for i in range(5):
            confounds[f'a_comp_cor_{i+5:02d}'] = wm_components[:, i]  # WM comp 5-9
        print()

        # Store variance for QC plots
        acompcor_variance = {
            'csf': csf_variance,
            'wm': wm_variance,
            'csf_components': csf_components,
            'wm_components': wm_components
        }

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

    # =========================================================================
    # Quality Control: Visualizations
    # =========================================================================
    print("="*80)
    print("Quality Control: Creating Visualizations")
    print("="*80)
    print()

    qc_dir = output_dir.parent.parent / 'qc' / f'sub-{subject}'
    qc_dir.mkdir(parents=True, exist_ok=True)

    if csf_mask is not None and wm_mask is not None:
        # 1. Tissue mask visualization
        print("[1/2] Tissue mask visualization...")
        mask_viz_file = qc_dir / f'sub-{subject}_run-{run}_tissue_masks.png'
        visualize_tissue_masks(bold_4d, brain_mask, csf_mask, wm_mask, mask_viz_file)
        print()

        # 2. aCompCor quality control
        print("[2/2] aCompCor quality control...")
        acompcor_qc_file = qc_dir / f'sub-{subject}_run-{run}_acompcor_qc.png'
        validate_acompcor_quality(
            acompcor_variance['csf_components'],
            acompcor_variance['wm_components'],
            acompcor_variance['csf'],
            acompcor_variance['wm'],
            acompcor_qc_file
        )
        print()

        # Save mask statistics
        stats_file = qc_dir / f'sub-{subject}_run-{run}_mask_stats.json'
        import json
        with open(stats_file, 'w') as f:
            json.dump(mask_stats, f, indent=2)
        print(f"  ✅ Mask statistics saved: {stats_file}")
        print()
    else:
        print("  ⚠️  Skipping visualizations (tissue masks not available)")
        print()

    # Summary statistics
    print("="*80)
    print("Summary Statistics")
    print("="*80)
    print(f"Motion:")
    print(f"  Mean FD: {fd.mean():.4f} mm")
    print(f"  Max FD: {fd.max():.4f} mm")
    print(f"  Timepoints with FD > 0.5mm: {np.sum(fd > 0.5)} ({np.sum(fd > 0.5)/len(fd)*100:.1f}%)")
    print()

    if mask_stats is not None:
        print(f"Tissue Masks (Partial FOV check):")
        print(f"  Brain voxels: {mask_stats['n_brain_voxels']}")
        print(f"  CSF voxels: {mask_stats['n_csf_voxels']} ({mask_stats['csf_coverage']:.2f}%)")
        print(f"  WM voxels: {mask_stats['n_wm_voxels']} ({mask_stats['wm_coverage']:.2f}%)")
        print()

        if mask_stats['n_csf_voxels'] == 0:
            print(f"  ⚠️  WARNING: No CSF voxels found!")
            print(f"     Partial FOV likely excludes ventricles.")
            print(f"     CSF aCompCor components will be zero.")
        if mask_stats['n_wm_voxels'] == 0:
            print(f"  ⚠️  WARNING: No WM voxels found!")
            print(f"     Check brain mask and tissue probability map alignment.")

    print()
    print(f"QC outputs: {qc_dir}/")
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
