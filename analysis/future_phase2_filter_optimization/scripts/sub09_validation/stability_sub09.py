#!/usr/bin/env python3
"""
stability_sub09.py — Robustness of sub-09 V1 Δλ≈16.5 nm under perturbations.

Checks whether the Gen-4 UNIFIED result for sub-09 protan × machado_1way
survives the following perturbations (all at fixed model = machado_1way,
fixed cvd_type = protan):

    1. Grid coarseness    (3 × 3 = 9 configs)
        - Stage 1 Δλ step  ∈ {0.25, 0.5, 1.0} nm  (1D anchor grid)
        - Stage 2 refine step ∈ {0.05, 0.1, 0.2} nm  (2D joint grid)
    2. Refine window width (4 widths)
        - ± {1.5, 3, 6, 10} nm around each Stage-1 anchor
    3. LOHO (7 HC leave-one-out refits)
        - Rebuild ridge_gcv W_HC without each HC subject, refit Stage 1+2
    4. LORO (6 CVD run leave-one-out refits)
        - Rebuild ΔRDM_obs on 5/6 CVD runs, refit Stage 1+2
    5. V1-only fit (λ_ROI = 0)
        - Decouple V1/V2; report each ROI's independent argmax
    6. Baseline reference
        - The canonical Stage 2 config (anchor 0.5 nm, refine ±3 nm / 0.1 nm,
          all 7 HC, all 6 runs) for comparison

For LOHO and LORO we additionally run the exact 8! joint V1+V2 permutation
test to check whether the ΔRDM geometry remains significant (label_p ≤ 0.10
and baseline_improvement_p ≤ 0.10) after the perturbation.

Pass criterion
--------------
    Primary:   Δλ_V1 ∈ [13, 19] nm for ≥ 80% of all perturbations
    Secondary: LOHO and LORO rounds keep label_p ≤ 0.10 for ≥ 6/7 and ≥ 5/6

Outputs (to ``results/sub09_validation/stability/``)
----------------------------------------------------
    stability_table.csv        one row per perturbation × ROI
    stability_summary.json     pass rates, histograms, verdict
    fig_delta_hist.png         histogram of Δλ_V1 with [13, 19] band shaded
    fig_perturbation_bar.png   bar chart of Δλ_V1 per perturbation class

Usage (local):
    conda activate srm
    python scripts/sub09_validation/stability_sub09.py

Reused helpers:
    L3_MachadoV1V2                 (l3_loss.py)
    get_design_matrix              (utils_distortion_models.py)
    compute_delta_rdm_sim / obs    (diagnostic_delta_rdm.py)
    precompute_hc_W                (diagnostic_delta_rdm.py)
    machado_shifted_hue            (machado_simulator.py)
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Path setup: scripts/sub09_validation/ → scripts/ → cone_shift_pipeline/ ↑ 3
_HERE = Path(__file__).resolve().parent
_SCRIPTS_DIR = _HERE.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

_FWD_DIR = str(_HERE.parent.parent.parent.parent
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
from diagnostic_delta_rdm import (  # noqa: E402
    compute_delta_rdm_obs,
    compute_delta_rdm_sim,
    cosine_similarity,
    precompute_hc_W,
)
from l3_loss import L3_MachadoV1V2  # noqa: E402
from machado_simulator import DELTA_LAMBDA_MAX  # noqa: E402

# ============================================================================
# Config — sub-09 only, machado_1way only
# ============================================================================

SUBJECT = '09'
CVD_TYPE = 'protan'
MODEL = 'machado_1way'

FIT_ROIS = ('V1', 'V2')
DISK_ROI = {'V1': 'V1', 'V2': 'V2', 'hV4': 'V4'}

LOCAL_BASELINE = (_HERE.parent.parent.parent.parent
                  / 'phase1_procrustes_decoding' / 'results' / 'visualization'
                  / 'full_dataset_C010_with_residuals')

# Canonical Gen-4 Stage 2 hyperparameters (for reference)
CANON_ANCHOR_STEP_NM = 0.5
CANON_REFINE_STEP_NM = 0.1
CANON_WINDOW_HALF_NM = 3.0
CANON_LAM_SCALE = 0.01
CANON_LAM_ROI = 0.005

# Pass band for the primary stability criterion
DELTA_V1_PASS_LO = 13.0
DELTA_V1_PASS_HI = 19.0
DELTA_V1_CANONICAL = 16.5   # from step2_finetune_l3/sub-09_machado_1way.json

# Perturbation grids
GRID_ANCHOR_STEPS = [0.25, 0.5, 1.0]        # nm
GRID_REFINE_STEPS = [0.05, 0.1, 0.2]        # nm
WINDOW_HALF_WIDTHS = [1.5, 3.0, 6.0, 10.0]  # nm


# ============================================================================
# Minimal Stage 1 + Stage 2 reimplementation (so we can rebuild caches)
# ============================================================================

def _delta_grid(step: float, dl_max: float = DELTA_LAMBDA_MAX) -> np.ndarray:
    n = int(round(dl_max / step)) + 1
    return np.linspace(0.0, dl_max, n)


def _narrow_grid(center: float, half: float, step: float,
                 dl_max: float = DELTA_LAMBDA_MAX) -> np.ndarray:
    lo = max(0.0, float(center) - half)
    hi = min(float(dl_max), float(center) + half)
    n = int(round((hi - lo) / step)) + 1
    if n < 2:
        return np.array([lo], dtype=float)
    return np.linspace(lo, hi, n)


def _stage1_anchor_1d(roi: str,
                      hc_W: Dict[str, np.ndarray],
                      delta_rdm_obs: np.ndarray,
                      C_baseline: np.ndarray,
                      anchor_step: float) -> Tuple[float, float]:
    """Replicate Stage 1 machado_1way anchor for a single ROI.

    Returns (best_delta_nm, best_l1).
    """
    grid = _delta_grid(anchor_step)
    best_l1 = -np.inf
    best_dl = 0.0
    for dl in grid:
        C_shifted = get_design_matrix(
            MODEL, [float(dl)], cvd_type=CVD_TYPE)
        delta_sim, _ = compute_delta_rdm_sim(
            hc_W, C_shifted, C_baseline, distance='correlation')
        l1 = cosine_similarity(delta_sim, delta_rdm_obs)
        if l1 > best_l1:
            best_l1 = l1
            best_dl = float(dl)
    return best_dl, float(best_l1)


def _stage2_joint_grid(loss: L3_MachadoV1V2,
                       hc_W_dicts: Dict[str, Dict[str, np.ndarray]],
                       C_baseline: np.ndarray,
                       delta_rdm_obs_dicts: Dict[str, np.ndarray],
                       anchor_v1: float,
                       anchor_v2: float,
                       half: float,
                       step: float) -> Dict:
    """Replicate Stage 2 joint L3 fine-tune and return the argmax result."""
    grid_v1 = _narrow_grid(anchor_v1, half=half, step=step)
    grid_v2 = _narrow_grid(anchor_v2, half=half, step=step)

    best = {'l3': -np.inf}
    for dv1 in grid_v1:
        for dv2 in grid_v2:
            out = loss.compute(
                delta_lambda_v1=float(dv1),
                delta_lambda_v2=float(dv2),
                cvd_type=CVD_TYPE,
                hc_W_dicts=hc_W_dicts,
                C_baseline=C_baseline,
                delta_rdm_obs_dicts=delta_rdm_obs_dicts,
            )
            if out['l3'] > best['l3']:
                best = out

    baseline_out = loss.compute(
        delta_lambda_v1=0.0,
        delta_lambda_v2=0.0,
        cvd_type=CVD_TYPE,
        hc_W_dicts=hc_W_dicts,
        C_baseline=C_baseline,
        delta_rdm_obs_dicts=delta_rdm_obs_dicts,
    )

    return {
        'best_delta_v1_nm': float(best['delta_v1']),
        'best_delta_v2_nm': float(best['delta_v2']),
        'best_l3': float(best['l3']),
        'best_l1': float(best['l1']),
        'best_l1_V1': float(best['l1_V1']),
        'best_l1_V2': float(best['l1_V2']),
        'baseline_l3': float(baseline_out['l3']),
        'baseline_l1': float(baseline_out['l1']),
    }


def _fit_pipeline(hc_W_dicts: Dict[str, Dict[str, np.ndarray]],
                  delta_rdm_obs_dicts: Dict[str, np.ndarray],
                  C_baseline: np.ndarray,
                  anchor_step: float,
                  refine_step: float,
                  window_half: float,
                  lam_scale: float = CANON_LAM_SCALE,
                  lam_roi: float = CANON_LAM_ROI,
                  run_permutation: bool = False) -> Dict:
    """Full Stage 1 → Stage 2 refit for the current (hc_W, ΔRDM_obs) state.

    Optionally runs the exact 8! joint permutation at the argmax.
    """
    # Stage 1 — independent anchors for V1, V2
    anchor_v1, l1_anchor_v1 = _stage1_anchor_1d(
        'V1', hc_W_dicts['V1'], delta_rdm_obs_dicts['V1'],
        C_baseline, anchor_step)
    anchor_v2, l1_anchor_v2 = _stage1_anchor_1d(
        'V2', hc_W_dicts['V2'], delta_rdm_obs_dicts['V2'],
        C_baseline, anchor_step)

    # Stage 2 — joint L3
    loss = L3_MachadoV1V2(
        lam_scale=lam_scale,
        lam_roi=lam_roi,
        delta_lambda_max=DELTA_LAMBDA_MAX,
        metric='cosine',
        model_name=MODEL,
    )
    stage2 = _stage2_joint_grid(
        loss=loss,
        hc_W_dicts=hc_W_dicts,
        C_baseline=C_baseline,
        delta_rdm_obs_dicts=delta_rdm_obs_dicts,
        anchor_v1=anchor_v1,
        anchor_v2=anchor_v2,
        half=window_half,
        step=refine_step,
    )

    out = {
        'anchor_step_nm': anchor_step,
        'refine_step_nm': refine_step,
        'window_half_nm': window_half,
        'lam_scale': lam_scale,
        'lam_roi': lam_roi,
        'anchor_v1_nm': float(anchor_v1),
        'anchor_v2_nm': float(anchor_v2),
        'l1_anchor_v1': float(l1_anchor_v1),
        'l1_anchor_v2': float(l1_anchor_v2),
        **stage2,
    }

    if run_permutation:
        null = loss.permutation_null(
            best_delta_v1=stage2['best_delta_v1_nm'],
            best_delta_v2=stage2['best_delta_v2_nm'],
            cvd_type=CVD_TYPE,
            hc_W_dicts=hc_W_dicts,
            C_baseline=C_baseline,
            delta_rdm_obs_dicts=delta_rdm_obs_dicts,
            baseline_l3=stage2['baseline_l3'],
        )
        out['label_perm_p'] = float(null['label_perm_p'])
        out['baseline_improvement_p'] = float(
            null.get('baseline_improvement_p', np.nan))
    else:
        out['label_perm_p'] = None
        out['baseline_improvement_p'] = None

    return out


# ============================================================================
# Data loading (fresh, so we can perturb at the amplitude level)
# ============================================================================

def _load_all_hc_amps(baseline_dir: str,
                      roi: str) -> Dict[str, np.ndarray]:
    disk_roi = DISK_ROI.get(roi, roi)
    return {s: load_amplitudes(baseline_dir, s, disk_roi) for s in HC_SUBJECTS}


def _load_cvd_amps(baseline_dir: str, roi: str) -> np.ndarray:
    disk_roi = DISK_ROI.get(roi, roi)
    return load_amplitudes(baseline_dir, SUBJECT, disk_roi)


def _build_state(baseline_dir: str,
                 hc_amps_by_roi: Dict[str, Dict[str, np.ndarray]],
                 cvd_amps_by_roi: Dict[str, np.ndarray],
                 C_baseline: np.ndarray,
                 hc_keep: Optional[List[str]] = None,
                 runs_keep: Optional[List[int]] = None
                 ) -> Tuple[Dict[str, Dict[str, np.ndarray]],
                            Dict[str, np.ndarray]]:
    """Build (hc_W_dicts, delta_rdm_obs_dicts) for the V1/V2 fit ROIs,
    after optionally dropping HC subjects or CVD runs.

    hc_keep:    subset of HC IDs to use when recomputing W (None → all)
    runs_keep:  subset of run indices (0..5) to use when recomputing ΔRDM_obs
                on the CVD side (None → all six)
    """
    hc_W_dicts: Dict[str, Dict[str, np.ndarray]] = {}
    delta_rdm_obs_dicts: Dict[str, np.ndarray] = {}

    for roi in FIT_ROIS:
        hc_amps_full = hc_amps_by_roi[roi]
        if hc_keep is not None:
            hc_amps = {s: hc_amps_full[s] for s in hc_keep}
        else:
            hc_amps = dict(hc_amps_full)

        # Recompute W_HC on this HC subset (α via GCV per subject)
        hc_W, _ = precompute_hc_W(hc_amps, C_baseline)
        hc_W_dicts[roi] = hc_W

        # Apply run subset on the CVD side only (we do not drop runs for HC
        # here — the LORO perturbation is defined at the CVD-ΔRDM level)
        amp_cvd = cvd_amps_by_roi[roi]
        if runs_keep is not None:
            amp_cvd = amp_cvd[np.asarray(runs_keep, dtype=int)]

        delta_obs, _, _, _ = compute_delta_rdm_obs(
            amp_cvd, hc_amps, distance='correlation')
        delta_rdm_obs_dicts[roi] = delta_obs

    return hc_W_dicts, delta_rdm_obs_dicts


# ============================================================================
# Perturbation runners
# ============================================================================

def run_canonical(baseline_dir: str,
                  hc_amps_by_roi,
                  cvd_amps_by_roi,
                  C_baseline) -> Dict:
    """Baseline Gen-4 Stage 2 config (full dataset, canonical grid)."""
    hc_W_dicts, drdm_dicts = _build_state(
        baseline_dir, hc_amps_by_roi, cvd_amps_by_roi, C_baseline)
    out = _fit_pipeline(
        hc_W_dicts, drdm_dicts, C_baseline,
        anchor_step=CANON_ANCHOR_STEP_NM,
        refine_step=CANON_REFINE_STEP_NM,
        window_half=CANON_WINDOW_HALF_NM,
        run_permutation=True,
    )
    out['class'] = 'canonical'
    out['label'] = 'canonical'
    return out


def run_grid_coarseness(baseline_dir,
                        hc_amps_by_roi,
                        cvd_amps_by_roi,
                        C_baseline) -> List[Dict]:
    """Sweep Stage-1 anchor step × Stage-2 refine step."""
    hc_W_dicts, drdm_dicts = _build_state(
        baseline_dir, hc_amps_by_roi, cvd_amps_by_roi, C_baseline)
    rows = []
    for a_step in GRID_ANCHOR_STEPS:
        for r_step in GRID_REFINE_STEPS:
            out = _fit_pipeline(
                hc_W_dicts, drdm_dicts, C_baseline,
                anchor_step=a_step,
                refine_step=r_step,
                window_half=CANON_WINDOW_HALF_NM,
                run_permutation=False,
            )
            out['class'] = 'grid_coarseness'
            out['label'] = f'anchor{a_step}nm_refine{r_step}nm'
            rows.append(out)
            print(f'    grid a={a_step:.2f}/r={r_step:.2f}: '
                  f'Δλ_V1={out["best_delta_v1_nm"]:.2f}, '
                  f'Δλ_V2={out["best_delta_v2_nm"]:.2f}, '
                  f'L3={out["best_l3"]:+.4f}')
    return rows


def run_window_width(baseline_dir,
                     hc_amps_by_roi,
                     cvd_amps_by_roi,
                     C_baseline) -> List[Dict]:
    """Sweep Stage-2 refine window half-width."""
    hc_W_dicts, drdm_dicts = _build_state(
        baseline_dir, hc_amps_by_roi, cvd_amps_by_roi, C_baseline)
    rows = []
    for half in WINDOW_HALF_WIDTHS:
        out = _fit_pipeline(
            hc_W_dicts, drdm_dicts, C_baseline,
            anchor_step=CANON_ANCHOR_STEP_NM,
            refine_step=CANON_REFINE_STEP_NM,
            window_half=half,
            run_permutation=False,
        )
        out['class'] = 'window_width'
        out['label'] = f'half{half}nm'
        rows.append(out)
        print(f'    window ±{half} nm: '
              f'Δλ_V1={out["best_delta_v1_nm"]:.2f}, '
              f'Δλ_V2={out["best_delta_v2_nm"]:.2f}, '
              f'L3={out["best_l3"]:+.4f}')
    return rows


def run_loho(baseline_dir,
             hc_amps_by_roi,
             cvd_amps_by_roi,
             C_baseline) -> List[Dict]:
    """Leave-one-HC-out: rebuild W_HC from 6 HCs, refit Stage 1+2, permute."""
    rows = []
    for left_out in HC_SUBJECTS:
        keep = [s for s in HC_SUBJECTS if s != left_out]
        hc_W_dicts, drdm_dicts = _build_state(
            baseline_dir, hc_amps_by_roi, cvd_amps_by_roi, C_baseline,
            hc_keep=keep, runs_keep=None)
        out = _fit_pipeline(
            hc_W_dicts, drdm_dicts, C_baseline,
            anchor_step=CANON_ANCHOR_STEP_NM,
            refine_step=CANON_REFINE_STEP_NM,
            window_half=CANON_WINDOW_HALF_NM,
            run_permutation=True,
        )
        out['class'] = 'loho'
        out['label'] = f'drop_{left_out}'
        out['left_out_hc'] = left_out
        rows.append(out)
        print(f'    LOHO drop {left_out}: '
              f'Δλ_V1={out["best_delta_v1_nm"]:.2f}, '
              f'Δλ_V2={out["best_delta_v2_nm"]:.2f}, '
              f'label_p={out["label_perm_p"]:.4f}, '
              f'improv_p={out["baseline_improvement_p"]:.4f}')
    return rows


def run_loro(baseline_dir,
             hc_amps_by_roi,
             cvd_amps_by_roi,
             C_baseline) -> List[Dict]:
    """Leave-one-CVD-run-out: refit Stage 1+2 on 5/6 runs, permute."""
    rows = []
    n_runs = cvd_amps_by_roi[FIT_ROIS[0]].shape[0]
    for drop in range(n_runs):
        keep = [r for r in range(n_runs) if r != drop]
        hc_W_dicts, drdm_dicts = _build_state(
            baseline_dir, hc_amps_by_roi, cvd_amps_by_roi, C_baseline,
            hc_keep=None, runs_keep=keep)
        out = _fit_pipeline(
            hc_W_dicts, drdm_dicts, C_baseline,
            anchor_step=CANON_ANCHOR_STEP_NM,
            refine_step=CANON_REFINE_STEP_NM,
            window_half=CANON_WINDOW_HALF_NM,
            run_permutation=True,
        )
        out['class'] = 'loro'
        out['label'] = f'drop_run{drop}'
        out['left_out_run'] = int(drop)
        rows.append(out)
        print(f'    LORO drop run {drop}: '
              f'Δλ_V1={out["best_delta_v1_nm"]:.2f}, '
              f'Δλ_V2={out["best_delta_v2_nm"]:.2f}, '
              f'label_p={out["label_perm_p"]:.4f}, '
              f'improv_p={out["baseline_improvement_p"]:.4f}')
    return rows


def run_v1_only(baseline_dir,
                hc_amps_by_roi,
                cvd_amps_by_roi,
                C_baseline) -> Dict:
    """λ_ROI = 0 → V1 and V2 decouple. Report each ROI's independent argmax."""
    hc_W_dicts, drdm_dicts = _build_state(
        baseline_dir, hc_amps_by_roi, cvd_amps_by_roi, C_baseline)
    out = _fit_pipeline(
        hc_W_dicts, drdm_dicts, C_baseline,
        anchor_step=CANON_ANCHOR_STEP_NM,
        refine_step=CANON_REFINE_STEP_NM,
        window_half=CANON_WINDOW_HALF_NM,
        lam_scale=CANON_LAM_SCALE,
        lam_roi=0.0,
        run_permutation=False,
    )
    out['class'] = 'v1_only'
    out['label'] = 'lam_roi_0'
    return out


