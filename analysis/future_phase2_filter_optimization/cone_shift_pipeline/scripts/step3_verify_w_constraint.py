#!/usr/bin/env python3
"""
step3_verify_w_constraint.py — W constraint verification.

Compares HC-derived W0 (constrained) vs CVD-fitted W_free (free) to test W_HC ≈ W_CVD.

CRITICAL: W_free is fit with ORIGINAL C(theta), NOT C(theta+delta*).
Fitting with C(theta+delta*) would absorb the cone shift into W.

Verifications:
  1. delta_W norm: ||W_free - W0||_F / ||W0||_F
  2. Crawford & Howell: per-HC W_i vs W_free
  3. Re-optimize delta_theta with W_free -> r(delta*_constrained, delta*_free) > 0.9
  4. Prediction comparison: C(theta+delta*) @ W0 vs C(theta+delta*) @ W_free

Runs locally (conda env: srm).

Usage:
    python scripts/step3_verify_w_constraint.py \
        --output_dir results/step3_w_constraint
"""

import argparse
import json
import numpy as np
from pathlib import Path
from datetime import datetime
from scipy.optimize import minimize
from scipy.spatial.distance import pdist, squareform
from scipy.stats import spearmanr, t as t_dist
import sys

_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR))

_FWD_DIR = str(Path(__file__).resolve().parent.parent.parent.parent
               / 'future_phase1_forward_model' / 'scripts')
sys.path.insert(0, _FWD_DIR)

from utils_forward_model import (
    HC_SUBJECTS, CVD_SUBJECTS, ROIS, N_CHANNELS, N_RUNS,
    HUE_ANGLES, load_amplitudes, create_basis_matrix,
    gcv_select_alpha, fit_W_ridge,
)
from utils_distortion_models import (
    MODELS, get_design_matrix, get_initial_params, compute_aicc,
)

LOCAL_BASELINE = Path(__file__).resolve().parent.parent.parent.parent \
    / 'phase1_preprocess_decoding' / 'results' / 'full_dataset_C010'
FILTER_RESULTS = Path(__file__).resolve().parent.parent.parent \
    / 'results' / 'step1_model'
STEP2_RESULTS = Path(__file__).resolve().parent.parent / 'results' / 'step2_rdm'

CVD_TYPE = {'08': 'deutan', '09': 'protan', '10': 'normal'}

# step1_model uses 'hV4' not 'V4'
STEP1_ROI_MAP = {'V4': 'hV4'}


def crawford_howell_test(x, sample_mean, sample_std, n):
    """Crawford & Howell (1998) modified t-test for single case.

    Tests if single observation x differs from a sample of size n.

    Returns:
        t_stat, p_value (two-tailed)
    """
    if sample_std == 0:
        return np.nan, np.nan
    t_stat = (x - sample_mean) / (sample_std * np.sqrt((n + 1) / n))
    p_value = 2 * t_dist.sf(abs(t_stat), df=n - 1)
    return float(t_stat), float(p_value)


def fit_w_per_subject(roi, subjects):
    """Fit ridge_gcv weights for given subjects using ORIGINAL C(theta).

    Returns:
        weights: dict {subj: (K, V_s)}
        alphas: dict {subj: float}
    """
    C = create_basis_matrix(HUE_ANGLES, N_CHANNELS)
    weights = {}
    alphas = {}

    for subj in subjects:
        amp = load_amplitudes(LOCAL_BASELINE, subj, roi)
        V_s = amp.shape[2]
        X = amp.reshape(-1, V_s)
        C_pooled = np.tile(C, (N_RUNS, 1))
        alpha, _ = gcv_select_alpha(C_pooled, X)
        W = fit_W_ridge(C_pooled, X, alpha)
        weights[subj] = W
        alphas[subj] = alpha

    return weights, alphas


