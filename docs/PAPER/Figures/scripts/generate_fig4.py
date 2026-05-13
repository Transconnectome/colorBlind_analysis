"""
Figure 4 — 2-Component Model: hV4 LOCO Vulnerability
=======================================================
Panel 4A: Per-subject vulnerability profile (observed vs 2-component prediction)
Panel 4B: Spearman ρ summary bar chart (2-component only, both subjects)
Panel 4C: Parameter landscape — 2D (β_s, β_c) grid LOCO ρ for both subjects

Layout (2-column × 2-row grid, with Panel B as top-left narrow strip):
  [top strip, left ]  Panel B — bar chart (sub-08 & sub-09 ρ summary)
  [row 1,     left ]  Panel A sub-08 — vulnerability profile
  [row 1,     right]  Panel C sub-08 — parameter landscape
  [row 2,     left ]  Panel A sub-09 — vulnerability profile
  [row 2,     right]  Panel C sub-09 — parameter landscape

Data sources
------------
2-component V4 fits  : results/fits/phase_a_2component/sub-XX_V4_2component.json
2-component landscape: results/fits/phase_a_2component/sub-XX_V4_2component_landscape.json

Key values (from data):
  sub-08 2-comp  β_s=38°  β_c=−14°  ρ=0.881  p=0.0036 **
  sub-09 2-comp  β_s=6°   β_c=−22°  ρ=0.690  p=0.035  *
"""

import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
BASE = Path("/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/"
            "colorBlind_analysis/analysis/future_phase2_filter_optimization/"
            "results/fits")
OUT  = Path("/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/"
            "colorBlind_analysis/docs/PAPER/Figures")

# ── Load data (2-component only) ─────────────────────────────────────────────
def load_json(path):
    with open(path) as f:
        return json.load(f)

s08_2c = load_json(BASE / "phase_a_2component" / "sub-08_V4_2component.json")
s09_2c = load_json(BASE / "phase_a_2component" / "sub-09_V4_2component.json")
s08_ls = load_json(BASE / "phase_a_2component" / "sub-08_V4_2component_landscape.json")
s09_ls = load_json(BASE / "phase_a_2component" / "sub-09_V4_2component_landscape.json")
# NOTE: Machado fits moved to Appendix A (2026-05-12) — no longer loaded here.

# ── Print diagnostics ─────────────────────────────────────────────────────────
print(f"sub-08 2-comp: β_s={s08_2c['best_params'][0]}, β_c={s08_2c['best_params'][1]}, "
      f"ρ={s08_2c['best_loss']['spearman_r']:.3f}, p={s08_2c['permutation']['label_perm_p']:.4f}")
print(f"sub-09 2-comp: β_s={s09_2c['best_params'][0]}, β_c={s09_2c['best_params'][1]}, "
      f"ρ={s09_2c['best_loss']['spearman_r']:.3f}, p={s09_2c['permutation']['label_perm_p']:.4f}")

# ── Colour / style ───────────────────────────────────────────────────────────
COL_08 = "#E07B2C"   # warm orange — sub-08 deutan
COL_09 = "#2D8E8B"   # teal — sub-09 protan
COL_OBS= "#222222"   # observed data

HUE_LABELS = ["R", "O", "Y", "G", "C", "B", "P", "M"]
HUE_X      = np.arange(8)

# Figure width = 180 mm = 7.087 in; height increased to accommodate 3 logical rows
FIG_W = 7.087
FIG_H = 7.0   # taller to give clear separation between Panel B and Panel A rows

matplotlib.rcParams.update({
    "font.family"      : "sans-serif",
    "font.sans-serif"  : ["Helvetica", "Arial", "DejaVu Sans"],
    "font.size"        : 7,
    "axes.titlesize"   : 7.5,
    "axes.labelsize"   : 7,
    "xtick.labelsize"  : 7,
    "ytick.labelsize"  : 7,
    "legend.fontsize"  : 7,
    "axes.linewidth"   : 0.6,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "xtick.major.size" : 2.5,
    "ytick.major.size" : 2.5,
    "lines.linewidth"  : 1.0,
    "pdf.fonttype"     : 42,
    "ps.fonttype"      : 42,
})

