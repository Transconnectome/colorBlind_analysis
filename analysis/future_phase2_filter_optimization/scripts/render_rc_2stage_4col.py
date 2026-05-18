"""render_rc_2stage_4col.py — 4-col viz for R+C 2-stage filter.

Self-contained (no dep on broken OLD-scheme renderer).

Generates:
  CORRECTED_RC_2stage_4col_sub-08.{png,pdf}  — (Δλ=2.5, β_s=38, β_c=-14)
  CORRECTED_RC_2stage_4col_sub-09.{png,pdf}  — (Δλ=19.5, β_s=0, β_c=0)

Uses NEW corrected labels (c3_relabel_p2a.HC_NAME_BINS_NEW) and STIM_LAB rendering.

4 columns per row:
  1. Original stimulus (HC perception)
  2. CVD perceives original (no filter) — forward_rc_2stage(θ_orig, family, Δλ, β_s, β_c)
  3. Filtered stimulus (pre-image) — θ_pre
  4. CVD perceives filtered — forward_rc_2stage(θ_pre, family, Δλ, β_s, β_c) ≈ θ_orig
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

_THIS = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS))
sys.path.insert(0, str(_THIS / 'forward_models'))

from stim_lab_render import render_at_hue
from rc_2stage import forward_rc_2stage, pre_image_rc_2stage
from c3_relabel_p2a import hc_name_new, hc_match, SUB08_ORIG_NEW
from c3_relabel_both_subjects import SUB09_ORIG_NEW

OUT = _THIS.parent / 'results' / 'c3_relabel'

HUE_8 = [0, 45, 90, 135, 180, 225, 270, 315]
# NEW HC names matching STIM_LAB rendering (HC_NAME_BINS_NEW @ ring angles)
COLOR_LABELS = ['pink', 'red-orange', 'olive', 'green',
                'cyan', 'sky-cyan', 'sky-blue', 'violet']

# R+C 2-stage filter parameters per subject (from R+C standalone fits 2026-04-07)
RC_2STAGE = {
    '08': {
        'family': 'deutan', 'axis': 150.0,
        'delta_lambda': 2.5, 'bs': 38.0, 'bc': -14.0,
        'target': SUB08_ORIG_NEW,
        'color': '#2CA02C',
        'note': 'Cortical-dominant (R+C g=-2.25 → cortical 2-comp residual large)',
    },
    '09': {
        'family': 'protan', 'axis': 16.0,
        'delta_lambda': 19.5, 'bs': 0.0, 'bc': 0.0,
        'target': SUB09_ORIG_NEW,
        'color': '#1F77B4',
        'note': 'Retinal-dominant (R+C g=-1.10 near-physiological → cortical residual ≈ 0)',
    },
}

LABEL = 'R+C 2-stage — Sequential retinal Δλ + cortical 2-comp'
LOSS_PLAIN = (
    'Stage 1: Machado(θ, Δλ) at retinal cone shift Δλ_subject  ·  '
    'Stage 2: 2-comp(β_s, β_c) cortical residual on h_retinal  ·  '
    'Composite: θ_perceived = θ_stim + δθ_retinal + δθ_cortical'
)


def p2a_rc(info):
    """Compute P2a for R+C 2-stage filter (uses corrected labels)."""
    bs, bc, dl, axis, fam = info['bs'], info['bc'], info['delta_lambda'], info['axis'], info['family']
    tmap = info['target']
    total = 0.0; ex = 0; details = []
    for theta in HUE_8:
        tcvd, dt = forward_rc_2stage(float(theta), fam, dl, bs, bc, axis_conf=axis)
        pred = hc_name_new(tcvd); tgt = tmap[theta]
        s = hc_match(pred, tgt)
        total += s
        if pred == tgt: ex += 1
        details.append({'theta': theta, 'tcvd': tcvd, 'dt': dt,
                        'pred': pred, 'tgt': tgt, 'score': s})
    return total/8.0, ex, details


def render_rc_4col(sid: str):
    info = RC_2STAGE[sid]
    bs, bc, dl = info['bs'], info['bc'], info['delta_lambda']
    fam, axis = info['family'], info['axis']

    p, ex, details = p2a_rc(info)

    nrows = len(HUE_8)
    fig, ax = plt.subplots(nrows, 4, figsize=(7.0, 0.72*nrows + 1.2),
                            gridspec_kw={'hspace': 0.10, 'wspace': 0.05})
    fig.suptitle(
        f"sub-{sid} ({fam}) — {LABEL}\n"
        fr"$\Delta\lambda$={dl:.1f} nm,  $\beta_s$={bs:.0f}°,  $\beta_c$={bc:+.0f}°,  "
        f"P2a={p:.3f} ({ex}/8)",
        fontsize=10, y=1.005, color=info['color'], fontweight='bold')
    fig.text(0.5, 0.973,
             f"axis={axis:.0f}°  ·  norm(β)={np.hypot(bs, bc):.1f}°  ·  "
             f"{info['note']}",
             ha='center', fontsize=7, color='#555555')

    for j, ct in enumerate(['Original\n(HC perception)',
                            'CVD perceives\n(no filter)',
                            'Filtered\n(pre-image)',
                            'CVD perceives\n(filtered)']):
        ax[0, j].set_title(ct, fontsize=8.0)

    for i, theta in enumerate(HUE_8):
        det = details[i]
        tcvd = det['tcvd']
        tpre, resid = pre_image_rc_2stage(float(theta), fam, dl, bs, bc, axis_conf=axis)
        tcvd_pre, _ = forward_rc_2stage(tpre, fam, dl, bs, bc, axis_conf=axis)
        for j, t_render in enumerate([theta, tcvd, tpre, tcvd_pre]):
            rgb = render_at_hue(float(t_render), dL=0.0)
            ax[i, j].imshow(np.array([[rgb]]), aspect='auto')
            ax[i, j].set_xticks([]); ax[i, j].set_yticks([])
        ax[i, 0].set_ylabel(f"c{i+1}\n{COLOR_LABELS[i]}\n{int(theta)}°",
                             rotation=0, ha='right', va='center',
                             fontsize=7.5, labelpad=15)
        # Match indicator (CVD-no-filter prediction vs subject's report)
        s = det['score']
        match = '✓' if s == 1.0 else ('~' if s > 0 else '✗')
        match_color = '#1a9850' if s == 1.0 else ('#fdae61' if s > 0 else '#d73027')
        ax[i, 1].text(1.06, 0.5,
                       f"sim: {det['pred']}\ntgt: {det['tgt']}\n"
                       f"{match} {s:.2f}",
                       transform=ax[i, 1].transAxes, va='center',
                       fontsize=6.5, color=match_color, fontweight='bold')
        # Filter shift annotation (col 3)
        delta_filter = ((tpre - theta + 180) % 360) - 180
        ax[i, 2].text(1.06, 0.5, f"δ={delta_filter:+.1f}°",
                       transform=ax[i, 2].transAxes, va='center',
                       fontsize=6.5, color='#777')
        # Pre-image residual (col 4)
        ax[i, 3].text(1.06, 0.5, f"err={resid:+.2f}°",
                       transform=ax[i, 3].transAxes, va='center',
                       fontsize=6.0, color='#777')

    fig.tight_layout(rect=[0, 0, 0.91, 0.96])
    base = OUT / f"CORRECTED_RC_2stage_4col_sub-{sid}"
    fig.savefig(f"{base}.png", dpi=200, bbox_inches='tight')
    fig.savefig(f"{base}.pdf", bbox_inches='tight')
    plt.close(fig)
    print(f'  wrote {base.name}.png/pdf')
    return p, ex


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    print('R+C 2-stage 4-col viz (NEW corrected labels)')
    print('=' * 60)
    print(f'Loss form: {LOSS_PLAIN}\n')
    for sid in ['08', '09']:
        info = RC_2STAGE[sid]
        print(f'sub-{sid} ({info["family"]}): '
              f'Δλ={info["delta_lambda"]} nm, β=({info["bs"]:.0f}, {info["bc"]:+.0f})')
        print(f'  → {info["note"]}')
        p, ex = render_rc_4col(sid)
        print(f'  → P2a = {p:.3f} ({ex}/8 exact)\n')
