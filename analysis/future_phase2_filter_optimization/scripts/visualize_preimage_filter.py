#!/usr/bin/env python3
"""
visualize_preimage_filter.py — Figures for the pre-image filter search.

Runs locally (conda env: srm). Uses matplotlib only (no seaborn).

Figures:
  1. Per-color angle comparison (θ_target, θ_in*, D(θ_in*))
  2. Color wheel (inner=original, middle=pre-image, outer=perceived)
  3. Cross-sim sanity sweep (Δλ vs mean angular error)
  4. Fourier approximation quality (exact δ vs Fourier δ)

Usage:
    conda activate srm
    python scripts/visualize_preimage_filter.py \
        --preimage_dir results/fits/preimage \
        --eval_dir results/fits/preimage/evaluation \
        --output_dir results/fits/preimage/figures
"""

import argparse
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Wedge
from pathlib import Path
import sys

_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR))

_FWD_DIR = str(Path(__file__).resolve().parent.parent.parent.parent
               / 'future_phase1_forward_model' / 'scripts')
sys.path.insert(0, _FWD_DIR)

from visualize_cone_shift_colors import (  # noqa: E402
    STIM_LAB_ARR, STIM_L, STIM_A, STIM_B,
    STIM_CHROMA, STIM_HUE_DEG, lab2rgb, get_stim_rgb,
)

COLOR_NAMES = ['red', 'orange', 'yellow', 'green',
               'cyan', 'blue', 'purple', 'magenta']
HUE_ANGLES = np.array([0, 45, 90, 135, 180, 225, 270, 315], dtype=float)


def _lab_at_hue(hue_deg, L=75.0, C=40.0):
    """CIELab at given hue angle(s)."""
    h_rad = np.deg2rad(hue_deg)
    a = C * np.cos(h_rad)
    b = C * np.sin(h_rad)
    L_arr = np.full_like(np.atleast_1d(hue_deg), L)
    return L_arr, a, b


def _hue_to_rgb(hue_deg, L=75.0, C=40.0):
    """Convert idealized hue angle(s) to sRGB."""
    L_arr, a, b = _lab_at_hue(hue_deg, L, C)
    return lab2rgb(L_arr, a, b)


# ---------------------------------------------------------------------------
# Figure 1: Per-color angle comparison
# ---------------------------------------------------------------------------

def fig_angle_comparison(preimage, output_dir, subj_label):
    """3 bars per color: θ_target (blue), θ_in* (orange), D(θ_in*) (green)."""
    target = np.array(preimage.get('target_angles_opponent', preimage.get('target_angles')))
    theta_in = np.array(preimage['preimage_angles'])
    perceived = np.array(preimage['perceived_angles'])
    residuals = np.array(preimage['residuals'])

    x = np.arange(8)
    w = 0.25

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar(x - w, target, w, label='θ_target (original)', color='#4C72B0', alpha=0.8)
    ax.bar(x,     theta_in, w, label='θ_in* (pre-image)', color='#DD8452', alpha=0.8)
    ax.bar(x + w, perceived, w, label='D(θ_in*) perceived', color='#55A868', alpha=0.8)

    # Annotate residuals
    for i in range(8):
        ax.text(x[i] + w, perceived[i] + 5,
                f'{residuals[i]:.3f}°', ha='center', va='bottom',
                fontsize=7, color='#55A868')

    ax.set_xticks(x)
    ax.set_xticklabels([f'c{i+1}\n{COLOR_NAMES[i]}' for i in range(8)])
    ax.set_ylabel('Hue Angle (°)')
    ax.set_title(f'Pre-Image Filter: Per-Color Angle Comparison — {subj_label}')
    ax.legend(loc='upper left', fontsize=9)
    ax.set_ylim(0, 380)

    fig.tight_layout()
    path = output_dir / f'angle_comparison_{subj_label}.png'
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f'  Saved: {path}')


# ---------------------------------------------------------------------------
# Figure 2: Color wheel
# ---------------------------------------------------------------------------

