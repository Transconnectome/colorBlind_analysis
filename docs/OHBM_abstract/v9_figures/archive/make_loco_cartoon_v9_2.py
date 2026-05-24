"""
LOCO intuition v9.2 — use real wedge fans (angular ranges) per held-out color.

Each held-out color = a transparent wedge spanning the angular extent of the 6
per-run predictions, anchored on the ring at the TRUTH angle. The wedge's
*color* matches the held-out hue, its *width* shows prediction spread.

HC (sub-06 hV4): 8 narrow wedges, each near its true slot.
CVD (sub-09 V1): 8 wide wedges, smeared across the wheel.

Concept panel uses a clear "?" + two example arrows (HC near, CVD far).
"""
from __future__ import annotations
from pathlib import Path
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge, FancyArrowPatch

PROJ = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis')
LOCO_DIR = PROJ / 'analysis/phase3_decoder_comparing/results/loco/procrustes'
OUT = PROJ / 'docs/OHBM_abstract/v9_figures'

HUE_RGB = np.array([
    [0.90,0.20,0.20],[0.95,0.55,0.10],[0.95,0.85,0.15],[0.20,0.75,0.25],
    [0.10,0.80,0.85],[0.20,0.40,0.95],[0.55,0.20,0.85],[0.90,0.30,0.75]])
HUE_LABELS = ['Red','Orange','Yellow','Green','Cyan','Blue','Purple','Magenta']
HUE_ANGLES = np.arange(0, 360, 45)


def deg2xy(deg, r):
    rad = np.deg2rad(deg)
    return r*np.cos(rad), r*np.sin(rad)


def circ_mean_deg(angs):
    rad = np.deg2rad(angs)
    return np.rad2deg(np.arctan2(np.sin(rad).mean(), np.cos(rad).mean())) % 360


def signed_diff_deg(a, b):
    return (a - b + 180) % 360 - 180


def load_loco(sub, roi):
    with open(LOCO_DIR/f'{sub}_loco.json') as f:
        d = json.load(f)
    e = d['results'][roi]['ForwardEncoding']
    return [{'th': float(fr['test_hue']),
             'ph': np.asarray(fr['pred_hues'], dtype=float)}
            for fr in e['fold_results']], float(e['overall_mae'])


def draw_ring(ax, *, r_outer=1.0, r_inner=0.75, missing_idx=None, dim=False):
    for i, ang in enumerate(HUE_ANGLES):
        a0, a1 = ang-22.5, ang+22.5
        if missing_idx is not None and i == missing_idx:
            w = Wedge((0,0), r_outer, a0, a1, width=r_outer-r_inner,
                      facecolor='#1a1a1a', edgecolor='white', lw=1.2, zorder=3)
        else:
            alpha = 0.4 if dim else 1.0
            w = Wedge((0,0), r_outer, a0, a1, width=r_outer-r_inner,
                      facecolor=HUE_RGB[i], edgecolor='white', lw=1.0,
                      alpha=alpha, zorder=2)
        ax.add_patch(w)
    ax.set_aspect('equal')
    ax.set_xlim(-1.4, 1.4); ax.set_ylim(-1.4, 1.4)
    ax.axis('off')