# ── Helpers ───────────────────────────────────────────────────────────────────
def sig_label(p):
    if p < 0.01:  return "**"
    if p < 0.05:  return "*"
    return "n.s."

def build_landscape_grid(landscape):
    """Return (bs_vals, bc_vals, rho_grid[bc,bs]) from flat landscape list."""
    bs_all = sorted(set(e["params"][0] for e in landscape))
    bc_all = sorted(set(e["params"][1] for e in landscape))
    rho    = np.full((len(bc_all), len(bs_all)), np.nan)
    bs_idx = {v: i for i, v in enumerate(bs_all)}
    bc_idx = {v: i for i, v in enumerate(bc_all)}
    for e in landscape:
        bs, bc = e["params"]
        rho[bc_idx[bc], bs_idx[bs]] = e["spearman_r"]
    return np.array(bs_all), np.array(bc_all), rho

bs08, bc08, rho08 = build_landscape_grid(s08_ls)
bs09, bc09, rho09 = build_landscape_grid(s09_ls)

# ── Vulnerability arrays ─────────────────────────────────────────────────────
vuln_obs_08 = np.array(s08_2c["baseline"]["vuln_baseline"])
vuln_2c_08  = np.array(s08_2c["best_loss"]["vuln_sim"])

vuln_obs_09 = np.array(s09_2c["baseline"]["vuln_baseline"])
vuln_2c_09  = np.array(s09_2c["best_loss"]["vuln_sim"])

# ── Figure layout ─────────────────────────────────────────────────────────────
# All coordinates are in figure fraction [0, 1].
#
# Horizontal zones:
#   Left  (A/B panels): left=0.07,  width=0.33,  right=0.40
#   Gap                                            = 0.06
#   Right (C panels):   left=0.46,  width=0.44,  right=0.90
#   Colorbar:           left=0.915, width=0.016
#
# Vertical zones (bottom to top):
#   Row 2 (sub-09):  bottom=0.055, height=0.28
#   Gap                                           = 0.045
#   Row 1 (sub-08):  bottom=0.380, height=0.28
#   Gap                                           = 0.065
#   Panel B strip:   bottom=0.745, height=0.155

fig = plt.figure(figsize=(FIG_W, FIG_H), dpi=300)

# Coordinates
L_A  = 0.07;   W_A  = 0.33
L_C  = 0.46;   W_C  = 0.44
L_CB = 0.915;  W_CB = 0.016

H_AB_ROW = 0.27   # height of A/C subject rows
H_B      = 0.150  # height of Panel B strip — taller so tick labels fit

B_R2 = 0.050                           # sub-09 row bottom
B_R1 = B_R2 + H_AB_ROW + 0.070        # sub-08 row bottom = 0.39  (wider gap for row titles)
B_B  = B_R1  + H_AB_ROW + 0.075       # Panel B bottom = 0.735

# Row 1 — sub-08
ax_a08 = fig.add_axes([L_A,  B_R1, W_A,  H_AB_ROW])
ax_c08 = fig.add_axes([L_C,  B_R1, W_C,  H_AB_ROW])

# Row 2 — sub-09
ax_a09 = fig.add_axes([L_A,  B_R2, W_A,  H_AB_ROW])
ax_c09 = fig.add_axes([L_C,  B_R2, W_C,  H_AB_ROW])

# Shared colorbar spanning both C rows
CB_bottom = B_R2
CB_top    = B_R1 + H_AB_ROW
ax_cb = fig.add_axes([L_CB, CB_bottom, W_CB, CB_top - CB_bottom])

# Panel B — top strip, spans full content width to fill right-upper void
W_B  = L_CB - L_A - 0.01   # 0.915 - 0.07 - 0.01 = 0.835
ax_b = fig.add_axes([L_A,  B_B, W_B,  H_B])

