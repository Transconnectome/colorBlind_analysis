"""p2amax_option_C_visualize.py — Detailed visualization for Option C.

Option C — Pure neural, heavy-Tikh sign-self-disambiguation:
  L = 0.3·L_topk + 0.3·L_mse + 0.3·L_rdmV1 + 3.0·L_Tikh
  s8 (40, +26) P2a=0.575 | s9 (12, -28) P2a=0.738

Outputs:
  P2AMAX_C_4col_sub-{08,09}.png/pdf  — 4-column color rendering
  P2AMAX_C_F4.png/pdf                — Integrated F4 (vuln + dt + landscape + P2a)
  P2AMAX_C_landscape_sub-{08,09}.png/pdf — L_C landscape with marker
  P2AMAX_C_vuln_hue.png/pdf          — Vulnerability line graph
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

_THIS = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS))

from stim_lab_render import render_at_hue as _render_stim_lab
from phase3_candidate_analysis_v2 import (
    hc_name, hc_match_score, SUB08_ORIGINAL_HC_EQUIV,
)
# Inlined from fixedW_onlyTest_p2a_ranking.py (deleted 2026-05-16 as OLD-scheme leaf).
# For NEW work, use c3_relabel_both_subjects.SUB09_ORIG_NEW instead — this OLD dict
# remains here only to keep this file's render functions runnable.
SUB09_ORIGINAL_HC_EQUIV = {
    0:   "pink", 45:  "orange", 90:  "yellow-green",
    135: "yellow-green", 180: "sky", 225: "sky",
    270: "blue", 315: "violet",
}
# Inlined from p2amax_neural_only_loss.py (deleted 2026-05-16, untracked).
# These helpers were OLD-scheme P2a computation; for NEW work use c3_relabel_p2a.
TARGET = {'08': SUB08_ORIGINAL_HC_EQUIV, '09': SUB09_ORIGINAL_HC_EQUIV}

def load_neural_grids(*args, **kwargs):
    """Stub — original loader for OLD landscape grids. Returns empty for safety."""
    return {}

def p2a_one(bs, bc, axis, target_map):
    """Stub — original OLD-scheme P2a one-cell computation.

    NEW work should use c3_relabel_both_subjects.p2a_corrected instead.
    This stub returns (P2a, exact_count) using OLD HC bins.
    """
    HUE_ANGLES = [0, 45, 90, 135, 180, 225, 270, 315]
    THETA_CONF_DEG = float(axis) if axis is not None else 150.0
    scores = []
    exact = 0
    for theta_orig in HUE_ANGLES:
        dt = (bs * np.cos(np.radians(theta_orig - 90.0))
              + bc * np.cos(np.radians(theta_orig - THETA_CONF_DEG)))
        theta_cvd = (theta_orig + dt) % 360.0
        pred = hc_name(theta_cvd)
        tgt = target_map.get(theta_orig, '')
        sc = hc_match_score(pred, tgt)
        scores.append(sc)
        if sc >= 0.99:
            exact += 1
    p2a = float(np.mean(scores))
    return p2a, exact

OUT = _THIS.parent / 'results'
PREFIX = 'P2AMAX_C_'
HUE_8 = [0, 45, 90, 135, 180, 225, 270, 315]
# NEW HC names matching STIM_LAB rendering (HC_NAME_BINS_NEW @ ring angles)
# OLD design-intent labels ('red','orange','yellow','green','cyan','blue','purple','magenta')
# deprecated 2026-05-17 — use these NEW perceptual labels for consistency with viz pixels
COLOR_LABELS = ['pink', 'red-orange', 'olive', 'green',
                'cyan', 'sky-cyan', 'sky-blue', 'violet']

OPTION_C = {
    'label': 'Option C — Pure neural + heavy Tikh',
    'loss_plain': 'L = 0.3·L_topk + 0.3·L_mse + 0.3·L_rdmV1 + 3.0·L_Tikh',
    'loss_tex':   r'$L = 0.3\,L_{\mathrm{topk}} + 0.3\,L_{\mathrm{mse}} + 0.3\,L_{\mathrm{rdmV1}} + 3.0\,\mathrm{Tikh}$',
    'subjects': {
        '08': {'bs': 40.0, 'bc': +26.0, 'family': 'deutan', 'axis': 150.0,
               'target': SUB08_ORIGINAL_HC_EQUIV, 'color': '#2CA02C',
               'landscape': 'results/axis_3way/sub-08_V4_Stockman150_landscape.json'},
        '09': {'bs': 12.0, 'bc': -28.0, 'family': 'protan', 'axis': 16.0,
               'target': SUB09_ORIGINAL_HC_EQUIV, 'color': '#2CA02C',
               'landscape': 'results/axis_3way/sub-09_V4_Stockman16_landscape.json'},
    },
}

matplotlib.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Helvetica', 'Arial', 'DejaVu Sans'],
    'font.size': 7.5, 'axes.titlesize': 8.5, 'axes.labelsize': 7.5,
    'xtick.labelsize': 7, 'ytick.labelsize': 7, 'legend.fontsize': 7,
    'axes.linewidth': 0.7, 'xtick.major.width': 0.7, 'ytick.major.width': 0.7,
    'pdf.fonttype': 42, 'ps.fonttype': 42,
})


def dt_2comp(theta, bs, bc, axis):
    th = np.deg2rad(theta)
    return bs * np.cos(th - np.pi/2) + bc * np.cos(th - np.deg2rad(axis))


def forward(theta, bs, bc, axis):
    dt = dt_2comp(theta, bs, bc, axis)
    return (theta + dt) % 360.0, dt


def pre_image(target, bs, bc, axis, n=3600):
    grid = np.linspace(0, 360, n, endpoint=False)
    fwd = (grid + dt_2comp(grid, bs, bc, axis)) % 360.0
    diff = (fwd - target + 180) % 360 - 180
    i = int(np.argmin(np.abs(diff)))
    return grid[i]


def p2a_compute(bs, bc, axis, tmap):
    total = 0.0; ex = 0; details = []
    for theta in HUE_8:
        tcvd, dt = forward(float(theta), bs, bc, axis)
        pred = hc_name(tcvd); tgt = tmap[theta]
        s = hc_match_score(pred, tgt)
        total += s
        if pred == tgt: ex += 1
        details.append({'theta': theta, 'tcvd': tcvd, 'dt': dt,
                        'pred': pred, 'tgt': tgt, 'score': s})
    return total/8.0, ex, details


def render_4col(sid):
    info = OPTION_C['subjects'][sid]
    bs, bc, axis = info['bs'], info['bc'], info['axis']
    p, ex, details = p2a_compute(bs, bc, axis, info['target'])

    nrows = len(HUE_8)
    fig, ax = plt.subplots(nrows, 4, figsize=(6.5, 0.7*nrows + 1.1),
                            gridspec_kw={'hspace': 0.10, 'wspace': 0.05})
    fig.text(0.5, 1.040,
             f"sub-{sid} ({info['family']}) — {OPTION_C['label']}",
             ha='center', fontsize=10, color=info['color'], fontweight='bold')
    fig.text(0.5, 1.015,
             fr"$\beta_s$={bs:.0f}°, $\beta_c$={bc:+.0f}°,  P2a={p:.3f} ({ex}/8)"
             f"  ·  axis={axis:.0f}°  ·  norm={np.hypot(bs,bc):.1f}°",
             ha='center', fontsize=9, color=info['color'], fontweight='bold')
    fig.text(0.5, 0.992,
             f"{OPTION_C['loss_plain']}",
             ha='center', fontsize=7, color='#555555')

    for j, ct in enumerate(['Original', 'CVD perceives',
                            'Filtered (pre-image)', 'CVD(Filtered)']):
        ax[0, j].set_title(ct, fontsize=8.5)

    for i, theta in enumerate(HUE_8):
        det = details[i]
        tcvd = det['tcvd']
        tpre = pre_image(float(theta), bs, bc, axis)
        tcvd_pre, _ = forward(tpre, bs, bc, axis)
        for j, t_render in enumerate([theta, tcvd, tpre, tcvd_pre]):
            rgb = _render_stim_lab(float(t_render), dL=0.0)
            ax[i, j].imshow(np.array([[rgb]]), aspect='auto')
            ax[i, j].set_xticks([]); ax[i, j].set_yticks([])
        ax[i, 0].set_ylabel(f"c{i+1}\n{COLOR_LABELS[i]}\n{int(theta)}°",
                             rotation=0, ha='right', va='center',
                             fontsize=7.5, labelpad=15)
        # Match indicator
        s = det['score']
        match = '✓' if s == 1.0 else ('~' if s > 0 else '✗')
        match_color = '#1a9850' if s == 1.0 else (
            '#fdae61' if s > 0 else '#d73027')
        ax[i, 1].text(1.06, 0.5,
                       f"sim: {det['pred']}\ntgt: {det['tgt']}\n"
                       f"{match} {s:.2f}",
                       transform=ax[i, 1].transAxes, va='center',
                       fontsize=6.5, color=match_color, fontweight='bold')
        # δθ for col 3 (filter)
        ax[i, 2].text(1.06, 0.5, f"δ={tpre - theta:+.0f}°",
                       transform=ax[i, 2].transAxes, va='center',
                       fontsize=6.5, color='#777')

    fig.tight_layout(rect=[0, 0, 0.92, 0.96])
    base = OUT / f"{PREFIX}4col_sub-{sid}"
    fig.savefig(f"{base}.png", dpi=200, bbox_inches='tight')
    fig.savefig(f"{base}.pdf", bbox_inches='tight')
    plt.close(fig)
    print(f'  wrote {base.name}.png/pdf')


def render_F4():
    """Integrated F4: vuln line + δθ profile + landscape + P2a bar."""
    fig = plt.figure(figsize=(14, 8.5))
    gs = GridSpec(2, 3, figure=fig, hspace=0.42, wspace=0.30,
                   width_ratios=[1.15, 1, 1.15])

    vuln_obs = {}
    for sid in ['08','09']:
        path = (_THIS.parent /
                f"results/axis_3way/sub-{sid}_V4_Stockman"
                f"{'150' if sid=='08' else '16'}_landscape.json")
        with open(path) as f:
            d = json.load(f)
        vuln_obs[sid] = np.array(d['vuln_cvd'])

    for row, sid in enumerate(['08','09']):
        info = OPTION_C['subjects'][sid]
        bs, bc, axis = info['bs'], info['bc'], info['axis']
        p, ex, details = p2a_compute(bs, bc, axis, info['target'])
        V_obs = vuln_obs[sid]
        V_sim = np.array([bs*np.cos(np.deg2rad(t-90)) + bc*np.cos(np.deg2rad(t-axis))
                          for t in HUE_8])
        dt_arr = np.array([d['dt'] for d in details])

        # Panel 1: vuln_obs vs δθ_sim
        ax = fig.add_subplot(gs[row, 0])
        x = np.arange(8)
        ax2 = ax.twinx()
        ax.bar(x - 0.18, dt_arr, width=0.36, color=info['color'],
                alpha=0.7, label=r'$\delta\theta$ (sim)', edgecolor='black',
                linewidth=0.5)
        ax2.plot(x, V_obs, '-o', color='#222', markersize=5, linewidth=1.2,
                  label='V4 LOCO vuln (obs)')
        ymax = max(abs(dt_arr).max(), 1.0)
        for i, det in enumerate(details):
            cm = '#1a9850' if det['score']==1.0 else (
                '#fdae61' if det['score']>0 else '#d73027')
            ax.scatter(i, ymax*1.10, marker='o', s=40, color=cm,
                        edgecolor='black', linewidth=0.5, zorder=5)
        ax.set_xticks(x)
        ax.set_xticklabels([f'c{k+1}\n{COLOR_LABELS[k][:3]}' for k in range(8)],
                            fontsize=6.5)
        ax.set_ylabel(r'$\delta\theta$ (deg, sim)', fontsize=8)
        ax2.set_ylabel('V4 LOCO vuln (obs)', fontsize=8, color='#333')
        ax.set_title(f"sub-{sid} ({info['family']})  Panel A: δθ + vuln",
                     fontsize=8.5, color=info['color'])
        ax.axhline(0, color='gray', lw=0.4)
        if row == 0:
            l1, lab1 = ax.get_legend_handles_labels()
            l2, lab2 = ax2.get_legend_handles_labels()
            ax.legend(l1+l2, lab1+lab2, loc='upper left',
                       fontsize=6.5, framealpha=0.85)

        # Panel 2: per-color P2a bars
        ax = fig.add_subplot(gs[row, 1])
        colors_p = ['#1a9850' if d['score']==1.0 else (
            '#fdae61' if d['score']>0 else '#d73027') for d in details]
        ax.bar(x, [d['score'] for d in details], color=colors_p,
                edgecolor='black', linewidth=0.5)
        ax.set_xticks(x)
        ax.set_xticklabels([f'c{k+1}' for k in range(8)], fontsize=7)
        ax.set_ylim(0, 1.05)
        ax.set_ylabel('P2a per-color score', fontsize=8)
        ax.set_title(f"Panel B: P2a={p:.3f} ({ex}/8 exact)",
                     fontsize=8.5, color=info['color'])
        ax.axhline(0.5, color='gray', lw=0.4, linestyle='--')
        for i, det in enumerate(details):
            ax.text(i, det['score']+0.04, det['pred'], rotation=70,
                     ha='center', va='bottom', fontsize=5.5, color='#333')
            ax.text(i, -0.07, f"→{det['tgt']}", rotation=70,
                     ha='center', va='top', fontsize=5.5, color='#555')

        # Panel 3: L_C landscape
        ax = fig.add_subplot(gs[row, 2])
        with open(_THIS.parent / info['landscape']) as f:
            d = json.load(f)
        bs_g = np.arange(d['grid']['bs'][0], d['grid']['bs'][1]+0.001,
                         d['grid']['bs'][2])
        bc_g = np.arange(d['grid']['bc'][0], d['grid']['bc'][1]+0.001,
                         d['grid']['bc'][2])
        L_combined = np.full((len(bs_g), len(bc_g)), np.nan)
        for c in d['cells']:
            i_ = int(round((c['bs']-d['grid']['bs'][0])/d['grid']['bs'][2]))
            j_ = int(round((c['bc']-d['grid']['bc'][0])/d['grid']['bc'][2]))
            L_combined[i_, j_] = c['L_combined']
        p5, p95 = np.nanpercentile(L_combined, [5, 95])
        pcm = ax.pcolormesh(bc_g, bs_g, L_combined, cmap='viridis_r',
                             vmin=p5, vmax=p95, shading='auto')
        plt.colorbar(pcm, ax=ax, label='cached L_combined', shrink=0.85)
        ax.scatter(bc, bs, marker='*', s=320, color='red',
                    edgecolor='black', linewidth=1.0,
                    label=f'Option C ({bs:.0f}, {bc:+.0f})', zorder=5)
        ax.set_xlabel(r'$\beta_c$ (deg)', fontsize=8)
        ax.set_ylabel(r'$\beta_s$ (deg)', fontsize=8)
        ax.set_title(f"Panel C: cached landscape + Option C marker",
                     fontsize=8.5, color=info['color'])
        ax.legend(loc='lower right', fontsize=6.5)

    fig.suptitle(
        f"Option C — Pure neural + heavy Tikh (avg P2a = 0.656)\n"
        f"{OPTION_C['loss_plain']}",
        fontsize=11, y=0.995, fontweight='bold', color='#2CA02C')
    fig.tight_layout(rect=[0, 0.01, 1, 0.96])
    base = OUT / f"{PREFIX}F4"
    fig.savefig(f"{base}.png", dpi=200, bbox_inches='tight')
    fig.savefig(f"{base}.pdf", bbox_inches='tight')
    plt.close(fig)
    print(f'  wrote {base.name}.png/pdf')


def render_vuln_hue():
    """Vulnerability line graph for both subjects under Option C."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5),
                              gridspec_kw={'wspace': 0.25})

    for col, sid in enumerate(['08','09']):
        info = OPTION_C['subjects'][sid]
        bs, bc, axis = info['bs'], info['bc'], info['axis']
        p, ex, details = p2a_compute(bs, bc, axis, info['target'])
        with open(_THIS.parent / info['landscape']) as f:
            d = json.load(f)
        V_obs = np.array(d['vuln_cvd'])
        bs_step = d['grid']['bs'][2]; bc_step = d['grid']['bc'][2]
        bs_min = d['grid']['bs'][0]; bc_min = d['grid']['bc'][0]
        i = int(round((bs-bs_min)/bs_step))
        j = int(round((bc-bc_min)/bc_step))
        target_cell = None
        for c in d['cells']:
            ii = int(round((c['bs']-bs_min)/bs_step))
            jj = int(round((c['bc']-bc_min)/bc_step))
            if ii == i and jj == j:
                target_cell = c
                break
        V_sim = np.array(target_cell['vuln_sim']) if target_cell else None

        ax = axes[col]
        x = np.arange(8)
        ax.plot(x, V_obs, '-o', color='#222', markersize=7, linewidth=1.5,
                 label='V4 LOCO vuln (observed)')
        if V_sim is not None:
            ax.plot(x, V_sim, '-s', color=info['color'], markersize=6,
                     linewidth=1.5, alpha=0.85,
                     label='V4 LOCO vuln (simulated)')
        ax.axhline(0, color='gray', lw=0.5)
        ax.set_xticks(x)
        ax.set_xticklabels([f'c{k+1}\n{COLOR_LABELS[k]}' for k in range(8)],
                            fontsize=7.5)
        ax.set_ylabel("LOCO voxel_corr\n(↑ preserved/HC-like  |  ↓ vulnerable/CVD-distorted)",
                       fontsize=8)
        ax.set_title(f"sub-{sid} ({info['family']}) — Option C "
                     fr"($\beta_s$={bs:.0f}°, $\beta_c$={bc:+.0f}°)"
                     f"  P2a={p:.3f} ({ex}/8)",
                     fontsize=9, color=info['color'])
        ax.legend(loc='best', fontsize=7.5, framealpha=0.85)

    fig.suptitle(
        'Option C: V4 LOCO vulnerability — Simulated vs Observed',
        fontsize=11, y=1.01, fontweight='bold')
    fig.tight_layout()
    base = OUT / f"{PREFIX}vuln_hue"
    fig.savefig(f"{base}.png", dpi=200, bbox_inches='tight')
    fig.savefig(f"{base}.pdf", bbox_inches='tight')
    plt.close(fig)
    print(f'  wrote {base.name}.png/pdf')


