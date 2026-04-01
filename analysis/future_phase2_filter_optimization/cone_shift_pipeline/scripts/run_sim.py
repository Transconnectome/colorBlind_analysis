#!/usr/bin/env python3
"""
run_sim.py — Geometry→Function simulation: RDM-fit δ → synthetic Y → LOCO reproduction.

Phase A: ΔRDM-based δ* estimation (fitting criterion = RDM metric)
Phase B: Synthetic CVD-like brain data generation
Phase C: LOCO reproduction on synthetic data (independent evaluation)

Usage:
    python run_sim.py --sub 08 --roi V1 --model cone_1way --metric corr \
                      --output_dir results/sim
    python run_sim.py --sub 09 --roi V2 --model fourier --metric triangle \
                      --output_dir results/sim

Arguments:
    --sub:    CVD subject ID (08, 09)
    --roi:    ROI name (V1, V2)
    --model:  Distortion model (cone_1way, cone_3way, fourier)
    --metric: RDM distance metric (corr, cosine, triangle, combination)
"""

import argparse
import json
import numpy as np
from pathlib import Path
from datetime import datetime
from scipy.optimize import differential_evolution
from scipy.stats import spearmanr, pearsonr
from scipy.spatial.distance import pdist
from itertools import permutations
import sys
import warnings

warnings.filterwarnings('ignore', category=RuntimeWarning)

# ============================================================================
# Path setup
# ============================================================================
_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR))

_FWD_DIR = str(Path(__file__).resolve().parent.parent.parent.parent
               / 'future_phase1_forward_model' / 'scripts')
sys.path.insert(0, _FWD_DIR)

from utils_forward_model import (
    HC_SUBJECTS, CVD_SUBJECTS, ROIS, N_CHANNELS, N_RUNS, N_COLORS,
    HUE_ANGLES, load_amplitudes, create_basis_matrix,
    gcv_select_alpha, fit_W_ridge, voxel_pattern_correlation,
)
from utils_distortion_models import (
    MODELS, get_design_matrix, get_initial_params, apply_distortion,
)

# ============================================================================
# Constants
# ============================================================================
_ANALYSIS_DIR = Path(__file__).resolve().parent.parent.parent.parent

# Data path: try local first, fall back to server derivatives
_LOCAL_BASELINE = _ANALYSIS_DIR / 'phase1_preprocess_decoding' / 'results' / 'full_dataset_C010'
_SERVER_BASELINE = Path('/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010')
LOCAL_BASELINE = _LOCAL_BASELINE if _LOCAL_BASELINE.exists() else _SERVER_BASELINE

FWD_RESULTS = _ANALYSIS_DIR / 'future_phase1_forward_model' / 'results'

CVD_TYPE = {'08': 'deutan', '09': 'protan', '10': 'normal'}
COLOR_NAMES = ['red', 'orange', 'yellow', 'green', 'cyan', 'blue', 'purple', 'magenta']

# 28 pair labels
PAIR_LABELS = []
for i in range(N_COLORS):
    for j in range(i + 1, N_COLORS):
        PAIR_LABELS.append(f'{COLOR_NAMES[i]}-{COLOR_NAMES[j]}')


# ============================================================================
# RDM Distance Functions
# ============================================================================

def compute_rdm_corr(patterns):
    """Correlation distance RDM: d(i,j) = 1 - pearson_r(y_i, y_j)."""
    return pdist(patterns, metric='correlation')


def compute_rdm_cosine(patterns):
    """Cosine distance RDM: d(i,j) = 1 - (y_i · y_j) / (||y_i|| ||y_j||).

    Unlike correlation, does NOT mean-center. Preserves absolute direction info.
    """
    return pdist(patterns, metric='cosine')


def compute_rdm_triangle(patterns, base_metric='correlation'):
    """Local triangle distortion RDM.

    For each pair (i,j), measures deviation from intermediate-point interpolation:
        Δ_local(i,j) = mean_k [ d(i,j) - (d(i,k) + d(k,j)) / 2 ]
    where k iterates over all other colors.

    Positive = detour (farther than expected from intermediates)
    Negative = shortcut (closer than expected)

    Args:
        patterns: (8, V_s) mean patterns per condition
        base_metric: underlying distance ('correlation' or 'cosine')

    Returns:
        triangle_upper: (28,) upper triangle of triangle distortion matrix
    """
    n = patterns.shape[0]

    # Compute full distance matrix using base metric
    if base_metric == 'correlation':
        rdm_full = pdist(patterns, metric='correlation')
    else:
        rdm_full = pdist(patterns, metric='cosine')

    from scipy.spatial.distance import squareform
    D = squareform(rdm_full)  # (8, 8)

    # Triangle distortion for each pair
    triangle = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            # Average over all intermediary points k != i, k != j
            intermediaries = [k for k in range(n) if k != i and k != j]
            detour_scores = []
            for k in intermediaries:
                # How much does d(i,j) deviate from average of d(i,k) and d(k,j)?
                expected = (D[i, k] + D[k, j]) / 2.0
                detour_scores.append(D[i, j] - expected)
            triangle[i, j] = np.mean(detour_scores)
            triangle[j, i] = triangle[i, j]

    return triangle[np.triu_indices(n, k=1)]


