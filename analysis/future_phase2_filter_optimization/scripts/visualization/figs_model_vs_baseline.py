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

Output: presentation/figures/data/model_vs_baseline.png
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np

SCRIPT = Path(__file__).resolve()
OUT = (SCRIPT.parents[2] / "presentation" / "figures" / "data" /
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
fig = plt.figure(figsize=(14.5, 8.4), dpi=160, facecolor=BG)
fig.suptitle("Voxel Prediction & Color Decoding  —  Our Models vs Original-Paper Baselines",
             fontsize=14, fontweight="bold", color=ACCENT, y=0.965)
fig.text(0.5, 0.93,
         "Discrimination (LORO) preserved across HC and CVD; interpolation (LOCO) selectively impaired in CVD  "
         "→  CVD = color-space distortion, NOT signal loss.",
         ha="center", fontsize=10, color="#444", style="italic")

# ============================================================ Q1 LORO heatmap
# Heatmap occupies left portion; right strip reserved for callouts; colorbar placed
# at the bottom of the heatmap to leave the right side clean for caption arrows.
ax1 = fig.add_axes([0.05, 0.52, 0.26, 0.34])
im = ax1.imshow(loro_acc, aspect="auto", cmap="Blues", vmin=0.10, vmax=0.85)
ax1.set_xticks(range(3))
ax1.set_xticklabels(loro_aligns, fontsize=10)
ax1.set_yticks(range(6))
ax1.set_yticklabels(loro_models, fontsize=9.5)
ax1.set_xlabel("Alignment", fontsize=10)
ax1.set_title("Q1.  LORO classification accuracy  (8-color, chance = 0.125)",
              fontsize=11, color=ACCENT, fontweight="bold", loc="left", pad=8)

# Cell value text — contrast threshold based on colormap value
# Blues colormap: high values are dark blue → white text; low values pale → dark text.
# vmin=0.10, vmax=0.85; threshold at ~0.55 of normalised value works well.
for i in range(6):
    for j in range(3):
        v = loro_acc[i, j]
        v_norm = (v - 0.10) / (0.85 - 0.10)
        col = "white" if v_norm > 0.55 else "#1a1a1a"
        ax1.text(j, i, f"{v:.3f}", ha="center", va="center",
                 fontsize=9, color=col, fontweight="bold")

# Marker overlays — small symbols in the relevant cells (NOT obscuring numbers).
# Place markers in the upper-left corner of each cell.
ax1.scatter([2 - 0.32], [0 - 0.32], s=120, marker="*", color=GREEN,
            edgecolor="black", linewidth=0.8, zorder=12, clip_on=False)
ax1.scatter([1 - 0.32], [2 - 0.32], s=80, marker="o", facecolor="white",
            edgecolor=AMBER, linewidth=1.6, zorder=12, clip_on=False)

# Colorbar placed BELOW the heatmap (horizontal) — leaves right side fully free.
cbar_ax = fig.add_axes([0.05, 0.475, 0.26, 0.018])
cbar = fig.colorbar(im, cax=cbar_ax, orientation="horizontal")
cbar.set_label("accuracy", fontsize=8.5)
cbar.ax.tick_params(labelsize=8)

# Captions in the clear right strip (figure-level coords for full control), with
# arrows pointing back to the marked cells. Use a larger horizontal gap so the
# caption text never overlaps the rightmost heatmap column.
ax1.annotate("★ OUR BEST\nLDA + SRM = 0.793",
             xy=(2, 0), xycoords="data",
             xytext=(0.355, 0.86), textcoords="figure fraction",
             fontsize=9.0, color=GREEN, fontweight="bold",
             ha="left", va="top",
             arrowprops=dict(arrowstyle="->", color=GREEN, lw=1.4,
                             connectionstyle="arc3,rad=0.18"))
ax1.annotate("○ B&H 2009 baseline\nFE + Procrustes = 0.545",
             xy=(1, 2), xycoords="data",
             xytext=(0.355, 0.66), textcoords="figure fraction",
             fontsize=8.5, color=AMBER, fontweight="bold",
             ha="left", va="top",
             arrowprops=dict(arrowstyle="->", color=AMBER, lw=1.2,
                             connectionstyle="arc3,rad=0.18"))

# Note in the right strip below the two callouts.
fig.text(0.355, 0.555,
         "Alignment is the single most\ncritical factor.\n"
         "Non-linear models do not\ncompensate for misalignment.",
         fontsize=8.0, color="#555", style="italic", ha="left", va="top")

# ============================================================ Q2 LOCO HC vs CVD
ax2 = fig.add_axes([0.58, 0.52, 0.32, 0.34])
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
ax2.axhline(0.10, color=AMBER, linestyle=":", linewidth=1.2)

# Effect-size labels ABOVE the HC error bar tops with small font.
for i, (d, p) in enumerate(zip(loco_d, loco_p)):
    sig = "**" if p < 0.01 else ("*" if p < 0.05 else "n.s.")
    color = GREEN if p < 0.05 else "#888"
    # Place above HC error-bar top (loco_hc_hi), with small offset
    y_top = loco_hc_hi[i] + 0.04
    ax2.text(i - w/2, y_top,
             f"d={d:.2f}\np={p:.3f} {sig}",
             ha="center", va="bottom", fontsize=7.5, color=color,
             fontweight="bold")

ax2.set_xticks(roi_x)
ax2.set_xticklabels(loco_rois, fontsize=10, fontweight="bold")
ax2.set_ylabel("LOCO voxel_corr  (held-out color interpolation)", fontsize=9.5)
ax2.set_ylim(-0.40, 0.65)
ax2.set_title("Q2.  LOCO interpolation  —  HC vs CVD  (ridge_gcv)",
              fontsize=11, color=ACCENT, fontweight="bold", loc="left", pad=8)
# Legend OUTSIDE plot area (right) to avoid overlap with hV4 bars.
ax2.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0), fontsize=8.5,
           frameon=True, edgecolor="#ccc")
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)
ax2.grid(axis="y", linestyle=":", alpha=0.4)

