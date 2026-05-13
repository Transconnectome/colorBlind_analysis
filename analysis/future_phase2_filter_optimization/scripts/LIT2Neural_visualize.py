"""LIT2Neural_visualize.py — Landscape figures for unified neural-only loss.

Two panels per subject:
  (A) L_total heatmap on (β_s, β_c) grid with markers:
        * V1 ΔRDM anchor (β_s)
        * V4 LOCO anchor (β_c)
        * Argmin (loss-best)
        * P2a-max (verbal-report target)
        * Canonical §3 LOCO (V4 2-comp)
  (B) P2a heatmap on same grid with same markers, for direct comparison.

Plus a summary bar comparing argmin↔literature anchors per subject.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR))

from phase3_candidate_analysis_v2 import hc_name, hc_match_score, SUB08_ORIGINAL_HC_EQUIV
from fixedW_onlyTest_p2a_ranking import SUB09_ORIGINAL_HC_EQUIV
from neural_only_deep_sweep import (
    NEURAL_ANCHORS, V1_DELTA_RDM, P2A_MAX, BAYESIAN_BEST,
    EMERY_BETA_S, TREGILLUS_NORM,
    L_rdm_cosine, p2a_eval,
)
from neural_only_unified_loss import unified_loss

OUT = _THIS_DIR.parent / 'results'
FILE_PREFIX = 'LIT2Neural_'
OUT.mkdir(parents=True, exist_ok=True)

HUE_8 = [0, 45, 90, 135, 180, 225, 270, 315]


def compute_grids(landscape_path, subject, axis, target_map,
                  w_s=1.0, w_c=1.0, sigma_s=10.0, sigma_c=15.0, lam_rdm=0.5):
    with open(landscape_path) as f:
        d = json.load(f)
    cells = d['cells']
    vuln_obs = np.array(d['vuln_cvd'])
    bs_arr = np.array([c['bs'] for c in cells])
    bc_arr = np.array([c['bc'] for c in cells])

    bs_vals = sorted(set(bs_arr.tolist()))
    bc_vals = sorted(set(bc_arr.tolist()))
    nbs, nbc = len(bs_vals), len(bc_vals)
    L_grid = np.full((nbc, nbs), np.nan)
    P_grid = np.full((nbc, nbs), np.nan)
    bs_idx = {b: i for i, b in enumerate(bs_vals)}
    bc_idx = {b: i for i, b in enumerate(bc_vals)}

    anchor_bs = V1_DELTA_RDM[subject][0]
    anchor_bc = NEURAL_ANCHORS[subject]['V4'][1]

    for c in cells:
        i = bs_idx[c['bs']]; j = bc_idx[c['bc']]
        L_grid[j, i] = unified_loss(c, vuln_obs, anchor_bs, anchor_bc,
                                     w_s, w_c, sigma_s, sigma_c, lam_rdm)
        p2a, _ = p2a_eval(c['bs'], c['bc'], axis, target_map)
        P_grid[j, i] = p2a

    # Argmin
    sort_key = L_grid * 1e6 + (np.array(bs_vals)[None, :]**2
                                + np.array(bc_vals)[:, None]**2)
    flat_idx = np.argmin(sort_key)
    j_min, i_min = np.unravel_index(flat_idx, L_grid.shape)
    argmin_pt = (bs_vals[i_min], bc_vals[j_min])

    return {
        'bs_vals': np.array(bs_vals), 'bc_vals': np.array(bc_vals),
        'L_grid': L_grid, 'P_grid': P_grid,
        'anchor_bs': anchor_bs, 'anchor_bc': anchor_bc,
        'argmin': argmin_pt,
    }


def plot_subject(ax_L, ax_P, gr, subject, axis):
    bs = gr['bs_vals']; bc = gr['bc_vals']
    extent = [bs.min()-1, bs.max()+1, bc.min()-1, bc.max()+1]

    # Panel A: Loss heatmap
    im1 = ax_L.imshow(gr['L_grid'], origin='lower', extent=extent,
                      aspect='auto', cmap='viridis_r')
    ax_L.set_xlabel(r'$\beta_s$ (°)')
    ax_L.set_ylabel(r'$\beta_c$ (°)')
    ax_L.set_title(f'{subject} — Loss L (axis={axis}°)')
    plt.colorbar(im1, ax=ax_L, label='L')

    # Panel B: P2a heatmap
    im2 = ax_P.imshow(gr['P_grid'], origin='lower', extent=extent,
                      aspect='auto', cmap='magma', vmin=0, vmax=1)
    ax_P.set_xlabel(r'$\beta_s$ (°)')
    ax_P.set_ylabel(r'$\beta_c$ (°)')
    ax_P.set_title(f'{subject} — P2a heatmap')
    plt.colorbar(im2, ax=ax_P, label='P2a')

    # Marker overlay (same on both)
    for ax in (ax_L, ax_P):
        # Anchor lines
        ax.axvline(gr['anchor_bs'], color='cyan', lw=0.7, ls=':',
                   alpha=0.8, label=fr'V1$\Delta$RDM $\beta_s$={gr["anchor_bs"]:.0f}°')
        ax.axhline(gr['anchor_bc'], color='magenta', lw=0.7, ls=':',
                   alpha=0.8, label=fr'V4 LOCO $\beta_c$={gr["anchor_bc"]:.0f}°')
        # Argmin
        ax.plot(*gr['argmin'], marker='o', mfc='white', mec='black', ms=11,
                mew=1.5, label=f"argmin ({gr['argmin'][0]:.0f},{gr['argmin'][1]:+.0f})",
                linestyle='None')
        # P2a-max
        pm = P2A_MAX[subject]
        ax.plot(*pm, marker='*', mfc='gold', mec='black', ms=18, mew=0.8,
                label=f"P2a-max ({pm[0]:.0f},{pm[1]:+.0f})", linestyle='None')
        # Canonical §3
        cn = NEURAL_ANCHORS[subject]['V4']
        ax.plot(*cn, marker='s', mfc='none', mec='red', ms=11, mew=1.5,
                label=f"§3 LOCO ({cn[0]:.0f},{cn[1]:+.0f})", linestyle='None')
        # Bayesian BEST
        bb = BAYESIAN_BEST[subject]
        ax.plot(*bb, marker='D', mfc='none', mec='blue', ms=9, mew=1.3,
                label=f"Bayes BEST ({bb[0]:.0f},{bb[1]:+.0f})", linestyle='None')
        # Literature region (Emery β_s ± 5)
        ax.axvspan(EMERY_BETA_S - 3, EMERY_BETA_S + 3, color='lime',
                   alpha=0.08, zorder=0)
    ax_L.legend(loc='upper right', fontsize=6, framealpha=0.92)


def plot_recovery_bar(ax, results):
    """Bar comparison of argmin vs literature anchors per subject."""
    labels = ['Emery β_s\n(21.4°)', 'Tregillus ||β||\n(28°)', 'Brettel β_c sign']
    width = 0.35
    x = np.arange(len(labels))

    for k, (sid, r) in enumerate(results.items()):
        b = r['best']
        vals = [b['bs'], b['norm'],
                +1 if b['brettel_sign_ok'] else (-1 if b['brettel_sign_ok'] is False else 0)]
        offset = (k - 0.5) * width
        col = 'tab:red' if sid == 'sub-08' else 'tab:blue'
        ax.bar(x + offset, vals, width, color=col, alpha=0.75,
               label=f'{sid} argmin')

    # Reference lines
    ax.axhline(EMERY_BETA_S, color='gray', ls='--', lw=0.8,
               xmax=0.33, alpha=0.8)
    ax.axhline(TREGILLUS_NORM, color='gray', ls='--', lw=0.8,
               xmin=0.34, xmax=0.66, alpha=0.8)
    ax.text(0, EMERY_BETA_S + 0.5, 'Emery 21.4°', ha='center',
            fontsize=7, color='gray')
    ax.text(1, TREGILLUS_NORM + 0.5, 'Tregillus 28°', ha='center',
            fontsize=7, color='gray')

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel('Value')
    ax.set_title('Argmin vs Literature Anchors')
    ax.legend(fontsize=8)


def main():
    cases = [
        ('sub-08', 150.0,
         'results/axis_3way/sub-08_V4_Stockman150_landscape.json',
         SUB08_ORIGINAL_HC_EQUIV),
        ('sub-09', 16.0,
         'results/axis_3way/sub-09_V4_Stockman16ext_landscape.json',
         SUB09_ORIGINAL_HC_EQUIV),
    ]

    grids = {}
    for sid, axis, lp, tmap in cases:
        if not Path(lp).exists():
            print(f'SKIP {lp}'); continue
        grids[sid] = (compute_grids(lp, sid, axis, tmap), axis)

    # ---- Main 4-panel figure ----
    fig = plt.figure(figsize=(13, 9))
    gs = fig.add_gridspec(2, 2, hspace=0.35, wspace=0.3,
                          left=0.07, right=0.97, top=0.93, bottom=0.07)
    axs = [[fig.add_subplot(gs[i, j]) for j in range(2)] for i in range(2)]

    for row_i, sid in enumerate(['sub-08', 'sub-09']):
        if sid not in grids: continue
        gr, axis = grids[sid]
        plot_subject(axs[row_i][0], axs[row_i][1], gr, sid, axis)

    fig.suptitle('LIT2Neural — Unified loss landscape + P2a heatmap',
                 fontsize=12, fontweight='bold')

    for ext in ('png', 'pdf'):
        out = OUT / f'fig_landscape_4panel.{ext}'
        fig.savefig(out, dpi=180, bbox_inches='tight')
        print(f'wrote {out}')
    plt.close(fig)

    # ---- Argmin vs anchors summary figure ----
    # Reload unified results
    res_path = OUT / 'unified_loss_results.json'
    if res_path.exists():
        results = json.load(open(res_path))
        results = {k: v for k, v in results.items() if k in ('sub-08', 'sub-09')}
        fig, ax = plt.subplots(1, 1, figsize=(7, 4))
        plot_recovery_bar(ax, results)
        for ext in ('png', 'pdf'):
            out = OUT / f'fig_argmin_vs_literature.{ext}'
            fig.savefig(out, dpi=180, bbox_inches='tight')
            print(f'wrote {out}')
        plt.close(fig)


if __name__ == '__main__':
    main()
