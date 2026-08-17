#!/usr/bin/env python3
"""Compute voxel-pattern noise ceiling for proper NC-normalized LOCO.

Problem: Current NC uses RDM Spearman r (noise_ceiling_upper/lower from
compute_reliability()), but LOCO metric is voxel Pearson r. Dividing
voxel_corr by RDM_spearman is apples/oranges.

Solution: Compute noise ceiling in voxel-pattern correlation space.

Method:
  For each subject, ROI, color:
    - Split 6 runs into odd (1,3,5) and even (2,4,6)
    - r_sh = corr(mean_odd_pattern, mean_even_pattern)
    - Spearman-Brown: r_full = 2*r_sh / (1 + r_sh)
  Average across 8 colors → noise ceiling per subject × ROI.

  Also compute LOO upper bound:
    For each run r, LOO_mean = mean(other 5 runs)
    r_upper = corr(Y_r, LOO_mean)
    Average across runs and colors.
"""

import json
import numpy as np
from pathlib import Path
from scipy.stats import pearsonr

DATA_DIR = Path(__file__).resolve().parent.parent.parent / \
    'phase1_preprocess_decoding' / 'results' / 'full_dataset_C010'
OUT_DIR = Path(__file__).resolve().parent.parent / 'results' / 'voxel_noise_ceiling'
OUT_DIR.mkdir(parents=True, exist_ok=True)

ROIS = ['V1', 'V2', 'V3', 'V4']  # V4 = hV4 on disk
ROI_NAMES = ['V1', 'V2', 'V3', 'hV4']
HC = [f'sub-{i:02d}' for i in range(1, 8)]
CVD = [f'sub-{i:02d}' for i in range(8, 11)]
ALL = HC + CVD


def load_amplitudes(subject, roi_dir):
    """Load amplitudes_procrustes.npy → shape (6, 8, n_voxels)."""
    path = DATA_DIR / subject / roi_dir / 'amplitudes_procrustes.npy'
    if not path.exists():
        return None
    return np.load(path)


def compute_split_half_voxel_nc(data):
    """Split-half voxel-pattern noise ceiling.

    Args:
        data: (6, 8, n_voxels) — 6 runs, 8 colors, V voxels

    Returns:
        dict with r_sh (raw split-half), r_sb (Spearman-Brown corrected),
        per_color_r_sh, per_color_r_sb
    """
    n_runs, n_colors, n_voxels = data.shape

    odd_idx = [0, 2, 4]   # runs 1, 3, 5
    even_idx = [1, 3, 5]  # runs 2, 4, 6

    per_color_r_sh = []
    per_color_r_sb = []

    for c in range(n_colors):
        odd_mean = data[odd_idx, c, :].mean(axis=0)   # (V,)
        even_mean = data[even_idx, c, :].mean(axis=0)  # (V,)

        # Check for zero variance
        if np.std(odd_mean) < 1e-10 or np.std(even_mean) < 1e-10:
            per_color_r_sh.append(np.nan)
            per_color_r_sb.append(np.nan)
            continue

        r_sh, _ = pearsonr(odd_mean, even_mean)
        # Spearman-Brown correction for full-data reliability
        r_sb = 2 * r_sh / (1 + r_sh) if (1 + r_sh) > 1e-10 else np.nan

        per_color_r_sh.append(r_sh)
        per_color_r_sb.append(r_sb)

    return {
        'r_sh': float(np.nanmean(per_color_r_sh)),
        'r_sb': float(np.nanmean(per_color_r_sb)),
        'per_color_r_sh': [float(x) for x in per_color_r_sh],
        'per_color_r_sb': [float(x) for x in per_color_r_sb],
    }


