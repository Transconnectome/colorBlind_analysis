#!/usr/bin/env python3
"""
analyze_5axis_comparison.py — 5-axis comparison of CVD prediction models.

Compares 4 models (Baseline FE-K, B1 subject-K, B2 anisotropic, B3 hierarchical)
across 5 evaluation axes:

  1. Overall accuracy: Mean LOCO voxel_corr per model per ROI
  2. Signed angular bias: decoded_hue - true_hue per color
  3. Confusion structure: which colors get confused
  4. Pairwise geometry: RDM correlation with ideal circular RDM
  5. Statistical comparison: HC paired t-test, CVD Crawford-Howell

Usage (local):
    conda activate srm
    python analyze_5axis_comparison.py \
        --results_dir analysis/future_phase1_forward_model/results \
        --output_dir analysis/future_phase1_forward_model/results/5axis_comparison
"""

import argparse
import json
import numpy as np
from pathlib import Path
from scipy import stats


# ============================================================================
# Constants
# ============================================================================

HC_SUBJECTS = [f'{i:02d}' for i in range(1, 8)]
CVD_SUBJECTS = [f'{i:02d}' for i in range(8, 11)]
ALL_SUBJECTS = HC_SUBJECTS + CVD_SUBJECTS
ROIS = ['V1', 'V2', 'V3', 'V4']
HUE_ANGLES = np.array([0, 45, 90, 135, 180, 225, 270, 315])
COLOR_NAMES = ['red', 'orange', 'yellow', 'green',
               'cyan', 'blue', 'purple', 'magenta']

# Models to compare
MODELS = ['baseline_fek', 'subject_k', 'anisotropic', 'hierarchical']
MODEL_LABELS = {
    'baseline_fek': 'Baseline FE-K',
    'subject_k': 'B1: Subject K*',
    'anisotropic': 'B2: Anisotropic',
    'hierarchical': 'B3: Hierarchical',
}


# ============================================================================
# Data Loading
# ============================================================================

def load_baseline(results_dir, subj, roi):
    """Load baseline FE-K from nested_adaptive results."""
    path = Path(results_dir) / 'nested_adaptive' / \
        f'sub-{subj}_{roi}_nested_adaptive.json'
    if not path.exists():
        return None
    with open(path) as f:
        data = json.load(f)
    return {
        'loco_mean': data['fixed_optimal']['loco_mean'],
        'loco_per_color': data['fixed_optimal']['loco_per_color'],
    }


def load_subject_k(results_dir, subj, roi):
    """Load B1 subject-K results (use optimal K's metrics)."""
    path = Path(results_dir) / 'subject_k' / \
        f'sub-{subj}_{roi}_subject_k.json'
    if not path.exists():
        return None
    with open(path) as f:
        data = json.load(f)
    k_star = str(data['optimal_k'])
    per_k = data['per_k'].get(k_star, {})
    return {
        'loco_mean': per_k.get('loco_mean'),
        'loco_per_color': per_k.get('loco_per_color'),
        'decoded_hues': per_k.get('decoded_hues'),
        'mae_degrees': per_k.get('mae_degrees'),
        'loco_predicted_rdm_ut': per_k.get('loco_predicted_rdm_ut'),
        'optimal_k': data['optimal_k'],
    }


def load_anisotropic(results_dir, subj, roi):
    """Load B2 anisotropic results."""
    path = Path(results_dir) / 'anisotropic_basis' / \
        f'sub-{subj}_{roi}_anisotropic.json'
    if not path.exists():
        return None
    with open(path) as f:
        data = json.load(f)
    aniso = data['anisotropic']
    return {
        'loco_mean': aniso['loco_mean'],
        'loco_per_color': aniso['loco_per_color'],
        'decoded_hues': aniso.get('decoded_hues'),
        'mae_degrees': aniso.get('mae_degrees'),
        'loco_predicted_rdm_ut': aniso.get('loco_predicted_rdm_ut'),
        'mean_a': aniso.get('mean_a'),
        'mean_b': aniso.get('mean_b'),
    }


