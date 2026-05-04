#!/usr/bin/env python3
"""cycle8_preimage.py — pre-image stimulus filter under Cycle 7 selection rule."""
import json
import numpy as np
from pathlib import Path

ROOT = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/future_phase2_filter_optimization')
RES = ROOT / 'results/cycles'

CONF_AXIS = {'protan': 16.0, 'deutan': 150.0}
HUE_8 = np.array([0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0])
COLOR_NAMES = ['red', 'orange', 'yellow', 'green', 'cyan', 'blue', 'purple', 'magenta']
SUBJ_FAMILY = {'08': 'deutan', '09': 'protan'}


def forward_T_arr(grid, bs, bc, family):
    theta_conf = CONF_AXIS[family]
    dt = bs * np.cos(np.deg2rad(grid - 90.0)) + bc * np.cos(np.deg2rad(grid - theta_conf))
    return (grid + dt) % 360.0


def find_inverse(theta_obs, bs, bc, family, n_search=3600, max_shift=90.0):
    grid = np.linspace(0.0, 360.0, n_search, endpoint=False)
    Tg = forward_T_arr(grid, bs, bc, family)
    diff = np.rad2deg(np.angle(np.exp(1j * np.deg2rad(Tg - theta_obs))))
    delta = np.rad2deg(np.angle(np.exp(1j * np.deg2rad(grid - theta_obs))))
    abs_diff = np.abs(diff)
    abs_delta = np.abs(delta)
    in_window = abs_delta <= max_shift
    if np.any(in_window):
        candidates = np.where(in_window)[0]
        local_min = candidates[np.argmin(abs_diff[candidates])]
    else:
        local_min = int(np.argmin(abs_diff))
    return float(grid[local_min]), float(abs_diff[local_min]), bool(np.any(in_window))


def get_boot(subj, roi):
    p = RES / 'bootstrap_server' / f'sub-{subj}_{roi}.json'
    if not p.exists():
        return None
    with open(p) as f:
        d = json.load(f)
    s = d['bootstrap_summary']
    return {
        'bs_med': s['best_bs']['median'], 'bc_med': s['best_bc']['median'],
        'bs_iqr': s['best_bs']['iqr'], 'bc_iqr': s['best_bc']['iqr'],
        'l_topk_med': s['l_topk']['median'], 'rho_med': s['rho_at_best']['median'],
    }


def compute_table(subj, family, bs, bc):
    rows = []
    for i, theta in enumerate(HUE_8):
        pre, err, in_win = find_inverse(theta, bs, bc, family)
        shift = ((pre - theta + 180.0) % 360.0) - 180.0
        rows.append({
            'color_idx': i, 'color_name': COLOR_NAMES[i],
            'theta_obs': float(theta), 'theta_preimage': pre,
            'delta_shift_deg': float(shift),
            'inverse_residual_deg': err,
            'in_window_90deg': in_win,
        })
    return rows


def main():
    out = {'config': {
        'forward_model': 'T(θ) = θ + β_s·cos(θ-90) + β_c·cos(θ-θ_conf)',
        'conf_axis': CONF_AXIS,
        'param_source': 'Cycle 6s server bootstrap median (n_boot=200)',
        'inverse_constraint': 'max_shift=90° from theta_obs',
    }, 'subjects': {}}

    for subj in ['08', '09']:
        family = SUBJ_FAMILY[subj]
        params = {roi: get_boot(subj, roi) for roi in ['V1', 'V2', 'V4']}
        out['subjects'][subj] = {'family': family, 'bootstrap_params': params}

        v4 = params['V4']
        if v4:
            rows = compute_table(subj, family, v4['bs_med'], v4['bc_med'])
            out['subjects'][subj]['preimage_V4_only'] = {
                'used_bs': v4['bs_med'], 'used_bc': v4['bc_med'], 'rows': rows,
            }

        v1 = params['V1']
        if v1 and v4:
            bs = (v1['bs_med'] + v4['bs_med']) / 2.0
            bc = (v1['bc_med'] + v4['bc_med']) / 2.0
            rows = compute_table(subj, family, bs, bc)
            out['subjects'][subj]['preimage_V1V4_avg'] = {
                'used_bs': float(bs), 'used_bc': float(bc), 'rows': rows,
            }

    out_path = RES / 'cycle8_preimage.json'
    with open(out_path, 'w') as f:
        json.dump(out, f, indent=2)
    print(f'[Wrote] {out_path}')

    for subj in ['08', '09']:
        s = out['subjects'][subj]
        print(f'\n=== sub-{subj} ({s["family"]}) ===')
        for key in ['preimage_V4_only', 'preimage_V1V4_avg']:
            if key not in s:
                continue
            p = s[key]
            tag = key.replace('preimage_', '')
            print(f'  {tag}: β_s={p["used_bs"]:.1f}, β_c={p["used_bc"]:.1f}')
            print(f'    {"color":<10} {"obs°":>6} {"pre°":>6} {"shift°":>7} {"err°":>6} {"in_win":>6}')
            for r in p['rows']:
                print(f'    {r["color_name"]:<10} {r["theta_obs"]:>6.1f} '
                      f'{r["theta_preimage"]:>6.1f} {r["delta_shift_deg"]:>+7.2f} '
                      f'{r["inverse_residual_deg"]:>6.3f} {str(r["in_window_90deg"]):>6}')


if __name__ == '__main__':
    main()
