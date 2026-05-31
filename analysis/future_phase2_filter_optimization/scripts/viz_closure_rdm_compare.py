"""Closure ground plot — PCA-RDM vs SRM-cosine vs SRM-disparity comparison.

Reproduces the closure Appendix A.2 robustness check on the (β_s, β_c) grid:
for the same combo (γ_atom + RDM_V1 or V2), swap only the RDM atom definition
and recompute the z-score composite. Shows the mechanism reversal for sub-09
where (β_s=2, β_c=+24) under PCA flips to (β_s=32, β_c=0) under SRM family.

Output:
  results/visualizations/closure_rdm_compare/
    rdm_compare_S09_bc_rot.png      γ_all + RDM_V1 (3 panels)
    rdm_compare_S08_bs_dom.png      γ_all + RDM_V1 (3 panels)
    rdm_compare_S08_bc_dom.png      γ_OY  + RDM_V2 (3 panels)
    rdm_compare_summary.png         all 3 subjects × 3 RDM families
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from two_comp import BS_GRID, BC_GRID
from neural_loss import load_amplitudes, load_hc_pool, ROI_K
from behav_loss import load_jnd_per_pair, HC_JND_SUBJS
from utils_forward_model import create_basis_full, HUE_ANGLES

from s10b_v6_pca_rdm import (
    make_gamma_pair_atom,
    make_rdm_atom as make_pca_rdm_atom,
    grid_eval_2comp,
    zscore_grid,
    HC_SUBJS,
)
from s10b_v6_srm_rdm import make_srm_rdm_atom
from s10b_v6_srm_disparity import make_srm_disparity_atom

import json
from collections import Counter

OUT_DIR = SCRIPT_DIR.parent / "results" / "visualizations" / "pipeline2_alternative_rdm"
OUT_DIR.mkdir(parents=True, exist_ok=True)
JSON_DIR = SCRIPT_DIR.parent / "results" / "s10_inclusion"

ATOM_FACTORIES = {
    "PCA-RDM": make_pca_rdm_atom,
    "SRM-cos": make_srm_rdm_atom,
    "SRM-dis": make_srm_disparity_atom,
}

JSON_BY_FAMILY = {
    "PCA-RDM": "s10b_v6_pca_rdm_results_{sub}.json",
    "SRM-cos": "s10b_v6_srm_rdm_results_{sub}.json",
    "SRM-dis": "s10b_v6_srm_disparity_results_{sub}.json",
}


def load_resample_cloud(subject, family, combo_key):
    """Load 300-resample (β_s, β_c) argmins from the corresponding v6 JSON."""
    path = JSON_DIR / JSON_BY_FAMILY[family].format(sub=subject)
    if not path.exists():
        return np.array([]), np.array([])
    d = json.load(open(path))
    store = d.get("storage", {}).get(combo_key)
    if store is None:
        return np.array([]), np.array([])
    two = store.get("2comp", [])
    bs = np.array([r["beta_s"] for r in two], dtype=float)
    bc = np.array([r["beta_c"] for r in two], dtype=float)
    return bs, bc

# Per closure A.2 — fit points by RDM family
CANDIDATES = [
    {
        "id": "S09_bc_rot",
        "subject": "sub-09",
        "family": "protan",
        "label": "Sub-09 protan · γ_all + RDM_V1",
        "gamma_atoms": ["ALL"],
        "rdm_roi": "V1",
        "combo_key": "γALL|RDMV1|noLOCO",
        "fit_by_family": {  # closure A.2 table (300-resample median)
            "PCA-RDM": (2.0, 24.0),
            "SRM-cos": (32.0, 0.0),
            "SRM-dis": (32.0, 0.0),
        },
    },
    {
        "id": "S08_bs_dom",
        "subject": "sub-08",
        "family": "deutan",
        "label": "Sub-08 deutan · γ_all + RDM_V1",
        "gamma_atoms": ["ALL"],
        "rdm_roi": "V1",
        "combo_key": "γALL|RDMV1|noLOCO",
        "fit_by_family": {
            "PCA-RDM": (38.0, -10.0),
            "SRM-cos": (22.0, -36.0),
            "SRM-dis": (24.0, -20.0),
        },
    },
    {
        "id": "S08_bc_dom",
        "subject": "sub-08",
        "family": "deutan",
        "label": "Sub-08 deutan · γ_OY + RDM_V2",
        "gamma_atoms": ["OY"],
        "rdm_roi": "V2",
        "combo_key": "γOY|RDMV2|noLOCO",
        "fit_by_family": {
            "PCA-RDM": (6.0, -42.0),
            "SRM-cos": (8.0, -42.0),
            "SRM-dis": (2.0, -24.0),
        },
    },
]


def build_composite(cand, rdm_family):
    """Composite over (β_s, β_c) for one (subject, gamma, RDM family)."""
    subject = cand["subject"]
    family = cand["family"]
    roi = cand["rdm_roi"]

    cvd_jnd = load_jnd_per_pair(subject)
    grids = []
    labels = []
    for p in cand["gamma_atoms"]:
        fn = make_gamma_pair_atom(p, cvd_jnd, HC_JND_SUBJS)
        if fn is None:
            continue
        grids.append(grid_eval_2comp(fn, family))
        labels.append(f"γ_{p}")

    cvd_amp = load_amplitudes(subject, roi)
    hc_amps = load_hc_pool(roi)
    pool = {h: hc_amps[h] for h in HC_SUBJS if h in hc_amps}
    K = ROI_K[roi]
    C_b = create_basis_full(K, basis_type="fe")[HUE_ANGLES.astype(int)]
    fn_r = ATOM_FACTORIES[rdm_family](roi, cvd_amp, pool, C_b, K)
    if fn_r is None:
        return None, None, None
    rdm_grid = grid_eval_2comp(fn_r, family)
    grids.append(rdm_grid)
    labels.append(f"{rdm_family}_{roi}")

    n_a = len(grids)
    z_sum = None
    z_each = []
    for g in grids:
        z = zscore_grid(g)
        z_each.append(z)
        z_sum = z if z_sum is None else z_sum + z
    comp = z_sum / np.sqrt(n_a)

    # Find argmin
    flat = int(np.nanargmin(comp.ravel()))
    i, j = np.unravel_index(flat, comp.shape)
    argmin = (BS_GRID[i], BC_GRID[j])

    return comp, argmin, labels


def plot_panel(ax, comp, argmin, fit_pt, family_label, atom_labels,
                bs_cloud=None, bc_cloud=None):
    BC, BS = np.meshgrid(BC_GRID, BS_GRID)
    vmin = np.nanpercentile(comp, 1)
    vmax = np.nanpercentile(comp, 99)
    im = ax.pcolormesh(BC, BS, comp, cmap="viridis_r", shading="auto",
                       norm=Normalize(vmin=vmin, vmax=vmax))
    levels = np.nanpercentile(comp, [5, 15, 30, 50, 70])
    ax.contour(BC, BS, comp, levels=levels, colors="white",
               alpha=0.45, linewidths=0.7)

    # 300-resample argmin cloud (white dots, size ~ count)
    if bs_cloud is not None and len(bs_cloud) > 0:
        counts = Counter(zip(bs_cloud, bc_cloud))
        for (bs_v, bc_v), n in counts.items():
            ax.scatter(bc_v, bs_v, s=8 + 2.0 * n, c="white",
                       edgecolors="black", linewidth=0.4, alpha=0.55, zorder=3)
        # most-frequent argmin (cloud mode)
        mode_pt = counts.most_common(1)[0]
        (mbs, mbc), mn = mode_pt
        ax.scatter(mbc, mbs, marker="o", s=140, c="cyan",
                   edgecolors="black", linewidth=1.1, zorder=5,
                   label=f"resample mode ({mbs:.0f},{mbc:.0f}) n={mn}/300")

    # closure-reported fit (300-resample median; red star)
    fit_bs, fit_bc = fit_pt
    ax.scatter(fit_bc, fit_bs, marker="*", s=320, c="red",
               edgecolors="white", linewidth=1.2, zorder=6,
               label=f"closure A.2 median ({fit_bs:.0f},{fit_bc:.0f})")

    # NOTE: 7HC full-pool argmin marker intentionally NOT plotted.
    # Closure analysis is entirely 300-resample based; the full-pool single fit
    # is a reconstruction artifact (e.g. sub-09 SRM-cos full-pool=(2,24) is a
    # knife-edge appearing in 0/300 resamples). Use resample mode/median only.

    ax.set_xlabel("β_c (deg)", fontsize=9)
    ax.set_ylabel("β_s (deg)", fontsize=9)
    ax.set_title(f"{family_label}  ·  {', '.join(atom_labels)}", fontsize=9.5)
    ax.legend(loc="lower right", fontsize=7, framealpha=0.85)
    ax.set_xlim(BC_GRID[0], BC_GRID[-1])
    ax.set_ylim(BS_GRID[0], BS_GRID[-1])
    return im


def main():
    summary_panels = []  # for global summary

    for cand in CANDIDATES:
        print(f"\n=== {cand['id']} === {cand['label']}", flush=True)
        fig, axes = plt.subplots(1, 3, figsize=(22, 7))
        comps = {}
        for ax, family in zip(axes, ATOM_FACTORIES.keys()):
            print(f"  building {family}...", flush=True)
            comp, argmin, labels = build_composite(cand, family)
            if comp is None:
                ax.set_title(f"{family}: build failed")
                continue
            comps[family] = (comp, argmin, labels)
            fit_pt = cand["fit_by_family"][family]
            bs_cloud, bc_cloud = load_resample_cloud(
                cand["subject"], family, cand["combo_key"])
            im = plot_panel(ax, comp, argmin, fit_pt, family, labels,
                            bs_cloud, bc_cloud)
            fig.colorbar(im, ax=ax, shrink=0.82, pad=0.02,
                         label="composite z (lower = better)")

        fig.suptitle(f"{cand['label']}  —  RDM-atom family swap "
                     f"(landscape=7-HC full-pool z-composite; "
                     f"markers=300-resample mode/median)",
                     fontsize=12, y=1.02)
        out_path = OUT_DIR / f"rdm_compare_{cand['id']}.png"
        fig.savefig(out_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"  → {out_path.name}", flush=True)
        summary_panels.append((cand, comps))

    # 3 × 3 grid summary (rows=candidates, cols=RDM families)
    fig, axes = plt.subplots(3, 3, figsize=(22, 20))
    for r, (cand, comps) in enumerate(summary_panels):
        for c, family in enumerate(ATOM_FACTORIES.keys()):
            ax = axes[r, c]
            if family not in comps:
                ax.set_title(f"{family}: missing")
                continue
            comp, argmin, labels = comps[family]
            fit_pt = cand["fit_by_family"][family]
            bs_cloud, bc_cloud = load_resample_cloud(
                cand["subject"], family, cand["combo_key"])
            im = plot_panel(ax, comp, argmin, fit_pt,
                            f"{cand['subject']}  ·  {family}", labels,
                            bs_cloud, bc_cloud)
            fig.colorbar(im, ax=ax, shrink=0.78, pad=0.02)
        axes[r, 0].set_ylabel(f"{cand['label']}\nβ_s (deg)", fontsize=9.5)

    fig.suptitle("Closure RDM-atom family comparison (Appendix A.2 reproduction)  ·  "
                 "PCA vs SRM-cosine vs SRM-disparity composite landscape",
                 fontsize=13, y=1.005)
    fig.tight_layout()
    out_path = OUT_DIR / "rdm_compare_summary.png"
    fig.savefig(out_path, dpi=140, bbox_inches="tight")
    plt.close(fig)
    print(f"\n→ {out_path}", flush=True)

    # Quantitative table dump
    print("\n=== Argmin reproducibility check (this script vs closure A.2) ===")
    print(f"{'subject':12s} {'family':10s} {'closure':18s} {'script':18s} {'match':6s}")
    for cand, comps in summary_panels:
        for family in ATOM_FACTORIES.keys():
            if family not in comps:
                continue
            _, argmin, _ = comps[family]
            fit_pt = cand["fit_by_family"][family]
            match = "✓" if (abs(argmin[0]-fit_pt[0]) < 4 and
                            abs(argmin[1]-fit_pt[1]) < 4) else "✗"
            print(f"  {cand['id']:12s} {family:10s} "
                  f"({fit_pt[0]:+.0f},{fit_pt[1]:+.0f})       "
                  f"({argmin[0]:+.0f},{argmin[1]:+.0f})       {match}")


if __name__ == "__main__":
    main()
