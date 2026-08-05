#!/usr/bin/env python
"""
run_count_crossnobis.py — Split-half RDM reliability via crossnobis (Walther 2016)

Computes split-half reliability of the 8×8 color RDM under crossnobis (cross-
validated Mahalanobis) distance, with shrinkage covariance multivariate noise
normalization (MVNN). Reports Spearman and Pearson correlations between RDMs
from disjoint halves of runs.

Splits per subset:
  - n=6: 3 vs 3 → C(6,3)/2 = 10 unique splits
  - n=4: 2 vs 2 → C(4,2)/2 = 3 unique splits

Crossnobis distance (Walther 2016 eq. simplified):
  d²(c1, c2) = (1/V) · <(b1_train - b2_train) · Σ^(-1), (b1_test - b2_test)>
  where train/test are different fold averages within the same half.

Scope:
  - 10 subjects (HC + CVD), 4 ROIs (V1, V2, V3, V4)
  - n ∈ {6, 4}: 17 subsets (1 + 1 + 15)
  - Multiple split-half pairs per subset, mean reliability reported

Output: run_count_validation/v1_crossnobis_n4_vs_n6.json
Per cell: {mean_spearman, mean_pearson, per_split_spearman, per_split_pearson, n_splits}
"""

from __future__ import annotations

import json
import sys
import time
from itertools import combinations
from pathlib import Path

import numpy as np
from joblib import Parallel, delayed
from scipy.stats import spearmanr, pearsonr

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT / "analysis" / "future_phase1_forward_model" / "scripts"))

from utils_forward_model import (  # noqa: E402
    HC_SUBJECTS, CVD_SUBJECTS, N_COLORS, load_amplitudes,
)

BASELINE_DIR = PROJECT_ROOT / "analysis" / "phase1_procrustes_decoding" / \
    "results" / "visualization" / "full_dataset_C010_with_residuals"

ROIS_TO_TEST = ["V1", "V2", "V3", "V4"]
ALL_SUBJECTS = HC_SUBJECTS + CVD_SUBJECTS
OUT_DIR = PROJECT_ROOT / "analysis" / "future_phase3_behavioral_analysis" / \
    "run_count_validation"
N_JOBS = 10


# ---------------------------------------------------------------------------
# Multivariate noise normalization (Walther 2016, Ledoit-Wolf-style shrinkage)
# ---------------------------------------------------------------------------
def shrinkage_covariance(residuals: np.ndarray) -> np.ndarray:
    """Ledoit-Wolf shrinkage estimator of voxel covariance.

    Args:
        residuals: (n_samples, n_voxels) residual matrix from condition mean removal

    Returns:
        Σ_hat: (n_voxels, n_voxels) shrunk covariance
    """
    n_samp, V = residuals.shape
    S = (residuals.T @ residuals) / n_samp                     # (V, V) empirical cov
    mu = np.trace(S) / V
    target = mu * np.eye(V)
    # Ledoit-Wolf optimal shrinkage intensity
    var_S = np.mean((residuals[:, :, None] * residuals[:, None, :] - S[None, :, :])**2)
    var_target = np.mean((S - target)**2)
    lam = np.clip(var_S / (var_target * n_samp + 1e-12), 0.0, 1.0)
    return lam * target + (1.0 - lam) * S


def mvnn_prewhiten(amp_half: np.ndarray) -> np.ndarray:
    """Pre-whiten patterns by Σ^(-1/2) computed from condition residuals.

    For n_runs < 2 the residual matrix is zero (each condition has a single
    sample → residual = sample − mean = 0). In that case MVNN is not defined;
    return the patterns unwhitened so the caller can fall back to Euclidean
    distance.

    Args:
        amp_half: (n_runs_half, 8, V)

    Returns:
        amp_white: (n_runs_half, 8, V) pre-whitened patterns
    """
    n_runs, _, V = amp_half.shape
    if n_runs < 2:
        return amp_half
    cond_mean = amp_half.mean(axis=0, keepdims=True)               # (1, 8, V)
    residuals = (amp_half - cond_mean).reshape(-1, V)              # (n_runs*8, V)
    Sigma = shrinkage_covariance(residuals)
    # Σ^(-1/2) via eigendecomposition
    eigvals, eigvecs = np.linalg.eigh(Sigma)
    eigvals = np.maximum(eigvals, 1e-8 * eigvals.max())
    inv_sqrt = eigvecs @ np.diag(1.0 / np.sqrt(eigvals)) @ eigvecs.T
    amp_white = amp_half @ inv_sqrt                                # broadcast on V
    return amp_white


