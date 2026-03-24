#!/usr/bin/env python3
"""
CI Distribution Plots for Forward Model Performance
====================================================
PPT/Notion용 시각화: 모델 성능을 CI 분포로 표현

Figure 1: LOCO Performance with Permutation Null (per ROI)
  - HC individual dots + group mean ± 95% bootstrap CI
  - Permutation null 95% CI as shaded band
  - CVD individual dots (different marker)

Figure 2: 3-Tier Comparison (LOCO vs LORO vs Zero-Shot)
  - Per ROI, HC/CVD group mean ± 95% bootstrap CI

Figure 3: Per-Color LOCO (hV4, FE-3) — HC vs CVD
  - Per color, individual dots + CI

Usage:
    conda activate srm
    python scripts/plot_ci_distributions.py
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path
from scipy import stats

# ─── Paths ─────────────────────────────────────────────
BASE = Path(__file__).resolve().parent.parent
RESULTS = BASE / "results"
OUT_DIR = BASE / "figures"
OUT_DIR.mkdir(exist_ok=True)

ROIS = ["V1", "V2", "V3", "V4"]
ROI_LABELS = ["V1", "V2", "V3", "hV4"]
HC_SUBS = [f"{i:02d}" for i in range(1, 8)]
CVD_SUBS = ["08", "09", "10"]
ALL_SUBS = HC_SUBS + CVD_SUBS
COLORS_8 = ["red", "orange", "yellow", "green", "cyan", "blue", "purple", "magenta"]
HUES_8 = [0, 45, 90, 135, 180, 225, 270, 315]

# sub-07 missing from validation/ but present in validation_extended/
VALIDATION_EXT_SUBS = {"07"}  # subjects only in extended dir

# Style
plt.rcParams.update({
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.labelsize": 12,
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "font.family": "sans-serif",
})


# ─── Data Loading ──────────────────────────────────────
def load_loco_per_subject(model="ridge_gcv"):
    """Load LOCO mean voxel_corr per subject per ROI."""
    data = {roi: {"HC": [], "CVD": []} for roi in ROIS}
    for sub in ALL_SUBS:
        # sub-07 only in validation_extended/
        if sub in VALIDATION_EXT_SUBS:
            fpath = RESULTS / "validation_extended" / f"sub-{sub}_loco.json"
        else:
            fpath = RESULTS / "validation" / f"sub-{sub}_loco.json"
        with open(fpath) as f:
            d = json.load(f)
        group = "HC" if sub in HC_SUBS else "CVD"
        for roi in ROIS:
            val = d[roi][model]["mean_voxel_corr"]
            data[roi][group].append(val)
    return data


def load_loro_per_subject(model="prior_finetune"):
    """Load LORO mean voxel_corr per subject per ROI.
    sub-07 has no LORO file → HC n=6 for LORO.
    """
    data = {roi: {"HC": [], "CVD": []} for roi in ROIS}
    for sub in ALL_SUBS:
        if sub in VALIDATION_EXT_SUBS:
            continue  # sub-07 has no LORO
        fpath = RESULTS / "validation" / f"sub-{sub}_loro.json"
        with open(fpath) as f:
            d = json.load(f)
        group = "HC" if sub in HC_SUBS else "CVD"
        for roi in ROIS:
            val = d[roi][model]["mean_voxel_corr"]
            data[roi][group].append(val)
    return data


def load_zeroshot():
    """Load LOSO zero-shot voxel_corr per subject per ROI.
    HC: results[roi].hc[sub].zero_shot.mean_voxel_corr
    CVD: results[roi].cvd[sub].voxel_corr_mean (different structure)
    """
    fpath = RESULTS / "loso_zero_shot" / "loso_zero_shot.json"
    with open(fpath) as f:
        d = json.load(f)
    # LOSO file uses "hV4" not "V4"
    roi_map = {"V1": "V1", "V2": "V2", "V3": "V3", "V4": "hV4"}
    data = {roi: {"HC": [], "CVD": []} for roi in ROIS}
    for roi in ROIS:
        roi_key = roi_map.get(roi, roi)
        roi_data = d["results"][roi_key]
        for sub in HC_SUBS:
            val = roi_data["hc"][sub]["zero_shot"]["mean_voxel_corr"]
            data[roi]["HC"].append(val)
        for sub in CVD_SUBS:
            sub_data = roi_data["cvd"][sub]
            if "zero_shot" in sub_data:
                val = sub_data["zero_shot"]["mean_voxel_corr"]
            else:
                val = sub_data["voxel_corr_mean"]
            data[roi]["CVD"].append(val)
    return data


def load_permutation_null():
    """Load permutation null distribution statistics per ROI (FE-6)."""
    fpath = RESULTS / "basis_comparison" / "basis_permutation_10K.json"
    with open(fpath) as f:
        d = json.load(f)
    null_stats = {}
    for roi in ROIS:
        fe6 = d[roi]["FE-6"]
        # Collect HC subjects null stats
        null_means = []
        null_sds = []
        observed = []
        p_perms = []
        for sub in HC_SUBS:
            null_means.append(fe6[sub]["null_mean"])
            null_sds.append(fe6[sub]["null_sd"])
            observed.append(fe6[sub]["observed"])
            p_perms.append(fe6[sub]["p_perm"])
        null_stats[roi] = {
            "null_mean": np.mean(null_means),
            "null_sd": np.mean(null_sds),
            "null_95ci_low": np.mean(null_means) - 1.96 * np.mean(null_sds),
            "null_95ci_high": np.mean(null_means) + 1.96 * np.mean(null_sds),
            "observed_per_sub": observed,
            "p_perms": p_perms,
        }
    return null_stats


def load_loco_per_color_hv4():
    """Load per-color LOCO voxel_corr for hV4 (FE-3 basis from subject_k)."""
    data = {"HC": [], "CVD": []}
    for sub in ALL_SUBS:
        fpath = RESULTS / "subject_k" / f"sub-{sub}_V4_subject_k.json"
        with open(fpath) as f:
            d = json.load(f)
        group = "HC" if sub in HC_SUBS else "CVD"
        per_color = d["per_k"]["3"]["loco_per_color"]
        data[group].append(per_color)
    return data


def bootstrap_ci(values, n_boot=10000, ci=0.95):
    """Compute bootstrap confidence interval for the mean."""
    values = np.array(values)
    n = len(values)
    boot_means = np.array([
        np.mean(np.random.choice(values, size=n, replace=True))
        for _ in range(n_boot)
    ])
    alpha = (1 - ci) / 2
    lo = np.percentile(boot_means, alpha * 100)
    hi = np.percentile(boot_means, (1 - alpha) * 100)
    return np.mean(values), lo, hi


# ─── Figure 1: LOCO with Permutation Null ──────────────
def plot_loco_with_null(save=True):
    """
    Per-ROI LOCO performance:
    - Permutation null 95% CI as shaded band
    - HC individual dots + group mean ± bootstrap 95% CI
    - CVD individual dots + group mean
    """
    loco = load_loco_per_subject("ridge_gcv")
    null = load_permutation_null()

    fig, axes = plt.subplots(1, 4, figsize=(14, 4.5), sharey=True)

    for i, (roi, label) in enumerate(zip(ROIS, ROI_LABELS)):
        ax = axes[i]

        # Permutation null band
        nl = null[roi]
        ax.axhspan(nl["null_95ci_low"], nl["null_95ci_high"],
                    color="#E0E0E0", alpha=0.7, zorder=0)
        ax.axhline(nl["null_mean"], color="gray", ls="--", lw=1,
                    alpha=0.7, zorder=1, label="Null mean")

        # Zero line
        ax.axhline(0, color="black", ls="-", lw=0.5, alpha=0.3)

        # HC data
        hc_vals = np.array(loco[roi]["HC"])
        hc_mean, hc_lo, hc_hi = bootstrap_ci(hc_vals)

        # Jittered individual points
        np.random.seed(42)
        jitter_hc = np.random.uniform(-0.12, 0.12, len(hc_vals))
        ax.scatter(0.0 + jitter_hc, hc_vals, c="#2196F3", s=45,
                   alpha=0.7, zorder=4, edgecolors="white", linewidths=0.5)
        # Mean + CI
        ax.errorbar(0.0, hc_mean, yerr=[[hc_mean - hc_lo], [hc_hi - hc_mean]],
                     fmt="D", color="#1565C0", markersize=8, capsize=5,
                     capthick=1.5, elinewidth=1.5, zorder=5)

        # CVD data
        cvd_vals = np.array(loco[roi]["CVD"])
        cvd_mean, cvd_lo, cvd_hi = bootstrap_ci(cvd_vals)

        jitter_cvd = np.random.uniform(-0.08, 0.08, len(cvd_vals))
        ax.scatter(0.6 + jitter_cvd, cvd_vals, c="#F44336", s=55,
                   marker="^", alpha=0.8, zorder=4, edgecolors="white",
                   linewidths=0.5)
        ax.errorbar(0.6, cvd_mean,
                     yerr=[[cvd_mean - cvd_lo], [cvd_hi - cvd_mean]],
                     fmt="^", color="#C62828", markersize=9, capsize=5,
                     capthick=1.5, elinewidth=1.5, zorder=5)

        # Annotations
        ax.set_title(label, fontweight="bold")
        ax.set_xticks([0.0, 0.6])
        ax.set_xticklabels(["HC", "CVD"], fontsize=10)
        ax.set_xlim(-0.4, 1.0)

        # p-value annotation
        # Get Stouffer combined p for this ROI (from memory)
        perm_p = {"V1": 0.274, "V2": 0.311, "V3": 0.880, "V4": 0.044}
        pp = perm_p[roi]
        star = "*" if pp < 0.05 else ""
        ax.text(0.95, 0.95, f"p={pp:.3f}{star}",
                transform=ax.transAxes, ha="right", va="top",
                fontsize=9, style="italic",
                color="#C62828" if pp < 0.05 else "gray")

    axes[0].set_ylabel("LOCO voxel_corr (Spearman)")

    # Legend
    legend_elements = [
        mpatches.Patch(facecolor="#E0E0E0", alpha=0.7,
                       label="Permutation null 95% CI"),
        plt.Line2D([0], [0], color="gray", ls="--", lw=1,
                    label="Null mean"),
        plt.Line2D([0], [0], marker="D", color="#1565C0", ls="",
                    markersize=7, label="HC mean ± 95% CI"),
        plt.Line2D([0], [0], marker="o", color="#2196F3", ls="",
                    markersize=6, alpha=0.7, label="HC individual"),
        plt.Line2D([0], [0], marker="^", color="#C62828", ls="",
                    markersize=7, label="CVD mean ± 95% CI"),
        plt.Line2D([0], [0], marker="^", color="#F44336", ls="",
                    markersize=6, alpha=0.8, label="CVD individual"),
    ]
    fig.legend(handles=legend_elements, loc="lower center",
               ncol=3, fontsize=9, frameon=True,
               bbox_to_anchor=(0.5, -0.08))

    fig.suptitle("LOCO Color Interpolation: Observed vs Permutation Null\n"
                 "(ridge_gcv, FE-6, 10K permutations)",
                 fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()

    if save:
        fig.savefig(OUT_DIR / "fig1_loco_permutation_ci.png",
                    bbox_inches="tight", pad_inches=0.3)
        fig.savefig(OUT_DIR / "fig1_loco_permutation_ci.pdf",
                    bbox_inches="tight", pad_inches=0.3)
        print(f"  Saved: {OUT_DIR / 'fig1_loco_permutation_ci.png'}")
    plt.close(fig)


# ─── Figure 2: 3-Tier Comparison ──────────────────────
def plot_three_tier(save=True):
    """
    LOCO vs LORO vs Zero-Shot comparison per ROI.
    HC and CVD side by side with bootstrap 95% CI.
    """
    loco = load_loco_per_subject("ridge_gcv")
    loro = load_loro_per_subject("prior_finetune")
    zs = load_zeroshot()

    fig, axes = plt.subplots(1, 4, figsize=(16, 5), sharey=True)

    tier_colors = {
        "LOCO": {"HC": "#E53935", "CVD": "#FFCDD2"},
        "LORO": {"HC": "#1E88E5", "CVD": "#BBDEFB"},
        "ZS":   {"HC": "#43A047", "CVD": "#C8E6C9"},
    }
    tier_labels = ["LOCO", "LORO", "ZS"]
    tier_data = [loco, loro, zs]

    x_base = np.array([0, 1.2, 2.4])

    for i, (roi, label) in enumerate(zip(ROIS, ROI_LABELS)):
        ax = axes[i]
        ax.axhline(0, color="black", ls="-", lw=0.5, alpha=0.3)

        for j, (tier_name, data_dict) in enumerate(zip(tier_labels, tier_data)):
            for k, group in enumerate(["HC", "CVD"]):
                vals = np.array(data_dict[roi][group])
                mean, lo, hi = bootstrap_ci(vals)
                x_pos = x_base[j] + k * 0.4

                color = tier_colors[tier_name][group]
                marker = "o" if group == "HC" else "^"

                # Individual points
                np.random.seed(42 + j + k)
                jit = np.random.uniform(-0.08, 0.08, len(vals))
                ax.scatter(x_pos + jit, vals, c=color, s=30,
                           marker=marker, alpha=0.5, zorder=3,
                           edgecolors="white", linewidths=0.3)

                # Mean + CI
                edge_color = "#B71C1C" if group == "CVD" else "black"
                ax.errorbar(x_pos, mean,
                            yerr=[[mean - lo], [hi - mean]],
                            fmt=marker, color=color, markersize=9,
                            markeredgecolor=edge_color,
                            markeredgewidth=1.0,
                            capsize=4, capthick=1.5, elinewidth=2,
                            zorder=5)

        ax.set_title(label, fontweight="bold")
        ax.set_xticks(x_base + 0.2)
        ax.set_xticklabels(tier_labels, fontsize=10)
        ax.set_xlim(-0.4, 3.2)

        # hV4 ZS≈LORO annotation
        if roi == "V4":
            ax.annotate("p=0.913", xy=(1.8, 0.42), fontsize=8,
                        style="italic", color="#666666", ha="center")

    axes[0].set_ylabel("voxel_corr (Spearman)")

    # Legend
    legend_elements = [
        plt.Line2D([0], [0], marker="o", color="black", ls="",
                    markersize=7, label="HC"),
        plt.Line2D([0], [0], marker="^", color="#B71C1C", ls="",
                    markersize=7, label="CVD"),
        mpatches.Patch(facecolor="#E53935", label="LOCO (ridge_gcv)"),
        mpatches.Patch(facecolor="#1E88E5", label="LORO (prior_ft)"),
        mpatches.Patch(facecolor="#43A047", label="Zero-Shot (W₀)"),
    ]
    fig.legend(handles=legend_elements, loc="lower center",
               ncol=5, fontsize=9, frameon=True,
               bbox_to_anchor=(0.5, -0.06))

    fig.suptitle("3-Tier Validation: LOCO vs LORO vs Zero-Shot\n"
                 "Individual subjects with bootstrap 95% CI",
                 fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()

    if save:
        fig.savefig(OUT_DIR / "fig2_three_tier_ci.png",
                    bbox_inches="tight", pad_inches=0.3)
        fig.savefig(OUT_DIR / "fig2_three_tier_ci.pdf",
                    bbox_inches="tight", pad_inches=0.3)
        print(f"  Saved: {OUT_DIR / 'fig2_three_tier_ci.png'}")
    plt.close(fig)


# ─── Figure 3: Per-Color LOCO hV4 ─────────────────────
def plot_per_color_hv4(save=True):
    """
    Per-color LOCO voxel_corr in hV4 (FE-3 basis).
    HC vs CVD with individual dots and bootstrap CI.
    """
    data = load_loco_per_color_hv4()
    hc = np.array(data["HC"])   # (7, 8)
    cvd = np.array(data["CVD"])  # (3, 8)

    fig, ax = plt.subplots(figsize=(12, 5))

    x = np.arange(8)
    width = 0.35

    # Color-code the hue bars
    hue_colors = [
        "#E53935",  # red
        "#FF9800",  # orange
        "#FDD835",  # yellow
        "#43A047",  # green
        "#00BCD4",  # cyan
        "#1E88E5",  # blue
        "#7B1FA2",  # purple
        "#E91E63",  # magenta
    ]

    for ci_idx, color_name in enumerate(COLORS_8):
        hc_vals = hc[:, ci_idx]
        cvd_vals = cvd[:, ci_idx]

        hc_mean, hc_lo, hc_hi = bootstrap_ci(hc_vals)
        cvd_mean, cvd_lo, cvd_hi = bootstrap_ci(cvd_vals)

        # HC bar
        ax.bar(x[ci_idx] - width/2, hc_mean, width,
               color=hue_colors[ci_idx], alpha=0.6, edgecolor="black",
               linewidth=0.5)
        ax.errorbar(x[ci_idx] - width/2, hc_mean,
                     yerr=[[hc_mean - hc_lo], [hc_hi - hc_mean]],
                     fmt="none", color="black", capsize=4,
                     capthick=1.2, elinewidth=1.2, zorder=5)

        # CVD bar
        ax.bar(x[ci_idx] + width/2, cvd_mean, width,
               color=hue_colors[ci_idx], alpha=0.25, edgecolor="#B71C1C",
               linewidth=1.0, hatch="//")
        ax.errorbar(x[ci_idx] + width/2, cvd_mean,
                     yerr=[[cvd_mean - cvd_lo], [cvd_hi - cvd_mean]],
                     fmt="none", color="#B71C1C", capsize=4,
                     capthick=1.2, elinewidth=1.2, zorder=5)

        # Individual dots
        np.random.seed(42 + ci_idx)
        jit_hc = np.random.uniform(-0.06, 0.06, len(hc_vals))
        jit_cvd = np.random.uniform(-0.06, 0.06, len(cvd_vals))
        ax.scatter(x[ci_idx] - width/2 + jit_hc, hc_vals,
                   c="black", s=18, alpha=0.5, zorder=6)

        # CVD dots with subject labels
        for cvd_idx, (y_val, jit) in enumerate(zip(cvd_vals, jit_cvd)):
            ax.scatter(x[ci_idx] + width/2 + jit, y_val,
                       c="#B71C1C", s=25, marker="^", alpha=0.7, zorder=6)
            # Add subject label for CVD only
            subj_id = CVD_SUBS[cvd_idx]
            ax.annotate(f'sub-{subj_id}',
                        xy=(x[ci_idx] + width/2 + jit, y_val),
                        xytext=(3, 3), textcoords='offset points',
                        fontsize=7, color='#B71C1C', alpha=0.8)

    ax.axhline(0, color="black", ls="-", lw=0.5, alpha=0.3)
    ax.set_xticks(x)
    ax.set_xticklabels(COLORS_8, fontsize=10)
    ax.set_ylabel("LOCO voxel_corr (Spearman)")
    ax.set_title("hV4 Per-Color LOCO: HC vs CVD (FE-3 basis)\n"
                 "bootstrap 95% CI", fontweight="bold")

    # Significance annotations
    # blue p=0.046*, purple p=0.060†
    sig_info = {5: ("*", 0.046), 6: ("†", 0.060)}
    for idx, (sym, pval) in sig_info.items():
        y_max = max(hc[:, idx].max(), cvd[:, idx].max()) + 0.08
        ax.annotate(f"p={pval:.3f}{sym}", xy=(x[idx], y_max),
                    ha="center", fontsize=9, style="italic",
                    color="#C62828")

    # Cool/Warm region shading
    ax.axvspan(3.5, 7.5, color="#E3F2FD", alpha=0.3, zorder=0)
    ax.text(5.5, ax.get_ylim()[1] * 0.92, "Cool axis",
            ha="center", fontsize=9, color="#1565C0", alpha=0.7)

    legend_elements = [
        mpatches.Patch(facecolor="gray", alpha=0.6, edgecolor="black",
                       label="HC (n=7)"),
        mpatches.Patch(facecolor="gray", alpha=0.25, edgecolor="#B71C1C",
                       hatch="//", label="CVD (n=3)"),
    ]
    ax.legend(handles=legend_elements, loc="upper left", fontsize=10)

    plt.tight_layout()
    if save:
        fig.savefig(OUT_DIR / "fig3_per_color_hv4_ci.png",
                    bbox_inches="tight", pad_inches=0.2)
        fig.savefig(OUT_DIR / "fig3_per_color_hv4_ci.pdf",
                    bbox_inches="tight", pad_inches=0.2)
        print(f"  Saved: {OUT_DIR / 'fig3_per_color_hv4_ci.png'}")
    plt.close(fig)


# ─── Figure 4: GO/NO-GO Gate Summary ──────────────────
def plot_gate_summary(save=True):
    """
    Forest plot style: per-ROI observed LOCO with CI vs permutation null.
    Clear GO/NO-GO visualization.
    """
    loco = load_loco_per_subject("ridge_gcv")
    null = load_permutation_null()

    gate_results = {
        "V1": {"basis": "FE-6", "perm_p": 0.274, "gate": "CONDITIONAL"},
        "V2": {"basis": "FE-6", "perm_p": 0.311, "gate": "CONDITIONAL"},
        "V3": {"basis": "FE-8", "perm_p": 0.045, "gate": "CONDITIONAL"},
        "V4": {"basis": "FE-3", "perm_p": 0.026, "gate": "PRIMARY GO"},
    }

    fig, ax = plt.subplots(figsize=(8, 5))

    y_pos = np.arange(len(ROIS))[::-1]

    for i, (roi, label) in enumerate(zip(ROIS, ROI_LABELS)):
        y = y_pos[i]
        hc_vals = np.array(loco[roi]["HC"])
        mean, lo, hi = bootstrap_ci(hc_vals)
        nl = null[roi]

        gate = gate_results[roi]
        is_go = gate["perm_p"] < 0.05

        # Null CI band (horizontal)
        ax.barh(y, nl["null_95ci_high"] - nl["null_95ci_low"],
                left=nl["null_95ci_low"], height=0.4,
                color="#FFCDD2" if not is_go else "#C8E6C9",
                alpha=0.5, zorder=1)
        ax.plot(nl["null_mean"], y, "|", color="gray",
                markersize=15, zorder=2)

        # Observed mean + CI
        color = "#2E7D32" if is_go else "#C62828"
        ax.errorbarx = ax.errorbar(
            mean, y, xerr=[[mean - lo], [hi - mean]],
            fmt="D", color=color, markersize=10,
            capsize=5, capthick=2, elinewidth=2, zorder=5
        )

        # Individual HC dots
        np.random.seed(42 + i)
        jit = np.random.uniform(-0.08, 0.08, len(hc_vals))
        ax.scatter(hc_vals, y + jit, c=color, s=25,
                   alpha=0.4, zorder=3)

        # Gate label
        gate_text = gate["gate"]
        ax.text(0.62, y, f'{gate_text}\np={gate["perm_p"]:.3f}',
                fontsize=8, va="center",
                fontweight="bold" if is_go else "normal",
                color=color)

    ax.axvline(0, color="black", ls="-", lw=0.5, alpha=0.3)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(ROI_LABELS, fontsize=12, fontweight="bold")
    ax.set_xlabel("LOCO voxel_corr (Spearman)")
    ax.set_title("GO/NO-GO Gate: HC LOCO vs Permutation Null\n"
                 "Forest plot with bootstrap 95% CI",
                 fontweight="bold")
    ax.set_xlim(-0.15, 0.75)

    legend_elements = [
        mpatches.Patch(facecolor="#C8E6C9", alpha=0.5,
                       label="Null 95% CI (PASS)"),
        mpatches.Patch(facecolor="#FFCDD2", alpha=0.5,
                       label="Null 95% CI (FAIL)"),
        plt.Line2D([0], [0], marker="D", color="#2E7D32", ls="",
                    markersize=8, label="Observed (PASS)"),
        plt.Line2D([0], [0], marker="D", color="#C62828", ls="",
                    markersize=8, label="Observed (FAIL)"),
    ]
    ax.legend(handles=legend_elements, loc="lower right",
              fontsize=9, frameon=True)

    plt.tight_layout()
    if save:
        fig.savefig(OUT_DIR / "fig4_gate_forest_ci.png",
                    bbox_inches="tight", pad_inches=0.2)
        fig.savefig(OUT_DIR / "fig4_gate_forest_ci.pdf",
                    bbox_inches="tight", pad_inches=0.2)
        print(f"  Saved: {OUT_DIR / 'fig4_gate_forest_ci.png'}")
    plt.close(fig)


# ─── Main ──────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("Forward Model CI Distribution Plots")
    print("=" * 60)

    print("\n[1/4] LOCO with Permutation Null...")
    plot_loco_with_null()

    print("[2/4] 3-Tier Comparison (LOCO/LORO/ZS)...")
    plot_three_tier()

    print("[3/4] Per-Color hV4 LOCO...")
    plot_per_color_hv4()

    print("[4/4] GO/NO-GO Gate Forest Plot...")
    plot_gate_summary()

    print("\n" + "=" * 60)
    print(f"All figures saved to: {OUT_DIR}")
    print("=" * 60)
