#!/usr/bin/env python3
"""
preimage_filter_search.py — Pre-image filter search + Fourier approximation.

Instead of inverting the Phase A delta (δ_filter = -δ_fit, which FAILED),
this script numerically finds the pre-image input θ_in such that D(θ_in) ≈ θ_target,
where D is the fitted forward distortion model.

Subject-specific forward models:
  sub-08 → R+C (rc_opponent): params=[Δλ, g]
  sub-09 → Machado (machado_1way): params=[Δλ]
  sub-10 → both (specificity check — expect identity)

Tiered evaluation:
  Tier 1: Model-consistent residual (necessary condition)
  Tier 2: Geometric correction profile (primary reportable)

Usage (server):
    mpirun -np 1 python scripts/preimage_filter_search.py \
        --subject 08 --roi V4 --model rc_opponent \
        --phase_a_dir results/loco_filter/phase_a \
        --output_dir results/loco_filter/preimage
"""

import argparse
import json
import numpy as np
import sys
import time
from datetime import datetime
from pathlib import Path
from scipy.optimize import minimize_scalar

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR))

_FWD_DIR = str(Path(__file__).resolve().parent.parent.parent.parent
               / 'future_phase1_forward_model' / 'scripts')
sys.path.insert(0, _FWD_DIR)

from machado_simulator import machado_shifted_hue_at  # noqa: E402
from retinal_cortical import machado_with_opponent_gain_at  # noqa: E402
from utils_forward_model import create_basis_full, N_CHANNELS  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CVD_TYPE = {'08': 'deutan', '09': 'protan', '10': 'normal'}
PRIMARY_MODEL = {'08': 'rc_opponent', '09': 'machado_1way', '10': 'machado_1way'}
HUE_ANGLES_FLOAT = np.array([0, 45, 90, 135, 180, 225, 270, 315], dtype=float)
COLOR_NAMES = ['red', 'orange', 'yellow', 'green',
               'cyan', 'blue', 'purple', 'magenta']


# ---------------------------------------------------------------------------
# Forward model wrapper (subject-specific)
# ---------------------------------------------------------------------------

def forward_model_at_angle(theta_input_deg, model_name, params, cvd_type):
    """Evaluate D(θ_input) → perceived hue angle.

    Creates CIELab at (L*=75, C=40, θ_input), runs through model.

    Args:
        theta_input_deg: input hue angle(s) in degrees
        model_name: 'rc_opponent' or 'machado_1way'
        params: model parameters (list)
        cvd_type: 'protan', 'deutan', or 'normal'

    Returns:
        perceived: hue angle(s) in [0, 360)
    """
    theta = np.atleast_1d(np.asarray(theta_input_deg, dtype=float))

    if model_name == 'machado_1way':
        dl = float(params[0])
        _, hue_shifted, _ = machado_shifted_hue_at(dl, cvd_type, theta)
        return hue_shifted

    elif model_name == 'rc_opponent':
        dl, g = float(params[0]), float(params[1])
        _, hue_final, _ = machado_with_opponent_gain_at(
            dl, g, cvd_type, theta)
        return hue_final

    else:
        raise ValueError(f'Unknown model: {model_name}')


def _circular_dist(a, b):
    """Unsigned circular distance in [0, 180]."""
    d = np.abs(a - b)
    return np.minimum(d, 360.0 - d)


# ---------------------------------------------------------------------------
# Pre-image search per color
# ---------------------------------------------------------------------------

