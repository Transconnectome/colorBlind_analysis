#!/usr/bin/env python3
"""
generate_fig1_v3.py — Figure 1 (fig:paradigm) for the Imaging Neuroscience submission.

WHY THIS SCRIPT EXISTS
----------------------
The previous Figure 1 (`fig1_generated_v2.pdf`) was produced with an image-
generation AI and had no generator script, which caused two problems:

  1. Its text was raster/DejaVu, violating the journal requirement that figures
     use Arial or Helvetica.
  2. Its panel B was an AI-rendered brain. Synthetic anatomy in a neuroimaging
     paper invites a credibility question it cannot answer, and it forced the
     AI-tool disclosure to name a figure.

Decision (2026-08-18): drop the brain/ROI panel entirely -- the ROIs are
atlas-defined (Wang et al. 2015) and cited in Methods, so no anatomical panel is
required -- and rebuild the remaining three panels programmatically. Figure 1 is
therefore fully script-generated and contains no AI-produced content.

PANELS
------
  A  Stimulus set: 8 hues in the CIE L*a*b* a*b* plane.
  B  RSVP trial structure, composited from the actual screen captures.
  C  Analysis pipeline: Stage A alignment -> Stage B neural features
     -> Stage C modeling and filter inversion.

PANEL A SHOWS THE NOMINAL SPECIFICATION (L* = 75, chroma = 40, 45 deg spacing),
which is what Methods sec:methods:stimuli and the current caption describe.
It is NOT what the screenshot-derived estimates say. `analysis/utils/
utils_color_decoding.py` COLOR_LAB (== phase5 `stim_lab_render.STIM_LAB`), the
values the filter fitting and physical RDM actually consume, give L* 57.3-74.6,
chroma 41.6-72.6, and hue steps of 29.8-67.6 deg. The repository already records
the distinction (`phase5_filter_optimization/scripts/visualization/_archive/
visualize_cone_shift_colors.py:14,53`: "idealized L*=75/chroma=40" vs "what
subjects saw"). Reconciling the Methods sentence with those estimates is a
manuscript-text decision, tracked as a P0 item in
SUBMISSION_CHECKLIST_IMAGING_NEURO.md; it is deliberately NOT made here, because
a figure must not assert something its own caption and Methods contradict.
If the disclosure is adopted, set SHOW_MEASURED = True below and update the
caption in the same commit.

Fonts: run with MATPLOTLIBRC pointed at Figures/scripts/inrc so Arial is used for
text and for mathtext. See Figures/scripts/FONT_POLICY.md.

    export MATPLOTLIBRC="<repo>/docs/PAPER/Figures/scripts/inrc"
    python3 generate_fig1_v3.py
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch
from PIL import Image

FIGDIR = Path(__file__).resolve().parent.parent
OUT_STEM = FIGDIR / "fig1_paradigm_v3"

# Ratio of panel-B axes width to height on the page, used to keep the square
# screen captures square. Derived from the gridspec below; update together.
PANEL_B_ASPECT = (7.0 * 0.50) / (4.75 * 0.55)

SHOW_MEASURED = False  # see the module docstring before enabling

# Nominal stimulus specification, as described in Methods.
L_NOMINAL = 75.0
C_NOMINAL = 40.0
HUES = np.arange(0, 360, 45)
HUE_NAMES = ["Red", "Orange", "Yellow", "Green", "Cyan", "Blue", "Purple", "Magenta"]

# Screenshot-derived estimates, for the optional second layer only.
MEASURED_LAB = np.array([
    [59.90, 62.69, 3.78], [64.20, 49.20, 45.58], [57.27, 13.06, 41.69],
    [69.08, -55.02, 47.38], [74.61, -41.33, -4.89], [69.14, -11.45, -40.91],
    [60.68, 19.18, -54.13], [60.17, 46.82, -40.31],
])


def lab_to_srgb(L, a, b):
    """CIELab (D65) -> sRGB in [0, 1], clipped. Self-contained on purpose so the
    released figure script has no cross-package dependency."""
    fy = (L + 16.0) / 116.0
    fx = fy + a / 500.0
    fz = fy - b / 200.0

    def finv(t):
        return t ** 3 if t ** 3 > 0.008856 else (t - 16.0 / 116.0) / 7.787

    xn, yn, zn = 0.95047, 1.00000, 1.08883
    X, Y, Z = finv(fx) * xn, finv(fy) * yn, finv(fz) * zn
    r = 3.2406 * X - 1.5372 * Y - 0.4986 * Z
    g = -0.9689 * X + 1.8758 * Y + 0.0415 * Z
    bl = 0.0557 * X - 0.2040 * Y + 1.0570 * Z

    def gamma(c):
        c = max(0.0, min(1.0, c))
        return 1.055 * c ** (1 / 2.4) - 0.055 if c > 0.0031308 else 12.92 * c

    return (gamma(r), gamma(g), gamma(bl))


def stim_rgb():
    out = []
    for h in HUES:
        a = C_NOMINAL * np.cos(np.radians(h))
        b = C_NOMINAL * np.sin(np.radians(h))
        out.append(lab_to_srgb(L_NOMINAL, a, b))
    return out


# ─── Panel A ──────────────────────────────────────────────────────────────────
def panel_a(ax):
    lim = 78
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_aspect("equal")

    for r in (20, 40, 60):
        ax.add_patch(Circle((0, 0), r, fill=False, ec="0.85", lw=0.5, zorder=0))
    ax.axhline(0, color="0.85", lw=0.5, zorder=0)
    ax.axvline(0, color="0.85", lw=0.5, zorder=0)

    rgbs = stim_rgb()
    for h, name, rgb in zip(HUES, HUE_NAMES, rgbs):
        x = C_NOMINAL * np.cos(np.radians(h))
        y = C_NOMINAL * np.sin(np.radians(h))
        ax.add_patch(Circle((x, y), 7.2, fc=rgb, ec="0.35", lw=0.5, zorder=3))
        lx = 62 * np.cos(np.radians(h))
        ly = 62 * np.sin(np.radians(h))
        ax.text(lx, ly, f"{h}°", fontsize=6, ha="center", va="center",
                color="0.35", zorder=4,
                bbox=dict(boxstyle="square,pad=0.12", fc="white", ec="none"))

    if SHOW_MEASURED:
        ax.scatter(MEASURED_LAB[:, 1], MEASURED_LAB[:, 2], s=14, facecolors="none",
                   edgecolors="0.2", lw=0.7, zorder=5, label="screenshot estimate")
        ax.legend(fontsize=5.5, loc="lower left", frameon=False)

    ax.set_xlabel("$a^{*}$", fontsize=7.5, labelpad=1)
    ax.set_ylabel("$b^{*}$", fontsize=7.5, labelpad=1)
    ax.tick_params(labelsize=6, length=2.5)
    ax.set_xticks([-60, -30, 0, 30, 60])
    ax.set_yticks([-60, -30, 0, 30, 60])
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


# ─── Panel B ──────────────────────────────────────────────────────────────────
def panel_b(ax):
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    frames = [
        ("rsvp_fix.png", "Fixation\n3–6 s"),
        ("rsvp_stim_red.png", "Colored disc\n1.5 s"),
        ("rsvp_stim_kblack.png", "Letter stream\n1-back on K"),
    ]
    # Fractions of the panel axes; each capture gets its own square inset so the
    # disc cannot be stretched.
    side, gap, y0 = 0.285, 0.075, 0.30
    x = 0.035
    for fname, label in frames:
        # Height compensates for the panel's non-square shape so the capture,
        # and therefore the disc, stays square on the page.
        sub = ax.inset_axes([x, y0, side, side * PANEL_B_ASPECT],
                            transform=ax.transAxes)
        img = np.asarray(Image.open(FIGDIR / fname).convert("RGB"))
        sub.imshow(img, aspect="equal")
        sub.set_xticks([])
        sub.set_yticks([])
        for sp in sub.spines.values():
            sp.set_edgecolor("0.4")
            sp.set_linewidth(0.6)
        ax.text(x + side / 2, y0 - 0.04, label, transform=ax.transAxes,
                fontsize=6.2, ha="center", va="top", color="0.2", linespacing=1.35)
        x += side + gap

    for k in range(2):
        xa = 0.035 + (k + 1) * side + k * gap
        ymid = y0 + side * PANEL_B_ASPECT / 2
        ax.annotate("", xy=(xa + gap - 0.012, ymid),
                    xytext=(xa + 0.012, ymid),
                    xycoords=ax.transAxes, textcoords=ax.transAxes,
                    arrowprops=dict(arrowstyle="-|>", lw=0.9, color="0.3",
                                    mutation_scale=8))
    ax.text(0.5, y0 + side * PANEL_B_ASPECT + 0.045,
            "72 events per run · 6 runs · ISI 3 / 4.5 / 6 s",
            transform=ax.transAxes, fontsize=6, ha="center", va="bottom", color="0.3")


# ─── Panel C ──────────────────────────────────────────────────────────────────
def panel_c(ax):
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    stages = [
        ("Stage A · Alignment", [
            "Two-stage GLM: one amplitude\nper color per run",
            "Procrustes rotation across runs",
            "SRM space trained on controls only",
        ], "#1f4e79"),
        ("Stage B · Neural features", [
            "LORO — color classification",
            "LOCO — hue interpolation",
            "RDM — representational geometry",
        ], "#1e6b52"),
        ("Stage C · Model and filter", [
            "2-component cortical model",
            "($\\beta_s$ S-cone axis, $\\beta_c$ confusion axis)",
            "Pre-image inversion",
            "Per-subject stimulus-space filter",
        ], "#a33a2b"),
    ]

    bw, bgap, by, bh = 29.7, 4.3, 6.0, 88.0
    hdr = 13.0
    x = 0.7
    for title, items, col in stages:
        ax.add_patch(FancyBboxPatch((x, by), bw, bh, boxstyle="round,pad=0.6,rounding_size=1.5",
                                    fc="white", ec=col, lw=1.0, zorder=2))
        ax.add_patch(FancyBboxPatch((x, by + bh - hdr), bw, hdr,
                                    boxstyle="round,pad=0.6,rounding_size=1.5",
                                    fc=col, ec=col, lw=1.0, zorder=3))
        ax.text(x + bw / 2, by + bh - hdr / 2, title, fontsize=7.0, fontweight="bold",
                ha="center", va="center", color="white", zorder=4)

        # One slot per item, evenly filling the body, so the box is never
        # top-packed above empty space.
        body_top, body_bot = by + bh - hdr - 4.0, by + 4.0
        n = len(items)
        slot = (body_top - body_bot) / n
        for i, it in enumerate(items):
            ytop = body_top - i * slot - 1.0
            ax.text(x + 2.2, ytop, "•", fontsize=6.2, ha="left", va="top",
                    color=col, zorder=4)
            ax.text(x + 5.0, ytop, it, fontsize=6.2, ha="left", va="top",
                    color="0.15", zorder=4, linespacing=1.35)
        x += bw + bgap

    for k in range(2):
        xa = 0.7 + (k + 1) * bw + k * bgap
        ax.add_patch(FancyArrowPatch((xa + 0.6, by + bh / 2), (xa + bgap - 0.6, by + bh / 2),
                                    arrowstyle="-|>", mutation_scale=8,
                                    lw=1.0, color="0.35", zorder=5))


# ─── Assemble ─────────────────────────────────────────────────────────────────
def main():
    fig = plt.figure(figsize=(7.0, 4.75))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 0.62],
                          width_ratios=[0.88, 1.12],
                          left=0.075, right=0.985, top=0.935, bottom=0.035,
                          wspace=0.20, hspace=0.42)

    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    ax_c = fig.add_subplot(gs[1, :])

    panel_a(ax_a)
    panel_b(ax_b)
    panel_c(ax_c)

    for ax, letter in ((ax_a, "A"), (ax_b, "B"), (ax_c, "C")):
        ax.text(-0.02, 1.07, letter, transform=ax.transAxes, fontsize=10,
                fontweight="bold", ha="left", va="bottom")

    fig.savefig(f"{OUT_STEM}.pdf", dpi=300)
    fig.savefig(f"{OUT_STEM}.png", dpi=300)
    print(f"Saved: {OUT_STEM}.pdf")
    print(f"Saved: {OUT_STEM}.png")


if __name__ == "__main__":
    main()
