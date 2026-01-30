"""
RDM Visualization Utilities

Comprehensive visualization suite for representational dissimilarity matrices (RDMs),
color embeddings, and alignment transformations.

Visualizations include:
1. RDM heatmaps (before/after alignment, difference maps)
2. MDS/UMAP embeddings of color space
3. Procrustes transformation vector fields
4. RDM reliability scatter plots
5. Hierarchical clustering dendrograms

References:
- Kriegeskorte & Kievit (2013). Representational geometry: integrating cognition, computation, and the brain. Trends in Cognitive Sciences.
- Nili et al. (2014). A Toolbox for Representational Similarity Analysis. PLoS Computational Biology.
"""

import numpy as np
from typing import List, Tuple, Optional, Dict
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.spatial.distance import squareform, pdist
from scipy.stats import spearmanr
from scipy.cluster.hierarchy import dendrogram, linkage
from sklearn.manifold import MDS
from sklearn.decomposition import PCA


# Color definitions for 8-color experiment
COLOR_RGB = {
    'color_1': (1.0, 0.0, 0.0),      # Red
    'color_2': (1.0, 0.5, 0.0),      # Orange
    'color_3': (1.0, 1.0, 0.0),      # Yellow
    'color_4': (0.0, 1.0, 0.0),      # Green
    'color_5': (0.0, 1.0, 1.0),      # Cyan
    'color_6': (0.0, 0.0, 1.0),      # Blue
    'color_7': (0.5, 0.0, 1.0),      # Purple
    'color_8': (1.0, 0.0, 1.0)       # Magenta
}

COLOR_NAMES = ['Red', 'Orange', 'Yellow', 'Green', 'Cyan', 'Blue', 'Purple', 'Magenta']
COLOR_LABELS = [f'C{i+1}' for i in range(8)]


def plot_rdm_matrices(rdms: List[np.ndarray],
                     titles: List[str],
                     output_path: str,
                     cmap: str = 'viridis',
                     vmin: Optional[float] = None,
                     vmax: Optional[float] = None,
                     labels: List[str] = COLOR_LABELS,
                     figsize: Tuple[int, int] = (15, 10)) -> None:
    """
    Plot multiple RDMs as heatmaps in a grid.

    Args:
        rdms: List of (8, 8) RDM matrices
        titles: List of titles for each RDM
        output_path: Path to save figure
        cmap: Colormap
        vmin, vmax: Color scale limits (auto if None)
        labels: Labels for RDM axes
        figsize: Figure size
    """
    n_rdms = len(rdms)

    # Determine grid layout
    if n_rdms <= 3:
        nrows, ncols = 1, n_rdms
    elif n_rdms <= 6:
        nrows, ncols = 2, 3
    elif n_rdms <= 9:
        nrows, ncols = 3, 3
    else:
        nrows = int(np.ceil(n_rdms / 4))
        ncols = 4

    fig, axes = plt.subplots(nrows, ncols, figsize=figsize)
    if n_rdms == 1:
        axes = np.array([axes])
    axes = axes.flatten()

    # Auto-scale if not provided
    if vmin is None:
        vmin = min(rdm.min() for rdm in rdms)
    if vmax is None:
        vmax = max(rdm.max() for rdm in rdms)

    for idx, (rdm, title) in enumerate(zip(rdms, titles)):
        ax = axes[idx]

        # Heatmap
        im = ax.imshow(rdm, cmap=cmap, vmin=vmin, vmax=vmax, aspect='auto')

        # Labels
        ax.set_xticks(range(len(labels)))
        ax.set_yticks(range(len(labels)))
        ax.set_xticklabels(labels, fontsize=9)
        ax.set_yticklabels(labels, fontsize=9)

        # Title
        ax.set_title(title, fontsize=11, fontweight='bold')

        # Colorbar
        cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        cbar.ax.tick_params(labelsize=8)

    # Hide extra subplots
    for idx in range(n_rdms, len(axes)):
        axes[idx].axis('off')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved RDM matrices to {output_path}")


