#!/usr/bin/env python3
"""
preimage_separation_search.py — Task-oriented separation optimization for
colors where exact pre-image restoration is impossible (many-to-one forward
model regions).

Problem: At large Machado Δλ, the forward model D compresses hue space so that
multiple CIELab inputs map to the same opponent hue. Exact pre-image targets
become unreachable.

Solution: Instead of exact target restoration, maximize minimum pairwise
separation among ALL 8 perceived hues. Colors with exact pre-images (residual
< threshold) are kept fixed; merged colors are optimized.

Algorithm:
  1. Load exact pre-image result → identify merged colors (residual > threshold)
  2. Build dense forward model map D(θ) at 0.1° resolution
  3. For merged colors: differential evolution to maximize min pairwise
     separation in perceived (opponent) space
  4. Optional ordinal constraint: perceived order should match healthy order
  5. Report: separation metrics, comparison to healthy/unfiltered/exact-preimage

Usage (server):
    mpirun -np 1 python scripts/preimage_separation_search.py \
        --subject 09 --roi V4 --model machado_1way \
        --preimage_dir results/fits/preimage \
        --output_dir results/fits/preimage
"""

import argparse
import json
import numpy as np
import sys
import time
from datetime import datetime
from pathlib import Path
from scipy.optimize import differential_evolution

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
HUE_ANGLES_FLOAT = np.array([0, 45, 90, 135, 180, 225, 270, 315], dtype=float)
COLOR_NAMES = ['red', 'orange', 'yellow', 'green',
               'cyan', 'blue', 'purple', 'magenta']

MERGE_THRESHOLD_DEG = 1.0  # colors with residual > this are "merged"


# ---------------------------------------------------------------------------
# Forward model wrapper
# ---------------------------------------------------------------------------

def forward_model_at_angle(theta_input_deg, model_name, params, cvd_type):
    """Evaluate D(θ_input) → perceived hue angle."""
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


def _min_pairwise_circular_dist(angles):
    """Minimum pairwise circular distance among n angles."""
    angles = np.asarray(angles)
    n = len(angles)
    min_dist = 360.0
    for i in range(n):
        for j in range(i + 1, n):
            d = _circular_dist(angles[i], angles[j])
            if d < min_dist:
                min_dist = d
    return min_dist


# ---------------------------------------------------------------------------
# Dense forward model map
# ---------------------------------------------------------------------------

def build_dense_forward_map(model_name, params, cvd_type, resolution=0.1):
    """Pre-compute D(θ) at fine resolution for fast optimization.

    Returns:
        theta_grid: (N,) CIELab input angles
        perceived_grid: (N,) opponent output angles
    """
    theta_grid = np.arange(0, 360, resolution)
    perceived_grid = forward_model_at_angle(theta_grid, model_name,
                                            params, cvd_type)
    return theta_grid, perceived_grid


def interpolate_perceived(theta_in, theta_grid, perceived_grid):
    """Fast lookup of D(θ_in) via linear interpolation of dense map.

    Handles circularity: wraps theta_in to [0, 360) and uses the
    pre-computed grid.
    """
    theta_in = np.asarray(theta_in, dtype=float) % 360.0
    resolution = theta_grid[1] - theta_grid[0]
    idx = theta_in / resolution
    idx_lo = np.floor(idx).astype(int) % len(theta_grid)
    idx_hi = (idx_lo + 1) % len(theta_grid)
    frac = idx - np.floor(idx)

    # Linear interpolation with circular distance handling
    p_lo = perceived_grid[idx_lo]
    p_hi = perceived_grid[idx_hi]

    # Handle wraparound in perceived space
    diff = p_hi - p_lo
    # If diff > 180, wrap around (e.g., 350→10 should interpolate through 360)
    wrap_mask = diff > 180
    diff[wrap_mask] -= 360
    wrap_mask = diff < -180
    diff[wrap_mask] += 360

    result = (p_lo + frac * diff) % 360.0
    return result


# ---------------------------------------------------------------------------
# Characterize forward model landscape
# ---------------------------------------------------------------------------

