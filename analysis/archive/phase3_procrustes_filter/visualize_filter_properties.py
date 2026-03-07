#!/usr/bin/env python3
"""
Visualize Phase 2A Filter Properties

Creates comprehensive visualizations for Section 3.3:
1. RDM improvement analysis (before/after filtering)
2. A matrix interpretation (structure, eigenvalues, gain patterns)
3. b vector analysis (distribution, patterns)

Usage:
    python scripts/visualize_filter_properties.py
"""

import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy.stats import spearmanr
import seaborn as sns

# Configuration
BASE_DIR = Path("/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis")
PATTERN_DIR = BASE_DIR / "results/group_level/phase2a_data/patterns"
MODEL_DIR = BASE_DIR / "results/filters/models/optionD/20251219_122240"
OUTPUT_DIR = BASE_DIR / "results/filters/analysis/filter_properties"

CVD_SUBJECTS = ['08', '09', '10']
ROIS = ['V1', 'V2']
COLOR_NAMES = ['Red', 'Orange', 'Yellow', 'Chartreuse',
               'Green', 'Cyan', 'Blue', 'Magenta']


def compute_rdm(pattern):
    """
    Compute Representational Dissimilarity Matrix

    Args:
        pattern: (n_colors, n_voxels)

    Returns:
        rdm: (n_colors, n_colors) dissimilarity matrix
    """
    n_colors = pattern.shape[0]
    rdm = np.zeros((n_colors, n_colors))

    for i in range(n_colors):
        for j in range(n_colors):
            if i == j:
                rdm[i, j] = 0.0
            else:
                corr, _ = spearmanr(pattern[i], pattern[j])
                rdm[i, j] = 1 - corr

    return rdm


