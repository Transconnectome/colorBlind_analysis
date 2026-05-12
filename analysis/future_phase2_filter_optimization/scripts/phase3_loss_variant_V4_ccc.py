"""phase3_loss_variant_V4_ccc.py — Variant V4: CCC-only loss + smoothness regularizer.

CCC = 2·r·σ_sim·σ_obs / (σ_sim² + σ_obs² + (μ_sim−μ_obs)²)

L_ccc    = (1 − ccc) / NORM['ccc']    ; NORM=2.0 → L_ccc ∈ [0, 1]
L_smooth = mean(circular_adjacent_diff(δθ)²) / 32400   ; 32400 = 180²
L_fit    = 1.0 · L_ccc + 0.1 · L_smooth

Applies to sub-{08,09} V4. Writes landscape + summary + F4-style figure.
"""
from __future__ import annotations
import json
from pathlib import Path

import numpy as np

from phase3_loss_variant_helpers import (
    load_cache, build_landscape,
    concordance_correlation_coefficient,
    spearman_safe, pearson_safe,
    NORM, OUT_BASE, generate_f4_style_figure,
)

VARIANT = 'V4_ccc'
OUT_DIR = OUT_BASE / VARIANT
OUT_DIR.mkdir(parents=True, exist_ok=True)


def _circular_adjacent_diff(dt: np.ndarray) -> np.ndarray:
    """Wrap-around adjacent diff for the 8-element δθ vector."""
    dt = np.asarray(dt, dtype=float)
    # next - current (with wrap)
    nxt = np.roll(dt, -1)
    d = nxt - dt
    # wrap into (-180, 180]
    d = (d + 180.0) % 360.0 - 180.0
    return d


def smoothness(dt: np.ndarray) -> float:
    d = _circular_adjacent_diff(dt)
    return float(np.mean(d ** 2) / 32400.0)


def ccc_loss_fn(sim: np.ndarray, obs: np.ndarray, dt: np.ndarray) -> dict:
    ccc = concordance_correlation_coefficient(sim, obs)
    l_ccc = (1.0 - ccc) / NORM['ccc']
    l_smooth = smoothness(dt)
    l_fit = 1.0 * l_ccc + 0.1 * l_smooth

    r = pearson_safe(sim, obs)
    rho = spearman_safe(sim, obs)
    sim_arr = np.asarray(sim); obs_arr = np.asarray(obs)
    return {
        'l_fit': float(l_fit),
        'l_ccc': float(l_ccc),
        'l_smooth': float(l_smooth),
        'ccc': float(ccc),
        'spearman_r': float(rho),
        'pearson_r': float(r),
        'sim_mean': float(sim_arr.mean()),
        'sim_std': float(sim_arr.std()),
        'obs_mean': float(obs_arr.mean()),
        'obs_std': float(obs_arr.std()),
    }


def _top_n(landscape, key='l_fit', n=10, reverse=False):
    sorted_ls = sorted(landscape, key=lambda r: r[key], reverse=reverse)
    return [{k: v for k, v in row.items() if k != 'vuln_sim'} for row in sorted_ls[:n]]


def process_subject(subj_id: str):
    cache = load_cache(subj_id, 'V4')
    landscape = build_landscape(cache, ccc_loss_fn)

    best = min(landscape, key=lambda r: r['l_fit'])
    best_ccc = max(landscape, key=lambda r: r['ccc'])

    summary = {
        'subject': subj_id,
        'roi': 'V4',
        'variant': VARIANT,
        'formula': 'L_fit = 1.0*L_ccc + 0.1*L_smooth ; L_ccc=(1-CCC)/2',
        'grid_bounds': cache.get('grid_bounds'),
        'n_cells': len(landscape),
        'best_by_l_fit': best,
        'best_by_ccc': best_ccc,
        'top_10_by_l_fit': _top_n(landscape, 'l_fit', 10, reverse=False),
        'top_10_by_ccc':   _top_n(landscape, 'ccc',   10, reverse=True),
    }

    out_summary = OUT_DIR / f'sub-{subj_id}_V4_summary.json'
    out_landscape = OUT_DIR / f'sub-{subj_id}_V4_landscape.json'
    with open(out_summary, 'w') as f:
        json.dump(summary, f, indent=2)
    with open(out_landscape, 'w') as f:
        json.dump({'subject': subj_id, 'roi': 'V4', 'variant': VARIANT,
                   'cells': landscape}, f)
    print(f'sub-{subj_id} V4: best (bs={best["bs"]}, bc={best["bc"]}) '
          f'l_fit={best["l_fit"]:.4f} ccc={best["ccc"]:.3f} '
          f'rho={best["spearman_r"]:.3f} r={best["pearson_r"]:.3f} '
          f'sim_std={best["sim_std"]:.3f}')
    return cache, landscape, best


def main():
    cache_08, ls_08, best_08 = process_subject('08')
    cache_09, ls_09, best_09 = process_subject('09')

    fig_path = OUT_DIR / 'fig_V4_ccc.png'
    generate_f4_style_figure(
        variant_name='V4 (CCC)',
        cache_08=cache_08, landscape_08=ls_08,
        cache_09=cache_09, landscape_09=ls_09,
        out_path=fig_path,
        loss_label='L_fit(CCC)',
        landscape_key='spearman_r',
        landscape_label='Spearman ρ',
    )
    print(f'Figure saved: {fig_path}')


if __name__ == '__main__':
    main()
