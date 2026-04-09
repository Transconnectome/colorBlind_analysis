#!/usr/bin/env python3
"""
cross_type_validation.py — Test whether sub-08/09 CVD type labels should be swapped.

Runs cone_1way with BOTH type assignments for each CVD subject:
  - Original: 08=deutan, 09=protan, 10=normal
  - Swapped:  08=protan, 09=deutan, 10=deutan

LOCO targets embedded from existing results. Only needs amplitudes data.

Usage (server):
    mpirun -np 1 python cross_type_validation.py
"""

import json
import numpy as np
from pathlib import Path
from scipy.stats import spearmanr
from scipy.optimize import differential_evolution
from itertools import permutations
import sys

_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR))

_FWD_DIR = str(Path(__file__).resolve().parent.parent.parent.parent
               / 'future_phase1_forward_model' / 'scripts')
sys.path.insert(0, _FWD_DIR)

from utils_forward_model import (
    HC_SUBJECTS, N_CHANNELS, N_RUNS, N_COLORS,
    HUE_ANGLES, load_amplitudes, create_basis_matrix,
    gcv_select_alpha, fit_W_ridge, voxel_pattern_correlation,
)
from utils_distortion_models import get_design_matrix, MODELS

# Server data path
BASELINE_DIR = Path('/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010')

# Embedded LOCO targets (from existing W-fixed results)
LOCO_TARGETS = {
    'V1': {
        '08': [0.1269, -0.1779, -0.4375, -0.0236, 0.4578, 0.1945, -0.4988, -0.1339],
        '09': [0.1198, -0.0004, -0.2441, -0.0816, 0.1811, 0.1121, -0.0092, -0.2415],
        '10': [0.0699, 0.1806, 0.0273, -0.0976, 0.0987, 0.1978, 0.0039, -0.1211],
    },
    'V2': {
        '08': [0.5575, -0.5751, -0.6934, -0.3997, -0.2108, -0.2480, -0.4787, 0.1190],
        '09': [0.1441, 0.1007, -0.1177, 0.1577, 0.0159, -0.2015, -0.0733, -0.2209],
        '10': [-0.1762, -0.2021, -0.1777, -0.1865, -0.2456, -0.3608, -0.4253, -0.2829],
    },
    'V4': {
        '08': [0.5730, -0.6368, -0.7331, -0.3057, 0.2499, -0.2506, -0.7588, -0.3343],
        '09': [0.0226, 0.5956, 0.3221, 0.1473, -0.4505, -0.2555, -0.0902, -0.5746],
        '10': [-0.0057, 0.1603, 0.0691, 0.2925, 0.5084, 0.1826, -0.0279, -0.0846],
    },
}

ORIGINAL = {'08': 'deutan', '09': 'protan', '10': 'normal'}
SWAPPED  = {'08': 'protan', '09': 'deutan', '10': 'deutan'}


def precompute_hc_W(hc_amps_dict, C_original):
    hc_W_dict, hc_alpha_dict = {}, {}
    C_pooled = np.tile(C_original, (N_RUNS, 1))
    for subj, amp in hc_amps_dict.items():
        V_s = amp.shape[2]
        X_all = amp.reshape(-1, V_s)
        alpha, _ = gcv_select_alpha(C_pooled, X_all)
        W = fit_W_ridge(C_pooled, X_all, alpha)
        hc_W_dict[subj] = W
        hc_alpha_dict[subj] = float(alpha)
    return hc_W_dict, hc_alpha_dict


def simulate_mean_hc_wfixed(hc_W_dict, hc_amps_dict, C_shifted):
    per_hc_vuln = {}
    for subj in hc_W_dict:
        vuln = np.zeros(N_COLORS)
        for color in range(N_COLORS):
            Y_pred = C_shifted[color:color+1] @ hc_W_dict[subj]
            Y_actual = hc_amps_dict[subj][:, color].mean(axis=0, keepdims=True)
            r = voxel_pattern_correlation(Y_pred, Y_actual)
            vuln[color] = r[0]
        per_hc_vuln[subj] = vuln
    vuln_matrix = np.array(list(per_hc_vuln.values()))
    return vuln_matrix.mean(axis=0), per_hc_vuln


