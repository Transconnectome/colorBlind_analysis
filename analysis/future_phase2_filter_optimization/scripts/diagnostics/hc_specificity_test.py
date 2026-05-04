#!/usr/bin/env python3
"""
hc_specificity_test.py — HC negative controls for cone-shift pipeline.

For each HC subject i (LOO pseudo-CVD):
  1. Remove subject i from HC pool → 6 remaining HC as predictors
  2. Compute subject i's LOCO target at baseline (δ=0)
  3. Fit distortion models under BOTH protan and deutan families
  4. Permutation test (8! exact) for each fit
  5. Optional ΔRDM 2-component analysis (V1/V2 only)

If ≤1/7 HC produce false positives, specificity is established (binomial).
Settings EXACTLY match CVD pipeline — no configurable model/weight options.

Usage:
    # Server (full run, ~1h)
    mpirun -np 1 python scripts/hc_specificity_test.py \
        --output_dir results/hc_specificity --include_drdm

    # Local sanity check (single subject, ~3 min)
    python scripts/hc_specificity_test.py --hc_subjects 01
"""

import argparse
import json
import numpy as np
import sys
import time
from datetime import datetime
from pathlib import Path
from scipy.stats import spearmanr, binom

# ---------------------------------------------------------------------------
# Path setup (same pattern as loco_distortion_fit.py)
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
_PHASE2_DIR = _SCRIPT_DIR.parent  # future_phase2_filter_optimization/
sys.path.insert(0, str(_SCRIPT_DIR.parent))

# Server has pipeline scripts under cone_shift_pipeline/scripts/
_CONE_DIR = _PHASE2_DIR / 'cone_shift_pipeline' / 'scripts'
if _CONE_DIR.exists() and str(_CONE_DIR) not in sys.path:
    sys.path.insert(0, str(_CONE_DIR))

# Forward model utils: try analysis/ level (parent^3) then repo root (parent^4)
for _base in [_PHASE2_DIR.parent, _PHASE2_DIR.parent.parent]:
    _fwd = _base / 'future_phase1_forward_model' / 'scripts'
    if _fwd.exists() and str(_fwd) not in sys.path:
        sys.path.insert(0, str(_fwd))
        break

from utils_forward_model import (
    HC_SUBJECTS, N_CHANNELS, N_COLORS, HUE_ANGLES,
    load_amplitudes, create_basis_full,
)
from loco_distortion_fit import (
    grid_search, optimize_de, run_permutation_tests,
    FILTER_MODELS, DEFAULT_WEIGHTS,
)
from step1_fit_loco_v2 import (
    precompute_hc_W, simulate_single_hc_wfixed,
    simulate_mean_hc_wfixed, simulate_mean_hc_loco_legacy,
)
from diagnostic_delta_rdm import compute_delta_rdm_obs
from comprehensive_2component_analysis import (
    grid_search_2component, permutation_test_8factorial,
    two_component_design_matrix, compute_delta_rdm_sim_fast,
)

# ---------------------------------------------------------------------------
# Data paths (auto-detect)
# ---------------------------------------------------------------------------
# Local data: try server layout (parent^4) then local (parent^3)
_root4 = Path(__file__).resolve().parent.parent.parent.parent
_root3 = Path(__file__).resolve().parent.parent.parent
LOCAL_DATA = (_root3 / 'phase1_procrustes_decoding' / 'results'
              / 'visualization' / 'full_dataset_C010_with_residuals')
if not LOCAL_DATA.exists():
    LOCAL_DATA = (_root4 / 'phase1_procrustes_decoding' / 'results'
                  / 'visualization' / 'full_dataset_C010_with_residuals')
SERVER_DATA = Path(
    '/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010')

# ---------------------------------------------------------------------------
# Hardcoded settings — MUST match CVD pipeline exactly
# ---------------------------------------------------------------------------
HV4_METHOD = 'shift_at_both'
# Fourier warp excluded: ceiling/nonparametric model, not part of CVD main claims.
# Including it would inflate the multiple-comparison space unfairly for HC FPR.
HV4_MODELS = ['machado_1way', 'rc_opponent', '2component']
V1V2_METHOD = 'w_fixed'
V1V2_MODELS = ['2component']
FAMILIES = ['protan', 'deutan']
WEIGHTS = DEFAULT_WEIGHTS.copy()  # alpha=1.0, beta=0.5, delta=0.2, epsilon=0.1
ROIS = ['V1', 'V2', 'V4']


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def is_valid_target(vuln):
    """Check vulnerability vector is valid (no NaN, non-degenerate)."""
    if vuln is None:
        return False
    if np.any(np.isnan(vuln)):
        return False
    if np.std(vuln) < 1e-10:
        return False
    return True


