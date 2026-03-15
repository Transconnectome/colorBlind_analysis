#!/usr/bin/env python3
"""
validate_loso_zero_shot.py — Leave-One-Subject-Out Zero-Shot Validation.

Tests whether the group prior can predict a completely new subject's
voxel patterns without any of that subject's data in encoding or SRM.

For each ROI, for each HC subject i (7 folds):
  1. Refit SRM on HC \ {i} (6 subjects)  — no leakage
  2. Build A_g from those 6 subjects
  3. SVD-project held-out subject -> R_new
  4. W0 = (R_new @ A_g).T
  5. Direct evaluation on ALL 8 colors (no LOCO/LORO needed —
     W0 is frozen and uses zero held-out data)

Baseline: subject-only ridge_gcv with LOCO (needs CV because it
trains on the subject's own data).

Usage:
    mpirun -np 1 python scripts/validate_loso_zero_shot.py \
        --baseline_dir /path/to/full_dataset_C010 \
        --output_dir results/loso_zero_shot
"""

import argparse
import json
import time
import numpy as np
from pathlib import Path
from scipy.stats import spearmanr, ttest_rel

from brainiak.funcalign.srm import SRM

from utils_forward_model import (
    HC_SUBJECTS, CVD_SUBJECTS, ROIS, K_VALUES,
    N_RUNS, N_COLORS, N_CHANNELS, ALPHA_GRID,
    HUE_ANGLES,
    load_amplitudes, create_basis_matrix, create_basis_full,
    fit_W_ridge, gcv_select_alpha,
    predict_patterns, decode_hue, circular_distance,
    voxel_pattern_correlation, explained_variance,
    compute_rdm, rdm_upper_tri, project_new_subject,
    save_config, DEFAULT_BASELINE_DIR,
)

ROI_DISPLAY = {'V1': 'V1', 'V2': 'V2', 'V3': 'V3', 'V4': 'hV4'}
SRM_N_ITER = 10


# ============================================================================
# Step 1: Refit SRM on HC \ {held_out} — no leakage
# ============================================================================

def fit_srm_loo(roi, baseline_dir, train_subjects, k):
    """Fit SRM on a subset of HC subjects (LOO fold).

    Args:
        roi: ROI name
        baseline_dir: C010 data path
        train_subjects: list of subject IDs (excluding held-out)
        k: number of SRM features

    Returns:
        srm: fitted SRM model
        R_dict: {subj: (V_s, k)} projection matrices for train subjects
    """
    srm_input = []
    for subj in train_subjects:
        amp = load_amplitudes(baseline_dir, subj, roi)  # (6, 8, V_s)
        beta = amp.mean(axis=0)  # (8, V_s)
        srm_input.append(beta.T)  # BrainIAK expects (V_s, 8)

    srm = SRM(n_iter=SRM_N_ITER, features=k)
    srm.fit(srm_input)

    R_dict = {}
    for i, subj in enumerate(train_subjects):
        R_dict[subj] = srm.w_[i]  # (V_s, k)

    return srm, R_dict


def build_Ag_loo(roi, baseline_dir, train_subjects, R_dict,
                 n_channels=N_CHANNELS):
    """Build A_g from LOO HC subjects using their R_i from the refitted SRM.

    Args:
        roi: ROI name
        baseline_dir: C010 data path
        train_subjects: list of subject IDs
        R_dict: {subj: (V_s, k)} projection matrices
        n_channels: basis channels

    Returns:
        A_g: (k, K) group prior encoding matrix
    """
    C = create_basis_matrix(HUE_ANGLES, n_channels)  # (8, K)
    K = C.shape[1]
    CtC_inv = np.linalg.inv(C.T @ C)

    A_list = []
    for subj in train_subjects:
        R_i = R_dict[subj]  # (V_s, k)
        amp = load_amplitudes(baseline_dir, subj, roi)  # (6, 8, V_s)
        beta = amp.mean(axis=0)  # (8, V_s)
        Z_i = R_i.T @ beta.T  # (k, 8)
        A_i = Z_i @ C @ CtC_inv  # (k, K)
        A_list.append(A_i)

    A_g = np.mean(A_list, axis=0)  # (k, K)
    return A_g


