"""V1 — Demeaned MSE loss variant.

L_vuln_dm = demeaned_mse(sim, obs) / NORM['vuln']
L_rank    = (1 - spearman_safe(sim, obs)) / NORM['rank']
L_smooth  = mean(circular_adjacent_diff(δθ)²) / 32400
L_fit     = 1.0·L_vuln_dm + 0.5·L_rank + 0.1·L_smooth

(No L_rdm in this variant.)
"""
from __future__ import annotations
import json
from pathlib import Path

import numpy as np

from phase3_loss_variant_helpers import (
    load_cache, demeaned_mse, mse, spearman_safe, pearson_safe,
    NORM, build_landscape, generate_f4_style_figure, OUT_BASE,
)

VARIANT = 'V1_demeaned_mse'
OUT_DIR = OUT_BASE / VARIANT
OUT_DIR.mkdir(parents=True, exist_ok=True)

SMOOTH_NORM = 32400.0
W_VULN = 1.0
W_RANK = 0.5
W_SMOOTH = 0.1


def circular_smooth_raw(delta_theta: np.ndarray) -> float:
    dt = np.asarray(delta_theta)
    diffs = np.diff(dt, append=dt[0])
    diffs = (diffs + 180.0) % 360.0 - 180.0
    return float(np.mean(diffs ** 2))


def per_cell_loss(sim, obs, dt):
    sim = np.asarray(sim, dtype=float)
    obs = np.asarray(obs, dtype=float)

    # Demeaned MSE (offset-free)
    l_vuln_dm_raw = demeaned_mse(sim, obs)
    l_vuln = l_vuln_dm_raw / NORM['vuln']

    # Original (with offset) for comparison
    l_vuln_with_offset_raw = mse(sim, obs)
    offset_squared = (float(sim.mean()) - float(obs.mean())) ** 2
    # Sanity: MSE = demeaned_MSE + offset²  (algebraic identity)

    # Spearman rank
    rho = spearman_safe(sim, obs)
    l_rank_raw = 1.0 - rho
    l_rank = l_rank_raw / NORM['rank']

    # Pearson (record only)
    r = pearson_safe(sim, obs)

    # Smooth (circular diff of δθ)
    l_smooth_raw = circular_smooth_raw(dt)
    l_smooth = l_smooth_raw / SMOOTH_NORM

    l_fit = W_VULN * l_vuln + W_RANK * l_rank + W_SMOOTH * l_smooth

    return {
        'l_fit': float(l_fit),
        'l_vuln': float(l_vuln),                       # demeaned, normalized
        'l_vuln_raw': float(l_vuln_dm_raw),
        'l_vuln_with_offset': float(l_vuln_with_offset_raw / NORM['vuln']),
        'l_vuln_with_offset_raw': float(l_vuln_with_offset_raw),
        'offset_squared': float(offset_squared),
        'l_rank': float(l_rank),
        'l_rank_raw': float(l_rank_raw),
        'l_smooth': float(l_smooth),
        'l_smooth_raw': float(l_smooth_raw),
        'spearman_r': float(rho),
        'pearson_r': float(r),
    }


def run_subject(subj_id: str, roi: str = 'V4'):
    cache = load_cache(subj_id, roi)
    landscape = build_landscape(cache, per_cell_loss)
    best = min(landscape, key=lambda r: r['l_fit'])

    summary = {
        'variant': VARIANT,
        'subject': cache.get('subject', f'sub-{subj_id}'),
        'roi': roi,
        'weights': {'vuln': W_VULN, 'rank': W_RANK, 'smooth': W_SMOOTH},
        'loss_formula': '1.0·L_vuln_dm + 0.5·L_rank + 0.1·L_smooth',
        'norm': {'vuln': NORM['vuln'], 'rank': NORM['rank'], 'smooth': SMOOTH_NORM},
        'n_cells': len(landscape),
        'best': {
            'bs': best['bs'], 'bc': best['bc'],
            'l_fit': best['l_fit'],
            'l_vuln': best['l_vuln'],
            'l_vuln_raw': best['l_vuln_raw'],
            'l_vuln_with_offset': best['l_vuln_with_offset'],
            'l_vuln_with_offset_raw': best['l_vuln_with_offset_raw'],
            'offset_squared': best['offset_squared'],
            'l_rank': best['l_rank'],
            'l_smooth': best['l_smooth'],
            'spearman_r': best['spearman_r'],
            'pearson_r': best['pearson_r'],
            'vuln_sim': best['vuln_sim'],
            'vuln_sim_std': float(np.std(best['vuln_sim'])),
            'vuln_obs_std': float(np.std(cache['vuln_cvd'])),
            'delta_theta': best['delta_theta'],
        },
        'composition_at_best': {
            'w_vuln_dm_contribution': W_VULN * best['l_vuln'],
            'w_rank_contribution':    W_RANK * best['l_rank'],
            'w_smooth_contribution':  W_SMOOTH * best['l_smooth'],
        },
    }

    (OUT_DIR / f'sub-{subj_id}_{roi}_landscape.json').write_text(
        json.dumps(landscape, indent=2))
    (OUT_DIR / f'sub-{subj_id}_{roi}_summary.json').write_text(
        json.dumps(summary, indent=2))

    return cache, landscape, summary


def main():
    print(f'[{VARIANT}] running...')
    cache_08, ls_08, sum_08 = run_subject('08', 'V4')
    cache_09, ls_09, sum_09 = run_subject('09', 'V4')

    for subj, s in (('sub-08', sum_08), ('sub-09', sum_09)):
        b = s['best']
        print(f"  {subj} V4: bs={b['bs']:.0f} bc={b['bc']:+.0f}  "
              f"L_fit={b['l_fit']:.4f}  ρ={b['spearman_r']:.3f}  r={b['pearson_r']:.3f}  "
              f"sim_std={b['vuln_sim_std']:.3f}  "
              f"L_vuln_dm={b['l_vuln']:.4f}  L_vuln_offset={b['l_vuln_with_offset']:.4f}  "
              f"offset²={b['offset_squared']:.4f}")

    fig_path = OUT_DIR / 'fig_V1_demeaned_mse.png'
    generate_f4_style_figure(
        VARIANT, cache_08, ls_08, cache_09, ls_09,
        out_path=fig_path,
        loss_label='L_fit(demeaned)',
    )
    print(f'[{VARIANT}] figure → {fig_path}')


if __name__ == '__main__':
    main()