# ============================================================================
# Aggregation + visualisation
# ============================================================================

def _in_pass_band(delta: float) -> bool:
    return DELTA_V1_PASS_LO <= delta <= DELTA_V1_PASS_HI


def _summarise(rows: List[Dict]) -> Dict:
    deltas_v1 = np.array([r['best_delta_v1_nm'] for r in rows], dtype=float)
    deltas_v2 = np.array([r['best_delta_v2_nm'] for r in rows], dtype=float)
    n = len(rows)
    n_pass = int(sum(_in_pass_band(d) for d in deltas_v1))
    pass_rate = float(n_pass) / float(n) if n else 0.0

    loho_rows = [r for r in rows if r['class'] == 'loho']
    loro_rows = [r for r in rows if r['class'] == 'loro']

    def _perm_pass(rs):
        total = len(rs)
        if not total:
            return 0, 0, 0.0
        label_pass = sum(1 for r in rs
                         if r.get('label_perm_p') is not None
                         and r['label_perm_p'] <= 0.10)
        return label_pass, total, float(label_pass) / float(total)

    loho_pass, loho_n, loho_rate = _perm_pass(loho_rows)
    loro_pass, loro_n, loro_rate = _perm_pass(loro_rows)

    verdict_primary = 'PASS' if pass_rate >= 0.80 else 'FAIL'
    verdict_loho = 'PASS' if (loho_n == 0 or loho_pass >= max(1, int(np.ceil(6 / 7 * loho_n)))) else 'FAIL'
    verdict_loro = 'PASS' if (loro_n == 0 or loro_pass >= max(1, int(np.ceil(5 / 6 * loro_n)))) else 'FAIL'

    return {
        'n_perturbations': n,
        'canonical_delta_v1_nm': DELTA_V1_CANONICAL,
        'pass_band_nm': [DELTA_V1_PASS_LO, DELTA_V1_PASS_HI],
        'delta_v1': {
            'mean': float(np.mean(deltas_v1)),
            'std': float(np.std(deltas_v1, ddof=0)),
            'median': float(np.median(deltas_v1)),
            'min': float(np.min(deltas_v1)),
            'max': float(np.max(deltas_v1)),
            'n_in_band': n_pass,
            'pass_rate': pass_rate,
        },
        'delta_v2': {
            'mean': float(np.mean(deltas_v2)),
            'std': float(np.std(deltas_v2, ddof=0)),
            'min': float(np.min(deltas_v2)),
            'max': float(np.max(deltas_v2)),
        },
        'loho': {
            'n': loho_n, 'label_p_pass_n': loho_pass,
            'label_p_pass_rate': loho_rate,
        },
        'loro': {
            'n': loro_n, 'label_p_pass_n': loro_pass,
            'label_p_pass_rate': loro_rate,
        },
        'verdict': {
            'primary_delta_band': verdict_primary,
            'loho_label_p': verdict_loho,
            'loro_label_p': verdict_loro,
            'overall': (
                'PASS'
                if verdict_primary == 'PASS'
                and verdict_loho == 'PASS'
                and verdict_loro == 'PASS'
                else 'FAIL'
            ),
        },
    }


