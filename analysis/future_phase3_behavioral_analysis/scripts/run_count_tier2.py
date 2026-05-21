#!/usr/bin/env python
"""
run_count_tier2.py — Tier 2: Geometric stability under run reduction.

Per (subject, ROI, n, subset) computes:
  (4) noise_ceiling           — Spearman-Brown-corrected upper bound on RDM
                                reliability, plus the raw split-half lower bound.
                                Crossnobis RDM is the substrate (Walther 2016).
  (5) procrustes_disparity    — disparity between half-A and half-B β-pattern
                                configurations (scipy.spatial.procrustes),
                                rotation/scale-invariant. Reported as mean over
                                split pairs. Low value = stable color geometry.
  (6) circular_rsa            — Spearman between observed crossnobis RDM and
                                the ideal circular-hue RDM (8 equispaced
                                colors on a circle, distance = chord length).
                                Tests whether circular topology survives.

Output: run_count_validation/tier2_geometric_stability.json
"""
from __future__ import annotations

import json
import sys
import time
from itertools import combinations
from pathlib import Path

import numpy as np
from joblib import Parallel, delayed
from scipy.spatial import procrustes
from scipy.stats import spearmanr

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT / "analysis" / "future_phase1_forward_model" / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT / "analysis" / "future_phase3_behavioral_analysis" / "scripts"))

from utils_forward_model import (  # noqa: E402
    HC_SUBJECTS, CVD_SUBJECTS, N_COLORS, load_amplitudes,
)
from run_count_crossnobis import (  # noqa: E402
    crossnobis_rdm, rdm_upper_vec, general_split_pairs,
)

BASELINE_DIR = PROJECT_ROOT / "analysis" / "phase1_procrustes_decoding" / \
    "results" / "visualization" / "full_dataset_C010_with_residuals"

ROIS = ["V1", "V2", "V3", "V4"]
ALL_SUBJECTS = HC_SUBJECTS + CVD_SUBJECTS
OUT_DIR = PROJECT_ROOT / "analysis" / "future_phase3_behavioral_analysis" / \
    "run_count_validation"
N_JOBS = 10
N_VALUES = [2, 3, 4, 5, 6]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def ideal_circular_rdm() -> np.ndarray:
    """8×8 ideal chord-distance RDM for equispaced colors on unit circle."""
    angles = np.deg2rad(np.arange(0, 360, 45))
    pts = np.column_stack([np.cos(angles), np.sin(angles)])
    diffs = pts[:, None, :] - pts[None, :, :]
    return np.sqrt((diffs ** 2).sum(axis=-1))


IDEAL_CIRCULAR_RDM_VEC = rdm_upper_vec(ideal_circular_rdm())


def spearman_brown(r: float) -> float:
    """Spearman-Brown projection from split-half to full-length reliability."""
    if not np.isfinite(r):
        return float("nan")
    denom = 1.0 + r
    if abs(denom) < 1e-12:
        return float("nan")
    return float(2.0 * r / denom)


# ---------------------------------------------------------------------------
# (4) Noise ceiling (lower = split-half ρ, upper = Spearman-Brown corrected)
# ---------------------------------------------------------------------------
def noise_ceiling(amp_sub: np.ndarray) -> dict:
    """Crossnobis split-half RDM Spearman + Spearman-Brown upper bound."""
    n_runs = amp_sub.shape[0]
    if n_runs < 2:
        return {"lower": float("nan"), "upper": float("nan"), "n_splits": 0}
    pairs = general_split_pairs(n_runs)
    sp_list = []
    for (a, b) in pairs:
        amp_a = amp_sub[np.array(a), :, :]
        amp_b = amp_sub[np.array(b), :, :]
        rdm_a = crossnobis_rdm(amp_a)
        rdm_b = crossnobis_rdm(amp_b)
        sp, _ = spearmanr(rdm_upper_vec(rdm_a), rdm_upper_vec(rdm_b))
        sp_list.append(float(sp) if np.isfinite(sp) else float("nan"))
    lower = float(np.nanmean(sp_list)) if sp_list else float("nan")
    upper = spearman_brown(lower)
    return {"lower": lower, "upper": upper, "n_splits": len(pairs)}


