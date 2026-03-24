#!/usr/bin/env python3
"""
step1_fit_loco_v2.py — LOCO-based δθ optimization (v2, W-fixed).

Key design (v2):
  - Mean-HC approach: average LOCO vulnerability across all HC, then fit
  - Spearman ρ as fitting criterion (profile match, not level match)
  - W-fixed: precompute W_HC from C(θ) once, sweep C(θ+δ) without retraining
    Physical model: W_CVD = W_HC (same cortical encoding), only input warped
  - Permutation evaluation — shuffle color labels for null distribution
  - MSE decomposition + Lin's CCC for supplementary reporting

Strategy:
  For each CVD subject × ROI:
    1. Precompute W_HC for each HC (pooled 6 runs × 8 colors, ridge_gcv)
    2. Compute mean_HC_vuln(δθ) = mean over 7 HC of W-fixed vuln at shift δθ
    3. Fit δθ to maximize Spearman(mean_HC_vuln(δθ), CVD_vuln)
    4. Evaluate: permutation test on observed Spearman r
    5. Report: MSE decomposition (bias², profile_mse), CCC, level match

  Additionally, per-HC diagnostics are saved for consistency analysis.

Usage:
    python scripts/step1_fit_loco_v2.py \
        --output_dir results/v2/step1_loco_wfixed
"""

import argparse
import json
import numpy as np
from pathlib import Path
from datetime import datetime
from scipy.optimize import differential_evolution
from scipy.stats import spearmanr
from itertools import permutations
import sys

_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR))

_FWD_DIR = str(Path(__file__).resolve().parent.parent.parent.parent
               / 'future_phase1_forward_model' / 'scripts')
sys.path.insert(0, _FWD_DIR)

from utils_forward_model import (
    HC_SUBJECTS, CVD_SUBJECTS, ROIS, N_CHANNELS, N_RUNS, N_COLORS,
    HUE_ANGLES, load_amplitudes, create_basis_matrix,
    gcv_select_alpha, fit_W_ridge, voxel_pattern_correlation,
)
from utils_distortion_models import (
    MODELS, get_design_matrix, get_initial_params, compute_aicc,
)

LOCAL_BASELINE = Path(__file__).resolve().parent.parent.parent.parent \
    / 'phase1_preprocess_decoding' / 'results' / 'full_dataset_C010'
FWD_RESULTS = Path(__file__).resolve().parent.parent.parent.parent \
    / 'future_phase1_forward_model' / 'results'

CVD_TYPE = {'08': 'deutan', '09': 'protan', '10': 'normal'}

FIT_MODELS = ['cone_1way', 'cone_3way', 'fourier', 'per_color']


# ============================================================================
# Metrics
# ============================================================================

def lins_ccc(x, y):
    """Lin's Concordance Correlation Coefficient."""
    x, y = np.asarray(x), np.asarray(y)
    mx, my = x.mean(), y.mean()
    sx, sy = x.std(ddof=1), y.std(ddof=1)
    if sx == 0 or sy == 0:
        return 0.0
    r = np.corrcoef(x, y)[0, 1]
    if not np.isfinite(r):
        return 0.0
    return 2 * r * sx * sy / (sx**2 + sy**2 + (mx - my)**2)


def mse_decompose(pred, target):
    """Decompose MSE into bias² and profile variance.

    MSE = bias² + mean((pred - mean_pred) - (target - mean_target))²

    Returns:
        mse, bias_sq, profile_mse
    """
    pred, target = np.asarray(pred), np.asarray(target)
    mse = float(np.mean((pred - target) ** 2))
    bias_sq = float((pred.mean() - target.mean()) ** 2)
    profile_mse = float(np.mean(
        ((pred - pred.mean()) - (target - target.mean())) ** 2
    ))
    return mse, bias_sq, profile_mse


# ============================================================================
# Legacy LOCO simulation (shift_at_both) — retained for comparison
# ============================================================================

