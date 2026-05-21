#!/usr/bin/env python
"""
plot_summary.py — Single composite overview figure for run-count validation.

Layout (3 rows × 2 cols, 16×11):
  Row 0 left  — Process flow text panel
  Row 0 right — Metric inventory by tier (text table)
  Row 1 left  — Consensus table (T1/T2/T3a/T3b/ALL × ROI × n)
  Row 1 right — Cohen's d × n for V1, V2, V3, V4 (CVD subjects)
  Row 2 left  — Op-B vulnerable-set retention × n (V1 + V2 + V3 + V4)
  Row 2 right — LOCO ρ × n for V1 (the recommended primary endpoint)

Output: figs/summary_overview.png
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec

PROJECT_ROOT = Path(__file__).resolve().parents[3]
VALID_DIR = PROJECT_ROOT / "analysis" / "future_phase3_behavioral_analysis" / \
    "run_count_validation"
FIG_DIR = VALID_DIR / "figs"
N_VALUES = [2, 3, 4, 5, 6]
ROIS = ["V1", "V2", "V3", "V4"]
CVD = ["08", "09", "10"]
HC = [f"{i:02d}" for i in range(1, 8)]
PALETTE = {
    "08": "#d62728",
    "09": "#1f77b4",
    "10": "#7f7f7f",
    "HC": "#2ca02c",
}


def load(name):
    with open(VALID_DIR / name) as f:
        return json.load(f)


def main():
    consensus = load("consensus_table.json")
    t3 = load("tier3_outcome_detection.json")
    prof = load("profile_stability.json")
    sat = load("v1_saturation_loco.json")

    fig = plt.figure(figsize=(18, 13))
    gs = GridSpec(3, 2, figure=fig, hspace=0.45, wspace=0.25,
                  left=0.06, right=0.97, top=0.95, bottom=0.05)

    # ----- Row 0 left: process flow -----
    ax = fig.add_subplot(gs[0, 0])
    ax.axis("off")
    proc_text = (
        "PROCESS\n"
        "------------------------------------------------\n"
        "1. Original question: can we reduce n=6 -> n<6?\n"
        "   v1 (May 20): LOCO rho + crossnobis RDM only\n"
        "   -> single-outcome metric is insufficient (feedback)\n\n"
        "2. Reframed as 3 independent questions:\n"
        "   (A) Is the raw signal reliably captured?\n"
        "   (B) Does representational geometry reproduce?\n"
        "   (C) Is the HC-vs-CVD outcome detectable?\n\n"
        "3. Tier 1/2/3 framework re-run (v2, May 21):\n"
        "   - 9 metrics x 4 ROI x 10 subj x 5 n x C(6,n) subsets\n"
        "   - Stockman-derived baseline (v1 stale fixed)\n"
        "   - sub-10 null control separated from gating\n\n"
        "4. Consensus rule: 4 criteria must pass jointly\n"
        "5. Recommendation: V1 primary, n=5 baseline\n"
        "                   (n=4 fallback if time-limited)"
    )
    ax.text(0.0, 1.0, proc_text, va="top", ha="left",
            fontsize=10.5, family="monospace",
            transform=ax.transAxes)

    # ----- Row 0 right: metric inventory -----
    ax = fig.add_subplot(gs[0, 1])
    ax.axis("off")
    inv_text = (
        "METRIC INVENTORY (9 metrics, 3 tiers)\n"
        "------------------------------------------------\n"
        "TIER 1 -- Signal quality (raw data)\n"
        "  - beta-split-half voxel r    (per color, mean)\n"
        "  - LORO 8-way decoding acc    (chance = 0.125)\n"
        "  - GCV alpha distribution     (over-regularization)\n\n"
        "TIER 2 -- Geometric stability (RDM)\n"
        "  - Crossnobis noise ceiling   (lower + SB upper)\n"
        "  - Procrustes split-half      (configuration cost)\n"
        "  - Circular-template RSA      (vs chord-distance)\n\n"
        "TIER 3 -- Outcome detection (HC vs CVD)\n"
        "  - LOCO rho mean + per-color profile\n"
        "  - Cohen's d                  (PRIMARY: vs HC dist)\n"
        "  - Op-A profile rank stability (across subsets)\n"
        "  - Op-B vulnerable-set retention vs n=6 anchor\n"
        "  - Permutation null           [DEPRECATED: bias]"
    )
    ax.text(0.0, 1.0, inv_text, va="top", ha="left",
            fontsize=10.5, family="monospace",
            transform=ax.transAxes)

    # ----- Row 1 left: consensus table -----
    ax = fig.add_subplot(gs[1, 0])
    ax.axis("off")
    cols = ["ROI"] + sum([[f"n={n}\nT1", "T2", "T3a", "T3b", "ALL"]
                          for n in N_VALUES], [])
    cell_text = []
    cell_colors = []
    for r in consensus:
        line = [r["ROI"]]
        cline = ["white"]
        for n in N_VALUES:
            cell = r[f"n={n}"]
            for key in ["T1", "T2", "T3a", "T3b", "ALL"]:
                line.append("✓" if cell[key] else "·")
                cline.append("#c6e7c6" if cell[key] else "#f7d6d6")
        cell_text.append(line)
        cell_colors.append(cline)
    tbl = ax.table(cellText=cell_text, colLabels=cols,
                   cellColours=cell_colors, loc="center", cellLoc="center")
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8)
    tbl.scale(1, 1.3)
    ax.set_title("Consensus pass/fail   (T1 signal · T2 geom · T3a power · T3b profile · ALL)",
                 fontsize=11, pad=8)

    # ----- Row 1 right: Cohen's d × n for all ROIs × CVD -----
    ax = fig.add_subplot(gs[1, 1])
    for roi, marker in zip(ROIS, ["o", "s", "^", "D"]):
        for subj in ["08", "09"]:
            ds = [t3["posthoc"]["per_roi"][roi][str(n)][subj]["cohens_d_vs_hc"]
                  for n in N_VALUES]
            ls = "-" if subj == "08" else "--"
            ax.plot(N_VALUES, ds, marker=marker, ls=ls,
                    color={"V1": "#d62728", "V2": "#ff7f0e",
                           "V3": "#1f77b4", "V4": "#7f7f7f"}[roi],
                    label=f"{roi} sub-{subj}", lw=1.5, ms=5)
    ax.axhspan(0.8, 6.0, alpha=0.08, color="green")
    ax.axhline(0.8, ls=":", color="k", lw=0.8)
    ax.axhline(0, ls="--", color="gray", lw=0.5)
    ax.set_xticks(N_VALUES)
    ax.set_ylim(-1, 5)
    ax.grid(alpha=0.3)
    ax.set_title("HC-vs-CVD Cohen's d   "
                 "(solid = sub-08 deutan, dashed = sub-09 protan)",
                 fontsize=11)
    ax.set_ylabel("Cohen's d  (HC mean − CVD) / SD_HC")
    ax.set_xlabel("number of runs (n)")
    ax.legend(fontsize=7.5, ncol=2, loc="upper right")
    # Annotation
    ax.text(2.1, 0.4, "d >= 0.8 threshold\n(large effect)",
            fontsize=8, color="darkgreen", style="italic")
    ax.text(2.1, -0.5, "V4 sub-09: d never reaches 0.8\n-> hV4 not viable as primary",
            fontsize=8, color="#7f7f7f", style="italic")

    # ----- Row 2 left: Op-B retention -----
    ax = fig.add_subplot(gs[2, 0])
    for roi, color in zip(ROIS, ["#d62728", "#ff7f0e", "#1f77b4", "#7f7f7f"]):
        for subj, ls in zip(["08", "09"], ["-", "--"]):
            vals = [prof["per_roi"][roi][str(n)][subj]["op_b"]["mean_retention"]
                    for n in N_VALUES]
            ax.plot(N_VALUES, vals, marker="o", ls=ls, color=color,
                    label=f"{roi} sub-{subj}", lw=1.5, ms=4)
    ax.axhline(0.5, ls=":", color="k", lw=0.7, label="threshold 0.50")
    ax.axhline(0.07, ls=":", color="r", lw=0.6, label="chance (k=2/8)")
    ax.set_xticks(N_VALUES)
    ax.set_ylim(0, 1.05)
    ax.grid(alpha=0.3)
    ax.set_title("Op-B vulnerable-set retention   (vs n=6 anchor bottom-2)",
                 fontsize=11)
    ax.set_ylabel("retention fraction")
    ax.set_xlabel("number of runs (n)")
    ax.legend(fontsize=7, ncol=2, loc="lower right")

    # ----- Row 2 right: V1 mean LOCO ρ with HC band -----
    ax = fig.add_subplot(gs[2, 1])
    # HC distribution at each n
    hc_means_by_n = []
    hc_sd_by_n = []
    for n in N_VALUES:
        vals = []
        for hc in HC:
            cells = sat["per_roi"]["V1"][str(n)][hc]
            rhos = [c["rho"] for c in cells.values()]
            vals.append(np.mean(rhos))
        hc_means_by_n.append(np.mean(vals))
        hc_sd_by_n.append(np.std(vals))
    hc_means_by_n = np.array(hc_means_by_n); hc_sd_by_n = np.array(hc_sd_by_n)
    ax.fill_between(N_VALUES, hc_means_by_n - hc_sd_by_n,
                    hc_means_by_n + hc_sd_by_n,
                    color="#2ca02c", alpha=0.2, label="HC ±SD")
    ax.plot(N_VALUES, hc_means_by_n, color="#2ca02c", lw=2, label="HC mean (n=7)")
    for subj in CVD:
        means = []; sds = []
        for n in N_VALUES:
            cells = sat["per_roi"]["V1"][str(n)][subj]
            rhos = [c["rho"] for c in cells.values()]
            means.append(np.mean(rhos)); sds.append(np.std(rhos))
        ax.errorbar(N_VALUES, means, yerr=sds, color=PALETTE[subj],
                    marker="o", capsize=2, lw=1.5, label=f"sub-{subj}")
    ax.axhline(0, ls=":", color="k", lw=0.7)
    ax.set_xticks(N_VALUES)
    ax.set_ylim(-0.4, 0.5)
    ax.grid(alpha=0.3)
    ax.set_title("V1 mean LOCO ρ   (recommended primary endpoint)",
                 fontsize=11)
    ax.set_ylabel("LOCO ρ mean ± subset SD")
    ax.set_xlabel("number of runs (n)")
    ax.legend(fontsize=8, loc="upper left")
    ax.text(4.5, -0.32, "n*=4: ALL 4 criteria pass\nfor sub-08 + sub-09",
            fontsize=8.5, color="darkblue", style="italic",
            bbox=dict(boxstyle="round", facecolor="#e0e8f0", alpha=0.8))

    fig.suptitle(
        "Run-count validation v2  --  Process | Metrics | Criteria | Results",
        fontsize=14, y=0.985, fontweight="bold")
    out = FIG_DIR / "summary_overview.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
