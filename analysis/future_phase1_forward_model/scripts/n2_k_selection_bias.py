#!/usr/bin/env python3
"""
N2: K-Selection Bias Permutation Test
======================================
Fixes RT-6 SEVERE #3 (K-dependent gap = HC-optimized search artifact).

Question: When HC/CVD labels are shuffled, does the same K-optimization
          procedure produce similar gap reduction? If yes → gap reduction
          is expected by chance under exhaustive K search.

Method:
1. Load per-subject LOCO voxel_corr for each K from subject_k results
2. For each permutation (n_perm=10000):
   a. Randomly assign 7 subjects as "pseudo-HC", 3 as "pseudo-CVD"
   b. Find optimal K for each ROI (maximize pseudo-HC mean LOCO)
   c. Compute gap (pseudo-HC - pseudo-CVD) under FE-6 and under optimal K
   d. Compute gap_reduction = (FE6_gap - optK_gap) / FE6_gap
3. Compare observed gap_reduction to null distribution
"""

import json
import numpy as np
from pathlib import Path
from itertools import combinations
from scipy import stats

RESULTS_DIR = Path(__file__).parent.parent / "results"
OUTPUT_DIR = RESULTS_DIR / "neutralization"
OUTPUT_DIR.mkdir(exist_ok=True)

# All subjects
ALL_SUBS = [f"{i:02d}" for i in range(1, 11)]
HC_SUBS = [f"{i:02d}" for i in range(1, 8)]
CVD_SUBS = ["08", "09", "10"]

ROIS = ["V1", "V2", "V3", "hV4"]
ROI_DIR_MAP = {"V1": "V1", "V2": "V2", "V3": "V3", "hV4": "V4"}

# K values tested
K_VALUES = [2, 3, 4, 5, 6, 8, 10, 12]

# Known per-ROI optimal K (from HC-optimized search)
OPTIMAL_K = {"V1": 2, "V2": 3, "V3": 8, "hV4": 3}

N_PERM = 10000
SEED = 42


def load_subject_k_data():
    """Load LOCO voxel_corr for each subject × ROI × K."""
    data = {}  # data[roi][sub][k] = loco_voxel_corr

    for roi in ROIS:
        roi_dir = ROI_DIR_MAP[roi]
        data[roi] = {}

        for sub in ALL_SUBS:
            fname = RESULTS_DIR / "subject_k" / f"sub-{sub}_{roi_dir}_subject_k.json"
            if not fname.exists():
                print(f"  WARNING: {fname} not found")
                continue

            with open(fname) as f:
                d = json.load(f)

            data[roi][sub] = {}
            per_k = d.get("per_k", d.get("k_results", {}))
            for k_str, k_data in per_k.items():
                k = int(k_str.replace("K", "").replace("k", ""))
                if k in K_VALUES:
                    val = k_data.get("loco_mean", k_data.get("loco_voxel_corr", np.nan))
                    data[roi][sub][k] = val

    return data


def compute_gap_reduction(data, hc_subs, cvd_subs, roi):
    """Compute gap under FE-6 and under optimal K for given group assignment."""
    # FE-6 gap
    hc_fe6 = [data[roi][s].get(6, np.nan) for s in hc_subs if s in data[roi]]
    cvd_fe6 = [data[roi][s].get(6, np.nan) for s in cvd_subs if s in data[roi]]

    hc_fe6 = [x for x in hc_fe6 if not np.isnan(x)]
    cvd_fe6 = [x for x in cvd_fe6 if not np.isnan(x)]

    if len(hc_fe6) == 0 or len(cvd_fe6) == 0:
        return np.nan, np.nan, np.nan, 6

    fe6_gap = np.mean(hc_fe6) - np.mean(cvd_fe6)

    # Find optimal K (maximize HC mean LOCO)
    best_k = 6
    best_hc_mean = np.mean(hc_fe6)

    for k in K_VALUES:
        hc_k = [data[roi][s].get(k, np.nan) for s in hc_subs if s in data[roi]]
        hc_k = [x for x in hc_k if not np.isnan(x)]
        if len(hc_k) > 0:
            m = np.mean(hc_k)
            if m > best_hc_mean:
                best_hc_mean = m
                best_k = k

    # Gap under optimal K
    hc_optk = [data[roi][s].get(best_k, np.nan) for s in hc_subs if s in data[roi]]
    cvd_optk = [data[roi][s].get(best_k, np.nan) for s in cvd_subs if s in data[roi]]

    hc_optk = [x for x in hc_optk if not np.isnan(x)]
    cvd_optk = [x for x in cvd_optk if not np.isnan(x)]

    if len(hc_optk) == 0 or len(cvd_optk) == 0:
        return fe6_gap, np.nan, np.nan, best_k

    optk_gap = np.mean(hc_optk) - np.mean(cvd_optk)

    # Gap reduction
    if abs(fe6_gap) < 1e-10:
        reduction = 0.0
    else:
        reduction = (fe6_gap - optk_gap) / abs(fe6_gap)

    return fe6_gap, optk_gap, reduction, best_k


