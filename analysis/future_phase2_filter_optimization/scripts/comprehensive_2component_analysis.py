#!/usr/bin/env python3
"""
comprehensive_2component_analysis.py — Full 2-Component Angular Dilation analysis.

Tasks:
  (1) Metric comparison: correlation vs crossnobis ΔRDM + cosine vs WUC
  (2) 2-Component model grid search with all metric combinations
  (3) 8! Permutation tests for each
  (4) Joint V1+V2 fitting
  (5) Cone-shift + 2-component hybrid model
  (6) Bootstrap CI (HC resampling)
  (7) Color visualization (swatches + wheel)
  (8) Machado CVD simulator filter validation

Usage:
    conda activate srm
    python scripts/comprehensive_2component_analysis.py \
        --subjects 08 09 --output_dir results/2component_comprehensive
"""

import argparse
import json
import sys
import itertools
from pathlib import Path
from datetime import datetime

import numpy as np
from scipy.stats import spearmanr
from scipy.spatial.distance import pdist
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR))

_FWD_DIR = str(_SCRIPT_DIR.parent.parent.parent / 'future_phase1_forward_model' / 'scripts')
sys.path.insert(0, _FWD_DIR)

from utils_forward_model import (
    HC_SUBJECTS, N_CHANNELS, N_RUNS, N_COLORS, HUE_ANGLES,
    load_amplitudes, create_basis_matrix, create_basis_full,
    gcv_select_alpha, fit_W_ridge,
)
from machado_simulator import machado_shifted_hue
from diagnostic_delta_rdm import (
    compute_rdm_correlation, compute_rdm_crossnobis,
    estimate_noise_cov, compute_rdm_crossnobis_predicted,
    compute_delta_rdm_obs, compute_delta_rdm_sim,
    cosine_similarity, signed_agreement_rate, PAIR_LABELS, COLOR_NAMES,
)
from visualize_cone_shift_colors import (
    lab2rgb, get_stim_rgb, shift_stim_hue,
    STIM_LAB_ARR, STIM_L, STIM_A, STIM_B, STIM_CHROMA,
    HUE_ANGLES_DEG,
)

LOCAL_BASELINE = _SCRIPT_DIR.parent.parent.parent \
    / 'phase1_procrustes_decoding' / 'results' / 'visualization' \
    / 'full_dataset_C010_with_residuals'
STEP0_DIR = _SCRIPT_DIR.parent / 'results' / 'step0_precompute'

CVD_TYPE = {'08': 'deutan', '09': 'protan', '10': 'normal'}
CONF_AXIS = {'protan': 16.0, 'deutan': 150.0, 'normal': 83.0}  # Stockman coordinates
# 'normal' = midpoint between protan/deutan axes (arbitrary for specificity check)

# =============================================================================
# 2-Component Angular Dilation Model
# =============================================================================

def two_component_delta_theta(beta_s, beta_c, cvd_type):
    """Compute per-color hue shifts for 2-component model.

    θ'(c) = θ_base(c) + β_s·cos(θ_base(c) − 90°) + β_c·cos(θ_base(c) − θ_conf)

    Returns: (8,) delta_theta in degrees
    """
    # P1 consolidation 2026-05-10: delegate to forward_models.two_component
    from forward_models.two_component import dt_2comp_8colors
    hue_base, _, _ = machado_shifted_hue(0.0, cvd_type)
    dt = dt_2comp_8colors(cvd_type, beta_s, beta_c)
    return dt, hue_base


def two_component_design_matrix(beta_s, beta_c, cvd_type,
                                 n_channels=N_CHANNELS, basis_type='fe'):
    """Build C_warped for 2-component model."""
    dt, hue_base = two_component_delta_theta(beta_s, beta_c, cvd_type)
    hue_shifted = (hue_base + dt) % 360.0
    basis_full = create_basis_full(n_channels, basis_type=basis_type)
    idx = np.round(hue_shifted).astype(int) % 360
    return basis_full[idx]


def cone_shift_two_component_delta_theta(delta_lambda, beta_s, beta_c, cvd_type):
    """Cone-shift + 2-component hybrid.

    θ'(c) = θ_cone(c; Δλ) + β_s·cos(θ_cone(c) − 90°) + β_c·cos(θ_cone(c) − θ_conf)
    """
    hue_base, hue_cone, _ = machado_shifted_hue(delta_lambda, cvd_type)
    theta_conf = CONF_AXIS[cvd_type]
    dt = (beta_s * np.cos(np.radians(hue_cone - 90.0))
          + beta_c * np.cos(np.radians(hue_cone - theta_conf)))
    total_dt = (hue_cone - hue_base) + dt
    return total_dt, hue_base, hue_cone


def cone_shift_two_component_design_matrix(delta_lambda, beta_s, beta_c, cvd_type,
                                            n_channels=N_CHANNELS):
    """Build C_warped for cone-shift + 2-component hybrid."""
    dt, hue_base, hue_cone = cone_shift_two_component_delta_theta(
        delta_lambda, beta_s, beta_c, cvd_type)
    hue_final = (hue_base + dt) % 360.0
    basis_full = create_basis_full(n_channels)
    idx = np.round(hue_final).astype(int) % 360
    return basis_full[idx]


# =============================================================================
# WUC (Whitened Unbiased Cosine)
# =============================================================================

def estimate_rdm_covariance(rdm_per_hc):
    """Estimate covariance of ΔRDM entries across HC subjects.

    Args:
        rdm_per_hc: (n_hc, 28) matrix of per-HC RDM vectors

    Returns:
        cov: (28, 28) covariance matrix (regularized)
    """
    n_hc = rdm_per_hc.shape[0]
    if n_hc < 3:
        return np.eye(28)
    cov = np.cov(rdm_per_hc, rowvar=False)
    # Shrinkage regularization
    trace_mean = np.trace(cov) / 28
    shrinkage = 0.2
    cov_reg = (1 - shrinkage) * cov + shrinkage * trace_mean * np.eye(28)
    return cov_reg


def precompute_W_half(cov):
    """Precompute whitening matrix from covariance (for repeated WUC calls)."""
    try:
        eigvals, eigvecs = np.linalg.eigh(cov)
        keep = eigvals > eigvals.max() * 1e-6
        return eigvecs[:, keep] @ np.diag(1.0 / np.sqrt(eigvals[keep]))
    except np.linalg.LinAlgError:
        return np.eye(cov.shape[0])


def wuc_similarity(a, b, cov=None, W_half=None):
    """Whitened Unbiased Cosine similarity (Diedrichsen et al. 2020).

    WUC = cosine(Σ^{-1/2} a, Σ^{-1/2} b)
    Pass precomputed W_half for speed in loops.
    """
    if W_half is None:
        if cov is None:
            return cosine_similarity(a, b)
        W_half = precompute_W_half(cov)
    a_w = a @ W_half
    b_w = b @ W_half
    return cosine_similarity(a_w, b_w)


# =============================================================================
# Fast crossnobis helpers (precompute L_inv once)
# =============================================================================

