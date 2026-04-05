#!/usr/bin/env python3
"""
step3_validate_cognition.py — Gen-4 Stage 3b COGNITION validation.

Cross-checks the data-fitted Δλ (from Stage 2) against Machado's published
canonical severities to quantify how compatible the neural fit is with the
independent psychophysical simulator.

Two complementary metrics per (subject, ROI) × canonical bucket:

    1. hue_mse : mean-squared error between the fitted hue profile
                 (8,)° and the Machado-canonical hue profile (8,)°,
                 using angle-wrapped differences in [-180, 180].

    2. drdm_cos: cosine similarity between the simulated ΔRDM
                 produced by the fitted Δλ and the one produced by the
                 Machado canonical Δλ, using the Stage-0 HC W and the
                 standard 6-channel C basis. Captures whether the ΔRDM
                 shape is consistent with Machado's, independently of
                 the exact Δλ magnitude.

We compare against three canonical buckets by default:

    anomalous (5 nm) — mild
    moderate  (10 nm)
    severe    (15 nm)

plus the Machado dichromat limit (20 nm) for the severe boundary. The
closest bucket (minimum hue MSE) is recorded per ROI for the summary table.

Outputs (results/step3_cognition/):

    sub-{ID}_{model}.json
        per-ROI block containing:
          delta_lambda_used_nm,
          hue_fit_deg (8,), delta_theta_fit_deg (8,),
          comparisons: list of {canonical_nm, hue_machado_deg,
                                delta_theta_machado_deg,
                                hue_mse_deg2, drdm_cos},
          closest: {canonical_nm, hue_mse_deg2, drdm_cos}

    step3_cognition_manifest.json

Usage:
    mpirun -np 1 python scripts/step3_validate_cognition.py \
        --step0_dir results/step0_precompute \
        --step2_dir results/step2_finetune_l3 \
        --output_dir results/step3_cognition

Reused helpers:
    machado_shifted_hue                  (machado_simulator.py)
    get_design_matrix / apply_distortion (utils_distortion_models.py)
    compute_delta_rdm_sim                (diagnostic_delta_rdm.py)
    cosine_similarity                    (diagnostic_delta_rdm.py)
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

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
    apply_distortion,
    get_design_matrix,
)
from diagnostic_delta_rdm import (  # noqa: E402
    compute_delta_rdm_sim,
    cosine_similarity,
)
from machado_simulator import (  # noqa: E402
    DELTA_LAMBDA_MAX,
    machado_shifted_hue,
)

# ============================================================================
# Config
# ============================================================================

CVD_TYPE = {'08': 'deutan', '09': 'protan', '10': 'normal'}

# Machado canonical severities (nm) from the paper's anomalous trichromat
# spectrum (5 nm = mild, 10 nm = moderate, 15 nm = severe, 20 nm = dichromat)
CANONICAL_DELTA_NM = (5.0, 10.0, 15.0, 20.0)
CANONICAL_LABELS = {5.0: 'mild', 10.0: 'moderate',
                    15.0: 'severe', 20.0: 'dichromat'}

DEFAULT_MODELS = ['machado_1way', 'machado_alpha_free']
FIT_ROIS = ('V1', 'V2')
HELD_OUT_ROI = 'hV4'
ALL_ROIS = ('V1', 'V2', 'hV4')


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


def _load_stage2(step2_dir: Path, cvd_subj: str, model: str) -> Dict:
    path = step2_dir / f'sub-{cvd_subj}_{model}.json'
    if not path.exists():
        raise FileNotFoundError(f'Missing Stage-2 fit: {path}')
    with open(path) as f:
        return json.load(f)


# ============================================================================
# Hue comparison helpers
# ============================================================================

def _wrap_delta_deg(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Wrapped (signed) angular difference a-b in [-180, 180]."""
    return (np.asarray(a, dtype=float) - np.asarray(b, dtype=float)
            + 180.0) % 360.0 - 180.0


def _hue_mse_deg2(a: np.ndarray, b: np.ndarray) -> float:
    """Mean-squared error between two hue profiles in degrees²."""
    d = _wrap_delta_deg(a, b)
    return float(np.mean(d ** 2))


# ============================================================================
# Cognitive check for one (subject, model, ROI)
# ============================================================================

