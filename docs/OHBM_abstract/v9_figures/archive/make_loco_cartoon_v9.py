"""
LOCO intuition cartoon + wedge fan (v9 Fig 1C replacement).

Left panel  — CONCEPT (cartoon):
    "Brain never saw this hue during training. Can the model fill in the gap?"
    - Color wheel with one slot (e.g. cyan) blacked out + "?" mark
    - 7 training neighbors shown saturated
    - Arrow from "model" -> recovered hue position; circular MAE shown

Middle panel — HC example (sub-06 hV4, MAE 62°):
    - Polar/wedge fan showing per-run predictions for each of 8 held-out colors
    - HC fan = tight wedge near truth (8 small wedges, near each true angle)

Right panel — CVD example (sub-09 V1, MAE 103° ~ chance):
    - Same format
    - CVD fan = wide spread covering most of the circle
    - The fan WIDTH itself communicates "the model has no idea"
"""
from __future__ import annotations
from pathlib import Path
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge, Circle, FancyArrowPatch
from matplotlib.collections import PatchCollection

PROJ = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis')
LOCO_DIR = PROJ / 'analysis/phase3_decoder_comparing/results/loco/procrustes'
OUT = PROJ / 'docs/OHBM_abstract/v9_figures'

HUE_RGB = np.array([
    [0.90,0.20,0.20],[0.95,0.55,0.10],[0.95,0.85,0.15],[0.20,0.75,0.25],
    [0.10,0.80,0.85],[0.20,0.40,0.95],[0.55,0.20,0.85],[0.90,0.30,0.75]])
HUE_LABELS = ['Red','Orange','Yellow','Green','Cyan','Blue','Purple','Magenta']
HUE_ANGLES = np.arange(0, 360, 45)   # degrees, CCW from +x


def deg2xy(deg, r):
    rad = np.deg2rad(deg)
    return r * np.cos(rad), r * np.sin(rad)


def load_loco(sub: str, roi: str):
    with open(LOCO_DIR / f'{sub}_loco.json') as f:
        d = json.load(f)
    e = d['results'][roi]['ForwardEncoding']
    folds = []
    for fr in e['fold_results']:
        folds.append({
            'test_hue': float(fr['test_hue']),
            'pred_hues': np.asarray(fr['pred_hues'], dtype=float),
            'mae': float(fr['mae']),
        })
    return folds, float(e['overall_mae'])


def circ_diff(a, b):
    d = (a - b + 180) % 360 - 180
    return d


def draw_color_wheel(ax, *, r_outer=1.0, r_inner=0.65, missing_idx=None,
                     dim_others=False):
    """Draw a 8-segment color wheel; optionally black out one segment."""
    for i, ang in enumerate(HUE_ANGLES):
        a0 = ang - 22.5; a1 = ang + 22.5
        if missing_idx is not None and i == missing_idx:
            w = Wedge((0,0), r_outer, a0, a1, width=r_outer - r_inner,
                      facecolor='#222', edgecolor='white', lw=1.2, zorder=3)
        else:
            fc = HUE_RGB[i]
            alpha = 0.35 if (dim_others and missing_idx is not None) else 1.0
            w = Wedge((0,0), r_outer, a0, a1, width=r_outer - r_inner,
                      facecolor=fc, edgecolor='white', lw=1.0, alpha=alpha, zorder=2)
        ax.add_patch(w)
    ax.set_aspect('equal')
    ax.set_xlim(-1.35, 1.35); ax.set_ylim(-1.35, 1.35)
    ax.axis('off')


