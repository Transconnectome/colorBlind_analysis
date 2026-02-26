#!/usr/bin/env python3
"""
LOCO SRM Validation: Crawford & Howell Single-Case Tests on LOCO MAE

Applies the same statistical framework used in Phase 2 SRM analysis
(rerun_loo_consistent.py) to the LOCO decoder results.

Tests:
1. Crawford & Howell (1998) single-case test per CVD subject per ROI
2. LOO-consistent variant: HC ref = mean of 6 remaining HC MAEs
3. Hedges' g effect size with bootstrap 95% CI
4. Permutation test (10,000 iter)
5. Spearman rank correlation: LOCO MAE rank vs SRM disparity rank

Usage: python validate_loco_srm.py [--model ForwardEncoding] [--loco_dir ...]
"""

import numpy as np
import json
import argparse
from pathlib import Path
from datetime import datetime
from scipy.stats import t as t_dist, spearmanr

# ============================================================================
# CONFIG
# ============================================================================

HC_SUBJECTS = [f"{i:02d}" for i in range(1, 8)]
CVD_SUBJECTS = [f"{i:02d}" for i in range(8, 11)]
ALL_SUBJECTS = HC_SUBJECTS + CVD_SUBJECTS

ROIS = ['V1', 'V2', 'V3', 'V4']
ROI_DISPLAY = {'V1': 'V1', 'V2': 'V2', 'V3': 'V3', 'V4': 'hV4'}

N_PERM = 10000
N_BOOT = 10000
SEED = 42


# ============================================================================
# STATISTICAL FUNCTIONS (from rerun_loo_consistent.py)
# ============================================================================

def crawford_howell_test(patient_score, control_scores):
    """Crawford & Howell (1998) modified t-test for single case."""
    n = len(control_scores)
    control_mean = np.mean(control_scores)
    control_sd = np.std(control_scores, ddof=1)

    if control_sd == 0:
        return float('inf') if patient_score > control_mean else 0.0, 0.0, n - 1

    t_stat = (patient_score - control_mean) / (control_sd * np.sqrt((n + 1) / n))
    df = n - 1
    p_value = 1 - t_dist.cdf(t_stat, df)  # one-tailed (patient > control)

    return float(t_stat), float(p_value), int(df)


def hedges_g(group1, group2):
    """Hedges' g effect size (bias-corrected Cohen's d)."""
    n1, n2 = len(group1), len(group2)
    s_pooled = np.sqrt(((n1-1)*np.var(group1, ddof=1) + (n2-1)*np.var(group2, ddof=1)) / (n1+n2-2))
    if s_pooled == 0:
        return 0.0
    d = (np.mean(group2) - np.mean(group1)) / s_pooled
    return d * (1 - 3 / (4*(n1+n2-2) - 1))


def bootstrap_ci(data, n_bootstrap=10000, seed=42):
    """Bootstrap 95% CI for the mean."""
    rng = np.random.RandomState(seed)
    means = [np.mean(data[rng.choice(len(data), len(data), replace=True)])
             for _ in range(n_bootstrap)]
    means = np.array(means)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


# ============================================================================
# MAIN ANALYSIS
# ============================================================================

def load_loco_mae(loco_dir, model='ForwardEncoding'):
    """Load LOCO MAE per subject per ROI for a given model."""
    mae_data = {}  # {roi: {subject_id: mae}}

    for s_id in ALL_SUBJECTS:
        path = Path(loco_dir) / f"sub-{s_id}_loco.json"
        if not path.exists():
            print(f"  WARNING: {path} not found, skipping")
            continue

        with open(path) as f:
            data = json.load(f)

        for roi in ROIS:
            if roi not in data.get('results', {}):
                continue
            if model not in data['results'][roi]:
                continue

            if roi not in mae_data:
                mae_data[roi] = {}
            mae_data[roi][s_id] = data['results'][roi][model]['overall_mae']

    return mae_data


