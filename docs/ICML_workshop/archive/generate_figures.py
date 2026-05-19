#!/usr/bin/env python3
"""
generate_figures.py — Generate all figures for the GenBio @ ICML 2026 paper.

Figure 1 (main text): Pipeline schematic + LOCO vulnerability profiles (3 subjects)
Figure 2 (appendix):  Correction geometry — opponent-arc + pre-image feasibility

Usage:
    conda activate srm
    python docs/ICML_workshop/icml2026/generate_figures.py
"""

import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Arc
from matplotlib.gridspec import GridSpec
from pathlib import Path
import sys

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_DIR = _SCRIPT_DIR.parents[2]   # colorBlind_analysis/
_PIPELINE_DIR = _PROJECT_DIR / 'analysis' / 'future_phase2_filter_optimization'
_RESULT_DIR = _PIPELINE_DIR / 'results' / 'loco_filter'
_OUT_DIR = _SCRIPT_DIR / 'figures'
_OUT_DIR.mkdir(exist_ok=True)

_FWD_DIR = str(_PIPELINE_DIR.parent / 'future_phase1_forward_model' / 'scripts')
_SCRIPTS_DIR = str(_PIPELINE_DIR / 'scripts')
if _FWD_DIR not in sys.path:
    sys.path.insert(0, _FWD_DIR)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from machado_simulator import machado_shifted_hue

# ---------------------------------------------------------------------------
# Constants (reused from visualize_color_structure.py)
# ---------------------------------------------------------------------------
CIELAB_ANGLES = np.array([0, 45, 90, 135, 180, 225, 270, 315], dtype=float)
COLOR_NAMES = ['Red', 'Orange', 'Yellow', 'Green', 'Cyan', 'Blue', 'Purple', 'Magenta']
COLOR_LABELS_SHORT = [f'c{i+1}' for i in range(8)]

STIM_LAB = np.array([
    [59.90, 62.69, 3.78],    # c1 Red
    [64.20, 49.20, 45.58],   # c2 Orange
    [57.27, 13.06, 41.69],   # c3 Yellow
    [69.08, -55.02, 47.38],  # c4 Green
    [74.61, -41.33, -4.89],  # c5 Cyan
    [69.14, -11.45, -40.91], # c6 Blue
    [60.68, 19.18, -54.13],  # c7 Purple
    [60.17, 46.82, -40.31],  # c8 Magenta
])

_M_XYZ_TO_SRGB = np.array([
    [3.2406, -1.5372, -0.4986],
    [-0.9689,  1.8758,  0.0415],
    [0.0557, -0.2040,  1.0570],
])


def lab2rgb(L, a, b):
    L, a, b = np.asarray(L, float), np.asarray(a, float), np.asarray(b, float)
    y = (L + 16) / 116
    x = a / 500 + y
    z = y - b / 200
    xyz = np.stack([x, y, z], axis=-1)
    mask = xyz > 0.206893
    xyz = np.where(mask, xyz ** 3, (xyz - 16 / 116) / 7.787)
    xyz *= np.array([0.95047, 1.0, 1.08883])
    rgb = xyz @ _M_XYZ_TO_SRGB.T
    rgb = np.where(rgb <= 0.0031308, 12.92 * rgb,
                   1.055 * np.power(np.maximum(rgb, 0), 1 / 2.4) - 0.055)
    return np.clip(rgb, 0, 1)


STIM_RGB = lab2rgb(STIM_LAB[:, 0], STIM_LAB[:, 1], STIM_LAB[:, 2])

SUBJECTS = [
    {'id': '09', 'cvd_type': 'protan', 'label': 'Sub-09 (protan)',
     'best_model': 'machado_1way', 'best_label': 'Machado',
     'params_str': r'$\Delta\lambda{=}13.5$nm'},
    {'id': '08', 'cvd_type': 'deutan', 'label': 'Sub-08 (deutan)',
     'best_model': 'rc_opponent', 'best_label': 'R+C',
     'params_str': r'$\Delta\lambda{=}2.0$nm, $g{=}{+}2.25$'},
    {'id': '10', 'cvd_type': 'normal', 'label': 'Sub-10 (control)',
     'best_model': None, 'best_label': '---',
     'params_str': 'No sig. model'},
]

