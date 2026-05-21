#!/usr/bin/env python
"""
run_count_tier3.py — Tier 3: Outcome detection power under run reduction.

Operates on v1_saturation_loco.json (now includes rho_per_color per cell) +
runs a permutation null on the CVD subjects only.

Computes:
  (7) LOCO ρ mean + per-subset SD             (read from saturation)
  (8) Per-color profile stability             (Op-A rank-Spearman across
       subsets per n; Op-B vulnerable-set retention against n=6 anchor)
  (9) HC-vs-CVD Cohen's d per n               (using HC distribution of
       per-subject mean ρ at that n; subject's ρ as effect)
 (10) Empirical specificity p (rank in HC)    (rank of CVD subject's mean ρ
       in the joint pool of 7 HC + self; one-sided lower test)
 (11) Permutation null (label shuffle within-run, B=100) for CVD subjects
       only — gives per-cell empirical p of mean LOCO ρ ≤ obs

Output: run_count_validation/tier3_outcome_detection.json
        run_count_validation/profile_stability.json
"""
from __future__ import annotations

import json
import sys
import time
from itertools import combinations
from pathlib import Path

import numpy as np
from joblib import Parallel, delayed
from scipy.stats import spearmanr

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT / "analysis" / "future_phase1_forward_model" / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT / "analysis" / "future_phase2_filter_optimization" / "scripts"))

from utils_forward_model import (  # noqa: E402
    HC_SUBJECTS, CVD_SUBJECTS, N_COLORS,
    load_amplitudes, gcv_select_alpha, fit_W_ridge, voxel_pattern_correlation,
)
from utils_distortion_models import get_design_matrix  # noqa: E402

BASELINE_DIR = PROJECT_ROOT / "analysis" / "phase1_procrustes_decoding" / \
    "results" / "visualization" / "full_dataset_C010_with_residuals"

ROIS = ["V1", "V2", "V3", "V4"]
ALL_SUBJECTS = HC_SUBJECTS + CVD_SUBJECTS
OUT_DIR = PROJECT_ROOT / "analysis" / "future_phase3_behavioral_analysis" / \
    "run_count_validation"
N_JOBS = 10
N_VALUES = [2, 3, 4, 5, 6]
N_PERM = 100
RNG_SEED = 20260521

VULNERABLE_K = 2  # bottom-K colors define vulnerable set


# ---------------------------------------------------------------------------
# LOCO under permutation
# ---------------------------------------------------------------------------
def loco_rho_mean(amp: np.ndarray, C: np.ndarray) -> float:
    n_runs, _, V = amp.shape
    per_color = np.zeros(N_COLORS)
    for color in range(N_COLORS):
        train_colors = [c for c in range(N_COLORS) if c != color]
        X_train = amp[:, train_colors].reshape(-1, V)
        C_train = np.tile(C[train_colors], (n_runs, 1))
        alpha, _ = gcv_select_alpha(C_train, X_train)
        W = fit_W_ridge(C_train, X_train, alpha)
        Y_pred = C[color:color + 1] @ W
        Y_test = amp[:, color].mean(axis=0, keepdims=True)
        per_color[color] = float(voxel_pattern_correlation(Y_pred, Y_test)[0])
    return float(per_color.mean())