def analyze_roi(roi, hc_maes, cvd_maes, rng):
    """Run full Crawford & Howell analysis for one ROI."""
    roi_display = ROI_DISPLAY.get(roi, roi)

    hc_arr = np.array(hc_maes)
    cvd_arr = np.array(cvd_maes)
    n_hc = len(hc_arr)

    print(f"\n{'='*60}")
    print(f"ROI: {roi_display}")
    print(f"{'='*60}")
    print(f"  HC MAEs: {[f'{v:.1f}' for v in hc_arr]}")
    print(f"  CVD MAEs: {[f'{v:.1f}' for v in cvd_arr]}")
    print(f"  HC mean: {hc_arr.mean():.1f} +/- {hc_arr.std(ddof=1):.1f}")
    print(f"  CVD mean: {cvd_arr.mean():.1f} +/- {cvd_arr.std(ddof=1):.1f}")

    # --- LOO-consistent HC disparities ---
    # For each fold i, HC ref = mean of 6 remaining HC MAEs
    hc_loo = np.zeros(n_hc)
    for i in range(n_hc):
        others = np.delete(hc_arr, i)
        hc_loo[i] = hc_arr[i] - others.mean()  # deviation from LOO reference

    # CVD scores: mean deviation across 7 LOO folds
    cvd_loo_scores = np.zeros(len(cvd_arr))
    cvd_loo_details = np.zeros((len(cvd_arr), n_hc))
    for j in range(len(cvd_arr)):
        for i in range(n_hc):
            others = np.delete(hc_arr, i)
            ref_i = others.mean()
            cvd_loo_details[j, i] = cvd_arr[j] - ref_i
        cvd_loo_scores[j] = cvd_loo_details[j].mean()

    # Use raw MAEs for Crawford & Howell (simpler, more standard)
    # Crawford & Howell tests each CVD MAE against HC MAE distribution
    individual_results = {}
    print(f"\n  Crawford & Howell individual CVD tests (raw MAE):")
    for j, s_id in enumerate(CVD_SUBJECTS):
        if j >= len(cvd_arr):
            break
        t_stat, p_val, df = crawford_howell_test(cvd_arr[j], hc_arr)
        sig = '*' if p_val < 0.05 else ''
        print(f"    sub-{s_id}: MAE={cvd_arr[j]:.1f}, t={t_stat:.3f}, p={p_val:.4f} {sig}")
        individual_results[f'sub-{s_id}'] = {
            'mae': float(cvd_arr[j]),
            't_stat': t_stat,
            'p_value': p_val,
            'df': df,
            'significant': p_val < 0.05,
        }

    # --- Group-level analysis ---
    separation = cvd_arr.mean() - hc_arr.mean()
    g = hedges_g(hc_arr, cvd_arr)
    print(f"\n  Group: separation={separation:.1f}, Hedges' g={g:.3f}")

    # Bootstrap CI
    boot_sep, boot_g = [], []
    for _ in range(N_BOOT):
        hc_b = hc_arr[rng.choice(n_hc, n_hc, replace=True)]
        cvd_b = cvd_arr[rng.choice(len(cvd_arr), len(cvd_arr), replace=True)]
        boot_sep.append(cvd_b.mean() - hc_b.mean())
        boot_g.append(hedges_g(hc_b, cvd_b))
    boot_sep = np.array(boot_sep)
    boot_g = np.array(boot_g)

    sep_ci = [float(np.percentile(boot_sep, 2.5)), float(np.percentile(boot_sep, 97.5))]
    g_ci = [float(np.percentile(boot_g, 2.5)), float(np.percentile(boot_g, 97.5))]
    hc_ci = bootstrap_ci(hc_arr, N_BOOT, SEED)
    cvd_ci = bootstrap_ci(cvd_arr, N_BOOT, SEED + 1)

    print(f"  Separation 95% CI: [{sep_ci[0]:.1f}, {sep_ci[1]:.1f}]")
    print(f"  Hedges' g 95% CI: [{g_ci[0]:.2f}, {g_ci[1]:.2f}]")

    # --- Permutation test ---
    all_maes = np.concatenate([hc_arr, cvd_arr])
    observed_diff = cvd_arr.mean() - hc_arr.mean()

    null_diffs = np.zeros(N_PERM)
    for p_i in range(N_PERM):
        perm = rng.permutation(len(all_maes))
        pseudo_hc = all_maes[perm[:n_hc]]
        pseudo_cvd = all_maes[perm[n_hc:]]
        null_diffs[p_i] = pseudo_cvd.mean() - pseudo_hc.mean()

    # Higher MAE = worse interpolation, so test CVD > HC
    p_perm = float(np.mean(null_diffs >= observed_diff))
    print(f"  Permutation p = {p_perm:.4f} (CVD > HC, {N_PERM} iter)")

    return {
        'roi': roi_display,
        'hc_maes': hc_arr.tolist(),
        'cvd_maes': cvd_arr.tolist(),
        'summary': {
            'hc_mean': float(hc_arr.mean()),
            'hc_std': float(hc_arr.std(ddof=1)),
            'hc_ci': list(hc_ci),
            'cvd_mean': float(cvd_arr.mean()),
            'cvd_std': float(cvd_arr.std(ddof=1)),
            'cvd_ci': list(cvd_ci),
            'separation': float(separation),
            'separation_ci': sep_ci,
            'hedges_g': float(g),
            'hedges_g_ci': g_ci,
            'perm_p': p_perm,
            'n_perm': N_PERM,
        },
        'individual_cvd': individual_results,
        'loo_consistent': {
            'hc_loo_deviations': hc_loo.tolist(),
            'cvd_loo_scores': cvd_loo_scores.tolist(),
            'cvd_loo_details': cvd_loo_details.tolist(),
        },
    }


