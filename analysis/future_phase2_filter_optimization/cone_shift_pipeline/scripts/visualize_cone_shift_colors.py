#!/usr/bin/env python3
"""
visualize_cone_shift_colors.py — Visualize modified colors from cone-shift pipeline results.

Uses ACTUAL experimental CIELab values and VALIDATED ΔRDM simulation results
(RESULTS_SIM.md) — NOT the older SRM-based LOCO multimodel fitting.

Data sources:
  - V1/V2: results/sim/{sub}_{roi}_{model}_{metric}/result.json  (ΔRDM Phase A+C)
  - V4: hardcoded shift_at_both values (different pipeline)

Key findings (RESULTS_SIM.md):
  - ONLY fully significant: sub-09 V2 cone_1way×cosine (δ*=47.7nm, LOCO ρ=0.810*)
  - Trending: sub-08 V1/V2 fourier×cosine (LOCO ρ≈0.57-0.62†)
  - sub-08 cone models FAIL LOCO reproduction (all negative ρ)

Figures:
  Fig 1: Color swatches — Original | CVD-perceived | Filter-corrected (V4)
  Fig 2: Polar distortion |δθ| across ROIs
  Fig 3: Color wheel with original → shifted arrows
  Fig 4: Per-color δθ bars (significant + trending)
  Fig 5: Continuous distortion curve δθ(θ)

Usage:
    conda activate srm
    python scripts/visualize_cone_shift_colors.py [--output_dir figures]
"""

import argparse
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from pathlib import Path
import sys

# ============================================================================
# Path setup
# ============================================================================
_SCRIPT_DIR = Path(__file__).resolve().parent
_FWD_DIR = str(_SCRIPT_DIR.parent.parent.parent / 'future_phase1_forward_model' / 'scripts')
if _FWD_DIR not in sys.path:
    sys.path.insert(0, _FWD_DIR)
sys.path.insert(0, str(_SCRIPT_DIR))

from stockman_cone_shift import COLOR_NAMES, HUE_ANGLES_DEG
from utils_cone_3way import compute_shifted_hue_3way, compute_1way_hue_shift

# ============================================================================
# Actual experimental stimulus colors (from utils_color_decoding.py)
# ============================================================================
STIM_LAB = {
    'color_1': [59.90, 62.69, 3.78],    # 0°  Red
    'color_2': [64.20, 49.20, 45.58],   # 45° Orange
    'color_3': [57.27, 13.06, 41.69],   # 90° Yellow/Brown
    'color_4': [69.08, -55.02, 47.38],  # 135° Green
    'color_5': [74.61, -41.33, -4.89],  # 180° Cyan
    'color_6': [69.14, -11.45, -40.91], # 225° Blue
    'color_7': [60.68, 19.18, -54.13],  # 270° Purple
    'color_8': [60.17, 46.82, -40.31],  # 315° Magenta
}

STIM_LAB_ARR = np.array([STIM_LAB[f'color_{i+1}'] for i in range(8)])
STIM_L = STIM_LAB_ARR[:, 0]
STIM_A = STIM_LAB_ARR[:, 1]
STIM_B = STIM_LAB_ARR[:, 2]
STIM_CHROMA = np.sqrt(STIM_A**2 + STIM_B**2)
STIM_HUE_DEG = np.rad2deg(np.arctan2(STIM_B, STIM_A)) % 360

# ============================================================================
# CIELab → sRGB conversion (matches lab2rgb_accurate from utils_color_decoding)
# ============================================================================

_M_XYZ_TO_SRGB = np.array([
    [3.2406, -1.5372, -0.4986],
    [-0.9689,  1.8758,  0.0415],
    [0.0557, -0.2040,  1.0570],
])


def lab2rgb(L, a, b):
    """CIELab → sRGB [0,1], scalar or array."""
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
    """Get sRGB array (8,3) for the 8 actual experimental colors."""
    return lab2rgb(STIM_L, STIM_A, STIM_B)


def shift_stim_hue(delta_deg):
    """Shift each stimulus color's hue by delta_deg[i] while keeping L* and chroma.

    Note: delta_deg are from Stockman opponent hue space; applying to CIELab hues
    is an approximation sufficient for visualization.
    """
    new_hue_rad = np.deg2rad(STIM_HUE_DEG + np.asarray(delta_deg))
    new_a = STIM_CHROMA * np.cos(new_hue_rad)
    new_b = STIM_CHROMA * np.sin(new_hue_rad)
    shifted_rgb = lab2rgb(STIM_L, new_a, new_b)
    return shifted_rgb


