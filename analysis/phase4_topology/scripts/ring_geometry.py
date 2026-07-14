#!/usr/bin/env python3
"""
ring_geometry.py — Phase 4: 8-hue ring (stimulus-configuration) geometry.

Per subject x ROI, computes configuration-level metrics (participation ratio,
effective rank, planarity, in-plane isotropy = ellipse axis ratio, circular
correlation = ring-ordering preservation, optional Betti-1). Then:

  (1) SANITY CHECK (the agreed first gate): is the HC participation-ratio
      distribution separable from each CVD subject? If not, PR is reported as
      a "no-collapse" descriptive only, and the signal lives in anisotropy.
  (2) Group HC-vs-CVD (Welch, matching Phase-1 eigenspectrum convention).
  (3) Per-CVD Crawford & Howell single-case (project-canonical).
  (4) warp-vs-collapse verdict per CVD subject x ROI.

Outputs (flat, per Output Convention): results/ring_geometry/
  - ring_geometry_results.json   (per-subject + group + single-case + verdicts)
  - config.json
  - fig_ring_metrics.pdf         (PR / eff-rank / isotropy / circ-corr by ROI)
  - fig_rings.pdf                (8-hue ring in PC1-2 plane: HC example vs CVD)

Usage:
    python ring_geometry.py --baseline_dir <C010> --output_dir results/ring_geometry
"""

import argparse
import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from utils_topology import (
    load_amplitudes, save_config, get_subject_group,
    HC_SUBJECTS, CVD_SUBJECTS, ALL_SUBJECTS, ROIS, HUE_ANGLES, HAS_RIPSER,
    subject_ring_metrics, crawford_howell, welch,
)

# Metrics where a LOWER value indicates collapse (used for directional CH test).
COLLAPSE_LOWER = ['participation_ratio', 'effective_rank',
                  'in_plane_isotropy', 'abs_circular_corr']
GROUP_METRICS = ['participation_ratio', 'effective_rank', 'planarity',
                 'in_plane_isotropy', 'abs_circular_corr']

CVD_LABEL = {'08': 'sub-08 deutan', '09': 'sub-09 protan', '10': 'sub-10 deutan'}


def compute_all(baseline_dir):
    per_subject = {}
    for roi in ROIS:
        for subj in ALL_SUBJECTS:
            try:
                amp = load_amplitudes(baseline_dir, subj, roi)
            except FileNotFoundError:
                continue
            m = subject_ring_metrics(amp)
            m['group'] = get_subject_group(subj)
            per_subject[f'sub-{subj}_{roi}'] = m
    return per_subject


def verdict(sc_subj, hc_means):
    """HC-RELATIVE warp/collapse label from Crawford-Howell single-case tests.

    A collapse signal requires a CVD value SIGNIFICANTLY BELOW the HC mean
    (p<0.05) on a collapse-lower metric. Absolute thresholds are invalid here
    because HC itself is not a clean 2-D ring (PR~3-5, |cc| highly variable).
    """
    sig_below = []
    for k in COLLAPSE_LOWER:
        if k not in sc_subj:
            continue
        x = sc_subj[k]['value']
        if sc_subj[k]['p_two_sided'] < 0.05 and x < hc_means.get(k, np.inf):
            sig_below.append(k)
    if {'participation_ratio', 'effective_rank'} & set(sig_below) and \
       {'in_plane_isotropy', 'abs_circular_corr'} & set(sig_below):
        return 'collapse(E2)'
    if sig_below:
        return 'partial: ' + '+'.join(sig_below)
    return 'no sig. deviation (warp/indeterminate)'


