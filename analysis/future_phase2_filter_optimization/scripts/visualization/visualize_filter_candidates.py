#!/usr/bin/env python3
"""
visualize_filter_candidates.py
==============================

6 figures (3 models × 2 subjects) showing 4-column progression:

    Col 1: Original color (hue θ on the L*=75, C*=40 experimental ring)
    Col 2: CVD-perceived  (forward pass under the model at θ)
    Col 3: Filtered       (pre-image θ_pre of θ under the model)
    Col 4: CVD(Filtered)  (forward pass at θ_pre — acid test)

Display note
------------
The model / pre-image math is done on the experimental L*=75, C*=40 ring,
but the swatches are rendered at the *most saturated in-gamut chroma*
at each hue (up to C*=80). This preserves the CIELab hue angle exactly
while restoring the vivid appearance of the actual experimental stimuli,
which look more saturated than the pastel C*=40 display ring suggests.

Three color tiers are stacked vertically in every figure:

    Tier 1: fMRI 8-stim ring (θ = 0°, 45°, …, 315°)
    Tier 2: CVD confusion anchors (near Stockman protan/deutan axes)
    Tier 3: sRGB vivid primaries mapped to the L*=75, C*=40 ring

Models    : machado_1way, rc_opponent (R+C), two_component
Subjects  : sub-08 (deutan, moderate), sub-09 (protan, moderate)

Pre-images that are not stored on disk are computed on the fly by minimising
the wrapped angular residual  f(θ) = θ + δθ(θ) − θ_target  on a dense grid
with bracket-refinement via brentq.

Caveats
-------
• We treat δθ as a hue-domain correction applied to the CIELab angle for
  display, i.e. "CVD-perceived" is rendered at (θ + δθ_forward). This is
  the hue-shift convention also adopted by the filter pre-image pipeline
  (preimage_angles are CIELab angles).
• Sub-09 R+C fit collapses to g=0 → the R+C figure for sub-09 is
  numerically identical to the Machado figure. We still generate it and
  flag this in the title to make the degeneracy explicit.
• Sub-09 Machado pre-image has 4/8 non-zero residuals in the stored JSON
  (non-surjective model); this script recomputes and reports residuals
  per cell so the failure mode is visible.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from scipy.optimize import brentq

# -------------------------------------------------------------------
# Path boilerplate
# -------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR.parent))

_PHASE2_DIR = _SCRIPT_DIR.parent
for _base in [_PHASE2_DIR.parent, _PHASE2_DIR.parent.parent]:
    _fwd = _base / 'future_phase1_forward_model' / 'scripts'
    if _fwd.exists() and str(_fwd) not in sys.path:
        sys.path.insert(0, str(_fwd))
        break

from machado_simulator import (                                # noqa: E402
    machado_shifted_hue_at, machado_mixed_fundamentals,
    _load_stockman_grid,
)
from retinal_cortical import machado_with_opponent_gain_at     # noqa: E402
from stockman_cone_shift import (                              # noqa: E402
    _compute_spectral_shift_lms, lab_to_xyz, D65_XYZ,
)

# -------------------------------------------------------------------
# Constants
# -------------------------------------------------------------------
CONF_AXIS = {'protan': 16.0, 'deutan': 150.0, 'normal': 83.0}  # Stockman
L_STAR = 75.0
CHROMA = 40.0                # model / experimental ring (keep fixed)

# ── DISPLAY-ONLY parameters ──────────────────────────────────────────
# A single fixed (L*, C*) in CIELab cannot simultaneously produce vivid
# sRGB for all 8 hue angles: yellow peaks at L*≈97, blue at L*≈32.
# For display we therefore search over both L* and C* per hue to find the
# maximally-saturated in-gamut sRGB with the given CIELab hue angle.
# This yields the "native monitor" appearance: red, orange, yellow, green,
# cyan, blue, purple, magenta — i.e. RGB primaries + complements.
DISPLAY_L_RANGE = (20.0, 97.0)
DISPLAY_L_STEPS = 40
DISPLAY_CHROMA_MAX = 150.0

OUTDIR = _PHASE2_DIR / 'results' / 'visualizations' / 'filter_visualization'
OUTDIR.mkdir(parents=True, exist_ok=True)

# Subject metadata — per-subject best-fit params for each model
# Sources:
#   machado / rc : results/fits/preimage/*.json  (phase_a fit)
#   2comp        : results/fits/canonical_2component_v2/*.json (best_params)
SUBJECTS = {
    '08': {
        'cvd':     'deutan',
        'machado': {'delta_lambda': 1.5},                         # sub-08 deutan
        'rc':      {'delta_lambda': 2.0,  'g': 2.25},             # LOCO-best
        '2comp':   {'beta_s': 38.0, 'beta_c': -14.0},             # LOCO-best
    },
    '09': {
        'cvd':     'protan',
        'machado': {'delta_lambda': 13.5},                        # sub-09 protan
        'rc':      {'delta_lambda': 13.5, 'g': 0.0},              # R+C degenerate
        '2comp':   {'beta_s': 6.0,  'beta_c': -22.0},             # LOCO-best
    },
}


# -------------------------------------------------------------------
# CIELab → sRGB for display (standard D65)
# -------------------------------------------------------------------
def _lab_to_srgb_unclipped(L: float, a: float, b: float) -> np.ndarray:
    """Raw CIELab → sRGB, may return values outside [0, 1] (out-of-gamut)."""
    y = (L + 16.0) / 116.0
    x = a / 500.0 + y
    z = y - b / 200.0
    xyz = np.array([x, y, z], dtype=float)
    xyz = np.where(xyz > 0.206893, xyz ** 3, (xyz - 16.0 / 116.0) / 7.787)
    xyz = xyz * np.array([0.95047, 1.0, 1.08883])
    M = np.array([[3.2406, -1.5372, -0.4986],
                  [-0.9689, 1.8758,  0.0415],
                  [0.0557,  -0.2040,  1.0570]])
    rgb = M @ xyz
    # Handle negative linear-RGB before gamma to preserve sign info
    sign = np.sign(rgb)
    mag = np.abs(rgb)
    rgb = np.where(mag <= 0.0031308,
                   12.92 * rgb,
                   sign * (1.055 * mag ** (1 / 2.4) - 0.055))
    return rgb


def lab_to_srgb(L: float, a: float, b: float) -> np.ndarray:
    """CIELab → sRGB with standard [0, 1] clip."""
    return np.clip(_lab_to_srgb_unclipped(L, a, b), 0.0, 1.0)


def angle_to_rgb(theta_deg: float, L: float = L_STAR, C: float = CHROMA) -> np.ndarray:
    """Standard CIELab hue convention (a = C·cos θ, b = C·sin θ)."""
    rad = np.deg2rad(theta_deg)
    a = C * np.cos(rad)
    b = C * np.sin(rad)
    return lab_to_srgb(L, a, b)


def _max_chroma_at_L(L: float, cos_t: float, sin_t: float,
                     c_max: float, tol: float) -> float:
    """Largest in-gamut chroma at fixed (L*, hue)."""
    def in_gamut(C: float) -> bool:
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


def angle_to_rgb_vivid(theta_deg: float,
                       L_range: tuple = DISPLAY_L_RANGE,
                       n_L: int = DISPLAY_L_STEPS,
                       c_max: float = DISPLAY_CHROMA_MAX,
                       tol: float = 1e-3) -> np.ndarray:
    """Return the most-vivid in-gamut sRGB for a given CIELab hue angle.

    Sweeps L* over `L_range` and, at each L*, binary-searches the largest
    in-gamut chroma. Picks the (L*, C*) that maximises (max-min) of the
    resulting sRGB — a robust proxy for visual saturation. Preserves the
    CIELab hue angle exactly; only L* and C* are free.

    This produces "native monitor" rendering per hue: yellow ≈ (1,1,0),
    blue ≈ (0,0,1), etc., matching RGB primaries and complements.

    DISPLAY ONLY. The experimental/model ring stays at (L_STAR, CHROMA).
    """
    rad = np.deg2rad(theta_deg)
    cos_t, sin_t = np.cos(rad), np.sin(rad)

    best_rgb = np.array([0.5, 0.5, 0.5])
    best_score = -1.0
    for L in np.linspace(L_range[0], L_range[1], n_L):
        C = _max_chroma_at_L(L, cos_t, sin_t, c_max, tol)
        rgb = np.clip(
            _lab_to_srgb_unclipped(L, C * cos_t, C * sin_t), 0.0, 1.0)
        # Saturation proxy: chroma-like (max-min) × brightness factor
        sat = float(rgb.max() - rgb.min())
        if sat > best_score:
            best_score = sat
            best_rgb = rgb
    return best_rgb


# -------------------------------------------------------------------
# CVD-response-equivalent Lab (cone-shift → luminance-aware simulation)
# -------------------------------------------------------------------
def _xyz_to_lab(xyz: np.ndarray, white: np.ndarray = D65_XYZ) -> np.ndarray:
    """XYZ → CIELab (D65)."""
    def f(t: np.ndarray) -> np.ndarray:
        delta = 6.0 / 29.0
        return np.where(
            t > delta ** 3,
            np.cbrt(t),
            t / (3.0 * delta ** 2) + 4.0 / 29.0,
        )

    xyz = np.asarray(xyz, dtype=float)
    xyz_n = xyz / white
    fx, fy, fz = f(xyz_n[..., 0]), f(xyz_n[..., 1]), f(xyz_n[..., 2])
    L = 116.0 * fy - 16.0
    a = 500.0 * (fx - fy)
    b = 200.0 * (fy - fz)
    return np.stack([L, a, b], axis=-1)


def cvd_response_lab(theta_deg: float, cvd: str, delta_lambda: float,
                     L_star: float = L_STAR,
                     chroma: float = CHROMA) -> np.ndarray:
    """Return CIELab of the cone-response-equivalent percept.

    Builds the stimulus at (L_star, chroma, θ), projects through the
    CVD-shifted Stockman fundamentals to get the anomalous LMS response,
    then displays it as the XYZ (via inverse normal-cone map) that a
    normal observer would need to see to produce the same LMS response.
    Returned L* varies with θ: long-λ colours darken under protan, etc.

    Returns:
        (3,) CIELab triplet (L*_cvd, a*_cvd, b*_cvd).
    """
    if cvd == 'normal' or abs(delta_lambda) < 1e-9:
        rad = np.deg2rad(theta_deg)
        return np.array([L_star, chroma * np.cos(rad), chroma * np.sin(rad)])

    wl, L, M, S, _, _, M_xyz2lms_orig = _load_stockman_grid()
    rad = np.deg2rad(float(theta_deg))
    lab = np.array([[L_star, chroma * np.cos(rad), chroma * np.sin(rad)]])
    xyz_orig = lab_to_xyz(lab)  # (1, 3)

    # CVD cone fundamentals (Machado 1-way, α coupled to Δλ)
    L_a, M_a, S_a = machado_mixed_fundamentals(float(delta_lambda), cvd,
                                               wl, L, M, S)

    # Anomalous LMS response to the original stimulus
    lms_cvd = _compute_spectral_shift_lms(wl, L_a, M_a, S_a,
                                          M_xyz2lms_orig, xyz_orig)  # (1, 3)

    # Normal-observer XYZ that produces the same LMS → visualised percept
    xyz_equiv = np.linalg.solve(M_xyz2lms_orig, lms_cvd[0])
    return _xyz_to_lab(xyz_equiv)


def lab_to_rgb_display(L: float, a: float, b: float) -> np.ndarray:
    """Lab → sRGB with gamut clip. Preserves luminance (no search)."""
    return lab_to_srgb(float(L), float(a), float(b))


# -------------------------------------------------------------------
# Forward δθ functions per model (CIELab-input, CIELab-output convention)
# -------------------------------------------------------------------
def _scalar(x):
    return float(np.atleast_1d(x)[0])


def dt_machado(theta: float, cvd: str, delta_lambda: float) -> float:
    _, _, dt = machado_shifted_hue_at(
        delta_lambda, cvd, float(theta), L_star=L_STAR, chroma=CHROMA)
    return _scalar(dt)


def dt_rc(theta: float, cvd: str, delta_lambda: float, g: float) -> float:
    _, _, dt = machado_with_opponent_gain_at(
        delta_lambda, g, cvd, float(theta), L_star=L_STAR, chroma=CHROMA)
    return _scalar(dt)


def dt_2comp(theta: float, cvd: str, beta_s: float, beta_c: float) -> float:
    hue_base, _, _ = machado_shifted_hue_at(
        0.0, cvd, float(theta), L_star=L_STAR, chroma=CHROMA)
    hb = _scalar(hue_base)
    theta_conf = CONF_AXIS[cvd]
    return (beta_s * np.cos(np.radians(hb - 90.0))
            + beta_c * np.cos(np.radians(hb - theta_conf)))


def forward_perceived(theta: float, model: str, cvd: str, params: dict):
    """Return (θ_perceived_cielab, δθ)."""
    if model == 'machado':
        dt = dt_machado(theta, cvd, params['delta_lambda'])
    elif model == 'rc':
        dt = dt_rc(theta, cvd, params['delta_lambda'], params['g'])
    elif model == '2comp':
        dt = dt_2comp(theta, cvd, params['beta_s'], params['beta_c'])
    else:
        raise ValueError(f'Unknown model: {model}')
    return (theta + dt) % 360.0, dt


# -------------------------------------------------------------------
# Pre-image search via dense grid + brentq refine
# -------------------------------------------------------------------
def _wrap180(x: float) -> float:
    return (x + 180.0) % 360.0 - 180.0


def find_preimage(theta_target: float, model: str, cvd: str, params: dict,
                  n_grid: int = 1440) -> tuple[float, float]:
    """Find θ_pre with forward(θ_pre) ≈ θ_target (mod 360).

    Returns (θ_pre, signed_residual_deg).
    """
    grid = np.linspace(0.0, 360.0, n_grid, endpoint=False)

    def residual(t: float) -> float:
        pred, _ = forward_perceived(float(t) % 360.0, model, cvd, params)
        return _wrap180(pred - theta_target)

    res_grid = np.array([residual(t) for t in grid])
    i_min = int(np.argmin(np.abs(res_grid)))
    theta_pre = float(grid[i_min])

    # Local brentq refine if sign change inside ±(360/n_grid)·3
    step = 360.0 / n_grid * 3
    lo = grid[i_min] - step
    hi = grid[i_min] + step
    try:
        f_lo = residual(lo)
        f_hi = residual(hi)
        if f_lo * f_hi < 0:
            theta_pre = brentq(lambda t: residual(t), lo, hi) % 360.0
    except Exception:
        pass

    return theta_pre % 360.0, residual(theta_pre)


# -------------------------------------------------------------------
# Color palettes (three tiers)
# -------------------------------------------------------------------
# Tier 1 — fMRI 8-stim ring, labels use standard CIELab naming
TIER1 = [
    (0,   'c1 (magenta-red)'),
    (45,  'c2 (orange)'),
    (90,  'c3 (yellow)'),
    (135, 'c4 (yellow-green)'),
    (180, 'c5 (teal/green)'),
    (225, 'c6 (cyan-blue)'),
    (270, 'c7 (blue)'),
    (315, 'c8 (purple)'),
]

# Tier 2 — CVD confusion anchors (Stockman-axis mapped onto CIELab ring)
TIER2 = [
    (16,  'confP+ (protan axis +)'),
    (196, 'confP− (protan axis −)'),
    (150, 'confD+ (deutan axis +)'),
    (330, 'confD− (deutan axis −)'),
    (60,  'Ishihara orange'),
    (240, 'cobalt (control)'),
]

# Tier 3 — sRGB primaries approximately projected to the L*=75 ring
# (These hues are chosen near the hue of saturated sRGB primaries at
#  L*=75; swatches are rendered at the max in-gamut chroma per hue, so
#  they look close to the vivid sRGB primaries.)
TIER3 = [
    (40,  'sRGB R (red)'),
    (90,  'sRGB Y (yellow)'),
    (140, 'sRGB G (green)'),
    (200, 'sRGB C (cyan)'),
    (270, 'sRGB B (blue)'),
    (330, 'sRGB M (magenta)'),
]

PALETTE = [
    ('Tier 1: fMRI 8-stim ring',          TIER1),
    ('Tier 2: CVD confusion anchors',     TIER2),
    ('Tier 3: sRGB primaries at L*=75',   TIER3),
]


# -------------------------------------------------------------------
# Figure rendering
# -------------------------------------------------------------------
MODEL_TITLE = {
    'machado': 'Machado 2009 (1-way cone shift)',
    'rc':      'R + C (retinal + opponent gain)',
    '2comp':   '2-Component (stimulus-space dilation)',
}


def _param_str(model: str, params: dict) -> str:
    if model == 'machado':
        return f"Δλ = {params['delta_lambda']} nm"
    if model == 'rc':
        gn = params['g']
        degen = '  [degenerate: g=0 ⇒ equals Machado]' if gn == 0.0 else ''
        return f"Δλ = {params['delta_lambda']} nm, g = {gn}{degen}"
    if model == '2comp':
        return f"β_s = {params['beta_s']}°, β_c = {params['beta_c']}°"
    return ''


def render_figure(model: str, subj_id: str, outpath: Path) -> None:
    meta = SUBJECTS[subj_id]
    cvd = meta['cvd']
    params = meta[{'machado': 'machado', 'rc': 'rc', '2comp': '2comp'}[model]]

    rows = [(tier, theta, label)
            for tier, colors in PALETTE
            for (theta, label) in colors]
    n_rows = len(rows)

    fig_height = 0.55 * n_rows + 1.8
    fig, axes = plt.subplots(
        n_rows, 4,
        figsize=(9.0, fig_height),
        gridspec_kw={'hspace': 0.08, 'wspace': 0.08})

    fig.suptitle(
        f'{MODEL_TITLE[model]}  —  sub-{subj_id} ({cvd})\n'
        f'{_param_str(model, params)}',
        fontsize=11, y=0.995)

    col_titles = ['Original', 'CVD perceives', 'Filtered (pre-image)',
                  'CVD(Filtered)']
    for ax, title in zip(axes[0], col_titles):
        ax.set_title(title, fontsize=9)

    # Luminance anchor: always use the subject's Machado Δλ fit so the
    # CVD columns carry the same cone-shift-derived ΔL* across all three
    # model figures. 2-comp has no Δλ of its own; Machado/R+C use their
    # own fit, but we read it from the Machado entry for consistency.
    dlam_cvd = float(SUBJECTS[subj_id]['machado']['delta_lambda'])

    last_tier = None
    for i, (tier, theta, label) in enumerate(rows):
        ax_row = axes[i]

        # Original & pre-image stimulus swatches (vivid, for anchoring)
        rgb_orig = angle_to_rgb_vivid(theta)
        theta_pre, resid = find_preimage(theta, model, cvd, params)
        rgb_pre = angle_to_rgb_vivid(theta_pre)

        # CVD-perceived: Machado-derived luminance at (θ, Δλ), hue from
        # the active model. Preserves experimental chroma at C*=40.
        theta_cvd, dt = forward_perceived(theta, model, cvd, params)
        lab_cvd_anchor = cvd_response_lab(theta, cvd, dlam_cvd)
        L_cvd = float(lab_cvd_anchor[0])
        rgb_cvd = lab_to_rgb_display(
            L_cvd,
            CHROMA * np.cos(np.deg2rad(theta_cvd)),
            CHROMA * np.sin(np.deg2rad(theta_cvd)))

        # CVD(Filtered): same luminance machinery applied to the filter
        # output (stimulus at θ_pre). The filter can only re-place the
        # stimulus on the L*=75 ring; residual CVD luminance drop remains.
        theta_cvd_of_pre, _ = forward_perceived(theta_pre, model, cvd, params)
        lab_cvd_of_pre = cvd_response_lab(theta_pre, cvd, dlam_cvd)
        L_cvd_of_pre = float(lab_cvd_of_pre[0])
        rgb_cvd_of_pre = lab_to_rgb_display(
            L_cvd_of_pre,
            CHROMA * np.cos(np.deg2rad(theta_cvd_of_pre)),
            CHROMA * np.sin(np.deg2rad(theta_cvd_of_pre)))

        ax_row[0].add_patch(Rectangle((0, 0), 1, 1, color=rgb_orig))
        ax_row[1].add_patch(Rectangle((0, 0), 1, 1, color=rgb_cvd))
        ax_row[2].add_patch(Rectangle((0, 0), 1, 1, color=rgb_pre))
        ax_row[3].add_patch(Rectangle((0, 0), 1, 1, color=rgb_cvd_of_pre))

        ax_row[0].text(
            -0.05, 0.5,
            f'{label}\nθ = {int(theta)}°',
            ha='right', va='center', fontsize=7,
            transform=ax_row[0].transAxes)
        ax_row[1].text(
            0.5, -0.02, f'δθ = {dt:+.1f}°',
            ha='center', va='top', fontsize=7,
            transform=ax_row[1].transAxes)
        ax_row[2].text(
            0.5, -0.02,
            f'θ_pre = {int(theta_pre)}°   |r| = {abs(resid):.2f}°',
            ha='center', va='top', fontsize=7,
            transform=ax_row[2].transAxes)

        if tier != last_tier:
            ax_row[0].text(
                -0.45, 1.05, tier,
                ha='left', va='bottom', fontsize=8,
                fontweight='bold', color='dimgray',
                transform=ax_row[0].transAxes)
            last_tier = tier

        for a in ax_row:
            a.set_xticks([])
            a.set_yticks([])
            a.set_xlim(0, 1)
            a.set_ylim(0, 1)
            for sp in a.spines.values():
                sp.set_edgecolor('black')
                sp.set_linewidth(0.5)

    plt.savefig(outpath, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'  → {outpath.name}')


# -------------------------------------------------------------------
# Driver
# -------------------------------------------------------------------
def main() -> None:
    print(f'Writing figures to: {OUTDIR}')
    for model in ['machado', 'rc', '2comp']:
        for subj in ['08', '09']:
            fname = f'filter_viz_sub-{subj}_{model}.png'
            render_figure(model, subj, OUTDIR / fname)

    # Also save a small text sanity report
    report = OUTDIR / 'README.txt'
    with report.open('w') as fh:
        fh.write('Filter-candidate visualization report\n')
        fh.write('=' * 40 + '\n\n')
        for subj, meta in SUBJECTS.items():
            fh.write(f'sub-{subj} ({meta["cvd"]})\n')
            for mk, mp in [('machado', meta['machado']),
                           ('rc', meta['rc']),
                           ('2comp', meta['2comp'])]:
                fh.write(f'  {mk}: {mp}\n')
            fh.write('\n')
        fh.write('\nInterpretation:\n')
        fh.write('  Col 1 == Col 4 indicates a surjective filter model\n')
        fh.write('  (CVD(Filtered(θ)) ≈ θ). Large |r| in Col 3 flags\n')
        fh.write('  non-surjective cells — the model cannot invert that θ.\n')
    print(f'  → {report.name}')
    print('Done.')


if __name__ == '__main__':
    main()
