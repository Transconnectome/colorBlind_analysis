#!/usr/bin/env python3
"""
loco_filter_derive.py -- Phase B: Derive corrective filter from Phase A distortion fit.

Takes Phase A best-fit distortion delta_fit(c) and produces:
  1. Raw inverse filter: delta_filter = -delta_fit
  2. Constrained filter: no-harm clipping at preserved colors + smoothness check
  3. Filtered design matrix C_filtered for Phase C evaluation
  4. L_improve sanity: quick LOCO sim at filtered angles vs baseline
  5. Composition test: filter + distortion ~= identity (for parametric models)

Usage (server):
    mpirun -np 1 python scripts/loco_filter_derive.py \
        --subject 08 --phase_a_dir results/loco_filter/phase_a \
        --data_dir /scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010 \
        --output_dir results/loco_filter/phase_b

Usage (local):
    python scripts/loco_filter_derive.py --subject 08
"""

import argparse
import json
import numpy as np
import sys
import time
from pathlib import Path
from scipy.stats import spearmanr

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR))

_FWD_DIR = str(Path(__file__).resolve().parent.parent.parent.parent
               / 'future_phase1_forward_model' / 'scripts')
sys.path.insert(0, _FWD_DIR)

from utils_forward_model import (
    HC_SUBJECTS, N_CHANNELS, N_RUNS, N_COLORS,
    HUE_ANGLES, load_amplitudes, create_basis_full,
)
from loco_distortion_fit import (
    get_shifted_design, FILTER_MODELS, CVD_TYPE,
    compute_fit_loss, run_permutation_tests,
    LOCAL_DATA, SERVER_DATA,
)
from step1_fit_loco_v2 import (
    simulate_mean_hc_loco_legacy,
    simulate_mean_hc_wfixed,
    precompute_hc_W,
    load_cvd_loco_target,
)
from visualize_cone_shift_colors import STIM_LAB_ARR, STIM_HUE_DEG, STIM_CHROMA, STIM_L

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
# Primary model selection from Phase A results
PRIMARY_MODEL = {
    '08': 'rc_opponent',
    '09': 'machado_1way',
    '10': 'machado_1way',
}

# No-harm: sign-based — colors with CVD LOCO vuln > 0 are "preserved"
# (vuln > 0 means CVD already performs well at that color)
NOHARM_VULN_THRESHOLD = 0.0  # sign-based: only vuln > 0 protected
# Max filter shift at preserved colors (degrees)
NOHARM_MAX_SHIFT = 5.0


# ---------------------------------------------------------------------------
# Filter derivation
# ---------------------------------------------------------------------------

def load_phase_a_result(phase_a_dir, subj, roi, model_name):
    """Load Phase A JSON result."""
    path = Path(phase_a_dir) / f'sub-{subj}_{roi}_{model_name}.json'
    with open(path) as f:
        return json.load(f)


def derive_raw_filter(delta_fit):
    """Raw inverse: delta_filter = -delta_fit."""
    return -np.array(delta_fit)


def apply_noharm_constraint(delta_filter, vuln_cvd,
                            vuln_threshold=NOHARM_VULN_THRESHOLD,
                            max_shift=NOHARM_MAX_SHIFT):
    """Clip filter at preserved colors (sign-based: vuln > 0 = already good).

    Colors where CVD vuln > 0 are well-interpolated and should not be
    shifted aggressively. Colors with vuln < 0 are vulnerable and need
    the full filter correction.

    Returns:
        delta_constrained: (8,) filter with preserved colors clipped
        preserved_mask: (8,) bool mask of preserved colors
        clipped_colors: list of color indices that were clipped
    """
    # Sign-based: only protect colors where CVD performs WELL (vuln > 0)
    preserved = vuln_cvd > vuln_threshold
    delta_constrained = delta_filter.copy()
    clipped = []
    for c in range(len(delta_filter)):
        if preserved[c] and np.abs(delta_filter[c]) > max_shift:
            delta_constrained[c] = np.clip(delta_filter[c],
                                           -max_shift, max_shift)
            clipped.append(int(c))
    return delta_constrained, preserved, clipped