# ── Panel A: Vulnerability profiles (2-component only) ─────────────────────
def plot_vuln(ax, vuln_obs, vuln_2c, color, subj, cvdtype, rho_2c, p_2c):
    x = HUE_X
    ax.axhline(0, color="#aaaaaa", lw=0.5, ls=":", zorder=1)

    # Observed
    ax.plot(x, vuln_obs, "o-", color=COL_OBS, ms=3.5, lw=0.6, zorder=5,
            label="Observed", markerfacecolor=COL_OBS)
    # 2-component: solid coloured line
    ax.plot(x, vuln_2c, "-", color=color, lw=1.8, zorder=4,
            label=f"2-comp  ρ={rho_2c:.2f} {sig_label(p_2c)}")

    ax.set_xticks(x)
    ax.set_xticklabels(HUE_LABELS, fontsize=7)
    ax.set_xlabel("Hue (DKL)", fontsize=7)
    ax.set_ylabel("LOCO vulnerability", fontsize=7)
    ax.set_ylim(-0.22, 0.52)
    ax.set_title(f"{subj}  ({cvdtype})", fontsize=7.5, fontweight="bold", pad=3)
    ax.legend(fontsize=6.0, framealpha=0.85, edgecolor="none",
              loc="upper right", handlelength=1.2, handletextpad=0.25,
              borderpad=0.3, labelspacing=0.3, borderaxespad=0.3)
    ax.spines[["top", "right"]].set_visible(False)

plot_vuln(ax_a08, vuln_obs_08, vuln_2c_08, COL_08, "Sub-08", "deutan",
          s08_2c["best_loss"]["spearman_r"],
          s08_2c["permutation"]["label_perm_p"])

plot_vuln(ax_a09, vuln_obs_09, vuln_2c_09, COL_09, "Sub-09", "protan",
          s09_2c["best_loss"]["spearman_r"],
          s09_2c["permutation"]["label_perm_p"])

# ── Panel B: 2-component Spearman ρ summary with null reference ─────────────
rho_2c_08 = s08_2c["best_loss"]["spearman_r"]
rho_2c_09 = s09_2c["best_loss"]["spearman_r"]
p_2c_08   = s08_2c["permutation"]["label_perm_p"]
p_2c_09   = s09_2c["permutation"]["label_perm_p"]

# Null distribution (chance band) — mean ± 2σ of label-permutation rho
null_mean_08 = s08_2c["permutation"]["null_rho_mean"]
null_std_08  = s08_2c["permutation"]["null_rho_std"]
null_mean_09 = s09_2c["permutation"]["null_rho_mean"]
null_std_09  = s09_2c["permutation"]["null_rho_std"]

x_subj = np.array([1.0, 2.2])
w = 0.55

bar_08 = ax_b.bar(x_subj[0], rho_2c_08, w, color=COL_08, alpha=0.95, zorder=3,
                   edgecolor="white", linewidth=0.5)
bar_09 = ax_b.bar(x_subj[1], rho_2c_09, w, color=COL_09, alpha=0.95, zorder=3,
                   edgecolor="white", linewidth=0.5)

def bar_annot(ax, bar, p, color, fs=8.0):
    h = max(bar.get_height(), 0)
    ax.text(bar.get_x() + bar.get_width()/2, h + 0.02, sig_label(p),
            ha="center", va="bottom", fontsize=fs, color=color, fontweight="bold")

bar_annot(ax_b, bar_08[0], p_2c_08, COL_08)
bar_annot(ax_b, bar_09[0], p_2c_09, COL_09)

# Chance band — gray shaded zone at null distribution per subject (no text label)
for sx, nmean, nstd in [(x_subj[0], null_mean_08, null_std_08),
                          (x_subj[1], null_mean_09, null_std_09)]:
    ax_b.fill_between([sx - w/2 - 0.05, sx + w/2 + 0.05],
                       nmean - 2*nstd, nmean + 2*nstd,
                       color="#bbbbbb", alpha=0.30, zorder=1,
                       edgecolor="none")

# Theoretical ceiling line (no text label)
ax_b.axhline(1.0, color="#888", lw=0.6, ls=":", zorder=2)

ax_b.set_xlim(0.3, 2.9)
ax_b.set_xticks(x_subj)
ax_b.set_xticklabels(["Sub-08 (deutan)", "Sub-09 (protan)"], fontsize=7)
ax_b.tick_params(axis='x', pad=2)
ax_b.set_ylabel("Spearman ρ\n(hV4 LOCO)", fontsize=7)
ax_b.set_ylim(-0.15, 1.20)
ax_b.set_title("2-component model fit (hV4)",
                fontsize=7.5, fontweight="bold", pad=3)
