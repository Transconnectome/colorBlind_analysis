#!/usr/bin/env python3
"""
cardinal_axis_amplitude.py — Post-hoc Tregillus-style univariate amplitude check.

For each subject × ROI:
  1. Mean voxel β per color (signed, run-averaged) — Tregillus β analog
  2. Mean |β| per color (modulation depth)

Then aggregate by axis class:
  - a*-axis (RG cardinal-like): c1 (red) + c5 (cyan)
  - b*-axis (BY cardinal-like): c3 (yellow) + c7 (blue)
  - Diagonal: c2/c4/c6/c8

Compare HC group (mean ± SD across n=7) to each CVD subject (sub-08, 09, 10).

Caveat: our 8-color ring stimuli are NOT cardinal-axis modulations.
Each color projects partially on both axes. This is approximation, not Tregillus-equivalent.
"""

import json
import numpy as np
from pathlib import Path
from scipy import stats

DATA = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/'
            'colorBlind_analysis/analysis/phase1_procrustes_decoding/results/'
            'visualization/full_dataset_C010_with_residuals')

OUT = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/'
           'colorBlind_analysis/analysis/phase5_filter_optimization/'
           'results/cardinal_axis_amplitude')
OUT.mkdir(parents=True, exist_ok=True)

HC = [f'sub-0{i}' for i in range(1, 8)]
CVD = ['sub-08', 'sub-09', 'sub-10']
ROIS = ['V1', 'V2', 'V3', 'V4']  # V4 ≡ hV4 on disk
COLORS = ['c1_red', 'c2_orange', 'c3_yellow', 'c4_yelgrn',
          'c5_cyan', 'c6_blucy', 'c7_blue', 'c8_magenta']
HUES_DEG = [0, 45, 90, 135, 180, 225, 270, 315]

# Cardinal-like pairs in our CIELab ring
A_AXIS = [0, 4]   # c1 + c5  (a*: red ↔ cyan)
B_AXIS = [2, 6]   # c3 + c7  (b*: yellow ↔ blue)
DIAG = [1, 3, 5, 7]  # c2/c4/c6/c8


def load_amp(sub, roi, kind='procrustes'):
    """Return (n_runs, 8, n_vox) array, or None if missing.

    kind: 'procrustes' or 'raw'
    """
    fname = f'amplitudes_{kind}.npy'
    f = DATA / sub / roi / fname
    if not f.exists():
        return None
    return np.load(f)


def compute_metrics(amp):
    """Return per-color signed mean and per-color |β|.

    amp: (n_runs, 8, n_vox)
    """
    if amp is None or amp.size == 0:
        return None
    # Average across runs first (per-color β estimate)
    per_color_run_mean = amp.mean(axis=0)  # (8, n_vox)
    # Drop voxels that are nan across all (sub-07 hV4 known issue)
    valid = ~np.all(np.isnan(per_color_run_mean), axis=0)
    per_color_run_mean = per_color_run_mean[:, valid]
    if per_color_run_mean.shape[1] == 0:
        return None
    # Voxel-mean per color → 8 numbers
    signed_mean = per_color_run_mean.mean(axis=1)  # (8,)
    abs_mean = np.abs(per_color_run_mean).mean(axis=1)  # (8,) — mod depth
    return {
        'signed_mean': signed_mean,
        'abs_mean': abs_mean,
        'n_voxels_valid': int(valid.sum()),
    }


def aggregate_axis(per_color_8):
    """Return (a_axis, b_axis, diag) means."""
    a = per_color_8[A_AXIS].mean()
    b = per_color_8[B_AXIS].mean()
    d = per_color_8[DIAG].mean()
    return a, b, d


