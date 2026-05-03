#!/usr/bin/env python3
"""
sub08_c8_variants_viz.py — Sub-08 c8-only variant visualization.

Per behav_validation §3-4 / B2 plan: render c8 filter at three pre-image
angles (290°, 300°, 310°) plus the canonical filter pre-image, so sub-08
can identify which variant reads as magenta/purple (vs current "dark sky").

Output:
  results/figures/filter_visualization/filter_viz_sub-08_c8variants.png
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from visualize_filter_candidates import (
    OUTDIR, SUBJECTS,
    angle_to_rgb_vivid, cvd_response_lab, lab_to_rgb_display,
    forward_perceived, find_preimage,
    L_STAR, CHROMA,
)

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--subject', default='08', choices=['08', '09'])
args = parser.parse_args()

SUBJ = args.subject
C8_TARGET = 315.0
VARIANT_THETA_PRE = [290.0, 300.0, 310.0]

meta = SUBJECTS[SUBJ]
cvd = meta['cvd']
params_2comp = meta['2comp']
dlam_cvd = float(meta['machado']['delta_lambda'])

theta_pre_canon, resid_canon = find_preimage(
    C8_TARGET, '2comp', cvd, params_2comp)
print(f'Canonical c8 pre-image: theta_pre={theta_pre_canon:.2f}deg, '
      f'residual={resid_canon:+.2f}deg')

rows = [
    ('canonical', float(theta_pre_canon), resid_canon),
    ('variant 290deg', 290.0, None),
    ('variant 300deg', 300.0, None),
    ('variant 310deg', 310.0, None),
]
n_rows = len(rows)


def render_swatch_with_lum(theta_render):
    """Render swatch at the given hue with CVD-derived luminance applied."""
    rgb_vivid = angle_to_rgb_vivid(theta_render)
    return rgb_vivid


fig_height = 0.75 * n_rows + 1.6
fig, axes = plt.subplots(
    n_rows, 4,
    figsize=(9.0, fig_height),
    gridspec_kw={'hspace': 0.10, 'wspace': 0.08})

fig.suptitle(
    f'sub-{SUBJ} ({cvd}) — 2-Component c8 variants\n'
    f'beta_s = {params_2comp["beta_s"]}deg, '
    f'beta_c = {params_2comp["beta_c"]}deg  '
    f'(c8 target = {int(C8_TARGET)}deg)',
    fontsize=11, y=0.995)

col_titles = ['Original (c8)', 'CVD perceives c8',
              'Filter swatch (theta_pre)', 'CVD(Filter swatch)']
for ax, title in zip(axes[0], col_titles):
    ax.set_title(title, fontsize=9)

for i, (label, theta_pre, resid) in enumerate(rows):
    ax_row = axes[i]

    rgb_orig = angle_to_rgb_vivid(C8_TARGET)

    theta_cvd_orig, dt_orig = forward_perceived(
        C8_TARGET, '2comp', cvd, params_2comp)
    lab_cvd_anchor_orig = cvd_response_lab(C8_TARGET, cvd, dlam_cvd)
    L_cvd_orig = float(lab_cvd_anchor_orig[0])
    rgb_cvd_orig = lab_to_rgb_display(
        L_cvd_orig,
        CHROMA * np.cos(np.deg2rad(theta_cvd_orig)),
        CHROMA * np.sin(np.deg2rad(theta_cvd_orig)))

    rgb_pre = angle_to_rgb_vivid(theta_pre)

    theta_cvd_of_pre, _ = forward_perceived(
        theta_pre, '2comp', cvd, params_2comp)
    lab_cvd_of_pre = cvd_response_lab(theta_pre, cvd, dlam_cvd)
    L_cvd_of_pre = float(lab_cvd_of_pre[0])
    rgb_cvd_of_pre = lab_to_rgb_display(
        L_cvd_of_pre,
        CHROMA * np.cos(np.deg2rad(theta_cvd_of_pre)),
        CHROMA * np.sin(np.deg2rad(theta_cvd_of_pre)))

    ax_row[0].add_patch(Rectangle((0, 0), 1, 1, color=rgb_orig))
    ax_row[1].add_patch(Rectangle((0, 0), 1, 1, color=rgb_cvd_orig))
    ax_row[2].add_patch(Rectangle((0, 0), 1, 1, color=rgb_pre))
    ax_row[3].add_patch(Rectangle((0, 0), 1, 1, color=rgb_cvd_of_pre))

    ax_row[0].text(
        -0.05, 0.5, f'{label}',
        ha='right', va='center', fontsize=9, fontweight='bold',
        transform=ax_row[0].transAxes)
    ax_row[1].text(
        0.5, -0.04, f'theta_perceived = {theta_cvd_orig:.0f}deg',
        ha='center', va='top', fontsize=7,
        transform=ax_row[1].transAxes)
    ax_row[2].text(
        0.5, -0.04,
        f'theta_pre = {theta_pre:.1f}deg' +
        (f'  |r| = {abs(resid):.2f}deg' if resid is not None else ''),
        ha='center', va='top', fontsize=7,
        transform=ax_row[2].transAxes)
    ax_row[3].text(
        0.5, -0.04,
        f'theta_perceived = {theta_cvd_of_pre:.0f}deg',
        ha='center', va='top', fontsize=7,
        transform=ax_row[3].transAxes)

    for a in ax_row:
        a.set_xticks([])
        a.set_yticks([])
        a.set_xlim(0, 1)
        a.set_ylim(0, 1)
        for sp in a.spines.values():
            sp.set_edgecolor('black')
            sp.set_linewidth(0.5)

outpath = OUTDIR / f'filter_viz_sub-{SUBJ}_c8variants.png'
plt.savefig(outpath, dpi=150, bbox_inches='tight')
plt.close(fig)
print(f'Saved: {outpath}')

print('\nBehavioral instruction for sub-08:')
print('  For each row (canonical / 290deg / 300deg / 310deg), report')
print('  the color name of column 3 (Filter swatch).')
print('  Question: "Which row reads most clearly as MAGENTA / PURPLE?"')
