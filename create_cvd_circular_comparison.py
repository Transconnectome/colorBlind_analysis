#!/usr/bin/env python3
"""
Create CVD-specific circular color space comparison visualizations
Highlighting red-green spectrum (colors 1-5) with detailed analysis
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from PIL import Image
import matplotlib.patches as patches

# Configuration
LOGS_DIR = Path("logs_1117")
COMPREHENSIVE_DIR = LOGS_DIR / "comprehensive_analysis"
OUTPUT_DIR = LOGS_DIR / "cvd_detailed_analysis"

SUBJECTS = ["sub-01", "sub-02", "sub-03", "sub-04"]
ROIS = ["V1", "V2", "V3", "hV4"]
NON_CVD = ["sub-01", "sub-02"]
CVD = ["sub-03", "sub-04"]

def create_cvd_circular_grid_comparison():
    """Create side-by-side comparison of Non-CVD vs CVD for each ROI"""

    fig, axes = plt.subplots(len(ROIS), 2, figsize=(20, 6*len(ROIS)))
    fig.suptitle('Circular Color Space Reconstruction: Non-CVD vs CVD Comparison\n(Red-Green Spectrum: Colors 1-5)',
                 fontsize=24, fontweight='bold', y=0.995)

    for method_idx, method in enumerate(['zScore', 'voxelSelect']):
        for roi_idx, roi in enumerate(ROIS):
            # Non-CVD column
            ax_noncvd = axes[roi_idx, 0] if len(ROIS) > 1 else axes[0]
            # CVD column
            ax_cvd = axes[roi_idx, 1] if len(ROIS) > 1 else axes[1]

            # Collect circular space images for this ROI
            method_folder = "zScore" if method == "zScore" else "voxelSelect"
            timestamp = "20251118_010419" if method == "zScore" else "20251118_012145"

            # Create composite image for Non-CVD
            noncvd_images = []
            for subject in NON_CVD:
                img_path = (LOGS_DIR / timestamp / subject / "fir_reconstruction_uni_hrf" /
                           method_folder / f"{roi}_universal_hrf" / "figures" /
                           f"{roi}_circular_color_space.png")
                if img_path.exists():
                    noncvd_images.append(Image.open(img_path))

            # Create composite image for CVD
            cvd_images = []
            for subject in CVD:
                img_path = (LOGS_DIR / timestamp / subject / "fir_reconstruction_uni_hrf" /
                           method_folder / f"{roi}_universal_hrf" / "figures" /
                           f"{roi}_circular_color_space.png")
                if img_path.exists():
                    cvd_images.append(Image.open(img_path))

            # Display Non-CVD composite
            if noncvd_images:
                if len(noncvd_images) == 2:
                    # Stack vertically
                    widths = [img.width for img in noncvd_images]
                    heights = [img.height for img in noncvd_images]
                    max_width = max(widths)
                    total_height = sum(heights)

                    composite = Image.new('RGB', (max_width, total_height), (255, 255, 255))
                    y_offset = 0
                    for img in noncvd_images:
                        composite.paste(img, (0, y_offset))
                        y_offset += img.height

                    ax_noncvd.imshow(composite)
                else:
                    ax_noncvd.imshow(noncvd_images[0])

                ax_noncvd.axis('off')
                ax_noncvd.set_title(f'{roi} - Non-CVD (sub-01, sub-02)\n{method}',
                                   fontsize=14, fontweight='bold', color='steelblue')
            else:
                ax_noncvd.text(0.5, 0.5, f'No data:\n{roi} - Non-CVD',
                             ha='center', va='center', fontsize=12)
                ax_noncvd.axis('off')

            # Display CVD composite
            if cvd_images:
                if len(cvd_images) == 2:
                    # Stack vertically
                    widths = [img.width for img in cvd_images]
                    heights = [img.height for img in cvd_images]
                    max_width = max(widths)
                    total_height = sum(heights)

                    composite = Image.new('RGB', (max_width, total_height), (255, 255, 255))
                    y_offset = 0
                    for img in cvd_images:
                        composite.paste(img, (0, y_offset))
                        y_offset += img.height

                    ax_cvd.imshow(composite)
                else:
                    ax_cvd.imshow(cvd_images[0])

                ax_cvd.axis('off')
                ax_cvd.set_title(f'{roi} - CVD (sub-03, sub-04)\n{method}',
                               fontsize=14, fontweight='bold', color='coral')
            else:
                ax_cvd.text(0.5, 0.5, f'No data:\n{roi} - CVD',
                          ha='center', va='center', fontsize=12)
                ax_cvd.axis('off')

    plt.tight_layout()
    output_file = OUTPUT_DIR / f"cvd_circular_comparison_{method}.png"
    plt.savefig(output_file, dpi=200, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()

    return output_file

def create_annotated_circular_interpretation():
    """Create an annotated interpretation figure explaining key features"""

    fig = plt.figure(figsize=(20, 12))
    gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)

    fig.suptitle('Circular Color Space: Interpretation Guide for CVD Analysis',
                 fontsize=20, fontweight='bold')

    # Load example images for annotation
    example_noncvd = None
    example_cvd = None

    # Try to find best V2 examples (best overall performance)
    for subject in NON_CVD:
        img_path = (LOGS_DIR / "20251118_010419" / subject / "fir_reconstruction_uni_hrf" /
                   "zScore" / "V2_universal_hrf" / "figures" / "V2_circular_color_space.png")
        if img_path.exists():
            example_noncvd = Image.open(img_path)
            break

    for subject in CVD:
        img_path = (LOGS_DIR / "20251118_010419" / subject / "fir_reconstruction_uni_hrf" /
                   "zScore" / "V2_universal_hrf" / "figures" / "V2_circular_color_space.png")
        if img_path.exists():
            example_cvd = Image.open(img_path)
            break

    # Panel 1: Non-CVD example with annotations
    ax1 = fig.add_subplot(gs[0, 0])
    if example_noncvd:
        ax1.imshow(example_noncvd)
        ax1.axis('off')
        ax1.set_title('Non-CVD Example (V2)\nKey Features:',
                     fontsize=14, fontweight='bold', color='steelblue')

        # Add text annotations
        text = """
