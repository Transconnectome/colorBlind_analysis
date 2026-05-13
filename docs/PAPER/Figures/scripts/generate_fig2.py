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
OUT_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SUBS_HC  = [f"{i:02d}" for i in range(1, 8)]
SUBS_CVD = ["08", "09"]
ROIS     = ["V1", "V2", "V3", "V4"]
ROI_LABELS  = ["V1", "V2", "V3", "hV4"]
HUE_NAMES   = ["Red", "Org", "Yel", "Grn", "Cyn", "Blu", "Pur", "Mag"]

CHANCE_EXACT = 0.125
CHANCE_MAE   = 90.0   # uniform-random predictor mean abs error over 8-hue circle

HC_COLOR  = "#AAAAAA"
HC_DOT    = "#555555"
S08_COLOR = "#D55E00"
S09_COLOR = "#009E73"
CHANCE_COL = "#888888"

# STIM_LAB palette (8 hue stimuli, same Lab values as Fig 1 / Fig 3)
COLOR_LAB = [
    [59.90,  62.69,   3.78],   # Red
    [64.20,  49.20,  45.58],   # Orange
    [57.27,  13.06,  41.69],   # Yellow
    [69.08, -55.02,  47.38],   # Green
    [74.61, -41.33,  -4.89],   # Cyan
    [69.14, -11.45, -40.91],   # Blue
    [60.68,  19.18, -54.13],   # Purple
    [60.17,  46.82, -40.31],   # Magenta
]

def _lab2rgb(L, a, b):
    y = (L + 16)/116; x = a/500 + y; z = y - b/200
    xyz = np.array([x, y, z])
    xyz = np.where(xyz > 0.206893, xyz**3, (xyz - 16/116)/7.787)
    xyz *= [0.95047, 1.0, 1.08883]
    M = np.array([[3.2406, -1.5372, -0.4986],
                  [-0.9689,  1.8758,  0.0415],
                  [0.0557, -0.2040,  1.0570]])
    rgb = M @ xyz
    rgb = np.where(rgb <= 0.0031308, 12.92*rgb, 1.055*rgb**(1/2.4) - 0.055)
    return tuple(np.clip(rgb, 0, 1))

HUE_RGB = [_lab2rgb(*lab) for lab in COLOR_LAB]

# ── Load data ─────────────────────────────────────────────────────────────────
with open(LOCO_FILE) as f:
    loco_cvd_raw = json.load(f)

loco_acc = {}
for sub in SUBS_CVD + ["10"]:
    loco_acc[sub] = {}
    for roi in ROIS:
        loco_acc[sub][roi] = loco_cvd_raw[sub][roi]["ForwardEncoding"]["mae"]

for sub in SUBS_HC:
    with open(f"{LOCO_HC_DIR}/sub-{sub}_loco.json") as f:
        d = json.load(f)
    loco_acc[sub] = {}
    for roi in ROIS:
        loco_acc[sub][roi] = d["results"][roi]["ForwardEncoding"]["overall_mae"]

hue_acc_08 = {}
hue_acc_09 = {}
for fold in loco_cvd_raw["08"]["V4"]["ForwardEncoding"]["fold_results"]:
    hue_acc_08[fold["test_color"]] = fold["mae"]
for fold in loco_cvd_raw["09"]["V4"]["ForwardEncoding"]["fold_results"]:
    hue_acc_09[fold["test_color"]] = fold["mae"]

hue_acc_hc = {i: [] for i in range(8)}
for sub in SUBS_HC:
    with open(f"{LOCO_HC_DIR}/sub-{sub}_loco.json") as f:
        d = json.load(f)
    for fold in d["results"]["V4"]["ForwardEncoding"]["fold_results"]:
        hue_acc_hc[fold["test_color"]].append(fold["mae"])

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

def crawford_howell(x_i, hc_vals, tail="lower"):
    """Crawford & Howell (1998) t-test for single case vs control sample.

    tail: "lower" (CVD < HC, deficit), "upper" (CVD > HC), or "two" (preserved).
    """
    n = len(hc_vals)
    mean_hc = np.mean(hc_vals)
    sd_hc = np.std(hc_vals, ddof=1)
    t = (x_i - mean_hc) / (sd_hc * np.sqrt((n + 1) / n))
    if tail == "lower":
        p = stats.t.cdf(t, df=n - 1)
    elif tail == "upper":
        p = stats.t.sf(t, df=n - 1)
    else:
        p = 2 * stats.t.sf(abs(t), df=n - 1)
    return t, p

# Panel A (LORO accuracy) — one-sided lower (deficit = lower accuracy)
ch_loro_per_roi = {}
for r in ROIS:
    ch_loro_per_roi[r] = {
        "08": crawford_howell(loro_acc["08"][r], loro_hc_ind[r], tail="lower"),
        "09": crawford_howell(loro_acc["09"][r], loro_hc_ind[r], tail="lower"),
    }
ch_loro_08 = ch_loro_per_roi["V4"]["08"]
ch_loro_09 = ch_loro_per_roi["V4"]["09"]