def _write_csv(rows: List[Dict], out_path: Path) -> None:
    columns = [
        'class', 'label',
        'anchor_step_nm', 'refine_step_nm', 'window_half_nm',
        'lam_scale', 'lam_roi',
        'anchor_v1_nm', 'anchor_v2_nm',
        'l1_anchor_v1', 'l1_anchor_v2',
        'best_delta_v1_nm', 'best_delta_v2_nm',
        'best_l3', 'best_l1', 'best_l1_V1', 'best_l1_V2',
        'baseline_l3', 'baseline_l1',
        'label_perm_p', 'baseline_improvement_p',
        'left_out_hc', 'left_out_run',
        'in_pass_band',
    ]
    with open(out_path, 'w') as f:
        f.write(','.join(columns) + '\n')
        for r in rows:
            in_band = _in_pass_band(r['best_delta_v1_nm'])
            vals = [
                r.get('class', ''),
                r.get('label', ''),
                r.get('anchor_step_nm', ''),
                r.get('refine_step_nm', ''),
                r.get('window_half_nm', ''),
                r.get('lam_scale', ''),
                r.get('lam_roi', ''),
                r.get('anchor_v1_nm', ''),
                r.get('anchor_v2_nm', ''),
                r.get('l1_anchor_v1', ''),
                r.get('l1_anchor_v2', ''),
                r.get('best_delta_v1_nm', ''),
                r.get('best_delta_v2_nm', ''),
                r.get('best_l3', ''),
                r.get('best_l1', ''),
                r.get('best_l1_V1', ''),
                r.get('best_l1_V2', ''),
                r.get('baseline_l3', ''),
                r.get('baseline_l1', ''),
                r.get('label_perm_p', '') if r.get('label_perm_p') is not None else '',
                r.get('baseline_improvement_p', '') if r.get('baseline_improvement_p') is not None else '',
                r.get('left_out_hc', ''),
                r.get('left_out_run', ''),
                int(in_band),
            ]
            f.write(','.join(str(v) for v in vals) + '\n')


