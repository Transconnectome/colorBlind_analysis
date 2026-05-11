"""
Figure 4 — 2-Component Model: hV4 LOCO Vulnerability
=======================================================
Panel 4A: Per-subject vulnerability profile (observed vs model predictions)
Panel 4B: Model comparison — LOCO Spearman ρ at hV4 for sub-08/09
Panel 4C: Parameter landscape — 2D (β_s, β_c) grid LOCO ρ for both subjects

Data sources
------------
2-component V4 fits  : results/fits/phase_a_2component/sub-XX_V4_2component.json
2-component landscape: results/fits/phase_a_2component/sub-XX_V4_2component_landscape.json
Machado V4 fits      : results/fits/phase_a/sub-XX_V4_machado_1way.json

Key values (from data):
  sub-08 2-comp  β_s=38°  β_c=−14°  ρ=0.881  p=0.0036 **
  sub-08 Machado Δλ=1.5nm          ρ=0.619  p=0.058 NS
  sub-09 2-comp  β_s=6°   β_c=−22°  ρ=0.690  p=0.035 *
  sub-09 Machado Δλ=13.5nm         ρ=0.762  p=0.018 *  (higher ρ but only LOCO; not dual-criterion)
"""

import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
BASE = Path("/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/"
            "colorBlind_analysis/analysis/future_phase2_filter_optimization/"
            "results/fits")
OUT  = Path("/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/"
            "colorBlind_analysis/docs/PAPER/Figures/F4_twocomp")

# ── Load data ─────────────────────────────────────────────────────────────────
def load_json(path):
    with open(path) as f:
        return json.load(f)

s08_2c = load_json(BASE / "phase_a_2component" / "sub-08_V4_2component.json")
s09_2c = load_json(BASE / "phase_a_2component" / "sub-09_V4_2component.json")
s08_mc = load_json(BASE / "phase_a" / "sub-08_V4_machado_1way.json")
s09_mc = load_json(BASE / "phase_a" / "sub-09_V4_machado_1way.json")
s08_ls = load_json(BASE / "phase_a_2component" / "sub-08_V4_2component_landscape.json")
s09_ls = load_json(BASE / "phase_a_2component" / "sub-09_V4_2component_landscape.json")

# ── Colour / style ───────────────────────────────────────────────────────────
COL_08 = "#E07B2C"   # warm orange — sub-08 deutan
COL_09 = "#2D8E8B"   # teal — sub-09 protan
COL_OBS= "#222222"   # observed data

HUE_LABELS = ["R", "O", "Y", "G", "C", "B", "P", "M"]
HUE_X      = np.arange(8)

# Figure width = 180 mm = 7.087 in
FIG_W = 7.087
FIG_H = 5.0

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

# Print diagnostic
print(f"sub-08 2-comp: β_s={s08_2c['best_params'][0]}, β_c={s08_2c['best_params'][1]}, "
      f"ρ={s08_2c['best_loss']['spearman_r']:.3f}, p={s08_2c['permutation']['label_perm_p']:.4f}")
print(f"sub-09 2-comp: β_s={s09_2c['best_params'][0]}, β_c={s09_2c['best_params'][1]}, "
      f"ρ={s09_2c['best_loss']['spearman_r']:.3f}, p={s09_2c['permutation']['label_perm_p']:.4f}")
print(f"sub-08 Machado: Δλ={s08_mc['best_params'][0]}, "
      f"ρ={s08_mc['best_loss']['spearman_r']:.3f}, p={s08_mc['permutation']['label_perm_p']:.4f}")
print(f"sub-09 Machado: Δλ={s09_mc['best_params'][0]}, "
      f"ρ={s09_mc['best_loss']['spearman_r']:.3f}, p={s09_mc['permutation']['label_perm_p']:.4f}")

# ── Vulnerability arrays ─────────────────────────────────────────────────────
vuln_obs_08 = np.array(s08_2c["baseline"]["vuln_baseline"])
vuln_2c_08  = np.array(s08_2c["best_loss"]["vuln_sim"])
vuln_mc_08  = np.array(s08_mc["best_loss"]["vuln_sim"])

