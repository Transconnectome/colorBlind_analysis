"""Slide 1 — Comprehensive summary across all phases.

Layout: 2x2 quadrant
  Q1 (top-left)  : RDM/SRM + LOCO reminder (Stage A)
  Q2 (top-right) : Activation + decoder summary (this meeting's M3+M4 condensed)
  Q3 (bottom-left): Phase 2 model+loss summary
  Q4 (bottom-right): Phase 2 status + plans summary

Output: results/visualizations/meeting/slide1_summary.png
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np

SCRIPT = Path(__file__).resolve()
OUT = (SCRIPT.parents[1] / "results" / "visualizations" / "meeting" /
       "slide1_summary.png")
OUT.parent.mkdir(parents=True, exist_ok=True)

ACCENT = "#1f4e79"
ACCENT_SOFT = "#dde7f1"
GREEN = "#2e7d32"
AMBER = "#e6a23c"
RED = "#c0392b"
GREY = "#666"
BG = "#fafbfc"

def quadrant(ax, title, color=ACCENT):
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values(): s.set_visible(False)
    ax.add_patch(mpatches.Rectangle((0, 0.94), 1, 0.06, facecolor=color, edgecolor="none"))
    ax.text(0.015, 0.97, title, color="white", fontsize=11.5, fontweight="bold", va="center")

# ====================================================================== figure
fig = plt.figure(figsize=(13.33, 7.5), dpi=160, facecolor=BG)

# Header
hax = fig.add_axes([0.0, 0.93, 1.0, 0.07])
hax.axis("off")
hax.add_patch(mpatches.Rectangle((0, 0), 1, 1, facecolor=ACCENT, edgecolor="none"))
hax.text(0.012, 0.55, "Slide 1 — Project Summary  (CVD personalized inverse filter)",
         color="white", fontsize=15.5, fontweight="bold", va="center")
hax.text(0.012, 0.18, "Stage A reminder (RDM, LOCO)  ·  Activation & decoder  ·  Phase 2 model+loss  ·  Status",
         color="#cfd8e3", fontsize=9.5, va="center")
hax.text(0.988, 0.5, "2026-05-04", color="white", fontsize=10.5, ha="right", va="center", fontstyle="italic")

# Quadrant axes
left_x, right_x = 0.025, 0.515
top_y, bot_y = 0.485, 0.025
qw, qh = 0.46, 0.42
ax1 = fig.add_axes([left_x, top_y, qw, qh])
ax2 = fig.add_axes([right_x, top_y, qw, qh])
ax3 = fig.add_axes([left_x, bot_y, qw, qh])
ax4 = fig.add_axes([right_x, bot_y, qw, qh])

# ============================================================ Q1 RDM/LOCO
quadrant(ax1, "  Q1.  Stage A reminder  (RDM/SRM disparity  +  LOCO interpolation)")

# Two stat panels side-by-side
# Left: SRM disparity (Crawford-Howell individual)
ax1.text(0.025, 0.85, "SRM disparity  (HC vs CVD, LOO-consistent, 10K perm)",
         fontsize=9.5, color=ACCENT, fontweight="bold")
ax1.text(0.025, 0.81, "Group: V1 p=0.062 (g=1.16) · V2 p=0.075 (g=1.04)  — trending",
         fontsize=8.0, color="#222")
ax1.text(0.025, 0.78, "Crawford & Howell (1998) per-subject:",
         fontsize=8.5, color=ACCENT, style="italic")

# Mini per-subject CVD table
rows_srm = [
    ("sub-09 protan", "V1 t=3.5", "p=0.007**", GREEN),
    ("sub-08 deutan", "V2 t=2.1", "p=0.040*",  GREEN),
    ("sub-10 normal", "all ROIs", "n.s.",       GREY),
]
y0 = 0.74
for i, (sub, roi, p, col) in enumerate(rows_srm):
    yy = y0 - i * 0.045
    ax1.text(0.04, yy, sub, fontsize=8.0, color="#222", fontweight="bold")
    ax1.text(0.30, yy, roi, fontsize=8.0, color="#222")
    ax1.text(0.50, yy, p, fontsize=8.5, color=col, fontweight="bold")

# Divider
ax1.add_patch(mpatches.Rectangle((0.025, 0.575), 0.95, 0.002, facecolor="#ccc", edgecolor="none"))

# Bottom half: LOCO HC vs CVD (mini bar)
ax1.text(0.025, 0.55, "LOCO interpolation  (ridge_gcv voxel_corr, leakage-free)",
         fontsize=9.5, color=ACCENT, fontweight="bold")

mini = ax1.inset_axes([0.05, 0.08, 0.92, 0.42], transform=ax1.transAxes)
rois = ["V1", "V2", "V3", "hV4"]
hc = [0.130, 0.150, 0.023, 0.183]
cvd = [-0.012, -0.174, -0.008, -0.058]
ds = [1.61, 1.85, 0.14, 1.19]
ps = [0.021, 0.022, 0.819, 0.169]
xx = np.arange(4); w = 0.35
mini.bar(xx - w/2, hc, w, color="#9aa6b2", edgecolor="#444", linewidth=0.7,
         label="HC (n=7)")
mini.bar(xx + w/2, cvd, w, color="#f3b3b3", edgecolor="#a04040", linewidth=0.7,
         label="CVD (n=3)")
mini.axhline(0, color="#444", linewidth=0.5)
mini.axhline(0.10, color=AMBER, linestyle=":", linewidth=1.0, label="V1/V2 perm null")
for i, (d, p) in enumerate(zip(ds, ps)):
    sig = "**" if p < 0.01 else ("*" if p < 0.05 else "")
    if sig:
        mini.text(i, max(hc[i], 0) + 0.02, f"d={d:.2f}{sig}",
                  ha="center", fontsize=7.5, color=GREEN, fontweight="bold")
    elif d > 1:
        mini.text(i, max(hc[i], 0) + 0.02, f"d={d:.2f}",
                  ha="center", fontsize=7.5, color="#666")
mini.set_xticks(xx); mini.set_xticklabels(rois, fontsize=8.5, fontweight="bold")
mini.set_ylim(-0.30, 0.32)
mini.tick_params(axis="y", labelsize=7)
mini.legend(loc="lower right", fontsize=6.5, frameon=True)
mini.spines["top"].set_visible(False); mini.spines["right"].set_visible(False)
mini.grid(axis="y", linestyle=":", alpha=0.3)
mini.set_ylabel("voxel_corr", fontsize=7.5)

ax1.text(0.025, 0.04, "→ Discrimination (LORO) preserved; interpolation (LOCO) selectively lost in CVD.",
         fontsize=7.8, color=GREEN, style="italic", fontweight="bold")

# ============================================================ Q2 Activation + Decoder
quadrant(ax2, "  Q2.  Activation  +  Decoder vs baseline")

# Top half: activation
ax2.text(0.025, 0.87, "Activation  (per-color tuning, group magnitude)",
         fontsize=9.5, color=ACCENT, fontweight="bold")
ax2.text(0.025, 0.83, "All 4 ROIs: HC vs CVD mean |activation| n.s. (p > 0.3)",
         fontsize=8.5, color="#222")
ax2.text(0.025, 0.80, "Modulation depth (color-tuning amplitude): also n.s.",
         fontsize=8.5, color="#222")
ax2.text(0.025, 0.76,
         "→ CVD has NORMAL signal magnitude — deficit is geometric, not loss.",
         fontsize=8.5, color=GREEN, fontweight="bold", style="italic")

ax2.add_patch(mpatches.Rectangle((0.025, 0.71), 0.95, 0.002,
                                  facecolor="#ccc", edgecolor="none"))

# Bottom: decoder vs baselines
ax2.text(0.025, 0.68, "Decoder vs original-paper baselines",
         fontsize=9.5, color=ACCENT, fontweight="bold")

# Mini comparison chart
mini2 = ax2.inset_axes([0.04, 0.05, 0.92, 0.55], transform=ax2.transAxes)
labels = ["chance", "Raw\n(no align)", "FE+Procrustes\n(B&H 2009)", "LDA+SRM\n(OUR BEST)"]
vals   = [0.125, 0.135, 0.545, 0.793]
colors = ["#cccccc", "#bdbdbd", AMBER, GREEN]
bars = mini2.bar(range(4), vals, color=colors, edgecolor="#333", linewidth=0.6)
for i, (v, c) in enumerate(zip(vals, colors)):
    mini2.text(i, v + 0.025, f"{v:.3f}", ha="center", fontsize=8.5,
               fontweight="bold", color=c if c != "#cccccc" else "#666")
mini2.set_xticks(range(4))
mini2.set_xticklabels(labels, fontsize=7.8)
mini2.set_ylim(0, 0.95)
mini2.set_ylabel("LORO classification accuracy (8-color)", fontsize=8.0)
mini2.tick_params(axis="y", labelsize=7)
mini2.spines["top"].set_visible(False); mini2.spines["right"].set_visible(False)
mini2.grid(axis="y", linestyle=":", alpha=0.3)
mini2.set_title("HC→CVD cross-decoding p=0.668  →  shared mapping confirmed",
                fontsize=8.0, color=ACCENT, fontweight="bold", pad=4, loc="left")

# ============================================================ Q3 Model + Loss
quadrant(ax3, "  Q3.  Phase 2 model + loss  (3 forward maps · L_LOCO · selection)", color="#5a3a8a")

# 3 model micro-cards
models = [
    ("Machado 1-way", "1-DOF · retinal cone", "θ' = machado_shifted_hue(Δλ, family)", "#7a3d8a"),
    ("R+C", "2-DOF · retinal + cortical RG", "rg' = rg_b + (1+g)·(rg_ret − rg_b)", "#5a3a8a"),
    ("2-Component (★)", "2-DOF · cortical angular dilation", "θ' = θ + β_s·cos(θ−90°) + β_c·cos(θ−θ_conf)", "#3a3a8a"),
]
mw = 0.30; gap = 0.015
mx0 = 0.025
my = 0.86
mh = 0.20
for i, (name, mech, eq, col) in enumerate(models):
    x = mx0 + i * (mw + gap)
    box = FancyBboxPatch((x, my - mh), mw, mh,
                         boxstyle="round,pad=0.005,rounding_size=0.01",
                         linewidth=1.2, edgecolor=col, facecolor="white")
    ax3.add_patch(box)
    ax3.text(x + mw / 2, my - 0.025, name, ha="center", va="top",
             fontsize=9.0, fontweight="bold", color=col)
    ax3.text(x + mw / 2, my - 0.06, mech, ha="center", va="top",
             fontsize=7.2, color="#444", style="italic")
    ax3.text(x + mw / 2, my - 0.13, eq, ha="center", va="top",
             fontsize=7.0, color="#222", family="monospace")

# Loss equation card
lc_y = 0.55
ax3.add_patch(FancyBboxPatch((0.025, lc_y - 0.15), 0.95, 0.13,
                             boxstyle="round,pad=0.005,rounding_size=0.01",
                             facecolor="#f3f6fa", edgecolor=ACCENT, linewidth=1.0))
ax3.text(0.5, lc_y - 0.025, "L_fit  =  1.0·L_vuln  +  0.5·L_rank  +  0.2·L_rdm  +  0.1·L_smooth",
         ha="center", fontsize=9.5, color=ACCENT, fontweight="bold")
ax3.text(0.5, lc_y - 0.07,
         "L_vuln = MSE  ·  L_rank = 1−Spearman ρ  ·  L_rdm = 1−cos(ΔRDM)  ·  Null = 8! perm",
         ha="center", fontsize=7.5, color="#333")
ax3.text(0.5, lc_y - 0.115,
         "L_improve · L_no-harm  →  evaluation only, NOT in fit",
         ha="center", fontsize=7.0, color=GREY, style="italic")

# Selection criterion
ax3.text(0.025, 0.32,
         "Selection rule  =  LOCO-best descriptive fit  +  behavioral validation  (override authority).",
         fontsize=8.0, color="#222")
ax3.text(0.025, 0.28,
         "[NEW 2026-05-03]  Loss Inventory  (12 variants × HC sanity, Cycle 15 mw_jaccard cross-validates winners)",
         fontsize=7.8, color=AMBER, fontweight="bold")

# Pre-image / evaluation
ax3.text(0.025, 0.22, "Evaluation:",
         fontsize=8.5, color=ACCENT, fontweight="bold")
evals = [
    ("Pre-image search",   "exact 8/8 required, else REJECT model–subject combo"),
    ("Permutation test",    "label-perm 8! exact (40,320)"),
    ("L_improve sanity",    "post-fit: filter must improve LOCO over baseline"),
    ("HC sanity (loss inv)","emp_p ≤ 0.20 → CVD outlier above HC distribution"),
    ("Behavioral validation", "qualitative naming test = final arbiter (sub-08 §3 PASS)"),
]
for i, (k, v) in enumerate(evals):
    yy = 0.18 - i * 0.035
    ax3.text(0.04, yy, "•  " + k + ":", fontsize=7.5, color="#222", fontweight="bold")
    ax3.text(0.36, yy, v, fontsize=7.3, color="#444")

# ============================================================ Q4 Status + Plans
quadrant(ax4, "  Q4.  Status  +  next steps", color="#0d5132")

# Per-subject status (compact)
rows_st = [
    ("OK", GREEN, "sub-08 deutan",
     "2-comp (β_s=38°, β_c=−14°) hV4  ·  pre-image 8/8  ·  behav PASS (YG-C separability)"),
    ("…", AMBER, "sub-09 protan",
     "Phase A (6°, −22°) + [NEW] mw_jaccard (44°, +54°)  ·  pre-image 8/8  ·  behav PENDING"),
    ("X", RED, "sub-10 near-normal",
     "Excluded — no CVD-HC signal at any ROI"),
]
sy = 0.85
sh = 0.11
for i, (icon, ic, name, body) in enumerate(rows_st):
    yy = sy - i * (sh + 0.004)
    box = FancyBboxPatch((0.025, yy - sh), 0.95, sh,
                         boxstyle="round,pad=0.003,rounding_size=0.008",
                         linewidth=0.7, edgecolor="#ccc", facecolor="white")
    ax4.add_patch(box)
    ax4.add_patch(mpatches.Circle((0.06, yy - sh / 2), 0.018,
                                  facecolor=ic, edgecolor="none"))
    ax4.text(0.06, yy - sh / 2, icon, ha="center", va="center",
             fontsize=7.5, color="white", fontweight="bold")
    ax4.text(0.10, yy - 0.025, name, fontsize=8.5, fontweight="bold", color="#111")
    ax4.text(0.10, yy - 0.07, body, fontsize=7.3, color="#222")

# Limits
lim_y = 0.51
ax4.text(0.025, lim_y, "Critical limits  (descriptive only — Cycle 13 framework decision):",
         fontsize=8.5, color="#7a3d1f", fontweight="bold")
limits = [
    "Specificity abandoned (HC FPR 100%, baseline_ρ confound r=−0.894)  ·  HC pool n=6 effective at hV4  ·  8-color resolution cap",
]
for i, t in enumerate(limits):
    ax4.text(0.025, lim_y - 0.04 - i * 0.035, t, fontsize=7.3, color="#444")

# Next steps
ns_y = 0.41
ax4.text(0.025, ns_y, "Next steps  →  Phase 3:",
         fontsize=8.5, color=ACCENT, fontweight="bold")
nexts = [
    ("HIGH", GREEN, "Sub-09 behavioral", "4-way: Phase-A · mw_jaccard NEW · Cycle 12 · Machado"),
    ("HIGH", GREEN, "Sub-08 4-way + canonical (38, −14)", "selection rule choice 직접 검증"),
    ("MED",  AMBER, "Loss inventory v2 — HC fit", "Phase A canonical L_LOCO HC re-run (server pending)"),
    ("MED",  AMBER, "Sub-08 c8 magenta variant", "pre-image θ ∈ {290°, 300°, 310°}"),
    ("LOW",  GREY,  "Phase 2 closure document", "two subjects + behavioral evidence + framework limits"),
    ("→",    ACCENT, "Phase 3 trigger (post sub-09 PASS)", "JND + filtered-stim fMRI re-acquisition"),
]
for i, (badge, bcol, title, body) in enumerate(nexts):
    yy = ns_y - 0.04 - i * 0.060
    bw = 0.08
    ax4.add_patch(FancyBboxPatch((0.04, yy - 0.025), bw, 0.025,
                                 boxstyle="round,pad=0.001,rounding_size=0.005",
                                 facecolor=bcol, edgecolor="none"))
    ax4.text(0.04 + bw / 2, yy - 0.013, badge, ha="center", va="center",
             fontsize=6.5, color="white", fontweight="bold")
    ax4.text(0.135, yy - 0.005, title, fontsize=7.5, fontweight="bold", color="#111")
    ax4.text(0.135, yy - 0.030, body, fontsize=6.8, color="#444")

# Footer
fig.text(0.5, 0.005,
         "Detail in Slides 2 (activation + decoder), 3 (model + loss), 4 (status + behavioral + plans)",
         ha="center", fontsize=7.5, color=GREY, style="italic", fontweight="bold")

plt.savefig(OUT, dpi=160, bbox_inches="tight", facecolor=BG)
print(f"saved → {OUT}")
