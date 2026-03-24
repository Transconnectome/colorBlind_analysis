#!/usr/bin/env python3
"""
Cone Opponency 정확한 계산 — Gaussian Fundamentals

수정사항:
1. 2D Euclidean distance (L-M, S-(L+M)) 제대로 계산
2. 모든 색 쌍에 대해 정량적 예측
3. SRM z, RDM diff와 비교
"""

import numpy as np
import pandas as pd

# ============================================================
# Cone Fundamentals (Gaussian Approximation)
# ============================================================

def cone_response(wavelength, peak, sigma=50):
    """
    Gaussian approximation of cone sensitivity
    Based on Stockman & Sharpe (2000)
    """
    return np.exp(-0.5 * ((wavelength - peak) / sigma) ** 2)

# Cone peaks
CONE_PEAKS = {
    'normal': {'L': 564, 'M': 534, 'S': 420},
    'deutan': {'L': 564, 'M': 560, 'S': 420},  # M' shift
    'protan': {'L': 534, 'M': 534, 'S': 420},  # L' shift (L≈M)
}

# 8색 dominant wavelength
COLOR_WL = {
    'red': 625,
    'orange': 600,
    'yellow': 580,
    'green': 530,
    'cyan': 490,
    'blue': 470,
    'purple': 440,
    'magenta': 420  # Non-spectral, S-biased approximation
}

# ============================================================
# Compute Single-Color Opponency
# ============================================================

def compute_single_color_opponency(color_wl, cone_peaks):
    """
    Compute (L-M, S-(L+M)) for a single color
    """
    results = {}
    for color, wl in color_wl.items():
        L = cone_response(wl, cone_peaks['L'])
        M = cone_response(wl, cone_peaks['M'])
        S = cone_response(wl, cone_peaks['S'])

        LM = L - M
        S_opp = S - (L + M) / 2

        results[color] = {'L-M': LM, 'S-(L+M)': S_opp, 'L': L, 'M': M, 'S': S}

    return pd.DataFrame(results).T

# ============================================================
# Pairwise Distance
# ============================================================

def compute_pairwise_distances(opponency_df):
    """
    2D Euclidean distance in (L-M, S-(L+M)) space
    """
    colors = opponency_df.index.tolist()
    distances = {}

    for i, c1 in enumerate(colors):
        for j, c2 in enumerate(colors):
            if i < j:
                p1 = opponency_df.loc[c1, ['L-M', 'S-(L+M)']].values
                p2 = opponency_df.loc[c2, ['L-M', 'S-(L+M)']].values
                dist = np.linalg.norm(p1 - p2)
                distances[(c1, c2)] = dist

    return distances

# ============================================================
# Main Analysis
# ============================================================

