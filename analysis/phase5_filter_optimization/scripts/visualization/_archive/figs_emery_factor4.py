"""Emery 2021 Factor 4 — structural form visualization.

Shows the non-uniform hue-circle warp pattern of Emery Factor 4:
  · Zero displacement at LvsM axis (R=0°, G=180°)
  · Maximum displacement at S-axis (Y=90°, B=270°), antiphase
  · One region compressed, opposite expanded (depends on β_s sign)

Structurally identical to β_s·sin(θ) in our 2-component model.

Output: presentation/figures/data/emery_factor4.png
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import numpy as np

SCRIPT = Path(__file__).resolve()
OUT_DIR = SCRIPT.parents[2] / "presentation" / "figures" / "data"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------ style
BG = "#fafbfc"
COL_ARROW = "#1f4e79"   # navy
COL_ZERO  = "#bbbbbb"   # grey for zero-tick
COL_EXP   = "#fef3e2"   # light orange — expansion zone
COL_COMP  = "#e8f4fd"   # light blue  — compression zone
COL_TEXT  = "#444444"

HUE_RGB = [
    "#e41a1c",  # red     0°
    "#ff7f00",  # orange 45°
    "#ffd700",  # yellow  90°
    "#4daf4a",  # green  135°
    "#00ced1",  # cyan   180°
    "#2780bf",  # blcyan 225°
    "#1f3a93",  # blue   270°
    "#d44c9a",  # magenta315°
]
ANGLES_DEG = np.array([0, 45, 90, 135, 180, 225, 270, 315], dtype=float)
ANGLES_RAD = np.radians(ANGLES_DEG)

ARROW_SCALE = 0.32
DOT_SIZE    = 13

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 11,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.spines.left": False, "axes.spines.bottom": False,
})

# ------------------------------------------------------------------ figure
fig, ax = plt.subplots(figsize=(6, 6.4), facecolor=BG)
fig.subplots_adjust(left=0.04, right=0.96, top=0.88, bottom=0.09)
ax.set_aspect("equal")
ax.axis("off")

# ── background shading: compression vs expansion (β_s > 0)
# With β_s > 0: sin(θ) displaces colors toward G(180°) from both sides
# → G/Cyan zone COMPRESSES, R zone EXPANDS.
def filled_arc(ax, theta1_deg, theta2_deg, r_inner, r_outer, color, alpha=0.35, n=120):
    t = np.linspace(np.radians(theta1_deg), np.radians(theta2_deg), n)
    xs = np.concatenate([r_inner * np.cos(t), r_outer * np.cos(t[::-1])])
    ys = np.concatenate([r_inner * np.sin(t), r_outer * np.sin(t[::-1])])
    ax.fill(xs, ys, color=color, alpha=alpha, zorder=0)

# Compression zone: around G(180°), ±70°
filled_arc(ax, 110, 250, 0.70, 1.28, COL_COMP, alpha=0.45)
# Expansion zone: around R(0°/360°), ±70°
filled_arc(ax, 290, 360, 0.70, 1.28, COL_EXP, alpha=0.45)
filled_arc(ax, 0, 70, 0.70, 1.28, COL_EXP, alpha=0.45)

# Zone labels
ax.text( 0.00,  0.90, "COMPRESSION", ha="center", va="center",
         fontsize=8, color="#2980b9", fontweight="bold", style="italic")
ax.text( 0.00, -0.90, "COMPRESSION", ha="center", va="center",
         fontsize=8, color="#2980b9", fontweight="bold", style="italic")
ax.text( 1.00,  0.00, "EXPANSION",   ha="center", va="center",
         fontsize=8, color="#e67e22", fontweight="bold", style="italic",
         rotation=90)

# ── background ring
theta_ring = np.linspace(0, 2 * np.pi, 360)
ax.plot(np.cos(theta_ring), np.sin(theta_ring), color="#cccccc", lw=1.2, zorder=1)

# ── axis spokes + labels
for ang, lbl, adj in [
    (0,   "R", (+0.16,  0.00)),
    (90,  "Y", ( 0.00, +0.16)),
    (180, "G", (-0.16,  0.00)),
    (270, "B", ( 0.00, -0.16)),
]:
    r = np.radians(ang)
    ax.plot([0, np.cos(r)], [0, np.sin(r)], color="#e0e0e0", lw=0.8, zorder=1)
    ax.text(1.22 * np.cos(r) + adj[0], 1.22 * np.sin(r) + adj[1],
            lbl, ha="center", va="center",
            fontsize=13, color="#888888", fontweight="bold")

# ── arrows + dots
for rgb, theta, theta_deg in zip(HUE_RGB, ANGLES_RAD, ANGLES_DEG):
    cx, cy = np.cos(theta), np.sin(theta)
    tx, ty = -np.sin(theta), np.cos(theta)   # CCW tangent
    mag    = np.sin(theta)                   # β_s · sin(θ) with β_s=+1

    ax.plot(cx, cy, "o", color=rgb, ms=DOT_SIZE,
            mec="#555555", mew=0.9, zorder=4)

    if abs(mag) < 0.04:
        # draw a small grey tick to mark zero
        ax.plot([cx - 0.04 * cx, cx + 0.04 * cx],
                [cy - 0.04 * cy, cy + 0.04 * cy],
                color=COL_ZERO, lw=2.0, zorder=5)
        # "zero" label near R and G
        lbl_x = cx * 1.38
        lbl_y = cy * 1.38
        ax.text(lbl_x, lbl_y, "0", ha="center", va="center",
                fontsize=9, color=COL_ZERO, fontweight="bold")
        continue

    dx = mag * ARROW_SCALE * tx
    dy = mag * ARROW_SCALE * ty
    ax.annotate(
        "",
        xy=(cx + dx, cy + dy),
        xytext=(cx, cy),
        arrowprops=dict(arrowstyle="-|>", color=COL_ARROW,
                        lw=2.2, mutation_scale=13),
        zorder=5,
    )

# ── "antiphase" bracket between Y(90°) and B(270°)
ax.annotate(
    "", xy=(0.0, -1.45), xytext=(0.0, 1.45),
    arrowprops=dict(arrowstyle="<->", color="#666666", lw=1.2,
                    connectionstyle="arc3,rad=0.55"),
    zorder=6,
)
ax.text(-0.52, 0.00, "antiphase", ha="center", va="center",
        fontsize=9, color="#666666", style="italic",
        rotation=90)

# ── "zero at R, G" annotation
ax.annotate("zero at R, G", xy=(1.0, 0), xytext=(1.45, -0.35),
            fontsize=8.5, color=COL_ZERO,
            ha="center", va="center",
            arrowprops=dict(arrowstyle="-", color=COL_ZERO, lw=0.8,
                            connectionstyle="arc3,rad=-0.2"))

ax.set_xlim(-1.55, 1.55)
ax.set_ylim(-1.65, 1.55)

ax.set_title("Emery 2021  —  Factor 4\n"
             r"$\beta_s \cdot \sin(\theta)$  structure: zero at LvsM axis, antiphase at S-axis",
             fontsize=11, color=COL_ARROW, pad=8, fontweight="bold")

fig.text(0.5, 0.01,
         "Arrow length ∝ displacement magnitude  ·  shading: compression (blue) / expansion (orange)  ·  β_s sign determines which zone",
         ha="center", fontsize=7.5, color="#999999", style="italic")

out = OUT_DIR / "emery_factor4.png"
fig.savefig(out, dpi=200, facecolor=BG, bbox_inches="tight")
print(f"[saved] {out}")
plt.close(fig)
