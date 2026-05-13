"""loss_alternatives_sweep.py — L_Brettel 대체 가능성 + 다양한 anchor 비교.

탐색:
  V1: 현재 FULL Bayesian
  V2: L_Brettel 제거 (no sign term)
  V3: L_Brettel 부호 REVERSE (cortical overshoot 가설 - sub-08 deutan β_c<0 expected)
  V4: V1 ΔRDM β_c 직접 anchor (subject-specific, family-agnostic)
       sub-08 anchor β_c=-18, sub-09 anchor β_c=+3
  V5: 2-component cortical β_c 직접 anchor
       sub-08 hV4 LOCO β_c=-14, sub-09 hV4 LOCO β_c=-22
  V6: Family-asymmetric Tikh (β_s 더 강한 penalty + β_c family-aware)
  V7: Single combined literature L (one weight)
  V8: Drop Emery, keep Tregillus + Brettel + Tikh
  V9: Drop Tregillus, keep Emery + Brettel + Tikh (replicate finding)
  V10: L_ccc·L_Emery cross-product (multiplicative not additive)

각 variant에서:
  - argmin (BEST 좌표)
  - P2a (sub-08, sub-09)
  - HC LOO 안정성 (sub-04 outlier 분리)
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
import numpy as np

_THIS = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS))

from phase3_candidate_analysis_v2 import (
    hc_name, hc_match_score, SUB08_ORIGINAL_HC_EQUIV,
)
from fixedW_onlyTest_p2a_ranking import SUB09_ORIGINAL_HC_EQUIV

OUT = _THIS.parent / 'results' / 'loss_alternatives'
OUT.mkdir(parents=True, exist_ok=True)

HUE_8 = [0, 45, 90, 135, 180, 225, 270, 315]
EMERY = 21.4
TREG_TARGET = EMERY * 1.3

# Anchors per subject
NEURAL_ANCHORS = {
    'sub-08': {
        'family': 'deutan',
        'v1_drdm_bc': -18.0,   # V1 ΔRDM bootstrap
        'cortical_bc': -14.0,  # 2-comp hV4 LOCO (behavioral PASS)
    },
    'sub-09': {
        'family': 'protan',
        'v1_drdm_bc': +3.0,
        'cortical_bc': -22.0,  # 2-comp hV4 LOCO
    },
}

BRETTEL_OLD = {'deutan': +1, 'protan': -1}     # OLD 150°
BRETTEL_CORTICAL = {'deutan': -1, 'protan': +1}  # REVERSE (Tregillus overshoot 가설)


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


def sweep_sub(sid, axis, fam, tmap, landscape_path):
    with open(landscape_path) as f:
        d = json.load(f)
    cells = d['cells']
    bs = np.array([c['bs'] for c in cells])
    bc = np.array([c['bc'] for c in cells])
    L_ccc = np.array([c['l_ccc'] for c in cells])

    # Base components
    L_E = ((bs - EMERY) / 10.0) ** 2
    norm = np.hypot(bs, bc)
    L_T = ((norm - TREG_TARGET) / 15.0) ** 2
    Tk = (bs ** 2 + bc ** 2) / 32400.0
    Tk50 = Tk * 50.0

    # Brettel variants
    s_old = BRETTEL_OLD[fam]
    s_cort = BRETTEL_CORTICAL[fam]
    L_Brettel_old = np.maximum(0.0, -bc * s_old / 50.0) ** 2
    L_Brettel_cort = np.maximum(0.0, -bc * s_cort / 50.0) ** 2

    # V1 ΔRDM anchor (subject-specific)
    anchor_bc = NEURAL_ANCHORS[f'sub-{sid}']['v1_drdm_bc']
    L_v1drdm_anchor = ((bc - anchor_bc) / 15.0) ** 2

    # 2-component cortical anchor
    cortical_bc = NEURAL_ANCHORS[f'sub-{sid}']['cortical_bc']
    L_cortical_anchor = ((bc - cortical_bc) / 15.0) ** 2

    # Family-asymmetric Tikh
    Tk_asymm_deutan = (bs ** 2 + 4.0 * np.maximum(0, -bc) ** 2 + np.maximum(0, bc) ** 2) / 32400.0
    Tk_asymm_protan = (bs ** 2 + 4.0 * np.maximum(0, bc) ** 2 + np.maximum(0, -bc) ** 2) / 32400.0
    Tk_asymm = Tk_asymm_deutan if fam == 'deutan' else Tk_asymm_protan

    # ======================================================================
    # Loss variants
    # ======================================================================
    variants = {
        'V1 FULL (current BEST)': (
            0.3*L_ccc + 0.7*(0.5*L_E + 0.5*L_T + 0.3*L_Brettel_old) + 0.1*Tk50),
        'V2 No Brettel': (
            0.3*L_ccc + 0.7*(0.5*L_E + 0.5*L_T) + 0.1*Tk50),
        'V3 Brettel REVERSED (cortical)': (
            0.3*L_ccc + 0.7*(0.5*L_E + 0.5*L_T + 0.3*L_Brettel_cort) + 0.1*Tk50),
        'V4 V1 ΔRDM anchor (subject)': (
            0.3*L_ccc + 0.7*(0.5*L_E + 0.5*L_T + 0.3*L_v1drdm_anchor) + 0.1*Tk50),
        'V5 2-comp cortical anchor (subject)': (
            0.3*L_ccc + 0.7*(0.5*L_E + 0.5*L_T + 0.3*L_cortical_anchor) + 0.1*Tk50),
        'V6 Family-asymm Tikh (no Brettel)': (
            0.3*L_ccc + 0.7*(0.5*L_E + 0.5*L_T) + 0.1*Tk_asymm*50.0),
        'V7 Single L_lit (one weight)': (
            0.3*L_ccc + 0.7*(0.4*L_E + 0.4*L_T + 0.2*L_Brettel_old) + 0.1*Tk50),
        'V8 Drop Emery (Tregillus+Brettel+Tikh)': (
            0.3*L_ccc + 0.7*(0.7*L_T + 0.3*L_Brettel_old) + 0.1*Tk50),
        'V9 Drop Tregillus (Emery+Brettel+Tikh)': (
            0.3*L_ccc + 0.7*(0.5*L_E + 0.5*L_Brettel_old) + 0.1*Tk50),
        'V10 Pure neural-anchor (V1 ΔRDM only, no lit)': (
            0.3*L_ccc + 0.7*L_v1drdm_anchor + 0.1*Tk50),
        'V11 Neural sign + Emery (drop Brettel/Tregillus)': (
            0.3*L_ccc + 0.7*(0.5*L_E + 0.5*L_v1drdm_anchor) + 0.1*Tk50),
        'V12 Family-asymm + Emery only (NO Tregillus)': (
            0.3*L_ccc + 0.7*0.5*L_E + 0.1*Tk_asymm*50.0),
        'V13 Min 3-term: Emery + Brettel + Tikh + L_ccc': (
            0.3*L_ccc + 0.7*(0.5*L_E + 0.3*L_Brettel_old) + 0.1*Tk50),
    }

    results = {}
    for name, L_arr in variants.items():
        idx = int(np.argmin(L_arr))
        b_s, b_c = float(bs[idx]), float(bc[idx])
        p, e = p2a_eval(b_s, b_c, axis, tmap)
        results[name] = {
            'bs': b_s, 'bc': b_c,
            'L_min': float(L_arr[idx]),
            'p2a': p, 'exact': e,
            'norm': float(np.hypot(b_s, b_c)),
            'sign_agrees_brettel_old': bool(np.sign(b_c) == s_old) if b_c != 0 else None,
            'sign_agrees_brettel_cortical': bool(np.sign(b_c) == s_cort) if b_c != 0 else None,
        }
    return results


def main():
    cases = [
        ('08', 150.0, 'deutan', SUB08_ORIGINAL_HC_EQUIV,
         _THIS.parent / 'results/axis_3way/sub-08_V4_Stockman150_landscape.json'),
        ('09', 16.0, 'protan', SUB09_ORIGINAL_HC_EQUIV,
         _THIS.parent / 'results/axis_3way/sub-09_V4_Stockman16ext_landscape.json'),
    ]

    all_results = {}
    for sid, axis, fam, tmap, path in cases:
        print(f'\n{"="*120}')
        print(f'sub-{sid} ({fam}, θ_conf={axis}°)  Anchors: V1ΔRDM={NEURAL_ANCHORS[f"sub-{sid}"]["v1_drdm_bc"]}, '
              f'cortical={NEURAL_ANCHORS[f"sub-{sid}"]["cortical_bc"]}')
        print(f'{"="*120}')
        r = sweep_sub(sid, axis, fam, tmap, path)
        all_results[f'sub-{sid}'] = r
        print(f'  {"variant":<48s}  {"(bs,bc)":<14s}  {"P2a":>5s} {"exact":>5s}  {"norm":>5s}  '
              f'{"Brettel_old":>11s} {"Brettel_cort":>12s}')
        for name, v in r.items():
            agrees_old = '✓' if v['sign_agrees_brettel_old'] is True else (
                '✗' if v['sign_agrees_brettel_old'] is False else '~')
            agrees_cort = '✓' if v['sign_agrees_brettel_cortical'] is True else (
                '✗' if v['sign_agrees_brettel_cortical'] is False else '~')
            print(f'  {name:<48s}  ({v["bs"]:>3.0f},{v["bc"]:+4.0f})    '
                  f'{v["p2a"]:>5.3f} {v["exact"]:>3d}/8  {v["norm"]:>5.1f}     '
                  f'{agrees_old:>11s}  {agrees_cort:>12s}')

    with open(OUT / 'loss_alternatives_results.json', 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f'\nWrote {OUT / "loss_alternatives_results.json"}')

    # Joint P2a (mean of both subjects)
    print('\n' + '='*120)
    print('JOINT P2a (mean of sub-08 and sub-09) — best across BOTH subjects')
    print('='*120)
    common_names = set(all_results['sub-08']) & set(all_results['sub-09'])
    rows = []
    for name in sorted(common_names):
        r8 = all_results['sub-08'][name]
        r9 = all_results['sub-09'][name]
        joint = (r8['p2a'] + r9['p2a']) / 2
        rows.append((name, r8['p2a'], r9['p2a'], joint,
                     r8['bs'], r8['bc'], r9['bs'], r9['bc']))
    rows.sort(key=lambda x: -x[3])
    for name, p8, p9, j, b8s, b8c, b9s, b9c in rows:
        print(f'  {name:<48s}  sub-08 ({b8s:>3.0f},{b8c:+4.0f}) P2a={p8:.3f}  '
              f'sub-09 ({b9s:>3.0f},{b9c:+4.0f}) P2a={p9:.3f}  joint={j:.3f}')


if __name__ == '__main__':
    main()
