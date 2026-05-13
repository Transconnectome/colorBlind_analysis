"""loss_simplification_sweep.py — Tregillus 제거 후 BEST 재탐색.

Simplified loss:
    L = alpha·L_ccc + (1-alpha)·[w_E·L_Emery + w_B·L_Brettel] + epsilon·Tikh

vs Full Bayesian:
    L = alpha·L_ccc + (1-alpha)·[0.5·L_Emery + 0.5·L_Tregillus + 0.3·L_Brettel] + 0.1·Tikh

Goal: sub-08/sub-09 BEST 좌표 안정성 확인 (Tregillus 항 제거 가능 여부)
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

OUT = _THIS_DIR.parent / 'results' / 'loss_simplification'
OUT.mkdir(parents=True, exist_ok=True)

HUE_8 = [0, 45, 90, 135, 180, 225, 270, 315]
EMERY_BETA_S = 21.4
TREGILLUS_TARGET = 21.4 * 1.3   # 27.82
BRETTEL_SIGN = {'deutan': +1, 'protan': -1}


def forward(theta, bs, bc, phi_c, phi_s=90.0):
    return (theta + bs * np.cos(np.radians(theta - phi_s))
                  + bc * np.cos(np.radians(theta - phi_c))) % 360.0


def p2a_eval(bs, bc, phi_c, target_map):
    total = 0.0; exact = 0
    for theta in HUE_8:
        theta_cvd = forward(float(theta), bs, bc, phi_c)
        pred = hc_name(theta_cvd)
        target = target_map[theta]
        total += hc_match_score(pred, target)
        if pred == target: exact += 1
    return total / 8.0, exact


def L_Emery(bs, bc):
    return ((bs - EMERY_BETA_S) / 10.0) ** 2


def L_Tregillus(bs, bc):
    norm = np.hypot(bs, bc)
    return ((norm - TREGILLUS_TARGET) / 15.0) ** 2


def L_Brettel(bs, bc, family):
    sign_exp = BRETTEL_SIGN[family]
    return max(0.0, -bc * sign_exp / 50.0) ** 2


def Tikh(bs, bc):
    return (bs * bs + bc * bc) / 32400.0


def sweep(landscape_path, family, axis, target_map, alpha=0.3, eps=0.1):
    with open(landscape_path) as f:
        d = json.load(f)
    cells = d['cells']
    L_ccc = np.array([c['l_ccc'] for c in cells])
    bs_a = np.array([c['bs'] for c in cells])
    bc_a = np.array([c['bc'] for c in cells])
    L_E = np.array([L_Emery(c['bs'], c['bc']) for c in cells])
    L_T = np.array([L_Tregillus(c['bs'], c['bc']) for c in cells])
    L_B = np.array([L_Brettel(c['bs'], c['bc'], family) for c in cells])
    Tk = np.array([Tikh(c['bs'], c['bc']) for c in cells])

    results = {}

    # 1. FULL Bayesian (current BEST formulation)
    L_full = (alpha * L_ccc + (1 - alpha) * (0.5 * L_E + 0.5 * L_T + 0.3 * L_B)
              + eps * Tk * 50.0)

    # 2. Simplified (Tregillus 제거)
    L_simple = (alpha * L_ccc + (1 - alpha) * (0.5 * L_E + 0.3 * L_B)
                + eps * Tk * 50.0)

    # 3. Variants — w_E sensitivity
    L_simple_high_E = (alpha * L_ccc + (1 - alpha) * (0.8 * L_E + 0.3 * L_B)
                       + eps * Tk * 50.0)
    L_simple_low_E = (alpha * L_ccc + (1 - alpha) * (0.3 * L_E + 0.3 * L_B)
                      + eps * Tk * 50.0)

    # 4. No Brettel (just Emery + CCC)
    L_emery_only = alpha * L_ccc + (1 - alpha) * 0.5 * L_E + eps * Tk * 50.0

    # 5. No Tikh
    L_no_tikh = alpha * L_ccc + (1 - alpha) * (0.5 * L_E + 0.3 * L_B)

    losses = {
        'FULL (Emery+Tregillus+Brettel+Tikh)': L_full,
        'SIMPLE (Emery+Brettel+Tikh)': L_simple,
        'SIMPLE high w_E=0.8': L_simple_high_E,
        'SIMPLE low w_E=0.3': L_simple_low_E,
        'Emery only + CCC + Tikh': L_emery_only,
        'SIMPLE no Tikh': L_no_tikh,
    }

    for name, L_arr in losses.items():
        idx = int(np.argmin(L_arr))
        bs = float(bs_a[idx]); bc = float(bc_a[idx])
        p2a, ex = p2a_eval(bs, bc, axis, target_map)
        results[name] = {
            'bs': bs, 'bc': bc, 'L_min': float(L_arr[idx]),
            'L_ccc': float(L_ccc[idx]), 'L_Emery': float(L_E[idx]),
            'L_Tregillus': float(L_T[idx]), 'L_Brettel': float(L_B[idx]),
            'Tikh': float(Tk[idx]),
            'p2a': p2a, 'exact': ex,
            'norm': float(np.hypot(bs, bc)),
        }
    return results


def main():
    cases = [
        ('08', 'V4_Stockman150', 150.0, 'deutan',
         _THIS_DIR.parent / 'results/axis_3way/sub-08_V4_Stockman150_landscape.json',
         SUB08_ORIGINAL_HC_EQUIV),
        ('09', 'V4_Stockman16', 16.0, 'protan',
         _THIS_DIR.parent / 'results/axis_3way/sub-09_V4_Stockman16ext_landscape.json',
         SUB09_ORIGINAL_HC_EQUIV),
        ('09', 'V4_CIELab11.8', 11.8, 'protan',
         _THIS_DIR.parent / 'results/axis_3way/sub-09_V4_CIELab11p8ext_landscape.json',
         SUB09_ORIGINAL_HC_EQUIV),
    ]

    all_results = {}
    for sid, tag, axis, fam, path, tmap in cases:
        if not path.exists():
            print(f'SKIP: {path}'); continue
        print(f'\n{"="*100}')
        print(f'sub-{sid} {tag} (θ_conf={axis}°, family={fam})')
        print(f'{"="*100}')
        r = sweep(path, fam, axis, tmap)
        all_results[f'sub-{sid}/{tag}'] = r
        print(f'  {"variant":<42s}  {"(bs,bc)":<12s}  {"L":>7s}  '
              f'{"P2a":>5s} {"ex":>4s}  {"norm":>5s}')
        for name, res in r.items():
            print(f'  {name:<42s}  ({res["bs"]:>2.0f},{res["bc"]:+3.0f})    '
                  f'{res["L_min"]:>7.3f}  {res["p2a"]:>5.3f} {res["exact"]:>3d}/8 '
                  f'{res["norm"]:>5.1f}')

    out_json = OUT / 'simplification_results.json'
    with open(out_json, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f'\nWrote {out_json}')

    # Stability check
    print('\n' + '='*100)
    print('STABILITY (FULL vs SIMPLE — Tregillus 제거 영향)')
    print('='*100)
    for key, r in all_results.items():
        full = r['FULL (Emery+Tregillus+Brettel+Tikh)']
        simp = r['SIMPLE (Emery+Brettel+Tikh)']
        dbs = simp['bs'] - full['bs']
        dbc = simp['bc'] - full['bc']
        dp2a = simp['p2a'] - full['p2a']
        print(f'  {key:<28s}  FULL ({full["bs"]:>2.0f},{full["bc"]:+3.0f}) P2a={full["p2a"]:.3f}  '
              f'→ SIMPLE ({simp["bs"]:>2.0f},{simp["bc"]:+3.0f}) P2a={simp["p2a"]:.3f}  '
              f'Δ=({dbs:+.0f},{dbc:+.0f}) ΔP2a={dp2a:+.3f}')


if __name__ == '__main__':
    main()
