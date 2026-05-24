"""
SRM spatial v9.2 — DISPLACEMENT VECTOR visualization.

The 'geometric distortion' is shown literally as 8 arrows per subject:
  arrow start = HC mean position of that hue (in HC-PCA 2D)
  arrow end   = CVD subject's position of that hue
  arrow color = the hue (so the reader sees which colors move where)
  arrow length = magnitude of displacement

HC subjects also shown (small arrows from HC mean -> individual HC) for the
'normal envelope' so CVD arrows can be compared.

Per ROI, 4 panels:
  (HC envelope) | sub-08 deutan | sub-09 protan | sub-10 mild

The hue dots at HC mean positions serve as anchors so the colors are visible.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch

PROJ = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis')
SRM_DIR = PROJ/'analysis/phase2_SRM_across_between/results/c010/combined_with_aligned'
OUT = PROJ/'docs/OHBM_abstract/v9_figures'

HUE_RGB = np.array([
    [0.90,0.20,0.20],[0.95,0.55,0.10],[0.95,0.85,0.15],[0.20,0.75,0.25],
    [0.10,0.80,0.85],[0.20,0.40,0.95],[0.55,0.20,0.85],[0.90,0.30,0.75]])
HUE_LABELS = ['Red','Orange','Yellow','Green','Cyan','Blue','Purple','Magenta']
HC = [f'sub-{i:02d}' for i in range(1,8)]
CVD_INFO = [
    ('sub-08','#E07B00','deutan','V1 z=1.40, V2 z=2.94*'),
    ('sub-09','#C0223D','protan','V1 z=5.17, p=.003'),
    ('sub-10','#F5C26E','mild',  'all ROIs null'),
]


def load_roi(roi):
    return np.load(SRM_DIR/f'{roi}_procrustes_aligned_amplitudes.npy',
                   allow_pickle=True).item()


def fit_hc_pca(data):
    hc_stack = np.stack([data[s] for s in HC], axis=0)
    hc_mean = hc_stack.mean(0)
    center = hc_mean.mean(0)
    centered = hc_mean - center
    U,S,Vt = np.linalg.svd(centered, full_matrices=False)
    axes = Vt[:2].T
    ve = (S**2)/((S**2).sum())
    return axes, center, ve, hc_mean


def project(pat, axes, center):
    return (pat - center) @ axes


def draw_panel(ax, hc_mean_proj, target_proj, *, arrow_color, label, target_lw=2.4,
                arrow_alpha=0.9, show_label=True):
    """Draw HC mean dots + arrows from HC mean -> target for each hue."""
    # Anchor dots: HC mean positions, colored by hue
    for i in range(8):
        ax.scatter(hc_mean_proj[i,0], hc_mean_proj[i,1],
                    s=300, c=[HUE_RGB[i]], edgecolors='black', linewidths=1.0,
                    zorder=4, alpha=0.55)
    # Displacement arrows
    for i in range(8):
        sx, sy = hc_mean_proj[i]
        ex, ey = target_proj[i]
        if np.hypot(ex-sx, ey-sy) < 1e-6:
            continue
        ax.add_patch(FancyArrowPatch((sx, sy),(ex, ey),
                                       arrowstyle='-|>', mutation_scale=18,
                                       color=arrow_color, lw=target_lw,
                                       alpha=arrow_alpha, zorder=6))
        # Endpoint with hue color (so each color's "new" position is visible too)
        ax.scatter(ex, ey, s=120, c=[HUE_RGB[i]], edgecolors=arrow_color,
                    linewidths=1.4, zorder=8)
    if show_label:
        ax.text(0.02, 0.98, label, transform=ax.transAxes, va='top',
                fontsize=11, weight='bold', color=arrow_color)


def setup_ax(ax, xlim, ylim, title=None, title_color='black'):
    ax.set_xlim(xlim); ax.set_ylim(ylim); ax.set_aspect('equal')
    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_edgecolor('#999'); sp.set_linewidth(0.8)
    ax.axhline(0, color='lightgray', lw=0.4, zorder=1)
    ax.axvline(0, color='lightgray', lw=0.4, zorder=1)
    if title:
        ax.set_title(title, fontsize=11, weight='bold', color=title_color, pad=4)


def make_one(roi_key, roi_label):
    data = load_roi(roi_key)
    axes_pca, center, ve, hc_mean_pat = fit_hc_pca(data)
    hc_mean_proj = project(hc_mean_pat, axes_pca, center)

    # global axis limits
    all_pts = [hc_mean_proj]
    for s in HC + ['sub-08','sub-09','sub-10']:
        all_pts.append(project(data[s], axes_pca, center))
    all_pts = np.concatenate(all_pts, axis=0)
    pad = 0.30
    xlim = (all_pts[:,0].min()-pad, all_pts[:,0].max()+pad)
    ylim = (all_pts[:,1].min()-pad, all_pts[:,1].max()+pad)

    fig, axes = plt.subplots(1, 4, figsize=(18, 5.0),
                              gridspec_kw=dict(wspace=0.10, left=0.02,
                                              right=0.98, top=0.85,
                                              bottom=0.08))

    # Panel 1: HC envelope — all HC arrows shown faintly
    ax = axes[0]
    setup_ax(ax, xlim, ylim,
              title=f'HC envelope (n=7) — typical individual scatter',
              title_color='#1f77b4')
    # anchors
    for i in range(8):
        ax.scatter(hc_mean_proj[i,0], hc_mean_proj[i,1], s=300, c=[HUE_RGB[i]],
                    edgecolors='black', linewidths=1.0, zorder=4, alpha=0.7)
    # HC arrows (faint)
    for s in HC:
        proj = project(data[s], axes_pca, center)
        for i in range(8):
            sx, sy = hc_mean_proj[i]; ex, ey = proj[i]
            if np.hypot(ex-sx, ey-sy) < 1e-6: continue
            ax.add_patch(FancyArrowPatch((sx,sy),(ex,ey),
                                          arrowstyle='-|>', mutation_scale=8,
                                          color='#1f77b4', lw=0.8, alpha=0.35,
                                          zorder=5))

    # Panels 2-4: each CVD subject
    for c, (sub, col, tt, zinfo) in enumerate(CVD_INFO, start=1):
        ax = axes[c]
        setup_ax(ax, xlim, ylim,
                  title=f'{sub} ({tt})  —  {zinfo}',
                  title_color=col)
        proj_cvd = project(data[sub], axes_pca, center)
        draw_panel(ax, hc_mean_proj, proj_cvd, arrow_color=col,
                   label=f'displacement', target_lw=2.5, arrow_alpha=0.92,
                   show_label=False)

    # Header
    fig.suptitle(
        f'Figure 3 (v9 displacement) — Per-color geometric distortion in {roi_label}\n'
        f'anchor dots = HC mean position of each hue (PCA on HC-mean, '
        f'PC1+PC2 = {(ve[0]+ve[1])*100:.0f}% var) · arrows = where each hue '
        f'moves to in CVD',
        fontsize=12.5, weight='bold', y=0.98)

    # Bottom hue legend strip
    fig.text(0.5, 0.02,
             '   '.join([f'■ {lbl}' for lbl in HUE_LABELS]),
             ha='center', fontsize=8, color='#444')

    out = OUT/f'srm_spatial_displacement_v9_{roi_label}.png'
    fig.savefig(out, dpi=180, bbox_inches='tight')
    print('wrote:', out)


if __name__ == '__main__':
    make_one('V1', 'V1')
    make_one('V4', 'hV4')
