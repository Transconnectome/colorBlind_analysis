#!/usr/bin/env python3
"""cycle7_blend_wspearman.py — Plan 04 Cycle 7 Task B.

Weighted Spearman + L_set blend.
  rho_w = weighted Pearson on ranks; w_i = max(-vuln_cvd_i, 0)
  L_wSpear = 1 - rho_w
  L_B = alpha * L_set + beta * L_wSpear
  alpha, beta in {0, 0.25, 0.5, 0.75, 1.0}

Reuses Cycle 1 landscape (l_topk_jaccard) for L_set; computes wSpear from
landscape's spearman_r is not enough -- need raw vuln_sim per grid point.
Workaround: compute weighted Spearman on (vuln_sim, vuln_cvd) where the
landscape provides best (bs, bc) per metric. We instead approximate using
vuln_target reload + reuse of FE pipeline.

Simpler approach: at the *best (bs, bc) for L_set* of each cell, compute
weighted Spearman rho_w. This binds wSpear evaluation to the L_set's best
point (consistent with the dual-criterion logic).
"""
import json
import sys
import numpy as np
from pathlib import Path

ROOT = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/future_phase2_filter_optimization')
RES_LAND = ROOT / 'results/cycles'
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'scripts' / 'older_cycles/cycle_loss_redesign'))
PROJ = ROOT.parent.parent
FWD = PROJ / 'analysis' / 'future_phase1_forward_model' / 'scripts'
sys.path.insert(0, str(FWD))

from utils_forward_model import (HC_SUBJECTS, N_CHANNELS, HUE_ANGLES,
                                  load_amplitudes, create_basis_full)
from step1_fit_loco_v2 import (precompute_hc_W, simulate_mean_hc_wfixed,
                                load_cvd_loco_target)
from loss_redesign_smoke import get_2component_design

LOCAL_DATA = (PROJ / 'analysis' / 'phase1_procrustes_decoding' / 'results'
              / 'visualization' / 'full_dataset_C010_with_residuals')

ROIS = ['V1', 'V2', 'V4']
HC = ['01', '02', '03', '04', '05', '06']
CVD = ['08', '09']
SANITY = ['10']
CVD_FAM = {'08': 'deutan', '09': 'protan', '10': 'deutan'}

_bs = np.arange(0.0, 81.0, 2.0)
_bc = np.arange(-60.0, 61.0, 2.0)
_BS, _BC = np.meshgrid(_bs, _bc, indexing='ij')
NORM_GRID = (_BS / 80.0) ** 2 + (_BC / 60.0) ** 2


def weighted_spearman(s, c):
    """Weighted Spearman: weighted Pearson on ranks. w = max(-c, 0)."""
    s = np.asarray(s, dtype=float)
    c = np.asarray(c, dtype=float)
    w = np.maximum(-c, 0.0)
    if w.sum() < 1e-12:
        return 0.0
    Rs = np.argsort(np.argsort(s)).astype(float)
    Rc = np.argsort(np.argsort(c)).astype(float)
    mu_s = (w * Rs).sum() / w.sum()
    mu_c = (w * Rc).sum() / w.sum()
    ds = Rs - mu_s
    dc = Rc - mu_c
    num = (w * ds * dc).sum()
    den = np.sqrt((w * ds ** 2).sum() * (w * dc ** 2).sum())
    if den < 1e-12:
        return 0.0
    return float(num / den)


def L_set_min_with_best(subj, roi, lam=0.2):
    p = RES_LAND / f'sub-{subj}_{roi}_landscape.json'
    if not p.exists():
        return None, None, None
    with open(p) as f:
        d = json.load(f)
    topk = np.array(d['l_topk_jaccard'])
    aug = topk + lam * NORM_GRID
    idx = np.unravel_index(int(np.argmin(aug)), aug.shape)
    return float(aug.min()), float(_bs[idx[0]]), float(_bc[idx[1]])


def compute_wspear_at_best(subj, roi, family, lam=0.2):
    """At L_set's best (bs, bc), recompute vuln_sim and weighted Spearman."""
    Ls, bs, bc = L_set_min_with_best(subj, roi, lam)
    if Ls is None:
        return None
    # Reload vuln_target
    try:
        vuln_target = load_cvd_loco_target(subj, roi)
    except Exception:
        return None
    # HC W (excluding subj if HC)
    hc_amps = {}
    for hc in HC + ['07']:  # also include sub-07 amps if available (W only)
        try:
            hc_amps[hc] = load_amplitudes(LOCAL_DATA, hc, roi)
        except Exception:
            pass
    pool_amps = {k: v for k, v in hc_amps.items() if k != subj}
    basis_full = create_basis_full(N_CHANNELS, basis_type='fe')
    C_orig = basis_full[HUE_ANGLES]
    pool_W, _ = precompute_hc_W(pool_amps, C_orig)
    C_shift, _ = get_2component_design(bs, bc, family)
    vsim, _ = simulate_mean_hc_wfixed(pool_W, pool_amps, C_shift)
    rho_w = weighted_spearman(vsim, vuln_target)
    return {'L_set': Ls, 'best_bs': bs, 'best_bc': bc,
            'rho_w': rho_w, 'L_wSpear': 1.0 - rho_w}


