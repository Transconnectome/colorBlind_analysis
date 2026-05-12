#!/usr/bin/env python3
"""
cycle14_v1_rdm_cross.py — V1 RDM cross-criterion (matched to Cycle 15 V4 anchor).

CONSISTENCY UPDATE 2026-05-04: V4 anchor changed from l_topk_jaccard to
mw_jaccard_loss to match Cycle 15 opt2 V4 anchor. Now Cycle 14 vs Cycle 15
opt2 differ ONLY in V1 channel (RDM cosine vs LOCO Spearman), enabling a
clean V1-channel ablation.

Cycle 14 (NEW):  L = a*mw_jaccard(V4) + b*(1-cos(ΔRDM_V1)) + 0.2*Tikh
Cycle 15 opt2:   L = a*mw_jaccard(V4) + b*(1-ρ_LOCO_V1)    + 0.2*Tikh
                                            ↑ only V1 channel differs

Motivation: sub-09 V1 LOCO is NS but ΔRDM is sig (p=0.005, MEMORY 2026-03-23).
The matched V4 anchor isolates the V1 signal-channel effect.

Method:
1. Compute ΔRDM_obs(V1) for each subject (existing diagnostic_delta_rdm).
2. For each (β_s, β_c) in grid (41x61): compute ΔRDM_sim(V1) under
   2-comp forward model, then L_rdm = 1 - cosine(sim, obs).
3. Load V4 mw_jaccard_loss landscape (precomputed in inventory).
4. Combine and find argmin for several (α, β) weights.

Output: results/cycles/cycle14_v1_rdm_cross.json + .csv
"""

import json
import csv
import sys
import time
from pathlib import Path

import numpy as np

_SCRIPT_DIR = Path(__file__).resolve().parent
_PHASE2_SCRIPTS = _SCRIPT_DIR  # now top-level scripts/
sys.path.insert(0, str(_SCRIPT_DIR))

import loco_distortion_fit as ldf
from loco_distortion_fit import (
    HC_SUBJECTS, N_CHANNELS, HUE_ANGLES,
    create_basis_full, precompute_hc_W, load_amplitudes,
    get_shifted_design,
)
from diagnostic_delta_rdm import (
    compute_delta_rdm_obs, compute_delta_rdm_sim, cosine_similarity,
)

ROOT = _SCRIPT_DIR.parent  # future_phase2_filter_optimization/
RES = ROOT / 'results' / 'cycles'
RES.mkdir(parents=True, exist_ok=True)

OUT_JSON = RES / 'cycle14_v1_rdm_cross.json'
OUT_CSV = RES / 'cycle14_v1_rdm_cross.csv'

CVD_TYPE_MAP = {'08': 'deutan', '09': 'protan'}
HC_SUBJECTS_LOCAL = ['01', '02', '03', '04', '05', '06']
SUBJECTS_TO_RUN = HC_SUBJECTS_LOCAL + ['08', '09']

# Family convention: CVD subjects use their assigned family;
# HC subjects fit under BOTH families for family-symmetric sanity check
# (mirrors fit_hc_phase_a_sanity.py). Inventory consumer picks min loss family.
SUBJECT_FAMILIES = {}
for _s in HC_SUBJECTS_LOCAL:
    SUBJECT_FAMILIES[_s] = ['deutan', 'protan']
for _s, _f in CVD_TYPE_MAP.items():
    SUBJECT_FAMILIES[_s] = [_f]

_BS = np.arange(0.0, 81.0, 2.0)
_BC = np.arange(-60.0, 61.0, 2.0)
_BS_GRID, _BC_GRID = np.meshgrid(_BS, _BC, indexing='ij')
NORM_GRID = (_BS_GRID / 80.0) ** 2 + (_BC_GRID / 60.0) ** 2

LAM = 0.2