def compute_rdm(patterns, metric):
    """Unified RDM computation dispatcher.

    Args:
        patterns: (8, V_s)
        metric: 'corr', 'cosine', or 'triangle'

    Returns:
        rdm_upper: (28,) upper triangle
    """
    if metric == 'corr':
        return compute_rdm_corr(patterns)
    elif metric == 'cosine':
        return compute_rdm_cosine(patterns)
    elif metric == 'triangle':
        return compute_rdm_triangle(patterns, base_metric='correlation')
    else:
        raise ValueError(f'Unknown metric: {metric}')


# ============================================================================
# ΔRDM Computation
# ============================================================================

def compute_delta_rdm_obs(amp_cvd, hc_amps_dict, metric):
    """Observed ΔRDM = RDM_CVD - RDM_HC_mean.

    Args:
        amp_cvd: (6, 8, V_s)
        hc_amps_dict: {subj: (6, 8, V_s)}
        metric: 'corr', 'cosine', 'triangle'

    Returns:
        delta_rdm: (28,)
        rdm_cvd: (28,)
        rdm_hc_mean: (28,)
    """
    rdm_cvd = compute_rdm(amp_cvd.mean(axis=0), metric)

    rdm_hc_list = []
    for subj, amp in hc_amps_dict.items():
        rdm_hc_list.append(compute_rdm(amp.mean(axis=0), metric))

    rdm_hc_mean = np.mean(rdm_hc_list, axis=0)
    delta_rdm = rdm_cvd - rdm_hc_mean
    return delta_rdm, rdm_cvd, rdm_hc_mean


def compute_delta_rdm_sim(hc_W_dict, C_shifted, C_baseline, metric):
    """Simulated ΔRDM = RDM(C_shifted @ W) - RDM(C_baseline @ W), mean over HC.

    Args:
        hc_W_dict: {subj: (K, V_s)}
        C_shifted: (8, K)
        C_baseline: (8, K)
        metric: 'corr', 'cosine', 'triangle'

    Returns:
        delta_rdm_mean: (28,)
    """
    deltas = []
    for subj, W in hc_W_dict.items():
        Y_shifted = C_shifted @ W      # (8, V_s)
        Y_baseline = C_baseline @ W    # (8, V_s)
        rdm_s = compute_rdm(Y_shifted, metric)
        rdm_b = compute_rdm(Y_baseline, metric)
        deltas.append(rdm_s - rdm_b)

    return np.mean(deltas, axis=0)


def compute_delta_rdm_combination(hc_W_dict, C_shifted, C_baseline,
                                   delta_obs_corr, delta_obs_cosine,
                                   delta_obs_triangle):
    """Combination loss: weighted sum of corr + cosine + triangle ΔRDM.

    Equal weights (1/3 each) after z-scoring each component.

    Returns:
        loss: scalar
        component_pearson: dict of per-metric Pearson r
    """
    sim_corr = compute_delta_rdm_sim(hc_W_dict, C_shifted, C_baseline, 'corr')
    sim_cos = compute_delta_rdm_sim(hc_W_dict, C_shifted, C_baseline, 'cosine')
    sim_tri = compute_delta_rdm_sim(hc_W_dict, C_shifted, C_baseline, 'triangle')

    def _pearson_safe(a, b):
        if np.std(a) == 0 or np.std(b) == 0:
            return 0.0
        r, _ = pearsonr(a, b)
        return float(r) if np.isfinite(r) else 0.0

    r_corr = _pearson_safe(sim_corr, delta_obs_corr)
    r_cos = _pearson_safe(sim_cos, delta_obs_cosine)
    r_tri = _pearson_safe(sim_tri, delta_obs_triangle)

    # Combine: negative mean r (for minimization → maximize combined r)
    loss = -(r_corr + r_cos + r_tri) / 3.0

    return loss, {'corr': r_corr, 'cosine': r_cos, 'triangle': r_tri}


# ============================================================================
# Phase A: ΔRDM-based δ optimization
# ============================================================================

def rdm_loss_single(params, model_name, cvd_type, hc_W_dict,
                    C_baseline, delta_obs, metric):
    """Loss for single-metric ΔRDM fitting: -Pearson(ΔRDM_sim, ΔRDM_obs).

    Minimizing this maximizes Pearson correlation between sim and obs.
    """
    C_shifted = get_design_matrix(model_name, params, cvd_type=cvd_type)
    delta_sim = compute_delta_rdm_sim(hc_W_dict, C_shifted, C_baseline, metric)

    if np.std(delta_sim) == 0 or np.std(delta_obs) == 0:
        return 1.0  # worst
    r, _ = pearsonr(delta_sim, delta_obs)
    if not np.isfinite(r):
        return 1.0
    return -float(r)


