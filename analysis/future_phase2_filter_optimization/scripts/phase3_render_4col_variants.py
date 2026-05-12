"""phase3_render_4col_variants.py — 4-column color filter viz for all loss variants.

For each variant's optimum (β_s, β_c), render a 4-column figure:
  col 1: Original stimulus color
  col 2: CVD perceives (forward_old)
  col 3: Filtered (pre-image)
  col 4: CVD perceives filtered output (= original target by construction)

Uses OLD CIElab-direct formula (matches the fit framework).
"""
from __future__ import annotations
import sys
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR))
sys.path.insert(0, str(_THIS_DIR / "visualization"))

from stim_lab_render import render_at_hue as _render_stim_lab

OUTDIR_BASE = _THIS_DIR.parent / "results" / "old_formula"

TIER1 = [(0, "c1 (red)"), (45, "c2 (orange)"), (90, "c3 (yellow)"),
         (135, "c4 (green)"), (180, "c5 (cyan)"), (225, "c6 (sky)"),
         (270, "c7 (blue)"), (315, "c8 (magenta)")]


def dt_old(theta_deg, beta_s, beta_c, theta_conf_deg=150.0):
    th_rad = np.deg2rad(theta_deg)
    return (beta_s * np.cos(th_rad - np.deg2rad(90.0))
            + beta_c * np.cos(th_rad - np.deg2rad(theta_conf_deg)))


def forward_old(theta_deg, beta_s, beta_c):
    dt = dt_old(theta_deg, beta_s, beta_c)
    return (theta_deg + dt) % 360.0, dt


def pre_image_old(target_deg, beta_s, beta_c, n_grid=3600):
    grid = np.linspace(0.0, 360.0, n_grid, endpoint=False)
    forwards = np.array([forward_old(t, beta_s, beta_c)[0] for t in grid])
    diff = (forwards - target_deg + 180.0) % 360.0 - 180.0
    i = int(np.argmin(np.abs(diff)))
    return float(grid[i]), float(diff[i])


def render_filter(beta_s, beta_c, title, subtitle, out_path):
    n = len(TIER1)
    fig, axes = plt.subplots(n, 4, figsize=(8.5, 0.65 * n + 1.5),
                             gridspec_kw={"hspace": 0.10, "wspace": 0.08})
    fig.suptitle(f"{title}\n{subtitle}",
                 fontsize=10, y=0.995)
    for ax, ct in zip(axes[0], ["Original", "CVD perceives",
                                 "Filtered (pre-image)", "CVD(Filtered)"]):
        ax.set_title(ct, fontsize=9)

    for i, (theta, label) in enumerate(TIER1):
        ax_row = axes[i]
        theta_pre, resid = pre_image_old(float(theta), beta_s, beta_c)
        theta_cvd, dt = forward_old(float(theta), beta_s, beta_c)
        theta_cvd_pre, _ = forward_old(theta_pre, beta_s, beta_c)

        rgb_orig = _render_stim_lab(float(theta), dL=0.0)
        rgb_cvd = _render_stim_lab(theta_cvd, dL=0.0)
        rgb_pre = _render_stim_lab(theta_pre, dL=0.0)
        rgb_cvd_pre = _render_stim_lab(theta_cvd_pre, dL=0.0)

        for ax, rgb in zip(ax_row, [rgb_orig, rgb_cvd, rgb_pre, rgb_cvd_pre]):
            ax.add_patch(Rectangle((0, 0), 1, 1, color=rgb))
        ax_row[0].text(-0.05, 0.5, f"{label}\nθ={theta}°", ha="right",
                       va="center", fontsize=7, transform=ax_row[0].transAxes)
        ax_row[1].text(0.5, -0.02, f"δθ={dt:+.1f}°", ha="center", va="top",
                       fontsize=7, transform=ax_row[1].transAxes)
        ax_row[2].text(0.5, -0.02, f"θ_pre={theta_pre:.1f}°  |r|={abs(resid):.2f}",
                       ha="center", va="top", fontsize=7, transform=ax_row[2].transAxes)
        for a in ax_row:
            a.set_xticks([]); a.set_yticks([])
            a.set_xlim(0, 1); a.set_ylim(0, 1)
            for sp in a.spines.values():
                sp.set_edgecolor("black"); sp.set_linewidth(0.5)

    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  → {out_path}")


def load_variant_optimum(variant_tag: str, subject: str) -> dict:
    """Load optimum from variant's summary JSON (handles inconsistent key names)."""
    fp = OUTDIR_BASE / f'{subject}_V4_{variant_tag}_summary.json'
    if not fp.exists():
        return None
    with open(fp) as f:
        d = json.load(f)
    for key in ('best_by_l_fit', 'best'):
        if key in d:
            return d[key]
    return None


def main():
    # All variants in unified naming (post-reorg 2026-05-11)
    variants = [
        ('simplified', 'OLD simplified L_fit'),
        ('4term',      'OLD 4-term L_fit'),
        ('V1demeaned', 'V1 Demeaned MSE'),
        ('V2pearson',  'V2 +Pearson r'),
        ('V3rankw03',  'V3 β=0.3'),
        ('V3rankw02',  'V3 β=0.2'),
        ('V4ccc',      'V4 CCC'),
    ]

    for subject_id in ['sub-08', 'sub-09']:
        sub_lbl = 'deutan' if subject_id == 'sub-08' else 'protan'
        for vtag, vlbl in variants:
            best = load_variant_optimum(vtag, subject_id)
            if best is None:
                continue
            out_path = OUTDIR_BASE / f'4col_{subject_id}_V4_{vtag}.png'
            extra = ''
            if 'rdm_cosine' in best:
                extra = f'  rdm_cos={best["rdm_cosine"]:.3f}'
            render_filter(best['bs'], best['bc'],
                          f'{subject_id} ({sub_lbl}) — {vlbl}',
                          f'β_s={best["bs"]:.0f}°, β_c={best["bc"]:+.0f}°  '
                          f'ρ={best["spearman_r"]:.3f}  '
                          f'L_fit={best["l_fit"]:.4f}{extra}',
                          out_path)


if __name__ == '__main__':
    main()