print('=' * 70)
print('Cycle 14: V1 RDM cross-criterion (variant of Cycle 12)')
print(f'Grid: {len(_BS)} x {len(_BC)} = {len(_BS) * len(_BC)} points')
print('=' * 70)

data_dir = ldf.LOCAL_DATA
print(f'Data: {data_dir}')

ROI_V1 = 'V1'
ROI_V4 = 'V4'

print(f'\n--- Loading HC + CVD data ---')
hc_amps_v1 = {hc: load_amplitudes(data_dir, hc, ROI_V1) for hc in HC_SUBJECTS}
basis_full = create_basis_full(N_CHANNELS, basis_type='fe')
C_baseline = basis_full[HUE_ANGLES]
hc_W_v1, _ = precompute_hc_W(hc_amps_v1, C_baseline)
print(f'  V1: {len(hc_amps_v1)} HC, V_s={hc_amps_v1["01"].shape[2]}')


def compute_v1_rdm_landscape(subj, cvd_type):
    print(f'\n--- Computing V1 ΔRDM landscape for sub-{subj} ({cvd_type}) ---')
    cvd_amp = load_amplitudes(data_dir, subj, ROI_V1)
    delta_rdm_obs, _, _, _ = compute_delta_rdm_obs(cvd_amp, hc_amps_v1)
    print(f'  ΔRDM_obs(V1, sub-{subj}) computed (28 elements)')
    print(f'    mean abs: {np.mean(np.abs(delta_rdm_obs)):.4f}, '
          f'max abs: {np.max(np.abs(delta_rdm_obs)):.4f}')

    landscape = np.zeros_like(_BS_GRID)
    cosines = np.zeros_like(_BS_GRID)

    t0 = time.time()
    for i in range(_BS_GRID.shape[0]):
        for j in range(_BS_GRID.shape[1]):
            params = np.array([_BS_GRID[i, j], _BC_GRID[i, j]])
            try:
                C_shifted, _ = get_shifted_design(
                    '2component', params, cvd_type)
                drdm_sim_mean, _ = compute_delta_rdm_sim(
                    hc_W_v1, C_shifted, C_baseline)
                cos = cosine_similarity(drdm_sim_mean, delta_rdm_obs)
                cosines[i, j] = cos
                landscape[i, j] = 1.0 - cos
            except Exception:
                landscape[i, j] = 1.0
                cosines[i, j] = 0.0
        if (i + 1) % 10 == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            print(f'  row {i+1}/{_BS_GRID.shape[0]} '
                  f'(min L_rdm so far = {landscape[:i+1].min():.4f}, '
                  f'{rate*_BS_GRID.shape[1]:.1f} pt/s)')

    elapsed = time.time() - t0
    min_idx = np.unravel_index(np.argmin(landscape), landscape.shape)
    print(f'  Done in {elapsed:.1f}s. '
          f'V1 RDM min: bs={_BS[min_idx[0]]:.0f}, bc={_BC[min_idx[1]]:.0f}, '
          f'L_rdm={landscape[min_idx]:.4f} (cos={cosines[min_idx]:+.4f})')

    return {
        'L_rdm_grid': landscape,
        'cosine_grid': cosines,
        'delta_rdm_obs': delta_rdm_obs.tolist(),
    }


def load_v4_anchor(subj):
    """V4 anchor = mw_jaccard_loss (matched to Cycle 15 opt2)."""
    p = RES / f'sub-{subj}_{ROI_V4}_landscape.json'
    if not p.exists():
        print(f'  WARN: V4 landscape not found at {p}')
        return None
    with open(p) as f:
        d = json.load(f)
    return np.array(d['mw_jaccard_loss'])


def find_min(grid):
    idx = np.unravel_index(np.argmin(grid), grid.shape)
    return float(_BS[idx[0]]), float(_BC[idx[1]]), float(grid[idx]), idx


WEIGHT_COMBOS = [(1.0, 1.0), (0.5, 1.0), (1.0, 0.5),
                 (2.0, 1.0), (1.0, 2.0)]

