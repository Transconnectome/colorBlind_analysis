"""p2a_landscape_explore.py — Direct P2a landscape per axis, weight sweep.

For each cached landscape JSON (β_s, β_c, φ_c=axis fixed):
  1. Compute P2a per cell directly from (β_s, β_c, 90°, axis) via forward map.
  2. Re-compute L_combined with varying weights:
     λ_tikh ∈ {0.1, 0.5, 1.0, 2.0}
     λ_topk ∈ {0.5, 1.0}
     L_p2a-penalty option (1 − P2a) added with λ_p2a ∈ {0.0, 0.5, 1.0}
  3. Find argmin per weight config; report new (β_s, β_c) + P2a + L.
  4. Also report P2a-max cell (loss-free).

Cached landscapes:
  results/axis_3way/sub-{08,09}_V4_{Stockman150,CIELab175p7,Stockman16,CIELab11p8,
                                    Stockman16ext,CIELab11p8ext,axis150_fine,
                                    bs_only}_landscape.json

Forward param mapping:
  bs, bc, φ_s=90° fixed, φ_c = axis (from landscape JSON 'theta_conf')
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import numpy as np

_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR))

from phase3_candidate_analysis_v2 import (
    hc_name, hc_match_score, SUB08_ORIGINAL_HC_EQUIV,
)
from fixedW_onlyTest_p2a_ranking import SUB09_ORIGINAL_HC_EQUIV

OUT = _THIS_DIR.parent / 'results' / 'p2a_landscape'
OUT.mkdir(parents=True, exist_ok=True)

TIKH_NORM = 32400.0
K_TOPK = 3
HUE_8 = [0, 45, 90, 135, 180, 225, 270, 315]


def forward(theta, bs, bc, phi_c, phi_s=90.0):
    return (theta + bs * np.cos(np.radians(theta - phi_s))
                  + bc * np.cos(np.radians(theta - phi_c))) % 360.0


def p2a_cell(bs, bc, phi_c, target_map):
    total = 0.0; exact = 0
    for theta in HUE_8:
        theta_cvd = forward(float(theta), bs, bc, phi_c)
        pred = hc_name(theta_cvd)
        target = target_map[theta]
        s = hc_match_score(pred, target)
        total += s
        if pred == target: exact += 1
    return total / 8.0, exact


def l_topk_jaccard(vuln_sim, vuln_obs, K=K_TOPK):
    sim_sort = np.argsort(vuln_sim)[:K]
    obs_sort = np.argsort(vuln_obs)[:K]
    return float(1.0 - len(set(sim_sort.tolist()) & set(obs_sort.tolist()))
                / max(1, len(set(sim_sort.tolist()) | set(obs_sort.tolist()))))


def analyze_landscape(path: Path, target_map):
    with open(path) as f:
        d = json.load(f)
    cells = d['cells']
    theta_conf = d.get('theta_conf', 150.0)
    vuln_cvd = np.array(d['vuln_cvd'])

    # Augment each cell with P2a + l_topk + base l_ccc + Tikh
    aug = []
    for c in cells:
        bs, bc = c['bs'], c['bc']
        vuln_sim = np.array(c['vuln_sim'])
        l_ccc = c['l_ccc']
        l_topk = c['l_topk']
        tikh = c['tikh']
        p2a, exact = p2a_cell(bs, bc, theta_conf, target_map)
        aug.append({
            'bs': bs, 'bc': bc, 'l_ccc': l_ccc, 'l_topk': l_topk, 'tikh': tikh,
            'ccc': c.get('ccc', 1 - 2*l_ccc),
            'p2a': p2a, 'exact': exact,
            'vuln_sim': vuln_sim,
        })

    # Sweep weight configs: each gives new argmin
    configs = [
        # (label, lam_ccc, lam_topk, lam_tikh, lam_p2a)
        ('current',      1.0, 0.5, 0.1, 0.0),
        ('tikh_0.5',     1.0, 0.5, 0.5, 0.0),
        ('tikh_1.0',     1.0, 0.5, 1.0, 0.0),
        ('tikh_2.0',     1.0, 0.5, 2.0, 0.0),
        ('topk_1.0',     1.0, 1.0, 0.1, 0.0),
        ('p2a_0.5',      1.0, 0.5, 0.1, 0.5),
        ('p2a_1.0',      1.0, 0.5, 0.1, 1.0),
        ('p2a_only',     0.0, 0.0, 0.0, 1.0),
        ('p2a + tikh',   1.0, 0.5, 0.5, 0.5),
    ]
    results = {}
    for label, lc, lt, lk, lp in configs:
        best_L = np.inf; best = None
        for a in aug:
            L = lc*a['l_ccc'] + lt*a['l_topk'] + lk*a['tikh'] + lp*(1.0 - a['p2a'])
            if L < best_L:
                best_L = L; best = {**a, 'L_new': L}
        results[label] = best

    # Direct P2a-max cell
    p2a_max = max(aug, key=lambda a: a['p2a'])

    return {
        'theta_conf': theta_conf,
        'configs': results,
        'p2a_max': p2a_max,
    }


def main():
    landscape_files = {
        ('08', 'Stockman150'):    'results/axis_3way/sub-08_V4_Stockman150_landscape.json',
        ('08', 'CIELab175.7'):    'results/axis_3way/sub-08_V4_CIELab175p7_landscape.json',
        ('08', 'bs_only'):        'results/axis_3way/sub-08_V4_bs_only_landscape.json',
        ('09', 'Stockman16'):     'results/axis_3way/sub-09_V4_Stockman16_landscape.json',
        ('09', 'CIELab11.8'):     'results/axis_3way/sub-09_V4_CIELab11p8_landscape.json',
        ('09', 'Stockman16ext'):  'results/axis_3way/sub-09_V4_Stockman16ext_landscape.json',
        ('09', 'CIELab11.8ext'):  'results/axis_3way/sub-09_V4_CIELab11p8ext_landscape.json',
        ('09', 'axis150_fine'):   'results/axis_3way/sub-09_V4_axis150_fine_landscape.json',
        ('09', 'bs_only'):        'results/axis_3way/sub-09_V4_bs_only_landscape.json',
    }
    target_maps = {'08': SUB08_ORIGINAL_HC_EQUIV, '09': SUB09_ORIGINAL_HC_EQUIV}

    all_results = {}
    for (sid, axis_label), p in landscape_files.items():
        path = Path(p)
        if not path.exists():
            print(f'SKIP {p}')
            continue
        print(f'\n=== sub-{sid} axis={axis_label} ({path.name}) ===')
        r = analyze_landscape(path, target_maps[sid])
        all_results[f'sub-{sid}/{axis_label}'] = r

        print(f'  P2a-max cell:  bs={r["p2a_max"]["bs"]:>4.0f}  bc={r["p2a_max"]["bc"]:+5.0f}  '
              f'P2a={r["p2a_max"]["p2a"]:.3f} ({r["p2a_max"]["exact"]}/8)  '
              f'CCC={r["p2a_max"]["ccc"]:+.3f}')
        print(f'  Weight sweep argmin:')
        print(f'    {"label":<12s} {"bs":>4s} {"bc":>5s}  {"P2a":>5s} {"exact":>5s} {"CCC":>6s} {"L_new":>6s}')
        for label, b in r['configs'].items():
            print(f'    {label:<12s} {b["bs"]:>4.0f} {b["bc"]:+5.0f}  '
                  f'{b["p2a"]:>5.3f} {b["exact"]:>3d}/8  {b["ccc"]:+5.3f} {b["L_new"]:>6.3f}')

    # Save
    serial = {}
    for k, r in all_results.items():
        serial[k] = {
            'theta_conf': r['theta_conf'],
            'p2a_max': {kk: (vv.tolist() if hasattr(vv, 'tolist') else vv)
                        for kk, vv in r['p2a_max'].items() if kk != 'vuln_sim'},
            'configs': {lab: {kk: (vv.tolist() if hasattr(vv, 'tolist') else vv)
                              for kk, vv in b.items() if kk != 'vuln_sim'}
                        for lab, b in r['configs'].items()},
        }
    with open(OUT / 'weight_sweep_summary.json', 'w') as f:
        json.dump(serial, f, indent=2)
    print(f'\nWrote {OUT / "weight_sweep_summary.json"}')


if __name__ == '__main__':
    main()
