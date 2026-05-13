"""c8_target_sensitivity.py — Test SUB09 c8 target sensitivity + P2a-max method.

Q1. sub-09 c8 target 변경 (violet → magenta or pinkish_violet adjacency) 후 P2a 재계산
Q2. P2a-max 어떻게 구했나 = method 명세
Q3. sub-08 동일 method (P2a max search) 모든 axes
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import numpy as np

_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR))

from phase3_candidate_analysis_v2 import (
    hc_name, hc_match_score, HC_ADJ, SUB08_ORIGINAL_HC_EQUIV,
)
from fixedW_onlyTest_p2a_ranking import SUB09_ORIGINAL_HC_EQUIV

HUE_8 = [0, 45, 90, 135, 180, 225, 270, 315]


def forward(theta, bs, bc, phi_c, phi_s=90.0):
    return (theta + bs * np.cos(np.radians(theta - phi_s))
                  + bc * np.cos(np.radians(theta - phi_c))) % 360.0


def p2a(bs, bc, phi_c, target_map):
    total = 0.0; exact = 0
    rows = []
    for theta in HUE_8:
        theta_cvd = forward(float(theta), bs, bc, phi_c)
        pred = hc_name(theta_cvd)
        target = target_map[theta]
        s = hc_match_score(pred, target)
        rows.append({'theta': theta, 'theta_cvd': round(theta_cvd, 1),
                     'pred': pred, 'target': target, 'score': round(s, 2),
                     'exact': pred == target})
        total += s
        if pred == target: exact += 1
    return total / 8.0, exact, rows


def main():
    # ----------------------------------------------------------------
    # Q1: All candidate c8 predictions + sensitivity to SUB09[315]
    # ----------------------------------------------------------------
    print("=" * 75)
    print("Q1. Candidate c8 (θ=315°) predictions + SUB09 c8 target sensitivity")
    print("=" * 75)
    candidates_sub09 = [
        ('Stockman16 BEST (14, +60)',        14.0, +60.0,  16.0),
        ('CIELab11.8 BEST (26, +60)',        26.0, +60.0,  11.8),
        ('Stockman16 ext (80, +2)',          80.0,  +2.0,  16.0),
        ('CIELab11.8 ext (80, +2)',          80.0,  +2.0,  11.8),
        ('OLD wrong (30, +46)',              30.0, +46.0, 150.0),
        ('axis150 fine BEST (22, +52)',      22.0, +52.0, 150.0),
        ('β_s only (88, 0)',                 88.0,   0.0,  16.0),
        ('4D canonical (74 @ -25.4°)',       74.0,   0.0, -25.4),  # treat as bs=74 with phi_s=-25.4 + bc=0
        ('P2a-max Stockman16 (24, -20)',     24.0, -20.0,  16.0),
        ('P2a-max CIELab11.8 (22, -18)',     22.0, -18.0,  11.8),
    ]
    print(f'{"candidate":<35s}  {"θ_cvd@c8":>9s}  {"pred":<10s}')
    for label, bs, bc, phi_c in candidates_sub09:
        if 'canonical' in label:
            t_cvd = (315 + 74*np.cos(np.radians(315 - (-25.4))) + 0) % 360
        else:
            t_cvd = forward(315.0, bs, bc, phi_c)
        pred = hc_name(t_cvd)
        print(f'{label:<35s}  {t_cvd:>9.1f}°  {pred:<10s}')

    print('\n--- HC bins around 315° ---')
    print('  violet:    265–295°')
    print('  magenta:   295–330°  ← stimulus θ=315° physical bin')
    print('  pink:      330–350°')

    print('\n--- HC adjacency for relevant bins ---')
    for k in ['violet', 'magenta', 'pink']:
        print(f'  {k:>8s}: {HC_ADJ.get(k, {})}')

    # Now SUB09 target sensitivity
    target_variants = [
        ('current "violet"',       'violet'),
        ('"magenta" (pinkish→magenta side)', 'magenta'),
        ('"pink" (pinkish dominant)', 'pink'),
    ]
    print('\n--- SUB09 c8 target sensitivity (re-compute P2a with c8 target varied) ---')
    print(f'{"candidate":<35s}  {"violet":>8s}  {"magenta":>8s}  {"pink":>8s}')
    for label, bs, bc, phi_c in candidates_sub09:
        row = [label]
        for _, c8_target in target_variants:
            tmap = dict(SUB09_ORIGINAL_HC_EQUIV); tmap[315] = c8_target
            if 'canonical' in label:
                # special case: forward with phi_s=-25.4
                def fwd_canon(theta):
                    return (theta + 74*np.cos(np.radians(theta - (-25.4))) + 0) % 360
                total = 0.0
                for theta in HUE_8:
                    t_cvd = fwd_canon(theta)
                    pred = hc_name(t_cvd)
                    target = tmap[theta]
                    total += hc_match_score(pred, target)
                row.append(f'{total/8:.3f}')
            else:
                p, _, _ = p2a(bs, bc, phi_c, tmap)
                row.append(f'{p:.3f}')
        print(f'{row[0]:<35s}  {row[1]:>8s}  {row[2]:>8s}  {row[3]:>8s}')

    # ----------------------------------------------------------------
    # Q2: P2a-max method
    # ----------------------------------------------------------------
    print('\n' + '=' * 75)
    print('Q2. P2a-max 어떻게 구했나')
    print('=' * 75)
    print("""
