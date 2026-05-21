#!/usr/bin/env python
"""
run_count_saturation.py — LOCO ρ + Crossnobis split-half saturation curve

Extends v1 by enumerating ALL C(6, n) subsets for n ∈ {2, 3, 4, 5, 6}.
Produces saturation curves (mean ± SD across subsets) per subject per ROI,
enabling visual cut-off identification.

Subset counts:
  n=2: C(6,2) = 15
  n=3: C(6,3) = 20
  n=4: C(6,4) = 15
  n=5: C(6,5) = 6
  n=6: 1 (anchor)
  Total: 57 subsets

Plus chronological "leading-n" subsets {0..n-1} for each n.

Outputs (run_count_validation/):
  - v1_saturation_loco.json     (LOCO ρ per cell)
  - v1_saturation_crossnobis.json (split-half RDM r, even n only: 2,4,6)
"""

from __future__ import annotations

import json
import sys
import time
from itertools import combinations
from pathlib import Path

import numpy as np
from joblib import Parallel, delayed

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT / "analysis" / "future_phase1_forward_model" / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT / "analysis" / "future_phase2_filter_optimization" / "scripts"))

# Import LOCO helpers
from utils_forward_model import (  # noqa: E402
    HC_SUBJECTS, CVD_SUBJECTS, N_COLORS,
    load_amplitudes, gcv_select_alpha, fit_W_ridge, voxel_pattern_correlation,
)
from utils_distortion_models import get_design_matrix  # noqa: E402
# Import crossnobis helpers from our v1 script
sys.path.insert(0, str(PROJECT_ROOT / "analysis" / "future_phase3_behavioral_analysis" / "scripts"))
from run_count_crossnobis import (  # noqa: E402
    crossnobis_rdm, rdm_upper_vec, split_half_pairs, general_split_pairs,
)
from scipy.stats import spearmanr, pearsonr  # noqa: E402

BASELINE_DIR = PROJECT_ROOT / "analysis" / "phase1_procrustes_decoding" / \
    "results" / "visualization" / "full_dataset_C010_with_residuals"

ROIS_TO_TEST = ["V1", "V2", "V3", "V4"]
ALL_SUBJECTS = HC_SUBJECTS + CVD_SUBJECTS
OUT_DIR = PROJECT_ROOT / "analysis" / "future_phase3_behavioral_analysis" / \
    "run_count_validation"
N_JOBS = 10
N_RUNS_TOTAL = 6
N_VALUES = [2, 3, 4, 5, 6]


# ---------------------------------------------------------------------------
# Core: per-subset metrics
# ---------------------------------------------------------------------------
def loco_rho_full(amp: np.ndarray, C: np.ndarray) -> dict:
    """LOCO ρ per color + alpha distribution. amp: (n_runs, 8, V).

    Returns dict with:
        rho_per_color: list[float] of length 8
        rho_mean: float (mean of rho_per_color)
        alpha_per_fold: list[float] of length 8 (selected GCV α per held-out color)
    """
    n_runs, _, V = amp.shape
    per_color = np.zeros(N_COLORS)
    alphas = np.zeros(N_COLORS)
    for color in range(N_COLORS):
        train_colors = [c for c in range(N_COLORS) if c != color]
        X_train = amp[:, train_colors].reshape(-1, V)
        C_train = np.tile(C[train_colors], (n_runs, 1))
        alpha, _ = gcv_select_alpha(C_train, X_train)
        W = fit_W_ridge(C_train, X_train, alpha)
        Y_pred = C[color:color + 1] @ W
        Y_test = amp[:, color].mean(axis=0, keepdims=True)
        per_color[color] = float(voxel_pattern_correlation(Y_pred, Y_test)[0])
        alphas[color] = float(alpha)
    return {
        "rho_per_color": per_color.tolist(),
        "rho_mean": float(per_color.mean()),
        "alpha_per_fold": alphas.tolist(),
    }


def loco_rho_mean(amp: np.ndarray, C: np.ndarray) -> float:
    """Backwards-compatible wrapper. Returns mean only."""
    return loco_rho_full(amp, C)["rho_mean"]


def crossnobis_splithalf_mean_r(amp: np.ndarray) -> dict:
    """Split-half Spearman of the 8×8 RDM, generalized to any n_runs ≥ 2.

    Splitting policy: floor(n/2) vs ceil(n/2). Each half's RDM is computed via
    LORO crossnobis with MVNN when the half has ≥2 runs; halves with a single
    run fall back to plain Euclidean distance on unwhitened patterns (so n=2
    and the small side of n=3 are reported as a degraded estimate — see REPORT
    §3 for justification).

    amp: (n_runs, 8, V).
    """
    n_runs = amp.shape[0]
    if n_runs < 2:
        return {"mean_spearman": float("nan"), "n_splits": 0}
    pairs = general_split_pairs(n_runs)
    sp_list = []
    for (a, b) in pairs:
        amp_a = amp[np.array(a), :, :]
        amp_b = amp[np.array(b), :, :]
        rdm_a = crossnobis_rdm(amp_a)
        rdm_b = crossnobis_rdm(amp_b)
        sp, _ = spearmanr(rdm_upper_vec(rdm_a), rdm_upper_vec(rdm_b))
        sp_list.append(float(sp) if np.isfinite(sp) else float("nan"))
    return {
        "mean_spearman": float(np.nanmean(sp_list)) if sp_list else float("nan"),
        "n_splits": len(pairs),
    }