def rdm_loss_scale_penalized(params, model_name, cvd_type, hc_W_dict,
                              C_baseline, delta_obs, metric, lam=0.1):
    """Scale-penalized Pearson loss for ΔRDM fitting.

    L = (1 - r) + λ · (log(||ΔRDM_sim|| / ||ΔRDM_obs||))²

    Breaks the singularity of pure Pearson by penalizing scale mismatch.
    - Direction: captured by (1 - r) term
    - Magnitude: captured by log-ratio penalty (symmetric for over/under-scaling)

    Args:
        params, model_name, cvd_type, hc_W_dict, C_baseline, delta_obs, metric:
            Same as rdm_loss_single.
        lam: scale penalty weight (default 0.1 — direction-dominant).

    Returns:
        loss: scalar to minimize
    """
    C_shifted = get_design_matrix(model_name, params, cvd_type=cvd_type)
    delta_sim = compute_delta_rdm_sim(hc_W_dict, C_shifted, C_baseline, metric)

    if np.std(delta_sim) == 0 or np.std(delta_obs) == 0:
        return 2.0  # worst (range: [0, 2+])

    r, _ = pearsonr(delta_sim, delta_obs)
    if not np.isfinite(r):
        return 2.0

    norm_sim = np.linalg.norm(delta_sim)
    norm_obs = np.linalg.norm(delta_obs)

    if norm_sim < 1e-12 or norm_obs < 1e-12:
        return 2.0

    log_ratio = np.log(norm_sim / norm_obs)
    scale_penalty = log_ratio ** 2

    return (1.0 - float(r)) + lam * scale_penalty


def rdm_loss_combination(params, model_name, cvd_type, hc_W_dict,
                          C_baseline, delta_obs_corr, delta_obs_cosine,
                          delta_obs_triangle):
    """Loss for combination ΔRDM fitting."""
    C_shifted = get_design_matrix(model_name, params, cvd_type=cvd_type)
    loss, _ = compute_delta_rdm_combination(
        hc_W_dict, C_shifted, C_baseline,
        delta_obs_corr, delta_obs_cosine, delta_obs_triangle)
    return loss


def fit_delta_rdm(model_name, cvd_type, hc_W_dict, C_baseline,
                  delta_obs, metric, delta_obs_corr=None,
                  delta_obs_cosine=None, delta_obs_triangle=None,
                  loss_type='pearson', scale_lambda=0.1):
    """Phase A: Optimize δ* to minimize ΔRDM loss.

    Args:
        loss_type: 'pearson' (default) or 'pearson_scale' (scale-penalized).
        scale_lambda: weight for scale penalty (only for 'pearson_scale').

    Returns:
        best_params, best_loss, best_pearson
    """
    bounds = MODELS[model_name]['bounds']

    if metric == 'combination':
        result = differential_evolution(
            rdm_loss_combination,
            bounds=bounds,
            args=(model_name, cvd_type, hc_W_dict, C_baseline,
                  delta_obs_corr, delta_obs_cosine, delta_obs_triangle),
            seed=42, maxiter=200, tol=1e-6, polish=True,
        )
        best_params = result.x.tolist()
        best_loss = float(result.fun)
        best_pearson = -best_loss
    elif loss_type == 'pearson_scale':
        result = differential_evolution(
            rdm_loss_scale_penalized,
            bounds=bounds,
            args=(model_name, cvd_type, hc_W_dict, C_baseline,
                  delta_obs, metric, scale_lambda),
            seed=42, maxiter=200, tol=1e-6, polish=True,
        )
        best_params = result.x.tolist()
        best_loss = float(result.fun)
        # Recover Pearson r from the best params for reporting
        C_shifted = get_design_matrix(model_name, best_params, cvd_type=cvd_type)
        delta_sim = compute_delta_rdm_sim(hc_W_dict, C_shifted, C_baseline, metric)
        r, _ = pearsonr(delta_sim, delta_obs)
        best_pearson = float(r) if np.isfinite(r) else 0.0
    else:
        result = differential_evolution(
            rdm_loss_single,
            bounds=bounds,
            args=(model_name, cvd_type, hc_W_dict, C_baseline,
                  delta_obs, metric),
            seed=42, maxiter=200, tol=1e-6, polish=True,
        )
        best_params = result.x.tolist()
        best_loss = float(result.fun)
        best_pearson = -best_loss

    return best_params, best_loss, best_pearson


