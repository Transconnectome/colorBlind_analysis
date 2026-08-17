#!/usr/bin/env python
"""
Pipeline 2 Closure front-matter figure (RQ1 / §5.1 / Appendix A.2).

Visualizes the 3 final candidate filters in (β_s, β_c) parameter space and their
cross-metric (PCA vs SRM-cosine vs SRM-disparity) argmin spread — i.e. the
mechanism-class convergence (sub-08) vs σ-level metric non-identifiability (sub-09, L9 / A.2).

All (β_s, β_c) read directly from the v6 fit result JSONs (per-subset median over
the HC 5/2 resample), reproducing the Appendix A.2 table — no hand-copied numbers.

Output: results/figures/fig_candidates_param_space.{png,pdf}
"""
import json
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SDIR = os.path.join(ROOT, "results", "s10_inclusion")
OUT = os.path.join(ROOT, "results", "figures")
os.makedirs(OUT, exist_ok=True)

ATOM_FILE = {
    "PCA": "s10b_v6_pca_rdm_results_%s.json",
    "SRM-cos": "s10b_v6_srm_rdm_results_%s.json",
    "SRM-dis": "s10b_v6_srm_disparity_results_%s.json",
}
# candidate -> (subject, fit-cell key, display label, color)
CANDS = {
    "S08-βs-dom": ("sub-08", "γALL|RDMV1|noLOCO", "S08-βs-dom  (γ_all+RDM_V1)", "#4C72B0"),
    "S08-βc-dom": ("sub-08", "γOY|RDMV2|noLOCO", "S08-βc-dom  (γ_OY+RDM_V2)", "#DD8452"),
    "S09-βc-rot": ("sub-09", "γALL|RDMV1|noLOCO", "S09-βc-rot  (γ_all+RDM_V1)", "#55A868"),
}
MARK = {"PCA": ("*", 340), "SRM-cos": ("o", 95), "SRM-dis": ("^", 110)}


def median_beta(subject, cell, atom):
    d = json.load(open(os.path.join(SDIR, ATOM_FILE[atom] % subject)))["storage"]
    sub = d[cell]["2comp"]
    return (float(np.median([s["beta_s"] for s in sub])),
            float(np.median([s["beta_c"] for s in sub])))


plt.rcParams.update({"font.size": 11, "axes.titlesize": 13, "axes.titleweight": "bold",
                     "axes.labelsize": 12, "figure.dpi": 120})
fig, ax = plt.subplots(figsize=(8.6, 8.0))

# --- mechanism-region shading ---
ax.axhspan(-52, 0, xmin=0, xmax=1, color="#4C72B0", alpha=0.06)
ax.axhspan(0, 52, xmin=0, xmax=1, color="#55A868", alpha=0.07)
ax.text(49, -49, "deutan-consistent\n(β_s>0, β_c<0)", ha="right", va="bottom",
        fontsize=10, color="#27496d", style="italic")
ax.text(49, 49, "protan rotation\n(β_s>0, β_c>0)", ha="right", va="top",
        fontsize=10, color="#1e5631", style="italic")
ax.axhline(0, color="grey", lw=0.8, ls="--")
ax.axvline(0, color="grey", lw=0.8)

# --- candidate points + cross-metric spread ---
for cname, (subj, cell, lab, col) in CANDS.items():
    pts = {a: median_beta(subj, cell, a) for a in ATOM_FILE}
    xs = [pts[a][0] for a in ATOM_FILE]
    ys = [pts[a][1] for a in ATOM_FILE]
    # faint connector showing metric spread
    ax.plot(xs, ys, color=col, lw=1.3, alpha=0.45, zorder=2)
    for a in ATOM_FILE:
        m, s = MARK[a]
        ax.scatter(*pts[a], marker=m, s=s, color=col, edgecolor="k", lw=0.7,
                   zorder=5)
    # label at PCA (production) point — offset chosen to avoid legends/cluster
    bx, by = pts["PCA"]
    if by < -30:
        off = (10, 6)          # bottom cluster -> label up-right (clears lower-center legend)
    elif by >= 0:
        off = (10, 8)
    else:
        off = (10, -4)
    ax.annotate(f"{cname}\nPCA ({bx:+.0f},{by:+.0f})", (bx, by), textcoords="offset points",
                xytext=off, fontsize=9, color=col, fontweight="bold")

# highlight S09 metric divergence span (β_c +24 -> 0 across the line)
s09 = CANDS["S09-βc-rot"]
p_pca = median_beta(s09[0], s09[1], "PCA")
p_srm = median_beta(s09[0], s09[1], "SRM-cos")
ax.annotate("", xy=p_srm, xytext=p_pca,
            arrowprops=dict(arrowstyle="<->", color="#55A868", lw=1.4, ls=":"))
ax.text(18, 14, "σ-level\nnon-identifiability\n(L9 / A.2)", color="#1e5631",
        fontsize=9, ha="center", style="italic")

ax.set_xlim(-3, 52)
ax.set_ylim(-52, 52)
ax.set_xlabel("β_s   (S-cone cardinal-axis rotation, °)")
ax.set_ylabel("β_c   (confusion-axis rotation, °)")
ax.set_title("Pipeline 2 — candidate filters in (β_s, β_c) space\ncross-metric spread: PCA vs SRM-cos vs SRM-dis  (RQ1 · §5.1 · App. A.2)")

# two legends: candidate color + metric marker
cand_handles = [Line2D([0], [0], marker="s", ls="", ms=9, mfc=c[3], mec="k",
                       label=name) for name, c in CANDS.items()]
mark_handles = [Line2D([0], [0], marker=MARK[a][0], ls="", ms=11 if a == "PCA" else 9,
                       mfc="grey", mec="k", label=f"{a}" + (" (production)" if a == "PCA" else ""))
                for a in ATOM_FILE]
leg1 = ax.legend(handles=cand_handles, loc="lower center", fontsize=9, frameon=True,
                 title="candidate", title_fontsize=9)
ax.add_artist(leg1)
ax.legend(handles=mark_handles, loc="upper left", fontsize=9, frameon=True,
          title="RDM metric", title_fontsize=9)

fig.tight_layout()
png = os.path.join(OUT, "fig_candidates_param_space.png")
pdf = os.path.join(OUT, "fig_candidates_param_space.pdf")
fig.savefig(png, dpi=300, bbox_inches="tight")
fig.savefig(pdf, bbox_inches="tight")
print("wrote", png)
print("wrote", pdf)

# console echo for cross-check against Appendix A.2
for cname, (subj, cell, lab, col) in CANDS.items():
    print(cname, {a: median_beta(subj, cell, a) for a in ATOM_FILE})
