"""
Figure 4 — Option C loss landscape only (per CURRENT BEST, SUMMARY.md 2026-05-13)
================================================================================
Two landscape panels (sub-08 left, sub-09 right) of the Option C loss

    L_C(β_s, β_c) = 0.3·L_topk(V4) + 0.3·L_mse(V4) + 0.3·L_rdmV1(SRM) + 3.0·Tikh

Argmins (white ★):
  sub-08 deutan: (β_s, β_c) = (40°, +26°)
  sub-09 protan: (β_s, β_c) = (12°, −28°)

Data source: results/axis_3way/sub-{08,09}_V4_Stockman{150,16}_landscape.json
            + results/CANDIDATE/tier2_v4ccc_srm_rdm/*_landscape.json
loaded through analysis/phase5_filter_optimization/scripts/p2amax_neural_only_loss.load_neural_grids.
"""

import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT = Path("/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/"
            "colorBlind_analysis")
SCRIPTS = ROOT / "analysis/phase5_filter_optimization/scripts"
OUT     = ROOT / "docs/PAPER/Figures"

sys.path.insert(0, str(SCRIPTS))
from p2amax_neural_only_loss import load_neural_grids  # noqa: E402

# ── Option C BEST parameters (from results/SUMMARY.md, 2026-05-13) ───────────
BEST = {
    "08": dict(bs=40.0, bc=+26.0, family="deutan", axis=150.0, color="#E07B2C"),
    "09": dict(bs=12.0, bc=-28.0, family="protan", axis=16.0,  color="#2D8E8B"),
}
LOSS_FORMULA = r"$L_C = 0.3\,L_\mathrm{topk} + 0.3\,L_\mathrm{mse}"\
               r" + 0.3\,L_\mathrm{rdmV1} + 3.0\,L_\mathrm{Tikh}$"

# ── Build Option C landscape from cached neural grids ────────────────────────
def option_c_landscape(sid):
    g = load_neural_grids(sid)

    def _safe(x):
        return np.where(np.isnan(x), 1e6, x)

    L = (0.3 * _safe(g["L_topk"])
       + 0.3 * _safe(g["L_mse"])
       + 0.3 * _safe(g["L_rdm_V1"])
       + 3.0 * _safe(g["L_tikh"]))
    L[L > 100] = np.nan
    bs_grid = np.asarray(g["bs_grid"], dtype=float)
    bc_grid = np.asarray(g["bc_grid"], dtype=float)
    # Verify argmin matches the published BEST
    idx = np.unravel_index(np.nanargmin(L), L.shape)
    bs_arg = float(bs_grid[idx[0]])
    bc_arg = float(bc_grid[idx[1]])
    Lmin   = float(L[idx])
    return bs_grid, bc_grid, L, bs_arg, bc_arg, Lmin

# ── Style ────────────────────────────────────────────────────────────────────
matplotlib.rcParams.update({
    "font.family"      : "sans-serif",
    "font.sans-serif"  : ["Helvetica", "Arial", "DejaVu Sans"],
    "font.size"        : 7,
    "axes.titlesize"   : 8,
    "axes.labelsize"   : 7.5,
    "xtick.labelsize"  : 7,
    "ytick.labelsize"  : 7,
    "legend.fontsize"  : 7,
    "axes.linewidth"   : 0.6,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "xtick.major.size" : 2.5,
    "ytick.major.size" : 2.5,
    "pdf.fonttype"     : 42,
    "ps.fonttype"      : 42,
})

# ── Figure (1 row × 2 columns; shared colorbar on the right) ─────────────────
FIG_W = 7.087           # ~ apa6 \textwidth in inches
FIG_H = 3.6

fig = plt.figure(figsize=(FIG_W, FIG_H), dpi=300)

L_M = 0.085;  PANEL_W = 0.36
L_L = L_M
L_R = L_M + PANEL_W + 0.08
B   = 0.16
H   = 0.74