def search_preimage(theta_target, model_name, params, cvd_type,
                    grid_step=1.0):
    """Find θ_in such that D(θ_in) ≈ θ_target.

    Algorithm:
    1. Coarse grid: evaluate D at [0, 1, 2, ..., 359]°
    2. Find grid point minimizing circular_dist(D(θ), θ_target)
    3. Refine with scipy.optimize.minimize_scalar (Brent) in ±5° bracket

    Args:
        theta_target: target hue angle in degrees
        model_name: forward model name
        params: model parameters
        cvd_type: CVD type
        grid_step: coarse grid step in degrees

    Returns:
        dict with theta_in, theta_perceived, residual_deg, n_evals
    """
    n_evals = [0]

    # Step 1: Coarse grid
    grid = np.arange(0, 360, grid_step)
    perceived_grid = forward_model_at_angle(grid, model_name, params, cvd_type)
    n_evals[0] += len(grid)

    errors = _circular_dist(perceived_grid, theta_target)
    best_idx = np.argmin(errors)
    theta_coarse = grid[best_idx]

    # Step 2: Brent refinement in ±5° bracket
    bracket_half = 5.0

    def objective(theta_in):
        n_evals[0] += 1
        perceived = forward_model_at_angle(theta_in, model_name, params, cvd_type)
        return float(_circular_dist(perceived, theta_target))

    lo = theta_coarse - bracket_half
    hi = theta_coarse + bracket_half

    result = minimize_scalar(objective, bounds=(lo, hi), method='bounded',
                             options={'xatol': 0.001, 'maxiter': 50})

    theta_in = float(result.x) % 360.0
    perceived = forward_model_at_angle(theta_in, model_name, params, cvd_type)
    residual = float(_circular_dist(perceived, theta_target))

    return {
        'theta_in': theta_in,
        'theta_perceived': float(perceived[0]) if perceived.ndim > 0 else float(perceived),
        'residual_deg': residual,
        'n_evals': n_evals[0],
    }


# ---------------------------------------------------------------------------
# Fourier approximation layer
# ---------------------------------------------------------------------------

def fit_fourier_approximation(theta_original, delta_preimage, n_harmonics=2):
    """Fit Fourier to exact pre-image corrections (approximation layer).

    δ(θ) = a₁sin(θ) + b₁cos(θ) + a₂sin(2θ) + b₂cos(2θ)
    Least squares fit to 8 points → 4 coefficients.

    Args:
        theta_original: (8,) original hue angles in degrees
        delta_preimage: (8,) exact pre-image corrections (θ_in - θ_original)
        n_harmonics: number of Fourier harmonics (default 2 → 4 DOF)

    Returns:
        dict with coeffs, delta_smooth, rmse_vs_exact
    """
    theta_rad = np.deg2rad(theta_original)
    cols = []
    for k in range(1, n_harmonics + 1):
        cols.append(np.sin(k * theta_rad))
        cols.append(np.cos(k * theta_rad))
    X = np.column_stack(cols)

    # OLS fit
    coeffs, residuals, _, _ = np.linalg.lstsq(X, delta_preimage, rcond=None)
    delta_smooth = X @ coeffs
    rmse = float(np.sqrt(np.mean((delta_smooth - delta_preimage) ** 2)))

    # Named coefficients
    coeff_names = []
    for k in range(1, n_harmonics + 1):
        coeff_names.extend([f'a{k}', f'b{k}'])
    coeffs_dict = {name: float(c) for name, c in zip(coeff_names, coeffs)}

    return {
        'coeffs': coeffs_dict,
        'coeffs_array': coeffs.tolist(),
        'delta_smooth': delta_smooth.tolist(),
        'rmse_vs_exact': rmse,
        'n_harmonics': n_harmonics,
    }


def eval_fourier(theta_deg, coeffs_dict, n_harmonics=2):
    """Evaluate Fourier correction at arbitrary angles.

    Args:
        theta_deg: angle(s) in degrees
        coeffs_dict: {a1, b1, a2, b2, ...}
        n_harmonics: number of harmonics

    Returns:
        delta: correction(s) in degrees
    """
    theta_rad = np.deg2rad(theta_deg)
    delta = np.zeros_like(theta_rad)
    for k in range(1, n_harmonics + 1):
        delta += coeffs_dict[f'a{k}'] * np.sin(k * theta_rad)
        delta += coeffs_dict[f'b{k}'] * np.cos(k * theta_rad)
    return delta