def main():
    import sys
    kind = sys.argv[1] if len(sys.argv) > 1 else 'procrustes'
    assert kind in ('procrustes', 'raw'), f'kind must be procrustes or raw, got {kind}'
    print(f'\n>>> Running with amplitudes_{kind}.npy <<<\n')
    results = {}
    for sub in HC + CVD:
        results[sub] = {}
        for roi in ROIS:
            amp = load_amp(sub, roi, kind=kind)
            m = compute_metrics(amp)
            if m is None:
                results[sub][roi] = None
                continue
            sig_a, sig_b, sig_d = aggregate_axis(m['signed_mean'])
            abs_a, abs_b, abs_d = aggregate_axis(m['abs_mean'])
            results[sub][roi] = {
                'n_voxels': m['n_voxels_valid'],
                'signed_per_color': m['signed_mean'].tolist(),
                'abs_per_color': m['abs_mean'].tolist(),
                'signed_a_axis': float(sig_a),
                'signed_b_axis': float(sig_b),
                'signed_diag': float(sig_d),
                'abs_a_axis': float(abs_a),
                'abs_b_axis': float(abs_b),
                'abs_diag': float(abs_d),
            }

    # Aggregate HC across 7 subjects per ROI
    hc_summary = {}
    for roi in ROIS:
        hc_vals = {k: [] for k in ['signed_a_axis', 'signed_b_axis', 'signed_diag',
                                    'abs_a_axis', 'abs_b_axis', 'abs_diag']}
        per_color_signed = []
        per_color_abs = []
        for sub in HC:
            r = results[sub][roi]
            if r is None:
                continue
            for k in hc_vals:
                hc_vals[k].append(r[k])
            per_color_signed.append(r['signed_per_color'])
            per_color_abs.append(r['abs_per_color'])
        hc_summary[roi] = {
            'n_hc': len(per_color_signed),
            'mean': {k: float(np.mean(v)) for k, v in hc_vals.items()},
            'sd': {k: float(np.std(v, ddof=1)) for k, v in hc_vals.items()},
            'per_color_signed_mean': np.mean(per_color_signed, axis=0).tolist(),
            'per_color_signed_sd': np.std(per_color_signed, axis=0, ddof=1).tolist(),
            'per_color_abs_mean': np.mean(per_color_abs, axis=0).tolist(),
            'per_color_abs_sd': np.std(per_color_abs, axis=0, ddof=1).tolist(),
        }

    # CVD vs HC z-scores per axis (using signed values — Tregillus-comparable)
    cvd_z = {}
    for sub in CVD:
        cvd_z[sub] = {}
        for roi in ROIS:
            r = results[sub][roi]
            if r is None:
                continue
            cvd_z[sub][roi] = {}
            for axis in ['signed_a_axis', 'signed_b_axis', 'signed_diag',
                         'abs_a_axis', 'abs_b_axis', 'abs_diag']:
                m = hc_summary[roi]['mean'][axis]
                s = hc_summary[roi]['sd'][axis]
                z = (r[axis] - m) / s if s > 0 else np.nan
                cvd_z[sub][roi][axis] = float(z)

    # Print human-readable summary
    print('=' * 78)
    print('CARDINAL-AXIS UNIVARIATE AMPLITUDE — POST-HOC TREGILLUS APPROXIMATION')
    print('=' * 78)
    print()
    print('Stimulus mapping (CIELab L*=75 C*=40 ring):')
    print('  a*-axis (RG-cardinal-like): c1 (red, 0°)  + c5 (cyan, 180°)')
    print('  b*-axis (BY-cardinal-like): c3 (yellow, 90°) + c7 (blue, 270°)')
    print('  diagonal: c2/c4/c6/c8 (45/135/225/315°)')
    print()
    print('Caveat: Our stimuli are fixed-chroma ring, NOT cardinal modulations.')
    print('  Each color projects partly on both axes (cos45°=0.71). This is a')
    print('  rough comparator, not a literal Tregillus replication.')
    print()
    print('---- HC GROUP (mean ± SD, n_hc per ROI) ----')
    for roi in ROIS:
        s = hc_summary[roi]
        print(f'  {roi} (n_hc={s["n_hc"]}):')
        print(f'    signed amplitude  a*-axis = {s["mean"]["signed_a_axis"]:+.4f} ± {s["sd"]["signed_a_axis"]:.4f}')
        print(f'                       b*-axis = {s["mean"]["signed_b_axis"]:+.4f} ± {s["sd"]["signed_b_axis"]:.4f}')
        print(f'                       diag    = {s["mean"]["signed_diag"]:+.4f} ± {s["sd"]["signed_diag"]:.4f}')
        print(f'    abs (mod depth)   a*-axis = {s["mean"]["abs_a_axis"]:.4f} ± {s["sd"]["abs_a_axis"]:.4f}')
        print(f'                       b*-axis = {s["mean"]["abs_b_axis"]:.4f} ± {s["sd"]["abs_b_axis"]:.4f}')
        print(f'                       diag    = {s["mean"]["abs_diag"]:.4f} ± {s["sd"]["abs_diag"]:.4f}')
    print()
    print('---- CVD INDIVIDUAL z-scores (vs HC mean/SD) ----')
    print('  Tregillus-style key: a*-axis = closest analog to L-vs-M cardinal.')
    print('  z < 0 means CVD < HC (consistent with cone-deficit reduction).')
    print('  z ≈ 0 means CVD indistinguishable from HC (consistent with compensation).')
    print()
    for sub in CVD:
        print(f'  {sub}:')
        for roi in ROIS:
            if roi not in cvd_z[sub]:
                print(f'    {roi}: <missing>')
                continue
            z = cvd_z[sub][roi]
            print(f'    {roi}:  a*-axis z = {z["signed_a_axis"]:+.2f}  '
                  f'b*-axis z = {z["signed_b_axis"]:+.2f}  '
                  f'diag z = {z["signed_diag"]:+.2f}     (mod-depth z: '
                  f'a* {z["abs_a_axis"]:+.2f}, b* {z["abs_b_axis"]:+.2f}, '
                  f'diag {z["abs_diag"]:+.2f})')
        print()

    # Save full JSON
    out_file = OUT / f'summary_{kind}.json'
    with open(out_file, 'w') as f:
        json.dump({
            'per_subject': results,
            'hc_summary': hc_summary,
            'cvd_z_scores': cvd_z,
            'colors': COLORS,
            'hues_deg': HUES_DEG,
            'a_axis_idx': A_AXIS,
            'b_axis_idx': B_AXIS,
            'diag_idx': DIAG,
        }, f, indent=2)
    print(f'Saved: {out_file}')


if __name__ == '__main__':
    main()
