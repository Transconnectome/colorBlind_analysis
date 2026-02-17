#!/usr/bin/env python3
"""
Brain Surface Plotting for Procrustes Visualization

Purpose: Create SPM-style 3D brain visualizations showing spatial distribution
         of Procrustes improvement on actual brain anatomy

Visualization types:
1. Glass brain plots - Quick overview (MVP)
2. Surface rendering - Publication-quality 3D (Enhancement)

Key figures:
- Correspondence map (main figure)
- Disparity reduction map
- Profile reliability map (NOT noise ceiling)

Usage:
    plot_correspondence_brain_map(
        mapper, corr_raw, corr_proc, improvement,
        subject, roi, output_path
    )
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.colors import Normalize, TwoSlopeNorm
import nibabel as nib
from nilearn import plotting, datasets, surface
from pathlib import Path


def plot_correspondence_brain_map(mapper, corr_raw, corr_proc, improvement,
                                   subject, roi, output_path):
    """
    Plot voxel-wise correspondence improvement on brain anatomy (glass brain).

    Four-panel figure:
    - Panel A: Before Procrustes (Blues colormap)
    - Panel B: After Procrustes (Reds colormap)
    - Panel C: Improvement map (RdYlGn diverging)
    - Panel D: Statistics text box

    Parameters
    ----------
    mapper : VoxelToBrainMapper
        Brain mapper with ROI mask
    corr_raw : np.ndarray
        Per-voxel correlation before Procrustes (n_voxels,)
    corr_proc : np.ndarray
        Per-voxel correlation after Procrustes (n_voxels,)
    improvement : np.ndarray
        Correlation improvement (n_voxels,)
    subject : str
        Subject ID
    roi : str
        ROI name
    output_path : str or Path
        Output file path
    """
    fig = plt.figure(figsize=(20, 14))

    # Create grid
    gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.2)

    # Panel A: Before Procrustes
    ax_a = plt.subplot(gs[0, 0])
    ax_a.axis('off')

    img_raw = mapper.create_brain_volume(corr_raw)
    display_a = plotting.plot_glass_brain(
        img_raw,
        display_mode='lyrz',
        colorbar=True,
        cmap='Blues',
        vmin=0, vmax=1,
        plot_abs=False,
        axes=ax_a,
        title=f'A. Before Procrustes\n{roi} HC-CVD Correspondence (r)'
    )

    # Panel B: After Procrustes
    ax_b = plt.subplot(gs[0, 1])
    ax_b.axis('off')

    img_proc = mapper.create_brain_volume(corr_proc)
    display_b = plotting.plot_glass_brain(
        img_proc,
        display_mode='lyrz',
        colorbar=True,
        cmap='Reds',
        vmin=0, vmax=1,
        plot_abs=False,
        axes=ax_b,
        title=f'B. After Procrustes\n{roi} HC-CVD Correspondence (r)'
    )

    # Panel C: Improvement map
    ax_c = plt.subplot(gs[1, 0])
    ax_c.axis('off')

    img_improvement = mapper.create_brain_volume(improvement)
    display_c = plotting.plot_glass_brain(
        img_improvement,
        display_mode='lyrz',
        colorbar=True,
        cmap='RdYlGn',
        vmin=-0.5, vmax=0.5,
        plot_abs=False,
        axes=ax_c,
        title=f'C. Improvement Map\nΔr = Procrustes - Raw'
    )

    # Panel D: Statistics
    ax_d = plt.subplot(gs[1, 1])
    ax_d.axis('off')

    # Compute statistics
    mean_improvement = np.mean(improvement)
    std_improvement = np.std(improvement)
    pct_improved = 100 * np.mean(improvement > 0)

    mean_raw = np.mean(corr_raw)
    mean_proc = np.mean(corr_proc)

    # Effect size (Cohen's d)
    cohens_d = mean_improvement / (std_improvement + 1e-8)

    # Statistics text
    stats_text = f"""
{roi} Voxel-Wise Correspondence Analysis
{subject}
{'='*50}

BEFORE PROCRUSTES:
  Mean correlation:  {mean_raw:.3f}
  Std:               {np.std(corr_raw):.3f}
  Range:             [{np.min(corr_raw):.3f}, {np.max(corr_raw):.3f}]

