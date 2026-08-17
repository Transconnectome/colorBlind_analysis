#!/usr/bin/env python3
"""
Bar graph: per-model LOCO performance across ROIs.
- 4 models × 1 figure each (separate PNG files)
- 4 bars per figure (V1, V2, V3, hV4)
- HC mean ± SEM with individual subject dots
- Permutation null overlay for Ridge-GCV
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from pathlib import Path

# ── Paths ──
BASE = Path(__file__).resolve().parent.parent
VALID_DIR = BASE / "results" / "validation"
STOUFFER_FILE = BASE / "results" / "neutralization" / "n1_stouffer_omnibus.json"
FIG_DIR = BASE / "figures"
FIG_DIR.mkdir(exist_ok=True)

ROIS = ["V1", "V2", "V3", "V4"]
ROI_LABELS = ["V1", "V2", "V3", "hV4"]
HC_SUBS = [f"{i:02d}" for i in range(1, 7)]  # sub-01 ~ sub-06

MODEL_DEFS = [
    ("ridge_gcv",      "Ridge-GCV"),
    ("ols",            "OLS"),
    ("prior_only",     "Prior Only (SRM Group Prior)"),
    ("prior_finetune", "Prior Finetune"),
]

BAR_COLORS = ["#4C72B0", "#55A868", "#C44E52", "#8172B2"]


def load_loco(model_key):
    data = {roi: [] for roi in ROIS}
    for sub in HC_SUBS:
        fpath = VALID_DIR / f"sub-{sub}_loco.json"
        if not fpath.exists():
            continue
        with open(fpath) as f:
            d = json.load(f)
        for roi in ROIS:
            if roi in d and model_key in d[roi]:
                data[roi].append(d[roi][model_key]["mean_voxel_corr"])
            else:
                data[roi].append(np.nan)
    return data


def load_ridge_null():
    null = {}
    if not STOUFFER_FILE.exists():
        return null
    with open(STOUFFER_FILE) as f:
        st = json.load(f)
    roi_map = {"V1": "V1", "V2": "V2", "V3": "V3", "V4": "hV4"}
    for roi_f, roi_s in roi_map.items():
        if roi_s in st["per_roi"]:
            info = st["per_roi"][roi_s]
            null[roi_f] = {
                "mean_null": info["mean_null"],
                "p": info["stouffer_p"],
                "basis": info["basis"],
            }
    return null


ridge_null = load_ridge_null()

for model_key, disp_name in MODEL_DEFS:
    loco = load_loco(model_key)
    means, sems, ind_vals = [], [], []
    for roi in ROIS:
        vals = [v for v in loco[roi] if not np.isnan(v)]
        means.append(np.mean(vals) if vals else 0.0)
        sems.append(np.std(vals, ddof=1) / np.sqrt(len(vals)) if vals else 0.0)
        ind_vals.append(vals)

    # ── Single figure ──
    fig, ax = plt.subplots(figsize=(5.5, 5))
    x = np.arange(len(ROIS))
    w = 0.55

    ax.bar(x, means, w, yerr=sems,
           color=BAR_COLORS, edgecolor="black", linewidth=0.8,
           capsize=5, error_kw={"linewidth": 1.2}, zorder=3)

    # Individual dots
    rng = np.random.default_rng(42)
    for i, vals in enumerate(ind_vals):
        jitter = rng.uniform(-0.12, 0.12, len(vals))
        ax.scatter(np.full(len(vals), i) + jitter, vals,
                   color="white", edgecolor="black", s=25,
                   linewidth=0.7, zorder=4, alpha=0.85)

    # Permutation null (Ridge-GCV only)
    if model_key == "ridge_gcv" and ridge_null:
        for i, roi in enumerate(ROIS):
            if roi not in ridge_null:
                continue
            nd = ridge_null[roi]
            ax.hlines(nd["mean_null"], i - w/2, i + w/2,
                      colors="red", linestyles="--", linewidth=2, zorder=5)
            p = nd["p"]
            if p < 0.01:
                sig, col = "**", "#D62728"
            elif p < 0.05:
                sig, col = "*", "#D62728"
            else:
                sig, col = "n.s.", "gray"
            y_top = max(means[i] + sems[i], nd["mean_null"]) + 0.025
            ax.text(i, y_top, sig, ha="center", va="bottom",
                    fontsize=12, fontweight="bold", color=col)

        # legend for null line
        legend_el = [
            Line2D([0], [0], color="red", linestyle="--", lw=2,
                   label="Perm. null mean"),
            Line2D([0], [0], marker="o", color="none",
                   markeredgecolor="black", markerfacecolor="white",
                   markersize=6, label="Individual HC"),
            Line2D([0], [0], color="none", label="* p<.05  ** p<.01"),
        ]
        ax.legend(handles=legend_el, fontsize=8.5, frameon=True,
                  edgecolor="gray", loc="upper left")

    ax.set_xticks(x)
    ax.set_xticklabels(ROI_LABELS, fontsize=13)
    ax.set_ylabel("LOCO voxel correlation (r)", fontsize=12)
    ax.set_title(f"{disp_name}\n(HC n={len(HC_SUBS)}, FE-6 basis)", fontsize=14,
                 fontweight="bold")
    ax.axhline(0, color="black", linewidth=0.6)
    ax.set_ylim(-0.30, 0.50)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="y", labelsize=10)

    fig.tight_layout()
    out = FIG_DIR / f"loco_bar_{model_key}.png"
    fig.savefig(out, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {out}")
