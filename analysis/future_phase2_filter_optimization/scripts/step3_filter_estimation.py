#!/usr/bin/env python3
"""
step3_filter_estimation.py — Two-level T_ψ filter estimation + nested model comparison.

Level 1 (Pattern): Confirms T_ψ* ≈ 0 (per-color patterns already match).
Level 2 (RDM): Finds T_ψ* that minimizes pairwise distance error vs HC mean RDM.

Nested models:
  Model 0 (1 param): Cone shift δ_θ(θ; Δλ) from Stockman physics
  Model A (4 params): Fourier T_ψ(θ) = θ + a₁cos + b₁sin + a₂cos2 + b₂sin2
  Model B (8 params): Per-color free shift T(θ_i) = θ_i + δ_i

Usage:
    mpirun -np 1 python scripts/step3_filter_estimation.py \
        --model_dir results/step1_model \
        --validation_json ../future_phase1_forward_model/results/cone_shift/cone_shift_validation_results.json \
        --output_dir results/step3_filter \
        --subject_idx 1   # SLURM array: 1=sub-08, 2=sub-09, 3=sub-10
"""

import argparse
import json
import sys
import time
import numpy as np
from pathlib import Path
from datetime import datetime
from scipy.optimize import minimize

# -- Imports --
PHASE1_SCRIPTS = Path(__file__).resolve().parents[2] / 'future_phase1_forward_model' / 'scripts'
sys.path.insert(0, str(PHASE1_SCRIPTS))
PHASE2_SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(PHASE2_SCRIPTS))

from utils_forward_model import (
    CVD_SUBJECTS, K_VALUES, N_CHANNELS, HUE_ANGLES, ROIS,
    create_basis_matrix, create_basis_full, predict_patterns,
    compute_rdm, rdm_upper_tri,
)
from utils_filter import (
    T_psi, T_psi_free, T_cone_shift,
    loss_pattern, loss_rdm, loss_rdm_with_penalty,
    compute_predicted_rdm, compute_rdm_improvement, compute_rdm_spearman,
    check_monotonicity, nested_model_comparison,
    N_PAIRS, PAIR_LABELS, COLOR_NAMES,
)

ROI_DISPLAY = {'V1': 'V1', 'V2': 'V2', 'V3': 'V3', 'V4': 'hV4'}
CVD_TYPES = {'08': 'deutan', '09': 'protan', '10': 'deutan'}
ROIS_FILTER = ['V4', 'V2', 'V1']  # hV4 primary, V2 validation, V1 exploratory


def load_step1_data(model_dir, roi_label, cvd_subj):
    """Load W₀, Y_mean, HC RDM, baseline RDM from step1 outputs."""
    model_dir = Path(model_dir)
    roi_dir = model_dir / roi_label / f'sub-{cvd_subj}'

    W0 = np.load(roi_dir / 'W0.npy')
    Y_mean = np.load(roi_dir / 'Y_mean.npy')
    baseline_rdm = np.load(roi_dir / 'baseline_rdm.npy')
    cvd_rdm = np.load(roi_dir / 'cvd_rdm.npy')
    hc_rdm_mean = np.load(model_dir / roi_label / 'hc_rdm_mean.npy')

    return W0, Y_mean, baseline_rdm, cvd_rdm, hc_rdm_mean


def fit_model_0(W0, hc_rdm_mean, n_channels, cvd_type, validation_json_data,
                cvd_subj):
    """Model 0: Evaluate cone-shift-based angles (1 param from physics).

    Uses θ_equiv from cone_shift_validation_results.json.
    No optimization — just evaluate the loss at the physically derived shift.
    """
    subj_key = f'sub-{cvd_subj}'
    if subj_key not in validation_json_data:
        return None

    theta_equiv = np.array(validation_json_data[subj_key]['theta_equiv_deg'],
                           dtype=float)
    delta_lambda = validation_json_data[subj_key].get('delta_lambda_nm', 0)

    # Evaluate predicted RDM at θ_equiv
    pred_rdm = compute_predicted_rdm(W0, theta_equiv, n_channels)
    hc_upper = hc_rdm_mean[np.triu_indices(8, k=1)]
    pred_upper = pred_rdm[np.triu_indices(8, k=1)]

    rss = float(np.sum((pred_upper - hc_upper) ** 2))
    rho, p_rho = compute_rdm_spearman(pred_rdm, hc_rdm_mean)

    return {
        'model': 'Model_0',
        'n_params': 1,
        'delta_lambda_nm': float(delta_lambda),
        'theta_equiv': theta_equiv.tolist(),
        'rss': rss,
        'rdm_spearman_rho': rho,
        'rdm_spearman_p': p_rho,
    }


