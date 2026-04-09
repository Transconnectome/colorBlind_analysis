#!/usr/bin/env python3
"""
step3_validate_neural.py — Gen-4 Stage 3a NEURAL validation on held-out hV4.

The Stage-2 L₃ fit only uses V1+V2 ΔRDM. hV4 is completely held out so its
LOCO-vulnerability prediction is the honest transfer test.

For each (CVD subject, model) we use the fitted Δλ from Stage 2 to generate
C(θ+δ) on the 8 stimuli, then predict mean-HC vulnerability via the W-fixed
approach (same function used by step1_fit_loco_v2.py). We compare the
simulated vulnerability profile against the CVD's observed LOCO vulnerability
via Spearman ρ and an exact 8! label permutation test.

Two transfer scenarios are reported per subject:

    primary / hV4 : use Δλ̄ = (Δλ_V1 + Δλ_V2) / 2 on hV4 (held out)
    sanity  / V1  : use Δλ_V1 on V1 (in-sample)
    sanity  / V2  : use Δλ_V2 on V2 (in-sample)

Two exact 8! p-values per comparison:
    label_perm_p           — Spearman(simulated, CVD_vuln) vs random labels
    baseline_improvement_p — Δρ(fit)−Δρ(Δλ=0) vs random labels

Outputs (results/step3_neural/):

    sub-{ID}_{model}.json
        per-ROI block containing delta_lambda_used, simulated vulnerability,
        observed vulnerability, rho_obs, rho_baseline, label_perm_p,
        baseline_improvement_p.

    step3_neural_manifest.json

Usage:
    mpirun -np 1 python scripts/step3_validate_neural.py \
        --step0_dir results/step0_precompute \
        --step2_dir results/step2_finetune_l3 \
        --output_dir results/step3_neural

Reused helpers:
    simulate_mean_hc_wfixed            (step1_fit_loco_v2.py)
    permutation_test_spearman          (step1_fit_loco_v2.py)
    permutation_test_improvement       (step1_fit_loco_v2.py)
    load_cvd_loco_target               (step1_fit_loco_v2.py)
    load_amplitudes                    (future_phase1_forward_model)
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple

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
    HUE_ANGLES,
    N_CHANNELS,
    create_basis_matrix,
    load_amplitudes,
)
from utils_distortion_models import get_design_matrix  # noqa: E402
from step1_fit_loco_v2 import (  # noqa: E402
    simulate_mean_hc_wfixed,
    permutation_test_spearman,
    permutation_test_improvement,
    load_cvd_loco_target,
)
from machado_simulator import DELTA_LAMBDA_MAX  # noqa: E402

# ============================================================================
# Config
# ============================================================================

CVD_TYPE = {'08': 'deutan', '09': 'protan', '10': 'normal'}

PRIMARY_HELD_OUT_ROI = 'hV4'
DISK_ROI = {'V1': 'V1', 'V2': 'V2', 'hV4': 'V4'}

DEFAULT_MODELS = ['machado_1way', 'machado_alpha_free']
DEFAULT_ROIS = ('V1', 'V2', 'hV4')  # V1/V2 in-sample sanity, hV4 held out

LOCAL_BASELINE = (Path(__file__).resolve().parent.parent.parent.parent
                  / 'phase1_preprocess_decoding' / 'results' / 'full_dataset_C010')


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


def _load_hc_amplitudes(baseline_dir: str,
                        hc_subjects,
                        logical_roi: str) -> Dict[str, np.ndarray]:
    disk_roi = DISK_ROI.get(logical_roi, logical_roi)
    return {
        subj: load_amplitudes(baseline_dir, subj, disk_roi)
        for subj in hc_subjects
    }


# ============================================================================
# Per-(subject, model, ROI) transfer
# ============================================================================

def _delta_for_roi(logical_roi: str,
                   delta_v1: float,
                   delta_v2: float) -> float:
    """Choose which Δλ to apply at a given ROI.

    V1/V2 use their own fitted Δλ (in-sample sanity). hV4 is held out and
    uses the joint mean Δλ̄ = (Δλ_V1 + Δλ_V2)/2 as the honest transfer value.
    """
    if logical_roi == 'V1':
        return float(delta_v1)
    if logical_roi == 'V2':
        return float(delta_v2)
    if logical_roi == 'hV4':
        return float(0.5 * (delta_v1 + delta_v2))
    return float(0.5 * (delta_v1 + delta_v2))


def _params_for_model(model: str, delta_lambda: float,
                      stage2_doc: Dict) -> np.ndarray:
    """Build the full parameter vector for a distortion model.

    machado_1way       : [Δλ]
    machado_alpha_free : [Δλ, α]  — α inherited from Stage 2 best block

    We reuse the α that Stage 2 used (stored on the best block). If absent
    we default to 0.75 which matches the Stage-1 initialiser.
    """
    if model == 'machado_1way':
        return np.array([float(delta_lambda)], dtype=float)
    if model == 'machado_alpha_free':
        alpha = stage2_doc.get('best', {}).get('alpha', 0.75)
        try:
            alpha = float(alpha)
        except Exception:  # noqa: BLE001
            alpha = 0.75
        return np.array([float(delta_lambda), alpha], dtype=float)
    # Legacy fallbacks (Stage 2 should not invoke these, but be safe)
    return np.array([float(delta_lambda)], dtype=float)


def _neural_validate_one(cvd_subj: str,
                         logical_roi: str,
                         model: str,
                         delta_lambda: float,
                         stage2_doc: Dict,
                         hc_W: Dict[str, np.ndarray],
                         hc_amps: Dict[str, np.ndarray],
                         n_perm: int = 40320,
                         cvd_type_override: str = None) -> Dict:
    """Run the NEURAL transfer check for one (subject, ROI, model).

    If ``cvd_type_override`` is supplied it overrides the native
    ``CVD_TYPE[cvd_subj]`` mapping (cross-family specificity mode).
    """
    cvd_type_native = CVD_TYPE[cvd_subj]
    cvd_type = cvd_type_override if cvd_type_override else cvd_type_native

    # Build C_fit and C_baseline
    params_fit = _params_for_model(model, delta_lambda, stage2_doc)
    C_fit = get_design_matrix(model, params_fit, cvd_type=cvd_type)
    C_baseline = create_basis_matrix(HUE_ANGLES, N_CHANNELS)

    # Simulated mean-HC vulnerability at fit and at Δλ=0
    vuln_fit, per_hc_fit = simulate_mean_hc_wfixed(hc_W, hc_amps, C_fit)
    vuln_base, per_hc_base = simulate_mean_hc_wfixed(hc_W, hc_amps, C_baseline)

    # Observed CVD LOCO vulnerability
    # NOTE: LOCO JSON keys are disk-ROI names ('V4'), not logical ('hV4').
    loco_key = DISK_ROI.get(logical_roi, logical_roi)
    cvd_vuln = load_cvd_loco_target(cvd_subj, loco_key, model='ridge_gcv')

    # Primary: label-permutation Spearman at the fit
    p_label, null_label, rho_fit = permutation_test_spearman(
        vuln_fit, cvd_vuln, n_perm=n_perm)

    # Secondary: improvement over Δλ=0 baseline
    # We need to reuse the dedicated improvement test with the full argument
    # list. permutation_test_improvement expects hc_W_dict/hc_amps_dict/...
    p_impr, null_impr, delta_rho_obs, rho_fit2, rho_base = \
        permutation_test_improvement(
            hc_W, hc_amps, cvd_vuln,
            model_name=model, params_opt=params_fit,
            cvd_type=cvd_type, n_perm=n_perm)

    return {
        'roi': logical_roi,
        'model': model,
        'cvd_type': cvd_type,
        'cvd_type_native': cvd_type_native,
        'cvd_type_override': cvd_type_override,
        'delta_lambda_nm': float(delta_lambda),
        'params': params_fit.tolist(),
        'simulated_vuln': vuln_fit.tolist(),
        'simulated_vuln_baseline': vuln_base.tolist(),
        'observed_vuln_cvd': cvd_vuln.tolist(),
        'per_hc_vuln_fit': {s: v.tolist() for s, v in per_hc_fit.items()},
        'rho_fit': float(rho_fit),
        'rho_baseline': float(rho_base),
        'delta_rho_obs': float(delta_rho_obs),
        'label_perm_p': float(p_label),
        'baseline_improvement_p': float(p_impr),
        'null_label_perm': {
            'mean': float(np.mean(null_label)),
            'std': float(np.std(null_label)),
            'size': int(len(null_label)),
        },
        'null_improvement': {
            'mean': float(np.mean(null_impr)),
            'std': float(np.std(null_impr)),
            'size': int(len(null_impr)),
        },
    }


# ============================================================================
# Main
# ============================================================================

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description='Gen-4 Stage 3a NEURAL transfer (hV4 held out)')
    p.add_argument('--step0_dir', type=str,
                   default='results/step0_precompute')
    p.add_argument('--step2_dir', type=str,
                   default='results/step2_finetune_l3')
    p.add_argument('--output_dir', type=str,
                   default='results/step3_neural')
    p.add_argument('--baseline_dir', type=str, default=str(LOCAL_BASELINE))
    p.add_argument('--rois', nargs='+', default=list(DEFAULT_ROIS))
    p.add_argument('--models', nargs='+', default=DEFAULT_MODELS)
    p.add_argument('--cvd_subjects', nargs='+',
                   default=list(CVD_TYPE.keys()))
    p.add_argument('--cvd_type_override', type=str, default=None,
                   choices=['protan', 'deutan', 'normal'],
                   help='Force a cvd_type for ALL --cvd_subjects (cross-'
                        'family specificity test). Default: use native '
                        'CVD_TYPE mapping.')
    p.add_argument('--hc_subjects', nargs='+', default=HC_SUBJECTS)
    p.add_argument('--n_perm', type=int, default=40320,
                   help='Permutation count; >=40320 triggers exact 8!')
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    step0_dir = Path(args.step0_dir).resolve()
    step2_dir = Path(args.step2_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    print('=' * 64)
    print('Gen-4 Stage 3a NEURAL validation (hV4 held out)')
    print(f'  step0_dir  : {step0_dir}')
    print(f'  step2_dir  : {step2_dir}')
    print(f'  output_dir : {output_dir}')
    print(f'  ROIs       : {args.rois}')
    print(f'  models     : {args.models}')
    print(f'  subjects   : {args.cvd_subjects}')
    if args.cvd_type_override:
        print(f'  ⚠ cvd_type_override: {args.cvd_type_override} '
              f'(cross-family specificity mode)')
    print(f'  n_perm     : {args.n_perm} (exact 8! if >= 40320)')
    print('=' * 64)

    # Load Stage-0 HC W for every ROI we will transfer to
    hc_W_per_roi: Dict[str, Dict[str, np.ndarray]] = {}
    for roi in args.rois:
        hc_W_per_roi[roi] = _load_hc_W(step0_dir, roi)

    # Load HC amplitudes for every ROI (needed by improvement permutation)
    hc_amps_per_roi: Dict[str, Dict[str, np.ndarray]] = {}
    for roi in args.rois:
        hc_amps_per_roi[roi] = _load_hc_amplitudes(
            args.baseline_dir, args.hc_subjects, roi)

    manifest = {
        'timestamp': datetime.now().isoformat(),
        'step0_dir': str(step0_dir),
        'step2_dir': str(step2_dir),
        'rois': list(args.rois),
        'models': list(args.models),
        'cvd_subjects': list(args.cvd_subjects),
        'cvd_type_override': args.cvd_type_override,
        'n_perm': int(args.n_perm),
        'entries': [],
    }

    for model in args.models:
        print(f'\n[model {model}]')
        for cvd_subj in args.cvd_subjects:
            stage2 = _load_stage2(step2_dir, cvd_subj, model)
            delta_v1 = float(stage2['best']['delta_v1_nm'])
            delta_v2 = float(stage2['best']['delta_v2_nm'])
            delta_bar = 0.5 * (delta_v1 + delta_v2)
            effective_cvd_type = (
                args.cvd_type_override
                if args.cvd_type_override else CVD_TYPE[cvd_subj])
            family_tag = effective_cvd_type
            if args.cvd_type_override:
                family_tag = (f'{effective_cvd_type} [override, '
                              f'native={CVD_TYPE[cvd_subj]}]')
            print(f'  sub-{cvd_subj} ({family_tag}): '
                  f'Δλ_V1={delta_v1:.2f}, Δλ_V2={delta_v2:.2f}, '
                  f'Δλ̄={delta_bar:.2f} nm')

            subject_entry = {
                'subject': cvd_subj,
                'cvd_type': effective_cvd_type,
                'cvd_type_native': CVD_TYPE[cvd_subj],
                'cvd_type_override': args.cvd_type_override,
                'model': model,
                'delta_v1_nm': delta_v1,
                'delta_v2_nm': delta_v2,
                'delta_bar_nm': float(delta_bar),
                'rois': {},
            }

            for roi in args.rois:
                dl = _delta_for_roi(roi, delta_v1, delta_v2)
                hc_W = hc_W_per_roi[roi]
                hc_amps = hc_amps_per_roi[roi]
                try:
                    out = _neural_validate_one(
                        cvd_subj=cvd_subj,
                        logical_roi=roi,
                        model=model,
                        delta_lambda=dl,
                        stage2_doc=stage2,
                        hc_W=hc_W,
                        hc_amps=hc_amps,
                        n_perm=args.n_perm,
                        cvd_type_override=args.cvd_type_override,
                    )
                except FileNotFoundError as exc:
                    print(f'    {roi}: missing LOCO target ({exc}) — skip')
                    continue
                subject_entry['rois'][roi] = out
                print(f'    {roi:4s}  Δλ={dl:5.2f}  '
                      f'ρ_fit={out["rho_fit"]:+.3f}  '
                      f'ρ_base={out["rho_baseline"]:+.3f}  '
                      f'label_p={out["label_perm_p"]:.4f}  '
                      f'improv_p={out["baseline_improvement_p"]:.4f}')

            out_path = output_dir / f'sub-{cvd_subj}_{model}.json'
            with open(out_path, 'w') as f:
                json.dump(subject_entry, f, indent=2)
            manifest['entries'].append({
                'subject': cvd_subj,
                'model': model,
                'path': str(out_path),
                'delta_v1_nm': delta_v1,
                'delta_v2_nm': delta_v2,
                'delta_bar_nm': float(delta_bar),
                'hV4_rho_fit': subject_entry['rois'].get(
                    'hV4', {}).get('rho_fit'),
                'hV4_label_perm_p': subject_entry['rois'].get(
                    'hV4', {}).get('label_perm_p'),
                'hV4_baseline_improvement_p': subject_entry['rois'].get(
                    'hV4', {}).get('baseline_improvement_p'),
            })

    manifest_path = output_dir / 'step3_neural_manifest.json'
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    print(f'\nManifest → {manifest_path}')
    print('Stage 3a NEURAL complete.')


if __name__ == '__main__':
    main()
