"""
Diagnostic: do the 8 SRM-aligned colors actually form a hue circle in 2D?

For each ROI:
  1. Compute HC group mean response (8, k).
  2. PCA → 2D. Plot scatter colored by stimulus hue. Also draw HC individuals.
  3. Quantify "circularity": Procrustes-fit a regular octagon → R^2.
  4. Report variance explained by PC1+PC2 vs higher PCs.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

PROJ = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis')
SRM_DIR = PROJ / 'analysis/phase2_SRM_across_between/results/c010/combined_with_aligned'
OUT = PROJ / 'docs/OHBM_abstract/v9_figures'

ROIS = [('V1','V1'),('V2','V2'),('V3','V3'),('V4','hV4')]
HC = [f'sub-{i:02d}' for i in range(1,8)]
CVD = ['sub-08','sub-09','sub-10']

HUE_RGB = np.array([
    [0.90,0.20,0.20],[0.95,0.55,0.10],[0.95,0.85,0.15],[0.20,0.75,0.25],
    [0.10,0.80,0.85],[0.20,0.40,0.95],[0.55,0.20,0.85],[0.90,0.30,0.75]])
HUE_LABELS = ['c1 R','c2 O','c3 Y','c4 G','c5 C','c6 B','c7 P','c8 M']


def procrustes_to_regular_octagon(pts: np.ndarray) -> tuple[float, np.ndarray]:
    """Best-fit similarity transform of a regular octagon to pts (8,2).
    Returns R^2 (1 - residual SS / total SS) and fitted target."""
    angles = np.deg2rad(np.arange(0, 360, 45))
    target = np.stack([np.cos(angles), np.sin(angles)], axis=1)  # (8,2)
    # Center
    P = pts - pts.mean(0)
    Q = target
    # Optimal rotation + scale (Procrustes)
    M = Q.T @ P
    U, S, Vt = np.linalg.svd(M)
    R = U @ Vt  # rotates P to Q-frame
    s = (S.sum()) / (P*P).sum()
    fitted = s * (P @ R)
    ss_res = ((Q - fitted)**2).sum()
    ss_tot = ((Q - Q.mean(0))**2).sum()
    r2 = 1 - ss_res/ss_tot
    return r2, fitted


def main():
    fig, axes = plt.subplots(2, 4, figsize=(16, 8), constrained_layout=True)

    diag_rows = []
    for col, (key, lbl) in enumerate(ROIS):
        data = np.load(SRM_DIR / f'{key}_procrustes_aligned_amplitudes.npy',
                       allow_pickle=True).item()
        hc_stack = np.stack([data[s] for s in HC], axis=0)  # (7,8,k)
        hc_mean = hc_stack.mean(0)                            # (8,k)

        # PCA on HC mean (across colors)
        centered = hc_mean - hc_mean.mean(0, keepdims=True)
        U, S, Vt = np.linalg.svd(centered, full_matrices=False)
        ve = (S**2)/((S**2).sum())  # var explained per PC
        axes_pca = Vt[:2].T
        proj_mean = centered @ axes_pca  # (8,2)

        r2, fitted_octagon = procrustes_to_regular_octagon(proj_mean)
        diag_rows.append((lbl, ve, r2))

        # Top row: HC mean projection
        ax = axes[0, col]
        # Draw fitted regular octagon (faint reference)
        fitted_centered = fitted_octagon
        ax.plot(*np.vstack([fitted_centered, fitted_centered[:1]]).T,
                ':', color='gray', lw=1, label='regular octagon (Procrustes fit)')
        # Connect HC mean colors c1→c2→...→c8→c1
        ax.plot(*np.vstack([proj_mean, proj_mean[:1]]).T,
                '-', color='#1f77b4', lw=1.5, alpha=0.7, zorder=2)
        for i in range(8):
            ax.scatter(proj_mean[i,0], proj_mean[i,1], s=200, c=[HUE_RGB[i]],
                       edgecolors='k', linewidths=1.0, zorder=5)
            ax.annotate(HUE_LABELS[i], proj_mean[i], fontsize=8,
                        xytext=(5,5), textcoords='offset points')
        ax.set_aspect('equal')
        ax.set_title(f'{lbl} HC mean  |  PC1+PC2 = {(ve[0]+ve[1])*100:.0f}%  |  octagon R²={r2:.2f}',
                     fontsize=10)
        ax.axhline(0, color='lightgray', lw=0.5); ax.axvline(0, color='lightgray', lw=0.5)
        ax.set_xticks([]); ax.set_yticks([])

        # Bottom row: same PCA but show all 10 subjects' projections (color = subject group)
        ax2 = axes[1, col]
        for s in HC:
            p = (data[s] - hc_mean.mean(0)) @ axes_pca
            ax2.plot(*np.vstack([p, p[:1]]).T, '-', color='#1f77b4', lw=0.6, alpha=0.4)
        for s, color_ in zip(CVD, ['#E07B00','#C0223D','#F5C26E']):
            p = (data[s] - hc_mean.mean(0)) @ axes_pca
            ax2.plot(*np.vstack([p, p[:1]]).T, '-', color=color_, lw=1.5, alpha=0.85,
                     label=s)
        # HC mean color dots overlaid
        for i in range(8):
            ax2.scatter(proj_mean[i,0], proj_mean[i,1], s=120, c=[HUE_RGB[i]],
                        edgecolors='k', linewidths=0.6, zorder=10)
        ax2.set_aspect('equal'); ax2.set_xticks([]); ax2.set_yticks([])
        ax2.set_title(f'{lbl} per-subject overlay (sequential polygon)', fontsize=10)
        if col == 3:
            ax2.legend(loc='upper right', fontsize=8)

    fig.suptitle('SRM 2D diagnostic — does HC mean form a hue circle?', fontsize=13, weight='bold')
    out_png = OUT / 'srm_diag_v9.png'
    fig.savefig(out_png, dpi=180, bbox_inches='tight')
    print(f'wrote: {out_png}')

    print('\nDiagnostic summary:')
    print(f'{"ROI":<6}{"PC1%":>8}{"PC2%":>8}{"PC1+2%":>10}{"octagon R²":>14}')
    for lbl, ve, r2 in diag_rows:
        print(f'{lbl:<6}{ve[0]*100:>7.1f}{ve[1]*100:>8.1f}{(ve[0]+ve[1])*100:>9.1f}{r2:>13.3f}')


if __name__ == '__main__':
    main()
