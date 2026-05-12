"""phase3_loss_variant_V2_pearson.py — V2: Pearson-added loss variant.

Loss:
  L_vuln    = mse(sim, obs) / NORM['vuln']               (NORM=4.0)
  L_rank    = (1 - spearman_safe) / NORM['rank']         (NORM=2.0)
  L_pearson = (1 - pearson_safe) / NORM['pearson']       (NORM=2.0)
  L_smooth  = mean(circular_adjacent_diff(dtheta)^2) / 32400
  L_fit     = 1.0*L_vuln + 0.5*L_rank + 0.5*L_pearson + 0.1*L_smooth

Inputs : results/old_formula_vulnsim_cache/sub-{08,09}_V4_cache.json
Outputs: results/old_formula_loss_variants/V2_pearson_added/
            sub-{08,09}_V4_{landscape,summary}.json
            fig_V2_pearson_added.png/.pdf
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np

from phase3_loss_variant_helpers import (
    load_cache, build_landscape, generate_f4_style_figure,
    mse, spearman_safe, pearson_safe, NORM, OUT_BASE,
)

VARIANT_NAME = 'V2_pearson_added'
OUT_DIR = OUT_BASE / VARIANT_NAME
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Smooth normalization: mean squared adjacent diff across 8 hues; max plausible
# circular jump on a 180-degree-rotated channel is ~180; (180)^2 = 32400.
SMOOTH_NORM = 32400.0


def circular_adjacent_diff_sq(dtheta) -> float:
    """Mean squared circular adjacent diff across the 8-hue cycle.

    Wraps angles to (-180, 180] then squares each adjacent difference,
    including the wrap from hue[-1] -> hue[0].
    """
    dt = np.asarray(dtheta, dtype=float)
    n = dt.size
    diffs = np.empty(n, dtype=float)
    for i in range(n):
        d = dt[(i + 1) % n] - dt[i]
        # wrap to (-180, 180]
        d = ((d + 180.0) % 360.0) - 180.0
        diffs[i] = d
    return float(np.mean(diffs ** 2))


def loss_v2(sim, obs, dt):
    l_vuln = mse(sim, obs) / NORM['vuln']
    s = spearman_safe(sim, obs)
    p = pearson_safe(sim, obs)
    l_rank = (1.0 - s) / NORM['rank']
    l_pearson = (1.0 - p) / NORM['pearson']
    l_smooth = circular_adjacent_diff_sq(dt) / SMOOTH_NORM
    l_fit = 1.0 * l_vuln + 0.5 * l_rank + 0.5 * l_pearson + 0.1 * l_smooth
    return {
        'l_fit': float(l_fit),
        'l_vuln': float(l_vuln),
        'l_rank': float(l_rank),
        'l_pearson': float(l_pearson),
        'l_smooth': float(l_smooth),
        'spearman_r': float(s),
        'pearson_r': float(p),
    }


def run_subject(subj_id: str, roi: str = 'V4'):
    cache = load_cache(subj_id, roi)
    landscape = build_landscape(cache, loss_v2)
    # Save landscape
    ls_path = OUT_DIR / f'sub-{subj_id}_{roi}_landscape.json'
    with open(ls_path, 'w') as f:
        json.dump({
            'subject': subj_id, 'roi': roi, 'variant': VARIANT_NAME,
            'loss_formula': 'L_fit = 1.0*L_vuln + 0.5*L_rank + 0.5*L_pearson + 0.1*L_smooth',
            'norm': {**NORM, 'smooth': SMOOTH_NORM},
            'n_cells': len(landscape),
            'cells': landscape,
        }, f)

    # Find best
    best = min(landscape, key=lambda r: r['l_fit'])
    vuln_cvd = np.array(cache['vuln_cvd'])
    vuln_sim = np.array(best['vuln_sim'])
    sim_std = float(np.std(vuln_sim))
    obs_std = float(np.std(vuln_cvd))

    summary = {
        'subject': subj_id, 'roi': roi, 'variant': VARIANT_NAME,
        'best': {k: best[k] for k in
                 ['bs', 'bc', 'l_fit', 'l_vuln', 'l_rank', 'l_pearson',
                  'l_smooth', 'spearman_r', 'pearson_r']},
        'best_vuln_sim': best['vuln_sim'],
        'best_delta_theta': best['delta_theta'],
        'vuln_cvd': cache['vuln_cvd'],
        'sim_std': sim_std,
        'obs_std': obs_std,
        'dynamic_range_ratio': sim_std / obs_std if obs_std > 0 else None,
    }
    summary_path = OUT_DIR / f'sub-{subj_id}_{roi}_summary.json'
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

    return cache, landscape, summary


def main():
    print(f'[{VARIANT_NAME}] Running...')
    cache_08, ls_08, sum_08 = run_subject('08', 'V4')
    cache_09, ls_09, sum_09 = run_subject('09', 'V4')

    fig_path = OUT_DIR / f'fig_{VARIANT_NAME}.png'
    best_08, best_09 = generate_f4_style_figure(
        VARIANT_NAME,
        cache_08, ls_08,
        cache_09, ls_09,
        fig_path,
        loss_label='L_fit(+Pearson)',
    )

    print(f'[sub-08 V4] best: bs={best_08["bs"]:.0f}, bc={best_08["bc"]:+.0f}')
    print(f'           l_fit={best_08["l_fit"]:.4f}  spearman={best_08["spearman_r"]:.3f}  pearson={best_08["pearson_r"]:.3f}')
    print(f'           sim_std={sum_08["sim_std"]:.4f}  obs_std={sum_08["obs_std"]:.4f}  ratio={sum_08["dynamic_range_ratio"]:.3f}')
    print(f'[sub-09 V4] best: bs={best_09["bs"]:.0f}, bc={best_09["bc"]:+.0f}')
    print(f'           l_fit={best_09["l_fit"]:.4f}  spearman={best_09["spearman_r"]:.3f}  pearson={best_09["pearson_r"]:.3f}')
    print(f'           sim_std={sum_09["sim_std"]:.4f}  obs_std={sum_09["obs_std"]:.4f}  ratio={sum_09["dynamic_range_ratio"]:.3f}')
    print(f'Outputs at: {OUT_DIR}')


if __name__ == '__main__':
    main()
