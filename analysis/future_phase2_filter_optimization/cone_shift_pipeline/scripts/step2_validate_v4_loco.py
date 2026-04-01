#!/usr/bin/env python3
"""
step2_validate_v4_loco.py — V4 LOCO validation for ΔRDM-fitted δθ.

Takes the best δθ from step1_fit_delta_rdm.py (ΔRDM V1+V2 fitting),
then evaluates it on V4 using LOCO vulnerability (ridge_gcv).

Validation logic:
  1. Load step1 result.json → best_δθ
  2. Simulate mean-HC LOCO vulnerability at best_δθ (W-fixed)
  3. Compare with observed CVD LOCO vulnerability (from forward model)
  4. Spearman ρ + exact 8! permutation + baseline improvement test

Usage:
    conda activate srm
    python scripts/step2_validate_v4_loco.py \
        --sim_dir results/sim \
        --output_dir results/sim
"""

import argparse
import json
import numpy as np
from pathlib import Path
from datetime import datetime
from itertools import permutations
from scipy.stats import spearmanr
import sys

_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR))

_FWD_DIR = str(Path(__file__).resolve().parent.parent.parent.parent
               / 'future_phase1_forward_model' / 'scripts')
sys.path.insert(0, _FWD_DIR)

from utils_forward_model import (
    HC_SUBJECTS, CVD_SUBJECTS, N_CHANNELS, N_RUNS, N_COLORS,
    HUE_ANGLES, load_amplitudes, create_basis_matrix,
)
from utils_distortion_models import get_design_matrix, MODELS
from step1_fit_loco_v2 import (
    precompute_hc_W,
    simulate_mean_hc_wfixed,
    load_cvd_loco_target,
)

LOCAL_BASELINE = Path(__file__).resolve().parent.parent.parent.parent \
    / 'phase1_preprocess_decoding' / 'results' / 'full_dataset_C010'

CVD_TYPE = {'08': 'deutan', '09': 'protan', '10': 'normal'}

COLOR_NAMES = ['red', 'orange', 'yellow', 'green',
               'cyan', 'blue', 'purple', 'magenta']


# ============================================================================
# Permutation tests
# ============================================================================

def exact_perm_spearman(synthetic, observed):
    """Exact 8! permutation test for Spearman ρ.

    Returns:
        p_value, null_distribution, observed_rho
    """
    rho_obs, _ = spearmanr(synthetic, observed)
    if not np.isfinite(rho_obs):
        rho_obs = 0.0

    null = []
    for perm in permutations(range(8)):
        r, _ = spearmanr(synthetic, observed[list(perm)])
        null.append(r if np.isfinite(r) else 0.0)
    null = np.array(null)

    p = float((np.sum(null >= rho_obs) + 1) / (len(null) + 1))
    return p, null, float(rho_obs)


