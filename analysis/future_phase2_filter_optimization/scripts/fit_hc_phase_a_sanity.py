#!/usr/bin/env python3
"""
fit_hc_phase_a_sanity.py — Run Phase A canonical L_LOCO fit on HC subjects.

Purpose: complete the loss inventory's HC sanity check for the canonical
loss (L_fit = α·L_vuln + β·L_rank + δ·L_rdm + ε·L_smooth, default weights).

For each HC subject (sub-01..07) × ROI {V1, V4} × cvd_type {deutan, protan}:
  - Use that HC's LOCO vulnerability profile as target
  - Use HC pool (LOO recommended but using all HC for consistency with phase_a)
  - Fit 2-component model
  - Save results matching phase_a JSON format

Output: results/fits/phase_a_2component_hc_sanity/
  - sub-XX_ROI_2component_{deutan,protan}.json
  - landscape JSONs (large)
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
    HC_SUBJECTS, N_CHANNELS, HUE_ANGLES,
    create_basis_full, precompute_hc_W, load_amplitudes,
    load_cvd_loco_target, grid_search, run_permutation_tests,
    DEFAULT_WEIGHTS, FILTER_MODELS,
)
from diagnostic_delta_rdm import compute_delta_rdm_obs

OUT_DIR = (_SCRIPT_DIR.parent / 'results' / 'fits'
           / 'phase_a_2component_hc_sanity')
OUT_DIR.mkdir(parents=True, exist_ok=True)

ROIS = ['V1', 'V4']
CVD_TYPES = ['deutan', 'protan']  # fit HC under both CVD models

data_dir = ldf.LOCAL_DATA
print(f'Data: {data_dir}')
print(f'Output: {OUT_DIR}')
print(f'Will fit: {len(HC_SUBJECTS)} HC × {len(ROIS)} ROIs × '
      f'{len(CVD_TYPES)} CVD models = '
      f'{len(HC_SUBJECTS) * len(ROIS) * len(CVD_TYPES)} fits')
print(f'2-component grid: {len(np.arange(0, 51, 2))}x'
      f'{len(np.arange(-50, 51, 2))} = '
      f'{len(np.arange(0, 51, 2)) * len(np.arange(-50, 51, 2))} pts/fit\n')


def load_hc_loco_vuln(hc_subj, roi):
    """Load HC's own LOCO vulnerability profile.

    HC LOCO files at future_phase1_forward_model/results/validation/.
    Same format as CVD: load_cvd_loco_target works for any subject.
    """
    return load_cvd_loco_target(hc_subj, roi)


total_start = time.time()
results_summary = []

for hc_subj in HC_SUBJECTS:
    for roi in ROIS:
        # Load HC pool (all 7) and target HC's vuln
        hc_amps_dict = {hc: load_amplitudes(data_dir, hc, roi)
                        for hc in HC_SUBJECTS}
        try:
            target_vuln = load_hc_loco_vuln(hc_subj, roi)
        except Exception as e:
            print(f'  SKIP sub-{hc_subj} {roi}: HC LOCO load failed: {e}')
            continue

        # Precompute W
        basis_full = create_basis_full(N_CHANNELS, basis_type='fe')
        C_baseline = basis_full[HUE_ANGLES]
        hc_W_dict, _ = precompute_hc_W(hc_amps_dict, C_baseline)

        # ΔRDM_obs for the target HC (vs HC pool mean — note: includes
        # self in pool, but consistent with phase_a CVD pipeline)
        cvd_amp = load_amplitudes(data_dir, hc_subj, roi)
        try:
            delta_rdm_obs, _, _, _ = compute_delta_rdm_obs(
                cvd_amp, hc_amps_dict)
        except Exception:
            delta_rdm_obs = None

        for cvd_type in CVD_TYPES:
            tag = f'sub-{hc_subj}_{roi}_2component_{cvd_type}'
            print(f'\n=== Fit {tag} ===')
            t0 = time.time()
            result = grid_search(
                '2component', hc_amps_dict, target_vuln, cvd_type,
                method='shift_at_both',
                hc_W_dict=hc_W_dict, delta_rdm_obs=delta_rdm_obs,
                weights=None,  # use DEFAULT_WEIGHTS
                verbose=False,
            )
            best_vuln = np.array(result['best_loss']['vuln_sim'])
            perm = run_permutation_tests(best_vuln, target_vuln, n_perm=2000)
            result['permutation'] = perm
            elapsed = time.time() - t0

            # Save compact (no landscape) for inventory
            compact = {k: v for k, v in result.items() if k != 'landscape'}
            compact['subject'] = hc_subj
            compact['role'] = 'HC'
            compact['roi'] = roi
            compact['cvd_type_assumed'] = cvd_type
            compact['fit_target'] = 'HC own LOCO vulnerability'
            out_path = OUT_DIR / f'{tag}.json'
            with open(out_path, 'w') as f:
                json.dump(compact, f, indent=2, default=str)

            bs, bc = result['best_params']
            print(f'  best params: ({bs}, {bc})  '
                  f'L_fit={result["best_loss"]["l_fit"]:.4f}  '
                  f'ρ={perm["spearman_r"]:+.3f}  '
                  f'perm_p={perm["label_perm_p"]:.3f}  '
                  f'elapsed={elapsed:.1f}s')
            results_summary.append({
                'subject': f'sub-{hc_subj}', 'role': 'HC', 'roi': roi,
                'cvd_type': cvd_type, 'beta_s': bs, 'beta_c': bc,
                'l_fit': result['best_loss']['l_fit'],
                'spearman_r': perm['spearman_r'],
                'perm_p': perm['label_perm_p'],
            })

# Summary
import csv
with open(OUT_DIR / 'hc_sanity_summary.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(results_summary[0].keys()))
    w.writeheader()
    w.writerows(results_summary)
print(f'\nSaved summary: {OUT_DIR / "hc_sanity_summary.csv"}')
print(f'Total elapsed: {(time.time() - total_start) / 60:.1f} min')

# Quick HC norm summary
print('\n=== HC sanity (per cvd_type, per ROI) ===')
for cvd_type in CVD_TYPES:
    for roi in ROIS:
        norms = [np.sqrt(r['beta_s']**2 + r['beta_c']**2)
                 for r in results_summary
                 if r['cvd_type'] == cvd_type and r['roi'] == roi]
        if norms:
            print(f'  cvd={cvd_type:>7s} ROI={roi}: '
                  f'HC norm mean={np.mean(norms):.1f}, '
                  f'sd={np.std(norms):.1f}, '
                  f'min={min(norms):.1f}, max={max(norms):.1f}, n={len(norms)}')
