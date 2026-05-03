#!/usr/bin/env python3
"""cycle11_per_term_cross_roi.py — Per-term cross-ROI selection rule.

기존 Cycle 7 selection rule:
  z_combined(R) = z_set(R) + z_vox-axis(R, c_family)
  → 두 항이 같은 ROI

본 cycle의 변형:
  z_combined_cross(R_a, R_b) = z_set(R_a) + z_vox(R_b, c_family)
  → z_set 과 z_vox-axis가 다른 ROI에서 추출 가능

조합 (R_a, R_b) ∈ {V1, V2, V4} × {V1, V2, V4} = 9 cells
+ Sum 변형: z_set(R_a) + z_set(R_b) + z_vox(R_c) + z_vox(R_d) → 너무 explosive
→ 일단 single-pair (R_a, R_b)만 평가

평가 metric:
  - HC LOO FP rate (z_combined < -2)
  - CVD detection (sub-08 deutan, sub-09 protan)
  - HC distribution vs CVD bootstrap CI overlap (using server bootstrap)
  - Best cross-ROI pair per CVD subject
"""
import json
import numpy as np
from pathlib import Path
from itertools import product

ROOT = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/'
            'colorBlind_analysis/analysis/future_phase2_filter_optimization')
RES = ROOT / 'results/cycle_filter_refinement'
RES_VOX = RES / 'cycle6_voxel_diag'
OUT = RES / 'cycle11_per_term_cross_roi.json'

HC = ['01', '02', '03', '04', '05', '06']
CVD = ['08', '09']
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
    return -(fam_sign * z_mean + abs(z_rdm) + abs(z_runc))


def pool_stats(pool, roi):
    Ls = [L_set(s, roi) for s in pool if L_set(s, roi) is not None]
    out = {'Ls_mu': float(np.mean(Ls)), 'Ls_sd': float(np.std(Ls, ddof=1))}
    for fam_name, (fc, fs) in FAMILIES.items():
        Lv = [L_vox(s, roi, fc, fs) for s in pool if L_vox(s, roi, fc, fs) is not None]
        out[f'Lv_{fam_name}_mu'] = float(np.mean(Lv))
        out[f'Lv_{fam_name}_sd'] = float(np.std(Lv, ddof=1))
    return out


def evaluate_pair(target, pool, roi_set, roi_vox, fam):
    """Return z_combined for (R_set=roi_set) + (R_vox=roi_vox)."""
    fc, fs = FAMILIES[fam]
    Ls = L_set(target, roi_set)
    Lv = L_vox(target, roi_vox, fc, fs)
    if Ls is None or Lv is None:
        return np.nan
    s_set = pool_stats(pool, roi_set)
    s_vox = pool_stats(pool, roi_vox)
    z_set = (Ls - s_set['Ls_mu']) / s_set['Ls_sd']
    z_vox = (Lv - s_vox[f'Lv_{fam}_mu']) / s_vox[f'Lv_{fam}_sd']
    return z_set + z_vox


