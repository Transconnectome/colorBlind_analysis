"""
SRM single-case illustration — what "geometric distortion" looks like in one subject.

Shows the strongest individual case from the abstract: sub-09 (protan) V1, z=5.17, p=.003.

3 panels (horizontal):
  (A) HC mean RDM at V1 — the canonical hue dissimilarity structure
  (B) sub-09 V1 RDM — the protan subject's pattern (visibly warped)
  (C) sub-09 V1 minus HC mean V1 — difference, L-M cells boxed (red/orange vs green/cyan)

Plus a small inline statistic: SRM disparity z = 5.17, Crawford & Howell p = .003.

Honest scope: this is ONE subject at ONE ROI. Group-level SRM evidence stays as
the bar plot in Fig 2D.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial.distance import pdist, squareform

PROJ = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis')
SRM_DIR = PROJ/'analysis/phase2_SRM_across_between/results/c010/combined_with_aligned'
OUT = PROJ/'docs/OHBM_abstract/v9_figures'

HUE_LABELS = ['Red','Orange','Yellow','Green','Cyan','Blue','Purple','Magenta']

# L-M pairs (red/orange vs green/cyan); both halves of the matrix
LM_PAIRS = [(0,3),(0,4),(1,3),(1,4)]


def rdm_corr(X: np.ndarray) -> np.ndarray:
    return squareform(pdist(X, metric='correlation'))


def box_lm(ax, pairs, color='cyan', lw=1.6):
    for (i,j) in pairs:
        ax.add_patch(plt.Rectangle((j-0.5, i-0.5), 1, 1, fill=False,
                                   edgecolor=color, lw=lw, zorder=10))
        ax.add_patch(plt.Rectangle((i-0.5, j-0.5), 1, 1, fill=False,
                                   edgecolor=color, lw=lw, zorder=10))


def label_axes(ax):
    ax.set_xticks(range(8)); ax.set_yticks(range(8))
    ax.set_xticklabels(HUE_LABELS, rotation=45, ha='right', fontsize=8)
    ax.set_yticklabels(HUE_LABELS, fontsize=8)


def main():
    roi = 'V1'
    data = np.load(SRM_DIR/f'{roi}_procrustes_aligned_amplitudes.npy',
                   allow_pickle=True).item()
    HC = [f'sub-{i:02d}' for i in range(1,8)]
    hc_rdms = np.stack([rdm_corr(data[s]) for s in HC], axis=0)
    hc_mean = hc_rdms.mean(0)
    sub09 = rdm_corr(data['sub-09'])
    diff = sub09 - hc_mean

    fig, axes = plt.subplots(1, 3, figsize=(14.5, 4.6))
    plt.subplots_adjust(wspace=0.45, top=0.85, bottom=0.20, left=0.06, right=0.97)

    vmax = max(hc_mean.max(), sub09.max())
    # (A)
    ax = axes[0]
    im = ax.imshow(hc_mean, cmap='magma', vmin=0, vmax=vmax)
    label_axes(ax); box_lm(ax, LM_PAIRS)
    ax.set_title('A.  HC mean V1 RDM\n(canonical hue structure)',
                 fontsize=11, weight='bold')
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label='correlation distance')

    # (B)
    ax = axes[1]
    im = ax.imshow(sub09, cmap='magma', vmin=0, vmax=vmax)
    label_axes(ax); box_lm(ax, LM_PAIRS)
    ax.set_title('B.  sub-09 (protan) V1 RDM\nwarped along L–M axis',
                 fontsize=11, weight='bold')
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label='correlation distance')

    # (C) difference
    ax = axes[2]
    dmax = np.max(np.abs(diff))
    im = ax.imshow(diff, cmap='RdBu_r', vmin=-dmax, vmax=dmax)
    label_axes(ax); box_lm(ax, LM_PAIRS, color='black', lw=1.8)
    ax.set_title('C.  sub-09 minus HC mean\nL–M cells reduced (cyan boxes)',
                 fontsize=11, weight='bold')
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label='Δ dissimilarity')

    # Mean Δ in L-M cells
    mean_dlm = np.mean([diff[i,j] for (i,j) in LM_PAIRS])

    fig.suptitle('Figure 3 (v9 draft) — What "SRM disparity" measures: '
                 'sub-09 (protan) V1 example  '
                 '(SRM z=5.17, Crawford & Howell p=.003)',
                 fontsize=12, weight='bold', y=0.99)
    fig.text(0.5, 0.04,
             f'Boxed cells = red/orange × green/cyan pairs (L–M cone-opponent axis).  '
             f'Mean Δ at L–M cells = {mean_dlm:+.2f}.  '
             'Convergent geometry evidence: see Fig 2D for group SRM disparities across all subjects.',
             ha='center', fontsize=9, style='italic')

    out_png = OUT/'srm_single_case_v9_draft.png'
    fig.savefig(out_png, dpi=200, bbox_inches='tight')
    print('wrote:', out_png)
    print(f'L-M mean Δ (sub-09 V1 minus HC mean) = {mean_dlm:+.3f}')


if __name__ == '__main__':
    main()
