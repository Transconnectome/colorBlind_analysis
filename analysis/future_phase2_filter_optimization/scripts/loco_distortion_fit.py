#!/usr/bin/env python3
"""
loco_distortion_fit.py — Phase A: Fit distortion to CVD LOCO vulnerability profile.

Fits a smooth distortion field δ(c) that reproduces the observed CVD per-color
LOCO vulnerability using shift_at_both LOCO simulation at hV4.

Loss:  L_fit = α·L_vuln + β·L_rank + δ·L_rdm + ε·L_smooth
       (minimize — target = CVD vulnerability, NOT HC recovery)

Models:
  machado_1way  (1 DOF): Machado 2009 Δλ, α coupled
  rc_opponent   (2 DOF): Machado Δλ + R-G opponent gain g
  2component    (2 DOF): β_s (S-cone) + β_c (confusion axis) angular dilation
  fourier_warp  (4 DOF): δ(θ) = a₁sin(θ) + b₁cos(θ) + a₂sin(2θ) + b₂cos(2θ)

Usage (server):
    mpirun -np 1 python scripts/loco_distortion_fit.py \
        --subject 08 --roi V4 --method shift_at_both \
        --data_dir /scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010 \
        --output_dir results/loco_filter/phase_a

Usage (local — slower, for debugging):
    python scripts/loco_distortion_fit.py --subject 08 --roi V4 --method w_fixed
"""

import argparse
import json
import numpy as np
import sys
import time
from datetime import datetime
from itertools import permutations
from pathlib import Path
from scipy.optimize import minimize, differential_evolution
from scipy.stats import spearmanr

# ---------------------------------------------------------------------------
# Path setup (same pattern as existing pipeline scripts)
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
_PHASE2_DIR = _SCRIPT_DIR.parent
sys.path.insert(0, str(_SCRIPT_DIR))

for _base in [_PHASE2_DIR.parent, _PHASE2_DIR.parent.parent]:
    _fwd = _base / 'future_phase1_forward_model' / 'scripts'
    if _fwd.exists() and str(_fwd) not in sys.path:
        sys.path.insert(0, str(_fwd))
        break

