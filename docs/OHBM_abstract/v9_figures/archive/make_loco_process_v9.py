"""
LOCO process diagram (v9) — how does the model "predict" a color the brain
never saw during training?

5 horizontal steps:
  1.  Train scan: brain views 8 hues, fMRI records 8 voxel patterns.
  2.  Hide one hue (here Cyan). Train set = 7 colors. Test = held-out Cyan.
  3.  Forward encoder: voxel pattern = weighted sum of 6 cosine basis curves
      across the hue circle. Smooth tuning assumption.
  4.  Predict: feed held-out (Cyan) pattern through the model -> get continuous
      angle, regardless of whether Cyan was in training.
  5.  Compare predicted vs true on the hue circle -> circular MAE.

Step 5 also previews the dissociation: HC lands near truth, CVD scatters.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import (FancyArrowPatch, FancyBboxPatch, Wedge,
                                Rectangle, Circle, Polygon)

PROJ = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis')
OUT = PROJ/'docs/OHBM_abstract/v9_figures'

HUE_RGB = np.array([
    [0.90,0.20,0.20],[0.95,0.55,0.10],[0.95,0.85,0.15],[0.20,0.75,0.25],
    [0.10,0.80,0.85],[0.20,0.40,0.95],[0.55,0.20,0.85],[0.90,0.30,0.75]])
HUE_LABELS = ['Red','Orange','Yellow','Green','Cyan','Blue','Purple','Magenta']
HUE_ANGLES = np.arange(0, 360, 45)
MISS = 4  # hide Cyan as the running example


def deg2xy(deg, r):
    rad = np.deg2rad(deg); return r*np.cos(rad), r*np.sin(rad)


def draw_color_ring(ax, cx, cy, r_outer=0.40, r_inner=0.30, missing=None,
                    dim_others=False):
    for i, ang in enumerate(HUE_ANGLES):
        a0, a1 = ang-22.5, ang+22.5
        if missing is not None and i == missing:
            ax.add_patch(Wedge((cx,cy), r_outer, a0, a1, width=r_outer-r_inner,
                                facecolor='#1a1a1a', edgecolor='white', lw=0.8,
                                zorder=3))
        else:
            a = 0.45 if dim_others else 1.0
            ax.add_patch(Wedge((cx,cy), r_outer, a0, a1, width=r_outer-r_inner,
                                facecolor=HUE_RGB[i], edgecolor='white', lw=0.8,
                                alpha=a, zorder=2))


def draw_pattern_strip(ax, x0, y0, w=0.45, h_per=0.018, n_vox=20,
                       seed_base=0, missing=None, dim_others=False):
    """A 'voxel pattern' stack: 8 rows (one per color), n_vox columns of
    colored cells, with the row color tinted by hue. Just decorative — meant
    to convey 'one voxel pattern per color'."""
    rng = np.random.default_rng(123 + seed_base)
    for i in range(8):
        # baseline gray pattern
        y = y0 - i * h_per * 1.1
        if missing is not None and i == missing:
            # black bar with strikethrough
            ax.add_patch(Rectangle((x0, y), w, h_per, facecolor='#2a2a2a',
                                    edgecolor='white', lw=0.5, zorder=2))
            ax.plot([x0, x0+w], [y+h_per/2, y+h_per/2], '-',
                    color='red', lw=1.0, zorder=3)
        else:
            a = 0.30 if dim_others else 1.0
            vals = rng.uniform(0.3, 1.0, n_vox)
            for j, v in enumerate(vals):
                cx = x0 + (j/n_vox)*w
                rgb = HUE_RGB[i] * v + (1-v) * np.array([0.95,0.95,0.95])
                ax.add_patch(Rectangle((cx, y), w/n_vox, h_per,
                                        facecolor=rgb, edgecolor='none',
                                        alpha=a, zorder=2))
        # color tag on the left
        ax.add_patch(Rectangle((x0-0.012, y), 0.012, h_per,
                                facecolor=HUE_RGB[i], edgecolor='none',
                                alpha=0.3 if (dim_others and (missing is None or i!=missing)) else 1.0,
                                zorder=2))


def draw_basis_curves(ax, x0, y0, w=0.30, h=0.10):
    """6 cosine basis curves over hue 0..360, half-wave rectified squared."""
    xs = np.linspace(0, 360, 200)
    centers = np.linspace(0, 300, 6)  # 6 evenly spaced channels
    for i, c in enumerate(centers):
        d = ((xs - c + 180) % 360) - 180
        y = np.cos(np.deg2rad(d))**5
        y = np.clip(y, 0, None)
        cx_arr = x0 + (xs/360.0)*w
        cy_arr = y0 + y * h
        ax.plot(cx_arr, cy_arr, '-', color=plt.cm.tab10(i % 10), lw=1.1,
                zorder=4)
    # baseline
    ax.plot([x0, x0+w],[y0, y0],'-', color='gray', lw=0.5, zorder=3)
    ax.text(x0+w/2, y0-0.018, '0°    90°    180°    270°    360°',
            ha='center', va='top', fontsize=6, color='gray')


def draw_step_box(ax, x, y, w, h, title, *, color='#f7f4ed'):
    bb = FancyBboxPatch((x,y), w, h,
                         boxstyle='round,pad=0.012,rounding_size=0.012',
                         facecolor=color, edgecolor='#888888', lw=1.0,
                         zorder=1)
    ax.add_patch(bb)
    ax.text(x + w/2, y + h - 0.025, title, ha='center', va='top',
            fontsize=11, weight='bold', zorder=10)


def draw_arrow(ax, x0, y0, x1, y1):
    ax.add_patch(FancyArrowPatch((x0,y0),(x1,y1), arrowstyle='-|>',
                                  mutation_scale=22, color='#444',
                                  lw=1.6, zorder=8))


def step1_train_scan(ax, x, y, w, h):
    draw_step_box(ax, x, y, w, h, '1. Brain views 8 hues (train scan)')
    # 8 colored squares as the stimuli
    for i in range(8):
        cx = x + 0.025 + i * (w-0.05)/8
        cy = y + h - 0.10
        ax.add_patch(Rectangle((cx, cy), (w-0.05)/8 * 0.85, 0.045,
                                facecolor=HUE_RGB[i], edgecolor='white', lw=0.5,
                                zorder=5))
    ax.text(x + w/2, y + h - 0.13, '↓ fMRI', ha='center', va='top',
            fontsize=9, color='#444')
    # pattern stack
    draw_pattern_strip(ax, x+0.04, y+h-0.165, w=w-0.08, h_per=0.015)
    # row labels
    ax.text(x + w/2, y + 0.018,
            'one voxel-pattern per color\n(rows = colors, cols = voxels)',
            ha='center', va='bottom', fontsize=8, color='#555', style='italic')


def step2_hide(ax, x, y, w, h):
    draw_step_box(ax, x, y, w, h, '2. Hide one hue (e.g. Cyan)')
    # ring with cyan blacked out
    draw_color_ring(ax, x+w/2, y+h-0.16, r_outer=0.12, r_inner=0.085,
                    missing=MISS, dim_others=False)
    # ? in slot
    qx, qy = deg2xy(HUE_ANGLES[MISS], 0.10)
    ax.text(x+w/2+qx, y+h-0.16+qy, '?', ha='center', va='center',
            color='white', fontsize=15, weight='bold', zorder=8)
    ax.text(x + w/2, y + 0.022,
            'train set = 7 patterns\ntest = the missing pattern',
            ha='center', va='bottom', fontsize=8, color='#555', style='italic')


def step3_basis(ax, x, y, w, h):
    draw_step_box(ax, x, y, w, h, '3. Forward encoder (6 channels)')
    draw_basis_curves(ax, x+0.025, y+h-0.10, w=w-0.05, h=0.075)
    ax.text(x + w/2, y + 0.038,
            'each pattern = weighted sum\nof 6 smooth cosine channels',
            ha='center', va='bottom', fontsize=8, color='#555', style='italic')
    ax.text(x + w/2, y + 0.014,
            '↑ smooth hue tuning assumption',
            ha='center', va='bottom', fontsize=7.5, color='#a33', weight='bold')


def step4_predict(ax, x, y, w, h):
    draw_step_box(ax, x, y, w, h, '4. Predict held-out hue')
    # show: held-out pattern -> arrow -> wheel with predicted angle
    # left: a single black row (the held-out pattern, anonymized)
    px = x + 0.020; py = y + h - 0.075
    rng = np.random.default_rng(7)
    n = 22
    for j in range(n):
        v = rng.uniform(0.2, 1.0)
        rgb = HUE_RGB[MISS] * v + (1-v) * np.array([0.95,0.95,0.95])
        ax.add_patch(Rectangle((px + j/n*0.12, py), 0.12/n, 0.022,
                                facecolor=rgb, edgecolor='none', zorder=4))
    ax.text(px + 0.06, py - 0.012, "held-out pattern", ha='center', va='top',
            fontsize=7, color='#555')
    # arrow
    ax.add_patch(FancyArrowPatch((px+0.135, py+0.011),(x+w/2-0.04, py+0.011),
                                  arrowstyle='-|>', mutation_scale=14,
                                  color='#444', lw=1.4, zorder=8))
    # wheel with predicted angle
    cx_w = x + w - 0.10; cy_w = y + h - 0.13
    draw_color_ring(ax, cx_w, cy_w, r_outer=0.11, r_inner=0.080,
                    missing=None)
    # predicted angle marker
    pred_ang = HUE_ANGLES[MISS] + 6   # near cyan ~6°
    mx, my = deg2xy(pred_ang, 0.13)
    ax.scatter([cx_w+mx],[cy_w+my], marker='v', s=120, c='black',
               edgecolors='white', linewidths=1.0, zorder=10)
    ax.text(cx_w+mx, cy_w+my+0.04, 'predicted', ha='center',
            fontsize=7, color='black', weight='bold')
    ax.text(x + w/2, y + 0.018,
            'model outputs a continuous angle\n(even for unseen hues)',
            ha='center', va='bottom', fontsize=8, color='#555', style='italic')


def step5_compare(ax, x, y, w, h):
    draw_step_box(ax, x, y, w, h, '5. Predicted vs true → circular MAE')
    cx_w = x + w/2; cy_w = y + h - 0.13
    draw_color_ring(ax, cx_w, cy_w, r_outer=0.13, r_inner=0.094, missing=None)
    truth = HUE_ANGLES[MISS]
    # truth star outside
    tx, ty = deg2xy(truth, 0.165)
    ax.scatter([cx_w+tx],[cy_w+ty], marker='*', s=200, c='white',
               edgecolors='black', linewidths=1.0, zorder=10)
    ax.text(cx_w+tx+0.012, cy_w+ty, 'truth', ha='left', va='center',
            fontsize=8, weight='bold')
    # HC pred near
    hc = truth + 12
    hx, hy = deg2xy(hc, 0.165)
    ax.scatter([cx_w+hx],[cy_w+hy], s=85, c='#1f77b4', edgecolors='k',
               linewidths=0.6, zorder=10)
    # CVD pred far
    cv = truth + 130
    vx, vy = deg2xy(cv, 0.165)
    ax.scatter([cx_w+vx],[cy_w+vy], s=85, c='#d62728', edgecolors='k',
               linewidths=0.6, zorder=10)
    # arc segments showing the gaps
    from matplotlib.patches import Arc
    ax.add_patch(Arc((cx_w, cy_w), 0.34, 0.34, angle=0,
                      theta1=truth, theta2=hc, color='#1f77b4',
                      lw=2.2, zorder=9))
    ax.add_patch(Arc((cx_w, cy_w), 0.30, 0.30, angle=0,
                      theta1=truth, theta2=cv, color='#d62728',
                      lw=2.2, zorder=9))
    # labels
    ax.text(cx_w - 0.18, cy_w + 0.05, 'HC ~12°',
            fontsize=9, color='#1f77b4', weight='bold')
    ax.text(cx_w - 0.18, cy_w - 0.02, 'CVD ~130°',
            fontsize=9, color='#d62728', weight='bold')
    ax.text(x + w/2, y + 0.018,
            'angular gap = LOCO error\n(0° perfect, 90° = chance)',
            ha='center', va='bottom', fontsize=8, color='#555', style='italic')


def main():
    fig = plt.figure(figsize=(17, 4.8))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0,1); ax.set_ylim(0,1)
    ax.axis('off')

    # 5 step boxes evenly spaced
    n = 5
    gap = 0.012
    box_w = (1 - (n+1)*gap) / n   # ≈ 0.188
    box_h = 0.82
    box_y = 0.07

    step_xs = [gap + i*(box_w + gap) for i in range(n)]

    step1_train_scan(ax, step_xs[0], box_y, box_w, box_h)
    step2_hide(      ax, step_xs[1], box_y, box_w, box_h)
    step3_basis(     ax, step_xs[2], box_y, box_w, box_h)
    step4_predict(   ax, step_xs[3], box_y, box_w, box_h)
    step5_compare(   ax, step_xs[4], box_y, box_w, box_h)

    # arrows between boxes
    arrow_y = box_y + box_h/2
    for i in range(n-1):
        x0 = step_xs[i] + box_w
        x1 = step_xs[i+1]
        ax.add_patch(FancyArrowPatch((x0 + 0.001, arrow_y),
                                       (x1 - 0.001, arrow_y),
                                       arrowstyle='-|>',
                                       mutation_scale=18, color='#444',
                                       lw=1.4, zorder=9))

    ax.text(0.5, 0.97,
            'Figure 1C (v9 process) — Leave-one-COLOUR-out (LOCO): '
            'a step-by-step view of what the model is being asked to do',
            ha='center', va='top', fontsize=12.5, weight='bold')

    out = OUT/'loco_process_v9_draft.png'
    fig.savefig(out, dpi=200, bbox_inches='tight')
    print('wrote:', out)


if __name__ == '__main__':
    main()
