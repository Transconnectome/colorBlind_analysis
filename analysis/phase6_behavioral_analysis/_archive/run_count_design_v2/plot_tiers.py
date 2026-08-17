#!/usr/bin/env python
"""
plot_tiers.py — Generate the tier-organized figures for run-count validation.

Inputs (all in run_count_validation/):
  - v1_saturation_loco.json
  - v1_saturation_crossnobis.json
  - tier1_signal_quality.json
  - tier2_geometric_stability.json
  - tier3_outcome_detection.json
  - profile_stability.json

Outputs (run_count_validation/figs/):
  - tier1_signal.png            β-split-half + LORO acc + GCV α median
  - tier2_geometric.png         noise ceiling + procrustes + circular RSA
  - tier3_outcome.png           LOCO ρ + Cohen's d + permutation p
  - per_color_profile.png       8×n heatmap per CVD subject per ROI
  - consensus_decision.png      consensus n* table figure
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[3]
VALID_DIR = PROJECT_ROOT / "analysis" / "future_phase3_behavioral_analysis" / \
    "run_count_validation"
FIG_DIR = VALID_DIR / "figs"
FIG_DIR.mkdir(parents=True, exist_ok=True)

ROIS = ["V1", "V2", "V3", "V4"]
HC = [f"{i:02d}" for i in range(1, 8)]
CVD = ["08", "09", "10"]
N_VALUES = [2, 3, 4, 5, 6]
COLOR_NAMES = ["red", "orange", "yellow", "green", "cyan", "blue", "purple", "magenta"]

PALETTE = {
    "08": "#d62728",  # CVD deutan
    "09": "#1f77b4",  # CVD protan
    "10": "#7f7f7f",  # null control
    "HC": "#2ca02c",
}


def load(name: str) -> dict:
    with open(VALID_DIR / name) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------
def aggregate_metric(data: dict, key_path: list, agg: str = "mean") -> dict:
    """Pull out (roi, n, subject) -> (mean, sd) across subsets.

    key_path: nested keys to scalar metric, e.g. ['beta_split_half', 'mean_r'].
    """
    out = {}
    for roi in ROIS:
        out[roi] = {n: {} for n in N_VALUES}
        for n in N_VALUES:
            cells_n = data["per_roi"][roi][str(n)]
            for subj, subset_cells in cells_n.items():
                vals = []
                for c in subset_cells.values():
                    v = c
                    for k in key_path:
                        v = v[k]
                    if v is None or (isinstance(v, float) and not np.isfinite(v)):
                        continue
                    vals.append(v)
                if vals:
                    out[roi][n][subj] = (float(np.mean(vals)), float(np.std(vals)))
                else:
                    out[roi][n][subj] = (float("nan"), float("nan"))
    return out


def hc_mean_sd(agg: dict, roi: str, n: int) -> tuple[float, float]:
    vals = [agg[roi][n][s][0] for s in HC if not np.isnan(agg[roi][n][s][0])]
    return (float(np.mean(vals)), float(np.std(vals))) if vals else (float("nan"), float("nan"))


# ---------------------------------------------------------------------------
# Figure 1: Tier 1 — signal quality
# ---------------------------------------------------------------------------
def fig_tier1():
    t1 = load("tier1_signal_quality.json")
    sat = load("v1_saturation_loco.json")

    beta = aggregate_metric(t1, ["beta_split_half", "mean_r"])
    loro = aggregate_metric(t1, ["loro_acc8", "mean_acc"])

    # GCV α median per (roi, n, subj) from saturation file
    alpha = {}
    for roi in ROIS:
        alpha[roi] = {n: {} for n in N_VALUES}
        for n in N_VALUES:
            for subj, subset_cells in sat["per_roi"][roi][str(n)].items():
                all_alphas = []
                for c in subset_cells.values():
                    all_alphas.extend(c["alpha_per_fold"])
                alpha[roi][n][subj] = (float(np.median(all_alphas)),
                                        float(np.percentile(all_alphas, 75) -
                                              np.percentile(all_alphas, 25)))

    fig, axes = plt.subplots(3, 4, figsize=(16, 11), sharex=True)
    metrics = [("β split-half voxel r", beta, "mean Pearson r", 0.0, 0.7, "lin"),
               ("LORO 8-way decoding accuracy", loro, "accuracy", 0.0, 0.7, "lin"),
               ("GCV α (median)", alpha, "α (log scale)", 1e-4, 1e4, "log")]
    for row, (title, agg, ylab, ymin, ymax, scale) in enumerate(metrics):
        for col, roi in enumerate(ROIS):
            ax = axes[row, col]
            # HC band
            hc_means = []
            hc_sds = []
            for n in N_VALUES:
                m, s = hc_mean_sd(agg, roi, n)
                hc_means.append(m); hc_sds.append(s)
            hc_means = np.array(hc_means); hc_sds = np.array(hc_sds)
            ax.fill_between(N_VALUES, hc_means - hc_sds, hc_means + hc_sds,
                            color=PALETTE["HC"], alpha=0.18, label="HC ±SD")
            ax.plot(N_VALUES, hc_means, color=PALETTE["HC"], lw=2, label="HC mean")

            # CVD subjects + null
            for subj in CVD:
                vals = [agg[roi][n][subj][0] for n in N_VALUES]
                sds  = [agg[roi][n][subj][1] for n in N_VALUES]
                ax.errorbar(N_VALUES, vals, yerr=sds, label=f"sub-{subj}",
                            color=PALETTE[subj], marker="o", capsize=2, lw=1.5)

            if row == 2:
                ax.set_yscale("log")
            ax.set_xticks(N_VALUES)
            ax.set_title(f"{roi}", fontsize=11)
            if col == 0:
                ax.set_ylabel(f"{title}\n{ylab}", fontsize=10)
            if row == 2:
                ax.set_xlabel("number of runs (n)")
            ax.grid(alpha=0.3)
            if row == 0 and col == 3:
                ax.legend(fontsize=8, loc="lower right")

    fig.suptitle("Tier 1 — Signal-quality metrics under run reduction",
                 fontsize=13, y=0.995)
    fig.tight_layout()
    out = FIG_DIR / "tier1_signal.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")


# ---------------------------------------------------------------------------
# Figure 2: Tier 2 — geometric stability
# ---------------------------------------------------------------------------
def fig_tier2():
    t2 = load("tier2_geometric_stability.json")
    nc_lower = aggregate_metric(t2, ["noise_ceiling", "lower"])
    nc_upper = aggregate_metric(t2, ["noise_ceiling", "upper"])
    proc = aggregate_metric(t2, ["procrustes", "mean_disparity"])
    rsa = aggregate_metric(t2, ["circular_rsa", "rho"])

    fig, axes = plt.subplots(3, 4, figsize=(16, 11), sharex=True)

    def plot_panel(ax, agg, roi, ylab, ylim=None, log=False):
        hc_m = []; hc_s = []
        for n in N_VALUES:
            m, s = hc_mean_sd(agg, roi, n); hc_m.append(m); hc_s.append(s)
        hc_m = np.array(hc_m); hc_s = np.array(hc_s)
        ax.fill_between(N_VALUES, hc_m - hc_s, hc_m + hc_s,
                        color=PALETTE["HC"], alpha=0.18)
        ax.plot(N_VALUES, hc_m, color=PALETTE["HC"], lw=2, label="HC mean")
        for subj in CVD:
            vals = [agg[roi][n][subj][0] for n in N_VALUES]
            sds  = [agg[roi][n][subj][1] for n in N_VALUES]
            ax.errorbar(N_VALUES, vals, yerr=sds, label=f"sub-{subj}",
                        color=PALETTE[subj], marker="o", capsize=2, lw=1.5)
        if log:
            ax.set_yscale("log")
        if ylim is not None:
            ax.set_ylim(ylim)
        ax.set_xticks(N_VALUES)
        ax.grid(alpha=0.3)
        ax.set_ylabel(ylab, fontsize=10)

    titles = [("Crossnobis RDM noise ceiling\n(lower = split-half, upper = SB)",
               (nc_lower, nc_upper), "Spearman ρ", (-0.5, 1.0)),
              ("Procrustes split-half disparity\n(↓ better)",
               (proc, None), "disparity", (0, 1.05)),
              ("Circular-template RSA\n(observed vs ideal chord-RDM)",
               (rsa, None), "Spearman ρ", (-0.5, 1.0))]

    for row, (title, (agg_main, agg_alt), ylab, ylim) in enumerate(titles):
        for col, roi in enumerate(ROIS):
            ax = axes[row, col]
            if row == 0 and agg_alt is not None:
                # plot both lower and upper bounds
                # lower
                hc_m_l = [hc_mean_sd(agg_main, roi, n)[0] for n in N_VALUES]
                hc_m_u = [hc_mean_sd(agg_alt, roi, n)[0] for n in N_VALUES]
                ax.fill_between(N_VALUES, hc_m_l, hc_m_u,
                                color=PALETTE["HC"], alpha=0.15, label="HC band")
                ax.plot(N_VALUES, hc_m_l, color=PALETTE["HC"], lw=1, ls="--",
                        label="HC lower")
                ax.plot(N_VALUES, hc_m_u, color=PALETTE["HC"], lw=1, label="HC upper")
                for subj in CVD:
                    vals_l = [agg_main[roi][n][subj][0] for n in N_VALUES]
                    vals_u = [agg_alt[roi][n][subj][0] for n in N_VALUES]
                    ax.plot(N_VALUES, vals_l, color=PALETTE[subj], lw=1, ls="--",
                            marker="o", ms=3)
                    ax.plot(N_VALUES, vals_u, color=PALETTE[subj], lw=1.5,
                            marker="o", ms=5, label=f"sub-{subj}")
                ax.set_ylim(ylim)
                ax.set_xticks(N_VALUES)
                ax.grid(alpha=0.3)
                ax.set_ylabel(ylab, fontsize=10)
            else:
                plot_panel(ax, agg_main, roi, ylab, ylim=ylim)
            ax.set_title(roi if row == 0 else "", fontsize=11)
            if col == 0 and row == 0:
                ax.legend(fontsize=7, loc="lower right")
            if row == 0 and col == 0:
                # title to left of leftmost panel
                pass
            if col == 0:
                ax.set_ylabel(f"{title}\n{ylab}", fontsize=9)
            if row == 2:
                ax.set_xlabel("number of runs (n)")

    fig.suptitle("Tier 2 — Geometric stability metrics", fontsize=13, y=0.995)
    fig.tight_layout()
    out = FIG_DIR / "tier2_geometric.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")


# ---------------------------------------------------------------------------
# Figure 3: Tier 3 — outcome detection
# ---------------------------------------------------------------------------
def fig_tier3():
    t3 = load("tier3_outcome_detection.json")
    sat = load("v1_saturation_loco.json")

    # Aggregate per (roi, n, subj) mean ρ from saturation
    sat_agg = {}
    for roi in ROIS:
        sat_agg[roi] = {n: {} for n in N_VALUES}
        for n in N_VALUES:
            for subj, cells in sat["per_roi"][roi][str(n)].items():
                rhos = [c["rho"] for c in cells.values()]
                sat_agg[roi][n][subj] = (float(np.mean(rhos)), float(np.std(rhos)))

    fig, axes = plt.subplots(2, 4, figsize=(16, 8), sharex=True)

    for col, roi in enumerate(ROIS):
        # Row 0: mean LOCO ρ with HC band
        ax = axes[0, col]
        hc_m = []; hc_s = []
        for n in N_VALUES:
            m, s = hc_mean_sd(sat_agg, roi, n); hc_m.append(m); hc_s.append(s)
        hc_m = np.array(hc_m); hc_s = np.array(hc_s)
        ax.fill_between(N_VALUES, hc_m - hc_s, hc_m + hc_s,
                        color=PALETTE["HC"], alpha=0.18, label="HC ±SD")
        ax.plot(N_VALUES, hc_m, color=PALETTE["HC"], lw=2, label="HC mean")
        for subj in CVD:
            vals = [sat_agg[roi][n][subj][0] for n in N_VALUES]
            sds  = [sat_agg[roi][n][subj][1] for n in N_VALUES]
            ax.errorbar(N_VALUES, vals, yerr=sds, label=f"sub-{subj}",
                        color=PALETTE[subj], marker="o", capsize=2, lw=1.5)
        ax.axhline(0, ls=":", color="k", lw=0.7)
        ax.set_xticks(N_VALUES); ax.grid(alpha=0.3)
        ax.set_title(roi, fontsize=11)
        ax.set_ylim(-0.5, 0.6)
        if col == 0:
            ax.set_ylabel("LOCO ρ mean ± subset SD", fontsize=10)
        if col == 3:
            ax.legend(fontsize=8, loc="upper left")

        # Row 1: Cohen's d (CVD vs HC); horizontal band at d=0.8 marks pass
        ax = axes[1, col]
        for subj in CVD:
            ds = [t3["posthoc"]["per_roi"][roi][str(n)][subj]["cohens_d_vs_hc"]
                  for n in N_VALUES]
            ax.plot(N_VALUES, ds, color=PALETTE[subj], marker="o", lw=1.5,
                    label=f"sub-{subj}")
        ax.axhspan(0.8, 5.0, alpha=0.08, color="green", label="d≥0.8 pass")
        ax.axhline(0.8, ls=":", color="k", lw=0.7)
        ax.axhline(0, ls="--", color="gray", lw=0.5)
        ax.set_xticks(N_VALUES); ax.grid(alpha=0.3)
        if col == 0:
            ax.set_ylabel("Cohen's d\n(HC mean − CVD) / SD_HC", fontsize=10)
        ax.set_ylim(-1, 5)
        ax.set_xlabel("number of runs (n)")
        if col == 3:
            ax.legend(fontsize=8, loc="upper right")

    fig.suptitle("Tier 3 — Outcome detection power "
                 "(permutation deprecated — grand-mean bias; see REPORT §3.6)",
                 fontsize=12, y=0.995)
    fig.tight_layout()
    out = FIG_DIR / "tier3_outcome.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")


# ---------------------------------------------------------------------------
# Figure 4: Per-color profile heatmap
# ---------------------------------------------------------------------------
def fig_per_color_profile():
    prof = load("profile_stability.json")
    subjs = ["08", "09", "10"]

    fig, axes = plt.subplots(len(subjs), len(ROIS), figsize=(16, 9))

    for row, subj in enumerate(subjs):
        for col, roi in enumerate(ROIS):
            ax = axes[row, col]
            mat = np.array([prof["per_roi"][roi][str(n)][subj]["per_color_mean"]
                            for n in N_VALUES])
            vmax = max(abs(mat.min()), abs(mat.max()), 0.3)
            im = ax.imshow(mat, aspect="auto", cmap="RdBu_r",
                            vmin=-vmax, vmax=vmax)
            ax.set_xticks(range(8))
            ax.set_xticklabels([f"c{i+1}" for i in range(8)], fontsize=7)
            ax.set_yticks(range(len(N_VALUES)))
            ax.set_yticklabels([f"n={n}" for n in N_VALUES], fontsize=8)
            if row == 0:
                ax.set_title(roi, fontsize=11)
            if col == 0:
                ax.set_ylabel(f"sub-{subj}", fontsize=11, fontweight="bold")
            # mark anchor bottom-K
            anchor_bottom = prof["per_roi"][roi]["6"][subj]["op_b"]["anchor_bottom_k"]
            for c in anchor_bottom:
                ax.add_patch(plt.Rectangle((c - 0.5, len(N_VALUES) - 1.5),
                                            1, 1, fill=False,
                                            edgecolor="lime", lw=2))
            plt.colorbar(im, ax=ax, fraction=0.04, pad=0.02)

    fig.suptitle("Per-color LOCO ρ profile under run reduction\n"
                 "(green box = bottom-2 vulnerable color at n=6 anchor)",
                 fontsize=12, y=0.995)
    fig.tight_layout()
    out = FIG_DIR / "per_color_profile.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")


# ---------------------------------------------------------------------------
# Figure 5: Op-A + Op-B stability curves
# ---------------------------------------------------------------------------
def fig_profile_stability():
    prof = load("profile_stability.json")

    fig, axes = plt.subplots(2, 4, figsize=(16, 8), sharex=True)
    for col, roi in enumerate(ROIS):
        # Op-A
        ax = axes[0, col]
        for subj in CVD:
            vals = [prof["per_roi"][roi][str(n)][subj]["op_a"]["mean_spearman"]
                    for n in N_VALUES]
            ax.plot(N_VALUES, vals, color=PALETTE[subj], marker="o",
                    lw=1.5, label=f"sub-{subj}")
        # HC mean
        hc_curve = []
        for n in N_VALUES:
            vals = [prof["per_roi"][roi][str(n)][hc]["op_a"]["mean_spearman"]
                    for hc in HC]
            vals = [v for v in vals if np.isfinite(v)]
            hc_curve.append(float(np.mean(vals)) if vals else float("nan"))
        ax.plot(N_VALUES, hc_curve, color=PALETTE["HC"], lw=2, label="HC mean")
        ax.axhline(0.5, ls=":", color="k", lw=0.7)
        ax.set_xticks(N_VALUES); ax.grid(alpha=0.3)
        ax.set_title(roi, fontsize=11)
        ax.set_ylim(-0.5, 1.0)
        if col == 0:
            ax.set_ylabel("Op-A: rank Spearman\nacross subsets", fontsize=10)
        if col == 3:
            ax.legend(fontsize=8, loc="lower right")

        # Op-B
        ax = axes[1, col]
        for subj in CVD:
            vals = [prof["per_roi"][roi][str(n)][subj]["op_b"]["mean_retention"]
                    for n in N_VALUES]
            ax.plot(N_VALUES, vals, color=PALETTE[subj], marker="o",
                    lw=1.5, label=f"sub-{subj}")
        hc_curve = []
        for n in N_VALUES:
            vals = [prof["per_roi"][roi][str(n)][hc]["op_b"]["mean_retention"]
                    for hc in HC]
            hc_curve.append(float(np.mean(vals)))
        ax.plot(N_VALUES, hc_curve, color=PALETTE["HC"], lw=2, label="HC mean")
        ax.axhline(0.5, ls=":", color="k", lw=0.7, label="chance (k=2)")
        ax.set_xticks(N_VALUES); ax.grid(alpha=0.3)
        ax.set_ylim(0, 1.05)
        if col == 0:
            ax.set_ylabel("Op-B: vulnerable-set retention\n(bottom-2 vs n=6 anchor)",
                          fontsize=10)
        ax.set_xlabel("number of runs (n)")
        if col == 3:
            ax.legend(fontsize=8, loc="lower right")

    fig.suptitle("Per-color profile stability — Op-A (rank) + Op-B (retention)",
                 fontsize=12, y=0.995)
    fig.tight_layout()
    out = FIG_DIR / "profile_stability.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")


# ---------------------------------------------------------------------------
# Figure 6: Consensus n* decision
# ---------------------------------------------------------------------------
def fig_consensus():
    """Compute and visualize the consensus n* per ROI for hV4 and V1."""
    t1 = load("tier1_signal_quality.json")
    t2 = load("tier2_geometric_stability.json")
    t3 = load("tier3_outcome_detection.json")
    prof = load("profile_stability.json")

    # Consensus criteria. Evaluated for sub-08 + sub-09 (CVD test subjects);
    # sub-10 (null control) is reported separately and not used to gate.
    # T1: per-CVD β-split-half ≥ 0.20 AND LORO 8-way acc ≥ 0.25 (= 2× chance)
    # T2: per-CVD crossnobis split-half ρ (lower bound) ≥ 0.40
    # T3a: HC-vs-CVD Cohen's d ≥ 0.8 for BOTH sub-08 and sub-09
    # T3b: Op-B vulnerable-set retention ≥ 0.50 for BOTH sub-08 and sub-09
    CVD_TEST = ["08", "09"]  # gating subjects (sub-10 is null control)
    rows = []
    for roi in ROIS:
        roi_row = {"ROI": roi}
        for n in N_VALUES:
            t1_betas = []
            t1_loros = []
            for subj in CVD_TEST:
                cells = t1["per_roi"][roi][str(n)][subj]
                t1_betas.append(np.mean([c["beta_split_half"]["mean_r"]
                                          for c in cells.values()]))
                t1_loros.append(np.mean([c["loro_acc8"]["mean_acc"]
                                          for c in cells.values()]))
            t1_pass = (min(t1_betas) >= 0.20) and (min(t1_loros) >= 0.25)
            nc_l = []
            for subj in CVD_TEST:
                cells = t2["per_roi"][roi][str(n)][subj]
                ncs = [c["noise_ceiling"]["lower"] for c in cells.values()]
                ncs = [v for v in ncs if np.isfinite(v)]
                nc_l.append(np.mean(ncs) if ncs else 0)
            t2_pass = min(nc_l) >= 0.40
            ds = [t3["posthoc"]["per_roi"][roi][str(n)][subj]["cohens_d_vs_hc"]
                  for subj in CVD_TEST]
            t3a_pass = all(d >= 0.8 for d in ds if np.isfinite(d))
            rets = [prof["per_roi"][roi][str(n)][subj]["op_b"]["mean_retention"]
                    for subj in CVD_TEST]
            t3b_pass = min(rets) >= 0.50
            roi_row[f"n={n}"] = {
                "T1": bool(t1_pass), "T2": bool(t2_pass),
                "T3a": bool(t3a_pass), "T3b": bool(t3b_pass),
                "ALL": bool(t1_pass and t2_pass and t3a_pass and t3b_pass),
                "stats": {
                    "min_beta_r_cvd": float(min(t1_betas)),
                    "min_loro_cvd": float(min(t1_loros)),
                    "min_nc_lower_cvd": float(min(nc_l)),
                    "min_d_cvd2": float(min(ds)),
                    "min_retention_cvd2": float(min(rets)),
                },
            }
        rows.append(roi_row)

    # Make table figure
    fig, ax = plt.subplots(figsize=(14, 4 + 0.6 * len(ROIS)))
    ax.axis("off")
    cols = ["ROI"] + sum([[f"n={n}\nT1", f"T2", f"T3a", f"T3b", f"ALL"]
                           for n in N_VALUES], [])
    cell_text = []
    cell_colors = []
    for r in rows:
        line = [r["ROI"]]
        cline = ["white"]
        for n in N_VALUES:
            cell = r[f"n={n}"]
            for key in ["T1", "T2", "T3a", "T3b", "ALL"]:
                line.append("✓" if cell[key] else "·")
                cline.append("#c6e7c6" if cell[key] else "#f7d6d6")
        cell_text.append(line)
        cell_colors.append(cline)
    tbl = ax.table(cellText=cell_text, colLabels=cols, cellColours=cell_colors,
                    loc="center", cellLoc="center")
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(9)
    tbl.scale(1, 1.5)
    ax.set_title("Consensus decision table  (T1 signal | T2 geometric | T3a power | T3b profile | ALL)",
                 fontsize=12, pad=10)

    fig.tight_layout()
    out = FIG_DIR / "consensus_decision.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")

    # Also save the table data as JSON for REPORT use
    out_json = VALID_DIR / "consensus_table.json"
    with open(out_json, "w") as f:
        json.dump(rows, f, indent=2)
    print(f"Saved: {out_json}")


def main():
    fig_tier1()
    fig_tier2()
    fig_tier3()
    fig_per_color_profile()
    fig_profile_stability()
    fig_consensus()


if __name__ == "__main__":
    main()
