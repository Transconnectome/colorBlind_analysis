#!/usr/bin/env python3
"""
Filter Pre-Validation: Per-Pair Z-Score Analysis with HC-only SRM

Computes per-pair neural distance z-scores in HC-only SRM space and validates:
  B1: Pair-level exhaustive permutation test (C(10,3)=120 group permutations)
  B2: Split-half stability (runs 1-3 vs 4-6, runs odd vs even)
  B3: Bootstrap 95% CIs (1000 resamples of HC subjects, with SRM retraining)

References canonical pipeline: rerun_loo_consistent.py
Z-score convention: positive = CVD over-separation, negative = CVD confusion

Usage:
  mpirun -np 1 python filter_pre_validation.py [--output_dir PATH]
  python filter_pre_validation.py  # if no BrainIAK / local with SimpleSRM fallback
"""

import numpy as np
import json
import sys
import time
import socket
import argparse
from pathlib import Path
from datetime import datetime
from itertools import combinations
from scipy.spatial.distance import pdist
from scipy.stats import spearmanr, pearsonr

# Try BrainIAK, fall back to pure numpy
try:
    from brainiak.funcalign.srm import SRM as BrainIAKSRM
    HAS_BRAINIAK = True
except ImportError:
    HAS_BRAINIAK = False

# ============================================================================
# CONFIG
# ============================================================================

HC_SUBJECTS = [f'sub-{i:02d}' for i in range(1, 8)]
CVD_SUBJECTS = [f'sub-{i:02d}' for i in range(8, 11)]
ALL_SUBJECTS = HC_SUBJECTS + CVD_SUBJECTS
N_HC = len(HC_SUBJECTS)
N_CVD = len(CVD_SUBJECTS)

ROIS = ['V1', 'V2', 'V3', 'V4']
ROI_DISPLAY = {'V1': 'V1', 'V2': 'V2', 'V3': 'V3', 'V4': 'hV4'}
K_VALUES = {'V1': 4, 'V2': 4, 'V3': 3, 'V4': 3}

COLOR_NAMES = ['red', 'orange', 'yellow', 'green', 'cyan', 'blue', 'purple', 'magenta']
N_COLORS = 8

# 28 unique pairs from C(8,2)
PAIR_INDICES = [(i, j) for i in range(N_COLORS) for j in range(i + 1, N_COLORS)]
PAIR_LABELS = [f"{COLOR_NAMES[i]}-{COLOR_NAMES[j]}" for i, j in PAIR_INDICES]
N_PAIRS = len(PAIR_LABELS)  # 28


def hue_step(i, j):
    """Minimum circular distance between colors on 8-color wheel."""
    d = abs(i - j)
    return min(d, N_COLORS - d)


PAIR_STEPS = [hue_step(i, j) for i, j in PAIR_INDICES]

# Adjacent pairs (step=1): key filter targets
ADJACENT_PAIRS = [p for p, s in zip(PAIR_LABELS, PAIR_STEPS) if s == 1]

N_BOOTSTRAP = 1000
SEED = 42

if socket.gethostname().startswith('node'):
    DATA_DIR = Path("/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010")
else:
    DATA_DIR = Path("/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis"
                    "/analysis/phase1_preprocess_decoding/results/full_dataset_C010")


# ============================================================================
# SIMPLE SRM (pure numpy fallback)
# ============================================================================

class SimpleSRM:
    """Deterministic SRM without BrainIAK. Matches BrainIAK API."""

    def __init__(self, features=3, n_iter=10):
        self.features = features
        self.n_iter = n_iter
        self.w_ = None
        self.s_ = None

    def fit(self, data_list):
        """
        Fit SRM. data_list: list of (n_voxels_i, n_timepoints) arrays.
        """
        k = self.features
        n_subjects = len(data_list)

        # Initialize S with SVD of first subject
        U, sigma, Vt = np.linalg.svd(data_list[0], full_matrices=False)
        s = Vt[:k]  # (k, n_timepoints)

        for _ in range(self.n_iter):
            w_list = []
            for i in range(n_subjects):
                M = data_list[i] @ s.T  # (n_voxels, k)
                Um, _, Vm = np.linalg.svd(M, full_matrices=False)
                W = Um[:, :k] @ Vm[:k, :]
                w_list.append(W)

            s = np.zeros((k, data_list[0].shape[1]))
            for i in range(n_subjects):
                s += w_list[i].T @ data_list[i]
            s /= n_subjects

        self.w_ = w_list
        self.s_ = s
        return self