def precompute_L_inv(hc_amps_dict):
    """Precompute whitening matrices for crossnobis, avoiding repeated Cholesky."""
    L_inv_dict = {}
    for subj, amps in hc_amps_dict.items():
        sigma_reg = estimate_noise_cov(amps)
        try:
            L = np.linalg.cholesky(sigma_reg)
            L_inv_dict[subj] = np.linalg.solve(L, np.eye(sigma_reg.shape[0]))
        except np.linalg.LinAlgError:
            eigvals, eigvecs = np.linalg.eigh(sigma_reg)
            keep = eigvals > eigvals.max() * 1e-6
            L_inv_dict[subj] = eigvecs[:, keep] @ np.diag(
                1.0 / np.sqrt(eigvals[keep]))
    return L_inv_dict


def compute_delta_rdm_sim_fast(hc_W_dict, C_shifted, C_baseline,
                                L_inv_dict=None, distance='correlation'):
    """Fast ΔRDM sim with precomputed L_inv for crossnobis."""
    delta_rdm_per_hc = {}
    for subj, W in hc_W_dict.items():
        Y_shifted = C_shifted @ W
        Y_baseline = C_baseline @ W
        if distance == 'correlation':
            rdm_shifted = compute_rdm_correlation(Y_shifted)
            rdm_baseline = compute_rdm_correlation(Y_baseline)
        else:
            L_inv = L_inv_dict[subj]
            rdm_shifted = compute_rdm_crossnobis_predicted(Y_shifted, L_inv)
            rdm_baseline = compute_rdm_crossnobis_predicted(Y_baseline, L_inv)
        delta_rdm_per_hc[subj] = rdm_shifted - rdm_baseline
    delta_rdm_mean = np.mean(list(delta_rdm_per_hc.values()), axis=0)
    return delta_rdm_mean, delta_rdm_per_hc


# =============================================================================
# Data loading
# =============================================================================

def load_precomputed_W(roi):
    """Load precomputed HC weights from step0."""
    data = np.load(STEP0_DIR / f'hc_W_{roi}.npz', allow_pickle=True)
    subj_ids = list(data['subj_ids'])
    W_dict = {s: data[f'W_{s}'] for s in subj_ids}
    return W_dict


def load_precomputed_delta_rdm_obs(roi, cvd_subj):
    """Load precomputed observed ΔRDM from step0."""
    data = np.load(STEP0_DIR / f'delta_rdm_obs_{roi}.npz')
    return data[f'delta_rdm_{cvd_subj}']


def load_all_amplitudes(roi):
    """Load amplitudes for all subjects."""
    hc_amps = {}
    for s in HC_SUBJECTS:
        hc_amps[s] = load_amplitudes(str(LOCAL_BASELINE), s, roi)
    return hc_amps


# =============================================================================
# Grid search
# =============================================================================

def grid_search_2component(cvd_subj, roi, hc_W_dict, delta_rdm_obs,
                            cvd_type, C_baseline,
                            beta_s_range=None, beta_c_range=None,
                            hc_amps_dict=None, distance='correlation',
                            rdm_cov=None, L_inv_dict=None):
    """Grid search for 2-component model.

    Returns: dict with best params, full landscape, permutation results
    """
    if beta_s_range is None:
        beta_s_range = np.arange(0, 51, 1.0)
    if beta_c_range is None:
        beta_c_range = np.arange(-50, 51, 1.0)

    # Precompute L_inv for crossnobis if not provided
    if distance == 'crossnobis' and L_inv_dict is None and hc_amps_dict is not None:
        L_inv_dict = precompute_L_inv(hc_amps_dict)

    best_cos = -2.0
    best_wuc = -2.0
    best_params_cos = (0, 0)
    best_params_wuc = (0, 0)
    landscape = []

    # Precompute whitening matrix for WUC (avoid repeated eigendecomp)
    W_half = precompute_W_half(rdm_cov) if rdm_cov is not None else None

    for bs in beta_s_range:
        for bc in beta_c_range:
            C_shifted = two_component_design_matrix(bs, bc, cvd_type)
            drdm_sim, _ = compute_delta_rdm_sim_fast(
                hc_W_dict, C_shifted, C_baseline,
                L_inv_dict=L_inv_dict, distance=distance)

            cos_val = cosine_similarity(drdm_sim, delta_rdm_obs)
            sign_rate, _ = signed_agreement_rate(drdm_sim, delta_rdm_obs)

            wuc_val = cos_val  # default
            if W_half is not None:
                wuc_val = wuc_similarity(drdm_sim, delta_rdm_obs, W_half=W_half)

            entry = {
                'beta_s': float(bs), 'beta_c': float(bc),
                'cosine': float(cos_val), 'wuc': float(wuc_val),
                'sign_rate': float(sign_rate),
            }
            landscape.append(entry)

            if cos_val > best_cos:
                best_cos = cos_val
                best_params_cos = (bs, bc)
            if wuc_val > best_wuc:
                best_wuc = wuc_val
                best_params_wuc = (bs, bc)

    return {
        'best_cosine': {'beta_s': float(best_params_cos[0]),
                        'beta_c': float(best_params_cos[1]),
                        'value': float(best_cos)},
        'best_wuc': {'beta_s': float(best_params_wuc[0]),
                     'beta_c': float(best_params_wuc[1]),
                     'value': float(best_wuc)},
        'landscape_shape': [len(beta_s_range), len(beta_c_range)],
        'landscape': landscape,
    }


def permutation_test_8factorial(delta_rdm_sim, delta_rdm_obs, rdm_cov=None):
    """Exact 8! label permutation test.

    Returns: cosine p-value, wuc p-value, null distributions
    """
    # Precompute whitening matrix once
    W_half = precompute_W_half(rdm_cov) if rdm_cov is not None else None

    observed_cos = cosine_similarity(delta_rdm_sim, delta_rdm_obs)
    observed_wuc = observed_cos
    if W_half is not None:
        observed_wuc = wuc_similarity(delta_rdm_sim, delta_rdm_obs, W_half=W_half)

    null_cos = []
    null_wuc = []
    n_colors = 8
    count = 0

    # Precompute all permutation index maps
    for perm in itertools.permutations(range(n_colors)):
        perm = list(perm)
        perm_idx = []
        for i in range(n_colors):
            for j in range(i + 1, n_colors):
                pi, pj = sorted([perm[i], perm[j]])
                flat_idx = sum(n_colors - 1 - k for k in range(pi)) + (pj - pi - 1)
                perm_idx.append(flat_idx)
        obs_perm = delta_rdm_obs[perm_idx]

        cos_val = cosine_similarity(delta_rdm_sim, obs_perm)
        null_cos.append(cos_val)

        if W_half is not None:
            wuc_val = wuc_similarity(delta_rdm_sim, obs_perm, W_half=W_half)
            null_wuc.append(wuc_val)

        count += 1

    null_cos = np.array(null_cos)
    perm_p_cos = float(np.mean(null_cos >= observed_cos))

    perm_p_wuc = perm_p_cos
    if W_half is not None:
        null_wuc = np.array(null_wuc)
        perm_p_wuc = float(np.mean(null_wuc >= observed_wuc))

    return {
        'observed_cosine': float(observed_cos),
        'observed_wuc': float(observed_wuc),
        'perm_p_cosine': perm_p_cos,
        'perm_p_wuc': perm_p_wuc,
        'null_cos_mean': float(null_cos.mean()),
        'null_cos_std': float(null_cos.std()),
        'n_permutations': count,
    }