def summarize(per_subject):
    out = {'group_statistics': {}, 'single_case': {}, 'sanity_check': {},
           'verdicts': {}}
    for roi in ROIS:
        hc = {k: [] for k in GROUP_METRICS}
        cvd = {}
        for subj in HC_SUBJECTS:
            key = f'sub-{subj}_{roi}'
            if key in per_subject:
                for k in GROUP_METRICS:
                    hc[k].append(per_subject[key][k])
        for subj in CVD_SUBJECTS:
            key = f'sub-{subj}_{roi}'
            if key in per_subject:
                cvd[subj] = {k: per_subject[key][k] for k in GROUP_METRICS}

        # (2) group Welch
        gs = {}
        for k in GROUP_METRICS:
            hc_v = [v for v in hc[k] if not np.isnan(v)]
            cvd_v = [cvd[s][k] for s in cvd if not np.isnan(cvd[s][k])]
            if len(hc_v) >= 2 and len(cvd_v) >= 2:
                t, p = welch(hc_v, cvd_v)
            else:
                t, p = np.nan, np.nan
            gs[k] = {'HC_mean': float(np.mean(hc_v)) if hc_v else np.nan,
                     'HC_std': float(np.std(hc_v, ddof=1)) if len(hc_v) > 1 else np.nan,
                     'CVD_mean': float(np.mean(cvd_v)) if cvd_v else np.nan,
                     't': t, 'p': p, 'n_HC': len(hc_v), 'n_CVD': len(cvd_v)}
        out['group_statistics'][roi] = gs

        # (3) per-CVD Crawford-Howell (directional for collapse-lower metrics)
        sc = {}
        for subj in cvd:
            sc[subj] = {}
            for k in GROUP_METRICS:
                hc_v = [v for v in hc[k] if not np.isnan(v)]
                x = cvd[subj][k]
                if len(hc_v) >= 2 and not np.isnan(x):
                    t, p = crawford_howell(x, hc_v)
                    sc[subj][k] = {'value': x, 't': t, 'p_two_sided': p}
        out['single_case'][roi] = sc

        # (1) sanity check on participation_ratio dynamic range
        hc_pr = [v for v in hc['participation_ratio'] if not np.isnan(v)]
        sep = {}
        if hc_pr:
            lo, hi = float(min(hc_pr)), float(max(hc_pr))
            for subj in cvd:
                x = cvd[subj]['participation_ratio']
                sep[subj] = {'value': x, 'below_HC_min': bool(x < lo),
                             'separable': bool(x < lo or x > hi)}
            out['sanity_check'][roi] = {'HC_PR_range': [lo, hi],
                                        'HC_PR_mean': float(np.mean(hc_pr)),
                                        'per_cvd': sep}

        # (4) verdicts (HC-relative, from single-case tests)
        hc_means = {k: float(np.mean([v for v in hc[k] if not np.isnan(v)]))
                    for k in GROUP_METRICS if any(not np.isnan(v) for v in hc[k])}
        vd = {}
        for subj in sc:
            vd[subj] = verdict(sc[subj], hc_means)
        out['verdicts'][roi] = vd
    return out


# ---------------------------------------------------------------------------
# Figures (matplotlib only; no seaborn)
# ---------------------------------------------------------------------------

def fig_metrics(per_subject, output_dir):
    metrics = [('participation_ratio', 'Participation ratio'),
               ('effective_rank', 'Effective rank'),
               ('in_plane_isotropy', 'In-plane isotropy (l2/l1)'),
               ('abs_circular_corr', '|circular corr| (ring ordering)')]
    fig, axes = plt.subplots(len(metrics), len(ROIS),
                             figsize=(3.2 * len(ROIS), 2.6 * len(metrics)))
    for r, (mk, mlabel) in enumerate(metrics):
        for c, roi in enumerate(ROIS):
            ax = axes[r, c]
            hc_v, cvd_pts = [], []
            for subj in HC_SUBJECTS:
                key = f'sub-{subj}_{roi}'
                if key in per_subject:
                    hc_v.append(per_subject[key][mk])
            for subj in CVD_SUBJECTS:
                key = f'sub-{subj}_{roi}'
                if key in per_subject:
                    cvd_pts.append((subj, per_subject[key][mk]))
            ax.scatter(np.zeros(len(hc_v)) + np.random.uniform(-.05, .05, len(hc_v)),
                       hc_v, c='0.6', s=28, label='HC' if r == 0 and c == 0 else None)
            colors = {'08': 'tab:red', '09': 'tab:blue', '10': 'tab:orange'}
            for subj, v in cvd_pts:
                ax.scatter([0.4], [v], c=colors.get(subj, 'k'), s=55, marker='D',
                           label=CVD_LABEL.get(subj) if r == 0 and c == 0 else None)
            ax.set_xlim(-0.4, 0.8)
            ax.set_xticks([])
            if c == 0:
                ax.set_ylabel(mlabel, fontsize=9)
            if r == 0:
                ax.set_title(roi if roi != 'V4' else 'hV4', fontsize=11)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center', ncol=4, fontsize=9,
               frameon=False, bbox_to_anchor=(0.5, 1.02))
    fig.tight_layout(rect=[0, 0, 1, 0.98])
    fig.savefig(Path(output_dir) / 'fig_ring_metrics.pdf', bbox_inches='tight')
    plt.close(fig)


