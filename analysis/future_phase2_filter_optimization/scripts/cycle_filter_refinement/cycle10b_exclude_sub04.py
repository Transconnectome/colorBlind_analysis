#!/usr/bin/env python3
"""cycle10b_exclude_sub04.py — sub-04 sensitivity analysis.

Cycle 10 finding: sub-04는 yellow z_mean 양수(sub-08과 부호 반대), magenta z_mean
양수(sub-09과 같은 방향)로 데이터 자체가 anomaly. 단순 HC outlier가 아닌 BOLD-high
또는 mild signal 후보. selection rule variant 변경으로 해결 불가.

Test: sub-04를 HC pool에서 제외하고 selection rule을 다시 평가.
H1: 나머지 HC LOO FP rate 변화 (sub-02 등 다른 FP는 어떻게 되는가)
H2: sub-08, sub-09 z_combined 변화 (pool 축소 → variance 변화)
H3: pool 통계의 안정성 (n=5에서 n=4 LOO로 감소 영향)
"""
import json
import numpy as np
from pathlib import Path

ROOT = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/'
            'colorBlind_analysis/analysis/future_phase2_filter_optimization')
RES = ROOT / 'results/cycles'
RES_VOX = RES / 'cycle6_voxel_diag'
OUT = RES / 'cycle10b_exclude_sub04.json'

HC_FULL = ['01', '02', '03', '04', '05', '06']
HC_NO04 = ['01', '02', '03', '05', '06']
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


def L_vox_A(target, roi, fam_color, fam_sign):
    """Variant A: -(sign·z_mean + |z_rdm_row| + |z_runc|)."""
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
    """Mean/SD of L_set and L_vox per family for a given pool."""
    Ls = [L_set(s, roi) for s in pool]
    Ls = [x for x in Ls if x is not None]
    out = {'Ls_mu': float(np.mean(Ls)), 'Ls_sd': float(np.std(Ls, ddof=1))}
    for fam_name, (fc, fs) in FAMILIES.items():
        Lv = [L_vox_A(s, roi, fc, fs) for s in pool]
        Lv = [x for x in Lv if x is not None]
        out[f'Lv_{fam_name}_mu'] = float(np.mean(Lv))
        out[f'Lv_{fam_name}_sd'] = float(np.std(Lv, ddof=1))
    return out


def evaluate(target, pool_subjects):
    """Compute z_combined for target against pool_subjects, all ROIs and families."""
    stats = {roi: pool_stats(pool_subjects, roi) for roi in ROIS}
    out = {'pool_n': len(pool_subjects)}
    for roi in ROIS:
        Ls = L_set(target, roi)
        z_set = (Ls - stats[roi]['Ls_mu']) / stats[roi]['Ls_sd']
        per_fam = {}
        for fam_name, (fc, fs) in FAMILIES.items():
            Lv = L_vox_A(target, roi, fc, fs)
            mu = stats[roi][f'Lv_{fam_name}_mu']
            sd = stats[roi][f'Lv_{fam_name}_sd']
            z_vox = (Lv - mu) / sd if sd > 0 else np.nan
            per_fam[fam_name] = {'z_set': float(z_set), 'z_vox': float(z_vox),
                                  'z_combined': float(z_set + z_vox)}
        out[roi] = per_fam
    return out


def combine(per_roi, fam, mode):
    """mode: 'V4' or 'V1+V4'."""
    if mode == 'V4':
        return per_roi['V4'][fam]['z_combined']
    elif mode == 'V1+V4':
        z_set = per_roi['V1'][fam]['z_set'] + per_roi['V4'][fam]['z_set']
        z_vox = per_roi['V1'][fam]['z_vox'] + per_roi['V4'][fam]['z_vox']
        return z_set + z_vox


