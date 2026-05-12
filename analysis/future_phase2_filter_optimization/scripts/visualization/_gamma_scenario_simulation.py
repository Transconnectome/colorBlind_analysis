"""Simulate what c1-c8 look like under different display gamma assumptions.

Uses lab2rgb_psychopy from colorBlind_test.py + complement,
then applies different physical display gamma to model the projector behavior.
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

from visualize_filter_candidates import angle_to_rgb_vivid, L_STAR, CHROMA

OUT = _PHASE2 / 'results' / 'visualizations' / 'rendering_options_comparison'

TIER1 = [(0,'c1 (Red)'),(45,'c2 (Orange)'),(90,'c3 (Yellow)'),
         (135,'c4 (Green)'),(180,'c5 (Cyan)'),(225,'c6 (Blue)'),
         (270,'c7 (Violet)'),(315,'c8 (Magenta)')]


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


def render_at_gamma(theta, gamma):
    """PsychoPy lab2rgb + complement, then apply display gamma."""
    rad = np.deg2rad(theta)
    a = CHROMA * np.cos(rad)  # post-complement
    b = CHROMA * np.sin(rad)
    rgb_srgb = lab2rgb_psychopy(L_STAR, a, b)  # what PsychoPy sends to monitor
    # Display gamma: light = pixel ^ gamma
    # For gamma=2.4 with sRGB decoding, equivalent to "intended" sRGB display
    # For gamma=1.0, displays sRGB-encoded as-is (washed out / lighter)
    # For gamma>2.4, mid-tones darken → more saturated/vivid
    light = rgb_srgb ** gamma
    return np.clip(light, 0, 1)


SCENARIOS = [
    ('PsychoPy intended\n(γ_display=2.4 sRGB)', 2.4),
    ('Linear monitor\n(γ_display=1.0)', 1.0),
    ('Boosted γ_display=3.0\n(typical projector)', 3.0),
    ('Extreme γ_display=4.0\n(high-contrast projector)', 4.0),
    ('Option A vivid\n(angle_to_rgb_vivid; reference)', None),
]

n_rows = len(TIER1)
n_cols = len(SCENARIOS)
fig, axes = plt.subplots(n_rows, n_cols, figsize=(2.0*n_cols, 0.55*n_rows + 1.6),
                         gridspec_kw={'hspace': 0.08, 'wspace': 0.05})
fig.suptitle('Display gamma sensitivity — c1-c8\n'
             'Same PsychoPy lab2rgb output + different physical monitor γ',
             fontsize=10, y=0.995)

for j, (sname, g) in enumerate(SCENARIOS):
    axes[0, j].set_title(sname, fontsize=8)

for i, (theta, label) in enumerate(TIER1):
    for j, (sname, g) in enumerate(SCENARIOS):
        if g is None:
            rgb = angle_to_rgb_vivid(theta)
        else:
            rgb = render_at_gamma(theta, g)
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
out = OUT / 'gamma_scenarios_c1c8.png'
fig.savefig(out, dpi=140, bbox_inches='tight')
plt.close(fig)
print(f'Saved: {out}')
