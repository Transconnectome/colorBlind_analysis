#!/usr/bin/env python3
"""
validate_smooth_tikh_artifact.py — Artifact validation for smooth_tikh.

Addresses two concerns about smooth_tikh (Section 9h):
  1. Section 18 artifact check: Does smooth_tikh sacrifice color-discriminative
     structure (rdm_pearson, id_accuracy) while inflating voxel_corr?
  2. Permutation test: Is smooth_tikh LOCO signal above the color-label-shuffle null?

Analysis 1 — RDM + Color Identification (per-subject):
  For each LOCO fold, collect predicted + actual patterns.
  Compute predicted RDM vs actual RDM (Spearman correlation).
  Compute id_accuracy: nearest-neighbor color identification.
  Compare ridge_gcv vs smooth_tikh on all metrics.

Analysis 2 — Permutation Test (HC group):
  10K permutations of color labels.
  Fixed smooth_tikh params (alpha=0.01, beta=100, the inner-LOCO selected mode).
  Null distribution of group-level LOCO voxel_corr.

Usage:
  # RDM + id analysis (per subject, can be array job)
  python validate_smooth_tikh_artifact.py --mode rdm --subject 01 \
      --baseline_dir /path/to/C010 --output_dir results/smooth_tikh_artifact

  # Permutation test (HC only, single job)
  python validate_smooth_tikh_artifact.py --mode perm --n_perms 10000 \
      --baseline_dir /path/to/C010 --output_dir results/smooth_tikh_artifact

  # Both analyses together (all subjects + permutation)
  python validate_smooth_tikh_artifact.py --mode both \
      --baseline_dir /path/to/C010 --output_dir results/smooth_tikh_artifact
"""

import argparse
import json
import time
import numpy as np
from pathlib import Path
from scipy import stats

import sys
sys.path.insert(0, str(Path(__file__).parent))

from utils_forward_model import (
    HC_SUBJECTS, CVD_SUBJECTS, ALL_SUBJECTS, ROIS,
    N_RUNS, N_COLORS, N_CHANNELS, HUE_ANGLES, ALPHA_GRID,
    load_amplitudes, create_basis_matrix,
    fit_W_ridge, fit_W_smooth_ridge, gcv_select_alpha,
    predict_patterns, voxel_pattern_correlation, explained_variance,
    compute_rdm, rdm_upper_tri,
    save_config, get_subject_group,
)

ROI_DISPLAY = {'V1': 'V1', 'V2': 'V2', 'V3': 'V3', 'V4': 'hV4'}

# Fixed smooth_tikh params (mode of inner-LOCO selection from Section 9h)
SMOOTH_TIKH_ALPHA = 0.01
SMOOTH_TIKH_BETA = 100.0


# ============================================================================
# LOCO with full pattern collection
# ============================================================================

def loco_with_patterns(amp, model='ridge_gcv', alpha=None, beta=None):
    """8-fold LOCO collecting predicted + actual patterns for RDM analysis.

    Args:
        amp: (6, 8, V_s)
        model: 'ridge_gcv' or 'smooth_tikh'
        alpha, beta: fixed params for smooth_tikh

    Returns:
        dict with:
          pred_patterns: (8, V_s) -- predicted pattern per held-out color
          actual_patterns: (8, V_s) -- actual run-averaged pattern per color
          per_fold: list of per-fold metrics
    """
    C = create_basis_matrix(HUE_ANGLES)
    V_s = amp.shape[2]

    pred_patterns = np.zeros((N_COLORS, V_s))
    actual_patterns = amp.mean(axis=0)  # (8, V_s) run-averaged
    fold_metrics = []

    for test_color in range(N_COLORS):
        train_colors = [c for c in range(N_COLORS) if c != test_color]
        C_train = C[train_colors]
        X_train = amp[:, train_colors, :].reshape(-1, V_s)
        C_train_tiled = np.tile(C_train, (N_RUNS, 1))

        if model == 'ridge_gcv':
            best_alpha, _ = gcv_select_alpha(C_train_tiled, X_train)
            W = fit_W_ridge(C_train_tiled, X_train, best_alpha)
        elif model == 'smooth_tikh':
            W = fit_W_smooth_ridge(C_train_tiled, X_train, alpha, beta)
        else:
            raise ValueError(f'Unknown model: {model}')

        # Predict held-out color
        C_test = C[test_color:test_color + 1]  # (1, K)
        Y_hat = predict_patterns(W, C_test)    # (1, V_s)
        X_mean = actual_patterns[test_color:test_color + 1]  # (1, V_s)

        pred_patterns[test_color] = Y_hat[0]

        # Per-fold voxel_corr
        r = voxel_pattern_correlation(Y_hat, X_mean)
        r2 = explained_variance(Y_hat, X_mean)

        fold_metrics.append({
            'test_color': int(test_color),
            'true_hue': int(HUE_ANGLES[test_color]),
            'voxel_corr': float(r[0]),
            'R2': float(r2[0]),
        })

    return {
        'pred_patterns': pred_patterns,
        'actual_patterns': actual_patterns,
        'per_fold': fold_metrics,
    }


