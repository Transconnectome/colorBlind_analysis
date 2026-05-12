"""HC specificity check for a 2-component filter (β_s, β_c).

Usage:
    python scripts/hc_specificity_check.py --beta_s 38 --beta_c -14 --cvd_type deutan --roi V4

Loads HC norms from SPECIFICITY_SUMMARY.json, computes CVD norm = sqrt(β_s²+β_c²),
bootstraps HC mean 10000 times, reports boot_frac and verdict.

Verdicts:
    ✓✓  boot_frac ≥ 0.975   (one-sided 95% CI excludes CVD norm)
    ~~  0.90 ≤ boot_frac < 0.975  (marginal)
    ✗   boot_frac < 0.90    (CVD inside HC CI)

§0 rule: DESCRIPTIVE ONLY — cannot override behavioral validation.
"""
import argparse
import json
import math
import os
import sys

import numpy as np

SUMMARY_JSON = os.path.join(
    os.path.dirname(__file__),
    "..", "results", "fits", "phase_a_2component_hc_sanity", "SPECIFICITY_SUMMARY.json"
)


def load_hc_norms(roi: str) -> list[float]:
    path = os.path.normpath(SUMMARY_JSON)
    if not os.path.exists(path):
        sys.exit(f"ERROR: SPECIFICITY_SUMMARY.json not found at {path}")
    with open(path) as f:
        data = json.load(f)
    roi_key = roi.upper()
    if roi_key not in data:
        sys.exit(f"ERROR: ROI '{roi_key}' not in summary. Available: {list(data.keys())}")
    norms = list(data[roi_key]["hc_norms"].values())
    return norms


def hc_specificity_check(beta_s: float, beta_c: float, hc_norms: list[float],
                          n_boot: int = 10000, rng_seed: int = 0) -> dict:
    cvd_norm = math.sqrt(beta_s ** 2 + beta_c ** 2)
    hc = np.array(hc_norms, dtype=float)

    rng = np.random.default_rng(rng_seed)
    boot_means = rng.choice(hc, size=(n_boot, len(hc)), replace=True).mean(axis=1)
    boot_frac = float((boot_means < cvd_norm).mean())

    if boot_frac >= 0.975:
        verdict = "✓✓"
    elif boot_frac >= 0.90:
        verdict = "~~"
    else:
        verdict = "✗"

    return {
        "beta_s": beta_s,
        "beta_c": beta_c,
        "cvd_norm": round(cvd_norm, 2),
        "hc_norms": list(hc_norms),
        "hc_mean": round(float(hc.mean()), 2),
        "hc_std": round(float(hc.std(ddof=1)), 2),
        "boot_frac": round(boot_frac, 4),
        "verdict": verdict,
        "n_boot": n_boot,
    }


def main():
    parser = argparse.ArgumentParser(description="HC specificity check for 2-component filter")
    parser.add_argument("--beta_s", type=float, required=True)
    parser.add_argument("--beta_c", type=float, required=True)
    parser.add_argument("--cvd_type", type=str, default="deutan",
                        choices=["deutan", "protan"], help="CVD type (informational only)")
    parser.add_argument("--roi", type=str, default="V4", choices=["V4", "V1"],
                        help="ROI for HC norm lookup")
    parser.add_argument("--n_boot", type=int, default=10000)
    args = parser.parse_args()

    hc_norms = load_hc_norms(args.roi)
    result = hc_specificity_check(args.beta_s, args.beta_c, hc_norms, n_boot=args.n_boot)

    print(f"\nHC Specificity Check — {args.cvd_type}, {args.roi}")
    print(f"  Filter: β_s={args.beta_s}, β_c={args.beta_c}  →  norm={result['cvd_norm']:.2f}°")
    print(f"  HC norms ({args.roi}): {[round(v,1) for v in result['hc_norms']]}")
    print(f"  HC mean={result['hc_mean']:.2f}°  std={result['hc_std']:.2f}°")
    print(f"  boot_frac={result['boot_frac']:.4f}  →  {result['verdict']}")
    print(f"\n  Interpretation (DESCRIPTIVE ONLY — §0 rule):")
    if result["verdict"] == "✓✓":
        print(f"  CVD norm ({result['cvd_norm']:.1f}°) exceeds HC bootstrap CI (p<0.025).")
    elif result["verdict"] == "~~":
        print(f"  CVD norm ({result['cvd_norm']:.1f}°) marginally above HC distribution.")
    else:
        print(f"  CVD norm ({result['cvd_norm']:.1f}°) inside HC CI — not distinct.")


if __name__ == "__main__":
    main()
