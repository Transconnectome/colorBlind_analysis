"""p2amax_new_loss_sweep.py — Forward-aware loss 제안 + sweep.

조건 분석:
  P2a-max는 forward map만 의존. simulator(vuln_sim)는 0-clustering 한계로 사용 어려움.

새 loss:
  L_theta_dist: 각 color c에서 forward(θ_c)가 target bin center와 얼마나 가까운가
                (P2a의 continuous surrogate, gradient-friendly)
  L_theta_bin_dist: bin 단위 거리 (categorical)
  L_p2a_direct: 1 − P2a (categorical)
  Hybrid: L_theta_dist + λ·Tikh + μ·L_simulator_soft

방해 요인 우회:
  - vuln_sim 무관 → 0-clustering 문제 회피
  - amplitude moderate 선호 → Tikh 강화
  - per-color target → simulator-perceptual dissociation 우회
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

OUT = _THIS_DIR.parent / 'results' / 'p2amax_new_loss'
OUT.mkdir(parents=True, exist_ok=True)

HUE_8 = [0, 45, 90, 135, 180, 225, 270, 315]
TIKH_NORM = 32400.0

# HC name bin centers (deg) — from HC_NAME_BINS in phase3_candidate_analysis_v2
TARGET_CENTERS = {
    'red':           0,       # bin (-10, 12)
    'red-orange':   21,       # (12, 30)
    'orange':       45,       # (30, 60)
    'yellow-orange':69,       # (60, 78)
    'yellow':       93,       # (78, 108)
    'yellow-green': 119,      # (108, 130)
    'green':        149,      # (130, 168)
    'cyan':         182,      # (168, 195)
    'sky':          215,      # (195, 235)
    'blue':         250,      # (235, 265)
    'violet':       280,      # (265, 295)
    'magenta':      312,      # (295, 330)
    'pink':         340,      # (330, 350)
}
# Bin half-widths (for tolerance)
TARGET_HALFWIDTH = {
    'red': 11,   'red-orange': 9,    'orange': 15,    'yellow-orange': 9,
    'yellow': 15,'yellow-green': 11, 'green': 19,     'cyan': 14,
    'sky': 20,   'blue': 15,         'violet': 15,    'magenta': 18,
    'pink': 10,
}
# Bin sequence (for bin-distance loss)
BIN_ORDER = ['red', 'red-orange', 'orange', 'yellow-orange', 'yellow',
             'yellow-green', 'green', 'cyan', 'sky', 'blue', 'violet',
             'magenta', 'pink']
BIN_IDX = {n: i for i, n in enumerate(BIN_ORDER)}


def forward(theta, bs, bc, phi_c, phi_s=90.0):
    return (theta + bs * np.cos(np.radians(theta - phi_s))
                  + bc * np.cos(np.radians(theta - phi_c))) % 360.0


def circular_dist(a, b):
    d = (a - b + 180) % 360 - 180
    return abs(d)


# ----------------------------------------------------------------------
# Loss definitions
# ----------------------------------------------------------------------
def L_theta_dist(bs, bc, phi_c, target_map):
    """Continuous: mean angular distance to target bin center."""
    total = 0.0
    for theta in HUE_8:
        theta_cvd = forward(float(theta), bs, bc, phi_c)
        target_center = TARGET_CENTERS[target_map[theta]]
        total += circular_dist(theta_cvd, target_center)
    return total / 8.0


def L_theta_bin_margin(bs, bc, phi_c, target_map):
    """Continuous: distance OUTSIDE target bin (0 if inside)."""
    total = 0.0
    for theta in HUE_8:
        theta_cvd = forward(float(theta), bs, bc, phi_c)
        tname = target_map[theta]
        tcenter = TARGET_CENTERS[tname]
        thw = TARGET_HALFWIDTH[tname]
        d = circular_dist(theta_cvd, tcenter)
        total += max(0.0, d - thw)
    return total / 8.0


def L_p2a_direct(bs, bc, phi_c, target_map):
    """Categorical: 1 - P2a (adjacency partial credit)."""
    total = 0.0
    for theta in HUE_8:
        theta_cvd = forward(float(theta), bs, bc, phi_c)
        pred = hc_name(theta_cvd)
        target = target_map[theta]
        total += hc_match_score(pred, target)
    return 1.0 - total / 8.0


def L_bin_dist(bs, bc, phi_c, target_map):
    """Discrete: bin-index distance (categorical 거리)."""
    total = 0
    for theta in HUE_8:
        theta_cvd = forward(float(theta), bs, bc, phi_c)
        pred = hc_name(theta_cvd)
        target = target_map[theta]
        # Circular bin distance (over 13 bins)
        d = abs(BIN_IDX[pred] - BIN_IDX[target])
        d = min(d, len(BIN_ORDER) - d)
        total += d
    return total / 8.0


def p2a(bs, bc, phi_c, target_map):
    total = 0.0; exact = 0
    for theta in HUE_8:
        theta_cvd = forward(float(theta), bs, bc, phi_c)
        pred = hc_name(theta_cvd)
        target = target_map[theta]
        total += hc_match_score(pred, target)
        if pred == target: exact += 1
    return total / 8.0, exact


# ----------------------------------------------------------------------
# Sweep
# ----------------------------------------------------------------------
def sweep_loss(axis, target_map, p2amax_bs, p2amax_bc,
               bs_range=None, bc_range=None):
    if bs_range is None:
        bs_range = np.arange(0, 51, 2, dtype=float)
    if bc_range is None:
        bc_range = np.arange(-60, 61, 2, dtype=float)

    loss_fns = {
        'L_theta_dist':       L_theta_dist,
        'L_theta_bin_margin': L_theta_bin_margin,
        'L_p2a_direct':       L_p2a_direct,
        'L_bin_dist':         L_bin_dist,
    }

    results = {}
    for name, fn in loss_fns.items():
        best_L = np.inf; best_cell = None
        for bs in bs_range:
            for bc in bc_range:
                L_val = fn(float(bs), float(bc), axis, target_map)
                if L_val < best_L:
                    best_L = L_val
                    p_val, ex_val = p2a(float(bs), float(bc), axis, target_map)
                    best_cell = {
                        'bs': float(bs), 'bc': float(bc),
                        'L': L_val, 'p2a': p_val, 'exact': ex_val,
                        'dist_to_p2amax': float(np.hypot(bs - p2amax_bs, bc - p2amax_bc)),
                    }
        results[name] = best_cell

    # Hybrid: L_theta_dist + Tikh
    for lam_tikh in [0.0, 0.1, 0.5]:
        best_L = np.inf; best_cell = None
        for bs in bs_range:
            for bc in bc_range:
                Ltd = L_theta_dist(float(bs), float(bc), axis, target_map)
                tikh = (bs*bs + bc*bc) / TIKH_NORM
                # Convert Tikh to comparable scale (multiply by ~50)
                L_val = Ltd + lam_tikh * 50.0 * tikh
                if L_val < best_L:
                    best_L = L_val
                    p_val, ex_val = p2a(float(bs), float(bc), axis, target_map)
                    best_cell = {
                        'bs': float(bs), 'bc': float(bc),
                        'L': L_val, 'p2a': p_val, 'exact': ex_val,
                        'dist_to_p2amax': float(np.hypot(bs - p2amax_bs, bc - p2amax_bc)),
                    }
        results[f'L_theta_dist + {lam_tikh}·Tikh'] = best_cell

    return results


def main():
    cases = [
        # (sid, axis_label, axis, p2amax_bs, p2amax_bc, target_map)
        ('08', 'Stockman150', 150.0, 26, +34, SUB08_ORIGINAL_HC_EQUIV),
        ('08', 'CIELab175.7', 175.7, 40, +30, SUB08_ORIGINAL_HC_EQUIV),
        ('09', 'Stockman16',   16.0, 24, -20, SUB09_ORIGINAL_HC_EQUIV),
        ('09', 'CIELab11.8',   11.8, 22, -18, SUB09_ORIGINAL_HC_EQUIV),
    ]

    all_results = {}
    for sid, axis_label, axis, pbs, pbc, tmap in cases:
        print(f'\n{"="*78}')
        print(f'sub-{sid} axis={axis_label} (θ_conf={axis}°)  '
              f'P2a-max target=({pbs}, {pbc:+d})')
        print(f'{"="*78}')
        results = sweep_loss(axis, tmap, pbs, pbc)
        all_results[f'sub-{sid}/{axis_label}'] = results
        print(f'  {"loss":<32s}  {"argmin":<10s}  {"L_min":>7s}  '
              f'{"P2a":>5s}  {"exact":>5s}  {"dist":>5s}')
        for loss_name, r in results.items():
            print(f'  {loss_name:<32s}  ({r["bs"]:>2.0f},{r["bc"]:+3.0f})    '
                  f'{r["L"]:>7.3f}  {r["p2a"]:>5.3f}  {r["exact"]:>3d}/8  '
                  f'{r["dist_to_p2amax"]:>5.1f}')

    # Save
    with open(OUT / 'new_loss_sweep_results.json', 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f'\nWrote {OUT / "new_loss_sweep_results.json"}')


if __name__ == '__main__':
    main()