L_CB = L_R + PANEL_W + 0.025;  W_CB = 0.016
ax_l = fig.add_axes([L_L, B, PANEL_W, H])
ax_r = fig.add_axes([L_R, B, PANEL_W, H])
ax_cb = fig.add_axes([L_CB, B, W_CB, H])

# ── Compute landscapes once; share vmin/vmax across both panels ──────────────
data = {}
all_vals = []
for sid in ("08", "09"):
    bs_g, bc_g, L_C, bs_arg, bc_arg, Lmin = option_c_landscape(sid)
    data[sid] = dict(bs=bs_g, bc=bc_g, L=L_C,
                     bs_arg=bs_arg, bc_arg=bc_arg, Lmin=Lmin)
    all_vals.append(L_C[np.isfinite(L_C)])
    # Sanity check: assert argmin matches BEST table
    bsB, bcB = BEST[sid]["bs"], BEST[sid]["bc"]
    if abs(bs_arg - bsB) > 0.5 or abs(bc_arg - bcB) > 0.5:
        print(f"WARN sub-{sid}: cached argmin ({bs_arg:.1f},{bc_arg:+.1f}) "
              f"differs from BEST table ({bsB:.0f},{bcB:+.0f})")

vals = np.concatenate(all_vals)
vmin, vmax = np.percentile(vals, [2, 98])

# ── Panel renderer ──────────────────────────────────────────────────────────
def render(ax, d, sid, info):
    # pcolormesh wants the grid indexed as L[i_bs, j_bc] -> (X=bc, Y=bs)
    pcm = ax.pcolormesh(d["bc"], d["bs"], d["L"],
                        cmap="viridis_r",
                        vmin=vmin, vmax=vmax,
                        shading="nearest", rasterized=True)
    ax.plot(d["bc_arg"], d["bs_arg"], marker="*", markersize=14,
            color="white", markeredgecolor="black", markeredgewidth=0.7,
            zorder=10, linestyle="none")
    # Inline label of the argmin parameters
    txt = (fr"$\hat\beta_s={d['bs_arg']:.0f}°,\ \hat\beta_c={d['bc_arg']:+.0f}°$"
           "\n"
           fr"$\|\hat\beta\|={np.hypot(d['bs_arg'], d['bc_arg']):.1f}°$"
           "\n"
           fr"$L_C={d['Lmin']:.3f}$")
    # place label opposite to the argmin so it doesn't overlap
    bc_med = 0.0
    bs_med = float(np.median(d["bs"]))
    ha = "left" if d["bc_arg"] < bc_med else "right"
    va = "bottom" if d["bs_arg"] < bs_med else "top"
    dx =  6 if ha == "left" else -6
    dy =  6 if va == "bottom" else -6
    ax.annotate(txt,
                xy=(d["bc_arg"], d["bs_arg"]),
                xytext=(dx, dy), textcoords="offset points",
                ha=ha, va=va, fontsize=6.8, color="white", fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.25",
                          facecolor="black", edgecolor="white",
                          alpha=0.65, lw=0.4))
    ax.set_xlabel(r"$\beta_c$ — cortical rot. (°)")
    ax.set_ylabel(r"$\beta_s$ — S-cone shift (°)")
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_title(f"Sub-{sid} ({info['family']}, axis {info['axis']:.0f}°)",
                 color=info["color"], pad=4)
    return pcm

pcm = render(ax_l, data["08"], "08", BEST["08"])
_   = render(ax_r, data["09"], "09", BEST["09"])

cb = fig.colorbar(pcm, cax=ax_cb)
cb.set_label(LOSS_FORMULA, fontsize=6.7, labelpad=4)
cb.ax.tick_params(labelsize=6.5)

# ── Save ─────────────────────────────────────────────────────────────────────
fig.savefig(OUT / "fig4_twocomp.png", dpi=300, bbox_inches="tight",
            facecolor="white")
fig.savefig(OUT / "fig4_twocomp.pdf", bbox_inches="tight",
            facecolor="white")
print(f"Saved:\n  {OUT}/fig4_twocomp.png\n  {OUT}/fig4_twocomp.pdf")
plt.close(fig)
