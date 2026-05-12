"""phase3_render_top_candidates.py — render 4-column filter visualizations
for top phase3 candidates using CURRENT formula.

Reuses logic from visualize_filter_candidates.py but parameterized over
arbitrary (β_s, β_c). Renders sub-08 deutan only.

Output: results/phase3_candidates/visualizations/{name}.png
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR))
sys.path.insert(0, str(_THIS_DIR / "forward_models"))
sys.path.insert(0, str(_THIS_DIR / "visualization"))

from forward_models.two_component import forward_2comp, pre_image_2comp
from stim_lab_render import render_at_hue as _render_stim_lab

OUTDIR = _THIS_DIR.parent / "results" / "phase3_candidates" / "visualizations"
OUTDIR.mkdir(parents=True, exist_ok=True)

CVD = "deutan"

TIER1 = [
    (0,   "c1 (red)"),
    (45,  "c2 (orange)"),
    (90,  "c3 (yellow)"),
    (135, "c4 (green)"),
    (180, "c5 (cyan)"),
    (225, "c6 (sky)"),
    (270, "c7 (blue)"),
    (315, "c8 (magenta)"),
]


def render_filter(beta_s: float, beta_c: float, title: str, outpath: Path) -> None:
    n = len(TIER1)
    fig, axes = plt.subplots(n, 4, figsize=(8.5, 0.65 * n + 1.5),
                             gridspec_kw={"hspace": 0.10, "wspace": 0.08})
    fig.suptitle(f"{title}\n2-component  β_s={beta_s}°, β_c={beta_c:+}°  (sub-08 deutan, CURRENT formula)",
                 fontsize=10, y=0.995)
    col_titles = ["Original", "CVD perceives", "Filtered (pre-image)", "CVD(Filtered)"]
    for ax, ct in zip(axes[0], col_titles):
        ax.set_title(ct, fontsize=9)

    for i, (theta, label) in enumerate(TIER1):
        ax_row = axes[i]
        theta_pre, resid = pre_image_2comp(float(theta), CVD, beta_s, beta_c)
        theta_cvd, dt = forward_2comp(float(theta), CVD, beta_s, beta_c)
        theta_cvd_of_pre, _ = forward_2comp(theta_pre, CVD, beta_s, beta_c)

        rgb_orig       = _render_stim_lab(float(theta), dL=0.0)
        rgb_cvd        = _render_stim_lab(theta_cvd, dL=0.0)
        rgb_pre        = _render_stim_lab(theta_pre, dL=0.0)
        rgb_cvd_of_pre = _render_stim_lab(theta_cvd_of_pre, dL=0.0)

        ax_row[0].add_patch(Rectangle((0, 0), 1, 1, color=rgb_orig))
        ax_row[1].add_patch(Rectangle((0, 0), 1, 1, color=rgb_cvd))
        ax_row[2].add_patch(Rectangle((0, 0), 1, 1, color=rgb_pre))
        ax_row[3].add_patch(Rectangle((0, 0), 1, 1, color=rgb_cvd_of_pre))

        ax_row[0].text(-0.05, 0.5, f"{label}\nθ={theta}°",
                       ha="right", va="center", fontsize=7,
                       transform=ax_row[0].transAxes)
        ax_row[1].text(0.5, -0.02, f"δθ={dt:+.1f}°",
                       ha="center", va="top", fontsize=7,
                       transform=ax_row[1].transAxes)
        ax_row[2].text(0.5, -0.02,
                       f"θ_pre={theta_pre:.1f}°  |r|={abs(resid):.2f}°",
                       ha="center", va="top", fontsize=7,
                       transform=ax_row[2].transAxes)

        for a in ax_row:
            a.set_xticks([]); a.set_yticks([])
            a.set_xlim(0, 1); a.set_ylim(0, 1)
            for sp in a.spines.values():
                sp.set_edgecolor("black"); sp.set_linewidth(0.5)

    plt.savefig(outpath, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  → {outpath.name}")


CANDIDATES = [
    # v3 candidates — behavior-anchored loss optimum (β_s ∈ [30,50] physiological constraint)
    {"name": "v3_behav_opt", "beta_s": 34.0, "beta_c": 2.0,
     "title": "v3 Top 1 (behav-anchored, β_s phys-constrained): NEW optimum"},
    {"name": "v3_behav_v4only", "beta_s": 38.0, "beta_c": 7.0,
     "title": "v3 Top 2 (= V4-only OLD): rank 119/1326 behavior loss"},
    {"name": "v3_behav_soft", "beta_s": 36.0, "beta_c": 4.0,
     "title": "v3 alt (β_s slightly smaller, β_c=+4)"},
    # Reference
    {"name": "ref_canonical",         "beta_s": 38.0, "beta_c": -14.0,
     "title": "Reference: Canonical (behav-loss rank 1028/1326, OLD-loss rank 1/1326)"},
]


def main():
    for c in CANDIDATES:
        render_filter(c["beta_s"], c["beta_c"], c["title"],
                      OUTDIR / f"{c['name']}.png")
    print(f"\nWrote {len(CANDIDATES)} figures to {OUTDIR}")


if __name__ == "__main__":
    main()