def create_srm(k):
    """Create SRM model (BrainIAK if available, else SimpleSRM)."""
    if HAS_BRAINIAK:
        return BrainIAKSRM(n_iter=10, features=k)
    return SimpleSRM(features=k, n_iter=10)


# ============================================================================
# CORE FUNCTIONS
# ============================================================================

def load_subject_data(subject, roi):
    """Load (6, 8, n_voxels) amplitudes_procrustes."""
    path = DATA_DIR / subject / roi / "amplitudes_procrustes.npy"
    return np.load(path)


def project_new_subject(srm_model, new_data):
    """
    Project new subject into SRM space via SVD orthogonalization.
    new_data: (n_voxels, n_timepoints)
    Returns: W (n_voxels, k) orthonormal transformation matrix.
    """
    S = srm_model.s_  # (k, n_timepoints)
    W_init = new_data @ np.linalg.pinv(S)  # (n_voxels, k)
    U, _, Vt = np.linalg.svd(W_init, full_matrices=False)
    return U @ Vt  # (n_voxels, k)


def get_aligned_patterns(hc_data_list, cvd_data_list, k, run_indices=None):
    """
    Train HC-only SRM and get aligned (8, k) patterns for all subjects.

    Parameters
    ----------
    hc_data_list : list of (6, 8, n_voxels) arrays
    cvd_data_list : list of (6, 8, n_voxels) arrays
    k : int
    run_indices : list of int, which runs to average (default: all 6)

    Returns
    -------
    hc_aligned : list of (8, k) arrays
    cvd_aligned : list of (8, k) arrays
    """
    if run_indices is None:
        run_indices = list(range(6))

    # Average over specified runs → (8, n_voxels) per subject
    hc_betas_t = [d[run_indices].mean(axis=0).T for d in hc_data_list]  # (n_voxels, 8)
    cvd_betas = [d[run_indices].mean(axis=0) for d in cvd_data_list]    # (8, n_voxels)

    # Train HC-only SRM
    srm = create_srm(k)
    srm.fit(hc_betas_t)

    # Transform HC
    hc_aligned = [(srm.w_[i].T @ hc_betas_t[i]).T for i in range(len(hc_data_list))]

    # Project CVD via SVD
    cvd_aligned = []
    for beta in cvd_betas:
        W = project_new_subject(srm, beta.T)  # (n_voxels, k)
        cvd_aligned.append(beta @ W)           # (8, k)

    return hc_aligned, cvd_aligned


def compute_pair_distances(aligned_pattern, metric='euclidean'):
    """Compute 28 pairwise distances from (8, k) pattern."""
    return pdist(aligned_pattern, metric=metric)


def compute_pair_zscores(hc_dists, cvd_dists):
    """
    Z-scores: (CVD - HC_mean) / HC_std per pair.
    hc_dists: (n_hc, 28), cvd_dists: (n_cvd, 28).
    Returns: (n_cvd, 28).
    """
    hc_mean = hc_dists.mean(axis=0)
    hc_std = hc_dists.std(axis=0, ddof=1)
    safe_std = np.where(hc_std > 1e-12, hc_std, 1e-12)
    return (cvd_dists - hc_mean) / safe_std


def normalize_distances(pair_dists):
    """Normalize pair distances to unit mean per subject (removes global magnitude)."""
    means = pair_dists.mean(axis=1, keepdims=True)
    safe_means = np.where(means > 1e-12, means, 1e-12)
    return pair_dists / safe_means


# ============================================================================
# B1: PAIR-LEVEL EXHAUSTIVE PERMUTATION TEST
# ============================================================================

