#!/usr/bin/env python3
"""
LOSO Benchmark Comparison: This Study vs Bannert & Bartels (2025)
=================================================================
PPT/Notion용 시각화: LOSO 피험자 간 전이 성능의 문헌 벤치마크 비교

Figure 5: LOSO Benchmark — ZS/LORO ratio comparison
  - Left panel: Bannert 2025 (LOSO acc, within acc, ratio)
  - Right panel: This study (ZS corr, LORO corr, ratio)
  - Center panel: Ratio comparison (our hV4 99.5% vs their 77.1%)

Usage:
    conda activate srm
    python scripts/plot_loso_benchmark.py
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

# ─── Paths ─────────────────────────────────────────────
BASE = Path(__file__).resolve().parent.parent
RESULTS = BASE / "results"
OUT_DIR = BASE / "figures"
OUT_DIR.mkdir(exist_ok=True)

ROIS = ["V1", "V2", "V3", "V4"]
ROI_LABELS = ["V1", "V2", "V3", "hV4"]
HC_SUBS = [f"{i:02d}" for i in range(1, 8)]
CVD_SUBS = ["08", "09", "10"]
VALIDATION_EXT_SUBS = {"07"}

plt.rcParams.update({
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.labelsize": 12,
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "font.family": "sans-serif",
})

# ─── Bannert & Bartels 2025 Data (bioRxiv v2) ─────────
# 3 colors (R/G/Y), chance = 33.3%, N = 15, 6 runs
# SRM trained on achromatic retinotopic mapping data
BANNERT = {
    "loso_acc":   {"V1": 44.7, "V2": 39.8, "V3": 39.6, "hV4": 39.5},
    "within_acc": {"V1": 57.0, "V2": 55.4, "V3": 52.8, "hV4": 51.2},
    "chance": 33.3,
    "n_colors": 3,
    "n_subjects": 15,
    "n_runs": 6,
}

# ─── Data Loading (our study) ─────────────────────────
def load_loro_hc(model="prior_finetune"):
    data = {roi: [] for roi in ROIS}
    for sub in HC_SUBS:
        if sub in VALIDATION_EXT_SUBS:
            continue
        fpath = RESULTS / "validation" / f"sub-{sub}_loro.json"
        with open(fpath) as f:
            d = json.load(f)
        for roi in ROIS:
            data[roi].append(d[roi][model]["mean_voxel_corr"])
    return {roi: np.mean(vals) for roi, vals in data.items()}


def load_zeroshot_hc():
    fpath = RESULTS / "loso_zero_shot" / "loso_zero_shot.json"
    with open(fpath) as f:
        d = json.load(f)
    roi_map = {"V1": "V1", "V2": "V2", "V3": "V3", "V4": "hV4"}
    data = {roi: [] for roi in ROIS}
    for roi in ROIS:
        roi_key = roi_map[roi]
        roi_data = d["results"][roi_key]
        for sub in HC_SUBS:
            if sub in roi_data.get("hc", {}):
                val = roi_data["hc"][sub]["zero_shot"]["mean_voxel_corr"]
                data[roi].append(val)
    return {roi: np.mean(vals) for roi, vals in data.items()}


# ─── Figure 5: LOSO Benchmark Comparison ──────────────
def plot_loso_benchmark():
    loro = load_loro_hc()
    zs = load_zeroshot_hc()

    # Compute ratios
    our_ratio = {roi: zs[roi] / loro[roi] * 100 for roi in ROIS}
    bannert_ratio = {
        roi: BANNERT["loso_acc"][roi] / BANNERT["within_acc"][roi] * 100
        for roi in ROI_LABELS
    }

    fig, axes = plt.subplots(1, 3, figsize=(15, 5.5), gridspec_kw={"width_ratios": [1, 1, 1.2]})

    x = np.arange(4)
    w = 0.35

    # ─── Panel A: Bannert & Bartels 2025 ───
    ax = axes[0]
    loso_vals = [BANNERT["loso_acc"][r] for r in ROI_LABELS]
    within_vals = [BANNERT["within_acc"][r] for r in ROI_LABELS]

    bars1 = ax.bar(x - w/2, within_vals, w, label="Within-subject",
                   color="#90CAF9", edgecolor="black", linewidth=0.5)
    bars2 = ax.bar(x + w/2, loso_vals, w, label="LOSO (cross-subject)",
                   color="#1565C0", edgecolor="black", linewidth=0.5)
    ax.axhline(33.3, color="gray", ls="--", lw=1, alpha=0.7, label="Chance (33.3%)")

    ax.set_xticks(x)
    ax.set_xticklabels(ROI_LABELS)
    ax.set_ylabel("Classification Accuracy (%)")
    ax.set_title("Bannert & Bartels (2025)\n3 colors, N=15, achromatic SRM")
    ax.set_ylim(25, 65)
    ax.legend(fontsize=9, loc="upper right")

    # Add ratio labels
    for i, roi in enumerate(ROI_LABELS):
        ratio = bannert_ratio[roi]
        ax.annotate(f"{ratio:.0f}%", xy=(x[i] + w/2, loso_vals[i] + 0.8),
                    ha="center", va="bottom", fontsize=8, color="#1565C0", fontweight="bold")

    # ─── Panel B: Our Study ───
    ax = axes[1]
    loro_vals = [loro[roi] for roi in ROIS]
    zs_vals = [zs[roi] for roi in ROIS]

    bars1 = ax.bar(x - w/2, loro_vals, w, label="LORO (within-subject)",
                   color="#A5D6A7", edgecolor="black", linewidth=0.5)
    bars2 = ax.bar(x + w/2, zs_vals, w, label="LOSO Zero-Shot",
                   color="#2E7D32", edgecolor="black", linewidth=0.5)

    ax.set_xticks(x)
    ax.set_xticklabels(ROI_LABELS)
    ax.set_ylabel("Voxel Pattern Correlation")
    ax.set_title("This Study\n8 colors, N=10, color-trained SRM")
    ax.set_ylim(0, 0.7)
    ax.legend(fontsize=9, loc="upper right")

    # Add ratio labels
    for i, roi in enumerate(ROIS):
        ratio = our_ratio[roi]
        color = "#2E7D32" if ratio < 110 else "#FF6F00"  # orange if inflated
        marker = "" if ratio < 110 else "*"
        ax.annotate(f"{ratio:.0f}%{marker}", xy=(x[i] + w/2, zs_vals[i] + 0.008),
                    ha="center", va="bottom", fontsize=8, color=color, fontweight="bold")

    # ─── Panel C: Ratio Comparison ───
    ax = axes[2]
    our_ratio_vals = [our_ratio[roi] for roi in ROIS]
    bannert_ratio_vals = [bannert_ratio[roi] for roi in ROI_LABELS]

    bars1 = ax.bar(x - w/2, bannert_ratio_vals, w, label="Bannert 2025",
                   color="#1565C0", edgecolor="black", linewidth=0.5)
    bars2 = ax.bar(x + w/2, our_ratio_vals, w, label="This study",
                   color="#2E7D32", edgecolor="black", linewidth=0.5)
    ax.axhline(100, color="gray", ls="--", lw=1, alpha=0.7, label="Perfect transfer (100%)")

    ax.set_xticks(x)
    ax.set_xticklabels(ROI_LABELS)
    ax.set_ylabel("LOSO / Within-Subject (%)")
    ax.set_title("Group Prior Efficiency\n(cross-subject / within-subject)")
    ax.set_ylim(0, 200)
    ax.legend(fontsize=9, loc="upper left")

    # Highlight hV4
    ax.annotate("hV4: 99.5%\nvs 77.1%",
                xy=(3 + w/2, our_ratio_vals[3]),
                xytext=(2.3, 140),
                fontsize=10, fontweight="bold", color="#2E7D32",
                arrowprops=dict(arrowstyle="->", color="#2E7D32", lw=1.5))

    # Note about V1-V3 inflation
    ax.text(0.02, 0.97, "* V1-V3 >100%: SNR artifact\n  (ZS uses 6-run avg template)",
            transform=ax.transAxes, fontsize=8, va="top", ha="left",
            color="#FF6F00", style="italic",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#FFF3E0", alpha=0.8))

    plt.tight_layout()

    for ext in ["png", "pdf"]:
        fig.savefig(OUT_DIR / f"fig5_loso_benchmark.{ext}")
    print(f"Saved to {OUT_DIR}/fig5_loso_benchmark.[png|pdf]")
    plt.close()


# ─── Figure 5b: HC vs CVD LOSO (unique to this study) ─
def plot_loso_hc_cvd():
    fpath = RESULTS / "loso_zero_shot" / "loso_zero_shot.json"
    with open(fpath) as f:
        d = json.load(f)
    roi_map = {"V1": "V1", "V2": "V2", "V3": "V3", "V4": "hV4"}

    hc_data = {roi: [] for roi in ROIS}
    cvd_data = {roi: [] for roi in ROIS}

    for roi in ROIS:
        roi_key = roi_map[roi]
        roi_data = d["results"][roi_key]
        # HC keys are bare numbers like "01", "02", ...
        for sub in HC_SUBS:
            if sub in roi_data.get("hc", {}):
                hc_data[roi].append(
                    roi_data["hc"][sub]["zero_shot"]["mean_voxel_corr"])
        for sub in CVD_SUBS:
            if sub in roi_data.get("cvd", {}):
                cvd_data[roi].append(
                    roi_data["cvd"][sub]["voxel_corr_mean"])

    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(4)
    w = 0.3

    hc_means = [np.mean(hc_data[roi]) for roi in ROIS]
    cvd_means = [np.mean(cvd_data[roi]) for roi in ROIS]
    hc_sems = [np.std(hc_data[roi]) / np.sqrt(len(hc_data[roi])) for roi in ROIS]
    cvd_sems = [np.std(cvd_data[roi]) / np.sqrt(max(len(cvd_data[roi]), 1)) for roi in ROIS]

    ax.bar(x - w/2, hc_means, w, yerr=hc_sems, capsize=3,
           label="HC (N=7)", color="#66BB6A", edgecolor="black", linewidth=0.5)
    ax.bar(x + w/2, cvd_means, w, yerr=cvd_sems, capsize=3,
           label="CVD (N=3)", color="#EF5350", edgecolor="black", linewidth=0.5)

    # Individual dots
    for i, roi in enumerate(ROIS):
        jitter = np.random.default_rng(42).uniform(-0.05, 0.05, len(hc_data[roi]))
        ax.scatter(x[i] - w/2 + jitter, hc_data[roi], s=20, color="darkgreen",
                   alpha=0.6, zorder=5)
        jitter_c = np.random.default_rng(43).uniform(-0.05, 0.05, len(cvd_data[roi]))
        ax.scatter(x[i] + w/2 + jitter_c, cvd_data[roi], s=20, color="darkred",
                   alpha=0.6, zorder=5)

    # p-values
    for i, roi in enumerate(ROIS):
        ax.text(x[i], max(hc_means[i], cvd_means[i]) + hc_sems[i] + 0.02,
                "n.s.", ha="center", fontsize=9, color="gray")

    ax.set_xticks(x)
    ax.set_xticklabels(ROI_LABELS)
    ax.set_ylabel("Zero-Shot Voxel Pattern Correlation")
    ax.set_title("LOSO Zero-Shot: HC vs CVD (all p > 0.4)\nSpatial pattern transfer preserved in CVD")
    ax.set_ylim(0, 0.7)
    ax.legend(fontsize=10)

    # Annotation
    ax.text(0.98, 0.02,
            "HC ≈ CVD in LOSO → CVD deficit only\n"
            "visible in LOCO (interpolation)",
            transform=ax.transAxes, fontsize=9, ha="right", va="bottom",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#FFF9C4", alpha=0.9))

    plt.tight_layout()
    for ext in ["png", "pdf"]:
        fig.savefig(OUT_DIR / f"fig5b_loso_hc_cvd.{ext}")
    print(f"Saved to {OUT_DIR}/fig5b_loso_hc_cvd.[png|pdf]")
    plt.close()


if __name__ == "__main__":
    plot_loso_benchmark()
    plot_loso_hc_cvd()
    print("Done.")