vuln_obs_09 = np.array(s09_2c["baseline"]["vuln_baseline"])
vuln_2c_09  = np.array(s09_2c["best_loss"]["vuln_sim"])
vuln_mc_09  = np.array(s09_mc["best_loss"]["vuln_sim"])

# ── Figure and axes layout ───────────────────────────────────────────────────
# Layout (all in figure fraction coordinates):
#   Left block  [0.06, 0.52]: panel A (two vuln profiles + vertical bar)
#   Right block [0.57, 0.97]: panel C (two landscape heat-maps, stacked)
#   Panel B sits between the two blocks [0.41, 0.53]
#
# Rows: top 0.56→0.92 (panel A + B top halves)
#        bot 0.08→0.49 (panel A + B bottom halves / panel C)
# Actually simplest: use figure-level absolute axes placement

fig = plt.figure(figsize=(FIG_W, FIG_H), dpi=300)

# Panel A axes (vulnerability profiles) — two equal columns, top zone
L_A08 = 0.065;  W_A  = 0.155;  GAP_A = 0.035
L_A09 = L_A08 + W_A + GAP_A
B_A   = 0.57;   H_A  = 0.31

ax_a08 = fig.add_axes([L_A08, B_A, W_A, H_A])
ax_a09 = fig.add_axes([L_A09, B_A, W_A, H_A])

# Panel B axes (bar chart) — between A and C, wider
L_B = L_A09 + W_A + 0.048
W_B = 0.135
ax_b = fig.add_axes([L_B, B_A, W_B, H_A])

# Panel C axes (landscapes) — right block, two rows stacked
L_C = 0.595
W_C = 0.33
H_C = 0.33
B_C_top = 0.535
B_C_bot = 0.115
GAP_CB  = 0.012   # colorbar gap

ax_c08 = fig.add_axes([L_C, B_C_top, W_C, H_C])
ax_c09 = fig.add_axes([L_C, B_C_bot, W_C, H_C])

# Colorbar axis (shared for both landscapes)
ax_cb = fig.add_axes([L_C + W_C + GAP_CB, B_C_bot, 0.013, B_C_top + H_C - B_C_bot])

# ── Panel A: Vulnerability profiles ─────────────────────────────────────────
def plot_vuln(ax, vuln_obs, vuln_2c, vuln_mc, color, subj, cvdtype,
              rho_2c, p_2c, rho_mc, p_mc):
    x = HUE_X
    ax.axhline(0, color="#aaaaaa", lw=0.5, ls=":", zorder=1)

    # Observed: filled circles + thin connecting line
    ax.plot(x, vuln_obs, "o-", color=COL_OBS, ms=3.5, lw=0.6, zorder=5,
            label="Observed", markerfacecolor=COL_OBS)

    # 2-component: solid coloured line
    ax.plot(x, vuln_2c, "-", color=color, lw=1.5, zorder=4,
            label=f"2-comp  ρ={rho_2c:.2f} {sig_label(p_2c)}")

    # Machado: dashed, lighter
    ax.plot(x, vuln_mc, "--", color=color, lw=1.0, alpha=0.55, zorder=3,
            label=f"Machado ρ={rho_mc:.2f} {sig_label(p_mc)}")

    ax.set_xticks(x)
    ax.set_xticklabels(HUE_LABELS, fontsize=7)
    ax.set_xlabel("Hue (DKL)", fontsize=7)
    ax.set_ylabel("LOCO vulnerability", fontsize=7)
    ax.set_ylim(-0.22, 0.52)
    ax.set_title(f"{subj}  ({cvdtype})", fontsize=7.5, fontweight="bold", pad=3)
    leg = ax.legend(fontsize=7.0, framealpha=0.9, edgecolor="none",
                    loc="upper right", handlelength=1.8, handletextpad=0.3,
                    borderpad=0.4)
    # Use monospace-like spacing in legend (simulate tabular look)
    ax.spines[["top", "right"]].set_visible(False)

