"""Slide 2 — combined Activation + Model Comparison detail.

Layout (compact 2-row):
  Row 1 (Activation): 4 mini per-color tuning panels (V1, V2, V3, hV4)
                       + 1 group magnitude bar panel (right edge)
  Row 2 (Decoder vs baseline):
    - left: LORO 3-alignment × 6-model heatmap (B&H + OUR BEST highlights)
    - mid:  LOCO HC vs CVD bars per ROI (with d, p)
    - right: 3-row narrative (replicate / extend / our best)

Output: results/visualizations/meeting/slide2_activation_decoder.png
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np

SCRIPT = Path(__file__).resolve()
PROJECT = SCRIPT.parents[3]
SRC_ACT = (PROJECT / "analysis" / "phase2_SRM_across_between" / "results" /
           "activation_prior" / "activation_prior_results.json")
OUT = (SCRIPT.parents[1] / "results" / "visualizations" / "meeting" /
       "slide2_activation_decoder.png")
OUT.parent.mkdir(parents=True, exist_ok=True)

ACCENT = "#1f4e79"
BG = "#fafbfc"
HC_LINE = "#444"; HC_BAND = "#9aa6b2"
CVD = {"sub-08": "#1f77b4", "sub-09": "#d62728", "sub-10": "#8c8c8c"}
GREEN = "#2e7d32"; AMBER = "#e6a23c"; RED = "#c0392b"
COLOR_NAMES = ["red", "or", "yel", "yg", "cy", "bc", "blu", "mag"]

with open(SRC_ACT) as f:
    actdata = json.load(f)
HC_SUBS = [f"sub-{i:02d}" for i in range(1, 8)]
CVD_SUBS = ["sub-08", "sub-09", "sub-10"]
ROIS = ["V1", "V2", "V3", "hV4"]

hc_color = {}; cvd_color = {}; group_act = {}
for roi in ROIS:
    ps = actdata[roi]["per_subject"]
    hc_arr = [np.array(ps[s]["color_means"]) for s in HC_SUBS if s in ps]
    hc_color[roi] = np.stack(hc_arr) if hc_arr else None
    cvd_color[roi] = {s: np.array(ps[s]["color_means"]) for s in CVD_SUBS if s in ps}
    g = actdata[roi]["group_tests"]["mean_abs_act"]
    group_act[roi] = (g["hc_mean"], g["hc_sd"], g["cvd_mean"], g["cvd_sd"], g["p"])

# ====================================================================== figure
fig = plt.figure(figsize=(13.5, 8.5), dpi=160, facecolor=BG)
fig.suptitle("Slide 2 — Activation  +  Decoder Comparison vs Original Papers",
             fontsize=14.5, fontweight="bold", color=ACCENT, y=0.975)
fig.text(0.5, 0.945,
         "Activation magnitude is preserved; only INTERPOLATION is impaired in CVD  "
         "→ deficit is geometric, not signal-loss.",
         ha="center", fontsize=10, color="#444", style="italic")

# Row label strip 1
fig.text(0.012, 0.88, "1. Activation", color="white", fontsize=11, fontweight="bold",
         ha="left", va="center",
         bbox=dict(facecolor=ACCENT, edgecolor="none", boxstyle="round,pad=0.3"))

# ----- Row 1: 4 per-color tuning panels + 1 group bar
xs = np.arange(8)
for i, roi in enumerate(ROIS):
    ax = fig.add_axes([0.045 + i * 0.165, 0.59, 0.145, 0.24])
    arr = hc_color[roi]
    hc_med = np.median(arr, axis=0)
    hc_q25 = np.percentile(arr, 25, axis=0)
    hc_q75 = np.percentile(arr, 75, axis=0)
    ax.fill_between(xs, hc_q25, hc_q75, color=HC_BAND, alpha=0.35, zorder=2)
    ax.plot(xs, hc_med, color=HC_LINE, linewidth=1.6, marker="o",
            markersize=3, zorder=3,
            label=f"HC IQR (n={arr.shape[0]})" if i == 0 else None)
    for s, vec in cvd_color[roi].items():
        lab = s if i == 0 else None
        ax.plot(xs, vec, color=CVD[s], linewidth=1.2, marker="o",
                markersize=3.5, alpha=0.9, label=lab, zorder=4)
    ax.axhline(0, color="#bbb", linestyle=":", linewidth=0.6)
    ax.set_xticks(xs)
    ax.set_xticklabels(COLOR_NAMES, fontsize=6.5, rotation=45)
    ax.tick_params(axis="y", labelsize=7)
    ax.set_title(roi, fontsize=10, color=ACCENT, fontweight="bold", loc="left", pad=4)
    if i == 0:
        ax.set_ylabel("activation (z)", fontsize=8)
        ax.legend(loc="upper right", fontsize=6.5, frameon=True, framealpha=0.85)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", linestyle=":", alpha=0.3)

# Group magnitude bars (right panel)
ax_mag = fig.add_axes([0.74, 0.59, 0.225, 0.24])
roi_x = np.arange(4); w = 0.34
hc_m = [group_act[r][0] for r in ROIS]
hc_s = [group_act[r][1] for r in ROIS]
cv_m = [group_act[r][2] for r in ROIS]
cv_s = [group_act[r][3] for r in ROIS]
ps   = [group_act[r][4] for r in ROIS]
ax_mag.bar(roi_x - w/2, hc_m, w, yerr=hc_s, color=HC_BAND, edgecolor=HC_LINE,
           linewidth=0.6, capsize=2.5, label="HC")
ax_mag.bar(roi_x + w/2, cv_m, w, yerr=cv_s, color="#f3b3b3", edgecolor="#a04040",
           linewidth=0.6, capsize=2.5, label="CVD")
ax_mag.set_xticks(roi_x); ax_mag.set_xticklabels(ROIS, fontsize=8.5, fontweight="bold")
ax_mag.set_ylabel("mean |activation|", fontsize=8)
ax_mag.tick_params(axis="y", labelsize=7)
ax_mag.set_title("group magnitude (HC vs CVD, all n.s.)",
                 fontsize=9.5, color=ACCENT, fontweight="bold", loc="left", pad=4)
for x, p in zip(roi_x, ps):
    ax_mag.text(x, max(hc_m[int(x)], cv_m[int(x)]) +
                max(hc_s[int(x)], cv_s[int(x)]) + 0.0008,
                f"p={p:.2f}", ha="center", fontsize=6.5, color="#666")
ax_mag.legend(loc="upper left", fontsize=7, frameon=True)
ax_mag.spines["top"].set_visible(False); ax_mag.spines["right"].set_visible(False)
ax_mag.grid(axis="y", linestyle=":", alpha=0.3)

# Row label strip 2
fig.text(0.012, 0.45, "2. Decoder", color="white", fontsize=11, fontweight="bold",
         ha="left", va="center",
         bbox=dict(facecolor=ACCENT, edgecolor="none", boxstyle="round,pad=0.3"))

# ----- Row 2 left: LORO heatmap
ax_loro = fig.add_axes([0.045 + 0.005, 0.07, 0.30, 0.36])
loro_models = ["LDA", "SVM", "FE", "Ridge", "KRidge", "MLP"]
loro_aligns = ["Raw", "Procrustes", "SRM"]
loro_acc = np.array([
    [0.135, 0.758, 0.793],
    [0.127, 0.685, 0.727],
    [0.129, 0.545, 0.480],
    [0.131, 0.388, 0.313],
    [0.127, 0.332, 0.285],
    [0.126, 0.147, 0.131],
])
im = ax_loro.imshow(loro_acc, aspect="auto", cmap="Blues", vmin=0.10, vmax=0.85)
ax_loro.set_xticks(range(3)); ax_loro.set_xticklabels(loro_aligns, fontsize=9)
ax_loro.set_yticks(range(6)); ax_loro.set_yticklabels(loro_models, fontsize=8.5)
ax_loro.set_title("LORO classification (8-color, chance 0.125)",
                  fontsize=9.5, color=ACCENT, fontweight="bold", loc="left", pad=6)
for i in range(6):
    for j in range(3):
        v = loro_acc[i, j]
        col = "white" if v > 0.5 else "#222"
        ax_loro.text(j, i, f"{v:.3f}", ha="center", va="center",
                     fontsize=7.8, color=col, fontweight="bold")
ax_loro.add_patch(mpatches.Rectangle((1.5, -0.5), 1, 1, fill=False,
                                      edgecolor=GREEN, linewidth=2.0, zorder=10))
ax_loro.add_patch(mpatches.Rectangle((0.5, 1.5), 1, 1, fill=False,
                                      edgecolor=AMBER, linewidth=1.6, linestyle="--", zorder=10))

# Annotations next to heatmap
ax_loro.text(2.6, 0, "★ OUR BEST\nLDA+SRM\n0.793",
             fontsize=7.5, color=GREEN, fontweight="bold", va="center")
ax_loro.text(2.6, 2.0, "B&H 2009\nFE+Procrustes\n0.545",
             fontsize=7.0, color=AMBER, fontweight="bold", va="center")

# ----- Row 2 mid: LOCO HC vs CVD
ax_loco = fig.add_axes([0.435, 0.07, 0.255, 0.36])
loco_rois = ["V1", "V2", "V3", "hV4"]
loco_hc  = [0.130, 0.150, 0.023, 0.183]
loco_cvd = [-0.012, -0.174, -0.008, -0.058]
ds = [1.61, 1.85, 0.14, 1.19]
ps_loco = [0.021, 0.022, 0.819, 0.169]
xx = np.arange(4); w = 0.36
ax_loco.bar(xx - w/2, loco_hc, w, color=HC_BAND, edgecolor=HC_LINE,
            linewidth=0.7, label="HC (n=7)")
ax_loco.bar(xx + w/2, loco_cvd, w, color="#f3b3b3", edgecolor="#a04040",
            linewidth=0.7, label="CVD (n=3)")
ax_loco.axhline(0, color="#444", linewidth=0.5)
ax_loco.axhline(0.10, color=AMBER, linestyle=":", linewidth=1.0,
                label="V1/V2 perm null")
for i, (d, p) in enumerate(zip(ds, ps_loco)):
    sig = "**" if p < 0.01 else ("*" if p < 0.05 else "")
    color = GREEN if p < 0.05 else "#666"
    ax_loco.text(i, max(loco_hc[i], 0) + 0.06,
                 f"d={d:.2f}{sig}", ha="center", fontsize=7.5,
                 color=color, fontweight="bold")
ax_loco.set_xticks(xx); ax_loco.set_xticklabels(loco_rois, fontsize=9, fontweight="bold")
ax_loco.set_ylabel("LOCO voxel_corr", fontsize=8)
ax_loco.set_ylim(-0.30, 0.42)
ax_loco.tick_params(axis="y", labelsize=7.5)
ax_loco.set_title("LOCO interpolation HC vs CVD (ridge_gcv)",
                  fontsize=9.5, color=ACCENT, fontweight="bold", loc="left", pad=6)
ax_loco.legend(loc="lower right", fontsize=7, frameon=True)
ax_loco.spines["top"].set_visible(False); ax_loco.spines["right"].set_visible(False)
ax_loco.grid(axis="y", linestyle=":", alpha=0.3)

# ----- Row 2 right: narrative panel
ax_nar = fig.add_axes([0.71, 0.07, 0.28, 0.36])
ax_nar.axis("off")
ax_nar.text(0.0, 0.95, "vs original-paper baselines",
            fontsize=9.5, color=ACCENT, fontweight="bold",
            transform=ax_nar.transAxes)

rows = [
    ("Brouwer & Heeger 2009",
     "REPLICATE: FE+Procrustes 0.545 LORO; hV4 best LOCO.",
     "EXTEND: per-ROI optimum FE-3 (hV4), not FE-6 default."),
    ("Bannert & Bartels 2018",
     "REPLICATE: hV4 carries the deficit (d=1.19).",
     "EXTEND: HC→CVD cross-decoding p=0.668 → shared mapping."),
    ("LDA + SRM (this study)",
     "OUR BEST: LORO 0.793 (chance 0.125) — beats every reported decoder.",
     "→ discrimination preserved; CVD difference is geometric."),
]
y = 0.86
for paper, repl, ext in rows:
    ax_nar.text(0.0, y, paper, fontsize=8.5, fontweight="bold", color=ACCENT,
                transform=ax_nar.transAxes)
    ax_nar.text(0.0, y - 0.06, repl, fontsize=7.5, color="#222",
                transform=ax_nar.transAxes)
    ax_nar.text(0.0, y - 0.115, ext, fontsize=7.5, color="#444", style="italic",
                transform=ax_nar.transAxes)
    y -= 0.30

# Footer
fig.text(0.5, 0.012,
         "Sources: phase2_SRM_across_between/.../activation_prior_results.json   ·   "
         "phase3_decoder_comparing/README.md   ·   phase4_forward_model/RESULTS.md",
         ha="center", fontsize=7.5, color="#777", style="italic")

plt.savefig(OUT, dpi=160, bbox_inches="tight", facecolor=BG)
print(f"saved → {OUT}")
