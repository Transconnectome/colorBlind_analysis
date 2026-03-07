#!/usr/bin/env python3
"""
RDM Difference Visualization: CVD - HC

Shows how filtering reduces the difference between CVD and HC RDMs
- Black (0): No difference (perfect match)
- Blue (negative): CVD dissimilarity lower than HC
- Red (positive): CVD dissimilarity higher than HC

Goal: After filtering, all colors converge to black (difference → 0)
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

# Diverging colormap: Blue (negative) - White (0) - Red (positive)
COLORMAP = 'RdBu_r'


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


def visualize_rdm_difference_by_roi(roi):
    """
    Create RDM difference visualization for one ROI
    Shows CVD - HC for all 3 subjects in before/after columns
    """
    print(f"\n[RDM Difference] {roi}")

    # Create figure
    fig = plt.figure(figsize=(14, 12))
    gs = gridspec.GridSpec(3, 2, hspace=0.4, wspace=0.3)

    # Collect data for all subjects
    diff_data = {}
    correlations = {}
    rmse_values = {}

    # First, load HC pattern (same for all subjects)
    hc_pattern = np.load(PATTERN_DIR / "HC_mean" / f"{roi}_pattern.npy")

    for subject_id in CVD_SUBJECTS:
        # Load CVD pattern
        cvd_pattern = np.load(PATTERN_DIR / f"sub-{subject_id}" / f"{roi}_pattern.npy")

        # Voxel alignment
        n_voxels = min(hc_pattern.shape[1], cvd_pattern.shape[1])
        hc_aligned = hc_pattern[:, :n_voxels]
        cvd_aligned = cvd_pattern[:, :n_voxels]

        # Load filter
        A = np.load(MODEL_DIR / f"sub-{subject_id}" / roi / "A_matrix.npy")
        b = np.load(MODEL_DIR / f"sub-{subject_id}" / roi / "b_vector.npy")

        # Apply filter
        filtered_pattern = cvd_aligned @ A + b[np.newaxis, :]

        # Compute RDMs
        rdm_hc = compute_rdm(hc_aligned)
        rdm_before = compute_rdm(cvd_aligned)
        rdm_after = compute_rdm(filtered_pattern)

        # Compute differences
        diff_before = rdm_before - rdm_hc
        diff_after = rdm_after - rdm_hc

        # Compute correlations
        corr_before, _ = spearmanr(rdm_before.flatten(), rdm_hc.flatten())
        corr_after, _ = spearmanr(rdm_after.flatten(), rdm_hc.flatten())

        # Compute RMSE (off-diagonal only)
        mask = ~np.eye(8, dtype=bool)
        rmse_before = np.sqrt(np.mean(diff_before[mask]**2))
        rmse_after = np.sqrt(np.mean(diff_after[mask]**2))

        diff_data[subject_id] = {
            'before': diff_before,
            'after': diff_after
        }
        correlations[subject_id] = {
            'before': corr_before,
            'after': corr_after
        }
        rmse_values[subject_id] = {
            'before': rmse_before,
            'after': rmse_after
        }

    # Global colorbar limits (symmetric around 0)
    all_diffs = []
    for subj_data in diff_data.values():
        all_diffs.extend([subj_data['before'], subj_data['after']])
    max_abs = max([np.abs(diff).max() for diff in all_diffs])
    vmin = -max_abs
    vmax = max_abs

    # Plot each subject
    for idx, subject_id in enumerate(CVD_SUBJECTS):
        data = diff_data[subject_id]
        corrs = correlations[subject_id]
        rmse = rmse_values[subject_id]

        # Before
        ax_before = plt.subplot(gs[idx, 0])
        im = ax_before.imshow(data['before'], cmap=COLORMAP, vmin=vmin, vmax=vmax)
        ax_before.set_title(f'sub-{subject_id} Before\nRMSE = {rmse["before"]:.3f}, ρ = {corrs["before"]:.3f}',
                           fontsize=11, fontweight='bold')
        ax_before.set_xticks(range(8))
        ax_before.set_yticks(range(8))
        ax_before.set_xticklabels(COLOR_NAMES, rotation=45, ha='right', fontsize=9)
        ax_before.set_yticklabels(COLOR_NAMES, fontsize=9)

        # After
        ax_after = plt.subplot(gs[idx, 1])
        im = ax_after.imshow(data['after'], cmap=COLORMAP, vmin=vmin, vmax=vmax)
        ax_after.set_title(f'sub-{subject_id} After\nRMSE = {rmse["after"]:.3f}, ρ = {corrs["after"]:.3f}',
                          fontsize=11, fontweight='bold')
        ax_after.set_xticks(range(8))
        ax_after.set_yticks(range(8))
        ax_after.set_xticklabels(COLOR_NAMES, rotation=45, ha='right', fontsize=9)
        ax_after.set_yticklabels(COLOR_NAMES, fontsize=9)


    # Add colorbar (positioned to avoid overlap with heatmaps)
    cbar_ax = fig.add_axes([0.95, 0.15, 0.02, 0.7])
    cbar = plt.colorbar(im, cax=cbar_ax)
    cbar.set_label('RDM Difference\n(CVD - HC)', fontsize=11, fontweight='bold', rotation=270, labelpad=20)

    # Add reference markers on colorbar
    cbar.ax.axhline(0, color='black', linewidth=2, linestyle='--')

    # Overall title
    plt.suptitle(f'RDM Difference from HC: {roi}\n'
                 f'Filter Convergence: CVD → HC (Difference → 0)',
                 fontsize=14, fontweight='bold', y=0.96)

    # Save
    output_file = OUTPUT_DIR / f"rdm_difference_{roi}.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  Saved: {output_file}")
    plt.close()

    # Print summary
    print(f"\n  Summary for {roi}:")
    for subject_id in CVD_SUBJECTS:
        rmse = rmse_values[subject_id]
        rmse_reduction = (rmse['before'] - rmse['after']) / rmse['before'] * 100
        print(f"    sub-{subject_id}: RMSE {rmse['before']:.3f} → {rmse['after']:.3f} "
              f"({rmse_reduction:.1f}% reduction)")


def visualize_rdm_difference_combined():
    """
    Create combined RDM difference visualization for V1 and V2
    Layout: 3 rows (subjects) × 4 columns (V1 Before, V1 After, V2 Before, V2 After)
    """
    print(f"\n[RDM Difference] Combined V1 + V2")

    # Create figure with more columns
    fig = plt.figure(figsize=(18, 12))
    gs = gridspec.GridSpec(3, 4, hspace=0.35, wspace=0.3)

    # Collect data for all subjects and ROIs
    all_data = {}

    for roi in ['V1', 'V2']:
        diff_data = {}
        correlations = {}
        rmse_values = {}

        # Load HC pattern
        hc_pattern = np.load(PATTERN_DIR / "HC_mean" / f"{roi}_pattern.npy")

        for subject_id in CVD_SUBJECTS:
            # Load CVD pattern
            cvd_pattern = np.load(PATTERN_DIR / f"sub-{subject_id}" / f"{roi}_pattern.npy")

            # Voxel alignment
            n_voxels = min(hc_pattern.shape[1], cvd_pattern.shape[1])
            hc_aligned = hc_pattern[:, :n_voxels]
            cvd_aligned = cvd_pattern[:, :n_voxels]

            # Load filter
            A = np.load(MODEL_DIR / f"sub-{subject_id}" / roi / "A_matrix.npy")
            b = np.load(MODEL_DIR / f"sub-{subject_id}" / roi / "b_vector.npy")

            # Apply filter
            filtered_pattern = cvd_aligned @ A + b[np.newaxis, :]

            # Compute RDMs
            rdm_hc = compute_rdm(hc_aligned)
            rdm_before = compute_rdm(cvd_aligned)
            rdm_after = compute_rdm(filtered_pattern)

            # Compute differences
            diff_before = rdm_before - rdm_hc
            diff_after = rdm_after - rdm_hc

            # Compute correlations
            corr_before, _ = spearmanr(rdm_before.flatten(), rdm_hc.flatten())
            corr_after, _ = spearmanr(rdm_after.flatten(), rdm_hc.flatten())

            # Compute RMSE (off-diagonal only)
            mask = ~np.eye(8, dtype=bool)
            rmse_before = np.sqrt(np.mean(diff_before[mask]**2))
            rmse_after = np.sqrt(np.mean(diff_after[mask]**2))

            diff_data[subject_id] = {
                'before': diff_before,
                'after': diff_after
            }
            correlations[subject_id] = {
                'before': corr_before,
                'after': corr_after
            }
            rmse_values[subject_id] = {
                'before': rmse_before,
                'after': rmse_after
            }

        all_data[roi] = {
            'diff_data': diff_data,
            'correlations': correlations,
            'rmse_values': rmse_values
        }

    # Global colorbar limits (symmetric around 0)
    all_diffs = []
    for roi_data in all_data.values():
        for subj_data in roi_data['diff_data'].values():
            all_diffs.extend([subj_data['before'], subj_data['after']])
    max_abs = max([np.abs(diff).max() for diff in all_diffs])
    vmin = -max_abs
    vmax = max_abs

    # Plot each subject (rows) × each ROI/condition (columns)
    for idx, subject_id in enumerate(CVD_SUBJECTS):
        # V1 Before (column 0)
        ax = plt.subplot(gs[idx, 0])
        data = all_data['V1']['diff_data'][subject_id]['before']
        rmse = all_data['V1']['rmse_values'][subject_id]['before']
        corr = all_data['V1']['correlations'][subject_id]['before']
        im = ax.imshow(data, cmap=COLORMAP, vmin=vmin, vmax=vmax)
        ax.set_title(f'V1 Before\nRMSE={rmse:.3f}, ρ={corr:.3f}',
                    fontsize=10, fontweight='bold')
        ax.set_xticks(range(8))
        ax.set_yticks(range(8))
        if idx == 2:  # Bottom row
            ax.set_xticklabels(COLOR_NAMES, rotation=45, ha='right', fontsize=8)
        else:
            ax.set_xticklabels([])
        ax.set_yticklabels(COLOR_NAMES, fontsize=8)
        # Add subject label on left
        if idx == 0:
            ax.text(-0.2, 0.5, f'sub-{subject_id}', transform=ax.transAxes,
                   fontsize=12, fontweight='bold', rotation=90, va='center')

        # V1 After (column 1)
        ax = plt.subplot(gs[idx, 1])
        data = all_data['V1']['diff_data'][subject_id]['after']
        rmse = all_data['V1']['rmse_values'][subject_id]['after']
        corr = all_data['V1']['correlations'][subject_id]['after']
        im = ax.imshow(data, cmap=COLORMAP, vmin=vmin, vmax=vmax)
        ax.set_title(f'V1 After\nRMSE={rmse:.3f}, ρ={corr:.3f}',
                    fontsize=10, fontweight='bold')
        ax.set_xticks(range(8))
        ax.set_yticks([])
        if idx == 2:
            ax.set_xticklabels(COLOR_NAMES, rotation=45, ha='right', fontsize=8)
        else:
            ax.set_xticklabels([])

        # V2 Before (column 2)
        ax = plt.subplot(gs[idx, 2])
        data = all_data['V2']['diff_data'][subject_id]['before']
        rmse = all_data['V2']['rmse_values'][subject_id]['before']
        corr = all_data['V2']['correlations'][subject_id]['before']
        im = ax.imshow(data, cmap=COLORMAP, vmin=vmin, vmax=vmax)
        ax.set_title(f'V2 Before\nRMSE={rmse:.3f}, ρ={corr:.3f}',
                    fontsize=10, fontweight='bold')
        ax.set_xticks(range(8))
        ax.set_yticks([])
        if idx == 2:
            ax.set_xticklabels(COLOR_NAMES, rotation=45, ha='right', fontsize=8)
        else:
            ax.set_xticklabels([])

        # V2 After (column 3)
        ax = plt.subplot(gs[idx, 3])
        data = all_data['V2']['diff_data'][subject_id]['after']
        rmse = all_data['V2']['rmse_values'][subject_id]['after']
        corr = all_data['V2']['correlations'][subject_id]['after']
        im = ax.imshow(data, cmap=COLORMAP, vmin=vmin, vmax=vmax)
        ax.set_title(f'V2 After\nRMSE={rmse:.3f}, ρ={corr:.3f}',
                    fontsize=10, fontweight='bold')
        ax.set_xticks(range(8))
        ax.set_yticks([])
        if idx == 2:
            ax.set_xticklabels(COLOR_NAMES, rotation=45, ha='right', fontsize=8)
        else:
            ax.set_xticklabels([])

    # Add subject labels on left side
    for idx, subject_id in enumerate(CVD_SUBJECTS):
        fig.text(0.02, 0.82 - idx * 0.295, f'sub-{subject_id}',
                fontsize=14, fontweight='bold', rotation=90, va='center')

    # Add colorbar
    cbar_ax = fig.add_axes([0.92, 0.15, 0.015, 0.7])
    cbar = plt.colorbar(im, cax=cbar_ax)
    cbar.set_label('RDM Difference\n(CVD - HC)', fontsize=11, fontweight='bold',
                  rotation=270, labelpad=20)
    cbar.ax.axhline(0, color='black', linewidth=2, linestyle='--')

    # Overall title
    plt.suptitle('RDM Difference from HC: V1 & V2\n'
                 'Filter Convergence: CVD → HC (Difference → 0)',
                 fontsize=16, fontweight='bold', y=0.98)

    # Save
    output_file = OUTPUT_DIR / "rdm_difference_combined.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  Saved: {output_file}")
    plt.close()

    # Print summary
    print(f"\n  Summary:")
    for roi in ['V1', 'V2']:
        print(f"\n  {roi}:")
        for subject_id in CVD_SUBJECTS:
            rmse = all_data[roi]['rmse_values'][subject_id]
            rmse_reduction = (rmse['before'] - rmse['after']) / rmse['before'] * 100
            print(f"    sub-{subject_id}: RMSE {rmse['before']:.3f} → {rmse['after']:.3f} "
                  f"({rmse_reduction:.1f}% reduction)")


def main():
    """Main execution"""
    print("=" * 70)
    print("RDM Difference Visualization (CVD - HC)")
    print("=" * 70)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Create combined figure
    visualize_rdm_difference_combined()

    print("\n" + "=" * 70)
    print("Visualization Complete!")
    print(f"Output: {OUTPUT_DIR}")
    print("  - rdm_difference_combined.png")
    print("=" * 70)


if __name__ == "__main__":
    main()
