#!/usr/bin/env python
"""
run_count_tier1.py — Tier 1: Signal-quality metrics under run reduction.

Per (subject, ROI, n, subset) computes:
  (1) beta_split_half_r       — per-color voxel-pattern Pearson between halves
                                (mean over colors; per-color also retained)
  (2) loro_acc8               — 8-way leave-one-run-out template-matching
                                accuracy (chance = 0.125). Only computed for
                                subsets with n_runs ≥ 2.

GCV α distribution (Tier 1 #2) is already saved by run_count_saturation.py.

Output: run_count_validation/tier1_signal_quality.json
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
sys.path.insert(0, str(PROJECT_ROOT / "analysis" / "phase4_forward_model" / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT / "analysis" / "phase5_filter_optimization" / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT / "analysis" / "phase6_behavioral_analysis" / "scripts"))

from utils_forward_model import (  # noqa: E402
    HC_SUBJECTS, CVD_SUBJECTS, N_COLORS,
    load_amplitudes, gcv_select_alpha, fit_W_ridge, voxel_pattern_correlation,
)
from utils_distortion_models import get_design_matrix  # noqa: E402
from run_count_crossnobis import general_split_pairs  # noqa: E402

BASELINE_DIR = PROJECT_ROOT / "analysis" / "phase1_procrustes_decoding" / \
    "results" / "visualization" / "full_dataset_C010_with_residuals"

ROIS = ["V1", "V2", "V3", "V4"]
ALL_SUBJECTS = HC_SUBJECTS + CVD_SUBJECTS
OUT_DIR = PROJECT_ROOT / "analysis" / "phase6_behavioral_analysis" / \
    "run_count_validation"
N_JOBS = 10
N_VALUES = [2, 3, 4, 5, 6]


# ---------------------------------------------------------------------------
# (1) Per-color β-map split-half voxel correlation
# ---------------------------------------------------------------------------
def beta_split_half(amp_sub: np.ndarray) -> dict:
    """Mean per-color voxel-pattern Pearson between disjoint halves of runs.

    For n_runs < 2 returns NaN. For each split, compute mean β per color in
    each half and correlate voxel patterns per color.

    amp_sub: (n_runs, 8, V)
    """
    n_runs = amp_sub.shape[0]
    if n_runs < 2:
        return {"mean_r": float("nan"),
                "per_color_mean_r": [float("nan")] * N_COLORS,
                "n_splits": 0}
    pairs = general_split_pairs(n_runs)
    per_color_per_split = np.zeros((len(pairs), N_COLORS))
    for k, (a, b) in enumerate(pairs):
        beta_a = amp_sub[np.array(a), :, :].mean(axis=0)   # (8, V)
        beta_b = amp_sub[np.array(b), :, :].mean(axis=0)   # (8, V)
        r = voxel_pattern_correlation(beta_a, beta_b)       # (8,)
        per_color_per_split[k] = r
    per_color_mean = per_color_per_split.mean(axis=0)        # (8,)
    return {
        "mean_r": float(per_color_mean.mean()),
        "per_color_mean_r": per_color_mean.tolist(),
        "n_splits": len(pairs),
    }


# ---------------------------------------------------------------------------
# (2) LORO 8-way template-matching decoding accuracy
# ---------------------------------------------------------------------------
def loro_acc8(amp_sub: np.ndarray, C: np.ndarray) -> dict:
    """LORO 8-way decoding via template-matching.

    For each held-out run r:
      - train W on amp[[runs!=r]] pooled, design matrix tiled
      - for each color c, predict Y_pred_c = C[c] @ W
      - for each test trial X_test[c_obs, :] = amp[r, c_obs, :],
        decode as argmax_c corr(X_test, Y_pred_c)
      - accuracy = mean(decoded == c_obs)

    amp_sub: (n_runs, 8, V); C: (8, K)

    Returns dict with mean_acc, per_run_acc, confusion (8x8 normalized rows).
    """
    n_runs, _, V = amp_sub.shape
    if n_runs < 2:
        return {"mean_acc": float("nan"), "per_run_acc": [], "confusion": None}
    accs = []
    conf = np.zeros((N_COLORS, N_COLORS), dtype=float)
    for r in range(n_runs):
        train = [t for t in range(n_runs) if t != r]
        X_train = amp_sub[train].reshape(-1, V)
        C_train = np.tile(C, (len(train), 1))
        alpha, _ = gcv_select_alpha(C_train, X_train)
        W = fit_W_ridge(C_train, X_train, alpha)
        Y_pred = C @ W                                # (8, V)
        X_test = amp_sub[r]                           # (8, V)
        correct = 0
        for true_c in range(N_COLORS):
            x = X_test[true_c]
            if x.std() < 1e-12:
                continue
            # corr between x and each Y_pred[c]
            corrs = np.zeros(N_COLORS)
            for c in range(N_COLORS):
                yp = Y_pred[c]
                if yp.std() < 1e-12:
                    corrs[c] = -np.inf
                else:
                    cc = np.corrcoef(x, yp)[0, 1]
                    corrs[c] = cc if np.isfinite(cc) else -np.inf
            pred_c = int(np.argmax(corrs))
            conf[true_c, pred_c] += 1.0
            if pred_c == true_c:
                correct += 1
        accs.append(correct / N_COLORS)
    # Normalize confusion rows
    row_sums = conf.sum(axis=1, keepdims=True)
    conf_norm = np.where(row_sums > 0, conf / np.maximum(row_sums, 1), 0.0)
    return {
        "mean_acc": float(np.mean(accs)),
        "per_run_acc": [float(a) for a in accs],
        "confusion": conf_norm.tolist(),
    }


# ---------------------------------------------------------------------------
# Cell worker
# ---------------------------------------------------------------------------
def cell_worker(amp_sub: np.ndarray, C: np.ndarray) -> dict:
    return {
        "beta_split_half": beta_split_half(amp_sub),
        "loro_acc8": loro_acc8(amp_sub, C),
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
    C = get_design_matrix("machado_1way", [0.0], cvd_type="deutan")

    subsets_by_n = {n: enumerate_n_subsets(n) for n in N_VALUES}
    total = sum(len(v) for v in subsets_by_n.values())
    grand = total * len(ALL_SUBJECTS) * len(ROIS)
    print(f"Tier 1: subsets {[(n, len(subsets_by_n[n])) for n in N_VALUES]} "
          f"= {total} | subjects {len(ALL_SUBJECTS)} | ROIs {len(ROIS)} | "
          f"grand cells {grand}")

    results = {"config": {"rois": ROIS, "subjects": ALL_SUBJECTS,
                          "n_values": N_VALUES,
                          "metrics": ["beta_split_half", "loro_acc8"],
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
            delayed(cell_worker)(amp_sub, C) for (_, _, _, _, amp_sub) in jobs
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

    out_path = OUT_DIR / "tier1_signal_quality.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nTotal: {time.time()-t_grand:.1f}s | Saved: {out_path}")


if __name__ == "__main__":
    main()