# ============================================================================
# RDM + identification metrics
# ============================================================================

def compute_rdm_metrics(pred_patterns, actual_patterns):
    """Compute RDM correlation and identification accuracy.

    Args:
        pred_patterns: (8, V_s)
        actual_patterns: (8, V_s)

    Returns:
        dict with rdm_pearson, rdm_spearman, id_accuracy, id_correct
    """
    # RDM correlation
    rdm_pred = compute_rdm(pred_patterns, metric='correlation')
    rdm_actual = compute_rdm(actual_patterns, metric='correlation')

    tri_pred = rdm_upper_tri(rdm_pred)
    tri_actual = rdm_upper_tri(rdm_actual)

    # Handle NaN
    valid = np.isfinite(tri_pred) & np.isfinite(tri_actual)
    if valid.sum() < 3:
        rdm_pearson = np.nan
        rdm_spearman = np.nan
    else:
        rdm_pearson = float(np.corrcoef(tri_pred[valid], tri_actual[valid])[0, 1])
        rdm_spearman_val, _ = stats.spearmanr(tri_pred[valid], tri_actual[valid])
        rdm_spearman = float(rdm_spearman_val)

    # Identification accuracy: for each held-out color, is the nearest actual
    # pattern (by Pearson r) the correct one?
    n_correct = 0
    id_detail = []
    for c in range(N_COLORS):
        corrs = np.array([
            float(np.corrcoef(pred_patterns[c], actual_patterns[j])[0, 1])
            if np.std(pred_patterns[c]) > 0 and np.std(actual_patterns[j]) > 0
            else -1.0
            for j in range(N_COLORS)
        ])
        corrs = np.where(np.isfinite(corrs), corrs, -1.0)

        best_match = int(np.argmax(corrs))
        correct = best_match == c
        if correct:
            n_correct += 1

        id_detail.append({
            'test_color': c,
            'predicted_match': best_match,
            'correct': correct,
            'correlation_with_correct': float(corrs[c]),
            'correlation_with_match': float(corrs[best_match]),
        })

    id_accuracy = n_correct / N_COLORS

    return {
        'rdm_pearson': rdm_pearson if np.isfinite(rdm_pearson) else 0.0,
        'rdm_spearman': rdm_spearman if np.isfinite(rdm_spearman) else 0.0,
        'id_accuracy': float(id_accuracy),
        'id_n_correct': n_correct,
        'id_detail': id_detail,
    }


# ============================================================================
# Analysis 1: RDM + ID comparison (per subject)
# ============================================================================

def run_rdm_analysis(subject, baseline_dir, output_dir, rois):
    """Run LOCO with pattern collection for both models, compute RDM metrics."""
    subj = subject.zfill(2)
    group = get_subject_group(subj)

    print(f'Subject: sub-{subj} ({group})')
    results = {}

    for roi in rois:
        roi_disp = ROI_DISPLAY[roi]
        print(f'\n  {roi_disp}:')

        try:
            amp = load_amplitudes(baseline_dir, subj, roi)
        except FileNotFoundError as e:
            print(f'    ERROR: {e}')
            continue

        roi_result = {}

        for model_name, model_kwargs in [
            ('ridge_gcv', {}),
            ('smooth_tikh', {'alpha': SMOOTH_TIKH_ALPHA,
                             'beta': SMOOTH_TIKH_BETA}),
        ]:
            loco_out = loco_with_patterns(amp, model=model_name, **model_kwargs)
            rdm_metrics = compute_rdm_metrics(
                loco_out['pred_patterns'], loco_out['actual_patterns'])

            mean_vc = np.mean([f['voxel_corr'] for f in loco_out['per_fold']])
            mean_r2 = np.mean([f['R2'] for f in loco_out['per_fold']])

            roi_result[model_name] = {
                'mean_voxel_corr': float(mean_vc),
                'mean_R2': float(mean_r2),
                'rdm_pearson': rdm_metrics['rdm_pearson'],
                'rdm_spearman': rdm_metrics['rdm_spearman'],
                'id_accuracy': rdm_metrics['id_accuracy'],
                'id_n_correct': rdm_metrics['id_n_correct'],
                'id_detail': rdm_metrics['id_detail'],
                'per_fold': loco_out['per_fold'],
            }

            print(f'    {model_name:>12}: voxel_corr={mean_vc:+.4f}  '
                  f'rdm_r={rdm_metrics["rdm_pearson"]:.3f}  '
                  f'id_acc={rdm_metrics["id_accuracy"]:.3f} '
                  f'({rdm_metrics["id_n_correct"]}/8)')

        # Delta
        d_vc = (roi_result['smooth_tikh']['mean_voxel_corr']
                - roi_result['ridge_gcv']['mean_voxel_corr'])
        d_rdm = (roi_result['smooth_tikh']['rdm_pearson']
                 - roi_result['ridge_gcv']['rdm_pearson'])
        d_id = (roi_result['smooth_tikh']['id_accuracy']
                - roi_result['ridge_gcv']['id_accuracy'])

        print(f'    {"delta":>12}: voxel_corr={d_vc:+.4f}  '
              f'rdm_r={d_rdm:+.3f}  id_acc={d_id:+.3f}')

        # Artifact flag: voxel_corr improves but rdm or id degrades
        artifact = d_vc > 0 and (d_rdm < -0.05 or d_id < -0.05)
        if artifact:
            print(f'    *** ARTIFACT FLAG: voxel_corr up but discriminability down ***')

        roi_result['delta'] = {
            'voxel_corr': float(d_vc),
            'rdm_pearson': float(d_rdm),
            'id_accuracy': float(d_id),
            'artifact_flag': artifact,
        }

        results[roi] = roi_result

    # Save
    output = {
        'subject': subj,
        'subject_group': group,
        'smooth_tikh_params': {
            'alpha': SMOOTH_TIKH_ALPHA,
            'beta': SMOOTH_TIKH_BETA,
        },
    }
    output.update(results)

    out_path = Path(output_dir) / f'sub-{subj}_artifact.json'
    with open(out_path, 'w') as f:
        json.dump(output, f, indent=2)
    print(f'\nSaved: {out_path}')

    return results


