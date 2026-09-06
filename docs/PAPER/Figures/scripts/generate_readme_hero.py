#!/usr/bin/env python3
"""
generate_readme_hero.py — pipeline banner for the repository README and for the
project homepage.

The banner is the analysis pipeline of Figure 1 panel C, re-cut for a landing
page: the manuscript panel starts at Stage A (Alignment) because acquisition is
covered by Figure 1 panels A and B, but a landing image has no such context, so
acquisition is drawn as its own first stage and the three manuscript stages
follow.  Stages are numbered 1-4 rather than lettered A-C, since the letters
only mean something next to the manuscript panel.

    1  Acquisition      the eight-hue stimulus set entering the scanner
    2  Alignment        Figure 1 stage A glyph
    3  Neural features  Figure 1 stage B glyphs (LORO / LOCO / RDM)
    4  Model and filter Figure 1 stage C glyphs

Two layouts are produced from the same drawing code:

    1x4   assets/readme_pipeline.png   a wide strip for the README header
    2x2   assets/pipeline_2x2.png      a squarer block for the homepage

Colors and the STIM_LAB swatch values are imported from generate_fig1_v3, so
the banner cannot drift from the manuscript figure.

Fonts: run with MATPLOTLIBRC pointed at Figures/scripts/inrc (see FONT_POLICY.md).

    export MATPLOTLIBRC="<repo>/docs/PAPER/Figures/scripts/inrc"
    python3 generate_readme_hero.py            # both layouts
    python3 generate_readme_hero.py 2x2        # one of them
"""
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_fig1_v3 import MEASURED_LAB, lab_to_srgb, stim_rgb  # noqa: E402

REPO = Path(__file__).resolve().parents[4]
ASSETS = REPO / "assets"

HUES = np.arange(0, 360, 45)
SUB = "0.35"

STAGES = [
    ("1 · Acquisition",      "#3f4a56", "8 hues, RSVP, six runs"),
    ("2 · Alignment",        "#1f4e79", "per-run patterns → control-trained shared space"),
    ("3 · Neural features",  "#1e6b52", "classification, interpolation, geometry"),
    ("4 · Model and filter", "#a33a2b", "fitted rotation → per-person stimulus filter"),
]

LAYOUTS = {
    "1x4": dict(out="readme_pipeline.png", figsize=(12.0, 2.55), grid=(1, 4),
                title_fs=14.5, cap_fs=8.8, tag_fs=7.4, hdr=17.0, margin=1.6,
                gh_frac=0.62),
    "2x2": dict(out="pipeline_2x2.png", figsize=(8.6, 4.9), grid=(2, 2),
                title_fs=16.5, cap_fs=9.8, tag_fs=8.0, hdr=10.2, margin=1.6,
                gh_frac=0.74),
}

# Every glyph is drawn in one fixed coordinate box, x in [-HALF_X, HALF_X] and
# y in [-1, 1], and the inset is sized to that ratio in both layouts, so the
# two banners differ in scale only and never in proportion.
HALF_X = 2.1


# ─── drawing helpers ──────────────────────────────────────────────────────────
def _inset(ax, cx, cy, h_frac_max, w_frac_max):
    """Inset centred at (cx, cy), as large as the box allows at HALF_X:1."""
    fig = ax.get_figure()
    fw, fh = fig.get_figwidth(), fig.get_figheight()
    h_in = min(h_frac_max * fh, w_frac_max * fw / HALF_X)
    w_in = h_in * HALF_X
    w_frac, h_frac = w_in / fw, h_in / fh
    sub = ax.inset_axes([cx - w_frac / 2, cy - h_frac / 2, w_frac, h_frac],
                        transform=ax.transAxes)
    sub.set_xlim(-HALF_X, HALF_X)
    sub.set_ylim(-1.0, 1.0)
    sub.set_aspect("equal")
    sub.axis("off")
    return sub


def _ring(sub, cx, r, rgbs, ghost_rot=None, skip=None, s=16, cy=0.0):
    sub.add_patch(Circle((cx, cy), r, fill=False, ec="0.85", lw=0.7))
    if ghost_rot is not None:
        for h, rgb in zip(HUES, rgbs):
            a = np.radians(h + ghost_rot)
            sub.scatter(cx + r * np.cos(a), cy + r * np.sin(a), s=s,
                        facecolors="none", edgecolors=[rgb], linewidths=0.8)
    for h, rgb in zip(HUES, rgbs):
        a = np.radians(h)
        x, y = cx + r * np.cos(a), cy + r * np.sin(a)
        if skip is not None and h == skip:
            sub.scatter(x, y, s=s + 4, facecolors="none", edgecolors="0.35",
                        linewidths=0.8, linestyle="--")
            continue
        sub.scatter(x, y, s=s, c=[rgb], edgecolors="0.3", linewidths=0.4)


