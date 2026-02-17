#!/usr/bin/env python3
"""
Improved Brain Visualization for Visual Cortex ROIs

Addresses the problem that glass brain doesn't show patterns well for
thin cortical ROIs (V1-V4) distributed on occipital surface.

Solutions implemented:
1. Inflated surface rendering (main) - patterns visible on unfolded cortex
2. ROI zoom-in slices - magnified view of occipital region
3. Robust scaling - percentile-based color limits
4. Multi-panel layout - context + detail

Usage:
    python plot_improved_brain_viz.py --subject sub-08 --roi V2
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import gridspec
import nibabel as nib
from nilearn import plotting, datasets, surface
from pathlib import Path
import argparse


def robust_scale(values, lower_percentile=2, upper_percentile=98):
    """
    Compute robust scaling limits using percentiles.

    Prevents outliers from dominating colormap.
    """
    vmin = np.nanpercentile(values, lower_percentile)
    vmax = np.nanpercentile(values, upper_percentile)
    return vmin, vmax


def symmetric_scale(values, percentile=95):
    """
    Compute symmetric scale around zero for diverging colormaps.

    For improvement/difference maps where 0 is meaningful center.
    """
    abs_max = np.nanpercentile(np.abs(values), percentile)
    return -abs_max, abs_max


def plot_inflated_surface_comparison(mapper, raw_values, proc_values, improvement,
                                      subject, roi, output_path):
    """
    Main visualization: Inflated cortical surface showing before/after/improvement.

    This is the PRIMARY figure for visual cortex ROIs.
    Inflated surface shows patterns that glass brain cannot reveal.

    Layout: 3 columns (raw/proc/improvement) × 4 rows (LH lateral/medial, RH lateral/medial)
    """
    from nilearn import datasets, surface, plotting as niplot

    print(f"\n{'='*80}")
    print(f"Generating INFLATED SURFACE visualization (main figure)")
    print(f"{'='*80}")

    # Fetch fsaverage surface
    print("  Fetching fsaverage5 surface mesh...")
    fsaverage = datasets.fetch_surf_fsaverage('fsaverage5')

    # Create brain volumes
    print("  Creating brain volumes...")
    img_raw = mapper.create_brain_volume(raw_values)
    img_proc = mapper.create_brain_volume(proc_values)
    img_improvement = mapper.create_brain_volume(improvement)

    # Project to surface
    print("  Projecting to inflated surface...")
    texture_lh_raw = surface.vol_to_surf(img_raw, fsaverage.pial_left)
    texture_rh_raw = surface.vol_to_surf(img_raw, fsaverage.pial_right)

    texture_lh_proc = surface.vol_to_surf(img_proc, fsaverage.pial_left)
    texture_rh_proc = surface.vol_to_surf(img_proc, fsaverage.pial_right)

    texture_lh_improvement = surface.vol_to_surf(img_improvement, fsaverage.pial_left)
    texture_rh_improvement = surface.vol_to_surf(img_improvement, fsaverage.pial_right)

    # Robust scaling
    print("  Computing robust color scales...")
    vmin_raw, vmax_raw = robust_scale(raw_values, 5, 95)
    vmin_proc, vmax_proc = robust_scale(proc_values, 5, 95)
    vmin_imp, vmax_imp = symmetric_scale(improvement, 90)

    print(f"    Raw scale: [{vmin_raw:.3f}, {vmax_raw:.3f}]")
    print(f"    Proc scale: [{vmin_proc:.3f}, {vmax_proc:.3f}]")
    print(f"    Improvement scale: [{vmin_imp:.3f}, {vmax_imp:.3f}]")

    # Create figure
    fig = plt.figure(figsize=(24, 16))

    # Title
    fig.suptitle(f'{roi} Procrustes Improvement - Inflated Cortical Surface ({subject})',
                fontsize=20, fontweight='bold', y=0.98)

    views = [
        ('lateral', 'Lateral'),
        ('medial', 'Medial')
    ]

    row_idx = 0

    # Left hemisphere
    for view_name, view_label in views:
        # Column 1: Raw
        ax = plt.subplot(4, 3, row_idx*3 + 1, projection='3d')
        niplot.plot_surf_stat_map(
            fsaverage.infl_left, texture_lh_raw,
            hemi='left', view=view_name,
            cmap='Blues', vmin=vmin_raw, vmax=vmax_raw,
            colorbar=(row_idx == 0),
            axes=ax,
            title=f'Before (LH {view_label})' if row_idx == 0 else f'LH {view_label}',
            threshold=None,  # Show all values
            bg_map=fsaverage.sulc_left  # Show sulci for anatomy
        )

        # Column 2: Procrustes
        ax = plt.subplot(4, 3, row_idx*3 + 2, projection='3d')
        niplot.plot_surf_stat_map(
            fsaverage.infl_left, texture_lh_proc,
            hemi='left', view=view_name,
            cmap='Reds', vmin=vmin_proc, vmax=vmax_proc,
            colorbar=(row_idx == 0),
            axes=ax,
            title=f'After (LH {view_label})' if row_idx == 0 else f'LH {view_label}',
            threshold=None,
            bg_map=fsaverage.sulc_left
        )

        # Column 3: Improvement
        ax = plt.subplot(4, 3, row_idx*3 + 3, projection='3d')
        niplot.plot_surf_stat_map(
            fsaverage.infl_left, texture_lh_improvement,
            hemi='left', view=view_name,
            cmap='RdYlGn', vmin=vmin_imp, vmax=vmax_imp,
            colorbar=(row_idx == 0),
            axes=ax,
            title=f'Improvement (LH {view_label})' if row_idx == 0 else f'LH {view_label}',
            threshold=None,
            bg_map=fsaverage.sulc_left
        )

        row_idx += 1

    # Right hemisphere
    for view_name, view_label in views:
        # Column 1: Raw
        ax = plt.subplot(4, 3, row_idx*3 + 1, projection='3d')
        niplot.plot_surf_stat_map(
            fsaverage.infl_right, texture_rh_raw,
            hemi='right', view=view_name,
            cmap='Blues', vmin=vmin_raw, vmax=vmax_raw,
            colorbar=False,
            axes=ax,
            title=f'RH {view_label}',
            threshold=None,
            bg_map=fsaverage.sulc_right
        )

        # Column 2: Procrustes
        ax = plt.subplot(4, 3, row_idx*3 + 2, projection='3d')
        niplot.plot_surf_stat_map(
            fsaverage.infl_right, texture_rh_proc,
            hemi='right', view=view_name,
            cmap='Reds', vmin=vmin_proc, vmax=vmax_proc,
            colorbar=False,
            axes=ax,
            title=f'RH {view_label}',
            threshold=None,
            bg_map=fsaverage.sulc_right
        )

        # Column 3: Improvement
        ax = plt.subplot(4, 3, row_idx*3 + 3, projection='3d')
        niplot.plot_surf_stat_map(
            fsaverage.infl_right, texture_rh_improvement,
            hemi='right', view=view_name,
            cmap='RdYlGn', vmin=vmin_imp, vmax=vmax_imp,
            colorbar=(row_idx == 3),  # Colorbar on last panel
            axes=ax,
            title=f'RH {view_label}',
            threshold=None,
            bg_map=fsaverage.sulc_right
        )

        row_idx += 1

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"✓ Saved inflated surface visualization: {output_path}")
    print(f"  File size: {output_path.stat().st_size / 1024 / 1024:.1f} MB")


def plot_roi_zoom_slices(mapper, raw_values, proc_values, improvement,
                          subject, roi, output_path):
    """
    ROI zoom-in: Occipital slices showing spatial patterns within ROI.

    Shows mosaic of slices centered on ROI, magnified to reveal patterns.
    """
    print(f"\nGenerating ROI ZOOM-IN slices...")

    # Create brain volumes
    img_raw = mapper.create_brain_volume(raw_values)
    img_proc = mapper.create_brain_volume(proc_values)
    img_improvement = mapper.create_brain_volume(improvement)

    # Robust scaling
    vmin_raw, vmax_raw = robust_scale(raw_values, 5, 95)
    vmin_proc, vmax_proc = robust_scale(proc_values, 5, 95)
    vmin_imp, vmax_imp = symmetric_scale(improvement, 90)

    # Figure with 3 rows
    fig, axes = plt.subplots(3, 1, figsize=(20, 18))

    # Row 1: Before
    display = plotting.plot_stat_map(
        img_raw,
        display_mode='z',
        cut_coords=8,  # 8 slices
        colorbar=True,
        cmap='Blues',
        vmin=vmin_raw, vmax=vmax_raw,
        axes=axes[0],
        title=f'A. Before Procrustes - {roi} ({subject})'
    )

    # Row 2: After
    display = plotting.plot_stat_map(
        img_proc,
        display_mode='z',
        cut_coords=8,
        colorbar=True,
        cmap='Reds',
        vmin=vmin_proc, vmax=vmax_proc,
        axes=axes[1],
        title=f'B. After Procrustes - {roi}'
    )

    # Row 3: Improvement
    display = plotting.plot_stat_map(
        img_improvement,
        display_mode='z',
        cut_coords=8,
        colorbar=True,
        cmap='RdYlGn',
        vmin=vmin_imp, vmax=vmax_imp,
        axes=axes[2],
        title=f'C. Improvement (Δr) - {roi}'
    )

    plt.suptitle(f'{roi} Occipital Slices - Axial View', fontsize=18, fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"✓ Saved ROI zoom slices: {output_path}")


def plot_combined_overview(mapper, raw_values, proc_values, improvement,
                            subject, roi, output_path):
    """
    Combined figure: Context (whole brain) + Detail (ROI zoom) + Stats.

    This is the RECOMMENDED main figure for papers.
    """
    print(f"\nGenerating COMBINED overview figure...")

    fig = plt.figure(figsize=(24, 14))
    gs = gridspec.GridSpec(2, 3, hspace=0.3, wspace=0.2, height_ratios=[1, 1])

    # Create brain volumes
    img_raw = mapper.create_brain_volume(raw_values)
    img_proc = mapper.create_brain_volume(proc_values)
    img_improvement = mapper.create_brain_volume(improvement)

    # Robust scaling
    vmin_raw, vmax_raw = robust_scale(raw_values, 5, 95)
    vmin_proc, vmax_proc = robust_scale(proc_values, 5, 95)
    vmin_imp, vmax_imp = symmetric_scale(improvement, 90)

    # Row 1: Glass brain (context)
    ax1 = plt.subplot(gs[0, 0])
    ax1.axis('off')
    plotting.plot_glass_brain(
        img_raw,
        display_mode='lyrz',
        colorbar=False,
        cmap='Blues',
        vmin=vmin_raw, vmax=vmax_raw,
        axes=ax1,
        title=f'Before - Whole Brain Context'
    )

    ax2 = plt.subplot(gs[0, 1])
    ax2.axis('off')
    plotting.plot_glass_brain(
        img_proc,
        display_mode='lyrz',
        colorbar=False,
        cmap='Reds',
        vmin=vmin_proc, vmax=vmax_proc,
        axes=ax2,
        title=f'After - Whole Brain'
    )

    ax3 = plt.subplot(gs[0, 2])
    ax3.axis('off')
    plotting.plot_glass_brain(
        img_improvement,
        display_mode='lyrz',
        colorbar=False,
        cmap='RdYlGn',
        vmin=vmin_imp, vmax=vmax_imp,
        axes=ax3,
        title=f'Improvement - Whole Brain'
    )

    # Row 2: Zoomed slices (detail)
    ax4 = plt.subplot(gs[1, 0])
    plotting.plot_stat_map(
        img_raw,
        display_mode='z',
        cut_coords=[-10, -5, 0],  # Occipital region
        colorbar=True,
        cmap='Blues',
        vmin=vmin_raw, vmax=vmax_raw,
        axes=ax4,
        title=f'{roi} Zoom: Before'
    )

    ax5 = plt.subplot(gs[1, 1])
    plotting.plot_stat_map(
        img_proc,
        display_mode='z',
        cut_coords=[-10, -5, 0],
        colorbar=True,
        cmap='Reds',
        vmin=vmin_proc, vmax=vmax_proc,
        axes=ax5,
        title=f'{roi} Zoom: After'
    )

    ax6 = plt.subplot(gs[1, 2])
    plotting.plot_stat_map(
        img_improvement,
        display_mode='z',
        cut_coords=[-10, -5, 0],
        colorbar=True,
        cmap='RdYlGn',
        vmin=vmin_imp, vmax=vmax_imp,
        axes=ax6,
        title=f'{roi} Zoom: Improvement'
    )

    plt.suptitle(f'{roi} Procrustes Improvement - Context + Detail ({subject})',
                fontsize=18, fontweight='bold', y=0.98)

    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"✓ Saved combined overview: {output_path}")


def main():
    """Generate improved brain visualizations."""

    parser = argparse.ArgumentParser(description='Improved brain visualization for visual cortex')
    parser.add_argument('--subject', type=str, default='sub-08')
    parser.add_argument('--roi', type=str, default='V2')
    parser.add_argument('--metric', type=str, default='correspondence',
                       choices=['correspondence', 'reliability'])
    parser.add_argument('--output-dir', type=str,
                       default='./results/brain_surface_visualization')

    args = parser.parse_args()

    # Import after argparse (faster startup)
    import sys
    sys.path.insert(0, '.')
    from brain_mapping_utils import load_bilateral_mask
    import json

    print("="*80)
    print("IMPROVED BRAIN VISUALIZATION FOR VISUAL CORTEX")
    print("="*80)
    print(f"Subject: {args.subject}")
    print(f"ROI: {args.roi}")
    print(f"Metric: {args.metric}")
    print("="*80)

    # Load data
    output_dir = Path(args.output_dir)
    metrics_path = output_dir / f'{args.subject}_{args.roi}_brain_metrics.json'

    if not metrics_path.exists():
        print(f"\n✗ Metrics file not found: {metrics_path}")
        print("  Run visualize_procrustes_brain_maps.py first")
        return

    # Load ROI mask
    atlas_dir = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/ProbAtlas_v4/subj_vol_all')
    mapper = load_bilateral_mask(args.roi, atlas_dir)

    # Load metric values (need to recompute from data)
    # For now, use existing data
    print("\nNote: This requires reloading voxel patterns")
    print("For full implementation, integrate with visualize_procrustes_brain_maps.py")

    # Generate demo with synthetic data
    print("\n" + "="*80)
    print("DEMO MODE: Using synthetic data")
    print("For real data, run via visualize_procrustes_brain_maps.py --improved-viz")
    print("="*80)

    n_voxels = mapper.n_voxels
    raw_values = np.random.randn(min(n_voxels, 400)) * 0.3
    proc_values = raw_values + np.random.randn(min(n_voxels, 400)) * 0.1 + 0.3
    improvement = proc_values - raw_values

    # Generate figures
    inflated_path = output_dir / f'{args.subject}_{args.roi}_inflated_surface_IMPROVED.png'
    plot_inflated_surface_comparison(mapper, raw_values, proc_values, improvement,
                                      args.subject, args.roi, inflated_path)

    zoom_path = output_dir / f'{args.subject}_{args.roi}_zoom_slices_IMPROVED.png'
    plot_roi_zoom_slices(mapper, raw_values, proc_values, improvement,
                          args.subject, args.roi, zoom_path)

    combined_path = output_dir / f'{args.subject}_{args.roi}_combined_overview_IMPROVED.png'
    plot_combined_overview(mapper, raw_values, proc_values, improvement,
                            args.subject, args.roi, combined_path)

    print("\n" + "="*80)
    print("✅ IMPROVED VISUALIZATIONS COMPLETE")
    print("="*80)
    print("\nGenerated:")
    print(f"  1. {inflated_path.name} (MAIN - inflated surface)")
    print(f"  2. {zoom_path.name} (ROI zoom slices)")
    print(f"  3. {combined_path.name} (Context + detail)")


if __name__ == '__main__':
    main()
