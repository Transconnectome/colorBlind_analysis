#!/usr/bin/env python3
"""
summarize_cross_family.py — Gen-4 cross-family specificity aggregator.

Reads the native Stage-2/Stage-3 outputs (`results/step2_finetune_l3`,
`results/step3_neural`) together with the cross-family override runs
(`results/cross_family/{l3,neural}_{protan,deutan}`) and builds a
(subject × family) matrix of:

    - Stage-2 label_perm_p    (joint V1+V2 L₃ exact 8!)
    - Stage-2 Δλ_V1, Δλ_V2    (best fit)
    - Stage-3 per-ROI ρ_fit, Δρ, label_perm_p
    - Stage-3 hV4 (held-out) label_perm_p
    - Stage-3 baseline_improvement_p (secondary)

Outputs:
    results/cross_family/cross_family_stage2.csv
    results/cross_family/cross_family_stage3_per_roi.csv
    results/cross_family/SPECIFICITY.md
    results/cross_family/SPECIFICITY.json   (raw cells for downstream use)

Conventions:
    - "native" family is always CVD_TYPE[subject] (08→deutan, 09→protan,
      10→normal). It is sourced from the top-level step2/step3 dirs, NOT
      the cross-family override dirs, so the diagonal cell is a genuine
      replicate-free reference.
    - "override protan"/"override deutan" cells come from
      `results/cross_family/{l3,neural}_{protan,deutan}`.
    - Models reported: machado_1way, machado_alpha_free (cone_3way is
      family-agnostic so is excluded from the specificity table).

This script does NOT mutate any upstream files — it only reads JSON and
writes CSV/MD/JSON summaries.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
PIPE_DIR = SCRIPT_DIR.parent
RESULTS_DIR = PIPE_DIR / 'results'

NATIVE_STEP2_DIR = RESULTS_DIR / 'step2_finetune_l3'
NATIVE_STEP3_DIR = RESULTS_DIR / 'step3_neural'
CROSS_DIR = RESULTS_DIR / 'cross_family'
OUT_DIR = CROSS_DIR

CVD_IDS = ['08', '09', '10']
CVD_TYPE = {'08': 'deutan', '09': 'protan', '10': 'normal'}
FAMILIES = ['protan', 'deutan']
MODELS = ['machado_1way', 'machado_alpha_free']
ROIS = ['V1', 'V2', 'hV4']


def _load_stage2(subj: str, model: str, family: str) -> Optional[Dict]:
    """Return the Stage-2 json for the requested (subject, model, family).

    ``family='native'`` → top-level step2_finetune_l3 dir.
    Otherwise → cross_family/l3_{family}/.
    """
    if family == 'native':
        path = NATIVE_STEP2_DIR / f'sub-{subj}_{model}.json'
    else:
        path = CROSS_DIR / f'l3_{family}' / f'sub-{subj}_{model}.json'
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def _load_stage3(subj: str, model: str, family: str) -> Optional[Dict]:
    """Load the Stage-3 NEURAL json for the requested cell."""
    if family == 'native':
        path = NATIVE_STEP3_DIR / f'sub-{subj}_{model}.json'
    else:
        path = CROSS_DIR / f'neural_{family}' / f'sub-{subj}_{model}.json'
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def _stage2_row(subj: str, model: str, family: str) -> Dict:
    doc = _load_stage2(subj, model, family)
    if doc is None:
        return {
            'subject': subj,
            'cvd_native': CVD_TYPE[subj],
            'family': family,
            'model': model,
            'delta_v1_nm': None,
            'delta_v2_nm': None,
            'l3': None,
            'l1': None,
            'label_perm_p': None,
            'baseline_improvement_p': None,
            'available': False,
        }
    best = doc['best']
    null = doc['permutation_null']
    return {
        'subject': subj,
        'cvd_native': CVD_TYPE[subj],
        'family': family,
        'model': model,
        'delta_v1_nm': float(best['delta_v1_nm']),
        'delta_v2_nm': float(best['delta_v2_nm']),
        'l3': float(best['l3']),
        'l1': float(best['l1']),
        'label_perm_p': float(null['label_perm_p']),
        'baseline_improvement_p': float(
            null.get('baseline_improvement_p', float('nan'))),
        'available': True,
    }


def _stage3_rows(subj: str, model: str, family: str) -> List[Dict]:
    doc = _load_stage3(subj, model, family)
    rows: List[Dict] = []
    if doc is None:
        for roi in ROIS:
            rows.append({
                'subject': subj,
                'cvd_native': CVD_TYPE[subj],
                'family': family,
                'model': model,
                'roi': roi,
                'delta_lambda_nm': None,
                'rho_fit': None,
                'rho_baseline': None,
                'delta_rho_obs': None,
                'label_perm_p': None,
                'baseline_improvement_p': None,
                'available': False,
            })
        return rows
    rois = doc.get('rois', {})
    for roi in ROIS:
        r = rois.get(roi)
        if r is None:
            rows.append({
                'subject': subj,
                'cvd_native': CVD_TYPE[subj],
                'family': family,
                'model': model,
                'roi': roi,
                'delta_lambda_nm': None,
                'rho_fit': None,
                'rho_baseline': None,
                'delta_rho_obs': None,
                'label_perm_p': None,
                'baseline_improvement_p': None,
                'available': False,
            })
            continue
        rows.append({
            'subject': subj,
            'cvd_native': CVD_TYPE[subj],
            'family': family,
            'model': model,
            'roi': roi,
            'delta_lambda_nm': float(r['delta_lambda_nm']),
            'rho_fit': float(r['rho_fit']),
            'rho_baseline': float(r['rho_baseline']),
            'delta_rho_obs': float(r['delta_rho_obs']),
            'label_perm_p': float(r['label_perm_p']),
            'baseline_improvement_p': float(r['baseline_improvement_p']),
            'available': True,
        })
    return rows


# ============================================================================
# CSV writers (no pandas dependency — keep local runs lean)
# ============================================================================

def _write_csv(path: Path, rows: List[Dict], columns: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        f.write(','.join(columns) + '\n')
        for row in rows:
            vals = []
            for c in columns:
                v = row.get(c)
                if v is None:
                    vals.append('')
                elif isinstance(v, float):
                    vals.append(f'{v:.6f}')
                else:
                    vals.append(str(v))
            f.write(','.join(vals) + '\n')


# ============================================================================
# Markdown report
# ============================================================================

def _fmt_p(p: Optional[float]) -> str:
    if p is None:
        return '—'
    tag = '*' if p < 0.05 else ''
    return f'{p:.3f}{tag}'


def _fmt_num(v: Optional[float], fmt: str = '+.3f') -> str:
    if v is None:
        return '—'
    return format(v, fmt)


def _stage2_table(model: str, stage2_rows: List[Dict]) -> str:
    # Lookup table keyed by (subject, family)
    lookup = {(r['subject'], r['family']): r for r in stage2_rows
              if r['model'] == model}
    lines = [
        f'#### {model}',
        '',
        '| Subject | Native | Fit family | Δλ_V1 | Δλ_V2 | L₁ | L₃ | label_p | improv_p |',
        '|---|---|---|---|---|---|---|---|---|',
    ]
    for subj in CVD_IDS:
        native = CVD_TYPE[subj]
        for fam in ['native', 'protan', 'deutan']:
            r = lookup.get((subj, fam))
            if r is None or not r.get('available'):
                continue
            fam_tag = fam
            if fam == 'native':
                fam_tag = f'{native} ← native'
            lines.append(
                f'| sub-{subj} | {native} | {fam_tag} | '
                f'{_fmt_num(r["delta_v1_nm"], "5.2f")} | '
                f'{_fmt_num(r["delta_v2_nm"], "5.2f")} | '
                f'{_fmt_num(r["l1"], "+.4f")} | '
                f'{_fmt_num(r["l3"], "+.4f")} | '
                f'{_fmt_p(r["label_perm_p"])} | '
                f'{_fmt_p(r["baseline_improvement_p"])} |'
            )
        lines.append('| | | | | | | | | |')
    return '\n'.join(lines)


def _stage3_table(model: str, stage3_rows: List[Dict]) -> str:
    # Key on (subject, family, roi)
    lookup = {(r['subject'], r['family'], r['roi']): r
              for r in stage3_rows if r['model'] == model}
    lines = [
        f'#### {model}',
        '',
        '| Subject | Native | Fit family | ROI | Δλ | ρ_fit | ρ_base | Δρ | label_p |',
        '|---|---|---|---|---|---|---|---|---|',
    ]
    for subj in CVD_IDS:
        native = CVD_TYPE[subj]
        for fam in ['native', 'protan', 'deutan']:
            for roi in ROIS:
                r = lookup.get((subj, fam, roi))
                if r is None or not r.get('available'):
                    continue
                fam_tag = fam if fam != 'native' else f'{native} ← native'
                lines.append(
                    f'| sub-{subj} | {native} | {fam_tag} | {roi} | '
                    f'{_fmt_num(r["delta_lambda_nm"], "5.2f")} | '
                    f'{_fmt_num(r["rho_fit"])} | '
                    f'{_fmt_num(r["rho_baseline"])} | '
                    f'{_fmt_num(r["delta_rho_obs"])} | '
                    f'{_fmt_p(r["label_perm_p"])} |'
                )
        lines.append('| | | | | | | | | |')
    return '\n'.join(lines)


def _write_specificity_md(stage2_rows: List[Dict],
                          stage3_rows: List[Dict],
                          out_path: Path) -> None:
    buf: List[str] = []
    buf.append('# Cross-Family Specificity Report')
    buf.append('')
    buf.append('_Generated by `summarize_cross_family.py`._')
    buf.append('')
    buf.append('## Design')
    buf.append('')
    buf.append(
        'Each CVD subject is fit with both the `protan` and `deutan` '
        'Machado templates via the new `--cvd_type_override` flag, alongside '
        'its native family. A clean specificity pattern would show:')
    buf.append('')
    buf.append('- **sub-08 (deutan)**: deutan-fit passes, protan-fit fails.')
    buf.append('- **sub-09 (protan)**: protan-fit passes, deutan-fit fails.')
    buf.append('- **sub-10 (normal)**: both null (correct control).')
    buf.append('')
    buf.append(
        'All Stage-2 label permutation nulls are exact 8! (40320). Stage-3 '
        'NEURAL tests use exact 8! Spearman permutation on held-out hV4 '
        'plus V1 and V2 transfer checks.')
    buf.append('')

    buf.append('## Stage 2 — joint V1+V2 L₃ label permutation')
    buf.append('')
    for model in MODELS:
        buf.append(_stage2_table(model, stage2_rows))
        buf.append('')

    buf.append('## Stage 3 — per-ROI neural transfer (exact 8!)')
    buf.append('')
    for model in MODELS:
        buf.append(_stage3_table(model, stage3_rows))
        buf.append('')

    # Headline summary
    def _lookup_p(s2, model: str, subj: str, family: str) -> Optional[float]:
        for r in s2:
            if (r['model'] == model and r['subject'] == subj
                    and r['family'] == family):
                return r.get('label_perm_p')
        return None

    buf.append('## Headline specificity matrix — Stage 2 label_perm_p')
    buf.append('')
    for model in MODELS:
        buf.append(f'### {model}')
        buf.append('')
        buf.append('| Subject | native | protan override | deutan override |')
        buf.append('|---|---|---|---|')
        for subj in CVD_IDS:
            nat = CVD_TYPE[subj]
            native_p = _lookup_p(stage2_rows, model, subj, 'native')
            protan_p = _lookup_p(stage2_rows, model, subj, 'protan')
            deutan_p = _lookup_p(stage2_rows, model, subj, 'deutan')
            buf.append(
                f'| sub-{subj} ({nat}) | '
                f'{_fmt_p(native_p)} | '
                f'{_fmt_p(protan_p)} | '
                f'{_fmt_p(deutan_p)} |'
            )
        buf.append('')

    # Narrative interpretation
    buf.append('## Interpretation')
    buf.append('')
    buf.append(
        'See `results/figures/diagnostic_protan_vs_deutan/DIAGNOSIS.md` for the five-'
        'axis structural analysis that motivated this run. Key take-aways to '
        'cross-check against the tables above:')
    buf.append('')
    buf.append(
        '1. **sub-08 deutan**: if Δλ_V1=Δλ_V2=0 under both families, '
        'the Machado 1-way model is **shape-incompatible** with sub-08\'s '
        'ΔRDM in either direction — consistent with the diagnostic finding '
        'that sub-08 has the largest ‖ΔRDM‖ and strongest cross-ROI '
        'coherence, but the pattern does not align with the Machado '
        '1-parameter prescription.')
    buf.append('')
    buf.append(
        '2. **sub-09 protan**: check whether the deutan-override cell is '
        'also significant. If it is (e.g. p < 0.10) the two families have '
        'overlapping 8-colour ΔRDM signatures and the native fit is not '
        'uniquely protan-specific.')
    buf.append('')
    buf.append(
        '3. **sub-10 normal**: both override cells should be non-significant '
        'and show Δρ ≤ 0 in Stage 3. Any false positive here warns of '
        'Machado-family baseline over-fitting.')
    buf.append('')
    buf.append(
        '4. **Stage 3 hV4 (held out)**: an override cell that passes Stage 2 '
        '(shape-fit) but fails Stage 3 hV4 confirms the shape-fit ≠ neural-'
        'fit dissociation highlighted in the diagnostic report.')
    buf.append('')

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w') as f:
        f.write('\n'.join(buf))
    print(f'SPECIFICITY.md → {out_path}')


# ============================================================================
# Main
# ============================================================================

def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Stage 2 aggregation
    stage2_rows: List[Dict] = []
    for model in MODELS:
        for subj in CVD_IDS:
            for family in ['native'] + FAMILIES:
                stage2_rows.append(_stage2_row(subj, model, family))

    stage2_columns = [
        'subject', 'cvd_native', 'family', 'model',
        'delta_v1_nm', 'delta_v2_nm', 'l3', 'l1',
        'label_perm_p', 'baseline_improvement_p', 'available',
    ]
    _write_csv(OUT_DIR / 'cross_family_stage2.csv',
               stage2_rows, stage2_columns)
    print(f'cross_family_stage2.csv → {OUT_DIR / "cross_family_stage2.csv"}')

    # Stage 3 aggregation
    stage3_rows: List[Dict] = []
    for model in MODELS:
        for subj in CVD_IDS:
            for family in ['native'] + FAMILIES:
                stage3_rows.extend(_stage3_rows(subj, model, family))

    stage3_columns = [
        'subject', 'cvd_native', 'family', 'model', 'roi',
        'delta_lambda_nm', 'rho_fit', 'rho_baseline', 'delta_rho_obs',
        'label_perm_p', 'baseline_improvement_p', 'available',
    ]
    _write_csv(OUT_DIR / 'cross_family_stage3_per_roi.csv',
               stage3_rows, stage3_columns)
    print(f'cross_family_stage3_per_roi.csv → '
          f'{OUT_DIR / "cross_family_stage3_per_roi.csv"}')

    # JSON snapshot for downstream aggregation
    with open(OUT_DIR / 'SPECIFICITY.json', 'w') as f:
        json.dump({'stage2': stage2_rows, 'stage3': stage3_rows},
                  f, indent=2)
    print(f'SPECIFICITY.json → {OUT_DIR / "SPECIFICITY.json"}')

    # Markdown report
    _write_specificity_md(stage2_rows, stage3_rows,
                          OUT_DIR / 'SPECIFICITY.md')


if __name__ == '__main__':
    main()
