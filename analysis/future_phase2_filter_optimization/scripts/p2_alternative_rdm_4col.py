"""Pipeline 2 ALTERNATIVE (SRM-RDM) — 4-col STIM_LAB filter rendering.

Parallel to p2_primary_4col.py, but renders the filters obtained when the RDM
atom is swapped to the SRM family (closure Appendix A.2, 300-resample median):

  candidate      PCA (primary)   SRM-cos        SRM-dis (canonical)
  S08-βs-dom     (38, -10)       (22, -36)      (24, -20)
  S08-βc-dom     ( 6, -42)       ( 8, -42)      ( 2, -24)
  S09-βc-rot     ( 2, +24)       (32,  0)       (32,  0)

The point: for sub-09 the PCA filter (cortical-rotation primary, β_c=+24) and the
canonical SRM-disparity filter (S-cone-shift primary, β_s=32, β_c=0) are DIFFERENT
correction filters from the SAME data (closure L9: metric-level non-identifiable).
This script makes that difference perceptually concrete.

Reuses forward / pre-image / STIM_LAB render from p2_primary_4col.

Output: results/visualizations/pipeline2_alternative_rdm/
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

_THIS = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS))

from stim_lab_render import render_at_hue
from two_comp import forward_2comp as _two_comp_forward_8
from p2_primary_4col import (
    forward_closure, pre_image_closure, render_one,
    HUE_8, COLOR_LABELS,
)

OUT = _THIS.parent / 'results' / 'visualizations' / 'pipeline2_alternative_rdm'
OUT.mkdir(parents=True, exist_ok=True)

matplotlib.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Helvetica', 'Arial', 'DejaVu Sans'],
    'font.size': 8, 'axes.titlesize': 9, 'axes.labelsize': 8,
    'xtick.labelsize': 7, 'ytick.labelsize': 7,
})

# Per candidate: the three RDM-metric variants (closure A.2 medians).
CANDIDATES = [
    {
        'label': 'S08-βs-dom',
        'subject': 'sub-08', 'family': 'deutan',
        'combo': 'γ_all + RDM_V1',
        'variants': [
            ('PCA',     38.0, -10.0),
            ('SRM-cos', 22.0, -36.0),
            ('SRM-dis', 24.0, -20.0),
        ],
    },
    {
        'label': 'S08-βc-dom',
        'subject': 'sub-08', 'family': 'deutan',
        'combo': 'γ_OY + RDM_V2',
        'variants': [
            ('PCA',      6.0, -42.0),
            ('SRM-cos',  8.0, -42.0),
            ('SRM-dis',  2.0, -24.0),
        ],
    },
    {
        'label': 'S09-βc-rot',
        'subject': 'sub-09', 'family': 'protan',
        'combo': 'γ_all + RDM_V1',
        'variants': [
            ('PCA',      2.0, 24.0),   # cortical-rotation primary
            ('SRM-cos', 32.0,  0.0),   # S-cone-shift primary
            ('SRM-dis', 32.0,  0.0),   # canonical; same as SRM-cos
        ],
    },
]


def render_metric_compare(cand, outpath):
    """One candidate, 3 metric variants side-by-side, each as a 4-col block."""
    variants = cand['variants']
    fam = cand['family']
    n_v = len(variants)
    ncol = 4 * n_v

    fig, axes = plt.subplots(8, ncol, figsize=(2.0 * ncol, 13),
                             gridspec_kw={'wspace': 0.05, 'hspace': 0.22})

    for v, (mname, bs, bc) in enumerate(variants):
        c0 = v * 4
        dt8 = _two_comp_forward_8(bs, bc, fam)
        for i, theta in enumerate(HUE_8):
            theta = float(theta)
            dt = float(dt8[i])
            theta_cvd = (theta + dt) % 360.0
            theta_pre, resid = pre_image_closure(theta, fam, bs, bc)
            theta_cvd_of_pre, _ = forward_closure(theta_pre, fam, bs, bc)

            rgbs = [render_at_hue(theta), render_at_hue(theta_cvd),
                    render_at_hue(theta_pre), render_at_hue(theta_cvd_of_pre)]
            for j, rgb in enumerate(rgbs):
                ax = axes[i, c0 + j]
                ax.add_patch(Rectangle((0, 0), 1, 1, color=rgb))
                ax.set_xlim(0, 1); ax.set_ylim(0, 1)
                ax.set_xticks([]); ax.set_yticks([])
                for sp in ax.spines.values():
                    sp.set_edgecolor('black'); sp.set_linewidth(0.4)

            if v == 0:
                axes[i, 0].text(-0.10, 0.5, COLOR_LABELS[i],
                                ha='right', va='center', fontsize=7,
                                transform=axes[i, 0].transAxes)
            axes[i, c0 + 1].text(0.5, -0.06, f'δθ={dt:+.1f}°',
                                 ha='center', va='top', fontsize=6.6,
                                 transform=axes[i, c0 + 1].transAxes)

        # column-group headers
        head = f"{mname}\nβ_s={bs:.0f}, β_c={bc:.0f}"
        axes[0, c0].set_title(f"Orig\n{head}", fontsize=7.5)
        axes[0, c0 + 1].set_title('CVD\nperceives', fontsize=7.5)
        axes[0, c0 + 2].set_title('Filter\n(pre-image)', fontsize=7.5)
        axes[0, c0 + 3].set_title('CVD\n(Filter)', fontsize=7.5)

        # divider line between metric blocks
        if v > 0:
            xpos = c0 / ncol
            fig.add_artist(plt.Line2D([xpos, xpos], [0.02, 0.94],
                                       color='0.5', lw=1.0,
                                       transform=fig.transFigure))

    fig.suptitle(
        f"{cand['label']}  —  {cand['subject']} ({fam})  ·  RDM-metric filter comparison\n"
        f"fit loss: {cand['combo']}  ·  parameters = closure A.2 (300-resample median)\n"
        f"PCA (closure primary) vs SRM-cos vs SRM-dis (canonical) — "
        f"see L9: sub-09 mechanism is metric-level non-identifiable",
        fontsize=10, y=1.005,
    )
    plt.tight_layout()
    plt.savefig(outpath, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'  saved: {outpath.name}')


if __name__ == '__main__':
    print(f'Output → {OUT}')
    # Per-candidate metric-comparison 4col blocks
    for cand in CANDIDATES:
        fname = OUT / (f"p2_alt_4col_compare_"
                       f"{cand['label'].replace('β', 'b').replace('-', '_')}.png")
        render_metric_compare(cand, fname)

    # Also emit standalone single-metric 4col for the canonical SRM-dis filters
    # (parallel to primary's per-candidate files), reusing primary render_one.
    for cand in CANDIDATES:
        _, bs, bc = cand['variants'][2]  # SRM-dis
        spec = {
            'label': cand['label'] + ' (SRM-dis)',
            'subject': cand['subject'], 'family': cand['family'],
            'beta_s': bs, 'beta_c': bc,
            'combo': cand['combo'] + '  ·  SRM-disparity (canonical)',
            'note': 'closure A.2 SRM-disparity median  ·  alternative to PCA primary',
        }
        fname = OUT / (f"p2_alt_4col_srmdis_"
                       f"{cand['label'].replace('β', 'b').replace('-', '_')}.png")
        render_one(spec, fname)
    print('\ndone.')
