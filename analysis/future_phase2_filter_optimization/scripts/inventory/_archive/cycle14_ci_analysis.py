#!/usr/bin/env python3
"""cycle14_ci_analysis.py — CI bootstrap + descriptive HC<CVD on Cycle 14.

Reads cycle14_v1_rdm_cross.json (now contains HC + CVD with family-symmetric
HC convention), and reports:
  - emp_p (rank-based)
  - boot_frac (fraction of 10K bootstrap HC means below CVD norm) — STRICT
  - HC<CVD descriptive (HC_mean vs CVD norm; HC_max vs CVD norm)
"""
import json
import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
JSON = ROOT / 'results' / 'cycles' / 'cycle14_v1_rdm_cross.json'
N_BOOT = 10000
SEED = 42


def boot_hc_mean_ci(hc_norms, n_boot=N_BOOT, ci=0.95):
    rng = np.random.default_rng(SEED)
    arr = np.array(hc_norms)
    n = len(arr)
    boot = rng.choice(arr, size=(n_boot, n), replace=True).mean(axis=1)
    lo = float(np.quantile(boot, (1 - ci) / 2))
    hi = float(np.quantile(boot, 1 - (1 - ci) / 2))
    return boot, lo, hi


def main():
    with open(JSON) as f:
        d = json.load(f)
    per_subj = d['per_subject']

    # Collect weight combos from any subject
    sample_subj = next(iter(per_subj.values()))
    weight_keys = list(sample_subj['cross_rdm_weights'].keys())

    print('=' * 78)
    print('Cycle 14 V1 RDM cross — CI bootstrap + HC<CVD descriptive')
    print('Family convention: HC fitted under both deutan AND protan, '
          'min-loss family kept')
    print('=' * 78)

    print(f"\n{'weight':<12}{'CVD':<7}{'norm':>7}{'HC_mean':>9}{'HC_CI':>14}"
          f"{'emp_p':>8}{'boot_frac':>11}{'HC<CVD':>9}{'verdict':>20}")

    for wkey in weight_keys:
        # Collect norms
        hc_norms = []
        cvd_norms = {}
        for subj, entry in per_subj.items():
            e = entry['cross_rdm_weights'].get(wkey)
            if not e:
                continue
            norm = float(np.sqrt(e['bs'] ** 2 + e['bc'] ** 2))
            if entry['role'] == 'HC':
                hc_norms.append(norm)
            else:
                cvd_norms[subj] = norm

        if not hc_norms:
            continue

        hc_arr = np.array(hc_norms)
        boot, lo, hi = boot_hc_mean_ci(hc_norms)
        hc_mean = float(hc_arr.mean())
        hc_max = float(hc_arr.max())

        print(f"\n  {wkey}: HC n={len(hc_norms)}, "
              f"mean={hc_mean:.1f}, sd={hc_arr.std():.1f}, "
              f"max={hc_max:.1f}, range=[{hc_arr.min():.1f}, {hc_max:.1f}]")
        print(f"    HC norms: {[f'{n:.0f}' for n in sorted(hc_norms, reverse=True)]}")

        for subj, cn in sorted(cvd_norms.items()):
            emp_p = float((hc_arr >= cn).sum() / len(hc_arr))
            boot_frac = float((boot < cn).sum() / len(boot))
            hc_less = 'Y' if hc_mean < cn else 'N'
            hc_max_less = 'Y' if hc_max < cn else 'N'

            # Verdict combining 3 levels
            if boot_frac >= 0.975:
                v = 'CI-strict ✓'
            elif emp_p <= 0.20:
                v = 'emp_p ✓'
            elif hc_max_less == 'Y':
                v = 'HC_max<CVD ✓'
            elif hc_less == 'Y':
                v = 'HC_mean<CVD ~'
            else:
                v = '✗ HC≥CVD'

            print(f"    sub-{subj}: norm={cn:.1f}  "
                  f"HC_CI=[{lo:.1f}, {hi:.1f}]  "
                  f"emp_p={emp_p:.2f}  boot_frac={boot_frac:.3f}  "
                  f"HC_mean<CVD={hc_less}  HC_max<CVD={hc_max_less}  → {v}")

    print('\n' + '=' * 78)
    print('Verdict legend:')
    print('  CI-strict ✓:    boot_frac ≥ 0.975 (CVD outside 95% CI of HC mean)')
    print('  emp_p ✓:        HC rank ≤ 20% above CVD (≤1/6 HC above)')
    print('  HC_max<CVD ✓:   CVD norm exceeds even HC maximum (descriptive)')
    print('  HC_mean<CVD ~:  CVD > HC mean but within HC range (weak desc)')
    print('  ✗:              CVD ≤ HC mean — no separation')
    print('=' * 78)


if __name__ == '__main__':
    main()
