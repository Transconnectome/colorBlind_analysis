"""unified_loss_bootstrap_anchor.py — Re-evaluate unified loss using
L_combined bootstrap median as the V4 β_c anchor.

Background (2026-05-13 update):
  Prior unified loss used phase_a V4 LOCO 2-comp anchors:
    sub-08: (β_s=38, β_c=−14)  [phase_a L_fit = α·MSE + β·rank + δ·RDM + ε·smooth]
  But L_combined bootstrap on axis_3way landscape gives:
    sub-08: (β_s=40, β_c=+22) [L_combined = l_ccc + l_topk + tikh, 100% sign consistency]

  These are OPPOSITE-sign fits from the SAME V4 neural data, distinguished only
  by the choice of loss formulation. L_combined is scale-invariant (CCC + rank)
  and is what we use in the actual filter-fitting pipeline.

  Therefore: V4 β_c anchor should be L_combined-bootstrap-derived, not phase_a.

This script:
  1. Loads L_combined bootstrap medians (computed by sub08_bc_bootstrap.py).
  2. Re-runs unified loss with this updated anchor for both subjects.
  3. Reports the new argmin, P2a, distance to P2a-max, literature compatibility.
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
    V1_DELTA_RDM, P2A_MAX, BAYESIAN_BEST,
    EMERY_BETA_S, TREGILLUS_NORM, BRETTEL_SIGN,
    L_rdm_cosine, p2a_eval, literature_score,
)

OUT = _THIS_DIR.parent / 'results' / 'LIT2Neural'

HUE_8 = [0, 45, 90, 135, 180, 225, 270, 315]


def bootstrap_anchor_v4(subject):
    """Compute V4 LOCO L_combined bootstrap β_s, β_c medians for `subject`.
    Reads from sub08_bc_bootstrap.py output if present (sub-08 axis=150°).
    For sub-09, runs the equivalent bootstrap on the fly.
    """
    boot_path = OUT / 'sub08_bc_bootstrap.json'
    if subject == 'sub-08' and boot_path.exists():
        d = json.load(open(boot_path))
        b = d['sub-08_axis150']['bootstrap']
        return b['bs_median'], b['bc_median']

    # Compute for sub-09 on the fly (axis=16°, Stockman protan)
    if subject == 'sub-09':
        from sub08_bc_bootstrap import load_landscape, bootstrap_bc_ci
        path = Path('results/axis_3way/sub-09_V4_Stockman16ext_landscape.json')
        bs, bc, vuln_sim, vuln_obs, l_topk, tikh, ccc_raw, cells = load_landscape(path)
        bs_b, bc_b = bootstrap_bc_ci(bs, bc, vuln_sim, vuln_obs,
                                       l_topk, tikh, n_boot=2000)
        bs_lo, bs_hi = np.percentile(bs_b, [2.5, 97.5])
        bc_lo, bc_hi = np.percentile(bc_b, [2.5, 97.5])
        frac_neg = float((bc_b < 0).mean())
        return float(np.median(bs_b)), float(np.median(bc_b)), {
            'bs_ci': (float(bs_lo), float(bs_hi)),
            'bc_ci': (float(bc_lo), float(bc_hi)),
            'frac_neg': frac_neg,
        }

    raise ValueError(f'No bootstrap data for {subject}')


def unified_loss_sweep(landscape_path, subject, axis, target_map, p2a_max_pt,
                        anchor_bs, anchor_bc,
                        sigma_s=10.0, sigma_c=15.0, lam_rdm=0.5):
    d = json.load(open(landscape_path))
    cells = d['cells']
    vuln_obs = np.array(d['vuln_cvd'])
    L_vals = np.array([
        ((c['bs'] - anchor_bs) / sigma_s) ** 2
        + ((c['bc'] - anchor_bc) / sigma_c) ** 2
        + lam_rdm * L_rdm_cosine(np.array(c['vuln_sim']), vuln_obs)
        for c in cells
    ])
    bs_arr = np.array([c['bs'] for c in cells])
    bc_arr = np.array([c['bc'] for c in cells])
    sort_key = L_vals * 1e6 + bs_arr**2 + bc_arr**2
    idx = int(np.argmin(sort_key))
    best = cells[idx]
    bs, bc = best['bs'], best['bc']
    p2a, ex = p2a_eval(bs, bc, axis, target_map)
    lit = literature_score(bs, bc, target_map_to_family(subject))
    return {
        'argmin': (bs, bc),
        'L_min': float(L_vals[idx]),
        'p2a': p2a, 'exact': ex,
        'dist_to_p2amax': float(np.hypot(bs - p2a_max_pt[0], bc - p2a_max_pt[1])),
        'norm': lit['norm'],
        'emery_dev': lit['emery_dev'],
        'tregillus_dev': lit['tregillus_dev'],
        'brettel_sign_ok': lit['brettel_sign_ok'],
    }


def target_map_to_family(subject):
    return 'deutan' if subject == 'sub-08' else 'protan'


def main():
    cases = [
        ('sub-08', 150.0,
         'results/axis_3way/sub-08_V4_Stockman150_landscape.json',
         SUB08_ORIGINAL_HC_EQUIV),
        ('sub-09', 16.0,
         'results/axis_3way/sub-09_V4_Stockman16ext_landscape.json',
         SUB09_ORIGINAL_HC_EQUIV),
    ]

    print('='*100)
    print('UNIFIED LOSS — bootstrap-derived V4 β_c anchor (L_combined)')
    print('='*100)
    print('  Anchor: β_s from V1 ΔRDM bootstrap')
    print('          β_c from V4 L_combined bootstrap median (N=2000, axis_3way landscape)')
    print()

    all_results = {}
    for sid, axis, lp, tmap in cases:
        if not Path(lp).exists(): continue

        # Compute or load bootstrap anchor
        if sid == 'sub-08':
            anchor_bs_v4, anchor_bc_v4 = bootstrap_anchor_v4(sid)
            extra = {}
        else:
            ret = bootstrap_anchor_v4(sid)
            anchor_bs_v4, anchor_bc_v4, extra = ret

        # β_s anchor: V1 ΔRDM (unchanged from prior pipeline)
        anchor_bs = V1_DELTA_RDM[sid][0]
        anchor_bc = anchor_bc_v4

        r = unified_loss_sweep(lp, sid, axis, tmap, P2A_MAX[sid],
                                anchor_bs, anchor_bc)

        print(f'\n--- {sid} axis={axis}° ---')
        print(f'  Anchors (bootstrap-derived):')
        print(f'    β_s = {anchor_bs:+.1f}° (V1 ΔRDM bootstrap)')
        print(f'    β_c = {anchor_bc:+.1f}° (V4 L_combined bootstrap median)')
        if extra:
            print(f'    [sub-09 V4 β_s_boot={anchor_bs_v4:.1f}°, β_c CI={extra["bc_ci"]}, '
                  f'frac_neg={extra["frac_neg"]:.3f}]')
        bs, bc = r['argmin']
        print(f'  Loss argmin: ({bs:.0f}, {bc:+.0f})')
        print(f'  P2a = {r["p2a"]:.3f}  exact={r["exact"]}/8  '
              f'dist_to_P2a-max = {r["dist_to_p2amax"]:.1f}°')
        print(f'  ‖β‖ = {r["norm"]:.1f}°  Emery dev = {r["emery_dev"]:.1f}°  '
              f'Tregillus dev = {r["norm"] - TREGILLUS_NORM:+.1f}°  '
              f'Brettel = {r["brettel_sign_ok"]}')
        all_results[sid] = {
            'anchors': {
                'beta_s_V1deltaRDM': anchor_bs,
                'beta_c_V4_Lcombined_boot_median': anchor_bc,
                'extra': extra,
            },
            **r,
        }

    print('\n' + '='*100)
    print('COMPARISON: phase_a anchor vs L_combined bootstrap anchor')
    print('='*100)
    # Re-run with original phase_a anchor (β_c = -14 for sub-08, -22 for sub-09)
    phase_a_anchors = {'sub-08': -14.0, 'sub-09': -22.0}
    for sid, axis, lp, tmap in cases:
        if not Path(lp).exists(): continue
        anchor_bs = V1_DELTA_RDM[sid][0]
        anchor_bc_phase_a = phase_a_anchors[sid]
        anchor_bc_lcomb = all_results[sid]['anchors']['beta_c_V4_Lcombined_boot_median']
        r_phase_a = unified_loss_sweep(lp, sid, axis, tmap, P2A_MAX[sid],
                                         anchor_bs, anchor_bc_phase_a)
        r_lcomb = all_results[sid]
        print(f'\n  {sid}:')
        print(f'    phase_a anchor (β_c={anchor_bc_phase_a:+.0f}°) → '
              f'argmin {r_phase_a["argmin"]}, P2a={r_phase_a["p2a"]:.3f}, '
              f'dist={r_phase_a["dist_to_p2amax"]:.1f}°')
        print(f'    L_comb anchor  (β_c={anchor_bc_lcomb:+.0f}°) → '
              f'argmin {r_lcomb["argmin"]}, P2a={r_lcomb["p2a"]:.3f}, '
              f'dist={r_lcomb["dist_to_p2amax"]:.1f}°')

    out_path = OUT / 'unified_loss_bootstrap_anchor.json'
    with open(out_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f'\nWrote {out_path}')


if __name__ == '__main__':
    main()
