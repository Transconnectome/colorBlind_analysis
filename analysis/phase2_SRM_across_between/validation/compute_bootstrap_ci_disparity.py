#!/usr/bin/env python3
"""
Bootstrap 95% CIs for Phase 2 SRM Disparity Results

Computes subject-level percentile bootstrap CIs for:
  1. HC-HC mean disparity
  2. CVD-HC mean disparity
  3. Separation (CVD-HC minus HC-HC)
  4. Hedges' g (bias-corrected effect size)
  5. RDM correlation means (HC-HC, HC-CVD, CVD-CVD)

Input: 4 ROI result JSONs from results/c010/combined_20260209/
Output: bootstrap_ci_results.json + console summary table

Usage:
    python compute_bootstrap_ci_disparity.py
"""

import json
import numpy as np
from pathlib import Path

# ============================================================================
# CONFIG
# ============================================================================

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results" / "c010" / "combined_20260209"
ALIGNED_DIR = RESULTS_DIR.parent / "combined_with_aligned"  # aligned amplitudes dir
ROIS = ["V1", "V2", "V3", "V4"]
ROI_DISPLAY = {"V1": "V1", "V2": "V2", "V3": "V3", "V4": "hV4"}
N_BOOTSTRAP = 10000
SEED = 42
CI_LEVEL = 95

# ============================================================================
# FUNCTIONS
# ============================================================================

def hedges_g(group1, group2):
    """Compute Hedges' g (bias-corrected effect size for small samples)."""
    n1, n2 = len(group1), len(group2)
    m1, m2 = np.mean(group1), np.mean(group2)
    # Pooled SD (using n-1 for unbiased)
    s_pooled = np.sqrt(((n1 - 1) * np.var(group1, ddof=1) +
                         (n2 - 1) * np.var(group2, ddof=1)) / (n1 + n2 - 2))
    if s_pooled == 0:
        return 0.0
    d = (m2 - m1) / s_pooled
    # Hedges' correction factor for small samples
    df = n1 + n2 - 2
    correction = 1 - (3 / (4 * df - 1))
    return d * correction


def bootstrap_group_stats(hc_vals, cvd_vals, n_bootstrap=10000, seed=42):
    """
    Bootstrap CIs for group means, separation, and effect size.

    Parameters
    ----------
    hc_vals : array-like, HC subject disparities (n=7)
    cvd_vals : array-like, CVD subject disparities (n=3)

    Returns
    -------
    dict with observed values and bootstrap 95% CIs
    """
    rng = np.random.RandomState(seed)
    hc = np.array(hc_vals)
    cvd = np.array(cvd_vals)
    n_hc, n_cvd = len(hc), len(cvd)

    # Observed statistics
    obs_hc_mean = np.mean(hc)
    obs_cvd_mean = np.mean(cvd)
    obs_separation = obs_cvd_mean - obs_hc_mean
    obs_g = hedges_g(hc, cvd)

    # Bootstrap
    boot_hc_means = np.zeros(n_bootstrap)
    boot_cvd_means = np.zeros(n_bootstrap)
    boot_separations = np.zeros(n_bootstrap)
    boot_gs = np.zeros(n_bootstrap)

    for i in range(n_bootstrap):
        hc_boot = hc[rng.choice(n_hc, size=n_hc, replace=True)]
        cvd_boot = cvd[rng.choice(n_cvd, size=n_cvd, replace=True)]

        boot_hc_means[i] = np.mean(hc_boot)
        boot_cvd_means[i] = np.mean(cvd_boot)
        boot_separations[i] = boot_cvd_means[i] - boot_hc_means[i]
        boot_gs[i] = hedges_g(hc_boot, cvd_boot)

    alpha = (100 - CI_LEVEL) / 2
    lo, hi = alpha, 100 - alpha

    return {
        "hc_mean": {
            "observed": float(obs_hc_mean),
            "ci_lower": float(np.percentile(boot_hc_means, lo)),
            "ci_upper": float(np.percentile(boot_hc_means, hi))
        },
        "cvd_mean": {
            "observed": float(obs_cvd_mean),
            "ci_lower": float(np.percentile(boot_cvd_means, lo)),
            "ci_upper": float(np.percentile(boot_cvd_means, hi))
        },
        "separation": {
            "observed": float(obs_separation),
            "ci_lower": float(np.percentile(boot_separations, lo)),
            "ci_upper": float(np.percentile(boot_separations, hi))
        },
        "hedges_g": {
            "observed": float(obs_g),
            "ci_lower": float(np.percentile(boot_gs, lo)),
            "ci_upper": float(np.percentile(boot_gs, hi))
        }
    }