def verify_w_constraint(roi, cvd_subj, output_dir):
    """Run W constraint verification for one CVD subject x ROI."""
    cvd_type = CVD_TYPE[cvd_subj]

    # Load or compute W0 (group prior)
    step1_roi = STEP1_ROI_MAP.get(roi, roi)
    w0_path = FILTER_RESULTS / step1_roi / f'sub-{cvd_subj}' / 'W0.npy'
    if w0_path.exists():
        W0 = np.load(w0_path)
    else:
        print(f'    W0 not found at {w0_path}, skipping.')
        return

    # Fit HC per-subject weights with ORIGINAL C(theta)
    hc_weights, hc_alphas = fit_w_per_subject(roi, HC_SUBJECTS)

    # Fit W_free for CVD with ORIGINAL C(theta) (NOT shifted)
    cvd_weights, cvd_alphas = fit_w_per_subject(roi, [cvd_subj])
    W_free = cvd_weights[cvd_subj]

    # ---- Verification 1: delta_W norm ----
    delta_w_norm = float(np.linalg.norm(W_free - W0) / np.linalg.norm(W0))

    # ---- Verification 2: Crawford & Howell ----
    # HC subjects may have different V_s, so compute norms individually
    # W0 comes from group prior (same V_s as CVD subject)
    # For C&H, compute each HC's within-subject W deviation from its own norm
    hc_W_list = [hc_weights[s] for s in HC_SUBJECTS]
    # Norm comparison: each HC W_i vs W0 (W0 has CVD V_s, so use channel-space norm)
    # Project to channel space for comparison: use RDM-based norm instead
    C = create_basis_matrix(HUE_ANGLES, N_CHANNELS)
    rdm_w0 = squareform(pdist(C @ W0, 'correlation'))
    rdm_free = squareform(pdist(C @ W_free, 'correlation'))
    rdm_norm_free = float(np.linalg.norm(
        rdm_free[np.triu_indices(8, k=1)] - rdm_w0[np.triu_indices(8, k=1)]))

    hc_rdm_norms = []
    for W_hc in hc_W_list:
        rdm_hc = squareform(pdist(C @ W_hc, 'correlation'))
        hc_rdm_norms.append(float(np.linalg.norm(
            rdm_hc[np.triu_indices(8, k=1)] - rdm_w0[np.triu_indices(8, k=1)])))
    hc_norms = np.array(hc_rdm_norms)

    ch_t, ch_p = crawford_howell_test(
        rdm_norm_free, hc_norms.mean(), hc_norms.std(ddof=1), len(HC_SUBJECTS))

    # Element-wise outlier fraction not possible with different V_s
    # Use channel-space comparison instead
    frac_outlier = np.nan

    # ---- Verification 3: Re-optimize delta with W_free ----
    # Load best delta from step2 RDM (1a) if available
    step2_path = STEP2_RESULTS / roi / f'sub-{cvd_subj}_rdm_fits.json'
    reopt_results = {}
    if step2_path.exists():
        with open(step2_path) as f:
            step2_data = json.load(f)

        for model_name in MODELS:
            if model_name not in step2_data.get('models', {}):
                continue
            m_data = step2_data['models'][model_name]
            if '1a' not in m_data:
                continue

            params_constrained = np.array(m_data['1a']['params'])

            # Re-optimize with W_free instead of HC weights
            amp_cvd = load_amplitudes(LOCAL_BASELINE, cvd_subj, roi)
            beta_cvd = amp_cvd.mean(axis=0)
            cvd_rdm = squareform(pdist(beta_cvd, 'correlation'))
            cvd_rdm_upper = cvd_rdm[np.triu_indices(8, k=1)]

            def loss_w_free(params):
                C_s = get_design_matrix(model_name, params, cvd_type=cvd_type)
                Y_pred = C_s @ W_free
                rdm_pred = squareform(pdist(Y_pred, 'correlation'))
                pred_upper = rdm_pred[np.triu_indices(8, k=1)]
                return float(np.sum((pred_upper - cvd_rdm_upper) ** 2))

            bounds = MODELS[model_name]['bounds']
            x0 = get_initial_params(model_name, cvd_type)
            res = minimize(loss_w_free, x0, method='L-BFGS-B', bounds=bounds,
                           options={'maxiter': 500, 'ftol': 1e-10})

            params_free = res.x
            # Correlation between constrained and free delta estimates
            if len(params_constrained) > 1:
                rho, _ = spearmanr(params_constrained, params_free)
            else:
                rho = 1.0 if np.sign(params_constrained[0]) == np.sign(params_free[0]) else -1.0

            reopt_results[model_name] = {
                'params_constrained': params_constrained.tolist(),
                'params_free': params_free.tolist(),
                'param_correlation': float(rho) if np.isfinite(rho) else 0.0,
            }

    # ---- Verification 4: Prediction comparison ----
    pred_comp = {}
    if step2_path.exists():
        for model_name in MODELS:
            if model_name not in step2_data.get('models', {}):
                continue
            m_data = step2_data['models'][model_name]
            if '1a' not in m_data:
                continue

            params = np.array(m_data['1a']['params'])
            C_shifted = get_design_matrix(model_name, params, cvd_type=cvd_type)

            Y_w0 = C_shifted @ W0
            Y_wfree = C_shifted @ W_free

            # Pattern correlation between W0 and W_free predictions
            from utils_forward_model import voxel_pattern_correlation
            pred_corrs = voxel_pattern_correlation(Y_w0, Y_wfree)
            pred_comp[model_name] = {
                'mean_pattern_corr': float(np.mean(pred_corrs)),
                'per_color_corr': pred_corrs.tolist(),
            }

    # Save
    out_dir = Path(output_dir) / roi
    out_dir.mkdir(parents=True, exist_ok=True)
    result = {
        'subject': cvd_subj,
        'roi': roi,
        'cvd_type': cvd_type,
        'timestamp': datetime.now().isoformat(),
        'delta_w_norm': delta_w_norm,
        'crawford_howell': {
            't_stat': ch_t,
            'p_value': ch_p,
            'hc_norms_mean': float(hc_norms.mean()),
            'hc_norms_std': float(hc_norms.std(ddof=1)),
        },
        'element_outlier_fraction': frac_outlier,
        'reoptimization': reopt_results,
        'prediction_comparison': pred_comp,
        'cvd_alpha': float(cvd_alphas[cvd_subj]),
        'hc_alphas': {k: float(v) for k, v in hc_alphas.items()},
    }

    out_path = out_dir / f'sub-{cvd_subj}_w_constraint.json'
    with open(out_path, 'w') as f:
        json.dump(result, f, indent=2)

    print(f'    delta_W norm: {delta_w_norm:.4f}')
    print(f'    Crawford-Howell: t={ch_t:.3f}, p={ch_p:.3f}')
    print(f'    Element outlier fraction (|z|>2): {frac_outlier:.3f}')


def main():
    parser = argparse.ArgumentParser(description='Step 3b: W constraint verification')
    parser.add_argument('--output_dir', type=str,
                        default='results/step3_w_constraint')
    parser.add_argument('--rois', nargs='+', default=ROIS)
    parser.add_argument('--cvd_subjects', nargs='+', default=CVD_SUBJECTS)
    args = parser.parse_args()

    print('=' * 60)
    print('Step 3b: W Constraint Verification')
    print(f'ROIs: {args.rois}')
    print(f'CVD subjects: {args.cvd_subjects}')
    print('=' * 60)

    for roi in args.rois:
        print(f'\n--- {roi} ---')
        for cvd_subj in args.cvd_subjects:
            print(f'  sub-{cvd_subj} ({CVD_TYPE[cvd_subj]}):')
            verify_w_constraint(roi, cvd_subj, args.output_dir)

    print('\nStep 3b complete.')


if __name__ == '__main__':
    main()
