"""LIT2Neural_original_visualize.py — 원본 통합 수식 시각화.

원본 LIT2Neural unified loss (양 피험자 동일 anchor source):

    L(β_s, β_c | subject) =
        ((β_s − β_s^{V1ΔRDM}[subject]) / 10)²
      + ((β_c − β_c^{V4 LOCO 2-comp phase_a}[subject]) / 15)²
      + 0.5 · L_RDM_cos(V4 vuln_sim ↔ vuln_cvd)

Argmin:
    sub-08 deutan: (β_s=20°, β_c=−14°), P2a=0.263, dist→P2a-max = 48.4°
    sub-09 protan: (β_s=22°, β_c=−22°), P2a=0.887, dist→P2a-max = 2.8°

Produces ORIG_-prefixed figures (BEST_ prefix reserved for current heterogeneous BEST).
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

from phase3_candidate_analysis_v2 import SUB08_ORIGINAL_HC_EQUIV
from fixedW_onlyTest_p2a_ranking import SUB09_ORIGINAL_HC_EQUIV
from LIT2Neural_filterBest_visualize import (
    LIT2N as _DEFAULT_LIT2N,  # used only as scaffolding
    render_4col, render_vuln_hue, render_landscape,
    p2a_compute, VULN_YLABEL, OUT,
)

# Override with ORIGINAL unified anchors (phase_a V4 LOCO 2-comp for BOTH)
LIT2N_ORIG = [
    {
        'sid': '08', 'family': 'deutan', 'color': '#E07B2C',
        'axis': 150.0,
        'bs': 20.0, 'bc': -14.0,   # ← ORIGINAL: phase_a anchor
        'anchor_source': 'V4 LOCO 2-comp phase_a (unified, both subjects)',
        'target_map': SUB08_ORIGINAL_HC_EQUIV,
        'p2a_max': (26.0, 34.0),
        'landscape_path': 'results/axis_3way/sub-08_V4_Stockman150_landscape.json',
    },
    {
        'sid': '09', 'family': 'protan', 'color': '#2D8E8B',
        'axis': 16.0,
        'bs': 22.0, 'bc': -22.0,   # same as before (phase_a was already used)
        'anchor_source': 'V4 LOCO 2-comp phase_a (unified, both subjects)',
        'target_map': SUB09_ORIGINAL_HC_EQUIV,
        'p2a_max': (24.0, -20.0),
        'landscape_path': 'results/axis_3way/sub-09_V4_Stockman16ext_landscape.json',
    },
]


def main():
    print(f'LIT2Neural ORIGINAL unified-formula visualization → {OUT}')
    print('=' * 80)
    print('Formula: L = ((β_s−β_s^{V1ΔRDM})/10)² + ((β_c−β_c^{V4LOCO2c phase_a})/15)²')
    print('         + 0.5·L_RDM_cos(V4)')
    print('Anchor source: V4 LOCO 2-comp phase_a fit (SAME for both subjects)')
    print('=' * 80)
    print()

    summary = {}
    for info in LIT2N_ORIG:
        sid = info['sid']
        bs, bc, axis = info['bs'], info['bc'], info['axis']
        p2a, exact, _ = p2a_compute(bs, bc, axis, info['target_map'])
        dist = float(np.hypot(bs - info['p2a_max'][0], bc - info['p2a_max'][1]))
        print(f"sub-{sid} ({info['family']}) β_s={bs:.0f} β_c={bc:+.0f} "
              f"axis={axis}° → P2a={p2a:.3f}, exact={exact}/8, "
              f"dist→P2a-max={dist:.1f}°")

        # Render with ORIG_ prefix
        _patched_info = {**info}
        # render_4col uses BEST_ prefix; we save with ORIG_ manually
        _render_with_prefix(info, 'ORIG_')
        summary[f'sub-{sid}'] = {
            'bs': bs, 'bc': bc, 'axis': axis,
            'anchor_source': info['anchor_source'],
            'p2a': p2a, 'exact': exact,
            'p2a_max': info['p2a_max'],
            'dist_to_p2amax': dist,
        }

    # F4 combined for original
    print('\nF4 combined (ORIGINAL):')
    _render_F4_original(LIT2N_ORIG)

    with open(OUT / 'LIT2Neural_ORIGINAL_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"\nWrote {OUT / 'LIT2Neural_ORIGINAL_summary.json'}")


def _render_with_prefix(info, prefix):
    """Use existing render_* functions but save with custom prefix."""
    import shutil
    # Use the standard renderers (they save as BEST_*); rename after
    render_4col(info)
    render_vuln_hue(info)
    render_landscape(info)
    # Rename BEST_ files to ORIG_
    sid, bs, bc = info['sid'], info['bs'], info['bc']
    bs_i, bc_i = int(bs), int(bc)
    suffix_map = [
        f'4col_sub-{sid}_V4_LIT2N_bs{bs_i}_bc{bc_i:+d}',
        f'vuln_hue_sub-{sid}_V4_LIT2N_bs{bs_i}_bc{bc_i:+d}',
        f'landscape_sub-{sid}_V4_LIT2N_bs{bs_i}_bc{bc_i:+d}',
    ]
    for sfx in suffix_map:
        for ext in ('png', 'pdf'):
            src = OUT / f'BEST_{sfx}.{ext}'
            dst = OUT / f'{prefix}{sfx}.{ext}'
            if src.exists():
                shutil.move(str(src), str(dst))
                print(f'  → {dst.name}')


def _render_F4_original(cases):
    """F4 plot for original unified formula."""
    from matplotlib.patches import Rectangle
    fig = plt.figure(figsize=(14, 9))
    gs = fig.add_gridspec(3, 2, hspace=0.40, wspace=0.28,
                          left=0.06, right=0.97, top=0.93, bottom=0.06)

    for row, info in enumerate(cases):
        sid = info['sid']; bs, bc = info['bs'], info['bc']
        axis = info['axis']
        with open(info['landscape_path']) as f:
            d = json.load(f)
        cells = d['cells']
        vuln_obs = np.array(d['vuln_cvd'])
        sel = next((c for c in cells
                    if abs(c['bs']-bs) < 1e-3 and abs(c['bc']-bc) < 1e-3), None)
        if sel is None:
            print(f'  cell ({bs},{bc}) not in landscape — using nearest')
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
                  label=fr'ORIG sim ($\rho$={rho:.2f}, CCC={ccc:.2f}, P2a={p2a:.3f})')
        top3 = np.argsort(vuln_obs)[:3]
        for idx in top3:
            ax_a.axvspan(idx-0.4, idx+0.4, alpha=0.1, color=info['color'])
        ax_a.set_xticks(x)
        ax_a.set_xticklabels(['R','O','Y','G','C','B','P','M'])
        ax_a.set_ylabel(VULN_YLABEL)
        ax_a.set_ylim(-1, 1)
        ax_a.set_title(
            f"sub-{sid} ({info['family']}) — ORIGINAL unified @ "
            f"({bs:.0f},{bc:+.0f}), axis={axis}°",
            fontweight='bold', color=info['color'])
        ax_a.legend(loc='best', fontsize=6.5)
        ax_a.spines[['top','right']].set_visible(False)

        # Panel B — landscape
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
        plt.colorbar(im, ax=ax_b, label='L_combined (axis_3way)', fraction=0.04)
        ax_b.plot(bs, bc, 'o', mfc='white', mec='black', ms=13, mew=1.5,
                  label=f'ORIG ({bs:.0f},{bc:+.0f})')
        pm = info['p2a_max']
        ax_b.plot(*pm, '*', mfc='gold', mec='black', ms=18, mew=0.7,
                  label=f'P2a-max ({pm[0]:.0f},{pm[1]:+.0f})')
        ax_b.axhline(0, color='gray', lw=0.4); ax_b.axvline(0, color='gray', lw=0.4)
        ax_b.set_xlabel(r'$\beta_s$ (°)'); ax_b.set_ylabel(r'$\beta_c$ (°)')
        ax_b.set_title(f"sub-{sid} — landscape",
                       fontsize=8, fontweight='bold', color=info['color'])
        ax_b.legend(loc='best', fontsize=6.5)

    # Bottom row — P2a comparison ORIG vs current BEST vs P2a-max
    ax_bars = fig.add_subplot(gs[2, :])
    labels = ['ORIGINAL unified\n(phase_a anchor both)',
              'BEST heterogeneous\n(per-subj anchor)',
              'P2a-max\n(behavioral target)']
    sub08_vals = [0.263, 0.550, 0.875]
    sub09_vals = [0.887, 0.887, 0.950]
    x = np.arange(len(labels))
    w = 0.35
    ax_bars.bar(x - w/2, sub08_vals, w, color='#E07B2C', alpha=0.85, label='sub-08')
    ax_bars.bar(x + w/2, sub09_vals, w, color='#2D8E8B', alpha=0.85, label='sub-09')
    for i, (a, b) in enumerate(zip(sub08_vals, sub09_vals)):
        ax_bars.text(i - w/2, a + 0.01, f'{a:.3f}', ha='center', fontsize=7)
        ax_bars.text(i + w/2, b + 0.01, f'{b:.3f}', ha='center', fontsize=7)
    ax_bars.set_xticks(x); ax_bars.set_xticklabels(labels, fontsize=8)
    ax_bars.set_ylabel('P2a'); ax_bars.set_ylim(0, 1.05)
    ax_bars.set_title('P2a: ORIGINAL unified vs heterogeneous BEST vs P2a-max',
                       fontweight='bold')
    ax_bars.legend()
    ax_bars.spines[['top', 'right']].set_visible(False)

    fig.suptitle('LIT2Neural ORIGINAL — unified loss with phase_a V4 LOCO anchor (both subjects)',
                 fontsize=11, fontweight='bold')

    out_png = OUT / 'ORIG_F4_V4_LIT2N_unified.png'
    plt.savefig(out_png, dpi=150, bbox_inches='tight')
    plt.savefig(str(out_png).replace('.png', '.pdf'), bbox_inches='tight')
    plt.close(fig)
    print(f'  wrote {out_png.name} (+pdf)')


if __name__ == '__main__':
    main()
