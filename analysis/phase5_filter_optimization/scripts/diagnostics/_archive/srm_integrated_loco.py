#!/usr/bin/env python3
"""
srm_integrated_loco.py — hV4 Procrustes LOCO + V1/V2 SRM ΔRDM (cross-ROI).

This implements the intended cross-ROI design:
  - LOCO vulnerability from hV4 Procrustes (w_fixed method)
  - L_rdm from V1/V2 SRM-space ΔRDM (averaged: 0.5*V1 + 0.5*V2)

Requires step0_srm_precompute.py to have been run first.

Loss: L_fit = α·L_vuln + β·L_rank + δ·L_rdm + ε·L_smooth
  where L_rdm = 1 - cosine(ΔRDM_sim_srm, ΔRDM_obs_srm)
  and ΔRDM is averaged across V1 and V2 SRM spaces.

Models: machado_1way, rc_opponent, 2component, fourier_warp
Subjects: sub-08, sub-09, sub-10
Families: protan, deutan

Usage:
    python scripts/srm_integrated_loco.py \
        --srm_dir results/diagnostics/srm_precompute \
        --output_dir results/diagnostics/srm_integrated_loco
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

# ── Path resolution (fallback: tries analysis/ then parent of analysis/) ──
_SCRIPT_DIR = Path(__file__).resolve().parent
_PHASE2_DIR = _SCRIPT_DIR.parent
sys.path.insert(0, str(_SCRIPT_DIR.parent))

for _base in [_PHASE2_DIR.parent, _PHASE2_DIR.parent.parent]:
    _fwd = _base / 'phase4_forward_model' / 'scripts'
    if _fwd.exists() and str(_fwd) not in sys.path:
        sys.path.insert(0, str(_fwd))
        break

from utils_forward_model import (  # noqa: E402
    HC_SUBJECTS, CVD_SUBJECTS, N_CHANNELS, N_RUNS, N_COLORS,
    HUE_ANGLES, load_amplitudes, create_basis_full,
)
from loco_distortion_fit import (  # noqa: E402
    get_shifted_design, compute_fit_loss, run_permutation_tests,
    FILTER_MODELS, DEFAULT_WEIGHTS, NORM,
)
from step1_fit_loco_v2 import (  # noqa: E402
    precompute_hc_W, simulate_mean_hc_wfixed, load_cvd_loco_target,
)
from step0_srm_precompute import (  # noqa: E402
    compute_delta_rdm_sim_srm,
)
# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CVD_TYPE = {'08': 'deutan', '09': 'protan', '10': 'normal'}
MODELS = ['machado_1way', 'rc_opponent', '2component', 'fourier_warp']
FAMILIES = ['protan', 'deutan']
SRM_ROIS = ['V1', 'V2']  # ROIs providing ΔRDM

LOCAL_DATA = (Path(__file__).resolve().parent.parent.parent.parent
              / 'phase1_procrustes_decoding' / 'results'
              / 'visualization' / 'full_dataset_C010_with_residuals')
SERVER_DATA = Path(
    '/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010')


def auto_detect_data_dir(override=None):
    if override:
        return Path(override)
    if SERVER_DATA.exists():
        return SERVER_DATA
    if LOCAL_DATA.exists():
        return LOCAL_DATA
    raise FileNotFoundError('No data dir found')


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(str(type(o)))


# ---------------------------------------------------------------------------
# Load SRM precomputed artifacts
# ---------------------------------------------------------------------------

def load_srm_artifacts(srm_dir, roi):
    """Load W_combined and ΔRDM_obs from step0_srm_precompute.

    Returns:
        W_combined: {subj: (K_basis, K_srm)}
        delta_rdm_obs: {cvd_subj: (28,)}
    """
    srm_path = Path(srm_dir) / f'srm_{roi}.npz'
    drdm_path = Path(srm_dir) / f'delta_rdm_obs_srm_{roi}.npz'

    if not srm_path.exists():
        raise FileNotFoundError(f'SRM artifacts not found: {srm_path}')
    if not drdm_path.exists():
        raise FileNotFoundError(f'ΔRDM artifacts not found: {drdm_path}')

    srm_data = np.load(srm_path)
    drdm_data = np.load(drdm_path)

    # Extract W_combined per HC
    W_combined = {}
    for subj in HC_SUBJECTS:
        key = f'W_combined_{subj}'
        if key in srm_data:
            W_combined[subj] = srm_data[key]

    # Extract ΔRDM_obs per CVD
    delta_rdm_obs = {}
    for cvd_s in CVD_SUBJECTS:
        key = f'sub_{cvd_s}'
        if key in drdm_data:
            delta_rdm_obs[cvd_s] = drdm_data[key]

    return W_combined, delta_rdm_obs


# ---------------------------------------------------------------------------
# Cross-ROI grid search
# ---------------------------------------------------------------------------

def grid_search_cross_roi(model_name, hc_W_hv4, hc_amps_hv4, vuln_cvd,
                          cvd_type, W_combined_V1, W_combined_V2,
                          drdm_obs_V1, drdm_obs_V2, C_baseline,
                          weights=None, verbose=True):
    """Grid search with hV4 LOCO + V1/V2 SRM ΔRDM.

    hV4 provides: L_vuln, L_rank (via w_fixed LOCO)
    V1/V2 SRM provides: L_rdm (averaged ΔRDM)

    Args:
        model_name: distortion model
        hc_W_hv4: {subj: (K_basis, V_s)} hV4 ridge weights
        hc_amps_hv4: {subj: (6, 8, V_s)} hV4 amplitudes
        vuln_cvd: (8,) CVD LOCO target
        cvd_type: 'deutan', 'protan', 'normal'
        W_combined_V1: {subj: (K_basis, K_srm)} V1 SRM W_combined
        W_combined_V2: same for V2
        drdm_obs_V1: (28,) V1 SRM ΔRDM_obs for this CVD
        drdm_obs_V2: (28,) V2 SRM ΔRDM_obs
        C_baseline: (8, K_basis) original design
        weights: loss weights dict
        verbose: print progress

    Returns:
        dict with best_params, best_loss, landscape
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS.copy()

    model_info = FILTER_MODELS[model_name]
    bounds = model_info['bounds']
    steps = model_info['grid_step']

    if steps is None:
        raise ValueError(f'Grid search not supported for {model_name} '
                         f'(use DE instead)')

    # Build grid
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
        print(f'[{model_name}] Grid: {len(grid)} points, cross-ROI LOCO+SRM')

    # Average ΔRDM_obs across V1 and V2
    drdm_obs_avg = 0.5 * drdm_obs_V1 + 0.5 * drdm_obs_V2

    landscape = []
    best_loss = np.inf
    best_entry = None
    t0 = time.time()

    for i, params in enumerate(grid):
        params_arr = np.array(params)

        # Get shifted design
        C_shifted, delta_theta = get_shifted_design(
            model_name, params_arr, cvd_type)

        # hV4 LOCO (w_fixed)
        vuln_sim, _ = simulate_mean_hc_wfixed(
            hc_W_hv4, hc_amps_hv4, C_shifted)

        # V1/V2 SRM ΔRDM_sim (averaged)
        drdm_sim_V1, _ = compute_delta_rdm_sim_srm(
            W_combined_V1, C_shifted, C_baseline)
        drdm_sim_V2, _ = compute_delta_rdm_sim_srm(
            W_combined_V2, C_shifted, C_baseline)
        drdm_sim_avg = 0.5 * drdm_sim_V1 + 0.5 * drdm_sim_V2

        # Compute loss (L_vuln + L_rank from hV4, L_rdm from V1/V2 SRM)
        loss = compute_fit_loss(vuln_sim, vuln_cvd, delta_theta,
                                drdm_sim_avg, drdm_obs_avg, weights)

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
                  f'rdm_cos={best_entry["rdm_cosine"]}'
                  f' ({rate:.1f} eval/s)')

    elapsed = time.time() - t0
    if verbose:
        print(f'  Done in {elapsed:.1f}s. '
              f'Best: params={best_entry["params"]}, '
              f'L_fit={best_loss:.4f}, ρ={best_entry["spearman_r"]:.3f}')

    return {
        'model': model_name,
        'method': 'w_fixed_cross_roi',
        'best_params': best_entry['params'],
        'best_loss': best_entry,
        'landscape': landscape,
        'n_evaluations': len(grid),
        'elapsed_s': elapsed,
        'weights': weights,
    }


