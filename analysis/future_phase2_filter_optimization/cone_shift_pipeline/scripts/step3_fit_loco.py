#!/usr/bin/env python3
"""
step3_fit_loco.py — Criterion 3: LOCO simulation.

Cannot use W0 for LOCO — W0 was trained on all 8 colors.
Instead: apply delta_theta to HC subjects' LOCO procedure -> see if resulting
per-color vulnerability matches CVD's actual LOCO pattern.

Two simulation modes:
  PRIMARY (shift_at_test): W trained with C(theta), predict with C(theta+delta)
  SECONDARY (shift_at_both): W trained with C(theta+delta), predict with C(theta+delta)

Runs locally (conda env: srm).

Usage:
    python scripts/step3_fit_loco.py \
        --output_dir results/step3_loco
"""

import argparse
import json
import numpy as np
from pathlib import Path
from datetime import datetime
from scipy.optimize import minimize
from scipy.stats import spearmanr
import sys

_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR))

_FWD_DIR = str(Path(__file__).resolve().parent.parent.parent.parent
               / 'future_phase1_forward_model' / 'scripts')
sys.path.insert(0, _FWD_DIR)

from utils_forward_model import (
    HC_SUBJECTS, CVD_SUBJECTS, ROIS, N_CHANNELS, N_RUNS, N_COLORS,
    HUE_ANGLES, load_amplitudes, create_basis_matrix,
    gcv_select_alpha, fit_W_ridge, voxel_pattern_correlation,
)
from utils_distortion_models import (
    MODELS, get_design_matrix, get_initial_params, compute_aicc,
    HUE_ANGLES_FLOAT,
)

LOCAL_BASELINE = Path(__file__).resolve().parent.parent.parent.parent \
    / 'phase1_preprocess_decoding' / 'results' / 'full_dataset_C010'
FWD_RESULTS = Path(__file__).resolve().parent.parent.parent.parent \
    / 'future_phase1_forward_model' / 'results'

CVD_TYPE = {'08': 'deutan', '09': 'protan', '10': 'normal'}


def load_cvd_loco_target(cvd_subj, roi, model='ridge_gcv'):
    """Load CVD actual LOCO per-color voxel_corr from Phase 1 results.

    Returns:
        per_color_corr: (8,) voxel_corr per held-out color
    """
    loco_path = FWD_RESULTS / 'validation' / f'sub-{cvd_subj}_loco.json'
    with open(loco_path) as f:
        data = json.load(f)
    folds = data[roi][model]['folds']
    per_color = np.zeros(8)
    for fold in folds:
        idx = fold['test_color']
        per_color[idx] = fold['voxel_corr']
    return per_color


def simulate_hc_loco(hc_amps, C_original, C_shifted, mode='shift_at_test'):
    """Run LOCO simulation across HC subjects.

    Args:
        hc_amps: list of (6, 8, V_s) arrays for HC subjects
        C_original: (8, K) original design matrix
        C_shifted: (8, K) shifted design matrix
        mode: 'shift_at_test' or 'shift_at_both'

    Returns:
        hc_mean_vuln: (8,) mean vulnerability across HC subjects
        hc_all_vuln: list of (8,) per-HC vulnerability
    """
    C_train_base = C_original if mode == 'shift_at_test' else C_shifted

    hc_all_vuln = []
    for amp_hc in hc_amps:
        V_s = amp_hc.shape[2]
        fold_corrs = np.zeros(N_COLORS)

        for color in range(N_COLORS):
            train_colors = [c for c in range(N_COLORS) if c != color]

            # Pool 6 runs x 7 colors = 42 training samples
            X_train = amp_hc[:, train_colors].reshape(-1, V_s)
            C_train = np.tile(C_train_base[train_colors], (N_RUNS, 1))

            alpha, _ = gcv_select_alpha(C_train, X_train)
            W = fit_W_ridge(C_train, X_train, alpha)

            # Predict with SHIFTED design
            Y_pred = C_shifted[color:color+1] @ W  # (1, V_s)

            # Test: run-averaged actual response
            Y_test = amp_hc[:, color].mean(axis=0, keepdims=True)  # (1, V_s)
            r = voxel_pattern_correlation(Y_pred, Y_test)
            fold_corrs[color] = r[0]

        hc_all_vuln.append(fold_corrs)

    hc_mean_vuln = np.mean(hc_all_vuln, axis=0)
    return hc_mean_vuln, hc_all_vuln


