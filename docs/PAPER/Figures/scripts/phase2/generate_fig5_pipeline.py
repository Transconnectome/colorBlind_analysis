"""Figure 5 — Inverse-problem workflow for stimulus-space filter design.

Publication SCHEMATIC (2026-06-05). NO fitted/empirical data is plotted here;
all glyphs are illustrative. The real loss landscape is Figure 6.

Sized for apa6 single-column \\textwidth = 6.27 in: native width ~9.2 in renders
at ~0.68x, keeping all type at >= ~6 pt.

Five-stage horizontal flow:
  1. Forward distortion model   delta-theta(theta; beta_s, beta_c)
  2. Three loss families        behavioural JND (gamma) | neural RDM | hV4 LOCO
  3. Grid search over (bs,bc)   argmin of the z-scored composite
  4. Pre-image inversion        solve forward(theta_pre) = theta
  5. Per-subject filter         delta-theta_filter(theta)

Output: docs/PAPER/Figures/fig5_pipeline.{pdf,png}
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT = Path(__file__).resolve().parents[2]

matplotlib.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
    "pdf.fonttype": 42, "ps.fonttype": 42,
})

# font sizes (native; rendered ~0.68x at \textwidth)
F_SUP, F_TITLE, F_EQ, F_LOSS, F_SMALL, F_FOOT = 13.5, 12.0, 10.0, 9.5, 8.8, 9.0

C_MODEL = "#3a5f8a"; C_LOSS = "#2e7d5b"; C_FIT = "#9c6b1f"; C_FILT = "#a33b3b"
INK = "#1a1a1a"


def stage_box(ax, x, y, w, h, color, title):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                 boxstyle="round,pad=0.012,rounding_size=0.02",
                 linewidth=1.4, edgecolor=color, facecolor=color + "14", zorder=1))
    ax.text(x + w / 2, y + h - 0.03, title, ha="center", va="top",
            fontsize=F_TITLE, fontweight="bold", color=color, zorder=5)


def arrow(ax, x0, x1, y):
    ax.add_patch(FancyArrowPatch((x0, y), (x1, y), arrowstyle="-|>",
                 mutation_scale=15, linewidth=1.7, color=INK, zorder=4))


def main():
    fig, ax = plt.subplots(figsize=(9.2, 3.5))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    W = 0.183; H = 0.72; Y = 0.14
    xs = [0.008, 0.206, 0.404, 0.602, 0.800]

    # ── Stage 1: forward distortion model ────────────────────────────────────
    x = xs[0]; stage_box(ax, x, Y, W, H, C_MODEL, "1 · Forward model")
    gx = x + 0.016; gw = W - 0.032
    cx = np.linspace(0, 1, 100)
    curve = 0.5 + 0.18 * np.cos(2 * np.pi * cx) + 0.07 * np.cos(2 * np.pi * cx - 1.0)
    ax.plot(gx + cx * gw, Y + 0.15 + (curve - 0.5) * 0.40, color=C_MODEL, lw=1.7,
            zorder=3)
    ax.plot([gx, gx + gw], [Y + 0.15, Y + 0.15], color="0.7", lw=0.5, ls=":",
            zorder=2)
    ax.text(x + W / 2, Y + 0.45,
            r"$\delta\theta = \beta_s\cos(\theta-90°)$" + "\n" +
            r"$\;+\,\beta_c\cos(\theta-\theta_{\rm conf})$",
            ha="center", va="center", fontsize=F_EQ, color=INK, zorder=5)
    ax.text(x + W / 2, Y + 0.045, "parameterised\ndistortion field", ha="center",
            va="center", fontsize=F_SMALL, color="0.4", zorder=3)

    # ── Stage 2: three loss families ─────────────────────────────────────────
    x = xs[1]; stage_box(ax, x, Y, W, H, C_LOSS, "2 · Loss families")
    rows = [("Behavioural JND", r"$\gamma_{\rm focal},\,\gamma_{\rm all}$"),
            ("Neural RDM cosine", r"$L_{\rm RDM}$"),
            ("hV4 forward LOCO", r"$L_{\rm LOCO}$")]
    for r, (name, sym) in enumerate(rows):
        yy = Y + 0.50 - r * 0.150
        ax.add_patch(plt.Rectangle((x + 0.018, yy - 0.016), 0.018, 0.032,
                     color=C_LOSS, zorder=3))
        ax.text(x + 0.046, yy + 0.022, name, ha="left", va="center",
                fontsize=F_LOSS, color=INK, zorder=3)
        ax.text(x + 0.046, yy - 0.028, sym, ha="left", va="center",
                fontsize=F_LOSS, color=C_LOSS, zorder=3)
    ax.text(x + W / 2, Y + 0.045, "observed CVD\nvs HC differences", ha="center",
            va="center", fontsize=F_SMALL, color="0.4", zorder=3)

    # ── Stage 3: grid search → argmin (schematic bowl) ───────────────────────
    x = xs[2]; stage_box(ax, x, Y, W, H, C_FIT, "3 · Grid search")
    gx0, gy0, gw2, gh2 = x + 0.030, Y + 0.24, W - 0.060, 0.34
    u = np.linspace(-1, 1, 60); v = np.linspace(-1, 1, 60)
    U, V = np.meshgrid(u, v)
    Z = (U + 0.25) ** 2 + (V - 0.2) ** 2
    Xp = gx0 + (U + 1) / 2 * gw2; Yp = gy0 + (V + 1) / 2 * gh2
    ax.contourf(Xp, Yp, Z, levels=8, cmap="viridis_r", zorder=2)
    ax.contour(Xp, Yp, Z, levels=6, colors="white", alpha=0.35, linewidths=0.4,
               zorder=3)
    ax.plot(gx0 + (-0.25 + 1) / 2 * gw2, gy0 + (0.2 + 1) / 2 * gh2, marker="*",
            ms=12, color="#d62728", mec="white", mew=0.8, zorder=4)
    ax.add_patch(plt.Rectangle((gx0, gy0), gw2, gh2, fill=False, edgecolor=C_FIT,
                 linewidth=1.0, zorder=4))
    ax.text(x + W / 2, Y + 0.115,
            r"$\hat\beta=\arg\min_{\beta_s,\beta_c} L_{\rm comp}$",
            ha="center", va="center", fontsize=F_EQ, color=INK, zorder=5)

    # ── Stage 4: pre-image inversion ─────────────────────────────────────────
    x = xs[3]; stage_box(ax, x, Y, W, H, C_FIT, "4 · Pre-image")
    cx = np.linspace(0, 1, 100); fwd = cx + 0.16 * np.sin(2 * np.pi * cx)
    ax.plot(x + 0.026 + cx * (W - 0.052), Y + 0.32 + (fwd - 0.5) * 0.38,
            color=C_FIT, lw=1.7, zorder=3)
    ax.plot([x + 0.026, x + W - 0.026], [Y + 0.32, Y + 0.32], color="0.7",
            lw=0.5, ls=":", zorder=2)
    ax.text(x + W / 2, Y + 0.60, "invert the\nforward map", ha="center",
            va="center", fontsize=F_SMALL, color="0.4", zorder=3)
    ax.text(x + W / 2, Y + 0.115,
            r"$\theta_{\rm pre}+\delta\theta(\theta_{\rm pre})=\theta$",
            ha="center", va="center", fontsize=F_EQ, color=INK, zorder=5)

    # ── Stage 5: per-subject filter ──────────────────────────────────────────
    x = xs[4]; stage_box(ax, x, Y, W, H, C_FILT, "5 · Stimulus filter")
    sw = 0.045
    ax.add_patch(plt.Rectangle((x + 0.032, Y + 0.42), sw, sw * 1.5,
                 color="#e8568c", ec="0.3", lw=0.5, zorder=3))
    ax.add_patch(plt.Rectangle((x + W - 0.032 - sw, Y + 0.42), sw, sw * 1.5,
                 color="#b07ad6", ec="0.3", lw=0.5, zorder=3))
    ax.add_patch(FancyArrowPatch((x + 0.032 + sw + 0.006, Y + 0.42 + sw * 0.75),
                 (x + W - 0.032 - sw - 0.006, Y + 0.42 + sw * 0.75),
                 arrowstyle="-|>", mutation_scale=10, lw=1.3, color=INK, zorder=4))
    ax.text(x + 0.032 + sw / 2, Y + 0.40, "stim", ha="center", va="top",
            fontsize=F_SMALL - 1, color="0.4")
    ax.text(x + W - 0.032 - sw / 2, Y + 0.40, "filtered", ha="center", va="top",
            fontsize=F_SMALL - 1, color="0.4")
    ax.text(x + W / 2, Y + 0.20,
            r"$\delta\theta_{\rm filter}=\theta_{\rm pre}-\theta$",
            ha="center", va="center", fontsize=F_EQ, color=INK, zorder=5)
    ax.text(x + W / 2, Y + 0.045, "per-subject\ncorrection", ha="center",
            va="center", fontsize=F_SMALL, color="0.4", zorder=3)

    # ── connecting arrows ────────────────────────────────────────────────────
    for a, b in zip(xs[:-1], xs[1:]):
        arrow(ax, a + W + 0.004, b - 0.004, Y + H / 2)

    fig.text(0.5, 0.975,
             "Inverse-problem workflow for personalised stimulus-space filter design",
             ha="center", va="top", fontsize=F_SUP, fontweight="bold")
    fig.text(0.5, 0.035,
             "Schematic — glyphs are illustrative; the fitted loss landscape is Figure 6.",
             ha="center", va="bottom", fontsize=F_FOOT, color="0.45", style="italic")

    fig.subplots_adjust(left=0.005, right=0.995, top=0.99, bottom=0.01)
    for ext in ("pdf", "png"):
        p = OUT / f"fig5_pipeline.{ext}"
        fig.savefig(p, dpi=300, bbox_inches="tight")
        print("saved:", p)
    plt.close(fig)


if __name__ == "__main__":
    main()
