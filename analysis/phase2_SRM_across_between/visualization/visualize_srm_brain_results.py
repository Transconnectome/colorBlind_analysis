#!/usr/bin/env python3
"""
SRM Brain Visualization: Using Actual C010 SRM Results

Purpose: Visualize SRM between-subject results with brain-based conceptual figures
Data: C010 Procrustes-averaged SRM results (k=4 features)

Key advantages:
- All subjects in same feature space (8 colors × 4 features)
- No voxel mismatch issues
- Direct HC-CVD comparison possible
- Real disparity metrics from SRM analysis

Outputs:
1. 3D feature space visualization (HC vs CVD clusters)
2. Disparity comparison (HC-HC vs CVD-HC)
3. RDM similarity heatmaps
4. "Scattered but Parallel" demonstration
5. Brain-based conceptual summary
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, FancyBboxPatch, Ellipse
from mpl_toolkits.mplot3d import Axes3D
from sklearn.decomposition import PCA
from sklearn.manifold import MDS
from scipy.spatial.distance import squareform, pdist
from scipy.stats import spearmanr
import seaborn as sns
from pathlib import Path
import json


def load_srm_results(results_dir, roi='V2', method='procrustes'):
    """
    Load SRM results from C010 analysis.

    Args:
        results_dir: Base results directory
        roi: ROI name (V1, V2, V3, V4)
        method: 'procrustes' or 'raw'

    Returns:
        results_json: Dict with statistical results
        aligned_amps: Dict of {subject: (8, k) aligned amplitudes}
    """
    results_dir = Path(results_dir)

    # Find directories with this ROI's results
    timestamp_dirs = sorted([d for d in results_dir.iterdir() if d.is_dir() and d.name.startswith('202')])
    if not timestamp_dirs:
        raise FileNotFoundError(f"No timestamp directories found in {results_dir}")

    # Find the directory that has this ROI's results
    target_dir = None
    for d in reversed(timestamp_dirs):  # Start from most recent
        json_file = d / f'{roi}_{method}_srm_results.json'
        amp_file = d / f'{roi}_{method}_aligned_amplitudes.npy'
        if json_file.exists() and amp_file.exists():
            target_dir = d
            break

    if target_dir is None:
        raise FileNotFoundError(f"No directory found with {roi} {method} results")

    print(f"Loading SRM results from: {target_dir.name}")

    # Load JSON results
    json_file = target_dir / f'{roi}_{method}_srm_results.json'
    with open(json_file, 'r') as f:
        results_json = json.load(f)

    # Load aligned amplitudes
    amp_file = target_dir / f'{roi}_{method}_aligned_amplitudes.npy'
    aligned_amps = np.load(amp_file, allow_pickle=True).item()

    print(f"Loaded {roi} {method} SRM results:")
    print(f"  Subjects: {len(aligned_amps)}")
    print(f"  Features: k={results_json['n_features']}")
    print(f"  Shape per subject: {list(aligned_amps.values())[0].shape}")

    return results_json, aligned_amps


def plot_3d_feature_space(aligned_amps, results_json, roi, output_path):
    """
    Plot 3D feature space showing HC and CVD clusters.

    Since we have k=4 features, use PCA to project to 3D for visualization.
    """
    hc_subjects = results_json['subjects']['hc']
    cvd_subjects = results_json['subjects']['cvd']

    # Collect all patterns
    hc_patterns = []
    cvd_patterns = []

    for subj in hc_subjects:
        if subj in aligned_amps:
            hc_patterns.append(aligned_amps[subj])  # (8, k)

    for subj in cvd_subjects:
        if subj in aligned_amps:
            cvd_patterns.append(aligned_amps[subj])

    # Stack for PCA
    all_patterns = np.vstack([np.vstack(hc_patterns), np.vstack(cvd_patterns)])

    # PCA to 3D
    pca = PCA(n_components=3)
    all_3d = pca.fit_transform(all_patterns)

    # Split back
    n_hc_points = len(hc_patterns) * 8
    hc_3d = all_3d[:n_hc_points]
    cvd_3d = all_3d[n_hc_points:]

    # Create figure
    fig = plt.figure(figsize=(16, 6))

    # Panel A: All points
    ax1 = fig.add_subplot(131, projection='3d')
    ax1.scatter(hc_3d[:, 0], hc_3d[:, 1], hc_3d[:, 2],
               c='blue', s=50, alpha=0.4, label=f'HC (n={len(hc_subjects)})', marker='o')
    ax1.scatter(cvd_3d[:, 0], cvd_3d[:, 1], cvd_3d[:, 2],
               c='red', s=50, alpha=0.6, label=f'CVD (n={len(cvd_subjects)})', marker='^')

    ax1.set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.1%})', fontweight='bold')
    ax1.set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.1%})', fontweight='bold')
    ax1.set_zlabel(f'PC3 ({pca.explained_variance_ratio_[2]:.1%})', fontweight='bold')
    ax1.set_title(f'{roi} SRM Feature Space\n(All color trials)', fontsize=14, fontweight='bold')
    ax1.legend(loc='upper right')
    ax1.view_init(elev=20, azim=45)

    # Panel B: Centroids with error ellipsoids
    ax2 = fig.add_subplot(132, projection='3d')

    # Compute centroids
    hc_centroid = np.mean(hc_3d, axis=0)
    cvd_centroid = np.mean(cvd_3d, axis=0)

    # Plot centroids
    ax2.scatter(*hc_centroid, c='blue', s=300, marker='*',
               edgecolors='black', linewidth=2, label='HC centroid', zorder=10)
    ax2.scatter(*cvd_centroid, c='red', s=300, marker='*',
               edgecolors='black', linewidth=2, label='CVD centroid', zorder=10)

    # Plot individual subject means
    for i, patterns in enumerate(hc_patterns):
        subj_3d = pca.transform(patterns)
        subj_mean = np.mean(subj_3d, axis=0)
        ax2.scatter(*subj_mean, c='blue', s=100, alpha=0.6, marker='o')
        # Connect to centroid
        ax2.plot([subj_mean[0], hc_centroid[0]],
                [subj_mean[1], hc_centroid[1]],
                [subj_mean[2], hc_centroid[2]],
                'b--', alpha=0.3, linewidth=1)

    for i, patterns in enumerate(cvd_patterns):
        subj_3d = pca.transform(patterns)
        subj_mean = np.mean(subj_3d, axis=0)
        ax2.scatter(*subj_mean, c='red', s=100, alpha=0.8, marker='^')
        # Connect to centroid
        ax2.plot([subj_mean[0], cvd_centroid[0]],
                [subj_mean[1], cvd_centroid[1]],
                [subj_mean[2], cvd_centroid[2]],
                'r--', alpha=0.5, linewidth=1)

    # Draw line between group centroids
    ax2.plot([hc_centroid[0], cvd_centroid[0]],
            [hc_centroid[1], cvd_centroid[1]],
            [hc_centroid[2], cvd_centroid[2]],
            'k-', linewidth=3, alpha=0.7, label='Group separation')

    # Compute separation distance
    separation = np.linalg.norm(cvd_centroid - hc_centroid)

    ax2.set_xlabel(f'PC1', fontweight='bold')
    ax2.set_ylabel(f'PC2', fontweight='bold')
    ax2.set_zlabel(f'PC3', fontweight='bold')
    ax2.set_title(f'Group Centroids\nSeparation: {separation:.3f}',
                 fontsize=14, fontweight='bold')
    ax2.legend(loc='upper right', fontsize=9)
    ax2.view_init(elev=20, azim=45)

    # Panel C: Statistical summary
    ax3 = fig.add_subplot(133)
    ax3.axis('off')

    # Extract metrics
    hc_hc_disp = results_json['results']['disparities']['hc_to_hc_reference']
    cvd_hc_disp = results_json['results']['disparities']['cvd_to_hc_reference']
    stats = results_json['results']['statistical_tests']['hc_vs_cvd']

    # Create text summary
    summary_text = f"""
{roi} SRM Between-Subject Results
{'='*40}