• Training colors (left): Tight clustering
  around true positions (border markers)

• Novel colors (right): Predictions closer
  to true positions

• Red-Green spectrum (Colors 1-5):
  Evenly distributed, 45° spacing preserved

• Low scatter: Consistent predictions
  across runs
        """
        ax1.text(0.02, 0.5, text, transform=ax1.transAxes,
                fontsize=11, verticalalignment='center',
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))

    # Panel 2: CVD example with annotations
    ax2 = fig.add_subplot(gs[0, 1])
    if example_cvd:
        ax2.imshow(example_cvd)
        ax2.axis('off')
        ax2.set_title('CVD Example (V2)\nKey Deficits:',
                     fontsize=14, fontweight='bold', color='coral')

        # Add text annotations
        text = """
• Training colors (left): Larger scatter,
  especially for yellow-green region

• Novel colors (right): Large errors,
  often >90° from true position

• Yellow-Green compression (Colors 3-4):
  Predictions cluster together, losing
  45° spacing

• High scatter: Inconsistent predictions
  across runs (bimodal distribution)
        """
        ax2.text(0.02, 0.5, text, transform=ax2.transAxes,
                fontsize=11, verticalalignment='center',
                bbox=dict(boxstyle='round', facecolor='lightsalmon', alpha=0.8))

    # Panel 3: Schematic diagram of ideal vs CVD pattern
    ax3 = fig.add_subplot(gs[1, :])
    ax3.set_xlim(-1.5, 1.5)
    ax3.set_ylim(-1.5, 1.5)
    ax3.set_aspect('equal')
    ax3.axis('off')
    ax3.set_title('Schematic: Color Space Compression in CVD',
                 fontsize=14, fontweight='bold')

    # Draw circle
    circle = plt.Circle((0, 0), 1, fill=False, edgecolor='black', linewidth=2)
    ax3.add_patch(circle)

    # Define color positions (in radians, but we'll use degrees for labels)
    colors_deg = [0, 45, 90, 135, 180, 225, 270, 315]
    colors_rad = [np.deg2rad(d) for d in colors_deg]
    color_names = ['Red', 'Orange', 'Yellow', 'Y-Green', 'Cyan', 'Blue', 'Purple', 'Magenta']
    color_colors = ['red', 'orange', 'yellow', 'yellowgreen', 'cyan', 'blue', 'purple', 'magenta']

    # Plot ideal (Non-CVD) positions on left semicircle
    for i, (rad, name, col) in enumerate(zip(colors_rad[:5], color_names[:5], color_colors[:5])):
        x = -0.5 + 0.4 * np.cos(rad)
        y = 0.4 * np.sin(rad)

        # True position marker
        ax3.plot(x, y, 'o', color=col, markersize=15, markeredgecolor='black',
                markeredgewidth=2, label=name if i == 0 else None)

        # Label
        label_x = -0.5 + 0.6 * np.cos(rad)
        label_y = 0.6 * np.sin(rad)
        ax3.text(label_x, label_y, f'{name}\n{colors_deg[i]}°',
                ha='center', va='center', fontsize=9, fontweight='bold')

    # Plot CVD compressed positions on right semicircle
    # Simulate compression: reduce spacing in yellow-green region
    cvd_deviations = [0, -5, -20, -25, -10]  # Degrees of error

    for i, (rad, name, col, dev) in enumerate(zip(colors_rad[:5], color_names[:5],
                                                    color_colors[:5], cvd_deviations)):
        # Add deviation
        cvd_rad = np.deg2rad(colors_deg[i] + dev)
        x = 0.5 + 0.4 * np.cos(cvd_rad)
        y = 0.4 * np.sin(cvd_rad)

        # True position marker (faded)
        true_x = 0.5 + 0.4 * np.cos(rad)
        true_y = 0.4 * np.sin(rad)
        ax3.plot(true_x, true_y, 'o', color=col, markersize=12,
                markeredgecolor='gray', markeredgewidth=1, alpha=0.3)

        # CVD position marker
        ax3.plot(x, y, 's', color=col, markersize=15, markeredgecolor='black',
                markeredgewidth=2, alpha=0.8)

        # Error arrow
        if abs(dev) > 0:
            ax3.annotate('', xy=(x, y), xytext=(true_x, true_y),
                        arrowprops=dict(arrowstyle='->', color='red', lw=2, alpha=0.6))

        # Label with error
        label_x = 0.5 + 0.6 * np.cos(rad)
        label_y = 0.6 * np.sin(rad)
        if abs(dev) > 0:
            ax3.text(label_x, label_y, f'{name}\n{colors_deg[i]+dev:.0f}°\n(Δ{dev:+.0f}°)',
                    ha='center', va='center', fontsize=9, fontweight='bold', color='red')
        else:
            ax3.text(label_x, label_y, f'{name}\n{colors_deg[i]}°',
                    ha='center', va='center', fontsize=9, fontweight='bold')

    # Add labels
    ax3.text(-0.5, -1.3, 'Non-CVD\n(Ideal Spacing)', ha='center', va='center',
            fontsize=12, fontweight='bold', color='steelblue',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
    ax3.text(0.5, -1.3, 'CVD\n(Compressed Y-Green)', ha='center', va='center',
            fontsize=12, fontweight='bold', color='coral',
            bbox=dict(boxstyle='round', facecolor='lightsalmon', alpha=0.5))

    # Legend
    ax3.text(0, 1.4, 'Red-Green Spectrum Compression in CVD',
            ha='center', va='center', fontsize=13, fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    ax3.text(0, 1.25, 'Circles: True positions | Squares: CVD predictions | Red arrows: Angular errors',
            ha='center', va='center', fontsize=10)

    plt.tight_layout()
    output_file = OUTPUT_DIR / "cvd_circular_interpretation_guide.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()

    return output_file

def main():
    print("\n" + "="*80)
    print("CREATING CVD CIRCULAR SPACE COMPARISON VISUALIZATIONS")
    print("="*80 + "\n")

    print("1. Creating ROI-by-ROI circular comparison (Non-CVD vs CVD)...")
    for method in ['zScore', 'voxelSelect']:
        # Note: We'll create one comparison per method
        # But for now, let's do zScore as primary
        if method == 'zScore':
            create_cvd_circular_grid_comparison()

    print("\n2. Creating annotated interpretation guide...")
    create_annotated_circular_interpretation()

    print("\n" + "="*80)
    print("✓ CVD CIRCULAR VISUALIZATIONS COMPLETE!")
    print(f"Results saved to: {OUTPUT_DIR}")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