def draw_concept(ax):
    miss = 4  # Cyan
    draw_ring(ax, missing_idx=miss, dim=True)
    # ? in slot
    qx, qy = deg2xy(HUE_ANGLES[miss], 0.875)
    ax.text(qx, qy, '?', ha='center', va='center', color='white',
            fontsize=20, weight='bold', zorder=5)

    # Show two candidate predictions
    # HC arrow: lands at +15° from truth
    truth = HUE_ANGLES[miss]
    hc_ang = truth + 18
    cvd_ang = truth + 130

    cx, cy = 0, 0
    hx, hy = deg2xy(hc_ang, 0.6)
    vx, vy = deg2xy(cvd_ang, 0.6)
    tx, ty = deg2xy(truth, 0.6)

    # truth marker outside ring
    tx_out, ty_out = deg2xy(truth, 1.18)
    ax.scatter([tx_out],[ty_out], marker='*', s=260, c='white',
               edgecolors='black', linewidths=1.2, zorder=8)
    ax.annotate('truth', (tx_out, ty_out), xytext=(12,-3),
                textcoords='offset points', fontsize=9, color='black', weight='bold')

    # HC prediction (lands near truth, just outside the ring)
    hx, hy = deg2xy(hc_ang, 1.18)
    ax.scatter([hx],[hy], s=130, c='#1f77b4', edgecolors='k', linewidths=0.8, zorder=8)
    ax.annotate('HC\n~12° gap', (hx,hy), xytext=(10,-3),
                textcoords='offset points', fontsize=9, color='#1f77b4', weight='bold')

    # CVD prediction (lands far)
    vx, vy = deg2xy(cvd_ang, 1.18)
    ax.scatter([vx],[vy], s=130, c='#d62728', edgecolors='k', linewidths=0.8, zorder=8)
    ax.annotate('CVD\n~130° gap', (vx,vy), xytext=(-58,-3),
                textcoords='offset points', fontsize=9, color='#d62728', weight='bold')

    ax.text(0, 1.55, 'What is LOCO?', ha='center', va='center',
            fontsize=13, weight='bold')
    ax.text(0, -1.55,
            'Hide one hue (here Cyan).  Train on the 7 neighbors.\n'
            'How close does the model land on the missing one?\n'
            'Distance = circular MAE (0° perfect, 90° chance).',
            ha='center', va='center', fontsize=9.5)
    ax.set_xlim(-1.7, 1.7); ax.set_ylim(-1.7, 1.7)


def draw_fan(ax, sub, roi, label):
    folds, overall_mae = load_loco(sub, roi)
    draw_ring(ax)
    # For each held-out color, draw a transparent wedge whose angular extent
    # is the per-run prediction range (using min / max of unwrapped predictions
    # relative to the truth). Place wedge at outer ring (slightly outside).
    for fr in folds:
        truth = fr['th']
        preds = fr['ph']
        # Signed differences from truth, in (-180, 180]
        diffs = np.array([signed_diff_deg(p, truth) for p in preds])
        # Use the angular range covered
        lo = diffs.min()
        hi = diffs.max()
        # Wedge spans (truth+lo) to (truth+hi)
        a0 = (truth + lo)
        a1 = (truth + hi)
        # Pick the color of the held-out hue
        idx = int(round((truth % 360) / 45.0)) % 8
        rgb = HUE_RGB[idx]
        w = Wedge((0,0), 1.30, a0, a1, width=0.20,
                  facecolor=rgb, alpha=0.55, edgecolor=rgb,
                  linewidth=0.5, zorder=4)
        ax.add_patch(w)
        # Mark fold-mean prediction with small dot
        mean_p = circ_mean_deg(preds)
        mx, my = deg2xy(mean_p, 1.20)
        ax.scatter([mx],[my], s=22, c=[rgb], edgecolors='k', linewidths=0.5,
                   zorder=6)
        # Mark truth with a notch on the inner ring
        tx, ty = deg2xy(truth, 0.74)
        ax.scatter([tx],[ty], marker='*', s=55, c='white',
                   edgecolors='k', linewidths=0.6, zorder=7)

    ax.text(0, 1.55, label, ha='center', va='center',
            fontsize=11, weight='bold')
    ax.text(0, -1.55,
            f'overall circular MAE = {overall_mae:.0f}°  (chance 90°)\n'
            'Outer wedges = range of per-run predictions (6 runs per held-out hue)\n'
            'Dots = fold-mean prediction;  ★ on inner ring = true held-out hue',
            ha='center', va='center', fontsize=8.5)
    ax.set_xlim(-1.7, 1.7); ax.set_ylim(-1.7, 1.7)


def main():
    fig, axes = plt.subplots(1, 3, figsize=(15.5, 5.8))
    plt.subplots_adjust(wspace=0.04, top=0.93, bottom=0.05, left=0.02, right=0.98)

    draw_concept(axes[0])
    draw_fan(axes[1], 'sub-06', 'V4',
             'HC sub-06, hV4 — wedges hug the true hues')
    draw_fan(axes[2], 'sub-09', 'V1',
             'CVD sub-09, V1 — wedges spread (near chance)')

    fig.suptitle('Figure 1C (v9.2 draft) — LOCO: leave-one-COLOUR-out interpolation',
                 fontsize=12.5, weight='bold', y=0.99)
    out = OUT/'loco_cartoon_v9_2_draft.png'
    fig.savefig(out, dpi=200, bbox_inches='tight')
    print('wrote:', out)


if __name__ == '__main__':
    main()
