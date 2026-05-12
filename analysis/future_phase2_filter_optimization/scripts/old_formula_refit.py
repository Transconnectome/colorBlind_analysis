#!/usr/bin/env python3
"""
old_formula_refit.py — Re-fit 2-component model using OLD CIELab-direct formula.

OLD formula:  dt = β_s·cos(θ − 90°) + β_c·cos(θ − θ_conf)   [CIELab, no Stockman h_base]
CURRENT:      dt = β_s·cos(h_base − 90°) + β_c·cos(h_base − θ_conf)  [Stockman h_base via Machado]

Experiment:
  1. Grid search OLD formula for LOCO optimum β* (sub-08, V4, shift_at_both)
  2. Evaluate CURRENT-formula optimum (38, +7) under OLD formula LOCO
  3. Compute θ_cvd under OLD formula at β* and compare with sub-08 perceptions (P2a analog)
  4. Report: is (38, +7) close to β*?

Usage:
    cd analysis/future_phase2_filter_optimization
    conda activate srm
    python scripts/old_formula_refit.py
"""

import sys
import time
import json
import numpy as np
from pathlib import Path
from scipy.stats import spearmanr

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_SCRIPTS = Path(__file__).resolve().parent
_PHASE2  = _SCRIPTS.parent
sys.path.insert(0, str(_SCRIPTS))

for _base in [_PHASE2.parent, _PHASE2.parent.parent]:
    _fwd = _base / 'future_phase1_forward_model' / 'scripts'
    if _fwd.exists() and str(_fwd) not in sys.path:
        sys.path.insert(0, str(_fwd))
        break

from utils_forward_model import (
    HC_SUBJECTS, N_CHANNELS, HUE_ANGLES, load_amplitudes, create_basis_full,
)
from step1_fit_loco_v2 import (
    simulate_mean_hc_loco_legacy,
    precompute_hc_W,
    load_cvd_loco_target,
    permutation_test_spearman,
)
from stim_lab_render import render_at_hue

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SUBJECT    = '08'
ROI        = 'V4'
CVD_TYPE   = 'deutan'
THETA_CONF = 150.0          # deutan confusion axis (same value, applied in CIELab)
THETA_8    = np.array([0, 45, 90, 135, 180, 225, 270, 315], dtype=float)

LOCAL_DATA = (_PHASE2.parent / 'phase1_procrustes_decoding' / 'results'
              / 'visualization' / 'full_dataset_C010_with_residuals')
SERVER_DATA = Path('/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010')

# Sub-08 original perceptions (raw_behav.md §Original, Korean labels)
SUB08_PERCEPTS = {
    'c1': '빨강에 분홍',
    'c2': '연한 빨강',
    'c3': '연두',
    'c4': '노랑',
    'c5': '웜톤 아이보리',
    'c6': '하늘',
    'c7': '더 진한 하늘',
    'c8': '진파랑',
}

# Hue-angle based color name lookup (CIELab °)
def theta_to_name(theta: float) -> str:
    t = float(theta) % 360
    if t < 15 or t >= 345:   return 'red'
    if t < 30:                return 'red-orange'
    if t < 60:                return 'orange'
    if t < 75:                return 'orange-yellow'
    if t < 100:               return 'yellow'
    if t < 120:               return 'yellow-green'
    if t < 150:               return 'green'
    if t < 175:               return 'green-cyan'
    if t < 210:               return 'cyan/sky'
    if t < 240:               return 'sky-cyan'
    if t < 260:               return 'blue'
    if t < 285:               return 'blue-violet'
    if t < 310:               return 'violet/purple'
    if t < 330:               return 'purple-pink'
    return 'pink-red'


def p2a_score(theta_cvd: float, c_idx: int) -> str:
    """Rough P2a: does theta_cvd's color match sub-08's original perception?"""
    name = theta_to_name(theta_cvd)
    sub08 = SUB08_PERCEPTS[f'c{c_idx + 1}']
    # Manual mapping (same logic as filter_eval_sub08.md)
    matches = {
        0: ['red', 'red-orange', 'pink-red'],    # c1: 빨강에 분홍
        1: ['red', 'red-orange'],                 # c2: 연한 빨강
        2: ['yellow-green', 'green'],             # c3: 연두 (초록 = partial)
        3: ['yellow', 'orange-yellow'],           # c4: 노랑
        4: [],                                    # c5: 웜톤 아이보리 (no model matches)
        5: ['cyan/sky', 'sky-cyan'],              # c6: 하늘
        6: ['cyan/sky', 'sky-cyan'],              # c7: 더 진한 하늘
        7: ['blue', 'blue-violet'],               # c8: 진파랑
    }
    partial = {
        2: ['green-cyan'],                        # c3 green-cyan is partial
        3: ['yellow-green'],                      # c4 YG is partial
        6: ['blue'],                              # c7 plain blue is partial
    }
    if name in matches.get(c_idx, []):
        return '✓'
    if name in partial.get(c_idx, []):
        return 'partial'
    return '✗'


