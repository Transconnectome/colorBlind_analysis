"""
LOCO intuition v9 — RADIAL SPOKES design (alternative to wedge fan).

For each held-out color, draw a spoke at the true hue angle. Spoke length =
mean absolute circular prediction error (degrees). Spoke head dot = mean
predicted hue position. Reference rings at 45° and 90° (chance) for scale.

HC = short spokes (predictions land near truth).
CVD = long spokes (predictions land far).

Clean, no overlap, instant read.
"""
from __future__ import annotations
from pathlib import Path
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge, Circle

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

def signed(a, b):
    return (a - b + 180) % 360 - 180

def circ_mean(angs):
    rad = np.deg2rad(angs)
    return np.rad2deg(np.arctan2(np.sin(rad).mean(), np.cos(rad).mean())) % 360


def load_loco(sub, roi):
    with open(LOCO_DIR/f'{sub}_loco.json') as f:
        d = json.load(f)
    e = d['results'][roi]['ForwardEncoding']
    return [{'th': float(fr['test_hue']),
             'ph': np.asarray(fr['pred_hues'], dtype=float)}
            for fr in e['fold_results']], float(e['overall_mae'])


def draw_ring(ax, *, r_outer=0.95, r_inner=0.78, missing_idx=None, dim=False):
    for i, ang in enumerate(HUE_ANGLES):
        a0, a1 = ang-22.5, ang+22.5
        if missing_idx is not None and i == missing_idx:
            ax.add_patch(Wedge((0,0), r_outer, a0, a1, width=r_outer-r_inner,
                                facecolor='#1a1a1a', edgecolor='white', lw=1.4,
                                zorder=3))
        else:
            alpha = 0.5 if dim else 1.0
            ax.add_patch(Wedge((0,0), r_outer, a0, a1, width=r_outer-r_inner,
                                facecolor=HUE_RGB[i], edgecolor='white', lw=1.2,
                                alpha=alpha, zorder=2))


def draw_reference_rings(ax, R_max):
    """Reference rings showing 45° and 90° errors (radius = error/180 * R_max)."""
    for err_deg, ls, lbl in [(45, ':', '45° (adjacent)'), (90, '--', '90° (chance)')]:
        r = (err_deg / 180.0) * (R_max - 1.0) + 1.0   # scale: 0° at the wheel edge, 180° at outer radius
        ax.add_patch(Circle((0,0), r, fill=False, edgecolor='gray',
                            linestyle=ls, lw=0.9, alpha=0.7, zorder=1))
        ax.text(0, -r-0.04, lbl, ha='center', va='top', fontsize=7,
                color='gray', alpha=0.9)


def draw_spokes(ax, sub, roi, title):
    folds, overall_mae = load_loco(sub, roi)
    R_max = 2.4         # outer radial extent
    draw_ring(ax)
    draw_reference_rings(ax, R_max)

    for fr in folds:
        truth = fr['th']
        preds = fr['ph']
        # Mean absolute angular error (in degrees)
        errs = np.abs([signed(p, truth) for p in preds])
        mean_err = float(np.mean(errs))
        # Spoke length: 0° = wheel edge (r=1.0), 180° = R_max
        spoke_r = 1.0 + (mean_err / 180.0) * (R_max - 1.0)
        # Spoke at the true hue angle
        x0, y0 = deg2xy(truth, 1.0)
        x1, y1 = deg2xy(truth, spoke_r)
        idx = int(round((truth % 360)/45.0)) % 8
        rgb = HUE_RGB[idx]
        ax.plot([x0, x1], [y0, y1], '-', color=rgb, lw=4.0, solid_capstyle='round',
                zorder=5)
        # Spoke head: bigger dot
        ax.scatter([x1],[y1], s=130, c=[rgb], edgecolors='black', linewidths=0.8,
                   zorder=6)
        # Error value as text label outside the head
        tx, ty = deg2xy(truth, spoke_r + 0.18)
        ax.text(tx, ty, f'{mean_err:.0f}°', ha='center', va='center',
                fontsize=8.5, color='black', weight='bold')

    ax.set_aspect('equal'); ax.axis('off')
    ax.set_xlim(-R_max-0.5, R_max+0.5); ax.set_ylim(-R_max-0.7, R_max+0.5)
    ax.text(0, R_max+0.25, title, ha='center', va='center',
            fontsize=12, weight='bold')
    ax.text(0, -R_max-0.45,
            f'circular MAE (mean across 8 colors) = {overall_mae:.0f}°',
            ha='center', va='center', fontsize=10)


