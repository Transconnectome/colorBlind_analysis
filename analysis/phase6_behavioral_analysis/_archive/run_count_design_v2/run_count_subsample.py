#!/usr/bin/env python
"""
run_count_subsample.py — v1 minimal skeleton

Enumerates C(6, n) run subsets and recomputes per-subject LOCO ρ on hV4.
Goal: empirically test whether 4-run subsets reproduce the 6-run LOCO ρ
landmark for sub-08 hV4 (the most-cited Phase 2 anchor).

Per advisor (2026-05-20), v1 scope is intentionally narrow:
  - 1 ROI (hV4 / V4 on disk)
  - All 10 subjects (HC + CVD) — HC FPR is the binding specificity criterion
  - n ∈ {6 (anchor), 4 (decision boundary)}
  - n=4: 15 random subsets C(6,4) + 1 leading subset {0,1,2,3}
  - Point estimate only — no permutation null (separate SLURM job later)
  - Encoding-direction LOCO ρ (ridge_gcv pooled), unshifted design

Output: run_count_validation/v1_hV4_n4_vs_n6.json
"""

from __future__ import annotations

import json
import sys
from itertools import combinations
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------------------
# Path setup — reuse existing canonical machinery
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT / "analysis" / "phase4_forward_model" / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT / "analysis" / "phase5_filter_optimization" / "scripts"))

from utils_forward_model import (  # noqa: E402
    HC_SUBJECTS, CVD_SUBJECTS, N_COLORS, HUE_ANGLES,
    load_amplitudes, gcv_select_alpha, fit_W_ridge, voxel_pattern_correlation,
)
from utils_distortion_models import get_design_matrix  # noqa: E402

BASELINE_DIR = PROJECT_ROOT / "analysis" / "phase1_procrustes_decoding" / \
    "results" / "visualization" / "full_dataset_C010_with_residuals"

ROIS_TO_TEST = ["V1", "V2", "V3", "V4"]  # V4 == hV4 on disk
ALL_SUBJECTS = HC_SUBJECTS + CVD_SUBJECTS  # 10 subjects
OUT_DIR = PROJECT_ROOT / "analysis" / "phase6_behavioral_analysis" / \
    "run_count_validation"


# ---------------------------------------------------------------------------
# Single-subject LOCO ρ on a subsetted amplitudes array
# ---------------------------------------------------------------------------
def loco_rho_subset(amp_subj: np.ndarray, C: np.ndarray) -> tuple[np.ndarray, float]:
    """LOCO over colors using ridge_gcv encoding, n_runs inferred from amp shape.

    Args:
        amp_subj: (n_runs, 8, V) subsetted amplitudes for one subject
        C: (8, K) unshifted design matrix

    Returns:
        per_color_rho: (8,) per-color voxel pattern correlation
        mean_rho: scalar mean across colors
    """
    n_runs, n_colors, V = amp_subj.shape
    assert n_colors == N_COLORS, f"expected 8 colors, got {n_colors}"

    per_color_rho = np.zeros(N_COLORS)
    for color in range(N_COLORS):
        train_colors = [c for c in range(N_COLORS) if c != color]
        X_train = amp_subj[:, train_colors].reshape(-1, V)            # (n_runs*7, V)
        C_train = np.tile(C[train_colors], (n_runs, 1))               # (n_runs*7, K)

        alpha, _ = gcv_select_alpha(C_train, X_train)
        W = fit_W_ridge(C_train, X_train, alpha)

        Y_pred = C[color:color + 1] @ W                                # (1, V)
        Y_test = amp_subj[:, color].mean(axis=0, keepdims=True)        # (1, V)
        r = voxel_pattern_correlation(Y_pred, Y_test)
        per_color_rho[color] = float(r[0])

    return per_color_rho, float(per_color_rho.mean())


# ---------------------------------------------------------------------------
# Subset enumeration
# ---------------------------------------------------------------------------
def enumerate_subsets(total_runs: int, subset_size: int) -> list[tuple[int, ...]]:
    """All C(total_runs, subset_size) subsets as sorted tuples."""
    return list(combinations(range(total_runs), subset_size))


def leading_subset(subset_size: int) -> tuple[int, ...]:
    """Chronologically leading n runs — the actual proposed shorter protocol."""
    return tuple(range(subset_size))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Unshifted design matrix (baseline, no cone shift)
    C = get_design_matrix("machado_1way", [0.0], cvd_type="deutan")  # (8, K)

    # Subset configuration (shared across ROIs)
    subsets_n4_random = enumerate_subsets(6, 4)     # C(6,4) = 15
    subset_n4_leading = leading_subset(4)            # {0,1,2,3}
    assert len(subsets_n4_random) == 15

    runs_protocol = []
    runs_protocol.append(("n6", tuple(range(6)), "anchor"))
    runs_protocol.append(("n4_leading", subset_n4_leading, "leading"))
    for idx, subset in enumerate(subsets_n4_random):
        runs_protocol.append((f"n4_random_{idx:02d}", subset, "random"))

    all_results = {
        "config": {
            "rois": ROIS_TO_TEST,
            "subjects": ALL_SUBJECTS,
            "design": "machado_1way @ Δλ=0 (unshifted), basis_type=fe, n_channels=6",
            "n_subsets_total": len(runs_protocol),
            "subsets_n4_random_count": 15,
            "model": "ridge_gcv (encoding LOCO)",
            "script": __file__,
        },
        "per_roi": {},
    }

    for roi in ROIS_TO_TEST:
        print(f"\n{'='*70}\nROI: {roi}\n{'='*70}")
        # Load amplitudes per subject for this ROI
        amps = {}
        for subj in ALL_SUBJECTS:
            amp = load_amplitudes(BASELINE_DIR, subj, roi)
            amps[subj] = amp
        print(f"Loaded {len(amps)} subjects | "
              f"voxel counts: {[amps[s].shape[2] for s in ALL_SUBJECTS]}")

        roi_results = {"per_subset": {}}
        for label, subset, kind in runs_protocol:
            subset_idx = np.array(subset)
            per_subj = {}
            for subj, amp in amps.items():
                amp_sub = amp[subset_idx, :, :]
                per_color, mean_rho = loco_rho_subset(amp_sub, C)
                per_subj[subj] = {
                    "mean_rho": mean_rho,
                    "per_color_rho": per_color.tolist(),
                }
            roi_results["per_subset"][label] = {
                "subset_runs": list(subset),
                "kind": kind,
                "n_runs": len(subset),
                "subjects": per_subj,
            }
            print(f"  [{label:18s}] runs={subset} | "
                  f"sub-08 ρ={per_subj['08']['mean_rho']:+.3f}, "
                  f"sub-09 ρ={per_subj['09']['mean_rho']:+.3f}, "
                  f"sub-10 ρ={per_subj['10']['mean_rho']:+.3f}, "
                  f"HC mean ρ={np.mean([per_subj[s]['mean_rho'] for s in HC_SUBJECTS]):+.3f}")

        all_results["per_roi"][roi] = roi_results

    # Save
    out_path = OUT_DIR / "v1_allroi_n4_vs_n6.json"
    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\n{'='*70}\nSaved: {out_path}")
    n_fits = len(runs_protocol) * len(ALL_SUBJECTS) * len(ROIS_TO_TEST) * N_COLORS
    print(f"Total fits: {n_fits} ({len(runs_protocol)} subsets × {len(ALL_SUBJECTS)} subj "
          f"× {len(ROIS_TO_TEST)} ROIs × {N_COLORS} LOCO folds)")


if __name__ == "__main__":
    main()
