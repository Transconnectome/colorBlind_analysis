#!/usr/bin/env python3
"""
evaluate_preimage_filter.py — Cross-sim sanity + L_improve diagnostic for pre-image filter.

Tier 3: cross_sim_sanity — Machado severity sweep confirms improvement direction.
        NOT proof — sanity check only.
Tier 4: L_improve diagnostic — Internal consistency check (circular: same model
        for derivation and evaluation).

Also builds a comparison table: no-filter / simple-inverse / exact pre-image.

Usage (server):
    mpirun -np 1 python scripts/evaluate_preimage_filter.py \
        --preimage_dir results/fits/preimage \
        --data_dir /scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010 \
        --output_dir results/fits/preimage/evaluation
"""

import argparse
import json
import numpy as np
import sys
import time
from datetime import datetime
from pathlib import Path
from scipy.stats import spearmanr

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR.parent))

_FWD_DIR = str(Path(__file__).resolve().parent.parent.parent.parent
               / 'phase4_forward_model' / 'scripts')
sys.path.insert(0, _FWD_DIR)

from machado_simulator import machado_shifted_hue_at  # noqa: E402
from preimage_filter_search import (  # noqa: E402
    forward_model_at_angle, _circular_dist,
    HUE_ANGLES_FLOAT, CVD_TYPE, COLOR_NAMES,
)
from utils_forward_model import (  # noqa: E402
    HC_SUBJECTS, N_CHANNELS, N_RUNS, N_COLORS,
    HUE_ANGLES, load_amplitudes, create_basis_full,
)
from step1_fit_loco_v2 import (  # noqa: E402
    simulate_mean_hc_loco_legacy,
    precompute_hc_W,
    load_cvd_loco_target,
)

LOCAL_DATA = (Path(__file__).resolve().parent.parent.parent.parent
              / 'phase1_procrustes_decoding' / 'results'
              / 'visualization' / 'full_dataset_C010_with_residuals')
SERVER_DATA = Path(
    '/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010')


# ---------------------------------------------------------------------------
# Tier 3: Cross-simulator sanity
# ---------------------------------------------------------------------------

def cross_sim_sanity(preimage_angles, delta_lambda_range,
                     cvd_type):
    """Evaluate pre-image correction under Machado at various Δλ.

    For each Δλ ∈ delta_lambda_range:
      For each condition ∈ {unfiltered, preimage, simple_inverse}:
        perceived = machado_shifted_hue_at(Δλ, cvd_type, condition_angles)
        error = mean circular_dist(perceived, normal_opponent_hue)

    Errors measured against normal-vision OPPONENT hue angles
    (same coordinate system as machado output).

    Purpose: sanity check — NOT proof of restoration.

    Args:
        preimage_angles: (8,) pre-image input angles (CIELab)
        delta_lambda_range: array of Δλ values to sweep
        cvd_type: 'protan' or 'deutan'

    Returns:
        dict with arrays for plotting
    """
    theta_original = HUE_ANGLES_FLOAT

    # Normal-vision opponent hue targets (reference for error measurement)
    hue_normal_opponent, _, _ = machado_shifted_hue_at(
        0.0, cvd_type, theta_original)

    # Simple inverse = 2*original - preimage (mirror around original in CIELab)
    delta_preimage = (preimage_angles - theta_original + 180) % 360 - 180
    simple_inverse_angles = (theta_original - delta_preimage) % 360

    errors_unfiltered = []
    errors_preimage = []
    errors_inverse = []

    for dl in delta_lambda_range:
        # Unfiltered: what CVD perceives at original stimuli
        _, perceived_unf, _ = machado_shifted_hue_at(
            float(dl), cvd_type, theta_original)
        err_unf = float(np.mean(_circular_dist(
            perceived_unf, hue_normal_opponent)))

        # Pre-image: what CVD perceives at corrected stimuli
        _, perceived_pre, _ = machado_shifted_hue_at(
            float(dl), cvd_type, preimage_angles)
        err_pre = float(np.mean(_circular_dist(
            perceived_pre, hue_normal_opponent)))

        # Simple inverse: what CVD perceives at simple-inverse stimuli
        _, perceived_inv, _ = machado_shifted_hue_at(
            float(dl), cvd_type, simple_inverse_angles)
        err_inv = float(np.mean(_circular_dist(
            perceived_inv, hue_normal_opponent)))

        errors_unfiltered.append(err_unf)
        errors_preimage.append(err_pre)
        errors_inverse.append(err_inv)

    return {
        'delta_lambda_range': delta_lambda_range.tolist(),
        'error_unfiltered': errors_unfiltered,
        'error_preimage': errors_preimage,
        'error_simple_inverse': errors_inverse,
        'preimage_angles': preimage_angles.tolist(),
        'simple_inverse_angles': simple_inverse_angles.tolist(),
        'normal_opponent_targets': hue_normal_opponent.tolist(),
    }