def characterize_forward_model(theta_grid, perceived_grid, model_name,
                               params, cvd_type):
    """Analyze the forward model's image: range, monotonicity, degeneracy."""
    # Perceived range
    p_min, p_max = perceived_grid.min(), perceived_grid.max()

    # Find the minimum and maximum perceived hues
    idx_min = np.argmin(perceived_grid)
    idx_max = np.argmax(perceived_grid)
    theta_at_min = theta_grid[idx_min]
    theta_at_max = theta_grid[idx_max]

    # Normal-vision perceived angles (Δλ=0)
    hue_normal, _, _ = machado_shifted_hue_at(0.0, cvd_type, HUE_ANGLES_FLOAT)

    # Perceived at original 8 angles (current CVD perception)
    perceived_8 = forward_model_at_angle(HUE_ANGLES_FLOAT, model_name,
                                         params, cvd_type)

    # Pairwise separation at original angles
    min_sep_original = _min_pairwise_circular_dist(perceived_8)
    min_sep_healthy = _min_pairwise_circular_dist(hue_normal)

    return {
        'perceived_range': [float(p_min), float(p_max)],
        'perceived_span': float(_circular_dist(p_min, p_max)),
        'theta_at_min_perceived': float(theta_at_min),
        'theta_at_max_perceived': float(theta_at_max),
        'min_perceived': float(p_min),
        'max_perceived': float(p_max),
        'healthy_targets': hue_normal.tolist(),
        'perceived_at_original': perceived_8.tolist(),
        'min_sep_original': float(min_sep_original),
        'min_sep_healthy': float(min_sep_healthy),
    }


# ---------------------------------------------------------------------------
# Separation optimization
# ---------------------------------------------------------------------------

