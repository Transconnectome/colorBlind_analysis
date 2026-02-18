#!/usr/bin/env python3
"""
Visualize Color Representational Space Per Subject

This script visualizes the 8-color representational space for each subject
after SRM alignment, using Multidimensional Scaling (MDS) to project the
RDM into 2D space.

Usage:
    python visualize_color_space_per_subject.py --roi V1 --results-dir results/srm_between_subject/...
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.manifold import MDS
from scipy.spatial.distance import squareform

# Color names for labeling
COLOR_NAMES = [
    'Red',      # color_1
    'Orange',   # color_2
    'Yellow',   # color_3
    'Green',    # color_4
    'Cyan',     # color_5
    'Blue',     # color_6
    'Purple',   # color_7
    'Magenta'   # color_8
]

# Color hex codes for plotting
COLOR_HEX = {
    'Red': '#FF0000',
    'Orange': '#FF8000',
    'Yellow': '#FFFF00',
    'Green': '#00FF00',
    'Cyan': '#00FFFF',
    'Blue': '#0000FF',
    'Purple': '#8000FF',
    'Magenta': '#FF00FF'
}


def compute_rdm_from_amplitudes(amplitudes: np.ndarray) -> np.ndarray:
    """
    Compute RDM from amplitudes using correlation distance.

    Args:
        amplitudes: (n_runs, n_colors, n_features) or (n_colors, n_features)

    Returns:
        rdm: (n_colors, n_colors) dissimilarity matrix
    """
    # Average across runs if needed
    if amplitudes.ndim == 3:
        amplitudes = np.mean(amplitudes, axis=0)  # (n_colors, n_features)

    # Compute pairwise correlation
    n_colors = amplitudes.shape[0]
    rdm = np.zeros((n_colors, n_colors))

    for i in range(n_colors):
        for j in range(n_colors):
            # Correlation distance = 1 - correlation
            corr = np.corrcoef(amplitudes[i], amplitudes[j])[0, 1]
            rdm[i, j] = 1 - corr

    return rdm


def rdm_to_2d_mds(rdm: np.ndarray, random_state: int = 42) -> np.ndarray:
    """
    Convert RDM to 2D coordinates using MDS.

    Args:
        rdm: (n_colors, n_colors) dissimilarity matrix
        random_state: Random seed for reproducibility

    Returns:
        coords_2d: (n_colors, 2) 2D coordinates
    """
    # MDS expects condensed distance matrix (upper triangle)
    # But we can also use the full symmetric matrix
    mds = MDS(n_components=2, dissimilarity='precomputed', random_state=random_state)
    coords_2d = mds.fit_transform(rdm)
    return coords_2d


def plot_subject_color_space(
    coords_2d: np.ndarray,
    subject: str,
    roi: str,
    ax: plt.Axes,
    is_cvd: bool = False,
    xlim: Optional[tuple] = None,
    ylim: Optional[tuple] = None
) -> None:
    """
    Plot 2D color space for a single subject.

    Args:
        coords_2d: (n_colors, 2) 2D coordinates from MDS
        subject: Subject ID
        roi: ROI name
        ax: Matplotlib axis
        is_cvd: Whether subject has CVD
        xlim: X-axis limits (min, max) for consistent scaling
        ylim: Y-axis limits (min, max) for consistent scaling
    """
    # Plot points with color-coded markers
    for i, (x, y) in enumerate(coords_2d):
        color_name = COLOR_NAMES[i]
        color_hex = COLOR_HEX[color_name]

        ax.scatter(x, y, c=color_hex, s=200, edgecolor='black',
                   linewidth=2, alpha=0.8, zorder=3)

        # Add labels
        ax.text(x, y, str(i+1), ha='center', va='center',
                fontsize=9, fontweight='bold', color='white', zorder=4)

    # Add connecting lines to show structure
    for i in range(len(coords_2d)):
        for j in range(i+1, len(coords_2d)):
            x_vals = [coords_2d[i, 0], coords_2d[j, 0]]
            y_vals = [coords_2d[i, 1], coords_2d[j, 1]]
            ax.plot(x_vals, y_vals, 'k-', alpha=0.1, linewidth=0.5, zorder=1)

    # Formatting
    group = 'CVD' if is_cvd else 'HC'
    ax.set_title(f'{subject} ({group})', fontsize=11, fontweight='bold')
    ax.set_xlabel('MDS Dimension 1', fontsize=9)
    ax.set_ylabel('MDS Dimension 2', fontsize=9)
    ax.grid(alpha=0.3, linestyle=':', zorder=0)

    # Set consistent axis limits if provided
    if xlim is not None:
        ax.set_xlim(xlim)
    if ylim is not None:
        ax.set_ylim(ylim)

    ax.set_aspect('equal', adjustable='box')


def create_legend_panel(ax: plt.Axes) -> None:
    """Create a legend panel showing color names."""
    ax.axis('off')

    # Add title
    ax.text(0.5, 0.95, 'Color Legend', ha='center', va='top',
            fontsize=12, fontweight='bold', transform=ax.transAxes)

    # Add color legend
    y_start = 0.85
    y_step = 0.09

    for i, color_name in enumerate(COLOR_NAMES):
        y_pos = y_start - i * y_step
        color_hex = COLOR_HEX[color_name]

        # Draw colored circle
        circle = plt.Circle((0.2, y_pos), 0.03, color=color_hex,
                           transform=ax.transAxes, zorder=3)
        ax.add_patch(circle)

        # Add label
        ax.text(0.3, y_pos, f'{i+1}. {color_name}', va='center',
                fontsize=10, transform=ax.transAxes)


def visualize_all_subjects(
    results_file: Path,
    output_dir: Path,
    roi: str
) -> None:
    """
    Create grid visualization of color spaces for all subjects.

    Args:
        results_file: Path to between-subject results JSON
        output_dir: Output directory for plots
        roi: ROI name
    """
    print(f"\n{'='*70}")
    print(f"Visualizing Color Representational Space: {roi}")
    print(f"{'='*70}\n")

    # Load results
    with open(results_file, 'r') as f:
        results = json.load(f)

    hc_subjects = results['subjects']['hc']
    cvd_subjects = results['subjects']['cvd']
    all_subjects = hc_subjects + cvd_subjects

    print(f"HC subjects: {hc_subjects}")
    print(f"CVD subjects: {cvd_subjects}")

    # Load aligned amplitudes (need to load from .npy files)
    # For now, compute RDMs from the results
    # We need to load the actual aligned data

    # Try to find aligned data file
    aligned_file = results_file.parent / f"{roi}_aligned_amplitudes.npy"

    if not aligned_file.exists():
        print(f"\n⚠️  WARNING: Aligned amplitudes file not found: {aligned_file}")
        print("Cannot visualize color space without aligned amplitudes.")
        print("This file should be saved by evaluate_srm_between_subject.py")
        return

    # Load aligned amplitudes
    print(f"\nLoading aligned amplitudes from {aligned_file}...")
    aligned_data = np.load(aligned_file, allow_pickle=True).item()

    # Compute RDMs and 2D coordinates for each subject
    rdms = {}
    coords_2d = {}

    print("\nComputing MDS coordinates for each subject...")
    for subject in all_subjects:
        if subject not in aligned_data:
            print(f"  ⚠️  {subject} not found in aligned data, skipping")
            continue

        # Compute RDM
        rdms[subject] = compute_rdm_from_amplitudes(aligned_data[subject])

        # Convert to 2D with MDS
        coords_2d[subject] = rdm_to_2d_mds(rdms[subject])
        print(f"  ✓ {subject}")

    # Compute global axis limits for consistent scaling
    all_coords = np.vstack([coords_2d[s] for s in coords_2d.keys()])
    x_min, x_max = all_coords[:, 0].min(), all_coords[:, 0].max()
    y_min, y_max = all_coords[:, 1].min(), all_coords[:, 1].max()

    # Add 10% padding
    x_range = x_max - x_min
    y_range = y_max - y_min
    x_padding = x_range * 0.1
    y_padding = y_range * 0.1

    global_xlim = (x_min - x_padding, x_max + x_padding)
    global_ylim = (y_min - y_padding, y_max + y_padding)

    print(f"\nGlobal axis limits:")
    print(f"  X: [{global_xlim[0]:.2f}, {global_xlim[1]:.2f}]")
    print(f"  Y: [{global_ylim[0]:.2f}, {global_ylim[1]:.2f}]")

    # Create subplot grid
    n_subjects = len(coords_2d)
    n_cols = 4
    n_rows = (n_subjects + n_cols) // n_cols  # +1 for legend panel

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(16, 4*n_rows))
    axes = axes.flatten()

    # Plot each subject
    for idx, subject in enumerate(all_subjects):
        if subject not in coords_2d:
            axes[idx].axis('off')
            continue

        is_cvd = subject in cvd_subjects
        plot_subject_color_space(coords_2d[subject], subject, roi,
                                 axes[idx], is_cvd=is_cvd,
                                 xlim=global_xlim, ylim=global_ylim)

    # Add legend panel in the last subplot
    create_legend_panel(axes[-1])

    # Hide unused subplots
    for idx in range(len(coords_2d) + 1, len(axes)):
        axes[idx].axis('off')

    # Main title
    fig.suptitle(f'Color Representational Space per Subject: {roi}\n'
                f'SRM k={results["n_features"]}, MDS 2D Projection',
                fontsize=16, fontweight='bold', y=0.995)

    plt.tight_layout()

    # Save
    output_file = output_dir / f"{roi}_color_space_all_subjects.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\n✅ Saved color space visualization to {output_file}")
    plt.close()

    # Also create separate HC vs CVD comparison
    create_hc_cvd_comparison(coords_2d, hc_subjects, cvd_subjects, roi,
                            results['n_features'], output_dir)


def create_hc_cvd_comparison(
    coords_2d: Dict[str, np.ndarray],
    hc_subjects: List[str],
    cvd_subjects: List[str],
    roi: str,
    n_features: int,
    output_dir: Path
) -> None:
    """
    Create side-by-side comparison of average HC vs CVD color spaces.

    Args:
        coords_2d: Dictionary of 2D coordinates per subject
        hc_subjects: List of HC subject IDs
        cvd_subjects: List of CVD subject IDs
        roi: ROI name
        n_features: Number of SRM features
        output_dir: Output directory
    """
    print("\nCreating HC vs CVD average comparison...")

    # Average coordinates for HC and CVD
    hc_coords_list = [coords_2d[s] for s in hc_subjects if s in coords_2d]
    cvd_coords_list = [coords_2d[s] for s in cvd_subjects if s in coords_2d]

    if not hc_coords_list or not cvd_coords_list:
        print("  ⚠️  Not enough data for HC vs CVD comparison")
        return

    hc_avg = np.mean(hc_coords_list, axis=0)
    cvd_avg = np.mean(cvd_coords_list, axis=0)

    # Procrustes alignment of CVD to HC for better visualization
    from scipy.spatial import procrustes
    _, cvd_aligned, _ = procrustes(hc_avg, cvd_avg)

    # Compute global axis limits for consistent scaling across all 3 panels
    all_comparison_coords = np.vstack([hc_avg, cvd_aligned])
    x_min, x_max = all_comparison_coords[:, 0].min(), all_comparison_coords[:, 0].max()
    y_min, y_max = all_comparison_coords[:, 1].min(), all_comparison_coords[:, 1].max()

    # Add 15% padding for better visibility
    x_range = x_max - x_min
    y_range = y_max - y_min
    x_padding = x_range * 0.15
    y_padding = y_range * 0.15

    comparison_xlim = (x_min - x_padding, x_max + x_padding)
    comparison_ylim = (y_min - y_padding, y_max + y_padding)

    # Create figure
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 5))

    # Plot HC average
    plot_average_color_space(hc_avg, 'HC Average', roi, ax1, 'HC',
                             xlim=comparison_xlim, ylim=comparison_ylim)

    # Plot CVD average (aligned to HC)
    plot_average_color_space(cvd_aligned, 'CVD Average (aligned to HC)', roi, ax2, 'CVD',
                             xlim=comparison_xlim, ylim=comparison_ylim)

    # Plot overlay
    plot_overlay_comparison(hc_avg, cvd_aligned, roi, ax3,
                           xlim=comparison_xlim, ylim=comparison_ylim)

    fig.suptitle(f'HC vs CVD Color Space Comparison: {roi} (SRM k={n_features})',
                fontsize=16, fontweight='bold')

    plt.tight_layout()

    output_file = output_dir / f"{roi}_hc_vs_cvd_color_space_comparison.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✅ Saved HC vs CVD comparison to {output_file}")
    plt.close()


def plot_average_color_space(
    coords_2d: np.ndarray,
    title: str,
    roi: str,
    ax: plt.Axes,
    group: str,
    xlim: Optional[tuple] = None,
    ylim: Optional[tuple] = None
) -> None:
    """Plot average color space for a group."""
    for i, (x, y) in enumerate(coords_2d):
        color_name = COLOR_NAMES[i]
        color_hex = COLOR_HEX[color_name]

        ax.scatter(x, y, c=color_hex, s=300, edgecolor='black',
                  linewidth=2, alpha=0.9, zorder=3)
        ax.text(x, y, str(i+1), ha='center', va='center',
               fontsize=11, fontweight='bold', color='white', zorder=4)

    ax.set_title(title, fontsize=13, fontweight='bold')
    ax.set_xlabel('MDS Dimension 1', fontsize=11)
    ax.set_ylabel('MDS Dimension 2', fontsize=11)
    ax.grid(alpha=0.3, linestyle=':')

    # Set consistent axis limits if provided
    if xlim is not None:
        ax.set_xlim(xlim)
    if ylim is not None:
        ax.set_ylim(ylim)

    ax.set_aspect('equal', adjustable='box')


def plot_overlay_comparison(
    hc_coords: np.ndarray,
    cvd_coords: np.ndarray,
    roi: str,
    ax: plt.Axes,
    xlim: Optional[tuple] = None,
    ylim: Optional[tuple] = None
) -> None:
    """Plot overlay of HC vs CVD color spaces with displacement vectors."""
    for i in range(len(COLOR_NAMES)):
        color_hex = COLOR_HEX[COLOR_NAMES[i]]

        # HC points (circles)
        ax.scatter(hc_coords[i, 0], hc_coords[i, 1], c=color_hex,
                  s=300, marker='o', edgecolor='black', linewidth=2,
                  alpha=0.6, label='HC' if i == 0 else '', zorder=3)

        # CVD points (squares)
        ax.scatter(cvd_coords[i, 0], cvd_coords[i, 1], c=color_hex,
                  s=300, marker='s', edgecolor='black', linewidth=2,
                  alpha=0.6, label='CVD' if i == 0 else '', zorder=3)

        # Displacement arrows
        dx = cvd_coords[i, 0] - hc_coords[i, 0]
        dy = cvd_coords[i, 1] - hc_coords[i, 1]
        ax.arrow(hc_coords[i, 0], hc_coords[i, 1], dx, dy,
                head_width=0.05, head_length=0.05, fc='gray',
                ec='gray', alpha=0.5, zorder=2, linewidth=1.5)

        # Add color number
        ax.text(hc_coords[i, 0], hc_coords[i, 1], str(i+1),
               ha='center', va='center', fontsize=9,
               fontweight='bold', color='white', zorder=4)

    ax.set_title('HC vs CVD Overlay\n(arrows show CVD displacement)',
                fontsize=13, fontweight='bold')
    ax.set_xlabel('MDS Dimension 1', fontsize=11)
    ax.set_ylabel('MDS Dimension 2', fontsize=11)
    ax.legend(loc='best', fontsize=10)
    ax.grid(alpha=0.3, linestyle=':')

    # Set consistent axis limits if provided
    if xlim is not None:
        ax.set_xlim(xlim)
    if ylim is not None:
        ax.set_ylim(ylim)

    ax.set_aspect('equal', adjustable='box')


def main():
    parser = argparse.ArgumentParser(
        description='Visualize color representational space per subject'
    )
    parser.add_argument('--roi', type=str, required=True,
                       choices=['V1', 'V2', 'V3', 'hV4'],
                       help='ROI name')
    parser.add_argument('--results-dir', type=Path, required=True,
                       help='Directory containing between-subject results')

    args = parser.parse_args()

    # Find results file
    results_file = args.results_dir / f"{args.roi}_srm_between_subject_results.json"

    if not results_file.exists():
        print(f"❌ Results file not found: {results_file}")
        print("\nPlease run evaluate_srm_between_subject.py first.")
        return 1

    # Create visualizations
    visualize_all_subjects(results_file, args.results_dir, args.roi)

    return 0


if __name__ == '__main__':
    exit(main())
