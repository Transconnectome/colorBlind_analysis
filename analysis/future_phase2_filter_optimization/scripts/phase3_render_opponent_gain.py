"""phase3_render_opponent_gain.py — 4-column STIM_LAB visualization of the
two-channel opponent gain (g_LM, g_S) forward + pre-image filter for sub-08
deutan.

Reuses the rendering pattern of `phase3_render_top_candidates.py` and the
STIM_LAB rendering helper at scripts/stim_lab_render.py.

Output: results/phase3_candidates/opponent_gain_fit/visualization.png
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle

_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR))
sys.path.insert(0, str(_THIS_DIR / 'forward_models'))
sys.path.insert(0, str(_THIS_DIR / 'visualization'))

from forward_models.opponent_gain import (
    forward_opponent_gain,
    pre_image_opponent_gain,
)
from stim_lab_render import render_at_hue as _render_stim_lab

OUTDIR = _THIS_DIR.parent / 'results' / 'phase3_candidates' / 'opponent_gain_fit'
OUTDIR.mkdir(parents=True, exist_ok=True)

CVD = 'deutan'
DELTA_LAMBDA = 14.0

TIER1 = [
    (0,   'c1 (red)'),
    (45,  'c2 (orange)'),
    (90,  'c3 (yellow)'),
    (135, 'c4 (green)'),
    (180, 'c5 (cyan)'),
    (225, 'c6 (sky)'),
    (270, 'c7 (blue)'),
    (315, 'c8 (magenta)'),
]


def render_filter(g_LM: float, g_S: float, title: str, outpath: Path) -> None:
    n = len(TIER1)
    fig, axes = plt.subplots(n, 4, figsize=(8.5, 0.65 * n + 1.5),
                             gridspec_kw={'hspace': 0.10, 'wspace': 0.08})
    fig.suptitle(
        f'{title}\n'
        f'Opponent gain  Δλ={DELTA_LAMBDA:.1f}nm  '
        f'g_LM={g_LM:.3f}, g_S={g_S:.3f}  '
        f'(ratio g_S/g_LM={g_S / g_LM:.3f})  '
        f'— sub-08 deutan, frame-mixed CIELab',
        fontsize=9, y=0.995)
    col_titles = ['Original', 'CVD perceives', 'Filtered (pre-image)', 'CVD(Filtered)']
    for ax, ct in zip(axes[0], col_titles):
        ax.set_title(ct, fontsize=9)

    for i, (theta, label) in enumerate(TIER1):
        ax_row = axes[i]
        theta_pre, resid = pre_image_opponent_gain(
            float(theta), CVD, DELTA_LAMBDA, g_LM, g_S)
        theta_cvd, dt = forward_opponent_gain(
            float(theta), CVD, DELTA_LAMBDA, g_LM, g_S)
        theta_cvd_of_pre, _ = forward_opponent_gain(
            theta_pre, CVD, DELTA_LAMBDA, g_LM, g_S)

        rgb_orig = _render_stim_lab(float(theta), dL=0.0)
        rgb_cvd = _render_stim_lab(theta_cvd, dL=0.0)
        rgb_pre = _render_stim_lab(theta_pre, dL=0.0)
        rgb_cvd_of_pre = _render_stim_lab(theta_cvd_of_pre, dL=0.0)

        ax_row[0].add_patch(Rectangle((0, 0), 1, 1, color=rgb_orig))
        ax_row[1].add_patch(Rectangle((0, 0), 1, 1, color=rgb_cvd))
        ax_row[2].add_patch(Rectangle((0, 0), 1, 1, color=rgb_pre))
        ax_row[3].add_patch(Rectangle((0, 0), 1, 1, color=rgb_cvd_of_pre))

        ax_row[0].text(-0.05, 0.5, f'{label}\nθ={theta}°',
                       ha='right', va='center', fontsize=7,
                       transform=ax_row[0].transAxes)
        ax_row[1].text(0.5, -0.02, f'θ_p={theta_cvd:.1f}°  δθ={dt:+.1f}°',
                       ha='center', va='top', fontsize=7,
                       transform=ax_row[1].transAxes)
        ax_row[2].text(0.5, -0.02,
                       f'θ_pre={theta_pre:.1f}°  |r|={abs(resid):.2f}°',
                       ha='center', va='top', fontsize=7,
                       transform=ax_row[2].transAxes)

        for a in ax_row:
            a.set_xticks([])
            a.set_yticks([])
            a.set_xlim(0, 1)
            a.set_ylim(0, 1)
            for sp in a.spines.values():
                sp.set_edgecolor('black')
                sp.set_linewidth(0.5)

    plt.savefig(outpath, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'  → {outpath}')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--g_LM', type=float, default=None,
                        help='(optional) override g_LM; default = fit result')
    parser.add_argument('--g_S', type=float, default=None,
                        help='(optional) override g_S; default = fit result')
    parser.add_argument('--out', type=str, default=str(OUTDIR / 'visualization.png'))
    args = parser.parse_args()

    if args.g_LM is None or args.g_S is None:
        fit_json = OUTDIR / 'fit_result.json'
        if not fit_json.exists():
            sys.exit(f'fit_result.json not found at {fit_json} — run '
                     'phase3_fit_opponent_gain.py first.')
        with open(fit_json) as f:
            fit = json.load(f)
        g_LM = fit['best_g_LM']
        g_S = fit['best_g_S']
        title = (f'Two-channel Opponent Gain (sub-08 deutan, fit)\n'
                 f'best of {fit.get("n_ties_at_best", 1)} tied cells '
                 f'(match={fit["best_match"]:.1f}/{fit["max_possible_match"]:.0f})')
    else:
        g_LM = float(args.g_LM)
        g_S = float(args.g_S)
        title = 'Two-channel Opponent Gain (sub-08 deutan, manual)'

    render_filter(g_LM, g_S, title, Path(args.out))


if __name__ == '__main__':
    main()