def loco_objective(params, model_name, hc_amps, cvd_loco_target, cvd_type,
                   mode='shift_at_test'):
    """Maximize Spearman r between HC_shifted LOCO and CVD actual LOCO."""
    C_original = create_basis_matrix(HUE_ANGLES, N_CHANNELS)
    C_shifted = get_design_matrix(model_name, params, cvd_type=cvd_type)

    hc_mean_vuln, _ = simulate_hc_loco(hc_amps, C_original, C_shifted, mode)

    # Handle constant arrays
    if np.std(hc_mean_vuln) == 0 or np.std(cvd_loco_target) == 0:
        return 0.0  # no signal -> return 0 (neutral)

    rho, _ = spearmanr(hc_mean_vuln, cvd_loco_target)
    if not np.isfinite(rho):
        return 0.0
    return -rho  # minimize negative correlation


def fit_loco(roi, cvd_subj, hc_amps, output_dir):
    """Run LOCO fitting for one CVD subject x ROI."""
    cvd_type = CVD_TYPE[cvd_subj]
    cvd_target = load_cvd_loco_target(cvd_subj, roi)
    print(f'    CVD LOCO target: {np.round(cvd_target, 3)}')

    model_results = {}

    for model_name in MODELS:
        bounds = MODELS[model_name]['bounds']
        x0 = get_initial_params(model_name, cvd_type)

        mode_results = {}
        for mode in ['shift_at_test', 'shift_at_both']:
            res = minimize(
                loco_objective, x0,
                args=(model_name, hc_amps, cvd_target, cvd_type, mode),
                method='L-BFGS-B', bounds=bounds,
                options={'maxiter': 200, 'ftol': 1e-8}
            )

            # Recompute final simulation for detailed output
            C_orig = create_basis_matrix(HUE_ANGLES, N_CHANNELS)
            C_shift = get_design_matrix(model_name, res.x, cvd_type=cvd_type)
            hc_mean_vuln, hc_all_vuln = simulate_hc_loco(
                hc_amps, C_orig, C_shift, mode)

            rho, p = spearmanr(hc_mean_vuln, cvd_target)
            if not np.isfinite(rho):
                rho, p = 0.0, 1.0

            mode_results[mode] = {
                'params': res.x.tolist(),
                'spearman_r': float(rho),
                'spearman_p': float(p),
                'hc_shifted_vuln': hc_mean_vuln.tolist(),
                'success': bool(res.success),
            }

        # Report primary mode
        primary = mode_results['shift_at_test']
        print(f'      {model_name}: rho={primary["spearman_r"]:.3f} '
              f'(p={primary["spearman_p"]:.3f})')

        model_results[model_name] = mode_results

    # Save
    out_dir = Path(output_dir) / roi
    out_dir.mkdir(parents=True, exist_ok=True)
    result = {
        'subject': cvd_subj,
        'roi': roi,
        'cvd_type': cvd_type,
        'timestamp': datetime.now().isoformat(),
        'cvd_loco_target': cvd_target.tolist(),
        'models': model_results,
    }
    out_path = out_dir / f'sub-{cvd_subj}_loco_sim.json'
    with open(out_path, 'w') as f:
        json.dump(result, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description='Step 3: LOCO simulation')
    parser.add_argument('--output_dir', type=str, default='results/step3_loco')
    parser.add_argument('--rois', nargs='+', default=ROIS)
    parser.add_argument('--cvd_subjects', nargs='+', default=CVD_SUBJECTS)
    args = parser.parse_args()

    print('=' * 60)
    print('Step 3: LOCO Simulation Fitting (Criterion 3)')
    print(f'ROIs: {args.rois}')
    print(f'CVD subjects: {args.cvd_subjects}')
    print('=' * 60)

    for roi in args.rois:
        print(f'\n--- {roi} ---')

        # Load HC amplitudes once per ROI
        print(f'  Loading HC amplitudes...')
        hc_amps = []
        for subj in HC_SUBJECTS:
            amp = load_amplitudes(LOCAL_BASELINE, subj, roi)
            hc_amps.append(amp)

        for cvd_subj in args.cvd_subjects:
            print(f'\n  sub-{cvd_subj} ({CVD_TYPE[cvd_subj]}):')
            fit_loco(roi, cvd_subj, hc_amps, args.output_dir)

    print('\nStep 3 (LOCO) complete.')


if __name__ == '__main__':
    main()
