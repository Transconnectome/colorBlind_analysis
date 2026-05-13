"""loss_role_analysis.py — L_Tregillus의 역할 + 3-term reduction 검증.

Questions:
  Q1. L_Tregillus가 정확히 무엇을 anchor 하는가? (수학적/기하학적)
  Q2. Emery + Tregillus + Tikh 만으로 BEST 좌표 재현 가능한가?
  Q3. L_ccc, L_Brettel 각각의 기여도?

분석:
  A. 각 항만의 argmin (단독 평가)
  B. 모든 2-term 조합
  C. 3-term: Emery + Tregillus + Tikh (no L_ccc, no L_Brettel)
  D. FULL과 reduced의 BEST 좌표/P2a 비교
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

OUT = _THIS_DIR.parent / 'results' / 'loss_role_analysis'
OUT.mkdir(parents=True, exist_ok=True)

HUE_8 = [0, 45, 90, 135, 180, 225, 270, 315]
EMERY = 21.4
TREG_TARGET = EMERY * 1.3   # 27.82
BRETTEL_SIGN = {'deutan': +1, 'protan': -1}


def forward(theta, bs, bc, phi_c, phi_s=90.0):
    return (theta + bs * np.cos(np.radians(theta - phi_s))
                  + bc * np.cos(np.radians(theta - phi_c))) % 360.0


def p2a_eval(bs, bc, phi_c, target_map):
    total = 0.0; ex = 0
    for theta in HUE_8:
        tc = forward(float(theta), bs, bc, phi_c)
        pred = hc_name(tc); tgt = target_map[theta]
        total += hc_match_score(pred, tgt)
        if pred == tgt: ex += 1
    return total / 8.0, ex


def main():
    cases = [
        ('08', 150.0, 'deutan', SUB08_ORIGINAL_HC_EQUIV,
         _THIS_DIR.parent / 'results/axis_3way/sub-08_V4_Stockman150_landscape.json'),
        ('09', 16.0, 'protan', SUB09_ORIGINAL_HC_EQUIV,
         _THIS_DIR.parent / 'results/axis_3way/sub-09_V4_Stockman16ext_landscape.json'),
    ]

    all_results = {}
    for sid, axis, fam, tmap, path in cases:
        with open(path) as f:
            d = json.load(f)
        cells = d['cells']
        bs = np.array([c['bs'] for c in cells])
        bc = np.array([c['bc'] for c in cells])
        L_ccc = np.array([c['l_ccc'] for c in cells])

        L_E = ((bs - EMERY) / 10.0) ** 2
        norm = np.hypot(bs, bc)
        L_T = ((norm - TREG_TARGET) / 15.0) ** 2
        sgn = BRETTEL_SIGN[fam]
        L_B = np.maximum(0.0, -bc * sgn / 50.0) ** 2
        Tk = (bs * bs + bc * bc) / 32400.0

        print(f'\n{"="*100}')
        print(f'sub-{sid} ({fam}, θ_conf={axis}°)')
        print(f'{"="*100}')

        # ======================================================================
        # A. 단독 평가 (각 항만의 argmin)
        # ======================================================================
        print('\nA. 각 항만의 argmin:')
        cands = []
        for nm, arr in [('L_ccc', L_ccc), ('L_Emery', L_E), ('L_Tregillus', L_T),
                        ('L_Brettel', L_B), ('Tikh', Tk)]:
            idx = int(np.argmin(arr))
            p, e = p2a_eval(float(bs[idx]), float(bc[idx]), axis, tmap)
            print(f'  {nm:<12s} argmin: ({bs[idx]:>3.0f}, {bc[idx]:+3.0f})  '
                  f'val={arr[idx]:.4f}  P2a={p:.3f} ({e}/8)  norm={norm[idx]:.1f}')
            cands.append((nm, float(bs[idx]), float(bc[idx]), float(arr[idx]), p, e))

        # ======================================================================
        # C. 3-term: Emery + Tregillus + Tikh (NO L_ccc, NO L_Brettel)
        # ======================================================================
        print('\nC. 3-term combinations:')
        # All combinations of {Emery, Tregillus, Tikh, Brettel, Ccc} subsets
        weights = {
            'Emery+Tregillus':              (0.5*L_E + 0.5*L_T),
            'Emery+Tregillus+Tikh':         (0.5*L_E + 0.5*L_T + 0.1*50*Tk),
            'Emery+Tregillus+Brettel':      (0.5*L_E + 0.5*L_T + 0.3*L_B),
            'Emery+Tregillus+Brettel+Tikh': (0.5*L_E + 0.5*L_T + 0.3*L_B + 0.1*50*Tk),
            'Ccc only':                     L_ccc,
            'Ccc+Tikh':                     L_ccc + 0.1*50*Tk,
            'Ccc+Emery':                    L_ccc + 0.5*L_E,
            'Ccc+Tregillus':                L_ccc + 0.5*L_T,
            'Ccc+Brettel':                  L_ccc + 0.3*L_B,
            'Ccc+Emery+Tregillus':          0.3*L_ccc + 0.7*(0.5*L_E + 0.5*L_T),
            'Ccc+Emery+Tregillus+Tikh':     0.3*L_ccc + 0.7*(0.5*L_E + 0.5*L_T) + 0.1*50*Tk,
            'Ccc+Emery+Tregillus+Brettel':  0.3*L_ccc + 0.7*(0.5*L_E + 0.5*L_T + 0.3*L_B),
            'FULL (current BEST)':          (0.3*L_ccc + 0.7*(0.5*L_E + 0.5*L_T + 0.3*L_B) + 0.1*50*Tk),
        }
        rows = []
        for nm, L_arr in weights.items():
            idx = int(np.argmin(L_arr))
            b_s, b_c = float(bs[idx]), float(bc[idx])
            p, e = p2a_eval(b_s, b_c, axis, tmap)
            print(f'  {nm:<38s}  ({b_s:>3.0f}, {b_c:+3.0f})  P2a={p:.3f} ({e}/8)  norm={np.hypot(b_s,b_c):.1f}')
            rows.append({'loss': nm, 'bs': b_s, 'bc': b_c,
                         'p2a': p, 'exact': e, 'norm': float(np.hypot(b_s, b_c))})

        all_results[f'sub-{sid}'] = {
            'family': fam, 'axis': axis,
            'single_arg_min': [{'term': c[0], 'bs': c[1], 'bc': c[2],
                                 'val': c[3], 'p2a': c[4], 'exact': c[5]} for c in cands],
            'combos': rows,
        }

    with open(OUT / 'loss_role_results.json', 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f'\nWrote {OUT / "loss_role_results.json"}')

    # ======================================================================
    # 3-term reduction 평가
    # ======================================================================
    print('\n' + '='*100)
    print('3-term reduction 평가 (Emery+Tregillus+Tikh, no L_ccc no L_Brettel)')
    print('='*100)
    for sid in ['08', '09']:
        d = all_results[f'sub-{sid}']
        red = next(c for c in d['combos'] if c['loss'] == 'Emery+Tregillus+Tikh')
        full = next(c for c in d['combos'] if c['loss'].startswith('FULL'))
        dbs = red['bs'] - full['bs']; dbc = red['bc'] - full['bc']; dp = red['p2a'] - full['p2a']
        print(f'  sub-{sid}: FULL ({full["bs"]:>3.0f}, {full["bc"]:+3.0f}) P2a={full["p2a"]:.3f}  '
              f'→ 3-term ({red["bs"]:>3.0f}, {red["bc"]:+3.0f}) P2a={red["p2a"]:.3f}  '
              f'Δ=({dbs:+.0f}, {dbc:+.0f}) ΔP2a={dp:+.3f}')


if __name__ == '__main__':
    main()
