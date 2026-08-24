#!/usr/bin/env python3
"""Experiment C: Delta-Vulnerability (ΔV) Loss for CVD-Specific Fitting.

Hypothesis: HC-baselined deficit (ΔV_obs) + shift-induced change (ΔV_sim)
achieves CVD specificity by removing shared LOCO structure that causes FP.

  ΔV_obs[c] = vuln_target[c] - mean_HC_vuln_baseline[c]   # observed deficit
  ΔV_sim[c] = vuln_sim_shifted[c] - vuln_sim_baseline[c]   # predicted change

  L_fit = α·L_delta_vuln + β·L_delta_rank + ε·L_smooth
    (no L_rdm — proven uninformative by Experiment B)

Mechanism for CVD specificity:
  - HC LOO: ΔV_obs ≈ 0 (each HC ≈ group mean) → best fit is Δλ=0 → NS
  - CVD:    ΔV_obs has confusion-axis structure → model matches → significant

Models: machado_1way (1 DOF), rc_opponent (2 DOF), 2component (2 DOF)
Method: w_fixed (fast, no BrainIAK needed)
ROI: hV4 only

Usage (server):
  python experiment_delta_vuln.py --output_dir results/experiment_c_delta_vuln

Does NOT require BrainIAK. ~15 min for all 10 subjects.
"""

import argparse
import json
import time
import sys
import numpy as np
from pathlib import Path
from itertools import permutations
from scipy.stats import spearmanr

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
_PHASE2_DIR = _SCRIPT_DIR.parent

for _base in [_PHASE2_DIR.parent, _PHASE2_DIR.parent.parent]:
    _fwd = _base / 'phase4_forward_model' / 'scripts'
    if _fwd.exists() and str(_fwd) not in sys.path:
        sys.path.insert(0, str(_fwd))
        break

if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR.parent))