def maxstat_permutation_test(drdm_sim_matrix, drdm_obs, n_colors=8):
    """Max-statistic permutation test (corrects for parameter optimization).

    For each 8! label permutation, re-optimizes over all grid points.
    This properly controls for the circularity of optimizing β_s, β_c
    on the same data used for testing.

    Args:
        drdm_sim_matrix: (N_grid, 28) precomputed ΔRDM_sim for all grid points
        drdm_obs: (28,) observed ΔRDM
        n_colors: number of colors (default 8)

    Returns:
        dict with observed_max_cos, perm_p, null distribution stats
    """
    # Precompute norms
    norms_sim = np.linalg.norm(drdm_sim_matrix, axis=1)
    valid = norms_sim > 1e-12
    norms_sim_safe = norms_sim.copy()
    norms_sim_safe[~valid] = 1.0  # avoid division by zero

    # Observed maximum cosine
    norm_obs = np.linalg.norm(drdm_obs)
    if norm_obs < 1e-12:
        return {'observed_max_cos': 0.0, 'maxstat_perm_p': 1.0,
                'n_permutations': 0}
    cos_all = (drdm_sim_matrix @ drdm_obs) / (norms_sim_safe * norm_obs)
    cos_all[~valid] = 0.0
    observed_max = float(np.max(cos_all))

    # Precompute all 8! permutation index maps
    perm_maps = []
    for perm in itertools.permutations(range(n_colors)):
        perm = list(perm)
        perm_idx = []
        for i in range(n_colors):
            for j in range(i + 1, n_colors):
                pi, pj = sorted([perm[i], perm[j]])
                flat_idx = sum(n_colors - 1 - k for k in range(pi)) + (pj - pi - 1)
                perm_idx.append(flat_idx)
        perm_maps.append(perm_idx)

    # For each permutation, compute max cosine over all grid points
    null_max = np.empty(len(perm_maps))
    for k, perm_idx in enumerate(perm_maps):
        obs_perm = drdm_obs[perm_idx]
        norm_perm = np.linalg.norm(obs_perm)  # same as norm_obs for permutation
        cos_perm = (drdm_sim_matrix @ obs_perm) / (norms_sim_safe * norm_perm)
        cos_perm[~valid] = 0.0
        null_max[k] = np.max(cos_perm)

    perm_p = float(np.mean(null_max >= observed_max))

    return {
        'observed_max_cos': observed_max,
        'maxstat_perm_p': perm_p,
        'null_max_mean': float(null_max.mean()),
        'null_max_std': float(null_max.std()),
        'null_max_95': float(np.percentile(null_max, 95)),
        'n_permutations': len(perm_maps),
    }


# =============================================================================
# Joint V1+V2 fitting
# =============================================================================

def joint_v1v2_grid_search(cvd_subj, cvd_type, C_baseline,
                            hc_W_V1, hc_W_V2,
                            drdm_obs_V1, drdm_obs_V2,
                            beta_s_range=None, beta_c_range=None):
    """Joint V1+V2 fitting with shared β_s, β_c."""
    if beta_s_range is None:
        beta_s_range = np.arange(0, 51, 1.0)
    if beta_c_range is None:
        beta_c_range = np.arange(-50, 51, 1.0)

    best_joint = -2.0
    best_params = (0, 0)

    for bs in beta_s_range:
        for bc in beta_c_range:
            C_shifted = two_component_design_matrix(bs, bc, cvd_type)

            drdm_sim_V1, _ = compute_delta_rdm_sim(hc_W_V1, C_shifted, C_baseline)
            drdm_sim_V2, _ = compute_delta_rdm_sim(hc_W_V2, C_shifted, C_baseline)

            cos_V1 = cosine_similarity(drdm_sim_V1, drdm_obs_V1)
            cos_V2 = cosine_similarity(drdm_sim_V2, drdm_obs_V2)
            joint = 0.5 * cos_V1 + 0.5 * cos_V2

            if joint > best_joint:
                best_joint = joint
                best_params = (bs, bc)
                best_cos_V1 = cos_V1
                best_cos_V2 = cos_V2

    return {
        'beta_s': float(best_params[0]),
        'beta_c': float(best_params[1]),
        'joint_cosine': float(best_joint),
        'cosine_V1': float(best_cos_V1),
        'cosine_V2': float(best_cos_V2),
    }


# =============================================================================
# Cone-shift + 2-component hybrid
# =============================================================================

def hybrid_grid_search(cvd_subj, cvd_type, hc_W_dict, delta_rdm_obs,
                        C_baseline,
                        dl_range=None, beta_s_range=None, beta_c_range=None):
    """Grid search for cone-shift + 2-component hybrid."""
    if dl_range is None:
        dl_range = np.arange(0, 21, 2.0)
    if beta_s_range is None:
        beta_s_range = np.arange(0, 51, 3.0)
    if beta_c_range is None:
        beta_c_range = np.arange(-50, 51, 3.0)

    best_cos = -2.0
    best_params = (0, 0, 0)

    for dl in dl_range:
        for bs in beta_s_range:
            for bc in beta_c_range:
                C_shifted = cone_shift_two_component_design_matrix(
                    dl, bs, bc, cvd_type)
                drdm_sim, _ = compute_delta_rdm_sim(
                    hc_W_dict, C_shifted, C_baseline)
                cos_val = cosine_similarity(drdm_sim, delta_rdm_obs)

                if cos_val > best_cos:
                    best_cos = cos_val
                    best_params = (dl, bs, bc)

    return {
        'delta_lambda': float(best_params[0]),
        'beta_s': float(best_params[1]),
        'beta_c': float(best_params[2]),
        'cosine': float(best_cos),
    }


# =============================================================================
# Bootstrap CI
# =============================================================================

