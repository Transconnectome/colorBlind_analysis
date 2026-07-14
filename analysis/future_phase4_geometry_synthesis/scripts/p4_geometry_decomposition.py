#!/usr/bin/env python3
"""p4_geometry_decomposition.py — GAP2/3/4: mechanistic decomposition (Q1).

Within each representation (srm, fe_latent) and ROI, decompose the geometry
DIFFERENCE into interpretable parts, in the NATIVE coord space (8xK):
  - CVD-nofilter  vs  HC-ref     -> how the CVD baseline geometry differs from HC
  - filter(win/opt) vs nofilter  -> what the filter changes

Each comparison reports (utils_p4.procrustes_decompose):
  global_gain   : isotropic dispersion ratio (||cond||/||ref||)  -> global gain
  aniso_ref/cond: eig1/eig2 aspect ratio     -> anisotropy (opponent-gain axis signature)
  disparity     : shape residual after gain+rotation removed -> genuine reconfiguration
  reflection    : axis flip

Tied to the project premise (cortical opponent GAIN vs stimulus dilation): a
difference dominated by gain/aniso (not disparity) is consistent with a gain
account; a difference dominated by disparity is a reconfiguration.
DESCRIPTIVE / hypothesis-generating only (N=2, 8 points). NOT proof of gain.

Run:  python p4_geometry_decomposition.py --subject 08 --variant matched
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

COMPARISONS = [
    ('cvd_vs_hc:nofilter', 'hc_ref', 'nofilter'),
    ('cvd_vs_hc:window', 'hc_ref', 'window'),
    ('cvd_vs_hc:optimal', 'hc_ref', 'optimal'),
    ('filter_vs_nf:window', 'nofilter', 'window'),
    ('filter_vs_nf:optimal', 'nofilter', 'optimal'),
]


def _coords(d1, roi, repr_, key):
    cond = None if key == 'hc_ref' else key
    return U.get_coords(d1, roi, repr_, cond)


def run(subject, variant):
    d1 = U.load_stage1(subject, variant)
    hc_self = U.hc_self_consistency()
    out = {'subject': subject, 'variant': variant,
           'hc_self_consistency': hc_self, 'reprs': {}}
    for repr_ in ['srm', 'fe_latent']:
        out['reprs'][repr_] = {}
        for roi in U.ROIS:
            out['reprs'][repr_][roi] = {}
            for label, ref_key, cond_key in COMPARISONS:
                Xref = _coords(d1, roi, repr_, ref_key)
                Xcond = _coords(d1, roi, repr_, cond_key)
                dec = U.procrustes_decompose(Xref, Xcond)
                # perm null on the shape residual (native coords)
                _, p, _ = U.label_perm_null(Xref, Xcond, n_perm=2000)
                dec['perm_p'] = p
                out['reprs'][repr_][roi][label] = dec

    # ---- figure: per repr, grouped bars of gain & disparity across ROIs ----
    for repr_ in ['srm', 'fe_latent']:
        fig, axes = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
        x = np.arange(len(U.ROIS))
        w = 0.15
        for k, (label, _, _) in enumerate(COMPARISONS):
            gains = [out['reprs'][repr_][roi][label]['global_gain'] for roi in U.ROIS]
            disp = [out['reprs'][repr_][roi][label]['disparity'] for roi in U.ROIS]
            axes[0].bar(x + (k - 2) * w, gains, w, label=label)
            axes[1].bar(x + (k - 2) * w, disp, w, label=label)
        axes[0].axhline(1.0, color='k', lw=0.8, ls='--')
        axes[0].set_ylabel('global_gain (||cond||/||ref||)\n>1 dilation, <1 compression')
        axes[1].set_ylabel('shape disparity (reconfiguration)')
        axes[1].set_xticks(x)
        axes[1].set_xticklabels([f"{U.ROI_DISPLAY[r]}\nHCρ={hc_self.get(r):.2f}"
                                 if hc_self.get(r) is not None else U.ROI_DISPLAY[r]
                                 for r in U.ROIS])
        axes[0].legend(fontsize=7, ncol=5, loc='upper right')
        axes[0].set_title(f"Geometry decomposition — sub-{subject} ({variant}), "
                          f"repr={repr_}\ngain-dominated => opponent-gain-consistent; "
                          f"disparity-dominated => reconfiguration (DESCRIPTIVE, N=2)",
                          fontsize=9)
        fig.tight_layout()
        f = FIGDIR / f"decomposition_sub-{subject}_{variant}_{repr_}.png"
        fig.savefig(f, dpi=150); plt.close(fig)
        print(f"saved: {f}")

    jout = RESDIR / f"p4_decomposition_sub-{subject}_{variant}.json"
    with open(jout, 'w') as fh:
        json.dump(out, fh, indent=1)
    print(f"saved: {jout}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--subject', default='08')
    ap.add_argument('--variant', default='matched', choices=['matched', 'native'])
    args = ap.parse_args()
    run(args.subject, args.variant)


if __name__ == '__main__':
    main()
