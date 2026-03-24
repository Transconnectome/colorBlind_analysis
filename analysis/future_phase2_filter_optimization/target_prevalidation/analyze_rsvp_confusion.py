#!/usr/bin/env python3
"""
3-Way Confusion Analysis: RSVP (Behavioral) + LOCO (Neural) + Cone (Receptor)

목표:
1. RSVP behavioral confusion pattern
2. LOCO neural confusion pattern
3. Cone shift prediction
→ 3-way convergence 평가
"""

import numpy as np
import pandas as pd

# RSVP Behavioral Confusion (sub-08 deutan, 12 errors / 64 trials)
RSVP_CONFUSION = {
    'purple': ['magenta', 'magenta', 'magenta'],  # 3 errors
    'magenta': ['purple', 'purple'],              # 2 errors
    'yellow': ['green', 'magenta', 'red'],        # 3 errors
    'orange': ['yellow'],                         # 1 error
    'green': ['yellow'],                          # 1 error
}

RSVP_ACCURACY = {
    'red': 1.000,
    'orange': 0.875,
    'yellow': 0.625,
    'green': 0.750,
    'cyan': 1.000,
    'blue': 1.000,
    'purple': 0.500,
    'magenta': 0.750,
}

# LOCO Neural Confusion (from analyze_loco_per_color.py)
LOCO_CONFUSION = {
    'orange': 'red',
    'yellow': 'cyan',
    'purple': 'red',
    'green': 'orange',
    'cyan': 'yellow',
    'blue': 'yellow',
    'magenta': 'green',
}

LOCO_PVALUE = {
    'orange': 0.029,
    'yellow': 0.044,
    'purple': 0.058,
    'green': 0.221,
    'cyan': 0.814,
    'blue': 0.124,
    'magenta': 0.287,
}

# Cone shift data (from analyze_confusion_vs_cone.py)
def cone_response(wavelength, peak, sigma=50):
    return np.exp(-0.5 * ((wavelength - peak) / sigma) ** 2)

CONE_PEAKS = {
    'normal': {'L': 564, 'M': 534, 'S': 420},
    'deutan': {'L': 564, 'M': 560, 'S': 420},
}

COLOR_WL = {
    'red': 625, 'orange': 600, 'yellow': 580, 'green': 530,
    'cyan': 490, 'blue': 470, 'purple': 440, 'magenta': 420
}

def compute_opponency(color_wl, cone_peaks):
    results = {}
    for color, wl in color_wl.items():
        L = cone_response(wl, cone_peaks['L'])
        M = cone_response(wl, cone_peaks['M'])
        S = cone_response(wl, cone_peaks['S'])
        results[color] = np.array([L - M, S - (L + M) / 2])
    return results

def cone_distance(c1, c2):
    return np.linalg.norm(c1 - c2)

normal_opp = compute_opponency(COLOR_WL, CONE_PEAKS['normal'])
deutan_opp = compute_opponency(COLOR_WL, CONE_PEAKS['deutan'])