MODEL_COLORS = {
    'machado_1way': '#2E7D32',
    'rc_opponent': '#E65100',
    '2component': '#1565C0',
}

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def _load_json(path):
    with open(path) as f:
        return json.load(f)


def load_manifest(subj_id):
    for d in ['phase_a_2component', 'phase_a_v2']:
        fname = _RESULT_DIR / d / f'sub-{subj_id}_V4_manifest.json'
        if fname.exists():
            return _load_json(fname)
    return None


def load_model_result(subj_id, model_name):
    if model_name == '2component':
        d = _RESULT_DIR / 'phase_a_2component'
    else:
        d = _RESULT_DIR / 'phase_a_v2'
    fname = d / f'sub-{subj_id}_V4_{model_name}.json'
    if not fname.exists():
        return None
    return _load_json(fname)


def load_preimage(subj_id, model_name):
    if model_name == '2component':
        d = _RESULT_DIR / 'preimage_2component'
    else:
        d = _RESULT_DIR / 'preimage'
    fname = d / f'sub-{subj_id}_V4_{model_name}_preimage.json'
    if not fname.exists():
        return None
    return _load_json(fname)


def load_separation(subj_id, model_name):
    fname = _RESULT_DIR / 'preimage' / f'sub-{subj_id}_V4_{model_name}_separation.json'
    if not fname.exists():
        return None
    return _load_json(fname)


# ===========================================================================
# FIGURE 1: Pipeline + LOCO Vulnerability Profiles
# ===========================================================================

def _draw_pipeline_schematic(ax):
    """Draw the inference pipeline schematic (panel a)."""
    ax.set_xlim(-0.1, 11.1)
    ax.set_ylim(0.2, 3.4)
    ax.axis('off')

    box_w, box_h = 1.45, 0.95
    box_y = 0.85
    # Position boxes evenly across [0.1, 11.0]
    x_positions = [0.15, 2.35, 4.55, 6.75, 8.95]

    boxes = [
        (x_positions[0], 'fMRI\nVoxel Data', '#E3F2FD'),
        (x_positions[1], 'Encoding\nModel ($W$)', '#E8F5E9'),
        (x_positions[2], 'LOCO Vuln.\n$\\mathbf{v} \\in \\mathbb{R}^8$', '#FFF3E0'),
        (x_positions[3], 'Inverse\nInference', '#FCE4EC'),
        (x_positions[4], 'Correction\nPrediction', '#F3E5F5'),
    ]

    for x, text, fc in boxes:
        bb = FancyBboxPatch((x, box_y), box_w, box_h,
                            boxstyle='round,pad=0.12',
                            facecolor=fc, edgecolor='#555', linewidth=1.0,
                            transform=ax.transData, zorder=2)
        ax.add_patch(bb)
        ax.text(x + box_w / 2, box_y + box_h / 2, text,
                ha='center', va='center',
                fontsize=6.5, fontweight='bold', color='#333', zorder=3)

    # Arrows between boxes (at box vertical center)
    y_arrow = box_y + box_h / 2
    for i in range(len(boxes) - 1):
        x1 = boxes[i][0] + box_w + 0.08
        x2 = boxes[i + 1][0] - 0.08
        ax.annotate('', xy=(x2, y_arrow), xytext=(x1, y_arrow),
                    arrowprops=dict(arrowstyle='->', color='#666', lw=1.4))

    # Labels above boxes
    labels = [
        'Ridge + GCV', 'Leave-one-\ncolor-out',
        'Grid search +\nperm. test', 'Pre-image\ninversion',
    ]
    y_label = box_y + box_h + 0.42
    for i, lbl in enumerate(labels):
        x_mid = (boxes[i][0] + box_w + boxes[i + 1][0]) / 2
        ax.text(x_mid, y_label, lbl, ha='center', va='center',
                fontsize=5.5, color='#777', style='italic')

    ax.set_title('(a) Inference Pipeline', fontsize=9, fontweight='bold',
                 loc='left', pad=6)