def fig_rings(per_subject, output_dir):
    show = ['01', '08', '09', '10']  # HC example + 3 CVD
    titles = {'01': 'sub-01 HC (ex.)', **CVD_LABEL}
    hue_colors = plt.cm.hsv(np.linspace(0, 1, 8, endpoint=False))
    fig, axes = plt.subplots(len(ROIS), len(show),
                             figsize=(2.6 * len(show), 2.6 * len(ROIS)))
    for r, roi in enumerate(ROIS):
        for c, subj in enumerate(show):
            ax = axes[r, c]
            key = f'sub-{subj}_{roi}'
            if key not in per_subject:
                ax.axis('off')
                continue
            coords = np.array(per_subject[key]['coords2d'])
            # close the ring in stimulus order (already hue-ordered rows 0..7)
            loop = np.vstack([coords, coords[0]])
            ax.plot(loop[:, 0], loop[:, 1], '-', c='0.7', lw=1, zorder=1)
            ax.scatter(coords[:, 0], coords[:, 1], c=hue_colors, s=60,
                       edgecolors='k', linewidths=0.5, zorder=2)
            ax.set_aspect('equal')
            ax.set_xticks([]); ax.set_yticks([])
            iso = per_subject[key]['in_plane_isotropy']
            cc = per_subject[key]['abs_circular_corr']
            ax.set_xlabel(f'iso={iso:.2f} |cc|={cc:.2f}', fontsize=7)
            if r == 0:
                ax.set_title(titles.get(subj, subj), fontsize=9)
            if c == 0:
                ax.set_ylabel(roi if roi != 'V4' else 'hV4', fontsize=10)
    fig.tight_layout()
    fig.savefig(Path(output_dir) / 'fig_rings.pdf', bbox_inches='tight')
    plt.close(fig)


def print_report(summary):
    print('=' * 76)
    print('PHASE 4 — 8-hue ring (stimulus-configuration) geometry')
    print(f'  persistent homology (Betti-1): {"ON" if HAS_RIPSER else "OFF (ripser absent)"}')
    print('=' * 76)
    for roi in ROIS:
        print(f'\n### {roi if roi != "V4" else "hV4"}')
        sc = summary['sanity_check'].get(roi)
        if sc:
            lo, hi = sc['HC_PR_range']
            print(f'  [SANITY] HC PR range [{lo:.2f},{hi:.2f}] mean {sc["HC_PR_mean"]:.2f}')
            for subj, d in sc['per_cvd'].items():
                tag = 'SEPARABLE' if d['separable'] else 'overlap'
                print(f'     {CVD_LABEL[subj]:16s} PR={d["value"]:.2f}  [{tag}]')
        gs = summary['group_statistics'][roi]
        for k in ['participation_ratio', 'in_plane_isotropy', 'abs_circular_corr']:
            g = gs[k]
            print(f'  {k:20s} HC {g["HC_mean"]:.3f} vs CVD {g["CVD_mean"]:.3f}  '
                  f'Welch p={g["p"]:.3f}')
        vd = summary['verdicts'][roi]
        print('  VERDICT: ' + ', '.join(f'{CVD_LABEL[s].split()[0]}={v}'
                                        for s, v in vd.items()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--baseline_dir', required=True)
    ap.add_argument('--output_dir', default='results/ring_geometry')
    ap.add_argument('--seed', type=int, default=0)
    args = ap.parse_args()
    np.random.seed(args.seed)

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    per_subject = compute_all(args.baseline_dir)
    summary = summarize(per_subject)

    results = {'per_subject': per_subject, **summary}
    with open(out / 'ring_geometry_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    save_config(out, baseline_dir=str(args.baseline_dir),
                has_ripser=HAS_RIPSER, metrics=GROUP_METRICS)

    fig_metrics(per_subject, out)
    fig_rings(per_subject, out)
    print_report(summary)
    print(f'\nSaved -> {out}')


if __name__ == '__main__':
    main()
