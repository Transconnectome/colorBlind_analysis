"""LIT2Neural_hybrid_visualize.py — F4 + 4col figures for HYBRID neural-primary BEST.

Hybrid loss (양 피험자 동일):
    L = 0.7 · L_mse(V4) + 0.3 · L_rdm_cosine(V4) + 2.0 · Tikh

HYBRID BEST:
  sub-08 deutan: (β_s=16°, β_c=+40°), P2a=0.537 (3/8), Brettel + OK
  sub-09 protan: (β_s=12°, β_c=-30°), P2a=0.738 (3/8), Brettel − OK

Output naming:
  LIT2Neural_HYBRID_4col_sub-{08,09}_V4_LIT2N_bsB_bcB.{png,pdf}
  LIT2Neural_HYBRID_F4_V4_LIT2N.{png,pdf}
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
OUT = _PHASE2 / 'results'
PREFIX = 'LIT2Neural_HYBRID_'

VULN_YLABEL = ("LOCO voxel_corr  (↑ preserved / HC-like  |  "
               "↓ vulnerable / CVD-distorted)")

HUE_ANGLES = [0, 45, 90, 135, 180, 225, 270, 315]
COLOR_LABELS = ['c1 (red)', 'c2 (orange)', 'c3 (yellow)', 'c4 (green)',
                'c5 (cyan)', 'c6 (sky)', 'c7 (blue)', 'c8 (magenta)']

HYBRID = [
    {
        'sid': '08', 'family': 'deutan', 'color': '#E07B2C',
        'axis': 150.0,
        'bs': 16.0, 'bc': 40.0,
        'target_map': SUB08_ORIGINAL_HC_EQUIV,
        'p2a_max': (26.0, 34.0),
        'landscape_path': 'results/axis_3way/sub-08_V4_Stockman150_landscape.json',
    },
    {
        'sid': '09', 'family': 'protan', 'color': '#2D8E8B',
        'axis': 16.0,
        'bs': 12.0, 'bc': -30.0,
        'target_map': SUB09_ORIGINAL_HC_EQUIV,
        'p2a_max': (24.0, -20.0),
        'landscape_path': 'results/axis_3way/sub-09_V4_Stockman16ext_landscape.json',
    },
]
LOSS_NAME = r'$L = 0.7\,L_{\mathrm{mse}} + 0.3\,L_{\mathrm{rdm\,cos}} + 2.0\,\mathrm{Tikh}$'
LOSS_NAME_PLAIN = '0.7·L_mse + 0.3·L_rdm_cosine + 2.0·Tikh'

matplotlib.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Helvetica', 'Arial', 'DejaVu Sans'],
    'font.size': 7, 'axes.titlesize': 7.5, 'axes.labelsize': 7,
    'xtick.labelsize': 7, 'ytick.labelsize': 7, 'legend.fontsize': 6.5,
    'axes.linewidth': 0.6, 'xtick.major.width': 0.6, 'ytick.major.width': 0.6,
    'pdf.fonttype': 42, 'ps.fonttype': 42,
})


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


def render_4col(info):
    sid = info['sid']; bs, bc = info['bs'], info['bc']
    axis = info['axis']; target_map = info['target_map']
    p2a, exact, _ = p2a_compute(bs, bc, axis, target_map)

    n_rows = len(HUE_ANGLES)
    fig, axes = plt.subplots(n_rows, 4,
                             figsize=(5.5, 0.65 * n_rows + 0.8),
                             gridspec_kw={'hspace': 0.10, 'wspace': 0.05})
    fig.suptitle(
        f"sub-{sid} ({info['family']}) V4 HYBRID — "
        fr"$\beta_s$={bs:.0f}°, $\beta_c$={bc:+.0f}°,  "
        f"P2a={p2a:.3f} ({exact}/8)",
        fontsize=10, y=1.005, color=info['color'], fontweight='bold')
    fig.text(0.5, 0.972,
             f"axis={axis}°  ·  norm={np.hypot(bs,bc):.1f}°  ·  "
             f"loss: {LOSS_NAME_PLAIN}",
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

    out_png = OUT / (f"{PREFIX}4col_sub-{sid}_V4_LIT2N_"
                     f"bs{int(bs)}_bc{int(bc):+d}.png")
    plt.savefig(out_png, dpi=150, bbox_inches='tight')
    plt.savefig(str(out_png).replace('.png', '.pdf'), bbox_inches='tight')
    plt.close(fig)
    print(f'  wrote {out_png.name} (+pdf)')
    return p2a, exact


def render_F4_combined():
    """F4: per-subject vuln + landscape + P2a bars."""
    fig = plt.figure(figsize=(14, 9))
    gs = fig.add_gridspec(3, 2, hspace=0.40, wspace=0.28,
                          left=0.06, right=0.97, top=0.91, bottom=0.06)

    for row, info in enumerate(HYBRID):
        sid = info['sid']; bs, bc = info['bs'], info['bc']
        axis = info['axis']
        with open(info['landscape_path']) as f:
            d = json.load(f)
        cells = d['cells']
        vuln_obs = np.array(d['vuln_cvd'])
        sel = next((c for c in cells
                    if abs(c['bs']-bs) < 1e-3 and abs(c['bc']-bc) < 1e-3), None)
        if sel is None:
            sel = min(cells, key=lambda c: (c['bs']-bs)**2 + (c['bc']-bc)**2)
        vuln_sim = np.array(sel['vuln_sim'])
        rho = float(np.corrcoef(vuln_sim, vuln_obs)[0, 1])
        ccc = sel.get('ccc', 0.0)
        p2a, exact, _ = p2a_compute(bs, bc, axis, info['target_map'])

        # Panel A — vuln_hue
        ax_a = fig.add_subplot(gs[row, 0])
        x = np.arange(8)
        ax_a.axhline(0, color='#aaa', lw=0.5, ls=':')
        ax_a.plot(x, vuln_obs, 'o-', color='#222', ms=6, lw=0.9, label='Observed')
        ax_a.plot(x, vuln_sim, 's-', color=info['color'], ms=7, lw=1.6,
                  label=fr'HYBRID sim ($\rho$={rho:.2f}, CCC={ccc:.2f}, P2a={p2a:.3f})')
        top3 = np.argsort(vuln_obs)[:3]
        for idx in top3:
            ax_a.axvspan(idx-0.4, idx+0.4, alpha=0.1, color=info['color'])
        ax_a.set_xticks(x)
        ax_a.set_xticklabels(['R','O','Y','G','C','B','P','M'])
        ax_a.set_ylabel(VULN_YLABEL)
        ax_a.set_ylim(-1, 1)
        ax_a.set_title(
            f"sub-{sid} ({info['family']}) — HYBRID @ "
            f"({bs:.0f},{bc:+.0f}), axis={axis}°",
            fontweight='bold', color=info['color'])
        ax_a.legend(loc='best', fontsize=6.5)
        ax_a.spines[['top','right']].set_visible(False)

        # Panel B — L_combined landscape
        ax_b = fig.add_subplot(gs[row, 1])
        bs_arr = np.array(sorted(set(c['bs'] for c in cells)))
        bc_arr = np.array(sorted(set(c['bc'] for c in cells)))
        L_grid = np.full((len(bc_arr), len(bs_arr)), np.nan)
        bs_idx = {v:i for i,v in enumerate(bs_arr)}
        bc_idx = {v:i for i,v in enumerate(bc_arr)}
        # Build hybrid loss per cell
        from scipy.stats import pearsonr  # noqa
        L_mse_raw = np.array([
            float(np.mean((np.array(c['vuln_sim']) - vuln_obs) ** 2))
            for c in cells])
        L_mse_n = L_mse_raw / L_mse_raw.max() if L_mse_raw.max() > 0 else L_mse_raw
        # RDM cosine per cell
        def _rdm_cos(s, o):
            iu = np.triu_indices(len(s), k=1)
            r_s = np.abs(s[:, None] - s[None, :])[iu]
            r_o = np.abs(o[:, None] - o[None, :])[iu]
            ns, no = np.linalg.norm(r_s), np.linalg.norm(r_o)
            if ns < 1e-10 or no < 1e-10: return 1.0
            return float(1.0 - np.dot(r_s, r_o) / (ns * no)) / 2
        L_rdm = np.array([_rdm_cos(np.array(c['vuln_sim']), vuln_obs) for c in cells])
        bs_arr_full = np.array([c['bs'] for c in cells])
        bc_arr_full = np.array([c['bc'] for c in cells])
        tikh = (bs_arr_full**2 + bc_arr_full**2) / 32400.0
        L_hybrid = 0.7 * L_mse_n + 0.3 * L_rdm + 2.0 * tikh
        for k, c in enumerate(cells):
            L_grid[bc_idx[c['bc']], bs_idx[c['bs']]] = L_hybrid[k]

        vmin, vmax = np.nanpercentile(L_grid, [5, 95])
        extent = [bs_arr.min()-1, bs_arr.max()+1,
                  bc_arr.min()-1, bc_arr.max()+1]
        im = ax_b.imshow(L_grid, origin='lower', extent=extent, aspect='auto',
                          cmap='RdBu_r', vmin=vmin, vmax=vmax)
        plt.colorbar(im, ax=ax_b, label='L_hybrid', fraction=0.04)
        ax_b.plot(bs, bc, 'o', mfc='white', mec='black', ms=13, mew=1.5,
                  label=f'HYBRID ({bs:.0f},{bc:+.0f})')
        pm = info['p2a_max']
        ax_b.plot(*pm, '*', mfc='gold', mec='black', ms=18, mew=0.7,
                  label=f'P2a-max ({pm[0]:.0f},{pm[1]:+.0f})')
        ax_b.axhline(0, color='gray', lw=0.4); ax_b.axvline(0, color='gray', lw=0.4)
        ax_b.set_xlabel(r'$\beta_s$ (°)'); ax_b.set_ylabel(r'$\beta_c$ (°)')
        ax_b.set_title(f"sub-{sid} — L_hybrid landscape (argmin=blue)",
                        fontsize=8, fontweight='bold', color=info['color'])
        ax_b.legend(loc='best', fontsize=6.5)

    # Bottom: P2a comparison bars
    ax_bars = fig.add_subplot(gs[2, :])
    methods = ['ORIGINAL\n(phase_a anchor)',
               'BEST hetero\n(L_combined anchor)',
               'Bayesian\nα=0.3',
               'HYBRID\nL_mse+RDMcos+Tikh',
               'P2a-max\n(behavioral)']
    sub08_vals = [0.263, 0.550, 0.550, 0.537, 0.875]
    sub09_vals = [0.887, 0.388, 0.887, 0.738, 0.950]
    x = np.arange(len(methods))
    w = 0.35
    ax_bars.bar(x - w/2, sub08_vals, w, color='#E07B2C', alpha=0.85, label='sub-08')
    ax_bars.bar(x + w/2, sub09_vals, w, color='#2D8E8B', alpha=0.85, label='sub-09')
    for i, (a, b) in enumerate(zip(sub08_vals, sub09_vals)):
        ax_bars.text(i - w/2, a + 0.01, f'{a:.3f}', ha='center', fontsize=7)
        ax_bars.text(i + w/2, b + 0.01, f'{b:.3f}', ha='center', fontsize=7)
    ax_bars.set_xticks(x); ax_bars.set_xticklabels(methods, fontsize=7.5)
    ax_bars.set_ylabel('P2a'); ax_bars.set_ylim(0, 1.02)
    ax_bars.set_title('P2a comparison: HYBRID neural-primary vs alternatives',
                       fontweight='bold')
    # Highlight HYBRID
    for pos in [3]:
        ax_bars.axvspan(pos - 0.45, pos + 0.45, color='yellow', alpha=0.15, zorder=0)
    ax_bars.legend()
    ax_bars.spines[['top', 'right']].set_visible(False)

    fig.suptitle(
        f'LIT2Neural HYBRID — neural-primary unified loss + Brettel sign recovery\n'
        f'{LOSS_NAME}',
        fontsize=11, fontweight='bold')

    out_png = OUT / f'{PREFIX}F4_V4_LIT2N.png'
    plt.savefig(out_png, dpi=150, bbox_inches='tight')
    plt.savefig(str(out_png).replace('.png', '.pdf'), bbox_inches='tight')
    plt.close(fig)
    print(f'  wrote {out_png.name} (+pdf)')


def main():
    print(f'LIT2Neural HYBRID visualization → {OUT}')
    print(f'  Loss: {LOSS_NAME_PLAIN}')
    print()
    summary = {}
    for info in HYBRID:
        print(f"sub-{info['sid']} ({info['family']}) "
              f"β_s={info['bs']:.0f}, β_c={info['bc']:+.0f}, axis={info['axis']}°")
        p2a, exact = render_4col(info)
        summary[f'sub-{info["sid"]}'] = {
            'bs': info['bs'], 'bc': info['bc'], 'axis': info['axis'],
            'p2a': p2a, 'exact': exact, 'p2a_max': info['p2a_max'],
        }
    print('F4 combined:')
    render_F4_combined()

    with open(OUT / f'{PREFIX}summary.json', 'w') as f:
        json.dump({
            'loss': LOSS_NAME_PLAIN,
            'alpha': 0.7, 'lambda_tikh': 2.0,
            'subjects': summary,
        }, f, indent=2)
    print(f"\nWrote {OUT / (PREFIX + 'summary.json')}")


if __name__ == '__main__':
    main()