def simulate_single_hc_loco_legacy(amp_hc, C_shifted):
    """[Legacy] Run LOCO for one HC subject with shifted design.

    shift_at_both: train with C(θ+δ), test with C(θ+δ).
    Retrains W at every δθ — ~3.5h for full sweep.

    Args:
        amp_hc: (6, 8, V_s) single HC amplitudes
        C_shifted: (8, K) shifted design matrix

    Returns:
        vuln: (8,) per-color voxel correlation
    """
    V_s = amp_hc.shape[2]
    vuln = np.zeros(N_COLORS)

    for color in range(N_COLORS):
        train_colors = [c for c in range(N_COLORS) if c != color]

        # Pool 6 runs × 7 train colors = 42 samples
        X_train = amp_hc[:, train_colors].reshape(-1, V_s)       # (42, V_s)
        C_train = np.tile(C_shifted[train_colors], (N_RUNS, 1))  # (42, K)

        alpha, _ = gcv_select_alpha(C_train, X_train)
        W = fit_W_ridge(C_train, X_train, alpha)

        # Predict held-out with shifted design
        Y_pred = C_shifted[color:color+1] @ W     # (1, V_s)
        Y_test = amp_hc[:, color].mean(axis=0, keepdims=True)  # (1, V_s)
        r = voxel_pattern_correlation(Y_pred, Y_test)
        vuln[color] = r[0]

    return vuln


def simulate_mean_hc_loco_legacy(hc_amps_dict, C_shifted):
    """[Legacy] Compute mean-HC vulnerability at a given shift.

    Runs LOCO for each HC subject (with W retraining), then averages.
    """
    per_hc_vuln = {}
    for subj, amp in hc_amps_dict.items():
        per_hc_vuln[subj] = simulate_single_hc_loco_legacy(amp, C_shifted)

    vuln_matrix = np.array(list(per_hc_vuln.values()))  # (n_hc, 8)
    mean_vuln = vuln_matrix.mean(axis=0)
    return mean_vuln, per_hc_vuln


# ============================================================================
# W-fixed LOCO simulation (primary)
# ============================================================================

def precompute_hc_W(hc_amps_dict, C_original):
    """Precompute ridge encoding weights for each HC subject.

    Uses pooled 6 runs × 8 colors = 48 samples with C(θ) (original design).
    W is fixed and reused for all δθ sweeps.

    Physical model: W encodes cortical processing (same for HC and CVD).
    Cone shift only changes the stimulus representation C(θ+δ).

    Args:
        hc_amps_dict: dict {subj_id: (6, 8, V_s) amplitudes}
        C_original: (8, K) original design matrix (unshifted)

    Returns:
        hc_W_dict: dict {subj_id: (K, V_s) weight matrix}
        hc_alpha_dict: dict {subj_id: float selected alpha}
    """
    hc_W_dict = {}
    hc_alpha_dict = {}
    C_pooled = np.tile(C_original, (N_RUNS, 1))  # (48, K)

    for subj, amp in hc_amps_dict.items():
        V_s = amp.shape[2]
        X_all = amp.reshape(-1, V_s)  # (48, V_s)
        alpha, _ = gcv_select_alpha(C_pooled, X_all)
        W = fit_W_ridge(C_pooled, X_all, alpha)  # (K, V_s)
        hc_W_dict[subj] = W
        hc_alpha_dict[subj] = float(alpha)

    return hc_W_dict, hc_alpha_dict


def simulate_single_hc_wfixed(W_hc, amp_hc, C_shifted):
    """Run W-fixed prediction for one HC subject with shifted design.

    W_HC is fixed (precomputed from C(θ)), only C(θ+δ) changes.
    Prediction: Y_pred[c] = C_shifted[c] @ W_HC
    Target: Y_actual[c] = run-averaged amp[c]

    Args:
        W_hc: (K, V_s) precomputed weight matrix for this HC
        amp_hc: (6, 8, V_s) single HC amplitudes
        C_shifted: (8, K) shifted design matrix

    Returns:
        vuln: (8,) per-color voxel correlation
    """
    vuln = np.zeros(N_COLORS)
    for color in range(N_COLORS):
        Y_pred = C_shifted[color:color+1] @ W_hc  # (1, V_s)
        Y_actual = amp_hc[:, color].mean(axis=0, keepdims=True)  # (1, V_s)
        r = voxel_pattern_correlation(Y_pred, Y_actual)
        vuln[color] = r[0]
    return vuln


