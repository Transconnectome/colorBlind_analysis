"""
SRM octagon — intuitive visualization of "what SRM disparity measures".

Idea:
  - Project each subject's 8 hue patterns (SRM-aligned, in HC shared space)
    into 2D via PCA fit on HC-mean response.
  - HC subjects' octagons should overlay tightly on the HC reference.
  - CVD subjects' octagons should be visibly warped (compression, rotation).

Output: 1 figure × 4 ROIs (V1, V2, V3, hV4), each panel a 2D scatter+polygon plot.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.collections import LineCollection

PROJ = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis')
SRM_DIR = PROJ / 'analysis/phase2_SRM_across_between/results/c010/combined_with_aligned'
OUT_DIR = PROJ / 'docs/OHBM_abstract/v9_figures'

ROIS = [('V1', 'V1'), ('V2', 'V2'), ('V3', 'V3'), ('V4', 'hV4')]
HC = [f'sub-{i:02d}' for i in range(1, 8)]
CVD = ['sub-08', 'sub-09', 'sub-10']

# Approx sRGB for the 8 stimulus hues (vivid)
HUE_RGB = np.array([
    [0.90, 0.20, 0.20],  # c1 red
    [0.95, 0.55, 0.10],  # c2 orange
    [0.95, 0.85, 0.15],  # c3 yellow
    [0.20, 0.75, 0.25],  # c4 green
    [0.10, 0.80, 0.85],  # c5 cyan
    [0.20, 0.40, 0.95],  # c6 blue
    [0.55, 0.20, 0.85],  # c7 purple
    [0.90, 0.30, 0.75],  # c8 magenta
])

CVD_STYLE = {
    'sub-08': dict(color='#E07B00', label='sub-08 (deutan)',   marker='o'),
    'sub-09': dict(color='#C0223D', label='sub-09 (protan)',   marker='s'),
    'sub-10': dict(color='#F5C26E', label='sub-10 (mild)',     marker='^'),
}


def load_roi(roi_key: str) -> dict:
    fp = SRM_DIR / f'{roi_key}_procrustes_aligned_amplitudes.npy'
    return np.load(fp, allow_pickle=True).item()


def pca_2d_from_hc_mean(data: dict) -> tuple[np.ndarray, np.ndarray]:
    """Fit PCA on HC group-mean (8, k); return (axes (k,2), hc_mean_projected (8,2))."""
    hc_stack = np.stack([data[s] for s in HC], axis=0)   # (7, 8, k)
    hc_mean = hc_stack.mean(axis=0)                       # (8, k)
    # Center across colors before PCA
    centered = hc_mean - hc_mean.mean(axis=0, keepdims=True)
    U, S, Vt = np.linalg.svd(centered, full_matrices=False)
    axes = Vt[:2].T                                        # (k, 2)
    proj = centered @ axes                                 # (8, 2)
    return axes, proj, hc_mean.mean(axis=0)               # also return center for projection of others


def project(subject_pat: np.ndarray, axes: np.ndarray, center: np.ndarray) -> np.ndarray:
    """(8,k) -> (8,2) using HC PCA axes."""
    return (subject_pat - center[None, :]) @ axes


def draw_octagon(ax, pts: np.ndarray, *, edgecolor='gray', lw=1.0, alpha=0.6,
                 fill=False, fc=None, zorder=2):
    poly = Polygon(pts, closed=True, fill=fill, edgecolor=edgecolor,
                   linewidth=lw, alpha=alpha, facecolor=fc or 'none',
                   zorder=zorder)
    ax.add_patch(poly)


def main():
    fig, axes_grid = plt.subplots(1, 4, figsize=(16, 4.3), constrained_layout=True)

    for ax, (roi_key, roi_lbl) in zip(axes_grid, ROIS):
        data = load_roi(roi_key)
        axes_pca, hc_mean_proj, color_center = pca_2d_from_hc_mean(data)

        # HC reference octagon (mean)
        draw_octagon(ax, hc_mean_proj, edgecolor='#1f77b4', lw=2.5,
                     alpha=0.95, zorder=5)
        # HC individuals (thin lines)
        for s in HC:
            proj = project(data[s], axes_pca, color_center)
            draw_octagon(ax, proj, edgecolor='#1f77b4', lw=0.7,
                         alpha=0.35, zorder=3)
        # CVD individuals (colored, thicker)
        for s in CVD:
            sty = CVD_STYLE[s]
            proj = project(data[s], axes_pca, color_center)
            draw_octagon(ax, proj, edgecolor=sty['color'], lw=1.8,
                         alpha=0.95, zorder=6)
            # color-coded vertices for the HC reference (only once at the end)
        # Color-coded vertices for HC reference
        for i, (xy, rgb) in enumerate(zip(hc_mean_proj, HUE_RGB)):
            ax.scatter([xy[0]], [xy[1]], s=85, c=[rgb], edgecolors='k',
                       linewidths=0.6, zorder=10)

        ax.set_title(roi_lbl, fontsize=13, weight='bold')
        ax.set_aspect('equal', adjustable='datalim')
        ax.axhline(0, color='lightgray', lw=0.5, zorder=1)
        ax.axvline(0, color='lightgray', lw=0.5, zorder=1)
        ax.set_xticks([]); ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_edgecolor('lightgray')

    # Single legend at right
    from matplotlib.lines import Line2D
    handles = [
        Line2D([0],[0], color='#1f77b4', lw=2.5, label='HC mean (reference)'),
        Line2D([0],[0], color='#1f77b4', lw=0.8, alpha=0.5, label='HC individuals (n=7)'),
    ] + [Line2D([0],[0], color=CVD_STYLE[s]['color'], lw=1.8, label=CVD_STYLE[s]['label'])
         for s in CVD]
    fig.legend(handles=handles, loc='lower center', ncol=5, frameon=False,
               fontsize=10, bbox_to_anchor=(0.5, -0.05))

    fig.suptitle('SRM-aligned hue geometry — 2D PCA projection of 8 colors per subject',
                 fontsize=12, weight='bold')

    out_png = OUT_DIR / 'srm_octagon_v9_draft.png'
    out_pdf = OUT_DIR / 'srm_octagon_v9_draft.pdf'
    fig.savefig(out_png, dpi=200, bbox_inches='tight')
    fig.savefig(out_pdf, bbox_inches='tight')
    print(f'wrote: {out_png}')
    print(f'wrote: {out_pdf}')


if __name__ == '__main__':
    main()
