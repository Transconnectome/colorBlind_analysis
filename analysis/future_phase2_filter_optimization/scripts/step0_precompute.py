#!/usr/bin/env python3
"""
step0_precompute.py — Gen-4 Stage 0 precompute.

Caches the expensive quantities that downstream stages (1, 2, 3a, 3b) all
depend on, so that each CVD × ROI × model fit no longer reloads raw
amplitudes or re-estimates ridge weights:

    1. HC ridge_gcv weights W_{V1,V2,hV4}
       - pooled 6 runs × 8 colors = 48 samples, unshifted C(θ)
       - reused by ΔRDM_sim (step 1/2) and hV4 NEURAL transfer (step 3a)

    2. Observed ΔRDM_obs{V1,V2,hV4} per CVD subject
       - RDM_CVD − mean(RDM_HC) on run-averaged patterns
       - correlation distance (matches diagnostic_delta_rdm.py)
       - feeds L₁ in the L₃ loss (step 2) and sanity in step 1

    3. Stockman grid cache
       - wavelength grid, L/M/S fundamentals, Area_L/Area_M, XYZ→LMS matrix
       - so that every Machado call downstream uses the same numerics

    4. Machado D65 gray-point sanity check
       - verify_machado_gray_point(tolerance_deg=2.5) — must return True
         before the pipeline is allowed to run. 2.5° is the empirical
         LSQ-residual floor for the mixed Machado spectrum (see the
         `verify_machado_gray_point` docstring in machado_simulator.py);
         failures above that indicate a Stockman normalization or k-factor
         bug, not Machado's paper calibration.

Outputs (written once to results/step0_precompute/):

    hc_W_{V1,V2,hV4}.npz          one K×V_s matrix per HC subject, per ROI
    delta_rdm_obs_{V1,V2,hV4}.npz one 28-vector per CVD subject, per ROI
    stockman_grid.npz             wl, L, M, S, area_L, area_M, M_xyz2lms
    machado_gray_check.json       {ok: bool, tolerance, details:[...]}
    step0_manifest.json           one row per (ROI, subject) with shapes/paths

Usage (local):
    conda activate srm
    python scripts/step0_precompute.py \
        --output_dir results/step0_precompute

Usage (server, per BrainIAK MPI fix):
    mpirun -np 1 python scripts/step0_precompute.py \
        --output_dir results/step0_precompute

Reused helpers:
    precompute_hc_W           (diagnostic_delta_rdm.py:357)
    compute_delta_rdm_obs     (diagnostic_delta_rdm.py:197)
    load_amplitudes           (future_phase1_forward_model/utils_forward_model.py)
    create_basis_matrix       (future_phase1_forward_model/utils_forward_model.py)
    load_stockman_fundamentals(future_phase1_forward_model/stockman_cone_shift.py)
    verify_machado_gray_point (cone_shift_pipeline/scripts/machado_simulator.py)
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict

import numpy as np

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

_FWD_DIR = str(Path(__file__).resolve().parent.parent.parent.parent
               / 'future_phase1_forward_model' / 'scripts')
if _FWD_DIR not in sys.path:
    sys.path.insert(0, _FWD_DIR)

from utils_forward_model import (  # noqa: E402
    HC_SUBJECTS,
    CVD_SUBJECTS,
    HUE_ANGLES,
    N_CHANNELS,
    create_basis_matrix,
    load_amplitudes,
)
from diagnostic_delta_rdm import (  # noqa: E402
    compute_delta_rdm_obs,
    precompute_hc_W,
)
from machado_simulator import (  # noqa: E402
    DELTA_LAMBDA_MAX,
    MACHADO_AREA_CONSTANT,
    _load_stockman_grid,
    verify_machado_gray_point,
    gray_point_details,
)

# ============================================================================
# Configuration
# ============================================================================

CVD_TYPE = {'08': 'deutan', '09': 'protan', '10': 'normal'}

# ROIs we fit on (V1, V2) and the held-out ROI (hV4, stored as V4 on disk).
# The external name in outputs stays 'hV4' for the held-out ROI so the rest
# of the Gen-4 pipeline can speak in Machado-paper terms; the on-disk dir is
# mapped via DISK_ROI.
LOGICAL_ROIS = ('V1', 'V2', 'hV4')
DISK_ROI = {'V1': 'V1', 'V2': 'V2', 'hV4': 'V4'}

# ΔRDM_obs is used ONLY by the V1+V2 L₃ loss (Stage 1/2). hV4 is held out for
# NEURAL (LOCO) and COGNITION (Machado canonical) validation, so we skip its
# observed ΔRDM to avoid shipping an unused artefact and to prevent confusion
# in the log output ("hV4 ΔRDM" could falsely suggest hV4 enters the fit).
# HC W, by contrast, IS needed for hV4 — Stage 3a simulates the mean-HC LOCO
# vulnerability through hc_W_hV4, and Stage 3b computes ΔRDM_sim for
# fitted-vs-Machado comparison, so hc_W is computed for every LOGICAL_ROI.
DRDM_ROIS = ('V1', 'V2')

LOCAL_BASELINE = (Path(__file__).resolve().parent.parent.parent.parent
                  / 'phase1_preprocess_decoding' / 'results' / 'full_dataset_C010')


# ============================================================================
# Helpers
# ============================================================================

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description='Gen-4 Stage 0 precompute (HC W, ΔRDM_obs, Stockman, gray check)')
    p.add_argument('--baseline_dir', type=str, default=str(LOCAL_BASELINE),
                   help='C010 amplitudes root (default: local)')
    p.add_argument('--output_dir', type=str,
                   default='results/step0_precompute',
                   help='Where to write the npz/json caches')
    p.add_argument('--rois', nargs='+', default=list(LOGICAL_ROIS),
                   help='Logical ROI names (V1, V2, hV4)')
    p.add_argument('--hc_subjects', nargs='+', default=HC_SUBJECTS,
                   help='HC subject IDs')
    p.add_argument('--cvd_subjects', nargs='+', default=CVD_SUBJECTS,
                   help='CVD subject IDs')
    p.add_argument('--skip_gray_check', action='store_true',
                   help='Skip the Machado D65 gray-point sanity check')
    p.add_argument('--gray_tolerance_deg', type=float, default=2.5,
                   help='Max allowed D65 chromatic-drift (degrees). Default '
                        '2.5° = LSQ-projection residual floor for Machado-'
                        'mixed cones.')
    return p.parse_args()


def _save_stockman_grid(output_dir: Path) -> Dict:
    """Persist the Stockman 1 nm grid + area terms + XYZ→LMS matrix."""
    wl, L, M, S, area_L, area_M, M_xyz2lms = _load_stockman_grid()
    out_path = output_dir / 'stockman_grid.npz'
    np.savez_compressed(
        out_path,
        wl=wl,
        L=L,
        M=M,
        S=S,
        area_L=np.array(area_L, dtype=float),
        area_M=np.array(area_M, dtype=float),
        M_xyz2lms=M_xyz2lms,
        delta_lambda_max=np.array(DELTA_LAMBDA_MAX, dtype=float),
        machado_area_constant=np.array(MACHADO_AREA_CONSTANT, dtype=float),
    )
    return {
        'path': str(out_path),
        'wl_min': float(wl.min()),
        'wl_max': float(wl.max()),
        'n_points': int(wl.size),
        'area_L': float(area_L),
        'area_M': float(area_M),
        'area_ratio_L_over_M': float(area_L / max(area_M, 1e-12)),
    }


def _run_gray_check(tolerance_deg: float) -> Dict:
    """Run verify_machado_gray_point and record the per-(Δλ, cvd) deviations."""
    ok = verify_machado_gray_point(tolerance_deg=tolerance_deg, verbose=False)
    details = gray_point_details()  # list of (cvd_type, Δλ, deviation_deg)
    return {
        'ok': bool(ok),
        'tolerance_deg': float(tolerance_deg),
        'details': [
            {'cvd_type': c, 'delta_lambda_nm': float(d), 'deviation_deg': float(dev)}
            for c, d, dev in details
        ],
    }


def _load_all_hc_amplitudes(baseline_dir: str,
                            hc_subjects,
                            disk_roi: str) -> Dict[str, np.ndarray]:
    """Load (6,8,V_s) amplitudes for every HC subject at a single ROI."""
    out = {}
    for subj in hc_subjects:
        out[subj] = load_amplitudes(baseline_dir, subj, disk_roi)
    return out


def _save_hc_W(hc_W_dict: Dict[str, np.ndarray],
               hc_alpha_dict: Dict[str, float],
               output_dir: Path,
               logical_roi: str) -> Dict:
    """Persist precomputed HC weights for a single ROI.

    File layout (npz):
        key 'subj_ids'     — array of HC subject IDs (object dtype)
        key 'alphas'       — array of selected ridge alphas
        key 'W_<subj>'     — (K, V_s) per subject
    """
    out_path = output_dir / f'hc_W_{logical_roi}.npz'
    payload = {
        'subj_ids': np.array(list(hc_W_dict.keys()), dtype=object),
        'alphas': np.array([hc_alpha_dict[s] for s in hc_W_dict], dtype=float),
    }
    for subj, W in hc_W_dict.items():
        payload[f'W_{subj}'] = W.astype(np.float32)
    np.savez_compressed(out_path, **payload)

    return {
        'path': str(out_path),
        'roi': logical_roi,
        'n_hc': len(hc_W_dict),
        'K': int(next(iter(hc_W_dict.values())).shape[0]),
        'V_s_per_subj': {
            subj: int(W.shape[1]) for subj, W in hc_W_dict.items()
        },
        'alphas': {s: float(a) for s, a in hc_alpha_dict.items()},
    }


def _save_delta_rdm_obs(delta_rdms: Dict[str, np.ndarray],
                        rdm_cvds: Dict[str, np.ndarray],
                        rdm_hc_means: Dict[str, np.ndarray],
                        output_dir: Path,
                        logical_roi: str) -> Dict:
    """Persist observed ΔRDM (28-vector) per CVD subject for a single ROI."""
    out_path = output_dir / f'delta_rdm_obs_{logical_roi}.npz'
    payload = {
        'cvd_ids': np.array(list(delta_rdms.keys()), dtype=object),
    }
    for subj, d in delta_rdms.items():
        payload[f'delta_rdm_{subj}'] = d.astype(np.float64)
        payload[f'rdm_cvd_{subj}'] = rdm_cvds[subj].astype(np.float64)
        payload[f'rdm_hc_mean_{subj}'] = rdm_hc_means[subj].astype(np.float64)
    np.savez_compressed(out_path, **payload)

    return {
        'path': str(out_path),
        'roi': logical_roi,
        'cvd_subjects': list(delta_rdms.keys()),
        'delta_rdm_abs_mean': {
            subj: float(np.mean(np.abs(d))) for subj, d in delta_rdms.items()
        },
        'delta_rdm_std': {
            subj: float(np.std(d)) for subj, d in delta_rdms.items()
        },
    }


# ============================================================================
# Main
# ============================================================================

def main() -> None:
    args = _parse_args()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    print('=' * 64)
    print('Gen-4 Stage 0 Precompute')
    print(f'  baseline_dir : {args.baseline_dir}')
    print(f'  output_dir   : {output_dir}')
    print(f'  HC subjects  : {args.hc_subjects}')
    print(f'  CVD subjects : {args.cvd_subjects}')
    print(f'  ROIs         : {args.rois}')
    print('=' * 64)

    manifest = {
        'timestamp': datetime.now().isoformat(),
        'baseline_dir': args.baseline_dir,
        'hc_subjects': list(args.hc_subjects),
        'cvd_subjects': list(args.cvd_subjects),
        'rois': list(args.rois),
        'delta_lambda_max': DELTA_LAMBDA_MAX,
        'machado_area_constant': MACHADO_AREA_CONSTANT,
    }

    # --- 1. Stockman grid cache --------------------------------------------
    print('\n[1/4] Caching Stockman fundamentals + area terms...')
    stockman_info = _save_stockman_grid(output_dir)
    manifest['stockman_grid'] = stockman_info
    print(f'  wl: {stockman_info["wl_min"]:.0f}-{stockman_info["wl_max"]:.0f} nm '
          f'({stockman_info["n_points"]} pts)')
    print(f'  Area_L = {stockman_info["area_L"]:.4f}, '
          f'Area_M = {stockman_info["area_M"]:.4f}  '
          f'(L/M = {stockman_info["area_ratio_L_over_M"]:.4f})')
    print(f'  saved → {stockman_info["path"]}')

    # --- 2. Machado D65 gray-point sanity check ----------------------------
    if not args.skip_gray_check:
        print('\n[2/4] Machado D65 gray-point sanity check...')
        gray = _run_gray_check(args.gray_tolerance_deg)
        gray_path = output_dir / 'machado_gray_check.json'
        with open(gray_path, 'w') as f:
            json.dump(gray, f, indent=2)
        manifest['machado_gray_check'] = {
            'ok': gray['ok'],
            'tolerance_deg': gray['tolerance_deg'],
            'max_deviation_deg': max(
                (d['deviation_deg'] for d in gray['details']), default=0.0),
            'path': str(gray_path),
        }
        verdict = 'PASS' if gray['ok'] else 'FAIL'
        print(f'  tolerance = {gray["tolerance_deg"]:.2f}°')
        print(f'  max |deviation| = '
              f'{manifest["machado_gray_check"]["max_deviation_deg"]:.3f}°')
        print(f'  verdict: {verdict}')
        if not gray['ok']:
            print('  WARNING: gray-point check failed — '
                  'Stockman area integration differs from Machado 0.96 '
                  'calibration. Fix before running downstream stages.')
        print(f'  saved → {gray_path}')
    else:
        print('\n[2/4] Skipping Machado gray-point check (--skip_gray_check).')
        manifest['machado_gray_check'] = {'ok': None, 'skipped': True}

    # --- 3. Precompute HC W + observed ΔRDM per ROI ------------------------
    print('\n[3/4] Per-ROI HC W + observed ΔRDM...')
    C_baseline = create_basis_matrix(HUE_ANGLES, N_CHANNELS)  # (8, K)
    print(f'  C_baseline shape: {C_baseline.shape}')

    manifest['rois'] = {}
    for logical_roi in args.rois:
        disk_roi = DISK_ROI.get(logical_roi, logical_roi)
        print(f'\n  --- ROI {logical_roi} (on disk: {disk_roi}) ---')

        hc_amps = _load_all_hc_amplitudes(
            args.baseline_dir, args.hc_subjects, disk_roi)
        vs_summary = ', '.join(
            f'{s}:{a.shape[2]}' for s, a in hc_amps.items())
        print(f'    HC amps loaded ({vs_summary})')

        hc_W, hc_alphas = precompute_hc_W(hc_amps, C_baseline)
        alpha_str = ', '.join(f'{s}={a:.2f}' for s, a in hc_alphas.items())
        print(f'    HC W computed (alphas: {alpha_str})')
        hc_W_info = _save_hc_W(hc_W, hc_alphas, output_dir, logical_roi)
        print(f'    saved → {hc_W_info["path"]}')

        roi_entry = {
            'disk_name': disk_roi,
            'hc_W': hc_W_info,
        }

        # Observed ΔRDM per CVD subject — V1/V2 only.
        # hV4 is held out for NEURAL (LOCO) and COGNITION (Machado canonical)
        # validation and must not enter the L₃ loss, so we do NOT compute
        # its ΔRDM_obs here. hc_W_hV4 is still saved above for Stage 3a/3b.
        if logical_roi in DRDM_ROIS:
            delta_rdms = {}
            rdm_cvds = {}
            rdm_hc_means = {}
            for cvd_subj in args.cvd_subjects:
                amp_cvd = load_amplitudes(args.baseline_dir, cvd_subj, disk_roi)
                delta_obs, rdm_cvd, rdm_hc_mean, _ = compute_delta_rdm_obs(
                    amp_cvd, hc_amps, distance='correlation')
                delta_rdms[cvd_subj] = delta_obs
                rdm_cvds[cvd_subj] = rdm_cvd
                rdm_hc_means[cvd_subj] = rdm_hc_mean
                print(f'    sub-{cvd_subj} ({CVD_TYPE.get(cvd_subj, "?")}): '
                      f'||ΔRDM|| = {np.linalg.norm(delta_obs):.4f}, '
                      f'abs_mean = {np.mean(np.abs(delta_obs)):.4f}')

            drdm_info = _save_delta_rdm_obs(
                delta_rdms, rdm_cvds, rdm_hc_means, output_dir, logical_roi)
            print(f'    saved → {drdm_info["path"]}')
            roi_entry['delta_rdm_obs'] = drdm_info
        else:
            print('    ΔRDM_obs skipped (held out — LOCO/Machado validation only)')
            roi_entry['delta_rdm_obs'] = {'skipped': True, 'reason': 'held_out'}

        manifest['rois'][logical_roi] = roi_entry

    # --- 4. Write manifest -------------------------------------------------
    print('\n[4/4] Writing manifest...')
    manifest_path = output_dir / 'step0_manifest.json'
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2, default=str)
    print(f'  saved → {manifest_path}')

    print('\nStep 0 precompute complete.')


if __name__ == '__main__':
    main()