ax_b.axhline(0, color="gray", lw=0.4)
ax_b.spines[["top", "right"]].set_visible(False)

# ── Panel C: Parameter landscapes ────────────────────────────────────────────
VMIN, VMAX = -0.5, 0.90
CMAP = "RdBu_r"

def plot_landscape(ax, bs, bc, rho_grid, best_bs, best_bc, best_rho, best_p,
                   color, subj, cvdtype):
    im = ax.pcolormesh(bs, bc, rho_grid,
                        cmap=CMAP, vmin=VMIN, vmax=VMAX,
                        shading="nearest", rasterized=True)
    # Optimal point star
    ax.plot(best_bs, best_bc, "*", color="white", ms=9, zorder=10,
            markeredgecolor="black", markeredgewidth=0.5)

    # Label box — adaptive horizontal placement to avoid left/right edges
    lbl_ha  = "left"  if best_bs < np.median(bs) else "right"
    lbl_x   = best_bs + 1.5 if lbl_ha == "left" else best_bs - 1.5
    # Adaptive vertical: near top → put label below; near bottom → above
    bc_mid  = np.median(bc)
    lbl_va  = "bottom" if best_bc < bc_mid else "top"
    lbl_dy  = 2.0 if lbl_va == "bottom" else -2.0

    ax.text(lbl_x, best_bc + lbl_dy,
            f"β_s={best_bs:.0f}°, β_c={best_bc:.0f}°\nρ={best_rho:.2f} {sig_label(best_p)}",
            fontsize=7.0, color="white", va=lbl_va, ha=lbl_ha, zorder=11,
            bbox=dict(boxstyle="round,pad=0.2", facecolor="black", alpha=0.55, lw=0))
    ax.set_xlabel("β_s — S-cone shift (°)", fontsize=7)
    ax.set_ylabel("β_c — cortical rot. (°)", fontsize=7)
    ax.set_title(f"{subj}  ({cvdtype})", fontsize=7.5, fontweight="bold", pad=3)
    ax.spines[["top", "right"]].set_visible(False)
    return im

im08 = plot_landscape(ax_c08, bs08, bc08, rho08,
                      s08_2c["best_params"][0], s08_2c["best_params"][1],
                      s08_2c["best_loss"]["spearman_r"],
                      s08_2c["permutation"]["label_perm_p"],
                      COL_08, "Sub-08", "deutan")

im09 = plot_landscape(ax_c09, bs09, bc09, rho09,
                      s09_2c["best_params"][0], s09_2c["best_params"][1],
                      s09_2c["best_loss"]["spearman_r"],
                      s09_2c["permutation"]["label_perm_p"],
                      COL_09, "Sub-09", "protan")

# Shared colorbar — spans both C rows
cb = fig.colorbar(im09, cax=ax_cb, extend="min")
cb.set_label("Spearman ρ", fontsize=7, labelpad=4)
cb.ax.tick_params(labelsize=7)
cb.set_ticks([-0.4, -0.2, 0.0, 0.2, 0.4, 0.6, 0.8])

# ── Panel letters ─────────────────────────────────────────────────────────────
letter_kw = dict(fontsize=10, fontweight="bold", va="top", ha="left",
                 transform=fig.transFigure)

# B: above the bar strip (top-left)
fig.text(L_A - 0.025, B_B + H_B + 0.025, "B", **letter_kw)

# A: above sub-08 row in the left column
fig.text(L_A - 0.025, B_R1 + H_AB_ROW + 0.025, "A", **letter_kw)

# C: above sub-08 row in the right column
fig.text(L_C - 0.02, B_R1 + H_AB_ROW + 0.025, "C", **letter_kw)

# ── Save ──────────────────────────────────────────────────────────────────────
fig.savefig(OUT / "fig4_twocomp.png", dpi=300, bbox_inches="tight",
            facecolor="white")
fig.savefig(OUT / "fig4_twocomp.pdf", bbox_inches="tight",
            facecolor="white")
print(f"\nSaved:\n  {OUT}/fig4_twocomp.png\n  {OUT}/fig4_twocomp.pdf")
plt.close()
