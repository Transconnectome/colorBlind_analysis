#!/usr/bin/env python3
"""
Confusion Pattern vs Cone Shift Analysis

분석 목표:
1. LOCO confusion pattern: 어떤 색이 어떤 색으로 헷갈리는가?
2. Cone shift 예측: 이 confusion을 예측하는가?
3. 색 쌍이 실제로 가까워지는가 vs 헷갈리는가?
"""

import numpy as np
import pandas as pd

# Cone fundamentals
def cone_response(wavelength, peak, sigma=50):
    return np.exp(-0.5 * ((wavelength - peak) / sigma) ** 2)

CONE_PEAKS = {
    'normal': {'L': 564, 'M': 534, 'S': 420},
    'deutan': {'L': 564, 'M': 560, 'S': 420},
}

COLOR_WL = {
    'red': 625,
    'orange': 600,
    'yellow': 580,
    'green': 530,
    'cyan': 490,
    'blue': 470,
    'purple': 440,
    'magenta': 420
}

def compute_opponency(color_wl, cone_peaks):
    """Compute (L-M, S-(L+M)) for each color"""
    results = {}
    for color, wl in color_wl.items():
        L = cone_response(wl, cone_peaks['L'])
        M = cone_response(wl, cone_peaks['M'])
        S = cone_response(wl, cone_peaks['S'])

        LM = L - M
        S_opp = S - (L + M) / 2

        results[color] = np.array([LM, S_opp])

    return results

def cone_distance(c1, c2):
    """2D Euclidean distance in cone opponency space"""
    return np.linalg.norm(c1 - c2)

# LOCO Confusion data from analyze_loco_per_color.py
CONFUSION_SUB08 = {
    'orange': 'red',      # 344° → red
    'yellow': 'cyan',     # 178° → cyan
    'purple': 'red',      # 5° → red
    'green': 'orange',    # 31° → orange
    'cyan': 'yellow',     # 86° → yellow
    'blue': 'yellow',     # 84° → yellow
    'magenta': 'green',   # 127° → green
}

