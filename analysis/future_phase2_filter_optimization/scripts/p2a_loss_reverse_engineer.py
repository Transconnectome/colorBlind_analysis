"""p2a_loss_reverse_engineer.py — 데이터에서 P2a-max를 발견하는 loss 도출.

Goal: 어떤 loss formulation이 P2a-max (β_s=24, β_c=-20) 근처를 argmin으로 만드는가?

Method (4 steps):
  1. cached landscape에서 (L_ccc, l_topk, Tikh) + 직접 P2a 계산 → per-cell matrix
  2. Component vs P2a correlation 분석:
     - Pearson r(L_ccc, P2a), r(l_topk, P2a), r(Tikh, P2a)
     - Spearman ρ도 같이 (rank-based)
  3. P2a-max cell 근처에서 각 component 값 vs grid 통계 (where they sit)
  4. Weight 조합 sweep: 각 (λ_ccc, λ_topk, λ_tikh) 조합에서 argmin이 P2a-max에 얼마나 가까운가
     - score = -dist(argmin, P2a_max_cell) + P2a_at_argmin
  5. Landscape 4-panel viz: L_ccc / l_topk / Tikh / P2a

V4 LOCO only policy 준수 — V1/V2 LOCO 안 씀. Cached landscape의 components 그대로 활용.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import pearsonr, spearmanr

_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR))

from phase3_candidate_analysis_v2 import (
    hc_name, hc_match_score, SUB08_ORIGINAL_HC_EQUIV,
)
from fixedW_onlyTest_p2a_ranking import SUB09_ORIGINAL_HC_EQUIV

OUT = _THIS_DIR.parent / 'results' / 'p2a_loss_reverse'
OUT.mkdir(parents=True, exist_ok=True)

HUE_8 = [0, 45, 90, 135, 180, 225, 270, 315]


def forward(theta, bs, bc, phi_c, phi_s=90.0):
    return (theta + bs * np.cos(np.radians(theta - phi_s))
                  + bc * np.cos(np.radians(theta - phi_c))) % 360.0


def p2a_at(bs, bc, phi_c, target_map):
    total = 0.0; exact = 0
    for theta in HUE_8:
        theta_cvd = forward(float(theta), bs, bc, phi_c)
        pred = hc_name(theta_cvd)
        target = target_map[theta]
        total += hc_match_score(pred, target)
        if pred == target: exact += 1
    return total / 8.0, exact


def analyze_one_landscape(path: Path, target_map, subject_id: str, axis_label: str):
    with open(path) as f:
        d = json.load(f)
    theta_conf = d['theta_conf']
    cells = d['cells']

    # Build matrix
    rows = []
    for c in cells:
        bs, bc = c['bs'], c['bc']
        l_ccc = c['l_ccc']
        l_topk = c['l_topk']
        tikh = c['tikh']
        ccc = c.get('ccc', 1 - 2*l_ccc)
        p2a, exact = p2a_at(bs, bc, theta_conf, target_map)
        rows.append({'bs': bs, 'bc': bc, 'l_ccc': l_ccc, 'l_topk': l_topk,
                     'tikh': tikh, 'ccc': ccc, 'p2a': p2a, 'exact': exact})

    bs_arr = np.array([r['bs'] for r in rows])
    bc_arr = np.array([r['bc'] for r in rows])
    L_ccc = np.array([r['l_ccc'] for r in rows])
    L_topk = np.array([r['l_topk'] for r in rows])
    Tikh = np.array([r['tikh'] for r in rows])
    P2a = np.array([r['p2a'] for r in rows])
    CCC = np.array([r['ccc'] for r in rows])

    p2a_max_idx = np.argmax(P2a)
    p2a_max = rows[p2a_max_idx]

    print(f'\n=== sub-{subject_id} axis={axis_label} (θ_conf={theta_conf}°) ===')
    print(f'  Grid: {len(rows)} cells')
    print(f'  P2a-max cell:  bs={p2a_max["bs"]:.0f}, bc={p2a_max["bc"]:+.0f}  '
          f'P2a={p2a_max["p2a"]:.3f} ({p2a_max["exact"]}/8)')
    print(f'  At P2a-max:    L_ccc={p2a_max["l_ccc"]:.3f}  '
          f'l_topk={p2a_max["l_topk"]:.3f}  Tikh={p2a_max["tikh"]:.4f}  CCC={p2a_max["ccc"]:+.3f}')
    print(f'  Grid stats:    L_ccc∈[{L_ccc.min():.3f},{L_ccc.max():.3f}]  '
          f'l_topk∈[{L_topk.min():.2f},{L_topk.max():.2f}]  '
          f'Tikh∈[{Tikh.min():.4f},{Tikh.max():.4f}]')

    # Correlations: component ↔ P2a
    print('\n  Component ↔ P2a correlations (negative = aligned w/ P2a, since low-loss = high-P2a is desired):')
    for name, x in [('L_ccc', L_ccc), ('l_topk', L_topk), ('Tikh', Tikh), ('CCC', CCC)]:
        if np.std(x) < 1e-10:
            print(f'    {name:>8s}: degenerate (no variance)')
            continue
        r_p, _ = pearsonr(x, P2a)
        r_s, _ = spearmanr(x, P2a)
        align = "ALIGNED w/ P2a" if (name != 'CCC' and r_p < -0.1) else \
                "ALIGNED w/ P2a" if (name == 'CCC' and r_p > 0.1) else \
                "ANTI-aligned" if (name != 'CCC' and r_p > 0.1) else \
                "ANTI-aligned" if (name == 'CCC' and r_p < -0.1) else "weak"
        print(f'    {name:>8s}: Pearson={r_p:+.3f}  Spearman={r_s:+.3f}   [{align}]')

    # Weight sweep: which (λ_ccc, λ_topk, λ_tikh) brings argmin close to P2a-max?
    print('\n  Weight sweep — search loss config that places argmin at/near P2a-max:')
    print('  (negative λ allowed for L_ccc/l_topk to flip direction — interpretation: anti-fit)')
    best_dist = np.inf
    best_combo = None
    # Search grid
    lambdas_ccc = [-2.0, -1.0, -0.5, 0.0, 0.5, 1.0, 2.0]
    lambdas_topk = [-1.0, -0.5, 0.0, 0.5, 1.0, 2.0]
    lambdas_tikh = [0.0, 0.1, 0.5, 1.0, 2.0, 5.0]
    p2a_max_pos = np.array([p2a_max['bs'], p2a_max['bc']])
    results_combos = []
    for lc in lambdas_ccc:
        for lt in lambdas_topk:
            for lk in lambdas_tikh:
                L = lc*L_ccc + lt*L_topk + lk*Tikh
                if not np.all(np.isfinite(L)):
                    continue
                amin = np.argmin(L)
                am_pos = np.array([rows[amin]['bs'], rows[amin]['bc']])
                dist = np.linalg.norm(am_pos - p2a_max_pos)
                argmin_p2a = rows[amin]['p2a']
                # Score: prioritize argmin reaching P2a-max with high P2a
                score = -dist + 50 * argmin_p2a
                results_combos.append({
                    'lc': lc, 'lt': lt, 'lk': lk, 'dist': dist,
                    'argmin_bs': rows[amin]['bs'], 'argmin_bc': rows[amin]['bc'],
                    'argmin_p2a': argmin_p2a, 'score': score,
                })
                if dist < best_dist:
                    best_dist = dist; best_combo = (lc, lt, lk, rows[amin])

    # Top-10 combos
    results_combos.sort(key=lambda r: -r['score'])
    print(f'\n  Top-10 (λ_ccc, λ_topk, λ_tikh) by [-dist + 50·argmin_P2a]:')
    print(f'    {"λ_ccc":>6s} {"λ_topk":>7s} {"λ_tikh":>7s}  '
          f'{"argmin":<14s}  {"dist":>5s}  {"P2a":>5s}')
    for r in results_combos[:10]:
        print(f'    {r["lc"]:>+6.1f} {r["lt"]:>+7.1f} {r["lk"]:>+7.1f}  '
              f'({r["argmin_bs"]:>2.0f},{r["argmin_bc"]:+3.0f})       '
              f'{r["dist"]:>5.1f}  {r["argmin_p2a"]:>5.3f}')

    # Visualize: 4-panel (L_ccc, l_topk, Tikh, P2a)
    if len(set(bs_arr.tolist())) > 1 and len(set(bc_arr.tolist())) > 1:
        bs_unique = sorted(set(bs_arr.tolist()))
        bc_unique = sorted(set(bc_arr.tolist()))
        nbs = len(bs_unique); nbc = len(bc_unique)
        idx_bs = {v: i for i, v in enumerate(bs_unique)}
        idx_bc = {v: i for i, v in enumerate(bc_unique)}
        def reshape(arr):
            M = np.full((nbs, nbc), np.nan)
            for k, r in enumerate(rows):
                M[idx_bs[r['bs']], idx_bc[r['bc']]] = arr[k]
            return M
        fig, axs = plt.subplots(1, 4, figsize=(20, 5.5), dpi=130)
        items = [('L_ccc', L_ccc, 'viridis_r'),
                 ('l_topk', L_topk, 'viridis_r'),
                 ('Tikh', Tikh, 'viridis_r'),
                 ('P2a (target)', P2a, 'plasma')]
        for ax, (name, arr, cmap) in zip(axs, items):
            M = reshape(arr)
            im = ax.imshow(M, origin='lower', aspect='auto', cmap=cmap,
                           extent=(min(bc_unique)-1, max(bc_unique)+1,
                                   min(bs_unique)-1, max(bs_unique)+1))
            ax.set_title(f'{name}', fontsize=11, fontweight='bold')
            ax.set_xlabel('β_c'); ax.set_ylabel('β_s')
            # Mark P2a-max
            ax.plot(p2a_max['bc'], p2a_max['bs'], '*', color='red',
                    markersize=18, markeredgecolor='white', label='P2a-max')
            # Mark current L_combined argmin (using 1·L_ccc + 0.5·L_topk + 0.1·Tikh)
            L_cur = 1.0*L_ccc + 0.5*L_topk + 0.1*Tikh
            amin = np.argmin(L_cur)
            ax.plot(rows[amin]['bc'], rows[amin]['bs'], 'o', color='cyan',
                    markersize=10, markeredgecolor='white', label='L_combined argmin')
            plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
            ax.legend(loc='upper left', fontsize=8)
        fig.suptitle(f'sub-{subject_id} axis={axis_label} (θ_conf={theta_conf}°)  '
                     f'P2a-max=(bs={p2a_max["bs"]:.0f}, bc={p2a_max["bc"]:+.0f}) P2a={p2a_max["p2a"]:.3f}',
                     fontsize=12, fontweight='bold')
        plt.tight_layout()
        out_path = OUT / f'landscape4_sub-{subject_id}_{axis_label}.png'
        plt.savefig(out_path, dpi=130, bbox_inches='tight')
        plt.savefig(str(out_path).replace('.png', '.pdf'), bbox_inches='tight')
        plt.close()
        print(f'  wrote {out_path.name}')

    return {
        'subject': subject_id, 'axis': axis_label, 'theta_conf': theta_conf,
        'p2a_max': p2a_max,
        'top_combos': results_combos[:10],
    }


def main():
    landscapes = [
        # (sid, axis_label, path)
        ('08', 'Stockman150',  'results/axis_3way/sub-08_V4_Stockman150_landscape.json'),
        ('08', 'CIELab175.7',  'results/axis_3way/sub-08_V4_CIELab175p7_landscape.json'),
        ('09', 'Stockman16',   'results/axis_3way/sub-09_V4_Stockman16_landscape.json'),
        ('09', 'CIELab11.8',   'results/axis_3way/sub-09_V4_CIELab11p8_landscape.json'),
        ('09', 'Stockman16ext','results/axis_3way/sub-09_V4_Stockman16ext_landscape.json'),
        ('09', 'CIELab11.8ext','results/axis_3way/sub-09_V4_CIELab11p8ext_landscape.json'),
        ('09', 'axis150_fine', 'results/axis_3way/sub-09_V4_axis150_fine_landscape.json'),
    ]
    target_maps = {'08': SUB08_ORIGINAL_HC_EQUIV, '09': SUB09_ORIGINAL_HC_EQUIV}

    all_results = []
    for sid, axis, p in landscapes:
        path = Path(p)
        if not path.exists():
            print(f'SKIP {p}'); continue
        r = analyze_one_landscape(path, target_maps[sid], sid, axis)
        all_results.append(r)

    # Save summary
    serial = []
    for r in all_results:
        serial.append({
            'subject': r['subject'], 'axis': r['axis'],
            'theta_conf': r['theta_conf'],
            'p2a_max': r['p2a_max'],
            'top_combos': r['top_combos'],
        })
    with open(OUT / 'p2a_loss_reverse_summary.json', 'w') as f:
        json.dump(serial, f, indent=2)
    print(f'\nWrote {OUT / "p2a_loss_reverse_summary.json"}')


if __name__ == '__main__':
    main()