def plot_rdm_before_after_diff(rdm_before: np.ndarray,
                               rdm_after: np.ndarray,
                               output_path: str,
                               method_name: str = 'Procrustes',
                               labels: List[str] = COLOR_LABELS,
                               figsize: Tuple[int, int] = (15, 5)) -> None:
    """
    Plot before/after/difference RDMs side-by-side.

    Args:
        rdm_before: (8, 8) RDM before alignment
        rdm_after: (8, 8) RDM after alignment
        output_path: Path to save figure
        method_name: Name of alignment method
        labels: Labels for RDM axes
        figsize: Figure size
    """
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=figsize)

    # Determine common scale
    vmin = min(rdm_before.min(), rdm_after.min())
    vmax = max(rdm_before.max(), rdm_after.max())

    # Before
    im1 = ax1.imshow(rdm_before, cmap='viridis', vmin=vmin, vmax=vmax, aspect='auto')
    ax1.set_title(f'Before {method_name}', fontsize=14, fontweight='bold')
    ax1.set_xticks(range(len(labels)))
    ax1.set_yticks(range(len(labels)))
    ax1.set_xticklabels(labels, fontsize=10)
    ax1.set_yticklabels(labels, fontsize=10)
    plt.colorbar(im1, ax=ax1, fraction=0.046, pad=0.04)

    # After
    im2 = ax2.imshow(rdm_after, cmap='viridis', vmin=vmin, vmax=vmax, aspect='auto')
    ax2.set_title(f'After {method_name}', fontsize=14, fontweight='bold')
    ax2.set_xticks(range(len(labels)))
    ax2.set_yticks(range(len(labels)))
    ax2.set_xticklabels(labels, fontsize=10)
    ax2.set_yticklabels(labels, fontsize=10)
    plt.colorbar(im2, ax=ax2, fraction=0.046, pad=0.04)

    # Difference
    diff = rdm_after - rdm_before
    vmax_diff = max(abs(diff.min()), abs(diff.max()))
    im3 = ax3.imshow(diff, cmap='RdBu_r', vmin=-vmax_diff, vmax=vmax_diff, aspect='auto')
    ax3.set_title('Difference (After - Before)', fontsize=14, fontweight='bold')
    ax3.set_xticks(range(len(labels)))
    ax3.set_yticks(range(len(labels)))
    ax3.set_xticklabels(labels, fontsize=10)
    ax3.set_yticklabels(labels, fontsize=10)
    plt.colorbar(im3, ax=ax3, fraction=0.046, pad=0.04)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved before/after/diff RDMs to {output_path}")


def plot_rdm_reliability_scatter(rdms_before: List[np.ndarray],
                                 rdms_after: List[np.ndarray],
                                 output_path: str,
                                 method_name: str = 'Procrustes',
                                 figsize: Tuple[int, int] = (8, 8)) -> None:
    """
    Scatter plot showing how RDM structure changes with alignment.

    Each point is one pairwise dissimilarity value.

    Args:
        rdms_before: List of RDMs before alignment
        rdms_after: List of RDMs after alignment
        output_path: Path to save figure
        method_name: Name of alignment method
        figsize: Figure size
    """
    # Vectorize RDMs (upper triangle only)
    mask = np.triu(np.ones((8, 8), dtype=bool), k=1)

    before_vals = []
    after_vals = []

    for rdm_before, rdm_after in zip(rdms_before, rdms_after):
        before_vals.extend(rdm_before[mask])
        after_vals.extend(rdm_after[mask])

    before_vals = np.array(before_vals)
    after_vals = np.array(after_vals)

    # Correlation
    r, p = spearmanr(before_vals, after_vals)

    # Plot
    fig, ax = plt.subplots(figsize=figsize)

    ax.scatter(before_vals, after_vals, alpha=0.5, s=20, c='steelblue', edgecolors='none')

    # Diagonal line (no change)
    lim_min = min(before_vals.min(), after_vals.min())
    lim_max = max(before_vals.max(), after_vals.max())
    ax.plot([lim_min, lim_max], [lim_min, lim_max], 'r--', linewidth=2, label='No Change')

    # Best fit line
    coeffs = np.polyfit(before_vals, after_vals, 1)
    poly = np.poly1d(coeffs)
    x_fit = np.linspace(lim_min, lim_max, 100)
    y_fit = poly(x_fit)
    ax.plot(x_fit, y_fit, 'k-', linewidth=2, label=f'Best Fit (r={r:.3f})')

    ax.set_xlabel(f'Dissimilarity Before {method_name}', fontsize=12, fontweight='bold')
    ax.set_ylabel(f'Dissimilarity After {method_name}', fontsize=12, fontweight='bold')
    ax.set_title(f'RDM Structure Preservation: {method_name}', fontsize=14, fontweight='bold')
    ax.legend(loc='upper left', fontsize=11)
    ax.grid(alpha=0.3, linestyle=':')
    ax.set_aspect('equal', adjustable='box')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved RDM reliability scatter to {output_path}")
    print(f"Spearman r = {r:.3f}, p = {p:.2e}")


