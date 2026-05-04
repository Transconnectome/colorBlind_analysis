#!/usr/bin/env python3
"""cycle8_hc_fp.py — HC LOO false positive check on Cycle 7 selection rule.

For each HC subject (sub-01..06):
  Pool = remaining 5 HC (sub-07 always excluded — V4=16voxel catastrophic)
  Evaluate selection rule under both family hypotheses (deutan/protan):
    z_set: l_topk + Tikh from landscape json (LOO recompute via grid; we just
           reuse the per-subject landscape min — note this is family-independent
           since l_topk uses argsort, which doesn't depend on family directly,
           but bs/bc grid was computed for one family.  For HC we re-evaluate)
    z_vox: family-aware = -[sign·z_mean(c) + |z_rdm-row(c)| + |z_runc(c)|]

Selection rule per Cycle 7: V1+V4 z_sum, alpha=beta=1.
Report z_combined for each (HC, family) — false positive if z<-2.
"""
import json
import numpy as np
from pathlib import Path

ROOT = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/future_phase2_filter_optimization')
RES = ROOT / 'results/cycles'
RES_VOX = RES / 'cycle6_voxel_diag'

HC = ['01', '02', '03', '04', '05', '06']
ROIS = ['V1', 'V2', 'V4']
COLOR_IDX = {'yellow': 2, 'magenta': 7}
FAMILIES = {'deutan': ('yellow', -1.0), 'protan': ('magenta', +1.0)}

_bs = np.arange(0.0, 81.0, 2.0)
_bc = np.arange(-60.0, 61.0, 2.0)
_BS, _BC = np.meshgrid(_bs, _bc, indexing='ij')
NORM_GRID = (_BS / 80.0) ** 2 + (_BC / 60.0) ** 2


def L_set_hc_loo(target, roi, lam=0.2):
    """For HC target: assume vuln target same as their own LOCO; landscape
    json was computed assuming target's family — but we can also recompute
    for either family. For HC pool, use the landscape from cycle 1 which is
    deutan-default. We just evaluate l_topk min."""
    p = RES / f'sub-{target}_{roi}_landscape.json'
    if not p.exists():
        return None
    with open(p) as f:
        d = json.load(f)
    topk = np.array(d['l_topk_jaccard'])
    aug = topk + lam * NORM_GRID
    return float(aug.min())


def L_vox_axis_hc_loo(target, roi, family_color, sign_family):
    """Read cycle6 voxel_diag json for the target (this already uses LOO HC
    pool when target is HC)."""
    p = RES_VOX / f'{roi}_summary.json'
    with open(p) as f:
        d = json.load(f)
    if target not in d['per_subject']:
        return None
    r = d['per_subject'][target]
    sigs_z = r['sigs_z']
    rdm_z = np.array(r['rdm_z'])
    c_idx = COLOR_IDX[family_color]
    z_mean = float(sigs_z['mean_amp'][c_idx])
    z_rdm_row = float(np.abs(rdm_z[c_idx]).mean())
    z_runc = float(sigs_z['run_consistency'][c_idx])
    return -(sign_family * z_mean + abs(z_rdm_row) + abs(z_runc))


