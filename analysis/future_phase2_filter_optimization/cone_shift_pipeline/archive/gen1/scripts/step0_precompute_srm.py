#!/usr/bin/env python3
"""
step0_precompute.py — 7-fold LOO SRM precomputation for cone-shift pipeline v2.

For each fold i (held-out HC sub-i):
  1. Train SRM on 6 HC subjects
  2. Project held-out HC and CVD into shared space via SVD
  3. Compute group prior A_g from 6 training HC
  4. Save all intermediate data for downstream fitting

Requires BrainIAK (conda activate srm).

Usage:
    python scripts/step0_precompute.py \
        --output_dir results/precomputed \
        --rois V4
"""

import argparse
import json
import numpy as np
from pathlib import Path
from datetime import datetime
import pickle
import sys

_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR))

_FWD_DIR = str(Path(__file__).resolve().parent.parent.parent.parent
               / 'future_phase1_forward_model' / 'scripts')
sys.path.insert(0, _FWD_DIR)

from utils_forward_model import (
    HC_SUBJECTS, CVD_SUBJECTS, ROIS, K_VALUES, N_CHANNELS,
    HUE_ANGLES, load_amplitudes, create_basis_matrix, save_config,
    gcv_select_alpha, fit_W_ridge,
)

try:
    from brainiak.funcalign.srm import SRM
    BRAINIAK_AVAILABLE = True
except ImportError:
    BRAINIAK_AVAILABLE = False
    print('WARNING: brainiak not available. Cannot run SRM.')

LOCAL_BASELINE = Path(__file__).resolve().parent.parent.parent.parent \
    / 'phase1_preprocess_decoding' / 'results' / 'full_dataset_C010'

CVD_TYPE = {'08': 'deutan', '09': 'protan', '10': 'normal'}


def project_new_subject_svd(shared_response, beta_new):
    """Project new subject into SRM space via SVD.

    Args:
        shared_response: (k, 8) shared response from SRM
        beta_new: (8, V_s) run-averaged amplitudes

    Returns:
        R_new: (V_s, k) orthonormal projection
    """
    S = shared_response
    W_init = beta_new.T @ np.linalg.pinv(S)  # (V_s, k)
    U, _, Vt = np.linalg.svd(W_init, full_matrices=False)
    return U @ Vt


def compute_A_i(R_i, beta_i, C, lambda_A=0.0):
    """Compute encoding matrix A_i in SRM common space.

    A_i = Z_i @ C @ inv(C^T C + lambda_A * I)
    where Z_i = R_i^T @ beta_i^T

    Args:
        R_i: (V_s, k) SRM projection
        beta_i: (8, V_s) run-averaged amplitudes
        C: (8, K) design matrix
        lambda_A: regularization

    Returns:
        A_i: (k, K) encoding in common space
        Z_i: (k, 8) common-space response
    """
    K = C.shape[1]
    Z_i = R_i.T @ beta_i.T  # (k, 8)
    CtC_reg_inv = np.linalg.inv(C.T @ C + lambda_A * np.eye(K))
    A_i = Z_i @ C @ CtC_reg_inv  # (k, K)
    return A_i, Z_i