def bootstrap_ci(cvd_subj, cvd_type, roi, C_baseline,
                  hc_amps_dict, delta_rdm_obs,
                  n_boot=1000, seed=42):
    """Bootstrap HC subjects to get CI for β_s, β_c."""
    rng = np.random.RandomState(seed)
    hc_subjs = list(hc_amps_dict.keys())
    n_hc = len(hc_subjs)

    boot_beta_s = []
    boot_beta_c = []
    boot_cosine = []

    C_pooled = np.tile(create_basis_matrix(HUE_ANGLES, N_CHANNELS), (N_RUNS, 1))

    for b in range(n_boot):
        # Resample HC subjects with replacement
        sample_idx = rng.choice(n_hc, n_hc, replace=True)
        sampled_subjs = [hc_subjs[i] for i in sample_idx]

        # Recompute W for each sampled subject
        W_boot = {}
        for s in sampled_subjs:
            amp = hc_amps_dict[s]
            V_s = amp.shape[2]
            X_all = amp.reshape(-1, V_s)
            alpha, _ = gcv_select_alpha(C_pooled, X_all)
            W = fit_W_ridge(C_pooled, X_all, alpha)
            # Use unique key to handle duplicates
            key = f'{s}_{b}_{len(W_boot)}'
            W_boot[key] = W

        # Quick grid search (coarse)
        best_cos = -2.0
        best_bs, best_bc = 0.0, 0.0
        for bs in range(0, 51, 3):
            for bc in range(-50, 51, 3):
                C_shifted = two_component_design_matrix(
                    float(bs), float(bc), cvd_type)
                drdm_sim, _ = compute_delta_rdm_sim(
                    W_boot, C_shifted, C_baseline)
                cos_val = cosine_similarity(drdm_sim, delta_rdm_obs)
                if cos_val > best_cos:
                    best_cos = cos_val
                    best_bs, best_bc = float(bs), float(bc)

        # Fine search around best
        for bs in np.arange(max(0, best_bs - 3), min(31, best_bs + 4), 1.0):
            for bc in np.arange(max(-30, best_bc - 3), min(31, best_bc + 4), 1.0):
                C_shifted = two_component_design_matrix(bs, bc, cvd_type)
                drdm_sim, _ = compute_delta_rdm_sim(
                    W_boot, C_shifted, C_baseline)
                cos_val = cosine_similarity(drdm_sim, delta_rdm_obs)
                if cos_val > best_cos:
                    best_cos = cos_val
                    best_bs, best_bc = bs, bc

        boot_beta_s.append(best_bs)
        boot_beta_c.append(best_bc)
        boot_cosine.append(best_cos)

        if (b + 1) % 100 == 0:
            print(f'    Bootstrap {b+1}/{n_boot}...')

    boot_beta_s = np.array(boot_beta_s)
    boot_beta_c = np.array(boot_beta_c)
    boot_cosine = np.array(boot_cosine)

    return {
        'n_boot': n_boot,
        'beta_s_mean': float(boot_beta_s.mean()),
        'beta_s_std': float(boot_beta_s.std()),
        'beta_s_ci95': [float(np.percentile(boot_beta_s, 2.5)),
                        float(np.percentile(boot_beta_s, 97.5))],
        'beta_c_mean': float(boot_beta_c.mean()),
        'beta_c_std': float(boot_beta_c.std()),
        'beta_c_ci95': [float(np.percentile(boot_beta_c, 2.5)),
                        float(np.percentile(boot_beta_c, 97.5))],
        'cosine_mean': float(boot_cosine.mean()),
        'cosine_ci95': [float(np.percentile(boot_cosine, 2.5)),
                        float(np.percentile(boot_cosine, 97.5))],
        'beta_s_dist': boot_beta_s.tolist(),
        'beta_c_dist': boot_beta_c.tolist(),
    }


# =============================================================================
# Color visualization
# =============================================================================

