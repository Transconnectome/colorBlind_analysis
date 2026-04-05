#!/usr/bin/env python3
"""
step2_cross_eval.py — Bidirectional cross-evaluation (v2, W-fixed).

Direction A→B: RDM-fit δθ → LOCO vulnerability (W-fixed) → compare to CVD
Direction B→A: LOCO-fit δθ → SRM-RDM → compare to CVD RDM

Convergence criterion: |δθ_A - δθ_B| consistency across criteria.

Uses Spearman + permutation test for LOCO evaluation.
Uses Spearman + MSE for RDM evaluation.

Usage:
    python scripts/step2_cross_eval.py \
        --rdm_dir results/v2/step1_rdm \
        --loco_dir results/v2/step1_loco_wfixed \
        --precomputed_dir results/precomputed \
        --output_dir results/v2/step2_cross
"""

import argparse
import json
import numpy as np
from pathlib import Path
from datetime import datetime
from scipy.spatial.distance import pdist, squareform
from scipy.stats import spearmanr
import sys

_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR))

_FWD_DIR = str(Path(__file__).resolve().parent.parent.parent.parent
               / 'future_phase1_forward_model' / 'scripts')
sys.path.insert(0, _FWD_DIR)

from utils_forward_model import (
    HC_SUBJECTS, CVD_SUBJECTS, ROIS, K_VALUES, N_CHANNELS, N_RUNS, N_COLORS,
    HUE_ANGLES, load_amplitudes, create_basis_matrix, voxel_pattern_correlation,
)
from utils_distortion_models import (
    MODELS, get_design_matrix, get_delta_theta,
)

# Import v2 metrics and W-fixed functions
from step1_fit_loco_v2 import (
    lins_ccc, mse_decompose,
    precompute_hc_W, simulate_mean_hc_wfixed,
    permutation_test_mse,
    permutation_test_spearman, load_cvd_loco_target,
)

LOCAL_BASELINE = Path(__file__).resolve().parent.parent.parent.parent \
    / 'phase1_preprocess_decoding' / 'results' / 'full_dataset_C010'
FWD_RESULTS = Path(__file__).resolve().parent.parent.parent.parent \
    / 'future_phase1_forward_model' / 'results'

CVD_TYPE = {'08': 'deutan', '09': 'protan', '10': 'normal'}

FIT_MODELS = ['cone_1way', 'cone_3way', 'fourier', 'per_color']


# ============================================================================
# Direction A→B: RDM-fit δθ → LOCO evaluation
# ============================================================================

def eval_rdm_params_on_loco(rdm_params, model_name, hc_W_dict, hc_amps,
                            cvd_vuln, cvd_type):
    """Evaluate RDM-fitted δθ on LOCO criterion (W-fixed, mean-HC).

    Computes mean-HC vulnerability at RDM-fit δθ using W-fixed approach,
    then evaluates Spearman profile match and MSE against CVD.

    Returns:
        eval_result: dict with mean-HC and per-HC metrics
    """
    C_shifted = get_design_matrix(model_name, rdm_params,
                                  cvd_type=cvd_type)
    mean_vuln, per_hc_vuln = simulate_mean_hc_wfixed(
        hc_W_dict, hc_amps, C_shifted)

    # Mean-HC metrics
    mse, bias_sq, profile_mse = mse_decompose(mean_vuln, cvd_vuln)
    ccc = lins_ccc(mean_vuln, cvd_vuln)
    rho, p_rho = spearmanr(mean_vuln, cvd_vuln)
    if not np.isfinite(rho):
        rho, p_rho = 0.0, 1.0

    perm_p_rho, _, _ = permutation_test_spearman(mean_vuln, cvd_vuln)
    perm_p_mse, _ = permutation_test_mse(mean_vuln, cvd_vuln)

    # Per-HC individual Spearman
    per_hc_rhos = {}
    for subj, vuln in per_hc_vuln.items():
        r, _ = spearmanr(vuln, cvd_vuln)
        per_hc_rhos[subj] = float(r) if np.isfinite(r) else 0.0

    return {
        'mean_hc_vuln': mean_vuln.tolist(),
        'spearman_r': float(rho),
        'perm_p_spearman': perm_p_rho,
        'mse': mse,
        'bias_sq': bias_sq,
        'profile_mse': profile_mse,
        'perm_p_mse': perm_p_mse,
        'ccc': float(ccc),
        'per_hc_spearman_r': per_hc_rhos,
    }


# ============================================================================
# Direction B→A: LOCO-fit δθ → RDM evaluation
# ============================================================================

