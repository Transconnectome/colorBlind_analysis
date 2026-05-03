#!/usr/bin/env python3
"""
sub08_fine_grid_2component.py — Sub-08 fine grid for 2-component model.

Per behav_validation §3-3 / B1 plan: 1° resolution over (β_s ∈ [32,44],
β_c ∈ [-18,-10]) to test c2 orange recovery without sacrificing YG-C
separation.

Uses monkey-patch of FILTER_MODELS['2component'] before calling grid_search.
Verified at loco_distortion_fit.py:290 — bounds/grid_step read at call time.

Outputs:
  results/fits/phase_a_2component_finegrid/sub-08_V4_2component_finegrid.json
"""

import json
import sys
import time
from pathlib import Path
import numpy as np

_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR))

import loco_distortion_fit as ldf
from loco_distortion_fit import (
    FILTER_MODELS, HC_SUBJECTS, N_CHANNELS, HUE_ANGLES,
    create_basis_full, precompute_hc_W, load_amplitudes,
    load_cvd_loco_target, grid_search, run_permutation_tests,
)
from diagnostic_delta_rdm import compute_delta_rdm_obs
from preimage_filter_search import search_preimage
from machado_simulator import machado_shifted_hue

ORIGINAL_BOUNDS = FILTER_MODELS['2component']['bounds']
ORIGINAL_STEP = FILTER_MODELS['2component']['grid_step']
FILTER_MODELS['2component']['bounds'] = [(32.0, 44.0), (-18.0, -10.0)]
FILTER_MODELS['2component']['grid_step'] = [1.0, 1.0]
print(f'[patch] bounds: {ORIGINAL_BOUNDS} -> {FILTER_MODELS["2component"]["bounds"]}')
print(f'[patch] step:   {ORIGINAL_STEP} -> {FILTER_MODELS["2component"]["grid_step"]}')

SUBJ = '08'
ROI = 'V4'
CVD_TYPE = 'deutan'
METHOD = 'shift_at_both'

data_dir = ldf.LOCAL_DATA
if not data_dir.exists():
    raise FileNotFoundError(f'Local data not found at {data_dir}')
print(f'Data: {data_dir}')

print('\n=== Loading HC + CVD data ===')
hc_amps_dict = {hc: load_amplitudes(data_dir, hc, ROI) for hc in HC_SUBJECTS}
print(f'  Loaded {len(hc_amps_dict)} HC subjects '
      f'(V_s={hc_amps_dict["01"].shape[2]})')

vuln_cvd = load_cvd_loco_target(SUBJ, ROI)
print(f'  CVD vuln target: {np.round(vuln_cvd, 3).tolist()}')

basis_full = create_basis_full(N_CHANNELS, basis_type='fe')
C_original = basis_full[HUE_ANGLES]
hc_W_dict, _ = precompute_hc_W(hc_amps_dict, C_original)

cvd_amp = load_amplitudes(data_dir, SUBJ, ROI)
delta_rdm_obs, _, _, _ = compute_delta_rdm_obs(cvd_amp, hc_amps_dict)
print(f'  delta_rdm_obs computed (28 elements)')

print('\n=== Running fine grid search ===')
t0 = time.time()
result = grid_search(
    '2component', hc_amps_dict, vuln_cvd, CVD_TYPE,
    method=METHOD,
    hc_W_dict=hc_W_dict, delta_rdm_obs=delta_rdm_obs,
    weights=None,
)
print(f'  Grid done in {time.time()-t0:.1f}s ({result["n_evaluations"]} pts)')
print(f'  Best params: {result["best_params"]}, '
      f'rho={result["best_loss"]["spearman_r"]:.3f}')

print('\n=== Permutation test at fine-grid best ===')
best_vuln = np.array(result['best_loss']['vuln_sim'])
perm = run_permutation_tests(best_vuln, vuln_cvd)
result['permutation'] = perm
print(f"  label_perm_p = {perm['label_perm_p']:.4f}, "
      f"rho = {perm['spearman_r']:.3f}, "
      f"CCC = {perm['ccc']:.3f}")

print('\n=== Per-point pre-image (c2 c5 c6) ===')
# Pre-image targets are in OPPONENT space (canonical convention).
# hue_base maps CIELab[8] -> opponent[8] for the cvd_type baseline.
hue_base, _, _ = machado_shifted_hue(0.0, CVD_TYPE)
# c2 = CIELab 45 -> opponent hue_base[1]; c5 -> hue_base[4]; c6 -> hue_base[5]
target_indices = [(1, 'c2', 45.0), (4, 'c5', 180.0), (5, 'c6', 225.0)]
opponent_targets = {name: float(hue_base[idx])
                    for idx, name, _ in target_indices}