def simulate_mean_hc_wfixed(hc_W_dict, hc_amps_dict, C_shifted):
    """Compute mean-HC vulnerability using W-fixed approach.

    For each HC, predicts patterns with fixed W and shifted C,
    then averages vulnerability across all HC.

    Args:
        hc_W_dict: dict {subj_id: (K, V_s) weight matrix}
        hc_amps_dict: dict {subj_id: (6, 8, V_s) amplitudes}
        C_shifted: (8, K) shifted design matrix

    Returns:
        mean_vuln: (8,) mean per-color voxel correlation across HC
        per_hc_vuln: dict {subj_id: (8,) vuln}
    """
    per_hc_vuln = {}
    for subj in hc_W_dict:
        per_hc_vuln[subj] = simulate_single_hc_wfixed(
            hc_W_dict[subj], hc_amps_dict[subj], C_shifted)

    vuln_matrix = np.array(list(per_hc_vuln.values()))  # (n_hc, 8)
    mean_vuln = vuln_matrix.mean(axis=0)
    return mean_vuln, per_hc_vuln




# ============================================================================
# Objective function: mean-HC Spearman
# ============================================================================

def mean_hc_spearman_objective(params, model_name, hc_W_dict, hc_amps_dict,
                                cvd_vuln, cvd_type):
    """Negative Spearman ρ between mean-HC shifted vuln and CVD vuln.

    Minimizing this maximizes profile match.
    Uses W-fixed approach: W precomputed, only C(θ+δ) changes.
    """
    C_shifted = get_design_matrix(model_name, params, cvd_type=cvd_type)
    mean_vuln, _ = simulate_mean_hc_wfixed(hc_W_dict, hc_amps_dict, C_shifted)
    rho, _ = spearmanr(mean_vuln, cvd_vuln)
    if not np.isfinite(rho):
        return 1.0  # worst case
    return -rho


# ============================================================================
# Permutation test
# ============================================================================

def permutation_test_spearman(hc_vuln_fitted, cvd_vuln, n_perm=10000):
    """Permutation test: shuffle CVD color labels.

    Tests whether the Spearman ρ is higher than chance alignment.

    Args:
        hc_vuln_fitted: (8,) fitted mean-HC shifted vulnerability
        cvd_vuln: (8,) CVD actual vulnerability
        n_perm: number of permutations

    Returns:
        p_value, null_distribution (n_perm,), observed_rho
    """
    rho_obs, _ = spearmanr(hc_vuln_fitted, cvd_vuln)
    if not np.isfinite(rho_obs):
        rho_obs = 0.0

    # Exact permutation if feasible (8! = 40320)
    use_exact = n_perm >= 40320
    if use_exact:
        null = []
        for perm in permutations(range(8)):
            cvd_perm = cvd_vuln[list(perm)]
            r, _ = spearmanr(hc_vuln_fitted, cvd_perm)
            null.append(r if np.isfinite(r) else 0.0)
        null = np.array(null)
    else:
        rng = np.random.default_rng(42)
        null = np.zeros(n_perm)
        for i in range(n_perm):
            perm = rng.permutation(8)
            r, _ = spearmanr(hc_vuln_fitted, cvd_vuln[perm])
            null[i] = r if np.isfinite(r) else 0.0

    # One-tailed: proportion of null ≥ observed (higher Spearman = better)
    p = (np.sum(null >= rho_obs) + 1) / (len(null) + 1)
    return float(p), null, float(rho_obs)


def permutation_test_mse(hc_vuln_fitted, cvd_vuln, n_perm=10000):
    """Permutation test on MSE (supplementary)."""
    mse_obs = np.mean((hc_vuln_fitted - cvd_vuln) ** 2)

    use_exact = n_perm >= 40320
    if use_exact:
        null = []
        for perm in permutations(range(8)):
            cvd_perm = cvd_vuln[list(perm)]
            null.append(np.mean((hc_vuln_fitted - cvd_perm) ** 2))
        null = np.array(null)
    else:
        rng = np.random.default_rng(42)
        null = np.zeros(n_perm)
        for i in range(n_perm):
            perm = rng.permutation(8)
            null[i] = np.mean((hc_vuln_fitted - cvd_vuln[perm]) ** 2)

    p = (np.sum(null <= mse_obs) + 1) / (len(null) + 1)
    return float(p), null


