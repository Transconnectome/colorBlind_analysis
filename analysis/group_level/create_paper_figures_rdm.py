#!/usr/bin/env python3
"""
create_paper_figures_rdm.py
===========================

논문용 Figure 5 & 6 생성
- Figure 5: RDM heatmaps (HC mean + 3 CVD × V1/V2)
- Figure 6: RDM difference heatmaps (CVD - HC)
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from pathlib import Path

matplotlib.use('Agg')

# Color names (8 colors from Brouwer & Heeger 2009)
COLOR_NAMES = ['Red', 'Orange', 'Yellow', 'Chartreuse',
               'Green', 'Cyan', 'Blue', 'Magenta']

# ============================================================================
# Data Loading
# ============================================================================

def load_rdm_data(base_dir='results/group_level/phase2a_data/rdm/matrices'):
    """Load RDM data for HC mean and CVD subjects"""
    base_path = Path(base_dir)

    data = {}

    # HC mean
    data['HC_mean'] = {}
    for roi in ['V1', 'V2']:
        rdm_file = base_path / 'HC_mean' / f'{roi}_rdm.npy'
        if rdm_file.exists():
            data['HC_mean'][roi] = np.load(rdm_file)
            print(f"Loaded HC_mean {roi}: {data['HC_mean'][roi].shape}")

    # CVD subjects
    for subject in ['08', '09', '10']:
        data[f'sub-{subject}'] = {}
        for roi in ['V1', 'V2']:
            rdm_file = base_path / f'sub-{subject}' / f'{roi}_rdm.npy'
            if rdm_file.exists():
                data[f'sub-{subject}'][roi] = np.load(rdm_file)
                print(f"Loaded sub-{subject} {roi}: {data[f'sub-{subject}'][roi].shape}")

    return data

# ============================================================================
# Figure 5: RDM Heatmaps
# ============================================================================

def create_figure5_rdm_heatmaps(data, output_dir='results/group_level'):
    """
    Figure 5: RDM heatmaps
    4 rows × 2 columns: (HC mean + 3 CVD) × (V1, V2)
    """
    print("Creating Figure 5: RDM Heatmaps...")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 4 rows (HC + 3 CVD) × 2 columns (V1, V2)
    fig, axes = plt.subplots(4, 2, figsize=(12, 18))

    subjects = ['HC_mean', 'sub-08', 'sub-09', 'sub-10']
    subject_labels = ['HC Mean', 'Sub-08\n(Deuteranopia)',
                      'Sub-09\n(Deuteranopia)', 'Sub-10\n(Protanomaly)']
    rois = ['V1', 'V2']

    for row, (subject, label) in enumerate(zip(subjects, subject_labels)):
        for col, roi in enumerate(rois):
            ax = axes[row, col]

            if subject in data and roi in data[subject]:
                rdm = data[subject][roi]

                # Plot heatmap
                im = ax.imshow(rdm, cmap='YlOrRd', vmin=0, vmax=2.0)

                # Title
                if row == 0:
                    ax.set_title(f'{roi}', fontsize=20, fontweight='bold', pad=10)

                # Y-axis label (subject info)
                if col == 0:
                    ax.set_ylabel(label, fontsize=16, fontweight='bold')

                # Tick labels
                if row == 3:  # Bottom row
                    ax.set_xticks(range(8))
                    ax.set_xticklabels(COLOR_NAMES, rotation=45, ha='right', fontsize=12)
                else:
                    ax.set_xticks([])

                if col == 0:  # Left column
                    ax.set_yticks(range(8))
                    ax.set_yticklabels(COLOR_NAMES, fontsize=12)
                else:
                    ax.set_yticks([])

                # Colorbar (only for rightmost column)
                if col == 1:
                    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
                    cbar.set_label('Dissimilarity', fontsize=12, rotation=270, labelpad=20)
                    cbar.ax.tick_params(labelsize=10)
            else:
                ax.axis('off')
                ax.text(0.5, 0.5, 'Data not available',
                       ha='center', va='center', fontsize=14)

    plt.suptitle('Figure 5: Representational Dissimilarity Matrices (RDMs)',
                 fontsize=22, fontweight='bold', y=0.995)
    plt.tight_layout(rect=[0, 0, 1, 0.99])

    # Save
    output_file = output_dir / 'Figure5_RDM_heatmaps.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()

# ============================================================================
# Figure 6: RDM Difference Heatmaps
# ============================================================================

def create_figure6_rdm_differences(data, output_dir='results/group_level'):
    """
    Figure 6: RDM difference heatmaps (CVD - HC)
    3 rows (CVD subjects) × 2 columns (V1, V2)
    """
    print("Creating Figure 6: RDM Difference Heatmaps...")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 3 rows (CVD) × 2 columns (V1, V2)
    fig, axes = plt.subplots(3, 2, figsize=(12, 14))

    cvd_subjects = ['sub-08', 'sub-09', 'sub-10']
    cvd_labels = ['Sub-08 (Deuteranopia)',
                  'Sub-09 (Deuteranopia)',
                  'Sub-10 (Protanomaly)']
    rois = ['V1', 'V2']

    # Determine global vmin/vmax for consistent colormap
    all_diffs = []
    for subject in cvd_subjects:
        for roi in rois:
            if subject in data and roi in data[subject]:
                diff = data[subject][roi] - data['HC_mean'][roi]
                all_diffs.append(np.abs(diff).max())

    vmax = max(all_diffs) if all_diffs else 0.5
    vmin = -vmax

    for row, (subject, label) in enumerate(zip(cvd_subjects, cvd_labels)):
        for col, roi in enumerate(rois):
            ax = axes[row, col]

            if subject in data and roi in data[subject]:
                # Compute difference: CVD - HC
                rdm_cvd = data[subject][roi]
                rdm_hc = data['HC_mean'][roi]
                diff = rdm_cvd - rdm_hc

                # Plot difference heatmap (diverging colormap)
                im = ax.imshow(diff, cmap='RdBu_r', vmin=vmin, vmax=vmax)

                # Title
                if row == 0:
                    ax.set_title(f'{roi}', fontsize=20, fontweight='bold', pad=10)

                # Y-axis label (subject info)
                if col == 0:
                    ax.set_ylabel(label, fontsize=14, fontweight='bold')

                # Tick labels
                if row == 2:  # Bottom row
                    ax.set_xticks(range(8))
                    ax.set_xticklabels(COLOR_NAMES, rotation=45, ha='right', fontsize=12)
                else:
                    ax.set_xticks([])

                if col == 0:  # Left column
                    ax.set_yticks(range(8))
                    ax.set_yticklabels(COLOR_NAMES, fontsize=12)
                else:
                    ax.set_yticks([])

                # Colorbar (only for rightmost column)
                if col == 1:
                    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
                    cbar.set_label('Difference (CVD - HC)', fontsize=12,
                                 rotation=270, labelpad=20)
                    cbar.ax.tick_params(labelsize=10)
            else:
                ax.axis('off')
                ax.text(0.5, 0.5, 'Data not available',
                       ha='center', va='center', fontsize=14)

    plt.suptitle('Figure 6: RDM Differences (CVD - HC)\nRed: Increased Dissimilarity, Blue: Decreased Dissimilarity',
                 fontsize=20, fontweight='bold', y=0.995)
    plt.tight_layout(rect=[0, 0, 1, 0.99])

    # Save
    output_file = output_dir / 'Figure6_RDM_differences.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()

# ============================================================================
# Main
# ============================================================================

def main():
    """Main function"""
    print("=" * 80)
    print("Creating Paper Figures: RDM Analysis")
    print("=" * 80)

    # Load data
    data = load_rdm_data()

    # Create figures
    create_figure5_rdm_heatmaps(data)
    create_figure6_rdm_differences(data)

    print("\n" + "=" * 80)
    print("✓ All figures created successfully!")
    print("=" * 80)

if __name__ == '__main__':
    main()
