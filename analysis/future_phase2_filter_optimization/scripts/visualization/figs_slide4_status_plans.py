"""Slide 4 — Status, behavioral evidence, plans.

Layout:
  Section 1 (~28%): Per-subject status (3 subject cards: sub-08 / sub-09 / sub-10)
  Section 2 (~30%): Behavioral evidence detail
                     - sub-08 §3 PASS verdict matrix (R+C vs 2-comp by stim pair)
                     - sub-09 PENDING protocol summary
  Section 3 (~30%): Limits + next steps + Phase 3 trigger

Output: results/visualizations/meeting/slide4_status_plans.png
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "visualizations" / "meeting" / "slide4_status_plans.png"
OUT.parent.mkdir(parents=True, exist_ok=True)

ACCENT = "#1f4e79"
GREEN  = "#2e7d32"
AMBER  = "#e6a23c"
RED    = "#c0392b"
GREY   = "#666"
BG     = "#fafbfc"

# ====================================================================== figure
fig = plt.figure(figsize=(13.5, 8.5), dpi=160, facecolor=BG)

# Header
hax = fig.add_axes([0.0, 0.94, 1.0, 0.06])
hax.axis("off")
hax.add_patch(mpatches.Rectangle((0, 0), 1, 1, facecolor=ACCENT, edgecolor="none"))
hax.text(0.012, 0.55, "Slide 4 — Current status  ·  behavioral evidence  ·  next steps",
         color="white", fontsize=14.5, fontweight="bold", va="center")
hax.text(0.012, 0.18, "Per-subject status  |  sub-08 §3 behavioral PASS detail  |  Critical limits  |  Phase 3 trigger",
         color="#cfd8e3", fontsize=9.5, va="center")

# =================================== Section 1: per-subject status
ax_st = fig.add_axes([0.025, 0.66, 0.95, 0.27])
ax_st.set_xlim(0, 1); ax_st.set_ylim(0, 1)
ax_st.axis("off")
ax_st.text(0.005, 0.96, "1.  Per-subject status",
           fontsize=11.5, color=ACCENT, fontweight="bold")

subjects = [
    {"icon": "OK", "color": GREEN, "name": "sub-08 deutan",
     "filter": "Canonical:  2-comp  (β_s = 38°,  β_c = −14°)  @ hV4",
     "stats":  "LOCO ρ = 0.881   ·   label-perm p = 0.004 **   ·   pre-image 8/8 exact",
     "behav":  "§3 PASS — YG-C 4-way collapse 해소 (c3/c4, c5/c6, c5/c6/c7 distinct)",
     "extra":  "Cross-val: (68°, −38°) by Cycle 12 + Cycle 15 mw_jaccard"},
    {"icon": "…", "color": AMBER, "name": "sub-09 protan",
     "filter": "Phase A:  (β_s = 6°,  β_c = −22°)   |   [NEW]  mw_jaccard:  (β_s = 44°,  β_c = +54°)",
     "stats":  "LOCO ρ = 0.690   ·   label-perm p = 0.035 *   ·   pre-image 8/8 exact",
     "behav":  "PENDING — multi-candidate behavioral protocol",
     "extra":  "mw_jaccard winner emp_p = 0.17 → cross-validated"},
    {"icon": "X", "color": RED, "name": "sub-10 near-normal",
     "filter": "—",
     "stats":  "—",
     "behav":  "Excluded — no CVD-HC signal at any ROI",
     "extra":  ""},
]
sw = 0.31; sgap = 0.018
sx0 = 0.005
sy_top = 0.88; sh = 0.72
for i, s in enumerate(subjects):
    x = sx0 + i * (sw + sgap)
    box = FancyBboxPatch((x, sy_top - sh), sw, sh,
                         boxstyle="round,pad=0.005,rounding_size=0.012",
                         linewidth=1.0, edgecolor=s["color"], facecolor="white")
    ax_st.add_patch(box)
    # icon disk
    ax_st.add_patch(mpatches.Circle((x + 0.025, sy_top - 0.05), 0.022,
                                     facecolor=s["color"], edgecolor="none"))
    ax_st.text(x + 0.025, sy_top - 0.05, s["icon"], ha="center", va="center",
               fontsize=8.5, color="white", fontweight="bold")
    ax_st.text(x + 0.060, sy_top - 0.045, s["name"],
               fontsize=10.5, fontweight="bold", color="#111", va="center")
    # body
    ax_st.text(x + 0.012, sy_top - 0.16, "Filter:",
               fontsize=7.8, color=GREY, fontweight="bold")
    ax_st.text(x + 0.012, sy_top - 0.20, s["filter"],
               fontsize=7.5, color="#222", family="monospace")
    ax_st.text(x + 0.012, sy_top - 0.30, "Stats:",
               fontsize=7.8, color=GREY, fontweight="bold")
    ax_st.text(x + 0.012, sy_top - 0.335, s["stats"],
               fontsize=7.4, color="#222")
    ax_st.text(x + 0.012, sy_top - 0.43, "Behavioral:",
               fontsize=7.8, color=GREY, fontweight="bold")
    ax_st.text(x + 0.012, sy_top - 0.465, s["behav"],
               fontsize=7.4, color=s["color"], fontweight="bold")
    if s["extra"]:
        ax_st.text(x + 0.012, sy_top - 0.585, s["extra"],
                   fontsize=7.0, color="#444", style="italic")

# =================================== Section 2: Behavioral evidence
ax_b = fig.add_axes([0.025, 0.345, 0.95, 0.30])
ax_b.set_xlim(0, 1); ax_b.set_ylim(0, 1)
ax_b.axis("off")
ax_b.text(0.005, 0.96, "2.  Behavioral evidence  —  ground truth for filter selection",
          fontsize=11.5, color=ACCENT, fontweight="bold")

# Left: sub-08 §3 verdict matrix
ax_b.text(0.005, 0.86, "Sub-08 §3 PASS  (2026-04-17)  —  R+C vs 2-component head-to-head",
          fontsize=9.5, color=GREEN, fontweight="bold")

# Verdict table (R+C → 2-comp transitions)
verdicts = [
    ("c3 vs c4 (yellow / yel-grn)",
     "BLOB: merged",          RED,
     "distinct (연두 / warm ivory)",  GREEN, "★"),
    ("c5 vs c6 (cyan / blu-cy)",
     "BLOB: merged",          RED,
     "distinct (sky / dark sky)",   GREEN, "★"),
    ("c5 / c6 / c7 gradient",
     "no order (collapse)",   RED,
     "ordinal sky → dark sky → deep blue", GREEN, "★"),
    ("sRGB G / Y / c3 / c4",
     "4-way collapse",        RED,
     "2-way merge at most",   GREEN, "★"),
    ("c1 (red), protan-axis+",
     "preserved (red)",       GREEN,
     "preserved (red)",       GREEN, "="),
    ("c2 (orange) — narrow band",
     "pale / washed",         AMBER,
     "연두/초록 (~40° miss)",  AMBER, "≈"),
    ("c8 (magenta) — narrow band",
     "preserved (magenta)",   GREEN,
     "darker sky (blue-leaning)", AMBER, "✗"),
]

# Header strip
hy = 0.78
ax_b.add_patch(mpatches.Rectangle((0.005, hy - 0.04), 0.45, 0.05,
                                   facecolor=ACCENT, edgecolor="none"))
ax_b.text(0.020, hy - 0.015, "Stim pair", fontsize=8.0, color="white", fontweight="bold")
ax_b.text(0.155, hy - 0.015, "R+C", fontsize=8.0, color="white", fontweight="bold")
ax_b.text(0.275, hy - 0.015, "2-component", fontsize=8.0, color="white", fontweight="bold")
ax_b.text(0.430, hy - 0.015, "→", fontsize=8.0, color="white", fontweight="bold", ha="center")

for i, (pair, rc, rc_col, two, two_col, mark) in enumerate(verdicts):
    yy = hy - 0.07 - i * 0.075
    if i % 2 == 1:
        ax_b.add_patch(mpatches.Rectangle((0.005, yy - 0.025), 0.45, 0.06,
                                           facecolor="#f1f4f7", edgecolor="none"))
    ax_b.text(0.020, yy, pair, fontsize=7.3, color="#222")
    ax_b.text(0.155, yy, rc, fontsize=7.0, color=rc_col, fontweight="bold")
    ax_b.text(0.275, yy, two, fontsize=7.0, color=two_col, fontweight="bold")
    ax_b.text(0.430, yy, mark, fontsize=10, color=two_col, fontweight="bold", ha="center")

# Right: sub-09 protocol summary
ax_b.text(0.49, 0.86, "Sub-09 PENDING  —  4-way comparison protocol",
          fontsize=9.5, color=AMBER, fontweight="bold")

protocol = [
    ("Candidate A", "Phase A LOCO  (β_s=6°, β_c=−22°)"),
    ("Candidate B", "[NEW] mw_jaccard  (β_s=44°, β_c=+54°)"),
    ("Candidate C", "Cycle 12 cross-ROI  (β_s=30°, β_c=+26°)"),
    ("Candidate D", "Machado 1-way  (Δλ=13.5 nm, partial pre-image 4/8)"),
]
for i, (lab, body) in enumerate(protocol):
    yy = 0.78 - i * 0.07
    ax_b.add_patch(FancyBboxPatch((0.495, yy - 0.025), 0.10, 0.035,
                                   boxstyle="round,pad=0.001,rounding_size=0.005",
                                   facecolor=AMBER, edgecolor="none"))
    ax_b.text(0.545, yy - 0.008, lab, ha="center", va="center",
              fontsize=7.5, color="white", fontweight="bold")
    ax_b.text(0.605, yy - 0.008, body, fontsize=7.5, color="#222", va="center")

# Predictions to falsify
ax_b.text(0.49, 0.45, "Predictions to falsify (sub-09):",
          fontsize=8.5, color=ACCENT, fontweight="bold")
preds = [
    "PASS: c1 protan보정 + c5/c6 cyan/blu-cy 분리 + c8 magenta 이상 재현 여부",
    "FAIL on c8 only → c8-only variant (sub-08 §3-4 mirror)",
    "FAIL globally → Machado-only / R+C 시도 (model class 재선택)",
]
for i, p in enumerate(preds):
    ax_b.text(0.50, 0.40 - i * 0.045, "•  " + p, fontsize=7.3, color="#222")

# Reinterpretation note
ax_b.text(0.005, 0.05,
          "Note (2026-05-03): c2 orange recovery is structurally unrecoverable in (β_s∈[32,44], β_c∈[−18,−10]) — "
          "intrinsic 2-comp limit at 8-color resolution, NOT model-class failure.",
          fontsize=7.3, color="#666", style="italic")

# =================================== Section 3: Limits + Next steps + Phase 3
ax_n = fig.add_axes([0.025, 0.045, 0.95, 0.28])
ax_n.set_xlim(0, 1); ax_n.set_ylim(0, 1)
ax_n.axis("off")
ax_n.text(0.005, 0.96, "3.  Critical limits  +  next steps  →  Phase 3 trigger",
          fontsize=11.5, color=ACCENT, fontweight="bold")

# Left: limits
ax_n.text(0.005, 0.86, "Critical limits  (Cycle 13 framework decision)",
          fontsize=9.5, color="#7a3d1f", fontweight="bold")
limits = [
    "1.  Specificity abandoned — HC FPR 100%, baseline_ρ confound r = −0.894 across ROI/loss cells",
    "    → 13 reformulations (Cycle 9~13), no net gain.  Reporting = descriptive only.",
    "2.  HC pool n = 6 effective at hV4 (sub-07: 16 voxels → nan).  Statistical specificity infeasible.",
    "3.  8-color resolution caps narrow-band recovery (c2 orange 45°, c8 magenta 315°).",
    "    → fine-grid B1 confirmed unreachable in 2-comp parameter region.",
]
for i, t in enumerate(limits):
    ax_n.text(0.005, 0.80 - i * 0.05, t, fontsize=7.5, color="#333")

# Right: next steps (priority badges)
ax_n.text(0.50, 0.86, "Next steps  →  Phase 3", fontsize=9.5, color=ACCENT, fontweight="bold")
nexts = [
    ("HIGH", GREEN, "Sub-09 behavioral session",
     "4-way comparison (Candidates A–D above) — Phase 2 closure gate"),
    ("HIGH", GREEN, "Sub-08 4-way + canonical (38°, −14°)",
     "V4-only vs V1+V4 vs cycle12 vs canonical — selection rule 직접 검증"),
    ("MED",  AMBER, "Loss inventory v2 — HC fit",
     "Phase A canonical L_LOCO HC re-run (sub-01~07, server pending)"),
    ("MED",  AMBER, "Sub-08 c8 magenta variant",
     "pre-image θ ∈ {290°, 300°, 310°} — close residual blue-leaning bias"),
    ("LOW",  GREY,  "Phase 2 closure document",
     "two subjects + behavioral evidence + framework limits"),
    ("→",    ACCENT, "Phase 3 trigger  (post sub-09 PASS)",
     "JND + filtered-stim fMRI re-acquisition · sub-09 V4-only filter"),
]
for i, (badge, bcol, title, body) in enumerate(nexts):
    yy = 0.80 - i * 0.118
    bw = 0.07
    ax_n.add_patch(FancyBboxPatch((0.50, yy - 0.03), bw, 0.030,
                                   boxstyle="round,pad=0.001,rounding_size=0.005",
                                   facecolor=bcol, edgecolor="none"))
    ax_n.text(0.50 + bw / 2, yy - 0.015, badge, ha="center", va="center",
              fontsize=7, color="white", fontweight="bold")
    ax_n.text(0.580, yy - 0.005, title, fontsize=7.8, fontweight="bold", color="#111")
    ax_n.text(0.580, yy - 0.035, body, fontsize=7.0, color="#444")

# Footer
fig.text(0.5, 0.005,
         "Sources: future_phase2_filter_optimization/CLAUDE.md §3, §5  ·  behav_validation.md §3  ·  README.md  ·  project_phase2_closure (memory)",
         ha="center", fontsize=7.2, color=GREY, style="italic")

plt.savefig(OUT, dpi=160, bbox_inches="tight", facecolor=BG)
print(f"saved → {OUT}")
