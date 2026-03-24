#!/usr/bin/env python3
"""
step1_fit_rdm_v2.py — SRM-RDM fitting with 7-fold LOO (v2, corrected).

For each CVD subject x ROI x distortion model:
  For each LOO fold (7 folds):
    Path A (Voxel→SRM): C(θ+δ) @ W_ridge → Y_shifted (voxel)
                         → SVD project into SRM space → Z_shifted
                         → RDM(Z_shifted) vs RDM(Z_cvd)
    Path B (Voxel-only): C(θ+δ) @ W_ridge → RDM in voxel space
                         → RDM_pred vs RDM_cvd_voxel

  Aggregate: 7-fold δθ → median, SD, AICc

Correction (2026-03-23):
  Old Path A used A_g @ C(θ+δ)^T — predicting directly in SRM space.
  This ignores voxel-level distortion and lets SRM alignment absorb the signal.

  New Path A:
  1. Predict voxel response using HC's ridge W: Y_shifted = C(θ+δ) @ W_HC
  2. Project Y_shifted into SRM space via SVD (same as CVD projection)
  3. Compare RDM in SRM space with Z_cvd RDM

  This preserves voxel-level cone-shift distortion through the SRM mapping.

Uses precomputed data from step0.

Usage:
    python scripts/step1_fit_rdm_v2.py \
        --precomputed_dir results/precomputed \
        --output_dir results/v2/step1_rdm
"""

import argparse
import json
import numpy as np
from pathlib import Path
from datetime import datetime
from scipy.optimize import differential_evolution
from scipy.spatial.distance import pdist, squareform
from scipy.stats import spearmanr
import sys

_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR))

_FWD_DIR = str(Path(__file__).resolve().parent.parent.parent.parent
               / 'future_phase1_forward_model' / 'scripts')
sys.path.insert(0, _FWD_DIR)

from utils_forward_model import (
    HC_SUBJECTS, CVD_SUBJECTS, ROIS, K_VALUES, N_CHANNELS,
    HUE_ANGLES, load_amplitudes, create_basis_matrix,
)
from utils_distortion_models import (
    MODELS, get_design_matrix, get_initial_params, compute_aicc,
)

LOCAL_BASELINE = Path(__file__).resolve().parent.parent.parent.parent \
    / 'phase1_preprocess_decoding' / 'results' / 'full_dataset_C010'

CVD_TYPE = {'08': 'deutan', '09': 'protan', '10': 'normal'}

# Models to fit (skip fourier_8 by default — same df as per_color)
FIT_MODELS = ['cone_1way', 'cone_3way', 'fourier', 'per_color']


# ============================================================================
# SVD projection (same as step0_precompute.py)
# ============================================================================

def project_new_subject_svd(shared_response, beta_new):
    """Project new subject into SRM space via SVD.

    Same function as step0. Treats beta_new as a novel subject's response
    and finds the orthonormal projection that best maps it to shared space.

    Args:
        shared_response: (k, 8) shared response from SRM
        beta_new: (8, V_s) response matrix (run-averaged or predicted)

    Returns:
        R_new: (V_s, k) orthonormal projection
    """
    S = shared_response
    W_init = beta_new.T @ np.linalg.pinv(S)  # (V_s, k)
    U, _, Vt = np.linalg.svd(W_init, full_matrices=False)
    return U @ Vt


# ============================================================================
# Path A (corrected): Voxel prediction → SRM projection → RDM
# ============================================================================