def optimize_separation(
    merged_indices,
    fixed_perceived,
    theta_grid,
    perceived_grid,
    healthy_targets,
    w_sep=1.0,
    w_target=0.1,
    w_order=0.5,
    maxiter=2000,
    popsize=40,
    seed=42,
):
    """Maximize minimum pairwise separation for merged colors.

    Objective (minimize):
      L = -w_sep * min_pairwise_sep
          + w_target * mean_dist_to_healthy
          + w_order * order_violation_penalty

    Args:
        merged_indices: list of indices (0-7) that need optimization
        fixed_perceived: dict {index: perceived_angle} for exact pre-image colors
        theta_grid: dense CIELab grid
        perceived_grid: dense D(θ) grid
        healthy_targets: (8,) normal-vision opponent hue angles
        w_sep: weight for separation objective
        w_target: weight for target proximity
        w_order: weight for ordinal constraint
        maxiter: DE maximum iterations
        popsize: DE population size
        seed: random seed

    Returns:
        dict with optimized angles, perceived hues, metrics
    """
    n_merged = len(merged_indices)
    fixed_indices = [i for i in range(8) if i not in merged_indices]

    # Determine healthy ordering for merged colors
    healthy_merged = np.array([healthy_targets[i] for i in merged_indices])
    # Sort indices by healthy perceived hue (ascending)
    healthy_order = np.argsort(healthy_merged)

    n_evals = [0]

    def objective(x):
        """x = [θ_in_0, θ_in_1, ...] for merged colors."""
        n_evals[0] += 1
        theta_merged = np.asarray(x) % 360.0
        perceived_merged = interpolate_perceived(theta_merged, theta_grid,
                                                 perceived_grid)

        # Assemble all 8 perceived angles
        all_perceived = np.zeros(8)
        for i, idx in enumerate(merged_indices):
            all_perceived[idx] = perceived_merged[i]
        for idx in fixed_indices:
            all_perceived[idx] = fixed_perceived[idx]

        # L_sep: negative min pairwise separation (to maximize)
        min_sep = _min_pairwise_circular_dist(all_perceived)
        L_sep = -min_sep

        # L_target: mean distance to healthy targets for merged colors
        target_dist = _circular_dist(
            perceived_merged,
            np.array([healthy_targets[i] for i in merged_indices])
        )
        L_target = float(np.mean(target_dist))

        # L_order: ordinal violation penalty
        # merged perceived should follow same ordering as healthy
        perceived_for_order = perceived_merged[healthy_order]
        # Check if perceived are in ascending circular order
        L_order = 0.0
        for k in range(len(perceived_for_order) - 1):
            # signed circular difference: should be positive (ascending)
            diff = (perceived_for_order[k + 1] -
                    perceived_for_order[k] + 180) % 360 - 180
            if diff < 0:
                L_order += abs(diff)

        loss = w_sep * L_sep + w_target * L_target + w_order * L_order
        return loss

    # Bounds: each θ_in ∈ [0, 360)
    bounds = [(0, 359.99)] * n_merged

    print(f'  Running DE optimization: {n_merged} merged colors, '
          f'popsize={popsize}, maxiter={maxiter}')
    t0 = time.time()

    result = differential_evolution(
        objective, bounds, maxiter=maxiter, popsize=popsize,
        seed=seed, tol=1e-8, atol=1e-8,
        mutation=(0.5, 1.5), recombination=0.9,
        workers=1, polish=True,
    )

    elapsed = time.time() - t0
    print(f'  DE converged: {result.success}, fun={result.fun:.4f}, '
          f'nit={result.nit}, nfev={n_evals[0]}, time={elapsed:.1f}s')

    # Extract optimized angles
    theta_opt = np.asarray(result.x) % 360.0
    perceived_opt = interpolate_perceived(theta_opt, theta_grid, perceived_grid)

    # Refine with exact forward model evaluation
    perceived_opt_exact = forward_model_at_angle(theta_opt, 'machado_1way',
                                                  [13.5], 'protan')
    # Actually, use proper model params — need to pass them
    # We'll refine in the main function

    return {
        'merged_indices': merged_indices,
        'theta_optimized': theta_opt.tolist(),
        'perceived_interpolated': perceived_opt.tolist(),
        'de_success': bool(result.success),
        'de_fun': float(result.fun),
        'de_nit': int(result.nit),
        'de_nfev': n_evals[0],
        'elapsed_s': elapsed,
        'weights': {'w_sep': w_sep, 'w_target': w_target, 'w_order': w_order},
    }


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run_separation_search(subj, roi, model_name, preimage_dir, output_dir):
    """Full separation optimization pipeline.

    1. Load existing pre-image result
    2. Identify merged colors
    3. Build dense forward map
    4. Optimize separation
    5. Assemble final result
    6. Compare to baselines
    7. Save JSON
    """
    cvd_type = CVD_TYPE[subj]
    preimage_path = (Path(preimage_dir) /
                     f'sub-{subj}_{roi}_{model_name}_preimage.json')

    print(f'{"=" * 60}')
    print(f'Task-Oriented Separation Search')
    print(f'Subject: sub-{subj} ({cvd_type}), Model: {model_name}')
    print(f'{"=" * 60}')

    # --- Load pre-image result ---
    with open(preimage_path) as f:
        preimage = json.load(f)

    params = preimage['phase_a_params']
    residuals = np.array(preimage['residuals'])
    preimage_angles = np.array(preimage['preimage_angles'])
    perceived_angles = np.array(preimage['perceived_angles'])
    target_opponent = np.array(preimage['target_angles_opponent'])

    print(f'\nPre-image residuals per color:')
    for i in range(8):
        flag = ' *** MERGED' if residuals[i] > MERGE_THRESHOLD_DEG else ''
        print(f'  c{i+1} ({COLOR_NAMES[i]:>7s}): {residuals[i]:8.4f}°{flag}')

    # --- Identify merged colors ---
    merged_indices = [i for i in range(8)
                      if residuals[i] > MERGE_THRESHOLD_DEG]
    fixed_indices = [i for i in range(8) if i not in merged_indices]

    if not merged_indices:
        print('\nNo merged colors — exact pre-image works for all 8!')
        print('No separation optimization needed.')
        return None

    print(f'\nMerged colors ({len(merged_indices)}): '
          f'{[f"c{i+1}({COLOR_NAMES[i]})" for i in merged_indices]}')
    print(f'Fixed colors ({len(fixed_indices)}): '
          f'{[f"c{i+1}({COLOR_NAMES[i]})" for i in fixed_indices]}')

    # --- Build dense forward model map ---
    print(f'\nBuilding dense forward model map (0.1° resolution)...')
    t0 = time.time()
    theta_grid, perceived_grid = build_dense_forward_map(
        model_name, params, cvd_type, resolution=0.1)
    print(f'  Done in {time.time() - t0:.1f}s, '
          f'{len(theta_grid)} grid points')

    # --- Characterize forward model landscape ---
    landscape = characterize_forward_model(
        theta_grid, perceived_grid, model_name, params, cvd_type)
    print(f'\nForward model landscape:')
    print(f'  Perceived range: [{landscape["min_perceived"]:.1f}°, '
          f'{landscape["max_perceived"]:.1f}°]')
    print(f'  Perceived span: {landscape["perceived_span"]:.1f}°')
    print(f'  Min separation (original): {landscape["min_sep_original"]:.2f}°')
    print(f'  Min separation (healthy): {landscape["min_sep_healthy"]:.2f}°')

    # --- Fixed perceived angles (from exact pre-image) ---
    fixed_perceived = {}
    for idx in fixed_indices:
        fixed_perceived[idx] = perceived_angles[idx]

    print(f'\nFixed perceived angles:')
    for idx in fixed_indices:
        print(f'  c{idx+1} ({COLOR_NAMES[idx]:>7s}): '
              f'perceived={perceived_angles[idx]:.2f}° '
              f'(target={target_opponent[idx]:.2f}°, '
              f'err={residuals[idx]:.4f}°)')

    # --- Run separation optimization ---
    print(f'\n--- Separation Optimization ---')
    de_result = optimize_separation(
        merged_indices, fixed_perceived,
        theta_grid, perceived_grid,
        target_opponent,
        w_sep=1.0, w_target=0.1, w_order=0.5,
        maxiter=2000, popsize=40, seed=42,
    )

    # --- Refine with exact forward model ---
    theta_merged_opt = np.array(de_result['theta_optimized'])
    perceived_merged_exact = forward_model_at_angle(
        theta_merged_opt, model_name, params, cvd_type)
    de_result['perceived_exact'] = perceived_merged_exact.tolist()

    # --- Assemble final 8-color result ---
    final_theta_in = np.copy(preimage_angles)
    final_perceived = np.copy(perceived_angles)

    for i, idx in enumerate(merged_indices):
        final_theta_in[idx] = theta_merged_opt[i]
        final_perceived[idx] = perceived_merged_exact[i]

    final_delta = (final_theta_in - HUE_ANGLES_FLOAT + 180) % 360 - 180
    final_residuals = _circular_dist(final_perceived, target_opponent)

    # --- Separation metrics ---
    min_sep_final = _min_pairwise_circular_dist(final_perceived)
    min_sep_preimage = _min_pairwise_circular_dist(perceived_angles)
    min_sep_unfiltered = landscape['min_sep_original']
    min_sep_healthy = landscape['min_sep_healthy']

    # Mean pairwise separation
    all_pairwise_final = []
    all_pairwise_unfilt = []
    all_pairwise_healthy = []
    perceived_orig_8 = np.array(landscape['perceived_at_original'])
    for i in range(8):
        for j in range(i + 1, 8):
            all_pairwise_final.append(
                _circular_dist(final_perceived[i], final_perceived[j]))
            all_pairwise_unfilt.append(
                _circular_dist(perceived_orig_8[i], perceived_orig_8[j]))
            all_pairwise_healthy.append(
                _circular_dist(target_opponent[i], target_opponent[j]))
    mean_sep_final = float(np.mean(all_pairwise_final))
    mean_sep_unfilt = float(np.mean(all_pairwise_unfilt))
    mean_sep_healthy = float(np.mean(all_pairwise_healthy))

    # Ordinal concordance (Spearman of perceived order vs healthy order)
    from scipy.stats import spearmanr
    rho_order, _ = spearmanr(final_perceived, target_opponent)

    # Mean distance to healthy targets
    mean_target_dist = float(np.mean(
        _circular_dist(final_perceived, target_opponent)))

    print(f'\n--- Final Result ---')
    print(f'\nPer-color angles:')
    print(f'  {"Color":>10s}  {"CIELab_in":>10s}  {"Perceived":>10s}  '
          f'{"Target":>10s}  {"Residual":>10s}  {"Type":>10s}')
    for i in range(8):
        ctype = 'exact' if i in fixed_indices else 'sep-opt'
        print(f'  c{i+1} {COLOR_NAMES[i]:>7s}  '
              f'{final_theta_in[i]:10.2f}  {final_perceived[i]:10.2f}  '
              f'{target_opponent[i]:10.2f}  {final_residuals[i]:10.3f}  '
              f'{ctype:>10s}')

    print(f'\nSeparation comparison:')
    print(f'  {"Condition":>20s}  {"Min Sep":>10s}  {"Mean Sep":>10s}')
    print(f'  {"Healthy (normal)":>20s}  {min_sep_healthy:10.2f}  '
          f'{mean_sep_healthy:10.2f}')
    print(f'  {"Unfiltered (CVD)":>20s}  {min_sep_unfiltered:10.2f}  '
          f'{mean_sep_unfilt:10.2f}')
    print(f'  {"Exact pre-image":>20s}  {min_sep_preimage:10.2f}  —')
    print(f'  {"Sep-optimized":>20s}  {min_sep_final:10.2f}  '
          f'{mean_sep_final:10.2f}')

    print(f'\nOrdinal concordance (ρ vs healthy): {rho_order:.3f}')
    print(f'Mean distance to healthy targets: {mean_target_dist:.2f}°')

    # Improvement ratios
    sep_improve_vs_unfilt = min_sep_final / max(min_sep_unfiltered, 0.01)
    sep_improve_vs_preimage = min_sep_final / max(min_sep_preimage, 0.01)

    print(f'\nImprovement ratios:')
    print(f'  Min sep vs unfiltered: {sep_improve_vs_unfilt:.2f}x')
    print(f'  Min sep vs exact preimage: {sep_improve_vs_preimage:.2f}x')

    # --- Generate design matrix ---
    basis_full = create_basis_full(N_CHANNELS, basis_type='fe')
    idx_final = np.round(final_perceived).astype(int) % 360
    C_final = basis_full[idx_final]

    # --- Save JSON ---
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    result = {
        'subject': subj,
        'cvd_type': cvd_type,
        'roi': roi,
        'model': model_name,
        'approach': 'task_oriented_separation',
        'phase_a_params': params,
        'merged_colors': {
            'indices': merged_indices,
            'names': [COLOR_NAMES[i] for i in merged_indices],
            'merge_threshold_deg': MERGE_THRESHOLD_DEG,
        },
        'fixed_colors': {
            'indices': fixed_indices,
            'names': [COLOR_NAMES[i] for i in fixed_indices],
        },
        'stimulus_angles_cielab': HUE_ANGLES_FLOAT.tolist(),
        'target_angles_opponent': target_opponent.tolist(),
        'final_theta_in': final_theta_in.tolist(),
        'final_perceived': final_perceived.tolist(),
        'final_residuals': final_residuals.tolist(),
        'final_delta': final_delta.tolist(),
        'separation_metrics': {
            'min_sep_healthy': float(min_sep_healthy),
            'min_sep_unfiltered': float(min_sep_unfiltered),
            'min_sep_exact_preimage': float(min_sep_preimage),
            'min_sep_optimized': float(min_sep_final),
            'mean_sep_healthy': mean_sep_healthy,
            'mean_sep_unfiltered': mean_sep_unfilt,
            'mean_sep_optimized': mean_sep_final,
            'improvement_vs_unfiltered': float(sep_improve_vs_unfilt),
            'improvement_vs_preimage': float(sep_improve_vs_preimage),
        },
        'ordinal_concordance_rho': float(rho_order),
        'mean_target_distance_deg': mean_target_dist,
        'forward_model_landscape': landscape,
        'de_optimization': de_result,
        'design_matrix': C_final.tolist(),
        'baselines': {
            'preimage_angles': preimage_angles.tolist(),
            'preimage_perceived': perceived_angles.tolist(),
            'preimage_residuals': residuals.tolist(),
            'unfiltered_perceived': landscape['perceived_at_original'],
        },
        'timestamp': datetime.now().isoformat(),
    }

    save_path = output_dir / f'sub-{subj}_{roi}_{model_name}_separation.json'
    with open(save_path, 'w') as f:
        json.dump(result, f, indent=2, default=str)
    print(f'\nSaved: {save_path}')

    # --- Summary ---
    print(f'\n{"=" * 60}')
    print(f'SEPARATION SUMMARY: sub-{subj} ({cvd_type})')
    print(f'{"=" * 60}')
    print(f'Merged colors: {len(merged_indices)}/8 '
          f'({[COLOR_NAMES[i] for i in merged_indices]})')
    print(f'Min separation: '
          f'{min_sep_unfiltered:.2f}° (unfilt) → '
          f'{min_sep_preimage:.2f}° (exact) → '
          f'{min_sep_final:.2f}° (optimized)')
    print(f'Ordinal concordance: ρ={rho_order:.3f}')
    print(f'Mean target distance: {mean_target_dist:.2f}°')
    print(f'{"=" * 60}')

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Task-oriented separation optimization for merged colors')
    parser.add_argument('--subject', required=True,
                        help='CVD subject ID (08, 09, or 10)')
    parser.add_argument('--roi', default='V4',
                        help='ROI (V4 for hV4)')
    parser.add_argument('--model', default='machado_1way',
                        help='Model name')
    parser.add_argument('--preimage_dir',
                        default='results/fits/preimage',
                        help='Pre-image results directory')
    parser.add_argument('--output_dir',
                        default='results/fits/preimage',
                        help='Output directory')
    args = parser.parse_args()

    run_separation_search(args.subject, args.roi, args.model,
                          args.preimage_dir, args.output_dir)


if __name__ == '__main__':
    main()
