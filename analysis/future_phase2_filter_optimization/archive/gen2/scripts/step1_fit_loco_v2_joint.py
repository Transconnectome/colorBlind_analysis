#!/usr/bin/env python3
"""
step1_fit_loco_v2_joint.py — Joint cross-ROI LOCO fitting with single Δλ.

Motivation:
  Δλ is a retinal property — it should be the same across all visual areas.
  Per-ROI fitting showed 10× variation (V1: 34.9nm vs V2: 3.9nm for sub-08),
  which is physically implausible. Joint fitting constrains a single Δλ
  across all ROIs.

Method:
  1. Precompute W_HC for ALL ROIs simultaneously
  2. Optimize single Δλ to maximize mean Spearman ρ across ROIs
  3. Permutation test: same color-label shuffle across all ROIs
     (because the retinal transformation is shared)
  4. Report: joint p-value, per-ROI ρ at joint Δλ, comparison with per-ROI fits

Usage:
    python scripts/step1_fit_loco_v2_joint.py \
        --output_dir results/v2/step1_loco_joint
"""

import argparse
import json
import numpy as np
from pathlib import Path
from datetime import datetime
from scipy.optimize import minimize_scalar
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
)
from utils_distortion_models import get_design_matrix
from step1_fit_loco_v2 import (
    precompute_hc_W, simulate_mean_hc_wfixed, load_cvd_loco_target,
    lins_ccc, mse_decompose,
)

LOCAL_BASELINE = Path(__file__).resolve().parent.parent.parent.parent \
    / 'phase1_preprocess_decoding' / 'results' / 'full_dataset_C010'
FWD_RESULTS = Path(__file__).resolve().parent.parent.parent.parent \
    / 'future_phase1_forward_model' / 'results'

CVD_TYPE = {'08': 'deutan', '09': 'protan', '10': 'normal'}

JOINT_ROIS = ['V1', 'V2', 'V3', 'V4']


# ============================================================================
# Joint objective
# ============================================================================

def joint_spearman_objective(delta_lambda, roi_data, cvd_type):
    """Negative mean Spearman ρ across ROIs for a single Δλ.

    Args:
        delta_lambda: single cone shift parameter (nm)
        roi_data: dict {roi: (hc_W_dict, hc_amps_dict, cvd_vuln)}
        cvd_type: 'deutan' or 'protan'

    Returns:
        neg_mean_rho: negative of mean Spearman ρ across ROIs
    """
    rhos = []
    for roi, (hc_W, hc_amps, cvd_vuln) in roi_data.items():
        C_shifted = get_design_matrix('cone_1way', [delta_lambda],
                                       cvd_type=cvd_type)
        mean_vuln, _ = simulate_mean_hc_wfixed(hc_W, hc_amps, C_shifted)
        rho, _ = spearmanr(mean_vuln, cvd_vuln)
        rhos.append(rho if np.isfinite(rho) else 0.0)
    return -np.mean(rhos)


# ============================================================================
# Joint permutation test
# ============================================================================

def permutation_test_joint(roi_data, delta_opt, cvd_type, n_perm=10000):
    """Joint permutation test with shared color-label shuffle across ROIs.

    Tests whether the joint Δρ = mean_ρ(Δλ*) − mean_ρ(Δλ=0) exceeds chance.
    Same permutation is applied to all ROIs (retinal property = shared).

    Args:
        roi_data: dict {roi: (hc_W_dict, hc_amps_dict, cvd_vuln)}
        delta_opt: optimal joint Δλ (nm)
        cvd_type: CVD type
        n_perm: number of permutations

    Returns:
        p_value, null_delta_rho, observed results dict
    """
    # Precompute fitted and baseline vulnerabilities per ROI
    C_opt = get_design_matrix('cone_1way', [delta_opt], cvd_type=cvd_type)
    C_base = create_basis_matrix(HUE_ANGLES, N_CHANNELS)

    per_roi_vuln_fit = {}
    per_roi_vuln_base = {}
    per_roi_cvd = {}
    for roi, (hc_W, hc_amps, cvd_vuln) in roi_data.items():
        per_roi_vuln_fit[roi], _ = simulate_mean_hc_wfixed(hc_W, hc_amps, C_opt)
        per_roi_vuln_base[roi], _ = simulate_mean_hc_wfixed(hc_W, hc_amps, C_base)
        per_roi_cvd[roi] = cvd_vuln

    # Observed: per-ROI ρ and joint mean
    rho_fit_per_roi = {}
    rho_base_per_roi = {}
    for roi in roi_data:
        r_fit, _ = spearmanr(per_roi_vuln_fit[roi], per_roi_cvd[roi])
        r_base, _ = spearmanr(per_roi_vuln_base[roi], per_roi_cvd[roi])
        rho_fit_per_roi[roi] = float(r_fit) if np.isfinite(r_fit) else 0.0
        rho_base_per_roi[roi] = float(r_base) if np.isfinite(r_base) else 0.0

    mean_rho_fit = np.mean(list(rho_fit_per_roi.values()))
    mean_rho_base = np.mean(list(rho_base_per_roi.values()))
    delta_rho_obs = mean_rho_fit - mean_rho_base

    roi_list = sorted(roi_data.keys())

    # Exact permutation if feasible (8! = 40320)
    use_exact = n_perm >= 40320
    if use_exact:
        null_delta = []
        for perm in permutations(range(8)):
            perm_list = list(perm)
            mean_fit_perm = np.mean([
                _safe_rho(per_roi_vuln_fit[roi], per_roi_cvd[roi][perm_list])
                for roi in roi_list
            ])
            mean_base_perm = np.mean([
                _safe_rho(per_roi_vuln_base[roi], per_roi_cvd[roi][perm_list])
                for roi in roi_list
            ])
            null_delta.append(mean_fit_perm - mean_base_perm)
        null_delta = np.array(null_delta)
    else:
        rng = np.random.default_rng(42)
        null_delta = np.zeros(n_perm)
        for i in range(n_perm):
            perm = rng.permutation(8)
            mean_fit_perm = np.mean([
                _safe_rho(per_roi_vuln_fit[roi], per_roi_cvd[roi][perm])
                for roi in roi_list
            ])
            mean_base_perm = np.mean([
                _safe_rho(per_roi_vuln_base[roi], per_roi_cvd[roi][perm])
                for roi in roi_list
            ])
            null_delta[i] = mean_fit_perm - mean_base_perm

    p = (np.sum(null_delta >= delta_rho_obs) + 1) / (len(null_delta) + 1)

    obs = {
        'per_roi_rho_fitted': rho_fit_per_roi,
        'per_roi_rho_baseline': rho_base_per_roi,
        'mean_rho_fitted': float(mean_rho_fit),
        'mean_rho_baseline': float(mean_rho_base),
        'delta_rho_joint': float(delta_rho_obs),
    }

    return float(p), null_delta, obs


