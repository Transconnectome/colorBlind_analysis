#!/usr/bin/env python3
"""
Compact RDM Improvement Visualization

V1: sub-08, 09, 10 Before/After comparison
V2: sub-08, 09, 10 Before/After comparison

Better colormap for RDM dissimilarity visualization
"""

import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy.stats import spearmanr

# Configuration
BASE_DIR = Path("/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis")
PATTERN_DIR = BASE_DIR / "results/group_level/phase2a_data/patterns"
MODEL_DIR = BASE_DIR / "results/filters/models/optionD/20251219_122240"
OUTPUT_DIR = BASE_DIR / "results/filters/analysis/filter_properties"

CVD_SUBJECTS = ['08', '09', '10']
COLOR_NAMES = ['Red', 'Orange', 'Yellow', 'Chartreuse',
               'Green', 'Cyan', 'Blue', 'Magenta']

# Better colormap for RDM (dissimilarity: 0=similar, high=different)
# viridis: better for perceptual uniformity and colorblind-friendly
COLORMAP = 'viridis'  # Dark purple (low) to yellow (high)


def compute_rdm(pattern):
    """Compute Representational Dissimilarity Matrix"""
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


def visualize_rdm_by_roi(roi):
    """
    Create compact RDM visualization for one ROI
    Shows all 3 subjects in before/after columns
    """
    print(f"\n[Compact RDM] {roi}")

    # Create figure
    fig = plt.figure(figsize=(16, 12))
    gs = gridspec.GridSpec(3, 3, width_ratios=[1, 1, 0.3], hspace=0.3, wspace=0.3)

    # Collect data for all subjects
    rdm_data = {}
    correlations = {}

    for subject_id in CVD_SUBJECTS:
        # Load patterns
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
        rdm_before = compute_rdm(cvd_pattern)
        rdm_after = compute_rdm(filtered_pattern)

        # Compute correlations
        corr_before, _ = spearmanr(rdm_before.flatten(), rdm_hc.flatten())
        corr_after, _ = spearmanr(rdm_after.flatten(), rdm_hc.flatten())

        rdm_data[subject_id] = {
            'before': rdm_before,
            'after': rdm_after,
            'hc': rdm_hc
        }
        correlations[subject_id] = {
            'before': corr_before,
            'after': corr_after
        }

    # Global colorbar limits (across all RDMs)
    all_rdms = []
    for subj_data in rdm_data.values():
        all_rdms.extend([subj_data['before'], subj_data['after'], subj_data['hc']])
    vmin = 0.0
    vmax = max([rdm.max() for rdm in all_rdms])

    # Plot each subject
    for idx, subject_id in enumerate(CVD_SUBJECTS):
        data = rdm_data[subject_id]
        corrs = correlations[subject_id]

        # Before
        ax_before = plt.subplot(gs[idx, 0])
        im = ax_before.imshow(data['before'], cmap=COLORMAP, vmin=vmin, vmax=vmax)
        ax_before.set_title(f'sub-{subject_id} Before\nρ(HC) = {corrs["before"]:.3f}',
                           fontsize=11, fontweight='bold')
        ax_before.set_xticks(range(8))
        ax_before.set_yticks(range(8))
        ax_before.set_xticklabels(COLOR_NAMES, rotation=45, ha='right', fontsize=9)
        ax_before.set_yticklabels(COLOR_NAMES, fontsize=9)

        # After
        ax_after = plt.subplot(gs[idx, 1])
        im = ax_after.imshow(data['after'], cmap=COLORMAP, vmin=vmin, vmax=vmax)
        ax_after.set_title(f'sub-{subject_id} After\nρ(HC) = {corrs["after"]:.3f}',
                          fontsize=11, fontweight='bold')
        ax_after.set_xticks(range(8))
        ax_after.set_yticks(range(8))
        ax_after.set_xticklabels(COLOR_NAMES, rotation=45, ha='right', fontsize=9)
        ax_after.set_yticklabels(COLOR_NAMES, fontsize=9)

        # Improvement text
        improvement = corrs['after'] - corrs['before']
        improvement_pct = (improvement / (1 - corrs['before'])) * 100 if corrs['before'] < 1 else 0

        ax_text = plt.subplot(gs[idx, 2])
        ax_text.axis('off')
        text = f"Improvement:\n\n"
        text += f"Δρ = {improvement:+.3f}\n\n"
        text += f"({improvement_pct:+.1f}%)\n\n"

        if improvement > 0:
            text += "✓ Improved"
            color = 'green'
        else:
            text += "✗ Degraded"
            color = 'red'

        ax_text.text(0.1, 0.5, text, fontsize=12, verticalalignment='center',
                    fontweight='bold', color=color,
                    bbox=dict(boxstyle='round', facecolor='white', edgecolor=color, linewidth=2))

    # Add colorbar (positioned to avoid overlap)
    cbar_ax = fig.add_axes([0.72, 0.15, 0.02, 0.7])
    cbar = plt.colorbar(im, cax=cbar_ax)
    cbar.set_label('Dissimilarity\n(1 - ρ_Spearman)', fontsize=10, fontweight='bold')

    # Overall title
    plt.suptitle(f'RDM Improvement Analysis: {roi}\nAll CVD Subjects (Before vs After Filtering)',
                 fontsize=14, fontweight='bold', y=0.98)

    # Add note about interpretation
    note_text = (f'Note: RDM values (color intensity) represent dissimilarity between color pairs (high = different colors).\n'
                 f'RDM correlation ρ(HC) measures structural similarity (ρ → 1.0 = structure matches HC perfectly).\n'
                 f'High RDM correlation with high RDM values is correct: colors are different, and this pattern matches HC.')
    fig.text(0.5, 0.01, note_text,
             ha='center', fontsize=9, style='italic',
             bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

    # Save
    output_file = OUTPUT_DIR / f"rdm_improvement_compact_{roi}.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  Saved: {output_file}")
    plt.close()

    # Print summary
    print(f"\n  Summary for {roi}:")
    for subject_id in CVD_SUBJECTS:
        corrs = correlations[subject_id]
        improvement = corrs['after'] - corrs['before']
        print(f"    sub-{subject_id}: {corrs['before']:.3f} → {corrs['after']:.3f} (Δ = {improvement:+.3f})")


def main():
    """Main execution"""
    print("=" * 70)
    print("Compact RDM Improvement Visualization")
    print("=" * 70)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for roi in ['V1', 'V2']:
        visualize_rdm_by_roi(roi)

    print("\n" + "=" * 70)
    print("Visualization Complete!")
    print(f"Output: {OUTPUT_DIR}")
    print("  - rdm_improvement_compact_V1.png")
    print("  - rdm_improvement_compact_V2.png")
    print("=" * 70)


if __name__ == "__main__":
    main()
