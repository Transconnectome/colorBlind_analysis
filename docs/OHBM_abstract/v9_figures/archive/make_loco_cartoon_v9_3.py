"""
LOCO intuition v9.3 — minimal/clean.

Design rules (per user feedback):
  - Interior of the wheel must stay EMPTY (no spaghetti, no dots).
  - All text well separated from the figure (no overlap with the wheel).
  - Make every marker readable at 2 m.

Layout (1 row, 3 panels):
  (1) Concept — color wheel with one slot dimmed, "?", and two big example
      markers (HC blue near truth, CVD red far) OUTSIDE the wheel.
  (2) HC sub-06 hV4 — 8 transparent wedges outside the wheel.
       Each wedge spans the angular range of 6 per-run predictions.
       Color = the true held-out hue. Width = uncertainty.
  (3) CVD sub-09 V1 — same format, dramatically wider wedges.

NO internal markers. Truth ★ stars are placed on the inner ring boundary so they
don't overlap with the wedges (which sit outside).
"""
from __future__ import annotations
from pathlib import Path
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge, FancyArrowPatch

PROJ = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis')
LOCO_DIR = PROJ/'analysis/phase3_decoder_comparing/results/loco/procrustes'
OUT = PROJ/'docs/OHBM_abstract/v9_figures'

HUE_RGB = np.array([
    [0.90,0.20,0.20],[0.95,0.55,0.10],[0.95,0.85,0.15],[0.20,0.75,0.25],
    [0.10,0.80,0.85],[0.20,0.40,0.95],[0.55,0.20,0.85],[0.90,0.30,0.75]])
HUE_LABELS = ['Red','Orange','Yellow','Green','Cyan','Blue','Purple','Magenta']
HUE_ANGLES = np.arange(0,360,45)


def deg2xy(deg, r):
    rad = np.deg2rad(deg); return r*np.cos(rad), r*np.sin(rad)

def signed_diff(a, b):
    return (a - b + 180) % 360 - 180


def load_loco(sub, roi):
    with open(LOCO_DIR/f'{sub}_loco.json') as f:
        d = json.load(f)
    e = d['results'][roi]['ForwardEncoding']
    return [{'th': float(fr['test_hue']),
             'ph': np.asarray(fr['pred_hues'], dtype=float)}
            for fr in e['fold_results']], float(e['overall_mae'])


def draw_clean_ring(ax, *, r_outer=1.0, r_inner=0.78, missing_idx=None, dim=False):
    for i, ang in enumerate(HUE_ANGLES):
        a0, a1 = ang-22.5, ang+22.5
        if missing_idx is not None and i == missing_idx:
            ax.add_patch(Wedge((0,0), r_outer, a0, a1, width=r_outer-r_inner,
                                facecolor='#1a1a1a', edgecolor='white', lw=1.4,
                                zorder=3))
        else:
            alpha = 0.45 if dim else 1.0
            ax.add_patch(Wedge((0,0), r_outer, a0, a1, width=r_outer-r_inner,
                                facecolor=HUE_RGB[i], edgecolor='white', lw=1.2,
                                alpha=alpha, zorder=2))
    ax.set_aspect('equal'); ax.axis('off')