def compute_loo_voxel_nc(data):
    """LOO voxel-pattern noise ceiling (upper bound).

    For each run r: LOO_mean = mean(other 5 runs)
    r_upper = corr(Y_r, LOO_mean) per color, averaged.

    This is the upper bound: best achievable correlation when comparing
    a prediction to a single run (but we compare to 6-run mean in LOCO,
    so split-half is more appropriate as NC_lower).
    """
    n_runs, n_colors, n_voxels = data.shape

    per_color_loo = []
    for c in range(n_colors):
        run_corrs = []
        for r in range(n_runs):
            y_r = data[r, c, :]
            loo_mean = np.delete(data[:, c, :], r, axis=0).mean(axis=0)

            if np.std(y_r) < 1e-10 or np.std(loo_mean) < 1e-10:
                continue

            rr, _ = pearsonr(y_r, loo_mean)
            run_corrs.append(rr)

        per_color_loo.append(np.mean(run_corrs) if run_corrs else np.nan)

    return {
        'r_loo_upper': float(np.nanmean(per_color_loo)),
        'per_color_r_loo': [float(x) for x in per_color_loo],
    }


def compute_full_mean_nc(data):
    """NC for comparison with 6-run mean (what LOCO actually uses).

    LOCO compares prediction to mean(6 runs) for held-out color.
    NC = what's the best correlation any model can achieve with the 6-run mean?

    Approach: Split-half, where each half is a 3-run mean.
    The 6-run mean reliability ≈ Spearman-Brown corrected split-half.
    """
    # Already computed in compute_split_half_voxel_nc
    # r_sb IS the estimated reliability of the full-data mean
    return compute_split_half_voxel_nc(data)


# ============================================================================
# Main
# ============================================================================
results = {}

for subj in ALL:
    results[subj] = {}
    for roi_dir, roi_name in zip(ROIS, ROI_NAMES):
        data = load_amplitudes(subj, roi_dir)
        if data is None:
            print(f'  {subj} {roi_name}: data not found, skipping')
            continue

        sh = compute_split_half_voxel_nc(data)
        loo = compute_loo_voxel_nc(data)

        results[subj][roi_name] = {
            'n_voxels': int(data.shape[2]),
            'split_half_r': sh['r_sh'],
            'spearman_brown_r': sh['r_sb'],
            'loo_upper_r': loo['r_loo_upper'],
            'per_color_split_half': sh['per_color_r_sh'],
            'per_color_spearman_brown': sh['per_color_r_sb'],
            'per_color_loo_upper': loo['per_color_r_loo'],
        }

        print(f'  {subj} {roi_name}: r_sh={sh["r_sh"]:.3f}  '
              f'r_sb={sh["r_sb"]:.3f}  r_loo={loo["r_loo_upper"]:.3f}  '
              f'({data.shape[2]} voxels)')

# Save per-subject results
out_path = OUT_DIR / 'voxel_noise_ceiling_all.json'
with open(out_path, 'w') as f:
    json.dump(results, f, indent=2)
print(f'\nSaved: {out_path}')


# ============================================================================
# Summary tables
# ============================================================================
print('\n' + '=' * 90)
print('TABLE 1: Split-Half Voxel-Pattern Noise Ceiling (r_sh)')
print('=' * 90)
header = f'{"Subject":>10}'
for roi in ROI_NAMES:
    header += f'  {roi:>8}'
print(header)
print('-' * 50)

for subj in ALL:
    line = f'{subj:>10}'
    for roi in ROI_NAMES:
        if roi in results[subj]:
            line += f'  {results[subj][roi]["split_half_r"]:>8.3f}'
        else:
            line += f'  {"N/A":>8}'
    print(line)

# Group means
for group_name, group in [('HC', HC), ('CVD', CVD)]:
    line = f'{group_name + " Mean":>10}'
    for roi in ROI_NAMES:
        vals = [results[s][roi]['split_half_r'] for s in group
                if roi in results[s]]
        if vals:
            line += f'  {np.mean(vals):>8.3f}'
        else:
            line += f'  {"N/A":>8}'
    print(line)


print(f'\n{"=" * 90}')
print('TABLE 2: Spearman-Brown Corrected Voxel NC (r_sb = estimated full-data reliability)')
print('=' * 90)
header = f'{"Subject":>10}'
for roi in ROI_NAMES:
    header += f'  {roi:>8}'