def run_B1_permutation(all_data, k):
    """
    Exhaustive permutation: enumerate all C(10,3)=120 group assignments.
    For each: retrain SRM on "HC", project "CVD" via SVD, compute z-scores.

    Returns dict with observed z-scores, null distributions, p-values.
    """
    n_total = N_HC + N_CVD

    # Observed (real group assignment)
    hc_al, cvd_al = get_aligned_patterns(all_data[:N_HC], all_data[N_HC:], k)
    hc_dists = np.array([compute_pair_distances(a) for a in hc_al])
    cvd_dists = np.array([compute_pair_distances(a) for a in cvd_al])
    obs_z = compute_pair_zscores(hc_dists, cvd_dists)        # (3, 28)
    obs_mean_z = obs_z.mean(axis=0)                           # (28,)

    # Normalized version
    all_dists = np.vstack([hc_dists, cvd_dists])
    norm_all = normalize_distances(all_dists)
    obs_norm_z = compute_pair_zscores(norm_all[:N_HC], norm_all[N_HC:])
    obs_norm_mean_z = obs_norm_z.mean(axis=0)

    # Enumerate all C(10,3) = 120 permutations
    all_perms = list(combinations(range(n_total), N_CVD))
    n_perms = len(all_perms)
    print(f"    B1: {n_perms} exhaustive permutations...")

    null_mean_z = np.zeros((n_perms, N_PAIRS))
    null_norm_mean_z = np.zeros((n_perms, N_PAIRS))
    null_individual_z = np.zeros((n_perms, N_CVD, N_PAIRS))

    for p_i, cvd_idx in enumerate(all_perms):
        if (p_i + 1) % 30 == 0:
            print(f"      perm {p_i + 1}/{n_perms}")

        hc_idx = [i for i in range(n_total) if i not in cvd_idx]

        perm_hc_data = [all_data[i] for i in hc_idx]
        perm_cvd_data = [all_data[i] for i in cvd_idx]

        try:
            p_hc_al, p_cvd_al = get_aligned_patterns(perm_hc_data, perm_cvd_data, k)
            p_hc_d = np.array([compute_pair_distances(a) for a in p_hc_al])
            p_cvd_d = np.array([compute_pair_distances(a) for a in p_cvd_al])
            p_z = compute_pair_zscores(p_hc_d, p_cvd_d)

            null_mean_z[p_i] = p_z.mean(axis=0)
            null_individual_z[p_i] = p_z

            # Normalized
            p_all_d = np.vstack([p_hc_d, p_cvd_d])
            p_norm = normalize_distances(p_all_d)
            p_norm_z = compute_pair_zscores(p_norm[:len(hc_idx)], p_norm[len(hc_idx):])
            null_norm_mean_z[p_i] = p_norm_z.mean(axis=0)
        except Exception as e:
            print(f"      Warning: perm {p_i} failed: {e}")
            null_mean_z[p_i] = 0.0
            null_norm_mean_z[p_i] = 0.0

    # P-values (two-sided)
    p_two_sided = np.array([
        np.mean(np.abs(null_mean_z[:, p]) >= np.abs(obs_mean_z[p]))
        for p in range(N_PAIRS)
    ])

    # P-values (directional): deficit (z < 0) and elevation (z > 0)
    p_deficit = np.array([
        np.mean(null_mean_z[:, p] <= obs_mean_z[p]) if obs_mean_z[p] < 0
        else np.mean(null_mean_z[:, p] >= obs_mean_z[p])
        for p in range(N_PAIRS)
    ])

    # Normalized p-values
    p_norm_two = np.array([
        np.mean(np.abs(null_norm_mean_z[:, p]) >= np.abs(obs_norm_mean_z[p]))
        for p in range(N_PAIRS)
    ])

    return {
        'n_permutations': n_perms,
        'observed_individual_z': {
            CVD_SUBJECTS[j]: obs_z[j].tolist() for j in range(N_CVD)
        },
        'observed_group_mean_z': obs_mean_z.tolist(),
        'observed_norm_group_mean_z': obs_norm_mean_z.tolist(),
        'p_two_sided': p_two_sided.tolist(),
        'p_directional': p_deficit.tolist(),
        'p_norm_two_sided': p_norm_two.tolist(),
        'null_mean_z_mean': null_mean_z.mean(axis=0).tolist(),
        'null_mean_z_std': null_mean_z.std(axis=0).tolist(),
        'significant_raw': [PAIR_LABELS[p] for p in range(N_PAIRS) if p_two_sided[p] < 0.05],
        'significant_norm': [PAIR_LABELS[p] for p in range(N_PAIRS) if p_norm_two[p] < 0.05],
        'hc_pair_distances': {
            HC_SUBJECTS[i]: hc_dists[i].tolist() for i in range(N_HC)
        },
        'cvd_pair_distances': {
            CVD_SUBJECTS[j]: cvd_dists[j].tolist() for j in range(N_CVD)
        },
    }