def permutation_test_rdm(hc_W_dict, C_baseline, delta_obs, metric,
                         best_params, model_name, cvd_type,
                         delta_obs_corr=None, delta_obs_cosine=None,
                         delta_obs_triangle=None,
                         loss_type='pearson', scale_lambda=0.1):
    """Permutation test: shuffle color labels of observed ΔRDM.

    Tests whether the best Pearson r (or scale-penalized score) is higher
    than chance. Uses exact permutation (8! = 40320).

    For loss_type='pearson': tests Pearson r.
    For loss_type='pearson_scale': tests -(loss) = r - λ·(log ratio)²
      so higher = better, consistent with Pearson r direction.

    Returns:
        p_value, observed_r
    """
    # Compute observed r at best δ — precompute simulated ΔRDM ONCE
    C_shifted = get_design_matrix(model_name, best_params, cvd_type=cvd_type)
    from scipy.spatial.distance import squareform
    triu_idx = np.triu_indices(8, k=1)

    if metric == 'combination':
        # Precompute simulated ΔRDM for each sub-metric (invariant across perms)
        sim_corr = compute_delta_rdm_sim(hc_W_dict, C_shifted, C_baseline, 'corr')
        sim_cos = compute_delta_rdm_sim(hc_W_dict, C_shifted, C_baseline, 'cosine')
        sim_tri = compute_delta_rdm_sim(hc_W_dict, C_shifted, C_baseline, 'triangle')

        def _pearson_safe(a, b):
            if np.std(a) == 0 or np.std(b) == 0:
                return 0.0
            r, _ = pearsonr(a, b)
            return float(r) if np.isfinite(r) else 0.0

        obs_r = np.mean([
            _pearson_safe(sim_corr, delta_obs_corr),
            _pearson_safe(sim_cos, delta_obs_cosine),
            _pearson_safe(sim_tri, delta_obs_triangle),
        ])

        # Precompute squareform matrices for obs
        mat_obs_corr = squareform(delta_obs_corr)
        mat_obs_cos = squareform(delta_obs_cosine)
        mat_obs_tri = squareform(delta_obs_triangle)
    else:
        delta_sim = compute_delta_rdm_sim(hc_W_dict, C_shifted, C_baseline, metric)
        norm_sim = np.linalg.norm(delta_sim)

        obs_r_raw, _ = pearsonr(delta_sim, delta_obs)
        obs_r_raw = float(obs_r_raw) if np.isfinite(obs_r_raw) else 0.0

        if loss_type == 'pearson_scale' and norm_sim > 1e-12:
            # Test statistic: r - λ·(log ratio)² (higher = better)
            norm_obs = np.linalg.norm(delta_obs)
            log_ratio = np.log(norm_sim / max(norm_obs, 1e-12))
            obs_r = obs_r_raw - scale_lambda * log_ratio ** 2
        else:
            obs_r = obs_r_raw

        mat_obs = squareform(delta_obs)

    # Permutation: shuffle the 8 color labels of ΔRDM_obs
    # ΔRDM has 28 entries from 8×8 upper triangle
    # Shuffling color labels = re-indexing the 8×8 matrix
    null_rs = []
    for perm in permutations(range(8)):
        perm = list(perm)

        if metric == 'combination':
            perm_corr = mat_obs_corr[np.ix_(perm, perm)][triu_idx]
            perm_cos = mat_obs_cos[np.ix_(perm, perm)][triu_idx]
            perm_tri = mat_obs_tri[np.ix_(perm, perm)][triu_idx]
            null_rs.append(np.mean([
                _pearson_safe(sim_corr, perm_corr),
                _pearson_safe(sim_cos, perm_cos),
                _pearson_safe(sim_tri, perm_tri),
            ]))
        else:
            delta_perm = mat_obs[np.ix_(perm, perm)][triu_idx]
            r, _ = pearsonr(delta_sim, delta_perm)
            r = float(r) if np.isfinite(r) else 0.0

            if loss_type == 'pearson_scale' and norm_sim > 1e-12:
                norm_perm = np.linalg.norm(delta_perm)
                log_ratio_p = np.log(norm_sim / max(norm_perm, 1e-12))
                null_rs.append(r - scale_lambda * log_ratio_p ** 2)
            else:
                null_rs.append(r)

    null_rs = np.array(null_rs)
    p = (np.sum(null_rs >= obs_r) + 1) / (len(null_rs) + 1)
    return float(p), float(obs_r)


# ============================================================================
# Phase B: Synthetic CVD-like brain data generation
# ============================================================================

def generate_synthetic_data(hc_W_dict, hc_amps_dict, best_params,
                            model_name, cvd_type):
    """Generate synthetic CVD-like data under two Phase B variants.

    Variant 1 (`per_hc`):
        Each HC keeps its own encoding weights W_i.
        Y_syn_i = C(θ + δ*) @ W_i + residual_i

    Variant 2 (`mean_w`):
        All HC subjects share the group-mean encoding weights W_mean, while
        retaining subject-specific residual structure.
        Y_syn_i = C(θ + δ*) @ W_mean + residual_i

    Returns:
        dict with:
            per_hc_runs: {subj: (6, 8, V_s)}
            per_hc_mean: {subj: (8, V_s)}
            mean_w_runs: {subj: (6, 8, V_s)}
            mean_w_mean: {subj: (8, V_s)}
            W_mean: (K, V_s)
            C_shifted: (8, K)
    """
    C_shifted = get_design_matrix(model_name, best_params, cvd_type=cvd_type)

    subj_ids = sorted(hc_W_dict.keys())
    w_shapes = {subj: tuple(hc_W_dict[subj].shape) for subj in subj_ids}
    unique_w_shapes = sorted(set(w_shapes.values()))

    mean_w_available = len(unique_w_shapes) == 1
    mean_w_reason = None
    W_mean = None
    Y_mean_w = None

    if mean_w_available:
        W_mean = np.mean(np.stack([hc_W_dict[s] for s in subj_ids], axis=0), axis=0)
        Y_mean_w = C_shifted @ W_mean
    else:
        mean_w_reason = (
            'HC W shapes differ across subjects; voxel-space W_mean is not '
            'defined without a common voxel basis'
        )

    per_hc_runs = {}
    per_hc_mean = {}
    mean_w_runs = {}
    mean_w_mean = {}

    for subj in subj_ids:
        amp = hc_amps_dict[subj]  # (6, 8, V_s)
        mean_patterns = amp.mean(axis=0)  # (8, V_s)
        residuals = amp - mean_patterns[np.newaxis, :, :]  # (6, 8, V_s)

        Y_per_hc = C_shifted @ hc_W_dict[subj]
        per_hc_mean[subj] = Y_per_hc
        per_hc_runs[subj] = Y_per_hc[np.newaxis, :, :] + residuals

        if mean_w_available:
            mean_w_mean[subj] = Y_mean_w
            mean_w_runs[subj] = Y_mean_w[np.newaxis, :, :] + residuals

    return {
        'per_hc_runs': per_hc_runs,
        'per_hc_mean': per_hc_mean,
        'mean_w_runs': mean_w_runs,
        'mean_w_mean': mean_w_mean,
        'W_mean': W_mean,
        'C_shifted': C_shifted,
        'w_shapes': w_shapes,
        'mean_w_available': mean_w_available,
        'mean_w_reason': mean_w_reason,
    }


