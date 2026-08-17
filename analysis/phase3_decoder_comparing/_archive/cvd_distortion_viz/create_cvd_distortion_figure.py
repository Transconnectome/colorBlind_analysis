#!/usr/bin/env python3
"""
Multi-panel CVD color distortion figure (3 rows × 4 columns).

Row per CVD subject: stimulus → anatomy → surface → distortion
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import gridspec
import nibabel as nib
from nilearn import datasets, plotting, surface
from pathlib import Path
from scipy.spatial.distance import pdist, squareform
import sys
import warnings
import json
warnings.filterwarnings('ignore')

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import existing utilities
from validation.scripts.utils.rdm_visualization import (
    COLOR_RGB, COLOR_NAMES, COLOR_LABELS
)
from phase2_SRM_across_between.brain_mapping_utils import VoxelToBrainMapper

# Configuration
BASE_DIR = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis')
C010_DIR = BASE_DIR / 'analysis/phase1_preprocess_decoding/results/full_dataset_C010'
MASK_DIR = BASE_DIR / 'analysis/roi_masks/method3_header_mi/method3_header_mi'
ATLAS_DIR = BASE_DIR / 'ProbAtlas_v4/subj_vol_all'

CVD_SUBJECTS = {'sub-08': 'Deutan', 'sub-09': 'Protan', 'sub-10': 'Deutan'}
HC_SUBJECTS = [f'sub-{i:02d}' for i in range(1, 8)]

# ROI directory name mapping (hV4 → V4 on disk)
ROI_DIR_MAP = {'V1': 'V1', 'V2': 'V2', 'V3': 'V3', 'hV4': 'V4'}

# FDR results path
FDR_RESULTS_PATH = BASE_DIR / 'analysis/phase5_filter_optimization/pre_validation/results/fdr_corrected/filter_pre_validation_fdr_corrected.json'


def load_subject_data(subject_id, roi):
    """
    Load amplitudes, mask, and compute RMS activation.

    Parameters
    ----------
    subject_id : str
        Subject ID (e.g., 'sub-08')
    roi : str
        ROI name (V1, V2, V3, hV4)

    Returns
    -------
    dict with keys:
        - amplitudes: (6, 8, n_voxels) array
        - mapper: VoxelToBrainMapper instance
        - rms_activation: (n_voxels,) RMS values
    """
    roi_dir = ROI_DIR_MAP[roi]

    # Load amplitudes (6 runs × 8 colors × n_voxels)
    amps_path = C010_DIR / subject_id / roi_dir / 'amplitudes_procrustes.npy'
    if not amps_path.exists():
        raise FileNotFoundError(f"Amplitudes not found: {amps_path}")

    amps = np.load(amps_path)
    print(f"  Loaded {subject_id} {roi}: amplitudes shape {amps.shape}")

    # Load mask and create mapper
    # Note: mask files use ROI name as-is (hV4 not V4)
    mask_file = f'{roi}_mask_thr50_intnearest_binTrue_maskfunc_gmTrue_subjFalse.nii.gz'
    mask_path = MASK_DIR / subject_id / 'roi_pipeline' / mask_file

    if not mask_path.exists():
        raise FileNotFoundError(f"Mask not found: {mask_path}")

    mapper = VoxelToBrainMapper(roi, str(mask_path))

    # Compute RMS activation: sqrt(mean(mean(amps)^2))
    # Average across runs first
    amps_mean = amps.mean(axis=0)  # (8, n_voxels)
    # RMS across colors
    rms = np.sqrt(np.mean(amps_mean**2, axis=0))  # (n_voxels,)

    print(f"  RMS activation range: [{rms.min():.3f}, {rms.max():.3f}]")

    return {
        'amplitudes': amps,
        'mapper': mapper,
        'rms_activation': rms
    }


def compute_rdm_from_amplitudes(amplitudes):
    """
    Compute RDM using correlation distance.

    Parameters
    ----------
    amplitudes : np.ndarray
        (6, 8, n_voxels) array

    Returns
    -------
    rdm : np.ndarray
        (8, 8) symmetric RDM
    """
    # Average across runs
    patterns = amplitudes.mean(axis=0)  # (8, n_voxels)

    # Compute pairwise correlation distance
    rdm = squareform(pdist(patterns, metric='correlation'))

    return rdm


def compute_hc_mean_rdm(roi):
    """
    Average RDM across HC subjects.

    Parameters
    ----------
    roi : str
        ROI name

    Returns
    -------
    hc_mean_rdm : np.ndarray
        (8, 8) mean HC RDM
    """
    print(f"\nComputing HC mean RDM for {roi}...")
    rdms = []

    for subj in HC_SUBJECTS:
        try:
            data = load_subject_data(subj, roi)
            rdm = compute_rdm_from_amplitudes(data['amplitudes'])
            rdms.append(rdm)
        except FileNotFoundError as e:
            print(f"  Warning: Skipping {subj} - {e}")
            continue

    if len(rdms) == 0:
        raise ValueError(f"No HC subjects found for {roi}")

    hc_mean_rdm = np.mean(rdms, axis=0)
    print(f"  Averaged {len(rdms)} HC subjects")

    return hc_mean_rdm


def load_fdr_significant_pairs(subject_id, roi):
    """
    Load Within-ROI FDR-corrected significant color pairs for a subject-ROI.

    Parameters
    ----------
    subject_id : str
        Subject ID (e.g., 'sub-08')
    roi : str
        ROI name (V1, V2, V3, hV4)

    Returns
    -------
    significant_pairs : list of str
        List of significant color pair names (e.g., ['red-green', 'blue-purple'])
        Empty list if no pairs survived within-ROI FDR correction
    """
    if not FDR_RESULTS_PATH.exists():
        print(f"  Warning: FDR results not found at {FDR_RESULTS_PATH}")
        return []

    try:
        with open(FDR_RESULTS_PATH) as f:
            fdr_data = json.load(f)

        sig_pairs = []

        # Use all_tests with within-ROI FDR correction
        if 'all_tests' in fdr_data:
            # Filter tests for this subject-ROI combination
            roi_tests = [t for t in fdr_data['all_tests']
                        if t['subject'] == subject_id and t['roi'] == roi]

            # Get pairs that survived within-ROI FDR (boolean field)
            for test in roi_tests:
                if test.get('fdr_within_roi') == True:
                    sig_pairs.append(test['pair'])

        return sig_pairs

    except Exception as e:
        print(f"  Warning: Error loading FDR results: {e}")
        return []


# ============================================================================
# Panel Creation Functions
# ============================================================================

def create_panel_A_color_wheel(ax):
    """
    Panel A: Circular color wheel stimulus.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Target axes
    """
    angles = np.linspace(0, 2*np.pi, 8, endpoint=False)
    radius = 0.5  # Further reduced to make more room for labels

    for i, (angle, color_key) in enumerate(zip(angles, COLOR_RGB.keys())):
        x, y = radius * np.cos(angle), radius * np.sin(angle)

        # Draw color patch (smaller circles)
        circle = plt.Circle((x, y), 0.08, color=COLOR_RGB[color_key],
                           edgecolor='black', linewidth=1.8, zorder=10)
        ax.add_patch(circle)

        # Label much further outside circle
        label_radius = 1.1  # Significantly increased from 1.0
        label_x = label_radius * np.cos(angle)
        label_y = label_radius * np.sin(angle)
        ax.text(label_x, label_y, COLOR_NAMES[i],
               ha='center', va='center',
               fontsize=8, fontweight='bold')

    ax.set_xlim(-1.4, 1.4)
    ax.set_ylim(-1.4, 1.4)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('Stimuli', fontsize=11, fontweight='bold', pad=5)


def create_panel_B_glass_brain(ax, mapper, activation):
    """
    Panel B: Glass brain with ROI activation.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Target axes
    mapper : VoxelToBrainMapper
        Brain mapper with ROI mask
    activation : np.ndarray
        (n_voxels,) activation values
    """
    brain_img = mapper.create_brain_volume(activation)

    # Determine color scale
    vmax = np.percentile(activation[activation > 0], 95)

    plotting.plot_glass_brain(
        brain_img,
        display_mode='lyrz',
        colorbar=True,
        cmap='Reds',
        vmin=0,
        vmax=vmax,
        plot_abs=False,
        axes=ax,
        title='Whole Brain',
        black_bg=False
    )


def create_panel_C_posterior_surface(ax, mapper, activation, roi, fsaverage, vmin, vmax):
    """
    Panel C: Posterior inflated surface with activation.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Target axes
    mapper : VoxelToBrainMapper
        Brain mapper
    activation : np.ndarray
        (n_voxels,) activation values
    roi : str
        ROI name
    fsaverage : dict
        fsaverage surface data
    vmin, vmax : float
        Color scale limits
    """
    brain_img = mapper.create_brain_volume(activation)

    # Try both hemispheres and use the one with more signal
    best_texture = None
    best_hemi = None
    max_signal = 0

    for hemi in ['left', 'right']:
        # Project to surface
        texture = surface.vol_to_surf(
            brain_img,
            fsaverage[f'pial_{hemi}'],
            radius=10.0,  # Large radius to ensure we capture the ROI
            interpolation='linear',
            kind='ball',
            n_samples=20  # More samples for better coverage
        )

        # Replace NaN with 0
        texture = np.nan_to_num(texture, nan=0.0)
        signal_sum = np.sum(texture)

        if signal_sum > max_signal:
            max_signal = signal_sum
            best_texture = texture
            best_hemi = hemi

    if best_texture is None:
        best_hemi = 'left'
        best_texture = np.zeros(fsaverage['pial_left'][0].shape[0])

    n_nonzero = np.sum(best_texture > 0)
    print(f"    Surface projection ({best_hemi}): {n_nonzero} vertices, "
          f"max={best_texture.max():.4f}, sum={np.sum(best_texture):.2f}")

    # Plot on inflated surface
    plotting.plot_surf_stat_map(
        fsaverage[f'infl_{best_hemi}'],
        best_texture,
        hemi=best_hemi,
        view='posterior',
        bg_map=fsaverage[f'sulc_{best_hemi}'],
        cmap='hot',
        vmin=0,
        vmax=vmax,
        colorbar=True,
        threshold=0.001,  # Very small threshold to show signal
        axes=ax,
        title='Occipital Surface'
    )


def create_panel_D_rdm_distortion_bars(ax, cvd_rdm, hc_rdm, subject_id, roi, top_n=10):
    """
    Panel D: Bar plot of RDM distortions (CVD - HC).
    Shows only FDR-corrected significant pairs, or top pairs if none significant.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Target axes
    cvd_rdm : np.ndarray
        (8, 8) CVD RDM
    hc_rdm : np.ndarray
        (8, 8) HC mean RDM
    subject_id : str
        Subject ID for FDR lookup
    roi : str
        ROI name for FDR lookup
    top_n : int
        Number of top pairs to show if no FDR-significant pairs
    """
    # Compute difference
    diff_rdm = cvd_rdm - hc_rdm

    # Extract upper triangle (unique pairs)
    mask = np.triu(np.ones_like(diff_rdm, dtype=bool), k=1)
    diffs = diff_rdm[mask]

    # Create color pair labels (lowercase for FDR matching)
    pairs = []
    pairs_display = []
    for i in range(8):
        for j in range(i+1, 8):
            pairs.append(f'{COLOR_NAMES[i].lower()}-{COLOR_NAMES[j].lower()}')
            pairs_display.append(f'{COLOR_NAMES[i][:3]}-{COLOR_NAMES[j][:3]}')

    # Load FDR-significant pairs
    fdr_sig_pairs = load_fdr_significant_pairs(subject_id, roi)

    if fdr_sig_pairs:
        # Show only FDR-significant pairs
        print(f"    Showing {len(fdr_sig_pairs)} FDR-significant pairs")

        # Find indices of significant pairs
        sig_indices = []
        for fdr_pair in fdr_sig_pairs:
            if fdr_pair in pairs:
                sig_indices.append(pairs.index(fdr_pair))

        # Sort by absolute magnitude
        sig_indices_sorted = sorted(sig_indices, key=lambda i: abs(diffs[i]), reverse=True)

        # Plot
        colors = ['#FF6B6B' if diffs[i] > 0 else '#4ECDC4' for i in sig_indices_sorted]
        x_pos = np.arange(len(sig_indices_sorted))
        ax.barh(x_pos, [diffs[i] for i in sig_indices_sorted], color=colors,
                edgecolor='black', linewidth=1.5, alpha=0.8)

        ax.set_yticks(x_pos)
        ax.set_yticklabels([pairs_display[i] + ' *' for i in sig_indices_sorted], fontsize=8)
        title_suffix = f'(within-ROI FDR q<0.05, n={len(sig_indices_sorted)})'
    else:
        # No FDR-significant pairs - show top pairs by magnitude
        print(f"    No FDR-significant pairs, showing top {top_n} by magnitude")

        sorted_idx = np.argsort(np.abs(diffs))[::-1][:top_n]
        colors = ['#FF6B6B' if diffs[i] > 0 else '#4ECDC4' for i in sorted_idx]

        x_pos = np.arange(top_n)
        ax.barh(x_pos, diffs[sorted_idx], color=colors,
                edgecolor='black', linewidth=1.5, alpha=0.8)

        ax.set_yticks(x_pos)
        ax.set_yticklabels([pairs_display[i] for i in sorted_idx], fontsize=8)
        title_suffix = '(top 10, uncorrected)'

    # Format
    ax.set_xlabel('Δ Dissimilarity (CVD - HC)', fontsize=9, fontweight='bold')
    ax.axvline(0, color='black', linewidth=2, linestyle='--', zorder=0)
    ax.grid(axis='x', alpha=0.3, linestyle=':', linewidth=0.5)
    ax.set_title(f'Color Pair Distortions\n{title_suffix}', fontsize=10, fontweight='bold')

    # Invert y-axis so largest is at top
    ax.invert_yaxis()


# ============================================================================
# Main Figure Assembly
# ============================================================================

def create_cvd_distortion_figure(roi='V2', output_path=None):
    """
    Create 3×4 multi-panel CVD distortion figure.

    Parameters
    ----------
    roi : str
        ROI name (V1, V2, V3, hV4)
    output_path : str or Path, optional
        Output file path (auto-generated if None)

    Returns
    -------
    output_path : Path
        Path to saved figure
    """
    print(f"\n{'='*70}")
    print(f"Creating CVD distortion figure for {roi}")
    print(f"{'='*70}\n")

    # Load CVD data
    print("Loading CVD subject data...")
    cvd_data = {}
    for subject_id in CVD_SUBJECTS.keys():
        try:
            cvd_data[subject_id] = load_subject_data(subject_id, roi)
        except FileNotFoundError as e:
            print(f"ERROR: {e}")
            raise

    # Compute HC mean RDM
    hc_mean_rdm = compute_hc_mean_rdm(roi)

    # Fetch fsaverage surfaces
    print("\nFetching fsaverage5 surfaces...")
    fsaverage = datasets.fetch_surf_fsaverage('fsaverage5')

    # Determine shared color scale for surface plots
    all_rms = [cvd_data[s]['rms_activation'] for s in CVD_SUBJECTS.keys()]
    vmin = np.percentile(np.concatenate(all_rms), 5)
    vmax = np.percentile(np.concatenate(all_rms), 95)
    print(f"Surface color scale: [{vmin:.3f}, {vmax:.3f}]")

    # Create figure
    print("\nCreating figure...")
    fig = plt.figure(figsize=(20, 16), facecolor='white', dpi=150)
    gs = gridspec.GridSpec(
        3, 4,
        figure=fig,
        hspace=0.30,
        wspace=0.20,
        left=0.06,
        right=0.96,
        top=0.92,
        bottom=0.05,
        width_ratios=[1.0, 2.5, 3.0, 2.5]
    )

    # Create panels for each CVD subject
    for row_idx, (subject_id, cvd_type) in enumerate(CVD_SUBJECTS.items()):
        print(f"\nRow {row_idx+1}: {subject_id} ({cvd_type})")
        data = cvd_data[subject_id]

        # Panel A: Color wheel
        print("  Panel A: Color wheel")
        ax_A = plt.subplot(gs[row_idx, 0])
        create_panel_A_color_wheel(ax_A)

        # Panel B: Glass brain
        print("  Panel B: Glass brain")
        ax_B = plt.subplot(gs[row_idx, 1])
        create_panel_B_glass_brain(ax_B, data['mapper'], data['rms_activation'])

        # Panel C: Posterior surface
        print("  Panel C: Posterior surface")
        ax_C = plt.subplot(gs[row_idx, 2], projection='3d')
        create_panel_C_posterior_surface(
            ax_C, data['mapper'], data['rms_activation'],
            roi, fsaverage, vmin, vmax
        )

        # Panel D: RDM distortion
        print("  Panel D: RDM distortion bars")
        ax_D = plt.subplot(gs[row_idx, 3])
        cvd_rdm = compute_rdm_from_amplitudes(data['amplitudes'])
        create_panel_D_rdm_distortion_bars(ax_D, cvd_rdm, hc_mean_rdm, subject_id, roi)

        # Row label (subject ID)
        fig.text(
            0.01, 0.78 - row_idx*0.31,
            f'{subject_id}\n({cvd_type})',
            fontsize=13, fontweight='bold',
            va='center', ha='left'
        )

    # Overall title
    fig.suptitle(
        f'{roi} Color Representation Distortions in CVD',
        fontsize=17, fontweight='bold', y=0.97
    )

    # Column labels
    col_titles = ['A. Stimuli', 'B. Whole Brain', 'C. Occipital Surface', 'D. Distortions']
    col_x_positions = [0.06, 0.25, 0.48, 0.75]
    for col_x, title in zip(col_x_positions, col_titles):
        fig.text(col_x, 0.95, title, fontsize=12, fontweight='bold', ha='left')

    # Save
    if output_path is None:
        output_dir = BASE_DIR / 'analysis/phase5_filter_optimization/figures'
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f'cvd_distortion_figure_{roi}.png'

    output_path = Path(output_path)
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()

    print(f"\n{'='*70}")
    print(f"SUCCESS: Saved figure to:")
    print(f"  {output_path}")
    print(f"  Size: {output_path.stat().st_size / 1e6:.1f} MB")
    print(f"{'='*70}\n")

    return output_path


# ============================================================================
# CLI Entry Point
# ============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Create multi-panel CVD color distortion figure'
    )
    parser.add_argument(
        '--roi',
        type=str,
        default='V2',
        choices=['V1', 'V2', 'V3', 'hV4'],
        help='ROI name (default: V2)'
    )
    parser.add_argument(
        '--all-rois',
        action='store_true',
        help='Generate figures for all ROIs'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output path (auto-generated if not specified)'
    )

    args = parser.parse_args()

    if args.all_rois:
        # Generate for all ROIs
        for roi in ['V1', 'V2', 'V3', 'hV4']:
            try:
                create_cvd_distortion_figure(roi)
            except Exception as e:
                print(f"\nERROR generating {roi}: {e}\n")
                continue
    else:
        # Generate for specified ROI
        create_cvd_distortion_figure(args.roi, args.output)