# ---------------------------------------------------------------------------
# OLD formula δθ
# ---------------------------------------------------------------------------
def dt_old(bs: float, bc: float, theta: np.ndarray = THETA_8) -> np.ndarray:
    """OLD CIELab-direct formula."""
    return (bs * np.cos(np.radians(theta - 90.0))
            + bc * np.cos(np.radians(theta - THETA_CONF)))


def get_shifted_design_old(bs: float, bc: float, n_channels: int = N_CHANNELS):
    """Design matrix for OLD formula at (bs, bc)."""
    dt = dt_old(bs, bc)
    hue_shifted = (THETA_8 + dt) % 360.0
    basis_full = create_basis_full(n_channels, basis_type='fe')
    idx = np.round(hue_shifted).astype(int) % 360
    return basis_full[idx], dt


# ---------------------------------------------------------------------------
# LOCO grid search under OLD formula
# ---------------------------------------------------------------------------
def grid_search_old(hc_amps_dict, vuln_cvd, bs_range, bc_range, verbose=True):
    t0 = time.time()
    n = len(bs_range) * len(bc_range)
    if verbose:
        print(f'Grid: β_s × β_c = {len(bs_range)} × {len(bc_range)} = {n} points')

    landscape = []
    best_loss = np.inf
    best_entry = None

    for i, bs in enumerate(bs_range):
        for bc in bc_range:
            C_shifted, delta_theta = get_shifted_design_old(bs, bc)
            vuln_sim, _ = simulate_mean_hc_loco_legacy(hc_amps_dict, C_shifted)
            rho, _ = spearmanr(vuln_sim, vuln_cvd)
            l_rank = 1.0 - (float(rho) if np.isfinite(rho) else 0.0)
            l_vuln = float(np.mean((vuln_sim - vuln_cvd) ** 2)) / 4.0
            l_fit  = 1.0 * l_vuln + 0.5 * l_rank

            entry = {'bs': float(bs), 'bc': float(bc),
                     'l_fit': l_fit, 'l_vuln': l_vuln, 'l_rank': l_rank,
                     'spearman_r': float(rho) if np.isfinite(rho) else 0.0,
                     'delta_theta': delta_theta.tolist(),
                     'vuln_sim': vuln_sim.tolist()}
            landscape.append(entry)

            if l_fit < best_loss:
                best_loss = l_fit
                best_entry = entry

        if verbose and (i + 1) % max(1, len(bs_range) // 5) == 0:
            print(f'  [{i+1}/{len(bs_range)} β_s rows] '
                  f'best ρ={best_entry["spearman_r"]:.3f} @ '
                  f'β_s={best_entry["bs"]}, β_c={best_entry["bc"]}')

    elapsed = time.time() - t0
    if verbose:
        print(f'Done in {elapsed:.1f}s')
    return best_entry, landscape


# ---------------------------------------------------------------------------
# P2a evaluation
# ---------------------------------------------------------------------------
def evaluate_p2a(bs: float, bc: float) -> dict:
    dt = dt_old(bs, bc)
    theta_cvd = (THETA_8 + dt) % 360.0
    rows = []
    for i, (theta_base, tc, dti) in enumerate(zip(THETA_8, theta_cvd, dt)):
        name = theta_to_name(tc)
        score = p2a_score(tc, i)
        rows.append({
            'c': f'c{i+1}',
            'theta_base': float(theta_base),
            'dt': float(dti),
            'theta_cvd': float(tc),
            'color_name': name,
            'sub08_percept': SUB08_PERCEPTS[f'c{i+1}'],
            'p2a': score,
        })
    n_pass = sum(1 for r in rows if r['p2a'] == '✓')
    n_part = sum(1 for r in rows if r['p2a'] == 'partial')
    return {'rows': rows, 'summary': f'{n_pass}+{n_part}p/{len(rows)}'}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    # --- Data ---
    data_dir = SERVER_DATA if SERVER_DATA.exists() else LOCAL_DATA
    print(f'Data: {data_dir}')

    hc_amps = {s: load_amplitudes(data_dir, s, ROI) for s in HC_SUBJECTS}
    vuln_cvd = load_cvd_loco_target(SUBJECT, ROI)
    print(f'CVD target: {np.round(vuln_cvd, 3).tolist()}')

    # --- Baseline ρ ---
    basis_full = create_basis_full(N_CHANNELS, basis_type='fe')
    C_orig = basis_full[HUE_ANGLES]
    vuln_base, _ = simulate_mean_hc_loco_legacy(hc_amps, C_orig)
    rho_base, _ = spearmanr(vuln_base, vuln_cvd)
    print(f'Baseline ρ(δ=0) = {rho_base:.3f}')

    # --- Grid search OLD formula ---
    bs_range = np.arange(0, 51, 2, dtype=float)
    bc_range = np.arange(-50, 51, 2, dtype=float)
    print('\n=== OLD formula grid search ===')
    best, landscape = grid_search_old(hc_amps, vuln_cvd, bs_range, bc_range)

    # --- Permutation test at OLD best ---
    best_vuln = np.array(best['vuln_sim'])
    perm_p, _, _ = permutation_test_spearman(best_vuln, vuln_cvd, n_perm=40320)
    print(f'\nOLD formula optimum: β_s={best["bs"]:.0f}, β_c={best["bc"]:.0f}')
    print(f'  ρ={best["spearman_r"]:.3f}, perm_p={perm_p:.4f}')
    print(f'  δθ: {np.round(best["delta_theta"], 1).tolist()}')

    # --- Evaluate CURRENT optimum (38, +7) under OLD formula ---
    print('\n=== CURRENT optimum (38, +7) under OLD formula ===')
    C38p7, dt38p7 = get_shifted_design_old(38.0, 7.0)
    vuln38p7, _ = simulate_mean_hc_loco_legacy(hc_amps, C38p7)
    rho38p7, _ = spearmanr(vuln38p7, vuln_cvd)
    perm_p38, _, _ = permutation_test_spearman(vuln38p7, vuln_cvd, n_perm=40320)
    print(f'  ρ={rho38p7:.3f}, perm_p={perm_p38:.4f}')
    print(f'  δθ: {np.round(dt38p7, 1).tolist()}')

    # --- Parameter distance ---
    dist = np.sqrt((best["bs"] - 38)**2 + (best["bc"] - 7)**2)
    print(f'\nβ distance: |β* − (38,+7)| = {dist:.1f}° '
          f'[β*=({best["bs"]:.0f},{best["bc"]:.0f})]')

    # --- P2a at OLD optimum and at (38, +7) ---
    print('\n=== P2a: OLD formula optimum β* ===')
    p2a_best = evaluate_p2a(best["bs"], best["bc"])
    print(f'Summary: {p2a_best["summary"]}')
    for r in p2a_best['rows']:
        print(f'  {r["c"]}: θ_base={r["theta_base"]:.0f}→θ_cvd={r["theta_cvd"]:.1f} '
              f'({r["color_name"]}) vs {r["sub08_percept"]}  {r["p2a"]}')

    print('\n=== P2a: OLD formula at (38, +7) ===')
    p2a_38p7 = evaluate_p2a(38.0, 7.0)
    print(f'Summary: {p2a_38p7["summary"]}')
    for r in p2a_38p7['rows']:
        print(f'  {r["c"]}: θ_base={r["theta_base"]:.0f}→θ_cvd={r["theta_cvd"]:.1f} '
              f'({r["color_name"]}) vs {r["sub08_percept"]}  {r["p2a"]}')

    # --- Save results ---
    out_dir = _PHASE2 / 'results' / 'old_formula_refit'
    out_dir.mkdir(parents=True, exist_ok=True)
    result = {
        'experiment': 'OLD CIELab-direct formula refit, sub-08 V4',
        'formula_old': 'dt = bs*cos(theta-90) + bc*cos(theta-150), CIELab angles',
        'formula_current': 'dt = bs*cos(h_base-90) + bc*cos(h_base-150), Stockman h_base',
        'baseline_rho': float(rho_base),
        'old_optimum': {
            'bs': float(best['bs']), 'bc': float(best['bc']),
            'spearman_r': float(best['spearman_r']),
            'perm_p': float(perm_p),
            'delta_theta': best['delta_theta'],
            'p2a': p2a_best['summary'],
        },
        'current_params_38p7_under_old': {
            'bs': 38, 'bc': 7,
            'spearman_r': float(rho38p7),
            'perm_p': float(perm_p38),
            'delta_theta': dt38p7.tolist(),
            'p2a': p2a_38p7['summary'],
        },
        'param_distance_to_38p7': float(dist),
    }
    with open(out_dir / 'sub-08_V4_old_vs_current.json', 'w') as f:
        json.dump(result, f, indent=2)
    print(f'\nSaved → {out_dir}/sub-08_V4_old_vs_current.json')

    # --- Summary verdict ---
    print('\n' + '='*60)
    print('VERDICT')
    print('='*60)
    if dist < 10:
        verdict = f'CLOSE (|Δβ|={dist:.1f}°) — P2a advantage is ROBUST at OLD optimum'
    elif dist < 25:
        verdict = f'MODERATE gap (|Δβ|={dist:.1f}°) — partial coincidence'
    else:
        verdict = f'DISTANT (|Δβ|={dist:.1f}°) — (38,+7) is coincidental for OLD formula'

    print(f'β* under OLD formula: ({best["bs"]:.0f}, {best["bc"]:.0f})')
    print(f'CURRENT optimum:      (38, +7)')
    print(f'Distance: {dist:.1f}°  →  {verdict}')
    print(f'\nOLD optimum LOCO: ρ={best["spearman_r"]:.3f}, p={perm_p:.4f}, P2a={p2a_best["summary"]}')
    print(f'(38,+7) under OLD:  ρ={rho38p7:.3f}, p={perm_p38:.4f}, P2a={p2a_38p7["summary"]}')


if __name__ == '__main__':
    main()