def rank_correlation_analysis(loco_mae, srm_disparity_path=None):
    """
    Compute Spearman rank correlation between LOCO MAE and SRM disparity.
    """
    if srm_disparity_path is None:
        return None

    # Load SRM results
    srm_path = Path(srm_disparity_path)
    if not srm_path.exists():
        print(f"\n  SRM results not found: {srm_path}, skipping rank correlation")
        return None

    with open(srm_path) as f:
        srm_data = json.load(f)

    correlations = {}
    for roi in ROIS:
        roi_display = ROI_DISPLAY.get(roi, roi)
        if roi not in loco_mae:
            continue

        # Get per-subject MAE and SRM disparity
        srm_results = srm_data.get('results', {}).get(roi_display, {})
        if not srm_results:
            continue

        hc_disps = srm_results.get('hc_loo_disparities', {})
        cvd_indiv = srm_results.get('individual_cvd', {})

        subjects_both = []
        mae_vals = []
        disp_vals = []

        for s_id in ALL_SUBJECTS:
            s_full = f'sub-{s_id}'
            if s_id not in loco_mae[roi]:
                continue

            if s_full in hc_disps:
                disp_vals.append(hc_disps[s_full])
                mae_vals.append(loco_mae[roi][s_id])
                subjects_both.append(s_full)
            elif s_full in cvd_indiv:
                disp_vals.append(cvd_indiv[s_full]['cvd_score'])
                mae_vals.append(loco_mae[roi][s_id])
                subjects_both.append(s_full)

        if len(subjects_both) < 5:
            continue

        rho, p = spearmanr(mae_vals, disp_vals)
        print(f"\n  Rank correlation {roi_display}: rho={rho:.3f}, p={p:.4f} (n={len(subjects_both)})")
        correlations[roi_display] = {
            'spearman_rho': float(rho),
            'p_value': float(p),
            'n': len(subjects_both),
            'subjects': subjects_both,
            'mae_values': mae_vals,
            'disparity_values': disp_vals,
        }

    return correlations