def _safe_rho(x, y):
    r, _ = spearmanr(x, y)
    return float(r) if np.isfinite(r) else 0.0


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Joint cross-ROI LOCO fitting with single Δλ')
    parser.add_argument('--output_dir', type=str,
                        default='results/v2/step1_loco_joint')
    parser.add_argument('--rois', nargs='+', default=JOINT_ROIS)
    parser.add_argument('--cvd_subjects', nargs='+', default=CVD_SUBJECTS)
    parser.add_argument('--hc_subjects', nargs='+', default=HC_SUBJECTS)
    parser.add_argument('--baseline_dir', type=str,
                        default=str(LOCAL_BASELINE))
    parser.add_argument('--max_shift', type=float, default=60.0)
    args = parser.parse_args()

    print('=' * 60)
    print('Joint Cross-ROI LOCO Fitting (single Δλ, cone_1way)')
    print(f'ROIs: {args.rois}')
    print(f'CVD subjects: {args.cvd_subjects}')
    print(f'HC subjects: {args.hc_subjects}')
    print('=' * 60)

    # Load HC amplitudes and precompute W for ALL ROIs
    roi_hc_W = {}
    roi_hc_amps = {}
    roi_hc_alphas = {}

    for roi in args.rois:
        print(f'\n--- Loading {roi} ---')
        hc_amps = {}
        for subj in args.hc_subjects:
            try:
                hc_amps[subj] = load_amplitudes(args.baseline_dir, subj, roi)
            except FileNotFoundError:
                print(f'  [SKIP] sub-{subj} {roi} not found')
        print(f'  Loaded {len(hc_amps)} HC subjects')

        C_original = create_basis_matrix(HUE_ANGLES, N_CHANNELS)
        hc_W, hc_alphas = precompute_hc_W(hc_amps, C_original)
        print(f'  Precomputed W for {len(hc_W)} HC subjects')

        roi_hc_W[roi] = hc_W
        roi_hc_amps[roi] = hc_amps
        roi_hc_alphas[roi] = hc_alphas

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for cvd_subj in args.cvd_subjects:
        cvd_type = CVD_TYPE[cvd_subj]
        if cvd_type == 'normal':
            print(f'\n  sub-{cvd_subj} (normal) — skipping joint fit')
            continue

        print(f'\n{"=" * 60}')
        print(f'sub-{cvd_subj} ({cvd_type})')
        print('=' * 60)

        # Build roi_data: {roi: (hc_W, hc_amps, cvd_vuln)}
        roi_data = {}
        for roi in args.rois:
            try:
                cvd_vuln = load_cvd_loco_target(cvd_subj, roi)
            except (FileNotFoundError, KeyError) as e:
                print(f'  [SKIP] {roi}: {e}')
                continue
            roi_data[roi] = (roi_hc_W[roi], roi_hc_amps[roi], cvd_vuln)
        print(f'  Available ROIs: {list(roi_data.keys())}')

        if not roi_data:
            print('  No ROI data available — skipping')
            continue

        # Grid search for landscape visualization
        print('\n  [1] Grid search (0..60nm, 1nm steps)...')
        delta_range = np.arange(0, args.max_shift + 1, 1)
        landscape = {'delta_range': [], 'mean_rho': [], 'per_roi_rho': {}}
        for roi in roi_data:
            landscape['per_roi_rho'][roi] = []

        for delta in delta_range:
            C = get_design_matrix('cone_1way', [delta], cvd_type=cvd_type)
            per_roi_rhos = {}
            for roi, (hc_W, hc_amps, cvd_vuln) in roi_data.items():
                mv, _ = simulate_mean_hc_wfixed(hc_W, hc_amps, C)
                r, _ = spearmanr(mv, cvd_vuln)
                per_roi_rhos[roi] = float(r) if np.isfinite(r) else 0.0
                landscape['per_roi_rho'][roi].append(per_roi_rhos[roi])
            landscape['delta_range'].append(float(delta))
            landscape['mean_rho'].append(float(np.mean(
                list(per_roi_rhos.values()))))

        # Find optimal from grid
        best_idx = np.argmax(landscape['mean_rho'])
        delta_grid = landscape['delta_range'][best_idx]
        print(f'    Grid optimum: Δλ = {delta_grid:.0f}nm, '
              f'mean ρ = {landscape["mean_rho"][best_idx]:.3f}')

        # Refine with bounded scalar optimization
        print('\n  [2] Refining with Brent optimization...')
        result = minimize_scalar(
            joint_spearman_objective,
            bounds=(max(0, delta_grid - 5), min(args.max_shift, delta_grid + 5)),
            args=(roi_data, cvd_type),
            method='bounded',
        )
        delta_opt = float(result.x)
        mean_rho_opt = float(-result.fun)
        print(f'    Optimal: Δλ = {delta_opt:.2f}nm, mean ρ = {mean_rho_opt:.3f}')

        # Per-ROI ρ at joint optimum
        C_opt = get_design_matrix('cone_1way', [delta_opt], cvd_type=cvd_type)
        per_roi_rho_opt = {}
        per_roi_vuln_opt = {}
        for roi, (hc_W, hc_amps, cvd_vuln) in roi_data.items():
            mv, _ = simulate_mean_hc_wfixed(hc_W, hc_amps, C_opt)
            r, _ = spearmanr(mv, cvd_vuln)
            per_roi_rho_opt[roi] = float(r) if np.isfinite(r) else 0.0
            per_roi_vuln_opt[roi] = mv.tolist()
            print(f'    {roi}: ρ = {per_roi_rho_opt[roi]:.3f}')

        # Baseline (Δλ=0) per-ROI ρ
        C_base = create_basis_matrix(HUE_ANGLES, N_CHANNELS)
        per_roi_rho_base = {}
        per_roi_vuln_base = {}
        for roi, (hc_W, hc_amps, cvd_vuln) in roi_data.items():
            mv, _ = simulate_mean_hc_wfixed(hc_W, hc_amps, C_base)
            r, _ = spearmanr(mv, cvd_vuln)
            per_roi_rho_base[roi] = float(r) if np.isfinite(r) else 0.0
            per_roi_vuln_base[roi] = mv.tolist()

        # Joint permutation test
        print('\n  [3] Joint permutation test (exact, 8!)...')
        perm_p, null_delta, obs = permutation_test_joint(
            roi_data, delta_opt, cvd_type)
        print(f'    Joint Δρ = {obs["delta_rho_joint"]:.4f}, '
              f'perm p = {perm_p:.4f}')
        print(f'    mean ρ(fitted) = {obs["mean_rho_fitted"]:.3f}, '
              f'mean ρ(baseline) = {obs["mean_rho_baseline"]:.3f}')

        # Save
        result_data = {
            'subject': cvd_subj,
            'cvd_type': cvd_type,
            'rois': list(roi_data.keys()),
            'timestamp': datetime.now().isoformat(),
            'method': 'joint_cross_roi_cone_1way',
            # Joint fit
            'joint_delta_lambda': delta_opt,
            'joint_mean_rho': mean_rho_opt,
            'perm_p_joint': perm_p,
            'delta_rho_joint': obs['delta_rho_joint'],
            'perm_null_delta_rho_mean': float(np.mean(null_delta)),
            'perm_null_delta_rho_std': float(np.std(null_delta)),
            # Per-ROI at joint Δλ
            'per_roi_rho': per_roi_rho_opt,
            'per_roi_rho_baseline': per_roi_rho_base,
            'per_roi_vuln': per_roi_vuln_opt,
            'per_roi_vuln_baseline': per_roi_vuln_base,
            # CVD targets
            'cvd_loco_targets': {
                roi: roi_data[roi][2].tolist() for roi in roi_data
            },
            # HC info
            'hc_subjects': args.hc_subjects,
            'hc_alphas': {
                roi: roi_hc_alphas[roi] for roi in roi_data
            },
            # Landscape
            'landscape': landscape,
        }

        out_path = out_dir / f'sub-{cvd_subj}_loco_v2_joint.json'
        with open(out_path, 'w') as f:
            json.dump(result_data, f, indent=2)
        print(f'\n  Saved: {out_path}')

    print('\nJoint cross-ROI fitting complete.')


if __name__ == '__main__':
    main()