# ============================================================================
# B2: SPLIT-HALF STABILITY
# ============================================================================

def run_B2_split_half(hc_data, cvd_data, k):
    """
    Split 6 runs into halves, train independent SRMs, compute z-scores.
    Correlate z-score profiles between halves.

    Two splits:
      - First/Last: runs 0-2 vs 3-5
      - Odd/Even: runs 0,2,4 vs 1,3,5
    """
    splits = {
        'first_last': ([0, 1, 2], [3, 4, 5]),
        'odd_even':   ([0, 2, 4], [1, 3, 5]),
    }

    results = {}
    for split_name, (half1_runs, half2_runs) in splits.items():
        print(f"    B2 split '{split_name}': runs {half1_runs} vs {half2_runs}")

        # Train independent SRMs on each half
        hc_al_1, cvd_al_1 = get_aligned_patterns(hc_data, cvd_data, k, half1_runs)
        hc_al_2, cvd_al_2 = get_aligned_patterns(hc_data, cvd_data, k, half2_runs)

        # Per-pair distances
        hc_d1 = np.array([compute_pair_distances(a) for a in hc_al_1])
        cvd_d1 = np.array([compute_pair_distances(a) for a in cvd_al_1])
        hc_d2 = np.array([compute_pair_distances(a) for a in hc_al_2])
        cvd_d2 = np.array([compute_pair_distances(a) for a in cvd_al_2])

        # Z-scores per half
        z_half1 = compute_pair_zscores(hc_d1, cvd_d1)  # (3, 28)
        z_half2 = compute_pair_zscores(hc_d2, cvd_d2)  # (3, 28)

        # Correlate z-score profiles between halves for each CVD subject
        split_result = {
            'half1_zscores': {CVD_SUBJECTS[j]: z_half1[j].tolist() for j in range(N_CVD)},
            'half2_zscores': {CVD_SUBJECTS[j]: z_half2[j].tolist() for j in range(N_CVD)},
            'per_subject_correlation': {},
        }

        for j in range(N_CVD):
            r_s, p_s = spearmanr(z_half1[j], z_half2[j])
            r_p, p_p = pearsonr(z_half1[j], z_half2[j])
            split_result['per_subject_correlation'][CVD_SUBJECTS[j]] = {
                'spearman_r': float(r_s) if np.isfinite(r_s) else None,
                'spearman_p': float(p_s) if np.isfinite(p_s) else None,
                'pearson_r': float(r_p) if np.isfinite(r_p) else None,
                'pearson_p': float(p_p) if np.isfinite(p_p) else None,
            }
            print(f"      {CVD_SUBJECTS[j]}: Spearman r={r_s:.3f} (p={p_s:.4f}), "
                  f"Pearson r={r_p:.3f} (p={p_p:.4f})")

        # Group-level stability: correlate group-mean z-scores between halves
        group_z1 = z_half1.mean(axis=0)
        group_z2 = z_half2.mean(axis=0)
        r_grp_s, p_grp_s = spearmanr(group_z1, group_z2)
        r_grp_p, p_grp_p = pearsonr(group_z1, group_z2)
        split_result['group_correlation'] = {
            'spearman_r': float(r_grp_s) if np.isfinite(r_grp_s) else None,
            'spearman_p': float(p_grp_s) if np.isfinite(p_grp_s) else None,
            'pearson_r': float(r_grp_p) if np.isfinite(r_grp_p) else None,
            'pearson_p': float(p_grp_p) if np.isfinite(p_grp_p) else None,
        }
        print(f"      Group: Spearman r={r_grp_s:.3f}, Pearson r={r_grp_p:.3f}")

        results[split_name] = split_result

    return results


