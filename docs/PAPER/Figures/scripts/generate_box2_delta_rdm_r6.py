#!/usr/bin/env python3
"""
generate_box2_delta_rdm_r6.py

REVISION R6 asset: the DeltaRDM heatmap pair, exported standalone so it can be
dropped into box 2 ("Candidate loss atoms") of the pipeline schematic
(Figure 2, `fig:pipeline`, file stem `fig3_workflow`).

WHY STANDALONE.  `fig3_workflow.png/.tif/.pdf` is NOT programmatically
generated: it is a hand-assembled PowerPoint composite
(`fig3_assets/Presentation1.pptx` -> `Presentation1.pdf` ->
`fig3_workflow_composited.pdf`), into which the pre-rendered box assets
(`box1_forward_wheel`, `box3_landscape_sub08`, `box4_preimage_wheel`) were
placed by hand.  This script therefore produces the same kind of asset as those
files; MANUAL INSERTION into the .pptx is required.

Source panel: old panel A of `fig3_geometry` (generate_fig3.py, recoverable via
`git show 6f66e67^:docs/PAPER/Figures/scripts/generate_fig3.py`).  The matrices,
colormap, symmetric scale rule and hue colour strips are reproduced unchanged.

Data (unchanged, no recomputation)
----------------------------------
    analysis/phase5_filter_optimization/results/_archive/
        old_labels_pre_2026-05-16/phase2_artifacts/diagnostics/srm_precompute/
        delta_rdm_obs_srm_{V1,V2}.npz          keys: sub_08, sub_09, sub_10
This is the same precompute the committed `fig3_geometry.pdf` (2026-05-12) was
built from; it was relocated under `_archive/old_labels_pre_2026-05-16/` after
the figure was made.  Only V1 (protan) and V2 (deutan) are needed.

Differences from the old panel A
--------------------------------
  * per-subject p-values are NOT annotated.  Figure 2's caption states that the
    schematic "reports no new statistics", and R6 moves the disparity test
    statistics into \\cref{tab:disparity_loso}.
  * titles read "Deutan (V2)" / "Protan (V1)" to match box 2's existing
    "Deutan: ... L_RDM(V2)" / "Protan: ... L_RDM(V1)" wording.
  * hue identity is carried by the colour strips only (no text tick labels),
    which would be illegible at the ~36 mm printed width of a pipeline box.
  * shared colorbar is horizontal, under the pair.

Output (docs/PAPER/Figures/fig3_assets/):
    box2_delta_rdm_r6.png  (400 dpi, matching box1/box4)
    box2_delta_rdm_r6.pdf  (vector)
    box2_delta_rdm_r6.svg  (editable, matching box1/box4)
"""

from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.spatial.distance import squareform

# --- Paths -------------------------------------------------------------------
BASE = Path(__file__).resolve().parents[3].parent   # repo root
DELTA_RDM_DIR = (BASE / 'analysis/phase5_filter_optimization/results/'
                        '_archive/old_labels_pre_2026-05-16/phase2_artifacts/'
                        'diagnostics/srm_precompute')
OUT_DIR = BASE / 'docs/PAPER/Figures/fig3_assets'

# --- Constants (verbatim from generate_fig3.py) ------------------------------
COLOR_LAB = [
    [59.90,  62.69,   3.78],   # Red
    [64.20,  49.20,  45.58],   # Orange
    [57.27,  13.06,  41.69],   # Yellow
    [69.08, -55.02,  47.38],   # Green
    [74.61, -41.33,  -4.89],   # Cyan
    [69.14, -11.45, -40.91],   # Blue
    [60.68,  19.18, -54.13],   # Purple
    [60.17,  46.82, -40.31],   # Magenta
]


def _lab2rgb(L, a, b):
    y = (L + 16) / 116
    x = a / 500 + y
    z = y - b / 200
    xyz = np.array([x, y, z])
    xyz = np.where(xyz > 0.206893, xyz ** 3, (xyz - 16 / 116) / 7.787)
    xyz *= [0.95047, 1.0, 1.08883]
    M = np.array([[3.2406, -1.5372, -0.4986],
                  [-0.9689,  1.8758,  0.0415],
                  [0.0557, -0.2040,  1.0570]])
    rgb = M @ xyz
    rgb = np.where(rgb <= 0.0031308, 12.92 * rgb, 1.055 * rgb ** (1 / 2.4) - 0.055)
    return tuple(np.clip(rgb, 0, 1))