def main():
    print("=" * 70)
    print("N2: K-SELECTION BIAS PERMUTATION TEST")
    print("=" * 70)

    # Load data
    print("\nLoading subject_k data...")
    data = load_subject_k_data()

    # Check data availability
    for roi in ROIS:
        n_subs = len(data[roi])
        n_ks = len(K_VALUES)
        print(f"  {roi}: {n_subs} subjects, {n_ks} K values")

    # Observed gap reduction (true HC/CVD labels)
    print("\n--- Observed Gap Reduction (True Labels) ---\n")
    observed = {}
    for roi in ROIS:
        fe6_gap, optk_gap, reduction, best_k = compute_gap_reduction(
            data, HC_SUBS, CVD_SUBS, roi
        )
        observed[roi] = {
            "fe6_gap": fe6_gap,
            "optk_gap": optk_gap,
            "reduction": reduction,
            "best_k": best_k,
        }
        print(f"  {roi}: FE-6 gap={fe6_gap:+.3f}, K*={best_k} gap={optk_gap:+.3f}, "
              f"reduction={reduction*100:.1f}%")

    # Permutation test
    print(f"\n--- Permutation Test (n={N_PERM}, label shuffle) ---\n")
    rng = np.random.RandomState(SEED)

    null_reductions = {roi: [] for roi in ROIS}
    null_fe6_gaps = {roi: [] for roi in ROIS}
    null_optk_gaps = {roi: [] for roi in ROIS}
    null_best_ks = {roi: [] for roi in ROIS}

    for i in range(N_PERM):
        if (i + 1) % 2000 == 0:
            print(f"  Permutation {i+1}/{N_PERM}...")

        # Shuffle labels: random 7 as "HC", 3 as "CVD"
        perm = rng.permutation(ALL_SUBS)
        pseudo_hc = list(perm[:7])
        pseudo_cvd = list(perm[7:])

        for roi in ROIS:
            fe6_gap, optk_gap, reduction, best_k = compute_gap_reduction(
                data, pseudo_hc, pseudo_cvd, roi
            )
            null_reductions[roi].append(reduction)
            null_fe6_gaps[roi].append(fe6_gap)
            null_optk_gaps[roi].append(optk_gap)
            null_best_ks[roi].append(best_k)

    # Results
    print("\n--- Results ---\n")
    print(f"  {'ROI':<6} {'Obs Red%':<10} {'Null Mean%':<10} {'Null SD%':<10} "
          f"{'p(>=obs)':<10} {'Interpretation':<30}")
    print(f"  {'-'*6} {'-'*10} {'-'*10} {'-'*10} {'-'*10} {'-'*30}")

    results = {}
    for roi in ROIS:
        obs_red = observed[roi]["reduction"]
        null_arr = np.array(null_reductions[roi])
        null_arr = null_arr[~np.isnan(null_arr)]

        if len(null_arr) == 0:
            print(f"  {roi:<6} {'N/A':<10} {'N/A':<10} {'N/A':<10} {'N/A':<10}   NO DATA")
            results[roi] = {"error": "no valid null samples"}
            continue

        null_mean = np.mean(null_arr)
        null_sd = np.std(null_arr)

        # p-value: proportion of null >= observed
        if np.isnan(obs_red):
            p_val = np.nan
        else:
            p_val = np.mean(null_arr >= obs_red)

        if p_val > 0.05:
            interp = "EXPECTED BY CHANCE"
        else:
            interp = "EXCEEDS CHANCE"

        print(f"  {roi:<6} {obs_red*100:>8.1f}% {null_mean*100:>8.1f}% "
              f"{null_sd*100:>8.1f}% {p_val:>8.4f}   {interp}")

        results[roi] = {
            "observed_reduction": float(obs_red),
            "observed_fe6_gap": float(observed[roi]["fe6_gap"]),
            "observed_optk_gap": float(observed[roi]["optk_gap"]),
            "observed_best_k": int(observed[roi]["best_k"]),
            "null_reduction_mean": float(null_mean),
            "null_reduction_sd": float(null_sd),
            "null_reduction_95ci": [
                float(np.percentile(null_arr, 2.5)),
                float(np.percentile(null_arr, 97.5)),
            ],
            "p_value": float(p_val),
            "n_perm": N_PERM,
            "interpretation": interp,
            "null_fe6_gap_mean": float(np.nanmean(null_fe6_gaps[roi])),
            "null_optk_gap_mean": float(np.nanmean(null_optk_gaps[roi])),
        }

    # Overall conclusion
    print("\n" + "=" * 70)
    all_expected = all(results[r]["p_value"] > 0.05 for r in ROIS)
    any_exceeds = any(results[r]["p_value"] < 0.05 for r in ROIS)

    if all_expected:
        conclusion = (
            "ALL ROIs: gap reduction under K-optimization is EXPECTED BY CHANCE. "
            "The 54-78% gap reduction reported is a statistical artifact of "
            "exhaustive K search on HC-optimized basis. HC-CVD gap magnitude "
            "under any specific K remains valid, but the 'gap reduction' narrative "
            "should be abandoned."
        )
    elif any_exceeds:
        exceeding = [r for r in ROIS if results[r]["p_value"] < 0.05]
        conclusion = (
            f"ROIs {exceeding} show gap reduction EXCEEDING chance levels. "
            f"The K-dependent gap reduction in these ROIs is not purely artifactual. "
            f"Other ROIs show expected-by-chance reduction."
        )
    else:
        conclusion = "Mixed results. See per-ROI details."

    print(f"CONCLUSION: {conclusion}")
    print("=" * 70)

    output = {
        "method": "K-selection bias permutation test",
        "fixes": "RT-6 SEVERE #3 (K-dependent gap = HC-optimized search artifact)",
        "n_perm": N_PERM,
        "seed": SEED,
        "per_roi": results,
        "conclusion": conclusion,
    }

    out_file = OUTPUT_DIR / "n2_k_selection_bias.json"
    with open(out_file, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nSaved to: {out_file}")


if __name__ == "__main__":
    main()
