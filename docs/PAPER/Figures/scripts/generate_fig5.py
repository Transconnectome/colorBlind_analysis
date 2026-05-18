"""
Figure 5 — Per-subject stimulus-space filter, 4-column rendering, side-by-side.
================================================================================
Layout: one figure with two 4-column blocks placed horizontally
        (sub-08 left, sub-09 right). Behavioural-validation panels deferred
        to a later revision once the 2AFC Phase-3 arm is complete.

Per-subject 4 columns (left → right):
    1. Original              — HC percept of the displayed stimulus
    2. CVD perceives         — simulated CVD percept of the original
    3. Filtered (pre-image)  — stimulus after applying δθ_filter
    4. CVD(Filtered)         — simulated CVD percept of the filtered stimulus

Parameters: Option C BEST argmins from
    analysis/future_phase2_filter_optimization/results/SUMMARY.md (2026-05-13)
        sub-08 deutan : (β_s, β_c) = (40°, +26°), axis 150°
        sub-09 protan : (β_s, β_c) = (12°, −28°), axis 16°

Forward map + Brent pre-image + STIM_LAB rendering imported from the
analysis package (stim_lab_render.render_at_hue).
"""
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT    = Path("/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/"
               "Projects/colorBlind_analysis")
SCRIPTS = ROOT / "analysis/future_phase2_filter_optimization/scripts"
OUT     = ROOT / "docs/PAPER/Figures"

sys.path.insert(0, str(SCRIPTS))
from stim_lab_render import render_at_hue as _render_stim_lab  # noqa: E402

# ── Stimuli + Option C BEST parameters ───────────────────────────────────────
HUE_8        = [0, 45, 90, 135, 180, 225, 270, 315]
COLOR_LABELS = ["red", "orange", "yellow", "green",
                "cyan", "blue", "purple", "magenta"]

SUBJECTS = [
    dict(sid="08", family="deutan", axis=150.0, bs=40.0, bc=+26.0,
         color="#E07B2C"),
    dict(sid="09", family="protan", axis=16.0,  bs=12.0, bc=-28.0,
         color="#2D8E8B"),
]
COL_TITLES = ["Original", "CVD percept",
              "Filtered", "CVD(Filt.)"]


# ── 2-component model ────────────────────────────────────────────────────────
def dt_2comp(theta, bs, bc, axis):
    th = np.deg2rad(theta)
    return bs * np.cos(th - np.pi/2) + bc * np.cos(th - np.deg2rad(axis))


def forward(theta, bs, bc, axis):
    dt = dt_2comp(theta, bs, bc, axis)
    return (theta + dt) % 360.0, dt


def pre_image(target, bs, bc, axis, n=3600):
    grid = np.linspace(0, 360, n, endpoint=False)
    fwd  = (grid + dt_2comp(grid, bs, bc, axis)) % 360.0
    diff = (fwd - target + 180) % 360 - 180
    return float(grid[int(np.argmin(np.abs(diff)))])


# ── Style ────────────────────────────────────────────────────────────────────
matplotlib.rcParams.update({
    "font.family"      : "sans-serif",
    "font.sans-serif"  : ["Helvetica", "Arial", "DejaVu Sans"],
    "font.size"        : 7.5,
    "axes.titlesize"   : 8.0,
    "axes.labelsize"   : 7.5,
    "pdf.fonttype"     : 42,
    "ps.fonttype"      : 42,
})

# ── Figure layout ────────────────────────────────────────────────────────────
NROWS = len(HUE_8)
FIG_W = 180 / 25.4              # 7.087 in (Nature double-column width)
FIG_H = 0.74 * NROWS + 1.05     # ≈ 6.97 in

fig = plt.figure(figsize=(FIG_W, FIG_H))

# 10 GridSpec columns:
#   0       : left-block row labels
#   1-4     : sub-08 4 columns
#   5       : inter-block gap
#   6-9     : sub-09 4 columns
N_COLS = 10
gs = GridSpec(NROWS, N_COLS, figure=fig,
              width_ratios=[0.55,
                            1.0, 1.0, 1.0, 1.0,
                            0.55,
                            1.0, 1.0, 1.0, 1.0],
              hspace=0.10, wspace=0.18,
              left=0.045, right=0.99,
              top=0.84, bottom=0.025)

LEFT_BLOCK_COLS  = (1, 2, 3, 4)
RIGHT_BLOCK_COLS = (6, 7, 8, 9)

# Per-subject column-block axes table (filled below)
all_block_axes = []  # list of (subject_index, dict[col_idx] -> axes_at_row0)

# ── Row labels (left only) ───────────────────────────────────────────────────
for i in range(NROWS):
    ax = fig.add_subplot(gs[i, 0])
    ax.axis("off")
    ax.text(0.98, 0.5,
            f"c{i+1}\n{COLOR_LABELS[i]}\n{HUE_8[i]}°",
            transform=ax.transAxes, ha="right", va="center",
            fontsize=7.0)

# ── Per-subject 4-column blocks ──────────────────────────────────────────────
for s_idx, subj in enumerate(SUBJECTS):
    block_cols = LEFT_BLOCK_COLS if s_idx == 0 else RIGHT_BLOCK_COLS
    bs, bc, axis = subj["bs"], subj["bc"], subj["axis"]

    row0_axes = {}  # gs_col -> axes at row 0 (used to set column titles)

    for i, theta in enumerate(HUE_8):
        tcvd, _      = forward(float(theta), bs, bc, axis)
        tpre         = pre_image(float(theta), bs, bc, axis)
        tcvd_pre, _  = forward(tpre, bs, bc, axis)
        col_hues = [float(theta), tcvd, tpre, tcvd_pre]
        for gs_col, t_render in zip(block_cols, col_hues):
            ax = fig.add_subplot(gs[i, gs_col])
            rgb = _render_stim_lab(t_render, dL=0.0)
            ax.imshow(np.array([[rgb]]), aspect="auto")
            ax.set_xticks([]); ax.set_yticks([])
            for sp in ax.spines.values():
                sp.set_linewidth(0.4)
            if i == 0:
                row0_axes[gs_col] = ax

    # Column titles inside this block
    for gs_col, ct in zip(block_cols, COL_TITLES):
        row0_axes[gs_col].set_title(ct, fontsize=7.5, pad=4)

    # Block subject header (figure-coord text, centred on the block)
    x0 = row0_axes[block_cols[0]].get_position().x0
    x1 = row0_axes[block_cols[-1]].get_position().x1
    x_center = 0.5 * (x0 + x1)
    title = (rf"sub-{subj['sid']} ({subj['family']}):  "
             rf"$\hat\beta_s = {bs:.0f}°$,  "
             rf"$\hat\beta_c = {bc:+.0f}°$,  "
             rf"$\|\hat\beta\| = {np.hypot(bs, bc):.1f}°$")
    fig.text(x_center, 0.92, title,
             ha="center", va="bottom",
             fontsize=9.0, fontweight="bold", color=subj["color"])

# ── Save ─────────────────────────────────────────────────────────────────────
out_base = OUT / "fig5_preimage"
fig.savefig(f"{out_base}.png", dpi=300, bbox_inches="tight",
            facecolor="white")
fig.savefig(f"{out_base}.pdf", bbox_inches="tight",
            facecolor="white")
print(f"Saved:\n  {out_base}.png\n  {out_base}.pdf")
plt.close(fig)