def main():
    # HC pool stats per ROI for L_set normalisation: use the same Cycle 7
    # cvd-evaluation HC pool (n=6) for fair comparison — but for HC LOO we
    # use n=5 (excluding the target).
    # Approach: for each HC target, recompute pool stats from remaining 5.
    pool_stats_loo = {}  # [target][roi] = {'Ls_mu', 'Ls_sd', 'Lv_yellow_mu', ...}

    for target in HC:
        pool_stats_loo[target] = {}
        for roi in ROIS:
            others = [h for h in HC if h != target]
            Ls_pool = []
            Lvy_pool = []
            Lvm_pool = []
            for h in others:
                Ls = L_set_hc_loo(h, roi)
                if Ls is not None:
                    Ls_pool.append(Ls)
                Lvy = L_vox_axis_hc_loo(h, roi, 'yellow', -1.0)
                if Lvy is not None:
                    Lvy_pool.append(Lvy)
                Lvm = L_vox_axis_hc_loo(h, roi, 'magenta', +1.0)
                if Lvm is not None:
                    Lvm_pool.append(Lvm)
            pool_stats_loo[target][roi] = {
                'Ls_mu': float(np.mean(Ls_pool)),
                'Ls_sd': float(np.std(Ls_pool, ddof=1)),
                'Lvy_mu': float(np.mean(Lvy_pool)),
                'Lvy_sd': float(np.std(Lvy_pool, ddof=1)),
                'Lvm_mu': float(np.mean(Lvm_pool)),
                'Lvm_sd': float(np.std(Lvm_pool, ddof=1)),
            }

    # For each HC target, evaluate z_set + z_vox under each family hypothesis
    results = {}
    for target in HC:
        results[target] = {}
        for fam_name, (fam_color, fam_sign) in FAMILIES.items():
            per_roi = {}
            for roi in ROIS:
                Ls = L_set_hc_loo(target, roi)
                Lv = L_vox_axis_hc_loo(target, roi, fam_color, fam_sign)
                pool = pool_stats_loo[target][roi]
                z_set = (Ls - pool['Ls_mu']) / pool['Ls_sd']
                key_mu = 'Lvy_mu' if fam_color == 'yellow' else 'Lvm_mu'
                key_sd = 'Lvy_sd' if fam_color == 'yellow' else 'Lvm_sd'
                z_vox = (Lv - pool[key_mu]) / pool[key_sd]
                per_roi[roi] = {'L_set': Ls, 'L_vox': Lv,
                                'z_set': z_set, 'z_vox': z_vox}
            # Selection rule: V1+V4 z_sum, alpha=beta=1
            z_combined_v1v4 = (per_roi['V1']['z_set'] + per_roi['V4']['z_set']
                               + per_roi['V1']['z_vox'] + per_roi['V4']['z_vox'])
            z_combined_v4 = (per_roi['V4']['z_set'] + per_roi['V4']['z_vox'])
            z_combined_v1 = (per_roi['V1']['z_set'] + per_roi['V1']['z_vox'])
            results[target][fam_name] = {
                'per_roi': per_roi,
                'z_V1_only': z_combined_v1,
                'z_V4_only': z_combined_v4,
                'z_V1+V4': z_combined_v1v4,
            }

    # Print compact table
    print('=== HC LOO false positive check — Cycle 7 selection rule ===')
    print('Selection: V1+V4 z_sum, α=β=1, family-aware family ∈ {deutan, protan}')
    print()
    print(f'{"target":<6} {"family":<8} {"z_V1":>8} {"z_V4":>8} {"z_V1+V4":>9}  {"verdict":<14}')
    fp_count = {'deutan': 0, 'protan': 0, 'either': 0}
    for target in HC:
        any_fp = False
        for fam in ['deutan', 'protan']:
            r = results[target][fam]
            zv1 = r['z_V1_only']; zv4 = r['z_V4_only']; zboth = r['z_V1+V4']
            verdict = 'FP' if zboth < -2 else ('marginal' if zboth < -1.5 else 'pass')
            if zboth < -2:
                fp_count[fam] += 1
                any_fp = True
            print(f'sub-{target:<2} {fam:<8} {zv1:>+8.2f} {zv4:>+8.2f} {zboth:>+9.2f}  {verdict:<14}')
        if any_fp:
            fp_count['either'] += 1
        print()

    print(f'\nFP summary (z_V1+V4 < -2):')
    print(f'  Under deutan family: {fp_count["deutan"]}/6')
    print(f'  Under protan family: {fp_count["protan"]}/6')
    print(f'  Either family:       {fp_count["either"]}/6')

    # Compare to CVD
    print('\n=== Reference: CVD z_V1+V4 (from Cycle 7) ===')
    print('  sub-08 (deutan):  -19.32')
    print('  sub-09 (protan):  -5.95')
    print('  sub-10 (deutan):  -0.09')

    out = {'config': {'cycle': 8, 'task': 'hc_fp_check',
                      'selection_rule': 'V1+V4 z_sum α=β=1 family-aware'},
           'pool_stats_loo': pool_stats_loo,
           'results': results,
           'fp_count': fp_count}
    out_path = RES / 'cycle8_hc_fp.json'
    with open(out_path, 'w') as f:
        json.dump(out, f, indent=2)
    print(f'\n[Wrote] {out_path}')


if __name__ == '__main__':
    main()
