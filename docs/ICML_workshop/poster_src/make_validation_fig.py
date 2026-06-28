#!/usr/bin/env python3
"""Result C — 2nd-MRI filter-validation figure (sub-08 done, sub-09 pending).

Two rows:
  (top)    hV4 LOCO rho  -> neural interpolation geometry, higher = HC-like.
  (bottom) mean JND       -> behavioral discrimination, lower = better (HC-like).
Punchline: behavioral parity with the deployed macOS filter, but ONLY the
model-derived (Optimal) filter restores hV4 geometry toward HC.
All numbers verified from exp2_hc_likeness_sub-08_native.json + sub-08_summary.json.
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

CONDS=["nofilter","macos","optimal"]
CLABEL=["No\nfilter","macOS\nfilter","Optimal\n(ours)"]
CCOL=[GREY,MACOS,ORANGE]

# ----- verified data -----
HC_RHO_M, HC_RHO_SD = 0.208, 0.179
rho08={"nofilter":-0.272,"macos":-0.388,"optimal":0.179}
HC_JND=0.104
jnd08={"nofilter":0.187,"macos":0.080,"optimal":0.080}

fig, axes = plt.subplots(2, 2, figsize=(9.0, 8.4), sharex="col")
fig.subplots_adjust(left=0.135, right=0.985, top=0.90, bottom=0.075,
                    wspace=0.08, hspace=0.22)

def bars(ax, data, band, hc_line, ylim, ylabel, fmt, better_up,
         pending=False, title=None, tcol=None):
    x=np.arange(len(CONDS))
    if band is not None:
        ax.axhspan(band[0],band[1],color=HCGREEN,alpha=0.16,zorder=0)
    ax.axhline(hc_line,color=HCGREEN,lw=2.0,zorder=1)
    if ylim[0]<0<ylim[1]:
        ax.axhline(0,color="#888888",lw=0.9,ls=(0,(4,3)),zorder=1)
    for i,c in enumerate(CONDS):
        v=data[c]
        if v is None:
            ax.bar(x[i],hc_line,width=0.62,facecolor="none",
                   edgecolor="#b9c0c9",hatch="////",lw=1.2,zorder=2)
        else:
            hi=(c=="optimal")
            ax.bar(x[i],v,width=0.62,color=CCOL[i],
                   edgecolor=NAVY if hi else "none",lw=2.2 if hi else 0,zorder=2)
            up = v>=hc_line if not (ylim[0]<0) else v>=0
            ax.annotate(fmt(v),(x[i],v),ha="center",
                        va="bottom" if up else "top",
                        xytext=(0,4 if up else -4),textcoords="offset points",
                        fontsize=12.5,fontweight="bold",color=NAVY if hi else INK)
    ax.set_xticks(x); ax.set_xticklabels(CLABEL,fontsize=12)
    ax.set_xlim(-0.62,len(CONDS)-0.38); ax.set_ylim(*ylim)
    if ylabel: ax.set_ylabel(ylabel,fontsize=12,fontweight="bold")
    if title: ax.set_title(title,fontsize=15,fontweight="bold",color=tcol,pad=7)
    if pending:
        ax.text(0.5,0.5,"to be collected\n2026-06-29",transform=ax.transAxes,
                ha="center",va="center",fontsize=13,color="#9aa3ad",
                style="italic",rotation=12,fontweight="bold")
    for s in ("top","right"): ax.spines[s].set_visible(False)

# row 0: hV4 LOCO rho
bars(axes[0,0],rho08,(HC_RHO_M-HC_RHO_SD,HC_RHO_M+HC_RHO_SD),HC_RHO_M,
     (-0.55,0.45),"hV4 LOCO ρ\n(neural geometry → HC)",lambda v:f"{v:+.2f}",True,
     title="Sub-08  deutan",tcol=ORANGE)
bars(axes[0,1],{k:None for k in CONDS},(HC_RHO_M-HC_RHO_SD,HC_RHO_M+HC_RHO_SD),
     HC_RHO_M,(-0.55,0.45),None,lambda v:f"{v:+.2f}",True,pending=True,
     title="Sub-09  protan  (in progress)",tcol=SBLUE)
axes[0,0].text(-0.55,HC_RHO_M+0.012,"HC mean ± SD",ha="left",va="bottom",
               fontsize=10.5,color=HCGREEN,fontweight="bold")
# row 1: behavioral mean JND (lower = better; HC line)
bars(axes[1,0],jnd08,None,HC_JND,(0,0.215),
     "Mean JND\n(behavior; lower = better)",lambda v:f"{v:.2f}",False)
bars(axes[1,1],{k:None for k in CONDS},None,HC_JND,(0,0.215),None,
     lambda v:f"{v:.2f}",False,pending=True)
axes[1,0].text(-0.55,HC_JND+0.004,"HC mean",ha="left",va="bottom",
               fontsize=10.5,color=HCGREEN,fontweight="bold")
axes[1,0].text(1.5,0.165,"both filters → HC level\n(parity, p=0.84)",
               ha="center",va="center",fontsize=10.5,color=INK,style="italic")

fig.suptitle("Behavioral parity, but only the model-derived filter repairs the cortex",
             fontsize=15,fontweight="bold",color=NAVY,y=0.975)
fig.savefig(OUT,dpi=300,facecolor="white")
print("saved",OUT)
