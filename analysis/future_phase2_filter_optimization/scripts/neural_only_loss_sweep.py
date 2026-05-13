"""neural_only_loss_sweep.py — Neural data + literature anchors only loss.

No raw_behav target. No P2a in loss. Evaluation by P2a (held-out).

Loss candidates:
  A. Rescaled Pearson — solves vuln_sim 0-clustering by per-cell standardization
  B. Emery anchor — β_s ≈ 21.4° (Emery 2021 B-Y rotation toward S-axis)
  C. Brettel sign — β_c sign constraint per family (protan / deutan)
  D. RDM match — pairwise distance, scale-invariant
  E. Composite — rescaled + Emery + Brettel
  F. Sign-aware (already tested) — kept for comparison

각 cell에 대해 loss 값 → argmin → 그 (β_s, β_c)에서 P2a 평가 (외부 metric).
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import pearsonr, spearmanr

_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR))

from phase3_candidate_analysis_v2 import (
    hc_name, hc_match_score, SUB08_ORIGINAL_HC_EQUIV,
)
from fixedW_onlyTest_p2a_ranking import SUB09_ORIGINAL_HC_EQUIV

OUT = _THIS_DIR.parent / 'results' / 'neural_only_loss'
OUT.mkdir(parents=True, exist_ok=True)

HUE_8 = [0, 45, 90, 135, 180, 225, 270, 315]
TIKH_NORM = 32400.0

# Literature anchors
EMERY_BETA_S = 21.4       # Emery 2021 NT→AT B-Y rotation toward S-axis
TREGILLUS_OVERSHOOT = 1.3  # 20-40% overshoot, midpoint
BRETTEL_SIGN_EXPECTED = {  # under OLD axis convention (150° for both)
    'deutan': +1,           # M-cone loss → β_c > 0 expected (toward red)
    'protan': -1,           # L-cone loss → β_c < 0 expected (toward green)
}


def forward(theta, bs, bc, phi_c, phi_s=90.0):
    return (theta + bs * np.cos(np.radians(theta - phi_s))
                  + bc * np.cos(np.radians(theta - phi_c))) % 360.0


def p2a_eval(bs, bc, phi_c, target_map):
    """External evaluation — NOT used in loss."""
    total = 0.0; exact = 0
    for theta in HUE_8:
        theta_cvd = forward(float(theta), bs, bc, phi_c)
        pred = hc_name(theta_cvd)
        target = target_map[theta]
        total += hc_match_score(pred, target)
        if pred == target: exact += 1
    return total / 8.0, exact


# ----------------------------------------------------------------------
# Loss definitions (Neural data only + literature anchors)
# ----------------------------------------------------------------------
def L_rescaled_pearson(sim, obs):
    """Per-cell standardization → Pearson correlation. Solves 0-clustering."""
    if np.std(sim) < 1e-10 or np.std(obs) < 1e-10:
        return 1.0
    sim_z = (sim - sim.mean()) / sim.std()
    obs_z = (obs - obs.mean()) / obs.std()
    r, _ = pearsonr(sim_z, obs_z)
    if not np.isfinite(r):
        return 1.0
    return float(1.0 - r) / 2  # ∈ [0, 1]


def L_rdm_match(sim, obs):
    """Pairwise distance RDM cosine — scale invariant."""
    n = len(sim)
    # Use rank values (most stable across cells)
    sim_r = np.argsort(np.argsort(sim))
    obs_r = np.argsort(np.argsort(obs))
    rdm_sim = np.array([[abs(sim_r[i] - sim_r[j]) for j in range(n)] for i in range(n)])
    rdm_obs = np.array([[abs(obs_r[i] - obs_r[j]) for j in range(n)] for i in range(n)])
    # Upper triangle
    iu = np.triu_indices(n, k=1)
    v_sim = rdm_sim[iu]; v_obs = rdm_obs[iu]
    if np.std(v_sim) < 1e-10 or np.std(v_obs) < 1e-10:
        return 1.0
    cos_val = np.dot(v_sim, v_obs) / (np.linalg.norm(v_sim) * np.linalg.norm(v_obs))
    return float(1.0 - cos_val) / 2


def L_basic_ccc(l_ccc_cached, **kwargs):
    return l_ccc_cached


def emery_penalty(bs, bc):
    """Emery anchor: β_s ≈ 21.4°. Soft prior on amplitude."""
    return ((bs - EMERY_BETA_S) / 10.0) ** 2


def brettel_sign_penalty(bs, bc, family):
    """Brettel sign expectation: deutan β_c>0, protan β_c<0."""
    sign_exp = BRETTEL_SIGN_EXPECTED[family]
    return max(0.0, -bc * sign_exp / 50.0) ** 2


def tregillus_penalty(bs, bc):
    """Tregillus 20-40% overshoot — moderate amplitude (~25-30°)."""
    norm = np.hypot(bs, bc)
    target = EMERY_BETA_S * TREGILLUS_OVERSHOOT  # ≈ 28°
    return ((norm - target) / 15.0) ** 2


def sweep_one_landscape(path, axis_label, axis, family, target_map, p2amax_bs, p2amax_bc):
    with open(path) as f:
        d = json.load(f)
    cells = d['cells']
    vuln_cvd = np.array(d['vuln_cvd'])

    results = {}

    def evaluate_loss(loss_label, loss_per_cell):
        best_L = np.inf; best = None; tied = []
        for c, L_val in zip(cells, loss_per_cell):
            if L_val < best_L - 1e-9:
                best_L = L_val; best = c; tied = [c]
            elif abs(L_val - best_L) < 1e-9:
                tied.append(c)
        if len(tied) > 1:
            tied.sort(key=lambda cc: cc['bs']**2 + cc['bc']**2)
            best = tied[0]
        bs, bc = best['bs'], best['bc']
        p2a, exact = p2a_eval(bs, bc, axis, target_map)
        dist = float(np.hypot(bs - p2amax_bs, bc - p2amax_bc))
        results[loss_label] = {
            'bs': bs, 'bc': bc, 'L_min': float(best_L),
            'p2a': p2a, 'exact': exact, 'dist_to_p2amax': dist,
            'n_tied': len(tied),
        }

    # Compute per-cell base loss components
    L_ccc_arr = np.array([c['l_ccc'] for c in cells])
    L_topk_arr = np.array([c['l_topk'] for c in cells])
    Tikh_arr = np.array([c['tikh'] for c in cells])
    bs_arr = np.array([c['bs'] for c in cells])
    bc_arr = np.array([c['bc'] for c in cells])

    L_rescaled_arr = np.array([L_rescaled_pearson(np.array(c['vuln_sim']), vuln_cvd)
                                for c in cells])
    L_rdm_arr = np.array([L_rdm_match(np.array(c['vuln_sim']), vuln_cvd) for c in cells])
    L_emery_arr = np.array([emery_penalty(c['bs'], c['bc']) for c in cells])
    L_brettel_arr = np.array([brettel_sign_penalty(c['bs'], c['bc'], family)
                               for c in cells])
    L_tregillus_arr = np.array([tregillus_penalty(c['bs'], c['bc']) for c in cells])

    # Evaluate individual + composites
    evaluate_loss('A.  L_rescaled_pearson',     L_rescaled_arr)
    evaluate_loss('A2. L_rescaled + 0.1 Tikh',  L_rescaled_arr + 0.1*Tikh_arr*50)
    evaluate_loss('A3. L_rescaled + 0.5 Tikh',  L_rescaled_arr + 0.5*Tikh_arr*50)

    evaluate_loss('B.  L_ccc + Emery anchor',   L_ccc_arr + 0.5*L_emery_arr)
    evaluate_loss('B2. L_ccc + Emery (heavy)',  L_ccc_arr + 2.0*L_emery_arr)
    evaluate_loss('B3. Emery alone',            L_emery_arr)
    evaluate_loss('B4. Tregillus alone',        L_tregillus_arr)

    evaluate_loss('C.  L_ccc + Brettel sign',   L_ccc_arr + 0.5*L_brettel_arr)
    evaluate_loss('C2. Brettel + Emery',        0.5*L_emery_arr + 0.5*L_brettel_arr)
    evaluate_loss('C3. Brettel alone',          L_brettel_arr)

    evaluate_loss('D.  L_rdm',                  L_rdm_arr)
    evaluate_loss('D2. L_rdm + 0.5 Tikh',       L_rdm_arr + 0.5*Tikh_arr*50)
    evaluate_loss('D3. L_rdm + Brettel',        L_rdm_arr + 0.5*L_brettel_arr)

    evaluate_loss('E.  rescaled + Emery + Brettel + Tikh',
                  L_rescaled_arr + 0.3*L_emery_arr + 0.3*L_brettel_arr + 0.1*Tikh_arr*50)
    evaluate_loss('E2. CCC + Emery + Brettel + Tikh',
                  L_ccc_arr + 0.3*L_emery_arr + 0.3*L_brettel_arr + 0.1*Tikh_arr*50)

    return results


def main():
    cases = [
        ('08', 'Stockman150', 150.0, 'deutan',
         'results/axis_3way/sub-08_V4_Stockman150_landscape.json',
         26, +34, SUB08_ORIGINAL_HC_EQUIV),
        ('09', 'Stockman16',   16.0, 'protan',
         'results/axis_3way/sub-09_V4_Stockman16_landscape.json',
         24, -20, SUB09_ORIGINAL_HC_EQUIV),
        ('09', 'Stockman16ext', 16.0, 'protan',
         'results/axis_3way/sub-09_V4_Stockman16ext_landscape.json',
         24, -20, SUB09_ORIGINAL_HC_EQUIV),
    ]

    all_results = {}
    for sid, axis_label, axis, fam, p, pbs, pbc, tmap in cases:
        path = Path(p)
        if not path.exists():
            print(f'SKIP {p}'); continue
        print(f'\n{"="*92}')
        print(f'sub-{sid} ({fam}) axis={axis_label} (θ_conf={axis}°)  '
              f'P2a-max=({pbs}, {pbc:+d})')
        print(f'{"="*92}')
        results = sweep_one_landscape(path, axis_label, axis, fam, tmap, pbs, pbc)
        all_results[f'sub-{sid}/{axis_label}'] = results

        print(f'  {"loss":<45s}  {"argmin":<10s}  {"L":>7s}  '
              f'{"P2a":>5s}  {"exact":>5s}  {"dist":>5s}  {"tied":>4s}')
        for loss_name, r in results.items():
            print(f'  {loss_name:<45s}  ({r["bs"]:>2.0f},{r["bc"]:+3.0f})    '
                  f'{r["L_min"]:>7.3f}  {r["p2a"]:>5.3f}  {r["exact"]:>3d}/8  '
                  f'{r["dist_to_p2amax"]:>5.1f}  {r["n_tied"]:>4d}')

    with open(OUT / 'neural_only_sweep.json', 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f'\nWrote {OUT / "neural_only_sweep.json"}')


if __name__ == '__main__':
    main()