def _cognition_one(cvd_subj: str,
                   logical_roi: str,
                   model: str,
                   delta_lambda: float,
                   stage2_doc: Dict,
                   hc_W: Dict[str, np.ndarray],
                   C_baseline: np.ndarray,
                   canonical_grid) -> Dict:
    """Compare fitted hue/ΔRDM against Machado canonical values."""
    cvd_type = CVD_TYPE[cvd_subj]

    # Fitted hue profile (same dispatch logic as utils_distortion_models)
    # For machado_* we just pass [Δλ] (and α when 2-DOF).
    if model == 'machado_1way':
        params_fit = [float(delta_lambda)]
    elif model == 'machado_alpha_free':
        alpha = stage2_doc.get('best', {}).get('alpha')
        try:
            alpha = float(alpha) if alpha is not None else 0.75
        except Exception:  # noqa: BLE001
            alpha = 0.75
        params_fit = [float(delta_lambda), alpha]
    else:
        params_fit = [float(delta_lambda)]

    hue_baseline = np.asarray(apply_distortion(
        model, [0.0] * len(params_fit), cvd_type='normal'), dtype=float)
    hue_fit = np.asarray(apply_distortion(
        model, params_fit, cvd_type=cvd_type), dtype=float)
    dtheta_fit = _wrap_delta_deg(hue_fit, hue_baseline)

    # Fitted ΔRDM_sim from the data-fitted design matrix
    C_fit = get_design_matrix(model, params_fit, cvd_type=cvd_type)
    drdm_sim_fit, _ = compute_delta_rdm_sim(
        hc_W, C_fit, C_baseline, distance='correlation')

    # Compare against each canonical Machado severity
    comparisons: List[Dict] = []
    for canonical_nm in canonical_grid:
        # Canonical hue via the Machado-1way simulator (α coupled) —
        # this matches Machado's published interpretation regardless of
        # whether the fit used machado_1way or machado_alpha_free.
        effective_cvd = cvd_type if cvd_type != 'normal' else 'deutan'
        _, hue_mach, dtheta_mach = machado_shifted_hue(
            float(canonical_nm), effective_cvd)

        # Canonical ΔRDM_sim uses the same unified machado_1way mapping
        C_mach = get_design_matrix(
            'machado_1way', [float(canonical_nm)], cvd_type=effective_cvd)
        drdm_sim_mach, _ = compute_delta_rdm_sim(
            hc_W, C_mach, C_baseline, distance='correlation')

        hue_mse = _hue_mse_deg2(hue_fit, hue_mach)
        drdm_cos = float(cosine_similarity(drdm_sim_fit, drdm_sim_mach))

        comparisons.append({
            'canonical_delta_lambda_nm': float(canonical_nm),
            'label': CANONICAL_LABELS.get(float(canonical_nm), 'custom'),
            'hue_machado_deg': hue_mach.tolist(),
            'delta_theta_machado_deg': dtheta_mach.tolist(),
            'hue_mse_deg2': hue_mse,
            'drdm_cos': drdm_cos,
            'drdm_sim_machado_norm': float(np.linalg.norm(drdm_sim_mach)),
        })

    # Closest canonical bucket (min hue MSE)
    closest = min(comparisons, key=lambda c: c['hue_mse_deg2'])

    return {
        'roi': logical_roi,
        'model': model,
        'cvd_type': cvd_type,
        'delta_lambda_used_nm': float(delta_lambda),
        'params_fit': params_fit,
        'hue_fit_deg': hue_fit.tolist(),
        'hue_baseline_deg': hue_baseline.tolist(),
        'delta_theta_fit_deg': dtheta_fit.tolist(),
        'drdm_sim_fit_norm': float(np.linalg.norm(drdm_sim_fit)),
        'comparisons': comparisons,
        'closest': {
            'canonical_delta_lambda_nm': closest['canonical_delta_lambda_nm'],
            'label': closest['label'],
            'hue_mse_deg2': closest['hue_mse_deg2'],
            'drdm_cos': closest['drdm_cos'],
        },
    }


# ============================================================================
# Main
# ============================================================================

