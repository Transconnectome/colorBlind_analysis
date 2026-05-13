"""neural_only_unified_loss.py — Single unified loss for BOTH subjects.

Loss formulation (identical for sub-08 and sub-09):

  L(β_s, β_c | subject) =
        w_s · ((β_s − β_s^{V1ΔRDM}[subject]) / σ_s)²
      + w_c · ((β_c − β_c^{V4LOCO2c}[subject]) / σ_c)²
      + λ  · L_RDM_cos(vuln_sim, vuln_cvd)

  Defaults: w_s = w_c = 1, σ_s = 10°, σ_c = 15°, λ = 0.5

Each anchor is extracted from THE subject's OWN neural data — same protocol
across subjects. No literature constants enter the loss. Per-subject anchor
values are listed for transparency.

Components — neural source & literature mapping:
  β_s anchor (V1 ΔRDM bootstrap)
    ↔ retinal-level cone-shift signal      → Machado 2009 severity, Emery 2021 β_s≈21.4°
  β_c anchor (V4 LOCO 2-comp fit)
    ↔ cortical confusion-axis amplitude    → Brettel 1997 sign convention
  L_RDM_cos (V4 vuln_sim ↔ vuln_cvd RDM cosine)
    ↔ representational geometry consistency → Kriegeskorte 2008 RSA, scale-invariant
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
import numpy as np

_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR))

from phase3_candidate_analysis_v2 import hc_name, hc_match_score, SUB08_ORIGINAL_HC_EQUIV
from fixedW_onlyTest_p2a_ranking import SUB09_ORIGINAL_HC_EQUIV
from neural_only_deep_sweep import (
    NEURAL_ANCHORS, V1_DELTA_RDM, P2A_MAX, BAYESIAN_BEST,
    EMERY_BETA_S, TREGILLUS_NORM, BRETTEL_SIGN,
    L_rdm_cosine, p2a_eval, literature_score,
)

OUT = _THIS_DIR.parent / 'results'
FILE_PREFIX = 'LIT2Neural_'
OUT.mkdir(parents=True, exist_ok=True)

HUE_8 = [0, 45, 90, 135, 180, 225, 270, 315]


def unified_loss(c, vuln_obs, anchor_bs, anchor_bc,
                 w_s=1.0, w_c=1.0, sigma_s=10.0, sigma_c=15.0, lam_rdm=0.5):
    return (
        w_s * ((c['bs'] - anchor_bs) / sigma_s) ** 2
        + w_c * ((c['bc'] - anchor_bc) / sigma_c) ** 2
        + lam_rdm * L_rdm_cosine(np.array(c['vuln_sim']), vuln_obs)
    )


def sweep(landscape_path, subject, family, axis, target_map, p2a_max_pt,
          w_s=1.0, w_c=1.0, sigma_s=10.0, sigma_c=15.0, lam_rdm=0.5):
    with open(landscape_path) as f:
        d = json.load(f)
    cells = d['cells']
    vuln_obs = np.array(d['vuln_cvd'])
    anchor_bs = V1_DELTA_RDM[subject][0]
    anchor_bc = NEURAL_ANCHORS[subject]['V4'][1]

    L_vals = np.array([
        unified_loss(c, vuln_obs, anchor_bs, anchor_bc,
                     w_s, w_c, sigma_s, sigma_c, lam_rdm)
        for c in cells
    ])
    bs_arr = np.array([c['bs'] for c in cells])
    bc_arr = np.array([c['bc'] for c in cells])
    sort_key = L_vals * 1e6 + bs_arr ** 2 + bc_arr ** 2
    idx = int(np.argmin(sort_key))
    best = cells[idx]
    bs, bc = best['bs'], best['bc']
    p2a, ex = p2a_eval(bs, bc, axis, target_map)
    lit = literature_score(bs, bc, family)
    return {
        'subject': subject, 'family': family, 'axis': axis,
        'anchors': {
            'beta_s_V1deltaRDM': anchor_bs,
            'beta_c_V4LOCO2c':   anchor_bc,
        },
        'best': {
            'bs': bs, 'bc': bc, 'L': float(L_vals[idx]),
            'p2a': p2a, 'exact': ex,
            'dist_to_p2amax': float(np.hypot(bs - p2a_max_pt[0], bc - p2a_max_pt[1])),
            'dist_to_canonical': float(np.hypot(
                bs - NEURAL_ANCHORS[subject]['V4'][0],
                bc - NEURAL_ANCHORS[subject]['V4'][1])),
            'norm': lit['norm'],
            'emery_dev':     lit['emery_dev'],
            'tregillus_dev': lit['tregillus_dev'],
            'brettel_sign_ok': lit['brettel_sign_ok'],
        },
    }


def hyperparam_sensitivity(landscape_path, subject, family, axis, target_map,
                            p2a_max_pt):
    """Test loss stability under hyperparameter perturbations."""
    settings = [
        # (label, w_s, w_c, sigma_s, sigma_c, lam_rdm)
        ('default',          1.0, 1.0, 10, 15, 0.5),
        ('high σ (loose)',    1.0, 1.0, 20, 25, 0.5),
        ('low σ (tight)',     1.0, 1.0,  5,  8, 0.5),
        ('no RDM',            1.0, 1.0, 10, 15, 0.0),
        ('high RDM',          1.0, 1.0, 10, 15, 2.0),
        ('β_s heavy',         2.0, 1.0, 10, 15, 0.5),
        ('β_c heavy',         1.0, 2.0, 10, 15, 0.5),
        ('β_s only',          1.0, 0.0, 10, 15, 0.0),
        ('β_c only',          0.0, 1.0, 10, 15, 0.0),
        ('shape only (RDM)',  0.0, 0.0, 10, 15, 1.0),
    ]
    rows = []
    for label, ws, wc, ss, sc, lr in settings:
        r = sweep(landscape_path, subject, family, axis, target_map, p2a_max_pt,
                  w_s=ws, w_c=wc, sigma_s=ss, sigma_c=sc, lam_rdm=lr)
        b = r['best']
        rows.append({
            'setting': label, 'bs': b['bs'], 'bc': b['bc'],
            'p2a': b['p2a'], 'dist_to_p2amax': b['dist_to_p2amax'],
            'norm': b['norm'], 'emery_dev': b['emery_dev'],
        })
    return rows


def main():
    cases = [
        ('sub-08', 'deutan', 150.0,
         'results/axis_3way/sub-08_V4_Stockman150_landscape.json',
         SUB08_ORIGINAL_HC_EQUIV),
        ('sub-09', 'protan',  16.0,
         'results/axis_3way/sub-09_V4_Stockman16ext_landscape.json',
         SUB09_ORIGINAL_HC_EQUIV),
    ]

    print('='*100)
    print('UNIFIED NEURAL-ONLY LOSS — same formulation, per-subject neural anchors')
    print('='*100)
    print('  L = ((β_s − β_s^V1ΔRDM)/10)² + ((β_c − β_c^V4LOCO2c)/15)² + 0.5·L_RDM_cos(V4)')
    print()

    main_results = {}
    for sid, fam, axis, lp, tmap in cases:
        if not Path(lp).exists(): continue
        r = sweep(lp, sid, fam, axis, tmap, P2A_MAX[sid])
        print(f'\n--- {sid} ({fam}) axis={axis}° ---')
        print(f'  Anchors (per-subject neural extraction):')
        print(f'    β_s = {r["anchors"]["beta_s_V1deltaRDM"]:+.1f}° from V1 ΔRDM bootstrap')
        print(f'    β_c = {r["anchors"]["beta_c_V4LOCO2c"]:+.1f}° from V4 LOCO 2-component')
        b = r['best']
        print(f'  Loss argmin: (β_s={b["bs"]:.0f}°, β_c={b["bc"]:+.0f}°)')
        print(f'  P2a = {b["p2a"]:.3f}   exact = {b["exact"]}/8   dist_to_P2a-max = {b["dist_to_p2amax"]:.1f}°')
        print(f'  ||β|| = {b["norm"]:.1f}°   Emery dev = {b["emery_dev"]:.1f}°   '
              f'Tregillus dev (28°) = {b["norm"] - TREGILLUS_NORM:+.1f}°   '
              f'Brettel sign = {b["brettel_sign_ok"]}')
        main_results[sid] = r

    print('\n' + '='*100)
    print('HYPERPARAMETER SENSITIVITY (sub-09)')
    print('='*100)
    rows = hyperparam_sensitivity('results/axis_3way/sub-09_V4_Stockman16ext_landscape.json',
                                   'sub-09', 'protan', 16.0,
                                   SUB09_ORIGINAL_HC_EQUIV, P2A_MAX['sub-09'])
    print(f'  {"setting":<22s}  {"argmin":<12s}  {"P2a":>5s}  {"d→max":>6s}  {"|β|":>5s}  {"Em-dev":>6s}')
    for row in rows:
        print(f'  {row["setting"]:<22s}  ({row["bs"]:>3.0f},{row["bc"]:>+4.0f})    '
              f'{row["p2a"]:>5.3f}  {row["dist_to_p2amax"]:>6.1f}  '
              f'{row["norm"]:>5.1f}  {row["emery_dev"]:>6.1f}')
    main_results['sub-09_sensitivity'] = rows

    print('\n' + '='*100)
    print('HYPERPARAMETER SENSITIVITY (sub-08)')
    print('='*100)
    rows = hyperparam_sensitivity('results/axis_3way/sub-08_V4_Stockman150_landscape.json',
                                   'sub-08', 'deutan', 150.0,
                                   SUB08_ORIGINAL_HC_EQUIV, P2A_MAX['sub-08'])
    print(f'  {"setting":<22s}  {"argmin":<12s}  {"P2a":>5s}  {"d→max":>6s}  {"|β|":>5s}  {"Em-dev":>6s}')
    for row in rows:
        print(f'  {row["setting"]:<22s}  ({row["bs"]:>3.0f},{row["bc"]:>+4.0f})    '
              f'{row["p2a"]:>5.3f}  {row["dist_to_p2amax"]:>6.1f}  '
              f'{row["norm"]:>5.1f}  {row["emery_dev"]:>6.1f}')
    main_results['sub-08_sensitivity'] = rows

    with open(OUT / 'unified_loss_results.json', 'w') as f:
        json.dump(main_results, f, indent=2)
    print(f'\nWrote {OUT / "unified_loss_results.json"}')


if __name__ == '__main__':
    main()