def eval_loco_params_on_rdm(loco_params, model_name, precomputed_dir,
                            roi, cvd_subj, cvd_type):
    """Evaluate LOCO-fitted δθ on RDM criterion.

    For each LOO fold: compute A_g @ C(θ+δ)^T → RDM → compare to CVD RDM.

    Returns:
        eval_result: dict with per-fold and aggregate metrics
    """
    per_fold = {}
    all_rhos = []
    all_losses = []

    for fold_idx in range(len(HC_SUBJECTS)):
        fold_dir = Path(precomputed_dir) / roi / f'fold_{fold_idx}'
        A_g = np.load(fold_dir / 'A_g.npy')
        Z_cvd = np.load(fold_dir / f'Z_cvd_{cvd_subj}.npy')

        # CVD target RDM
        cvd_rdm = squareform(pdist(Z_cvd.T, 'correlation'))
        cvd_upper = cvd_rdm[np.triu_indices(8, k=1)]

        # Predicted RDM
        C_shifted = get_design_matrix(model_name, loco_params,
                                      cvd_type=cvd_type)
        Z_model = A_g @ C_shifted.T
        rdm_model = squareform(pdist(Z_model.T, 'correlation'))
        pred_upper = rdm_model[np.triu_indices(8, k=1)]

        loss = float(np.sum((pred_upper - cvd_upper) ** 2))
        rho, p = spearmanr(pred_upper, cvd_upper)
        if not np.isfinite(rho):
            rho, p = 0.0, 1.0

        per_fold[fold_idx] = {
            'loss': loss,
            'spearman_r': float(rho),
            'spearman_p': float(p),
        }
        all_rhos.append(float(rho))
        all_losses.append(loss)

    return {
        'per_fold': per_fold,
        'loss_median': float(np.median(all_losses)),
        'spearman_r_median': float(np.median(all_rhos)),
        'spearman_r_range': [float(np.min(all_rhos)),
                             float(np.max(all_rhos))],
    }


# ============================================================================
# Convergence analysis
# ============================================================================