def _plot_loco_bar(ax, vuln_hc, vuln_cvd, vuln_sim, model_color, subj_info):
    """Bar chart: HC baseline, CVD observed, and model fit for one subject."""
    x = np.arange(8)
    width = 0.25

    # HC baseline
    bars_hc = ax.bar(x - width, vuln_hc, width, color='#BDBDBD',
                     edgecolor='#888', linewidth=0.5, label='HC baseline',
                     zorder=2)

    # CVD observed — color-coded bars
    for i in range(8):
        ax.bar(x[i], vuln_cvd[i], width,
               color=STIM_RGB[i], edgecolor='#555', linewidth=0.8, zorder=3)
    # Invisible bar for legend
    ax.bar([], [], width, color='#C62828', edgecolor='#555',
           linewidth=0.8, label='CVD observed')

    # Model fit (if significant)
    if vuln_sim is not None:
        ax.bar(x + width, vuln_sim, width, color=model_color,
               edgecolor=model_color, linewidth=0.5, alpha=0.6,
               label=f'{subj_info["best_label"]} fit', zorder=2)
        # Connect CVD and model with thin lines
        for i in range(8):
            ax.plot([x[i], x[i] + width], [vuln_cvd[i], vuln_sim[i]],
                    color=model_color, linewidth=0.6, alpha=0.4, zorder=1)

    ax.set_xticks(x)
    ax.set_xticklabels(COLOR_LABELS_SHORT, fontsize=7)
    # Color the tick labels
    for tick_label, rgb in zip(ax.get_xticklabels(), STIM_RGB):
        tick_label.set_color(np.clip(rgb * 0.7, 0, 1))
        tick_label.set_fontweight('bold')

    ax.axhline(0, color='black', linewidth=0.5, zorder=0)
    ax.set_ylabel('LOCO error', fontsize=7)
    ax.tick_params(axis='y', labelsize=6.5)

    # Title with stats (compact: 2 lines max)
    r = load_model_result(subj_info['id'], subj_info['best_model']) if subj_info['best_model'] else None
    if r is not None:
        rho = r['best_loss']['spearman_r']
        p = r['permutation']['label_perm_p']
        stars = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else ''
        title = (f'{subj_info["label"]}\n'
                 f'{subj_info["best_label"]}, '
                 f'$\\rho$={rho:.2f}, p={p:.3f}{stars}')
    else:
        title = f'{subj_info["label"]}\n{subj_info["params_str"]}'

    ax.set_title(title, fontsize=7.5, fontweight='bold', pad=5)
    ax.legend(fontsize=5.5, loc='upper right', framealpha=0.85)


def generate_figure1():
    """Figure 1: Pipeline schematic (a) + LOCO profiles (b-d)."""
    print('Generating Figure 1...')

    fig = plt.figure(figsize=(7.2, 6.0))  # ICML two-column width
    gs = GridSpec(2, 3, figure=fig, height_ratios=[0.60, 1.0],
                  hspace=0.65, wspace=0.40,
                  left=0.07, right=0.98, top=0.93, bottom=0.08)

    # Panel (a): Pipeline schematic — spans full top row
    ax_pipe = fig.add_subplot(gs[0, :])
    _draw_pipeline_schematic(ax_pipe)

    # Panels (b-d): LOCO bar charts
    panel_labels = ['(b)', '(c)', '(d)']
    for col, subj_info in enumerate(SUBJECTS):
        ax = fig.add_subplot(gs[1, col])

        manifest = load_manifest(subj_info['id'])
        vuln_hc = np.array(manifest['vuln_baseline'])
        vuln_cvd = np.array(manifest['vuln_cvd'])

        vuln_sim = None
        model_color = '#999'
        if subj_info['best_model'] is not None:
            r = load_model_result(subj_info['id'], subj_info['best_model'])
            if r is not None:
                vuln_sim = np.array(r['best_loss']['vuln_sim'])
                model_color = MODEL_COLORS.get(subj_info['best_model'], '#999')

        _plot_loco_bar(ax, vuln_hc, vuln_cvd, vuln_sim, model_color, subj_info)

        # Panel label
        ax.text(-0.15, 1.15, panel_labels[col], transform=ax.transAxes,
                fontsize=10, fontweight='bold', va='top')

    out = _OUT_DIR / 'figure1_pipeline_loco.pdf'
    fig.savefig(out, dpi=300, bbox_inches='tight', facecolor='white')
    fig.savefig(out.with_suffix('.png'), dpi=300, bbox_inches='tight',
                facecolor='white')
    plt.close(fig)
    print(f'  Saved: {out}')


