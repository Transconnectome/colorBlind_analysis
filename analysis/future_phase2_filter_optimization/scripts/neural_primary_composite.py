"""neural_primary_composite.py — Neural-primary filter with weak physiological prior.

Framework architecture (사용자 제안, 2026-05-13):

    L = α_n · L_neural_composite
      + α_p · L_phys_prior
      + α_a · L_amplitude

  L_neural_composite =
        w1 · L_V1_ΔRDM_anchor       (β_s, primary, retinal-level cone-shift)
      + w2 · L_V4_LOCO_2comp_anchor  (β_c, primary, cortical confusion-axis)
      + w3 · L_V4_RDM_shape          (V4 vuln_sim ↔ vuln_cvd cosine, scale-invariant)
      + w4 · L_local_vulnerability   (l_topk Jaccard, top-K vulnerable colors)

  L_phys_prior =
        w_sign · weak Brettel sign  (very low weight — implausibility filter only)
      + w_norm · weak Tregillus     (very low weight — large-norm penalty only)

  L_amplitude = Tikh (β_s² + β_c²) / 32400

α_neural sweep: {0.5, 0.7, 0.9} — physiological prior가 implausible 영역만 차단.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
import numpy as np
from scipy.stats import pearsonr

_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR))

from phase3_candidate_analysis_v2 import hc_name, hc_match_score, SUB08_ORIGINAL_HC_EQUIV
from fixedW_onlyTest_p2a_ranking import SUB09_ORIGINAL_HC_EQUIV
from neural_only_deep_sweep import (
    NEURAL_ANCHORS, V1_DELTA_RDM, P2A_MAX, BAYESIAN_BEST,
    EMERY_BETA_S, TREGILLUS_NORM, BRETTEL_SIGN,
    L_rdm_cosine, p2a_eval,
)

OUT = _THIS_DIR.parent / 'results' / 'neural_primary'
OUT.mkdir(parents=True, exist_ok=True)

HUE_8 = [0, 45, 90, 135, 180, 225, 270, 315]


def L_anchor_quad(value, target, scale):
    return ((value - target) / scale) ** 2


def L_sign_weak(bc, sign_exp, scale=50.0):
    """Weak Brettel sign — only penalize when β_c clearly wrong direction with large amp."""
    return max(0.0, -bc * sign_exp / scale) ** 2


def L_norm_plausibility(bs, bc, norm_max=50.0):
    """Penalize only above plausibility ceiling (Tregillus 50% upper bound ~32°)."""
    norm = np.hypot(bs, bc)
    return max(0.0, (norm - norm_max) / 10.0) ** 2


def composite_loss(c, vuln_obs, anchor_bs, anchor_bc, family,
                   alpha_neural=0.7, alpha_phys=0.2, alpha_amp=0.1,
                   w1=0.3, w2=0.3, w3=0.2, w4=0.2,
                   w_sign=0.5, w_norm=0.5,
                   sigma_s=10.0, sigma_c=15.0,
                   norm_ceiling=50.0):
    """Compute composite L for a single grid cell."""
    bs, bc = c['bs'], c['bc']
    vuln_sim = np.array(c['vuln_sim'])

    # Neural composite
    L_v1 = L_anchor_quad(bs, anchor_bs, sigma_s)
    L_v4 = L_anchor_quad(bc, anchor_bc, sigma_c)
    L_shape = L_rdm_cosine(vuln_sim, vuln_obs)
    L_topk = float(c['l_topk'])  # already in [0, 1]
    L_neural = w1 * L_v1 + w2 * L_v4 + w3 * L_shape + w4 * L_topk

    # Physiological prior (weak)
    sign_exp = BRETTEL_SIGN[family]
    L_sign = L_sign_weak(bc, sign_exp)
    L_norm = L_norm_plausibility(bs, bc, norm_ceiling)
    L_phys = w_sign * L_sign + w_norm * L_norm

    # Amplitude regularization
    Tikh = (bs * bs + bc * bc) / 32400.0

    L_total = alpha_neural * L_neural + alpha_phys * L_phys + alpha_amp * 50.0 * Tikh
    return L_total, {
        'L_v1_anchor': L_v1, 'L_v4_anchor': L_v4,
        'L_shape': L_shape, 'L_topk': L_topk,
        'L_sign': L_sign, 'L_norm': L_norm, 'Tikh': Tikh,
        'L_neural_composite': L_neural, 'L_phys': L_phys,
    }


def sweep_subject(landscape_path, subject, family, axis, target_map, p2a_max_pt,
                  alpha_neural=0.7):
    """Sweep one (subject, alpha_neural) configuration."""
    with open(landscape_path) as f:
        d = json.load(f)
    cells = d['cells']
    vuln_obs = np.array(d['vuln_cvd'])

    anchor_bs = V1_DELTA_RDM[subject][0]
    anchor_bc = NEURAL_ANCHORS[subject]['V4'][1]

    alpha_phys = (1 - alpha_neural) * 0.67   # 2/3 of remainder to phys
    alpha_amp  = (1 - alpha_neural) * 0.33   # 1/3 to amplitude

    L_vals = []
    comps = []
    for c in cells:
        L, comp = composite_loss(c, vuln_obs, anchor_bs, anchor_bc, family,
                                  alpha_neural=alpha_neural,
                                  alpha_phys=alpha_phys,
                                  alpha_amp=alpha_amp)
        L_vals.append(L)
        comps.append(comp)
    L_arr = np.array(L_vals)
    bs_arr = np.array([c['bs'] for c in cells])
    bc_arr = np.array([c['bc'] for c in cells])

    sort_key = L_arr * 1e6 + bs_arr ** 2 + bc_arr ** 2
    idx = int(np.argmin(sort_key))
    bs, bc = float(bs_arr[idx]), float(bc_arr[idx])
    p2a, ex = p2a_eval(bs, bc, axis, target_map)

    return {
        'alpha_neural': alpha_neural,
        'alpha_phys': alpha_phys, 'alpha_amp': alpha_amp,
        'anchor_bs': anchor_bs, 'anchor_bc': anchor_bc,
        'bs': bs, 'bc': bc,
        'L_min': float(L_arr[idx]),
        'p2a': p2a, 'exact': ex,
        'norm': float(np.hypot(bs, bc)),
        'dist_to_p2amax': float(np.hypot(bs - p2a_max_pt[0], bc - p2a_max_pt[1])),
        'dist_to_anchor': float(np.hypot(bs - anchor_bs, bc - anchor_bc)),
        'components_at_argmin': {k: float(v) for k, v in comps[idx].items()},
    }


def main():
    cases = [
        ('sub-08', 'deutan', 150.0,
         _THIS_DIR.parent / 'results/axis_3way/sub-08_V4_Stockman150_landscape.json',
         SUB08_ORIGINAL_HC_EQUIV),
        ('sub-09', 'protan',  16.0,
         _THIS_DIR.parent / 'results/axis_3way/sub-09_V4_Stockman16ext_landscape.json',
         SUB09_ORIGINAL_HC_EQUIV),
    ]

    alpha_neurals = [0.3, 0.5, 0.7, 0.9]  # include 0.3 for parity with Bayesian
    all_results = {}

    print('='*120)
    print('NEURAL-PRIMARY COMPOSITE — α_neural sweep')
    print('='*120)
    print('  L = α_n·(0.3·V1ΔRDM + 0.3·V4LOCO + 0.2·V4_RDM_shape + 0.2·l_topk)')
    print('    + α_p·(0.5·weak_sign + 0.5·weak_norm_plaus)')
    print('    + α_a·50·Tikh')
    print('  α_p = (1−α_n)·0.67,  α_a = (1−α_n)·0.33')
    print()

    for sid, fam, axis, path, tmap in cases:
        print(f'\n--- {sid} ({fam}) axis={axis}° ---')
        print(f'  V1ΔRDM β_s anchor = {V1_DELTA_RDM[sid][0]}°')
        print(f'  V4LOCO β_c anchor = {NEURAL_ANCHORS[sid]["V4"][1]}°')
        print(f'  P2a-max target    = {P2A_MAX[sid]}')
        print(f'  Bayesian BEST     = {BAYESIAN_BEST[sid]}')
        print(f'  {"α_n":>5s}  {"argmin":<14s}  {"P2a":>5s}  {"exact":>5s}  '
              f'{"|β|":>5s}  {"d→max":>6s}  {"d→anchor":>9s}')
        subj_rows = []
        for an in alpha_neurals:
            r = sweep_subject(path, sid, fam, axis, tmap, P2A_MAX[sid], alpha_neural=an)
            print(f'  {an:>5.2f}  ({r["bs"]:>3.0f},{r["bc"]:>+4.0f})       '
                  f'{r["p2a"]:>5.3f}  {r["exact"]:>3d}/8  {r["norm"]:>5.1f}  '
                  f'{r["dist_to_p2amax"]:>6.1f}  {r["dist_to_anchor"]:>9.1f}')
            subj_rows.append(r)
        all_results[sid] = subj_rows

    # ---- Three-model comparison table ----
    print('\n' + '='*120)
    print('THREE-MODEL COMPARISON — Bayesian / Neural-primary / P2a-max oracle')
    print('='*120)

    P2A_MAX_VAL = {  # external P2a-max
        'sub-08': 0.613, 'sub-09': 0.950,
    }
    BAYESIAN_P2A = {'sub-08': 0.550, 'sub-09': 0.887}

    for sid in ['sub-08', 'sub-09']:
        np07 = all_results[sid][2]  # α_n=0.7
        print(f'\n  {sid} ({"deutan" if sid == "sub-08" else "protan"}):')
        print(f'    Model 1 (Bayesian α=0.3):      ({BAYESIAN_BEST[sid][0]:>3.0f},{BAYESIAN_BEST[sid][1]:>+4.0f})  '
              f'P2a={BAYESIAN_P2A[sid]:.3f}  literature-led')
        print(f'    Model 2 (Neural-primary α=0.7): ({np07["bs"]:>3.0f},{np07["bc"]:>+4.0f})  '
              f'P2a={np07["p2a"]:.3f}  neural-led')
        print(f'    Model 3 (P2a-max oracle):       ({P2A_MAX[sid][0]:>3.0f},{P2A_MAX[sid][1]:>+4.0f})  '
              f'P2a={P2A_MAX_VAL[sid]:.3f}  behavioral target (NOT in any loss)')

        # Dissociation map
        conv = 'CONVERGE' if np07['dist_to_p2amax'] < 10 else 'DIVERGE'
        print(f'    → Neural-primary {conv} with P2a-max '
              f'(dist={np07["dist_to_p2amax"]:.1f}°)')

    # Save
    with open(OUT / 'neural_primary_results.json', 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f'\nWrote {OUT / "neural_primary_results.json"}')


if __name__ == '__main__':
    main()
