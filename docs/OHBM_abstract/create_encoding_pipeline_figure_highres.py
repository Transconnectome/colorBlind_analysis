#!/usr/bin/env python3
"""
Create HIGH RESOLUTION forward encoding model pipeline figure for OHBM abstract (A0 Poster)
Shows 4 stages: Color → Channel → Voxel → Channel → Color
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Rectangle
from matplotlib.lines import Line2D
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

def create_basis_function_plot(ax, hue_deg=0):
    """Create a single basis function (half-wave rectified squared sinusoid)"""
    angles = np.linspace(0, 360, 360)
    dist = np.abs(angles - hue_deg)
    dist = np.where(dist > 180, 360 - dist, dist)

    response = np.cos(np.deg2rad(dist))
    response = np.where(response > 0, response ** 2, 0)

    return angles, response

def create_pipeline_figure_highres():
    """
    Create complete 4-stage pipeline figure - HIGH RESOLUTION for A0 poster
    """
    # INCREASED figure size
    fig = plt.figure(figsize=(32, 20))

    # Create main layout
    ax1 = plt.subplot(2, 2, 1)  # Stage 1
    ax2 = plt.subplot(2, 2, 2)  # Stage 2
    ax3 = plt.subplot(2, 2, 3)  # Stage 3
    ax4 = plt.subplot(2, 2, 4)  # Stage 4

    # ========================================================================
    # STAGE 1: Color → Channel (Basis Functions)
    # ========================================================================
    ax1.set_title('Stage 1: Color → Channel\n(Cone-like Basis Functions)',
                  fontsize=32, fontweight='bold', pad=25)

    # Create color wheel background
    theta_bg = np.linspace(0, 2*np.pi, 360)
    for i in range(360):
        color_angle = np.rad2deg(theta_bg[i])
        # Simple color mapping for visualization
        r = max(0, np.cos(np.deg2rad(color_angle)))
        g = max(0, np.cos(np.deg2rad(color_angle - 120)))
        b = max(0, np.cos(np.deg2rad(color_angle + 120)))
        norm = max(r, g, b)
        if norm > 0:
            r, g, b = r/norm, g/norm, b/norm
        ax1.axvline(color_angle, color=(r, g, b), alpha=0.1, linewidth=2)

    # Plot 6 basis functions - THICKER lines
    colors_bf = ['red', 'orange', 'yellow', 'green', 'cyan', 'blue']
    channel_centers = [0, 60, 120, 180, 240, 300]

    for i, (center, color) in enumerate(zip(channel_centers, colors_bf)):
        angles, response = create_basis_function_plot(ax1, center)
        ax1.plot(angles, response, linewidth=5, color=color, alpha=0.8)

        # Mark peak - LARGER markers
        ax1.plot([center], [1.0], 'o', markersize=20, color=color,
                markeredgecolor='black', markeredgewidth=3, zorder=10)

    ax1.set_xlabel('Hue Angle (degrees)', fontsize=28, fontweight='bold')
    ax1.set_ylabel('Channel Response', fontsize=28, fontweight='bold')
    ax1.set_xlim(0, 360)
    ax1.set_ylim(-0.05, 1.15)
    ax1.grid(True, alpha=0.3, linestyle='--', linewidth=1.5)
    ax1.tick_params(axis='both', which='major', labelsize=22)

    # ========================================================================
    # STAGE 2: Channel → Voxel (Training: Learn W)
    # ========================================================================
    ax2.set_title('Stage 2: Channel → Voxel (Training)\n(Linear Mapping W)',
                  fontsize=32, fontweight='bold', pad=25)
    ax2.axis('off')
    ax2.set_xlim(0, 10)
    ax2.set_ylim(0, 10)

    # Channel representation (left) - LARGER circles
    channel_y = np.linspace(7, 3, 6)
    for i, y in enumerate(channel_y):
        circle = Circle((2, y), 0.35, facecolor=colors_bf[i],
                       edgecolor='black', linewidth=3, zorder=5)
        ax2.add_patch(circle)
        ax2.text(1.2, y, f'C{i+1}', ha='right', va='center',
                fontsize=24, fontweight='bold')

    # Voxel representation (right) - LARGER rectangles
    voxel_y = np.linspace(2.5, 7.5, 8)
    for i, y in enumerate(voxel_y):
        rect = Rectangle((7.5, y-0.25), 1.0, 0.5, facecolor='lightblue',
                        edgecolor='black', linewidth=2.5, zorder=5)
        ax2.add_patch(rect)
        ax2.text(9.3, y, f'V{i+1}', ha='left', va='center',
                fontsize=22, fontweight='bold')

    # Weight matrix connections - THICKER lines
    np.random.seed(42)
    for _ in range(20):
        c_idx = np.random.randint(0, 6)
        v_idx = np.random.randint(0, 8)
        weight = np.random.randn()
        alpha = min(abs(weight) * 0.3, 0.6)
        color = 'blue' if weight > 0 else 'red'
        linewidth = abs(weight) * 1.2 + 0.8

        ax2.plot([2.35, 7.5], [channel_y[c_idx], voxel_y[v_idx]],
                color=color, alpha=alpha, linewidth=linewidth, zorder=1)

    # Labels - LARGER fonts
    ax2.text(2, 8.8, 'Channel\nActivations', ha='center', va='center',
            fontsize=24, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.7', facecolor='wheat', alpha=0.8))

    ax2.text(8.2, 8.8, 'Voxel\nResponses', ha='center', va='center',
            fontsize=24, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.7', facecolor='lightblue', alpha=0.8))

    # Equation - LARGER
    ax2.text(5, 1.5, r'$\mathbf{B} = \mathbf{W} \times \mathbf{C}$',
            ha='center', va='center', fontsize=36, fontweight='bold',
            bbox=dict(boxstyle='round,pad=1.2', facecolor='white',
                     edgecolor='black', linewidth=3))

    # ========================================================================
    # STAGE 3: Voxel → Channel (Testing: Invert W)
    # ========================================================================
    ax3.set_title('Stage 3: Voxel → Channel (Testing)\n(Inverse Mapping W⁻¹)',
                  fontsize=32, fontweight='bold', pad=25)
    ax3.axis('off')
    ax3.set_xlim(0, 10)
    ax3.set_ylim(0, 10)

    # Voxel representation (left) - LARGER
    voxel_y_test = np.linspace(2.5, 7.5, 8)
    for i, y in enumerate(voxel_y_test):
        rect = Rectangle((1.0, y-0.25), 1.0, 0.5, facecolor='lightcoral',
                        edgecolor='black', linewidth=2.5, zorder=5)
        ax3.add_patch(rect)
        ax3.text(0.2, y, f'V{i+1}', ha='right', va='center',
                fontsize=22, fontweight='bold')

    # Predicted channel representation (right) - LARGER circles
    channel_y_pred = np.linspace(3, 7, 6)
    for i, y in enumerate(channel_y_pred):
        circle = Circle((8, y), 0.35, facecolor=colors_bf[i],
                       edgecolor='black', linewidth=3, linestyle='--', zorder=5)
        ax3.add_patch(circle)
        ax3.text(8.8, y, f'Ĉ{i+1}', ha='left', va='center',
                fontsize=24, fontweight='bold')

    # Inverse mapping connections - THICKER
    for _ in range(20):
        v_idx = np.random.randint(0, 8)
        c_idx = np.random.randint(0, 6)
        weight = np.random.randn()
        alpha = min(abs(weight) * 0.3, 0.6)
        color = 'darkgreen' if weight > 0 else 'purple'
        linewidth = abs(weight) * 1.2 + 0.8

        ax3.plot([2.0, 7.65], [voxel_y_test[v_idx], channel_y_pred[c_idx]],
                color=color, alpha=alpha, linewidth=linewidth, zorder=1)

    # Labels - LARGER fonts
    ax3.text(1.5, 8.8, 'Test Voxel\nResponses', ha='center', va='center',
            fontsize=24, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.7', facecolor='lightcoral', alpha=0.8))

    ax3.text(8, 8.8, 'Predicted\nChannels', ha='center', va='center',
            fontsize=24, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.7', facecolor='wheat', alpha=0.8))

    # Equation - LARGER
    ax3.text(5, 1.5, r'$\mathbf{\hat{C}} = (\mathbf{W}^T \mathbf{W})^{-1} \mathbf{W}^T \mathbf{B}_{test}$',
            ha='center', va='center', fontsize=32, fontweight='bold',
            bbox=dict(boxstyle='round,pad=1.2', facecolor='white',
                     edgecolor='black', linewidth=3))

    # ========================================================================
    # STAGE 4: Channel → Color (Reconstruction)
    # ========================================================================
    ax4.set_title('Stage 4: Channel → Color\n(Correlation-Based Selection)',
                  fontsize=32, fontweight='bold', pad=25)
    ax4.axis('off')
    ax4.set_xlim(0, 10)
    ax4.set_ylim(0, 10)

    # Predicted channel pattern (bar plot style) - WIDER bars
    channel_bars_x = np.linspace(1.5, 4.5, 6)
    predicted_values = [0.3, 0.1, 0.05, 0.2, 0.8, 0.9]

    for i, (x, val) in enumerate(zip(channel_bars_x, predicted_values)):
        height = val * 3
        rect = Rectangle((x-0.25, 5-height/2), 0.5, height,
                        facecolor=colors_bf[i], edgecolor='black',
                        linewidth=2.5, alpha=0.8, zorder=5)
        ax4.add_patch(rect)
        ax4.text(x, 3.2, f'Ĉ{i+1}', ha='center', va='top',
                fontsize=22, fontweight='bold')

    ax4.text(3, 7.5, 'Predicted Channel Pattern', ha='center', va='center',
            fontsize=24, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.7', facecolor='wheat', alpha=0.8))

    # Shorter arrow - THICKER
    arrow = FancyArrowPatch((5.0, 5), (5.6, 5),
                           arrowstyle='->', mutation_scale=50,
                           linewidth=5, color='black', zorder=10)
    ax4.add_patch(arrow)

    # Color wheel with reconstruction - LARGER
    center_x, center_y = 8, 5
    radius = 1.4

    # Draw background circle - THICKER
    bg_circle = Circle((center_x, center_y), radius, fill=False,
                      edgecolor='gray', linewidth=3, linestyle='-', alpha=0.5, zorder=1)
    ax4.add_patch(bg_circle)

    # Draw axis lines - THICKER
    ax4.plot([center_x - radius - 0.2, center_x + radius + 0.2], [center_y, center_y],
            color='lightgray', linewidth=2, alpha=0.5, zorder=1)
    ax4.plot([center_x, center_x], [center_y - radius - 0.2, center_y + radius + 0.2],
            color='lightgray', linewidth=2, alpha=0.5, zorder=1)

    # Plot the 8 stimulus colors - LARGER circles
    stimulus_angles = [0, 45, 90, 135, 180, 225, 270, 315]
    color_circle_radius = 0.28

    for i, angle_deg in enumerate(stimulus_angles, 1):
        angle_rad = np.deg2rad(angle_deg)
        x_pos = center_x + radius * np.cos(angle_rad)
        y_pos = center_y + radius * np.sin(angle_rad)

        color_name = f'color_{i}'
        L, a_val, b_val = COLOR_LAB[color_name]
        rgb = lab2rgb_accurate(L, a_val, b_val)

        color_circle = Circle((x_pos, y_pos), color_circle_radius,
                             facecolor=rgb, edgecolor='black',
                             linewidth=3, zorder=4)
        ax4.add_patch(color_circle)

        # Degree labels - LARGER font
        label_offset = 1.40
        label_x = center_x + radius * label_offset * np.cos(angle_rad)
        label_y = center_y + radius * label_offset * np.sin(angle_rad)
        ax4.text(label_x, label_y, f'{angle_deg}°',
                ha='center', va='center', fontsize=20, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                         edgecolor='none', alpha=0.7))

    # Reconstructed hue arrow - THICKER
    reconstructed_angle = 255
    recon_rad = np.deg2rad(reconstructed_angle)
    recon_x = center_x + radius * 0.75 * np.cos(recon_rad)
    recon_y = center_y + radius * 0.75 * np.sin(recon_rad)

    arrow_recon = FancyArrowPatch((center_x, center_y), (recon_x, recon_y),
                                 arrowstyle='->', mutation_scale=45,
                                 linewidth=5, color='red', zorder=15)
    ax4.add_patch(arrow_recon)

    # Label - LARGER font
    label_angle_rad = np.deg2rad(90)
    text_x = center_x + radius * 1.5 * np.cos(label_angle_rad)
    text_y = center_y + radius * 2.9 * np.sin(label_angle_rad)
    ax4.text(text_x, text_y, f'{reconstructed_angle}°\nReconstructed',
            ha='center', va='center', fontsize=24, fontweight='bold', color='black',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='white',
                     edgecolor='black', linewidth=2.5, alpha=0.9))

    # Equation - LARGER
    ax4.text(5, 1.2, r'$\theta_{recon} = \arg\max_{\theta} \, \text{corr}(\mathbf{\hat{C}}, \mathbf{C}(\theta))$',
            ha='center', va='center', fontsize=30, fontweight='bold',
            bbox=dict(boxstyle='round,pad=1.0', facecolor='white',
                     edgecolor='black', linewidth=3))

    # ========================================================================
    # Overall title - LARGER
    # ========================================================================
    fig.suptitle('Forward Encoding Model Pipeline: Color Reconstruction from fMRI',
                fontsize=40, fontweight='bold', y=0.98)

    plt.tight_layout(rect=[0, 0, 1, 0.96])

    # Save with HIGH RESOLUTION
    output_png = 'Forward_Encoding_Pipeline_HighRes.png'
    output_pdf = 'Forward_Encoding_Pipeline_HighRes.pdf'

    plt.savefig(output_png, dpi=600, bbox_inches='tight', facecolor='white')
    plt.savefig(output_pdf, bbox_inches='tight', facecolor='white')

    print(f"✓ HIGH RESOLUTION Figure saved:")
    print(f"  - {output_png} (DPI=600)")
    print(f"  - {output_pdf} (vector format)")

    print("\n" + "="*70)
    print("Figure Settings for A0 Poster:")
    print("="*70)
    print(f"  Figure size: 32 x 20 inches")
    print(f"  DPI: 600 (high resolution)")
    print(f"  Title: fontsize=40")
    print(f"  Subtitles: fontsize=32")
    print(f"  Labels: fontsize=24-28")
    print(f"  Equations: fontsize=30-36")
    print(f"  Line widths: increased 2-3x")
    print(f"  Circle/marker sizes: increased 1.5-2x")
    print("="*70)

    return fig


if __name__ == '__main__':
    fig = create_pipeline_figure_highres()
    plt.show()
