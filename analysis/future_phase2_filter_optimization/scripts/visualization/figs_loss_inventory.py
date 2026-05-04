"""Loss-inventory HC sanity supporting figure for advisor meeting.

Renders 3 panels:
  Left: per-loss HC vs CVD norm distribution (key losses only)
  Right-top: best (β_s, β_c) candidates per subject (scatter on parameter space)
  Right-bot: HC sanity verdict matrix (✓✓ / ✓ / ✗ for top 6 losses)

Source: results/inventory/loss_inventory.csv  +  loss_inventory.md (rank-based emp_p stats)

Output: results/visualizations/meeting/loss_inventory_summary.png
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "results" / "inventory" / "loss_inventory.csv"
OUT = ROOT / "results" / "visualizations" / "meeting" / "loss_inventory_summary.png"
OUT.parent.mkdir(parents=True, exist_ok=True)

ACCENT = "#1f4e79"
GREEN = "#2e7d32"
AMBER = "#e6a23c"
RED = "#c0392b"
GREY = "#888888"
HC_COL = "#9aa6b2"
CVD08 = "#1f77b4"
CVD09 = "#d62728"
BG = "#fafbfc"

df = pd.read_csv(SRC)

# Selected loss variants (most informative spectrum)
loss_order = [
    "cycle15_opt2_v4mwj_v1lrank",  # ✓✓ winner
    "mw_jaccard_loss",              # ✓✓
    "cycle12_cross_roi",            # ✓ partial (sub-08 perfect)
    "spearman_r",                   # ✓ partial
    "l_topk_jaccard",               # ✗ neither distinct
    "sign_agree",                   # ✗ neither distinct
]

# Verdict per loss (from loss_inventory.md table)
verdict = {
    "cycle15_opt2_v4mwj_v1lrank": ("PASS+", GREEN, "both CVD distinct"),
    "mw_jaccard_loss":            ("PASS+", GREEN, "both CVD distinct"),
    "cycle12_cross_roi":          ("PASS",  AMBER, "sub-08 perfect, sub-09 marginal"),
    "spearman_r":                 ("PASS",  AMBER, "sub-08 only"),
    "l_topk_jaccard":             ("FAIL",  RED,   "neither distinct"),
    "sign_agree":                 ("FAIL",  RED,   "neither distinct"),
}

# emp_p values (sub-08, sub-09)
emp_p = {
    "cycle15_opt2_v4mwj_v1lrank": (0.00, 0.17),
    "mw_jaccard_loss":            (0.17, 0.17),
    "cycle12_cross_roi":          (0.00, 0.33),
    "spearman_r":                 (0.17, 0.50),
    "l_topk_jaccard":             (0.33, 0.83),
    "sign_agree":                 (0.67, 0.67),
}

# ============================================================ figure
fig = plt.figure(figsize=(14.0, 8.0), dpi=160, facecolor=BG)
fig.suptitle("Loss Inventory + HC Sanity Check  —  Cycle 15 (mw_jaccard) winners cross-validated",
             fontsize=14, fontweight="bold", color=ACCENT, y=0.965)
fig.text(0.5, 0.925,
         "A 'useful' loss should give HC ≈ (0, 0) and CVD ≠ (0, 0).  "
         "Rank-based emp_p ≤ 0.20  =>  CVD outlier above HC distribution.  "
         "PASS+ = both CVD distinct from HC.",
         ha="center", fontsize=9.5, color="#444", style="italic")

# Left panel: distribution of (β_s, β_c) norms per loss
ax_l = fig.add_axes([0.055, 0.10, 0.48, 0.74])
y_positions = np.arange(len(loss_order))[::-1]

for i, loss in enumerate(loss_order):
    yp = y_positions[i]
    sub = df[df.loss_variant == loss]
    hc = sub[sub.role == "HC"].norm_raw.values
    cvd08 = sub[sub.subject == "sub-08"].norm_raw.values
    cvd09 = sub[sub.subject == "sub-09"].norm_raw.values

    # HC dots
    ax_l.scatter(hc, [yp] * len(hc), s=42, color=HC_COL, alpha=0.65,
                 edgecolor="white", linewidth=0.6, zorder=3, label="HC" if i == 0 else None)
    # HC mean
    if len(hc) > 0:
        ax_l.scatter([hc.mean()], [yp], marker="|", s=300, color="#444",
                     linewidth=2, zorder=4)
    # CVD
    if len(cvd08) > 0:
        ax_l.scatter(cvd08, [yp + 0.18], s=110, color=CVD08, marker="D",
                     edgecolor="white", linewidth=0.8, zorder=5,
                     label="sub-08 (deutan)" if i == 0 else None)
    if len(cvd09) > 0:
        ax_l.scatter(cvd09, [yp - 0.18], s=110, color=CVD09, marker="s",
                     edgecolor="white", linewidth=0.8, zorder=5,
                     label="sub-09 (protan)" if i == 0 else None)

    # verdict tag
    sym, col, _ = verdict[loss]
    ax_l.add_patch(mpatches.Rectangle((-25, yp - 0.35), 22, 0.7,
                                       facecolor=col, edgecolor="none", alpha=0.18))
    ax_l.text(-14, yp, sym, ha="center", va="center",
              fontsize=8.5, color=col, fontweight="bold")

ax_l.set_yticks(y_positions)
ax_l.set_yticklabels([l.replace("_", "\n") if len(l) > 18 else l for l in loss_order],
                     fontsize=8.5)
ax_l.set_xlabel("‖ (β_s, β_c) ‖   (degrees)", fontsize=10, color="#222")
ax_l.set_xlim(-30, 130)
ax_l.set_ylim(-0.7, len(loss_order) - 0.3)
ax_l.spines["top"].set_visible(False)
ax_l.spines["right"].set_visible(False)
ax_l.grid(axis="x", linestyle=":", alpha=0.4, zorder=1)
ax_l.legend(loc="upper right", fontsize=8.5, frameon=True, framealpha=0.9)
ax_l.set_title("Per-loss best-fit norm distribution  (HC pool n=6  vs  CVD)",
               fontsize=10.5, color=ACCENT, fontweight="bold", loc="left", pad=8)

# Right-top panel: parameter scatter for top 4 losses
ax_rt = fig.add_axes([0.605, 0.55, 0.36, 0.30])
ax_rt.set_title("CVD candidate filters in (β_s, β_c) plane  —  top 4 losses",
                fontsize=10.5, color=ACCENT, fontweight="bold", loc="left", pad=8)

# Plot HC pool of cycle15_opt2 as background
hc_ref = df[(df.loss_variant == "cycle15_opt2_v4mwj_v1lrank") & (df.role == "HC")]
ax_rt.scatter(hc_ref.beta_s, hc_ref.beta_c, s=45, color=HC_COL, alpha=0.55,
              edgecolor="white", linewidth=0.6, label="HC (cycle15_opt2)", zorder=2)

cands = [
    ("Phase A (canonical)", "sub-08", 38, -14, "o", CVD08, "behav PASS"),
    ("Phase A LOCO",        "sub-09",  6, -22, "o", CVD09, ""),
    ("Cycle 12 cross-ROI",  "sub-08", 68, -38, "D", CVD08, ""),
    ("Cycle 12 cross-ROI",  "sub-09", 30,  26, "D", CVD09, ""),
    ("mw_jaccard winner",   "sub-08", 58, -36, "*", CVD08, ""),
    ("mw_jaccard winner",   "sub-09", 44,  54, "*", CVD09, "NEW"),
    ("Cycle 15 opt2 PASS+", "sub-08", 68, -38, "P", CVD08, ""),
    ("Cycle 15 opt2 PASS+", "sub-09", 44,  54, "P", CVD09, "NEW"),
]
seen_labels = set()
for src, sub, bs, bc, mk, col, tag in cands:
    label = f"{sub}: {src}" if (sub, src) not in seen_labels else None
    seen_labels.add((sub, src))
    ax_rt.scatter([bs], [bc], s=140, marker=mk, color=col,
                  edgecolor="black", linewidth=0.7, alpha=0.85, zorder=4)
    if tag == "NEW":
        ax_rt.annotate(f"NEW\n({bs}°,{bc:+}°)",
                       xy=(bs, bc), xytext=(bs + 8, bc + 8),
                       fontsize=7.5, color=AMBER, fontweight="bold",
                       arrowprops=dict(arrowstyle="-", color=AMBER, lw=0.8))
    elif tag == "behav PASS":
        ax_rt.annotate(f"canonical\n({bs}°,{bc:+}°)",
                       xy=(bs, bc), xytext=(bs - 30, bc - 12),
                       fontsize=7.5, color=GREEN, fontweight="bold",
                       arrowprops=dict(arrowstyle="-", color=GREEN, lw=0.8))

ax_rt.axhline(0, color="#bbb", linestyle=":", linewidth=0.8)
ax_rt.axvline(0, color="#bbb", linestyle=":", linewidth=0.8)
ax_rt.set_xlabel("β_s  (S-cone axis dilation, deg)", fontsize=9.5)
ax_rt.set_ylabel("β_c  (confusion-axis rotation, deg)", fontsize=9.5)
ax_rt.set_xlim(-15, 90)
ax_rt.set_ylim(-55, 70)
ax_rt.spines["top"].set_visible(False)
ax_rt.spines["right"].set_visible(False)
ax_rt.grid(linestyle=":", alpha=0.4)

# legend (custom)
import matplotlib.lines as mlines
leg_handles = [
    mlines.Line2D([], [], color=HC_COL, marker="o", linestyle="none", markersize=7,
                  markeredgecolor="white", label="HC pool (n=6)"),
    mlines.Line2D([], [], color=CVD08,  marker="o", linestyle="none", markersize=7,
                  markeredgecolor="black", label="sub-08 deutan"),
    mlines.Line2D([], [], color=CVD09,  marker="o", linestyle="none", markersize=7,
                  markeredgecolor="black", label="sub-09 protan"),
]
ax_rt.legend(handles=leg_handles, loc="lower right", fontsize=7.5, frameon=True)

# Right-bot panel: emp_p verdict table
ax_rb = fig.add_axes([0.605, 0.085, 0.36, 0.38])
ax_rb.axis("off")
ax_rb.text(0.0, 1.005, "HC sanity verdict   (emp_p <= 0.20  =>  CVD distinct from HC)",
           fontsize=10.5, color=ACCENT, fontweight="bold",
           transform=ax_rb.transAxes, ha="left", va="bottom")

col_x = [0.0, 0.50, 0.66, 0.82]
col_w = [0.50, 0.16, 0.16, 0.18]
hdr_y = 0.80
ax_rb.add_patch(mpatches.Rectangle((-0.005, hdr_y - 0.04), 1.005, 0.07,
                                   facecolor=ACCENT, edgecolor="none"))
for x, h in zip(col_x, ["Loss variant", "sub-08 emp_p", "sub-09 emp_p", "Verdict"]):
    ax_rb.text(x + 0.005, hdr_y - 0.005, h, fontsize=9, fontweight="bold",
               color="white", va="center")

for i, loss in enumerate(loss_order):
    yy = hdr_y - 0.10 - i * 0.125
    if i % 2 == 1:
        ax_rb.add_patch(mpatches.Rectangle((-0.005, yy - 0.05), 1.005, 0.10,
                                           facecolor="#f1f4f7", edgecolor="none"))
    sym, col, descr = verdict[loss]
    p08, p09 = emp_p[loss]

    nm = loss.replace("_", " ").replace("v4mwj v1lrank", "v4-mwj + v1-rank")
    ax_rb.text(col_x[0] + 0.005, yy + 0.015, nm, fontsize=8.0, color="#222",
               fontweight="bold" if sym == "✓✓" else "normal")
    ax_rb.text(col_x[0] + 0.005, yy - 0.022, descr, fontsize=7.0, color=GREY, style="italic")

    pcol08 = GREEN if p08 <= 0.20 else (AMBER if p08 <= 0.50 else RED)
    pcol09 = GREEN if p09 <= 0.20 else (AMBER if p09 <= 0.50 else RED)
    ax_rb.text(col_x[1] + col_w[1] / 2, yy, f"{p08:.2f}", fontsize=10,
               color=pcol08, fontweight="bold", ha="center", va="center")
    ax_rb.text(col_x[2] + col_w[2] / 2, yy, f"{p09:.2f}", fontsize=10,
               color=pcol09, fontweight="bold", ha="center", va="center")
    ax_rb.text(col_x[3] + col_w[3] / 2, yy, sym, fontsize=10,
               color=col, fontweight="bold", ha="center", va="center")

ax_rb.set_xlim(0, 1)
ax_rb.set_ylim(0, 1)

fig.text(0.5, 0.02,
         "Source: results/inventory/loss_inventory.{md,csv}  ·  build_loss_inventory.py  ·  10000-resample bootstrap on HC means",
         ha="center", fontsize=7.5, color=GREY, style="italic")

plt.savefig(OUT, dpi=160, bbox_inches="tight", facecolor=BG)
print(f"saved → {OUT}")
