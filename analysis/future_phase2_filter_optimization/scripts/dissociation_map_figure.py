"""dissociation_map_figure.py — Neural-primary vs Bayesian vs P2a-max oracle 시각화.

Output: results/neural_primary/dissociation_map.{png,pdf}

Panel layout (2 × 3):
  [A] sub-08 landscape (V4 LOCO ρ heatmap) + 4 points overlay
  [B] sub-09 landscape + 4 points overlay
  [C] α_neural sweep — sub-08
  [D] α_neural sweep — sub-09
  [E] Per-color P2a — sub-08 (Bayesian vs Neural-primary vs P2a-max)
  [F] Per-color P2a — sub-09
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

_THIS = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS))
from phase3_candidate_analysis_v2 import hc_name, hc_match_score, SUB08_ORIGINAL_HC_EQUIV
from fixedW_onlyTest_p2a_ranking import SUB09_ORIGINAL_HC_EQUIV
from neural_only_deep_sweep import (
    NEURAL_ANCHORS, V1_DELTA_RDM, P2A_MAX, BAYESIAN_BEST,
)

OUT = _THIS.parent / 'results' / 'neural_primary'
COLOR_NAMES = ['c1\nred', 'c2\norange', 'c3\nyellow', 'c4\ngreen',
               'c5\ncyan', 'c6\nsky', 'c7\nblue', 'c8\nmagenta']
HUE_8 = [0, 45, 90, 135, 180, 225, 270, 315]


def forward(theta, bs, bc, phi_c, phi_s=90.0):
    return (theta + bs * np.cos(np.radians(theta - phi_s))
                  + bc * np.cos(np.radians(theta - phi_c))) % 360.0


def per_color_score(bs, bc, phi_c, target_map):
    scores = []
    for theta in HUE_8:
        tc = forward(float(theta), bs, bc, phi_c)
        pred = hc_name(tc)
        scores.append(hc_match_score(pred, target_map[theta]))
    return scores


def load_landscape_grid(path):
    with open(path) as f:
        d = json.load(f)
    cells = d['cells']
    bs = np.array([c['bs'] for c in cells])
    bc = np.array([c['bc'] for c in cells])
    ccc = np.array([c['ccc'] for c in cells])
    bs_unique = np.unique(bs)
    bc_unique = np.unique(bc)
    Z = np.full((len(bc_unique), len(bs_unique)), np.nan)
    for b_s, b_c, val in zip(bs, bc, ccc):
        i = int(np.searchsorted(bc_unique, b_c))
        j = int(np.searchsorted(bs_unique, b_s))
        Z[i, j] = val
    return bs_unique, bc_unique, Z


def panel_landscape(ax, path, sid, axis, np_pt, alpha_results):
    """Landscape heatmap + 4 model points."""
    bs_u, bc_u, Z = load_landscape_grid(path)
    im = ax.imshow(Z, origin='lower', aspect='auto', cmap='RdBu_r',
                    extent=[bs_u.min(), bs_u.max(), bc_u.min(), bc_u.max()],
                    vmin=-0.5, vmax=0.5)
    plt.colorbar(im, ax=ax, fraction=0.04, pad=0.02, label='V4 LOCO CCC')

    # Points
    bay = BAYESIAN_BEST[sid]
    p2a_max = P2A_MAX[sid]
    anchor_bs = V1_DELTA_RDM[sid][0]
    anchor_bc = NEURAL_ANCHORS[sid]['V4'][1]

    ax.scatter(*bay, marker='s', s=180, edgecolor='black', facecolor='#E07B2C',
               linewidth=2, label=f'Bayesian {bay}', zorder=8)
    ax.scatter(np_pt[0], np_pt[1], marker='o', s=180, edgecolor='black',
               facecolor='#2D8E8B', linewidth=2,
               label=f'Neural-primary α=0.7 ({np_pt[0]:.0f},{np_pt[1]:+.0f})', zorder=8)
    ax.scatter(*p2a_max, marker='*', s=350, edgecolor='black', facecolor='#FFD700',
               linewidth=1.5, label=f'P2a-max oracle {p2a_max}', zorder=9)
    ax.scatter(anchor_bs, anchor_bc, marker='^', s=180,
               edgecolor='black', facecolor='white', linewidth=2,
               label=f'Neural anchors (V1 β_s={anchor_bs}, V4 β_c={anchor_bc})', zorder=8)

    # α_neural trajectory
    bs_traj = [r['bs'] for r in alpha_results]
    bc_traj = [r['bc'] for r in alpha_results]
    ax.plot(bs_traj, bc_traj, '-', color='#2D8E8B', alpha=0.6, lw=2, zorder=7)
    for r in alpha_results:
        ax.annotate(f'α={r["alpha_neural"]:.1f}',
                    xy=(r['bs'], r['bc']),
                    xytext=(r['bs']+1.5, r['bc']+1.5), fontsize=8,
                    color='#2D8E8B')

    ax.set_xlabel('β_s (degrees)')
    ax.set_ylabel('β_c (degrees)')
    ax.legend(loc='lower left', fontsize=8, framealpha=0.9)
    ax.axhline(0, color='black', lw=0.5, alpha=0.4)
    ax.axvline(0, color='black', lw=0.5, alpha=0.4)


def panel_alpha_sweep(ax, alpha_results, sid):
    """P2a vs α_neural + dist→P2a-max."""
    alphas = [r['alpha_neural'] for r in alpha_results]
    p2as = [r['p2a'] for r in alpha_results]
    dists = [r['dist_to_p2amax'] for r in alpha_results]

    ax.plot(alphas, p2as, 'o-', color='#2D8E8B', ms=10, lw=2, label='P2a (left)')
    ax2 = ax.twinx()
    ax2.plot(alphas, dists, 's--', color='#E07B2C', ms=10, lw=2, label='dist→P2a-max (right)')

    ax.axhline(P2A_BAY[sid], color='gray', ls=':', lw=1, label=f'Bayesian P2a={P2A_BAY[sid]}')
    ax.axhline(P2A_ORACLE[sid], color='#FFA500', ls=':', lw=1, label=f'P2a-max={P2A_ORACLE[sid]}')

    ax.set_xlabel('α_neural')
    ax.set_ylabel('P2a', color='#2D8E8B')
    ax.set_ylim(0, 1)
    ax2.set_ylabel('dist→P2a-max (degrees)', color='#E07B2C')
    ax2.set_ylim(0, 50)
    ax.set_title(f'{sid} — α_neural sweep')
    ax.legend(loc='lower left', fontsize=8)
    ax2.legend(loc='upper right', fontsize=8)
    ax.grid(alpha=0.3)


def panel_per_color(ax, sid, axis, target_map):
    """Per-color P2a — Bayesian vs Neural-primary vs P2a-max."""
    bay = BAYESIAN_BEST[sid]
    np_pt = NP07[sid]
    oracle = P2A_MAX[sid]

    s_bay = per_color_score(bay[0], bay[1], axis, target_map)
    s_np = per_color_score(np_pt[0], np_pt[1], axis, target_map)
    s_or = per_color_score(oracle[0], oracle[1], axis, target_map)

    x = np.arange(8); width = 0.27
    ax.bar(x - width, s_bay, width, label=f'Bayesian {bay}', color='#E07B2C', alpha=0.85)
    ax.bar(x,         s_np,  width, label=f'Neural-primary {np_pt}', color='#2D8E8B', alpha=0.85)
    ax.bar(x + width, s_or,  width, label=f'P2a-max {oracle}', color='#FFD700',
           edgecolor='black', alpha=0.85)
    ax.set_xticks(x); ax.set_xticklabels(COLOR_NAMES, fontsize=8)
    ax.set_ylabel('per-color P2a score'); ax.set_ylim(0, 1.1)
    ax.set_title(f'{sid} per-color: Bayesian P2a={np.mean(s_bay):.3f} | '
                 f'Neural-primary={np.mean(s_np):.3f} | P2a-max={np.mean(s_or):.3f}')
    ax.legend(loc='upper right', fontsize=8)
    ax.grid(axis='y', alpha=0.3)


# Load α sweep
with open(OUT / 'neural_primary_results.json') as f:
    all_results = json.load(f)

P2A_BAY = {'sub-08': 0.550, 'sub-09': 0.887}
P2A_ORACLE = {'sub-08': 0.613, 'sub-09': 0.950}
NP07 = {  # neural-primary at α=0.7
    'sub-08': (all_results['sub-08'][2]['bs'], all_results['sub-08'][2]['bc']),
    'sub-09': (all_results['sub-09'][2]['bs'], all_results['sub-09'][2]['bc']),
}


def main():
    fig, axes = plt.subplots(3, 2, figsize=(15, 16), dpi=140)

    panel_landscape(axes[0, 0],
                    _THIS.parent / 'results/axis_3way/sub-08_V4_Stockman150_landscape.json',
                    'sub-08', 150.0, NP07['sub-08'], all_results['sub-08'])
    axes[0, 0].set_title('(A) sub-08 deutan landscape — 4 models')

    panel_landscape(axes[0, 1],
                    _THIS.parent / 'results/axis_3way/sub-09_V4_Stockman16ext_landscape.json',
                    'sub-09', 16.0, NP07['sub-09'], all_results['sub-09'])
    axes[0, 1].set_title('(B) sub-09 protan landscape — 4 models')

    panel_alpha_sweep(axes[1, 0], all_results['sub-08'], 'sub-08')
    axes[1, 0].set_title('(C) sub-08 α_neural sweep — DIVERGE (P2a 감소)')

    panel_alpha_sweep(axes[1, 1], all_results['sub-09'], 'sub-09')
    axes[1, 1].set_title('(D) sub-09 α_neural sweep — CONVERGE (P2a-max에 2.8° 도달)')

    panel_per_color(axes[2, 0], 'sub-08', 150.0, SUB08_ORIGINAL_HC_EQUIV)
    panel_per_color(axes[2, 1], 'sub-09',  16.0, SUB09_ORIGINAL_HC_EQUIV)

    fig.suptitle(
        'Neural-primary vs Bayesian vs P2a-max — Dissociation Map\n'
        '★ sub-09: neural ↔ behavior CONVERGE (filter validated)  |  '
        '✗ sub-08: neural ↔ behavior DIVERGE (dissociation finding)',
        fontsize=13, fontweight='bold', y=0.998)
    plt.tight_layout()
    out_png = OUT / 'dissociation_map.png'
    plt.savefig(out_png, dpi=140, bbox_inches='tight')
    plt.savefig(str(out_png).replace('.png', '.pdf'), bbox_inches='tight')
    plt.close()
    print(f'wrote {out_png}')


if __name__ == '__main__':
    main()
