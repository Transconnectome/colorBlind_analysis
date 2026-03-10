#!/usr/bin/env python3
"""
residual_structure_loco.py — Residual Structure Analysis (9f-3).

Fits ridge_gcv on ALL 8 colors (run-averaged), computes residuals,
and tests whether residual structure correlates with the original
or ideal-circular RDM.

Interpretation:
  r(resid, orig) ~ 0  -> noise ceiling reached (model captures structure)
  r(resid, orig) high  -> systematic structure missed
  r(resid, ideal) high -> circular geometry not fully captured

Usage:
    python residual_structure_loco.py \
        --baseline_dir ../../phase1_preprocess_decoding/results/full_dataset_C010 \
        --output_dir ../results/loco_reinforcement
"""

import argparse
import json
import numpy as np
from pathlib import Path
from scipy import stats
from scipy.spatial.distance import pdist, squareform

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from utils_forward_model import (
    HC_SUBJECTS, CVD_SUBJECTS, ALL_SUBJECTS, ROIS,
    N_RUNS, N_COLORS, N_CHANNELS, HUE_ANGLES, ALPHA_GRID,
    load_amplitudes, create_basis_matrix,
    fit_W_ridge, gcv_select_alpha, predict_patterns,
    compute_rdm, rdm_upper_tri,
)

ROI_DISPLAY = {'V1': 'V1', 'V2': 'V2', 'V3': 'V3', 'V4': 'hV4'}

COLOR_NAMES = ['Red', 'Orange', 'Yellow', 'Green', 'Cyan', 'Blue', 'Purple', 'Magenta']


# ============================================================================
# Ideal circular RDM
# ============================================================================

def ideal_circular_rdm(hue_angles=HUE_ANGLES):
    """Create ideal circular RDM based on angular distances.

    Returns:
        rdm: (8, 8) symmetric distance matrix (0-180 degrees, normalized to 0-1)
    """
    n = len(hue_angles)
    rdm = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            diff = abs(hue_angles[i] - hue_angles[j])
            rdm[i, j] = min(diff, 360 - diff) / 180.0  # Normalize to [0, 1]
    return rdm


# ============================================================================
# Residual analysis per subject
# ============================================================================

