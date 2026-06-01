#!/usr/bin/env python
"""
Pipeline 2 Closure §5.2 Theme A — specificity/identifiability statistical summary figure.

Reads the redteam result JSONs directly (no hand-copied numbers) and renders a
4-panel figure that visualizes the closure thesis:

  (A) averaged-surface loss landscape depth  -> signal is real (Exp17)
  (B) per-realization specificity p-values    -> only 1/3 single-source marginal (Exp22, Test2c)
  (C) production-GT parameter recovery bias    -> all 3 FAIL, f10deg<0.30 (Test1)
  (D) (0,0) algorithm-validation noise floor   -> ~20deg/25deg per-axis, f10_origin=0 (Test2a/B2)

Output: results/figures/fig_specificity_summary.{png,pdf}
Pure matplotlib (no seaborn).
"""
import json
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RT = os.path.join(ROOT, "results", "redteam")
OUT = os.path.join(ROOT, "results", "figures")
os.makedirs(OUT, exist_ok=True)


def load(name):
    with open(os.path.join(RT, name)) as f:
        return json.load(f)


# ---- candidate order, labels, colors (consistent across panels) ----
CANDS = ["S08-stable", "S08-robust", "S09-primary"]
LBL = {
    "S08-stable": "S08-βs-dom\n(+38, −10)",
    "S08-robust": "S08-βc-dom\n(+6, −42)",
    "S09-primary": "S09-βc-rot\n(+2, +24)",
}
COL = {"S08-stable": "#4C72B0", "S08-robust": "#DD8452", "S09-primary": "#55A868"}

exp17 = load("exp17_loss_landscape.json")["candidates"]
exp22 = load("exp22_origin_loss_specificity.json")["candidates"]
vm = load("verdict_matrix_v6_pca_v2.json")["per_candidate"]

plt.rcParams.update({
    "font.size": 10, "axes.titlesize": 11, "axes.titleweight": "bold",
    "axes.labelsize": 10, "figure.dpi": 120,
})
fig, axes = plt.subplots(2, 2, figsize=(12.5, 9.2))
axA, axB, axC, axD = axes.ravel()
x = np.arange(len(CANDS))

# ================= Panel A : loss landscape depth (Exp17) =================
real = [exp17[c]["real_analysis"]["loss_at_argmin"] for c in CANDS]
synth = [exp17[c]["synth_analysis"]["loss_at_argmin"] for c in CANDS]
w = 0.38
bR = axA.bar(x - w / 2, real, w, label="REAL CVD", color=[COL[c] for c in CANDS], edgecolor="k", lw=0.6)
bS = axA.bar(x + w / 2, synth, w, label="synthetic HC null", color="#cccccc", edgecolor="k", lw=0.6)
for i, c in enumerate(CANDS):
    ratio = real[i] / synth[i]
    axA.annotate(f"{ratio:.1f}×", (i - w / 2, real[i] - 0.06),
                 ha="center", va="top", fontsize=10, fontweight="bold", color=COL[c])
axA.axhline(0, color="k", lw=0.8)
axA.set_xticks(x)
axA.set_xticklabels([LBL[c] for c in CANDS])
axA.set_ylim(min(real) - 0.45, 0.35)
axA.set_ylabel("loss at argmin  (z; more negative = deeper)")
axA.set_title("A  Averaged-surface loss depth (Exp 17)\nREAL minima 2.1–5.5× deeper → signal present")
axA.legend(loc="upper right", fontsize=9, frameon=False)

# ================= Panel B : per-realization specificity p-values =================
tests = ["Exp22\nBonferroni", "Exp22\nL(argmin)", "Test2c\nlabel-perm"]
P = np.array([
    [exp22[c]["p_values"]["p_bonferroni_3metrics"],
     exp22[c]["p_values"]["p_Lmin_real_low"],
     vm[c]["within_subject_sig"]["p_perm"]]
    for c in CANDS
])
im = axB.imshow(P, cmap="RdYlGn_r", vmin=0, vmax=1, aspect="auto")
axB.set_xticks(range(len(tests)))
axB.set_xticklabels(tests)
axB.set_yticks(range(len(CANDS)))
axB.set_yticklabels([LBL[c].replace("\n", " ") for c in CANDS], fontsize=9)
for i in range(len(CANDS)):
    for j in range(len(tests)):
        sig = P[i, j] < 0.05
        axB.text(j, i, f"{P[i,j]:.3f}" + ("\n*" if sig else ""),
                 ha="center", va="center", fontsize=10,
                 color="white" if sig else "black",
                 fontweight="bold" if sig else "normal")
        if sig:
            axB.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1, fill=False, edgecolor="k", lw=2.5))
