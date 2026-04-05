#!/usr/bin/env python3
"""
step1_machado_anchor.py — Gen-4 Stage 1 coarse Machado anchor.

Explicit grid search (no Differential Evolution — Gen-3 failure mode) over
Δλ ∈ [0, Δλ_max] using the ΔRDM similarity L₁ as the fitness.

For each (CVD subject, ROI ∈ {V1, V2}, model) triple:

    machado_1way       : Δλ grid of 41 points at 0.5 nm steps
    machado_alpha_free : outer α grid × inner Δλ grid = 21 × 41 = 861 points
    cone_3way (ablat.) : 3-D Stockman grid — reused legacy bounds, 11^3 pts

At every grid point we
    1) build C(θ+δ) via apply_distortion / get_design_matrix,
    2) compute ΔRDM_sim = RDM(C(θ+δ)@W_HC) − RDM(C(θ)@W_HC) per HC,
    3) average ΔRDM_sim across HC,
    4) score L₁ = cosine_similarity(ΔRDM_sim, ΔRDM_obs).

The argmax over the grid is recorded as the (subject, ROI, model) anchor,
which feeds Stage 2's narrow ±3 nm joint L₃ fine-tune.

Outputs (results/step1_machado_anchor/):

    sub-{ID}_{ROI}_{model}.json   per-triple anchor
      - best: {delta_lambda_nm, alpha, params, L1, hue_shifted_deg (8,),
               delta_theta_deg (8,)}
      - sweep: list of per-grid-point {params, L1, delta_rdm_sim_norm}
      - baseline_L1: L₁ at Δλ=0 (for improvement reference)
    step1_manifest.json           one row per (ROI, subj, model)

Usage:
    mpirun -np 1 python scripts/step1_machado_anchor.py \
        --step0_dir results/step0_precompute \
        --output_dir results/step1_machado_anchor

Reused helpers:
    apply_distortion / get_design_matrix  (utils_distortion_models.py)
    compute_delta_rdm_sim                 (diagnostic_delta_rdm.py)
    cosine_similarity                     (diagnostic_delta_rdm.py)
    create_basis_matrix                   (future_phase1_forward_model)
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

_FWD_DIR = str(Path(__file__).resolve().parent.parent.parent.parent
               / 'future_phase1_forward_model' / 'scripts')
if _FWD_DIR not in sys.path:
    sys.path.insert(0, _FWD_DIR)

from utils_forward_model import (  # noqa: E402
    HUE_ANGLES,
    N_CHANNELS,
    create_basis_matrix,
)
from utils_distortion_models import (  # noqa: E402
    MODELS,
    apply_distortion,
    get_design_matrix,
)
from diagnostic_delta_rdm import (  # noqa: E402
    compute_delta_rdm_sim,
    cosine_similarity,
)
from machado_simulator import DELTA_LAMBDA_MAX, machado_shifted_hue  # noqa: E402

# ============================================================================
# Config
# ============================================================================

CVD_TYPE = {'08': 'deutan', '09': 'protan', '10': 'normal'}

DEFAULT_MODELS = ['machado_1way', 'machado_alpha_free', 'cone_3way']
DEFAULT_ROIS = ('V1', 'V2')  # V1+V2 fit the loss; hV4 is held out

# Grid step controls
DELTA_STEP_NM_DEFAULT = 0.5   # machado_1way / machado_alpha_free
ALPHA_STEP_DEFAULT = 0.05     # machado_alpha_free outer loop
CONE_3WAY_STEP_NM = 6.0       # coarse 3-D sweep (legacy ablation only)
CONE_3WAY_RANGE = (-30.0, 30.0)


# ============================================================================
# Grid enumeration
# ============================================================================

def _delta_grid(step: float = DELTA_STEP_NM_DEFAULT,
                dl_max: float = DELTA_LAMBDA_MAX) -> np.ndarray:
    """1-D Δλ grid in [0, Δλ_max] (inclusive)."""
    n = int(round(dl_max / step)) + 1
    return np.linspace(0.0, dl_max, n)


def _alpha_grid(step: float = ALPHA_STEP_DEFAULT) -> np.ndarray:
    """1-D α grid in [0, 1] (inclusive)."""
    n = int(round(1.0 / step)) + 1
    return np.linspace(0.0, 1.0, n)


def _cone3_grid(step: float = CONE_3WAY_STEP_NM,
                rng: Tuple[float, float] = CONE_3WAY_RANGE) -> np.ndarray:
    """1-D axis for cone_3way's Stockman L, M, S shifts."""
    lo, hi = rng
    n = int(round((hi - lo) / step)) + 1
    return np.linspace(lo, hi, n)


