#!/usr/bin/env python3
"""
step2_fit_rdm.py — Criterion 1: RDM fitting (voxel-space 1a + SRM-space 1b).

For each CVD subject x ROI x distortion model:
  1a. Voxel-space RDM: HC per-subject W, predict RDM via C(theta+delta) @ W_i
  1b. SRM-space RDM: A_g @ C(theta+delta)^T -> Z_model RDM vs Z_CVD RDM

Optimizes delta_theta to match CVD RDM.

Runs locally (conda env: srm).

Usage:
    python scripts/step2_fit_rdm.py \
        --output_dir results/step2_rdm
"""

import argparse
import json
import numpy as np
from pathlib import Path
from datetime import datetime
from scipy.optimize import minimize
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
    gcv_select_alpha, fit_W_ridge, compute_rdm, rdm_upper_tri,
)
from utils_distortion_models import (
    MODELS, apply_distortion, get_design_matrix,
    get_initial_params, compute_aicc,
)

# ============================================================================
# Paths
# ============================================================================

LOCAL_BASELINE = Path(__file__).resolve().parent.parent.parent.parent \
    / 'phase1_preprocess_decoding' / 'results' / 'full_dataset_C010'
FWD_RESULTS = Path(__file__).resolve().parent.parent.parent.parent \
    / 'future_phase1_forward_model' / 'results'

CVD_TYPE = {'08': 'deutan', '09': 'protan', '10': 'normal'}


# ============================================================================
# Criterion 1a: Voxel-Space RDM
# ============================================================================

def fit_hc_weights(roi):
    """Fit ridge_gcv weights for all HC subjects.

    Returns:
        hc_weights: list of (K, V_s) weight matrices
        hc_alphas: dict {subj: alpha}
    """
    C = create_basis_matrix(HUE_ANGLES, N_CHANNELS)
    hc_weights = []
    hc_alphas = {}

    for subj in HC_SUBJECTS:
        amp = load_amplitudes(LOCAL_BASELINE, subj, roi)
        # Pool 6 runs x 8 colors = 48 samples
        V_s = amp.shape[2]
        X = amp.reshape(-1, V_s)  # (48, V_s)
        C_pooled = np.tile(C, (6, 1))  # (48, K)
        alpha, _ = gcv_select_alpha(C_pooled, X)
        W = fit_W_ridge(C_pooled, X, alpha)
        hc_weights.append(W)
        hc_alphas[subj] = alpha

    return hc_weights, hc_alphas


def rdm_loss_1a(params, model_name, hc_weights, cvd_rdm_upper, cvd_type):
    """Voxel-space RDM loss (Criterion 1a).

    For each HC W_i: compute RDM from C(theta+delta) @ W_i.
    Average RDMs, compare to CVD actual RDM.
    """
    C_shifted = get_design_matrix(model_name, params, cvd_type=cvd_type)

    rdm_sum = None
    for W_i in hc_weights:
        Y_pred = C_shifted @ W_i  # (8, V_s)
        rdm_i = squareform(pdist(Y_pred, 'correlation'))
        if rdm_sum is None:
            rdm_sum = rdm_i
        else:
            rdm_sum += rdm_i
    rdm_mean = rdm_sum / len(hc_weights)
    pred_upper = rdm_mean[np.triu_indices(8, k=1)]
    return float(np.sum((pred_upper - cvd_rdm_upper) ** 2))


def fit_criterion_1a(roi, cvd_subj, hc_weights, model_results):
    """Run criterion 1a for one CVD subject x ROI."""
    cvd_type = CVD_TYPE[cvd_subj]
    amp_cvd = load_amplitudes(LOCAL_BASELINE, cvd_subj, roi)
    beta_cvd = amp_cvd.mean(axis=0)  # (8, V_s)
    cvd_rdm = squareform(pdist(beta_cvd, 'correlation'))
    cvd_rdm_upper = cvd_rdm[np.triu_indices(8, k=1)]

    for model_name in MODELS:
        bounds = MODELS[model_name]['bounds']
        x0 = get_initial_params(model_name, cvd_type)

        res = minimize(
            rdm_loss_1a, x0,
            args=(model_name, hc_weights, cvd_rdm_upper, cvd_type),
            method='L-BFGS-B', bounds=bounds,
            options={'maxiter': 500, 'ftol': 1e-10}
        )

        model_results[model_name]['1a'] = {
            'params': res.x.tolist(),
            'loss': float(res.fun),
            'aicc': compute_aicc(res.fun, MODELS[model_name]['df']),
            'success': bool(res.success),
        }


# ============================================================================
# Criterion 1b: SRM-Space RDM
# ============================================================================

def compute_R_new(beta_cvd, shared_response):
    """Compute CVD SRM projection without BrainIAK.

    Args:
        beta_cvd: (8, V_s) run-averaged CVD amplitudes
        shared_response: (k, 8) SRM shared response

    Returns:
        R_new: (V_s, k) orthonormal projection
    """
    S = shared_response  # (k, 8)
    W_init = beta_cvd.T @ np.linalg.pinv(S)  # (V_s, k)
    U, _, Vt = np.linalg.svd(W_init, full_matrices=False)
    return U @ Vt  # (V_s, k)


