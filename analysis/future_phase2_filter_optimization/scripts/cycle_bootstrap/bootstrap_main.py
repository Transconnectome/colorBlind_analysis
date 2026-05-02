#!/usr/bin/env python3
"""bootstrap_main.py — Cycle 1 main: HC LOHO + bootstrap of LOCO ρ.

Computes:
1. **LOHO (deterministic)**: 7 leave-one-HC-out variants, full grid.
2. **Bootstrap (probabilistic)**: HC subject resampling with replacement,
   refit grid each bootstrap iteration.
3. **HC null distribution**: each HC treated as pseudo-CVD (LOO HC ↔ HC),
   produces ρ_HC distribution to compare against ρ_CVD.

Output (one JSON per (subject, roi, model)):
    sub-{ID}_{roi}_{model}.json with:
      - all7_fit (baseline, full 7-HC mean)
      - loho: [ {drop_subj, best_params, rho, label_perm_p} × 7 ]
      - bootstrap: [ {boot_id, sample, best_params, rho} × n_boot ]
      - hc_null: { hc_id: rho_hc_as_pseudo_cvd }

Usage:
    python bootstrap_main.py --subject 08 --roi V4 --model 2component \\
        --n_boot 200 --output_dir results/cycle_bootstrap/main

For SLURM: see sbatch/cycle_bootstrap/run_bootstrap_main.sbatch
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

_SCRIPT_DIR = Path(__file__).resolve().parent
_PHASE2_DIR = _SCRIPT_DIR.parent.parent
_PHASE2_SCRIPTS = _PHASE2_DIR / 'scripts'
sys.path.insert(0, str(_PHASE2_SCRIPTS))

for _base in [_PHASE2_DIR.parent, _PHASE2_DIR.parent.parent]:
    _fwd = _base / 'future_phase1_forward_model' / 'scripts'
    if _fwd.exists() and str(_fwd) not in sys.path:
        sys.path.insert(0, str(_fwd))
        break

from utils_forward_model import (
    HC_SUBJECTS, N_CHANNELS, N_RUNS, HUE_ANGLES,
    load_amplitudes, create_basis_matrix, voxel_pattern_correlation,
    gcv_select_alpha, fit_W_ridge,
)
from step1_fit_loco_v2 import (
    precompute_hc_W,
    simulate_mean_hc_wfixed,
    simulate_single_hc_wfixed,
    load_cvd_loco_target,
    permutation_test_spearman,
)
from loco_distortion_fit import (
    FILTER_MODELS, get_shifted_design, compute_fit_loss, DEFAULT_WEIGHTS,
)

CVD_TYPE = {'08': 'deutan', '09': 'protan', '10': 'normal'}
LOCAL_DATA = (_PHASE2_DIR.parent / 'phase1_procrustes_decoding' / 'results'
              / 'visualization' / 'full_dataset_C010_with_residuals')


def grid_axes(model_name: str):
    info = FILTER_MODELS[model_name]
    bounds = info['bounds']
    steps = info['grid_step']
    if steps is None:
        raise ValueError(f"Grid not supported for {model_name}")
    axes = []
    for (lo, hi), step in zip(bounds, steps):
        axes.append(np.arange(lo, hi + step * 0.5, step))
    if len(axes) == 1:
        grid = [(x,) for x in axes[0]]
    elif len(axes) == 2:
        grid = [(x, y) for x in axes[0] for y in axes[1]]
    else:
        raise ValueError("only 1D/2D grids supported")
    return grid


def grid_search_wfixed(
    model_name: str,
    hc_amps_dict: dict,
    hc_W_dict: dict,
    cvd_vuln: np.ndarray,
    cvd_type: str,
    grid: list,
    weights=None,
    do_perm: bool = True,
):
    if weights is None:
        weights = DEFAULT_WEIGHTS

    best_loss = np.inf
    best_params = None
    best_rho = None
    best_vuln_sim = None
    best_dt = None
    for params in grid:
        params_arr = np.array(params)
        C_shifted, dt = get_shifted_design(model_name, params_arr, cvd_type)
        vuln_sim, _ = simulate_mean_hc_wfixed(hc_W_dict, hc_amps_dict, C_shifted)
        loss = compute_fit_loss(vuln_sim, cvd_vuln, dt, weights=weights)
        if loss['l_fit'] < best_loss:
            best_loss = loss['l_fit']
            best_params = params_arr.tolist()
            best_rho = loss['spearman_r']
            best_vuln_sim = vuln_sim.tolist()
            best_dt = dt.tolist()

    out = {
        'best_params': best_params,
        'best_loss': float(best_loss),
        'rho': float(best_rho),
        'vuln_sim': best_vuln_sim,
        'delta_theta': best_dt,
    }
    if do_perm:
        perm_p, _, rho_obs = permutation_test_spearman(
            np.array(best_vuln_sim), cvd_vuln, n_perm=40320)
        out['label_perm_p'] = float(perm_p)
        out['rho_obs_perm'] = float(rho_obs)
    return out


def fit_subset(
    model_name: str,
    hc_amps: dict,
    cvd_vuln: np.ndarray,
    cvd_type: str,
    drop_subjs: list[str] | None,
    C_original: np.ndarray,
    grid: list,
    do_perm: bool = True,
    boot_resample_idx: list[str] | None = None,
):
    """Fit with either drop list or with-replacement bootstrap sample.

    If boot_resample_idx is given, each entry is an HC ID; W is precomputed
    per unique subject and reused.
    """
    if boot_resample_idx is not None:
        # Resample with replacement: precompute W per unique subject
        unique_subjs = sorted(set(boot_resample_idx))
        amps_unique = {s: hc_amps[s] for s in unique_subjs}
        W_unique, alpha_unique = precompute_hc_W(amps_unique, C_original)
        # Build full dict using duplicate keys to weight properly
        hc_amps_use = {}
        hc_W_use = {}
        for k, s in enumerate(boot_resample_idx):
            key = f'{s}__{k}'
            hc_amps_use[key] = hc_amps[s]
            hc_W_use[key] = W_unique[s]
        label = 'boot'
    else:
        if drop_subjs:
            amps_use = {k: v for k, v in hc_amps.items() if k not in drop_subjs}
        else:
            amps_use = dict(hc_amps)
        W_use, _ = precompute_hc_W(amps_use, C_original)
        hc_amps_use = amps_use
        hc_W_use = W_use
        label = ('drop_' + '_'.join(sorted(drop_subjs))
                 if drop_subjs else 'all')

    res = grid_search_wfixed(
        model_name, hc_amps_use, hc_W_use, cvd_vuln, cvd_type,
        grid, do_perm=do_perm)
    res['label'] = label
    res['n_hc_used'] = len(hc_amps_use)
    return res


def compute_hc_loco_target(hc_amps: dict, hc_subj: str,
                           C_original: np.ndarray):
    """Compute LOCO vulnerability for one HC, using its own data.

    Replicates the W-fixed single-HC vulnerability used in the pipeline,
    but performs LOCO retraining (W trained on n_runs × 7 colors per held-out
    color). This matches how CVD LOCO target is computed in the forward model
    pipeline.
    """
    amp = hc_amps[hc_subj]
    n_runs, n_colors, V_s = amp.shape
    vuln = np.zeros(n_colors)
    for color in range(n_colors):
        train_colors = [c for c in range(n_colors) if c != color]
        X_train = amp[:, train_colors].reshape(-1, V_s)
        C_train = np.tile(C_original[train_colors], (n_runs, 1))
        alpha, _ = gcv_select_alpha(C_train, X_train)
        W = fit_W_ridge(C_train, X_train, alpha)
        Y_pred = C_original[color:color + 1] @ W
        Y_test = amp[:, color].mean(axis=0, keepdims=True)
        r = voxel_pattern_correlation(Y_pred, Y_test)
        vuln[color] = float(r[0])
    return vuln


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--subject', required=True)
    ap.add_argument('--roi', default='V4')
    ap.add_argument('--model', default='2component',
                    choices=['2component', 'machado_1way', 'rc_opponent'])
    ap.add_argument('--data_dir', default=str(LOCAL_DATA))
    ap.add_argument('--n_boot', type=int, default=200)
    ap.add_argument('--seed', type=int, default=42)
    ap.add_argument('--output_dir', default=str(
        _PHASE2_DIR / 'results' / 'cycle_bootstrap' / 'main'))
    ap.add_argument('--skip_loho', action='store_true')
    ap.add_argument('--skip_boot', action='store_true')
    ap.add_argument('--skip_hc_null', action='store_true')
    args = ap.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cvd_type = CVD_TYPE[args.subject]

    # ---- Load HC amps ----
    hc_amps = {}
    for s in HC_SUBJECTS:
        try:
            hc_amps[s] = load_amplitudes(args.data_dir, s, args.roi)
        except FileNotFoundError as e:
            print(f'[warn] missing {s}: {e}')
    if not hc_amps:
        raise SystemExit('No HC amps loaded')

    # ---- CVD target ----
    cvd_vuln = load_cvd_loco_target(args.subject, args.roi)

    # ---- Common ----
    C_original = create_basis_matrix(HUE_ANGLES, N_CHANNELS, basis_type='fe')
    grid = grid_axes(args.model)
    print(f'[main] sub-{args.subject} roi={args.roi} model={args.model} '
          f'grid_size={len(grid)} HC={list(hc_amps.keys())} cvd_type={cvd_type}')

    summary = {
        'subject': args.subject,
        'roi': args.roi,
        'model': args.model,
        'cvd_type': cvd_type,
        'n_hc': len(hc_amps),
        'cvd_vuln': cvd_vuln.tolist(),
        'timestamp_start': datetime.now().isoformat(),
    }

    # ---- 1) ALL-7 baseline ----
    t0 = time.time()
    res_all = fit_subset(args.model, hc_amps, cvd_vuln, cvd_type,
                         drop_subjs=None, C_original=C_original, grid=grid,
                         do_perm=True)
    res_all['elapsed_s'] = time.time() - t0
    summary['all7'] = res_all
    print(f'  [all7] params={res_all["best_params"]} ρ={res_all["rho"]:.3f} '
          f'p={res_all.get("label_perm_p", float("nan")):.4f} ({res_all["elapsed_s"]:.1f}s)')

    # ---- 2) LOHO 7 ----
    if not args.skip_loho:
        loho = []
        for s in sorted(hc_amps.keys()):
            t0 = time.time()
            r = fit_subset(args.model, hc_amps, cvd_vuln, cvd_type,
                           drop_subjs=[s], C_original=C_original, grid=grid,
                           do_perm=True)
            r['elapsed_s'] = time.time() - t0
            loho.append(r)
            print(f'  [drop_{s}] params={r["best_params"]} ρ={r["rho"]:.3f} '
                  f'p={r.get("label_perm_p", float("nan")):.4f} ({r["elapsed_s"]:.1f}s)')
        summary['loho'] = loho

    # ---- 3) Bootstrap (with-replacement) ----
    if not args.skip_boot and args.n_boot > 0:
        rng = np.random.default_rng(args.seed)
        hc_keys = sorted(hc_amps.keys())
        n_hc = len(hc_keys)
        boot = []
        t_boot_start = time.time()
        for b in range(args.n_boot):
            sample_idx = rng.integers(0, n_hc, size=n_hc)
            sample = [hc_keys[i] for i in sample_idx]
            r = fit_subset(args.model, hc_amps, cvd_vuln, cvd_type,
                           drop_subjs=None, C_original=C_original, grid=grid,
                           do_perm=False, boot_resample_idx=sample)
            boot.append({
                'boot_id': b,
                'sample': sample,
                'best_params': r['best_params'],
                'rho': r['rho'],
            })
            if (b + 1) % 25 == 0:
                el = time.time() - t_boot_start
                rate = (b + 1) / el if el > 0 else 0.0
                print(f'  [boot] {b + 1}/{args.n_boot} '
                      f'rho_avg={np.mean([x["rho"] for x in boot]):.3f} '
                      f'({rate:.2f} fits/s)')
        summary['bootstrap'] = boot

    # ---- 4) HC null distribution ----
    if not args.skip_hc_null:
        hc_null = {}
        # For each HC, treat it as "pseudo-CVD" and refit using the other 6 HC
        for held in sorted(hc_amps.keys()):
            t0 = time.time()
            target_vuln = compute_hc_loco_target(hc_amps, held, C_original)
            r = fit_subset(args.model, hc_amps, target_vuln, cvd_type,
                           drop_subjs=[held], C_original=C_original, grid=grid,
                           do_perm=True)
            hc_null[held] = {
                'pseudo_cvd_vuln': target_vuln.tolist(),
                'best_params': r['best_params'],
                'rho': r['rho'],
                'label_perm_p': r.get('label_perm_p'),
                'elapsed_s': time.time() - t0,
            }
            print(f'  [hc_null held={held}] params={r["best_params"]} '
                  f'ρ={r["rho"]:.3f} p={r.get("label_perm_p", float("nan")):.4f}')
        summary['hc_null'] = hc_null

    summary['timestamp_end'] = datetime.now().isoformat()

    # ---- Save ----
    out = out_dir / f'sub-{args.subject}_{args.roi}_{args.model}.json'
    with open(out, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f'[saved] {out}')

    # ---- Quick stat dump ----
    rhos_all = [summary['all7']['rho']]
    if 'loho' in summary:
        rhos_all.extend([r['rho'] for r in summary['loho']])
    rhos_boot = [r['rho'] for r in summary.get('bootstrap', [])]
    rhos_hc = [v['rho'] for v in summary.get('hc_null', {}).values()]
    print(f'\n  ρ_LOHO+all7 (n={len(rhos_all)}): mean={np.mean(rhos_all):.3f} '
          f'median={np.median(rhos_all):.3f} '
          f'std={np.std(rhos_all, ddof=1) if len(rhos_all) > 1 else 0:.3f} '
          f'min={np.min(rhos_all):.3f} max={np.max(rhos_all):.3f}')
    if rhos_boot:
        ci = np.percentile(rhos_boot, [2.5, 97.5])
        print(f'  ρ_boot (n={len(rhos_boot)}): mean={np.mean(rhos_boot):.3f} '
              f'median={np.median(rhos_boot):.3f} '
              f'std={np.std(rhos_boot, ddof=1):.3f} '
              f'ci95=[{ci[0]:.3f}, {ci[1]:.3f}]')
    if rhos_hc:
        print(f'  ρ_HC_null (n={len(rhos_hc)}): mean={np.mean(rhos_hc):.3f} '
              f'std={np.std(rhos_hc, ddof=1):.3f} '
              f'min={np.min(rhos_hc):.3f} max={np.max(rhos_hc):.3f}')
        # z-score
        if len(rhos_hc) > 1:
            cvd_z = (summary['all7']['rho'] - np.mean(rhos_hc)) / np.std(rhos_hc, ddof=1)
            print(f'  ρ_CVD z-score vs HC null: {cvd_z:.2f}')


if __name__ == '__main__':
    main()
