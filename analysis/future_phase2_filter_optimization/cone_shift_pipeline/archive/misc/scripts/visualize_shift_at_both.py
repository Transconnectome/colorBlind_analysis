#!/usr/bin/env python3
"""
visualize_shift_at_both.py — V4 shift_at_both results visualization.

Specific to hV4 where W is retrained at each δθ (shift_at_both method).
This is the legacy V4-specific pipeline that differs from W-fixed.

Figures:
  Fig 1: Color swatches — Original | CVD-perceived | Filter-corrected
  Fig 2: Color wheel with shift arrows (V4 only)

Usage:
    conda activate srm
    python scripts/visualize_shift_at_both.py [--output_dir figures/shift_at_both]
"""

import argparse
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from pathlib import Path
import sys

_SCRIPT_DIR = Path(__file__).resolve().parent
_FWD_DIR = str(_SCRIPT_DIR.parent.parent.parent / 'future_phase1_forward_model' / 'scripts')
if _FWD_DIR not in sys.path:
    sys.path.insert(0, _FWD_DIR)
sys.path.insert(0, str(_SCRIPT_DIR))

from stockman_cone_shift import COLOR_NAMES, HUE_ANGLES_DEG
from utils_cone_3way import compute_1way_hue_shift

# ============================================================================
# Idealized stimulus colors (L*=75, chroma=40)
# ============================================================================
_L_STAR = 75.0
_CHROMA = 40.0
_M_XYZ_TO_SRGB = np.array([
    [3.2406, -1.5372, -0.4986],
    [-0.9689,  1.8758,  0.0415],
    [0.0557, -0.2040,  1.0570],
])

STIM_HUE_DEG = HUE_ANGLES_DEG.copy()


def lab2rgb(L, a, b):
    L, a, b = np.asarray(L, float), np.asarray(a, float), np.asarray(b, float)
    y = (L + 16) / 116
    x = a / 500 + y
    z = y - b / 200
    xyz = np.stack([x, y, z], axis=-1)
    mask = xyz > 0.206893
    xyz = np.where(mask, xyz**3, (xyz - 16/116) / 7.787)
    xyz *= np.array([0.95047, 1.0, 1.08883])
    rgb = xyz @ _M_XYZ_TO_SRGB.T
    rgb = np.where(rgb <= 0.0031308, 12.92 * rgb,
                   1.055 * np.power(np.maximum(rgb, 0), 1/2.4) - 0.055)
    return np.clip(rgb, 0, 1)


def get_stim_rgb():
    hue_rad = np.deg2rad(HUE_ANGLES_DEG)
    a = _CHROMA * np.cos(hue_rad)
    b = _CHROMA * np.sin(hue_rad)
    return lab2rgb(np.full(8, _L_STAR), a, b)


def shift_stim_hue(delta_deg):
    new_hue_rad = np.deg2rad(STIM_HUE_DEG + np.asarray(delta_deg))
    new_a = _CHROMA * np.cos(new_hue_rad)
    new_b = _CHROMA * np.sin(new_hue_rad)
    return lab2rgb(np.full(8, _L_STAR), new_a, new_b)


# V4 results from shift_at_both method (validated)
V4_FITS = {
    '08': {'model': 'cone_1way', 'params': [8.639], 'cvd_type': 'deutan',
           'rho': 0.690, 'p': 0.036, 'source': 'shift_at_both'},
    '09': {'model': 'cone_1way', 'params': [25.204], 'cvd_type': 'protan',
           'rho': 0.833, 'p': 0.009, 'source': 'shift_at_both'},
}

CVD_TYPE = {'08': 'deutan', '09': 'protan', '10': 'normal'}


def compute_v4_delta(subj):
    fit = V4_FITS.get(subj)
    if fit is None:
        return None
    _, _, delta = compute_1way_hue_shift(fit['params'][0], fit['cvd_type'])
    return delta


# ============================================================================
# Fig 1: Color Swatches
# ============================================================================

