#!/usr/bin/env python3
"""S13 color-specificity permutation across the three preprocessing arms.

Closes the control S13 flags as outstanding:

    "The circular-shift control that separates these accounts was applied to the
     disparity endpoint (S2) and remains to be extended to the permutation
     reported here."

S13 reports that motion regression raised the number of FDR-surviving
color-specificity cells from 7 to 15 and leaves two readings open: motion
contributes label-independent variance that masks color structure, or the twelve
added regressors reshape the residual variance in a way that favours the observed
correspondence. The circular-shift arm carries the same twelve regressors with
their temporal alignment destroyed, so it produces the variance-inflation cost
without removing any motion-aligned variance. Comparing the three arms decides
between the readings:

    shift ~ original, regression differs   -> real motion-aligned variance
    shift ~ regression, both differ        -> cost of adding twelve regressors

Inputs are the per-arm outputs of disparity_frozen_permutation.py. Benjamini--
Hochberg is applied within each arm over the same 35 participant-by-ROI cells the
paper corrects over (HC 7 lacks sufficient hV4 coverage).

Usage
-----
    conda activate srm
    python scripts/color_specificity_arm_comparison.py
"""

import json
import os

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
VAL = os.path.dirname(_HERE)
RES = os.path.join(VAL, 'results')

ARMS = [('original', 'disparity_frozen_permutation_current'),
        ('regression', 'disparity_frozen_permutation_motreg'),
        ('shift', 'disparity_frozen_permutation_motshift')]
ROIS = ['V1', 'V2', 'V3', 'hV4']
CVD = {'sub-08': 'deutan', 'sub-09': 'protan'}


def bh(pvals):
    """Benjamini-Hochberg adjusted p-values."""
    p = np.asarray(pvals, float)
    n = len(p)
    order = np.argsort(p)
    q = np.empty(n)
    prev = 1.0
    for rank, idx in enumerate(order[::-1]):
        i = n - rank
        prev = min(prev, p[idx] * n / i)
        q[idx] = prev
    return q


def load(tag):
    with open(os.path.join(RES, f'{tag}.json')) as f:
        return json.load(f)['results']


def cells(res):
    """(subject, roi) -> p_perm over the frozen projection."""
    out = {}
    for roi in ROIS:
        fp = res[roi]['modes']['frozen_projection']
        # HC entries sit under hc/per_subject; CVD entries sit directly under cvd
        entries = dict(fp.get('hc', {}).get('per_subject', {}))
        entries.update({s: v for s, v in fp.get('cvd', {}).items() if isinstance(v, dict)})
        for sub, v in entries.items():
            if sub == 'sub-10' or 'p_perm' not in v:
                continue
            out[(sub, roi)] = float(v['p_perm'])
    return out


def main():
    tables = {}
    for name, tag in ARMS:
        path = os.path.join(RES, f'{tag}.json')
        if not os.path.exists(path):
            print(f'MISSING: {path} -- run disparity_frozen_permutation.py for this arm')
            return
        tables[name] = cells(load(tag))

    keys = sorted(set.intersection(*[set(t) for t in tables.values()]),
                  key=lambda k: (k[0], ROIS.index(k[1])))
    print(f'{len(keys)} participant-by-ROI cells common to all three arms\n')

    q = {}
    for name in tables:
        ps = [tables[name][k] for k in keys]
        q[name] = dict(zip(keys, bh(ps)))
        n_raw = sum(p < .05 for p in ps)
        n_fdr = sum(v < .05 for v in q[name].values())
        print(f'{name:11s} raw p<.05: {n_raw:2d}/{len(keys)}   BH q<.05: {n_fdr:2d}/{len(keys)}')

    print('\n' + '=' * 78)
    print(f'{"participant":12s} {"ROI":5s} ' +
          ' '.join(f'{n:>18s}' for n, _ in ARMS))
    print('-' * 78)
    for k in keys:
        sub, roi = k
        label = CVD.get(sub, sub)
        row = ' '.join(f'{tables[n][k]:8.3f} ({q[n][k]:5.3f})' for n, _ in ARMS)
        star = ' <' if sub in CVD else ''
        print(f'{label:12s} {roi:5s} {row}{star}')

    print('\n=== CVD cells ===')
    for sub, label in CVD.items():
        for roi in ROIS:
            k = (sub, roi)
            if k not in keys:
                continue
            o, r, s = (tables[n][k] for n, _ in ARMS)
            # S2 discriminator: regression minus shift isolates motion-aligned variance
            print(f'  {label:7s} {roi:4s} original {o:.3f} -> regression {r:.3f} '
                  f'(shift {s:.3f})   motion-attributable delta = {r - s:+.3f}')

    out = os.path.join(RES, 'color_specificity_arm_comparison.json')
    with open(out, 'w') as f:
        json.dump({'cells': {f'{a}|{b}': {n: dict(p=tables[n][(a, b)], q=q[n][(a, b)])
                                          for n, _ in ARMS} for a, b in keys},
                   'n_cells': len(keys),
                   'n_fdr': {n: int(sum(v < .05 for v in q[n].values())) for n in q}},
                  f, indent=1)
    print(f'\nwrote {out}')


if __name__ == '__main__':
    main()
