"""fixedW_onlyTest_two_best_losses.py — Visualization for two behaviorally-best
losses (V4-CCC and cycle12_cross_roi) for sub-08 + sub-09.

Generates into results/fixedW_onlyTest/:
  - fig_F4_V4_V4ccc_fixedWtest.{png,pdf}                       F4-style for V4-CCC
  - 4col_sub-{sid}_V4_{loss}_bs{bs}_bc{bc:+d}.{png,pdf}         4 fig
  - vuln_hue_sub-{sid}_V4_V4CCC_bs{bs}_bc{bc:+d}.{png,pdf}      2 fig

Two candidate losses (best-common across subjects, behaviorally tested):
  - V4-CCC wretrained (OLD CIElab-direct formula): sub-08 (16,+40), sub-09 (30,+46)
  - cycle12_cross_roi (V4 l_topk + V1 l_rank):     sub-08 (68,-38), sub-09 (30,+26)

Forward model (OLD): δθ(θ) = β_s·cos(θ−90°) + β_c·cos(θ−150°)
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
from phase3_loss_variant_helpers import generate_f4_style_figure
from phase3_candidate_analysis_v2 import (
    hc_name, hc_match_score, SUB08_ORIGINAL_HC_EQUIV,
)
from fixedW_onlyTest_p2a_ranking import SUB09_ORIGINAL_HC_EQUIV

_PHASE2 = _THIS_DIR.parent
OUTDIR = _PHASE2 / 'results' / 'fixedW_onlyTest'
OUTDIR.mkdir(parents=True, exist_ok=True)
SRCDIR = _PHASE2 / 'results' / 'old_formula'

THETA_CONF_DEG = 150.0
HUE_ANGLES = [0, 45, 90, 135, 180, 225, 270, 315]
COLOR_LABELS = ['c1 (red)', 'c2 (orange)', 'c3 (yellow)', 'c4 (green)',
                'c5 (cyan)', 'c6 (sky)', 'c7 (blue)', 'c8 (magenta)']

COL_08 = '#E07B2C'
COL_09 = '#2D8E8B'

# Two behaviorally-best losses
ARGMINS = {
    'V4CCC': {
        '08': dict(bs=16, bc=+40, cvd='deutan', color=COL_08, target=SUB08_ORIGINAL_HC_EQUIV),
        '09': dict(bs=30, bc=+46, cvd='protan', color=COL_09, target=SUB09_ORIGINAL_HC_EQUIV),
    },
    'cycle12': {
        '08': dict(bs=68, bc=-38, cvd='deutan', color=COL_08, target=SUB08_ORIGINAL_HC_EQUIV),
        '09': dict(bs=30, bc=+26, cvd='protan', color=COL_09, target=SUB09_ORIGINAL_HC_EQUIV),
    },
}

LOSS_LABEL = {'V4CCC': 'V4-CCC', 'cycle12': 'cycle12_cross_roi'}


# --------------------------- forward / pre-image ---------------------------
def dt_old(theta_deg, bs, bc, theta_conf_deg=THETA_CONF_DEG):
    th = np.deg2rad(theta_deg)
    return (bs * np.cos(th - np.deg2rad(90.0))
            + bc * np.cos(th - np.deg2rad(theta_conf_deg)))


def forward_old(theta_deg, bs, bc):
    dt = dt_old(theta_deg, bs, bc)
    return (theta_deg + dt) % 360.0, dt


def pre_image_old(target_deg, bs, bc, n_grid=3600):
    grid = np.linspace(0.0, 360.0, n_grid, endpoint=False)
    forwards = np.array([forward_old(t, bs, bc)[0] for t in grid])
    diff = (forwards - target_deg + 180.0) % 360.0 - 180.0
    i = int(np.argmin(np.abs(diff)))
    return float(grid[i]), float(diff[i])


# ----------------- 4-col color figure (per loss, per subject) -----------------
def render_4col(sid: str, info: dict, loss_key: str, extra_metric: dict | None,
                out_path_png: Path):
    """Render 8-row x 4-col color figure. P2a annotated using info['target']."""
    bs, bc = info['bs'], info['bc']
    color = info['color']
    cvd = info['cvd']
    target_map = info['target']

    n_rows = len(HUE_ANGLES)
    fig, axes = plt.subplots(n_rows, 4,
                             figsize=(5.5, 0.65 * n_rows + 0.8),
                             gridspec_kw={'hspace': 0.10, 'wspace': 0.05})

    norm = float(np.hypot(bs, bc))
    extra_str = ''
    if extra_metric:
        parts = [f'{k}={v:.3f}' for k, v in extra_metric.items()]
        extra_str = '  ' + ', '.join(parts)

    fig.suptitle(
        f"sub-{sid} ({cvd}) V4 — {LOSS_LABEL[loss_key]} wretrained — "
        f"β_s={bs:.0f}°, β_c={bc:+.0f}°  (norm={norm:.1f}°){extra_str}",
        fontsize=10, y=1.00, color=color, fontweight='bold')

    for j, ct in enumerate(['Original', 'CVD perceives',
                            'Filtered (pre-image)', 'CVD(Filtered)']):
        axes[0, j].set_title(ct, fontsize=8)

    p2a_total = 0.0
    p2a_exact = 0
    for i, theta in enumerate(HUE_ANGLES):
        theta_cvd, dt = forward_old(float(theta), bs, bc)
        theta_pre, _resid = pre_image_old(float(theta), bs, bc)
        theta_cvd_pre, _ = forward_old(theta_pre, bs, bc)

        rgb_orig = _render_stim_lab(float(theta), dL=0.0)
        rgb_cvd = _render_stim_lab(theta_cvd, dL=0.0)
        rgb_pre = _render_stim_lab(theta_pre, dL=0.0)
        rgb_cvd_pre = _render_stim_lab(theta_cvd_pre, dL=0.0)

        for k, rgb in enumerate([rgb_orig, rgb_cvd, rgb_pre, rgb_cvd_pre]):
            ax = axes[i, k]
            ax.add_patch(Rectangle((0, 0), 1, 1, color=rgb))
            ax.set_xticks([]); ax.set_yticks([])
            ax.set_xlim(0, 1); ax.set_ylim(0, 1)
            for sp in ax.spines.values():
                sp.set_edgecolor('black'); sp.set_linewidth(0.5)

        axes[i, 0].text(-0.10, 0.5, f'{COLOR_LABELS[i]}\nθ={theta}°',
                        ha='right', va='center', fontsize=7,
                        transform=axes[i, 0].transAxes)

        # P2a — works for both sub-08 and sub-09 using target_map
        pred_name = hc_name(theta_cvd)
        target_name = target_map[int(theta)]
        score = hc_match_score(pred_name, target_name)
        mark = '✓' if pred_name == target_name else ('~' if score > 0 else '✗')
        color_p2a = 'green' if score == 1.0 else ('darkorange' if score > 0 else 'red')
        axes[i, 1].text(0.5, -0.02, f'δθ={dt:+.0f}° {mark}',
                        ha='center', va='top', fontsize=7,
                        transform=axes[i, 1].transAxes, color=color_p2a)
        p2a_total += score
        if pred_name == target_name:
            p2a_exact += 1

        axes[i, 2].text(0.5, -0.02, f'θ_pre={theta_pre:.0f}°',
                        ha='center', va='top', fontsize=7,
                        transform=axes[i, 2].transAxes)

    fig.text(0.5, -0.005, f'P2a={p2a_total/8:.3f} ({p2a_exact}/8 exact)',
             ha='center', fontsize=8, color=color)
    plt.savefig(out_path_png, dpi=150, bbox_inches='tight')
    plt.savefig(str(out_path_png).replace('.png', '.pdf'), bbox_inches='tight')
    plt.close(fig)
    print(f'  wrote {out_path_png.name} (+ .pdf)  P2a={p2a_total/8:.3f}')
    return p2a_total / 8, p2a_exact


# ----------------- vuln-hue line graph (V4-CCC only) -----------------
def render_vuln_hue(sid: str, info: dict, vuln_cvd, vuln_sim, rho,
                    out_path_png: Path):
    bs, bc = info['bs'], info['bc']
    color = info['color']
    cvd = info['cvd']
    fig, ax = plt.subplots(figsize=(6.5, 3.6), dpi=150)
    x = np.arange(8)
    labels_short = ['R', 'O', 'Y', 'G', 'C', 'B', 'P', 'M']

    ax.axhline(0, color='#aaaaaa', lw=0.5, ls=':')
    ax.plot(x, vuln_cvd, 'o-', color='#222222', ms=6, lw=0.8,
            label='Observed (CVD LOCO)')
    ax.plot(x, vuln_sim, 's-', color=color, ms=6, lw=1.5,
            label=f'V4-CCC wretrained sim (ρ={rho:.3f})')
    ax.set_xticks(x); ax.set_xticklabels(labels_short)
    ax.set_xlabel('Hue (DKL bin)')
    ax.set_ylabel('LOCO vulnerability (voxel_corr)')
    ax.set_title(
        f"sub-{sid} ({cvd}) V4 — V4-CCC wretrained "
        f"argmin β_s={bs:.0f}°, β_c={bc:+.0f}°",
        fontweight='bold', color=color)
    ax.set_ylim(-1.0, 1.0)
    ax.legend(loc='best', fontsize=9)
    ax.spines[['top', 'right']].set_visible(False)
    plt.tight_layout()
    plt.savefig(out_path_png, dpi=150, bbox_inches='tight')
    plt.savefig(str(out_path_png).replace('.png', '.pdf'), bbox_inches='tight')
    plt.close(fig)
    print(f'  wrote {out_path_png.name} (+ .pdf)')


# ----------------- F4 figure for V4-CCC -----------------
def make_f4_v4ccc(out_path: Path):
    """Build F4-style figure for V4-CCC using cached landscape + vuln_cvd."""
    cells_by_sid = {}
    cache_by_sid = {}
    for sid in ('08', '09'):
        ls_path = SRCDIR / f'sub-{sid}_V4_V4ccc_landscape.json'
        cache_path = SRCDIR / f'sub-{sid}_V4_vulnsim_cache.json'
        ls = json.load(open(ls_path))
        cells = ls['cells']
        cache = json.load(open(cache_path))
        cells_by_sid[sid] = cells
        cache_by_sid[sid] = cache

    best_08, best_09 = generate_f4_style_figure(
        variant_name='V4-CCC wretrained (best common loss across subjects)',
        cache_08={'vuln_cvd': cache_by_sid['08']['vuln_cvd']},
        landscape_08=cells_by_sid['08'],
        cache_09={'vuln_cvd': cache_by_sid['09']['vuln_cvd']},
        landscape_09=cells_by_sid['09'],
        out_path=out_path,
        loss_label='L_fit_V4ccc',
        landscape_key='spearman_r',   # task spec: color by Spearman ρ for comparability
        landscape_label='Spearman ρ',
    )
    print(f'  wrote {out_path.name} (+ .pdf)')
    return best_08, best_09, cache_by_sid


# ----------------- main -----------------
def main():
    print(f'OUTDIR: {OUTDIR}')

    # 1. F4-style figure (V4-CCC, color by Spearman ρ)
    print('\n=== F4 V4-CCC (wretrained) ===')
    f4_path = OUTDIR / 'fig_F4_V4_V4ccc_fixedWtest.png'
    best_08_v4, best_09_v4, cache_by_sid = make_f4_v4ccc(f4_path)
    print(f'  sub-08 argmin: β=({best_08_v4["bs"]:.0f},{best_08_v4["bc"]:+.0f}) '
          f'CCC={best_08_v4["ccc"]:.3f} ρ={best_08_v4["spearman_r"]:.3f}')
    print(f'  sub-09 argmin: β=({best_09_v4["bs"]:.0f},{best_09_v4["bc"]:+.0f}) '
          f'CCC={best_09_v4["ccc"]:.3f} ρ={best_09_v4["spearman_r"]:.3f}')

    # 2. 4-col figures (4 total)
    print('\n=== 4-col V4-CCC ===')
    for sid in ('08', '09'):
        info = ARGMINS['V4CCC'][sid]
        # match argmin cell
        cells = json.load(open(SRCDIR / f'sub-{sid}_V4_V4ccc_landscape.json'))['cells']
        cell = next(c for c in cells if c['bs'] == info['bs'] and c['bc'] == info['bc'])
        ccc_val = cell['ccc']; rho = cell['spearman_r']
        out_name = f"4col_sub-{sid}_V4_V4CCC_bs{int(info['bs'])}_bc{int(info['bc']):+d}.png"
        render_4col(sid, info, 'V4CCC',
                    extra_metric={'CCC': ccc_val, 'ρ': rho},
                    out_path_png=OUTDIR / out_name)

    print('\n=== 4-col cycle12_cross_roi ===')
    for sid in ('08', '09'):
        info = ARGMINS['cycle12'][sid]
        out_name = f"4col_sub-{sid}_V4_cycle12_bs{int(info['bs'])}_bc{int(info['bc']):+d}.png"
        render_4col(sid, info, 'cycle12',
                    extra_metric=None,
                    out_path_png=OUTDIR / out_name)

    # 3. vuln-hue line graphs (V4-CCC only)
    print('\n=== vuln-hue V4-CCC ===')
    for sid in ('08', '09'):
        info = ARGMINS['V4CCC'][sid]
        cells = json.load(open(SRCDIR / f'sub-{sid}_V4_V4ccc_landscape.json'))['cells']
        cell = next(c for c in cells if c['bs'] == info['bs'] and c['bc'] == info['bc'])
        vuln_sim = np.array(cell['vuln_sim'])
        rho = cell['spearman_r']
        vuln_cvd = np.array(cache_by_sid[sid]['vuln_cvd'])
        out_name = (f"vuln_hue_sub-{sid}_V4_V4CCC_"
                    f"bs{int(info['bs'])}_bc{int(info['bc']):+d}.png")
        render_vuln_hue(sid, info, vuln_cvd, vuln_sim, rho,
                        OUTDIR / out_name)

    print('\nDone.')


if __name__ == '__main__':
    main()
