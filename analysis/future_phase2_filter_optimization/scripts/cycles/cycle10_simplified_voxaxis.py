#!/usr/bin/env python3
"""cycle10_simplified_voxaxis.py — z_vox-axis 항 단순화 변형 비교.

Cycle 8 #4 finding: sub-04 yellow z=+2.21 (sub-08과 부호 반대) 이지만
|z_rdm|+|z_runc| 가 부호 무관하게 큰 양수로 합산되어 false specificity 유도.

세 variant 비교:
  A (current):  L_vox = -(sign_fam·z_mean + |z_rdm_row| + |z_runc|)
  B (mean only):L_vox = -(sign_fam·z_mean)                          ← 단순화
  C (signed):   L_vox = -(sign_fam·z_mean + sign_fam·z_runc)        ← runc 도 signed

평가:
- HC LOO (n=5 pool, target 제외) z_combined under deutan/protan family
- CVD (n=6 pool) z_combined
- selection rule: V1+V4 z_sum 또는 V4 single-ROI

성공 기준:
  H1: variant B/C 에서 sub-04 FP 해소 (z_combined > -2)
  H2: sub-08 deutan detection 유지 (z_combined < -5)
  H3: sub-09 protan detection 유지 또는 약화 정도 정량
"""
import json
import numpy as np
from pathlib import Path

ROOT = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/'
            'colorBlind_analysis/analysis/future_phase2_filter_optimization')
RES = ROOT / 'results/cycles'
RES_VOX = RES / 'cycle6_voxel_diag'
OUT = RES / 'cycle10_simplified_voxaxis.json'

HC = ['01', '02', '03', '04', '05', '06']
CVD = ['08', '09']
ROIS = ['V1', 'V2', 'V4']
COLOR_IDX = {'yellow': 2, 'magenta': 7}
FAMILIES = {'deutan': ('yellow', -1.0), 'protan': ('magenta', +1.0)}

_bs = np.arange(0.0, 81.0, 2.0)
_bc = np.arange(-60.0, 61.0, 2.0)
_BS, _BC = np.meshgrid(_bs, _bc, indexing='ij')
NORM_GRID = (_BS / 80.0) ** 2 + (_BC / 60.0) ** 2


# ---------------------------------------------------------------------------
def L_set(target, roi, lam=0.2):
    p = RES / f'sub-{target}_{roi}_landscape.json'
    if not p.exists():
        return None
    with open(p) as f:
        d = json.load(f)
    topk = np.array(d['l_topk_jaccard'])
    return float((topk + lam * NORM_GRID).min())


def get_voxel_components(target, roi, fam_color):
    """Return (z_mean, z_rdm_row_abs, z_runc, z_rdm_row_signed_mean)."""
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
    z_rdm_abs = float(np.abs(rdm_z[c_idx]).mean())
    z_rdm_signed = float(rdm_z[c_idx].mean())  # signed average of row
    z_runc = float(sigs_z['run_consistency'][c_idx])
    return z_mean, z_rdm_abs, z_runc, z_rdm_signed


def L_vox(target, roi, fam_color, fam_sign, variant):
    """Return L_vox for a given variant.

    A: -(sign·z_mean + |z_rdm| + |z_runc|)   [current Cycle 7 rule]
    B: -(sign·z_mean)                         [mean only]
    C: -(sign·z_mean + sign·z_runc)           [signed mean + signed runc]
    """
    comp = get_voxel_components(target, roi, fam_color)
    if comp is None:
        return None
    z_mean, z_rdm_abs, z_runc, _ = comp
    if variant == 'A':
        return -(fam_sign * z_mean + abs(z_rdm_abs) + abs(z_runc))
    elif variant == 'B':
        return -(fam_sign * z_mean)
    elif variant == 'C':
        return -(fam_sign * z_mean + fam_sign * z_runc)
    raise ValueError(variant)


# ---------------------------------------------------------------------------
def compute_pool_stats(pool_subjects, roi, variants=('A', 'B', 'C')):
    """For a pool of subjects, compute mu/sd of L_set, L_vox per variant per family."""
    Ls_pool = []
    for s in pool_subjects:
        x = L_set(s, roi)
        if x is not None:
            Ls_pool.append(x)
    Lv_pool = {v: {f: [] for f in FAMILIES} for v in variants}
    for s in pool_subjects:
        for fam_name, (fc, fs) in FAMILIES.items():
            for v in variants:
                lv = L_vox(s, roi, fc, fs, v)
                if lv is not None:
                    Lv_pool[v][fam_name].append(lv)
    out = {
        'Ls_mu': float(np.mean(Ls_pool)),
        'Ls_sd': float(np.std(Ls_pool, ddof=1)),
    }
    for v in variants:
        for fam in FAMILIES:
            arr = Lv_pool[v][fam]
            out[f'Lv_{v}_{fam}_mu'] = float(np.mean(arr))
            out[f'Lv_{v}_{fam}_sd'] = float(np.std(arr, ddof=1))
    return out


