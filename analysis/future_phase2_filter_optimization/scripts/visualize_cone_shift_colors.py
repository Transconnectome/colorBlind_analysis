#!/usr/bin/env python3
"""
visualize_cone_shift_colors.py — Unified visualization for the ΔRDM cone-shift pipeline.

Pipeline: ΔRDM-based fitting (Phase A) → LOCO reproduction (Phase C)
Models: cone_1way (df=1), cone_3way (df=3), fourier (df=4)
Metrics: cosine (primary), correlation, triangle, combination

Data source: results/sim/{sub}_{roi}_{model}_{metric}/result.json
Reference:   RESULTS_SIM.md (validated results summary)

Stimulus colors use screenshot-derived CIELab values (from utils_color_decoding.py)
which faithfully represent what subjects actually saw on the monitor.
Model coordinates use idealized L*=75/chroma=40 (for cone shift computation only).

Figures:
  Fig 1: Color swatches — Original | CVD-perceived | Filter-corrected
  Fig 2: Per-color δθ bars (significant + trending, ΔRDM + LOCO validated)
  Fig 3: Color wheel with original → shifted arrows
  Fig 4: Continuous distortion curve δθ(θ) across ROIs

Usage:
    conda activate srm
    python scripts/visualize_cone_shift_colors.py [--output_dir figures]
"""

import argparse
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch
from pathlib import Path
from scipy.interpolate import CubicSpline
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
# Stimulus colors: screenshot-derived CIELab (actual monitor appearance)
#
# These values were extracted from actual experiment screenshots and represent
# what subjects saw. They differ from the idealized L*=75/chroma=40 specification
# due to monitor color profile and sRGB gamut mapping.
# Source: analysis/utils/utils_color_decoding.py
# ============================================================================
STIM_LAB = {
    'color_1': [59.90, 62.69, 3.78],    # 0°  Red
    'color_2': [64.20, 49.20, 45.58],   # 45° Orange
    'color_3': [57.27, 13.06, 41.69],   # 90° Yellow
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
# CIELab → sRGB conversion
# ============================================================================
_M_XYZ_TO_SRGB = np.array([
    [3.2406, -1.5372, -0.4986],
    [-0.9689,  1.8758,  0.0415],
    [0.0557, -0.2040,  1.0570],
])


def lab2rgb(L, a, b):
    """CIELab → sRGB [0,1]. Matches lab2rgb_accurate in utils_color_decoding.py."""
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
    """Get sRGB (8,3) for the 8 actual experimental colors."""
    return lab2rgb(STIM_L, STIM_A, STIM_B)


def shift_stim_hue(delta_deg):
    """Shift each stimulus color's hue by delta_deg[i] from the IDEALIZED position.

    Uses idealized hue angles (0,45,...,315) as the reference, but preserves
    per-color L* and chroma from screenshot-derived values for vivid rendering.
    """
    new_hue_rad = np.deg2rad(HUE_ANGLES_DEG + np.asarray(delta_deg))
    new_a = STIM_CHROMA * np.cos(new_hue_rad)
    new_b = STIM_CHROMA * np.sin(new_hue_rad)
    return lab2rgb(STIM_L, new_a, new_b)


# ============================================================================
# Constants
# ============================================================================
RESULTS_BASE = _SCRIPT_DIR.parent / 'results'
SIM_DIR = RESULTS_BASE / 'sim'
CVD_TYPE = {'08': 'deutan', '09': 'protan', '10': 'normal'}

ROI_COLORS = {'V1': '#2196F3', 'V2': '#4CAF50', 'V3': '#9C27B0', 'V4': '#FF9800'}
ROI_STYLES = {'V1': '-', 'V2': '--', 'V3': ':', 'V4': '-.'}

# ΔRDM sim configurations to load (cosine metric as primary)
SIM_CONFIGS = [
    # (subj, roi, model, metric)
    ('09', 'V2', 'cone_1way', 'cosine'),    # ONLY fully significant (A+C)
    ('09', 'V2', 'cone_3way', 'cosine'),    # trending
    ('08', 'V1', 'fourier', 'cosine'),       # trending
    ('08', 'V2', 'fourier', 'cosine'),       # trending
    ('09', 'V1', 'cone_1way', 'cosine'),     # Phase A sig, Phase C NS
    ('08', 'V1', 'cone_1way', 'cosine'),     # NS (cone fails for deutan)
    ('08', 'V2', 'cone_1way', 'cosine'),     # NS
    ('09', 'V1', 'cone_3way', 'cosine'),     # for cross-ROI comparison
    ('09', 'V1', 'fourier', 'cosine'),       # for cross-ROI comparison
    ('08', 'V1', 'cone_3way', 'cosine'),     # for cross-ROI comparison
    ('08', 'V2', 'cone_3way', 'cosine'),     # for cross-ROI comparison
    ('09', 'V2', 'fourier', 'cosine'),       # for cross-ROI comparison
]


# ============================================================================
# Load results
# ============================================================================

def load_sim_results():
    """Load ΔRDM simulation results from results/sim/ directory."""
    results = {}
    for subj, roi, model, metric in SIM_CONFIGS:
        dirname = f'sub-{subj}_{roi}_{model}_{metric}'
        result_path = SIM_DIR / dirname / 'result.json'
        if not result_path.exists():
            print(f'  [WARN] Missing: {result_path}')
            continue

        with open(result_path) as f:
            data = json.load(f)

        pa = data['phase_a']
        pc = data['phase_c']

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
    """Select best model per (subject, roi): significant > trending > ns,
    then lower df, then higher LOCO rho."""
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
                (new_rank == cur_rank and
                 df_map.get(res['model'], 99) < df_map.get(cur['model'], 99)) or
                (new_rank == cur_rank and
                 df_map.get(res['model'], 99) == df_map.get(cur['model'], 99) and
                 res['loco_rho'] > cur['loco_rho'])):
                best[sr_key] = res
    return best


