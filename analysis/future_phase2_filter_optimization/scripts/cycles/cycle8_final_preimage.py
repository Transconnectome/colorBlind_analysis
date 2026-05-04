#!/usr/bin/env python3
"""cycle8_final_preimage.py — Final pre-image filter under revised selection rule.

Subject-specific ROI:
  sub-08 (deutan): V4 single-ROI
  sub-09 (protan): V1+V4 결합 (β_s, β_c) bootstrap median 평균

Source for (β_s, β_c) point estimates:
  Cycle 6s server bootstrap (n_boot=200, results/cycles/bootstrap_server)
"""
import json, numpy as np
from pathlib import Path

ROOT = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/future_phase2_filter_optimization')
RES = ROOT / 'results/cycles'

CONF_AXIS = {'protan': 16.0, 'deutan': 150.0}
HUE_8 = np.array([0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0])
COLOR = ['red','orange','yellow','green','cyan','blue','purple','magenta']

# Selection rule: subject-specific ROI based on overlap analysis
SELECTION = {
    '08': {'family': 'deutan', 'rois': ['V4'], 'rationale': 'V4 single-ROI (sub-04 V1 catastrophic tail bypass)'},
    '09': {'family': 'protan', 'rois': ['V1', 'V4'], 'rationale': 'V1+V4 결합 (sub-02 narrow LOO 분포 안전)'},
}


def get_boot_params(subj, roi):
    """Cycle 6s server bootstrap (n=200) median 사용."""
    p = RES / 'bootstrap_server' / f'sub-{subj}_{roi}.json'
    if not p.exists(): return None
    with open(p) as f: d = json.load(f)
    s = d['bootstrap_summary']
    return {
        'bs_med': s['best_bs']['median'], 'bc_med': s['best_bc']['median'],
        'bs_iqr': s['best_bs']['iqr'], 'bc_iqr': s['best_bc']['iqr'],
        'l_topk_med': s['l_topk']['median'], 'rho_med': s['rho_at_best']['median'],
    }


def forward_T(grid, bs, bc, family):
    theta_conf = CONF_AXIS[family]
    dt = bs * np.cos(np.deg2rad(grid - 90.0)) + bc * np.cos(np.deg2rad(grid - theta_conf))
    return (grid + dt) % 360.0


def find_inverse(theta_obs, bs, bc, family, n_search=3600, max_shift=90.0):
    grid = np.linspace(0.0, 360.0, n_search, endpoint=False)
    Tg = forward_T(grid, bs, bc, family)
    diff = np.rad2deg(np.angle(np.exp(1j * np.deg2rad(Tg - theta_obs))))
    delta = np.rad2deg(np.angle(np.exp(1j * np.deg2rad(grid - theta_obs))))
    abs_diff = np.abs(diff); abs_delta = np.abs(delta)
    in_window = abs_delta <= max_shift
    if np.any(in_window):
        cand = np.where(in_window)[0]
        local_min = cand[np.argmin(abs_diff[cand])]
    else:
        local_min = int(np.argmin(abs_diff))
    return float(grid[local_min]), float(abs_diff[local_min]), bool(np.any(in_window))


def compute_table(subj, family, bs, bc):
    rows = []
    for i, theta in enumerate(HUE_8):
        pre, err, in_win = find_inverse(theta, bs, bc, family)
        shift = ((pre - theta + 180.0) % 360.0) - 180.0
        rows.append({
            'color_idx': i, 'color_name': COLOR[i],
            'theta_obs': float(theta), 'theta_preimage': pre,
            'delta_shift_deg': float(shift),
            'inverse_residual_deg': err, 'in_window_90deg': in_win,
        })
    return rows


def main():
    out = {'config': {
        'forward_model': 'T(θ) = θ + β_s·cos(θ-90) + β_c·cos(θ-θ_conf)',
        'conf_axis': CONF_AXIS,
        'param_source': 'Cycle 6s server bootstrap n=200 median',
        'inverse_constraint': 'max_shift=90° from theta_obs',
        'selection_rule': 'subject-specific ROI per Cycle 8s overlap analysis',
    }, 'subjects': {}}

    for subj in ['08', '09']:
        sel = SELECTION[subj]
        family = sel['family']
        rois = sel['rois']
        params_per_roi = {roi: get_boot_params(subj, roi) for roi in rois}
        # Compute averaged (β_s, β_c)
        bs_list = [p['bs_med'] for p in params_per_roi.values() if p]
        bc_list = [p['bc_med'] for p in params_per_roi.values() if p]
        bs_avg = float(np.mean(bs_list))
        bc_avg = float(np.mean(bc_list))
        rows = compute_table(subj, family, bs_avg, bc_avg)
        out['subjects'][subj] = {
            'family': family, 'rois_used': rois,
            'rationale': sel['rationale'],
            'bootstrap_params_per_roi': params_per_roi,
            'used_bs_avg': bs_avg, 'used_bc_avg': bc_avg,
            'preimage_table': rows,
        }

    out_path = RES / 'cycle8_final_preimage.json'
    with open(out_path, 'w') as f:
        json.dump(out, f, indent=2)
    print(f'[Wrote] {out_path}\n')

    print('='*72)
    print('FINAL PRE-IMAGE TABLE (subject-specific selection rule)')
    print('='*72)
    for subj in ['08', '09']:
        s = out['subjects'][subj]
        print(f"\n=== sub-{subj} ({s['family']}) — ROI: {'+'.join(s['rois_used'])} ===")
        print(f'  Rationale: {s["rationale"]}')
        print(f'  (β_s, β_c) per ROI (cycle 6s n=200 median):')
        for roi, p in s['bootstrap_params_per_roi'].items():
            if p:
                print(f'    {roi}: ({p["bs_med"]:.1f}, {p["bc_med"]:.1f})  '
                      f'IQR=({p["bs_iqr"]:.1f}, {p["bc_iqr"]:.1f})')
        print(f'  → averaged (β_s, β_c) = ({s["used_bs_avg"]:.1f}, {s["used_bc_avg"]:.1f})')
        print()
        print(f'  {"color":<10} {"obs°":>6} {"pre°":>7} {"shift°":>8} {"err°":>6} {"in_win":>6}')
        print('  ' + '-'*48)
        for r in s['preimage_table']:
            shift_marker = '★' if abs(r['delta_shift_deg']) > 20 else ''
            print(f'  {r["color_name"]:<10} {r["theta_obs"]:>6.1f} '
                  f'{r["theta_preimage"]:>7.1f} {r["delta_shift_deg"]:>+8.2f} '
                  f'{r["inverse_residual_deg"]:>6.3f} {str(r["in_window_90deg"]):>6}  {shift_marker}')


if __name__ == '__main__':
    main()
