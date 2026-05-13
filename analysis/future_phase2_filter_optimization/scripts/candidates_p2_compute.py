"""candidates_p2_compute.py — P2a/P2b for all 4 candidate filters.

Candidates:
  sub-08 deutan:
    (β) Stockman 150° axis: β_s=44, β_c=+28, φ_s=90°, φ_c=150°
    (α) 4D canonical: amp=70, phase=90° → β_s=70, β_c=0 (single-axis)
  sub-09 protan:
    (β) CIELab 11.8° axis: β_s=26, β_c=+60, φ_s=90°, φ_c=11.8°
    (α) 4D canonical: amp=74, phase=−25.4° → β_s=74·sin(−25.4°+90°),
                                              β_c=74·cos(−25.4°+90°) but canonical form

Forward map (general):
  δθ(θ) = β_s·cos(θ−φ_s) + β_c·cos(θ−φ_c)
  θ_perceived = (θ + δθ) mod 360

P2a (adjacent-tolerant naming match):
  For each c in {0..7}:
    θ_perceived = forward(θ_c)
    pred_name = hc_name(θ_perceived)
    target_name = SUBxx_ORIGINAL_HC_EQUIV[θ_c]    ← raw_behav.md
    score = hc_match_score(pred_name, target_name)
  P2a = mean(score) / 8

P2b: similar but with FILTER APPLIED (inverse pre-image):
  - Original perception: θ → forward(θ) = θ_perceived
  - With filter f(θ) = pre-image: present f(θ), perceived as forward(f(θ)) = θ_HC_target

But for our P2a target, we just check the CVD-perceived name match.

For now compute:
  - P2a: HC-target name match for filter-applied perception
  - "exact" count = exact name match (no adjacency partial credit)
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

HUE_8 = [0, 45, 90, 135, 180, 225, 270, 315]


def forward_4param(theta, bs, bc, phi_s, phi_c):
    dt = (bs * np.cos(np.radians(theta - phi_s))
          + bc * np.cos(np.radians(theta - phi_c)))
    return (theta + dt) % 360.0, float(dt)


def p2a(bs, bc, phi_s, phi_c, target_map):
    total = 0.0
    exact = 0
    rows = []
    for theta in HUE_8:
        theta_cvd, dt = forward_4param(float(theta), bs, bc, phi_s, phi_c)
        pred = hc_name(theta_cvd)
        target = target_map[theta]
        s = hc_match_score(pred, target)
        rows.append({'theta': theta, 'dt': round(dt, 1),
                     'theta_cvd': round(theta_cvd, 1),
                     'pred': pred, 'target': target,
                     'score': round(s, 2),
                     'exact': pred == target})
        total += s
        if pred == target:
            exact += 1
    return total / 8.0, exact, rows


def main():
    candidates = [
        # (label, subject, family, bs, bc, phi_s, phi_c, target_map)
        ('sub-08 β Stockman150',  '08', 'deutan', 44.0, +28.0, 90.0, 150.0, SUB08_ORIGINAL_HC_EQUIV),
        ('sub-08 β CIELab175.7',  '08', 'deutan', 50.0, -36.0, 90.0, 175.7, SUB08_ORIGINAL_HC_EQUIV),
        ('sub-08 α 4D canonical', '08', 'deutan', 70.0,  0.0,  90.0, 0.0,   SUB08_ORIGINAL_HC_EQUIV),
        ('sub-09 β Stockman16',   '09', 'protan', 14.0, +60.0, 90.0, 16.0,  SUB09_ORIGINAL_HC_EQUIV),
        ('sub-09 β CIELab11.8',   '09', 'protan', 26.0, +60.0, 90.0, 11.8,  SUB09_ORIGINAL_HC_EQUIV),
        ('sub-09 α 4D canonical', '09', 'protan', 74.0,  0.0,  -25.4, 0.0,  SUB09_ORIGINAL_HC_EQUIV),
        ('sub-09 OLD wrong',      '09', 'protan', 30.0, +46.0, 90.0, 150.0, SUB09_ORIGINAL_HC_EQUIV),
        # New: grid extended fine-grid axis-fixed results (single-axis along S)
        ('sub-09 Stockman16 ext', '09', 'protan', 80.0,  +2.0, 90.0, 16.0,  SUB09_ORIGINAL_HC_EQUIV),
        ('sub-09 CIELab11.8 ext', '09', 'protan', 80.0,  +2.0, 90.0, 11.8,  SUB09_ORIGINAL_HC_EQUIV),
        # β_s only (single-axis Emery, β_c=0 enforced)
        ('sub-08 β_s only',       '08', 'deutan', 68.0,   0.0, 90.0, 0.0,   SUB08_ORIGINAL_HC_EQUIV),
        ('sub-09 β_s only',       '09', 'protan', 88.0,   0.0, 90.0, 0.0,   SUB09_ORIGINAL_HC_EQUIV),
        # sub-09 axis=150° fine BEST (mechanism verification)
        ('sub-09 axis150 fine BEST', '09', 'protan', 22.0, +52.0, 90.0, 150.0, SUB09_ORIGINAL_HC_EQUIV),
        # **P2a-MAX cells from landscape exploration (game-changer)**
        ('sub-08 P2a-max Stockman150', '08', 'deutan', 26.0, +34.0, 90.0, 150.0, SUB08_ORIGINAL_HC_EQUIV),
        ('sub-09 P2a-max Stockman16',  '09', 'protan', 24.0, -20.0, 90.0,  16.0, SUB09_ORIGINAL_HC_EQUIV),
        ('sub-09 P2a-max CIELab11.8',  '09', 'protan', 22.0, -18.0, 90.0,  11.8, SUB09_ORIGINAL_HC_EQUIV),
    ]

    print(f'{"label":<28s}  P2a    exact/8   βs   βc   φs    φc')
    summary = []
    detail = {}
    for label, sid, fam, bs, bc, phi_s, phi_c, tmap in candidates:
        score, exact, rows = p2a(bs, bc, phi_s, phi_c, tmap)
        print(f'{label:<28s}  {score:.3f}  {exact}/8       {bs:.0f}   {bc:+.0f}   {phi_s:.1f}   {phi_c:.1f}')
        summary.append({
            'label': label, 'subject': f'sub-{sid}', 'family': fam,
            'bs': bs, 'bc': bc, 'phi_s': phi_s, 'phi_c': phi_c,
            'p2a': round(score, 3), 'exact': exact,
        })
        detail[label] = rows

    out = Path(__file__).resolve().parent.parent / 'results' / 'candidates_p2'
    out.mkdir(parents=True, exist_ok=True)
    with open(out / 'p2_summary.json', 'w') as f:
        json.dump({'summary': summary, 'detail': detail}, f, indent=2)
    print(f'\nWrote {out / "p2_summary.json"}')

    # Per-candidate detailed table
    print('\n=== Per-color detail (sub-08 candidates) ===')
    for label in ['sub-08 β Stockman150', 'sub-08 β CIELab175.7', 'sub-08 α 4D canonical']:
        print(f'\n{label}:')
        print(f'{"θ":>4s} {"δθ":>7s} {"θ_cvd":>7s} {"pred":<18s} {"target":<18s} {"score":>5s}')
        for r in detail[label]:
            mark = '✓' if r['exact'] else ('~' if r['score'] > 0 else '✗')
            print(f'{r["theta"]:>4d}° {r["dt"]:>+6.1f}° {r["theta_cvd"]:>6.1f}°  '
                  f'{r["pred"]:<18s} {r["target"]:<18s} {r["score"]:>4.2f} {mark}')

    print('\n=== Per-color detail (sub-09 candidates) ===')
    for label in ['sub-09 β Stockman16', 'sub-09 β CIELab11.8', 'sub-09 α 4D canonical']:
        print(f'\n{label}:')
        print(f'{"θ":>4s} {"δθ":>7s} {"θ_cvd":>7s} {"pred":<18s} {"target":<18s} {"score":>5s}')
        for r in detail[label]:
            mark = '✓' if r['exact'] else ('~' if r['score'] > 0 else '✗')
            print(f'{r["theta"]:>4d}° {r["dt"]:>+6.1f}° {r["theta_cvd"]:>6.1f}°  '
                  f'{r["pred"]:<18s} {r["target"]:<18s} {r["score"]:>4.2f} {mark}')


if __name__ == '__main__':
    main()
