"""Generate one-page advisor-meeting overview figure for future_phase2.

Layout: 2x2 quadrant + header band.
- Q1 (top-left): pipeline schematic
- Q2 (top-right): models + loss equation card
- Q3 (bottom-left): per-subject status + framework limits
- Q4 (bottom-right): next steps / phase 3 trigger

Output: results/visualizations/meeting/phase2_meeting_overview.png
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "visualizations" / "meeting" / "phase2_meeting_overview.png"
OUT.parent.mkdir(parents=True, exist_ok=True)

ACCENT = "#1f4e79"
ACCENT_SOFT = "#dde7f1"
GREY = "#666666"
GREEN = "#2e7d32"
AMBER = "#e6a23c"
RED = "#c0392b"
BG = "#fafbfc"


def quadrant(ax, title, color=ACCENT):
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    # title strip
    ax.add_patch(mpatches.Rectangle((0, 0.94), 1, 0.06, facecolor=color, edgecolor="none"))
    ax.text(0.015, 0.97, title, color="white", fontsize=11.5, fontweight="bold", va="center")


def chip(ax, x, y, w, h, label, fill=ACCENT_SOFT, edge=ACCENT, text=ACCENT, fs=8.5, weight="bold"):
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.005,rounding_size=0.012",
                         linewidth=1.0, edgecolor=edge, facecolor=fill)
    ax.add_patch(box)
    ax.text(x + w / 2, y + h / 2, label, ha="center", va="center",
            fontsize=fs, color=text, fontweight=weight)


def arrow(ax, x1, y1, x2, y2, color=ACCENT, lw=1.6):
    a = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="->,head_length=4,head_width=3",
                        color=color, lw=lw, mutation_scale=10)
    ax.add_patch(a)


# ---------------------------------------------------------------- figure
fig = plt.figure(figsize=(13.33, 7.5), dpi=160, facecolor=BG)

# Header band
hax = fig.add_axes([0.0, 0.93, 1.0, 0.07])
hax.axis("off")
hax.add_patch(mpatches.Rectangle((0, 0), 1, 1, facecolor=ACCENT, edgecolor="none"))
hax.text(0.012, 0.55, "Phase 2 — Personalized Inverse Filter for CVD",
         color="white", fontsize=15.5, fontweight="bold", va="center")
hax.text(0.012, 0.18, "Pipeline · Models · Status · Next   |   phase5_filter_optimization",
         color="#cfd8e3", fontsize=9.5, va="center")
hax.text(0.988, 0.5, "2026-05-04", color="white", fontsize=10.5, ha="right", va="center", fontstyle="italic")

# Quadrant axes (2x2 grid below header)
left_x, right_x = 0.025, 0.515
top_y, bot_y = 0.485, 0.025
qw, qh = 0.46, 0.42
ax1 = fig.add_axes([left_x, top_y, qw, qh])
ax2 = fig.add_axes([right_x, top_y, qw, qh])
ax3 = fig.add_axes([left_x, bot_y, qw, qh])
ax4 = fig.add_axes([right_x, bot_y, qw, qh])

# ============================================================ Q1 Pipeline
quadrant(ax1, "  Q1.  Pipeline  (Distortion Fit  →  Filter Derive  →  Verify)")

# 3 phase boxes
phases = [
    ("Phase A", "Distortion fit", ["hV4 LOCO target", "ridge_gcv W retrain", "shift_at_both", "→ δ_fit(θ)"]),
    ("Phase B", "Filter derive", ["δ_filter = −δ_fit", "+ no-harm", "+ smoothness", "→ pre-image (8/8)"]),
    ("Phase C", "Verify", ["label-perm p", "L_improve sanity", "HC sanity (loss inv)", "behavioral test"]),
]
n = 3
gap = 0.02
boxw = (1 - 2 * 0.025 - (n - 1) * gap) / n
ystart = 0.55
boxh = 0.34
for i, (tag, name, lines) in enumerate(phases):
    x = 0.025 + i * (boxw + gap)
    box = FancyBboxPatch((x, ystart - boxh), boxw, boxh,
                         boxstyle="round,pad=0.003,rounding_size=0.018",
                         linewidth=1.3, edgecolor=ACCENT, facecolor="white")
    ax1.add_patch(box)
    ax1.text(x + boxw / 2, ystart - 0.03, tag, ha="center", va="top",
             fontsize=10.5, color=ACCENT, fontweight="bold")
    ax1.text(x + boxw / 2, ystart - 0.075, name, ha="center", va="top",
             fontsize=9.5, color="#222", fontweight="bold")
    for j, ln in enumerate(lines):
        ax1.text(x + 0.018, ystart - 0.13 - j * 0.05, "•  " + ln,
                 ha="left", va="top", fontsize=8.0, color="#333")
    if i < n - 1:
        ax1.annotate("", xy=(x + boxw + gap, ystart - boxh / 2 - 0.02),
                     xytext=(x + boxw, ystart - boxh / 2 - 0.02),
                     arrowprops=dict(arrowstyle="->", color=ACCENT, lw=1.6))

# Inputs / outputs
ax1.text(0.025, 0.13, "Inputs",
         fontsize=8.5, fontweight="bold", color=GREY)
ax1.text(0.025, 0.085, "C010 amplitudes (6×8×V) · HC W (n=6 eff. hV4) · ΔRDM_obs · Stockman",
         fontsize=8.0, color="#333")
ax1.text(0.025, 0.04, "Output",
         fontsize=8.5, fontweight="bold", color=GREY)
ax1.text(0.025, 0.005, "δ_filter(θ) per subject — stimulus-space hue correction",
         fontsize=8.0, color="#333", fontweight="bold")

# ============================================================ Q2 Models + Loss
quadrant(ax2, "  Q2.  Models  (3 fixed)  +  Loss  (L_LOCO, hV4)")

# Table
hdr = ["Model", "DOF", "Mechanism", "sub-08 hV4", "sub-09 hV4"]
rows = [
    ["Machado 1-way", "1", "retinal cone", "p = 0.036 *", "p = 0.018 *"],
    ["R+C", "2", "retinal + RG gain", "p = 0.005 ** (behav FAIL)", "—"],
    ["2-Component", "2", "cortical (β_s, β_c)", "p = 0.004 ** (behav PASS)", "p = 0.035 *"],
]
col_x = [0.030, 0.235, 0.305, 0.500, 0.780]
col_w = [0.205, 0.070, 0.195, 0.280, 0.210]
y_hdr = 0.78
ax2.add_patch(mpatches.Rectangle((0.02, y_hdr - 0.005), 0.96, 0.045,
                                 facecolor=ACCENT_SOFT, edgecolor="none"))
for x, w, h in zip(col_x, col_w, hdr):
    ax2.text(x + 0.005, y_hdr + 0.013, h, fontsize=8.5, fontweight="bold", color=ACCENT)

row_y = y_hdr - 0.05
for r, row in enumerate(rows):
    yy = row_y - r * 0.055
    if r == 2:  # 2-component highlight
        ax2.add_patch(mpatches.Rectangle((0.02, yy - 0.018), 0.96, 0.05,
                                         facecolor="#fff8e1", edgecolor="#e6a23c", linewidth=0.8))
    for x, w, val in zip(col_x, col_w, row):
        weight = "bold" if (r == 2) else "normal"
        ax2.text(x + 0.005, yy, val, fontsize=8.0, color="#222", fontweight=weight, va="bottom")

# Loss card
lc_y = 0.36
ax2.add_patch(FancyBboxPatch((0.04, lc_y - 0.21), 0.92, 0.18,
                             boxstyle="round,pad=0.006,rounding_size=0.012",
                             facecolor="#f3f6fa", edgecolor=ACCENT, linewidth=1.2))
ax2.text(0.5, lc_y - 0.025, "L_fit  =  1.0·L_vuln  +  0.5·L_rank  +  0.2·L_rdm  +  0.1·L_smooth",
         ha="center", fontsize=10.5, color=ACCENT, fontweight="bold")
ax2.text(0.5, lc_y - 0.07,
         "L_vuln = MSE(v_sim, v_CVD)   ·   L_rank = 1 − Spearman ρ   ·   L_rdm = 1 − cos(ΔRDM_sim, ΔRDM_obs)",
         ha="center", fontsize=8.2, color="#333")
ax2.text(0.5, lc_y - 0.105,
         "L_smooth = Σ (δ(c+1) − δ(c))²        Null: 8! exact label permutation (40,320)",
         ha="center", fontsize=8.2, color="#333")
ax2.text(0.5, lc_y - 0.16,
         "L_improve · L_no-harm  →  evaluation / derivation only, NOT in fit loss",
         ha="center", fontsize=7.8, color=GREY, style="italic")
ax2.text(0.5, lc_y - 0.195,
         "[NEW 2026-05-03]  Loss Inventory: 12 variants × HC sanity check (Cycle 15)",
         ha="center", fontsize=7.8, color=AMBER, fontweight="bold")

# Bottom note
ax2.text(0.025, 0.02, "Models fixed by assumption A2 — no addition/removal.",
         fontsize=7.6, color=GREY, style="italic")

# ============================================================ Q3 Status × Limits
quadrant(ax3, "  Q3.  Per-Subject Status  ×  Framework Limits", color="#7a3d1f")

# Subject status — 3 cards
sub_y = 0.78
sub_h = 0.16
sub_data = [
    ("OK", GREEN, "sub-08 deutan", "Canonical: 2-comp (β_s=38°, β_c=−14°) hV4",
     "behav PASS (YG-C separability) · pre-image 8/8 exact",
     "Cross-val: (68°, −38°) confirmed by Cycle 12 + Cycle 15 mw_jaccard"),
    ("…", AMBER, "sub-09 protan", "Phase A: 2-comp (β_s=6°, β_c=−22°) hV4 — pre-image 8/8 exact",
     "[NEW] Cycle 15 mw_jaccard winner: (β_s=44°, β_c=+54°) — emp_p=0.17",
     "Behavioral validation pending — multi-candidate 4-way comparison"),
    ("X", RED, "sub-10 near-normal", "Excluded — no CVD-HC signal at any ROI",
     "—", "—"),
]
for i, (icon, ic, name, l1, l2, l3) in enumerate(sub_data):
    yy = sub_y - i * (sub_h + 0.005)
    box = FancyBboxPatch((0.025, yy - sub_h), 0.95, sub_h,
                         boxstyle="round,pad=0.003,rounding_size=0.012",
                         linewidth=0.8, edgecolor="#cccccc", facecolor="white")
    ax3.add_patch(box)
    # icon disk
    ax3.add_patch(mpatches.Circle((0.06, yy - sub_h / 2), 0.022,
                                  facecolor=ic, edgecolor="none"))
    ax3.text(0.06, yy - sub_h / 2, icon, ha="center", va="center",
             fontsize=8.5, color="white", fontweight="bold")
    ax3.text(0.10, yy - 0.025, name, fontsize=9.5, fontweight="bold", color="#111")
    ax3.text(0.10, yy - 0.065, l1, fontsize=8.0, color="#222")
    if l2 != "—":
        ax3.text(0.10, yy - 0.097, l2, fontsize=7.8, color="#222")
    if l3 != "—":
        ax3.text(0.10, yy - 0.128, l3, fontsize=7.6, color=GREY, style="italic")

# Limits
lim_y = 0.27
ax3.text(0.025, lim_y, "Critical framework limits",
         fontsize=9.5, fontweight="bold", color="#7a3d1f")
limits = [
    "1.  Specificity abandoned — HC FPR 100%, baseline_ρ confound r = −0.894 (Cycle 13). 13 reformulations, no net gain. Descriptive only.",
    "2.  HC pool n = 6 effective at hV4 (sub-07: 16 voxels → nan). Statistical specificity claim infeasible.",
    "3.  8-color resolution caps narrow-band recovery (c2 orange 45°, c8 magenta 315°) — fine-grid B1 confirmed unreachable.",
]
for i, t in enumerate(limits):
    ax3.text(0.025, lim_y - 0.045 - i * 0.04, t, fontsize=7.7, color="#333")

# ============================================================ Q4 Next steps
quadrant(ax4, "  Q4.  Next Steps  →  Phase 3 trigger", color="#0d5132")

steps = [
    ("HIGH", GREEN, "Sub-09 behavioral session",
     "4-way comparison: Phase-A (6, −22) · mw_jaccard (44, +54) · Cycle 12 (30, +26) · Machado",
     "Gates Phase-2 closure — model class confirmation pending"),
    ("HIGH", GREEN, "Sub-08 4-way + canonical",
     "V4-only (38, +7) · V1+V4 avg (19, +3.5) · Cycle 12 (68, −38) · §3 canonical (38, −14)",
     "Validates selection rule choice; canonical is reference baseline"),
    ("MED", AMBER, "Loss inventory v2 — HC fit",
     "Phase A canonical L_LOCO HC (sub-01~07, V1, hV4) — server re-run pending",
     "Closes loss inventory completeness gap"),
    ("MED", AMBER, "Sub-08 c8 magenta variant",
     "Pre-image θ ∈ {290°, 300°, 310°} — close residual magenta bias",
     "B2 viz already generated"),
    ("LOW", GREY, "Phase 2 closure document",
     "Two subjects, final filters, behavioral evidence, framework limits — pre-Phase 3 deliverable",
     ""),
    ("NEXT", ACCENT, "Phase 3 trigger (post sub-09 PASS)",
     "JND + filtered-stimulus fMRI re-acquisition · sub-09 V4-only filter",
     ""),
]

step_y = 0.83
step_h = 0.13
for i, (badge, bcol, title, body, sub) in enumerate(steps):
    yy = step_y - i * (step_h + 0.005)
    box = FancyBboxPatch((0.025, yy - step_h), 0.95, step_h,
                         boxstyle="round,pad=0.003,rounding_size=0.010",
                         linewidth=0.8, edgecolor="#cccccc", facecolor="white")
    ax4.add_patch(box)
    # badge
    bw = 0.08
    ax4.add_patch(FancyBboxPatch((0.04, yy - 0.085), bw, 0.04,
                                 boxstyle="round,pad=0.002,rounding_size=0.006",
                                 facecolor=bcol, edgecolor="none"))
    ax4.text(0.04 + bw / 2, yy - 0.065, badge, ha="center", va="center",
             fontsize=7.5, color="white", fontweight="bold")
    # text
    ax4.text(0.135, yy - 0.025, title, fontsize=9.0, fontweight="bold", color="#111")
    ax4.text(0.135, yy - 0.06, body, fontsize=7.6, color="#222")
    if sub:
        ax4.text(0.135, yy - 0.092, sub, fontsize=7.2, color=GREY, style="italic")

# Footer
fig.text(0.5, 0.005,
         "References — phase5_filter_optimization/CLAUDE.md §0–§8 · behav_validation.md §3 · loss_inventory.md (Cycle 15) · LOCO_FILTER_PLAN.md",
         ha="center", fontsize=7.0, color=GREY, style="italic")

plt.savefig(OUT, dpi=160, bbox_inches="tight", facecolor=BG)
print(f"saved → {OUT}")