def plot_color_embedding_mds(rdm: np.ndarray,
                            output_path: str,
                            color_labels: Optional[List[str]] = None,
                            color_rgb: Optional[Dict] = None,
                            method: str = 'MDS',
                            figsize: Tuple[int, int] = (10, 10)) -> None:
    """
    MDS or UMAP embedding of RDM to 2D, color-coded by stimulus color.

    Args:
        rdm: (8, 8) dissimilarity matrix
        output_path: Path to save figure
        color_labels: Labels for colors (default: COLOR_NAMES)
        color_rgb: RGB tuples for colors (default: COLOR_RGB)
        method: 'MDS' or 'UMAP'
        figsize: Figure size
    """
    if color_labels is None:
        color_labels = COLOR_NAMES
    if color_rgb is None:
        color_rgb = COLOR_RGB

    # Extract colors in order
    colors = [color_rgb[f'color_{i+1}'] for i in range(8)]

    # Embedding
    if method == 'MDS':
        # MDS with precomputed dissimilarity
        mds = MDS(n_components=2, dissimilarity='precomputed', random_state=42)
        embedding = mds.fit_transform(rdm)
    elif method == 'UMAP':
        try:
            from umap import UMAP
            # UMAP expects distances
            umap_model = UMAP(n_components=2, metric='precomputed', random_state=42)
            embedding = umap_model.fit_transform(rdm)
        except ImportError:
            print("UMAP not available, falling back to MDS")
            mds = MDS(n_components=2, dissimilarity='precomputed', random_state=42)
            embedding = mds.fit_transform(rdm)
    else:
        raise ValueError(f"Unknown method: {method}")

    # Plot
    fig, ax = plt.subplots(figsize=figsize)

    for i, (label, color) in enumerate(zip(color_labels, colors)):
        ax.scatter(embedding[i, 0], embedding[i, 1],
                  c=[color], s=500, edgecolors='black', linewidths=2,
                  label=label, alpha=0.8)

        # Annotate
        ax.text(embedding[i, 0], embedding[i, 1], label,
               fontsize=12, fontweight='bold', ha='center', va='center')

    ax.set_xlabel(f'{method} Dimension 1', fontsize=12, fontweight='bold')
    ax.set_ylabel(f'{method} Dimension 2', fontsize=12, fontweight='bold')
    ax.set_title(f'Color Space Embedding ({method})', fontsize=14, fontweight='bold')
    ax.legend(loc='upper left', fontsize=10, framealpha=0.9)
    ax.grid(alpha=0.3, linestyle=':')
    ax.set_aspect('equal', adjustable='box')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved {method} embedding to {output_path}")


