#!/usr/bin/env python3
"""
sub09_mwjaccard_viz.py — Sub-09 2-component filter at mw_jaccard_loss best
parameters (β_s=44, β_c=+54).

Per loss inventory 2026-05-03: mw_jaccard_loss is the only loss variant where
both CVD subjects pass HC sanity check (emp_p=0.17 each, 1/6 HC above).
Sub-09 (44, +54) is structurally different from existing candidates:
  - Phase A LOCO best: (6, -22)
  - Cycle 12 cross-ROI: (30, +26)
  - Cycle 14 cross-ROI RDM: (32, +22)
  - mw_jaccard_loss V4: (44, +54)  ← THIS

Generate viz file for behavioral session 4-way comparison.

Output: results/visualizations/filter_visualization/filter_viz_sub-09_mwjaccard.png
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle

_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR))

from visualize_filter_candidates import (
    OUTDIR, SUBJECTS,
    angle_to_rgb_vivid, cvd_response_lab, lab_to_rgb_display,
    forward_perceived, find_preimage,
    L_STAR, CHROMA,
)

SUBJ = '09'
PARAMS = {'beta_s': 44.0, 'beta_c': 54.0}
LABEL = 'mw_jaccard_loss V4'

cvd = SUBJECTS[SUBJ]['cvd']
dlam_cvd = float(SUBJECTS[SUBJ]['machado']['delta_lambda'])

# Color tiers (mirror visualize_filter_candidates)
TIER1 = [(0, 'c1 (red)'), (45, 'c2 (orange)'), (90, 'c3 (yellow)'),
         (135, 'c4 (yel-grn)'), (180, 'c5 (cyan)'), (225, 'c6 (blu-cy)'),
         (270, 'c7 (blue)'), (315, 'c8 (magenta)')]
TIER2 = [(16, 'protan+'), (196, 'protan-'), (150, 'deutan+'),
         (330, 'deutan-'), (60, 'Ishihara orange'), (240, 'cobalt')]
TIER3 = [(40, 'sRGB R'), (90, 'sRGB Y'), (140, 'sRGB G'),
         (200, 'sRGB C'), (270, 'sRGB B'), (330, 'sRGB M')]

PALETTE = [('Tier 1: 8-stim', TIER1),
           ('Tier 2: confusion anchors', TIER2),
           ('Tier 3: sRGB primaries', TIER3)]

rows = [(tier, theta, label) for tier, colors in PALETTE
        for theta, label in colors]
n_rows = len(rows)

fig_height = 0.55 * n_rows + 1.8
fig, axes = plt.subplots(n_rows, 4, figsize=(9.0, fig_height),
                         gridspec_kw={'hspace': 0.08, 'wspace': 0.08})

fig.suptitle(
    f'2-Component {LABEL}  -  sub-{SUBJ} ({cvd})\n'
    f'beta_s = {PARAMS["beta_s"]} deg, beta_c = {PARAMS["beta_c"]} deg  '
    f'(mw_jaccard_loss winner @ V4 per loss inventory)',
    fontsize=10, y=0.995)

col_titles = ['Original', 'CVD perceives', 'Filtered (pre-image)',
              'CVD(Filtered)']
for ax, title in zip(axes[0], col_titles):
    ax.set_title(title, fontsize=9)

last_tier = None
for i, (tier, theta, label) in enumerate(rows):
    ax_row = axes[i]

    rgb_orig = angle_to_rgb_vivid(theta)
    theta_pre, resid = find_preimage(theta, '2comp', cvd, PARAMS)
    rgb_pre = angle_to_rgb_vivid(theta_pre)

    theta_cvd, dt = forward_perceived(theta, '2comp', cvd, PARAMS)
    lab_cvd_anchor = cvd_response_lab(theta, cvd, dlam_cvd)
    L_cvd = float(lab_cvd_anchor[0])
    rgb_cvd = lab_to_rgb_display(
        L_cvd,
        CHROMA * np.cos(np.deg2rad(theta_cvd)),
        CHROMA * np.sin(np.deg2rad(theta_cvd)))

    theta_cvd_of_pre, _ = forward_perceived(theta_pre, '2comp', cvd, PARAMS)
    lab_cvd_of_pre = cvd_response_lab(theta_pre, cvd, dlam_cvd)
    L_cvd_of_pre = float(lab_cvd_of_pre[0])
    rgb_cvd_of_pre = lab_to_rgb_display(
        L_cvd_of_pre,
        CHROMA * np.cos(np.deg2rad(theta_cvd_of_pre)),
        CHROMA * np.sin(np.deg2rad(theta_cvd_of_pre)))

    ax_row[0].add_patch(Rectangle((0, 0), 1, 1, color=rgb_orig))
    ax_row[1].add_patch(Rectangle((0, 0), 1, 1, color=rgb_cvd))
    ax_row[2].add_patch(Rectangle((0, 0), 1, 1, color=rgb_pre))
    ax_row[3].add_patch(Rectangle((0, 0), 1, 1, color=rgb_cvd_of_pre))

    ax_row[0].text(-0.05, 0.5, f'{label}\ntheta={int(theta)}',
                   ha='right', va='center', fontsize=7,
                   transform=ax_row[0].transAxes)
    ax_row[1].text(0.5, -0.02, f'dtheta={dt:+.1f}',
                   ha='center', va='top', fontsize=7,
                   transform=ax_row[1].transAxes)
    ax_row[2].text(0.5, -0.02,
                   f'theta_pre={int(theta_pre)}  |r|={abs(resid):.2f}',
                   ha='center', va='top', fontsize=7,
                   transform=ax_row[2].transAxes)

    if tier != last_tier:
        ax_row[0].text(-0.45, 1.05, tier,
                       ha='left', va='bottom', fontsize=8,
                       fontweight='bold', color='dimgray',
                       transform=ax_row[0].transAxes)
        last_tier = tier

    for a in ax_row:
        a.set_xticks([])
        a.set_yticks([])
        a.set_xlim(0, 1)
        a.set_ylim(0, 1)
        for sp in a.spines.values():
            sp.set_edgecolor('black')
            sp.set_linewidth(0.5)

outpath = OUTDIR / f'filter_viz_sub-{SUBJ}_mwjaccard.png'
plt.savefig(outpath, dpi=150, bbox_inches='tight')
plt.close(fig)
print(f'Saved: {outpath}')
print(f'\nThis is sub-09 4th candidate filter (alongside Phase A LOCO 6/-22, '
      f'Cycle 12 30/+26, Cycle 14 32/+22).')
print(f'mw_jaccard_loss is the only loss with ✓✓ both CVD distinct from HC '
      f'in inventory.')
