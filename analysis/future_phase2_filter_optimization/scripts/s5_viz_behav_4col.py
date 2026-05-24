"""s5_viz_behav_4col.py — 4-col color rendering for S5 behav-path (L2 γ) fits.

Follows existing 4-col convention (cf. p2amax_option_C_visualize.render_4col):
  cols = Original | CVD perceives | Filtered (pre-image) | CVD(Filtered)
  rows = 8 canonical hues (c1=0°..c8=315°)

Models:
  R+C    forward: θ_perc = θ + (2 - g) · δθ_Machado(θ; Δλ, family)
  2-Comp forward: θ_perc = θ + β_s·cos(θ−90°) + β_c·cos(θ−axis)

Renders:
  S5_BEHAV_4col_RC_sub-08.png         (deutan, Δλ=6, g=2.25)
  S5_BEHAV_4col_RC_sub-09.png         (protan, Δλ=10, g=2.60)
  S5_BEHAV_4col_2Comp_sub-08.png      (β_s=48, β_c=−36; marginal model-stability)
  [2Comp sub-09 skipped — cos(R+C, 2-Comp)=0.07 → behav-stability fail per user rule]
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
from machado_simulator import machado_shifted_hue_at
from c3_relabel_p2a import (
    hc_name_new, hc_match,
    SUB08_ORIG_NEW, HC_TARGET_NEW,
)
from c3_relabel_both_subjects import SUB09_ORIG_NEW

OUT = _THIS.parent / 'results' / 's5_all_paths'
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

# ---- forward maps ----------------------------------------------------------

def rc_delta(theta_arr, delta_lambda, g, cvd_family):
    """R+C δθ at given theta(s). Uses machado_shifted_hue_at for arbitrary θ."""
    theta_arr = np.atleast_1d(np.asarray(theta_arr, dtype=float)) % 360.0
    _, _, delta_m = machado_shifted_hue_at(delta_lambda, cvd_family, theta_arr)
    return (2.0 - g) * delta_m

def rc_forward(theta, delta_lambda, g, cvd_family):
    """θ_perc = θ + δθ_RC."""
    theta_arr = np.atleast_1d(np.asarray(theta, dtype=float))
    dt = rc_delta(theta_arr, delta_lambda, g, cvd_family)
    return (theta_arr + dt) % 360.0, dt

def rc_pre_image(target, delta_lambda, g, cvd_family, n=3600):
    grid = np.linspace(0, 360, n, endpoint=False)
    fwd, _ = rc_forward(grid, delta_lambda, g, cvd_family)
    diff = (fwd - target + 180) % 360 - 180
    return float(grid[int(np.argmin(np.abs(diff)))])

def tc_delta(theta, bs, bc, axis):
    th = np.deg2rad(np.atleast_1d(theta))
    return bs * np.cos(th - np.pi / 2) + bc * np.cos(th - np.deg2rad(axis))

def tc_forward(theta, bs, bc, axis):
    dt = tc_delta(theta, bs, bc, axis)
    return (np.atleast_1d(theta) + dt) % 360.0, dt

def tc_pre_image(target, bs, bc, axis, n=3600):
    grid = np.linspace(0, 360, n, endpoint=False)
    fwd, _ = tc_forward(grid, bs, bc, axis)
    diff = (fwd - target + 180) % 360 - 180
    return float(grid[int(np.argmin(np.abs(diff)))])

# ---- core 4-col renderer ---------------------------------------------------

def render_4col(model_kind, params, family, sid, tmap, title_head, loss_plain,
                color_accent, out_basename):
    """model_kind: 'RC' or '2Comp'.
       params: dict — RC: {delta_lambda, g}; 2Comp: {bs, bc, axis}
    """
    if model_kind == 'RC':
        fwd = lambda t: rc_forward(t, params['delta_lambda'], params['g'], family)
        pre = lambda tgt: rc_pre_image(tgt, params['delta_lambda'], params['g'], family)
        params_str = (fr"$\Delta\lambda$={params['delta_lambda']:.1f} nm, "
                      fr"g={params['g']:.2f},  M={max(0, params['g']-1)*params['delta_lambda']:.1f} nm")
    else:
        fwd = lambda t: tc_forward(t, params['bs'], params['bc'], params['axis'])
        pre = lambda tgt: tc_pre_image(tgt, params['bs'], params['bc'], params['axis'])
        params_str = (fr"$\beta_s$={params['bs']:.0f}°, $\beta_c$={params['bc']:+.0f}°,  "
                      fr"axis={params['axis']:.0f}°,  norm={math.hypot(params['bs'], params['bc']):.1f}°")

    # Per-color details
    details = []
    p2a_total = 0.0; exact = 0
    for theta in HUE_8:
        tcvd_arr, dt_arr = fwd(float(theta))
        tcvd = float(tcvd_arr[0]); dt = float(dt_arr[0])
        pred = hc_name_new(tcvd); tgt = tmap[theta]
        s = hc_match(pred, tgt)
        p2a_total += s
        if pred == tgt: exact += 1
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

    for j, ct in enumerate(['Original',
                            'CVD perceives',
                            'Filtered (pre-image)',
                            'CVD(Filtered)']):
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
        match_color = '#1a9850' if s == 1.0 else ('#fdae61' if s > 0 else '#d73027')
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
    # Cells to render — behav-stability rule applied
    # R+C: both subjects (always)
    # 2-Comp: only sub-08 (cos=+0.54 marginal); skip sub-09 (cos=+0.07 fail)

    print("S5 behav-path 4-col rendering (L2 γ-dominant, K=6)")
    print("=" * 60)

    results = {}

    # --- R+C sub-08 deutan ---
    results['RC_sub-08'] = render_4col(
        model_kind='RC',
        params={'delta_lambda': 6.0, 'g': 2.25},
        family='deutan',
        sid='08',
        tmap=SUB08_ORIG_NEW,
        title_head='sub-08 (deutan) — R+C 1-DOF, L2 behav γ fit',
        loss_plain='L2 = JND-weighted behav loss  ·  Δλ source: DPS literature',
        color_accent='#4a78c4',
        out_basename='S5_BEHAV_4col_RC_sub-08',
    )

    # --- R+C sub-09 protan ---
    results['RC_sub-09'] = render_4col(
        model_kind='RC',
        params={'delta_lambda': 10.0, 'g': 2.60},
        family='protan',
        sid='09',
        tmap=SUB09_ORIG_NEW,
        title_head='sub-09 (protan) — R+C 1-DOF, L2 behav γ fit',
        loss_plain='L2 = JND-weighted behav loss  ·  Δλ source: DPS literature',
        color_accent='#4a78c4',
        out_basename='S5_BEHAV_4col_RC_sub-09',
    )

    # --- 2-Comp sub-08 deutan (cos=+0.54 marginal → visualize) ---
    results['2Comp_sub-08'] = render_4col(
        model_kind='2Comp',
        params={'bs': 48.0, 'bc': -36.0, 'axis': 150.0},
        family='deutan',
        sid='08',
        tmap=SUB08_ORIG_NEW,
        title_head='sub-08 (deutan) — 2-Comp, L2 behav γ fit  [model-stability: marginal]',
        loss_plain=('L2 = JND-weighted behav loss  ·  cross-model cos(R+C, 2-Comp)=+0.54, '
                    'sign 7/8, but ‖2-Comp δθ‖ 4× ‖R+C δθ‖'),
        color_accent='#d97a3e',
        out_basename='S5_BEHAV_4col_2Comp_sub-08',
    )

    # --- 2-Comp sub-09: skip ---
    print("\n  SKIP: 2-Comp sub-09 — cos(R+C, 2-Comp)=+0.07 → behav-stability fail")
    print("  (per user rule: visualize 2-Comp behav only when model-stable)")

    out_json = OUT / 'S5_BEHAV_4col_summary.json'
    with open(out_json, 'w') as f:
        json.dump({
            'note': '4-col viz for S5 behav-path L2 fits; 2-Comp sub-09 skipped per behav-stability rule',
            'cells': {
                k: {'p2a': v['p2a'], 'exact': v['exact']} for k, v in results.items()
            },
        }, f, indent=2)
    print(f"\nWrote {out_json}")


if __name__ == '__main__':
    main()