def permute_within_run(amp: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Independently shuffle the color dimension within each run."""
    amp_perm = amp.copy()
    for r in range(amp_perm.shape[0]):
        perm = rng.permutation(N_COLORS)
        amp_perm[r] = amp_perm[r, perm, :]
    return amp_perm


def perm_null_one_cell(amp_sub: np.ndarray, C: np.ndarray,
                       n_perm: int, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    rhos = []
    for _ in range(n_perm):
        amp_p = permute_within_run(amp_sub, rng)
        rhos.append(loco_rho_mean(amp_p, C))
    return {"perm_rho_mean": float(np.mean(rhos)),
            "perm_rho_5pct": float(np.percentile(rhos, 5)),
            "perm_rho_95pct": float(np.percentile(rhos, 95)),
            "n_perm": n_perm,
            "perm_rhos": rhos}


# ---------------------------------------------------------------------------
# Helpers for post-hoc analysis on saturation file
# ---------------------------------------------------------------------------
def per_subject_n_means(sat: dict, roi: str, subj: str, n: int) -> dict:
    """Mean across subsets at given n. Returns dict with mean ρ + per-color array."""
    cells = sat["per_roi"][roi][str(n)][subj]
    rhos = np.array([c["rho"] for c in cells.values()])
    per_color = np.array([c["rho_per_color"] for c in cells.values()])  # (S, 8)
    return {
        "mean_rho": float(rhos.mean()),
        "sd_rho": float(rhos.std()),
        "per_color_mean": per_color.mean(axis=0).tolist(),
        "per_color_sd": per_color.std(axis=0).tolist(),
        "per_subset_rho": rhos.tolist(),
        "per_subset_per_color": per_color.tolist(),
        "n_subsets": len(cells),
    }


# ---------------------------------------------------------------------------
# Op-A: rank Spearman between subset per-color profiles
# ---------------------------------------------------------------------------
def op_a_rank_stability(per_subset_per_color: np.ndarray) -> dict:
    """Mean pairwise Spearman of per-color ρ profile across subsets."""
    S = per_subset_per_color.shape[0]
    if S < 2:
        return {"mean_spearman": float("nan"), "n_pairs": 0}
    rhos = []
    for i, j in combinations(range(S), 2):
        rho, _ = spearmanr(per_subset_per_color[i], per_subset_per_color[j])
        rhos.append(float(rho) if np.isfinite(rho) else float("nan"))
    return {
        "mean_spearman": float(np.nanmean(rhos)),
        "sd_spearman": float(np.nanstd(rhos)),
        "n_pairs": len(rhos),
    }


# ---------------------------------------------------------------------------
# Op-B: vulnerable-set retention against n=6 anchor
# ---------------------------------------------------------------------------
def op_b_vulnerable_retention(per_subset_per_color: np.ndarray,
                              anchor_per_color: np.ndarray,
                              k: int = VULNERABLE_K) -> dict:
    """Fraction of subset bottom-K colors that overlap with anchor's bottom-K."""
    anchor_bottom = set(np.argsort(anchor_per_color)[:k].tolist())
    overlaps = []
    for prof in per_subset_per_color:
        subset_bottom = set(np.argsort(prof)[:k].tolist())
        overlap = len(anchor_bottom & subset_bottom) / k
        overlaps.append(overlap)
    return {
        "anchor_bottom_k": sorted(anchor_bottom),
        "mean_retention": float(np.mean(overlaps)),
        "sd_retention": float(np.std(overlaps)),
        "k": k,
        "n_subsets": len(overlaps),
    }


# ---------------------------------------------------------------------------
# Cohen's d for CVD vs HC distribution
# ---------------------------------------------------------------------------
def cohens_d_vs_hc(cvd_mean: float, hc_means: list[float]) -> float:
    hc_arr = np.array(hc_means)
    sd = hc_arr.std(ddof=1)
    if sd < 1e-12:
        return float("nan")
    return float((hc_arr.mean() - cvd_mean) / sd)


def hc_rank_p(cvd_mean: float, hc_means: list[float]) -> float:
    """Empirical one-sided lower-tail p: fraction of (HC, self) <= cvd_mean.

    HC means + self pooled; rank of self / (N+1).
    """
    pool = list(hc_means) + [cvd_mean]
    pool_sorted = sorted(pool)
    rank = pool_sorted.index(cvd_mean) + 1
    return float(rank / (len(pool) + 1))


# ---------------------------------------------------------------------------
# Subset enumeration
# ---------------------------------------------------------------------------
def enumerate_n_subsets(n: int) -> list[tuple[int, ...]]:
    return [tuple(c) for c in combinations(range(6), n)]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    sat_path = OUT_DIR / "v1_saturation_loco.json"
    with open(sat_path) as f:
        sat = json.load(f)
    print(f"Loaded saturation: {sat_path}")

    C = get_design_matrix("machado_1way", [0.0], cvd_type="deutan")

    # -------- A. Post-hoc Cohen's d + HC-rank p --------
    print("\n=== Post-hoc: Cohen's d + HC-rank p ===")
    posthoc = {"per_roi": {}}
    for roi in ROIS:
        roi_out = {n: {} for n in N_VALUES}
        for n in N_VALUES:
            hc_means = []
            for hc in HC_SUBJECTS:
                pm = per_subject_n_means(sat, roi, hc, n)
                hc_means.append(pm["mean_rho"])
            for subj in ALL_SUBJECTS:
                pm = per_subject_n_means(sat, roi, subj, n)
                d = cohens_d_vs_hc(pm["mean_rho"], hc_means)
                p = hc_rank_p(pm["mean_rho"], hc_means)
                roi_out[n][subj] = {
                    "mean_rho": pm["mean_rho"],
                    "sd_rho_across_subsets": pm["sd_rho"],
                    "n_subsets": pm["n_subsets"],
                    "cohens_d_vs_hc": d,
                    "hc_rank_p_one_sided": p,
                }
        posthoc["per_roi"][roi] = roi_out

    # -------- B. Profile stability (Op-A + Op-B) --------
    print("\n=== Profile stability (Op-A + Op-B) ===")
    profile = {"per_roi": {}, "config": {
        "op_a": "mean pairwise Spearman of per-color ρ profile across C(6,n) subsets",
        "op_b": f"retention of bottom-{VULNERABLE_K} colors against n=6 anchor profile",
        "subjects": ALL_SUBJECTS,
        "rois": ROIS,
        "n_values": N_VALUES,
    }}
    for roi in ROIS:
        roi_out = {n: {} for n in N_VALUES}
        for subj in ALL_SUBJECTS:
            anchor = np.array(per_subject_n_means(sat, roi, subj, 6)["per_color_mean"])
            for n in N_VALUES:
                pm = per_subject_n_means(sat, roi, subj, n)
                per_sub = np.array(pm["per_subset_per_color"])  # (S, 8)
                opa = op_a_rank_stability(per_sub)
                opb = op_b_vulnerable_retention(per_sub, anchor, k=VULNERABLE_K)
                roi_out[n][subj] = {
                    "op_a": opa,
                    "op_b": opb,
                    "per_color_mean": pm["per_color_mean"],
                    "per_color_sd": pm["per_color_sd"],
                }
        profile["per_roi"][roi] = roi_out

    profile_path = OUT_DIR / "profile_stability.json"
    with open(profile_path, "w") as f:
        json.dump(profile, f, indent=2)
    print(f"Saved profile_stability: {profile_path}")

    # -------- C. Permutation null on CVD subjects --------
    print(f"\n=== Permutation null (CVD subjects, B={N_PERM}) ===")
    perm_results = {"per_roi": {},
                    "config": {"n_perm": N_PERM, "subjects": CVD_SUBJECTS,
                               "rois": ROIS, "n_values": N_VALUES,
                               "permutation": "within-run color label shuffle",
                               "seed": RNG_SEED}}
    rng_master = np.random.default_rng(RNG_SEED)
    t_grand = time.time()
    for roi in ROIS:
        print(f"\nROI {roi}:")
        amps = {s: load_amplitudes(BASELINE_DIR, s, roi) for s in CVD_SUBJECTS}
        jobs = []
        for n in N_VALUES:
            subsets = enumerate_n_subsets(n)
            for sidx, subset in enumerate(subsets):
                for subj in CVD_SUBJECTS:
                    amp_sub = amps[subj][np.array(subset), :, :]
                    seed = int(rng_master.integers(0, 2**31 - 1))
                    jobs.append((n, sidx, subset, subj, amp_sub, seed))
        t0 = time.time()
        outputs = Parallel(n_jobs=N_JOBS, verbose=0)(
            delayed(perm_null_one_cell)(amp_sub, C, N_PERM, seed)
            for (_, _, _, _, amp_sub, seed) in jobs
        )
        elapsed = time.time() - t0
        print(f"  {len(jobs)} cells × B={N_PERM} in {elapsed:.1f}s "
              f"({elapsed/len(jobs)*1000:.0f}ms/cell)")

        roi_out = {n: {} for n in N_VALUES}
        for (n, sidx, subset, subj, _amp, _seed), result in zip(jobs, outputs):
            obs_rho = sat["per_roi"][roi][str(n)][subj][f"subset_{sidx:02d}"]["rho"]
            # one-sided lower p
            perm_rhos = np.array(result["perm_rhos"])
            emp_p = float((1 + (perm_rhos <= obs_rho).sum()) / (N_PERM + 1))
            if subj not in roi_out[n]:
                roi_out[n][subj] = {}
            roi_out[n][subj][f"subset_{sidx:02d}"] = {
                "runs": list(subset),
                "obs_rho": obs_rho,
                "perm_rho_mean": result["perm_rho_mean"],
                "perm_rho_5pct": result["perm_rho_5pct"],
                "perm_rho_95pct": result["perm_rho_95pct"],
                "empirical_p_lower": emp_p,
            }
        perm_results["per_roi"][roi] = roi_out

    print(f"\nTotal permutation time: {time.time()-t_grand:.1f}s")

    # -------- D. Consolidate into single Tier 3 output --------
    out = {
        "config": {
            "script": __file__,
            "rois": ROIS,
            "subjects": ALL_SUBJECTS,
            "cvd_subjects": CVD_SUBJECTS,
            "n_values": N_VALUES,
            "n_perm": N_PERM,
        },
        "posthoc": posthoc,
        "permutation": perm_results,
    }
    out_path = OUT_DIR / "tier3_outcome_detection.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"Saved Tier 3: {out_path}")


if __name__ == "__main__":
    main()
