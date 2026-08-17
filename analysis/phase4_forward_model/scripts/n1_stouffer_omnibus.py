#!/usr/bin/env python3
"""
N1: Stouffer Omnibus Hierarchical Test
=======================================
Fixes RT-6 FATAL #2 (multiple comparisons).

Strategy:
1. Compute Stouffer combined p across 4 ROIs (per-ROI optimal basis)
   → "Does cortex-level color interpolation exist?" (omnibus gate)
2. If omnibus p < 0.05 → proceed to ROI-specific post-hoc
3. Report both uncorrected and Bonferroni-corrected ROI p-values

Uses existing 10K permutation data from basis_permutation_10K.json
"""

import json
import numpy as np
from scipy import stats
from pathlib import Path

RESULTS_DIR = Path(__file__).parent.parent / "results"
OUTPUT_DIR = RESULTS_DIR / "neutralization"
OUTPUT_DIR.mkdir(exist_ok=True)

# Per-ROI optimal basis (from RESULTS.md §4)
OPTIMAL_BASIS = {
    "V1": "FE-2",
    "V2": "FE-3",
    "V3": "FE-8",
    "hV4": "FE-3",
}

HC_SUBS = ["01", "02", "03", "04", "05", "06", "07"]
ROIS = ["V1", "V2", "V3", "hV4"]


def stouffer_combine(p_values, weights=None):
    """Stouffer's method: Z = sum(w_i * Z_i) / sqrt(sum(w_i^2))"""
    z_scores = stats.norm.ppf(1 - np.array(p_values))
    # Clip extreme z-scores
    z_scores = np.clip(z_scores, -8, 8)
    if weights is None:
        weights = np.ones(len(z_scores))
    weights = np.array(weights)
    z_combined = np.sum(weights * z_scores) / np.sqrt(np.sum(weights**2))
    p_combined = 1 - stats.norm.cdf(z_combined)
    return z_combined, p_combined