def render_decision_panel():
    """Single-page decision panel comparing A vs C — for paper/decision use."""
    fig, axes = plt.subplots(2, 2, figsize=(11, 9),
                              gridspec_kw={'hspace': 0.32, 'wspace': 0.22})

    options = {
        'A_lit': {
            'label': 'A — Lit-anchored\n(avg P2a 0.738)',
            'color': '#1F77B4',
            'loss': 'L_ccc + 0.3·Emery + 0.3·Tregillus + 0.3·Brettel + 0.1·Tikh',
            'subjects': {'08': (22, 18), '09': (22, -16)},
        },
        'C_neural': {
            'label': 'C — Pure neural + heavy Tikh\n(avg P2a 0.656)',
            'color': '#2CA02C',
            'loss': '0.3·L_topk + 0.3·L_mse + 0.3·L_rdmV1 + 3.0·L_Tikh',
            'subjects': {'08': (40, 26), '09': (12, -28)},
        },
    }

    SID_AXES = {'08': 150.0, '09': 16.0}
    SID_TMAPS = {'08': SUB08_ORIGINAL_HC_EQUIV, '09': SUB09_ORIGINAL_HC_EQUIV}

    for row, sid in enumerate(['08', '09']):
        for col, (key, opt) in enumerate(options.items()):
            ax = axes[row, col]
            bs, bc = opt['subjects'][sid]
            p, ex, details = p2a_compute(bs, bc, SID_AXES[sid], SID_TMAPS[sid])
            x = np.arange(8)
            # Per-color score bars + color names
            colors_p = ['#1a9850' if d['score']==1.0 else (
                '#fdae61' if d['score']>0 else '#d73027') for d in details]
            ax.bar(x, [d['score'] for d in details], color=colors_p,
                    edgecolor='black', linewidth=0.5)
            ax.set_ylim(0, 1.15)
            ax.set_xticks(x)
            ax.set_xticklabels([f'c{k+1}' for k in range(8)], fontsize=8)
            ax.set_ylabel('P2a per-color', fontsize=8.5)
            fam = 'deutan' if sid=='08' else 'protan'
            ax.set_title(
                f"sub-{sid} {fam} · {opt['label']}\n"
                fr"$\beta_s$={bs}°, $\beta_c$={bc:+d}°,  P2a={p:.3f} ({ex}/8)",
                fontsize=9, color=opt['color'])
            ax.axhline(0.5, color='gray', lw=0.4, linestyle='--')
            for i, det in enumerate(details):
                ax.text(i, det['score']+0.05,
                         f"{det['pred']}\n→{det['tgt']}",
                         ha='center', va='bottom', fontsize=6,
                         color='#333' if det['score'] > 0 else '#900')

    fig.suptitle(
        "DECISION PANEL: Option A (lit) vs Option C (neural-only) — same model class ceiling\n"
        "Green=exact, Orange=partial, Red=miss   ·   c2 orange→green miss is UNIVERSAL",
        fontsize=11.5, y=0.995, fontweight='bold')
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    base = OUT / f"{PREFIX}decision_AvsC"
    fig.savefig(f"{base}.png", dpi=200, bbox_inches='tight')
    fig.savefig(f"{base}.pdf", bbox_inches='tight')
    plt.close(fig)
    print(f'  wrote {base.name}.png/pdf')