def bootstrap_rdm_correlations(aligned_file, n_bootstrap=10000, seed=42):
    """
    Load aligned amplitudes, compute pairwise RDM correlations,
    then bootstrap CIs for HC-HC, HC-CVD, CVD-CVD means.
    """
    from scipy.stats import spearmanr
    from itertools import combinations

    data = np.load(aligned_file, allow_pickle=True).item()
    hc_keys = sorted([k for k in data if int(k.split('-')[1]) <= 7])
    cvd_keys = sorted([k for k in data if int(k.split('-')[1]) > 7])

    # Compute RDMs
    rdms = {}
    for key, patterns in data.items():
        rdm = 1 - np.corrcoef(patterns)
        mask = np.triu(np.ones(rdm.shape, dtype=bool), k=1)
        rdms[key] = rdm[mask]

    # Pairwise correlations
    hc_hc_rs, hc_cvd_rs, cvd_cvd_rs = [], [], []
    all_keys = hc_keys + cvd_keys
    for ki, kj in combinations(all_keys, 2):
        r, _ = spearmanr(rdms[ki], rdms[kj])
        if ki in hc_keys and kj in hc_keys:
            hc_hc_rs.append(r)
        elif ki in cvd_keys and kj in cvd_keys:
            cvd_cvd_rs.append(r)
        else:
            hc_cvd_rs.append(r)

    rng = np.random.RandomState(seed)
    hc_hc_arr = np.array(hc_hc_rs)
    hc_cvd_arr = np.array(hc_cvd_rs)
    cvd_cvd_arr = np.array(cvd_cvd_rs) if cvd_cvd_rs else None

    alpha = (100 - CI_LEVEL) / 2
    lo, hi = alpha, 100 - alpha

    result = {}

    # Bootstrap HC-HC (21 pairs)
    boot_means = np.zeros(n_bootstrap)
    n = len(hc_hc_arr)
    for i in range(n_bootstrap):
        boot_means[i] = np.mean(hc_hc_arr[rng.choice(n, size=n, replace=True)])
    result["hc_hc_rdm"] = {
        "observed": float(np.mean(hc_hc_arr)),
        "ci_lower": float(np.percentile(boot_means, lo)),
        "ci_upper": float(np.percentile(boot_means, hi)),
        "n_pairs": int(n)
    }

    # Bootstrap HC-CVD (21 pairs)
    boot_means = np.zeros(n_bootstrap)
    n = len(hc_cvd_arr)
    for i in range(n_bootstrap):
        boot_means[i] = np.mean(hc_cvd_arr[rng.choice(n, size=n, replace=True)])
    result["hc_cvd_rdm"] = {
        "observed": float(np.mean(hc_cvd_arr)),
        "ci_lower": float(np.percentile(boot_means, lo)),
        "ci_upper": float(np.percentile(boot_means, hi)),
        "n_pairs": int(n)
    }

    # Bootstrap CVD-CVD (3 pairs)
    if cvd_cvd_arr is not None and len(cvd_cvd_arr) > 0:
        boot_means = np.zeros(n_bootstrap)
        n = len(cvd_cvd_arr)
        for i in range(n_bootstrap):
            boot_means[i] = np.mean(cvd_cvd_arr[rng.choice(n, size=n, replace=True)])
        result["cvd_cvd_rdm"] = {
            "observed": float(np.mean(cvd_cvd_arr)),
            "ci_lower": float(np.percentile(boot_means, lo)),
            "ci_upper": float(np.percentile(boot_means, hi)),
            "n_pairs": int(n)
        }

    return result


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 80)
    print("Bootstrap 95% CIs for Phase 2 SRM Disparity")
    print(f"n_bootstrap={N_BOOTSTRAP}, seed={SEED}, CI={CI_LEVEL}%")
    print("=" * 80)

    all_results = {}

    for roi in ROIS:
        roi_display = ROI_DISPLAY[roi]
        print(f"\n--- {roi_display} ---")

        # Load disparity values
        json_path = RESULTS_DIR / f"{roi}_procrustes_srm_results.json"
        if not json_path.exists():
            print(f"  SKIP: {json_path} not found")
            continue

        with open(json_path) as f:
            data = json.load(f)

        hc_vals = data["results"]["disparities"]["hc_to_hc_reference"]["values"]
        cvd_vals = data["results"]["disparities"]["cvd_to_hc_reference"]["values"]

        print(f"  HC values (n={len(hc_vals)}): {[f'{v:.3f}' for v in hc_vals]}")
        print(f"  CVD values (n={len(cvd_vals)}): {[f'{v:.3f}' for v in cvd_vals]}")

        # Bootstrap disparity stats
        disp_ci = bootstrap_group_stats(hc_vals, cvd_vals, N_BOOTSTRAP, SEED)

        print(f"  HC mean:     {disp_ci['hc_mean']['observed']:.4f} "
              f"[{disp_ci['hc_mean']['ci_lower']:.4f}, {disp_ci['hc_mean']['ci_upper']:.4f}]")
        print(f"  CVD mean:    {disp_ci['cvd_mean']['observed']:.4f} "
              f"[{disp_ci['cvd_mean']['ci_lower']:.4f}, {disp_ci['cvd_mean']['ci_upper']:.4f}]")
        print(f"  Separation:  {disp_ci['separation']['observed']:.4f} "
              f"[{disp_ci['separation']['ci_lower']:.4f}, {disp_ci['separation']['ci_upper']:.4f}]")
        print(f"  Hedges' g:   {disp_ci['hedges_g']['observed']:.3f} "
              f"[{disp_ci['hedges_g']['ci_lower']:.3f}, {disp_ci['hedges_g']['ci_upper']:.3f}]")

        roi_result = {"disparity": disp_ci}

        # Bootstrap RDM correlations (if aligned amplitudes exist)
        aligned_path = ALIGNED_DIR / f"{roi}_procrustes_aligned_amplitudes.npy"
        if aligned_path.exists():
            print(f"  Computing RDM bootstrap CIs from aligned amplitudes...")
            rdm_ci = bootstrap_rdm_correlations(aligned_path, N_BOOTSTRAP, SEED)
            for key in ["hc_hc_rdm", "hc_cvd_rdm", "cvd_cvd_rdm"]:
                if key in rdm_ci:
                    r = rdm_ci[key]
                    print(f"  {key}: {r['observed']:.3f} "
                          f"[{r['ci_lower']:.3f}, {r['ci_upper']:.3f}] (n={r['n_pairs']})")
            roi_result["rdm_correlations"] = rdm_ci
        else:
            print(f"  No aligned amplitudes found at {aligned_path}")

        all_results[roi_display] = roi_result

    # ========================================================================
    # SUMMARY TABLE
    # ========================================================================

    print("\n" + "=" * 80)
    print("PUBLICATION TABLE: Bootstrap 95% CIs for SRM Disparity")
    print("=" * 80)

    header = f"{'ROI':<5} | {'HC-HC [95% CI]':<28} | {'CVD-HC [95% CI]':<28} | {'Separation [95% CI]':<28} | {'g [95% CI]':<24} | {'p':<8}"
    print(header)
    print("-" * len(header))

    # Load p-values from original results
    for roi in ROIS:
        roi_display = ROI_DISPLAY[roi]
        if roi_display not in all_results:
            continue

        d = all_results[roi_display]["disparity"]

        # Get p-value from original JSON
        json_path = RESULTS_DIR / f"{roi}_procrustes_srm_results.json"
        with open(json_path) as f:
            orig = json.load(f)
        p_val = orig["results"]["statistical_tests"]["hc_vs_cvd"]["p_value"]

        hc = d["hc_mean"]
        cvd = d["cvd_mean"]
        sep = d["separation"]
        g = d["hedges_g"]

        print(f"{roi_display:<5} | "
              f"{hc['observed']:.3f} [{hc['ci_lower']:.3f}, {hc['ci_upper']:.3f}]  | "
              f"{cvd['observed']:.3f} [{cvd['ci_lower']:.3f}, {cvd['ci_upper']:.3f}]  | "
              f"{sep['observed']:.3f} [{sep['ci_lower']:.3f}, {sep['ci_upper']:.3f}]  | "
              f"{g['observed']:.2f} [{g['ci_lower']:.2f}, {g['ci_upper']:.2f}] | "
              f"{p_val:.4f}")

    print("\n" + "=" * 80)
    print("RDM Correlation Bootstrap 95% CIs")
    print("=" * 80)
    header2 = f"{'ROI':<5} | {'HC-HC [95% CI]':<28} | {'HC-CVD [95% CI]':<28} | {'CVD-CVD [95% CI]':<28}"
    print(header2)
    print("-" * len(header2))

    for roi in ROIS:
        roi_display = ROI_DISPLAY[roi]
        if roi_display not in all_results or "rdm_correlations" not in all_results[roi_display]:
            continue
        rdm = all_results[roi_display]["rdm_correlations"]
        hh = rdm.get("hc_hc_rdm", {})
        hc_cvd = rdm.get("hc_cvd_rdm", {})
        cc = rdm.get("cvd_cvd_rdm", {})

        parts = [f"{roi_display:<5}"]
        for r in [hh, hc_cvd, cc]:
            if r:
                parts.append(f"{r['observed']:.3f} [{r['ci_lower']:.3f}, {r['ci_upper']:.3f}]")
            else:
                parts.append("N/A")
        print(f"{parts[0]} | {parts[1]:<28} | {parts[2]:<28} | {parts[3]:<28}")

    # Save results
    output_path = Path(__file__).resolve().parent / "bootstrap_ci_results.json"
    save_data = {
        "config": {
            "n_bootstrap": N_BOOTSTRAP,
            "seed": SEED,
            "ci_level": CI_LEVEL,
            "source": str(RESULTS_DIR)
        },
        "results": all_results
    }
    with open(output_path, "w") as f:
        json.dump(save_data, f, indent=2)
    print(f"\nResults saved to {output_path}")


if __name__ == "__main__":
    main()
