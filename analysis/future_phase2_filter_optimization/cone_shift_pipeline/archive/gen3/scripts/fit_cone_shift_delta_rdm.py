#!/usr/bin/env python3
"""
fit_cone_shift_delta_rdm.py — Fit cone-shift using ΔRDM loss (V1+V2).

Objective: ΔRDM loss (pairwise geometry distortion)
Method: W-fixed simulation, 2-stage grid search, exact 8! permutation

Fits cone-shift δθ by maximizing combined V1+V2 ΔRDM similarity:
  Loss = 0.5 × sim(ΔRDM_sim_V1, ΔRDM_obs_V1) + 0.5 × sim(ΔRDM_sim_V2, ΔRDM_obs_V2)
  where ΔRDM_sim(δ) = RDM(C(θ+δ)@W_HC) - RDM(C(θ)@W_HC)
        ΔRDM_obs = RDM_CVD - RDM_HC_mean

Key design:
  - W-fixed: precompute W_HC from C(θ) once, sweep C(θ+δ) only
  - 2-stage grid: coarse (2° step) → refine (0.5° step, ±5°)
  - Exact 8! permutation (40,320): label_perm_p, baseline_improvement_p
  - Phase B: per-color synthetic vulnerability at best δθ

Models: cone_1way (df=1), cone_3way (df=3), fourier (df=4)
Subjects: sub-08 (deutan), sub-09 (protan), sub-10 (normal)

Usage:
    conda activate srm
    python scripts/fit_cone_shift_delta_rdm.py \
        --output_dir results/sim \
        --metric cosine
"""

import argparse
import json
import numpy as np
from pathlib import Path
from datetime import datetime
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
from utils_distortion_models import (
    MODELS, get_design_matrix, get_delta_theta,
)
from diagnostic_delta_rdm import (
    compute_delta_rdm_obs,
    compute_delta_rdm_sim,
    precompute_hc_W,
)
from loss_functions import DeltaRDM_V1V2_Equal

LOCAL_BASELINE = Path(__file__).resolve().parent.parent.parent.parent \
    / 'phase1_preprocess_decoding' / 'results' / 'full_dataset_C010'

CVD_TYPE = {'08': 'deutan', '09': 'protan', '10': 'normal'}

COLOR_NAMES = ['red', 'orange', 'yellow', 'green',
               'cyan', 'blue', 'purple', 'magenta']

FIT_MODELS = ['cone_1way', 'cone_3way', 'fourier']


# ============================================================================
# 2-stage grid search
# ============================================================================

def grid_search_1d(loss_fn, model_name, cvd_type,
                   hc_W_dicts, hc_amps_dicts, delta_rdm_obs_dicts,
                   C_baseline, coarse_step=2, refine_step=0.5,
                   refine_range=5):
    """2-stage grid search for 1-parameter models (cone_1way).

    Stage 1: coarse sweep over full bounds with coarse_step
    Stage 2: refine around best with refine_step in ±refine_range

    Returns:
        best_params, best_loss, best_result, coarse_info, refine_info
    """
    bounds = MODELS[model_name]['bounds']
    lo, hi = bounds[0]

    # Stage 1: Coarse
    coarse_grid = np.arange(lo, hi + coarse_step, coarse_step)
    coarse_losses = []
    coarse_results = []

    for val in coarse_grid:
        C_shifted = get_design_matrix(model_name, [val], cvd_type=cvd_type)
        r = loss_fn.compute(C_shifted, C_baseline,
                            hc_W_dicts, hc_amps_dicts, delta_rdm_obs_dicts)
        coarse_losses.append(r['combined'])
        coarse_results.append(r)

    best_coarse_idx = int(np.argmax(coarse_losses))
    best_coarse_val = float(coarse_grid[best_coarse_idx])

    # Stage 2: Refine
    refine_lo = max(lo, best_coarse_val - refine_range)
    refine_hi = min(hi, best_coarse_val + refine_range)
    refine_grid = np.arange(refine_lo, refine_hi + refine_step, refine_step)
    refine_losses = []
    refine_results = []

    for val in refine_grid:
        C_shifted = get_design_matrix(model_name, [val], cvd_type=cvd_type)
        r = loss_fn.compute(C_shifted, C_baseline,
                            hc_W_dicts, hc_amps_dicts, delta_rdm_obs_dicts)
        refine_losses.append(r['combined'])
        refine_results.append(r)

    best_refine_idx = int(np.argmax(refine_losses))
    best_val = float(refine_grid[best_refine_idx])
    best_result = refine_results[best_refine_idx]

    coarse_info = {
        'step': coarse_step,
        'n_points': len(coarse_grid),
        'grid': coarse_grid.tolist(),
        'losses': coarse_losses,
        'best_idx': best_coarse_idx,
        'best_val': best_coarse_val,
    }
    refine_info = {
        'center': best_coarse_val,
        'step': refine_step,
        'range': refine_range,
        'n_points': len(refine_grid),
        'grid': refine_grid.tolist(),
        'losses': refine_losses,
        'best_idx': best_refine_idx,
        'best_val': best_val,
    }

    return [best_val], best_result['combined'], best_result, coarse_info, refine_info


