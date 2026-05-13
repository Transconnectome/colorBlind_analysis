"""LIT2Neural_filterBest_visualize.py — /filter-best standard viz set for
LIT2Neural BEST candidates.

Candidates:
  sub-08 deutan: (β_s=20°, β_c=+22°), anchor source = L_combined bootstrap (V4)
    → P2a=0.550, exact=3/8, dist_to_P2a-max=13.4°
  sub-09 protan: (β_s=22°, β_c=-22°), anchor source = phase_a V4 LOCO 2-comp
    → P2a=0.887, exact=6/8, dist_to_P2a-max=2.8°

Visualization conventions (per /filter-best skill):
  - V4-only LOCO policy
  - Y-axis: "LOCO voxel_corr (↑ preserved / HC-like | ↓ vulnerable / CVD-distorted)"
  - Standard renderers from fixedW_onlyTest_best_visualize.py
  - Outputs go to results/LIT2Neural/

Forward model: δθ = β_s·cos(θ-90°) + β_c·cos(θ-θ_conf)
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
sys.path.insert(0, str(_THIS_DIR / 'visualization'))

from stim_lab_render import render_at_hue as _render_stim_lab
from phase3_candidate_analysis_v2 import (
    hc_name, hc_match_score, SUB08_ORIGINAL_HC_EQUIV,
)
from fixedW_onlyTest_p2a_ranking import SUB09_ORIGINAL_HC_EQUIV

_PHASE2 = _THIS_DIR.parent
OUT = _PHASE2 / 'results' / 'LIT2Neural'
OUT.mkdir(parents=True, exist_ok=True)

VULN_YLABEL = ("LOCO voxel_corr  (↑ preserved / HC-like  |  "
               "↓ vulnerable / CVD-distorted)")

HUE_ANGLES = [0, 45, 90, 135, 180, 225, 270, 315]
COLOR_LABELS = ['c1 (red)', 'c2 (orange)', 'c3 (yellow)', 'c4 (green)',
                'c5 (cyan)', 'c6 (sky)', 'c7 (blue)', 'c8 (magenta)']

# LIT2Neural candidates — same forward model, per-subject axis + anchor source
LIT2N = [
    {
        'sid': '08', 'family': 'deutan', 'color': '#E07B2C',
        'axis': 150.0,
        'bs': 20.0, 'bc': 22.0,
        'anchor_source': 'V4 L_combined bootstrap median (N=2000)',
        'target_map': SUB08_ORIGINAL_HC_EQUIV,
        'p2a_max': (26.0, 34.0),
        'landscape_path': 'results/axis_3way/sub-08_V4_Stockman150_landscape.json',
    },
    {
        'sid': '09', 'family': 'protan', 'color': '#2D8E8B',
        'axis': 16.0,
        'bs': 22.0, 'bc': -22.0,
        'anchor_source': 'V4 LOCO 2-comp phase_a fit',
        'target_map': SUB09_ORIGINAL_HC_EQUIV,
        'p2a_max': (24.0, -20.0),
        'landscape_path': 'results/axis_3way/sub-09_V4_Stockman16ext_landscape.json',
    },
]

matplotlib.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Helvetica', 'Arial', 'DejaVu Sans'],
    'font.size': 7, 'axes.titlesize': 7.5, 'axes.labelsize': 7,
    'xtick.labelsize': 7, 'ytick.labelsize': 7, 'legend.fontsize': 6.5,
    'axes.linewidth': 0.6, 'xtick.major.width': 0.6, 'ytick.major.width': 0.6,
    'pdf.fonttype': 42, 'ps.fonttype': 42,
})


# ---------- forward + pre-image ----------
def dt_2comp(theta_deg, bs, bc, theta_conf):
    th = np.deg2rad(theta_deg)
    return bs * np.cos(th - np.pi/2) + bc * np.cos(th - np.deg2rad(theta_conf))


def forward_2comp(theta, bs, bc, theta_conf):
    dt = dt_2comp(theta, bs, bc, theta_conf)
    return (theta + dt) % 360.0, dt


def pre_image_2comp(target_deg, bs, bc, theta_conf, n_grid=3600):
    grid = np.linspace(0, 360, n_grid, endpoint=False)
    fwd = (grid + dt_2comp(grid, bs, bc, theta_conf)) % 360.0
    diff = (fwd - target_deg + 180) % 360 - 180
    i = int(np.argmin(np.abs(diff)))
    return grid[i], dt_2comp(grid[i], bs, bc, theta_conf)


def p2a_compute(bs, bc, theta_conf, target_map):
    total = 0.0; exact = 0; details = []
    for theta in HUE_ANGLES:
        theta_cvd, dt = forward_2comp(float(theta), bs, bc, theta_conf)
        pred = hc_name(theta_cvd)
        target = target_map[theta]
        score = hc_match_score(pred, target)
        total += score
        if pred == target: exact += 1
        details.append({'theta': theta, 'dt': dt, 'pred': pred,
                        'target': target, 'score': score})
    return total / 8.0, exact, details


# ---------- renderers ----------
def render_4col(info):
    sid = info['sid']; bs, bc = info['bs'], info['bc']
    axis = info['axis']; target_map = info['target_map']
    p2a, exact, _ = p2a_compute(bs, bc, axis, target_map)

    n_rows = len(HUE_ANGLES)
    fig, axes = plt.subplots(n_rows, 4,
                             figsize=(5.5, 0.65 * n_rows + 0.8),
                             gridspec_kw={'hspace': 0.10, 'wspace': 0.05})
    fig.suptitle(
        f"sub-{sid} ({info['family']}) V4 — "
        fr"$\beta_s$={bs:.0f}°, $\beta_c$={bc:+.0f}°,  "
        f"P2a={p2a:.3f} ({exact}/8)",
        fontsize=10, y=1.005, color=info['color'], fontweight='bold')
    fig.text(0.5, 0.972,
             f"axis={axis}°  ·  norm={np.hypot(bs,bc):.1f}°  ·  "
             f"anchor: {info['anchor_source']}",
             ha='center', fontsize=7, color='#555555')

    for j, ct in enumerate(['Original', 'CVD perceives',
                            'Filtered (pre-image)', 'CVD(Filtered)']):
        axes[0, j].set_title(ct, fontsize=8)

    for i, theta in enumerate(HUE_ANGLES):
        theta_cvd, dt = forward_2comp(float(theta), bs, bc, axis)
        theta_pre, _ = pre_image_2comp(float(theta), bs, bc, axis)
        theta_cvd_pre, _ = forward_2comp(theta_pre, bs, bc, axis)

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

        pred = hc_name(theta_cvd)
        target = target_map[theta]
        score = hc_match_score(pred, target)
        mark = '✓' if pred == target else ('~' if score > 0 else '✗')
        col_p2a = 'green' if score == 1.0 else ('darkorange' if score > 0 else 'red')
        axes[i, 1].text(0.5, -0.02, f'δθ={dt:+.0f}° {mark}',
                        ha='center', va='top', fontsize=7,
                        transform=axes[i, 1].transAxes, color=col_p2a)
        axes[i, 2].text(0.5, -0.02, f'θ_pre={theta_pre:.0f}°',
                        ha='center', va='top', fontsize=7,
                        transform=axes[i, 2].transAxes)

    out_png = OUT / (f"BEST_4col_sub-{sid}_V4_LIT2N_"
                     f"bs{int(bs)}_bc{int(bc):+d}.png")
    plt.savefig(out_png, dpi=150, bbox_inches='tight')
    plt.savefig(str(out_png).replace('.png', '.pdf'), bbox_inches='tight')
    plt.close(fig)
    print(f'  wrote {out_png.name} (+pdf)')
    return p2a, exact


def render_vuln_hue(info):
    sid = info['sid']; bs, bc = info['bs'], info['bc']
    axis = info['axis']
    with open(info['landscape_path']) as f:
        d = json.load(f)
    cells = d['cells']
    vuln_obs = np.array(d['vuln_cvd'])
    # find cell matching (bs, bc)
    sel = next((c for c in cells if abs(c['bs']-bs) < 1e-3 and abs(c['bc']-bc) < 1e-3),
               None)
    if sel is None:
        print(f'  WARN cell ({bs},{bc}) not in landscape — skip'); return
    vuln_sim = np.array(sel['vuln_sim'])
    rho = float(np.corrcoef(vuln_sim, vuln_obs)[0, 1])
    ccc = sel.get('ccc', 0.0)
    p2a, _, _ = p2a_compute(bs, bc, axis, info['target_map'])

    fig, ax = plt.subplots(figsize=(6.5, 3.6), dpi=150)
    x = np.arange(8)
    labels_short = ['R', 'O', 'Y', 'G', 'C', 'B', 'P', 'M']

    ax.axhline(0, color='#aaaaaa', lw=0.5, ls=':')
    ax.plot(x, vuln_obs, 'o-', color='#222222', ms=6, lw=0.9,
            label='Observed CVD LOCO')
    ax.plot(x, vuln_sim, 's-', color=info['color'], ms=6, lw=1.5,
            label=fr'BEST sim @ ($\beta_s$={bs:.0f}°, $\beta_c$={bc:+.0f}°)  '
                  fr'$\rho$={rho:.2f}, CCC={ccc:.2f}')
    top3_obs = np.argsort(vuln_obs)[:3]
    for idx in top3_obs:
        ax.axvspan(idx-0.4, idx+0.4, alpha=0.10, color=info['color'], zorder=0)
    ax.set_xticks(x); ax.set_xticklabels(labels_short)
    ax.set_xlabel('Hue (DKL bin)  —  shaded = top-3 vulnerable observed')
    ax.set_ylabel(VULN_YLABEL)
    ax.set_title(
        f"sub-{sid} ({info['family']}) V4 LIT2Neural BEST  "
        f"P2a={p2a:.3f}  |  anchor: {info['anchor_source']}",
        fontweight='bold', color=info['color'])
    ax.set_ylim(-1.0, 1.0)
    ax.legend(loc='best', fontsize=7)
    ax.spines[['top', 'right']].set_visible(False)
    plt.tight_layout()
    out_png = OUT / (f"BEST_vuln_hue_sub-{sid}_V4_LIT2N_"
                     f"bs{int(bs)}_bc{int(bc):+d}.png")
    plt.savefig(out_png, dpi=150, bbox_inches='tight')
    plt.savefig(str(out_png).replace('.png', '.pdf'), bbox_inches='tight')
    plt.close(fig)
    print(f'  wrote {out_png.name} (+pdf)')


def render_landscape(info):
    """Combined L heatmap on (β_s, β_c) grid with markers."""
    sid = info['sid']; bs, bc = info['bs'], info['bc']
    axis = info['axis']
    with open(info['landscape_path']) as f:
        d = json.load(f)
    cells = d['cells']
    bs_arr = np.array(sorted(set(c['bs'] for c in cells)))
    bc_arr = np.array(sorted(set(c['bc'] for c in cells)))
    L_grid = np.full((len(bc_arr), len(bs_arr)), np.nan)
    bs_idx = {v: i for i, v in enumerate(bs_arr)}
    bc_idx = {v: i for i, v in enumerate(bc_arr)}
    for c in cells:
        L_grid[bc_idx[c['bc']], bs_idx[c['bs']]] = c['L_combined']

    # Dynamic vmin/vmax (5-95 pct)
    vmin, vmax = np.nanpercentile(L_grid, [5, 95])

    fig, ax = plt.subplots(figsize=(6.5, 5))
    extent = [bs_arr.min()-1, bs_arr.max()+1, bc_arr.min()-1, bc_arr.max()+1]
    im = ax.imshow(L_grid, origin='lower', extent=extent, aspect='auto',
                   cmap='RdBu_r', vmin=vmin, vmax=vmax)
    plt.colorbar(im, ax=ax, label='L_combined')

    # Markers
    ax.plot(bs, bc, marker='o', mfc='white', mec='black', ms=14, mew=1.7,
            linestyle='None',
            label=f'BEST ({bs:.0f},{bc:+.0f})')
    pm = info['p2a_max']
    ax.plot(*pm, marker='*', mfc='gold', mec='black', ms=18, mew=0.7,
            linestyle='None',
            label=f'P2a-max ({pm[0]:.0f},{pm[1]:+.0f})')
    ax.axhline(0, color='gray', lw=0.4)
    ax.axvline(0, color='gray', lw=0.4)
    ax.set_xlabel(r'$\beta_s$ (°)')
    ax.set_ylabel(r'$\beta_c$ (°)')
    p2a, exact, _ = p2a_compute(bs, bc, axis, info['target_map'])
    ax.set_title(
        f"sub-{sid} ({info['family']}) V4 LIT2Neural BEST  "
        f"axis={axis}°  |  P2a={p2a:.3f}  exact={exact}/8\n"
        f"argmin=blue, high L=red  |  anchor: {info['anchor_source']}",
        fontsize=9)
    ax.legend(loc='best', fontsize=7)
    plt.tight_layout()
    out_png = OUT / (f"BEST_landscape_sub-{sid}_V4_LIT2N_"
                     f"bs{int(bs)}_bc{int(bc):+d}.png")
    plt.savefig(out_png, dpi=150, bbox_inches='tight')
    plt.savefig(str(out_png).replace('.png', '.pdf'), bbox_inches='tight')
    plt.close(fig)
    print(f'  wrote {out_png.name} (+pdf)')


def render_F4_combined():
    """F4 = combined figure: per-subject vuln + landscape + P2a bars."""
    fig = plt.figure(figsize=(14, 9))
    gs = fig.add_gridspec(3, 2, hspace=0.40, wspace=0.28,
                          left=0.06, right=0.97, top=0.93, bottom=0.06)

    for row, info in enumerate(LIT2N):
        sid = info['sid']; bs, bc = info['bs'], info['bc']
        axis = info['axis']
        with open(info['landscape_path']) as f:
            d = json.load(f)
        cells = d['cells']
        vuln_obs = np.array(d['vuln_cvd'])
        sel = next((c for c in cells
                    if abs(c['bs']-bs)<1e-3 and abs(c['bc']-bc)<1e-3), None)
        vuln_sim = np.array(sel['vuln_sim'])
        rho = float(np.corrcoef(vuln_sim, vuln_obs)[0, 1])
        ccc = sel.get('ccc', 0.0)
        p2a, exact, details = p2a_compute(bs, bc, axis, info['target_map'])

        # Panel A: vuln_hue
        ax_a = fig.add_subplot(gs[row, 0])
        x = np.arange(8)
        ax_a.axhline(0, color='#aaa', lw=0.5, ls=':')
        ax_a.plot(x, vuln_obs, 'o-', color='#222', ms=6, lw=0.9,
                  label='Observed')
        ax_a.plot(x, vuln_sim, 's-', color=info['color'], ms=7, lw=1.6,
                  label=fr'BEST sim ($\rho$={rho:.2f}, CCC={ccc:.2f}, P2a={p2a:.3f})')
        top3 = np.argsort(vuln_obs)[:3]
        for idx in top3:
            ax_a.axvspan(idx-0.4, idx+0.4, alpha=0.1, color=info['color'])
        ax_a.set_xticks(x)
        ax_a.set_xticklabels(['R','O','Y','G','C','B','P','M'])
        ax_a.set_ylabel(VULN_YLABEL)
        ax_a.set_ylim(-1, 1)
        ax_a.set_title(
            f"sub-{sid} ({info['family']}) — vuln @ "
            f"({bs:.0f},{bc:+.0f}), axis={axis}°",
            fontweight='bold', color=info['color'])
        ax_a.legend(loc='best', fontsize=6.5)
        ax_a.spines[['top','right']].set_visible(False)

        # Panel B: landscape
        ax_b = fig.add_subplot(gs[row, 1])
        bs_arr = np.array(sorted(set(c['bs'] for c in cells)))
        bc_arr = np.array(sorted(set(c['bc'] for c in cells)))
        L_grid = np.full((len(bc_arr), len(bs_arr)), np.nan)
        bs_idx = {v:i for i,v in enumerate(bs_arr)}
        bc_idx = {v:i for i,v in enumerate(bc_arr)}
        for c in cells:
            L_grid[bc_idx[c['bc']], bs_idx[c['bs']]] = c['L_combined']
        vmin, vmax = np.nanpercentile(L_grid, [5, 95])
        extent = [bs_arr.min()-1, bs_arr.max()+1,
                  bc_arr.min()-1, bc_arr.max()+1]
        im = ax_b.imshow(L_grid, origin='lower', extent=extent, aspect='auto',
                          cmap='RdBu_r', vmin=vmin, vmax=vmax)
        plt.colorbar(im, ax=ax_b, label='L_combined', fraction=0.04)
        ax_b.plot(bs, bc, 'o', mfc='white', mec='black', ms=13, mew=1.5,
                  label=f'BEST ({bs:.0f},{bc:+.0f})')
        pm = info['p2a_max']
        ax_b.plot(*pm, '*', mfc='gold', mec='black', ms=18, mew=0.7,
                  label=f'P2a-max ({pm[0]:.0f},{pm[1]:+.0f})')
        ax_b.axhline(0, color='gray', lw=0.4)
        ax_b.axvline(0, color='gray', lw=0.4)
        ax_b.set_xlabel(r'$\beta_s$ (°)')
        ax_b.set_ylabel(r'$\beta_c$ (°)')
        ax_b.set_title(f"sub-{sid} ({info['family']}) — L_combined landscape",
                        fontsize=8, fontweight='bold', color=info['color'])
        ax_b.legend(loc='best', fontsize=6.5)

    # Bottom row — P2a comparison bars
    ax_bars = fig.add_subplot(gs[2, :])
    labels = ['LIT2Neural BEST', 'P2a-max', 'phase_a §3', 'Bayes (prev)']
    sub08_vals = [0.550, 0.875, 0.263, 0.550]
    sub09_vals = [0.887, 0.950, 0.712, 0.887]
    x = np.arange(len(labels))
    w = 0.35
    ax_bars.bar(x - w/2, sub08_vals, w, color='#E07B2C', alpha=0.8, label='sub-08')
    ax_bars.bar(x + w/2, sub09_vals, w, color='#2D8E8B', alpha=0.8, label='sub-09')
    for i, (a, b) in enumerate(zip(sub08_vals, sub09_vals)):
        ax_bars.text(i - w/2, a + 0.01, f'{a:.3f}', ha='center', fontsize=7)
        ax_bars.text(i + w/2, b + 0.01, f'{b:.3f}', ha='center', fontsize=7)
    ax_bars.set_xticks(x)
    ax_bars.set_xticklabels(labels)
    ax_bars.set_ylabel('P2a')
    ax_bars.set_ylim(0, 1.0)
    ax_bars.set_title('P2a comparison across candidate filters', fontweight='bold')
    ax_bars.legend()
    ax_bars.spines[['top', 'right']].set_visible(False)

    fig.suptitle('LIT2Neural BEST — /filter-best standard visualization set',
                 fontsize=11, fontweight='bold')

    out_png = OUT / 'BEST_F4_V4_LIT2N.png'
    plt.savefig(out_png, dpi=150, bbox_inches='tight')
    plt.savefig(str(out_png).replace('.png', '.pdf'), bbox_inches='tight')
    plt.close(fig)
    print(f'  wrote {out_png.name} (+pdf)')


def main():
    print(f'LIT2Neural /filter-best visualization → {OUT}')
    print()
    summary = {}
    for info in LIT2N:
        print(f"sub-{info['sid']} ({info['family']}) "
              f"β_s={info['bs']:.0f}, β_c={info['bc']:+.0f}, axis={info['axis']}°")
        p2a, exact = render_4col(info)
        render_vuln_hue(info)
        render_landscape(info)
        summary[f'sub-{info["sid"]}'] = {
            'bs': info['bs'], 'bc': info['bc'], 'axis': info['axis'],
            'anchor_source': info['anchor_source'],
            'p2a': p2a, 'exact': exact,
            'p2a_max': info['p2a_max'],
        }
    print()
    print('F4 combined:')
    render_F4_combined()

    with open(OUT / 'LIT2Neural_BEST_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    print(f'\nWrote summary → {OUT / "LIT2Neural_BEST_summary.json"}')


if __name__ == '__main__':
    main()
