#!/usr/bin/env python3
"""
delta_rho_perm_test.py — Fit-vs-baseline Δρ permutation specificity test.

Background (peer_review/problematic_params_and_loss.md §2.2, §4.3 #5):
  Existing pipeline (loco_distortion_fit.py / hc_specificity_test.py) reports
  label_perm_p — fit fixed, CVD labels shuffled. This penalizes baseline ρ
  inflation: subjects with high baseline_ρ (∈ [-0.36, +0.69] for hV4)
  appear "significant" without genuine cone-shift improvement.

  This script replaces label permutation with Δρ permutation:
      Δρ_obs  = ρ_fit(unperm) - ρ_base(unperm)
      Δρ_perm = ρ_fit(perm)   - ρ_base(perm)     for each color shuffle
      p       = P(Δρ_perm >= Δρ_obs)

Subjects:
  - HC 01-07: LOO pseudo-CVD (6-HC pool, target = self at δ=0)
  - CVD 08-10: 7-HC pool, target = CVD LOCO from forward_phase1

Models: machado_1way, rc_opponent, 2component, rc_opponent_2d
ROIs: V1, V2, V4 (hV4 = V4 on disk)

Usage:
    # Single (subj, roi, model, family) test
    python scripts/delta_rho_perm_test.py \
        --subject 08 --roi V4 --model 2component --cvd_type deutan \
        --output_dir results/delta_rho_perm

    # Array launcher: see sbatch/run_delta_rho_perm.sbatch
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

_SCRIPT_DIR = Path(__file__).resolve().parent
_PHASE2_DIR = _SCRIPT_DIR.parent
sys.path.insert(0, str(_SCRIPT_DIR))

_CONE_DIR = _PHASE2_DIR / 'cone_shift_pipeline' / 'scripts'
if _CONE_DIR.exists() and str(_CONE_DIR) not in sys.path:
    sys.path.insert(0, str(_CONE_DIR))

for _base in [_PHASE2_DIR.parent, _PHASE2_DIR.parent.parent]:
    _fwd = _base / 'future_phase1_forward_model' / 'scripts'
    if _fwd.exists() and str(_fwd) not in sys.path:
        sys.path.insert(0, str(_fwd))
        break

from utils_forward_model import (  # noqa: E402
    HC_SUBJECTS, N_CHANNELS, HUE_ANGLES,
    load_amplitudes, create_basis_full,
)
from loco_distortion_fit import (  # noqa: E402
    grid_search, optimize_de, get_shifted_design,
    FILTER_MODELS, DEFAULT_WEIGHTS, CVD_TYPE,
)
from step1_fit_loco_v2 import (  # noqa: E402
    precompute_hc_W, simulate_single_hc_wfixed,
    simulate_mean_hc_wfixed, simulate_mean_hc_loco_legacy,
    load_cvd_loco_target, permutation_test_spearman,
)
from diagnostic_delta_rdm import compute_delta_rdm_obs  # noqa: E402

LOCAL_DATA = (_PHASE2_DIR.parent / 'phase1_procrustes_decoding' / 'results'
              / 'visualization' / 'full_dataset_C010_with_residuals')
SERVER_DATA = Path(
    '/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010')

CVD_SUBJECTS = ['08', '09', '10']


# ---------------------------------------------------------------------------
# Δρ permutation test (model-agnostic, runs at any best-fit point)
# ---------------------------------------------------------------------------

def delta_rho_permutation(
    vuln_fit, vuln_base, vuln_target, n_perm=40320,
):
    """Δρ = ρ(vuln_fit, vuln_target) − ρ(vuln_base, vuln_target).

    Permutation null: shuffle target color labels. For each shuffle,
    recompute Δρ_perm. p = (count(perm ≥ obs) + 1) / (N + 1).

    Default n_perm=40320 → exact 8! permutation.

    Args:
        vuln_fit: (8,) fitted mean-HC vulnerability at best params
        vuln_base: (8,) baseline mean-HC vulnerability at δ=0
        vuln_target: (8,) target (CVD or HC LOO)
        n_perm: permutation count

    Returns:
        dict with rho_fit, rho_base, delta_rho_obs, delta_rho_perm_p,
              null_mean, null_std, observed_percentile
    """
    from itertools import permutations

    rho_fit, _ = spearmanr(vuln_fit, vuln_target)
    rho_base, _ = spearmanr(vuln_base, vuln_target)
    rho_fit = float(rho_fit) if np.isfinite(rho_fit) else 0.0
    rho_base = float(rho_base) if np.isfinite(rho_base) else 0.0
    delta_obs = rho_fit - rho_base

    use_exact = n_perm >= 40320
    if use_exact:
        null = np.empty(40320)
        for i, perm in enumerate(permutations(range(8))):
            tgt = vuln_target[list(perm)]
            r_f, _ = spearmanr(vuln_fit, tgt)
            r_b, _ = spearmanr(vuln_base, tgt)
            r_f = float(r_f) if np.isfinite(r_f) else 0.0
            r_b = float(r_b) if np.isfinite(r_b) else 0.0
            null[i] = r_f - r_b
    else:
        rng = np.random.default_rng(42)
        null = np.empty(n_perm)
        for i in range(n_perm):
            perm = rng.permutation(8)
            tgt = vuln_target[perm]
            r_f, _ = spearmanr(vuln_fit, tgt)
            r_b, _ = spearmanr(vuln_base, tgt)
            r_f = float(r_f) if np.isfinite(r_f) else 0.0
            r_b = float(r_b) if np.isfinite(r_b) else 0.0
            null[i] = r_f - r_b

    p = float((np.sum(null >= delta_obs) + 1) / (len(null) + 1))
    pct = float((np.sum(null < delta_obs) / len(null)) * 100.0)

    return {
        'rho_fit': rho_fit,
        'rho_baseline': rho_base,
        'delta_rho_obs': float(delta_obs),
        'delta_rho_perm_p': p,
        'null_mean': float(np.mean(null)),
        'null_std': float(np.std(null)),
        'observed_percentile': pct,
        'n_perm': int(len(null)),
    }


# ---------------------------------------------------------------------------
# Single-cell test (one subject × roi × model × cvd_type)
# ---------------------------------------------------------------------------

def run_single_cell(subj, roi, model_name, cvd_type, data_dir,
                    method='shift_at_both', weights=None, skip_rdm=False):
    """One (subject, ROI, model, family) Δρ permutation cell.

    Returns dict with fit params, baseline ρ, fit ρ, Δρ_obs, Δρ_perm_p,
    label_perm_p (for backward comparison), and timing.
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS.copy()

    is_hc = subj in HC_SUBJECTS

    # --- Load all amps ---
    if is_hc:
        # LOO: target = self, pool = remaining 6 HCs
        hc_pool = [s for s in HC_SUBJECTS if s != subj]
        hc_amps_dict = {s: load_amplitudes(data_dir, s, roi) for s in hc_pool}
        target_amp = load_amplitudes(data_dir, subj, roi)
    else:
        # CVD: pool = full 7 HCs, target = CVD direct
        hc_amps_dict = {s: load_amplitudes(data_dir, s, roi)
                        for s in HC_SUBJECTS}
        target_amp = load_amplitudes(data_dir, subj, roi)

    # --- Precompute W ---
    basis_full = create_basis_full(N_CHANNELS, basis_type='fe')
    C_original = basis_full[HUE_ANGLES]
    hc_W_dict, _ = precompute_hc_W(hc_amps_dict, C_original)

    # --- Compute target vulnerability ---
    if is_hc:
        # LOO: target = subject's own δ=0 prediction (self W applied to self amp)
        target_W, _ = precompute_hc_W({subj: target_amp}, C_original)
        vuln_target = simulate_single_hc_wfixed(
            target_W[subj], target_amp, C_original)
    else:
        # CVD: forward_phase1 LOCO json
        try:
            vuln_target = load_cvd_loco_target(subj, roi)
        except FileNotFoundError as e:
            return {'error': f'CVD LOCO json missing: {e}'}

    if not np.all(np.isfinite(vuln_target)) or np.std(vuln_target) < 1e-10:
        return {'error': 'invalid target (NaN or zero variance)'}

    # --- ΔRDM observed (optional) ---
    delta_rdm_obs = None
    if not skip_rdm:
        try:
            delta_rdm_obs, _, _, _ = compute_delta_rdm_obs(
                target_amp, hc_amps_dict)
        except Exception as e:
            print(f'  WARNING: ΔRDM computation failed ({e}); skipping')
            delta_rdm_obs = None

    # --- Baseline vulnerability (δ=0) ---
    if method == 'shift_at_both':
        vuln_baseline, _ = simulate_mean_hc_loco_legacy(
            hc_amps_dict, C_original)
    else:
        vuln_baseline, _ = simulate_mean_hc_wfixed(
            hc_W_dict, hc_amps_dict, C_original)

    rho_baseline = float(spearmanr(vuln_baseline, vuln_target).statistic)
    if not np.isfinite(rho_baseline):
        rho_baseline = 0.0

    # --- Fit model ---
    t0 = time.time()
    if FILTER_MODELS[model_name]['grid_step'] is not None:
        result = grid_search(
            model_name, hc_amps_dict, vuln_target, cvd_type,
            method=method, hc_W_dict=hc_W_dict,
            delta_rdm_obs=delta_rdm_obs, weights=weights,
            verbose=False)
    else:
        result = optimize_de(
            model_name, hc_amps_dict, vuln_target, cvd_type,
            method=method, hc_W_dict=hc_W_dict,
            delta_rdm_obs=delta_rdm_obs, weights=weights,
            verbose=False)
    elapsed_fit = time.time() - t0

    best_params = np.asarray(result['best_params'])
    best_vuln = np.array(result['best_loss']['vuln_sim'])

    # --- Δρ permutation test ---
    t1 = time.time()
    drho = delta_rho_permutation(best_vuln, vuln_baseline, vuln_target)
    elapsed_drho = time.time() - t1

    # --- Backward-compatible label_perm_p (fit-fixed) for comparison ---
    label_p, _, _ = permutation_test_spearman(
        best_vuln, vuln_target, n_perm=40320)

    return {
        'subject': subj,
        'is_hc': is_hc,
        'roi': roi,
        'model': model_name,
        'cvd_type': cvd_type,
        'method': method,
        'best_params': best_params.tolist(),
        'vuln_target': vuln_target.tolist(),
        'vuln_baseline': vuln_baseline.tolist(),
        'vuln_fit': best_vuln.tolist(),
        # Primary metric
        'delta_rho_obs': drho['delta_rho_obs'],
        'delta_rho_perm_p': drho['delta_rho_perm_p'],
        'null_delta_rho_mean': drho['null_mean'],
        'null_delta_rho_std': drho['null_std'],
        'observed_percentile': drho['observed_percentile'],
        # Components
        'rho_fit': drho['rho_fit'],
        'rho_baseline': drho['rho_baseline'],
        # Backward-compat
        'label_perm_p': float(label_p),
        # Loss components
        'l_fit': float(result['best_loss']['l_fit']),
        'l_vuln': float(result['best_loss']['l_vuln']),
        'l_rank': float(result['best_loss']['l_rank']),
        'l_rdm': float(result['best_loss'].get('l_rdm', 0.0)),
        # Timing
        'elapsed_fit_s': round(elapsed_fit, 1),
        'elapsed_drho_s': round(elapsed_drho, 1),
        'timestamp': datetime.now().isoformat(),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Δρ permutation specificity test')
    parser.add_argument('--subject', required=True,
                        help='01-07 (HC LOO) or 08-10 (CVD)')
    parser.add_argument('--roi', default='V4', choices=['V1', 'V2', 'V4'])
    parser.add_argument('--model', required=True,
                        choices=['machado_1way', 'rc_opponent',
                                 '2component', 'rc_opponent_2d',
                                 'fourier_warp'])
    parser.add_argument('--cvd_type', default=None,
                        choices=['protan', 'deutan', 'normal'],
                        help='Family. CVD subjects auto-derive; HC defaults '
                             'to deutan if not specified.')
    parser.add_argument('--method', default='shift_at_both',
                        choices=['shift_at_both', 'w_fixed'])
    parser.add_argument('--data_dir', default=None)
    parser.add_argument('--output_dir', default='results/delta_rho_perm')
    parser.add_argument('--skip_rdm', action='store_true')
    args = parser.parse_args()

    subj = args.subject
    if subj in CVD_SUBJECTS:
        cvd_type = CVD_TYPE[subj]
    elif args.cvd_type is not None:
        cvd_type = args.cvd_type
    else:
        cvd_type = 'deutan'  # default for HC LOO

    # Resolve data path
    if args.data_dir:
        data_dir = Path(args.data_dir)
    elif SERVER_DATA.exists():
        data_dir = SERVER_DATA
    elif LOCAL_DATA.exists():
        data_dir = LOCAL_DATA
    else:
        raise FileNotFoundError('Cannot find C010 data')

    print(f'=== Δρ perm test: sub-{subj} {args.roi} {args.model} '
          f'({cvd_type}, {args.method}) ===')
    print(f'  Data: {data_dir}')

    res = run_single_cell(subj, args.roi, args.model, cvd_type,
                          data_dir, method=args.method,
                          skip_rdm=args.skip_rdm)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / (
        f'sub-{subj}_{args.roi}_{args.model}_{cvd_type}.json')
    with open(out_path, 'w') as f:
        json.dump(res, f, indent=2, default=str)

    if 'error' in res:
        print(f'  ERROR: {res["error"]}')
        sys.exit(1)

    print(f'\n  rho_baseline = {res["rho_baseline"]:+.3f}')
    print(f'  rho_fit      = {res["rho_fit"]:+.3f}')
    print(f'  Δρ_obs       = {res["delta_rho_obs"]:+.3f}')
    print(f'  Δρ_perm_p    = {res["delta_rho_perm_p"]:.4f}')
    print(f'  label_perm_p = {res["label_perm_p"]:.4f} (backward-compat)')
    print(f'\n  Saved: {out_path}')


if __name__ == '__main__':
    main()