# ============================================================================
# Step 2: Direct zero-shot evaluation (frozen W0, no CV needed)
# ============================================================================

def evaluate_zero_shot(amp, W0):
    """Evaluate frozen W0 directly on all 8 colors.

    W0 uses zero data from this subject -> no CV needed.

    Args:
        amp: (6, 8, V_s) amplitudes
        W0: (K, V_s) frozen zero-shot weights

    Returns:
        dict with voxel_corr, R2, rdm_corr, mae metrics
    """
    C = create_basis_matrix(HUE_ANGLES)  # (8, K)
    basis_full = create_basis_full()  # (360, K)

    # Predicted patterns for all 8 colors
    Y_hat = predict_patterns(W0, C)  # (8, V_s)

    # Actual run-averaged patterns
    Y_real = amp.mean(axis=0)  # (8, V_s)

    # 1. Voxel pattern correlation per color (8 values)
    r_per_color = voxel_pattern_correlation(Y_hat, Y_real)  # (8,)

    # 2. R^2 per color
    r2_per_color = explained_variance(Y_hat, Y_real)  # (8,)

    # 3. RDM correlation (predicted vs actual structure)
    rdm_pred = compute_rdm(Y_hat)
    rdm_real = compute_rdm(Y_real)
    rdm_r, rdm_p = spearmanr(rdm_upper_tri(rdm_pred), rdm_upper_tri(rdm_real))
    if not np.isfinite(rdm_r):
        rdm_r = 0.0
        rdm_p = 1.0

    # 4. Hue decoding MAE (per run)
    run_maes = []
    for r in range(N_RUNS):
        pred_hues = decode_hue(W0, basis_full, amp[r])  # (8,)
        errors = circular_distance(HUE_ANGLES, pred_hues)
        run_maes.append(float(np.nanmean(errors)))
    mean_mae = float(np.mean(run_maes))

    # Per-color detail
    per_color = []
    for c_idx in range(N_COLORS):
        per_color.append({
            'color': int(c_idx),
            'hue': int(HUE_ANGLES[c_idx]),
            'voxel_corr': float(r_per_color[c_idx]),
            'R2': float(r2_per_color[c_idx]),
        })

    return {
        'mean_voxel_corr': float(np.mean(r_per_color)),
        'mean_R2': float(np.mean(r2_per_color)),
        'rdm_corr': float(rdm_r),
        'rdm_p': float(rdm_p),
        'mean_mae': mean_mae,
        'run_maes': run_maes,
        'per_color': per_color,
    }


# ============================================================================
# Step 3: Subject-only baseline (ridge_gcv LOCO — needs CV)
# ============================================================================

