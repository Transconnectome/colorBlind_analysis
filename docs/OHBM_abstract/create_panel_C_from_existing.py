#!/usr/bin/env python3
"""
Create Panel C by combining existing circular reconstruction figures
"""

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from pathlib import Path

def create_panel_C_from_existing():
    """Combine existing circular plots into 2x4 grid"""

    # Base path to existing figures
    base_path = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/logs/permutation_analysis/roi_specific/anova_config32_determin')

    # Define files for HC (sub-06) and CVD (sub-08)
    hc_files = {
        'V1': 'anova_circular_config32_determin_sub-06_V1_k10.png',
        'V2': 'anova_circular_config32_determin_sub-06_V2_k10.png',
        'V3': 'anova_circular_config32_determin_sub-06_V3_k3.png',
        'hV4': 'anova_circular_config32_determin_sub-06_hV4_k5.png',
    }

    cvd_files = {
        'V1': 'anova_circular_config32_determin_sub-08_V1_k10.png',
        'V2': 'anova_circular_config32_determin_sub-08_V2_k10.png',
        'V3': 'anova_circular_config32_determin_sub-08_V3_k4.png',
        'hV4': 'anova_circular_config32_determin_sub-08_hV4_k4.png',
    }

    # ROIs
    rois = ['V1', 'V2', 'V3', 'hV4']

    # Create figure
    fig, axes = plt.subplots(2, 4, figsize=(20, 10))

    # Plot HC (row 0)
    for col, roi in enumerate(rois):
        img_path = base_path / hc_files[roi]
        if img_path.exists():
            img = mpimg.imread(str(img_path))
            axes[0, col].imshow(img)
            axes[0, col].axis('off')

            # Add blue border for HC
            for spine in axes[0, col].spines.values():
                spine.set_edgecolor('#1f77b4')
                spine.set_linewidth(4)
                spine.set_visible(True)
        else:
            axes[0, col].text(0.5, 0.5, f'{roi}\nNo data',
                            ha='center', va='center', fontsize=14)
            axes[0, col].axis('off')

    # Plot CVD (row 1)
    for col, roi in enumerate(rois):
        img_path = base_path / cvd_files[roi]
        if img_path.exists():
            img = mpimg.imread(str(img_path))
            axes[1, col].imshow(img)
            axes[1, col].axis('off')

            # Add orange border for CVD
            for spine in axes[1, col].spines.values():
                spine.set_edgecolor('#ff7f0e')
                spine.set_linewidth(4)
                spine.set_visible(True)
        else:
            axes[1, col].text(0.5, 0.5, f'{roi}\nNo data',
                            ha='center', va='center', fontsize=14)
            axes[1, col].axis('off')

    # Add row labels
    fig.text(0.02, 0.75, 'HC\n(sub-06)', ha='center', va='center',
            fontsize=14, fontweight='bold', rotation=0,
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#1f77b4',
                     edgecolor='black', alpha=0.3, linewidth=2))

    fig.text(0.02, 0.25, 'CVD\n(sub-08)', ha='center', va='center',
            fontsize=14, fontweight='bold', rotation=0,
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#ff7f0e',
                     edgecolor='black', alpha=0.3, linewidth=2))

    # Overall title
    fig.suptitle('Panel C: Color Reconstruction - Representative Subjects',
                fontsize=18, fontweight='bold', y=0.98)

    plt.tight_layout(rect=[0.04, 0, 1, 0.96])

    # Save
    output_png = 'Panel_C_Reconstruction.png'
    output_pdf = 'Panel_C_Reconstruction.pdf'

    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    plt.savefig(output_pdf, bbox_inches='tight')

    print(f"✓ Figure saved:")
    print(f"  - {output_png}")
    print(f"  - {output_pdf}")

    return fig

if __name__ == '__main__':
    create_panel_C_from_existing()
    plt.show()