# ---------------------------------------------------------------------------
# Crossnobis distance matrix from a single half of runs
# ---------------------------------------------------------------------------
def crossnobis_rdm(amp_half: np.ndarray) -> np.ndarray:
    """Crossnobis 8×8 RDM via leave-one-run-out within the half.

    For each pair (c1, c2):
      d²(c1,c2) = mean_r [ (b1_train_r - b2_train_r) · (b1_test_r - b2_test_r) ] / V
    where train_r = mean over runs ≠ r, test_r = run r.

    Pre-whitening is applied (Walther 2016 recommendation: MVNN).

    Args:
        amp_half: (n_runs_half, 8, V)

    Returns:
        rdm: (8, 8) symmetric, zero diagonal
    """
    amp_w = mvnn_prewhiten(amp_half)                                # (R, 8, V)
    R, K, V = amp_w.shape
    if R < 2:
        # Cannot crossvalidate with single run — return Mahalanobis on whitened
        b = amp_w.mean(axis=0)                                       # (8, V)
        rdm = np.zeros((K, K))
        for i in range(K):
            for j in range(i + 1, K):
                d = b[i] - b[j]
                rdm[i, j] = rdm[j, i] = float(np.dot(d, d)) / V
        return rdm

    rdm = np.zeros((K, K))
    for r in range(R):
        test_idx = [r]
        train_idx = [t for t in range(R) if t != r]
        b_train = amp_w[train_idx].mean(axis=0)                      # (8, V)
        b_test = amp_w[test_idx].mean(axis=0)                        # (8, V)
        for i in range(K):
            for j in range(i + 1, K):
                d_train = b_train[i] - b_train[j]
                d_test = b_test[i] - b_test[j]
                rdm[i, j] += float(np.dot(d_train, d_test)) / V
                rdm[j, i] = rdm[i, j]
    rdm /= R
    return rdm


# ---------------------------------------------------------------------------
# Split-half reliability via crossnobis
# ---------------------------------------------------------------------------
def split_half_pairs(n_runs: int):
    """Enumerate unique disjoint half-pairs of runs (even n_runs only)."""
    half = n_runs // 2
    if n_runs % 2 != 0:
        raise ValueError(f"Need even n_runs; got {n_runs}")
    pairs = []
    seen = set()
    for combo_a in combinations(range(n_runs), half):
        combo_b = tuple(sorted(set(range(n_runs)) - set(combo_a)))
        canonical = tuple(sorted([combo_a, combo_b]))
        if canonical not in seen:
            seen.add(canonical)
            pairs.append((combo_a, combo_b))
    return pairs


def general_split_pairs(n_runs: int):
    """All unique disjoint floor(n/2) vs ceil(n/2) splits.

    Equal-size splits (even n_runs) are canonicalized to avoid double counting;
    unequal-size splits (odd n_runs) are enumerated by C(n, floor(n/2)) and are
    inherently unique because the two halves are distinguishable by size.

    Returns:
        list of (small_half_runs_tuple, large_half_runs_tuple)
    """
    small = n_runs // 2
    large = n_runs - small
    if small == 0:
        return []
    if small == large:
        return split_half_pairs(n_runs)
    pairs = []
    for combo_small in combinations(range(n_runs), small):
        combo_large = tuple(sorted(set(range(n_runs)) - set(combo_small)))
        pairs.append((combo_small, combo_large))
    return pairs


def rdm_upper_vec(rdm: np.ndarray) -> np.ndarray:
    """Upper-triangular off-diagonal of RDM as a flat vector."""
    K = rdm.shape[0]
    iu = np.triu_indices(K, k=1)
    return rdm[iu]


