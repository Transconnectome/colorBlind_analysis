"""fixedW_onlyTest_best_visualize.py — visualize current BEST under V4-only LOCO policy.

CURRENT BEST: V4-CCC + λ·l_topk(V4) wretrained, λ ∈ [0.25, 2.0] gives identical argmin.
  sub-08 deutan: (β_s=44°, β_c=+28°), P2a=0.575 (4/8 exact)
  sub-09 protan: (β_s=30°, β_c=+46°), P2a=0.650 (3/8 exact, same as V4-CCC alone)

Generates at results/fixedW_onlyTest/:
  - BEST_4col_sub-{08,09}_V4_V4CCCltopk_bsB_bcB.png(/pdf)
  - BEST_vuln_hue_sub-{08,09}_V4_V4CCCltopk_bsB_bcB.png(/pdf)
  - BEST_landscape_sub-{08,09}_V4_V4CCCltopk_bsB_bcB.png(/pdf)
  - BEST_F4_V4_V4CCCltopk.png(/pdf)
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
from old_formula_refit import load_cvd_loco_target

_PHASE2 = _THIS_DIR.parent
OUT = _PHASE2 / 'results'  # BEST files go to results root
SRC = _PHASE2 / 'results' / 'old_formula'
OUT.mkdir(parents=True, exist_ok=True)

# Y-axis label for vuln plots.
# Rationale: project shorthand "LOCO vulnerability" denoted signed voxel_corr
# (negative = CVD-different = vulnerable). This label clarifies the directional
# interpretation: ↑ preserved (HC-like), ↓ vulnerable (CVD-distorted).
VULN_YLABEL = "LOCO voxel_corr  (↑ preserved / HC-like  |  ↓ vulnerable / CVD-distorted)"

# V4-CCC alone argmin (for the comparison curve in F4 Panel A).
# Source: results/old_formula/sub-{sid}_V4_V4ccc_summary.json — best_by_l_fit cell.
# sub-08: (16, +40) — distinct from BEST V4-CCC+l_topk argmin (44, +28)
# sub-09: (30, +46) — same as BEST (l_topk has no effect on sub-09 V4)
V4CCC_ALONE_ARGMIN = {
    '08': (16.0, 40.0),
    '09': (30.0, 46.0),
}

THETA_CONF_DEG = 150.0
HUE_ANGLES = [0, 45, 90, 135, 180, 225, 270, 315]
COLOR_LABELS = ['c1 (red)', 'c2 (orange)', 'c3 (yellow)', 'c4 (green)',
                'c5 (cyan)', 'c6 (sky)', 'c7 (blue)', 'c8 (magenta)']
K_TOPK = 3
TIKH_NORM = 32400.0
LAMBDA_REPR = 0.5  # representative λ (λ≥0.25 all give same argmin)

# (sid, cvd_type, color, target_map, best_bs, best_bc)
SUBJECTS = [
    ('08', 'deutan', '#E07B2C', SUB08_ORIGINAL_HC_EQUIV, 44.0, 28.0),
    ('09', 'protan', '#2D8E8B', SUB09_ORIGINAL_HC_EQUIV, 30.0, 46.0),
]

matplotlib.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Helvetica', 'Arial', 'DejaVu Sans'],
    'font.size': 7, 'axes.titlesize': 7.5, 'axes.labelsize': 7,
    'xtick.labelsize': 7, 'ytick.labelsize': 7, 'legend.fontsize': 7,
    'axes.linewidth': 0.6, 'xtick.major.width': 0.6, 'ytick.major.width': 0.6,
    'xtick.major.size': 2.5, 'ytick.major.size': 2.5, 'lines.linewidth': 1.0,
    'pdf.fonttype': 42, 'ps.fonttype': 42,
})


# ---------- forward + pre-image ----------
def dt_old(theta_deg, bs, bc):
    th = np.deg2rad(theta_deg)
    return (bs * np.cos(th - np.deg2rad(90.0))
            + bc * np.cos(th - np.deg2rad(THETA_CONF_DEG)))


def forward_old(theta, bs, bc):
    dt = dt_old(theta, bs, bc)
    return (theta + dt) % 360.0, dt


def pre_image_old(target_deg, bs, bc, n_grid=3600):
    grid = np.linspace(0.0, 360.0, n_grid, endpoint=False)
    forwards = np.array([forward_old(t, bs, bc)[0] for t in grid])
    diff = (forwards - target_deg + 180.0) % 360.0 - 180.0
    i = int(np.argmin(np.abs(diff)))
    return float(grid[i]), float(diff[i])


# ---------- loss components ----------
def l_topk(vuln_sim, vuln_obs, K=K_TOPK):
    sim = np.asarray(vuln_sim); obs = np.asarray(vuln_obs)
    top_sim = set(np.argsort(sim)[:K].tolist())
    top_obs = set(np.argsort(obs)[:K].tolist())
    inter = len(top_sim & top_obs)
    union = len(top_sim | top_obs)
    return 1.0 - (inter / union)


def compute_combined_loss(cells, vuln_cvd, lam=LAMBDA_REPR):
    for c in cells:
        sim = np.asarray(c['vuln_sim'])
        c['_l_topk'] = l_topk(sim, vuln_cvd)
        c['_tikh'] = (c['bs']**2 + c['bc']**2) / TIKH_NORM
        c['_L_combined'] = 1.0 * c['l_ccc'] + lam * c['_l_topk'] + 0.1 * c['_tikh']
    return cells


def grid_to_arr(cells, key):
    bs_all = sorted(set(c['bs'] for c in cells))
    bc_all = sorted(set(c['bc'] for c in cells))
    arr = np.full((len(bc_all), len(bs_all)), np.nan)
    bs_idx = {v: i for i, v in enumerate(bs_all)}
    bc_idx = {v: i for i, v in enumerate(bc_all)}
    for c in cells:
        arr[bc_idx[c['bc']], bs_idx[c['bs']]] = c[key]
    return np.array(bs_all), np.array(bc_all), arr


def load_landscape(sid):
    fn = SRC / f'sub-{sid}_V4_V4ccc_landscape.json'
    ls = json.load(open(fn))
    cells = ls if isinstance(ls, list) else ls.get('cells', ls)
    return cells


# ---------- renderers ----------
def render_4col(sid, cvd_type, color, bs, bc, target_map, P2a, exact, out_path):
    n_rows = len(HUE_ANGLES)
    fig, axes = plt.subplots(n_rows, 4,
                             figsize=(5.5, 0.65 * n_rows + 0.8),
                             gridspec_kw={'hspace': 0.10, 'wspace': 0.05})
    fig.suptitle(
        f"sub-{sid} ({cvd_type}) V4 — V4-CCC+l_topk BEST  β_s={bs:.0f}°, β_c={bc:+.0f}°  "
        f"(norm={np.hypot(bs,bc):.1f}°)  P2a={P2a:.3f}  exact={exact}/8",
        fontsize=10, y=1.00, color=color, fontweight='bold')

    for j, ct in enumerate(['Original', 'CVD perceives',
                            'Filtered (pre-image)', 'CVD(Filtered)']):
        axes[0, j].set_title(ct, fontsize=8)

    for i, theta in enumerate(HUE_ANGLES):
        theta_cvd, dt = forward_old(float(theta), bs, bc)
        theta_pre, _ = pre_image_old(float(theta), bs, bc)
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

        pred = hc_name(theta_cvd)
        target = target_map[theta]
        score = hc_match_score(pred, target)
        mark = '✓' if pred == target else ('~' if score > 0 else '✗')
        color_p2a = 'green' if score == 1.0 else ('darkorange' if score > 0 else 'red')
        axes[i, 1].text(0.5, -0.02, f'δθ={dt:+.0f}° {mark}',
                        ha='center', va='top', fontsize=7,
                        transform=axes[i, 1].transAxes, color=color_p2a)
        axes[i, 2].text(0.5, -0.02, f'θ_pre={theta_pre:.0f}°',
                        ha='center', va='top', fontsize=7,
                        transform=axes[i, 2].transAxes)

    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.savefig(str(out_path).replace('.png', '.pdf'), bbox_inches='tight')
    plt.close(fig)
    print(f'  wrote {out_path.name} (+ pdf)')


def render_vuln_hue(sid, cvd_type, color, vuln_cvd, vuln_sim, bs, bc, rho, ccc,
                    P2a, l_topk_val, out_path):
    fig, ax = plt.subplots(figsize=(6.5, 3.6), dpi=150)
    x = np.arange(8)
    labels_short = ['R', 'O', 'Y', 'G', 'C', 'B', 'P', 'M']

    ax.axhline(0, color='#aaaaaa', lw=0.5, ls=':')
    ax.plot(x, vuln_cvd, 'o-', color='#222222', ms=6, lw=0.8,
            label='Observed (CVD LOCO)')
    ax.plot(x, vuln_sim, 's-', color=color, ms=6, lw=1.5,
            label=f'BEST sim @ argmin (ρ={rho:.2f}, CCC={ccc:.2f}, l_topk={l_topk_val:.2f})')
    # mark top-3 vulnerable colors
    top3_obs = np.argsort(vuln_cvd)[:3]
    for idx in top3_obs:
        ax.axvspan(idx-0.4, idx+0.4, alpha=0.10, color=color, zorder=0)
    ax.set_xticks(x); ax.set_xticklabels(labels_short)
    ax.set_xlabel('Hue (DKL bin) — shaded: top-3 vulnerable (most negative voxel_corr in observed)')
    ax.set_ylabel(VULN_YLABEL)
    ax.set_title(
        f"sub-{sid} ({cvd_type}) V4 — V4-CCC+l_topk BEST  β_s={bs:.0f}°, β_c={bc:+.0f}°  "
        f"P2a={P2a:.3f}",
        fontweight='bold', color=color)
    ax.set_ylim(-1.0, 1.0)
    ax.legend(loc='best', fontsize=8)
    ax.spines[['top', 'right']].set_visible(False)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.savefig(str(out_path).replace('.png', '.pdf'), bbox_inches='tight')
    plt.close(fig)
    print(f'  wrote {out_path.name} (+ pdf)')


def render_landscape(sid, cvd_type, color, cells, best, key, key_label,
                     vmin=None, vmax=None, out_path=None):
    """Loss landscape — dynamic vmin/vmax from data percentiles.
    For loss values (low=good), use percentile-based [5, 95] to avoid all-clip.
    cmap='RdBu_r' → low=blue (cold, argmin), high=red (warm, bad).
    """
    bs, bc, arr = grid_to_arr(cells, key)
    arr_finite = arr[np.isfinite(arr)]
    # Dynamic normalization: percentile-based (robust to outliers)
    if vmin is None:
        vmin = float(np.percentile(arr_finite, 1))
    if vmax is None:
        vmax = float(np.percentile(arr_finite, 95))
    fig, ax = plt.subplots(figsize=(5.8, 4.8), dpi=150)
    im = ax.pcolormesh(bs, bc, arr, cmap='RdBu_r', vmin=vmin, vmax=vmax,
                       shading='nearest', rasterized=True)
    ax.plot(best['bs'], best['bc'], '*', color='white', ms=14,
            markeredgecolor='black', markeredgewidth=0.8, zorder=10)
    val = best.get(key, 0)
    # Smart positioning: if star is in right half, put text LEFT of star
    bs_mid = np.median(bs)
    bc_mid = np.median(bc)
    if best['bs'] >= bs_mid:
        lbl_x, lbl_ha = best['bs'] - 2, 'right'
    else:
        lbl_x, lbl_ha = best['bs'] + 2, 'left'
    if best['bc'] >= bc_mid:
        lbl_y, lbl_va = best['bc'] - 3, 'top'
    else:
        lbl_y, lbl_va = best['bc'] + 3, 'bottom'
    ax.text(lbl_x, lbl_y,
            f"β_s={best['bs']:.0f}°, β_c={best['bc']:+.0f}°\n"
            f"{key_label}={val:.3f}\n"
            f"(range [{arr_finite.min():.2f}, {arr_finite.max():.2f}])",
            fontsize=7, color='white', ha=lbl_ha, va=lbl_va, zorder=11,
            bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.65, lw=0))
    ax.set_xlabel('β_s — S-cone shift (°)')
    ax.set_ylabel('β_c — confusion rotation (°)')
    ax.set_title(
        f"sub-{sid} ({cvd_type}) V4 — BEST landscape colored by {key_label}\n"
        f"argmin = blue (cold), high loss = red",
        fontweight='bold', color=color, fontsize=10)
    cb = fig.colorbar(im, ax=ax, extend='both')
    cb.set_label(f'{key_label} (vmin={vmin:.2f}, vmax={vmax:.2f})')
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.savefig(str(out_path).replace('.png', '.pdf'), bbox_inches='tight')
    plt.close(fig)
    print(f'  wrote {out_path.name} (+ pdf)  vmin={vmin:.3f} vmax={vmax:.3f}')


def render_f4_combined(per_subj, out_path):
    """F4-style: A=vuln plots, B=bar chart, C=landscapes."""
    s08 = per_subj['08']
    s09 = per_subj['09']

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

    HUE_LABELS = ['R', 'O', 'Y', 'G', 'C', 'B', 'P', 'M']
    HUE_X = np.arange(8)
    COL_OBS = '#222222'

    def plot_vuln(ax, vobs, vsim, vsim_alone, color, subj, cvdtype, best, best_alone,
                  P2a, P2a_alone, identical=False):
        # Top-3 vulnerable (observed) shading (no axis-label explanation; kept implicit)
        top3 = np.argsort(np.asarray(vobs))[:3]
        for idx in top3:
            ax.axvspan(idx - 0.4, idx + 0.4, alpha=0.12, color=color, zorder=0)
        ax.axhline(0, color='#aaaaaa', lw=0.5, ls=':')
        # Two vsim curves overlay (V4-CCC alone vs V4-CCC + l_topk)
        ax.plot(HUE_X, vobs, 'o-', color=COL_OBS, ms=3.5, lw=0.6, label='Observed')
        if identical:
            ax.plot(HUE_X, vsim, '-', color=color, lw=1.8,
                    label=(f"BEST=alone β=({best['bs']:.0f},{best['bc']:+.0f}) "
                           f"P2a={P2a:.3f}"))
        else:
            ax.plot(HUE_X, vsim_alone, '--', color=color, lw=1.2, alpha=0.7,
                    label=(f"alone β=({best_alone['bs']:.0f},{best_alone['bc']:+.0f}) "
                           f"P2a={P2a_alone:.3f}"))
            ax.plot(HUE_X, vsim, '-', color=color, lw=1.8,
                    label=(f"BEST β=({best['bs']:.0f},{best['bc']:+.0f}) "
                           f"P2a={P2a:.3f}"))
        ax.set_xticks(HUE_X); ax.set_xticklabels(HUE_LABELS)
        ax.set_xlabel('Hue (DKL)')
        ax.set_ylabel('LOCO voxel_corr')
        ax.set_ylim(-1.0, 1.0)
        ax.set_title(f"{subj}  ({cvdtype})", fontweight='bold', pad=3)
        # Upper-right legend, ~3/4 of previous size (fontsize 6 → 4.5,
        # handle/text/border ~3/4)
        ax.legend(loc='upper right', handlelength=1.35, handletextpad=0.22,
                  borderpad=0.30, labelspacing=0.30, fontsize=4.5,
                  frameon=True, framealpha=0.85)
        ax.spines[['top', 'right']].set_visible(False)

    plot_vuln(ax_a08, s08['vuln_cvd'], s08['vuln_sim'], s08['vuln_sim_alone'],
              s08['color'], 'Sub-08', 'deutan',
              s08['best'], s08['best_alone'], s08['P2a'], s08['P2a_alone'],
              identical=s08.get('alone_identical', False))
    plot_vuln(ax_a09, s09['vuln_cvd'], s09['vuln_sim'], s09['vuln_sim_alone'],
              s09['color'], 'Sub-09', 'protan',
              s09['best'], s09['best_alone'], s09['P2a'], s09['P2a_alone'],
              identical=s09.get('alone_identical', False))

    # Panel B: P2a + ρ bars
    x_subj = np.array([1.0, 2.0]); w = 0.55
    ax_b.bar(x_subj[0], s08['P2a'], w, color=s08['color'], alpha=0.9, label='P2a')
    ax_b.bar(x_subj[1], s09['P2a'], w, color=s09['color'], alpha=0.9)
    ax_b.set_xlim(0.0, 3.0); ax_b.set_xticks(x_subj)
    ax_b.set_xticklabels(['Sub-08\n(deutan)', 'Sub-09\n(protan)'])
    ax_b.set_ylabel('P2a (raw_behav match)')
    ax_b.set_ylim(0, 1.0)
    ax_b.set_title('V4-CCC+l_topk BEST (V4 LOCO only policy)',
                   fontweight='bold', pad=3)
    ax_b.axhline(0.5, color='gray', lw=0.4, ls='--')
    ax_b.spines[['top', 'right']].set_visible(False)
    # annotate
    ax_b.text(x_subj[0], s08['P2a'] + 0.02, f"{s08['P2a']:.3f}",
              ha='center', va='bottom', fontsize=8, color=s08['color'], fontweight='bold')
    ax_b.text(x_subj[1], s09['P2a'] + 0.02, f"{s09['P2a']:.3f}",
              ha='center', va='bottom', fontsize=8, color=s09['color'], fontweight='bold')

    # Panel C: landscapes colored by L_combined (min optimum, blue=argmin)
    # Combined vmin/vmax from BOTH subjects so colorscale is shared
    all_L = np.concatenate([
        np.array([c['_L_combined'] for c in s08['cells']]),
        np.array([c['_L_combined'] for c in s09['cells']]),
    ])
    VMIN = float(np.percentile(all_L, 1))
    VMAX = float(np.percentile(all_L, 95))

    def plot_ls(ax, cells, best, color, subj, cvdtype):
        bs, bc, arr = grid_to_arr(cells, '_L_combined')
        im = ax.pcolormesh(bs, bc, arr, cmap='RdBu_r', vmin=VMIN, vmax=VMAX,
                           shading='nearest', rasterized=True)
        ax.plot(best['bs'], best['bc'], '*', color='white', ms=9, zorder=10,
                markeredgecolor='black', markeredgewidth=0.5)
        # Smart annotation positioning
        bs_arr = np.array(bs); bc_arr = np.array(bc)
        if best['bs'] >= np.median(bs_arr):
            lbl_x, lbl_ha = best['bs'] - 1.5, 'right'
        else:
            lbl_x, lbl_ha = best['bs'] + 1.5, 'left'
        if best['bc'] >= np.median(bc_arr):
            lbl_y, lbl_va = best['bc'] - 2.0, 'top'
        else:
            lbl_y, lbl_va = best['bc'] + 2.0, 'bottom'
        ax.text(lbl_x, lbl_y,
                f"β_s={best['bs']:.0f}°, β_c={best['bc']:+.0f}°\n"
                f"L={best['_L_combined']:.3f}\n"
                f"ρ={best['spearman_r']:.2f}, l_topk={best['_l_topk']:.2f}",
                fontsize=7, color='white', va=lbl_va, ha=lbl_ha, zorder=11,
                bbox=dict(boxstyle='round,pad=0.2', facecolor='black', alpha=0.55, lw=0))
        ax.set_xlabel('β_s — S-cone shift (°)')
        ax.set_ylabel('β_c — confusion rot. (°)')
        ax.set_title(f"{subj}  ({cvdtype})  (BLUE=argmin)", fontweight='bold', pad=3)
        ax.spines[['top', 'right']].set_visible(False)
        return im

    plot_ls(ax_c08, s08['cells'], s08['best'], s08['color'], 'Sub-08', 'deutan')
    im09 = plot_ls(ax_c09, s09['cells'], s09['best'], s09['color'], 'Sub-09', 'protan')
    cb = fig.colorbar(im09, cax=ax_cb, extend='both')
    cb.set_label(f'L_combined (CCC+λl_topk+Tikh)\nmin = optimum',
                 fontsize=7, labelpad=4)
    cb.ax.tick_params(labelsize=7)

    letter_kw = dict(fontsize=10, fontweight='bold', va='top', ha='left',
                     transform=fig.transFigure)
    fig.text(L_A - 0.025, B_B + H_B + 0.025, 'B', **letter_kw)
    fig.text(L_A - 0.025, B_R1 + H_AB_ROW + 0.025, 'A', **letter_kw)
    fig.text(L_C - 0.02, B_R1 + H_AB_ROW + 0.025, 'C', **letter_kw)

    fig.savefig(out_path, dpi=300, bbox_inches='tight', facecolor='white')
    fig.savefig(str(out_path).replace('.png', '.pdf'), bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'  wrote {out_path.name} (+ pdf)')


def p2a_compute(bs, bc, target_map):
    total = 0.0
    exact = 0
    for theta in HUE_ANGLES:
        theta_cvd, _ = forward_old(float(theta), bs, bc)
        pred = hc_name(theta_cvd)
        target = target_map[theta]
        s = hc_match_score(pred, target)
        total += s
        if pred == target:
            exact += 1
    return total / 8.0, exact


def main():
    print(f'OUTDIR: {OUT}')
    per_subj = {}

    for sid, cvd_type, color, target_map, best_bs, best_bc in SUBJECTS:
        print(f'\n=== sub-{sid} {cvd_type} BEST = ({best_bs:.0f}, {best_bc:+.0f}) ===')
        cells = load_landscape(sid)
        vuln_cvd = np.array(load_cvd_loco_target(sid, 'V4'))
        cells = compute_combined_loss(cells, vuln_cvd, lam=LAMBDA_REPR)

        # Find best cell matching target
        best = None
        for c in cells:
            if abs(c['bs'] - best_bs) < 0.5 and abs(c['bc'] - best_bc) < 0.5:
                best = c
                break
        if best is None:
            raise RuntimeError(f'best cell not found at ({best_bs}, {best_bc})')

        vuln_sim = np.array(best['vuln_sim'])
        P2a, exact = p2a_compute(best_bs, best_bc, target_map)
        tag = f"bs{int(best_bs)}_bc{int(best_bc):+d}"

        # Find V4-CCC alone argmin cell (for F4 Panel A two-curve overlay)
        alone_bs, alone_bc = V4CCC_ALONE_ARGMIN[sid]
        alone_identical = (abs(alone_bs - best_bs) < 0.5 and
                           abs(alone_bc - best_bc) < 0.5)
        best_alone = None
        for c in cells:
            if abs(c['bs'] - alone_bs) < 0.5 and abs(c['bc'] - alone_bc) < 0.5:
                best_alone = c
                break
        if best_alone is None:
            raise RuntimeError(
                f'V4-CCC alone cell not found at ({alone_bs}, {alone_bc}) for sub-{sid}')
        vuln_sim_alone = np.array(best_alone['vuln_sim'])
        P2a_alone, exact_alone = p2a_compute(alone_bs, alone_bc, target_map)
        print(f'  V4-CCC alone argmin = ({alone_bs:.0f}, {alone_bc:+.0f}), '
              f'P2a_alone={P2a_alone:.3f}, identical_to_BEST={alone_identical}')

        # 1. 4-col
        render_4col(sid, cvd_type, color, best_bs, best_bc, target_map, P2a, exact,
                    OUT / f"BEST_4col_sub-{sid}_V4_V4CCCltopk_{tag}.png")

        # 2. vuln_hue
        render_vuln_hue(sid, cvd_type, color, vuln_cvd, vuln_sim,
                        best_bs, best_bc, best['spearman_r'], best['ccc'],
                        P2a, best['_l_topk'],
                        OUT / f"BEST_vuln_hue_sub-{sid}_V4_V4CCCltopk_{tag}.png")

        # 3. Landscape colored by combined L (dynamic percentile-based vmin/vmax)
        render_landscape(sid, cvd_type, color, cells, best, '_L_combined',
                         'L_combined (CCC+λ·l_topk+Tikh)',
                         vmin=None, vmax=None,
                         out_path=OUT / f"BEST_landscape_sub-{sid}_V4_V4CCCltopk_{tag}.png")

        per_subj[sid] = {
            'cells': cells, 'best': best,
            'vuln_cvd': vuln_cvd, 'vuln_sim': vuln_sim,
            'color': color, 'cvd_type': cvd_type,
            'P2a': P2a, 'exact': exact,
            # V4-CCC alone (no l_topk) reference for F4 Panel A overlay
            'best_alone': best_alone,
            'vuln_sim_alone': vuln_sim_alone,
            'P2a_alone': P2a_alone,
            'exact_alone': exact_alone,
            'alone_identical': alone_identical,
        }

    # 4. F4 combined
    print('\n=== F4 combined ===')
    render_f4_combined(per_subj, OUT / 'BEST_F4_V4_V4CCCltopk.png')

    # Save summary JSON
    summary = {
        'best_loss': 'V4-CCC + λ·l_topk(V4) wretrained',
        'lambda_representative': LAMBDA_REPR,
        'lambda_range_giving_same_argmin': '[0.25, 2.0]',
        'simulator': 'wretrained',
        'policy': 'V4 LOCO only',
        'subjects': {
            f"sub-{sid}": {
                'cvd_type': per_subj[sid]['cvd_type'],
                'bs': per_subj[sid]['best']['bs'],
                'bc': per_subj[sid]['best']['bc'],
                'norm': float(np.hypot(per_subj[sid]['best']['bs'],
                                       per_subj[sid]['best']['bc'])),
                'p2a': per_subj[sid]['P2a'],
                'exact': per_subj[sid]['exact'],
                'spearman_r': per_subj[sid]['best']['spearman_r'],
                'ccc': per_subj[sid]['best']['ccc'],
                'l_topk': per_subj[sid]['best']['_l_topk'],
                'l_ccc': per_subj[sid]['best']['l_ccc'],
                'L_combined': per_subj[sid]['best']['_L_combined'],
                'vuln_sim': per_subj[sid]['vuln_sim'].tolist(),
                'vuln_cvd': per_subj[sid]['vuln_cvd'].tolist(),
            } for sid in ['08', '09']
        }
    }
    json_path = OUT / 'BEST_summary.json'
    with open(json_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f'  wrote {json_path.name}')


if __name__ == '__main__':
    main()
