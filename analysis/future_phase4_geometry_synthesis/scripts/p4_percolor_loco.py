#!/usr/bin/env python3
"""p4_percolor_loco.py — GAP5: per-colour LOCO diagnostic ("which colour leaves").

Uses Stage-1 loco block: for each held-out colour, decoded_hue vs true_hue.
  hue_error_deg[c] = circular error when colour c is held out (in-sample training
                     on the other 7, out-sample prediction of c).
A single colour with a large error is the one poorly interpolated ("leaving").
Also renders the 8x8 confusion matrix per condition.

Cross-reference: does the leaving colour sit on the CVD confusion axis
(deutan red-green / protan)? -> flagged in the JSON.

Run:  python p4_percolor_loco.py --subject 08 --variant matched
"""
import argparse
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import utils_p4 as U

FIGDIR = U.P4 / "figures"; RESDIR = U.P4 / "results"
FIGDIR.mkdir(exist_ok=True); RESDIR.mkdir(exist_ok=True)


def run(subject, variant):
    d1 = U.load_stage1(subject, variant)
    out = {'subject': subject, 'variant': variant, 'color_names': U.COLOR_NAMES,
           'rois': {}}
    nrow, ncol = len(U.ROIS), len(U.CONDS)
    # figure A: per-colour hue error bars (which colour leaves)
    figE, axE = plt.subplots(nrow, ncol, figsize=(3.4 * ncol, 2.4 * nrow),
                             sharey=True, squeeze=False)
    # figure B: confusion heatmaps
    figC, axC = plt.subplots(nrow, ncol, figsize=(2.8 * ncol, 2.8 * nrow),
                             squeeze=False)
    for r, roi in enumerate(U.ROIS):
        out['rois'][roi] = {}
        for c, cond in enumerate(U.CONDS):
            loco = d1['rois'][roi]['loco'][cond]
            err = np.asarray(loco['hue_error_deg'], float)
            conf = np.asarray(loco['confusion'], float)
            mu, sd = err.mean(), err.std()
            leaving = [U.COLOR_NAMES[i] for i in np.where(err > mu + 2 * sd)[0]]
            out['rois'][roi][cond] = {
                'hue_error_deg': err.tolist(),
                'adj_acc': loco.get('adj_acc'), 'exact_acc': loco.get('exact_acc'),
                'leaving_colors_>2sd': leaving,
                'max_error_color': U.COLOR_NAMES[int(np.argmax(err))],
                'max_error_deg': float(err.max())}
            # bars
            ax = axE[r][c]
            ax.bar(range(8), err, color=U.COLOR_HEX, edgecolor='k', linewidth=0.6)
            ax.axhline(mu + 2 * sd, color='r', ls='--', lw=0.8)
            ax.set_title(f"{U.ROI_DISPLAY[roi]}·{cond}  adj={loco.get('adj_acc'):.2f}",
                         fontsize=8)
            ax.set_xticks(range(8))
            ax.set_xticklabels([n[:3] for n in U.COLOR_NAMES], rotation=90, fontsize=6)
            # confusion
            axc = axC[r][c]
            im = axc.imshow(conf, cmap='magma', aspect='equal')
            axc.set_title(f"{U.ROI_DISPLAY[roi]}·{cond}", fontsize=8)
            axc.set_xticks(range(8)); axc.set_yticks(range(8))
            axc.set_xticklabels([n[:3] for n in U.COLOR_NAMES], rotation=90, fontsize=5)
            axc.set_yticklabels([n[:3] for n in U.COLOR_NAMES], fontsize=5)
    figE.suptitle(f"Per-colour LOCO hue error — sub-{subject} ({variant})\n"
                  f"tall bar = colour poorly interpolated ('leaving'); "
                  f"red line = mean+2SD", fontsize=10)
    figE.tight_layout(rect=[0, 0, 1, 0.96])
    fA = FIGDIR / f"percolor_error_sub-{subject}_{variant}.png"
    figE.savefig(fA, dpi=150); plt.close(figE)
    figC.suptitle(f"LOCO confusion (rows=true, cols=decoded) — sub-{subject} ({variant})",
                  fontsize=10)
    figC.tight_layout(rect=[0, 0, 1, 0.97])
    fB = FIGDIR / f"percolor_confusion_sub-{subject}_{variant}.png"
    figC.savefig(fB, dpi=150); plt.close(figC)
    jout = RESDIR / f"p4_percolor_sub-{subject}_{variant}.json"
    with open(jout, 'w') as fh:
        json.dump(out, fh, indent=1)
    print(f"saved: {fA}\n       {fB}\n       {jout}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--subject', default='08')
    ap.add_argument('--variant', default='matched', choices=['matched', 'native'])
    args = ap.parse_args()
    run(args.subject, args.variant)


if __name__ == '__main__':
    main()
