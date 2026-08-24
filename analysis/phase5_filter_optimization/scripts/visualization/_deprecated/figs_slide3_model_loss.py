"""Slide 3 — Model + Loss explanation (principles, equations, selection, evaluation).

Layout:
  Row 1 (~35%): 3 model cards (Machado / R+C / 2-Component)
  Row 2 (~25%): L_LOCO equation card with component definitions
  Row 3 (~30%): Loss selection criterion & evaluation pipeline (4 boxes)

Output: results/visualizations/meeting/slide3_model_loss.png
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "visualizations" / "meeting" / "slide3_model_loss.png"
OUT.parent.mkdir(parents=True, exist_ok=True)

ACCENT = "#1f4e79"
GREEN = "#2e7d32"
AMBER = "#e6a23c"
RED   = "#c0392b"
GREY  = "#666"
BG    = "#fafbfc"

# ====================================================================== figure
fig = plt.figure(figsize=(13.5, 8.5), dpi=160, facecolor=BG)

# Header
hax = fig.add_axes([0.0, 0.94, 1.0, 0.06])
hax.axis("off")
hax.add_patch(mpatches.Rectangle((0, 0), 1, 1, facecolor=ACCENT, edgecolor="none"))
hax.text(0.012, 0.55, "Slide 3 — Model + Loss  (principles · equations · selection · evaluation)",
         color="white", fontsize=14.5, fontweight="bold", va="center")
hax.text(0.012, 0.18, "3 forward-model classes  |  L_LOCO multi-objective fit  |  Loss Inventory selection  |  Multi-stage evaluation",
         color="#cfd8e3", fontsize=9.5, va="center")

# =================================== Row 1: 3 model cards
ax_models = fig.add_axes([0.025, 0.61, 0.95, 0.30])
ax_models.set_xlim(0, 1); ax_models.set_ylim(0, 1)
ax_models.axis("off")
ax_models.text(0.005, 0.96, "1.  Three forward models  (mechanistic level: retinal → cortical)",
               fontsize=11.5, color=ACCENT, fontweight="bold")

models = [
    {
        "name": "Machado 1-way",
        "color": "#7a3d8a",
        "dof": "1 DOF",
        "level": "Retinal — pre-receptoral cone fundamentals",
        "params": "Δλ ∈ [0, 20] nm  (peak-sensitivity shift)",
        "eq":     "θ' = machado_shifted_hue(Δλ, family)",
        "principle": "Spectral shift of L (protan) or M (deutan) cone; based on Machado et al. (2009) Eq 5/6",
        "invert":  "monotone for small Δλ; arc collapses at large Δλ (sub-09: 4/8 exact)",
    },
    {
        "name": "R+C  (retinal + cortical)",
        "color": "#5a3a8a",
        "dof": "2 DOF",
        "level": "Retinal shift + post-receptoral RG opponent gain",
        "params": "Δλ ∈ [0, 20]  ·  g ∈ [−3, 1]   (g=0 ≡ Machado)",
        "eq":     "rg' = rg_b + (1+g)·(rg_ret − rg_b);   yb' = yb",
        "principle": "Single tuning knob on RG axis; cortical compensation factor g",
        "invert":  "algebraic bijective; perceptually 1-axis (sub-08: behav YG-C collapse)",
    },
    {
        "name": "2-Component  (★ best for both CVD)",
        "color": "#2a5a8a",
        "dof": "2 DOF",
        "level": "Cortical hue map — angular dilation, NO retinal term",
        "params": "β_s ∈ [0, 50]  ·  β_c ∈ [−50, 50]  (degrees)",
        "eq":     "θ' = θ + β_s·cos(θ−90°) + β_c·cos(θ−θ_conf)",
        "principle": "S-cone axis dilation (Emery 2021) + confusion-axis rotation (Brettel 1997)\nθ_conf = 16° protan / 150° deutan",
        "invert":  "smooth bijective; pre-image 8/8 exact for sub-08 AND sub-09",
    },
]

mx0 = 0.005; gap = 0.012
mw = (1 - 2 * mx0 - 2 * gap) / 3
my_top = 0.88; mh = 0.84
for i, m in enumerate(models):
    x = mx0 + i * (mw + gap)
    is_best = "★" in m["name"]
    edge_w = 2.0 if is_best else 1.2
    box = FancyBboxPatch((x, my_top - mh), mw, mh,
                         boxstyle="round,pad=0.005,rounding_size=0.012",
                         linewidth=edge_w, edgecolor=m["color"],
                         facecolor="#fff8e1" if is_best else "white")
    ax_models.add_patch(box)

    # name + DOF chip
    ax_models.text(x + 0.012, my_top - 0.03, m["name"],
                   fontsize=10.5, fontweight="bold", color=m["color"])
    ax_models.add_patch(FancyBboxPatch((x + mw - 0.06, my_top - 0.045), 0.05, 0.025,
                                        boxstyle="round,pad=0.001,rounding_size=0.005",
                                        facecolor=m["color"], edgecolor="none"))
    ax_models.text(x + mw - 0.035, my_top - 0.0325, m["dof"],
                   ha="center", va="center", fontsize=7.0,
                   color="white", fontweight="bold")

    # level
    ax_models.text(x + 0.012, my_top - 0.10, "Level:",
                   fontsize=7.5, color=GREY, fontweight="bold")
    ax_models.text(x + 0.012, my_top - 0.135, m["level"],
                   fontsize=7.3, color="#222")

    # params
    ax_models.text(x + 0.012, my_top - 0.20, "Parameters:",
                   fontsize=7.5, color=GREY, fontweight="bold")
    ax_models.text(x + 0.012, my_top - 0.235, m["params"],
                   fontsize=7.3, color="#222", family="monospace")

    # equation (in box)
    ax_models.add_patch(mpatches.Rectangle((x + 0.012, my_top - 0.36), mw - 0.024, 0.05,
                                            facecolor="#f3f6fa", edgecolor=m["color"],
                                            linewidth=0.6))
    ax_models.text(x + mw / 2, my_top - 0.335, m["eq"], ha="center", va="center",
                   fontsize=7.5, color=m["color"], family="monospace", fontweight="bold")

    # principle
    ax_models.text(x + 0.012, my_top - 0.42, "Principle:",
                   fontsize=7.5, color=GREY, fontweight="bold")
    ax_models.text(x + 0.012, my_top - 0.455, m["principle"],
                   fontsize=7.0, color="#222", style="italic")

    # invertibility
    ax_models.text(x + 0.012, my_top - 0.55, "Invertibility:",
                   fontsize=7.5, color=GREY, fontweight="bold")
    ax_models.text(x + 0.012, my_top - 0.585, m["invert"],
                   fontsize=7.0, color="#222")

# =================================== Row 2: L_LOCO equation card
ax_loss = fig.add_axes([0.025, 0.355, 0.95, 0.215])
ax_loss.set_xlim(0, 1); ax_loss.set_ylim(0, 1)
ax_loss.axis("off")
ax_loss.text(0.005, 0.92, "2.  Fit loss  L_LOCO  (multi-objective, hV4, shift_at_both)",
             fontsize=11.5, color=ACCENT, fontweight="bold")

# Big equation
ax_loss.add_patch(FancyBboxPatch((0.025, 0.45), 0.95, 0.32,
                                  boxstyle="round,pad=0.008,rounding_size=0.012",
                                  facecolor="#f3f6fa", edgecolor=ACCENT, linewidth=1.2))
ax_loss.text(0.5, 0.66,
             "L_fit  =  α · L_vuln  +  β · L_rank  +  δ · L_rdm  +  ε · L_smooth",
             ha="center", fontsize=13.5, color=ACCENT, fontweight="bold")
ax_loss.text(0.5, 0.55,
             "α = 1.0    β = 0.5    δ = 0.2    ε = 0.1",
             ha="center", fontsize=10, color="#222", family="monospace")

# Component definitions in 4 columns
defs = [
    ("L_vuln", "MSE(v_sim, v_CVD)",   "primary — reproduce per-color vulnerability profile"),
    ("L_rank", "1 − Spearman ρ",       "secondary — preserve vulnerability ordering"),
    ("L_rdm",  "1 − cos(ΔRDM_sim, ΔRDM_obs)", "auxiliary — pairwise structure consistency"),
    ("L_smooth", "Σ (δ(c+1) − δ(c))²", "regularizer — physiological smoothness in hue"),
]
cw = 0.235
for i, (n, eq, desc) in enumerate(defs):
    x = 0.025 + i * (cw + 0.005)
    ax_loss.text(x + cw/2, 0.36, n, ha="center", fontsize=9, fontweight="bold", color=ACCENT)
    ax_loss.text(x + cw/2, 0.27, eq, ha="center", fontsize=7.8,
                 color="#222", family="monospace")
    ax_loss.text(x + cw/2, 0.16, desc, ha="center", fontsize=7.3, color="#444",
                 style="italic", wrap=True)

ax_loss.text(0.025, 0.04,
             "Null = 8! exact label permutation (40,320).   "
             "L_improve · L_no-harm  →  evaluation/derivation only, NOT in fit.",
             fontsize=8.0, color=GREY, style="italic")

# =================================== Row 3: Selection + Evaluation pipeline
ax_sel = fig.add_axes([0.025, 0.04, 0.95, 0.29])
ax_sel.set_xlim(0, 1); ax_sel.set_ylim(0, 1)
ax_sel.axis("off")
ax_sel.text(0.005, 0.96, "3.  Selection criterion  +  Multi-stage evaluation",
            fontsize=11.5, color=ACCENT, fontweight="bold")
ax_sel.text(0.005, 0.89,
            "Filter selection rule  =  LOCO-best descriptive fit  +  behavioral validation  (override authority).  "
            "Behavioral PASS overrides LOCO ρ when they conflict (sub-08 R+C → 2-comp case).",
            fontsize=8.5, color="#222")

stages = [
    ("Pre-image",
     "Forward exact inverse  (θ_pre = argmin |D(θ)−θ_target|)",
     "Pass: 8/8 within 1e-3°. FAIL → reject model–subject combo.",
     "2-comp 8/8 sub-08+09  ·  Machado 4/8 sub-09",
     GREEN),
    ("Permutation",
     "8! exact label-shuffle null on Spearman ρ",
     "Sub-08 hV4: p = 0.004**.  Sub-09 hV4: p = 0.035*.",
     "(Machado sub-09: p = 0.018*)",
     GREEN),
    ("HC sanity (Loss inventory)",
     "12 loss variants × 6 HC × 2 CVD  →  emp_p ≤ 0.20",
     "PASS+: cycle15_opt2 + mw_jaccard_loss (both CVD distinct).",
     "Confirms (68, −38) sub-08, (44, +54) sub-09",
     AMBER),
    ("Behavioral validation",
     "Qualitative naming on filtered swatches  =  FINAL ARBITER",
     "Sub-08 (38, −14) §3 PASS — YG-C 4-way collapse 해소 확인.",
     "Sub-09 PENDING — 4-way comparison protocol",
     ACCENT),
]
sw = 0.232; sgap = 0.010
sx0 = 0.005
sy_top = 0.78; sh = 0.72
for i, (n, what, result, detail, col) in enumerate(stages):
    x = sx0 + i * (sw + sgap)
    box = FancyBboxPatch((x, sy_top - sh), sw, sh,
                         boxstyle="round,pad=0.005,rounding_size=0.010",
                         linewidth=1.0, edgecolor=col, facecolor="white")
    ax_sel.add_patch(box)
    # numbered tag
    ax_sel.add_patch(mpatches.Circle((x + 0.025, sy_top - 0.05), 0.018,
                                      facecolor=col, edgecolor="none"))
    ax_sel.text(x + 0.025, sy_top - 0.05, str(i + 1), ha="center", va="center",
                fontsize=10, color="white", fontweight="bold")
    ax_sel.text(x + 0.055, sy_top - 0.045, n,
                fontsize=9.5, fontweight="bold", color=col, va="center")
    ax_sel.text(x + 0.012, sy_top - 0.12, "What:",
                fontsize=7.5, color=GREY, fontweight="bold")
    ax_sel.text(x + 0.012, sy_top - 0.155, what,
                fontsize=7.3, color="#222", style="italic")
    ax_sel.text(x + 0.012, sy_top - 0.245, "Result:",
                fontsize=7.5, color=GREY, fontweight="bold")
    ax_sel.text(x + 0.012, sy_top - 0.28, result,
                fontsize=7.3, color="#222")
    ax_sel.text(x + 0.012, sy_top - 0.41, detail,
                fontsize=7.0, color="#444", style="italic")

# Arrow flow between stages
for i in range(3):
    x1 = sx0 + (i + 1) * sw + i * sgap - 0.002
    x2 = x1 + sgap + 0.002
    ax_sel.annotate("", xy=(x2, sy_top - sh / 2),
                    xytext=(x1, sy_top - sh / 2),
                    arrowprops=dict(arrowstyle="->", color=ACCENT, lw=1.4))

# Footer
fig.text(0.5, 0.005,
         "Sources: phase5_filter_optimization/CLAUDE.md §0–§8  ·  README.md §3  ·  loss_inventory.md  ·  behav_validation.md §3",
         ha="center", fontsize=7.2, color=GREY, style="italic")

plt.savefig(OUT, dpi=160, bbox_inches="tight", facecolor=BG)
print(f"saved → {OUT}")
