#!/usr/bin/env python3
"""
exp2 neural HC-likeness figure (sub-08) — cloned from docs/PAPER/Figures/scripts/generate_fig2.py
style (mm sizing, gray HC reference bar + jittered HC dots, condition markers, Wong palette,
stripped spines, Crawford-Howell single-case stars, PNG+PDF @300dpi).

2x2 — functional (top) vs geometry (bottom):
  A  LOCO rho (FE-6 forward-encoder, voxel prediction)   higher = HC-like
  B  LORO accuracy (FE-6 forward-encoder, discrimination) higher = HC-like
  C  SRM Procrustes disparity (HC shared space)           lower  = HC-like
  D  RDM-rho to HC (corr-dist RDM in SRM space, paper)    higher = HC-like

Conditions per ROI: HC reference (bar = mean, error = SD) + 3 markers
(No-filter, Window=macOS, Optimal=personalized). Single subject sub-08, descriptive.

Usage: python generate_exp2_fig.py [--variant native|matched]
"""
import json
import argparse
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
from pathlib import Path
from scipy import stats

BASE = Path("/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis")
RESDIR = BASE / "analysis/future_phase3_behavioral_analysis/exp2_neural/results"
OUTDIR = BASE / "analysis/future_phase3_behavioral_analysis/exp2_neural/figures"

ROIS = ["V1", "V2", "V3", "V4"]
ROI_LABELS = ["V1", "V2", "V3", "hV4"]

# Wong colorblind-safe palette
HC_BAR   = "#CCCCCC"
HC_DOT   = "#555555"
C_NOFILT = "#666666"   # no-filter
C_WINDOW = "#0072B2"   # macOS Window (blue)
C_OPTIM  = "#D55E00"   # personalized Optimal (orange = focus)
COND_STYLE = {
    "nofilter": (C_NOFILT, "o", "No-filter"),
    "window":   (C_WINDOW, "s", "Window (macOS)"),
    "optimal":  (C_OPTIM,  "D", "Optimal (ours)"),
}


def crawford_howell(x, mean_hc, sd_hc, n, tail):
    if sd_hc <= 0:
        return 0.0, 1.0
    t = (x - mean_hc) / (sd_hc * np.sqrt((n + 1) / n))
    if tail == "lower":   # deficit = x below HC
        p = stats.t.cdf(t, df=n - 1)
    else:                 # "upper": deficit = x above HC (disparity)
        p = stats.t.sf(t, df=n - 1)
    return float(t), float(p)


def sig_star(p):
    if p < 0.001: return "***"
    if p < 0.01:  return "**"
    if p < 0.05:  return "*"
    return ""


