#!/usr/bin/env python3
"""
GLMsingle Visualization Utilities

Implements visualizations from example1.ipynb:
- Design matrix heatmaps
- GLMsingle output maps (betas, R2, HRF, FRACvalue)
- Reliability comparisons
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import warnings


def plot_design_matrices(
    design_list: List[np.ndarray],
    trial_labels_list: List[np.ndarray],
    output_dir: Path,
    runs_to_plot: List[int] = [0, 1],
    figsize: Tuple[int, int] = (20, 10)
):
    """
    Plot design matrices (similar to example1.ipynb cell 10).

    Args:
        design_list: List of (n_scans, n_conditions) design matrices
        trial_labels_list: List of trial labels per run
        output_dir: Directory to save figures
        runs_to_plot: Which runs to plot (default: first 2)
        figsize: Figure size
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    n_runs_to_plot = len(runs_to_plot)
    fig, axes = plt.subplots(1, n_runs_to_plot, figsize=figsize)

    if n_runs_to_plot == 1:
        axes = [axes]

    for i, run_idx in enumerate(runs_to_plot):
        design = design_list[run_idx]

        ax = axes[i]
        im = ax.imshow(design, interpolation='none', cmap='binary', aspect='auto')
        ax.set_title(f'Design Matrix - Run {run_idx + 1}', fontsize=16)
        ax.set_xlabel('Conditions (8 colors)', fontsize=14)
        ax.set_ylabel('Time (TRs)', fontsize=14)

        # Add colorbar
        plt.colorbar(im, ax=ax)

        # Print info
        n_scans, n_conditions = design.shape
        print(f"Run {run_idx + 1}:")
        print(f"  Design shape: {design.shape} (scans, conditions)")
        print(f"  Total trials: {len(trial_labels_list[run_idx])}")
        print(f"  Trials per condition: {[(trial_labels_list[run_idx] == i).sum() for i in range(1, n_conditions + 1)]}")

    plt.tight_layout()
    fig_path = output_dir / 'design_matrices.png'
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    print(f"\n✓ Saved: {fig_path}")
    plt.close()