# ============================================================================
# Load CVD target
# ============================================================================

def load_cvd_loco_target(cvd_subj, roi, model='ridge_gcv'):
    """Load CVD actual LOCO per-color voxel_corr."""
    loco_path = FWD_RESULTS / 'validation' / f'sub-{cvd_subj}_loco.json'
    with open(loco_path) as f:
        data = json.load(f)
    folds = data[roi][model]['folds']
    per_color = np.zeros(8)
    for fold in folds:
        per_color[fold['test_color']] = fold['voxel_corr']
    return per_color


# ============================================================================
# Main fitting: mean-HC approach
# ============================================================================

def fit_mean_hc(hc_W_dict, hc_amps_dict, cvd_vuln, cvd_type, models=None):
    """Fit δθ using mean-HC vulnerability profile (W-fixed).

    For each distortion model:
      1. Optimize: maximize Spearman(mean_HC_vuln(δθ), CVD_vuln)
      2. Evaluate: permutation test, MSE decomposition, CCC

    Args:
        hc_W_dict: dict {subj_id: (K, V_s)} precomputed weights
        hc_amps_dict: dict {subj_id: (6, 8, V_s)} amplitudes
        cvd_vuln: (8,) CVD LOCO target
        cvd_type: 'deutan', 'protan', or 'normal'
        models: list of model names to fit

    Returns:
        fit_result: dict with per-model results
        per_hc_diagnostics: dict with per-HC vulnerability at optimal δθ
    """
    if models is None:
        models = FIT_MODELS

    fit_result = {}
    per_hc_diagnostics = {}

    for model_name in models:
        bounds = MODELS[model_name]['bounds']

        # Optimize: maximize Spearman ρ via mean-HC (W-fixed)
        df = MODELS[model_name]['df']
        pop = 10 if df <= 3 else 8
        maxit = 80 if df <= 3 else 50

        res = differential_evolution(
            mean_hc_spearman_objective, bounds,
            args=(model_name, hc_W_dict, hc_amps_dict, cvd_vuln, cvd_type),
            seed=42, maxiter=maxit, tol=1e-6,
            popsize=pop, mutation=(0.5, 1.5), recombination=0.7,
        )

        # Compute final vulnerability at optimal δθ
        C_opt = get_design_matrix(model_name, res.x, cvd_type=cvd_type)
        mean_vuln, per_hc_vuln = simulate_mean_hc_wfixed(
            hc_W_dict, hc_amps_dict, C_opt)

        # Spearman ρ (fitting criterion)
        rho_fit, p_rho = spearmanr(mean_vuln, cvd_vuln)
        if not np.isfinite(rho_fit):
            rho_fit, p_rho = 0.0, 1.0

        # Permutation test (Spearman — primary)
        perm_p_rho, perm_null_rho, _ = permutation_test_spearman(
            mean_vuln, cvd_vuln)

        # MSE decomposition (supplementary)
        mse, bias_sq, profile_mse = mse_decompose(mean_vuln, cvd_vuln)

        # Permutation test (MSE — supplementary)
        perm_p_mse, perm_null_mse = permutation_test_mse(mean_vuln, cvd_vuln)

        # CCC (supplementary)
        ccc = lins_ccc(mean_vuln, cvd_vuln)

        # Baseline: δθ=0
        C_baseline = create_basis_matrix(HUE_ANGLES, N_CHANNELS)
        mean_vuln_baseline, _ = simulate_mean_hc_wfixed(
            hc_W_dict, hc_amps_dict, C_baseline)
        rho_baseline, _ = spearmanr(mean_vuln_baseline, cvd_vuln)
        mse_baseline = float(np.mean((mean_vuln_baseline - cvd_vuln) ** 2))

        # Per-HC individual Spearman r at optimal δθ
        per_hc_rhos = {}
        for subj, vuln in per_hc_vuln.items():
            r, _ = spearmanr(vuln, cvd_vuln)
            per_hc_rhos[subj] = float(r) if np.isfinite(r) else 0.0

        fit_result[model_name] = {
            'params': res.x.tolist(),
            'mean_hc_vuln': mean_vuln.tolist(),
            'mean_hc_vuln_baseline': mean_vuln_baseline.tolist(),
            # Primary: Spearman
            'spearman_r': float(rho_fit),
            'spearman_p': float(p_rho),
            'spearman_r_baseline': float(rho_baseline)
                if np.isfinite(rho_baseline) else 0.0,
            'perm_p_spearman': perm_p_rho,
            'perm_null_rho_mean': float(np.mean(perm_null_rho)),
            'perm_null_rho_std': float(np.std(perm_null_rho)),
            # Supplementary: MSE decomposition
            'mse': mse,
            'mse_baseline': mse_baseline,
            'mse_reduction': float((mse_baseline - mse) / mse_baseline)
                if mse_baseline > 0 else 0.0,
            'bias_sq': bias_sq,
            'profile_mse': profile_mse,
            'perm_p_mse': perm_p_mse,
            # Supplementary: CCC
            'ccc': float(ccc),
            # Per-HC diagnostics
            'per_hc_spearman_r': per_hc_rhos,
            'per_hc_spearman_r_mean': float(np.mean(list(per_hc_rhos.values()))),
            'per_hc_spearman_r_sd': float(np.std(
                list(per_hc_rhos.values()), ddof=1)),
            # Optimizer info
            'success': bool(res.success),
            'n_hc': len(hc_amps_dict),
            'method': 'w_fixed',
        }

        # Per-HC vuln at optimal δθ (for diagnostics)
        per_hc_diagnostics[model_name] = {
            subj: vuln.tolist() for subj, vuln in per_hc_vuln.items()
        }

    return fit_result, per_hc_diagnostics


