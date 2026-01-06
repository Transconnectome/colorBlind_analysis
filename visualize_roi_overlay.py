#!/usr/bin/env python3
"""
Visualize ROI Overlay on Functional Data

Creates visual overlays to check if ROI masks are in the correct location.
For problem subjects, this will reveal if the alignment is actually correct.
"""

import nibabel as nib
import numpy as np
from nilearn import plotting
import matplotlib.pyplot as plt
from pathlib import Path

# Configuration
BASE_DIR = Path('/scratch/connectome/haba6030/colorBlind')
FMRIPREP_DIR = Path('/storage/connectome/haba6030/fmriprep_out_original_v3')  # v3: FreeSurfer removed
DERIVATIVES_DIR = BASE_DIR / 'derivatives'
OUTPUT_DIR = BASE_DIR / 'logs' / 'alignment_visualizations'

# Subjects to check
PROBLEM_SUBJECTS = ['02', '03', '04', '09', '10']
GOOD_SUBJECTS = ['01', '05']  # For comparison

def visualize_subject(subject_id, is_problem=False):
    """Create overlay visualizations for one subject"""
    print(f"\n{'='*70}")
    print(f"Visualizing sub-{subject_id}")
    print(f"{'='*70}")

    # Paths
    subj_dir = FMRIPREP_DIR / f'sub-{subject_id}'
    func_dir = subj_dir / 'func'
    deriv_dir = DERIVATIVES_DIR / f'sub-{subject_id}' / 'roi_pipeline'

    boldref_path = func_dir / f'sub-{subject_id}_task-rsvp_run-1_space-MNI152NLin2009cAsym_res-2_boldref.nii.gz'
    brain_mask_path = func_dir / f'sub-{subject_id}_task-rsvp_run-1_space-MNI152NLin2009cAsym_res-2_desc-brain_mask.nii.gz'

    if not boldref_path.exists():
        print(f"⚠️  BOLDREF not found")
        return

    # Load images
    boldref = nib.load(str(boldref_path))
    brain_mask = nib.load(str(brain_mask_path)) if brain_mask_path.exists() else None

    # Create output directory
    subj_output_dir = OUTPUT_DIR / f'sub-{subject_id}'
    subj_output_dir.mkdir(parents=True, exist_ok=True)

    # ROIs to visualize
    rois = ['V1', 'V2', 'V3', 'hV4']

    for roi in rois:
        roi_mask_none = deriv_dir / f'{roi}_mask_thr50_intnearest_binTrue_masknone_gmTrue_subjFalse.nii.gz'
        roi_mask_func = deriv_dir / f'{roi}_mask_thr50_intnearest_binTrue_maskfunc_gmTrue_subjFalse.nii.gz'

        # Check if ROI masks exist
        if not roi_mask_none.exists():
            print(f"  ⚠️  {roi} mask=none not found")
            continue

        # Load ROI masks
        roi_none = nib.load(str(roi_mask_none))
        roi_none_data = roi_none.get_fdata()
        roi_none_voxels = np.count_nonzero(roi_none_data)

        roi_func_voxels = 0
        if roi_mask_func.exists():
            roi_func = nib.load(str(roi_mask_func))
            roi_func_data = roi_func.get_fdata()
            roi_func_voxels = np.count_nonzero(roi_func_data)

        print(f"\n  {roi}:")
        print(f"    mask=none voxels: {roi_none_voxels}")
        print(f"    mask=func voxels: {roi_func_voxels}")

        # Create visualization
        fig = plt.figure(figsize=(20, 10))

        # Subplot 1: ROI on BOLDREF (mask=none)
        ax1 = plt.subplot(2, 3, 1)
        display = plotting.plot_roi(
            roi_none,
            bg_img=boldref,
            display_mode='ortho',
            cut_coords=None,
            title=f'sub-{subject_id} {roi} mask=none\nVoxels: {roi_none_voxels}',
            axes=ax1,
            draw_cross=True,
            annotate=True
        )

        # Subplot 2: ROI on BOLDREF (sagittal)
        ax2 = plt.subplot(2, 3, 2)
        display = plotting.plot_roi(
            roi_none,
            bg_img=boldref,
            display_mode='x',
            cut_coords=5,
            title=f'{roi} - Sagittal slices',
            axes=ax2,
            annotate=True
        )

        # Subplot 3: Brain mask overlay
        if brain_mask is not None:
            ax3 = plt.subplot(2, 3, 3)
            display = plotting.plot_roi(
                brain_mask,
                bg_img=boldref,
                display_mode='ortho',
                cut_coords=None,
                title=f'Brain Mask Coverage',
                axes=ax3,
                draw_cross=True,
                cmap='Reds',
                alpha=0.5
            )

        # Subplot 4: Axial view of ROI
        ax4 = plt.subplot(2, 3, 4)
        display = plotting.plot_roi(
            roi_none,
            bg_img=boldref,
            display_mode='z',
            cut_coords=5,
            title=f'{roi} - Axial slices',
            axes=ax4,
            annotate=True
        )

        # Subplot 5: Coronal view focusing on occipital
        ax5 = plt.subplot(2, 3, 5)
        display = plotting.plot_roi(
            roi_none,
            bg_img=boldref,
            display_mode='y',
            cut_coords=[-90, -80, -70, -60, -50],  # Posterior slices
            title=f'{roi} - Coronal (Posterior)',
            axes=ax5,
            annotate=True
        )

        # Subplot 6: Check if ROI overlaps with functional signal
        ax6 = plt.subplot(2, 3, 6)
        boldref_data = boldref.get_fdata()

        # Calculate overlap with non-zero BOLD signal
        bold_nonzero = boldref_data > np.percentile(boldref_data[boldref_data > 0], 5)
        roi_in_bold = roi_none_data * bold_nonzero
        overlap_voxels = np.count_nonzero(roi_in_bold)
        overlap_ratio = overlap_voxels / roi_none_voxels if roi_none_voxels > 0 else 0

        ax6.text(0.1, 0.5,
                 f'{roi} Overlap Analysis\n\n'
                 f'ROI voxels: {roi_none_voxels}\n'
                 f'Overlap with BOLD signal: {overlap_voxels}\n'
                 f'Overlap ratio: {100*overlap_ratio:.1f}%\n\n'
                 f'mask=func voxels: {roi_func_voxels}\n'
                 f'Difference: {roi_none_voxels - roi_func_voxels}',
                 fontsize=12,
                 verticalalignment='center')
        ax6.axis('off')

        plt.tight_layout()

        # Save
        output_path = subj_output_dir / f'{roi}_overlay.png'
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()

        print(f"    ✓ Saved: {output_path}")

    print(f"\n✓ Completed sub-{subject_id}")

def main():
    """Main visualization"""
    print("="*70)
    print("ROI OVERLAY VISUALIZATION")
    print("="*70)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("\nVisualizing GOOD subjects (for comparison):")
    for subject in GOOD_SUBJECTS:
        visualize_subject(subject, is_problem=False)

    print("\n\nVisualizing PROBLEM subjects:")
    for subject in PROBLEM_SUBJECTS:
        visualize_subject(subject, is_problem=True)

    print("\n" + "="*70)
    print("VISUALIZATION COMPLETE")
    print(f"Output: {OUTPUT_DIR}")
    print("="*70)

if __name__ == "__main__":
    main()
