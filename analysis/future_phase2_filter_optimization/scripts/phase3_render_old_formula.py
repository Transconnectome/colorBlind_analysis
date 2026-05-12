"""phase3_render_old_formula.py — render OLD-formula filter candidates.

Uses CIElab-direct (OLD) formula for δθ:
    dt = β_s · cos(θ − 90°) + β_c · cos(θ − 150°)

Same display path (stim_lab_render → sRGB) as CURRENT formula viz.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR))
sys.path.insert(0, str(_THIS_DIR / "visualization"))

from stim_lab_render import render_at_hue as _render_stim_lab

OUTDIR = _THIS_DIR.parent / "results" / "phase3_candidates" / "old_formula_viz"
OUTDIR.mkdir(parents=True, exist_ok=True)

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
    """Solve forward_old(θ) = target via fine grid search."""
    grid = np.linspace(0.0, 360.0, n_grid, endpoint=False)
    forwards = np.array([forward_old(t, beta_s, beta_c)[0] for t in grid])
    diff = (forwards - target_deg + 180.0) % 360.0 - 180.0
    i_min = int(np.argmin(np.abs(diff)))
    return float(grid[i_min]), float(diff[i_min])


def render_filter(beta_s, beta_c, title, outpath):
    n = len(TIER1)
    fig, axes = plt.subplots(n, 4, figsize=(8.5, 0.65 * n + 1.5),
                             gridspec_kw={"hspace": 0.10, "wspace": 0.08})
    fig.suptitle(f"{title}\nOLD 2-component  β_s={beta_s}°, β_c={beta_c:+}°  "
                 f"(θ_conf=150°, CIELab-direct)",
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

    plt.savefig(outpath, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  → {outpath.name}")


CANDIDATES = [
    # sub-08 V4 OLD §3-primary
    {"name": "old_sub08_V4_primary", "bs": 10.0, "bc": -32.0,
     "title": "sub-08 V4 OLD §3-primary (L_fit argmin, ρ=0.833)"},
    # sub-08 V4 OLD P2a-best (positive β_c outlier in top 10)
    {"name": "old_sub08_V4_p2a_top", "bs": 40.0, "bc": +26.0,
     "title": "sub-08 V4 OLD top10/P2a-best (ρ=0.690, P2a=0.575 4/8)"},
    # V4-only OLD (behavioral PASS under OLD rendering)
    {"name": "old_sub08_V4_behavPASS", "bs": 38.0, "bc": +7.0,
     "title": "sub-08 V4-only OLD (raw_behav P1=2+3p/8) — rank 619/1326 by L_fit"},
    # sub-08 V1 OLD §3-primary (edge degenerate)
    {"name": "old_sub08_V1_primary", "bs": 50.0, "bc": +50.0,
     "title": "sub-08 V1 OLD §3-primary GRID-EDGE (50, +50), ρ=0.762"},
    # sub-09 V4 OLD §3-primary
    {"name": "old_sub09_V4_primary", "bs": 30.0, "bc": +46.0,
     "title": "sub-09 V4 OLD §3-primary (ρ=0.500 weak)"},
]


def main():
    for c in CANDIDATES:
        render_filter(c["bs"], c["bc"], c["title"],
                      OUTDIR / f"{c['name']}.png")
    print(f"\nWrote {len(CANDIDATES)} figures to {OUTDIR}")


if __name__ == "__main__":
    main()
