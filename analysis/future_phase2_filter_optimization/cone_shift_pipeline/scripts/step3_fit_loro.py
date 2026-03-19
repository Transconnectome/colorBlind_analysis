#!/usr/bin/env python3
"""
step3_fit_loro.py — Criterion 2: SRM-space LORO fitting.

Uses A_g in SRM space (NOT W0 in voxel space).
W0 = (R_new @ A_g)^T contains CVD-specific R_new which absorbed partial cone shift.
Working in SRM k-space keeps the model side R_new-free.

For each CVD subject x ROI x model:
  1. Load A_g and compute R_new locally (no BrainIAK)
  2. Project CVD per-run data to SRM space: Z_CVD_r = R_new^T @ Y_CVD_r^T
  3. 6-fold LORO: predict Z_pred = A_g @ C(theta+delta)^T, compare to Z_CVD_r
  4. Optimize delta_theta to maximize mean fold correlation

Runs locally (conda env: srm).

Usage:
    python scripts/step3_fit_loro.py \
        --output_dir results/step3_loro
"""

import argparse
import json
import numpy as np
from pathlib import Path
from datetime import datetime
from scipy.optimize import minimize
import sys

_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR))

_FWD_DIR = str(Path(__file__).resolve().parent.parent.parent.parent
               / 'future_phase1_forward_model' / 'scripts')
sys.path.insert(0, _FWD_DIR)

from utils_forward_model import (
    HC_SUBJECTS, CVD_SUBJECTS, ROIS, K_VALUES, N_CHANNELS,
    HUE_ANGLES, N_RUNS, load_amplitudes,
)
from utils_distortion_models import (
    MODELS, get_design_matrix, get_initial_params, compute_aicc,
)

LOCAL_BASELINE = Path(__file__).resolve().parent.parent.parent.parent \
    / 'phase1_preprocess_decoding' / 'results' / 'full_dataset_C010'
FWD_RESULTS = Path(__file__).resolve().parent.parent.parent.parent \
    / 'future_phase1_forward_model' / 'results'

CVD_TYPE = {'08': 'deutan', '09': 'protan', '10': 'normal'}


def compute_R_new(beta_cvd, shared_response):
    """Compute CVD SRM projection without BrainIAK."""
    S = shared_response
    W_init = beta_cvd.T @ np.linalg.pinv(S)
    U, _, Vt = np.linalg.svd(W_init, full_matrices=False)
    return U @ Vt


def loro_objective(params, model_name, A_g, Z_cvd_runs, cvd_type):
    """Negative mean LORO correlation in SRM space.

    Z_pred = A_g @ C(theta+delta)^T  (model, NO R_new)
    Z_test = Z_cvd_runs[run]          (target via R_new, fixed)
    """
    C_shifted = get_design_matrix(model_name, params, cvd_type=cvd_type)
    Z_pred = A_g @ C_shifted.T  # (k, 8) — model prediction

    fold_corrs = []
    for run in range(N_RUNS):
        Z_test = Z_cvd_runs[run]  # (k, 8)
        # Pattern correlation across k dimensions for each color
        corrs = []
        for c in range(8):
            pred_vec = Z_pred[:, c]
            test_vec = Z_test[:, c]
            if np.std(pred_vec) == 0 or np.std(test_vec) == 0:
                corrs.append(0.0)
            else:
                r = np.corrcoef(pred_vec, test_vec)[0, 1]
                corrs.append(r if np.isfinite(r) else 0.0)
        fold_corrs.append(np.mean(corrs))

    return -np.mean(fold_corrs)


def fit_loro(roi, cvd_subj, output_dir):
    """Run LORO fitting for one CVD subject x ROI."""
    cvd_type = CVD_TYPE[cvd_subj]

    # Load SRM data
    A_g = np.load(FWD_RESULTS / 'group_prior' / roi / 'A_g.npy')
    S = np.load(FWD_RESULTS / 'srm_projections' / roi / 'shared_response.npy')

    # CVD data
    amp_cvd = load_amplitudes(LOCAL_BASELINE, cvd_subj, roi)
    beta_cvd = amp_cvd.mean(axis=0)  # (8, V_s)
    R_new = compute_R_new(beta_cvd, S)

    # Project CVD per-run to SRM space
    Z_cvd_runs = []
    for run in range(N_RUNS):
        Y_run = amp_cvd[run]  # (8, V_s)
        Z_run = R_new.T @ Y_run.T  # (k, 8)
        Z_cvd_runs.append(Z_run)

    # Baseline: delta=0 (unshifted)
    C_orig = get_design_matrix('per_color', [0]*8)
    Z_pred_orig = A_g @ C_orig.T
    baseline_corrs = []
    for run in range(N_RUNS):
        run_corrs = []
        for c in range(8):
            pv = Z_pred_orig[:, c]
            tv = Z_cvd_runs[run][:, c]
            if np.std(pv) > 0 and np.std(tv) > 0:
                r = np.corrcoef(pv, tv)[0, 1]
                run_corrs.append(r if np.isfinite(r) else 0.0)
            else:
                run_corrs.append(0.0)
        baseline_corrs.append(np.mean(run_corrs))
    baseline_score = float(np.mean(baseline_corrs))

    model_results = {}
    for model_name in MODELS:
        bounds = MODELS[model_name]['bounds']
        x0 = get_initial_params(model_name, cvd_type)

        res = minimize(
            loro_objective, x0,
            args=(model_name, A_g, Z_cvd_runs, cvd_type),
            method='L-BFGS-B', bounds=bounds,
            options={'maxiter': 500, 'ftol': 1e-10}
        )

        opt_score = -res.fun
        improvement = opt_score - baseline_score

        model_results[model_name] = {
            'params': res.x.tolist(),
            'loro_corr': float(opt_score),
            'baseline_corr': baseline_score,
            'improvement': float(improvement),
            'aicc': compute_aicc(max(1e-10, 1 - opt_score), MODELS[model_name]['df'],
                                 n_obs=N_RUNS * 8),
            'success': bool(res.success),
        }

        print(f'      {model_name}: LORO r={opt_score:.4f} '
              f'(baseline={baseline_score:.4f}, improve={improvement:+.4f})')

    # Save
    out_dir = Path(output_dir) / roi
    out_dir.mkdir(parents=True, exist_ok=True)
    result = {
        'subject': cvd_subj,
        'roi': roi,
        'cvd_type': cvd_type,
        'timestamp': datetime.now().isoformat(),
        'k': int(K_VALUES[roi]),
        'baseline_loro_corr': baseline_score,
        'models': model_results,
    }
    out_path = out_dir / f'sub-{cvd_subj}_loro_fits.json'
    with open(out_path, 'w') as f:
        json.dump(result, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description='Step 3: LORO fitting')
    parser.add_argument('--output_dir', type=str, default='results/step3_loro')
    parser.add_argument('--rois', nargs='+', default=ROIS)
    parser.add_argument('--cvd_subjects', nargs='+', default=CVD_SUBJECTS)
    args = parser.parse_args()

    print('=' * 60)
    print('Step 3: SRM-Space LORO Fitting (Criterion 2)')
    print(f'ROIs: {args.rois}')
    print(f'CVD subjects: {args.cvd_subjects}')
    print('=' * 60)

    for roi in args.rois:
        print(f'\n--- {roi} (k={K_VALUES[roi]}) ---')
        for cvd_subj in args.cvd_subjects:
            print(f'  sub-{cvd_subj} ({CVD_TYPE[cvd_subj]}):')
            fit_loro(roi, cvd_subj, args.output_dir)

    print('\nStep 3 (LORO) complete.')


if __name__ == '__main__':
    main()
