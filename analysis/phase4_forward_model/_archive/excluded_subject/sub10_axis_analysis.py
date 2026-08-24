"""
Sub-10 Axis-Specific Anomaly Detection
=======================================
기존 파이프라인(SRM RDM, Forward Model LOCO) 내에서
sub-10의 cool-축 특이점을 탐색하는 5가지 분석.

Colors: 0=red, 1=orange, 2=yellow, 3=green, 4=cyan, 5=blue, 6=purple, 7=magenta
Warm: 0,1,2,3 (red, orange, yellow, green)
Cool: 4,5,6,7 (cyan, blue, purple, magenta)
"""

import numpy as np
import json
import os
from scipy import stats
from itertools import combinations

# ── Config ──
BASE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(os.path.dirname(BASE))
ALIGNED_DIR = os.path.join(PROJECT, "analysis/phase2_SRM_across_between/results/c010/combined_with_aligned")
LOCO_DIR = os.path.join(PROJECT, "analysis/phase4_forward_model/results/loco_reinforcement")
AMP_DIR = os.path.join(PROJECT, "analysis/phase1_procrustes_decoding/results/full_dataset_C010")

COLOR_NAMES = ['red', 'orange', 'yellow', 'green', 'cyan', 'blue', 'purple', 'magenta']
WARM_IDX = [0, 1, 2, 3]
COOL_IDX = [4, 5, 6, 7]

HC_SUBS = ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05', 'sub-06', 'sub-07']
CVD_SUBS = ['sub-08', 'sub-09', 'sub-10']
HC_ANALYSIS = ['sub-02', 'sub-03', 'sub-05', 'sub-06', 'sub-07']  # excluding sub-01

ROIS = ['V1', 'V2', 'V3', 'V4']
ROI_K = {'V1': 4, 'V2': 4, 'V3': 3, 'V4': 3}


def crawford_howell(x, group_values):
    """Crawford & Howell (1998) modified t-test for single case."""
    n = len(group_values)
    m = np.mean(group_values)
    s = np.std(group_values, ddof=1)
    if s < 1e-12:
        return np.nan, np.nan
    t = (x - m) / (s * np.sqrt((n + 1) / n))
    p = 2 * stats.t.sf(abs(t), df=n - 1)
    return t, p


def compute_rdm_corr(patterns):
    """Compute RDM from 8×K patterns using correlation distance."""
    n = patterns.shape[0]
    rdm = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            r = np.corrcoef(patterns[i], patterns[j])[0, 1]
            rdm[i, j] = rdm[j, i] = 1 - r
    return rdm


def compute_rdm_euclidean(patterns):
    """Compute RDM from 8×K patterns using Euclidean distance."""
    from scipy.spatial.distance import pdist, squareform
    return squareform(pdist(patterns, metric='euclidean'))


def get_pair_categories():
    """Classify 28 pairs into warm-internal, cool-internal, cross-axis, warm-adjacent, cool-adjacent."""
    pairs = list(combinations(range(8), 2))

    # Adjacent pairs on hue circle (distance = 1 step = 45°)
    warm_adj = [(0, 1), (1, 2), (2, 3)]  # red-orange, orange-yellow, yellow-green
    cool_adj = [(4, 5), (5, 6), (6, 7)]  # cyan-blue, blue-purple, purple-magenta
    bridge = [(3, 4), (0, 7)]  # green-cyan, red-magenta (warm↔cool boundary)

    # Within-group pairs
    warm_pairs = [(i, j) for i, j in pairs if i in WARM_IDX and j in WARM_IDX]
    cool_pairs = [(i, j) for i, j in pairs if i in COOL_IDX and j in COOL_IDX]
    cross_pairs = [(i, j) for i, j in pairs
                   if (i in WARM_IDX and j in COOL_IDX) or (i in COOL_IDX and j in WARM_IDX)]

    return {
        'warm_internal': warm_pairs,
        'cool_internal': cool_pairs,
        'cross_axis': cross_pairs,
        'warm_adjacent': warm_adj,
        'cool_adjacent': cool_adj,
        'bridge': bridge,
    }


