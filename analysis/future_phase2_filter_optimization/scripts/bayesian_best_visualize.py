"""bayesian_best_visualize.py — Bayesian BEST candidate (α=0.3) 시각화.

L = α·L_ccc + (1−α)·(0.5·Emery + 0.5·Tregillus + 0.3·Brettel) + 0.1·Tikh
α = 0.3 fixed

Outputs:
  results/BAYESIAN_BEST/
    F4_unified.png             — sub-08 + sub-09 candidates side-by-side
    4col_sub-{08,09}.png       — full 4-col rendering
    vuln_hue_sub-{08,09}.png   — line graph
    alpha_sensitivity.png      — α sweep curve
    landscape_sub-{08,09}.png  — L_unified landscape
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR))

from stim_lab_render import render_at_hue as _render_stim_lab
from phase3_candidate_analysis_v2 import (
    hc_name, hc_match_score, SUB08_ORIGINAL_HC_EQUIV,
)
from fixedW_onlyTest_p2a_ranking import SUB09_ORIGINAL_HC_EQUIV

OUT = _THIS_DIR.parent / 'results' / 'BAYESIAN_BEST'
OUT.mkdir(parents=True, exist_ok=True)

HUE_8 = [0, 45, 90, 135, 180, 225, 270, 315]
COLOR_LABELS = ['c1 R(0°)', 'c2 O(45°)', 'c3 Y(90°)', 'c4 G(135°)',
                'c5 C(180°)', 'c6 S(225°)', 'c7 B(270°)', 'c8 M(315°)']
SHORT = ['R', 'O', 'Y', 'G', 'C', 'S', 'B', 'M']

EMERY_BS = 21.4
TREG_NORM = 28.0
BRETTEL_SIGN = {'deutan': +1, 'protan': -1}
ALPHA_DEFAULT = 0.3


def forward(theta, bs, bc, phi_c, phi_s=90.0):
    dt = (bs*np.cos(np.radians(theta-phi_s)) + bc*np.cos(np.radians(theta-phi_c)))
    return (theta + dt) % 360.0, float(dt)


def pre_image(target, bs, bc, phi_c, n_grid=3600):
    grid = np.linspace(0, 360, n_grid, endpoint=False)
    forwards = np.array([forward(t, bs, bc, phi_c)[0] for t in grid])
    diff = (forwards - target + 180) % 360 - 180
    i = int(np.argmin(np.abs(diff)))
    return float(grid[i]), float(diff[i])


def p2a(bs, bc, phi_c, target_map):
    total = 0.0; exact = 0
    for theta in HUE_8:
        theta_cvd, _ = forward(float(theta), bs, bc, phi_c)
        pred = hc_name(theta_cvd)
        target = target_map[theta]
        total += hc_match_score(pred, target)
        if pred == target: exact += 1
    return total / 8.0, exact


def L_unified(bs, bc, l_ccc, family, alpha=ALPHA_DEFAULT):
    L_emery = ((bs - EMERY_BS) / 10.0) ** 2
    L_tregillus = ((np.hypot(bs, bc) - TREG_NORM) / 15.0) ** 2
    L_brettel = max(0.0, -bc * BRETTEL_SIGN[family] / 50.0) ** 2
    Tikh = (bs*bs + bc*bc) / 32400.0
    return (alpha * l_ccc
            + (1 - alpha) * (0.5*L_emery + 0.5*L_tregillus + 0.3*L_brettel)
            + 0.1 * Tikh)


def find_best(cells, family, alpha=ALPHA_DEFAULT):
    best_L = np.inf; best = None
    for c in cells:
        L = L_unified(c['bs'], c['bc'], c['l_ccc'], family, alpha)
        if L < best_L:
            best_L = L; best = c
    return best, best_L


# ----------------------------------------------------------------------
# Plot 1: F4-style — vuln_hue + 4-col rendering
# ----------------------------------------------------------------------
def render_F4_panel(sid, family, color, axis, cells, vuln_cvd, target_map, bs, bc, p2a_val, exact, l_ccc, ccc, l_topk, out_path):
    fig = plt.figure(figsize=(15, 11), dpi=140)
    gs = fig.add_gridspec(2, 2, width_ratios=[1.2, 1.6], height_ratios=[1, 1.6],
                          hspace=0.28, wspace=0.20)

    # Find the actual cell with this (bs, bc)
    target_cell = None
    for c in cells:
        if abs(c['bs']-bs) < 0.5 and abs(c['bc']-bc) < 0.5:
            target_cell = c; break
    vuln_sim = np.array(target_cell['vuln_sim']) if target_cell else None

    # Panel A: vuln_hue (top-left) — actually plot
    ax_a = fig.add_subplot(gs[0, 0])
    x = np.arange(8)
    ax_a.axhline(0, color='#aaa', lw=0.5, ls=':')
    ax_a.plot(x, vuln_cvd, 'o-', color='#222', ms=6, lw=1.0,
              label='Observed CVD LOCO')
    if vuln_sim is not None:
        ax_a.plot(x, vuln_sim, 's-', color=color, ms=7, lw=1.6,
                  label=f'sim (CCC={ccc:+.2f}, l_topk={l_topk:.2f})')
        top3_obs = np.argsort(vuln_cvd)[:3]
        for idx in top3_obs:
            ax_a.axvspan(idx-0.4, idx+0.4, alpha=0.10, color=color, zorder=0)
    ax_a.set_xticks(x); ax_a.set_xticklabels(SHORT)
    ax_a.set_ylim(-1, 1)
    ax_a.set_xlabel('Hue bin (shaded = top-3 obs)')
    ax_a.set_ylabel('LOCO voxel_corr')
    ax_a.set_title(f'(A) vuln_hue line — V4 LOCO  CCC={ccc:+.3f}',
                   fontsize=10, fontweight='bold')
    ax_a.legend(loc='lower right', fontsize=7)
    ax_a.spines[['top', 'right']].set_visible(False)

    # Panel B: P2a per-color bars (top-right)
    ax_b = fig.add_subplot(gs[0, 1])
    rows = []
    for theta in HUE_8:
        theta_cvd, dt = forward(float(theta), bs, bc, axis)
        pred = hc_name(theta_cvd)
        target = target_map[theta]
        s = hc_match_score(pred, target)
        rows.append({'theta': theta, 'pred': pred, 'target': target,
                     'score': s, 'dt': dt})
    scores = [r['score'] for r in rows]
    colors_bar = ['green' if s == 1.0 else ('darkorange' if s > 0 else 'red')
                  for s in scores]
    x = np.arange(8)
    ax_b.bar(x, scores, color=colors_bar, edgecolor='black', linewidth=0.5)
    ax_b.set_xticks(x); ax_b.set_xticklabels(SHORT)
    ax_b.axhline(0.5, color='gray', ls=':', lw=0.5)
    ax_b.set_ylim(0, 1.05)
    ax_b.set_ylabel('hc_match_score')
    ax_b.set_title(f'(B) P2a per-color  '
                   f'mean={p2a_val:.3f}  exact={exact}/8',
                   fontsize=10, fontweight='bold')
    for i, r in enumerate(rows):
        ax_b.text(x[i], 0.05, f'{r["pred"]}\n→{r["target"]}',
                  ha='center', va='bottom', fontsize=6, rotation=0)

    # Panel C: 4-col rendering matrix (bottom, full width)
    gs_sub = gs[1, :].subgridspec(8, 4, hspace=0.05, wspace=0.05)
    for i, theta in enumerate(HUE_8):
        theta_cvd, dt = forward(float(theta), bs, bc, axis)
        theta_pre, _ = pre_image(float(theta), bs, bc, axis)
        theta_cvd_pre, _ = forward(theta_pre, bs, bc, axis)
        rgbs = [_render_stim_lab(float(theta)), _render_stim_lab(theta_cvd),
                _render_stim_lab(theta_pre), _render_stim_lab(theta_cvd_pre)]
        for k, rgb in enumerate(rgbs):
            ax = fig.add_subplot(gs_sub[i, k])
            ax.add_patch(Rectangle((0,0), 1, 1, color=rgb))
            ax.set_xticks([]); ax.set_yticks([])
            ax.set_xlim(0,1); ax.set_ylim(0,1)
            for sp in ax.spines.values():
                sp.set_edgecolor('black'); sp.set_linewidth(0.4)
            if i == 0:
                titles = ['Original', 'CVD perceives', 'Filter', 'CVD(Filter)']
                ax.set_title(titles[k], fontsize=9)
            if k == 0:
                ax.text(-0.04, 0.5, f'{COLOR_LABELS[i]}\nδθ={dt:+.0f}°',
                        ha='right', va='center', fontsize=7,
                        transform=ax.transAxes)
            if k == 1:
                target = target_map[theta]
                pred = hc_name(theta_cvd)
                s = hc_match_score(pred, target)
                mark = '✓' if pred == target else ('~' if s > 0 else '✗')
                col_p = 'green' if s == 1.0 else ('darkorange' if s > 0 else 'red')
                ax.text(0.5, -0.05, f'{pred} {mark}',
                        ha='center', va='top', fontsize=7,
                        transform=ax.transAxes, color=col_p)

    fig.suptitle(f'sub-{sid} ({family}) V4 — Bayesian BEST  '
                 f'L = 0.3·L_ccc + 0.7·(0.5·Emery + 0.5·Tregillus + 0.3·Brettel) + 0.1·Tikh\n'
                 f'argmin β_s={bs:.0f}, β_c={bc:+.0f}  '
                 f'(axis={axis}°)  L_ccc={l_ccc:.3f}  P2a={p2a_val:.3f} ({exact}/8)',
                 fontsize=11, fontweight='bold', color=color, y=0.99)

    plt.savefig(out_path, dpi=140, bbox_inches='tight')
    plt.savefig(str(out_path).replace('.png', '.pdf'), bbox_inches='tight')
    plt.close()
    return rows, vuln_sim, ax_a


def render_vuln_hue_panel(out_path, sid, family, color, vuln_cvd, vuln_sim, bs, bc, ccc, l_topk, p2a_val):
    fig, ax = plt.subplots(figsize=(7, 4), dpi=140)
    x = np.arange(8)
    ax.axhline(0, color='#aaa', lw=0.5, ls=':')
    ax.plot(x, vuln_cvd, 'o-', color='#222', ms=6, lw=1.0, label='Observed CVD LOCO')
    ax.plot(x, vuln_sim, 's-', color=color, ms=7, lw=1.6,
            label=f'Bayesian BEST sim (CCC={ccc:+.2f}, l_topk={l_topk:.2f})')
    top3_obs = np.argsort(vuln_cvd)[:3]
    for idx in top3_obs:
        ax.axvspan(idx-0.4, idx+0.4, alpha=0.10, color=color, zorder=0)
    ax.set_xticks(x); ax.set_xticklabels(SHORT)
    ax.set_ylim(-1, 1)
    ax.set_xlabel('Hue bin (shaded = top-3 vulnerable in obs)')
    ax.set_ylabel('LOCO voxel_corr (↑preserved/↓vulnerable)')
    ax.set_title(f'sub-{sid} ({family}) V4 — Bayesian BEST  '
                 f'β_s={bs:.0f}, β_c={bc:+.0f}  P2a={p2a_val:.3f}',
                 fontsize=10, fontweight='bold', color=color)
    ax.legend(loc='lower right', fontsize=8)
    ax.spines[['top', 'right']].set_visible(False)
    plt.tight_layout()
    plt.savefig(out_path, dpi=140, bbox_inches='tight')
    plt.savefig(str(out_path).replace('.png', '.pdf'), bbox_inches='tight')
    plt.close()


def render_alpha_sensitivity(out_path, sweep_results):
    """sweep_results: dict {subject_id: [(alpha, bs, bc, p2a, exact), ...]}"""
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), dpi=140)
    colors = {'08': '#E07B2C', '09': '#2D8E8B'}
    titles = {'08': 'sub-08 (deutan)', '09': 'sub-09 (protan)'}
    for ax, sid in zip(axes, ['08', '09']):
        rows = sweep_results[sid]
        alphas = [r[0] for r in rows]
        p2as = [r[3] for r in rows]
        ex = [r[4] for r in rows]
        ax.plot(alphas, p2as, 'o-', color=colors[sid], ms=8, lw=1.5,
                label='P2a (mean score)')
        ax2 = ax.twinx()
        ax2.plot(alphas, ex, 's--', color='#888', ms=6, lw=1.0,
                 label='exact match (right axis)')
        ax2.set_ylim(-0.5, 8.5)
        ax2.set_ylabel('exact / 8', color='#888')
        ax.axvline(ALPHA_DEFAULT, color='red', ls=':', lw=1.0,
                   label=f'α={ALPHA_DEFAULT} (BEST)')
        ax.set_xlabel('α (neural likelihood weight)')
        ax.set_ylabel('P2a')
        ax.set_title(f'{titles[sid]} α sensitivity', fontsize=11, fontweight='bold')
        ax.set_ylim(0, 1)
        ax.legend(loc='upper left', fontsize=8)
        ax2.legend(loc='upper right', fontsize=8)
        # Annotate breakpoint
        # show argmin (bs, bc) for each α
        for r in rows:
            ax.annotate(f'({r[1]:.0f},{r[2]:+.0f})',
                        (r[0], r[3]), fontsize=6, ha='center',
                        xytext=(0, 8), textcoords='offset points')
    fig.suptitle('Bayesian framework α sensitivity\n'
                 'L = α·L_ccc + (1−α)·(0.5·Emery + 0.5·Tregillus + 0.3·Brettel) + 0.1·Tikh',
                 fontsize=11, fontweight='bold')
    plt.tight_layout()
    plt.savefig(out_path, dpi=140, bbox_inches='tight')
    plt.savefig(str(out_path).replace('.png', '.pdf'), bbox_inches='tight')
    plt.close()


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main():
    cases = [
        ('08', 'deutan', '#E07B2C', 150.0,
         'results/axis_3way/sub-08_V4_Stockman150_landscape.json',
         SUB08_ORIGINAL_HC_EQUIV),
        ('09', 'protan', '#2D8E8B', 16.0,
         'results/axis_3way/sub-09_V4_Stockman16ext_landscape.json',
         SUB09_ORIGINAL_HC_EQUIV),
    ]

    sensitivity = {'08': [], '09': []}
    alpha_grid = np.arange(0.0, 1.01, 0.05)
    summary = {}

    for sid, family, color, axis, path, tmap in cases:
        with open(path) as f:
            d = json.load(f)
        cells = d['cells']
        vuln_cvd = np.array(d['vuln_cvd'])

        # α sweep for sensitivity plot
        for alpha in alpha_grid:
            best, best_L = find_best(cells, family, alpha=float(alpha))
            p_val, ex = p2a(best['bs'], best['bc'], axis, tmap)
            sensitivity[sid].append(
                (float(alpha), best['bs'], best['bc'], p_val, ex))

        # BEST at α=0.3
        best, best_L = find_best(cells, family, alpha=ALPHA_DEFAULT)
        p_val, exact = p2a(best['bs'], best['bc'], axis, tmap)
        print(f'sub-{sid} BEST: (β_s={best["bs"]:.0f}, β_c={best["bc"]:+.0f})  '
              f'L={best_L:.4f}  L_ccc={best["l_ccc"]:.3f}  CCC={best.get("ccc",0):+.3f}  '
              f'P2a={p_val:.3f} ({exact}/8)')

        # F4 figure
        render_F4_panel(sid, family, color, axis, cells, vuln_cvd, tmap,
                        best['bs'], best['bc'], p_val, exact,
                        best['l_ccc'], best.get('ccc', 0), best.get('l_topk', 0),
                        OUT / f'F4_sub-{sid}.png')
        # Vuln_hue
        render_vuln_hue_panel(OUT / f'vuln_hue_sub-{sid}.png',
                              sid, family, color, vuln_cvd,
                              np.array(best['vuln_sim']),
                              best['bs'], best['bc'],
                              best.get('ccc', 0), best.get('l_topk', 0),
                              p_val)

        summary[f'sub-{sid}'] = {
            'family': family, 'axis': axis,
            'bs': best['bs'], 'bc': best['bc'],
            'norm': float(np.hypot(best['bs'], best['bc'])),
            'L_unified': float(best_L),
            'L_ccc': best['l_ccc'],
            'ccc': best.get('ccc', 0),
            'l_topk': best.get('l_topk', 0),
            'p2a': float(p_val),
            'exact': int(exact),
            'alpha_used': ALPHA_DEFAULT,
        }

    # α sensitivity plot
    render_alpha_sensitivity(OUT / 'alpha_sensitivity.png', sensitivity)

    # Save BEST summary
    with open(OUT / 'BAYESIAN_BEST_summary.json', 'w') as f:
        json.dump({
            'framework': 'Hierarchical Bayesian filter design',
            'loss_formula': 'L = α·L_ccc + (1−α)·(0.5·Emery + 0.5·Tregillus + 0.3·Brettel) + 0.1·Tikh',
            'alpha': ALPHA_DEFAULT,
            'literature_anchors': {
                'Emery_2021_beta_s': EMERY_BS,
                'Tregillus_2021_norm': TREG_NORM,
                'Brettel_1997_signs': BRETTEL_SIGN,
            },
            'BEST': summary,
            'alpha_sensitivity': {
                sid: [{'alpha': r[0], 'bs': r[1], 'bc': r[2],
                       'p2a': r[3], 'exact': r[4]}
                      for r in rows] for sid, rows in sensitivity.items()
            },
        }, f, indent=2)
    print(f'\nWrote {OUT}/ figures + BAYESIAN_BEST_summary.json')


if __name__ == '__main__':
    main()