results = {
    'meta': {
        'cycle': 14,
        'task': 'V1 RDM cross-criterion variant of Cycle 12',
        'rule': ('L = alpha*mw_jaccard_loss(V4) + '
                 'beta*(1-cosine(ΔRDM_sim_V1, ΔRDM_obs_V1)) + 0.2*Tikh'),
        'v4_anchor_metric': 'mw_jaccard_loss (matched to Cycle 15 opt2)',
        'motivation': ('sub-09 V1 LOCO NS but ΔRDM p=0.005 (MEMORY). '
                       'Test if RDM-based V1 metric extracts different '
                       '(βs, βc) than Cycle 12 l_rank-based.'),
        'grid_bs': _BS.tolist(),
        'grid_bc': _BC.tolist(),
        'lam': LAM,
    },
    'per_subject': {},
    'csv_rows': [],
}

for subj in SUBJECTS_TO_RUN:
    families = SUBJECT_FAMILIES[subj]
    role = 'HC' if subj in HC_SUBJECTS_LOCAL else 'CVD'
    print(f'\n{"=" * 70}\nProcessing sub-{subj} ({role}, families={families})'
          f'\n{"=" * 70}')

    L_v4_anchor = load_v4_anchor(subj)
    if L_v4_anchor is None:
        print(f'  Skipping sub-{subj}: no V4 landscape')
        continue

    bs_v4, bc_v4, val_v4, _ = find_min(L_v4_anchor + LAM * NORM_GRID)
    print(f'  V4 mw_jaccard min only (deutan landscape): '
          f'bs={bs_v4:.0f}, bc={bc_v4:.0f}, L_anchor+Tikh={val_v4:.4f}')

    subj_entry = {
        'role': role,
        'families_fit': families,
        'v4_anchor_only': {'bs': bs_v4, 'bc': bc_v4,
                           'L_mw_jaccard_plus_tikh': val_v4},
        'per_family': {},
        'cross_rdm_weights': {},  # filled with min-family per weight combo
    }

    # Compute V1 RDM landscape per family
    fam_results = {}
    for cvd_type in families:
        v1 = compute_v1_rdm_landscape(subj, cvd_type)
        L_rdm_v1 = v1['L_rdm_grid']
        bs_v1, bc_v1, val_v1, _ = find_min(L_rdm_v1)

        fam_entry = {
            'cvd_type': cvd_type,
            'v1_rdm_only': {'bs': bs_v1, 'bc': bc_v1, 'L_rdm': val_v1},
            'cross_rdm_weights': {},
            'delta_rdm_obs_meanabs': float(np.mean(np.abs(v1['delta_rdm_obs']))),
        }

        for alpha, beta in WEIGHT_COMBOS:
            L_cross = alpha * L_v4_anchor + beta * L_rdm_v1 + LAM * NORM_GRID
            bs, bc, val, idx = find_min(L_cross)
            contrib = {
                'mw_jaccard_v4': float(L_v4_anchor[idx]),
                'l_rdm_v1': float(L_rdm_v1[idx]),
                'tikh': float(LAM * NORM_GRID[idx]),
                'cosine_v1': float(v1['cosine_grid'][idx]),
            }
            key = f'a{alpha}_b{beta}'
            fam_entry['cross_rdm_weights'][key] = {
                'bs': bs, 'bc': bc, 'L_total': val, **contrib,
            }
            print(f'  [{cvd_type}] α={alpha}, β={beta}: bs={bs:.0f}, '
                  f'bc={bc:.0f}, L={val:.4f}')

        fam_results[cvd_type] = fam_entry

    subj_entry['per_family'] = fam_results

    # For inventory consumer: pick the family with min L_total at default
    # weights (α=1, β=1), so that subj_entry['cross_rdm_weights'] mirrors
    # the original CVD-only schema. HC: best-fit family across deutan/protan.
    for alpha, beta in WEIGHT_COMBOS:
        key = f'a{alpha}_b{beta}'
        best_fam = min(
            families,
            key=lambda f: fam_results[f]['cross_rdm_weights'][key]['L_total'],
        )
        best = fam_results[best_fam]['cross_rdm_weights'][key]
        subj_entry['cross_rdm_weights'][key] = {
            **best,
            'best_family': best_fam,
        }
        results['csv_rows'].append({
            'subject': f'sub-{subj}',
            'role': role,
            'best_family': best_fam,
            'alpha': alpha, 'beta': beta,
            'bs': best['bs'], 'bc': best['bc'],
            'L_total': round(best['L_total'], 4),
            'mw_jaccard_v4': round(best['mw_jaccard_v4'], 4),
            'l_rdm_v1': round(best['l_rdm_v1'], 4),
            'cosine_v1': round(best['cosine_v1'], 4),
        })

    results['per_subject'][subj] = subj_entry