def _plot_histogram(rows: List[Dict], out_path: Path) -> None:
    deltas = [r['best_delta_v1_nm'] for r in rows]
    fig, ax = plt.subplots(figsize=(7, 4))
    bins = np.arange(0, 21, 0.5)
    ax.hist(deltas, bins=bins, color='#2ca02c', alpha=0.75, edgecolor='k')
    ax.axvspan(DELTA_V1_PASS_LO, DELTA_V1_PASS_HI, color='#2ca02c', alpha=0.15,
               label=f'Pass band [{DELTA_V1_PASS_LO}, {DELTA_V1_PASS_HI}] nm')
    ax.axvline(DELTA_V1_CANONICAL, color='#d62728', linestyle='--', lw=2,
               label=f'Canonical Δλ_V1 = {DELTA_V1_CANONICAL} nm')
    ax.set_xlabel('Fitted Δλ_V1 (nm)')
    ax.set_ylabel('Count (perturbations)')
    ax.set_title('sub-09 × machado_1way: Δλ_V1 stability under perturbations')
    ax.legend(loc='upper left', frameon=False)
    ax.set_xlim(0, 20)
    fig.tight_layout()
    fig.savefig(out_path, dpi=160)
    plt.close(fig)


def _plot_perturbation_bar(rows: List[Dict], out_path: Path) -> None:
    # One bar per perturbation, grouped by class
    class_order = ['canonical', 'grid_coarseness', 'window_width',
                   'loho', 'loro', 'v1_only']
    class_color = {
        'canonical': '#2ca02c',
        'grid_coarseness': '#1f77b4',
        'window_width': '#ff7f0e',
        'loho': '#9467bd',
        'loro': '#8c564b',
        'v1_only': '#e377c2',
    }
    fig, ax = plt.subplots(figsize=(11, 4.5))
    x = []
    heights = []
    colors = []
    xticklabels = []
    i = 0
    for cls in class_order:
        subset = [r for r in rows if r['class'] == cls]
        for r in subset:
            x.append(i)
            heights.append(r['best_delta_v1_nm'])
            colors.append(class_color.get(cls, '#333333'))
            xticklabels.append(f"{cls}:{r['label']}")
            i += 1
    ax.bar(x, heights, color=colors, edgecolor='k', linewidth=0.5)
    ax.axhspan(DELTA_V1_PASS_LO, DELTA_V1_PASS_HI, color='#2ca02c', alpha=0.12,
               label='Pass band')
    ax.axhline(DELTA_V1_CANONICAL, color='#d62728', linestyle='--', lw=1.5,
               label=f'Canonical = {DELTA_V1_CANONICAL} nm')
    ax.set_ylabel('Fitted Δλ_V1 (nm)')
    ax.set_xticks(x)
    ax.set_xticklabels(xticklabels, rotation=75, ha='right', fontsize=7)
    ax.set_ylim(0, 20)
    ax.set_title('sub-09 × machado_1way: Δλ_V1 per perturbation')
    ax.legend(loc='upper right', frameon=False)
    fig.tight_layout()
    fig.savefig(out_path, dpi=160)
    plt.close(fig)