def split_half_reliability(amp_sub: np.ndarray) -> dict:
    """Compute mean split-half Spearman/Pearson over all disjoint half-pairs.

    Args:
        amp_sub: (n_runs, 8, V) subsetted amplitudes for one subject

    Returns:
        Dict with mean and per-split reliabilities
    """
    n_runs = amp_sub.shape[0]
    if n_runs % 2 != 0:
        # Can't split evenly; report nan
        return {"mean_spearman": float("nan"), "mean_pearson": float("nan"),
                "n_splits": 0, "per_split_spearman": [], "per_split_pearson": []}

    pairs = split_half_pairs(n_runs)
    sp_list, pe_list = [], []
    for (a, b) in pairs:
        amp_a = amp_sub[np.array(a), :, :]
        amp_b = amp_sub[np.array(b), :, :]
        rdm_a = crossnobis_rdm(amp_a)
        rdm_b = crossnobis_rdm(amp_b)
        va = rdm_upper_vec(rdm_a)
        vb = rdm_upper_vec(rdm_b)
        sp, _ = spearmanr(va, vb)
        pe, _ = pearsonr(va, vb)
        sp_list.append(float(sp) if np.isfinite(sp) else float("nan"))
        pe_list.append(float(pe) if np.isfinite(pe) else float("nan"))

    return {
        "n_splits": len(pairs),
        "mean_spearman": float(np.nanmean(sp_list)),
        "mean_pearson": float(np.nanmean(pe_list)),
        "per_split_spearman": sp_list,
        "per_split_pearson": pe_list,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def build_subset_protocol():
    protocol = [("n6", tuple(range(6)), "anchor"),
                ("n4_leading", tuple(range(4)), "leading")]
    for idx, sub in enumerate(combinations(range(6), 4)):
        protocol.append((f"n4_random_{idx:02d}", tuple(sub), "random"))
    return protocol


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    subset_protocol = build_subset_protocol()
    print(f"Subsets: {len(subset_protocol)} | Subjects: {len(ALL_SUBJECTS)} | "
          f"ROIs: {len(ROIS_TO_TEST)} | parallel jobs: {N_JOBS}")

    all_results = {
        "config": {
            "rois": ROIS_TO_TEST,
            "subjects": ALL_SUBJECTS,
            "metric": "crossnobis (LORO cross-validated Mahalanobis with MVNN)",
            "reliability": "split-half (n=6: 3v3, n=4: 2v2), mean over all unique splits",
            "script": __file__,
        },
        "per_roi": {},
    }

    t_grand = time.time()
    for roi in ROIS_TO_TEST:
        print(f"\n{'='*70}\nROI: {roi}\n{'='*70}")
        amps = {s: load_amplitudes(BASELINE_DIR, s, roi) for s in ALL_SUBJECTS}

        jobs = []
        for subj in ALL_SUBJECTS:
            for (label, subset, _kind) in subset_protocol:
                amp_sub = amps[subj][np.array(subset), :, :]
                jobs.append((label, subj, amp_sub))

        t0 = time.time()
        outputs = Parallel(n_jobs=N_JOBS, verbose=5)(
            delayed(split_half_reliability)(amp_sub) for (_, _, amp_sub) in jobs
        )
        elapsed = time.time() - t0
        print(f"ROI {roi}: {len(jobs)} cells done in {elapsed:.1f}s "
              f"({elapsed/len(jobs)*1000:.0f}ms/cell)")

        roi_out = {"per_subset": {}}
        for (label, subset, kind) in subset_protocol:
            roi_out["per_subset"][label] = {
                "subset_runs": list(subset),
                "kind": kind,
                "n_runs": len(subset),
                "subjects": {},
            }
        for (label, subj, _amp), result in zip(jobs, outputs):
            roi_out["per_subset"][label]["subjects"][subj] = result

        all_results["per_roi"][roi] = roi_out

        # Inline summary for n=6 vs n=4 leading
        for (label, _sub, _k) in subset_protocol[:2]:
            entries = roi_out["per_subset"][label]["subjects"]
            print(f"  [{label}] reliability (Spearman): "
                  f"sub-08={entries['08']['mean_spearman']:+.3f}, "
                  f"sub-09={entries['09']['mean_spearman']:+.3f}, "
                  f"sub-10={entries['10']['mean_spearman']:+.3f}, "
                  f"HC mean={np.mean([entries[s]['mean_spearman'] for s in HC_SUBJECTS]):+.3f}")

    print(f"\n{'='*70}\nTotal: {time.time()-t_grand:.1f}s")
    out_path = OUT_DIR / "v1_crossnobis_n4_vs_n6.json"
    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