def visualize_rdm_improvement(subject_id, roi):
    """
    Visualize RDM improvement: Before | After | HC Target
    Shows how filtering improves color dissimilarity structure
    """
    print(f"\n[RDM Improvement] sub-{subject_id} {roi}")

    # Load data
    hc_pattern = np.load(PATTERN_DIR / "HC_mean" / f"{roi}_pattern.npy")
    cvd_pattern = np.load(PATTERN_DIR / f"sub-{subject_id}" / f"{roi}_pattern.npy")

    # Voxel alignment
    n_voxels = min(hc_pattern.shape[1], cvd_pattern.shape[1])
    hc_pattern = hc_pattern[:, :n_voxels]
    cvd_pattern = cvd_pattern[:, :n_voxels]

    # Load filter
    A = np.load(MODEL_DIR / f"sub-{subject_id}" / roi / "A_matrix.npy")
    b = np.load(MODEL_DIR / f"sub-{subject_id}" / roi / "b_vector.npy")

    # Apply filter
    filtered_pattern = cvd_pattern @ A + b[np.newaxis, :]

    # Compute RDMs
    rdm_hc = compute_rdm(hc_pattern)
    rdm_cvd_before = compute_rdm(cvd_pattern)
    rdm_cvd_after = compute_rdm(filtered_pattern)

    # Compute correlations
    corr_before, _ = spearmanr(rdm_cvd_before.flatten(), rdm_hc.flatten())
    corr_after, _ = spearmanr(rdm_cvd_after.flatten(), rdm_hc.flatten())

    # Create figure
    fig = plt.figure(figsize=(18, 5))
    gs = gridspec.GridSpec(1, 4, width_ratios=[1, 1, 1, 1.2])

    # Shared colorbar limits
    vmin = 0.0
    vmax = max(rdm_hc.max(), rdm_cvd_before.max(), rdm_cvd_after.max())

    # 1. CVD Before
    ax1 = plt.subplot(gs[0])
    im1 = ax1.imshow(rdm_cvd_before, cmap='hot', vmin=vmin, vmax=vmax)
    ax1.set_title(f'CVD Before Filtering\nρ(HC) = {corr_before:.3f}', fontsize=11)
    ax1.set_xticks(range(8))
    ax1.set_yticks(range(8))
    ax1.set_xticklabels(COLOR_NAMES, rotation=45, ha='right', fontsize=8)
    ax1.set_yticklabels(COLOR_NAMES, fontsize=8)
    plt.colorbar(im1, ax=ax1, fraction=0.046, pad=0.04)

    # 2. CVD After
    ax2 = plt.subplot(gs[1])
    im2 = ax2.imshow(rdm_cvd_after, cmap='hot', vmin=vmin, vmax=vmax)
    ax2.set_title(f'CVD After Filtering\nρ(HC) = {corr_after:.3f}', fontsize=11)
    ax2.set_xticks(range(8))
    ax2.set_yticks(range(8))
    ax2.set_xticklabels(COLOR_NAMES, rotation=45, ha='right', fontsize=8)
    ax2.set_yticklabels(COLOR_NAMES, fontsize=8)
    plt.colorbar(im2, ax=ax2, fraction=0.046, pad=0.04)

    # 3. HC Target
    ax3 = plt.subplot(gs[2])
    im3 = ax3.imshow(rdm_hc, cmap='hot', vmin=vmin, vmax=vmax)
    ax3.set_title('HC Target\n(Reference)', fontsize=11)
    ax3.set_xticks(range(8))
    ax3.set_yticks(range(8))
    ax3.set_xticklabels(COLOR_NAMES, rotation=45, ha='right', fontsize=8)
    ax3.set_yticklabels(COLOR_NAMES, fontsize=8)
    plt.colorbar(im3, ax=ax3, fraction=0.046, pad=0.04)

    # 4. Scatter plot: CVD vs HC RDM
    ax4 = plt.subplot(gs[3])

    # Get upper triangle indices (excluding diagonal)
    mask = np.triu(np.ones((8, 8)), k=1).astype(bool)
    rdm_hc_upper = rdm_hc[mask]
    rdm_before_upper = rdm_cvd_before[mask]
    rdm_after_upper = rdm_cvd_after[mask]

    # Scatter
    ax4.scatter(rdm_hc_upper, rdm_before_upper, alpha=0.6, s=50,
                label=f'Before (ρ={corr_before:.3f})', color='red', edgecolors='black', linewidth=0.5)
    ax4.scatter(rdm_hc_upper, rdm_after_upper, alpha=0.6, s=50,
                label=f'After (ρ={corr_after:.3f})', color='green', edgecolors='black', linewidth=0.5)

    # Identity line
    lims = [0, max(rdm_hc_upper.max(), rdm_before_upper.max(), rdm_after_upper.max())]
    ax4.plot(lims, lims, 'k--', alpha=0.5, linewidth=1, label='Identity')

    ax4.set_xlabel('HC RDM Dissimilarity', fontsize=10)
    ax4.set_ylabel('CVD RDM Dissimilarity', fontsize=10)
    ax4.set_title('RDM Structure Matching', fontsize=11)
    ax4.legend(fontsize=9)
    ax4.grid(True, alpha=0.3)
    ax4.set_aspect('equal')

    plt.suptitle(f'RDM Improvement Analysis: sub-{subject_id} {roi}\n'
                 f'Correlation improvement: {corr_before:.3f} → {corr_after:.3f} '
                 f'(+{(corr_after - corr_before):.3f})',
                 fontsize=13, fontweight='bold')

    plt.tight_layout()

    # Save
    output_file = OUTPUT_DIR / f"rdm_improvement_sub{subject_id}_{roi}.png"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  Saved: {output_file}")
    plt.close()

    return corr_before, corr_after


