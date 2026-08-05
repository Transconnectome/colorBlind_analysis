#!/usr/bin/env python3
"""
Phase 3: Gaussian Process LOCO Decoder

Replaces/augments Forward Encoding channel model with GP for principled interpolation.
Uses periodic kernel (ExpSineSquared, periodicity=360) to exploit circular structure.

Sub-phases:
  3-1: basic     - Voxel-wise GP with periodic kernel, log-likelihood decoding
  3-2: fe_mean   - GP with FE group-mean as mean function
  3-3: cross_roi - Cross-ROI prior (V4 log-lik added to V1/V2 log-lik)

Usage:
    # SRM data (local, fast)
    python loco_gp.py --subject 01 --rois V1 V2 V3 V4 --subphase basic --alignment srm

    # Raw data (server, slower)
    python loco_gp.py --subject 01 --rois V1 --subphase basic --alignment raw

Output:
    results/gp/sub-{ID}_gp_{subphase}.json
"""

import sys
import argparse
import json
import numpy as np
from pathlib import Path
from datetime import datetime
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import (
    ConstantKernel, ExpSineSquared, WhiteKernel, RBF
)

# Resolve paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
RESULTS_DIR = PROJECT_DIR / 'results' / 'gp'
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Import shared utilities
MCV_DIR = SCRIPT_DIR.parents[1] / 'model_comparison_validation' / 'scripts'
sys.path.insert(0, str(MCV_DIR))
from loco_baseline import (
    load_amplitudes, circular_distance, HUE_ANGLES,
)

