#!/usr/bin/env python3
"""
step2b_cross_roi_eval.py — Between-ROI cross-evaluation.

Tests cone-shift ROI independence:
  Forward: V1/V2 RDM-fit delta_theta -> V4 LOCO eval (W-fixed)
  Reverse: V4 LOCO-fit delta_theta -> V1/V2 RDM eval

If cone shift is retinal (ROI-independent), delta_theta should be consistent
across ROIs and cross-ROI evaluation should yield significant results.

Uses precomputed SRM data and W-fixed LOCO.

Usage:
    python scripts/step2b_cross_roi_eval.py \
        --rdm_dir results/v2/step1_rdm \
        --loco_dir results/v2/step1_loco_wfixed \
        --precomputed_dir results/precomputed \
        --output_dir results/v2/step2b_cross_roi
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
    HC_SUBJECTS, CVD_SUBJECTS, ROIS, K_VALUES, N_CHANNELS, N_RUNS,
    HUE_ANGLES, load_amplitudes, create_basis_matrix,
)
from utils_distortion_models import get_design_matrix, get_delta_theta
from step1_fit_loco_v2 import (
    precompute_hc_W, simulate_mean_hc_wfixed,
    permutation_test_spearman, load_cvd_loco_target,
    lins_ccc, mse_decompose,
)

LOCAL_BASELINE = Path(__file__).resolve().parent.parent.parent.parent \
    / 'phase1_preprocess_decoding' / 'results' / 'full_dataset_C010'

CVD_TYPE = {'08': 'deutan', '09': 'protan', '10': 'normal'}


def eval_cross_roi_loco(source_params, model_name, target_roi,
                        hc_W_target, hc_amps_target,
                        cvd_vuln_target, cvd_type):
    """Evaluate source ROI's delta_theta on target ROI's LOCO (W-fixed).

    Args:
        source_params: fitted parameters from source ROI
        model_name: distortion model name
        target_roi: target ROI name
        hc_W_target: dict {subj: (K, V_s)} W for target ROI
        hc_amps_target: dict {subj: (6, 8, V_s)} amps for target ROI
        cvd_vuln_target: (8,) CVD LOCO target for target ROI
        cvd_type: CVD type string

    Returns:
        eval_result: dict with LOCO evaluation metrics
    """
    C_shifted = get_design_matrix(model_name, source_params,
                                  cvd_type=cvd_type)
    mean_vuln, per_hc_vuln = simulate_mean_hc_wfixed(
        hc_W_target, hc_amps_target, C_shifted)

    rho, p_rho = spearmanr(mean_vuln, cvd_vuln_target)
    if not np.isfinite(rho):
        rho, p_rho = 0.0, 1.0

    perm_p, _, _ = permutation_test_spearman(mean_vuln, cvd_vuln_target)
    mse, bias_sq, profile_mse = mse_decompose(mean_vuln, cvd_vuln_target)
    ccc = lins_ccc(mean_vuln, cvd_vuln_target)

    per_hc_rhos = {}
    for subj, vuln in per_hc_vuln.items():
        r, _ = spearmanr(vuln, cvd_vuln_target)
        per_hc_rhos[subj] = float(r) if np.isfinite(r) else 0.0

    return {
        'mean_hc_vuln': mean_vuln.tolist(),
        'spearman_r': float(rho),
        'perm_p_spearman': perm_p,
        'mse': mse,
        'bias_sq': bias_sq,
        'profile_mse': profile_mse,
        'ccc': float(ccc),
        'per_hc_spearman_r': per_hc_rhos,
    }


def eval_cross_roi_rdm(source_params, model_name, target_roi,
                       precomputed_dir, cvd_subj, cvd_type):
    """Evaluate source ROI's delta_theta on target ROI's RDM criterion.

    For each LOO fold: A_g @ C(theta+delta)^T -> RDM vs CVD RDM.

    Args:
        source_params: fitted parameters from source ROI
        model_name: distortion model name
        target_roi: target ROI name
        precomputed_dir: path to precomputed SRM data
        cvd_subj: CVD subject ID
        cvd_type: CVD type string

    Returns:
        eval_result: dict with per-fold and aggregate RDM metrics
    """
    per_fold = {}
    all_rhos = []
    all_losses = []

    for fold_idx in range(len(HC_SUBJECTS)):
        fold_dir = Path(precomputed_dir) / target_roi / f'fold_{fold_idx}'
        if not fold_dir.exists():
            continue

        A_g = np.load(fold_dir / 'A_g.npy')
        Z_cvd = np.load(fold_dir / f'Z_cvd_{cvd_subj}.npy')

        cvd_rdm = squareform(pdist(Z_cvd.T, 'correlation'))
        cvd_upper = cvd_rdm[np.triu_indices(8, k=1)]

        C_shifted = get_design_matrix(model_name, source_params,
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

    if not all_rhos:
        return {'error': f'No precomputed data for {target_roi}'}

    return {
        'per_fold': per_fold,
        'loss_median': float(np.median(all_losses)),
        'spearman_r_median': float(np.median(all_rhos)),
        'spearman_r_range': [float(np.min(all_rhos)),
                             float(np.max(all_rhos))],
    }


def main():
    parser = argparse.ArgumentParser(
        description='Step 2b: Between-ROI cross-evaluation')
    parser.add_argument('--rdm_dir', type=str,
                        default='results/v2/step1_rdm')
    parser.add_argument('--loco_dir', type=str,
                        default='results/v2/step1_loco_wfixed')
    parser.add_argument('--precomputed_dir', type=str,
                        default='results/precomputed')
    parser.add_argument('--output_dir', type=str,
                        default='results/v2/step2b_cross_roi')
    parser.add_argument('--source_rois', nargs='+', default=['V1', 'V2'])
    parser.add_argument('--target_roi', type=str, default='V4')
    parser.add_argument('--cvd_subjects', nargs='+', default=CVD_SUBJECTS)
    parser.add_argument('--baseline_dir', type=str,
                        default=str(LOCAL_BASELINE))
    args = parser.parse_args()

    model_name = 'cone_1way'

    print('=' * 60)
    print('Step 2b: Between-ROI Cross-Evaluation')
    print(f'Source ROIs: {args.source_rois}')
    print(f'Target ROI: {args.target_roi}')
    print(f'Model: {model_name}')
    print(f'CVD subjects: {args.cvd_subjects}')
    print('=' * 60)

    # Load target ROI data (V4)
    print(f'\nLoading target ROI ({args.target_roi}) data...')
    hc_amps_target = {}
    for subj in HC_SUBJECTS:
        hc_amps_target[subj] = load_amplitudes(
            args.baseline_dir, subj, args.target_roi)

    C_original = create_basis_matrix(HUE_ANGLES, N_CHANNELS)
    hc_W_target, _ = precompute_hc_W(hc_amps_target, C_original)
    print(f'  Precomputed W for {len(hc_W_target)} HC in {args.target_roi}')

    for cvd_subj in args.cvd_subjects:
        cvd_type = CVD_TYPE[cvd_subj]
        print(f'\n{"="*50}')
        print(f'sub-{cvd_subj} ({cvd_type})')
        print(f'{"="*50}')

        # Load target (V4) LOCO target
        cvd_vuln_target = load_cvd_loco_target(cvd_subj, args.target_roi)
        print(f'  V4 CVD target: {np.round(cvd_vuln_target, 3)}')

        # Load V4 LOCO-fit delta_theta
        loco_v4_path = (Path(args.loco_dir) / args.target_roi
                        / f'sub-{cvd_subj}_loco_v2.json')
        v4_loco_params = None
        if loco_v4_path.exists():
            with open(loco_v4_path) as f:
                v4_data = json.load(f)
            fits = v4_data.get('fit_results', {})
            if model_name in fits:
                v4_loco_params = np.array(fits[model_name]['params'])
                print(f'  V4 LOCO-fit: delta={v4_loco_params[0]:.2f}nm')

        cross_results = {}

        for src_roi in args.source_rois:
            print(f'\n  --- Source: {src_roi} ---')

            # === Forward: source RDM-fit -> target LOCO ===
            rdm_path = (Path(args.rdm_dir) / src_roi
                        / f'sub-{cvd_subj}_rdm_v2.json')
            rdm_params = None
            if rdm_path.exists():
                with open(rdm_path) as f:
                    rdm_data = json.load(f)
                agg = rdm_data.get('aggregate', {})
                key = f'{model_name}_path_A'
                if key in agg:
                    rdm_params = np.array(agg[key]['params_median'])
                    rdm_sd = agg[key].get('params_sd', [0])
                    print(f'    {src_roi} RDM-fit: '
                          f'delta={rdm_params[0]:.2f}nm '
                          f'(sd={rdm_sd[0]:.2f})')

            forward_result = None
            if rdm_params is not None:
                print(f'    Forward: {src_roi} RDM -> '
                      f'{args.target_roi} LOCO...')
                forward_result = eval_cross_roi_loco(
                    rdm_params, model_name, args.target_roi,
                    hc_W_target, hc_amps_target,
                    cvd_vuln_target, cvd_type)
                print(f'      Spearman r={forward_result["spearman_r"]:.3f} '
                      f'perm_p={forward_result["perm_p_spearman"]:.4f} '
                      f'CCC={forward_result["ccc"]:.3f}')

            # === Reverse: V4 LOCO-fit -> source RDM ===
            reverse_result = None
            if v4_loco_params is not None:
                src_precomp = Path(args.precomputed_dir) / src_roi
                if src_precomp.exists():
                    print(f'    Reverse: {args.target_roi} LOCO -> '
                          f'{src_roi} RDM...')
                    reverse_result = eval_cross_roi_rdm(
                        v4_loco_params, model_name, src_roi,
                        args.precomputed_dir, cvd_subj, cvd_type)
                    if 'error' not in reverse_result:
                        print(f'      RDM r_median='
                              f'{reverse_result["spearman_r_median"]:.3f} '
                              f'loss_median='
                              f'{reverse_result["loss_median"]:.4f}')
                    else:
                        print(f'      {reverse_result["error"]}')
                else:
                    print(f'    Reverse: skipped (no precomputed data '
                          f'for {src_roi})')

            # === Source LOCO-fit -> target LOCO (if available) ===
            src_loco_path = (Path(args.loco_dir) / src_roi
                             / f'sub-{cvd_subj}_loco_v2.json')
            src_loco_result = None
            src_loco_params = None
            if src_loco_path.exists():
                with open(src_loco_path) as f:
                    src_loco_data = json.load(f)
                src_fits = src_loco_data.get('fit_results', {})
                if model_name in src_fits:
                    src_loco_params = np.array(
                        src_fits[model_name]['params'])
                    print(f'    {src_roi} LOCO-fit: '
                          f'delta={src_loco_params[0]:.2f}nm')
                    print(f'    Cross-LOCO: {src_roi} LOCO -> '
                          f'{args.target_roi} LOCO...')
                    src_loco_result = eval_cross_roi_loco(
                        src_loco_params, model_name, args.target_roi,
                        hc_W_target, hc_amps_target,
                        cvd_vuln_target, cvd_type)
                    print(f'      Spearman r='
                          f'{src_loco_result["spearman_r"]:.3f} '
                          f'perm_p='
                          f'{src_loco_result["perm_p_spearman"]:.4f}')

            # === Convergence: delta_theta comparison ===
            convergence = {}
            if rdm_params is not None and v4_loco_params is not None:
                diff = abs(rdm_params[0] - v4_loco_params[0])
                convergence['rdm_vs_v4_loco'] = {
                    'source_delta_nm': float(rdm_params[0]),
                    'target_delta_nm': float(v4_loco_params[0]),
                    'abs_diff_nm': float(diff),
                    'converged': bool(diff < 10.0),
                }
            if src_loco_params is not None and v4_loco_params is not None:
                diff = abs(src_loco_params[0] - v4_loco_params[0])
                convergence['src_loco_vs_v4_loco'] = {
                    'source_delta_nm': float(src_loco_params[0]),
                    'target_delta_nm': float(v4_loco_params[0]),
                    'abs_diff_nm': float(diff),
                    'converged': bool(diff < 10.0),
                }

            cross_results[src_roi] = {
                'rdm_params': rdm_params.tolist()
                    if rdm_params is not None else None,
                'src_loco_params': src_loco_params.tolist()
                    if src_loco_params is not None else None,
                'v4_loco_params': v4_loco_params.tolist()
                    if v4_loco_params is not None else None,
                'forward_rdm_to_loco': forward_result,
                'reverse_loco_to_rdm': reverse_result,
                'cross_loco': src_loco_result,
                'convergence': convergence,
            }

        # Save
        out_dir = Path(args.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        result = {
            'subject': cvd_subj,
            'cvd_type': cvd_type,
            'target_roi': args.target_roi,
            'source_rois': args.source_rois,
            'model': model_name,
            'timestamp': datetime.now().isoformat(),
            'cvd_vuln_target': cvd_vuln_target.tolist(),
            'cross_results': cross_results,
        }
        out_path = out_dir / f'sub-{cvd_subj}_cross_roi.json'
        with open(out_path, 'w') as f:
            json.dump(result, f, indent=2)
        print(f'\n  Saved: {out_path}')

    # Print summary table
    print(f'\n{"="*60}')
    print('Between-ROI Cross-Evaluation Summary (cone_1way)')
    print(f'{"="*60}')
    print(f'  {"Subject":>10} | {"Source":>6} | {"Criterion":>12} | '
          f'{"delta_nm":>8} | {"rho":>6} | {"perm_p":>7} | '
          f'{"Conv?":>5}')
    print(f'  {"-"*10}-+-{"-"*6}-+-{"-"*12}-+-{"-"*8}-+-{"-"*6}-+-'
          f'{"-"*7}-+-{"-"*5}')

    for cvd_subj in args.cvd_subjects:
        out_path = Path(args.output_dir) / f'sub-{cvd_subj}_cross_roi.json'
        if not out_path.exists():
            continue
        with open(out_path) as f:
            data = json.load(f)
        for src_roi, cr in data.get('cross_results', {}).items():
            # Forward
            fwd = cr.get('forward_rdm_to_loco')
            rdm_p = cr.get('rdm_params')
            if fwd and rdm_p:
                conv = cr.get('convergence', {}).get(
                    'rdm_vs_v4_loco', {})
                print(f'  sub-{cvd_subj:>5} | {src_roi:>6} | '
                      f'{"RDM->LOCO":>12} | {rdm_p[0]:>8.2f} | '
                      f'{fwd["spearman_r"]:>6.3f} | '
                      f'{fwd["perm_p_spearman"]:>7.4f} | '
                      f'{"Y" if conv.get("converged") else "N":>5}')
            # Cross-LOCO
            cl = cr.get('cross_loco')
            slp = cr.get('src_loco_params')
            if cl and slp:
                conv = cr.get('convergence', {}).get(
                    'src_loco_vs_v4_loco', {})
                print(f'  sub-{cvd_subj:>5} | {src_roi:>6} | '
                      f'{"LOCO->LOCO":>12} | {slp[0]:>8.2f} | '
                      f'{cl["spearman_r"]:>6.3f} | '
                      f'{cl["perm_p_spearman"]:>7.4f} | '
                      f'{"Y" if conv.get("converged") else "N":>5}')

    print('\nStep 2b (Cross-ROI) complete.')


if __name__ == '__main__':
    main()
