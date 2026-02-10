#!/usr/bin/env python3
"""
MDS Color Space Embedding for V4 ROI

Generate MDS color space visualizations for sub-01, 04, 08, 09, 10 in V4 ROI
Based on visualize_raw_procrustes_comparison.py

Author: Claude Code
Date: 2026-02-10
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from scipy.spatial.distance import pdist, squareform
from sklearn.manifold import MDS

# Configuration
DATA_DIR = Path(__file__).parent / "full_dataset_C010"
OUTPUT_DIR = Path(__file__).parent / "visualization"

# Subjects of interest (HC: 01, 04 / CVD: 08, 09, 10)
SUBJECTS = ['01', '04', '08', '09', '10']
ROI = 'V4'

N_COLORS = 8
N_RUNS = 6

# Color names and RGB values for visualization
COLOR_NAMES = ['Red', 'Orange', 'Yellow', 'Green', 'Cyan', 'Blue', 'Purple', 'Magenta']
COLOR_RGB = [
    '#FF0000',  # Red
    '#FF8800',  # Orange
    '#FFFF00',  # Yellow
    '#00FF00',  # Green
    '#00FFFF',  # Cyan
    '#0000FF',  # Blue
    '#8800FF',  # Purple
    '#FF00FF',  # Magenta
]


def load_subject_roi_data(subject_id, roi_name):
    """Load amplitude data for one subject-ROI"""
    data_path = DATA_DIR / f"sub-{subject_id}" / roi_name

    if not data_path.exists():
        print(f"  ⚠️  Data path not found: {data_path}")
        return None

    try:
        amplitudes_raw = np.load(data_path / "amplitudes_raw.npy")
        amplitudes_proc = np.load(data_path / "amplitudes_procrustes.npy")

        return {
            'amplitudes_raw': amplitudes_raw,
            'amplitudes_proc': amplitudes_proc,
        }
    except Exception as e:
        print(f"  ⚠️  Error loading data: {e}")
        return None


def compute_mds_embedding(amplitudes):
    """
    Compute MDS embedding for color space visualization

    Args:
        amplitudes: (n_runs, n_colors, n_voxels)

    Returns:
        embedding: (n_runs, n_colors, 2) - 2D MDS coordinates
    """
    n_runs, n_colors, n_voxels = amplitudes.shape

    # Compute MDS for each run separately
    embeddings = []

    for run_idx in range(n_runs):
        patterns = amplitudes[run_idx]  # (n_colors, n_voxels)

        # Compute pairwise distances (correlation distance)
        rdm = 1 - np.corrcoef(patterns)

        # MDS
        mds = MDS(n_components=2, dissimilarity='precomputed', random_state=42)
        embedding = mds.fit_transform(rdm)

        embeddings.append(embedding)

    embeddings = np.array(embeddings)  # (n_runs, n_colors, 2)

    return embeddings


def plot_mds_color_space(subject_id, roi_name, data, output_dir):
    """
    Plot MDS color space embedding (Before vs After Procrustes)
    """
    amplitudes_raw = data['amplitudes_raw']
    amplitudes_proc = data['amplitudes_proc']

    print(f"  Computing MDS embeddings for sub-{subject_id} {roi_name}...")

    # Compute MDS embeddings
    embedding_raw = compute_mds_embedding(amplitudes_raw)
    embedding_proc = compute_mds_embedding(amplitudes_proc)

    # Create figure
    fig, axes = plt.subplots(1, 2, figsize=(20, 9))

    titles = ['A. Before Procrustes', 'B. After Procrustes']
    embeddings = [embedding_raw, embedding_proc]

    for ax, title, embedding in zip(axes, titles, embeddings):
        # Plot each run's colors
        for run_idx in range(N_RUNS):
            for color_idx in range(N_COLORS):
                x = embedding[run_idx, color_idx, 0]
                y = embedding[run_idx, color_idx, 1]

                ax.scatter(x, y, c=COLOR_RGB[color_idx], s=200,
                          alpha=0.6, edgecolors='black', linewidths=1.5)

        # Add color labels (positioned at the mean of all runs)
        for color_idx in range(N_COLORS):
            mean_x = embedding[:, color_idx, 0].mean()
            mean_y = embedding[:, color_idx, 1].mean()

            ax.annotate(COLOR_NAMES[color_idx],
                       xy=(mean_x, mean_y),
                       xytext=(10, 10), textcoords='offset points',
                       fontsize=11, fontweight='bold',
                       bbox=dict(boxstyle='round,pad=0.4', facecolor='white',
                                edgecolor='black', alpha=0.9))

        ax.axhline(0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
        ax.axvline(0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
        ax.set_xlabel('MDS Dimension 1', fontsize=13, fontweight='bold')
        ax.set_ylabel('MDS Dimension 2', fontsize=13, fontweight='bold')
        ax.set_title(f'{title}\n{subject_id} {roi_name} (6 runs overlaid)',
                    fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)

    plt.tight_layout()

    output_file = output_dir / f'color_space_embedding_{subject_id}_{roi_name}.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"  ✓ Saved: {output_file.name}")


def main():
    """Main execution"""
    print(f"\n{'='*80}")
    print(f"MDS Color Space Embedding - V4 ROI Analysis")
    print(f"{'='*80}\n")
    print(f"Subjects: {', '.join(['sub-'+s for s in SUBJECTS])}")
    print(f"ROI: {ROI}")
    print(f"{'='*80}\n")

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Process each subject
    for subject_id in SUBJECTS:
        print(f"Processing sub-{subject_id} {ROI}...")

        # Load data
        data = load_subject_roi_data(subject_id, ROI)

        if data is None:
            print(f"  ⚠️  Skipping sub-{subject_id} {ROI} (data not found)")
            continue

        # Generate MDS plot
        plot_mds_color_space(subject_id, ROI, data, OUTPUT_DIR)
        print("")

    print(f"{'='*80}")
    print(f"✓ All visualizations saved to: {OUTPUT_DIR}")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    main()