def main():
    parser = argparse.ArgumentParser(description="Validate LOCO with Crawford & Howell")
    parser.add_argument('--loco_dir', type=str,
                        default=str(Path(__file__).resolve().parent.parent / "results" / "loco"),
                        help='Directory with sub-*_loco.json files')
    parser.add_argument('--model', type=str, default='ForwardEncoding',
                        help='Model to extract MAE from')
    parser.add_argument('--srm_results', type=str, default=None,
                        help='Path to SRM loo_consistent_results.json for rank correlation')
    parser.add_argument('--output_dir', type=str,
                        default=str(Path(__file__).resolve().parent.parent / "results"))
    args = parser.parse_args()

    rng = np.random.RandomState(SEED)

    print("="*60)
    print(f"LOCO SRM Validation: {args.model}")
    print(f"LOCO dir: {args.loco_dir}")
    print("="*60)

    # Load LOCO MAE
    mae_data = load_loco_mae(args.loco_dir, args.model)

    all_results = {}
    for roi in ROIS:
        if roi not in mae_data:
            print(f"\n  Skipping {roi}: no data")
            continue

        hc_maes = [mae_data[roi][s] for s in HC_SUBJECTS if s in mae_data[roi]]
        cvd_maes = [mae_data[roi][s] for s in CVD_SUBJECTS if s in mae_data[roi]]

        if len(hc_maes) < 3 or len(cvd_maes) < 1:
            print(f"\n  Skipping {roi}: insufficient subjects")
            continue

        result = analyze_roi(roi, hc_maes, cvd_maes, rng)
        all_results[ROI_DISPLAY.get(roi, roi)] = result

    # Rank correlation
    rank_corrs = rank_correlation_analysis(mae_data, args.srm_results)

    # Save
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    output_file = output_path / "loco_srm_validation.json"

    save_data = {
        'description': f'Crawford & Howell validation of LOCO {args.model} MAE',
        'model': args.model,
        'loco_dir': str(args.loco_dir),
        'n_perm': N_PERM,
        'n_boot': N_BOOT,
        'seed': SEED,
        'results': all_results,
        'rank_correlations': rank_corrs,
        'created': datetime.now().isoformat(),
    }

    with open(output_file, 'w') as f:
        json.dump(save_data, f, indent=2)

    # Summary table
    print(f"\n\n{'='*80}")
    print("SUMMARY TABLE")
    print(f"{'='*80}")
    print(f"{'ROI':<5} | {'HC MAE [CI]':<24} | {'CVD MAE [CI]':<24} | {'Sep [CI]':<22} | {'g [CI]':<20} | {'p_perm':>6}")
    print("-"*110)
    for roi_d in ['V1', 'V2', 'V3', 'hV4']:
        if roi_d not in all_results:
            continue
        s = all_results[roi_d]['summary']
        print(f"{roi_d:<5} | "
              f"{s['hc_mean']:5.1f} [{s['hc_ci'][0]:.1f},{s['hc_ci'][1]:.1f}] | "
              f"{s['cvd_mean']:5.1f} [{s['cvd_ci'][0]:.1f},{s['cvd_ci'][1]:.1f}] | "
              f"{s['separation']:5.1f} [{s['separation_ci'][0]:.1f},{s['separation_ci'][1]:.1f}] | "
              f"{s['hedges_g']:.2f} [{s['hedges_g_ci'][0]:.2f},{s['hedges_g_ci'][1]:.2f}] | "
              f"{s['perm_p']:>6.4f}")

    print(f"\nIndividual CVD (Crawford & Howell):")
    print(f"{'Subject':<8} | {'V1 (t, p)':<20} | {'V2 (t, p)':<20} | {'V3 (t, p)':<20} | {'hV4 (t, p)':<20}")
    print("-"*95)
    for s_id in CVD_SUBJECTS:
        s_full = f'sub-{s_id}'
        parts = []
        for roi_d in ['V1', 'V2', 'V3', 'hV4']:
            if roi_d in all_results and s_full in all_results[roi_d]['individual_cvd']:
                iv = all_results[roi_d]['individual_cvd'][s_full]
                sig = '*' if iv['significant'] else ''
                parts.append(f"{iv['t_stat']:.2f}, {iv['p_value']:.3f}{sig}")
            else:
                parts.append("N/A")
        print(f"{s_full:<8} | " + " | ".join(f"{p:<20}" for p in parts))

    print(f"\nSaved: {output_file}")


if __name__ == '__main__':
    main()