def draw_concept(ax):
    miss = 4  # Cyan
    draw_clean_ring(ax, missing_idx=miss, dim=True)
    qx, qy = deg2xy(HUE_ANGLES[miss], 0.89)
    ax.text(qx, qy, '?', ha='center', va='center', color='white',
            fontsize=28, weight='bold', zorder=5)
    # Example outcome markers OUTSIDE the wheel
    truth = HUE_ANGLES[miss]
    # truth: star OUTSIDE the wheel at r=1.20
    tx, ty = deg2xy(truth, 1.22)
    ax.scatter([tx],[ty], marker='*', s=420, c='white',
               edgecolors='black', linewidths=1.4, zorder=8)
    ax.text(tx - 0.05, ty + 0.18, 'TRUTH', ha='center', va='center',
            fontsize=10, weight='bold')

    # HC marker: ~15° from truth, big dot
    hc_ang = truth + 15
    hx, hy = deg2xy(hc_ang, 1.22)
    ax.scatter([hx],[hy], s=260, c='#1f77b4', edgecolors='k', linewidths=1.2, zorder=8)
    ax.text(hx + 0.30, hy, 'HC\nlands near',
            ha='left', va='center', fontsize=10, color='#1f77b4', weight='bold')

    # CVD marker: ~130° away
    cv_ang = truth + 130
    cx, cy = deg2xy(cv_ang, 1.22)
    ax.scatter([cx],[cy], s=260, c='#d62728', edgecolors='k', linewidths=1.2, zorder=8)
    ax.text(cx - 0.22, cy - 0.08, 'CVD\nlands far',
            ha='right', va='top', fontsize=10, color='#d62728', weight='bold')

    ax.text(0, 1.85, 'What is LOCO?', ha='center', va='center',
            fontsize=14, weight='bold')
    ax.text(0, -1.85,
            'Hide one hue. Train on the other 7.\n'
            'How close does the model put back the missing one?',
            ha='center', va='center', fontsize=11)
    ax.set_xlim(-2.0, 2.0); ax.set_ylim(-2.0, 2.0)


def draw_fan(ax, sub, roi, title, sub_mae_text):
    folds, overall_mae = load_loco(sub, roi)
    draw_clean_ring(ax)
    # For each fold, wedge OUTSIDE the wheel; min/max of signed diffs
    for fr in folds:
        truth = fr['th']
        diffs = np.array([signed_diff(p, truth) for p in fr['ph']])
        lo, hi = diffs.min(), diffs.max()
        # Use radial band r=[1.10, 1.35]
        idx = int(round((truth % 360)/45.0)) % 8
        rgb = HUE_RGB[idx]
        # Span centered on truth+lo to truth+hi
        a0 = truth + lo; a1 = truth + hi
        if a1 - a0 < 4:           # too thin to see — give a minimum
            mid = (a0 + a1)/2; a0, a1 = mid-2, mid+2
        ax.add_patch(Wedge((0,0), 1.40, a0, a1, width=0.30,
                            facecolor=rgb, alpha=0.78,
                            edgecolor='black', lw=0.4, zorder=5))
        # Truth marker on the ring outer edge
        tx, ty = deg2xy(truth, 1.04)
        ax.scatter([tx],[ty], marker='*', s=150, c='white',
                   edgecolors='black', linewidths=1.0, zorder=8)
    ax.text(0, 1.85, title, ha='center', va='center', fontsize=12, weight='bold')
    ax.text(0, -1.85, sub_mae_text, ha='center', va='center', fontsize=10.5)
    ax.set_xlim(-2.0, 2.0); ax.set_ylim(-2.0, 2.0)


def main():
    fig, axes = plt.subplots(1, 3, figsize=(17, 7))
    plt.subplots_adjust(wspace=0.02, top=0.96, bottom=0.04, left=0.01, right=0.99)
    draw_concept(axes[0])
    draw_fan(axes[1], 'sub-06', 'V4',
             'HC sub-06, hV4',
             'wedges are tight → model knows where each hue belongs\n'
             'circular MAE = 62°  (chance = 90°)')
    draw_fan(axes[2], 'sub-09', 'V1',
             'CVD sub-09, V1',
             'wedges sprawl across the wheel → predictions ≈ chance\n'
             'circular MAE = 103°  (chance = 90°)')
    fig.suptitle('Figure 1C (v9.3) — LOCO: leave-one-COLOUR-out, wedge = '
                 'angular range of 6 per-run predictions',
                 fontsize=13, weight='bold', y=1.005)
    out = OUT/'loco_cartoon_v9_3_draft.png'
    fig.savefig(out, dpi=200, bbox_inches='tight')
    print('wrote:', out)


if __name__ == '__main__':
    main()
