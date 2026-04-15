#!/usr/bin/env python3
"""
Analyze LOCO vulnerability profiles as direct CVD biomarker.

Instead of fitting a cone-shift model (which overfits to HC),
directly test whether CVD subjects' LOCO vulnerability profiles
are outliers relative to the HC distribution.

Methods:
1. Per-color Crawford & Howell (2002) modified t-test
2. Multivariate: Mahalanobis distance from HC centroid
3. Profile variance / range as univariate summary
4. Permutation-based group comparison

Uses vuln_target data from experiment_b_weight_sweep results.
"""
import json
import numpy as np
from pathlib import Path
from scipy import stats
from itertools import combinations

# ── Data from Experiment B ──────────────────────────────────────────
VULN_DATA = {
    # HC subjects
    '01': [0.9192, 0.9381, 0.6693, 0.7075, 0.8820, 0.9304, 0.8697, 0.9479],
    '02': [0.9637, 0.8708, 0.9256, 0.8021, 0.9502, 0.9504, 0.9653, 0.8980],
    '03': [0.9244, 0.8833, 0.9365, 0.9881, 0.9528, 0.8716, 0.9883, 0.6753],
    '04': [0.9429, 0.8840, 0.9004, 0.8467, 0.9532, 0.7194, 0.9033, 0.8040],
    '05': [0.9477, 0.9258, 0.7856, 0.8456, 0.9123, 0.9219, 0.7758, 0.6875],
    '06': [0.9549, 0.9233, 0.8365, 0.8993, 0.9149, 0.9633, 0.8356, 0.9306],
    '07': [0.9825, 0.7469, 0.7695, 0.3552, 0.9261, 0.7672, 0.9327, 0.7985],
    # CVD subjects
    '08': [0.9929, 0.9049, 0.8847, 0.1540, 0.9750, 0.4866, 0.8923, 0.0924],
    '09': [0.8770, 0.9751, 0.7834, 0.8314, 0.6731, 0.7451, 0.6040, 0.9158],
    '10': [0.8202, 0.7973, 0.8317, 0.8332, 0.8896, 0.8980, 0.7013, 0.7430],
}

COLOR_NAMES = ['c1_red', 'c2_orange', 'c3_yellow', 'c4_green',
               'c5_cyan', 'c6_blue', 'c7_purple', 'c8_magenta']

HC_IDS = ['01', '02', '03', '04', '05', '06', '07']
CVD_IDS = ['08', '09', '10']
CVD_TYPES = {'08': 'deutan', '09': 'protan', '10': 'normal'}


def crawford_howell(x, control_scores):
    """Crawford & Howell (2002) modified t-test for single case."""
    n = len(control_scores)
    mean_c = np.mean(control_scores)
    std_c = np.std(control_scores, ddof=1)
    if std_c < 1e-10:
        return 0.0, 1.0
    t = (x - mean_c) / (std_c * np.sqrt((n + 1) / n))
    p = 2 * stats.t.sf(abs(t), df=n - 1)  # two-tailed
    return float(t), float(p)


def mahalanobis_distance(x, X_ref):
    """Mahalanobis distance of x from centroid of X_ref."""
    mu = np.mean(X_ref, axis=0)
    cov = np.cov(X_ref, rowvar=False)
    # Regularize for numerical stability (n=7, d=8 → singular)
    cov_reg = cov + 0.01 * np.eye(cov.shape[0])
    diff = x - mu
    try:
        d2 = diff @ np.linalg.solve(cov_reg, diff)
        return float(np.sqrt(max(d2, 0)))
    except np.linalg.LinAlgError:
        return float('nan')


def profile_range(vuln):
    """Range of vulnerability profile (max - min)."""
    return float(np.max(vuln) - np.min(vuln))


def profile_cv(vuln):
    """Coefficient of variation of vulnerability profile."""
    return float(np.std(vuln) / np.mean(vuln)) if np.mean(vuln) > 0 else 0.0


