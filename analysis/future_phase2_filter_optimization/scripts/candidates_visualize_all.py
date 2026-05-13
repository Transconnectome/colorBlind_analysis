"""candidates_visualize_all.py — 4-col + vuln_hue for all 7 candidates.

Generates 4-col rendering for each candidate using fixedW_onlyTest_best_visualize
helpers. Adapts the forward function to use family-aware θ_conf via direct
4-parameter (β_s, β_c, φ_s, φ_c) specification.
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
sys.path.insert(0, str(_THIS_DIR / 'visualization'))

from phase3_candidate_analysis_v2 import (
    hc_name, hc_match_score, SUB08_ORIGINAL_HC_EQUIV,
)
from fixedW_onlyTest_p2a_ranking import SUB09_ORIGINAL_HC_EQUIV
from stim_lab_render import render_at_hue as _render_stim_lab

OUT = _THIS_DIR.parent / 'results' / 'candidates_p2'
OUT.mkdir(parents=True, exist_ok=True)

HUE_8 = [0, 45, 90, 135, 180, 225, 270, 315]
COLOR_LABELS = ['c1 (red)', 'c2 (orange)', 'c3 (yellow)', 'c4 (green)',
                'c5 (cyan)', 'c6 (sky)', 'c7 (blue)', 'c8 (magenta)']


def forward(theta, bs, bc, phi_s, phi_c):
    dt = (bs * np.cos(np.radians(theta - phi_s))
          + bc * np.cos(np.radians(theta - phi_c)))
    return (theta + dt) % 360.0, float(dt)


def pre_image(target_deg, bs, bc, phi_s, phi_c, n_grid=3600):
    grid = np.linspace(0.0, 360.0, n_grid, endpoint=False)
    forwards = np.array([forward(t, bs, bc, phi_s, phi_c)[0] for t in grid])
    diff = (forwards - target_deg + 180.0) % 360.0 - 180.0
    i = int(np.argmin(np.abs(diff)))
    return float(grid[i]), float(diff[i])


def render_4col_4param(sid, cvd_type, color, bs, bc, phi_s, phi_c,
                       target_map, P2a, exact, label, out_path):
    fig, axs = plt.subplots(8, 4, figsize=(11, 17), dpi=140)
    fig.suptitle(
        f"sub-{sid} ({cvd_type}) V4 — {label}  "
        f"β_s={bs:.0f}°, β_c={bc:+.0f}°, φ_s={phi_s:.1f}°, φ_c={phi_c:.1f}°\n"
        f"P2a={P2a:.3f}  exact={exact}/8",
        fontsize=10, fontweight='bold')
    col_titles = ['HC native (target HC)', 'CVD perceives (no filter)',
                  'Filter applied (pre-image)', 'CVD perceives with filter']
    for j, t in enumerate(col_titles):
        axs[0, j].set_title(t, fontsize=9, fontweight='bold')

    for i, theta in enumerate(HUE_8):
        theta_cvd, _ = forward(float(theta), bs, bc, phi_s, phi_c)
        theta_pre, _ = pre_image(float(theta), bs, bc, phi_s, phi_c)
        theta_pre_cvd, _ = forward(theta_pre, bs, bc, phi_s, phi_c)

        def _show(ax, hue_deg):
            rgb = _render_stim_lab(float(hue_deg))
            ax.imshow(np.tile(rgb, (10, 10, 1)))

        # Col 1: HC native
        _show(axs[i, 0], float(theta))
        axs[i, 0].set_ylabel(COLOR_LABELS[i], fontsize=8, rotation=0,
                             labelpad=40, ha='right', va='center')
        # Col 2: CVD perceives (forward)
        _show(axs[i, 1], theta_cvd)
        # Col 3: Filter applied (pre-image)
        _show(axs[i, 2], theta_pre)
        # Col 4: CVD perceives with filter
        _show(axs[i, 3], theta_pre_cvd)

        # Annotations
        target_name = target_map[theta]
        pred = hc_name(theta_cvd)
        score = hc_match_score(pred, target_name)
        mark = '✓' if pred == target_name else ('~' if score > 0 else '✗')
        axs[i, 1].text(0.5, -0.20, f'{pred} {mark}', transform=axs[i, 1].transAxes,
                       ha='center', va='top', fontsize=7, color=color)
        axs[i, 0].text(0.5, -0.20, f'→ {target_name}', transform=axs[i, 0].transAxes,
                       ha='center', va='top', fontsize=7)

        for ax in axs[i, :]:
            ax.set_xticks([]); ax.set_yticks([])

    plt.tight_layout(rect=(0, 0, 1, 0.97))
    plt.savefig(out_path, dpi=140, bbox_inches='tight')
    plt.savefig(str(out_path).replace('.png', '.pdf'), bbox_inches='tight')
    plt.close()
    print(f'wrote {out_path.name}')


def render_delta_theta_plot(candidates_per_subj, sid, out_path):
    """Compare δθ(θ) curves across candidates for one subject."""
    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=140)
    theta_grid = np.linspace(0, 360, 720)
    target_color = '#E07B2C' if sid == '08' else '#2D8E8B'
    styles = ['-', '--', '-.', ':']
    markers = ['o', 's', '^', 'D']
    for k, (label, bs, bc, phi_s, phi_c, p2a, exact) in enumerate(candidates_per_subj):
        dt = (bs * np.cos(np.radians(theta_grid - phi_s))
              + bc * np.cos(np.radians(theta_grid - phi_c)))
        ax.plot(theta_grid, dt, ls=styles[k % 4], lw=1.7,
                label=f'{label}  P2a={p2a:.3f}  ({exact}/8)')
        # Mark 8 stimulus points
        for theta in HUE_8:
            dt_pt = (bs * np.cos(np.radians(theta - phi_s))
                     + bc * np.cos(np.radians(theta - phi_c)))
            ax.plot(theta, dt_pt, marker=markers[k % 4], markersize=6,
                    color=ax.get_lines()[-1].get_color())
    ax.axhline(0, color='gray', lw=0.5, alpha=0.5)
    for theta in HUE_8:
        ax.axvline(theta, color='gray', lw=0.3, alpha=0.3, ls=':')
    ax.set_xlabel('θ (stimulus hue, CIELab degrees)')
    ax.set_ylabel('δθ (perceptual shift, degrees)')
    ax.set_title(f'sub-{sid} — δθ(θ) candidate comparison', fontsize=11, fontweight='bold')
    ax.set_xlim(0, 360); ax.set_xticks(HUE_8)
    ax.legend(loc='best', fontsize=8)
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_path, dpi=140, bbox_inches='tight')
    plt.savefig(str(out_path).replace('.png', '.pdf'), bbox_inches='tight')
    plt.close()
    print(f'wrote {out_path.name}')


def main():
    # Load P2a
    with open(OUT / 'p2_summary.json') as f:
        p2 = json.load(f)
    p2_lookup = {r['label']: r for r in p2['summary']}

    candidates = [
        ('sub-08 β Stockman150',  '08', 'deutan', '#E07B2C', 44.0, +28.0, 90.0, 150.0,  SUB08_ORIGINAL_HC_EQUIV),
        ('sub-08 β CIELab175.7',  '08', 'deutan', '#E07B2C', 50.0, -36.0, 90.0, 175.7,  SUB08_ORIGINAL_HC_EQUIV),
        ('sub-08 α 4D canonical', '08', 'deutan', '#E07B2C', 70.0,  0.0,  90.0, 0.0,    SUB08_ORIGINAL_HC_EQUIV),
        ('sub-08 P2amax Stockman150', '08', 'deutan', '#E07B2C', 26.0, +34.0, 90.0, 150.0, SUB08_ORIGINAL_HC_EQUIV),
        ('sub-09 β Stockman16',   '09', 'protan', '#2D8E8B', 14.0, +60.0, 90.0, 16.0,   SUB09_ORIGINAL_HC_EQUIV),
        ('sub-09 β CIELab11.8',   '09', 'protan', '#2D8E8B', 26.0, +60.0, 90.0, 11.8,   SUB09_ORIGINAL_HC_EQUIV),
        ('sub-09 α 4D canonical', '09', 'protan', '#2D8E8B', 74.0,  0.0,  -25.4, 0.0,   SUB09_ORIGINAL_HC_EQUIV),
        ('sub-09 OLD150wrong',    '09', 'protan', '#2D8E8B', 30.0, +46.0, 90.0, 150.0,  SUB09_ORIGINAL_HC_EQUIV),
        ('sub-09 P2amax Stockman16', '09', 'protan', '#2D8E8B', 24.0, -20.0, 90.0, 16.0, SUB09_ORIGINAL_HC_EQUIV),
        ('sub-09 P2amax CIELab11.8', '09', 'protan', '#2D8E8B', 22.0, -18.0, 90.0, 11.8, SUB09_ORIGINAL_HC_EQUIV),
    ]

    for label, sid, fam, color, bs, bc, phi_s, phi_c, tmap in candidates:
        # map visualization label → p2_summary label
        lookup_label = (label
                        .replace('OLD150wrong', 'OLD wrong')
                        .replace('P2amax Stockman150', 'P2a-max Stockman150')
                        .replace('P2amax Stockman16',  'P2a-max Stockman16')
                        .replace('P2amax CIELab11.8',  'P2a-max CIELab11.8'))
        r = p2_lookup.get(lookup_label, {'p2a': 0, 'exact': 0})
        slug = label.replace(' ', '_').replace('°', 'deg').replace('.', 'p').replace('+', 'p').replace('-', 'm')
        out = OUT / f'4col_{slug}.png'
        render_4col_4param(sid, fam, color, bs, bc, phi_s, phi_c,
                           tmap, r['p2a'], r['exact'], label, out)

    # δθ comparison plots per subject
    sub08_cands = [
        ('β Stockman150',  44.0, +28.0, 90.0, 150.0,
         p2_lookup['sub-08 β Stockman150']['p2a'], p2_lookup['sub-08 β Stockman150']['exact']),
        ('β CIELab175.7',  50.0, -36.0, 90.0, 175.7,
         p2_lookup['sub-08 β CIELab175.7']['p2a'], p2_lookup['sub-08 β CIELab175.7']['exact']),
        ('α 4D canonical (φ=90°)', 70.0, 0.0, 90.0, 0.0,
         p2_lookup['sub-08 α 4D canonical']['p2a'], p2_lookup['sub-08 α 4D canonical']['exact']),
    ]
    render_delta_theta_plot(sub08_cands, '08', OUT / 'delta_theta_sub08.png')

    sub09_cands = [
        ('β Stockman16',  14.0, +60.0, 90.0, 16.0,
         p2_lookup['sub-09 β Stockman16']['p2a'], p2_lookup['sub-09 β Stockman16']['exact']),
        ('β CIELab11.8',  26.0, +60.0, 90.0, 11.8,
         p2_lookup['sub-09 β CIELab11.8']['p2a'], p2_lookup['sub-09 β CIELab11.8']['exact']),
        ('α 4D (φ=-25.4°)', 74.0, 0.0, -25.4, 0.0,
         p2_lookup['sub-09 α 4D canonical']['p2a'], p2_lookup['sub-09 α 4D canonical']['exact']),
        ('OLD150wrong (30,+46)', 30.0, +46.0, 90.0, 150.0,
         p2_lookup['sub-09 OLD wrong']['p2a'], p2_lookup['sub-09 OLD wrong']['exact']),
    ]
    render_delta_theta_plot(sub09_cands, '09', OUT / 'delta_theta_sub09.png')


if __name__ == '__main__':
    main()