def rdm_loss_voxel_to_srm(params, model_name, W_ridge_list,
                           shared_response, cvd_rdm_upper, cvd_type):
    """Voxel→SRM RDM loss.

    For each training HC:
      1. Y_shifted = C(θ+δ) @ W_HC  — predicted voxel response with cone shift
      2. R_shifted = SVD project Y_shifted into SRM space (like CVD)
      3. Z_shifted = R_shifted^T @ Y_shifted^T — SRM representation
      4. RDM(Z_shifted)
    Average RDMs across training HCs, compare with Z_cvd RDM.

    Args:
        params: distortion model parameters
        model_name: distortion model name
        W_ridge_list: list of (K, V_s) ridge weights for training HCs
        shared_response: (k, 8) SRM shared response
        cvd_rdm_upper: (28,) upper triangle of CVD RDM in SRM space
        cvd_type: 'deutan', 'protan', or 'normal'

    Returns:
        loss: sum of squared differences between predicted and CVD RDM
    """
    C_shifted = get_design_matrix(model_name, params, cvd_type=cvd_type)
    rdm_sum = None

    for W_i in W_ridge_list:
        # 1. Voxel-space prediction
        Y_shifted = C_shifted @ W_i  # (8, V_s)

        # 2. Project into SRM space (treat as novel subject)
        R_shifted = project_new_subject_svd(shared_response, Y_shifted)

        # 3. SRM representation
        Z_shifted = R_shifted.T @ Y_shifted.T  # (k, 8)

        # 4. RDM in SRM space
        rdm_i = squareform(pdist(Z_shifted.T, 'correlation'))
        if rdm_sum is None:
            rdm_sum = rdm_i
        else:
            rdm_sum += rdm_i

    rdm_mean = rdm_sum / len(W_ridge_list)
    pred_upper = rdm_mean[np.triu_indices(8, k=1)]
    return float(np.sum((pred_upper - cvd_rdm_upper) ** 2))


# ============================================================================
# Path B: Voxel-space RDM loss (unchanged, supplementary)
# ============================================================================

def rdm_loss_voxel(params, model_name, W_ridge_list,
                   cvd_voxel_rdm_upper, cvd_type):
    """Voxel-space RDM loss (supplementary).

    For each training HC W_i: RDM from C(θ+δ) @ W_i in voxel space.
    Average RDMs, compare with CVD voxel-space RDM.
    """
    C_shifted = get_design_matrix(model_name, params, cvd_type=cvd_type)
    rdm_sum = None
    for W_i in W_ridge_list:
        Y_pred = C_shifted @ W_i  # (8, V_s)
        rdm_i = squareform(pdist(Y_pred, 'correlation'))
        if rdm_sum is None:
            rdm_sum = rdm_i
        else:
            rdm_sum += rdm_i
    rdm_mean = rdm_sum / len(W_ridge_list)
    pred_upper = rdm_mean[np.triu_indices(8, k=1)]
    return float(np.sum((pred_upper - cvd_voxel_rdm_upper) ** 2))


# ============================================================================
# Main fitting
# ============================================================================