# ============================================================================
# Grid search for landscape visualization
# ============================================================================

def landscape_1d(hc_W_dict, hc_amps_dict, cvd_vuln, cvd_type,
                 delta_range=None):
    """Sweep Δλ for cone_1way and compute Spearman + MSE at each point.

    Uses W-fixed approach: precomputed W, only C(θ+δ) changes.

    Returns dict with arrays for plotting.
    """
    if delta_range is None:
        delta_range = np.arange(0, 61, 1)

    rhos = []
    mses = []
    mean_vulns = []

    for delta in delta_range:
        C = get_design_matrix('cone_1way', [delta], cvd_type=cvd_type)
        mean_vuln, _ = simulate_mean_hc_wfixed(hc_W_dict, hc_amps_dict, C)
        r, _ = spearmanr(mean_vuln, cvd_vuln)
        mse = float(np.mean((mean_vuln - cvd_vuln) ** 2))
        rhos.append(float(r) if np.isfinite(r) else 0.0)
        mses.append(mse)
        mean_vulns.append(mean_vuln.tolist())

    return {
        'delta_range': delta_range.tolist(),
        'spearman_r': rhos,
        'mse': mses,
        'mean_vulns': mean_vulns,
    }


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Step 1B: LOCO fitting (v2, W-fixed, mean-HC Spearman)')
    parser.add_argument('--output_dir', type=str,
                        default='results/v2/step1_loco_wfixed')
    parser.add_argument('--rois', nargs='+', default=['V4'])
    parser.add_argument('--cvd_subjects', nargs='+', default=CVD_SUBJECTS)
    parser.add_argument('--hc_subjects', nargs='+', default=HC_SUBJECTS)
    parser.add_argument('--models', nargs='+', default=FIT_MODELS)
    parser.add_argument('--baseline_dir', type=str,
                        default=str(LOCAL_BASELINE))
    parser.add_argument('--landscape', action='store_true',
                        help='Also compute 1D landscape for cone_1way')
    args = parser.parse_args()

    print('=' * 60)
    print('Step 1B: LOCO Fitting (v2, W-fixed, mean-HC Spearman)')
    print(f'ROIs: {args.rois}')
    print(f'CVD subjects: {args.cvd_subjects}')
    print(f'HC subjects: {args.hc_subjects}')
    print(f'Models: {args.models}')
    print('=' * 60)

    for roi in args.rois:
        print(f'\n=== {roi} ===')

        # Load HC amplitudes once per ROI
        hc_amps = {}
        for subj in args.hc_subjects:
            hc_amps[subj] = load_amplitudes(args.baseline_dir, subj, roi)
        print(f'  Loaded {len(hc_amps)} HC subjects')

        # Precompute W for all HC subjects (W-fixed approach)
        C_original = create_basis_matrix(HUE_ANGLES, N_CHANNELS)
        hc_W, hc_alphas = precompute_hc_W(hc_amps, C_original)
        print(f'  Precomputed W for {len(hc_W)} HC subjects')
        for subj, alpha in hc_alphas.items():
            print(f'    sub-{subj}: alpha={alpha}, '
                  f'W shape={hc_W[subj].shape}')

        for cvd_subj in args.cvd_subjects:
            cvd_type = CVD_TYPE[cvd_subj]
            cvd_vuln = load_cvd_loco_target(cvd_subj, roi)
            print(f'\n  sub-{cvd_subj} ({cvd_type}):')
            print(f'    CVD target vuln: {np.round(cvd_vuln, 3)}')

            # Fit using mean-HC W-fixed approach
            fit_result, per_hc_diag = fit_mean_hc(
                hc_W, hc_amps, cvd_vuln, cvd_type, args.models)

            # Print results
            print(f'\n    --- Results (W-fixed, {len(hc_amps)} HC) ---')
            for m, r in fit_result.items():
                print(f'      {m}:')
                print(f'        δθ = {r["params"]}')
                print(f'        Spearman r = {r["spearman_r"]:.3f} '
                      f'(baseline: {r["spearman_r_baseline"]:.3f})')
                print(f'        Perm p (Spearman) = {r["perm_p_spearman"]:.4f}')
                print(f'        MSE = {r["mse"]:.4f} '
                      f'(baseline: {r["mse_baseline"]:.4f}, '
                      f'reduction: {r["mse_reduction"]:.1%})')
                print(f'        CCC = {r["ccc"]:.3f}')
                print(f'        Per-HC rho: mean={r["per_hc_spearman_r_mean"]:.3f} '
                      f'sd={r["per_hc_spearman_r_sd"]:.3f}')

            # Landscape (optional)
            landscape = None
            if args.landscape and 'cone_1way' in args.models:
                print(f'\n    Computing cone_1way landscape (W-fixed)...')
                landscape = landscape_1d(hc_W, hc_amps, cvd_vuln, cvd_type)
                best_idx = np.argmax(landscape['spearman_r'])
                print(f'      Peak: Δλ={landscape["delta_range"][best_idx]}nm, '
                      f'r={landscape["spearman_r"][best_idx]:.3f}')

            # Save (merge with existing results if present)
            out_dir = Path(args.output_dir) / roi
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / f'sub-{cvd_subj}_loco_v2.json'

            # Load existing results to merge
            existing = {}
            if out_path.exists():
                with open(out_path) as f:
                    existing = json.load(f)

            # Merge fit_results and per_hc_diagnostics
            merged_fits = existing.get('fit_results', {})
            merged_fits.update(fit_result)
            merged_diag = existing.get('per_hc_diagnostics', {})
            merged_diag.update(per_hc_diag)

            result = {
                'subject': cvd_subj,
                'roi': roi,
                'cvd_type': cvd_type,
                'timestamp': datetime.now().isoformat(),
                'method': 'mean_hc_spearman_wfixed',
                'cvd_loco_target': cvd_vuln.tolist(),
                'hc_subjects': args.hc_subjects,
                'hc_alphas': hc_alphas,
                'fit_results': merged_fits,
                'per_hc_diagnostics': merged_diag,
            }
            # Preserve landscape if it exists
            if landscape is not None:
                result['landscape_cone_1way'] = landscape
            elif 'landscape_cone_1way' in existing:
                result['landscape_cone_1way'] = existing['landscape_cone_1way']

            with open(out_path, 'w') as f:
                json.dump(result, f, indent=2)
            print(f'    Saved: {out_path}')

    print('\nStep 1B (LOCO v2, W-fixed) complete.')


if __name__ == '__main__':
    main()