def load_aligned_amplitudes(roi):
    """Load SRM-aligned amplitudes dict {subject: (8, K)} for a ROI."""
    roi_dir = roi if roi != 'V4' else 'V4'
    path = os.path.join(ALIGNED_DIR, f"{roi}_procrustes_aligned_amplitudes.npy")
    data = np.load(path, allow_pickle=True).item()
    return data


# ══════════════════════════════════════════════════════════════
# Analysis 1: SRM RDM 축별 분해
# ══════════════════════════════════════════════════════════════
def analysis1_rdm_axis_decomposition():
    print("\n" + "=" * 70)
    print("분석 1: SRM RDM 축별 분해 (Cool/Warm/Cross-axis 체계적 편향)")
    print("=" * 70)

    cats = get_pair_categories()

    for roi in ROIS:
        data = load_aligned_amplitudes(roi)
        print(f"\n{'─' * 50}")
        print(f"ROI: {roi}")

        # Compute RDM for each subject (correlation distance)
        rdms = {}
        for sub in HC_ANALYSIS + CVD_SUBS:
            if sub in data:
                rdms[sub] = compute_rdm_corr(data[sub])

        # HC mean RDM
        hc_rdm_list = [rdms[s] for s in HC_ANALYSIS if s in rdms]
        hc_mean_rdm = np.mean(hc_rdm_list, axis=0)

        # Per-category analysis for sub-10
        if 'sub-10' not in rdms:
            print("  sub-10 data not found")
            continue

        sub10_rdm = rdms['sub-10']
        delta_rdm = sub10_rdm - hc_mean_rdm

        for cat_name, pairs in cats.items():
            # Extract delta values for this category
            deltas = [delta_rdm[i, j] for i, j in pairs]

            # HC individual deltas for this category (for Crawford-Howell)
            hc_cat_means = []
            for hc_sub in HC_ANALYSIS:
                if hc_sub in rdms:
                    hc_deltas = [rdms[hc_sub][i, j] - hc_mean_rdm[i, j] for i, j in pairs]
                    hc_cat_means.append(np.mean(hc_deltas))

            sub10_cat_mean = np.mean(deltas)
            t_val, p_val = crawford_howell(sub10_cat_mean, hc_cat_means)

            sig = "***" if p_val < 0.01 else "**" if p_val < 0.05 else "*" if p_val < 0.1 else ""
            print(f"  {cat_name:20s}: Δ={sub10_cat_mean:+.4f}, HC_mean={np.mean(hc_cat_means):+.4f}, "
                  f"HC_SD={np.std(hc_cat_means, ddof=1):.4f}, t={t_val:+.3f}, p={p_val:.4f} {sig}")

        # Also report sub-08 and sub-09 for comparison
        for cvd_sub in ['sub-08', 'sub-09']:
            if cvd_sub not in rdms:
                continue
            cvd_rdm = rdms[cvd_sub]
            delta = cvd_rdm - hc_mean_rdm
            print(f"\n  [{cvd_sub} 비교]")
            for cat_name, pairs in cats.items():
                deltas = [delta[i, j] for i, j in pairs]
                hc_cat_means = []
                for hc_sub in HC_ANALYSIS:
                    if hc_sub in rdms:
                        hc_d = [rdms[hc_sub][i, j] - hc_mean_rdm[i, j] for i, j in pairs]
                        hc_cat_means.append(np.mean(hc_d))
                cat_mean = np.mean(deltas)
                t_val, p_val = crawford_howell(cat_mean, hc_cat_means)
                sig = "***" if p_val < 0.01 else "**" if p_val < 0.05 else "*" if p_val < 0.1 else ""
                print(f"    {cat_name:20s}: Δ={cat_mean:+.4f}, t={t_val:+.3f}, p={p_val:.4f} {sig}")


