#!/usr/bin/env python3
"""
Visualization for activation prior analysis.
Generates a multi-panel figure summarizing HC vs CVD activation comparison.
"""

import numpy as np
import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path
from scipy import stats

# ── Config ──────────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).parent.parent / "phase1_preprocess_decoding" / "results" / "full_dataset_C010"
SRM_PATH = Path(__file__).parent / "results" / "loo_consistent" / "20260218_163819" / "loo_consistent_results.json"
OUT_DIR = Path(__file__).parent / "results" / "activation_prior"
OUT_DIR.mkdir(parents=True, exist_ok=True)

HC_SUBS = [f"sub-{i:02d}" for i in range(1, 8)]
CVD_SUBS = [f"sub-{i:02d}" for i in range(8, 11)]
ALL_SUBS = HC_SUBS + CVD_SUBS
ROIS = ["V1", "V2", "V3", "V4"]
ROI_LABELS = {"V1": "V1", "V2": "V2", "V3": "V3", "V4": "hV4"}
COLORS_HUE = ["red", "orange", "yellow", "green", "cyan", "blue", "purple", "magenta"]
PLOT_COLORS = ["#E74C3C", "#E67E22", "#F1C40F", "#27AE60", "#00BCD4", "#2980B9", "#8E44AD", "#E91E63"]
CVD_TYPES = {"sub-08": "deutan", "sub-09": "protan", "sub-10": "deutan"}

# ── Load data ───────────────────────────────────────────────────────────
subject_data = {}
for sub in ALL_SUBS:
    subject_data[sub] = {}
    for roi in ROIS:
        amp = np.load(DATA_DIR / sub / roi / "amplitudes_raw.npy")
        subject_data[sub][roi] = amp

# Load SRM disparities
with open(SRM_PATH) as f:
    srm_raw = json.load(f)
srm_data = srm_raw["results"]

# ── Figure ──────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(18, 14))
fig.suptitle("Prior Analysis: Activation-Level HC vs CVD Comparison", fontsize=14, fontweight="bold", y=0.98)

# Panel layout: 3 rows × 4 cols
# Row 1: Mean |activation| bar plot per ROI
# Row 2: Color tuning curves (mean across voxels/runs) per ROI
# Row 3: |activation| vs SRM disparity scatter per ROI

# ── Row 1: Mean |activation| per subject ────────────────────────────────
for i, roi in enumerate(ROIS):
    ax = fig.add_subplot(3, 4, i + 1)
    label = ROI_LABELS[roi]

    hc_vals = [np.abs(subject_data[s][roi]).mean() for s in HC_SUBS]
    cvd_vals = [np.abs(subject_data[s][roi]).mean() for s in CVD_SUBS]

    # Individual points
    x_hc = np.ones(len(hc_vals)) * 0 + np.random.default_rng(42).uniform(-0.15, 0.15, len(hc_vals))
    x_cvd = np.ones(len(cvd_vals)) * 1 + np.random.default_rng(43).uniform(-0.15, 0.15, len(cvd_vals))

    ax.scatter(x_hc, hc_vals, c="steelblue", s=40, alpha=0.7, zorder=3)
    ax.scatter(x_cvd, cvd_vals, c="tomato", s=60, marker="D", alpha=0.8, zorder=3)

    # Group means with error bars
    ax.errorbar(0, np.mean(hc_vals), yerr=np.std(hc_vals, ddof=1), fmt="o", color="navy",
                markersize=10, capsize=5, capthick=2, zorder=4)
    ax.errorbar(1, np.mean(cvd_vals), yerr=np.std(cvd_vals, ddof=1), fmt="D", color="darkred",
                markersize=10, capsize=5, capthick=2, zorder=4)

    # Welch's t-test
    t, p = stats.ttest_ind(hc_vals, cvd_vals, equal_var=False)
    sig = "n.s." if p >= 0.05 else f"p={p:.3f}*"

    ax.set_xticks([0, 1])
    ax.set_xticklabels(["HC", "CVD"])
    ax.set_ylabel("Mean |activation|" if i == 0 else "")
    ax.set_title(f"{label}\n{sig}", fontsize=11)
    ax.set_xlim(-0.5, 1.5)

    # Label CVD subjects
    for j, s in enumerate(CVD_SUBS):
        ax.annotate(s[-2:], (x_cvd[j], cvd_vals[j]), fontsize=7, ha="left",
                    xytext=(5, 0), textcoords="offset points")

