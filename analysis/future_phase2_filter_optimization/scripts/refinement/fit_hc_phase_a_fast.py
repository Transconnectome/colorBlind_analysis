#!/usr/bin/env python3
"""fit_hc_phase_a_fast.py — Fast V4-only canonical L_LOCO HC sanity.

Skips run_permutation_tests (we only need (β_s, β_c) norms for inventory CI).
ROI = V4 only (canonical §3 PASS filter is at V4).
Family-symmetric (both deutan AND protan, take min L_fit).

Output: results/fits/phase_a_2component_hc_sanity/sub-XX_V4_2component_FAST.json
"""
import json
import sys
import time
from pathlib import Path
import numpy as np

_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR.parent))

import loco_distortion_fit as ldf
from loco_distortion_fit import (
    HC_SUBJECTS, N_CHANNELS, HUE_ANGLES,
    create_basis_full, precompute_hc_W, load_amplitudes,
    load_cvd_loco_target, grid_search,
)
from diagnostic_delta_rdm import compute_delta_rdm_obs

OUT_DIR = (_SCRIPT_DIR.parent.parent / 'results' / 'fits'
           / 'phase_a_2component_hc_sanity')
OUT_DIR.mkdir(parents=True, exist_ok=True)
SUMMARY_JSON = OUT_DIR / 'fast_summary_V4.json'

ROI = 'V4'
CVD_TYPES = ['deutan', 'protan']
HC_USE = ['01', '02', '03', '04', '05', '06']  # exclude sub-07 (16 voxels)

# Add CVD subjects so we have apples-to-apples norms
CVD_FAMILIES = {'08': ['deutan'], '09': ['protan']}

data_dir = ldf.LOCAL_DATA
print(f'Data: {data_dir}', flush=True)
print(f'Output: {OUT_DIR}', flush=True)

# Pre-load HC amps + W (use full 7 HC for the simulator pool, even though
# we only test sanity on 6 of them; this matches CVD pipeline)
print('Loading HC amplitudes...', flush=True)
hc_amps_dict = {hc: load_amplitudes(data_dir, hc, ROI) for hc in HC_SUBJECTS}
basis_full = create_basis_full(N_CHANNELS, basis_type='fe')
C_baseline = basis_full[HUE_ANGLES]
hc_W_dict, _ = precompute_hc_W(hc_amps_dict, C_baseline)
print(f'  HC pool: {len(hc_W_dict)} subjects', flush=True)

results_summary = []
total_start = time.time()

# Subjects to test sanity on: HC (6, both families) + CVD (2, single family)
TEST_SUBJECTS = [(s, 'HC', CVD_TYPES) for s in HC_USE] + \
                [(s, 'CVD', CVD_FAMILIES[s]) for s in CVD_FAMILIES]

for subj, role, families in TEST_SUBJECTS:
    print(f'\n=== sub-{subj} ({role}, families={families}) ===', flush=True)

    try:
        target_vuln = load_cvd_loco_target(subj, ROI)
    except Exception as e:
        print(f'  SKIP: LOCO load failed: {e}', flush=True)
        continue

    cvd_amp = load_amplitudes(data_dir, subj, ROI)
    try:
        delta_rdm_obs, _, _, _ = compute_delta_rdm_obs(cvd_amp, hc_amps_dict)
    except Exception:
        delta_rdm_obs = None

    fam_results = {}
    for cvd_type in families:
        t0 = time.time()
        result = grid_search(
            '2component', hc_amps_dict, target_vuln, cvd_type,
            method='shift_at_both',
            hc_W_dict=hc_W_dict, delta_rdm_obs=delta_rdm_obs,
            weights=None,  # canonical L_fit weights
            verbose=False,
        )
        elapsed = time.time() - t0
        bs, bc = result['best_params']
        l_fit = result['best_loss']['l_fit']
        fam_results[cvd_type] = {
            'beta_s': float(bs), 'beta_c': float(bc),
            'l_fit': float(l_fit),
            'l_vuln': float(result['best_loss'].get('l_vuln', np.nan)),
            'l_rank': float(result['best_loss'].get('l_rank', np.nan)),
            'l_rdm': float(result['best_loss'].get('l_rdm', np.nan)),
            'l_smooth': float(result['best_loss'].get('l_smooth', np.nan)),
            'spearman_r_raw': float(result['best_loss'].get(
                'spearman_r', np.nan)),
        }
        print(f'  [{cvd_type}] (β_s,β_c)=({bs},{bc}) L_fit={l_fit:.4f} '
              f'elapsed={elapsed:.1f}s', flush=True)

    # Pick best family by L_fit
    best_fam = min(fam_results, key=lambda f: fam_results[f]['l_fit'])
    best = fam_results[best_fam]
    norm = float(np.sqrt(best['beta_s'] ** 2 + best['beta_c'] ** 2))

    results_summary.append({
        'subject': f'sub-{subj}', 'role': role, 'roi': ROI,
        'best_family': best_fam,
        'beta_s': best['beta_s'], 'beta_c': best['beta_c'],
        'norm': round(norm, 2),
        'l_fit': best['l_fit'],
        'per_family': fam_results,
    })

    print(f'  → best_family={best_fam}, norm={norm:.1f}', flush=True)

# Save
with open(SUMMARY_JSON, 'w') as f:
    json.dump({'roi': ROI,
               'family_convention': 'symmetric (deutan + protan, min L_fit)',
               'weights': 'canonical L_fit (default)',
               'subjects': results_summary,
               }, f, indent=2)

total_elapsed = (time.time() - total_start) / 60
print(f'\n=== DONE in {total_elapsed:.1f} min ===', flush=True)
print(f'Saved: {SUMMARY_JSON}', flush=True)

# Quick HC vs CVD summary
hc_norms = [r['norm'] for r in results_summary if r['role'] == 'HC']
cvd_norms = {r['subject']: r['norm']
             for r in results_summary if r['role'] == 'CVD'}
if hc_norms and cvd_norms:
    hc_arr = np.array(hc_norms)
    print(f'\nHC norms (n={len(hc_norms)}): mean={hc_arr.mean():.1f}, '
          f'sd={hc_arr.std():.1f}, range=[{hc_arr.min():.1f}, '
          f'{hc_arr.max():.1f}]', flush=True)
    print(f'HC: {sorted(hc_norms, reverse=True)}', flush=True)
    for cs, cn in cvd_norms.items():
        emp_p = float((hc_arr >= cn).sum() / len(hc_arr))
        print(f'  {cs}: norm={cn}  emp_p={emp_p:.2f}  '
              f'HC_mean<CVD={"Y" if hc_arr.mean() < cn else "N"}  '
              f'HC_max<CVD={"Y" if hc_arr.max() < cn else "N"}', flush=True)
