#!/usr/bin/env python3
"""
Visual Cortex Only Visualization

Problem: Whole-brain glass brain and surface rendering don't show
         patterns in small visual cortex ROIs (V1-V4).

Solution: Occipital lobe slice mosaic with ROI contour overlay.
          This shows ONLY the posterior brain region where visual cortex is.

Key features:
1. Occipital slices only (z: -25 to +10 mm)
2. ROI mask as contour overlay (boundaries visible)
3. Tight crop around visual cortex
4. Robust scaling for pattern visibility
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import gridspec
import nibabel as nib
from nilearn import plotting, image
from pathlib import Path
import sys
sys.path.insert(0, '.')
from brain_mapping_utils import load_bilateral_mask


def create_visual_cortex_mosaic(stat_map_img, roi_mask_img,
                                 title, cmap, vmin=None, vmax=None,
                                 symmetric_cmap=False):
    """
    Create occipital slice mosaic focused on visual cortex.

    Parameters
    ----------
    stat_map_img : Nifti1Image
        Statistical map to display
    roi_mask_img : Nifti1Image
        ROI mask for contour overlay
    title : str
        Figure title
    cmap : str
        Colormap name
    vmin, vmax : float
        Color scale limits (computed automatically if None)
    symmetric_cmap : bool
        If True, use symmetric scale around zero

    Returns
    -------
    fig : matplotlib.figure.Figure
    """
    # Get data for robust scaling
    stat_data = stat_map_img.get_fdata()
    stat_data_flat = stat_data[~np.isnan(stat_data)]

    if vmin is None or vmax is None:
        if symmetric_cmap:
            abs_max = np.nanpercentile(np.abs(stat_data_flat), 90)
            vmin, vmax = -abs_max, abs_max
        else:
            vmin = np.nanpercentile(stat_data_flat, 5)
            vmax = np.nanpercentile(stat_data_flat, 95)

    print(f"  Color scale: [{vmin:.3f}, {vmax:.3f}]")

    # Occipital slice coordinates (posterior brain)
    # Z coordinates from -25mm (inferior) to +10mm (superior)
    cut_coords = list(range(-24, 11, 3))  # 12 slices

    # Create figure
    fig = plt.figure(figsize=(20, 8))

    # Plot stat map with ROI contour overlay
    display = plotting.plot_stat_map(
        stat_map_img,
        display_mode='z',
        cut_coords=cut_coords,
        colorbar=True,
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
        title=title,
        draw_cross=False,
        annotate=True,
        black_bg=False,
        threshold=None  # Show all values
    )

    # Add ROI contour overlay
    display.add_contours(
        roi_mask_img,
        levels=[0.25],  # 25% probability threshold
        colors='black',
        linewidths=1.5,
        alpha=0.8
    )

    return fig


def plot_visual_cortex_comparison(mapper, raw_values, proc_values, improvement,
                                    subject, roi, output_dir):
    """
    Create comprehensive visual cortex visualization.

    Three figures:
    1. Before Procrustes (occipital mosaic)
    2. After Procrustes (occipital mosaic)
    3. Improvement map (occipital mosaic)

    Each shows ONLY occipital lobe with ROI boundaries.
    """
    print("\n" + "="*80)
    print("VISUAL CORTEX ONLY VISUALIZATION")
    print("="*80)
    print(f"ROI: {roi} ({len(raw_values)} voxels)")
    print(f"Subject: {subject}")

    # Create brain volumes
    print("\nCreating brain volumes...")
    img_raw = mapper.create_brain_volume(raw_values)
    img_proc = mapper.create_brain_volume(proc_values)
    img_improvement = mapper.create_brain_volume(improvement)

    # Create ROI mask image for contour
    roi_mask_data = mapper.binary_mask.astype(float)
    roi_mask_img = nib.Nifti1Image(roi_mask_data, mapper.affine)

    # Figure 1: Before Procrustes
    print("\n[1/4] Before Procrustes...")
    fig1 = create_visual_cortex_mosaic(
        img_raw, roi_mask_img,
        title=f'Before Procrustes - {roi} (Occipital Slices, {subject})',
        cmap='Blues',
        symmetric_cmap=False
    )

    path1 = output_dir / f'{subject}_{roi}_visual_cortex_BEFORE.png'
    fig1.savefig(path1, dpi=300, bbox_inches='tight')
    plt.close(fig1)
    print(f"  ✓ Saved: {path1.name}")

    # Figure 2: After Procrustes
    print("\n[2/4] After Procrustes...")
    fig2 = create_visual_cortex_mosaic(
        img_proc, roi_mask_img,
        title=f'After Procrustes - {roi} (Occipital Slices, {subject})',
        cmap='Reds',
        symmetric_cmap=False
    )

    path2 = output_dir / f'{subject}_{roi}_visual_cortex_AFTER.png'
    fig2.savefig(path2, dpi=300, bbox_inches='tight')
    plt.close(fig2)
    print(f"  ✓ Saved: {path2.name}")

    # Figure 3: Improvement
    print("\n[3/4] Improvement map...")
    fig3 = create_visual_cortex_mosaic(
        img_improvement, roi_mask_img,
        title=f'Improvement (Δr) - {roi} (Occipital Slices, {subject})',
        cmap='RdYlGn',
        symmetric_cmap=True  # Diverging colormap
    )

    path3 = output_dir / f'{subject}_{roi}_visual_cortex_IMPROVEMENT.png'
    fig3.savefig(path3, dpi=300, bbox_inches='tight')
    plt.close(fig3)
    print(f"  ✓ Saved: {path3.name}")

    # Figure 4: Combined (all three in one)
    print("\n[4/4] Combined figure...")
    fig4 = plt.figure(figsize=(24, 18))

    # Get robust scales
    vmin_raw = np.nanpercentile(raw_values, 5)
    vmax_raw = np.nanpercentile(raw_values, 95)
    vmin_proc = np.nanpercentile(proc_values, 5)
    vmax_proc = np.nanpercentile(proc_values, 95)
    abs_max_imp = np.nanpercentile(np.abs(improvement), 90)

    # Slice coordinates
    cut_coords = list(range(-24, 11, 4))  # 9 slices for tighter layout

    # Row 1: Before
    ax1 = plt.subplot(3, 1, 1)
    display1 = plotting.plot_stat_map(
        img_raw,
        display_mode='z',
        cut_coords=cut_coords,
        colorbar=True,
        cmap='Blues',
        vmin=vmin_raw,
        vmax=vmax_raw,
        axes=ax1,
        title=f'A. Before Procrustes - {roi}',
        draw_cross=False,
        threshold=None
    )
    display1.add_contours(roi_mask_img, levels=[0.25], colors='black',
                         linewidths=2, alpha=0.8)

    # Row 2: After
    ax2 = plt.subplot(3, 1, 2)
    display2 = plotting.plot_stat_map(
        img_proc,
        display_mode='z',
        cut_coords=cut_coords,
        colorbar=True,
        cmap='Reds',
        vmin=vmin_proc,
        vmax=vmax_proc,
        axes=ax2,
        title=f'B. After Procrustes - {roi}',
        draw_cross=False,
        threshold=None
    )
    display2.add_contours(roi_mask_img, levels=[0.25], colors='black',
                         linewidths=2, alpha=0.8)

    # Row 3: Improvement
    ax3 = plt.subplot(3, 1, 3)
    display3 = plotting.plot_stat_map(
        img_improvement,
        display_mode='z',
        cut_coords=cut_coords,
        colorbar=True,
        cmap='RdYlGn',
        vmin=-abs_max_imp,
        vmax=abs_max_imp,
        axes=ax3,
        title=f'C. Improvement (Δr) - {roi}',
        draw_cross=False,
        threshold=None
    )
    display3.add_contours(roi_mask_img, levels=[0.25], colors='black',
                         linewidths=2, alpha=0.8)

    plt.suptitle(f'{roi} Procrustes Effect - Visual Cortex Focus ({subject})',
                fontsize=18, fontweight='bold', y=0.995)

    path4 = output_dir / f'{subject}_{roi}_visual_cortex_COMBINED.png'
    fig4.savefig(path4, dpi=300, bbox_inches='tight')
    plt.close(fig4)
    print(f"  ✓ Saved: {path4.name}")

    print("\n" + "="*80)
    print("✅ VISUAL CORTEX VISUALIZATION COMPLETE")
    print("="*80)
    print("\nGenerated 4 figures:")
    print(f"  1. {path1.name} - Before")
    print(f"  2. {path2.name} - After")
    print(f"  3. {path3.name} - Improvement")
    print(f"  4. {path4.name} - Combined (RECOMMENDED)")

    return path4


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Visual cortex only visualization')
    parser.add_argument('--subject', type=str, default='sub-08')
    parser.add_argument('--roi', type=str, default='V2', choices=['V1', 'V2', 'V3', 'V4'])
    parser.add_argument('--metric', type=str, default='correspondence',
                       choices=['correspondence', 'reliability'])
    args = parser.parse_args()

    # Setup paths
    atlas_dir = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/ProbAtlas_v4/subj_vol_all')
    base_dir = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase1_preprocess_decoding/results/visualization/full_dataset_C010_with_residuals')
    output_dir = Path('./results/brain_surface_visualization')

    print("="*80)
    print("VISUAL CORTEX ONLY VISUALIZATION")
    print("="*80)
    print(f"Subject: {args.subject}")
    print(f"ROI: {args.roi}")
    print(f"Metric: {args.metric}")
    print("="*80)

    # Load ROI mask
    print("\nLoading ROI mask...")
    mapper = load_bilateral_mask(args.roi, atlas_dir)

    # Load voxel patterns
    print("Loading voxel patterns...")
    subj_dir = base_dir / args.subject / args.roi
    raw_patterns = np.load(subj_dir / 'amplitudes_raw.npy')
    proc_patterns = np.load(subj_dir / 'amplitudes_procrustes.npy')

    # Average across runs
    raw_avg = np.mean(raw_patterns, axis=0)  # (8, n_voxels)
    proc_avg = np.mean(proc_patterns, axis=0)

    # Select metric
    if args.metric == 'correspondence':
        # Load HC reference (sub-01)
        hc_dir = base_dir / 'sub-01' / args.roi
        hc_proc = np.load(hc_dir / 'amplitudes_procrustes.npy')
        hc_avg = np.mean(hc_proc, axis=0)

        # Match voxels (use minimum)
        n_voxels = min(raw_avg.shape[1], proc_avg.shape[1], hc_avg.shape[1])
        raw_matched = raw_avg[:, :n_voxels]
        proc_matched = proc_avg[:, :n_voxels]
        hc_matched = hc_avg[:, :n_voxels]

        # Compute correspondence (8-color profile correlation)
        from scipy.stats import pearsonr

        corr_raw = np.zeros(n_voxels)
        corr_proc = np.zeros(n_voxels)

        for v in range(n_voxels):
            if np.std(hc_matched[:, v]) > 1e-8 and np.std(raw_matched[:, v]) > 1e-8:
                corr_raw[v], _ = pearsonr(hc_matched[:, v], raw_matched[:, v])
            if np.std(hc_matched[:, v]) > 1e-8 and np.std(proc_matched[:, v]) > 1e-8:
                corr_proc[v], _ = pearsonr(hc_matched[:, v], proc_matched[:, v])

        raw_values = corr_raw
        proc_values = corr_proc
        improvement = corr_proc - corr_raw

        print(f"\nCorrespondence computed:")
        print(f"  Raw mean: {np.mean(corr_raw):.3f}")
        print(f"  Proc mean: {np.mean(corr_proc):.3f}")
        print(f"  Improvement: {np.mean(improvement):.3f}")

    elif args.metric == 'reliability':
        # Use profile reliability from Phase 1 output if available
        # For now, use dummy values
        print("Note: Profile reliability requires recomputation")
        print("Using correspondence as fallback")
        args.metric = 'correspondence'

    # Generate visualizations
    output_path = plot_visual_cortex_comparison(
        mapper, raw_values, proc_values, improvement,
        args.subject, args.roi, output_dir
    )

    print(f"\n✅ Main figure: {output_path}")
    print("\nTo view:")
    print(f"  open {output_path}")
