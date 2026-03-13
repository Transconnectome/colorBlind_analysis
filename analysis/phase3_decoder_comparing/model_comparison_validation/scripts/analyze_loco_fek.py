#!/usr/bin/env python3
"""
analyze_loco_fek.py — Analyze LOCO FE-K retry results.

Compares FE-6 vs FE-K MAE and checks if HC-CVD gap survives.

Usage:
    python analyze_loco_fek.py \
        --results_dir ../results/loco_fek_retry
"""

import json
import argparse
import numpy as np
from pathlib import Path
from scipy import stats

HC_SUBJECTS = [f'{i:02d}' for i in range(1, 8)]
CVD_SUBJECTS = [f'{i:02d}' for i in range(8, 11)]
ROIS = ['V1', 'V2', 'V3', 'V4']
ROI_DISPLAY = {'V1': 'V1', 'V2': 'V2', 'V3': 'V3', 'V4': 'hV4'}


def load_results(results_dir):
    data = {}
    for sub in HC_SUBJECTS + CVD_SUBJECTS:
        path = results_dir / f'sub-{sub}_loco_fek.json'
        if path.exists():
            with open(path) as f:
                data[sub] = json.load(f)
    return data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--results_dir', type=str, required=True)
    args = parser.parse_args()
    results_dir = Path(args.results_dir)
    data = load_results(results_dir)
    print(f"Loaded {len(data)} subjects from {results_dir}")

    # === 1. MAE Comparison Table ===
    print("\n" + "=" * 90)
    print("LOCO MAE: FE-6 vs FE-K (per-ROI optimal)")
    print("=" * 90)

    for roi in ROIS:
        name = ROI_DISPLAY[roi]
        k = data[list(data.keys())[0]]['results'].get(roi, {}).get('n_channels_optimal', '?')
        print(f"\n--- {name} (K={k}) ---")
        print(f"{'Subject':>10} | {'FE-6 MAE':>10} | {'FE-K MAE':>10} | {'Δ MAE':>8} | "
              f"{'FE-6 vc':>8} | {'FE-K vc':>8} | {'Δ vc':>8}")
        print("-" * 80)

        hc_mae6, hc_maek, hc_vc6, hc_vck = [], [], [], []
        cvd_mae6, cvd_maek, cvd_vc6, cvd_vck = [], [], [], []

        for sub in HC_SUBJECTS + CVD_SUBJECTS:
            if sub not in data or roi not in data[sub]['results']:
                continue
            r = data[sub]['results'][roi]
            m6 = r['fe6']['overall_mae']
            mk = r['fek']['overall_mae']
            v6 = r['fe6']['overall_voxel_corr']
            vk = r['fek']['overall_voxel_corr']
            group = "HC" if sub in HC_SUBJECTS else "CVD"
            print(f"  {group}-{sub} | {m6:10.1f}° | {mk:10.1f}° | {mk-m6:+7.1f}° | "
                  f"{v6:+.4f} | {vk:+.4f} | {vk-v6:+.4f}")

            if sub in HC_SUBJECTS:
                hc_mae6.append(m6); hc_maek.append(mk)
                hc_vc6.append(v6); hc_vck.append(vk)
            else:
                cvd_mae6.append(m6); cvd_maek.append(mk)
                cvd_vc6.append(v6); cvd_vck.append(vk)

        print("-" * 80)
        if hc_mae6:
            print(f"  HC mean  | {np.mean(hc_mae6):10.1f}° | {np.mean(hc_maek):10.1f}° | "
                  f"{np.mean(hc_maek)-np.mean(hc_mae6):+7.1f}° | "
                  f"{np.mean(hc_vc6):+.4f} | {np.mean(hc_vck):+.4f} | "
                  f"{np.mean(hc_vck)-np.mean(hc_vc6):+.4f}")
        if cvd_mae6:
            print(f"  CVD mean | {np.mean(cvd_mae6):10.1f}° | {np.mean(cvd_maek):10.1f}° | "
                  f"{np.mean(cvd_maek)-np.mean(cvd_mae6):+7.1f}° | "
                  f"{np.mean(cvd_vc6):+.4f} | {np.mean(cvd_vck):+.4f} | "
                  f"{np.mean(cvd_vck)-np.mean(cvd_vc6):+.4f}")

    # === 2. HC-CVD Gap: FE-6 vs FE-K ===
    print("\n" + "=" * 90)
    print("HC-CVD GAP COMPARISON: FE-6 vs FE-K")
    print("=" * 90)
    print(f"\n{'ROI':>5} | {'Metric':>8} | {'HC M(SD)':>14} | {'CVD M(SD)':>14} | "
          f"{'d':>6} | {'p(Welch)':>9} | {'Sig':>3}")
    print("-" * 80)

    for roi in ROIS:
        name = ROI_DISPLAY[roi]
        hc_m6, cvd_m6, hc_mk, cvd_mk = [], [], [], []
        hc_v6, cvd_v6, hc_vk, cvd_vk = [], [], [], []

        for sub in HC_SUBJECTS:
            if sub in data and roi in data[sub]['results']:
                hc_m6.append(data[sub]['results'][roi]['fe6']['overall_mae'])
                hc_mk.append(data[sub]['results'][roi]['fek']['overall_mae'])
                hc_v6.append(data[sub]['results'][roi]['fe6']['overall_voxel_corr'])
                hc_vk.append(data[sub]['results'][roi]['fek']['overall_voxel_corr'])
        for sub in CVD_SUBJECTS:
            if sub in data and roi in data[sub]['results']:
                cvd_m6.append(data[sub]['results'][roi]['fe6']['overall_mae'])
                cvd_mk.append(data[sub]['results'][roi]['fek']['overall_mae'])
                cvd_v6.append(data[sub]['results'][roi]['fe6']['overall_voxel_corr'])
                cvd_vk.append(data[sub]['results'][roi]['fek']['overall_voxel_corr'])

        if not hc_m6 or not cvd_m6:
            continue

        hc_m6 = np.array(hc_m6); cvd_m6 = np.array(cvd_m6)
        hc_mk = np.array(hc_mk); cvd_mk = np.array(cvd_mk)
        hc_v6 = np.array(hc_v6); cvd_v6 = np.array(cvd_v6)
        hc_vk = np.array(hc_vk); cvd_vk = np.array(cvd_vk)

        # MAE gap (lower is better → positive d means HC better)
        for label, hc, cvd in [('MAE FE-6', hc_m6, cvd_m6),
                                ('MAE FE-K', hc_mk, cvd_mk),
                                ('vc FE-6', hc_v6, cvd_v6),
                                ('vc FE-K', hc_vk, cvd_vk)]:
            t, p = stats.ttest_ind(hc, cvd, equal_var=False)
            pooled_sd = np.sqrt((hc.std()**2 + cvd.std()**2) / 2)
            d = (hc.mean() - cvd.mean()) / pooled_sd if pooled_sd > 0 else 0
            sig = '*' if p < 0.05 else ''
            print(f"  {name:>3} | {label:>8} | {hc.mean():+7.1f}({hc.std():5.1f}) | "
                  f"{cvd.mean():+7.1f}({cvd.std():5.1f}) | {d:+5.2f} | {p:9.3f} | {sig}")

    # === 3. HC Paired t-test: FE-K vs FE-6 ===
    print("\n" + "=" * 90)
    print("HC PAIRED t-TEST: FE-K vs FE-6")
    print("=" * 90)
    print(f"\n{'ROI':>5} | {'Metric':>8} | {'Δ M(SD)':>14} | {'t(6)':>7} | {'p':>7}")
    print("-" * 55)

    for roi in ROIS:
        name = ROI_DISPLAY[roi]
        hc_dm, hc_dv = [], []
        for sub in HC_SUBJECTS:
            if sub in data and roi in data[sub]['results']:
                r = data[sub]['results'][roi]
                hc_dm.append(r['fek']['overall_mae'] - r['fe6']['overall_mae'])
                hc_dv.append(r['fek']['overall_voxel_corr'] - r['fe6']['overall_voxel_corr'])

        if len(hc_dm) < 3:
            continue
        hc_dm = np.array(hc_dm); hc_dv = np.array(hc_dv)

        t_m, p_m = stats.ttest_1samp(hc_dm, 0)
        t_v, p_v = stats.ttest_1samp(hc_dv, 0)
        print(f"  {name:>3} | {'MAE':>8} | {hc_dm.mean():+7.1f}({hc_dm.std():5.1f}) | "
              f"{t_m:7.3f} | {p_m:.3f}")
        print(f"  {'':>3} | {'vc':>8} | {hc_dv.mean():+.4f}({hc_dv.std():.4f}) | "
              f"{t_v:7.3f} | {p_v:.3f}")

    # === 4. Save summary ===
    summary = {}
    for roi in ROIS:
        roi_summary = {}
        for sub in HC_SUBJECTS + CVD_SUBJECTS:
            if sub in data and roi in data[sub]['results']:
                r = data[sub]['results'][roi]
                roi_summary[sub] = {
                    'group': 'hc' if sub in HC_SUBJECTS else 'cvd',
                    'fe6_mae': r['fe6']['overall_mae'],
                    'fek_mae': r['fek']['overall_mae'],
                    'fe6_vc': r['fe6']['overall_voxel_corr'],
                    'fek_vc': r['fek']['overall_voxel_corr'],
                    'delta_mae': r['delta_mae'],
                    'delta_vc': r['delta_voxel_corr']
                }
        summary[roi] = roi_summary

    out_file = results_dir / 'loco_fek_summary.json'
    with open(out_file, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"\nSummary saved: {out_file}")


if __name__ == '__main__':
    main()