def fig_color_wheel(preimage, output_dir, subj_label):
    """Inner=original, Middle=pre-image input, Outer=perceived output."""
    target = np.array(preimage.get('target_angles_opponent', preimage.get('target_angles')))
    theta_in = np.array(preimage['preimage_angles'])
    perceived = np.array(preimage['perceived_angles'])

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={'polar': True})
    ax.set_theta_zero_location('E')
    ax.set_theta_direction(1)

    # Draw rings
    rings = [
        (target,    0.6, 0.8, 'Original (target)'),
        (theta_in,  0.85, 1.05, 'Pre-image input'),
        (perceived, 1.1, 1.3, 'Perceived output'),
    ]

    for angles, r_in, r_out, label in rings:
        rgbs = _hue_to_rgb(angles)
        for i in range(8):
            theta_rad = np.deg2rad(angles[i])
            width = np.deg2rad(40)  # angular width
            wedge_theta = np.linspace(theta_rad - width/2,
                                      theta_rad + width/2, 30)
            # Draw as scatter approximation
            for r in np.linspace(r_in, r_out, 8):
                ax.scatter(wedge_theta, np.full_like(wedge_theta, r),
                           c=[rgbs[i]], s=5, marker='s')

    # Arrows from pre-image to perceived
    for i in range(8):
        ax.annotate('',
                    xy=(np.deg2rad(perceived[i]), 1.15),
                    xytext=(np.deg2rad(theta_in[i]), 0.95),
                    arrowprops=dict(arrowstyle='->', color='gray',
                                   lw=1, alpha=0.5))

    ax.set_rticks([])
    ax.set_title(f'Color Wheel: Pre-Image Filter — {subj_label}',
                 pad=20, fontsize=12)

    # Legend
    ax.text(0.02, 0.98, 'Inner: Original\nMiddle: Pre-image\nOuter: Perceived',
            transform=ax.transAxes, fontsize=8, va='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    fig.tight_layout()
    path = output_dir / f'color_wheel_{subj_label}.png'
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f'  Saved: {path}')


# ---------------------------------------------------------------------------
# Figure 3: Cross-sim sanity sweep
# ---------------------------------------------------------------------------

def fig_cross_sim_sweep(cross_sim_data, output_dir):
    """X: Δλ (nm), Y: mean angular error (°). Lines for 3 conditions."""
    # Collect all subjects
    subjects = {}
    for key, cs in cross_sim_data.items():
        if 'delta_lambda_range' not in cs:
            continue
        subjects[key] = cs

    if not subjects:
        print('  No cross-sim data to plot')
        return

    n_subj = len(subjects)
    fig, axes = plt.subplots(1, n_subj, figsize=(6 * n_subj, 5), squeeze=False)

    for idx, (key, cs) in enumerate(subjects.items()):
        ax = axes[0, idx]
        dl = np.array(cs['delta_lambda_range'])

        ax.plot(dl, cs['error_unfiltered'], 'b-', lw=2, label='Unfiltered')
        ax.plot(dl, cs['error_preimage'], 'g-', lw=2, label='Pre-image')
        ax.plot(dl, cs['error_simple_inverse'], 'r--', lw=1.5,
                label='Simple inverse', alpha=0.7)

        # Vertical line at fitted Δλ
        if 'fitted_delta_lambda' in cs:
            ax.axvline(cs['fitted_delta_lambda'], color='gray',
                       ls=':', lw=1, alpha=0.7)
            ax.text(cs['fitted_delta_lambda'] + 0.3, ax.get_ylim()[1] * 0.9,
                    f'Δλ={cs["fitted_delta_lambda"]}',
                    fontsize=8, color='gray')

        ax.set_xlabel('Δλ (nm)')
        ax.set_ylabel('Mean Angular Error (°)')
        ax.set_title(f'Cross-Simulator Sanity Check\n{key}')
        ax.legend(fontsize=9)
        ax.set_xlim(dl[0], dl[-1])

    fig.tight_layout()
    path = output_dir / 'cross_sim_sanity.png'
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f'  Saved: {path}')


# ---------------------------------------------------------------------------
# Figure 4: Fourier approximation quality
# ---------------------------------------------------------------------------

