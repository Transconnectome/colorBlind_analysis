#!/usr/bin/env python
"""ICML Fig2 MAIN — 2x2 composite: (A) canonical loss landscape + (B) fixed-param
held-out per-fold RDM generalization, for sub-08 (deutan) and sub-09 (protan).

DATA FIGURE — every number is real.

Panel (A): reuses viz_closure_ground_plot.build_composite_full_hc + plot_panel
           (canonical z-score composite over (β_s,β_c), argmin star + 300-resample
           cloud). Candidates S08_bc_dom (6,−42) / S09_bc_rot (2,+24) already match
           the locked canonical.

Panel (B): FIXED-PARAM held-out RDM loss. For every leave-one-HC-out fold the loss
           is evaluated at the FIXED canonical (β_s,β_c) — NOT refit per fold.
           Fixed-param pin: s18.rdm_heldout_eval reads β at s18_heldout_predictive.py
           lines ~290-291 (bi/bj = nearest grid index to fit['beta_s']/['beta_c'],
           val = grid[bi,bj]). We pass fit={'beta_s':canon,'beta_c':canon} for every
           fold instead of the per-fold composite_argmin refit. L_rdm_test_at_00
           (line ~320, atom(zeros)) is fit-independent.

CORRECTNESS GATE (must pass before plotting):
  median(dL_fold) within +-0.03 of published, AND all 7 dL_fold < 0 (7/7).
  Published: sub-08 -0.406 / sub-09 -0.472.
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import s17_hc_loo as s17
import s18_heldout_predictive as s18
import viz_closure_ground_plot as vcg

OUT_DIR = SCRIPT_DIR.parent / "results" / "visualizations" / "fig2_main"
OUT_DIR.mkdir(parents=True, exist_ok=True)
DOCS_FIG = Path("/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/"
                "colorBlind_analysis/docs/ICML_workshop/figures/fig2_main.pdf")

HC_SUBJS = s18.HC_SUBJS

# Locked canonical candidates. landscape_id -> matching viz_closure_ground_plot CANDIDATE.
SUBJECTS = [
    {
        "subject": "sub-08", "family": "deutan", "roi": "V2",
        "bs": 6.0, "bc": -42.0, "published_dL": -0.406,
        "landscape_id": "S08_bc_dom",
        "title": "Sub-08 deutan  ·  γ_OY + RDM_V2  ·  (β_s, β_c) = (+6, −42)",
    },
    {
        "subject": "sub-09", "family": "protan", "roi": "V1",
        "bs": 2.0, "bc": 24.0, "published_dL": -0.472,
        "landscape_id": "S09_bc_rot",
        "title": "Sub-09 protan  ·  γ_all + RDM_V1  ·  (β_s, β_c) = (+2, +24)",
    },
]


def compute_fixed_param_folds(cfg, cvd_amps, hc_amps_by_roi, K_by_roi, C_by_roi):
    """FIXED-PARAM held-out: evaluate L_rdm_test at the FIXED canonical (β_s,β_c)
    for every leave-one-HC-out fold (no per-fold refit)."""
    roi = cfg["roi"]
    fam = cfg["family"]
    fixed_fit = {"beta_s": cfg["bs"], "beta_c": cfg["bc"]}
    folds = []
    for held in HC_SUBJS:
        rr = s18.rdm_heldout_eval(
            fixed_fit, roi, cvd_amps[roi], held,
            hc_amps_by_roi, C_by_roi[roi], K_by_roi[roi], fam)
        if rr is None:
            continue
        folds.append({
            "held_out_hc": held,
            "L_rdm_test": rr["L_rdm_test"],
            "L_rdm_test_at_00": rr["L_rdm_test_at_00"],
            "dL": rr["L_rdm_test"] - rr["L_rdm_test_at_00"],
        })
    return folds


def check_gate(cfg, folds):
    dLs = np.array([f["dL"] for f in folds])
    med = float(np.median(dLs))
    n_neg = int(np.sum(dLs < 0))
    median_ok = abs(med - cfg["published_dL"]) <= 0.03
    all_neg = bool(np.all(dLs < 0))
    return {"median_dL": med, "n_neg": n_neg, "n": len(dLs),
            "median_ok": median_ok, "all_neg": all_neg,
            "passed": median_ok and all_neg}


def plot_panel_B(ax, cfg, folds, gate):
    """Per-fold held-out RDM loss vs the no-correction (0,0) baseline."""
    labels = [f["held_out_hc"].replace("sub-", "") for f in folds]
    L_test = np.array([f["L_rdm_test"] for f in folds])
    L_00 = np.array([f["L_rdm_test_at_00"] for f in folds])  # ~1.0 (degenerate floor)
    x = np.arange(len(folds))

    baseline = float(np.median(L_00))  # ==1.0; no-correction floor
    below = L_test < baseline
    colors = np.where(below, "#2166ac", "#b2182b")  # blue below baseline, red above

    # no-correction baseline line
    ax.axhline(baseline, color="0.35", lw=1.6, ls="--", zorder=1,
               label="no-correction (0,0) baseline")
    # drop lines from baseline to each point
    for xi, lt in zip(x, L_test):
        ax.plot([xi, xi], [baseline, lt], color="0.7", lw=1.0, zorder=1)
    ax.scatter(x, L_test, s=110, c=colors, edgecolors="white", linewidth=1.0,
               zorder=3)

    med_L = float(np.median(L_test))
    ax.axhline(med_L, color="#2166ac", lw=1.2, ls=":", alpha=0.8, zorder=2,
               label=f"median held-out L = {med_L:.3f}")

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_xlabel("held-out HC (leave-one-HC-out fold)", fontsize=10)
    ax.set_ylabel("held-out RDM loss  L_rdm_test", fontsize=10)
    ax.set_ylim(0.0, 1.12)
    ax.set_xlim(-0.6, len(folds) - 0.4)
    ax.set_title("Fixed-param held-out RDM generalization", fontsize=10)

    annot = (f"median ΔL = {gate['median_dL']:+.3f}\n"
             f"{gate['n_neg']}/{gate['n']} folds beat no-correction")
    ax.text(0.03, 0.05, annot, transform=ax.transAxes, fontsize=9.5,
            va="bottom", ha="left",
            bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="0.5", alpha=0.9))
    ax.legend(loc="upper right", fontsize=8, framealpha=0.85)


def main():
    print("=" * 80)
    print("Fig2 MAIN — fixed-param held-out gate check + 2x2 composite")
    print("=" * 80)

    cvd_amps_by_subj, hc_amps_by_roi, K_by_roi, C_by_roi, _ = \
        s17.preload_data(["sub-08", "sub-09"])

    # ---- (B) compute fixed-param folds + GATE (before any plotting) ----
    per_subject = []
    for cfg in SUBJECTS:
        folds = compute_fixed_param_folds(
            cfg, cvd_amps_by_subj[cfg["subject"]],
            hc_amps_by_roi, K_by_roi, C_by_roi)
        gate = check_gate(cfg, folds)
        per_subject.append((cfg, folds, gate))
        print(f"\n[{cfg['subject']}] {cfg['family']}  RDM_{cfg['roi']}  "
              f"FIXED (β_s,β_c)=({cfg['bs']:.0f},{cfg['bc']:.0f})")
        for f in folds:
            print(f"  {f['held_out_hc']}  L_rdm_test={f['L_rdm_test']:.4f}  "
                  f"L_rdm_test_at_00={f['L_rdm_test_at_00']:.4f}  "
                  f"dL={f['dL']:+.4f}")
        print(f"  median dL = {gate['median_dL']:+.4f}  "
              f"(published {cfg['published_dL']})  "
              f"n_neg={gate['n_neg']}/{gate['n']}")
        print(f"  GATE: median_within_0.03={gate['median_ok']}  "
              f"all_neg={gate['all_neg']}  -> {'PASS' if gate['passed'] else 'FAIL'}")

    if not all(g["passed"] for _, _, g in per_subject):
        print("\n*** CORRECTNESS GATE FAILED — NOT plotting. See per-fold values above.")
        sys.exit(1)
    print("\nAll gates PASSED — building figure.")

    # ---- 2x2 figure ----
    fig = plt.figure(figsize=(20, 12))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.25, 1.0],
                          hspace=0.32, wspace=0.22)

    for row, (cfg, folds, gate) in enumerate(per_subject):
        # Panel (A): canonical loss landscape (reuse ground_plot logic)
        cand = next(c for c in vcg.CANDIDATES if c["id"] == cfg["landscape_id"])
        # sanity: ground_plot candidate must match locked canonical (β_s,β_c)
        assert cand["fit_point"] == (cfg["bs"], cfg["bc"]), \
            f"landscape {cfg['landscape_id']} fit_point {cand['fit_point']} != " \
            f"canonical ({cfg['bs']},{cfg['bc']})"
        comp, _, _, atom_labels, n_a = vcg.build_composite_full_hc(cand)
        bs_s, bc_s = vcg.load_resample_argmins(cand)

        axA = fig.add_subplot(gs[row, 0])
        imA = vcg.plot_panel(axA, comp, atom_labels, n_a, cand["fit_point"],
                             bs_s, bc_s, cfg["title"])
        fig.colorbar(imA, ax=axA, label="composite z (lower = better fit)",
                     shrink=0.85, pad=0.02)

        # Panel (B): fixed-param held-out folds
        axB = fig.add_subplot(gs[row, 1])
        plot_panel_B(axB, cfg, folds, gate)

    fig.suptitle(
        "Fig 2 — Canonical loss landscape (A) and fixed-param held-out RDM "
        "generalization (B) for two CVD subjects",
        fontsize=14, y=0.995)

    pdf_path = OUT_DIR / "fig2_main.pdf"
    png_path = OUT_DIR / "fig2_main.png"
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(png_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"\nsaved {pdf_path}")
    print(f"saved {png_path}")

    DOCS_FIG.parent.mkdir(parents=True, exist_ok=True)
    import shutil
    shutil.copy(pdf_path, DOCS_FIG)
    print(f"copied pdf -> {DOCS_FIG}")


if __name__ == "__main__":
    main()
