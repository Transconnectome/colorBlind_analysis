"""phase3_old_formula_4term.py — full §3 4-term L_fit under OLD CIELab-direct formula.

Implements CURRENT canonical loss form under OLD δθ formula:
    L_fit = 1.0·L_vuln + 0.5·L_rank + 0.2·L_rdm + 0.1·L_smooth

where:
  L_vuln   = mean((vuln_sim − vuln_cvd)²) / 4.0
  L_rank   = (1 − Spearman_ρ(vuln_sim, vuln_cvd)) / 2.0
  L_rdm    = (1 − cosine(ΔRDM_sim, ΔRDM_obs)) / 2.0
  L_smooth = mean(circular_adjacent_diff(δθ)²) / 32400

Subjects: sub-08 V4, sub-09 V4. (sub-08 V1 / sub-09 V1 skipped per user.)
Output: results/old_formula/sub-XX_VV_4term_{summary,landscape}.json
"""
from __future__ import annotations
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR))
sys.path.insert(0, str(_THIS_DIR / 'forward_models'))

from old_formula_refit import (
    HC_SUBJECTS, N_CHANNELS, HUE_ANGLES, THETA_8, THETA_CONF,
    load_amplitudes, load_cvd_loco_target, create_basis_full,
    simulate_mean_hc_loco_legacy, get_shifted_design_old, dt_old,
    LOCAL_DATA, SERVER_DATA,
)
from diagnostic_delta_rdm import (
    compute_delta_rdm_obs, compute_delta_rdm_sim, compute_rdm_correlation,
)
from step1_fit_loco_v2 import precompute_hc_W

OUTDIR = _THIS_DIR.parent / 'results' / 'old_formula'
OUTDIR.mkdir(parents=True, exist_ok=True)
VARIANT_TAG = '4term'


def cosine_sim(a, b):
    a = np.asarray(a).ravel(); b = np.asarray(b).ravel()
    na = np.linalg.norm(a); nb = np.linalg.norm(b)
    if na < 1e-10 or nb < 1e-10:
        return 0.0
    return float(a @ b / (na * nb))


# Normalization constants (match loco_distortion_fit.py NORM)
NORM = {'vuln': 4.0, 'rank': 2.0, 'rdm': 2.0, 'smooth': 32400.0}
WEIGHTS = {'alpha': 1.0, 'beta': 0.5, 'delta': 0.2, 'epsilon': 0.1}


def compute_L_fit_4term(vuln_sim, vuln_cvd, dt, delta_rdm_sim, delta_rdm_obs):
    """All 4 terms + total."""
    L_vuln_raw = float(np.mean((vuln_sim - vuln_cvd) ** 2))
    L_vuln = L_vuln_raw / NORM['vuln']

    rho, _ = spearmanr(vuln_sim, vuln_cvd)
    rho = float(rho) if np.isfinite(rho) else 0.0
    L_rank_raw = 1.0 - rho
    L_rank = L_rank_raw / NORM['rank']

    cos_sim = cosine_sim(delta_rdm_sim, delta_rdm_obs)
    L_rdm_raw = 1.0 - cos_sim
    L_rdm = L_rdm_raw / NORM['rdm']

    dt_arr = np.asarray(dt)
    diffs = np.diff(dt_arr, append=dt_arr[0])
    diffs = (diffs + 180.0) % 360.0 - 180.0   # wrap to [-180, 180]
    L_smooth_raw = float(np.mean(diffs ** 2))
    L_smooth = L_smooth_raw / NORM['smooth']

    L_fit = (WEIGHTS['alpha'] * L_vuln
             + WEIGHTS['beta'] * L_rank
             + WEIGHTS['delta'] * L_rdm
             + WEIGHTS['epsilon'] * L_smooth)
    return {
        'l_fit': L_fit, 'l_vuln': L_vuln, 'l_rank': L_rank,
        'l_rdm': L_rdm, 'l_smooth': L_smooth,
        'spearman_r': rho, 'rdm_cosine': cos_sim,
    }


