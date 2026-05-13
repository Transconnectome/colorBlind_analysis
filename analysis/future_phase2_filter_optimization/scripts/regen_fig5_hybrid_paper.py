"""regen_fig5_hybrid_paper.py — paper Fig 5 under the HYBRID loss.

Two 4-column color-rendering panels, sub-08 (top) and sub-09 (bottom).
No text inside the figure — caption is self-contained.

Layout: 16 rows × 4 cols (8 hues × 2 subjects × 4 columns).
Columns: Original, CVD perceives, Filtered (pre-image), CVD(Filtered).

Output: docs/PAPER/Figures/fig5_preimage.{pdf,png}
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR))
sys.path.insert(0, str(_THIS_DIR / 'visualization'))

from stim_lab_render import render_at_hue as _render_stim_lab

_PHASE2 = _THIS_DIR.parent
_REPO = _PHASE2.parent.parent
_PAPER_FIG = _REPO / 'docs' / 'PAPER' / 'Figures'

HUE_ANGLES = [0, 45, 90, 135, 180, 225, 270, 315]

HYBRID = [
    {'sid': '08', 'family': 'deutan', 'color': '#E07B2C',
     'axis': 150.0, 'bs': 16.0, 'bc': 40.0},
    {'sid': '09', 'family': 'protan', 'color': '#2D8E8B',
     'axis': 16.0, 'bs': 12.0, 'bc': -30.0},
]

matplotlib.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Helvetica', 'Arial', 'DejaVu Sans'],
    'pdf.fonttype': 42, 'ps.fonttype': 42,
})


def dt_2comp(theta_deg, bs, bc, theta_conf):
    th = np.deg2rad(theta_deg)
    return bs * np.cos(th - np.pi / 2) + bc * np.cos(th - np.deg2rad(theta_conf))


def forward_2comp(theta, bs, bc, theta_conf):
    dt = dt_2comp(theta, bs, bc, theta_conf)
    return (theta + dt) % 360.0


def pre_image_2comp(target_deg, bs, bc, theta_conf, n_grid=3600):
    grid = np.linspace(0, 360, n_grid, endpoint=False)
    fwd = (grid + dt_2comp(grid, bs, bc, theta_conf)) % 360.0
    diff = (fwd - target_deg + 180) % 360 - 180
    return grid[int(np.argmin(np.abs(diff)))]


COL_LABELS = ['Original', 'CVD perceives', 'Filtered', 'CVD(Filtered)']


def render_one(info, tag):
    """Render an 8-row × 4-col grid for a single subject with column
    headers only (no other text)."""
    n_h = len(HUE_ANGLES)
    fig, axes = plt.subplots(n_h, 4,
                             figsize=(3.6, 0.40 * n_h + 0.25),
                             gridspec_kw={'hspace': 0.07, 'wspace': 0.05,
                                          'left': 0.005, 'right': 0.995,
                                          'top': 0.955, 'bottom': 0.003})

    for k, label in enumerate(COL_LABELS):
        axes[0, k].set_title(label, fontsize=9, pad=4)

    bs, bc, axis = info['bs'], info['bc'], info['axis']
    for i, theta in enumerate(HUE_ANGLES):
        theta_cvd = forward_2comp(float(theta), bs, bc, axis)
        theta_pre = pre_image_2comp(float(theta), bs, bc, axis)
        theta_cvd_pre = forward_2comp(theta_pre, bs, bc, axis)
        rgbs = [
            _render_stim_lab(float(theta), dL=0.0),
            _render_stim_lab(theta_cvd, dL=0.0),
            _render_stim_lab(theta_pre, dL=0.0),
            _render_stim_lab(theta_cvd_pre, dL=0.0),
        ]
        for k, rgb in enumerate(rgbs):
            ax = axes[i, k]
            ax.add_patch(Rectangle((0, 0), 1, 1, color=rgb))
            ax.set_xticks([]); ax.set_yticks([])
            ax.set_xlim(0, 1); ax.set_ylim(0, 1)
            for sp in ax.spines.values():
                sp.set_edgecolor('black')
                sp.set_linewidth(0.4)

    _PAPER_FIG.mkdir(parents=True, exist_ok=True)
    out_pdf = _PAPER_FIG / f'fig5{tag}_preimage.pdf'
    out_png = _PAPER_FIG / f'fig5{tag}_preimage.png'
    plt.savefig(out_pdf, bbox_inches='tight')
    plt.savefig(out_png, dpi=200, bbox_inches='tight')
    plt.close(fig)
    print(f'wrote {out_pdf}')
    print(f'wrote {out_png}')


def render():
    render_one(HYBRID[0], 'a')  # sub-08
    render_one(HYBRID[1], 'b')  # sub-09


if __name__ == '__main__':
    render()