if __name__ == '__main__':
    print("="*70)
    print("Cone Opponency 정확한 계산")
    print("="*70)

    # Compute for normal, deutan, protan
    normal_opp = compute_single_color_opponency(COLOR_WL, CONE_PEAKS['normal'])
    deutan_opp = compute_single_color_opponency(COLOR_WL, CONE_PEAKS['deutan'])
    protan_opp = compute_single_color_opponency(COLOR_WL, CONE_PEAKS['protan'])

    print("\n### Normal Opponency")
    print(normal_opp[['L-M', 'S-(L+M)']].to_markdown(floatfmt=".3f"))

    print("\n### Deutan Opponency")
    print(deutan_opp[['L-M', 'S-(L+M)']].to_markdown(floatfmt=".3f"))

    print("\n### Protan Opponency")
    print(protan_opp[['L-M', 'S-(L+M)']].to_markdown(floatfmt=".3f"))

    # Pairwise distances
    normal_dist = compute_pairwise_distances(normal_opp)
    deutan_dist = compute_pairwise_distances(deutan_opp)
    protan_dist = compute_pairwise_distances(protan_opp)

    # Key pairs for sub-08 (deutan)
    key_pairs_deutan = [
        ('red', 'orange'),
        ('orange', 'yellow'),
        ('yellow', 'green'),
        ('green', 'blue'),
        ('yellow', 'purple'),
        ('blue', 'purple'),
        ('cyan', 'blue'),
    ]

    print("\n" + "="*70)
    print("Sub-08 (Deutan) — Cone 예측 vs 관측")
    print("="*70)

    # SRM z-scores (from prevalidation)
    srm_z = {
        ('red', 'orange'): -0.82,
        ('orange', 'yellow'): 3.29,
        ('yellow', 'green'): 4.14,
        ('green', 'blue'): -0.89,
        ('yellow', 'purple'): 13.87,
        ('blue', 'purple'): 6.15,
        ('cyan', 'blue'): -0.95,
    }

    # RDM V2 diff (from behavioral notion.md)
    rdm_diff = {
        ('red', 'orange'): -0.605,
        ('orange', 'yellow'): 0.498,
        ('yellow', 'green'): 0.496,
        ('green', 'blue'): -0.158,
        ('yellow', 'purple'): 0.670,
        ('blue', 'purple'): 0.881,
        ('cyan', 'blue'): 0.452,
    }

    results = []
    for pair in key_pairs_deutan:
        c1, c2 = pair

        # Cone predictions
        n_dist = normal_dist[pair]
        d_dist = deutan_dist[pair]
        delta_dist = d_dist - n_dist

        # Component breakdown
        n_p1 = normal_opp.loc[c1, ['L-M', 'S-(L+M)']].values
        n_p2 = normal_opp.loc[c2, ['L-M', 'S-(L+M)']].values
        d_p1 = deutan_opp.loc[c1, ['L-M', 'S-(L+M)']].values
        d_p2 = deutan_opp.loc[c2, ['L-M', 'S-(L+M)']].values

        delta_LM = (d_p1[0] - d_p2[0]) - (n_p1[0] - n_p2[0])
        delta_S = (d_p1[1] - d_p2[1]) - (n_p1[1] - n_p2[1])

        cone_sign = '+' if delta_dist > 0 else '-'
        srm_sign = '+' if srm_z[pair] > 0 else '-'
        rdm_sign = '+' if rdm_diff[pair] > 0 else '-'

        match = "✓" if cone_sign == srm_sign else "✗"

        results.append({
            'pair': f"{c1}-{c2}",
            'normal_dist': f"{n_dist:.3f}",
            'deutan_dist': f"{d_dist:.3f}",
            'Δdist': f"{delta_dist:+.3f}",
            'ΔL-M': f"{delta_LM:+.3f}",
            'ΔS': f"{delta_S:+.3f}",
            'cone_sign': cone_sign,
            'SRM_z': f"{srm_z[pair]:+.2f}",
            'srm_sign': srm_sign,
            'RDM_diff': f"{rdm_diff[pair]:+.3f}",
            'rdm_sign': rdm_sign,
            'match': match
        })

    df = pd.DataFrame(results)
    print("\n" + df.to_markdown(index=False))

    # Count matches
    matches = df['match'].value_counts()
    print(f"\n✓ 일치: {matches.get('✓', 0)}/{len(df)}")
    print(f"✗ 불일치: {matches.get('✗', 0)}/{len(df)}")

    # Protan analysis
    print("\n" + "="*70)
    print("Sub-09 (Protan) — Cone 예측 vs 관측")
    print("="*70)

    key_pairs_protan = [
        ('red', 'orange'),
        ('red', 'magenta'),
        ('orange', 'magenta'),
        ('cyan', 'magenta'),
        ('yellow', 'purple'),
        ('green', 'blue'),
    ]

    srm_z_protan = {
        ('red', 'orange'): -1.35,
        ('red', 'magenta'): 3.52,
        ('orange', 'magenta'): 3.71,
        ('cyan', 'magenta'): 4.08,
        ('yellow', 'purple'): -3.31,
        ('green', 'blue'): -2.41,
    }

    results_protan = []
    for pair in key_pairs_protan:
        c1, c2 = pair

        n_dist = normal_dist[pair]
        p_dist = protan_dist[pair]
        delta_dist = p_dist - n_dist

        n_p1 = normal_opp.loc[c1, ['L-M', 'S-(L+M)']].values
        n_p2 = normal_opp.loc[c2, ['L-M', 'S-(L+M)']].values
        p_p1 = protan_opp.loc[c1, ['L-M', 'S-(L+M)']].values
        p_p2 = protan_opp.loc[c2, ['L-M', 'S-(L+M)']].values

        delta_LM = (p_p1[0] - p_p2[0]) - (n_p1[0] - n_p2[0])
        delta_S = (p_p1[1] - p_p2[1]) - (n_p1[1] - n_p2[1])

        cone_sign = '+' if delta_dist > 0 else '-'
        srm_sign = '+' if srm_z_protan[pair] > 0 else '-'

        match = "✓" if cone_sign == srm_sign else "✗"

        results_protan.append({
            'pair': f"{c1}-{c2}",
            'normal_dist': f"{n_dist:.3f}",
            'protan_dist': f"{p_dist:.3f}",
            'Δdist': f"{delta_dist:+.3f}",
            'ΔL-M': f"{delta_LM:+.3f}",
            'ΔS': f"{delta_S:+.3f}",
            'cone_sign': cone_sign,
            'SRM_z': f"{srm_z_protan[pair]:+.2f}",
            'srm_sign': srm_sign,
            'match': match
        })

    df_protan = pd.DataFrame(results_protan)
    print("\n" + df_protan.to_markdown(index=False))

    matches_protan = df_protan['match'].value_counts()
    print(f"\n✓ 일치: {matches_protan.get('✓', 0)}/{len(df_protan)}")
    print(f"✗ 불일치: {matches_protan.get('✗', 0)}/{len(df_protan)}")
