#!/usr/bin/env python3
"""
step3_fit_loro.py — Criterion 2: Voxel-space LORO fitting.

Loads W0 directly from Phase 1 subject_weights (pre-computed by step_c):
  W0 = (R_new @ A_g)^T   shape (K, V_s)

Evaluates voxel-space pattern correlation (identical to Phase 1 prior_only):
  Y_hat = C(theta+delta) @ W0   shape (8, V_s)
  corr(Y_hat[c], X_test[c])     across V_s dimensions per color

For each CVD subject x ROI x model:
  1. Load pre-computed W0 from Phase 1 subject_weights
  2. 6-fold LORO: predict Y_hat = C(theta+delta) @ W0, compare to CVD run data
  3. Optimize delta_theta to maximize mean fold voxel correlation

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
    HUE_ANGLES, N_RUNS, load_amplitudes, voxel_pattern_correlation,
)
from utils_distortion_models import (
    MODELS, get_design_matrix, get_initial_params, compute_aicc,
)

LOCAL_BASELINE = Path(__file__).resolve().parent.parent.parent.parent \
    / 'phase1_preprocess_decoding' / 'results' / 'full_dataset_C010'
FWD_RESULTS = Path(__file__).resolve().parent.parent.parent.parent \
    / 'future_phase1_forward_model' / 'results'

CVD_TYPE = {'08': 'deutan', '09': 'protan', '10': 'normal'}


def loro_objective(params, model_name, W0, cvd_runs, cvd_type):
    """Negative mean LORO voxel correlation.

    Y_hat = C(theta+delta) @ W0    (8, V_s) — voxel-space prediction
    X_test = cvd_runs[run]         (8, V_s) — actual CVD run data
    corr across V_s dimensions per color (identical to Phase 1 evaluate_fold_loro).
    """
    C_shifted = get_design_matrix(model_name, params, cvd_type=cvd_type)
    Y_hat = C_shifted @ W0  # (8, V_s)

    fold_corrs = []
    for run in range(N_RUNS):
        X_test = cvd_runs[run]  # (8, V_s)
        r = voxel_pattern_correlation(Y_hat, X_test)  # (8,)
        fold_corrs.append(float(np.mean(r)))

    return -np.mean(fold_corrs)


def fit_loro(roi, cvd_subj, output_dir):
    """Run LORO fitting for one CVD subject x ROI."""
    cvd_type = CVD_TYPE[cvd_subj]

    # Load W0 from Phase 1 (pre-computed by step_c_project_prior.py)
    W0_path = FWD_RESULTS / 'subject_weights' / roi / f'sub-{cvd_subj}_W0.npy'
    W0 = np.load(W0_path)  # (K, V_s)
    V_s = W0.shape[1]

    # CVD per-run data in voxel space
    amp_cvd = load_amplitudes(LOCAL_BASELINE, cvd_subj, roi)
    cvd_runs = [amp_cvd[run] for run in range(N_RUNS)]  # each (8, V_s)

    # Baseline: delta=0 (unshifted) — should match Phase 1 prior_only LORO
    C_orig = get_design_matrix('per_color', [0]*8)
    Y_hat_orig = C_orig @ W0  # (8, V_s)
    baseline_corrs = []
    for run in range(N_RUNS):
        r = voxel_pattern_correlation(Y_hat_orig, cvd_runs[run])
        baseline_corrs.append(float(np.mean(r)))
    baseline_score = float(np.mean(baseline_corrs))

    model_results = {}
    for model_name in MODELS:
        bounds = MODELS[model_name]['bounds']
        x0 = get_initial_params(model_name, cvd_type)

        res = minimize(
            loro_objective, x0,
            args=(model_name, W0, cvd_runs, cvd_type),
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
        'n_voxels': V_s,
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
    print('Step 3: Voxel-Space LORO Fitting (Criterion 2)')
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