def load_hierarchical(results_dir, subj, roi):
    """Load B3 hierarchical results."""
    path = Path(results_dir) / 'hierarchical_fe' / \
        f'sub-{subj}_{roi}_hierarchical.json'
    if not path.exists():
        return None
    with open(path) as f:
        data = json.load(f)
    hier = data['hierarchical']
    return {
        'loco_mean': hier['loco_mean'],
        'loco_per_color': hier['loco_per_color'],
        'decoded_hues': hier.get('decoded_hues'),
        'mae_degrees': hier.get('mae_degrees'),
        'loco_predicted_rdm_ut': hier.get('loco_predicted_rdm_ut'),
        'mean_lambda': hier.get('mean_lambda'),
    }


LOADERS = {
    'baseline_fek': load_baseline,
    'subject_k': load_subject_k,
    'anisotropic': load_anisotropic,
    'hierarchical': load_hierarchical,
}


def load_all_data(results_dir):
    """Load all model results into a nested dict.

    Returns:
        data[model][subj][roi] = {loco_mean, loco_per_color, ...}
    """
    data = {}
    for model in MODELS:
        data[model] = {}
        loader = LOADERS[model]
        for subj in ALL_SUBJECTS:
            data[model][subj] = {}
            for roi in ROIS:
                result = loader(results_dir, subj, roi)
                data[model][subj][roi] = result
    return data


# ============================================================================
# Statistical Tests
# ============================================================================

def crawford_howell(x_i, control_scores):
    """Modified t-test for single case vs control group.

    Args:
        x_i: single CVD subject's score
        control_scores: array of HC scores

    Returns:
        t_stat, p_value (two-tailed)
    """
    n = len(control_scores)
    M = np.mean(control_scores)
    S = np.std(control_scores, ddof=1)
    if S == 0:
        return np.nan, np.nan
    t = (x_i - M) / (S * np.sqrt((n + 1) / n))
    p = 2 * stats.t.sf(np.abs(t), df=n - 1)
    return float(t), float(p)


def signed_circular_error(true_hue, decoded_hue):
    """Signed circular error in degrees, wrapped to [-180, 180]."""
    diff = decoded_hue - true_hue
    diff = (diff + 180) % 360 - 180
    return diff


def ideal_circular_rdm(n=8):
    """Ideal circular RDM for 8 equispaced hues."""
    angles = np.linspace(0, 360, n, endpoint=False)
    rdm = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            d = np.abs(angles[i] - angles[j])
            rdm[i, j] = min(d, 360 - d)
    return rdm


def rdm_upper_tri(rdm):
    """Extract upper triangle."""
    mask = np.triu(np.ones(rdm.shape, dtype=bool), k=1)
    return rdm[mask]


# ============================================================================
# Axis 1: Overall Accuracy
# ============================================================================

def axis1_overall_accuracy(data):
    """Print overall LOCO accuracy table."""
    print("\n" + "=" * 80)
    print("AXIS 1: Overall Accuracy (Mean LOCO Voxel Correlation)")
    print("=" * 80)

    results = {}

    for roi in ROIS:
        print(f"\n--- {roi} ---")
        header = f"{'Subject':>8s}"
        for model in MODELS:
            header += f"  {MODEL_LABELS[model]:>16s}"
        print(header)
        print("-" * len(header))

        for subj in ALL_SUBJECTS:
            group = 'HC' if subj in HC_SUBJECTS else 'CVD'
            line = f"  {subj:>3s}({group})"
            for model in MODELS:
                d = data[model][subj][roi]
                if d and d.get('loco_mean') is not None:
                    line += f"  {d['loco_mean']:>16.4f}"
                else:
                    line += f"  {'N/A':>16s}"
            print(line)

        # Group means
        for group_name, group_subjs in [('HC mean', HC_SUBJECTS),
                                         ('CVD mean', CVD_SUBJECTS)]:
            line = f"  {group_name:>7s}"
            for model in MODELS:
                vals = []
                for s in group_subjs:
                    d = data[model][s][roi]
                    if d and d.get('loco_mean') is not None:
                        vals.append(d['loco_mean'])
                if vals:
                    line += f"  {np.mean(vals):>16.4f}"
                    key = (model, roi, group_name.split()[0])
                    results[key] = vals
                else:
                    line += f"  {'N/A':>16s}"
            print(line)

    return results


