#!/usr/bin/env python3
"""cycle6_step3_specificity.py — Plan 04 Cycle 6 Step 3.

Cycle 6 Step 1 결과로부터 두 후속:
  (A) magenta z 단독을 sub-09 specificity metric으로 사용 시 분리도
  (B) HC pool 에서 sub-04 (sub-08-like outlier) 제외 시 sub-08 specificity 변화

Step 1 의 aggregate.json 을 재활용. 추가 grid search 없음.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
PHASE2 = HERE.parent.parent
RES = PHASE2 / 'results' / 'cycle_filter_refinement' / 'cycle6_voxel_diag'
OUT = PHASE2 / 'results' / 'cycle_filter_refinement'

ROIS = ['V1', 'V2', 'V4']
HC_SUBS = ['01', '02', '03', '04', '05', '06']  # sub-07 제외 (V4=16voxel catastrophic)
COLOR_NAMES = ['red', 'orange', 'yellow', 'green',
               'cyan', 'blue', 'purple', 'magenta']
MAGENTA = 7
YELLOW = 2


def load_roi(roi):
    p = RES / f'{roi}_summary.json'
    with open(p) as f:
        return json.load(f)


def get_agg(d, subj):
    r = d['per_subject'].get(subj)
    if not r:
        return None
    return np.array(r['agg_per_color']), np.array(r['rdm_z']), r['sigs_z']


def hc_distribution_for_color(roi_data, color_idx, hc_subs):
    """Return |agg_z| at color_idx for each HC LOO."""
    vals = []
    for hc in hc_subs:
        if hc not in roi_data['per_subject']:
            continue
        agg = np.array(roi_data['per_subject'][hc]['agg_per_color'])
        vals.append(agg[color_idx])
    return np.array(vals)


def empirical_p(target, hc_vals):
    """Two-sided emp p (target outlier = larger agg_z = more anomalous)."""
    n = len(hc_vals)
    return (np.sum(hc_vals >= target) + 1) / (n + 1)


def main():
    out = {'config': {'cycle': 6, 'step': 3,
                      'hc_subs_used': HC_SUBS,
                      'note': 'sub-07 excluded (V4=16 voxel catastrophic).'},
           'A_magenta_specificity': {},
           'B_remove_sub04': {}}

    print('\n=== A. Magenta-only specificity (sub-09 sniff test) ===')
    for roi in ROIS:
        d = load_roi(roi)
        # magenta agg_z per subject
        rows = {}
        for s in HC_SUBS + ['08', '09', '10']:
            r = d['per_subject'].get(s)
            if not r:
                continue
            agg = np.array(r['agg_per_color'])
            rdm_z = np.array(r['rdm_z'])
            rows[s] = {
                'agg_magenta': float(agg[MAGENTA]),
                'rdm_row_magenta': float(np.abs(rdm_z[MAGENTA]).mean()),
            }
        hc_mag = np.array([rows[h]['agg_magenta'] for h in HC_SUBS if h in rows])
        for tgt in ('08', '09', '10'):
            if tgt not in rows:
                continue
            v = rows[tgt]['agg_magenta']
            z = (v - hc_mag.mean()) / hc_mag.std(ddof=1)
            p = empirical_p(v, hc_mag)
            rows[tgt]['z_vs_HC_pool'] = float(z)
            rows[tgt]['emp_p'] = float(p)
        out['A_magenta_specificity'][roi] = {
            'rows': rows,
            'hc_pool_mean': float(hc_mag.mean()),
            'hc_pool_std': float(hc_mag.std(ddof=1)),
        }
        print(f'\n  [{roi}] magenta agg_z (HC pool: μ={hc_mag.mean():.2f} ± {hc_mag.std(ddof=1):.2f})')
        for s in HC_SUBS:
            if s in rows:
                print(f'    HC sub-{s}: {rows[s]["agg_magenta"]:.2f}')
        for s in ('08', '09', '10'):
            if s in rows and 'z_vs_HC_pool' in rows[s]:
                tag = 'CVD-09' if s == '09' else ('CVD-08' if s == '08' else 'NORM-10')
                print(f'    {tag}: {rows[s]["agg_magenta"]:.2f}  '
                      f'z={rows[s]["z_vs_HC_pool"]:+.2f}  '
                      f'emp_p={rows[s]["emp_p"]:.3f}')

    print('\n=== B. Remove sub-04 (deutan-like HC outlier) — sub-08 specificity ===')
    for roi in ROIS:
        d = load_roi(roi)
        hc_with = [h for h in HC_SUBS]
        hc_without = [h for h in HC_SUBS if h != '04']
        sub08_agg = np.array(d['per_subject']['08']['agg_per_color'])
        # Use yellow (sub-08 max outlier color in V1/V2)
        for color_idx, color_name in [(YELLOW, 'yellow'), (MAGENTA, 'magenta')]:
            hc_vals_w = hc_distribution_for_color(d, color_idx, hc_with)
            hc_vals_wo = hc_distribution_for_color(d, color_idx, hc_without)
            sv = sub08_agg[color_idx]
            z_w = (sv - hc_vals_w.mean()) / hc_vals_w.std(ddof=1)
            z_wo = (sv - hc_vals_wo.mean()) / hc_vals_wo.std(ddof=1)
            p_w = empirical_p(sv, hc_vals_w)
            p_wo = empirical_p(sv, hc_vals_wo)
            key = f'{roi}_{color_name}'
            out['B_remove_sub04'][key] = {
                'with_sub04': {'mu': float(hc_vals_w.mean()),
                                'sd': float(hc_vals_w.std(ddof=1)),
                                'z_sub08': float(z_w),
                                'p_sub08': float(p_w)},
                'without_sub04': {'mu': float(hc_vals_wo.mean()),
                                   'sd': float(hc_vals_wo.std(ddof=1)),
                                   'z_sub08': float(z_wo),
                                   'p_sub08': float(p_wo)},
                'sub08_value': float(sv),
            }
            print(f'  [{roi} {color_name}] sub-08={sv:.2f}; '
                  f'with sub-04: HC μ={hc_vals_w.mean():.2f} z={z_w:+.2f} p={p_w:.2f}; '
                  f'without: μ={hc_vals_wo.mean():.2f} z={z_wo:+.2f} p={p_wo:.2f}')

    out_path = OUT / 'cycle6_step3_specificity.json'
    with open(out_path, 'w') as f:
        json.dump(out, f, indent=2)
    print(f'\n[Wrote] {out_path}')


if __name__ == '__main__':
    main()