def main():
    print(f'Option C visualization → {OUT}\n')
    print('--- 4-column color rendering ---')
    for sid in ['08','09']:
        render_4col(sid)
    print('\n--- F4 integrated figure ---')
    render_F4()
    print('\n--- Vulnerability line graph ---')
    render_vuln_hue()
    print('\n--- Decision panel (A vs C) ---')
    render_decision_panel()

    # Per-color summary for both subjects under C
    summary = {
        'loss_formula': OPTION_C['loss_plain'],
        'subjects': {}
    }
    for sid in ['08','09']:
        info = OPTION_C['subjects'][sid]
        bs, bc, axis = info['bs'], info['bc'], info['axis']
        p, ex, details = p2a_compute(bs, bc, axis, info['target'])
        summary['subjects'][sid] = {
            'bs': bs, 'bc': bc, 'family': info['family'], 'axis': axis,
            'p2a': float(p), 'exact': int(ex),
            'norm': float(np.hypot(bs, bc)),
            'per_color': [
                {'c': f'c{i+1}', 'theta': int(d['theta']),
                 'tcvd': float(d['tcvd']), 'dt': float(d['dt']),
                 'pred': d['pred'], 'tgt': d['tgt'], 'score': float(d['score'])}
                for i, d in enumerate(details)
            ],
        }
    with open(OUT / f"{PREFIX}summary.json", 'w') as f:
        json.dump(summary, f, indent=2)
    print(f'\nWrote {OUT / f"{PREFIX}summary.json"}')


if __name__ == '__main__':
    main()