# ============================================================================
# Main
# ============================================================================

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description='sub-09 V1 Δλ stability under perturbations')
    p.add_argument('--baseline_dir', type=str, default=str(LOCAL_BASELINE),
                   help='C010 amplitudes root (default: local)')
    p.add_argument('--output_dir', type=str,
                   default='results/sub09_validation/stability',
                   help='Output directory (relative to cone_shift_pipeline)')
    p.add_argument('--skip_permutation', action='store_true',
                   help='Skip exact 8! permutations (faster but no p-values)')
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    print('=' * 64)
    print('sub-09 V1 Δλ stability verification')
    print(f'  subject       : sub-{SUBJECT} ({CVD_TYPE})')
    print(f'  model         : {MODEL}')
    print(f'  canonical Δλ  : {DELTA_V1_CANONICAL} nm')
    print(f'  pass band     : [{DELTA_V1_PASS_LO}, {DELTA_V1_PASS_HI}] nm')
    print(f'  baseline_dir  : {args.baseline_dir}')
    print(f'  output_dir    : {output_dir}')
    print('=' * 64)

    # Load raw amplitudes ONCE (HC + CVD) for V1 and V2 — then every
    # perturbation can sub-sample from these in-memory arrays.
    print('\n[load] HC + CVD amplitudes for V1, V2')
    hc_amps_by_roi: Dict[str, Dict[str, np.ndarray]] = {}
    cvd_amps_by_roi: Dict[str, np.ndarray] = {}
    for roi in FIT_ROIS:
        hc_amps_by_roi[roi] = _load_all_hc_amps(args.baseline_dir, roi)
        cvd_amps_by_roi[roi] = _load_cvd_amps(args.baseline_dir, roi)
        vs_summary = ', '.join(
            f'{s}:{a.shape[2]}' for s, a in hc_amps_by_roi[roi].items())
        print(f'    {roi}: HC {vs_summary} | CVD '
              f'shape={cvd_amps_by_roi[roi].shape}')

    C_baseline = create_basis_matrix(HUE_ANGLES, N_CHANNELS)

    all_rows: List[Dict] = []

    # Canonical reference
    print('\n[run] canonical (full 7 HC, full 6 runs, a=0.5/r=0.1/±3)')
    canon = run_canonical(
        args.baseline_dir, hc_amps_by_roi, cvd_amps_by_roi, C_baseline)
    print(f'    Δλ_V1={canon["best_delta_v1_nm"]:.2f}, '
          f'Δλ_V2={canon["best_delta_v2_nm"]:.2f}, '
          f'L3={canon["best_l3"]:+.4f}, '
          f'label_p={canon["label_perm_p"]:.4f}, '
          f'improv_p={canon["baseline_improvement_p"]:.4f}')
    all_rows.append(canon)

    # Grid coarseness
    print('\n[run] grid coarseness (3 × 3)')
    all_rows.extend(run_grid_coarseness(
        args.baseline_dir, hc_amps_by_roi, cvd_amps_by_roi, C_baseline))

    # Window width
    print('\n[run] window width (4)')
    all_rows.extend(run_window_width(
        args.baseline_dir, hc_amps_by_roi, cvd_amps_by_roi, C_baseline))

    # LOHO — optionally skip the 7× permutation
    if args.skip_permutation:
        print('\n[run] LOHO (7 HCs, no permutation)')
    else:
        print('\n[run] LOHO (7 HCs, exact 8! permutation)')
    # When skip_permutation is set, we temporarily monkey-patch the wrapper
    # below to avoid the expensive null; implement by branching.
    loho_rows = []
    for left_out in HC_SUBJECTS:
        keep = [s for s in HC_SUBJECTS if s != left_out]
        hc_W_dicts, drdm_dicts = _build_state(
            args.baseline_dir, hc_amps_by_roi, cvd_amps_by_roi, C_baseline,
            hc_keep=keep, runs_keep=None)
        out = _fit_pipeline(
            hc_W_dicts, drdm_dicts, C_baseline,
            anchor_step=CANON_ANCHOR_STEP_NM,
            refine_step=CANON_REFINE_STEP_NM,
            window_half=CANON_WINDOW_HALF_NM,
            run_permutation=not args.skip_permutation,
        )
        out['class'] = 'loho'
        out['label'] = f'drop_{left_out}'
        out['left_out_hc'] = left_out
        lp = out.get('label_perm_p')
        ip = out.get('baseline_improvement_p')
        lp_str = f'{lp:.4f}' if lp is not None else 'skip'
        ip_str = f'{ip:.4f}' if ip is not None else 'skip'
        print(f'    LOHO drop {left_out}: '
              f'Δλ_V1={out["best_delta_v1_nm"]:.2f}, '
              f'Δλ_V2={out["best_delta_v2_nm"]:.2f}, '
              f'label_p={lp_str}, improv_p={ip_str}')
        loho_rows.append(out)
    all_rows.extend(loho_rows)

    # LORO — 6 CVD runs
    if args.skip_permutation:
        print('\n[run] LORO (6 CVD runs, no permutation)')
    else:
        print('\n[run] LORO (6 CVD runs, exact 8! permutation)')
    loro_rows = []
    n_runs = cvd_amps_by_roi[FIT_ROIS[0]].shape[0]
    for drop in range(n_runs):
        keep = [r for r in range(n_runs) if r != drop]
        hc_W_dicts, drdm_dicts = _build_state(
            args.baseline_dir, hc_amps_by_roi, cvd_amps_by_roi, C_baseline,
            hc_keep=None, runs_keep=keep)
        out = _fit_pipeline(
            hc_W_dicts, drdm_dicts, C_baseline,
            anchor_step=CANON_ANCHOR_STEP_NM,
            refine_step=CANON_REFINE_STEP_NM,
            window_half=CANON_WINDOW_HALF_NM,
            run_permutation=not args.skip_permutation,
        )
        out['class'] = 'loro'
        out['label'] = f'drop_run{drop}'
        out['left_out_run'] = int(drop)
        lp = out.get('label_perm_p')
        ip = out.get('baseline_improvement_p')
        lp_str = f'{lp:.4f}' if lp is not None else 'skip'
        ip_str = f'{ip:.4f}' if ip is not None else 'skip'
        print(f'    LORO drop run {drop}: '
              f'Δλ_V1={out["best_delta_v1_nm"]:.2f}, '
              f'Δλ_V2={out["best_delta_v2_nm"]:.2f}, '
              f'label_p={lp_str}, improv_p={ip_str}')
        loro_rows.append(out)
    all_rows.extend(loro_rows)

    # V1-only fit
    print('\n[run] V1-only (λ_ROI = 0)')
    v1_only = run_v1_only(
        args.baseline_dir, hc_amps_by_roi, cvd_amps_by_roi, C_baseline)
    print(f'    V1-only: Δλ_V1={v1_only["best_delta_v1_nm"]:.2f}, '
          f'Δλ_V2={v1_only["best_delta_v2_nm"]:.2f}, '
          f'L3={v1_only["best_l3"]:+.4f}')
    all_rows.append(v1_only)

    # Write outputs
    print('\n[write] stability_table.csv')
    _write_csv(all_rows, output_dir / 'stability_table.csv')

    summary = _summarise(all_rows)
    summary['subject'] = SUBJECT
    summary['model'] = MODEL
    summary['cvd_type'] = CVD_TYPE
    summary['timestamp'] = datetime.now().isoformat()
    summary['perturbations'] = [
        {
            'class': r['class'],
            'label': r['label'],
            'best_delta_v1_nm': r['best_delta_v1_nm'],
            'best_delta_v2_nm': r['best_delta_v2_nm'],
            'best_l3': r['best_l3'],
            'label_perm_p': r.get('label_perm_p'),
            'baseline_improvement_p': r.get('baseline_improvement_p'),
            'in_pass_band': bool(_in_pass_band(r['best_delta_v1_nm'])),
        }
        for r in all_rows
    ]

    print('[write] stability_summary.json')
    with open(output_dir / 'stability_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)

    print('[plot] fig_delta_hist.png')
    _plot_histogram(all_rows, output_dir / 'fig_delta_hist.png')
    print('[plot] fig_perturbation_bar.png')
    _plot_perturbation_bar(all_rows, output_dir / 'fig_perturbation_bar.png')

    # Stdout summary
    print('\n' + '=' * 64)
    print('SUMMARY')
    print(f'  n_perturbations        : {summary["n_perturbations"]}')
    print(f'  Δλ_V1 pass band        : [{DELTA_V1_PASS_LO}, {DELTA_V1_PASS_HI}] nm')
    print(f'  Δλ_V1 mean ± std       : '
          f'{summary["delta_v1"]["mean"]:.2f} ± {summary["delta_v1"]["std"]:.2f} nm')
    print(f'  Δλ_V1 median [min,max] : '
          f'{summary["delta_v1"]["median"]:.2f} '
          f'[{summary["delta_v1"]["min"]:.2f}, '
          f'{summary["delta_v1"]["max"]:.2f}] nm')
    print(f'  Δλ_V1 pass rate        : '
          f'{summary["delta_v1"]["n_in_band"]}/{summary["n_perturbations"]} '
          f'({summary["delta_v1"]["pass_rate"] * 100:.1f}%)')
    print(f'  LOHO label_p ≤ 0.10    : '
          f'{summary["loho"]["label_p_pass_n"]}/{summary["loho"]["n"]}')
    print(f'  LORO label_p ≤ 0.10    : '
          f'{summary["loro"]["label_p_pass_n"]}/{summary["loro"]["n"]}')
    print(f'  verdict                : {summary["verdict"]["overall"]} '
          f'(primary={summary["verdict"]["primary_delta_band"]}, '
          f'loho={summary["verdict"]["loho_label_p"]}, '
          f'loro={summary["verdict"]["loro_label_p"]})')
    print('=' * 64)


if __name__ == '__main__':
    main()
