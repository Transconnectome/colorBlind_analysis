#!/usr/bin/env python3
"""
cone_shift_loco.py — Cone-shift-informed CVD prediction evaluation.

Uses HC group prior (W_HC) + θ_equiv (from cone_shift_validation.py) to
predict CVD voxel patterns for all 8 colors.

Concept:
  Cone shift hypothesis: CVD perceives color θ as if it were θ_equiv.
  → W_HC @ C(θ_equiv) should predict Y_CVD(θ) better than W_HC @ C(θ).

  For each color i:
    Baseline:   Y_pred = W_HC @ C(θ_original[i])
    Corrected:  Y_pred = W_HC @ C(θ_equiv[i])
    compare both Y_pred with CVD actual response Y_CVD[i]

Runs on server (needs C010 data) via sbatch.
Requires: cone_shift_validation_results.json (from local cone_shift_validation.py).

Usage:
    mpirun -np 1 python scripts/cone_shift_loco.py \
        --baseline_dir /scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010 \
        --validation_json results/cone_shift/cone_shift_validation_results.json \
        --output_dir results/cone_shift_loco
"""

import argparse
import json
import time
import numpy as np
from pathlib import Path
from scipy.stats import spearmanr, wilcoxon

from brainiak.funcalign.srm import SRM

from utils_forward_model import (
    HC_SUBJECTS, CVD_SUBJECTS, K_VALUES,
    N_RUNS, N_COLORS, N_CHANNELS,
    HUE_ANGLES,
    load_amplitudes, create_basis_matrix, create_basis_full,
    predict_patterns,
    voxel_pattern_correlation, explained_variance,
    project_new_subject,
    DEFAULT_BASELINE_DIR,
)

ROI_DISPLAY = {'V1': 'V1', 'V2': 'V2', 'V3': 'V3', 'V4': 'hV4'}
SRM_N_ITER = 10
COLOR_NAMES = ['red', 'orange', 'yellow', 'green',
               'cyan', 'blue', 'purple', 'magenta']


# ============================================================================
# SRM + Group Prior (reused from validate_loso_zero_shot.py)
# ============================================================================

def fit_srm_all_hc(roi, baseline_dir, k):
    """Fit SRM on all HC subjects."""
    srm_input = []
    for subj in HC_SUBJECTS:
        amp = load_amplitudes(baseline_dir, subj, roi)  # (6, 8, V_s)
        beta = amp.mean(axis=0)  # (8, V_s)
        srm_input.append(beta.T)  # (V_s, 8)

    srm = SRM(n_iter=SRM_N_ITER, features=k)
    srm.fit(srm_input)

    R_dict = {}
    for i, subj in enumerate(HC_SUBJECTS):
        R_dict[subj] = srm.w_[i]  # (V_s, k)

    return srm, R_dict


def build_Ag_all_hc(roi, baseline_dir, R_dict, n_channels=N_CHANNELS):
    """Build group prior A_g from all HC subjects."""
    C = create_basis_matrix(HUE_ANGLES, n_channels)  # (8, K)
    CtC_inv = np.linalg.inv(C.T @ C)

    A_list = []
    for subj in HC_SUBJECTS:
        R_i = R_dict[subj]
        amp = load_amplitudes(baseline_dir, subj, roi)
        beta = amp.mean(axis=0)  # (8, V_s)
        Z_i = R_i.T @ beta.T  # (k, 8)
        A_i = Z_i @ C @ CtC_inv  # (k, K)
        A_list.append(A_i)

    return np.mean(A_list, axis=0)  # (k, K)


def build_W_HC_for_cvd(roi, baseline_dir, srm, A_g, cvd_subj):
    """Build W_HC (group prior) for a CVD subject."""
    amp = load_amplitudes(baseline_dir, cvd_subj, roi)
    beta = amp.mean(axis=0)  # (8, V_s)
    R_new = project_new_subject(srm, beta.T)  # (V_s, k)
    W_HC = (R_new @ A_g).T  # (K, V_s)
    return W_HC


# ============================================================================
# Evaluation: Baseline vs Cone-Shift Corrected
# ============================================================================