# ============================================================================
# Results loading — from VALIDATED ΔRDM simulation pipeline
# ============================================================================
RESULTS_BASE = _SCRIPT_DIR.parent / 'results'
SIM_DIR = RESULTS_BASE / 'sim'

# V4 results from shift_at_both method (separate pipeline, validated)
V4_FITS = {
    '08': {'model': 'cone_1way', 'params': [8.639], 'cvd_type': 'deutan',
           'rho': 0.690, 'p': 0.036, 'source': 'shift_at_both'},
    '09': {'model': 'cone_1way', 'params': [25.204], 'cvd_type': 'protan',
           'rho': 0.833, 'p': 0.009, 'source': 'shift_at_both'},
}

CVD_TYPE = {'08': 'deutan', '09': 'protan', '10': 'normal'}

# Define which sim results to load (from RESULTS_SIM.md top findings, cosine metric)
SIM_CONFIGS = [
    # (subj, roi, model, metric) — All use cosine metric (dominant per RESULTS_SIM.md)
    ('09', 'V2', 'cone_1way', 'cosine'),   # ONLY fully significant
    ('09', 'V2', 'cone_3way', 'cosine'),   # trending
    ('08', 'V1', 'fourier', 'cosine'),      # trending
    ('08', 'V2', 'fourier', 'cosine'),      # trending
    # NS results — still loaded for visualization completeness
    ('09', 'V1', 'cone_1way', 'cosine'),    # Phase A sig but Phase C NS (p=.44)
    ('08', 'V1', 'cone_1way', 'cosine'),    # NS (cone fails for deutan)
    ('08', 'V2', 'cone_1way', 'cosine'),    # NS
]


def load_sim_results():
    """Load validated simulation results from results/sim/ directory."""
    results = {}
    for subj, roi, model, metric in SIM_CONFIGS:
        dirname = f'sub-{subj}_{roi}_{model}_{metric}'
        result_path = SIM_DIR / dirname / 'result.json'
        if not result_path.exists():
            print(f"  [WARN] Missing: {result_path}")
            continue

        with open(result_path) as f:
            data = json.load(f)

        pa = data['phase_a']
        pc = data['phase_c']

        # Determine significance level
        pa_sig = pa.get('significant', False) and pa['perm_p'] < 0.05
        pc_perm_p = pc['loco_match']['perm_p']
        pc_rho = pc['loco_match']['spearman_rho']

        if pa_sig and pc_perm_p < 0.05:
            sig_level = 'significant'
        elif pa_sig and pc_perm_p < 0.10:
            sig_level = 'trending'
        else:
            sig_level = 'ns'

        key = (subj, roi, model, metric)
        results[key] = {
            'subj': subj, 'roi': roi, 'model': model, 'metric': metric,
            'cvd_type': CVD_TYPE[subj],
            'params': pa['best_params'],
            'delta_theta_deg': np.array(pa['delta_theta_deg']),
            'rdm_r': pa['best_pearson_r'],
            'rdm_p': pa['perm_p'],
            'loco_rho': pc_rho,
            'loco_p': pc_perm_p,
            'worst3_syn': pc['loco_match'].get('worst3_synthetic', []),
            'worst3_obs': pc['loco_match'].get('worst3_observed', []),
            'worst3_overlap': pc['loco_match'].get('worst3_overlap', 0),
            'sig_level': sig_level,
        }

    return results


def get_best_per_roi(sim_results):
    """Select best model per (subject, roi) — prefer significant > trending > ns,
    then lower df (parsimony), then higher LOCO rho."""
    best = {}
    rank = {'significant': 0, 'trending': 1, 'ns': 2}
    df_map = {'cone_1way': 1, 'cone_3way': 3, 'fourier': 4}

    for key, res in sim_results.items():
        subj, roi = res['subj'], res['roi']
        sr_key = (subj, roi)
        if sr_key not in best:
            best[sr_key] = res
        else:
            cur = best[sr_key]
            cur_rank = rank[cur['sig_level']]
            new_rank = rank[res['sig_level']]
            if (new_rank < cur_rank or
                (new_rank == cur_rank and df_map.get(res['model'], 99) < df_map.get(cur['model'], 99)) or
                (new_rank == cur_rank and df_map.get(res['model'], 99) == df_map.get(cur['model'], 99) and
                 res['loco_rho'] > cur['loco_rho'])):
                best[sr_key] = res
    return best