def strip(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", default="native", choices=["native", "matched"])
    ap.add_argument("--subject", default="08", help="CVD subject id, e.g. 08 / 09")
    args = ap.parse_args()
    subj = f"sub-{args.subject}"
    hl = json.load(open(RESDIR / f"exp2_hc_likeness_{subj}_{args.variant}.json"))
    cv = json.load(open(RESDIR / f"exp2_convergent_{subj}_{args.variant}.json"))

    # ---- assemble per-panel data: hc(mean,sd,n,dots) + cond values + CH tail ----
    def panel_data(metric):
        d = {"hc_mean": [], "hc_sd": [], "hc_dots": [], "n": [],
             "nofilter": [], "window": [], "optimal": [], "tail": metric_tail[metric]}
        for roi in ROIS:
            h = hl[roi]; c = cv[roi]
            if metric == "loco":
                d["hc_mean"].append(h["hc_loco_rho_n4_mean"]); d["hc_sd"].append(h["hc_loco_rho_n4_sd"])
                d["hc_dots"].append(h["hc_loco_rho_n4_values"]); d["n"].append(h["hc_n"])
                d["nofilter"].append(h["nofilter_baseline_exp1"]["loco_rho_n4_matched"])
                d["window"].append(h["conditions"]["window"]["loco_rho_mean"])
                d["optimal"].append(h["conditions"]["optimal"]["loco_rho_mean"])
            elif metric == "loro":
                d["hc_mean"].append(h["hc_loro_fe6_acc_mean"]); d["hc_sd"].append(h["hc_loro_fe6_acc_sd"])
                d["hc_dots"].append(None); d["n"].append(h["hc_n"])
                d["nofilter"].append(h["nofilter_baseline_exp1"]["loro_fe6_acc"])
                d["window"].append(h["conditions"]["window"]["loro_fe6_acc"])
                d["optimal"].append(h["conditions"]["optimal"]["loro_fe6_acc"])
            elif metric == "srm":
                s = c["srm"]; d["hc_mean"].append(s["hc_disp_mean"]); d["hc_sd"].append(s["hc_disp_sd"])
                d["hc_dots"].append(None); d["n"].append(h["hc_n"])
                d["nofilter"].append(s["conditions"]["nofilter"]["disparity"])
                d["window"].append(s["conditions"]["window"]["disparity"])
                d["optimal"].append(s["conditions"]["optimal"]["disparity"])
            elif metric == "rdm":
                rp = c["srm_rdm_paper"]
                d["hc_mean"].append(rp["_hc"]["spearman_self_loo_mean"]); d["hc_sd"].append(np.nan)
                d["hc_dots"].append(None); d["n"].append(h["hc_n"])
                d["nofilter"].append(rp["nofilter"]["spearman_to_hc"])
                d["window"].append(rp["window"]["spearman_to_hc"])
                d["optimal"].append(rp["optimal"]["spearman_to_hc"])
        return d

    metric_tail = {"loco": "lower", "loro": "lower", "srm": "upper", "rdm": "lower"}
    panels = [
        ("loco", "A", "LOCO ρ (voxel prediction)", "Functional — forward encoding", "Decoding ρ", True),
        ("loro", "B", "LORO accuracy (discrimination)", "Functional — forward encoding", "Proportion correct", True),
        ("srm",  "C", "SRM disparity", "Geometry — shared-space alignment", "Procrustes disparity", False),
        ("rdm",  "D", "RDM similarity to HC", "Geometry — representational RDM", "Spearman ρ to HC", True),
    ]

    mm = 1 / 25.4
    fig = plt.figure(figsize=(180 * mm, 158 * mm))
    gs = fig.add_gridspec(2, 2, left=0.085, right=0.985, top=0.85, bottom=0.16,
                          wspace=0.34, hspace=0.62)
    x = np.arange(len(ROIS)); bw = 0.6

    for idx, (metric, letter, title, group, ylabel, higher_better) in enumerate(panels):
        ax = fig.add_subplot(gs[idx // 2, idx % 2])
        d = panel_data(metric)
        hc_mean = np.array(d["hc_mean"], float); hc_sd = np.array(d["hc_sd"], float)
        # HC reference bar + SD
        ax.bar(x, hc_mean, width=bw, color=HC_BAR, zorder=2, linewidth=0)
        if np.isfinite(hc_sd).any():
            ax.errorbar(x, hc_mean, yerr=np.nan_to_num(hc_sd), fmt="none",
                        color="#333", capsize=2.5, linewidth=0.9, zorder=3)
        # HC individual dots where available (LOCO)
        np.random.seed(42)
        for i in range(len(ROIS)):
            if d["hc_dots"][i] is not None:
                v = np.array(d["hc_dots"][i]); jit = np.random.uniform(-0.13, 0.13, len(v))
                ax.scatter(i + jit, v, s=7, color=HC_DOT, alpha=0.6, zorder=4, linewidths=0)
        # condition markers (slight x-offset so they don't overlap) + CH stars
        offs = {"nofilter": -0.22, "window": 0.0, "optimal": 0.22}
        yr = None
        for cond in ["nofilter", "window", "optimal"]:
            col, mk, _ = COND_STYLE[cond]
            yv = np.array(d[cond], float)
            ax.plot(x + offs[cond], yv, marker=mk, color=col, markersize=6, linewidth=0,
                    markeredgecolor="white", markeredgewidth=0.5, zorder=5)
        ylo, yhi = ax.get_ylim(); yr = yhi - ylo
        for cond in ["nofilter", "window", "optimal"]:
            col, mk, _ = COND_STYLE[cond]
            yv = np.array(d[cond], float)
            for i in range(len(ROIS)):
                if not np.isfinite(hc_sd[i]):
                    continue
                _, p = crawford_howell(yv[i], hc_mean[i], hc_sd[i], d["n"][i], d["tail"])
                s = sig_star(p)
                if s:
                    ax.text(x[i] + offs[cond], yv[i] + yr * 0.03, s, fontsize=7, color=col,
                            ha="center", va="bottom", fontweight="bold")
        ax.set_xticks(x); ax.set_xticklabels(ROI_LABELS, fontsize=7)
        ax.set_ylabel(ylabel, fontsize=7, labelpad=3)
        ax.tick_params(axis="both", labelsize=6.5, length=3)
        ax.axhline(0, color="#bbb", linewidth=0.6, zorder=0)
        strip(ax)
        ax.text(-0.02, 1.18, letter, transform=ax.transAxes, fontsize=11, fontweight="bold",
                va="bottom", ha="left")
        ax.text(0.08, 1.19, title, transform=ax.transAxes, fontsize=7.5, va="bottom",
                ha="left", color="#222", fontweight="bold")
        ax.text(0.08, 1.07, group + ("  (↑ HC-like)" if higher_better else "  (↓ HC-like)"),
                transform=ax.transAxes, fontsize=6.3, va="bottom", ha="left", color="#666")

    # legend
    handles = [
        mpatches.Patch(facecolor=HC_BAR, label="HC reference (mean ± SD)", edgecolor="none"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor=HC_DOT, markersize=5,
               label="HC individuals (LOCO)", linewidth=0),
    ] + [Line2D([0], [0], marker=COND_STYLE[c][1], color="w", markerfacecolor=COND_STYLE[c][0],
                markersize=6, label=COND_STYLE[c][2], linewidth=0) for c in ["nofilter", "window", "optimal"]]
    fig.legend(handles=handles, loc="lower center", ncol=5, fontsize=6.5, frameon=False,
               bbox_to_anchor=(0.5, 0.055))
    fig.suptitle(f"exp2 neural HC-likeness — {subj} ({args.variant} voxels, descriptive)",
                 y=0.965, fontsize=9, fontweight="bold")

    OUTDIR.mkdir(parents=True, exist_ok=True)
    png = OUTDIR / f"exp2_neural_hc_likeness_{subj}_{args.variant}.png"
    pdf = OUTDIR / f"exp2_neural_hc_likeness_{subj}_{args.variant}.pdf"
    fig.savefig(png, dpi=300, bbox_inches="tight")
    fig.savefig(pdf, bbox_inches="tight")
    print(f"Saved: {png}")
    print(f"Saved: {pdf}")


if __name__ == "__main__":
    main()