def _arrow(sub, x0, x1, y=0.0, scale=7):
    sub.add_patch(FancyArrowPatch((x0, y), (x1, y), arrowstyle="-|>",
                                  mutation_scale=scale, lw=1.1, color="0.45"))


# ─── stage glyphs ─────────────────────────────────────────────────────────────
def glyph_acquisition(sub, rgbs, tag_fs):
    """The eight-hue stimulus set, then the participant in the scanner."""
    sw, gp = 0.30, 0.055
    px, py = -1.34, 0.0
    for i, rgb in enumerate(rgbs):
        col, row = i % 4, i // 4
        x = px - 2 * (sw + gp) + col * (sw + gp) + gp / 2
        y = py + (sw + gp) / 2 - row * (sw + gp)
        sub.add_patch(plt.Rectangle((x, y - sw), sw, sw, fc=rgb, ec="0.35",
                                    lw=0.5))
    _arrow(sub, -0.50, -0.10)

    cx = 1.15
    sub.add_patch(Circle((cx, 0), 0.78, fc="#e8ebee", ec="0.55", lw=0.9))
    sub.add_patch(Circle((cx, 0), 0.42, fc="white", ec="0.55", lw=0.9))
    sub.add_patch(plt.Rectangle((cx - 0.40, -0.125), 1.12, 0.105, fc="0.86",
                                ec="0.5", lw=0.6, zorder=3))
    sub.add_patch(Circle((cx, 0.06), 0.21, fc="0.78", ec="0.35", lw=0.8,
                         zorder=4))


def glyph_alignment(sub, rgbs, tag_fs):
    _ring(sub, -1.05, 0.60, rgbs, ghost_rot=24.0)
    _arrow(sub, -0.30, 0.30)
    _ring(sub, 1.05, 0.60, rgbs)


def glyph_neural(sub, rgbs, tag_fs):
    gy, ty, dx = 0.18, -0.78, 1.35

    n_runs, row_h, row_gap, width = 6, 0.105, 0.035, 1.05
    seg_w = width / 8
    y_top = gy + (n_runs * (row_h + row_gap)) / 2
    for rr in range(n_runs):
        yb = y_top - (rr + 1) * (row_h + row_gap)
        held = rr == 0
        xoff = 0.14 if held else 0.0
        for k, rgb in enumerate(rgbs):
            sub.add_patch(plt.Rectangle((-dx - width / 2 + xoff + k * seg_w, yb),
                                        seg_w, row_h, fc=rgb, ec="none",
                                        alpha=0.55 if held else 1.0))
        sub.add_patch(plt.Rectangle((-dx - width / 2 + xoff, yb), width, row_h,
                                    fill=False, ec="0.25", lw=0.6,
                                    linestyle="--" if held else "-"))

    _ring(sub, 0.0, 0.44, rgbs, skip=225, s=13, cy=gy)
    aa = np.radians(235.0)
    sub.add_patch(FancyArrowPatch((0, gy), (0.32 * np.cos(aa), gy + 0.32 * np.sin(aa)),
                                  arrowstyle="-|>", mutation_scale=5, lw=1.0,
                                  color="0.2"))

    def pair(y, i, j, w):
        sub.scatter([dx - w, dx + w], [y, y], s=22, c=[rgbs[i], rgbs[j]],
                    edgecolors="0.3", linewidths=0.4, zorder=5)
        sub.add_patch(FancyArrowPatch((dx - w + 0.11, y), (dx + w - 0.11, y),
                                      arrowstyle="<|-|>", mutation_scale=4,
                                      lw=0.8, color="0.3"))
    pair(gy + 0.26, 0, 1, 0.30)
    pair(gy - 0.26, 0, 4, 0.54)

    for x, name in ((-dx, "LORO"), (0.0, "LOCO"), (dx, "RDM")):
        sub.text(x, ty, name, fontsize=tag_fs, color=SUB, ha="center",
                 va="center")