def permutation_test_mahalanobis(cvd_data, hc_data, n_perm=10000):
    """
    Test if CVD subjects are farther from HC centroid than expected
    by permuting group labels.
    """
    all_data = np.vstack([hc_data, cvd_data])
    n_hc = hc_data.shape[0]
    n_total = all_data.shape[0]

    # Observed: mean Mahalanobis of CVD subjects
    obs_distances = []
    for i in range(cvd_data.shape[0]):
        d = mahalanobis_distance(cvd_data[i], hc_data)
        obs_distances.append(d)
    obs_stat = np.mean(obs_distances)

    # Permutation null
    rng = np.random.default_rng(42)
    null_stats = []
    for _ in range(n_perm):
        perm = rng.permutation(n_total)
        hc_perm = all_data[perm[:n_hc]]
        cvd_perm = all_data[perm[n_hc:]]
        perm_distances = []
        for i in range(cvd_perm.shape[0]):
            d = mahalanobis_distance(cvd_perm[i], hc_perm)
            perm_distances.append(d)
        null_stats.append(np.mean(perm_distances))

    p = (np.sum(np.array(null_stats) >= obs_stat) + 1) / (n_perm + 1)
    return float(obs_stat), float(p), obs_distances, null_stats


def min_vuln_test(cvd_data, hc_data, n_perm=10000):
    """
    Test if CVD subjects have lower minimum vulnerability than HC.
    Captures the 'weakest color' signal without model fitting.
    """
    all_data = np.vstack([hc_data, cvd_data])
    n_hc = hc_data.shape[0]
    n_total = all_data.shape[0]

    # Observed: mean of per-subject minimum vulnerability
    obs_cvd_mins = [np.min(cvd_data[i]) for i in range(cvd_data.shape[0])]
    obs_stat = np.mean(obs_cvd_mins)

    rng = np.random.default_rng(42)
    null_stats = []
    for _ in range(n_perm):
        perm = rng.permutation(n_total)
        cvd_perm = all_data[perm[n_hc:]]
        perm_mins = [np.min(cvd_perm[i]) for i in range(cvd_perm.shape[0])]
        null_stats.append(np.mean(perm_mins))

    # One-tailed: CVD should have LOWER minimum
    p = (np.sum(np.array(null_stats) <= obs_stat) + 1) / (n_perm + 1)
    return float(obs_stat), float(p), obs_cvd_mins, null_stats


def profile_range_test(cvd_data, hc_data, n_perm=10000):
    """Test if CVD profiles have higher range (max-min) than HC."""
    all_data = np.vstack([hc_data, cvd_data])
    n_hc = hc_data.shape[0]
    n_total = all_data.shape[0]

    obs_ranges = [profile_range(cvd_data[i]) for i in range(cvd_data.shape[0])]
    obs_stat = np.mean(obs_ranges)

    rng = np.random.default_rng(42)
    null_stats = []
    for _ in range(n_perm):
        perm = rng.permutation(n_total)
        cvd_perm = all_data[perm[n_hc:]]
        perm_ranges = [profile_range(cvd_perm[i]) for i in range(cvd_perm.shape[0])]
        null_stats.append(np.mean(perm_ranges))

    p = (np.sum(np.array(null_stats) >= obs_stat) + 1) / (n_perm + 1)
    return float(obs_stat), float(p), obs_ranges, null_stats