# ---------------------------------------------------------------------------
# Tier 4: L_improve diagnostic
# ---------------------------------------------------------------------------

def l_improve_diagnostic(hc_amps_dict, preimage_angles,
                         model_name, params, cvd_type,
                         vuln_cvd, method='shift_at_both'):
    """L_improve with correct perceived-angle chain.

    DIAGNOSTIC ONLY — uses same fitted simulator for both derivation and
    evaluation, so this is an internal consistency check, not independent
    evidence.

    Step 1: θ_physical = preimage_angles (what we show to CVD)
    Step 2: θ_perceived = D(θ_physical) (what CVD perceives — should ≈ original)
    Step 3: C_perceived = basis_full[round(θ_perceived)]
    Step 4: vuln_perceived = simulate_LOCO(hc_amps, C_perceived)

    Compare to:
    - CVD baseline: vuln at D(θ_original) — current CVD state
    - HC baseline: vuln at θ_original (upper bound)
    """
    basis_full = create_basis_full(N_CHANNELS, basis_type='fe')
    C_original = basis_full[HUE_ANGLES]

    # HC baseline: LOCO at original (unshifted) angles
    vuln_hc_baseline, _ = simulate_mean_hc_loco_legacy(hc_amps_dict, C_original)

    # CVD baseline: LOCO at what CVD currently perceives
    perceived_current = forward_model_at_angle(
        HUE_ANGLES_FLOAT, model_name, params, cvd_type)
    idx_current = np.round(perceived_current).astype(int) % 360
    C_current = basis_full[idx_current]
    vuln_cvd_sim, _ = simulate_mean_hc_loco_legacy(hc_amps_dict, C_current)

    # Pre-image filtered: LOCO at what CVD perceives after filter
    perceived_filtered = forward_model_at_angle(
        preimage_angles, model_name, params, cvd_type)
    idx_filtered = np.round(perceived_filtered).astype(int) % 360
    C_filtered = basis_full[idx_filtered]
    vuln_filtered, _ = simulate_mean_hc_loco_legacy(hc_amps_dict, C_filtered)

    # Per-color improvement (filtered vs CVD baseline)
    delta_v = vuln_filtered - vuln_cvd_sim

    # L_improve: overall improvement
    l_improve = float(np.mean(delta_v))

    # Correlation with actual CVD vulnerability
    rho_baseline, _ = spearmanr(vuln_cvd_sim, vuln_cvd)
    rho_filtered, _ = spearmanr(vuln_filtered, vuln_cvd)
    rho_hc, _ = spearmanr(vuln_hc_baseline, vuln_cvd)

    return {
        'vuln_hc_baseline': vuln_hc_baseline.tolist(),
        'vuln_cvd_sim': vuln_cvd_sim.tolist(),
        'vuln_filtered': vuln_filtered.tolist(),
        'vuln_cvd_actual': vuln_cvd.tolist(),
        'delta_v': delta_v.tolist(),
        'l_improve': l_improve,
        'l_improve_positive': l_improve > 0,
        'rho_hc_vs_cvd': float(rho_hc) if np.isfinite(rho_hc) else 0.0,
        'rho_cvdsim_vs_cvd': float(rho_baseline) if np.isfinite(rho_baseline) else 0.0,
        'rho_filtered_vs_cvd': float(rho_filtered) if np.isfinite(rho_filtered) else 0.0,
        'perceived_current': perceived_current.tolist(),
        'perceived_filtered': perceived_filtered.tolist(),
        'flag': 'DIAGNOSTIC — circular evaluation (same model for derivation and evaluation)',
    }


