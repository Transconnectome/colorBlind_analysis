"""phase3_lsmooth_sensitivity.py — Sweep ε (L_smooth weight) over cached 4-term landscapes.

Goal
----
Test the hypothesis: increasing L_smooth weight collapses HC LOO argmin toward
β=0 (because HC L_fit landscapes are flat) while CVD argmin remains near the
canonical optimum (because CVD has a sharp basin).

Inputs (cached, no simulator rerun needed)
------------------------------------------
- CVD: results/old_formula/sub-08_V4_4term_landscape.json (1326 cells, per-cell
  l_vuln/l_rank/l_rdm/l_smooth already normalised)
- HC LOO: results/fits/phase_a_2component_hc_sanity/sub-{0X}_V4_2component.json
  (1326 cells each, same per-cell breakdown). sub-01..sub-06 V4 available.
  (Note: sub-09 V4 4term is cached too.)

Weight recomposition
--------------------
L_fit(ε) = 1.0·l_vuln + 0.5·l_rank + 0.2·l_rdm + ε·l_smooth
(α, β, δ fixed at canonical values, only ε swept.)

ε sweep: 0.1 (canonical), 0.5, 1.0, 2.0, 5.0.

Outputs
-------
- results/old_formula/lsmooth_sensitivity_summary.json
- results/old_formula/sub-XX_V4_smooth{w}.json (argmin records per (subj, ε))
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / 'results'
OUT_DIR = RESULTS / 'old_formula'
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Canonical weights (alpha, beta, delta fixed; epsilon swept)
ALPHA, BETA, DELTA = 1.0, 0.5, 0.2
EPS_SWEEP = [0.1, 0.5, 1.0, 2.0, 5.0]

CVD_FILES = {
    'sub-08_V4': RESULTS / 'old_formula' / 'sub-08_V4_4term_landscape.json',
    'sub-09_V4': RESULTS / 'old_formula' / 'sub-09_V4_4term_landscape.json',
}
HC_FILES = {
    f'sub-0{k}_V4': RESULTS / 'fits' / 'phase_a_2component_hc_sanity' / f'sub-0{k}_V4_2component.json'
    for k in range(1, 7)
}


def load_cvd_cells(path):
    with open(path) as f:
        rows = json.load(f)
    return [
        {
            'bs': float(r['bs']),
            'bc': float(r['bc']),
            'l_vuln': float(r['l_vuln']),
            'l_rank': float(r['l_rank']),
            'l_rdm': float(r['l_rdm']),
            'l_smooth': float(r['l_smooth']),
            'spearman_r': float(r['spearman_r']),
        }
        for r in rows
    ]


def load_hc_cells(path):
    with open(path) as f:
        d = json.load(f)
    return [
        {
            'bs': float(r['params'][0]),
            'bc': float(r['params'][1]),
            'l_vuln': float(r['l_vuln']),
            'l_rank': float(r['l_rank']),
            'l_rdm': float(r['l_rdm']),
            'l_smooth': float(r['l_smooth']),
            'spearman_r': float(r['spearman_r']),
        }
        for r in d['landscape']
    ]


def recompose_argmin(cells, eps):
    best = None
    for c in cells:
        L = ALPHA * c['l_vuln'] + BETA * c['l_rank'] + DELTA * c['l_rdm'] + eps * c['l_smooth']
        if best is None or L < best['l_fit']:
            best = {
                'bs': c['bs'],
                'bc': c['bc'],
                'norm': (c['bs'] ** 2 + c['bc'] ** 2) ** 0.5,
                'l_fit': L,
                'l_vuln': c['l_vuln'],
                'l_rank': c['l_rank'],
                'l_rdm': c['l_rdm'],
                'l_smooth': c['l_smooth'],
                'spearman_r': c['spearman_r'],
            }
    return best


def landscape_flatness(cells, eps):
    """Quantify how peaked the landscape is at the chosen eps."""
    Ls = [
        ALPHA * c['l_vuln'] + BETA * c['l_rank'] + DELTA * c['l_rdm'] + eps * c['l_smooth']
        for c in cells
    ]
    Lmin = min(Ls)
    Lmean = sum(Ls) / len(Ls)
    Lmax = max(Ls)
    # depth: how far below the mean the basin sits, normalised by spread
    depth = (Lmean - Lmin) / (Lmax - Lmin + 1e-12)
    return {'l_min': Lmin, 'l_mean': Lmean, 'l_max': Lmax, 'basin_depth': depth}


def run():
    summary = {'weights_canonical': {'alpha': ALPHA, 'beta': BETA, 'delta': DELTA, 'epsilon': 0.1},
               'epsilon_sweep': EPS_SWEEP,
               'cvd': {},
               'hc': {}}

    # CVD
    for tag, path in CVD_FILES.items():
        if not path.exists():
            print(f'[SKIP] {tag} not found')
            continue
        cells = load_cvd_cells(path)
        per_eps = {}
        for eps in EPS_SWEEP:
            argmin = recompose_argmin(cells, eps)
            flat = landscape_flatness(cells, eps)
            per_eps[str(eps)] = {**argmin, **flat}
            # save per-eps record
            out_path = OUT_DIR / f'{tag}_smooth{eps}.json'
            with open(out_path, 'w') as f:
                json.dump({**{'subject': tag, 'epsilon': eps, 'alpha': ALPHA,
                              'beta': BETA, 'delta': DELTA}, **argmin, **flat}, f, indent=2)
        summary['cvd'][tag] = per_eps
        print(f'\nCVD {tag}:')
        print(f'  {"eps":>6} {"argmin":>12} {"norm":>7} {"L_fit":>8} {"basin":>7}')
        for eps in EPS_SWEEP:
            r = per_eps[str(eps)]
            print(f'  {eps:>6.1f} ({r["bs"]:>3.0f},{r["bc"]:>+4.0f}) {r["norm"]:>7.1f} '
                  f'{r["l_fit"]:>8.4f} {r["basin_depth"]:>7.3f}')

    # HC
    for tag, path in HC_FILES.items():
        if not path.exists():
            print(f'[SKIP] {tag} not found')
            continue
        cells = load_hc_cells(path)
        per_eps = {}
        for eps in EPS_SWEEP:
            argmin = recompose_argmin(cells, eps)
            flat = landscape_flatness(cells, eps)
            per_eps[str(eps)] = {**argmin, **flat}
            out_path = OUT_DIR / f'{tag}_smooth{eps}.json'
            with open(out_path, 'w') as f:
                json.dump({**{'subject': tag, 'epsilon': eps, 'alpha': ALPHA,
                              'beta': BETA, 'delta': DELTA}, **argmin, **flat}, f, indent=2)
        summary['hc'][tag] = per_eps
        print(f'\nHC {tag}:')
        print(f'  {"eps":>6} {"argmin":>12} {"norm":>7} {"L_fit":>8} {"basin":>7}')
        for eps in EPS_SWEEP:
            r = per_eps[str(eps)]
            print(f'  {eps:>6.1f} ({r["bs"]:>3.0f},{r["bc"]:>+4.0f}) {r["norm"]:>7.1f} '
                  f'{r["l_fit"]:>8.4f} {r["basin_depth"]:>7.3f}')

    # HC summary: mean argmin norm per epsilon
    print(f'\n=== HC mean argmin norm per ε ===')
    for eps in EPS_SWEEP:
        norms = [summary['hc'][s][str(eps)]['norm'] for s in summary['hc']]
        zero_count = sum(1 for s in summary['hc'] if summary['hc'][s][str(eps)]['norm'] < 1.5)
        print(f'  ε={eps:>4.1f}  mean HC norm = {sum(norms)/len(norms):>5.1f}  '
              f'(zero-collapse: {zero_count}/{len(norms)})')

    out_path = OUT_DIR / 'lsmooth_sensitivity_summary.json'
    with open(out_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f'\nWrote {out_path}')


if __name__ == '__main__':
    run()