def analyze_residuals(amp, C_full, alpha_grid=ALPHA_GRID):
    """Fit full-data ridge_gcv and analyze residual structure.

    Args:
        amp: (6, 8, V_s) amplitudes
        C_full: (8, K) design matrix

    Returns:
        dict with residual analysis results
    """
    V_s = amp.shape[2]

    # Run-averaged patterns
    Y_mean = amp.mean(axis=0)  # (8, V_s)

    # Fit ridge_gcv on ALL data (all runs, all colors)
    X_train = amp.reshape(-1, V_s)  # (48, V_s)
    C_train = np.tile(C_full, (N_RUNS, 1))  # (48, K)

    best_alpha, _ = gcv_select_alpha(C_train, X_train, alpha_grid)
    W = fit_W_ridge(C_train, X_train, best_alpha)  # (K, V_s)

    # Predicted patterns
    Y_hat = predict_patterns(W, C_full)  # (8, V_s)

    # Residuals
    R = Y_mean - Y_hat  # (8, V_s)

    # RDMs
    rdm_original = compute_rdm(Y_mean, metric='correlation')
    rdm_predicted = compute_rdm(Y_hat, metric='correlation')
    rdm_residual = compute_rdm(R, metric='correlation')
    rdm_ideal = ideal_circular_rdm()

    # Extract upper triangles for correlation
    tri_orig = rdm_upper_tri(rdm_original)
    tri_pred = rdm_upper_tri(rdm_predicted)
    tri_resid = rdm_upper_tri(rdm_residual)
    tri_ideal = rdm_upper_tri(rdm_ideal)

    # Handle NaN in correlation distances (e.g., constant patterns)
    if np.any(np.isnan(tri_orig)) or np.any(np.isnan(tri_resid)):
        return {
            'alpha': float(best_alpha),
            'r_resid_orig': np.nan,
            'r_resid_ideal': np.nan,
            'r_pred_orig': np.nan,
            'r_orig_ideal': np.nan,
            'residual_norm': float(np.sqrt(np.sum(R**2))),
            'signal_norm': float(np.sqrt(np.sum(Y_mean**2))),
            'nan_warning': True,
        }

    # Spearman correlations
    r_resid_orig, p_resid_orig = stats.spearmanr(tri_resid, tri_orig)
    r_resid_ideal, p_resid_ideal = stats.spearmanr(tri_resid, tri_ideal)
    r_pred_orig, p_pred_orig = stats.spearmanr(tri_pred, tri_orig)
    r_orig_ideal, p_orig_ideal = stats.spearmanr(tri_orig, tri_ideal)

    # Pattern-level metrics
    residual_norm = float(np.sqrt(np.sum(R**2)))
    signal_norm = float(np.sqrt(np.sum(Y_mean**2)))
    ratio = residual_norm / signal_norm if signal_norm > 0 else np.inf

    # Per-color residual magnitude
    per_color_resid_norm = np.sqrt(np.sum(R**2, axis=1))  # (8,)

    return {
        'alpha': float(best_alpha),
        'r_resid_orig': float(r_resid_orig) if np.isfinite(r_resid_orig) else 0.0,
        'p_resid_orig': float(p_resid_orig) if np.isfinite(p_resid_orig) else 1.0,
        'r_resid_ideal': float(r_resid_ideal) if np.isfinite(r_resid_ideal) else 0.0,
        'p_resid_ideal': float(p_resid_ideal) if np.isfinite(p_resid_ideal) else 1.0,
        'r_pred_orig': float(r_pred_orig) if np.isfinite(r_pred_orig) else 0.0,
        'p_pred_orig': float(p_pred_orig) if np.isfinite(p_pred_orig) else 1.0,
        'r_orig_ideal': float(r_orig_ideal) if np.isfinite(r_orig_ideal) else 0.0,
        'p_orig_ideal': float(p_orig_ideal) if np.isfinite(p_orig_ideal) else 1.0,
        'residual_norm': residual_norm,
        'signal_norm': signal_norm,
        'resid_signal_ratio': float(ratio),
        'per_color_resid_norm': per_color_resid_norm.tolist(),
        'rdm_original': rdm_original.tolist(),
        'rdm_predicted': rdm_predicted.tolist(),
        'rdm_residual': rdm_residual.tolist(),
    }


# ============================================================================
# Plotting
# ============================================================================

