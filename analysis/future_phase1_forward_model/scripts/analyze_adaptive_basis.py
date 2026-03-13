#!/usr/bin/env python3
"""
analyze_adaptive_basis.py — Aggregate and analyze adaptive basis results.

Runs locally after downloading results from server.
Produces: comparison table, HC vs CVD center analysis, delta summary.

Usage:
    python analyze_adaptive_basis.py \
        --results_dir ../results/adaptive_basis \
        [--output_dir ../results/adaptive_basis]
"""

import argparse
import json
import numpy as np
from pathlib import Path
from scipy import stats

HC_SUBJECTS = [f'{i:02d}' for i in range(1, 8)]
CVD_SUBJECTS = [f'{i:02d}' for i in range(8, 11)]
ALL_SUBJECTS = HC_SUBJECTS + CVD_SUBJECTS
ROIS = ['V1', 'V2', 'V3', 'V4']
ROI_DISPLAY = {'V1': 'V1', 'V2': 'V2', 'V3': 'V3', 'V4': 'hV4'}
OPTIMAL_K = {'V1': 2, 'V2': 3, 'V3': 8, 'V4': 3}


def load_results(results_dir):
    """Load all adaptive basis result JSONs."""
    results = {}
    for sub in ALL_SUBJECTS:
        for roi in ROIS:
            path = results_dir / f'sub-{sub}_{roi}_adaptive.json'
            if path.exists():
                with open(path) as f:
                    results[(sub, roi)] = json.load(f)
    return results


def print_comparison_table(results):
    """Print fixed vs adaptive LOCO comparison."""
    print("\n" + "=" * 80)
    print("FIXED vs ADAPTIVE LOCO voxel_corr (mean across LOCO folds)")
    print("=" * 80)

    # Header
    header = f"{'Subject':>10}"
    for roi in ROIS:
        k = OPTIMAL_K[roi]
        name = ROI_DISPLAY[roi]
        header += f" | {name}(K={k}) Fixed  Adapt  Delta"
    print(header)
    print("-" * len(header))

    for sub in ALL_SUBJECTS:
        group = "HC" if sub in HC_SUBJECTS else "CVD"
        line = f"  {group}-{sub}"
        for roi in ROIS:
            key = (sub, roi)
            if key in results:
                r = results[key]
                fixed = r['fixed']['loco_mean']
                adapt = r['adaptive']['loco_mean']
                delta = r['adaptive']['delta']
                sign = '+' if delta >= 0 else ''
                line += f" |    {fixed:6.3f}  {adapt:6.3f} {sign}{delta:.3f}"
            else:
                line += f" |      ---    ---    ---"
        print(line)

    # Group means
    print("-" * len(header))
    for group_name, group_subs in [("HC mean", HC_SUBJECTS),
                                    ("CVD mean", CVD_SUBJECTS)]:
        line = f"{group_name:>10}"
        for roi in ROIS:
            fixeds, adapts, deltas = [], [], []
            for sub in group_subs:
                key = (sub, roi)
                if key in results:
                    fixeds.append(results[key]['fixed']['loco_mean'])
                    adapts.append(results[key]['adaptive']['loco_mean'])
                    deltas.append(results[key]['adaptive']['delta'])
            if fixeds:
                mf = np.mean(fixeds)
                ma = np.mean(adapts)
                md = np.mean(deltas)
                sign = '+' if md >= 0 else ''
                line += f" |    {mf:6.3f}  {ma:6.3f} {sign}{md:.3f}"
            else:
                line += f" |      ---    ---    ---"
        print(line)


