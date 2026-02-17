#!/usr/bin/env python3
"""
Visual Cortex Visualization - ACTUALLY VISIBLE VERSION

Problem: Sparse voxels (400 out of 41,473) don't show up in slices.
Solution: Smooth/dilate voxel values to make them visible.

Three strategies:
1. Gaussian smoothing (sigma=2-3mm) - spread values spatially
2. Morphological dilation - expand each voxel to small sphere
3. ROI-average fill - fill entire ROI with average value
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import gridspec, patches
import nibabel as nib
from nilearn import plotting, image
from scipy.ndimage import gaussian_filter, grey_dilation
from pathlib import Path
import sys
sys.path.insert(0, '.')
from brain_mapping_utils import load_bilateral_mask


def make_voxels_visible(brain_img, method='smooth', sigma=2.5, dilation_size=3):
    """
    Make sparse voxels visible by smoothing or dilation.

    Parameters
    ----------
    brain_img : Nifti1Image
        Sparse brain volume with mostly NaN
    method : str
        'smooth' (Gaussian), 'dilate' (morphological), or 'both'
    sigma : float
        Gaussian smoothing sigma in mm
    dilation_size : int
        Dilation structure size in voxels

    Returns
    -------
    visible_img : Nifti1Image
        Smoothed/dilated volume where voxels are visible
    """
    data = brain_img.get_fdata()

    # Replace NaN with 0 for processing
    data_filled = np.nan_to_num(data, nan=0.0)

    if method == 'smooth' or method == 'both':
        print(f"  Applying Gaussian smoothing (sigma={sigma}mm)...")
        # Convert sigma from mm to voxels (assuming 1mm resolution)
        sigma_voxels = sigma / 1.0
        data_smooth = gaussian_filter(data_filled, sigma=sigma_voxels)

        if method == 'both':
            data_filled = data_smooth
        else:
            result_data = data_smooth

    if method == 'dilate' or method == 'both':
        print(f"  Applying morphological dilation (size={dilation_size})...")
        # Create structure element (sphere)
        from scipy.ndimage import generate_binary_structure, iterate_structure
        struct = generate_binary_structure(3, 1)
        struct = iterate_structure(struct, dilation_size)

        # Dilate (expand non-zero regions)
        data_dilated = grey_dilation(data_filled, footprint=struct)
        result_data = data_dilated

    # Put NaN back in completely empty regions
    result_data[data == 0] = np.nan

    # Create new image
    visible_img = nib.Nifti1Image(result_data, brain_img.affine)

    # Count visible voxels
    n_nonzero_before = np.sum(~np.isnan(data))
    n_nonzero_after = np.sum(~np.isnan(result_data))
    print(f"  Visible voxels: {n_nonzero_before} → {n_nonzero_after} ({n_nonzero_after/n_nonzero_before:.1f}× increase)")

    return visible_img


def plot_visual_cortex_visible(mapper, raw_values, proc_values, improvement,
                                subject, roi, output_dir, method='smooth'):
    """
    Create ACTUALLY VISIBLE visual cortex visualization.

    Uses smoothing/dilation to make sparse voxels show up in slices.
    """
    print("\n" + "="*80)
    print("VISUAL CORTEX VISUALIZATION - VISIBLE VERSION")
    print("="*80)
    print(f"ROI: {roi} ({len(raw_values)} voxels)")
    print(f"Subject: {subject}")
    print(f"Visibility method: {method}")

    # Create brain volumes (sparse)
    print("\nCreating sparse brain volumes...")
    img_raw = mapper.create_brain_volume(raw_values)
    img_proc = mapper.create_brain_volume(proc_values)
    img_improvement = mapper.create_brain_volume(improvement)

    # Make visible
    print("\nMaking voxels visible...")
    img_raw_visible = make_voxels_visible(img_raw, method=method, sigma=2.5)
    img_proc_visible = make_voxels_visible(img_proc, method=method, sigma=2.5)
    img_improvement_visible = make_voxels_visible(img_improvement, method=method, sigma=2.5)

    # ROI mask for contour
    roi_mask_data = mapper.binary_mask.astype(float)
    roi_mask_img = nib.Nifti1Image(roi_mask_data, mapper.affine)

    # Robust scaling
    vmin_raw = np.nanpercentile(raw_values, 5)
    vmax_raw = np.nanpercentile(raw_values, 95)
    vmin_proc = np.nanpercentile(proc_values, 5)
    vmax_proc = np.nanpercentile(proc_values, 95)
    abs_max_imp = np.nanpercentile(np.abs(improvement), 90)

    print(f"\nColor scales:")
    print(f"  Raw: [{vmin_raw:.3f}, {vmax_raw:.3f}]")
    print(f"  Proc: [{vmin_proc:.3f}, {vmax_proc:.3f}]")
    print(f"  Improvement: [{-abs_max_imp:.3f}, {abs_max_imp:.3f}]")

    # Create combined figure
    fig = plt.figure(figsize=(24, 18))

    # Occipital slice coordinates
    cut_coords = list(range(-20, 8, 3))  # 10 slices

    # Row 1: Before
    print("\nGenerating plots...")
    ax1 = plt.subplot(3, 1, 1)
    display1 = plotting.plot_stat_map(
        img_raw_visible,
        display_mode='z',
        cut_coords=cut_coords,
        colorbar=True,
        cmap='Blues',
        vmin=vmin_raw,
        vmax=vmax_raw,
        axes=ax1,
        title=f'A. Before Procrustes - {roi} (smoothed for visibility)',
        draw_cross=False,
        threshold=None,
        black_bg=False
    )
    display1.add_contours(roi_mask_img, levels=[0.25], colors='red',
                         linewidths=2.5)

    # Row 2: After
    ax2 = plt.subplot(3, 1, 2)
    display2 = plotting.plot_stat_map(
        img_proc_visible,
        display_mode='z',
        cut_coords=cut_coords,
        colorbar=True,
        cmap='Reds',
        vmin=vmin_proc,
        vmax=vmax_proc,
        axes=ax2,
        title=f'B. After Procrustes - {roi} (smoothed for visibility)',
        draw_cross=False,
        threshold=None,
        black_bg=False
    )
    display2.add_contours(roi_mask_img, levels=[0.25], colors='black',
                         linewidths=2.5)

    # Row 3: Improvement
    ax3 = plt.subplot(3, 1, 3)
    display3 = plotting.plot_stat_map(
        img_improvement_visible,
        display_mode='z',
        cut_coords=cut_coords,
        colorbar=True,
        cmap='RdYlGn',
        vmin=-abs_max_imp,
        vmax=abs_max_imp,
        axes=ax3,
        title=f'C. Improvement (Δr) - {roi} (smoothed for visibility)',
        draw_cross=False,
        threshold=None,
        black_bg=False
    )
    display3.add_contours(roi_mask_img, levels=[0.25], colors='black',
                         linewidths=2.5)

    plt.suptitle(f'{roi} Procrustes Effect - Visual Cortex (Smoothed, {subject})',
                fontsize=18, fontweight='bold', y=0.995)

    output_path = output_dir / f'{subject}_{roi}_visual_cortex_VISIBLE.png'
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"\n✅ Saved: {output_path}")
    print(f"  File size: {output_path.stat().st_size / 1024:.0f} KB")

    return output_path


def plot_roi_average_fill(mapper, raw_mean, proc_mean, improvement_mean,
                          subject, roi, output_dir):
    """
    Alternative: Fill entire ROI with average value.

    Honest representation: "This is the ROI-level average"
    """
    print("\n" + "="*80)
    print("ROI AVERAGE FILL VERSION")
    print("="*80)

    # Create volumes filled with average
    roi_mask_data = mapper.binary_mask.astype(float)

    data_raw = np.where(roi_mask_data > 0.25, raw_mean, np.nan)
    data_proc = np.where(roi_mask_data > 0.25, proc_mean, np.nan)
    data_imp = np.where(roi_mask_data > 0.25, improvement_mean, np.nan)

    img_raw = nib.Nifti1Image(data_raw, mapper.affine)
    img_proc = nib.Nifti1Image(data_proc, mapper.affine)
    img_imp = nib.Nifti1Image(data_imp, mapper.affine)

    # Plot
    fig = plt.figure(figsize=(24, 6))

    cut_coords = [-15, -10, -5, 0, 5]

    # Before
    ax1 = plt.subplot(1, 3, 1)
    plotting.plot_stat_map(
        img_raw,
        display_mode='z',
        cut_coords=cut_coords,
        colorbar=True,
        cmap='Blues',
        axes=ax1,
        title=f'Before (mean={raw_mean:.3f})',
        draw_cross=False
    )

    # After
    ax2 = plt.subplot(1, 3, 2)
    plotting.plot_stat_map(
        img_proc,
        display_mode='z',
        cut_coords=cut_coords,
        colorbar=True,
        cmap='Reds',
        axes=ax2,
        title=f'After (mean={proc_mean:.3f})',
        draw_cross=False
    )

    # Improvement
    ax3 = plt.subplot(1, 3, 3)
    plotting.plot_stat_map(
        img_imp,
        display_mode='z',
        cut_coords=cut_coords,
        colorbar=True,
        cmap='RdYlGn',
        axes=ax3,
        title=f'Improvement (Δ={improvement_mean:.3f})',
        draw_cross=False,
        symmetric_cmap=True
    )

    plt.suptitle(f'{roi} ROI-Level Average ({subject})',
                fontsize=16, fontweight='bold')

    output_path = output_dir / f'{subject}_{roi}_roi_average_fill.png'
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"✅ Saved: {output_path}")
    return output_path


if __name__ == '__main__':
    import argparse
    from scipy.stats import pearsonr

    parser = argparse.ArgumentParser(description='Actually visible visual cortex visualization')
    parser.add_argument('--subject', type=str, default='sub-08')
    parser.add_argument('--roi', type=str, default='V2')
    parser.add_argument('--method', type=str, default='smooth',
                       choices=['smooth', 'dilate', 'both'])
    args = parser.parse_args()

    # Paths
    atlas_dir = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/ProbAtlas_v4/subj_vol_all')
    base_dir = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase1_preprocess_decoding/results/visualization/full_dataset_C010_with_residuals')
    output_dir = Path('./results/brain_surface_visualization')

    print("="*80)
    print("ACTUALLY VISIBLE VISUAL CORTEX VISUALIZATION")
    print("="*80)
    print(f"Subject: {args.subject}")
    print(f"ROI: {args.roi}")
    print(f"Method: {args.method}")
    print("="*80)

    # Load
    mapper = load_bilateral_mask(args.roi, atlas_dir)

    subj_dir = base_dir / args.subject / args.roi
    raw_patterns = np.load(subj_dir / 'amplitudes_raw.npy')
    proc_patterns = np.load(subj_dir / 'amplitudes_procrustes.npy')

    raw_avg = np.mean(raw_patterns, axis=0)
    proc_avg = np.mean(proc_patterns, axis=0)

    # Load HC
    hc_dir = base_dir / 'sub-01' / args.roi
    hc_proc = np.load(hc_dir / 'amplitudes_procrustes.npy')
    hc_avg = np.mean(hc_proc, axis=0)

    # Match
    n_voxels = min(raw_avg.shape[1], proc_avg.shape[1], hc_avg.shape[1])

    # Correspondence
    corr_raw = np.zeros(n_voxels)
    corr_proc = np.zeros(n_voxels)

    for v in range(n_voxels):
        if np.std(hc_avg[:, v]) > 1e-8 and np.std(raw_avg[:, v]) > 1e-8:
            corr_raw[v], _ = pearsonr(hc_avg[:, v], raw_avg[:, v])
        if np.std(hc_avg[:, v]) > 1e-8 and np.std(proc_avg[:, v]) > 1e-8:
            corr_proc[v], _ = pearsonr(hc_avg[:, v], proc_avg[:, v])

    improvement = corr_proc - corr_raw

    print(f"\nData loaded:")
    print(f"  N voxels: {n_voxels}")
    print(f"  Raw mean: {np.mean(corr_raw):.3f}")
    print(f"  Proc mean: {np.mean(corr_proc):.3f}")
    print(f"  Improvement: {np.mean(improvement):.3f}")

    # Generate visible version
    output_path = plot_visual_cortex_visible(
        mapper, corr_raw, corr_proc, improvement,
        args.subject, args.roi, output_dir, method=args.method
    )

    # Also generate ROI average version
    roi_avg_path = plot_roi_average_fill(
        mapper, np.mean(corr_raw), np.mean(corr_proc), np.mean(improvement),
        args.subject, args.roi, output_dir
    )

    print("\n" + "="*80)
    print("✅ COMPLETE")
    print("="*80)
    print(f"\nGenerated:")
    print(f"  1. {output_path.name} (smoothed/dilated - shows spatial pattern)")
    print(f"  2. {roi_avg_path.name} (ROI average - shows location)")
    print("\nView:")
    print(f"  open {output_path}")