def plot_residual_rdms(hc_results, roi_display, output_dir):
    """3 RDM heatmaps (original, predicted, residual) + scatter plot."""
    # Average RDMs across HC subjects
    rdm_orig_list = [np.array(r['rdm_original']) for r in hc_results
                     if 'rdm_original' in r and not r.get('nan_warning')]
    rdm_pred_list = [np.array(r['rdm_predicted']) for r in hc_results
                     if 'rdm_predicted' in r and not r.get('nan_warning')]
    rdm_resid_list = [np.array(r['rdm_residual']) for r in hc_results
                      if 'rdm_residual' in r and not r.get('nan_warning')]

    if not rdm_orig_list:
        print(f'  Warning: no valid RDMs for {roi_display}, skipping plot')
        return

    rdm_orig_mean = np.mean(rdm_orig_list, axis=0)
    rdm_pred_mean = np.mean(rdm_pred_list, axis=0)
    rdm_resid_mean = np.mean(rdm_resid_list, axis=0)

    # Mean correlations
    r_resid_orig = np.mean([r['r_resid_orig'] for r in hc_results
                            if not r.get('nan_warning')])
    r_resid_ideal = np.mean([r['r_resid_ideal'] for r in hc_results
                             if not r.get('nan_warning')])
    r_pred_orig = np.mean([r['r_pred_orig'] for r in hc_results
                           if not r.get('nan_warning')])

    labels = [f'{COLOR_NAMES[c][:3]}' for c in range(8)]

    fig, axes = plt.subplots(1, 4, figsize=(20, 5))

    # Original RDM
    im0 = axes[0].imshow(rdm_orig_mean, cmap='RdBu_r', vmin=0, vmax=2)
    axes[0].set_title('Original RDM\n(data)', fontsize=11, fontweight='bold')
    axes[0].set_xticks(range(8)); axes[0].set_xticklabels(labels, fontsize=7, rotation=45)
    axes[0].set_yticks(range(8)); axes[0].set_yticklabels(labels, fontsize=7)
    plt.colorbar(im0, ax=axes[0], fraction=0.046)

    # Predicted RDM
    im1 = axes[1].imshow(rdm_pred_mean, cmap='RdBu_r', vmin=0, vmax=2)
    axes[1].set_title(f'Predicted RDM\n(model, r(pred,orig)={r_pred_orig:.3f})',
                      fontsize=11, fontweight='bold')
    axes[1].set_xticks(range(8)); axes[1].set_xticklabels(labels, fontsize=7, rotation=45)
    axes[1].set_yticks(range(8)); axes[1].set_yticklabels(labels, fontsize=7)
    plt.colorbar(im1, ax=axes[1], fraction=0.046)

    # Residual RDM
    im2 = axes[2].imshow(rdm_resid_mean, cmap='RdBu_r', vmin=0, vmax=2)
    axes[2].set_title(f'Residual RDM\nr(resid,orig)={r_resid_orig:.3f}\n'
                      f'r(resid,ideal)={r_resid_ideal:.3f}',
                      fontsize=11, fontweight='bold')
    axes[2].set_xticks(range(8)); axes[2].set_xticklabels(labels, fontsize=7, rotation=45)
    axes[2].set_yticks(range(8)); axes[2].set_yticklabels(labels, fontsize=7)
    plt.colorbar(im2, ax=axes[2], fraction=0.046)

    # Scatter: residual vs original upper tri
    tri_orig = rdm_upper_tri(rdm_orig_mean)
    tri_resid = rdm_upper_tri(rdm_resid_mean)
    axes[3].scatter(tri_orig, tri_resid, alpha=0.6, s=30, color='steelblue')
    axes[3].set_xlabel('Original RDM', fontsize=10)
    axes[3].set_ylabel('Residual RDM', fontsize=10)
    r_scatter, _ = stats.spearmanr(tri_orig, tri_resid)
    axes[3].set_title(f'Resid vs Orig\nSpearman r={r_scatter:.3f}',
                      fontsize=11, fontweight='bold')
    # Add identity line
    lims = [min(min(tri_orig), min(tri_resid)),
            max(max(tri_orig), max(tri_resid))]
    axes[3].plot(lims, lims, 'k--', alpha=0.3)
    axes[3].grid(alpha=0.3)

    plt.suptitle(f'{roi_display} — Residual Structure Analysis (HC mean, ridge_gcv)',
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    out_path = output_dir / f'residual_rdm_{roi_display}.png'
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'  Saved: {out_path}')


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Residual structure analysis')
    parser.add_argument('--baseline_dir', type=str, required=True,
                        help='Path to full_dataset_C010')
    parser.add_argument('--output_dir', type=str, required=True,
                        help='Output directory')
    parser.add_argument('--rois', nargs='+', default=['V1', 'V2', 'V3', 'V4'],
                        help='ROIs to analyze')
    args = parser.parse_args()

    baseline_dir = Path(args.baseline_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    C_full = create_basis_matrix(HUE_ANGLES, N_CHANNELS, 'fe')  # (8, 6)
    rdm_ideal = ideal_circular_rdm()

    print('=' * 60)
    print('Residual Structure Analysis (9f-3)')
    print('=' * 60)

    all_results = {}

    for roi in args.rois:
        roi_disp = ROI_DISPLAY[roi]
        print(f'\n--- {roi_disp} ---')

        hc_results = []
        cvd_results = []

        for subj in ALL_SUBJECTS:
            try:
                amp = load_amplitudes(baseline_dir, subj, roi)
            except FileNotFoundError:
                print(f'  Warning: missing sub-{subj} {roi}')
                continue

            res = analyze_residuals(amp, C_full)
            res['subject'] = subj
            res['group'] = 'HC' if subj in HC_SUBJECTS else 'CVD'

            if subj in HC_SUBJECTS:
                hc_results.append(res)
            else:
                cvd_results.append(res)

            if not res.get('nan_warning'):
                print(f'  sub-{subj}: r(resid,orig)={res["r_resid_orig"]:.3f}, '
                      f'r(resid,ideal)={res["r_resid_ideal"]:.3f}, '
                      f'r(pred,orig)={res["r_pred_orig"]:.3f}, '
                      f'ratio={res["resid_signal_ratio"]:.3f}')
            else:
                print(f'  sub-{subj}: NaN in RDM (skipped)')

        # HC summary
        valid_hc = [r for r in hc_results if not r.get('nan_warning')]
        if valid_hc:
            hc_r_resid_orig = [r['r_resid_orig'] for r in valid_hc]
            hc_r_resid_ideal = [r['r_resid_ideal'] for r in valid_hc]
            hc_r_pred_orig = [r['r_pred_orig'] for r in valid_hc]
            hc_ratio = [r['resid_signal_ratio'] for r in valid_hc]

            print(f'\n  HC summary (n={len(valid_hc)}):')
            print(f'    r(resid,orig):  {np.mean(hc_r_resid_orig):.3f} +/- '
                  f'{np.std(hc_r_resid_orig,ddof=1):.3f}')
            print(f'    r(resid,ideal): {np.mean(hc_r_resid_ideal):.3f} +/- '
                  f'{np.std(hc_r_resid_ideal,ddof=1):.3f}')
            print(f'    r(pred,orig):   {np.mean(hc_r_pred_orig):.3f} +/- '
                  f'{np.std(hc_r_pred_orig,ddof=1):.3f}')
            print(f'    resid/signal:   {np.mean(hc_ratio):.3f} +/- '
                  f'{np.std(hc_ratio,ddof=1):.3f}')

        # Plot
        if valid_hc:
            plot_residual_rdms(valid_hc, roi_disp, output_dir)

        all_results[roi_disp] = {
            'hc': [{k: v for k, v in r.items()
                    if k not in ('rdm_original', 'rdm_predicted', 'rdm_residual')}
                   for r in hc_results],
            'cvd': [{k: v for k, v in r.items()
                     if k not in ('rdm_original', 'rdm_predicted', 'rdm_residual')}
                    for r in cvd_results],
            'hc_summary': {
                'n': len(valid_hc),
                'r_resid_orig_mean': float(np.mean(hc_r_resid_orig)) if valid_hc else None,
                'r_resid_orig_sd': float(np.std(hc_r_resid_orig, ddof=1)) if valid_hc else None,
                'r_resid_ideal_mean': float(np.mean(hc_r_resid_ideal)) if valid_hc else None,
                'r_resid_ideal_sd': float(np.std(hc_r_resid_ideal, ddof=1)) if valid_hc else None,
                'r_pred_orig_mean': float(np.mean(hc_r_pred_orig)) if valid_hc else None,
                'r_pred_orig_sd': float(np.std(hc_r_pred_orig, ddof=1)) if valid_hc else None,
                'resid_signal_ratio_mean': float(np.mean(hc_ratio)) if valid_hc else None,
            } if valid_hc else {},
        }

    # Save results
    with open(output_dir / 'residual_structure.json', 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f'\nSaved: {output_dir / "residual_structure.json"}')

    # Update config
    config_path = output_dir / 'config.json'
    if config_path.exists():
        config = json.loads(config_path.read_text())
    else:
        config = {}
    config['residual_structure'] = {
        'script': 'residual_structure_loco.py',
        'baseline_dir': str(baseline_dir),
    }
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2, default=str)

    print('\nDone.')


if __name__ == '__main__':
    main()
