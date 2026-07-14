#!/usr/bin/env python3
"""p4_overlay_viz.py — GAP1: SRM vs FE embedding overlay (consumer layer).

For each (ROI x condition): take SRM coords (8xK) and FE-latent coords (8x6) from
Stage-1 JSON, build RDM(metric) -> classical MDS 2D -> Procrustes-align FE onto SRM
-> overlay both 8-colour configs, connect corresponding colours with displacement
lines. Annotate Procrustes disparity + label-permutation p (PRIMARY discriminator).

Grid: rows = ROIs (V1,V2,V3,hV4), cols = conditions (nofilter,window,optimal).
One figure per (subject, variant, metric). 3D optional via --dim 3.

Run:  conda activate srm
      python p4_overlay_viz.py --subject 08 --variant matched --metric corr
"""
import argparse
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

import utils_p4 as U

FIGDIR = U.P4 / "figures"
RESDIR = U.P4 / "results"
FIGDIR.mkdir(exist_ok=True)
RESDIR.mkdir(exist_ok=True)


def align_pair(srm_coords, fe_coords, metric, ndim):
    """SRM & FE coords -> RDM -> MDS(ndim) -> Procrustes align FE to SRM."""
    Ds = U.rdm_from_coords(srm_coords, metric)
    Df = U.rdm_from_coords(fe_coords, metric)
    Xs, eig_s, stress_s = U.classical_mds(Ds, ndim)
    Xf, eig_f, stress_f = U.classical_mds(Df, ndim)
    # Procrustes align FE (Xf) onto SRM (Xs): centre+unit-Frob+rotation
    Xsc = Xs - Xs.mean(0); Xfc = Xf - Xf.mean(0)
    Xsn = Xsc / (np.linalg.norm(Xsc) + 1e-12)
    Xfn = Xfc / (np.linalg.norm(Xfc) + 1e-12)
    from scipy.linalg import orthogonal_procrustes
    R, _ = orthogonal_procrustes(Xfn, Xsn)
    Xf_al = Xfn @ R
    obs, p, null_mean = U.label_perm_null(Xsn, Xfn, n_perm=2000)
    return {'Xs': Xsn, 'Xf': Xf_al, 'disparity': obs, 'perm_p': p,
            'null_mean': null_mean, 'stress_s': stress_s, 'stress_f': stress_f,
            'eig_s': eig_s.tolist(), 'eig_f': eig_f.tolist()}


def plot_panel(ax, res, ndim, title):
    Xs, Xf = res['Xs'], res['Xf']
    loop = list(range(8)) + [0]           # closed hue path red->...->magenta->red
    # embedding SHAPE: connect the 8 colours in hue order WITHIN each embedding
    # (SRM solid, FE dashed) so each embedding's hue-circle form is visible.
    if ndim == 2:
        ax.plot(Xs[loop, 0], Xs[loop, 1], '-', c='0.35', lw=1.2, alpha=0.75, zorder=1)
        ax.plot(Xf[loop, 0], Xf[loop, 1], '--', c='0.35', lw=1.2, alpha=0.75, zorder=1)
    else:
        ax.plot(Xs[loop, 0], Xs[loop, 1], Xs[loop, 2], '-', c='0.35', lw=1.0, alpha=0.7)
        ax.plot(Xf[loop, 0], Xf[loop, 1], Xf[loop, 2], '--', c='0.35', lw=1.0, alpha=0.7)
    for i, (name, hx) in enumerate(zip(U.COLOR_NAMES, U.COLOR_HEX)):
        if ndim == 2:
            ax.scatter(*Xs[i], c=hx, s=110, edgecolors='k', linewidths=0.8, zorder=3)
            ax.scatter(*Xf[i], c=hx, s=70, marker='^', edgecolors='k',
                       linewidths=0.8, zorder=3)
        else:
            ax.scatter(*Xs[i], c=hx, s=90, edgecolors='k', linewidths=0.6)
            ax.scatter(*Xf[i], c=hx, s=55, marker='^', edgecolors='k', linewidths=0.6)
    sig = '*' if res['perm_p'] < 0.05 else ''
    ax.set_title(f"{title}\nM²={res['disparity']:.3f}  p={res['perm_p']:.3f}{sig}",
                 fontsize=8)
    ax.set_xticks([]); ax.set_yticks([])
    if ndim == 2:
        ax.set_aspect('equal', 'datalim')
    else:
        ax.set_zticks([])


def run(subject, variant, metric, ndim):
    d1 = U.load_stage1(subject, variant)
    hc_self = U.hc_self_consistency()
    nrow, ncol = len(U.ROIS), len(U.CONDS)
    subplot_kw = {'projection': '3d'} if ndim == 3 else {}
    fig, axes = plt.subplots(nrow, ncol, figsize=(3.1 * ncol, 3.1 * nrow),
                             subplot_kw=subplot_kw, squeeze=False)
    summary = {'subject': subject, 'variant': variant, 'metric': metric,
               'ndim': ndim, 'hc_self_consistency': hc_self, 'rois': {}}
    for r, roi in enumerate(U.ROIS):
        summary['rois'][roi] = {}
        for c, cond in enumerate(U.CONDS):
            srm = U.get_coords(d1, roi, 'srm', cond)
            fe = U.get_coords(d1, roi, 'fe_latent', cond)
            res = align_pair(srm, fe, metric, ndim)
            hc = hc_self.get(roi)
            hc_txt = f"{hc:.2f}" if hc is not None else "NA"
            title = f"{U.ROI_DISPLAY[roi]} · {cond}  (HCρ={hc_txt})"
            plot_panel(axes[r][c], res, ndim, title)
            summary['rois'][roi][cond] = {
                'disparity': res['disparity'], 'perm_p': res['perm_p'],
                'null_mean': res['null_mean'], 'stress_srm': res['stress_s'],
                'stress_fe': res['stress_f'], 'hc_self_consistency': hc}
    fig.suptitle(f"SRM vs FE embedding overlay — sub-{subject} ({variant}, {metric}, {ndim}D)\n"
                 f"circle+solid=SRM hue path   triangle+dashed=FE hue path (aligned)   "
                 f"loop = colours in hue order (red→…→magenta)   * = perm p<0.05", fontsize=10)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    out = FIGDIR / f"overlay_sub-{subject}_{variant}_{metric}_{ndim}d.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    jout = RESDIR / f"p4_overlay_sub-{subject}_{variant}_{metric}_{ndim}d.json"
    with open(jout, 'w') as fh:
        json.dump(summary, fh, indent=1)
    print(f"saved: {out}\n       {jout}")
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--subject', default='08')
    ap.add_argument('--variant', default='matched', choices=['matched', 'native'])
    ap.add_argument('--metric', default='corr', choices=['eucl', 'corr'])
    ap.add_argument('--dim', type=int, default=2, choices=[2, 3])
    args = ap.parse_args()
    run(args.subject, args.variant, args.metric, args.dim)


if __name__ == '__main__':
    main()
