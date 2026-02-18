#!/usr/bin/env python3
"""
HC-Only SRM Re-Run (RT-2 Fix for Phase 2)

CRITICAL FIX: Original evaluate_srm_c010_between_subject.py trained SRM
on ALL 10 subjects (HC+CVD jointly), contradicting the methods description
("HC-only training, CVD projected"). This script corrects the bug:

  1. Train SRM on 7 HC subjects ONLY
  2. Project 3 CVD subjects into HC-defined shared space
  3. Compute HC-HC and CVD-HC disparities (same metrics as original)
  4. Run permutation test (10,000 iterations)
  5. Compare with original all-subjects results

Uses the same project_new_subject() approach as the validated
2C k-selection script (run_k_selection_cv.py).

Usage:
    mpirun -np 1 python rerun_hc_only_srm.py
    mpirun -np 1 python rerun_hc_only_srm.py --roi V2
"""

import sys
import argparse
import json
import time
import socket
import numpy as np
from pathlib import Path
from datetime import datetime
from scipy.stats import spearmanr, ttest_ind
from scipy.linalg import orthogonal_procrustes
from itertools import combinations

try:
    from brainiak.funcalign.srm import SRM
except ImportError:
    print("ERROR: brainiak not installed. Run on server with: mpirun -np 1 python rerun_hc_only_srm.py")
    sys.exit(1)

# ============================================================================
# CONFIG
# ============================================================================

HC_SUBJECTS = ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05', 'sub-06', 'sub-07']
CVD_SUBJECTS = ['sub-08', 'sub-09', 'sub-10']
ROIS = ['V1', 'V2', 'V3', 'V4']
ROI_DIR_MAP = {'V1': 'V1', 'V2': 'V2', 'V3': 'V3', 'V4': 'V4'}
ROI_DISPLAY = {'V1': 'V1', 'V2': 'V2', 'V3': 'V3', 'V4': 'hV4'}

# Updated k values from formal aggregation (2026-02-18)
K_VALUES = {'V1': 4, 'V2': 4, 'V3': 3, 'V4': 3}

N_PERMUTATIONS = 10000
SEED = 42

if socket.gethostname().startswith('node'):
    DATA_DIR = Path("/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010")
    OUTPUT_DIR = Path("/scratch/connectome/haba6030/colorBlind/analysis/phase2_SRM_across_between/results/hc_only_rerun")
else:
    DATA_DIR = Path("/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase1_preprocess_decoding/results/full_dataset_C010")
    OUTPUT_DIR = Path(__file__).resolve().parent / "results" / "hc_only_rerun"


# ============================================================================
# CORE FUNCTIONS
# ============================================================================

def load_subject_data(subject, roi):
    """Load Procrustes-aligned amplitudes (6, 8, n_voxels)."""
    roi_dir = ROI_DIR_MAP.get(roi, roi)
    path = DATA_DIR / subject / roi_dir / "amplitudes_procrustes.npy"
    if not path.exists():
        raise FileNotFoundError(f"Not found: {path}")
    return np.load(path)


def project_new_subject(srm_model, new_data):
    """
    Project a new subject into the SRM shared space.
    Copied from validated run_k_selection_cv.py (lines 56-60).

    Args:
        srm_model: Fitted SRM object (trained on HC only)
        new_data: (n_voxels, n_samples) for the new subject

    Returns:
        W_new: (n_voxels, k) orthogonal transformation matrix
    """
    S = srm_model.s_  # (k, n_samples)
    W_init = new_data @ np.linalg.pinv(S)
    U, _, Vt = np.linalg.svd(W_init, full_matrices=False)
    return U @ Vt


def compute_procrustes_disparity(X, Y):
    """Procrustes disparity between two (n_colors, k) patterns."""
    X_c = X - X.mean(axis=0)
    Y_c = Y - Y.mean(axis=0)
    X_n = X_c / np.linalg.norm(X_c, 'fro')
    Y_n = Y_c / np.linalg.norm(Y_c, 'fro')
    R, _ = orthogonal_procrustes(X_n, Y_n)
    return float(np.linalg.norm(X_n @ R - Y_n, 'fro'))