def fit_model_A(W0, Y_mean, hc_rdm_mean, baseline_rdm, n_channels):
    """Model A: Fourier T_ψ with 4 parameters, multi-start optimization."""
    hc_upper = hc_rdm_mean[np.triu_indices(8, k=1)]

    # -- Level 1: Pattern-level (confirmation) --
    def pattern_obj(psi):
        return loss_pattern(psi, W0, Y_mean, n_channels, transform='fourier')

    res_pattern = minimize(pattern_obj, x0=np.zeros(4), method='L-BFGS-B',
                           options={'maxiter': 500})
    psi_pattern = res_pattern.x
    max_shift_pattern = float(np.max(np.abs(
        T_psi(HUE_ANGLES, psi_pattern) - HUE_ANGLES)))

    # -- Level 2: RDM-level (the real test) --
    def rdm_obj(psi):
        return loss_rdm_with_penalty(psi, W0, hc_upper, n_channels,
                                     transform='fourier', penalty_scale=1000.0)

    # Multi-start: x0=0 + 5 random starts
    best_res = None
    best_loss = np.inf
    rng = np.random.RandomState(42)

    starts = [np.zeros(4)]
    for _ in range(5):
        starts.append(rng.uniform(-30, 30, size=4))

    for x0 in starts:
        res = minimize(rdm_obj, x0=x0, method='L-BFGS-B',
                       options={'maxiter': 1000})
        if res.fun < best_loss:
            best_loss = res.fun
            best_res = res

    psi_star = best_res.x
    theta_star = T_psi(HUE_ANGLES, psi_star)
    is_mono, min_deriv = check_monotonicity(psi_star)

    # Evaluate pure RDM loss (without penalty) at optimum
    rss = loss_rdm(psi_star, W0, hc_upper, n_channels, transform='fourier')
    pred_rdm = compute_predicted_rdm(W0, theta_star, n_channels)
    rho, p_rho = compute_rdm_spearman(pred_rdm, hc_rdm_mean)

    # RDM improvement
    improvement = compute_rdm_improvement(psi_star, W0, hc_rdm_mean,
                                          baseline_rdm, n_channels,
                                          transform='fourier')

    return {
        'model': 'Model_A',
        'n_params': 4,
        'psi_star': psi_star.tolist(),
        'theta_transformed': theta_star.tolist(),
        'max_shift_deg': float(np.max(np.abs(theta_star - HUE_ANGLES))),
        'rss': float(rss),
        'rdm_spearman_rho': rho,
        'rdm_spearman_p': p_rho,
        'is_monotone': bool(is_mono),
        'min_derivative': float(min_deriv),
        'n_starts': len(starts),
        'optimizer_success': bool(best_res.success),
        'optimizer_message': str(best_res.message),
        'improvement': improvement,
        # Level 1 results
        'pattern_level': {
            'psi_pattern': psi_pattern.tolist(),
            'max_shift_deg': max_shift_pattern,
            'loss_pattern': float(res_pattern.fun),
            'near_identity': bool(max_shift_pattern < 5.0),
        },
    }


def fit_model_B(W0, hc_rdm_mean, baseline_rdm, n_channels):
    """Model B: Per-color free shift with 8 parameters."""
    hc_upper = hc_rdm_mean[np.triu_indices(8, k=1)]

    def rdm_obj(deltas):
        return loss_rdm(deltas, W0, hc_upper, n_channels, transform='free')

    # Multi-start: x0=0 + 5 random
    best_res = None
    best_loss = np.inf
    rng = np.random.RandomState(42)

    starts = [np.zeros(8)]
    for _ in range(5):
        starts.append(rng.uniform(-45, 45, size=8))

    for x0 in starts:
        res = minimize(rdm_obj, x0=x0, method='L-BFGS-B',
                       options={'maxiter': 1000})
        if res.fun < best_loss:
            best_loss = res.fun
            best_res = res

    deltas_star = best_res.x
    theta_star = T_psi_free(HUE_ANGLES, deltas_star)
    rss = float(best_res.fun)

    pred_rdm = compute_predicted_rdm(W0, theta_star, n_channels)
    rho, p_rho = compute_rdm_spearman(pred_rdm, hc_rdm_mean)

    improvement = compute_rdm_improvement(deltas_star, W0, hc_rdm_mean,
                                          baseline_rdm, n_channels,
                                          transform='free')

    return {
        'model': 'Model_B',
        'n_params': 8,
        'deltas_star': deltas_star.tolist(),
        'theta_transformed': theta_star.tolist(),
        'per_color_shifts': {COLOR_NAMES[i]: float(deltas_star[i])
                             for i in range(8)},
        'max_shift_deg': float(np.max(np.abs(deltas_star))),
        'rss': float(rss),
        'rdm_spearman_rho': rho,
        'rdm_spearman_p': p_rho,
        'improvement': improvement,
    }


