#!/usr/bin/env python3
"""analyze_bootstrap.py — Cycle 1 analysis: robust estimators + specificity check.

Reads JSONs from results/cycle_bootstrap/main/ and computes:
- mean / median / trimmed-mean / mode (KDE peak) of ρ
- HC null mean+std → z-score for CVD
- separation between sub-10 and sub-08/09
- HC LOO null vs CVD CI overlap (specificity proxy)

Output:
  - Console table of robust estimators
  - JSON summary at results/cycle_bootstrap/summary.json

Usage:
    python analyze_bootstrap.py --results_dir results/cycle_bootstrap/main
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

_SCRIPT_DIR = Path(__file__).resolve().parent
_PHASE2_DIR = _SCRIPT_DIR.parent.parent


def trimmed_mean(x, prop=0.2):
    x = np.sort(np.asarray(x))
    n = len(x)
    k = int(n * prop)
    if k * 2 >= n:
        return float(np.median(x))
    return float(np.mean(x[k: n - k]))


def kde_mode(x, bandwidth=None):
    """Approximate mode via Gaussian KDE."""
    from scipy.stats import gaussian_kde
    x = np.asarray(x, dtype=float)
    if len(x) < 4:
        return float(np.median(x))
    try:
        kde = gaussian_kde(x, bw_method=bandwidth)
        grid = np.linspace(x.min() - 0.05, x.max() + 0.05, 512)
        dens = kde(grid)
        return float(grid[np.argmax(dens)])
    except Exception:
        return float(np.median(x))


def summarize_one(d):
    """Compute robust estimators for one subject/roi/model JSON."""
    out = {
        'subject': d['subject'],
        'roi': d['roi'],
        'model': d['model'],
        'cvd_type': d['cvd_type'],
        'all7_rho': d['all7']['rho'],
        'all7_params': d['all7']['best_params'],
        'all7_label_p': d['all7'].get('label_perm_p'),
    }

    # LOHO
    rhos_loho = [d['all7']['rho']] + [r['rho'] for r in d.get('loho', [])]
    if rhos_loho:
        out['loho_n'] = len(rhos_loho)
        out['loho_mean'] = float(np.mean(rhos_loho))
        out['loho_median'] = float(np.median(rhos_loho))
        out['loho_std'] = float(np.std(rhos_loho, ddof=1)) if len(rhos_loho) > 1 else 0.0
        out['loho_min'] = float(np.min(rhos_loho))
        out['loho_max'] = float(np.max(rhos_loho))
        out['loho_trimmed20'] = trimmed_mean(rhos_loho, 0.2)
        # parameter spread
        params_arr = np.array([d['all7']['best_params']]
                              + [r['best_params'] for r in d.get('loho', [])])
        out['loho_param_std'] = np.std(params_arr, axis=0, ddof=1).tolist()

    # Bootstrap
    rhos_boot = [r['rho'] for r in d.get('bootstrap', [])]
    if rhos_boot:
        out['boot_n'] = len(rhos_boot)
        out['boot_mean'] = float(np.mean(rhos_boot))
        out['boot_median'] = float(np.median(rhos_boot))
        out['boot_std'] = float(np.std(rhos_boot, ddof=1))
        out['boot_ci95'] = np.percentile(rhos_boot, [2.5, 97.5]).tolist()
        out['boot_trimmed20'] = trimmed_mean(rhos_boot, 0.2)
        out['boot_mode_kde'] = kde_mode(rhos_boot)

    # HC null
    rhos_hc = [v['rho'] for v in d.get('hc_null', {}).values()]
    if rhos_hc:
        out['hc_null_n'] = len(rhos_hc)
        out['hc_null_mean'] = float(np.mean(rhos_hc))
        out['hc_null_median'] = float(np.median(rhos_hc))
        out['hc_null_std'] = float(np.std(rhos_hc, ddof=1)) if len(rhos_hc) > 1 else 0.0
        out['hc_null_min'] = float(np.min(rhos_hc))
        out['hc_null_max'] = float(np.max(rhos_hc))
        # z-score for CVD
        if out['hc_null_std'] > 0:
            out['cvd_z_vs_hc_null'] = (
                (out['all7_rho'] - out['hc_null_mean']) / out['hc_null_std'])
        # rank-based emp_p (one-sided): how many HC null ≥ CVD ρ?
        n_ge = int(np.sum(np.array(rhos_hc) >= out['all7_rho']))
        out['hc_null_emp_p'] = (n_ge + 1) / (len(rhos_hc) + 1)

    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--results_dir', default=str(
        _PHASE2_DIR / 'results' / 'cycle_bootstrap' / 'main'))
    ap.add_argument('--output_path', default=str(
        _PHASE2_DIR / 'results' / 'cycle_bootstrap' / 'summary.json'))
    args = ap.parse_args()

    res_dir = Path(args.results_dir)
    files = sorted(res_dir.glob('sub-*_*_*.json'))
    if not files:
        print(f'No result files in {res_dir}')
        return

    summaries = []
    for f in files:
        with open(f) as fh:
            d = json.load(fh)
        summaries.append(summarize_one(d))

    # Pretty print
    print(f"{'subj':>4} {'roi':>3} {'model':>10} | "
          f"{'all7':>6} {'mean':>6} {'med':>6} {'tm20':>6} "
          f"{'std':>6} | "
          f"{'HCnull μ±σ':>16} {'z_CVD':>6} {'emp_p':>6}")
    for s in summaries:
        zstr = f"{s.get('cvd_z_vs_hc_null', float('nan')):>6.2f}"
        empstr = f"{s.get('hc_null_emp_p', float('nan')):>6.3f}"
        hc_str = f"{s.get('hc_null_mean', float('nan')):.3f}±{s.get('hc_null_std', float('nan')):.3f}"
        print(f"{s['subject']:>4} {s['roi']:>3} {s['model']:>10} | "
              f"{s['all7_rho']:>6.3f} {s.get('loho_mean', float('nan')):>6.3f} "
              f"{s.get('loho_median', float('nan')):>6.3f} "
              f"{s.get('loho_trimmed20', float('nan')):>6.3f} "
              f"{s.get('loho_std', float('nan')):>6.3f} | "
              f"{hc_str:>16} {zstr} {empstr}")

    out_path = Path(args.output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w') as f:
        json.dump(summaries, f, indent=2)
    print(f'\n[saved] {out_path}')


if __name__ == '__main__':
    main()