# ---------------------------------------------------------------------------
# (5) Procrustes split-half disparity
# ---------------------------------------------------------------------------
def procrustes_disparity_mean(amp_sub: np.ndarray) -> dict:
    """Mean Procrustes disparity between split halves of β-patterns.

    Each half: mean β per color = (8, V). Procrustes aligns the two 8-point
    configurations in V-dim; disparity ∈ [0, 1] (lower = more similar).
    """
    n_runs = amp_sub.shape[0]
    if n_runs < 2:
        return {"mean_disparity": float("nan"), "n_splits": 0}
    pairs = general_split_pairs(n_runs)
    disps = []
    for (a, b) in pairs:
        beta_a = amp_sub[np.array(a), :, :].mean(axis=0)  # (8, V)
        beta_b = amp_sub[np.array(b), :, :].mean(axis=0)
        try:
            _, _, d = procrustes(beta_a, beta_b)
        except ValueError:
            d = float("nan")
        disps.append(float(d))
    return {
        "mean_disparity": float(np.nanmean(disps)),
        "per_split": disps,
        "n_splits": len(pairs),
    }


# ---------------------------------------------------------------------------
# (6) Circular-template RSA
# ---------------------------------------------------------------------------
def circular_rsa(amp_sub: np.ndarray) -> dict:
    """Spearman of observed RDM with ideal chord-distance RDM."""
    rdm = crossnobis_rdm(amp_sub)
    obs_vec = rdm_upper_vec(rdm)
    if not np.all(np.isfinite(obs_vec)) or obs_vec.std() < 1e-12:
        return {"rho": float("nan")}
    rho, _ = spearmanr(obs_vec, IDEAL_CIRCULAR_RDM_VEC)
    return {"rho": float(rho) if np.isfinite(rho) else float("nan")}


# ---------------------------------------------------------------------------
# Cell worker
# ---------------------------------------------------------------------------
def cell_worker(amp_sub: np.ndarray) -> dict:
    return {
        "noise_ceiling": noise_ceiling(amp_sub),
        "procrustes": procrustes_disparity_mean(amp_sub),
        "circular_rsa": circular_rsa(amp_sub),
    }


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
    subsets_by_n = {n: enumerate_n_subsets(n) for n in N_VALUES}
    total = sum(len(v) for v in subsets_by_n.values())
    grand = total * len(ALL_SUBJECTS) * len(ROIS)
    print(f"Tier 2: subsets {[(n, len(subsets_by_n[n])) for n in N_VALUES]} "
          f"= {total} | subjects {len(ALL_SUBJECTS)} | ROIs {len(ROIS)} | "
          f"grand cells {grand}")

    results = {"config": {"rois": ROIS, "subjects": ALL_SUBJECTS,
                          "n_values": N_VALUES,
                          "metrics": ["noise_ceiling", "procrustes", "circular_rsa"],
                          "ideal_template": "chord-distance, 8 equispaced angles",
                          "script": __file__},
               "per_roi": {}}

    t_grand = time.time()
    for roi in ROIS:
        print(f"\n=== ROI {roi} ===")
        amps = {s: load_amplitudes(BASELINE_DIR, s, roi) for s in ALL_SUBJECTS}
        jobs = []
        for n in N_VALUES:
            for sidx, subset in enumerate(subsets_by_n[n]):
                for subj in ALL_SUBJECTS:
                    amp_sub = amps[subj][np.array(subset), :, :]
                    jobs.append((n, sidx, subset, subj, amp_sub))
        t0 = time.time()
        outputs = Parallel(n_jobs=N_JOBS, verbose=0)(
            delayed(cell_worker)(amp_sub) for (_, _, _, _, amp_sub) in jobs
        )
        elapsed = time.time() - t0
        print(f"  {len(jobs)} cells in {elapsed:.1f}s "
              f"({elapsed/len(jobs)*1000:.0f}ms/cell)")

        roi_out = {n: {} for n in N_VALUES}
        for (n, sidx, subset, subj, _amp), result in zip(jobs, outputs):
            if subj not in roi_out[n]:
                roi_out[n][subj] = {}
            roi_out[n][subj][f"subset_{sidx:02d}"] = {
                "runs": list(subset),
                **result,
            }
        results["per_roi"][roi] = roi_out

    out_path = OUT_DIR / "tier2_geometric_stability.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nTotal: {time.time()-t_grand:.1f}s | Saved: {out_path}")


if __name__ == "__main__":
    main()
