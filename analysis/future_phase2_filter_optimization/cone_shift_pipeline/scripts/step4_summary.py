#!/usr/bin/env python3
"""
step4_summary.py — Gen-4 Stage 4 aggregation and figures.

Reads every Stage-1/2/3a/3b JSON and emits:

    results/step4_summary/summary_table.csv
        One row per (subject, model, ROI) with
            subject, cvd_type, model, roi,
            anchor_delta_nm, anchor_l1,
            fit_delta_nm, fit_l1, l_scale, l_roi, l3,
            drift_nm,
            neural_rho_fit, neural_rho_base, neural_label_p,
            neural_baseline_improvement_p,
            cognition_closest_nm, cognition_label,
            cognition_hue_mse_deg2, cognition_drdm_cos,
            verdict

    results/step4_summary/step4_manifest.json
    results/step4_summary/figures/fig1_delta_lambda_bar.png
    results/step4_summary/figures/fig2_l3_landscape_sub08.png
    results/step4_summary/figures/fig3_neural_vs_cognition.png

Verdict rules (plan §4):

    PASS           NEURAL p ≤ α  AND  COGNITION hue_mse ≤ threshold
    NEURAL_ONLY    NEURAL p ≤ α  AND  COGNITION hue_mse >  threshold
    COGNITION_ONLY NEURAL p >  α  AND  COGNITION hue_mse ≤ threshold
    HOLD           NEURAL p >  α  AND  COGNITION hue_mse >  threshold

Per-ROI NEURAL p is used.

Usage:
    mpirun -np 1 python scripts/step4_summary.py \
        --step1_dir results/step1_machado_anchor \
        --step2_dir results/step2_finetune_l3 \
        --step3_neural_dir results/step3_neural \
        --step3_cognition_dir results/step3_cognition \
        --output_dir results/step4_summary
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402

# ============================================================================
# Config
# ============================================================================

CVD_TYPE = {'08': 'deutan', '09': 'protan', '10': 'normal'}

DEFAULT_MODELS = ['machado_1way', 'machado_alpha_free']
DEFAULT_ROIS = ('V1', 'V2', 'hV4')
DEFAULT_CVD_SUBJECTS = ('08', '09', '10')

DEFAULT_ALPHA = 0.05
DEFAULT_HUE_MSE_THRESHOLD = 15.0

SUMMARY_COLUMNS = [
    'subject', 'cvd_type', 'model', 'roi',
    'anchor_delta_nm', 'anchor_l1',
    'fit_delta_nm', 'fit_l1', 'l_scale', 'l_roi', 'l3',
    'drift_nm',
    'neural_rho_fit', 'neural_rho_base',
    'neural_label_perm_p', 'neural_baseline_improvement_p',
    'cognition_closest_nm', 'cognition_label',
    'cognition_hue_mse_deg2', 'cognition_drdm_cos',
    'verdict',
]


# ============================================================================
# JSON loaders
# ============================================================================

def _load_json(path: Path) -> Optional[Dict]:
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def _load_stage1(step1_dir: Path,
                 cvd_subj: str,
                 roi: str,
                 model: str) -> Optional[Dict]:
    return _load_json(step1_dir / f'sub-{cvd_subj}_{roi}_{model}.json')


def _load_stage2(step2_dir: Path,
                 cvd_subj: str,
                 model: str) -> Optional[Dict]:
    return _load_json(step2_dir / f'sub-{cvd_subj}_{model}.json')


def _load_stage3(dir_path: Path,
                 cvd_subj: str,
                 model: str) -> Optional[Dict]:
    return _load_json(dir_path / f'sub-{cvd_subj}_{model}.json')


# ============================================================================
# Row extraction
# ============================================================================

def _fit_delta_for_roi(roi: str, delta_v1: float, delta_v2: float) -> float:
    if roi == 'V1':
        return float(delta_v1)
    if roi == 'V2':
        return float(delta_v2)
    return float(0.5 * (delta_v1 + delta_v2))


def _anchor_delta_for_roi(step1_dir: Path,
                          cvd_subj: str,
                          roi: str,
                          model: str) -> (Optional[float], Optional[float]):
    """Return (anchor_delta_nm, anchor_l1) from Stage 1.

    For hV4 we return the V1/V2 mean as the reference anchor.
    """
    if roi in ('V1', 'V2'):
        doc = _load_stage1(step1_dir, cvd_subj, roi, model)
        if doc is None:
            return None, None
        params = doc.get('best', {}).get('params', [])
        l1 = doc.get('best', {}).get('l1')
        if not params:
            return None, None
        return float(params[0]), float(l1) if l1 is not None else None
    # hV4 — average V1 and V2 anchors
    d1, _ = _anchor_delta_for_roi(step1_dir, cvd_subj, 'V1', model)
    d2, _ = _anchor_delta_for_roi(step1_dir, cvd_subj, 'V2', model)
    if d1 is None or d2 is None:
        return None, None
    return float(0.5 * (d1 + d2)), None


def _fit_l1_for_roi(stage2_doc: Dict, roi: str) -> Optional[float]:
    best = stage2_doc.get('best', {}) if stage2_doc else {}
    if roi == 'V1':
        return float(best.get('l1_V1')) if best.get('l1_V1') is not None else None
    if roi == 'V2':
        return float(best.get('l1_V2')) if best.get('l1_V2') is not None else None
    # hV4 — no L1 (held out from the fit)
    return None


def _drift_for_roi(stage2_doc: Dict, roi: str) -> Optional[float]:
    drift = stage2_doc.get('drift', {}) if stage2_doc else {}
    if roi == 'V1':
        return float(drift.get('drift_v1_nm')) if drift.get('drift_v1_nm') is not None else None
    if roi == 'V2':
        return float(drift.get('drift_v2_nm')) if drift.get('drift_v2_nm') is not None else None
    return None


def _verdict(neural_p: Optional[float],
             cognition_hue_mse: Optional[float],
             alpha: float,
             hue_mse_threshold: float) -> str:
    if neural_p is None or cognition_hue_mse is None:
        return 'INCOMPLETE'
    neural_pass = float(neural_p) <= alpha
    cognition_pass = float(cognition_hue_mse) <= hue_mse_threshold
    if neural_pass and cognition_pass:
        return 'PASS'
    if neural_pass and not cognition_pass:
        return 'NEURAL_ONLY'
    if cognition_pass and not neural_pass:
        return 'COGNITION_ONLY'
    return 'HOLD'


def _build_row(cvd_subj: str,
               model: str,
               roi: str,
               step1_dir: Path,
               stage2_doc: Optional[Dict],
               stage3n_doc: Optional[Dict],
               stage3c_doc: Optional[Dict],
               alpha: float,
               hue_mse_threshold: float) -> Dict:
    """Assemble one row across all four stages."""
    cvd_type = CVD_TYPE.get(cvd_subj, 'unknown')

    # Stage 1 anchor
    anchor_delta, anchor_l1 = _anchor_delta_for_roi(
        step1_dir, cvd_subj, roi, model)

    # Stage 2 fit
    fit_delta = None
    fit_l1 = None
    l_scale = None
    l_roi = None
    l3 = None
    drift = None
    if stage2_doc is not None:
        best = stage2_doc.get('best', {})
        dv1 = best.get('delta_v1_nm')
        dv2 = best.get('delta_v2_nm')
        if dv1 is not None and dv2 is not None:
            fit_delta = _fit_delta_for_roi(roi, float(dv1), float(dv2))
        fit_l1 = _fit_l1_for_roi(stage2_doc, roi)
        l_scale = float(best.get('l_scale')) if best.get('l_scale') is not None else None
        l_roi = float(best.get('l_roi')) if best.get('l_roi') is not None else None
        l3 = float(best.get('l3')) if best.get('l3') is not None else None
        drift = _drift_for_roi(stage2_doc, roi)

    # Stage 3a — NEURAL
    neural_rho_fit = None
    neural_rho_base = None
    neural_label_p = None
    neural_improv_p = None
    if stage3n_doc is not None:
        n_block = stage3n_doc.get('rois', {}).get(roi, {})
        if n_block:
            neural_rho_fit = float(n_block.get('rho_fit')) if n_block.get('rho_fit') is not None else None
            neural_rho_base = float(n_block.get('rho_baseline')) if n_block.get('rho_baseline') is not None else None
            neural_label_p = float(n_block.get('label_perm_p')) if n_block.get('label_perm_p') is not None else None
            neural_improv_p = float(n_block.get('baseline_improvement_p')) if n_block.get('baseline_improvement_p') is not None else None

    # Stage 3b — COGNITION
    cog_closest_nm = None
    cog_label = None
    cog_hue_mse = None
    cog_drdm_cos = None
    if stage3c_doc is not None:
        c_block = stage3c_doc.get('rois', {}).get(roi, {})
        closest = c_block.get('closest', {}) if c_block else {}
        if closest:
            cog_closest_nm = float(closest.get('canonical_delta_lambda_nm')) if closest.get('canonical_delta_lambda_nm') is not None else None
            cog_label = closest.get('label')
            cog_hue_mse = float(closest.get('hue_mse_deg2')) if closest.get('hue_mse_deg2') is not None else None
            cog_drdm_cos = float(closest.get('drdm_cos')) if closest.get('drdm_cos') is not None else None

    verdict = _verdict(neural_label_p, cog_hue_mse, alpha, hue_mse_threshold)

    return {
        'subject': cvd_subj,
        'cvd_type': cvd_type,
        'model': model,
        'roi': roi,
        'anchor_delta_nm': anchor_delta,
        'anchor_l1': anchor_l1,
        'fit_delta_nm': fit_delta,
        'fit_l1': fit_l1,
        'l_scale': l_scale,
        'l_roi': l_roi,
        'l3': l3,
        'drift_nm': drift,
        'neural_rho_fit': neural_rho_fit,
        'neural_rho_base': neural_rho_base,
        'neural_label_perm_p': neural_label_p,
        'neural_baseline_improvement_p': neural_improv_p,
        'cognition_closest_nm': cog_closest_nm,
        'cognition_label': cog_label,
        'cognition_hue_mse_deg2': cog_hue_mse,
        'cognition_drdm_cos': cog_drdm_cos,
        'verdict': verdict,
    }


# ============================================================================
# CSV writer
# ============================================================================

def _write_csv(rows: List[Dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=SUMMARY_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k) for k in SUMMARY_COLUMNS})


# ============================================================================
# Figures (matplotlib only — no seaborn per CLAUDE.md)
# ============================================================================

VERDICT_COLORS = {
    'PASS': '#2ca02c',
    'NEURAL_ONLY': '#1f77b4',
    'COGNITION_ONLY': '#ff7f0e',
    'HOLD': '#d62728',
    'INCOMPLETE': '#7f7f7f',
}


def _fig1_delta_lambda_bar(rows: List[Dict],
                           out_path: Path,
                           models: List[str]) -> None:
    """Bar chart: fitted Δλ per (subject, model) × ROI."""
    fig, axes = plt.subplots(1, len(models),
                             figsize=(4 * len(models), 4),
                             sharey=True)
    if len(models) == 1:
        axes = [axes]

    subjects = sorted({r['subject'] for r in rows})
    rois = ['V1', 'V2', 'hV4']
    n_s = len(subjects)
    n_r = len(rois)
    width = 0.8 / n_r

    for ax, model in zip(axes, models):
        x = np.arange(n_s)
        for k, roi in enumerate(rois):
            vals = []
            for subj in subjects:
                match = [r for r in rows
                         if r['subject'] == subj
                         and r['model'] == model
                         and r['roi'] == roi]
                vals.append(match[0]['fit_delta_nm']
                            if match and match[0]['fit_delta_nm'] is not None
                            else np.nan)
            ax.bar(x + (k - (n_r - 1) / 2) * width, vals, width=width,
                   label=roi)
        ax.set_xticks(x)
        ax.set_xticklabels([f'sub-{s}\n({CVD_TYPE.get(s, "?")})'
                            for s in subjects])
        ax.set_title(model)
        ax.set_ylabel('Fitted Δλ (nm)')
        ax.axhline(0, color='k', linewidth=0.5)
        ax.grid(axis='y', alpha=0.3)
    axes[-1].legend(loc='upper right', frameon=False)
    fig.suptitle('Gen-4 fitted Δλ per ROI (Stage 2)')
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def _fig2_l3_landscape(step2_dir: Path,
                       out_path: Path,
                       subject: str = '08',
                       model: str = 'machado_1way') -> None:
    """Heatmap of the Stage-2 L₃ landscape for a chosen subject."""
    doc = _load_stage2(step2_dir, subject, model)
    if doc is None:
        return
    grid = doc.get('grid', {})
    l3 = np.asarray(grid.get('l3_grid', []), dtype=float)
    gv1 = np.asarray(grid.get('grid_v1_nm', []), dtype=float)
    gv2 = np.asarray(grid.get('grid_v2_nm', []), dtype=float)
    if l3.size == 0 or gv1.size == 0 or gv2.size == 0:
        return

    best = doc.get('best', {})
    anchor = doc.get('anchor', {})

    fig, ax = plt.subplots(figsize=(5, 4.5))
    extent = [gv2.min(), gv2.max(), gv1.min(), gv1.max()]
    im = ax.imshow(l3, origin='lower', extent=extent, aspect='auto',
                   cmap='viridis')
    fig.colorbar(im, ax=ax, label='L₃')
    if best:
        ax.plot(best.get('delta_v2_nm'), best.get('delta_v1_nm'),
                '*', color='white', markersize=14, markeredgecolor='black',
                label='best')
    if anchor:
        ax.plot(anchor.get('delta_v2_nm'), anchor.get('delta_v1_nm'),
                'o', color='red', markersize=8, markerfacecolor='none',
                label='Stage-1 anchor')
    ax.set_xlabel('Δλ_V2 (nm)')
    ax.set_ylabel('Δλ_V1 (nm)')
    ax.set_title(f'L₃ landscape  sub-{subject} × {model}')
    ax.legend(loc='upper right', frameon=True, fontsize=8)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def _fig3_neural_vs_cognition(rows: List[Dict],
                              out_path: Path,
                              hue_mse_threshold: float,
                              alpha: float) -> None:
    """Scatter: NEURAL rho_fit vs COGNITION hue_mse, coloured by verdict."""
    fig, ax = plt.subplots(figsize=(6, 5))
    # Quadrant lines
    ax.axvline(hue_mse_threshold, color='k', linestyle='--',
               linewidth=0.7, alpha=0.5)
    ax.axhline(0, color='k', linewidth=0.5)

    for verdict, color in VERDICT_COLORS.items():
        matches = [r for r in rows
                   if r['verdict'] == verdict
                   and r.get('cognition_hue_mse_deg2') is not None
                   and r.get('neural_rho_fit') is not None]
        if not matches:
            continue
        xs = [r['cognition_hue_mse_deg2'] for r in matches]
        ys = [r['neural_rho_fit'] for r in matches]
        ax.scatter(xs, ys, s=80, color=color, label=verdict,
                   edgecolors='black', linewidths=0.5, alpha=0.85)
        for r in matches:
            label = f'sub-{r["subject"]}·{r["roi"]}·{r["model"][:4]}'
            ax.annotate(label,
                        (r['cognition_hue_mse_deg2'], r['neural_rho_fit']),
                        fontsize=7, xytext=(4, 2), textcoords='offset points')

    ax.set_xlabel('COGNITION hue MSE (deg²)')
    ax.set_ylabel('NEURAL Spearman ρ(fit)')
    ax.set_title(f'Dual validation  (α={alpha}, hue_mse≤{hue_mse_threshold})')
    ax.legend(loc='best', frameon=True, fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


# ============================================================================
# Main
# ============================================================================

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description='Gen-4 Stage 4 summary and figures')
    p.add_argument('--step1_dir', type=str,
                   default='results/step1_machado_anchor')
    p.add_argument('--step2_dir', type=str,
                   default='results/step2_finetune_l3')
    p.add_argument('--step3_neural_dir', type=str,
                   default='results/step3_neural')
    p.add_argument('--step3_cognition_dir', type=str,
                   default='results/step3_cognition')
    p.add_argument('--output_dir', type=str,
                   default='results/step4_summary')
    p.add_argument('--models', nargs='+', default=DEFAULT_MODELS)
    p.add_argument('--rois', nargs='+', default=list(DEFAULT_ROIS))
    p.add_argument('--cvd_subjects', nargs='+',
                   default=list(DEFAULT_CVD_SUBJECTS))
    p.add_argument('--alpha', type=float, default=DEFAULT_ALPHA,
                   help='Significance threshold for NEURAL label_perm_p')
    p.add_argument('--hue_mse_threshold', type=float,
                   default=DEFAULT_HUE_MSE_THRESHOLD,
                   help='Maximum COGNITION hue_mse (deg²) for PASS verdict')
    p.add_argument('--landscape_subject', type=str, default='08')
    p.add_argument('--landscape_model', type=str,
                   default='machado_1way')
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    step1_dir = Path(args.step1_dir).resolve()
    step2_dir = Path(args.step2_dir).resolve()
    step3n_dir = Path(args.step3_neural_dir).resolve()
    step3c_dir = Path(args.step3_cognition_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    print('=' * 64)
    print('Gen-4 Stage 4 summary and figures')
    print(f'  step1_dir         : {step1_dir}')
    print(f'  step2_dir         : {step2_dir}')
    print(f'  step3_neural_dir  : {step3n_dir}')
    print(f'  step3_cognition_dir: {step3c_dir}')
    print(f'  output_dir        : {output_dir}')
    print(f'  ROIs              : {args.rois}')
    print(f'  models            : {args.models}')
    print(f'  subjects          : {args.cvd_subjects}')
    print(f'  α (NEURAL p)      : {args.alpha}')
    print(f'  hue_mse threshold : {args.hue_mse_threshold} deg²')
    print('=' * 64)

    rows: List[Dict] = []
    for model in args.models:
        for cvd_subj in args.cvd_subjects:
            stage2 = _load_stage2(step2_dir, cvd_subj, model)
            stage3n = _load_stage3(step3n_dir, cvd_subj, model)
            stage3c = _load_stage3(step3c_dir, cvd_subj, model)
            for roi in args.rois:
                row = _build_row(
                    cvd_subj=cvd_subj,
                    model=model,
                    roi=roi,
                    step1_dir=step1_dir,
                    stage2_doc=stage2,
                    stage3n_doc=stage3n,
                    stage3c_doc=stage3c,
                    alpha=args.alpha,
                    hue_mse_threshold=args.hue_mse_threshold,
                )
                rows.append(row)

    # CSV table
    csv_path = output_dir / 'summary_table.csv'
    _write_csv(rows, csv_path)
    print(f'\nSummary table → {csv_path}  ({len(rows)} rows)')

    # Figures
    figures_dir = output_dir / 'figures'
    _fig1_delta_lambda_bar(
        rows, figures_dir / 'fig1_delta_lambda_bar.png',
        models=list(args.models))
    _fig2_l3_landscape(
        step2_dir, figures_dir / 'fig2_l3_landscape_sub08.png',
        subject=args.landscape_subject, model=args.landscape_model)
    _fig3_neural_vs_cognition(
        rows, figures_dir / 'fig3_neural_vs_cognition.png',
        hue_mse_threshold=args.hue_mse_threshold, alpha=args.alpha)
    print(f'Figures → {figures_dir}')

    # Verdict histogram
    tally: Dict[str, int] = {}
    for row in rows:
        tally[row['verdict']] = tally.get(row['verdict'], 0) + 1
    print('\nVerdict tally:')
    for verdict, n in sorted(tally.items()):
        print(f'  {verdict:15s}: {n}')

    manifest = {
        'timestamp': datetime.now().isoformat(),
        'step1_dir': str(step1_dir),
        'step2_dir': str(step2_dir),
        'step3_neural_dir': str(step3n_dir),
        'step3_cognition_dir': str(step3c_dir),
        'alpha': float(args.alpha),
        'hue_mse_threshold': float(args.hue_mse_threshold),
        'models': list(args.models),
        'rois': list(args.rois),
        'cvd_subjects': list(args.cvd_subjects),
        'n_rows': len(rows),
        'verdict_tally': tally,
        'summary_table_csv': str(csv_path),
        'figures': [
            str(figures_dir / 'fig1_delta_lambda_bar.png'),
            str(figures_dir / 'fig2_l3_landscape_sub08.png'),
            str(figures_dir / 'fig3_neural_vs_cognition.png'),
        ],
    }
    manifest_path = output_dir / 'step4_manifest.json'
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    print(f'Manifest → {manifest_path}')
    print('Stage 4 complete.')


if __name__ == '__main__':
    main()