def permutation_test_spearman(hc_vuln_fitted, cvd_vuln):
    rho_obs, _ = spearmanr(hc_vuln_fitted, cvd_vuln)
    if not np.isfinite(rho_obs):
        rho_obs = 0.0
    null = []
    for perm in permutations(range(8)):
        r, _ = spearmanr(hc_vuln_fitted, cvd_vuln[list(perm)])
        null.append(r if np.isfinite(r) else 0.0)
    null = np.array(null)
    p = (np.sum(null >= rho_obs) + 1) / (len(null) + 1)
    return float(p), float(rho_obs)


def sweep_cone_1way(hc_W_dict, hc_amps_dict, cvd_vuln, cvd_type):
    delta_range = np.arange(0, 61, 1)
    best_r, best_delta = -999, 0
    all_rhos = []

    for delta in delta_range:
        C = get_design_matrix('cone_1way', [delta], cvd_type=cvd_type)
        mean_vuln, _ = simulate_mean_hc_wfixed(hc_W_dict, hc_amps_dict, C)
        r, _ = spearmanr(mean_vuln, cvd_vuln)
        r = float(r) if np.isfinite(r) else 0.0
        all_rhos.append(r)
        if r > best_r:
            best_r = r
            best_delta = float(delta)

    C_best = get_design_matrix('cone_1way', [best_delta], cvd_type=cvd_type)
    mean_vuln_best, _ = simulate_mean_hc_wfixed(hc_W_dict, hc_amps_dict, C_best)
    perm_p, rho_obs = permutation_test_spearman(mean_vuln_best, cvd_vuln)

    return {
        'best_delta_nm': best_delta,
        'best_spearman_r': best_r,
        'perm_p': perm_p,
        'mean_vuln_best': mean_vuln_best.tolist(),
    }


def sweep_cone_3way_free(hc_W_dict, hc_amps_dict, cvd_vuln):
    """cone_3way: free L/M/S — type-agnostic."""
    def objective(params):
        C = get_design_matrix('cone_3way', params, cvd_type='deutan')
        mean_vuln, _ = simulate_mean_hc_wfixed(hc_W_dict, hc_amps_dict, C)
        r, _ = spearmanr(mean_vuln, cvd_vuln)
        return -(r if np.isfinite(r) else 0.0)

    res = differential_evolution(objective, [(-60,60)]*3, seed=42,
                                  maxiter=80, tol=1e-6, popsize=10)
    C_opt = get_design_matrix('cone_3way', res.x, cvd_type='deutan')
    mean_vuln, _ = simulate_mean_hc_wfixed(hc_W_dict, hc_amps_dict, C_opt)
    r, _ = spearmanr(mean_vuln, cvd_vuln)
    perm_p, _ = permutation_test_spearman(mean_vuln, cvd_vuln)

    return {
        'L_shift': float(res.x[0]),
        'M_shift': float(res.x[1]),
        'S_shift': float(res.x[2]),
        'dominant_cone': ['L', 'M', 'S'][np.argmax(np.abs(res.x))],
        'spearman_r': float(r) if np.isfinite(r) else 0.0,
        'perm_p': perm_p,
    }