# ══════════════════════════════════════════════════════════════
# Analysis 2: Per-color LOCO 축별 분해
# ══════════════════════════════════════════════════════════════
def analysis2_loco_axis_decomposition():
    print("\n" + "=" * 70)
    print("분석 2: Per-color LOCO 축별 분해 (Warm vs Cool 보간 결손)")
    print("=" * 70)

    with open(os.path.join(LOCO_DIR, "per_color_breakdown.json")) as f:
        loco_data = json.load(f)

    for roi_key in ['V1', 'V2', 'V3', 'hV4']:
        if roi_key not in loco_data:
            continue
        rd = loco_data[roi_key]
        print(f"\n{'─' * 50}")
        print(f"ROI: {roi_key}")

        # HC per-subject per-color matrix (7 HC × 8 colors)
        hc_matrix = np.array(rd['hc_matrix'])  # (N_hc, 8)
        n_hc = hc_matrix.shape[0]

        # HC warm/cool means per subject
        hc_warm = np.mean(hc_matrix[:, WARM_IDX], axis=1)
        hc_cool = np.mean(hc_matrix[:, COOL_IDX], axis=1)
        hc_delta = hc_warm - hc_cool  # positive = warm > cool

        # Sub-10 per-color
        if 'sub-10' not in rd.get('cvd_per_color', {}):
            print("  sub-10 not found")
            continue

        sub10_colors = rd['cvd_per_color']['sub-10']
        sub10_vals = [sub10_colors[str(i)]['value'] for i in range(8)]

        sub10_warm = np.mean([sub10_vals[i] for i in WARM_IDX])
        sub10_cool = np.mean([sub10_vals[i] for i in COOL_IDX])
        sub10_delta = sub10_warm - sub10_cool

        # Crawford-Howell on warm-cool delta
        t_delta, p_delta = crawford_howell(sub10_delta, hc_delta)

        # Also test warm and cool separately
        t_warm, p_warm = crawford_howell(sub10_warm, hc_warm)
        t_cool, p_cool = crawford_howell(sub10_cool, hc_cool)

        sig_d = "***" if p_delta < 0.01 else "**" if p_delta < 0.05 else "*" if p_delta < 0.1 else ""
        sig_w = "***" if p_warm < 0.01 else "**" if p_warm < 0.05 else "*" if p_warm < 0.1 else ""
        sig_c = "***" if p_cool < 0.01 else "**" if p_cool < 0.05 else "*" if p_cool < 0.1 else ""

        print(f"  HC Warm mean:  {np.mean(hc_warm):.4f} ± {np.std(hc_warm, ddof=1):.4f}")
        print(f"  HC Cool mean:  {np.mean(hc_cool):.4f} ± {np.std(hc_cool, ddof=1):.4f}")
        print(f"  HC Δ(W-C):     {np.mean(hc_delta):+.4f} ± {np.std(hc_delta, ddof=1):.4f}")
        print(f"  Sub-10 Warm:   {sub10_warm:.4f}, t={t_warm:+.3f}, p={p_warm:.4f} {sig_w}")
        print(f"  Sub-10 Cool:   {sub10_cool:.4f}, t={t_cool:+.3f}, p={p_cool:.4f} {sig_c}")
        print(f"  Sub-10 Δ(W-C): {sub10_delta:+.4f}, t={t_delta:+.3f}, p={p_delta:.4f} {sig_d}")

        # Per-color detail
        print(f"\n  Per-color LOCO (sub-10 vs HC):")
        for i in range(8):
            axis = "WARM" if i in WARM_IDX else "COOL"
            hc_vals_i = hc_matrix[:, i]
            sub10_v = sub10_vals[i]
            t_i, p_i = crawford_howell(sub10_v, hc_vals_i)
            sig_i = "**" if p_i < 0.05 else "*" if p_i < 0.1 else ""
            print(f"    {COLOR_NAMES[i]:8s} [{axis}]: sub10={sub10_v:+.3f}, "
                  f"HC={np.mean(hc_vals_i):+.3f}±{np.std(hc_vals_i, ddof=1):.3f}, "
                  f"t={t_i:+.3f}, p={p_i:.3f} {sig_i}")

        # Comparison: sub-08, sub-09
        for cvd_sub in ['sub-08', 'sub-09']:
            if cvd_sub not in rd.get('cvd_per_color', {}):
                continue
            cvd_colors = rd['cvd_per_color'][cvd_sub]
            cvd_vals = [cvd_colors[str(i)]['value'] for i in range(8)]
            cvd_warm = np.mean([cvd_vals[i] for i in WARM_IDX])
            cvd_cool = np.mean([cvd_vals[i] for i in COOL_IDX])
            cvd_delta = cvd_warm - cvd_cool
            t_d, p_d = crawford_howell(cvd_delta, hc_delta)
            sig = "**" if p_d < 0.05 else "*" if p_d < 0.1 else ""
            print(f"\n  [{cvd_sub}] Warm={cvd_warm:.4f}, Cool={cvd_cool:.4f}, "
                  f"Δ={cvd_delta:+.4f}, t={t_d:+.3f}, p={p_d:.4f} {sig}")