Group Separation (Procrustes Disparity):
  HC-to-HC:  {hc_hc_disp['mean']:.3f} ± {hc_hc_disp['std']:.3f}
  CVD-to-HC: {cvd_hc_disp['mean']:.3f} ± {cvd_hc_disp['std']:.3f}

  Δ(CVD-HC): {cvd_hc_disp['mean'] - hc_hc_disp['mean']:.3f}

Statistical Test (HC vs CVD):
  t = {stats['t_statistic']:.2f}
  p = {stats['p_value']:.4f} {'✓ Significant' if stats['significant'] else '✗ Not sig'}
  Cohen's d = {stats['cohens_d']:.2f}

Effect Size: {'Large' if abs(stats['cohens_d']) > 0.8 else 'Medium' if abs(stats['cohens_d']) > 0.5 else 'Small'}

PCA Variance Explained:
  PC1: {pca.explained_variance_ratio_[0]:.1%}
  PC2: {pca.explained_variance_ratio_[1]:.1%}
  PC3: {pca.explained_variance_ratio_[2]:.1%}
  Total: {sum(pca.explained_variance_ratio_[:3]):.1%}
"""

    ax3.text(0.1, 0.9, summary_text, transform=ax3.transAxes,
            fontsize=11, verticalalignment='top', family='monospace',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    plt.suptitle(f'SRM Feature Space Visualization: {roi}',
                fontsize=16, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved 3D feature space plot: {output_path}")

    return {
        'separation': float(separation),
        'variance_explained': pca.explained_variance_ratio_.tolist()
    }


def plot_disparity_comparison(results_json, roi, output_path):
    """
    Plot disparity comparison showing HC-HC baseline vs CVD-HC.
    """
    hc_hc = results_json['results']['disparities']['hc_to_hc_reference']
    cvd_hc = results_json['results']['disparities']['cvd_to_hc_reference']
    cvd_cvd = results_json['results']['disparities']['cvd_to_cvd_pairwise']
    stats = results_json['results']['statistical_tests']['hc_vs_cvd']

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Panel A: Boxplot comparison
    data_to_plot = [
        hc_hc['values'],
        cvd_hc['values'],
        cvd_cvd['values']
    ]

    labels = [
        f"HC-to-HC\n(n={len(hc_hc['values'])})",
        f"CVD-to-HC\n(n={len(cvd_hc['values'])})",
        f"CVD-to-CVD\n(n={len(cvd_cvd['values'])})"
    ]

    colors = ['blue', 'red', 'orange']

    bp = ax1.boxplot(data_to_plot, labels=labels, patch_artist=True,
                     widths=0.6, showmeans=True, meanline=True)

    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.6)

    ax1.set_ylabel('Procrustes Disparity', fontsize=12, fontweight='bold')
    ax1.set_title(f'{roi} Group Comparison', fontsize=14, fontweight='bold')
    ax1.grid(alpha=0.3, axis='y')

    # Add significance stars
    y_max = max([max(d) for d in data_to_plot]) * 1.1
    if stats['significant']:
        ax1.plot([1, 2], [y_max, y_max], 'k-', linewidth=2)
        significance = '***' if stats['p_value'] < 0.001 else '**' if stats['p_value'] < 0.01 else '*'
        ax1.text(1.5, y_max, significance, ha='center', va='bottom',
                fontsize=16, fontweight='bold')

    # Add statistics text
    ax1.text(0.05, 0.95,
            f"t = {stats['t_statistic']:.2f}\n"
            f"p = {stats['p_value']:.4f}\n"
            f"d = {stats['cohens_d']:.2f}",
            transform=ax1.transAxes, fontsize=11, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))

    # Panel B: Effect size visualization
    groups = ['HC-HC', 'CVD-HC']
    means = [hc_hc['mean'], cvd_hc['mean']]
    stds = [hc_hc['std'], cvd_hc['std']]

    x_pos = np.arange(len(groups))
    bars = ax2.bar(x_pos, means, yerr=stds, capsize=10, alpha=0.7,
                   color=['blue', 'red'], edgecolor='black', linewidth=2)

    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(groups, fontsize=12, fontweight='bold')
    ax2.set_ylabel('Mean Disparity', fontsize=12, fontweight='bold')
    ax2.set_title(f'Effect Size: Cohen\'s d = {stats["cohens_d"]:.2f}',
                 fontsize=14, fontweight='bold')
    ax2.grid(alpha=0.3, axis='y')

    # Add values on bars
    for bar, mean, std in zip(bars, means, stds):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + std,
                f'{mean:.3f}\n±{std:.3f}',
                ha='center', va='bottom', fontsize=10, fontweight='bold')

    # Add effect interpretation
    interpretation = 'Large' if abs(stats['cohens_d']) > 0.8 else \
                     'Medium' if abs(stats['cohens_d']) > 0.5 else 'Small'

    ax2.text(0.5, 0.15,
            f"Effect Size: {interpretation}\n"
            f"Δ = {cvd_hc['mean'] - hc_hc['mean']:.3f}",
            transform=ax2.transAxes, fontsize=12, ha='center',
            bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.7),
            fontweight='bold')

    plt.suptitle(f'Procrustes Disparity Comparison: {roi}',
                fontsize=16, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved disparity comparison: {output_path}")


def plot_rdm_similarity_analysis(results_json, roi, output_path):
    """
    Plot RDM similarity analysis showing "scattered but parallel" pattern.
    """
    rdm_sims = results_json['results']['rdm_similarities']

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Panel A: RDM similarity comparison
    groups = ['HC-HC', 'CVD-CVD', 'HC-CVD']
    means = [rdm_sims['hc_hc']['mean'],
             rdm_sims['cvd_cvd']['mean'],
             rdm_sims['hc_cvd']['mean']]
    stds = [rdm_sims['hc_hc']['std'],
            rdm_sims['cvd_cvd']['std'],
            rdm_sims['hc_cvd']['std']]
    n_pairs = [rdm_sims['hc_hc']['n_pairs'],
               rdm_sims['cvd_cvd']['n_pairs'],
               rdm_sims['hc_cvd']['n_pairs']]

    colors_rdm = ['blue', 'red', 'purple']
    x_pos = np.arange(len(groups))

    bars = ax1.bar(x_pos, means, yerr=stds, capsize=10, alpha=0.7,
                   color=colors_rdm, edgecolor='black', linewidth=2)

    ax1.set_xticks(x_pos)
    ax1.set_xticklabels([f"{g}\n(n={n})" for g, n in zip(groups, n_pairs)],
                        fontsize=11)
    ax1.set_ylabel('RDM Similarity (Spearman r)', fontsize=12, fontweight='bold')
    ax1.set_title(f'{roi} RDM Structural Similarity', fontsize=14, fontweight='bold')
    ax1.axhline(y=0, color='k', linestyle='-', linewidth=0.5)
    ax1.grid(alpha=0.3, axis='y')
    ax1.set_ylim([-0.2, 1.0])

    # Add values on bars
    for bar, mean, std in zip(bars, means, stds):
        height = max(bar.get_height(), 0)
        ax1.text(bar.get_x() + bar.get_width()/2., height + std + 0.05,
                f'{mean:.3f}', ha='center', va='bottom',
                fontsize=10, fontweight='bold')

    # Highlight if CVD-CVD > HC-HC
    if rdm_sims['cvd_cvd']['mean'] > rdm_sims['hc_hc']['mean']:
        ax1.text(0.5, 0.95,
                '⚠️ CVD-CVD > HC-HC\n"Scattered but Parallel"',
                transform=ax1.transAxes, ha='center', va='top',
                fontsize=11, fontweight='bold', color='red',
                bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.8))

    # Panel B: Interpretation diagram
    ax2.axis('off')
    ax2.set_xlim(0, 10)
    ax2.set_ylim(0, 10)

    # Title
    ax2.text(5, 9.5, '"Scattered but Parallel" Interpretation',
            ha='center', fontsize=14, fontweight='bold')

    # Level 1: Spatial (Disparity)
    hc_hc_disp = results_json['results']['disparities']['hc_to_hc_reference']['mean']
    cvd_cvd_disp = results_json['results']['disparities']['cvd_to_cvd_pairwise']['mean']
    spatial_ratio = cvd_cvd_disp / hc_hc_disp if hc_hc_disp > 0 else 0

    ax2.add_patch(Rectangle((0.5, 6.5), 9, 2,
                            facecolor='#ffe6e6', edgecolor='red', linewidth=3))
    ax2.text(5, 8, 'Level 1: Spatial Heterogeneity', ha='center',
            fontsize=12, fontweight='bold', color='red')
    ax2.text(5, 7.2,
            f'CVD-CVD disparity: {cvd_cvd_disp:.3f}\n'
            f'HC-HC disparity: {hc_hc_disp:.3f}\n'
            f'Ratio: {spatial_ratio:.2f}× (CVD more scattered)',
            ha='center', fontsize=10,
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))

    # Arrow
    ax2.arrow(5, 6.3, 0, -1.3, head_width=0.4, head_length=0.3,
             fc='black', ec='black', linewidth=2)

    # Level 2: Structural (RDM)
    structural_ratio = rdm_sims['cvd_cvd']['mean'] / rdm_sims['hc_hc']['mean'] if rdm_sims['hc_hc']['mean'] > 0 else 0

    ax2.add_patch(Rectangle((0.5, 3), 9, 2,
                            facecolor='#e6ffe6', edgecolor='green', linewidth=3))
    ax2.text(5, 4.5, 'Level 2: Structural Homogeneity', ha='center',
            fontsize=12, fontweight='bold', color='green')
    ax2.text(5, 3.7,
            f'CVD-CVD RDM: {rdm_sims["cvd_cvd"]["mean"]:.3f}\n'
            f'HC-HC RDM: {rdm_sims["hc_hc"]["mean"]:.3f}\n'
            f'Ratio: {structural_ratio:.2f}× (CVD {"more" if structural_ratio > 1 else "less"} similar)',
            ha='center', fontsize=10,
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))

    # Bottom conclusion
    if spatial_ratio > 1.2 and structural_ratio > 0.9:
        conclusion = "✓ 'Scattered but Parallel' pattern confirmed:\nDifferent positions but similar structure"
        color = 'gold'
    else:
        conclusion = "Mixed pattern:\nCheck individual subject profiles"
        color = 'lightblue'

    ax2.text(5, 1.5, conclusion, ha='center', fontsize=11, style='italic',
            bbox=dict(boxstyle='round', facecolor=color, alpha=0.7))

    plt.suptitle(f'RDM Similarity Analysis: {roi}',
                fontsize=16, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved RDM similarity analysis: {output_path}")


def create_brain_conceptual_summary(results_json, roi, metrics_3d, output_path):
    """
    Create brain-based conceptual summary figure.
    """
    fig = plt.figure(figsize=(18, 10))

    # Title
    fig.text(0.5, 0.96,
             f'{roi} SRM Between-Subject Analysis: Brain-Based Summary',
             ha='center', fontsize=18, fontweight='bold')

    # Main finding
    stats = results_json['results']['statistical_tests']['hc_vs_cvd']
    fig.text(0.5, 0.92,
             f'{"✓ Significant" if stats["significant"] else "✗ Not Significant"} HC-CVD Difference: '
             f'p={stats["p_value"]:.4f}, d={stats["cohens_d"]:.2f}',
             ha='center', fontsize=14, fontweight='bold',
             color='green' if stats['significant'] else 'gray')

    # Create grid
    gs = fig.add_gridspec(2, 3, hspace=0.3, wspace=0.3,
                         left=0.08, right=0.92, top=0.88, bottom=0.08)

    # Panel 1: SRM Feature Space
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.axis('off')
    ax1.text(0.5, 0.9, '1. SRM Feature Space', ha='center', fontsize=13, fontweight='bold')
    ax1.text(0.5, 0.5,
             f'Shared dimensions: k={results_json["n_features"]}\n'
             f'HC subjects: {len(results_json["subjects"]["hc"])}\n'
             f'CVD subjects: {len(results_json["subjects"]["cvd"])}\n\n'
             f'Group separation: {metrics_3d["separation"]:.3f}\n'
             f'Variance explained (3D): {sum(metrics_3d["variance_explained"][:3]):.1%}',
             ha='center', va='center', fontsize=10,
             bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))

    # Panel 2: Disparity Metrics
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.axis('off')
    ax2.text(0.5, 0.9, '2. Procrustes Disparity', ha='center', fontsize=13, fontweight='bold')

    hc_hc = results_json['results']['disparities']['hc_to_hc_reference']
    cvd_hc = results_json['results']['disparities']['cvd_to_hc_reference']

    ax2.text(0.5, 0.5,
             f'HC-to-HC baseline:\n  {hc_hc["mean"]:.3f} ± {hc_hc["std"]:.3f}\n\n'
             f'CVD-to-HC:\n  {cvd_hc["mean"]:.3f} ± {cvd_hc["std"]:.3f}\n\n'
             f'Difference:\n  Δ = {cvd_hc["mean"] - hc_hc["mean"]:.3f}\n'
             f'  ({(cvd_hc["mean"]/hc_hc["mean"] - 1)*100:.1f}% increase)',
             ha='center', va='center', fontsize=10,
             bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.8))

    # Panel 3: RDM Similarity
    ax3 = fig.add_subplot(gs[0, 2])
    ax3.axis('off')
    ax3.text(0.5, 0.9, '3. RDM Similarity', ha='center', fontsize=13, fontweight='bold')

    rdm = results_json['results']['rdm_similarities']
    ax3.text(0.5, 0.5,
             f'HC-HC structure:\n  r = {rdm["hc_hc"]["mean"]:.3f} ± {rdm["hc_hc"]["std"]:.3f}\n\n'
             f'CVD-CVD structure:\n  r = {rdm["cvd_cvd"]["mean"]:.3f} ± {rdm["cvd_cvd"]["std"]:.3f}\n\n'
             f'Pattern:\n  {"Scattered but Parallel" if rdm["cvd_cvd"]["mean"] > rdm["hc_hc"]["mean"] else "Heterogeneous"}',
             ha='center', va='center', fontsize=10,
             bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))

    # Panel 4: Brain Schematic (simplified)
    ax4 = fig.add_subplot(gs[1, :])
    ax4.set_xlim(0, 10)
    ax4.set_ylim(0, 4)
    ax4.axis('off')

    # Draw simplified brain regions
    ax4.text(5, 3.5, f'{roi} Region', ha='center', fontsize=14, fontweight='bold')

    # HC representation
    hc_x = 2.5
    ax4.add_patch(Circle((hc_x, 2), 0.8, facecolor='blue', alpha=0.6, edgecolor='black', linewidth=2))
    ax4.text(hc_x, 2, 'HC', ha='center', va='center', fontsize=12, fontweight='bold', color='white')
    ax4.text(hc_x, 0.8, f'Disparity: {hc_hc["mean"]:.3f}\nRDM: {rdm["hc_hc"]["mean"]:.3f}',
            ha='center', fontsize=9, bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))

    # CVD representation
    cvd_x = 7.5
    ax4.add_patch(Circle((cvd_x, 2), 0.8, facecolor='red', alpha=0.6, edgecolor='black', linewidth=2))
    ax4.text(cvd_x, 2, 'CVD', ha='center', va='center', fontsize=12, fontweight='bold', color='white')
    ax4.text(cvd_x, 0.8, f'Disparity: {cvd_hc["mean"]:.3f}\nRDM: {rdm["cvd_cvd"]["mean"]:.3f}',
            ha='center', fontsize=9, bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))

    # Arrow between groups
    ax4.annotate('', xy=(cvd_x-1, 2), xytext=(hc_x+1, 2),
                arrowprops=dict(arrowstyle='<->', lw=3, color='black'))
    ax4.text(5, 2.4, f'p={stats["p_value"]:.4f}\nd={stats["cohens_d"]:.2f}',
            ha='center', fontsize=11, fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.9))

    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved brain conceptual summary: {output_path}")


def main():
    """
    Main execution: Generate all SRM brain visualizations.
    """
    import argparse

    parser = argparse.ArgumentParser(description='SRM Brain Visualization from C010 Results')
    parser.add_argument('--results-dir', type=str,
                       default='./results/c010/separated',
                       help='C010 SRM results directory')
    parser.add_argument('--roi', type=str, default='V2',
                       help='ROI to visualize (V1, V2, V3, V4)')
    parser.add_argument('--method', type=str, default='procrustes',
                       choices=['procrustes', 'raw'],
                       help='SRM method to visualize')
    parser.add_argument('--output-dir', type=str,
                       default='./results/srm_brain_visualization',
                       help='Output directory')

    args = parser.parse_args()

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("="*80)
    print(f"SRM Brain Visualization: {args.roi} ({args.method})")
    print("="*80)

    # Load SRM results
    print("\n[1/5] Loading SRM results...")
    results_json, aligned_amps = load_srm_results(args.results_dir, args.roi, args.method)

    # Generate visualizations
    print("\n" + "="*80)
    print("Generating visualizations...")
    print("="*80)

    # 1. 3D feature space
    print("\n[2/5] 3D feature space plot...")
    metrics_3d = plot_3d_feature_space(
        aligned_amps, results_json, args.roi,
        output_dir / f'{args.roi}_{args.method}_3d_feature_space.png'
    )

    # 2. Disparity comparison
    print("\n[3/5] Disparity comparison...")
    plot_disparity_comparison(
        results_json, args.roi,
        output_dir / f'{args.roi}_{args.method}_disparity_comparison.png'
    )

    # 3. RDM similarity analysis
    print("\n[4/5] RDM similarity analysis...")
    plot_rdm_similarity_analysis(
        results_json, args.roi,
        output_dir / f'{args.roi}_{args.method}_rdm_similarity.png'
    )

    # 4. Brain conceptual summary
    print("\n[5/5] Brain conceptual summary...")
    create_brain_conceptual_summary(
        results_json, args.roi, metrics_3d,
        output_dir / f'{args.roi}_{args.method}_brain_summary.png'
    )

    # Save combined metrics
    all_metrics = {
        'roi': args.roi,
        'method': args.method,
        'results': results_json['results'],
        '3d_metrics': metrics_3d
    }

    with open(output_dir / f'{args.roi}_{args.method}_all_metrics.json', 'w') as f:
        json.dump(all_metrics, f, indent=2)

    print("\n" + "="*80)
    print("✅ COMPLETE!")
    print("="*80)
    print(f"\nOutput directory: {output_dir}")
    print("\nGenerated files:")
    print(f"  1. {args.roi}_{args.method}_3d_feature_space.png")
    print(f"  2. {args.roi}_{args.method}_disparity_comparison.png")
    print(f"  3. {args.roi}_{args.method}_rdm_similarity.png")
    print(f"  4. {args.roi}_{args.method}_brain_summary.png")
    print(f"  5. {args.roi}_{args.method}_all_metrics.json")

    # Print key findings
    stats = results_json['results']['statistical_tests']['hc_vs_cvd']
    print("\n🎯 Key Findings:")
    print(f"  • HC-CVD significant: {stats['significant']}")
    print(f"  • p-value: {stats['p_value']:.4f}")
    print(f"  • Cohen's d: {stats['cohens_d']:.2f}")
    print(f"  • Effect size: {'Large' if abs(stats['cohens_d']) > 0.8 else 'Medium' if abs(stats['cohens_d']) > 0.5 else 'Small'}")


if __name__ == '__main__':
    main()
