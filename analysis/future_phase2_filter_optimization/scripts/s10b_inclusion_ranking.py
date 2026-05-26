"""S10b: Inclusion combo ranking — fair test L_γ across 8 combos × 12 cells.

For each cell × combo:
  Load fitted param (g_best or β_s, β_c) from s7 cell JSON (k=5 subsets, 21 entries).
  For each subset's complement HC:
    Compute L_γ_test at fitted param using complement HC as baseline.
  Aggregate: median test L_γ across 21 subsets.

Cross-combo ranking uses *same* test metric (L_γ alone) → fair comparison.

8 inclusion combos:
  1. {} (empty: g=g_HC, no fit — baseline reference)
  2. {γ}
  3. {RDM}
  4. {LOCO}
  5. {γ, RDM}
  6. {γ, LOCO}
  7. {RDM, LOCO}
  8. {γ, RDM, LOCO}

Output: results/s10_inclusion/inclusion_ranking.json + ASCII table.
"""
import json
import sys
import time
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from rc_1dof import forward_rc
from two_comp import forward_2comp
from behav_loss import (
    load_jnd_per_pair, L_behav_gamma, PAIR_HUES, HC_JND_SUBJS,
)
from s8_loo_train_test import jnd_baseline_from_pool, DELTA_LAMBDA_BY_FAMILY

CELLS_DIR = SCRIPT_DIR.parent / "results" / "s7_loss_combo_subset"
OUT_DIR = SCRIPT_DIR.parent / "results" / "s10_inclusion"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Combo definitions for s7 lookup
COMBO_DEFS = {
    'γ':            ('single', 'L_gamma'),
    'RDM':          ('single', 'L_RDM'),
    'LOCO':         ('single', 'L_LOCO'),
    'γ+RDM':        ('combo',  'L_gamma+L_RDM'),
    'γ+LOCO':       ('combo',  'L_gamma+L_LOCO'),
    'RDM+LOCO':     ('combo',  'L_LOCO+L_RDM'),  # s7 key order
    'γ+RDM+LOCO':   ('combo',  'L_gamma+L_LOCO+L_RDM'),
}
# Note: s7 PAIR_COMBOS order has γ+LOCO, γ+RDM, LOCO+RDM
# TRIPLE_COMBO = (γ, LOCO, RDM) → key 'L_gamma+L_LOCO+L_RDM'

CVD_SUBJS = {'sub-08': 'deutan', 'sub-09': 'protan', 'sub-10': 'deutan'}


def compute_test_L_gamma(delta, cvd_jnd, complement_jnd_subjs):
    """Test L_γ at fitted param using complement HC subjects as baseline."""
    pool_jnd = [s for s in complement_jnd_subjs if s in HC_JND_SUBJS]
    if not pool_jnd:
        return None
    try:
        bl, sd = jnd_baseline_from_pool(pool_jnd)
    except Exception:
        return None
    if cvd_jnd is None:
        return None
    valid = {p: cvd_jnd[p] for p in bl.keys()
             if cvd_jnd.get(p) is not None and bl.get(p) is not None}
    if not valid:
        return None
    sd_d = {p: max(sd[p], 1e-3) for p in valid}
    return float(L_behav_gamma(delta, valid, bl, sd_d))


def extract_fit_params(fit_dict, model_key):
    """Return list of (model_label, delta_args) from a fit dict."""
    out = []
    if fit_dict is None:
        return out
    if model_key == 'rc':
        rc = fit_dict.get('rc')
        if isinstance(rc, dict):
            for src, res in rc.items():
                if res is not None and 'g_best' in res:
                    out.append((f'rc_{src}', {'g': res['g_best'], 'src': src}))
    elif model_key == '2comp':
        twc = fit_dict.get('2comp')
        if twc is not None and 'beta_s_best' in twc:
            out.append(('2comp', {'bs': twc['beta_s_best'], 'bc': twc['beta_c_best']}))
    return out


def get_fit_from_subset(subset_record, combo_label):
    """Extract fit dict from a subset record by combo label."""
    if combo_label == 'EMPTY':
        return None  # baseline: g=2 (full compensation, R+C), or skip
    kind, key = COMBO_DEFS[combo_label]
    if kind == 'single':
        return subset_record.get('single_fits', {}).get(key)
    elif kind == 'combo':
        return subset_record.get('combo_fits', {}).get(key)
    return None