# ============================================================================
# Analysis 2: Permutation test for smooth_tikh
# ============================================================================

def loco_smooth_tikh_fixed(amp, C_full, alpha, beta):
    """LOCO with fixed smooth_tikh params. Fast version for permutation."""
    V_s = amp.shape[2]
    fold_corrs = np.zeros(N_COLORS)

    for test_color in range(N_COLORS):
        train_colors = [c for c in range(N_COLORS) if c != test_color]
        C_train_row = C_full[train_colors]
        X_train = amp[:, train_colors, :].reshape(-1, V_s)
        C_train = np.tile(C_train_row, (N_RUNS, 1))

        W = fit_W_smooth_ridge(C_train, X_train, alpha, beta)

        C_test = C_full[test_color:test_color + 1]
        Y_hat = predict_patterns(W, C_test)
        X_test_mean = amp[:, test_color, :].mean(axis=0, keepdims=True)

        r = voxel_pattern_correlation(Y_hat, X_test_mean)
        fold_corrs[test_color] = r[0]

    return float(np.mean(fold_corrs))


def run_permutation_test(baseline_dir, output_dir, n_perms, seed, rois):
    """Permutation test for smooth_tikh with fixed hyperparameters."""
    rng = np.random.default_rng(seed)
    C_full = create_basis_matrix(HUE_ANGLES, N_CHANNELS, 'fe')

    results = {}

    for roi in rois:
        roi_disp = ROI_DISPLAY[roi]
        print(f'\n--- {roi_disp} ---')

        # Load all HC amplitudes
        hc_amps = {}
        for subj in HC_SUBJECTS:
            try:
                amp = load_amplitudes(baseline_dir, subj, roi)
                hc_amps[subj] = amp
            except FileNotFoundError:
                print(f'  Warning: missing sub-{subj} {roi}')

        available_subjects = list(hc_amps.keys())
        n_subj = len(available_subjects)
        print(f'  Loaded {n_subj} HC subjects')

        if n_subj == 0:
            continue

        # Observed value (smooth_tikh with fixed params)
        obs_subj_corrs = np.zeros(n_subj)
        for s_idx, subj in enumerate(available_subjects):
            obs_subj_corrs[s_idx] = loco_smooth_tikh_fixed(
                hc_amps[subj], C_full, SMOOTH_TIKH_ALPHA, SMOOTH_TIKH_BETA)
        observed = float(np.mean(obs_subj_corrs))
        print(f'  Observed HC mean LOCO_r (smooth_tikh): {observed:.4f}')
        print(f'  Per-subject: {[f"{v:.4f}" for v in obs_subj_corrs]}')

        # Permutation loop
        null_dist = np.zeros(n_perms)
        t0 = time.time()

        for perm_i in range(n_perms):
            subj_corrs = np.zeros(n_subj)
            for s_idx, subj in enumerate(available_subjects):
                amp = hc_amps[subj]
                perm = rng.permutation(N_COLORS)
                amp_shuffled = amp[:, perm, :]
                subj_corrs[s_idx] = loco_smooth_tikh_fixed(
                    amp_shuffled, C_full, SMOOTH_TIKH_ALPHA, SMOOTH_TIKH_BETA)
            null_dist[perm_i] = np.mean(subj_corrs)

            if (perm_i + 1) % 500 == 0:
                elapsed = time.time() - t0
                rate = (perm_i + 1) / elapsed
                eta = (n_perms - perm_i - 1) / rate
                print(f'  [{perm_i+1}/{n_perms}] '
                      f'null mean={np.mean(null_dist[:perm_i+1]):.4f}, '
                      f'{rate:.0f} perm/s, ETA {eta:.0f}s')

        elapsed = time.time() - t0
        p_perm = float(np.mean(null_dist >= observed))
        null_mean = float(np.mean(null_dist))
        null_sd = float(np.std(null_dist))
        null_ci = (float(np.percentile(null_dist, 2.5)),
                   float(np.percentile(null_dist, 97.5)))

        print(f'  p_perm = {p_perm:.4f} ({elapsed:.1f}s)')
        print(f'  Null: mean={null_mean:.4f}, SD={null_sd:.4f}, '
              f'95%CI=[{null_ci[0]:.4f}, {null_ci[1]:.4f}]')

        # Save null distribution
        np.save(Path(output_dir) / f'permutation_null_smooth_tikh_{roi_disp}.npy',
                null_dist)

        results[roi_disp] = {
            'model': 'smooth_tikh',
            'params': {'alpha': SMOOTH_TIKH_ALPHA, 'beta': SMOOTH_TIKH_BETA},
            'observed': observed,
            'per_subject_observed': {
                subj: float(obs_subj_corrs[i])
                for i, subj in enumerate(available_subjects)
            },
            'p_perm': p_perm,
            'n_perms': n_perms,
            'null_mean': null_mean,
            'null_sd': null_sd,
            'null_ci_95': null_ci,
            'n_subjects': n_subj,
            'elapsed_s': round(elapsed, 1),
        }

    return results


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Validate smooth_tikh: artifact check + permutation test')
    parser.add_argument('--mode', type=str, required=True,
                        choices=['rdm', 'perm', 'both'],
                        help='rdm: RDM/id analysis per subject; '
                             'perm: permutation test; both: run both')
    parser.add_argument('--subject', type=str, default=None,
                        help='Subject ID for rdm mode (e.g., 01)')
    parser.add_argument('--baseline_dir', type=str, required=True,
                        help='Path to full_dataset_C010')
    parser.add_argument('--output_dir', type=str, required=True,
                        help='Output directory')
    parser.add_argument('--rois', nargs='+', default=['V1', 'V2', 'V3', 'V4'])
    parser.add_argument('--n_perms', type=int, default=10000)
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print('=' * 60)
    print(f'Smooth_tikh Artifact Validation (mode={args.mode})')
    print(f'Params: alpha={SMOOTH_TIKH_ALPHA}, beta={SMOOTH_TIKH_BETA}')
    print('=' * 60)

    if args.mode in ('rdm', 'both'):
        if args.subject is not None:
            subjects = [args.subject.zfill(2)]
        else:
            subjects = ALL_SUBJECTS

        for subj in subjects:
            run_rdm_analysis(subj, args.baseline_dir, args.output_dir,
                             args.rois)

    if args.mode in ('perm', 'both'):
        perm_results = run_permutation_test(
            args.baseline_dir, output_dir, args.n_perms, args.seed, args.rois)

        perm_out = {
            'model': 'smooth_tikh',
            'params': {'alpha': SMOOTH_TIKH_ALPHA, 'beta': SMOOTH_TIKH_BETA},
            'n_perms': args.n_perms,
            'seed': args.seed,
            'results': perm_results,
        }
        with open(output_dir / 'permutation_test_smooth_tikh.json', 'w') as f:
            json.dump(perm_out, f, indent=2)
        print(f'\nSaved: {output_dir / "permutation_test_smooth_tikh.json"}')

        # Summary
        print('\n' + '=' * 60)
        print('PERMUTATION TEST SUMMARY (smooth_tikh)')
        print('=' * 60)
        for roi_disp, res in perm_results.items():
            sig = '*' if res['p_perm'] < 0.05 else ''
            print(f'  {roi_disp}: observed={res["observed"]:.4f}, '
                  f'p_perm={res["p_perm"]:.4f}{sig}, '
                  f'null_mean={res["null_mean"]:.4f}')

    save_config(output_dir,
                step='validate_smooth_tikh_artifact',
                mode=args.mode,
                smooth_tikh_alpha=SMOOTH_TIKH_ALPHA,
                smooth_tikh_beta=SMOOTH_TIKH_BETA,
                baseline_dir=str(args.baseline_dir),
                rois=args.rois)

    print('\nDone.')


if __name__ == '__main__':
    main()
