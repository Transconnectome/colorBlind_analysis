"""fixedW_onlyTest_v4ccc.py — V4 CCC loss on wfixed (A1) simulator, sub-08 + sub-09.

Reuses cached wfixed landscape JSONs (vuln_sim cached). Replaces (L_vuln + L_rank)
with single CCC term:
    CCC = 2·r·σ_sim·σ_obs / (σ_sim² + σ_obs² + (μ_sim - μ_obs)²)
    L_ccc = (1 - CCC) / 2

L_fit_V4 = 1.0 · L_ccc + 0.2 · L_rdm + 0.1 · L_smooth
(keeps L_rdm and L_smooth identical to canonical 4-term).

Outputs in results/fixedW_onlyTest/:
  - landscape_sub-XX_V4_wfixed_V4ccc_bsB_bcB.png
  - 4col_sub-XX_V4_wfixed_V4ccc_bsB_bcB.png
  - vuln_hue_sub-XX_V4_wfixed_V4ccc_bsB_bcB.png
  - F4_twocomp_wfixed_V4ccc.png
  - summary_V4ccc.json
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
from matplotlib.patches import Rectangle

_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR))
sys.path.insert(0, str(_THIS_DIR / 'visualization'))

from stim_lab_render import render_at_hue as _render_stim_lab
from phase3_loss_variant_helpers import generate_f4_style_figure
from phase3_candidate_analysis_v2 import (
    hc_name, hc_match_score, SUB08_ORIGINAL_HC_EQUIV,
)

_PHASE2 = _THIS_DIR.parent
OUTDIR = _PHASE2 / 'results' / 'fixedW_onlyTest'
OUTDIR.mkdir(parents=True, exist_ok=True)
SRCDIR = _PHASE2 / 'results' / 'old_formula'

THETA_CONF_DEG = 150.0
HUE_ANGLES = [0, 45, 90, 135, 180, 225, 270, 315]
COLOR_LABELS = ['c1 (red)', 'c2 (orange)', 'c3 (yellow)', 'c4 (green)',
                'c5 (cyan)', 'c6 (sky)', 'c7 (blue)', 'c8 (magenta)']

SUBJECTS = [
    ('08', 'deutan', '#E07B2C'),
    ('09', 'protan', '#2D8E8B'),
]

NORM = {'ccc': 2.0}
WEIGHTS = {'alpha_ccc': 1.0, 'delta_rdm': 0.2, 'epsilon_smooth': 0.1}


def dt_old(theta_deg, bs, bc, theta_conf_deg=THETA_CONF_DEG):
    th = np.deg2rad(theta_deg)
    return (bs * np.cos(th - np.deg2rad(90.0))
            + bc * np.cos(th - np.deg2rad(theta_conf_deg)))


def forward_old(theta_deg, bs, bc):
    dt = dt_old(theta_deg, bs, bc)
    return (theta_deg + dt) % 360.0, dt


def pre_image_old(target_deg, bs, bc, n_grid=3600):
    grid = np.linspace(0.0, 360.0, n_grid, endpoint=False)
    forwards = np.array([forward_old(t, bs, bc)[0] for t in grid])
    diff = (forwards - target_deg + 180.0) % 360.0 - 180.0
    i = int(np.argmin(np.abs(diff)))
    return float(grid[i]), float(diff[i])


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


def load_wfixed_landscape(sid):
    fn = SRCDIR / f'sub-{sid}_V4_wfixed_landscape.json'
    with open(fn) as f:
        ls = json.load(f)
    return ls if isinstance(ls, list) else ls.get('cells', ls)


def load_wfixed_summary(sid):
    fn = SRCDIR / f'sub-{sid}_V4_wfixed_summary.json'
    with open(fn) as f:
        return json.load(f)


def recompute_v4ccc(cells, vuln_cvd):
    """Add ccc, l_ccc, l_fit_V4ccc to each cell."""
    for c in cells:
        sim = np.asarray(c['vuln_sim'])
        ccc = ccc_value(sim, vuln_cvd)
        l_ccc = (1.0 - ccc) / NORM['ccc']
        l_rdm = c.get('l_rdm', 0.0)
        l_smooth = c.get('l_smooth', 0.0)
        l_fit_v4 = (WEIGHTS['alpha_ccc'] * l_ccc +
                    WEIGHTS['delta_rdm'] * l_rdm +
                    WEIGHTS['epsilon_smooth'] * l_smooth)
        c['ccc'] = float(ccc)
        c['l_ccc'] = float(l_ccc)
        c['l_fit_V4ccc'] = float(l_fit_v4)
    return cells


def landscape_to_grid(cells, key):
    bs_all = sorted(set(c['bs'] for c in cells))
    bc_all = sorted(set(c['bc'] for c in cells))
    arr = np.full((len(bc_all), len(bs_all)), np.nan)
    bs_idx = {v: i for i, v in enumerate(bs_all)}
    bc_idx = {v: i for i, v in enumerate(bc_all)}
    for c in cells:
        arr[bc_idx[c['bc']], bs_idx[c['bs']]] = c[key]
    return np.array(bs_all), np.array(bc_all), arr


def render_landscape(sid, cvd_type, color, cells, best, out_path):
    bs, bc, ccc = landscape_to_grid(cells, 'ccc')
    fig, ax = plt.subplots(figsize=(5.2, 4.8), dpi=150)
    im = ax.pcolormesh(bs, bc, ccc, cmap='RdBu_r',
                       vmin=-0.3, vmax=0.6, shading='nearest', rasterized=True)
    ax.plot(best['bs'], best['bc'], '*', color='white', ms=14,
            markeredgecolor='black', markeredgewidth=0.8, zorder=10)
    ax.text(best['bs'] + 2, best['bc'] - 2,
            f"β_s={best['bs']:.0f}°, β_c={best['bc']:+.0f}°\n"
            f"CCC={best['ccc']:.3f}\nρ={best['spearman_r']:.3f}",
            fontsize=9, color='white',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.55, lw=0))
    ax.set_xlabel('β_s — S-cone shift (°)')
    ax.set_ylabel('β_c — confusion rotation (°)')
    ax.set_title(f"sub-{sid} ({cvd_type}) V4 — wfixed + V4 CCC landscape",
                 fontweight='bold', color=color)
    cb = fig.colorbar(im, ax=ax, extend='min')
    cb.set_label('CCC')
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'  wrote {out_path.name}')


def render_4col(sid, cvd_type, color, bs, bc, ccc_val, out_path):
    n_rows = len(HUE_ANGLES)
    fig, axes = plt.subplots(n_rows, 4,
                             figsize=(5.5, 0.65 * n_rows + 0.8),
                             gridspec_kw={'hspace': 0.10, 'wspace': 0.05})
    fig.suptitle(
        f"sub-{sid} ({cvd_type}) V4 wfixed + V4 CCC — β_s={bs:.0f}°, β_c={bc:+.0f}°  "
        f"(norm={np.hypot(bs, bc):.1f}°, CCC={ccc_val:.3f})",
        fontsize=10, y=1.00, color=color, fontweight='bold')

    for j, ct in enumerate(['Original', 'CVD perceives',
                            'Filtered (pre-image)', 'CVD(Filtered)']):
        axes[0, j].set_title(ct, fontsize=8)

    p2a_total = 0.0
    p2a_exact = 0
    for i, theta in enumerate(HUE_ANGLES):
        theta_cvd, dt = forward_old(float(theta), bs, bc)
        theta_pre, resid = pre_image_old(float(theta), bs, bc)
        theta_cvd_pre, _ = forward_old(theta_pre, bs, bc)

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
        if sid == '08':
            pred_name = hc_name(theta_cvd)
            target_name = SUB08_ORIGINAL_HC_EQUIV[int(theta)]
            score = hc_match_score(pred_name, target_name)
            mark = '✓' if pred_name == target_name else ('~' if score > 0 else '✗')
            color_p2a = 'green' if score == 1.0 else ('darkorange' if score > 0 else 'red')
            axes[i, 1].text(0.5, -0.02, f'δθ={dt:+.0f}° {mark}',
                            ha='center', va='top', fontsize=7,
                            transform=axes[i, 1].transAxes, color=color_p2a)
            p2a_total += score
            if pred_name == target_name:
                p2a_exact += 1
        else:
            axes[i, 1].text(0.5, -0.02, f'δθ={dt:+.0f}°',
                            ha='center', va='top', fontsize=7,
                            transform=axes[i, 1].transAxes)
        axes[i, 2].text(0.5, -0.02, f'θ_pre={theta_pre:.0f}°',
                        ha='center', va='top', fontsize=7,
                        transform=axes[i, 2].transAxes)

    if sid == '08':
        fig.text(0.5, -0.005, f'P2a={p2a_total/8:.3f} ({p2a_exact}/8 exact)',
                 ha='center', fontsize=8, color=color)
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'  wrote {out_path.name}')


def render_vuln_hue(sid, cvd_type, color, vuln_cvd, vuln_sim, bs, bc, ccc_val, rho, out_path):
    fig, ax = plt.subplots(figsize=(6.5, 3.6), dpi=150)
    x = np.arange(8)
    labels_short = ['R', 'O', 'Y', 'G', 'C', 'B', 'P', 'M']

    ax.axhline(0, color='#aaaaaa', lw=0.5, ls=':')
    ax.plot(x, vuln_cvd, 'o-', color='#222222', ms=6, lw=0.8,
            label='Observed (CVD LOCO)')
    ax.plot(x, vuln_sim, 's-', color=color, ms=6, lw=1.5,
            label=f'wfixed+V4ccc sim (CCC={ccc_val:.3f}, ρ={rho:.3f})')
    ax.set_xticks(x); ax.set_xticklabels(labels_short)
    ax.set_xlabel('Hue (DKL bin)')
    ax.set_ylabel('LOCO vulnerability (voxel_corr)')
    ax.set_title(
        f"sub-{sid} ({cvd_type}) V4 — wfixed + V4 CCC argmin β_s={bs:.0f}°, β_c={bc:+.0f}°",
        fontweight='bold', color=color)
    ax.set_ylim(-1.0, 1.0)
    ax.legend(loc='best', fontsize=9)
    ax.spines[['top', 'right']].set_visible(False)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'  wrote {out_path.name}')


def make_f4_combined(sub08_cells, sub08_summary, sub09_cells, sub09_summary, out_path):
    cache_08 = {'vuln_cvd': sub08_summary['vuln_cvd']}
    cache_09 = {'vuln_cvd': sub09_summary['vuln_cvd']}
    # Re-tag l_fit with V4 CCC version so F4 helper picks correct argmin
    for c in sub08_cells:
        c['l_fit'] = c['l_fit_V4ccc']
    for c in sub09_cells:
        c['l_fit'] = c['l_fit_V4ccc']
    generate_f4_style_figure(
        variant_name='wfixed + V4 CCC',
        cache_08=cache_08, landscape_08=sub08_cells,
        cache_09=cache_09, landscape_09=sub09_cells,
        out_path=out_path,
        loss_label='L_fit_V4ccc',
        landscape_key='ccc',
        landscape_label='CCC',
    )
    print(f'  wrote {out_path.name}')


def main():
    print(f'OUTDIR: {OUTDIR}')
    summary_all = {}
    per_subject_info = []
    for sid, cvd_type, color in SUBJECTS:
        print(f'\n=== sub-{sid} {cvd_type} (V4 CCC on wfixed) ===')
        cells = load_wfixed_landscape(sid)
        summary = load_wfixed_summary(sid)
        vuln_cvd = np.array(summary['vuln_cvd'])
        cells = recompute_v4ccc(cells, vuln_cvd)

        best = min(cells, key=lambda c: c['l_fit_V4ccc'])
        bs, bc = best['bs'], best['bc']
        rho = best['spearman_r']
        ccc_val = best['ccc']
        vuln_sim = np.array(best['vuln_sim'])
        tag = f'bs{int(bs)}_bc{int(bc):+d}'

        print(f'  argmin: β_s={bs:.0f}, β_c={bc:+.0f}, norm={np.hypot(bs,bc):.1f}°')
        print(f'  CCC={ccc_val:.3f}, ρ={rho:.3f}, L_fit_V4ccc={best["l_fit_V4ccc"]:.4f}')

        render_landscape(sid, cvd_type, color, cells, best,
                         OUTDIR / f'landscape_sub-{sid}_V4_wfixed_V4ccc_{tag}.png')
        render_4col(sid, cvd_type, color, bs, bc, ccc_val,
                    OUTDIR / f'4col_sub-{sid}_V4_wfixed_V4ccc_{tag}.png')
        render_vuln_hue(sid, cvd_type, color, vuln_cvd, vuln_sim,
                        bs, bc, ccc_val, rho,
                        OUTDIR / f'vuln_hue_sub-{sid}_V4_wfixed_V4ccc_{tag}.png')

        summary_all[f'sub-{sid}'] = {
            'cvd_type': cvd_type,
            'bs': float(bs), 'bc': float(bc),
            'norm': float(np.hypot(bs, bc)),
            'ccc': float(ccc_val),
            'spearman_r': float(rho),
            'l_fit_V4ccc': float(best['l_fit_V4ccc']),
            'l_ccc': float(best['l_ccc']),
            'l_rdm': float(best.get('l_rdm', 0.0)),
            'l_smooth': float(best.get('l_smooth', 0.0)),
            'vuln_sim': vuln_sim.tolist(),
            'vuln_cvd': vuln_cvd.tolist(),
        }
        per_subject_info.append({'sid': sid, 'cells': cells, 'summary': summary})

    print('\n=== F4 combined (wfixed + V4 CCC) ===')
    make_f4_combined(
        per_subject_info[0]['cells'], per_subject_info[0]['summary'],
        per_subject_info[1]['cells'], per_subject_info[1]['summary'],
        OUTDIR / 'F4_twocomp_wfixed_V4ccc.png',
    )

    sjson = OUTDIR / 'summary_V4ccc.json'
    with open(sjson, 'w') as f:
        json.dump({
            'simulator': 'wfixed (A1 = shift_at_test_only)',
            'loss': 'L_fit_V4ccc = 1.0·L_ccc + 0.2·L_rdm + 0.1·L_smooth',
            'subjects': summary_all,
        }, f, indent=2)
    print(f'\nwrote {sjson.name}')


if __name__ == '__main__':
    main()