def plot_color_swatches(output_dir):
    """Three-row swatch per CVD subject: Original | CVD-perceived | Corrected."""
    orig_rgb = get_stim_rgb()
    subjects = [('08', 'deutan'), ('09', 'protan')]
    n_subj = len(subjects)

    fig, axes = plt.subplots(3 * n_subj + 1, 9, figsize=(15, 3 * n_subj + 2.5),
                              gridspec_kw={'width_ratios': [1.5] + [1]*8,
                                           'hspace': 0.5, 'wspace': 0.12})

    # Row 0: original stimulus colors
    axes[0, 0].text(0.5, 0.5, 'Stimulus\n(Normal)', ha='center', va='center',
                     fontsize=9, fontweight='bold', transform=axes[0, 0].transAxes)
    axes[0, 0].set_facecolor('white')
    axes[0, 0].set_xticks([]); axes[0, 0].set_yticks([])
    for spine in axes[0, 0].spines.values():
        spine.set_visible(False)

    for j in range(8):
        ax = axes[0, j+1]
        ax.set_facecolor(orig_rgb[j])
        ax.set_xticks([]); ax.set_yticks([])
        ax.set_title(COLOR_NAMES[j], fontsize=8, fontweight='bold', pad=2)
        for spine in ax.spines.values():
            spine.set_linewidth(2)
            spine.set_color('#333333')

    for s_idx, (subj, cvd_type) in enumerate(subjects):
        delta = compute_v4_delta(subj)
        if delta is None:
            continue

        fit = V4_FITS[subj]
        perceived_rgb = shift_stim_hue(delta)
        corrected_rgb = shift_stim_hue(-delta)

        base_row = 1 + s_idx * 3
        rho = fit['rho']

        row_labels = [
            (f'sub-{subj} ({cvd_type})\nCVD Perceived\nhV4 ' + r'$\rho$' + f'={rho:.2f}*',
             perceived_rgb, delta, '#D32F2F'),
            (f'Filter Corrected\n(inverse ' + r'$\delta\theta$' + ')',
             corrected_rgb, -delta, '#1565C0'),
            (f'Original\n(reference)',
             orig_rgb, np.zeros(8), '#666666'),
        ]

        for r_off, (label, rgb_arr, d_arr, accent) in enumerate(row_labels):
            row = base_row + r_off
            ax_label = axes[row, 0]
            ax_label.text(0.5, 0.5, label, ha='center', va='center', fontsize=7,
                          color=accent, fontweight='bold',
                          transform=ax_label.transAxes)
            ax_label.set_facecolor('white')
            ax_label.set_xticks([]); ax_label.set_yticks([])
            for spine in ax_label.spines.values():
                spine.set_visible(False)

            for j in range(8):
                ax = axes[row, j+1]
                ax.set_facecolor(np.clip(rgb_arr[j], 0, 1))
                ax.set_xticks([]); ax.set_yticks([])
                d = d_arr[j]
                if abs(d) > 0.5:
                    ax.text(0.5, -0.08, f'{d:+.1f}\u00B0',
                            ha='center', va='top', fontsize=6,
                            color=accent, transform=ax.transAxes)
                for spine in ax.spines.values():
                    spine.set_linewidth(1.5 if abs(d) <= 5 else 2.5)
                    spine.set_color(accent if abs(d) > 5 else '#999999')

    fig.suptitle('Cone-Shift Model: Perceived vs Filter-Corrected Colors\n'
                 '(hV4, shift_at_both method)',
                  fontsize=13, fontweight='bold', y=0.99)
    fig.text(0.5, 0.005,
             'CVD Perceived = what CVD brain encodes (hue shifted by +' +
             r'$\delta\theta$' + ') | Filter Corrected = pre-compensated stimulus '
             '(shifted by ' + r'$-\delta\theta$' + ')',
             ha='center', fontsize=8, style='italic', color='gray')

    plt.savefig(output_dir / 'color_swatches_hV4.png', dpi=200,
                bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'  Saved: {output_dir / "color_swatches_hV4.png"}')


# ============================================================================
# Fig 2: Color Wheel with Shift Arrows (V4 only)
# ============================================================================

