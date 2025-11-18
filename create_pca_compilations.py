#!/usr/bin/env python3
"""
Create compilation images for PCA-related figures
- pca_components_matrix.png (zscore and voxelSelect versions)
- pca_colorspace.png (zscore and voxelSelect versions)
"""

import os
import matplotlib.pyplot as plt
from matplotlib.image import imread
from pathlib import Path
import numpy as np

# Configuration
BASE_DIR = Path("logs_1117")
OUTPUT_DIR = Path("logs_1117/pca_compilations")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Methods and directories
METHOD_DIRS = {
    'zScore': '20251118_010419_zscore',
    'voxelSelect': '20251118_012145_zSelect'
}

ROIS = ['V1', 'V2', 'V3', 'hV4']
SUBJECTS = ['sub-01', 'sub-02', 'sub-03', 'sub-04']

# Figure types to compile
FIGURE_TYPES = {
    'pca_components_matrix': 'PCA Components Matrix',
    'pca_colorspace': 'PCA Color Space'
}


def find_figures(method, roi, figure_type):
    """Find all figures of a given type for a method-ROI combination."""
    method_dir = BASE_DIR / METHOD_DIRS[method]
    if not method_dir.exists():
        return []

    figures = []
    for subject in SUBJECTS:
        # Path structure differs by method
        if method == 'zScore':
            # zScore: {method_dir}/{subject}/{ROI}_universal_hrf/figures/{ROI}_{figure_type}.png
            fig_path = method_dir / subject / f"{roi}_universal_hrf" / "figures" / f"{roi}_{figure_type}.png"
        else:
            # voxelSelect: {method_dir}/{subject}/fir_reconstruction_uni_hrf/voxelSelect/{ROI}_universal_hrf/figures/{ROI}_{figure_type}.png
            fig_path = method_dir / subject / "fir_reconstruction_uni_hrf" / "voxelSelect" / f"{roi}_universal_hrf" / "figures" / f"{roi}_{figure_type}.png"

        if fig_path.exists():
            figures.append((subject, fig_path))

    return figures


def create_compilation(method, figure_type):
    """Create a compilation image for a given method and figure type."""
    print(f"\nCreating compilation for {method} - {figure_type}")

    # Collect all figures
    all_figures = {}
    for roi in ROIS:
        figures = find_figures(method, roi, figure_type)
        if figures:
            all_figures[roi] = figures

    if not all_figures:
        print(f"  No figures found for {method} - {figure_type}")
        return

    # Calculate grid layout
    n_rois = len(all_figures)
    n_subjects = max(len(figs) for figs in all_figures.values())

    # Create figure with subplots (ROIs × Subjects)
    fig = plt.figure(figsize=(6 * n_subjects, 6 * n_rois))
    fig.suptitle(f"{FIGURE_TYPES[figure_type]} - {method}",
                 fontsize=20, fontweight='bold', y=0.995)

    # Plot each ROI's figures
    for roi_idx, roi in enumerate(ROIS):
        # Create subject-to-figure mapping for this ROI
        subject_fig_map = {}
        if roi in all_figures:
            for subject, fig_path in all_figures[roi]:
                subject_fig_map[subject] = fig_path

        # Plot for each subject slot
        for sub_idx, subject in enumerate(SUBJECTS):
            plot_idx = roi_idx * n_subjects + sub_idx + 1
            ax = plt.subplot(n_rois, n_subjects, plot_idx)

            if subject in subject_fig_map:
                fig_path = subject_fig_map[subject]
                try:
                    img = imread(fig_path)
                    ax.imshow(img)
                    ax.axis('off')

                    # Add title with ROI and Subject
                    title = f"{roi} - {subject}"
                    ax.set_title(title, fontsize=14, fontweight='bold')

                    print(f"  Added: {roi} - {subject}")

                except Exception as e:
                    print(f"  Error loading {fig_path}: {e}")
                    ax.text(0.5, 0.5, f"Error loading\n{roi} - {subject}",
                           ha='center', va='center', transform=ax.transAxes)
                    ax.axis('off')
            else:
                # Empty subplot for missing data
                ax.text(0.5, 0.5, f"{roi} - {subject}\nNot available",
                       ha='center', va='center', transform=ax.transAxes,
                       fontsize=10, color='gray')
                ax.axis('off')
                print(f"  Missing: {roi} - {subject}")

    # Adjust layout
    plt.tight_layout(rect=[0, 0, 1, 0.99])

    # Save compilation
    output_filename = f"{figure_type}_{method}_compilation.png"
    output_path = OUTPUT_DIR / output_filename
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"  Saved: {output_path}")
    print(f"  Total figures compiled: {sum(len(figs) for figs in all_figures.values())}")


def main():
    """Main function to create all compilations."""
    print("=" * 70)
    print("Creating PCA Figure Compilations")
    print("=" * 70)

    for method in METHOD_DIRS.keys():
        for figure_type in FIGURE_TYPES.keys():
            create_compilation(method, figure_type)

    print("\n" + "=" * 70)
    print("Compilation Complete!")
    print(f"Output directory: {OUTPUT_DIR}")
    print("=" * 70)

    # List all created files
    created_files = sorted(OUTPUT_DIR.glob("*.png"))
    if created_files:
        print("\nCreated files:")
        for f in created_files:
            print(f"  - {f.name}")


if __name__ == "__main__":
    main()
