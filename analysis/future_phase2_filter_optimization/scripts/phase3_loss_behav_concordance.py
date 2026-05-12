"""phase3_loss_behav_concordance.py — §0-compliant loss × behavior selection.

Pipeline (§0-compliant):
1. Each neural loss in loss_inventory.csv selects (β_s, β_c) for sub-08.
2. For each selection, compute the 2-component forward map at 8 colors.
3. Predicted CVD percept = HC color name at θ_perceived.
4. Compare to sub-08's actual reported HC-equivalent percept (SUB08_ORIGINAL_HC_EQUIV).
5. P2a_concordance = sum of hc_match_score over 8 colors.
6. Rank losses by behavioral concordance.

Behavioral data is USED AS GROUND TRUTH FOR SELECTING AMONG LOSSES (§0 path).
NO new loss is created; existing neural losses are scored against behavior.

Output: results/phase3_candidates/loss_behav_concordance/concordance_table.json
"""
from __future__ import annotations
import csv
import json
import sys
from pathlib import Path
import numpy as np

_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR))
sys.path.insert(0, str(_THIS_DIR / 'forward_models'))

from forward_models.two_component import forward_2comp
from phase3_candidate_analysis_v2 import (
    hc_name, hc_match_score, SUB08_ORIGINAL_HC_EQUIV
)

OUTDIR = _THIS_DIR.parent / 'results' / 'phase3_candidates' / 'loss_behav_concordance'
OUTDIR.mkdir(parents=True, exist_ok=True)

INVENTORY_CSV = _THIS_DIR.parent / 'results' / 'inventory' / 'loss_inventory.csv'

CVD = 'deutan'
TIER1 = [0, 45, 90, 135, 180, 225, 270, 315]


def load_sub08_selections() -> list[dict]:
    rows = []
    with open(INVENTORY_CSV) as f:
        reader = csv.DictReader(f)
        for r in reader:
            if r['subject'] != 'sub-08':
                continue
            if r['roi'] not in ('V4', 'V4+V1'):
                continue
            rows.append({
                'loss_variant': r['loss_variant'],
                'description': r['description'],
                'roi': r['roi'],
                'beta_s': float(r['beta_s']),
                'beta_c': float(r['beta_c']),
                'best_value': r['best_value'],
                'norm': float(r['norm_raw']),
            })
    return rows


def score_filter(beta_s: float, beta_c: float) -> dict:
    """Compute behavioral concordance + per-color details."""
    rows = []
    total = 0.0
    exact = 0
    family_match = 0
    for theta in TIER1:
        theta_cvd, dt = forward_2comp(float(theta), CVD, beta_s, beta_c)
        pred_name = hc_name(theta_cvd)
        target_name = SUB08_ORIGINAL_HC_EQUIV[theta]
        score = hc_match_score(pred_name, target_name)
        total += score
        if pred_name == target_name:
            exact += 1
        # family-level match
        from phase3_candidate_analysis_v2 import HC_FAMILY
        if HC_FAMILY.get(pred_name) == HC_FAMILY.get(target_name):
            family_match += 1
        rows.append({
            'theta': theta, 'theta_cvd': round(theta_cvd, 2),
            'dt': round(dt, 2),
            'pred_name': pred_name, 'target_name': target_name,
            'score': round(score, 3),
        })
    return {
        'beta_s': beta_s, 'beta_c': beta_c,
        'concordance_total': round(total, 3),
        'concordance_per8': round(total / 8.0, 3),
        'exact_matches': exact,
        'family_matches': family_match,
        'per_color': rows,
    }


def main():
    losses = load_sub08_selections()
    print(f"Loaded {len(losses)} loss variants for sub-08")

    results = []
    for L in losses:
        s = score_filter(L['beta_s'], L['beta_c'])
        results.append({
            'loss': L['loss_variant'],
            'roi': L['roi'],
            'beta_s': L['beta_s'],
            'beta_c': L['beta_c'],
            'norm': L['norm'],
            'concordance': s['concordance_per8'],
            'exact': s['exact_matches'],
            'family': s['family_matches'],
            'per_color_pred': [r['pred_name'] for r in s['per_color']],
        })

    # Sort by concordance (descending)
    results.sort(key=lambda r: -r['concordance'])

    print()
    print(f"{'rank':>4}  {'loss':>30}  {'ROI':>6}  {'β_s':>5}  {'β_c':>5}  {'conc':>5}  {'exact':>5}  {'fam':>4}")
    print('-' * 90)
    for i, r in enumerate(results):
        print(f"  {i+1:>2}  {r['loss']:>30}  {r['roi']:>6}  "
              f"{r['beta_s']:>5.0f}  {r['beta_c']:>+5.0f}  "
              f"{r['concordance']:>5.3f}  {r['exact']:>5}  {r['family']:>4}")

    # Show top 3 predictions in detail
    print()
    print('=== TOP 3 detailed predictions ===')
    for r in results[:3]:
        s = score_filter(r['beta_s'], r['beta_c'])
        print(f"\n{r['loss']} (β_s={r['beta_s']}, β_c={r['beta_c']:+}):")
        print(f"  concordance={r['concordance']:.3f}, exact={r['exact']}/8, family={r['family']}/8")
        for pc in s['per_color']:
            print(f"  c{TIER1.index(pc['theta'])+1} θ={pc['theta']:>3}  "
                  f"θ_cvd={pc['theta_cvd']:>6.1f}  "
                  f"pred={pc['pred_name']:>13}  target={pc['target_name']:>13}  "
                  f"score={pc['score']:.2f}")

    # Reference: Canonical, V4-only OLD, Cycle14
    print()
    print('=== Reference filters ===')
    for label, bs, bc in [('Canonical', 38, -14), ('V4-only OLD', 38, 7),
                          ('Cycle14', 58, -36)]:
        s = score_filter(bs, bc)
        rank = sum(1 for x in results if x['concordance'] > s['concordance_per8']) + 1
        print(f"  {label:>14} (β_s={bs}, β_c={bc:+}): conc={s['concordance_per8']:.3f}, "
              f"exact={s['exact_matches']}, family={s['family_matches']}, "
              f"rank≈{rank}/{len(results)}")

    out = {
        'method': 'loss_behav_concordance',
        'description': 'Score each neural loss filter against sub-08 behavioral targets (§0-compliant).',
        'ground_truth': 'SUB08_ORIGINAL_HC_EQUIV from phase3_candidate_analysis_v2.py',
        'n_losses': len(results),
        'ranked_results': results,
        'reference_scores': {
            label: score_filter(bs, bc)
            for label, bs, bc in [('Canonical', 38, -14),
                                  ('V4-only_OLD', 38, 7),
                                  ('Cycle14', 58, -36)]
        },
    }
    with open(OUTDIR / 'concordance_table.json', 'w') as f:
        json.dump(out, f, indent=2)
    print(f"\nWrote {OUTDIR / 'concordance_table.json'}")


if __name__ == '__main__':
    main()
