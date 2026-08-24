"""R+C model panels — three separate figures for presentation.

Panel A: Stockman LMS + M-cone shift (cone level)
Panel C: Hue circle — 8 colors before and after Δλ (retinal shift)
Panel D: Opponent plane — retinal → final with horizontal (RG-only) g arrows

Outputs:
  presentation/figures/data/rc_panel_a.png
  presentation/figures/data/rc_panel_c.png
  presentation/figures/data/rc_panel_d.png
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np

# --------------------------------------------------------------------- paths
SCRIPT = Path(__file__).resolve()
PROJECT = SCRIPT.parents[4]
SCRIPTS = PROJECT / "analysis" / "phase5_filter_optimization" / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(PROJECT / "analysis" / "phase4_forward_model" / "scripts"))

from machado_simulator import machado_shifted_hue
from stockman_cone_shift import (
    COLOR_NAMES,
    load_stockman_fundamentals,
    shift_cone_sensitivity,
)

OUT_DIR = SCRIPT.parents[2] / "presentation" / "figures" / "data"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------- style
ACCENT = "#1f4e79"
BG = "#fafbfc"
COL_BASE = "#555555"
COL_RET = "#7a3d8a"    # purple — after Δλ
COL_FINAL = "#1f4e79"  # navy  — after g
COL_L = "#c0392b"
COL_M = "#27ae60"
COL_S = "#2980b9"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 11,
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "axes.labelsize": 10,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "axes.spines.top": False,
    "axes.spines.right": False,
})

# --------------------------------------------------------------------- params
DELTA_LAMBDA = 18.0   # nm, deutan example
G_GAIN = -0.7         # cortical gain (70 % compensation toward baseline)
CVD_TYPE = "deutan"

# 8 hue colors: approximate CIELab display colors
HUE_RGB = [
    "#e41a1c",  # red 0°
    "#ff7f00",  # orange 45°
    "#ffd700",  # yellow 90°
    "#4daf4a",  # green 135°
    "#00ced1",  # cyan 180°
    "#2780bf",  # blue-cyan 225°
    "#1f3a93",  # blue 270°
    "#d44c9a",  # magenta 315°
]

# --------------------------------------------------------------------- compute hue angles
hue_base, hue_ret, _ = machado_shifted_hue(DELTA_LAMBDA, CVD_TYPE)

# R+C cortical stage: compute explicitly so we can show intermediate steps
theta_base_rad = np.radians(hue_base)
theta_ret_rad = np.radians(hue_ret)

rg_base = np.cos(theta_base_rad)
by_base = np.sin(theta_base_rad)
rg_ret = np.cos(theta_ret_rad)
by_ret = np.sin(theta_ret_rad)

# Cortical gain — RG only
rg_final = rg_ret + G_GAIN * (rg_ret - rg_base)
by_final = by_ret   # BY unchanged

hue_final = np.degrees(np.arctan2(by_final, rg_final)) % 360.0

# --------------------------------------------------------------------- Panel A: Stockman LMS
wl, L, M, S = load_stockman_fundamentals()
M_shift = shift_cone_sensitivity(wl, M, DELTA_LAMBDA)

fig_a, ax_a = plt.subplots(figsize=(7, 5), facecolor=BG)
ax_a.plot(wl, L, color=COL_L, lw=2.2, label=r"$S_L(\lambda)$")
ax_a.plot(wl, M, color=COL_M, lw=2.2, label=r"$S_M(\lambda)$")
ax_a.plot(wl, S, color=COL_S, lw=2.2, label=r"$S_S(\lambda)$")
ax_a.plot(wl, M_shift, color=COL_M, lw=1.8, ls="--",
          label=fr"$S_M(\lambda-{DELTA_LAMBDA:.0f})$  (deutan shift)")

peak_idx = int(np.argmax(M))
peak_wl = wl[peak_idx]
ax_a.annotate("", xy=(peak_wl + DELTA_LAMBDA, 0.55), xytext=(peak_wl, 0.55),
              arrowprops=dict(arrowstyle="->", color=COL_M, lw=1.5))
ax_a.annotate(fr"$\Delta\lambda$ = {DELTA_LAMBDA:.0f} nm",
              xy=(peak_wl + DELTA_LAMBDA / 2, 0.55), xytext=(660, 0.30),
              color=COL_M, ha="center", fontsize=10, fontweight="bold",
              arrowprops=dict(arrowstyle="-", color=COL_M, lw=0.7, alpha=0.6))

ax_a.set_xlim(390, 720)
ax_a.set_ylim(0, 1.05)
ax_a.set_xlabel("Wavelength λ (nm)")
ax_a.set_ylabel("Cone sensitivity (normalized)")
ax_a.set_title(f"Retinal stage — M-cone shifts {DELTA_LAMBDA:.0f} nm toward L (deutan)")
ax_a.legend(loc="upper right", frameon=False, fontsize=9.5)
ax_a.grid(alpha=0.2, linestyle=":")
fig_a.tight_layout()
out_a = OUT_DIR / "rc_panel_a.png"
fig_a.savefig(out_a, dpi=200, facecolor=BG)
print(f"[saved] {out_a}")
plt.close(fig_a)

# --------------------------------------------------------------------- Panel C: hue circle — Δλ effect
# Use CIELab convention for placement (0°=red right, 90°=yellow up, 270°=blue down)
# so the circle matches audience intuition.  Movement arrows encode delta_theta from
# the Machado opponent-space model, capped at ±75° to handle the near-axis instability
# of blue (which has only tiny opponent-space chromatic magnitude in Stockman space).

CIELAB_ANGLES = np.array([0, 45, 90, 135, 180, 225, 270, 315], dtype=float)
ARROW_SCALE = 1.0      # length of arrow = delta_theta / 180 * pi * ARROW_SCALE
DELTA_CAP = 75.0       # max |delta_theta| shown; blue anomaly is ~144°

_, _, delta_ret = machado_shifted_hue(DELTA_LAMBDA, CVD_TYPE)  # opponent-space delta
delta_ret_capped = np.clip(delta_ret, -DELTA_CAP, DELTA_CAP)

fig_c, ax_c = plt.subplots(figsize=(6, 6), facecolor=BG)
ax_c.set_aspect("equal")
ax_c.axis("off")

# Background unit circle
theta_ring = np.linspace(0, 2 * np.pi, 360)
ax_c.plot(np.cos(theta_ring), np.sin(theta_ring), color="#cccccc", lw=1.2, zorder=0)

# Axis labels — CIELab convention (b*>0 = yellow up, b*<0 = blue down)
for ang, lbl, adj in [(0, "R", (0.13, 0)), (180, "G", (-0.13, 0)),
                       (90, "Y", (0, 0.13)), (270, "B", (0, -0.13))]:
    r = np.radians(ang)
    ax_c.text(1.15 * np.cos(r) + adj[0], 1.15 * np.sin(r) + adj[1],
              lbl, ha="center", va="center", fontsize=12,
              color="#999999", fontweight="bold")

# Thin grey spokes
for ang in [0, 90, 180, 270]:
    r = np.radians(ang)
    ax_c.plot([0, np.cos(r)], [0, np.sin(r)], color="#e0e0e0", lw=0.8, zorder=0)

for i, (name, rgb) in enumerate(zip(COLOR_NAMES, HUE_RGB)):
    base_ang = np.radians(CIELAB_ANGLES[i])
    shift_ang = np.radians(CIELAB_ANGLES[i] + delta_ret_capped[i])

    bx, by_coord = np.cos(base_ang), np.sin(base_ang)
    rx, ry = np.cos(shift_ang), np.sin(shift_ang)

    is_blue = (name == "blue")
    lw = 1.4 if not is_blue else 1.0
    ls = "-" if not is_blue else "--"
    alpha_arrow = 0.9 if not is_blue else 0.45

    # Arrow from baseline to shifted
    ax_c.annotate("", xy=(rx, ry), xytext=(bx, by_coord),
                  arrowprops=dict(arrowstyle="-|>", color=COL_RET,
                                  lw=lw, linestyle=ls, mutation_scale=11,
                                  alpha=alpha_arrow),
                  zorder=2)
    # Baseline filled dot
    ax_c.plot(bx, by_coord, "o", color=rgb, ms=14, mec=COL_BASE, mew=1.2,
              zorder=3)
    # Shifted open ring
    ax_c.plot(rx, ry, "o", color=rgb, ms=14, mec=COL_RET, mew=2.0,
              markerfacecolor="white", alpha=0.9, zorder=4)

    # Color name label — offset outward from baseline
    lx = 1.28 * np.cos(base_ang)
    ly = 1.28 * np.sin(base_ang)
    ax_c.text(lx, ly, name, ha="center", va="center", fontsize=9,
              color="#444444", fontweight="bold")

h_b = mpatches.Patch(facecolor=COL_BASE, label="baseline (HC)  ●")
h_r = mpatches.Patch(facecolor=COL_RET,
                     label=f"after Δλ={DELTA_LAMBDA:.0f} nm deutan  ○")
ax_c.legend(handles=[h_b, h_r], loc="lower right",
            frameon=True, framealpha=0.9, fontsize=9)

ax_c.set_xlim(-1.50, 1.50)
ax_c.set_ylim(-1.50, 1.50)
ax_c.set_title(
    f"Retinal stage — hue shift under Δλ={DELTA_LAMBDA:.0f} nm (deutan)\n"
    "R/G-region colors shift most  ·  blue: dashed = near-axis instability",
    fontsize=10.5, pad=10)
fig_c.tight_layout()
out_c = OUT_DIR / "rc_panel_c.png"
fig_c.savefig(out_c, dpi=200, facecolor=BG)
print(f"[saved] {out_c}")
plt.close(fig_c)

# --------------------------------------------------------------------- Panel D: hue circle — g effect
# Use CIELab convention (same as Panel C) so colors sit at expected positions.
# Baseline = CIELAB_ANGLES; retinal = CIELAB_ANGLES + delta_ret_capped.
# g acts only on the RG component → project back to angle to get final hue.
theta_nom_d  = np.radians(CIELAB_ANGLES)
theta_ret_d  = np.radians(CIELAB_ANGLES + delta_ret_capped)
rg_nom_d     = np.cos(theta_nom_d)
by_nom_d     = np.sin(theta_nom_d)
rg_ret_d     = np.cos(theta_ret_d)
by_ret_d     = np.sin(theta_ret_d)
rg_fin_d     = rg_ret_d + G_GAIN * (rg_ret_d - rg_nom_d)
by_fin_d     = by_ret_d    # BY unchanged
hue_fin_d    = np.degrees(np.arctan2(by_fin_d, rg_fin_d)) % 360.0

fig_d, ax_d = plt.subplots(figsize=(6, 6.2), facecolor=BG)
fig_d.subplots_adjust(left=0.04, right=0.96, top=0.87, bottom=0.06)
ax_d.set_aspect("equal")
ax_d.axis("off")

# Warm band on RG axis: g only acts on RG
ax_d.fill_between([-1.4, 1.4], [-0.09, -0.09], [0.09, 0.09],
                  color="#fde8cc", alpha=0.40, zorder=0)

# Background unit circle + axis spokes + RGBY labels
theta_ring = np.linspace(0, 2 * np.pi, 360)
ax_d.plot(np.cos(theta_ring), np.sin(theta_ring), color="#cccccc", lw=1.2, zorder=1)
for ang, lbl, adj in [(0, "R", (+0.14, 0.00)), (180, "G", (-0.14, 0.00)),
                       (90, "Y", (0.00, +0.14)), (270, "B", (0.00, -0.14))]:
    r = np.radians(ang)
    ax_d.plot([0, np.cos(r)], [0, np.sin(r)], color="#e0e0e0", lw=0.8, zorder=1)
    ax_d.text(1.20 * np.cos(r) + adj[0], 1.20 * np.sin(r) + adj[1],
              lbl, ha="center", va="center", fontsize=13,
              color="#888888", fontweight="bold")

for i, (name, rgb) in enumerate(zip(COLOR_NAMES, HUE_RGB)):
    nom_ang = CIELAB_ANGLES[i]           # baseline (nominal)
    ret_ang = CIELAB_ANGLES[i] + delta_ret_capped[i]  # retinal (panel C convention)
    fin_ang = hue_fin_d[i]               # g-corrected

    bx = np.cos(np.radians(nom_ang));  by_c = np.sin(np.radians(nom_ang))
    rx = np.cos(np.radians(ret_ang));  ry   = np.sin(np.radians(ret_ang))
    fx = np.cos(np.radians(fin_ang));  fy   = np.sin(np.radians(fin_ang))

    # Colors that hit the delta cap = near-axis instability (same treatment as Panel C)
    is_unstable = abs(delta_ret_capped[i]) >= DELTA_CAP - 1.0

    # Faint ghost: baseline (HC) position
    ax_d.plot(bx, by_c, "o", color=rgb, ms=9, mec=COL_BASE, mew=0.6,
              alpha=0.22, zorder=2)

    # Arrow: retinal → g-corrected (skip if negligible)
    diff = abs(fin_ang - ret_ang) % 360
    if diff > 180:
        diff = 360 - diff
    if diff > 0.5:
        arr_alpha = 0.35 if is_unstable else 1.0
        arr_ls    = "--" if is_unstable else "-"
        arr_lw    = 1.0  if is_unstable else 1.8
        ax_d.annotate("", xy=(fx, fy), xytext=(rx, ry),
                      arrowprops=dict(arrowstyle="-|>", color=COL_FINAL,
                                      lw=arr_lw, linestyle=arr_ls,
                                      mutation_scale=12,
                                      alpha=arr_alpha),
                      zorder=5)

    # Retinal position: filled square ■
    sq_alpha = 0.50 if is_unstable else 1.0
    ax_d.plot(rx, ry, "s", color=rgb, ms=13, mec=COL_RET, mew=1.8,
              alpha=sq_alpha, zorder=3)
    # g-corrected position: open diamond ◇
    ax_d.plot(fx, fy, "D", color=rgb, ms=10, mec=COL_FINAL, mew=2.0,
              markerfacecolor="white",
              alpha=0.45 if is_unstable else 0.95, zorder=4)

    # Color name label offset outward from retinal position
    lx = 1.30 * np.cos(np.radians(ret_ang))
    ly = 1.30 * np.sin(np.radians(ret_ang))
    txt_col = "#aaaaaa" if is_unstable else "#444444"
    ax_d.text(lx, ly, name, ha="center", va="center", fontsize=8.5,
              color=txt_col, fontweight="bold")

ax_d.text(0.0, -1.56, "BY unchanged  ·  B/Y barely move  ·  dashed = near-axis instability",
          ha="center", va="top", fontsize=7, color="#888888", style="italic")

ax_d.set_xlim(-1.55, 1.55)
ax_d.set_ylim(-1.80, 1.55)
ax_d.set_title(
    f"Cortical RG-gain stage  ·  g = {G_GAIN:+.1f}\n"
    "■ retinal  →  ◇ g-corrected   (ghost ● = HC baseline)",
    fontsize=10.5, pad=8, color=ACCENT)

h_base = mpatches.Patch(facecolor=COL_BASE, alpha=0.30, label="baseline ●  (HC)")
h_ret2 = mpatches.Patch(facecolor=COL_RET,   label=f"retinal ■  (Δλ={DELTA_LAMBDA:.0f} nm)")
h_fin2 = mpatches.Patch(facecolor=COL_FINAL, label=f"g-corrected ◇  (g={G_GAIN:+.1f})")
ax_d.legend(handles=[h_base, h_ret2, h_fin2], loc="lower right",
            frameon=True, framealpha=0.90, fontsize=8.5)

out_d = OUT_DIR / "rc_panel_d.png"
fig_d.savefig(out_d, dpi=200, facecolor=BG, bbox_inches="tight")
print(f"[saved] {out_d}")
plt.close(fig_d)
