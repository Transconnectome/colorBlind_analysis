#!/usr/bin/env python
"""
plot_saturation.py — Visualize n-saturation curves for run-count validation.

Outputs:
  run_count_validation/fig_saturation_loco.png
  run_count_validation/fig_saturation_sd.png
  run_count_validation/fig_saturation_crossnobis.png
  run_count_validation/fig_decision.png (annotated cut-off panel)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RES_DIR = PROJECT_ROOT / "analysis" / "future_phase3_behavioral_analysis" / \
    "run_count_validation"

# Aesthetics
mpl.rcParams["axes.grid"] = True
mpl.rcParams["grid.alpha"] = 0.3
mpl.rcParams["axes.spines.top"] = False
mpl.rcParams["axes.spines.right"] = False
mpl.rcParams["font.size"] = 9.5

ROIS = ["V1", "V2", "V3", "V4"]
ROI_LABELS = {"V1": "V1", "V2": "V2", "V3": "V3", "V4": "hV4"}
CVD = ["08", "09", "10"]
CVD_LABEL = {"08": "sub-08 (deutan)", "09": "sub-09 (protan)", "10": "sub-10 (near-normal)"}
HC = [f"{i:02d}" for i in range(1, 8)]
N_VALUES = [2, 3, 4, 5, 6]
N_VALUES_EVEN = [4, 6]

CVD_COLORS = {"08": "#d62728", "09": "#2ca02c", "10": "#7f7f7f"}
HC_COLOR = "#1f77b4"


def load_data():
    with open(RES_DIR / "v1_saturation_loco.json") as f:
        loco = json.load(f)
    with open(RES_DIR / "v1_saturation_crossnobis.json") as f:
        cn = json.load(f)
    return loco, cn


def collect_loco(loco, roi, subj, n):
    """Return numpy array of LOCO ρ values across C(6,n) subsets."""
    if subj == "HC_mean":
        vals = []
        for hc_s in HC:
            d = loco["per_roi"][roi][str(n)].get(hc_s, {})
            for v in d.values():
                vals.append(v["rho"])
        return np.array(vals)
    return np.array([v["rho"] for v in loco["per_roi"][roi][str(n)][subj].values()])


def collect_crossnobis(cn, roi, subj, n):
    vals = []
    for v in cn["per_roi"][roi][str(n)][subj].values():
        if not np.isnan(v["mean_spearman"]):
            vals.append(v["mean_spearman"])
    return np.array(vals)


# ---------------------------------------------------------------------------
# Figure 1: LOCO ρ saturation grid (4 ROIs × 3 CVD + HC mean)
# ---------------------------------------------------------------------------
def fig_loco_saturation(loco):
    fig, axes = plt.subplots(1, 4, figsize=(14, 4), sharey=True)
    for ax, roi in zip(axes, ROIS):
        for subj in CVD:
            means, sds, low, high = [], [], [], []
            for n in N_VALUES:
                vals = collect_loco(loco, roi, subj, n)
                means.append(vals.mean())
                sds.append(vals.std())
                low.append(np.percentile(vals, 10) if len(vals) > 1 else vals[0])
                high.append(np.percentile(vals, 90) if len(vals) > 1 else vals[0])
            means = np.array(means); sds = np.array(sds)
            low = np.array(low); high = np.array(high)
            ax.fill_between(N_VALUES, low, high, color=CVD_COLORS[subj], alpha=0.13)
            ax.errorbar(N_VALUES, means, yerr=sds, marker='o', ms=6, lw=1.8,
                        color=CVD_COLORS[subj], label=CVD_LABEL[subj], capsize=3)

        # HC mean
        hc_means, hc_sds = [], []
        for n in N_VALUES:
            vals = collect_loco(loco, roi, "HC_mean", n)
            hc_means.append(vals.mean())
            hc_sds.append(vals.std())
        ax.errorbar(N_VALUES, hc_means, yerr=hc_sds, marker='s', ms=5, lw=1.6,
                    color=HC_COLOR, label="HC mean (n=7)",
                    linestyle='--', alpha=0.85, capsize=3)

        ax.axhline(0, color='k', lw=0.6, alpha=0.4)
        ax.axvspan(3.5, 4.5, color='gold', alpha=0.15)  # highlight n=4
        ax.set_title(f"{ROI_LABELS[roi]}", fontsize=11, fontweight='bold')
        ax.set_xlabel("n runs per condition")
        ax.set_xticks(N_VALUES)
        if roi == "V1":
            ax.set_ylabel("LOCO ρ (mean ± SD across subsets)")
    axes[0].legend(loc='lower left', fontsize=8.5, frameon=True)
    fig.suptitle("LOCO ρ saturation curve — mean ± SD across C(6,n) subsets, 10/90 percentile band",
                 y=1.02, fontsize=11)
    fig.tight_layout()
    out = RES_DIR / "fig_saturation_loco.png"
    fig.savefig(out, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return out


# ---------------------------------------------------------------------------
# Figure 2: across-subset SD decay per (subject × ROI)
# ---------------------------------------------------------------------------
def fig_sd_decay(loco):
    fig, axes = plt.subplots(1, 4, figsize=(14, 3.5), sharey=True)
    for ax, roi in zip(axes, ROIS):
        for subj in CVD:
            sds = [collect_loco(loco, roi, subj, n).std() for n in N_VALUES]
            ax.plot(N_VALUES, sds, marker='o', ms=6, lw=1.8,
                    color=CVD_COLORS[subj], label=CVD_LABEL[subj])
        hc_sds = []
        for n in N_VALUES:
            vals = collect_loco(loco, roi, "HC_mean", n)
            hc_sds.append(vals.std())
        ax.plot(N_VALUES, hc_sds, marker='s', ms=5, lw=1.5,
                color=HC_COLOR, label="HC mean", linestyle='--', alpha=0.85)

        # Annotate sub-08 SD at n=4 (decision-relevant)
        sd_n4 = collect_loco(loco, roi, "08", 4).std()
        ax.annotate(f"sub-08 SD={sd_n4:.3f}", xy=(4, sd_n4),
                    xytext=(4.3, sd_n4 + 0.02), fontsize=8,
                    color=CVD_COLORS["08"],
                    arrowprops=dict(arrowstyle='->', color=CVD_COLORS["08"], lw=0.8))

        ax.axvspan(3.5, 4.5, color='gold', alpha=0.15)
        ax.set_title(ROI_LABELS[roi], fontsize=11, fontweight='bold')
        ax.set_xlabel("n runs")
        ax.set_xticks(N_VALUES)
        ax.set_ylim(-0.005, 0.20)
        if roi == "V1":
            ax.set_ylabel("SD across C(6,n) subsets")
    axes[0].legend(loc='upper right', fontsize=8.5, frameon=True)
    fig.suptitle("Across-subset SD (stability metric) vs n — monotonic decrease, golden = n=4",
                 y=1.02, fontsize=11)
    fig.tight_layout()
    out = RES_DIR / "fig_saturation_sd.png"
    fig.savefig(out, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return out


# ---------------------------------------------------------------------------
# Figure 3: Crossnobis split-half reliability (all n ∈ {2,3,4,5,6})
# ---------------------------------------------------------------------------
def fig_crossnobis(cn):
    fig, axes = plt.subplots(1, 4, figsize=(14, 4), sharey=True)
    for ax, roi in zip(axes, ROIS):
        for subj in CVD:
            means, sds, low, high = [], [], [], []
            for n in N_VALUES:
                vals = collect_crossnobis(cn, roi, subj, n)
                if len(vals) == 0:
                    means.append(np.nan); sds.append(np.nan)
                    low.append(np.nan); high.append(np.nan); continue
                means.append(vals.mean()); sds.append(vals.std())
                low.append(np.percentile(vals, 10) if len(vals) > 1 else vals[0])
                high.append(np.percentile(vals, 90) if len(vals) > 1 else vals[0])
            means = np.array(means); sds = np.array(sds)
            low = np.array(low); high = np.array(high)
            ax.fill_between(N_VALUES, low, high, color=CVD_COLORS[subj], alpha=0.12)
            ax.errorbar(N_VALUES, means, yerr=sds, marker='o', ms=7, lw=1.8,
                        color=CVD_COLORS[subj], label=CVD_LABEL[subj], capsize=3)

        # HC mean
        hc_means, hc_sds = [], []
        for n in N_VALUES:
            all_hc_vals = []
            for hc_s in HC:
                v = collect_crossnobis(cn, roi, hc_s, n)
                if len(v):
                    all_hc_vals.extend(v)
            hc_means.append(np.nanmean(all_hc_vals) if all_hc_vals else np.nan)
            hc_sds.append(np.nanstd(all_hc_vals) if all_hc_vals else np.nan)
        ax.errorbar(N_VALUES, hc_means, yerr=hc_sds, marker='s', ms=5, lw=1.5,
                    color=HC_COLOR, label="HC mean (n=7)",
                    linestyle='--', alpha=0.85, capsize=3)

        # MVNN-CV regime band: n≥4 = LORO+MVNN, n<4 = degraded
        ax.axvspan(1.7, 3.5, color='lightgray', alpha=0.30, zorder=0)
        ax.axhline(0.5, color='red', lw=1.0, linestyle=':',
                   label='Walther r≥0.5' if roi == "V1" else None)
        ax.axhline(0, color='k', lw=0.5, alpha=0.4)
        ax.axvspan(3.5, 4.5, color='gold', alpha=0.15)
        ax.set_title(ROI_LABELS[roi], fontsize=11, fontweight='bold')
        ax.set_xlabel("n runs per condition")
        ax.set_xticks(N_VALUES)
        ax.set_ylim(-0.3, 1.05)
        if roi == "V1":
            ax.set_ylabel("Split-half RDM Spearman r")
            ax.text(2.6, -0.22, "Euclidean\nfallback\n(no MVNN)",
                    fontsize=7.5, ha='center', color='gray', style='italic')
    axes[0].legend(loc='lower right', fontsize=8.5, frameon=True)
    fig.suptitle("Crossnobis split-half RDM reliability (Walther 2016) — "
                 "gray band: n<4 single-run half uses Euclidean fallback",
                 y=1.02, fontsize=11)
    fig.tight_layout()
    out = RES_DIR / "fig_saturation_crossnobis.png"
    fig.savefig(out, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return out


# ---------------------------------------------------------------------------
# Figure 4: Decision panel — cut-off scenarios annotated
# ---------------------------------------------------------------------------
def fig_decision(loco, cn):
    """Annotated decision panel focused on hV4 (primary endpoint) + V1 (binding ROI)."""
    fig, axes = plt.subplots(2, 2, figsize=(13, 8.5))

    # Top row: hV4 LOCO + RDM
    ax = axes[0, 0]
    for subj in CVD:
        means = [collect_loco(loco, "V4", subj, n).mean() for n in N_VALUES]
        sds = [collect_loco(loco, "V4", subj, n).std() for n in N_VALUES]
        ax.errorbar(N_VALUES, means, yerr=sds, marker='o', ms=7, lw=2,
                    color=CVD_COLORS[subj], label=CVD_LABEL[subj], capsize=3)
    ax.axhline(0, color='k', lw=0.5, alpha=0.4)
    # Highlight scenarios
    for n_cut, color, label in [(3, '#d62728', 'aggressive'),
                                  (4, '#ff7f0e', 'balanced'),
                                  (5, '#2ca02c', 'conservative')]:
        ax.axvline(n_cut, color=color, lw=2.5, alpha=0.4)
        ax.text(n_cut, 0.30, f'n={n_cut}\n{label}', ha='center', fontsize=9,
                color=color, fontweight='bold')
    ax.set_xticks(N_VALUES)
    ax.set_xlabel("n runs per condition")
    ax.set_ylabel("LOCO ρ")
    ax.set_title("hV4 LOCO ρ — primary endpoint", fontsize=11, fontweight='bold')
    ax.set_ylim(-0.35, 0.40)
    ax.legend(loc='lower left', fontsize=8.5)

    # Top right: hV4 crossnobis (all n)
    ax = axes[0, 1]
    for subj in CVD:
        means = [collect_crossnobis(cn, "V4", subj, n).mean() if len(collect_crossnobis(cn, "V4", subj, n)) else np.nan
                 for n in N_VALUES]
        sds = [collect_crossnobis(cn, "V4", subj, n).std() if len(collect_crossnobis(cn, "V4", subj, n)) else np.nan
               for n in N_VALUES]
        ax.errorbar(N_VALUES, means, yerr=sds, marker='o', ms=7, lw=1.8,
                    color=CVD_COLORS[subj], label=CVD_LABEL[subj], capsize=3)
    ax.axvspan(1.7, 3.5, color='lightgray', alpha=0.30, zorder=0)
    ax.axhline(0.5, color='red', linestyle=':', lw=1.2, label='Walther r≥0.5')
    ax.set_xticks(N_VALUES)
    ax.set_xlabel("n runs")
    ax.set_ylabel("Split-half RDM Spearman r")
    ax.set_title("hV4 Crossnobis split-half RDM reliability", fontsize=11, fontweight='bold')
    ax.set_ylim(-0.3, 1.05)
    ax.legend(loc='lower right', fontsize=8.5)

    # Bottom row: V1 LOCO + sub-09 V4 (the two "binding" cells)
    ax = axes[1, 0]
    for subj in CVD:
        means = [collect_loco(loco, "V1", subj, n).mean() for n in N_VALUES]
        sds = [collect_loco(loco, "V1", subj, n).std() for n in N_VALUES]
        ax.errorbar(N_VALUES, means, yerr=sds, marker='o', ms=7, lw=2,
                    color=CVD_COLORS[subj], label=CVD_LABEL[subj], capsize=3)
    ax.axhline(0, color='k', lw=0.5, alpha=0.4)
    # Annotate sub-08 V1 ρ retention
    rho6 = collect_loco(loco, "V1", "08", 6).mean()
    rho4 = collect_loco(loco, "V1", "08", 4).mean()
    pct = abs(rho4) / abs(rho6) * 100
    ax.annotate(f'sub-08 V1: n=4 ρ={rho4:+.3f}\n  ({pct:.0f}% of n=6 amplitude)',
                xy=(4, rho4), xytext=(2.3, -0.25), fontsize=9,
                color=CVD_COLORS["08"],
                arrowprops=dict(arrowstyle='->', color=CVD_COLORS["08"], lw=1.0))
    for n_cut in [3, 4, 5]:
        ax.axvline(n_cut, color='gray', lw=1, alpha=0.3)
    ax.set_xticks(N_VALUES)
    ax.set_xlabel("n runs")
    ax.set_ylabel("LOCO ρ")
    ax.set_title("V1 LOCO ρ — binding ROI for stricter cut-off", fontsize=11, fontweight='bold')
    ax.legend(loc='upper right', fontsize=8.5)

    # Bottom right: sub-09 across ROIs (vulnerability landmark fragility)
    ax = axes[1, 1]
    for roi in ROIS:
        means = [collect_loco(loco, roi, "09", n).mean() for n in N_VALUES]
        sds = [collect_loco(loco, roi, "09", n).std() for n in N_VALUES]
        ax.errorbar(N_VALUES, means, yerr=sds, marker='o', ms=6, lw=1.8,
                    label=ROI_LABELS[roi], capsize=3)
    ax.axhline(0, color='k', lw=0.5, alpha=0.4)
    ax.set_xticks(N_VALUES)
    ax.set_xlabel("n runs")
    ax.set_ylabel("LOCO ρ")
    ax.set_title("sub-09 (protan) — vulnerability landmark fragility",
                 fontsize=11, fontweight='bold')
    ax.legend(loc='upper right', fontsize=9, title="ROI")

    fig.suptitle("Run-count cut-off decision panel — primary (hV4) + binding (V1) + fragility (sub-09)",
                 fontsize=12, y=1.005)
    fig.tight_layout()
    out = RES_DIR / "fig_decision.png"
    fig.savefig(out, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return out


def main():
    loco, cn = load_data()
    files = []
    files.append(fig_loco_saturation(loco))
    files.append(fig_sd_decay(loco))
    files.append(fig_crossnobis(cn))
    files.append(fig_decision(loco, cn))
    print("Saved figures:")
    for f in files:
        print(f"  {f}")


if __name__ == "__main__":
    main()
