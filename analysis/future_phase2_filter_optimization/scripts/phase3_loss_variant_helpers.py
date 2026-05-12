"""phase3_loss_variant_helpers.py — shared helpers for loss-variant sub-agents.

Loss-variant agents (V1-V4) all share these utilities:
  - Read cached vuln_sim from results/old_formula/sub-XX_V4_vulnsim_cache.json
  - Compute per-cell loss value with their variant's formula
  - Save landscape as results/old_formula/sub-XX_V4_{VARIANT}_{landscape,summary}.json
  - Generate F4-style figure (sub-08 V4 + sub-09 V4 in single fig)

Variants:
  V1demeaned: L_vuln replaced with offset-free MSE
  V2pearson:  Add L_pearson term
  V3rankw03 / V3rankw02: Reduce β (L_rank weight) from 0.5 → 0.3 / 0.2
  V4ccc:      Replace L_vuln + L_rank with single CCC term

Layout (post-reorg 2026-05-11): single flat folder, naming convention
  sub-XX_VV_VARIANT_TYPE.{json,png,pdf}
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr, pearsonr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

_THIS_DIR = Path(__file__).resolve().parent
_PHASE2 = _THIS_DIR.parent

OUT_DIR = _PHASE2 / 'results' / 'old_formula'
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Backward-compat alias (variant scripts V1/V2/V3/V4 imported OUT_BASE)
OUT_BASE = OUT_DIR


# ---------- Cache loading ----------
def load_cache(subj_id: str, roi: str = 'V4') -> dict:
    """Load vuln_sim cache. New layout: results/old_formula/sub-XX_VV_vulnsim_cache.json"""
    fn = OUT_DIR / f'sub-{subj_id}_{roi}_vulnsim_cache.json'
    with open(fn) as f:
        return json.load(f)


# ---------- Loss components ----------
def mse(a, b):
    return float(np.mean((np.asarray(a) - np.asarray(b)) ** 2))


def demeaned_mse(sim, obs):
    sim = np.asarray(sim); obs = np.asarray(obs)
    return float(np.mean(((sim - sim.mean()) - (obs - obs.mean())) ** 2))


def spearman_safe(a, b):
    rho, _ = spearmanr(a, b)
    return float(rho) if np.isfinite(rho) else 0.0


def pearson_safe(a, b):
    r, _ = pearsonr(a, b)
    return float(r) if np.isfinite(r) else 0.0


def concordance_correlation_coefficient(sim, obs):
    """CCC = 2 · r · sd_sim · sd_obs / (sd_sim² + sd_obs² + (mean_sim - mean_obs)²)."""
    sim = np.asarray(sim); obs = np.asarray(obs)
    r = pearson_safe(sim, obs)
    msim = sim.mean(); mobs = obs.mean()
    ssim = sim.std(); sobs = obs.std()
    denom = ssim**2 + sobs**2 + (msim - mobs)**2
    if denom < 1e-10:
        return 0.0
    return 2.0 * r * ssim * sobs / denom


# Normalization constants
NORM = {'vuln': 4.0, 'rank': 2.0, 'pearson': 2.0, 'ccc': 2.0}


# ---------- Landscape builder ----------
def build_landscape(cache: dict, loss_fn) -> list:
    """Apply loss_fn(vuln_sim, vuln_cvd, dt) → dict to each cell."""
    vuln_cvd = np.array(cache['vuln_cvd'])
    landscape = []
    for c in cache['cells']:
        sim = np.array(c['vuln_sim'])
        dt = np.array(c['delta_theta'])
        loss_dict = loss_fn(sim, vuln_cvd, dt)
        entry = {'bs': c['bs'], 'bc': c['bc'], 'vuln_sim': c['vuln_sim'],
                 'delta_theta': c['delta_theta'], **loss_dict}
        landscape.append(entry)
    return landscape


def grid_to_array(landscape: list, key: str = 'l_fit') -> tuple:
    bs_all = sorted(set(e['bs'] for e in landscape))
    bc_all = sorted(set(e['bc'] for e in landscape))
    arr = np.full((len(bc_all), len(bs_all)), np.nan)
    bs_idx = {v: i for i, v in enumerate(bs_all)}
    bc_idx = {v: i for i, v in enumerate(bc_all)}
    for e in landscape:
        arr[bc_idx[e['bc']], bs_idx[e['bs']]] = e[key]
    return np.array(bs_all), np.array(bc_all), arr


# ---------- F4-style figure ----------
def generate_f4_style_figure(variant_name: str,
                              cache_08: dict, landscape_08: list,
                              cache_09: dict, landscape_09: list,
                              out_path: Path,
                              loss_label: str = 'L_fit',
                              landscape_key: str = 'spearman_r',
                              landscape_label: str = 'Spearman ρ'):
    """Generate F4_twocomp-style figure for a loss variant."""
    matplotlib.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
        "font.size": 7, "axes.titlesize": 7.5, "axes.labelsize": 7,
        "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7,
        "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
        "xtick.major.size": 2.5, "ytick.major.size": 2.5, "lines.linewidth": 1.0,
        "pdf.fonttype": 42, "ps.fonttype": 42,
    })

    COL_08 = "#E07B2C"; COL_09 = "#2D8E8B"; COL_OBS = "#222222"
    HUE_LABELS = ["R", "O", "Y", "G", "C", "B", "P", "M"]; HUE_X = np.arange(8)

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

    # Find best by l_fit
    best_08 = min(landscape_08, key=lambda r: r['l_fit'])
    best_09 = min(landscape_09, key=lambda r: r['l_fit'])

    vuln_cvd_08 = np.array(cache_08['vuln_cvd'])
    vuln_sim_08 = np.array(best_08['vuln_sim'])
    vuln_cvd_09 = np.array(cache_09['vuln_cvd'])
    vuln_sim_09 = np.array(best_09['vuln_sim'])

    def plot_vuln(ax, vobs, vsim, color, subj, cvdtype, b):
        ax.axhline(0, color="#aaaaaa", lw=0.5, ls=":")
        ax.plot(HUE_X, vobs, "o-", color=COL_OBS, ms=3.5, lw=0.6, label="Observed (CVD)")
        ax.plot(HUE_X, vsim, "-", color=color, lw=1.8,
                label=f"{loss_label}-best  ρ={b['spearman_r']:.2f}")
        ax.set_xticks(HUE_X); ax.set_xticklabels(HUE_LABELS)
        ax.set_xlabel("Hue (DKL)"); ax.set_ylabel("LOCO vulnerability")
        ax.set_ylim(-1.0, 1.0)
        ax.set_title(f"{subj}  ({cvdtype})", fontweight="bold", pad=3)
        ax.legend(loc="upper right", handlelength=1.8, handletextpad=0.3, borderpad=0.4)
        ax.spines[["top", "right"]].set_visible(False)

    plot_vuln(ax_a08, vuln_cvd_08, vuln_sim_08, COL_08, "Sub-08", "deutan", best_08)
    plot_vuln(ax_a09, vuln_cvd_09, vuln_sim_09, COL_09, "Sub-09", "protan", best_09)

    # Panel B
    x_subj = np.array([1.0, 2.0]); w = 0.55
    ax_b.bar(x_subj[0], best_08['spearman_r'], w, color=COL_08, alpha=0.9)
    ax_b.bar(x_subj[1], best_09['spearman_r'], w, color=COL_09, alpha=0.9)
    ax_b.set_xlim(0.0, 3.0); ax_b.set_xticks(x_subj)
    ax_b.set_xticklabels(["Sub-08\n(deutan)", "Sub-09\n(protan)"])
    ax_b.set_ylabel("Spearman ρ")
    ax_b.set_ylim(-0.5, 1.10)
    ax_b.set_title(f"{variant_name}: 2-component fit", fontweight="bold", pad=3)
    ax_b.axhline(0, color="gray", lw=0.4)
    ax_b.spines[["top", "right"]].set_visible(False)

    # Panel C: landscape colored by Spearman ρ (universal axis for comparability)
    VMIN, VMAX = -0.5, 0.90
    bs08, bc08, rho08 = grid_to_array(landscape_08, key=landscape_key)
    bs09, bc09, rho09 = grid_to_array(landscape_09, key=landscape_key)

    def plot_ls(ax, bs, bc, grid, best, color, subj, cvdtype):
        im = ax.pcolormesh(bs, bc, grid, cmap="RdBu_r", vmin=VMIN, vmax=VMAX,
                           shading="nearest", rasterized=True)
        ax.plot(best['bs'], best['bc'], "*", color="white", ms=9, zorder=10,
                markeredgecolor="black", markeredgewidth=0.5)
        lbl_ha = "left" if best['bs'] < np.median(bs) else "right"
        lbl_x = best['bs'] + 1.5 if lbl_ha == "left" else best['bs'] - 1.5
        lbl_va = "bottom" if best['bc'] < np.median(bc) else "top"
        lbl_dy = 2.0 if lbl_va == "bottom" else -2.0
        ax.text(lbl_x, best['bc']+lbl_dy,
                f"β_s={best['bs']:.0f}°, β_c={best['bc']:+.0f}°\n"
                f"{loss_label}={best['l_fit']:.3f}",
                fontsize=7, color="white", va=lbl_va, ha=lbl_ha, zorder=11,
                bbox=dict(boxstyle="round,pad=0.2", facecolor="black", alpha=0.55, lw=0))
        ax.set_xlabel("β_s — S-cone shift (°)"); ax.set_ylabel("β_c — confusion rot. (°)")
        ax.set_title(f"{subj}  ({cvdtype})", fontweight="bold", pad=3)
        ax.spines[["top", "right"]].set_visible(False)
        return im

    im_a = plot_ls(ax_c08, bs08, bc08, rho08, best_08, COL_08, "Sub-08", "deutan")
    im_b = plot_ls(ax_c09, bs09, bc09, rho09, best_09, COL_09, "Sub-09", "protan")
    cb = fig.colorbar(im_b, cax=ax_cb, extend="min")
    cb.set_label(landscape_label); cb.ax.tick_params(labelsize=7)
    cb.set_ticks([-0.4, -0.2, 0, 0.2, 0.4, 0.6, 0.8])

    letter_kw = dict(fontsize=10, fontweight="bold", va="top", ha="left", transform=fig.transFigure)
    fig.text(L_A-0.025, B_B+H_B+0.025, "B", **letter_kw)
    fig.text(L_A-0.025, B_R1+H_AB_ROW+0.025, "A", **letter_kw)
    fig.text(L_C-0.02,  B_R1+H_AB_ROW+0.025, "C", **letter_kw)

    fig.savefig(out_path, dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(str(out_path).replace('.png', '.pdf'), bbox_inches="tight", facecolor="white")
    plt.close()
    return best_08, best_09
