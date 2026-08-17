"""_fig_delta_loco.py — participant-level Delta LOCO (hmc - primary) vs motion.

Answers the question raised on 2026-08-15: the protan hV4 estimate moves
0.125 -> 0.271 under realignment, but that only matters if the controls do not
move by a comparable amount. Plots each participant's Delta against motion so the
HC distribution and the two CVD cases can be read directly.

Descriptive only: n = 9, no inferential correlation is claimed.
"""
import json
import statistics as st

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import sys as _sys
from pathlib import Path as _Path

# Moved out of docs/PAPER/repro on 2026-08-17 (analysis/future_phase1_sensitivity).
# _repro_util still lives there and stays the single definition of the data roots.
_REPRO = _Path(__file__).resolve().parents[3] / "docs" / "PAPER" / "repro"
_sys.path.insert(0, str(_REPRO))
OUT = _Path(__file__).resolve().parent.parent / "results"
OUT.mkdir(parents=True, exist_ok=True)

import _repro_util as U  # noqa: E402

ALL = [f"sub-0{i}" for i in range(1, 10)]
HC = ALL[:7]
CVD = {"sub-08": "deutan", "sub-09": "protan"}

# mean FD, 95th-percentile FD, mean max displacement from each run's reference volume
MOTION = {
    "sub-01": (0.3379, 0.8027, 0.8267), "sub-02": (0.2431, 0.5265, 0.7138),
    "sub-03": (0.3205, 0.6419, 0.9255), "sub-04": (0.2762, 0.6295, 0.9920),
    "sub-05": (0.3793, 0.8008, 0.7179), "sub-06": (0.3033, 0.6354, 1.1637),
    "sub-07": (0.3132, 0.6811, 0.7690), "sub-08": (0.3837, 1.0595, 1.6990),
    "sub-09": (0.2922, 0.7309, 0.7291),
}
XLAB = {0: "mean FD (mm)", 1: "95th-percentile FD (mm)",
        2: "max displacement from reference volume (mm)"}


def main():
    A = json.load(open(OUT / "boot_runs_with_residuals.json"))["rois"]
    B = json.load(open(OUT / "boot_runs_hmc_v2.json"))["rois"]
    rois = ["V1", "V2", "V3", "hV4"]

    fig, axes = plt.subplots(len(rois), 3, figsize=(13, 4 * len(rois)))
    for i, roi in enumerate(rois):
        base = {s: A[roi]["subjects"][s]["point"] for s in ALL}
        d = {s: B[roi]["subjects"][s]["point"] - base[s] for s in ALL}
        hcd = [d[s] for s in HC]
        m, sd = st.mean(hcd), st.stdev(hcd)

        for j in range(3):
            ax = axes[i, j]
            ax.axhspan(m - sd, m + sd, color="0.85", zorder=0)
            ax.axhline(m, color="0.45", lw=1, zorder=1)
            ax.axhline(0, color="k", lw=0.6, ls=":", zorder=1)
            for s in HC:
                ax.scatter(MOTION[s][j], d[s], s=52, c="0.35", zorder=3)
            for s, kind in CVD.items():
                c = "#c0392b" if kind == "deutan" else "#2471a3"
                ax.scatter(MOTION[s][j], d[s], s=140, marker="D", c=c,
                           edgecolor="k", linewidth=0.8, zorder=4)
                ax.annotate(kind, (MOTION[s][j], d[s]), textcoords="offset points",
                            xytext=(9, 4), fontsize=9, color=c, weight="bold")
            ax.set_xlabel(XLAB[j], fontsize=9)
            if j == 0:
                ax.set_ylabel(f"{roi}\n$\\Delta$ LOCO (hmc $-$ primary)", fontsize=10)
            ax.tick_params(labelsize=8)
            if i == 0 and j == 1:
                ax.set_title("grey band = HC mean $\\pm$ SD;  n = 9, descriptive only",
                             fontsize=10)
    fig.tight_layout()
    out = OUT / "fig_delta_loco_vs_motion.png"
    fig.savefig(out, dpi=150)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