axB.set_title("B  Per-realization specificity p-values\nonly S08-βc-dom Exp22 < .05 (single null source)")
cb = fig.colorbar(im, ax=axB, fraction=0.046, pad=0.04)
cb.set_label("p-value", fontsize=9)
cb.ax.axhline(0.05, color="k", lw=1.5)

# ================= Panel C : production-GT recovery bias (Test1) =================
axC.axhline(0, color="grey", lw=0.7, ls="--")
axC.axvline(0, color="grey", lw=0.7, ls="--")
for c in CANDS:
    idn = vm[c]["identifiability"]
    bs, bc = idn["bias_bs_median"], idn["bias_bc_median"]
    f10 = idn["frac_within_10deg_median"]
    axC.add_patch(FancyArrowPatch((0, 0), (bs, bc), arrowstyle="-|>", mutation_scale=16,
                                  color=COL[c], lw=2.2))
    axC.scatter([bs], [bc], s=55, color=COL[c], edgecolor="k", zorder=5,
                label=f"{LBL[c].split(chr(10))[0]}  f₁₀°={f10:.2f}")
    dy = 9 if bc >= 0 else -9
    axC.annotate(f"({bs:+.0f}, {bc:+.0f})", (bs, bc), textcoords="offset points",
                 xytext=(7, dy), fontsize=8.5, color=COL[c])
# 10deg tolerance ring
th = np.linspace(0, 2 * np.pi, 200)
axC.plot(10 * np.cos(th), 10 * np.sin(th), color="k", lw=1, ls=":")
axC.text(0, -9.4, "10° tol", ha="center", va="top", fontsize=8)
axC.set_xlabel("β_s recovery bias (°)")
axC.set_ylabel("β_c recovery bias (°)")
axC.set_aspect("equal")
lim = 36
axC.set_xlim(-lim, lim); axC.set_ylim(-lim, lim)
axC.set_title("C  Production-GT parameter recovery (Test 1)\nbias vectors exit 10° tol → all 3 FAIL")
axC.legend(loc="upper right", fontsize=8, frameon=False)

# ================= Panel D : (0,0) noise floor (Test2a / B2) =================
us = load("uncertainty_summary.json")["candidates"]
bs_med = [us[c]["effective_uncertainty_B2"]["abs_bs_median"] for c in CANDS]
bc_med = [us[c]["effective_uncertainty_B2"]["abs_bc_median"] for c in CANDS]
bs_iqr = [us[c]["effective_uncertainty_B2"]["abs_bs_iqr"] for c in CANDS]
bc_iqr = [us[c]["effective_uncertainty_B2"]["abs_bc_iqr"] for c in CANDS]
bD1 = axD.bar(x - w / 2, bs_med, w, yerr=np.array(bs_iqr) / 2, capsize=4,
              label="|β_s| @ GT=(0,0)", color="#8172B3", edgecolor="k", lw=0.6)
bD2 = axD.bar(x + w / 2, bc_med, w, yerr=np.array(bc_iqr) / 2, capsize=4,
              label="|β_c| @ GT=(0,0)", color="#C44E52", edgecolor="k", lw=0.6)
axD.axhline(20, color="#8172B3", ls="--", lw=1.2)
axD.axhline(25, color="#C44E52", ls="--", lw=1.2)
axD.text(-0.46, 20.0, "β_s floor ~20°", fontsize=8, color="#8172B3", ha="left", va="bottom")
axD.text(-0.46, 25.0, "β_c floor ~25°", fontsize=8, color="#C44E52", ha="left", va="bottom")
axD.axhline(10, color="k", ls=":", lw=1)
axD.text(-0.46, 10.0, "10° tol", fontsize=8, ha="left", va="bottom")
axD.set_xticks(x)
axD.set_xticklabels([LBL[c] for c in CANDS])
axD.set_ylim(0, max(bs_med[i] + bs_iqr[i] / 2 for i in range(len(CANDS))) + 16)
axD.set_ylabel("argmin distance from origin (°)")
axD.set_title("D  Algorithm validation @ GT=(0,0)  (Test 2a / B2)\nf₁₀°(origin)=0/140 → noise floor ~20°/25°")
axD.legend(loc="upper right", fontsize=8.5, frameon=False, ncol=2)

fig.suptitle("Pipeline 2 Closure §5.2 Theme A — identifiability & specificity of the 3 candidate filters",
             fontsize=13, fontweight="bold", y=0.995)
fig.tight_layout(rect=[0, 0, 1, 0.97])

png = os.path.join(OUT, "fig_specificity_summary.png")
pdf = os.path.join(OUT, "fig_specificity_summary.pdf")
fig.savefig(png, dpi=300, bbox_inches="tight")
fig.savefig(pdf, bbox_inches="tight")
print("wrote", png)
print("wrote", pdf)