# Footnote BELOW the panel for the perm-null annotation.
ax2.text(0.0, -0.18,
         "Dotted amber line: V1/V2 permutation null ~ 0.10–0.13  "
         "(voxel covariance contribution; not color signal).",
         transform=ax2.transAxes, fontsize=7.8, color="#666",
         style="italic", ha="left", va="top")

# ============================================================ Q3 FE-K ablation
ax3 = fig.add_axes([0.06, 0.085, 0.36, 0.32])
ks = np.arange(len(fe_K))
roi_curves = [("V1", fe_v1, "#1f77b4"),
              ("V2", fe_v2, "#ff7f0e"),
              ("V3", fe_v3, "#2ca02c"),
              ("hV4", fe_hv4, "#d62728")]
for name, vals, col in roi_curves:
    ax3.plot(ks, vals, marker="o", markersize=6, linewidth=1.6,
             color=col, label=name)
# Mark B&H 2009 default (FE-6)
ax3.axvline(3, color=AMBER, linestyle="--", linewidth=1.2, alpha=0.7)
ax3.set_xticks(ks)
ax3.set_xticklabels(fe_K, fontsize=9)
ax3.set_xlabel("ForwardEncoding basis size", fontsize=9.5)
ax3.set_ylabel("LOCO voxel_corr  (HC mean)", fontsize=9.5)
ax3.set_title("Q3.  FE channel-count ablation (HC, ridge_gcv)  —  per-ROI optima differ from B&H FE-6",
              fontsize=10, color=ACCENT, fontweight="bold", loc="left", pad=8)
# Legend OUTSIDE plot (right side).
ax3.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0), fontsize=8.5,
           frameon=True, edgecolor="#ccc", title="ROI", title_fontsize=8.5)
ax3.spines["top"].set_visible(False)
ax3.spines["right"].set_visible(False)
ax3.grid(linestyle=":", alpha=0.4)

# Annotate best K per ROI with star markers.
best = {"V1": (0, fe_v1[0]), "V2": (1, fe_v2[1]),
        "V3": (4, fe_v3[4]), "hV4": (1, fe_hv4[1])}
for name, (k, val) in best.items():
    ax3.scatter([k], [val], s=90, marker="*", color="gold",
                edgecolor="black", linewidth=0.6, zorder=10)

