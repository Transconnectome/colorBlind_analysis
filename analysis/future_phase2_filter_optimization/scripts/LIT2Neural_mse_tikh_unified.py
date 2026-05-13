"""LIT2Neural_mse_tikh_unified.py — Neural-primary unified loss using L_mse + Tikh.

Hypothesis (user 2026-05-13):
  Sub-08 vuln_obs has weak 2-comp structure (LSQ projection r=0.09) and localized
  distortions. Correlation-based losses (CCC, Pearson, Spearman, RDM cos) are
  underdetermined for sub-08. Amplitude/MSE + Tikh regularization may yield a more
  robust unified anchor:

    L(β_s, β_c | subject) = L_mse(vuln_sim, vuln_obs) + λ · Tikh(β_s, β_c)

  Properties:
    - Fully neural-primary: only V4 vuln_obs + L2 amplitude penalty
    - No anchor extraction from separate fit (no "phase_a" or "L_combined" boot)
    - No literature constants
    - Same formulation across subjects

  Test λ ∈ {0.1, 0.25, 0.5, 1.0, 2.0} on both subjects.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR))

from phase3_candidate_analysis_v2 import hc_name, hc_match_score, SUB08_ORIGINAL_HC_EQUIV
from fixedW_onlyTest_p2a_ranking import SUB09_ORIGINAL_HC_EQUIV

OUT = _THIS_DIR.parent / 'results'
PREFIX = 'LIT2Neural_msetikh_'

HUE_8 = np.array([0, 45, 90, 135, 180, 225, 270, 315], dtype=float)
TIKH_NORM = 32400.0   # (180°)²

CASES = [
    {
        'sid': '08', 'family': 'deutan', 'axis': 150.0, 'color': '#E07B2C',
        'landscape': 'results/axis_3way/sub-08_V4_Stockman150_landscape.json',
        'target_map': SUB08_ORIGINAL_HC_EQUIV,
        'p2a_max': (26.0, 34.0),
        'phase_a': (38.0, -14.0),
        'bayes': (22.0, 18.0),
    },
    {
        'sid': '09', 'family': 'protan', 'axis': 16.0, 'color': '#2D8E8B',
        'landscape': 'results/axis_3way/sub-09_V4_Stockman16ext_landscape.json',
        'target_map': SUB09_ORIGINAL_HC_EQUIV,
        'p2a_max': (24.0, -20.0),
        'phase_a': (6.0, -22.0),
        'bayes': (22.0, -16.0),
    },
]

LAMBDAS = [0.0, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0]


def forward(theta, bs, bc, theta_conf):
    th = np.deg2rad(theta)
    return (theta + bs * np.cos(th - np.pi/2)
                  + bc * np.cos(th - np.deg2rad(theta_conf))) % 360.0


def p2a_compute(bs, bc, theta_conf, target_map):
    total = 0.0; exact = 0
    for theta in HUE_8:
        theta_cvd = forward(float(theta), bs, bc, theta_conf)
        pred = hc_name(theta_cvd)
        target = target_map[int(theta)]
        s = hc_match_score(pred, target)
        total += s
        if pred == target: exact += 1
    return total / 8.0, exact


def sweep_msetikh(landscape_path, axis, target_map, p2a_max_pt, phase_a_pt, bayes_pt):
    d = json.load(open(landscape_path))
    cells = d['cells']
    vuln_obs = np.array(d['vuln_cvd'])
    bs_arr = np.array([c['bs'] for c in cells])
    bc_arr = np.array([c['bc'] for c in cells])
    vsim = np.array([c['vuln_sim'] for c in cells])

    # Compute L_mse per cell (amplitude-sensitive)
    L_mse_raw = ((vsim - vuln_obs[None, :]) ** 2).mean(axis=1)
    # Normalize L_mse to make λ comparable across data
    L_mse_norm = L_mse_raw / L_mse_raw.max() if L_mse_raw.max() > 0 else L_mse_raw
    # Tikh penalty
    tikh = (bs_arr**2 + bc_arr**2) / TIKH_NORM

    rows = []
    for lam in LAMBDAS:
        L = L_mse_norm + lam * tikh
        idx = int(np.argmin(L))
        bs, bc = float(bs_arr[idx]), float(bc_arr[idx])
        p2a, ex = p2a_compute(bs, bc, axis, target_map)
        rows.append({
            'lambda': lam,
            'bs': bs, 'bc': bc,
            'L': float(L[idx]),
            'L_mse_norm': float(L_mse_norm[idx]),
            'tikh': float(tikh[idx]),
            'p2a': p2a, 'exact': ex,
            'dist_to_p2amax': float(np.hypot(bs - p2a_max_pt[0], bc - p2a_max_pt[1])),
            'dist_to_phase_a': float(np.hypot(bs - phase_a_pt[0], bc - phase_a_pt[1])),
            'dist_to_bayes':   float(np.hypot(bs - bayes_pt[0], bc - bayes_pt[1])),
            'norm': float(np.hypot(bs, bc)),
            'sign': '+' if bc > 0 else ('-' if bc < 0 else '0'),
        })
    return rows, vuln_obs, bs_arr, bc_arr, L_mse_norm, tikh, vsim


def main():
    print('=' * 110)
    print('NEURAL-PRIMARY UNIFIED LOSS: L_mse(V4) + λ · Tikh')
    print('=' * 110)
    print('  Same formulation both subjects, no anchor extraction, no literature')
    print(f'  λ sweep: {LAMBDAS}')
    print()

    all_results = {}
    for case in CASES:
        sid = case['sid']
        print(f'\n--- sub-{sid} ({case["family"]}) axis={case["axis"]}° ---')
        rows, vuln_obs, bs_arr, bc_arr, L_mse_n, tikh, vsim = sweep_msetikh(
            case['landscape'], case['axis'], case['target_map'],
            case['p2a_max'], case['phase_a'], case['bayes'])
        print(f'  {"λ":>5s}  {"argmin":<14s}  {"P2a":>5s}  '
              f'{"d→max":>6s}  {"d→pha":>6s}  {"|β|":>5s}  sign')
        for r in rows:
            print(f'  {r["lambda"]:>5.2f}  ({r["bs"]:>3.0f}°, {r["bc"]:>+4.0f}°)  '
                  f'{r["p2a"]:>5.3f}  {r["dist_to_p2amax"]:>6.1f}  '
                  f'{r["dist_to_phase_a"]:>6.1f}  {r["norm"]:>5.1f}  {r["sign"]}')
        all_results[f'sub-{sid}'] = {
            'axis': case['axis'],
            'family': case['family'],
            'reference': {
                'P2a_max':       case['p2a_max'],
                'phase_a':       case['phase_a'],
                'bayes':         case['bayes'],
            },
            'lambda_sweep': rows,
        }

    # Best λ for joint criteria (P2a high, |β| moderate)
    print('\n' + '=' * 110)
    print('UNIFIED λ SELECTION (joint criterion: high P2a both + moderate norm)')
    print('=' * 110)
    sub08_rows = all_results['sub-08']['lambda_sweep']
    sub09_rows = all_results['sub-09']['lambda_sweep']
    print(f'  {"λ":>5s}  {"sub-08 (β_s,β_c)":<18s}  {"sub-09 (β_s,β_c)":<18s}  '
          f'{"P2a-08":>6s}  {"P2a-09":>6s}  {"min":>5s}  {"avg":>5s}  '
          f'{"|β|-08":>7s}  {"|β|-09":>7s}')
    best_lambda = None
    best_min_p2a = -np.inf
    for r8, r9 in zip(sub08_rows, sub09_rows):
        min_p2a = min(r8['p2a'], r9['p2a'])
        avg_p2a = (r8['p2a'] + r9['p2a']) / 2
        if min_p2a > best_min_p2a:
            best_min_p2a = min_p2a; best_lambda = r8['lambda']
        marker = ' ★' if min_p2a == best_min_p2a else '  '
        print(f'  {r8["lambda"]:>5.2f}{marker}'
              f'  ({r8["bs"]:>3.0f}°, {r8["bc"]:>+4.0f}°)    '
              f'  ({r9["bs"]:>3.0f}°, {r9["bc"]:>+4.0f}°)    '
              f'  {r8["p2a"]:>6.3f}  {r9["p2a"]:>6.3f}  '
              f'{min_p2a:>5.3f}  {avg_p2a:>5.3f}  '
              f'{r8["norm"]:>7.1f}  {r9["norm"]:>7.1f}')
    print(f'\n  → BEST λ (max min P2a) = {best_lambda}')

    # Final selected λ comparison vs existing BESTs
    print('\n' + '=' * 110)
    print('COMPARISON: L_mse+Tikh BEST vs existing options')
    print('=' * 110)
    if best_lambda is not None:
        r8 = next(r for r in sub08_rows if r['lambda'] == best_lambda)
        r9 = next(r for r in sub09_rows if r['lambda'] == best_lambda)
        print(f'\n  L_mse + {best_lambda}·Tikh:')
        print(f'    sub-08 (β_s, β_c) = ({r8["bs"]:.0f}°, {r8["bc"]:+.0f}°), '
              f'P2a={r8["p2a"]:.3f} ({r8["exact"]}/8), '
              f'dist→P2a-max={r8["dist_to_p2amax"]:.1f}°, Brettel + sign = '
              f'{"OK" if r8["sign"] == "+" else "FAIL"}')
        print(f'    sub-09 (β_s, β_c) = ({r9["bs"]:.0f}°, {r9["bc"]:+.0f}°), '
              f'P2a={r9["p2a"]:.3f} ({r9["exact"]}/8), '
              f'dist→P2a-max={r9["dist_to_p2amax"]:.1f}°, Brettel − sign = '
              f'{"OK" if r9["sign"] == "-" else "FAIL"}')
        print(f'    avg P2a = {(r8["p2a"]+r9["p2a"])/2:.3f}')

    print('\n  Comparison table:')
    print(f'  {"loss":<32s}  {"sub-08":>16s}  {"P2a-08":>6s}  '
          f'{"sub-09":>16s}  {"P2a-09":>6s}  {"avg":>5s}')
    print(f'  {"-"*32}  {"-"*16}  {"-"*6}  {"-"*16}  {"-"*6}  {"-"*5}')
    print(f'  {"P2a-max (behavioral)":<32s}  '
          f'({CASES[0]["p2a_max"][0]:>2.0f}°,{CASES[0]["p2a_max"][1]:>+3.0f}°)     0.875  '
          f'({CASES[1]["p2a_max"][0]:>2.0f}°,{CASES[1]["p2a_max"][1]:>+3.0f}°)     0.950   0.913')
    print(f'  {"LIT2N-ORIG (phase_a anchor)":<32s}  '
          f'( 20°, -14°)     0.263  ( 22°, -22°)     0.887   0.575')
    print(f'  {"LIT2N-BEST (heterogeneous)":<32s}  '
          f'( 20°, +22°)     0.550  ( 22°, -22°)     0.887   0.719')
    print(f'  {"Bayesian (α=0.3)":<32s}  '
          f'( 22°, +18°)     0.550  ( 22°, -16°)     0.887   0.719')
    if best_lambda is not None:
        print(f'  {"L_mse + " + str(best_lambda) + "·Tikh":<32s}  '
              f'({r8["bs"]:>3.0f}°,{r8["bc"]:>+3.0f}°)    {r8["p2a"]:>6.3f}  '
              f'({r9["bs"]:>3.0f}°,{r9["bc"]:>+3.0f}°)    {r9["p2a"]:>6.3f}  '
              f'{(r8["p2a"]+r9["p2a"])/2:>5.3f}')

    out_json = OUT / f'{PREFIX}results.json'
    with open(out_json, 'w') as f:
        json.dump({
            'lambdas': LAMBDAS,
            'best_lambda': best_lambda,
            'subjects': all_results,
        }, f, indent=2)
    print(f'\nWrote {out_json}')

    # Visualization
    _render_msetikh_fig(all_results, best_lambda)


def _render_msetikh_fig(results, best_lambda):
    fig = plt.figure(figsize=(14, 8))
    gs = fig.add_gridspec(2, 3, hspace=0.32, wspace=0.30,
                          left=0.06, right=0.97, top=0.93, bottom=0.07)

    for col, sid in enumerate(['sub-08', 'sub-09']):
        rows = results[sid]['lambda_sweep']
        ref = results[sid]['reference']

        # Top row: λ vs (β_s, β_c) trajectory
        ax = fig.add_subplot(gs[0, col])
        xs = [r['bs'] for r in rows]
        ys = [r['bc'] for r in rows]
        lams = [r['lambda'] for r in rows]
        ax.plot(xs, ys, 'o-', color='black', lw=0.6, alpha=0.5)
        sc = ax.scatter(xs, ys, c=lams, cmap='viridis', s=80, edgecolors='black',
                         linewidth=0.6, zorder=3)
        for r in rows:
            ax.annotate(f'λ={r["lambda"]:g}', (r['bs'], r['bc']),
                        xytext=(4, 4), textcoords='offset points', fontsize=6)
        # References
        ax.plot(*ref['P2a_max'], '*', mfc='gold', mec='black', ms=20, mew=0.7,
                label=f'P2a-max', zorder=5)
        ax.plot(*ref['phase_a'], 's', mfc='none', mec='red', ms=12, mew=1.4,
                label='phase_a', zorder=4)
        ax.plot(*ref['bayes'], 'D', mfc='none', mec='blue', ms=10, mew=1.2,
                label='Bayes', zorder=4)
        ax.axhline(0, color='gray', lw=0.4); ax.axvline(0, color='gray', lw=0.4)
        ax.set_xlabel(r'$\beta_s$ (°)')
        ax.set_ylabel(r'$\beta_c$ (°)')
        ax.set_title(f'{sid} — argmin trajectory across λ',
                     fontweight='bold')
        ax.legend(fontsize=6, loc='best')
        plt.colorbar(sc, ax=ax, label='λ', fraction=0.04)

        # Bottom row: λ vs P2a + |β|
        ax = fig.add_subplot(gs[1, col])
        ax2 = ax.twinx()
        ax.plot(lams, [r['p2a'] for r in rows], 'o-', color='#2E86AB', ms=8,
                lw=1.5, label='P2a')
        ax2.plot(lams, [r['norm'] for r in rows], 's-', color='#E63946', ms=7,
                 lw=1.2, label='||β||')
        ax.axhline(0.875 if sid == 'sub-08' else 0.950, ls='--', color='gold',
                   lw=1.0, label='P2a-max')
        ax.set_xlabel('λ (Tikh weight)')
        ax.set_ylabel('P2a', color='#2E86AB')
        ax2.set_ylabel('||β|| (°)', color='#E63946')
        ax.set_xscale('symlog', linthresh=0.05)
        ax.set_ylim(0, 1.0)
        if best_lambda is not None:
            ax.axvline(best_lambda, color='black', lw=0.8, ls=':',
                       label=f'BEST λ={best_lambda}')
        ax.set_title(f'{sid} — λ sensitivity (P2a vs amplitude)',
                     fontweight='bold')
        ax.legend(loc='upper left', fontsize=7)
        ax2.legend(loc='upper right', fontsize=7)

    # Comparison panel
    ax = fig.add_subplot(gs[0, 2])
    ax.axis('off')
    r8 = next((r for r in results['sub-08']['lambda_sweep']
               if r['lambda'] == best_lambda), None)
    r9 = next((r for r in results['sub-09']['lambda_sweep']
               if r['lambda'] == best_lambda), None)

    text = "L_mse + λ·Tikh UNIFIED RESULTS\n\n"
    text += f"BEST λ = {best_lambda}\n\n"
    if r8 and r9:
        text += "sub-08 deutan:\n"
        text += f"  (β_s, β_c) = ({r8['bs']:.0f}°, {r8['bc']:+.0f}°)\n"
        text += f"  P2a = {r8['p2a']:.3f} (exact {r8['exact']}/8)\n"
        text += f"  ||β|| = {r8['norm']:.1f}°\n"
        text += f"  dist → P2a-max = {r8['dist_to_p2amax']:.1f}°\n"
        text += f"  β_c sign = {r8['sign']} (Brettel + expected)\n\n"
        text += "sub-09 protan:\n"
        text += f"  (β_s, β_c) = ({r9['bs']:.0f}°, {r9['bc']:+.0f}°)\n"
        text += f"  P2a = {r9['p2a']:.3f} (exact {r9['exact']}/8)\n"
        text += f"  ||β|| = {r9['norm']:.1f}°\n"
        text += f"  dist → P2a-max = {r9['dist_to_p2amax']:.1f}°\n"
        text += f"  β_c sign = {r9['sign']} (Brettel − expected)\n\n"
        text += f"avg P2a = {(r8['p2a']+r9['p2a'])/2:.3f}\n"
    ax.text(0.0, 0.95, text, ha='left', va='top', family='monospace',
            fontsize=8.5, transform=ax.transAxes)

    # Avg P2a comparison bar
    ax = fig.add_subplot(gs[1, 2])
    methods = ['phase_a\nanchor', 'L_combined\nboot anchor', 'Bayesian\nα=0.3',
               f'L_mse+\nλ={best_lambda}·Tikh']
    sub08_p2a = [0.263, 0.550, 0.550, r8['p2a'] if r8 else 0]
    sub09_p2a = [0.887, 0.388, 0.887, r9['p2a'] if r9 else 0]
    x = np.arange(len(methods))
    w = 0.35
    ax.bar(x - w/2, sub08_p2a, w, color='#E07B2C', alpha=0.85, label='sub-08')
    ax.bar(x + w/2, sub09_p2a, w, color='#2D8E8B', alpha=0.85, label='sub-09')
    for i, (a, b) in enumerate(zip(sub08_p2a, sub09_p2a)):
        ax.text(i - w/2, a + 0.01, f'{a:.3f}', ha='center', fontsize=6.5)
        ax.text(i + w/2, b + 0.01, f'{b:.3f}', ha='center', fontsize=6.5)
    ax.axhline(0.875, ls='--', color='#E07B2C', lw=0.7, alpha=0.6)
    ax.axhline(0.950, ls='--', color='#2D8E8B', lw=0.7, alpha=0.6)
    ax.set_xticks(x); ax.set_xticklabels(methods, fontsize=7)
    ax.set_ylabel('P2a'); ax.set_ylim(0, 1.0)
    ax.set_title('P2a comparison across unified loss choices',
                 fontweight='bold')
    ax.legend(fontsize=7); ax.spines[['top','right']].set_visible(False)

    fig.suptitle('LIT2Neural ALT — L_mse + λ·Tikh neural-primary unified loss',
                 fontsize=11, fontweight='bold')
    out_png = OUT / f'{PREFIX}lambda_sweep.png'
    plt.savefig(out_png, dpi=150, bbox_inches='tight')
    plt.savefig(str(out_png).replace('.png', '.pdf'), bbox_inches='tight')
    plt.close(fig)
    print(f'wrote {out_png.name} (+pdf)')


if __name__ == '__main__':
    main()