# Panel B (LOCO MAE) — one-sided upper per ROI (deficit = higher MAE)
ch_loco_per_roi = {}
for r in ROIS:
    ch_loco_per_roi[r] = {
        "08": crawford_howell(loco_acc["08"][r], loco_hc_ind[r], tail="upper"),
        "09": crawford_howell(loco_acc["09"][r], loco_hc_ind[r], tail="upper"),
    }
ch_08 = ch_loco_per_roi["V4"]["08"]
ch_09 = ch_loco_per_roi["V4"]["09"]

# Panel C — per-hue Crawford & Howell at hV4 (each hue tested independently)
ch_per_hue_08 = {i: crawford_howell(hue_acc_08[i], hue_acc_hc[i], tail="upper")
                 for i in range(8)}
ch_per_hue_09 = {i: crawford_howell(hue_acc_09[i], hue_acc_hc[i], tail="upper")
                 for i in range(8)}

# ── Figure layout ─────────────────────────────────────────────────────────────
mm = 1/25.4
fig = plt.figure(figsize=(180*mm, 105*mm))

gs = fig.add_gridspec(1, 3,
                      left=0.09, right=0.97,
                      top=0.76, bottom=0.18,
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

def _sig_label(p):
    """Return (text, fontsize, weight). Empty text for n.s. — keeps the plot clean."""
    if p < 0.001: return ("***", 8.5, "bold")
    if p < 0.01:  return ("**",  8.5, "bold")
    if p < 0.05:  return ("*",   8.5, "bold")
    return ("", 0, "normal")

def plot_bars(ax, hc_mean, hc_sem, hc_ind, v08, v09,
              ylabel, chance, y_lo, y_hi,
              per_roi_p08=None, per_roi_p09=None):
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
    # Chance line only (no text label)
    ax.axhline(chance, color=CHANCE_COL, linestyle="--",
               linewidth=0.8, zorder=1, alpha=0.75)
    # Per-ROI per-subject Crawford & Howell sig labels — attached directly above
    # each CVD marker (sig only; n.s. omitted)
    if per_roi_p08 is not None and per_roi_p09 is not None:
        y_pad = (y_hi - y_lo) * 0.028
        for i, roi in enumerate(ROIS):
            lbl08, fs08, fw08 = _sig_label(per_roi_p08[roi])
            lbl09, fs09, fw09 = _sig_label(per_roi_p09[roi])
            if lbl08:
                ax.text(x[i], v08[i] + y_pad, lbl08,
                        fontsize=fs08, color=S08_COLOR, fontweight=fw08,
                        ha="center", va="bottom")
            if lbl09:
                ax.text(x[i], v09[i] + y_pad, lbl09,
                        fontsize=fs09, color=S09_COLOR, fontweight=fw09,
                        ha="center", va="bottom")
    ax.set_xticks(x)
    ax.set_xticklabels(ROI_LABELS, fontsize=7)
    ax.set_ylabel(ylabel, fontsize=7, labelpad=3)
    ax.tick_params(axis="both", labelsize=6.5, length=3)
    ax.set_ylim(y_lo, y_hi)
    strip_spines(ax)

# ── Panel A: LORO (leave-one-run-out, discrimination) ────────────────────────
loro_08 = np.array([loro_acc["08"][r] for r in ROIS])
loro_09 = np.array([loro_acc["09"][r] for r in ROIS])

plot_bars(ax_a,
          hc_mean=loro_hc_mean, hc_sem=loro_hc_sem, hc_ind=loro_hc_ind,
          v08=loro_08, v09=loro_09,
          ylabel="Proportion correct",
          chance=CHANCE_EXACT,
          y_lo=0.0, y_hi=1.12,
          per_roi_p08={r: ch_loro_per_roi[r]["08"][1] for r in ROIS},
          per_roi_p09={r: ch_loro_per_roi[r]["09"][1] for r in ROIS})

ax_a.text(0.0, 1.20, "A", transform=ax_a.transAxes,
          fontsize=10, fontweight="bold", va="bottom", ha="left")
ax_a.text(0.07, 1.21, "Discrimination", transform=ax_a.transAxes,
          fontsize=7.5, va="bottom", ha="left", color="#222", fontweight="bold")
ax_a.text(0.07, 1.10, "LORO (leave-one-run-out)", transform=ax_a.transAxes,
          fontsize=6.5, va="bottom", ha="left", color="#555")

# ── Panel B: LOCO (leave-one-color-out, interpolation) ───────────────────────
loco_08 = np.array([loco_acc["08"][r] for r in ROIS])
loco_09 = np.array([loco_acc["09"][r] for r in ROIS])

plot_bars(ax_b,
          hc_mean=loco_hc_mean, hc_sem=loco_hc_sem, hc_ind=loco_hc_ind,
          v08=loco_08, v09=loco_09,
          ylabel="MAE (°)",
          chance=CHANCE_MAE,
          y_lo=0.0, y_hi=125.0,
          per_roi_p08={r: ch_loco_per_roi[r]["08"][1] for r in ROIS},
          per_roi_p09={r: ch_loco_per_roi[r]["09"][1] for r in ROIS})

ax_b.text(0.0, 1.20, "B", transform=ax_b.transAxes,
          fontsize=10, fontweight="bold", va="bottom", ha="left")
ax_b.text(0.07, 1.21, "Interpolation", transform=ax_b.transAxes,
          fontsize=7.5, va="bottom", ha="left", color="#222", fontweight="bold")
ax_b.text(0.07, 1.10, "LOCO (leave-one-color-out)", transform=ax_b.transAxes,
          fontsize=6.5, va="bottom", ha="left", color="#555")

# ── Panel C: Per-hue at hV4 (LOCO, same encoding as A/B) ─────────────────────
hue_x = np.arange(8)

# HC = bar (per-hue STIM_LAB color), CVD = markers — matches Panels A/B encoding
ax_c.bar(hue_x, hue_acc_hc_mean, width=0.55,
         color=HUE_RGB, linewidth=0.4, edgecolor="#444", zorder=2)
ax_c.errorbar(hue_x, hue_acc_hc_mean, yerr=hue_acc_hc_sem,
              fmt="none", color="#333333", capsize=1.8, linewidth=0.8, zorder=3)
ax_c.plot(hue_x, hue_acc_08_arr,
          marker="s", color=S08_COLOR, markersize=5.5,
          linestyle="-", linewidth=0.7,
          markeredgecolor="white", markeredgewidth=0.4, zorder=5)
ax_c.plot(hue_x, hue_acc_09_arr,
          marker="^", color=S09_COLOR, markersize=5.5,
          linestyle="-", linewidth=0.7,
          markeredgecolor="white", markeredgewidth=0.4, zorder=5)

ax_c.axhline(CHANCE_MAE, color=CHANCE_COL, linestyle="--",
             linewidth=0.8, zorder=1, alpha=0.75)

# Per-hue per-subject sig labels attached directly above each CVD marker
y_pad_c = 7
for i in range(8):
    lbl08, fs08, fw08 = _sig_label(ch_per_hue_08[i][1])
    lbl09, fs09, fw09 = _sig_label(ch_per_hue_09[i][1])
    if lbl08:
        ax_c.text(i, hue_acc_08_arr[i] + y_pad_c, lbl08,
                  fontsize=fs08, color=S08_COLOR, fontweight=fw08,
                  ha="center", va="bottom")
    if lbl09:
        ax_c.text(i, hue_acc_09_arr[i] + y_pad_c, lbl09,
                  fontsize=fs09, color=S09_COLOR, fontweight=fw09,
                  ha="center", va="bottom")

ax_c.set_xticks(hue_x)
ax_c.set_xticklabels(HUE_NAMES, rotation=35, ha="right", fontsize=6.5)
ax_c.set_ylabel("MAE (°)", fontsize=7, labelpad=3)
ax_c.set_ylim(0, 175)
ax_c.set_xlim(-0.6, 7.6)
ax_c.tick_params(axis="both", labelsize=6.5, length=3)
strip_spines(ax_c)
ax_c.text(0.0, 1.20, "C", transform=ax_c.transAxes,
          fontsize=10, fontweight="bold", va="bottom", ha="left")
ax_c.text(0.07, 1.21, "Per-hue interpolation at hV4",
          transform=ax_c.transAxes,
          fontsize=7.5, va="bottom", ha="left", color="#222", fontweight="bold")
ax_c.text(0.07, 1.10, "LOCO (leave-one-color-out)",
          transform=ax_c.transAxes,
          fontsize=6.5, va="bottom", ha="left", color="#555")

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
out_png = os.path.join(OUT_DIR, "fig2_loro_loco.png")
out_pdf = os.path.join(OUT_DIR, "fig2_loro_loco.pdf")
fig.savefig(out_png, dpi=300, bbox_inches="tight")
fig.savefig(out_pdf, bbox_inches="tight")
print(f"Saved: {out_png}")

print("\nCrawford & Howell — hV4 (parametric t, df=6); test: CVD performance < HC")
print("  LORO accuracy (one-sided lower, deficit = lower accuracy):")
print(f"    sub-08: t={ch_loro_08[0]:.3f}, p={ch_loro_08[1]:.4f}")
print(f"    sub-09: t={ch_loro_09[0]:.3f}, p={ch_loro_09[1]:.4f}")
print("  LOCO MAE (one-sided upper, deficit = higher MAE):")
print(f"    sub-08: t={ch_08[0]:.3f}, p={ch_08[1]:.4f}")
print(f"    sub-09: t={ch_09[0]:.3f}, p={ch_09[1]:.4f}")

print("\nPer-hue C&H at hV4 (LOCO, one-sided upper):")
print(f"  {'Hue':<7} {'sub-08 t':<10} {'p':<8} {'sub-09 t':<10} {'p':<8}")
for i, name in enumerate(HUE_NAMES):
    t08, p08 = ch_per_hue_08[i]
    t09, p09 = ch_per_hue_09[i]
    sig08 = _sig_label(p08)[0] or "-"
    sig09 = _sig_label(p09)[0] or "-"
    print(f"  {name:<7} {t08:>+8.2f}  {p08:.4f} {sig08:<3} "
          f"{t09:>+8.2f}  {p09:.4f} {sig09}")