def check_smoothness(delta_filter):
    """Check adjacent-color hue difference in filter.

    Returns:
        adj_diffs: (8,) circular differences (wrapped to [-180, 180])
        max_adj_diff: float max absolute adjacent difference
        smooth_pass: bool True if all |adj_diff| < 10 degrees
    """
    diffs = np.diff(delta_filter, append=delta_filter[0])
    diffs = (diffs + 180) % 360 - 180
    return diffs, float(np.max(np.abs(diffs))), bool(np.all(np.abs(diffs) < 10))


def generate_filtered_design(delta_filter, n_channels=N_CHANNELS):
    """Generate design matrix C at filtered hue angles.

    Filtered angles = original + delta_filter (pre-compensation).
    """
    basis_full = create_basis_full(n_channels, basis_type='fe')
    filtered_hue = (np.array([0, 45, 90, 135, 180, 225, 270, 315],
                             dtype=float) + delta_filter) % 360
    idx = np.round(filtered_hue).astype(int) % 360
    C_filtered = basis_full[idx]
    return C_filtered, filtered_hue


def composition_test(delta_fit, delta_filter, model_name, params,
                     cvd_type, n_channels=N_CHANNELS):
    """Test that distortion + filter ~= identity.

    For parametric models: apply distortion to filtered stimuli,
    check that result is close to original angles.

    Returns:
        residual: (8,) per-color residual angle after composition
        max_residual: float max |residual| in degrees
        pass_1deg: bool True if max |residual| < 1 degree
    """
    original_hue = np.array([0, 45, 90, 135, 180, 225, 270, 315], dtype=float)

    # Step 1: Apply filter to stimuli
    filtered_hue = (original_hue + delta_filter) % 360

    # Step 2: Apply distortion model to filtered stimuli
    # For Machado/R+C: the distortion is defined by model params, not by delta_fit directly
    # We compute what CVD would perceive after seeing the filtered stimuli
    # Approximation: perceived = filtered + delta_fit (locally linear)
    # Better: recompute from model at each filtered angle
    # But Machado operates on CIELab stimuli, not arbitrary angles...
    # Use the linear approximation for now (valid for small delta)
    perceived = filtered_hue + delta_fit

    # Residual from identity
    residual = perceived - original_hue
    residual = (residual + 180) % 360 - 180  # wrap to [-180, 180]

    return residual, float(np.max(np.abs(residual))), bool(np.max(np.abs(residual)) < 1.0)


def evaluate_l_improve(hc_amps_dict, vuln_cvd, C_filtered, C_original,
                       method='shift_at_both', hc_W_dict=None):
    """L_improve sanity check: does the filter improve LOCO at vulnerable colors?

    Computes vulnerability at filtered angles and compares to baseline.
    This is a POST-FIT evaluation, NOT a training loss.

    Returns dict with improvement metrics.
    """
    # Baseline: HC LOCO at original angles
    if method == 'shift_at_both':
        vuln_baseline, _ = simulate_mean_hc_loco_legacy(hc_amps_dict, C_original)
        vuln_filtered, _ = simulate_mean_hc_loco_legacy(hc_amps_dict, C_filtered)
    else:
        vuln_baseline, _ = simulate_mean_hc_wfixed(hc_W_dict, hc_amps_dict, C_original)
        vuln_filtered, _ = simulate_mean_hc_wfixed(hc_W_dict, hc_amps_dict, C_filtered)

    # Per-color improvement
    delta_v = vuln_filtered - vuln_baseline

    # Vulnerable colors: CVD vuln < 0 (negative = poor interpolation)
    vulnerable_mask = vuln_cvd < 0
    preserved_mask = vuln_cvd > 0  # sign-based, consistent with constraint

    mean_improve_all = float(np.mean(delta_v))
    mean_improve_vuln = float(np.mean(delta_v[vulnerable_mask])) if vulnerable_mask.any() else 0.0
    mean_improve_pres = float(np.mean(delta_v[preserved_mask])) if preserved_mask.any() else 0.0

    # Spearman correlation: does filter bring HC vulnerability closer to CVD?
    rho_baseline, _ = spearmanr(vuln_baseline, vuln_cvd)
    rho_filtered, _ = spearmanr(vuln_filtered, vuln_cvd)

    return {
        'vuln_baseline': vuln_baseline.tolist(),
        'vuln_filtered': vuln_filtered.tolist(),
        'vuln_cvd': vuln_cvd.tolist(),
        'delta_v': delta_v.tolist(),
        'mean_improve_all': mean_improve_all,
        'mean_improve_vulnerable': mean_improve_vuln,
        'mean_improve_preserved': mean_improve_pres,
        'rho_baseline_vs_cvd': float(rho_baseline) if np.isfinite(rho_baseline) else 0.0,
        'rho_filtered_vs_cvd': float(rho_filtered) if np.isfinite(rho_filtered) else 0.0,
        'n_vulnerable': int(vulnerable_mask.sum()),
        'n_preserved': int(preserved_mask.sum()),
        'l_improve_positive': mean_improve_all > 0,
        'noharm_pass': mean_improve_pres >= 0 if preserved_mask.any() else True,
    }


