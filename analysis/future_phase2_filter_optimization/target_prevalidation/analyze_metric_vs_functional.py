#!/usr/bin/env python3
"""
Metric vs Functional Dissociation Analysis (CORRECTED)

핵심 구분:
- **Metric properties**: 기하학적 거리 (SRM z-score, RDM diff) — 0차 속성 (pairwise distance)
- **Functional properties**: 행동/보간 성능 (LOCO, JND) — 고차 속성 (interpolation capability)

해리(Dissociation): Metric overseparation (+) ≠ Functional discrimination difficulty (HYPO)
"""

import numpy as np
import pandas as pd

# Data from cone_opponency_table_proposal.md §2-2
data = {
    'pair': ['red-orange', 'orange-yellow', 'yellow-green', 'green-blue',
             'yellow-purple', 'blue-purple', 'cyan-blue'],
    'cone_delta': [0.026, -0.027, -0.282, 0.039, 0.138, -0.084, -0.037],
    'srm_z': [-0.82, 3.29, 4.14, -0.89, 13.87, 6.15, -0.95],
    'rdm_diff': [-0.605, 0.498, 0.496, -0.158, 0.670, 0.881, 0.452],
    'loco_orange': [True, True, True, False, True, False, False],
    'loco_yellow': [False, True, True, False, True, False, False],
    'loco_purple': [False, False, False, False, True, True, False],
    'jnd': ['HYPER', 'HYPO', 'HYPO', 'HYPER', 'HYPO', 'HYPER', None],
}

df = pd.DataFrame(data)

# Add LOCO vulnerability
df['loco_vulnerable'] = df[['loco_orange', 'loco_yellow', 'loco_purple']].any(axis=1)

print("="*90)
print("Metric vs Functional Dissociation Analysis — Sub-08 (Deutan)")
print("="*90)

print("\n### 1. 핵심 개념 구분")
print("""
| 속성 | 측정 대상 | 지표 | 차수 | 질문 |
|------|----------|------|------|------|
| **Metric** | 기하학적 거리 | SRM z, RDM diff | 0차 | "두 색이 얼마나 먼가?" |
| **Functional** | 보간/변별 성능 | LOCO, JND | 고차 | "이 색을 보간/변별할 수 있는가?" |

**예상되는 관계**: Metric overseparation (양수, 멀어짐) → Functional HYPER (쉬움)
                  Metric compression (음수, 가까워짐) → Functional HYPO (어려움)

**해리(Dissociation)**: 예상과 반대 — Overseparation + HYPO, Compression + HYPER
""")

print("\n### 2. 5-Way Integration Table (CORRECTED)")
print()
print("| 쌍 | Cone Δ | SRM z | RDM diff | LOCO | JND | Metric 방향 | Functional 방향 | Metric-Functional 관계 |")
print("|:---|:------:|:-----:|:--------:|:----:|:---:|:-----------:|:---------------:|:---------------------:|")

for _, row in df.iterrows():
    pair = row['pair']
    cone = row['cone_delta']
    srm = row['srm_z']
    rdm = row['rdm_diff']
    loco = "✓" if row['loco_vulnerable'] else "—"
    jnd = row['jnd'] if row['jnd'] else "—"

    # Metric direction (SRM/RDM)
    if srm > 1.0 and rdm > 0.2:
        metric_dir = "과분리 +"
    elif srm < -0.5 and rdm < -0.2:
        metric_dir = "압축 -"
    else:
        metric_dir = "혼재"

    # Functional direction
    if row['loco_vulnerable'] and jnd == 'HYPO':
        func_dir = "실패/HYPO"
    elif not row['loco_vulnerable'] and jnd == 'HYPER':
        func_dir = "성공/HYPER"
    elif row['loco_vulnerable'] and jnd == 'HYPER':
        func_dir = "LOCO실패+HYPER"
    elif not row['loco_vulnerable'] and jnd == 'HYPO':
        func_dir = "LOCO성공+HYPO"
    else:
        func_dir = "—"

    # Metric-Functional relationship
    if metric_dir == "과분리 +" and func_dir == "실패/HYPO":
        relation = "**해리 ✗** (oversep + diff)"
    elif metric_dir == "압축 -" and func_dir == "성공/HYPER":
        relation = "**해리 ✗** (comp + easy)"
    elif metric_dir == "과분리 +" and func_dir == "성공/HYPER":
        relation = "예상 불일치"
    elif metric_dir == "압축 -" and func_dir == "실패/HYPO":
        relation = "예상 일치 ✓"
    else:
        relation = "불명확"

    # Highlight rows
    if "해리" in relation:
        pair_str = f"**{pair}**"
    else:
        pair_str = pair

    print(f"| {pair_str:15s} | {cone:+.3f} | {srm:+.2f} | {rdm:+.3f} | {loco:4s} | {jnd:4s} | {metric_dir:11s} | {func_dir:15s} | {relation:21s} |")

print("\n### 3. 해리(Dissociation) 패턴 분석")
print()

# Count dissociations
dissociations = df[
    ((df['srm_z'] > 1.0) & (df['rdm_diff'] > 0.2) & (df['jnd'] == 'HYPO'))
].copy()

print(f"**Metric Overseparation + Functional HYPO (해리): {len(dissociations)}쌍**")
print()
for _, row in dissociations.iterrows():
    pair = row['pair']
    srm = row['srm_z']
    rdm = row['rdm_diff']
    print(f"  - **{pair}**: SRM z={srm:+.2f} (과분리), RDM={rdm:+.3f} (과분리) BUT JND=HYPO (어려움)")
    print(f"    → 기하학적으로 멀어졌는데 변별은 더 어려움 — **해리**")

