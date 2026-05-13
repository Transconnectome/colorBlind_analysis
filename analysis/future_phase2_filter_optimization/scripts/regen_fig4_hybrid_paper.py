"""regen_fig4_hybrid_paper.py — paper Fig 4 under the HYBRID loss.

Layout follows docs/PAPER/Figures/fig4_twocomp.pdf:
  Panel B (top, full width): HYBRID loss decomposition bar at argmin
    (L_mse, L_rdm, Tikh) × subject, weighted by (w_pat, w_rdm, mu)
  Panel A (bottom-left, 2 rows): per-hue vulnerability profile at HYBRID argmin
  Panel C (bottom-right, 2 rows): L_HYBRID landscape with argmin star

Output: docs/PAPER/Figures/fig4_twocomp.{pdf,png}
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

_THIS_DIR = Path(__file__).resolve().parent
_PHASE2 = _THIS_DIR.parent
_REPO = _PHASE2.parent.parent
_PAPER_FIG = _REPO / 'docs' / 'PAPER' / 'Figures'

HYBRID = [
    {'sid': '08', 'family': 'deutan', 'color': '#E07B2C',
     'axis': 150.0, 'bs': 16.0, 'bc': 40.0,
     'landscape': _PHASE2 / 'results' / 'axis_3way' / 'sub-08_V4_Stockman150_landscape.json'},
    {'sid': '09', 'family': 'protan', 'color': '#2D8E8B',
     'axis': 16.0, 'bs': 12.0, 'bc': -30.0,
     'landscape': _PHASE2 / 'results' / 'axis_3way' / 'sub-09_V4_Stockman16ext_landscape.json'},
]

W_PAT, W_RDM, MU = 0.7, 0.3, 2.0
TIKH_NORM = 32400.0  # max(β²+β²) at (50,50), normalises Tikh to [0,~0.077]

matplotlib.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Helvetica', 'Arial', 'DejaVu Sans'],
    'font.size': 8, 'axes.titlesize': 9, 'axes.labelsize': 8,
    'xtick.labelsize': 7.5, 'ytick.labelsize': 7.5, 'legend.fontsize': 7.5,
    'axes.linewidth': 0.6, 'xtick.major.width': 0.6, 'ytick.major.width': 0.6,
    'pdf.fonttype': 42, 'ps.fonttype': 42,
})


def rdm_cosine_dist(sim, obs):
    iu = np.triu_indices(len(sim), k=1)
    r_s = np.abs(sim[:, None] - sim[None, :])[iu]
    r_o = np.abs(obs[:, None] - obs[None, :])[iu]
    ns, no = np.linalg.norm(r_s), np.linalg.norm(r_o)
    if ns < 1e-10 or no < 1e-10:
        return 1.0
    return float(1.0 - np.dot(r_s, r_o) / (ns * no)) / 2


def compute_components(landscape_path, bs_t, bc_t):
    d = json.load(open(landscape_path))
    cells = d['cells']
    vuln_obs = np.array(d['vuln_cvd'])

    # Whole-grid components for landscape rendering
    L_mse_raw = np.array([
        float(np.mean((np.array(c['vuln_sim']) - vuln_obs) ** 2))
        for c in cells])
    L_mse_n = L_mse_raw / L_mse_raw.max() if L_mse_raw.max() > 0 else L_mse_raw
    L_rdm = np.array([rdm_cosine_dist(np.array(c['vuln_sim']), vuln_obs)
                      for c in cells])
    bs_full = np.array([c['bs'] for c in cells])
    bc_full = np.array([c['bc'] for c in cells])
    tikh = (bs_full ** 2 + bc_full ** 2) / TIKH_NORM
    L_hybrid = W_PAT * L_mse_n + W_RDM * L_rdm + MU * tikh

    # Argmin cell
    target_idx = None
    for i, c in enumerate(cells):
        if abs(c['bs'] - bs_t) < 1e-3 and abs(c['bc'] - bc_t) < 1e-3:
            target_idx = i
            break
    assert target_idx is not None, f'cell ({bs_t}, {bc_t}) not found'
    vuln_sim_argmin = np.array(cells[target_idx]['vuln_sim'])

    return {
        'vuln_obs': vuln_obs,
        'vuln_sim_argmin': vuln_sim_argmin,
        'L_mse_n_argmin': float(L_mse_n[target_idx]),
        'L_rdm_argmin': float(L_rdm[target_idx]),
        'tikh_argmin': float(tikh[target_idx]),
        'L_hybrid_argmin': float(L_hybrid[target_idx]),
        'L_hybrid_grid': L_hybrid,
        'bs_full': bs_full,
        'bc_full': bc_full,
        'bs_axis': np.array(sorted(set(bs_full))),
        'bc_axis': np.array(sorted(set(bc_full))),
    }


def render():
    data = {info['sid']: compute_components(info['landscape'], info['bs'], info['bc'])
            for info in HYBRID}

    fig = plt.figure(figsize=(8.5, 7.2))
    gs = fig.add_gridspec(3, 2, height_ratios=[1.0, 1.3, 1.3],
                          hspace=0.50, wspace=0.32,
                          left=0.08, right=0.96, top=0.92, bottom=0.07)

    # ── Panel B (top, full width) — HYBRID decomposition bar ─────────────
    ax_b = fig.add_subplot(gs[0, :])
    comps = ['$w_{pat}\\cdot L_{mse}$', '$w_{rdm}\\cdot L_{rdm}$', '$\\mu\\cdot\\|\\beta\\|^2$', 'L (total)']
    x = np.arange(len(comps))
    w = 0.36
    vals_08 = np.array([
        W_PAT * data['08']['L_mse_n_argmin'],
        W_RDM * data['08']['L_rdm_argmin'],
        MU * data['08']['tikh_argmin'],
        data['08']['L_hybrid_argmin'],
    ])
    vals_09 = np.array([
        W_PAT * data['09']['L_mse_n_argmin'],
        W_RDM * data['09']['L_rdm_argmin'],
        MU * data['09']['tikh_argmin'],
        data['09']['L_hybrid_argmin'],
    ])
    ax_b.bar(x - w / 2, vals_08, w, color=HYBRID[0]['color'], alpha=0.85,
             label='sub-08 (deutan)')
    ax_b.bar(x + w / 2, vals_09, w, color=HYBRID[1]['color'], alpha=0.85,
             label='sub-09 (protan)')
    for i, (a, b) in enumerate(zip(vals_08, vals_09)):
        ax_b.text(i - w / 2, a + 0.002, f'{a:.3f}', ha='center', fontsize=7)
        ax_b.text(i + w / 2, b + 0.002, f'{b:.3f}', ha='center', fontsize=7)
    ax_b.set_xticks(x)
    ax_b.set_xticklabels(comps, fontsize=8.5)
    ax_b.set_ylabel('Contribution to L')
    ax_b.set_title(r'$\bf{B}$  HYBRID-loss decomposition at argmin',
                   fontweight='bold', fontsize=9, loc='left')
    ax_b.legend(loc='upper left', fontsize=6.5, frameon=True,
                framealpha=0.85, borderpad=0.25, handlelength=1.1,
                handletextpad=0.4)
    ax_b.spines[['top', 'right']].set_visible(False)

    # ── Panel A (bottom-left, 2 rows) — per-hue vulnerability profile ───
    hue_labels = ['R', 'O', 'Y', 'G', 'C', 'B', 'P', 'M']
    for row, info in enumerate(HYBRID):
        ax = fig.add_subplot(gs[1 + row, 0])
        d = data[info['sid']]
        xh = np.arange(8)
        ax.axhline(0, color='#aaa', lw=0.5, ls=':')
        ax.plot(xh, d['vuln_obs'], 'o-', color='#222', ms=6, lw=0.9, label='Observed')
        ax.plot(xh, d['vuln_sim_argmin'], 's-', color=info['color'],
                ms=7, lw=1.6,
                label=f'HYBRID sim @ ({info["bs"]:.0f}°, {info["bc"]:+.0f}°)')
        ax.set_xticks(xh); ax.set_xticklabels(hue_labels)
        ax.set_ylabel('LOCO vulnerability')
        ax.set_ylim(-1, 1)
        title_lr = r'$\bf{A}$  ' if row == 0 else ''
        ax.set_title(f'{title_lr}sub-{info["sid"]} ({info["family"]}) — per-hue '
                     f'vulnerability profile',
                     fontweight='bold', color=info['color'], fontsize=8.5,
                     loc='left')
        ax.legend(loc='lower right', fontsize=7)
        ax.spines[['top', 'right']].set_visible(False)

    # ── Panel C (bottom-right, 2 rows) — L_hybrid landscape ─────────────
    for row, info in enumerate(HYBRID):
        ax = fig.add_subplot(gs[1 + row, 1])
        d = data[info['sid']]
        bs_axis, bc_axis = d['bs_axis'], d['bc_axis']
        L_grid = np.full((len(bc_axis), len(bs_axis)), np.nan)
        bs_idx = {v: i for i, v in enumerate(bs_axis)}
        bc_idx = {v: i for i, v in enumerate(bc_axis)}
        for k in range(len(d['bs_full'])):
            L_grid[bc_idx[d['bc_full'][k]], bs_idx[d['bs_full'][k]]] = \
                d['L_hybrid_grid'][k]
        # Standard loss-landscape convention: low L (good fit) = blue,
        # high L = red.  argmin star sits in the deep-blue valley.
        vmin, vmax = np.nanpercentile(L_grid, [5, 95])
        extent = [bs_axis.min() - 1, bs_axis.max() + 1,
                  bc_axis.min() - 1, bc_axis.max() + 1]
        im = ax.imshow(L_grid, origin='lower', extent=extent, aspect='auto',
                       cmap='RdBu_r', vmin=vmin, vmax=vmax)
        plt.colorbar(im, ax=ax, label=r'$L_\mathrm{hybrid}$ (low = good fit)',
                     fraction=0.046, pad=0.03)
        ax.plot(info['bs'], info['bc'], '*', mfc='white', mec='black',
                ms=18, mew=1.4, zorder=10)
        ax.axhline(0, color='gray', lw=0.4)
        ax.axvline(0, color='gray', lw=0.4)
        ax.set_xlabel(r'$\beta_s$ — S-cone shift (°)')
        ax.set_ylabel(r'$\beta_c$ — cortical rotation (°)')
        title_lr = r'$\bf{C}$  ' if row == 0 else ''
        ax.set_title(f'{title_lr}sub-{info["sid"]} ({info["family"]}) — '
                     r'$L_\mathrm{hybrid}$ landscape',
                     fontweight='bold', color=info['color'], fontsize=8.5,
                     loc='left')

    fig.suptitle('Fig 4 — A neural-primary HYBRID-loss fit recovers '
                 'per-subject 2-component distortion at hV4',
                 fontsize=11, fontweight='bold', y=0.985)

    _PAPER_FIG.mkdir(parents=True, exist_ok=True)
    out_pdf = _PAPER_FIG / 'fig4_twocomp.pdf'
    out_png = _PAPER_FIG / 'fig4_twocomp.png'
    plt.savefig(out_pdf, bbox_inches='tight')
    plt.savefig(out_png, dpi=200, bbox_inches='tight')
    plt.close(fig)
    print(f'wrote {out_pdf}')
    print(f'wrote {out_png}')


if __name__ == '__main__':
    render()
