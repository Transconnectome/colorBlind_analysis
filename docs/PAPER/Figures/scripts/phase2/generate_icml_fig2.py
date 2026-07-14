"""ICML SD4H camera-ready Figure 2 — per-subject loss landscape | inverted filter.

Single-column (\\columnwidth) composite that reuses the closure-canonical logic
of generate_fig6_landscape.py and generate_fig7_filter.py, re-laid-out as a
2x2 grid:

    rows = subjects (Sub-08 deutan, Sub-09 protan)
    cols = [ loss landscape over (beta_s, beta_c) | inverted filter strip ]

The filter strip is an 8-hue x 2-row (Original / Filtered) mini-grid; the
Filtered row is the exact stimulus-space pre-image of the fitted 2-Component
transform.  Surfaces, argmin clouds, fits, and rendering are identical to the
paper figures (PIPELINE_2_CLOSURE.md 2026-06-01) -- only the layout changes.

Run from this directory (conda env: srm), needs closure results on disk:
    python generate_icml_fig2.py
Output: docs/ICML_workshop/figures/fig2_landscape_filter.{pdf,png}
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

# Reuse the canonical paper-figure logic (these imports also wire up the
# future_phase2 scripts path and pull in the closure loaders / renderer).
from generate_fig6_landscape import (          # noqa: E402
    CANDIDATES, plot_panel, build_composite_full_hc, load_resample_argmins,
)
from generate_fig7_filter import (             # noqa: E402
    pre_image, HUE_8, HUE_NAMES, SUBJECTS, render_at_hue,
)

# camera-ready figures dir: docs/PAPER/Figures/scripts/phase2 -> docs/ICML_workshop/figures
OUT = HERE.resolve().parents[3] / "ICML_workshop" / "figures"

matplotlib.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
    "font.size": 7, "axes.titlesize": 16,   # landscape subject title 8->16 (2x)
    "pdf.fonttype": 42, "ps.fonttype": 42,
})


def main():
    # ~ single column tall: landscape (square-ish) beside an 8-hue filter strip,
    # one subject per row.
    fig = plt.figure(figsize=(7.6, 5.3))
    outer = fig.add_gridspec(2, 2, width_ratios=[1.0, 1.22],
                             wspace=0.28, hspace=0.42,
                             top=0.90, bottom=0.08, left=0.09, right=0.99)
    im = None
    land_axes = []

    for k in range(2):
        cand = CANDIDATES[k]
        spec = SUBJECTS[k]

        # ---- left: loss landscape (reuse paper plot_panel) -------------------
        ax = fig.add_subplot(outer[k, 0])
        print(f"building landscape {cand['id']} ...", flush=True)
        comp, *_ = build_composite_full_hc(cand)
        bs_s, bc_s = load_resample_argmins(cand)
        im = plot_panel(ax, comp, cand["fit_point"], bs_s, bc_s, cand["title"])
        # tighten labels for the narrow column
        ax.set_xlabel(r"$\beta_c$ (°)", fontsize=10)   # 7->14 (2x)
        ax.set_ylabel(r"$\beta_s$ (°)", fontsize=10)   # 7->14 (2x)
        ax.tick_params(labelsize=12)                    # 6->12 (2x)
        land_axes.append(ax)

        # ---- right: inverted filter strip (8 hues x Original/Filtered) -------
        inner = outer[k, 1].subgridspec(2, 8, wspace=0.10, hspace=0.14)
        fam, bs, bc = spec["family"], spec["beta_s"], spec["beta_c"]
        for c, theta in enumerate(HUE_8):
            theta = float(theta)
            theta_pre = pre_image(theta, fam, bs, bc)
            for r, hue in [(0, theta), (1, theta_pre)]:
                axc = fig.add_subplot(inner[r, c])
                axc.add_patch(Rectangle((0, 0), 1, 1, color=render_at_hue(hue)))
                axc.set_xlim(0, 1); axc.set_ylim(0, 1)
                axc.set_xticks([]); axc.set_yticks([])
                for sp in axc.spines.values():
                    sp.set_edgecolor("0.3"); sp.set_linewidth(0.4)
                if r == 0:
                    axc.set_title("ROYGCBPM"[c], fontsize=6, pad=1.5)
                if c == 0:
                    axc.set_ylabel("Orig" if r == 0 else "Filt", fontsize=12,
                                   rotation=0, ha="right", va="center", labelpad=7)   # 6->12 (2x)
        # subject + params tag, raised clear of the hue-letter row and axes
        pos = outer[k, 1].get_position(fig)
        fig.text(pos.x0 + pos.width / 2, pos.y1 + 0.045,
                 f"{spec['subject']} ({spec['family']}):  "
                 f"$\\beta_s$={bs:+.0f}°, $\\beta_c$={bc:+.0f}°",
                 ha="center", va="bottom", fontsize=14, fontweight="bold")   # 7->14 (2x)

    # shared colorbar for the two landscapes
    cb = fig.colorbar(im, ax=land_axes, shrink=0.94, pad=0.05, aspect=30,
                      location="right")
    cb.set_label("composite loss (z; lower = better)", fontsize=9)
    cb.ax.tick_params(labelsize=8)

    handles = [
        Line2D([0], [0], marker="*", color="none", markerfacecolor="#d62728",
               markeredgecolor="white", markersize=12, label="selected fit"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor="white",
               markeredgecolor="black", markersize=7, label="HC-resample argmins"),
    ]
    land_axes[0].legend(handles=handles, loc="upper left", fontsize=7,
                        framealpha=0.9, handletextpad=0.3, borderpad=0.3)

    OUT.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png"):
        p = OUT / f"fig2_landscape_filter.{ext}"
        fig.savefig(p, dpi=300, bbox_inches="tight")
        print("saved:", p)
    plt.close(fig)


if __name__ == "__main__":
    main()