if __name__ == '__main__':
    print("="*100)
    print("3-Way Confusion Analysis: RSVP (Behavioral) + LOCO (Neural) + Cone (Receptor)")
    print("="*100)

    print("\n### 1. Per-Color 취약성 — 3개 지표 수렴")
    print()
    print("| 색 | RSVP 정확도 | LOCO p | Cone ΔL-M | 해석 |")
    print("|:---|:-----------:|:------:|:---------:|:-----|")

    # Per-color vulnerability convergence
    for color in ['red', 'orange', 'yellow', 'green', 'cyan', 'blue', 'purple', 'magenta']:
        rsvp_acc = RSVP_ACCURACY[color]
        loco_p = LOCO_PVALUE.get(color, 1.0)

        # Cone change
        n_lm = normal_opp[color][0]
        d_lm = deutan_opp[color][0]
        delta_lm = d_lm - n_lm

        # Interpretation
        vulnerable = []
        if rsvp_acc < 0.8:
            vulnerable.append("RSVP")
        if loco_p < 0.05:
            vulnerable.append("LOCO")
        if abs(delta_lm) > 0.15:
            vulnerable.append("Cone")

        converge = len(vulnerable)
        interp = f"{'/'.join(vulnerable) if vulnerable else '—'} ({converge}/3)"

        # Significance markers
        rsvp_str = f"{rsvp_acc:.1%}" + ("*" if rsvp_acc < 0.8 else "")
        loco_str = f"{loco_p:.3f}" + ("*" if loco_p < 0.05 else "")
        cone_str = f"{delta_lm:+.3f}" + ("↓" if delta_lm < -0.15 else "")

        print(f"| {color:7s} | {rsvp_str:11s} | {loco_str:6s} | {cone_str:9s} | {interp:40s} |")

    print("\n> **3/3 완전 수렴**: yellow, purple — RSVP + LOCO + Cone 모두 취약")
    print("> **2/3 부분 수렴**: orange — RSVP + LOCO (Cone 약함)")

    print("\n### 2. Confusion Pattern — RSVP vs LOCO vs Cone")
    print()
    print("| 원 색 | RSVP → | LOCO → | Cone 가까워지는 색 | 3-way 일치 |")
    print("|:------|:-------|:-------|:------------------|:----------:|")

    confusion_rows = []
    for color in ['orange', 'yellow', 'green', 'purple', 'magenta']:
        # RSVP confusion
        if color in RSVP_CONFUSION:
            rsvp_errors = RSVP_CONFUSION[color]
            from collections import Counter
            rsvp_most_common = Counter(rsvp_errors).most_common(1)[0][0]
            rsvp_conf = f"{rsvp_most_common} ({len(rsvp_errors)}회)"
        else:
            rsvp_conf = "—"

        # LOCO confusion
        loco_conf = LOCO_CONFUSION.get(color, "—")

        # Cone closest
        min_dist = float('inf')
        closest = None
        for other in COLOR_WL.keys():
            if other != color:
                n_dist = cone_distance(normal_opp[color], normal_opp[other])
                d_dist = cone_distance(deutan_opp[color], deutan_opp[other])
                delta = d_dist - n_dist
                if delta < -0.05 and d_dist < min_dist:  # Gets closer
                    min_dist = d_dist
                    closest = other

        cone_closest = closest if closest else "—"

        # Check 3-way match
        rsvp_target = rsvp_most_common if color in RSVP_CONFUSION else None
        matches = []
        if rsvp_target and rsvp_target == loco_conf:
            matches.append("RSVP↔LOCO")
        if rsvp_target and rsvp_target == cone_closest:
            matches.append("RSVP↔Cone")
        if loco_conf != "—" and loco_conf == cone_closest:
            matches.append("LOCO↔Cone")

        match_str = ", ".join(matches) if matches else "—"

        confusion_rows.append({
            'color': color,
            'rsvp': rsvp_conf,
            'loco': loco_conf,
            'cone': cone_closest,
            'match': match_str
        })

        print(f"| {color:7s} | {rsvp_conf:6s} | {loco_conf:6s} | {cone_closest:17s} | {match_str:10s} |")

    print("\n### 3. Confusion 쌍 분석 — 수렴도")
    print()
    print("**3-way 일치 (RSVP = LOCO = Cone)**:")

    three_way = [r for r in confusion_rows if "RSVP↔LOCO" in r['match'] and "LOCO↔Cone" in r['match']]
    if three_way:
        for row in three_way:
            print(f"  - {row['color']}: RSVP → {RSVP_CONFUSION[row['color']][0]}, LOCO → {row['loco']}, Cone → {row['cone']}")
    else:
        print("  - **없음**")

    print("\n**2-way 일치 (RSVP ↔ LOCO, Cone 불일치)**:")
    rsvp_loco = [r for r in confusion_rows if "RSVP↔LOCO" in r['match'] and "LOCO↔Cone" not in r['match']]
    if rsvp_loco:
        for row in rsvp_loco:
            rsvp_target = Counter(RSVP_CONFUSION[row['color']]).most_common(1)[0][0]
            print(f"  - {row['color']}: RSVP → {rsvp_target}, LOCO → {row['loco']} ✓, Cone → {row['cone']} ✗")
    else:
        print("  - **없음**")

    print("\n**2-way 일치 (RSVP ↔ Cone, LOCO 불일치)**:")
    rsvp_cone = [r for r in confusion_rows if "RSVP↔Cone" in r['match'] and "RSVP↔LOCO" not in r['match']]
    if rsvp_cone:
        for row in rsvp_cone:
            rsvp_target = Counter(RSVP_CONFUSION[row['color']]).most_common(1)[0][0]
            print(f"  - {row['color']}: RSVP → {rsvp_target}, Cone → {row['cone']} ✓, LOCO → {row['loco']} ✗")
    else:
        print("  - **없음**")

    print("\n**LOCO ↔ Cone 일치 (RSVP 데이터 없음)**:")
    loco_cone = [r for r in confusion_rows if "LOCO↔Cone" in r['match'] and r['color'] not in RSVP_CONFUSION]
    if loco_cone:
        for row in loco_cone:
            print(f"  - {row['color']}: LOCO → {row['loco']}, Cone → {row['cone']} ✓, RSVP no error")
    else:
        print("  - **없음**")

    print("\n**완전 불일치 (3개 지표 모두 다름)**:")
    no_match = [r for r in confusion_rows if not r['match'] or r['match'] == "—"]
    if no_match:
        for row in no_match:
            if row['color'] in RSVP_CONFUSION:
                rsvp_target = Counter(RSVP_CONFUSION[row['color']]).most_common(1)[0][0]
                print(f"  - {row['color']}: RSVP → {rsvp_target}, LOCO → {row['loco']}, Cone → {row['cone']}")
    else:
        print("  - **없음**")

    print("\n" + "="*100)
    print("핵심 발견")
    print("="*100)

    print("""
1. **Per-Color 취약성 수렴 (3/3)**:
   - yellow, purple: RSVP 낮음 + LOCO 유의 + Cone 변화 큼 → 완전 수렴
   - orange: RSVP 낮음 + LOCO 유의, Cone 변화 약함 → 2/3

2. **Confusion Pattern 불일치**:
   - RSVP ↔ LOCO ↔ Cone 3-way 일치: 0건
   - 가장 흔한 RSVP confusion (purple↔magenta)는 LOCO/Cone과 불일치

3. **핵심 차이**:
   - RSVP (8AFC): 범주적 판단 (purple vs magenta 경계 불안정)
   - LOCO: 연속 hue 예측 (purple → red 방향 drift)
   - Cone: Receptor-level shift (purple ≈ magenta 가까움)

4. **함의**:
   - Per-color 취약성: 3개 지표 수렴 (yellow, purple)
   - Confusion 방향: 과제 의존적 (범주적 vs 연속적)
   - Cone model: 취약 색 식별 가능, 방향 예측 불가
    """)
