"""cvd_specificity_alternatives.py — comprehensive CVD specificity verification.

3 independent tests, all within-subject (no HC pool dependence, no sub-10):

Test A: Leave-one-color-out (LOCO of LOCO) argmin stability
  - For each held-out color k: recompute argmin using only 7 colors in loss
  - 8 argmins per (subject, loss) → distribution of (β_s, β_c)
  - Tight cluster = real signal; scattered = fragile fit
  - Compare CVD argmin σ vs HC LOO argmin σ

Test B: Per-color residual concentration at BEST argmin
  - residual[c] = |vuln_obs[c] - vuln_sim[c]| at BEST argmin
  - Concentration metric: gini coefficient + top-3 residual fraction
  - For deutan sub-08: residuals on signature colors (c2/c3/c7 = top-3 most negative)?
  - For HC: residuals spread evenly?

Test C: Cross-loss argmin sign consistency
  - Two losses: CCC alone vs CCC+l_topk
  - For each subject, do both losses give same β_c sign family?
  - CVD consistent → structural signal
  - HC LOO scattered → random walk

References:
  - Hsu, Borst, Theunissen (2004) — noise ceiling / reliability
  - Schoppe et al. (2016) — encoding-model reliability ceiling
  - Raue et al. (2009) — identifiability via profile likelihood (motif)

Output: results/CANDIDATE/specificity_alternatives/
"""
from __future__ import annotations
import json
import sys
import csv
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
from scipy.stats import pearsonr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR))

from old_formula_refit import load_cvd_loco_target

_PHASE2 = _THIS_DIR.parent
SRC_CVD = _PHASE2 / 'results' / 'old_formula'
SRC_HC = _PHASE2 / 'results' / 'fits' / 'phase_a_2component_hc_sanity'
OUT = _PHASE2 / 'results' / 'CANDIDATE' / 'specificity_alternatives'
OUT.mkdir(parents=True, exist_ok=True)

K_TOPK = 3
TIKH_NORM = 32400.0
LAMBDA_TOPK = 0.5

SUBJECTS = {
    'cvd': {
        '08': {'cvd_type': 'deutan', 'color': '#E07B2C'},
        '09': {'cvd_type': 'protan', 'color': '#2D8E8B'},
    },
    'hc': {hc: {'cvd_type': 'HC', 'color': '#888888'} for hc in
           ['01', '02', '03', '04', '05', '06']},
}

# BEST argmins (current state)
BEST = {
    '08': {'ccc_alone': (16.0, 40.0), 'ccc_ltopk': (44.0, 28.0)},
    '09': {'ccc_alone': (30.0, 46.0), 'ccc_ltopk': (30.0, 46.0)},
}


# ---------- loss components ----------
def ccc_value(sim, obs):
    sim = np.asarray(sim); obs = np.asarray(obs)
    if np.std(sim) < 1e-10 or np.std(obs) < 1e-10:
        return 0.0
    r, _ = pearsonr(sim, obs)
    if not np.isfinite(r):
        return 0.0
    msim = sim.mean(); mobs = obs.mean()
    ssim = sim.std(); sobs = obs.std()
    denom = ssim**2 + sobs**2 + (msim - mobs)**2
    if denom < 1e-10:
        return 0.0
    return 2.0 * r * ssim * sobs / denom


def l_topk_jaccard(sim, obs, K=K_TOPK):
    s = np.asarray(sim); o = np.asarray(obs)
    top_s = set(np.argsort(s)[:K].tolist())
    top_o = set(np.argsort(o)[:K].tolist())
    inter = len(top_s & top_o); union = len(top_s | top_o)
    return 1.0 - (inter / union)


def compute_loss_subset(vuln_sim, vuln_obs, tikh, loss='ccc_ltopk', subset_idx=None):
    """Compute loss using only a subset of color indices (for LOSO).

    vuln_sim, vuln_obs: (8,) arrays
    subset_idx: list of indices to use (e.g., [0,1,2,4,5,6,7] = leave c3 out)
                If None, use all 8.
    """
    if subset_idx is None:
        sim_sub = vuln_sim; obs_sub = vuln_obs
    else:
        sim_sub = np.asarray(vuln_sim)[subset_idx]
        obs_sub = np.asarray(vuln_obs)[subset_idx]
    ccc = ccc_value(sim_sub, obs_sub)
    l_ccc = (1.0 - ccc) / 2.0
    if loss == 'ccc_alone':
        return l_ccc + 0.1 * tikh
    # ccc + l_topk — note K is fixed at K_TOPK; if subset size < K, fallback
    K = min(K_TOPK, len(sim_sub) - 1)
    if K < 1:
        return l_ccc + 0.1 * tikh
    top_s = set(np.argsort(sim_sub)[:K].tolist())
    top_o = set(np.argsort(obs_sub)[:K].tolist())
    inter = len(top_s & top_o); union = len(top_s | top_o)
    l_topk = 1.0 - (inter / union) if union > 0 else 0.0
    return l_ccc + LAMBDA_TOPK * l_topk + 0.1 * tikh


