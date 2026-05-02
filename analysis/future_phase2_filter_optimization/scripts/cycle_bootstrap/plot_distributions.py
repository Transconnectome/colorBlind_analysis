#!/usr/bin/env python3
"""plot_distributions.py — Cycle 1: violin/strip plots of ρ distributions.

Produces a multi-panel figure: per (roi, model) panel showing
- ρ_LOHO (jittered points) for sub-08, sub-09, sub-10
- ρ_HC_null (boxplot) overlaid
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

_SCRIPT_DIR = Path(__file__).resolve().parent
_PHASE2_DIR = _SCRIPT_DIR.parent.parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--results_dir', default=str(
        _PHASE2_DIR / 'results' / 'cycle_bootstrap' / 'main'))
    ap.add_argument('--out_path', default=str(
        _PHASE2_DIR / 'results' / 'cycle_bootstrap' / 'rho_distributions.png'))
    args = ap.parse_args()

    files = sorted(Path(args.results_dir).glob('sub-*_*_*.json'))
    bundles = {}
    for f in files:
        with open(f) as fh:
            d = json.load(fh)
        key = (d['roi'], d['model'])
        bundles.setdefault(key, []).append(d)

    n_panels = len(bundles)
    fig, axes = plt.subplots(1, n_panels, figsize=(4 * n_panels, 5),
                             squeeze=False)
    axes = axes[0]

    cmap = {'08': '#d62728', '09': '#1f77b4', '10': '#7f7f7f'}

    for ax, ((roi, model), datas) in zip(axes, bundles.items()):
        positions = []
        labels = []
        for i, d in enumerate(sorted(datas, key=lambda x: x['subject'])):
            sid = d['subject']
            rhos_loho = [d['all7']['rho']] + [r['rho'] for r in d.get('loho', [])]
            rhos_hc = [v['rho'] for v in d.get('hc_null', {}).values()]
            x = i * 2.0

            # CVD LOHO points
            ax.scatter([x] * len(rhos_loho),
                       rhos_loho + np.random.uniform(-0.04, 0.04, len(rhos_loho)),
                       c=cmap[sid], s=42, alpha=0.7, edgecolors='black',
                       linewidth=0.5, label=f'sub-{sid} LOHO' if i == 0 else None)
            # CVD all7 emphasis
            ax.scatter([x], [d['all7']['rho']], c=cmap[sid], s=120,
                       marker='*', edgecolors='black', linewidth=1.0)

            # HC null boxplot at x+1.0
            if rhos_hc:
                bp = ax.boxplot([rhos_hc], positions=[x + 0.6], widths=0.4,
                                patch_artist=True,
                                boxprops=dict(facecolor='#e0e0e0', alpha=0.5),
                                medianprops=dict(color='black'))
            positions.append(x + 0.3)
            labels.append(f"sub-{sid}\nz={d.get('all7', {}).get('rho', 0):.2f}")

        ax.set_xticks(positions)
        ax.set_xticklabels(labels)
        ax.axhline(0, c='gray', ls=':', lw=0.7)
        ax.set_title(f'{roi} · {model}')
        ax.set_ylabel(r'$\rho$ (Spearman)')
        ax.set_ylim(-0.4, 1.0)
        ax.grid(alpha=0.2)

    fig.suptitle(
        r'Cycle-1: $\rho_{\mathrm{LOHO}}$ (CVD) vs $\rho_{\mathrm{HC\,null}}$ (LOO HC as pseudo-CVD)',
        y=1.02)
    fig.tight_layout()
    fig.savefig(args.out_path, dpi=150, bbox_inches='tight')
    print(f'[saved] {args.out_path}')


if __name__ == '__main__':
    main()