from utils_forward_model import (
    load_amplitudes, create_basis_full, HUE_ANGLES, N_CHANNELS,
    gcv_select_alpha, fit_W_ridge, voxel_pattern_correlation,
)
from step1_fit_loco_v2 import (
    precompute_hc_W, simulate_mean_hc_wfixed,
    lins_ccc, mse_decompose,
)
from loco_distortion_fit import (
    get_shifted_design, run_permutation_tests, FILTER_MODELS, NORM,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
HC_SUBJECTS = ['01', '02', '03', '04', '05', '06', '07']
CVD_SUBJECTS = ['08', '09', '10']
CVD_TYPES = {'08': 'deutan', '09': 'protan', '10': 'deutan'}  # sub-10 = mild deutan
N_COLORS = 8

# Models (no fourier_warp — 4 DOF causes 100% HC FPR)
MODELS = ['machado_1way', 'rc_opponent', '2component']
FAMILIES = ['protan', 'deutan']

# Loss weights: L_fit = α·L_delta_vuln + β·L_delta_rank + ε·L_smooth
WEIGHTS = {'alpha': 1.0, 'beta': 0.5, 'epsilon': 0.1}

# Normalization constants (same scale as loco_distortion_fit.py)
NORM_DV = {
    'vuln': 4.0,       # max MSE when corr ∈ [-1, 1]
    'rank': 2.0,       # max of (1 - Spearman ρ)
    'smooth': 32400.0,  # 180²
}


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
def load_data(data_dir):
    """Load hV4 amplitudes for all 10 subjects."""
    all_amps = {}
    roi_dir = 'V4'  # hV4 on disk
    for subj in HC_SUBJECTS + CVD_SUBJECTS:
        subj_dir = Path(data_dir) / f'sub-{subj}' / roi_dir
        amp_file = subj_dir / 'amplitudes_procrustes.npy'
        if amp_file.exists():
            all_amps[subj] = np.load(amp_file)
            print(f'  sub-{subj}: {all_amps[subj].shape}')
        else:
            print(f'  WARNING: Missing {amp_file}')
    return all_amps


# ---------------------------------------------------------------------------
# Self-vulnerability computation
# ---------------------------------------------------------------------------
def compute_self_vulnerability(target_amp, C_design):
    """Compute self-vulnerability: how well the encoding model predicts
    the target's own patterns at each color.

    Fits W from target's own data (pooled 6 runs × 8 colors = 48 samples),
    then vuln[c] = corr(C[c] @ W, target_amp[:, c].mean(0)).

    Args:
        target_amp: (6, 8, V_s) target amplitudes
        C_design: (8, K) design matrix

    Returns:
        vuln: (8,) per-color correlation
        W: (K, V_s) fitted weight matrix
        alpha: float selected regularization
    """
    V_s = target_amp.shape[2]
    n_runs = target_amp.shape[0]
    target_pooled = target_amp.reshape(-1, V_s)           # (48, V_s)
    C_pooled = np.tile(C_design, (n_runs, 1))             # (48, K)

    alpha, _ = gcv_select_alpha(C_pooled, target_pooled)
    W = fit_W_ridge(C_pooled, target_pooled, alpha)       # (K, V_s)

    vuln = np.zeros(N_COLORS)
    for c in range(N_COLORS):
        Y_pred = (C_design[c:c + 1] @ W).flatten()        # (V_s,)
        Y_actual = target_amp[:, c].mean(axis=0)           # (V_s,)
        r = np.corrcoef(Y_pred, Y_actual)[0, 1]
        vuln[c] = r if np.isfinite(r) else 0.0

    return vuln, W, float(alpha)


# ---------------------------------------------------------------------------
# ΔV loss function
# ---------------------------------------------------------------------------
def compute_delta_vuln_loss(dv_sim, dv_obs, delta_theta, weights=None):
    """Compute ΔV-based loss.

    L_fit = α·L_delta_vuln + β·L_delta_rank + ε·L_smooth

    Args:
        dv_sim: (8,) simulated delta-vulnerability
        dv_obs: (8,) observed delta-vulnerability
        delta_theta: (8,) per-color hue shift in degrees
        weights: dict with alpha, beta, epsilon

    Returns:
        dict with l_fit and component losses
    """
    if weights is None:
        weights = WEIGHTS

    # L_delta_vuln: MSE(ΔV_sim, ΔV_obs)
    l_vuln_raw = float(np.mean((dv_sim - dv_obs) ** 2))
    l_vuln = l_vuln_raw / NORM_DV['vuln']

    # L_delta_rank: 1 - Spearman(ΔV_sim, ΔV_obs)
    # When ΔV_sim is constant (all zeros at Δλ=0), Spearman is undefined.
    # Set ρ=0 → L_rank=0.5 (neutral, not penalized or rewarded)
    if np.std(dv_sim) < 1e-10:
        rho = 0.0
    else:
        rho, _ = spearmanr(dv_sim, dv_obs)
        if not np.isfinite(rho):
            rho = 0.0
    l_rank_raw = 1.0 - rho
    l_rank = l_rank_raw / NORM_DV['rank']

    # L_smooth: adjacent-color hue shift regularity
    dt = np.asarray(delta_theta)
    diffs = np.diff(dt, append=dt[0])
    diffs = (diffs + 180) % 360 - 180   # circular wrap
    l_smooth_raw = float(np.mean(diffs ** 2))
    l_smooth = l_smooth_raw / NORM_DV['smooth']

    l_fit = (weights['alpha'] * l_vuln
             + weights['beta'] * l_rank
             + weights.get('epsilon', 0.1) * l_smooth)

    return {
        'l_fit': float(l_fit),
        'l_delta_vuln': float(l_vuln),
        'l_delta_rank': float(l_rank),
        'l_smooth': float(l_smooth),
        'l_vuln_raw': float(l_vuln_raw),
        'l_rank_raw': float(l_rank_raw),
        'l_smooth_raw': float(l_smooth_raw),
        'spearman_r': float(rho),
    }


# ---------------------------------------------------------------------------
# Permutation test on ΔV
# ---------------------------------------------------------------------------
def delta_vuln_permutation_test(dv_sim, dv_obs):
    """Exact 8! permutation test on ΔV_sim vs ΔV_obs.

    Permutes color labels of ΔV_obs (or equivalently ΔV_sim).
    Tests: Spearman ρ and MSE.

    Returns dict with dv_perm_p (Spearman), dv_mse_perm_p, etc.
    """
    if np.std(dv_sim) < 1e-10:
        return {
            'dv_perm_p': 1.0,
            'dv_spearman_r': 0.0,
            'dv_mse_perm_p': 1.0,
            'dv_mse': float(np.mean((dv_sim - dv_obs) ** 2)),
            'null_rho_mean': 0.0,
            'null_rho_std': 0.0,
        }

    rho_obs, _ = spearmanr(dv_sim, dv_obs)
    if not np.isfinite(rho_obs):
        rho_obs = 0.0
    mse_obs = float(np.mean((dv_sim - dv_obs) ** 2))

    null_rhos = []
    null_mses = []
    for perm in permutations(range(8)):
        dv_obs_p = dv_obs[list(perm)]
        r, _ = spearmanr(dv_sim, dv_obs_p)
        null_rhos.append(r if np.isfinite(r) else 0.0)
        null_mses.append(float(np.mean((dv_sim - dv_obs_p) ** 2)))

    null_rhos = np.array(null_rhos)
    null_mses = np.array(null_mses)

    rho_p = float((np.sum(null_rhos >= rho_obs) + 1) / (len(null_rhos) + 1))
    mse_p = float((np.sum(null_mses <= mse_obs) + 1) / (len(null_mses) + 1))

    return {
        'dv_perm_p': float(rho_p),
        'dv_spearman_r': float(rho_obs),
        'dv_mse_perm_p': float(mse_p),
        'dv_mse': float(mse_obs),
        'null_rho_mean': float(np.mean(null_rhos)),
        'null_rho_std': float(np.std(null_rhos)),
    }


# ---------------------------------------------------------------------------
# Per-subject fitting
# ---------------------------------------------------------------------------
def run_for_subject(subj, all_amps, output_dir, is_hc=False):
    """Run ΔV grid search for one subject across all models and families."""

    t0 = time.time()
    print(f'\n{"=" * 60}')
    print(f'  Subject: sub-{subj} ({"HC LOO" if is_hc else "CVD"})')
    print(f'{"=" * 60}')

    # --- HC pool (LOO for HC subjects) ---
    if is_hc:
        hc_pool = [s for s in HC_SUBJECTS if s != subj]
    else:
        hc_pool = HC_SUBJECTS

    hc_amps = {s: all_amps[s] for s in hc_pool if s in all_amps}
    target_amp = all_amps.get(subj)
    if target_amp is None:
        print(f'  ERROR: No data for sub-{subj}')
        return None

    # --- Baseline design matrix ---
    # CRITICAL: Use Machado's Stockman-derived hue angles at Δλ=0, NOT
    # nominal CIELab angles [0,45,90,...]. The Machado model's get_shifted_design
    # returns C at Stockman angles even at Δλ=0, which differ from nominal by
    # up to 15°. Using nominal for baseline but Stockman for shifts creates a
    # systematic artifact where ΔV_sim ≠ 0 at Δλ=0.
    # The Stockman baseline is the same for protan/deutan at Δλ=0.
    C_ref, _ = get_shifted_design('machado_1way', np.array([0.0]), 'protan')

    # --- Precompute HC W using Stockman baseline ---
    hc_W, hc_alpha = precompute_hc_W(hc_amps, C_ref)

    # --- Step 1: mean_HC_vuln at baseline ---
    mean_hc_vuln_baseline, per_hc_vuln = simulate_mean_hc_wfixed(
        hc_W, hc_amps, C_ref)

    # --- Step 2: target's self-vulnerability at baseline ---
    vuln_target, W_target, alpha_target = compute_self_vulnerability(
        target_amp, C_ref)

    # --- Step 3: ΔV_obs = deficit relative to HC mean ---
    dv_obs = vuln_target - mean_hc_vuln_baseline

    print(f'  vuln_target:      [{", ".join(f"{v:.3f}" for v in vuln_target)}]')
    print(f'  mean_HC_baseline: '
          f'[{", ".join(f"{v:.3f}" for v in mean_hc_vuln_baseline)}]')
    print(f'  ΔV_obs:           [{", ".join(f"{v:.3f}" for v in dv_obs)}]')
    print(f'  ΔV_obs range: [{dv_obs.min():.3f}, {dv_obs.max():.3f}], '
          f'std={dv_obs.std():.3f}')

    # Reference: raw baseline Spearman ρ (for comparison with existing pipeline)
    baseline_rho, _ = spearmanr(mean_hc_vuln_baseline, vuln_target)
    if not np.isfinite(baseline_rho):
        baseline_rho = 0.0
    print(f'  Baseline ρ (raw vuln): {baseline_rho:.3f}')

    # --- Grid search per model × family ---
    results = {}
    vuln_sim_baseline = mean_hc_vuln_baseline  # = HC pool at unshifted C

    for model_name in MODELS:
        model_info = FILTER_MODELS[model_name]
        bounds = model_info['bounds']
        steps = model_info['grid_step']

        if steps is None:
            continue  # skip fourier_warp (DE only)

        # Build grid
        axes = [np.arange(lo, hi + step * 0.5, step)
                for (lo, hi), step in zip(bounds, steps)]
        if len(axes) == 1:
            grid = [(x,) for x in axes[0]]
        elif len(axes) == 2:
            grid = [(x, y) for x in axes[0] for y in axes[1]]
        else:
            continue

        for family in FAMILIES:
            key = f'{model_name}_{family}'
            print(f'\n  [{key}] Grid: {len(grid)} points')

            best_loss_val = np.inf
            best_entry = None

            for i, params in enumerate(grid):
                params_arr = np.array(params)

                C_shifted, delta_theta = get_shifted_design(
                    model_name, params_arr, family)

                # HC pool vulnerability at shifted C
                vuln_sim_shifted, _ = simulate_mean_hc_wfixed(
                    hc_W, hc_amps, C_shifted)

                # ΔV_sim = change induced by shift
                dv_sim = vuln_sim_shifted - vuln_sim_baseline

                loss = compute_delta_vuln_loss(dv_sim, dv_obs, delta_theta)

                if loss['l_fit'] < best_loss_val:
                    best_loss_val = loss['l_fit']
                    best_entry = {
                        'params': params_arr.tolist(),
                        'dv_sim': dv_sim.tolist(),
                        'vuln_sim_shifted': vuln_sim_shifted.tolist(),
                        'delta_theta': delta_theta.tolist(),
                        **loss,
                    }

                if (i + 1) % max(1, len(grid) // 5) == 0:
                    print(f'    [{i + 1}/{len(grid)}] best L={best_loss_val:.4f}')

            # --- Permutation tests ---
            if best_entry is not None:
                dv_sim_best = np.array(best_entry['dv_sim'])
                dv_perm = delta_vuln_permutation_test(dv_sim_best, dv_obs)

                # Also test raw vuln match (for comparison)
                vuln_sim_best = np.array(best_entry['vuln_sim_shifted'])
                raw_perm = run_permutation_tests(vuln_sim_best, vuln_target)

                results[key] = {
                    'model': model_name,
                    'family': family,
                    'best_params': best_entry['params'],
                    # ΔV metrics (primary)
                    'dv_spearman_r': dv_perm['dv_spearman_r'],
                    'dv_perm_p': dv_perm['dv_perm_p'],
                    'dv_mse_perm_p': dv_perm['dv_mse_perm_p'],
                    'dv_mse': dv_perm['dv_mse'],
                    # Raw vuln metrics (comparison)
                    'raw_spearman_r': raw_perm['spearman_r'],
                    'raw_perm_p': raw_perm['label_perm_p'],
                    'raw_delta_rho': raw_perm['spearman_r'] - baseline_rho,
                    'raw_ccc': raw_perm['ccc'],
                    # Loss components
                    'l_fit': best_entry['l_fit'],
                    'l_delta_vuln': best_entry['l_delta_vuln'],
                    'l_delta_rank': best_entry['l_delta_rank'],
                    'l_smooth': best_entry['l_smooth'],
                    # Detailed vectors (for diagnostics)
                    'dv_sim': best_entry['dv_sim'],
                    'delta_theta': best_entry['delta_theta'],
                    'n_grid_points': len(grid),
                }

                print(f'  {key}: params={best_entry["params"]}, '
                      f'ΔV_ρ={dv_perm["dv_spearman_r"]:.3f} '
                      f'(p={dv_perm["dv_perm_p"]:.4f}), '
                      f'raw_ρ={raw_perm["spearman_r"]:.3f} '
                      f'(p={raw_perm["label_perm_p"]:.4f})')

    # --- Best model across all ---
    best_key = None
    if results:
        best_key = min(results, key=lambda k: results[k]['l_fit'])

    output = {
        'subject': subj,
        'group': 'HC' if is_hc else 'CVD',
        'cvd_type': CVD_TYPES.get(subj, 'HC' if is_hc else 'unknown'),
        'baseline_rho': float(baseline_rho),
        'alpha_target': alpha_target,
        'vuln_target': vuln_target.tolist(),
        'mean_hc_vuln_baseline': mean_hc_vuln_baseline.tolist(),
        'dv_obs': dv_obs.tolist(),
        'dv_obs_stats': {
            'mean': float(dv_obs.mean()),
            'std': float(dv_obs.std()),
            'min': float(dv_obs.min()),
            'max': float(dv_obs.max()),
            'range': float(dv_obs.max() - dv_obs.min()),
        },
        'best_overall': best_key,
        'results': results,
        'elapsed_s': time.time() - t0,
    }

    save_path = output_dir / f'sub-{subj}.json'
    with open(save_path, 'w') as f:
        json.dump(output, f, indent=2)
    print(f'\n  Saved: {save_path} ({time.time() - t0:.1f}s)')

    return output


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description='Experiment C: Delta-Vulnerability Loss')
    parser.add_argument('--subjects', nargs='+',
                        default=HC_SUBJECTS + CVD_SUBJECTS)
    parser.add_argument('--data_dir', default=None)
    parser.add_argument('--output_dir',
                        default='results/experiment_c_delta_vuln')
    args = parser.parse_args()

    # Auto-detect data dir
    data_dir = args.data_dir
    if data_dir is None:
        candidates = [
            Path('/scratch/connectome/haba6030/colorBlind/derivatives/'
                 'full_dataset_C010'),
            _PHASE2_DIR.parent / 'phase1_procrustes_decoding' / 'results' /
            'visualization' / 'full_dataset_C010_with_residuals',
        ]
        for c in candidates:
            if c.exists():
                data_dir = str(c)
                break
    if data_dir is None:
        print('ERROR: Could not find C010 data directory')
        sys.exit(1)
    print(f'Data dir: {data_dir}')

    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = _PHASE2_DIR / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    print('\n--- Loading hV4 amplitudes ---')
    all_amps = load_data(data_dir)

    # Run per subject
    all_results = {}
    for subj in args.subjects:
        is_hc = subj in HC_SUBJECTS
        result = run_for_subject(subj, all_amps, output_dir, is_hc=is_hc)
        if result:
            all_results[subj] = result

    # =========================================================================
    # Summary
    # =========================================================================
    print(f'\n{"=" * 70}')
    print('SUMMARY: DELTA-VULNERABILITY (ΔV) RESULTS')
    print(f'{"=" * 70}')

    for model_name in MODELS:
        df = FILTER_MODELS[model_name]['df']
        print(f'\n  Model: {model_name} ({df} DOF)')
        print(f'  {"Subj":>6} {"Grp":>3} {"Type":>7} {"Fam":>7} '
              f'{"Params":>20} '
              f'{"ΔV_ρ":>7} {"ΔV_p":>8} '
              f'{"raw_ρ":>7} {"raw_p":>8} {"Δρ":>7} {"Sig":>5}')

        hc_fp_dv = 0
        hc_fp_raw = 0
        hc_total = 0

        for subj in sorted(all_results.keys()):
            res = all_results[subj]
            group = res['group']
            cvd_type = res.get('cvd_type', '?')

            # Best family for this model (by ΔV Spearman)
            best_key = None
            best_dv_rho = -2
            for family in FAMILIES:
                k = f'{model_name}_{family}'
                if k in res['results']:
                    r = res['results'][k]['dv_spearman_r']
                    if r > best_dv_rho:
                        best_dv_rho = r
                        best_key = k

            if best_key is not None:
                r = res['results'][best_key]
                sig_dv = '*' if r['dv_perm_p'] < 0.05 else ''
                if r['dv_perm_p'] < 0.01:
                    sig_dv = '**'
                if r['dv_perm_p'] < 0.001:
                    sig_dv = '***'

                sig_raw = '(r*)' if r['raw_perm_p'] < 0.05 else ''

                params_str = str([round(p, 1) for p in r['best_params']])
                print(f'  sub-{subj:>2} {group:>3} {cvd_type:>7} '
                      f'{r["family"]:>7} {params_str:>20} '
                      f'{r["dv_spearman_r"]:>7.3f} {r["dv_perm_p"]:>8.4f} '
                      f'{r["raw_spearman_r"]:>7.3f} {r["raw_perm_p"]:>8.4f} '
                      f'{r["raw_delta_rho"]:>7.3f} '
                      f'{sig_dv:>3}{sig_raw:>4}')

                if group == 'HC':
                    hc_total += 1
                    if r['dv_perm_p'] < 0.05:
                        hc_fp_dv += 1
                    if r['raw_perm_p'] < 0.05:
                        hc_fp_raw += 1

        if hc_total > 0:
            print(f'\n  HC FPR (ΔV criterion):  {hc_fp_dv}/{hc_total} '
                  f'= {hc_fp_dv / hc_total:.1%}')
            print(f'  HC FPR (raw criterion): {hc_fp_raw}/{hc_total} '
                  f'= {hc_fp_raw / hc_total:.1%}')

    # ΔV_obs statistics
    print(f'\n{"=" * 70}')
    print('ΔV_obs PROFILE (deficit relative to HC mean)')
    print(f'{"=" * 70}')
    print(f'  {"Subj":>6} {"Grp":>3} {"Type":>7} '
          f'{"std":>7} {"min":>7} {"max":>7} {"range":>7}')
    for subj in sorted(all_results.keys()):
        res = all_results[subj]
        dv = res['dv_obs_stats']
        print(f'  sub-{subj:>2} {res["group"]:>3} '
              f'{res.get("cvd_type", "?"):>7} '
              f'{dv["std"]:>7.3f} {dv["min"]:>7.3f} '
              f'{dv["max"]:>7.3f} {dv["range"]:>7.3f}')

    # Save summary
    summary = {
        'date': time.strftime('%Y-%m-%dT%H:%M:%S'),
        'experiment': 'delta_vulnerability',
        'models': MODELS,
        'families': FAMILIES,
        'weights': WEIGHTS,
        'norm': NORM_DV,
        'method': 'w_fixed',
        'roi': 'hV4',
        'subjects': list(all_results.keys()),
        'hypothesis': (
            'ΔV_obs = vuln_target - mean_HC_vuln removes shared LOCO '
            'structure. For HC: ΔV_obs ≈ 0 → best fit Δλ=0 → NS. '
            'For CVD: ΔV_obs has confusion-axis pattern → model matches.'
        ),
    }
    with open(output_dir / 'summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    print(f'\nSummary saved to {output_dir}/summary.json')


if __name__ == '__main__':
    main()