plot_vuln(ax_a08, vuln_obs_08, vuln_2c_08, vuln_mc_08, COL_08,
          "Sub-08", "deutan",
          s08_2c["best_loss"]["spearman_r"], s08_2c["permutation"]["label_perm_p"],
          s08_mc["best_loss"]["spearman_r"],  s08_mc["permutation"]["label_perm_p"])

plot_vuln(ax_a09, vuln_obs_09, vuln_2c_09, vuln_mc_09, COL_09,
          "Sub-09", "protan",
          s09_2c["best_loss"]["spearman_r"], s09_2c["permutation"]["label_perm_p"],
          s09_mc["best_loss"]["spearman_r"],  s09_mc["permutation"]["label_perm_p"])

# ── Panel B: Model comparison ─────────────────────────────────────────────────
# Show both models for both subjects.
# IMPORTANT: for sub-09, Machado ρ=0.762 > 2-comp ρ=0.690 — plot honestly.
rho_vals = {
    "08_2c" : s08_2c["best_loss"]["spearman_r"],
    "08_mc" : s08_mc["best_loss"]["spearman_r"],
    "09_2c" : s09_2c["best_loss"]["spearman_r"],
    "09_mc" : s09_mc["best_loss"]["spearman_r"],
}
p_vals = {
    "08_2c" : s08_2c["permutation"]["label_perm_p"],
    "08_mc" : s08_mc["permutation"]["label_perm_p"],
    "09_2c" : s09_2c["permutation"]["label_perm_p"],
    "09_mc" : s09_mc["permutation"]["label_perm_p"],
}

# x positions: sub-08 group left, sub-09 group right
x_subj = np.array([0.0, 1.0])
w = 0.34

bars = {}
bars["08_2c"] = ax_b.bar(x_subj[0] - w/2, rho_vals["08_2c"], w, color=COL_08, alpha=0.9, zorder=3)
bars["08_mc"] = ax_b.bar(x_subj[0] + w/2, rho_vals["08_mc"], w, color=COL_08, alpha=0.42,
                          hatch="//", edgecolor=COL_08, lw=0.5, zorder=3)
bars["09_2c"] = ax_b.bar(x_subj[1] - w/2, rho_vals["09_2c"], w, color=COL_09, alpha=0.9, zorder=3)
bars["09_mc"] = ax_b.bar(x_subj[1] + w/2, rho_vals["09_mc"], w, color=COL_09, alpha=0.42,
                          hatch="//", edgecolor=COL_09, lw=0.5, zorder=3)

def bar_annot(ax, bar, p, color):
    h = max(bar.get_height(), 0)
    lbl = sig_label(p)
    fs = 7.0
    ax.text(bar.get_x() + bar.get_width()/2, h + 0.018, lbl,
            ha="center", va="bottom", fontsize=fs, color=color, fontweight="bold")

bar_annot(ax_b, bars["08_2c"][0], p_vals["08_2c"], COL_08)
bar_annot(ax_b, bars["08_mc"][0],  p_vals["08_mc"], COL_08)
bar_annot(ax_b, bars["09_2c"][0], p_vals["09_2c"], COL_09)
bar_annot(ax_b, bars["09_mc"][0],  p_vals["09_mc"], COL_09)

ax_b.set_xticks(x_subj)
ax_b.set_xticklabels(["Sub-08\n(deutan)", "Sub-09\n(protan)"], fontsize=7)
ax_b.set_ylabel("Spearman ρ  (hV4 LOCO)", fontsize=7)
ax_b.set_ylim(0, 1.10)
ax_b.set_title("Model fit (hV4)", fontsize=7.5, fontweight="bold", pad=3)
ax_b.axhline(0, color="gray", lw=0.4)
ax_b.spines[["top", "right"]].set_visible(False)