# ============================================================================
# B3: BOOTSTRAP 95% CIs
# ============================================================================

def run_B3_bootstrap(hc_data, cvd_data, k, n_bootstrap=N_BOOTSTRAP):
    """
    Resample HC subjects with replacement, retrain SRM, recompute z-scores.
    Reports 95% CIs for each pair's z-score per CVD subject.
    """
    rng = np.random.RandomState(SEED)

    boot_z = np.zeros((n_bootstrap, N_CVD, N_PAIRS))
    boot_norm_z = np.zeros((n_bootstrap, N_CVD, N_PAIRS))

    print(f"    B3: {n_bootstrap} bootstrap iterations (with SRM retraining)...")

    for b in range(n_bootstrap):
        if (b + 1) % 100 == 0:
            print(f"      bootstrap {b + 1}/{n_bootstrap}")

        # Resample HC subjects with replacement
        idx = rng.choice(N_HC, size=N_HC, replace=True)
        boot_hc = [hc_data[i] for i in idx]

        try:
            b_hc_al, b_cvd_al = get_aligned_patterns(boot_hc, cvd_data, k)
            b_hc_d = np.array([compute_pair_distances(a) for a in b_hc_al])
            b_cvd_d = np.array([compute_pair_distances(a) for a in b_cvd_al])

            boot_z[b] = compute_pair_zscores(b_hc_d, b_cvd_d)

            # Normalized
            b_all_d = np.vstack([b_hc_d, b_cvd_d])
            b_norm = normalize_distances(b_all_d)
            boot_norm_z[b] = compute_pair_zscores(b_norm[:N_HC], b_norm[N_HC:])
        except Exception as e:
            print(f"      Warning: bootstrap {b} failed: {e}")
            boot_z[b] = np.nan
            boot_norm_z[b] = np.nan

    # Remove any nan iterations
    valid = ~np.any(np.isnan(boot_z.reshape(n_bootstrap, -1)), axis=1)
    boot_z_valid = boot_z[valid]
    boot_norm_z_valid = boot_norm_z[valid]
    n_valid = valid.sum()
    print(f"      {n_valid}/{n_bootstrap} valid bootstrap iterations")

    # Compute CIs
    ci_lower = np.percentile(boot_z_valid, 2.5, axis=0)    # (3, 28)
    ci_upper = np.percentile(boot_z_valid, 97.5, axis=0)
    boot_mean = boot_z_valid.mean(axis=0)
    boot_std = boot_z_valid.std(axis=0)

    ci_norm_lower = np.percentile(boot_norm_z_valid, 2.5, axis=0)
    ci_norm_upper = np.percentile(boot_norm_z_valid, 97.5, axis=0)

    # Identify pairs where CI excludes zero (significant at 95%)
    results = {
        'n_bootstrap': n_bootstrap,
        'n_valid': int(n_valid),
        'per_subject': {},
    }

    for j in range(N_CVD):
        subj = CVD_SUBJECTS[j]
        sig_pairs = []
        for p in range(N_PAIRS):
            if ci_lower[j, p] > 0 or ci_upper[j, p] < 0:
                sig_pairs.append(PAIR_LABELS[p])

        results['per_subject'][subj] = {
            'z_mean': boot_mean[j].tolist(),
            'z_std': boot_std[j].tolist(),
            'ci_lower': ci_lower[j].tolist(),
            'ci_upper': ci_upper[j].tolist(),
            'ci_norm_lower': ci_norm_lower[j].tolist(),
            'ci_norm_upper': ci_norm_upper[j].tolist(),
            'significant_pairs': sig_pairs,
            'n_significant': len(sig_pairs),
        }
        print(f"      {subj}: {len(sig_pairs)}/{N_PAIRS} pairs with CI excluding zero")

    return results


# ============================================================================
# SUMMARY STATISTICS
# ============================================================================

