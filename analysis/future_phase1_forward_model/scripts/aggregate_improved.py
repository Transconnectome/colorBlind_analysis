#!/usr/bin/env python3
"""Aggregate improved encoding results across all 10 subjects."""

import json
import numpy as np
from pathlib import Path

RESULT_DIR = Path(__file__).parent.parent / 'results' / 'improved_encoding'
ROIS = ['V1', 'V2', 'V3', 'V4']
HC = [f'{i:02d}' for i in range(1, 8)]
CVD = [f'{i:02d}' for i in range(8, 11)]
ALL = HC + CVD

# Key methods to compare
KEY_METHODS = ['ridge_gcv', 'ridge_rrr_r2', 'ridge_rrr_r3', 'ridge_rrr_r4',
               'ridge_smooth_best']
METRICS = ['mean_voxel_corr', 'mean_id_accuracy', 'mean_weighted_corr',
           'rdm_pred_pearson', 'mean_mae']

# Load all data
data = {}
for subj in ALL:
    path = RESULT_DIR / f'sub-{subj}_improved.json'
    if path.exists():
        with open(path) as f:
            data[subj] = json.load(f)

print(f'Loaded {len(data)} subjects\n')

# ============================================================================
# 1. Method Comparison: All 10 subjects mean per ROI
# ============================================================================
print('=' * 90)
print('TABLE 1: LOCO mean_voxel_corr — All 10 subjects mean (SD)')
print('=' * 90)
header = f'{"Method":>24}'
for roi in ROIS:
    header += f'  {"":>4}{roi:>4}{"":>8}'
print(header)
print('-' * 90)

for method in KEY_METHODS:
    line = f'{method:>24}'
    for roi in ROIS:
        vals = []
        for subj in ALL:
            if subj in data and roi in data[subj] and method in data[subj][roi]:
                vals.append(data[subj][roi][method]['mean_voxel_corr'])
        if vals:
            line += f'  {np.mean(vals):>+7.4f} ({np.std(vals,ddof=1):.3f})'
        else:
            line += f'  {"N/A":>16}'
    print(line)

# Also add combined method
print('\n  Combined methods (per-subject best):')
for roi in ROIS:
    combo_vals = []
    combo_names = []
    for subj in ALL:
        if subj not in data or roi not in data[subj]:
            continue
        # Find combined method key
        combos = {k: v for k, v in data[subj][roi].items()
                  if 'rrr' in k and 'smooth' in k}
        if combos:
            best = max(combos, key=lambda k: combos[k]['mean_voxel_corr'])
            combo_vals.append(combos[best]['mean_voxel_corr'])
            combo_names.append(best)
    if combo_vals:
        print(f'    {roi}: {np.mean(combo_vals):+.4f} ({np.std(combo_vals,ddof=1):.3f})')

# ============================================================================
# 2. All metrics for key comparison
# ============================================================================
print(f'\n{"=" * 90}')
print('TABLE 2: All metrics — All 10 subjects mean')
print('=' * 90)

for roi in ROIS:
    print(f'\n  --- {roi} ---')
    header = f'  {"Method":>24}'
    for metric in METRICS:
        short = metric.replace('mean_', '').replace('rdm_pred_', 'rdm_')[:10]
        header += f'  {short:>10}'
    print(header)
    print('  ' + '-' * 78)

    for method in KEY_METHODS:
        line = f'  {method:>24}'
        for metric in METRICS:
            vals = []
            for subj in ALL:
                if subj in data and roi in data[subj] and method in data[subj][roi]:
                    vals.append(data[subj][roi][method][metric])
            if vals:
                line += f'  {np.mean(vals):>10.4f}'
            else:
                line += f'  {"N/A":>10}'
        print(line)

# ============================================================================
# 3. Best beta per subject × ROI
# ============================================================================
print(f'\n{"=" * 90}')
print('TABLE 3: Best smooth beta per subject × ROI')
print('=' * 90)
header = f'  {"Subject":>8}'
for roi in ROIS:
    header += f'  {roi:>8}'
print(header)
print('  ' + '-' * 44)

