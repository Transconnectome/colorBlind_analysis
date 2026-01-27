#!/usr/bin/env python3
"""
Visualize ROI overlay on T1w space for quality control.

This script creates detailed visualization of ROI masks overlaid on T1w space
BOLD images to verify proper alignment in occipital cortex.

Usage:
    python visualize_native_roi.py --subject 02 --roi V1 --run 1

Author: Modified for T1w space analysis
Date: 2025-01-23
"""

import argparse
import numpy as np
import nibabel as nib
import matplotlib.pyplot as plt
from pathlib import Path
from nilearn import plotting, image


def create_roi_overlay(bold_ref, roi_mask, output_path, title="ROI Overlay"):
    """
    Create multi-view overlay of ROI on BOLD reference.

    Parameters
    ----------
    bold_ref : str or Path
        Path to native BOLD reference image
    roi_mask : str or Path
        Path to ROI mask in native BOLD space
    output_path : str or Path
        Path to save output figure
    title : str
        Figure title
    """
    # Load images
    bold_img = nib.load(bold_ref)
    roi_img = nib.load(roi_mask)

    # Create orthogonal views (x, y, z)
    display = plotting.plot_roi(
        roi_img,
        bg_img=bold_img,
        display_mode='ortho',
        cut_coords=(0, -80, -10),  # Approximate location of visual cortex
        alpha=0.5,
        cmap='autumn',
        title=title,
        draw_cross=False
    )

    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"✓ Saved overlay figure: {output_path}")


def create_intensity_histogram(roi_file, output_path, title="ROI Intensity Distribution"):
    """
    Create histogram of ROI probability values.

    Parameters
    ----------
    roi_file : str or Path
        Path to ROI file (probabilistic or binary)
    output_path : str or Path
        Path to save output figure
    title : str
        Figure title
    """
    # Load ROI
    roi_img = nib.load(roi_file)
    roi_data = roi_img.get_fdata()

    # Get non-zero values
    nonzero_vals = roi_data[roi_data > 0]

    if len(nonzero_vals) == 0:
        print("⚠ No non-zero voxels in ROI")
        return

    # Create histogram
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    ax.hist(nonzero_vals, bins=50, edgecolor='black', alpha=0.7)
    ax.set_xlabel('Intensity Value', fontsize=12)
    ax.set_ylabel('Voxel Count', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)

    # Add statistics
    stats_text = f"N voxels: {len(nonzero_vals)}\n"
    stats_text += f"Mean: {np.mean(nonzero_vals):.2f}\n"
    stats_text += f"Median: {np.median(nonzero_vals):.2f}\n"
    stats_text += f"Max: {np.max(nonzero_vals):.2f}"

    ax.text(0.98, 0.98, stats_text,
            transform=ax.transAxes,
            verticalalignment='top',
            horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
            fontsize=10)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"✓ Saved intensity histogram: {output_path}")


def check_roi_location(roi_file, bold_ref):
    """
    Check if ROI is located in expected posterior occipital region.

    Parameters
    ----------
    roi_file : str or Path
        Path to ROI mask
    bold_ref : str or Path
        Path to BOLD reference

    Returns
    -------
    dict
        Dictionary with location statistics
    """
    # Load ROI
    roi_img = nib.load(roi_file)
    roi_data = roi_img.get_fdata()

    # Get center of mass
    from scipy.ndimage import center_of_mass

    if np.sum(roi_data > 0) == 0:
        print("⚠ Empty ROI - cannot compute location")
        return None

    com = center_of_mass(roi_data > 0)

    # Convert voxel coordinates to mm (MNI space)
    affine = roi_img.affine
    com_mm = nib.affines.apply_affine(affine, com)

    # Check if in posterior region (negative Y for occipital)
    is_posterior = com_mm[1] < -50  # Y < -50mm is posterior

    # Get extent in each direction
    coords = np.where(roi_data > 0)
    extent = {
        'x_range': (coords[0].min(), coords[0].max()),
        'y_range': (coords[1].min(), coords[1].max()),
        'z_range': (coords[2].min(), coords[2].max()),
        'center_vox': com,
        'center_mm': com_mm,
        'is_posterior': is_posterior,
        'n_voxels': len(coords[0])
    }

    return extent


