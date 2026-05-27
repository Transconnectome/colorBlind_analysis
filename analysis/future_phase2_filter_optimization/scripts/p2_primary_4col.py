"""Pipeline 2 PRIMARY candidates — 4-col visualization.

Per PIPELINE_2_CLOSURE.md (2026-05-26) §5.1, the primary results are three
2-Component filter candidates:

  sub-08 βs-dom  (β_s=38, β_c=-10)   γ_all + RDM_V1     deutan
  sub-08 βc-dom  (β_s= 6, β_c=-42)   γ_OY  + RDM_V2/V3  deutan
  sub-09 βc-rot  (β_s= 2, β_c= 24)   γ_all + RDM_V1     protan

R+C references (Δλ, g) are NOT primary candidates (§5.1: "R+C insufficient
for sub-09"); shown as a supplementary panel.

4-col STIM_LAB convention (project memory project_stim_lab_rendering 2026-05-10):
  col 1: Original          render_at_hue(θ)
  col 2: CVD perceives     render_at_hue(θ + δθ)     [forward 2-comp]
  col 3: Filter (pre-image) render_at_hue(θ_pre)
  col 4: CVD(Filter)        render_at_hue(forward(θ_pre))  ≈ θ

Rows: c1..c8 canonical experimental hues.
Output: results/visualizations/pipeline2_primary_4col/
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

_THIS = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS))

from stim_lab_render import render_at_hue
from two_comp import forward_2comp as _two_comp_forward_8, THETA_CONF

OUT = _THIS.parent / 'results' / 'visualizations' / 'pipeline2_primary_4col'
OUT.mkdir(parents=True, exist_ok=True)

HUE_8 = np.array([0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0])
COLOR_LABELS = ['c1 R(0°)', 'c2 O(45°)', 'c3 Y(90°)', 'c4 G(135°)',
                'c5 C(180°)', 'c6 B(225°)', 'c7 P(270°)', 'c8 M(315°)']


# ---- Raw nominal-θ forward (matches Phase B v6 closure: scripts/two_comp.py) ----
# PIPELINE_2_CLOSURE.md Phase B v6 main runner (s10b_v6_pca_rdm.py:31, :231, :607)
# uses scripts/two_comp.py:forward_2comp which applies trig to CIElab nominal θ
# directly (no h_base / Stockman frame conversion). Use the same convention here.
def forward_closure(theta_deg: float, family: str, bs: float, bc: float):
    """δθ = β_s·cos(θ−90°) + β_c·cos(θ−θ_conf), θ in CIElab nominal."""
    theta_conf = THETA_CONF[family]
    rad_s = np.deg2rad(float(theta_deg) - 90.0)
    rad_c = np.deg2rad(float(theta_deg) - theta_conf)
    dt = bs * np.cos(rad_s) + bc * np.cos(rad_c)
    theta_perc = (float(theta_deg) + dt) % 360.0
    return theta_perc, float(dt)


def pre_image_closure(theta_target: float, family: str, bs: float, bc: float,
                      n_grid: int = 2880):
    """Pre-image under closure forward. Returns (θ_pre, signed_residual_deg)."""
    grid = np.linspace(0.0, 360.0, n_grid, endpoint=False)

    def _wrap180(x):
        return (x + 180.0) % 360.0 - 180.0

    theta_conf = THETA_CONF[family]
    rad_s = np.deg2rad(grid - 90.0)
    rad_c = np.deg2rad(grid - theta_conf)
    dt = bs * np.cos(rad_s) + bc * np.cos(rad_c)
    fwd = (grid + dt) % 360.0
    resid = _wrap180(fwd - theta_target)
    i = int(np.argmin(np.abs(resid)))
    return float(grid[i]), float(resid[i])

matplotlib.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Helvetica', 'Arial', 'DejaVu Sans'],
    'font.size': 8, 'axes.titlesize': 9, 'axes.labelsize': 8,
    'xtick.labelsize': 7, 'ytick.labelsize': 7,
})

PRIMARY = [
    {
        'label': 'S08-βs-dom',
        'subject': 'sub-08', 'family': 'deutan',
        'beta_s': 38.0, 'beta_c': -10.0,
        'combo': 'γ_all + RDM_V1',
        'note': 'AIC 9.28  BIC 6.66  bdy 0%  test_med −1.14±0.86  focal 28.0',
    },
    {
        'label': 'S08-βc-dom',
        'subject': 'sub-08', 'family': 'deutan',
        'beta_s': 6.0, 'beta_c': -42.0,
        'combo': 'γ_OY + RDM_V2 (also V3)',
        'note': 'AIC 10.88  BIC 8.27  bdy 9%  test_med −2.36±2.15  focal 62.5',
    },
    {
        'label': 'S09-βc-rot',
        'subject': 'sub-09', 'family': 'protan',
        'beta_s': 2.0, 'beta_c': 24.0,
        'combo': 'γ_all + RDM_V1 (also γ_GB)',
        'note': 'AIC 6.26  BIC 3.64  bdy 0%  test_med −1.52±1.41  focal 6.18',
    },
]


def render_one(spec, outpath):
    sub = spec['subject']; fam = spec['family']
    bs = spec['beta_s']; bc = spec['beta_c']

    fig, axes = plt.subplots(8, 4, figsize=(7.5, 12.5),
                             gridspec_kw={'wspace': 0.05, 'hspace': 0.22})
    fig.suptitle(
        f"{spec['label']}  —  {sub} ({fam})  ·  2-Component  ·  β_s={bs:.0f}°, β_c={bc:.0f}°\n"
        f"fit loss: {spec['combo']}\n"
        f"{spec['note']}",
        fontsize=9.5, y=0.998,
    )

    # Closure δθ 8-vec (exact match to Phase B v6: scripts/two_comp.py)
    dt_closure_8 = _two_comp_forward_8(bs, bc, fam)

    for i, theta in enumerate(HUE_8):
        theta = float(theta)
        # col 2 δθ: closure forward (raw nominal-θ, fit code consistent)
        dt = float(dt_closure_8[i])
        theta_cvd = (theta + dt) % 360.0
        # col 3/4: pre-image under same closure forward
        theta_pre, resid = pre_image_closure(theta, fam, bs, bc)
        theta_cvd_of_pre, _ = forward_closure(theta_pre, fam, bs, bc)

        rgb0 = render_at_hue(theta)            # ΔL*=0 (2-comp by definition)
        rgb1 = render_at_hue(theta_cvd)
        rgb2 = render_at_hue(theta_pre)
        rgb3 = render_at_hue(theta_cvd_of_pre)

        for j, rgb in enumerate([rgb0, rgb1, rgb2, rgb3]):
            ax = axes[i, j]
            ax.add_patch(Rectangle((0, 0), 1, 1, color=rgb))
            ax.set_xlim(0, 1); ax.set_ylim(0, 1)
            ax.set_xticks([]); ax.set_yticks([])
            for sp in ax.spines.values():
                sp.set_edgecolor('black'); sp.set_linewidth(0.4)

        axes[i, 0].text(-0.06, 0.5, f'{COLOR_LABELS[i]}\nθ={int(theta)}°',
                        ha='right', va='center', fontsize=7,
                        transform=axes[i, 0].transAxes)
        axes[i, 1].text(0.5, -0.06, f'δθ={dt:+.1f}°',
                        ha='center', va='top', fontsize=7.2,
                        transform=axes[i, 1].transAxes)
        axes[i, 2].text(0.5, -0.06,
                        f'θ_pre={int(round(theta_pre))}°  |r|={abs(resid):.2f}°',
                        ha='center', va='top', fontsize=7.2,
                        transform=axes[i, 2].transAxes)

    axes[0, 0].set_title('Original\n(stimulus θ)', fontsize=9)
    axes[0, 1].set_title('CVD perceives\n(forward 2-comp)', fontsize=9)
    axes[0, 2].set_title('Filter\n(pre-image θ_pre)', fontsize=9)
    axes[0, 3].set_title('CVD(Filter)\n(target restored)', fontsize=9)

    plt.tight_layout()
    plt.savefig(outpath, dpi=160, bbox_inches='tight')
    plt.close(fig)
    print(f'  saved: {outpath.name}')


def render_summary(specs, outpath):
    n = len(specs)
    fig, axes = plt.subplots(8, 4 * n, figsize=(6.5 * n, 13),
                             gridspec_kw={'wspace': 0.05, 'hspace': 0.22})

    for k, spec in enumerate(specs):
        sub = spec['subject']; fam = spec['family']
        bs = spec['beta_s']; bc = spec['beta_c']
        c0 = k * 4

        dt_closure_8 = _two_comp_forward_8(bs, bc, fam)
        for i, theta in enumerate(HUE_8):
            theta = float(theta)
            dt = float(dt_closure_8[i])
            theta_cvd = (theta + dt) % 360.0
            theta_pre, resid = pre_image_closure(theta, fam, bs, bc)
            theta_cvd_of_pre, _ = forward_closure(theta_pre, fam, bs, bc)

            rgbs = [render_at_hue(theta), render_at_hue(theta_cvd),
                    render_at_hue(theta_pre), render_at_hue(theta_cvd_of_pre)]
            for j, rgb in enumerate(rgbs):
                ax = axes[i, c0 + j]
                ax.add_patch(Rectangle((0, 0), 1, 1, color=rgb))
                ax.set_xlim(0, 1); ax.set_ylim(0, 1)
                ax.set_xticks([]); ax.set_yticks([])
                for sp in ax.spines.values():
                    sp.set_edgecolor('black'); sp.set_linewidth(0.4)

            if k == 0:
                axes[i, c0].text(-0.07, 0.5, COLOR_LABELS[i],
                                 ha='right', va='center', fontsize=7,
                                 transform=axes[i, c0].transAxes)
            axes[i, c0 + 1].text(0.5, -0.06, f'δθ={dt:+.1f}°',
                                 ha='center', va='top', fontsize=7.0,
                                 transform=axes[i, c0 + 1].transAxes)

        head = (f"{spec['label']}\n{spec['subject']} ({spec['family']})\n"
                f"β_s={bs:.0f}°, β_c={bc:.0f}°")
        axes[0, c0].set_title(f"Orig\n{head}", fontsize=8)
        axes[0, c0 + 1].set_title('CVD\nperceives', fontsize=8)
        axes[0, c0 + 2].set_title('Filter\n(pre-image)', fontsize=8)
        axes[0, c0 + 3].set_title('CVD\n(Filter)', fontsize=8)

    fig.suptitle('Pipeline 2 — primary 2-Component filter candidates  ·  STIM_LAB rendering  ·  '
                 'forward = scripts/two_comp.py (Phase B v6 closure)',
                 fontsize=10.5, y=1.005)
    plt.tight_layout()
    plt.savefig(outpath, dpi=160, bbox_inches='tight')
    plt.close(fig)
    print(f'  saved: {outpath.name}')


if __name__ == '__main__':
    print(f'Output → {OUT}')
    for spec in PRIMARY:
        fname = OUT / f"p2_primary_4col_{spec['label'].replace('β', 'b').replace('-', '_')}.png"
        render_one(spec, fname)
    render_summary(PRIMARY, OUT / 'p2_primary_4col_summary.png')
    print('\ndone.')