def main():
    fam_for = lambda s: CVD_FAM.get(s, 'deutan')

    # Per (subj, ROI) compute L_set, L_wSpear at the L_set best point
    rec = {}
    for subj in HC + CVD + SANITY:
        rec[subj] = {}
        for roi in ROIS:
            r = compute_wspear_at_best(subj, roi, fam_for(subj))
            rec[subj][roi] = r

    # HC pool stats per ROI
    hc_pool = {}
    for roi in ROIS:
        Ls = np.array([rec[h][roi]['L_set'] for h in HC if rec[h][roi]])
        Lw = np.array([rec[h][roi]['L_wSpear'] for h in HC if rec[h][roi]])
        hc_pool[roi] = {
            'Ls_mu': Ls.mean(), 'Ls_sd': Ls.std(ddof=1),
            'Lw_mu': Lw.mean(), 'Lw_sd': Lw.std(ddof=1),
        }

    print('\n=== HC pool L_set + L_wSpear (n=6) ===')
    for roi in ROIS:
        p = hc_pool[roi]
        print(f'  [{roi}] L_set μ={p["Ls_mu"]:.3f} σ={p["Ls_sd"]:.3f}; '
              f'L_wSpear μ={p["Lw_mu"]:.3f} σ={p["Lw_sd"]:.3f}')

    print('\n=== Per (subj, ROI) ===')
    print(f'{"subj":<6} {"ROI":<4} {"L_set":>7} {"z_set":>7} {"rho_w":>7} {"L_wSpear":>9} {"z_wSp":>7}')
    cvd_z = {}
    for subj in CVD + SANITY:
        cvd_z[subj] = {}
        for roi in ROIS:
            r = rec[subj][roi]
            if r is None:
                continue
            zs = (r['L_set'] - hc_pool[roi]['Ls_mu']) / hc_pool[roi]['Ls_sd']
            zw = (r['L_wSpear'] - hc_pool[roi]['Lw_mu']) / hc_pool[roi]['Lw_sd']
            cvd_z[subj][roi] = {'z_set': zs, 'z_wSp': zw,
                                'rho_w': r['rho_w'], 'L_set': r['L_set']}
            print(f'sub-{subj:<2} {roi:<4} {r["L_set"]:>7.3f} {zs:>+7.2f} '
                  f'{r["rho_w"]:>+7.3f} {r["L_wSpear"]:>9.3f} {zw:>+7.2f}')

    roi_configs = {
        'V1_only': ['V1'], 'V2_only': ['V2'], 'V4_only': ['V4'],
        'V1+V4': ['V1', 'V4'], 'V2+V4': ['V2', 'V4'],
    }
    alphas = [0.0, 0.25, 0.5, 0.75, 1.0]
    betas = [0.0, 0.25, 0.5, 0.75, 1.0]

    sweep = []
    for cfg_name, cfg in roi_configs.items():
        for alpha in alphas:
            for beta in betas:
                if alpha == 0 and beta == 0:
                    continue
                row = {'cfg': cfg_name, 'alpha': alpha, 'beta': beta}
                for subj in CVD + SANITY:
                    z_set_sum = sum(cvd_z[subj][r]['z_set'] for r in cfg
                                     if r in cvd_z[subj])
                    z_wSp_sum = sum(cvd_z[subj][r]['z_wSp'] for r in cfg
                                     if r in cvd_z[subj])
                    z_comb = alpha * z_set_sum + beta * z_wSp_sum
                    row[f'sub-{subj}_zcomb'] = z_comb
                    row[f'sub-{subj}_zset'] = z_set_sum
                    row[f'sub-{subj}_zwSp'] = z_wSp_sum
                sweep.append(row)

    common = [r for r in sweep
              if r['sub-08_zcomb'] < -2 and r['sub-09_zcomb'] < -2
              and abs(r['sub-10_zcomb']) < 1.5]
    print(f'\n=== Common best (both CVD z<=-2, |sub-10|<1.5) ===')
    print(f'Total cells: {len(sweep)}, Common best: {len(common)}')
    if common:
        common.sort(key=lambda x: max(x['sub-08_zcomb'], x['sub-09_zcomb']))
        print(f'{"cfg":<10} {"a":>4} {"b":>4} {"z08":>7} {"z09":>7} {"z10":>7}')
        for r in common[:15]:
            print(f'{r["cfg"]:<10} {r["alpha"]:>4.2f} {r["beta"]:>4.2f} '
                  f'{r["sub-08_zcomb"]:>+7.2f} {r["sub-09_zcomb"]:>+7.2f} '
                  f'{r["sub-10_zcomb"]:>+7.2f}')

    relaxed = [r for r in sweep
               if r['sub-08_zcomb'] < -1.5 and r['sub-09_zcomb'] < -1.5
               and abs(r['sub-10_zcomb']) < 1.5]
    print(f'\nRelaxed (z<=-1.5): {len(relaxed)} cells')
    if relaxed:
        relaxed.sort(key=lambda x: max(x['sub-08_zcomb'], x['sub-09_zcomb']))
        print(f'{"cfg":<10} {"a":>4} {"b":>4} {"z08":>7} {"z09":>7} {"z10":>7}')
        for r in relaxed[:10]:
            print(f'{r["cfg"]:<10} {r["alpha"]:>4.2f} {r["beta"]:>4.2f} '
                  f'{r["sub-08_zcomb"]:>+7.2f} {r["sub-09_zcomb"]:>+7.2f} '
                  f'{r["sub-10_zcomb"]:>+7.2f}')

    out = {
        'config': {'lam_tikh': 0.2, 'wspear_at_best_lset': True},
        'rec': {s: {roi: rec[s][roi] for roi in ROIS}
                for s in HC + CVD + SANITY},
        'hc_pool': hc_pool,
        'sweep': sweep, 'common_best': common, 'relaxed_best': relaxed,
    }
    out_path = ROOT / 'results' / 'cycles' / 'cycle7_blend_wspearman.json'
    with open(out_path, 'w') as f:
        json.dump(out, f, indent=2, default=lambda o: float(o) if hasattr(o, 'item') else str(o))
    print(f'\n[Wrote] {out_path}')


if __name__ == '__main__':
    main()
