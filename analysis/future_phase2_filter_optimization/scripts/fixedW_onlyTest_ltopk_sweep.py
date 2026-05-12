"""fixedW_onlyTest_ltopk_sweep.py — l_topk(V4) weight sweep on V4-CCC landscape.

Loss: L = 1·L_ccc + λ·l_topk(V4, K=3) + 0.1·Tikh
λ sweep ∈ {0, 0.25, 0.5, 1.0, 2.0}

V4-only LOCO policy applied: only V4 LOCO metrics in loss.

Uses cached wretrained V4-CCC landscape (vuln_sim per cell already computed)
in `results/old_formula/sub-{08,09}_V4_V4ccc_landscape.json`. Numpy-only loss
recomputation, no simulator rerun.

Outputs:
  - results/fixedW_onlyTest/ltopk_sweep_results.csv (per λ × subject argmin + P2a)
  - results/fixedW_onlyTest/ltopk_sweep_summary.md
  - results/fixedW_onlyTest/ltopk_sweep_argmin_trace.png (visualization)
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

from phase3_candidate_analysis_v2 import (
    hc_name, hc_match_score, SUB08_ORIGINAL_HC_EQUIV,
)
from fixedW_onlyTest_p2a_ranking import SUB09_ORIGINAL_HC_EQUIV
from old_formula_refit import load_cvd_loco_target

_PHASE2 = _THIS_DIR.parent
SRC = _PHASE2 / 'results' / 'old_formula'
OUT = _PHASE2 / 'results' / 'fixedW_onlyTest'
OUT.mkdir(parents=True, exist_ok=True)

HUE_ANGLES = [0, 45, 90, 135, 180, 225, 270, 315]
THETA_CONF_DEG = 150.0
K_TOPK = 3
TIKH_NORM = 32400.0
LAMBDA_SWEEP = [0.0, 0.25, 0.5, 1.0, 2.0]


def dt_old(theta_deg, bs, bc):
    th = np.deg2rad(theta_deg)
    return (bs * np.cos(th - np.deg2rad(90.0))
            + bc * np.cos(th - np.deg2rad(THETA_CONF_DEG)))


def forward(theta, bs, bc):
    return (theta + dt_old(theta, bs, bc)) % 360.0


def l_topk(vuln_sim, vuln_obs, K=K_TOPK):
    """Jaccard distance between top-K most negative (most vulnerable) indices."""
    sim = np.asarray(vuln_sim)
    obs = np.asarray(vuln_obs)
    top_sim = set(np.argsort(sim)[:K].tolist())  # smallest K (most negative)
    top_obs = set(np.argsort(obs)[:K].tolist())
    inter = len(top_sim & top_obs)
    union = len(top_sim | top_obs)
    return 1.0 - (inter / union)


def p2a_compute(bs, bc, target_map):
    total = 0.0
    exact = 0
    for theta in HUE_ANGLES:
        theta_cvd = forward(float(theta), bs, bc)
        pred = hc_name(theta_cvd)
        target = target_map[theta]
        score = hc_match_score(pred, target)
        total += score
        if pred == target:
            exact += 1
    return total / 8.0, exact


def load_v4ccc_landscape(sid):
    fn = SRC / f'sub-{sid}_V4_V4ccc_landscape.json'
    ls = json.load(open(fn))
    cells = ls if isinstance(ls, list) else ls.get('cells', ls)
    summary_fn = SRC / f'sub-{sid}_V4_V4ccc_summary.json'
    summ = json.load(open(summary_fn))
    return cells, summ


def build_grid(cells, key):
    bs_all = sorted(set(c['bs'] for c in cells))
    bc_all = sorted(set(c['bc'] for c in cells))
    arr = np.full((len(bc_all), len(bs_all)), np.nan)
    bs_idx = {v: i for i, v in enumerate(bs_all)}
    bc_idx = {v: i for i, v in enumerate(bc_all)}
    for c in cells:
        arr[bc_idx[c['bc']], bs_idx[c['bs']]] = c[key]
    return np.array(bs_all), np.array(bc_all), arr


def main():
    SUBJECTS = [
        ('08', 'deutan', '#E07B2C', SUB08_ORIGINAL_HC_EQUIV),
        ('09', 'protan', '#2D8E8B', SUB09_ORIGINAL_HC_EQUIV),
    ]

    all_rows = []
    per_subj_data = {}

    for sid, cvd_type, color, target_map in SUBJECTS:
        print(f'\n=== sub-{sid} {cvd_type} ===')
        cells, summ = load_v4ccc_landscape(sid)
        vuln_cvd = np.array(load_cvd_loco_target(sid, 'V4'))
        print(f'  vuln_cvd top-3 negative indices: {np.argsort(vuln_cvd)[:3].tolist()}')

        # Per cell: compute l_ccc (already there), l_topk fresh, tikh
        for c in cells:
            vuln_sim = np.asarray(c['vuln_sim'])
            c['_l_topk'] = l_topk(vuln_sim, vuln_cvd, K=K_TOPK)
            c['_tikh'] = (c['bs']**2 + c['bc']**2) / TIKH_NORM
            # l_ccc already in c['l_ccc']

        # For each λ, find argmin
        subj_records = []
        n_topk_zero = sum(1 for c in cells if c['_l_topk'] < 1e-9)
        print(f'  cells with l_topk=0: {n_topk_zero} / {len(cells)}')

        for lam in LAMBDA_SWEEP:
            for c in cells:
                c['_L'] = 1.0 * c['l_ccc'] + lam * c['_l_topk'] + 0.1 * c['_tikh']
            best = min(cells, key=lambda c: c['_L'])
            bs, bc = best['bs'], best['bc']
            p2a, exact = p2a_compute(bs, bc, target_map)
            norm = float(np.hypot(bs, bc))
            ccc = best['ccc']
            l_topk_val = best['_l_topk']
            spearman_r = best['spearman_r']
            row = {
                'subject': f'sub-{sid}',
                'cvd_type': cvd_type,
                'lambda_topk': lam,
                'argmin_bs': bs,
                'argmin_bc': bc,
                'norm': norm,
                'l_ccc': best['l_ccc'],
                'l_topk_at_min': l_topk_val,
                'L_total': best['_L'],
                'ccc': ccc,
                'spearman_r': spearman_r,
                'p2a': p2a,
                'exact': exact,
            }
            subj_records.append(row)
            all_rows.append(row)
            print(f'  λ={lam:.2f}: argmin=({bs:.0f}, {bc:+.0f}) norm={norm:.1f}° '
                  f'P2a={p2a:.3f} (exact={exact}/8) l_topk={l_topk_val:.3f} CCC={ccc:.3f}')

        per_subj_data[sid] = {'subject_records': subj_records,
                              'cells': cells, 'vuln_cvd': vuln_cvd,
                              'color': color, 'cvd_type': cvd_type}

    # Save CSV
    csv_path = OUT / 'ltopk_sweep_results.csv'
    with open(csv_path, 'w', newline='') as f:
        w = csv.writer(f)
        if all_rows:
            w.writerow(list(all_rows[0].keys()))
            for r in all_rows:
                w.writerow([r[k] for k in all_rows[0].keys()])
    print(f'\nWrote {csv_path}')

    # Save markdown summary
    md = []
    md.append('# l_topk(V4) Weight Sweep on V4-CCC Landscape')
    md.append('')
    md.append(f'**Loss**: `L = 1·L_ccc + λ·l_topk(V4, K={K_TOPK}) + 0.1·Tikh`')
    md.append(f'**λ values**: {LAMBDA_SWEEP}')
    md.append(f'**Simulator**: wretrained (V4-CCC original)')
    md.append(f'**Policy**: V4 LOCO only (no V1 LOCO)')
    md.append('')
    for sid, cvd_type, color, _ in SUBJECTS:
        md.append(f'## sub-{sid} {cvd_type}')
        md.append('')
        md.append('| λ | argmin (β_s, β_c) | norm | l_topk | CCC | ρ | **P2a** | exact/8 |')
        md.append('|---|---|---|---|---|---|---|---|')
        for r in per_subj_data[sid]['subject_records']:
            md.append(f"| {r['lambda_topk']:.2f} | "
                      f"({r['argmin_bs']:.0f}, {r['argmin_bc']:+.0f}) | "
                      f"{r['norm']:.1f}° | {r['l_topk_at_min']:.3f} | "
                      f"{r['ccc']:.3f} | {r['spearman_r']:.3f} | "
                      f"**{r['p2a']:.3f}** | {r['exact']}/8 |")
        md.append('')
    # Cross-subject summary
    md.append('## Cross-subject (min P2a, avg P2a)')
    md.append('')
    md.append('| λ | sub-08 P2a | sub-09 P2a | min P2a | avg P2a |')
    md.append('|---|---|---|---|---|')
    for lam in LAMBDA_SWEEP:
        p08 = next(r['p2a'] for r in per_subj_data['08']['subject_records'] if r['lambda_topk'] == lam)
        p09 = next(r['p2a'] for r in per_subj_data['09']['subject_records'] if r['lambda_topk'] == lam)
        md.append(f"| {lam:.2f} | {p08:.3f} | {p09:.3f} | {min(p08,p09):.3f} | {(p08+p09)/2:.3f} |")
    md.append('')
    md_path = OUT / 'ltopk_sweep_summary.md'
    md_path.write_text('\n'.join(md))
    print(f'Wrote {md_path}')

    # Visualization: argmin trace + P2a curve
    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    # Panel 1: argmin trajectory in (β_s, β_c) space
    ax = axes[0]
    for sid, cvd_type, color, _ in SUBJECTS:
        recs = per_subj_data[sid]['subject_records']
        bs_arr = [r['argmin_bs'] for r in recs]
        bc_arr = [r['argmin_bc'] for r in recs]
        ax.plot(bs_arr, bc_arr, 'o-', color=color, label=f'sub-{sid} {cvd_type}', ms=6)
        for r, lam in zip(recs, LAMBDA_SWEEP):
            ax.annotate(f'λ={lam}', (r['argmin_bs'], r['argmin_bc']),
                        fontsize=7, alpha=0.7, xytext=(3, 3), textcoords='offset points')
    ax.axhline(0, color='gray', lw=0.5, ls=':')
    ax.axvline(0, color='gray', lw=0.5, ls=':')
    ax.set_xlabel('β_s (°)')
    ax.set_ylabel('β_c (°)')
    ax.set_title('Argmin trajectory in (β_s, β_c) as λ increases')
    ax.legend()
    ax.grid(alpha=0.3)

    # Panel 2: P2a vs λ
    ax = axes[1]
    for sid, cvd_type, color, _ in SUBJECTS:
        recs = per_subj_data[sid]['subject_records']
        lams = [r['lambda_topk'] for r in recs]
        p2as = [r['p2a'] for r in recs]
        ax.plot(lams, p2as, 'o-', color=color, label=f'sub-{sid} {cvd_type}', ms=6)
    ax.set_xlabel('λ (l_topk weight)')
    ax.set_ylabel('P2a')
    ax.set_title('P2a vs λ')
    ax.legend()
    ax.grid(alpha=0.3)
    ax.set_ylim(0, 1)

    # Panel 3: norm vs λ
    ax = axes[2]
    for sid, cvd_type, color, _ in SUBJECTS:
        recs = per_subj_data[sid]['subject_records']
        lams = [r['lambda_topk'] for r in recs]
        norms = [r['norm'] for r in recs]
        ax.plot(lams, norms, 'o-', color=color, label=f'sub-{sid} {cvd_type}', ms=6)
    ax.set_xlabel('λ (l_topk weight)')
    ax.set_ylabel('norm (°)')
    ax.set_title('Argmin norm vs λ')
    ax.legend()
    ax.grid(alpha=0.3)

    plt.tight_layout()
    fig_path = OUT / 'ltopk_sweep_argmin_trace.png'
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'Wrote {fig_path}')


if __name__ == '__main__':
    main()
