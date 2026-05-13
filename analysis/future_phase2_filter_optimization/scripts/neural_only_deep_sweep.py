"""neural_only_deep_sweep.py — Deep, multi-variant neural-only loss exploration.

Goal: identify a loss using ONLY neural data that
  (1) lands close to P2a-max,
  (2) recovers literature anchors (Emery β_s≈21.4°, Tregillus ||β||≈28°, Brettel sign),
  (3) is logically valid (each component traceable to a neural source).

Neural sources available:
  - V4 landscape per cell: vuln_sim (8-D), l_ccc, l_topk, delta_theta
  - V4 vuln_cvd (8-D): observed CVD vulnerability
  - V1 LOCO 2-comp fit: (β_s, β_c) anchor
  - V4 LOCO 2-comp fit: (β_s, β_c) anchor  (= CANONICAL §3 filter)

External known points (NOT used in loss, only for evaluation):
  - P2a-max: sub-08 (26, +34), sub-09 (24, -20)
  - Bayesian BEST: sub-08 (22, +18), sub-09 (22, -16)
  - Canonical §3: sub-08 (38, -14), sub-09 (6, -22)
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
import numpy as np
from scipy.stats import pearsonr, spearmanr

_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR))

from phase3_candidate_analysis_v2 import hc_name, hc_match_score, SUB08_ORIGINAL_HC_EQUIV
from fixedW_onlyTest_p2a_ranking import SUB09_ORIGINAL_HC_EQUIV

OUT = _THIS_DIR.parent / 'results' / 'neural_only_deep'
OUT.mkdir(parents=True, exist_ok=True)

HUE_8 = [0, 45, 90, 135, 180, 225, 270, 315]
TIKH_NORM = 32400.0

# Literature anchors (for EVALUATION only — never enters loss)
EMERY_BETA_S = 21.4
TREGILLUS_NORM = EMERY_BETA_S * 1.3
BRETTEL_SIGN = {'deutan': +1, 'protan': -1}

# Neural anchors from 2-component LOCO fits (results/fits/phase_a_2component/)
NEURAL_ANCHORS = {
    'sub-08': {
        'V1': (50.0, -14.0),   # p=0.001, spearman=0.93
        'V4': (38.0, -14.0),   # p=0.004, spearman=0.88 (canonical §3)
    },
    'sub-09': {
        'V1': (38.0, +22.0),   # p=0.018, spearman=0.76 — NOTE: β_c POSITIVE
        'V4': ( 6.0, -22.0),   # p=0.035, spearman=0.69 — β_c NEGATIVE
    },
}
# V1 ΔRDM bootstrap (from MEMORY — separate from LOCO 2-comp)
V1_DELTA_RDM = {
    'sub-08': (20.0, -18.0),
    'sub-09': (23.0,  +3.0),
}

# Evaluation references
P2A_MAX = {'sub-08': (26.0, +34.0), 'sub-09': (24.0, -20.0)}
BAYESIAN_BEST = {'sub-08': (22.0, +18.0), 'sub-09': (22.0, -16.0)}


def forward(theta, bs, bc, phi_c, phi_s=90.0):
    return (theta + bs * np.cos(np.radians(theta - phi_s))
                  + bc * np.cos(np.radians(theta - phi_c))) % 360.0


def p2a_eval(bs, bc, phi_c, target_map):
    total = 0.0; exact = 0
    for th in HUE_8:
        theta_cvd = forward(float(th), bs, bc, phi_c)
        pred = hc_name(theta_cvd)
        target = target_map[th]
        total += hc_match_score(pred, target)
        if pred == target: exact += 1
    return total / 8.0, exact


# ----------------------------------------------------------------------
# Loss component primitives — all neural-derived
# ----------------------------------------------------------------------
def L_pearson_rescaled(sim, obs):
    """Per-cell z-score Pearson — scale invariant. ∈ [0, 1]"""
    if np.std(sim) < 1e-10 or np.std(obs) < 1e-10:
        return 1.0
    sim_z = (sim - sim.mean()) / sim.std()
    obs_z = (obs - obs.mean()) / obs.std()
    r, _ = pearsonr(sim_z, obs_z)
    if not np.isfinite(r):
        return 1.0
    return float(1.0 - r) / 2


def L_spearman(sim, obs):
    """Rank correlation — ordering invariant."""
    if np.std(sim) < 1e-10:
        return 1.0
    r, _ = spearmanr(sim, obs)
    if not np.isfinite(r):
        return 1.0
    return float(1.0 - r) / 2


def L_rdm_cosine(sim, obs):
    """Pairwise distance cosine. Scale-invariant."""
    n = len(sim)
    iu = np.triu_indices(n, k=1)
    rdm_sim = np.abs(sim[:, None] - sim[None, :])[iu]
    rdm_obs = np.abs(obs[:, None] - obs[None, :])[iu]
    if np.linalg.norm(rdm_sim) < 1e-10 or np.linalg.norm(rdm_obs) < 1e-10:
        return 1.0
    cos = np.dot(rdm_sim, rdm_obs) / (np.linalg.norm(rdm_sim) * np.linalg.norm(rdm_obs))
    return float(1.0 - cos) / 2


def L_anchor(bs, bc, target_bs, target_bc, scale=15.0):
    """Quadratic distance to a (β_s, β_c) anchor point."""
    return ((bs - target_bs) / scale) ** 2 + ((bc - target_bc) / scale) ** 2


def L_neural_sign(bc, sign_observed, scale=50.0):
    """Penalize β_c that has opposite sign from observed neural β_c."""
    if sign_observed > 0:
        return max(0.0, -bc / scale) ** 2  # penalize β_c<0
    else:
        return max(0.0,  bc / scale) ** 2  # penalize β_c>0


# ----------------------------------------------------------------------
# Loss variants — each is a function (cell, ctx) -> scalar
# ----------------------------------------------------------------------
def make_variants(subject, family):
    v1_bs, v1_bc = NEURAL_ANCHORS[subject]['V1']
    v4_bs, v4_bc = NEURAL_ANCHORS[subject]['V4']
    v1r_bs, v1r_bc = V1_DELTA_RDM[subject]

    variants = {}

    # Single-ROI anchor variants
    variants['N1_V4_anchor_only'] = lambda c, vc: L_anchor(
        c['bs'], c['bc'], v4_bs, v4_bc, scale=15.0)
    variants['N2_V1_anchor_only'] = lambda c, vc: L_anchor(
        c['bs'], c['bc'], v1_bs, v1_bc, scale=15.0)
    variants['N3_V1ΔRDM_anchor_only'] = lambda c, vc: L_anchor(
        c['bs'], c['bc'], v1r_bs, v1r_bc, scale=15.0)

    # Cross-ROI consensus
    variants['N4_V1V4_consensus_mean'] = lambda c, vc: L_anchor(
        c['bs'], c['bc'],
        (v1_bs + v4_bs) / 2, (v1_bc + v4_bc) / 2, scale=15.0)

    # Hierarchical: V1 → β_s (cone-driven), V4 → β_c (cortical opponent)
    variants['N5_V1βs_V4βc_hierarchy'] = lambda c, vc: L_anchor(
        c['bs'], c['bc'], v1_bs, v4_bc, scale=15.0)
    # Alternative hierarchical with V1 ΔRDM β_s
    variants['N6_V1ΔRDMβs_V4βc'] = lambda c, vc: L_anchor(
        c['bs'], c['bc'], v1r_bs, v4_bc, scale=15.0)

    # Scale-invariant landscape fits (no anchor, pure shape matching)
    variants['N7_pearson_rescaled_V4'] = lambda c, vc: L_pearson_rescaled(
        np.array(c['vuln_sim']), vc)
    variants['N8_spearman_V4'] = lambda c, vc: L_spearman(
        np.array(c['vuln_sim']), vc)
    variants['N9_rdm_cosine_V4'] = lambda c, vc: L_rdm_cosine(
        np.array(c['vuln_sim']), vc)

    # Pure shape + neural norm anchor (Tikh from V1+V4 mean amplitude)
    target_norm = (np.hypot(v1_bs, v1_bc) + np.hypot(v4_bs, v4_bc)) / 2
    variants['N10_pearson + neural_norm'] = lambda c, vc, tn=target_norm: (
        L_pearson_rescaled(np.array(c['vuln_sim']), vc)
        + ((np.hypot(c['bs'], c['bc']) - tn) / 20.0) ** 2 * 0.5)

    # Anchor + scale-invariant fit hybrid
    variants['N11_V4anchor + pearson'] = lambda c, vc: (
        L_anchor(c['bs'], c['bc'], v4_bs, v4_bc, scale=15.0)
        + 1.0 * L_pearson_rescaled(np.array(c['vuln_sim']), vc))

    variants['N12_V1V4_consensus + rdm_cos'] = lambda c, vc: (
        L_anchor(c['bs'], c['bc'],
                 (v1_bs + v4_bs) / 2, (v1_bc + v4_bc) / 2, scale=15.0)
        + 1.0 * L_rdm_cosine(np.array(c['vuln_sim']), vc))

    # Disagreement-aware: if V1, V4 disagree on β_c sign, average is unreliable
    # → fall back to V4 anchor (since V4 is the LOCO target)
    sign_agree = (v1_bc * v4_bc) > 0
    if sign_agree:
        # Trust consensus
        variants['N13_consensus_or_V4(disagree)'] = lambda c, vc: L_anchor(
            c['bs'], c['bc'],
            (v1_bs + v4_bs) / 2, (v1_bc + v4_bc) / 2, scale=15.0)
    else:
        variants['N13_consensus_or_V4(disagree)'] = lambda c, vc: L_anchor(
            c['bs'], c['bc'], v4_bs, v4_bc, scale=15.0)

    # Bayesian-style but anchor from V1 ΔRDM (neural Emery analog) instead of literature 21.4
    variants['N14_V1ΔRDM_βs + V4βc + rdm_cos'] = lambda c, vc: (
        ((c['bs'] - v1r_bs) / 10.0) ** 2
        + ((c['bc'] - v4_bc) / 15.0) ** 2
        + 0.5 * L_rdm_cosine(np.array(c['vuln_sim']), vc))

    # Pearson + L_ccc original (control)
    variants['N15_l_ccc_only'] = lambda c, vc: c['l_ccc']

    return variants


# ----------------------------------------------------------------------
# Evaluation: literature compatibility scoring
# ----------------------------------------------------------------------
def literature_score(bs, bc, family):
    """Compute how well a (β_s, β_c) point matches literature anchors."""
    emery_dev = abs(bs - EMERY_BETA_S)
    norm = np.hypot(bs, bc)
    tregillus_dev = abs(norm - TREGILLUS_NORM)
    brettel_sign_ok = (bc * BRETTEL_SIGN[family]) > 0 if abs(bc) > 1 else None
    return {
        'emery_dev': float(emery_dev),
        'tregillus_dev': float(tregillus_dev),
        'brettel_sign_ok': brettel_sign_ok,
        'norm': float(norm),
    }


# ----------------------------------------------------------------------
# Main sweep
# ----------------------------------------------------------------------
def sweep_subject(landscape_path, subject, family, axis, target_map, p2a_max_pt):
    with open(landscape_path) as f:
        d = json.load(f)
    cells = d['cells']
    vuln_obs = np.array(d['vuln_cvd'])

    variants = make_variants(subject, family)
    results = {}

    for vname, vfn in variants.items():
        L_vals = np.array([vfn(c, vuln_obs) for c in cells])
        # Argmin (with Tikh-like tie-breaker on amplitude)
        bs_arr = np.array([c['bs'] for c in cells])
        bc_arr = np.array([c['bc'] for c in cells])
        sort_key = L_vals * 1e6 + (bs_arr**2 + bc_arr**2)
        idx = np.argmin(sort_key)
        best = cells[idx]
        bs, bc = best['bs'], best['bc']
        p2a, ex = p2a_eval(bs, bc, axis, target_map)
        lit = literature_score(bs, bc, family)
        results[vname] = {
            'bs': bs, 'bc': bc, 'L_min': float(L_vals[idx]),
            'p2a': p2a, 'exact': ex,
            'dist_to_p2amax': float(np.hypot(bs - p2a_max_pt[0], bc - p2a_max_pt[1])),
            'dist_to_canonical': float(np.hypot(
                bs - NEURAL_ANCHORS[subject]['V4'][0],
                bc - NEURAL_ANCHORS[subject]['V4'][1])),
            'dist_to_bayesian': float(np.hypot(
                bs - BAYESIAN_BEST[subject][0],
                bc - BAYESIAN_BEST[subject][1])),
            **lit,
        }
    return results


def main():
    cases = [
        ('sub-08', 'deutan', 150.0,
         'results/axis_3way/sub-08_V4_Stockman150_landscape.json',
         SUB08_ORIGINAL_HC_EQUIV),
        ('sub-09', 'protan',  16.0,
         'results/axis_3way/sub-09_V4_Stockman16ext_landscape.json',
         SUB09_ORIGINAL_HC_EQUIV),
    ]

    all_results = {}
    for sid, fam, axis, lp, tmap in cases:
        if not Path(lp).exists():
            print(f'SKIP {lp}'); continue
        p2a_pt = P2A_MAX[sid]
        print(f'\n{"="*108}')
        print(f'{sid} ({fam}) axis={axis}° | P2a-max={p2a_pt} | Canonical={NEURAL_ANCHORS[sid]["V4"]}')
        print(f'{"="*108}')
        print(f'  {"variant":<32s}  {"argmin":<12s}  {"P2a":>5s}  {"ex":>3s}  '
              f'{"d→p2a":>6s}  {"d→can":>6s}  {"d→bay":>6s}  '
              f'{"|β|":>5s}  {"Em-dev":>6s}  {"Tr-dev":>6s}  Brettel')
        results = sweep_subject(lp, sid, fam, axis, tmap, p2a_pt)
        for vn, r in results.items():
            bsign = 'OK' if r['brettel_sign_ok'] is True else (
                'FAIL' if r['brettel_sign_ok'] is False else 'n/a')
            print(f'  {vn:<32s}  ({r["bs"]:>3.0f},{r["bc"]:>+4.0f})    '
                  f'{r["p2a"]:>5.3f}  {r["exact"]:>2d}/8  '
                  f'{r["dist_to_p2amax"]:>6.1f}  {r["dist_to_canonical"]:>6.1f}  '
                  f'{r["dist_to_bayesian"]:>6.1f}  '
                  f'{r["norm"]:>5.1f}  {r["emery_dev"]:>6.1f}  {r["tregillus_dev"]:>6.1f}  '
                  f'{bsign}')
        all_results[sid] = results

    out_path = OUT / 'neural_only_deep_results.json'
    with open(out_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f'\nWrote {out_path}')


if __name__ == '__main__':
    main()