# ---------------------------------------------------------------------------
# Subset enumeration
# ---------------------------------------------------------------------------
def enumerate_n_subsets(n: int) -> list[tuple[int, ...]]:
    """All C(N_RUNS_TOTAL, n) subsets."""
    return [tuple(c) for c in combinations(range(N_RUNS_TOTAL), n)]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    C = get_design_matrix("machado_1way", [0.0], cvd_type="deutan")

    # Build subset protocol: dict n -> list of subset tuples + leading subset
    subsets_by_n = {}
    for n in N_VALUES:
        all_subsets = enumerate_n_subsets(n)
        subsets_by_n[n] = all_subsets
    total_subsets = sum(len(v) for v in subsets_by_n.values())
    print(f"Subset counts: {[(n, len(subsets_by_n[n])) for n in N_VALUES]} "
          f"| Total: {total_subsets} | "
          f"Subjects: {len(ALL_SUBJECTS)} | ROIs: {len(ROIS_TO_TEST)}")
    print(f"Grand total cells: {total_subsets * len(ALL_SUBJECTS) * len(ROIS_TO_TEST)}")

    # ----- 1. LOCO saturation -----
    print(f"\n{'='*70}\nLOCO ρ saturation curve\n{'='*70}")
    loco_results = {"config": {"rois": ROIS_TO_TEST, "subjects": ALL_SUBJECTS,
                                "n_values": N_VALUES, "script": __file__},
                    "per_roi": {}}
    t_grand = time.time()

    for roi in ROIS_TO_TEST:
        print(f"\nROI {roi}:")
        amps = {s: load_amplitudes(BASELINE_DIR, s, roi) for s in ALL_SUBJECTS}

        # Build job list: (n, subset_idx_in_n, subject, amp_sub)
        jobs = []
        for n in N_VALUES:
            for sub_idx, subset in enumerate(subsets_by_n[n]):
                for subj in ALL_SUBJECTS:
                    amp_sub = amps[subj][np.array(subset), :, :]
                    jobs.append((n, sub_idx, subset, subj, amp_sub))

        t0 = time.time()
        outputs = Parallel(n_jobs=N_JOBS, verbose=0)(
            delayed(loco_rho_full)(amp_sub, C) for (_, _, _, _, amp_sub) in jobs
        )
        elapsed = time.time() - t0
        print(f"  LOCO ρ: {len(jobs)} cells done in {elapsed:.1f}s")

        # Repack
        roi_out = {n: {} for n in N_VALUES}
        for (n, sub_idx, subset, subj, _amp), result in zip(jobs, outputs):
            if subj not in roi_out[n]:
                roi_out[n][subj] = {}
            roi_out[n][subj][f"subset_{sub_idx:02d}"] = {
                "runs": list(subset),
                "rho": result["rho_mean"],
                "rho_per_color": result["rho_per_color"],
                "alpha_per_fold": result["alpha_per_fold"],
            }
        loco_results["per_roi"][roi] = roi_out

    out_loco = OUT_DIR / "v1_saturation_loco.json"
    with open(out_loco, "w") as f:
        json.dump(loco_results, f, indent=2)
    print(f"\nSaved LOCO: {out_loco}")

    # ----- 2. Crossnobis saturation (all n ≥ 2) -----
    print(f"\n{'='*70}\nCrossnobis split-half saturation (all n ≥ 2)\n{'='*70}")
    cn_results = {"config": {"rois": ROIS_TO_TEST, "subjects": ALL_SUBJECTS,
                              "n_values": [n for n in N_VALUES if n >= 2],
                              "split_policy": "floor(n/2) vs ceil(n/2); halves "
                                              "with 1 run use Euclidean fallback",
                              "script": __file__},
                  "per_roi": {}}

    for roi in ROIS_TO_TEST:
        print(f"\nROI {roi}:")
        amps = {s: load_amplitudes(BASELINE_DIR, s, roi) for s in ALL_SUBJECTS}

        jobs = []
        for n in cn_results["config"]["n_values"]:
            for sub_idx, subset in enumerate(subsets_by_n[n]):
                for subj in ALL_SUBJECTS:
                    amp_sub = amps[subj][np.array(subset), :, :]
                    jobs.append((n, sub_idx, subset, subj, amp_sub))

        t0 = time.time()
        outputs = Parallel(n_jobs=N_JOBS, verbose=0)(
            delayed(crossnobis_splithalf_mean_r)(amp_sub)
            for (_, _, _, _, amp_sub) in jobs
        )
        elapsed = time.time() - t0
        print(f"  Crossnobis: {len(jobs)} cells done in {elapsed:.1f}s")

        roi_out = {n: {} for n in cn_results["config"]["n_values"]}
        for (n, sub_idx, subset, subj, _amp), result in zip(jobs, outputs):
            if subj not in roi_out[n]:
                roi_out[n][subj] = {}
            roi_out[n][subj][f"subset_{sub_idx:02d}"] = {
                "runs": list(subset),
                "mean_spearman": result["mean_spearman"],
                "n_splits": result["n_splits"],
            }
        cn_results["per_roi"][roi] = roi_out

    out_cn = OUT_DIR / "v1_saturation_crossnobis.json"
    with open(out_cn, "w") as f:
        json.dump(cn_results, f, indent=2)
    print(f"\nSaved Crossnobis: {out_cn}")

    print(f"\n{'='*70}\nTotal: {time.time()-t_grand:.1f}s ({(time.time()-t_grand)/60:.1f} min)")


if __name__ == "__main__":
    main()