def visualize_A_matrix(subject_id, roi):
    """
    Visualize A matrix structure and properties

    Subplots:
    1. Full A matrix heatmap
    2. Diagonal elements distribution
    3. Off-diagonal elements distribution
    4. Eigenvalue spectrum
    """
    print(f"\n[A Matrix] sub-{subject_id} {roi}")

    # Load A matrix
    A = np.load(MODEL_DIR / f"sub-{subject_id}" / roi / "A_matrix.npy")
    n_voxels = A.shape[0]

    # Compute properties
    diag_elements = np.diag(A)
    off_diag_mask = ~np.eye(n_voxels, dtype=bool)
    off_diag_elements = A[off_diag_mask]

    # Eigenvalues
    eigenvalues = np.linalg.eigvalsh(A)
    eigenvalues = np.sort(eigenvalues)[::-1]  # Descending order

    # Deviation from identity
    I = np.eye(n_voxels)
    deviation = np.linalg.norm(A - I, ord='fro')
    relative_dev = (deviation / np.linalg.norm(I, ord='fro')) * 100

    # Singular values
    singular_values = np.linalg.svd(A, compute_uv=False)
    condition_number = singular_values.max() / singular_values.min()

    # Create figure
    fig = plt.figure(figsize=(18, 10))
    gs = gridspec.GridSpec(2, 3, height_ratios=[1, 1])

    # 1. Full A matrix heatmap
    ax1 = plt.subplot(gs[0, :2])

    # Subsample for visualization if too large
    if n_voxels > 100:
        step = max(1, n_voxels // 100)
        A_vis = A[::step, ::step]
        extent = [0, n_voxels, n_voxels, 0]
    else:
        A_vis = A
        extent = None

    vmax = max(abs(A_vis.min()), abs(A_vis.max()))
    im1 = ax1.imshow(A_vis, cmap='RdBu_r', vmin=-vmax, vmax=vmax, extent=extent, aspect='auto')
    ax1.set_title(f'A Matrix Heatmap ({n_voxels}×{n_voxels})\n'
                  f'||A-I||_F = {deviation:.3f} ({relative_dev:.2f}%)',
                  fontsize=11, fontweight='bold')
    ax1.set_xlabel('Voxel Index', fontsize=10)
    ax1.set_ylabel('Voxel Index', fontsize=10)
    plt.colorbar(im1, ax=ax1, fraction=0.046, pad=0.04, label='Weight')

    # 2. Diagonal elements
    ax2 = plt.subplot(gs[0, 2])
    ax2.hist(diag_elements, bins=30, alpha=0.7, color='blue', edgecolor='black')
    ax2.axvline(1.0, color='red', linestyle='--', linewidth=2, label='Identity (1.0)')
    ax2.axvline(diag_elements.mean(), color='green', linestyle='-', linewidth=2,
                label=f'Mean ({diag_elements.mean():.3f})')
    ax2.set_xlabel('Diagonal Value', fontsize=10)
    ax2.set_ylabel('Count', fontsize=10)
    ax2.set_title(f'Diagonal Elements (Self-Gain)\n'
                  f'Mean: {diag_elements.mean():.3f} ± {diag_elements.std():.3f}\n'
                  f'Range: [{diag_elements.min():.3f}, {diag_elements.max():.3f}]',
                  fontsize=10)
    ax2.legend(fontsize=8)
    ax2.grid(True, alpha=0.3, axis='y')

    # 3. Off-diagonal elements
    ax3 = plt.subplot(gs[1, 0])
    ax3.hist(off_diag_elements, bins=50, alpha=0.7, color='orange', edgecolor='black')
    ax3.axvline(0.0, color='red', linestyle='--', linewidth=2, label='Zero')
    ax3.axvline(off_diag_elements.mean(), color='green', linestyle='-', linewidth=2,
                label=f'Mean ({off_diag_elements.mean():.4f})')
    ax3.set_xlabel('Off-Diagonal Value', fontsize=10)
    ax3.set_ylabel('Count', fontsize=10)
    ax3.set_title(f'Off-Diagonal Elements (Cross-Coupling)\n'
                  f'Mean: {off_diag_elements.mean():.4f} ± {off_diag_elements.std():.3f}\n'
                  f'Sparsity: {(np.abs(off_diag_elements) < 0.05).sum() / len(off_diag_elements) * 100:.1f}% near-zero',
                  fontsize=10)
    ax3.legend(fontsize=8)
    ax3.grid(True, alpha=0.3, axis='y')

    # 4. Eigenvalue spectrum
    ax4 = plt.subplot(gs[1, 1])
    ax4.plot(eigenvalues, 'o-', linewidth=2, markersize=4, color='purple')
    ax4.axhline(1.0, color='red', linestyle='--', linewidth=1, alpha=0.5, label='Identity eigenvalue')
    ax4.set_xlabel('Eigenvalue Index', fontsize=10)
    ax4.set_ylabel('Eigenvalue', fontsize=10)
    ax4.set_title(f'Eigenvalue Spectrum\n'
                  f'Range: [{eigenvalues.min():.3f}, {eigenvalues.max():.3f}]\n'
                  f'Condition #: {condition_number:.2f}',
                  fontsize=10)
    ax4.legend(fontsize=8)
    ax4.grid(True, alpha=0.3)

    # 5. Diagonal vs Off-diagonal scatter
    ax5 = plt.subplot(gs[1, 2])

    # Sample off-diagonal elements for each row
    off_diag_per_row = []
    for i in range(n_voxels):
        row_off_diag = np.concatenate([A[i, :i], A[i, i+1:]])
        off_diag_per_row.append(np.abs(row_off_diag).mean())

    off_diag_per_row = np.array(off_diag_per_row)

    ax5.scatter(diag_elements, off_diag_per_row, alpha=0.4, s=20, color='teal', edgecolors='black', linewidth=0.3)
    ax5.set_xlabel('Diagonal Element (Self-Gain)', fontsize=10)
    ax5.set_ylabel('Mean |Off-Diagonal| per Row', fontsize=10)
    ax5.set_title('Diagonal Dominance\n(Diagonal vs Off-Diagonal Strength)', fontsize=10)
    ax5.grid(True, alpha=0.3)

    # Correlation
    corr = np.corrcoef(diag_elements, off_diag_per_row)[0, 1]
    ax5.text(0.05, 0.95, f'ρ = {corr:.3f}', transform=ax5.transAxes,
             fontsize=10, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    plt.suptitle(f'A Matrix Analysis: sub-{subject_id} {roi}',
                 fontsize=14, fontweight='bold')

    plt.tight_layout()

    # Save
    output_file = OUTPUT_DIR / f"A_matrix_analysis_sub{subject_id}_{roi}.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  Saved: {output_file}")
    plt.close()

    # Return statistics
    stats = {
        'subject': subject_id,
        'roi': roi,
        'n_voxels': n_voxels,
        'deviation_from_I': deviation,
        'relative_dev_pct': relative_dev,
        'diag_mean': diag_elements.mean(),
        'diag_std': diag_elements.std(),
        'off_diag_mean': off_diag_elements.mean(),
        'off_diag_std': off_diag_elements.std(),
        'sparsity_pct': (np.abs(off_diag_elements) < 0.05).sum() / len(off_diag_elements) * 100,
        'condition_number': condition_number,
        'eigenvalue_min': eigenvalues.min(),
        'eigenvalue_max': eigenvalues.max(),
    }

    return stats


def create_summary_figure(rdm_results, a_matrix_stats):
    """
    Create summary figure across all subjects and ROIs
    """
    print("\n[Summary Figure]")

    fig, axes = plt.subplots(2, 3, figsize=(18, 10))

    subjects_rois = [(s, r) for s in CVD_SUBJECTS for r in ROIS]
    labels = [f"sub-{s}\n{r}" for s, r in subjects_rois]
    x = np.arange(len(labels))

    # 1. RDM Correlation Improvement
    ax = axes[0, 0]
    before = [rdm_results[f"{s}_{r}"][0] for s, r in subjects_rois]
    after = [rdm_results[f"{s}_{r}"][1] for s, r in subjects_rois]

    width = 0.35
    ax.bar(x - width/2, before, width, label='Before', alpha=0.7, color='red', edgecolor='black')
    ax.bar(x + width/2, after, width, label='After', alpha=0.7, color='green', edgecolor='black')
    ax.axhline(1.0, color='black', linestyle='--', linewidth=1, alpha=0.5, label='Perfect (1.0)')
    ax.set_ylabel('RDM Correlation with HC', fontsize=10)
    ax.set_title('RDM Structure Improvement', fontsize=11, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3, axis='y')

    # 2. A Matrix Deviation from Identity
    ax = axes[0, 1]
    deviations = [a_matrix_stats[f"{s}_{r}"]['relative_dev_pct'] for s, r in subjects_rois]
    ax.bar(x, deviations, alpha=0.7, color='blue', edgecolor='black')
    ax.set_ylabel('||A - I||_F (%)', fontsize=10)
    ax.set_title('Transformation Magnitude', fontsize=11, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)
    ax.grid(True, alpha=0.3, axis='y')

    # 3. Diagonal Mean (Self-Gain)
    ax = axes[0, 2]
    diag_means = [a_matrix_stats[f"{s}_{r}"]['diag_mean'] for s, r in subjects_rois]
    ax.bar(x, diag_means, alpha=0.7, color='purple', edgecolor='black')
    ax.axhline(1.0, color='red', linestyle='--', linewidth=1, label='Identity (1.0)')
    ax.set_ylabel('Mean Diagonal Value', fontsize=10)
    ax.set_title('Average Self-Gain', fontsize=11, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3, axis='y')

    # 4. Off-Diagonal Sparsity
    ax = axes[1, 0]
    sparsity = [a_matrix_stats[f"{s}_{r}"]['sparsity_pct'] for s, r in subjects_rois]
    ax.bar(x, sparsity, alpha=0.7, color='orange', edgecolor='black')
    ax.set_ylabel('Sparsity (%)', fontsize=10)
    ax.set_title('Off-Diagonal Sparsity (|A[i,j]| < 0.05)', fontsize=11, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)
    ax.grid(True, alpha=0.3, axis='y')

    # 5. Condition Number
    ax = axes[1, 1]
    cond_nums = [a_matrix_stats[f"{s}_{r}"]['condition_number'] for s, r in subjects_rois]
    ax.bar(x, cond_nums, alpha=0.7, color='teal', edgecolor='black')
    ax.set_ylabel('Condition Number', fontsize=10)
    ax.set_title('Matrix Conditioning', fontsize=11, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)
    ax.grid(True, alpha=0.3, axis='y')

    # 6. RDM Improvement Percentage
    ax = axes[1, 2]
    improvements = [(after[i] - before[i]) / (1 - before[i]) * 100 if before[i] < 1 else 0
                    for i in range(len(before))]
    ax.bar(x, improvements, alpha=0.7, color='green', edgecolor='black')
    ax.set_ylabel('RDM Improvement (%)', fontsize=10)
    ax.set_title('Relative RDM Improvement', fontsize=11, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)
    ax.grid(True, alpha=0.3, axis='y')

    plt.suptitle('Phase 2A Filter Properties Summary\n(All Subjects and ROIs)',
                 fontsize=14, fontweight='bold')

    plt.tight_layout()

    # Save
    output_file = OUTPUT_DIR / "filter_properties_summary.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  Saved: {output_file}")
    plt.close()


def main():
    """Main execution"""
    print("=" * 70)
    print("Phase 2A Filter Properties Visualization")
    print("=" * 70)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    rdm_results = {}
    a_matrix_stats = {}

    for subject in CVD_SUBJECTS:
        for roi in ROIS:
            # RDM improvement
            corr_before, corr_after = visualize_rdm_improvement(subject, roi)
            rdm_results[f"{subject}_{roi}"] = (corr_before, corr_after)

            # A matrix analysis
            stats = visualize_A_matrix(subject, roi)
            a_matrix_stats[f"{subject}_{roi}"] = stats

    # Summary figure
    create_summary_figure(rdm_results, a_matrix_stats)

    print("\n" + "=" * 70)
    print("Visualization Complete!")
    print(f"Output directory: {OUTPUT_DIR}")
    print("=" * 70)


if __name__ == "__main__":
    main()
