"""
create_figure_compilations.py
-----------------------------
Create comprehensive compilations of each figure type
across methods, ROIs, and subjects

Generates:
- HRF_compilation.png: All HRF curves (method × ROI × subject)
- CircularColorSpace_compilation.png: All circular plots
- ConfusionMatrix_compilation.png: All confusion matrices
- ReconstructionPerRun_compilation.png: All per-run reconstructions

Date: 2025-11-17
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from pathlib import Path
from PIL import Image
import pandas as pd

# Configuration
BASE_DIR = Path("logs/20251117_combined_reorganized")
SUBJECTS = ["sub-01", "sub-02", "sub-03", "sub-04"]
ROIS = ["V1", "V2", "V3", "hV4"]
METHODS = ["zScore", "voxelSelect"]

# Subject groups
NON_CVD = ["sub-01", "sub-02"]
CVD = ["sub-03", "sub-04"]

def get_figure_path(method, roi, subject, figure_type):
    """Get path to a specific figure"""
    method_roi_dir = BASE_DIR / f"{method}_{roi}"
    fig_path = method_roi_dir / f"{subject}_{figure_type}.png"
    return fig_path if fig_path.exists() else None

def create_hrf_compilation():
    """
    Create comprehensive HRF compilation
    Layout: Methods (rows) × ROIs (columns), with subjects overlaid
    """
    print("\n" + "="*70)
    print("Creating HRF Compilation")
    print("="*70)

    n_methods = len(METHODS)
    n_rois = len(ROIS)

    fig = plt.figure(figsize=(24, 12))
    gs = GridSpec(n_methods, n_rois, figure=fig, hspace=0.3, wspace=0.3)

    for i, method in enumerate(METHODS):
        for j, roi in enumerate(ROIS):
            ax = fig.add_subplot(gs[i, j])

            # Count how many subjects have this figure
            n_found = 0

            for subject in SUBJECTS:
                fig_path = get_figure_path(method, roi, subject, "universal_hrf")

                if fig_path:
                    # Load and display image
                    img = Image.open(fig_path)

                    # Create semi-transparent overlay
                    alpha = 0.7 if n_found > 0 else 1.0

                    # For first image, show it
                    if n_found == 0:
                        ax.imshow(img, alpha=alpha)
                        ax.axis('off')

                    n_found += 1

                    # Add subject label
                    group = "NC" if subject in NON_CVD else "CVD"
                    color = 'blue' if group == "NC" else 'red'

                    label_y = 0.95 - (n_found - 1) * 0.08
                    ax.text(0.02, label_y, f"{subject} ({group})",
                           transform=ax.transAxes,
                           fontsize=8, fontweight='bold',
                           bbox=dict(boxstyle='round', facecolor=color, alpha=0.3),
                           verticalalignment='top')

            if n_found == 0:
                ax.text(0.5, 0.5, 'No data', transform=ax.transAxes,
                       ha='center', va='center', fontsize=12, color='gray')
                ax.axis('off')

            # Title
            title = f"{method} - {roi}\n(n={n_found})"
            ax.set_title(title, fontsize=12, fontweight='bold', pad=10)

    plt.suptitle('HRF Curves: All Methods × ROIs × Subjects',
                 fontsize=16, fontweight='bold', y=0.98)

    output_path = "HRF_compilation.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"✓ Saved: {output_path}")
    return output_path

def create_circular_compilation():
    """
    Create comprehensive circular color space compilation
    Layout: Subjects (rows) × Methods×ROIs (columns)
    """
    print("\n" + "="*70)
    print("Creating Circular Color Space Compilation")
    print("="*70)

    n_subjects = len(SUBJECTS)
    n_conditions = len(METHODS) * len(ROIS)

    # Create grid: subjects × (methods × ROIs)
    fig = plt.figure(figsize=(28, 18))
    gs = GridSpec(n_subjects, n_conditions, figure=fig,
                  hspace=0.25, wspace=0.15)

    col_idx = 0
    condition_labels = []

    for method in METHODS:
        for roi in ROIS:
            condition_labels.append(f"{method}\n{roi}")

            for row_idx, subject in enumerate(SUBJECTS):
                ax = fig.add_subplot(gs[row_idx, col_idx])

                fig_path = get_figure_path(method, roi, subject, "circular_color_space")

                if fig_path:
                    img = Image.open(fig_path)
                    ax.imshow(img)
                    ax.axis('off')

                    # Add subject label on first column
                    if col_idx == 0:
                        group = "Non-CVD" if subject in NON_CVD else "CVD"
                        color = 'blue' if group == "Non-CVD" else 'red'
                        ax.text(-0.1, 0.5, f"{subject}\n({group})",
                               transform=ax.transAxes,
                               fontsize=11, fontweight='bold',
                               ha='right', va='center',
                               bbox=dict(boxstyle='round', facecolor=color, alpha=0.2))
                else:
                    ax.text(0.5, 0.5, 'No data', transform=ax.transAxes,
                           ha='center', va='center', fontsize=10, color='gray')
                    ax.axis('off')

                # Column titles (only for first row)
                if row_idx == 0:
                    ax.set_title(condition_labels[col_idx],
                               fontsize=11, fontweight='bold', pad=10)

            col_idx += 1

    plt.suptitle('Circular Color Space: All Subjects × Methods × ROIs\n' +
                 '(Check color label positions)',
                 fontsize=16, fontweight='bold', y=0.995)

    output_path = "CircularColorSpace_compilation.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"✓ Saved: {output_path}")
    return output_path

def create_confusion_matrix_compilation():
    """
    Create comprehensive confusion matrix compilation
    Layout: Subjects (rows) × Methods×ROIs (columns)
    """
    print("\n" + "="*70)
    print("Creating Confusion Matrix Compilation")
    print("="*70)

    n_subjects = len(SUBJECTS)
    n_conditions = len(METHODS) * len(ROIS)

    fig = plt.figure(figsize=(28, 18))
    gs = GridSpec(n_subjects, n_conditions, figure=fig,
                  hspace=0.25, wspace=0.15)

    col_idx = 0
    condition_labels = []

    for method in METHODS:
        for roi in ROIS:
            condition_labels.append(f"{method}\n{roi}")

            for row_idx, subject in enumerate(SUBJECTS):
                ax = fig.add_subplot(gs[row_idx, col_idx])

                fig_path = get_figure_path(method, roi, subject, "confusion_matrix")

                if fig_path:
                    img = Image.open(fig_path)
                    ax.imshow(img)
                    ax.axis('off')

                    # Add subject label on first column
                    if col_idx == 0:
                        group = "Non-CVD" if subject in NON_CVD else "CVD"
                        color = 'blue' if group == "Non-CVD" else 'red'
                        ax.text(-0.1, 0.5, f"{subject}\n({group})",
                               transform=ax.transAxes,
                               fontsize=11, fontweight='bold',
                               ha='right', va='center',
                               bbox=dict(boxstyle='round', facecolor=color, alpha=0.2))
                else:
                    ax.text(0.5, 0.5, 'No data', transform=ax.transAxes,
                           ha='center', va='center', fontsize=10, color='gray')
                    ax.axis('off')

                # Column titles
                if row_idx == 0:
                    ax.set_title(condition_labels[col_idx],
                               fontsize=11, fontweight='bold', pad=10)

            col_idx += 1

    plt.suptitle('Classification Confusion Matrices: All Subjects × Methods × ROIs',
                 fontsize=16, fontweight='bold', y=0.995)

    output_path = "ConfusionMatrix_compilation.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"✓ Saved: {output_path}")
    return output_path

def create_reconstruction_compilation():
    """
    Create comprehensive reconstruction per run compilation
    Layout: Subjects (rows) × Methods×ROIs (columns)
    """
    print("\n" + "="*70)
    print("Creating Reconstruction Per Run Compilation")
    print("="*70)

    n_subjects = len(SUBJECTS)
    n_conditions = len(METHODS) * len(ROIS)

    fig = plt.figure(figsize=(28, 18))
    gs = GridSpec(n_subjects, n_conditions, figure=fig,
                  hspace=0.25, wspace=0.15)

    col_idx = 0
    condition_labels = []

    for method in METHODS:
        for roi in ROIS:
            condition_labels.append(f"{method}\n{roi}")

            for row_idx, subject in enumerate(SUBJECTS):
                ax = fig.add_subplot(gs[row_idx, col_idx])

                fig_path = get_figure_path(method, roi, subject, "reconstruction_per_run")

                if fig_path:
                    img = Image.open(fig_path)
                    ax.imshow(img)
                    ax.axis('off')

                    # Add subject label on first column
                    if col_idx == 0:
                        group = "Non-CVD" if subject in NON_CVD else "CVD"
                        color = 'blue' if group == "Non-CVD" else 'red'
                        ax.text(-0.1, 0.5, f"{subject}\n({group})",
                               transform=ax.transAxes,
                               fontsize=11, fontweight='bold',
                               ha='right', va='center',
                               bbox=dict(boxstyle='round', facecolor=color, alpha=0.2))
                else:
                    ax.text(0.5, 0.5, 'No data', transform=ax.transAxes,
                           ha='center', va='center', fontsize=10, color='gray')
                    ax.axis('off')

                # Column titles
                if row_idx == 0:
                    ax.set_title(condition_labels[col_idx],
                               fontsize=11, fontweight='bold', pad=10)

            col_idx += 1

    plt.suptitle('Reconstruction Per Run: All Subjects × Methods × ROIs',
                 fontsize=16, fontweight='bold', y=0.995)

    output_path = "ReconstructionPerRun_compilation.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"✓ Saved: {output_path}")
    return output_path

def create_summary_stats_table():
    """
    Create summary statistics table from all summary.csv files
    """
    print("\n" + "="*70)
    print("Creating Summary Statistics Table")
    print("="*70)

    all_data = []

    for method in METHODS:
        for roi in ROIS:
            method_roi_dir = BASE_DIR / f"{method}_{roi}"

            for subject in SUBJECTS:
                csv_path = method_roi_dir / f"{subject}_summary.csv"

                if csv_path.exists():
                    df = pd.read_csv(csv_path)
                    df['Subject'] = subject
                    df['Group'] = 'Non-CVD' if subject in NON_CVD else 'CVD'
                    all_data.append(df)

    combined = pd.concat(all_data, ignore_index=True)

    # Save combined table
    output_path = "AllResults_summary.csv"
    combined.to_csv(output_path, index=False)
    print(f"✓ Saved: {output_path}")

    # Create summary statistics figure
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # 1. Reconstruction error by method-ROI
    ax = axes[0, 0]
    pivot = combined.pivot_table(
        index='ROI',
        columns='Method',
        values='Reconstruction_error_deg',
        aggfunc='mean'
    )
    pivot.plot(kind='bar', ax=ax, width=0.8)
    ax.set_title('Average Reconstruction Error by ROI and Method',
                fontsize=12, fontweight='bold')
    ax.set_ylabel('Error (degrees)')
    ax.legend(title='Method')
    ax.grid(axis='y', alpha=0.3)

    # 2. Novel color error by method-ROI
    ax = axes[0, 1]
    pivot = combined.pivot_table(
        index='ROI',
        columns='Method',
        values='Novel_color_error_deg',
        aggfunc='mean'
    )
    pivot.plot(kind='bar', ax=ax, width=0.8)
    ax.set_title('Average Novel Color Error by ROI and Method',
                fontsize=12, fontweight='bold')
    ax.set_ylabel('Error (degrees)')
    ax.legend(title='Method')
    ax.grid(axis='y', alpha=0.3)

    # 3. Reconstruction error by group
    ax = axes[1, 0]
    pivot = combined.pivot_table(
        index='Group',
        columns=['Method', 'ROI'],
        values='Reconstruction_error_deg',
        aggfunc='mean'
    )
    pivot.T.plot(kind='bar', ax=ax, width=0.8)
    ax.set_title('Reconstruction Error: Non-CVD vs CVD',
                fontsize=12, fontweight='bold')
    ax.set_ylabel('Error (degrees)')
    ax.set_xlabel('Method - ROI')
    ax.legend(title='Group')
    ax.grid(axis='y', alpha=0.3)
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

    # 4. N_voxels by method-ROI
    ax = axes[1, 1]
    pivot = combined.pivot_table(
        index='ROI',
        columns='Method',
        values='N_voxels',
        aggfunc='mean'
    )
    pivot.plot(kind='bar', ax=ax, width=0.8)
    ax.set_title('Average Number of Voxels by ROI and Method',
                fontsize=12, fontweight='bold')
    ax.set_ylabel('N voxels')
    ax.set_yscale('log')
    ax.legend(title='Method')
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()

    output_path = "SummaryStatistics_compilation.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"✓ Saved: {output_path}")

    return combined

def main():
    """Main compilation function"""

    print("\n" + "="*70)
    print("CREATING FIGURE COMPILATIONS")
    print("="*70)
    print(f"Base directory: {BASE_DIR}")
    print(f"Subjects: {SUBJECTS}")
    print(f"ROIs: {ROIS}")
    print(f"Methods: {METHODS}")
    print()

    # Check base directory exists
    if not BASE_DIR.exists():
        print(f"ERROR: Base directory not found: {BASE_DIR}")
        return

    # Create compilations
    outputs = []

    # 1. HRF compilation
    outputs.append(create_hrf_compilation())

    # 2. Circular color space compilation
    outputs.append(create_circular_compilation())

    # 3. Confusion matrix compilation
    outputs.append(create_confusion_matrix_compilation())

    # 4. Reconstruction per run compilation
    outputs.append(create_reconstruction_compilation())

    # 5. Summary statistics
    df = create_summary_stats_table()

    # Summary
    print("\n" + "="*70)
    print("COMPILATION COMPLETE")
    print("="*70)
    print("\nGenerated files:")
    for output in outputs:
        print(f"  ✓ {output}")
    print(f"  ✓ AllResults_summary.csv")
    print(f"  ✓ SummaryStatistics_compilation.png")

    print("\n" + "="*70)
    print("NOTES ON COLOR LABELS")
    print("="*70)
    print("""
Current analysis uses LABEL2HUE_DEG_PILOT which contains the ACTUAL
measured Lab hue angles from the pilot data:

  color_1: 182.14° (measured)
  color_2: 287.98° (measured)
  color_3: 305.23° (measured)
  color_4: 330.20° (measured)
  color_5: 35.27°  (measured)
  color_6: 73.37°  (measured)
  color_7: 125.59° (measured)
  color_8: 143.91° (measured)

These differ from the DESIGNED values (45° spacing):
  color_1: 0°   (designed)
  color_2: 45°  (designed)
  color_3: 90°  (designed)
  etc.

The circular color space plots should show the MEASURED positions.
Please verify the color labels in CircularColorSpace_compilation.png
match the actual stimulus colors.
    """)

if __name__ == "__main__":
    main()