from utils_forward_model import (
    HC_SUBJECTS, CVD_SUBJECTS, N_CHANNELS, N_RUNS, N_COLORS,
    HUE_ANGLES, load_amplitudes, create_basis_full,
    gcv_select_alpha, fit_W_ridge, voxel_pattern_correlation,
)
from utils_distortion_models import get_design_matrix, MODELS
from machado_simulator import machado_shifted_hue
from retinal_cortical import machado_with_opponent_gain
from step1_fit_loco_v2 import (
    simulate_mean_hc_loco_legacy,
    simulate_mean_hc_wfixed,
    precompute_hc_W,
    load_cvd_loco_target,
    permutation_test_spearman,
    mse_decompose, lins_ccc,
)
from diagnostic_delta_rdm import (
    compute_delta_rdm_obs,
    compute_delta_rdm_sim,
    cosine_similarity,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CVD_TYPE = {'08': 'deutan', '09': 'protan', '10': 'normal'}
CONF_AXIS = {'protan': 16.0, 'deutan': 150.0, 'normal': 83.0}  # Stockman confusion axes
HUE_ANGLES_FLOAT = np.array([0, 45, 90, 135, 180, 225, 270, 315], dtype=float)

LOCAL_DATA = (_PHASE2_DIR.parent / 'phase1_procrustes_decoding' / 'results'
              / 'visualization' / 'full_dataset_C010_with_residuals')
SERVER_DATA = Path(
    '/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010')

# Default fit weights  (L_fit = α·L_vuln + β·L_rank + δ·L_rdm + ε·L_smooth)
# All loss terms are normalized to [0, 1] so weights are directly interpretable:
#   α=1.0 means "L_vuln is as important as 1 unit of L_rank at β=1.0"
DEFAULT_WEIGHTS = {'alpha': 1.0, 'beta': 0.5, 'delta': 0.2, 'epsilon': 0.1}

# Normalization constants (map raw terms → [0, 1])
#   L_vuln: MSE of correlations ∈ [-1,1] → max raw ≈ 4.0, typical ≈ 0.5
#   L_rank: 1 - ρ ∈ [0, 2]
#   L_rdm:  1 - cos ∈ [0, 2]
#   L_smooth: mean(Δdeg²), max adjacent diff = 180° → max raw = 180² = 32400
NORM = {
    'vuln': 4.0,      # max MSE when correlations span [-1, 1]
    'rank': 2.0,      # max of (1 - Spearman ρ)
    'rdm': 2.0,       # max of (1 - cosine)
    'smooth': 32400.0, # 180² — max possible circular adjacent-diff²
}

# ---------------------------------------------------------------------------
# Extended model interface (adds R+C and Fourier to existing Machado)
# ---------------------------------------------------------------------------

FILTER_MODELS = {
    'machado_1way': {
        'df': 1,
        'bounds': [(0.0, 20.0)],
        'grid_step': [0.5],
        'description': 'Machado 2009 Δλ only (α coupled)',
    },
    'rc_opponent': {
        'df': 2,
        'bounds': [(0.0, 20.0), (-3.0, 3.0)],
        'grid_step': [0.5, 0.25],
        'description': 'Machado Δλ + opponent R-G gain g',
    },
    'fourier_warp': {
        'df': 4,
        'bounds': [(-30.0, 30.0)] * 4,
        'grid_step': None,  # use differential evolution
        'description': 'Fourier: a₁sin + b₁cos + a₂sin(2θ) + b₂cos(2θ)',
    },
    '2component': {
        'df': 2,
        'bounds': [(0.0, 50.0), (-50.0, 50.0)],
        'grid_step': [2.0, 2.0],
        'description': '2-Component angular dilation: β_s (S-cone) + β_c (confusion axis)',
    },
}


def get_shifted_design(model_name, params, cvd_type, n_channels=N_CHANNELS):
    """Unified design matrix from model parameters.

    Returns:
        C_shifted: (8, K) design matrix at shifted hue angles
        delta_theta: (8,) per-color hue shift in degrees
    """
    if model_name == 'machado_1way':
        C = get_design_matrix('machado_1way', params, cvd_type=cvd_type,
                              n_channels=n_channels)
        _, _, dt = machado_shifted_hue(float(params[0]), cvd_type)
        return C, dt

    elif model_name == 'rc_opponent':
        dl, g = float(params[0]), float(params[1])
        _, hue_final, dt = machado_with_opponent_gain(dl, g, cvd_type)
        basis_full = create_basis_full(n_channels, basis_type='fe')
        idx = np.round(hue_final).astype(int) % 360
        return basis_full[idx], dt

    elif model_name == 'fourier_warp':
        a1, b1, a2, b2 = [float(p) for p in params]
        theta_rad = np.deg2rad(HUE_ANGLES_FLOAT)
        delta = (a1 * np.sin(theta_rad) + b1 * np.cos(theta_rad)
                 + a2 * np.sin(2 * theta_rad) + b2 * np.cos(2 * theta_rad))
        shifted = (HUE_ANGLES_FLOAT + delta) % 360
        basis_full = create_basis_full(n_channels, basis_type='fe')
        idx = np.round(shifted).astype(int) % 360
        dt = (delta + 180) % 360 - 180
        return basis_full[idx], dt

    elif model_name == '2component':
        bs, bc = float(params[0]), float(params[1])
        hue_base, _, _ = machado_shifted_hue(0.0, cvd_type)
        theta_conf = CONF_AXIS[cvd_type]
        dt = (bs * np.cos(np.radians(hue_base - 90.0))
              + bc * np.cos(np.radians(hue_base - theta_conf)))
        hue_shifted = (hue_base + dt) % 360.0
        basis_full = create_basis_full(n_channels, basis_type='fe')
        idx = np.round(hue_shifted).astype(int) % 360
        return basis_full[idx], dt

    else:
        raise ValueError(f'Unknown model: {model_name}')


# ---------------------------------------------------------------------------
# Multi-objective distortion fit loss
# ---------------------------------------------------------------------------

def compute_fit_loss(vuln_sim, vuln_cvd, delta_theta,
                     delta_rdm_sim=None, delta_rdm_obs=None,
                     weights=None):
    """Compute L_fit = α·L_vuln + β·L_rank + δ·L_rdm + ε·L_smooth.

    Args:
        vuln_sim: (8,) simulated HC vulnerability at shifted angles
        vuln_cvd: (8,) observed CVD vulnerability (target)
        delta_theta: (8,) per-color hue shift in degrees
        delta_rdm_sim: (28,) optional simulated ΔRDM
        delta_rdm_obs: (28,) optional observed ΔRDM
        weights: dict with keys alpha, beta, delta, epsilon

    Returns:
        dict with l_fit, l_vuln, l_rank, l_rdm, l_smooth, spearman_r
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS

    # L_vuln: MSE between simulated and observed vulnerability
    l_vuln_raw = float(np.mean((vuln_sim - vuln_cvd) ** 2))
    l_vuln = l_vuln_raw / NORM['vuln']

    # L_rank: 1 - Spearman ρ
    rho, _ = spearmanr(vuln_sim, vuln_cvd)
    if not np.isfinite(rho):
        rho = 0.0
    l_rank_raw = 1.0 - rho
    l_rank = l_rank_raw / NORM['rank']

    # L_rdm: 1 - cosine(ΔRDM_sim, ΔRDM_obs)
    if delta_rdm_sim is not None and delta_rdm_obs is not None:
        cos_sim = cosine_similarity(delta_rdm_sim, delta_rdm_obs)
        if not np.isfinite(cos_sim):
            cos_sim = 0.0
        l_rdm_raw = 1.0 - cos_sim
    else:
        l_rdm_raw = 0.0
        cos_sim = np.nan
    l_rdm = l_rdm_raw / NORM['rdm']

    # L_smooth: adjacent-color hue shift difference squared
    dt = np.asarray(delta_theta)
    diffs = np.diff(dt, append=dt[0])
    diffs = (diffs + 180) % 360 - 180  # wrap
    l_smooth_raw = float(np.mean(diffs ** 2))
    l_smooth = l_smooth_raw / NORM['smooth']

    # Total (all terms now in [0, 1], weights are directly interpretable)
    l_fit = (weights['alpha'] * l_vuln
             + weights['beta'] * l_rank
             + weights.get('delta', 0.2) * l_rdm
             + weights.get('epsilon', 0.1) * l_smooth)

    return {
        'l_fit': float(l_fit),
        'l_vuln': float(l_vuln),
        'l_rank': float(l_rank),
        'l_rdm': float(l_rdm),
        'l_smooth': float(l_smooth),
        'l_vuln_raw': float(l_vuln_raw),
        'l_rank_raw': float(l_rank_raw),
        'l_rdm_raw': float(l_rdm_raw),
        'l_smooth_raw': float(l_smooth_raw),
        'spearman_r': float(rho),
        'rdm_cosine': float(cos_sim) if np.isfinite(cos_sim) else None,
    }


# ---------------------------------------------------------------------------
# Grid search (1D and 2D)
# ---------------------------------------------------------------------------

def grid_search(model_name, hc_amps_dict, vuln_cvd, cvd_type,
                method='shift_at_both',
                hc_W_dict=None, delta_rdm_obs=None,
                weights=None, verbose=True):
    """Exhaustive grid search for low-DOF models.

    Args:
        model_name: 'machado_1way' or 'rc_opponent'
        hc_amps_dict: {subj: (6, 8, V_s)} HC amplitudes
        vuln_cvd: (8,) CVD vulnerability target
        cvd_type: 'deutan', 'protan', or 'normal'
        method: 'shift_at_both' or 'w_fixed'
        hc_W_dict: precomputed W (needed for w_fixed and L_rdm)
        delta_rdm_obs: (28,) observed ΔRDM (optional, for L_rdm)
        weights: loss weights dict
        verbose: print progress

    Returns:
        dict with best_params, best_loss, landscape, etc.
    """
    model_info = FILTER_MODELS[model_name]
    bounds = model_info['bounds']
    steps = model_info['grid_step']

    # Build grid axes
    axes = []
    for (lo, hi), step in zip(bounds, steps):
        axes.append(np.arange(lo, hi + step * 0.5, step))

    if len(axes) == 1:
        grid = [(x,) for x in axes[0]]
    elif len(axes) == 2:
        grid = [(x, y) for x in axes[0] for y in axes[1]]
    else:
        raise ValueError(f'Grid search not supported for {len(axes)}-DOF')

    if verbose:
        print(f'[{model_name}] Grid: {len(grid)} points, method={method}')

    # Precompute C_baseline for ΔRDM
    basis_full = create_basis_full(N_CHANNELS, basis_type='fe')
    C_baseline = basis_full[HUE_ANGLES]

    landscape = []
    best_loss = np.inf
    best_entry = None
    t0 = time.time()

    for i, params in enumerate(grid):
        params_arr = np.array(params)

        # Get shifted design matrix
        C_shifted, delta_theta = get_shifted_design(
            model_name, params_arr, cvd_type)

        # LOCO simulation
        if method == 'shift_at_both':
            vuln_sim, _ = simulate_mean_hc_loco_legacy(hc_amps_dict, C_shifted)
        else:
            vuln_sim, _ = simulate_mean_hc_wfixed(
                hc_W_dict, hc_amps_dict, C_shifted)

        # ΔRDM (always W-fixed for consistency)
        drdm_sim = None
        if delta_rdm_obs is not None and hc_W_dict is not None:
            drdm_sim_mean, _ = compute_delta_rdm_sim(
                hc_W_dict, C_shifted, C_baseline)
            drdm_sim = drdm_sim_mean

        # Compute loss
        loss = compute_fit_loss(vuln_sim, vuln_cvd, delta_theta,
                                drdm_sim, delta_rdm_obs, weights)

        entry = {
            'params': params_arr.tolist(),
            'vuln_sim': vuln_sim.tolist(),
            'delta_theta': delta_theta.tolist(),
            **loss,
        }
        landscape.append(entry)

        if loss['l_fit'] < best_loss:
            best_loss = loss['l_fit']
            best_entry = entry

        if verbose and (i + 1) % max(1, len(grid) // 10) == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            print(f'  [{i+1}/{len(grid)}] best L_fit={best_loss:.4f} '
                  f'ρ={best_entry["spearman_r"]:.3f} '
                  f'({rate:.1f} eval/s)')

    elapsed = time.time() - t0
    if verbose:
        print(f'  Done in {elapsed:.1f}s. '
              f'Best: params={best_entry["params"]}, '
              f'L_fit={best_loss:.4f}, ρ={best_entry["spearman_r"]:.3f}')

    return {
        'model': model_name,
        'method': method,
        'best_params': best_entry['params'],
        'best_loss': best_entry,
        'landscape': landscape,
        'n_evaluations': len(grid),
        'elapsed_s': elapsed,
        'weights': weights or DEFAULT_WEIGHTS,
    }


# ---------------------------------------------------------------------------
# Differential Evolution optimizer (for Fourier 4-DOF)
# ---------------------------------------------------------------------------

def optimize_de(model_name, hc_amps_dict, vuln_cvd, cvd_type,
                method='shift_at_both',
                hc_W_dict=None, delta_rdm_obs=None,
                weights=None, verbose=True,
                n_restarts=3, maxiter=80, popsize=12, seed=42):
    """Differential Evolution for higher-DOF models (Fourier warp).

    Runs multiple restarts and returns the best solution.
    DE is gradient-free, so it works with the non-smooth shift_at_both
    landscape where L-BFGS-B fails.
    """
    model_info = FILTER_MODELS[model_name]
    bounds = model_info['bounds']

    basis_full = create_basis_full(N_CHANNELS, basis_type='fe')
    C_baseline = basis_full[HUE_ANGLES]

    n_eval = [0]

    def objective(params):
        C_shifted, delta_theta = get_shifted_design(
            model_name, params, cvd_type)
        if method == 'shift_at_both':
            vuln_sim, _ = simulate_mean_hc_loco_legacy(
                hc_amps_dict, C_shifted)
        else:
            vuln_sim, _ = simulate_mean_hc_wfixed(
                hc_W_dict, hc_amps_dict, C_shifted)

        drdm_sim = None
        if delta_rdm_obs is not None and hc_W_dict is not None:
            drdm_sim_mean, _ = compute_delta_rdm_sim(
                hc_W_dict, C_shifted, C_baseline)
            drdm_sim = drdm_sim_mean

        loss = compute_fit_loss(vuln_sim, vuln_cvd, delta_theta,
                                drdm_sim, delta_rdm_obs, weights)
        n_eval[0] += 1
        return loss['l_fit']

    if verbose:
        print(f'[{model_name}] DE: {n_restarts} restarts, '
              f'maxiter={maxiter}, popsize={popsize}, bounds={bounds}')

    best_result = None
    best_fun = np.inf
    t0 = time.time()

    for restart in range(n_restarts):
        n_eval[0] = 0
        rs = seed + restart * 1000

        def callback(xk, convergence):
            if verbose:
                print(f'  [restart {restart+1}, gen {callback.gen}, '
                      f'{n_eval[0]} evals] convergence={convergence:.4f}')
                callback.gen += 1
        callback.gen = 1

        res = differential_evolution(
            objective, bounds=bounds,
            maxiter=maxiter, popsize=popsize,
            tol=1e-6, atol=1e-8,
            seed=rs, mutation=(0.5, 1.0), recombination=0.7,
            callback=callback if verbose else None,
            polish=True)  # L-BFGS-B polish at end (now near optimum)

        if verbose:
            print(f'  Restart {restart+1}: fun={res.fun:.4f}, '
                  f'params={np.round(res.x, 2).tolist()}, '
                  f'{n_eval[0]} evals, success={res.success}')

        if res.fun < best_fun:
            best_fun = res.fun
            best_result = res

    elapsed = time.time() - t0

    # Compute final loss at best optimum
    C_shifted, delta_theta = get_shifted_design(
        model_name, best_result.x, cvd_type)
    if method == 'shift_at_both':
        vuln_sim, _ = simulate_mean_hc_loco_legacy(hc_amps_dict, C_shifted)
    else:
        vuln_sim, _ = simulate_mean_hc_wfixed(
            hc_W_dict, hc_amps_dict, C_shifted)

    drdm_sim = None
    if delta_rdm_obs is not None and hc_W_dict is not None:
        drdm_sim_mean, _ = compute_delta_rdm_sim(
            hc_W_dict, C_shifted, C_baseline)
        drdm_sim = drdm_sim_mean

    best_loss = compute_fit_loss(vuln_sim, vuln_cvd, delta_theta,
                                 drdm_sim, delta_rdm_obs, weights)

    if verbose:
        print(f'  Best across {n_restarts} restarts: '
              f'params={np.round(best_result.x, 2).tolist()}, '
              f'L_fit={best_loss["l_fit"]:.4f}, '
              f'ρ={best_loss["spearman_r"]:.3f} '
              f'({elapsed:.1f}s total)')

    return {
        'model': model_name,
        'method': method,
        'best_params': best_result.x.tolist(),
        'best_loss': {
            'params': best_result.x.tolist(),
            'vuln_sim': vuln_sim.tolist(),
            'delta_theta': delta_theta.tolist(),
            **best_loss,
        },
        'landscape': None,  # no landscape for DE
        'n_evaluations': best_result.nfev,
        'n_restarts': n_restarts,
        'elapsed_s': elapsed,
        'optimizer_success': bool(best_result.success),
        'optimizer_message': str(best_result.message),
        'weights': weights or DEFAULT_WEIGHTS,
    }


# ---------------------------------------------------------------------------
# Permutation tests
# ---------------------------------------------------------------------------

def run_permutation_tests(best_vuln_sim, vuln_cvd, n_perm=50000):
    """Run exact 8! permutation tests on the best fit.

    Returns dict with label_perm_p, spearman_r.
    """
    perm_p, null, rho_obs = permutation_test_spearman(
        best_vuln_sim, vuln_cvd, n_perm=n_perm)

    # MSE permutation
    mse_obs = float(np.mean((best_vuln_sim - vuln_cvd) ** 2))
    null_mse = []
    for perm in permutations(range(8)):
        cvd_perm = vuln_cvd[list(perm)]
        null_mse.append(float(np.mean((best_vuln_sim - cvd_perm) ** 2)))
    null_mse = np.array(null_mse)
    mse_p = float((np.sum(null_mse <= mse_obs) + 1) / (len(null_mse) + 1))

    # CCC and MSE decomposition
    mse, bias_sq, profile_mse = mse_decompose(best_vuln_sim, vuln_cvd)
    ccc = lins_ccc(best_vuln_sim, vuln_cvd)

    return {
        'label_perm_p': float(perm_p),
        'spearman_r': float(rho_obs),
        'mse_perm_p': float(mse_p),
        'mse': float(mse),
        'bias_sq': float(bias_sq),
        'profile_mse': float(profile_mse),
        'ccc': float(ccc),
        'null_rho_mean': float(np.mean(null)),
        'null_rho_std': float(np.std(null)),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Phase A: Fit distortion to CVD LOCO vulnerability')
    parser.add_argument('--subject', required=True,
                        help='CVD subject ID (08, 09, or 10)')
    parser.add_argument('--roi', default='V4',
                        help='ROI (V4 for hV4, V1, V2)')
    parser.add_argument('--method', default='shift_at_both',
                        choices=['shift_at_both', 'w_fixed'],
                        help='LOCO simulation method')
    parser.add_argument('--models', nargs='+',
                        default=['machado_1way', 'rc_opponent', 'fourier_warp'],
                        help='Models to fit')
    parser.add_argument('--data_dir', default=None,
                        help='Path to C010 data (auto-detect if omitted)')
    parser.add_argument('--output_dir', default='results/loco_filter/phase_a',
                        help='Output directory')
    parser.add_argument('--weights', nargs=4, type=float,
                        default=None, metavar=('A', 'B', 'D', 'E'),
                        help='Loss weights: alpha beta delta epsilon')
    parser.add_argument('--skip_rdm', action='store_true',
                        help='Skip L_rdm computation (faster)')
    args = parser.parse_args()

    subj = args.subject
    roi = args.roi
    cvd_type = CVD_TYPE[subj]
    weights = DEFAULT_WEIGHTS.copy()
    if args.weights:
        weights['alpha'] = args.weights[0]
        weights['beta'] = args.weights[1]
        weights['delta'] = args.weights[2]
        weights['epsilon'] = args.weights[3]
    if args.skip_rdm:
        weights['delta'] = 0.0

    # --- Auto-detect data path ---
    if args.data_dir:
        data_dir = Path(args.data_dir)
    elif SERVER_DATA.exists():
        data_dir = SERVER_DATA
    elif LOCAL_DATA.exists():
        data_dir = LOCAL_DATA
    else:
        # Fallback to old local path
        old_local = (_PHASE2_DIR.parent / 'phase1_preprocess_decoding' / 'results'
                     / 'full_dataset_C010')
        if old_local.exists():
            data_dir = old_local
        else:
            raise FileNotFoundError(
                'Cannot find C010 data. Specify --data_dir.')
    print(f'Data: {data_dir}')
    print(f'Subject: sub-{subj} ({cvd_type}), ROI: {roi}')
    print(f'Method: {args.method}, Models: {args.models}')
    print(f'Weights: {weights}')

    # --- Step 0: Load data ---
    print('\n=== STEP 0: Data loading ===')
    t0 = time.time()

    # HC amplitudes
    hc_amps_dict = {}
    for hc in HC_SUBJECTS:
        hc_amps_dict[hc] = load_amplitudes(data_dir, hc, roi)
    print(f'  Loaded {len(hc_amps_dict)} HC subjects '
          f'(V_s={hc_amps_dict["01"].shape[2]})')

    # CVD LOCO target
    vuln_cvd = load_cvd_loco_target(subj, roi)
    print(f'  CVD target: {np.round(vuln_cvd, 3).tolist()}')

    # Precompute W for W-fixed LOCO and ΔRDM
    basis_full = create_basis_full(N_CHANNELS, basis_type='fe')
    C_original = basis_full[HUE_ANGLES]
    hc_W_dict, hc_alpha_dict = precompute_hc_W(hc_amps_dict, C_original)
    print(f'  Precomputed W for {len(hc_W_dict)} HC subjects')

    # ΔRDM observed (optional)
    delta_rdm_obs = None
    if not args.skip_rdm:
        cvd_amp = load_amplitudes(data_dir, subj, roi)
        delta_rdm_obs, _, _, _ = compute_delta_rdm_obs(
            cvd_amp, hc_amps_dict)
        print(f'  ΔRDM_obs computed (28 elements)')

    # Baseline vulnerability (δ=0)
    if args.method == 'shift_at_both':
        vuln_baseline, _ = simulate_mean_hc_loco_legacy(
            hc_amps_dict, C_original)
    else:
        vuln_baseline, _ = simulate_mean_hc_wfixed(
            hc_W_dict, hc_amps_dict, C_original)
    rho_baseline, _ = spearmanr(vuln_baseline, vuln_cvd)
    print(f'  Baseline ρ(δ=0) = {rho_baseline:.3f}')
    print(f'  Baseline vuln: {np.round(vuln_baseline, 3).tolist()}')
    print(f'  Step 0 done in {time.time() - t0:.1f}s')

    # --- Steps 1-3: Fit each model ---
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    all_results = {}
    for model_name in args.models:
        if model_name not in FILTER_MODELS:
            print(f'\n  WARNING: Unknown model {model_name}, skipping')
            continue

        print(f'\n=== STEP 1-3: Fitting {model_name} ===')

        if FILTER_MODELS[model_name]['grid_step'] is not None:
            result = grid_search(
                model_name, hc_amps_dict, vuln_cvd, cvd_type,
                method=args.method,
                hc_W_dict=hc_W_dict, delta_rdm_obs=delta_rdm_obs,
                weights=weights)
        else:
            result = optimize_de(
                model_name, hc_amps_dict, vuln_cvd, cvd_type,
                method=args.method,
                hc_W_dict=hc_W_dict, delta_rdm_obs=delta_rdm_obs,
                weights=weights)

        # Permutation test at best point
        print(f'\n  Running permutation tests...')
        best_vuln = np.array(result['best_loss']['vuln_sim'])
        perm = run_permutation_tests(best_vuln, vuln_cvd)
        result['permutation'] = perm
        print(f'  label_perm_p = {perm["label_perm_p"]:.4f}, '
              f'ρ = {perm["spearman_r"]:.3f}, '
              f'CCC = {perm["ccc"]:.3f}')

        # Baseline comparison
        result['baseline'] = {
            'vuln_baseline': vuln_baseline.tolist(),
            'spearman_r_baseline': float(rho_baseline)
                if np.isfinite(rho_baseline) else 0.0,
            'delta_rho': float(perm['spearman_r'] - rho_baseline)
                if np.isfinite(rho_baseline) else float(perm['spearman_r']),
        }

        all_results[model_name] = result

        # Save per-model result
        save_path = output_dir / f'sub-{subj}_{roi}_{model_name}.json'
        # Strip landscape for compact output (save separately if needed)
        result_compact = {k: v for k, v in result.items() if k != 'landscape'}
        with open(save_path, 'w') as f:
            json.dump(result_compact, f, indent=2, default=str)
        print(f'  Saved: {save_path}')

        # Save full landscape separately
        if result.get('landscape'):
            land_path = output_dir / f'sub-{subj}_{roi}_{model_name}_landscape.json'
            with open(land_path, 'w') as f:
                json.dump(result['landscape'], f, default=str)
            print(f'  Landscape: {land_path}')

    # --- Summary ---
    print('\n' + '=' * 70)
    print('PHASE A SUMMARY')
    print('=' * 70)
    print(f'Subject: sub-{subj} ({cvd_type}), ROI: {roi}, '
          f'Method: {args.method}')
    print(f'Baseline ρ(δ=0) = {rho_baseline:.3f}')
    print(f'{"Model":<18} {"ρ":>6} {"Δρ":>6} {"perm_p":>8} '
          f'{"L_fit":>7} {"params"}')
    print('-' * 70)
    for model_name, res in all_results.items():
        bl = res['best_loss']
        pm = res['permutation']
        base = res['baseline']
        sig = '*' if pm['label_perm_p'] < 0.05 else (
              't' if pm['label_perm_p'] < 0.10 else ' ')
        print(f'{model_name:<18} {pm["spearman_r"]:>6.3f} '
              f'{base["delta_rho"]:>+6.3f} '
              f'{pm["label_perm_p"]:>7.4f}{sig} '
              f'{bl["l_fit"]:>7.4f} '
              f'{bl["params"]}')

    # Save manifest
    manifest = {
        'subject': subj,
        'cvd_type': cvd_type,
        'roi': roi,
        'method': args.method,
        'weights': weights,
        'baseline_rho': float(rho_baseline) if np.isfinite(rho_baseline) else 0.0,
        'vuln_cvd': vuln_cvd.tolist(),
        'vuln_baseline': vuln_baseline.tolist(),
        'models': list(all_results.keys()),
        'data_dir': str(data_dir),
        'timestamp': datetime.now().isoformat(),
    }
    with open(output_dir / f'sub-{subj}_{roi}_manifest.json', 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f'\nAll results saved to {output_dir}/')
    return all_results


if __name__ == '__main__':
    main()