# ===========================================================================
# FIGURE 2 (Appendix): Correction Geometry — opponent-arc + pre-image
# ===========================================================================

def _compute_opponent_arc(delta_lambda, cvd_type, n_points=360):
    """Compute the opponent-space arc for a given cone shift."""
    angles_in = np.linspace(0, 360, n_points, endpoint=False)
    angles_out = np.array([machado_shifted_hue(a, delta_lambda, cvd_type)
                           for a in angles_in])
    return angles_in, angles_out


def _plot_opponent_arc(ax, subj_info, preimage_data, is_mild):
    """Plot opponent-space hue circle with original vs perceived angles."""
    # Outer ring: original stimulus positions
    theta_circle = np.linspace(0, 2 * np.pi, 200)
    r_outer = 1.0
    r_inner = 0.6
    ax.plot(r_outer * np.cos(theta_circle), r_outer * np.sin(theta_circle),
            color='#ddd', linewidth=0.6, zorder=0)

    # Original positions
    theta_orig = np.deg2rad(CIELAB_ANGLES)
    x_orig = r_outer * np.cos(theta_orig)
    y_orig = r_outer * np.sin(theta_orig)
    for i in range(8):
        ax.scatter(x_orig[i], y_orig[i], c=[STIM_RGB[i]], s=120,
                   marker='o', edgecolors='#333', linewidths=1.2, zorder=5)
        r_lab = 1.22
        ax.text(r_lab * np.cos(theta_orig[i]), r_lab * np.sin(theta_orig[i]),
                COLOR_LABELS_SHORT[i], fontsize=6, fontweight='bold',
                ha='center', va='center',
                color=np.clip(STIM_RGB[i] * 0.6, 0, 1))

    if preimage_data is None:
        ax.text(0, 0, 'No data', ha='center', va='center', fontsize=10,
                color='#bbb')
        ax.set_xlim(-1.5, 1.5)
        ax.set_ylim(-1.5, 1.5)
        ax.set_aspect('equal')
        ax.axis('off')
        return

    # Perceived positions (inner ring)
    perceived = np.array(preimage_data['perceived_angles'])
    theta_perc = np.deg2rad(perceived)
    x_perc = r_inner * np.cos(theta_perc)
    y_perc = r_inner * np.sin(theta_perc)

    ax.plot(r_inner * np.cos(theta_circle), r_inner * np.sin(theta_circle),
            color='#eee', linewidth=0.4, linestyle=':', zorder=0)

    # Lines from original to perceived
    for i in range(8):
        ax.plot([x_orig[i], x_perc[i]], [y_orig[i], y_perc[i]],
                color=np.clip(STIM_RGB[i] * 0.8, 0, 1),
                alpha=0.35, linewidth=1.2, zorder=2)

    # Perceived dots
    for i in range(8):
        if is_mild:
            ax.scatter(x_perc[i], y_perc[i], c=[STIM_RGB[i]], s=70,
                       marker='s', edgecolors='#333',
                       linewidths=1.0, zorder=5)
        else:
            ax.scatter(x_perc[i], y_perc[i], c='#C62828', s=70,
                       marker='x', linewidths=1.5, zorder=5)

    # Check for merged colors (large residuals)
    residuals = np.array(preimage_data['residuals'])
    merged = residuals > 1.0  # > 1 degree residual = merge
    if np.any(merged):
        merged_idx = np.where(merged)[0]
        # Draw red circle around merged perceived positions
        for i in merged_idx:
            circle = plt.Circle((x_perc[i], y_perc[i]), 0.08,
                                fill=False, edgecolor='red',
                                linewidth=1.5, linestyle='--', zorder=6)
            ax.add_patch(circle)

    # Pre-image corrected positions (if available)
    preimage_angles = np.array(preimage_data['preimage_angles'])
    theta_pre = np.deg2rad(preimage_angles)
    r_pre = 0.85
    for i in range(8):
        if residuals[i] < 1.0:  # Only show exact solutions
            x_pre = r_pre * np.cos(theta_pre[i])
            y_pre = r_pre * np.sin(theta_pre[i])
            ax.scatter(x_pre, y_pre, c=[STIM_RGB[i]], s=50,
                       marker='D', edgecolors='#2E7D32', linewidths=0.8,
                       alpha=0.7, zorder=4)
            # Thin arrow from pre-image to perceived
            ax.annotate('', xy=(x_perc[i], y_perc[i]),
                        xytext=(x_pre, y_pre),
                        arrowprops=dict(arrowstyle='->', color='#2E7D32',
                                        lw=0.6, alpha=0.4))

    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(-1.5, 1.5)
    ax.set_aspect('equal')
    ax.axis('off')


