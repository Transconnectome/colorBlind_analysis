"""regularization_comparison.py — 4-way comparison of BEST/Tier2 × Tikh/L_smooth.

Conditions:
  1. BEST + Tikh:   L = 1·L_ccc + 0.5·l_topk + 0.1·Tikh             (current BEST)
  2. BEST + L_smooth: L = 1·L_ccc + 0.5·l_topk + 0.1·L_smooth        (V4-CCC origin reg)
  3. Tier 2 + L_smooth: L = 1·L_ccc + 0.2·L_rdm(V1+V2 SRM) + 0.1·L_smooth (current Tier 2)
  4. Tier 2 + Tikh: L = 1·L_ccc + 0.2·L_rdm(V1+V2 SRM) + 0.1·Tikh    (BEST-style reg)

For each condition × subject:
  - Find argmin in 1326-cell landscape
  - Compute P2a (raw_behav match)
  - Generate 4-col + vuln_hue + landscape figures

Output → results/CANDIDATE/regularization_comparison/
"""
from __future__ import annotations
import json
import sys
import csv
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR))

from fixedW_onlyTest_best_visualize import (
    render_4col, render_vuln_hue, render_landscape,
    l_topk, grid_to_arr,
    THETA_CONF_DEG, TIKH_NORM, HUE_ANGLES, K_TOPK,
)
from phase3_candidate_analysis_v2 import SUB08_ORIGINAL_HC_EQUIV, hc_name, hc_match_score
from fixedW_onlyTest_p2a_ranking import SUB09_ORIGINAL_HC_EQUIV
from old_formula_refit import load_cvd_loco_target

_PHASE2 = _THIS_DIR.parent
SRC_V4CCC = _PHASE2 / 'results' / 'old_formula'
SRC_TIER2 = _PHASE2 / 'results' / 'CANDIDATE' / 'tier2_v4ccc_srm_rdm'
OUT = _PHASE2 / 'results' / 'CANDIDATE' / 'regularization_comparison'
OUT.mkdir(parents=True, exist_ok=True)

LAMBDA_TOPK = 0.5
SUBJECTS = [
    ('08', 'deutan', '#E07B2C', SUB08_ORIGINAL_HC_EQUIV),
    ('09', 'protan', '#2D8E8B', SUB09_ORIGINAL_HC_EQUIV),
]


def forward_old(theta, bs, bc):
    th = np.deg2rad(theta)
    dt = bs * np.cos(th - np.deg2rad(90.0)) + bc * np.cos(th - np.deg2rad(THETA_CONF_DEG))
    return (theta + dt) % 360.0, dt


def p2a_compute(bs, bc, target_map):
    total = 0.0
    exact = 0
    for theta in HUE_ANGLES:
        theta_cvd, _ = forward_old(float(theta), bs, bc)
        pred = hc_name(theta_cvd)
        target = target_map[theta]
        s = hc_match_score(pred, target)
        total += s
        if pred == target:
            exact += 1
    return total / 8.0, exact


def load_v4ccc_cells(sid):
    fn = SRC_V4CCC / f'sub-{sid}_V4_V4ccc_landscape.json'
    ls = json.load(open(fn))
    cells = ls if isinstance(ls, list) else ls.get('cells', ls)
    return cells


def load_tier2_cells(sid):
    fn = SRC_TIER2 / f'sub-{sid}_V4_V4CCC_SRMRDM_landscape.json'
    cells = json.load(open(fn))
    return cells


def compute_loss(cells, vuln_cvd, loss_type, reg_type):
    """Recompute L_combined per cell.

    loss_type: 'BEST' (l_ccc + 0.5·l_topk) or 'TIER2' (l_ccc + 0.2·l_rdm_avg)
    reg_type: 'tikh' or 'lsmooth'
    """
    out = []
    for c in cells:
        l_ccc = c['l_ccc']
        l_smooth = c.get('l_smooth', 0.0)
        tikh = (c['bs']**2 + c['bc']**2) / TIKH_NORM

        if loss_type == 'BEST':
            sim = np.asarray(c['vuln_sim'])
            lt = l_topk(sim, vuln_cvd, K=K_TOPK)
            extra = LAMBDA_TOPK * lt
            extra_label = f'topk={lt:.3f}'
        else:  # TIER2
            lt = None
            extra = 0.2 * c.get('l_rdm_avg', 0.0)
            extra_label = f'rdm_avg={c.get("l_rdm_avg", 0.0):.3f}'

        if reg_type == 'tikh':
            reg = 0.1 * tikh
        else:  # lsmooth
            reg = 0.1 * l_smooth

        L_total = l_ccc + extra + reg
        rec = dict(c)
        rec['_L'] = float(L_total)
        rec['_extra'] = float(extra)
        rec['_reg'] = float(reg)
        rec['_l_topk'] = float(lt) if lt is not None else None
        rec['_tikh'] = float(tikh)
        rec['_lsmooth'] = float(l_smooth)
        out.append(rec)
    return out


