"""
Figure 1 v8.1 — OHBM 2026 (FE-unified, 3-panel: pipeline-focused).

Changes vs v8:
- Removed LDA-based LORO reconstruction panel (sub-06/sub-08 hV4 acc=81%/81%
  message was LDA-specific; under FE the per-subject numbers diverge).
- Pipeline panel relabeled: same FE encoder, two CV schemes
  ("LORO: within-color CV" + "LOCO: across-color CV").
- LOCO illustration retained (sub-06 hV4 MAE 62° vs sub-09 V1 MAE 103°).

Layout (3 panels):
  [ A | B ]
  [   C   ]
  A: 8 isoluminant DKL stimuli.
  B: Pipeline — same FE encoder, dual CV schemes.
  C: LOCO reconstruction example.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import numpy as np

from _data import (
    ROI_KEYS, ROI_LBLS, HUE_ANGLES_DEG, hue_deg_to_srgb,
    load_loco_subject, loco_fold_predictions,
    HC_COLOR, CVD_COLOR,
)

OUT_DIR = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/docs/OHBM_abstract/figures/v8')
OUT_DIR.mkdir(parents=True, exist_ok=True)

mpl.rcParams.update({
    'font.family': 'Helvetica',
    'font.size': 9,
    'axes.linewidth': 0.8,
    'pdf.fonttype': 42,
    'ps.fonttype':  42,
})


# --------------------------------------------------------------------------- #
def panel_A(ax):
    """Stimulus design wheel — 8 isoluminant DKL hues."""
    ax.set_aspect('equal')
    ax.axis('off')

    n_bands = 360
    r_inner, r_outer = 0.50, 0.74
    for k in range(n_bands):
        deg = (k + 0.5)
        rgb = hue_deg_to_srgb(deg)
        wedge = mpatches.Wedge((0, 0), r_outer, k, k+1, width=r_outer-r_inner,
                                facecolor=rgb, edgecolor='none')
        ax.add_patch(wedge)

    R = 0.94
    names = ['Red', 'Orange', 'Yellow', 'Green', 'Cyan', 'Blue', 'Purple', 'Magenta']
    for i, deg in enumerate(HUE_ANGLES_DEG):
        rad = np.deg2rad(deg)
        x, y = R * np.cos(rad), R * np.sin(rad)
        rgb = hue_deg_to_srgb(deg)
        ax.scatter([x], [y], s=300, facecolor=rgb,
                   edgecolor='black', linewidth=0.8, zorder=5)
        tx, ty = 1.18 * np.cos(rad), 1.18 * np.sin(rad)
        ha = 'left' if np.cos(rad) > 0.1 else ('right' if np.cos(rad) < -0.1 else 'center')
        va = 'bottom' if np.sin(rad) > 0.1 else ('top' if np.sin(rad) < -0.1 else 'center')
        ax.text(tx, ty, f'{names[i]}\n({int(deg)}°)',
                ha=ha, va=va, fontsize=7)

    ax.annotate('', xy=(1.4, 0), xytext=(-1.4, 0),
                arrowprops=dict(arrowstyle='->', lw=0.6, color='gray'))
    ax.annotate('', xy=(0, 1.4), xytext=(0, -1.4),
                arrowprops=dict(arrowstyle='->', lw=0.6, color='gray'))
    ax.text(1.42, -0.06, '+a*', fontsize=8, color='gray', va='top')
    ax.text(0.04, 1.42, '+b*', fontsize=8, color='gray')
    ax.text(0, -1.55, 'L* = 75 (isoluminant)', ha='center', fontsize=8, color='dimgray')

    ax.set_xlim(-1.6, 1.6); ax.set_ylim(-1.7, 1.55)
    ax.set_title('A  Stimulus design — 8 DKL hues',
                 loc='left', fontweight='bold', y=1.00)


# --------------------------------------------------------------------------- #
def _flow_box(ax, x, y, w, h, label, sub='', color='#e9eef7', edge='#2c3e50'):
    box = FancyBboxPatch((x - w/2, y - h/2), w, h,
                         boxstyle='round,pad=0.012,rounding_size=0.018',
                         facecolor=color, edgecolor=edge, linewidth=0.9, zorder=3)
    ax.add_patch(box)
    ax.text(x, y + (h*0.08 if sub else 0), label,
            ha='center', va='center', fontsize=8.0, fontweight='bold', zorder=4)
    if sub:
        ax.text(x, y - h*0.26, sub, ha='center', va='center',
                fontsize=6.6, color='#445', zorder=4)


def _flow_arrow(ax, x0, y0, x1, y1, color='black'):
    ar = FancyArrowPatch((x0, y0), (x1, y1),
                         arrowstyle='-|>', mutation_scale=11,
                         lw=1.0, color=color, zorder=2)
    ax.add_patch(ar)


def panel_B(ax):
    """Pipeline — same FE encoder, dual CV schemes (LORO + LOCO)."""
    ax.set_aspect('auto')
    ax.set_xlim(0, 10); ax.set_ylim(0, 6.2)
    ax.axis('off')
    ax.set_title('B  Pipeline — same FE encoder, two CV schemes',
                 loc='left', fontweight='bold', y=1.00)

    # serial chain top row (shifted left to keep FE-6 within frame)
    _flow_box(ax, 0.9, 5.3, 1.6, 0.7, 'fMRIPrep',  'BOLD preproc.')
    _flow_box(ax, 2.8, 5.3, 1.6, 0.7, 'Wang ROI',  'V1, V2, V3, hV4')
    _flow_box(ax, 4.7, 5.3, 1.6, 0.7, 'GLM betas', '6 runs × 8 colours')
    _flow_box(ax, 6.6, 5.3, 1.6, 0.7, 'Procrustes', 'within-subj align')
    for x0, x1 in [(1.70, 2.00), (3.60, 3.90), (5.50, 5.80)]:
        _flow_arrow(ax, x0, 5.3, x1, 5.3)
    _flow_arrow(ax, 7.40, 5.3, 7.85, 5.3)

    # shared encoder node
    _flow_box(ax, 8.55, 5.3, 1.10, 0.78, 'FE-6 encoder', 'pooled W, ridge λ',
              color='#fff0d6', edge='#b8860b')

    # downward into split bus
    _flow_arrow(ax, 8.55, 4.86, 8.55, 4.20)
    ax.text(8.55, 4.00, 'Same W feeds both CV schemes', ha='center',
            fontsize=7, fontstyle='italic', color='#7a5500')

    # branch arrows
    _flow_arrow(ax, 8.55, 3.65, 6.6, 2.85)
    _flow_arrow(ax, 8.55, 3.65, 3.2, 2.85)

    # Branch 1: LORO (within-color CV)
    _flow_box(ax, 6.6, 2.50, 2.2, 0.78,
              'LORO',
              'leave-one-RUN-out',
              color='#cfe1f6', edge='#1f77b4')
    _flow_box(ax, 6.6, 1.30, 2.4, 0.75,
              'Classification accuracy',
              'all 8 colours in train',
              color='#eaf2fa', edge='#1f77b4')
    _flow_arrow(ax, 6.6, 2.11, 6.6, 1.68)
    ax.text(6.6, 0.55, 'within-color generalization',
            ha='center', fontsize=7.2, color='#0d3b66', fontstyle='italic')

    # Branch 2: LOCO (across-color CV)
    _flow_box(ax, 3.2, 2.50, 2.2, 0.78,
              'LOCO',
              'leave-one-COLOUR-out',
              color='#fde2c8', edge='#d96b00')
    _flow_box(ax, 3.2, 1.30, 2.4, 0.75,
              'Circular MAE on novel hue',
              'held-out colour excluded',
              color='#fcefdc', edge='#d96b00')
    _flow_arrow(ax, 3.2, 2.11, 3.2, 1.68)
    ax.text(3.2, 0.55, 'across-color interpolation',
            ha='center', fontsize=7.2, color='#7a3a05', fontstyle='italic')

    # caption (bottom)
    ax.text(5.0, 0.10,
            'Same readout, two CV schemes — dissociation indexes operation, not model class.',
            ha='center', fontsize=7.4, color='dimgray')


# --------------------------------------------------------------------------- #
def _empty_polar(ax):
    ax.set_aspect('equal')
    ax.axis('off')
    th = np.linspace(0, 2*np.pi, 360)
    ax.plot(np.cos(th), np.sin(th), color='lightgray', lw=0.7)


def _draw_color_wheel(ax, r_inner=0.85, r_outer=1.0):
    for k in range(360):
        deg = k + 0.5
        rgb = hue_deg_to_srgb(deg)
        w = mpatches.Wedge((0, 0), r_outer, k, k + 1, width=r_outer - r_inner,
                           facecolor=rgb, edgecolor='none', zorder=1)
        ax.add_patch(w)


def _draw_loco_arrows(ax, test_hues, pred_means, edge_color, *,
                      r_pres=0.78, r_pred=0.52):
    for true_deg, pred_deg in zip(test_hues, pred_means):
        rad_true = np.deg2rad(true_deg)
        rad_pred = np.deg2rad(pred_deg)
        rgb = hue_deg_to_srgb(true_deg)
        ax.scatter([r_pres * np.cos(rad_true)], [r_pres * np.sin(rad_true)],
                   s=140, facecolor=rgb, edgecolor='black',
                   linewidth=0.6, zorder=4)
        ax.scatter([r_pred * np.cos(rad_pred)], [r_pred * np.sin(rad_pred)],
                   s=90, facecolor='white', edgecolor=edge_color,
                   linewidth=1.4, zorder=4)
        ax.annotate('',
                    xy=(r_pred * np.cos(rad_pred), r_pred * np.sin(rad_pred)),
                    xytext=(r_pres * np.cos(rad_true), r_pres * np.sin(rad_true)),
                    arrowprops=dict(arrowstyle='->', lw=0.6,
                                    color=edge_color, alpha=0.7), zorder=3)


def panel_C(ax,
            hc_sub='sub-06', hc_roi='V4',
            cvd_sub='sub-09', cvd_roi='V1'):
    """LOCO interpolation — HC (good) vs CVD (poor)."""
    _empty_polar(ax)
    ax.set_xlim(-1.65, 1.65); ax.set_ylim(-1.4, 1.4)
    _draw_color_wheel(ax, r_inner=0.86, r_outer=1.00)

    hc_t, hc_p, _ = loco_fold_predictions(hc_sub, hc_roi, 'ForwardEncoding')
    cvd_t, cvd_p, _ = loco_fold_predictions(cvd_sub, cvd_roi, 'ForwardEncoding')

    _draw_loco_arrows(ax, hc_t, hc_p, HC_COLOR,
                      r_pres=0.78, r_pred=0.55)
    _draw_loco_arrows(ax, cvd_t, cvd_p, CVD_COLOR,
                      r_pres=0.78, r_pred=0.28)

    hc_mae = load_loco_subject(hc_sub)['results'][hc_roi]['ForwardEncoding']['overall_mae']
    cvd_mae = load_loco_subject(cvd_sub)['results'][cvd_roi]['ForwardEncoding']['overall_mae']

    ax.text(0, -1.20,
            f'{hc_sub} (HC) {ROI_LBLS[ROI_KEYS.index(hc_roi)]}: MAE={hc_mae:.1f}°\n'
            f'{cvd_sub} (CVD) {ROI_LBLS[ROI_KEYS.index(cvd_roi)]}: MAE={cvd_mae:.1f}°  (chance=90°)',
            ha='center', fontsize=8)

    ax.scatter([-1.45], [1.10], s=110, facecolor='white', edgecolor=HC_COLOR, linewidth=1.4)
    ax.text(-1.30, 1.10, f'{hc_sub} HC ({ROI_LBLS[ROI_KEYS.index(hc_roi)]})', va='center', fontsize=7)
    ax.scatter([-1.45], [0.92], s=90, facecolor='white', edgecolor=CVD_COLOR, linewidth=1.4)
    ax.text(-1.30, 0.92, f'{cvd_sub} CVD ({ROI_LBLS[ROI_KEYS.index(cvd_roi)]})', va='center', fontsize=7)
    ax.scatter([-1.45], [0.74], s=110, facecolor='lightgray', edgecolor='black', linewidth=0.6)
    ax.text(-1.30, 0.74, 'presented', va='center', fontsize=7)

    ax.set_title('C  LOCO reconstruction — interpolation impaired in CVD (FE)',
                 loc='left', fontweight='bold', y=0.99)


# --------------------------------------------------------------------------- #
def main():
    fig = plt.figure(figsize=(10.5, 9.6))
    gs = fig.add_gridspec(2, 2, left=0.03, right=0.98, top=0.95, bottom=0.03,
                          hspace=0.32, wspace=0.10,
                          height_ratios=[1.0, 1.05])
    ax_A = fig.add_subplot(gs[0, 0])
    ax_B = fig.add_subplot(gs[0, 1])
    ax_C = fig.add_subplot(gs[1, :])   # full-width LOCO illustration

    panel_A(ax_A)
    panel_B(ax_B)
    panel_C(ax_C, hc_sub='sub-06', hc_roi='V4',
                  cvd_sub='sub-09', cvd_roi='V1')

    fig.suptitle('Figure 1.  Stimulus design, dual-CV pipeline (same FE encoder), and LOCO reconstruction example.',
                 fontsize=10, fontweight='bold', x=0.05, y=0.985, ha='left')

    fig.savefig(OUT_DIR / 'Figure_1_v8_1.pdf')
    fig.savefig(OUT_DIR / 'Figure_1_v8_1.png', dpi=350)
    plt.close(fig)
    print('Wrote', OUT_DIR / 'Figure_1_v8_1.{pdf,png}')

    info = {
        'panel_C': {
            'hc_sub': 'sub-06', 'hc_roi': 'hV4',
            'hc_mae': load_loco_subject('sub-06')['results']['V4']['ForwardEncoding']['overall_mae'],
            'cvd_sub': 'sub-09', 'cvd_roi': 'V1',
            'cvd_mae': load_loco_subject('sub-09')['results']['V1']['ForwardEncoding']['overall_mae'],
        },
    }
    with open(OUT_DIR / 'Figure_1_v8_1_numbers.json', 'w') as f:
        json.dump(info, f, indent=2)
    print('Wrote', OUT_DIR / 'Figure_1_v8_1_numbers.json')


if __name__ == '__main__':
    main()
