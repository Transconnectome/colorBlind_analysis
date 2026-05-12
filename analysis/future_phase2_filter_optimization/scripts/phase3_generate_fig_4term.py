"""phase3_generate_fig_4term.py — F4-style figure for 4-term OLD L_fit.

Loss: L_fit = 1.0·L_vuln + 0.5·L_rank + 0.2·L_rdm + 0.1·L_smooth

Reads results/old_formula/sub-XX_V4_4term_{summary,landscape}.json
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

BASE = _THIS_DIR.parent / "results" / "old_formula"
OUT = _THIS_DIR.parent / "results" / "old_formula"
OUT.mkdir(parents=True, exist_ok=True)

# Permutation p approximations (descriptive only)
PERM_P = {'sub-08_V4': 0.008, 'sub-09_V4': 0.10}


def load(name):
    with open(BASE / name) as f:
        return json.load(f)


s08_sum = load("sub-08_V4_4term_summary.json")
s09_sum = load("sub-09_V4_4term_summary.json")
s08_ls = load("sub-08_V4_4term_landscape.json")
s09_ls = load("sub-09_V4_4term_landscape.json")


# Recompute vuln_sim at best points (not saved in landscape directly)
sys.path.insert(0, str(_THIS_DIR))
sys.path.insert(0, str(_THIS_DIR / 'forward_models'))
from old_formula_refit import (
    HC_SUBJECTS, load_amplitudes, simulate_mean_hc_loco_legacy,
    get_shifted_design_old, load_cvd_loco_target,
    LOCAL_DATA, SERVER_DATA,
)

DATA_DIR = SERVER_DATA if SERVER_DATA.exists() else LOCAL_DATA
hc_amps = {s: load_amplitudes(DATA_DIR, s, 'V4') for s in HC_SUBJECTS}

b08 = s08_sum['best_by_l_fit']
b09 = s09_sum['best_by_l_fit']

C08, _ = get_shifted_design_old(b08['bs'], b08['bc'])
vuln_sim_08, _ = simulate_mean_hc_loco_legacy(hc_amps, C08)
C09, _ = get_shifted_design_old(b09['bs'], b09['bc'])
vuln_sim_09, _ = simulate_mean_hc_loco_legacy(hc_amps, C09)

vuln_obs_08 = np.array(load_cvd_loco_target('08', 'V4'))
vuln_obs_09 = np.array(load_cvd_loco_target('09', 'V4'))


def build_grid(landscape, key='spearman_r'):
    bs_all = sorted(set(e['bs'] for e in landscape))
    bc_all = sorted(set(e['bc'] for e in landscape))
    arr = np.full((len(bc_all), len(bs_all)), np.nan)
    bs_idx = {v: i for i, v in enumerate(bs_all)}
    bc_idx = {v: i for i, v in enumerate(bc_all)}
    for e in landscape:
        arr[bc_idx[e['bc']], bs_idx[e['bs']]] = e[key]
    return np.array(bs_all), np.array(bc_all), arr


bs08, bc08, rho08 = build_grid(s08_ls)
bs09, bc09, rho09 = build_grid(s09_ls)

# Style
COL_08 = "#E07B2C"; COL_09 = "#2D8E8B"; COL_OBS = "#222222"
HUE_LABELS = ["R", "O", "Y", "G", "C", "B", "P", "M"]; HUE_X = np.arange(8)

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


fig = plt.figure(figsize=(7.087, 7.0), dpi=300)
L_A=0.07; W_A=0.33; L_C=0.46; W_C=0.44; L_CB=0.915; W_CB=0.016
H_AB_ROW=0.27; H_B=0.150
B_R2=0.050; B_R1=B_R2+H_AB_ROW+0.070; B_B=B_R1+H_AB_ROW+0.075

ax_a08 = fig.add_axes([L_A, B_R1, W_A, H_AB_ROW])
ax_c08 = fig.add_axes([L_C, B_R1, W_C, H_AB_ROW])
ax_a09 = fig.add_axes([L_A, B_R2, W_A, H_AB_ROW])
ax_c09 = fig.add_axes([L_C, B_R2, W_C, H_AB_ROW])
ax_cb = fig.add_axes([L_CB, B_R2, W_CB, B_R1+H_AB_ROW-B_R2])
ax_b = fig.add_axes([L_A, B_B, L_CB-L_A-0.01, H_B])


def plot_vuln(ax, vobs, vsim, color, subj, cvdtype, b, p):
    ax.axhline(0, color="#aaaaaa", lw=0.5, ls=":")
    ax.plot(HUE_X, vobs, "o-", color=COL_OBS, ms=3.5, lw=0.6, label="Observed (CVD)")
    ax.plot(HUE_X, vsim, "-", color=color, lw=1.8,
            label=f"OLD 4-term  ρ={b['spearman_r']:.2f} {sig_label(p)}")
    ax.set_xticks(HUE_X); ax.set_xticklabels(HUE_LABELS)
    ax.set_xlabel("Hue (DKL)"); ax.set_ylabel("LOCO vulnerability")
    ax.set_ylim(-1.0, 1.0)
    ax.set_title(f"{subj}  ({cvdtype})", fontweight="bold", pad=3)
    ax.legend(loc="upper right", handlelength=1.8, handletextpad=0.3, borderpad=0.4)
    ax.spines[["top", "right"]].set_visible(False)


plot_vuln(ax_a08, vuln_obs_08, vuln_sim_08, COL_08, "Sub-08", "deutan",
          b08, PERM_P['sub-08_V4'])
plot_vuln(ax_a09, vuln_obs_09, vuln_sim_09, COL_09, "Sub-09", "protan",
          b09, PERM_P['sub-09_V4'])

# Panel B
x_subj = np.array([1.0, 2.0]); w = 0.55
bar08 = ax_b.bar(x_subj[0], b08['spearman_r'], w, color=COL_08, alpha=0.9)
bar09 = ax_b.bar(x_subj[1], b09['spearman_r'], w, color=COL_09, alpha=0.9)


def bar_annot(ax, bar, p, color):
    h = max(bar.get_height(), 0)
    ax.text(bar.get_x()+bar.get_width()/2, h+0.022, sig_label(p),
            ha="center", va="bottom", fontsize=8.0, color=color, fontweight="bold")


bar_annot(ax_b, bar08[0], PERM_P['sub-08_V4'], COL_08)
bar_annot(ax_b, bar09[0], PERM_P['sub-09_V4'], COL_09)
ax_b.set_xlim(0.0, 3.0); ax_b.set_xticks(x_subj)
ax_b.set_xticklabels(["Sub-08\n(deutan)", "Sub-09\n(protan)"])
ax_b.set_ylabel("Spearman ρ\n(V4 LOCO, OLD 4-term)")
ax_b.set_ylim(-0.5, 1.10)
ax_b.set_title("OLD-formula 2-component fit (V4, 4-term L_fit: vuln+rank+rdm+smooth)",
               fontweight="bold", pad=3)
ax_b.axhline(0, color="gray", lw=0.4)
ax_b.spines[["top", "right"]].set_visible(False)


# Panel C
VMIN, VMAX = -0.5, 0.90


def plot_ls(ax, bs, bc, grid, best, p, color, subj, cvdtype):
    im = ax.pcolormesh(bs, bc, grid, cmap="RdBu_r", vmin=VMIN, vmax=VMAX,
                       shading="nearest", rasterized=True)
    ax.plot(best['bs'], best['bc'], "*", color="white", ms=9, zorder=10,
            markeredgecolor="black", markeredgewidth=0.5)
    lbl_ha = "left" if best['bs'] < np.median(bs) else "right"
    lbl_x = best['bs']+1.5 if lbl_ha == "left" else best['bs']-1.5
    lbl_va = "bottom" if best['bc'] < np.median(bc) else "top"
    lbl_dy = 2.0 if lbl_va == "bottom" else -2.0
    ax.text(lbl_x, best['bc']+lbl_dy,
            f"β_s={best['bs']:.0f}°, β_c={best['bc']:+.0f}°\n"
            f"ρ={best['spearman_r']:.2f} {sig_label(p)}\n"
            f"L_fit={best['l_fit']:.3f}",
            fontsize=7, color="white", va=lbl_va, ha=lbl_ha, zorder=11,
            bbox=dict(boxstyle="round,pad=0.2", facecolor="black", alpha=0.55, lw=0))
    ax.set_xlabel("β_s — S-cone shift (°)"); ax.set_ylabel("β_c — confusion rot. (°)")
    ax.set_title(f"{subj}  ({cvdtype})", fontweight="bold", pad=3)
    ax.spines[["top", "right"]].set_visible(False)
    return im


im08 = plot_ls(ax_c08, bs08, bc08, rho08, b08, PERM_P['sub-08_V4'],
               COL_08, "Sub-08", "deutan")
im09 = plot_ls(ax_c09, bs09, bc09, rho09, b09, PERM_P['sub-09_V4'],
               COL_09, "Sub-09", "protan")
cb = fig.colorbar(im09, cax=ax_cb, extend="min")
cb.set_label("Spearman ρ", fontsize=7, labelpad=4)
cb.ax.tick_params(labelsize=7)
cb.set_ticks([-0.4, -0.2, 0, 0.2, 0.4, 0.6, 0.8])


# Panel letters
letter_kw = dict(fontsize=10, fontweight="bold", va="top", ha="left",
                 transform=fig.transFigure)
fig.text(L_A-0.025, B_B+H_B+0.025, "B", **letter_kw)
fig.text(L_A-0.025, B_R1+H_AB_ROW+0.025, "A", **letter_kw)
fig.text(L_C-0.02,  B_R1+H_AB_ROW+0.025, "C", **letter_kw)

out_png = OUT / "fig_F4_V4_4term.png"
out_pdf = OUT / "fig_F4_V4_4term.pdf"
fig.savefig(out_png, dpi=300, bbox_inches="tight", facecolor="white")
fig.savefig(out_pdf, bbox_inches="tight", facecolor="white")
plt.close()
print(f"Wrote {out_png}")
print(f"      {out_pdf}")
print()
print(f"sub-08 V4 OLD 4-term: β=({b08['bs']:.0f}, {b08['bc']:+.0f})")
print(f"  L_fit={b08['l_fit']:.4f} = α·{b08['l_vuln']:.3f} + β·{b08['l_rank']:.3f} "
      f"+ δ·{b08['l_rdm']:.3f} + ε·{b08['l_smooth']:.4f}")
print(f"  ρ={b08['spearman_r']:.3f}, rdm_cos={b08['rdm_cosine']:.3f}")
print(f"sub-09 V4 OLD 4-term: β=({b09['bs']:.0f}, {b09['bc']:+.0f})")
print(f"  L_fit={b09['l_fit']:.4f} = α·{b09['l_vuln']:.3f} + β·{b09['l_rank']:.3f} "
      f"+ δ·{b09['l_rdm']:.3f} + ε·{b09['l_smooth']:.4f}")
print(f"  ρ={b09['spearman_r']:.3f}, rdm_cos={b09['rdm_cosine']:.3f}")
