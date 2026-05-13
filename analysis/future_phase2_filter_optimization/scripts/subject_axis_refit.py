"""subject_axis_refit.py — Generalized V4 refit with parametric (family, θ_conf, grid).

Usage:
    python subject_axis_refit.py --subject 08 --family deutan --theta_conf 175.7 \
        --bs_max 50 --bc_min -60 --bc_max 60 --step 2 --tag CIELab

    python subject_axis_refit.py --subject 09 --family protan --theta_conf 11.8 \
        --bs_max 50 --bc_min -60 --bc_max 60 --step 2 --tag CIELab

Output → results/sub09_protan_refit/sub-{ID}_V4_{tag}_landscape.json
"""
from __future__ import annotations
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.stats import pearsonr

_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR))

_PHASE2 = _THIS_DIR.parent
for _base in [_PHASE2.parent, _PHASE2.parent.parent]:
    _fwd = _base / 'future_phase1_forward_model' / 'scripts'
    if _fwd.exists() and str(_fwd) not in sys.path:
        sys.path.insert(0, str(_fwd)); break
    _fwd2 = _base / 'future_phase1_forward_model'
    if _fwd2.exists() and str(_fwd2) not in sys.path:
        sys.path.insert(0, str(_fwd2)); break

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

OUT = _THIS_DIR.parent / 'results' / 'sub09_protan_refit'
OUT.mkdir(parents=True, exist_ok=True)

TIKH_NORM = 32400.0
K_TOPK = 3
LAMBDA_TOPK = 0.5
LAMBDA_CCC = 1.0
LAMBDA_REG = 0.1


def dt_family(bs: float, bc: float, theta_conf: float,
              theta: np.ndarray = THETA_8) -> np.ndarray:
    return (bs * np.cos(np.radians(theta - 90.0))
            + bc * np.cos(np.radians(theta - theta_conf)))


def get_shifted_design(bs: float, bc: float, theta_conf: float):
    dt = dt_family(bs, bc, theta_conf)
    hue_shifted = (THETA_8 + dt) % 360.0
    basis_full = create_basis_full(N_CHANNELS, basis_type='fe')
    idx = np.round(hue_shifted).astype(int) % 360
    return basis_full[idx], dt


def ccc_value(sim: np.ndarray, obs: np.ndarray) -> float:
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


def l_topk_jaccard(vuln_sim: np.ndarray, vuln_obs: np.ndarray,
                   K: int = K_TOPK) -> float:
    sim_sort = np.argsort(vuln_sim)[:K]
    obs_sort = np.argsort(vuln_obs)[:K]
    S_sim = set(int(i) for i in sim_sort)
    S_obs = set(int(i) for i in obs_sort)
    inter = S_sim & S_obs
    union = S_sim | S_obs
    if not union:
        return 1.0
    return float(1.0 - len(inter) / len(union))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--subject', required=True)
    p.add_argument('--family', required=True, choices=['protan', 'deutan'])
    p.add_argument('--theta_conf', type=float, required=True)
    p.add_argument('--bs_min', type=float, default=0)
    p.add_argument('--bs_max', type=float, default=50)
    p.add_argument('--bc_min', type=float, default=-60)
    p.add_argument('--bc_max', type=float, default=60)
    p.add_argument('--step', type=float, default=2)
    p.add_argument('--tag', required=True, help='filename tag')
    p.add_argument('--roi', default='V4')
    args = p.parse_args()

    data_dir = SERVER_DATA if SERVER_DATA.exists() else LOCAL_DATA
    print(f'sub-{args.subject} {args.family} ROI={args.roi} '
          f'θ_conf={args.theta_conf}° tag={args.tag}')
    print(f'data_dir: {data_dir}')

    hc_amps = {s: load_amplitudes(data_dir, s, args.roi) for s in HC_SUBJECTS}
    vuln_cvd = load_cvd_loco_target(args.subject, args.roi)
    print(f'LOCO target: {vuln_cvd.round(3)}')

    bs_range = np.arange(args.bs_min, args.bs_max + args.step / 2, args.step,
                         dtype=float)
    bc_range = np.arange(args.bc_min, args.bc_max + args.step / 2, args.step,
                         dtype=float)
    n_cells = len(bs_range) * len(bc_range)
    print(f'Grid: {len(bs_range)} × {len(bc_range)} = {n_cells} cells')

    landscape = []
    t0 = time.time()
    for i, bs in enumerate(bs_range):
        for bc in bc_range:
            C_shifted, dt = get_shifted_design(bs, bc, args.theta_conf)
            vuln_sim, _ = simulate_mean_hc_loco_legacy(hc_amps, C_shifted)
            ccc = ccc_value(vuln_sim, vuln_cvd)
            l_ccc = (1.0 - ccc) / 2.0
            lt = l_topk_jaccard(vuln_sim, vuln_cvd)
            tikh = (float(bs)**2 + float(bc)**2) / TIKH_NORM
            L = LAMBDA_CCC * l_ccc + LAMBDA_TOPK * lt + LAMBDA_REG * tikh
            landscape.append({
                'bs': float(bs), 'bc': float(bc),
                'vuln_sim': vuln_sim.tolist(),
                'delta_theta': dt.tolist(),
                'ccc': ccc, 'l_ccc': l_ccc,
                'l_topk': lt, 'tikh': tikh,
                'L_combined': L,
            })
        if (i + 1) % 5 == 0 or i == len(bs_range) - 1:
            print(f'  [{i+1}/{len(bs_range)} β_s] '
                  f'elapsed={time.time()-t0:.0f}s', flush=True)

    elapsed = time.time() - t0
    print(f'Done in {elapsed:.0f}s')

    best = min(landscape, key=lambda c: c['L_combined'])
    print(f"\nBEST argmin: (β_s={best['bs']:.0f}, β_c={best['bc']:+.0f})  "
          f"L={best['L_combined']:.4f}  CCC={best['ccc']:+.3f}  "
          f"l_topk={best['l_topk']:.3f}")

    top5 = sorted(landscape, key=lambda c: c['L_combined'])[:5]
    print("Top-5:")
    for k, c in enumerate(top5):
        print(f"  #{k+1}: (β_s={c['bs']:.0f}, β_c={c['bc']:+.0f})  "
              f"L={c['L_combined']:.4f}  CCC={c['ccc']:+.3f}")

    out = {
        'subject': f'sub-{args.subject}', 'roi': args.roi,
        'family': args.family, 'theta_conf': args.theta_conf,
        'tag': args.tag,
        'loss': '1·L_ccc + 0.5·l_topk + 0.1·Tikh',
        'grid': {'bs': [args.bs_min, args.bs_max, args.step],
                 'bc': [args.bc_min, args.bc_max, args.step]},
        'best': best, 'top5': top5,
        'vuln_cvd': vuln_cvd.tolist(),
        'cells': landscape,
    }
    out_fn = OUT / f'sub-{args.subject}_{args.roi}_{args.tag}_landscape.json'
    with open(out_fn, 'w') as f:
        json.dump(out, f)
    print(f'Wrote {out_fn.name} ({out_fn.stat().st_size/1024:.0f} KB)')


if __name__ == '__main__':
    main()
