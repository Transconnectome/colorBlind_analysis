#!/usr/bin/env python
"""
run_count_permutation.py — Label-permutation null at each run-subset

Extends run_count_subsample.py with label-shuffle permutation test for each
(subject, ROI, subset) cell. Used to determine whether the n=6 LOCO p-value
landmarks (19일 plan §4) survive at n=4.

Scope (per user request 2026-05-20, including sub-09):
  - 10 subjects (HC sub-01..07 + CVD sub-08, sub-09, sub-10)
  - 4 ROIs (V1, V2, V3, V4=hV4)
  - 17 subsets (1×n=6 + 16×n=4)
  - 1000 permutations per cell (screening; can extend to 5000 in v2)

Permutation: within each run, shuffle the assignment of color labels.
This preserves per-run voxel response structure but breaks the
color-pattern association across runs.

Output: run_count_validation/v1_permutation_n4_vs_n6.json
Each cell reports:
  - observed_rho (mean LOCO ρ across 8 colors)
  - perm_p_two: two-sided p (|perm_ρ| >= |observed_ρ|)
  - perm_p_positive: one-sided p (perm_ρ >= observed)
  - perm_p_negative: one-sided p (perm_ρ <= observed)
  - perm_quantiles [2.5, 50, 97.5]
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
from itertools import permutations as iter_permutations

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT / "analysis" / "phase4_forward_model" / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT / "analysis" / "phase5_filter_optimization" / "scripts"))

from utils_forward_model import (  # noqa: E402
    HC_SUBJECTS, CVD_SUBJECTS, N_COLORS,
    load_amplitudes, gcv_select_alpha, fit_W_ridge, voxel_pattern_correlation,
)
from utils_distortion_models import get_design_matrix  # noqa: E402

BASELINE_DIR = PROJECT_ROOT / "analysis" / "phase1_procrustes_decoding" / \
    "results" / "visualization" / "full_dataset_C010_with_residuals"

ROIS_TO_TEST = ["V1", "V2", "V3", "V4"]
ALL_SUBJECTS = HC_SUBJECTS + CVD_SUBJECTS
OUT_DIR = PROJECT_ROOT / "analysis" / "phase6_behavioral_analysis" / \
    "run_count_validation"

N_PERM = 1000          # screening pass; can bump to 5000 in v2
N_JOBS = 10            # parallel cells (14 cores available)
SEED_BASE = 20260520


# ---------------------------------------------------------------------------
# Core LOCO ρ on subsetted amplitudes — returns per-color vector (vulnerability)
# ---------------------------------------------------------------------------
def loco_vuln(amp: np.ndarray, C: np.ndarray) -> np.ndarray:
    """LOCO per-color vulnerability profile. amp: (n_runs, 8, V). Returns (8,)."""
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
    return per_color


def loco_rho(amp: np.ndarray, C: np.ndarray) -> float:
    """Mean LOCO ρ across 8 colors."""
    return float(loco_vuln(amp, C).mean())


# ---------------------------------------------------------------------------
# Two permutation tests at each subset
# ---------------------------------------------------------------------------
# Test A: raw LOCO ρ vs chance label shuffle (decoding test)
#         - shuffle color labels within each run, recompute LOCO ρ
#         - p = fraction of null ρ as extreme as observed
#
# Test B: Spearman(subject_vuln, HC_baseline_vuln) vs chance (profile-match test)
#         - matches project convention (permutation_test_spearman in step1_fit_loco_v2.py)
#         - 8! = 40320 ≤ N_PERM → exact permutation when feasible
#         - one-sided p = fraction of null ρ ≥ observed (positive direction = HC-like)
#         - for CVD vulnerability, we ALSO report one-sided NEGATIVE direction
#           (subject anti-correlated with HC → vulnerability signature)
def run_cell(amp: np.ndarray, C: np.ndarray, hc_baseline_vuln: np.ndarray,
             n_perm: int, seed: int) -> dict:
    """Compute observed LOCO vulnerability profile + 2 permutation tests."""
    rng = np.random.default_rng(seed)
    observed_vuln = loco_vuln(amp, C)
    observed_rho = float(observed_vuln.mean())

    # --- Test A: raw LOCO ρ permutation (decoding above chance) ---
    n_runs = amp.shape[0]
    perm_rhos = np.zeros(n_perm)
    for i in range(n_perm):
        amp_perm = np.empty_like(amp)
        for r in range(n_runs):
            order = rng.permutation(N_COLORS)
            amp_perm[r] = amp[r, order]
        perm_rhos[i] = loco_rho(amp_perm, C)
    p_two_decoding = float((np.abs(perm_rhos) >= abs(observed_rho)).mean())
    p_pos_decoding = float((perm_rhos >= observed_rho).mean())
    p_neg_decoding = float((perm_rhos <= observed_rho).mean())

    # --- Test B: Spearman(observed_vuln, hc_baseline_vuln) permutation ---
    # Project convention (step1_fit_loco_v2.py:permutation_test_spearman)
    # Random sampling (not exact 8!=40320) for speed; matches the non-exact branch
    # of the original implementation when n_perm < 40320.
    spearman_obs, _ = spearmanr(observed_vuln, hc_baseline_vuln)
    if not np.isfinite(spearman_obs):
        spearman_obs = 0.0
    n_perm_spearman = n_perm  # matched with decoding perm
    null_spearman = np.zeros(n_perm_spearman)
    for i in range(n_perm_spearman):
        order = rng.permutation(N_COLORS)
        r, _ = spearmanr(observed_vuln[order], hc_baseline_vuln)
        null_spearman[i] = r if np.isfinite(r) else 0.0
    # One-sided p values (project uses +1 stabilization)
    p_pos_spearman = float((np.sum(null_spearman >= spearman_obs) + 1)
                            / (len(null_spearman) + 1))
    p_neg_spearman = float((np.sum(null_spearman <= spearman_obs) + 1)
                            / (len(null_spearman) + 1))
    p_two_spearman = float((np.sum(np.abs(null_spearman) >= abs(spearman_obs)) + 1)
                            / (len(null_spearman) + 1))

    return {
        "observed_rho": observed_rho,
        "observed_vuln": observed_vuln.tolist(),
        # Test A: raw decoding above chance
        "decoding_perm_p_two": p_two_decoding,
        "decoding_perm_p_positive": p_pos_decoding,
        "decoding_perm_p_negative": p_neg_decoding,
        "decoding_perm_quantiles_2p5_50_97p5":
            np.percentile(perm_rhos, [2.5, 50, 97.5]).tolist(),
        # Test B: profile match with HC baseline (project landmark convention)
        "spearman_obs": float(spearman_obs),
        "profile_perm_p_two": p_two_spearman,
        "profile_perm_p_positive": p_pos_spearman,  # HC-like (decoding)
        "profile_perm_p_negative": p_neg_spearman,  # anti-HC (vulnerability)
    }


# ---------------------------------------------------------------------------
# Subset enumeration
# ---------------------------------------------------------------------------
def build_subset_protocol() -> list[tuple[str, tuple[int, ...], str]]:
    """1×n=6 + 1×n=4 leading + 15×n=4 random."""
    protocol = [("n6", tuple(range(6)), "anchor"),
                ("n4_leading", tuple(range(4)), "leading")]
    for idx, sub in enumerate(combinations(range(6), 4)):
        protocol.append((f"n4_random_{idx:02d}", tuple(sub), "random"))
    return protocol


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    C = get_design_matrix("machado_1way", [0.0], cvd_type="deutan")
    subset_protocol = build_subset_protocol()
    print(f"Subsets: {len(subset_protocol)} | "
          f"Subjects: {len(ALL_SUBJECTS)} | ROIs: {len(ROIS_TO_TEST)} | "
          f"N_PERM: {N_PERM} | parallel jobs: {N_JOBS}")

    all_results = {
        "config": {
            "rois": ROIS_TO_TEST,
            "subjects": ALL_SUBJECTS,
            "design": "machado_1way @ Δλ=0 (unshifted)",
            "model": "ridge_gcv encoding LOCO",
            "n_perm": N_PERM,
            "seed_base": SEED_BASE,
            "script": __file__,
        },
        "per_roi": {},
    }

    grand_t0 = time.time()
    for roi in ROIS_TO_TEST:
        print(f"\n{'='*70}\nROI: {roi}\n{'='*70}")
        amps = {s: load_amplitudes(BASELINE_DIR, s, roi) for s in ALL_SUBJECTS}

        # Compute HC baseline vulnerability profile per subset
        # (mean of HC subjects' LOCO vuln vectors on the subsetted runs)
        # Each subject contributes its own vuln; this serves as the reference
        # for the project's permutation_test_spearman convention.
        # NOTE: per-subset HC baseline → HC reference adapts to subset.
        print("  Pre-computing HC baseline vuln per subset (single-thread)...")
        hc_baseline_per_subset = {}
        for (label, subset, _kind) in subset_protocol:
            subset_idx = np.array(subset)
            hc_vulns = []
            for hc_subj in HC_SUBJECTS:
                amp_sub_hc = amps[hc_subj][subset_idx, :, :]
                hc_vulns.append(loco_vuln(amp_sub_hc, C))
            hc_baseline_per_subset[label] = np.mean(np.stack(hc_vulns), axis=0)
        print(f"  HC baseline vuln shape: {hc_baseline_per_subset['n6'].shape}")

        # Build job list with HC baseline injected
        jobs = []
        for s_idx, subj in enumerate(ALL_SUBJECTS):
            for sub_idx, (label, subset, _kind) in enumerate(subset_protocol):
                amp_sub = amps[subj][np.array(subset), :, :]
                hc_base = hc_baseline_per_subset[label]
                seed = SEED_BASE + 10000 * s_idx + sub_idx
                jobs.append((label, subj, amp_sub, hc_base, seed))

        # Parallel execution
        t0 = time.time()
        outputs = Parallel(n_jobs=N_JOBS, verbose=5)(
            delayed(run_cell)(amp_sub, C, hc_base, N_PERM, seed)
            for (_, _, amp_sub, hc_base, seed) in jobs
        )
        elapsed = time.time() - t0
        print(f"ROI {roi}: {len(jobs)} cells × {N_PERM} perm done in {elapsed:.1f}s "
              f"({elapsed/len(jobs)*1000:.0f}ms/cell)")

        # Repack by subset
        roi_out = {"per_subset": {}, "hc_baseline_vuln": {}}
        for (label, subset, kind) in subset_protocol:
            roi_out["per_subset"][label] = {
                "subset_runs": list(subset),
                "kind": kind,
                "n_runs": len(subset),
                "subjects": {},
            }
            roi_out["hc_baseline_vuln"][label] = hc_baseline_per_subset[label].tolist()
        for (label, subj, _amp, _hc, _seed), result in zip(jobs, outputs):
            roi_out["per_subset"][label]["subjects"][subj] = result

        all_results["per_roi"][roi] = roi_out

        # Inline quick summary — focus on profile-match test (project landmark convention)
        for (label, subset, kind) in subset_protocol[:2]:  # n6 + n4_leading
            entries = roi_out["per_subset"][label]["subjects"]
            print(f"  [{label}] "
                  f"sub-08: ρ={entries['08']['observed_rho']:+.3f} "
                  f"sp={entries['08']['spearman_obs']:+.3f} "
                  f"p_neg={entries['08']['profile_perm_p_negative']:.3f} | "
                  f"sub-09 sp={entries['09']['spearman_obs']:+.3f} "
                  f"p_neg={entries['09']['profile_perm_p_negative']:.3f} | "
                  f"sub-10 sp={entries['10']['spearman_obs']:+.3f} "
                  f"p_neg={entries['10']['profile_perm_p_negative']:.3f}")

    grand_elapsed = time.time() - grand_t0
    print(f"\n{'='*70}\nTotal: {grand_elapsed:.1f}s "
          f"({grand_elapsed/60:.1f} min)")

    out_path = OUT_DIR / "v1_permutation_n4_vs_n6.json"
    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
