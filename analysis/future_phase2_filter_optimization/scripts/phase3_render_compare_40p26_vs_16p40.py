"""phase3_render_compare_40p26_vs_16p40.py — side-by-side compare
two positive-β_c candidates for sub-08 V4:
  Left:  (β_s=40, β_c=+26) — P2a-behavior-best within OLD top 10
  Right: (β_s=16, β_c=+40) — V4 CCC argmin

8 rows × 8 cols layout:
  cols 1-4: (40, +26) Original / CVD perceives / Filtered / CVD(Filtered)
  cols 5-8: (16, +40) Original / CVD perceives / Filtered / CVD(Filtered)
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR))
sys.path.insert(0, str(_THIS_DIR / "visualization"))

from stim_lab_render import render_at_hue as _render_stim_lab
from phase3_candidate_analysis_v2 import hc_name, hc_match_score, SUB08_ORIGINAL_HC_EQUIV

OUTDIR = _THIS_DIR.parent / "results" / "old_formula"
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
    grid = np.linspace(0.0, 360.0, n_grid, endpoint=False)
    forwards = np.array([forward_old(t, beta_s, beta_c)[0] for t in grid])
    diff = (forwards - target_deg + 180.0) % 360.0 - 180.0
    i = int(np.argmin(np.abs(diff)))
    return float(grid[i]), float(diff[i])


def render_compare(filters, title, out_path):
    """filters: list of dicts with keys 'bs', 'bc', 'label', 'subtitle'."""
    n_rows = len(TIER1)
    n_filt = len(filters)
    n_cols = 4 * n_filt  # 4 columns per filter

    fig, axes = plt.subplots(n_rows, n_cols,
                             figsize=(2.2 * n_filt + 7.5, 0.65 * n_rows + 1.5),
                             gridspec_kw={"hspace": 0.10, "wspace": 0.05})
    fig.suptitle(title, fontsize=11, y=0.99)

    # Per-filter header
    for fi, f in enumerate(filters):
        cstart = fi * 4
        cend = cstart + 4
        # Title row above the 4 columns of this filter
        for j, ct in enumerate(["Original", "CVD perceives",
                                "Filtered (pre-image)", "CVD(Filtered)"]):
            axes[0, cstart + j].set_title(ct, fontsize=8)
        # Group label above the entire block — use figure text
        cx_center = ((cstart + 0.5) + (cend - 0.5)) / (2 * n_cols)
        fig.text(cx_center * 0.96 + 0.04, 0.97,
                 f.get('group', f"Filter {fi+1}"),
                 ha='center', fontsize=10, fontweight='bold',
                 color=f.get('color', 'black'))

    for i, (theta, label) in enumerate(TIER1):
        for fi, f in enumerate(filters):
            bs = f['bs']; bc = f['bc']
            cstart = fi * 4

            theta_cvd, dt = forward_old(float(theta), bs, bc)
            theta_pre, resid = pre_image_old(float(theta), bs, bc)
            theta_cvd_pre, _ = forward_old(theta_pre, bs, bc)

            rgb_orig = _render_stim_lab(float(theta), dL=0.0)
            rgb_cvd = _render_stim_lab(theta_cvd, dL=0.0)
            rgb_pre = _render_stim_lab(theta_pre, dL=0.0)
            rgb_cvd_pre = _render_stim_lab(theta_cvd_pre, dL=0.0)

            ax_o = axes[i, cstart]
            ax_c = axes[i, cstart + 1]
            ax_p = axes[i, cstart + 2]
            ax_f = axes[i, cstart + 3]

            for ax, rgb in zip([ax_o, ax_c, ax_p, ax_f],
                               [rgb_orig, rgb_cvd, rgb_pre, rgb_cvd_pre]):
                ax.add_patch(Rectangle((0, 0), 1, 1, color=rgb))
                ax.set_xticks([]); ax.set_yticks([])
                ax.set_xlim(0, 1); ax.set_ylim(0, 1)
                for sp in ax.spines.values():
                    sp.set_edgecolor("black"); sp.set_linewidth(0.5)

            # Only label cells once (leftmost filter, leftmost column)
            if fi == 0:
                ax_o.text(-0.10, 0.5, f"{label}\nθ={theta}°",
                          ha="right", va="center", fontsize=7,
                          transform=ax_o.transAxes)

            # P2a annotation under col 2 (CVD perceives)
            pred_name = hc_name(theta_cvd)
            target_name = SUB08_ORIGINAL_HC_EQUIV[int(theta)]
            score = hc_match_score(pred_name, target_name)
            mark = '✓' if pred_name == target_name else ('~' if score > 0 else '✗')
            ax_c.text(0.5, -0.02, f"δθ={dt:+.0f}° {mark}",
                      ha="center", va="top", fontsize=7,
                      transform=ax_c.transAxes,
                      color=('green' if score == 1.0
                             else ('darkorange' if score > 0 else 'red')))

            # pre-image annotation under col 3
            ax_p.text(0.5, -0.02, f"θ_pre={theta_pre:.0f}°",
                      ha="center", va="top", fontsize=7,
                      transform=ax_p.transAxes)

    # Footer with P2a summary per filter
    for fi, f in enumerate(filters):
        bs = f['bs']; bc = f['bc']
        cstart = fi * 4
        # Compute P2a
        total = 0; exact = 0
        for theta, _ in TIER1:
            theta_cvd, _ = forward_old(float(theta), bs, bc)
            p = hc_name(theta_cvd); t = SUB08_ORIGINAL_HC_EQUIV[int(theta)]
            s = hc_match_score(p, t); total += s
            if p == t: exact += 1
        cx_center = ((cstart + 0.5) + (cstart + 3.5)) / (2 * n_cols)
        fig.text(cx_center * 0.96 + 0.04, 0.005,
                 f"{f['subtitle']}  P2a={total/8:.3f} ({exact}/8 exact)",
                 ha='center', fontsize=8, color=f.get('color', 'black'))

    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {out_path}")


def main():
    filters = [
        {'bs': 40, 'bc': 26,
         'group': '(β_s=40°, β_c=+26°)',
         'subtitle': 'OLD top10 P2a-best (L_fit rank 4)',
         'color': '#cc4400'},
        {'bs': 16, 'bc': 40,
         'group': '(β_s=16°, β_c=+40°)',
         'subtitle': 'V4 CCC argmin (L_fit rank 1 under CCC)',
         'color': '#0066aa'},
    ]
    render_compare(
        filters,
        "sub-08 V4 OLD: (β_s=40, β_c=+26) vs (β_s=16, β_c=+40) — both positive-β_c family",
        OUTDIR / "compare_sub-08_V4_40p26-vs-16p40.png")


if __name__ == '__main__':
    main()
