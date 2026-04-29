#!/usr/bin/env python3
"""
step2_finetune_l3_v2.py — Gen-4.5 Stage 2 joint V1+V2 L_total fine-tune.

Gen-4.5 loss (see l3_loss.py :: L3_MachadoV1V2_V2 for full derivation):

    L_total(Δλ_V1, Δλ_V2 | target_family) =
        L₁_joint_floor(target)
      + λ_sign · L_sign_joint(target)
      + λ_fam  · (L₁_joint_floor(target) − L₁_joint_floor(other))
      − λ_scale · L_scale
      − λ_ROI   · L_ROI

with
    L₁_joint_floor(fam) = 0.5·L₁_V1(fam) + 0.5·L₁_V2(fam)
                          − κ · max(0, τ − L₁_V2(fam))
    L_sign_joint(fam)   = 0.5 · (L_sign_V1(fam) + L_sign_V2(fam))

Defaults:
    λ_sign = 0.30, λ_fam = 0.50, τ = −0.02, κ = 0.5
    λ_scale = 0.01, λ_ROI = 0.005, Δλ_max = 20 nm

Search strategy — full 2-D grid [0, Δλ_max] at 0.5 nm step (default)
for BOTH target and other families. We do NOT anchor around Stage-1
because Gen-4.5 is expected to move the argmax if v1's (16.5, 3.0)
was a physiologically implausible local optimum.

Caching: ΔRDM_sim(Δλ, family, roi) only depends on Δλ through the 1-D
axis for that ROI. Therefore for each (ROI, family, Δλ) triple we
evaluate the ΔRDM_sim and its L₁ + L_sign once, and look them up at
the grid iteration step. This reduces cost from 41×41×4 = 6724
ΔRDM_sim evaluations to 41×2×2 = 164 evaluations per subject.

Outputs (results/step2_finetune_l3_v2/):

    sub-{ID}_{model}.json
        target_family / other_family, grid definition, loss params,
        full 2-D landscape (l_total, l1_joint_target, l1_joint_other,
        l_sign_joint, l_fam), best argmax, baseline at (0,0),
        v1_reference at Gen-4 v1 argmax for side-by-side comparison,
        selection_gate verdicts (sign / fam / V1+V2 L₁ floor).

    step2_v2_manifest.json

Usage (local, CPU):
    python scripts/step2_finetune_l3_v2.py \\
        --step0_dir results/step0_precompute \\
        --output_dir results/step2_finetune_l3_v2 \\
        --cvd_subjects 09 \\
        --models machado_1way

Reused helpers:
    L3_MachadoV1V2_V2            (l3_loss.py)
    compute_delta_rdm_sim        (diagnostic_delta_rdm.py)
    create_basis_matrix          (future_phase1_forward_model)
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

_FWD_DIR = str(Path(__file__).resolve().parent.parent.parent.parent
               / 'future_phase1_forward_model' / 'scripts')
if _FWD_DIR not in sys.path:
    sys.path.insert(0, _FWD_DIR)

from utils_forward_model import HUE_ANGLES, N_CHANNELS  # noqa: E402 (create_basis_matrix removed — use Stockman-derived baseline)
from l3_loss import L3_MachadoV1V2_V2  # noqa: E402
from machado_simulator import DELTA_LAMBDA_MAX  # noqa: E402

# ============================================================================
# Config
# ============================================================================

CVD_TYPE_NATIVE = {'08': 'deutan', '09': 'protan', '10': 'normal'}
CVD_TYPE_OTHER = {'protan': 'deutan', 'deutan': 'protan',
                  'normal': 'protan'}  # for sub-10 specificity, pair vs protan

FIT_ROIS = ('V1', 'V2')  # hV4 held out

# Loss hyperparameters (user-approved 2026-04-06)
DEFAULT_LAM_SCALE = 0.01
DEFAULT_LAM_ROI = 0.005
DEFAULT_LAM_SIGN = 0.30
DEFAULT_LAM_FAM = 0.50
DEFAULT_TAU_V2 = -0.02
DEFAULT_KAPPA_V2 = 0.5
DEFAULT_METRIC = 'cosine'

# Full grid
DEFAULT_GRID_STEP = 0.5  # nm
DEFAULT_GRID_MIN = 0.0
DEFAULT_GRID_MAX = 20.0

# Selection gate thresholds
GATE_SIGN_MIN = 0.25
GATE_FAM_MIN = 0.0
GATE_V1_L1_MIN = 0.0
GATE_V2_L1_MIN = -0.02

# Gen-4 v1 argmax for side-by-side reference
V1_REFERENCE = {'09': {'machado_1way': (16.5, 3.0)}}


# ============================================================================
# Cache loaders (same as v1 step2)
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
# Per-ROI per-family cache builder
# ============================================================================

def _build_roi_family_cache(loss: L3_MachadoV1V2_V2,
                             grid: np.ndarray,
                             roi: str,
                             family: str,
                             hc_W_roi: Dict[str, np.ndarray],
                             C_baseline: np.ndarray,
                             delta_rdm_obs_roi: np.ndarray
                             ) -> Dict[str, np.ndarray]:
    """Precompute (L₁, L_sign) for every Δλ in ``grid`` under ``family``.

    Returns dict with arrays of shape (n_grid,):
        l1    — cosine similarity between ΔRDM_sim and ΔRDM_obs
        l_sign — sign-match score in [-1, +1]
    """
    n = grid.size
    l1_arr = np.empty(n, dtype=float)
    lsign_arr = np.empty(n, dtype=float)
    for i, dl in enumerate(grid):
        l1, l_sign = loss._l1_and_sign_per_roi(
            float(dl), family, hc_W_roi, C_baseline,
            delta_rdm_obs_roi, roi=roi)
        l1_arr[i] = l1
        lsign_arr[i] = l_sign
    return {'l1': l1_arr, 'l_sign': lsign_arr}


# ============================================================================
# Core per-subject fine-tune
# ============================================================================

def _fine_tune_subject_v2(cvd_subj: str,
                           model: str,
                           loss: L3_MachadoV1V2_V2,
                           hc_W_dicts: Dict[str, Dict[str, np.ndarray]],
                           C_baseline: np.ndarray,
                           delta_rdm_obs_dicts: Dict[str, np.ndarray],
                           grid: np.ndarray,
                           target_family: str,
                           other_family: str) -> Dict:
    """Run full 2-D joint grid over [0, Δλ_max]² for one (subject, model)."""

    # ------------------------------------------------------------------
    # Cache: for each (ROI, family, Δλ) -> {l1, l_sign}
    # ------------------------------------------------------------------
    cache: Dict[Tuple[str, str], Dict[str, np.ndarray]] = {}
    for roi in FIT_ROIS:
        for fam in (target_family, other_family):
            cache[(roi, fam)] = _build_roi_family_cache(
                loss, grid, roi, fam,
                hc_W_dicts[roi], C_baseline,
                delta_rdm_obs_dicts[roi])

    n = grid.size

    # ------------------------------------------------------------------
    # Vectorised grid evaluation
    # ------------------------------------------------------------------
    # Per-ROI 1-D arrays across the grid
    l1_t_v1 = cache[('V1', target_family)]['l1']       # (n,)
    l1_t_v2 = cache[('V2', target_family)]['l1']       # (n,)
    l1_o_v1 = cache[('V1', other_family)]['l1']        # (n,)
    l1_o_v2 = cache[('V2', other_family)]['l1']        # (n,)
    ls_t_v1 = cache[('V1', target_family)]['l_sign']   # (n,)
    ls_t_v2 = cache[('V2', target_family)]['l_sign']   # (n,)

    # Broadcast (n_v1, n_v2) along V1 rows × V2 cols
    L1_T_V1 = l1_t_v1[:, None]                          # (n, 1)
    L1_T_V2 = l1_t_v2[None, :]                          # (1, n)
    L1_O_V1 = l1_o_v1[:, None]
    L1_O_V2 = l1_o_v2[None, :]
    LS_T_V1 = ls_t_v1[:, None]
    LS_T_V2 = ls_t_v2[None, :]

    wv1 = loss.weights['V1']
    wv2 = loss.weights['V2']

    # Joint L₁ with V2 floor penalty
    floor_t = loss.kappa_v2_floor * np.maximum(0.0,
                                                loss.tau_v2_floor - L1_T_V2)
    floor_o = loss.kappa_v2_floor * np.maximum(0.0,
                                                loss.tau_v2_floor - L1_O_V2)
    L1_joint_target = wv1 * L1_T_V1 + wv2 * L1_T_V2 - floor_t  # (n, n)
    L1_joint_other = wv1 * L1_O_V1 + wv2 * L1_O_V2 - floor_o    # (n, n)

    # L_sign joint (target only)
    L_sign_joint = 0.5 * (LS_T_V1 + LS_T_V2)

    # L_fam margin
    L_fam = L1_joint_target - L1_joint_other

    # Regularisers (2-D)
    Dv1 = grid[:, None]
    Dv2 = grid[None, :]
    L_scale = (np.maximum(0.0, np.abs(Dv1) - loss.delta_lambda_max) ** 2
               + np.maximum(0.0, np.abs(Dv2) - loss.delta_lambda_max) ** 2)
    L_roi = 0.5 * (Dv1 - Dv2) ** 2

    # L_total
    L_total = (L1_joint_target
               + loss.lam_sign * L_sign_joint
               + loss.lam_fam * L_fam
               - loss.lam_scale * L_scale
               - loss.lam_roi * L_roi)

    # Argmax
    i_best, j_best = np.unravel_index(int(np.argmax(L_total)), L_total.shape)
    best_dv1 = float(grid[i_best])
    best_dv2 = float(grid[j_best])

    best_detail = loss.compute_v2(
        delta_lambda_v1=best_dv1,
        delta_lambda_v2=best_dv2,
        target_family=target_family,
        other_family=other_family,
        hc_W_dicts=hc_W_dicts,
        C_baseline=C_baseline,
        delta_rdm_obs_dicts=delta_rdm_obs_dicts,
    )

    # Baseline at (0, 0)
    baseline_detail = loss.compute_v2(
        delta_lambda_v1=0.0,
        delta_lambda_v2=0.0,
        target_family=target_family,
        other_family=other_family,
        hc_W_dicts=hc_W_dicts,
        C_baseline=C_baseline,
        delta_rdm_obs_dicts=delta_rdm_obs_dicts,
    )

    # Gen-4 v1 reference point (if available for this subject/model)
    v1_ref_detail = None
    ref = V1_REFERENCE.get(cvd_subj, {}).get(model)
    if ref is not None:
        v1_ref_detail = loss.compute_v2(
            delta_lambda_v1=float(ref[0]),
            delta_lambda_v2=float(ref[1]),
            target_family=target_family,
            other_family=other_family,
            hc_W_dicts=hc_W_dicts,
            C_baseline=C_baseline,
            delta_rdm_obs_dicts=delta_rdm_obs_dicts,
        )

    # ------------------------------------------------------------------
    # Selection gate
    # ------------------------------------------------------------------
    gate = {
        'sign_pass': bool(best_detail['l_sign_joint'] >= GATE_SIGN_MIN),
        'fam_pass': bool(best_detail['l_fam'] > GATE_FAM_MIN),
        'v1_l1_pass': bool(best_detail['l1_V1_target'] > GATE_V1_L1_MIN),
        'v2_l1_pass': bool(best_detail['l1_V2_target'] > GATE_V2_L1_MIN),
    }
    gate['all_pass'] = all(gate[k] for k in
                            ('sign_pass', 'fam_pass',
                             'v1_l1_pass', 'v2_l1_pass'))
    gate['thresholds'] = {
        'l_sign_joint_min': GATE_SIGN_MIN,
        'l_fam_min_strict': GATE_FAM_MIN,
        'l1_V1_min': GATE_V1_L1_MIN,
        'l1_V2_min': GATE_V2_L1_MIN,
    }

    # ------------------------------------------------------------------
    # Assemble result
    # ------------------------------------------------------------------
    result = {
        'subject': cvd_subj,
        'model': model,
        'cvd_type_native': CVD_TYPE_NATIVE[cvd_subj],
        'target_family': target_family,
        'other_family': other_family,
        'rois': list(FIT_ROIS),
        'loss_params': {
            'lam_scale': loss.lam_scale,
            'lam_roi': loss.lam_roi,
            'lam_sign': loss.lam_sign,
            'lam_fam': loss.lam_fam,
            'tau_v2_floor': loss.tau_v2_floor,
            'kappa_v2_floor': loss.kappa_v2_floor,
            'delta_lambda_max': loss.delta_lambda_max,
            'metric': loss.metric,
            'weights_V1': loss.weights['V1'],
            'weights_V2': loss.weights['V2'],
        },
        'grid': {
            'min_nm': float(grid.min()),
            'max_nm': float(grid.max()),
            'step_nm': float(grid[1] - grid[0]) if grid.size > 1 else 0.0,
            'n_points': int(grid.size),
            'grid_nm': grid.tolist(),
        },
        'best': {
            'delta_v1_nm': best_dv1,
            'delta_v2_nm': best_dv2,
            **{k: float(v) for k, v in best_detail.items()
               if isinstance(v, (int, float))},
        },
        'baseline': {
            **{k: float(v) for k, v in baseline_detail.items()
               if isinstance(v, (int, float))},
        },
        'v1_reference': (
            {'delta_v1_nm': float(ref[0]), 'delta_v2_nm': float(ref[1]),
             **{k: float(v) for k, v in v1_ref_detail.items()
                if isinstance(v, (int, float))}}
            if v1_ref_detail is not None else None
        ),
        'selection_gate': gate,
        'landscape': {
            'l_total': L_total.tolist(),
            'l1_joint_target': L1_joint_target.tolist(),
            'l1_joint_other': L1_joint_other.tolist(),
            'l_sign_joint': L_sign_joint.tolist(),
            'l_fam': L_fam.tolist(),
        },
        'cache_1d': {
            'l1_target_V1': l1_t_v1.tolist(),
            'l1_target_V2': l1_t_v2.tolist(),
            'l1_other_V1': l1_o_v1.tolist(),
            'l1_other_V2': l1_o_v2.tolist(),
            'l_sign_target_V1': ls_t_v1.tolist(),
            'l_sign_target_V2': ls_t_v2.tolist(),
        },
    }
    return result


# ============================================================================
# Main
# ============================================================================

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description='Gen-4.5 Stage 2 joint V1+V2 L_total fine-tune')
    p.add_argument('--step0_dir', type=str,
                   default='results/step0_precompute')
    p.add_argument('--output_dir', type=str,
                   default='results/archive_superseded/step2_finetune_l3_v2')
    p.add_argument('--cvd_subjects', nargs='+', default=['09'])
    p.add_argument('--models', nargs='+', default=['machado_1way'])
    p.add_argument('--grid_min', type=float, default=DEFAULT_GRID_MIN)
    p.add_argument('--grid_max', type=float, default=DEFAULT_GRID_MAX)
    p.add_argument('--grid_step', type=float, default=DEFAULT_GRID_STEP)
    p.add_argument('--lam_scale', type=float, default=DEFAULT_LAM_SCALE)
    p.add_argument('--lam_roi', type=float, default=DEFAULT_LAM_ROI)
    p.add_argument('--lam_sign', type=float, default=DEFAULT_LAM_SIGN)
    p.add_argument('--lam_fam', type=float, default=DEFAULT_LAM_FAM)
    p.add_argument('--tau_v2', type=float, default=DEFAULT_TAU_V2)
    p.add_argument('--kappa_v2', type=float, default=DEFAULT_KAPPA_V2)
    p.add_argument('--metric', type=str, default=DEFAULT_METRIC,
                   choices=['cosine', 'pearson', 'spearman'])
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    step0_dir = Path(args.step0_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    print('=' * 72)
    print('Gen-4.5 Stage 2 joint V1+V2 L_total fine-tune')
    print(f'  step0_dir   : {step0_dir}')
    print(f'  output_dir  : {output_dir}')
    print(f'  ROIs fit    : {FIT_ROIS} (hV4 held out)')
    print(f'  models      : {args.models}')
    print(f'  subjects    : {args.cvd_subjects}')
    print(f'  grid        : [{args.grid_min}, {args.grid_max}] '
          f'step {args.grid_step} nm '
          f'({int(round((args.grid_max - args.grid_min) / args.grid_step)) + 1}'
          f' points × {FIT_ROIS[0]}/{FIT_ROIS[1]})')
    print(f'  λ_scale     : {args.lam_scale}')
    print(f'  λ_ROI       : {args.lam_roi}')
    print(f'  λ_sign      : {args.lam_sign}')
    print(f'  λ_fam       : {args.lam_fam}')
    print(f'  τ_V2_floor  : {args.tau_v2}')
    print(f'  κ_V2_floor  : {args.kappa_v2}')
    print(f'  metric      : {args.metric}')
    print('=' * 72)

    # Use Stockman-derived normal-vision basis as C_baseline (not nominal
    # CIELab HUE_ANGLES). This ensures ΔRDM_sim(Δλ=0) = 0 by construction
    # and removes the ~+0.30 L₁ bias from the CIELab↔Stockman coordinate
    # mismatch.  At Δλ=0, protan == deutan == normal, so family is irrelevant.
    from utils_distortion_models import get_design_matrix as _gdm
    C_baseline = _gdm('machado_1way', [0.0], cvd_type='protan')

    # Load Stage-0 caches for all fit ROIs once
    hc_W_dicts: Dict[str, Dict[str, np.ndarray]] = {}
    delta_rdm_obs_roi: Dict[str, Dict[str, np.ndarray]] = {}
    for roi in FIT_ROIS:
        hc_W_dicts[roi] = _load_hc_W(step0_dir, roi)
        delta_rdm_obs_roi[roi] = _load_delta_rdm_obs(step0_dir, roi)
        print(f'  loaded {roi}: {len(hc_W_dicts[roi])} HC, '
              f'{len(delta_rdm_obs_roi[roi])} CVD')

    grid = np.arange(args.grid_min,
                     args.grid_max + 1e-9,
                     args.grid_step)

    manifest = {
        'timestamp': datetime.now().isoformat(),
        'step0_dir': str(step0_dir),
        'grid_min_nm': args.grid_min,
        'grid_max_nm': args.grid_max,
        'grid_step_nm': args.grid_step,
        'lam_scale': args.lam_scale,
        'lam_roi': args.lam_roi,
        'lam_sign': args.lam_sign,
        'lam_fam': args.lam_fam,
        'tau_v2_floor': args.tau_v2,
        'kappa_v2_floor': args.kappa_v2,
        'metric': args.metric,
        'rois': list(FIT_ROIS),
        'models': list(args.models),
        'cvd_subjects': list(args.cvd_subjects),
        'entries': [],
    }

    for model in args.models:
        print(f'\n[model {model}]')
        loss = L3_MachadoV1V2_V2(
            lam_scale=args.lam_scale,
            lam_roi=args.lam_roi,
            lam_sign=args.lam_sign,
            lam_fam=args.lam_fam,
            tau_v2_floor=args.tau_v2,
            kappa_v2_floor=args.kappa_v2,
            delta_lambda_max=DELTA_LAMBDA_MAX,
            metric=args.metric,
            model_name=model,
        )

        for cvd_subj in args.cvd_subjects:
            drdm_dicts: Dict[str, np.ndarray] = {
                roi: delta_rdm_obs_roi[roi][cvd_subj]
                for roi in FIT_ROIS
            }

            native = CVD_TYPE_NATIVE[cvd_subj]
            if native == 'normal':
                # For sub-10 we still need a target/other pair; assign
                # deutan as target (native diagnosis), protan as other.
                target_family = 'deutan'
                other_family = 'protan'
            else:
                target_family = native
                other_family = CVD_TYPE_OTHER[native]

            print(f'  sub-{cvd_subj} ({native}) '
                  f'[target={target_family}, other={other_family}]')

            result = _fine_tune_subject_v2(
                cvd_subj=cvd_subj,
                model=model,
                loss=loss,
                hc_W_dicts=hc_W_dicts,
                C_baseline=C_baseline,
                delta_rdm_obs_dicts=drdm_dicts,
                grid=grid,
                target_family=target_family,
                other_family=other_family,
            )

            best = result['best']
            gate = result['selection_gate']
            print(f'    best: Δλ_V1={best["delta_v1_nm"]:.2f}, '
                  f'Δλ_V2={best["delta_v2_nm"]:.2f}')
            print(f'          L_total={best["l_total"]:+.4f}, '
                  f'L1_joint_T={best["l1_joint_target"]:+.4f}, '
                  f'L1_joint_O={best["l1_joint_other"]:+.4f}')
            print(f'          L_sign={best["l_sign_joint"]:+.3f}, '
                  f'L_fam={best["l_fam"]:+.4f}')
            print(f'          L1_V1={best["l1_V1_target"]:+.4f}, '
                  f'L1_V2={best["l1_V2_target"]:+.4f}')
            print(f'    gate: sign={gate["sign_pass"]} '
                  f'fam={gate["fam_pass"]} '
                  f'V1L1={gate["v1_l1_pass"]} '
                  f'V2L1={gate["v2_l1_pass"]} '
                  f'=> all_pass={gate["all_pass"]}')
            if result['v1_reference'] is not None:
                ref = result['v1_reference']
                print(f'    v1_ref@({ref["delta_v1_nm"]}, '
                      f'{ref["delta_v2_nm"]}): '
                      f'L_total={ref["l_total"]:+.4f}, '
                      f'L_sign={ref["l_sign_joint"]:+.3f}, '
                      f'L_fam={ref["l_fam"]:+.4f}')

            out_path = output_dir / f'sub-{cvd_subj}_{model}.json'
            with open(out_path, 'w') as f:
                json.dump(result, f, indent=2)
            manifest['entries'].append({
                'subject': cvd_subj,
                'model': model,
                'path': str(out_path),
                'delta_v1_nm': best['delta_v1_nm'],
                'delta_v2_nm': best['delta_v2_nm'],
                'l_total': best['l_total'],
                'l_sign_joint': best['l_sign_joint'],
                'l_fam': best['l_fam'],
                'l1_V1_target': best['l1_V1_target'],
                'l1_V2_target': best['l1_V2_target'],
                'gate_all_pass': gate['all_pass'],
            })

    manifest_path = output_dir / 'step2_v2_manifest.json'
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    print(f'\nManifest → {manifest_path}')
    print('Stage 2 v2 complete.')


if __name__ == '__main__':
    main()