def optimize_de_cross_roi(model_name, hc_W_hv4, hc_amps_hv4, vuln_cvd,
                           cvd_type, W_combined_V1, W_combined_V2,
                           drdm_obs_V1, drdm_obs_V2, C_baseline,
                           weights=None, verbose=True,
                           n_restarts=3, maxiter=80, popsize=12, seed=42):
    """Differential Evolution for fourier_warp with cross-ROI LOCO+SRM."""
    from scipy.optimize import differential_evolution

    if weights is None:
        weights = DEFAULT_WEIGHTS.copy()

    model_info = FILTER_MODELS[model_name]
    bounds = model_info['bounds']

    drdm_obs_avg = 0.5 * drdm_obs_V1 + 0.5 * drdm_obs_V2

    n_eval = [0]

    def objective(params):
        C_shifted, delta_theta = get_shifted_design(
            model_name, params, cvd_type)

        vuln_sim, _ = simulate_mean_hc_wfixed(
            hc_W_hv4, hc_amps_hv4, C_shifted)

        drdm_sim_V1, _ = compute_delta_rdm_sim_srm(
            W_combined_V1, C_shifted, C_baseline)
        drdm_sim_V2, _ = compute_delta_rdm_sim_srm(
            W_combined_V2, C_shifted, C_baseline)
        drdm_sim_avg = 0.5 * drdm_sim_V1 + 0.5 * drdm_sim_V2

        loss = compute_fit_loss(vuln_sim, vuln_cvd, delta_theta,
                                drdm_sim_avg, drdm_obs_avg, weights)
        n_eval[0] += 1
        return loss['l_fit']

    if verbose:
        print(f'[{model_name}] DE cross-ROI: {n_restarts} restarts, '
              f'maxiter={maxiter}, popsize={popsize}')

    best_result = None
    best_fun = np.inf
    t0 = time.time()

    for restart in range(n_restarts):
        n_eval[0] = 0
        rs = seed + restart * 1000

        res = differential_evolution(
            objective, bounds=bounds,
            maxiter=maxiter, popsize=popsize,
            tol=1e-6, atol=1e-8,
            seed=rs, mutation=(0.5, 1.0), recombination=0.7,
            polish=True)

        if verbose:
            print(f'  Restart {restart+1}: fun={res.fun:.4f}, '
                  f'params={np.round(res.x, 2).tolist()}, '
                  f'{n_eval[0]} evals')

        if res.fun < best_fun:
            best_fun = res.fun
            best_result = res

    elapsed = time.time() - t0

    # Compute final loss
    C_shifted, delta_theta = get_shifted_design(
        model_name, best_result.x, cvd_type)
    vuln_sim, _ = simulate_mean_hc_wfixed(
        hc_W_hv4, hc_amps_hv4, C_shifted)
    drdm_sim_V1, _ = compute_delta_rdm_sim_srm(
        W_combined_V1, C_shifted, C_baseline)
    drdm_sim_V2, _ = compute_delta_rdm_sim_srm(
        W_combined_V2, C_shifted, C_baseline)
    drdm_sim_avg = 0.5 * drdm_sim_V1 + 0.5 * drdm_sim_V2
    drdm_obs_avg = 0.5 * drdm_obs_V1 + 0.5 * drdm_obs_V2

    best_loss = compute_fit_loss(vuln_sim, vuln_cvd, delta_theta,
                                 drdm_sim_avg, drdm_obs_avg, weights)

    if verbose:
        print(f'  Best: params={np.round(best_result.x, 2).tolist()}, '
              f'L_fit={best_loss["l_fit"]:.4f}, '
              f'ρ={best_loss["spearman_r"]:.3f} ({elapsed:.1f}s)')

    return {
        'model': model_name,
        'method': 'w_fixed_cross_roi',
        'best_params': best_result.x.tolist(),
        'best_loss': {
            'params': best_result.x.tolist(),
            'vuln_sim': vuln_sim.tolist(),
            'delta_theta': delta_theta.tolist(),
            **best_loss,
        },
        'landscape': None,
        'n_evaluations': best_result.nfev,
        'n_restarts': n_restarts,
        'elapsed_s': elapsed,
        'optimizer_success': bool(best_result.success),
        'weights': weights,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='SRM-Integrated LOCO: hV4 LOCO + V1/V2 SRM ΔRDM')
    parser.add_argument('--subjects', nargs='+', default=CVD_SUBJECTS,
                        help='CVD subjects to fit')
    parser.add_argument('--models', nargs='+', default=MODELS,
                        help='Models to fit')
    parser.add_argument('--families', nargs='+', default=FAMILIES,
                        help='CVD families to sweep')
    parser.add_argument('--srm_dir', type=str,
                        default='results/diagnostics/srm_precompute',
                        help='Directory with step0_srm_precompute outputs')
    parser.add_argument('--data_dir', type=str, default=None)
    parser.add_argument('--output_dir', type=str,
                        default='results/diagnostics/srm_integrated_loco')
    parser.add_argument('--weights', nargs=4, type=float, default=None,
                        metavar=('A', 'B', 'D', 'E'),
                        help='Loss weights: alpha beta delta epsilon')
    args = parser.parse_args()

    data_dir = auto_detect_data_dir(args.data_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    srm_dir = Path(args.srm_dir)

    weights = DEFAULT_WEIGHTS.copy()
    if args.weights:
        weights['alpha'] = args.weights[0]
        weights['beta'] = args.weights[1]
        weights['delta'] = args.weights[2]
        weights['epsilon'] = args.weights[3]

    print('=' * 70)
    print('SRM-INTEGRATED LOCO: hV4 LOCO + V1/V2 SRM ΔRDM')
    print('=' * 70)
    print(f'Data:       {data_dir}')
    print(f'SRM dir:    {srm_dir}')
    print(f'Subjects:   {args.subjects}')
    print(f'Models:     {args.models}')
    print(f'Families:   {args.families}')
    print(f'Weights:    {weights}')
    print(f'Output:     {output_dir}')

    # --- Load SRM precomputed artifacts for V1 and V2 ---
    print('\n=== Loading SRM artifacts ===')
    W_combined = {}
    delta_rdm_obs_srm = {}
    for roi in SRM_ROIS:
        W_comb, drdm_obs = load_srm_artifacts(srm_dir, roi)
        W_combined[roi] = W_comb
        delta_rdm_obs_srm[roi] = drdm_obs
        print(f'  {roi}: {len(W_comb)} HC W_combined, '
              f'{len(drdm_obs)} CVD ΔRDM_obs')
        for s in W_comb:
            print(f'    W_combined[{s}] shape={W_comb[s].shape}')

    # --- Load hV4 amplitudes ---
    print('\n=== Loading hV4 data ===')
    hv4_roi = 'V4'
    hc_amps_hv4 = {}
    for subj in HC_SUBJECTS:
        hc_amps_hv4[subj] = load_amplitudes(data_dir, subj, hv4_roi)
    print(f'  HC hV4: {len(hc_amps_hv4)} subjects, '
          f'V_s={hc_amps_hv4[HC_SUBJECTS[0]].shape[2]}')

    # --- Precompute hV4 W for w_fixed ---
    basis_full = create_basis_full(N_CHANNELS, basis_type='fe')
    C_original = basis_full[HUE_ANGLES]
    hc_W_hv4, hc_alpha_hv4 = precompute_hc_W(hc_amps_hv4, C_original)
    print(f'  hV4 W precomputed: {len(hc_W_hv4)} HCs')

    # --- Baseline vulnerability (δ=0) ---
    vuln_baseline, _ = simulate_mean_hc_wfixed(
        hc_W_hv4, hc_amps_hv4, C_original)
    print(f'  Baseline vuln: {np.round(vuln_baseline, 3).tolist()}')

    # --- Fit each CVD subject ---
    t_total = time.time()
    all_summary = {}

    for subj in args.subjects:
        cvd_type = CVD_TYPE[subj]
        print(f'\n{"=" * 70}')
        print(f'Subject: sub-{subj} ({cvd_type})')
        print(f'{"=" * 70}')

        # Load CVD LOCO target
        vuln_cvd = load_cvd_loco_target(subj, hv4_roi)
        print(f'  CVD target: {np.round(vuln_cvd, 3).tolist()}')

        rho_baseline, _ = spearmanr(vuln_baseline, vuln_cvd)
        if not np.isfinite(rho_baseline):
            rho_baseline = 0.0
        print(f'  Baseline ρ(δ=0) = {rho_baseline:.3f}')

        # Get SRM ΔRDM_obs for this subject
        drdm_obs_V1 = delta_rdm_obs_srm['V1'].get(subj)
        drdm_obs_V2 = delta_rdm_obs_srm['V2'].get(subj)
        if drdm_obs_V1 is None or drdm_obs_V2 is None:
            print(f'  WARNING: Missing SRM ΔRDM_obs for sub-{subj}, skipping')
            continue
        print(f'  ΔRDM_obs norms: V1={np.linalg.norm(drdm_obs_V1):.4f}, '
              f'V2={np.linalg.norm(drdm_obs_V2):.4f}')

        subj_results = {}

        for family in args.families:
            print(f'\n  --- Family: {family} ---')

            for model_name in args.models:
                if model_name not in FILTER_MODELS:
                    print(f'  WARNING: Unknown model {model_name}, skipping')
                    continue

                print(f'\n  [{model_name}]')
                model_info = FILTER_MODELS[model_name]

                if model_info['grid_step'] is not None:
                    result = grid_search_cross_roi(
                        model_name, hc_W_hv4, hc_amps_hv4, vuln_cvd,
                        family,
                        W_combined['V1'], W_combined['V2'],
                        drdm_obs_V1, drdm_obs_V2, C_original,
                        weights=weights)
                else:
                    result = optimize_de_cross_roi(
                        model_name, hc_W_hv4, hc_amps_hv4, vuln_cvd,
                        family,
                        W_combined['V1'], W_combined['V2'],
                        drdm_obs_V1, drdm_obs_V2, C_original,
                        weights=weights)

                # Permutation test
                print(f'  Running permutation tests...')
                best_vuln = np.array(result['best_loss']['vuln_sim'])
                perm = run_permutation_tests(best_vuln, vuln_cvd)
                result['permutation'] = perm
                print(f'  label_perm_p = {perm["label_perm_p"]:.4f}, '
                      f'ρ = {perm["spearman_r"]:.3f}')

                # Baseline comparison
                result['baseline'] = {
                    'vuln_baseline': vuln_baseline.tolist(),
                    'spearman_r_baseline': float(rho_baseline),
                    'delta_rho': float(perm['spearman_r'] - rho_baseline),
                }

                key = f'{family}_{model_name}'
                subj_results[key] = result

                # Save per-model result
                save_path = (output_dir
                             / f'sub-{subj}_{family}_{model_name}.json')
                result_compact = {
                    k: v for k, v in result.items() if k != 'landscape'}
                with open(save_path, 'w') as f:
                    json.dump(result_compact, f, indent=2,
                              default=_json_default)
                print(f'  Saved: {save_path}')

        # Per-subject summary
        print(f'\n  --- sub-{subj} Summary ---')
        print(f'  Baseline ρ = {rho_baseline:.3f}')
        print(f'  {"Model":>25s}  {"ρ":>6s}  {"Δρ":>6s}  {"p":>7s}  params')
        print(f'  {"-"*65}')
        best_overall = {'l_fit': np.inf}
        for key, res in subj_results.items():
            bl = res['best_loss']
            pm = res['permutation']
            base = res['baseline']
            sig = '*' if pm['label_perm_p'] < 0.05 else ''
            print(f'  {key:>25s}  {pm["spearman_r"]:>6.3f}  '
                  f'{base["delta_rho"]:>+6.3f}  '
                  f'{pm["label_perm_p"]:>6.4f}{sig}  '
                  f'{bl["params"]}')
            if bl['l_fit'] < best_overall.get('l_fit', np.inf):
                best_overall = {
                    'key': key,
                    'l_fit': bl['l_fit'],
                    'spearman_r': pm['spearman_r'],
                    'delta_rho': base['delta_rho'],
                    'perm_p': pm['label_perm_p'],
                    'params': bl['params'],
                }

        all_summary[subj] = {
            'cvd_type': cvd_type,
            'baseline_rho': float(rho_baseline),
            'best': best_overall,
            'n_models': len(subj_results),
        }

    # --- Global summary ---
    elapsed_total = time.time() - t_total
    summary = {
        'date': datetime.now().isoformat(),
        'method': 'w_fixed_cross_roi',
        'loco_roi': 'hV4',
        'rdm_rois': SRM_ROIS,
        'weights': weights,
        'models': args.models,
        'families': args.families,
        'subjects': args.subjects,
        'per_subject': all_summary,
        'total_elapsed_s': round(elapsed_total, 1),
    }

    with open(output_dir / 'summary.json', 'w') as f:
        json.dump(summary, f, indent=2, default=_json_default)

    print(f'\n{"=" * 70}')
    print('GLOBAL SUMMARY')
    print(f'{"=" * 70}')
    for subj, info in all_summary.items():
        b = info.get('best', {})
        sig = '*' if b.get('perm_p', 1) < 0.05 else ''
        print(f'  sub-{subj} ({info["cvd_type"]}): '
              f'best={b.get("key", "N/A")} '
              f'ρ={b.get("spearman_r", 0):.3f} '
              f'Δρ={b.get("delta_rho", 0):+.3f} '
              f'p={b.get("perm_p", 1):.4f}{sig}')

    print(f'\nTotal: {elapsed_total:.0f}s')
    print(f'Saved: {output_dir}/summary.json')


if __name__ == '__main__':
    main()
