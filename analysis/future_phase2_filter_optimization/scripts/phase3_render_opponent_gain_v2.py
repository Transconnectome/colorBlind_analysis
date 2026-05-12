"""phase3_render_opponent_gain_v2.py — 4-column viz for (h) v2 fit + v1 compare."""
from __future__ import annotations
import json
import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR))
sys.path.insert(0, str(_THIS_DIR / "forward_models"))
sys.path.insert(0, str(_THIS_DIR / "visualization"))

from forward_models.opponent_gain import forward_opponent_gain, pre_image_opponent_gain
from stim_lab_render import render_at_hue as _render_stim_lab

OUTDIR = _THIS_DIR.parent / "results" / "phase3_candidates" / "opponent_gain_fit"

CVD = "deutan"
TIER1 = [(0, "c1 (red)"), (45, "c2 (orange)"), (90, "c3 (yellow)"),
         (135, "c4 (green)"), (180, "c5 (cyan)"), (225, "c6 (sky)"),
         (270, "c7 (blue)"), (315, "c8 (magenta)")]


def render_fit(dl, glm, gs, title, outpath):
    n = len(TIER1)
    fig, axes = plt.subplots(n, 4, figsize=(8.5, 0.65*n + 1.5),
                             gridspec_kw={"hspace": 0.10, "wspace": 0.08})
    fig.suptitle(f"{title}\n2-channel opponent gain  "
                 f"Δλ={dl}nm  g_LM={glm:.3f}  g_S={gs:.3f}", fontsize=10, y=0.995)
    for ax, ct in zip(axes[0], ["Original", "CVD perceives",
                                 "Filtered (pre-image)", "CVD(Filtered)"]):
        ax.set_title(ct, fontsize=9)

    for i, (theta, label) in enumerate(TIER1):
        ax_row = axes[i]
        theta_pre, resid = pre_image_opponent_gain(float(theta), CVD, dl, glm, gs)
        theta_cvd, dt = forward_opponent_gain(float(theta), CVD, dl, glm, gs)
        theta_cvd_pre, _ = forward_opponent_gain(theta_pre, CVD, dl, glm, gs)

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


def main():
    with open(OUTDIR / "fit_result_v2.json") as f:
        v2 = json.load(f)
    b = v2["best"]
    render_fit(b["dl"], b["g_LM"], b["g_S"],
               f"Path A v2: joint hue+chroma loss (loss={b['loss']:.4f})",
               OUTDIR / "visualization_v2.png")

    # v1 for direct compare
    render_fit(14.0, 0.45, 1.15,
               "v1: hue-only loss (Δλ=14 fixed)",
               OUTDIR / "visualization_v1_compare.png")


if __name__ == "__main__":
    main()
