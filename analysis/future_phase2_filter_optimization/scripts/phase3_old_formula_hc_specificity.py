"""phase3_old_formula_hc_specificity.py — HC specificity under OLD formula.

For each HC i in {sub-01, ..., sub-06}:
  - hc_pool = remaining 5 HCs (leave-one-HC-out)
  - Run OLD-formula 2-component grid search using hc_pool as training mean,
    HC i's V4 LOCO vulnerability as target
  - Record best (β_s, β_c, norm, ρ, L_fit)

Note: sub-07 V4 has only 16 voxels → nan in correlations (per project memory),
      so excluded from HC pool.

After per-HC fits, bootstrap HC norms and compute specificity for key filters:
  - (10, -32) simplified argmin
  - (16, +40) V4 CCC argmin (primary question)
  - (40, +26) P2a-behavior-best
  - (38, +7)  V4-only OLD
  - (38, -14) Canonical CURRENT (for reference)

Outputs:
  - results/old_formula/hc_specificity_norms.csv  (per-HC fit results)
  - results/old_formula/hc_specificity_filters.csv  (per-filter boot_frac + verdict)
  - results/old_formula/hc_specificity_summary.json (combined)

Loss: simplified L_fit = L_vuln + 0.5·L_rank (same as primary OLD refit).
"""
from __future__ import annotations
import csv
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR))

from old_formula_refit import (
    HC_SUBJECTS, N_CHANNELS, HUE_ANGLES, THETA_8,
    load_amplitudes, load_cvd_loco_target, create_basis_full,
    simulate_mean_hc_loco_legacy, get_shifted_design_old,
    LOCAL_DATA, SERVER_DATA,
)

OUTDIR = _THIS_DIR.parent / 'results' / 'old_formula'
OUTDIR.mkdir(parents=True, exist_ok=True)

# HC pool: sub-01 to sub-06 only (sub-07 V4 has nan due to 16 voxels)
HC_POOL_AVAILABLE = ['01', '02', '03', '04', '05', '06']
print(f'HC pool: {HC_POOL_AVAILABLE} (sub-07 excluded — V4 nan)')


def fit_loo_hc(target_hc: str, hc_pool: list[str]) -> dict:
    """Fit OLD formula to target_hc's vulnerability using hc_pool as training mean."""
    print(f'\n=== Fitting sub-{target_hc} (target) with pool: {hc_pool} ===')
    data_dir = SERVER_DATA if SERVER_DATA.exists() else LOCAL_DATA
    hc_amps = {s: load_amplitudes(data_dir, s, 'V4') for s in hc_pool}
    vuln_target = load_cvd_loco_target(target_hc, 'V4')
    print(f'  Target vuln: {np.round(vuln_target, 3).tolist()}')

    bs_range = np.arange(0, 51, 2, dtype=float)
    bc_range = np.arange(-50, 51, 2, dtype=float)
    best = None
    best_lfit = np.inf
    t0 = time.time()

    for bs in bs_range:
        for bc in bc_range:
            C_shifted, dt = get_shifted_design_old(bs, bc)
            vuln_sim, _ = simulate_mean_hc_loco_legacy(hc_amps, C_shifted)
            rho, _ = spearmanr(vuln_sim, vuln_target)
            rho = float(rho) if np.isfinite(rho) else 0.0
            l_vuln = float(np.mean((vuln_sim - vuln_target) ** 2)) / 4.0
            l_rank = (1.0 - rho) / 2.0
            l_fit = l_vuln + 0.5 * l_rank
            if l_fit < best_lfit:
                best_lfit = l_fit
                best = {
                    'bs': float(bs), 'bc': float(bc),
                    'spearman_r': rho,
                    'l_vuln': l_vuln, 'l_rank': l_rank, 'l_fit': l_fit,
                    'delta_theta': dt.tolist(),
                }
    elapsed = time.time() - t0
    norm = math.sqrt(best['bs']**2 + best['bc']**2)
    best['norm'] = norm
    print(f'  Best: β=({best["bs"]:.0f}, {best["bc"]:+.0f}) '
          f'norm={norm:.1f}° ρ={best["spearman_r"]:.3f} L_fit={best["l_fit"]:.4f}  '
          f'({elapsed:.0f}s)')
    return best