AFTER PROCRUSTES:
  Mean correlation:  {mean_proc:.3f}
  Std:               {np.std(corr_proc):.3f}
  Range:             [{np.min(corr_proc):.3f}, {np.max(corr_proc):.3f}]

IMPROVEMENT:
  Mean Δr:           {mean_improvement:+.3f} ± {std_improvement:.3f}
  % voxels improved: {pct_improved:.1f}%
  Effect size (d):   {cohens_d:.2f}

INTERPRETATION:
  {'Large effect' if abs(cohens_d) > 0.8 else 'Medium effect' if abs(cohens_d) > 0.5 else 'Small effect'}
  {'✓ Substantial improvement' if mean_improvement > 0.2 else '⚠ Modest improvement' if mean_improvement > 0.1 else '✗ Minimal improvement'}

NOTE: Correspondence = 8-color profile correlation per voxel
      HC reference: sub-01 (single subject)
"""

    ax_d.text(0.05, 0.95, stats_text,
             transform=ax_d.transAxes,
             fontsize=11,
             verticalalignment='top',
             family='monospace',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.9))

    # Main title
    fig.suptitle(f'Procrustes Correspondence Improvement: {roi} ({subject})',
                fontsize=18, fontweight='bold', y=0.98)

    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"\n✓ Saved correspondence brain map: {output_path}")


def plot_disparity_brain_map(mapper, disp_raw, disp_proc, reduction_pct,
                              subject, roi, output_path):
    """
    Plot voxel-wise disparity reduction on brain anatomy.

    Parameters
    ----------
    mapper : VoxelToBrainMapper
        Brain mapper
    disp_raw : np.ndarray
        Disparity before Procrustes (n_voxels,)
    disp_proc : np.ndarray
        Disparity after Procrustes (n_voxels,)
    reduction_pct : np.ndarray
        Percent reduction (n_voxels,)
    subject : str
        Subject ID
    roi : str
        ROI name
    output_path : str or Path
        Output file path
    """
    fig = plt.figure(figsize=(20, 14))
    gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.2)

    # Panel A: Raw disparity
    ax_a = plt.subplot(gs[0, 0])
    ax_a.axis('off')

    img_raw = mapper.create_brain_volume(disp_raw)
    plotting.plot_glass_brain(
        img_raw,
        display_mode='lyrz',
        colorbar=True,
        cmap='Purples',
        vmin=0, vmax=np.percentile(disp_raw, 95),
        plot_abs=False,
        axes=ax_a,
        title=f'A. Before Procrustes\n{roi} HC-CVD Disparity (L2)'
    )

    # Panel B: Procrustes disparity
    ax_b = plt.subplot(gs[0, 1])
    ax_b.axis('off')

    img_proc = mapper.create_brain_volume(disp_proc)
    plotting.plot_glass_brain(
        img_proc,
        display_mode='lyrz',
        colorbar=True,
        cmap='Purples',
        vmin=0, vmax=np.percentile(disp_raw, 95),  # Same scale as raw
        plot_abs=False,
        axes=ax_b,
        title=f'B. After Procrustes\n{roi} HC-CVD Disparity (L2)'
    )

    # Panel C: Reduction map
    ax_c = plt.subplot(gs[1, 0])
    ax_c.axis('off')

    img_reduction = mapper.create_brain_volume(reduction_pct)
    plotting.plot_glass_brain(
        img_reduction,
        display_mode='lyrz',
        colorbar=True,
        cmap='RdYlGn',
        vmin=-50, vmax=100,
        plot_abs=False,
        axes=ax_c,
        title=f'C. Disparity Reduction\n% Reduction = 100(Raw-Proc)/Raw'
    )

    # Panel D: Statistics
    ax_d = plt.subplot(gs[1, 1])
    ax_d.axis('off')

    stats_text = f"""
{roi} Voxel-Wise Disparity Analysis
{subject}
{'='*50}

BEFORE PROCRUSTES:
  Mean disparity:    {np.mean(disp_raw):.3f}
  Std:               {np.std(disp_raw):.3f}
  Range:             [{np.min(disp_raw):.3f}, {np.max(disp_raw):.3f}]

