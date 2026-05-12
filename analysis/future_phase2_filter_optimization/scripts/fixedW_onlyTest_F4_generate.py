"""fixedW_onlyTest_F4_generate.py — F4-style figures matching fig_F4_V4_4term.png layout.

Generates F4 figures for 2x2 diagnostic comparison (loss × simulator):
  - fig_F4_V4_wfixed_4term.png  : wfixed simulator + canonical 4-term L_fit
  - fig_F4_V4_wfixed_V4ccc.png  : wfixed simulator + V4 CCC loss

Reference: results/old_formula/fig_F4_V4_4term.png (wretrained + 4-term)
Output: results/fixedW_onlyTest/

V4 CCC loss: L_fit_V4ccc = 1.0·L_ccc + 0.2·L_rdm + 0.1·L_smooth
where L_ccc = (1 - CCC)/2.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import pearsonr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR))

_PHASE2 = _THIS_DIR.parent
SRC = _PHASE2 / 'results' / 'old_formula'
OUT = _PHASE2 / 'results' / 'fixedW_onlyTest'
OUT.mkdir(parents=True, exist_ok=True)

COL_08 = '#E07B2C'; COL_09 = '#2D8E8B'; COL_OBS = '#222222'
HUE_LABELS = ['R', 'O', 'Y', 'G', 'C', 'B', 'P', 'M']
HUE_X = np.arange(8)

matplotlib.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Helvetica', 'Arial', 'DejaVu Sans'],
    'font.size': 7, 'axes.titlesize': 7.5, 'axes.labelsize': 7,
    'xtick.labelsize': 7, 'ytick.labelsize': 7, 'legend.fontsize': 7,
    'axes.linewidth': 0.6, 'xtick.major.width': 0.6, 'ytick.major.width': 0.6,
    'xtick.major.size': 2.5, 'ytick.major.size': 2.5, 'lines.linewidth': 1.0,
    'pdf.fonttype': 42, 'ps.fonttype': 42,
})


def load_wfixed(sid):
    ls = json.load(open(SRC / f'sub-{sid}_V4_wfixed_landscape.json'))
    summ = json.load(open(SRC / f'sub-{sid}_V4_wfixed_summary.json'))
    cells = ls if isinstance(ls, list) else ls.get('cells', ls)
    return cells, summ


def ccc_value(sim, obs):
    sim = np.asarray(sim); obs = np.asarray(obs)
    if np.std(sim) < 1e-10 or np.std(obs) < 1e-10:
        return 0.0
    r, _ = pearsonr(sim, obs)
    if not np.isfinite(r):
        return 0.0
    msim = sim.mean(); mobs = obs.mean()
    ssim = sim.std(); sobs = obs.std()
    denom = ssim**2 + sobs**2 + (msim - mobs)**2
    if denom < 1e-10:
        return 0.0
    return 2.0 * r * ssim * sobs / denom


def compute_v4ccc(cells, vuln_cvd):
    for c in cells:
        sim = np.asarray(c['vuln_sim'])
        ccc = ccc_value(sim, vuln_cvd)
        c['ccc'] = float(ccc)
        c['l_ccc'] = float((1.0 - ccc) / 2.0)
        c['l_fit_V4ccc'] = float(
            1.0 * c['l_ccc'] + 0.2 * c.get('l_rdm', 0.0) + 0.1 * c.get('l_smooth', 0.0)
        )
    return cells


def build_grid(cells, key):
    bs_all = sorted(set(c['bs'] for c in cells))
    bc_all = sorted(set(c['bc'] for c in cells))
    arr = np.full((len(bc_all), len(bs_all)), np.nan)
    bs_idx = {v: i for i, v in enumerate(bs_all)}
    bc_idx = {v: i for i, v in enumerate(bc_all)}
    for c in cells:
        arr[bc_idx[c['bc']], bs_idx[c['bs']]] = c[key]
    return np.array(bs_all), np.array(bc_all), arr


def sig_label(p):
    if p is None:
        return 'n/a'
    if p < 0.01: return '**'
    if p < 0.05: return '*'
    return 'n.s.'


def make_f4_figure(
    cells_08, summ_08, cells_09, summ_09,
    sim_label, loss_label, loss_key,
    rho_landscape_key, landscape_label,
    rho_vmin, rho_vmax,
    out_path,
    title_extra,
    perm_p_08=None, perm_p_09=None,
):
    """Generic F4 figure builder.
    loss_key: which loss field to argmin on (l_fit or l_fit_V4ccc).
    rho_landscape_key: which field colors the landscape (spearman_r or ccc).
    """
    b08 = min(cells_08, key=lambda c: c[loss_key])
    b09 = min(cells_09, key=lambda c: c[loss_key])
    vuln_obs_08 = np.array(summ_08['vuln_cvd'])
    vuln_obs_09 = np.array(summ_09['vuln_cvd'])
    vuln_sim_08 = np.array(b08['vuln_sim'])
    vuln_sim_09 = np.array(b09['vuln_sim'])
    bs08, bc08, grid08 = build_grid(cells_08, rho_landscape_key)
    bs09, bc09, grid09 = build_grid(cells_09, rho_landscape_key)

    fig = plt.figure(figsize=(7.087, 7.0), dpi=300)
    L_A = 0.07; W_A = 0.33; L_C = 0.46; W_C = 0.44; L_CB = 0.915; W_CB = 0.016
    H_AB_ROW = 0.27; H_B = 0.150
    B_R2 = 0.050; B_R1 = B_R2 + H_AB_ROW + 0.070; B_B = B_R1 + H_AB_ROW + 0.075

    ax_a08 = fig.add_axes([L_A, B_R1, W_A, H_AB_ROW])
    ax_c08 = fig.add_axes([L_C, B_R1, W_C, H_AB_ROW])
    ax_a09 = fig.add_axes([L_A, B_R2, W_A, H_AB_ROW])
    ax_c09 = fig.add_axes([L_C, B_R2, W_C, H_AB_ROW])
    ax_cb = fig.add_axes([L_CB, B_R2, W_CB, B_R1 + H_AB_ROW - B_R2])
    ax_b = fig.add_axes([L_A, B_B, L_CB - L_A - 0.01, H_B])

    def plot_vuln(ax, vobs, vsim, color, subj, cvdtype, b, p):
        ax.axhline(0, color='#aaaaaa', lw=0.5, ls=':')
        ax.plot(HUE_X, vobs, 'o-', color=COL_OBS, ms=3.5, lw=0.6,
                label='Observed (CVD)')
        ax.plot(HUE_X, vsim, '-', color=color, lw=1.8,
                label=f"{loss_label}  ρ={b['spearman_r']:.2f} {sig_label(p)}")
        ax.set_xticks(HUE_X); ax.set_xticklabels(HUE_LABELS)
        ax.set_xlabel('Hue (DKL)'); ax.set_ylabel('LOCO vulnerability')
        ax.set_ylim(-1.0, 1.0)
        ax.set_title(f"{subj}  ({cvdtype})", fontweight='bold', pad=3)
        ax.legend(loc='upper right', handlelength=1.8, handletextpad=0.3, borderpad=0.4)
        ax.spines[['top', 'right']].set_visible(False)

    plot_vuln(ax_a08, vuln_obs_08, vuln_sim_08, COL_08, 'Sub-08', 'deutan',
              b08, perm_p_08)
    plot_vuln(ax_a09, vuln_obs_09, vuln_sim_09, COL_09, 'Sub-09', 'protan',
              b09, perm_p_09)

    # Panel B (top bar)
    x_subj = np.array([1.0, 2.0]); w = 0.55
    bar08 = ax_b.bar(x_subj[0], b08['spearman_r'], w, color=COL_08, alpha=0.9)
    bar09 = ax_b.bar(x_subj[1], b09['spearman_r'], w, color=COL_09, alpha=0.9)

    def bar_annot(ax, bar, p, color):
        h = max(bar.get_height(), 0)
        ax.text(bar.get_x() + bar.get_width()/2, h + 0.022,
                sig_label(p), ha='center', va='bottom',
                fontsize=8.0, color=color, fontweight='bold')

    bar_annot(ax_b, bar08[0], perm_p_08, COL_08)
    bar_annot(ax_b, bar09[0], perm_p_09, COL_09)
    ax_b.set_xlim(0.0, 3.0); ax_b.set_xticks(x_subj)
    ax_b.set_xticklabels(['Sub-08\n(deutan)', 'Sub-09\n(protan)'])
    ax_b.set_ylabel(f'Spearman ρ\n(V4 LOCO, {sim_label} {loss_label})')
    ax_b.set_ylim(-0.5, 1.10)
    ax_b.set_title(title_extra, fontweight='bold', pad=3)
    ax_b.axhline(0, color='gray', lw=0.4)
    ax_b.spines[['top', 'right']].set_visible(False)

    # Panel C
    def plot_ls(ax, bs, bc, grid, best, p, color, subj, cvdtype):
        im = ax.pcolormesh(bs, bc, grid, cmap='RdBu_r',
                           vmin=rho_vmin, vmax=rho_vmax,
                           shading='nearest', rasterized=True)
        ax.plot(best['bs'], best['bc'], '*', color='white', ms=9, zorder=10,
                markeredgecolor='black', markeredgewidth=0.5)
        lbl_ha = 'left' if best['bs'] < np.median(bs) else 'right'
        lbl_x = best['bs'] + 1.5 if lbl_ha == 'left' else best['bs'] - 1.5
        lbl_va = 'bottom' if best['bc'] < np.median(bc) else 'top'
        lbl_dy = 2.0 if lbl_va == 'bottom' else -2.0
        # Annotation text — show argmin location, ρ, key loss value
        loss_show = best.get(loss_key, best.get('l_fit', 0.0))
        ax.text(lbl_x, best['bc'] + lbl_dy,
                f"β_s={best['bs']:.0f}°, β_c={best['bc']:+.0f}°\n"
                f"ρ={best['spearman_r']:.2f} {sig_label(p)}\n"
                f"{loss_key}={loss_show:.3f}",
                fontsize=7, color='white', va=lbl_va, ha=lbl_ha, zorder=11,
                bbox=dict(boxstyle='round,pad=0.2', facecolor='black', alpha=0.55, lw=0))
        ax.set_xlabel('β_s — S-cone shift (°)')
        ax.set_ylabel('β_c — confusion rot. (°)')
        ax.set_title(f"{subj}  ({cvdtype})", fontweight='bold', pad=3)
        ax.spines[['top', 'right']].set_visible(False)
        return im

    im08 = plot_ls(ax_c08, bs08, bc08, grid08, b08, perm_p_08,
                   COL_08, 'Sub-08', 'deutan')
    im09 = plot_ls(ax_c09, bs09, bc09, grid09, b09, perm_p_09,
                   COL_09, 'Sub-09', 'protan')
    cb = fig.colorbar(im09, cax=ax_cb, extend='min')
    cb.set_label(landscape_label, fontsize=7, labelpad=4)
    cb.ax.tick_params(labelsize=7)

    letter_kw = dict(fontsize=10, fontweight='bold', va='top', ha='left',
                     transform=fig.transFigure)
    fig.text(L_A - 0.025, B_B + H_B + 0.025, 'B', **letter_kw)
    fig.text(L_A - 0.025, B_R1 + H_AB_ROW + 0.025, 'A', **letter_kw)
    fig.text(L_C - 0.02, B_R1 + H_AB_ROW + 0.025, 'C', **letter_kw)

    fig.savefig(out_path, dpi=300, bbox_inches='tight', facecolor='white')
    pdf_path = str(out_path).replace('.png', '.pdf')
    fig.savefig(pdf_path, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'  wrote {out_path.name}')
    return b08, b09


def main():
    print('Loading wfixed landscapes...')
    cells_08, summ_08 = load_wfixed('08')
    cells_09, summ_09 = load_wfixed('09')

    # ---- Figure 1: wfixed + 4-term ----
    print('\n=== wfixed + 4-term ===')
    b08_4t, b09_4t = make_f4_figure(
        cells_08, summ_08, cells_09, summ_09,
        sim_label='wfixed',
        loss_label='wfixed 4-term',
        loss_key='l_fit',
        rho_landscape_key='spearman_r',
        landscape_label='Spearman ρ',
        rho_vmin=-0.5, rho_vmax=0.90,
        out_path=OUT / 'fig_F4_V4_wfixed_4term.png',
        title_extra='wfixed (A1) 2-component fit (V4, 4-term L_fit: vuln+rank+rdm+smooth)',
    )

    # ---- Figure 2: wfixed + V4 CCC ----
    print('\n=== wfixed + V4 CCC ===')
    vuln_cvd_08 = np.array(summ_08['vuln_cvd'])
    vuln_cvd_09 = np.array(summ_09['vuln_cvd'])
    cells_08_ccc = compute_v4ccc([dict(c) for c in cells_08], vuln_cvd_08)
    cells_09_ccc = compute_v4ccc([dict(c) for c in cells_09], vuln_cvd_09)
    b08_ccc, b09_ccc = make_f4_figure(
        cells_08_ccc, summ_08, cells_09_ccc, summ_09,
        sim_label='wfixed',
        loss_label='wfixed V4-CCC',
        loss_key='l_fit_V4ccc',
        rho_landscape_key='ccc',
        landscape_label='CCC',
        rho_vmin=-0.3, rho_vmax=0.6,
        out_path=OUT / 'fig_F4_V4_wfixed_V4ccc.png',
        title_extra='wfixed (A1) 2-component fit (V4, V4-CCC L_fit: ccc+rdm+smooth)',
    )

    # ---- Diagnostic summary ----
    print('\n' + '='*70)
    print('DIAGNOSTIC SUMMARY — 2x2 (simulator × loss)')
    print('='*70)
    # wretrained 4-term values (from existing fig_F4_V4_4term.png)
    print(f'  (wretrained, 4-term)  sub-08: β=(10, -32) ρ=0.83 **')
    print(f'                        sub-09: β=(30, +46) ρ=0.50 n.s.')
    print(f'  (wfixed,     4-term)  sub-08: β=({b08_4t["bs"]:.0f}, {b08_4t["bc"]:+.0f}) ρ={b08_4t["spearman_r"]:.2f}')
    print(f'                        sub-09: β=({b09_4t["bs"]:.0f}, {b09_4t["bc"]:+.0f}) ρ={b09_4t["spearman_r"]:.2f}')
    print(f'  (wfixed,     V4-CCC)  sub-08: β=({b08_ccc["bs"]:.0f}, {b08_ccc["bc"]:+.0f}) ρ={b08_ccc["spearman_r"]:.2f}')
    print(f'                        sub-09: β=({b09_ccc["bs"]:.0f}, {b09_ccc["bc"]:+.0f}) ρ={b09_ccc["spearman_r"]:.2f}')
    print()
    # Δρ analysis
    print('Δρ analysis (sub-08 / sub-09):')
    print(f'  Setup change (wretrained→wfixed, 4-term):')
    print(f'    sub-08: 0.83 → {b08_4t["spearman_r"]:.2f} (Δ = {b08_4t["spearman_r"]-0.83:+.2f})')
    print(f'    sub-09: 0.50 → {b09_4t["spearman_r"]:.2f} (Δ = {b09_4t["spearman_r"]-0.50:+.2f})')
    print(f'  Loss change (4-term→V4-CCC, wfixed):')
    print(f'    sub-08: {b08_4t["spearman_r"]:.2f} → {b08_ccc["spearman_r"]:.2f} (Δ = {b08_ccc["spearman_r"]-b08_4t["spearman_r"]:+.2f})')
    print(f'    sub-09: {b09_4t["spearman_r"]:.2f} → {b09_ccc["spearman_r"]:.2f} (Δ = {b09_ccc["spearman_r"]-b09_4t["spearman_r"]:+.2f})')


if __name__ == '__main__':
    main()