# ---------------------------------------------------------------------------
# Comparison table
# ---------------------------------------------------------------------------

def build_comparison_table(preimage_result, model_name, params, cvd_type,
                           phase_b_path=None):
    """Compare 3 conditions:
    1. No filter (identity) — current CVD perception
    2. Simple inverse (-δ_fit) — confirmed failure from Phase B
    3. Exact pre-image lookup — this pipeline's output

    Errors measured against normal-vision OPPONENT hue angles.
    Fourier approximation reported as quality-of-fit to (3), not separate.
    """
    theta_original = HUE_ANGLES_FLOAT
    preimage_angles = np.array(preimage_result['preimage_angles'])

    # Normal-vision opponent hue targets
    hue_normal_opponent, _, _ = machado_shifted_hue_at(
        0.0, cvd_type, theta_original)

    # Simple inverse from Phase A delta_theta (in opponent space)
    perceived_at_original = forward_model_at_angle(
        theta_original, model_name, params, cvd_type)
    delta_fit_opponent = (perceived_at_original - hue_normal_opponent + 180) % 360 - 180
    # Invert in CIELab: shift original angles by -delta_fit in CIELab
    # (This is the naive approach that Phase B tried and failed)
    delta_fit_cielab = (perceived_at_original - theta_original + 180) % 360 - 180
    simple_inverse_angles = (theta_original - delta_fit_cielab) % 360

    # Evaluate each condition through the forward model
    conditions = {}

    # 1. No filter — error = how far CVD perception is from normal
    perceived_nofilt = perceived_at_original
    err_nofilt = _circular_dist(perceived_nofilt, hue_normal_opponent)
    conditions['no_filter'] = {
        'input_angles': theta_original.tolist(),
        'perceived_angles': perceived_nofilt.tolist(),
        'per_color_error': err_nofilt.tolist(),
        'mean_error': float(np.mean(err_nofilt)),
        'max_error': float(np.max(err_nofilt)),
    }

    # 2. Simple inverse
    perceived_inv = forward_model_at_angle(
        simple_inverse_angles, model_name, params, cvd_type)
    err_inv = _circular_dist(perceived_inv, hue_normal_opponent)
    conditions['simple_inverse'] = {
        'input_angles': simple_inverse_angles.tolist(),
        'perceived_angles': perceived_inv.tolist(),
        'per_color_error': err_inv.tolist(),
        'mean_error': float(np.mean(err_inv)),
        'max_error': float(np.max(err_inv)),
    }

    # 3. Exact pre-image
    perceived_pre = forward_model_at_angle(
        preimage_angles, model_name, params, cvd_type)
    err_pre = _circular_dist(perceived_pre, hue_normal_opponent)
    conditions['exact_preimage'] = {
        'input_angles': preimage_angles.tolist(),
        'perceived_angles': perceived_pre.tolist(),
        'per_color_error': err_pre.tolist(),
        'mean_error': float(np.mean(err_pre)),
        'max_error': float(np.max(err_pre)),
    }

    # Load Phase B result if available
    if phase_b_path and Path(phase_b_path).exists():
        with open(phase_b_path) as f:
            phase_b = json.load(f)
        conditions['phase_b_inverse'] = {
            'verdict': phase_b.get('verdict', 'unknown'),
            'delta_filter': phase_b.get('delta_filter_constrained', []),
        }

    return conditions


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Evaluate pre-image filter: cross-sim + L_improve diagnostic')
    parser.add_argument('--preimage_dir', required=True,
                        help='Directory with preimage JSON files')
    parser.add_argument('--data_dir', default=None,
                        help='Path to C010 data (for L_improve)')
    parser.add_argument('--output_dir', default=None,
                        help='Output dir (default: preimage_dir/evaluation)')
    parser.add_argument('--phase_b_dir', default=None,
                        help='Phase B results for comparison')
    parser.add_argument('--dl_min', type=float, default=0.0,
                        help='Min Δλ for cross-sim sweep')
    parser.add_argument('--dl_max', type=float, default=25.0,
                        help='Max Δλ for cross-sim sweep')
    parser.add_argument('--dl_step', type=float, default=0.5,
                        help='Step for cross-sim sweep')
    args = parser.parse_args()

    preimage_dir = Path(args.preimage_dir)
    output_dir = Path(args.output_dir) if args.output_dir else preimage_dir / 'evaluation'
    output_dir.mkdir(parents=True, exist_ok=True)

    # Discover preimage JSON files
    preimage_files = sorted(preimage_dir.glob('*_preimage.json'))
    if not preimage_files:
        print(f'ERROR: No preimage JSON files found in {preimage_dir}')
        sys.exit(1)

    print(f'Found {len(preimage_files)} preimage results')

    # Auto-detect data path for L_improve
    if args.data_dir:
        data_dir = Path(args.data_dir)
    elif SERVER_DATA.exists():
        data_dir = SERVER_DATA
    elif LOCAL_DATA.exists():
        data_dir = LOCAL_DATA
    else:
        print('WARNING: C010 data not found, L_improve will be skipped')
        data_dir = None

    # Load HC amplitudes once
    hc_amps_dict = None
    if data_dir is not None:
        hc_amps_dict = {}
        # Detect ROI from first file
        with open(preimage_files[0]) as f:
            first = json.load(f)
        roi = first['roi']
        for hc in HC_SUBJECTS:
            hc_amps_dict[hc] = load_amplitudes(data_dir, hc, roi)
        print(f'Loaded {len(hc_amps_dict)} HC subjects for {roi}')

    dl_range = np.arange(args.dl_min, args.dl_max + args.dl_step * 0.5,
                         args.dl_step)

    all_cross_sim = {}
    all_l_improve = {}
    all_comparison = {}

    for pf in preimage_files:
        with open(pf) as f:
            preimage = json.load(f)

        subj = preimage['subject']
        roi = preimage['roi']
        model_name = preimage['model']
        cvd_type = preimage['cvd_type']
        params = preimage['phase_a_params']
        preimage_angles = np.array(preimage['preimage_angles'])

        key = f'sub-{subj}_{roi}_{model_name}'
        print(f'\n=== Evaluating {key} ===')

        # --- Tier 3: Cross-sim sanity ---
        if cvd_type != 'normal':
            print(f'  Cross-sim sanity (Machado Δλ sweep)...')
            cs = cross_sim_sanity(preimage_angles, dl_range, cvd_type)

            # Find fitted Δλ for annotation
            fitted_dl = float(params[0])
            # Find nearest index
            dl_idx = int(np.argmin(np.abs(dl_range - fitted_dl)))
            print(f'  At fitted Δλ={fitted_dl}nm:')
            print(f'    Unfiltered error: {cs["error_unfiltered"][dl_idx]:.2f}°')
            print(f'    Pre-image error:  {cs["error_preimage"][dl_idx]:.2f}°')
            print(f'    Simple inverse:   {cs["error_simple_inverse"][dl_idx]:.2f}°')

            cs['fitted_delta_lambda'] = fitted_dl
            all_cross_sim[key] = cs
        else:
            print(f'  Skipping cross-sim for normal subject')
            all_cross_sim[key] = {'note': 'normal subject — no distortion'}

        # --- Tier 4: L_improve diagnostic ---
        if hc_amps_dict is not None:
            print(f'  L_improve diagnostic...')
            vuln_cvd = load_cvd_loco_target(subj, roi)
            li = l_improve_diagnostic(
                hc_amps_dict, preimage_angles,
                model_name, params, cvd_type, vuln_cvd)
            print(f'    L_improve = {li["l_improve"]:+.4f} '
                  f'({"positive ✓" if li["l_improve_positive"] else "NEGATIVE ✗"})')
            print(f'    ρ(CVD_sim, CVD_actual) = {li["rho_cvdsim_vs_cvd"]:.3f}')
            print(f'    ρ(filtered, CVD_actual) = {li["rho_filtered_vs_cvd"]:.3f}')
            all_l_improve[key] = li
        else:
            all_l_improve[key] = {'note': 'C010 data not available'}

        # --- Comparison table ---
        phase_b_path = None
        if args.phase_b_dir:
            phase_b_path = (Path(args.phase_b_dir)
                            / f'sub-{subj}_{roi}_{model_name}_filter.json')
        comp = build_comparison_table(
            preimage, model_name, params, cvd_type, phase_b_path)

        print(f'  Comparison:')
        for cond, vals in comp.items():
            if isinstance(vals, dict) and 'mean_error' in vals:
                print(f'    {cond:>20s}: mean_err={vals["mean_error"]:.2f}°, '
                      f'max_err={vals["max_error"]:.2f}°')
        all_comparison[key] = comp

    # --- Save all evaluations ---
    cs_path = output_dir / 'cross_sim_sanity.json'
    with open(cs_path, 'w') as f:
        json.dump(all_cross_sim, f, indent=2, default=str)
    print(f'\nSaved: {cs_path}')

    li_path = output_dir / 'l_improve_diagnostic.json'
    with open(li_path, 'w') as f:
        json.dump(all_l_improve, f, indent=2, default=str)
    print(f'Saved: {li_path}')

    comp_path = output_dir / 'comparison_table.json'
    with open(comp_path, 'w') as f:
        json.dump(all_comparison, f, indent=2, default=str)
    print(f'Saved: {comp_path}')

    # --- Print summary ---
    print(f'\n{"=" * 70}')
    print('EVALUATION SUMMARY')
    print(f'{"=" * 70}')
    for key in all_cross_sim:
        parts = key.split('_')
        subj_str = parts[0]  # sub-XX
        print(f'\n{key}:')
        cs = all_cross_sim[key]
        if 'fitted_delta_lambda' in cs:
            dl_idx = int(np.argmin(
                np.abs(np.array(cs['delta_lambda_range']) - cs['fitted_delta_lambda'])))
            print(f'  Tier 3 (cross-sim @ Δλ={cs["fitted_delta_lambda"]}): '
                  f'pre-image={cs["error_preimage"][dl_idx]:.2f}° '
                  f'(unfiltered={cs["error_unfiltered"][dl_idx]:.2f}°)')
        li = all_l_improve[key]
        if 'l_improve' in li:
            print(f'  Tier 4 (L_improve): {li["l_improve"]:+.4f} '
                  f'[DIAGNOSTIC, {"positive" if li["l_improve_positive"] else "NEGATIVE"}]')
        comp = all_comparison[key]
        if 'exact_preimage' in comp:
            print(f'  Comparison: no-filt={comp["no_filter"]["mean_error"]:.2f}°, '
                  f'inverse={comp["simple_inverse"]["mean_error"]:.2f}°, '
                  f'preimage={comp["exact_preimage"]["mean_error"]:.2f}°')
    print(f'{"=" * 70}')


if __name__ == '__main__':
    main()