# ============================================================================
# Axis 2: Signed Angular Bias
# ============================================================================

def axis2_signed_bias(data):
    """Print signed angular bias per color."""
    print("\n" + "=" * 80)
    print("AXIS 2: Signed Angular Bias (decoded - true, degrees)")
    print("=" * 80)

    results = {}

    for roi in ROIS:
        for model in MODELS:
            if model == 'baseline_fek':
                continue  # no decoded_hues for baseline

            bias_hc = []
            bias_cvd = []

            for subj in ALL_SUBJECTS:
                d = data[model][subj][roi]
                if d is None or d.get('decoded_hues') is None:
                    continue

                dec = np.array(d['decoded_hues'])
                errors = np.array([signed_circular_error(HUE_ANGLES[i], dec[i])
                                   for i in range(len(HUE_ANGLES))])

                if subj in HC_SUBJECTS:
                    bias_hc.append(errors)
                else:
                    bias_cvd.append(errors)

            if not bias_hc and not bias_cvd:
                continue

            print(f"\n--- {roi} | {MODEL_LABELS[model]} ---")
            print(f"{'Color':>10s}  {'HC mean':>10s}  {'HC std':>10s}  ", end='')
            for cvd_s in CVD_SUBJECTS:
                print(f"  {cvd_s:>8s}", end='')
            print()

            if bias_hc:
                hc_arr = np.array(bias_hc)  # (n_hc, 8)
                hc_mean = np.mean(hc_arr, axis=0)
                hc_std = np.std(hc_arr, axis=0, ddof=1)
            else:
                hc_mean = np.full(8, np.nan)
                hc_std = np.full(8, np.nan)

            for c in range(8):
                line = f"{COLOR_NAMES[c]:>10s}  {hc_mean[c]:>10.1f}  {hc_std[c]:>10.1f}  "
                for ci, cvd_s in enumerate(CVD_SUBJECTS):
                    if ci < len(bias_cvd):
                        line += f"  {bias_cvd[ci][c]:>8.1f}"
                    else:
                        line += f"  {'N/A':>8s}"
                print(line)

            results[(model, roi)] = {
                'hc_mean': hc_mean.tolist() if bias_hc else None,
                'cvd': [b.tolist() for b in bias_cvd],
            }

    return results


# ============================================================================
# Axis 3: Confusion Structure
# ============================================================================

def axis3_confusion(data):
    """Analyze nearest-neighbor vs non-neighbor errors."""
    print("\n" + "=" * 80)
    print("AXIS 3: Confusion Structure (Nearest-Neighbor Errors)")
    print("=" * 80)

    results = {}

    for roi in ROIS:
        for model in MODELS:
            if model == 'baseline_fek':
                continue

            nn_errors_hc = []
            nn_errors_cvd = []

            for subj in ALL_SUBJECTS:
                d = data[model][subj][roi]
                if d is None or d.get('decoded_hues') is None:
                    continue

                dec = np.array(d['decoded_hues'])
                n_nn = 0  # nearest-neighbor errors
                n_total = 0
                for c in range(8):
                    if np.isnan(dec[c]):
                        continue
                    pred_idx = int(round(dec[c] / 45)) % 8
                    if pred_idx != c:
                        n_total += 1
                        # Check if predicted is adjacent
                        if abs(pred_idx - c) == 1 or abs(pred_idx - c) == 7:
                            n_nn += 1

                frac_nn = n_nn / n_total if n_total > 0 else np.nan

                if subj in HC_SUBJECTS:
                    nn_errors_hc.append(frac_nn)
                else:
                    nn_errors_cvd.append(frac_nn)

            if not nn_errors_hc and not nn_errors_cvd:
                continue

            hc_mean = np.nanmean(nn_errors_hc) if nn_errors_hc else np.nan
            print(f"  {roi} | {MODEL_LABELS[model]:20s}: "
                  f"HC nn_frac={hc_mean:.2f}  "
                  f"CVD nn_frac={nn_errors_cvd}")

            results[(model, roi)] = {
                'hc_nn_fractions': nn_errors_hc,
                'cvd_nn_fractions': nn_errors_cvd,
            }

    return results