# Place "B&H 2009 default (FE-6)" label ABOVE the FE-6 reference line at top of axes.
# Use axes-fraction so it stays above curves regardless of data ylim.
ax3.text(3, 1.005, "B&H 2009 default (FE-6)",
         transform=ax3.get_xaxis_transform(),
         rotation=0, va="bottom", ha="center",
         fontsize=8, color=AMBER, fontweight="bold")

# Star caption (smaller, top-left of axes)
ax3.text(0.02, 0.97, "★ per-ROI optimum",
         transform=ax3.transAxes, fontsize=7.5, color="#444",
         va="top", ha="left",
         bbox=dict(facecolor="white", edgecolor="#ccc", boxstyle="round,pad=0.3"))

# ============================================================ Q4 Narrative
ax4 = fig.add_axes([0.55, 0.085, 0.42, 0.32])
ax4.axis("off")
ax4.text(0.0, 1.0, "Q4.  Comparison vs original papers  —  what we replicate, what we extend",
         fontsize=11, color=ACCENT, fontweight="bold", transform=ax4.transAxes,
         va="top")

# Updated rows: B&B 2018 → 2025 reference, marked NOT a direct comparator.
# Section 1 = direct paradigm match for Color decoding LOCO.
# Section 2 = conceptually adjacent (LORO classification), NOT direct.
# Section 3 = our LDA+SRM result.
rows = [
    ("Brouwer & Heeger 2009",
     "DIRECT comparator (Color-decoding LOCO).",
     "Method: FE-6 + Procrustes for novel-color reconstruction in V4/VO1.",
     "REPLICATE: FE+Procrustes 0.545 LORO acc; hV4 best LOCO interpolation.",
     "EXTEND: systematic K ablation (FE-2 → FE-12), per-ROI optimum is FE-3 not FE-6 for hV4.",
     ACCENT),
    ("Bannert & Bartels 2025",
     "NOT a direct comparator (different question/method).",
     "Question: hV4 perceptual hub  ·  Target: LORO classification  ·  Method: SVM on visual ROIs.",
     "Conceptually adjacent — their LORO result motivates our hV4 focus.",
     "Our voxel-prediction LOCO (Bannert & Bartels do NOT report) is the dissociation tool.",
     "#7a5c2c"),
    ("LDA + SRM  (this study)",
     "Highest LORO accuracy across all alignment × model combinations.",
     "Method: 8-color classification on shared HC space (k=3–4 per ROI).",
     "OUR BEST: LORO acc 0.793 (chance 0.125). Beats every reported decoder.",
     "Critical: discrimination preserved → CVD difference is geometric, not signal-loss.",
     GREEN),
]

# Use larger spacing between sections; bold header; sub-line for "role"; rule between.
y = 0.92
section_height = 0.31  # generous spacing
for i, (paper, role, base, repl, ext, hcol) in enumerate(rows):
    # Header
    ax4.text(0.0, y, paper, fontsize=10, fontweight="bold", color=hcol,
             transform=ax4.transAxes, va="top")
    # Role tag (italic)
    ax4.text(0.0, y - 0.045, role, fontsize=8.0, color="#555", style="italic",
             transform=ax4.transAxes, va="top")
    # Body lines
    ax4.text(0.0, y - 0.10, base, fontsize=7.8, color="#222",
             transform=ax4.transAxes, va="top")
    ax4.text(0.0, y - 0.155, repl, fontsize=7.8, color="#222",
             transform=ax4.transAxes, va="top")
    ax4.text(0.0, y - 0.21, ext, fontsize=7.8, color="#444", style="italic",
             transform=ax4.transAxes, va="top")
    # Horizontal rule below each section (except last) — drawn in axes coords
    if i < len(rows) - 1:
        ax4.plot([0.0, 1.0], [y - 0.255, y - 0.255],
                 color="#cccccc", linewidth=0.6,
                 transform=ax4.transAxes, clip_on=False)
    y -= section_height

# Footer
fig.text(0.5, 0.02,
         "Sources: phase3_decoder_comparing/README.md (LORO 3-alignment × 6-model)   ·   "
         "future_phase1_forward_model/RESULTS.md (LOCO ridge_gcv, FE-K ablation)",
         ha="center", fontsize=7.5, color="#777", style="italic")

plt.savefig(OUT, dpi=160, bbox_inches="tight", facecolor=BG)
print(f"saved → {OUT}")
