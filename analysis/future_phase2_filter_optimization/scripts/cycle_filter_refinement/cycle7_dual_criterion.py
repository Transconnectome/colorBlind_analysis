#!/usr/bin/env python3
"""cycle7_dual_criterion.py — Plan 04 Cycle 7 Task A.

V4-inclusive Family-aware dual-criterion loss:
  L_common(s) = alpha * L_set(s, R) + beta * L_voxel-axis(s, R, c_family)

L_voxel-axis(s, R, c) = -[ sign_family * z_mean_amp(c) + |z_rdm_row(c)| + |z_runc(c)| ]

Reuses Cycle 1 landscape (41x61 grid) for L_set and Cycle 6 voxel_diag for signature z.
Scale-normalize via z-score within HC pool (n=6, sub-07 excluded).
"""
import json
import numpy as np
from pathlib import Path

ROOT = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/future_phase2_filter_optimization')
RES_VOX = ROOT / 'results/cycles/cycle6_voxel_diag'
RES_LAND = ROOT / 'results/cycles'

ROIS = ['V1', 'V2', 'V4']
HC = ['01', '02', '03', '04', '05', '06']
CVD = ['08', '09']
SANITY = ['10']
COLOR_IDX = {'yellow': 2, 'magenta': 7}
# (family, family_color, sign_family)
FAMILY = {'08': ('deutan', 'yellow', -1.0),
          '09': ('protan', 'magenta', +1.0),
          '10': ('deutan', 'yellow', -1.0)}

# Tikhonov norm grid (matches Cycle 1 landscape)
_bs = np.arange(0.0, 81.0, 2.0)   # 41 pts
_bc = np.arange(-60.0, 61.0, 2.0)  # 61 pts
_BS, _BC = np.meshgrid(_bs, _bc, indexing='ij')
NORM_GRID = (_BS / 80.0) ** 2 + (_BC / 60.0) ** 2


def L_set_min(subj, roi, lam=0.2):
    p = RES_LAND / f'sub-{subj}_{roi}_landscape.json'
    if not p.exists():
        return None
    with open(p) as f:
        d = json.load(f)
    topk = np.array(d['l_topk_jaccard'])
    aug = topk + lam * NORM_GRID
    return float(aug.min())


def L_vox_axis(subj, roi, family_color, sign_family):
    p = RES_VOX / f'{roi}_summary.json'
    with open(p) as f:
        d = json.load(f)
    if subj not in d['per_subject']:
        return None
    r = d['per_subject'][subj]
    sigs_z = r['sigs_z']
    rdm_z = np.array(r['rdm_z'])
    c_idx = COLOR_IDX[family_color]
    z_mean = float(sigs_z['mean_amp'][c_idx])
    z_rdm_row = float(np.abs(rdm_z[c_idx]).mean())
    z_runc = float(sigs_z['run_consistency'][c_idx])
    L = -(sign_family * z_mean + abs(z_rdm_row) + abs(z_runc))
    return L