def plot_procrustes_transformation(patterns_before: np.ndarray,
                                  patterns_after: np.ndarray,
                                  output_path: str,
                                  color_labels: Optional[List[str]] = None,
                                  color_rgb: Optional[Dict] = None,
                                  figsize: Tuple[int, int] = (12, 10)) -> None:
    """
    Visualize Procrustes transformation as vector field in 2D PCA space.

    Shows how neural patterns move during alignment.

    Args:
        patterns_before: (8, n_voxels) - Patterns before alignment
        patterns_after: (8, n_voxels) - Patterns after alignment
        output_path: Path to save figure
        color_labels: Labels for colors
        color_rgb: RGB tuples for colors
        figsize: Figure size
    """
    if color_labels is None:
        color_labels = COLOR_NAMES
    if color_rgb is None:
        color_rgb = COLOR_RGB

    colors = [color_rgb[f'color_{i+1}'] for i in range(8)]

    # PCA to 2D
    pca = PCA(n_components=2)
    pca.fit(np.vstack([patterns_before, patterns_after]))

    before_2d = pca.transform(patterns_before)
    after_2d = pca.transform(patterns_after)

    # Plot
    fig, ax = plt.subplots(figsize=figsize)

    # Arrows showing transformation
    for i, (label, color) in enumerate(zip(color_labels, colors)):
        # Before position
        ax.scatter(before_2d[i, 0], before_2d[i, 1],
                  c=[color], s=300, edgecolors='black', linewidths=2,
                  alpha=0.5, marker='o', label=f'{label} (Before)' if i == 0 else '')

        # After position
        ax.scatter(after_2d[i, 0], after_2d[i, 1],
                  c=[color], s=300, edgecolors='black', linewidths=2,
                  alpha=0.9, marker='s')

        # Arrow
        ax.arrow(before_2d[i, 0], before_2d[i, 1],
                after_2d[i, 0] - before_2d[i, 0],
                after_2d[i, 1] - before_2d[i, 1],
                head_width=0.3, head_length=0.2, fc=color, ec='black',
                linewidth=1.5, alpha=0.7, length_includes_head=True)

        # Label
        ax.text(after_2d[i, 0], after_2d[i, 1] + 0.5, label,
               fontsize=10, fontweight='bold', ha='center', va='bottom')

    # Legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor='gray',
              markersize=12, alpha=0.5, label='Before', markeredgecolor='black'),
        Line2D([0], [0], marker='s', color='w', markerfacecolor='gray',
              markersize=12, alpha=0.9, label='After', markeredgecolor='black'),
        Line2D([0], [0], marker='>', color='black', markersize=10,
              label='Transformation', linestyle='-', linewidth=2)
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=11, framealpha=0.9)

    ax.set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]*100:.1f}% var)', fontsize=12, fontweight='bold')
    ax.set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]*100:.1f}% var)', fontsize=12, fontweight='bold')
    ax.set_title('Procrustes Transformation Vector Field', fontsize=14, fontweight='bold')
    ax.grid(alpha=0.3, linestyle=':')
    ax.set_aspect('equal', adjustable='box')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved Procrustes transformation visualization to {output_path}")


def plot_rdm_dendrogram(rdm: np.ndarray,
                        output_path: str,
                        labels: List[str] = COLOR_LABELS,
                        color_rgb: Optional[Dict] = None,
                        figsize: Tuple[int, int] = (10, 8)) -> None:
    """
    Plot hierarchical clustering dendrogram from RDM.

    Args:
        rdm: (8, 8) dissimilarity matrix
        output_path: Path to save figure
        labels: Labels for leaves
        color_rgb: RGB tuples for color-coding (optional)
        figsize: Figure size
    """
    # Convert RDM to condensed distance matrix
    rdm_condensed = squareform(rdm, checks=False)

    # Hierarchical clustering
    linkage_matrix = linkage(rdm_condensed, method='average')

    # Plot
    fig, ax = plt.subplots(figsize=figsize)

    dendrogram(linkage_matrix, labels=labels, ax=ax,
              leaf_font_size=12, color_threshold=0)

    ax.set_xlabel('Color', fontsize=12, fontweight='bold')
    ax.set_ylabel('Dissimilarity', fontsize=12, fontweight='bold')
    ax.set_title('Hierarchical Clustering of Color Representations', fontsize=14, fontweight='bold')
    ax.grid(axis='y', alpha=0.3, linestyle=':')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved dendrogram to {output_path}")


