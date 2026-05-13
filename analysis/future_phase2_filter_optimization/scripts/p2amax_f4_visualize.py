"""p2amax_f4_visualize.py — F4-style vuln_hue + 4-col for P2a-max + current BEST.

비교 군:
  sub-08 axis=Stockman150
    - current BEST (44, +28) P2a=0.575
    - P2a-max     (26, +34) P2a=0.613

  sub-09 axis=Stockman16
    - prior BEST  (14, +60) P2a=0.375
    - P2a-max     (24, -20) P2a=0.950
    - OLD150      (30, +46) P2a=0.650  ← from axis=150° landscape (sub-09 axis150 fine)

각 candidate에 대해:
  (a) vuln_hue: per-color obs vs sim line (8-point), top-3 vulnerable shading
  (b) 4-col: Original / CVD perceives / Filter applied / CVD(Filtered)
  (c) δθ curve (8 points)
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

OUT = _THIS_DIR.parent / 'results' / 'p2amax_F4'
OUT.mkdir(parents=True, exist_ok=True)

HUE_8 = [0, 45, 90, 135, 180, 225, 270, 315]
COLOR_LABELS = ['c1 R(0°)', 'c2 O(45°)', 'c3 Y(90°)', 'c4 G(135°)',
                'c5 C(180°)', 'c6 S(225°)', 'c7 B(270°)', 'c8 M(315°)']
SHORT = ['R', 'O', 'Y', 'G', 'C', 'S', 'B', 'M']
VULN_YLABEL = "LOCO voxel_corr  (↑ preserved / HC-like  |  ↓ vulnerable / CVD-distorted)"


def forward(theta, bs, bc, phi_c, phi_s=90.0):
    dt = (bs * np.cos(np.radians(theta - phi_s))
          + bc * np.cos(np.radians(theta - phi_c)))
    return (theta + dt) % 360.0, float(dt)


def pre_image(target, bs, bc, phi_c, n_grid=3600):
    grid = np.linspace(0, 360, n_grid, endpoint=False)
    forwards = np.array([forward(t, bs, bc, phi_c)[0] for t in grid])
    diff = (forwards - target + 180) % 360 - 180
    i = int(np.argmin(np.abs(diff)))
    return float(grid[i]), float(diff[i])


def load_landscape_cell(path: Path, bs_target: float, bc_target: float):
    with open(path) as f:
        d = json.load(f)
    cells = d['cells']
    for c in cells:
        if abs(c['bs'] - bs_target) < 0.5 and abs(c['bc'] - bc_target) < 0.5:
            return d['theta_conf'], np.array(d['vuln_cvd']), np.array(c['vuln_sim']), c
    return d['theta_conf'], np.array(d['vuln_cvd']), None, None


def render_vuln_hue(ax, vuln_cvd, vuln_sim, label, color, bs, bc, p2a, exact, ccc=None, l_topk=None):
    x = np.arange(8)
    ax.axhline(0, color='#aaaaaa', lw=0.5, ls=':')
    ax.plot(x, vuln_cvd, 'o-', color='#222', ms=6, lw=1.0, label='Observed (CVD LOCO)')
    sim_lab = f'sim @ ({bs:.0f},{bc:+.0f})'
    if ccc is not None: sim_lab += f' CCC={ccc:+.2f}'
    if l_topk is not None: sim_lab += f' l_topk={l_topk:.2f}'
    ax.plot(x, vuln_sim, 's-', color=color, ms=7, lw=1.6, label=sim_lab)
    top3_obs = np.argsort(vuln_cvd)[:3]
    for idx in top3_obs:
        ax.axvspan(idx-0.4, idx+0.4, alpha=0.10, color=color, zorder=0)
    ax.set_xticks(x); ax.set_xticklabels(SHORT)
    ax.set_ylim(-1.0, 1.0)
    ax.set_title(label + f'  P2a={p2a:.3f} ({exact}/8)',
                 fontsize=10, fontweight='bold', color=color)
    ax.set_xlabel('Hue bin (shaded = top-3 vulnerable in obs)')
    ax.set_ylabel(VULN_YLABEL, fontsize=7)
    ax.legend(loc='lower right', fontsize=7)
    ax.spines[['top', 'right']].set_visible(False)


def render_4col_compact(axes_row, bs, bc, phi_c, target_map, color, p2a, exact):
    for i, theta in enumerate(HUE_8):
        theta_cvd, dt = forward(theta, bs, bc, phi_c)
        theta_pre, _ = pre_image(float(theta), bs, bc, phi_c)
        theta_cvd_pre, _ = forward(theta_pre, bs, bc, phi_c)

        rgb_orig = _render_stim_lab(float(theta))
        rgb_cvd = _render_stim_lab(theta_cvd)
        rgb_pre = _render_stim_lab(theta_pre)
        rgb_cvd_pre = _render_stim_lab(theta_cvd_pre)

        for k, rgb in enumerate([rgb_orig, rgb_cvd, rgb_pre, rgb_cvd_pre]):
            ax = axes_row[i, k]
            ax.add_patch(Rectangle((0, 0), 1, 1, color=rgb))
            ax.set_xticks([]); ax.set_yticks([])
            ax.set_xlim(0, 1); ax.set_ylim(0, 1)
            for sp in ax.spines.values():
                sp.set_edgecolor('black'); sp.set_linewidth(0.4)

        axes_row[i, 0].text(-0.05, 0.5, f'c{i+1}\nθ={theta}°',
                            ha='right', va='center', fontsize=6,
                            transform=axes_row[i, 0].transAxes)

        pred = hc_name(theta_cvd)
        target = target_map[theta]
        score = hc_match_score(pred, target)
        mark = '✓' if pred == target else ('~' if score > 0 else '✗')
        color_p2a = 'green' if score == 1.0 else ('darkorange' if score > 0 else 'red')
        axes_row[i, 1].text(0.5, -0.05, f'{pred} {mark}',
                            ha='center', va='top', fontsize=6,
                            transform=axes_row[i, 1].transAxes, color=color_p2a)


def render_F4_panel(sid, family, color, candidates, out_path):
    """F4-style: top row = vuln_hue lines per candidate; bottom = 4-col rendering matrix per candidate."""
    n_cand = len(candidates)
    fig = plt.figure(figsize=(6.5 * n_cand, 12.5), dpi=140)
    gs = fig.add_gridspec(2, n_cand, height_ratios=[1, 3], hspace=0.18, wspace=0.15)

    # Top row: vuln_hue per candidate
    for ci, cand in enumerate(candidates):
        ax = fig.add_subplot(gs[0, ci])
        render_vuln_hue(ax, cand['vuln_cvd'], cand['vuln_sim'],
                        cand['label'], color,
                        cand['bs'], cand['bc'],
                        cand['p2a'], cand['exact'],
                        ccc=cand.get('ccc'), l_topk=cand.get('l_topk'))

    # Bottom row: 4-col matrices per candidate
    for ci, cand in enumerate(candidates):
        gs_sub = gs[1, ci].subgridspec(8, 4, hspace=0.06, wspace=0.06)
        axes = np.empty((8, 4), dtype=object)
        for i in range(8):
            for k in range(4):
                axes[i, k] = fig.add_subplot(gs_sub[i, k])
        # Header titles for cols (place above row 0)
        col_titles = ['Original', 'CVD perceives', 'Filter', 'CVD(Filter)']
        for k, t in enumerate(col_titles):
            axes[0, k].set_title(t, fontsize=7, pad=2)
        render_4col_compact(axes, cand['bs'], cand['bc'], cand['phi_c'],
                            cand['target_map'], color,
                            cand['p2a'], cand['exact'])

    fig.suptitle(f"sub-{sid} ({family}) V4 — Candidate F4 comparison "
                 f"(vuln_hue line + 4-col rendering)",
                 fontsize=12, fontweight='bold', color=color, y=0.995)
    plt.savefig(out_path, dpi=140, bbox_inches='tight')
    plt.savefig(str(out_path).replace('.png', '.pdf'), bbox_inches='tight')
    plt.close()
    print(f'wrote {out_path.name}')


def main():
    # Sub-08 candidates
    sub08_candidates = []
    for label, bs, bc, axis, axis_path in [
        ('Current BEST (44,+28)', 44.0, +28.0, 150.0,
         'results/axis_3way/sub-08_V4_Stockman150_landscape.json'),
        ('P2a-max (26,+34)',      26.0, +34.0, 150.0,
         'results/axis_3way/sub-08_V4_Stockman150_landscape.json'),
        ('CIELab P2a-max (40,+30)', 40.0, +30.0, 175.7,
         'results/axis_3way/sub-08_V4_CIELab175p7_landscape.json'),
    ]:
        theta_conf, vuln_cvd, vuln_sim, cell = load_landscape_cell(
            Path(axis_path), bs, bc)
        if vuln_sim is None:
            print(f'SKIP {label} — cell not found')
            continue
        p2a, exact = 0, 0
        total = 0.0
        for theta in HUE_8:
            theta_cvd, _ = forward(float(theta), bs, bc, axis)
            pred = hc_name(theta_cvd)
            target = SUB08_ORIGINAL_HC_EQUIV[theta]
            s = hc_match_score(pred, target)
            total += s
            if pred == target: exact += 1
        p2a = total / 8
        sub08_candidates.append({
            'label': f'{label}\n(axis={axis}°)',
            'bs': bs, 'bc': bc, 'phi_c': axis,
            'vuln_cvd': vuln_cvd, 'vuln_sim': vuln_sim,
            'p2a': p2a, 'exact': exact,
            'ccc': cell.get('ccc'), 'l_topk': cell.get('l_topk'),
            'target_map': SUB08_ORIGINAL_HC_EQUIV,
        })

    render_F4_panel('08', 'deutan', '#E07B2C', sub08_candidates,
                    OUT / 'F4_sub-08_candidates.png')

    # Sub-09 candidates
    sub09_candidates = []
    for label, bs, bc, axis, axis_path in [
        ('Stockman16 fit BEST (14,+60)', 14.0, +60.0,  16.0,
         'results/axis_3way/sub-09_V4_Stockman16_landscape.json'),
        ('Stockman16 P2a-max (24,-20)',  24.0, -20.0,  16.0,
         'results/axis_3way/sub-09_V4_Stockman16_landscape.json'),
        ('CIELab11.8 P2a-max (22,-18)',  22.0, -18.0,  11.8,
         'results/axis_3way/sub-09_V4_CIELab11p8_landscape.json'),
        ('axis150 BEST/OLD wrong (22,+52)', 22.0, +52.0, 150.0,
         'results/axis_3way/sub-09_V4_axis150_fine_landscape.json'),
    ]:
        theta_conf, vuln_cvd, vuln_sim, cell = load_landscape_cell(
            Path(axis_path), bs, bc)
        if vuln_sim is None:
            print(f'SKIP {label} — cell not found')
            continue
        total = 0.0; exact = 0
        for theta in HUE_8:
            theta_cvd, _ = forward(float(theta), bs, bc, axis)
            pred = hc_name(theta_cvd)
            target = SUB09_ORIGINAL_HC_EQUIV[theta]
            s = hc_match_score(pred, target)
            total += s
            if pred == target: exact += 1
        p2a = total / 8
        sub09_candidates.append({
            'label': f'{label}\n(axis={axis}°)',
            'bs': bs, 'bc': bc, 'phi_c': axis,
            'vuln_cvd': vuln_cvd, 'vuln_sim': vuln_sim,
            'p2a': p2a, 'exact': exact,
            'ccc': cell.get('ccc'), 'l_topk': cell.get('l_topk'),
            'target_map': SUB09_ORIGINAL_HC_EQUIV,
        })

    render_F4_panel('09', 'protan', '#2D8E8B', sub09_candidates,
                    OUT / 'F4_sub-09_candidates.png')


if __name__ == '__main__':
    main()
