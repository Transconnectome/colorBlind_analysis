#!/usr/bin/env python3
"""consolidate_results.py — Phase 2 filter optimization 모든 cell 결과 통합 CSV/JSON 저장.

매번 cycle10b/cycle11/cycle8_voxel_diag JSON에서 재계산하지 않도록
모든 (subject × ROI × family × metric) 값을 한 파일에 저장.

CSV columns:
  subject, role, ROI, family, family_color, sign_family,
  L_set, L_vox, z_set, z_vox, z_combined,
  bootstrap_L_vox_pt, bootstrap_L_vox_ci_lo, bootstrap_L_vox_ci_hi,
  z_combined_ci_lo, z_combined_ci_hi,
  pool_n, pool_Ls_mu, pool_Ls_sd, pool_Lv_mu, pool_Lv_sd,
  cross_roi_pairs (json string of {R_set|R_vox: z_combined})
"""
import json
import csv
import numpy as np
from pathlib import Path
from itertools import product

ROOT = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/'
            'colorBlind_analysis/analysis/future_phase2_filter_optimization')
RES = ROOT / 'results/cycle_filter_refinement'
RES_VOX = RES / 'cycle6_voxel_diag'
BOOT_DIR = RES / 'cycle8_voxel_bootstrap_server'

OUT_CSV = RES / 'consolidated_phase2_results.csv'
OUT_JSON = RES / 'consolidated_phase2_results.json'

HC = ['01', '02', '03', '04', '05', '06']
CVD = ['08', '09']
ALL = HC + CVD
ROIS = ['V1', 'V2', 'V4']
COLOR_IDX = {'yellow': 2, 'magenta': 7}
FAMILIES = {'deutan': ('yellow', -1.0), 'protan': ('magenta', +1.0)}

_bs = np.arange(0.0, 81.0, 2.0)
_bc = np.arange(-60.0, 61.0, 2.0)
_BS, _BC = np.meshgrid(_bs, _bc, indexing='ij')
NORM_GRID = (_BS / 80.0) ** 2 + (_BC / 60.0) ** 2


def L_set(target, roi, lam=0.2):
    p = RES / f'sub-{target}_{roi}_landscape.json'
    if not p.exists():
        return None
    with open(p) as f:
        d = json.load(f)
    topk = np.array(d['l_topk_jaccard'])
    return float((topk + lam * NORM_GRID).min())


def L_vox(target, roi, fam_color, fam_sign):
    p = RES_VOX / f'{roi}_summary.json'
    with open(p) as f:
        d = json.load(f)
    if target not in d['per_subject']:
        return None
    r = d['per_subject'][target]
    sigs_z = r['sigs_z']
    rdm_z = np.array(r['rdm_z'])
    c_idx = COLOR_IDX[fam_color]
    z_mean = float(sigs_z['mean_amp'][c_idx])
    z_rdm = float(np.abs(rdm_z[c_idx]).mean())
    z_runc = float(sigs_z['run_consistency'][c_idx])
    return -(fam_sign * z_mean + abs(z_rdm) + abs(z_runc)), z_mean, z_rdm, z_runc


def pool_stats(pool, roi):
    Ls = [L_set(s, roi) for s in pool if L_set(s, roi) is not None]
    out = {'Ls_mu': float(np.mean(Ls)), 'Ls_sd': float(np.std(Ls, ddof=1))}
    for fam_name, (fc, fs) in FAMILIES.items():
        Lv = [L_vox(s, roi, fc, fs)[0] for s in pool if L_vox(s, roi, fc, fs) is not None]
        out[f'Lv_{fam_name}_mu'] = float(np.mean(Lv))
        out[f'Lv_{fam_name}_sd'] = float(np.std(Lv, ddof=1))
    return out


def get_bootstrap(subj, roi):
    p = BOOT_DIR / f'sub-{subj}_{roi}.json'
    if not p.exists():
        return None
    with open(p) as f:
        return json.load(f)


