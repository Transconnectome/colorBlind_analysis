#!/usr/bin/env python3
"""
Create figure showing the 8 isoluminant color stimuli in CIE L*a*b* space
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch
import matplotlib.patches as mpatches

# CIELab color definitions from actual experiment
COLOR_LAB = {
    'color_1': [59.90, 62.69, 3.78],    # 0°: Red/Pink
    'color_2': [64.20, 49.20, 45.58],   # 45°: Orange
    'color_3': [57.27, 13.06, 41.69],   # 90°: Brown/Yellow
    'color_4': [69.08, -55.02, 47.38],  # 135°: Green
    'color_5': [74.61, -41.33, -4.89],  # 180°: Cyan
    'color_6': [69.14, -11.45, -40.91], # 225°: Blue
    'color_7': [60.68, 19.18, -54.13],  # 270°: Dark Blue
    'color_8': [60.17, 46.82, -40.31],  # 315°: Purple/Pink
}

LABEL2HUE_DEG = {
    'color_1': 0.0,
    'color_2': 45.0,
    'color_3': 90.0,
    'color_4': 135.0,
    'color_5': 180.0,
    'color_6': 225.0,
    'color_7': 270.0,
    'color_8': 315.0,
}

def lab2rgb_accurate(L, a, b, clip=True):
    """
    CIELab → RGB accurate color space conversion
    """
    L, a, b = float(L), float(a), float(b)

    # Lab to XYZ
    y = (L + 16) / 116
    x = a / 500 + y
    z = y - b / 200

    xyz = np.array([x, y, z])
    xyz = np.where(xyz > 0.206893, xyz**3, (xyz - 16/116) / 7.787)
    xyz *= [0.95047, 1., 1.08883]  # D65 white point

    # XYZ to RGB (sRGB matrix)
    rgb = np.dot([[3.2406, -1.5372, -0.4986],
                  [-0.9689, 1.8758, 0.0415],
                  [0.0557, -0.2040, 1.0570]], xyz)

    # Gamma correction
    rgb = np.where(rgb <= 0.0031308, 12.92 * rgb, 1.055 * rgb**(1/2.4) - 0.055)

    if clip:
        rgb = np.clip(rgb, 0, 1)

    return tuple(rgb)


def create_stimulus_figure():
    """
    Create figure showing 8 isoluminant color stimuli in CIE L*a*b* space
    Clean version: colors on perfect circle, minimal labeling
    """
    fig, ax = plt.subplots(1, 1, figsize=(8, 8))

    # Set up L*a*b* coordinate system
    ax.set_xlim(-60, 60)
    ax.set_ylim(-60, 60)
    ax.set_aspect('equal')

    # Draw axes
    ax.axhline(y=0, color='gray', linestyle='-', linewidth=1.5, alpha=0.5, zorder=1)
    ax.axvline(x=0, color='gray', linestyle='-', linewidth=1.5, alpha=0.5, zorder=1)

    # Draw concentric circles for reference
    for radius in [20, 40]:
        circle = Circle((0, 0), radius, fill=False, edgecolor='gray',
                       linestyle='--', linewidth=1, alpha=0.3, zorder=1)
        ax.add_patch(circle)

    # Simple axis labels
    ax.set_xlabel('a*', fontsize=16, fontweight='bold')
    ax.set_ylabel('b*', fontsize=16, fontweight='bold')

    # Plot neutral gray in center
    gray_rgb = lab2rgb_accurate(54, 0, 0)  # L*=54, a*=0, b*=0
    gray_circle = Circle((0, 0), 4, facecolor=gray_rgb, edgecolor='black',
                         linewidth=1.5, zorder=5)
    ax.add_patch(gray_circle)

    # Plot the 8 colors on PERFECT CIRCLE (theoretical positions)
    radius = 38  # Target radius
    for i in range(1, 9):
        color_name = f'color_{i}'
        hue_deg = LABEL2HUE_DEG[color_name]

        # Calculate position on perfect circle
        # 0° is at right, counterclockwise
        hue_rad = np.deg2rad(hue_deg)
        a_pos = radius * np.cos(hue_rad)
        b_pos = radius * np.sin(hue_rad)

        # Get actual color from experiment
        L, a_val, b_val = COLOR_LAB[color_name]
        rgb = lab2rgb_accurate(L, a_val, b_val)

        # Plot color circle on theoretical position
        color_circle = Circle((a_pos, b_pos), 5, facecolor=rgb,
                             edgecolor='black', linewidth=2, zorder=4)
        ax.add_patch(color_circle)

        # Add angle label outside
        label_offset = 1.35
        label_x = radius * label_offset * np.cos(hue_rad)
        label_y = radius * label_offset * np.sin(hue_rad)
        ax.text(label_x, label_y, f'{int(hue_deg)}°',
               fontsize=10, ha='center', va='center',
               fontweight='bold',
               bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                        edgecolor='none', alpha=0.8))

    # Draw the perfect circle
    theta = np.linspace(0, 2*np.pi, 100)
    x_circle = radius * np.cos(theta)
    y_circle = radius * np.sin(theta)
    ax.plot(x_circle, y_circle, 'k-', linewidth=2, alpha=0.6, zorder=2)

    # Grid
    ax.grid(True, alpha=0.2, linestyle=':', zorder=0)

    plt.tight_layout()

    # Save figure
    output_path_png = 'Stimulus_Colors_Lab_Space.png'
    output_path_pdf = 'Stimulus_Colors_Lab_Space.pdf'

    plt.savefig(output_path_png, dpi=300, bbox_inches='tight')
    plt.savefig(output_path_pdf, bbox_inches='tight')

    print(f"✓ Figure saved:")
    print(f"  - {output_path_png}")
    print(f"  - {output_path_pdf}")

    # Also create a summary table
    print("\n" + "="*70)
    print("Color Stimulus Summary")
    print("="*70)
    print(f"{'Color':<10} {'Hue (°)':<10} {'L*':<10} {'a*':<10} {'b*':<10} {'RGB':<20}")
    print("-"*70)
    for i in range(1, 9):
        color_name = f'color_{i}'
        L, a_val, b_val = COLOR_LAB[color_name]
        hue_deg = LABEL2HUE_DEG[color_name]
        rgb = lab2rgb_accurate(L, a_val, b_val)
        rgb_str = f"({rgb[0]:.2f}, {rgb[1]:.2f}, {rgb[2]:.2f})"
        print(f"{color_name:<10} {hue_deg:<10.0f} {L:<10.2f} {a_val:<10.2f} {b_val:<10.2f} {rgb_str:<20}")
    print("="*70)
    print(f"Mean L*: {np.mean([COLOR_LAB[f'color_{i}'][0] for i in range(1, 9)]):.2f}")
    print(f"Std L*:  {np.std([COLOR_LAB[f'color_{i}'][0] for i in range(1, 9)]):.2f}")

    # Calculate actual radius for each color
    radii = []
    for i in range(1, 9):
        color_name = f'color_{i}'
        L, a_val, b_val = COLOR_LAB[color_name]
        radius = np.sqrt(a_val**2 + b_val**2)
        radii.append(radius)
    print(f"\nMean radius (√(a*² + b*²)): {np.mean(radii):.2f}")
    print(f"Std radius:                  {np.std(radii):.2f}")
    print(f"Range: [{np.min(radii):.2f}, {np.max(radii):.2f}]")

    return fig


if __name__ == '__main__':
    create_stimulus_figure()
    plt.show()