# ══════════════════════════════════════════════════════════════
# Analysis 3: SRM 공유 공간 형태 분석 (타원성 + 각도 균일성)
# ══════════════════════════════════════════════════════════════
def analysis3_shared_space_shape():
    print("\n" + "=" * 70)
    print("분석 3: SRM 공유 공간 형태 분석 (타원성 + 각도 균일성)")
    print("=" * 70)

    for roi in ROIS:
        data = load_aligned_amplitudes(roi)
        K = ROI_K[roi]
        print(f"\n{'─' * 50}")
        print(f"ROI: {roi} (K={K})")

        # ── 3a: Eccentricity (PC1/PC2 ratio) ──
        print(f"\n  [3a] Eccentricity (PC1/PC2 eigenvalue ratio):")

        eccentricities = {}
        for sub in HC_ANALYSIS + CVD_SUBS:
            if sub not in data:
                continue
            patterns = data[sub]  # (8, K)
            centered = patterns - patterns.mean(axis=0)
            cov = np.cov(centered.T)
            eigvals = np.sort(np.linalg.eigvalsh(cov))[::-1]
            if eigvals[1] > 1e-12:
                ratio = eigvals[0] / eigvals[1]
            else:
                ratio = np.inf
            eccentricities[sub] = ratio

        hc_ecc = [eccentricities[s] for s in HC_ANALYSIS if s in eccentricities]
        for cvd_sub in CVD_SUBS:
            if cvd_sub in eccentricities:
                t_val, p_val = crawford_howell(eccentricities[cvd_sub], hc_ecc)
                sig = "**" if p_val < 0.05 else "*" if p_val < 0.1 else ""
                print(f"    {cvd_sub}: ratio={eccentricities[cvd_sub]:.3f}, "
                      f"HC={np.mean(hc_ecc):.3f}±{np.std(hc_ecc, ddof=1):.3f}, "
                      f"t={t_val:+.3f}, p={p_val:.4f} {sig}")

        # ── 3b: Angular uniformity ──
        print(f"\n  [3b] Angular spacing (cool region vs warm region):")

        for sub in ['sub-10'] + ['sub-08', 'sub-09']:
            if sub not in data:
                continue
            patterns = data[sub]  # (8, K)

            # Use first 2 PCs for angular analysis
            centered = patterns - patterns.mean(axis=0)
            U, S, Vt = np.linalg.svd(centered, full_matrices=False)
            coords_2d = centered @ Vt[:2].T  # project to 2D

            # Compute angles from centroid
            centroid = coords_2d.mean(axis=0)
            angles = np.array([np.arctan2(coords_2d[i, 1] - centroid[1],
                                          coords_2d[i, 0] - centroid[0])
                               for i in range(8)])
            angles_deg = np.degrees(angles)

            # Sort by expected hue order and compute inter-color spacing
            # Expected order: 0,1,2,3,4,5,6,7 (red→magenta)
            # Compute angular spacing between consecutive colors
            spacings = []
            for i in range(8):
                j = (i + 1) % 8
                diff = angles[j] - angles[i]
                # Handle wrap-around
                diff = (diff + np.pi) % (2 * np.pi) - np.pi
                spacings.append(np.degrees(diff))

            warm_spacings = [abs(spacings[i]) for i in range(3)]  # 0-1, 1-2, 2-3
            cool_spacings = [abs(spacings[i]) for i in range(4, 7)]  # 4-5, 5-6, 6-7

            # Uniformity: SD of spacings (lower = more uniform)
            all_abs = [abs(s) for s in spacings]
            print(f"    {sub}: warm_mean={np.mean(warm_spacings):.1f}°, "
                  f"cool_mean={np.mean(cool_spacings):.1f}°, "
                  f"spacing_SD={np.std(all_abs):.1f}°, "
                  f"warm/cool ratio={np.mean(warm_spacings)/max(np.mean(cool_spacings),1e-6):.2f}")


