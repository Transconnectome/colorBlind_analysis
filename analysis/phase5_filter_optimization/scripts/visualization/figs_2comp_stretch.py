#!/usr/bin/env python3
"""
figs_2comp_stretch.py — 2-Component model: sign-dependent compression/expansion.

The δθ = β·cos(θ−θ_axis) term is a TANGENTIAL displacement field, not an axis
dilation. The geometrically correct quantity is the local stretch factor
1 + d(δθ)/dθ = 1 − β·sin(θ−θ_axis), which is asymmetric across the perpendicular.

This figure shows for each parameter (β_s, β_c) and each sign (±):
  (A) δθ(θ) sinusoid with the named axis marked
  (B) Local stretch factor on a hue ring — color-coded:
        red = expansion  (stretch > 1)
        blue = compression (stretch < 1)

Saved to: presentation/figures/data/two_comp_stretch_anatomy.png
"""

from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge

ROOT = Path(__file__).resolve().parents[2]
OUT_PATH = ROOT / 'presentation' / 'figures' / 'data' / 'two_comp_stretch_anatomy.png'
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

THETA_S = 90.0
PROTAN_CONF = 16.0
DEUTAN_CONF = 150.0

# Demo amplitude: small enough to keep stretch positive but visible
BETA = 30.0  # degrees

fig, axes = plt.subplots(2, 4, figsize=(16, 8))

cases = [
    ('β_s = +30°', THETA_S, +BETA, 'S-axis (90°)'),
    ('β_s = −30°', THETA_S, -BETA, 'S-axis (90°)'),
    ('β_c = +30° (deutan)', DEUTAN_CONF, +BETA, 'deutan conf (150°)'),
    ('β_c = −30° (deutan)', DEUTAN_CONF, -BETA, 'deutan conf (150°)'),
]

theta_grid = np.linspace(0, 360, 721)