Method: P2a 자체를 maximize (loss 없음, fit 무관, exhaustive search).

  for cell in landscape (β_s × β_c × axis fixed):
      forward map δθ = β_s·cos(θ-90°) + β_c·cos(θ-axis)
      θ_cvd = (θ + δθ) mod 360
      pred_name = hc_name(θ_cvd)
      score = hc_match_score(pred, target)
      P2a_cell = mean(score over 8 hues)

  P2a-max = argmax(P2a_cell over all cells)

CCC, l_topk, Tikh — 모두 무시. 단순히 perceptual prediction(명명) 일치도 maximize.
이건 weight sweep에서 'p2a_only' config = (λ_ccc=0, λ_topk=0, λ_tikh=0, λ_p2a=1.0)
이 도달한 argmin과 동일 (loss = 1−P2a 최소화 = P2a 최대화).
""")

    # ----------------------------------------------------------------
    # Q3: Sub-08 same method, all available axes
    # ----------------------------------------------------------------
    print('=' * 75)
    print('Q3. Sub-08 P2a-max — 모든 axes')
    print('=' * 75)

    # Direct grid search across (β_s, β_c) for each axis
    axes_sub08 = [
        ('Stockman 150° (current OLD)', 150.0),
        ('CIELab 175.7°',               175.7),
        ('Emery 90° (β_s only proxy)',   90.0),
        ('Stockman 16° (protan axis)',   16.0),  # sanity
        ('CIELab 11.8° (protan axis)',   11.8),  # sanity
    ]
    bs_range = np.arange(0, 51, 2)
    bc_range = np.arange(-60, 61, 2)

    print(f'{"axis":<35s}  {"BEST (bs, bc)":<14s}  {"P2a":>5s}  {"exact":>5s}')
    for label, axis in axes_sub08:
        best_p2a = -1.0; best_cell = None
        for bs in bs_range:
            for bc in bc_range:
                p, ex, _ = p2a(float(bs), float(bc), axis, SUB08_ORIGINAL_HC_EQUIV)
                if p > best_p2a:
                    best_p2a = p; best_cell = (bs, bc, ex)
        bs_b, bc_b, ex_b = best_cell
        print(f'{label:<35s}  ({bs_b:>2.0f}, {bc_b:+3.0f})    {best_p2a:>5.3f}  {ex_b:>3d}/8')


if __name__ == '__main__':
    main()
