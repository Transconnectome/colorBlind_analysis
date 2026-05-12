#!/usr/bin/env python3
"""cycle12_landscape_fig.py — F4-style figure for cycle12 cross-ROI landscape.

Reads the per-subject landscape JSONs produced by
`cycle12_landscape_recompute.py` and builds an F4-style 3-panel figure:
  A: V4 LOCO vulnerability — observed vs simulated at argmin
  B: Bar chart of L_total at argmin per subject
  C: L_total landscape (β_s × β_c) with argmin star

Output: results/fixedW_onlyTest/fig_F4_V4V1_cycle12.{png,pdf}
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

_THIS = Path(__file__).resolve().parent
_PHASE2 = _THIS.parent
RES = _PHASE2 / 'results' / 'fixedW_onlyTest'

SUBJECTS = [('sub-08', 'deutan', '#E07B2C'),
            ('sub-09', 'protan', '#2D8E8B')]
COL_OBS = '#222222'
HUE_LABELS = ['R', 'O', 'Y', 'G', 'C', 'B', 'P', 'M']
HUE_X = np.arange(8)

matplotlib.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Helvetica', 'Arial', 'DejaVu Sans'],
    'font.size': 7, 'axes.titlesize': 7.5, 'axes.labelsize': 7,
    'xtick.labelsize': 7, 'ytick.labelsize': 7, 'legend.fontsize': 7,
    'axes.linewidth': 0.6,
    'xtick.major.width': 0.6, 'ytick.major.width': 0.6,
    'xtick.major.size': 2.5, 'ytick.major.size': 2.5,
    'lines.linewidth': 1.0,
    'pdf.fonttype': 42, 'ps.fonttype': 42,
})


def load_landscape(subj_id):
    p = RES / f'sub-{subj_id}_V4V1_cycle12_landscape.json'
    with open(p) as f:
        return json.load(f)


def rebuild_grids(payload):
    cells = payload['cells']
    bs_arr = np.array(payload['meta']['grid']['bs'])
    bc_arr = np.array(payload['meta']['grid']['bc'])
    n_bs, n_bc = len(bs_arr), len(bc_arr)
    L = np.zeros((n_bs, n_bc))
    bs_idx = {round(v, 6): i for i, v in enumerate(bs_arr.tolist())}
    bc_idx = {round(v, 6): j for j, v in enumerate(bc_arr.tolist())}
    for c in cells:
        i = bs_idx[round(c['bs'], 6)]
        j = bc_idx[round(c['bc'], 6)]
        L[i, j] = c['l_total']
    return bs_arr, bc_arr, L


def main():
    packs = {}
    for subj_id, fam, _ in SUBJECTS:
        sid = subj_id.split('-')[1]
        pld = load_landscape(sid)
        bs_arr, bc_arr, L = rebuild_grids(pld)
        packs[subj_id] = {
            'family': fam,
            'payload': pld,
            'bs': bs_arr,
            'bc': bc_arr,
            'L_total': L,
            'best': pld['argmin'],
            'vuln_cvd_V4': np.array(pld['vuln_cvd_V4']),
        }

    fig = plt.figure(figsize=(7.087, 7.0), dpi=300)
    L_A = 0.07; W_A = 0.33; L_C = 0.46; W_C = 0.44
    L_CB = 0.915; W_CB = 0.016
    H_AB_ROW = 0.27; H_B = 0.150
    B_R2 = 0.050; B_R1 = B_R2 + H_AB_ROW + 0.070
    B_B = B_R1 + H_AB_ROW + 0.075

    ax_a08 = fig.add_axes([L_A, B_R1, W_A, H_AB_ROW])
    ax_c08 = fig.add_axes([L_C, B_R1, W_C, H_AB_ROW])
    ax_a09 = fig.add_axes([L_A, B_R2, W_A, H_AB_ROW])
    ax_c09 = fig.add_axes([L_C, B_R2, W_C, H_AB_ROW])
    ax_cb = fig.add_axes([L_CB, B_R2, W_CB, B_R1 + H_AB_ROW - B_R2])
    ax_b = fig.add_axes([L_A, B_B, L_CB - L_A - 0.01, H_B])

    AX_A = {'sub-08': ax_a08, 'sub-09': ax_a09}
    AX_C = {'sub-08': ax_c08, 'sub-09': ax_c09}

    # Panel A: vuln traces
    for subj_id, fam, color in SUBJECTS:
        pack = packs[subj_id]
        best = pack['best']
        vsim = np.array(best['vuln_sim_V4'])
        vobs = pack['vuln_cvd_V4']
        ax = AX_A[subj_id]
        ax.axhline(0, color='#aaaaaa', lw=0.5, ls=':')
        ax.plot(HUE_X, vobs, 'o-', color=COL_OBS, ms=3.5, lw=0.6,
                label='Observed CVD (V4 LOCO)')
        ax.plot(HUE_X, vsim, '-', color=color, lw=1.8,
                label=(f'Cycle12 argmin  L={best["L_total"]:.3f}\n'
                       f'l_topk(V4)={best["l_topk_V4"]:.3f}, '
                       f'l_rank(V1)={best["l_rank_V1"]:.3f}'))
        ax.set_xticks(HUE_X); ax.set_xticklabels(HUE_LABELS)
        ax.set_xlabel('Hue (DKL)'); ax.set_ylabel('LOCO vulnerability')
        ax.set_ylim(-1.0, 1.0)
        ax.set_title(f'{subj_id} ({fam})', fontweight='bold', pad=3)
        ax.legend(loc='upper right', handlelength=1.8, handletextpad=0.3,
                  borderpad=0.4)
        ax.spines[['top', 'right']].set_visible(False)

    # Panel B: bar chart of L_total
    x_subj = np.array([1.0, 2.0]); w = 0.55
    L08 = packs['sub-08']['best']['L_total']
    L09 = packs['sub-09']['best']['L_total']
    bar08 = ax_b.bar(x_subj[0], L08, w, color=SUBJECTS[0][2], alpha=0.9)
    bar09 = ax_b.bar(x_subj[1], L09, w, color=SUBJECTS[1][2], alpha=0.9)
    for bar, sid in zip([bar08[0], bar09[0]], ['sub-08', 'sub-09']):
        best = packs[sid]['best']
        ax_b.text(bar.get_x() + bar.get_width() / 2,
                  bar.get_height() + 0.02,
                  f'(β_s={best["bs"]:.0f}, β_c={best["bc"]:+.0f})',
                  ha='center', va='bottom', fontsize=7)
    ax_b.set_xlim(0.0, 3.0); ax_b.set_xticks(x_subj)
    ax_b.set_xticklabels(['Sub-08\n(deutan)', 'Sub-09\n(protan)'])
    ax_b.set_ylabel('L_total at cycle12 argmin\n'
                    'L = l_topk(V4) + l_rank(V1) + 0.2·Tikh')
    ax_b.set_ylim(0, max(L08, L09) * 1.25)
    ax_b.set_title('Cycle12 cross-ROI loss (V4 l_topk + V1 l_rank, W-fixed)',
                   fontweight='bold', pad=3)
    ax_b.axhline(0, color='gray', lw=0.4)
    ax_b.spines[['top', 'right']].set_visible(False)

    # Panel C: L_total landscape
    VMIN = min(packs['sub-08']['L_total'].min(),
               packs['sub-09']['L_total'].min())
    VMAX = max(packs['sub-08']['L_total'].max(),
               packs['sub-09']['L_total'].max())

    for subj_id, fam, color in SUBJECTS:
        pack = packs[subj_id]
        ax = AX_C[subj_id]
        bs_arr = pack['bs']; bc_arr = pack['bc']
        L = pack['L_total']
        best = pack['best']
        # pcolormesh wants the transposed grid: bc on Y, bs on X
        im = ax.pcolormesh(bs_arr, bc_arr, L.T, cmap='viridis_r',
                           vmin=VMIN, vmax=VMAX, shading='nearest',
                           rasterized=True)
        ax.plot(best['bs'], best['bc'], '*', color='white', ms=10,
                zorder=10, markeredgecolor='black', markeredgewidth=0.6)
        lbl_ha = 'left' if best['bs'] < np.median(bs_arr) else 'right'
        lbl_x = best['bs'] + 1.5 if lbl_ha == 'left' else best['bs'] - 1.5
        lbl_va = 'bottom' if best['bc'] < np.median(bc_arr) else 'top'
        lbl_dy = 2.0 if lbl_va == 'bottom' else -2.0
        ax.text(lbl_x, best['bc'] + lbl_dy,
                f"β_s={best['bs']:.0f}°, β_c={best['bc']:+.0f}°\n"
                f"L={best['L_total']:.3f}\n"
                f"l_topk(V4)={best['l_topk_V4']:.2f}\n"
                f"l_rank(V1)={best['l_rank_V1']:.2f}",
                fontsize=7, color='white', va=lbl_va, ha=lbl_ha,
                zorder=11,
                bbox=dict(boxstyle='round,pad=0.2', facecolor='black',
                          alpha=0.55, lw=0))
        ax.set_xlabel('β_s — S-cone shift (°)')
        ax.set_ylabel('β_c — confusion rot. (°)')
        ax.set_title(f'{subj_id} ({fam})  L_total landscape',
                     fontweight='bold', pad=3)
        ax.spines[['top', 'right']].set_visible(False)

    cb = fig.colorbar(im, cax=ax_cb)
    cb.set_label('L_total', fontsize=7, labelpad=4)
    cb.ax.tick_params(labelsize=7)

    letter_kw = dict(fontsize=10, fontweight='bold', va='top', ha='left',
                     transform=fig.transFigure)
    fig.text(L_A - 0.025, B_B + H_B + 0.025, 'B', **letter_kw)
    fig.text(L_A - 0.025, B_R1 + H_AB_ROW + 0.025, 'A', **letter_kw)
    fig.text(L_C - 0.02, B_R1 + H_AB_ROW + 0.025, 'C', **letter_kw)

    out_png = RES / 'fig_F4_V4V1_cycle12.png'
    out_pdf = RES / 'fig_F4_V4V1_cycle12.pdf'
    fig.savefig(out_png, dpi=300, bbox_inches='tight', facecolor='white')
    fig.savefig(out_pdf, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'Wrote {out_png}')
    print(f'      {out_pdf}')

    # Print summary
    for subj_id, fam, _ in SUBJECTS:
        b = packs[subj_id]['best']
        print(f'{subj_id} ({fam}): argmin (β_s={b["bs"]:.0f}, β_c={b["bc"]:+.0f}) '
              f'L_total={b["L_total"]:.4f}')


if __name__ == '__main__':
    main()
