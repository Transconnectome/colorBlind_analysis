"""s5_tregillus_viz_4col.py — 4-col color render for Tregillus R+C L2 fits.

Output:
  results/s5_tregillus/4col_RC_opp_sub-08.{png,pdf}
  results/s5_tregillus/4col_RC_opp_sub-09.{png,pdf}

Best L2 (behav γ) fit per subject (DPS Δλ source, lowest loss in summary.json):
  sub-08 (deutan): Δλ=6.0, g=-2.00 (boundary)
  sub-09 (protan): Δλ=10.0, g=-1.65 (NOT boundary, NOT in zone)

Forward: machado_with_opponent_gain_at (R-G channel gain on retinal change).
"""
from __future__ import annotations
import json
import math
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

_THIS = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS))

from stim_lab_render import render_at_hue
from retinal_cortical import machado_with_opponent_gain_at
from c3_relabel_p2a import (
    hc_name_new, hc_match, SUB08_ORIG_NEW,
)
from c3_relabel_both_subjects import SUB09_ORIG_NEW

OUT = _THIS.parent / 'results' / 's5_tregillus'
OUT.mkdir(parents=True, exist_ok=True)

HUE_8 = [0, 45, 90, 135, 180, 225, 270, 315]
COLOR_LABELS = ['pink', 'red-orange', 'olive', 'green',
                'cyan', 'sky-cyan', 'sky-blue', 'violet']

matplotlib.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Helvetica', 'Arial', 'DejaVu Sans'],
    'font.size': 7.5, 'axes.titlesize': 8.5, 'axes.labelsize': 7.5,
    'xtick.labelsize': 7, 'ytick.labelsize': 7, 'legend.fontsize': 7,
    'axes.linewidth': 0.7, 'pdf.fonttype': 42, 'ps.fonttype': 42,
})


def rc_opp_forward(theta, delta_lambda, g, family):
    """Tregillus R+C forward at arbitrary CIELab angle(s).
    Returns (perceived θ_perc, δθ)."""
    theta_arr = np.atleast_1d(np.asarray(theta, dtype=float))
    _, hue_final, delta_theta = machado_with_opponent_gain_at(
        delta_lambda, g, family, theta_arr)
    return hue_final % 360.0, np.asarray(delta_theta, dtype=float)


def rc_opp_pre_image(target, delta_lambda, g, family, n=3600):
    grid = np.linspace(0, 360, n, endpoint=False)
    fwd, _ = rc_opp_forward(grid, delta_lambda, g, family)
    diff = (fwd - target + 180.0) % 360.0 - 180.0
    return float(grid[int(np.argmin(np.abs(diff)))])