def process_cell(cell_data):
    sub = cell_data['subject']
    family = cell_data['family']
    roi = cell_data['roi']
    dl_sources = DELTA_LAMBDA_BY_FAMILY[family]

    cvd_jnd = load_jnd_per_pair(sub) if sub != 'sub-10' or _has_jnd(sub) else None

    out = {}
    for combo_label in COMBO_DEFS:
        per_subset = {'rc_DPS_lit': [], 'rc_Boehm_low': [], 'rc_Boehm_mid': [],
                       'rc_JND_Lamb': [], '2comp': []}
        for s in cell_data['subsets']:
            if s['k'] != 5:
                continue
            complement = s['complement']
            fit_dict = get_fit_from_subset(s, combo_label)
            if fit_dict is None:
                continue
            # Iterate all model classes
            for model_key in ['rc', '2comp']:
                fits = extract_fit_params(fit_dict, model_key)
                for model_label, params in fits:
                    if model_label == '2comp':
                        delta = forward_2comp(params['bs'], params['bc'], family)
                    else:
                        dl = dl_sources[params['src']]
                        delta = forward_rc(dl, params['g'], family)
                    test_L = compute_test_L_gamma(delta, cvd_jnd, complement)
                    if model_label in per_subset:
                        per_subset[model_label].append(test_L)
        out[combo_label] = {}
        for model_label, vals in per_subset.items():
            valid = [v for v in vals if v is not None and np.isfinite(v)]
            if not valid:
                out[combo_label][model_label] = {'median': None, 'iqr': None, 'n': 0}
            else:
                arr = np.array(valid)
                out[combo_label][model_label] = {
                    'median': float(np.median(arr)),
                    'iqr': float(np.percentile(arr, 75) - np.percentile(arr, 25)),
                    'n': len(valid),
                }
    return {'subject': sub, 'family': family, 'roi': roi, 'combos': out}


def _has_jnd(sub):
    """Check if subject has JND file."""
    try:
        load_jnd_per_pair(sub)
        return True
    except Exception:
        return False


def main():
    cell_files = sorted(CELLS_DIR.glob("cell_*.json"))
    print(f"Found {len(cell_files)} cell files.")
    if len(cell_files) < 12:
        print(f"  WARNING: expected 12, missing some sub-10 cells likely (SLURM still running)")

    all_results = []
    for fp in cell_files:
        with open(fp) as f:
            cd = json.load(f)
        r = process_cell(cd)
        all_results.append(r)
        print(f"  Processed {r['subject']} {r['roi']}")

    out_file = OUT_DIR / "inclusion_ranking.json"
    with open(out_file, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nSaved: {out_file}")

    # Print ranking per cell: best combo (min median test L_γ) per model class
    print("\n" + "=" * 110)
    print("INCLUSION RANKING — median test L_γ per (combo, model)  (lower = better)")
    print("=" * 110)
    print(f"{'Cell':14s} | {'Model':10s} | " + " | ".join([f"{c:>10s}" for c in COMBO_DEFS]) + " | Best")
    print("-" * 110)

    # Aggregate rank per combo for top-3 identification
    rank_tally = {combo: [] for combo in COMBO_DEFS}

    for r in all_results:
        cell_key = f"{r['subject']} {r['roi']}"
        for model_label in ['rc_DPS_lit', 'rc_Boehm_mid', 'rc_JND_Lamb', '2comp']:
            row = f"{cell_key:14s} | {model_label:10s} | "
            vals = []
            for combo in COMBO_DEFS:
                v = r['combos'][combo].get(model_label, {}).get('median')
                vals.append(v)
                row += f"{v:>10.3f} | " if v is not None else f"{'NA':>10s} | "
            valid_vals = [(c, v) for c, v in zip(COMBO_DEFS, vals) if v is not None]
            if valid_vals:
                best_combo = min(valid_vals, key=lambda x: x[1])
                row += f"{best_combo[0]} ({best_combo[1]:.3f})"
                # Rank within cell-model
                sorted_combos = sorted(valid_vals, key=lambda x: x[1])
                for rank, (c, _) in enumerate(sorted_combos, start=1):
                    rank_tally[c].append(rank)
            print(row)

    # Aggregate
    print("\n" + "=" * 70)
    print("AGGREGATE — mean rank per combo (across all cell×model entries)")
    print("=" * 70)
    print(f"{'Combo':14s} | mean rank | n_entries | top-1 count")
    print("-" * 70)
    summary = {}
    for combo in COMBO_DEFS:
        ranks = rank_tally[combo]
        if ranks:
            mean_r = float(np.mean(ranks))
            top1 = sum(1 for r in ranks if r == 1)
            summary[combo] = {'mean_rank': round(mean_r, 2), 'n': len(ranks), 'top1_count': top1}
            print(f"{combo:14s} | {mean_r:9.2f} | {len(ranks):9d} | {top1:5d}")
        else:
            print(f"{combo:14s} | NA")
    # Top 3 by mean rank
    ranked = sorted([(c, summary[c]['mean_rank']) for c in summary], key=lambda x: x[1])
    print(f"\nTop 3 combos by mean rank: {[c for c, _ in ranked[:3]]}")
    summary['_top3'] = [c for c, _ in ranked[:3]]

    with open(OUT_DIR / "inclusion_ranking_summary.json", 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"Saved: {OUT_DIR / 'inclusion_ranking_summary.json'}")


if __name__ == "__main__":
    t0 = time.time()
    main()
    print(f"\nElapsed: {time.time() - t0:.1f}s")
