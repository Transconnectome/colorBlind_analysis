"""V3: Reduce L_rank weight (β=0.3 and β=0.2).

L_vuln  = mse(sim, obs) / NORM['vuln']
L_rank  = (1 - spearman_safe) / NORM['rank']
L_smooth = mean(circular adjacent diff(δθ)²) / 32400

L_fit_β = 1.0·L_vuln + β·L_rank + 0.1·L_smooth
"""
from __future__ import annotations
import json
from pathlib import Path

import numpy as np

from phase3_loss_variant_helpers import (
    OUT_BASE, load_cache, mse, spearman_safe, pearson_safe, NORM,
    build_landscape, generate_f4_style_figure,
)


def circular_adjacent_diff_sq_mean(dt):
    """Mean of (δθ[i] − δθ[(i+1)%N])² for N=8."""
    dt = np.asarray(dt, dtype=float)
    diffs = dt - np.roll(dt, -1)
    return float(np.mean(diffs ** 2))


def make_loss_fn(beta_rank: float):
    def loss_fn(sim, obs, dt):
        l_vuln = mse(sim, obs) / NORM['vuln']
        rho = spearman_safe(sim, obs)
        l_rank = (1.0 - rho) / NORM['rank']
        l_smooth = circular_adjacent_diff_sq_mean(dt) / 32400.0
        l_fit = 1.0 * l_vuln + beta_rank * l_rank + 0.1 * l_smooth
        return {
            'l_vuln': l_vuln,
            'l_rank': l_rank,
            'l_smooth': l_smooth,
            'l_fit': l_fit,
            'spearman_r': rho,
            'pearson_r': pearson_safe(sim, obs),
        }
    return loss_fn


def summary_from_landscape(landscape):
    best = min(landscape, key=lambda r: r['l_fit'])
    return {
        'best': {
            'bs': best['bs'], 'bc': best['bc'],
            'l_fit': best['l_fit'], 'l_vuln': best['l_vuln'],
            'l_rank': best['l_rank'], 'l_smooth': best['l_smooth'],
            'spearman_r': best['spearman_r'], 'pearson_r': best['pearson_r'],
            'vuln_sim': best['vuln_sim'], 'delta_theta': best['delta_theta'],
        },
        'n_cells': len(landscape),
    }


def run_variant(beta_rank: float, variant_subdir: str, loss_label: str):
    out_dir = OUT_BASE / variant_subdir
    out_dir.mkdir(parents=True, exist_ok=True)
    loss_fn = make_loss_fn(beta_rank)

    cache_08 = load_cache('08', 'V4')
    cache_09 = load_cache('09', 'V4')

    landscape_08 = build_landscape(cache_08, loss_fn)
    landscape_09 = build_landscape(cache_09, loss_fn)

    # save landscapes (full per-cell records)
    with open(out_dir / 'sub-08_V4_landscape.json', 'w') as f:
        json.dump(landscape_08, f)
    with open(out_dir / 'sub-09_V4_landscape.json', 'w') as f:
        json.dump(landscape_09, f)

    summary_08 = summary_from_landscape(landscape_08)
    summary_08['subject'] = '08'; summary_08['roi'] = 'V4'
    summary_08['variant'] = variant_subdir
    summary_08['beta_rank'] = beta_rank
    summary_08['loss_formula'] = f'1.0·L_vuln + {beta_rank}·L_rank + 0.1·L_smooth'
    with open(out_dir / 'sub-08_V4_summary.json', 'w') as f:
        json.dump(summary_08, f, indent=2)

    summary_09 = summary_from_landscape(landscape_09)
    summary_09['subject'] = '09'; summary_09['roi'] = 'V4'
    summary_09['variant'] = variant_subdir
    summary_09['beta_rank'] = beta_rank
    summary_09['loss_formula'] = f'1.0·L_vuln + {beta_rank}·L_rank + 0.1·L_smooth'
    with open(out_dir / 'sub-09_V4_summary.json', 'w') as f:
        json.dump(summary_09, f, indent=2)

    fig_path = out_dir / f'fig_{variant_subdir}.png'
    best_08, best_09 = generate_f4_style_figure(
        variant_name=variant_subdir,
        cache_08=cache_08, landscape_08=landscape_08,
        cache_09=cache_09, landscape_09=landscape_09,
        out_path=fig_path,
        loss_label=loss_label,
    )
    print(f'[{variant_subdir}] sub-08 best: bs={best_08["bs"]:.0f}, bc={best_08["bc"]:.0f}, '
          f'L_fit={best_08["l_fit"]:.4f}, ρ={best_08["spearman_r"]:.3f}, '
          f'r={best_08["pearson_r"]:.3f}, L_vuln={best_08["l_vuln"]:.4f}, '
          f'L_rank={best_08["l_rank"]:.4f}, L_smooth={best_08["l_smooth"]:.4f}')
    print(f'[{variant_subdir}] sub-09 best: bs={best_09["bs"]:.0f}, bc={best_09["bc"]:.0f}, '
          f'L_fit={best_09["l_fit"]:.4f}, ρ={best_09["spearman_r"]:.3f}, '
          f'r={best_09["pearson_r"]:.3f}, L_vuln={best_09["l_vuln"]:.4f}, '
          f'L_rank={best_09["l_rank"]:.4f}, L_smooth={best_09["l_smooth"]:.4f}')
    # Dynamic range of best sim
    sim08 = np.array(best_08['vuln_sim']); sim09 = np.array(best_09['vuln_sim'])
    obs08 = np.array(cache_08['vuln_cvd']); obs09 = np.array(cache_09['vuln_cvd'])
    print(f'[{variant_subdir}] sub-08 sim range=[{sim08.min():.3f},{sim08.max():.3f}] '
          f'span={sim08.ptp():.3f} | obs span={obs08.ptp():.3f}')
    print(f'[{variant_subdir}] sub-09 sim range=[{sim09.min():.3f},{sim09.max():.3f}] '
          f'span={sim09.ptp():.3f} | obs span={obs09.ptp():.3f}')

    return best_08, best_09


if __name__ == '__main__':
    print('=== V3 β=0.3 ===')
    b08_03, b09_03 = run_variant(0.3, 'V3_rank_w03', 'L_fit(β=0.3)')
    print('\n=== V3 β=0.2 ===')
    b08_02, b09_02 = run_variant(0.2, 'V3_rank_w02', 'L_fit(β=0.2)')