def evaluate_prediction(amp, W_HC, hue_angles, n_channels=N_CHANNELS):
    """Predict CVD voxel patterns using W_HC @ C(angles).

    For each color:
      Y_pred = W_HC @ C(angle)
      compare with Y_CVD (run-averaged actual response)

    Args:
        amp: (6, 8, V_s) CVD subject's amplitudes
        W_HC: (K, V_s) HC group prior weights
        hue_angles: (8,) hue angles in degrees to use for prediction
        n_channels: basis channels

    Returns:
        dict with per-color results
    """
    basis_full = create_basis_full(n_channels)  # (360, K)
    folds = []

    for color_idx in range(N_COLORS):
        theta = float(hue_angles[color_idx])
        theta_int = int(round(theta)) % 360
        C_test = basis_full[theta_int:theta_int + 1]  # (1, K)

        # Predict voxel pattern
        Y_hat = predict_patterns(W_HC, C_test)  # (1, V_s)

        # Actual CVD response (run-averaged)
        X_actual = amp[:, color_idx, :].mean(axis=0, keepdims=True)  # (1, V_s)

        # Metrics
        r = voxel_pattern_correlation(Y_hat, X_actual)
        r2 = explained_variance(Y_hat, X_actual)

        # Per-run voxel correlations (for confidence)
        run_corrs = []
        for run in range(N_RUNS):
            X_run = amp[run, color_idx, :].reshape(1, -1)
            r_run = voxel_pattern_correlation(Y_hat, X_run)
            run_corrs.append(float(r_run[0]))

        folds.append({
            'color_idx': int(color_idx),
            'color_name': COLOR_NAMES[color_idx],
            'hue_used': float(theta),
            'voxel_corr': float(r[0]),
            'R2': float(r2[0]),
            'run_corrs': run_corrs,
            'run_corr_mean': float(np.mean(run_corrs)),
            'run_corr_std': float(np.std(run_corrs)),
        })

    return {
        'mean_voxel_corr': float(np.mean([f['voxel_corr'] for f in folds])),
        'mean_R2': float(np.mean([f['R2'] for f in folds])),
        'folds': folds,
    }


# ============================================================================
# HC Baseline: Same evaluation for HC subjects (reference)
# ============================================================================