def main():
    # Build HC pool stats per ROI (separately for yellow/magenta family-color)
    hc_pool = {}
    for roi in ROIS:
        Ls_list = []
        Lv_yellow_list = []
        Lv_magenta_list = []
        for hc in HC:
            Ls = L_set_min(hc, roi)
            if Ls is not None:
                Ls_list.append(Ls)
            Lvy = L_vox_axis(hc, roi, 'yellow', -1.0)
            if Lvy is not None:
                Lv_yellow_list.append(Lvy)
            Lvm = L_vox_axis(hc, roi, 'magenta', +1.0)
            if Lvm is not None:
                Lv_magenta_list.append(Lvm)
        hc_pool[roi] = {
            'Ls': np.array(Ls_list),
            'Lv_yellow': np.array(Lv_yellow_list),
            'Lv_magenta': np.array(Lv_magenta_list),
        }

    print('=== HC pool stats (n=6, sub-07 excluded) ===')
    for roi in ROIS:
        p = hc_pool[roi]
        print(f'  [{roi}] L_set mu={p["Ls"].mean():.3f} sd={p["Ls"].std(ddof=1):.3f}; '
              f'Lv_yellow mu={p["Lv_yellow"].mean():+.2f} sd={p["Lv_yellow"].std(ddof=1):.2f}; '
              f'Lv_magenta mu={p["Lv_magenta"].mean():+.2f} sd={p["Lv_magenta"].std(ddof=1):.2f}')

    # Compute z per (subj, ROI) using subject-family-specific pool
    cvd_z = {}
    for subj in CVD + SANITY:
        fam, color, sign = FAMILY[subj]
        cvd_z[subj] = {}
        for roi in ROIS:
            Ls = L_set_min(subj, roi)
            Lv = L_vox_axis(subj, roi, color, sign)
            mu_Ls = hc_pool[roi]['Ls'].mean()
            sd_Ls = hc_pool[roi]['Ls'].std(ddof=1)
            mu_Lv = hc_pool[roi][f'Lv_{color}'].mean()
            sd_Lv = hc_pool[roi][f'Lv_{color}'].std(ddof=1)
            z_set = (Ls - mu_Ls) / sd_Ls
            z_vox = (Lv - mu_Lv) / sd_Lv
            cvd_z[subj][roi] = {
                'L_set': Ls, 'L_vox': Lv,
                'z_set': z_set, 'z_vox': z_vox,
            }

    print('\n=== Per (subj, ROI) z (family-color: sub-08 yellow, sub-09 magenta, sub-10 yellow) ===')
    print(f'{"subj":<6} {"ROI":<4} {"L_set":>7} {"z_set":>7} {"L_vox":>7} {"z_vox":>7}')
    for subj in CVD + SANITY:
        for roi in ROIS:
            r = cvd_z[subj][roi]
            print(f'sub-{subj:<2} {roi:<4} {r["L_set"]:>7.3f} {r["z_set"]:>+7.2f} '
                  f'{r["L_vox"]:>+7.2f} {r["z_vox"]:>+7.2f}')

    # ROI configs (V4 enforced)
    roi_configs = {
        'V1_only': ['V1'],
        'V2_only': ['V2'],
        'V4_only': ['V4'],
        'V1+V4': ['V1', 'V4'],
        'V2+V4': ['V2', 'V4'],
    }

    alphas = [0.0, 0.25, 0.5, 0.75, 1.0]
    betas = [0.0, 0.25, 0.5, 0.75, 1.0]

    # alpha,beta sweep + ROI configs (combined z = α·sum(z_set) + β·sum(z_vox))
    sweep = []
    for cfg_name, cfg in roi_configs.items():
        for alpha in alphas:
            for beta in betas:
                if alpha == 0 and beta == 0:
                    continue
                row = {'cfg': cfg_name, 'alpha': alpha, 'beta': beta,
                       'has_V4': 'V4' in cfg}
                for subj in CVD + SANITY:
                    z_set_sum = sum(cvd_z[subj][r]['z_set'] for r in cfg)
                    z_vox_sum = sum(cvd_z[subj][r]['z_vox'] for r in cfg)
                    z_comb = alpha * z_set_sum + beta * z_vox_sum
                    row[f'sub-{subj}_zcomb'] = z_comb
                    row[f'sub-{subj}_zset'] = z_set_sum
                    row[f'sub-{subj}_zvox'] = z_vox_sum
                sweep.append(row)

    # Common best: both CVD z_comb <= -2 AND sub-10 |z_comb| < 1.5
    common = []
    for r in sweep:
        z08 = r['sub-08_zcomb']
        z09 = r['sub-09_zcomb']
        z10 = r['sub-10_zcomb']
        # specificity: CVD specific (negative z = small loss = specific) AND sub-10 not specific
        if z08 < -2 and z09 < -2 and abs(z10) < 1.5:
            common.append(r)

    print(f'\n=== α/β sweep — Common best (both CVD z<=-2, |sub-10|<1.5) ===')
    print(f'Total cells: {len(sweep)}, Common best: {len(common)}')
    if common:
        # Sort by max(z08, z09) — most extreme negative wins
        common.sort(key=lambda x: max(x['sub-08_zcomb'], x['sub-09_zcomb']))
        print(f'\n{"cfg":<10} {"a":>4} {"b":>4} {"z08":>7} {"z09":>7} {"z10":>7}')
        for r in common[:15]:
            print(f'{r["cfg"]:<10} {r["alpha"]:>4.2f} {r["beta"]:>4.2f} '
                  f'{r["sub-08_zcomb"]:>+7.2f} {r["sub-09_zcomb"]:>+7.2f} '
                  f'{r["sub-10_zcomb"]:>+7.2f}')
    else:
        print('No (α, β, ROI config) cell satisfies criteria.')

    # Relax criteria: both CVD <= -1.5
    relaxed = [r for r in sweep
               if r['sub-08_zcomb'] < -1.5 and r['sub-09_zcomb'] < -1.5
               and abs(r['sub-10_zcomb']) < 1.5]
    print(f'\nRelaxed (z<=-1.5, |s10|<1.5): {len(relaxed)} cells')
    if relaxed:
        relaxed.sort(key=lambda x: max(x['sub-08_zcomb'], x['sub-09_zcomb']))
        print(f'{"cfg":<10} {"a":>4} {"b":>4} {"z08":>7} {"z09":>7} {"z10":>7}')
        for r in relaxed[:10]:
            print(f'{r["cfg"]:<10} {r["alpha"]:>4.2f} {r["beta"]:>4.2f} '
                  f'{r["sub-08_zcomb"]:>+7.2f} {r["sub-09_zcomb"]:>+7.2f} '
                  f'{r["sub-10_zcomb"]:>+7.2f}')

    # Save full results
    out = {
        'config': {'lam_tikh': 0.2, 'family_map': FAMILY, 'hc_n': 6,
                   'sub07_excluded': True},
        'hc_pool_stats': {roi: {k: v.tolist() if hasattr(v, 'tolist') else v
                                  for k, v in hc_pool[roi].items()}
                          for roi in ROIS},
        'cvd_per_cell': {s: {roi: {k: v for k, v in cvd_z[s][roi].items()}
                              for roi in ROIS}
                         for s in CVD + SANITY},
        'sweep': sweep,
        'common_best': common,
        'relaxed_best': relaxed,
    }
    out_path = ROOT / 'results' / 'cycles' / 'cycle7_dual_criterion.json'
    with open(out_path, 'w') as f:
        json.dump(out, f, indent=2)
    print(f'\n[Wrote] {out_path}')


if __name__ == '__main__':
    main()
