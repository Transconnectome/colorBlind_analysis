"""Slide 5 supplementary — R+C model 4-panel mechanism figure.

Visualizes how retinal shift (Δλ = r) and cortical gain (g) separately act on
the LMS → opponent → hue pipeline, in line with mathematical_basis.md §10.

Panels:
  A (top-left)   Stockman LMS curves + dashed M-cone shifted (deutan example)
  B (top-right)  Forward-equation card (LMS → opponent → atan2)
  C (bot-left)   Opponent plane — baseline → retinal-shifted (5 test stimuli)
  D (bot-right)  Opponent plane — retinal → final (RG-axis displacement × (1+g))

Output: presentation/figures/data/slide5_rc_panels.png
Companion: ../mathematical_basis.md §10
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np

# --------------------------------------------------------------------- paths
SCRIPT = Path(__file__).resolve()
PROJECT = SCRIPT.parents[4]  # …/colorBlind_analysis
OUT = (SCRIPT.parents[2] / "presentation" / "figures" / "data" /
       "slide5_rc_panels.png")
OUT.parent.mkdir(parents=True, exist_ok=True)

# Reuse the Stockman loader from future_phase1_forward_model
sys.path.insert(0, str(PROJECT / "analysis" / "future_phase1_forward_model" / "scripts"))
from stockman_cone_shift import load_stockman_fundamentals, shift_cone_sensitivity

# --------------------------------------------------------------------- style
ACCENT = "#1f4e79"
BG = "#fafbfc"
COL_L = "#c0392b"   # red
COL_M = "#27ae60"   # green
COL_S = "#2980b9"   # blue
COL_BASE = "#444444"
COL_RET = "#7a3d8a"  # purple
COL_FINAL = "#1f4e79"  # navy

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.titleweight": "bold",
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "axes.spines.top": False,
    "axes.spines.right": False,
})

# --------------------------------------------------------------------- params
DELTA_LAMBDA = 18.0   # retinal shift r (nm), deutan example (chosen for visibility)
G_GAIN = -0.7         # cortical gain g (70% compensation toward baseline)

# 5 representative test stimuli: monochromatic at peak wavelengths spanning hue
TEST_WL = np.array([600.0, 580.0, 540.0, 500.0, 460.0])   # nm
TEST_NAME = ["red", "yellow", "yel-grn", "cyan", "blue"]
TEST_COLOR = ["#e41a1c", "#ffd700", "#4daf4a", "#00ced1", "#1f3a93"]

# --------------------------------------------------------------------- compute
wl, L, M, S = load_stockman_fundamentals()

# Retinal-shifted M-cone (deutan: M shifts toward L)
M_shift = shift_cone_sensitivity(wl, M, DELTA_LAMBDA)

# For monochromatic test stimuli, LMS = sensitivity at that wavelength
def lms_at(wavelengths, sens_L, sens_M, sens_S, target_wls):
    """Return (n_test, 3) LMS for monochromatic stimuli at target wavelengths."""
    L_t = np.interp(target_wls, wavelengths, sens_L)
    M_t = np.interp(target_wls, wavelengths, sens_M)
    S_t = np.interp(target_wls, wavelengths, sens_S)
    return np.stack([L_t, M_t, S_t], axis=1)

lms_base = lms_at(wl, L, M, S, TEST_WL)
lms_ret  = lms_at(wl, L, M_shift, S, TEST_WL)

def opponent(lms):
    """LMS (n,3) → opponent (n,2) where col0 = RG, col1 = BY."""
    rg = lms[:, 0] - lms[:, 1]
    by = lms[:, 2] - 0.5 * (lms[:, 0] + lms[:, 1])
    return np.stack([rg, by], axis=1)

opp_base = opponent(lms_base)
opp_ret  = opponent(lms_ret)

# Cortical gain: RG_final = (1+g)·RG_ret - g·RG_base; BY unchanged
opp_final = opp_ret.copy()
opp_final[:, 0] = (1 + G_GAIN) * opp_ret[:, 0] - G_GAIN * opp_base[:, 0]

# --------------------------------------------------------------------- figure
fig = plt.figure(figsize=(14, 10), facecolor=BG)
gs = fig.add_gridspec(2, 2, hspace=0.42, wspace=0.30,
                       left=0.07, right=0.97, top=0.91, bottom=0.07)

fig.suptitle(
    "R+C Model — Pipeline Visualization  (retinal Δλ + cortical RG-axis gain)",
    fontsize=14, fontweight="bold", color=ACCENT, y=0.97)

# ============================================================ Panel A — LMS
axA = fig.add_subplot(gs[0, 0])
axA.plot(wl, L, color=COL_L, lw=2.2, label=r"$S_L(\lambda)$")
axA.plot(wl, M, color=COL_M, lw=2.2, label=r"$S_M(\lambda)$")
axA.plot(wl, S, color=COL_S, lw=2.2, label=r"$S_S(\lambda)$")
axA.plot(wl, M_shift, color=COL_M, lw=1.8, ls="--",
          label=fr"$S_M(\lambda - {DELTA_LAMBDA:.0f})$ (deutan)")

# Annotate shift direction — short arrow on curve, label moved to lower-right
# corner so the M-cone peak stays unobscured.
peak_idx = int(np.argmax(M))
peak_wl = wl[peak_idx]
axA.annotate("", xy=(peak_wl + DELTA_LAMBDA, 0.55), xytext=(peak_wl, 0.55),
              arrowprops=dict(arrowstyle="->", color=COL_M, lw=1.5))
axA.annotate(fr"$\Delta\lambda$ = {DELTA_LAMBDA:.0f} nm",
             xy=(peak_wl + DELTA_LAMBDA / 2, 0.55),
             xytext=(660, 0.30),
             color=COL_M, ha="center", fontsize=9, fontweight="bold",
             arrowprops=dict(arrowstyle="-", color=COL_M, lw=0.7, alpha=0.6))

axA.set_xlim(390, 720)
axA.set_ylim(0, 1.05)
axA.set_xlabel("Wavelength λ (nm)")
axA.set_ylabel("Cone sensitivity (normalized)")
axA.set_title("A.  Cone-level retinal shift")
axA.legend(loc="upper right", frameon=False, fontsize=8.5)
axA.grid(alpha=0.25, linestyle=":")

# ============================================================ Panel B — Eqs
axB = fig.add_subplot(gs[0, 1])
axB.axis("off")

eq_text = (
    r"$\bf{Forward\ map:}$"  "\n"
    r"$\quad (L,M,S)_{\rm ret} = \int E(\lambda)\,(S_L,\,S_M(\lambda{-}r),\,S_S)\,d\lambda$"  "\n\n"
    r"$\bf{Opponent\ transform:}$"  "\n"
    r"$\quad RG = L - M$"  "\n"
    r"$\quad BY = S - \frac{L+M}{2}$"  "\n\n"
    r"$\bf{Cortical\ gain\ (RG\ only):}$"  "\n"
    r"$\quad RG_{\rm final} = (1{+}g)\,RG_{\rm ret} - g\,RG_{\rm base}$"  "\n"
    r"$\quad BY_{\rm final} = BY_{\rm ret}$"  "\n\n"
    r"$\bf{Hue\ recovery:}$"  "\n"
    r"$\quad \theta_{\rm final} = \mathrm{atan2}(BY_{\rm final},\ RG_{\rm final})$"
)
axB.text(0.04, 0.96, eq_text, transform=axB.transAxes, va="top", ha="left",
          fontsize=11, family="monospace",
          bbox=dict(boxstyle="round,pad=0.6", facecolor="#f3f6fa",
                    edgecolor=ACCENT, lw=1.0))
axB.set_title("B.  Forward equations", loc="left")

# ============================================================ Panel C — opponent (retinal)
axC = fig.add_subplot(gs[1, 0])
_lim = 1.05 * max(np.abs(opp_base).max(), np.abs(opp_ret).max(), np.abs(opp_final).max())

# Quadrant guides
axC.axhline(0, color="#aaa", lw=0.7, zorder=0)
axC.axvline(0, color="#aaa", lw=0.7, zorder=0)

# Baseline points (filled circles) and retinal-shifted points (open squares)
for i, (name, c) in enumerate(zip(TEST_NAME, TEST_COLOR)):
    rb, yb = opp_base[i]
    rr, yr = opp_ret[i]
    axC.plot(rb, yb, "o", color=c, ms=11, mec=COL_BASE, mew=1.2,
              label=name if i == 0 else None, zorder=3)
    axC.plot(rr, yr, "s", color=c, ms=10, mec=COL_RET, mew=1.5, alpha=0.9, zorder=3)
    # Arrow baseline → retinal
    axC.annotate("", xy=(rr, yr), xytext=(rb, yb),
                  arrowprops=dict(arrowstyle="->", color=COL_RET, lw=1.3, alpha=0.75))
    # Color label
    axC.text(rb, yb + 0.04 * _lim, name, fontsize=8, ha="center", color=COL_BASE)

axC.set_xlim(-_lim, _lim)
axC.set_ylim(-_lim, _lim)
axC.set_aspect("equal")
axC.set_xlabel(r"$RG\ \ (L - M)$  →  red")
axC.set_ylabel(r"$BY\ \ (S - \frac{L+M}{2})$  →  blue")
axC.set_title(r"C.  Opponent plane — baseline ● → retinal-shifted ■")

# Legend — placed in upper-left corner away from data clusters which sit
# in lower/right quadrants of the opponent plane.
h_base = mpatches.Patch(facecolor=COL_BASE, edgecolor=COL_BASE, label="baseline ●")
h_ret = mpatches.Patch(facecolor=COL_RET, edgecolor=COL_RET, label=fr"retinal ■ (Δλ={DELTA_LAMBDA:.0f} nm)")
axC.legend(handles=[h_base, h_ret], loc="upper left", frameon=True,
           framealpha=0.85, fontsize=8.5)

# ============================================================ Panel D — opponent (cortical gain)
axD = fig.add_subplot(gs[1, 1])
axD.axhline(0, color="#aaa", lw=0.7, zorder=0)
axD.axvline(0, color="#aaa", lw=0.7, zorder=0)

# Show baseline (faded), retinal (squares), final (filled diamonds)
for i, (name, c) in enumerate(zip(TEST_NAME, TEST_COLOR)):
    rb, yb = opp_base[i]
    rr, yr = opp_ret[i]
    rf, yf = opp_final[i]
    # Faded baseline
    axD.plot(rb, yb, "o", color=c, ms=8, mec=COL_BASE, mew=0.8, alpha=0.25, zorder=2)
    # Retinal point (square, purple edge)
    axD.plot(rr, yr, "s", color=c, ms=10, mec=COL_RET, mew=1.5, zorder=3)
    # Final point (diamond, navy edge)
    axD.plot(rf, yf, "D", color=c, ms=11, mec=COL_FINAL, mew=1.6, zorder=4)
    # HORIZONTAL arrow: retinal → final (RG-axis displacement only)
    axD.annotate("", xy=(rf, yf), xytext=(rr, yr),
                  arrowprops=dict(arrowstyle="->", color=COL_FINAL, lw=1.6))

axD.set_xlim(-_lim, _lim)
axD.set_ylim(-_lim, _lim)
axD.set_aspect("equal")
axD.set_xlabel(r"$RG$  →  red")
axD.set_ylabel(r"$BY$  →  blue (unchanged)")
# Formula merged into the title so it lives above the axis frame, not on top of data.
axD.set_title(
    "D.  Cortical RG-axis gain — retinal ■ → final ◆\n"
    fr"$g$ = {G_GAIN:+.1f}     "
    fr"$RG_{{\rm final}} = (1{{+}}g)\,RG_{{\rm ret}} - g\,RG_{{\rm base}}$    (BY unchanged)",
    fontsize=10, pad=8)

h_ret2 = mpatches.Patch(facecolor=COL_RET, edgecolor=COL_RET, label="retinal ■")
h_fin = mpatches.Patch(facecolor=COL_FINAL, edgecolor=COL_FINAL, label="final ◆ (cortical-corrected)")
axD.legend(handles=[h_ret2, h_fin], loc="upper left", frameon=True,
           framealpha=0.85, fontsize=8.5)

# ============================================================ footer
fig.text(0.5, 0.015,
          "Companion: future_phase2_filter_optimization/mathematical_basis.md §10  ·  "
          "5 monochromatic test stimuli (Stockman 2-deg).",
          ha="center", fontsize=8.5, style="italic", color="#666")

fig.savefig(OUT, dpi=200, facecolor=BG)
print(f"[saved] {OUT}")