if __name__ == '__main__':
    print("="*90)
    print("Confusion Pattern vs Cone Shift Analysis — Sub-08 (Deutan)")
    print("="*90)

    # Compute cone opponency
    normal_opp = compute_opponency(COLOR_WL, CONE_PEAKS['normal'])
    deutan_opp = compute_opponency(COLOR_WL, CONE_PEAKS['deutan'])

    print("\n### 1. Confusion Pattern 분석")
    print("\n| Confused Color | Predicted As | 해석 |")
    print("|:---------------|:-------------|:-----|")

    for confused, predicted in CONFUSION_SUB08.items():
        print(f"| {confused:14s} | {predicted:12s} | CVD {confused} → Normal {predicted} 근처 |")

    print("\n### 2. Cone Distance 검증 — Confusion 쌍이 실제로 가까워지는가?")
    print()
    print("| 쌍 (Confused → Predicted) | Normal Dist | Deutan Dist | Δdist | 가까워짐? | Confusion 설명 가능? |")
    print("|:--------------------------|:-----------:|:-----------:|:-----:|:--------:|:-------------------:|")

    results = []
    for confused, predicted in CONFUSION_SUB08.items():
        # Cone distances
        n_dist = cone_distance(normal_opp[confused], normal_opp[predicted])
        d_dist = cone_distance(deutan_opp[confused], deutan_opp[predicted])
        delta = d_dist - n_dist

        closer = "✓ YES" if delta < -0.05 else "— NO" if delta > 0.05 else "≈"
        explain = "✓" if delta < -0.05 else "✗"

        results.append({
            'pair': f"{confused} → {predicted}",
            'normal_dist': f"{n_dist:.3f}",
            'deutan_dist': f"{d_dist:.3f}",
            'delta': f"{delta:+.3f}",
            'closer': closer,
            'explain': explain
        })

        print(f"| {confused:9s} → {predicted:9s} | {n_dist:11.3f} | {d_dist:11.3f} | {delta:+5.3f} | {closer:8s} | {explain:19s} |")

    df = pd.DataFrame(results)
    n_explained = sum([1 for r in results if r['explain'] == '✓'])

    print(f"\n**Cone model 설명력: {n_explained}/{len(results)} ({n_explained/len(results)*100:.0f}%)**")

    print("\n### 3. 대안 분석 — CVD 색이 Normal 어느 색에 가까워지는가?")
    print()
    print("| CVD Color | Closest Normal Color | Distance | Interpretation |")
    print("|:----------|:---------------------|:--------:|:---------------|")

    for cvd_color in COLOR_WL.keys():
        # Find which normal color is closest to this CVD color
        min_dist = float('inf')
        closest_normal = None

        for normal_color in COLOR_WL.keys():
            dist = cone_distance(deutan_opp[cvd_color], normal_opp[normal_color])
            if dist < min_dist:
                min_dist = dist
                closest_normal = normal_color

        # Compare with confusion pattern
        confused_as = CONFUSION_SUB08.get(cvd_color, '—')
        match = "✓" if closest_normal == confused_as else "✗"

        interp = f"Cone: → {closest_normal}, LOCO: → {confused_as} ({match})"

        print(f"| {cvd_color:9s} | {closest_normal:20s} | {min_dist:8.3f} | {interp:40s} |")

    print("\n### 4. 역방향 분석 — 어떤 색들이 실제로 가까워지는가?")
    print()
    print("| 색 쌍 | Normal Dist | Deutan Dist | Δdist | 설명 |")
    print("|:------|:-----------:|:-----------:|:-----:|:-----|")

    all_pairs = []
    colors = list(COLOR_WL.keys())

    for i, c1 in enumerate(colors):
        for j, c2 in enumerate(colors):
            if i < j:
                n_dist = cone_distance(normal_opp[c1], normal_opp[c2])
                d_dist = cone_distance(deutan_opp[c1], deutan_opp[c2])
                delta = d_dist - n_dist
                all_pairs.append({
                    'pair': f"{c1}-{c2}",
                    'delta': delta,
                    'n_dist': n_dist,
                    'd_dist': d_dist,
                    'c1': c1,
                    'c2': c2
                })

    # Sort by delta (most compression first)
    all_pairs_sorted = sorted(all_pairs, key=lambda x: x['delta'])

    print("\n**가장 많이 압축된 쌍 (Top 5):**")
    for pair in all_pairs_sorted[:5]:
        confused_1 = CONFUSION_SUB08.get(pair['c1'], '—')
        confused_2 = CONFUSION_SUB08.get(pair['c2'], '—')
        confusion_match = "✓" if (confused_1 == pair['c2'] or confused_2 == pair['c1']) else "—"

        print(f"| {pair['pair']:15s} | {pair['n_dist']:11.3f} | {pair['d_dist']:11.3f} | {pair['delta']:+5.3f} | Compression, Confusion: {confusion_match} |")

    print("\n**가장 많이 팽창된 쌍 (Top 5):**")
    for pair in all_pairs_sorted[-5:]:
        confused_1 = CONFUSION_SUB08.get(pair['c1'], '—')
        confused_2 = CONFUSION_SUB08.get(pair['c2'], '—')
        confusion_match = "✓" if (confused_1 == pair['c2'] or confused_2 == pair['c1']) else "—"

        print(f"| {pair['pair']:15s} | {pair['n_dist']:11.3f} | {pair['d_dist']:11.3f} | {pair['delta']:+5.3f} | Expansion, Confusion: {confusion_match} |")

    print("\n" + "="*90)
    print("결론")
    print("="*90)

    print(f"""
1. **Cone model은 confusion pattern을 설명하지 못함**:
   - Confusion 쌍 {len(results)}개 중 {n_explained}개만 cone 압축으로 설명 가능
   - 예: orange→red confusion, but cone distance INCREASED

2. **CVD 색의 "closest normal" ≠ LOCO confusion**:
   - Cone space에서 가장 가까운 normal 색 ≠ LOCO가 예측한 색

3. **압축 vs Confusion 불일치**:
   - Cone level에서 가장 압축된 쌍 ≠ LOCO confusion 쌍
   - 피질 변환 (S-cone gain 등)이 cone 예측을 역전

4. **핵심**: Confusion은 **피질 표상**의 문제, cone shift로 직접 예측 불가
   """)
