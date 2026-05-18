"""render_loco_canonical_4col.py — 4-col viz for LOCO-canonical filter.

Generates CORRECTED_LOCO_canonical_4col_sub-{08,09}.{png,pdf} using NEW labels.

LOCO-canonical filter (Phase 2 PRIMARY candidate per 2026-05-16 retrospective screen):
  sub-08 deutan: (β_s=38°, β_c=-14°) — V4 LOCO 2-comp fit, perm_p=0.004
  sub-09 protan: (β_s=6°,  β_c=-22°) — V4 LOCO 2-comp fit, perm_p=0.035

Under corrected labels:
  sub-08 P2a = 0.750 (passes hard screen P2a ≥ identity 0.688)
  sub-09 P2a = 0.975 (tied with identity — confirms R+C retinal-dominant prediction)
"""
from __future__ import annotations
import sys
from pathlib import Path

_THIS = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS))

import p2amax_option_C_visualize as P2C
from c3_relabel_p2a import SUB08_ORIG_NEW, hc_name_new, hc_match
from c3_relabel_both_subjects import SUB09_ORIG_NEW

OUT = _THIS.parent / 'results' / 'c3_relabel'


def _p2a_compute_corrected(bs, bc, axis, tmap):
    """P2a using NEW corrected labels (hc_name_new + hc_match)."""
    import numpy as np
    total = 0.0; ex = 0; details = []
    for theta in P2C.HUE_8:
        tcvd, dt = P2C.forward(float(theta), bs, bc, axis)
        pred = hc_name_new(tcvd); tgt = tmap[theta]
        s = hc_match(pred, tgt)
        total += s
        if pred == tgt:
            ex += 1
        details.append({'theta': theta, 'tcvd': tcvd, 'dt': dt,
                        'pred': pred, 'tgt': tgt, 'score': s})
    return total / 8.0, ex, details


def render_loco_canonical():
    # Backup
    orig_subs = {sid: P2C.OPTION_C['subjects'][sid].copy() for sid in ['08', '09']}
    orig_label = P2C.OPTION_C['label']
    orig_loss = P2C.OPTION_C['loss_plain']
    orig_prefix = P2C.PREFIX
    orig_out = P2C.OUT

    # Apply LOCO-canonical params
    P2C.OPTION_C['subjects']['08']['bs'] = 38.0
    P2C.OPTION_C['subjects']['08']['bc'] = -14.0
    P2C.OPTION_C['subjects']['08']['target'] = SUB08_ORIG_NEW
    P2C.OPTION_C['subjects']['09']['bs'] = 6.0
    P2C.OPTION_C['subjects']['09']['bc'] = -22.0
    P2C.OPTION_C['subjects']['09']['target'] = SUB09_ORIG_NEW
    P2C.OPTION_C['label'] = 'LOCO-canonical — V4 LOCO 2-comp fit (Phase 2 PRIMARY)'
    P2C.OPTION_C['loss_plain'] = (
        'L_fit = 1.0·L_vuln + 0.5·L_rank + 0.2·L_rdm + 0.1·L_smooth  '
        '@ V4 hV4 LOCO'
    )
    P2C.PREFIX = 'CORRECTED_LOCO_canonical_'
    P2C.OUT = OUT

    # Monkey-patch p2a_compute and hc_name with NEW corrected versions
    # so the title P2a and per-row sim/tgt strings use NEW 9-bin labels
    orig_p2a = P2C.p2a_compute
    orig_hcname = P2C.hc_name
    orig_match = P2C.hc_match_score
    P2C.p2a_compute = _p2a_compute_corrected
    P2C.hc_name = hc_name_new
    P2C.hc_match_score = hc_match

    try:
        OUT.mkdir(parents=True, exist_ok=True)
        for sid in ['08', '09']:
            print(f'  Rendering sub-{sid}: (β_s={P2C.OPTION_C["subjects"][sid]["bs"]:.0f}, '
                  f'β_c={P2C.OPTION_C["subjects"][sid]["bc"]:+.0f})')
            P2C.render_4col(sid)
    finally:
        for sid in ['08', '09']:
            P2C.OPTION_C['subjects'][sid] = orig_subs[sid]
        P2C.OPTION_C['label'] = orig_label
        P2C.OPTION_C['loss_plain'] = orig_loss
        P2C.PREFIX = orig_prefix
        P2C.OUT = orig_out
        P2C.p2a_compute = orig_p2a
        P2C.hc_name = orig_hcname
        P2C.hc_match_score = orig_match


if __name__ == '__main__':
    print('Rendering LOCO-canonical 4-col viz under CORRECTED labels')
    print('=' * 60)
    render_loco_canonical()
    print('\nDone. Files at:')
    for sid in ['08', '09']:
        for ext in ['png', 'pdf']:
            print(f'  {OUT}/CORRECTED_LOCO_canonical_4col_sub-{sid}.{ext}')
