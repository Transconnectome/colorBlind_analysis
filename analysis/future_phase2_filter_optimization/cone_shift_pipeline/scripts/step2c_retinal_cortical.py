#!/usr/bin/env python3
"""
step2c_retinal_cortical.py — 2-stage retinal + cortical compensation fitting.

Model: Machado retinal shift + opponent R-G gain (3 DOF: Δλ_V1, Δλ_V2, g).

Sub-08 (deutan) has large, coherent ΔRDM (V1↔V2 r=0.78) but Machado
retinal-only predicts the WRONG direction: observed = expansion, predicted
= compression (cosine = -0.340). This is consistent with Tregillus et al.'s
cortical compensation: post-receptoral R-G gain overcompensation produces
neural distance expansion despite retinal L-M separation reduction.

Algorithm:
    Phase A — Coarse per-ROI 2D grid (Δλ × g) to find anchors
    Phase B — Fine joint 3D grid (Δλ_V1 × Δλ_V2 × g) with all penalties
    Phase C — 8! permutation null at (Δλ*, g*)
    Phase D — Inline LOCO validation with compensation-aware C_final

Usage (local, CPU):
    python scripts/step2c_retinal_cortical.py \\
        --step0_dir results/step0_precompute \\
        --step1_dir results/step1_machado_anchor \\
        --output_dir results/step2c_retinal_cortical \\
        --subjects 08

Reused helpers:
    L3_RetinalCortical                         (l3_loss.py)
    get_design_matrix_rc, opponent_gain_diagnostic (retinal_cortical.py)
    compute_delta_rdm_sim, cosine_similarity   (diagnostic_delta_rdm.py)
    simulate_mean_hc_wfixed, load_cvd_loco_target,
        permutation_test_spearman              (step1_fit_loco_v2.py)
    create_basis_matrix, load_amplitudes       (utils_forward_model.py)
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import numpy as np
from scipy.stats import spearmanr

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

_FWD_DIR = str(Path(__file__).resolve().parent.parent.parent.parent
               / 'future_phase1_forward_model' / 'scripts')
if _FWD_DIR not in sys.path:
    sys.path.insert(0, _FWD_DIR)

from diagnostic_delta_rdm import (  # noqa: E402
    compute_delta_rdm_sim,
    cosine_similarity,
)
from l3_loss import L3_RetinalCortical, _similarity  # noqa: E402
from machado_simulator import DELTA_LAMBDA_MAX  # noqa: E402
from retinal_cortical import (  # noqa: E402
    get_design_matrix_rc,
    opponent_gain_diagnostic,
)
from step1_fit_loco_v2 import (  # noqa: E402
    load_cvd_loco_target,
    permutation_test_spearman,
    precompute_hc_W,
    simulate_mean_hc_wfixed,
)
from utils_distortion_models import get_design_matrix  # noqa: E402
from utils_forward_model import (  # noqa: E402
    HC_SUBJECTS,
    HUE_ANGLES,
    N_CHANNELS,
    create_basis_matrix,
    load_amplitudes,
)

# ============================================================================
# Config
# ============================================================================

CVD_TYPE = {'08': 'deutan', '09': 'protan', '10': 'normal'}

FIT_ROIS = ('V1', 'V2')
LOCO_ROIS = ('V1', 'V2', 'V4')  # hV4 = V4 on disk

LOCAL_BASELINE = Path(__file__).resolve().parent.parent.parent.parent \
    / 'phase1_procrustes_decoding' / 'results' / 'visualization' \
    / 'full_dataset_C010_with_residuals'

# Defaults
DEFAULT_G_MIN = -3.0   # Negative g = overcompensation (Tregillus)
DEFAULT_G_MAX = 2.0
DEFAULT_G_STEP_COARSE = 0.1
DEFAULT_G_STEP_FINE = 0.02
DEFAULT_DL_STEP_COARSE = 1.0
DEFAULT_DL_STEP_FINE = 0.5
DEFAULT_DL_MAX = 20.0
DEFAULT_FINE_WINDOW = 3.0  # ± nm around anchor


# ============================================================================
# Cache loaders (same as step2_finetune_l3_v2.py)
# ============================================================================

def _load_hc_W(step0_dir: Path, logical_roi: str) -> Dict[str, np.ndarray]:
    path = step0_dir / f'hc_W_{logical_roi}.npz'
    if not path.exists():
        raise FileNotFoundError(f'Missing Stage-0 HC W cache: {path}')
    data = np.load(path, allow_pickle=True)
    subj_ids = list(data['subj_ids'])
    return {s: np.asarray(data[f'W_{s}'], dtype=np.float64) for s in subj_ids}


def _load_delta_rdm_obs(step0_dir: Path,
                        logical_roi: str) -> Dict[str, np.ndarray]:
    path = step0_dir / f'delta_rdm_obs_{logical_roi}.npz'
    if not path.exists():
        raise FileNotFoundError(f'Missing Stage-0 ΔRDM_obs cache: {path}')
    data = np.load(path, allow_pickle=True)
    cvd_ids = list(data['cvd_ids'])
    return {s: np.asarray(data[f'delta_rdm_{s}'], dtype=np.float64)
            for s in cvd_ids}


# ============================================================================
# Phase A: Coarse per-ROI anchor
# ============================================================================

def _phase_a_coarse_anchor(
    loss: L3_RetinalCortical,
    cvd_type: str,
    hc_W_roi: Dict[str, np.ndarray],
    C_baseline: np.ndarray,
    delta_rdm_obs_roi: np.ndarray,
    roi: str,
    dl_grid: np.ndarray,
    g_grid: np.ndarray,
) -> dict:
    """Per-ROI coarse 2D grid (Δλ × g) → anchor (Δλ*, g*, L₁).

    Returns dict with anchor point and full landscape.
    """
    n_dl = dl_grid.size
    n_g = g_grid.size
    landscape = np.full((n_dl, n_g), -np.inf)

    for i, dl in enumerate(dl_grid):
        for j, g in enumerate(g_grid):
            C_final = get_design_matrix_rc(
                float(dl), float(g), cvd_type, N_CHANNELS)
            delta_sim, _ = compute_delta_rdm_sim(
                hc_W_roi, C_final, C_baseline, distance='correlation')
            landscape[i, j] = float(
                _similarity(delta_sim, delta_rdm_obs_roi, loss.metric))

    i_best, j_best = np.unravel_index(
        int(np.argmax(landscape)), landscape.shape)
    return {
        'roi': roi,
        'dl_anchor': float(dl_grid[i_best]),
        'g_anchor': float(g_grid[j_best]),
        'l1_anchor': float(landscape[i_best, j_best]),
        'landscape_shape': [n_dl, n_g],
    }


# ============================================================================
# Phase B: Fine joint 3D grid
# ============================================================================

def _precompute_retinal_drdm(
    hc_W_roi: Dict[str, np.ndarray],
    dl_values: np.ndarray,
    cvd_type: str,
    C_baseline: np.ndarray,
) -> Dict[float, np.ndarray]:
    """Precompute retinal-only ΔRDM for each unique Δλ (no gain).

    Used for dominance penalty computation.
    """
    cache = {}
    for dl in dl_values:
        dl_f = float(dl)
        if dl_f not in cache:
            C_ret = get_design_matrix('machado_1way', [dl_f], cvd_type=cvd_type)
            drdm, _ = compute_delta_rdm_sim(
                hc_W_roi, C_ret, C_baseline, distance='correlation')
            cache[dl_f] = drdm
    return cache


def _phase_b_fine_joint(
    loss: L3_RetinalCortical,
    cvd_type: str,
    hc_W_dicts: Dict[str, Dict[str, np.ndarray]],
    C_baseline: np.ndarray,
    delta_rdm_obs_dicts: Dict[str, np.ndarray],
    dl_v1_grid: np.ndarray,
    dl_v2_grid: np.ndarray,
    g_grid: np.ndarray,
) -> dict:
    """Fine 3D grid search over (Δλ_V1, Δλ_V2, g).

    Precomputes retinal-only ΔRDM for dominance penalty, then sweeps
    all (Δλ_V1, Δλ_V2, g) combinations with full L₃_rc scoring.

    Returns dict with best params and landscape stats.
    """
    n_v1, n_v2, n_g = dl_v1_grid.size, dl_v2_grid.size, g_grid.size
    total = n_v1 * n_v2 * n_g

    # Precompute retinal-only ΔRDM caches per ROI
    ret_cache_V1 = _precompute_retinal_drdm(
        hc_W_dicts['V1'], dl_v1_grid, cvd_type, C_baseline)
    ret_cache_V2 = _precompute_retinal_drdm(
        hc_W_dicts['V2'], dl_v2_grid, cvd_type, C_baseline)

    # Precompute baseline RDMs per HC (constant across grid)
    # These are used inside compute_delta_rdm_sim via C_baseline @ W
    # — no extra caching needed, compute_delta_rdm_sim already computes both.

    # Precompute C_final for each (Δλ, g) combination per ROI
    # C_final only depends on (Δλ, g), not on HC. Precompute (Δλ, g) → C_final.
    # Then compute ΔRDM_sim for each (Δλ, g, ROI) combination.
    # This is the bottleneck: compute_delta_rdm_sim ~ 1ms per call.

    best_l3 = -np.inf
    best_params = {'dv1': 0.0, 'dv2': 0.0, 'g': 0.0}
    best_result = None

    # Progress tracking
    t_start = time.time()
    n_done = 0
    report_interval = max(1, total // 20)

    for iv1, dv1 in enumerate(dl_v1_grid):
        for iv2, dv2 in enumerate(dl_v2_grid):
            for ig, g_val in enumerate(g_grid):
                ret_cache = {
                    'V1': ret_cache_V1.get(float(dv1)),
                    'V2': ret_cache_V2.get(float(dv2)),
                }
                result = loss.compute_rc(
                    delta_v1=float(dv1),
                    delta_v2=float(dv2),
                    g=float(g_val),
                    cvd_type=cvd_type,
                    hc_W_dicts=hc_W_dicts,
                    C_baseline=C_baseline,
                    delta_rdm_obs_dicts=delta_rdm_obs_dicts,
                    delta_rdm_ret_cache=ret_cache,
                )
                if result['l3_rc'] > best_l3:
                    best_l3 = result['l3_rc']
                    best_params = {
                        'dv1': float(dv1),
                        'dv2': float(dv2),
                        'g': float(g_val),
                    }
                    best_result = result

                n_done += 1
                if n_done % report_interval == 0:
                    elapsed = time.time() - t_start
                    rate = n_done / max(elapsed, 0.01)
                    eta = (total - n_done) / max(rate, 0.01)
                    print(f'      [{n_done}/{total}] '
                          f'{elapsed:.0f}s elapsed, ~{eta:.0f}s remaining')

    elapsed_total = time.time() - t_start
    print(f'      Phase B complete: {total} points in {elapsed_total:.1f}s')

    return {
        'best': best_result,
        'best_params': best_params,
        'grid_shape': [n_v1, n_v2, n_g],
        'n_evaluated': total,
        'elapsed_s': elapsed_total,
    }


# ============================================================================
# Phase D: Inline LOCO validation
# ============================================================================

def _phase_d_loco_validation(
    best_dv1: float,
    best_dv2: float,
    best_g: float,
    cvd_type: str,
    cvd_subj: str,
    baseline_dir: Path,
) -> dict:
    """LOCO validation with compensation-aware C_final.

    For V1/V2: use per-ROI Δλ. For hV4: use Δλ_bar = mean(Δλ_V1, Δλ_V2).
    """
    delta_bar = 0.5 * (best_dv1 + best_dv2)
    loco_results = {}

    for roi in LOCO_ROIS:
        # Choose Δλ: per-ROI for V1/V2, bar for hV4
        if roi == 'V1':
            dl_roi = best_dv1
        elif roi == 'V2':
            dl_roi = best_dv2
        else:  # V4 = hV4
            dl_roi = delta_bar

        try:
            # Load amplitudes
            hc_amps = {}
            for subj in HC_SUBJECTS:
                hc_amps[subj] = load_amplitudes(str(baseline_dir), subj, roi)

            # Precompute W from unshifted design
            C_original = create_basis_matrix(HUE_ANGLES, N_CHANNELS)
            hc_W, _ = precompute_hc_W(hc_amps, C_original)

            # Compensation-aware C_final
            C_final = get_design_matrix_rc(dl_roi, best_g, cvd_type, N_CHANNELS)
            vuln_fit, _ = simulate_mean_hc_wfixed(hc_W, hc_amps, C_final)

            # Baseline (no shift, no gain)
            vuln_base, _ = simulate_mean_hc_wfixed(hc_W, hc_amps, C_original)

            # Load CVD LOCO target
            cvd_vuln = load_cvd_loco_target(cvd_subj, roi)

            # Spearman
            rho_fit, _ = spearmanr(vuln_fit, cvd_vuln)
            rho_base, _ = spearmanr(vuln_base, cvd_vuln)
            rho_fit = float(rho_fit) if np.isfinite(rho_fit) else 0.0
            rho_base = float(rho_base) if np.isfinite(rho_base) else 0.0

            # 8! permutation test
            label_p, _, _ = permutation_test_spearman(vuln_fit, cvd_vuln)

            loco_results[roi] = {
                'rho_fit': rho_fit,
                'rho_base': rho_base,
                'delta_rho': rho_fit - rho_base,
                'label_p': label_p,
                'delta_lambda_used': float(dl_roi),
                'vuln_fit': vuln_fit.tolist(),
                'vuln_base': vuln_base.tolist(),
                'cvd_vuln': cvd_vuln.tolist(),
            }
            print(f'      LOCO {roi}: ρ_fit={rho_fit:.3f}, '
                  f'ρ_base={rho_base:.3f}, Δρ={rho_fit - rho_base:+.3f}, '
                  f'label_p={label_p:.4f}')

        except FileNotFoundError as e:
            print(f'      LOCO {roi}: SKIPPED ({e})')
            loco_results[roi] = {'error': str(e)}

    return loco_results


# ============================================================================
# Main per-subject pipeline
# ============================================================================

def fit_subject(
    cvd_subj: str,
    model: str,
    step0_dir: Path,
    baseline_dir: Path,
    loss: L3_RetinalCortical,
    dl_max: float,
    dl_step_coarse: float,
    dl_step_fine: float,
    g_min: float,
    g_max: float,
    g_step_coarse: float,
    g_step_fine: float,
    fine_window: float,
) -> dict:
    """Full fitting pipeline for one CVD subject."""
    cvd_type = CVD_TYPE[cvd_subj]
    print(f'\n  === sub-{cvd_subj} ({cvd_type}) ===')

    # Load Stage-0 caches
    hc_W_dicts: Dict[str, Dict[str, np.ndarray]] = {}
    delta_rdm_obs_all: Dict[str, Dict[str, np.ndarray]] = {}
    for roi in FIT_ROIS:
        hc_W_dicts[roi] = _load_hc_W(step0_dir, roi)
        delta_rdm_obs_all[roi] = _load_delta_rdm_obs(step0_dir, roi)
    delta_rdm_obs = {roi: delta_rdm_obs_all[roi][cvd_subj]
                     for roi in FIT_ROIS}

    # Stockman-derived baseline (Δλ=0 → ΔRDM_sim = 0 by construction)
    C_baseline = get_design_matrix('machado_1way', [0.0], cvd_type='protan')

    # Coarse grids
    dl_coarse = np.arange(0, dl_max + 1e-9, dl_step_coarse)
    g_coarse = np.arange(g_min, g_max + 1e-9, g_step_coarse)

    # ------------------------------------------------------------------
    # Phase A: Coarse per-ROI anchors
    # ------------------------------------------------------------------
    print('    Phase A: Coarse per-ROI anchors')
    anchors = {}
    for roi in FIT_ROIS:
        t0 = time.time()
        anchor = _phase_a_coarse_anchor(
            loss=loss,
            cvd_type=cvd_type,
            hc_W_roi=hc_W_dicts[roi],
            C_baseline=C_baseline,
            delta_rdm_obs_roi=delta_rdm_obs[roi],
            roi=roi,
            dl_grid=dl_coarse,
            g_grid=g_coarse,
        )
        anchors[roi] = anchor
        dt = time.time() - t0
        print(f'      {roi}: Δλ*={anchor["dl_anchor"]:.1f} nm, '
              f'g*={anchor["g_anchor"]:.2f}, L₁={anchor["l1_anchor"]:.4f} '
              f'({dt:.1f}s)')

    # ------------------------------------------------------------------
    # Phase B: Fine joint 3D grid
    # ------------------------------------------------------------------
    print('    Phase B: Fine joint 3D grid')

    # Build fine grids around anchors
    dl_v1_center = anchors['V1']['dl_anchor']
    dl_v2_center = anchors['V2']['dl_anchor']
    g_center = 0.5 * (anchors['V1']['g_anchor'] + anchors['V2']['g_anchor'])

    dl_v1_fine = np.arange(
        max(0, dl_v1_center - fine_window),
        min(dl_max, dl_v1_center + fine_window) + 1e-9,
        dl_step_fine)
    dl_v2_fine = np.arange(
        max(0, dl_v2_center - fine_window),
        min(dl_max, dl_v2_center + fine_window) + 1e-9,
        dl_step_fine)
    g_fine = np.arange(g_min, g_max + 1e-9, g_step_fine)

    print(f'      V1 grid: [{dl_v1_fine[0]:.1f}, {dl_v1_fine[-1]:.1f}] '
          f'step {dl_step_fine} ({dl_v1_fine.size} pts)')
    print(f'      V2 grid: [{dl_v2_fine[0]:.1f}, {dl_v2_fine[-1]:.1f}] '
          f'step {dl_step_fine} ({dl_v2_fine.size} pts)')
    print(f'      g  grid: [{g_min}, {g_max}] step {g_step_fine} ({g_fine.size} pts)')
    print(f'      total:   {dl_v1_fine.size * dl_v2_fine.size * g_fine.size}')

    phase_b = _phase_b_fine_joint(
        loss=loss,
        cvd_type=cvd_type,
        hc_W_dicts=hc_W_dicts,
        C_baseline=C_baseline,
        delta_rdm_obs_dicts=delta_rdm_obs,
        dl_v1_grid=dl_v1_fine,
        dl_v2_grid=dl_v2_fine,
        g_grid=g_fine,
    )

    best = phase_b['best']
    bp = phase_b['best_params']
    print(f'    Best: Δλ_V1={bp["dv1"]:.2f}, Δλ_V2={bp["dv2"]:.2f}, '
          f'g={bp["g"]:.3f}')
    print(f'          L₃_rc={best["l3_rc"]:.4f}, '
          f'L₁={best["l1"]:.4f} '
          f'(V1={best["l1_V1"]:.4f}, V2={best["l1_V2"]:.4f})')
    print(f'          cosine_full V1={best["cosine_full_V1"]:.4f}, '
          f'V2={best["cosine_full_V2"]:.4f}')
    print(f'          sign_full V1={best["sign_agree_full_V1"]:.2%}, '
          f'V2={best["sign_agree_full_V2"]:.2%}')

    # Baseline at (0, 0, 0)
    baseline = loss.compute_rc(
        0.0, 0.0, 0.0, cvd_type,
        hc_W_dicts, C_baseline, delta_rdm_obs)
    print(f'    Baseline (0,0,0): L₃_rc={baseline["l3_rc"]:.4f}, '
          f'cos_V1={baseline["cosine_full_V1"]:.4f}, '
          f'cos_V2={baseline["cosine_full_V2"]:.4f}')

    # Sanity check: retinal-only (g=0) at best Δλ
    retinal_only = loss.compute_rc(
        bp['dv1'], bp['dv2'], 0.0, cvd_type,
        hc_W_dicts, C_baseline, delta_rdm_obs)
    print(f'    Retinal-only (g=0): L₃_rc={retinal_only["l3_rc"]:.4f}, '
          f'cos_V1={retinal_only["cosine_full_V1"]:.4f}, '
          f'cos_V2={retinal_only["cosine_full_V2"]:.4f}')

    # ------------------------------------------------------------------
    # Phase C: Permutation null
    # ------------------------------------------------------------------
    print('    Phase C: 8! permutation null')
    t0 = time.time()
    perm_result = loss.permutation_null_rc(
        best_dv1=bp['dv1'],
        best_dv2=bp['dv2'],
        best_g=bp['g'],
        cvd_type=cvd_type,
        hc_W_dicts=hc_W_dicts,
        C_baseline=C_baseline,
        delta_rdm_obs_dicts=delta_rdm_obs,
        baseline_l3=baseline['l3_rc'],
    )
    dt = time.time() - t0
    print(f'      label_perm_p = {perm_result["label_perm_p"]:.5f} ({dt:.1f}s)')
    if 'baseline_improvement_p' in perm_result:
        print(f'      baseline_improvement_p = '
              f'{perm_result["baseline_improvement_p"]:.5f}')

    # ------------------------------------------------------------------
    # Phase D: Inline LOCO validation
    # ------------------------------------------------------------------
    print('    Phase D: Inline LOCO validation')
    loco_validation = _phase_d_loco_validation(
        best_dv1=bp['dv1'],
        best_dv2=bp['dv2'],
        best_g=bp['g'],
        cvd_type=cvd_type,
        cvd_subj=cvd_subj,
        baseline_dir=baseline_dir,
    )

    # ------------------------------------------------------------------
    # Opponent gain diagnostic
    # ------------------------------------------------------------------
    diag = opponent_gain_diagnostic(
        0.5 * (bp['dv1'] + bp['dv2']),
        bp['g'], cvd_type)

    # ------------------------------------------------------------------
    # Assemble output
    # ------------------------------------------------------------------
    output = {
        'subject': cvd_subj,
        'cvd_type': cvd_type,
        'model': model,
        'comp_type': 'opponent_rg',
        'timestamp': datetime.now().isoformat(),
        'best': {
            'delta_v1_nm': bp['dv1'],
            'delta_v2_nm': bp['dv2'],
            'g': bp['g'],
            **{k: v for k, v in best.items()
               if isinstance(v, (int, float)) and v is not None},
        },
        'baseline': {
            k: v for k, v in baseline.items()
            if isinstance(v, (int, float)) and v is not None
        },
        'retinal_only': {
            k: v for k, v in retinal_only.items()
            if isinstance(v, (int, float)) and v is not None
        },
        'permutation_null': perm_result,
        'loco_validation': loco_validation,
        'opponent_gain_diagnostic': diag,
        'anchors': anchors,
        'phase_b_meta': {
            'grid_shape': phase_b['grid_shape'],
            'n_evaluated': phase_b['n_evaluated'],
            'elapsed_s': phase_b['elapsed_s'],
            'dl_v1_range': [float(dl_v1_fine[0]), float(dl_v1_fine[-1])],
            'dl_v2_range': [float(dl_v2_fine[0]), float(dl_v2_fine[-1])],
            'g_range': [float(g_min), float(g_max)],
        },
        'loss_params': {
            'lam_scale': loss.lam_scale,
            'lam_roi': loss.lam_roi,
            'lam_couple': loss.lam_couple,
            'couple_eps': loss.couple_eps,
            'lam_dom': loss.lam_dom,
            'dom_tau': loss.dom_tau,
            'delta_lambda_max': loss.delta_lambda_max,
            'metric': loss.metric,
        },
    }
    return output


# ============================================================================
# CLI + Main
# ============================================================================

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description='2-stage retinal + cortical compensation fitting')
    p.add_argument('--step0_dir', type=str,
                   default='results/step0_precompute')
    p.add_argument('--step1_dir', type=str,
                   default='results/step1_machado_anchor',
                   help='Stage-1 anchor results (for reference only)')
    p.add_argument('--output_dir', type=str,
                   default='results/step2c_retinal_cortical')
    p.add_argument('--baseline_dir', type=str,
                   default=str(LOCAL_BASELINE),
                   help='C010 amplitudes directory (for LOCO validation)')
    p.add_argument('--subjects', nargs='+', default=['08'])
    p.add_argument('--model', type=str, default='machado_1way')
    # Grid parameters
    p.add_argument('--dl_max', type=float, default=DEFAULT_DL_MAX)
    p.add_argument('--dl_step_coarse', type=float,
                   default=DEFAULT_DL_STEP_COARSE)
    p.add_argument('--dl_step_fine', type=float, default=DEFAULT_DL_STEP_FINE)
    p.add_argument('--g_min', type=float, default=DEFAULT_G_MIN,
                   help='Min g (negative = overcompensation per Tregillus)')
    p.add_argument('--g_max', type=float, default=DEFAULT_G_MAX)
    p.add_argument('--g_step_coarse', type=float,
                   default=DEFAULT_G_STEP_COARSE)
    p.add_argument('--g_step_fine', type=float, default=DEFAULT_G_STEP_FINE)
    p.add_argument('--fine_window', type=float, default=DEFAULT_FINE_WINDOW)
    # Loss hyperparameters
    p.add_argument('--lam_scale', type=float, default=0.01)
    p.add_argument('--lam_roi', type=float, default=0.005)
    p.add_argument('--lam_couple', type=float, default=0.01,
                   help='Coupling penalty weight: λ_c * g² / (|Δλ_bar| + ε)')
    p.add_argument('--couple_eps', type=float, default=1.0,
                   help='ε in coupling penalty denominator (nm)')
    p.add_argument('--lam_dom', type=float, default=0.005)
    p.add_argument('--dom_tau', type=float, default=1.5)
    p.add_argument('--metric', type=str, default='cosine',
                   choices=['cosine', 'pearson', 'spearman'])
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    step0_dir = Path(args.step0_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    baseline_dir = Path(args.baseline_dir).resolve()

    print('=' * 72)
    print('Step 2c: Retinal + Cortical Compensation (opponent R-G gain)')
    print(f'  step0_dir    : {step0_dir}')
    print(f'  output_dir   : {output_dir}')
    print(f'  baseline_dir : {baseline_dir}')
    print(f'  subjects     : {args.subjects}')
    print(f'  model        : {args.model}')
    print(f'  Δλ max       : {args.dl_max} nm')
    print(f'  g range      : [{args.g_min}, {args.g_max}]')
    print(f'  fine window  : ±{args.fine_window} nm')
    print(f'  λ_couple={args.lam_couple}, ε_couple={args.couple_eps}, '
          f'λ_dom={args.lam_dom}, τ_dom={args.dom_tau}')
    print('=' * 72)

    loss = L3_RetinalCortical(
        lam_couple=args.lam_couple,
        couple_eps=args.couple_eps,
        lam_dom=args.lam_dom,
        dom_tau=args.dom_tau,
        lam_scale=args.lam_scale,
        lam_roi=args.lam_roi,
        delta_lambda_max=args.dl_max,
        metric=args.metric,
        model_name=args.model,
    )

    manifest = {
        'timestamp': datetime.now().isoformat(),
        'step0_dir': str(step0_dir),
        'model': args.model,
        'loss_params': {
            'lam_scale': args.lam_scale,
            'lam_roi': args.lam_roi,
            'lam_couple': args.lam_couple,
            'couple_eps': args.couple_eps,
            'lam_dom': args.lam_dom,
            'dom_tau': args.dom_tau,
            'metric': args.metric,
        },
        'grid_params': {
            'dl_max': args.dl_max,
            'dl_step_coarse': args.dl_step_coarse,
            'dl_step_fine': args.dl_step_fine,
            'g_max': args.g_max,
            'g_step_coarse': args.g_step_coarse,
            'g_step_fine': args.g_step_fine,
            'fine_window': args.fine_window,
        },
        'entries': [],
    }

    for cvd_subj in args.subjects:
        result = fit_subject(
            cvd_subj=cvd_subj,
            model=args.model,
            step0_dir=step0_dir,
            baseline_dir=baseline_dir,
            loss=loss,
            dl_max=args.dl_max,
            dl_step_coarse=args.dl_step_coarse,
            dl_step_fine=args.dl_step_fine,
            g_min=args.g_min,
            g_max=args.g_max,
            g_step_coarse=args.g_step_coarse,
            g_step_fine=args.g_step_fine,
            fine_window=args.fine_window,
        )

        out_path = output_dir / f'sub-{cvd_subj}_opponent_rg_{args.model}.json'
        with open(out_path, 'w') as f:
            json.dump(result, f, indent=2)
        print(f'    Saved: {out_path}')

        manifest['entries'].append({
            'subject': cvd_subj,
            'path': str(out_path),
            'delta_v1_nm': result['best']['delta_v1_nm'],
            'delta_v2_nm': result['best']['delta_v2_nm'],
            'g': result['best']['g'],
            'l3_rc': result['best']['l3_rc'],
            'label_perm_p': result['permutation_null']['label_perm_p'],
        })

    manifest_path = output_dir / 'step2c_manifest.json'
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    print(f'\nManifest -> {manifest_path}')
    print('Step 2c complete.')


if __name__ == '__main__':
    main()