def hedges_g(group1, group2):
    """Hedges' g with small-sample correction."""
    n1, n2 = len(group1), len(group2)
    s_pooled = np.sqrt(((n1-1)*np.var(group1, ddof=1) + (n2-1)*np.var(group2, ddof=1)) / (n1+n2-2))
    if s_pooled == 0:
        return 0.0
    d = (np.mean(group2) - np.mean(group1)) / s_pooled
    return d * (1 - 3 / (4*(n1+n2-2) - 1))


# ============================================================================
# MAIN ANALYSIS
# ============================================================================

def run_hc_only_srm(roi, k):
    """
    HC-only SRM: train on HC, project CVD, compute disparities.

    Returns dict with all results.
    """
    roi_display = ROI_DISPLAY.get(roi, roi)
    print(f"\n{'='*70}")
    print(f"HC-Only SRM: {roi_display}, k={k}")
    print(f"{'='*70}")

    # --- Load data ---
    hc_data = {}  # {subject: (6, 8, n_voxels)}
    for s in HC_SUBJECTS:
        hc_data[s] = load_subject_data(s, roi)
        print(f"  Loaded {s}: {hc_data[s].shape}")

    cvd_data = {}
    for s in CVD_SUBJECTS:
        cvd_data[s] = load_subject_data(s, roi)
        print(f"  Loaded {s}: {cvd_data[s].shape}")

    # --- Train SRM on HC only ---
    print(f"\n  Training SRM on {len(HC_SUBJECTS)} HC subjects only...")
    hc_betas = []  # list of (n_voxels, 8)
    for s in HC_SUBJECTS:
        beta = hc_data[s].mean(axis=0)  # (8, n_voxels)
        hc_betas.append(beta.T)  # (n_voxels, 8)

    srm = SRM(n_iter=10, features=k)
    srm.fit(hc_betas)
    print(f"  SRM fitted. Shared response shape: {srm.s_.shape}")

    # --- Transform HC subjects (using learned W_i) ---
    hc_aligned = {}
    for i, s in enumerate(HC_SUBJECTS):
        W_i = srm.w_[i]  # (n_voxels, k)
        aligned = hc_data[s].mean(axis=0) @ W_i  # (8, k)
        hc_aligned[s] = aligned

    # --- Project CVD subjects into HC space ---
    print(f"  Projecting {len(CVD_SUBJECTS)} CVD subjects into HC-defined space...")
    cvd_aligned = {}
    for s in CVD_SUBJECTS:
        beta = cvd_data[s].mean(axis=0)  # (8, n_voxels)
        W_cvd = project_new_subject(srm, beta.T)  # (n_voxels, k)
        aligned = beta @ W_cvd  # (8, k)
        cvd_aligned[s] = aligned
        print(f"    {s}: projected to ({aligned.shape})")

    # --- Compute disparities (LOO for HC to avoid group-mean leakage) ---
    hc_aligned_arr = np.array([hc_aligned[s] for s in HC_SUBJECTS])  # (7, 8, k)
    hc_reference_full = hc_aligned_arr.mean(axis=0)  # (8, k) — for CVD only

    # HC: Leave-One-Out reference (sub-i vs mean of other 6)
    hc_disparities = {}
    for i, s in enumerate(HC_SUBJECTS):
        others = np.delete(hc_aligned_arr, i, axis=0)  # (6, 8, k)
        loo_ref = others.mean(axis=0)
        hc_disparities[s] = compute_procrustes_disparity(hc_aligned[s], loo_ref)

    # CVD: vs full HC mean (no leakage — CVD not in HC reference)
    cvd_disparities = {}
    for s in CVD_SUBJECTS:
        cvd_disparities[s] = compute_procrustes_disparity(cvd_aligned[s], hc_reference_full)

    hc_vals = np.array(list(hc_disparities.values()))
    cvd_vals = np.array(list(cvd_disparities.values()))

    print(f"\n  HC-HC disparities (LOO): {hc_vals.mean():.4f} +/- {hc_vals.std():.4f}")
    print(f"  CVD-HC disparities: {cvd_vals.mean():.4f} +/- {cvd_vals.std():.4f}")
    print(f"  Separation: {cvd_vals.mean() - hc_vals.mean():.4f}")
    print(f"  Hedges' g: {hedges_g(hc_vals, cvd_vals):.3f}")

    # --- Compute RDM correlations ---
    rdms = {}
    for s in HC_SUBJECTS:
        rdm = 1 - np.corrcoef(hc_aligned[s])
        rdms[s] = rdm
    for s in CVD_SUBJECTS:
        rdm = 1 - np.corrcoef(cvd_aligned[s])
        rdms[s] = rdm

    mask = np.triu(np.ones((8, 8), dtype=bool), k=1)
    hc_hc_rs, hc_cvd_rs, cvd_cvd_rs = [], [], []
    all_subjs = HC_SUBJECTS + CVD_SUBJECTS
    for si, sj in combinations(all_subjs, 2):
        r, _ = spearmanr(rdms[si][mask], rdms[sj][mask])
        if si in HC_SUBJECTS and sj in HC_SUBJECTS:
            hc_hc_rs.append(r)
        elif si in CVD_SUBJECTS and sj in CVD_SUBJECTS:
            cvd_cvd_rs.append(r)
        else:
            hc_cvd_rs.append(r)

    print(f"  RDM corr: HC-HC={np.mean(hc_hc_rs):.3f}, HC-CVD={np.mean(hc_cvd_rs):.3f}, CVD-CVD={np.mean(cvd_cvd_rs):.3f}")

    # --- Permutation test (label shuffle with LOO recomputation, 10000 iterations) ---
    print(f"\n  Running permutation test ({N_PERMUTATIONS} iterations, LOO-consistent)...")
    rng = np.random.RandomState(SEED)
    observed_diff = cvd_vals.mean() - hc_vals.mean()

    # All aligned patterns: [hc_0, ..., hc_6, cvd_0, cvd_1, cvd_2]
    all_aligned = np.concatenate([
        hc_aligned_arr,
        np.array([cvd_aligned[s] for s in CVD_SUBJECTS])
    ], axis=0)  # (10, 8, k)
    n_hc = len(HC_SUBJECTS)

    null_diffs = np.zeros(N_PERMUTATIONS)
    for i in range(N_PERMUTATIONS):
        perm = rng.permutation(len(all_aligned))
        pseudo_hc = all_aligned[perm[:n_hc]]   # (7, 8, k)
        pseudo_cvd = all_aligned[perm[n_hc:]]  # (3, 8, k)

        # pseudo-HC: LOO disparity
        phc_disps = []
        for j in range(n_hc):
            others = np.delete(pseudo_hc, j, axis=0)
            loo_ref = others.mean(axis=0)
            phc_disps.append(compute_procrustes_disparity(pseudo_hc[j], loo_ref))

        # pseudo-CVD: vs full pseudo-HC mean
        phc_ref = pseudo_hc.mean(axis=0)
        pcvd_disps = [compute_procrustes_disparity(pseudo_cvd[j], phc_ref)
                      for j in range(len(pseudo_cvd))]

        null_diffs[i] = np.mean(pcvd_disps) - np.mean(phc_disps)

    p_value = float(np.mean(null_diffs >= observed_diff))
    print(f"  Observed diff: {observed_diff:.4f}")
    print(f"  Permutation p-value: {p_value:.4f}")

    # --- Bootstrap CIs ---
    print(f"  Computing bootstrap CIs (10000 iterations)...")
    n_boot = 10000
    boot_hc = np.zeros(n_boot)
    boot_cvd = np.zeros(n_boot)
    boot_sep = np.zeros(n_boot)
    boot_g = np.zeros(n_boot)
    for i in range(n_boot):
        hc_b = hc_vals[rng.choice(len(hc_vals), len(hc_vals), replace=True)]
        cvd_b = cvd_vals[rng.choice(len(cvd_vals), len(cvd_vals), replace=True)]
        boot_hc[i] = hc_b.mean()
        boot_cvd[i] = cvd_b.mean()
        boot_sep[i] = cvd_b.mean() - hc_b.mean()
        boot_g[i] = hedges_g(hc_b, cvd_b)

    return {
        'roi': roi_display,
        'k': k,
        'method': 'hc_only_srm_with_cvd_projection',
        'hc_disparities': {s: float(v) for s, v in hc_disparities.items()},
        'cvd_disparities': {s: float(v) for s, v in cvd_disparities.items()},
        'summary': {
            'hc_mean': float(hc_vals.mean()),
            'hc_std': float(hc_vals.std()),
            'hc_ci': [float(np.percentile(boot_hc, 2.5)), float(np.percentile(boot_hc, 97.5))],
            'cvd_mean': float(cvd_vals.mean()),
            'cvd_std': float(cvd_vals.std()),
            'cvd_ci': [float(np.percentile(boot_cvd, 2.5)), float(np.percentile(boot_cvd, 97.5))],
            'separation': float(observed_diff),
            'separation_ci': [float(np.percentile(boot_sep, 2.5)), float(np.percentile(boot_sep, 97.5))],
            'hedges_g': float(hedges_g(hc_vals, cvd_vals)),
            'hedges_g_ci': [float(np.percentile(boot_g, 2.5)), float(np.percentile(boot_g, 97.5))],
            'permutation_p': p_value,
            'n_permutations': N_PERMUTATIONS,
        },
        'rdm_correlations': {
            'hc_hc': {'mean': float(np.mean(hc_hc_rs)), 'n': len(hc_hc_rs)},
            'hc_cvd': {'mean': float(np.mean(hc_cvd_rs)), 'n': len(hc_cvd_rs)},
            'cvd_cvd': {'mean': float(np.mean(cvd_cvd_rs)), 'n': len(cvd_cvd_rs)},
        },
        'individual_cvd': {
            s: {
                'disparity': float(cvd_disparities[s]),
                'pct_above_hc': float((cvd_disparities[s] - hc_vals.mean()) / hc_vals.mean() * 100),
                'note': 'pct_above_hc uses HC LOO mean as denominator'
            } for s in CVD_SUBJECTS
        }
    }


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='HC-Only SRM Re-Run (RT-2 Fix)')
    parser.add_argument('--roi', type=str, default=None, help='Single ROI (V1/V2/V3/V4). Omit for all.')
    args = parser.parse_args()

    rois = [args.roi] if args.roi else ROIS
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_dir = OUTPUT_DIR / timestamp
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("HC-Only SRM Re-Run (RT-2 Circularity Fix)")
    print(f"Data: {DATA_DIR}")
    print(f"Output: {out_dir}")
    print(f"ROIs: {rois}")
    print(f"k values: {K_VALUES}")
    print(f"Permutations: {N_PERMUTATIONS}")
    print("=" * 70)

    all_results = {}
    start = time.time()

    for roi in rois:
        k = K_VALUES.get(roi, 4)
        try:
            result = run_hc_only_srm(roi, k)
            all_results[ROI_DISPLAY.get(roi, roi)] = result
        except Exception as e:
            print(f"ERROR in {roi}: {e}")
            import traceback
            traceback.print_exc()

    # Save results
    out_file = out_dir / "hc_only_srm_results.json"
    with open(out_file, 'w') as f:
        json.dump({
            'config': {
                'method': 'hc_only_srm_with_cvd_projection',
                'fix': 'RT-2: SRM trained on HC only; CVD projected via SVD',
                'k_values': K_VALUES,
                'n_permutations': N_PERMUTATIONS,
                'seed': SEED,
                'timestamp': timestamp,
                'data_dir': str(DATA_DIR),
                'elapsed_sec': time.time() - start
            },
            'results': all_results
        }, f, indent=2)
    print(f"\nResults saved to {out_file}")

    # Print comparison table
    print("\n" + "=" * 70)
    print("SUMMARY: HC-Only SRM Results")
    print("=" * 70)
    header = f"{'ROI':<5} | {'HC-HC [95% CI]':<24} | {'CVD-HC [95% CI]':<24} | {'Sep [95% CI]':<24} | {'g [95% CI]':<20} | {'p':<8}"
    print(header)
    print("-" * len(header))
    for roi_d in ['V1', 'V2', 'V3', 'hV4']:
        if roi_d not in all_results:
            continue
        s = all_results[roi_d]['summary']
        print(f"{roi_d:<5} | "
              f"{s['hc_mean']:.3f} [{s['hc_ci'][0]:.3f}, {s['hc_ci'][1]:.3f}] | "
              f"{s['cvd_mean']:.3f} [{s['cvd_ci'][0]:.3f}, {s['cvd_ci'][1]:.3f}] | "
              f"{s['separation']:.3f} [{s['separation_ci'][0]:.3f}, {s['separation_ci'][1]:.3f}] | "
              f"{s['hedges_g']:.2f} [{s['hedges_g_ci'][0]:.2f}, {s['hedges_g_ci'][1]:.2f}] | "
              f"{s['permutation_p']:.4f}")

    elapsed = time.time() - start
    print(f"\nTotal time: {elapsed:.1f}s")


if __name__ == '__main__':
    main()
