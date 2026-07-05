#!/usr/bin/env python3
"""Result C — 2nd-MRI filter-validation figure (N=2, EXPLORATORY).

Grid: 2 rows x 2 subject columns.
  row 0 (neural)     : hV4 LOCO adjacent-accuracy   -> higher = HC-like (HC 0.456; chance 0.375)
  row 1 (behavioral) : |JND - HC| in z (HC-disparity) -> lower = HC-like (HC = 0)

Framing (ResearchNOTE 2026-07-04, section 6.5): descriptive, hypothesis-generating.
NO 'neural superiority' / 'only Optimal restores' claims (section 6.5.3 forbidden list).
All numbers verified from:
  neural   : exp2_neural/results/exp2_followup_native.json  (V4.loco_adj, .nofilter_subset_n4)
  behavior : results/exp2_behavior/sub-0X_jnd_vs_hc.json     (mean_abs_z_to_HC)
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

_HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(_HERE, "fig", "fig_validation.png")

GREY="#9aa3ad"; MACOS="#5b6b8c"; ORANGE="#E8762C"; SBLUE="#2E6FBF"
HCGREEN="#3A8E4A"; NAVY="#13294B"; INK="#222222"

plt.rcParams.update({"font.family":"DejaVu Sans","font.size":13,
    "axes.edgecolor":"#444444","axes.linewidth":1.0})

CONDS=["nofilter","window","optimal"]
CLABEL=["No\nfilter","Window\n(macOS)","Optimal\n(ours)"]
CCOL=[GREY,MACOS,ORANGE]

# ---------- verified data ----------
# neural: hV4 (V4) LOCO adjacent-accuracy; NF = run-matched n4 subset for fair 4-run comparison
HC_ADJ=0.456; CHANCE=0.375
adj={"sub-08":{"nofilter":0.231,"window":0.250,"optimal":0.312},
     "sub-09":{"nofilter":0.138,"window":0.188,"optimal":0.062}}
# behavioral: |JND - HC| in z (mean_abs_z_to_HC); HC-disparity, 0 = HC
zhc={"sub-08":{"nofilter":2.241,"window":0.853,"optimal":0.780},
     "sub-09":{"nofilter":0.897,"window":1.775,"optimal":0.934}}

SUBS=[("sub-08","Sub-08  deutan",ORANGE),("sub-09","Sub-09  protan",SBLUE)]

fig, axes = plt.subplots(2, 2, figsize=(9.4, 8.6), sharex="col")
fig.subplots_adjust(left=0.14, right=0.985, top=0.885, bottom=0.075,
                    wspace=0.10, hspace=0.24)

def bars(ax, data, hlines, ylim, ylabel, fmt, better_up, title=None, tcol=None):
    x=np.arange(len(CONDS))
    for y,lab,col,ls in hlines:
        ax.axhline(y,color=col,lw=2.0,ls=ls,zorder=1)
    for i,c in enumerate(CONDS):
        v=data[c]; hi=(c=="optimal")
        ax.bar(x[i],v,width=0.62,color=CCOL[i],
               edgecolor=NAVY if hi else "none",lw=2.2 if hi else 0,zorder=2)
        va="bottom"; off=4
        ax.annotate(fmt(v),(x[i],v),ha="center",va=va,
                    xytext=(0,off),textcoords="offset points",
                    fontsize=12.5,fontweight="bold",color=NAVY if hi else INK)
    ax.set_xticks(x); ax.set_xticklabels(CLABEL,fontsize=11.5)
    ax.set_xlim(-0.62,len(CONDS)-0.38); ax.set_ylim(*ylim)
    if ylabel: ax.set_ylabel(ylabel,fontsize=11.5,fontweight="bold")
    if title: ax.set_title(title,fontsize=15,fontweight="bold",color=tcol,pad=8)
    for s in ("top","right"): ax.spines[s].set_visible(False)

# ---- row 0: neural (higher = HC-like) ----
for j,(sid,stitle,scol) in enumerate(SUBS):
    bars(axes[0,j],adj[sid],
         [(HC_ADJ,"HC",HCGREEN,"-"),(CHANCE,"chance",INK,(0,(4,3)))],
         (0,0.52),
         "hV4 LOCO\nadjacent-acc  (↑ = HC-like)" if j==0 else None,
         lambda v:f"{v:.2f}",True,title=stitle,tcol=scol)
axes[0,0].text(-0.55,HC_ADJ+0.006,"HC",ha="left",va="bottom",fontsize=10.5,
               color=HCGREEN,fontweight="bold")
axes[0,1].text(2.38,CHANCE+0.006,"chance",ha="right",va="bottom",fontsize=10,
               color=INK)

# ---- row 1: behavioral HC-disparity (lower = HC-like) ----
for j,(sid,stitle,scol) in enumerate(SUBS):
    bars(axes[1,j],zhc[sid],[(0,"HC",HCGREEN,"-")],
         (0,2.55),
         "|JND − HC|  (z)\n(↓ = HC-like)" if j==0 else None,
         lambda v:f"{v:.2f}",False)

# ---- honest per-subject read-outs (no 'superiority') ----
fig.suptitle("Filter validation (2nd MRI, N=2) — descriptive, exploratory",
             fontsize=15.5,fontweight="bold",color=NAVY,y=0.965)
fig.savefig(OUT,dpi=300,facecolor="white")
print("saved",OUT)
