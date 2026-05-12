"""Side-by-side: col 1 (Original) c1-c8 across 4 rendering options.

Purpose: let user visually pick which option best matches actual MRI display.
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

from visualize_filter_candidates import angle_to_rgb_vivid, lab_to_rgb_display, L_STAR, CHROMA

OUT = _PHASE2 / 'results' / 'visualizations' / 'rendering_options_comparison'

TIER1 = [(0,'c1'),(45,'c2'),(90,'c3'),(135,'c4'),
         (180,'c5'),(225,'c6'),(270,'c7'),(315,'c8')]


def lab2rgb_psychopy(L, a, b, clip=True):
    L, a, b = float(L), float(a), float(b)
    y = (L + 16) / 116; x = a / 500 + y; z = y - b / 200
    xyz = np.array([x, y, z])
    xyz = np.where(xyz > 0.206893, xyz**3, (xyz - 16/116) / 7.787)
    xyz *= [0.95047, 1.0, 1.08883]
    rgb = np.dot([[3.2406, -1.5372, -0.4986],
                  [-0.9689, 1.8758, 0.0415],
                  [0.0557, -0.2040, 1.0570]], xyz)
    rgb = np.where(rgb <= 0.0031308, 12.92 * rgb, 1.055 * rgb**(1/2.4) - 0.055)
    if clip: rgb = np.clip(rgb, 0, 1)
    return rgb


def opt_A(theta):
    return angle_to_rgb_vivid(theta)

def opt_B(theta):
    rad = np.deg2rad(theta)
    return lab2rgb_psychopy(L_STAR, CHROMA*np.cos(rad), CHROMA*np.sin(rad))

def opt_C(theta):
    """Same as B (current col 2,4 = ring at L=75, C=40, no Machado here for fairness)."""
    rad = np.deg2rad(theta)
    return lab_to_rgb_display(L_STAR, CHROMA*np.cos(rad), CHROMA*np.sin(rad))

def opt_D(theta):
    rad = np.deg2rad(theta)
    return lab2rgb_psychopy(L_STAR, -CHROMA*np.cos(rad), -CHROMA*np.sin(rad))


OPTIONS = [
    ('A: vivid (max-saturation sweep)', opt_A),
    ('B: PsychoPy + complement\n(L=75, C=40, std hue)', opt_B),
    ('C: lab_to_rgb_display\n(L=75, C=40, std hue) — = current col 2,4 path', opt_C),
    ('D: PsychoPy no complement\n(dict values directly)', opt_D),
]

n_rows = len(TIER1)
n_cols = len(OPTIONS)
fig, axes = plt.subplots(n_rows, n_cols, figsize=(2.0*n_cols, 0.55*n_rows + 1.4),
                         gridspec_kw={'hspace': 0.08, 'wspace': 0.05})
fig.suptitle('Col 1 (Original) — c1-c8 across 4 rendering options\n'
             'Compare to your memory of the actual MRI screen',
             fontsize=10, y=0.995)

for j, (oname, ofunc) in enumerate(OPTIONS):
    axes[0, j].set_title(oname, fontsize=8)

for i, (theta, label) in enumerate(TIER1):
    for j, (oname, ofunc) in enumerate(OPTIONS):
        rgb = ofunc(theta)
        Y = 0.2126*rgb[0] + 0.7152*rgb[1] + 0.0722*rgb[2]
        ax = axes[i, j]
        ax.add_patch(Rectangle((0,0), 1, 1, color=rgb))
        ax.text(0.5, -0.05, f'Y={Y:.2f}',
                ha='center', va='top', fontsize=6,
                transform=ax.transAxes)
        ax.set_xticks([]); ax.set_yticks([])
        ax.set_xlim(0,1); ax.set_ylim(0,1)
        for sp in ax.spines.values():
            sp.set_edgecolor('black')
    axes[i, 0].text(-0.08, 0.5, f'{label}\nθ={int(theta)}°',
                    ha='right', va='center', fontsize=8,
                    transform=axes[i, 0].transAxes)

plt.subplots_adjust(left=0.10, right=0.98, top=0.90, bottom=0.04)
out = OUT / 'sidebyside_col1_4options.png'
fig.savefig(out, dpi=140, bbox_inches='tight')
plt.close(fig)
print(f'Saved: {out}')