def plot_color_analysis(output_dir, cvd_subj, cvd_type, best_bs, best_bc,
                         delta_theta, hue_base):
    """Generate color visualization figures."""
    orig_rgb = get_stim_rgb()

    # Fig 1: Color swatches — Original | 2-Component Warped | Filter Corrected
    fig, axes = plt.subplots(3, 9, figsize=(15, 4),
                              gridspec_kw={'width_ratios': [2] + [1]*8,
                                           'hspace': 0.4, 'wspace': 0.1})

    row_labels = [
        f'Normal Vision\n(Original)',
        f'sub-{cvd_subj} ({cvd_type})\n2-Comp Warped\nβ_s={best_bs:.0f}° β_c={best_bc:.0f}°',
        f'Filter Corrected\n(inverse warp)',
    ]
    row_colors = ['#333333', '#D32F2F', '#1565C0']

    warped_rgb = shift_stim_hue(delta_theta)
    corrected_rgb = shift_stim_hue(-delta_theta)

    for row, (label, color, rgb_arr) in enumerate(zip(
            row_labels, row_colors,
            [orig_rgb, warped_rgb, corrected_rgb])):
        ax_label = axes[row, 0]
        ax_label.text(0.5, 0.5, label, ha='center', va='center',
                       fontsize=7, fontweight='bold', color=color,
                       transform=ax_label.transAxes)
        ax_label.set_facecolor('white')
        ax_label.set_xticks([]); ax_label.set_yticks([])
        for sp in ax_label.spines.values():
            sp.set_visible(False)

        for j in range(8):
            ax = axes[row, j + 1]
            ax.set_facecolor(np.clip(rgb_arr[j], 0, 1))
            ax.set_xticks([]); ax.set_yticks([])
            if row == 0:
                ax.set_title(COLOR_NAMES[j], fontsize=8, fontweight='bold', pad=2)
            if row > 0:
                d = delta_theta[j] if row == 1 else -delta_theta[j]
                if abs(d) > 0.5:
                    ax.text(0.5, -0.08, f'{d:+.1f}°', ha='center', va='top',
                            fontsize=6, color=color, transform=ax.transAxes)
            for sp in ax.spines.values():
                sp.set_linewidth(2)
                sp.set_color('#333333')

    fig.suptitle(f'2-Component Angular Dilation: sub-{cvd_subj} ({cvd_type})',
                 fontsize=12, fontweight='bold')
    plt.savefig(output_dir / f'sub-{cvd_subj}_color_swatches.png',
                dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()

    # Fig 2: Color wheel
    fig, ax = plt.subplots(1, 1, figsize=(7, 7), subplot_kw={'projection': 'polar'})

    n_bg = 360
    bg_hues = np.linspace(0, 360, n_bg, endpoint=False)
    med_L = np.median(STIM_L)
    med_C = np.median(STIM_CHROMA)
    bg_a = med_C * np.cos(np.deg2rad(bg_hues))
    bg_b = med_C * np.sin(np.deg2rad(bg_hues))
    bg_rgb = lab2rgb(np.full(n_bg, med_L), bg_a, bg_b)
    for i in range(n_bg):
        ax.bar(np.deg2rad(bg_hues[i]), 0.25, width=np.deg2rad(1.2),
               bottom=0.0, color=bg_rgb[i], alpha=0.2, edgecolor='none')

    ring_t = np.linspace(0, 2 * np.pi, 200)
    ax.plot(ring_t, np.full(200, 0.70), '-', color='#cccccc', lw=0.5)
    ax.plot(ring_t, np.full(200, 0.48), '-', color='#ffcccc', lw=0.5)

    for j in range(8):
        t_orig = np.deg2rad(HUE_ANGLES_DEG[j])
        t_shift = np.deg2rad((HUE_ANGLES_DEG[j] + delta_theta[j]) % 360)

        ax.scatter(t_orig, 0.70, s=300, c=[orig_rgb[j]],
                   edgecolors='black', linewidths=1.5, zorder=5)
        ax.scatter(t_shift, 0.48, s=200, c=[warped_rgb[j]],
                   edgecolors='red', linewidths=1.5, zorder=5, marker='D')
        if abs(delta_theta[j]) > 2:
            ax.annotate('', xy=(t_shift, 0.54), xytext=(t_orig, 0.64),
                        arrowprops=dict(arrowstyle='->', color='red',
                                        lw=1.5, alpha=0.7,
                                        connectionstyle='arc3,rad=0.15'))

    ax.set_theta_zero_location('E')
    ax.set_theta_direction(1)
    ax.set_ylim(0, 0.95)
    ax.set_yticks([])
    ax.set_xticks(np.deg2rad(HUE_ANGLES_DEG))
    ax.set_xticklabels(COLOR_NAMES, fontsize=9)
    ax.set_title(f'sub-{cvd_subj} ({cvd_type}) — 2-Component Warp\n'
                 f'β_s={best_bs:.0f}°, β_c={best_bc:.0f}°, θ_conf={CONF_AXIS[cvd_type]:.0f}°',
                 fontsize=11, fontweight='bold', pad=20)

    plt.savefig(output_dir / f'sub-{cvd_subj}_color_wheel.png',
                dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()

    # Fig 3: Per-color delta-theta bars
    fig, ax = plt.subplots(1, 1, figsize=(8, 4))
    x = np.arange(8)
    bars = ax.bar(x, delta_theta,
                   color=[orig_rgb[j] for j in range(8)],
                   edgecolor='black', linewidth=0.8)
    for j, bar in enumerate(bars):
        if abs(delta_theta[j]) > 10:
            bar.set_edgecolor('red')
            bar.set_linewidth(2)
    ax.axhline(0, color='gray', lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(COLOR_NAMES, fontsize=9)
    ax.set_ylabel('δθ (degrees)', fontsize=11)
    ax.set_title(f'sub-{cvd_subj} ({cvd_type}) — Per-Color Hue Shift\n'
                 f'β_s={best_bs:.0f}° (S-cone) + β_c={best_bc:.0f}° (confusion)',
                 fontsize=11, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / f'sub-{cvd_subj}_delta_theta_bars.png',
                dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()


# =============================================================================
# Machado CVD filter validation
# =============================================================================

def machado_cvd_simulate_color(lab_L, lab_a, lab_b, delta_lambda, cvd_type):
    """Simulate how a CVD observer perceives a color.

    Uses the Machado model to shift the hue angle, preserving L* and chroma.
    This is an approximation: the actual Machado model operates on cone fundamentals,
    but for visualization we apply the hue shift to CIELab coordinates.
    """
    # Get hue shift for this color
    hue_orig = np.degrees(np.arctan2(lab_b, lab_a)) % 360.0
    chroma = np.sqrt(lab_a**2 + lab_b**2)

    # For a single arbitrary color, we can't directly use machado_shifted_hue
    # (which operates on the 8 experimental stimuli via Stockman fundamentals).
    # Instead, approximate: use the per-stimulus shifts and interpolate.
    hue_base, hue_shifted, _ = machado_shifted_hue(delta_lambda, cvd_type)

    # Find closest stimulus and apply that shift proportion
    diffs = np.abs((hue_base - hue_orig + 180) % 360 - 180)
    closest = np.argmin(diffs)
    shift = hue_shifted[closest] - hue_base[closest]

    new_hue = np.radians(hue_orig + shift)
    new_a = chroma * np.cos(new_hue)
    new_b = chroma * np.sin(new_hue)

    return lab_L, new_a, new_b


def filter_validation_machado(output_dir, cvd_subj, cvd_type, delta_theta,
                               delta_lambda_sim=10.0):
    """Validate filter by simulating CVD perception of filtered stimuli.

    Pipeline:
    1. Original stimuli → 8 colors
    2. Apply filter (inverse warp) → filtered stimuli
    3. Pass filtered stimuli through Machado CVD simulator → CVD-perceived
    4. Compare CVD-perceived with normal-vision original
    """
    orig_rgb = get_stim_rgb()

    # Step 1: Original hue angles (CIELab)
    orig_hues = np.degrees(np.arctan2(STIM_B, STIM_A)) % 360.0

    # Step 2: Apply inverse filter (shift hues back)
    filtered_hues = orig_hues - delta_theta
    filtered_a = STIM_CHROMA * np.cos(np.radians(filtered_hues))
    filtered_b = STIM_CHROMA * np.sin(np.radians(filtered_hues))
    filtered_rgb = lab2rgb(STIM_L, filtered_a, filtered_b)

    # Step 3: Simulate CVD perception of filtered stimuli
    # Use Machado at a representative Δλ
    hue_base, hue_shifted, machado_dt = machado_shifted_hue(
        delta_lambda_sim, cvd_type)

    # For each filtered color, apply the Machado shift
    # Map filtered hues to nearest stimulus for shift lookup
    perceived_hues = np.zeros(8)
    for j in range(8):
        # The Machado shift is stimulus-specific, so for the filtered hue
        # we interpolate the shift from the original stimuli
        # Simple approach: apply the same relative shift pattern
        perceived_hues[j] = filtered_hues[j] + machado_dt[j]

    perceived_a = STIM_CHROMA * np.cos(np.radians(perceived_hues))
    perceived_b = STIM_CHROMA * np.sin(np.radians(perceived_hues))
    perceived_rgb = lab2rgb(STIM_L, perceived_a, perceived_b)

    # Step 4: Also show unfiltered CVD perception
    unfiltered_perceived_hues = orig_hues + machado_dt
    unfilt_a = STIM_CHROMA * np.cos(np.radians(unfiltered_perceived_hues))
    unfilt_b = STIM_CHROMA * np.sin(np.radians(unfiltered_perceived_hues))
    unfiltered_perceived_rgb = lab2rgb(STIM_L, unfilt_a, unfilt_b)

    # Compute hue error (how close CVD perception is to normal)
    error_unfiltered = np.abs((unfiltered_perceived_hues - orig_hues + 180) % 360 - 180)
    error_filtered = np.abs((perceived_hues - orig_hues + 180) % 360 - 180)

    # Plot
    fig, axes = plt.subplots(4, 9, figsize=(15, 5.5),
                              gridspec_kw={'width_ratios': [2.5] + [1]*8,
                                           'hspace': 0.5, 'wspace': 0.1})

    rows = [
        ('Normal Vision\n(target)', orig_rgb, np.zeros(8), '#333333'),
        (f'CVD Perception\n(Δλ={delta_lambda_sim}nm, no filter)',
         unfiltered_perceived_rgb, error_unfiltered, '#D32F2F'),
        (f'Filtered Stimuli\n(inverse warp applied)',
         filtered_rgb, delta_theta, '#1565C0'),
        (f'CVD Perception\nof Filtered Stimuli',
         perceived_rgb, error_filtered, '#2E7D32'),
    ]

    for row, (label, rgb_arr, vals, color) in enumerate(rows):
        ax_label = axes[row, 0]
        ax_label.text(0.5, 0.5, label, ha='center', va='center',
                       fontsize=7, fontweight='bold', color=color,
                       transform=ax_label.transAxes)
        ax_label.set_facecolor('white')
        ax_label.set_xticks([]); ax_label.set_yticks([])
        for sp in ax_label.spines.values():
            sp.set_visible(False)

        for j in range(8):
            ax = axes[row, j + 1]
            ax.set_facecolor(np.clip(rgb_arr[j], 0, 1))
            ax.set_xticks([]); ax.set_yticks([])
            if row == 0:
                ax.set_title(COLOR_NAMES[j], fontsize=8, fontweight='bold', pad=2)
            if row in (1, 3) and vals[j] > 1.0:
                ax.text(0.5, -0.08, f'err={vals[j]:.1f}°',
                        ha='center', va='top', fontsize=5, color=color,
                        transform=ax.transAxes)
            for sp in ax.spines.values():
                sp.set_linewidth(2)
                sp.set_color(color if row > 0 else '#333333')

    mean_err_unfilt = float(error_unfiltered.mean())
    mean_err_filt = float(error_filtered.mean())
    improvement = (1 - mean_err_filt / max(mean_err_unfilt, 0.01)) * 100

    fig.suptitle(f'Filter Validation: sub-{cvd_subj} ({cvd_type})\n'
                 f'Mean hue error: unfiltered={mean_err_unfilt:.1f}° → '
                 f'filtered={mean_err_filt:.1f}° ({improvement:.0f}% improvement)',
                 fontsize=11, fontweight='bold')
    plt.savefig(output_dir / f'sub-{cvd_subj}_filter_validation.png',
                dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()

    return {
        'delta_lambda_sim': delta_lambda_sim,
        'mean_hue_error_unfiltered': mean_err_unfilt,
        'mean_hue_error_filtered': mean_err_filt,
        'improvement_pct': improvement,
        'per_color_error_unfiltered': error_unfiltered.tolist(),
        'per_color_error_filtered': error_filtered.tolist(),
    }


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Comprehensive 2-component angular dilation analysis')
    parser.add_argument('--subjects', nargs='+', default=['08', '09'])
    parser.add_argument('--rois', nargs='+', default=['V1', 'V2'])
    parser.add_argument('--output_dir', type=str,
                        default='results/archive_superseded/2component_comprehensive')
    parser.add_argument('--n_boot', type=int, default=500)
    parser.add_argument('--skip_bootstrap', action='store_true')
    parser.add_argument('--machado_dl', type=float, default=10.0,
                        help='Machado Δλ for filter validation simulation')
    args = parser.parse_args()

    output_dir = _SCRIPT_DIR.parent / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    # Use Stockman normal-vision baseline (not CIELab nominal).
    # At Δλ=0, machado_shifted_hue returns normal-vision Stockman hue angles.
    # Using CIELab nominal as baseline creates a large artifact (norm≈1.82)
    # because Stockman and CIELab coordinates differ by up to 1.0 in basis
    # space, producing a ΔRDM_sim(0,0) ≠ 0 that anti-correlates with sub-08.
    hue_nv, _, _ = machado_shifted_hue(0.0, 'protan')  # same for any type at Δλ=0
    C_baseline = create_basis_full(N_CHANNELS)[
        np.round(hue_nv).astype(int) % 360]

    print('=' * 70)
    print('Comprehensive 2-Component Angular Dilation Analysis')
    print(f'Subjects: {args.subjects}')
    print(f'ROIs: {args.rois}')
    print(f'Output: {output_dir}')
    print('=' * 70)

    all_results = {}

    for cvd_subj in args.subjects:
        cvd_type = CVD_TYPE[cvd_subj]
        print(f'\n{"="*60}')
        print(f'Subject: sub-{cvd_subj} ({cvd_type})')
        print(f'{"="*60}')

        subj_results = {
            'subject': cvd_subj,
            'cvd_type': cvd_type,
            'timestamp': datetime.now().isoformat(),
        }

        # Load amplitudes for crossnobis
        print('\n[1] Loading amplitudes...')
        hc_amps = {}
        for roi in args.rois:
            hc_amps[roi] = load_all_amplitudes(roi)
            print(f'  {roi}: loaded {len(hc_amps[roi])} HC subjects')

        # =================================================================
        # Per-ROI analysis
        # =================================================================
        for roi in args.rois:
            print(f'\n--- {roi} ---')
            roi_results = {}

            # Load precomputed W and ΔRDM_obs
            hc_W = load_precomputed_W(roi)
            drdm_obs_corr = load_precomputed_delta_rdm_obs(roi, cvd_subj)

            # Compute crossnobis ΔRDM_obs
            print(f'  [2a] Computing crossnobis ΔRDM_obs...')
            amp_cvd = load_amplitudes(str(LOCAL_BASELINE), cvd_subj, roi)
            drdm_obs_xnobis, _, _, rdm_hc_ind_xnobis = compute_delta_rdm_obs(
                amp_cvd, hc_amps[roi], distance='crossnobis')

            # Compute RDM covariance for WUC
            print(f'  [2b] Computing RDM covariance for WUC...')
            hc_rdm_matrix = np.array(list(rdm_hc_ind_xnobis.values()))
            rdm_cov = estimate_rdm_covariance(hc_rdm_matrix)

            # Store basic stats
            roi_results['drdm_obs_correlation'] = {
                'n_positive': int(np.sum(drdm_obs_corr > 0)),
                'n_negative': int(np.sum(drdm_obs_corr < 0)),
                'norm': float(np.linalg.norm(drdm_obs_corr)),
            }
            roi_results['drdm_obs_crossnobis'] = {
                'n_positive': int(np.sum(drdm_obs_xnobis > 0)),
                'n_negative': int(np.sum(drdm_obs_xnobis < 0)),
                'norm': float(np.linalg.norm(drdm_obs_xnobis)),
            }

            # =============================================================
            # 2-Component grid search with CORRELATION distance
            # =============================================================
            print(f'  [3a] Grid search: 2-Component + correlation distance...')
            gs_corr = grid_search_2component(
                cvd_subj, roi, hc_W, drdm_obs_corr, cvd_type, C_baseline,
                rdm_cov=rdm_cov)
            roi_results['grid_correlation'] = {
                'best_cosine': gs_corr['best_cosine'],
                'best_wuc': gs_corr['best_wuc'],
            }
            print(f'    Cosine best: β_s={gs_corr["best_cosine"]["beta_s"]:.0f}°, '
                  f'β_c={gs_corr["best_cosine"]["beta_c"]:.0f}°, '
                  f'cos={gs_corr["best_cosine"]["value"]:.4f}')
            print(f'    WUC best:    β_s={gs_corr["best_wuc"]["beta_s"]:.0f}°, '
                  f'β_c={gs_corr["best_wuc"]["beta_c"]:.0f}°, '
                  f'wuc={gs_corr["best_wuc"]["value"]:.4f}')

            # =============================================================
            # 2-Component grid search with CROSSNOBIS distance
            # =============================================================
            print(f'  [3b] Grid search: 2-Component + crossnobis distance (coarse)...')
            L_inv_dict = precompute_L_inv(hc_amps[roi])
            gs_xnobis = grid_search_2component(
                cvd_subj, roi, hc_W, drdm_obs_xnobis, cvd_type, C_baseline,
                hc_amps_dict=hc_amps[roi], distance='crossnobis',
                rdm_cov=rdm_cov, L_inv_dict=L_inv_dict,
                beta_s_range=np.arange(0, 51, 5.0),
                beta_c_range=np.arange(-50, 51, 5.0))
            roi_results['grid_crossnobis'] = {
                'best_cosine': gs_xnobis['best_cosine'],
                'best_wuc': gs_xnobis['best_wuc'],
            }
            print(f'    Cosine best: β_s={gs_xnobis["best_cosine"]["beta_s"]:.0f}°, '
                  f'β_c={gs_xnobis["best_cosine"]["beta_c"]:.0f}°, '
                  f'cos={gs_xnobis["best_cosine"]["value"]:.4f}')

            # =============================================================
            # Permutation tests (8! = 40320)
            # =============================================================
            print(f'  [4] Permutation tests (8! = 40,320)...')

            # Correlation + cosine (primary)
            best_bs = gs_corr['best_cosine']['beta_s']
            best_bc = gs_corr['best_cosine']['beta_c']
            C_best = two_component_design_matrix(best_bs, best_bc, cvd_type)
            drdm_sim_best, _ = compute_delta_rdm_sim(hc_W, C_best, C_baseline)
            perm_corr_cos = permutation_test_8factorial(
                drdm_sim_best, drdm_obs_corr, rdm_cov=rdm_cov)
            roi_results['perm_correlation_cosine'] = perm_corr_cos
            print(f'    Corr+Cosine: p={perm_corr_cos["perm_p_cosine"]:.4f} '
                  f'(cos={perm_corr_cos["observed_cosine"]:.4f})')
            print(f'    Corr+WUC:    p={perm_corr_cos["perm_p_wuc"]:.4f} '
                  f'(wuc={perm_corr_cos["observed_wuc"]:.4f})')

            # Crossnobis + cosine
            best_bs_x = gs_xnobis['best_cosine']['beta_s']
            best_bc_x = gs_xnobis['best_cosine']['beta_c']
            C_best_x = two_component_design_matrix(best_bs_x, best_bc_x, cvd_type)
            drdm_sim_best_x, _ = compute_delta_rdm_sim_fast(
                hc_W, C_best_x, C_baseline,
                L_inv_dict=L_inv_dict, distance='crossnobis')
            perm_xnobis_cos = permutation_test_8factorial(
                drdm_sim_best_x, drdm_obs_xnobis, rdm_cov=rdm_cov)
            roi_results['perm_crossnobis_cosine'] = perm_xnobis_cos
            print(f'    Xnobis+Cos:  p={perm_xnobis_cos["perm_p_cosine"]:.4f} '
                  f'(cos={perm_xnobis_cos["observed_cosine"]:.4f})')

            # =============================================================
            # Max-statistic permutation (corrects for optimization circularity)
            # =============================================================
            print(f'  [4b] Max-statistic permutation (8! × grid)...')
            # Precompute ΔRDM_sim for all grid points
            beta_s_range = gs_corr.get('_beta_s_range', np.arange(0, 51, 1.0))
            beta_c_range = gs_corr.get('_beta_c_range', np.arange(-50, 51, 1.0))
            sim_matrix = []
            for bs in beta_s_range:
                for bc in beta_c_range:
                    C_shifted = two_component_design_matrix(bs, bc, cvd_type)
                    drdm_sim, _ = compute_delta_rdm_sim(
                        hc_W, C_shifted, C_baseline)
                    sim_matrix.append(drdm_sim)
            sim_matrix = np.array(sim_matrix)

            maxstat = maxstat_permutation_test(sim_matrix, drdm_obs_corr)
            roi_results['maxstat_perm'] = maxstat
            print(f'    MaxStat:     p={maxstat["maxstat_perm_p"]:.4f} '
                  f'(max_cos={maxstat["observed_max_cos"]:.4f}, '
                  f'null_95={maxstat["null_max_95"]:.4f})')

            subj_results[roi] = roi_results

        # =================================================================
        # Joint V1+V2 fitting
        # =================================================================
        if 'V1' in args.rois and 'V2' in args.rois:
            print(f'\n[5] Joint V1+V2 fitting...')
            hc_W_V1 = load_precomputed_W('V1')
            hc_W_V2 = load_precomputed_W('V2')
            drdm_obs_V1 = load_precomputed_delta_rdm_obs('V1', cvd_subj)
            drdm_obs_V2 = load_precomputed_delta_rdm_obs('V2', cvd_subj)

            joint_result = joint_v1v2_grid_search(
                cvd_subj, cvd_type, C_baseline,
                hc_W_V1, hc_W_V2, drdm_obs_V1, drdm_obs_V2)

            # Permutation for joint
            C_joint = two_component_design_matrix(
                joint_result['beta_s'], joint_result['beta_c'], cvd_type)
            drdm_sim_V1, _ = compute_delta_rdm_sim(hc_W_V1, C_joint, C_baseline)
            drdm_sim_V2, _ = compute_delta_rdm_sim(hc_W_V2, C_joint, C_baseline)

            # Joint permutation
            observed_joint = 0.5 * cosine_similarity(drdm_sim_V1, drdm_obs_V1) \
                           + 0.5 * cosine_similarity(drdm_sim_V2, drdm_obs_V2)

            null_joint = []
            for perm in itertools.permutations(range(8)):
                perm = list(perm)
                perm_idx = []
                for i in range(8):
                    for j in range(i + 1, 8):
                        pi, pj = sorted([perm[i], perm[j]])
                        flat_idx = sum(8 - 1 - k for k in range(pi)) + (pj - pi - 1)
                        perm_idx.append(flat_idx)
                obs_perm_V1 = drdm_obs_V1[perm_idx]
                obs_perm_V2 = drdm_obs_V2[perm_idx]
                null_joint.append(
                    0.5 * cosine_similarity(drdm_sim_V1, obs_perm_V1)
                    + 0.5 * cosine_similarity(drdm_sim_V2, obs_perm_V2))

            null_joint = np.array(null_joint)
            joint_p = float(np.mean(null_joint >= observed_joint))

            joint_result['perm_p'] = joint_p
            joint_result['null_mean'] = float(null_joint.mean())
            joint_result['null_std'] = float(null_joint.std())
            subj_results['joint_v1v2'] = joint_result

            print(f'  Joint: β_s={joint_result["beta_s"]:.0f}°, '
                  f'β_c={joint_result["beta_c"]:.0f}°, '
                  f'cos_joint={joint_result["joint_cosine"]:.4f}, '
                  f'p={joint_p:.4f}')
            print(f'  V1={joint_result["cosine_V1"]:.4f}, '
                  f'V2={joint_result["cosine_V2"]:.4f}')

        # =================================================================
        # Cone-shift + 2-component hybrid
        # =================================================================
        print(f'\n[6] Cone-shift + 2-component hybrid (V1)...')
        hc_W_V1 = load_precomputed_W('V1')
        drdm_obs_V1 = load_precomputed_delta_rdm_obs('V1', cvd_subj)
        hybrid = hybrid_grid_search(
            cvd_subj, cvd_type, hc_W_V1, drdm_obs_V1, C_baseline)
        subj_results['hybrid_v1'] = hybrid
        print(f'  Hybrid: Δλ={hybrid["delta_lambda"]:.1f}nm, '
              f'β_s={hybrid["beta_s"]:.0f}°, β_c={hybrid["beta_c"]:.0f}°, '
              f'cos={hybrid["cosine"]:.4f}')

        # =================================================================
        # Bootstrap CI
        # =================================================================
        if not args.skip_bootstrap:
            print(f'\n[7] Bootstrap CI (n={args.n_boot})...')
            drdm_obs_V1 = load_precomputed_delta_rdm_obs('V1', cvd_subj)
            boot = bootstrap_ci(
                cvd_subj, cvd_type, 'V1', C_baseline,
                hc_amps['V1'], drdm_obs_V1, n_boot=args.n_boot)
            subj_results['bootstrap_V1'] = boot
            print(f'  β_s: {boot["beta_s_mean"]:.1f}° ± {boot["beta_s_std"]:.1f}° '
                  f'CI95=[{boot["beta_s_ci95"][0]:.1f}, {boot["beta_s_ci95"][1]:.1f}]')
            print(f'  β_c: {boot["beta_c_mean"]:.1f}° ± {boot["beta_c_std"]:.1f}° '
                  f'CI95=[{boot["beta_c_ci95"][0]:.1f}, {boot["beta_c_ci95"][1]:.1f}]')
        else:
            print('\n[7] Bootstrap skipped (--skip_bootstrap)')

        # =================================================================
        # Color visualization
        # =================================================================
        print(f'\n[8] Color visualization...')
        best_bs = subj_results['V1']['grid_correlation']['best_cosine']['beta_s']
        best_bc = subj_results['V1']['grid_correlation']['best_cosine']['beta_c']
        dt, hue_base = two_component_delta_theta(best_bs, best_bc, cvd_type)
        plot_color_analysis(output_dir, cvd_subj, cvd_type, best_bs, best_bc,
                            dt, hue_base)
        subj_results['delta_theta_deg'] = dt.tolist()
        subj_results['hue_base_deg'] = hue_base.tolist()
        print(f'  Saved color figures for sub-{cvd_subj}')

        # =================================================================
        # Filter validation with Machado simulator
        # =================================================================
        print(f'\n[9] Filter validation (Machado CVD simulation)...')
        filter_val = filter_validation_machado(
            output_dir, cvd_subj, cvd_type, dt,
            delta_lambda_sim=args.machado_dl)
        subj_results['filter_validation'] = filter_val
        print(f'  Mean hue error: {filter_val["mean_hue_error_unfiltered"]:.1f}° → '
              f'{filter_val["mean_hue_error_filtered"]:.1f}° '
              f'({filter_val["improvement_pct"]:.0f}% improvement)')

        # Save per-subject JSON
        out_path = output_dir / f'sub-{cvd_subj}_2component_results.json'
        with open(out_path, 'w') as f:
            json.dump(subj_results, f, indent=2, default=str)
        print(f'\nSaved: {out_path}')
        all_results[cvd_subj] = subj_results

    # =====================================================================
    # Summary table
    # =====================================================================
    print('\n' + '=' * 80)
    print('COMPREHENSIVE RESULTS SUMMARY')
    print('=' * 80)
    print(f'{"Subj":<6} {"ROI":<4} {"Dist":<10} {"Metric":<8} '
          f'{"β_s":>5} {"β_c":>5} {"Value":>8} {"perm_p":>8}')
    print('-' * 80)

    for cvd_subj in args.subjects:
        r = all_results[cvd_subj]
        for roi in args.rois:
            rr = r[roi]
            # Correlation + cosine
            gc = rr['grid_correlation']['best_cosine']
            pc = rr['perm_correlation_cosine']
            sig = '*' if pc['perm_p_cosine'] < 0.05 else (
                '†' if pc['perm_p_cosine'] < 0.10 else '')
            print(f'  {cvd_subj:<4} {roi:<4} {"corr":<10} {"cosine":<8} '
                  f'{gc["beta_s"]:>5.0f} {gc["beta_c"]:>5.0f} '
                  f'{gc["value"]:>8.4f} {pc["perm_p_cosine"]:>7.4f}{sig}')

            # Correlation + WUC
            gw = rr['grid_correlation']['best_wuc']
            print(f'  {cvd_subj:<4} {roi:<4} {"corr":<10} {"WUC":<8} '
                  f'{gw["beta_s"]:>5.0f} {gw["beta_c"]:>5.0f} '
                  f'{gw["value"]:>8.4f} {pc["perm_p_wuc"]:>7.4f}')

            # Crossnobis + cosine
            gx = rr['grid_crossnobis']['best_cosine']
            px = rr['perm_crossnobis_cosine']
            sig = '*' if px['perm_p_cosine'] < 0.05 else (
                '†' if px['perm_p_cosine'] < 0.10 else '')
            print(f'  {cvd_subj:<4} {roi:<4} {"crossnobis":<10} {"cosine":<8} '
                  f'{gx["beta_s"]:>5.0f} {gx["beta_c"]:>5.0f} '
                  f'{gx["value"]:>8.4f} {px["perm_p_cosine"]:>7.4f}{sig}')

            # Max-statistic (corrected)
            if 'maxstat_perm' in rr:
                ms = rr['maxstat_perm']
                sig = '*' if ms['maxstat_perm_p'] < 0.05 else (
                    '†' if ms['maxstat_perm_p'] < 0.10 else '')
                print(f'  {cvd_subj:<4} {roi:<4} {"corr":<10} {"maxstat":<8} '
                      f'{gc["beta_s"]:>5.0f} {gc["beta_c"]:>5.0f} '
                      f'{ms["observed_max_cos"]:>8.4f} '
                      f'{ms["maxstat_perm_p"]:>7.4f}{sig}')

        # Joint
        if 'joint_v1v2' in r:
            j = r['joint_v1v2']
            sig = '*' if j['perm_p'] < 0.05 else (
                '†' if j['perm_p'] < 0.10 else '')
            print(f'  {cvd_subj:<4} {"V1+2":<4} {"corr":<10} {"joint":<8} '
                  f'{j["beta_s"]:>5.0f} {j["beta_c"]:>5.0f} '
                  f'{j["joint_cosine"]:>8.4f} {j["perm_p"]:>7.4f}{sig}')

        # Hybrid
        if 'hybrid_v1' in r:
            h = r['hybrid_v1']
            print(f'  {cvd_subj:<4} {"V1":<4} {"corr":<10} {"hybrid":<8} '
                  f'Δλ={h["delta_lambda"]:.0f} β_s={h["beta_s"]:.0f} '
                  f'β_c={h["beta_c"]:.0f} cos={h["cosine"]:.4f}')

        print()

    print('Analysis complete.')


if __name__ == '__main__':
    main()
