#!/usr/bin/env python3
"""Quick test: compare LOCO scores with per-run centering vs uncentered."""
import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
import numpy as np
from utils_forward_model import (
    load_amplitudes, create_basis_matrix, HUE_ANGLES, N_CHANNELS, N_RUNS, N_COLORS,
    fit_W_ridge, fit_W_smooth_ridge, gcv_select_alpha, ALPHA_GRID,
    predict_patterns, voxel_pattern_correlation,
)

baseline_dir = '../../../analysis/phase1_preprocess_decoding/results/full_dataset_C010'
C_full = create_basis_matrix(HUE_ANGLES, N_CHANNELS, 'fe')


def loco_single(amp, model_name, alpha_val=None, beta_val=None):
    """Standard LOCO on raw amplitudes."""
    V_s = amp.shape[2]
    fold_corrs = np.zeros(N_COLORS)
    for tc in range(N_COLORS):
        train_colors = [c for c in range(N_COLORS) if c != tc]
        X_train = amp[:, train_colors, :].reshape(-1, V_s)
        C_train = np.tile(C_full[train_colors], (N_RUNS, 1))

        if model_name == 'ridge_gcv':
            ba, _ = gcv_select_alpha(C_train, X_train, ALPHA_GRID)
            W = fit_W_ridge(C_train, X_train, ba)
        else:
            W = fit_W_smooth_ridge(C_train, X_train, alpha_val, beta_val)

        Y_hat = predict_patterns(W, C_full[tc:tc + 1])
        X_test = amp[:, tc, :].mean(axis=0, keepdims=True)
        r = voxel_pattern_correlation(Y_hat, X_test)
        fold_corrs[tc] = r[0]
    return np.mean(fold_corrs)


def loco_centered(amp_raw, model_name, alpha_val=None, beta_val=None):
    """LOCO with per-run condition centering."""
    # Per-run centering: remove mean across 8 colors within each run
    amp = amp_raw - amp_raw.mean(axis=1, keepdims=True)
    V_s = amp.shape[2]
    fold_corrs = np.zeros(N_COLORS)
    for tc in range(N_COLORS):
        train_colors = [c for c in range(N_COLORS) if c != tc]
        X_train = amp[:, train_colors, :].reshape(-1, V_s)
        C_train = np.tile(C_full[train_colors], (N_RUNS, 1))

        if model_name == 'ridge_gcv':
            ba, _ = gcv_select_alpha(C_train, X_train, ALPHA_GRID)
            W = fit_W_ridge(C_train, X_train, ba)
        else:
            W = fit_W_smooth_ridge(C_train, X_train, alpha_val, beta_val)

        Y_hat = predict_patterns(W, C_full[tc:tc + 1])
        X_test = amp[:, tc, :].mean(axis=0, keepdims=True)
        r = voxel_pattern_correlation(Y_hat, X_test)
        fold_corrs[tc] = r[0]
    return np.mean(fold_corrs)


def quick_null(amp_raw, model_name, alpha_val, beta_val, n_perms=200,
               center=False):
    """Quick permutation null estimate."""
    rng = np.random.default_rng(42)
    null_scores = np.zeros(n_perms)
    for i in range(n_perms):
        perm = rng.permutation(N_COLORS)
        amp_shuf = amp_raw[:, perm, :]
        if center:
            null_scores[i] = loco_centered(amp_shuf, model_name,
                                           alpha_val, beta_val)
        else:
            null_scores[i] = loco_single(amp_shuf, model_name,
                                         alpha_val, beta_val)
    return null_scores


print('=== Per-Run Centering: LOCO Scores ===')
header = (f'{"Sub":>4} {"ROI":>5} {"Model":>15} '
          f'{"Raw":>8} {"Centered":>10} {"Delta":>8}')
print(header)
print('-' * len(header))

for roi in ['V1', 'V2', 'V4']:
    roi_disp = {'V1': 'V1', 'V2': 'V2', 'V4': 'hV4'}[roi]
    for subj in ['01', '02', '04']:
        try:
            amp = load_amplitudes(baseline_dir, subj, roi)
        except FileNotFoundError:
            continue

        for model_name, alpha_val, beta_val in [
            ('ridge_gcv', None, None),
            ('smooth_tikh', 0.01, 100.0),
        ]:
            raw = loco_single(amp, model_name, alpha_val, beta_val)
            cen = loco_centered(amp, model_name, alpha_val, beta_val)
            print(f'{subj:>4} {roi_disp:>5} {model_name:>15} '
                  f'{raw:>+8.4f} {cen:>+10.4f} {cen - raw:>+8.4f}')

# Quick null comparison for one subject/ROI
print('\n=== Quick Null Comparison (sub-02, hV4, 200 perms) ===')
try:
    amp_02_hv4 = load_amplitudes(baseline_dir, '02', 'V4')
    for model_name, alpha_val, beta_val in [
        ('ridge_gcv', None, None),
        ('smooth_tikh', 0.01, 100.0),
    ]:
        obs_raw = loco_single(amp_02_hv4, model_name, alpha_val, beta_val)
        obs_cen = loco_centered(amp_02_hv4, model_name, alpha_val, beta_val)

        null_raw = quick_null(amp_02_hv4, model_name, alpha_val, beta_val,
                              n_perms=200, center=False)
        null_cen = quick_null(amp_02_hv4, model_name, alpha_val, beta_val,
                              n_perms=200, center=True)

        print(f'\n  {model_name}:')
        print(f'    Raw:      obs={obs_raw:+.4f}, '
              f'null_mean={null_raw.mean():+.4f}, '
              f'delta={obs_raw - null_raw.mean():+.4f}, '
              f'p~{(null_raw >= obs_raw).mean():.3f}')
        print(f'    Centered: obs={obs_cen:+.4f}, '
              f'null_mean={null_cen.mean():+.4f}, '
              f'delta={obs_cen - null_cen.mean():+.4f}, '
              f'p~{(null_cen >= obs_cen).mean():.3f}')
except FileNotFoundError:
    print('  Data not found, skipping.')