def main():
    results = {'meta': {
        'cycle': '10b',
        'task': 'sub-04 exclusion sensitivity (Variant A only)',
        'pool_full': HC_FULL,
        'pool_no04': HC_NO04,
    }, 'comparisons': {}}

    print('=== HC LOO FP check (Variant A current rule) ===')
    print(f'{"target":<6} {"family":<7} {"V4_full":>9} {"V4_no04":>9} {"V14_full":>9} {"V14_no04":>9} {"shift":>7}')
    print('-' * 70)
    for target in HC_FULL:
        if target == '04':
            # sub-04 vs pool excluding sub-04 (special case): use HC_NO04 as full pool
            pool_full = HC_NO04  # already excludes sub-04
            pool_no04 = HC_NO04  # same
        else:
            pool_full = [h for h in HC_FULL if h != target]
            pool_no04 = [h for h in HC_NO04 if h != target]
        if len(pool_no04) < 2:
            continue
        per_roi_full = evaluate(target, pool_full)
        per_roi_no04 = evaluate(target, pool_no04)
        results['comparisons'][f'sub-{target}'] = {
            'role': 'HC',
            'with_sub04': per_roi_full,
            'no_sub04': per_roi_no04,
        }
        for fam in FAMILIES:
            zv4_f = combine(per_roi_full, fam, 'V4')
            zv4_n = combine(per_roi_no04, fam, 'V4')
            z14_f = combine(per_roi_full, fam, 'V1+V4')
            z14_n = combine(per_roi_no04, fam, 'V1+V4')
            shift = z14_n - z14_f
            mark_full = '** FP' if z14_f < -2 else ''
            mark_no04 = '** FP' if z14_n < -2 else ''
            print(f'sub-{target:<2} {fam:<7} {zv4_f:>+9.2f} {zv4_n:>+9.2f} {z14_f:>+9.2f}{mark_full:<5} {z14_n:>+9.2f}{mark_no04:<5} {shift:>+7.2f}')
        print()

    print('=== CVD detection (full pool n=6 vs no-sub04 pool n=5) ===')
    print(f'{"target":<6} {"family":<7} {"V4_full":>9} {"V4_no04":>9} {"V14_full":>9} {"V14_no04":>9} {"shift":>7}')
    print('-' * 70)
    for target in CVD:
        per_roi_full = evaluate(target, HC_FULL)
        per_roi_no04 = evaluate(target, HC_NO04)
        results['comparisons'][f'sub-{target}'] = {
            'role': 'CVD',
            'with_sub04': per_roi_full,
            'no_sub04': per_roi_no04,
        }
        for fam in FAMILIES:
            zv4_f = combine(per_roi_full, fam, 'V4')
            zv4_n = combine(per_roi_no04, fam, 'V4')
            z14_f = combine(per_roi_full, fam, 'V1+V4')
            z14_n = combine(per_roi_no04, fam, 'V1+V4')
            shift = z14_n - z14_f
            expected = (target == '08' and fam == 'deutan') or \
                       (target == '09' and fam == 'protan')
            tag = '←expected' if expected else ''
            print(f'sub-{target:<2} {fam:<7} {zv4_f:>+9.2f} {zv4_n:>+9.2f} {z14_f:>+9.2f} {z14_n:>+9.2f} {shift:>+7.2f}  {tag}')
        print()

    # Pool stats comparison
    print('\n=== Pool stats: full HC vs HC w/o sub-04 ===')
    for roi in ROIS:
        s_full = pool_stats(HC_FULL, roi)
        s_no04 = pool_stats(HC_NO04, roi)
        print(f'{roi}:')
        print(f'  L_set: μ={s_full["Ls_mu"]:.3f}±{s_full["Ls_sd"]:.3f} (full) → '
              f'μ={s_no04["Ls_mu"]:.3f}±{s_no04["Ls_sd"]:.3f} (no04)')
        for fam in FAMILIES:
            print(f'  L_vox[{fam}]: μ={s_full[f"Lv_{fam}_mu"]:.2f}±{s_full[f"Lv_{fam}_sd"]:.2f} → '
                  f'μ={s_no04[f"Lv_{fam}_mu"]:.2f}±{s_no04[f"Lv_{fam}_sd"]:.2f}')

    with open(OUT, 'w') as f:
        json.dump(results, f, indent=2)
    print(f'\nSaved: {OUT}')


if __name__ == '__main__':
    main()
