#!/usr/bin/env python3
"""
step2_finetune_l3.py — Gen-4 Stage 2 joint V1+V2 L₃ fine-tune.

Reads the coarse anchors produced by Stage 1 and runs a narrow joint 2-D
grid around them, maximising the L₃ loss:

    L₃(Δλ_V1, Δλ_V2) = 0.5·L₁_V1 + 0.5·L₁_V2
                      − λ_scale · L_scale(Δλ_V1, Δλ_V2)
                      − λ_ROI   · L_ROI(Δλ_V1, Δλ_V2)

with defaults λ_scale = 0.01, λ_ROI = 0.005, Δλ_max = 20 nm.

After finding the argmax we:
    • compute L₃ at the Δλ=0 baseline for the improvement test,
    • run an exact 8! joint V1+V2 permutation of ΔRDM_obs labels
      via L3_MachadoV1V2.permutation_null → label_perm_p,
      baseline_improvement_p.

Stage 2 is intentionally restricted to the Machado models
(machado_1way primary, machado_alpha_free candidate). Legacy models
(cone_3way / fourier / per_color) stay in Stage 1 for ablation only
because their 3+-D search spaces are incompatible with the narrow
±Δ joint L₃ box and they failed in Gen-3.

Outputs (results/step2_finetune_l3/):

    sub-{ID}_{model}.json
        best_delta_v1 / best_delta_v2, their anchors & drifts,
        l3, l1, l1_V1, l1_V2, l_scale, l_roi, reg_penalty,
        baseline_l3, label_perm_p, baseline_improvement_p,
        2-D l3 landscape, and the Δλ=0 baseline landscape.

    step2_manifest.json

Usage:
    mpirun -np 1 python scripts/step2_finetune_l3.py \
        --step0_dir results/step0_precompute \
        --step1_dir results/step1_machado_anchor \
        --output_dir results/step2_finetune_l3 \
        --models machado_1way machado_alpha_free

Reused helpers:
    L3_MachadoV1V2               (l3_loss.py)
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

from utils_forward_model import HUE_ANGLES, N_CHANNELS, create_basis_matrix  # noqa: E402
from l3_loss import L3_MachadoV1V2  # noqa: E402
from machado_simulator import DELTA_LAMBDA_MAX  # noqa: E402

# ============================================================================
# Config
# ============================================================================

CVD_TYPE = {'08': 'deutan', '09': 'protan', '10': 'normal'}

DEFAULT_MODELS = ['machado_1way', 'machado_alpha_free']
FIT_ROIS = ('V1', 'V2')   # held-out ROI is hV4 — not used in L₃

# Narrow joint box and step (plan §4 Stage 2)
WINDOW_HALF_WIDTH_NM = 3.0
WINDOW_STEP_NM = 0.1

# Loss hyperparameters (plan §3-1)
DEFAULT_LAM_SCALE = 0.01
DEFAULT_LAM_ROI = 0.005
DEFAULT_METRIC = 'cosine'


# ============================================================================
# Cache loaders
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


def _load_stage1_anchor(step1_dir: Path,
                        cvd_subj: str,
                        logical_roi: str,
                        model: str) -> Dict:
    path = step1_dir / f'sub-{cvd_subj}_{logical_roi}_{model}.json'
    if not path.exists():
        raise FileNotFoundError(f'Missing Stage-1 anchor: {path}')
    with open(path) as f:
        return json.load(f)


# ============================================================================
# Joint 2-D grid construction
# ============================================================================

def _narrow_grid(center: float,
                 half: float = WINDOW_HALF_WIDTH_NM,
                 step: float = WINDOW_STEP_NM,
                 dl_max: float = DELTA_LAMBDA_MAX) -> np.ndarray:
    """1-D narrow Δλ grid around ``center`` clamped to [0, Δλ_max]."""
    lo = max(0.0, float(center) - half)
    hi = min(float(dl_max), float(center) + half)
    n = int(round((hi - lo) / step)) + 1
    if n < 2:
        return np.array([lo], dtype=float)
    return np.linspace(lo, hi, n)


# ============================================================================
# Core per-subject fine-tune
# ============================================================================

def _fine_tune_subject(cvd_subj: str,
                       model: str,
                       loss: L3_MachadoV1V2,
                       hc_W_dicts: Dict[str, Dict[str, np.ndarray]],
                       C_baseline: np.ndarray,
                       delta_rdm_obs_dicts: Dict[str, np.ndarray],
                       anchor_v1: float,
                       anchor_v2: float,
                       half: float,
                       step: float,
                       cvd_type_override: str = None) -> Dict:
    """Run the narrow joint L₃ grid for one (subject, model).

    If ``cvd_type_override`` is supplied it bypasses the native
    ``CVD_TYPE[cvd_subj]`` mapping — used by the cross-family specificity
    sweep.
    """
    cvd_type_native = CVD_TYPE[cvd_subj]
    cvd_type = cvd_type_override if cvd_type_override else cvd_type_native
    grid_v1 = _narrow_grid(anchor_v1, half=half, step=step)
    grid_v2 = _narrow_grid(anchor_v2, half=half, step=step)

    # L3 landscape
    n1, n2 = grid_v1.size, grid_v2.size
    l3_grid = np.full((n1, n2), -np.inf, dtype=float)
    l1_grid = np.full((n1, n2), -np.inf, dtype=float)
    l1_v1_grid = np.full((n1, n2), -np.inf, dtype=float)
    l1_v2_grid = np.full((n1, n2), -np.inf, dtype=float)

    best = {'l3': -np.inf}
    for i, dv1 in enumerate(grid_v1):
        for j, dv2 in enumerate(grid_v2):
            out = loss.compute(
                delta_lambda_v1=float(dv1),
                delta_lambda_v2=float(dv2),
                cvd_type=cvd_type,
                hc_W_dicts=hc_W_dicts,
                C_baseline=C_baseline,
                delta_rdm_obs_dicts=delta_rdm_obs_dicts,
            )
            l3_grid[i, j] = out['l3']
            l1_grid[i, j] = out['l1']
            l1_v1_grid[i, j] = out['l1_V1']
            l1_v2_grid[i, j] = out['l1_V2']
            if out['l3'] > best['l3']:
                best = out

    best_dv1 = float(best['delta_v1'])
    best_dv2 = float(best['delta_v2'])

    # Baseline L₃ at Δλ=0 for the improvement null
    baseline_out = loss.compute(
        delta_lambda_v1=0.0,
        delta_lambda_v2=0.0,
        cvd_type=cvd_type,
        hc_W_dicts=hc_W_dicts,
        C_baseline=C_baseline,
        delta_rdm_obs_dicts=delta_rdm_obs_dicts,
    )

    # Exact 8! joint V1+V2 permutation null
    print(f'    Running 8! joint V1+V2 permutation null (40320)...')
    null = loss.permutation_null(
        best_delta_v1=best_dv1,
        best_delta_v2=best_dv2,
        cvd_type=cvd_type,
        hc_W_dicts=hc_W_dicts,
        C_baseline=C_baseline,
        delta_rdm_obs_dicts=delta_rdm_obs_dicts,
        baseline_l3=baseline_out['l3'],
    )

    result = {
        'subject': cvd_subj,
        'cvd_type': cvd_type,
        'cvd_type_native': cvd_type_native,
        'cvd_type_override': cvd_type_override,
        'model': model,
        'rois': list(FIT_ROIS),
        'loss': {
            'lam_scale': loss.lam_scale,
            'lam_roi': loss.lam_roi,
            'delta_lambda_max': loss.delta_lambda_max,
            'metric': loss.metric,
        },
        'grid': {
            'half_width_nm': half,
            'step_nm': step,
            'grid_v1_nm': grid_v1.tolist(),
            'grid_v2_nm': grid_v2.tolist(),
            'l3_grid': l3_grid.tolist(),
            'l1_grid': l1_grid.tolist(),
            'l1_V1_grid': l1_v1_grid.tolist(),
            'l1_V2_grid': l1_v2_grid.tolist(),
        },
        'anchor': {
            'delta_v1_nm': float(anchor_v1),
            'delta_v2_nm': float(anchor_v2),
        },
        'best': {
            'delta_v1_nm': best_dv1,
            'delta_v2_nm': best_dv2,
            'delta_bar_nm': float(best['delta_bar']),
            'l3': float(best['l3']),
            'l1': float(best['l1']),
            'l1_V1': float(best['l1_V1']),
            'l1_V2': float(best['l1_V2']),
            'l_scale': float(best['l_scale']),
            'l_roi': float(best['l_roi']),
        },
        'drift': {
            'drift_v1_nm': float(abs(best_dv1 - float(anchor_v1))),
            'drift_v2_nm': float(abs(best_dv2 - float(anchor_v2))),
        },
        'baseline': {
            'delta_v1_nm': 0.0,
            'delta_v2_nm': 0.0,
            'l3': float(baseline_out['l3']),
            'l1': float(baseline_out['l1']),
            'l1_V1': float(baseline_out['l1_V1']),
            'l1_V2': float(baseline_out['l1_V2']),
        },
        'permutation_null': {
            'observed_l3': float(null['observed_l3']),
            'observed_l1': float(null['observed_l1']),
            'observed_l1_V1': float(null['observed_l1_V1']),
            'observed_l1_V2': float(null['observed_l1_V2']),
            'reg_penalty': float(null['reg_penalty']),
            'l_scale_const': float(null['l_scale_const']),
            'l_roi_const': float(null['l_roi_const']),
            'null_l3_mean': float(null['null_l3_mean']),
            'null_l3_std': float(null['null_l3_std']),
            'null_l3_size': int(null['null_l3_size']),
            'label_perm_p': float(null['label_perm_p']),
            'baseline_l3': float(null.get('baseline_l3', baseline_out['l3'])),
            'observed_improvement': float(
                null.get('observed_improvement',
                         best['l3'] - baseline_out['l3'])),
            'baseline_improvement_p': float(
                null.get('baseline_improvement_p', np.nan)),
        },
    }
    return result


# ============================================================================
# Main
# ============================================================================

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description='Gen-4 Stage 2 joint V1+V2 L3 fine-tune')
    p.add_argument('--step0_dir', type=str,
                   default='results/step0_precompute')
    p.add_argument('--step1_dir', type=str,
                   default='results/step1_machado_anchor')
    p.add_argument('--output_dir', type=str,
                   default='results/step2_finetune_l3')
    p.add_argument('--models', nargs='+', default=DEFAULT_MODELS,
                   help='Machado models only (legacy stays in Stage 1)')
    p.add_argument('--cvd_subjects', nargs='+',
                   default=list(CVD_TYPE.keys()))
    p.add_argument('--cvd_type_override', type=str, default=None,
                   choices=['protan', 'deutan', 'normal'],
                   help='Force a cvd_type for ALL --cvd_subjects (cross-'
                        'family specificity test). Default: use native '
                        'CVD_TYPE mapping.')
    p.add_argument('--half_width_nm', type=float,
                   default=WINDOW_HALF_WIDTH_NM)
    p.add_argument('--step_nm', type=float, default=WINDOW_STEP_NM)
    p.add_argument('--lam_scale', type=float, default=DEFAULT_LAM_SCALE)
    p.add_argument('--lam_roi', type=float, default=DEFAULT_LAM_ROI)
    p.add_argument('--metric', type=str, default=DEFAULT_METRIC,
                   choices=['cosine', 'pearson', 'spearman'])
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    step0_dir = Path(args.step0_dir).resolve()
    step1_dir = Path(args.step1_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    print('=' * 64)
    print('Gen-4 Stage 2 joint V1+V2 L3 fine-tune')
    print(f'  step0_dir  : {step0_dir}')
    print(f'  step1_dir  : {step1_dir}')
    print(f'  output_dir : {output_dir}')
    print(f'  ROIs fit   : {FIT_ROIS} (hV4 held out)')
    print(f'  models     : {args.models}')
    print(f'  subjects   : {args.cvd_subjects}')
    if args.cvd_type_override:
        print(f'  ⚠ cvd_type_override: {args.cvd_type_override} '
              f'(cross-family specificity mode)')
    print(f'  window     : ±{args.half_width_nm} nm, step {args.step_nm} nm')
    print(f'  λ_scale    : {args.lam_scale}')
    print(f'  λ_ROI      : {args.lam_roi}')
    print(f'  metric     : {args.metric}')
    print('=' * 64)

    C_baseline = create_basis_matrix(HUE_ANGLES, N_CHANNELS)

    # Load Stage-0 caches for all fit ROIs once
    hc_W_dicts: Dict[str, Dict[str, np.ndarray]] = {}
    delta_rdm_obs_roi: Dict[str, Dict[str, np.ndarray]] = {}
    for roi in FIT_ROIS:
        hc_W_dicts[roi] = _load_hc_W(step0_dir, roi)
        delta_rdm_obs_roi[roi] = _load_delta_rdm_obs(step0_dir, roi)
        print(f'  loaded {roi}: {len(hc_W_dicts[roi])} HC, '
              f'{len(delta_rdm_obs_roi[roi])} CVD')

    manifest = {
        'timestamp': datetime.now().isoformat(),
        'step0_dir': str(step0_dir),
        'step1_dir': str(step1_dir),
        'lam_scale': args.lam_scale,
        'lam_roi': args.lam_roi,
        'delta_lambda_max': DELTA_LAMBDA_MAX,
        'metric': args.metric,
        'half_width_nm': args.half_width_nm,
        'step_nm': args.step_nm,
        'rois': list(FIT_ROIS),
        'models': list(args.models),
        'cvd_subjects': list(args.cvd_subjects),
        'cvd_type_override': args.cvd_type_override,
        'entries': [],
    }

    for model in args.models:
        print(f'\n[model {model}]')
        loss = L3_MachadoV1V2(
            lam_scale=args.lam_scale,
            lam_roi=args.lam_roi,
            delta_lambda_max=DELTA_LAMBDA_MAX,
            metric=args.metric,
            model_name=model,
        )

        for cvd_subj in args.cvd_subjects:
            # Per-CVD ΔRDM_obs dict keyed by ROI
            drdm_dicts: Dict[str, np.ndarray] = {
                roi: delta_rdm_obs_roi[roi][cvd_subj]
                for roi in FIT_ROIS
            }

            # Pull anchor Δλ per ROI
            anchor_v1_doc = _load_stage1_anchor(
                step1_dir, cvd_subj, 'V1', model)
            anchor_v2_doc = _load_stage1_anchor(
                step1_dir, cvd_subj, 'V2', model)
            # best.params[0] == Δλ for both machado_1way and machado_alpha_free
            anchor_v1 = float(anchor_v1_doc['best']['params'][0])
            anchor_v2 = float(anchor_v2_doc['best']['params'][0])

            # For machado_alpha_free: freeze per-ROI α at the Stage-1 anchor
            # so the Stage-2 joint grid stays 2-D over Δλ only.
            if model == 'machado_alpha_free':
                alpha_v1 = float(anchor_v1_doc['best'].get('alpha', 1.0))
                alpha_v2 = float(anchor_v2_doc['best'].get('alpha', 1.0))
                loss.set_fixed_alphas({'V1': alpha_v1, 'V2': alpha_v2})
            else:
                loss.set_fixed_alphas({})

            effective_cvd_type = (
                args.cvd_type_override
                if args.cvd_type_override else CVD_TYPE[cvd_subj])
            family_tag = effective_cvd_type
            if args.cvd_type_override:
                family_tag = (f'{effective_cvd_type} [override, '
                              f'native={CVD_TYPE[cvd_subj]}]')
            if model == 'machado_alpha_free':
                print(f'  sub-{cvd_subj} ({family_tag}): '
                      f'anchors V1={anchor_v1:.2f} nm (α={alpha_v1:.2f}), '
                      f'V2={anchor_v2:.2f} nm (α={alpha_v2:.2f})')
            else:
                print(f'  sub-{cvd_subj} ({family_tag}): '
                      f'anchors V1={anchor_v1:.2f} nm, V2={anchor_v2:.2f} nm')

            result = _fine_tune_subject(
                cvd_subj=cvd_subj,
                model=model,
                loss=loss,
                hc_W_dicts=hc_W_dicts,
                C_baseline=C_baseline,
                delta_rdm_obs_dicts=drdm_dicts,
                anchor_v1=anchor_v1,
                anchor_v2=anchor_v2,
                half=args.half_width_nm,
                step=args.step_nm,
                cvd_type_override=args.cvd_type_override,
            )

            best = result['best']
            null = result['permutation_null']
            print(f'    best: Δλ_V1={best["delta_v1_nm"]:.2f}, '
                  f'Δλ_V2={best["delta_v2_nm"]:.2f}, '
                  f'L3={best["l3"]:+.4f}, L1={best["l1"]:+.4f}, '
                  f'label_p={null["label_perm_p"]:.4f}, '
                  f'improv_p={null["baseline_improvement_p"]:.4f}')

            out_path = output_dir / f'sub-{cvd_subj}_{model}.json'
            with open(out_path, 'w') as f:
                json.dump(result, f, indent=2)
            manifest['entries'].append({
                'subject': cvd_subj,
                'model': model,
                'path': str(out_path),
                'delta_v1_nm': best['delta_v1_nm'],
                'delta_v2_nm': best['delta_v2_nm'],
                'l3': best['l3'],
                'label_perm_p': null['label_perm_p'],
                'baseline_improvement_p': null['baseline_improvement_p'],
                'drift_v1_nm': result['drift']['drift_v1_nm'],
                'drift_v2_nm': result['drift']['drift_v2_nm'],
            })

    manifest_path = output_dir / 'step2_manifest.json'
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    print(f'\nManifest → {manifest_path}')
    print('Stage 2 complete.')


if __name__ == '__main__':
    main()