def generate_figure2():
    """Figure 2 (appendix): Correction geometry."""
    print('Generating Figure 2...')

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 4.2))

    # Panel (a): Sub-08 (mild) — R+C pre-image, all exact
    preimage_08 = load_preimage('08', 'rc_opponent')
    ax = axes[0]
    _plot_opponent_arc(ax, SUBJECTS[1], preimage_08, is_mild=True)
    n_exact = sum(1 for r in preimage_08['residuals'] if r < 1.0)
    ax.set_title(f'(a) Sub-08 (mild deutan)\nR+C: {n_exact}/8 exact pre-image',
                 fontsize=8, fontweight='bold')

    # Panel (b): Sub-09 (moderate) — Machado pre-image, arc collapse
    preimage_09 = load_preimage('09', 'machado_1way')
    ax = axes[1]
    _plot_opponent_arc(ax, SUBJECTS[0], preimage_09, is_mild=False)
    n_exact_09 = sum(1 for r in preimage_09['residuals'] if r < 1.0)
    n_merged = 8 - n_exact_09
    ax.set_title(f'(b) Sub-09 (mod. protan)\n'
                 f'Machado: {n_exact_09}/8 exact, {n_merged} merged',
                 fontsize=8, fontweight='bold')

    # Shared legend — use Line2D everywhere to ensure consistent rendering
    legend_elements = [
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='gray',
                   markersize=8, markeredgecolor='#333',
                   label='Original stimulus'),
        plt.Line2D([0], [0], marker='s', color='w', markerfacecolor='gray',
                   markersize=7, markeredgecolor='#333',
                   label='Perceived (mild)'),
        plt.Line2D([0], [0], marker='x', color='#C62828',
                   markersize=8, markeredgewidth=1.8, linestyle='None',
                   label='Perceived (moderate)'),
        plt.Line2D([0], [0], marker='D', color='w', markerfacecolor='gray',
                   markersize=6, markeredgecolor='#2E7D32',
                   label='Pre-image (corrected)'),
        plt.Line2D([0], [0], marker='o', color='red', markerfacecolor='none',
                   markersize=9, markeredgewidth=1.4, linestyle='--',
                   label='Merged (no exact solution)'),
    ]
    fig.legend(handles=legend_elements, loc='lower center', ncol=3,
               fontsize=7, frameon=True, bbox_to_anchor=(0.5, -0.04))

    fig.suptitle('Correction Geometry: Opponent-Space Pre-Image Feasibility',
                 fontsize=10, fontweight='bold', y=0.99)

    fig.subplots_adjust(top=0.84, bottom=0.12, left=0.04, right=0.96,
                        wspace=0.15)

    out = _OUT_DIR / 'figure2_correction_geometry.pdf'
    fig.savefig(out, dpi=300, bbox_inches='tight', facecolor='white')
    fig.savefig(out.with_suffix('.png'), dpi=300, bbox_inches='tight',
                facecolor='white')
    plt.close(fig)
    print(f'  Saved: {out}')


# ===========================================================================
# FIGURE 3 (Appendix): Full model comparison — hue wheels for 2-component
# ===========================================================================