AFTER PROCRUSTES:
  Mean disparity:    {np.mean(disp_proc):.3f}
  Std:               {np.std(disp_proc):.3f}
  Range:             [{np.min(disp_proc):.3f}, {np.max(disp_proc):.3f}]

REDUCTION:
  Mean reduction:    {np.mean(reduction_pct):.1f}% ± {np.std(reduction_pct):.1f}%
  % voxels reduced:  {100 * np.mean(reduction_pct > 0):.1f}%
  Median reduction:  {np.median(reduction_pct):.1f}%

INTERPRETATION:
  {'✓ Strong reduction' if np.mean(reduction_pct) > 50 else '⚠ Moderate reduction' if np.mean(reduction_pct) > 30 else '✗ Weak reduction'}

NOTE: Disparity = L2 distance across 8-color profile
"""

    ax_d.text(0.05, 0.95, stats_text,
             transform=ax_d.transAxes,
             fontsize=11,
             verticalalignment='top',
             family='monospace',
             bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.9))

    fig.suptitle(f'Procrustes Disparity Reduction: {roi} ({subject})',
                fontsize=18, fontweight='bold', y=0.98)

    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"✓ Saved disparity brain map: {output_path}")


def plot_profile_reliability_brain_map(mapper, reliability_raw, reliability_proc,
                                        improvement, subject, roi, output_path):
    """
    Plot voxel-level profile reliability improvement on brain anatomy.

    IMPORTANT: This is NOT "noise ceiling" - it's run-to-run profile stability.

    Parameters
    ----------
    mapper : VoxelToBrainMapper
        Brain mapper
    reliability_raw : np.ndarray
        Profile reliability before Procrustes (n_voxels,)
    reliability_proc : np.ndarray
        Profile reliability after Procrustes (n_voxels,)
    improvement : np.ndarray
        Reliability improvement (n_voxels,)
    subject : str
        Subject ID
    roi : str
        ROI name
    output_path : str or Path
        Output file path
    """
    fig = plt.figure(figsize=(20, 14))
    gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.2)

    # Panel A: Raw reliability
    ax_a = plt.subplot(gs[0, 0])
    ax_a.axis('off')

    img_raw = mapper.create_brain_volume(reliability_raw)
    plotting.plot_glass_brain(
        img_raw,
        display_mode='lyrz',
        colorbar=True,
        cmap='Blues',
        vmin=-0.5, vmax=1.0,
        plot_abs=False,
        axes=ax_a,
        title=f'A. Before Procrustes\n{roi} Profile Reliability (r)'
    )

    # Panel B: Procrustes reliability
    ax_b = plt.subplot(gs[0, 1])
    ax_b.axis('off')

    img_proc = mapper.create_brain_volume(reliability_proc)
    plotting.plot_glass_brain(
        img_proc,
        display_mode='lyrz',
        colorbar=True,
        cmap='Reds',
        vmin=-0.5, vmax=1.0,
        plot_abs=False,
        axes=ax_b,
        title=f'B. After Procrustes\n{roi} Profile Reliability (r)'
    )

    # Panel C: Improvement map
    ax_c = plt.subplot(gs[1, 0])
    ax_c.axis('off')

    img_improvement = mapper.create_brain_volume(improvement)
    plotting.plot_glass_brain(
        img_improvement,
        display_mode='lyrz',
        colorbar=True,
        cmap='RdYlGn',
        vmin=-0.5, vmax=1.0,
        plot_abs=False,
        axes=ax_c,
        title=f'C. Reliability Improvement\nΔr = Procrustes - Raw'
    )

    # Panel D: Statistics
    ax_d = plt.subplot(gs[1, 1])
    ax_d.axis('off')

    stats_text = f"""
{roi} Voxel-Level Profile Reliability
{subject}
{'='*50}

IMPORTANT: This is NOT "noise ceiling"
- RDM noise ceiling = ROI-level geometry reliability
- Profile reliability = voxel-level run stability

BEFORE PROCRUSTES:
  Mean reliability:  {np.mean(reliability_raw):.3f}
  Std:               {np.std(reliability_raw):.3f}
  Range:             [{np.min(reliability_raw):.3f}, {np.max(reliability_raw):.3f}]

