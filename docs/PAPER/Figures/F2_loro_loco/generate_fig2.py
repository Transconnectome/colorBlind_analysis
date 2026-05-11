#!/usr/bin/env python3
"""
Figure 2 — LORO (discrimination) vs LOCO (interpolation) dissociation in CVD
=============================================================================
Panel A: LORO LDA accuracy (SRM) — discrimination preserved in CVD
Panel B: LOCO adjacent_acc (ForwardEncoding) — interpolation impaired in hV4
Panel C: Per-hue adjacent_acc at hV4

Chance: Panel A = 1/8 = 0.125 (exact). Panels B/C = 3/8 = 0.375 (adjacent).
Statistics: Crawford & Howell one-tailed t-test (vs HC distribution).
"""

import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import os
from scipy import stats

BASE = "/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis"
LOCO_FILE   = f"{BASE}/analysis/phase3_decoder_comparing/results/loco_decoding_comparison/decoding_comparison_full.json"
LOCO_HC_DIR = f"{BASE}/analysis/phase3_decoder_comparing/results/loco_srm"
LORO_DIR    = f"{BASE}/analysis/phase3_decoder_comparing/results/loro/srm"
OUT_DIR     = os.path.dirname(os.path.abspath(__file__))

SUBS_HC  = [f"{i:02d}" for i in range(1, 8)]
SUBS_CVD = ["08", "09"]
ROIS     = ["V1", "V2", "V3", "V4"]
ROI_LABELS  = ["V1", "V2", "V3", "hV4"]
HUE_NAMES   = ["Red", "Org", "Yel", "Grn", "Cyn", "Blu", "Pur", "Mag"]

CHANCE_EXACT    = 0.125
CHANCE_ADJACENT = 0.375

HC_COLOR  = "#AAAAAA"
HC_DOT    = "#555555"
S08_COLOR = "#D55E00"
S09_COLOR = "#009E73"
CHANCE_COL = "#888888"

# ── Load data ─────────────────────────────────────────────────────────────────
with open(LOCO_FILE) as f:
    loco_cvd_raw = json.load(f)

loco_acc = {}
for sub in SUBS_CVD + ["10"]:
    loco_acc[sub] = {}
    for roi in ROIS:
        loco_acc[sub][roi] = loco_cvd_raw[sub][roi]["ForwardEncoding"]["adjacent_acc"]

for sub in SUBS_HC:
    with open(f"{LOCO_HC_DIR}/sub-{sub}_loco.json") as f:
        d = json.load(f)
    loco_acc[sub] = {}
    for roi in ROIS:
        loco_acc[sub][roi] = d["results"][roi]["ForwardEncoding"]["overall_adjacent_acc"]

hue_acc_08 = {}
hue_acc_09 = {}
for fold in loco_cvd_raw["08"]["V4"]["ForwardEncoding"]["fold_results"]:
    hue_acc_08[fold["test_color"]] = fold["adjacent_acc"]
for fold in loco_cvd_raw["09"]["V4"]["ForwardEncoding"]["fold_results"]:
    hue_acc_09[fold["test_color"]] = fold["adjacent_acc"]

hue_acc_hc = {i: [] for i in range(8)}
for sub in SUBS_HC:
    with open(f"{LOCO_HC_DIR}/sub-{sub}_loco.json") as f:
        d = json.load(f)
    for fold in d["results"]["V4"]["ForwardEncoding"]["fold_results"]:
        hue_acc_hc[fold["test_color"]].append(fold["adjacent_acc"])

hue_acc_hc_mean = np.array([np.mean(hue_acc_hc[i]) for i in range(8)])
hue_acc_hc_sem  = np.array([np.std(hue_acc_hc[i], ddof=1) / np.sqrt(7) for i in range(8)])
hue_acc_08_arr  = np.array([hue_acc_08[i] for i in range(8)])
hue_acc_09_arr  = np.array([hue_acc_09[i] for i in range(8)])

loro_acc = {}
for sub in SUBS_HC + SUBS_CVD:
    with open(f"{LORO_DIR}/sub-{sub}_performance_raw.json") as f:
        d = json.load(f)
    srm = d["results"]["srm"]
    loro_acc[sub] = {}
    for roi in ROIS:
        folds = srm[roi]["LDA"]
        loro_acc[sub][roi] = np.mean([fold["acc_exact"] for fold in folds])

