#!/usr/bin/env python3
"""
generate_fig3.py
Figure 3: Individually-patterned geometric distortion in CVD color representations.

Panel 3A: ΔRDM heatmaps for sub-08 (primary ROI = V2) and sub-09 (primary ROI = V1)
Panel 3B: Disparity summary metric across V1/V2/V3/hV4 for all CVD subjects + HC band

p-value sources:
  3A heatmap annotations: task-provided ΔRDM permutation p-values
    sub-09 V1: p=.005* (from ΔRDM criterion, MEMORY.md 2026-03-23)
    sub-08 V2: p=.179 NS (from ΔRDM criterion, consistent with R+C model run)
  3B summary: loo_consistent_results.json individual_cvd p_value (Crawford & Howell t-test)
    (separate analysis family — see FIGURE_NOTES.md)

Output: fig3_output.png, fig3_output.pdf
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import Patch
from scipy.spatial.distance import squareform
import json
from pathlib import Path

# ─── Paths ───────────────────────────────────────────────────────────────────
BASE = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis')
DELTA_RDM_DIR = BASE / 'analysis/future_phase2_filter_optimization/results/diagnostics/srm_precompute'
LOO_JSON = BASE / 'analysis/phase2_SRM_across_between/results/loo_consistent/20260218_163819/loo_consistent_results.json'
OUT_DIR = BASE / 'docs/PAPER/Figures/F3_geometry'

# ─── Constants ────────────────────────────────────────────────────────────────
COLOR_NAMES = ['Red', 'Orange', 'Yellow', 'Green', 'Cyan', 'Blue', 'Purple', 'Magenta']
COLOR_ABBR  = ['Red', 'Org', 'Yel', 'Grn', 'Cyn', 'Blu', 'Pur', 'Mag']
ROIS = ['V1', 'V2', 'V3', 'hV4']
ROI_LABELS = ['V1', 'V2', 'V3', 'hV4']

# ─── Style ────────────────────────────────────────────────────────────────────
plt.rcParams.update({
    'font.family': 'Arial',
    'font.size': 7,
    'axes.titlesize': 8,
    'axes.labelsize': 7,
    'xtick.labelsize': 6,
    'ytick.labelsize': 6,
    'legend.fontsize': 6.5,
    'axes.linewidth': 0.6,
    'xtick.major.width': 0.6,
    'ytick.major.width': 0.6,
    'xtick.major.size': 2,
    'ytick.major.size': 2,
    'pdf.fonttype': 42,  # Embed fonts as TrueType for vector PDF
    'svg.fonttype': 'none',
})

# ─── Load data ────────────────────────────────────────────────────────────────

def load_delta_rdm_matrix(roi, sub_key):
    """Load ΔRDM upper-triangle vector and expand to symmetric 8×8 matrix."""
    data = np.load(DELTA_RDM_DIR / f'delta_rdm_obs_srm_{roi}.npz')
    vec = data[sub_key]  # shape (28,)
    mat = squareform(vec)  # symmetric 8×8, diagonal=0
    return mat


def load_loo_results():
    with open(LOO_JSON) as f:
        return json.load(f)


# ─── Significance label ───────────────────────────────────────────────────────

def sig_label(p):
    if p < 0.01:
        return '**'
    elif p < 0.05:
        return '*'
    else:
        return 'ns'


# ─── Main figure ──────────────────────────────────────────────────────────────

def make_figure():
    # Figure size: 180mm wide × 120mm tall (eLife double-column)
    fig_w_in = 180 / 25.4
    fig_h_in = 120 / 25.4

    fig = plt.figure(figsize=(fig_w_in, fig_h_in))

    # Manual axes placement (normalized coordinates) to control spacing precisely
    # Panel A: two heatmaps side by side in left 55% of figure
    # Panel B: line plot in right 40%
    # [left, bottom, width, height]
    ax_a1 = fig.add_axes([0.09, 0.14, 0.24, 0.72])   # sub-08 heatmap
    ax_a2 = fig.add_axes([0.38, 0.14, 0.24, 0.72])   # sub-09 heatmap
    ax_b  = fig.add_axes([0.68, 0.14, 0.15, 0.72])   # summary plot (width=0.15 → right edge 0.83; 0.17 strip for legend)

    # ── Panel 3A ─────────────────────────────────────────────────────────────
    heatmap_configs = [
        # (sub_key, roi, display_label, p_annotation, p_source_note)
        ('sub_08', 'V2', 'Sub-08 (deutan), V2', 0.179, 'ΔRDM'),
        ('sub_09', 'V1', 'Sub-09 (protan), V1', 0.026, 'ΔRDM'),
    ]

    heatmap_axes = [ax_a1, ax_a2]
    all_mats = []
    for sub_key, roi, _, _, _ in heatmap_configs:
        m = load_delta_rdm_matrix(roi, sub_key)
        all_mats.append(m)

    # Symmetric color scale: 95th percentile of absolute values across both mats
    vmax_global = np.percentile([np.abs(m).max() for m in all_mats], 100) * 0.80
    vmax_global = round(vmax_global * 4) / 4  # round to nearest 0.25

    for idx, (ax, cfg, mat) in enumerate(zip(heatmap_axes, heatmap_configs, all_mats)):
        sub_key, roi, title, p_val, p_src = cfg

        im = ax.imshow(mat, cmap='RdBu_r', vmin=-vmax_global, vmax=vmax_global,
                       aspect='equal', interpolation='nearest')

        # Axis ticks and labels
        ax.set_xticks(range(8))
        ax.set_yticks(range(8))
        ax.set_xticklabels(COLOR_ABBR, rotation=45, ha='right', fontsize=5.5)
        ax.set_yticklabels(COLOR_ABBR, fontsize=5.5)

        # Title with significance
        sig = sig_label(p_val)
        if sig == 'ns':
            sig_str = f'\n(ns, p = {p_val:.3f})'
        elif sig == '*':
            sig_str = f'\n(*p = {p_val:.3f})'
        else:
            sig_str = f'\n(**p = {p_val:.3f})'
        ax.set_title(f'{title}{sig_str}', fontsize=6.5, pad=3, fontweight='bold',
                     linespacing=1.3)

        # Colorbar placed explicitly to avoid squeezing the heatmap
        from mpl_toolkits.axes_grid1 import make_axes_locatable
        divider = make_axes_locatable(ax)
        cax = divider.append_axes('right', size='6%', pad=0.05)
        cbar = fig.colorbar(im, cax=cax)
        if idx == 1:
            cbar.set_label('ΔRDM (CVD - HC)', fontsize=5.5, labelpad=2)
        cbar.ax.tick_params(labelsize=4.5)
        cbar.set_ticks([-vmax_global, 0, vmax_global])
        cbar.set_ticklabels([f'{-vmax_global:.1f}', '0', f'{vmax_global:.1f}'])

        # Thin spines
        for spine in ax.spines.values():
            spine.set_linewidth(0.5)

    # Panel 3A label — placed in figure coordinates
    fig.text(0.005, 0.95, 'A', fontsize=12, fontweight='bold', va='top', ha='left')

    # ── Panel 3B ─────────────────────────────────────────────────────────────
    loo = load_loo_results()

    x = np.arange(len(ROIS))
    width = 0.22
    offsets = {'sub-08': -width, 'sub-09': 0, 'sub-10': width}
    colors_cvd = {
        'sub-08': '#D55E00',   # vermillion (deutan)
        'sub-09': '#0072B2',   # blue (protan)
        'sub-10': '#999999',   # gray (near-normal)
    }
    markers = {'sub-08': 'o', 'sub-09': 's', 'sub-10': '^'}
    labels = {
        'sub-08': 'Sub-08 (deutan)',
        'sub-09': 'Sub-09 (protan)',
        'sub-10': 'Sub-10 (near-normal)',
    }

    # HC confidence band
    hc_means = []
    hc_stds = []
    for roi_name in ROIS:
        roi_key = roi_name  # V1, V2, V3 match; hV4 is the key
        s = loo['results'][roi_key]['summary']
        hc_means.append(s['hc_mean'])
        hc_stds.append(s['hc_std'])
    hc_means = np.array(hc_means)
    hc_stds = np.array(hc_stds)

    ax_b.fill_between(x, hc_means - hc_stds, hc_means + hc_stds,
                      alpha=0.18, color='#4CAF50', label='HC mean ± 1 SD', zorder=1)
    ax_b.plot(x, hc_means, color='#2E7D32', linewidth=1.2, linestyle='--',
              marker='D', markersize=4, label='HC mean', zorder=2, markerfacecolor='white',
              markeredgewidth=1.0)

    # HC individual LOO data points (jittered slightly)
    hc_sub_labels = ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05', 'sub-06', 'sub-07']
    rng = np.random.default_rng(42)
    for roi_idx, roi_name in enumerate(ROIS):
        hc_disp = loo['results'][roi_name]['hc_loo_disparities']
        hc_vals = [hc_disp[s] for s in hc_sub_labels if s in hc_disp]
        jitter = rng.uniform(-0.08, 0.08, len(hc_vals))
        ax_b.scatter(np.full(len(hc_vals), roi_idx) + jitter, hc_vals,
                     color='#4CAF50', alpha=0.4, s=8, zorder=1, linewidths=0)

    # CVD subjects
    for sub in ['sub-08', 'sub-09', 'sub-10']:
        scores = []
        p_vals = []
        for roi_name in ROIS:
            roi_data = loo['results'][roi_name]['individual_cvd'][sub]
            scores.append(roi_data['cvd_score'])
            p_vals.append(roi_data['p_value'])

        xpos = x + offsets[sub]
        ax_b.plot(xpos, scores, color=colors_cvd[sub], linewidth=1.0,
                  linestyle='-', zorder=3)
        ax_b.scatter(xpos, scores, color=colors_cvd[sub], marker=markers[sub],
                     s=30, zorder=4, label=labels[sub])

        # Significance stars above points
        for xi, sc, pv in zip(xpos, scores, p_vals):
            if pv < 0.05:
                stars = '**' if pv < 0.01 else '*'
                ax_b.text(xi, sc + 0.025, stars, ha='center', va='bottom',
                          fontsize=7.5, color=colors_cvd[sub], fontweight='bold')

    ax_b.set_xticks(x)
    ax_b.set_xticklabels(ROI_LABELS, fontsize=7)
    ax_b.set_ylabel('SRM disparity (correlation distance)', fontsize=7)
    ax_b.set_xlabel('ROI', fontsize=7)
    ax_b.set_title('Disparity by ROI', fontsize=8, fontweight='bold', pad=4)

    # y-axis range — leave room for stars
    ymin = 0.30
    ymax = 1.00
    ax_b.set_ylim(ymin, ymax)
    ax_b.set_xlim(-0.5, len(ROIS) - 0.5)

    ax_b.spines['top'].set_visible(False)
    ax_b.spines['right'].set_visible(False)

    # Legend outside ax_b, anchored in figure coordinates to the freed right strip.
    # ax_b right edge = 0.68+0.20 = 0.88 → legend starts at 0.89 in figure coords.
    # bbox_to_anchor uses axes coords when transform=ax_b.transAxes.
    ax_b.legend(loc='upper left', bbox_to_anchor=(1.04, 1.0),
                bbox_transform=ax_b.transAxes, borderaxespad=0,
                frameon=False, fontsize=5.8,
                handlelength=1.4, handletextpad=0.4, labelspacing=0.3)

    # Panel B label — aligned with left edge of ax_b
    fig.text(0.63, 0.95, 'B', fontsize=12, fontweight='bold', va='top', ha='left')

    # ── Figure-level annotation ───────────────────────────────────────────────
    fig.text(0.5, 0.005,
             'ΔRDM = RDM_CVD − mean(RDM_HC,LOO)  |  Disparity = mean pairwise correlation distance in SRM space',
             ha='center', va='bottom', fontsize=5, color='#555555', style='italic')

    # ── Save ──────────────────────────────────────────────────────────────────
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_png = OUT_DIR / 'fig3_output.png'
    out_pdf = OUT_DIR / 'fig3_output.pdf'
    # Use bbox_inches=None (no auto-tight) — layout is pre-allocated to fit within 180mm.
    fig.savefig(out_png, dpi=300, bbox_inches=None, facecolor='white')
    fig.savefig(out_pdf, bbox_inches=None, facecolor='white')
    print(f'Saved: {out_png}')
    print(f'Saved: {out_pdf}')
    plt.close(fig)


if __name__ == '__main__':
    make_figure()