def evaluate_ridge_gcv_loco(amp):
    """Subject-only ridge_gcv LOCO baseline.

    Uses the subject's own data to train -> needs LOCO cross-validation.

    Args:
        amp: (6, 8, V_s) amplitudes

    Returns:
        dict with mean_voxel_corr, mean_mae, folds
    """
    C_full = create_basis_matrix(HUE_ANGLES)  # (8, K)
    basis_full = create_basis_full()  # (360, K)
    V_s = amp.shape[2]
    folds = []

    for test_color in range(N_COLORS):
        train_colors = [c for c in range(N_COLORS) if c != test_color]
        C_train_row = C_full[train_colors]  # (7, K)

        X_train = amp[:, train_colors, :].reshape(-1, V_s)  # (42, V_s)
        C_train = np.tile(C_train_row, (N_RUNS, 1))  # (42, K)

        best_alpha, _ = gcv_select_alpha(C_train, X_train, ALPHA_GRID)
        W = fit_W_ridge(C_train, X_train, best_alpha)  # (K, V_s)

        C_test = C_full[test_color:test_color + 1]  # (1, K)
        Y_hat = predict_patterns(W, C_test)  # (1, V_s)
        X_test = amp[:, test_color, :]  # (6, V_s)
        X_mean = X_test.mean(axis=0, keepdims=True)  # (1, V_s)

        r = voxel_pattern_correlation(Y_hat, X_mean)
        r2 = explained_variance(Y_hat, X_mean)

        pred_hues = decode_hue(W, basis_full, X_test)
        true_hue = HUE_ANGLES[test_color]
        errors = circular_distance(np.full(len(pred_hues), true_hue), pred_hues)

        folds.append({
            'test_color': int(test_color),
            'true_hue': int(true_hue),
            'voxel_corr': float(r[0]),
            'R2': float(r2[0]),
            'mae': float(np.nanmean(errors)),
            'alpha': float(best_alpha),
        })

    return {
        'mean_voxel_corr': float(np.mean([f['voxel_corr'] for f in folds])),
        'mean_R2': float(np.mean([f['R2'] for f in folds])),
        'mean_mae': float(np.mean([f['mae'] for f in folds])),
        'folds': folds,
    }


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='LOSO Zero-Shot Validation (SRM refit, no leakage)')
    parser.add_argument('--baseline_dir', type=str,
                        default=str(DEFAULT_BASELINE_DIR))
    parser.add_argument('--output_dir', type=str,
                        default='results/loso_zero_shot')
    parser.add_argument('--rois', nargs='+', default=ROIS)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print('=' * 60)
    print('LOSO Zero-Shot Validation (SRM refit per fold)')
    print(f'ROIs: {args.rois}')
    print(f'Baseline dir: {args.baseline_dir}')
    print(f'Output dir: {args.output_dir}')
    print(f'HC subjects: {HC_SUBJECTS} (7 LOSO folds)')
    print(f'CVD subjects: {CVD_SUBJECTS}')
    print('=' * 60)
    print('\nApproach: Refit SRM on HC\\{i} per fold (no leakage).')
    print('W0 is frozen -> direct evaluation (no LOCO/LORO needed).')

    all_results = {}
    t_start = time.time()

    for roi in args.rois:
        roi_disp = ROI_DISPLAY[roi]
        k = K_VALUES[roi]
        print(f'\n{"="*50} {roi_disp} (k={k}) {"="*50}')

        # Pre-load all amplitudes
        amp_cache = {}
        for subj in HC_SUBJECTS + CVD_SUBJECTS:
            try:
                amp_cache[subj] = load_amplitudes(args.baseline_dir, subj, roi)
            except FileNotFoundError:
                print(f'  WARNING: missing sub-{subj} {roi}, skipping')

        # ---- HC LOSO ----
        hc_results = {}
        cached_srm_Ag = []  # [(srm, A_g)] for CVD reuse

        for held_out in HC_SUBJECTS:
            if held_out not in amp_cache:
                continue

            train_subjects = [s for s in HC_SUBJECTS if s != held_out]
            print(f'\n  LOSO fold: held-out=sub-{held_out}, '
                  f'train={[f"sub-{s}" for s in train_subjects]}')

            t0 = time.time()

            # 1. Refit SRM on 6 subjects
            srm, R_dict = fit_srm_loo(roi, args.baseline_dir, train_subjects, k)

            # 2. Build A_g from those 6
            A_g = build_Ag_loo(roi, args.baseline_dir, train_subjects, R_dict)
            cached_srm_Ag.append((srm, A_g))

            # 3. Project held-out subject via SVD
            amp_ho = amp_cache[held_out]
            beta_ho = amp_ho.mean(axis=0)  # (8, V_s)
            R_new = project_new_subject(srm, beta_ho.T)  # (V_s, k)

            # 4. W0 = (R_new @ A_g).T
            W0 = (R_new @ A_g).T  # (K, V_s)

            # 5. Direct evaluation (frozen W0, no CV needed)
            zs = evaluate_zero_shot(amp_ho, W0)

            # 6. Ridge-GCV LOCO baseline (subject-own, needs CV)
            bl = evaluate_ridge_gcv_loco(amp_ho)

            elapsed = time.time() - t0
            print(f'    ZS direct: voxel_corr={zs["mean_voxel_corr"]:.4f}  '
                  f'R2={zs["mean_R2"]:.4f}  rdm_r={zs["rdm_corr"]:.4f}  '
                  f'MAE={zs["mean_mae"]:.1f}')
            print(f'    BL LOCO:   voxel_corr={bl["mean_voxel_corr"]:.4f}  '
                  f'MAE={bl["mean_mae"]:.1f}')
            print(f'    ({elapsed:.1f}s)')

            hc_results[held_out] = {
                'zero_shot': zs,
                'ridge_gcv_loco': bl,
            }

        # ---- HC summary stats ----
        zs_vals = [hc_results[s]['zero_shot']['mean_voxel_corr']
                   for s in HC_SUBJECTS if s in hc_results]
        bl_vals = [hc_results[s]['ridge_gcv_loco']['mean_voxel_corr']
                   for s in HC_SUBJECTS if s in hc_results]
        zs_rdm = [hc_results[s]['zero_shot']['rdm_corr']
                  for s in HC_SUBJECTS if s in hc_results]
        zs_mae = [hc_results[s]['zero_shot']['mean_mae']
                  for s in HC_SUBJECTS if s in hc_results]

        n_hc = len(zs_vals)
        if n_hc >= 2:
            t_vc, p_vc = ttest_rel(zs_vals, bl_vals)
        else:
            t_vc, p_vc = np.nan, np.nan

        print(f'\n  HC Summary (n={n_hc}):')
        print(f'    ZS voxel_corr: {np.mean(zs_vals):.4f} +/- '
              f'{np.std(zs_vals, ddof=1):.4f}')
        print(f'    BL voxel_corr: {np.mean(bl_vals):.4f} +/- '
              f'{np.std(bl_vals, ddof=1):.4f}')
        print(f'    Paired t: t={t_vc:.3f}, p={p_vc:.4f}')
        print(f'    ZS rdm_corr:   {np.mean(zs_rdm):.4f} +/- '
              f'{np.std(zs_rdm, ddof=1):.4f}')
        print(f'    ZS MAE:        {np.mean(zs_mae):.1f} +/- '
              f'{np.std(zs_mae, ddof=1):.1f}')

        # ---- CVD evaluation ----
        cvd_results = {}
        for cvd_subj in CVD_SUBJECTS:
            if cvd_subj not in amp_cache:
                continue

            print(f'\n  CVD sub-{cvd_subj}: evaluating across '
                  f'{len(cached_srm_Ag)} LOO priors')
            amp_cvd = amp_cache[cvd_subj]
            beta_cvd = amp_cvd.mean(axis=0)  # (8, V_s)

            per_prior = []
            for fold_idx, (srm_loo, A_g_loo) in enumerate(cached_srm_Ag):
                R_cvd = project_new_subject(srm_loo, beta_cvd.T)
                W0_cvd = (R_cvd @ A_g_loo).T

                zs_cvd = evaluate_zero_shot(amp_cvd, W0_cvd)
                per_prior.append({
                    'fold': fold_idx,
                    'voxel_corr': zs_cvd['mean_voxel_corr'],
                    'R2': zs_cvd['mean_R2'],
                    'rdm_corr': zs_cvd['rdm_corr'],
                    'mae': zs_cvd['mean_mae'],
                })

            vc_vals = [pp['voxel_corr'] for pp in per_prior]
            vc_mean = float(np.mean(vc_vals))
            vc_sd = float(np.std(vc_vals, ddof=1)) if len(vc_vals) > 1 else 0.0

            print(f'    voxel_corr: {vc_mean:.4f} +/- {vc_sd:.4f}')

            # CVD ridge_gcv LOCO baseline
            bl_cvd = evaluate_ridge_gcv_loco(amp_cvd)

            cvd_results[cvd_subj] = {
                'voxel_corr_mean': vc_mean,
                'voxel_corr_sd': vc_sd,
                'per_prior': per_prior,
                'ridge_gcv_loco': bl_cvd,
            }

        # ---- Assemble ROI results ----
        all_results[roi_disp] = {
            'k': k,
            'hc': hc_results,
            'hc_stats': {
                'zs_voxel_corr_mean': float(np.mean(zs_vals)),
                'zs_voxel_corr_sd': float(np.std(zs_vals, ddof=1)) if n_hc > 1 else 0.0,
                'zs_rdm_corr_mean': float(np.mean(zs_rdm)),
                'zs_rdm_corr_sd': float(np.std(zs_rdm, ddof=1)) if n_hc > 1 else 0.0,
                'zs_mae_mean': float(np.mean(zs_mae)),
                'zs_mae_sd': float(np.std(zs_mae, ddof=1)) if n_hc > 1 else 0.0,
                'bl_voxel_corr_mean': float(np.mean(bl_vals)),
                'bl_voxel_corr_sd': float(np.std(bl_vals, ddof=1)) if n_hc > 1 else 0.0,
                'paired_t': float(t_vc),
                'paired_p': float(p_vc),
                'n': n_hc,
            },
            'cvd': cvd_results,
        }

    elapsed_total = time.time() - t_start

    # ============================================================
    # Save results
    # ============================================================
    output = {
        'description': 'LOSO zero-shot validation (SRM refit per fold, '
                       'direct eval — no LOCO/LORO on ZS)',
        'elapsed_s': round(elapsed_total, 1),
        'results': all_results,
    }
    out_path = output_dir / 'loso_zero_shot.json'
    with open(out_path, 'w') as f:
        json.dump(output, f, indent=2)
    print(f'\nSaved: {out_path}')

    save_config(output_dir,
                step='validate_loso_zero_shot',
                rois=args.rois,
                baseline_dir=args.baseline_dir,
                k_values={r: K_VALUES[r] for r in args.rois},
                hc_subjects=HC_SUBJECTS,
                cvd_subjects=CVD_SUBJECTS,
                srm_n_iter=SRM_N_ITER,
                n_channels=N_CHANNELS,
                note='SRM refitted per fold (no leakage); '
                     'W0 frozen -> direct eval on all 8 colors')

    # ============================================================
    # Final summary
    # ============================================================
    print('\n' + '=' * 60)
    print('SUMMARY')
    print('=' * 60)

    print(f'\n  {"ROI":>6s}  {"ZS_vc":>8s}  {"BL_vc":>8s}  '
          f'{"t":>7s}  {"p":>7s}  {"ZS_rdm":>8s}  {"ZS_MAE":>8s}')
    for roi in args.rois:
        rd = ROI_DISPLAY[roi]
        if rd not in all_results:
            continue
        s = all_results[rd]['hc_stats']
        sig = '*' if s['paired_p'] < 0.05 else ''
        print(f'  {rd:>6s}  {s["zs_voxel_corr_mean"]:>8.4f}  '
              f'{s["bl_voxel_corr_mean"]:>8.4f}  '
              f'{s["paired_t"]:>7.3f}  {s["paired_p"]:>6.4f}{sig}  '
              f'{s["zs_rdm_corr_mean"]:>8.4f}  '
              f'{s["zs_mae_mean"]:>7.1f}')

    print('\n  CVD (mean +/- SD across LOO priors):')
    for roi in args.rois:
        rd = ROI_DISPLAY[roi]
        if rd not in all_results:
            continue
        for cvd_subj, cr in all_results[rd].get('cvd', {}).items():
            bl_vc = cr['ridge_gcv_loco']['mean_voxel_corr']
            print(f'  {rd:>6s} sub-{cvd_subj}: '
                  f'ZS={cr["voxel_corr_mean"]:.4f}+/-{cr["voxel_corr_sd"]:.4f}  '
                  f'BL={bl_vc:.4f}')

    print(f'\nTotal time: {elapsed_total:.1f}s')
    print('Done.')


if __name__ == '__main__':
    main()