# ============================================================================
# Fig 1: Color Swatches — Original | CVD-perceived | Filter-corrected
# ============================================================================

def plot_color_swatches(output_dir, best_per_roi):
    """Swatch rows for best-fit results per subject (ΔRDM pipeline only)."""
    orig_rgb = get_stim_rgb()

    # Collect best results with non-trivial delta
    panels = []
    for (subj, roi), res in sorted(best_per_roi.items()):
        if res['sig_level'] in ('significant', 'trending'):
            panels.append(res)

    if not panels:
        print('  [SKIP] No significant/trending results for swatches.')
        return

    n_panels = len(panels)
    n_rows = 3 * n_panels + 1

    fig, axes = plt.subplots(n_rows, 9, figsize=(15, 2.8 * n_panels + 2),
                              gridspec_kw={'width_ratios': [1.8] + [1]*8,
                                           'hspace': 0.45, 'wspace': 0.10})

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
            spine.set_linewidth(2); spine.set_color('#333333')

    for p_idx, res in enumerate(panels):
        subj = res['subj']
        roi = res['roi']
        model = res['model']
        cvd_type = res['cvd_type']
        delta = res['delta_theta_deg']
        rho = res['loco_rho']
        p = res['loco_p']
        sig_sym = '*' if p < 0.05 else '\u2020'

        perceived_rgb = shift_stim_hue(delta)
        corrected_rgb = shift_stim_hue(-delta)

        base_row = 1 + p_idx * 3

        row_data = [
            (f'sub-{subj} ({cvd_type})\n{roi} {model}\nLOCO ' + r'$\rho$' + f'={rho:.2f}{sig_sym}',
             perceived_rgb, delta, '#D32F2F'),
            (f'Filter Corrected\n(inverse ' + r'$\delta\theta$' + ')',
             corrected_rgb, -delta, '#1565C0'),
            (f'Original\n(reference)',
             orig_rgb, np.zeros(8), '#666666'),
        ]

        for r_off, (label, rgb_arr, d_arr, accent) in enumerate(row_data):
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
                 + r'($\Delta$RDM fitting $\rightarrow$ LOCO validation)',
                 fontsize=13, fontweight='bold', y=1.01)
    plt.savefig(output_dir / 'color_swatches.png', dpi=200,
                bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'  Saved: {output_dir / "color_swatches.png"}')


# ============================================================================
# Fig 2: Delta-theta Bar Chart
# ============================================================================