# Import basis functions + fit_W for FE mean
import importlib.util
_spec = importlib.util.spec_from_file_location(
    'utils_color_decoding',
    SCRIPT_DIR.parents[2] / 'utils' / 'utils_color_decoding.py'
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
create_basis_functions = _mod.create_basis_functions

# Constants
HC_SUBJECTS = [f'{i:02d}' for i in range(1, 8)]
CVD_SUBJECTS = [f'{i:02d}' for i in range(8, 11)]
ROIS = ['V1', 'V2', 'V3', 'V4']

BASELINE_DIR = Path('/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010')


# ============================================================================
# GP Kernel & Fitting
# ============================================================================

def make_periodic_kernel():
    """Create periodic kernel for circular hue (periodicity=360 fixed)."""
    kernel = (
        ConstantKernel(1.0, constant_value_bounds=(1e-3, 1e3)) *
        ExpSineSquared(
            length_scale=1.0,
            periodicity=360.0,
            length_scale_bounds=(1e-2, 1e2),
            periodicity_bounds='fixed'
        ) +
        WhiteKernel(noise_level=0.1, noise_level_bounds=(1e-5, 1e1))
    )
    return kernel


def fit_voxelwise_gp(hues_train, X_train, hues_predict=None):
    """Fit independent GP per voxel/feature.

    Args:
        hues_train: (n_train,) hue angles in degrees
        X_train: (n_train, n_features) brain patterns
        hues_predict: (n_pred,) hue angles to predict at (default: 0-359)

    Returns:
        mean_pred: (n_pred, n_features) predicted mean
        std_pred: (n_pred, n_features) predicted std
        log_marginal: sum of log marginal likelihoods across voxels
    """
    if hues_predict is None:
        hues_predict = np.arange(360)

    n_features = X_train.shape[1]
    n_pred = len(hues_predict)

    mean_pred = np.zeros((n_pred, n_features))
    std_pred = np.zeros((n_pred, n_features))
    log_marginal = 0.0

    hues_train_2d = hues_train.reshape(-1, 1)
    hues_pred_2d = hues_predict.reshape(-1, 1)

    for v in range(n_features):
        y = X_train[:, v]
        kernel = make_periodic_kernel()
        gp = GaussianProcessRegressor(
            kernel=kernel, n_restarts_optimizer=2,
            alpha=1e-6, normalize_y=True
        )
        gp.fit(hues_train_2d, y)
        mu, sigma = gp.predict(hues_pred_2d, return_std=True)
        mean_pred[:, v] = mu
        std_pred[:, v] = sigma
        log_marginal += gp.log_marginal_likelihood_value_

    return mean_pred, std_pred, log_marginal


def gp_decode(hues_train, X_train, X_test, candidate_hues=None):
    """Decode hue for test samples using GP log-likelihood.

    For each test sample, compute log p(x_test | hue) across candidate hues.
    Under Gaussian assumption: log p = -0.5 * sum_v [(x_v - mu_v(h))^2 / sigma_v(h)^2]

    Args:
        hues_train: (n_train,) training hue angles
        X_train: (n_train, n_features) training patterns
        X_test: (n_test, n_features) test patterns
        candidate_hues: hue angles to evaluate (default: 0-359)

    Returns:
        pred_hues: (n_test,) predicted hue angles
        log_liks: (n_test, n_candidates) log-likelihood matrix
    """
    if candidate_hues is None:
        candidate_hues = np.arange(360)

    # Fit GPs and get predictions at all candidate hues
    mean_pred, std_pred, _ = fit_voxelwise_gp(hues_train, X_train, candidate_hues)
    # mean_pred: (n_candidates, n_features)
    # std_pred: (n_candidates, n_features)

    # Clamp std to avoid division by zero
    std_pred = np.maximum(std_pred, 1e-6)

    n_test = X_test.shape[0]
    n_candidates = len(candidate_hues)
    log_liks = np.zeros((n_test, n_candidates))

    for i in range(n_test):
        for h_idx in range(n_candidates):
            diff = X_test[i] - mean_pred[h_idx]
            log_liks[i, h_idx] = -0.5 * np.sum(
                (diff / std_pred[h_idx]) ** 2 + np.log(std_pred[h_idx] ** 2)
            )

    pred_hues = candidate_hues[np.argmax(log_liks, axis=1)]
    return pred_hues, log_liks


# ============================================================================
# Sub-phase 3-1: Basic GP (periodic kernel only)
# ============================================================================

def loco_gp_basic(amp):
    """LOCO with voxel-wise GP, periodic kernel, log-likelihood decoding.

    Args:
        amp: (n_runs, n_colors, n_features)

    Returns:
        results: dict with mean_mae, fold_maes
    """
    n_runs, n_colors, n_features = amp.shape
    fold_maes = []

    for test_color in range(n_colors):
        train_colors = [c for c in range(n_colors) if c != test_color]
        train_hues = np.array([HUE_ANGLES[c] for c in train_colors])
        test_hue = HUE_ANGLES[test_color]

        # Mean pattern across runs for training colors
        X_train_mean = amp[:, train_colors, :].mean(axis=0)  # (7, n_features)
        X_test = amp[:, test_color, :]  # (n_runs, n_features)

        pred_hues, _ = gp_decode(train_hues, X_train_mean, X_test)
        errors = circular_distance(np.full(n_runs, test_hue), pred_hues)
        fold_maes.append(float(np.mean(errors)))

        print(f'    Color {test_color} ({test_hue}deg): MAE={np.mean(errors):.1f}')

    return {
        'mean_mae': float(np.mean(fold_maes)),
        'fold_maes': fold_maes,
    }


# ============================================================================
# Sub-phase 3-2: GP + FE Mean Function
# ============================================================================

def fit_W_from_amps(other_amps_dict, exclude_color_idx=None):
    """Compute group W from HC subjects for FE mean function."""
    W_others = []
    for s, a in other_amps_dict.items():
        n_r, n_c, n_v = a.shape
        if exclude_color_idx is not None:
            tc = [c for c in range(n_c) if c != exclude_color_idx]
            X = a[:, tc, :].reshape(-1, n_v)
            hues = np.tile(np.array([HUE_ANGLES[c] for c in tc]), n_r)
        else:
            X = a.reshape(-1, n_v)
            hues = np.tile(np.array(HUE_ANGLES), n_r)

        basis_full = create_basis_functions(n_channels=6)
        C = basis_full[hues.astype(int)]
        W = np.linalg.pinv(C) @ X
        W_others.append(W)

    return np.mean(W_others, axis=0)  # (6, n_features)


def gp_decode_with_fe_mean(hues_train, X_train, X_test, W_group):
    """GP decoder where mean function is FE group prediction.

    GP learns residuals: r(theta) = x(theta) - W_group @ basis(theta)

    Args:
        hues_train: (n_train,) training hue angles
        X_train: (n_train, n_features) training patterns
        X_test: (n_test, n_features) test patterns
        W_group: (6, n_features) group FE weights

    Returns:
        pred_hues: (n_test,)
        log_liks: (n_test, 360)
    """
    basis_full = create_basis_functions(n_channels=6)
    candidate_hues = np.arange(360)

    # FE mean predictions at training hues
    fe_train = basis_full[hues_train.astype(int)] @ W_group  # (n_train, n_features)
    residuals_train = X_train - fe_train

    # Fit GP on residuals
    mean_resid, std_resid, _ = fit_voxelwise_gp(
        hues_train, residuals_train, candidate_hues
    )

    # Full prediction = FE mean + GP residual
    fe_pred = basis_full @ W_group  # (360, n_features)
    mean_pred = fe_pred + mean_resid  # (360, n_features)

    std_pred = np.maximum(std_resid, 1e-6)

    n_test = X_test.shape[0]
    log_liks = np.zeros((n_test, 360))

    for i in range(n_test):
        for h_idx in range(360):
            diff = X_test[i] - mean_pred[h_idx]
            log_liks[i, h_idx] = -0.5 * np.sum(
                (diff / std_pred[h_idx]) ** 2 + np.log(std_pred[h_idx] ** 2)
            )

    pred_hues = candidate_hues[np.argmax(log_liks, axis=1)]
    return pred_hues, log_liks


def loco_gp_fe_mean(amp, other_amps_dict):
    """LOCO with GP + FE group-mean function.

    Args:
        amp: (n_runs, n_colors, n_features) target subject
        other_amps_dict: {subj: (n_runs, n_colors, n_features)} HC group

    Returns:
        results: dict with mean_mae, fold_maes
    """
    n_runs, n_colors, n_features = amp.shape
    fold_maes = []

    for test_color in range(n_colors):
        train_colors = [c for c in range(n_colors) if c != test_color]
        train_hues = np.array([HUE_ANGLES[c] for c in train_colors])
        test_hue = HUE_ANGLES[test_color]

        # Group W excluding test color (leakage fix)
        W_group = fit_W_from_amps(other_amps_dict, exclude_color_idx=test_color)

        X_train_mean = amp[:, train_colors, :].mean(axis=0)
        X_test = amp[:, test_color, :]

        pred_hues, _ = gp_decode_with_fe_mean(
            train_hues, X_train_mean, X_test, W_group
        )
        errors = circular_distance(np.full(n_runs, test_hue), pred_hues)
        fold_maes.append(float(np.mean(errors)))

        print(f'    Color {test_color} ({test_hue}deg): MAE={np.mean(errors):.1f}')

    return {
        'mean_mae': float(np.mean(fold_maes)),
        'fold_maes': fold_maes,
    }


# ============================================================================
# Sub-phase 3-3: Cross-ROI Prior
# ============================================================================

def loco_gp_cross_roi(amps_by_roi, primary_roi, prior_roi='V4'):
    """Cross-ROI GP decoder: log_posterior = log_lik(primary) + log_lik(prior_roi).

    Args:
        amps_by_roi: {roi: (n_runs, n_colors, n_features)}
        primary_roi: ROI to decode (e.g., 'V1')
        prior_roi: ROI to use as topological prior (e.g., 'V4')

    Returns:
        results: dict with mean_mae, fold_maes
    """
    amp_primary = amps_by_roi[primary_roi]
    amp_prior = amps_by_roi[prior_roi]
    n_runs, n_colors, _ = amp_primary.shape
    fold_maes = []

    for test_color in range(n_colors):
        train_colors = [c for c in range(n_colors) if c != test_color]
        train_hues = np.array([HUE_ANGLES[c] for c in train_colors])
        test_hue = HUE_ANGLES[test_color]

        # Primary ROI
        X_train_primary = amp_primary[:, train_colors, :].mean(axis=0)
        X_test_primary = amp_primary[:, test_color, :]
        _, log_liks_primary = gp_decode(train_hues, X_train_primary, X_test_primary)

        # Prior ROI
        X_train_prior = amp_prior[:, train_colors, :].mean(axis=0)
        X_test_prior = amp_prior[:, test_color, :]
        _, log_liks_prior = gp_decode(train_hues, X_train_prior, X_test_prior)

        # Combined log posterior
        log_posterior = log_liks_primary + log_liks_prior
        candidate_hues = np.arange(360)
        pred_hues = candidate_hues[np.argmax(log_posterior, axis=1)]

        errors = circular_distance(np.full(n_runs, test_hue), pred_hues)
        fold_maes.append(float(np.mean(errors)))

        print(f'    Color {test_color} ({test_hue}deg): MAE={np.mean(errors):.1f}')

    return {
        'mean_mae': float(np.mean(fold_maes)),
        'fold_maes': fold_maes,
    }


# ============================================================================
# FE OLS Baseline (for comparison)
# ============================================================================

def loco_fe_ols_baseline(amp):
    """Standard FE OLS LOCO baseline for comparison."""
    n_runs, n_colors, n_features = amp.shape
    fold_maes = []

    for test_color in range(n_colors):
        train_colors = [c for c in range(n_colors) if c != test_color]
        train_hues = np.array([HUE_ANGLES[c] for c in train_colors])
        test_hue = HUE_ANGLES[test_color]

        X_train = amp[:, train_colors, :].reshape(-1, n_features)
        hues_train = np.tile(train_hues, n_runs)

        basis_full = create_basis_functions(n_channels=6)
        C = basis_full[hues_train.astype(int)]
        W = np.linalg.pinv(C) @ X_train

        X_test = amp[:, test_color, :]
        channel_responses = W @ X_test.T
        pred_hues = np.zeros(n_runs)
        for i in range(n_runs):
            resp = channel_responses[:, i]
            corrs = np.array([np.corrcoef(resp, basis_full[h])[0, 1] for h in range(360)])
            pred_hues[i] = np.nanargmax(corrs)

        errors = circular_distance(np.full(n_runs, test_hue), pred_hues)
        fold_maes.append(float(np.mean(errors)))

    return {
        'mean_mae': float(np.mean(fold_maes)),
        'fold_maes': fold_maes,
    }


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Phase 3: GP LOCO')
    parser.add_argument('--subject', type=str, required=True)
    parser.add_argument('--rois', nargs='+', default=ROIS)
    parser.add_argument('--subphase', type=str, default='basic',
                        choices=['basic', 'fe_mean', 'cross_roi', 'all'])
    parser.add_argument('--alignment', type=str, default='srm',
                        choices=['raw', 'procrustes', 'srm'])
    parser.add_argument('--baseline_dir', type=str, default=str(BASELINE_DIR))
    parser.add_argument('--output_dir', type=str, default=str(RESULTS_DIR))
    args = parser.parse_args()

    baseline_dir = Path(args.baseline_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    subphases = [args.subphase] if args.subphase != 'all' else ['basic', 'fe_mean', 'cross_roi']

    print('=' * 70)
    print(f'Phase 3: GP LOCO (subphase={args.subphase})')
    print(f'Subject: sub-{args.subject}')
    print(f'ROIs: {args.rois}')
    print(f'Alignment: {args.alignment}')
    print('=' * 70)

    # Load subject data for all ROIs
    amps_by_roi = {}
    for roi in args.rois:
        try:
            amps_by_roi[roi] = load_amplitudes(
                str(baseline_dir), args.subject, roi, args.alignment)
            print(f'  Loaded {roi}: {amps_by_roi[roi].shape}')
        except FileNotFoundError as e:
            print(f'  ERROR: {e}')

    # Load HC group data for fe_mean subphase
    other_amps = {}
    if 'fe_mean' in subphases:
        hc_pool = [s for s in HC_SUBJECTS if s != args.subject]
        for roi in args.rois:
            other_amps[roi] = {}
            for s in hc_pool:
                try:
                    other_amps[roi][s] = load_amplitudes(
                        str(baseline_dir), s, roi, args.alignment)
                except FileNotFoundError:
                    pass

    all_results = {}

    for roi in args.rois:
        if roi not in amps_by_roi:
            continue
        amp = amps_by_roi[roi]

        print(f'\n{"=" * 50}')
        print(f'ROI: {roi}')
        print(f'{"=" * 50}')

        roi_result = {}

        # FE OLS baseline
        print('  Computing FE OLS baseline...')
        ols = loco_fe_ols_baseline(amp)
        roi_result['FE_OLS_baseline'] = ols
        print(f'  FE OLS baseline MAE: {ols["mean_mae"]:.1f}')

        # Sub-phase 3-1: Basic GP
        if 'basic' in subphases:
            print('\n  --- Sub-phase 3-1: Basic GP ---')
            gp_basic = loco_gp_basic(amp)
            roi_result['GP_basic'] = gp_basic
            delta = gp_basic['mean_mae'] - ols['mean_mae']
            print(f'  GP basic MAE: {gp_basic["mean_mae"]:.1f} (delta={delta:+.1f})')

        # Sub-phase 3-2: GP + FE Mean
        if 'fe_mean' in subphases and roi in other_amps and other_amps[roi]:
            print('\n  --- Sub-phase 3-2: GP + FE Mean ---')
            gp_fe = loco_gp_fe_mean(amp, other_amps[roi])
            roi_result['GP_fe_mean'] = gp_fe
            delta = gp_fe['mean_mae'] - ols['mean_mae']
            print(f'  GP+FE mean MAE: {gp_fe["mean_mae"]:.1f} (delta={delta:+.1f})')

        # Sub-phase 3-3: Cross-ROI (V4 prior for V1, V2, V3)
        if 'cross_roi' in subphases and roi != 'V4' and 'V4' in amps_by_roi:
            print('\n  --- Sub-phase 3-3: Cross-ROI Prior (V4) ---')
            gp_cross = loco_gp_cross_roi(amps_by_roi, roi, 'V4')
            roi_result['GP_cross_roi'] = gp_cross
            delta = gp_cross['mean_mae'] - ols['mean_mae']
            print(f'  Cross-ROI MAE: {gp_cross["mean_mae"]:.1f} (delta={delta:+.1f})')

        all_results[roi] = roi_result

    # Save
    output_file = output_dir / f'sub-{args.subject}_gp_{args.subphase}.json'
    save_data = {
        'subject': args.subject,
        'subject_group': 'HC' if args.subject in HC_SUBJECTS else 'CVD',
        'subphases': subphases,
        'alignment': args.alignment,
        'rois': args.rois,
        'kernel': 'ConstantKernel * ExpSineSquared(periodicity=360, fixed) + WhiteKernel',
        'results': all_results,
        'timestamp': datetime.now().isoformat(),
    }
    with open(output_file, 'w') as f:
        json.dump(save_data, f, indent=2)
    print(f'\nSaved: {output_file}')

    # Summary
    print(f'\n{"=" * 70}')
    print('SUMMARY')
    print(f'{"=" * 70}')
    for roi in args.rois:
        if roi not in all_results:
            continue
        r = all_results[roi]
        ols_mae = r['FE_OLS_baseline']['mean_mae']
        line = f'{roi}: FE_OLS={ols_mae:.1f}'
        if 'GP_basic' in r:
            line += f' | GP_basic={r["GP_basic"]["mean_mae"]:.1f}'
        if 'GP_fe_mean' in r:
            line += f' | GP+FE={r["GP_fe_mean"]["mean_mae"]:.1f}'
        if 'GP_cross_roi' in r:
            line += f' | Cross-ROI={r["GP_cross_roi"]["mean_mae"]:.1f}'
        print(f'  {line}')


if __name__ == '__main__':
    main()