def main():
    rois = ['V1', 'V2', 'V4']
    cvd_subjects = ['08', '09', '10']
    results = {}

    for roi in rois:
        print(f'\n{"="*60}')
        print(f'ROI: {roi}')
        print(f'{"="*60}')

        hc_amps = {}
        for subj in HC_SUBJECTS:
            hc_amps[subj] = load_amplitudes(str(BASELINE_DIR), subj, roi)
        print(f'  Loaded {len(hc_amps)} HC subjects')

        C_original = create_basis_matrix(HUE_ANGLES, N_CHANNELS)
        hc_W, hc_alphas = precompute_hc_W(hc_amps, C_original)
        print(f'  Precomputed W')

        for cvd_subj in cvd_subjects:
            cvd_vuln = np.array(LOCO_TARGETS[roi][cvd_subj])
            key = f'{roi}_sub-{cvd_subj}'
            results[key] = {}

            print(f'\n  sub-{cvd_subj}:')
            print(f'    LOCO target: {np.round(cvd_vuln, 3)}')

            for label, type_map in [('ORIGINAL', ORIGINAL), ('SWAPPED', SWAPPED)]:
                cvd_type = type_map[cvd_subj]
                print(f'\n    [{label}] type={cvd_type}')
                r1 = sweep_cone_1way(hc_W, hc_amps, cvd_vuln, cvd_type)
                sig = '*' if r1['perm_p'] < 0.05 else ''
                print(f'      cone_1way: Δλ={r1["best_delta_nm"]:.0f}nm, '
                      f'r={r1["best_spearman_r"]:.3f}, '
                      f'p={r1["perm_p"]:.4f} {sig}')
                results[key][f'cone_1way_{label.lower()}'] = r1
                results[key][f'type_{label.lower()}'] = cvd_type

            print(f'\n    [FREE] cone_3way:')
            r3 = sweep_cone_3way_free(hc_W, hc_amps, cvd_vuln)
            print(f'      L={r3["L_shift"]:.1f}, M={r3["M_shift"]:.1f}, '
                  f'S={r3["S_shift"]:.1f}nm → dominant={r3["dominant_cone"]}')
            print(f'      r={r3["spearman_r"]:.3f}, p={r3["perm_p"]:.4f}')
            results[key]['cone_3way_free'] = r3

    # Summary
    print(f'\n\n{"="*80}')
    print('CROSS-TYPE VALIDATION SUMMARY')
    print(f'{"="*80}')
    print(f'{"Key":<20} {"Hyp":<10} {"Type":<8} {"Δλ":<6} {"r":<8} {"p":<10} {"sig":<4}')
    print(f'{"-"*70}')

    for roi in rois:
        for cvd_subj in cvd_subjects:
            key = f'{roi}_sub-{cvd_subj}'
            r = results[key]
            for label in ['original', 'swapped']:
                c1 = r[f'cone_1way_{label}']
                sig = '***' if c1['perm_p'] < 0.001 else '**' if c1['perm_p'] < 0.01 else '*' if c1['perm_p'] < 0.05 else ''
                print(f'{key:<20} {label:<10} {r[f"type_{label}"]:<8} '
                      f'{c1["best_delta_nm"]:<6.0f} '
                      f'{c1["best_spearman_r"]:<8.3f} '
                      f'{c1["perm_p"]:<10.4f} {sig:<4}')
            c3 = r['cone_3way_free']
            print(f'{key:<20} {"free":<10} {"3way":<8} '
                  f'{"L"+str(int(c3["L_shift"])):<6} '
                  f'{c3["spearman_r"]:<8.3f} '
                  f'{c3["perm_p"]:<10.4f} {c3["dominant_cone"]:<4}')
        print()

    # Decision
    print(f'\n{"="*80}')
    print('DECISION: Which type assignment fits better?')
    print(f'{"="*80}')
    for cvd_subj in ['08', '09']:
        print(f'\nsub-{cvd_subj} (original={ORIGINAL[cvd_subj]}, '
              f'swapped={SWAPPED[cvd_subj]}):')
        for roi in rois:
            key = f'{roi}_sub-{cvd_subj}'
            r_o = results[key]['cone_1way_original']['best_spearman_r']
            p_o = results[key]['cone_1way_original']['perm_p']
            r_s = results[key]['cone_1way_swapped']['best_spearman_r']
            p_s = results[key]['cone_1way_swapped']['perm_p']
            winner = 'ORIG' if r_o >= r_s else 'SWAP'
            dom = results[key]['cone_3way_free']['dominant_cone']
            L = results[key]['cone_3way_free']['L_shift']
            M = results[key]['cone_3way_free']['M_shift']
            print(f'  {roi}: orig r={r_o:.3f}(p={p_o:.3f}) vs '
                  f'swap r={r_s:.3f}(p={p_s:.3f}) → {winner} | '
                  f'3way: {dom}-cone (L={L:.0f},M={M:.0f})')

    out_path = _SCRIPT_DIR.parent / 'results' / 'cross_type_validation.json'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f'\nSaved: {out_path}')


if __name__ == '__main__':
    main()