# ---------------------------------------------------------------------------
# Model-consistent check (Tier 1)
# ---------------------------------------------------------------------------

def check_model_consistent(preimage_results, model_name, params, cvd_type,
                           fourier_result=None, targets_opponent=None):
    """Compose pre-image through forward model, check residuals.

    For each color:
      perceived = D(θ_in*)
      error = circular_dist(perceived, θ_target_opponent)

    Also check Fourier approximation if provided.

    Args:
        targets_opponent: (8,) normal-vision opponent hue angles.
            If None, computed internally.

    Returns:
        dict with per-color errors, mean/max error, exact vs approx
    """
    if targets_opponent is None:
        targets_opponent, _, _ = machado_shifted_hue_at(
            0.0, cvd_type, HUE_ANGLES_FLOAT)

    errors_exact = []
    for pr in preimage_results:
        errors_exact.append(pr['residual_deg'])
    errors_exact = np.array(errors_exact)

    result = {
        'exact_per_color_error': errors_exact.tolist(),
        'exact_mean_error': float(np.mean(errors_exact)),
        'exact_max_error': float(np.max(errors_exact)),
        'exact_pass': bool(np.mean(errors_exact) < 0.5),
    }

    if fourier_result is not None:
        delta_fourier = np.array(fourier_result['delta_smooth'])
        theta_approx = (HUE_ANGLES_FLOAT + delta_fourier) % 360.0

        perceived_approx = forward_model_at_angle(
            theta_approx, model_name, params, cvd_type)
        errors_approx = _circular_dist(perceived_approx, targets_opponent)

        result['fourier_per_color_error'] = errors_approx.tolist()
        result['fourier_mean_error'] = float(np.mean(errors_approx))
        result['fourier_max_error'] = float(np.max(errors_approx))
        result['fourier_pass'] = bool(np.mean(errors_approx) < 3.0)

    return result


# ---------------------------------------------------------------------------
# Main flow
# ---------------------------------------------------------------------------

def load_phase_a_result(phase_a_dir, subj, roi, model_name):
    """Load Phase A JSON result."""
    path = Path(phase_a_dir) / f'sub-{subj}_{roi}_{model_name}.json'
    with open(path) as f:
        return json.load(f)


