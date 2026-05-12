"""Side-by-side OLD (Option C buggy) vs NEW (STIM_LAB) for F0 canonical c1-c8.

Just the Tier 1 colors, both renderings shown side by side.
"""
import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

_HERE = Path(__file__).resolve()
_PHASE2 = _HERE.parents[2]
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_PHASE2 / 'scripts'))

from visualize_filter_candidates import (
    angle_to_rgb_vivid, lab_to_rgb_display, cvd_response_lab,
    find_preimage, forward_perceived, L_STAR, CHROMA, SUBJECTS,
)
from stim_lab_render import render_at_hue as render_stim_lab

OUT = _PHASE2 / 'results' / 'visualizations' / 'rendering_options_comparison'

# F0 canonical
SUBJECTS['08']['2comp'] = {'beta_s': 38.0, 'beta_c': -14.0}
PARAMS = SUBJECTS['08']['2comp']
CVD = 'deutan'
DLAM_MACHADO = SUBJECTS['08']['machado']['delta_lambda']

TIER1 = [(0,'c1'),(45,'c2'),(90,'c3'),(135,'c4'),(180,'c5'),(225,'c6'),(270,'c7'),(315,'c8')]


def render_old_col(theta, col_idx):
    """Old rendering — Option C buggy (col 1,3 vivid, col 2,4 ring with Machado)."""
    theta_pre, _ = find_preimage(theta, '2comp', CVD, PARAMS)
    theta_cvd, _ = forward_perceived(theta, '2comp', CVD, PARAMS)
    theta_cvd_pre, _ = forward_perceived(theta_pre, '2comp', CVD, PARAMS)
    if col_idx == 0:
        return angle_to_rgb_vivid(theta)
    elif col_idx == 2:
        return angle_to_rgb_vivid(theta_pre)
    elif col_idx == 1:
        L_cvd = float(cvd_response_lab(theta, CVD, DLAM_MACHADO)[0])
        return lab_to_rgb_display(L_cvd,
                                   CHROMA*np.cos(np.deg2rad(theta_cvd)),
                                   CHROMA*np.sin(np.deg2rad(theta_cvd)))
    elif col_idx == 3:
        L_cvd_pre = float(cvd_response_lab(theta_pre, CVD, DLAM_MACHADO)[0])
        return lab_to_rgb_display(L_cvd_pre,
                                   CHROMA*np.cos(np.deg2rad(theta_cvd_pre)),
                                   CHROMA*np.sin(np.deg2rad(theta_cvd_pre)))


def render_new_col(theta, col_idx):
    """New rendering — STIM_LAB-based (all 4 columns same convention)."""
    theta_pre, _ = find_preimage(theta, '2comp', CVD, PARAMS)
    theta_cvd, _ = forward_perceived(theta, '2comp', CVD, PARAMS)
    theta_cvd_pre, _ = forward_perceived(theta_pre, '2comp', CVD, PARAMS)
    if col_idx == 0:
        return render_stim_lab(theta, dL=0.0)
    elif col_idx == 1:
        return render_stim_lab(theta_cvd, dL=0.0)
    elif col_idx == 2:
        return render_stim_lab(theta_pre, dL=0.0)
    elif col_idx == 3:
        return render_stim_lab(theta_cvd_pre, dL=0.0)


COL_TITLES = ['Original', 'CVD perceives', 'Filtered', 'CVD(Filtered)']

fig, axes = plt.subplots(8, 8, figsize=(12, 9),
                         gridspec_kw={'hspace': 0.10, 'wspace': 0.06})
fig.suptitle('OLD (Option C, current bugs) vs NEW (STIM_LAB) — sub-08 2-comp F0 canonical (38, -14)\n'
             'Left 4 cols: OLD  |  Right 4 cols: NEW',
             fontsize=11, y=0.995)

for j, t in enumerate(COL_TITLES):
    axes[0, j].set_title(f'OLD: {t}', fontsize=8)
    axes[0, j+4].set_title(f'NEW: {t}', fontsize=8)

for i, (theta, label) in enumerate(TIER1):
    for j in range(4):
        rgb_old = render_old_col(theta, j)
        rgb_new = render_new_col(theta, j)
        axes[i, j].add_patch(Rectangle((0,0), 1, 1, color=rgb_old))
        axes[i, j+4].add_patch(Rectangle((0,0), 1, 1, color=rgb_new))
    for j in range(8):
        ax = axes[i, j]
        ax.set_xticks([]); ax.set_yticks([])
        ax.set_xlim(0,1); ax.set_ylim(0,1)
        for sp in ax.spines.values():
            sp.set_edgecolor('black')
    axes[i, 0].text(-0.10, 0.5, f'{label}\nθ={int(theta)}°',
                    ha='right', va='center', fontsize=8,
                    transform=axes[i, 0].transAxes)

# Vertical separator between OLD and NEW
sep_x = 0.5125
fig.add_artist(plt.Line2D([sep_x, sep_x], [0.04, 0.92],
                           color='red', linewidth=1.5, transform=fig.transFigure))

plt.subplots_adjust(left=0.07, right=0.98, top=0.92, bottom=0.04)
out = OUT / 'OLD_vs_NEW_F0_canonical_c1c8.png'
fig.savefig(out, dpi=140, bbox_inches='tight')
plt.close(fig)
print(f'Saved: {out}')