def main():
    print(f'OUT: {OUT}')
    summary_rows = []

    conditions = [
        ('BEST', 'tikh', 'V4-CCC + l_topk + 0.1·Tikh', SRC_V4CCC, load_v4ccc_cells),
        ('BEST', 'lsmooth', 'V4-CCC + l_topk + 0.1·L_smooth', SRC_V4CCC, load_v4ccc_cells),
        ('TIER2', 'lsmooth', 'V4-CCC + 0.2·L_rdm + 0.1·L_smooth', SRC_TIER2, load_tier2_cells),
        ('TIER2', 'tikh', 'V4-CCC + 0.2·L_rdm + 0.1·Tikh', SRC_TIER2, load_tier2_cells),
    ]

    for loss_type, reg_type, label, src_dir, loader in conditions:
        print(f'\n=== {loss_type} + {reg_type} === {label}')
        for sid, cvd_type, color, target_map in SUBJECTS:
            cells = loader(sid)
            vuln_cvd = np.array(load_cvd_loco_target(sid, 'V4'))
            cells_L = compute_loss(cells, vuln_cvd, loss_type, reg_type)
            best = min(cells_L, key=lambda c: c['_L'])
            bs, bc = best['bs'], best['bc']
            norm = float(np.hypot(bs, bc))
            P2a, exact = p2a_compute(bs, bc, target_map)
            tag = f"bs{int(bs)}_bc{int(bc):+d}"

            print(f'  sub-{sid}: argmin=({bs:.0f}, {bc:+.0f}) norm={norm:.1f}°  '
                  f'L={best["_L"]:.3f}  P2a={P2a:.3f} ({exact}/8)')

            summary_rows.append({
                'loss_type': loss_type, 'reg_type': reg_type, 'label': label,
                'subject': f'sub-{sid}', 'cvd_type': cvd_type,
                'bs': bs, 'bc': bc, 'norm': round(norm, 1),
                'L_total': round(best['_L'], 4),
                'l_ccc': round(best['l_ccc'], 4),
                'extra_term': round(best['_extra'], 4),
                'reg_term': round(best['_reg'], 4),
                'l_topk_at_min': (round(best['_l_topk'], 4) if best.get('_l_topk') is not None else None),
                'l_smooth_at_min': round(best['_lsmooth'], 4),
                'tikh_at_min': round(best['_tikh'], 4),
                'ccc': round(best.get('ccc', 0), 3),
                'spearman_r': round(best.get('spearman_r', 0), 3),
                'p2a': round(P2a, 3),
                'exact': exact,
            })

            # Visualizations
            prefix = f'{loss_type}{reg_type.upper()}'
            color_for_fn = color
            # 4-col
            render_4col(sid, cvd_type, color_for_fn, bs, bc, target_map, P2a, exact,
                        OUT / f'{prefix}_4col_sub-{sid}_{tag}.png')
            # vuln_hue
            sim = np.array(best['vuln_sim'])
            rho = best.get('spearman_r', 0)
            ccc_v = best.get('ccc', 0)
            render_vuln_hue(sid, cvd_type, color_for_fn, vuln_cvd, sim,
                            bs, bc, rho, ccc_v,
                            P2a, best.get('_l_topk', 0.0) if best.get('_l_topk') else 0.0,
                            OUT / f'{prefix}_vuln_hue_sub-{sid}_{tag}.png')
            # landscape colored by L_total
            for c in cells_L:
                c['_landscape_key'] = c['_L']
            render_landscape(sid, cvd_type, color_for_fn, cells_L, best, '_L',
                             f'L_total ({label})',
                             vmin=None, vmax=None,
                             out_path=OUT / f'{prefix}_landscape_sub-{sid}_{tag}.png')

    # Save CSV
    csv_path = OUT / 'regularization_comparison.csv'
    with open(csv_path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(list(summary_rows[0].keys()))
        for r in summary_rows:
            w.writerow([r[k] for k in summary_rows[0].keys()])
    print(f'\nwrote {csv_path}')

    # Save markdown summary
    md = []
    md.append('# Regularization Comparison — BEST/Tier 2 × Tikh/L_smooth')
    md.append('')
    md.append('## P2a comparison')
    md.append('')
    md.append('| Loss | Reg | Subject | argmin (β_s, β_c) | norm | L_total | **P2a** | exact/8 |')
    md.append('|---|---|---|---|---|---|---|---|')
    for r in summary_rows:
        bsbc = f"({r['bs']:.0f}, {r['bc']:+.0f})"
        md.append(f"| {r['loss_type']} | {r['reg_type']} | {r['subject']} | "
                  f"{bsbc} | {r['norm']:.1f}° | {r['L_total']:.3f} | "
                  f"**{r['p2a']:.3f}** | {r['exact']}/8 |")
    md.append('')
    md.append('## P2a aggregate (min, avg per condition)')
    md.append('')
    md.append('| Loss | Reg | sub-08 P2a | sub-09 P2a | min | avg |')
    md.append('|---|---|---|---|---|---|')
    for lt in ['BEST', 'TIER2']:
        for rt in ['tikh', 'lsmooth']:
            r08 = next((r for r in summary_rows
                        if r['loss_type'] == lt and r['reg_type'] == rt
                        and r['subject'] == 'sub-08'), None)
            r09 = next((r for r in summary_rows
                        if r['loss_type'] == lt and r['reg_type'] == rt
                        and r['subject'] == 'sub-09'), None)
            if r08 and r09:
                p08 = r08['p2a']; p09 = r09['p2a']
                md.append(f"| {lt} | {rt} | {p08:.3f} | {p09:.3f} | "
                          f"{min(p08,p09):.3f} | {(p08+p09)/2:.3f} |")
    md.append('')
    md_path = OUT / 'regularization_comparison_summary.md'
    md_path.write_text('\n'.join(md))
    print(f'wrote {md_path}')


if __name__ == '__main__':
    main()
