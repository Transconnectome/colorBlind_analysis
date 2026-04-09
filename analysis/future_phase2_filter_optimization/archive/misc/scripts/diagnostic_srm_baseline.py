#!/usr/bin/env python3
"""
diagnostic_srm_baseline.py — SRM prediction baseline diagnostic.

For each ROI (V1, V2, V4):
  For each LOO fold (0..6):
    1. A_g prediction quality: Z_pred = A_g @ C^T vs Z_heldout
    2. A_g vs mean training HC Z
    3. Mean train Z vs CVD Z (Phase 2 style)
    4. Inter-run consistency in SRM space
    5. A_g @ C(delta) sweep: does shifting move toward CVD?

Uses precomputed data from step0.

Usage:
    python scripts/diagnostic_srm_baseline.py \
        --precomputed_dir results/precomputed \
        --output_dir results/v2/srm_baseline
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
from utils_distortion_models import get_design_matrix

LOCAL_BASELINE = Path(__file__).resolve().parent.parent.parent.parent \
    / 'phase1_preprocess_decoding' / 'results' / 'full_dataset_C010'

CVD_TYPE = {'08': 'deutan', '09': 'protan', '10': 'normal'}


def rdm_spearman(Z1, Z2):
    """Spearman correlation between upper triangle of RDMs from two Z matrices.

    Args:
        Z1, Z2: (k, 8) SRM-space representations

    Returns:
        rho: Spearman r between RDM upper triangles
    """
    rdm1 = squareform(pdist(Z1.T, 'correlation'))
    rdm2 = squareform(pdist(Z2.T, 'correlation'))
    upper1 = rdm1[np.triu_indices(8, k=1)]
    upper2 = rdm2[np.triu_indices(8, k=1)]
    rho, _ = spearmanr(upper1, upper2)
    return float(rho) if np.isfinite(rho) else 0.0


def z_corr_mean(Z1, Z2):
    """Mean per-color correlation between two Z matrices.

    Args:
        Z1, Z2: (k, 8) SRM-space representations

    Returns:
        mean_r: mean Pearson r across 8 colors
    """
    corrs = []
    for c in range(8):
        r = np.corrcoef(Z1[:, c], Z2[:, c])[0, 1]
        corrs.append(float(r) if np.isfinite(r) else 0.0)
    return float(np.mean(corrs))


def frobenius_dist(Z1, Z2):
    """Frobenius distance between two matrices."""
    return float(np.linalg.norm(Z1 - Z2))


def diagnose_fold(fold_idx, roi, precomputed_dir, baseline_dir):
    """Run all diagnostics for one fold.

    Returns:
        fold_diag: dict with all diagnostic metrics
    """
    fold_dir = Path(precomputed_dir) / roi / f'fold_{fold_idx}'
    held_out = HC_SUBJECTS[fold_idx]
    train_subjects = [s for s in HC_SUBJECTS if s != held_out]

    # Load precomputed data
    A_g = np.load(fold_dir / 'A_g.npy')               # (k, K)
    Z_heldout = np.load(fold_dir / 'Z_heldout.npy')   # (k, 8)
    shared_resp = np.load(fold_dir / 'shared_response.npy')  # (k, 8)

    C = create_basis_matrix(HUE_ANGLES, N_CHANNELS)

    # --- 1. A_g prediction quality ---
    Z_pred = A_g @ C.T  # (k, 8)
    rdm_rho_pred_held = rdm_spearman(Z_pred, Z_heldout)
    z_corr_pred_held = z_corr_mean(Z_pred, Z_heldout)
    frob_pred_held = frobenius_dist(Z_pred, Z_heldout)

    # --- 2. A_g prediction vs shared response ---
    rdm_rho_pred_shared = rdm_spearman(Z_pred, shared_resp)

    # --- 3. Mean training HC Z ---
    # Compute Z_train_mean from training HC
    train_Z_list = []
    for subj in train_subjects:
        W_i = np.load(fold_dir / f'W_train_{subj}.npy')  # (V_s, k)
        amp = load_amplitudes(baseline_dir, subj, roi)
        beta = amp.mean(axis=0)  # (8, V_s)
        Z_i = W_i.T @ beta.T  # (k, 8)
        train_Z_list.append(Z_i)
    Z_train_mean = np.mean(train_Z_list, axis=0)  # (k, 8)

    rdm_rho_Ag_Ztrain = rdm_spearman(Z_pred, Z_train_mean)
    z_corr_Ag_Ztrain = z_corr_mean(Z_pred, Z_train_mean)

    # --- 3b. Mean train Z vs CVD Z ---
    cvd_metrics = {}
    for cvd_subj in CVD_SUBJECTS:
        Z_cvd = np.load(fold_dir / f'Z_cvd_{cvd_subj}.npy')  # (k, 8)
        rdm_rho_train_cvd = rdm_spearman(Z_train_mean, Z_cvd)
        rdm_rho_pred_cvd = rdm_spearman(Z_pred, Z_cvd)
        z_corr_train_cvd = z_corr_mean(Z_train_mean, Z_cvd)
        cvd_metrics[cvd_subj] = {
            'rdm_rho_trainmean_cvd': rdm_rho_train_cvd,
            'rdm_rho_pred_cvd': rdm_rho_pred_cvd,
            'z_corr_trainmean_cvd': z_corr_train_cvd,
        }

    # --- 4. Inter-run consistency in SRM space ---
    amp_held = load_amplitudes(baseline_dir, held_out, roi)
    W_held = np.load(fold_dir / 'W_heldout.npy')  # (V_s, k)
    run_rdm_rhos = []
    Z_runs = []
    for run in range(N_RUNS):
        Z_run = W_held.T @ amp_held[run].T  # (k, 8)
        Z_runs.append(Z_run)
    # Pairwise inter-run RDM consistency
    for i in range(N_RUNS):
        for j in range(i + 1, N_RUNS):
            rho = rdm_spearman(Z_runs[i], Z_runs[j])
            run_rdm_rhos.append(rho)

    # --- 5. A_g @ C(delta) sweep ---
    sweep_results = {}
    for cvd_subj in CVD_SUBJECTS:
        cvd_type = CVD_TYPE[cvd_subj]
        Z_cvd = np.load(fold_dir / f'Z_cvd_{cvd_subj}.npy')
        deltas = [0, 5, 10, 15, 20, 25, 30]
        sweep_rhos = []
        for delta in deltas:
            C_shifted = get_design_matrix('cone_1way', [delta],
                                          cvd_type=cvd_type)
            Z_shifted = A_g @ C_shifted.T  # (k, 8)
            rho = rdm_spearman(Z_shifted, Z_cvd)
            sweep_rhos.append(rho)
        sweep_results[cvd_subj] = {
            'deltas': deltas,
            'rdm_rhos': sweep_rhos,
        }

    return {
        'fold_idx': fold_idx,
        'held_out': held_out,
        # 1. A_g prediction quality
        'rdm_rho_pred_held': rdm_rho_pred_held,
        'z_corr_pred_held': z_corr_pred_held,
        'frob_pred_held': frob_pred_held,
        # 2. vs shared response
        'rdm_rho_pred_shared': rdm_rho_pred_shared,
        # 3. A_g vs mean train Z
        'rdm_rho_Ag_Ztrain': rdm_rho_Ag_Ztrain,
        'z_corr_Ag_Ztrain': z_corr_Ag_Ztrain,
        # 3b. Mean train Z vs CVD
        'cvd_metrics': cvd_metrics,
        # 4. Inter-run consistency
        'inter_run_rdm_rho_mean': float(np.mean(run_rdm_rhos)),
        'inter_run_rdm_rho_sd': float(np.std(run_rdm_rhos, ddof=1))
            if len(run_rdm_rhos) > 1 else 0.0,
        # 5. Cone-shift sweep
        'cone_shift_sweep': sweep_results,
    }


def aggregate_diagnostics(fold_diags):
    """Aggregate fold-level diagnostics into summary statistics."""
    keys = ['rdm_rho_pred_held', 'z_corr_pred_held', 'frob_pred_held',
            'rdm_rho_pred_shared', 'rdm_rho_Ag_Ztrain', 'z_corr_Ag_Ztrain',
            'inter_run_rdm_rho_mean']

    agg = {}
    for key in keys:
        values = [f[key] for f in fold_diags if key in f]
        if values:
            agg[key] = {
                'mean': float(np.mean(values)),
                'sd': float(np.std(values, ddof=1)) if len(values) > 1 else 0.0,
                'min': float(np.min(values)),
                'max': float(np.max(values)),
            }

    # CVD-specific aggregation
    for cvd_subj in CVD_SUBJECTS:
        cvd_keys = ['rdm_rho_trainmean_cvd', 'rdm_rho_pred_cvd',
                     'z_corr_trainmean_cvd']
        for ck in cvd_keys:
            values = [f['cvd_metrics'][cvd_subj][ck]
                      for f in fold_diags
                      if cvd_subj in f.get('cvd_metrics', {})]
            if values:
                agg[f'{ck}_sub{cvd_subj}'] = {
                    'mean': float(np.mean(values)),
                    'sd': float(np.std(values, ddof=1)) if len(values) > 1 else 0.0,
                }

    # Cone-shift sweep aggregation (mean across folds)
    for cvd_subj in CVD_SUBJECTS:
        sweeps = [f['cone_shift_sweep'][cvd_subj]
                  for f in fold_diags
                  if cvd_subj in f.get('cone_shift_sweep', {})]
        if sweeps:
            deltas = sweeps[0]['deltas']
            rho_matrix = np.array([s['rdm_rhos'] for s in sweeps])
            agg[f'sweep_sub{cvd_subj}'] = {
                'deltas': deltas,
                'rdm_rhos_mean': rho_matrix.mean(axis=0).tolist(),
                'rdm_rhos_sd': rho_matrix.std(axis=0, ddof=1).tolist()
                    if rho_matrix.shape[0] > 1
                    else [0.0] * len(deltas),
            }

    return agg


def main():
    parser = argparse.ArgumentParser(
        description='SRM prediction baseline diagnostic')
    parser.add_argument('--precomputed_dir', type=str,
                        default='results/precomputed')
    parser.add_argument('--output_dir', type=str,
                        default='results/v2/srm_baseline')
    parser.add_argument('--rois', nargs='+', default=['V1', 'V2', 'V4'])
    parser.add_argument('--baseline_dir', type=str,
                        default=str(LOCAL_BASELINE))
    args = parser.parse_args()

    print('=' * 60)
    print('SRM Prediction Baseline Diagnostic')
    print(f'ROIs: {args.rois}')
    print('=' * 60)

    for roi in args.rois:
        print(f'\n=== {roi} (k={K_VALUES[roi]}) ===')

        # Check if precomputed data exists
        roi_dir = Path(args.precomputed_dir) / roi
        if not roi_dir.exists():
            print(f'  WARNING: Precomputed data not found: {roi_dir}')
            print(f'  Run step0_precompute.py --rois {roi} first.')
            continue

        fold_diags = []
        for fold_idx in range(len(HC_SUBJECTS)):
            print(f'  Fold {fold_idx} (held-out: sub-{HC_SUBJECTS[fold_idx]})...')
            diag = diagnose_fold(
                fold_idx, roi, args.precomputed_dir, args.baseline_dir)
            fold_diags.append(diag)

            # Brief report
            print(f'    A_g pred: RDM r={diag["rdm_rho_pred_held"]:.3f}, '
                  f'Z corr={diag["z_corr_pred_held"]:.3f}')
            print(f'    Inter-run: mean RDM r='
                  f'{diag["inter_run_rdm_rho_mean"]:.3f}')
            for cvd_subj in CVD_SUBJECTS:
                cm = diag['cvd_metrics'][cvd_subj]
                print(f'    CVD sub-{cvd_subj}: '
                      f'train-CVD RDM r={cm["rdm_rho_trainmean_cvd"]:.3f}, '
                      f'pred-CVD RDM r={cm["rdm_rho_pred_cvd"]:.3f}')

        # Aggregate
        agg = aggregate_diagnostics(fold_diags)
        print(f'\n  --- Aggregated (7-fold) ---')
        for key in ['rdm_rho_pred_held', 'z_corr_pred_held',
                     'inter_run_rdm_rho_mean']:
            if key in agg:
                print(f'    {key}: {agg[key]["mean"]:.3f} '
                      f'(sd={agg[key]["sd"]:.3f})')

        # Print sweep summary
        for cvd_subj in CVD_SUBJECTS:
            sk = f'sweep_sub{cvd_subj}'
            if sk in agg:
                deltas = agg[sk]['deltas']
                rhos = agg[sk]['rdm_rhos_mean']
                best_idx = np.argmax(rhos)
                print(f'    Sweep sub-{cvd_subj}: '
                      f'best delta={deltas[best_idx]}nm, '
                      f'r={rhos[best_idx]:.3f} '
                      f'(delta=0: r={rhos[0]:.3f})')

        # Save
        out_dir = Path(args.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        result = {
            'roi': roi,
            'k': K_VALUES[roi],
            'timestamp': datetime.now().isoformat(),
            'n_folds': len(HC_SUBJECTS),
            'folds': fold_diags,
            'aggregate': agg,
        }
        out_path = out_dir / f'{roi}_baseline.json'
        with open(out_path, 'w') as f:
            json.dump(result, f, indent=2)
        print(f'  Saved: {out_path}')

    # Print cross-ROI comparison table
    print(f'\n{"="*60}')
    print('Cross-ROI Summary')
    print(f'{"="*60}')
    print(f'  {"ROI":>4} | {"Pred RDM r":>10} | {"Z corr":>8} | '
          f'{"Inter-run":>10} | {"HC-CVD RDM":>10}')
    print(f'  {"-"*4}-+-{"-"*10}-+-{"-"*8}-+-{"-"*10}-+-{"-"*10}')
    for roi in args.rois:
        out_path = Path(args.output_dir) / f'{roi}_baseline.json'
        if not out_path.exists():
            continue
        with open(out_path) as f:
            data = json.load(f)
        agg = data.get('aggregate', {})
        pred_r = agg.get('rdm_rho_pred_held', {}).get('mean', float('nan'))
        z_c = agg.get('z_corr_pred_held', {}).get('mean', float('nan'))
        ir = agg.get('inter_run_rdm_rho_mean', {}).get('mean', float('nan'))
        # Average across CVD subjects
        cvd_rhos = []
        for cvd_subj in CVD_SUBJECTS:
            k = f'rdm_rho_pred_cvd_sub{cvd_subj}'
            if k in agg:
                cvd_rhos.append(agg[k]['mean'])
        cvd_r = float(np.mean(cvd_rhos)) if cvd_rhos else float('nan')
        print(f'  {roi:>4} | {pred_r:>10.3f} | {z_c:>8.3f} | '
              f'{ir:>10.3f} | {cvd_r:>10.3f}')

    print('\nDiagnostic complete.')


if __name__ == '__main__':
    main()
