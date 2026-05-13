"""p2a_gap_diagnosis.py — sub-08 FULL (22, +12) vs P2a-max (26, +34) per-color 비교.

심각성 평가:
  어떤 색이 FULL에서 mis-classified되어 P2a-max에서 회복되는가?
"""
from __future__ import annotations
import sys
import numpy as np
from pathlib import Path

_THIS = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS))
from phase3_candidate_analysis_v2 import (
    hc_name, hc_match_score, SUB08_ORIGINAL_HC_EQUIV,
)
from fixedW_onlyTest_p2a_ranking import SUB09_ORIGINAL_HC_EQUIV

HUE_8 = [0, 45, 90, 135, 180, 225, 270, 315]
COLOR_NAMES = ['c1_red', 'c2_orange', 'c3_yellow', 'c4_green',
               'c5_cyan', 'c6_sky', 'c7_blue', 'c8_magenta']


def forward(theta, bs, bc, phi_c, phi_s=90.0):
    return (theta + bs * np.cos(np.radians(theta - phi_s))
                  + bc * np.cos(np.radians(theta - phi_c))) % 360.0


def per_color(bs, bc, phi_c, target_map, label):
    print(f'\n{label}  (β_s={bs}, β_c={bc:+}, θ_conf={phi_c}°)')
    print(f'  {"color":<11s} {"θ":>4s}  {"θ_cvd":>6s} {"pred":<14s} {"target":<14s} {"score":>5s}')
    total = 0.0; exact = 0
    rows = []
    for cname, theta in zip(COLOR_NAMES, HUE_8):
        tc = forward(float(theta), bs, bc, phi_c)
        pred = hc_name(tc); tgt = target_map[theta]
        sc = hc_match_score(pred, tgt)
        total += sc
        if pred == tgt: exact += 1
        marker = '✓' if pred == tgt else ('~' if sc > 0 else '✗')
        print(f'  {cname:<11s} {theta:>4d}  {tc:>6.1f} {pred:<14s} {tgt:<14s} {sc:>5.2f} {marker}')
        rows.append({'color': cname, 'theta': theta, 'theta_cvd': tc,
                     'pred': pred, 'target': tgt, 'score': sc, 'match': pred == tgt})
    print(f'  Total: P2a = {total/8:.3f}, exact = {exact}/8')
    return rows, total/8, exact


def main():
    cases = [
        ('sub-08 deutan', 150.0, SUB08_ORIGINAL_HC_EQUIV, [
            ('FULL BEST',  22,  +12),
            ('P2a-max',    26,  +34),
            ('2-comp behav (보류)', 38, -14),
        ]),
        ('sub-09 protan', 16.0, SUB09_ORIGINAL_HC_EQUIV, [
            ('FULL BEST',  22, -10),
            ('P2a-max',    24, -20),
        ]),
    ]
    for sid, axis, tmap, configs in cases:
        print(f'\n{"="*88}\n{sid}\n{"="*88}')
        comparisons = []
        for label, bs, bc in configs:
            rows, p2a, ex = per_color(bs, bc, axis, tmap, label)
            comparisons.append((label, p2a, ex, rows))

        # Differential analysis
        if len(comparisons) >= 2:
            full_rows = comparisons[0][3]
            max_rows = comparisons[1][3]
            print(f'\n  Differential (FULL vs P2a-max):')
            for f, m in zip(full_rows, max_rows):
                if f['score'] != m['score'] or f['pred'] != m['pred']:
                    print(f"  {f['color']:<11s}  FULL: {f['pred']:<14s} ({f['score']:.2f})  "
                          f"→  P2a-max: {m['pred']:<14s} ({m['score']:.2f})  "
                          f"target={f['target']}")


if __name__ == '__main__':
    main()