# ══════════════════════════════════════════════════════════════
# Analysis 4: Forward Model 채널 균형 검정
# ══════════════════════════════════════════════════════════════
def analysis4_channel_balance():
    print("\n" + "=" * 70)
    print("분석 4: Forward Model 채널 균형 (Warm/Cool ratio)")
    print("=" * 70)

    with open(os.path.join(LOCO_DIR, "per_color_breakdown.json")) as f:
        loco_data = json.load(f)

    # Use hV4 data (main finding from notion.md §8e)
    for roi_key in ['V1', 'V2', 'hV4']:
        if roi_key not in loco_data:
            continue
        rd = loco_data[roi_key]
        print(f"\n{'─' * 50}")
        print(f"ROI: {roi_key}")

        hc_matrix = np.array(rd['hc_matrix'])
        n_hc = hc_matrix.shape[0]

        # Per-subject warm/cool means and ratios
        hc_warm_means = np.mean(hc_matrix[:, WARM_IDX], axis=1)
        hc_cool_means = np.mean(hc_matrix[:, COOL_IDX], axis=1)
        hc_ratios = hc_warm_means / np.where(np.abs(hc_cool_means) > 1e-8,
                                              hc_cool_means, 1e-8)

        for cvd_sub in CVD_SUBS:
            if cvd_sub not in rd.get('cvd_per_color', {}):
                continue
            cvd_colors = rd['cvd_per_color'][cvd_sub]
            cvd_vals = [cvd_colors[str(i)]['value'] for i in range(8)]
            cvd_warm = np.mean([cvd_vals[i] for i in WARM_IDX])
            cvd_cool = np.mean([cvd_vals[i] for i in COOL_IDX])

            if abs(cvd_cool) > 1e-8:
                cvd_ratio = cvd_warm / cvd_cool
            else:
                cvd_ratio = np.inf

            t_val, p_val = crawford_howell(cvd_ratio, hc_ratios)
            sig = "***" if p_val < 0.01 else "**" if p_val < 0.05 else "*" if p_val < 0.1 else ""

            print(f"  {cvd_sub}: warm={cvd_warm:+.4f}, cool={cvd_cool:+.4f}, "
                  f"ratio={cvd_ratio:+.3f}")
            print(f"    HC ratio: {np.mean(hc_ratios):+.3f} ± {np.std(hc_ratios, ddof=1):.3f}")
            print(f"    Crawford-Howell: t={t_val:+.3f}, p={p_val:.4f} {sig}")


