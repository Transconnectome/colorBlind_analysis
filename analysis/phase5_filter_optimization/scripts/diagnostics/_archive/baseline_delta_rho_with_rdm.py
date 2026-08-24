#!/usr/bin/env python3
"""
baseline_delta_rho_with_rdm.py — HC validation with L_rdm fix.

Same as baseline_delta_rho_diagnostic.py but computes hV4 Procrustes ΔRDM_obs
for each subject and includes it in the loss (δ=0.2), making HC and CVD results
directly comparable.

Changes from original:
  1. Imports compute_delta_rdm_obs for hV4 Procrustes ΔRDM
  2. Imports optimize_de for fourier_warp model
  3. Adds fourier_warp to MODELS list
  4. Computes ΔRDM_obs per subject and passes to grid_search/optimize_de

Usage:
    python scripts/baseline_delta_rho_with_rdm.py \
        --subjects 01 02 03 04 05 06 07 08 09 10 \
        --output_dir results/baseline_delta_rho_with_rdm
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

# ── Path resolution (matches baseline_delta_rho_diagnostic.py) ────────────
_SCRIPT_DIR = Path(__file__).resolve().parent
_PHASE2_DIR = _SCRIPT_DIR.parent
sys.path.insert(0, str(_SCRIPT_DIR.parent))

_CONE_DIR = _PHASE2_DIR / 'cone_shift_pipeline' / 'scripts'
if _CONE_DIR.exists() and str(_CONE_DIR) not in sys.path:
    sys.path.insert(0, str(_CONE_DIR))

for _base in [_PHASE2_DIR.parent, _PHASE2_DIR.parent.parent]:
    _fwd = _base / 'phase4_forward_model' / 'scripts'
    if _fwd.exists() and str(_fwd) not in sys.path:
        sys.path.insert(0, str(_fwd))
        break

from utils_forward_model import (  # noqa: E402
    N_CHANNELS, HUE_ANGLES, load_amplitudes, create_basis_full)
from loco_distortion_fit import (  # noqa: E402
    grid_search, optimize_de, FILTER_MODELS, DEFAULT_WEIGHTS)
from step1_fit_loco_v2 import (  # noqa: E402
    precompute_hc_W, simulate_single_hc_wfixed, simulate_mean_hc_loco_legacy)
from diagnostic_delta_rdm import (  # noqa: E402
    compute_delta_rdm_obs)

# ---------------------------------------------------------------------------
HC_IDS = {'01', '02', '03', '04', '05', '06', '07'}
ROI = 'V4'  # hV4 only — primary claim
METHOD = 'shift_at_both'  # matches CVD pipeline
MODELS = ['machado_1way', 'rc_opponent', '2component', 'fourier_warp']
FAMILIES = ['protan', 'deutan']
WEIGHTS = DEFAULT_WEIGHTS.copy()

# CVD type mapping (needed for model fitting)
CVD_TYPE_MAP = {
    '08': 'deutan', '09': 'protan', '10': 'normal',
    # HC subjects use protan as default family (doesn't matter much for HC)
    '01': 'protan', '02': 'protan', '03': 'protan', '04': 'protan',
    '05': 'protan', '06': 'protan', '07': 'protan',
}

# Auto-detect data
LOCAL_DATA = (_PHASE2_DIR.parent.parent / 'analysis'
              / 'phase1_procrustes_decoding' / 'results'
              / 'visualization' / 'full_dataset_C010_with_residuals')
SERVER_DATA = Path(
    '/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010')


def auto_detect_data_dir(override=None):
    if override:
        return Path(override)
    if SERVER_DATA.exists():
        return SERVER_DATA
    if LOCAL_DATA.exists():
        return LOCAL_DATA
    raise FileNotFoundError('No data dir found')


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(str(type(o)))


def run_single_subject(subject, all_amps, all_W, C_original):
    """Diagnostic for one subject (HC or CVD), now with L_rdm included."""
    is_hc = subject in HC_IDS
    group = 'HC' if is_hc else 'CVD'

    # Pool: LOO for HC, full 7-HC for CVD
    if is_hc:
        pool_amps = {s: v for s, v in all_amps.items()
                     if s != subject and s in HC_IDS}
        pool_W = {s: v for s, v in all_W.items()
                  if s != subject and s in HC_IDS}
    else:
        pool_amps = {s: v for s, v in all_amps.items() if s in HC_IDS}
        pool_W = {s: v for s, v in all_W.items() if s in HC_IDS}

    # Target: subject's own baseline LOCO pattern
    vuln_target = simulate_single_hc_wfixed(
        all_W[subject], all_amps[subject], C_original)

    if np.any(np.isnan(vuln_target)) or np.std(vuln_target) < 1e-10:
        return {
            'subject': subject,
            'group': group,
            'skipped': True,
            'reason': 'invalid_target',
        }

    # Baseline ρ: pool LOCO mean at δ=0 vs target
    vuln_baseline, _ = simulate_mean_hc_loco_legacy(pool_amps, C_original)
    rho_baseline = float(spearmanr(vuln_baseline, vuln_target).statistic)
    if not np.isfinite(rho_baseline):
        rho_baseline = 0.0

    # Pearson too for completeness
    pearson_baseline = float(np.corrcoef(vuln_baseline, vuln_target)[0, 1])
    if not np.isfinite(pearson_baseline):
        pearson_baseline = 0.0

    # ── NEW: Compute hV4 Procrustes ΔRDM_obs for this subject ──
    # ΔRDM_obs = RDM(subject) - RDM(mean pool HC)
    # For HC LOO: RDM(HC_i) - RDM(mean other 6 HC)
    # For CVD: RDM(CVD) - RDM(mean 7 HC)
    drdm_obs, _, _, _ = compute_delta_rdm_obs(all_amps[subject], pool_amps)
    print(f'  [{subject}] ΔRDM_obs computed '
          f'(norm={np.linalg.norm(drdm_obs):.4f})')

    result = {
        'subject': subject,
        'group': group,
        'pool_size': len(pool_amps),
        'baseline_rho': rho_baseline,
        'baseline_pearson': pearson_baseline,
        'vuln_target': vuln_target.tolist(),
        'vuln_baseline': vuln_baseline.tolist(),
        'drdm_obs_norm': float(np.linalg.norm(drdm_obs)),
        'families': {},
    }

    for family in FAMILIES:
        family_res = {}
        for model in MODELS:
            print(f'  [{subject}] {family}/{model}...', end=' ', flush=True)
            t0 = time.time()

            model_info = FILTER_MODELS[model]

            if model_info['grid_step'] is not None:
                # Grid search for low-DOF models
                fit = grid_search(
                    model, pool_amps, vuln_target, family,
                    method=METHOD, hc_W_dict=pool_W,
                    delta_rdm_obs=drdm_obs,
                    weights=WEIGHTS)
            else:
                # DE for fourier_warp (4-DOF)
                fit = optimize_de(
                    model, pool_amps, vuln_target, family,
                    method=METHOD, hc_W_dict=pool_W,
                    delta_rdm_obs=drdm_obs,
                    weights=WEIGHTS, verbose=False,
                    n_restarts=2, maxiter=60, popsize=10)

            fitted_rho = float(fit['best_loss']['spearman_r'])
            if not np.isfinite(fitted_rho):
                fitted_rho = 0.0
            delta_rho = fitted_rho - rho_baseline

            # Loss components
            l_fit = float(fit['best_loss'].get('l_fit', np.nan))
            l_rdm = float(fit['best_loss'].get('l_rdm', np.nan))
            rdm_cosine = fit['best_loss'].get('rdm_cosine', None)

            elapsed = time.time() - t0
            rdm_str = (f' rdm_cos={rdm_cosine:.3f}'
                       if rdm_cosine is not None and np.isfinite(rdm_cosine)
                       else '')
            print(f'baseline={rho_baseline:.3f} fitted={fitted_rho:.3f} '
                  f'Δρ={delta_rho:+.3f} L_fit={l_fit:.4f}'
                  f'{rdm_str} ({elapsed:.1f}s)')

            family_res[model] = {
                'best_params': fit['best_params'],
                'fitted_rho': fitted_rho,
                'baseline_rho': rho_baseline,
                'delta_rho': delta_rho,
                'l_fit': l_fit,
                'l_rdm': l_rdm,
                'rdm_cosine': rdm_cosine,
                'elapsed_s': round(elapsed, 1),
            }
        result['families'][family] = family_res

    return result


def compute_best_delta_rho(subj_result):
    """Return best Δρ across all (family, model) for one subject."""
    best = {'delta_rho': -np.inf, 'model': None, 'family': None,
            'fitted_rho': None, 'best_params': None, 'l_fit': None}
    if subj_result.get('skipped'):
        return best
    for fam, fam_res in subj_result['families'].items():
        for model, mres in fam_res.items():
            if mres['delta_rho'] > best['delta_rho']:
                best = {
                    'delta_rho': mres['delta_rho'],
                    'model': model,
                    'family': fam,
                    'fitted_rho': mres['fitted_rho'],
                    'best_params': mres['best_params'],
                    'l_fit': mres['l_fit'],
                }
    return best


def aggregate_summary(all_results):
    """Build HC vs CVD comparison summary."""
    hc_baseline, cvd_baseline = [], []
    hc_delta, cvd_delta = [], []
    rows = []

    for subj, r in sorted(all_results.items()):
        if r.get('skipped'):
            continue
        best = compute_best_delta_rho(r)
        row = {
            'subject': subj,
            'group': r['group'],
            'baseline_rho': r['baseline_rho'],
            'best_fitted_rho': best['fitted_rho'],
            'best_delta_rho': best['delta_rho'],
            'best_model': best['model'],
            'best_family': best['family'],
            'best_params': best['best_params'],
            'best_l_fit': best['l_fit'],
        }
        rows.append(row)

        if r['group'] == 'HC':
            hc_baseline.append(r['baseline_rho'])
            hc_delta.append(best['delta_rho'])
        else:
            cvd_baseline.append(r['baseline_rho'])
            cvd_delta.append(best['delta_rho'])

    hc_baseline = np.asarray(hc_baseline)
    cvd_baseline = np.asarray(cvd_baseline)
    hc_delta = np.asarray(hc_delta)
    cvd_delta = np.asarray(cvd_delta)

    # Empirical p: rank of each CVD in HC Δρ distribution (one-tailed)
    empirical_p = {}
    for subj, r in sorted(all_results.items()):
        if r.get('group') != 'CVD' or r.get('skipped'):
            continue
        best = compute_best_delta_rho(r)
        cvd_dr = best['delta_rho']
        n_exceed = int(np.sum(hc_delta >= cvd_dr))
        p = (n_exceed + 1) / (len(hc_delta) + 1)
        empirical_p[subj] = {
            'cvd_delta_rho': cvd_dr,
            'n_hc_exceed': n_exceed,
            'empirical_p': p,
            'rank_in_hc': int(np.sum(hc_delta < cvd_dr)) + 1,
        }

    summary = {
        'n_hc': len(hc_delta),
        'n_cvd': len(cvd_delta),
        'hc_baseline_stats': {
            'mean': float(hc_baseline.mean()) if hc_baseline.size else None,
            'std': float(hc_baseline.std()) if hc_baseline.size else None,
            'min': float(hc_baseline.min()) if hc_baseline.size else None,
            'max': float(hc_baseline.max()) if hc_baseline.size else None,
        },
        'cvd_baseline_stats': {
            'mean': float(cvd_baseline.mean()) if cvd_baseline.size else None,
            'values': cvd_baseline.tolist(),
        },
        'hc_delta_stats': {
            'mean': float(hc_delta.mean()) if hc_delta.size else None,
            'std': float(hc_delta.std()) if hc_delta.size else None,
            'min': float(hc_delta.min()) if hc_delta.size else None,
            'max': float(hc_delta.max()) if hc_delta.size else None,
            'values': hc_delta.tolist(),
        },
        'cvd_delta_stats': {
            'mean': float(cvd_delta.mean()) if cvd_delta.size else None,
            'values': cvd_delta.tolist(),
        },
        'empirical_p_per_cvd': empirical_p,
        'rows': rows,
        'l_rdm_included': True,
        'l_rdm_weight': WEIGHTS.get('delta', 0.2),
        'models': MODELS,
    }
    return summary


def print_comparison_table(summary):
    print('\n' + '=' * 80)
    print('BASELINE ρ + Δρ DIAGNOSTIC — hV4 (with L_rdm)')
    print('=' * 80)
    print(f'{"Subject":10s} {"Group":7s} {"Baseline":>10s} {"Fitted":>8s} '
          f'{"Δρ":>8s} {"L_fit":>7s} {"Model":15s} {"Family":7s}')
    print('-' * 80)
    for row in summary['rows']:
        l_fit_str = (f'{row["best_l_fit"]:.4f}'
                     if row["best_l_fit"] is not None else '   N/A')
        print(f'{row["subject"]:10s} {row["group"]:7s} '
              f'{row["baseline_rho"]:10.3f} {row["best_fitted_rho"]:8.3f} '
              f'{row["best_delta_rho"]:+8.3f} {l_fit_str:>7s} '
              f'{row["best_model"]:15s} {row["best_family"]:7s}')
    print('-' * 80)

    hs = summary['hc_delta_stats']
    cs = summary['cvd_delta_stats']
    bs_hc = summary['hc_baseline_stats']
    bs_cvd = summary['cvd_baseline_stats']

    print(f'\nHC baseline:  mean={bs_hc["mean"]:+.3f}  '
          f'range=[{bs_hc["min"]:+.3f}, {bs_hc["max"]:+.3f}]  '
          f'(n={summary["n_hc"]})')
    print(f'CVD baseline: values={bs_cvd["values"]}')
    print(f'HC Δρ:  mean={hs["mean"]:+.3f} ± {hs["std"]:.3f}  '
          f'range=[{hs["min"]:+.3f}, {hs["max"]:+.3f}]')
    print(f'CVD Δρ: values={cs["values"]}')

    print('\nEmpirical p (CVD Δρ vs HC Δρ distribution, one-tailed):')
    for subj, info in summary['empirical_p_per_cvd'].items():
        sig = '*' if info['empirical_p'] < 0.05 else ''
        print(f'  sub-{subj}: Δρ={info["cvd_delta_rho"]:+.3f}  '
              f'rank={info["rank_in_hc"]}/{summary["n_hc"] + 1}  '
              f'p={info["empirical_p"]:.4f} {sig}')
    print(f'\nL_rdm included: δ={summary["l_rdm_weight"]}')
    print(f'Models: {summary["models"]}')
    print('=' * 80)


def main():
    parser = argparse.ArgumentParser(
        description='Baseline ρ + Δρ diagnostic with L_rdm (hV4 Procrustes ΔRDM)')
    parser.add_argument('--subjects', nargs='+',
                        default=['01', '02', '03', '04', '05', '06', '07',
                                 '08', '09', '10'])
    parser.add_argument('--data_dir', type=str, default=None)
    parser.add_argument('--output_dir', type=str,
                        default='results/baseline_delta_rho_with_rdm')
    args = parser.parse_args()

    data_dir = auto_detect_data_dir(args.data_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print('=' * 60)
    print('BASELINE ρ + Δρ DIAGNOSTIC (hV4) — WITH L_rdm')
    print('=' * 60)
    print(f'Data:        {data_dir}')
    print(f'Subjects:    {args.subjects}')
    print(f'ROI:         {ROI}')
    print(f'Method:      {METHOD}')
    print(f'Models:      {MODELS}')
    print(f'Weights:     {WEIGHTS}')
    print(f'Output:      {output_dir}\n')

    # Load hV4 amplitudes
    print('=== Loading data ===')
    t0 = time.time()
    subjects_to_load = sorted(set(args.subjects) | HC_IDS)
    all_amps = {}
    for s in subjects_to_load:
        all_amps[s] = load_amplitudes(data_dir, s, ROI)
    print(f'  Loaded {len(all_amps)} subjects (pool + targets), '
          f'V_s={all_amps[subjects_to_load[0]].shape[2]}')

    # Precompute W for ALL subjects
    basis_full = create_basis_full(N_CHANNELS, basis_type='fe')
    C_original = basis_full[HUE_ANGLES]
    all_W, _ = precompute_hc_W(all_amps, C_original)
    print(f'  W precomputed in {time.time() - t0:.1f}s\n')

    # Run diagnostic for each subject
    all_results = {}
    t_global = time.time()
    for i, subj in enumerate(args.subjects):
        print(f'[{i+1}/{len(args.subjects)}] sub-{subj}')
        t_subj = time.time()
        r = run_single_subject(subj, all_amps, all_W, C_original)
        r['elapsed_total_s'] = round(time.time() - t_subj, 1)
        all_results[subj] = r

        save_path = output_dir / f'sub-{subj}_baseline_delta.json'
        with open(save_path, 'w') as f:
            json.dump(r, f, indent=2, default=_json_default)
        print(f'  Saved: {save_path}  ({r["elapsed_total_s"]:.1f}s)\n')

    # Aggregate
    summary = aggregate_summary(all_results)
    print_comparison_table(summary)

    # Save summary + config
    with open(output_dir / 'summary.json', 'w') as f:
        json.dump(summary, f, indent=2, default=_json_default)

    config = {
        'date': datetime.now().isoformat(),
        'subjects': args.subjects,
        'roi': ROI,
        'method': METHOD,
        'models': MODELS,
        'families': FAMILIES,
        'weights': WEIGHTS,
        'data_dir': str(data_dir),
        'l_rdm_included': True,
        'total_elapsed_s': round(time.time() - t_global, 1),
    }
    with open(output_dir / 'config.json', 'w') as f:
        json.dump(config, f, indent=2, default=_json_default)

    print(f'\nTotal: {time.time() - t_global:.0f}s')
    print(f'Saved: {output_dir}/summary.json, config.json')


if __name__ == '__main__':
    main()