print(f'  Opponent targets: c2={opponent_targets["c2"]:.2f} '
      f'c5={opponent_targets["c5"]:.2f} c6={opponent_targets["c6"]:.2f}')
cielab_targets = {name: cl for _, name, cl in target_indices}

t0 = time.time()
for i, entry in enumerate(result['landscape']):
    params_arr = np.array(entry['params'])
    pre_map = {}
    for _, name, _ in target_indices:
        try:
            pi = search_preimage(opponent_targets[name], '2component',
                                 params_arr, CVD_TYPE)
            pre_map[name] = float(pi['theta_in'])
            pre_map[f'{name}_resid'] = float(pi['residual_deg'])
        except Exception as e:
            pre_map[name] = None
            pre_map[f'{name}_resid'] = None
            if i == 0:
                print(f'  preimage error for {name}: {e}')
    entry['preimage_c2'] = pre_map.get('c2')
    entry['preimage_c5'] = pre_map.get('c5')
    entry['preimage_c6'] = pre_map.get('c6')
    if pre_map.get('c2') is not None:
        entry['delta_c2'] = (
            (pre_map['c2'] - cielab_targets['c2'] + 180) % 360) - 180
    if pre_map.get('c5') is not None and pre_map.get('c6') is not None:
        entry['gap_c5_c6'] = (
            (pre_map['c6'] - pre_map['c5'] + 180) % 360
        ) - 180
    if (i + 1) % 20 == 0:
        print(f'  [{i+1}/{len(result["landscape"])}]')
print(f'  Pre-image done in {time.time()-t0:.1f}s')

baseline_path = (_SCRIPT_DIR.parent / 'results' / 'fits'
                 / 'phase_a_2component'
                 / f'sub-{SUBJ}_{ROI}_2component.json')
baseline_summary = None
if baseline_path.exists():
    with open(baseline_path) as f:
        prev = json.load(f)
    baseline_summary = {
        'coarse_best_params': prev.get('best_params'),
        'coarse_best_rho': prev.get('best_loss', {}).get('spearman_r'),
        'coarse_perm_p': prev.get('permutation', {}).get('label_perm_p'),
    }

result['fine_grid_baseline'] = baseline_summary
result['fine_grid_bounds'] = [(32.0, 44.0), (-18.0, -10.0)]
result['fine_grid_step'] = [1.0, 1.0]
result['subject'] = SUBJ
result['roi'] = ROI
result['cvd_type'] = CVD_TYPE
result['c2_target_theta'] = 45.0
result['note'] = (
    'Fine grid for sub-08 2-component model per behav_validation.md sec 3-3. '
    'Selection criterion: rho within 0.02 of coarse best AND |c2 delta| '
    'reduces (c2 pre-image moves out of red locus toward 30-40 deg) AND '
    'gap_c5_c6 magnitude maintained for YG-C separability.'
)

out_dir = (_SCRIPT_DIR.parent / 'results' / 'fits'
           / 'phase_a_2component_finegrid')
out_dir.mkdir(parents=True, exist_ok=True)
out_path = out_dir / f'sub-{SUBJ}_{ROI}_2component_finegrid.json'
with open(out_path, 'w') as f:
    json.dump(result, f, indent=2, default=str)
print(f'\nSaved: {out_path}')

print('\n=== TOP 5 by rho ===')
sorted_landscape = sorted(
    result['landscape'],
    key=lambda e: -e.get('spearman_r', float('-inf')))
for i, e in enumerate(sorted_landscape[:5]):
    print(f"  #{i+1}: params={e['params']} "
          f"rho={e.get('spearman_r', float('nan')):.3f} "
          f"L_fit={e.get('l_fit', float('nan')):.4f} "
          f"c2_pre={e.get('preimage_c2')} "
          f"delta_c2={e.get('delta_c2')} "
          f"gap_c5_c6={e.get('gap_c5_c6')}")

print('\n=== Coarse vs Fine ===')
if baseline_summary:
    print(f"  Coarse: params={baseline_summary['coarse_best_params']} "
          f"rho={baseline_summary['coarse_best_rho']} "
          f"perm_p={baseline_summary['coarse_perm_p']}")
print(f"  Fine:   params={result['best_params']} "
      f"rho={result['best_loss']['spearman_r']:.3f} "
      f"perm_p={result.get('permutation', {}).get('label_perm_p')}")
