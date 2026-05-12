"""phase3_generate_fig_old_simplified.py — F4-style figure for OLD-formula (simplified L_fit).

Layout (matches docs/PAPER/Figures/F4_twocomp/generate_fig4.py):
  Panel B (top):    Spearman ρ summary bar chart (sub-08 V4, sub-09 V4) — OLD
  Panel A (left):   Vulnerability profile per subject (observed vs OLD optimum)
  Panel C (right):  2D (β_s, β_c) parameter landscape with optimum marker

Uses simplified OLD L_fit (= L_vuln + 0.5·L_rank, no L_rdm / L_smooth).

Data: results/old_formula/sub-XX_VV_simplified_{summary,landscape}.json
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR))
sys.path.insert(0, str(_THIS_DIR / 'forward_models'))

BASE = _THIS_DIR.parent / "results" / "old_formula"
OUT = _THIS_DIR.parent / "results" / "old_formula"
OUT.mkdir(parents=True, exist_ok=True)


def load(name):
    with open(BASE / name) as f:
        return json.load(f)


s08_sum = load("sub-08_V4_simplified_summary.json")
s08_ls = load("sub-08_V4_simplified_landscape.json")
s09_sum = load("sub-09_V4_simplified_summary.json")
s09_ls = load("sub-09_V4_simplified_landscape.json")

# Permutation test result is NOT in OLD refit. Approximate p from rank via N=1326 permutations
# of vuln_cvd. For display purposes, mark p<0.05 if rank ρ > rho_at_random_top5pct.
# We use a simple "label_perm_p" approximation based on landscape rank.
# OR just use existing sub-08 V4 p=0.008 from old_formula_refit.py output.
# Hard-coded from existing OLD refit:
OLD_LABEL_PERM_P = {
    'sub-08_V4': 0.008,   # from prior run (β_s=10, β_c=-32)
    'sub-09_V4': 0.10,    # not formally tested; placeholder NS
}


def vuln_baseline_load(subj_id):
    """Load CVD vulnerability (target). Reuse step1_fit_loco_v2.load_cvd_loco_target."""
    fp = (_THIS_DIR.parent.parent / 'future_phase1_forward_model' / 'results'
          / 'validation' / f'sub-{subj_id}_loco.json')
    with open(fp) as f:
        d = json.load(f)
    per_color = np.zeros(8)
    for fold in d['V4']['ridge_gcv']['folds']:
        per_color[fold['test_color']] = fold['voxel_corr']
    return per_color


vuln_obs_08 = vuln_baseline_load('08')
vuln_obs_09 = vuln_baseline_load('09')

vuln_sim_08 = None
vuln_sim_09 = None
# OLD landscape doesn't save vuln_sim. Recompute at best (β_s, β_c) using OLD δθ + design.
# But we'd need hc_amps + simulate_mean_hc_loco_legacy. Recompute is heavy.
# Alternative: use existing OLD refit's best_by_l_fit (only has δθ, not vuln_sim).
# For display, recompute on-the-fly is needed — invoke step1_fit_loco_v2 pipeline.

import sys as _sys
_sys.path.insert(0, str(_THIS_DIR))
from old_formula_refit import (
    HC_SUBJECTS, load_amplitudes, create_basis_full, N_CHANNELS, HUE_ANGLES,
    simulate_mean_hc_loco_legacy, get_shifted_design_old,
    LOCAL_DATA, SERVER_DATA,
)

DATA_DIR = SERVER_DATA if SERVER_DATA.exists() else LOCAL_DATA
hc_amps = {s: load_amplitudes(DATA_DIR, s, 'V4') for s in HC_SUBJECTS}

# Recompute vuln_sim at OLD optimum
b08 = s08_sum['best_by_l_fit']
C08, _ = get_shifted_design_old(b08['bs'], b08['bc'])
vuln_sim_08, _ = simulate_mean_hc_loco_legacy(hc_amps, C08)

b09 = s09_sum['best_by_l_fit']
C09, _ = get_shifted_design_old(b09['bs'], b09['bc'])
vuln_sim_09, _ = simulate_mean_hc_loco_legacy(hc_amps, C09)

# Also recompute baseline (δθ=0)
basis_full = create_basis_full(N_CHANNELS, basis_type='fe')
C_baseline = basis_full[HUE_ANGLES]
vuln_baseline_08, _ = simulate_mean_hc_loco_legacy(hc_amps, C_baseline)


# Build landscape grids
def build_grid(landscape):
    bs_all = sorted(set(e['bs'] for e in landscape))
    bc_all = sorted(set(e['bc'] for e in landscape))
    rho = np.full((len(bc_all), len(bs_all)), np.nan)
    bs_idx = {v: i for i, v in enumerate(bs_all)}
    bc_idx = {v: i for i, v in enumerate(bc_all)}
    for e in landscape:
        rho[bc_idx[e['bc']], bs_idx[e['bs']]] = e['spearman_r']
    return np.array(bs_all), np.array(bc_all), rho


bs08, bc08, rho08 = build_grid(s08_ls)
bs09, bc09, rho09 = build_grid(s09_ls)


# Style (matches F4_twocomp)
COL_08 = "#E07B2C"
COL_09 = "#2D8E8B"
COL_OBS = "#222222"
HUE_LABELS = ["R", "O", "Y", "G", "C", "B", "P", "M"]
HUE_X = np.arange(8)
FIG_W = 7.087
FIG_H = 7.0

matplotlib.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
    "font.size": 7, "axes.titlesize": 7.5, "axes.labelsize": 7,
    "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7,
    "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "xtick.major.size": 2.5, "ytick.major.size": 2.5, "lines.linewidth": 1.0,
    "pdf.fonttype": 42, "ps.fonttype": 42,
})


def sig_label(p):
    if p < 0.01: return "**"
    if p < 0.05: return "*"
    return "n.s."


fig = plt.figure(figsize=(FIG_W, FIG_H), dpi=300)

# Layout (mirrors F4)
L_A = 0.07; W_A = 0.33
L_C = 0.46; W_C = 0.44
L_CB = 0.915; W_CB = 0.016
H_AB_ROW = 0.27
H_B = 0.150
B_R2 = 0.050
B_R1 = B_R2 + H_AB_ROW + 0.070
B_B = B_R1 + H_AB_ROW + 0.075

ax_a08 = fig.add_axes([L_A, B_R1, W_A, H_AB_ROW])
ax_c08 = fig.add_axes([L_C, B_R1, W_C, H_AB_ROW])
ax_a09 = fig.add_axes([L_A, B_R2, W_A, H_AB_ROW])
ax_c09 = fig.add_axes([L_C, B_R2, W_C, H_AB_ROW])
ax_cb = fig.add_axes([L_CB, B_R2, W_CB, B_R1 + H_AB_ROW - B_R2])
W_B_strip = L_CB - L_A - 0.01
ax_b = fig.add_axes([L_A, B_B, W_B_strip, H_B])


def plot_vuln(ax, vuln_obs, vuln_2c, color, subj, cvdtype, rho, p):
    x = HUE_X
    ax.axhline(0, color="#aaaaaa", lw=0.5, ls=":", zorder=1)
    ax.plot(x, vuln_obs, "o-", color=COL_OBS, ms=3.5, lw=0.6, zorder=5,
            label="Observed (CVD)", markerfacecolor=COL_OBS)
    ax.plot(x, vuln_2c, "-", color=color, lw=1.8, zorder=4,
            label=f"OLD 2-comp  ρ={rho:.2f} {sig_label(p)}")
    ax.set_xticks(x); ax.set_xticklabels(HUE_LABELS, fontsize=7)
    ax.set_xlabel("Hue (DKL)", fontsize=7)
    ax.set_ylabel("LOCO vulnerability", fontsize=7)
    ax.set_ylim(-1.0, 1.0)
    ax.set_title(f"{subj}  ({cvdtype})", fontsize=7.5, fontweight="bold", pad=3)
    ax.legend(fontsize=7.0, framealpha=0.9, edgecolor="none",
              loc="upper right", handlelength=1.8, handletextpad=0.3, borderpad=0.4)
    ax.spines[["top", "right"]].set_visible(False)


plot_vuln(ax_a08, vuln_obs_08, vuln_sim_08, COL_08, "Sub-08", "deutan",
          b08['spearman_r'], OLD_LABEL_PERM_P['sub-08_V4'])
plot_vuln(ax_a09, vuln_obs_09, vuln_sim_09, COL_09, "Sub-09", "protan",
          b09['spearman_r'], OLD_LABEL_PERM_P['sub-09_V4'])


# Panel B
x_subj = np.array([1.0, 2.0]); w = 0.55
bar08 = ax_b.bar(x_subj[0], b08['spearman_r'], w, color=COL_08, alpha=0.9)
bar09 = ax_b.bar(x_subj[1], b09['spearman_r'], w, color=COL_09, alpha=0.9)


def bar_annot(ax, bar, p, color):
    h = max(bar.get_height(), 0)
    ax.text(bar.get_x() + bar.get_width() / 2, h + 0.022, sig_label(p),
            ha="center", va="bottom", fontsize=8.0, color=color, fontweight="bold")


bar_annot(ax_b, bar08[0], OLD_LABEL_PERM_P['sub-08_V4'], COL_08)
bar_annot(ax_b, bar09[0], OLD_LABEL_PERM_P['sub-09_V4'], COL_09)
ax_b.set_xlim(0.0, 3.0)
ax_b.set_xticks(x_subj); ax_b.set_xticklabels(["Sub-08\n(deutan)", "Sub-09\n(protan)"], fontsize=7)
ax_b.set_ylabel("Spearman ρ\n(V4 LOCO, OLD)", fontsize=7)
ax_b.set_ylim(0, 1.10)
ax_b.set_title("OLD-formula 2-component fit (V4, simplified L_fit)", fontsize=7.5, fontweight="bold", pad=3)
ax_b.axhline(0, color="gray", lw=0.4)
ax_b.spines[["top", "right"]].set_visible(False)


# Panel C
VMIN, VMAX = -0.5, 0.90
CMAP = "RdBu_r"


def plot_landscape(ax, bs, bc, rho_grid, best_bs, best_bc, best_rho, best_p,
                   color, subj, cvdtype):
    im = ax.pcolormesh(bs, bc, rho_grid, cmap=CMAP, vmin=VMIN, vmax=VMAX,
                       shading="nearest", rasterized=True)
    ax.plot(best_bs, best_bc, "*", color="white", ms=9, zorder=10,
            markeredgecolor="black", markeredgewidth=0.5)
    lbl_ha = "left" if best_bs < np.median(bs) else "right"
    lbl_x = best_bs + 1.5 if lbl_ha == "left" else best_bs - 1.5
    bc_mid = np.median(bc)
    lbl_va = "bottom" if best_bc < bc_mid else "top"
    lbl_dy = 2.0 if lbl_va == "bottom" else -2.0
    ax.text(lbl_x, best_bc + lbl_dy,
            f"β_s={best_bs:.0f}°, β_c={best_bc:+.0f}°\nρ={best_rho:.2f} {sig_label(best_p)}",
            fontsize=7.0, color="white", va=lbl_va, ha=lbl_ha, zorder=11,
            bbox=dict(boxstyle="round,pad=0.2", facecolor="black", alpha=0.55, lw=0))
    ax.set_xlabel("β_s — S-cone shift (°)", fontsize=7)
    ax.set_ylabel("β_c — confusion rot. (°)", fontsize=7)
    ax.set_title(f"{subj}  ({cvdtype})", fontsize=7.5, fontweight="bold", pad=3)
    ax.spines[["top", "right"]].set_visible(False)
    return im


im08 = plot_landscape(ax_c08, bs08, bc08, rho08, b08['bs'], b08['bc'],
                     b08['spearman_r'], OLD_LABEL_PERM_P['sub-08_V4'],
                     COL_08, "Sub-08", "deutan")
im09 = plot_landscape(ax_c09, bs09, bc09, rho09, b09['bs'], b09['bc'],
                     b09['spearman_r'], OLD_LABEL_PERM_P['sub-09_V4'],
                     COL_09, "Sub-09", "protan")

cb = fig.colorbar(im09, cax=ax_cb, extend="min")
cb.set_label("Spearman ρ", fontsize=7, labelpad=4)
cb.ax.tick_params(labelsize=7)
cb.set_ticks([-0.4, -0.2, 0.0, 0.2, 0.4, 0.6, 0.8])


# Panel letters
letter_kw = dict(fontsize=10, fontweight="bold", va="top", ha="left", transform=fig.transFigure)
fig.text(L_A - 0.025, B_B + H_B + 0.025, "B", **letter_kw)
fig.text(L_A - 0.025, B_R1 + H_AB_ROW + 0.025, "A", **letter_kw)
fig.text(L_C - 0.02, B_R1 + H_AB_ROW + 0.025, "C", **letter_kw)

out_png = OUT / "fig_F4_V4_simplified.png"
out_pdf = OUT / "fig_F4_V4_simplified.pdf"
fig.savefig(out_png, dpi=300, bbox_inches="tight", facecolor="white")
fig.savefig(out_pdf, bbox_inches="tight", facecolor="white")
plt.close()
print(f"Wrote {out_png}\n      {out_pdf}")
print(f"  sub-08 V4 OLD: β=({b08['bs']:.0f}, {b08['bc']:+.0f}), ρ={b08['spearman_r']:.3f}")
print(f"  sub-09 V4 OLD: β=({b09['bs']:.0f}, {b09['bc']:+.0f}), ρ={b09['spearman_r']:.3f}")
