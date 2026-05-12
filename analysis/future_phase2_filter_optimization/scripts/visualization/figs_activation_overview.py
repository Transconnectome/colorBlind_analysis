"""Per-color activation overview for advisor meeting (Slide M3).

Sources:
  analysis/phase2_SRM_across_between/results/activation_prior/activation_prior_results.json

Layout: 2-row figure
  Row 1 (4 panels): V1, V2, V3, hV4 — per-color activation curves
                     HC mean (line + IQR band) + sub-08, sub-09, sub-10 individual
  Row 2 (2 panels): (a) Group test bar (mean |activation| HC vs CVD per ROI, with t-test p)
                     (b) Modulation depth HC vs CVD per ROI

Output: presentation/figures/data/activation_overview.png
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np

# --------------------------------------------------------------------- paths
SCRIPT = Path(__file__).resolve()
PROJECT = SCRIPT.parents[4]  # …/colorBlind_analysis
SRC = (PROJECT / "analysis" / "phase2_SRM_across_between" / "results" /
       "activation_prior" / "activation_prior_results.json")
OUT = (SCRIPT.parents[2] / "presentation" / "figures" / "data" /
       "activation_overview.png")
OUT.parent.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------- style
ACCENT = "#1f4e79"
BG = "#fafbfc"
HC_LINE = "#444"
HC_BAND = "#9aa6b2"
CVD = {"sub-08": "#1f77b4", "sub-09": "#d62728", "sub-10": "#8c8c8c"}
CVD_LABEL = {"sub-08": "sub-08 deutan", "sub-09": "sub-09 protan", "sub-10": "sub-10 normal*"}

# Color labels (8 hue stim)
COLOR_NAMES = ["red", "orange", "yellow", "yel-grn", "cyan", "blu-cy", "blue", "magenta"]
COLOR_THETA = [0, 45, 90, 135, 180, 225, 270, 315]
HUE_RGB = ["#e41a1c", "#ff7f00", "#ffd700", "#4daf4a", "#00ced1",
           "#2c7fb8", "#1f3a93", "#9b59b6"]

ROIS = ["V1", "V2", "V3", "hV4"]

# --------------------------------------------------------------------- load
with open(SRC) as f:
    data = json.load(f)

HC_SUBS = [f"sub-{i:02d}" for i in range(1, 8)]
CVD_SUBS = ["sub-08", "sub-09", "sub-10"]

# Per-ROI HC mean ± IQR of color_means; per-CVD individual color_means
hc_color = {}     # ROI -> (n_hc, 8)
cvd_color = {}    # ROI -> {sub: (8,)}
group_metrics = {}  # ROI -> {'mean_abs_act': (hc_m, hc_sd, cvd_m, cvd_sd, p),
                    #          'modulation_depth': (...)}

for roi in ROIS:
    if roi not in data:
        continue
    ps = data[roi]["per_subject"]
    hc_arr = []
    for s in HC_SUBS:
        if s in ps and "color_means" in ps[s]:
            hc_arr.append(np.array(ps[s]["color_means"]))
    hc_color[roi] = np.stack(hc_arr) if hc_arr else None

    cvd_color[roi] = {}
    for s in CVD_SUBS:
        if s in ps and "color_means" in ps[s]:
            cvd_color[roi][s] = np.array(ps[s]["color_means"])

    g = data[roi]["group_tests"]
    group_metrics[roi] = {
        "mean_abs_act": (g["mean_abs_act"]["hc_mean"], g["mean_abs_act"]["hc_sd"],
                         g["mean_abs_act"]["cvd_mean"], g["mean_abs_act"]["cvd_sd"],
                         g["mean_abs_act"]["p"]),
        "modulation_depth": (g["modulation_depth"]["hc_mean"], g["modulation_depth"]["hc_sd"],
                              g["modulation_depth"]["cvd_mean"], g["modulation_depth"]["cvd_sd"],
                              g["modulation_depth"]["p"]),
    }

# --------------------------------------------------------------------- figure
fig = plt.figure(figsize=(16, 9), dpi=160, facecolor=BG)
fig.suptitle("Activation Overview  —  Per-color tuning + group magnitude",
             fontsize=14, fontweight="bold", color=ACCENT, y=0.965)
fig.text(0.5, 0.935,
         "Top: per-color mean activation curves (z-units, HC pool n=7 IQR band).   "
         "Bottom: HC vs CVD group means (all p > 0.3, n.s.) → CVD deficit is not signal loss.",
         ha="center", fontsize=9.5, color="#444", style="italic")

# Row 1: per-color tuning per ROI
xs = np.arange(8)
legend_handles = None
legend_labels = None
for i, roi in enumerate(ROIS):
    # Slightly narrower panels with more spacing; leave horizontal room.
    ax = fig.add_axes([0.05 + i * 0.235, 0.56, 0.20, 0.30])
    if hc_color.get(roi) is None or hc_color[roi].size == 0:
        ax.set_title(f"{roi}: no data"); continue
    arr = hc_color[roi]
    hc_med = np.median(arr, axis=0)
    hc_q25 = np.percentile(arr, 25, axis=0)
    hc_q75 = np.percentile(arr, 75, axis=0)
    ax.fill_between(xs, hc_q25, hc_q75, color=HC_BAND, alpha=0.35,
                    label=f"HC IQR (n={arr.shape[0]})", zorder=2)
    ax.plot(xs, hc_med, color=HC_LINE, linewidth=2.0, marker="o", markersize=4,
            label="HC median", zorder=3)
    for s, vec in cvd_color[roi].items():
        ax.plot(xs, vec, color=CVD[s], linewidth=1.4, marker="o", markersize=4.5,
                alpha=0.9, label=CVD_LABEL[s], zorder=4)
    ax.axhline(0, color="#bbb", linestyle=":", linewidth=0.8)
    ax.set_xticks(xs)
    # Short codes only; full color names redundant with hue-colored ticks.
    ax.set_xticklabels([f"c{c+1}" for c in range(8)],
                       fontsize=9, rotation=0)
    for tick, hue in zip(ax.get_xticklabels(), HUE_RGB):
        tick.set_color(hue)
        tick.set_fontweight("bold")
    ax.set_ylabel("mean activation (z)", fontsize=8.5)
    ax.tick_params(axis="y", labelsize=8)
    ax.set_title(roi, fontsize=11, color=ACCENT, fontweight="bold", loc="left")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    # Capture legend handles from last panel — emit a single shared figure
    # legend BELOW the top row so it does not overlap any data.
    if i == len(ROIS) - 1:
        legend_handles, legend_labels = ax.get_legend_handles_labels()

if legend_handles is not None:
    fig.legend(legend_handles, legend_labels,
               loc="lower center", bbox_to_anchor=(0.5, 0.495),
               ncol=5, fontsize=8.5, frameon=True, framealpha=0.9,
               handlelength=2.0, columnspacing=1.5)

# Row 2 (a): mean |activation| group bars
ax_a = fig.add_axes([0.06, 0.10, 0.42, 0.30])
roi_x = np.arange(len(ROIS))
hc_means = [group_metrics[r]["mean_abs_act"][0] for r in ROIS]
hc_sds   = [group_metrics[r]["mean_abs_act"][1] for r in ROIS]
cvd_means = [group_metrics[r]["mean_abs_act"][2] for r in ROIS]
cvd_sds   = [group_metrics[r]["mean_abs_act"][3] for r in ROIS]
ps        = [group_metrics[r]["mean_abs_act"][4] for r in ROIS]
w = 0.34
ax_a.bar(roi_x - w/2, hc_means, w, yerr=hc_sds, color=HC_BAND,
         edgecolor=HC_LINE, linewidth=0.8, capsize=3, label="HC (n=7)")
ax_a.bar(roi_x + w/2, cvd_means, w, yerr=cvd_sds, color="#f3b3b3",
         edgecolor="#a04040", linewidth=0.8, capsize=3, label="CVD (n=3)")
ax_a.set_xticks(roi_x)
ax_a.set_xticklabels(ROIS, fontsize=10, fontweight="bold")
ax_a.set_ylabel("mean |activation|  (a.u.)", fontsize=9.5)
ax_a.set_title("(a)  Group magnitude per ROI  —  no HC vs CVD difference",
               fontsize=10.5, color=ACCENT, fontweight="bold", loc="left", pad=8)
# Place p-values ABOVE bars (with vertical headroom) instead of inside.
_a_top = max(hc_means[i] + hc_sds[i] for i in range(len(ROIS)))
_a_top = max(_a_top, max(cvd_means[i] + cvd_sds[i] for i in range(len(ROIS))))
for x, p in zip(roi_x, ps):
    bar_top = max(hc_means[int(x)] + hc_sds[int(x)],
                  cvd_means[int(x)] + cvd_sds[int(x)])
    ax_a.text(x, bar_top + _a_top * 0.04,
              f"p={p:.2f} (n.s.)", ha="center", va="bottom",
              fontsize=9, color="#444")
ax_a.set_ylim(top=_a_top * 1.22)
ax_a.legend(loc="upper left", fontsize=8.5)
ax_a.spines["top"].set_visible(False)
ax_a.spines["right"].set_visible(False)
ax_a.grid(axis="y", linestyle=":", alpha=0.4)

# Row 2 (b): modulation depth (color-tuning amplitude)
ax_b = fig.add_axes([0.55, 0.10, 0.42, 0.30])
hc_md = [group_metrics[r]["modulation_depth"][0] for r in ROIS]
hc_md_sd = [group_metrics[r]["modulation_depth"][1] for r in ROIS]
cvd_md = [group_metrics[r]["modulation_depth"][2] for r in ROIS]
cvd_md_sd = [group_metrics[r]["modulation_depth"][3] for r in ROIS]
ps_md = [group_metrics[r]["modulation_depth"][4] for r in ROIS]
ax_b.bar(roi_x - w/2, hc_md, w, yerr=hc_md_sd, color=HC_BAND,
         edgecolor=HC_LINE, linewidth=0.8, capsize=3, label="HC (n=7)")
ax_b.bar(roi_x + w/2, cvd_md, w, yerr=cvd_md_sd, color="#f3b3b3",
         edgecolor="#a04040", linewidth=0.8, capsize=3, label="CVD (n=3)")
ax_b.set_xticks(roi_x)
ax_b.set_xticklabels(ROIS, fontsize=10, fontweight="bold")
ax_b.set_ylabel("modulation depth  (color-tuning amplitude)", fontsize=9.5)
ax_b.set_title("(b)  Color-tuning amplitude per ROI  —  no group difference",
               fontsize=10.5, color=ACCENT, fontweight="bold", loc="left", pad=8)
# p-values ABOVE bars with sufficient headroom.
_b_top = max(hc_md[i] + hc_md_sd[i] for i in range(len(ROIS)))
_b_top = max(_b_top, max(cvd_md[i] + cvd_md_sd[i] for i in range(len(ROIS))))
for x, p in zip(roi_x, ps_md):
    bar_top = max(hc_md[int(x)] + hc_md_sd[int(x)],
                  cvd_md[int(x)] + cvd_md_sd[int(x)])
    ax_b.text(x, bar_top + _b_top * 0.04,
              f"p={p:.2f} (n.s.)", ha="center", va="bottom",
              fontsize=9, color="#444")
ax_b.set_ylim(top=_b_top * 1.22)
ax_b.legend(loc="upper left", fontsize=8.5)
ax_b.spines["top"].set_visible(False)
ax_b.spines["right"].set_visible(False)
ax_b.grid(axis="y", linestyle=":", alpha=0.4)

# Footer — pull text up from very bottom and use slightly smaller font; the
# bbox_inches='tight' below preserves margin so it never gets clipped.
fig.text(0.5, 0.025,
         "Source: phase2_SRM_across_between/results/activation_prior/activation_prior_results.json   "
         "·  generator: scripts/figs_activation_overview.py   *sub-10 = near-normal control.",
         ha="center", fontsize=7.5, color="#777", style="italic")

plt.savefig(OUT, dpi=160, bbox_inches="tight", pad_inches=0.25, facecolor=BG)
print(f"saved → {OUT}")
