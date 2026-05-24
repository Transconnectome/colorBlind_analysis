"""
LOCO process diagram v9.2 — proper per-step subplots so the visuals scale.

5 horizontally arranged panels (one matplotlib Axes each):
  1. fMRI patterns for 8 hues
  2. Hide one (Cyan) — wheel with slot blacked out
  3. Forward encoder — 6 cosine channels
  4. Predict — held-out pattern → wheel with prediction marker
  5. Compare — wheel with truth + HC/CVD example outcomes

Arrows between panels via figure-level annotations.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import (Wedge, Rectangle, FancyArrowPatch, Arc)

PROJ = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis')
OUT = PROJ/'docs/OHBM_abstract/v9_figures'

HUE_RGB = np.array([
    [0.90,0.20,0.20],[0.95,0.55,0.10],[0.95,0.85,0.15],[0.20,0.75,0.25],
    [0.10,0.80,0.85],[0.20,0.40,0.95],[0.55,0.20,0.85],[0.90,0.30,0.75]])
HUE_LABELS = ['Red','Orange','Yellow','Green','Cyan','Blue','Purple','Magenta']
HUE_ANGLES = np.arange(0, 360, 45)
MISS = 4  # Cyan


def deg2xy(deg, r):
    rad = np.deg2rad(deg); return r*np.cos(rad), r*np.sin(rad)


def style_panel(ax, title):
    for spine in ax.spines.values():
        spine.set_visible(True); spine.set_edgecolor('#888'); spine.set_linewidth(1.0)
    ax.set_facecolor('#faf8f3')
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title(title, fontsize=11.5, weight='bold', loc='left', pad=4)


def draw_color_ring(ax, cx, cy, r_outer, r_inner, missing=None, dim=False):
    for i, ang in enumerate(HUE_ANGLES):
        a0, a1 = ang-22.5, ang+22.5
        if missing is not None and i == missing:
            ax.add_patch(Wedge((cx,cy), r_outer, a0, a1, width=r_outer-r_inner,
                                facecolor='#1a1a1a', edgecolor='white', lw=1.0,
                                zorder=3))
        else:
            a = 0.5 if dim else 1.0
            ax.add_patch(Wedge((cx,cy), r_outer, a0, a1, width=r_outer-r_inner,
                                facecolor=HUE_RGB[i], edgecolor='white', lw=1.0,
                                alpha=a, zorder=2))


def panel1(ax):
    """Step 1: 8 stimuli + fMRI pattern matrix."""
    style_panel(ax, '1. fMRI scan: brain sees 8 hues')
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    # 8 colored stimulus tiles at top
    for i in range(8):
        x = 0.06 + i*0.105
        ax.add_patch(Rectangle((x, 0.78), 0.085, 0.10,
                                facecolor=HUE_RGB[i], edgecolor='white', lw=0.8))
    ax.text(0.5, 0.71, '↓ fMRI', ha='center', va='center', fontsize=10, color='#444')
    # pattern matrix below
    rng = np.random.default_rng(7)
    n_vox = 24
    y_top = 0.62; row_h = 0.06; gap = 0.005
    for i in range(8):
        y = y_top - i*(row_h + gap)
        # left tag = stimulus color
        ax.add_patch(Rectangle((0.04, y), 0.035, row_h,
                                facecolor=HUE_RGB[i], edgecolor='white', lw=0.5,
                                zorder=4))
        # pattern row
        vals = rng.uniform(0.15, 1.0, n_vox)
        for j, v in enumerate(vals):
            rgb = HUE_RGB[i]*v + (1-v)*np.array([0.95,0.95,0.95])
            ax.add_patch(Rectangle((0.085 + j*(0.86/n_vox), y), 0.86/n_vox, row_h,
                                    facecolor=rgb, edgecolor='none'))
    ax.text(0.5, 0.06,
            'rows = colors,  columns = voxels\n→ one neural pattern per hue',
            ha='center', va='center', fontsize=9, color='#444', style='italic')


def panel2(ax):
    """Step 2: hide one hue."""
    style_panel(ax, '2. Hide one hue (e.g. Cyan)')
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.set_aspect('equal')
    draw_color_ring(ax, 0.5, 0.55, r_outer=0.36, r_inner=0.24, missing=MISS)
    # ? in slot
    qx, qy = deg2xy(HUE_ANGLES[MISS], 0.30)
    ax.text(0.5+qx, 0.55+qy, '?', ha='center', va='center',
            color='white', fontsize=28, weight='bold', zorder=10)
    ax.text(0.5, 0.10,
            'train  = patterns for the 7 visible hues\n'
            'test  =  the missing pattern',
            ha='center', va='center', fontsize=9, color='#444', style='italic')


def panel3(ax):
    """Step 3: forward encoder basis."""
    style_panel(ax, '3. Forward encoder (6 cosine channels)')
    ax.set_xlim(0, 360); ax.set_ylim(-0.18, 1.25)
    centers = np.linspace(0, 300, 6)
    xs = np.linspace(0, 360, 400)
    cmap = plt.get_cmap('tab10')
    for i, c in enumerate(centers):
        d = ((xs - c + 180) % 360) - 180
        y = np.clip(np.cos(np.deg2rad(d))**5, 0, None)
        ax.plot(xs, y, '-', color=cmap(i), lw=1.6)
    ax.axhline(0, color='gray', lw=0.6)
    # X-axis hue tick markers (color circles)
    for i, ang in enumerate(HUE_ANGLES):
        ax.scatter(ang, -0.08, s=70, c=[HUE_RGB[i]], edgecolors='k',
                   linewidths=0.5, zorder=5, clip_on=False)
    ax.text(180, -0.16, 'hue (deg)', ha='center', va='top', fontsize=9, color='#444')
    ax.set_xticks([])
    ax.text(180, 1.10,
            'every voxel = weighted sum of 6 smooth channels\n'
            '→ smooth hue tuning assumption',
            ha='center', va='center', fontsize=9, color='#a33', style='italic')


def panel4(ax):
    """Step 4: predict the held-out hue."""
    style_panel(ax, '4. Predict the held-out hue')
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.set_aspect('equal')

    # left: the held-out pattern (single row)
    rng = np.random.default_rng(11)
    n = 24
    yrow = 0.66; rowh = 0.10
    ax.add_patch(Rectangle((0.03, yrow), 0.04, rowh,
                            facecolor=HUE_RGB[MISS], edgecolor='white', lw=0.5,
                            alpha=0.9))
    for j in range(n):
        v = rng.uniform(0.15, 1.0)
        rgb = HUE_RGB[MISS]*v + (1-v)*np.array([0.95,0.95,0.95])
        ax.add_patch(Rectangle((0.08 + j*(0.30/n), yrow), 0.30/n, rowh,
                                facecolor=rgb, edgecolor='none'))
    ax.text(0.23, yrow-0.04, 'held-out pattern\n(Cyan)', ha='center', va='top',
            fontsize=8.5, color='#444')
    # arrow to wheel
    ax.add_patch(FancyArrowPatch((0.42, yrow+rowh/2),(0.55, yrow+rowh/2),
                                  arrowstyle='-|>', mutation_scale=18,
                                  color='#444', lw=1.6))
    ax.text(0.485, yrow+rowh/2+0.05, 'feed into\nmodel', ha='center', va='bottom',
            fontsize=8, color='#555', style='italic')
    # wheel on right
    draw_color_ring(ax, 0.78, 0.60, r_outer=0.18, r_inner=0.12)
    # predicted angle marker — slightly off cyan (e.g., 192°)
    pred = 192
    px, py = deg2xy(pred, 0.22)
    ax.scatter([0.78+px],[0.60+py], marker='v', s=170, c='black',
               edgecolors='white', linewidths=1.0, zorder=10)
    ax.text(0.78+px, 0.60+py+0.07, 'predicted\nangle',
            ha='center', va='bottom', fontsize=8, color='black', weight='bold')
    ax.text(0.5, 0.16,
            'model outputs a continuous angle\n— even for an unseen hue (it interpolates)',
            ha='center', va='center', fontsize=9, color='#444', style='italic')


def panel5(ax):
    """Step 5: compare to truth, preview HC vs CVD."""
    style_panel(ax, '5. Predicted vs true → circular MAE')
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.set_aspect('equal')
    cx, cy = 0.5, 0.58
    draw_color_ring(ax, cx, cy, r_outer=0.30, r_inner=0.20)
    truth = HUE_ANGLES[MISS]
    # truth star outside
    tx, ty = deg2xy(truth, 0.40)
    ax.scatter([cx+tx],[cy+ty], marker='*', s=260, c='white',
               edgecolors='black', linewidths=1.2, zorder=10)
    ax.text(cx+tx+0.03, cy+ty+0.04, 'truth\n(Cyan, 180°)', ha='left', va='center',
            fontsize=8.5, weight='bold')
    # HC outcome — close to truth
    hc = truth + 12
    hx, hy = deg2xy(hc, 0.40)
    ax.scatter([cx+hx],[cy+hy], s=140, c='#1f77b4', edgecolors='k',
               linewidths=0.8, zorder=10)
    ax.text(cx+hx-0.03, cy+hy-0.06, 'HC\n12° gap', ha='right', va='top',
            fontsize=8.5, color='#1f77b4', weight='bold')
    # CVD outcome — far
    cv = truth - 130
    vx, vy = deg2xy(cv, 0.40)
    ax.scatter([cx+vx],[cy+vy], s=140, c='#d62728', edgecolors='k',
               linewidths=0.8, zorder=10)
    ax.text(cx+vx+0.02, cy+vy, 'CVD\n130° gap', ha='left', va='center',
            fontsize=8.5, color='#d62728', weight='bold')
    # arcs showing the gaps
    ax.add_patch(Arc((cx, cy), 0.80, 0.80, angle=0, theta1=truth, theta2=hc,
                      color='#1f77b4', lw=2.4, zorder=9))
    ax.add_patch(Arc((cx, cy), 0.74, 0.74, angle=0, theta1=cv, theta2=truth,
                      color='#d62728', lw=2.4, zorder=9))
    ax.text(0.5, 0.08,
            'gap = LOCO error (0° perfect, 90° = chance)',
            ha='center', va='center', fontsize=9, color='#444', style='italic')


def main():
    fig = plt.figure(figsize=(20, 5.0))
    gs = fig.add_gridspec(1, 5, left=0.02, right=0.985, top=0.86, bottom=0.04,
                          wspace=0.07)
    axs = [fig.add_subplot(gs[0, i]) for i in range(5)]
    panel1(axs[0]); panel2(axs[1]); panel3(axs[2]); panel4(axs[3]); panel5(axs[4])

    # arrows between panels (figure-coordinates)
    for i in range(4):
        # right edge of panel i to left edge of panel i+1 at vertical center
        bb0 = axs[i].get_position(); bb1 = axs[i+1].get_position()
        y = (bb0.y0 + bb0.y1)/2
        fig.add_artist(FancyArrowPatch((bb0.x1, y),(bb1.x0, y),
                                         arrowstyle='-|>', mutation_scale=22,
                                         color='#444', lw=1.8))

    fig.suptitle('Figure 1C (v9 process) — what is LOCO?  '
                 'A step-by-step view of the model\'s task',
                 fontsize=13, weight='bold', y=0.99)

    out = OUT/'loco_process_v9_2_draft.png'
    fig.savefig(out, dpi=200, bbox_inches='tight')
    print('wrote:', out)


if __name__ == '__main__':
    main()