def compute_v4_delta(subj):
    """Compute delta_theta for V4 shift_at_both cone_1way results."""
    fit = V4_FITS.get(subj)
    if fit is None:
        return None
    _, _, delta = compute_1way_hue_shift(fit['params'][0], fit['cvd_type'])
    return delta


# ============================================================================
# Figure 1: Color Swatches — Original | CVD-perceived | Filter-corrected (V4)
# ============================================================================

def plot_color_swatches(output_dir, sim_results):
    """Three-row swatch per CVD subject using V4 (shift_at_both) results."""

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
        p = fit['p']

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

    fig.suptitle('Cone-Shift Model: Perceived vs Filter-Corrected Colors (hV4, shift_at_both)',
                  fontsize=13, fontweight='bold', y=0.99)
    fig.text(0.5, 0.005,
             'CVD Perceived = what CVD brain encodes (hue shifted by +' +
             r'$\delta\theta$' + ') | Filter Corrected = pre-compensated stimulus '
             '(shifted by ' + r'$-\delta\theta$' + ')',
             ha='center', fontsize=8, style='italic', color='gray')

    plt.savefig(output_dir / 'color_swatches_hV4.png', dpi=200,
                bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  Saved: {output_dir / 'color_swatches_hV4.png'}")


# ============================================================================
# Figure 2: Polar Distortion Profile across ROIs
# ============================================================================

def plot_polar_distortion(output_dir, best_per_roi):
    """Polar radar of |delta_theta| per color across ROIs."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.5),
                              subplot_kw={'projection': 'polar'})

    stim_rgb = get_stim_rgb()
    roi_colors = {'V1': '#2196F3', 'V2': '#4CAF50', 'V4': '#FF9800'}
    roi_styles = {'V1': '-', 'V2': '--', 'V4': '-.'}
    theta_base = np.deg2rad(HUE_ANGLES_DEG)
    theta_plot = np.append(theta_base, theta_base[0])

    for ax_idx, subj in enumerate(['08', '09']):
        ax = axes[ax_idx]
        cvd_type = CVD_TYPE[subj]

        for j in range(8):
            ax.scatter(theta_base[j], 0, s=120, c=[stim_rgb[j]],
                       edgecolors='black', linewidths=0.8, zorder=10, clip_on=False)

        for roi in ['V1', 'V2', 'V4']:
            if roi == 'V4':
                delta = compute_v4_delta(subj)
                if delta is None:
                    continue
                fit = V4_FITS[subj]
                model = fit['model']
                rho = fit['rho']
                p = fit['p']
            else:
                res = best_per_roi.get((subj, roi))
                if res is None:
                    continue
                delta = res['delta_theta_deg']
                model = res['model']
                rho = res['loco_rho']
                p = res['loco_p']

            mag = np.abs(delta)
            mag_plot = np.append(mag, mag[0])
            sig_sym = '*' if p < 0.05 else ('\u2020' if p < 0.10 else '')
            label = f'{roi} ({model[:7]}) ' + r'$\rho$' + f'={rho:.2f}{sig_sym}'
            alpha = 0.9 if p < 0.05 else (0.6 if p < 0.10 else 0.3)
            ax.plot(theta_plot, mag_plot, roi_styles[roi],
                    color=roi_colors[roi], linewidth=2, label=label, alpha=alpha)
            ax.fill(theta_plot, mag_plot, alpha=0.06, color=roi_colors[roi])

        ax.set_theta_zero_location('E')
        ax.set_theta_direction(1)
        ax.set_xticks(theta_base)
        ax.set_xticklabels(COLOR_NAMES, fontsize=7)
        ax.set_title(f'sub-{subj} ({cvd_type})', fontsize=11,
                      fontweight='bold', pad=15)
        ax.legend(loc='upper right', fontsize=7, bbox_to_anchor=(1.35, 1.15))

    fig.suptitle('Hue Distortion Magnitude |' + r'$\delta\theta$' +
                  '| by ROI (cosine metric, RESULTS_SIM.md)',
                  fontsize=13, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(output_dir / 'polar_distortion_by_roi.png', dpi=200,
                bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  Saved: {output_dir / 'polar_distortion_by_roi.png'}")


# ============================================================================
# Figure 3: Color Wheel with Shift Arrows
# ============================================================================

def plot_color_wheel(output_dir, best_per_roi):
    """Color wheel: actual stimulus colors with shift arrows."""

    panels = [
        ('08', 'V4', 'sub-08 deutan \u2014 hV4'),
        ('09', 'V4', 'sub-09 protan \u2014 hV4'),
        ('09', 'V2', 'sub-09 protan \u2014 V2'),
        ('08', 'V1', 'sub-08 deutan \u2014 V1'),
        ('08', 'V2', 'sub-08 deutan \u2014 V2'),
        ('09', 'V1', 'sub-09 protan \u2014 V1'),
    ]

    fig, axes = plt.subplots(2, 3, figsize=(15, 10),
                              subplot_kw={'projection': 'polar'})

    orig_rgb = get_stim_rgb()

    for idx, (subj, roi, title) in enumerate(panels):
        row, col = divmod(idx, 3)
        ax = axes[row, col]
        cvd_type = CVD_TYPE[subj]

        # Get delta and metadata
        if roi == 'V4':
            delta = compute_v4_delta(subj)
            if delta is None:
                ax.set_title(title + ' (no data)', fontsize=10)
                ax.set_yticks([])
                continue
            fit = V4_FITS[subj]
            model = fit['model']
            rho, p = fit['rho'], fit['p']
            source = 'shift_at_both'
        else:
            res = best_per_roi.get((subj, roi))
            if res is None:
                ax.set_title(f'{title} (no data)', fontsize=10)
                ax.set_yticks([])
                continue
            delta = res['delta_theta_deg']
            model = res['model']
            rho, p = res['loco_rho'], res['loco_p']
            source = f"ΔRDM {res['metric']}"

        shifted_rgb = shift_stim_hue(delta)

        # Background color wheel
        n_bg = 360
        bg_hues = np.linspace(0, 360, n_bg, endpoint=False)
        med_L = np.median(STIM_L)
        med_C = np.median(STIM_CHROMA)
        bg_a = med_C * np.cos(np.deg2rad(bg_hues))
        bg_b = med_C * np.sin(np.deg2rad(bg_hues))
        bg_rgb = lab2rgb(np.full(n_bg, med_L), bg_a, bg_b)
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
        sig_sym = '*' if p < 0.05 else ('\u2020' if p < 0.10 else 'ns')
        ax.set_title(f'{title}\n{model} LOCO ' +
                      r'$\rho$' + f'={rho:.2f}{sig_sym} [{source}]',
                      fontsize=8, fontweight='bold', pad=15)

    legend_elements = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor='gray',
               markeredgecolor='black', markersize=10, label='Original (outer)'),
        Line2D([0], [0], marker='D', color='w', markerfacecolor='gray',
               markeredgecolor='red', markersize=8, label='CVD-shifted (inner)'),
    ]
    fig.legend(handles=legend_elements, loc='lower center', ncol=2,
               fontsize=9, bbox_to_anchor=(0.5, -0.02))
    fig.suptitle('Color Wheel: Original vs Predicted CVD Perception\n'
                 '(* p<.05, \u2020 p<.10 — ΔRDM cosine metric)',
                  fontsize=13, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(output_dir / 'color_wheel_shifts.png', dpi=200,
                bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  Saved: {output_dir / 'color_wheel_shifts.png'}")


# ============================================================================
# Figure 4: Delta-theta Bar Chart (Phase A significant only)
# ============================================================================

def plot_delta_theta_bars(output_dir, sim_results, best_per_roi):
    """Bar chart of per-color delta_theta for Phase A+C validated results."""

    stim_rgb = get_stim_rgb()

    # Collect: Phase A significant results (include trending for completeness)
    panels = []
    for key, res in sim_results.items():
        if res['sig_level'] in ('significant', 'trending'):
            panels.append(res)

    # Add V4 results
    for subj in ['08', '09']:
        delta = compute_v4_delta(subj)
        if delta is not None:
            fit = V4_FITS[subj]
            panels.append({
                'subj': subj, 'roi': 'V4', 'model': fit['model'],
                'cvd_type': CVD_TYPE[subj], 'delta_theta_deg': delta,
                'loco_rho': fit['rho'], 'loco_p': fit['p'],
                'rdm_r': None, 'rdm_p': None,
                'sig_level': 'significant',
                'metric': 'shift_at_both',
            })

    # Sort: significant first, then by subject, roi
    panels.sort(key=lambda x: (0 if x['sig_level'] == 'significant' else 1,
                                 x['subj'], x['roi']))

    if not panels:
        print("  [SKIP] No significant/trending results.")
        return

    n = len(panels)
    fig, axes = plt.subplots(1, n, figsize=(3.5 * n, 4.5), sharey=True)
    if n == 1:
        axes = [axes]
    x = np.arange(8)

    for idx, res in enumerate(panels):
        ax = axes[idx]
        delta = res['delta_theta_deg']
        bars = ax.bar(x, delta,
                       color=[stim_rgb[j] for j in range(8)],
                       edgecolor='black', linewidth=0.8)
        for j, bar in enumerate(bars):
            if abs(delta[j]) > 10:
                bar.set_edgecolor('red'); bar.set_linewidth(2)

        ax.axhline(0, color='gray', lw=0.8)
        ax.set_xticks(x)
        ax.set_xticklabels(COLOR_NAMES, fontsize=7, rotation=45, ha='right')
        ax.set_ylabel(r'$\delta\theta$ (deg)' if idx == 0 else '', fontsize=10)

        sig_sym = '*' if res['sig_level'] == 'significant' else '\u2020'
        rho = res['loco_rho']
        metric = res.get('metric', '')
        rdm_r = res.get('rdm_r')

        title_lines = [f"sub-{res['subj']} ({res['cvd_type']}) \u2014 {res['roi']}"]
        title_lines.append(f"{res['model']} LOCO " + r'$\rho$' + f"={rho:.2f}{sig_sym}")
        if rdm_r is not None:
            title_lines[-1] += f" | ΔRDM r={rdm_r:.2f}"

        ax.set_title('\n'.join(title_lines), fontsize=8, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)

        # Highlight border for significant vs trending
        if res['sig_level'] == 'significant':
            for spine in ax.spines.values():
                spine.set_linewidth(2.5)
                spine.set_color('#2E7D32')
        elif res['sig_level'] == 'trending':
            for spine in ax.spines.values():
                spine.set_linewidth(1.5)
                spine.set_color('#FF8F00')

    fig.suptitle('Per-Color Hue Distortion ' + r'$\delta\theta$' +
                  ' (Validated: ΔRDM + LOCO)\n'
                  'Green border = significant (p<.05), Orange = trending (p<.10)',
                  fontsize=11, fontweight='bold', y=1.04)
    plt.tight_layout()
    plt.savefig(output_dir / 'delta_theta_bars.png', dpi=200,
                bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  Saved: {output_dir / 'delta_theta_bars.png'}")


# ============================================================================
# Figure 5: Continuous Distortion Curve
# ============================================================================

def plot_continuous_distortion(output_dir, sim_results, best_per_roi):
    """Continuous delta_theta(theta) for validated models."""
    from scipy.interpolate import CubicSpline

    stim_rgb = get_stim_rgb()
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    theta_fine = np.linspace(0, 360, 361)

    for ax_idx, subj in enumerate(['08', '09']):
        ax = axes[ax_idx]
        cvd_type = CVD_TYPE[subj]

        # V4 (shift_at_both)
        delta_v4 = compute_v4_delta(subj)
        if delta_v4 is not None:
            fit = V4_FITS[subj]
            _, _, delta_8 = compute_1way_hue_shift(fit['params'][0], fit['cvd_type'])
            delta_uw = np.rad2deg(np.unwrap(np.deg2rad(delta_8)))
            x_p = np.append(HUE_ANGLES_DEG, 360.0)
            y_p = np.append(delta_uw, delta_uw[0])
            cs = CubicSpline(x_p, y_p, bc_type='periodic')
            delta_fine = cs(theta_fine)
            p_v4 = fit['p']
            sig = '*' if p_v4 < 0.05 else ''
            ax.plot(theta_fine, delta_fine, '-.', color='#FF9800', lw=2,
                    label=f'V4 (cone_1w) p={p_v4:.3f}{sig}', alpha=0.9)

        # V1/V2 from ΔRDM sim results
        for roi, clr, ls in [('V1', '#2196F3', '-'), ('V2', '#4CAF50', '--')]:
            res = best_per_roi.get((subj, roi))
            if res is None:
                continue

            model = res['model']
            params = res['params']
            p_loco = res['loco_p']

            if model in ('cone_1way', 'cone_3way'):
                if model == 'cone_1way':
                    _, _, delta_8 = compute_1way_hue_shift(params[0], cvd_type)
                else:
                    _, _, delta_8 = compute_shifted_hue_3way(*params)
                delta_uw = np.rad2deg(np.unwrap(np.deg2rad(delta_8)))
                x_p = np.append(HUE_ANGLES_DEG, 360.0)
                y_p = np.append(delta_uw, delta_uw[0])
                cs = CubicSpline(x_p, y_p, bc_type='periodic')
                delta_fine = cs(theta_fine)
            elif model == 'fourier':
                a1, b1, a2, b2 = params
                tr = np.deg2rad(theta_fine)
                delta_fine = (a1 * np.cos(tr) + b1 * np.sin(tr) +
                              a2 * np.cos(2 * tr) + b2 * np.sin(2 * tr))
            else:
                continue

            sig_sym = '*' if p_loco < 0.05 else ('\u2020' if p_loco < 0.10 else ' ns')
            alpha = 0.9 if p_loco < 0.05 else (0.6 if p_loco < 0.10 else 0.3)
            ax.plot(theta_fine, delta_fine, ls, color=clr, lw=2,
                    label=f'{roi} ({model[:7]}) LOCO p={p_loco:.3f}{sig_sym}',
                    alpha=alpha)

        for j in range(8):
            ax.axvline(HUE_ANGLES_DEG[j], color=stim_rgb[j], alpha=0.35, lw=8)

        ax.axhline(0, color='gray', lw=0.8, ls=':')
        ax.set_xlabel('Hue Angle ' + r'$\theta$' + ' (deg)', fontsize=10)
        ax.set_ylabel(r'$\delta\theta$ (deg)', fontsize=10)
        ax.set_title(f'sub-{subj} ({cvd_type})', fontsize=11, fontweight='bold')
        ax.set_xticks(HUE_ANGLES_DEG)
        ax.set_xticklabels(COLOR_NAMES, fontsize=7, rotation=45, ha='right')
        ax.legend(fontsize=8)
        ax.grid(alpha=0.2)
        ax.set_xlim(0, 360)

    fig.suptitle('Continuous Hue Distortion Profile ' +
                  r'$\delta\theta(\theta)$' + ' \u2014 ΔRDM Cosine Metric',
                  fontsize=13, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(output_dir / 'continuous_distortion_curve.png', dpi=200,
                bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  Saved: {output_dir / 'continuous_distortion_curve.png'}")


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Visualize modified colors from cone-shift pipeline results')
    parser.add_argument('--output_dir', type=str, default='figures')
    args = parser.parse_args()

    output_dir = _SCRIPT_DIR.parent / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    print('=' * 60)
    print('Cone-Shift Color Visualization')
    print('Source: RESULTS_SIM.md (ΔRDM Phase A + LOCO Phase C)')
    print(f'Output: {output_dir}')
    print('=' * 60)

    print('\n[1] Loading ΔRDM simulation results...')
    sim_results = load_sim_results()
    best_per_roi = get_best_per_roi(sim_results)

    print('\n[2] Summary of validated fits (cosine metric):')
    print('\n  === V4 (shift_at_both method) ===')
    for subj in ['08', '09']:
        fit = V4_FITS[subj]
        print(f"  sub-{subj} ({CVD_TYPE[subj]}): {fit['model']} "
              f"delta={fit['params'][0]:.1f}nm rho={fit['rho']:.3f} p={fit['p']:.4f}*")

    print('\n  === V1/V2 (ΔRDM simulation) ===')
    for key in sorted(sim_results.keys()):
        res = sim_results[key]
        is_best = best_per_roi.get((res['subj'], res['roi'])) is res
        marker = ' <-- BEST' if is_best else ''
        sig_sym = '*' if res['sig_level'] == 'significant' else ('\u2020' if res['sig_level'] == 'trending' else '')
        print(f"  sub-{res['subj']} {res['roi']} {res['model']}x{res['metric']}: "
              f"ΔRDM r={res['rdm_r']:.3f} (p={res['rdm_p']:.4f}) | "
              f"LOCO rho={res['loco_rho']:.3f} (p={res['loco_p']:.4f}) "
              f"[{res['sig_level']}{sig_sym}]{marker}")

    print('\n[3] Generating figures...')

    print('\n  -- Color swatches (hV4 shift_at_both) --')
    plot_color_swatches(output_dir, sim_results)

    print('\n  -- Polar distortion profile --')
    plot_polar_distortion(output_dir, best_per_roi)

    print('\n  -- Color wheel shifts --')
    plot_color_wheel(output_dir, best_per_roi)

    print('\n  -- Delta-theta bar chart --')
    plot_delta_theta_bars(output_dir, sim_results, best_per_roi)

    print('\n  -- Continuous distortion curves --')
    plot_continuous_distortion(output_dir, sim_results, best_per_roi)

    print(f'\n{"=" * 60}')
    print(f'All figures saved to: {output_dir}')
    print('=' * 60)


if __name__ == '__main__':
    main()