def print_center_analysis(results):
    """Analyze optimized centers: HC vs CVD patterns."""
    print("\n" + "=" * 80)
    print("OPTIMIZED BASIS CENTERS (degrees)")
    print("=" * 80)

    for roi in ROIS:
        k = OPTIMAL_K[roi]
        name = ROI_DISPLAY[roi]
        print(f"\n--- {name} (K={k}) ---")
        uniform = np.linspace(0, 360, k, endpoint=False)
        print(f"  Uniform: {np.array2string(uniform, precision=1)}")

        hc_centers = []
        cvd_centers = []
        for sub in ALL_SUBJECTS:
            key = (sub, roi)
            if key not in results:
                continue
            centers = np.array(results[key]['adaptive']['centers'])
            group = "HC" if sub in HC_SUBJECTS else "CVD"
            tag = f"  {group}-{sub}: {np.array2string(centers, precision=1)}"

            spacings = np.array(results[key]['adaptive']['spacings'])
            tag += f"  spacings={np.array2string(spacings, precision=1)}"
            print(tag)

            if sub in HC_SUBJECTS:
                hc_centers.append(centers)
            else:
                cvd_centers.append(centers)

        if hc_centers:
            hc_mean = np.mean(hc_centers, axis=0)
            hc_std = np.std(hc_centers, axis=0)
            print(f"  HC  mean: {np.array2string(hc_mean, precision=1)} "
                  f"+/- {np.array2string(hc_std, precision=1)}")
        if cvd_centers:
            cvd_mean = np.mean(cvd_centers, axis=0)
            cvd_std = np.std(cvd_centers, axis=0)
            print(f"  CVD mean: {np.array2string(cvd_mean, precision=1)} "
                  f"+/- {np.array2string(cvd_std, precision=1)}")

        # Test HC vs CVD center differences
        if len(hc_centers) >= 3 and len(cvd_centers) >= 2:
            hc_arr = np.array(hc_centers)
            cvd_arr = np.array(cvd_centers)
            for ch in range(k):
                t, p = stats.ttest_ind(hc_arr[:, ch], cvd_arr[:, ch],
                                       equal_var=False)
                if p < 0.1:
                    print(f"    Channel {ch}: HC={hc_arr[:, ch].mean():.1f} "
                          f"vs CVD={cvd_arr[:, ch].mean():.1f}, "
                          f"t={t:.2f}, p={p:.3f}{'*' if p < 0.05 else ''}")


def print_delta_statistics(results):
    """Statistical test: does adaptive basis improve over fixed?"""
    print("\n" + "=" * 80)
    print("DELTA STATISTICS (adaptive - fixed)")
    print("=" * 80)

    for roi in ROIS:
        name = ROI_DISPLAY[roi]
        k = OPTIMAL_K[roi]

        hc_deltas = []
        cvd_deltas = []
        for sub in ALL_SUBJECTS:
            key = (sub, roi)
            if key not in results:
                continue
            d = results[key]['adaptive']['delta']
            if sub in HC_SUBJECTS:
                hc_deltas.append(d)
            else:
                cvd_deltas.append(d)

        print(f"\n{name} (K={k}):")
        if hc_deltas:
            arr = np.array(hc_deltas)
            t, p = stats.ttest_1samp(arr, 0)
            print(f"  HC  (n={len(arr)}): mean={arr.mean():+.4f}, "
                  f"SD={arr.std():.4f}, t={t:.2f}, p={p:.3f}"
                  f"{'*' if p < 0.05 else ''}")
            n_pos = np.sum(arr > 0)
            print(f"    Improved: {n_pos}/{len(arr)} subjects")

        if cvd_deltas:
            arr = np.array(cvd_deltas)
            print(f"  CVD (n={len(arr)}): mean={arr.mean():+.4f}, "
                  f"SD={arr.std():.4f}")
            for i, sub in enumerate(CVD_SUBJECTS):
                if (sub, roi) in results:
                    d = results[(sub, roi)]['adaptive']['delta']
                    print(f"    sub-{sub}: delta={d:+.4f}")


def save_summary(results, output_dir):
    """Save summary JSON for downstream use."""
    summary = {}
    for roi in ROIS:
        roi_data = {
            'roi': roi,
            'n_channels': OPTIMAL_K[roi],
            'hc': {}, 'cvd': {}
        }
        for sub in ALL_SUBJECTS:
            key = (sub, roi)
            if key not in results:
                continue
            group = 'hc' if sub in HC_SUBJECTS else 'cvd'
            roi_data[group][sub] = {
                'fixed_loco': results[key]['fixed']['loco_mean'],
                'adaptive_loco': results[key]['adaptive']['loco_mean'],
                'delta': results[key]['adaptive']['delta'],
                'centers': results[key]['adaptive']['centers']
            }
        summary[roi] = roi_data

    out_file = output_dir / 'adaptive_basis_summary.json'
    with open(out_file, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"\nSummary saved: {out_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Analyze adaptive basis optimization results')
    parser.add_argument('--results_dir', required=True,
                        help='Directory with adaptive result JSONs')
    parser.add_argument('--output_dir', default=None,
                        help='Output directory (default: same as results_dir)')
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    output_dir = Path(args.output_dir) if args.output_dir else results_dir

    results = load_results(results_dir)
    print(f"Loaded {len(results)} result files from {results_dir}")

    if not results:
        print("No results found!")
        return

    print_comparison_table(results)
    print_center_analysis(results)
    print_delta_statistics(results)
    save_summary(results, output_dir)


if __name__ == '__main__':
    main()
