#!/usr/bin/env python3
"""
"Scattered but Parallel" Phenomenon Visualization

Purpose: Show dual nature of CVD heterogeneity in V2
Target: Paper Figure 2 (SRM reveals structured heterogeneity)

Key Finding:
- Level 1 (Spatial): CVD-CVD disparity 1.71× > HC-HC (heterogeneous positions)
- Level 2 (Structural): CVD-CVD RDM r=0.591 > HC-HC r=0.517 (homogeneous relations)

Interpretation: CVD is NOT random noise, but systematic transformation
"Same melody, different keys" - Musical analogy

Panels:
A. MDS spatial layout showing scatter
B. RDM heatmaps showing preserved structure
C. RDM similarity comparison (bar plot)
D. Schematic diagram of dual-level model
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, FancyBboxPatch, FancyArrow
from matplotlib.lines import Line2D
import seaborn as sns
from scipy.spatial.distance import squareform, pdist
from scipy.stats import spearmanr
from sklearn.manifold import MDS
from pathlib import Path
import json


def compute_rdm(patterns, metric='correlation'):
    """
    Compute RDM from pattern matrix.

    Args:
        patterns: (n_colors, n_features) pattern matrix
        metric: Distance metric

    Returns:
        rdm: (n_colors, n_colors) RDM
    """
    if metric == 'correlation':
        rdm = 1 - np.corrcoef(patterns)
    else:
        rdm = squareform(pdist(patterns, metric=metric))

    return rdm


def compute_disparity(patterns1, patterns2):
    """Compute Procrustes disparity between pattern sets."""
    n, m = patterns1.shape
    return np.linalg.norm(patterns1 - patterns2, 'fro') / np.sqrt(n * m)


def load_srm_results(results_file):
    """Load SRM between-subject results."""
    with open(results_file, 'r') as f:
        results = json.load(f)
    return results


def plot_mds_spatial_scatter(hc_patterns, cvd_patterns, hc_labels, cvd_labels,
                             roi, output_path):
    """
    Panel A: MDS spatial layout showing CVD scatter.

    Shows CVD subjects occupy broader region than HC (spatial heterogeneity).
    """
    # Average patterns for each subject
    all_patterns = []
    all_labels = []
    all_groups = []

    for hc_label, hc_pat in zip(hc_labels, hc_patterns):
        all_patterns.append(np.mean(hc_pat, axis=0))  # Average across runs
        all_labels.append(hc_label)
        all_groups.append('HC')

    for cvd_label, cvd_pat in zip(cvd_labels, cvd_patterns):
        all_patterns.append(np.mean(cvd_pat, axis=0))
        all_labels.append(cvd_label)
        all_groups.append('CVD')

    # Compute RDMs
    rdms = [compute_rdm(pat) for pat in all_patterns]

    # RDM similarity matrix (n_subjects × n_subjects)
    n_subjects = len(all_patterns)
    rdm_sim_matrix = np.zeros((n_subjects, n_subjects))

    for i in range(n_subjects):
        for j in range(n_subjects):
            rdm_i = rdms[i][np.triu_indices(8, k=1)]
            rdm_j = rdms[j][np.triu_indices(8, k=1)]
            rdm_sim_matrix[i, j], _ = spearmanr(rdm_i, rdm_j)

    # MDS on RDM similarity (distance = 1 - similarity)
    rdm_dist = 1 - rdm_sim_matrix
    mds = MDS(n_components=2, dissimilarity='precomputed', random_state=42)
    coords_2d = mds.fit_transform(rdm_dist)

    # Separate HC and CVD
    hc_coords = coords_2d[:len(hc_labels)]
    cvd_coords = coords_2d[len(hc_labels):]

    # Create figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))

    # Panel A: MDS scatter with convex hulls
    from scipy.spatial import ConvexHull

    # Plot HC
    ax1.scatter(hc_coords[:, 0], hc_coords[:, 1],
               c='blue', s=200, alpha=0.6, marker='o', label='HC', edgecolors='black', linewidth=2)

    # HC labels
    for i, label in enumerate(hc_labels):
        ax1.text(hc_coords[i, 0], hc_coords[i, 1] + 0.05,
                label.replace('sub-', ''), fontsize=9, ha='center', fontweight='bold')

    # Convex hull for HC
    if len(hc_coords) >= 3:
        hull_hc = ConvexHull(hc_coords)
        for simplex in hull_hc.simplices:
            ax1.plot(hc_coords[simplex, 0], hc_coords[simplex, 1],
                    'b-', alpha=0.3, linewidth=2)

    # Plot CVD
    ax1.scatter(cvd_coords[:, 0], cvd_coords[:, 1],
               c='red', s=200, alpha=0.8, marker='^', label='CVD', edgecolors='black', linewidth=2)

    # CVD labels
    for i, label in enumerate(cvd_labels):
        ax1.text(cvd_coords[i, 0], cvd_coords[i, 1] + 0.05,
                label.replace('sub-', ''), fontsize=9, ha='center', fontweight='bold', color='red')

    # Convex hull for CVD
    if len(cvd_coords) >= 3:
        hull_cvd = ConvexHull(cvd_coords)
        for simplex in hull_cvd.simplices:
            ax1.plot(cvd_coords[simplex, 0], cvd_coords[simplex, 1],
                    'r--', alpha=0.5, linewidth=2)

    # Compute spatial spread
    hc_centroid = np.mean(hc_coords, axis=0)
    cvd_centroid = np.mean(cvd_coords, axis=0)

    hc_spread = np.mean(np.linalg.norm(hc_coords - hc_centroid, axis=1))
    cvd_spread = np.mean(np.linalg.norm(cvd_coords - cvd_centroid, axis=1))
    spread_ratio = cvd_spread / hc_spread

    ax1.set_xlabel('MDS Dimension 1', fontsize=12, fontweight='bold')
    ax1.set_ylabel('MDS Dimension 2', fontsize=12, fontweight='bold')
    ax1.set_title(f'Spatial Heterogeneity ({roi})\n'
                  f'CVD spread: {spread_ratio:.2f}× HC',
                  fontsize=14, fontweight='bold')
    ax1.legend(loc='best', fontsize=12, framealpha=0.9)
    ax1.grid(alpha=0.3)
    ax1.axis('equal')

    # Add annotation
    ax1.text(0.05, 0.95,
             f'HC spread: {hc_spread:.3f}\n'
             f'CVD spread: {cvd_spread:.3f}\n'
             f'Ratio: {spread_ratio:.2f}×',
             transform=ax1.transAxes, fontsize=11, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    # Panel B: RDM similarity matrix heatmap
    # Reorder: HC first, then CVD
    group_order = ['HC'] * len(hc_labels) + ['CVD'] * len(cvd_labels)

    im = ax2.imshow(rdm_sim_matrix, cmap='RdYlBu_r', vmin=-0.5, vmax=1.0,
                    aspect='auto', interpolation='nearest')

    # Add grid separating HC and CVD
    ax2.axhline(y=len(hc_labels)-0.5, color='black', linewidth=3)
    ax2.axvline(x=len(hc_labels)-0.5, color='black', linewidth=3)

    # Ticks
    ax2.set_xticks(range(n_subjects))
    ax2.set_yticks(range(n_subjects))
    ax2.set_xticklabels([l.replace('sub-', '') for l in all_labels],
                        rotation=45, ha='right', fontsize=9)
    ax2.set_yticklabels([l.replace('sub-', '') for l in all_labels],
                        fontsize=9)

    # Color-code labels
    for i, group in enumerate(group_order):
        color = 'blue' if group == 'HC' else 'red'
        ax2.get_xticklabels()[i].set_color(color)
        ax2.get_xticklabels()[i].set_fontweight('bold')
        ax2.get_yticklabels()[i].set_color(color)
        ax2.get_yticklabels()[i].set_fontweight('bold')

    ax2.set_xlabel('Subject', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Subject', fontsize=12, fontweight='bold')
    ax2.set_title(f'RDM Similarity Matrix ({roi})\n'
                  f'Structural Homogeneity',
                  fontsize=14, fontweight='bold')

    cbar = plt.colorbar(im, ax=ax2, fraction=0.046, pad=0.04)
    cbar.set_label('Spearman r (RDM similarity)', fontsize=10, fontweight='bold')

    # Compute within/between group similarities
    hc_hc_pairs = []
    cvd_cvd_pairs = []
    hc_cvd_pairs = []

    n_hc = len(hc_labels)
    for i in range(n_subjects):
        for j in range(i+1, n_subjects):
            if i < n_hc and j < n_hc:
                hc_hc_pairs.append(rdm_sim_matrix[i, j])
            elif i >= n_hc and j >= n_hc:
                cvd_cvd_pairs.append(rdm_sim_matrix[i, j])
            else:
                hc_cvd_pairs.append(rdm_sim_matrix[i, j])

    # Add annotation
    ax2.text(0.05, 0.95,
             f'HC-HC: {np.mean(hc_hc_pairs):.3f} ± {np.std(hc_hc_pairs):.3f}\n'
             f'CVD-CVD: {np.mean(cvd_cvd_pairs):.3f} ± {np.std(cvd_cvd_pairs):.3f}\n'
             f'HC-CVD: {np.mean(hc_cvd_pairs):.3f} ± {np.std(hc_cvd_pairs):.3f}',
             transform=ax2.transAxes, fontsize=11, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))

    plt.suptitle(f'"Scattered but Parallel" Phenomenon: {roi}',
                fontsize=16, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved MDS spatial scatter: {output_path}")

    return {
        'spatial_spread_ratio': float(spread_ratio),
        'hc_hc_rdm': {'mean': float(np.mean(hc_hc_pairs)), 'std': float(np.std(hc_hc_pairs))},
        'cvd_cvd_rdm': {'mean': float(np.mean(cvd_cvd_pairs)), 'std': float(np.std(cvd_cvd_pairs))},
        'hc_cvd_rdm': {'mean': float(np.mean(hc_cvd_pairs)), 'std': float(np.std(hc_cvd_pairs))}
    }


def plot_rdm_comparison(hc_patterns, cvd_patterns, roi, output_path):
    """
    Panel B: RDM heatmaps showing preserved structure.

    Three heatmaps: HC average, CVD average, Difference.
    """
    # Average across subjects and runs
    hc_avg = np.mean([np.mean(pat, axis=0) for pat in hc_patterns], axis=0)  # (8, n_features)
    cvd_avg = np.mean([np.mean(pat, axis=0) for pat in cvd_patterns], axis=0)

    # Compute RDMs
    rdm_hc = compute_rdm(hc_avg)
    rdm_cvd = compute_rdm(cvd_avg)
    rdm_diff = rdm_cvd - rdm_hc

    # RDM correlation
    rdm_hc_vec = rdm_hc[np.triu_indices(8, k=1)]
    rdm_cvd_vec = rdm_cvd[np.triu_indices(8, k=1)]
    rdm_corr, _ = spearmanr(rdm_hc_vec, rdm_cvd_vec)

    # Create figure
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    color_names = ['Red', 'Orange', 'Yellow', 'Green', 'Cyan', 'Blue', 'Purple', 'Magenta']

    # Panel A: HC RDM
    im1 = axes[0].imshow(rdm_hc, cmap='RdYlBu_r', vmin=0, vmax=2, aspect='auto')
    axes[0].set_xticks(range(8))
    axes[0].set_yticks(range(8))
    axes[0].set_xticklabels(color_names, rotation=45, ha='right', fontsize=9)
    axes[0].set_yticklabels(color_names, fontsize=9)
    axes[0].set_title(f'HC RDM ({roi})\nAverage Structure',
                     fontsize=12, fontweight='bold')
    plt.colorbar(im1, ax=axes[0], fraction=0.046, pad=0.04)

    # Panel B: CVD RDM
    im2 = axes[1].imshow(rdm_cvd, cmap='RdYlBu_r', vmin=0, vmax=2, aspect='auto')
    axes[1].set_xticks(range(8))
    axes[1].set_yticks(range(8))
    axes[1].set_xticklabels(color_names, rotation=45, ha='right', fontsize=9)
    axes[1].set_yticklabels(color_names, fontsize=9)
    axes[1].set_title(f'CVD RDM ({roi})\nPreserved Structure\nr = {rdm_corr:.3f}',
                     fontsize=12, fontweight='bold', color='green')
    plt.colorbar(im2, ax=axes[1], fraction=0.046, pad=0.04)

    # Panel C: Difference
    im3 = axes[2].imshow(rdm_diff, cmap='RdBu_r', vmin=-0.5, vmax=0.5, aspect='auto')
    axes[2].set_xticks(range(8))
    axes[2].set_yticks(range(8))
    axes[2].set_xticklabels(color_names, rotation=45, ha='right', fontsize=9)
    axes[2].set_yticklabels(color_names, fontsize=9)
    axes[2].set_title(f'Difference (CVD - HC)\nΔRDM',
                     fontsize=12, fontweight='bold')
    plt.colorbar(im3, ax=axes[2], fraction=0.046, pad=0.04, label='Δ Dissimilarity')

    plt.suptitle(f'RDM Structural Comparison: {roi}',
                fontsize=16, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved RDM comparison: {output_path}")

    return {
        'rdm_correlation': float(rdm_corr),
        'mean_diff': float(np.mean(np.abs(rdm_diff)))
    }


def plot_dual_level_schematic(output_path):
    """
    Panel D: Schematic diagram of dual-level model.

    Illustrates "scattered but parallel" concept with musical analogy.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

    # Panel A: Musical analogy
    ax1.set_xlim(0, 10)
    ax1.set_ylim(0, 10)
    ax1.axis('off')

    # Title
    ax1.text(5, 9.5, 'Musical Analogy: Same Melody, Different Keys',
            ha='center', fontsize=14, fontweight='bold')

    # HC: C major (tight cluster)
    hc_y = 7
    ax1.text(1, hc_y + 0.5, 'HC (C major):', fontsize=12, fontweight='bold', color='blue')
    notes = ['C', 'D', 'E', 'F', 'G', 'A', 'B', 'C']
    for i, note in enumerate(notes):
        x = 2 + i * 0.8
        ax1.add_patch(plt.Circle((x, hc_y), 0.3, color='blue', alpha=0.6))
        ax1.text(x, hc_y, note, ha='center', va='center', fontsize=10, fontweight='bold')

    # Draw line connecting notes
    ax1.plot([2 + i*0.8 for i in range(8)], [hc_y]*8, 'b-', linewidth=2, alpha=0.3)

    # CVD: Different keys (scattered positions)
    cvd_base_y = 4
    keys = ['C major', 'D major', 'E major']
    colors_cvd = ['#ff6b6b', '#ff8787', '#ffa5a5']
    y_offsets = [0, -1, -2]

    for key_idx, (key, color, y_off) in enumerate(zip(keys, colors_cvd, y_offsets)):
        y = cvd_base_y + y_off
        ax1.text(1, y + 0.5, f'CVD-{key_idx+1} ({key}):', fontsize=10, fontweight='bold', color=color)

        # Notes (transposed)
        base_notes = ['C', 'D', 'E', 'F', 'G', 'A', 'B', 'C']
        transpositions = [0, 2, 4]  # C, D, E
        note_names_all = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

        for i in range(8):
            # Transpose
            base_idx = note_names_all.index(base_notes[i] if base_notes[i] != 'C' or i == 0 else 'C')
            transposed_idx = (base_idx + transpositions[key_idx]) % 12
            transposed_note = note_names_all[transposed_idx]

            x = 2 + i * 0.8
            ax1.add_patch(plt.Circle((x, y), 0.25, color=color, alpha=0.7))
            ax1.text(x, y, transposed_note, ha='center', va='center', fontsize=8)

        # Draw line connecting notes (same melody structure)
        ax1.plot([2 + i*0.8 for i in range(8)], [y]*8, color=color, linestyle='--',
                linewidth=2, alpha=0.5)

    # Annotations
    ax1.text(5, 1.5,
            '✓ Different absolute pitch (spatial heterogeneity)\n'
            '✓ Same relative intervals (structural homogeneity)',
            ha='center', fontsize=11, style='italic',
            bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5))

    # Panel B: Two-level model
    ax2.set_xlim(0, 10)
    ax2.set_ylim(0, 10)
    ax2.axis('off')

    # Title
    ax2.text(5, 9.5, 'Dual-Level Model of CVD Heterogeneity',
            ha='center', fontsize=14, fontweight='bold')

    # Level 1: Spatial (Disparity)
    level1_y = 7
    ax2.add_patch(FancyBboxPatch((0.5, level1_y-0.5), 9, 1.5,
                                boxstyle="round,pad=0.1", edgecolor='red',
                                facecolor='#ffe6e6', linewidth=3))

    ax2.text(5, level1_y + 0.5, 'Level 1: Spatial Heterogeneity (Absolute Position)',
            ha='center', fontsize=12, fontweight='bold', color='red')

    ax2.text(5, level1_y - 0.2,
            'CVD-CVD disparity: 0.683 ± 0.022\n'
            'HC-HC disparity: 0.400 ± 0.074\n'
            '→ 1.71× higher (scattered positions)',
            ha='center', fontsize=10,
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    # Arrow
    ax2.add_patch(FancyArrow(5, level1_y - 1, 0, -1,
                            width=0.3, head_width=0.6, head_length=0.3,
                            fc='black', ec='black'))

    # Level 2: Structural (RDM)
    level2_y = 3.5
    ax2.add_patch(FancyBboxPatch((0.5, level2_y-0.5), 9, 1.5,
                                boxstyle="round,pad=0.1", edgecolor='green',
                                facecolor='#e6ffe6', linewidth=3))

    ax2.text(5, level2_y + 0.5, 'Level 2: Structural Homogeneity (Relational Patterns)',
            ha='center', fontsize=12, fontweight='bold', color='green')

    ax2.text(5, level2_y - 0.2,
            'CVD-CVD RDM: 0.591 ± 0.095\n'
            'HC-HC RDM: 0.517 ± 0.176\n'
            '→ 1.14× higher (preserved structure)',
            ha='center', fontsize=10,
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    # Bottom: Interpretation
    ax2.text(5, 1,
            'CVD heterogeneity is STRUCTURED, not random:\n'
            '• Different absolute positions (explain phenotypic variability)\n'
            '• Similar relational structure (shared compensatory mechanism)\n'
            '→ Systematic transformation, like musical transposition',
            ha='center', fontsize=11, style='italic',
            bbox=dict(boxstyle='round', facecolor='gold', alpha=0.6))

    plt.suptitle('"Scattered but Parallel": Conceptual Framework',
                fontsize=16, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved dual-level schematic: {output_path}")


def main():
    """
    Main execution: Generate "scattered but parallel" visualizations.
    """
    import argparse

    parser = argparse.ArgumentParser(description='"Scattered but Parallel" Visualization')
    parser.add_argument('--results-file', type=str,
                       default='./results/c010/combined_20260209/V2_procrustes_srm_results.json',
                       help='SRM results JSON file')
    parser.add_argument('--base-dir', type=str,
                       default='/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase1_preprocess_decoding',
                       help='Base directory with amplitude data')
    parser.add_argument('--roi', type=str, default='V2',
                       help='ROI to visualize')
    parser.add_argument('--output-dir', type=str,
                       default='./results/scattered_parallel_visualization',
                       help='Output directory')

    args = parser.parse_args()

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("="*80)
    print(f'"Scattered but Parallel" Visualization: {args.roi}')
    print("="*80)

    # For demonstration, create dummy data
    # In actual use, load from your SRM results
    print("\nGenerating schematic diagrams...")

    # Panel D: Dual-level schematic (doesn't need real data)
    print("\n[1/1] Dual-level schematic...")
    plot_dual_level_schematic(
        output_dir / f'{args.roi}_dual_level_schematic.png'
    )

    print("\n" + "="*80)
    print("✅ COMPLETE!")
    print("="*80)
    print(f"\nOutput directory: {output_dir}")
    print(f"\nGenerated file:")
    print(f"  1. {args.roi}_dual_level_schematic.png")

    print("\n📝 Note:")
    print("  To generate full visualizations with MDS scatter and RDM heatmaps,")
    print("  you need to load actual SRM-aligned amplitude data.")
    print("  See plot_mds_spatial_scatter() and plot_rdm_comparison() functions.")


if __name__ == '__main__':
    main()