AFTER PROCRUSTES:
  Mean reliability:  {np.mean(reliability_proc):.3f}
  Std:               {np.std(reliability_proc):.3f}
  Range:             [{np.min(reliability_proc):.3f}, {np.max(reliability_proc):.3f}]

IMPROVEMENT:
  Mean Δr:           {np.mean(improvement):+.3f} ± {np.std(improvement):.3f}
  % voxels improved: {100 * np.mean(improvement > 0):.1f}%

INTERPRETATION:
  Profile reliability measures run-to-run
  stability of voxel's 8-color selectivity.

  Procrustes improves this by reducing
  geometric run variability.

NOTE: Reliability = split-half correlation of
      8-color profiles (averaged over 50 splits)
"""

    ax_d.text(0.05, 0.95, stats_text,
             transform=ax_d.transAxes,
             fontsize=10,
             verticalalignment='top',
             family='monospace',
             bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.9))

    fig.suptitle(f'Profile Reliability (Run-to-Run Stability): {roi} ({subject})',
                fontsize=18, fontweight='bold', y=0.98)

    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"✓ Saved profile reliability brain map: {output_path}")


def plot_surface_procrustes_improvement(mapper, improvement, subject, roi, output_path):
    """
    Project improvement values onto fsaverage inflated cortical surface.

    TRUE SPM-STYLE 3D SURFACE VISUALIZATION (Enhancement).

    Parameters
    ----------
    mapper : VoxelToBrainMapper
        Brain mapper
    improvement : np.ndarray
        Improvement values to project (n_voxels,)
    subject : str
        Subject ID
    roi : str
        ROI name
    output_path : str or Path
        Output file path
    """
    try:
        from nilearn import datasets, surface, plotting as niplot

        print(f"\nGenerating surface rendering...")
        print(f"  Fetching fsaverage surface mesh...")

        # Fetch fsaverage surface
        fsaverage = datasets.fetch_surf_fsaverage('fsaverage5')

        # Create brain volume
        improvement_img = mapper.create_brain_volume(improvement)

        # Project volume to surface
        print(f"  Projecting to surface...")
        texture_lh = surface.vol_to_surf(improvement_img, fsaverage.pial_left)
        texture_rh = surface.vol_to_surf(improvement_img, fsaverage.pial_right)

        # Create figure with multiple views
        fig = plt.figure(figsize=(24, 12))

        views = [
            ('lateral', 0),
            ('medial', 1),
            ('dorsal', 2),
            ('ventral', 3)
        ]

        for view_idx, (view_name, col) in enumerate(views):
            # Left hemisphere
            ax_lh = plt.subplot(2, 4, col + 1, projection='3d')
            niplot.plot_surf_stat_map(
                fsaverage.infl_left, texture_lh,
                hemi='left', view=view_name,
                cmap='RdYlGn', vmin=-0.5, vmax=0.5,
                colorbar=False,
                axes=ax_lh,
                title=f'Left {view_name.capitalize()}'
            )

            # Right hemisphere
            ax_rh = plt.subplot(2, 4, col + 5, projection='3d')
            niplot.plot_surf_stat_map(
                fsaverage.infl_right, texture_rh,
                hemi='right', view=view_name,
                cmap='RdYlGn', vmin=-0.5, vmax=0.5,
                colorbar=(col == 3),  # Only on last panel
                axes=ax_rh,
                title=f'Right {view_name.capitalize()}'
            )

        fig.suptitle(f'{roi} Procrustes Improvement - Surface Rendering ({subject})',
                    fontsize=18, fontweight='bold')

        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"✓ Saved surface rendering: {output_path}")

    except Exception as e:
        print(f"⚠ Surface rendering failed: {e}")
        print(f"  (This is optional enhancement - glass brain plots are primary)")


if __name__ == '__main__':
    """Test plotting functions with synthetic data."""

    print("Testing brain surface plotting...")
    print("="*80)

    # This would require actual brain mapper and data
    # For now, just verify imports work

    print("✓ All imports successful")
    print("✓ Functions defined:")
    print("  - plot_correspondence_brain_map")
    print("  - plot_disparity_brain_map")
    print("  - plot_profile_reliability_brain_map")
    print("  - plot_surface_procrustes_improvement")

    print("\nTo test with real data, use visualize_procrustes_brain_maps.py")
