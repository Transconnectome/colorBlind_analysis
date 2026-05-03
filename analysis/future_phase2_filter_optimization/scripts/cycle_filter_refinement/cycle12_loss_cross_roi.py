#!/usr/bin/env python3
"""cycle12_loss_cross_roi.py — Pre-registered cross-ROI LOSS for filter fitting.

Cycle 11c 옵션 A 진행. (β_s, β_c)를 fitting할 때 두 ROI의 다른 metric을 결합:

  L_cross(β_s, β_c) = α · l_topk_jaccard(V4, β_s, β_c)   ← LOCO-derived
                    + β · l_rank(V1, β_s, β_c)            ← RDM-like (1−Spearman)
                    + λ · Tikh(β_s, β_c)

Pre-registered (post-hoc 아님):
  - V4 = LOCO gate ROI (forward 2-comp p=0.004 sub-08, p=0.035 sub-09)
  - V1 = SRM 개인 강한 ROI (sub-09 p=0.007, sub-08 V2 p=0.040)
  - 모든 CVD subject에 동일 적용 (per-subject custom 아님)

비교:
  1. Same-ROI baseline: (β_s, β_c) at l_topk_jaccard(V4) min only
  2. Cross-ROI loss: (β_s, β_c) at L_cross min
  3. Specificity (cycle 7 selection rule) 두 parameter set으로 평가
  4. Pre-image filter 변화

α=β=1 default (둘 다 [0,1] 범위). λ=0.2 Tikh.
Sensitivity sweep: α/β ∈ {0.5, 1.0, 2.0} 추가 검토.
"""
import json
import csv
import numpy as np
from pathlib import Path
from itertools import product

ROOT = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/'
            'colorBlind_analysis/analysis/future_phase2_filter_optimization')
RES = ROOT / 'results/cycle_filter_refinement'
OUT = RES / 'cycle12_loss_cross_roi.json'
OUT_CSV = RES / 'cycle12_loss_cross_roi.csv'

HC = ['01', '02', '03', '04', '05', '06']
CVD = ['08', '09']
ALL = HC + CVD
ROIS = ['V1', 'V2', 'V4']
COLOR_IDX = {'yellow': 2, 'magenta': 7}
FAMILIES = {'deutan': ('yellow', -1.0), 'protan': ('magenta', +1.0)}

_bs = np.arange(0.0, 81.0, 2.0)
_bc = np.arange(-60.0, 61.0, 2.0)
_BS, _BC = np.meshgrid(_bs, _bc, indexing='ij')
NORM_GRID = (_BS / 80.0) ** 2 + (_BC / 60.0) ** 2

LAM = 0.2  # Tikhonov, 동일


def load_landscape(subj, roi, metric):
    """Return (41, 61) grid for given metric."""
    p = RES / f'sub-{subj}_{roi}_landscape.json'
    if not p.exists():
        return None
    with open(p) as f:
        d = json.load(f)
    if metric not in d:
        return None
    return np.array(d[metric])


def find_min(loss_grid):
    """Return (best_bs, best_bc, min_value)."""
    idx = np.unravel_index(np.argmin(loss_grid), loss_grid.shape)
    return float(_bs[idx[0]]), float(_bc[idx[1]]), float(loss_grid[idx])


def eval_cross_roi_loss(subj, alpha=1.0, beta=1.0, R_topk='V4', R_rank='V1'):
    """Compute L_cross(β_s, β_c) and return min."""
    g_topk = load_landscape(subj, R_topk, 'l_topk_jaccard')
    g_rank = load_landscape(subj, R_rank, 'l_rank')
    if g_topk is None or g_rank is None:
        return None
    L = alpha * g_topk + beta * g_rank + LAM * NORM_GRID
    bs, bc, val = find_min(L)
    # Also report individual contributions at the min
    idx = np.unravel_index(np.argmin(L), L.shape)
    contrib_topk = float(g_topk[idx])
    contrib_rank = float(g_rank[idx])
    contrib_tikh = float(LAM * NORM_GRID[idx])
    return {
        'bs': bs, 'bc': bc,
        'L_total': val,
        'l_topk_at_min': contrib_topk,
        'l_rank_at_min': contrib_rank,
        'tikh_at_min': contrib_tikh,
    }