def generate_figure3():
    """Figure 3 (appendix): 2-component hue wheel comparison (convergent
    detection / divergent correction)."""
    print('Generating Figure 3...')

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 4.2))

    for col, (subj_info, subj_idx) in enumerate([(SUBJECTS[0], '09'),
                                                   (SUBJECTS[1], '08')]):
        ax = axes[col]
        r_2comp = load_model_result(subj_idx, '2component')
        if r_2comp is None:
            ax.text(0.5, 0.5, 'No data', transform=ax.transAxes,
                    ha='center', fontsize=12, color='#bbb')
            continue

        dt = np.array(r_2comp['best_loss']['delta_theta'])
        rho = r_2comp['best_loss']['spearman_r']
        p = r_2comp['permutation']['label_perm_p']
        params = r_2comp['best_params']

        # Outer ring
        theta_circle = np.linspace(0, 2 * np.pi, 200)
        r_outer, r_inner = 1.0, 0.62
        ax.plot(r_outer * np.cos(theta_circle),
                r_outer * np.sin(theta_circle),
                color='#ddd', linewidth=0.6, zorder=0)
        ax.plot(r_inner * np.cos(theta_circle),
                r_inner * np.sin(theta_circle),
                color='#eee', linewidth=0.4, linestyle=':', zorder=0)

        theta_orig = np.deg2rad(CIELAB_ANGLES)
        x_orig = r_outer * np.cos(theta_orig)
        y_orig = r_outer * np.sin(theta_orig)

        hue_shifted = (CIELAB_ANGLES + dt) % 360.0
        theta_shift = np.deg2rad(hue_shifted)
        x_shift = r_inner * np.cos(theta_shift)
        y_shift = r_inner * np.sin(theta_shift)

        for i in range(8):
            # Original
            ax.scatter(x_orig[i], y_orig[i], c=[STIM_RGB[i]], s=120,
                       marker='o', edgecolors='#333', linewidths=1.2, zorder=5)
            # Label
            r_lab = 1.20
            ax.text(r_lab * np.cos(theta_orig[i]),
                    r_lab * np.sin(theta_orig[i]),
                    COLOR_LABELS_SHORT[i], fontsize=6, fontweight='bold',
                    ha='center', va='center',
                    color=np.clip(STIM_RGB[i] * 0.6, 0, 1))
            # Connection line
            ax.plot([x_orig[i], x_shift[i]], [y_orig[i], y_shift[i]],
                    color=np.clip(STIM_RGB[i] * 0.8, 0, 1),
                    alpha=0.35, linewidth=1.2, zorder=2)
            # Shifted
            ax.scatter(x_shift[i], y_shift[i], c=[STIM_RGB[i]], s=70,
                       marker='D', edgecolors='#1565C0', linewidths=1.0,
                       zorder=5)
            # Delta label
            if abs(dt[i]) > 8:
                ax.text(x_shift[i], y_shift[i] - 0.10,
                        f'{dt[i]:+.0f}°', fontsize=5, ha='center', va='top',
                        color='#1565C0', fontweight='bold')

        stars = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else ''
        ax.set_title(
            f'{subj_info["label"]}  |  '
            r'$\beta_s$' f'={params[0]:.0f}°, '
            r'$\beta_c$' f'={params[1]:+.0f}°\n'
            r'$\rho$' f'={rho:.3f}, p={p:.4f}{stars}',
            fontsize=7.5, fontweight='bold', pad=6)

        ax.set_xlim(-1.5, 1.5)
        ax.set_ylim(-1.5, 1.5)
        ax.set_aspect('equal')
        ax.axis('off')

    fig.suptitle('Cortical 2-Component Model: Angular Distortion',
                 fontsize=10, fontweight='bold', y=0.99)

    fig.subplots_adjust(top=0.82, bottom=0.05, left=0.04, right=0.96,
                        wspace=0.10)

    out = _OUT_DIR / 'figure3_2component_huewheel.pdf'
    fig.savefig(out, dpi=300, bbox_inches='tight', facecolor='white')
    fig.savefig(out.with_suffix('.png'), dpi=300, bbox_inches='tight',
                facecolor='white')
    plt.close(fig)
    print(f'  Saved: {out}')


# ===========================================================================
# Main
# ===========================================================================

if __name__ == '__main__':
    print(f'Output directory: {_OUT_DIR}')
    print(f'Result directory: {_RESULT_DIR}')
    print()

    generate_figure1()
    print()
    generate_figure2()
    print()
    generate_figure3()
    print()
    print('All figures generated.')
