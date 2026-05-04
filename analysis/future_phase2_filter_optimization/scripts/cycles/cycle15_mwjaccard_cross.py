#!/usr/bin/env python3
"""
cycle15_mwjaccard_cross.py — mw_jaccard cross-criterion variants.

Per Loss Inventory 2026-05-03: mw_jaccard_loss @ V4 is the only single
metric that statistically separates both CVD subjects from HC distribution
(emp_p=0.17 each).

Test cross-ROI combinations with mw_jaccard as the V4 anchor:

  Option 2:  L = α·mw_jaccard(V4) + β·l_rank(V1) + 0.2·Tikh
  Option 3:  L = α·mw_jaccard(V4) + β·mw_jaccard(V1) + 0.2·Tikh
  Option 4:  L = α·mw_jaccard(V4) + β·(1-spearman_r)(V4) + 0.2·Tikh

For each variant, evaluate HC sanity (rank emp_p < 0.20 = sig).
"""

import json
import csv
import sys
from pathlib import Path
import numpy as np

_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR))

LANDSCAPE_DIR = (_SCRIPT_DIR.parent.parent / 'results'
                 / 'cycles')
OUT_JSON = LANDSCAPE_DIR / 'cycle15_mwjaccard_cross.json'
OUT_CSV = LANDSCAPE_DIR / 'cycle15_mwjaccard_cross.csv'

HC = ['01', '02', '03', '04', '05', '06']
CVD = ['08', '09']
ALL = HC + CVD

_BS = np.arange(0.0, 81.0, 2.0)
_BC = np.arange(-60.0, 61.0, 2.0)
_BS_GRID, _BC_GRID = np.meshgrid(_BS, _BC, indexing='ij')
NORM_GRID = (_BS_GRID / 80.0) ** 2 + (_BC_GRID / 60.0) ** 2
LAM = 0.2


def load_landscape(subj, roi, metric):
    p = LANDSCAPE_DIR / f'sub-{subj}_{roi}_landscape.json'
    if not p.exists():
        return None
    with open(p) as f:
        d = json.load(f)
    if metric not in d:
        return None
    return np.array(d[metric])


def find_min(grid):
    idx = np.unravel_index(np.argmin(grid), grid.shape)
    return float(_BS[idx[0]]), float(_BC[idx[1]]), float(grid[idx]), idx


def empirical_p(hc_norms, cvd_norm):
    return sum(1 for h in hc_norms if h >= cvd_norm) / len(hc_norms)


def beta_norm(bs, bc):
    return float(np.sqrt(bs ** 2 + bc ** 2))


VARIANTS = {
    'opt2_v4mwj_v1lrank': {
        'V4_metric': 'mw_jaccard_loss',
        'V1_metric': 'l_rank',
        'desc': 'α·mw_jaccard(V4) + β·l_rank(V1) + 0.2·Tikh',
    },
    'opt3_v4mwj_v1mwj': {
        'V4_metric': 'mw_jaccard_loss',
        'V1_metric': 'mw_jaccard_loss',
        'desc': 'α·mw_jaccard(V4) + β·mw_jaccard(V1) + 0.2·Tikh',
    },
    'opt4_v4mwj_v4spear': {
        'V4_metric': 'mw_jaccard_loss',
        'V1_metric': 'spearman_r',  # but as V4
        'desc': 'α·mw_jaccard(V4) + β·(1-spearman_r)(V4) + 0.2·Tikh',
    },
}

WEIGHT_COMBOS = [(1.0, 1.0), (0.5, 1.0), (1.0, 0.5),
                 (2.0, 1.0), (1.0, 2.0)]

results = {'meta': {'cycle': 15, 'task': 'mw_jaccard cross-criterion variants',
                    'variants': {k: v['desc'] for k, v in VARIANTS.items()}},
           'per_variant': {}, 'csv_rows': []}

print('=' * 70)
print('Cycle 15: mw_jaccard cross-criterion')
print('=' * 70)