def grid_search_nd(loss_fn, model_name, cvd_type,
                   hc_W_dicts, hc_amps_dicts, delta_rdm_obs_dicts,
                   C_baseline, coarse_step=4, refine_step=1,
                   refine_range=5):
    """2-stage grid search for multi-parameter models.

    Uses scipy.optimize.differential_evolution for coarse search,
    then refines around the optimum with a local grid.

    Returns:
        best_params, best_loss, best_result, coarse_info, refine_info
    """
    from scipy.optimize import differential_evolution

    bounds = MODELS[model_name]['bounds']
    df = MODELS[model_name]['df']

    # Objective: negate combined similarity (minimize)
    def objective(params):
        C_shifted = get_design_matrix(model_name, params, cvd_type=cvd_type)
        r = loss_fn.compute(C_shifted, C_baseline,
                            hc_W_dicts, hc_amps_dicts, delta_rdm_obs_dicts)
        return -r['combined']

    # DE optimization
    pop = 12 if df <= 3 else 10
    maxit = 100 if df <= 3 else 60

    res = differential_evolution(
        objective, bounds,
        seed=42, maxiter=maxit, tol=1e-6,
        popsize=pop, mutation=(0.5, 1.5), recombination=0.7,
    )

    best_params = res.x.tolist()
    C_shifted = get_design_matrix(model_name, best_params, cvd_type=cvd_type)
    best_result = loss_fn.compute(C_shifted, C_baseline,
                                  hc_W_dicts, hc_amps_dicts,
                                  delta_rdm_obs_dicts)

    coarse_info = {
        'method': 'differential_evolution',
        'success': bool(res.success),
        'n_iter': int(res.nit),
        'n_fev': int(res.nfev),
    }
    refine_info = None  # DE already converges to fine resolution

    return best_params, best_result['combined'], best_result, coarse_info, refine_info


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Step 1: ΔRDM loss fitting (V1+V2 combined, W-fixed)')
    parser.add_argument('--output_dir', type=str, default='results/sim')
    parser.add_argument('--cvd_subjects', nargs='+', default=CVD_SUBJECTS)
    parser.add_argument('--hc_subjects', nargs='+', default=HC_SUBJECTS)
    parser.add_argument('--models', nargs='+', default=FIT_MODELS)
    parser.add_argument('--metric', type=str, default='cosine',
                        choices=['cosine', 'pearson', 'spearman'])
    parser.add_argument('--baseline_dir', type=str,
                        default=str(LOCAL_BASELINE))
    args = parser.parse_args()

    print('=' * 60)
    print('Step 1: ΔRDM Loss Fitting (V1+V2 Combined, W-fixed)')
    print(f'CVD subjects: {args.cvd_subjects}')
    print(f'HC subjects: {args.hc_subjects}')
    print(f'Models: {args.models}')
    print(f'Metric: {args.metric}')
    print('=' * 60)

    loss_fn = DeltaRDM_V1V2_Equal(metric=args.metric)
    fitting_rois = loss_fn.rois  # ['V1', 'V2']
    C_baseline = create_basis_matrix(HUE_ANGLES, N_CHANNELS)

    # Load amplitudes for V1, V2 (all subjects)
    print('\nLoading amplitudes...')
    hc_amps = {}
    for roi in fitting_rois:
        hc_amps[roi] = {}
        for subj in args.hc_subjects:
            hc_amps[roi][subj] = load_amplitudes(args.baseline_dir, subj, roi)
    print(f'  Loaded HC: {len(args.hc_subjects)} subjects x {len(fitting_rois)} ROIs')

    # Precompute W for V1, V2
    print('Precomputing W...')
    hc_W = {}
    hc_alphas = {}
    for roi in fitting_rois:
        hc_W[roi], hc_alphas[roi] = precompute_hc_W(hc_amps[roi], C_baseline)
        alpha_str = ', '.join(f'{a:.1f}' for a in hc_alphas[roi].values())
        print(f'  {roi}: alphas = [{alpha_str}]')

    # Process each CVD subject
    for cvd_subj in args.cvd_subjects:
        cvd_type = CVD_TYPE[cvd_subj]
        print(f'\n{"="*50}')
        print(f'sub-{cvd_subj} ({cvd_type})')
        print(f'{"="*50}')

        # Load CVD amplitudes
        amp_cvd = {}
        for roi in fitting_rois:
            amp_cvd[roi] = load_amplitudes(args.baseline_dir, cvd_subj, roi)

        # Compute observed ΔRDM for V1, V2
        delta_rdm_obs = {}
        for roi in fitting_rois:
            d_obs, _, _, _ = compute_delta_rdm_obs(
                amp_cvd[roi], hc_amps[roi], distance='correlation')
            delta_rdm_obs[roi] = d_obs
            print(f'  ΔRDM_obs {roi}: '
                  f'mean={d_obs.mean():.4f}, std={d_obs.std():.4f}, '
                  f'range=[{d_obs.min():.4f}, {d_obs.max():.4f}]')

        # Fit each model
        for model_name in args.models:
            print(f'\n  --- {model_name} (df={MODELS[model_name]["df"]}) ---')

            df = MODELS[model_name]['df']

            # 2-stage grid search
            if df == 1:
                best_params, best_loss, best_result, coarse_info, refine_info = \
                    grid_search_1d(
                        loss_fn, model_name, cvd_type,
                        hc_W, hc_amps, delta_rdm_obs, C_baseline)
            else:
                best_params, best_loss, best_result, coarse_info, refine_info = \
                    grid_search_nd(
                        loss_fn, model_name, cvd_type,
                        hc_W, hc_amps, delta_rdm_obs, C_baseline)

            print(f'    Best params: {best_params}')
            print(f'    Best loss: {best_loss:.4f} '
                  f'(V1={best_result["V1"]:.4f}, V2={best_result["V2"]:.4f})')

            # Baseline: δ=0
            C_zero = get_design_matrix(
                model_name, [0] * df, cvd_type=cvd_type)
            baseline_result = loss_fn.compute(
                C_zero, C_baseline,
                hc_W, hc_amps, delta_rdm_obs)
            baseline_loss = baseline_result['combined']
            improvement = best_loss - baseline_loss
            print(f'    Baseline loss (δ=0): {baseline_loss:.4f}')
            print(f'    Improvement: {improvement:+.4f}')

            # Permutation test at best δθ
            print('    Running exact 8! permutation test...')
            C_best = get_design_matrix(
                model_name, best_params, cvd_type=cvd_type)
            perm_result = loss_fn.permutation_null(
                C_best, C_baseline,
                hc_W, hc_amps,
                amp_cvd, hc_amps,
                baseline_combined=baseline_loss)
            print(f'    label_perm_p = {perm_result["label_perm_p"]:.4f}')
            if 'baseline_improvement_p' in perm_result:
                print(f'    baseline_improvement_p = '
                      f'{perm_result["baseline_improvement_p"]:.4f}')

            # Per-color delta_theta for phase_b
            delta_theta_deg = get_delta_theta(
                model_name, best_params, cvd_type=cvd_type)

            # Phase B: per-color synthetic vulnerability
            vuln_synthetic = {}
            for roi in fitting_rois:
                delta_sim, _ = compute_delta_rdm_sim(
                    hc_W[roi], C_best, C_baseline,
                    distance='correlation')
                vuln_synthetic[roi] = delta_sim.tolist()

            # Build output
            out = {
                'subject': cvd_subj,
                'cvd_type': cvd_type,
                'loss_function': loss_fn.name,
                'metric': args.metric,
                'model': model_name,
                'model_df': MODELS[model_name]['df'],
                'timestamp': datetime.now().isoformat(),
                'hc_subjects': args.hc_subjects,
                'hc_alphas': {roi: hc_alphas[roi] for roi in fitting_rois},
                'phase_a': {
                    'best_params': best_params,
                    'best_loss': float(best_loss),
                    'best_loss_V1': float(best_result['V1']),
                    'best_loss_V2': float(best_result['V2']),
                    'baseline_loss': float(baseline_loss),
                    'baseline_loss_V1': float(baseline_result['V1']),
                    'baseline_loss_V2': float(baseline_result['V2']),
                    'improvement': float(improvement),
                    'label_perm_p': perm_result['label_perm_p'],
                    'baseline_improvement_p': perm_result.get(
                        'baseline_improvement_p', None),
                    'null_distribution_size': perm_result[
                        'null_distribution_size'],
                    'null_distribution_mean': perm_result[
                        'null_distribution_mean'],
                    'null_distribution_std': perm_result[
                        'null_distribution_std'],
                    'delta_theta_deg': delta_theta_deg.tolist(),
                    'coarse_grid': coarse_info,
                    'refine_grid': refine_info,
                },
                'phase_b': {
                    f'vuln_synthetic_{roi}': vuln_synthetic[roi]
                    for roi in fitting_rois
                },
                'color_names': COLOR_NAMES,
            }

            # Save
            out_dir = (Path(args.output_dir)
                       / f'sub-{cvd_subj}_{model_name}_delta_rdm')
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / 'result.json'
            with open(out_path, 'w') as f:
                json.dump(out, f, indent=2)
            print(f'    Saved: {out_path}')

    print('\nStep 1 (ΔRDM fitting) complete.')


if __name__ == '__main__':
    main()
