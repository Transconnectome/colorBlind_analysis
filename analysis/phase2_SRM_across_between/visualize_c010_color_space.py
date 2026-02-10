#!/usr/bin/env python3
"""
Visualize C010 SRM Color Representational Space and RDM Similarity

Creates two key visualizations for C010 SRM results:
1. Color Representational Space per Subject (MDS 2D projection)
2. Inter-Subject RDM Similarity Matrix

Usage:
    python visualize_c010_color_space.py --results-dir results/c010/combined_20260209/ --method procrustes

Options:
    --method: 'procrustes' or 'raw' (default: procrustes, better performing)
    --roi: Specific ROI or 'all' (default: all)
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.manifold import MDS
from scipy.stats import spearmanr

# Color definitions
COLOR_NAMES = [
    'Red', 'Orange', 'Yellow', 'Green',
    'Cyan', 'Blue', 'Purple', 'Magenta'
]

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

# Subject groups
HC_SUBJECTS = [f'sub-{i:02d}' for i in range(1, 8)]
CVD_SUBJECTS = [f'sub-{i:02d}' for i in range(8, 11)]


def compute_rdm_from_amplitudes(amplitudes: np.ndarray) -> np.ndarray:
    """
    Compute RDM from amplitudes using Pearson dissimilarity.

    Args:
        amplitudes: (n_colors, n_features)

    Returns:
        rdm: (n_colors, n_colors) dissimilarity matrix
    """
    # Pearson dissimilarity = 1 - correlation
    rdm = 1 - np.corrcoef(amplitudes)
    return rdm


def rdm_to_2d_mds(rdm: np.ndarray, random_state: int = 42) -> np.ndarray:
    """
    Convert RDM to 2D coordinates using MDS.

    Args:
        rdm: (n_colors, n_colors) dissimilarity matrix
        random_state: Random seed

    Returns:
        coords_2d: (n_colors, 2) 2D coordinates
    """
    mds = MDS(n_components=2, dissimilarity='precomputed', random_state=random_state)
    coords_2d = mds.fit_transform(rdm)
    return coords_2d


def plot_subject_color_space(coords_2d: np.ndarray, subject: str, ax: plt.Axes,
                             is_cvd: bool = False,
                             xlim: Optional[tuple] = None,
                             ylim: Optional[tuple] = None) -> None:
    """Plot 2D color space for a single subject."""
    # Plot points
    for i, (x, y) in enumerate(coords_2d):
        color_hex = COLOR_HEX[COLOR_NAMES[i]]
        ax.scatter(x, y, c=color_hex, s=200, edgecolor='black',
                  linewidth=2, alpha=0.8, zorder=3)
        ax.text(x, y, str(i+1), ha='center', va='center',
               fontsize=9, fontweight='bold', color='white', zorder=4)

    # Connecting lines
    for i in range(len(coords_2d)):
        for j in range(i+1, len(coords_2d)):
            ax.plot([coords_2d[i, 0], coords_2d[j, 0]],
                   [coords_2d[i, 1], coords_2d[j, 1]],
                   'k-', alpha=0.1, linewidth=0.5, zorder=1)

    group = 'CVD' if is_cvd else 'HC'
    ax.set_title(f'{subject} ({group})', fontsize=11, fontweight='bold')
    ax.set_xlabel('MDS Dimension 1', fontsize=9)
    ax.set_ylabel('MDS Dimension 2', fontsize=9)
    ax.grid(alpha=0.3, linestyle=':', zorder=0)

    if xlim: ax.set_xlim(xlim)
    if ylim: ax.set_ylim(ylim)
    ax.set_aspect('equal', adjustable='box')


def create_legend_panel(ax: plt.Axes) -> None:
    """Create color legend panel."""
    ax.axis('off')
    ax.text(0.5, 0.95, 'Color Legend', ha='center', va='top',
            fontsize=12, fontweight='bold', transform=ax.transAxes)

    y_start = 0.85
    y_step = 0.09

    for i, color_name in enumerate(COLOR_NAMES):
        y_pos = y_start - i * y_step
        circle = plt.Circle((0.2, y_pos), 0.03, color=COLOR_HEX[color_name],
                           transform=ax.transAxes, zorder=3)
        ax.add_patch(circle)
        ax.text(0.3, y_pos, f'{i+1}. {color_name}', va='center',
               fontsize=10, transform=ax.transAxes)


def visualize_color_space_all_subjects(aligned_file: Path, roi: str,
                                       method: str, output_dir: Path) -> None:
    """Create grid visualization of color spaces for all subjects."""
    print(f"\n{'='*70}")
    print(f"Visualizing Color Representational Space: {roi} ({method})")
    print(f"{'='*70}\n")

    # Load aligned amplitudes
    aligned_data = np.load(aligned_file, allow_pickle=True).item()

    all_subjects = HC_SUBJECTS + CVD_SUBJECTS
    print(f"HC subjects: {HC_SUBJECTS}")
    print(f"CVD subjects: {CVD_SUBJECTS}\n")

    # Compute RDMs and MDS coordinates
    coords_2d = {}
    print("Computing MDS coordinates...")
    for subject in all_subjects:
        if subject not in aligned_data:
            print(f"  ⚠️  {subject} not in aligned data")
            continue

        amplitudes = aligned_data[subject]  # (8, k)
        rdm = compute_rdm_from_amplitudes(amplitudes)
        coords_2d[subject] = rdm_to_2d_mds(rdm)
        print(f"  ✓ {subject}")

    # Global axis limits
    all_coords = np.vstack(list(coords_2d.values()))
    x_min, x_max = all_coords[:, 0].min(), all_coords[:, 0].max()
    y_min, y_max = all_coords[:, 1].min(), all_coords[:, 1].max()

    x_padding = (x_max - x_min) * 0.1
    y_padding = (y_max - y_min) * 0.1

    xlim = (x_min - x_padding, x_max + x_padding)
    ylim = (y_min - y_padding, y_max + y_padding)

    # Create subplot grid
    n_subjects = len(coords_2d)
    n_cols = 4
    n_rows = (n_subjects + 1 + n_cols - 1) // n_cols  # +1 for legend

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(16, 4*n_rows))
    axes = axes.flatten()

    # Plot each subject
    for idx, subject in enumerate(all_subjects):
        if subject not in coords_2d:
            axes[idx].axis('off')
            continue

        is_cvd = subject in CVD_SUBJECTS
        plot_subject_color_space(coords_2d[subject], subject, axes[idx],
                                is_cvd=is_cvd, xlim=xlim, ylim=ylim)

    # Legend panel
    create_legend_panel(axes[n_subjects])

    # Hide unused
    for idx in range(n_subjects + 1, len(axes)):
        axes[idx].axis('off')

    # Main title
    k_features = aligned_data[HC_SUBJECTS[0]].shape[1]
    fig.suptitle(f'Color Representational Space per Subject: {roi}\n'
                f'{method.capitalize()} SRM k={k_features}, MDS 2D Projection',
                fontsize=16, fontweight='bold', y=0.995)

    plt.tight_layout()

    output_file = output_dir / f"{roi}_{method}_color_space_all_subjects.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\n✅ Saved to {output_file}")
    plt.close()


def visualize_rdm_similarity_matrix(aligned_file: Path, roi: str,
                                   method: str, output_dir: Path) -> None:
    """Create inter-subject RDM similarity matrix."""
    print(f"\n{'='*70}")
    print(f"Visualizing RDM Similarity Matrix: {roi} ({method})")
    print(f"{'='*70}\n")

    # Load aligned amplitudes
    aligned_data = np.load(aligned_file, allow_pickle=True).item()

    all_subjects = HC_SUBJECTS + CVD_SUBJECTS

    # Compute RDMs
    rdms = {}
    print("Computing RDMs...")
    for subject in all_subjects:
        if subject not in aligned_data:
            print(f"  ⚠️  {subject} not in aligned data")
            continue

        amplitudes = aligned_data[subject]
        rdms[subject] = compute_rdm_from_amplitudes(amplitudes)
        print(f"  ✓ {subject}")

    # Compute pairwise RDM correlations
    subjects_ordered = [s for s in all_subjects if s in rdms]
    n_subjects = len(subjects_ordered)

    similarity_matrix = np.zeros((n_subjects, n_subjects))

    print("\nComputing inter-subject RDM correlations...")
    for i, subj_i in enumerate(subjects_ordered):
        for j, subj_j in enumerate(subjects_ordered):
            if i == j:
                similarity_matrix[i, j] = 1.0
            else:
                # Upper triangle of RDM
                mask = np.triu(np.ones_like(rdms[subj_i], dtype=bool), k=1)
                vec_i = rdms[subj_i][mask]
                vec_j = rdms[subj_j][mask]

                r, _ = spearmanr(vec_i, vec_j)
                similarity_matrix[i, j] = r

    # Plot heatmap
    fig, ax = plt.subplots(figsize=(10, 8))

    sns.heatmap(similarity_matrix, annot=True, fmt='.2f', cmap='RdYlGn',
               center=0, vmin=-0.5, vmax=1.0,
               xticklabels=subjects_ordered, yticklabels=subjects_ordered,
               cbar_kws={'label': 'RDM Correlation (Spearman r)'},
               ax=ax)

    # Add group separators
    n_hc = len([s for s in subjects_ordered if s in HC_SUBJECTS])
    ax.axhline(n_hc, color='black', linewidth=3)
    ax.axvline(n_hc, color='black', linewidth=3)

    k_features = aligned_data[subjects_ordered[0]].shape[1]
    ax.set_title(f'Inter-Subject RDM Similarity: {roi} ({method.capitalize()} SRM k={k_features})',
                fontsize=14, fontweight='bold')

    plt.tight_layout()

    output_file = output_dir / f"{roi}_{method}_rdm_similarity_matrix.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\n✅ Saved to {output_file}")
    plt.close()

    # Print summary statistics
    print("\n=== RDM Similarity Summary ===")

    hc_idx = [i for i, s in enumerate(subjects_ordered) if s in HC_SUBJECTS]
    cvd_idx = [i for i, s in enumerate(subjects_ordered) if s in CVD_SUBJECTS]

    # HC-HC pairs
    hc_hc_vals = []
    for i in hc_idx:
        for j in hc_idx:
            if i < j:
                hc_hc_vals.append(similarity_matrix[i, j])

    # CVD-CVD pairs
    cvd_cvd_vals = []
    for i in cvd_idx:
        for j in cvd_idx:
            if i < j:
                cvd_cvd_vals.append(similarity_matrix[i, j])

    # HC-CVD pairs
    hc_cvd_vals = []
    for i in hc_idx:
        for j in cvd_idx:
            hc_cvd_vals.append(similarity_matrix[i, j])

    if hc_hc_vals:
        print(f"HC-HC:   {np.mean(hc_hc_vals):.3f} ± {np.std(hc_hc_vals):.3f} (n={len(hc_hc_vals)})")
    if cvd_cvd_vals:
        print(f"CVD-CVD: {np.mean(cvd_cvd_vals):.3f} ± {np.std(cvd_cvd_vals):.3f} (n={len(cvd_cvd_vals)})")
    if hc_cvd_vals:
        print(f"HC-CVD:  {np.mean(hc_cvd_vals):.3f} ± {np.std(hc_cvd_vals):.3f} (n={len(hc_cvd_vals)})")


def main():
    parser = argparse.ArgumentParser(
        description='Visualize C010 SRM Color Space and RDM Similarity'
    )
    parser.add_argument('--results-dir', type=Path, required=True,
                       help='Combined results directory')
    parser.add_argument('--method', type=str, default='procrustes',
                       choices=['procrustes', 'raw'],
                       help='SRM method to visualize (default: procrustes)')
    parser.add_argument('--roi', type=str, default='all',
                       help='Specific ROI or "all" (default: all)')

    args = parser.parse_args()

    if not args.results_dir.exists():
        print(f"❌ Results directory not found: {args.results_dir}")
        return 1

    # Create visualization output directory
    vis_dir = args.results_dir / "visualizations"
    vis_dir.mkdir(exist_ok=True)

    # Determine which ROIs to process
    if args.roi == 'all':
        rois = ['V1', 'V2', 'V3', 'V4']
    else:
        rois = [args.roi]

    print(f"\n{'='*70}")
    print("C010 SRM Color Space & RDM Visualization")
    print(f"{'='*70}")
    print(f"Method: {args.method}")
    print(f"ROIs: {rois}")
    print(f"Output: {vis_dir}\n")

    # Process each ROI
    for roi in rois:
        # Find aligned amplitudes file
        aligned_file = args.results_dir / f"{roi}_{args.method}_aligned_amplitudes.npy"

        if not aligned_file.exists():
            print(f"\n⚠️  Aligned amplitudes not found: {aligned_file}")
            print(f"Skipping {roi}...")
            continue

        # Generate visualizations
        visualize_color_space_all_subjects(aligned_file, roi, args.method, vis_dir)
        visualize_rdm_similarity_matrix(aligned_file, roi, args.method, vis_dir)

    print(f"\n{'='*70}")
    print(f"Visualization complete!")
    print(f"{'='*70}\n")

    return 0


if __name__ == '__main__':
    exit(main())