def get_method_and_models(roi):
    """Return (method, model_list) for the given ROI."""
    if roi == 'V4':
        return HV4_METHOD, list(HV4_MODELS)
    else:
        return V1V2_METHOD, list(V1V2_MODELS)


def auto_detect_data_dir(args_data_dir=None):
    """Auto-detect data directory."""
    if args_data_dir:
        return Path(args_data_dir)
    if SERVER_DATA.exists():
        return SERVER_DATA
    if LOCAL_DATA.exists():
        return LOCAL_DATA
    old_local = (_root3 / 'phase1_preprocess_decoding' / 'results'
                 / 'full_dataset_C010')
    if not old_local.exists():
        old_local = (_root4 / 'phase1_preprocess_decoding' / 'results'
                     / 'full_dataset_C010')
    if old_local.exists():
        return old_local
    raise FileNotFoundError('Cannot find C010 data. Specify --data_dir.')


def _json_default(obj):
    """JSON serializer for numpy types."""
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return str(obj)


# ---------------------------------------------------------------------------
# Core: single-subject specificity test
# ---------------------------------------------------------------------------

def run_single_subject(hc_subj, all_amps, all_W, C_original,
                       include_drdm=False):
    """Run specificity test for one HC subject as pseudo-CVD.

    Returns dict with per-ROI, per-family, per-model results.
    """
    subj_result = {'subject': hc_subj}
    all_loco_p = []
    all_drdm_p = []

    for roi in ROIS:
        method, models = get_method_and_models(roi)
        roi_result = {}

        # LOO: exclude target subject from pool
        loo_amps = {s: v for s, v in all_amps[roi].items() if s != hc_subj}
        loo_W = {s: v for s, v in all_W[roi].items() if s != hc_subj}

        # Target: subject i's own per-color prediction at baseline (δ=0)
        vuln_target = simulate_single_hc_wfixed(
            all_W[roi][hc_subj], all_amps[roi][hc_subj], C_original)

        if not is_valid_target(vuln_target):
            roi_result['skipped'] = True
            roi_result['reason'] = 'invalid_target'
            subj_result[roi] = roi_result
            print(f'  [{roi}] SKIPPED: invalid target for sub-{hc_subj}')
            continue

        # Baseline ρ at δ=0 (LOO-mean vs target)
        if method == 'shift_at_both':
            vuln_baseline, _ = simulate_mean_hc_loco_legacy(
                loo_amps, C_original)
        else:
            vuln_baseline, _ = simulate_mean_hc_wfixed(
                loo_W, loo_amps, C_original)
        rho_baseline = float(spearmanr(vuln_baseline, vuln_target).statistic)
        if not np.isfinite(rho_baseline):
            rho_baseline = 0.0

        # ΔRDM observed (used as L_rdm regularizer in LOCO loss)
        drdm_obs, _, _, _ = compute_delta_rdm_obs(
            all_amps[roi][hc_subj], loo_amps)

        roi_result['baseline_rho'] = rho_baseline
        roi_result['vuln_target'] = vuln_target.tolist()
        roi_result['families'] = {}

        for cvd_type in FAMILIES:
            family_result = {}

            for model_name in models:
                print(f'  [{roi}] {cvd_type}/{model_name}...', end=' ',
                      flush=True)
                t0 = time.time()

                # Fit: grid search or DE (same logic as CVD pipeline)
                if FILTER_MODELS[model_name]['grid_step'] is not None:
                    result = grid_search(
                        model_name, loo_amps, vuln_target, cvd_type,
                        method=method, hc_W_dict=loo_W,
                        delta_rdm_obs=drdm_obs, weights=WEIGHTS,
                        verbose=False)
                else:
                    result = optimize_de(
                        model_name, loo_amps, vuln_target, cvd_type,
                        method=method, hc_W_dict=loo_W,
                        delta_rdm_obs=drdm_obs, weights=WEIGHTS,
                        verbose=False)

                # 8! exact permutation test at best point
                best_vuln = np.array(result['best_loss']['vuln_sim'])
                perm = run_permutation_tests(best_vuln, vuln_target)

                elapsed = time.time() - t0
                print(f'rho={perm["spearman_r"]:.3f}, '
                      f'p={perm["label_perm_p"]:.4f} ({elapsed:.1f}s)')

                family_result[model_name] = {
                    'best_params': result['best_params'],
                    'spearman_r': perm['spearman_r'],
                    'label_perm_p': perm['label_perm_p'],
                    'mse_perm_p': perm['mse_perm_p'],
                    'ccc': perm['ccc'],
                    'baseline_rho': rho_baseline,
                    'delta_rho': perm['spearman_r'] - rho_baseline,
                    'elapsed_s': round(elapsed, 1),
                }
                all_loco_p.append(perm['label_perm_p'])

            roi_result['families'][cvd_type] = family_result

        # ΔRDM 2-component (V1/V2 only, if requested)
        if include_drdm and roi != 'V4':
            roi_result['drdm'] = {}

            for cvd_type in FAMILIES:
                print(f'  [{roi}] DRDM {cvd_type}...', end=' ', flush=True)
                t0 = time.time()

                gs = grid_search_2component(
                    hc_subj, roi, loo_W, drdm_obs,
                    cvd_type, C_original)

                best_bs = gs['best_cosine']['beta_s']
                best_bc = gs['best_cosine']['beta_c']
                best_cos = gs['best_cosine']['value']

                # Re-compute sim at best params for permutation
                C_shifted = two_component_design_matrix(
                    best_bs, best_bc, cvd_type)
                drdm_sim_best, _ = compute_delta_rdm_sim_fast(
                    loo_W, C_shifted, C_original)

                perm_drdm = permutation_test_8factorial(
                    drdm_sim_best, drdm_obs)

                elapsed = time.time() - t0
                print(f'cos={best_cos:.3f}, '
                      f'p={perm_drdm["perm_p_cosine"]:.4f} ({elapsed:.1f}s)')

                roi_result['drdm'][cvd_type] = {
                    'best_beta_s': float(best_bs),
                    'best_beta_c': float(best_bc),
                    'cosine': float(best_cos),
                    'perm_p_cosine': perm_drdm['perm_p_cosine'],
                    'elapsed_s': round(elapsed, 1),
                }
                all_drdm_p.append(perm_drdm['perm_p_cosine'])

        subj_result[roi] = roi_result

    # Per-subject summary
    min_loco_p = min(all_loco_p) if all_loco_p else 1.0
    min_drdm_p = min(all_drdm_p) if all_drdm_p else 1.0
    subj_result['summary'] = {
        'min_loco_p': min_loco_p,
        'min_drdm_p': min_drdm_p,
        'min_overall_p': min(min_loco_p, min_drdm_p),
        'is_fp_loco': min_loco_p < 0.05,
        'is_fp_drdm': min_drdm_p < 0.05,
        'is_fp_overall': min(min_loco_p, min_drdm_p) < 0.05,
        'n_loco_tests': len(all_loco_p),
        'n_drdm_tests': len(all_drdm_p),
    }
    return subj_result