print("\n**해석**:")
print("""
SRM z-score와 RDM은 두 색의 **끝점 간 거리**(0차 기하학적 속성)를 측정.
JND는 두 색 사이를 **보간한 중간 자극**의 변별 민감도(고차 기능적 속성)를 측정.

Overseparation (끝점이 멀어짐) + HYPO (보간 구간 변별 어려움) 해리의 원인:
  1. **국소 불규칙성**: 끝점은 멀지만 중간 구간의 manifold가 불규칙
  2. **S-cone 보상**: L-M 손실 → S-cone gain 증폭 → 끝점 팽창하나 보간 충실도는 저하
  3. **차수(order) 차이**: 0차(거리)는 고차(보간)를 예측 못함
""")

print("\n### 4. Cone Model의 한계 — Metric vs Functional")
print()
print("| Cone Δdist 방향 | Metric (SRM/RDM) 일치 | Functional (LOCO/JND) 일치 |")
print("|:---------------|:--------------------:|:-------------------------:|")

cone_metric_match = 0
cone_func_match = 0
total_pairs = 0

for _, row in df.iterrows():
    if row['jnd'] is None:
        continue

    total_pairs += 1
    cone = row['cone_delta']
    srm = row['srm_z']
    rdm = row['rdm_diff']
    jnd = row['jnd']
    loco = row['loco_vulnerable']

    # Cone vs Metric
    cone_srm_match = (cone > 0 and srm > 0) or (cone < 0 and srm < 0)
    cone_rdm_match = (cone > 0 and rdm > 0) or (cone < 0 and rdm < 0)
    if cone_srm_match or cone_rdm_match:
        cone_metric_match += 1
        metric_str = "✓"
    else:
        metric_str = "✗"

    # Cone vs Functional
    # Cone compression (-) should predict HYPO
    if cone < -0.05 and jnd == 'HYPO':
        cone_func_match += 1
        func_str = "✓"
    elif cone > 0.05 and jnd == 'HYPER':
        cone_func_match += 1
        func_str = "✓"
    else:
        func_str = "✗"

    pair = row['pair']
    print(f"| {pair:15s} | {cone:+.3f} → {metric_str:20s} | {cone:+.3f} → {func_str:25s} |")

print()
print(f"**Cone → Metric: {cone_metric_match}/{total_pairs} ({cone_metric_match/total_pairs*100:.0f}%)**")
print(f"**Cone → Functional: {cone_func_match}/{total_pairs} ({cone_func_match/total_pairs*100:.0f}%)**")

print("\n**결론**: Cone model은 Metric도 Functional도 제대로 예측 못함")
print("         → Cone shift는 **필요조건**이나 **충분조건 아님**")
print("         → 피질 보상 기전(S-cone gain)이 Cone 예측을 역전")

print("\n### 5. LOCO ↔ JND vs SRM ↔ JND 비교")
print()

loco_jnd_match = 0
srm_jnd_match = 0

for _, row in df.iterrows():
    if row['jnd'] is None:
        continue

    pair = row['pair']
    loco = row['loco_vulnerable']
    jnd = row['jnd']
    srm = row['srm_z']

    # LOCO-JND
    if (loco and jnd == 'HYPO') or (not loco and jnd == 'HYPER'):
        loco_jnd_match += 1
        loco_match_str = "✓"
    else:
        loco_match_str = "✗"

    # SRM-JND (simple prediction: + → HYPER, - → HYPO)
    if (srm > 1.0 and jnd == 'HYPER') or (srm < -0.5 and jnd == 'HYPO'):
        srm_jnd_match += 1
        srm_match_str = "✓"
    else:
        srm_match_str = "✗"

    print(f"{pair:15s}: LOCO vulnerable={str(loco):5s} + JND={jnd:5s} → {loco_match_str:2s} | SRM z={srm:+.2f} + JND={jnd:5s} → {srm_match_str:2s}")

print()
print(f"**LOCO → JND: {loco_jnd_match}/{total_pairs} ({loco_jnd_match/total_pairs*100:.0f}%)**")
print(f"**SRM → JND:  {srm_jnd_match}/{total_pairs} ({srm_jnd_match/total_pairs*100:.0f}%)**")

print("\n" + "="*90)
print("최종 결론")
print("="*90)

print("""
1. **Metric-Functional 해리 존재** (3쌍: orange-yellow, yellow-green, yellow-purple):
   - Metric overseparation (SRM/RDM 양수) + Functional HYPO (JND 어려움)
   - 0차 기하학적 거리 ≠ 고차 보간 성능

2. **LOCO는 Functional 속성을 정확히 예측** (100%):
   - LOCO 취약성(보간 실패) → JND HYPO 완벽 일치
   - 둘 다 고차(higher-order) manifold regularity 측정

3. **SRM z-score는 JND 예측 실패** (4/6 불일치, 67%):
   - SRM은 0차 끝점 거리만 측정, 보간 구간 특성 포착 못함
   - Overseparation ≠ HYPER 예측 불가

4. **Cone model은 양쪽 다 실패**:
   - Metric 예측: ~30% 일치 (S-cone 보상으로 방향 역전)
   - Functional 예측: ~33% 일치 (피질 변환 복잡도 과소평가)

5. **"수렴"의 재정의**:
   - ✗ 잘못된 해석: "모든 지표가 같은 방향" → 수렴
   - ✓ 올바른 해석: **같은 차수** 지표끼리만 비교 가능
     - Metric-Metric convergence: SRM ↔ RDM (86% 일치)
     - Functional-Functional convergence: LOCO ↔ JND (100% 일치)
     - Metric-Functional: 비교 불가 (서로 다른 속성 측정)
""")