for subj in ALL:
    line = f'  sub-{subj:>3}'
    for roi in ROIS:
        if subj in data and roi in data[subj] and 'ridge_smooth_best' in data[subj][roi]:
            beta = data[subj][roi]['ridge_smooth_best'].get('best_beta', '?')
            line += f'  {beta:>8}'
        else:
            line += f'  {"N/A":>8}'
    print(line)

# ============================================================================
# 4. Winner per ROI (which method best?)
# ============================================================================
print(f'\n{"=" * 90}')
print('TABLE 4: Best method per ROI (by mean_voxel_corr across all 10 subjects)')
print('=' * 90)

all_methods_set = set()
for subj in ALL:
    if subj in data:
        for roi in ROIS:
            if roi in data[subj]:
                all_methods_set.update(data[subj][roi].keys())
# Remove non-method keys
all_methods = sorted([m for m in all_methods_set
                      if not m.startswith('ridge_smooth_b')
                      and m != 'ridge_smooth_best'])

for roi in ROIS:
    best_method = None
    best_mean = -999
    for method in KEY_METHODS + ['ridge_smooth_best']:
        vals = []
        for subj in ALL:
            if subj in data and roi in data[subj] and method in data[subj][roi]:
                vals.append(data[subj][roi][method]['mean_voxel_corr'])
        if vals and np.mean(vals) > best_mean:
            best_mean = np.mean(vals)
            best_method = method
    # Also check combined
    combo_vals = []
    for subj in ALL:
        if subj in data and roi in data[subj]:
            combos = {k: v for k, v in data[subj][roi].items()
                      if 'rrr' in k and 'smooth' in k}
            if combos:
                best = max(combos, key=lambda k: combos[k]['mean_voxel_corr'])
                combo_vals.append(combos[best]['mean_voxel_corr'])
    if combo_vals and np.mean(combo_vals) > best_mean:
        best_mean = np.mean(combo_vals)
        best_method = 'combined (best per-subj)'

    print(f'  {roi}: {best_method} → r = {best_mean:+.4f}')

# ============================================================================
# 5. Improvement over baseline (ridge_gcv)
# ============================================================================
print(f'\n{"=" * 90}')
print('TABLE 5: Improvement over ridge_gcv baseline (delta voxel_corr)')
print('=' * 90)
header = f'  {"Method":>24}'
for roi in ROIS:
    header += f'  {roi:>8}'
print(header)
print('  ' + '-' * 60)

for method in KEY_METHODS[1:]:  # skip ridge_gcv itself
    line = f'  {method:>24}'
    for roi in ROIS:
        base_vals = []
        method_vals = []
        for subj in ALL:
            if (subj in data and roi in data[subj]
                    and 'ridge_gcv' in data[subj][roi]
                    and method in data[subj][roi]):
                base_vals.append(data[subj][roi]['ridge_gcv']['mean_voxel_corr'])
                method_vals.append(data[subj][roi][method]['mean_voxel_corr'])
        if base_vals:
            delta = np.mean(method_vals) - np.mean(base_vals)
            line += f'  {delta:>+8.4f}'
        else:
            line += f'  {"N/A":>8}'
    print(line)

# ============================================================================
# 6. Identification accuracy (chance = 12.5%)
# ============================================================================
print(f'\n{"=" * 90}')
print('TABLE 6: Identification accuracy — All 10 subjects mean (chance = 12.5%)')
print('=' * 90)
header = f'  {"Method":>24}'
for roi in ROIS:
    header += f'  {roi:>8}'
print(header)
print('  ' + '-' * 60)

for method in KEY_METHODS:
    line = f'  {method:>24}'
    for roi in ROIS:
        vals = []
        for subj in ALL:
            if subj in data and roi in data[subj] and method in data[subj][roi]:
                vals.append(data[subj][roi][method]['mean_id_accuracy'])
        if vals:
            mean_acc = np.mean(vals) * 100
            line += f'  {mean_acc:>7.1f}%'
        else:
            line += f'  {"N/A":>8}'
    print(line)

print(f'\n  Chance level = 12.5%')