def plot_delta_theta_bars(output_dir, sim_results):
    """Per-color δθ bars for significant + trending results."""
    stim_rgb = get_stim_rgb()

    panels = [res for res in sim_results.values()
              if res['sig_level'] in ('significant', 'trending')]
    panels.sort(key=lambda x: (0 if x['sig_level'] == 'significant' else 1,
                                 x['subj'], x['roi']))

    if not panels:
        print('  [SKIP] No significant/trending results.')
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
        rdm_r = res.get('rdm_r')

        title_lines = [f"sub-{res['subj']} ({res['cvd_type']}) \u2014 {res['roi']}"]
        line2 = f"{res['model']} LOCO " + r'$\rho$' + f"={res['loco_rho']:.2f}{sig_sym}"
        if rdm_r is not None:
            line2 += f" | \u0394RDM r={rdm_r:.2f}"
        title_lines.append(line2)
        ax.set_title('\n'.join(title_lines), fontsize=8, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)

        border_color = '#2E7D32' if res['sig_level'] == 'significant' else '#FF8F00'
        border_width = 2.5 if res['sig_level'] == 'significant' else 1.5
        for spine in ax.spines.values():
            spine.set_linewidth(border_width); spine.set_color(border_color)

    fig.suptitle('Per-Color Hue Distortion ' + r'$\delta\theta$' +
                  ' (\u0394RDM \u2192 LOCO validated)\n'
                  'Green = p<.05, Orange = p<.10',
                  fontsize=11, fontweight='bold', y=1.04)
    plt.tight_layout()
    plt.savefig(output_dir / 'delta_theta_bars.png', dpi=200,
                bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'  Saved: {output_dir / "delta_theta_bars.png"}')


# ============================================================================
# Fig 3: Color Wheel with Shift Arrows
# ============================================================================

