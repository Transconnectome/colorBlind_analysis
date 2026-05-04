#!/usr/bin/env python3
"""cycle7_3way_blend.py — Plan 04 Cycle 7 alt (Task A+B 결합).

Task B (wSpear) 단독은 sub-09 NS — vuln-vector level의 한계 답습.
대안: 3-way blend
  L = α·z_set + β·z_vox(family-aware) + γ·z_wSp
α, β, γ ∈ {0, 0.25, 0.5, 0.75, 1.0}
"""
import json
import numpy as np
from pathlib import Path

ROOT = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/future_phase2_filter_optimization')
RES = ROOT / 'results/cycles'

# Load Task A and Task B results
with open(RES / 'cycle7_dual_criterion.json') as f:
    A = json.load(f)
with open(RES / 'cycle7_blend_wspearman.json') as f:
    B = json.load(f)

ROIS = ['V1', 'V2', 'V4']
CVD = ['08', '09']
SANITY = ['10']

# Build z table per (subj, ROI)
z_table = {}
for s in CVD + SANITY:
    z_table[s] = {}
    for roi in ROIS:
        # Task A z_set, z_vox
        a_cell = A['cvd_per_cell'][s][roi]
        # Task B z_wSp (recompute from rec)
        b_rec = B['rec'][s][roi]
        Lw = b_rec['L_wSpear']
        Lw_mu = B['hc_pool'][roi]['Lw_mu']
        Lw_sd = B['hc_pool'][roi]['Lw_sd']
        z_wSp = (Lw - Lw_mu) / Lw_sd
        z_table[s][roi] = {
            'z_set': a_cell['z_set'],
            'z_vox': a_cell['z_vox'],
            'z_wSp': z_wSp,
        }

# Sweep
roi_configs = {
    'V1_only': ['V1'], 'V2_only': ['V2'], 'V4_only': ['V4'],
    'V1+V4': ['V1', 'V4'], 'V2+V4': ['V2', 'V4'],
}
weights = [0.0, 0.25, 0.5, 0.75, 1.0]

sweep = []
for cfg_name, cfg in roi_configs.items():
    for a in weights:
        for b in weights:
            for g in weights:
                if a == 0 and b == 0 and g == 0:
                    continue
                row = {'cfg': cfg_name, 'a_set': a, 'b_vox': b, 'g_wSp': g}
                for s in CVD + SANITY:
                    z_set_sum = sum(z_table[s][r]['z_set'] for r in cfg)
                    z_vox_sum = sum(z_table[s][r]['z_vox'] for r in cfg)
                    z_wSp_sum = sum(z_table[s][r]['z_wSp'] for r in cfg)
                    z_comb = a * z_set_sum + b * z_vox_sum + g * z_wSp_sum
                    row[f'sub-{s}_zcomb'] = z_comb
                sweep.append(row)

# Common best
common = [r for r in sweep
          if r['sub-08_zcomb'] < -2 and r['sub-09_zcomb'] < -2
          and abs(r['sub-10_zcomb']) < 1.5]
print(f'Total cells: {len(sweep)}, Common best: {len(common)}')

# Filter for cells that have both b>0 (voxel) AND g>0 (wSpear) — true 3-way contribution
true_3way = [r for r in common if r['b_vox'] > 0 and r['g_wSp'] > 0 and r['a_set'] > 0]
print(f'True 3-way (all weights >0): {len(true_3way)}')

# Best-balanced: minimize max(z) while keeping common
common.sort(key=lambda x: max(x['sub-08_zcomb'], x['sub-09_zcomb']))
print('\n=== Top 15 common best (sorted by max CVD z) ===')
print(f'{"cfg":<10} {"αset":>5} {"βvox":>5} {"γwSp":>5} {"z08":>7} {"z09":>7} {"z10":>7}')
for r in common[:15]:
    print(f'{r["cfg"]:<10} {r["a_set"]:>5.2f} {r["b_vox"]:>5.2f} {r["g_wSp"]:>5.2f} '
          f'{r["sub-08_zcomb"]:>+7.2f} {r["sub-09_zcomb"]:>+7.2f} {r["sub-10_zcomb"]:>+7.2f}')

print('\n=== Top 10 true 3-way (all weights >0) ===')
true_3way.sort(key=lambda x: max(x['sub-08_zcomb'], x['sub-09_zcomb']))
for r in true_3way[:10]:
    print(f'{r["cfg"]:<10} {r["a_set"]:>5.2f} {r["b_vox"]:>5.2f} {r["g_wSp"]:>5.2f} '
          f'{r["sub-08_zcomb"]:>+7.2f} {r["sub-09_zcomb"]:>+7.2f} {r["sub-10_zcomb"]:>+7.2f}')

# Selection rule candidate: simplest balanced (small weights, unique ROI)
# Look for V4-inclusive + balanced (a=b=g equal-ish) cells
balanced = [r for r in common
            if 'V4' in r['cfg'] and r['a_set'] > 0 and r['b_vox'] > 0]
balanced.sort(key=lambda x: (-min(abs(x['sub-08_zcomb']), abs(x['sub-09_zcomb']))))
print(f'\n=== V4-inclusive balanced (a>0, b>0, V4 in cfg, sorted by min |z| descending) ===')
print(f'{"cfg":<10} {"αset":>5} {"βvox":>5} {"γwSp":>5} {"z08":>7} {"z09":>7} {"z10":>7}')
for r in balanced[:10]:
    print(f'{r["cfg"]:<10} {r["a_set"]:>5.2f} {r["b_vox"]:>5.2f} {r["g_wSp"]:>5.2f} '
          f'{r["sub-08_zcomb"]:>+7.2f} {r["sub-09_zcomb"]:>+7.2f} {r["sub-10_zcomb"]:>+7.2f}')

out = {'sweep': sweep, 'common_best': common, 'true_3way': true_3way,
       'balanced': balanced, 'z_table': z_table}
out_path = RES / 'cycle7_3way_blend.json'
with open(out_path, 'w') as f:
    json.dump(out, f, indent=2)
print(f'\n[Wrote] {out_path}')