def exact_perm_improvement(synthetic_fit, synthetic_base, observed):
    """Exact 8! permutation test for Δρ = ρ(fit) - ρ(baseline).

    Returns:
        p_value, null_delta, observed_delta, rho_fit, rho_base
    """
    rho_fit, _ = spearmanr(synthetic_fit, observed)
    rho_base, _ = spearmanr(synthetic_base, observed)
    rho_fit = float(rho_fit) if np.isfinite(rho_fit) else 0.0
    rho_base = float(rho_base) if np.isfinite(rho_base) else 0.0
    delta_obs = rho_fit - rho_base

    null_delta = []
    for perm in permutations(range(8)):
        obs_perm = observed[list(perm)]
        r_fit, _ = spearmanr(synthetic_fit, obs_perm)
        r_base, _ = spearmanr(synthetic_base, obs_perm)
        r_fit = r_fit if np.isfinite(r_fit) else 0.0
        r_base = r_base if np.isfinite(r_base) else 0.0
        null_delta.append(r_fit - r_base)
    null_delta = np.array(null_delta)

    p = float((np.sum(null_delta >= delta_obs) + 1) / (len(null_delta) + 1))
    return p, null_delta, float(delta_obs), rho_fit, rho_base


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Step 2: V4 LOCO validation for ΔRDM-fitted δθ')
    parser.add_argument('--sim_dir', type=str, default='results/sim',
                        help='Directory containing step1 result.json files')
    parser.add_argument('--output_dir', type=str, default='results/sim',
                        help='Output directory (same as sim_dir by default)')
    parser.add_argument('--cvd_subjects', nargs='+', default=CVD_SUBJECTS)
    parser.add_argument('--hc_subjects', nargs='+', default=HC_SUBJECTS)
    parser.add_argument('--models', nargs='+',
                        default=['cone_1way', 'cone_3way', 'fourier'])
    parser.add_argument('--baseline_dir', type=str,
                        default=str(LOCAL_BASELINE))
    args = parser.parse_args()

    print('=' * 60)
    print('Step 2: V4 LOCO Validation (ΔRDM-fitted δθ)')
    print(f'CVD subjects: {args.cvd_subjects}')
    print(f'Models: {args.models}')
    print('=' * 60)

    roi = 'V4'
    C_baseline = create_basis_matrix(HUE_ANGLES, N_CHANNELS)

    # Load V4 HC amplitudes
    print('\nLoading V4 amplitudes...')
    hc_amps_v4 = {}
    for subj in args.hc_subjects:
        hc_amps_v4[subj] = load_amplitudes(args.baseline_dir, subj, roi)
    print(f'  Loaded {len(hc_amps_v4)} HC subjects')

    # Precompute V4 W
    hc_W_v4, hc_alphas_v4 = precompute_hc_W(hc_amps_v4, C_baseline)
    alpha_str = ', '.join(f'{a:.1f}' for a in hc_alphas_v4.values())
    print(f'  V4 alphas: [{alpha_str}]')

    # Baseline V4 LOCO vulnerability (δ=0)
    mean_vuln_base, _ = simulate_mean_hc_wfixed(
        hc_W_v4, hc_amps_v4, C_baseline)

    for cvd_subj in args.cvd_subjects:
        cvd_type = CVD_TYPE[cvd_subj]
        print(f'\n{"="*50}')
        print(f'sub-{cvd_subj} ({cvd_type})')
        print(f'{"="*50}')

        # Load CVD LOCO target (from forward model results)
        cvd_vuln = load_cvd_loco_target(cvd_subj, roi)
        print(f'  CVD LOCO target: {np.round(cvd_vuln, 3)}')

        for model_name in args.models:
            # Load step1 result
            result_path = (Path(args.sim_dir)
                           / f'sub-{cvd_subj}_{model_name}_delta_rdm'
                           / 'result.json')
            if not result_path.exists():
                print(f'\n  --- {model_name}: result.json not found, skipping ---')
                continue

            with open(result_path) as f:
                step1 = json.load(f)

            best_params = step1['phase_a']['best_params']
            source_metric = step1['metric']
            print(f'\n  --- {model_name} (source: ΔRDM {source_metric}) ---')
            print(f'    Best δθ params: {best_params}')

            # Simulate V4 LOCO at best δθ
            C_shifted = get_design_matrix(
                model_name, best_params, cvd_type=cvd_type)
            mean_vuln_fit, per_hc_vuln = simulate_mean_hc_wfixed(
                hc_W_v4, hc_amps_v4, C_shifted)

            # Spearman ρ
            rho_fit, _ = spearmanr(mean_vuln_fit, cvd_vuln)
            rho_base, _ = spearmanr(mean_vuln_base, cvd_vuln)
            rho_fit = float(rho_fit) if np.isfinite(rho_fit) else 0.0
            rho_base = float(rho_base) if np.isfinite(rho_base) else 0.0
            print(f'    V4 LOCO Spearman: fitted={rho_fit:.3f}, '
                  f'baseline={rho_base:.3f}')

            # Exact permutation tests
            print('    Running exact 8! permutation tests...')
            label_p, _, _ = exact_perm_spearman(mean_vuln_fit, cvd_vuln)
            impr_p, _, delta_rho, _, _ = exact_perm_improvement(
                mean_vuln_fit, mean_vuln_base, cvd_vuln)
            print(f'    label_perm_p = {label_p:.4f}')
            print(f'    Δρ = {delta_rho:+.4f}, '
                  f'baseline_improvement_p = {impr_p:.4f}')

            # Per-HC V4 Spearman at fitted δθ
            per_hc_rhos = {}
            for subj, vuln in per_hc_vuln.items():
                r, _ = spearmanr(vuln, cvd_vuln)
                per_hc_rhos[subj] = float(r) if np.isfinite(r) else 0.0

            # Build output
            validation = {
                'subject': cvd_subj,
                'cvd_type': cvd_type,
                'source': step1['loss_function'],
                'source_metric': source_metric,
                'source_model': model_name,
                'source_best_params': best_params,
                'source_label_perm_p': step1['phase_a']['label_perm_p'],
                'timestamp': datetime.now().isoformat(),
                'v4_loco': {
                    'spearman_rho': rho_fit,
                    'label_perm_p': label_p,
                    'baseline_rho': rho_base,
                    'delta_rho': delta_rho,
                    'baseline_improvement_p': impr_p,
                    'vuln_synthetic': mean_vuln_fit.tolist(),
                    'vuln_observed': cvd_vuln.tolist(),
                    'vuln_baseline': mean_vuln_base.tolist(),
                    'per_hc_spearman': per_hc_rhos,
                    'per_hc_mean_rho': float(
                        np.mean(list(per_hc_rhos.values()))),
                    'per_hc_std_rho': float(
                        np.std(list(per_hc_rhos.values()), ddof=1)),
                },
                'hc_subjects': args.hc_subjects,
                'hc_alphas_v4': hc_alphas_v4,
                'color_names': COLOR_NAMES,
            }

            # Save to same directory as step1 result
            out_dir = (Path(args.output_dir)
                       / f'sub-{cvd_subj}_{model_name}_delta_rdm')
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / 'validation_v4.json'
            with open(out_path, 'w') as f:
                json.dump(validation, f, indent=2)
            print(f'    Saved: {out_path}')

    print('\nStep 2 (V4 LOCO validation) complete.')


if __name__ == '__main__':
    main()
