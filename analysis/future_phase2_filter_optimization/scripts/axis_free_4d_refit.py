"""axis_free_4d_refit.py — 4D Emery-style free-axis refit.

δθ(θ) = β_s · cos(θ − φ_s) + β_c · cos(θ − φ_c)

All four params free: β_s ∈ [bs_min, bs_max], β_c ∈ [bc_min, bc_max],
φ_s ∈ [0°, 360°), φ_c ∈ [0°, 360°). Per Emery 2021: both axis phases data-driven.

Usage:
    python axis_free_4d_refit.py \
        --subject 09 --family protan \
        --bs_min 0 --bs_max 50 --bs_step 5 \
        --bc_min -50 --bc_max 50 --bc_step 5 \
        --phi_step 45 \
        --tag emery_coarse

Output → results/axis_free_4d/sub-{ID}_V4_{tag}_landscape.json
         (large file; only top-K cells stored + best argmin)
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from scipy.stats import pearsonr

_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR))

# Locate future_phase1_forward_model/scripts in both local and server layouts
_PHASE2 = _THIS_DIR.parent
for _base in [_PHASE2.parent, _PHASE2.parent.parent]:
    _fwd = _base / 'future_phase1_forward_model' / 'scripts'
    if _fwd.exists() and str(_fwd) not in sys.path:
        sys.path.insert(0, str(_fwd))
        break
    _fwd2 = _base / 'future_phase1_forward_model'
    if _fwd2.exists() and str(_fwd2) not in sys.path:
        sys.path.insert(0, str(_fwd2))
        break

from utils_forward_model import (  # type: ignore
    HC_SUBJECTS, N_CHANNELS, load_amplitudes, create_basis_full,
)
from step1_fit_loco_v2 import (  # type: ignore
    simulate_mean_hc_loco_legacy, load_cvd_loco_target,
)

THETA_8 = np.array([0, 45, 90, 135, 180, 225, 270, 315], dtype=float)
LOCAL_DATA = (_PHASE2.parent / 'phase1_procrustes_decoding' / 'results'
              / 'visualization' / 'full_dataset_C010_with_residuals')
SERVER_DATA = Path('/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010')

OUT = _THIS_DIR.parent / 'results' / 'axis_free_4d'
OUT.mkdir(parents=True, exist_ok=True)

TIKH_NORM = 32400.0
K_TOPK = 3
LAMBDA_TOPK = 0.5
LAMBDA_CCC = 1.0
LAMBDA_REG = 0.1
TOP_K_STORE = 200  # store top 200 cells (not all) to keep file size manageable


def dt_free(bs, bc, phi_s, phi_c, theta=THETA_8):
    return (bs * np.cos(np.radians(theta - phi_s))
            + bc * np.cos(np.radians(theta - phi_c)))


def get_shifted_design(bs, bc, phi_s, phi_c):
    dt = dt_free(bs, bc, phi_s, phi_c)
    hue_shifted = (THETA_8 + dt) % 360.0
    basis_full = create_basis_full(N_CHANNELS, basis_type='fe')
    idx = np.round(hue_shifted).astype(int) % 360
    return basis_full[idx], dt


def ccc_value(sim, obs):
    sim = np.asarray(sim, dtype=float); obs = np.asarray(obs, dtype=float)
    if np.std(sim) < 1e-10 or np.std(obs) < 1e-10:
        return 0.0
    r, _ = pearsonr(sim, obs)
    if not np.isfinite(r):
        return 0.0
    msim = sim.mean(); mobs = obs.mean()
    ssim = sim.std();  sobs = obs.std()
    denom = ssim**2 + sobs**2 + (msim - mobs)**2
    if denom < 1e-10:
        return 0.0
    return float(2.0 * r * ssim * sobs / denom)


def l_topk_jaccard(vuln_sim, vuln_obs, K=K_TOPK):
    sim_sort = np.argsort(vuln_sim)[:K]
    obs_sort = np.argsort(vuln_obs)[:K]
    S_sim = set(int(i) for i in sim_sort)
    S_obs = set(int(i) for i in obs_sort)
    inter = S_sim & S_obs
    union = S_sim | S_obs
    return float(1.0 - len(inter) / len(union)) if union else 1.0


# ----------------------------------------------------------------------
# Worker pool: HC amps + target vector loaded once per worker via fork
# ----------------------------------------------------------------------
_W_HC_AMPS = None
_W_VULN_CVD = None


def _worker_init(hc_amps_dict, vuln_cvd_arr):
    global _W_HC_AMPS, _W_VULN_CVD
    _W_HC_AMPS = hc_amps_dict
    _W_VULN_CVD = vuln_cvd_arr


def _cell_eval(args):
    bs, bc, phi_s, phi_c = args
    C_shifted, dt = get_shifted_design(bs, bc, phi_s, phi_c)
    vuln_sim, _ = simulate_mean_hc_loco_legacy(_W_HC_AMPS, C_shifted)
    ccc = ccc_value(vuln_sim, _W_VULN_CVD)
    l_ccc = (1.0 - ccc) / 2.0
    lt = l_topk_jaccard(vuln_sim, _W_VULN_CVD)
    tikh = (float(bs)**2 + float(bc)**2) / TIKH_NORM
    L = LAMBDA_CCC * l_ccc + LAMBDA_TOPK * lt + LAMBDA_REG * tikh
    return {
        'bs': float(bs), 'bc': float(bc),
        'phi_s': float(phi_s), 'phi_c': float(phi_c),
        'ccc': ccc, 'l_ccc': l_ccc, 'l_topk': lt,
        'tikh': tikh, 'L_combined': L,
        'vuln_sim': vuln_sim.tolist(),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--subject', required=True)
    p.add_argument('--family', required=True, choices=['protan', 'deutan'])
    p.add_argument('--bs_min', type=float, default=0)
    p.add_argument('--bs_max', type=float, default=50)
    p.add_argument('--bs_step', type=float, default=5)
    p.add_argument('--bc_min', type=float, default=-50)
    p.add_argument('--bc_max', type=float, default=50)
    p.add_argument('--bc_step', type=float, default=5)
    p.add_argument('--phi_s_min', type=float, default=0)
    p.add_argument('--phi_s_max', type=float, default=359)
    p.add_argument('--phi_c_min', type=float, default=0)
    p.add_argument('--phi_c_max', type=float, default=359)
    p.add_argument('--phi_step', type=float, default=30)
    p.add_argument('--tag', required=True)
    p.add_argument('--roi', default='V4')
    p.add_argument('--n_workers', type=int,
                   default=int(os.environ.get('SLURM_CPUS_PER_TASK', 1)),
                   help='multiprocessing workers (default: $SLURM_CPUS_PER_TASK or 1)')
    args = p.parse_args()

    data_dir = SERVER_DATA if SERVER_DATA.exists() else LOCAL_DATA
    print(f'4D free-axis refit  sub-{args.subject} {args.family} '
          f'tag={args.tag}', flush=True)
    print(f'data_dir: {data_dir}', flush=True)

    hc_amps = {s: load_amplitudes(data_dir, s, args.roi) for s in HC_SUBJECTS}
    vuln_cvd = load_cvd_loco_target(args.subject, args.roi)
    print(f'LOCO target: {vuln_cvd.round(3)}', flush=True)

    bs_range = np.arange(args.bs_min, args.bs_max + args.bs_step/2, args.bs_step,
                         dtype=float)
    bc_range = np.arange(args.bc_min, args.bc_max + args.bc_step/2, args.bc_step,
                         dtype=float)
    phi_s_range = np.arange(args.phi_s_min, args.phi_s_max + args.phi_step/2,
                            args.phi_step, dtype=float)
    phi_c_range = np.arange(args.phi_c_min, args.phi_c_max + args.phi_step/2,
                            args.phi_step, dtype=float)
    n_cells = len(bs_range) * len(bc_range) * len(phi_s_range) * len(phi_c_range)
    print(f'Grid: β_s={len(bs_range)} × β_c={len(bc_range)} '
          f'× φ_s={len(phi_s_range)} × φ_c={len(phi_c_range)} = {n_cells} cells',
          flush=True)

    # Build full parameter list
    all_params = []
    for bs in bs_range:
        for bc in bc_range:
            for phi_s in phi_s_range:
                for phi_c in phi_c_range:
                    all_params.append((float(bs), float(bc),
                                       float(phi_s), float(phi_c)))
    n_total = len(all_params)
    print(f'Workers: {args.n_workers}  (multiprocessing fork)', flush=True)

    all_records = []
    best = None
    best_L = np.inf
    t0 = time.time()

    if args.n_workers > 1:
        with ProcessPoolExecutor(
            max_workers=args.n_workers,
            initializer=_worker_init,
            initargs=(hc_amps, vuln_cvd),
        ) as ex:
            chunk = max(1, n_total // (args.n_workers * 8))
            for i, rec in enumerate(ex.map(_cell_eval, all_params,
                                            chunksize=chunk)):
                all_records.append(rec)
                if rec['L_combined'] < best_L:
                    best_L = rec['L_combined']; best = rec
                if (i + 1) % max(1, n_total // 20) == 0:
                    el = time.time() - t0
                    pct = 100.0 * (i + 1) / n_total
                    eta = el * (n_total - (i + 1)) / max(i + 1, 1)
                    print(f'  {i+1}/{n_total} ({pct:.1f}%)  '
                          f'elapsed={el:.0f}s  eta={eta:.0f}s  '
                          f'best_L={best_L:.4f} '
                          f'@ (β_s={best["bs"]:.0f},β_c={best["bc"]:+.0f},'
                          f'φ_s={best["phi_s"]:.0f},φ_c={best["phi_c"]:.0f})',
                          flush=True)
    else:
        _worker_init(hc_amps, vuln_cvd)
        for i, params in enumerate(all_params):
            rec = _cell_eval(params)
            all_records.append(rec)
            if rec['L_combined'] < best_L:
                best_L = rec['L_combined']; best = rec
            if (i + 1) % max(1, n_total // 20) == 0:
                el = time.time() - t0
                pct = 100.0 * (i + 1) / n_total
                eta = el * (n_total - (i + 1)) / max(i + 1, 1)
                print(f'  {i+1}/{n_total} ({pct:.1f}%)  '
                      f'elapsed={el:.0f}s  eta={eta:.0f}s  '
                      f'best_L={best_L:.4f}',
                      flush=True)

    print(f'Done in {time.time()-t0:.0f}s', flush=True)

    # Sort all records by L, store top-K (full grid stats not stored to save space)
    all_records.sort(key=lambda c: c['L_combined'])
    top_k = all_records[:TOP_K_STORE]

    # Also compute marginal best for each fixed φ_s, φ_c pair
    by_axis = {}
    for r in all_records:
        key = (r['phi_s'], r['phi_c'])
        if key not in by_axis or r['L_combined'] < by_axis[key]['L_combined']:
            by_axis[key] = r
    axis_marginals = sorted(by_axis.values(), key=lambda r: r['L_combined'])

    out = {
        'subject': f'sub-{args.subject}', 'roi': args.roi,
        'family': args.family, 'tag': args.tag,
        'loss': '1·L_ccc + 0.5·l_topk + 0.1·Tikh',
        'grid': {
            'bs': [args.bs_min, args.bs_max, args.bs_step],
            'bc': [args.bc_min, args.bc_max, args.bc_step],
            'phi_s': [args.phi_s_min, args.phi_s_max, args.phi_step],
            'phi_c': [args.phi_c_min, args.phi_c_max, args.phi_step],
        },
        'n_cells_total': n_total,
        'best': best,
        'top_k_records': top_k,
        'axis_marginals_sorted': axis_marginals[:50],
        'vuln_cvd': vuln_cvd.tolist(),
    }
    out_fn = OUT / f'sub-{args.subject}_{args.roi}_{args.tag}_landscape.json'
    with open(out_fn, 'w') as f:
        json.dump(out, f)
    print(f'\nBEST: β_s={best["bs"]:.0f}  β_c={best["bc"]:+.0f}  '
          f'φ_s={best["phi_s"]:.0f}°  φ_c={best["phi_c"]:.0f}°  '
          f'L={best["L_combined"]:.4f}  CCC={best["ccc"]:+.3f}',
          flush=True)
    print(f'Wrote {out_fn.name} ({out_fn.stat().st_size/1024:.0f} KB)', flush=True)


if __name__ == '__main__':
    main()