# ============================================================================
# Phase C: LOCO Reproduction on Synthetic Data
# ============================================================================

def loco_on_synthetic(Y_synthetic_runs, C_shifted):
    """Run true LOCO on one synthetic dataset.

    For each left-out color c, re-fit W using only the other 7 colors, then
    predict the held-out color response and compare it to the synthetic target.

    Args:
        Y_synthetic_runs: (6, 8, V_s)
        C_shifted: (8, K)

    Returns:
        vuln_synthetic: (8,) per-color LOCO vulnerability
        alpha_per_color: list of ridge alphas used for each held-out color
    """
    V_s = Y_synthetic_runs.shape[2]
    vuln = np.zeros(N_COLORS)
    alpha_per_color = []

    for color in range(N_COLORS):
        train_colors = [c for c in range(N_COLORS) if c != color]

        # Pool 6 runs × 7 colors = 42 samples
        X_train = Y_synthetic_runs[:, train_colors].reshape(-1, V_s)  # (42, V_s)
        C_train = np.tile(C_shifted[train_colors], (N_RUNS, 1))       # (42, K)

        alpha, _ = gcv_select_alpha(C_train, X_train)
        W_sim = fit_W_ridge(C_train, X_train, alpha)
        alpha_per_color.append(float(alpha))

        # Predict the held-out color from a W learned only on the remaining 7.
        Y_pred = C_shifted[color:color + 1] @ W_sim               # (1, V_s)
        Y_actual = Y_synthetic_runs[:, color].mean(axis=0, keepdims=True)  # (1, V_s)
        r = voxel_pattern_correlation(Y_pred, Y_actual)
        vuln[color] = r[0]

    return vuln, alpha_per_color


def loco_on_synthetic_group(synthetic_runs_dict, C_shifted):
    """Run LOCO for a collection of synthetic datasets and average profiles."""
    per_subject = {}
    vuln_list = []

    for subj in sorted(synthetic_runs_dict.keys()):
        vuln, alpha_per_color = loco_on_synthetic(synthetic_runs_dict[subj], C_shifted)
        vuln_list.append(vuln)
        per_subject[subj] = {
            'vuln_synthetic': vuln.tolist(),
            'alpha_per_color': alpha_per_color,
            'mean_vulnerability': float(np.mean(vuln)),
        }

    vuln_mean = np.mean(vuln_list, axis=0)
    return vuln_mean, per_subject


def summarize_loco_match(vuln_synthetic, vuln_observed):
    """Compare one synthetic LOCO profile against observed CVD LOCO."""
    if vuln_observed is None:
        return {}

    rho_loco, p_loco_raw = spearmanr(vuln_synthetic, vuln_observed)
    rho_loco = float(rho_loco) if np.isfinite(rho_loco) else 0.0

    perm_p_loco, obs_rho_loco, _ = null_loco_match(vuln_synthetic, vuln_observed)

    worst3_syn = np.argsort(vuln_synthetic)[:3].tolist()
    worst3_obs = np.argsort(vuln_observed)[:3].tolist()
    overlap = len(set(worst3_syn) & set(worst3_obs))

    return {
        'spearman_rho': rho_loco,
        'spearman_p_raw': float(p_loco_raw),
        'perm_p': perm_p_loco,
        'obs_rho': obs_rho_loco,
        'worst3_synthetic': [COLOR_NAMES[i] for i in worst3_syn],
        'worst3_observed': [COLOR_NAMES[i] for i in worst3_obs],
        'worst3_overlap': overlap,
    }


def load_cvd_loco_observed(sub_id, roi):
    """Load observed CVD LOCO from Phase 1 Forward Model results.

    JSON structure: {subject, subject_group, V1: {ridge_gcv: {folds: [...]}}, ...}
    Each fold has: {voxel_corr, test_color, ...}

    Returns:
        vuln_observed: (8,) per-color LOCO vulnerability (voxel_corr per color)
    """
    loco_path = FWD_RESULTS / 'validation' / f'sub-{sub_id}_loco.json'
    if not loco_path.exists():
        raise FileNotFoundError(f'LOCO results not found: {loco_path}')

    with open(loco_path) as f:
        data = json.load(f)

    roi_key = roi  # V1, V2, V3, V4 (disk key matches)
    if roi_key not in data:
        raise ValueError(f'ROI {roi_key} not in LOCO file. Available: {list(data.keys())}')

    roi_data = data[roi_key]
    if 'ridge_gcv' not in roi_data:
        raise ValueError(f'ridge_gcv not in {roi_key}. Available: {list(roi_data.keys())}')

    folds = roi_data['ridge_gcv']['folds']
    vuln = np.zeros(N_COLORS)
    for fold in folds:
        color_idx = fold['test_color']
        vuln[color_idx] = fold['voxel_corr']

    return vuln