def _delta_for_roi(logical_roi: str, delta_v1: float, delta_v2: float) -> float:
    if logical_roi == 'V1':
        return float(delta_v1)
    if logical_roi == 'V2':
        return float(delta_v2)
    return float(0.5 * (delta_v1 + delta_v2))


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description='Gen-4 Stage 3b COGNITION validation (Machado agreement)')
    p.add_argument('--step0_dir', type=str,
                   default='results/step0_precompute')
    p.add_argument('--step2_dir', type=str,
                   default='results/step2_finetune_l3')
    p.add_argument('--output_dir', type=str,
                   default='results/step3_cognition')
    p.add_argument('--models', nargs='+', default=DEFAULT_MODELS)
    p.add_argument('--cvd_subjects', nargs='+',
                   default=list(CVD_TYPE.keys()))
    p.add_argument('--rois', nargs='+', default=list(ALL_ROIS))
    p.add_argument('--canonical_grid', type=float, nargs='+',
                   default=list(CANONICAL_DELTA_NM),
                   help='Machado canonical Δλ values (nm)')
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    step0_dir = Path(args.step0_dir).resolve()
    step2_dir = Path(args.step2_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    print('=' * 64)
    print('Gen-4 Stage 3b COGNITION validation')
    print(f'  step0_dir  : {step0_dir}')
    print(f'  step2_dir  : {step2_dir}')
    print(f'  output_dir : {output_dir}')
    print(f'  ROIs       : {args.rois}')
    print(f'  models     : {args.models}')
    print(f'  subjects   : {args.cvd_subjects}')
    print(f'  canonical  : {args.canonical_grid} nm')
    print('=' * 64)

    C_baseline = create_basis_matrix(HUE_ANGLES, N_CHANNELS)

    hc_W_per_roi: Dict[str, Dict[str, np.ndarray]] = {}
    for roi in args.rois:
        hc_W_per_roi[roi] = _load_hc_W(step0_dir, roi)

    manifest = {
        'timestamp': datetime.now().isoformat(),
        'step0_dir': str(step0_dir),
        'step2_dir': str(step2_dir),
        'rois': list(args.rois),
        'models': list(args.models),
        'cvd_subjects': list(args.cvd_subjects),
        'canonical_grid_nm': [float(x) for x in args.canonical_grid],
        'delta_lambda_max': DELTA_LAMBDA_MAX,
        'entries': [],
    }

    for model in args.models:
        print(f'\n[model {model}]')
        for cvd_subj in args.cvd_subjects:
            stage2 = _load_stage2(step2_dir, cvd_subj, model)
            delta_v1 = float(stage2['best']['delta_v1_nm'])
            delta_v2 = float(stage2['best']['delta_v2_nm'])
            print(f'  sub-{cvd_subj} ({CVD_TYPE[cvd_subj]}): '
                  f'Δλ_V1={delta_v1:.2f}, Δλ_V2={delta_v2:.2f}')

            subject_entry = {
                'subject': cvd_subj,
                'cvd_type': CVD_TYPE[cvd_subj],
                'model': model,
                'delta_v1_nm': delta_v1,
                'delta_v2_nm': delta_v2,
                'delta_bar_nm': float(0.5 * (delta_v1 + delta_v2)),
                'rois': {},
            }

            for roi in args.rois:
                dl = _delta_for_roi(roi, delta_v1, delta_v2)
                hc_W = hc_W_per_roi[roi]
                out = _cognition_one(
                    cvd_subj=cvd_subj,
                    logical_roi=roi,
                    model=model,
                    delta_lambda=dl,
                    stage2_doc=stage2,
                    hc_W=hc_W,
                    C_baseline=C_baseline,
                    canonical_grid=args.canonical_grid,
                )
                subject_entry['rois'][roi] = out
                closest = out['closest']
                print(f'    {roi:4s}  Δλ={dl:5.2f}  '
                      f'closest={closest["label"]:9s} '
                      f'({closest["canonical_delta_lambda_nm"]:.1f} nm)  '
                      f'hue_mse={closest["hue_mse_deg2"]:.2f}°²  '
                      f'drdm_cos={closest["drdm_cos"]:+.3f}')

            out_path = output_dir / f'sub-{cvd_subj}_{model}.json'
            with open(out_path, 'w') as f:
                json.dump(subject_entry, f, indent=2)
            manifest['entries'].append({
                'subject': cvd_subj,
                'model': model,
                'path': str(out_path),
                'delta_v1_nm': delta_v1,
                'delta_v2_nm': delta_v2,
                'delta_bar_nm': subject_entry['delta_bar_nm'],
                'hV4_closest_nm': subject_entry['rois'].get(
                    HELD_OUT_ROI, {}).get('closest', {}).get(
                        'canonical_delta_lambda_nm'),
                'hV4_hue_mse_deg2': subject_entry['rois'].get(
                    HELD_OUT_ROI, {}).get('closest', {}).get('hue_mse_deg2'),
                'hV4_drdm_cos': subject_entry['rois'].get(
                    HELD_OUT_ROI, {}).get('closest', {}).get('drdm_cos'),
            })

    manifest_path = output_dir / 'step3_cognition_manifest.json'
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    print(f'\nManifest → {manifest_path}')
    print('Stage 3b COGNITION complete.')


if __name__ == '__main__':
    main()