def plot_color_wheel(output_dir, best_per_roi):
    """Color wheel showing original → shifted colors for best fits per ROI."""
    orig_rgb = get_stim_rgb()

    # Select panels to show: best per (subject, roi) that have data
    panel_specs = [
        ('09', 'V2', 'sub-09 protan \u2014 V2'),
        ('09', 'V1', 'sub-09 protan \u2014 V1'),
        ('08', 'V1', 'sub-08 deutan \u2014 V1'),
        ('08', 'V2', 'sub-08 deutan \u2014 V2'),
    ]

    # Filter to those with data
    active = [(s, r, t) for s, r, t in panel_specs if (s, r) in best_per_roi]
    n = len(active)
    if n == 0:
        print('  [SKIP] No data for color wheel.')
        return

    cols = min(n, 2)
    rows = (n + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(6 * cols, 5.5 * rows),
                              subplot_kw={'projection': 'polar'})
    if n == 1:
        axes = np.array([axes])
    axes = np.atleast_2d(axes)

    for idx, (subj, roi, title) in enumerate(active):
        row, col = divmod(idx, cols)
        ax = axes[row, col]
        res = best_per_roi[(subj, roi)]
        delta = res['delta_theta_deg']
        model = res['model']
        rho, p = res['loco_rho'], res['loco_p']
        shifted_rgb = shift_stim_hue(delta)

        # Background hue ring
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
            t_shift = np.deg2rad((HUE_ANGLES_DEG[j] + delta[j]) % 360)

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
        sig_sym = '*' if p < 0.05 else ('\u2020' if p < 0.10 else ' ns')
        ax.set_title(f'{title}\n{model} LOCO ' +
                      r'$\rho$' + f'={rho:.2f}{sig_sym}',
                      fontsize=9, fontweight='bold', pad=15)

    # Hide unused axes
    for idx in range(n, rows * cols):
        row, col = divmod(idx, cols)
        axes[row, col].set_visible(False)

    legend_elements = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor='gray',
               markeredgecolor='black', markersize=10, label='Original (outer)'),
        Line2D([0], [0], marker='D', color='w', markerfacecolor='gray',
               markeredgecolor='red', markersize=8, label='CVD-shifted (inner)'),
    ]
    fig.legend(handles=legend_elements, loc='lower center', ncol=2,
               fontsize=9, bbox_to_anchor=(0.5, -0.02))
    fig.suptitle('Color Wheel: Original vs Predicted CVD Perception\n'
                 '(\u0394RDM cosine \u2192 LOCO validated)',
                  fontsize=13, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(output_dir / 'color_wheel_shifts.png', dpi=200,
                bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'  Saved: {output_dir / "color_wheel_shifts.png"}')


# ============================================================================
# Fig 4: Continuous Distortion Curve
# ============================================================================

def plot_continuous_distortion(output_dir, best_per_roi):
    """Continuous δθ(θ) for best model per ROI."""
    stim_rgb = get_stim_rgb()
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    theta_fine = np.linspace(0, 360, 361)

    for ax_idx, subj in enumerate(['08', '09']):
        ax = axes[ax_idx]
        cvd_type = CVD_TYPE[subj]

        for roi in ['V1', 'V2']:
            res = best_per_roi.get((subj, roi))
            if res is None:
                continue

            model = res['model']
            params = res['params']
            p_loco = res['loco_p']
            clr = ROI_COLORS[roi]
            ls = ROI_STYLES[roi]

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
                    label=f'{roi} ({model[:7]}) p={p_loco:.3f}{sig_sym}',
                    alpha=alpha)

        for j in range(8):
            ax.axvline(HUE_ANGLES_DEG[j], color=stim_rgb[j], alpha=0.4, lw=8)

        ax.axhline(0, color='gray', lw=0.8, ls=':')
        ax.set_xlabel('Hue Angle ' + r'$\theta$' + ' (deg)', fontsize=10)
        ax.set_ylabel(r'$\delta\theta$ (deg)', fontsize=10)
        ax.set_title(f'sub-{subj} ({cvd_type})', fontsize=11, fontweight='bold')
        ax.set_xticks(HUE_ANGLES_DEG)
        ax.set_xticklabels(COLOR_NAMES, fontsize=7, rotation=45, ha='right')
        ax.legend(fontsize=8)
        ax.grid(alpha=0.2)
        ax.set_xlim(0, 360)

    fig.suptitle('Continuous Hue Distortion ' +
                  r'$\delta\theta(\theta)$' + ' \u2014 \u0394RDM Cosine',
                  fontsize=13, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(output_dir / 'continuous_distortion.png', dpi=200,
                bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'  Saved: {output_dir / "continuous_distortion.png"}')


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Unified visualization for ΔRDM cone-shift pipeline')
    parser.add_argument('--output_dir', type=str, default='figures')
    args = parser.parse_args()

    output_dir = _SCRIPT_DIR.parent / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    print('=' * 60)
    print('Cone-Shift Pipeline Visualization (ΔRDM → LOCO)')
    print(f'Source: {SIM_DIR}')
    print(f'Output: {output_dir}')
    print('=' * 60)

    # Load
    print('\n[1] Loading ΔRDM simulation results...')
    sim_results = load_sim_results()
    best_per_roi = get_best_per_roi(sim_results)
    print(f'  Loaded {len(sim_results)} results')

    # Summary
    print('\n[2] Summary (cosine metric):')
    for key in sorted(sim_results.keys()):
        res = sim_results[key]
        is_best = best_per_roi.get((res['subj'], res['roi'])) is res
        marker = ' <-- BEST' if is_best else ''
        sig_sym = '*' if res['sig_level'] == 'significant' else (
            '\u2020' if res['sig_level'] == 'trending' else '')
        print(f"  sub-{res['subj']} {res['roi']} {res['model']}: "
              f"\u0394RDM r={res['rdm_r']:.3f} (p={res['rdm_p']:.3f}) | "
              f"LOCO \u03c1={res['loco_rho']:.3f} (p={res['loco_p']:.3f}) "
              f"[{res['sig_level']}{sig_sym}]{marker}")

    # Generate figures
    print('\n[3] Color swatches...')
    plot_color_swatches(output_dir, best_per_roi)

    print('\n[4] Delta-theta bars...')
    plot_delta_theta_bars(output_dir, sim_results)

    print('\n[5] Color wheel...')
    plot_color_wheel(output_dir, best_per_roi)

    print('\n[6] Continuous distortion...')
    plot_continuous_distortion(output_dir, best_per_roi)

    print(f'\n{"=" * 60}')
    print(f'All figures saved to: {output_dir}')
    print('=' * 60)


if __name__ == '__main__':
    main()