# ---------- data loading ----------
def load_cvd_landscape(sid):
    fn = SRC_CVD / f'sub-{sid}_V4_V4ccc_landscape.json'
    ls = json.load(open(fn))
    return ls if isinstance(ls, list) else ls.get('cells', ls)


def load_hc_landscape(sid):
    fn = SRC_HC / f'sub-{sid}_V4_2component.json'
    d = json.load(open(fn))
    # HC sanity landscape format differs: cells have 'params', 'vuln_sim', etc.
    cells = []
    for c in d['landscape']:
        cells.append({
            'bs': c['params'][0], 'bc': c['params'][1],
            'vuln_sim': c['vuln_sim'],
            'l_smooth': c['l_smooth'],
            'spearman_r': c['spearman_r'],
        })
    return cells


def get_vuln_obs(sid):
    """For CVD: load via load_cvd_loco_target. For HC: load same way (function works for any subject)."""
    return np.array(load_cvd_loco_target(sid, 'V4'))


# ---------- Tests ----------
def test_A_loso_argmin(sid, cells, vuln_obs, loss='ccc_ltopk', verbose=False):
    """Leave-one-color-out: 8 argmins by removing one color each time.

    Returns dict with argmin_bs (8,), argmin_bc (8,), Δ_L (8,)
    and aggregate stability metric.
    """
    # Precompute cell arrays
    bss = np.array([c['bs'] for c in cells])
    bcs = np.array([c['bc'] for c in cells])
    tikhs = (bss**2 + bcs**2) / TIKH_NORM
    vuln_sims = np.array([c['vuln_sim'] for c in cells])  # (N, 8)

    argmin_bs = np.zeros(8); argmin_bc = np.zeros(8); delta_L = np.zeros(8)
    for k in range(8):
        subset = [i for i in range(8) if i != k]
        L_per_cell = np.array([
            compute_loss_subset(vuln_sims[c], vuln_obs, tikhs[c], loss, subset)
            for c in range(len(cells))
        ])
        L_baseline = L_per_cell[(bss == 0) & (bcs == 0)][0] if any((bss==0)&(bcs==0)) else L_per_cell.mean()
        argmin_idx = np.argmin(L_per_cell)
        argmin_bs[k] = bss[argmin_idx]
        argmin_bc[k] = bcs[argmin_idx]
        delta_L[k] = L_baseline - L_per_cell[argmin_idx]
        if verbose:
            print(f'    LOSO color={k}: argmin=({argmin_bs[k]:+.0f},{argmin_bc[k]:+.0f}) Δ_L={delta_L[k]:.3f}')

    # Stability metrics
    std_bs = float(np.std(argmin_bs, ddof=1))
    std_bc = float(np.std(argmin_bc, ddof=1))
    # Fraction within ±5° of median argmin
    med_bs = float(np.median(argmin_bs))
    med_bc = float(np.median(argmin_bc))
    near_median = ((np.abs(argmin_bs - med_bs) <= 5) &
                   (np.abs(argmin_bc - med_bc) <= 5)).mean()
    # Sign consistency of β_c
    bc_sign_consistent = float(((argmin_bc > 0).mean() >= 0.75) or
                               ((argmin_bc < 0).mean() >= 0.75))

    return {
        'argmin_bs': argmin_bs.tolist(),
        'argmin_bc': argmin_bc.tolist(),
        'delta_L': delta_L.tolist(),
        'std_bs': std_bs,
        'std_bc': std_bc,
        'median_bs': med_bs,
        'median_bc': med_bc,
        'fraction_near_median': float(near_median),
        'bc_sign_consistent': bool(bc_sign_consistent),
    }