# Legend: solid = 2-component, hatched = Machado
from matplotlib.patches import Patch
leg_handles = [
    Patch(facecolor="#888888", alpha=0.9,  label="2-component"),
    Patch(facecolor="#888888", alpha=0.42, hatch="//",
          edgecolor="#888888", lw=0.5,     label="Machado"),
]
ax_b.legend(handles=leg_handles, fontsize=7.0, framealpha=0.9,
            edgecolor="none", loc="lower right", handlelength=1.2,
            borderpad=0.4, handletextpad=0.4)

# Footnote: 2-comp is dual-criterion validated (bump to 6pt minimum)
ax_b.annotate("†2-comp: dual-criterion\n (LOCO + pre-image exact)",
              xy=(0.03, 0.02), xycoords="axes fraction",
              fontsize=7.0, color="#555555", va="bottom")

# ── Panel C: Parameter landscapes ───────────────────────────────────────────
VMIN, VMAX = -0.5, 0.90
CMAP = "RdBu_r"

def plot_landscape(ax, bs, bc, rho_grid, best_bs, best_bc, best_rho, best_p,
                   color, subj, cvdtype):
    im = ax.pcolormesh(bs, bc, rho_grid,
                        cmap=CMAP, vmin=VMIN, vmax=VMAX,
                        shading="nearest", rasterized=True)
    # Optimal point star
    ax.plot(best_bs, best_bc, "*", color="white", ms=8, zorder=10,
            markeredgecolor="black", markeredgewidth=0.5)
    # Position label — always to the right of star for left-zone points,
    # to the left for right-zone points. Shift up if near bc limits.
    lbl_ha  = "left"  if best_bs < 35 else "right"
    lbl_x   = best_bs + 2 if lbl_ha == "left" else best_bs - 2
    # If near the top bc boundary, put label below
    bc_max = max(bc)
    lbl_va  = "bottom" if best_bc < bc_max - 10 else "top"
    lbl_dy  = 2.5 if lbl_va == "bottom" else -2.5
    ax.text(lbl_x, best_bc + lbl_dy,
            f"β_s={best_bs:.0f}°, β_c={best_bc:.0f}°\nρ={best_rho:.2f} {sig_label(best_p)}",
            fontsize=7.0, color="white", va=lbl_va, ha=lbl_ha, zorder=11,
            bbox=dict(boxstyle="round,pad=0.2", facecolor="black", alpha=0.55, lw=0))
    ax.set_xlabel("β_s — S-cone shift (°)", fontsize=7)
    ax.set_ylabel("β_c — cortical rot. (°)", fontsize=7)
    ax.set_title(f"{subj}  ({cvdtype})", fontsize=7, fontweight="bold", pad=2)
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

# Shared colorbar
cb = fig.colorbar(im09, cax=ax_cb, extend="min")
cb.set_label("Spearman ρ", fontsize=7, labelpad=4)
cb.ax.tick_params(labelsize=7)
cb.set_ticks([-0.4, -0.2, 0.0, 0.2, 0.4, 0.6, 0.8])

# ── Panel letters ─────────────────────────────────────────────────────────────
letter_kw = dict(fontsize=10, fontweight="bold", va="top", ha="left",
                 transform=fig.transFigure)
# A: above the vulnerability profiles block
fig.text(0.03, 0.948, "A", **letter_kw)
# B: above the bar panel
fig.text(L_B - 0.01, 0.948, "B", **letter_kw)
# C: above the landscapes block
fig.text(L_C - 0.025, 0.948, "C", **letter_kw)

# ── Save ──────────────────────────────────────────────────────────────────────
fig.savefig(OUT / "fig4_output.png", dpi=300, bbox_inches="tight",
            facecolor="white")
fig.savefig(OUT / "fig4_output.pdf", bbox_inches="tight",
            facecolor="white")
print(f"\nSaved:\n  {OUT}/fig4_output.png\n  {OUT}/fig4_output.pdf")
plt.close()