def run_preimage_search(subj, roi, model_name, phase_a_dir, output_dir):
    """Full pre-image search pipeline for one subject.

    Steps:
    1. Load Phase A → model params
    2. For each target color: search pre-image θ_in*
    3. Compute δ_preimage = θ_in* - θ_original
    4. Fit Fourier approximation
    5. Check model-consistent (Tier 1)
    6. Report geometric correction (Tier 2)
    7. Save JSON
    """
    cvd_type = CVD_TYPE[subj]

    print(f'=== Pre-Image Filter Search ===')
    print(f'Subject: sub-{subj} ({cvd_type}), ROI: {roi}')
    print(f'Model: {model_name}')

    # --- Load Phase A ---
    phase_a = load_phase_a_result(phase_a_dir, subj, roi, model_name)
    best_params = phase_a['best_params']
    perm_p = phase_a['permutation']['label_perm_p']
    rho_fit = phase_a['permutation']['spearman_r']

    print(f'\nPhase A: params={best_params}, rho={rho_fit:.3f}, p={perm_p:.4f}')

    # --- Normal-vision opponent hue targets ---
    # D_normal(θ_original) = opponent hue angles a normal observer perceives
    # These are the CORRECT targets: D_CVD(θ_in) should match these.
    hue_normal_opponent, _, _ = machado_shifted_hue_at(
        0.0, cvd_type, HUE_ANGLES_FLOAT)

    # --- Evaluate forward model at original 8 angles (sanity) ---
    perceived_original = forward_model_at_angle(
        HUE_ANGLES_FLOAT, model_name, best_params, cvd_type)
    delta_fit_opponent = _circular_dist(perceived_original, hue_normal_opponent)
    print(f'Normal-vision opponent targets:')
    print(f'  {np.round(hue_normal_opponent, 1).tolist()}')
    print(f'Forward model at original angles (CVD perception):')
    print(f'  Perceived: {np.round(perceived_original, 1).tolist()}')
    print(f'  Dist from normal: {np.round(delta_fit_opponent, 1).tolist()}')

    # --- Pre-image search for each target color ---
    # Target = normal opponent hue (same coordinate system as D output)
    print(f'\nSearching pre-images (targets in opponent hue space)...')
    t0 = time.time()
    preimage_results = []
    for i, theta_target in enumerate(hue_normal_opponent):
        pr = search_preimage(theta_target, model_name, best_params, cvd_type)
        preimage_results.append(pr)
        print(f'  c{i+1} ({COLOR_NAMES[i]:>7s}): '
              f'target={theta_target:5.1f}°, '
              f'θ_in={pr["theta_in"]:6.2f}°, '
              f'perceived={pr["theta_perceived"]:6.2f}°, '
              f'residual={pr["residual_deg"]:.4f}°')
    elapsed = time.time() - t0
    print(f'  Done in {elapsed:.1f}s')

    # --- Compute delta_preimage ---
    theta_in_arr = np.array([pr['theta_in'] for pr in preimage_results])
    delta_preimage = (theta_in_arr - HUE_ANGLES_FLOAT + 180) % 360 - 180

    print(f'\nPre-image corrections (δ_preimage = θ_in - θ_original):')
    for i, (d, name) in enumerate(zip(delta_preimage, COLOR_NAMES)):
        print(f'  c{i+1} ({name:>7s}): {d:+7.2f}°')
    print(f'  Mean |correction|: {np.mean(np.abs(delta_preimage)):.2f}°')
    print(f'  Max  |correction|: {np.max(np.abs(delta_preimage)):.2f}°')

    # --- Fourier approximation ---
    fourier = fit_fourier_approximation(HUE_ANGLES_FLOAT, delta_preimage)
    print(f'\nFourier approximation (4-DOF):')
    print(f'  Coefficients: {fourier["coeffs"]}')
    print(f'  RMSE vs exact: {fourier["rmse_vs_exact"]:.3f}°')
    print(f'  Smooth δ: {np.round(fourier["delta_smooth"], 2).tolist()}')

    # --- Tier 1: Model-consistent check ---
    tier1 = check_model_consistent(
        preimage_results, model_name, best_params, cvd_type,
        fourier_result=fourier, targets_opponent=hue_normal_opponent)
    print(f'\nTier 1: Model-consistent check')
    print(f'  Exact lookup: mean={tier1["exact_mean_error"]:.4f}°, '
          f'max={tier1["exact_max_error"]:.4f}° → '
          f'{"PASS" if tier1["exact_pass"] else "FAIL"}')
    if 'fourier_mean_error' in tier1:
        print(f'  Fourier approx: mean={tier1["fourier_mean_error"]:.2f}°, '
              f'max={tier1["fourier_max_error"]:.2f}° → '
              f'{"PASS" if tier1["fourier_pass"] else "FAIL"}')

    # --- Tier 2: Geometric correction profile ---
    tier2 = {
        'delta_preimage': delta_preimage.tolist(),
        'mean_correction': float(np.mean(np.abs(delta_preimage))),
        'max_correction': float(np.max(np.abs(delta_preimage))),
        'fourier_rmse': fourier['rmse_vs_exact'],
    }
    print(f'\nTier 2: Geometric correction profile')
    print(f'  Mean |correction|: {tier2["mean_correction"]:.2f}°')
    print(f'  Max  |correction|: {tier2["max_correction"]:.2f}°')

    # --- Generate filtered design matrix for downstream use ---
    # Design matrix indexes by PERCEIVED opponent hue (what the brain represents)
    basis_full = create_basis_full(N_CHANNELS, basis_type='fe')
    perceived_arr = np.array([pr['theta_perceived'] for pr in preimage_results])
    idx_preimage = np.round(perceived_arr).astype(int) % 360
    C_preimage = basis_full[idx_preimage]

    # Fourier approximation design (also through forward model)
    delta_fourier = np.array(fourier['delta_smooth'])
    theta_fourier = (HUE_ANGLES_FLOAT + delta_fourier) % 360
    perceived_fourier = forward_model_at_angle(
        theta_fourier, model_name, best_params, cvd_type)
    idx_fourier = np.round(perceived_fourier).astype(int) % 360
    C_fourier = basis_full[idx_fourier]

    # --- Save JSON ---
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    result = {
        'subject': subj,
        'cvd_type': cvd_type,
        'roi': roi,
        'model': model_name,
        'phase_a_params': best_params,
        'phase_a_rho': rho_fit,
        'phase_a_perm_p': perm_p,
        'stimulus_angles_cielab': HUE_ANGLES_FLOAT.tolist(),
        'target_angles_opponent': hue_normal_opponent.tolist(),
        'preimage_angles': theta_in_arr.tolist(),
        'perceived_angles': [pr['theta_perceived'] for pr in preimage_results],
        'residuals': [pr['residual_deg'] for pr in preimage_results],
        'delta_preimage': delta_preimage.tolist(),
        'fourier_approx': fourier,
        'tier1_model_consistent': tier1,
        'tier2_geometric': tier2,
        'design_matrix_preimage': C_preimage.tolist(),
        'design_matrix_fourier': C_fourier.tolist(),
        'theta_fourier_cielab': theta_fourier.tolist(),
        'theta_fourier_perceived': perceived_fourier.tolist(),
        'forward_model_at_original': {
            'perceived': perceived_original.tolist(),
        },
        'elapsed_s': elapsed,
        'timestamp': datetime.now().isoformat(),
    }

    save_path = output_dir / f'sub-{subj}_{roi}_{model_name}_preimage.json'
    with open(save_path, 'w') as f:
        json.dump(result, f, indent=2, default=str)
    print(f'\nSaved: {save_path}')

    # --- Summary ---
    print(f'\n{"=" * 60}')
    print(f'PRE-IMAGE SUMMARY: sub-{subj} ({cvd_type})')
    print(f'{"=" * 60}')
    print(f'Model: {model_name}, params={best_params}')
    print(f'Tier 1 (model-consistent): '
          f'{"PASS" if tier1["exact_pass"] else "FAIL"} '
          f'(mean err={tier1["exact_mean_error"]:.4f}°)')
    print(f'Tier 2 (correction magnitude): '
          f'mean={tier2["mean_correction"]:.2f}°, '
          f'max={tier2["max_correction"]:.2f}°')
    print(f'Fourier RMSE: {fourier["rmse_vs_exact"]:.3f}°')
    if 'fourier_pass' in tier1:
        print(f'Fourier through-model: '
              f'{"PASS" if tier1["fourier_pass"] else "FAIL"} '
              f'(mean err={tier1["fourier_mean_error"]:.2f}°)')
    print(f'{"=" * 60}')

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Pre-image filter search + Fourier approximation')
    parser.add_argument('--subject', required=True,
                        help='CVD subject ID (08, 09, or 10)')
    parser.add_argument('--roi', default='V4',
                        help='ROI (V4 for hV4)')
    parser.add_argument('--model', default=None,
                        help='Model name (default: auto-select primary)')
    parser.add_argument('--phase_a_dir', default='results/loco_filter/phase_a',
                        help='Phase A results directory')
    parser.add_argument('--output_dir', default='results/loco_filter/preimage',
                        help='Output directory')
    args = parser.parse_args()

    subj = args.subject
    model_name = args.model or PRIMARY_MODEL.get(subj)
    if model_name is None:
        print(f'ERROR: No primary model defined for sub-{subj}')
        sys.exit(1)

    run_preimage_search(subj, args.roi, model_name,
                        args.phase_a_dir, args.output_dir)


if __name__ == '__main__':
    main()