def _enumerate_model_grid(model: str,
                          delta_step: float,
                          alpha_step: float) -> List[Tuple[List[float], Dict]]:
    """Return a list of (params, meta) tuples to evaluate for the given model.

    ``meta`` carries per-point annotations we want to store in the sweep log.
    """
    points: List[Tuple[List[float], Dict]] = []

    if model == 'machado_1way':
        for dl in _delta_grid(delta_step):
            points.append(([float(dl)],
                           {'delta_lambda_nm': float(dl)}))
        return points

    if model == 'machado_alpha_free':
        for alpha in _alpha_grid(alpha_step):
            for dl in _delta_grid(delta_step):
                points.append(([float(dl), float(alpha)],
                               {'delta_lambda_nm': float(dl),
                                'alpha': float(alpha)}))
        return points

    if model == 'cone_3way':
        axis = _cone3_grid()
        for dL in axis:
            for dM in axis:
                for dS in axis:
                    points.append(
                        ([float(dL), float(dM), float(dS)],
                         {'delta_L_nm': float(dL),
                          'delta_M_nm': float(dM),
                          'delta_S_nm': float(dS)}))
        return points

    raise ValueError(f'Unknown model for Stage 1: {model}')


# ============================================================================
# Stage-0 cache loaders
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
# Per-triple fitting
# ============================================================================

def _score_params(model: str,
                  params: List[float],
                  cvd_type: str,
                  hc_W: Dict[str, np.ndarray],
                  C_baseline: np.ndarray,
                  delta_rdm_obs: np.ndarray) -> Tuple[float, float]:
    """Compute (L1 cosine, ||ΔRDM_sim||) at a single grid point."""
    C_shifted = get_design_matrix(model, params, cvd_type=cvd_type)
    delta_sim, _ = compute_delta_rdm_sim(
        hc_W, C_shifted, C_baseline, distance='correlation')
    l1 = float(cosine_similarity(delta_sim, delta_rdm_obs))
    norm = float(np.linalg.norm(delta_sim))
    return l1, norm


def _fit_triple(cvd_subj: str,
                logical_roi: str,
                model: str,
                hc_W: Dict[str, np.ndarray],
                C_baseline: np.ndarray,
                delta_rdm_obs: np.ndarray,
                delta_step: float,
                alpha_step: float) -> Dict:
    """Grid-search a single (subject, ROI, model) triple."""
    cvd_type = CVD_TYPE[cvd_subj]

    grid = _enumerate_model_grid(model, delta_step, alpha_step)
    sweep: List[Dict] = []
    best_l1 = -np.inf
    best_entry: Dict = {}
    best_params: List[float] = list(grid[0][0])

    for params, meta in grid:
        l1, norm = _score_params(
            model, params, cvd_type, hc_W, C_baseline, delta_rdm_obs)
        entry = {
            'params': list(map(float, params)),
            **meta,
            'l1': l1,
            'delta_rdm_sim_norm': norm,
        }
        sweep.append(entry)
        if l1 > best_l1:
            best_l1 = l1
            best_entry = entry
            best_params = list(params)

    # Baseline Δλ=0 reference (all zeros across all models)
    zero_params = [0.0] * MODELS[model]['df']
    baseline_l1, baseline_norm = _score_params(
        model, zero_params, cvd_type, hc_W, C_baseline, delta_rdm_obs)

    # Cognitive annotation — report the Machado/Stockman hue profile at best
    try:
        hue_shifted = apply_distortion(
            model, best_params, cvd_type=cvd_type)
        hue_shifted = np.asarray(hue_shifted, dtype=float)
    except Exception:  # noqa: BLE001 — fallback if model can't apply
        hue_shifted = None

    delta_theta_deg = None
    if hue_shifted is not None:
        hue_baseline = apply_distortion(
            model, zero_params, cvd_type='normal')
        hue_baseline = np.asarray(hue_baseline, dtype=float)
        dtheta = (hue_shifted - hue_baseline + 180.0) % 360.0 - 180.0
        delta_theta_deg = dtheta.tolist()

    # For Machado-family models, also emit the canonical Machado hue for the
    # fitted Δλ so Stage 3b can reuse it directly without re-running the grid.
    machado_hue = None
    if model in ('machado_1way', 'machado_alpha_free'):
        dl = float(best_params[0])
        alpha = float(best_params[1]) if len(best_params) > 1 else None
        _, hue_s, dtheta_m = machado_shifted_hue(
            dl, cvd_type if cvd_type != 'normal' else 'deutan',
            alpha=alpha)
        machado_hue = {
            'delta_lambda_nm': dl,
            'alpha': alpha,
            'hue_shifted_deg': hue_s.tolist(),
            'delta_theta_deg': dtheta_m.tolist(),
        }

    result = {
        'subject': cvd_subj,
        'cvd_type': cvd_type,
        'roi': logical_roi,
        'model': model,
        'df': MODELS[model]['df'],
        'bounds': MODELS[model]['bounds'],
        'grid_size': len(grid),
        'delta_step_nm': delta_step if model in (
            'machado_1way', 'machado_alpha_free') else None,
        'alpha_step': alpha_step if model == 'machado_alpha_free' else None,
        'cone3way_step_nm': CONE_3WAY_STEP_NM if model == 'cone_3way' else None,
        'baseline_l1': baseline_l1,
        'baseline_delta_rdm_sim_norm': baseline_norm,
        'best': {
            **best_entry,
            'params': list(map(float, best_params)),
            'hue_shifted_deg': hue_shifted.tolist() if hue_shifted is not None else None,
            'delta_theta_deg': delta_theta_deg,
        },
        'improvement_over_baseline': float(best_l1 - baseline_l1),
        'machado_hue': machado_hue,
        'sweep': sweep,
    }
    return result


