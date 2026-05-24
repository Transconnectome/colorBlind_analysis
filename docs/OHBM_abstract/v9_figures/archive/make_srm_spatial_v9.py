"""
SRM spatial scatter (v9) — show the 8 hues as POINTS in neural space,
per subject. The 'shape' of those 8 points is what SRM disparity measures.

Strategy:
  - Use V1 (where sub-09 has strongest individual SRM signal, z=5.17).
  - PCA fit on HC group-mean (8, k) -> 2D projection axes shared by all.
  - Project every subject's 8 colors through those axes.
  - For each subject: plot 8 colored dots + thin line connecting them in
    canonical hue order (Red->Orange->...->Magenta->Red).
  - Layout: 2x5 grid showing every subject (7 HC + HC mean + 3 CVD = 11; we
    drop one HC to fit a clean 5+5 grid, or use a 3x4 layout).

Honest framing:
  - HC mean shape = the canonical reference (thick).
  - HC individuals = variable but envelope visible.
  - CVD = positions shifted relative to HC mean (this is what z captures).

Plus a summary panel: HC envelope (light) + HC mean (thick blue) + 3 CVD shapes
(colored) overlaid on a single plot.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

PROJ = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis')
SRM_DIR = PROJ/'analysis/phase2_SRM_across_between/results/c010/combined_with_aligned'
OUT = PROJ/'docs/OHBM_abstract/v9_figures'

HUE_RGB = np.array([
    [0.90,0.20,0.20],[0.95,0.55,0.10],[0.95,0.85,0.15],[0.20,0.75,0.25],
    [0.10,0.80,0.85],[0.20,0.40,0.95],[0.55,0.20,0.85],[0.90,0.30,0.75]])
HC = [f'sub-{i:02d}' for i in range(1,8)]
CVD_INFO = [
    ('sub-08','#E07B00','deutan'),
    ('sub-09','#C0223D','protan'),
    ('sub-10','#F5C26E','mild'),
]


def load_roi(roi: str) -> dict:
    return np.load(SRM_DIR/f'{roi}_procrustes_aligned_amplitudes.npy',
                   allow_pickle=True).item()


def fit_hc_pca(data: dict):
    """Return (axes (k,2), center (k,)) from HC group-mean PCA."""
    hc_stack = np.stack([data[s] for s in HC], axis=0)   # (7,8,k)
    hc_mean = hc_stack.mean(axis=0)                       # (8,k)
    center = hc_mean.mean(0)                              # (k,)
    centered = hc_mean - center
    U,S,Vt = np.linalg.svd(centered, full_matrices=False)
    axes = Vt[:2].T                                       # (k,2)
    return axes, center


def project(pat: np.ndarray, axes: np.ndarray, center: np.ndarray) -> np.ndarray:
    return (pat - center) @ axes


def draw_subject_shape(ax, pts2d, *, alpha=1.0, lw=1.0, ec='#444',
                       dot_size=110, show_dots=True, line_color=None,
                       line_alpha=None):
    """Connect 8 points in hue order (closing the loop). Color each dot by hue."""
    if line_color is None: line_color = ec
    if line_alpha is None: line_alpha = alpha * 0.5
    loop = np.vstack([pts2d, pts2d[:1]])
    ax.plot(loop[:,0], loop[:,1], '-', color=line_color, lw=lw, alpha=line_alpha,
            zorder=3)
    if show_dots:
        for i in range(8):
            ax.scatter(pts2d[i,0], pts2d[i,1], s=dot_size, c=[HUE_RGB[i]],
                       edgecolors='black', linewidths=0.6, alpha=alpha, zorder=5)


def make_figure(roi_key='V1', roi_label='V1'):
    data = load_roi(roi_key)
    axes_pca, center = fit_hc_pca(data)
    hc_stack = np.stack([data[s] for s in HC], axis=0)
    hc_mean_pat = hc_stack.mean(0)
    hc_mean_proj = project(hc_mean_pat, axes_pca, center)

    # global axis limits
    all_pts = []
    for s in HC + ['sub-08','sub-09','sub-10']:
        all_pts.append(project(data[s], axes_pca, center))
    all_pts = np.concatenate(all_pts, axis=0)
    pad = 0.20
    xmin, xmax = all_pts[:,0].min()-pad, all_pts[:,0].max()+pad
    ymin, ymax = all_pts[:,1].min()-pad, all_pts[:,1].max()+pad

    # Layout: 3 columns x 2 rows for "per-subject" detail + 1 wide row for summary
    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(3, 5, height_ratios=[1, 1, 1.35],
                          hspace=0.32, wspace=0.18,
                          left=0.04, right=0.98, top=0.92, bottom=0.05)

    def setup(ax, title, *, title_color='black'):
        ax.set_xlim(xmin, xmax); ax.set_ylim(ymin, ymax); ax.set_aspect('equal')
        ax.set_xticks([]); ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_edgecolor('#999'); sp.set_linewidth(0.8)
        ax.axhline(0, color='lightgray', lw=0.4, zorder=1)
        ax.axvline(0, color='lightgray', lw=0.4, zorder=1)
        ax.set_title(title, fontsize=10.5, weight='bold', color=title_color,
                     pad=4)

    # Row 0: HC mean (col 0) + 4 HC individuals (col 1-4)
    ax = fig.add_subplot(gs[0,0])
    setup(ax, 'HC mean (n=7) — reference shape', title_color='#1f77b4')
    draw_subject_shape(ax, hc_mean_proj, lw=2.5, ec='#1f77b4', dot_size=170)

    hc_to_show_top = HC[:4]
    for c, s in enumerate(hc_to_show_top, start=1):
        ax = fig.add_subplot(gs[0,c])
        setup(ax, f'HC {s}')
        proj = project(data[s], axes_pca, center)
        # faint HC mean as guide
        draw_subject_shape(ax, hc_mean_proj, lw=1.0, ec='#1f77b4',
                            dot_size=0, alpha=0.35, show_dots=False,
                            line_color='#1f77b4', line_alpha=0.35)
        draw_subject_shape(ax, proj, lw=1.4, ec='#666')

    # Row 1: remaining 3 HC + 1 spacer (or use 3 HC + 1 placeholder note)
    for c, s in enumerate(HC[4:], start=0):
        ax = fig.add_subplot(gs[1,c])
        setup(ax, f'HC {s}')
        proj = project(data[s], axes_pca, center)
        draw_subject_shape(ax, hc_mean_proj, lw=1.0, ec='#1f77b4',
                            dot_size=0, alpha=0.35, show_dots=False,
                            line_color='#1f77b4', line_alpha=0.35)
        draw_subject_shape(ax, proj, lw=1.4, ec='#666')

    # cols 3,4 in row 1 — first two CVD
    cvd_top = CVD_INFO[:2]
    for c, (sub, col, tt) in enumerate(cvd_top, start=3):
        ax = fig.add_subplot(gs[1,c])
        z_info = {'sub-08':'V1 z=1.40 (V2 z=2.94*)',
                  'sub-09':'V1 z=5.17, p=.003',
                  'sub-10':'V1 z=0.51 (null)'}.get(sub,'')
        setup(ax, f'CVD {sub} ({tt})\n{z_info}', title_color=col)
        proj = project(data[sub], axes_pca, center)
        draw_subject_shape(ax, hc_mean_proj, lw=1.0, ec='#1f77b4',
                            dot_size=0, alpha=0.4, show_dots=False,
                            line_color='#1f77b4', line_alpha=0.4)
        draw_subject_shape(ax, proj, lw=2.0, ec=col)

    # Row 2: summary overlay (wide spanning all 5 cols)
    ax = fig.add_subplot(gs[2,:])
    setup(ax, f'Summary — all subjects overlaid in HC PCA space  '
              f'({roi_label}, 2D projection of {len(data["sub-01"][0])}-dim SRM patterns)')
    ax.set_aspect('equal')
    # HC individuals as faint lines
    for s in HC:
        proj = project(data[s], axes_pca, center)
        loop = np.vstack([proj, proj[:1]])
        ax.plot(loop[:,0], loop[:,1], '-', color='#1f77b4', lw=0.7,
                alpha=0.35, zorder=2)
    # HC mean thick
    loop = np.vstack([hc_mean_proj, hc_mean_proj[:1]])
    ax.plot(loop[:,0], loop[:,1], '-', color='#1f77b4', lw=3.0, alpha=0.95,
            zorder=4, label=f'HC mean (n=7)')
    # HC mean dots colored by hue
    for i in range(8):
        ax.scatter(hc_mean_proj[i,0], hc_mean_proj[i,1], s=150, c=[HUE_RGB[i]],
                    edgecolors='black', linewidths=0.8, zorder=8)
    # CVD lines
    for sub, col, tt in CVD_INFO:
        proj = project(data[sub], axes_pca, center)
        loop = np.vstack([proj, proj[:1]])
        ax.plot(loop[:,0], loop[:,1], '-', color=col, lw=2.0, alpha=0.95,
                 zorder=5, label=f'{sub} ({tt})')
        for i in range(8):
            ax.scatter(proj[i,0], proj[i,1], s=70, c=[HUE_RGB[i]],
                        edgecolors=col, linewidths=1.5, zorder=7)
    ax.legend(loc='upper right', fontsize=10, frameon=True)
    # Place ROI label and PC variance info
    # variance explained for this projection
    hc_stack = np.stack([data[s] for s in HC], axis=0)
    hc_mean_pat = hc_stack.mean(0)
    centered = hc_mean_pat - hc_mean_pat.mean(0)
    _, S, _ = np.linalg.svd(centered, full_matrices=False)
    ve = (S**2)/((S**2).sum())
    ax.text(0.02, 0.97,
            f'PC1+PC2 captures {(ve[0]+ve[1])*100:.0f}% of HC-mean variance',
            transform=ax.transAxes, va='top', ha='left',
            fontsize=9, color='#444', style='italic')

    fig.suptitle(f'Figure 3 (v9 spatial) — Per-subject "shape" of 8 hues in {roi_label} SRM space\n'
                 f'each dot is a hue (colored = stimulus identity), each closed loop = one subject\'s neural geometry',
                 fontsize=12.5, weight='bold', y=0.985)

    out = OUT/f'srm_spatial_v9_draft_{roi_label}.png'
    fig.savefig(out, dpi=180, bbox_inches='tight')
    print('wrote:', out)


if __name__ == '__main__':
    make_figure('V1', 'V1')
    make_figure('V4', 'hV4')