# ============================================================================
# Null distribution for Phase C
# ============================================================================

def null_loco_match(vuln_synthetic, vuln_observed, n_null=1000):
    """Permutation test: is LOCO profile match better than random δ?

    Shuffles synthetic vulnerability labels to create null.

    Returns:
        p_value, obs_rho, null_rhos
    """
    obs_rho, _ = spearmanr(vuln_synthetic, vuln_observed)
    obs_rho = float(obs_rho) if np.isfinite(obs_rho) else 0.0

    # Exact permutation (8! = 40320)
    null_rhos = []
    for perm in permutations(range(8)):
        r, _ = spearmanr(vuln_synthetic[list(perm)], vuln_observed)
        null_rhos.append(float(r) if np.isfinite(r) else 0.0)

    null_rhos = np.array(null_rhos)
    p = (np.sum(null_rhos >= obs_rho) + 1) / (len(null_rhos) + 1)
    return float(p), obs_rho, null_rhos


# ============================================================================
# W precomputation
# ============================================================================

def precompute_hc_W(hc_amps_dict, C_original):
    """Precompute W_HC from pooled data (8 colors × 6 runs = 48 samples)."""
    hc_W_dict = {}
    hc_alpha_dict = {}
    C_pooled = np.tile(C_original, (N_RUNS, 1))  # (48, K)

    for subj, amp in hc_amps_dict.items():
        V_s = amp.shape[2]
        X_all = amp.reshape(-1, V_s)  # (48, V_s)
        alpha, _ = gcv_select_alpha(C_pooled, X_all)
        W = fit_W_ridge(C_pooled, X_all, alpha)  # (K, V_s)
        hc_W_dict[subj] = W
        hc_alpha_dict[subj] = float(alpha)

    return hc_W_dict, hc_alpha_dict


# ============================================================================
# Main pipeline
# ============================================================================