def precompute_fold(fold_idx, roi, baseline_dir, output_dir, n_iter=20,
                    lambda_A=0.0):
    """Precompute one LOO fold.

    Args:
        fold_idx: index of held-out HC (0-6)
        roi: ROI name
        baseline_dir: path to C010 data
        output_dir: base output directory
        n_iter: SRM iterations
        lambda_A: regularization for A_i

    Returns:
        fold_summary: dict with fold metadata
    """
    k = K_VALUES[roi]
    held_out_subj = HC_SUBJECTS[fold_idx]
    train_subjects = [s for s in HC_SUBJECTS if s != held_out_subj]

    fold_dir = Path(output_dir) / roi / f'fold_{fold_idx}'
    fold_dir.mkdir(parents=True, exist_ok=True)

    print(f'  Fold {fold_idx}: held-out=sub-{held_out_subj}, '
          f'train={[f"sub-{s}" for s in train_subjects]}')

    # Load all amplitudes
    all_amps = {}
    for subj in HC_SUBJECTS:
        all_amps[subj] = load_amplitudes(baseline_dir, subj, roi)

    cvd_amps = {}
    for subj in CVD_SUBJECTS:
        cvd_amps[subj] = load_amplitudes(baseline_dir, subj, roi)

    # --- 1. Train SRM on 6 training HC ---
    srm_input = []
    for subj in train_subjects:
        beta = all_amps[subj].mean(axis=0)  # (8, V_s)
        srm_input.append(beta.T)  # (V_s, 8)

    srm = SRM(n_iter=n_iter, features=k)
    srm.fit(srm_input)

    shared_response = srm.s_  # (k, 8)
    np.save(fold_dir / 'shared_response.npy', shared_response)

    # Save training HC SRM weights
    train_W_list = []
    for i, subj in enumerate(train_subjects):
        W_i = srm.w_[i]  # (V_s, k)
        np.save(fold_dir / f'W_train_{subj}.npy', W_i)
        train_W_list.append(W_i)

    # --- 2. Project held-out HC into shared space ---
    beta_held = all_amps[held_out_subj].mean(axis=0)  # (8, V_s)
    R_held = project_new_subject_svd(shared_response, beta_held)
    np.save(fold_dir / 'W_heldout.npy', R_held)

    # --- 3. Project CVD subjects ---
    for cvd_subj in CVD_SUBJECTS:
        beta_cvd = cvd_amps[cvd_subj].mean(axis=0)
        R_cvd = project_new_subject_svd(shared_response, beta_cvd)
        np.save(fold_dir / f'W_cvd_{cvd_subj}.npy', R_cvd)

        Z_cvd = R_cvd.T @ beta_cvd.T  # (k, 8)
        np.save(fold_dir / f'Z_cvd_{cvd_subj}.npy', Z_cvd)

    # --- 4. Compute group prior A_g from 6 training HC ---
    C = create_basis_matrix(HUE_ANGLES, N_CHANNELS)
    A_list = []

    for i, subj in enumerate(train_subjects):
        R_i = train_W_list[i]
        beta_i = all_amps[subj].mean(axis=0)
        A_i, Z_i = compute_A_i(R_i, beta_i, C, lambda_A)
        np.save(fold_dir / f'A_train_{subj}.npy', A_i)
        A_list.append(A_i)

    A_g = np.mean(A_list, axis=0)  # (k, K)
    np.save(fold_dir / 'A_g.npy', A_g)

    # --- 5. Compute held-out HC encoding (for validation) ---
    A_held, Z_held = compute_A_i(R_held, beta_held, C, lambda_A)
    np.save(fold_dir / 'A_heldout.npy', A_held)
    np.save(fold_dir / 'Z_heldout.npy', Z_held)

    # --- 6. Also fit voxel-space ridge weights for training HC ---
    C_pooled = np.tile(C, (6, 1))  # (48, K)
    hc_ridge_weights = {}
    for subj in train_subjects:
        amp = all_amps[subj]
        V_s = amp.shape[2]
        X = amp.reshape(-1, V_s)
        alpha, _ = gcv_select_alpha(C_pooled, X)
        W = fit_W_ridge(C_pooled, X, alpha)
        np.save(fold_dir / f'W_ridge_{subj}.npy', W)
        hc_ridge_weights[subj] = float(alpha)

    fold_summary = {
        'fold_idx': fold_idx,
        'held_out': held_out_subj,
        'train_subjects': train_subjects,
        'k': k,
        'n_iter': n_iter,
        'lambda_A': lambda_A,
        'hc_ridge_alphas': hc_ridge_weights,
        'shared_response_shape': list(shared_response.shape),
    }

    with open(fold_dir / 'fold_config.json', 'w') as f:
        json.dump(fold_summary, f, indent=2)

    return fold_summary


def main():
    if not BRAINIAK_AVAILABLE:
        print('ERROR: brainiak required. Use: conda activate srm')
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description='Step 0: LOO SRM precomputation')
    parser.add_argument('--output_dir', type=str,
                        default='results/precomputed')
    parser.add_argument('--rois', nargs='+', default=['V4'])
    parser.add_argument('--baseline_dir', type=str,
                        default=str(LOCAL_BASELINE))
    parser.add_argument('--n_iter', type=int, default=20)
    parser.add_argument('--lambda_A', type=float, default=0.0)
    args = parser.parse_args()

    print('=' * 60)
    print('Step 0: LOO SRM Precomputation (v2)')
    print(f'ROIs: {args.rois}')
    print(f'SRM n_iter: {args.n_iter}')
    print(f'lambda_A: {args.lambda_A}')
    print(f'Baseline: {args.baseline_dir}')
    print('=' * 60)

    all_summaries = {}
    for roi in args.rois:
        print(f'\n=== {roi} (k={K_VALUES[roi]}) ===')
        roi_summaries = []

        for fold_idx in range(len(HC_SUBJECTS)):
            summary = precompute_fold(
                fold_idx, roi, args.baseline_dir, args.output_dir,
                n_iter=args.n_iter, lambda_A=args.lambda_A)
            roi_summaries.append(summary)

        all_summaries[roi] = roi_summaries

    save_config(args.output_dir,
                step='step0_precompute_v2',
                rois=args.rois,
                n_folds=len(HC_SUBJECTS),
                hc_subjects=HC_SUBJECTS,
                cvd_subjects=CVD_SUBJECTS,
                n_iter=args.n_iter,
                lambda_A=args.lambda_A,
                summaries=all_summaries)

    print('\nStep 0 precomputation complete.')


if __name__ == '__main__':
    main()