# ============================================================================
# Axis 4: Pairwise Geometry (RDM vs Ideal)
# ============================================================================

def axis4_geometry(data):
    """Compare LOCO-predicted RDM with ideal circular RDM."""
    print("\n" + "=" * 80)
    print("AXIS 4: Pairwise Geometry (Spearman rho vs Ideal Circular RDM)")
    print("=" * 80)

    ideal = ideal_circular_rdm()
    ideal_ut = rdm_upper_tri(ideal)

    results = {}

    for roi in ROIS:
        print(f"\n--- {roi} ---")
        header = f"{'Subject':>8s}"
        for model in MODELS:
            if model == 'baseline_fek':
                continue
            header += f"  {MODEL_LABELS[model]:>16s}"
        print(header)
        print("-" * len(header))

        for subj in ALL_SUBJECTS:
            group = 'HC' if subj in HC_SUBJECTS else 'CVD'
            line = f"  {subj:>3s}({group})"
            for model in MODELS:
                if model == 'baseline_fek':
                    continue
                d = data[model][subj][roi]
                if d and d.get('loco_predicted_rdm_ut') is not None:
                    rdm_ut = np.array(d['loco_predicted_rdm_ut'])
                    rho, p = stats.spearmanr(rdm_ut, ideal_ut)
                    line += f"  {rho:>16.3f}"
                    key = (model, roi, subj)
                    results[key] = {'rho': float(rho), 'p': float(p)}
                else:
                    line += f"  {'N/A':>16s}"
            print(line)

    return results


# ============================================================================
# Axis 5: Statistical Comparison
# ============================================================================

def axis5_statistics(data):
    """HC paired t-test (model vs baseline), CVD Crawford-Howell."""
    print("\n" + "=" * 80)
    print("AXIS 5: Statistical Comparison")
    print("=" * 80)

    results = {}

    for roi in ROIS:
        print(f"\n--- {roi} ---")

        # HC paired t-test: each model vs baseline
        print("\n  HC Paired t-test (model vs baseline FE-K):")
        for model in MODELS:
            if model == 'baseline_fek':
                continue

            baseline_vals = []
            model_vals = []
            for s in HC_SUBJECTS:
                b = data['baseline_fek'][s][roi]
                m = data[model][s][roi]
                if (b and b.get('loco_mean') is not None and
                    m and m.get('loco_mean') is not None):
                    baseline_vals.append(b['loco_mean'])
                    model_vals.append(m['loco_mean'])

            if len(baseline_vals) >= 2:
                t, p = stats.ttest_rel(model_vals, baseline_vals)
                diff = np.mean(model_vals) - np.mean(baseline_vals)
                # Cohen's d for paired samples
                d_vals = np.array(model_vals) - np.array(baseline_vals)
                d_cohen = np.mean(d_vals) / np.std(d_vals, ddof=1) \
                    if np.std(d_vals, ddof=1) > 0 else np.nan
                print(f"    {MODEL_LABELS[model]:20s}: "
                      f"delta={diff:+.4f}  t={t:.3f}  "
                      f"p={p:.4f}  d={d_cohen:.3f}")
                results[('hc_ttest', model, roi)] = {
                    'delta': float(diff), 't': float(t),
                    'p': float(p), 'd': float(d_cohen),
                    'n': len(baseline_vals),
                }
            else:
                print(f"    {MODEL_LABELS[model]:20s}: insufficient data")

        # CVD Crawford-Howell: individual vs HC group
        print("\n  CVD Crawford-Howell (individual vs HC group):")
        for model in MODELS:
            if model == 'baseline_fek':
                continue

            # HC scores for this model
            hc_scores = []
            for s in HC_SUBJECTS:
                m = data[model][s][roi]
                if m and m.get('loco_mean') is not None:
                    hc_scores.append(m['loco_mean'])

            if len(hc_scores) < 3:
                print(f"    {MODEL_LABELS[model]:20s}: "
                      f"insufficient HC data (n={len(hc_scores)})")
                continue

            for cvd_s in CVD_SUBJECTS:
                m = data[model][cvd_s][roi]
                if m and m.get('loco_mean') is not None:
                    t, p = crawford_howell(m['loco_mean'],
                                           np.array(hc_scores))
                    print(f"    {MODEL_LABELS[model]:20s} | sub-{cvd_s}: "
                          f"score={m['loco_mean']:.4f}  "
                          f"t={t:.3f}  p={p:.4f}")
                    results[('cvd_ch', model, roi, cvd_s)] = {
                        'score': m['loco_mean'],
                        't': float(t), 'p': float(p),
                        'hc_mean': float(np.mean(hc_scores)),
                        'hc_std': float(np.std(hc_scores, ddof=1)),
                    }
                else:
                    print(f"    {MODEL_LABELS[model]:20s} | sub-{cvd_s}: N/A")

    return results