def fit_subject_roi(subj_id: str, roi: str):
    print(f'\n{"="*70}')
    print(f'=== sub-{subj_id} {roi} (OLD formula, 4-term L_fit) ===')
    print(f'{"="*70}')

    data_dir = SERVER_DATA if SERVER_DATA.exists() else LOCAL_DATA
    hc_amps = {s: load_amplitudes(data_dir, s, roi) for s in HC_SUBJECTS}
    amp_cvd = load_amplitudes(data_dir, subj_id, roi)
    vuln_cvd = load_cvd_loco_target(subj_id, roi)
    print(f'CVD vuln: {np.round(vuln_cvd, 3).tolist()}')

    # Baseline design
    basis_full = create_basis_full(N_CHANNELS, basis_type='fe')
    C_baseline = basis_full[HUE_ANGLES]   # (8, K)

    # Pre-compute hc_W_dict
    print('Precomputing HC weights...')
    hc_W_dict, hc_alpha_dict = precompute_hc_W(hc_amps, C_baseline)

    # Pre-compute ΔRDM_obs (does not depend on β)
    print('Computing ΔRDM_obs...')
    delta_rdm_obs, rdm_cvd, rdm_hc_mean, _ = compute_delta_rdm_obs(
        amp_cvd, hc_amps, distance='correlation')
    print(f'  ΔRDM_obs norm: {np.linalg.norm(delta_rdm_obs):.4f}')

    # Grid
    bs_range = np.arange(0, 51, 2, dtype=float)
    bc_range = np.arange(-50, 51, 2, dtype=float)
    n_cells = len(bs_range) * len(bc_range)
    print(f'Grid: {len(bs_range)} × {len(bc_range)} = {n_cells} cells')

    landscape = []
    t0 = time.time()
    for i, bs in enumerate(bs_range):
        for bc in bc_range:
            C_shifted, dt = get_shifted_design_old(bs, bc)

            # vuln_sim
            vuln_sim, _ = simulate_mean_hc_loco_legacy(hc_amps, C_shifted)

            # ΔRDM_sim
            delta_rdm_sim, _ = compute_delta_rdm_sim(
                hc_W_dict, C_shifted, C_baseline, distance='correlation')

            # 4-term loss
            loss = compute_L_fit_4term(vuln_sim, vuln_cvd, dt,
                                       delta_rdm_sim, delta_rdm_obs)
            entry = {'bs': float(bs), 'bc': float(bc),
                     'delta_theta': dt.tolist(),
                     **loss}
            landscape.append(entry)
        if (i + 1) % max(1, len(bs_range) // 5) == 0:
            best_so_far = min(landscape, key=lambda r: r['l_fit'])
            print(f'  [{i+1}/{len(bs_range)} β_s] '
                  f'best L_fit={best_so_far["l_fit"]:.4f} @ '
                  f'β=({best_so_far["bs"]:.0f}, {best_so_far["bc"]:+.0f})  '
                  f'ρ={best_so_far["spearman_r"]:.3f}  rdm_cos={best_so_far["rdm_cosine"]:.3f}')

    elapsed = time.time() - t0
    print(f'Done in {elapsed:.0f}s')

    # Sort
    by_lfit = sorted(landscape, key=lambda r: r['l_fit'])
    by_rho = sorted(landscape, key=lambda r: -r['spearman_r'])

    print(f'\nTop 10 by L_fit:')
    for r in by_lfit[:10]:
        print(f'  β=({r["bs"]:>4.0f},{r["bc"]:>+5.0f}) '
              f'L={r["l_fit"]:.4f} '
              f'(vuln={r["l_vuln"]:.4f} rank={r["l_rank"]:.4f} '
              f'rdm={r["l_rdm"]:.4f} sm={r["l_smooth"]:.4f}) ρ={r["spearman_r"]:.3f}')

    out = {
        'subject': subj_id, 'roi': roi,
        'formula': 'OLD CIELab-direct + 4-term L_fit',
        'weights': WEIGHTS,
        'norm': NORM,
        'grid_bounds': {'bs': [0, 50, 2], 'bc': [-50, 50, 2]},
        'n_cells': n_cells,
        'elapsed_s': elapsed,
        'delta_rdm_obs': delta_rdm_obs.tolist(),
        'best_by_l_fit': by_lfit[0],
        'best_by_rho': by_rho[0],
        'top_10_by_l_fit': by_lfit[:10],
        'top_10_by_rho': by_rho[:10],
    }
    fn = f'sub-{subj_id}_{roi}_{VARIANT_TAG}'
    with open(OUTDIR / f'{fn}_summary.json', 'w') as f:
        json.dump(out, f, indent=2)
    with open(OUTDIR / f'{fn}_landscape.json', 'w') as f:
        json.dump(landscape, f, indent=2)
    print(f'\nWrote {fn}_summary.json + _landscape.json')
    return out


def main():
    cfg = [('08', 'V4'), ('09', 'V4')]
    for sid, roi in cfg:
        fit_subject_roi(sid, roi)


if __name__ == '__main__':
    main()