def main():
    results = {'meta': {
        'cycle': 11,
        'task': 'per-term cross-ROI selection rule',
        'rule': 'z_combined = z_set(R_set) + z_vox-axis(R_vox, c_family)',
    }, 'per_pair': {}, 'best_per_subject': {}}

    # Evaluate all 9 (R_set, R_vox) pairs for each subject × family
    print('=== Cycle 11: per-term cross-ROI z_combined ===')
    print(f'Rule: z_combined = z_set(R_set) + z_vox-axis(R_vox, c_family)')
    print()

    # CVD subjects: pool = full HC (n=6)
    print(f'{"target":<6} {"family":<7} {"R_set":<5} {"R_vox":<5} {"z_combo":>9}  verdict')
    print('-' * 55)
    for target in CVD + HC:
        is_cvd = target in CVD
        if is_cvd:
            pool = HC
        else:
            pool = [h for h in HC if h != target]
        results['per_pair'][f'sub-{target}'] = {}
        for fam in FAMILIES:
            if is_cvd:
                # Determine expected family
                expected_fam = 'deutan' if target == '08' else 'protan'
                if fam != expected_fam:
                    continue
            results['per_pair'][f'sub-{target}'][fam] = {}
            for roi_set, roi_vox in product(ROIS, ROIS):
                z = evaluate_pair(target, pool, roi_set, roi_vox, fam)
                results['per_pair'][f'sub-{target}'][fam][f'{roi_set}|{roi_vox}'] = float(z) if not np.isnan(z) else None
                if is_cvd:
                    role = 'detect' if z < -2 else 'miss'
                    print(f'sub-{target:<2} {fam:<7} {roi_set:<5} {roi_vox:<5} {z:>+9.2f}  {role}')
        if is_cvd:
            print()

    # HC LOO FP rate per pair
    print('\n=== HC LOO FP rate per (R_set, R_vox) pair (n=6 HC) ===')
    print(f'{"R_set":<5} {"R_vox":<5} {"deutan FP":>10} {"protan FP":>10}  HC FPs')
    print('-' * 60)
    fp_summary = {}
    for roi_set, roi_vox in product(ROIS, ROIS):
        fp_d, fp_p = 0, 0
        fp_d_subjs, fp_p_subjs = [], []
        for target in HC:
            for fam in FAMILIES:
                z = results['per_pair'][f'sub-{target}'].get(fam, {}).get(f'{roi_set}|{roi_vox}')
                if z is not None and z < -2:
                    if fam == 'deutan':
                        fp_d += 1
                        fp_d_subjs.append(target)
                    else:
                        fp_p += 1
                        fp_p_subjs.append(target)
        fp_summary[f'{roi_set}|{roi_vox}'] = {
            'deutan_fp': fp_d, 'protan_fp': fp_p,
            'deutan_subjs': fp_d_subjs, 'protan_subjs': fp_p_subjs,
        }
        d_subj_str = ','.join(fp_d_subjs) if fp_d_subjs else '-'
        p_subj_str = ','.join(fp_p_subjs) if fp_p_subjs else '-'
        print(f'{roi_set:<5} {roi_vox:<5} {fp_d}/6{"":>5} {fp_p}/6{"":>5}  d:[{d_subj_str}]  p:[{p_subj_str}]')

    results['fp_summary'] = fp_summary

    # Find best pair per CVD subject (lowest z while HC FP minimized)
    print('\n=== Best (R_set, R_vox) pair per CVD subject ===')
    print('Criterion: lowest CVD z_combined with HC FP ≤ 1 in same family\n')
    for target in CVD:
        fam = 'deutan' if target == '08' else 'protan'
        candidates = []
        for roi_set, roi_vox in product(ROIS, ROIS):
            pair = f'{roi_set}|{roi_vox}'
            z_cvd = results['per_pair'][f'sub-{target}'][fam][pair]
            fp_count = fp_summary[pair][f'{fam}_fp']
            candidates.append((pair, z_cvd, fp_count))
        # Sort by FP first (asc), then by z (asc, more negative = better)
        candidates.sort(key=lambda x: (x[2], x[1]))
        results['best_per_subject'][f'sub-{target}'] = candidates[:5]
        print(f'sub-{target} ({fam}) — top-5 by (FP↓, CVD z↓):')
        for pair, z, fp in candidates[:5]:
            mark = ''
            same_roi = pair.split('|')[0] == pair.split('|')[1]
            if same_roi:
                mark = '  [SAME-ROI baseline]'
            print(f'  {pair:<12} z={z:>+7.2f}  HC FP={fp}/6{mark}')
        print()

    # Compare best cross-ROI to current selection rule
    print('\n=== Comparison: cross-ROI best vs current rule ===')
    for target in CVD:
        fam = 'deutan' if target == '08' else 'protan'
        # Current rule uses V1+V4 z_sum (different framework)
        # For pair comparison use V4|V4 as same-ROI baseline
        baseline_pair = 'V4|V4'
        z_baseline = results['per_pair'][f'sub-{target}'][fam][baseline_pair]
        fp_baseline = fp_summary[baseline_pair][f'{fam}_fp']
        best = results['best_per_subject'][f'sub-{target}'][0]
        print(f'sub-{target} {fam}:')
        print(f'  V4|V4 baseline:   z={z_baseline:+.2f}, HC FP={fp_baseline}/6')
        print(f'  Best cross-ROI:   {best[0]:<12} z={best[1]:+.2f}, HC FP={best[2]}/6')
        if best[2] < fp_baseline or (best[2] == fp_baseline and best[1] < z_baseline):
            print(f'  → cross-ROI BETTER (FP↓ or same FP with stronger z)')
        else:
            print(f'  → no improvement')
        print()

    with open(OUT, 'w') as f:
        json.dump(results, f, indent=2)
    print(f'\nSaved: {OUT}')


if __name__ == '__main__':
    main()