# ============================================================================
# Summary
# ============================================================================

def print_summary(data):
    """Print a concise summary across all axes."""
    print("\n" + "=" * 80)
    print("SUMMARY: Best Model per ROI (by mean LOCO)")
    print("=" * 80)

    for roi in ROIS:
        print(f"\n  {roi}:")
        for group_name, group_subjs in [('HC', HC_SUBJECTS),
                                         ('CVD', CVD_SUBJECTS)]:
            best_model = None
            best_val = -np.inf
            for model in MODELS:
                vals = []
                for s in group_subjs:
                    d = data[model][s][roi]
                    if d and d.get('loco_mean') is not None:
                        vals.append(d['loco_mean'])
                if vals:
                    mean_val = np.mean(vals)
                    if mean_val > best_val:
                        best_val = mean_val
                        best_model = model
            if best_model:
                print(f"    {group_name}: {MODEL_LABELS[best_model]} "
                      f"(mean={best_val:.4f})")
            else:
                print(f"    {group_name}: no data")


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='5-Axis comparison of CVD prediction models')
    parser.add_argument('--results_dir', type=str, required=True,
                        help='Root results directory')
    parser.add_argument('--output_dir', type=str, required=True,
                        help='Output directory for summary')
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Loading all model results...")
    data = load_all_data(args.results_dir)

    # Count loaded results
    for model in MODELS:
        n = sum(1 for s in ALL_SUBJECTS for r in ROIS
                if data[model][s][r] is not None)
        print(f"  {MODEL_LABELS[model]:20s}: {n}/40 results loaded")

    # Run all 5 axes
    r1 = axis1_overall_accuracy(data)
    r2 = axis2_signed_bias(data)
    r3 = axis3_confusion(data)
    r4 = axis4_geometry(data)
    r5 = axis5_statistics(data)

    print_summary(data)

    # Save summary JSON
    summary = {
        'axis1_note': 'Overall LOCO accuracy per model x ROI',
        'axis2_note': 'Signed angular bias per color',
        'axis3_note': 'Nearest-neighbor confusion fraction',
        'axis4_note': 'RDM Spearman rho vs ideal circular',
        'axis5_note': 'HC paired t-test + CVD Crawford-Howell',
    }

    # Serialize axis5 results (keys are tuples, convert to strings)
    axis5_serialized = {}
    for k, v in r5.items():
        axis5_serialized[str(k)] = v
    summary['axis5_statistics'] = axis5_serialized

    # Axis1: group means per model x ROI
    axis1_serialized = {}
    for k, v in r1.items():
        axis1_serialized[str(k)] = {
            'mean': float(np.mean(v)),
            'std': float(np.std(v, ddof=1)) if len(v) > 1 else 0,
            'n': len(v),
        }
    summary['axis1_group_means'] = axis1_serialized

    out_file = output_dir / '5axis_summary.json'
    with open(out_file, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"\nSummary saved to: {out_file}")


if __name__ == '__main__':
    main()