def rdm_loss_1b(params, model_name, A_g, cvd_rdm_upper, cvd_type):
    """SRM-space RDM loss (Criterion 1b).

    Z_model = A_g @ C(theta+delta)^T -> RDM in k-space.
    """
    C_shifted = get_design_matrix(model_name, params, cvd_type=cvd_type)
    Z_model = A_g @ C_shifted.T  # (k, 8)
    rdm_model = squareform(pdist(Z_model.T, 'correlation'))
    pred_upper = rdm_model[np.triu_indices(8, k=1)]
    return float(np.sum((pred_upper - cvd_rdm_upper) ** 2))


def fit_criterion_1b(roi, cvd_subj, model_results):
    """Run criterion 1b for one CVD subject x ROI."""
    cvd_type = CVD_TYPE[cvd_subj]

    # Load SRM data
    A_g = np.load(FWD_RESULTS / 'group_prior' / roi / 'A_g.npy')
    S = np.load(FWD_RESULTS / 'srm_projections' / roi / 'shared_response.npy')

    # CVD target RDM in SRM space
    amp_cvd = load_amplitudes(LOCAL_BASELINE, cvd_subj, roi)
    beta_cvd = amp_cvd.mean(axis=0)  # (8, V_s)
    R_new = compute_R_new(beta_cvd, S)
    Z_cvd = R_new.T @ beta_cvd.T  # (k, 8)
    cvd_rdm = squareform(pdist(Z_cvd.T, 'correlation'))
    cvd_rdm_upper = cvd_rdm[np.triu_indices(8, k=1)]

    for model_name in MODELS:
        bounds = MODELS[model_name]['bounds']
        x0 = get_initial_params(model_name, cvd_type)

        # Independent 1b fit
        res = minimize(
            rdm_loss_1b, x0,
            args=(model_name, A_g, cvd_rdm_upper, cvd_type),
            method='L-BFGS-B', bounds=bounds,
            options={'maxiter': 500, 'ftol': 1e-10}
        )

        model_results[model_name]['1b'] = {
            'params': res.x.tolist(),
            'loss': float(res.fun),
            'aicc': compute_aicc(res.fun, MODELS[model_name]['df']),
            'success': bool(res.success),
        }

        # 1a -> 1b transfer (if 1a was fit)
        if '1a' in model_results[model_name]:
            params_1a = model_results[model_name]['1a']['params']
            transfer_loss = rdm_loss_1b(
                params_1a, model_name, A_g, cvd_rdm_upper, cvd_type)
            # Spearman correlation for transfer quality
            C_shifted_1a = get_design_matrix(model_name, params_1a, cvd_type=cvd_type)
            Z_transfer = A_g @ C_shifted_1a.T
            rdm_transfer = squareform(pdist(Z_transfer.T, 'correlation'))
            transfer_upper = rdm_transfer[np.triu_indices(8, k=1)]
            rho, p = spearmanr(transfer_upper, cvd_rdm_upper)

            model_results[model_name]['1a_to_1b_transfer'] = {
                'loss': float(transfer_loss),
                'spearman_r': float(rho) if np.isfinite(rho) else 0.0,
                'spearman_p': float(p) if np.isfinite(p) else 1.0,
            }


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Step 2: RDM fitting')
    parser.add_argument('--output_dir', type=str, default='results/step2_rdm')
    parser.add_argument('--rois', nargs='+', default=ROIS)
    parser.add_argument('--cvd_subjects', nargs='+', default=CVD_SUBJECTS)
    args = parser.parse_args()

    print('=' * 60)
    print('Step 2: RDM Fitting (Criterion 1a + 1b)')
    print(f'ROIs: {args.rois}')
    print(f'CVD subjects: {args.cvd_subjects}')
    print('=' * 60)

    for roi in args.rois:
        print(f'\n--- {roi} ---')

        # Fit HC weights once per ROI (shared across CVD subjects)
        print(f'  Fitting HC weights...')
        hc_weights, hc_alphas = fit_hc_weights(roi)
        print(f'  HC alphas: {hc_alphas}')

        for cvd_subj in args.cvd_subjects:
            print(f'\n  sub-{cvd_subj} ({CVD_TYPE[cvd_subj]}):')

            model_results = {m: {} for m in MODELS}

            # Criterion 1a
            print(f'    Fitting criterion 1a (voxel-space RDM)...')
            fit_criterion_1a(roi, cvd_subj, hc_weights, model_results)
            for m, r in model_results.items():
                if '1a' in r:
                    print(f'      {m}: loss={r["1a"]["loss"]:.6f}, '
                          f'AICc={r["1a"]["aicc"]:.2f}')

            # Criterion 1b
            print(f'    Fitting criterion 1b (SRM-space RDM)...')
            fit_criterion_1b(roi, cvd_subj, model_results)
            for m, r in model_results.items():
                if '1b' in r:
                    print(f'      {m}: loss={r["1b"]["loss"]:.6f}, '
                          f'AICc={r["1b"]["aicc"]:.2f}')
                if '1a_to_1b_transfer' in r:
                    t = r['1a_to_1b_transfer']
                    print(f'        1a->1b transfer: r={t["spearman_r"]:.3f}')

            # Save
            out_dir = Path(args.output_dir) / roi
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / f'sub-{cvd_subj}_rdm_fits.json'
            result = {
                'subject': cvd_subj,
                'roi': roi,
                'cvd_type': CVD_TYPE[cvd_subj],
                'timestamp': datetime.now().isoformat(),
                'hc_alphas': {k: float(v) for k, v in hc_alphas.items()},
                'models': model_results,
            }
            with open(out_path, 'w') as f:
                json.dump(result, f, indent=2)

    print('\nStep 2 complete.')


if __name__ == '__main__':
    main()