# ---------------------------------------------------------------------------
# FPR summary
# ---------------------------------------------------------------------------

def compute_fpr_summary(all_results, include_drdm=False):
    """Compute false-positive rate summary across all HC subjects."""
    n = len(all_results)
    fp_loco = sum(1 for r in all_results.values()
                  if r['summary']['is_fp_loco'])
    fp_drdm = sum(1 for r in all_results.values()
                  if r['summary']['is_fp_drdm'])
    fp_overall = sum(1 for r in all_results.values()
                     if r['summary']['is_fp_overall'])

    # Binomial: P(X >= k | n, p=0.05) — large = consistent with alpha
    def binom_pval(k, n_tot):
        if k == 0:
            return 1.0
        return float(1.0 - binom.cdf(k - 1, n_tot, 0.05))

    # Per-model FPR
    all_model_names = list(dict.fromkeys(HV4_MODELS + V1V2_MODELS))
    model_fpr = {}
    for model_name in all_model_names:
        n_fp = 0
        n_tested = 0
        for r in all_results.values():
            min_p = 1.0
            found = False
            for roi in ROIS:
                if roi not in r or 'families' not in r.get(roi, {}):
                    continue
                for fam in FAMILIES:
                    fam_res = r[roi].get('families', {}).get(fam, {})
                    if model_name in fam_res:
                        found = True
                        min_p = min(min_p, fam_res[model_name]['label_perm_p'])
            if found:
                n_tested += 1
                if min_p < 0.05:
                    n_fp += 1
        model_fpr[model_name] = {
            'n_fp': n_fp, 'n_tested': n_tested,
            'fpr': n_fp / n_tested if n_tested > 0 else 0.0,
        }

    # Manuscript table rows (best model per subject)
    table_rows = []
    for subj_id in sorted(all_results.keys()):
        r = all_results[subj_id]
        best_model, best_roi, best_rho, best_p = None, None, None, 1.0
        for roi in ROIS:
            if roi not in r or 'families' not in r.get(roi, {}):
                continue
            for fam in FAMILIES:
                for mname, mres in r[roi].get('families', {}).get(fam, {}).items():
                    if mres['label_perm_p'] < best_p:
                        best_p = mres['label_perm_p']
                        best_model = mname
                        best_roi = roi
                        best_rho = mres['spearman_r']
        table_rows.append({
            'subject': f'sub-{subj_id}', 'group': 'HC',
            'best_model': best_model or '-',
            'best_roi': best_roi or '-',
            'best_rho': round(best_rho, 3) if best_rho is not None else 0.0,
            'best_p': round(best_p, 4),
            'sig': '**' if best_p < 0.01 else ('*' if best_p < 0.05 else ''),
        })

    summary = {
        'n_subjects': n,
        'fpr_loco': fp_loco / n if n > 0 else 0.0,
        'fpr_overall': fp_overall / n if n > 0 else 0.0,
        'n_fp_loco': fp_loco,
        'n_fp_overall': fp_overall,
        'binom_p_loco': binom_pval(fp_loco, n),
        'binom_p_overall': binom_pval(fp_overall, n),
        'model_fpr': model_fpr,
        'table_rows': table_rows,
    }
    if include_drdm:
        summary['fpr_drdm'] = fp_drdm / n if n > 0 else 0.0
        summary['n_fp_drdm'] = fp_drdm
        summary['binom_p_drdm'] = binom_pval(fp_drdm, n)
    return summary


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='HC specificity test for cone-shift pipeline')
    parser.add_argument('--hc_subjects', nargs='+', default=HC_SUBJECTS,
                        help='HC subjects to test (default: all 7)')
    parser.add_argument('--data_dir', type=str, default=None,
                        help='C010 data path (auto-detected if omitted)')
    parser.add_argument('--output_dir', type=str,
                        default='results/hc_specificity')
    parser.add_argument('--include_drdm', action='store_true',
                        help='Include DRDM 2-component analysis (V1/V2)')
    args = parser.parse_args()

    data_dir = auto_detect_data_dir(args.data_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    hc_subjects = args.hc_subjects

    print('=' * 60)
    print('HC SPECIFICITY TEST — Cone-Shift Negative Controls')
    print('=' * 60)
    print(f'Data:          {data_dir}')
    print(f'HC subjects:   {hc_subjects}')
    print(f'hV4 models:    {HV4_MODELS}')
    print(f'V1/V2 models:  {V1V2_MODELS}')
    print(f'Include DRDM:  {args.include_drdm}')
    print(f'Weights:       {WEIGHTS}')
    print(f'Output:        {output_dir}')
    print()

    # ── STEP 0: Load ALL HC data for all 3 ROIs ──────────────────────
    print('=== STEP 0: Loading data ===')
    t_global = time.time()

    all_amps = {}   # {roi: {subj: (6,8,V_s)}}
    all_W = {}      # {roi: {subj: (K,V_s)}}

    basis_full = create_basis_full(N_CHANNELS, basis_type='fe')
    C_original = basis_full[HUE_ANGLES]

    for roi in ROIS:
        all_amps[roi] = {}
        for s in HC_SUBJECTS:  # always load ALL 7 (needed for LOO pool)
            all_amps[roi][s] = load_amplitudes(data_dir, s, roi)
        all_W[roi], _ = precompute_hc_W(all_amps[roi], C_original)
        n_vox = all_amps[roi][HC_SUBJECTS[0]].shape[2]
        print(f'  {roi}: {len(all_amps[roi])} subjects, V_s={n_vox}')

    print(f'  Data loaded in {time.time() - t_global:.1f}s\n')

    # ── STEP 1: Per-subject specificity test ─────────────────────────
    all_results = {}

    for i, hc_subj in enumerate(hc_subjects):
        print(f'{"=" * 60}')
        print(f'[{i+1}/{len(hc_subjects)}] sub-{hc_subj} as pseudo-CVD')
        print(f'{"=" * 60}')
        t_subj = time.time()

        subj_result = run_single_subject(
            hc_subj, all_amps, all_W, C_original,
            include_drdm=args.include_drdm)

        elapsed = time.time() - t_subj
        subj_result['elapsed_total_s'] = round(elapsed, 1)

        s = subj_result['summary']
        print(f'\n  sub-{hc_subj} done in {elapsed:.1f}s  |  '
              f'min_loco_p={s["min_loco_p"]:.4f}  '
              f'FP={s["is_fp_loco"]}')

        save_path = output_dir / f'sub-{hc_subj}_specificity.json'
        with open(save_path, 'w') as f:
            json.dump(subj_result, f, indent=2, default=_json_default)
        print(f'  Saved: {save_path}')

        all_results[hc_subj] = subj_result

    # ── STEP 2: FPR summary ──────────────────────────────────────────
    print(f'\n{"=" * 60}')
    print('FPR SUMMARY')
    print(f'{"=" * 60}')

    summary = compute_fpr_summary(all_results, args.include_drdm)

    print(f'\nLOCO FPR: {summary["n_fp_loco"]}/{summary["n_subjects"]} '
          f'= {summary["fpr_loco"]:.3f}')
    print(f'  Binomial P(X >= {summary["n_fp_loco"]} | n='
          f'{summary["n_subjects"]}, alpha=0.05) = '
          f'{summary["binom_p_loco"]:.4f}')

    if args.include_drdm:
        print(f'\nDRDM FPR: {summary["n_fp_drdm"]}/{summary["n_subjects"]} '
              f'= {summary["fpr_drdm"]:.3f}')

    print(f'\nOverall FPR: {summary["n_fp_overall"]}/{summary["n_subjects"]} '
          f'= {summary["fpr_overall"]:.3f}')

    print('\nPer-model FPR:')
    for model, fpr in summary['model_fpr'].items():
        print(f'  {model:20s}: {fpr["n_fp"]}/{fpr["n_tested"]} '
              f'= {fpr["fpr"]:.3f}')

    print(f'\n{"Subject":10s} {"Group":6s} {"Model":15s} {"ROI":5s} '
          f'{"rho":>6s} {"p":>8s} {"Sig":3s}')
    print('-' * 57)
    for row in summary['table_rows']:
        print(f'{row["subject"]:10s} {row["group"]:6s} '
              f'{row["best_model"]:15s} {row["best_roi"]:5s} '
              f'{row["best_rho"]:6.3f} {row["best_p"]:8.4f} {row["sig"]:3s}')

    # Save summary + config
    with open(output_dir / 'summary.json', 'w') as f:
        json.dump(summary, f, indent=2, default=_json_default)

    config = {
        'date': datetime.now().isoformat(),
        'hc_subjects': hc_subjects,
        'rois': ROIS,
        'hv4_method': HV4_METHOD,
        'hv4_models': HV4_MODELS,
        'v1v2_method': V1V2_METHOD,
        'v1v2_models': V1V2_MODELS,
        'families': FAMILIES,
        'weights': WEIGHTS,
        'include_drdm': args.include_drdm,
        'data_dir': str(data_dir),
        'total_elapsed_s': round(time.time() - t_global, 1),
    }
    with open(output_dir / 'config.json', 'w') as f:
        json.dump(config, f, indent=2, default=_json_default)

    total = time.time() - t_global
    print(f'\nTotal: {total:.0f}s ({total / 60:.1f} min)')
    print(f'Saved: {output_dir}/summary.json, config.json')


if __name__ == '__main__':
    main()