def render_4col(params, family, tmap, title_head, loss_plain,
                color_accent, out_basename):
    delta_lambda = params['delta_lambda']
    g = params['g']
    fwd = lambda t: rc_opp_forward(t, delta_lambda, g, family)
    pre = lambda tgt: rc_opp_pre_image(tgt, delta_lambda, g, family)
    params_str = (fr"$\Delta\lambda$={delta_lambda:.1f} nm, "
                  fr"g={g:+.2f}  (Tregillus opponent R-G gain)")

    details = []
    p2a_total = 0.0
    exact = 0
    for theta in HUE_8:
        tcvd_arr, dt_arr = fwd(float(theta))
        tcvd = float(tcvd_arr[0])
        dt = float(dt_arr[0])
        pred = hc_name_new(tcvd)
        tgt = tmap[theta]
        s = hc_match(pred, tgt)
        p2a_total += s
        if pred == tgt:
            exact += 1
        details.append({'theta': theta, 'tcvd': tcvd, 'dt': dt,
                        'pred': pred, 'tgt': tgt, 'score': s})
    p2a = p2a_total / 8.0

    nrows = len(HUE_8)
    fig, ax = plt.subplots(nrows, 4, figsize=(6.5, 0.7 * nrows + 1.1),
                            gridspec_kw={'hspace': 0.10, 'wspace': 0.05})
    fig.text(0.5, 1.045, title_head, ha='center', fontsize=10,
             color=color_accent, fontweight='bold')
    fig.text(0.5, 1.020, params_str + f"  ·  descriptive P2a={p2a:.3f} ({exact}/8)",
             ha='center', fontsize=9, color=color_accent, fontweight='bold')
    fig.text(0.5, 0.997, loss_plain, ha='center', fontsize=7, color='#555')

    for j, ct in enumerate(['Original', 'CVD perceives',
                            'Filtered (pre-image)', 'CVD(Filtered)']):
        ax[0, j].set_title(ct, fontsize=8.5)

    for i, theta in enumerate(HUE_8):
        det = details[i]
        tcvd = det['tcvd']
        tpre = pre(float(theta))
        tcvd_pre_arr, _ = fwd(tpre)
        tcvd_pre = float(tcvd_pre_arr[0])
        for j, t_render in enumerate([theta, tcvd, tpre, tcvd_pre]):
            rgb = render_at_hue(float(t_render), dL=0.0)
            ax[i, j].imshow(np.array([[rgb]]), aspect='auto')
            ax[i, j].set_xticks([]); ax[i, j].set_yticks([])
        ax[i, 0].set_ylabel(f"c{i+1}\n{COLOR_LABELS[i]}\n{int(theta)}°",
                             rotation=0, ha='right', va='center',
                             fontsize=7.5, labelpad=15)
        s = det['score']
        match = '✓' if s == 1.0 else ('~' if s > 0 else '✗')
        match_color = ('#1a9850' if s == 1.0
                       else ('#fdae61' if s > 0 else '#d73027'))
        ax[i, 1].text(1.06, 0.5,
                       f"sim: {det['pred']}\ntgt: {det['tgt']}\n{match} {s:.2f}\n"
                       f"δ={det['dt']:+.1f}°",
                       transform=ax[i, 1].transAxes, va='center',
                       fontsize=6.5, color=match_color, fontweight='bold')
        ax[i, 2].text(1.06, 0.5, f"δ_pre={tpre - theta:+.0f}°",
                       transform=ax[i, 2].transAxes, va='center',
                       fontsize=6.5, color='#777')

    fig.tight_layout(rect=[0, 0, 0.92, 0.96])
    base = OUT / out_basename
    fig.savefig(f"{base}.png", dpi=200, bbox_inches='tight')
    fig.savefig(f"{base}.pdf", bbox_inches='tight')
    plt.close(fig)
    print(f"  wrote {base.name}.png/pdf  (P2a={p2a:.3f}, {exact}/8 exact)")
    return {'p2a': p2a, 'exact': exact, 'details': details}


def main():
    print("Tregillus R+C 4-col viz (L2 behav γ best fits per S5_tregillus summary)")
    print("=" * 60)

    results = {}

    # sub-08 deutan: Δλ=6.0 (DPS), g=-2.00 — boundary low hit
    results['RC_opp_sub-08'] = render_4col(
        params={'delta_lambda': 6.0, 'g': -2.00},
        family='deutan', tmap=SUB08_ORIG_NEW,
        title_head='sub-08 (deutan) — Tregillus R+C (opponent R-G gain), L2 behav γ',
        loss_plain=('L2 = JND-weighted behav loss  ·  Δλ source: DPS literature  ·  '
                    'g at grid boundary [-2, +2] — true minimum may lie below'),
        color_accent='#6a3d9a',
        out_basename='4col_RC_opp_sub-08',
    )

    # sub-09 protan: Δλ=10.0 (DPS), g=-1.65 — clean (not boundary, not in [-1,0])
    results['RC_opp_sub-09'] = render_4col(
        params={'delta_lambda': 10.0, 'g': -1.65},
        family='protan', tmap=SUB09_ORIG_NEW,
        title_head='sub-09 (protan) — Tregillus R+C (opponent R-G gain), L2 behav γ',
        loss_plain=('L2 = JND-weighted behav loss  ·  Δλ source: DPS literature  ·  '
                    'g=-1.65: over-shoot past full compensation (not in [-1, 0])'),
        color_accent='#6a3d9a',
        out_basename='4col_RC_opp_sub-09',
    )

    out_json = OUT / '4col_RC_opp_summary.json'
    with open(out_json, 'w') as f:
        json.dump({
            'note': 'Tregillus R+C 4-col viz, L2 behav γ best fits',
            'forward_model': 'machado_with_opponent_gain_at (R-G channel gain, B-Y preserved)',
            'g_convention': 'g=0 retinal-only; g=-1 full R-G compensation; '
                            'g<-1 over-shoot; g>0 anti-Machado',
            'cells': {
                k: {'p2a': v['p2a'], 'exact': v['exact']}
                for k, v in results.items()
            },
        }, f, indent=2)
    print(f"\nWrote {out_json}")


if __name__ == '__main__':
    main()