def compute_summary(b1_results, b2_results, b3_results, roi_display):
    """Generate concise summary for this ROI."""
    summary = {
        'roi': roi_display,
        'B1_permutation': {
            'n_significant_raw': len(b1_results['significant_raw']),
            'n_significant_norm': len(b1_results['significant_norm']),
            'significant_raw_pairs': b1_results['significant_raw'],
            'significant_norm_pairs': b1_results['significant_norm'],
        },
        'B2_split_half': {},
        'B3_bootstrap': {},
    }

    # B2: average stability
    for split_name, split_data in b2_results.items():
        cors = [v['spearman_r'] for v in split_data['per_subject_correlation'].values()
                if v['spearman_r'] is not None]
        summary['B2_split_half'][split_name] = {
            'mean_spearman_r': float(np.mean(cors)) if cors else None,
            'group_spearman_r': split_data['group_correlation']['spearman_r'],
        }

    # B3: total significant pairs
    for subj in CVD_SUBJECTS:
        summary['B3_bootstrap'][subj] = b3_results['per_subject'][subj]['n_significant']

    return summary


# ============================================================================
# CROSS-SUBJECT CONSISTENCY ANALYSIS
# ============================================================================

def compute_cross_subject_consistency(b1_results):
    """
    Identify pairs where all 3 CVD subjects agree on direction (sign of z).
    Also identify deutan-specific and protan-specific patterns.
    """
    z_scores = np.array([b1_results['observed_individual_z'][s] for s in CVD_SUBJECTS])
    # z_scores: (3, 28)

    consistent = {
        'all_3_deficit': [],     # All 3 CVD have z < 0
        'all_3_elevation': [],   # All 3 CVD have z > 0
        'deutan_deficit': [],    # sub-08 + sub-10 (deutan) have z < 0
        'deutan_elevation': [],
        'protan_specific': [],   # sub-09 deviates from deutan pattern
    }

    for p in range(N_PAIRS):
        z_08, z_09, z_10 = z_scores[0, p], z_scores[1, p], z_scores[2, p]

        if z_08 < 0 and z_09 < 0 and z_10 < 0:
            consistent['all_3_deficit'].append({
                'pair': PAIR_LABELS[p], 'step': PAIR_STEPS[p],
                'z_sub08': round(z_08, 2), 'z_sub09': round(z_09, 2), 'z_sub10': round(z_10, 2),
            })
        elif z_08 > 0 and z_09 > 0 and z_10 > 0:
            consistent['all_3_elevation'].append({
                'pair': PAIR_LABELS[p], 'step': PAIR_STEPS[p],
                'z_sub08': round(z_08, 2), 'z_sub09': round(z_09, 2), 'z_sub10': round(z_10, 2),
            })

        # Deutan-specific (sub-08 + sub-10 agree, sub-09 may differ)
        if z_08 < -1.0 and z_10 < -1.0:
            consistent['deutan_deficit'].append({
                'pair': PAIR_LABELS[p], 'step': PAIR_STEPS[p],
                'z_sub08': round(z_08, 2), 'z_sub10': round(z_10, 2), 'z_sub09': round(z_09, 2),
            })
        if z_08 > 1.0 and z_10 > 1.0:
            consistent['deutan_elevation'].append({
                'pair': PAIR_LABELS[p], 'step': PAIR_STEPS[p],
                'z_sub08': round(z_08, 2), 'z_sub10': round(z_10, 2), 'z_sub09': round(z_09, 2),
            })

        # Protan-specific: sub-09 has |z| > 1.0 but deutan pair is not extreme
        if abs(z_09) > 1.5 and abs(z_08) < 1.0 and abs(z_10) < 1.0:
            consistent['protan_specific'].append({
                'pair': PAIR_LABELS[p], 'step': PAIR_STEPS[p],
                'z_sub09': round(z_09, 2), 'z_sub08': round(z_08, 2), 'z_sub10': round(z_10, 2),
            })

    return consistent


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Filter Pre-Validation: Per-Pair Z-Score Analysis')
    parser.add_argument('--output_dir', type=str, default=None,
                        help='Output directory (default: auto)')
    args = parser.parse_args()

    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = Path(__file__).resolve().parent / "results"

    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("Filter Pre-Validation: Per-Pair Z-Score Analysis (B1-B3)")
    print("=" * 70)
    print(f"  BrainIAK: {'available' if HAS_BRAINIAK else 'using SimpleSRM fallback'}")
    print(f"  Data dir: {DATA_DIR}")
    print(f"  Output:   {output_dir}")
    print(f"  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    t_start = time.time()
    all_results = {
        'config': {
            'method': 'filter_pre_validation_B1_B2_B3',
            'srm_backend': 'brainiak' if HAS_BRAINIAK else 'simple_srm',
            'k_values': K_VALUES,
            'n_bootstrap': N_BOOTSTRAP,
            'n_permutations_exhaustive': 120,
            'seed': SEED,
            'timestamp': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'pair_labels': PAIR_LABELS,
            'pair_steps': PAIR_STEPS,
            'color_names': COLOR_NAMES,
            'hc_subjects': HC_SUBJECTS,
            'cvd_subjects': CVD_SUBJECTS,
        },
        'results': {},
    }

    for roi in ROIS:
        roi_display = ROI_DISPLAY[roi]
        k = K_VALUES[roi]

        print(f"\n{'=' * 70}")
        print(f"ROI: {roi_display} (k={k})")
        print(f"{'=' * 70}")

        # Load data
        hc_data = [load_subject_data(s, roi) for s in HC_SUBJECTS]
        cvd_data = [load_subject_data(s, roi) for s in CVD_SUBJECTS]
        all_data = hc_data + cvd_data

        for i, s in enumerate(HC_SUBJECTS):
            print(f"  {s}: {hc_data[i].shape}")
        for i, s in enumerate(CVD_SUBJECTS):
            print(f"  {s}: {cvd_data[i].shape}")

        t_roi = time.time()

        # --- B1: Pair-level permutation test ---
        print(f"\n  [B1] Pair-level exhaustive permutation test")
        b1 = run_B1_permutation(all_data, k)

        # --- B2: Split-half stability ---
        print(f"\n  [B2] Split-half stability")
        b2 = run_B2_split_half(hc_data, cvd_data, k)

        # --- B3: Bootstrap CIs ---
        print(f"\n  [B3] Bootstrap 95% CIs")
        b3 = run_B3_bootstrap(hc_data, cvd_data, k, n_bootstrap=N_BOOTSTRAP)

        # Cross-subject consistency
        consistency = compute_cross_subject_consistency(b1)

        # Summary
        summary = compute_summary(b1, b2, b3, roi_display)

        elapsed_roi = time.time() - t_roi
        print(f"\n  {roi_display} completed in {elapsed_roi:.1f}s")

        all_results['results'][roi_display] = {
            'roi': roi_display,
            'k': k,
            'B1_permutation': b1,
            'B2_split_half': b2,
            'B3_bootstrap': b3,
            'cross_subject_consistency': consistency,
            'summary': summary,
            'elapsed_sec': round(elapsed_roi, 1),
        }

    total_elapsed = time.time() - t_start
    all_results['config']['total_elapsed_sec'] = round(total_elapsed, 1)

    # Print overall summary
    print(f"\n{'=' * 70}")
    print(f"OVERALL SUMMARY")
    print(f"{'=' * 70}")
    for roi in ROIS:
        roi_d = ROI_DISPLAY[roi]
        s = all_results['results'][roi_d]['summary']
        print(f"\n  {roi_d}:")
        print(f"    B1 significant pairs (raw/norm): "
              f"{s['B1_permutation']['n_significant_raw']}/{s['B1_permutation']['n_significant_norm']}")
        for split_name, sv in s['B2_split_half'].items():
            r_val = sv['mean_spearman_r']
            r_str = f"{r_val:.3f}" if r_val is not None else "N/A"
            print(f"    B2 {split_name} mean Spearman r: {r_str}")
        for subj in CVD_SUBJECTS:
            n_sig = s['B3_bootstrap'][subj]
            print(f"    B3 {subj}: {n_sig}/28 pairs with CI excl. zero")

    print(f"\n  Total elapsed: {total_elapsed:.1f}s")

    # Save results
    out_path = output_dir / "filter_pre_validation_results.json"
    with open(out_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f"\n  Results saved to: {out_path}")


if __name__ == '__main__':
    main()
