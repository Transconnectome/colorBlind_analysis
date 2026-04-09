#!/usr/bin/env python3
"""
family_specificity.py — Gen-4 sub-09 family-sanity + α-degeneracy probe.

This script answers two questions about the Gen-4 sub-09 fit:

    (1) Cross-family sanity: if we refit every CVD subject with the *wrong*
        cone family (protan ↔ deutan), does the L1 cosine similarity
        collapse as expected? Sub-09 is protan, so fitting sub-09 under
        the deutan family must underperform fitting it under the protan
        family — otherwise the Machado anchor is not actually
        discriminative between families and our fitted Δλ is arbitrary.

    (2) α-degeneracy probe: the Stage-1 / Stage-2 machado_alpha_free fits
        collapsed to α ≈ 0.05 (near-dichromat) with small Δλ for every
        subject. Is that a true minimum, or is the joint surface so
        shallow that the unconstrained search drops into the α→0 corner?
        We answer this by fixing α ∈ {0.25, 0.50, 0.75, 0.90, 1.00} and
        sweeping Δλ ∈ [0, 20] at 0.5 nm on sub-09 V1+V2. If any
        constrained α recovers a Δλ ≥ 15 nm with near-competitive L1,
        the Gen-4 α_free fit is a degenerate optimum, not the global one.

Design notes
------------
* Reuses Stage-0 caches (``results/step0_precompute/hc_W_{V1,V2}.npz`` and
  ``delta_rdm_obs_{V1,V2}.npz``) — no refit of W or ΔRDM_obs.
* L1 = cosine similarity between the simulated ΔRDM and the observed
  ΔRDM per ROI, exactly as in ``step1_machado_anchor._score_params``.
* Joint score L1_joint = 0.5 · (L1_V1 + L1_V2) — matches Stage-2 L3
  base.
* α-sweep uses the same machado_alpha_free design matrix that Stage 2
  used (via ``get_design_matrix('machado_alpha_free', [Δλ, α], ...)``).

Pass criteria (stated, not enforced):
    (1) For sub-09, L1_joint(protan) > L1_joint(deutan) by a clear
        margin (Δ ≥ 0.05 on cosine scale).
    (2) For sub-09, some α ∈ {0.25, …, 1.00} recovers a best Δλ ≥ 15 nm
        within 0.05 of the Gen-4 machado_alpha_free L1 (which collapsed
        to Δλ ≈ 4 nm, α = 0.05).

Outputs (to ``results/sub09_validation/family_specificity/``):
    family_table.csv                       — 3 subj × 2 family × 2 ROI rows
    family_summary.json                    — structured summary
    alpha_sweep_table.csv                  — α-constrained Δλ sweep, sub-09
    alpha_sweep_summary.json
    fig_family_heatmap.png                 — 3×2 L1_joint heatmap
    fig_alpha_sweep.png                    — sub-09 V1+V2 L1 vs Δλ per α
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ---------------------------------------------------------------- paths
_HERE = Path(__file__).resolve().parent
_SCRIPTS_DIR = _HERE.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))
_FWD_DIR = str(_HERE.parent.parent.parent.parent
               / 'future_phase1_forward_model' / 'scripts')
if _FWD_DIR not in sys.path:
    sys.path.insert(0, _FWD_DIR)

from utils_forward_model import (  # noqa: E402
    HUE_ANGLES,
    N_CHANNELS,
    create_basis_matrix,
)
from utils_distortion_models import get_design_matrix  # noqa: E402
from diagnostic_delta_rdm import (  # noqa: E402
    compute_delta_rdm_sim,
    cosine_similarity,
)

_PIPELINE = _HERE.parent.parent
STEP0_DIR = _PIPELINE / 'results' / 'step0_precompute'
DEFAULT_OUT = _PIPELINE / 'results' / 'sub09_validation' / 'family_specificity'

# ---------------------------------------------------------------- config
CVD_SUBJECTS = ['08', '09', '10']
CVD_TRUE_TYPE = {'08': 'deutan', '09': 'protan', '10': 'deutan'}
FAMILIES = ['protan', 'deutan']
ROIS = ['V1', 'V2']

# Grid (matches Stage 1 default: 41 points)
DELTA_GRID = np.arange(0.0, 20.0 + 1e-9, 0.5)
ALPHA_CONSTRAINTS = [0.25, 0.50, 0.75, 0.90, 1.00]

# Pass-criterion thresholds (diagnostic, not enforced)
FAMILY_MARGIN = 0.05       # L1_joint(correct) − L1_joint(wrong)
ALPHA_RECOVER_THRESH = 15.0  # nm


# ---------------------------------------------------------------- loaders
def _load_hc_W(roi: str) -> Dict[str, np.ndarray]:
    data = np.load(STEP0_DIR / f'hc_W_{roi}.npz', allow_pickle=True)
    subj_ids = list(data['subj_ids'])
    return {s: np.asarray(data[f'W_{s}'], dtype=np.float64) for s in subj_ids}


def _load_delta_rdm_obs(roi: str) -> Dict[str, np.ndarray]:
    data = np.load(STEP0_DIR / f'delta_rdm_obs_{roi}.npz', allow_pickle=True)
    cvd_ids = list(data['cvd_ids'])
    return {s: np.asarray(data[f'delta_rdm_{s}'], dtype=np.float64)
            for s in cvd_ids}


# ---------------------------------------------------------------- scoring
def _score(model: str,
           params: List[float],
           cvd_type: str,
           hc_W: Dict[str, np.ndarray],
           C_baseline: np.ndarray,
           delta_rdm_obs: np.ndarray) -> float:
    C_shifted = get_design_matrix(model, params, cvd_type=cvd_type)
    delta_sim, _ = compute_delta_rdm_sim(
        hc_W, C_shifted, C_baseline, distance='correlation')
    return float(cosine_similarity(delta_sim, delta_rdm_obs))


def _sweep_machado_1way(cvd_type: str,
                        hc_W: Dict[str, np.ndarray],
                        C_baseline: np.ndarray,
                        delta_rdm_obs: np.ndarray) -> Dict:
    l1_profile = np.array([
        _score('machado_1way', [float(dl)], cvd_type, hc_W, C_baseline,
               delta_rdm_obs)
        for dl in DELTA_GRID
    ])
    best_idx = int(np.argmax(l1_profile))
    return {
        'delta_grid_nm': DELTA_GRID.tolist(),
        'l1_profile': l1_profile.tolist(),
        'best_delta_lambda_nm': float(DELTA_GRID[best_idx]),
        'best_l1': float(l1_profile[best_idx]),
        'l1_at_zero': float(l1_profile[0]),
    }


def _sweep_alpha_constrained(cvd_type: str,
                             alpha: float,
                             hc_W: Dict[str, np.ndarray],
                             C_baseline: np.ndarray,
                             delta_rdm_obs: np.ndarray) -> Dict:
    l1_profile = np.array([
        _score('machado_alpha_free', [float(dl), float(alpha)],
               cvd_type, hc_W, C_baseline, delta_rdm_obs)
        for dl in DELTA_GRID
    ])
    best_idx = int(np.argmax(l1_profile))
    return {
        'alpha': float(alpha),
        'delta_grid_nm': DELTA_GRID.tolist(),
        'l1_profile': l1_profile.tolist(),
        'best_delta_lambda_nm': float(DELTA_GRID[best_idx]),
        'best_l1': float(l1_profile[best_idx]),
    }


# ---------------------------------------------------------------- main blocks
def _family_matrix(hc_W_all: Dict[str, Dict[str, np.ndarray]],
                   delta_obs_all: Dict[str, Dict[str, np.ndarray]],
                   C_baseline: np.ndarray) -> Dict:
    """Fit every (subject, family, ROI) triple and build 3×2 joint matrix."""
    table: List[Dict] = []
    joint: Dict[str, Dict[str, float]] = {s: {} for s in CVD_SUBJECTS}
    per_roi_profiles: Dict[str, Dict[str, Dict[str, Dict]]] = {
        s: {fam: {} for fam in FAMILIES} for s in CVD_SUBJECTS
    }

    for subj in CVD_SUBJECTS:
        for family in FAMILIES:
            per_roi_scores = {}
            for roi in ROIS:
                res = _sweep_machado_1way(
                    family,
                    hc_W_all[roi],
                    C_baseline,
                    delta_obs_all[roi][subj],
                )
                per_roi_scores[roi] = res['best_l1']
                per_roi_profiles[subj][family][roi] = res
                table.append({
                    'subject': subj,
                    'true_family': CVD_TRUE_TYPE[subj],
                    'tested_family': family,
                    'roi': roi,
                    'best_delta_lambda_nm': res['best_delta_lambda_nm'],
                    'best_l1': res['best_l1'],
                    'l1_at_zero': res['l1_at_zero'],
                })
            joint[subj][family] = 0.5 * (per_roi_scores['V1']
                                         + per_roi_scores['V2'])

    # Verdict per subject
    verdicts: Dict[str, Dict] = {}
    for subj in CVD_SUBJECTS:
        l1_correct = joint[subj][CVD_TRUE_TYPE[subj]]
        l1_wrong = joint[subj]['protan' if CVD_TRUE_TYPE[subj] == 'deutan'
                               else 'deutan']
        margin = l1_correct - l1_wrong
        verdicts[subj] = {
            'true_family': CVD_TRUE_TYPE[subj],
            'l1_joint_true': float(l1_correct),
            'l1_joint_swapped': float(l1_wrong),
            'margin': float(margin),
            'pass_margin_05': bool(margin >= FAMILY_MARGIN),
        }

    return {
        'cvd_subjects': CVD_SUBJECTS,
        'families': FAMILIES,
        'rois': ROIS,
        'table': table,
        'joint_l1': {s: {f: float(v) for f, v in joint[s].items()}
                     for s in CVD_SUBJECTS},
        'per_roi_profiles': per_roi_profiles,
        'verdicts': verdicts,
    }


def _alpha_sweep(hc_W_all: Dict[str, Dict[str, np.ndarray]],
                 delta_obs_all: Dict[str, Dict[str, np.ndarray]],
                 C_baseline: np.ndarray) -> Dict:
    """α-constrained sweep on sub-09 V1+V2 under protan family."""
    subj = '09'
    family = 'protan'
    results: Dict[str, Dict] = {}
    for alpha in ALPHA_CONSTRAINTS:
        per_roi = {}
        joint_profile = np.zeros_like(DELTA_GRID)
        for roi in ROIS:
            res = _sweep_alpha_constrained(
                family,
                alpha,
                hc_W_all[roi],
                C_baseline,
                delta_obs_all[roi][subj],
            )
            per_roi[roi] = res
            joint_profile += 0.5 * np.asarray(res['l1_profile'])
        best_idx = int(np.argmax(joint_profile))
        results[f'alpha_{alpha:.2f}'] = {
            'alpha': float(alpha),
            'per_roi': per_roi,
            'joint_l1_profile': joint_profile.tolist(),
            'best_delta_lambda_nm': float(DELTA_GRID[best_idx]),
            'best_joint_l1': float(joint_profile[best_idx]),
        }

    # Reference: Gen-4 actual fit
    gen4_reference = {
        'delta_v1_nm': 1.0,   # from step2_finetune_l3/sub-09_machado_alpha_free.json
        'delta_v2_nm': 0.0,
        'alpha': 0.05,
        'best_l1': 0.08010244498225735,  # l1_V1 from that file
        'source': 'step2_finetune_l3/sub-09_machado_alpha_free.json',
    }

    # Verdict
    recover_hits = [
        (name, block) for name, block in results.items()
        if block['best_delta_lambda_nm'] >= ALPHA_RECOVER_THRESH
    ]
    return {
        'subject': subj,
        'family': family,
        'alphas': ALPHA_CONSTRAINTS,
        'delta_grid_nm': DELTA_GRID.tolist(),
        'per_alpha': results,
        'gen4_reference': gen4_reference,
        'alpha_recover_threshold_nm': ALPHA_RECOVER_THRESH,
        'n_alphas_recovering_ge_15nm': len(recover_hits),
        'recovering_alphas': [
            {'name': name,
             'alpha': block['alpha'],
             'best_delta_lambda_nm': block['best_delta_lambda_nm'],
             'best_joint_l1': block['best_joint_l1']}
            for name, block in recover_hits
        ],
    }


# ---------------------------------------------------------------- writers
def _write_family_table(family_block: Dict, path: Path) -> None:
    keys = ['subject', 'true_family', 'tested_family', 'roi',
            'best_delta_lambda_nm', 'best_l1', 'l1_at_zero']
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(family_block['table'])


def _write_alpha_table(alpha_block: Dict, path: Path) -> None:
    keys = ['alpha', 'roi', 'best_delta_lambda_nm', 'best_l1',
            'joint_best_delta_lambda_nm', 'joint_best_l1']
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for _, block in alpha_block['per_alpha'].items():
            for roi_name, roi_res in block['per_roi'].items():
                w.writerow({
                    'alpha': block['alpha'],
                    'roi': roi_name,
                    'best_delta_lambda_nm': roi_res['best_delta_lambda_nm'],
                    'best_l1': roi_res['best_l1'],
                    'joint_best_delta_lambda_nm': block['best_delta_lambda_nm'],
                    'joint_best_l1': block['best_joint_l1'],
                })


def _plot_family_heatmap(family_block: Dict, path: Path) -> None:
    mat = np.array([
        [family_block['joint_l1'][s][f] for f in FAMILIES]
        for s in CVD_SUBJECTS
    ])
    fig, ax = plt.subplots(figsize=(5.2, 4.2))
    im = ax.imshow(mat, aspect='auto', cmap='RdBu_r',
                   vmin=-max(abs(mat.max()), abs(mat.min())),
                   vmax=max(abs(mat.max()), abs(mat.min())))
    ax.set_xticks(range(len(FAMILIES)))
    ax.set_xticklabels(FAMILIES)
    ax.set_yticks(range(len(CVD_SUBJECTS)))
    ax.set_yticklabels([f'sub-{s}\n({CVD_TRUE_TYPE[s]})'
                        for s in CVD_SUBJECTS])
    ax.set_xlabel('tested family')
    ax.set_title('L1_joint(V1+V2)/2 — Gen-4 family specificity')
    for i, s in enumerate(CVD_SUBJECTS):
        for j, fam in enumerate(FAMILIES):
            val = mat[i, j]
            ax.text(j, i, f'{val:+.3f}', ha='center', va='center',
                    color='white' if abs(val) > 0.15 else 'black',
                    fontsize=10)
    fig.colorbar(im, ax=ax, label='L1_joint (cosine)')
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)


def _plot_alpha_sweep(alpha_block: Dict, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(6.0, 4.2))
    cmap = plt.get_cmap('viridis')
    for i, (_name, block) in enumerate(alpha_block['per_alpha'].items()):
        color = cmap(i / max(1, len(alpha_block['per_alpha']) - 1))
        ax.plot(DELTA_GRID, block['joint_l1_profile'],
                label=f'α={block["alpha"]:.2f}',
                color=color, lw=1.8)
        ax.scatter([block['best_delta_lambda_nm']],
                   [block['best_joint_l1']],
                   color=color, s=40, zorder=5, edgecolor='k')
    # Gen-4 reference marker
    ref = alpha_block['gen4_reference']
    ax.axvline(ref['delta_v1_nm'], ls=':', color='red', lw=1.2,
               label=f'Gen-4 α_free V1 Δλ={ref["delta_v1_nm"]} '
                     f'(α={ref["alpha"]})')
    ax.axvline(ALPHA_RECOVER_THRESH, ls='--', color='grey', lw=1.0,
               label=f'recover threshold {ALPHA_RECOVER_THRESH} nm')
    ax.set_xlabel('Δλ (nm)')
    ax.set_ylabel('L1_joint (V1+V2)/2')
    ax.set_title('sub-09 α-constrained Machado sweep')
    ax.legend(loc='lower right', fontsize=8)
    ax.grid(True, alpha=0.2)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)


# ---------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output_dir', default=str(DEFAULT_OUT))
    args = ap.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load caches (V1 + V2 only — hV4 is held out from L1)
    hc_W_all: Dict[str, Dict[str, np.ndarray]] = {}
    delta_obs_all: Dict[str, Dict[str, np.ndarray]] = {}
    for roi in ROIS:
        hc_W_all[roi] = _load_hc_W(roi)
        delta_obs_all[roi] = _load_delta_rdm_obs(roi)

    C_baseline = create_basis_matrix(HUE_ANGLES, N_CHANNELS)

    # Block 1: cross-family 3×2 matrix
    print('== Cross-family sanity ==')
    family_block = _family_matrix(hc_W_all, delta_obs_all, C_baseline)
    for subj, v in family_block['verdicts'].items():
        print(f'  sub-{subj} ({v["true_family"]}) '
              f'L1_true={v["l1_joint_true"]:+.3f} '
              f'L1_swap={v["l1_joint_swapped"]:+.3f} '
              f'margin={v["margin"]:+.3f} '
              f'pass_margin_05={"YES" if v["pass_margin_05"] else "NO"}')

    _write_family_table(family_block, out_dir / 'family_table.csv')
    with (out_dir / 'family_summary.json').open('w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'family_margin_threshold': FAMILY_MARGIN,
            **family_block,
        }, f, indent=2)
    _plot_family_heatmap(family_block, out_dir / 'fig_family_heatmap.png')

    # Block 2: α-constrained sweep for sub-09
    print('\n== sub-09 α-constrained sweep ==')
    alpha_block = _alpha_sweep(hc_W_all, delta_obs_all, C_baseline)
    for _, block in alpha_block['per_alpha'].items():
        print(f'  α={block["alpha"]:.2f}  '
              f'best Δλ={block["best_delta_lambda_nm"]:5.1f} nm  '
              f'joint L1={block["best_joint_l1"]:+.4f}')
    print(f'  # α recovering Δλ ≥ {ALPHA_RECOVER_THRESH} nm: '
          f'{alpha_block["n_alphas_recovering_ge_15nm"]} / '
          f'{len(ALPHA_CONSTRAINTS)}')

    _write_alpha_table(alpha_block, out_dir / 'alpha_sweep_table.csv')
    with (out_dir / 'alpha_sweep_summary.json').open('w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            **alpha_block,
        }, f, indent=2)
    _plot_alpha_sweep(alpha_block, out_dir / 'fig_alpha_sweep.png')

    print(f'\nOutputs written to: {out_dir}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