def draw_concept_panel(ax):
    """LEFT panel — what is LOCO?"""
    miss = 4  # Cyan
    draw_color_wheel(ax, missing_idx=miss, dim_others=True)
    # "?" in the blacked-out slot
    qx, qy = deg2xy(HUE_ANGLES[miss], 0.83)
    ax.text(qx, qy, '?', color='white', ha='center', va='center',
            fontsize=22, weight='bold', zorder=5)

    # Title block
    ax.text(0, 1.25, 'Leave-one-COLOUR-out (LOCO)',
            ha='center', va='center', fontsize=13, weight='bold')
    ax.text(0, -1.20,
            'Train on 7 hues → predict the missing 8th\n'
            'How close does the model land?',
            ha='center', va='center', fontsize=10)

    # Arrows from a "model" box pointing to where the prediction lands
    # HC prediction lands near true angle
    tx, ty = deg2xy(HUE_ANGLES[miss], 0.0)
    # Two example arrows
    hc_pred_ang = HUE_ANGLES[miss] + 12  # close
    cvd_pred_ang = HUE_ANGLES[miss] + 150  # far
    px_hc, py_hc = deg2xy(hc_pred_ang, 0.55)
    px_cvd, py_cvd = deg2xy(cvd_pred_ang, 0.55)
    # Place the dots
    ax.scatter([px_hc], [py_hc], s=110, c=[[0.12,0.47,0.71]],
               edgecolors='k', linewidths=0.8, zorder=6, label='HC: near truth')
    ax.scatter([px_cvd], [py_cvd], s=110, c=[[0.85,0.30,0.15]],
               edgecolors='k', linewidths=0.8, zorder=6, label='CVD: far')
    # Arc indicating circular MAE
    from matplotlib.patches import Arc
    # arrow from center to truth
    truth_dot = deg2xy(HUE_ANGLES[miss], 0.55)
    ax.scatter([truth_dot[0]],[truth_dot[1]], marker='*', s=160, c='white',
               edgecolors='k', linewidths=0.9, zorder=7)
    ax.legend(loc='lower center', bbox_to_anchor=(0.5, -0.42),
              fontsize=9, frameon=False, ncol=1)


def draw_fan_panel(ax, sub: str, roi: str, label: str):
    folds, overall_mae = load_loco(sub, roi)
    draw_color_wheel(ax, missing_idx=None)
    # For each of 8 held-out colors, draw 6 short arrows from a center dot at the
    # true hue radius toward the predicted angle.
    for fr in folds:
        truth = fr['test_hue']
        # base point: on the wheel at the truth hue, just inside the ring
        bx, by = deg2xy(truth, 0.62)
        # mark truth
        ax.scatter([bx],[by], marker='*', s=70, c='white', edgecolors='k',
                   linewidths=0.6, zorder=8)
        # draw per-run prediction wedges as thin lines from center to predicted angle
        for pred in fr['pred_hues']:
            # predicted point on a slightly inner radius
            px, py = deg2xy(pred, 0.40)
            ax.plot([bx, px], [by, py], '-', color='black', lw=0.4, alpha=0.45,
                    zorder=4)
            ax.scatter([px],[py], s=10, c='black', alpha=0.6, zorder=5)
        # central tendency arrow (circular mean of predictions)
        mean_pred = np.rad2deg(np.arctan2(
            np.sin(np.deg2rad(fr['pred_hues'])).mean(),
            np.cos(np.deg2rad(fr['pred_hues'])).mean())) % 360
        mx, my = deg2xy(mean_pred, 0.40)
        # thicker arrow showing fold-mean
        arrow = FancyArrowPatch((bx,by),(mx,my), arrowstyle='->',
                                mutation_scale=10, color='black', lw=1.0,
                                alpha=0.85, zorder=6)
        ax.add_patch(arrow)

    ax.text(0, 1.25, label, ha='center', va='center', fontsize=12, weight='bold')
    ax.text(0, -1.22, f'overall circular MAE = {overall_mae:.0f}°'
                       f'  (chance = 90°)',
            ha='center', va='center', fontsize=10)


def main():
    fig, axes = plt.subplots(1, 3, figsize=(15, 5.5), constrained_layout=False)
    plt.subplots_adjust(wspace=0.05, top=0.95, bottom=0.07)

    draw_concept_panel(axes[0])
    draw_fan_panel(axes[1], 'sub-06', 'V4',
                   'HC: sub-06, hV4 — tight predictions')
    draw_fan_panel(axes[2], 'sub-09', 'V1',
                   'CVD: sub-09, V1 — predictions scatter')

    fig.suptitle('Figure 1C (v9 draft) — LOCO interpolation: concept + per-run prediction fan',
                 fontsize=12, weight='bold', y=1.01)
    out_png = OUT / 'loco_cartoon_v9_draft.png'
    fig.savefig(out_png, dpi=200, bbox_inches='tight')
    print(f'wrote: {out_png}')


if __name__ == '__main__':
    main()