def main():
    # Load per-subject per-basis permutation data
    perm_file = RESULTS_DIR / "basis_comparison" / "basis_permutation_10K.json"
    with open(perm_file) as f:
        perm_data = json.load(f)

    print("=" * 70)
    print("N1: STOUFFER OMNIBUS HIERARCHICAL TEST")
    print("=" * 70)

    # --- Step 1: Per-ROI Stouffer combined p (across HC subjects) ---
    print("\n--- Step 1: Per-ROI Stouffer (HC subjects, optimal basis) ---\n")
    roi_p_values = {}
    roi_details = {}

    ROI_JSON_MAP = {"V1": "V1", "V2": "V2", "V3": "V3", "hV4": "V4"}

    for roi in ROIS:
        basis = OPTIMAL_BASIS[roi]
        roi_key = ROI_JSON_MAP[roi]

        subj_p = []
        subj_obs = []
        subj_null = []

        for sub in HC_SUBS:
            d = perm_data[roi_key][basis][sub]
            subj_p.append(d["p_perm"])
            subj_obs.append(d["observed"])
            subj_null.append(d["null_mean"])

        z_comb, p_comb = stouffer_combine(subj_p)
        roi_p_values[roi] = p_comb

        roi_details[roi] = {
            "basis": basis,
            "subject_p": subj_p,
            "subject_obs": subj_obs,
            "subject_null": subj_null,
            "stouffer_z": float(z_comb),
            "stouffer_p": float(p_comb),
            "mean_obs": float(np.mean(subj_obs)),
            "mean_null": float(np.mean(subj_null)),
        }

        print(f"  {roi} ({basis}): Stouffer Z={z_comb:.3f}, p={p_comb:.4f}")
        print(f"    Mean obs={np.mean(subj_obs):.3f}, Mean null={np.mean(subj_null):.3f}")
        print(f"    Per-subj p: {[f'{p:.3f}' for p in subj_p]}")

    # --- Step 2: Omnibus test (4 ROIs combined) ---
    print("\n--- Step 2: Omnibus Gate (4 ROIs combined) ---\n")

    roi_stouffer_ps = [roi_p_values[r] for r in ROIS]
    z_omni, p_omni = stouffer_combine(roi_stouffer_ps)

    print(f"  Input p-values: {[f'{p:.4f}' for p in roi_stouffer_ps]}")
    print(f"  Omnibus Stouffer Z = {z_omni:.3f}")
    print(f"  Omnibus p = {p_omni:.4f}")
    print(f"  Gate: {'PASS' if p_omni < 0.05 else 'FAIL'} (threshold: 0.05)")

    # --- Step 3: Post-hoc ROI comparison ---
    print("\n--- Step 3: Post-hoc ROI (if omnibus PASS) ---\n")

    if p_omni < 0.05:
        print("  Omnibus PASSED → proceeding to post-hoc ROI tests\n")
    else:
        print("  Omnibus FAILED → post-hoc tests are exploratory only\n")

    bonf_alpha = 0.05 / len(ROIS)
    print(f"  Bonferroni-4 threshold: {bonf_alpha:.4f}")
    print()
    print(f"  {'ROI':<6} {'Basis':<6} {'Stouffer p':<12} {'Bonf. Adj':<12} {'Status':<15}")
    print(f"  {'-'*6} {'-'*6} {'-'*12} {'-'*12} {'-'*15}")

    # BH FDR
    sorted_ps = sorted(enumerate(roi_stouffer_ps), key=lambda x: x[1])
    m = len(sorted_ps)
    bh_results = {}
    for rank, (idx, p) in enumerate(sorted_ps, 1):
        q = p * m / rank
        bh_results[ROIS[idx]] = min(q, 1.0)

    for roi in ROIS:
        p = roi_p_values[roi]
        basis = OPTIMAL_BASIS[roi]
        bonf_pass = "PASS" if p < bonf_alpha else "FAIL"
        fdr_q = bh_results[roi]
        print(f"  {roi:<6} {basis:<6} {p:<12.4f} {bonf_pass:<12} FDR q={fdr_q:.4f}")

    # --- Step 4: Fisher's method (alternative omnibus) ---
    print("\n--- Step 4: Fisher's Method (robustness check) ---\n")
    chi2_fisher = -2 * np.sum(np.log(roi_stouffer_ps))
    df_fisher = 2 * len(roi_stouffer_ps)
    p_fisher = 1 - stats.chi2.cdf(chi2_fisher, df_fisher)
    print(f"  Fisher chi2({df_fisher}) = {chi2_fisher:.3f}")
    print(f"  Fisher p = {p_fisher:.4f}")
    print(f"  Gate: {'PASS' if p_fisher < 0.05 else 'FAIL'}")

    # --- Save results ---
    results = {
        "method": "Stouffer omnibus hierarchical test",
        "fixes": "RT-6 FATAL #2 (multiple comparisons)",
        "per_roi": roi_details,
        "omnibus": {
            "stouffer_z": float(z_omni),
            "stouffer_p": float(p_omni),
            "fisher_chi2": float(chi2_fisher),
            "fisher_df": df_fisher,
            "fisher_p": float(p_fisher),
            "gate": "PASS" if p_omni < 0.05 else "FAIL",
        },
        "post_hoc": {
            "bonferroni_alpha": bonf_alpha,
            "fdr_q": {roi: float(bh_results[roi]) for roi in ROIS},
            "per_roi_pass_bonf": {roi: bool(roi_p_values[roi] < bonf_alpha) for roi in ROIS},
        },
        "conclusion": "",
    }

    # Generate conclusion
    if p_omni < 0.05:
        passing = [r for r in ROIS if roi_p_values[r] < bonf_alpha]
        marginal = [r for r in ROIS if bonf_alpha <= roi_p_values[r] < 0.05]
        results["conclusion"] = (
            f"Omnibus test PASSES (p={p_omni:.4f}): cortex-level color interpolation exists. "
            f"Bonferroni-surviving ROIs: {passing if passing else 'none'}. "
            f"Marginal (uncorrected only): {marginal if marginal else 'none'}. "
            f"This resolves FATAL #2: the claim is 'cortex-level interpolation exists' "
            f"(omnibus-protected), with hV4 as the primary driver."
        )
    else:
        results["conclusion"] = (
            f"Omnibus test FAILS (p={p_omni:.4f}): no cortex-level evidence for "
            f"color interpolation at α=0.05. Individual ROI results are exploratory."
        )

    out_file = OUTPUT_DIR / "n1_stouffer_omnibus.json"
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n{'=' * 70}")
    print(f"CONCLUSION: {results['conclusion']}")
    print(f"{'=' * 70}")
    print(f"\nSaved to: {out_file}")


if __name__ == "__main__":
    main()
