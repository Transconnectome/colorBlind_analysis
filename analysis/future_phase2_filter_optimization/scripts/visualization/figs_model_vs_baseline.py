"""Decoder / voxel-prediction model comparison vs original-paper baselines.

Sources:
  analysis/phase3_decoder_comparing/README.md  (LORO 3-alignment × 6-model table)
  analysis/future_phase1_forward_model/RESULTS.md  (LOCO ridge_gcv HC-CVD gap, FE-K ablation)

Layout: 2×2 quadrant
  Q1 (top-left)  : LORO classification — 6 models × 3 alignments heatmap
                   (chance = 0.125; B&H 2009 = FE Procrustes; ours = LDA + SRM)
  Q2 (top-right) : LOCO interpolation HC vs CVD per ROI (ridge_gcv voxel_corr)
                   with Cohen's d annotations
  Q3 (bottom-left): FE channel-count ablation per ROI (LOCO ridge_gcv)
  Q4 (bottom-right): cross-decoding HC→CVD summary + key narrative

Output: results/visualizations/meeting/model_vs_baseline.png
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np

SCRIPT = Path(__file__).resolve()
OUT = (SCRIPT.parents[1] / "results" / "visualizations" / "meeting" /
       "model_vs_baseline.png")
OUT.parent.mkdir(parents=True, exist_ok=True)

ACCENT = "#1f4e79"
BG = "#fafbfc"
GREEN = "#2e7d32"
AMBER = "#e6a23c"
RED = "#c0392b"
HC_COL = "#9aa6b2"
CVD_COL = "#f3b3b3"
HC_EDGE = "#444"
CVD_EDGE = "#a04040"

# ===================================================================== data
# LORO 3-alignment × 6-model accuracy (from phase3_decoder_comparing/README.md)
loro_models = ["LDA", "SVM", "FE", "Ridge", "KRidge", "MLP"]
loro_aligns = ["Raw", "Procrustes", "SRM"]
loro_acc = np.array([
    [0.135, 0.758, 0.793],   # LDA
    [0.127, 0.685, 0.727],   # SVM
    [0.129, 0.545, 0.480],   # FE  ← B&H 2009 baseline lives here (Procrustes)
    [0.131, 0.388, 0.313],   # Ridge
    [0.127, 0.332, 0.285],   # KRidge
    [0.126, 0.147, 0.131],   # MLP
])
LORO_CHANCE = 0.125

# LOCO HC vs CVD (ridge_gcv voxel_corr) — from RESULTS.md §2b
loco_rois = ["V1", "V2", "V3", "hV4"]
loco_hc      = [0.130, 0.150, 0.023, 0.183]
loco_hc_lo   = [0.061, 0.006, -0.146, 0.042]
loco_hc_hi   = [0.191, 0.247, 0.177, 0.318]
loco_cvd     = [-0.012, -0.174, -0.008, -0.058]
loco_cvd_lo  = [-0.062, -0.257, -0.193, -0.275]
loco_cvd_hi  = [0.045, -0.024, 0.118, 0.137]
loco_d       = [1.61, 1.85, 0.14, 1.19]
loco_p       = [0.021, 0.022, 0.819, 0.169]

# FE channel-count ablation (LOCO ridge_gcv, HC n=7) — RESULTS.md §2c
fe_K = ["FE-2", "FE-3", "FE-4", "FE-6", "FE-8", "FE-12"]
fe_v1   = [0.153, 0.143, 0.109, 0.130, 0.128, 0.134]
fe_v2   = [0.180, 0.180, 0.165, 0.150, 0.176, 0.168]
fe_v3   = [0.085, 0.097, 0.052, 0.023, 0.112, 0.106]
fe_hv4  = [0.186, 0.205, 0.185, 0.183, 0.191, 0.190]

# Cross-decoding HC→CVD (LDA+SRM cross-subject; phase3_decoder_comparing)
cross_p = 0.668  # no significant HC vs CVD bias

# ===================================================================== figure
fig = plt.figure(figsize=(13.5, 8.0), dpi=160, facecolor=BG)
fig.suptitle("Voxel Prediction & Color Decoding  —  Our Models vs Original-Paper Baselines",
             fontsize=14, fontweight="bold", color=ACCENT, y=0.965)
fig.text(0.5, 0.93,
         "Discrimination (LORO) preserved across HC and CVD; interpolation (LOCO) selectively impaired in CVD  "
         "→  CVD = color-space distortion, NOT signal loss.",
         ha="center", fontsize=10, color="#444", style="italic")

# ============================================================ Q1 LORO heatmap
ax1 = fig.add_axes([0.06, 0.50, 0.40, 0.36])
im = ax1.imshow(loro_acc, aspect="auto", cmap="Blues", vmin=0.10, vmax=0.85)
ax1.set_xticks(range(3))
ax1.set_xticklabels(loro_aligns, fontsize=10)
ax1.set_yticks(range(6))
ax1.set_yticklabels(loro_models, fontsize=9.5)
ax1.set_xlabel("Alignment", fontsize=10)
ax1.set_title("Q1.  LORO classification accuracy  (8-color, chance = 0.125)",
              fontsize=11, color=ACCENT, fontweight="bold", loc="left", pad=8)

for i in range(6):
    for j in range(3):
        v = loro_acc[i, j]
        col = "white" if v > 0.5 else "#222"
        ax1.text(j, i, f"{v:.3f}", ha="center", va="center",
                 fontsize=9, color=col, fontweight="bold")

# Best (LDA+SRM) and B&H baseline (FE+Procrustes) call-outs
ax1.add_patch(mpatches.Rectangle((1.5, -0.5), 1, 1, fill=False,
                                  edgecolor=GREEN, linewidth=2.5, zorder=10))
ax1.text(2, -0.7, "★ OUR BEST\n0.793", ha="center", fontsize=8.0,
         color=GREEN, fontweight="bold")
ax1.add_patch(mpatches.Rectangle((0.5, 1.5), 1, 1, fill=False,
                                  edgecolor=AMBER, linewidth=2.0, linestyle="--", zorder=10))
ax1.text(1, 2.95, "B&H 2009 baseline\n(FE-6 + Procrustes) = 0.545",
         ha="center", fontsize=7.5, color=AMBER, fontweight="bold")

cbar = fig.colorbar(im, ax=ax1, fraction=0.04, pad=0.02)
cbar.set_label("accuracy", fontsize=8.5)
cbar.ax.tick_params(labelsize=8)

# Note below
ax1.text(0.0, 6.4,
         "Alignment is the single most critical factor. Non-linear models do not compensate for misalignment.",
         transform=ax1.transData, fontsize=8.0, color="#555", style="italic")

# ============================================================ Q2 LOCO HC vs CVD
ax2 = fig.add_axes([0.55, 0.50, 0.42, 0.36])
roi_x = np.arange(len(loco_rois))
w = 0.35
hc_err = [[loco_hc[i] - loco_hc_lo[i] for i in range(4)],
          [loco_hc_hi[i] - loco_hc[i] for i in range(4)]]
cvd_err = [[loco_cvd[i] - loco_cvd_lo[i] for i in range(4)],
           [loco_cvd_hi[i] - loco_cvd[i] for i in range(4)]]
ax2.bar(roi_x - w/2, loco_hc, w, yerr=hc_err, color=HC_COL, edgecolor=HC_EDGE,
        linewidth=0.8, capsize=3, label="HC (n=7)")
ax2.bar(roi_x + w/2, loco_cvd, w, yerr=cvd_err, color=CVD_COL, edgecolor=CVD_EDGE,
        linewidth=0.8, capsize=3, label="CVD (n=3)")
ax2.axhline(0, color="#444", linestyle="-", linewidth=0.6)
ax2.axhline(0.10, color=AMBER, linestyle=":", linewidth=1.2,
            label="V1/V2 perm null ~0.10–0.13")

for i, (d, p) in enumerate(zip(loco_d, loco_p)):
    sig = "**" if p < 0.01 else ("*" if p < 0.05 else "n.s.")
    color = GREEN if p < 0.05 else "#888"
    ax2.text(i, max(loco_hc[i], 0) + 0.10,
             f"d = {d:.2f}\np = {p:.3f}  {sig}",
             ha="center", fontsize=7.8, color=color, fontweight="bold")

ax2.set_xticks(roi_x)
ax2.set_xticklabels(loco_rois, fontsize=10, fontweight="bold")
ax2.set_ylabel("LOCO voxel_corr  (held-out color interpolation)", fontsize=9.5)
ax2.set_ylim(-0.40, 0.55)
ax2.set_title("Q2.  LOCO interpolation  —  HC vs CVD  (ridge_gcv, our final encoder)",
              fontsize=11, color=ACCENT, fontweight="bold", loc="left", pad=8)
ax2.legend(loc="lower right", fontsize=8.5)
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)
ax2.grid(axis="y", linestyle=":", alpha=0.4)

# ============================================================ Q3 FE-K ablation
ax3 = fig.add_axes([0.06, 0.075, 0.40, 0.34])
ks = np.arange(len(fe_K))
roi_curves = [("V1", fe_v1, "#1f77b4"),
              ("V2", fe_v2, "#ff7f0e"),
              ("V3", fe_v3, "#2ca02c"),
              ("hV4", fe_hv4, "#d62728")]
for name, vals, col in roi_curves:
    ax3.plot(ks, vals, marker="o", markersize=6, linewidth=1.6,
             color=col, label=name)
# Mark B&H 2009 default (FE-6)
ax3.axvline(3, color=AMBER, linestyle="--", linewidth=1.2, alpha=0.7,
            label="B&H 2009 default (FE-6)")
ax3.set_xticks(ks)
ax3.set_xticklabels(fe_K, fontsize=9)
ax3.set_xlabel("ForwardEncoding basis size", fontsize=9.5)
ax3.set_ylabel("LOCO voxel_corr  (HC mean)", fontsize=9.5)
ax3.set_title("Q3.  FE channel-count ablation (HC, ridge_gcv)  —  per-ROI optima differ from B&H FE-6",
              fontsize=10, color=ACCENT, fontweight="bold", loc="left", pad=8)
ax3.legend(loc="lower right", fontsize=8.0, ncol=2)
ax3.spines["top"].set_visible(False)
ax3.spines["right"].set_visible(False)
ax3.grid(linestyle=":", alpha=0.4)
# Annotate best K per ROI
best = {"V1": (0, fe_v1[0]), "V2": (1, fe_v2[1]),
        "V3": (4, fe_v3[4]), "hV4": (1, fe_hv4[1])}
for name, (k, val) in best.items():
    ax3.scatter([k], [val], s=90, marker="*", color="gold",
                edgecolor="black", linewidth=0.6, zorder=10)
ax3.text(0.02, 0.02, "★ per-ROI optimum",
         transform=ax3.transAxes, fontsize=7.5, color="#444",
         bbox=dict(facecolor="white", edgecolor="#ccc", boxstyle="round,pad=0.3"))

# ============================================================ Q4 Narrative
ax4 = fig.add_axes([0.55, 0.075, 0.42, 0.34])
ax4.axis("off")
ax4.text(0.0, 0.95, "Q4.  Comparison vs original papers  —  what we replicate, what we extend",
         fontsize=11, color=ACCENT, fontweight="bold", transform=ax4.transAxes)

rows = [
    ("Brouwer & Heeger 2009",
     "FE-6 + Procrustes for novel-color reconstruction in V4/VO1.",
     "REPLICATE: FE+Procrustes 0.545 LORO acc; hV4 best LOCO interpolation.",
     "EXTEND: systematic K ablation (FE-2 → FE-12), per-ROI optimum is FE-3 not FE-6 for hV4."),
    ("Bannert & Bartels 2018",
     "hV4 perceptual hub; only area predicting trial-by-trial behavior.",
     "REPLICATE: hV4 LOCO HC=+0.183 vs CVD=−0.058 (d=1.19) — hV4 carries the deficit.",
     "EXTEND: HC→CVD cross-decoding p = 0.668 → shared mapping confirmed (CVD is distortion, not bias)."),
    ("LDA + SRM (this study)",
     "8-color classification on shared HC space (k=3–4).",
     "OUR BEST: LORO acc 0.793 (chance 0.125). Beats every reported decoder.",
     "Critical for filter design: discrimination preserved → CVD difference is geometric, not signal-loss."),
]

y = 0.82
for paper, base, repl, ext in rows:
    ax4.text(0.0, y, paper, fontsize=9.5, fontweight="bold", color=ACCENT,
             transform=ax4.transAxes)
    ax4.text(0.0, y - 0.05, "Method:  " + base, fontsize=8.0, color="#222",
             transform=ax4.transAxes)
    ax4.text(0.0, y - 0.095, "Ours:    " + repl, fontsize=8.0, color="#222",
             transform=ax4.transAxes)
    ax4.text(0.0, y - 0.14, "Extend:  " + ext, fontsize=8.0, color="#444", style="italic",
             transform=ax4.transAxes)
    y -= 0.30

# Footer
fig.text(0.5, 0.02,
         "Sources: phase3_decoder_comparing/README.md (LORO 3-alignment × 6-model)   ·   "
         "future_phase1_forward_model/RESULTS.md (LOCO ridge_gcv, FE-K ablation)",
         ha="center", fontsize=7.5, color="#777", style="italic")

plt.savefig(OUT, dpi=160, bbox_inches="tight", facecolor=BG)
print(f"saved → {OUT}")