def fig_fourier_fit(preimage, output_dir, subj_label):
    """Per-color: exact δ_preimage (circles) vs Fourier δ (line)."""
    delta_exact = np.array(preimage['delta_preimage'])
    fourier = preimage['fourier_approx']
    delta_fourier = np.array(fourier['delta_smooth'])
    rmse = fourier['rmse_vs_exact']

    # Continuous curve
    theta_fine = np.linspace(0, 360, 361)
    coeffs = fourier['coeffs']
    theta_rad = np.deg2rad(theta_fine)
    delta_fine = np.zeros_like(theta_fine)
    n_harm = fourier.get('n_harmonics', 2)
    for k in range(1, n_harm + 1):
        delta_fine += coeffs[f'a{k}'] * np.sin(k * theta_rad)
        delta_fine += coeffs[f'b{k}'] * np.cos(k * theta_rad)

    fig, ax = plt.subplots(figsize=(10, 5))

    # Fourier curve
    ax.plot(theta_fine, delta_fine, 'b-', lw=1.5, alpha=0.7,
            label=f'Fourier ({2*n_harm}-DOF)')

    # Exact points
    ax.scatter(HUE_ANGLES, delta_exact, c='red', s=80, zorder=5,
               label='Exact pre-image', edgecolors='black', linewidths=0.5)

    # Fourier at sample points
    ax.scatter(HUE_ANGLES, delta_fourier, c='blue', s=40, zorder=4,
               marker='D', label='Fourier at stimuli', alpha=0.7)

    # Connect exact to Fourier
    for i in range(8):
        ax.plot([HUE_ANGLES[i], HUE_ANGLES[i]],
                [delta_exact[i], delta_fourier[i]],
                'k-', lw=0.5, alpha=0.3)

    ax.axhline(0, color='gray', ls=':', lw=0.5)
    ax.set_xlabel('Original Hue Angle (°)')
    ax.set_ylabel('Correction δ (°)')
    ax.set_title(f'Fourier Approximation Quality — {subj_label}\n'
                 f'RMSE = {rmse:.3f}°')
    ax.legend(fontsize=9)
    ax.set_xticks(HUE_ANGLES)
    ax.set_xticklabels([f'{int(h)}°\n{COLOR_NAMES[i]}'
                        for i, h in enumerate(HUE_ANGLES)], fontsize=8)

    fig.tight_layout()
    path = output_dir / f'fourier_approximation_{subj_label}.png'
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f'  Saved: {path}')


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Visualize pre-image filter results (local only)')
    parser.add_argument('--preimage_dir', required=True,
                        help='Directory with preimage JSON files')
    parser.add_argument('--eval_dir', default=None,
                        help='Evaluation directory (default: preimage_dir/evaluation)')
    parser.add_argument('--output_dir', default=None,
                        help='Figure output (default: preimage_dir/figures)')
    args = parser.parse_args()

    preimage_dir = Path(args.preimage_dir)
    eval_dir = Path(args.eval_dir) if args.eval_dir else preimage_dir / 'evaluation'
    output_dir = Path(args.output_dir) if args.output_dir else preimage_dir / 'figures'
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load preimage results
    preimage_files = sorted(preimage_dir.glob('*_preimage.json'))
    if not preimage_files:
        print(f'ERROR: No preimage JSON files in {preimage_dir}')
        sys.exit(1)

    print(f'Found {len(preimage_files)} preimage results')

    for pf in preimage_files:
        with open(pf) as f:
            preimage = json.load(f)

        subj = preimage['subject']
        model = preimage['model']
        subj_label = f'sub-{subj}_{model}'

        print(f'\n--- {subj_label} ---')

        # Fig 1: Angle comparison
        fig_angle_comparison(preimage, output_dir, subj_label)

        # Fig 2: Color wheel
        fig_color_wheel(preimage, output_dir, subj_label)

        # Fig 4: Fourier fit
        fig_fourier_fit(preimage, output_dir, subj_label)

    # Fig 3: Cross-sim sweep (from evaluation)
    cs_path = eval_dir / 'cross_sim_sanity.json'
    if cs_path.exists():
        with open(cs_path) as f:
            cross_sim = json.load(f)
        print(f'\n--- Cross-sim sweep ---')
        fig_cross_sim_sweep(cross_sim, output_dir)
    else:
        print(f'\nSkipping cross-sim figure ({cs_path} not found)')

    print(f'\nAll figures saved to {output_dir}/')


if __name__ == '__main__':
    main()