print(header)
print('-' * 50)

for subj in ALL:
    line = f'{subj:>10}'
    for roi in ROI_NAMES:
        if roi in results[subj]:
            line += f'  {results[subj][roi]["spearman_brown_r"]:>8.3f}'
        else:
            line += f'  {"N/A":>8}'
    print(line)

for group_name, group in [('HC', HC), ('CVD', CVD)]:
    line = f'{group_name + " Mean":>10}'
    for roi in ROI_NAMES:
        vals = [results[s][roi]['spearman_brown_r'] for s in group
                if roi in results[s]]
        if vals:
            line += f'  {np.mean(vals):>8.3f}'
        else:
            line += f'  {"N/A":>8}'
    print(line)


# ============================================================================
# NC-normalized LOCO (proper)
# ============================================================================
print(f'\n{"=" * 90}')
print('TABLE 3: NC-Normalized LOCO voxel_corr (LOCO_r / NC_voxel_r_sb)')
print('  NC = Spearman-Brown corrected split-half voxel-pattern reliability')
print('=' * 90)

# Load LOCO results from validation
VAL_DIR = Path(__file__).resolve().parent.parent / 'results' / 'validation'

loco_data = {}
for subj_id in [f'{i:02d}' for i in range(1, 11)]:
    subj = f'sub-{subj_id}'
    # Try multiple file patterns
    for pattern in [f'{subj}_loco.json', f'{subj}_validation.json']:
        path = VAL_DIR / pattern
        if path.exists():
            with open(path) as f:
                d = json.load(f)
            loco_data[subj] = d
            break

if loco_data:
    header = f'{"Subject":>10}  {"Group":>5}'
    for roi in ROI_NAMES:
        header += f'  {roi:>10}'
    print(header)
    print('-' * 70)

    group_vals = {roi: {'HC': [], 'CVD': []} for roi in ROI_NAMES}

    # Mapping: display name → JSON key in validation files
    roi_to_json_key = {'V1': 'V1', 'V2': 'V2', 'V3': 'V3', 'hV4': 'V4'}

    for subj in ALL:
        group = 'HC' if subj in HC else 'CVD'
        line = f'{subj:>10}  {group:>5}'

        for roi in ROI_NAMES:
            json_key = roi_to_json_key[roi]
            loco_r = None
            nc_r = None

            if subj in loco_data:
                d = loco_data[subj]
                if json_key in d:
                    roi_d = d[json_key]
                    if 'ridge_gcv' in roi_d:
                        loco_r = roi_d['ridge_gcv'].get('mean_voxel_corr')

            if roi in results.get(subj, {}):
                nc_r = results[subj][roi]['spearman_brown_r']

            if loco_r is not None and nc_r is not None and nc_r > 0.01:
                normalized = loco_r / nc_r
                line += f'  {normalized:>10.3f}'
                group_vals[roi][group].append(normalized)
            else:
                line += f'  {"N/A":>10}'
        print(line)

    print('-' * 70)
    for group_name in ['HC', 'CVD']:
        line = f'{group_name + " Mean":>10}  {"":>5}'
        for roi in ROI_NAMES:
            vals = group_vals[roi][group_name]
            if vals:
                line += f'  {np.mean(vals):>10.3f}'
            else:
                line += f'  {"N/A":>10}'
        print(line)

    # HC Mean (SD)
    line = f'{"HC M(SD)":>10}  {"":>5}'
    for roi in ROI_NAMES:
        vals = group_vals[roi]['HC']
        if vals:
            line += f'  {np.mean(vals):+.3f}({np.std(vals,ddof=1):.2f})'
        else:
            line += f'  {"N/A":>10}'
    print(line)

else:
    print('  No validation LOCO data found. Skipping normalized table.')
    print(f'  Looked in: {VAL_DIR}')
    print('  Available files:')
    if VAL_DIR.exists():
        for f in sorted(VAL_DIR.iterdir()):
            print(f'    {f.name}')
