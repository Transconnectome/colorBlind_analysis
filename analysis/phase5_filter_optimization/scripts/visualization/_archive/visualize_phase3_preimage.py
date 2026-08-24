#!/usr/bin/env python3
"""visualize_phase3_preimage.py
================================

4 figures (2 subjects × 2 ROI configs) showing 4-column progression for
Phase 3 candidate cells using cycle8_preimage parameters:

  Col 1: Original color (hue θ on the L*=75, C*=40 experimental ring)
  Col 2: CVD-perceived  (forward pass under 2-comp at θ)
  Col 3: Filtered       (pre-image θ_pre of θ under 2-comp)
  Col 4: CVD(Filtered)  (forward pass at θ_pre — acid test)

Subjects × ROI configs:
  sub-08 V4-only       β_s=38, β_c=7   (deutan, primary recommended)
  sub-08 V1+V4 avg     β_s=19, β_c=3.5 (deutan, V1 degenerate pulls toward null)
  sub-09 V4-only       β_s=0,  β_c=2   (protan, near-trivial filter)
  sub-09 V1+V4 avg     β_s=30.5, β_c=12 (protan, primary documented in PLAN04 §6)

Display tier identical to visualize_filter_candidates.py:
  Tier 1: fMRI 8-stim ring  Tier 2: CVD confusion anchors  Tier 3: sRGB primaries
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from scipy.optimize import brentq

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR.parent))

_PHASE2_DIR = _SCRIPT_DIR.parent
for _base in [_PHASE2_DIR.parent, _PHASE2_DIR.parent.parent]:
    _fwd = _base / 'phase4_forward_model' / 'scripts'
    if _fwd.exists() and str(_fwd) not in sys.path:
        sys.path.insert(0, str(_fwd))
        break

from machado_simulator import (
    machado_shifted_hue_at, machado_mixed_fundamentals, _load_stockman_grid,
)
from stockman_cone_shift import (
    _compute_spectral_shift_lms, lab_to_xyz, D65_XYZ,
)

# STIM_LAB-based rendering (screenshot-derived; matches actual MRI projector)
sys.path.insert(0, str(_SCRIPT_DIR.parent))
from stim_lab_render import render_at_hue as _render_stim_lab

# ------------------------------------------------------------------- Constants
CONF_AXIS = {'protan': 16.0, 'deutan': 150.0}
L_STAR = 75.0
CHROMA = 40.0
DISPLAY_L_RANGE = (20.0, 97.0)
DISPLAY_L_STEPS = 40
DISPLAY_CHROMA_MAX = 150.0

OUTDIR = _PHASE2_DIR / 'results' / 'visualizations' / 'filter_visualization_phase3'
OUTDIR.mkdir(parents=True, exist_ok=True)

# Phase 3 candidate cells (cycle8_preimage parameters)
CELLS = [
    {'subj': '08', 'cvd': 'deutan', 'roi_label': 'V4-only',
     'beta_s': 38.0, 'beta_c': 7.0, 'dlam_anchor': 1.5,
     'note': 'PRIMARY recommendation (z_combined CI disjoint from HC)'},
    {'subj': '08', 'cvd': 'deutan', 'roi_label': 'V1+V4 avg',
     'beta_s': 19.0, 'beta_c': 3.5, 'dlam_anchor': 1.5,
     'note': 'V1 fit degenerate (β=0,0) pulls average toward null'},
    {'subj': '09', 'cvd': 'protan', 'roi_label': 'V4-only',
     'beta_s': 0.0, 'beta_c': 2.0, 'dlam_anchor': 13.5,
     'note': 'Near-trivial filter (β_s=0); no compensation'},
    {'subj': '09', 'cvd': 'protan', 'roi_label': 'V1+V4 avg',
     'beta_s': 30.5, 'beta_c': 12.0, 'dlam_anchor': 13.5,
     'note': 'Documented in PLAN04 §6; HC distribution overlap exists'},
]


# ------------------------------------------------------------------- CIELab → sRGB
def _lab_to_srgb_unclipped(L, a, b):
    y = (L + 16.0) / 116.0
    x = a / 500.0 + y
    z = y - b / 200.0
    xyz = np.array([x, y, z], dtype=float)
    xyz = np.where(xyz > 0.206893, xyz ** 3, (xyz - 16.0/116.0)/7.787)
    xyz = xyz * np.array([0.95047, 1.0, 1.08883])
    M = np.array([[3.2406, -1.5372, -0.4986],
                  [-0.9689, 1.8758,  0.0415],
                  [0.0557,  -0.2040,  1.0570]])
    rgb = M @ xyz
    sign = np.sign(rgb)
    mag = np.abs(rgb)
    rgb = np.where(mag <= 0.0031308, 12.92 * rgb,
                   sign * (1.055 * mag ** (1/2.4) - 0.055))
    return rgb


def lab_to_srgb(L, a, b):
    return np.clip(_lab_to_srgb_unclipped(L, a, b), 0.0, 1.0)


def _max_chroma_at_L(L, cos_t, sin_t, c_max, tol):
    def in_gamut(C):
        rgb = _lab_to_srgb_unclipped(L, C * cos_t, C * sin_t)
        return bool(np.all(rgb >= -tol) and np.all(rgb <= 1.0 + tol))
    if in_gamut(c_max):
        return c_max
    lo, hi = 0.0, c_max
    for _ in range(20):
        mid = 0.5 * (lo + hi)
        if in_gamut(mid):
            lo = mid
        else:
            hi = mid
    return lo


def angle_to_rgb_vivid(theta_deg, L_range=DISPLAY_L_RANGE, n_L=DISPLAY_L_STEPS,
                       c_max=DISPLAY_CHROMA_MAX, tol=1e-3):
    rad = np.deg2rad(theta_deg)
    cos_t, sin_t = np.cos(rad), np.sin(rad)
    best_rgb = np.array([0.5, 0.5, 0.5])
    best_score = -1.0
    for L in np.linspace(L_range[0], L_range[1], n_L):
        C = _max_chroma_at_L(L, cos_t, sin_t, c_max, tol)
        rgb = np.clip(_lab_to_srgb_unclipped(L, C * cos_t, C * sin_t), 0.0, 1.0)
        sat = float(rgb.max() - rgb.min())
        if sat > best_score:
            best_score = sat
            best_rgb = rgb
    return best_rgb


def _xyz_to_lab(xyz, white=D65_XYZ):
    def f(t):
        delta = 6.0/29.0
        return np.where(t > delta**3, np.cbrt(t), t/(3*delta**2) + 4.0/29.0)
    xyz = np.asarray(xyz, dtype=float)
    xyz_n = xyz / white
    fx, fy, fz = f(xyz_n[..., 0]), f(xyz_n[..., 1]), f(xyz_n[..., 2])
    L = 116.0 * fy - 16.0
    a = 500.0 * (fx - fy)
    b = 200.0 * (fy - fz)
    return np.stack([L, a, b], axis=-1)


def cvd_response_lab(theta_deg, cvd, delta_lambda, L_star=L_STAR, chroma=CHROMA):
    if cvd == 'normal' or abs(delta_lambda) < 1e-9:
        rad = np.deg2rad(theta_deg)
        return np.array([L_star, chroma * np.cos(rad), chroma * np.sin(rad)])
    wl, L, M, S, _, _, M_xyz2lms_orig = _load_stockman_grid()
    rad = np.deg2rad(float(theta_deg))
    lab = np.array([[L_star, chroma * np.cos(rad), chroma * np.sin(rad)]])
    xyz_orig = lab_to_xyz(lab)
    L_a, M_a, S_a = machado_mixed_fundamentals(float(delta_lambda), cvd, wl, L, M, S)
    lms_cvd = _compute_spectral_shift_lms(wl, L_a, M_a, S_a, M_xyz2lms_orig, xyz_orig)
    xyz_equiv = np.linalg.solve(M_xyz2lms_orig, lms_cvd[0])
    return _xyz_to_lab(xyz_equiv)


def lab_to_rgb_display(L, a, b):
    return lab_to_srgb(float(L), float(a), float(b))


def _scalar(x):
    return float(np.atleast_1d(x)[0])


def dt_2comp(theta, cvd, beta_s, beta_c):
    """δθ for 2-component model.

    DEPRECATED 2026-05-10 (P2): Original implementation used CIELab nominal θ
    directly in the trig (frame mismatch with Stockman θ_conf). This produced
    different visualizations than the canonical h_base-based formula in
    visualize_filter_candidates.py at the same (β_s, β_c), causing the
    F3 vs F4 paradox documented in behav_sub08_6way_implications.md §7.

    Now delegates to forward_models.dt_2comp (single source of truth, matches
    fitting code in loco_distortion_fit.py and comprehensive_2component_analysis.py).
    """
    from forward_models import dt_2comp as _canonical_dt_2comp
    return _canonical_dt_2comp(theta, cvd, beta_s, beta_c, L_star=L_STAR, chroma=CHROMA)


def forward_perceived(theta, cvd, beta_s, beta_c):
    dt = dt_2comp(theta, cvd, beta_s, beta_c)
    return (theta + dt) % 360.0, dt


def _wrap180(x):
    return (x + 180.0) % 360.0 - 180.0


def find_preimage(theta_target, cvd, beta_s, beta_c, n_grid=1440):
    grid = np.linspace(0.0, 360.0, n_grid, endpoint=False)
    def residual(t):
        pred, _ = forward_perceived(float(t) % 360.0, cvd, beta_s, beta_c)
        return _wrap180(pred - theta_target)
    res_grid = np.array([residual(t) for t in grid])
    i_min = int(np.argmin(np.abs(res_grid)))
    theta_pre = float(grid[i_min])
    step = 360.0 / n_grid * 3
    lo = grid[i_min] - step
    hi = grid[i_min] + step
    try:
        f_lo, f_hi = residual(lo), residual(hi)
        if f_lo * f_hi < 0:
            theta_pre = brentq(lambda t: residual(t), lo, hi) % 360.0
    except Exception:
        pass
    return theta_pre % 360.0, residual(theta_pre)


# ------------------------------------------------------------------- Color tiers
TIER1 = [(0,'c1 (magenta-red)'),(45,'c2 (orange)'),(90,'c3 (yellow)'),
         (135,'c4 (yellow-green)'),(180,'c5 (teal/green)'),(225,'c6 (cyan-blue)'),
         (270,'c7 (blue)'),(315,'c8 (purple)')]
TIER2 = [(16,'confP+ (protan +)'),(196,'confP− (protan −)'),
         (150,'confD+ (deutan +)'),(330,'confD− (deutan −)'),
         (60,'Ishihara orange'),(240,'cobalt (control)')]
TIER3 = [(40,'sRGB R'),(90,'sRGB Y'),(140,'sRGB G'),
         (200,'sRGB C'),(270,'sRGB B'),(330,'sRGB M')]
PALETTE = [('Tier 1: fMRI 8-stim ring', TIER1),
           ('Tier 2: CVD confusion anchors', TIER2),
           ('Tier 3: sRGB primaries at L*=75', TIER3)]


def render_figure(cell, outpath):
    cvd = cell['cvd']
    beta_s, beta_c = cell['beta_s'], cell['beta_c']
    # NOTE: dlam_cvd (Machado anchor) NOT used — 2-comp ΔL*=0 by definition.
    # STIM_LAB rendering applied to all 4 columns (matches actual MRI display).
    rows = [(tier, theta, label) for tier, colors in PALETTE for theta, label in colors]
    n_rows = len(rows)
    fig_height = 0.55 * n_rows + 2.0
    fig, axes = plt.subplots(n_rows, 4, figsize=(9.0, fig_height),
                             gridspec_kw={'hspace': 0.08, 'wspace': 0.08})
    fig.suptitle(
        f'2-Component (stimulus-space dilation)  —  sub-{cell["subj"]} ({cvd}), {cell["roi_label"]}\n'
        f'β_s = {beta_s}°, β_c = {beta_c}°    [{cell["note"]}]\n'
        f'Render: STIM_LAB (utils_color_decoding) — screenshot-derived MRI display',
        fontsize=10, y=0.995)
    col_titles = ['Original', 'CVD perceives', 'Filtered (pre-image)', 'CVD(Filtered)']
    for ax, title in zip(axes[0], col_titles):
        ax.set_title(title, fontsize=9)
    last_tier = None
    for i, (tier, theta, label) in enumerate(rows):
        ax_row = axes[i]
        # Pre-image and perceived hues
        theta_pre, resid = find_preimage(theta, cvd, beta_s, beta_c)
        theta_cvd, dt = forward_perceived(theta, cvd, beta_s, beta_c)
        theta_cvd_of_pre, _ = forward_perceived(theta_pre, cvd, beta_s, beta_c)

        # All 4 columns: STIM_LAB-interpolated (L*, chroma) at the relevant hue.
        # 2-comp model: ΔL* = 0 (no cone-shift in stimulus-space dilation).
        rgb_orig          = _render_stim_lab(theta,            dL=0.0)
        rgb_cvd           = _render_stim_lab(theta_cvd,        dL=0.0)
        rgb_pre           = _render_stim_lab(theta_pre,        dL=0.0)
        rgb_cvd_of_pre    = _render_stim_lab(theta_cvd_of_pre, dL=0.0)

        ax_row[0].add_patch(Rectangle((0,0),1,1,color=rgb_orig))
        ax_row[1].add_patch(Rectangle((0,0),1,1,color=rgb_cvd))
        ax_row[2].add_patch(Rectangle((0,0),1,1,color=rgb_pre))
        ax_row[3].add_patch(Rectangle((0,0),1,1,color=rgb_cvd_of_pre))
        ax_row[0].text(-0.05, 0.5, f'{label}\nθ = {int(theta)}°',
                       ha='right', va='center', fontsize=7,
                       transform=ax_row[0].transAxes)
        ax_row[1].text(0.5, -0.02, f'δθ = {dt:+.1f}°',
                       ha='center', va='top', fontsize=7,
                       transform=ax_row[1].transAxes)
        ax_row[2].text(0.5, -0.02,
                       f'θ_pre = {int(theta_pre)}°   |r| = {abs(resid):.2f}°',
                       ha='center', va='top', fontsize=7,
                       transform=ax_row[2].transAxes)
        if tier != last_tier:
            ax_row[0].text(-0.45, 1.05, tier, ha='left', va='bottom', fontsize=8,
                           fontweight='bold', color='dimgray',
                           transform=ax_row[0].transAxes)
            last_tier = tier
        for a in ax_row:
            a.set_xticks([]); a.set_yticks([])
            a.set_xlim(0,1); a.set_ylim(0,1)
            for sp in a.spines.values():
                sp.set_edgecolor('black'); sp.set_linewidth(0.5)
    plt.savefig(outpath, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'  → {outpath.name}')


def main():
    print(f'Writing Phase 3 candidate visualizations to: {OUTDIR}')
    for cell in CELLS:
        roi_tag = cell['roi_label'].replace(' ', '').replace('+','_').replace('-','')
        fname = f'phase3_sub-{cell["subj"]}_{roi_tag}.png'
        render_figure(cell, OUTDIR / fname)
    # README
    with (OUTDIR / 'README.txt').open('w') as fh:
        fh.write('Phase 3 candidate filter visualizations\n')
        fh.write('=' * 40 + '\n')
        fh.write('Generated 2026-05-03 (cycle10d / cycle8_preimage params)\n\n')
        for c in CELLS:
            fh.write(f'sub-{c["subj"]} ({c["cvd"]}) {c["roi_label"]}: '
                     f'β_s={c["beta_s"]}, β_c={c["beta_c"]}\n')
            fh.write(f'  {c["note"]}\n\n')
        fh.write('Interpretation:\n')
        fh.write('  Col 1 == Col 4 indicates a surjective filter (pre-image is exact).\n')
        fh.write('  CVD(Original) (Col 2) → Filtered (Col 3) shows what stimulus to present.\n')
        fh.write('  CVD(Filtered) (Col 4) is what the CVD subject would perceive AFTER filter.\n')
        fh.write('  Goal: Col 4 ≈ Col 1 (CVD perception of filtered ≈ HC perception of original).\n')
    print(f'  → README.txt')
    print('Done.')


if __name__ == '__main__':
    main()