def fit_one_fold(fold_idx, roi, cvd_subj, precomputed_dir, models=None):
    """Fit δθ for one fold x CVD subject.

    Returns:
        fold_result: dict with model results for both paths
    """
    if models is None:
        models = FIT_MODELS
    cvd_type = CVD_TYPE[cvd_subj]

    fold_dir = Path(precomputed_dir) / roi / f'fold_{fold_idx}'
    held_out = HC_SUBJECTS[fold_idx]
    train_subjects = [s for s in HC_SUBJECTS if s != held_out]

    # Load precomputed data
    shared_response = np.load(fold_dir / 'shared_response.npy')  # (k, 8)
    Z_cvd = np.load(fold_dir / f'Z_cvd_{cvd_subj}.npy')          # (k, 8)

    # CVD target RDM in SRM space (for Path A)
    cvd_rdm = squareform(pdist(Z_cvd.T, 'correlation'))
    cvd_rdm_upper = cvd_rdm[np.triu_indices(8, k=1)]

    # Load training HC ridge weights
    W_ridge_list = []
    for subj in train_subjects:
        W = np.load(fold_dir / f'W_ridge_{subj}.npy')
        W_ridge_list.append(W)

    # CVD voxel-space RDM (for Path B)
    amp_cvd = load_amplitudes(LOCAL_BASELINE, cvd_subj, roi)
    beta_cvd = amp_cvd.mean(axis=0)
    cvd_voxel_rdm = squareform(pdist(beta_cvd, 'correlation'))
    cvd_voxel_upper = cvd_voxel_rdm[np.triu_indices(8, k=1)]

    fold_result = {'fold_idx': fold_idx, 'held_out': held_out, 'models': {}}

    for model_name in models:
        bounds = MODELS[model_name]['bounds']
        df = MODELS[model_name]['df']

        # --- Path A: Voxel→SRM (corrected) ---
        res_a = differential_evolution(
            rdm_loss_voxel_to_srm, bounds,
            args=(model_name, W_ridge_list, shared_response,
                  cvd_rdm_upper, cvd_type),
            seed=42, maxiter=200, tol=1e-8,
            popsize=15, mutation=(0.5, 1.5), recombination=0.7,
        )

        # --- Path B: Voxel-only (supplementary) ---
        res_b = differential_evolution(
            rdm_loss_voxel, bounds,
            args=(model_name, W_ridge_list, cvd_voxel_upper, cvd_type),
            seed=42, maxiter=200, tol=1e-8,
            popsize=15, mutation=(0.5, 1.5), recombination=0.7,
        )

        # Evaluate Path A: Spearman r
        C_a = get_design_matrix(model_name, res_a.x, cvd_type=cvd_type)
        rdm_a_sum = np.zeros((8, 8))
        for W_i in W_ridge_list:
            Y_shifted = C_a @ W_i
            R_shifted = project_new_subject_svd(shared_response, Y_shifted)
            Z_shifted = R_shifted.T @ Y_shifted.T
            rdm_a_sum += squareform(pdist(Z_shifted.T, 'correlation'))
        a_upper = (rdm_a_sum / len(W_ridge_list))[np.triu_indices(8, k=1)]
        rho_a, p_a = spearmanr(a_upper, cvd_rdm_upper)

        # Evaluate Path B: Spearman r
        C_b = get_design_matrix(model_name, res_b.x, cvd_type=cvd_type)
        rdm_b_sum = np.zeros((8, 8))
        for W_i in W_ridge_list:
            rdm_b_sum += squareform(pdist(C_b @ W_i, 'correlation'))
        b_upper = (rdm_b_sum / len(W_ridge_list))[np.triu_indices(8, k=1)]
        rho_b, p_b = spearmanr(b_upper, cvd_voxel_upper)

        fold_result['models'][model_name] = {
            'path_A': {
                'description': 'voxel_to_srm',
                'params': res_a.x.tolist(),
                'loss': float(res_a.fun),
                'aicc': compute_aicc(res_a.fun, df),
                'spearman_r': float(rho_a) if np.isfinite(rho_a) else 0.0,
                'spearman_p': float(p_a) if np.isfinite(p_a) else 1.0,
                'success': bool(res_a.success),
            },
            'path_B': {
                'description': 'voxel_only',
                'params': res_b.x.tolist(),
                'loss': float(res_b.fun),
                'aicc': compute_aicc(res_b.fun, df),
                'spearman_r': float(rho_b) if np.isfinite(rho_b) else 0.0,
                'spearman_p': float(p_b) if np.isfinite(p_b) else 1.0,
                'success': bool(res_b.success),
            },
        }

    return fold_result


def aggregate_folds(fold_results, models=None):
    """Aggregate 7-fold results: median, SD of fitted parameters.

    Returns:
        agg: dict with per-model aggregated statistics
    """
    if models is None:
        models = FIT_MODELS

    agg = {}
    for model_name in models:
        for path in ['path_A', 'path_B']:
            key = f'{model_name}_{path}'
            params_list = []
            losses = []
            aiccs = []
            rhos = []

            for fold in fold_results:
                m = fold['models'].get(model_name, {}).get(path)
                if m is None:
                    continue
                params_list.append(m['params'])
                losses.append(m['loss'])
                aiccs.append(m['aicc'])
                rhos.append(m['spearman_r'])

            if not params_list:
                continue

            params_arr = np.array(params_list)
            agg[key] = {
                'params_median': np.median(params_arr, axis=0).tolist(),
                'params_mean': np.mean(params_arr, axis=0).tolist(),
                'params_sd': np.std(params_arr, axis=0, ddof=1).tolist(),
                'loss_median': float(np.median(losses)),
                'loss_sd': float(np.std(losses, ddof=1)),
                'aicc_median': float(np.median(aiccs)),
                'spearman_r_median': float(np.median(rhos)),
                'spearman_r_range': [float(np.min(rhos)), float(np.max(rhos))],
                'n_folds': len(params_list),
            }

    return agg