# ============================================================================
# Main
# ============================================================================

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description='Gen-4 Stage 1 Machado coarse grid anchor')
    p.add_argument('--step0_dir', type=str,
                   default='results/step0_precompute')
    p.add_argument('--output_dir', type=str,
                   default='results/step1_machado_anchor')
    p.add_argument('--rois', nargs='+', default=list(DEFAULT_ROIS),
                   help='Logical ROI names (V1 V2 — hV4 held out)')
    p.add_argument('--models', nargs='+', default=DEFAULT_MODELS,
                   help='Distortion models to sweep '
                        '(machado_1way machado_alpha_free cone_3way)')
    p.add_argument('--cvd_subjects', nargs='+',
                   default=list(CVD_TYPE.keys()))
    p.add_argument('--delta_step_nm', type=float,
                   default=DELTA_STEP_NM_DEFAULT)
    p.add_argument('--alpha_step', type=float, default=ALPHA_STEP_DEFAULT)
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    step0_dir = Path(args.step0_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    print('=' * 64)
    print('Gen-4 Stage 1 Machado coarse anchor')
    print(f'  step0_dir : {step0_dir}')
    print(f'  output_dir: {output_dir}')
    print(f'  ROIs      : {args.rois}')
    print(f'  models    : {args.models}')
    print(f'  subjects  : {args.cvd_subjects}')
    print(f'  Δλ step   : {args.delta_step_nm} nm '
          f'(range [0, {DELTA_LAMBDA_MAX}] nm)')
    print(f'  α step    : {args.alpha_step}')
    print('=' * 64)

    C_baseline = create_basis_matrix(HUE_ANGLES, N_CHANNELS)

    manifest = {
        'timestamp': datetime.now().isoformat(),
        'step0_dir': str(step0_dir),
        'delta_lambda_max': DELTA_LAMBDA_MAX,
        'delta_step_nm': args.delta_step_nm,
        'alpha_step': args.alpha_step,
        'rois': list(args.rois),
        'models': list(args.models),
        'cvd_subjects': list(args.cvd_subjects),
        'entries': [],
    }

    for logical_roi in args.rois:
        print(f'\n[ROI {logical_roi}]')
        hc_W = _load_hc_W(step0_dir, logical_roi)
        delta_rdm_obs_map = _load_delta_rdm_obs(step0_dir, logical_roi)

        for cvd_subj in args.cvd_subjects:
            if cvd_subj not in delta_rdm_obs_map:
                print(f'  sub-{cvd_subj}: no ΔRDM_obs cached, skipping')
                continue
            delta_rdm_obs = delta_rdm_obs_map[cvd_subj]

            for model in args.models:
                print(f'  sub-{cvd_subj} × {model}')
                result = _fit_triple(
                    cvd_subj=cvd_subj,
                    logical_roi=logical_roi,
                    model=model,
                    hc_W=hc_W,
                    C_baseline=C_baseline,
                    delta_rdm_obs=delta_rdm_obs,
                    delta_step=args.delta_step_nm,
                    alpha_step=args.alpha_step,
                )

                # One-line summary
                best = result['best']
                if model == 'machado_1way':
                    tag = f'Δλ={best["delta_lambda_nm"]:5.2f} nm'
                elif model == 'machado_alpha_free':
                    tag = (f'Δλ={best["delta_lambda_nm"]:5.2f} nm, '
                           f'α={best["alpha"]:.2f}')
                elif model == 'cone_3way':
                    tag = (f'L={best["delta_L_nm"]:+.1f} '
                           f'M={best["delta_M_nm"]:+.1f} '
                           f'S={best["delta_S_nm"]:+.1f} nm')
                else:
                    tag = str(best['params'])
                print(f'    grid={result["grid_size"]:5d}  '
                      f'L1={best["l1"]:+.4f}  '
                      f'baseline_L1={result["baseline_l1"]:+.4f}  '
                      f'Δ={result["improvement_over_baseline"]:+.4f}  '
                      f'{tag}')

                out_path = output_dir / f'sub-{cvd_subj}_{logical_roi}_{model}.json'
                with open(out_path, 'w') as f:
                    json.dump(result, f, indent=2)
                manifest['entries'].append({
                    'subject': cvd_subj,
                    'roi': logical_roi,
                    'model': model,
                    'path': str(out_path),
                    'best_l1': float(best['l1']),
                    'best_params': list(map(float, best['params'])),
                    'baseline_l1': float(result['baseline_l1']),
                    'improvement_over_baseline':
                        float(result['improvement_over_baseline']),
                })

    manifest_path = output_dir / 'step1_manifest.json'
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    print(f'\nManifest → {manifest_path}')
    print('Stage 1 complete.')


if __name__ == '__main__':
    main()