def plot_glmsingle_outputs(
    results: Dict,
    output_dir: Path,
    slice_idx: Optional[int] = None,
    roi_mask: Optional[np.ndarray] = None,
    figsize: Tuple[int, int] = (16, 12)
):
    """
    Plot GLMsingle outputs: betas, R2, HRF index, FRACvalue
    (similar to example1.ipynb cell 19).

    Args:
        results: GLMsingle results dict with 'typed' field
        output_dir: Directory to save figures
        slice_idx: Which slice to plot (for 3D data, default: middle)
        roi_mask: Optional ROI mask for overlay
        figsize: Figure size
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get typed results (full GLMsingle optimization)
    typed_results = results.get('typed', results)

    # Fields to plot
    plot_fields = ['betasmd', 'R2', 'HRFindex', 'FRACvalue']
    titles = [
        'Average Betas (across colors)',
        'Model R²',
        'Optimal HRF Index',
        'Fracridge Regularization Level'
    ]
    colormaps = ['RdBu_r', 'hot', 'jet', 'copper']

    # Determine color limits
    clims = [
        None,  # Will compute for betas
        [0, 100],  # R2 percentage
        None,  # Will compute for HRF index
        [0, 1]  # Frac value
    ]

    fig, axes = plt.subplots(2, 2, figsize=figsize)
    axes = axes.flatten()

    for i, field in enumerate(plot_fields):
        if field not in typed_results:
            print(f"Warning: {field} not found in results, skipping")
            continue

        data = typed_results[field]

        # Handle different data shapes
        if field == 'betasmd':
            # Betas: (n_runs, n_colors, n_voxels) or (n_voxels, n_trials)
            # Average across conditions/trials
            if data.ndim == 3:
                # (n_runs, n_colors, n_voxels)
                plot_data = data.mean(axis=(0, 1))  # Average across runs and colors
            elif data.ndim == 2:
                # (n_voxels, n_trials)
                plot_data = data.mean(axis=1)  # Average across trials
            else:
                plot_data = data

            # Compute symmetric color limits
            vmax = np.percentile(np.abs(plot_data[~np.isnan(plot_data)]), 95)
            clims[i] = [-vmax, vmax]

        else:
            # R2, HRFindex, FRACvalue: (n_voxels,)
            plot_data = data

            if clims[i] is None:
                # Auto-compute limits
                vmin = np.percentile(plot_data[~np.isnan(plot_data)], 1)
                vmax = np.percentile(plot_data[~np.isnan(plot_data)], 99)
                clims[i] = [vmin, vmax]

        # Plot
        ax = axes[i]

        # For 1D voxel data, need to reshape to ROI if mask available
        if plot_data.ndim == 1 and roi_mask is not None:
            # Create 3D volume
            plot_volume = np.full(roi_mask.shape, np.nan)
            plot_volume[roi_mask] = plot_data

            # Select slice
            if slice_idx is None:
                slice_idx = roi_mask.shape[2] // 2

            plot_slice = plot_volume[:, :, slice_idx]
        else:
            plot_slice = plot_data

        im = ax.imshow(plot_slice, cmap=colormaps[i],
                      clim=clims[i], aspect='auto')
        ax.set_title(titles[i], fontsize=14)
        ax.axis('off')

        plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    plt.tight_layout()
    fig_path = output_dir / 'glmsingle_outputs.png'
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    print(f"✓ Saved: {fig_path}")
    plt.close()


def plot_reliability_comparison(
    reliabilities: Dict[str, float],
    reliability_maps: Optional[Dict[str, np.ndarray]] = None,
    roi_mask: Optional[np.ndarray] = None,
    output_dir: Path = None,
    figsize: Tuple[int, int] = (18, 6)
):
    """
    Plot reliability comparison across models
    (similar to example1.ipynb cell 34).

    Args:
        reliabilities: Dict of {model_name: median_reliability}
        reliability_maps: Optional dict of {model_name: voxel_reliability_map}
        roi_mask: Optional ROI mask
        output_dir: Directory to save figure
        figsize: Figure size
    """
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    # Prepare data
    model_names = list(reliabilities.keys())
    reliability_values = list(reliabilities.values())

    # Create figure
    if reliability_maps is not None and len(reliability_maps) > 0:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
    else:
        fig, ax1 = plt.subplots(1, 1, figsize=(10, 6))

    # Plot 1: Bar chart
    x_pos = np.arange(len(model_names))
    bars = ax1.bar(x_pos, reliability_values, width=0.6,
                   color=['lightgray', 'skyblue', 'steelblue', 'darkblue'][:len(model_names)])

    ax1.set_xlabel('Model', fontsize=14)
    ax1.set_ylabel('Median Split-Half Reliability (r)', fontsize=14)
    ax1.set_title('Model Reliability Comparison', fontsize=16)
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(model_names, rotation=15, ha='right')
    ax1.set_ylim([0, max(reliability_values) * 1.2])
    ax1.grid(axis='y', alpha=0.3)

    # Add value labels on bars
    for i, (bar, val) in enumerate(zip(bars, reliability_values)):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{val:.3f}',
                ha='center', va='bottom', fontsize=11)

    # Plot 2: Brain map showing improvement (if available)
    if reliability_maps is not None and len(reliability_maps) >= 2:
        # Compute improvement: best - baseline
        baseline_name = model_names[0]
        best_name = model_names[-1]

        improvement = reliability_maps[best_name] - reliability_maps[baseline_name]

        # Mask outside ROI
        if roi_mask is not None and improvement.ndim == 3:
            improvement_masked = improvement.copy()
            improvement_masked[~roi_mask] = np.nan

            # Select middle slice
            slice_idx = improvement.shape[2] // 2
            improvement_slice = improvement_masked[:, :, slice_idx]
        else:
            improvement_slice = improvement

        im = ax2.imshow(improvement_slice, cmap='RdBu_r',
                       clim=[-0.3, 0.3], aspect='auto')
        ax2.set_title(f'Reliability Improvement\n({best_name} - {baseline_name})',
                     fontsize=14)
        ax2.axis('off')
        plt.colorbar(im, ax=ax2, fraction=0.046, pad=0.04, label='Δr')

    plt.tight_layout()

    if output_dir:
        fig_path = output_dir / 'reliability_comparison.png'
        plt.savefig(fig_path, dpi=150, bbox_inches='tight')
        print(f"✓ Saved: {fig_path}")

    plt.close()


def plot_color_distribution(
    trial_labels_list: List[np.ndarray],
    output_dir: Path,
    n_colors: int = 8,
    figsize: Tuple[int, int] = (14, 8)
):
    """
    Plot distribution of trials across colors for each run.

    Args:
        trial_labels_list: List of trial labels (1-8) per run
        output_dir: Directory to save figure
        n_colors: Number of colors (default: 8)
        figsize: Figure size
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    n_runs = len(trial_labels_list)

    # Count trials per color per run
    counts = np.zeros((n_runs, n_colors))
    for run_idx, labels in enumerate(trial_labels_list):
        for color_id in range(1, n_colors + 1):
            counts[run_idx, color_id - 1] = (labels == color_id).sum()

    # Plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

    # Heatmap
    im = ax1.imshow(counts.T, cmap='YlOrRd', aspect='auto')
    ax1.set_xlabel('Run', fontsize=14)
    ax1.set_ylabel('Color', fontsize=14)
    ax1.set_title('Trial Distribution Heatmap', fontsize=16)
    ax1.set_xticks(range(n_runs))
    ax1.set_xticklabels([f'R{i+1}' for i in range(n_runs)])
    ax1.set_yticks(range(n_colors))
    ax1.set_yticklabels([f'C{i+1}' for i in range(n_colors)])
    plt.colorbar(im, ax=ax1, label='Trial count')

    # Add text annotations
    for i in range(n_runs):
        for j in range(n_colors):
            text = ax1.text(i, j, int(counts[i, j]),
                          ha="center", va="center", color="black", fontsize=9)

    # Grouped bar chart
    x = np.arange(n_colors)
    width = 0.8 / n_runs

    for run_idx in range(n_runs):
        offset = (run_idx - n_runs/2) * width + width/2
        ax2.bar(x + offset, counts[run_idx, :], width,
               label=f'Run {run_idx+1}', alpha=0.8)

    ax2.set_xlabel('Color', fontsize=14)
    ax2.set_ylabel('Trial Count', fontsize=14)
    ax2.set_title('Trials per Color per Run', fontsize=16)
    ax2.set_xticks(x)
    ax2.set_xticklabels([f'C{i+1}' for i in range(n_colors)])
    ax2.legend(ncol=2, fontsize=10)
    ax2.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    fig_path = output_dir / 'color_distribution.png'
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    print(f"✓ Saved: {fig_path}")
    plt.close()

    # Print summary
    print("\nColor distribution summary:")
    print(f"  Total trials per run: {counts.sum(axis=1).astype(int)}")
    print(f"  Trials per color (averaged): {counts.mean(axis=0).round(1)}")
    print(f"  Min/Max trials per color: {counts.min():.0f} / {counts.max():.0f}")