def main():
    parser = argparse.ArgumentParser(
        description='Step 1A: SRM-RDM fitting (v2, corrected Voxel→SRM)')
    parser.add_argument('--precomputed_dir', type=str,
                        default='results/precomputed')
    parser.add_argument('--output_dir', type=str,
                        default='results/v2/step1_rdm')
    parser.add_argument('--rois', nargs='+', default=['V4'])
    parser.add_argument('--cvd_subjects', nargs='+', default=CVD_SUBJECTS)
    parser.add_argument('--models', nargs='+', default=FIT_MODELS)
    args = parser.parse_args()

    print('=' * 60)
    print('Step 1A: SRM-RDM Fitting (v2, Voxel→SRM corrected)')
    print(f'ROIs: {args.rois}')
    print(f'CVD subjects: {args.cvd_subjects}')
    print(f'Models: {args.models}')
    print('=' * 60)
    print()
    print('Path A: C(θ+δ) @ W_ridge → voxel → SVD project → SRM RDM')
    print('        Target: Z_cvd RDM in SRM space')
    print('Path B: C(θ+δ) @ W_ridge → voxel RDM')
    print('        Target: CVD voxel RDM (supplementary)')
    print()

    for roi in args.rois:
        print(f'\n=== {roi} ===')

        for cvd_subj in args.cvd_subjects:
            cvd_type = CVD_TYPE[cvd_subj]
            print(f'\n  sub-{cvd_subj} ({cvd_type}):')

            fold_results = []
            for fold_idx in range(len(HC_SUBJECTS)):
                print(f'    Fold {fold_idx} '
                      f'(held-out: sub-{HC_SUBJECTS[fold_idx]})...')
                fold_res = fit_one_fold(
                    fold_idx, roi, cvd_subj,
                    args.precomputed_dir, args.models)
                fold_results.append(fold_res)

                # Brief report
                for m in args.models:
                    pa = fold_res['models'][m]['path_A']
                    pb = fold_res['models'][m]['path_B']
                    print(f'      {m}: '
                          f'A(vox→srm) r={pa["spearman_r"]:.3f} '
                          f'δ={pa["params"]} | '
                          f'B(vox) r={pb["spearman_r"]:.3f} '
                          f'δ={pb["params"]}')

            # Aggregate
            agg = aggregate_folds(fold_results, args.models)
            print(f'\n    --- Aggregated (7-fold) ---')
            for key, val in agg.items():
                print(f'      {key}: '
                      f'median_r={val["spearman_r_median"]:.3f} '
                      f'median_δ={val["params_median"]} '
                      f'sd_δ={val["params_sd"]}')

            # Save
            out_dir = Path(args.output_dir) / roi
            out_dir.mkdir(parents=True, exist_ok=True)
            result = {
                'subject': cvd_subj,
                'roi': roi,
                'cvd_type': cvd_type,
                'timestamp': datetime.now().isoformat(),
                'method': 'voxel_to_srm_corrected',
                'n_folds': len(HC_SUBJECTS),
                'path_A_description': ('C(θ+δ) @ W_ridge → voxel → '
                                       'SVD project → SRM RDM vs Z_cvd RDM'),
                'path_B_description': ('C(θ+δ) @ W_ridge → voxel RDM '
                                       'vs CVD voxel RDM'),
                'folds': fold_results,
                'aggregate': agg,
            }
            out_path = out_dir / f'sub-{cvd_subj}_rdm_v2.json'
            with open(out_path, 'w') as f:
                json.dump(result, f, indent=2)
            print(f'    Saved: {out_path}')

    print('\nStep 1A (RDM v2, corrected) complete.')


if __name__ == '__main__':
    main()