def compute_convergence(rdm_params, loco_params, model_name, cvd_type):
    """Compute convergence metrics between RDM-fit and LOCO-fit δθ.

    For cone models: |Δλ_rdm - Δλ_loco| in nm
    For angle models: RMSD of δθ vectors

    Returns:
        convergence: dict with metrics
    """
    rdm_delta = get_delta_theta(model_name, rdm_params, cvd_type)
    loco_delta = get_delta_theta(model_name, loco_params, cvd_type)

    diff = rdm_delta - loco_delta
    rmsd = float(np.sqrt(np.mean(diff ** 2)))
    max_diff = float(np.max(np.abs(diff)))

    result = {
        'rdm_delta_theta': rdm_delta.tolist(),
        'loco_delta_theta': loco_delta.tolist(),
        'delta_diff': diff.tolist(),
        'rmsd_degrees': rmsd,
        'max_diff_degrees': max_diff,
    }

    # For cone_1way: direct parameter comparison
    if model_name == 'cone_1way':
        result['param_diff_nm'] = float(abs(rdm_params[0] - loco_params[0]))
        result['converged'] = result['param_diff_nm'] < 5.0
    elif model_name == 'cone_3way':
        result['param_diff_nm'] = [
            float(abs(rdm_params[i] - loco_params[i])) for i in range(3)
        ]
        result['converged'] = all(d < 5.0 for d in result['param_diff_nm'])
    else:
        result['converged'] = rmsd < 10.0

    return result


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Step 2: Cross-evaluation (v2)')
    parser.add_argument('--rdm_dir', type=str,
                        default='results/v2/step1_rdm')
    parser.add_argument('--loco_dir', type=str,
                        default='results/v2/step1_loco_wfixed')
    parser.add_argument('--precomputed_dir', type=str,
                        default='results/precomputed')
    parser.add_argument('--output_dir', type=str,
                        default='results/v2/step2_cross')
    parser.add_argument('--rois', nargs='+', default=['V4'])
    parser.add_argument('--cvd_subjects', nargs='+', default=CVD_SUBJECTS)
    parser.add_argument('--models', nargs='+', default=FIT_MODELS)
    parser.add_argument('--baseline_dir', type=str,
                        default=str(LOCAL_BASELINE))
    args = parser.parse_args()

    print('=' * 60)
    print('Step 2: Bidirectional Cross-Evaluation (v2)')
    print(f'ROIs: {args.rois}')
    print(f'CVD subjects: {args.cvd_subjects}')
    print(f'Models: {args.models}')
    print('=' * 60)

    for roi in args.rois:
        print(f'\n=== {roi} ===')

        # Load HC amplitudes for LOCO evaluation
        hc_amps = {}
        for subj in HC_SUBJECTS:
            hc_amps[subj] = load_amplitudes(args.baseline_dir, subj, roi)

        # Precompute W for W-fixed LOCO evaluation
        C_original = create_basis_matrix(HUE_ANGLES, N_CHANNELS)
        hc_W, _ = precompute_hc_W(hc_amps, C_original)
        print(f'  Precomputed W for {len(hc_W)} HC subjects')

        for cvd_subj in args.cvd_subjects:
            cvd_type = CVD_TYPE[cvd_subj]
            cvd_vuln = load_cvd_loco_target(cvd_subj, roi)
            print(f'\n  sub-{cvd_subj} ({cvd_type}):')

            # Load RDM results
            rdm_path = Path(args.rdm_dir) / roi / f'sub-{cvd_subj}_rdm_v2.json'
            if not rdm_path.exists():
                print(f'    WARNING: RDM results not found: {rdm_path}')
                continue
            with open(rdm_path) as f:
                rdm_data = json.load(f)

            # Load LOCO results
            loco_path = Path(args.loco_dir) / roi / f'sub-{cvd_subj}_loco_v2.json'
            if not loco_path.exists():
                print(f'    WARNING: LOCO results not found: {loco_path}')
                continue
            with open(loco_path) as f:
                loco_data = json.load(f)

            cross_results = {}

            for model_name in args.models:
                print(f'\n    {model_name}:')

                # --- Get median RDM params (path_A, group prior) ---
                rdm_agg = rdm_data.get('aggregate', {})
                rdm_key = f'{model_name}_path_A'
                if rdm_key not in rdm_agg:
                    print(f'      No RDM aggregate for {rdm_key}, skipping')
                    continue
                rdm_params = np.array(rdm_agg[rdm_key]['params_median'])

                # --- Get LOCO-fit params (mean-HC Spearman) ---
                loco_fits = loco_data.get('fit_results', {})
                if model_name not in loco_fits:
                    print(f'      No LOCO fit for {model_name}, skipping')
                    continue
                loco_params = np.array(loco_fits[model_name]['params'])

                # --- Direction A→B: RDM δθ → LOCO eval (W-fixed) ---
                print(f'      A→B (RDM→LOCO, W-fixed)...')
                a_to_b = eval_rdm_params_on_loco(
                    rdm_params, model_name, hc_W, hc_amps,
                    cvd_vuln, cvd_type)
                print(f'        Spearman r={a_to_b["spearman_r"]:.3f} '
                      f'perm_p={a_to_b["perm_p_spearman"]:.4f} '
                      f'CCC={a_to_b["ccc"]:.3f}')

                # --- Direction B→A: LOCO δθ → RDM eval ---
                print(f'      B→A (LOCO→RDM)...')
                b_to_a = eval_loco_params_on_rdm(
                    loco_params, model_name,
                    args.precomputed_dir, roi, cvd_subj, cvd_type)
                print(f'        loss_med={b_to_a["loss_median"]:.4f} '
                      f'r_med={b_to_a["spearman_r_median"]:.3f}')

                # --- Convergence ---
                conv = compute_convergence(
                    rdm_params, loco_params, model_name, cvd_type)
                status = 'CONVERGED' if conv['converged'] else 'DIVERGED'
                print(f'      Convergence: {status} '
                      f'(RMSD={conv["rmsd_degrees"]:.1f}°)')

                cross_results[model_name] = {
                    'rdm_params_median': rdm_params.tolist(),
                    'loco_params_median': loco_params.tolist(),
                    'A_to_B': a_to_b,
                    'B_to_A': b_to_a,
                    'convergence': conv,
                }

            # Save
            out_dir = Path(args.output_dir) / roi
            out_dir.mkdir(parents=True, exist_ok=True)
            result = {
                'subject': cvd_subj,
                'roi': roi,
                'cvd_type': cvd_type,
                'timestamp': datetime.now().isoformat(),
                'cvd_loco_target': cvd_vuln.tolist(),
                'models': cross_results,
            }
            out_path = out_dir / f'sub-{cvd_subj}_cross_v2.json'
            with open(out_path, 'w') as f:
                json.dump(result, f, indent=2)
            print(f'\n    Saved: {out_path}')

    print('\nStep 2 (Cross-Eval v2) complete.')


if __name__ == '__main__':
    main()
