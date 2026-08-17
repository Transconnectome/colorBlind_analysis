#!/usr/bin/env python3
"""Inspect RDM structure: does it show the expected circular hue arrangement?

Computes and displays:
1. Actual RDM from run-averaged voxel patterns
2. LOCO-predicted RDM (ridge_gcv, smooth_tikh)
3. Ideal RDM (circular hue distance)
4. Correlations between them
"""
import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
import numpy as np
from scipy.spatial.distance import pdist, squareform
from scipy.stats import spearmanr
from utils_forward_model import (
    load_amplitudes, create_basis_matrix, HUE_ANGLES, N_CHANNELS, N_RUNS, N_COLORS,
    fit_W_ridge, fit_W_smooth_ridge, gcv_select_alpha, ALPHA_GRID,
    predict_patterns, voxel_pattern_correlation, compute_rdm, rdm_upper_tri,
)

baseline_dir = '../../../analysis/phase1_preprocess_decoding/results/full_dataset_C010'
C_full = create_basis_matrix(HUE_ANGLES, N_CHANNELS, 'fe')

COLOR_NAMES = ['red', 'orange', 'yellow', 'green', 'cyan', 'blue', 'purple', 'magenta']


def ideal_rdm():
    """Ideal RDM based on circular hue distance."""
    n = len(HUE_ANGLES)
    rdm = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            diff = abs(HUE_ANGLES[i] - HUE_ANGLES[j])
            rdm[i, j] = min(diff, 360 - diff) / 180.0  # normalize to [0, 1]
    return rdm


def loco_predict_all(amp, model_name, alpha_val=None, beta_val=None):
    """LOCO: predict all 8 color patterns."""
    V_s = amp.shape[2]
    pred = np.zeros((N_COLORS, V_s))
    for tc in range(N_COLORS):
        train_colors = [c for c in range(N_COLORS) if c != tc]
        X_train = amp[:, train_colors, :].reshape(-1, V_s)
        C_train = np.tile(C_full[train_colors], (N_RUNS, 1))
        if model_name == 'ridge_gcv':
            ba, _ = gcv_select_alpha(C_train, X_train, ALPHA_GRID)
            W = fit_W_ridge(C_train, X_train, ba)
        else:
            W = fit_W_smooth_ridge(C_train, X_train, alpha_val, beta_val)
        pred[tc] = (C_full[tc:tc + 1] @ W)[0]
    return pred


def print_rdm(rdm, label, names=None):
    """Print RDM matrix nicely."""
    n = rdm.shape[0]
    if names is None:
        names = [f'c{i}' for i in range(n)]
    # Short names
    short = [nm[:4] for nm in names]
    header = '       ' + '  '.join(f'{s:>6}' for s in short)
    print(f'\n  {label}:')
    print(header)
    for i in range(n):
        row = f'  {short[i]:>5} '
        for j in range(n):
            if i == j:
                row += '     - '
            else:
                row += f'{rdm[i, j]:6.3f} '
        print(row)


# Ideal RDM
rdm_ideal = ideal_rdm()
print('=== Ideal RDM (circular hue distance, normalized) ===')
print_rdm(rdm_ideal, 'Ideal', COLOR_NAMES)

print('\n\n=== Actual & Predicted RDMs per Subject/ROI ===')

for roi in ['V1', 'V2', 'V4']:
    roi_disp = {'V1': 'V1', 'V2': 'V2', 'V4': 'hV4'}[roi]
    print(f'\n{"=" * 70}')
    print(f'  ROI: {roi_disp}')
    print(f'{"=" * 70}')

    all_actual_corrs = []
    all_ridge_corrs = []
    all_smooth_corrs = []

    for subj in ['01', '02', '03', '04', '05', '06', '07']:
        try:
            amp = load_amplitudes(baseline_dir, subj, roi)
        except FileNotFoundError:
            continue

        # Actual RDM
        actual_patterns = amp.mean(axis=0)  # (8, V_s)
        rdm_actual = compute_rdm(actual_patterns)

        # LOCO predicted RDMs
        pred_ridge = loco_predict_all(amp, 'ridge_gcv')
        pred_smooth = loco_predict_all(amp, 'smooth_tikh', 0.01, 100.0)
        rdm_ridge = compute_rdm(pred_ridge)
        rdm_smooth = compute_rdm(pred_smooth)

        # Correlations with ideal
        tri_ideal = rdm_upper_tri(rdm_ideal)
        tri_actual = rdm_upper_tri(rdm_actual)
        tri_ridge = rdm_upper_tri(rdm_ridge)
        tri_smooth = rdm_upper_tri(rdm_smooth)

        # Filter NaN
        mask = (np.isfinite(tri_actual) & np.isfinite(tri_ridge)
                & np.isfinite(tri_smooth))
        if mask.sum() < 3:
            continue

        r_actual_ideal = spearmanr(tri_actual[mask], tri_ideal[mask])[0]
        r_ridge_actual = np.corrcoef(tri_ridge[mask], tri_actual[mask])[0, 1]
        r_smooth_actual = np.corrcoef(tri_smooth[mask], tri_actual[mask])[0, 1]
        r_ridge_ideal = spearmanr(tri_ridge[mask], tri_ideal[mask])[0]
        r_smooth_ideal = spearmanr(tri_smooth[mask], tri_ideal[mask])[0]

        all_actual_corrs.append(r_actual_ideal)
        all_ridge_corrs.append(r_ridge_ideal)
        all_smooth_corrs.append(r_smooth_ideal)

        print(f'\n  sub-{subj}:')
        print(f'    Actual vs Ideal (Spearman):       {r_actual_ideal:+.3f}')
        print(f'    Ridge pred vs Actual (Pearson):    {r_ridge_actual:+.3f}')
        print(f'    Smooth pred vs Actual (Pearson):   {r_smooth_actual:+.3f}')
        print(f'    Ridge pred vs Ideal (Spearman):    {r_ridge_ideal:+.3f}')
        print(f'    Smooth pred vs Ideal (Spearman):   {r_smooth_ideal:+.3f}')

        # Print actual RDM for first subject per ROI
        if subj == '01':
            print_rdm(rdm_actual, f'Actual RDM (sub-{subj})', COLOR_NAMES)
            print_rdm(rdm_ridge, f'Ridge LOCO-predicted RDM (sub-{subj})', COLOR_NAMES)
            print_rdm(rdm_smooth, f'Smooth LOCO-predicted RDM (sub-{subj})', COLOR_NAMES)

    if all_actual_corrs:
        print(f'\n  --- HC Mean (n={len(all_actual_corrs)}) ---')
        print(f'    Actual vs Ideal:   {np.mean(all_actual_corrs):+.3f} '
              f'(SD={np.std(all_actual_corrs):.3f})')
        print(f'    Ridge vs Ideal:    {np.mean(all_ridge_corrs):+.3f} '
              f'(SD={np.std(all_ridge_corrs):.3f})')
        print(f'    Smooth vs Ideal:   {np.mean(all_smooth_corrs):+.3f} '
              f'(SD={np.std(all_smooth_corrs):.3f})')
