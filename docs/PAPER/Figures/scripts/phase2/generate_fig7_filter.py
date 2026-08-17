"""Figure 7 — Per-subject stimulus-space correction filter (wide / landscape).

Publication version (2026-06-05, wide layout). Hues run across as 8 COLUMNS;
each subject is a 2-row block (Original / Filtered). Two subjects stacked.

  columns: 8 scanner hues (Red ... Magenta)
  rows   : [sub-08 Original, sub-08 Filtered, sub-09 Original, sub-09 Filtered]
  Filtered = render_at_hue(theta_pre)  (corrected stimulus = pre-image)
  per-hue filter shift delta-theta = theta_pre - theta annotated on Filtered rows

Canonical 2-Component fits (PIPELINE_2_CLOSURE.md 2026-06-01, A13 raw forward):
  sub-08 deutan  (beta_s=+6,  beta_c=-42)
  sub-09 protan  (beta_s=+2,  beta_c=+24)

Forward / pre-image use canonical scripts/two_comp.py:forward_2comp (A13).
Rendering: STIM_LAB CIELab (stim_lab_render.render_at_hue).
Output: docs/PAPER/Figures/fig7_filter.{pdf,png}
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

_P2_SCRIPTS = (Path(__file__).resolve().parents[5]
               / "analysis" / "phase5_filter_optimization" / "scripts")
sys.path.insert(0, str(_P2_SCRIPTS))
from stim_lab_render import render_at_hue                      # noqa: E402
from two_comp import THETA_CONF                                # noqa: E402

OUT = Path(__file__).resolve().parents[2]

HUE_8 = np.array([0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0])
HUE_NAMES = ["Red", "Orange", "Yellow", "Green", "Cyan", "Blue", "Purple", "Magenta"]

SUBJECTS = [
    dict(label="Sub-08\n(deutan)", subject="sub-08", family="deutan",
         beta_s=6.0, beta_c=-42.0),
    dict(label="Sub-09\n(protan)", subject="sub-09", family="protan",
         beta_s=2.0, beta_c=24.0),
]

matplotlib.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],  # Arial first: IN requires Arial or Helvetica; kept uniform across all figures
    "font.size": 8, "pdf.fonttype": 42, "ps.fonttype": 42,
})


def pre_image(theta_target, family, bs, bc, n_grid=4096):
    grid = np.linspace(0.0, 360.0, n_grid, endpoint=False)
    tc = THETA_CONF[family]
    dt = bs * np.cos(np.deg2rad(grid - 90.0)) + bc * np.cos(np.deg2rad(grid - tc))
    fwd = (grid + dt) % 360.0
    resid = (fwd - theta_target + 180.0) % 360.0 - 180.0
    i = int(np.argmin(np.abs(resid)))
    return float(grid[i])


def main():
    n_sub = len(SUBJECTS)
    nrow = 2 * n_sub            # Original/Filtered per subject
    ncol = 8
    # height ratios: insert a thin spacer row between subject blocks
    fig, axes = plt.subplots(
        nrow, ncol, figsize=(10.2, 4.6),
        gridspec_kw={"wspace": 0.06, "hspace": 0.30},
    )

    row_titles = []
    for k, spec in enumerate(SUBJECTS):
        fam, bs, bc = spec["family"], spec["beta_s"], spec["beta_c"]
        r_orig, r_filt = 2 * k, 2 * k + 1
        for c, theta in enumerate(HUE_8):
            theta = float(theta)
            theta_pre = pre_image(theta, fam, bs, bc)
            dshift = (theta_pre - theta + 180.0) % 360.0 - 180.0
            for r, hue in [(r_orig, theta), (r_filt, theta_pre)]:
                ax = axes[r, c]
                ax.add_patch(Rectangle((0, 0), 1, 1, color=render_at_hue(hue)))
                ax.set_xlim(0, 1); ax.set_ylim(0, 1)
                ax.set_xticks([]); ax.set_yticks([])
                for sp in ax.spines.values():
                    sp.set_edgecolor("0.25"); sp.set_linewidth(0.5)
            # delta-theta beneath each Filtered swatch
            axes[r_filt, c].text(0.5, -0.16, f"{dshift:+.0f}°", ha="center",
                                 va="top", fontsize=7.0, color="0.30",
                                 transform=axes[r_filt, c].transAxes)
        # hue column headers (top row only)
        if k == 0:
            for c, name in enumerate(HUE_NAMES):
                axes[0, c].set_title(name, fontsize=8.2, pad=4)
        # row labels (left)
        axes[r_orig, 0].set_ylabel("Original", fontsize=8.5, rotation=90,
                                   labelpad=6)
        axes[r_filt, 0].set_ylabel("Filtered", fontsize=8.5, rotation=90,
                                   labelpad=6)

    # subject block labels + (beta_s, beta_c) on the far left, spanning 2 rows
    for k, spec in enumerate(SUBJECTS):
        y0 = axes[2 * k + 1, 0].get_position().y0
        y1 = axes[2 * k, 0].get_position().y1
        fig.text(0.012, (y0 + y1) / 2,
                 f"{spec['label']}\n$\\beta_s$={spec['beta_s']:+.0f}°, "
                 f"$\\beta_c$={spec['beta_c']:+.0f}°",
                 ha="left", va="center", fontsize=8.6, fontweight="bold",
                 rotation=90)

    # No suptitle: Elsevier/NeuroImage require the figure title in the caption,
    # not on the illustration itself. The LaTeX caption carries it (fig:filter).
    fig.subplots_adjust(left=0.105, right=0.99, top=0.94, bottom=0.07)
    for ext in ("pdf", "png"):
        p = OUT / f"fig7_filter.{ext}"
        fig.savefig(p, dpi=300, bbox_inches="tight")
        print("saved:", p)
    plt.close(fig)


if __name__ == "__main__":
    main()