def test_B_residual_concentration(cells, vuln_obs, argmin_bs, argmin_bc):
    """Find cell at given argmin, compute per-color residual."""
    # Find cell at argmin
    for c in cells:
        if abs(c['bs'] - argmin_bs) < 0.5 and abs(c['bc'] - argmin_bc) < 0.5:
            best = c
            break
    else:
        return None
    sim = np.asarray(best['vuln_sim'])
    obs = np.asarray(vuln_obs)
    res = np.abs(obs - sim)  # (8,)
    # Concentration: gini coefficient of residuals
    sorted_r = np.sort(res)
    n = len(res)
    cumsum = np.cumsum(sorted_r)
    gini = (2 * np.sum((np.arange(1, n+1)) * sorted_r) -
            (n + 1) * cumsum[-1]) / (n * cumsum[-1]) if cumsum[-1] > 0 else 0.0
    # Top-3 residual fraction
    top3_frac = float(np.sort(res)[-3:].sum() / res.sum() if res.sum() > 0 else 0.0)
    # Index of top-3 highest residual
    top3_idx = np.argsort(res)[-3:][::-1]
    return {
        'residuals': res.tolist(),
        'argmin_bs': argmin_bs, 'argmin_bc': argmin_bc,
        'gini': float(gini),
        'top3_residual_frac': top3_frac,
        'top3_residual_idx': top3_idx.tolist(),
    }


def test_C_cross_loss_consistency(cells, vuln_obs):
    """For each loss, find argmin. Return both argmins + sign consistency."""
    bss = np.array([c['bs'] for c in cells])
    bcs = np.array([c['bc'] for c in cells])
    tikhs = (bss**2 + bcs**2) / TIKH_NORM
    vuln_sims = np.array([c['vuln_sim'] for c in cells])

    argmins = {}
    for loss_name in ['ccc_alone', 'ccc_ltopk']:
        L_per_cell = np.array([
            compute_loss_subset(vuln_sims[c], vuln_obs, tikhs[c], loss_name, None)
            for c in range(len(cells))
        ])
        amin = np.argmin(L_per_cell)
        argmins[loss_name] = {'bs': float(bss[amin]), 'bc': float(bcs[amin])}

    # Sign consistency
    bc_alone = argmins['ccc_alone']['bc']
    bc_ltopk = argmins['ccc_ltopk']['bc']
    sign_consistent = (np.sign(bc_alone) == np.sign(bc_ltopk)) or (abs(bc_alone) < 1e-3) or (abs(bc_ltopk) < 1e-3)
    # Distance
    dist = float(np.hypot(argmins['ccc_alone']['bs'] - argmins['ccc_ltopk']['bs'],
                          argmins['ccc_alone']['bc'] - argmins['ccc_ltopk']['bc']))
    return {
        'ccc_alone': argmins['ccc_alone'],
        'ccc_ltopk': argmins['ccc_ltopk'],
        'bc_sign_consistent': bool(sign_consistent),
        'argmin_distance': dist,
    }


