"""fixedW_onlyTest_visualize.py — generate fixedW (A1) figures for Phase 2 cycle.

Subjects: sub-08, sub-09, sub-10 (V4, OLD CIElab-direct 2-component, wfixed simulator).
(β_s, β_c) = wfixed argmin per subject.

Outputs in results/fixedW_onlyTest/:
  - landscape_sub-XX_V4_wfixed_bsB_bcB.png        (Spearman ρ heatmap with argmin star)
  - 4col_sub-XX_V4_wfixed_bsB_bcB.png             (Original/CVD perceives/Filtered/CVD-filt)
  - vuln_hue_sub-XX_V4_wfixed_bsB_bcB.png         (per-color vuln line graph)
  - F4_twocomp_wfixed.pdf                          (combined sub-08 + sub-09 F4 style)
  - README.md
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
from phase3_loss_variant_helpers import generate_f4_style_figure
from phase3_candidate_analysis_v2 import (
    hc_name, hc_match_score, SUB08_ORIGINAL_HC_EQUIV,
)

_PHASE2 = _THIS_DIR.parent
OUTDIR = _PHASE2 / 'results' / 'fixedW_onlyTest'
OUTDIR.mkdir(parents=True, exist_ok=True)
SRCDIR = _PHASE2 / 'results' / 'old_formula'

THETA_CONF_DEG = 150.0  # OLD formula convention, applied to both subjects
HUE_ANGLES = [0, 45, 90, 135, 180, 225, 270, 315]
COLOR_LABELS = ['c1 (red)', 'c2 (orange)', 'c3 (yellow)', 'c4 (green)',
                'c5 (cyan)', 'c6 (sky)', 'c7 (blue)', 'c8 (magenta)']

SUBJECTS = [
    ('08', 'deutan', '#E07B2C'),
    ('09', 'protan', '#2D8E8B'),
    ('10', 'near-normal', '#7E7E7E'),
]


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


def load_wfixed_landscape(sid):
    fn = SRCDIR / f'sub-{sid}_V4_wfixed_landscape.json'
    with open(fn) as f:
        ls = json.load(f)
    if isinstance(ls, list):
        cells = ls
    else:
        cells = ls.get('cells', ls)
    return cells


def load_wfixed_summary(sid):
    fn = SRCDIR / f'sub-{sid}_V4_wfixed_summary.json'
    with open(fn) as f:
        return json.load(f)


def landscape_to_grid(cells, key='spearman_r'):
    bs_all = sorted(set(c['bs'] for c in cells))
    bc_all = sorted(set(c['bc'] for c in cells))
    arr = np.full((len(bc_all), len(bs_all)), np.nan)
    bs_idx = {v: i for i, v in enumerate(bs_all)}
    bc_idx = {v: i for i, v in enumerate(bc_all)}
    for c in cells:
        arr[bc_idx[c['bc']], bs_idx[c['bs']]] = c[key]
    return np.array(bs_all), np.array(bc_all), arr


def render_landscape(sid, cvd_type, color, cells, best, out_path):
    bs, bc, rho = landscape_to_grid(cells, 'spearman_r')
    fig, ax = plt.subplots(figsize=(5.2, 4.8), dpi=150)
    im = ax.pcolormesh(bs, bc, rho, cmap='RdBu_r',
                       vmin=-0.5, vmax=0.9, shading='nearest', rasterized=True)
    ax.plot(best['bs'], best['bc'], '*', color='white', ms=14,
            markeredgecolor='black', markeredgewidth=0.8, zorder=10)
    ax.text(best['bs'] + 2, best['bc'] - 2,
            f"β_s={best['bs']:.0f}°, β_c={best['bc']:+.0f}°\n"
            f"ρ={best['spearman_r']:.3f}",
            fontsize=9, color='white',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.55, lw=0))
    ax.set_xlabel('β_s — S-cone shift (°)')
    ax.set_ylabel('β_c — confusion rotation (°)')
    ax.set_title(f"sub-{sid} ({cvd_type}) V4 — wfixed (A1) landscape",
                 fontweight='bold', color=color)
    cb = fig.colorbar(im, ax=ax, extend='min')
    cb.set_label('Spearman ρ')
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'  wrote {out_path.name}')


def render_4col(sid, cvd_type, color, bs, bc, out_path):
    """Original / CVD perceives / Filtered (pre-image) / CVD(Filtered)."""
    n_rows = len(HUE_ANGLES)
    fig, axes = plt.subplots(n_rows, 4,
                             figsize=(5.5, 0.65 * n_rows + 0.8),
                             gridspec_kw={'hspace': 0.10, 'wspace': 0.05})
    fig.suptitle(
        f"sub-{sid} ({cvd_type}) V4 wfixed — β_s={bs:.0f}°, β_c={bc:+.0f}°  "
        f"(norm={np.hypot(bs, bc):.1f}°)",
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


def render_vuln_hue(sid, cvd_type, color, vuln_cvd, vuln_sim, bs, bc, rho, out_path):
    fig, ax = plt.subplots(figsize=(6.5, 3.6), dpi=150)
    x = np.arange(8)
    labels_short = ['R', 'O', 'Y', 'G', 'C', 'B', 'P', 'M']

    ax.axhline(0, color='#aaaaaa', lw=0.5, ls=':')
    ax.plot(x, vuln_cvd, 'o-', color='#222222', ms=6, lw=0.8,
            label='Observed (CVD LOCO)')
    ax.plot(x, vuln_sim, 's-', color=color, ms=6, lw=1.5,
            label=f'wfixed sim @ argmin (ρ={rho:.3f})')
    ax.set_xticks(x); ax.set_xticklabels(labels_short)
    ax.set_xlabel('Hue (DKL bin)')
    ax.set_ylabel('LOCO vulnerability (voxel_corr)')
    ax.set_title(
        f"sub-{sid} ({cvd_type}) V4 — wfixed argmin β_s={bs:.0f}°, β_c={bc:+.0f}°",
        fontweight='bold', color=color)
    ax.set_ylim(-1.0, 1.0)
    ax.legend(loc='best', fontsize=9)
    ax.spines[['top', 'right']].set_visible(False)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'  wrote {out_path.name}')


def make_f4_combined(sub08_cells, sub08_summary, sub09_cells, sub09_summary, out_path):
    """Use existing F4 helper. Pre-shape data to its API."""
    # Both args expect dict with 'vuln_cvd' and the landscape list with 'l_fit' / 'vuln_sim'.
    cache_08 = {'vuln_cvd': sub08_summary['vuln_cvd']}
    cache_09 = {'vuln_cvd': sub09_summary['vuln_cvd']}
    # Landscapes already have l_fit + vuln_sim + delta_theta
    generate_f4_style_figure(
        variant_name='wfixed (A1)',
        cache_08=cache_08, landscape_08=sub08_cells,
        cache_09=cache_09, landscape_09=sub09_cells,
        out_path=out_path,
        loss_label='L_fit',
        landscape_key='spearman_r',
        landscape_label='Spearman ρ',
    )
    print(f'  wrote {out_path.name}')


def main():
    print(f'OUTDIR: {OUTDIR}')
    per_subject_info = []
    for sid, cvd_type, color in SUBJECTS:
        print(f'\n=== sub-{sid} {cvd_type} ===')
        cells = load_wfixed_landscape(sid)
        summary = load_wfixed_summary(sid)
        best = min(cells, key=lambda c: c['l_fit'])
        bs, bc = best['bs'], best['bc']
        rho = best['spearman_r']
        vuln_cvd = np.array(summary['vuln_cvd'])
        vuln_sim = np.array(best['vuln_sim'])
        tag = f'bs{int(bs)}_bc{int(bc):+d}'

        # 1. Landscape
        render_landscape(sid, cvd_type, color, cells, best,
                         OUTDIR / f'landscape_sub-{sid}_V4_wfixed_{tag}.png')

        # 2. 4-column color figure
        render_4col(sid, cvd_type, color, bs, bc,
                    OUTDIR / f'4col_sub-{sid}_V4_wfixed_{tag}.png')

        # 3. Vuln line graph
        render_vuln_hue(sid, cvd_type, color, vuln_cvd, vuln_sim, bs, bc, rho,
                        OUTDIR / f'vuln_hue_sub-{sid}_V4_wfixed_{tag}.png')

        per_subject_info.append({
            'sid': sid, 'cvd_type': cvd_type,
            'bs': bs, 'bc': bc, 'norm': float(np.hypot(bs, bc)),
            'rho': rho, 'l_fit': best['l_fit'],
            'cells': cells, 'summary': summary,
        })

    # F4 combined sub-08 + sub-09 (sub-10 = null, separate)
    print('\n=== F4 combined ===')
    sub08 = per_subject_info[0]
    sub09 = per_subject_info[1]
    make_f4_combined(
        sub08['cells'], sub08['summary'],
        sub09['cells'], sub09['summary'],
        OUTDIR / 'F4_twocomp_wfixed.png',
    )

    # README
    write_readme(per_subject_info)


def write_readme(info_list):
    md = []
    md.append('# fixedW_onlyTest — wfixed (A1) Visualization')
    md.append('')
    md.append('Generated from `scripts/fixedW_onlyTest_visualize.py`.')
    md.append('')
    md.append('## Simulator')
    md.append('')
    md.append('**A1 (W-fixed, shift_at_test_only)**:')
    md.append('- Ridge weights W_k trained on UNSHIFTED design C_orig for 7 non-k colors (canonical LOCO).')
    md.append('- Test-time prediction uses shifted design C(θ_k + δθ_k) at every (β_s, β_c) grid cell.')
    md.append('- W_k is independent of (β_s, β_c) — no leakage.')
    md.append('- Loss: canonical 4-term L_fit (`1·L_vuln + 0.5·L_rank + 0.2·L_rdm + 0.1·L_smooth`).')
    md.append('')
    md.append('## Per-subject wfixed argmin')
    md.append('')
    md.append('| Subject | Group | β_s | β_c | norm | ρ | L_fit |')
    md.append('|---|---|---|---|---|---|---|')
    for info in info_list:
        md.append(
            f"| sub-{info['sid']} | {info['cvd_type']} | {info['bs']:.0f} | "
            f"{info['bc']:+.0f} | {info['norm']:.1f}° | {info['rho']:.3f} | "
            f"{info['l_fit']:.4f} |"
        )
    md.append('')
    md.append('## Files')
    md.append('')
    md.append('Per subject (XX = sid, B = bs / bc with sign suffix):')
    md.append('- `landscape_sub-XX_V4_wfixed_bsB_bcB.png` — 2D landscape coloured by Spearman ρ; argmin marked.')
    md.append('- `4col_sub-XX_V4_wfixed_bsB_bcB.png` — per-hue colour rendering Original / CVD perceives / Filtered (pre-image) / CVD(Filtered).')
    md.append('- `vuln_hue_sub-XX_V4_wfixed_bsB_bcB.png` — per-color vuln line graph (observed vs simulated).')
    md.append('')
    md.append('Combined:')
    md.append('- `F4_twocomp_wfixed.png` — sub-08 + sub-09 F4_twocomp-style 3-panel figure (vuln traces + landscapes + bar chart).')
    md.append('')
    md.append('## Behavioral consistency caveat')
    md.append('')
    md.append('sub-09 wfixed argmin has weak ρ=0.214 (vs sub-08 ρ=0.762). The (46, +48) location is potentially plateau noise rather than a sharp identifiable optimum. Per raw_behav.md, sub-09 shows LESS behavioral colour distortion than sub-08, which is INCONSISTENT with sub-09 norm (66.5°) > sub-08 norm (48.4°). Follow-up loss variants and ROI-V1 wfixed runs are pending to assess whether a smaller-norm solution closer to Phase A LOCO (6, -22) reappears under alternative formulations.')
    md.append('')
    (OUTDIR / 'README.md').write_text('\n'.join(md))
    print(f'  wrote README.md')


if __name__ == '__main__':
    main()