loco_hc_mean = np.array([np.mean([loco_acc[s][r] for s in SUBS_HC]) for r in ROIS])
loco_hc_sem  = np.array([np.std([loco_acc[s][r] for s in SUBS_HC], ddof=1)/np.sqrt(7) for r in ROIS])
loco_hc_ind  = {r: [loco_acc[s][r] for s in SUBS_HC] for r in ROIS}

loro_hc_mean = np.array([np.mean([loro_acc[s][r] for s in SUBS_HC]) for r in ROIS])
loro_hc_sem  = np.array([np.std([loro_acc[s][r] for s in SUBS_HC], ddof=1)/np.sqrt(7) for r in ROIS])
loro_hc_ind  = {r: [loro_acc[s][r] for s in SUBS_HC] for r in ROIS}

def crawford_howell(x_i, hc_vals):
    n = len(hc_vals)
    mean_hc = np.mean(hc_vals)
    sd_hc = np.std(hc_vals, ddof=1)
    t = (x_i - mean_hc) / (sd_hc * np.sqrt((n + 1) / n))
    p = stats.t.cdf(t, df=n - 1)
    return t, p

hc_hv4_vals = loco_hc_ind["V4"]
ch_08 = crawford_howell(loco_acc["08"]["V4"], hc_hv4_vals)
ch_09 = crawford_howell(loco_acc["09"]["V4"], hc_hv4_vals)

# ── Figure layout ─────────────────────────────────────────────────────────────
mm = 1/25.4
fig = plt.figure(figsize=(180*mm, 88*mm))

gs = fig.add_gridspec(1, 3,
                      left=0.09, right=0.97,
                      top=0.90, bottom=0.22,
                      wspace=0.42,
                      width_ratios=[1, 1, 1.1])

ax_a = fig.add_subplot(gs[0])
ax_b = fig.add_subplot(gs[1])
ax_c = fig.add_subplot(gs[2])

x  = np.arange(len(ROIS))
bw = 0.55