if results['csv_rows']:
    with open(OUT_CSV, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(results['csv_rows'][0].keys()))
        w.writeheader()
        w.writerows(results['csv_rows'])
    print(f'\nSaved CSV: {OUT_CSV}')

with open(OUT_JSON, 'w') as f:
    json.dump(results, f, indent=2)
print(f'Saved JSON: {OUT_JSON}')

print('\n' + '=' * 70)
print('COMPARISON WITH CYCLE 12 (l_rank-based) BEST PARAMS')
print('=' * 70)
cyc12_path = RES / 'cycle12_loss_cross_roi.json'
if cyc12_path.exists():
    with open(cyc12_path) as f:
        c12 = json.load(f)
    for subj in SUBJECTS_TO_RUN:
        if subj not in c12['per_subject']:
            continue
        c12_sub = c12['per_subject'][subj]
        c14_sub = results['per_subject'].get(subj)
        if not c14_sub:
            continue
        c12_def = c12_sub['cross_roi_weights'].get('a1.0_b1.0', {})
        c14_def = c14_sub['cross_rdm_weights'].get('a1.0_b1.0', {})
        role = c14_sub.get('role', 'CVD')
        fam_str = c14_def.get('best_family', '?')
        print(f'\nsub-{subj} ({role}, fam={fam_str}):')
        print(f"  Cycle 12 (V1 l_rank, a=b=1):  bs={c12_def.get('bs')}, "
              f"bc={c12_def.get('bc')}")
        print(f"  Cycle 14 (V1 RDM,    a=b=1):  bs={c14_def.get('bs')}, "
              f"bc={c14_def.get('bc')}")

# HC sanity summary
print('\n' + '=' * 70)
print('HC SANITY SUMMARY (Cycle 14 V1 RDM cross-criterion)')
print('=' * 70)
for alpha, beta in WEIGHT_COMBOS:
    key = f'a{alpha}_b{beta}'
    hc_norms = []
    cvd_norms = {}
    for subj, entry in results['per_subject'].items():
        e = entry['cross_rdm_weights'].get(key, {})
        norm = float(np.sqrt(e.get('bs', 0) ** 2 + e.get('bc', 0) ** 2))
        if entry.get('role') == 'HC':
            hc_norms.append(norm)
        else:
            cvd_norms[subj] = norm
    if not hc_norms:
        continue
    hc_arr = np.array(hc_norms)
    print(f'\n  α={alpha}, β={beta}:')
    print(f'    HC norms (n={len(hc_norms)}): mean={hc_arr.mean():.1f}, '
          f'sd={hc_arr.std():.1f}, range=[{hc_arr.min():.1f}, '
          f'{hc_arr.max():.1f}]')
    for cs, cn in cvd_norms.items():
        emp_p = float((hc_arr >= cn).sum() / len(hc_arr))
        verdict = 'sig' if emp_p <= 0.20 else 'NS'
        print(f'    sub-{cs}: norm={cn:.1f}  emp_p={emp_p:.2f}  ({verdict})')