def run_subject(cvd_subj, model_dir, validation_json_data, output_dir):
    """Run full filter estimation for one CVD subject across ROIs."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    cvd_type = CVD_TYPES.get(cvd_subj, 'deutan')
    results = {
        'subject': f'sub-{cvd_subj}',
        'cvd_type': cvd_type,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }

    for roi in ROIS_FILTER:
        roi_label = ROI_DISPLAY.get(roi, roi)
        n_channels = N_CHANNELS
        print(f'\n{"="*60}')
        print(f'sub-{cvd_subj} | {roi_label}')
        print(f'{"="*60}')

        try:
            W0, Y_mean, baseline_rdm, cvd_rdm, hc_rdm_mean = \
                load_step1_data(model_dir, roi_label, cvd_subj)
        except FileNotFoundError as e:
            print(f'  SKIP: {e}')
            continue

        print(f'  W₀: {W0.shape}, Y_mean: {Y_mean.shape}')

        # Baseline: identity transform (no shift)
        hc_upper = hc_rdm_mean[np.triu_indices(8, k=1)]
        baseline_upper = baseline_rdm[np.triu_indices(8, k=1)]
        baseline_rss = float(np.sum((baseline_upper - hc_upper) ** 2))
        baseline_rho, baseline_p = compute_rdm_spearman(baseline_rdm, hc_rdm_mean)

        print(f'  Baseline RDM RSS: {baseline_rss:.6f}')
        print(f'  Baseline RDM Spearman: rho={baseline_rho:.4f}, p={baseline_p:.4f}')

        # -- Model 0: Cone shift --
        t0 = time.time()
        m0 = fit_model_0(W0, hc_rdm_mean, n_channels, cvd_type,
                         validation_json_data, cvd_subj)
        if m0:
            print(f'  Model 0: RSS={m0["rss"]:.6f}, '
                  f'rho={m0["rdm_spearman_rho"]:.4f} ({time.time()-t0:.1f}s)')

        # -- Model A: Fourier (4 params) --
        t0 = time.time()
        mA = fit_model_A(W0, Y_mean, hc_rdm_mean, baseline_rdm, n_channels)
        print(f'  Model A: RSS={mA["rss"]:.6f}, '
              f'rho={mA["rdm_spearman_rho"]:.4f}, '
              f'max_shift={mA["max_shift_deg"]:.1f}°, '
              f'mono={mA["is_monotone"]} ({time.time()-t0:.1f}s)')
        print(f'    Pattern T_ψ* near identity: {mA["pattern_level"]["near_identity"]} '
              f'(max_shift={mA["pattern_level"]["max_shift_deg"]:.2f}°)')
        print(f'    RDM improvement: {mA["improvement"]["pct_improvement"]:.1f}%')

        # -- Model B: Free (8 params) --
        t0 = time.time()
        mB = fit_model_B(W0, hc_rdm_mean, baseline_rdm, n_channels)
        print(f'  Model B: RSS={mB["rss"]:.6f}, '
              f'rho={mB["rdm_spearman_rho"]:.4f}, '
              f'max_shift={mB["max_shift_deg"]:.1f}° ({time.time()-t0:.1f}s)')
        print(f'    RDM improvement: {mB["improvement"]["pct_improvement"]:.1f}%')

        # -- Nested model comparison --
        rss_dict = {'Model_A': mA['rss'], 'Model_B': mB['rss']}
        df_dict = {'Model_A': 4, 'Model_B': 8}
        if m0:
            rss_dict['Model_0'] = m0['rss']
            df_dict['Model_0'] = 1

        comparison = nested_model_comparison(rss_dict, df_dict, N_PAIRS)
        print(f'  Preferred model (AICc): {comparison["preferred_model"]}')
        for test_name, test_res in comparison['f_tests'].items():
            print(f'    F-test {test_name}: F={test_res["F"]:.3f}, '
                  f'p={test_res["p"]:.4f}, sig={test_res["significant"]}')

        # Store results for this ROI
        results[roi_label] = {
            'baseline': {
                'rss': baseline_rss,
                'rdm_spearman_rho': baseline_rho,
                'rdm_spearman_p': baseline_p,
            },
            'model_0': m0,
            'model_A': mA,
            'model_B': mB,
            'comparison': comparison,
        }

    # Save results
    out_file = output_dir / f'sub-{cvd_subj}_filter_results.json'
    with open(out_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f'\nResults saved to {out_file}')

    return results


def main():
    parser = argparse.ArgumentParser(
        description='Step 3: Two-level T_ψ filter estimation')
    parser.add_argument('--model_dir', type=str,
                        default='results/step1_model')
    parser.add_argument('--validation_json', type=str,
                        default='../future_phase1_forward_model/results/cone_shift/cone_shift_validation_results.json')
    parser.add_argument('--output_dir', type=str,
                        default='results/step3_filter')
    parser.add_argument('--subject_idx', type=int, default=None,
                        help='SLURM array index: 1=sub-08, 2=sub-09, 3=sub-10')
    args = parser.parse_args()

    # Load cone shift validation data
    val_path = Path(args.validation_json)
    if val_path.exists():
        with open(val_path) as f:
            validation_json_data = json.load(f)
    else:
        print(f'WARNING: validation JSON not found at {val_path}, Model 0 will be skipped')
        validation_json_data = {}

    if args.subject_idx is not None:
        # SLURM array mode: run single subject
        cvd_subj = CVD_SUBJECTS[args.subject_idx - 1]
        run_subject(cvd_subj, args.model_dir, validation_json_data,
                    args.output_dir)
    else:
        # Run all CVD subjects
        for cvd_subj in CVD_SUBJECTS:
            run_subject(cvd_subj, args.model_dir, validation_json_data,
                        args.output_dir)


if __name__ == '__main__':
    main()