def main():
    print("=" * 70)
    print("LOCO Vulnerability Profile — CVD Specificity Analysis")
    print("=" * 70)

    hc_matrix = np.array([VULN_DATA[s] for s in HC_IDS])  # (7, 8)
    cvd_matrix = np.array([VULN_DATA[s] for s in CVD_IDS])  # (3, 8)

    results = {}

    # ── 1. Descriptive statistics ────────────────────────────────────
    print("\n[1] Descriptive Statistics")
    print(f"{'Subject':>8}  {'Mean':>6}  {'Min':>6}  {'Max':>6}  {'Range':>6}  {'CV':>6}  {'Min Color'}")
    print("-" * 70)
    for sid in HC_IDS + CVD_IDS:
        v = np.array(VULN_DATA[sid])
        tag = "CVD" if sid in CVD_IDS else "HC"
        min_idx = np.argmin(v)
        print(f"  {tag}-{sid}  {np.mean(v):.3f}  {np.min(v):.3f}  {np.max(v):.3f}  "
              f"{profile_range(v):.3f}  {profile_cv(v):.3f}  {COLOR_NAMES[min_idx]}")

    hc_means = hc_matrix.mean(axis=0)
    hc_stds = hc_matrix.std(axis=0, ddof=1)
    print(f"\n  HC mean: [{', '.join(f'{x:.3f}' for x in hc_means)}]")
    print(f"  HC std:  [{', '.join(f'{x:.3f}' for x in hc_stds)}]")

    # ── 2. Per-color Crawford & Howell ───────────────────────────────
    print("\n[2] Per-Color Crawford & Howell Tests")
    print(f"{'Subject':>8}  {'Color':>12}  {'Value':>6}  {'HC mean':>7}  {'t':>7}  {'p':>7}  {'Sig'}")
    print("-" * 70)

    ch_results = {}
    for sid in CVD_IDS:
        ch_results[sid] = {}
        vuln = np.array(VULN_DATA[sid])
        hc_per_color = hc_matrix  # (7, 8)
        sig_colors = []
        for c in range(8):
            t, p = crawford_howell(vuln[c], hc_per_color[:, c])
            sig = '*' if p < 0.05 else '**' if p < 0.01 else ''
            if p < 0.05:
                sig = '**' if p < 0.01 else '*'
                sig_colors.append(COLOR_NAMES[c])
            else:
                sig = ''
            ch_results[sid][COLOR_NAMES[c]] = {'t': t, 'p': p, 'value': vuln[c]}
            print(f"  CVD-{sid}  {COLOR_NAMES[c]:>12}  {vuln[c]:.3f}  {hc_means[c]:.3f}  "
                  f"{t:+.3f}  {p:.4f}  {sig}")
        if sig_colors:
            print(f"  → sig colors for {sid}: {', '.join(sig_colors)}")
        print()

    # ── 3. Summary statistics tests ──────────────────────────────────
    print("\n[3] Profile Summary Statistics — Group Comparison")

    # Profile range
    hc_ranges = [profile_range(hc_matrix[i]) for i in range(7)]
    cvd_ranges = [profile_range(cvd_matrix[i]) for i in range(3)]
    print(f"  Profile Range:  HC mean={np.mean(hc_ranges):.3f} (SD={np.std(hc_ranges, ddof=1):.3f})")
    print(f"                  CVD: {', '.join(f'{r:.3f}' for r in cvd_ranges)}")

    # Profile min
    hc_mins = [np.min(hc_matrix[i]) for i in range(7)]
    cvd_mins = [np.min(cvd_matrix[i]) for i in range(3)]
    print(f"  Profile Min:    HC mean={np.mean(hc_mins):.3f} (SD={np.std(hc_mins, ddof=1):.3f})")
    print(f"                  CVD: {', '.join(f'{m:.3f}' for m in cvd_mins)}")

    # Crawford & Howell on profile range
    print(f"\n  Crawford & Howell on Profile Range:")
    for i, sid in enumerate(CVD_IDS):
        t, p = crawford_howell(cvd_ranges[i], hc_ranges)
        sig = '**' if p < 0.01 else '*' if p < 0.05 else 'NS'
        print(f"    CVD-{sid} ({CVD_TYPES[sid]}): range={cvd_ranges[i]:.3f}, t={t:+.3f}, p={p:.4f} {sig}")

    # Crawford & Howell on profile min
    print(f"\n  Crawford & Howell on Profile Min:")
    for i, sid in enumerate(CVD_IDS):
        t, p = crawford_howell(cvd_mins[i], hc_mins)
        sig = '**' if p < 0.01 else '*' if p < 0.05 else 'NS'
        print(f"    CVD-{sid} ({CVD_TYPES[sid]}): min={cvd_mins[i]:.3f}, t={t:+.3f}, p={p:.4f} {sig}")

    # ── 4. Mahalanobis distance ──────────────────────────────────────
    print("\n[4] Mahalanobis Distance from HC Centroid")

    # Also compute HC LOO Mahalanobis for comparison
    hc_maha = []
    for i in range(7):
        hc_loo = np.delete(hc_matrix, i, axis=0)
        d = mahalanobis_distance(hc_matrix[i], hc_loo)
        hc_maha.append(d)
        print(f"  HC-{HC_IDS[i]} (LOO): d={d:.3f}")

    print()
    cvd_maha = []
    for i, sid in enumerate(CVD_IDS):
        d = mahalanobis_distance(cvd_matrix[i], hc_matrix)
        cvd_maha.append(d)
        rank = sum(1 for h in hc_maha if h >= d) + 1
        emp_p = rank / (len(hc_maha) + 1)
        print(f"  CVD-{sid} ({CVD_TYPES[sid]}): d={d:.3f}, rank={8-rank+1}/8, emp_p={emp_p:.3f}")

    # ── 5. Permutation tests ─────────────────────────────────────────
    print("\n[5] Permutation Tests (10,000 permutations)")

    # 5a. Mahalanobis
    obs, p, obs_dists, null = permutation_test_mahalanobis(cvd_matrix, hc_matrix)
    sig = '**' if p < 0.01 else '*' if p < 0.05 else 'NS'
    print(f"  Mahalanobis group test: obs_mean={obs:.3f}, p={p:.4f} {sig}")
    print(f"    Null: mean={np.mean(null):.3f}, 95th={np.percentile(null, 95):.3f}")
    results['mahalanobis_perm'] = {'obs': obs, 'p': p}

    # 5b. Minimum vulnerability
    obs, p, obs_mins, null = min_vuln_test(cvd_matrix, hc_matrix)
    sig = '**' if p < 0.01 else '*' if p < 0.05 else 'NS'
    print(f"  Min-vulnerability test: obs_mean={obs:.3f}, p={p:.4f} {sig}")
    print(f"    Null: mean={np.mean(null):.3f}, 5th={np.percentile(null, 5):.3f}")
    results['min_vuln_perm'] = {'obs': obs, 'p': p}

    # 5c. Profile range
    obs, p, obs_ranges_perm, null = profile_range_test(cvd_matrix, hc_matrix)
    sig = '**' if p < 0.01 else '*' if p < 0.05 else 'NS'
    print(f"  Profile-range test: obs_mean={obs:.3f}, p={p:.4f} {sig}")
    print(f"    Null: mean={np.mean(null):.3f}, 95th={np.percentile(null, 95):.3f}")
    results['range_perm'] = {'obs': obs, 'p': p}

    # ── 6. Individual-level specificity ──────────────────────────────
    print("\n[6] Individual-Level Specificity Summary")
    print(f"{'Subject':>8}  {'Type':>8}  {'Min':>6}  {'Range':>6}  {'Maha':>6}  "
          f"{'#sig_colors':>11}  {'Verdict'}")
    print("-" * 70)

    for sid in CVD_IDS:
        vuln = np.array(VULN_DATA[sid])
        n_sig = sum(1 for c in range(8)
                    if crawford_howell(vuln[c], hc_matrix[:, c])[1] < 0.05)
        maha = mahalanobis_distance(vuln, hc_matrix)
        rang = profile_range(vuln)
        mn = np.min(vuln)

        # Verdict based on convergence of evidence
        if n_sig >= 2 and maha > np.percentile(hc_maha, 95):
            verdict = "OUTLIER"
        elif n_sig >= 1 or maha > np.mean(hc_maha) + np.std(hc_maha):
            verdict = "marginal"
        else:
            verdict = "within HC"

        print(f"  CVD-{sid}  {CVD_TYPES[sid]:>8}  {mn:.3f}  {rang:.3f}  {maha:.3f}  "
              f"  {n_sig:>3}        {verdict}")

    # ── 7. Comparison with existing pipeline ─────────────────────────
    print("\n[7] Comparison: LOCO Profile vs Cone-Shift Pipeline")
    print("""
    ┌──────────────────────────────────────────────────────────────────┐
    │ Method                      │ HC FPR  │ CVD-08 │ CVD-09 │ CVD-10│
    ├─────────────────────────────┼─────────┼────────┼────────┼───────┤
    │ Cone-shift (2comp, hV4)     │ 100%    │ p=0.004│ p=0.035│ p=0.06│
    │ Cone-shift (machado, hV4)   │ 14%     │ NS     │ p=0.058│ NS    │
    │ Cross-ROI (SRM+LOCO)        │ ?       │ p=0.00 │ p=0.00 │ FP!   │
    │ LOCO profile (this analysis)│ See above results                  │
    └──────────────────────────────────────────────────────────────────┘
    """)

    # Save results
    output = {
        'hc_vuln': {s: VULN_DATA[s] for s in HC_IDS},
        'cvd_vuln': {s: VULN_DATA[s] for s in CVD_IDS},
        'per_color_crawford_howell': ch_results,
        'hc_profile_ranges': hc_ranges,
        'cvd_profile_ranges': cvd_ranges,
        'hc_profile_mins': hc_mins,
        'cvd_profile_mins': cvd_mins,
        'hc_mahalanobis_loo': hc_maha,
        'cvd_mahalanobis': cvd_maha,
        'permutation_tests': results,
    }

    out_dir = Path(__file__).parent.parent / 'results' / 'loco_profile_specificity'
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / 'analysis_results.json', 'w') as f:
        json.dump(output, f, indent=2, default=float)
    print(f"\nResults saved to {out_dir / 'analysis_results.json'}")


if __name__ == '__main__':
    main()