def baseline_same_roi(subj, roi='V4'):
    """Cycle 8 preimage same-ROI baseline: l_topk + Tikh at given ROI."""
    g = load_landscape(subj, roi, 'l_topk_jaccard')
    if g is None:
        return None
    L = g + LAM * NORM_GRID
    bs, bc, val = find_min(L)
    return {'bs': bs, 'bc': bc, 'L_total': val, 'l_topk_at_min': float(g[np.unravel_index(np.argmin(L), L.shape)])}


def main():
    results = {
        'meta': {
            'cycle': 12,
            'task': 'pre-registered cross-ROI LOSS for filter fitting',
            'rule_pre_registered': 'L = alpha*l_topk_jaccard(V4) + beta*l_rank(V1) + 0.2*Tikh',
            'justification': {
                'V4_l_topk': 'LOCO gate ROI (forward 2-comp p=0.004 sub-08, p=0.035 sub-09)',
                'V1_l_rank': 'SRM individual sig (sub-09 V1 p=0.007); RDM-like via Spearman of vuln vector',
            },
            'note': 'pre-registered (a priori), not post-hoc selection',
        },
        'per_subject': {},
        'csv_rows': [],
    }

    print('=== Cycle 12: Pre-registered cross-ROI LOSS ===')
    print('L_cross = alpha*l_topk(V4) + beta*l_rank(V1) + 0.2*Tikh')
    print()

    print(f'{"subj":<6} {"role":<5} {"alpha":>5} {"beta":>5} {"baseline V4 (β_s,β_c)":>22} {"cross (β_s,β_c)":>17} {"shift":>8}')
    print('-' * 80)

    weight_combos = [(1.0, 1.0), (0.5, 1.0), (1.0, 0.5), (2.0, 1.0), (1.0, 2.0)]

    for subj in ALL:
        role = 'CVD' if subj in CVD else 'HC'
        results['per_subject'][subj] = {'role': role, 'baseline': {}, 'cross_roi_weights': {}}

        # Baseline: V4 same-ROI
        base_v4 = baseline_same_roi(subj, 'V4')
        base_v1 = baseline_same_roi(subj, 'V1')
        results['per_subject'][subj]['baseline']['V4_only'] = base_v4
        results['per_subject'][subj]['baseline']['V1_only'] = base_v1

        for alpha, beta in weight_combos:
            cross = eval_cross_roi_loss(subj, alpha=alpha, beta=beta)
            if cross is None:
                continue
            key = f'a{alpha}_b{beta}'
            results['per_subject'][subj]['cross_roi_weights'][key] = cross

            shift_bs = cross['bs'] - base_v4['bs']
            shift_bc = cross['bc'] - base_v4['bc']
            shift_str = f'({shift_bs:+.0f},{shift_bc:+.0f})'

            print(f'sub-{subj:<2} {role:<5} {alpha:>5} {beta:>5} '
                  f'({base_v4["bs"]:>4.0f},{base_v4["bc"]:>4.0f}) → '
                  f'({cross["bs"]:>4.0f},{cross["bc"]:>4.0f}) '
                  f'{shift_str:>8}')

            results['csv_rows'].append({
                'subject': f'sub-{subj}',
                'role': role,
                'alpha': alpha,
                'beta': beta,
                'baseline_V4_bs': base_v4['bs'],
                'baseline_V4_bc': base_v4['bc'],
                'cross_bs': cross['bs'],
                'cross_bc': cross['bc'],
                'shift_bs': shift_bs,
                'shift_bc': shift_bc,
                'L_total': round(cross['L_total'], 4),
                'l_topk_at_min': round(cross['l_topk_at_min'], 4),
                'l_rank_at_min': round(cross['l_rank_at_min'], 4),
            })
        print()

    # CSV save
    if results['csv_rows']:
        with open(OUT_CSV, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(results['csv_rows'][0].keys()))
            w.writeheader()
            w.writerows(results['csv_rows'])

    with open(OUT, 'w') as f:
        json.dump(results, f, indent=2)
    print(f'\nSaved JSON: {OUT}')
    print(f'Saved CSV:  {OUT_CSV}')


if __name__ == '__main__':
    main()