def run_pipeline(sub_id, roi, model_name, metric, output_dir,
                 loss_type='pearson', scale_lambda=0.1):
    """Run full Phase A → B → C pipeline for one combination."""

    cvd_type = CVD_TYPE[sub_id]
    loss_suffix = f'_{loss_type}' if loss_type != 'pearson' else ''
    combo_name = f'sub-{sub_id}_{roi}_{model_name}_{metric}{loss_suffix}'
    out_path = Path(output_dir) / combo_name
    out_path.mkdir(parents=True, exist_ok=True)

    print(f'=== {combo_name} ===')
    print(f'CVD type: {cvd_type}')
    t0 = datetime.now()

    # ------------------------------------------------------------------
    # 0. Load data
    # ------------------------------------------------------------------
    print('[0] Loading data...')
    hc_amps_dict = {}
    for s in HC_SUBJECTS:
        try:
            hc_amps_dict[s] = load_amplitudes(LOCAL_BASELINE, s, roi)
        except FileNotFoundError:
            print(f'  WARNING: skipping HC sub-{s} (not found)')

    amp_cvd = load_amplitudes(LOCAL_BASELINE, sub_id, roi)
    C_baseline = create_basis_matrix()  # (8, K)

    print(f'  HC subjects loaded: {len(hc_amps_dict)}')
    print(f'  CVD amp shape: {amp_cvd.shape}')
    print(f'  Basis shape: {C_baseline.shape}')

    # ------------------------------------------------------------------
    # 1. Precompute W_HC
    # ------------------------------------------------------------------
    print('[1] Precomputing W_HC...')
    hc_W_dict, hc_alpha_dict = precompute_hc_W(hc_amps_dict, C_baseline)
    print(f'  Alpha range: {min(hc_alpha_dict.values()):.1f} - '
          f'{max(hc_alpha_dict.values()):.1f}')

    # ------------------------------------------------------------------
    # 2. Compute observed ΔRDM
    # ------------------------------------------------------------------
    print('[2] Computing observed ΔRDM...')

    if metric == 'combination':
        delta_obs_corr, _, _ = compute_delta_rdm_obs(amp_cvd, hc_amps_dict, 'corr')
        delta_obs_cosine, _, _ = compute_delta_rdm_obs(amp_cvd, hc_amps_dict, 'cosine')
        delta_obs_triangle, _, _ = compute_delta_rdm_obs(amp_cvd, hc_amps_dict, 'triangle')
        delta_obs = None  # not used for combination
        print(f'  ΔRDM corr norm: {np.linalg.norm(delta_obs_corr):.4f}')
        print(f'  ΔRDM cosine norm: {np.linalg.norm(delta_obs_cosine):.4f}')
        print(f'  ΔRDM triangle norm: {np.linalg.norm(delta_obs_triangle):.4f}')
    else:
        delta_obs, rdm_cvd, rdm_hc_mean = compute_delta_rdm_obs(
            amp_cvd, hc_amps_dict, metric)
        delta_obs_corr = delta_obs_cosine = delta_obs_triangle = None
        print(f'  ΔRDM norm: {np.linalg.norm(delta_obs):.4f}')
        print(f'  ΔRDM range: [{delta_obs.min():.4f}, {delta_obs.max():.4f}]')

    # ------------------------------------------------------------------
    # Phase A: ΔRDM-based δ optimization
    # ------------------------------------------------------------------
    print(f'[A] Phase A: ΔRDM fitting (loss={loss_type})...')
    best_params, best_loss, best_pearson = fit_delta_rdm(
        model_name, cvd_type, hc_W_dict, C_baseline,
        delta_obs, metric,
        delta_obs_corr=delta_obs_corr,
        delta_obs_cosine=delta_obs_cosine,
        delta_obs_triangle=delta_obs_triangle,
        loss_type=loss_type,
        scale_lambda=scale_lambda,
    )
    print(f'  Best params: {best_params}')
    print(f'  Best Pearson r: {best_pearson:.4f}')
    if loss_type == 'pearson_scale':
        print(f'  Total loss (r + λ·scale): {best_loss:.4f}  (λ={scale_lambda})')

    # Permutation test
    print('[A+] Permutation test (8! = 40320)...')
    perm_p, obs_r = permutation_test_rdm(
        hc_W_dict, C_baseline, delta_obs, metric,
        best_params, model_name, cvd_type,
        delta_obs_corr=delta_obs_corr,
        delta_obs_cosine=delta_obs_cosine,
        delta_obs_triangle=delta_obs_triangle,
        loss_type=loss_type,
        scale_lambda=scale_lambda,
    )
    sig = '*' if perm_p < 0.05 else ''
    print(f'  Perm p = {perm_p:.4f}{sig}')

    # Compute hue shift in nm/degrees for reporting
    shifted_angles = apply_distortion(model_name, best_params, cvd_type=cvd_type)
    delta_theta = shifted_angles - np.array([0, 45, 90, 135, 180, 225, 270, 315],
                                             dtype=float)
    delta_theta = (delta_theta + 180) % 360 - 180

    # ------------------------------------------------------------------
    # Phase B: Synthetic data generation
    # ------------------------------------------------------------------
    print('[B] Phase B: Generating synthetic CVD-like data...')
    syn_data = generate_synthetic_data(
        hc_W_dict, hc_amps_dict, best_params, model_name, cvd_type)
    per_hc_shapes = {
        subj: tuple(arr.shape) for subj, arr in syn_data['per_hc_mean'].items()
    }
    print(f'  per-HC synthetic mean shapes: {per_hc_shapes}')
    if syn_data['mean_w_available']:
        mean_w_mean_stack = np.stack(list(syn_data['mean_w_mean'].values()), axis=0)
        print(f'  mean-W synthetic mean stack: {mean_w_mean_stack.shape}')
        print(f'  W_mean shape: {syn_data["W_mean"].shape}')
    else:
        mean_w_mean_stack = None
        print(f'  mean-W synthetic data unavailable: {syn_data["mean_w_reason"]}')
        print(f'  HC W shapes: {syn_data["w_shapes"]}')

    # ------------------------------------------------------------------
    # Phase C: LOCO on synthetic data
    # ------------------------------------------------------------------
    print('[C] Phase C: LOCO on synthetic data...')
    C_shifted = syn_data['C_shifted']
    vuln_synthetic_per_hc, per_hc_loco = loco_on_synthetic_group(
        syn_data['per_hc_runs'], C_shifted)
    print(f'  Synthetic LOCO (per-HC W): {np.array2string(vuln_synthetic_per_hc, precision=3)}')
    if syn_data['mean_w_available']:
        vuln_synthetic_mean_w, mean_w_loco = loco_on_synthetic_group(
            syn_data['mean_w_runs'], C_shifted)
        print(f'  Synthetic LOCO (mean W):   {np.array2string(vuln_synthetic_mean_w, precision=3)}')
    else:
        vuln_synthetic_mean_w = None
        mean_w_loco = {}

    # Load observed LOCO
    try:
        vuln_observed = load_cvd_loco_observed(sub_id, roi)
        print(f'  Observed LOCO:  {np.array2string(vuln_observed, precision=3)}')
    except (FileNotFoundError, ValueError) as e:
        print(f'  WARNING: Could not load observed LOCO: {e}')
        vuln_observed = None

    # Compare synthetic vs observed LOCO
    loco_match_per_hc = summarize_loco_match(vuln_synthetic_per_hc, vuln_observed)
    loco_match_mean_w = (
        summarize_loco_match(vuln_synthetic_mean_w, vuln_observed)
        if vuln_synthetic_mean_w is not None else {}
    )

    if vuln_observed is not None:
        for label, match in [('per-HC W', loco_match_per_hc)]:
            sig_c = '*' if match.get('perm_p', 1.0) < 0.05 else ''
            print(f'  LOCO match ({label}): ρ={match["spearman_rho"]:.3f}, '
                  f'perm_p={match["perm_p"]:.4f}{sig_c}')
            print(f'    Worst 3 syn: {match["worst3_synthetic"]}')
            print(f'    Worst 3 obs: {match["worst3_observed"]}')
            print(f'    Overlap: {match["worst3_overlap"]}/3')
        if syn_data['mean_w_available']:
            match = loco_match_mean_w
            sig_c = '*' if match.get('perm_p', 1.0) < 0.05 else ''
            print(f'  LOCO match (mean W): ρ={match["spearman_rho"]:.3f}, '
                  f'perm_p={match["perm_p"]:.4f}{sig_c}')
            print(f'    Worst 3 syn: {match["worst3_synthetic"]}')
            print(f'    Worst 3 obs: {match["worst3_observed"]}')
            print(f'    Overlap: {match["worst3_overlap"]}/3')
        else:
            print(f'  LOCO match (mean W): skipped — {syn_data["mean_w_reason"]}')

    profile_delta = (
        vuln_synthetic_per_hc - vuln_synthetic_mean_w
        if vuln_synthetic_mean_w is not None else None
    )

    # ------------------------------------------------------------------
    # Save results
    # ------------------------------------------------------------------
    elapsed = (datetime.now() - t0).total_seconds()

    config = {
        'subject': f'sub-{sub_id}',
        'cvd_type': cvd_type,
        'roi': roi,
        'model': model_name,
        'model_df': MODELS[model_name]['df'],
        'metric': metric,
        'n_hc': len(hc_amps_dict),
        'n_voxels': int(amp_cvd.shape[2]),
        'n_channels': N_CHANNELS,
        'timestamp': datetime.now().isoformat(),
        'elapsed_sec': round(elapsed, 1),
    }

    result = {
        'phase_a': {
            'best_params': best_params,
            'best_pearson_r': best_pearson,
            'perm_p': perm_p,
            'delta_theta_deg': delta_theta.tolist(),
            'significant': perm_p < 0.05,
            'loss_type': loss_type,
            'scale_lambda': scale_lambda if loss_type == 'pearson_scale' else None,
            'total_loss': best_loss,
        },
        'phase_b': {
            'primary_mode': 'per_hc',
            'mean_w_available': syn_data['mean_w_available'],
            'mean_w_reason': syn_data['mean_w_reason'],
            'w_shapes': syn_data['w_shapes'],
            'w_mean_norm': (
                float(np.linalg.norm(syn_data['W_mean']))
                if syn_data['W_mean'] is not None else None
            ),
            'per_hc': {
                'synthetic_mean_norm_mean': float(np.mean([
                    np.linalg.norm(arr) for arr in syn_data['per_hc_mean'].values()
                ])),
                'synthetic_mean_norms': {
                    subj: float(np.linalg.norm(arr))
                    for subj, arr in syn_data['per_hc_mean'].items()
                },
            },
            'mean_w': {
                'synthetic_mean_norm': (
                    float(np.linalg.norm(mean_w_mean_stack[0]))
                    if mean_w_mean_stack is not None else None
                ),
                'n_residual_subjects': len(syn_data['mean_w_runs']),
            },
            'synthetic_mean_norm': float(np.mean([
                np.linalg.norm(arr) for arr in syn_data['per_hc_mean'].values()
            ])),
        },
        'phase_c': {
            'primary_mode': 'per_hc',
            'vuln_synthetic': vuln_synthetic_per_hc.tolist(),
            'vuln_observed': vuln_observed.tolist() if vuln_observed is not None else None,
            'loco_match': loco_match_per_hc,
            'per_hc': {
                'vuln_synthetic': vuln_synthetic_per_hc.tolist(),
                'per_subject': per_hc_loco,
                'loco_match': loco_match_per_hc,
            },
            'mean_w': {
                'vuln_synthetic': (
                    vuln_synthetic_mean_w.tolist()
                    if vuln_synthetic_mean_w is not None else None
                ),
                'per_subject': mean_w_loco,
                'loco_match': loco_match_mean_w,
            },
            'comparison': {
                'profile_delta_per_hc_minus_mean_w': (
                    profile_delta.tolist() if profile_delta is not None else None
                ),
                'mean_abs_profile_delta': (
                    float(np.mean(np.abs(profile_delta)))
                    if profile_delta is not None else None
                ),
            },
        },
        'color_names': COLOR_NAMES,
    }

    with open(out_path / 'config.json', 'w') as f:
        json.dump(config, f, indent=2)

    with open(out_path / 'result.json', 'w') as f:
        json.dump(result, f, indent=2)

    print(f'\nDone in {elapsed:.1f}s. Saved to {out_path}/')
    return config, result


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Geometry→Function simulation')
    parser.add_argument('--sub', required=True, choices=['08', '09'],
                        help='CVD subject ID')
    parser.add_argument('--roi', required=True, choices=['V1', 'V2'],
                        help='ROI')
    parser.add_argument('--model', required=True,
                        choices=['cone_1way', 'cone_3way', 'fourier'],
                        help='Distortion model')
    parser.add_argument('--metric', required=True,
                        choices=['corr', 'cosine', 'triangle', 'combination'],
                        help='RDM distance metric')
    parser.add_argument('--loss', default='pearson',
                        choices=['pearson', 'pearson_scale'],
                        help='Phase A loss function (default: pearson)')
    parser.add_argument('--scale_lambda', type=float, default=0.1,
                        help='Scale penalty weight for pearson_scale loss')
    parser.add_argument('--output_dir', default='results/sim',
                        help='Output directory')
    args = parser.parse_args()

    run_pipeline(args.sub, args.roi, args.model, args.metric, args.output_dir,
                 loss_type=args.loss, scale_lambda=args.scale_lambda)


if __name__ == '__main__':
    main()