for col, (title, axis_deg, beta, axis_label) in enumerate(cases):
    # Compute δθ and local stretch
    delta = beta * np.cos(np.radians(theta_grid - axis_deg))
    stretch = 1 - (beta * np.pi/180) * np.sin(np.radians(theta_grid - axis_deg))
    # Note: derivative of β·cos(θ−φ) wrt θ (in radians) is −β·sin(θ−φ).
    # If β is in degrees, δθ is in degrees. To get dimensionless stretch, β must be
    # in radians for the derivative. Above we convert β to radians for the deriv.

    # --- Top row: δθ(θ) ---
    ax = axes[0, col]
    ax.plot(theta_grid, delta, color='#1f4e79', lw=2)
    ax.axhline(0, color='black', lw=0.5)
    ax.axvline(axis_deg, color='#a6396b', ls='--', lw=1, alpha=0.7,
               label=axis_label)
    ax.axvline((axis_deg + 180) % 360, color='#a6396b', ls=':', lw=1, alpha=0.5)
    ax.set_xticks([0, 90, 180, 270, 360])
    ax.set_xlim(0, 360)
    ax.set_ylim(-50, 50)   # extra headroom so legend stays clear of curve
    ax.set_xlabel('θ (degrees)')
    ax.set_ylabel('δθ (degrees)')
    ax.set_title(title, fontsize=11, fontweight='bold')
    ax.legend(loc='upper right', fontsize=7, framealpha=0.85)
    ax.grid(alpha=0.3)

    # --- Bottom row: Stretch ring ---
    ax = axes[1, col]
    # Polar-style ring with color encoding stretch
    R_OUTER = 1.05
    R_INNER = 0.85
    n_segments = 360
    seg_angles = np.linspace(0, 360, n_segments + 1)
    seg_centers = (seg_angles[:-1] + seg_angles[1:]) / 2
    seg_stretch = 1 - (beta * np.pi/180) * np.sin(np.radians(seg_centers - axis_deg))

    vmin, vmax = 0.5, 1.5
    cmap = plt.cm.RdBu_r  # red = expansion (>1), blue = compression (<1)
    norm = plt.Normalize(vmin=vmin, vmax=vmax)

    for i in range(n_segments):
        wedge = Wedge((0, 0), R_OUTER, seg_angles[i], seg_angles[i+1],
                      width=R_OUTER - R_INNER, facecolor=cmap(norm(seg_stretch[i])),
                      edgecolor='none')
        ax.add_patch(wedge)

    # Mark named axis poles — labels sit well outside the colored ring so they
    # do not collide with the red/blue gradient.
    for sign, marker_size in [(1, 12), (-1, 8)]:
        ang = (axis_deg if sign == 1 else axis_deg + 180) % 360
        x = (R_OUTER + 0.22) * np.cos(np.radians(ang))
        y = (R_OUTER + 0.22) * np.sin(np.radians(ang))
        ax.text(x, y, f'{int(ang)}°', ha='center', va='center', fontsize=9,
                fontweight='bold' if sign == 1 else 'normal',
                color='#a6396b')

    # Mark perpendicular (max stretch effect)
    perp_pos = (axis_deg - 90) % 360
    perp_neg = (axis_deg + 90) % 360
    for ang, label in [(perp_pos, '+1+β'), (perp_neg, '+1−β')]:
        if beta < 0:
            label = label.replace('+1+β', '+1−|β|').replace('+1−β', '+1+|β|')
        x = (R_OUTER + 0.18) * np.cos(np.radians(ang))
        y = (R_OUTER + 0.18) * np.sin(np.radians(ang))
        # ax.annotate(label, (x, y), ha='center', va='center', fontsize=7,
        #             color='#444')

    # Draw cardinal hue tick marks (0/90/180/270) — labels offset further out.
    for ang, name in [(0, 'L+'), (90, 'S+'), (180, 'L−'), (270, 'S−')]:
        x_in = R_INNER * np.cos(np.radians(ang))
        y_in = R_INNER * np.sin(np.radians(ang))
        x_out = R_OUTER * np.cos(np.radians(ang))
        y_out = R_OUTER * np.sin(np.radians(ang))
        ax.plot([x_in, x_out], [y_in, y_out], color='black', lw=0.6, alpha=0.5)
        x_lbl = (R_OUTER + 0.12) * np.cos(np.radians(ang))
        y_lbl = (R_OUTER + 0.12) * np.sin(np.radians(ang))
        ax.text(x_lbl, y_lbl, name, ha='center', va='center', fontsize=8,
                color='#666')

    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(-1.5, 1.5)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('Local stretch factor  1 − β·sin(θ−φ)', fontsize=9)

# Single colorbar on the right
cax = fig.add_axes([0.92, 0.10, 0.012, 0.34])
cb = plt.colorbar(plt.cm.ScalarMappable(norm=plt.Normalize(0.5, 1.5), cmap='RdBu_r'),
                  cax=cax)
cb.set_label('Local stretch  d(θ′)/dθ', fontsize=9)
cb.ax.tick_params(labelsize=8)
cb.set_ticks([0.5, 0.75, 1.0, 1.25, 1.5])
cb.ax.text(2.5, 1.5, 'expansion', fontsize=8, color='#b22222',
           transform=cb.ax.transAxes)
cb.ax.text(2.5, 0.0, 'compression', fontsize=8, color='#1f4e79',
           transform=cb.ax.transAxes)

fig.suptitle('2-Component model — sign of β controls perpendicular-axis '
             'compression/expansion, NOT named-axis dilation',
             fontsize=12, fontweight='bold', y=0.98)

# Footer note — split across 2 lines, narrower per-line text, smaller font.
fig.text(0.5, 0.025,
         'Top: angular displacement δθ(θ).   Bottom: local stretch factor on hue ring.\n'
         'β > 0 ⇒ expansion at θ_axis − 90°, compression at θ_axis + 90°  '
         '(β < 0 reverses).\n'
         'Named-axis poles (θ_axis, θ_axis+180°) have stretch = 1 (translation only).',
         ha='center', fontsize=8, style='italic')

plt.tight_layout(rect=[0, 0.09, 0.91, 0.95])
fig.savefig(OUT_PATH, dpi=140, bbox_inches='tight')
print(f'Wrote → {OUT_PATH}')
