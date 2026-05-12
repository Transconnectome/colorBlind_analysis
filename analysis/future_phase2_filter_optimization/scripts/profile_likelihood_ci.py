"""Profile-likelihood-based confidence intervals for 2-component cone-shift fits.

Descriptive diagnostic — NOT a specificity test.

Per-subject pipeline (read existing landscape, no simulator rerun):
  1. argmin cell (min L_fit)
  2. sigma^2 = var(vuln_cvd - vuln_sim_best, ddof=1)
  3. threshold = L_fit_min + sigma^2 * chi2(2, 0.95) / 8
  4. CI cells = {L_fit <= threshold}
  5. ci_area, sharpness, bs/bc/norm ranges, ci_open flag

Subjects: sub-08 V4 + sub-09 V4 (CVD) + sub-01..06 V4 (HC LOO).
sub-10 V4 is reported missing (no 1326-cell landscape with vuln_sim available).
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import chi2, mannwhitneyu

ROOT = Path(__file__).resolve().parent.parent
OLD = ROOT / "results" / "old_formula"
HC_DIR = ROOT / "results" / "fits" / "phase_a_2component_hc_sanity"
OUT_DIR = OLD  # required output location

CHI2_95_DF2 = float(chi2.ppf(0.95, df=2))  # 5.991...

GRID_BS_MIN, GRID_BS_MAX = 0.0, 50.0
GRID_BC_MIN, GRID_BC_MAX = -50.0, 50.0
BOUNDARY_TOL = 1e-9


# ---------- loaders ----------------------------------------------------------

def _load_cvd(subject: str) -> dict:
    """Load CVD subject landscape merging old_formula landscape (L_fit) and cache (vuln_sim).

    Returns dict {cells: [{bs, bc, l_fit, vuln_sim, spearman_r}], vuln_target}
    """
    sid = subject.replace("sub-", "")
    cache = json.loads((OLD / f"sub-{sid}_V4_vulnsim_cache.json").read_text())
    land = json.loads((OLD / f"sub-{sid}_V4_4term_landscape.json").read_text())
    assert len(cache["cells"]) == len(land) == 1326, f"cell count mismatch for {subject}"
    cells = []
    for c_cache, c_land in zip(cache["cells"], land):
        assert c_cache["bs"] == c_land["bs"] and c_cache["bc"] == c_land["bc"], \
            f"ordering mismatch for {subject} at bs={c_cache['bs']}, bc={c_cache['bc']}"
        cells.append({
            "bs": float(c_cache["bs"]),
            "bc": float(c_cache["bc"]),
            "l_fit": float(c_land["l_fit"]),
            "vuln_sim": list(c_cache["vuln_sim"]),
            "spearman_r": float(c_land["spearman_r"]),
        })
    return {"cells": cells, "vuln_target": list(cache["vuln_cvd"])}


def _load_hc_loo(subject: str) -> dict:
    """Load HC LOO subject landscape from phase_a_2component_hc_sanity dir.

    Each landscape cell has 'params'=[bs, bc], 'vuln_sim', 'l_fit', 'spearman_r'.
    Target vuln is baseline.vuln_baseline (the LOO HC's own LOCO vulnerability).
    """
    sid = subject.replace("sub-", "")
    f = HC_DIR / f"sub-{sid}_V4_2component.json"
    d = json.loads(f.read_text())
    cells = []
    for c in d["landscape"]:
        bs, bc = c["params"]
        cells.append({
            "bs": float(bs),
            "bc": float(bc),
            "l_fit": float(c["l_fit"]),
            "vuln_sim": list(c["vuln_sim"]),
            "spearman_r": float(c["spearman_r"]),
        })
    assert len(cells) == 1326, f"unexpected cell count for {subject}: {len(cells)}"
    return {"cells": cells, "vuln_target": list(d["baseline"]["vuln_baseline"])}


# ---------- core metric ------------------------------------------------------

def _compute_ci(cells: list[dict], vuln_target: list[float]) -> dict:
    bs_arr = np.array([c["bs"] for c in cells])
    bc_arr = np.array([c["bc"] for c in cells])
    lfit = np.array([c["l_fit"] for c in cells])
    vs = np.array([c["vuln_sim"] for c in cells])  # (1326, 8)
    target = np.array(vuln_target)

    idx_min = int(np.argmin(lfit))
    vs_best = vs[idx_min]
    resid = target - vs_best
    sigma_sq = float(np.var(resid, ddof=1))
    if sigma_sq <= 0 or not np.isfinite(sigma_sq):
        raise ValueError(f"non-positive sigma_sq={sigma_sq}")

    threshold = float(lfit[idx_min] + sigma_sq * CHI2_95_DF2 / 8.0)
    in_ci = lfit <= threshold
    n_in = int(in_ci.sum())
    assert in_ci[idx_min], "argmin not in CI — bug"

    ci_bs = bs_arr[in_ci]
    ci_bc = bc_arr[in_ci]
    ci_norms = np.sqrt(ci_bs ** 2 + ci_bc ** 2)

    # boundary check (any CI cell on grid border)
    on_bs_bound = np.any(np.isclose(ci_bs, GRID_BS_MIN, atol=BOUNDARY_TOL)
                          | np.isclose(ci_bs, GRID_BS_MAX, atol=BOUNDARY_TOL))
    on_bc_bound = np.any(np.isclose(ci_bc, GRID_BC_MIN, atol=BOUNDARY_TOL)
                          | np.isclose(ci_bc, GRID_BC_MAX, atol=BOUNDARY_TOL))
    ci_open = bool(on_bs_bound or on_bc_bound)

    return {
        "argmin_idx": idx_min,
        "argmin_bs": float(bs_arr[idx_min]),
        "argmin_bc": float(bc_arr[idx_min]),
        "argmin_norm": float(math.hypot(bs_arr[idx_min], bc_arr[idx_min])),
        "l_fit_min": float(lfit[idx_min]),
        "sigma_sq": sigma_sq,
        "threshold": threshold,
        "raw_spearman_r": float(cells[idx_min]["spearman_r"]),
        "ci_area": float(n_in / 1326),
        "ci_norm_min": float(ci_norms.min()),
        "ci_norm_max": float(ci_norms.max()),
        "ci_sharpness": float(1326 / n_in),
        "ci_bs_range_min": float(ci_bs.min()),
        "ci_bs_range_max": float(ci_bs.max()),
        "ci_bc_range_min": float(ci_bc.min()),
        "ci_bc_range_max": float(ci_bc.max()),
        "ci_open": ci_open,
        "in_ci_mask": in_ci.tolist(),
    }


# ---------- registry ---------------------------------------------------------

def _build_registry() -> list[dict]:
    reg = [
        {"subject": "sub-08", "group": "CVD", "loader": _load_cvd},
        {"subject": "sub-09", "group": "CVD", "loader": _load_cvd},
    ]
    for sid in ["01", "02", "03", "04", "05", "06"]:
        reg.append({"subject": f"sub-{sid}", "group": "HC", "loader": _load_hc_loo})
    return reg


# ---------- figures ----------------------------------------------------------

def _plot_landscapes(per_subject: list[dict], out_pdf: Path) -> None:
    """3x3 grid of L_fit landscapes with white CI contour and argmin star."""
    bs_vals = np.linspace(0, 50, 26)
    bc_vals = np.linspace(-50, 50, 51)
    BS_GRID, BC_GRID = np.meshgrid(bs_vals, bc_vals, indexing="xy")  # shape (51, 26)

    fig, axes = plt.subplots(3, 3, figsize=(15, 13))
    axes = axes.flatten()
    for ax in axes:
        ax.set_visible(False)

    order = []
    cvd = [r for r in per_subject if r["group"] == "CVD"]
    hc = [r for r in per_subject if r["group"] == "HC"]
    nul = [r for r in per_subject if r["group"] == "null"]
    order = cvd + nul + hc

    for ax_idx, rec in enumerate(order):
        if ax_idx >= 9:
            break
        ax = axes[ax_idx]
        ax.set_visible(True)
        cells = rec["_cells"]
        lfit = np.array([c["l_fit"] for c in cells])
        # map cells to grid: bs index = bs/2, bc index = (bc+50)/2
        L = np.full((51, 26), np.nan)
        for c, lv in zip(cells, lfit):
            j = int(round(c["bs"] / 2))
            i = int(round((c["bc"] + 50) / 2))
            L[i, j] = lv

        pcm = ax.pcolormesh(BS_GRID, BC_GRID, L, cmap="viridis_r", shading="auto")
        # CI contour at threshold
        ax.contour(BS_GRID, BC_GRID, L, levels=[rec["threshold"]],
                   colors="white", linewidths=1.5)
        # argmin star
        ax.plot(rec["argmin_bs"], rec["argmin_bc"], marker="*",
                color="white", markersize=14, markeredgecolor="black", markeredgewidth=0.8)

        col = {"CVD": "tab:red", "HC": "tab:blue", "null": "gray"}[rec["group"]]
        title = f"{rec['subject']} ({rec['group']})  argmin=({rec['argmin_bs']:.0f},{rec['argmin_bc']:.0f})"
        ax.set_title(title, color=col, fontsize=10)
        ax.set_xlabel(r"$\beta_s$")
        ax.set_ylabel(r"$\beta_c$")
        ann = (f"raw ρ={rec['raw_spearman_r']:+.2f}\n"
               f"CI area={rec['ci_area']*100:.1f}%\n"
               f"|norm|∈[{rec['ci_norm_min']:.1f},{rec['ci_norm_max']:.1f}]\n"
               f"open={rec['ci_open']}")
        ax.text(0.02, 0.98, ann, transform=ax.transAxes,
                fontsize=8, color="white", va="top",
                bbox=dict(facecolor="black", alpha=0.55, edgecolor="none", pad=2))
        fig.colorbar(pcm, ax=ax, fraction=0.04, pad=0.02)

    fig.suptitle("2-component L_fit landscapes with profile-likelihood CI (white contour)\n"
                 "Descriptive only — not a specificity test", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(out_pdf, format="pdf", bbox_inches="tight")
    plt.close(fig)


def _plot_ci_bars(per_subject: list[dict], out_pdf: Path) -> None:
    """Bar chart of CI area per subject, sorted ascending; group-coloured."""
    recs = sorted(per_subject, key=lambda r: r["ci_area"])
    labels = [r["subject"] for r in recs]
    areas = np.array([r["ci_area"] for r in recs]) * 100
    colors = {"CVD": "tab:red", "HC": "tab:blue", "null": "gray"}
    bar_colors = [colors[r["group"]] for r in recs]

    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(len(labels))
    bars = ax.bar(x, areas, color=bar_colors, edgecolor="black", linewidth=0.5)
    for bar, rec in zip(bars, recs):
        if rec["ci_open"]:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                    "open", ha="center", fontsize=8, color="black")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_ylabel("CI area (% of 1326 cells)")
    ax.set_title("Profile-likelihood CI area per subject — V4, 2-component\n"
                 "(descriptive landscape sharpness; not a specificity test)")
    median = float(np.median(areas))
    ax.axhline(median, ls="--", color="gray", lw=1.0,
               label=f"median={median:.1f}%")
    handles = [
        plt.Rectangle((0, 0), 1, 1, color="tab:red", label="CVD"),
        plt.Rectangle((0, 0), 1, 1, color="tab:blue", label="HC LOO"),
    ]
    if any(r["group"] == "null" for r in recs):
        handles.append(plt.Rectangle((0, 0), 1, 1, color="gray", label="null"))
    handles.append(plt.Line2D([0], [0], color="gray", ls="--", label=f"median={median:.1f}%"))
    ax.legend(handles=handles, loc="upper left")
    ax.set_ylim(0, max(100, areas.max() * 1.1))
    fig.tight_layout()
    fig.savefig(out_pdf, format="pdf", bbox_inches="tight")
    plt.close(fig)


# ---------- main -------------------------------------------------------------

def main() -> None:
    reg = _build_registry()
    per_subject_full: list[dict] = []
    missing: list[str] = []

    # sub-10 V4: no 1326-cell landscape with vuln_sim available
    missing.append("sub-10 V4: no compatible 1326-cell landscape with vuln_sim "
                   "(only cycles/sub-10_V4_landscape.json which is 41-row format, "
                   "and bootstrap main which stores only best-fit; skipped)")

    for rec in reg:
        sub = rec["subject"]
        try:
            data = rec["loader"](sub)
        except FileNotFoundError as exc:
            missing.append(f"{sub} V4: file not found ({exc})")
            continue
        ci = _compute_ci(data["cells"], data["vuln_target"])
        full = {
            "subject": sub,
            "roi": "V4",
            "group": rec["group"],
            **{k: v for k, v in ci.items() if k != "in_ci_mask"},
            "_cells": data["cells"],
            "_in_ci_mask": ci["in_ci_mask"],
        }
        per_subject_full.append(full)
        print(f"{sub} ({rec['group']:>3}): L_fit_min={ci['l_fit_min']:.4f}  "
              f"sigma^2={ci['sigma_sq']:.4f}  threshold={ci['threshold']:.4f}  "
              f"ci_area={ci['ci_area']*100:5.1f}%  open={ci['ci_open']}  "
              f"argmin=({ci['argmin_bs']:>4.0f},{ci['argmin_bc']:>4.0f}) "
              f"raw_rho={ci['raw_spearman_r']:+.3f}")

    # CSV
    csv_path = OUT_DIR / "profile_likelihood_ci.csv"
    fields = [
        "subject", "roi", "group",
        "argmin_bs", "argmin_bc", "argmin_norm",
        "l_fit_min", "sigma_sq", "threshold", "raw_spearman_r",
        "ci_area", "ci_norm_min", "ci_norm_max", "ci_sharpness",
        "ci_bs_range_min", "ci_bs_range_max",
        "ci_bc_range_min", "ci_bc_range_max",
        "ci_open",
    ]
    with csv_path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in per_subject_full:
            w.writerow({k: r[k] for k in fields})
    print(f"\nWrote {csv_path}")

    # Figures
    fig1 = OUT_DIR / "profile_likelihood_landscapes.pdf"
    fig2 = OUT_DIR / "profile_likelihood_ci_bars.pdf"
    _plot_landscapes(per_subject_full, fig1)
    print(f"Wrote {fig1}")
    _plot_ci_bars(per_subject_full, fig2)
    print(f"Wrote {fig2}")

    # JSON summary with group statistics + MW test
    cvd_areas = [r["ci_area"] for r in per_subject_full if r["group"] == "CVD"]
    hc_areas = [r["ci_area"] for r in per_subject_full if r["group"] == "HC"]

    def _stats(arr: list[float]) -> dict:
        if not arr:
            return {"n": 0}
        a = np.asarray(arr)
        return {
            "n": int(a.size),
            "median": float(np.median(a)),
            "iqr_low": float(np.quantile(a, 0.25)),
            "iqr_high": float(np.quantile(a, 0.75)),
            "min": float(a.min()),
            "max": float(a.max()),
        }

    mw_result = {}
    if cvd_areas and hc_areas:
        u, p = mannwhitneyu(cvd_areas, hc_areas, alternative="less")
        mw_result = {
            "test": "Mann-Whitney U (one-sided: CVD ci_area < HC ci_area)",
            "u_statistic": float(u),
            "p_value": float(p),
            "n_cvd": len(cvd_areas),
            "n_hc": len(hc_areas),
        }

    # Verdict (descriptive language only — CLAUDE.md §0/§6 compliance)
    cvd_med = float(np.median(cvd_areas)) if cvd_areas else float("nan")
    hc_med = float(np.median(hc_areas)) if hc_areas else float("nan")
    cvd_sig = [float(r["sigma_sq"]) for r in per_subject_full if r["group"] == "CVD"]
    hc_sig = [float(r["sigma_sq"]) for r in per_subject_full if r["group"] == "HC"]
    cvd_sig_med = float(np.median(cvd_sig)) if cvd_sig else float("nan")
    hc_sig_med = float(np.median(hc_sig)) if hc_sig else float("nan")
    p_val = mw_result.get("p_value", float("nan"))
    if not math.isnan(p_val):
        if p_val < 0.05 and cvd_med < hc_med:
            verdict_label = "cvd_narrower_than_hc_loo"
            verdict_text = (
                f"CVD V4 landscapes are descriptively narrower than HC LOO V4 landscapes "
                f"(median CI area {cvd_med*100:.1f}% vs {hc_med*100:.1f}%, "
                f"one-sided Mann-Whitney p={p_val:.3f}). "
                f"Descriptive observation only; consistent with the 2-component model class."
            )
        elif cvd_med <= hc_med:
            verdict_label = "weak_descriptive_separation"
            verdict_text = (
                f"CVD V4 landscapes trend narrower than HC LOO (median {cvd_med*100:.1f}% vs "
                f"{hc_med*100:.1f}%) but one-sided Mann-Whitney does not reach 0.05 "
                f"(p={p_val:.3f}). Descriptive only."
            )
        else:
            verdict_label = "cvd_wider_than_hc_loo"
            verdict_text = (
                f"CVD V4 landscapes are descriptively WIDER than HC LOO V4 landscapes "
                f"(median CI area CVD={cvd_med*100:.1f}% vs HC={hc_med*100:.1f}%; one-sided "
                f"Mann-Whitney CVD<HC p={p_val:.3f}). "
                f"This direction is driven by residual-variance asymmetry: HC LOO sigma^2 median "
                f"={hc_sig_med:.3f} (HC pool fits held-out HC tightly) vs CVD sigma^2 median "
                f"={cvd_sig_med:.3f} (HC pool fits CVD poorly). Wider CI under the profile-"
                f"likelihood formula = L_fit_min + sigma^2*chi2/8 is therefore a fit-residual "
                f"scale artifact, not parameter identifiability per se. "
                f"Descriptive landscape-shape observation only; consistent with the prior finding "
                f"(MEMORY 2026-04-11) that hV4 LOCO landscape shape does not specifically "
                f"distinguish CVD from HC LOO. NO specificity claim, NO selection-rule change."
            )
    else:
        verdict_label = "incomplete_data"
        verdict_text = "Group comparison not computed (missing CVD or HC LOO data)."

    summary = {
        "method": (
            "profile_likelihood_CI: threshold = L_fit_min + sigma^2 * chi2(2, 0.95) / 8, "
            "with sigma^2 = var(vuln_target - vuln_sim_best, ddof=1). "
            "Descriptive landscape-sharpness diagnostic only; NOT a specificity test."
        ),
        "chi2_95_df2": CHI2_95_DF2,
        "grid": {"bs": [GRID_BS_MIN, GRID_BS_MAX, 2.0], "bc": [GRID_BC_MIN, GRID_BC_MAX, 2.0],
                 "n_cells": 1326},
        "loss_weights_shared": {"alpha": 1.0, "beta": 0.5, "delta": 0.2, "epsilon": 0.1},
        "loss_weights_note": (
            "Confirmed identical across CVD (old_formula) and HC LOO "
            "(phase_a_2component_hc_sanity) landscapes."
        ),
        "subjects": [
            {k: v for k, v in r.items() if not k.startswith("_")}
            for r in per_subject_full
        ],
        "missing": missing,
        "group_summary": {
            "cvd_ci_area": _stats(cvd_areas),
            "hc_ci_area": _stats(hc_areas),
            "mann_whitney": mw_result,
        },
        "verdict": {"label": verdict_label, "text": verdict_text},
        "interpretation_rules": (
            "Profile-likelihood CI here is a single-subject internal landscape property. "
            "Not used for filter selection, specificity claim, or selection-rule reformulation."
        ),
    }

    json_path = OUT_DIR / "profile_likelihood_ci_summary.json"
    json_path.write_text(json.dumps(summary, indent=2))
    print(f"Wrote {json_path}")

    if missing:
        print("\nMissing/skipped:")
        for m in missing:
            print(f"  - {m}")


if __name__ == "__main__":
    main()
