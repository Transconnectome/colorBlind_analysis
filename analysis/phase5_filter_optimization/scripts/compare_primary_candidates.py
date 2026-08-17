"""Compare PCA-RDM / SRM-cosine / SRM-disparity at Pipeline 2 PRIMARY candidate cells.

Primary candidates (from PIPELINE_2_CLOSURE.md §5.1, model=2comp):
  - S08-βs-dom    : γ_all + RDM_V1                 → (β_s≈38, β_c≈-10)
  - S08-βc-dom    : γ_OY + RDM_V2 / V3 (2 combos)  → (β_s≈6,  β_c≈-42)
  - S09-βc-rot    : γ_all + RDM_V1, γ_GB + RDM_V1  → (β_s≈2,  β_c≈24)

R+C references (NOT competing candidates, closure §3.5):
  - sub-08 R+C g=2.25 (rc_JND_Lamb, RDM_V1 only)
  - sub-09 R+C g=2.95 (rc_Boehm_low, γ_all + RDM_V1)

For each candidate we (a) identify the closest matching v6 combo label by PCA
(β_s_median, β_c_median), then (b) show that same label's per_model stats
across PCA / COS / DIS outputs.

Usage:
  python compare_primary_candidates.py
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np

RES = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/'
            'Projects/colorBlind_analysis/analysis/'
            'future_phase2_filter_optimization/results/s10_inclusion')

PRIMARY = {
    'sub-08': [
        {'id': 'S08-βs-dom',
         'fit_combos_hint': ['γALL|RDMV1|noLOCO', 'γALL|RDMV1|LOCO'],
         'gt': (38.0, -10.0), 'model': '2comp'},
        {'id': 'S08-βc-dom-V2',
         'fit_combos_hint': ['γOY|RDMV2|noLOCO', 'γOY|RDMV2|LOCO'],
         'gt': (6.0, -42.0), 'model': '2comp'},
        {'id': 'S08-βc-dom-V3',
         'fit_combos_hint': ['γOY|RDMV3|noLOCO', 'γOY|RDMV3|LOCO'],
         'gt': (6.0, -42.0), 'model': '2comp'},
        {'id': 'S08-RC-ref',
         'fit_combos_hint': ['γ_|RDMV1|noLOCO', 'γ_|RDMV1|LOCO'],
         'gt': (2.25,), 'model': 'rc_JND_Lamb'},
    ],
    'sub-09': [
        {'id': 'S09-βc-rot-ALL',
         'fit_combos_hint': ['γALL|RDMV1|noLOCO', 'γALL|RDMV1|LOCO'],
         'gt': (2.0, 24.0), 'model': '2comp'},
        {'id': 'S09-βc-rot-GB',
         'fit_combos_hint': ['γGB|RDMV1|noLOCO', 'γGB|RDMV1|LOCO'],
         'gt': (2.0, 24.0), 'model': '2comp'},
        {'id': 'S09-RC-ref',
         'fit_combos_hint': ['γALL|RDMV1|noLOCO', 'γALL|RDMV1|LOCO'],
         'gt': (2.95,), 'model': 'rc_Boehm_low'},
    ],
}


def load(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text())['summary']


def fmt(v, prec=3):
    if v is None:
        return '   nan'
    return f'{v:7.{prec}f}'


def cell_row(pm, model):
    if pm is None:
        return None
    ps = pm.get('param_summary', {})
    if model.startswith('rc'):
        param = f"g={fmt(ps.get('g_median'),2)} (iqr={fmt(ps.get('g_iqr'),2)})"
    else:
        param = (f"({fmt(ps.get('bs_median'),1)},"
                  f"{fmt(ps.get('bc_median'),1)})  "
                  f"iqr({fmt(ps.get('bs_iqr'),1)},{fmt(ps.get('bc_iqr'),1)})")
    return {
        'param': param,
        'test_loss': pm.get('test_loss_median'),
        'test_iqr': pm.get('test_loss_iqr'),
        'train_loss': pm.get('train_loss_median'),
        'test_focal': pm.get('test_focal_median'),
        'test_agg': pm.get('test_agg_median'),
        'test_V1_RDM': pm.get('test_V1_RDM_median'),
        'bdy': pm.get('boundary_rate'),
        'n': pm.get('n'),
    }


def pick_best_match(summaries: dict, hints: list, gt: tuple, model: str):
    """Return the combo label that best matches the GT param across hints.

    Best = the hint combo whose PCA median (β_s, β_c) or g is closest to gt.
    """
    pca = summaries.get('PCA')
    if pca is None:
        return hints[0]
    best = (1e18, hints[0])
    for h in hints:
        if h not in pca:
            continue
        pm = pca[h]['per_model'].get(model)
        if not pm:
            continue
        ps = pm.get('param_summary', {})
        if model.startswith('rc'):
            g = ps.get('g_median')
            if g is None:
                continue
            d = (g - gt[0]) ** 2
        else:
            bs = ps.get('bs_median'); bc = ps.get('bc_median')
            if bs is None or bc is None:
                continue
            d = (bs - gt[0]) ** 2 + (bc - gt[1]) ** 2
        if d < best[0]:
            best = (d, h)
    return best[1]


def main():
    for subject, cands in PRIMARY.items():
        pca = load(RES / f's10b_v6_pca_rdm_results_{subject}.json')
        cos = load(RES / f's10b_v6_srm_rdm_results_{subject}.json')
        dis = load(RES / f's10b_v6_srm_disparity_results_{subject}.json')
        summaries = {'PCA': pca, 'COS': cos, 'DIS': dis}

        print('\n' + '=' * 140)
        print(f'{subject} — Pipeline 2 PRIMARY candidates: PCA-RDM vs SRM-cosine vs SRM-disparity')
        print('=' * 140)

        for c in cands:
            label = pick_best_match(summaries, c['fit_combos_hint'],
                                     c['gt'], c['model'])
            gt_str = (f"g={c['gt'][0]}" if c['model'].startswith('rc')
                       else f"(β_s={c['gt'][0]:+.0f}, β_c={c['gt'][1]:+.0f})")
            print(f"\n>>> {c['id']:18s} | model={c['model']:14s} | "
                  f"closure GT={gt_str:24s} | combo={label}")
            hdr = (f"  {'method':5s}  {'param':46s}  "
                   f"{'test':>10s}±{'iqr':<7s}  {'train':>10s}  "
                   f"{'focal':>8s}  {'agg':>8s}  {'V1_RDM':>8s}  "
                   f"{'bdy':>5s}  {'n':>4s}")
            print(hdr)
            print('  ' + '-' * (len(hdr) - 2))
            for tag in ('PCA', 'COS', 'DIS'):
                s = summaries[tag]
                if s is None or label not in s:
                    print(f"  {tag}:  (no data)")
                    continue
                pm = s[label]['per_model'].get(c['model'])
                row = cell_row(pm, c['model'])
                if row is None:
                    print(f"  {tag}:  (model={c['model']} missing)")
                    continue
                print(f"  {tag:5s}  {row['param']:46s}  "
                      f"{fmt(row['test_loss']):>10s}±{fmt(row['test_iqr']):<7s}  "
                      f"{fmt(row['train_loss']):>10s}  "
                      f"{fmt(row['test_focal']):>8s}  "
                      f"{fmt(row['test_agg']):>8s}  "
                      f"{fmt(row['test_V1_RDM']):>8s}  "
                      f"{(fmt(row['bdy'],2) if row['bdy'] is not None else ' nan '):>5s}  "
                      f"{str(row['n']) if row['n'] is not None else 'nan':>4s}")


if __name__ == '__main__':
    main()