def compute_filter_specificity(filter_name: str, beta_s: float, beta_c: float,
                                 hc_norms: list[float], n_boot: int = 10000,
                                 seed: int = 0) -> dict:
    cvd_norm = math.sqrt(beta_s**2 + beta_c**2)
    hc = np.array(hc_norms, dtype=float)
    rng = np.random.default_rng(seed)
    boot_means = rng.choice(hc, size=(n_boot, len(hc)), replace=True).mean(axis=1)
    boot_frac = float((boot_means < cvd_norm).mean())
    if boot_frac >= 0.975:
        verdict = '✓✓'
    elif boot_frac >= 0.90:
        verdict = '~~'
    else:
        verdict = '✗'
    return {
        'filter_name': filter_name,
        'beta_s': beta_s, 'beta_c': beta_c,
        'cvd_norm': round(cvd_norm, 2),
        'hc_mean_norm': round(float(hc.mean()), 2),
        'hc_std_norm': round(float(hc.std(ddof=1)), 2),
        'hc_min': round(float(hc.min()), 2),
        'hc_max': round(float(hc.max()), 2),
        'boot_frac': round(boot_frac, 4),
        'verdict': verdict,
    }


def main():
    # ---- Step 1: LOO HC fits ----
    hc_fits = {}
    t0_all = time.time()
    for target in HC_POOL_AVAILABLE:
        pool = [s for s in HC_POOL_AVAILABLE if s != target]
        hc_fits[target] = fit_loo_hc(target, pool)
    print(f'\nTotal LOO fit time: {time.time()-t0_all:.0f}s')

    # ---- Save HC norms CSV ----
    csv_norms = OUTDIR / 'hc_specificity_norms.csv'
    with open(csv_norms, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['hc_subject', 'beta_s', 'beta_c', 'norm',
                    'spearman_r', 'l_vuln', 'l_rank', 'l_fit'])
        for sid, fit in hc_fits.items():
            w.writerow([f'sub-{sid}', fit['bs'], fit['bc'],
                        round(fit['norm'], 2),
                        round(fit['spearman_r'], 3),
                        round(fit['l_vuln'], 4),
                        round(fit['l_rank'], 4),
                        round(fit['l_fit'], 4)])
    print(f'Wrote {csv_norms}')

    # ---- Step 2: bootstrap specificity for key filters ----
    hc_norms = [hc_fits[sid]['norm'] for sid in HC_POOL_AVAILABLE]
    filters = [
        ('OLD simplified argmin (10,-32)',    10,  -32),
        ('V4 CCC argmin (16,+40)',            16,  +40),
        ('P2a-behavior-best (40,+26)',        40,  +26),
        ('V4-only OLD (38,+7)',               38,  +7),
        ('Canonical CURRENT (38,-14)',        38,  -14),
        ('OLD top10 cluster (8,-28)',          8,  -28),
    ]
    results = []
    for fname, bs, bc in filters:
        r = compute_filter_specificity(fname, bs, bc, hc_norms)
        results.append(r)
        print(f'  {fname:>35}: norm={r["cvd_norm"]:.2f}, '
              f'boot_frac={r["boot_frac"]:.4f}  {r["verdict"]}')

    # ---- Save filter CSV ----
    csv_filt = OUTDIR / 'hc_specificity_filters.csv'
    with open(csv_filt, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['filter_name', 'beta_s', 'beta_c', 'cvd_norm',
                    'hc_mean_norm', 'hc_std_norm', 'hc_min', 'hc_max',
                    'boot_frac', 'verdict'])
        for r in results:
            w.writerow([r['filter_name'], r['beta_s'], r['beta_c'], r['cvd_norm'],
                        r['hc_mean_norm'], r['hc_std_norm'],
                        r['hc_min'], r['hc_max'],
                        r['boot_frac'], r['verdict']])
    print(f'Wrote {csv_filt}')

    # ---- Combined JSON ----
    summary = {
        'framework': 'OLD CIElab-direct 2-component, simplified L_fit',
        'hc_pool': [f'sub-{s}' for s in HC_POOL_AVAILABLE],
        'hc_pool_size': len(HC_POOL_AVAILABLE),
        'note_sub07': 'sub-07 V4 excluded — only 16 voxels (nan in correlations)',
        'hc_fits': {f'sub-{sid}': fit for sid, fit in hc_fits.items()},
        'hc_norms_list': hc_norms,
        'hc_mean_norm': float(np.mean(hc_norms)),
        'hc_std_norm': float(np.std(hc_norms, ddof=1)),
        'filter_specificity': results,
    }
    out_json = OUTDIR / 'hc_specificity_summary.json'
    with open(out_json, 'w') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f'Wrote {out_json}')


if __name__ == '__main__':
    main()
