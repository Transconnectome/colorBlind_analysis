"""phase3_behav_loss_search.py — behavior-anchored loss for 2-component filter.

Motivation
----------
Existing LOCO loss (l_fit) minimizes against HC vulnerability pattern and rank,
which selects (β_s=38, β_c=−14) — "Canonical". But behavioral measurements show
V4-only (β_s=38, β_c=+7) outperforms Canonical (P1 2+3p/8 vs 2+2p/8) and is the
ONLY filter that corrects C8 magenta (sub-08 reports "pinkish purple" vs
Canonical's "unchanged deep blue").

Structural reason (verified separately):
    pre_image_C8 under V4-only = 353.2°   (pink region)
    pre_image_C8 under Canonical = 285.5° (deep purple, sub-08 perceives as blue)
Sub-08's only path to a magenta-family percept is through her pink-percept zone
(near C1 = 0°). Therefore the filter MUST land pre_image(c8) in [340°, 360°].

This script defines a behavior-anchored loss that encodes pre-image targets +
anti-collapse penalties (no information from HC vulnerability), then grid-searches
the 2-component parameter space (β_s, β_c) and reports the optimum. We test
whether V4-only neighborhood (β_s=38, β_c≈+7) emerges as the minimum.

Loss components (all in same angular units, squared deg):
    L_C8  = (pre_image(315°) − target_C8 = 355°)²
    L_C1  = (pre_image(0°)   − target_C1 = 0°)²
    L_C7  = (pre_image(270°) − target_C7 = 245°)²     (sub-08 perceives 245° as blue)
    L_C5C6_collapse = max(0, 30 − |pre_image(180°) − pre_image(225°)|)²
    L_C3C4_collapse = max(0, 30 − |pre_image(90°)  − pre_image(135°)|)²
    L_total = w_C8 · L_C8 + w_C1 · L_C1 + w_C7 · L_C7
            + w_col · (L_C5C6_collapse + L_C3C4_collapse)

The C8 weight dominates because it captures the unique failure of Canonical.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
import numpy as np

_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR))
sys.path.insert(0, str(_THIS_DIR / 'forward_models'))

from forward_models.two_component import forward_2comp, pre_image_2comp


# Vectorized pre-image via forward lookup table (1° resolution).
# 30x faster than scipy.brentq for grid search.
_FINE_GRID = np.arange(0.0, 360.0, 1.0)


def fast_pre_image(theta_target: float, cvd_type: str,
                   beta_s: float, beta_c: float) -> float:
    """Fast pre-image via 1°-grid forward lookup. Returns theta_pre in [0, 360)."""
    forwards = np.empty_like(_FINE_GRID)
    for i, t in enumerate(_FINE_GRID):
        f, _ = forward_2comp(float(t), cvd_type, beta_s, beta_c)
        forwards[i] = f
    diff = (forwards - theta_target + 180.0) % 360.0 - 180.0
    return float(_FINE_GRID[int(np.argmin(np.abs(diff)))])

OUTDIR = _THIS_DIR.parent / 'results' / 'phase3_candidates' / 'behav_loss'
OUTDIR.mkdir(parents=True, exist_ok=True)

CVD = 'deutan'

# --- Behavioral targets derived from raw_behav.md (sub-08) ---
# Where pre_image must land so that, when rendered, sub-08 perceives the
# HC-equivalent percept.
TARGETS = {
    0:   {'target': 0.0,   'weight': 1.0,  'desc': 'C1 red:    sub-08 perceives ~0° as pink-red'},
    270: {'target': 245.0, 'weight': 1.0,  'desc': 'C7 blue:   sub-08 perceives 240-290° as blue'},
    315: {'target': 355.0, 'weight': 3.0,  'desc': 'C8 magenta: sub-08 ONLY perceives magenta-family near pink zone'},
}
COLLAPSE_PAIRS = [
    {'pair': (90, 135),  'threshold': 30.0, 'desc': 'C3-C4 must not collapse (yellow vs green)'},
    {'pair': (180, 225), 'threshold': 30.0, 'desc': 'C5-C6 must not collapse (cyan vs sky)'},
]
W_COLLAPSE = 0.5


def wrap360(a: float) -> float:
    return a % 360.0


def angular_diff(a: float, b: float) -> float:
    """Unsigned circular distance in degrees."""
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


def behav_loss(beta_s: float, beta_c: float, fast: bool = True) -> dict:
    """Compute behavior-anchored loss + components for (β_s, β_c).

    fast=True: use 1°-grid lookup (≈10ms per call). Used for grid search.
    fast=False: use scipy.brentq pre_image_2comp (≈2s per call). Used for top-k refinement.
    """
    pre = {}
    if fast:
        # Build forward LUT once, query 8 angles
        forwards = np.empty_like(_FINE_GRID)
        for i, t in enumerate(_FINE_GRID):
            f, _ = forward_2comp(float(t), CVD, beta_s, beta_c)
            forwards[i] = f
        for theta in [0, 45, 90, 135, 180, 225, 270, 315]:
            diff = (forwards - theta + 180.0) % 360.0 - 180.0
            pre[theta] = float(_FINE_GRID[int(np.argmin(np.abs(diff)))])
    else:
        for theta in [0, 45, 90, 135, 180, 225, 270, 315]:
            p, _ = pre_image_2comp(float(theta), CVD, beta_s, beta_c)
            pre[theta] = p

    L_C1 = angular_diff(pre[0],   TARGETS[0]['target'])   ** 2
    L_C7 = angular_diff(pre[270], TARGETS[270]['target']) ** 2
    L_C8 = angular_diff(pre[315], TARGETS[315]['target']) ** 2

    cps = []
    for cp in COLLAPSE_PAIRS:
        a, b = cp['pair']
        gap = angular_diff(pre[a], pre[b])
        deficit = max(0.0, cp['threshold'] - gap)
        cps.append(deficit ** 2)
    L_col = sum(cps)

    total = (TARGETS[0]['weight']   * L_C1
           + TARGETS[270]['weight'] * L_C7
           + TARGETS[315]['weight'] * L_C8
           + W_COLLAPSE             * L_col)

    return {
        'beta_s': beta_s, 'beta_c': beta_c, 'L_total': float(total),
        'L_C1': float(L_C1), 'L_C7': float(L_C7), 'L_C8': float(L_C8),
        'L_collapse': float(L_col),
        'pre_C1': float(pre[0]),   'pre_C7': float(pre[270]),
        'pre_C8': float(pre[315]),
        'pre_C3': float(pre[90]),  'pre_C4': float(pre[135]),
        'pre_C5': float(pre[180]), 'pre_C6': float(pre[225]),
        'gap_C3C4': float(angular_diff(pre[90], pre[135])),
        'gap_C5C6': float(angular_diff(pre[180], pre[225])),
    }


def main():
    BS_GRID = np.arange(0, 51, 2)
    BC_GRID = np.arange(-50, 51, 2)
    print(f'Grid: β_s {len(BS_GRID)} × β_c {len(BC_GRID)} = '
          f'{len(BS_GRID)*len(BC_GRID)} cells')

    results = []
    for bs in BS_GRID:
        for bc in BC_GRID:
            r = behav_loss(float(bs), float(bc))
            results.append(r)
        print(f'  β_s={bs:>4.0f} done')

    # Find minimum
    results.sort(key=lambda r: r['L_total'])
    best = results[0]
    print(f"\nGlobal min: (β_s={best['beta_s']}, β_c={best['beta_c']}), "
          f"L_total={best['L_total']:.2f}")
    print(f"  L_C1={best['L_C1']:.1f}, L_C7={best['L_C7']:.1f}, "
          f"L_C8={best['L_C8']:.1f}, L_collapse={best['L_collapse']:.1f}")
    print(f"  pre_C8={best['pre_C8']:.1f}, pre_C1={best['pre_C1']:.1f}")

    # Top 10
    print('\nTop 10:')
    for i, r in enumerate(results[:10]):
        print(f"  {i+1:>2}. β_s={r['beta_s']:>4.0f} β_c={r['beta_c']:>+5.0f} "
              f"L={r['L_total']:>7.2f}  L_C8={r['L_C8']:>6.1f}  "
              f"pre_C8={r['pre_C8']:>6.1f}  pre_C1={r['pre_C1']:>6.1f}")

    # Reference scores
    print('\nReference points:')
    for label, bs, bc in [('Canonical', 38, -14), ('V4-only OLD', 38, 7),
                          ('Cycle14', 58, -36), ('Cycle12', 68, -38)]:
        r = behav_loss(float(bs), float(bc))
        rank = sum(1 for x in results if x['L_total'] < r['L_total']) + 1
        print(f"  {label:>16} (β_s={bs},β_c={bc:+d}): L={r['L_total']:>7.2f}, "
              f"pre_C8={r['pre_C8']:>6.1f}, rank={rank}/{len(results)}")

    # Save
    out = {
        'method': 'behavior_anchored_loss_search',
        'targets': TARGETS,
        'collapse_pairs': COLLAPSE_PAIRS,
        'w_collapse': W_COLLAPSE,
        'grid_bounds': {'beta_s': [0, 50, 2], 'beta_c': [-50, 50, 2]},
        'global_min': best,
        'top10': results[:10],
        'reference_scores': {
            label: behav_loss(float(bs), float(bc))
            for label, bs, bc in [('Canonical', 38, -14),
                                  ('V4-only OLD', 38, 7),
                                  ('Cycle14', 58, -36),
                                  ('Cycle12', 68, -38)]
        },
        'all_results': results,
    }
    with open(OUTDIR / 'behav_loss_landscape.json', 'w') as f:
        json.dump(out, f, indent=2)
    print(f"\nWrote {OUTDIR / 'behav_loss_landscape.json'}")


if __name__ == '__main__':
    main()