def compute_z_for_target(target, pool_stats, variants=('A', 'B', 'C')):
    """Return per_roi z_set + z_vox per variant per family."""
    out = {}
    for roi in ROIS:
        Ls = L_set(target, roi)
        z_set = (Ls - pool_stats[roi]['Ls_mu']) / pool_stats[roi]['Ls_sd']
        per_var = {}
        for v in variants:
            per_fam = {}
            for fam_name, (fc, fs) in FAMILIES.items():
                Lv = L_vox(target, roi, fc, fs, v)
                mu = pool_stats[roi][f'Lv_{v}_{fam_name}_mu']
                sd = pool_stats[roi][f'Lv_{v}_{fam_name}_sd']
                z_vox = (Lv - mu) / sd if sd > 0 else np.nan
                per_fam[fam_name] = {
                    'L_vox': Lv,
                    'z_vox': float(z_vox),
                    'z_combined': float(z_set + z_vox),
                }
            per_var[v] = per_fam
        out[roi] = {
            'L_set': Ls,
            'z_set': float(z_set),
            'variants': per_var,
        }
    return out


def combine_v1_v4(per_roi_results, variant, fam):
    """Selection rule: V1+V4 z_sum."""
    if 'V1' not in per_roi_results or 'V4' not in per_roi_results:
        return None
    z_set_sum = per_roi_results['V1']['z_set'] + per_roi_results['V4']['z_set']
    z_vox_sum = (per_roi_results['V1']['variants'][variant][fam]['z_vox']
                 + per_roi_results['V4']['variants'][variant][fam]['z_vox'])
    return z_set_sum + z_vox_sum


def v4_only(per_roi_results, variant, fam):
    return per_roi_results['V4']['variants'][variant][fam]['z_combined']


# ---------------------------------------------------------------------------
def main():
    results = {'per_target': {}, 'meta': {}}

    # HC LOO
    print('=== HC LOO false positive check (3 variants × 2 families) ===')
    print(f'{"target":<6} {"variant":<7} {"family":<7} {"V4_only":>9} {"V1+V4":>9}  verdict')
    print('-' * 65)
    fp_summary = {v: {f: 0 for f in FAMILIES} for v in ['A', 'B', 'C']}
    for target in HC:
        others = [h for h in HC if h != target]
        pool_stats = {roi: compute_pool_stats(others, roi) for roi in ROIS}
        per_roi = compute_z_for_target(target, pool_stats)
        results['per_target'][f'sub-{target}'] = {
            'role': 'HC',
            'pool_n': len(others),
            'per_roi': per_roi,
        }
        for variant in ['A', 'B', 'C']:
            for fam_name in FAMILIES:
                z_v4 = v4_only(per_roi, variant, fam_name)
                z_combo = combine_v1_v4(per_roi, variant, fam_name)
                verdict = 'FP' if z_combo < -2 else ('marg' if z_combo < -1.5 else 'pass')
                if z_combo < -2:
                    fp_summary[variant][fam_name] += 1
                print(f'sub-{target:<2} {variant:<7} {fam_name:<7} '
                      f'{z_v4:>+9.2f} {z_combo:>+9.2f}  {verdict}')
        print()

    # CVD vs full HC pool (n=6)
    print('=== CVD vs full HC pool (n=6) ===')
    print(f'{"target":<6} {"variant":<7} {"family":<7} {"V4_only":>9} {"V1+V4":>9}  verdict')
    print('-' * 65)
    for target in CVD:
        pool_stats = {roi: compute_pool_stats(HC, roi) for roi in ROIS}
        per_roi = compute_z_for_target(target, pool_stats)
        results['per_target'][f'sub-{target}'] = {
            'role': 'CVD',
            'pool_n': len(HC),
            'per_roi': per_roi,
        }
        for variant in ['A', 'B', 'C']:
            for fam_name in FAMILIES:
                z_v4 = v4_only(per_roi, variant, fam_name)
                z_combo = combine_v1_v4(per_roi, variant, fam_name)
                expected = (target == '08' and fam_name == 'deutan') or \
                           (target == '09' and fam_name == 'protan')
                tag = '←expected' if expected else ''
                verdict = 'detect' if z_combo < -2 else 'miss'
                print(f'sub-{target:<2} {variant:<7} {fam_name:<7} '
                      f'{z_v4:>+9.2f} {z_combo:>+9.2f}  {verdict}  {tag}')
        print()

    # Summary
    print('\n=== FP rate summary (HC LOO, V1+V4 z_combined < -2) ===')
    print(f'{"variant":<10} {"deutan":>8} {"protan":>8}')
    for v in ['A', 'B', 'C']:
        print(f'{v:<10} {fp_summary[v]["deutan"]:>4d}/6 {fp_summary[v]["protan"]:>4d}/6')

    results['meta'] = {
        'cycle': 10,
        'task': 'simplified z_vox-axis comparison',
        'variants': {
            'A': '-(sign·z_mean + |z_rdm_row| + |z_runc|)  [current]',
            'B': '-(sign·z_mean)                            [mean only]',
            'C': '-(sign·z_mean + sign·z_runc)              [signed mean+runc]',
        },
        'selection_rule': 'V1+V4 z_sum (z_set + z_vox)',
        'fp_threshold': -2.0,
        'fp_summary': fp_summary,
    }

    with open(OUT, 'w') as f:
        json.dump(results, f, indent=2)
    print(f'\nSaved: {OUT}')


if __name__ == '__main__':
    main()