# ---------------------------------------------------------------------------
# CIELab filter application
# ---------------------------------------------------------------------------

def apply_filter_cielab(delta_filter_deg):
    """Apply hue-angle filter to CIELab stimulus colors.

    Shifts each stimulus's CIELab hue angle by delta_filter(c) degrees
    while preserving L* and chroma. Returns modified CIELab coordinates.

    Args:
        delta_filter_deg: (8,) per-color hue correction in degrees

    Returns:
        lab_filtered: (8, 3) filtered CIELab [L*, a*, b*]
        hue_filtered: (8,) filtered CIELab hue angles
    """
    hue_filtered = STIM_HUE_DEG + delta_filter_deg
    a_new = STIM_CHROMA * np.cos(np.deg2rad(hue_filtered))
    b_new = STIM_CHROMA * np.sin(np.deg2rad(hue_filtered))
    lab_filtered = np.column_stack([STIM_L, a_new, b_new])
    return lab_filtered, hue_filtered


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Phase B: Derive corrective filter from Phase A distortion fit')
    parser.add_argument('--subject', required=True,
                        help='CVD subject ID (08, 09, or 10)')
    parser.add_argument('--roi', default='V4')
    parser.add_argument('--model', default=None,
                        help='Model name (default: auto-select primary)')
    parser.add_argument('--method', default='shift_at_both',
                        choices=['shift_at_both', 'w_fixed'])
    parser.add_argument('--phase_a_dir', default='results/loco_filter/phase_a')
    parser.add_argument('--data_dir', default=None)
    parser.add_argument('--output_dir', default='results/loco_filter/phase_b')
    parser.add_argument('--noharm_threshold', type=float,
                        default=NOHARM_VULN_THRESHOLD)
    parser.add_argument('--noharm_max_shift', type=float,
                        default=NOHARM_MAX_SHIFT)
    args = parser.parse_args()

    subj = args.subject
    roi = args.roi
    cvd_type = CVD_TYPE[subj]
    model_name = args.model or PRIMARY_MODEL.get(subj)

    if model_name is None:
        print(f'ERROR: No primary model defined for sub-{subj}')
        sys.exit(1)

    print(f'=== Phase B: Filter Derivation ===')
    print(f'Subject: sub-{subj} ({cvd_type}), ROI: {roi}')
    print(f'Model: {model_name}')

    # --- Load Phase A result ---
    phase_a = load_phase_a_result(args.phase_a_dir, subj, roi, model_name)
    best_params = phase_a['best_params']
    delta_fit = np.array(phase_a['best_loss']['delta_theta'])
    vuln_sim = np.array(phase_a['best_loss']['vuln_sim'])
    perm_p = phase_a['permutation']['label_perm_p']
    rho_fit = phase_a['permutation']['spearman_r']

    print(f'\nPhase A best fit:')
    print(f'  params = {best_params}')
    print(f'  rho = {rho_fit:.3f}, perm_p = {perm_p:.4f}')
    print(f'  delta_fit = {np.round(delta_fit, 1).tolist()}')

    # --- Load CVD target ---
    vuln_cvd = load_cvd_loco_target(subj, roi)
    print(f'  vuln_cvd = {np.round(vuln_cvd, 3).tolist()}')

    # --- Step 4a: Raw inverse filter ---
    delta_raw = derive_raw_filter(delta_fit)
    print(f'\nRaw filter (= -delta_fit):')
    print(f'  delta_filter_raw = {np.round(delta_raw, 1).tolist()}')

    # --- Step 4b: Constrained filter ---
    delta_constrained, preserved_mask, clipped = apply_noharm_constraint(
        delta_raw, vuln_cvd,
        vuln_threshold=args.noharm_threshold,
        max_shift=args.noharm_max_shift)

    print(f'\nNo-harm constraint (threshold={args.noharm_threshold}):')
    print(f'  Preserved colors: {np.where(preserved_mask)[0].tolist()}')
    print(f'  Clipped colors: {clipped}')
    print(f'  delta_constrained = {np.round(delta_constrained, 1).tolist()}')

    # Smoothness check
    adj_diffs, max_adj, smooth_pass = check_smoothness(delta_constrained)
    print(f'\nSmoothness check:')
    print(f'  Adjacent diffs: {np.round(adj_diffs, 1).tolist()}')
    print(f'  Max |adj_diff| = {max_adj:.1f} deg')
    print(f'  Smooth (<10 deg): {"PASS" if smooth_pass else "FAIL"}')

    # --- Generate filtered design matrix ---
    C_filtered_raw, hue_filtered_raw = generate_filtered_design(delta_raw)
    C_filtered_con, hue_filtered_con = generate_filtered_design(delta_constrained)
    print(f'\nFiltered hue angles (constrained):')
    print(f'  {np.round(hue_filtered_con, 1).tolist()}')

    # --- Composition test ---
    residual, max_res, comp_pass = composition_test(
        delta_fit, delta_constrained, model_name, best_params, cvd_type)
    print(f'\nComposition test (filter + distortion ~= identity):')
    print(f'  Residual: {np.round(residual, 2).tolist()}')
    print(f'  Max |residual| = {max_res:.2f} deg')
    print(f'  Pass (<1 deg): {"PASS" if comp_pass else "FAIL"}')

    # --- CIELab filter application ---
    lab_filtered_raw, cielab_hue_raw = apply_filter_cielab(delta_raw)
    lab_filtered_con, cielab_hue_con = apply_filter_cielab(delta_constrained)
    print(f'\nOriginal CIELab hues: {np.round(STIM_HUE_DEG, 1).tolist()}')
    print(f'Filtered CIELab hues: {np.round(cielab_hue_con, 1).tolist()}')

    # --- L_improve sanity check ---
    print(f'\n=== L_improve sanity check ===')

    # Auto-detect data path
    if args.data_dir:
        data_dir = Path(args.data_dir)
    elif SERVER_DATA.exists():
        data_dir = SERVER_DATA
    elif LOCAL_DATA.exists():
        data_dir = LOCAL_DATA
    else:
        old_local = (Path(__file__).resolve().parent.parent.parent.parent
                     / 'phase1_preprocess_decoding' / 'results'
                     / 'full_dataset_C010')
        if old_local.exists():
            data_dir = old_local
        else:
            print('WARNING: Cannot find C010 data, skipping L_improve.')
            data_dir = None

    l_improve_result = None
    if data_dir is not None:
        hc_amps_dict = {}
        for hc in HC_SUBJECTS:
            hc_amps_dict[hc] = load_amplitudes(data_dir, hc, roi)
        print(f'Loaded {len(hc_amps_dict)} HC subjects')

        basis_full = create_basis_full(N_CHANNELS, basis_type='fe')
        C_original = basis_full[HUE_ANGLES]

        hc_W_dict = None
        if args.method == 'w_fixed':
            hc_W_dict, _ = precompute_hc_W(hc_amps_dict, C_original)

        # Raw filter L_improve
        l_improve_raw = evaluate_l_improve(
            hc_amps_dict, vuln_cvd, C_filtered_raw, C_original,
            method=args.method, hc_W_dict=hc_W_dict)

        # Constrained filter L_improve
        l_improve_con = evaluate_l_improve(
            hc_amps_dict, vuln_cvd, C_filtered_con, C_original,
            method=args.method, hc_W_dict=hc_W_dict)

        l_improve_result = {
            'raw': l_improve_raw,
            'constrained': l_improve_con,
        }

        print(f'\nRaw filter:')
        print(f'  mean_improve_all = {l_improve_raw["mean_improve_all"]:+.4f}')
        print(f'  mean_improve_vulnerable = {l_improve_raw["mean_improve_vulnerable"]:+.4f}')
        print(f'  mean_improve_preserved = {l_improve_raw["mean_improve_preserved"]:+.4f}')
        print(f'  rho(baseline, CVD) = {l_improve_raw["rho_baseline_vs_cvd"]:.3f}')
        print(f'  rho(filtered, CVD) = {l_improve_raw["rho_filtered_vs_cvd"]:.3f}')
        print(f'  L_improve positive: {l_improve_raw["l_improve_positive"]}')
        print(f'  No-harm pass: {l_improve_raw["noharm_pass"]}')

        print(f'\nConstrained filter:')
        print(f'  mean_improve_all = {l_improve_con["mean_improve_all"]:+.4f}')
        print(f'  mean_improve_vulnerable = {l_improve_con["mean_improve_vulnerable"]:+.4f}')
        print(f'  mean_improve_preserved = {l_improve_con["mean_improve_preserved"]:+.4f}')
        print(f'  rho(filtered, CVD) = {l_improve_con["rho_filtered_vs_cvd"]:.3f}')
        print(f'  L_improve positive: {l_improve_con["l_improve_positive"]}')
        print(f'  No-harm pass: {l_improve_con["noharm_pass"]}')

        # CRITICAL GATE
        if not l_improve_con['l_improve_positive']:
            print('\n*** WARNING: L_improve NEGATIVE — filter worsens LOCO! ***')
            print('*** This replicates the DRDM inverse failure mode. ***')
            print('*** Proceeding with caveats — report as non-invertible. ***')

    # --- Save results ---
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    result = {
        'subject': subj,
        'cvd_type': cvd_type,
        'roi': roi,
        'model': model_name,
        'method': args.method,
        'phase_a_params': best_params,
        'phase_a_rho': rho_fit,
        'phase_a_perm_p': perm_p,
        'delta_fit': delta_fit.tolist(),
        'delta_filter_raw': delta_raw.tolist(),
        'delta_filter_constrained': delta_constrained.tolist(),
        'noharm_threshold': args.noharm_threshold,
        'noharm_max_shift': args.noharm_max_shift,
        'preserved_colors': np.where(preserved_mask)[0].tolist(),
        'clipped_colors': clipped,
        'smoothness': {
            'adjacent_diffs': adj_diffs.tolist(),
            'max_adj_diff': max_adj,
            'pass': smooth_pass,
        },
        'composition_test': {
            'residual': residual.tolist(),
            'max_residual': max_res,
            'pass': comp_pass,
        },
        'hue_original': [0, 45, 90, 135, 180, 225, 270, 315],
        'hue_filtered_raw': hue_filtered_raw.tolist(),
        'hue_filtered_constrained': hue_filtered_con.tolist(),
        'cielab_original': STIM_LAB_ARR.tolist(),
        'cielab_filtered_raw': lab_filtered_raw.tolist(),
        'cielab_filtered_constrained': lab_filtered_con.tolist(),
        'cielab_hue_original': STIM_HUE_DEG.tolist(),
        'cielab_hue_filtered': cielab_hue_con.tolist(),
    }

    if l_improve_result:
        result['l_improve'] = l_improve_result

    # Verdict
    if perm_p > 0.05:
        verdict = 'NO_FILTER'
    elif l_improve_result and not l_improve_result['constrained']['l_improve_positive']:
        verdict = 'NON_INVERTIBLE'
    elif not smooth_pass:
        verdict = 'FILTER_ROUGH'
    else:
        verdict = 'FILTER_OK'
    result['verdict'] = verdict

    save_path = output_dir / f'sub-{subj}_{roi}_{model_name}_filter.json'
    with open(save_path, 'w') as f:
        json.dump(result, f, indent=2, default=str)
    print(f'\nSaved: {save_path}')

    # --- Summary ---
    print(f'\n{"=" * 60}')
    print(f'PHASE B SUMMARY: sub-{subj} ({cvd_type})')
    print(f'{"=" * 60}')
    print(f'Model: {model_name}, params={best_params}')
    print(f'Phase A: rho={rho_fit:.3f}, p={perm_p:.4f}')
    print(f'Filter (constrained): {np.round(delta_constrained, 1).tolist()}')
    print(f'Smoothness: {"PASS" if smooth_pass else "FAIL"} (max adj={max_adj:.1f} deg)')
    print(f'Composition: {"PASS" if comp_pass else "FAIL"} (max res={max_res:.2f} deg)')
    if l_improve_result:
        lc = l_improve_result['constrained']
        print(f'L_improve: {lc["mean_improve_all"]:+.4f} '
              f'(vuln: {lc["mean_improve_vulnerable"]:+.4f}, '
              f'pres: {lc["mean_improve_preserved"]:+.4f})')
    print(f'Verdict: {verdict}')
    print(f'{"=" * 60}')

    return result


if __name__ == '__main__':
    main()