def glyph_model(sub, rgbs, tag_fs):
    _ring(sub, -1.30, 0.52, rgbs, s=14)
    for h0, dd in ((90.0, -34.0), (180.0, -30.0), (315.0, 28.0)):
        a0, a1 = np.radians(h0), np.radians(h0 + dd)
        rr = 0.70
        sub.add_patch(FancyArrowPatch((-1.30 + rr * np.cos(a0), rr * np.sin(a0)),
                                      (-1.30 + rr * np.cos(a1), rr * np.sin(a1)),
                                      connectionstyle=f"arc3,rad={0.22 if dd > 0 else -0.22}",
                                      arrowstyle="-|>", mutation_scale=6,
                                      lw=1.0, color="0.2"))
    _arrow(sub, -0.55, -0.15)
    for i, k in enumerate((1, 3, 6)):
        xc = 0.45 + i * 0.62
        L0, a0, b0 = MEASURED_LAB[k]
        sub.add_patch(plt.Rectangle((xc - 0.22, 0.10), 0.44, 0.42,
                                    fc=lab_to_srgb(L0, a0, b0), ec="0.4", lw=0.5))
        ch = float(np.hypot(a0, b0))
        hp = np.degrees(np.arctan2(b0, a0)) - 28.0
        sub.add_patch(plt.Rectangle((xc - 0.22, -0.52), 0.44, 0.42,
                                    fc=lab_to_srgb(L0, ch * np.cos(np.radians(hp)),
                                                   ch * np.sin(np.radians(hp))),
                                    ec="0.4", lw=0.5))
        sub.add_patch(FancyArrowPatch((xc, 0.07), (xc, -0.07), arrowstyle="-|>",
                                      mutation_scale=4, lw=0.8, color="0.35"))


GLYPHS = [glyph_acquisition, glyph_alignment, glyph_neural, glyph_model]


# ─── assemble ─────────────────────────────────────────────────────────────────
def render(name):
    cfg = LAYOUTS[name]
    nrow, ncol = cfg["grid"]
    rgbs = stim_rgb()

    fig = plt.figure(figsize=cfg["figsize"])
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    m, gap = cfg["margin"], 3.0
    bw = (100 - 2 * m - (ncol - 1) * gap) / ncol
    bh = (100 - 2 * m - (nrow - 1) * gap) / nrow
    hdr = cfg["hdr"]

    for idx, ((title, col, cap), draw) in enumerate(zip(STAGES, GLYPHS)):
        r, c = divmod(idx, ncol)
        x = m + c * (bw + gap)
        y = 100 - m - (r + 1) * bh - r * gap

        ax.add_patch(FancyBboxPatch((x, y), bw, bh,
                                    boxstyle="round,pad=0.4,rounding_size=1.4",
                                    fc="white", ec=col, lw=1.1, zorder=2))
        ax.add_patch(FancyBboxPatch((x, y + bh - hdr), bw, hdr,
                                    boxstyle="round,pad=0.4,rounding_size=1.4",
                                    fc=col, ec=col, lw=1.1, zorder=3))
        ax.text(x + bw / 2, y + bh - hdr / 2, title, fontsize=cfg["title_fs"],
                fontweight="bold", ha="center", va="center", color="white",
                zorder=4)

        # glyph and caption as one group, centred in the body of the box
        body_top, body_bot = y + bh - hdr, y
        gh = (bh - hdr) * cfg["gh_frac"]             # glyph height, data units
        cap_h, pad = 4.6, 2.4
        block = gh + pad + cap_h
        top = (body_top + body_bot) / 2 + block / 2
        gy = top - gh / 2
        sub = _inset(ax, (x + bw / 2) / 100, gy / 100,
                     gh / 100, (bw * 0.92) / 100)
        draw(sub, rgbs, cfg["tag_fs"])
        ax.text(x + bw / 2, top - gh - pad - cap_h / 2, cap,
                fontsize=cfg["cap_fs"], color=SUB, ha="center", va="center")

    if name == "1x4":
        for k in range(3):
            xa = m + (k + 1) * bw + k * gap
            ax.add_patch(FancyArrowPatch((xa + 0.4, 50 - 2), (xa + gap - 0.4, 50 - 2),
                                         arrowstyle="-|>", mutation_scale=10,
                                         lw=1.3, color="0.35", zorder=5))

    ASSETS.mkdir(parents=True, exist_ok=True)
    out = ASSETS / cfg["out"]
    fig.savefig(out, dpi=200, facecolor="white")
    print("saved:", out)
    plt.close(fig)


if __name__ == "__main__":
    names = sys.argv[1:] or list(LAYOUTS)
    for n in names:
        render(n)