def create_comprehensive_rdm_report(rdms_dict: Dict[str, np.ndarray],
                                   patterns_dict: Optional[Dict[str, np.ndarray]] = None,
                                   output_dir: str = './rdm_report',
                                   subject_id: str = 'sub-01',
                                   roi: str = 'V1') -> None:
    """
    Generate comprehensive RDM analysis report with all visualizations.

    Args:
        rdms_dict: Dict with keys like 'raw', 'procrustes', 'srm', 'whitening'
                  Values are (8, 8) RDMs or lists of RDMs
        patterns_dict: Dict with patterns (before/after) for transformation viz
        output_dir: Output directory for all figures
        subject_id: Subject identifier
        roi: ROI name
    """
    import os
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n=== Generating Comprehensive RDM Report: {subject_id} {roi} ===")

    # 1. All RDMs in grid
    rdm_list = []
    title_list = []
    for key, rdm in rdms_dict.items():
        if isinstance(rdm, list):
            rdm = np.mean(rdm, axis=0)  # Average if multiple
        rdm_list.append(rdm)
        title_list.append(key.replace('_', ' ').title())

    plot_rdm_matrices(rdm_list, title_list,
                     os.path.join(output_dir, f'{subject_id}_{roi}_rdms_all.png'))

    # 2. Before/After comparison (if available)
    if 'raw' in rdms_dict and 'procrustes' in rdms_dict:
        rdm_raw = rdms_dict['raw'] if not isinstance(rdms_dict['raw'], list) else np.mean(rdms_dict['raw'], axis=0)
        rdm_proc = rdms_dict['procrustes'] if not isinstance(rdms_dict['procrustes'], list) else np.mean(rdms_dict['procrustes'], axis=0)

        plot_rdm_before_after_diff(rdm_raw, rdm_proc,
                                   os.path.join(output_dir, f'{subject_id}_{roi}_rdm_before_after.png'),
                                   method_name='Procrustes')

    # 3. MDS embeddings for each method
    for key, rdm in rdms_dict.items():
        if isinstance(rdm, list):
            rdm = np.mean(rdm, axis=0)

        plot_color_embedding_mds(rdm,
                                os.path.join(output_dir, f'{subject_id}_{roi}_mds_{key}.png'))

        # Dendrogram
        plot_rdm_dendrogram(rdm,
                           os.path.join(output_dir, f'{subject_id}_{roi}_dendrogram_{key}.png'))

    # 4. Transformation vector field (if patterns available)
    if patterns_dict is not None:
        if 'before' in patterns_dict and 'after' in patterns_dict:
            plot_procrustes_transformation(patterns_dict['before'],
                                          patterns_dict['after'],
                                          os.path.join(output_dir, f'{subject_id}_{roi}_transformation.png'))

    print(f"Report saved to {output_dir}")


if __name__ == '__main__':
    # Test with synthetic data
    print("Testing RDM visualization with synthetic data...")

    np.random.seed(42)

    # Create synthetic RDMs
    # Ground truth: Circular color space
    angles = np.linspace(0, 2*np.pi, 8, endpoint=False)
    true_positions = np.stack([np.cos(angles), np.sin(angles)], axis=1)

    # RDM from Euclidean distances
    rdm_true = squareform(pdist(true_positions, metric='euclidean'))

    # Add noise for "before" RDM
    rdm_before = rdm_true + np.random.randn(8, 8) * 0.3
    rdm_before = (rdm_before + rdm_before.T) / 2  # Symmetrize

    # "After" RDM (closer to true)
    rdm_after = rdm_true + np.random.randn(8, 8) * 0.1
    rdm_after = (rdm_after + rdm_after.T) / 2

    # Test visualizations
    print("\n1. Testing RDM matrices plot...")
    plot_rdm_matrices([rdm_before, rdm_after, rdm_true],
                     ['Before Alignment', 'After Alignment', 'Ground Truth'],
                     '/tmp/test_rdm_matrices.png')

    print("\n2. Testing before/after/diff plot...")
    plot_rdm_before_after_diff(rdm_before, rdm_after,
                               '/tmp/test_rdm_before_after.png')

    print("\n3. Testing MDS embedding...")
    plot_color_embedding_mds(rdm_after, '/tmp/test_mds.png')

    print("\n4. Testing dendrogram...")
    plot_rdm_dendrogram(rdm_after, '/tmp/test_dendrogram.png')

    # Test transformation visualization
    patterns_before = np.random.randn(8, 100)
    patterns_after = patterns_before + np.random.randn(8, 100) * 0.1

    print("\n5. Testing Procrustes transformation...")
    plot_procrustes_transformation(patterns_before, patterns_after,
                                   '/tmp/test_transformation.png')

    print("\nAll tests completed! Check /tmp/test_*.png files.")