HUE_RGB = [_lab2rgb(*lab) for lab in COLOR_LAB]

plt.rcParams.update({
    'font.family': 'Arial',
    'font.size': 9,
    'axes.linewidth': 0.8,
    'pdf.fonttype': 42,
    'svg.fonttype': 'none',
})


def load_delta_rdm_matrix(roi, sub_key):
    """Load DeltaRDM upper-triangle vector and expand to a symmetric 8x8."""
    data = np.load(DELTA_RDM_DIR / f'delta_rdm_obs_srm_{roi}.npz')
    return squareform(data[sub_key])


def make_asset():
    configs = [
        ('sub_08', 'V2', 'Deutan (V2)'),
        ('sub_09', 'V1', 'Protan (V1)'),
    ]
    mats = [load_delta_rdm_matrix(roi, sub) for sub, roi, _ in configs]

    # Symmetric scale -- identical rule to generate_fig3.py (0.80 of the max
    # absolute value across both matrices, rounded to 0.25).
    vmax = np.percentile([np.abs(m).max() for m in mats], 100) * 0.80
    vmax = round(vmax * 4) / 4

    fig_w_in = 84 / 25.4          # 84 mm, matching box1/box4 canvas width
    fig_h_in = 62 / 25.4
    fig = plt.figure(figsize=(fig_w_in, fig_h_in))

    axes = [fig.add_axes([0.075, 0.280, 0.395, 0.545]),
            fig.add_axes([0.545, 0.280, 0.395, 0.545])]
    cax = fig.add_axes([0.30, 0.195, 0.40, 0.045])

    last_im = None
    for ax, (sub_key, roi, title), mat in zip(axes, configs, mats):
        im = ax.imshow(mat, cmap='RdBu_r', vmin=-vmax, vmax=vmax,
                       aspect='equal', interpolation='nearest')
        last_im = im

        ax.set_xticks([])
        ax.set_yticks([])

        # hue colour strips -- TOP and LEFT edges
        for i, rgb in enumerate(HUE_RGB):
            ax.add_patch(plt.Rectangle((i - 0.5, -1.20), 1.0, 0.70,
                                       facecolor=rgb, edgecolor='#333',
                                       linewidth=0.3, clip_on=False))
            ax.add_patch(plt.Rectangle((-1.20, i - 0.5), 0.70, 1.0,
                                       facecolor=rgb, edgecolor='#333',
                                       linewidth=0.3, clip_on=False))

        ax.set_title(title, fontsize=9, fontweight='bold', pad=13)
        for spine in ax.spines.values():
            spine.set_linewidth(0.7)

    cbar = fig.colorbar(last_im, cax=cax, orientation='horizontal')
    cbar.set_ticks([-vmax, 0, vmax])
    cbar.set_ticklabels([f'{-vmax:.1f}', '0', f'+{vmax:.1f}'])
    cbar.ax.tick_params(labelsize=7, length=1.5, pad=1.5)
    cbar.outline.set_linewidth(0.5)
    fig.text(0.50, 0.145, r'$\Delta$RDM  (CVD $-$ HC)', ha='center', va='top',
             fontsize=8)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stem = OUT_DIR / 'box2_delta_rdm_r6'
    save_kw = dict(bbox_inches='tight', pad_inches=0.02, facecolor='white')
    fig.savefig(f'{stem}.png', dpi=400, **save_kw)
    fig.savefig(f'{stem}.pdf', **save_kw)
    fig.savefig(f'{stem}.svg', **save_kw)
    print(f'vmax = {vmax}')
    for ext in ('png', 'pdf', 'svg'):
        print(f'Saved: {stem}.{ext}')
    plt.close(fig)


if __name__ == '__main__':
    make_asset()