def strip_spines(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

def plot_bars(ax, hc_mean, hc_sem, hc_ind, v08, v09,
              ylabel, chance, y_lo, y_hi,
              sig_annot=None, ns_annot=None):
    ax.bar(x, hc_mean, width=bw, color=HC_COLOR, zorder=2, linewidth=0)
    ax.errorbar(x, hc_mean, yerr=hc_sem, fmt="none",
                color="#333333", capsize=2.5, linewidth=0.9, zorder=3)
    np.random.seed(42)
    for i, roi in enumerate(ROIS):
        jit = np.random.uniform(-0.12, 0.12, len(hc_ind[roi]))
        ax.scatter(i + jit, hc_ind[roi], s=8, color=HC_DOT,
                   alpha=0.65, zorder=4, linewidths=0)
    for i in range(len(ROIS)):
        ax.plot(x[i], v08[i], marker="s", color=S08_COLOR,
                markersize=6.5, zorder=5, linewidth=0,
                markeredgecolor="white", markeredgewidth=0.4)
        ax.plot(x[i], v09[i], marker="^", color=S09_COLOR,
                markersize=6.5, zorder=5, linewidth=0,
                markeredgecolor="white", markeredgewidth=0.4)
    ax.axhline(chance, color=CHANCE_COL, linestyle="--",
               linewidth=0.8, zorder=1, alpha=0.75)
    top = y_hi - (y_hi - y_lo) * 0.02
    if sig_annot:
        for ri, lbl in sig_annot:
            ax.text(x[ri], top, lbl, ha="center", va="top",
                    fontsize=9, fontweight="bold", color="#333333")
    if ns_annot:
        for ri, lbl in ns_annot:
            ax.text(x[ri], top, lbl, ha="center", va="top",
                    fontsize=6.5, color="#777777")
    ax.set_xticks(x)
    ax.set_xticklabels(ROI_LABELS, fontsize=7)
    ax.set_ylabel(ylabel, fontsize=7, labelpad=3)
    ax.tick_params(axis="both", labelsize=6.5, length=3)
    ax.set_ylim(y_lo, y_hi)
    strip_spines(ax)

# ── Panel A: LORO ─────────────────────────────────────────────────────────────
loro_08 = np.array([loro_acc["08"][r] for r in ROIS])
loro_09 = np.array([loro_acc["09"][r] for r in ROIS])

plot_bars(ax_a,
          hc_mean=loro_hc_mean, hc_sem=loro_hc_sem, hc_ind=loro_hc_ind,
          v08=loro_08, v09=loro_09,
          ylabel="Proportion correct",
          chance=CHANCE_EXACT,
          y_lo=0.0, y_hi=1.12,
          ns_annot=[(3, "n.s.")])

ax_a.text(-0.45, 1.10, "A", fontsize=10, fontweight="bold", va="top")

# ── Panel B: LOCO ─────────────────────────────────────────────────────────────
loco_08 = np.array([loco_acc["08"][r] for r in ROIS])
loco_09 = np.array([loco_acc["09"][r] for r in ROIS])

hv4_sig = [(3, "*")] if (ch_08[1] < 0.05 or ch_09[1] < 0.05) else None
hv4_ns  = [(3, "n.s.")] if hv4_sig is None else None

plot_bars(ax_b,
          hc_mean=loco_hc_mean, hc_sem=loco_hc_sem, hc_ind=loco_hc_ind,
          v08=loco_08, v09=loco_09,
          ylabel="Adjacent accuracy",
          chance=CHANCE_ADJACENT,
          y_lo=0.0, y_hi=0.82,
          sig_annot=hv4_sig,
          ns_annot=hv4_ns)

ax_b.text(-0.45, 0.805, "B", fontsize=10, fontweight="bold", va="top")

# ── Panel C: Per-hue at hV4 ───────────────────────────────────────────────────
hue_x = np.arange(8)
bw_c  = 0.25

ax_c.bar(hue_x - bw_c, hue_acc_hc_mean, width=bw_c,
         color=HC_COLOR, linewidth=0, zorder=2)
ax_c.errorbar(hue_x - bw_c, hue_acc_hc_mean, yerr=hue_acc_hc_sem,
              fmt="none", color="#333333", capsize=1.5, linewidth=0.8, zorder=3)
ax_c.bar(hue_x,      hue_acc_08_arr, width=bw_c,
         color=S08_COLOR, linewidth=0, zorder=2, alpha=0.85)
ax_c.bar(hue_x + bw_c, hue_acc_09_arr, width=bw_c,
         color=S09_COLOR, linewidth=0, zorder=2, alpha=0.85)

ax_c.axhline(CHANCE_ADJACENT, color=CHANCE_COL, linestyle="--",
             linewidth=0.8, zorder=1, alpha=0.75)

ax_c.set_xticks(hue_x)
ax_c.set_xticklabels(HUE_NAMES, rotation=35, ha="right", fontsize=6.5)
ax_c.set_ylabel("Adjacent accuracy", fontsize=7, labelpad=3)
ax_c.set_ylim(0, 1.08)
ax_c.tick_params(axis="both", labelsize=6.5, length=3)
strip_spines(ax_c)
ax_c.text(-0.9, 1.06, "C", fontsize=10, fontweight="bold", va="top")

# ── Shared legend ─────────────────────────────────────────────────────────────
legend_handles = [
    mpatches.Patch(facecolor=HC_COLOR, label="HC mean ± SEM", edgecolor="none"),
    Line2D([0], [0], marker="o", color="w", markerfacecolor=HC_DOT,
           markersize=5, label="HC individuals", linewidth=0),
    Line2D([0], [0], marker="s", color="w", markerfacecolor=S08_COLOR,
           markersize=6, label="sub-08 (deutan)", linewidth=0),
    Line2D([0], [0], marker="^", color="w", markerfacecolor=S09_COLOR,
           markersize=6, label="sub-09 (protan)", linewidth=0),
]
fig.legend(handles=legend_handles, loc="lower center",
           ncol=4, fontsize=6.5, frameon=False,
           bbox_to_anchor=(0.5, 0.01))

# ── Save ──────────────────────────────────────────────────────────────────────
out_png = os.path.join(OUT_DIR, "fig2_output.png")
out_pdf = os.path.join(OUT_DIR, "fig2_output.pdf")
fig.savefig(out_png, dpi=300, bbox_inches="tight")
fig.savefig(out_pdf, bbox_inches="tight")
print(f"Saved: {out_png}")

print("\nLOCO hV4 Crawford & Howell:")
print(f"  sub-08: t={ch_08[0]:.3f}, p={ch_08[1]:.4f}")
print(f"  sub-09: t={ch_09[0]:.3f}, p={ch_09[1]:.4f}")