for vname, vinfo in VARIANTS.items():
    print(f'\n--- Variant {vname} ---')
    print(f'  {vinfo["desc"]}')

    v_results = {'description': vinfo['desc'], 'per_subject': {}}

    for alpha, beta in WEIGHT_COMBOS:
        wkey = f'a{alpha}_b{beta}'
        v_results['per_subject'][wkey] = {}
        norms = {}

        for subj in ALL:
            G_v4 = load_landscape(subj, 'V4', vinfo['V4_metric'])

            if vname == 'opt4_v4mwj_v4spear':
                # Both at V4, second is 1-spearman
                G_other = load_landscape(subj, 'V4', 'spearman_r')
                if G_other is not None:
                    G_other = 1.0 - G_other  # convert to loss
            else:
                G_other = load_landscape(subj, 'V1', vinfo['V1_metric'])

            if G_v4 is None or G_other is None:
                continue

            L = alpha * G_v4 + beta * G_other + LAM * NORM_GRID
            bs, bc, val, _ = find_min(L)
            norms[subj] = beta_norm(bs, bc)
            v_results['per_subject'][wkey][subj] = {
                'bs': bs, 'bc': bc, 'L': val,
                'norm': round(norms[subj], 2),
            }

        # HC sanity
        hc_norms = [norms[s] for s in HC if s in norms]
        s08 = norms.get('08')
        s09 = norms.get('09')
        ep_08 = empirical_p(hc_norms, s08) if s08 is not None else None
        ep_09 = empirical_p(hc_norms, s09) if s09 is not None else None
        if ep_08 is not None and ep_09 is not None:
            sig08 = ep_08 <= 0.20
            sig09 = ep_09 <= 0.20
            verdict = ('✓✓ both CVD distinct' if (sig08 and sig09)
                       else ('✓ one distinct' if (sig08 or sig09)
                             else '✗ neither distinct'))
        else:
            verdict = '? insufficient'

        v_results['per_subject'][wkey]['HC_mean_norm'] = float(
            np.mean(hc_norms)) if hc_norms else None
        v_results['per_subject'][wkey]['HC_n'] = len(hc_norms)
        v_results['per_subject'][wkey]['emp_p_08'] = ep_08
        v_results['per_subject'][wkey]['emp_p_09'] = ep_09
        v_results['per_subject'][wkey]['verdict'] = verdict

        s08_str = (f"({norms['08']:.0f})" if '08' in norms else '—')
        s09_str = (f"({norms['09']:.0f})" if '09' in norms else '—')
        ep08_str = f'{ep_08:.2f}' if ep_08 is not None else '—'
        ep09_str = f'{ep_09:.2f}' if ep_09 is not None else '—'
        print(f'  α={alpha}, β={beta}: '
              f'sub-08 norm{s08_str}={norms.get("08", 0):.0f} ep_p={ep08_str}, '
              f'sub-09 norm{s09_str}={norms.get("09", 0):.0f} ep_p={ep09_str}, '
              f'HC mean={np.mean(hc_norms):.1f}  →  {verdict}')

        # CSV row
        for s in ALL:
            if s in norms:
                e = v_results['per_subject'][wkey][s]
                results['csv_rows'].append({
                    'variant': vname,
                    'alpha': alpha, 'beta': beta,
                    'subject': f'sub-{s}',
                    'role': 'HC' if s in HC else 'CVD',
                    'bs': e['bs'], 'bc': e['bc'], 'norm': e['norm'],
                    'emp_p_08': ep_08, 'emp_p_09': ep_09,
                    'verdict': verdict,
                })

    results['per_variant'][vname] = v_results

# Save
with open(OUT_JSON, 'w') as f:
    json.dump(results, f, indent=2, default=str)
with open(OUT_CSV, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(results['csv_rows'][0].keys()))
    w.writeheader()
    w.writerows(results['csv_rows'])

print(f'\nSaved: {OUT_JSON}')
print(f'Saved: {OUT_CSV}')

# Final verdict
print('\n' + '=' * 70)
print('BEST VARIANT × WEIGHT (by ✓✓ verdict)')
print('=' * 70)
for vname, vres in results['per_variant'].items():
    for wkey, e in vres['per_subject'].items():
        if e.get('verdict', '').startswith('✓✓'):
            print(f'  {vname} | {wkey} | sub-08 ep_p={e["emp_p_08"]:.2f}, '
                  f'sub-09 ep_p={e["emp_p_09"]:.2f}')