def main():
    rows = []
    consolidated = {}

    for subj in ALL:
        role = 'CVD' if subj in CVD else 'HC'
        # Pool: full HC for CVD, LOO for HC
        pool = HC if role == 'CVD' else [h for h in HC if h != subj]
        pool_n = len(pool)
        consolidated[subj] = {'role': role, 'pool_n': pool_n, 'pool': pool, 'cells': {}}

        for roi in ROIS:
            ps = pool_stats(pool, roi)
            Ls = L_set(subj, roi)
            consolidated[subj]['cells'][roi] = {
                'L_set': Ls, 'pool_Ls_mu': ps['Ls_mu'], 'pool_Ls_sd': ps['Ls_sd'],
                'families': {}}

            for fam_name, (fc, fs) in FAMILIES.items():
                Lv_tup = L_vox(subj, roi, fc, fs)
                if Lv_tup is None:
                    continue
                Lv, zmean, zrdm, zrunc = Lv_tup
                z_set = (Ls - ps['Ls_mu']) / ps['Ls_sd']
                z_vox = (Lv - ps[f'Lv_{fam_name}_mu']) / ps[f'Lv_{fam_name}_sd']
                z_combined = z_set + z_vox

                # Bootstrap CI for L_vox (server bootstrap if available)
                boot = get_bootstrap(subj, roi)
                if boot and boot['family'] == fam_name:
                    L_vox_ci = boot['bootstrap_summary']['L_vox']['ci95']
                    z_vox_ci = ((L_vox_ci[0] - ps[f'Lv_{fam_name}_mu']) / ps[f'Lv_{fam_name}_sd'],
                                (L_vox_ci[1] - ps[f'Lv_{fam_name}_mu']) / ps[f'Lv_{fam_name}_sd'])
                    z_combo_ci = (z_set + z_vox_ci[0], z_set + z_vox_ci[1])
                else:
                    L_vox_ci = (None, None)
                    z_vox_ci = (None, None)
                    z_combo_ci = (None, None)

                cell = {
                    'L_set': Ls, 'L_vox': Lv,
                    'z_mean': zmean, 'z_rdm': zrdm, 'z_runc': zrunc,
                    'z_set': z_set, 'z_vox': z_vox, 'z_combined': z_combined,
                    'pool_Lv_mu': ps[f'Lv_{fam_name}_mu'],
                    'pool_Lv_sd': ps[f'Lv_{fam_name}_sd'],
                    'L_vox_boot_ci_lo': L_vox_ci[0],
                    'L_vox_boot_ci_hi': L_vox_ci[1],
                    'z_vox_boot_ci_lo': z_vox_ci[0],
                    'z_vox_boot_ci_hi': z_vox_ci[1],
                    'z_combined_ci_lo': z_combo_ci[0],
                    'z_combined_ci_hi': z_combo_ci[1],
                }
                consolidated[subj]['cells'][roi]['families'][fam_name] = cell

                rows.append({
                    'subject': f'sub-{subj}', 'role': role, 'ROI': roi,
                    'family': fam_name, 'family_color': fc, 'sign_family': fs,
                    'pool_n': pool_n,
                    'L_set': round(Ls, 4), 'L_vox': round(Lv, 4),
                    'z_mean': round(zmean, 4), 'z_rdm': round(zrdm, 4), 'z_runc': round(zrunc, 4),
                    'z_set': round(z_set, 4), 'z_vox': round(z_vox, 4),
                    'z_combined': round(z_combined, 4),
                    'pool_Ls_mu': round(ps['Ls_mu'], 4), 'pool_Ls_sd': round(ps['Ls_sd'], 4),
                    'pool_Lv_mu': round(ps[f'Lv_{fam_name}_mu'], 4),
                    'pool_Lv_sd': round(ps[f'Lv_{fam_name}_sd'], 4),
                    'L_vox_boot_ci_lo': round(L_vox_ci[0], 4) if L_vox_ci[0] is not None else '',
                    'L_vox_boot_ci_hi': round(L_vox_ci[1], 4) if L_vox_ci[1] is not None else '',
                    'z_combined_ci_lo': round(z_combo_ci[0], 4) if z_combo_ci[0] is not None else '',
                    'z_combined_ci_hi': round(z_combo_ci[1], 4) if z_combo_ci[1] is not None else '',
                })

    # V1+V4 sum (same-ROI rule)
    print(f'Writing CSV: {OUT_CSV}')
    fields = ['subject', 'role', 'ROI', 'family', 'family_color', 'sign_family',
              'pool_n', 'L_set', 'L_vox', 'z_mean', 'z_rdm', 'z_runc',
              'z_set', 'z_vox', 'z_combined',
              'pool_Ls_mu', 'pool_Ls_sd', 'pool_Lv_mu', 'pool_Lv_sd',
              'L_vox_boot_ci_lo', 'L_vox_boot_ci_hi',
              'z_combined_ci_lo', 'z_combined_ci_hi']
    with open(OUT_CSV, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    # Cross-ROI pairs CSV
    cross_rows = []
    for subj in ALL:
        role = 'CVD' if subj in CVD else 'HC'
        pool = HC if role == 'CVD' else [h for h in HC if h != subj]
        for fam_name in FAMILIES:
            cells = consolidated[subj]['cells']
            for R_set, R_vox in product(ROIS, ROIS):
                if (R_set not in cells or fam_name not in cells[R_set]['families'] or
                    R_vox not in cells or fam_name not in cells[R_vox]['families']):
                    continue
                z_set = cells[R_set]['families'][fam_name]['z_set']
                z_vox = cells[R_vox]['families'][fam_name]['z_vox']
                cross_rows.append({
                    'subject': f'sub-{subj}', 'role': role, 'family': fam_name,
                    'R_set': R_set, 'R_vox': R_vox,
                    'pair': f'{R_set}|{R_vox}',
                    'z_set': round(z_set, 4),
                    'z_vox': round(z_vox, 4),
                    'z_combined_cross': round(z_set + z_vox, 4),
                    'same_ROI': R_set == R_vox,
                })

    OUT_CROSS_CSV = RES / 'consolidated_cross_roi.csv'
    print(f'Writing cross-ROI CSV: {OUT_CROSS_CSV}')
    with open(OUT_CROSS_CSV, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['subject','role','family','R_set','R_vox','pair',
                                          'z_set','z_vox','z_combined_cross','same_ROI'])
        w.writeheader()
        w.writerows(cross_rows)

    # JSON full structure
    print(f'Writing JSON: {OUT_JSON}')
    with open(OUT_JSON, 'w') as f:
        json.dump({
            'meta': {
                'generated': '2026-05-03',
                'description': 'Consolidated Phase 2 filter optimization results',
                'pool_convention': 'CVD: full HC n=6, HC: LOO n=5',
                'L_set_formula': 'min over (β_s, β_c) of [l_topk_jaccard(k=3) + 0.2*Tikh]',
                'L_vox_formula': '-(sign_family*z_mean[c] + |z_rdm_row[c]| + |z_runc[c]|)',
                'z_combined_same_roi': 'z_set(R) + z_vox(R)',
                'z_combined_cross_roi': 'z_set(R_a) + z_vox(R_b), R_a may differ from R_b',
                'bootstrap_n': 200,
                'bootstrap_source': 'cycle8_voxel_bootstrap_server (sub-02/04/08/09 only)',
            },
            'subjects': consolidated,
        }, f, indent=2, default=lambda x: float(x) if isinstance(x, (np.float64, np.float32)) else x)

    print(f'Done.')
    print(f'  Rows in main CSV: {len(rows)}')
    print(f'  Rows in cross-ROI CSV: {len(cross_rows)}')


if __name__ == '__main__':
    main()
