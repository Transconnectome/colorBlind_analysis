"""2-Component model anatomy — β_s and β_c independent axis panels.

Two side-by-side hue circles (unit amplitude):
  Left:  β_s · sin(θ)       — S-cone axis, zero at R/G, antiphase B vs Y
  Right: β_c · cos(θ−150°)  — deutan confusion axis, zero at 60°/240°

Arrows are tangential, length ∝ displacement magnitude, direction = CCW or CW.
Minimal text: only axis labels (R/G/B/Y) and subplot titles.

Output: presentation/figures/data/two_comp_anatomy.png
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

SCRIPT = Path(__file__).resolve()
PROJECT = SCRIPT.parents[4]
OUT_DIR = SCRIPT.parents[2] / "presentation" / "figures" / "data"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------ style
BG = "#fafbfc"
COL_BS = "#1f4e79"     # navy — β_s component
COL_BC = "#a93226"     # dark-red — β_c component
COL_ZERO = "#cccccc"   # zero-line indicator

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.spines.left": False,
    "axes.spines.bottom": False,
})

# ------------------------------------------------------------------ data
HUE_RGB = [
    "#e41a1c",  # red    0°
    "#ff7f00",  # orange 45°
    "#ffd700",  # yellow 90°
    "#4daf4a",  # green  135°
    "#00ced1",  # cyan   180°
    "#2780bf",  # blue-cyan 225°
    "#1f3a93",  # blue   270°
    "#d44c9a",  # magenta 315°
]
ANGLES_DEG = np.array([0, 45, 90, 135, 180, 225, 270, 315], dtype=float)
ANGLES_RAD = np.radians(ANGLES_DEG)

THETA_CONF_DEUTAN = np.radians(150.0)   # Brettel confusion line
ARROW_SCALE = 0.32   # visual scale: unit amplitude → arrow length on unit circle


# ------------------------------------------------------------------ helper
def draw_circle(ax):
    """Background ring + axis spokes + R/G/B/Y labels."""
    t = np.linspace(0, 2 * np.pi, 360)
    ax.plot(np.cos(t), np.sin(t), color="#cccccc", lw=1.2, zorder=0)
    for ang in [0, 90, 180, 270]:
        r = np.radians(ang)
        ax.plot([0, np.cos(r)], [0, np.sin(r)], color="#e4e4e4", lw=0.9, zorder=0)
    for ang, lbl, adj in [
        (0,   "R", (+0.14,  0.00)),
        (90,  "Y", ( 0.00, +0.14)),
        (180, "G", (-0.14,  0.00)),
        (270, "B", ( 0.00, -0.14)),
    ]:
        r = np.radians(ang)
        ax.text(1.20 * np.cos(r) + adj[0], 1.20 * np.sin(r) + adj[1],
                lbl, ha="center", va="center",
                fontsize=12, color="#aaaaaa", fontweight="bold")


def draw_component(ax, magnitudes, color, label_col, dot_size=13):
    """
    Draw color dots + tangential arrows for one component.

    magnitudes: array of signed angular displacements (unit amplitude).
    Arrow direction encodes sign (CCW = positive, CW = negative).
    Arrow length encodes magnitude.
    """
    draw_circle(ax)

    for i, (rgb, theta, mag) in enumerate(zip(HUE_RGB, ANGLES_RAD, magnitudes)):
        cx, cy = np.cos(theta), np.sin(theta)
        # Tangential unit vector (CCW direction)
        tx, ty = -np.sin(theta), np.cos(theta)

        # Dot
        ax.plot(cx, cy, "o", color=rgb, ms=dot_size,
                mec="#555555", mew=0.9, zorder=3)

        if abs(mag) < 0.04:
            # Zero: draw a small grey tick perpendicular (radial) to indicate null
            rx, ry = np.cos(theta), np.sin(theta)
            ax.plot([cx - 0.04 * rx, cx + 0.04 * rx],
                    [cy - 0.04 * ry, cy + 0.04 * ry],
                    color=COL_ZERO, lw=1.5, zorder=4)
            continue

        # Arrow from dot to displaced position on circle
        dx = mag * ARROW_SCALE * tx
        dy = mag * ARROW_SCALE * ty
        ax.annotate(
            "",
            xy=(cx + dx, cy + dy),
            xytext=(cx, cy),
            arrowprops=dict(
                arrowstyle="-|>",
                color=color,
                lw=2.0,
                mutation_scale=12,
            ),
            zorder=5,
        )

    ax.set_xlim(-1.48, 1.48)
    ax.set_ylim(-1.48, 1.48)
    ax.set_aspect("equal")
    ax.axis("off")


# ------------------------------------------------------------------ compute
# β_s component: δθ = sin(θ)
bs_mags = np.sin(ANGLES_RAD)

# β_c component (deutan): δθ = cos(θ − 150°)
bc_mags = np.cos(ANGLES_RAD - THETA_CONF_DEUTAN)

# ------------------------------------------------------------------ figure
fig, axes = plt.subplots(1, 2, figsize=(10, 5.2), facecolor=BG)
fig.subplots_adjust(left=0.02, right=0.98, top=0.84, bottom=0.02, wspace=0.05)

draw_component(axes[0], bs_mags, COL_BS, COL_BS)
draw_component(axes[1], bc_mags, COL_BC, COL_BC)

axes[0].set_title(r"$\beta_s \cdot \sin(\theta)$  —  S-cone axis",
                  fontsize=12, color=COL_BS, pad=10, fontweight="bold")
axes[1].set_title(r"$\beta_c \cdot \cos(\theta - 150°)$  —  confusion axis (deutan)",
                  fontsize=12, color=COL_BC, pad=10, fontweight="bold")

# Minimal footnote
fig.text(0.5, 0.01, "Arrow direction = tangential displacement  ·  length ∝ magnitude  ·  grey tick = zero",
         ha="center", fontsize=8.5, color="#999999", style="italic")

out = OUT_DIR / "two_comp_anatomy.png"
fig.savefig(out, dpi=200, facecolor=BG, bbox_inches="tight")
print(f"[saved] {out}")
plt.close(fig)