def plot_color_wheel(output_dir):
    """Color wheel with original → shifted arrows for V4."""
    orig_rgb = get_stim_rgb()

    fig, axes = plt.subplots(1, 2, figsize=(12, 5.5),
                              subplot_kw={'projection': 'polar'})

    for ax_idx, subj in enumerate(['08', '09']):
        ax = axes[ax_idx]
        cvd_type = CVD_TYPE[subj]
        delta = compute_v4_delta(subj)
        if delta is None:
            ax.set_title(f'sub-{subj} (no data)', fontsize=10)
            continue

        fit = V4_FITS[subj]
        shifted_rgb = shift_stim_hue(delta)

        # Background color wheel
        n_bg = 360
        bg_hues = np.linspace(0, 360, n_bg, endpoint=False)
        bg_a = _CHROMA * np.cos(np.deg2rad(bg_hues))
        bg_b = _CHROMA * np.sin(np.deg2rad(bg_hues))
        bg_rgb = lab2rgb(np.full(n_bg, _L_STAR), bg_a, bg_b)
        for i in range(n_bg):
            ax.bar(np.deg2rad(bg_hues[i]), 0.25, width=np.deg2rad(1.2),
                   bottom=0.0, color=bg_rgb[i], alpha=0.25, edgecolor='none')

        ring_t = np.linspace(0, 2 * np.pi, 200)
        ax.plot(ring_t, np.full(200, 0.70), '-', color='#cccccc', lw=0.5)
        ax.plot(ring_t, np.full(200, 0.48), '-', color='#ffcccc', lw=0.5)

        for j in range(8):
            t_orig = np.deg2rad(HUE_ANGLES_DEG[j])
            t_shift = np.deg2rad((STIM_HUE_DEG[j] + delta[j]) % 360)

            ax.scatter(t_orig, 0.70, s=250, c=[orig_rgb[j]],
                       edgecolors='black', linewidths=1.5, zorder=5)
            ax.scatter(t_shift, 0.48, s=180, c=[shifted_rgb[j]],
                       edgecolors='red', linewidths=1.5, zorder=5, marker='D')
            if abs(delta[j]) > 2:
                ax.annotate('', xy=(t_shift, 0.54), xytext=(t_orig, 0.64),
                            arrowprops=dict(arrowstyle='->', color='red',
                                            lw=1.0, alpha=0.5,
                                            connectionstyle='arc3,rad=0.15'))

        ax.set_theta_zero_location('E')
        ax.set_theta_direction(1)
        ax.set_ylim(0, 0.95)
        ax.set_yticks([])
        ax.set_xticks(np.deg2rad(HUE_ANGLES_DEG))
        ax.set_xticklabels(COLOR_NAMES, fontsize=7)
        sig_sym = '*' if fit['p'] < 0.05 else ''
        ax.set_title(f'sub-{subj} ({cvd_type}) hV4\n'
                     f'Δλ={fit["params"][0]:.1f}nm '
                     + r'$\rho$' + f'={fit["rho"]:.2f}{sig_sym}',
                     fontsize=10, fontweight='bold', pad=15)

    legend_elements = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor='gray',
               markeredgecolor='black', markersize=10, label='Original (outer)'),
        Line2D([0], [0], marker='D', color='w', markerfacecolor='gray',
               markeredgecolor='red', markersize=8, label='CVD-shifted (inner)'),
    ]
    fig.legend(handles=legend_elements, loc='lower center', ncol=2,
               fontsize=9, bbox_to_anchor=(0.5, -0.02))
    fig.suptitle('hV4 Color Wheel: Original vs CVD Prediction (shift_at_both)',
                  fontsize=13, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(output_dir / 'color_wheel_v4.png', dpi=200,
                bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'  Saved: {output_dir / "color_wheel_v4.png"}')


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Visualize V4 shift_at_both cone-shift results')
    parser.add_argument('--output_dir', type=str,
                        default='figures/shift_at_both')
    args = parser.parse_args()

    output_dir = _SCRIPT_DIR.parent / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    print('=' * 60)
    print('V4 shift_at_both Visualization')
    print(f'Output: {output_dir}')
    print('=' * 60)

    print('\n[1] Color swatches...')
    plot_color_swatches(output_dir)

    print('\n[2] Color wheel...')
    plot_color_wheel(output_dir)

    print(f'\nAll figures saved to: {output_dir}')


if __name__ == '__main__':
    main()