def draw_concept(ax, R_max=2.4):
    miss = 4  # Cyan
    draw_ring(ax, missing_idx=miss, dim=True)
    qx, qy = deg2xy(HUE_ANGLES[miss], 0.86)
    ax.text(qx, qy, '?', ha='center', va='center', color='white',
            fontsize=24, weight='bold', zorder=5)

    truth = HUE_ANGLES[miss]
    # truth indicator outside
    tx, ty = deg2xy(truth, R_max-0.2)
    ax.scatter([tx],[ty], marker='*', s=380, c='white',
               edgecolors='black', linewidths=1.4, zorder=8)
    ax.annotate('TRUTH', (tx, ty), xytext=(-10, -25), textcoords='offset points',
                fontsize=10, weight='bold')

    # HC: short spoke (~15° error)
    hc_ang = truth + 15
    hc_r = 1.0 + (15/180.0)*(R_max-1.0)
    x0,y0 = deg2xy(truth, 1.0)   # spoke base AT true hue
    x1,y1 = deg2xy(hc_ang, hc_r)
    ax.plot([x0,x1],[y0,y1], '-', color='#1f77b4', lw=3.5, solid_capstyle='round')
    ax.scatter([x1],[y1], s=240, c='#1f77b4', edgecolors='k', linewidths=1.0, zorder=8)
    ax.text(x1-0.1, y1-0.3, 'HC ≈ 15°', ha='right', va='top',
            fontsize=10, color='#1f77b4', weight='bold')

    # CVD: long spoke (~130° error)
    cv_ang = truth + 130
    cv_r = 1.0 + (130/180.0)*(R_max-1.0)
    x2,y2 = deg2xy(cv_ang, cv_r)
    ax.plot([x0,x1*0+x2*0, x2],[y0,y1*0+y2*0, y2], '-', color='#d62728', lw=3.5, solid_capstyle='round')
    # Simpler: draw straight from base
    ax.plot([x0, x2],[y0, y2], '-', color='#d62728', lw=3.5, solid_capstyle='round')
    ax.scatter([x2],[y2], s=240, c='#d62728', edgecolors='k', linewidths=1.0, zorder=8)
    ax.text(x2+0.1, y2, 'CVD ≈ 130°', ha='left', va='center',
            fontsize=10, color='#d62728', weight='bold')

    ax.set_aspect('equal'); ax.axis('off')
    ax.set_xlim(-R_max-0.5, R_max+0.5); ax.set_ylim(-R_max-0.7, R_max+0.5)
    ax.text(0, R_max+0.25, 'What is LOCO?', ha='center', va='center',
            fontsize=14, weight='bold')
    ax.text(0, -R_max-0.45,
            'Hide one hue → train on 7 → measure where the model puts it back\n'
            'spoke length = mean angular error (0° = wheel edge, 90° = chance ring)',
            ha='center', va='center', fontsize=10)


def main():
    fig, axes = plt.subplots(1, 3, figsize=(18, 7.5))
    plt.subplots_adjust(wspace=0.04, top=0.96, bottom=0.04, left=0.01, right=0.99)
    draw_concept(axes[0])
    draw_spokes(axes[1], 'sub-06', 'V4', 'HC sub-06, hV4 — short spokes')
    draw_spokes(axes[2], 'sub-09', 'V1', 'CVD sub-09, V1 — long spokes')
    fig.suptitle('Figure 1C (v9 spokes draft) — LOCO error per color, '
                 'spoke length = mean angular error',
                 fontsize=13, weight='bold', y=1.005)
    out = OUT/'loco_spokes_v9_draft.png'
    fig.savefig(out, dpi=200, bbox_inches='tight')
    print('wrote:', out)


if __name__ == '__main__':
    main()