def evaluate_hc_baseline(roi, baseline_dir, srm, R_dict, A_g,
                         n_channels=N_CHANNELS):
    """Evaluate W_HC prediction quality for each HC subject.

    NOTE: This is an OPTIMISTIC upper bound — subject i's data was used
    in both SRM fitting and A_g construction (circular). The purpose is
    to provide a rough HC reference range, not a formal benchmark.
    CVD comparisons (baseline vs corrected) are valid because both
    use the same W_HC derived independently of CVD data.
    """
    hc_corrs = []
    for subj in HC_SUBJECTS:
        amp = load_amplitudes(baseline_dir, subj, roi)
        beta = amp.mean(axis=0)  # (8, V_s)
        R_i = R_dict[subj]
        W_i = (R_i @ A_g).T  # (K, V_s) — using full A_g (slight optimism)

        result = evaluate_prediction(amp, W_i, HUE_ANGLES, n_channels)
        hc_corrs.append(result['mean_voxel_corr'])

    return {
        'mean': float(np.mean(hc_corrs)),
        'std': float(np.std(hc_corrs)),
        'per_subject': {f'sub-{s}': float(c) for s, c in
                        zip(HC_SUBJECTS, hc_corrs)},
    }


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Cone-shift-informed CVD prediction evaluation'
    )
    parser.add_argument('--baseline_dir', type=str,
                        default=str(DEFAULT_BASELINE_DIR))
    parser.add_argument('--validation_json', type=str,
                        default='results/cone_shift/cone_shift_validation_results.json',
                        help='Path to cone_shift_validation_results.json')
    parser.add_argument('--output_dir', type=str,
                        default='results/cone_shift_loco')
    parser.add_argument('--roi', type=str, default='V4',
                        help='ROI to evaluate (V4 = hV4)')
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load validation results (θ_equiv)
    print("[1] Loading cone shift validation results (θ_equiv)...")
    with open(args.validation_json) as f:
        validation = json.load(f)
    for subj_key in validation:
        te = validation[subj_key]['theta_equiv_deg']
        print(f"    {subj_key}: θ_equiv = {[f'{a:.0f}' for a in te]}")

    roi = args.roi
    k = K_VALUES[roi]
    roi_disp = ROI_DISPLAY[roi]

    print(f"\n[2] Fitting SRM on all HC subjects (roi={roi_disp}, k={k})...")
    t0 = time.time()
    srm, R_dict = fit_srm_all_hc(roi, args.baseline_dir, k)
    print(f"    SRM fit done in {time.time()-t0:.1f}s")

    print("[3] Building group prior A_g...")
    A_g = build_Ag_all_hc(roi, args.baseline_dir, R_dict)
    print(f"    A_g shape: {A_g.shape}")

    # HC reference
    print("\n[4] HC baseline (reference range)...")
    hc_ref = evaluate_hc_baseline(roi, args.baseline_dir, srm, R_dict, A_g)
    print(f"    HC mean voxel_corr = {hc_ref['mean']:.4f} ± {hc_ref['std']:.4f}")
    for s, c in hc_ref['per_subject'].items():
        print(f"      {s}: {c:.4f}")

    all_results = {'hc_reference': hc_ref}

    for cvd_subj in CVD_SUBJECTS:
        subj_key = f'sub-{cvd_subj}'
        print(f"\n{'='*60}")
        print(f"[5] {subj_key} — {roi_disp}")

        # Build W_HC for this CVD subject
        W_HC = build_W_HC_for_cvd(roi, args.baseline_dir, srm, A_g, cvd_subj)
        print(f"    W_HC shape: {W_HC.shape}")

        # Load CVD amplitudes
        amp = load_amplitudes(args.baseline_dir, cvd_subj, roi)
        print(f"    Amplitudes shape: {amp.shape}")

        # Baseline: W_HC @ C(θ_original) vs Y_CVD
        print("    [a] Baseline (original CIELab angles)...")
        baseline = evaluate_prediction(amp, W_HC, HUE_ANGLES)
        print(f"        mean voxel_corr = {baseline['mean_voxel_corr']:.4f}")

        # Corrected: W_HC @ C(θ_equiv) vs Y_CVD
        if subj_key in validation:
            theta_equiv = np.array(validation[subj_key]['theta_equiv_deg'])
            cvd_type = validation[subj_key]['cvd_type']
            dl = validation[subj_key]['delta_lambda_nm']

            print(f"    [b] Cone-shift corrected (θ_equiv, Δλ={dl}nm, {cvd_type})...")
            corrected = evaluate_prediction(amp, W_HC, theta_equiv)
            print(f"        mean voxel_corr = {corrected['mean_voxel_corr']:.4f}")

            improvement = corrected['mean_voxel_corr'] - baseline['mean_voxel_corr']
            print(f"        Improvement: {improvement:+.4f}")

            # Per-color comparison
            print(f"\n        {'Color':>8s}  {'Baseline':>8s}  {'Corrected':>9s}  {'Δ':>8s}  "
                  f"{'θ_orig':>7s}  {'θ_equiv':>7s}")
            per_color_imp = []
            for i in range(N_COLORS):
                b_corr = baseline['folds'][i]['voxel_corr']
                c_corr = corrected['folds'][i]['voxel_corr']
                delta = c_corr - b_corr
                per_color_imp.append(delta)
                marker = '***' if delta > 0.05 else ('*' if delta > 0.01 else '')
                print(f"        {COLOR_NAMES[i]:>8s}  {b_corr:+8.4f}  {c_corr:+9.4f}  "
                      f"{delta:+8.4f}  {HUE_ANGLES[i]:7.0f}°  {theta_equiv[i]:7.0f}° {marker}")

            # Wilcoxon signed-rank test on per-color improvement
            n_improved = sum(1 for d in per_color_imp if d > 0)
            if np.any(np.array(per_color_imp) != 0):
                try:
                    w_stat, w_p = wilcoxon(per_color_imp)
                    print(f"\n        Wilcoxon: W={w_stat:.1f}, p={w_p:.3f}")
                except ValueError:
                    w_stat, w_p = float('nan'), float('nan')
            else:
                w_stat, w_p = float('nan'), float('nan')
            print(f"        Improved: {n_improved}/8 colors")

            all_results[subj_key] = {
                'roi': roi_disp,
                'cvd_type': cvd_type,
                'delta_lambda_nm': dl,
                'theta_equiv_deg': theta_equiv.tolist(),
                'baseline': baseline,
                'corrected': corrected,
                'improvement': float(improvement),
                'per_color_improvement': per_color_imp,
                'n_improved': n_improved,
                'wilcoxon_W': float(w_stat) if np.isfinite(w_stat) else None,
                'wilcoxon_p': float(w_p) if np.isfinite(w_p) else None,
            }
        else:
            print(f"    [b] No validation data for {subj_key}")
            all_results[subj_key] = {
                'roi': roi_disp,
                'baseline': baseline,
                'corrected': None,
                'improvement': None,
            }

    # Save results
    out_path = output_dir / 'cone_shift_prediction_results.json'
    with open(out_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f"\n[6] Results saved to {out_path}")

    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"  HC reference: {hc_ref['mean']:.4f} ± {hc_ref['std']:.4f}")
    print()
    for subj_key in [f'sub-{s}' for s in CVD_SUBJECTS]:
        res = all_results[subj_key]
        b_corr = res['baseline']['mean_voxel_corr']
        if res.get('corrected') is not None:
            c_corr = res['corrected']['mean_voxel_corr']
            imp = res['improvement']
            n_imp = res['n_improved']
            print(f"  {subj_key} ({res['cvd_type']}, Δλ={res['delta_lambda_nm']}nm):")
            print(f"    baseline={b_corr:.4f} → corrected={c_corr:.4f} "
                  f"(Δ={imp:+.4f}, {n_imp}/8 improved)")
        else:
            print(f"  {subj_key}: baseline={b_corr:.4f} (no correction)")

    # Save config
    config = {
        'date': time.strftime('%Y-%m-%d %H:%M'),
        'script': 'cone_shift_loco.py',
        'method': 'theta_equiv_direct (not Fourier T_psi)',
        'parameters': {
            'baseline_dir': str(args.baseline_dir),
            'validation_json': str(args.validation_json),
            'roi': roi,
            'srm_n_iter': SRM_N_ITER,
            'n_channels': N_CHANNELS,
        },
    }
    config_path = output_dir / 'config.json'
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)


if __name__ == '__main__':
    main()