def main():
    parser = argparse.ArgumentParser(
        description='Visualize ROI overlay on native BOLD space'
    )
    parser.add_argument('--subject', type=str, required=True,
                        help='Subject ID (e.g., 02, 03, 05)')
    parser.add_argument('--roi', type=str, required=True,
                        help='ROI name (V1, V2, V3, hV4)')
    parser.add_argument('--run', type=int, default=1,
                        help='Run number (default: 1)')
    parser.add_argument('--derivatives', type=str,
                        default='/scratch/connectome/haba6030/colorBlind/analysis/prep_trials/results/native_roi',
                        help='Path to derivatives directory')
    parser.add_argument('--fmriprep', type=str,
                        default='/storage/connectome/haba6030/fmriprep_out_method3_header_mi',
                        help='Path to fMRIPrep output directory')

    args = parser.parse_args()

    # Construct paths
    subj_deriv_dir = Path(args.derivatives) / f"sub-{args.subject}"
    fmriprep_func_dir = Path(args.fmriprep) / f"sub-{args.subject}" / "func"

    # Input files (T1w space)
    roi_prob = subj_deriv_dir / f"sub-{args.subject}_{args.roi}_space-T1w.nii.gz"
    roi_mask = subj_deriv_dir / f"sub-{args.subject}_{args.roi}_space-T1w_mask.nii.gz"
    bold_t1w = fmriprep_func_dir / f"sub-{args.subject}_task-rsvp_run-{args.run}_space-T1w_desc-preproc_bold.nii.gz"

    # Check files exist
    if not roi_prob.exists():
        print(f"❌ ROI file not found: {roi_prob}")
        return 1

    if not roi_mask.exists():
        print(f"❌ ROI mask not found: {roi_mask}")
        return 1

    if not bold_t1w.exists():
        print(f"❌ T1w space BOLD not found: {bold_t1w}")
        return 1

    print("=" * 80)
    print("T1w Space ROI Visualization")
    print("=" * 80)
    print(f"Subject: sub-{args.subject}")
    print(f"ROI: {args.roi}")
    print(f"Run: {args.run}")
    print()

    # Output paths
    overlay_png = subj_deriv_dir / f"QC_sub-{args.subject}_{args.roi}_detailed.png"
    hist_png = subj_deriv_dir / f"QC_sub-{args.subject}_{args.roi}_histogram.png"

    # Create visualizations
    print("📊 Creating overlay visualization...")
    create_roi_overlay(
        bold_t1w, roi_mask, overlay_png,
        title=f"sub-{args.subject} {args.roi} ROI Overlay (T1w Space)"
    )

    print("📊 Creating intensity histogram...")
    create_intensity_histogram(
        roi_prob, hist_png,
        title=f"sub-{args.subject} {args.roi} Intensity Distribution"
    )

    # Check location
    print("🔍 Checking ROI location...")
    location = check_roi_location(roi_mask, bold_t1w)

    if location is not None:
        print()
        print("ROI Location Statistics:")
        print(f"  Voxels: {location['n_voxels']}")
        print(f"  Center (vox): ({location['center_vox'][0]:.1f}, "
              f"{location['center_vox'][1]:.1f}, {location['center_vox'][2]:.1f})")
        print(f"  Center (mm):  ({location['center_mm'][0]:.1f}, "
              f"{location['center_mm'][1]:.1f}, {location['center_mm'][2]:.1f})")
        print(f"  Posterior location: {'✓ YES' if location['is_posterior'] else '✗ NO (WARNING)'}")

        if not location['is_posterior']:
            print()
            print("⚠ WARNING: ROI center is not in posterior region!")
            print("   Visual cortex (V1-V4) should be in posterior occipital cortex (Y < -50mm)")
            print("   → Manual inspection strongly recommended")

    print()
    print("=" * 80)
    print("✓ Visualization complete")
    print()
    print("Output files:")
    print(f"  {overlay_png}")
    print(f"  {hist_png}")
    print()
    print("Next steps:")
    print("  1. Open overlay image to verify ROI location")
    print("  2. Check that ROI is in posterior occipital cortex")
    print("  3. If location is correct, proceed with functional analysis")
    print()

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