# ══════════════════════════════════════════════════════════════
# Analysis 5: RDM Scale (Euclidean distance + L2 norm)
# ══════════════════════════════════════════════════════════════
def analysis5_rdm_scale():
    print("\n" + "=" * 70)
    print("분석 5: RDM Scale — 표상 크기 (L2 norm + Euclidean RDM)")
    print("=" * 70)
    print("  RDM(corr)은 스케일 불변. 색 점이 원점에 가깝지만 각도가")
    print("  유사하면 RDM 정상으로 보임. Euclidean distance와 L2 norm으로 확인.\n")

    for roi in ROIS:
        data = load_aligned_amplitudes(roi)
        print(f"{'─' * 50}")
        print(f"ROI: {roi}")

        # ── 5a: Per-subject mean L2 norm of color patterns ──
        norms = {}
        for sub in HC_ANALYSIS + CVD_SUBS:
            if sub not in data:
                continue
            patterns = data[sub]  # (8, K)
            color_norms = np.linalg.norm(patterns, axis=1)  # (8,)
            norms[sub] = {
                'mean_norm': np.mean(color_norms),
                'warm_norm': np.mean(color_norms[WARM_IDX]),
                'cool_norm': np.mean(color_norms[COOL_IDX]),
                'per_color': color_norms,
            }

        hc_mean_norms = [norms[s]['mean_norm'] for s in HC_ANALYSIS if s in norms]
        hc_warm_norms = [norms[s]['warm_norm'] for s in HC_ANALYSIS if s in norms]
        hc_cool_norms = [norms[s]['cool_norm'] for s in HC_ANALYSIS if s in norms]

        print(f"\n  [5a] Mean L2 norm of color patterns:")
        print(f"  HC overall: {np.mean(hc_mean_norms):.4f} ± {np.std(hc_mean_norms, ddof=1):.4f}")
        print(f"  HC warm:    {np.mean(hc_warm_norms):.4f} ± {np.std(hc_warm_norms, ddof=1):.4f}")
        print(f"  HC cool:    {np.mean(hc_cool_norms):.4f} ± {np.std(hc_cool_norms, ddof=1):.4f}")

        for cvd_sub in CVD_SUBS:
            if cvd_sub not in norms:
                continue
            n = norms[cvd_sub]
            t_all, p_all = crawford_howell(n['mean_norm'], hc_mean_norms)
            t_warm, p_warm = crawford_howell(n['warm_norm'], hc_warm_norms)
            t_cool, p_cool = crawford_howell(n['cool_norm'], hc_cool_norms)

            sig_a = "**" if p_all < 0.05 else "*" if p_all < 0.1 else ""
            sig_w = "**" if p_warm < 0.05 else "*" if p_warm < 0.1 else ""
            sig_c = "**" if p_cool < 0.05 else "*" if p_cool < 0.1 else ""

            print(f"\n  {cvd_sub}:")
            print(f"    overall={n['mean_norm']:.4f}, t={t_all:+.3f}, p={p_all:.4f} {sig_a}")
            print(f"    warm   ={n['warm_norm']:.4f}, t={t_warm:+.3f}, p={p_warm:.4f} {sig_w}")
            print(f"    cool   ={n['cool_norm']:.4f}, t={t_cool:+.3f}, p={p_cool:.4f} {sig_c}")

        # ── 5b: Euclidean RDM mean distance ──
        print(f"\n  [5b] Euclidean RDM mean distance (scale-sensitive):")

        euc_rdm_means = {}
        for sub in HC_ANALYSIS + CVD_SUBS:
            if sub not in data:
                continue
            rdm_euc = compute_rdm_euclidean(data[sub])
            upper = rdm_euc[np.triu_indices(8, k=1)]
            euc_rdm_means[sub] = {
                'overall': np.mean(upper),
                'warm': np.mean([rdm_euc[i, j] for i, j in combinations(WARM_IDX, 2)]),
                'cool': np.mean([rdm_euc[i, j] for i, j in combinations(COOL_IDX, 2)]),
                'cross': np.mean([rdm_euc[i, j] for i in WARM_IDX for j in COOL_IDX]),
            }

        hc_euc_overall = [euc_rdm_means[s]['overall'] for s in HC_ANALYSIS if s in euc_rdm_means]
        hc_euc_warm = [euc_rdm_means[s]['warm'] for s in HC_ANALYSIS if s in euc_rdm_means]
        hc_euc_cool = [euc_rdm_means[s]['cool'] for s in HC_ANALYSIS if s in euc_rdm_means]
        hc_euc_cross = [euc_rdm_means[s]['cross'] for s in HC_ANALYSIS if s in euc_rdm_means]

        print(f"  HC: overall={np.mean(hc_euc_overall):.4f}, "
              f"warm={np.mean(hc_euc_warm):.4f}, cool={np.mean(hc_euc_cool):.4f}, "
              f"cross={np.mean(hc_euc_cross):.4f}")

        for cvd_sub in CVD_SUBS:
            if cvd_sub not in euc_rdm_means:
                continue
            e = euc_rdm_means[cvd_sub]
            t_o, p_o = crawford_howell(e['overall'], hc_euc_overall)
            t_w, p_w = crawford_howell(e['warm'], hc_euc_warm)
            t_c, p_c = crawford_howell(e['cool'], hc_euc_cool)
            t_x, p_x = crawford_howell(e['cross'], hc_euc_cross)

            sig_o = "**" if p_o < 0.05 else "*" if p_o < 0.1 else ""
            sig_w = "**" if p_w < 0.05 else "*" if p_w < 0.1 else ""
            sig_c = "**" if p_c < 0.05 else "*" if p_c < 0.1 else ""
            sig_x = "**" if p_x < 0.05 else "*" if p_x < 0.1 else ""

            print(f"  {cvd_sub}: overall={e['overall']:.4f} {sig_o}, "
                  f"warm={e['warm']:.4f} {sig_w}, cool={e['cool']:.4f} {sig_c}, "
                  f"cross={e['cross']:.4f} {sig_x}")
            print(f"    p: overall={p_o:.4f}, warm={p_w:.4f}, cool={p_c:.4f}, cross={p_x:.4f}")

        # ── 5c: Warm/Cool norm ratio ──
        print(f"\n  [5c] Warm/Cool L2 norm ratio:")
        hc_wc_ratios = []
        for s in HC_ANALYSIS:
            if s in norms:
                r = norms[s]['warm_norm'] / max(norms[s]['cool_norm'], 1e-8)
                hc_wc_ratios.append(r)

        print(f"  HC: {np.mean(hc_wc_ratios):.4f} ± {np.std(hc_wc_ratios, ddof=1):.4f}")
        for cvd_sub in CVD_SUBS:
            if cvd_sub not in norms:
                continue
            n = norms[cvd_sub]
            r = n['warm_norm'] / max(n['cool_norm'], 1e-8)
            t_val, p_val = crawford_howell(r, hc_wc_ratios)
            sig = "**" if p_val < 0.05 else "*" if p_val < 0.1 else ""
            print(f"  {cvd_sub}: ratio={r:.4f}, t={t_val:+.3f}, p={p_val:.4f} {sig}")


# ══════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("Sub-10 Axis-Specific Anomaly Detection")
    print("=" * 70)
    print(f"HC (analysis): {HC_ANALYSIS}")
    print(f"CVD: {CVD_SUBS}")
    print(f"ROIs: {ROIS}")

    analysis1_rdm_axis_decomposition()
    analysis2_loco_axis_decomposition()
    analysis3_shared_space_shape()
    analysis4_channel_balance()
    analysis5_rdm_scale()

    print("\n" + "=" * 70)
    print("완료")
    print("=" * 70)