def main():
    all_results = {'cvd': {}, 'hc': {}}

    print('=== TEST A: Leave-one-color-out argmin stability ===')
    print('=== TEST B: Per-color residual concentration at BEST argmin ===')
    print('=== TEST C: Cross-loss argmin sign consistency ===')

    # CVD subjects
    for sid, info in SUBJECTS['cvd'].items():
        print(f'\n--- CVD sub-{sid} ({info["cvd_type"]}) ---')
        cells = load_cvd_landscape(sid)
        vuln_obs = get_vuln_obs(sid)

        # Test A
        test_a = {}
        for loss in ['ccc_alone', 'ccc_ltopk']:
            test_a[loss] = test_A_loso_argmin(sid, cells, vuln_obs, loss)
            r = test_a[loss]
            print(f'  Test A [{loss}]: argmin std=({r["std_bs"]:.1f}, {r["std_bc"]:.1f})  '
                  f'median=({r["median_bs"]:+.0f},{r["median_bc"]:+.0f})  '
                  f'near_median={r["fraction_near_median"]:.2f}  '
                  f'bc_sign_consistent={r["bc_sign_consistent"]}')

        # Test B at BEST argmin under ccc_ltopk
        bs_best, bc_best = BEST[sid]['ccc_ltopk']
        test_b = test_B_residual_concentration(cells, vuln_obs, bs_best, bc_best)
        if test_b:
            print(f'  Test B [argmin=({bs_best:+.0f},{bc_best:+.0f})]: '
                  f'gini={test_b["gini"]:.3f}  top3_frac={test_b["top3_residual_frac"]:.3f}  '
                  f'top3_idx={test_b["top3_residual_idx"]}')

        # Test C
        test_c = test_C_cross_loss_consistency(cells, vuln_obs)
        print(f'  Test C: alone=({test_c["ccc_alone"]["bs"]:+.0f},{test_c["ccc_alone"]["bc"]:+.0f}), '
              f'ltopk=({test_c["ccc_ltopk"]["bs"]:+.0f},{test_c["ccc_ltopk"]["bc"]:+.0f})  '
              f'sign_consistent={test_c["bc_sign_consistent"]}  dist={test_c["argmin_distance"]:.1f}°')

        all_results['cvd'][sid] = {
            'cvd_type': info['cvd_type'],
            'test_A_loso': test_a,
            'test_B_residual': test_b,
            'test_C_cross_loss': test_c,
        }

    # HC LOO subjects (for comparison)
    for sid, info in SUBJECTS['hc'].items():
        print(f'\n--- HC sub-{sid} ---')
        try:
            cells = load_hc_landscape(sid)
            vuln_obs = get_vuln_obs(sid)
        except Exception as e:
            print(f'  skip (cannot load): {e}')
            continue

        test_a = {}
        for loss in ['ccc_alone', 'ccc_ltopk']:
            test_a[loss] = test_A_loso_argmin(sid, cells, vuln_obs, loss)
            r = test_a[loss]
            print(f'  Test A [{loss}]: argmin std=({r["std_bs"]:.1f}, {r["std_bc"]:.1f})  '
                  f'near_median={r["fraction_near_median"]:.2f}  '
                  f'bc_sign_consistent={r["bc_sign_consistent"]}')

        test_c = test_C_cross_loss_consistency(cells, vuln_obs)
        print(f'  Test C: dist={test_c["argmin_distance"]:.1f}°  '
              f'sign_consistent={test_c["bc_sign_consistent"]}')

        all_results['hc'][sid] = {
            'test_A_loso': test_a,
            'test_C_cross_loss': test_c,
        }

    # Save
    out_path = OUT / 'cvd_specificity_alternatives.json'
    with open(out_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f'\nwrote {out_path}')

    # Summary CSV
    csv_path = OUT / 'cvd_specificity_alternatives_summary.csv'
    with open(csv_path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['group', 'subject', 'loss', 'test_A_std_bs', 'test_A_std_bc',
                    'test_A_near_median_frac', 'test_A_bc_sign_consistent',
                    'test_C_bc_sign_consistent', 'test_C_argmin_dist'])
        for group in ['cvd', 'hc']:
            for sid, r in all_results[group].items():
                for loss in ['ccc_alone', 'ccc_ltopk']:
                    ta = r['test_A_loso'][loss]
                    tc = r.get('test_C_cross_loss', {})
                    w.writerow([
                        group, f'sub-{sid}', loss,
                        round(ta['std_bs'], 2), round(ta['std_bc'], 2),
                        round(ta['fraction_near_median'], 3),
                        ta['bc_sign_consistent'],
                        tc.get('bc_sign_consistent', ''),
                        round(tc.get('argmin_distance', 0), 2),
                    ])
    print(f'wrote {csv_path}')

    # === Comparative analysis ===
    print('\n' + '=' * 60)
    print('COMPARATIVE ANALYSIS — CVD vs HC')
    print('=' * 60)

    print('\nTest A (LOSO argmin stability):')
    print(f'{"Group":<8}{"Subj":<10}{"Loss":<14}{"std_bs":<10}{"std_bc":<10}{"near_med":<10}{"bc_sign":<10}')
    for group in ['cvd', 'hc']:
        for sid, r in all_results[group].items():
            for loss in ['ccc_alone', 'ccc_ltopk']:
                ta = r['test_A_loso'][loss]
                print(f'{group:<8}sub-{sid:<6}{loss:<14}{ta["std_bs"]:<10.1f}{ta["std_bc"]:<10.1f}'
                      f'{ta["fraction_near_median"]:<10.2f}{str(ta["bc_sign_consistent"]):<10}')

    print('\nTest C (cross-loss argmin convergence):')
    print(f'{"Group":<8}{"Subj":<10}{"dist (°)":<12}{"bc_sign_consistent":<22}')
    for group in ['cvd', 'hc']:
        for sid, r in all_results[group].items():
            tc = r.get('test_C_cross_loss', {})
            print(f'{group:<8}sub-{sid:<6}{tc.get("argmin_distance", 0):<12.1f}'
                  f'{str(tc.get("bc_sign_consistent", "")):<22}')


if __name__ == '__main__':
    main()