def create_diagnostic_report(
    results: Dict,
    design_list: List[np.ndarray],
    trial_labels_list: List[np.ndarray],
    output_dir: Path,
    roi_mask: Optional[np.ndarray] = None
):
    """
    Create comprehensive diagnostic report with all visualizations.

    Args:
        results: GLMsingle results
        design_list: Design matrices
        trial_labels_list: Trial labels
        output_dir: Output directory
        roi_mask: Optional ROI mask
    """
    output_dir = Path(output_dir)
    print(f"\nCreating diagnostic visualizations in: {output_dir}")
    print("=" * 80)

    # 1. Design matrices
    print("\n[1/4] Design matrices...")
    plot_design_matrices(design_list, trial_labels_list, output_dir)

    # 2. Color distribution
    print("\n[2/4] Color distribution...")
    plot_color_distribution(trial_labels_list, output_dir)

    # 3. GLMsingle outputs
    print("\n[3/4] GLMsingle outputs...")
    plot_glmsingle_outputs(results, output_dir, roi_mask=roi_mask)

    # 4. Summary text report
    print("\n[4/4] Summary report...")
    create_text_summary(results, design_list, output_dir)

    print("\n" + "=" * 80)
    print("✓ Diagnostic report complete!")
    print(f"  Output directory: {output_dir}")


def create_text_summary(
    results: Dict,
    design_list: List[np.ndarray],
    output_dir: Path
):
    """Create text summary of GLMsingle results."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_file = output_dir / 'summary.txt'

    with open(summary_file, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("GLMsingle Results Summary\n")
        f.write("=" * 80 + "\n\n")

        # Design info
        f.write("Design Information:\n")
        f.write(f"  Number of runs: {len(design_list)}\n")
        f.write(f"  Scans per run: {[d.shape[0] for d in design_list]}\n")
        f.write(f"  Conditions: {design_list[0].shape[1]}\n\n")

        # Results info
        typed_results = results.get('typed', results)

        if 'R2' in typed_results:
            r2 = typed_results['R2']
            f.write("Model Fit (R²):\n")
            f.write(f"  Mean: {r2.mean():.3f}\n")
            f.write(f"  Median: {np.median(r2):.3f}\n")
            f.write(f"  Range: [{r2.min():.3f}, {r2.max():.3f}]\n")
            f.write(f"  Voxels with R² > 0.5: {(r2 > 0.5).sum()} ({100*(r2 > 0.5).sum()/len(r2):.1f}%)\n\n")

        if 'HRFindex' in typed_results:
            hrf_idx = typed_results['HRFindex']
            f.write("HRF Selection:\n")
            f.write(f"  Mean HRF index: {hrf_idx.mean():.2f}\n")
            f.write(f"  Most common HRF: {np.bincount(hrf_idx.astype(int)).argmax()}\n\n")

        if 'FRACvalue' in typed_results:
            frac = typed_results['FRACvalue']
            f.write("Fracridge Regularization:\n")
            f.write(f"  Mean frac: {frac.mean():.3f}\n")
            f.write(f"  Median frac: {np.median(frac):.3f}\n")
            f.write(f"  Voxels with frac > 0.9: {(frac > 0.9).sum()} ({100*(frac > 0.9).sum()/len(frac):.1f}%)\n\n")

    print(f"✓ Saved: {summary_file}")