# ── Row 2: Color tuning curves ─────────────────────────────────────────
for i, roi in enumerate(ROIS):
    ax = fig.add_subplot(3, 4, i + 5)
    label = ROI_LABELS[roi]

    # HC mean ± SEM
    hc_profiles = np.array([subject_data[s][roi].mean(axis=(0, 2)) for s in HC_SUBS])  # (7, 8)
    hc_mean = hc_profiles.mean(axis=0) * 1000
    hc_sem = hc_profiles.std(axis=0, ddof=1) / np.sqrt(len(HC_SUBS)) * 1000

    x = np.arange(8)
    ax.fill_between(x, hc_mean - hc_sem, hc_mean + hc_sem, alpha=0.2, color="steelblue")
    ax.plot(x, hc_mean, "o-", color="steelblue", linewidth=2, markersize=5, label="HC mean")

    # Individual CVD
    cvd_colors = {"sub-08": "#E74C3C", "sub-09": "#E67E22", "sub-10": "#8B4513"}
    cvd_markers = {"sub-08": "D", "sub-09": "^", "sub-10": "s"}
    for s in CVD_SUBS:
        profile = subject_data[s][roi].mean(axis=(0, 2)) * 1000
        ax.plot(x, profile, f"{cvd_markers[s]}-", color=cvd_colors[s], linewidth=1.5,
                markersize=6, label=f"{s} ({CVD_TYPES[s]})", alpha=0.8)

    ax.axhline(0, color="gray", linestyle="--", linewidth=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels([c[:3] for c in COLORS_HUE], rotation=45, fontsize=8)
    ax.set_ylabel(r"Mean activation ($\times 10^3$)" if i == 0 else "")
    ax.set_title(f"{label}: Color Tuning", fontsize=11)
    if i == 3:
        ax.legend(fontsize=7, loc="upper right")

    # Color-code x-axis
    for j, c in enumerate(PLOT_COLORS):
        ax.get_xticklabels()[j].set_color(c)

# ── Row 3: |activation| vs SRM disparity ───────────────────────────────
for i, roi in enumerate(ROIS):
    ax = fig.add_subplot(3, 4, i + 9)
    label = ROI_LABELS[roi]

    # Get SRM disparities
    roi_res = srm_data[label]
    hc_disp = roi_res.get("hc_loo_disparities", {})
    cvd_disp = {s: roi_res["individual_cvd"][s]["cvd_score"] for s in CVD_SUBS}

    act_all, disp_all = [], []
    for s in HC_SUBS:
        if s in hc_disp:
            a = np.abs(subject_data[s][roi]).mean()
            act_all.append(a)
            disp_all.append(hc_disp[s])
            ax.scatter(a, hc_disp[s], c="steelblue", s=40, alpha=0.7, zorder=3)

    for s in CVD_SUBS:
        if s in cvd_disp:
            a = np.abs(subject_data[s][roi]).mean()
            act_all.append(a)
            disp_all.append(cvd_disp[s])
            ax.scatter(a, cvd_disp[s], c="tomato", s=60, marker="D", alpha=0.8, zorder=3)
            ax.annotate(s[-2:], (a, cvd_disp[s]), fontsize=7, ha="left",
                        xytext=(5, 0), textcoords="offset points")

    # Correlation line
    if len(act_all) >= 5:
        r, p = stats.pearsonr(act_all, disp_all)
        z = np.polyfit(act_all, disp_all, 1)
        xline = np.linspace(min(act_all), max(act_all), 50)
        ax.plot(xline, np.polyval(z, xline), "--", color="gray", linewidth=1, alpha=0.5)
        sig = "*" if p < 0.05 else ""
        ax.set_title(f"{label}: r={r:.2f}, p={p:.3f}{sig}", fontsize=11)
    else:
        ax.set_title(f"{label}", fontsize=11)

    ax.set_xlabel("Mean |activation|")
    ax.set_ylabel("SRM disparity" if i == 0 else "")

# Legend
hc_patch = mpatches.Patch(color="steelblue", label="HC (n=7)")
cvd_patch = mpatches.Patch(color="tomato", label="CVD (n=3)")
fig.legend(handles=[hc_patch, cvd_patch], loc="lower center", ncol=2, fontsize=10,
           bbox_to_anchor=(0.5, 0.01))

plt.tight_layout(rect=[0, 0.03, 1, 0.96])
fig.savefig(OUT_DIR / "activation_prior_figure.png", dpi=150, bbox_inches="tight")
print(f"Figure saved to: {OUT_DIR / 'activation_prior_figure.png'}")
plt.close()
