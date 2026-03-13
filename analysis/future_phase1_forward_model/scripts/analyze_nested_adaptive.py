#!/usr/bin/env python3
"""
analyze_nested_adaptive.py — Analyze nested LOCO validation results.

Runs locally after downloading results from server.
Produces:
  1. 3-way comparison table (FE-6 vs FE-K vs Nested Adaptive)
  2. HC paired t-test (nested adaptive vs fixed)
  3. Per-fold center variability analysis
  4. Circular vs Nested comparison (overestimation check)
  5. CVD individual profiles

Usage:
    python analyze_nested_adaptive.py \
        --results_dir ../results/nested_adaptive \
        --circular_dir ../results/adaptive_basis \
        [--output_dir ../results/nested_adaptive]
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


def load_nested_results(results_dir):
    """Load nested LOCO results."""
    results = {}
    for sub in ALL_SUBJECTS:
        for roi in ROIS:
            path = results_dir / f'sub-{sub}_{roi}_nested_adaptive.json'
            if path.exists():
                with open(path) as f:
                    results[(sub, roi)] = json.load(f)
    return results


def load_circular_results(circular_dir):
    """Load circular (biased) adaptive results for comparison."""
    results = {}
    for sub in ALL_SUBJECTS:
        for roi in ROIS:
            path = circular_dir / f'sub-{sub}_{roi}_adaptive.json'
            if path.exists():
                with open(path) as f:
                    results[(sub, roi)] = json.load(f)
    return results


def print_3way_table(results):
    """Print FE-6 vs FE-K vs Nested Adaptive comparison."""
    print("\n" + "=" * 90)
    print("3-WAY COMPARISON: FE-6 vs FE-K(optimal) vs Nested Adaptive")
    print("=" * 90)

    for roi in ROIS:
        name = ROI_DISPLAY[roi]
        k = OPTIMAL_K[roi]
        print(f"\n--- {name} (K={k}) ---")
        print(f"{'Subject':>10} | {'FE-6':>8} | {'FE-'+str(k):>8} | {'Nested':>8} | "
              f"{'Δ(N-FE6)':>9} | {'Δ(N-FEK)':>9}")
        print("-" * 65)

        hc_fe6, hc_fek, hc_nest = [], [], []
        cvd_fe6, cvd_fek, cvd_nest = [], [], []

        for sub in ALL_SUBJECTS:
            key = (sub, roi)
            if key not in results:
                continue
            r = results[key]
            fe6 = r['fixed_fe6']['loco_mean']
            fek = r['fixed_optimal']['loco_mean']
            nest = r['nested_adaptive']['loco_mean']
            d_fe6 = nest - fe6
            d_fek = nest - fek

            group = "HC" if sub in HC_SUBJECTS else "CVD"
            print(f"  {group}-{sub} | {fe6:+.4f} | {fek:+.4f} | {nest:+.4f} | "
                  f"{d_fe6:+.4f} | {d_fek:+.4f}")

            if sub in HC_SUBJECTS:
                hc_fe6.append(fe6)
                hc_fek.append(fek)
                hc_nest.append(nest)
            else:
                cvd_fe6.append(fe6)
                cvd_fek.append(fek)
                cvd_nest.append(nest)

        print("-" * 65)
        if hc_fe6:
            print(f"  HC mean  | {np.mean(hc_fe6):+.4f} | {np.mean(hc_fek):+.4f} | "
                  f"{np.mean(hc_nest):+.4f} | {np.mean(hc_nest)-np.mean(hc_fe6):+.4f} | "
                  f"{np.mean(hc_nest)-np.mean(hc_fek):+.4f}")
        if cvd_fe6:
            print(f"  CVD mean | {np.mean(cvd_fe6):+.4f} | {np.mean(cvd_fek):+.4f} | "
                  f"{np.mean(cvd_nest):+.4f} | {np.mean(cvd_nest)-np.mean(cvd_fe6):+.4f} | "
                  f"{np.mean(cvd_nest)-np.mean(cvd_fek):+.4f}")


def print_hc_ttest(results):
    """HC paired t-tests: nested adaptive vs fixed baselines."""
    print("\n" + "=" * 90)
    print("HC PAIRED t-TESTS: Nested Adaptive vs Fixed Baselines")
    print("=" * 90)

    print(f"\n{'ROI':>5} | {'Comparison':>20} | {'Δ M(SD)':>15} | "
          f"{'t(6)':>7} | {'p':>7} | {'n_pos':>5}")
    print("-" * 75)

    for roi in ROIS:
        name = ROI_DISPLAY[roi]
        k = OPTIMAL_K[roi]

        hc_fe6, hc_fek, hc_nest = [], [], []
        for sub in HC_SUBJECTS:
            key = (sub, roi)
            if key not in results:
                continue
            r = results[key]
            hc_fe6.append(r['fixed_fe6']['loco_mean'])
            hc_fek.append(r['fixed_optimal']['loco_mean'])
            hc_nest.append(r['nested_adaptive']['loco_mean'])

        if len(hc_nest) < 3:
            continue

        hc_fe6 = np.array(hc_fe6)
        hc_fek = np.array(hc_fek)
        hc_nest = np.array(hc_nest)

        # Nested vs FE-6
        d1 = hc_nest - hc_fe6
        t1, p1 = stats.ttest_1samp(d1, 0)
        star1 = '*' if p1 < 0.05 else ''
        print(f"  {name:>3} | {'Nested vs FE-6':>20} | {d1.mean():+.4f}({d1.std():.4f}) | "
              f"{t1:7.3f} | {p1:.3f}{star1} | {np.sum(d1>0)}/{len(d1)}")

        # Nested vs FE-K
        d2 = hc_nest - hc_fek
        t2, p2 = stats.ttest_1samp(d2, 0)
        star2 = '*' if p2 < 0.05 else ''
        print(f"  {'':>3} | {'Nested vs FE-'+str(k):>20} | {d2.mean():+.4f}({d2.std():.4f}) | "
              f"{t2:7.3f} | {p2:.3f}{star2} | {np.sum(d2>0)}/{len(d2)}")

        # FE-K vs FE-6 (channel count effect)
        d3 = hc_fek - hc_fe6
        t3, p3 = stats.ttest_1samp(d3, 0)
        star3 = '*' if p3 < 0.05 else ''
        print(f"  {'':>3} | {'FE-'+str(k)+' vs FE-6':>20} | {d3.mean():+.4f}({d3.std():.4f}) | "
              f"{t3:7.3f} | {p3:.3f}{star3} | {np.sum(d3>0)}/{len(d3)}")


def print_circular_vs_nested(nested_results, circular_results):
    """Compare circular (biased) vs nested (unbiased) adaptive scores."""
    print("\n" + "=" * 90)
    print("CIRCULAR vs NESTED ADAPTIVE (overestimation check)")
    print("=" * 90)

    print(f"\n{'ROI':>5} | {'Subject':>10} | {'Circular':>9} | {'Nested':>9} | "
          f"{'Bias':>9} | {'Note':>15}")
    print("-" * 70)

    for roi in ROIS:
        name = ROI_DISPLAY[roi]
        hc_biases = []

        for sub in ALL_SUBJECTS:
            n_key = (sub, roi)
            c_key = (sub, roi)

            if n_key not in nested_results or c_key not in circular_results:
                continue

            circ = circular_results[c_key]['adaptive']['loco_mean']
            nest = nested_results[n_key]['nested_adaptive']['loco_mean']
            bias = circ - nest

            group = "HC" if sub in HC_SUBJECTS else "CVD"
            note = ""
            if bias > 0.05:
                note = "large bias"
            elif bias < -0.01:
                note = "negative?!"

            print(f"  {name:>3} | {group}-{sub:>5} | {circ:+.4f} | {nest:+.4f} | "
                  f"{bias:+.4f} | {note}")

            if sub in HC_SUBJECTS:
                hc_biases.append(bias)

        if hc_biases:
            hc_b = np.array(hc_biases)
            print(f"  {name:>3} | {'HC mean':>10} | {'':>9} | {'':>9} | "
                  f"{hc_b.mean():+.4f} | SD={hc_b.std():.4f}")
        print()


def print_center_variability(results):
    """Analyze per-fold center variability in nested LOCO."""
    print("\n" + "=" * 90)
    print("PER-FOLD CENTER VARIABILITY (nested adaptive)")
    print("=" * 90)

    for roi in ROIS:
        name = ROI_DISPLAY[roi]
        k = OPTIMAL_K[roi]
        print(f"\n--- {name} (K={k}) ---")

        for sub in ALL_SUBJECTS[:3] + CVD_SUBJECTS[:1]:
            key = (sub, roi)
            if key not in results:
                continue
            r = results[key]
            centers = np.array(r['nested_adaptive']['per_fold_centers'])
            inner_scores = np.array(r['nested_adaptive']['per_fold_inner_score'])

            group = "HC" if sub in HC_SUBJECTS else "CVD"
            print(f"\n  {group}-{sub}:")
            print(f"    Per-fold centers (8 folds × K={k}):")
            for fold in range(min(8, len(centers))):
                c = np.array(centers[fold])
                print(f"      Fold {fold}: {np.array2string(c, precision=1)} "
                      f"(inner={inner_scores[fold]:.3f})")

            center_std = np.std(centers, axis=0)
            print(f"    Center SD across folds: "
                  f"{np.array2string(center_std, precision=1)}")
            print(f"    Inner score range: "
                  f"[{inner_scores.min():.3f}, {inner_scores.max():.3f}]")


def print_cvd_profiles(results):
    """CVD individual profiles for nested adaptive."""
    print("\n" + "=" * 90)
    print("CVD INDIVIDUAL PROFILES (Nested Adaptive)")
    print("=" * 90)

    for sub in CVD_SUBJECTS:
        print(f"\n  sub-{sub}:")
        for roi in ROIS:
            key = (sub, roi)
            if key not in results:
                continue
            r = results[key]
            name = ROI_DISPLAY[roi]
            fe6 = r['fixed_fe6']['loco_mean']
            fek = r['fixed_optimal']['loco_mean']
            nest = r['nested_adaptive']['loco_mean']
            print(f"    {name}: FE-6={fe6:+.4f}, "
                  f"FE-{r['fixed_optimal']['n_channels']}={fek:+.4f}, "
                  f"Nested={nest:+.4f} (Δ={nest-fek:+.4f})")


def save_summary(nested_results, circular_results, output_dir):
    """Save summary JSON."""
    summary = {}
    for roi in ROIS:
        roi_data = {'roi': roi, 'n_channels': OPTIMAL_K[roi]}
        for sub in ALL_SUBJECTS:
            key = (sub, roi)
            if key not in nested_results:
                continue
            r = nested_results[key]
            group = 'hc' if sub in HC_SUBJECTS else 'cvd'
            if group not in roi_data:
                roi_data[group] = {}

            entry = {
                'fe6': r['fixed_fe6']['loco_mean'],
                'fek': r['fixed_optimal']['loco_mean'],
                'nested': r['nested_adaptive']['loco_mean'],
                'delta_vs_fe6': r['delta_vs_fe6'],
                'delta_vs_fek': r['delta_vs_fixed_optimal'],
            }
            if circular_results and key in circular_results:
                circ = circular_results[key]['adaptive']['loco_mean']
                entry['circular'] = circ
                entry['overestimation'] = circ - r['nested_adaptive']['loco_mean']

            roi_data[group][sub] = entry

        summary[roi] = roi_data

    out_file = output_dir / 'nested_adaptive_summary.json'
    with open(out_file, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"\nSummary saved: {out_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Analyze nested LOCO validation results')
    parser.add_argument('--results_dir', required=True,
                        help='Directory with nested adaptive JSONs')
    parser.add_argument('--circular_dir', default=None,
                        help='Directory with circular adaptive JSONs (for bias check)')
    parser.add_argument('--output_dir', default=None,
                        help='Output directory (default: results_dir)')
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    output_dir = Path(args.output_dir) if args.output_dir else results_dir

    nested_results = load_nested_results(results_dir)
    print(f"Loaded {len(nested_results)} nested results from {results_dir}")

    circular_results = {}
    if args.circular_dir:
        circular_dir = Path(args.circular_dir)
        circular_results = load_circular_results(circular_dir)
        print(f"Loaded {len(circular_results)} circular results from {circular_dir}")

    if not nested_results:
        print("No results found!")
        return

    print_3way_table(nested_results)
    print_hc_ttest(nested_results)

    if circular_results:
        print_circular_vs_nested(nested_results, circular_results)

    print_center_variability(nested_results)
    print_cvd_profiles(nested_results)
    save_summary(nested_results, circular_results, output_dir)


if __name__ == '__main__':
    main()
