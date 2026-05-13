"""tier2_srm_rdm_visualize.py — SRM RDM matrices at TIER 2 argmin.

Tier 2 (V4-CCC + V1+V2 SRM RDM, wretrained) maximizes L_rdm cosine to V1+V2 SRM ΔRDM.
This script renders the same 4-panel view as best_srm_rdm_visualize.py but at
TIER 2 argmin (different from BEST). Output → CANDIDATE/tier2_v4ccc_srm_rdm/

TIER 2 argmins:
  sub-08: (50, +24)
  sub-09: (34, +44)
"""
from __future__ import annotations
import sys
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR))

import best_srm_rdm_visualize as bsrm
import matplotlib.pyplot as plt
import json

_PHASE2 = _THIS_DIR.parent
OUT = _PHASE2 / 'results' / 'CANDIDATE' / 'tier2_v4ccc_srm_rdm'
OUT.mkdir(parents=True, exist_ok=True)

# Override BEST argmins to TIER 2 argmins
bsrm.BEST = {
    '08': {'cvd_type': 'deutan', 'color': '#E07B2C', 'bs': 50.0, 'bc': 24.0},
    '09': {'cvd_type': 'protan', 'color': '#2D8E8B', 'bs': 34.0, 'bc': 44.0},
}
# Override output directory
bsrm.OUT = OUT


def main():
    print(f'TIER 2 argmins: {bsrm.BEST}')
    print(f'OUT: {bsrm.OUT}')

    # Combined 2x2 figure
    fig, axes = plt.subplots(4, 4, figsize=(14, 13), dpi=150)
    fig.suptitle('TIER 2 — V1/V2 SRM RDM at Tier 2 argmin (V4-CCC + L_rdm(V1+V2 SRM) wretrained)\n'
                 'Panel: Observed ΔRDM | Simulated ΔRDM | L2-norm disagreement | scatter',
                 fontsize=11, fontweight='bold', y=0.998)

    cos_summary = {}
    row = 0
    for sid in ['08', '09']:
        cos_summary[sid] = {}
        info = bsrm.BEST[sid]
        cell = bsrm.load_tier2_cell(sid, info['bs'], info['bc'])
        cos_summary[sid]['cos_V1'] = cell['cos_V1']
        cos_summary[sid]['cos_V2'] = cell['cos_V2']

        for roi in ['V1', 'V2']:
            cos_val = cell[f'cos_{roi}']
            bsrm.render_subject_roi(sid, roi,
                                    axes[row, 0], axes[row, 1], axes[row, 2], axes[row, 3],
                                    cos_val)
            print(f'  sub-{sid} {roi}: cos = {cos_val:+.3f}')
            row += 1

    plt.tight_layout()
    out_combined = OUT / 'TIER2_srm_rdm_combined.png'
    plt.savefig(out_combined, dpi=150, bbox_inches='tight')
    plt.savefig(str(out_combined).replace('.png', '.pdf'), bbox_inches='tight')
    plt.close()
    print(f'\nwrote {out_combined.name} (+ pdf)')

    # Per-subject-ROI standalone
    for sid in ['08', '09']:
        info = bsrm.BEST[sid]
        cell = bsrm.load_tier2_cell(sid, info['bs'], info['bc'])
        for roi in ['V1', 'V2']:
            cos_val = cell[f'cos_{roi}']
            fig, axes = plt.subplots(1, 4, figsize=(14, 3.5), dpi=150)
            bsrm.render_subject_roi(sid, roi,
                                    axes[0], axes[1], axes[2], axes[3], cos_val)
            plt.tight_layout()
            out = OUT / f'TIER2_srm_rdm_sub-{sid}_{roi}.png'
            plt.savefig(out, dpi=150, bbox_inches='tight')
            plt.savefig(str(out).replace('.png', '.pdf'), bbox_inches='tight')
            plt.close()
            print(f'wrote {out.name} (+ pdf)')

    # Save cos summary alongside TIER2_summary.json
    cos_json = OUT / 'TIER2_srm_rdm_cos_summary.json'
    with open(cos_json, 'w') as f:
        json.dump({
            'argmin': {sid: {'bs': bsrm.BEST[sid]['bs'], 'bc': bsrm.BEST[sid]['bc']}
                       for sid in ['08', '09']},
            'cos_values': cos_summary,
        }, f, indent=2)
    print(f'wrote {cos_json.name}')

    print('\n=== TIER 2 cos values at Tier 2 argmin ===')
    for sid in ['08', '09']:
        print(f"  sub-{sid}: cos_V1={cos_summary[sid]['cos_V1']:+.3f}  "
              f"cos_V2={cos_summary[sid]['cos_V2']:+.3f}")


if __name__ == '__main__':
    main()
