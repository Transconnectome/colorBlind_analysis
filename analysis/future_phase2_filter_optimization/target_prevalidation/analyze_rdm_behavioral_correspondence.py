#!/usr/bin/env python3
"""
RDM과 대응되는 행동 지표 탐색

질문:
1. RDM overseparation은 어떤 행동 능력을 예측하는가?
2. JND와 RDM이 해리하는 이유는?
3. 추가 행동 실험이 필요한가?

가설:
- RDM overseparation = Categorical distinctiveness (범주적 구분성)
- JND HYPO = Fine discrimination deficit (미세 변별력 결손)
- 둘은 다른 차원의 속성 → trade-off 가능
"""

import numpy as np
import pandas as pd

# Data
data = {
    'pair': ['red-orange', 'orange-yellow', 'yellow-green', 'green-blue',
             'yellow-purple', 'blue-purple', 'cyan-blue'],
    'rdm_diff': [-0.605, 0.498, 0.496, -0.158, 0.670, 0.881, 0.452],
    'srm_z': [-0.82, 3.29, 4.14, -0.89, 13.87, 6.15, -0.95],
    'jnd': ['HYPER', 'HYPO', 'HYPO', 'HYPER', 'HYPO', 'HYPER', None],
    'loco_vulnerable': [True, True, True, False, True, True, False],
    # RSVP 8AFC 정확도 (범주적 판단)
    'rsvp_constituent': {
        'red-orange': ['red', 'orange'],
        'orange-yellow': ['orange', 'yellow'],
        'yellow-green': ['yellow', 'green'],
        'green-blue': ['green', 'blue'],
        'yellow-purple': ['yellow', 'purple'],
        'blue-purple': ['blue', 'purple'],
        'cyan-blue': ['cyan', 'blue'],
    },
}

# RSVP accuracy per color (categorical classification)
rsvp_accuracy = {
    'red': 1.000,
    'orange': 0.875,
    'yellow': 0.625,
    'green': 0.750,
    'cyan': 1.000,
    'blue': 1.000,
    'purple': 0.500,
    'magenta': 0.750,
}

df = pd.DataFrame(data)

print("="*90)
print("RDM과 행동 지표 대응 분석")
print("="*90)

print("\n### 1. RDM vs JND vs RSVP — 3가지 행동 지표 비교")
print()
print("**가설**:")
print("- RDM overseparation (+) → RSVP categorical distinctiveness (높은 정확도)")
print("- JND HYPO → Fine discrimination deficit (끝점 사이 변별 어려움)")
print("- RSVP = 범주적 판단, JND = 연속적 변별 → 서로 다른 속성")
print()

# Add RSVP pairwise distinctiveness
df['rsvp_min_acc'] = df.apply(
    lambda row: min([rsvp_accuracy[c] for c in data['rsvp_constituent'][row['pair']]]),
    axis=1
)
df['rsvp_mean_acc'] = df.apply(
    lambda row: np.mean([rsvp_accuracy[c] for c in data['rsvp_constituent'][row['pair']]]),
    axis=1
)

print("| 쌍 | RDM diff | JND | RSVP min | RSVP mean | 해석 |")
print("|:---|:--------:|:---:|:--------:|:---------:|:-----|")

for _, row in df.iterrows():
    pair = row['pair']
    rdm = row['rdm_diff']
    jnd = row['jnd'] if row['jnd'] else '—'
    rsvp_min = row['rsvp_min_acc']
    rsvp_mean = row['rsvp_mean_acc']

    # Interpretation
    if rdm > 0.3 and jnd == 'HYPO':
        interp = "RDM+ JND- → 범주↑ 연속↓"
    elif rdm < -0.3 and jnd == 'HYPER':
        interp = "RDM- JND+ → 범주↓ 연속↑"
    elif rdm > 0.3 and jnd == 'HYPER':
        interp = "RDM+ JND+ → 둘 다 좋음"
    else:
        interp = "약한 효과"

    print(f"| {pair:15s} | {rdm:+8.3f} | {jnd:4s} | {rsvp_min:8.1%} | {rsvp_mean:9.1%} | {interp:20s} |")

print("\n### 2. RDM Overseparation의 의미 재해석")
print()
print("**문제**: RDM overseparation (+) + JND HYPO = 해리")
print()
print("**가설**: RDM은 범주적 구분성(categorical distinctiveness)을 반영")
print()

# Correlation analysis
valid_pairs = df[df['jnd'].notna()].copy()

# RDM vs RSVP
from scipy.stats import spearmanr

rdm_rsvp_min_r, rdm_rsvp_min_p = spearmanr(valid_pairs['rdm_diff'], valid_pairs['rsvp_min_acc'])
rdm_rsvp_mean_r, rdm_rsvp_mean_p = spearmanr(valid_pairs['rdm_diff'], valid_pairs['rsvp_mean_acc'])

print(f"**RDM vs RSVP min accuracy**: ρ = {rdm_rsvp_min_r:.3f}, p = {rdm_rsvp_min_p:.3f}")
print(f"**RDM vs RSVP mean accuracy**: ρ = {rdm_rsvp_mean_r:.3f}, p = {rdm_rsvp_mean_p:.3f}")
print()

# Check if RDM+ predicts RSVP accuracy
oversep_pairs = valid_pairs[valid_pairs['rdm_diff'] > 0.3]
compression_pairs = valid_pairs[valid_pairs['rdm_diff'] < -0.3]

print(f"**RDM overseparation (>+0.3) 쌍들**: {len(oversep_pairs)}쌍")
print(f"  - RSVP mean accuracy: {oversep_pairs['rsvp_mean_acc'].mean():.1%}")
print()
print(f"**RDM compression (<-0.3) 쌍들**: {len(compression_pairs)}쌍")
print(f"  - RSVP mean accuracy: {compression_pairs['rsvp_mean_acc'].mean():.1%}")
print()

print("### 3. 범주적 vs 연속적 속성의 해리")
print()
print("| 속성 | 측정 지표 | 예측하는 행동 | 우리 데이터 |")
print("|:-----|:---------|:-------------|:-----------|")
print("| **Categorical distinctiveness** | RDM, SRM | Same-different, RSVP classification | RDM+ 쌍의 RSVP 정확도 |")
print("| **Fine discriminability** | JND, LOCO | Continuous interpolation, gradient perception | JND HYPO 쌍의 변별 어려움 |")
print()

print("**핵심 통찰**:")
print("""
1. **RDM overseparation = Categorical separation 증가**
   - 두 색이 복셀 공간에서 멀어짐 → 범주적으로 구분하기 쉬움
   - 예: orange vs yellow를 "다르다"고 빠르게 판단 가능
   - RSVP 8AFC에서 높은 정확도 예측

2. **JND HYPO = Fine discrimination 결손**
   - 두 색 사이 중간 색을 변별하기 어려움
   - 예: orange-yellow 구간의 미세한 차이 못 느낌
   - LOCO interpolation 실패와 일치 (100%)

3. **Trade-off 가능성**:
   - Categorical separation ↑ → Fine resolution ↓
   - S-cone gain → 범주 과분리 but 연속 표상 왜곡
""")

print("\n### 4. 현재 데이터로 검증 가능한 것")
print()

# Check classification accuracy hypothesis
print("**가설**: RDM overseparation → RSVP 8AFC constituent colors 높은 정확도")
print()
print("| 쌍 | RDM | 구성 색 | RSVP 정확도 | 검증 |")
print("|:---|:---:|:-------|:-----------:|:----:|")

for _, row in df.iterrows():
    pair = row['pair']
    rdm = row['rdm_diff']
    colors = data['rsvp_constituent'][pair]
    accs = [rsvp_accuracy[c] for c in colors]
    acc_str = ", ".join([f"{c}: {rsvp_accuracy[c]:.0%}" for c in colors])

    # Check if overseparation predicts high accuracy
    if rdm > 0.3:
        expected = "높음"
        observed = "높음" if min(accs) > 0.7 else "낮음"
        match = "✓" if observed == expected else "✗"
    elif rdm < -0.3:
        expected = "낮음"
        observed = "높음" if min(accs) > 0.7 else "낮음"
        match = "✓" if observed == expected else "✗"
    else:
        expected = "—"
        match = "—"

    print(f"| {pair:15s} | {rdm:+.2f} | {acc_str:30s} | {expected:4s} | {match:4s} |")

print("\n### 5. 필요한 추가 실험")
print()
print("**현재 한계**: RSVP 8AFC만으로는 범주적 구분성 직접 측정 어려움")
print("  - RSVP는 8개 색 전체에 대한 classification")
print("  - Pairwise categorical distinctiveness는 측정 안 됨")
print()
print("**제안 1: Same-Different Task (2AFC)**")
print("```")
print("자극: 두 색을 sequential 또는 simultaneous 제시")
print("과제: '같다' vs '다르다' 빠르게 판단 (speeded response)")
print("가설: RDM overseparation 쌍 → 빠르고 정확한 'different' 판단")
print("      JND HYPO와 독립적 (JND는 fine threshold, same-diff는 categorical)")
print("```")
print()
print("**제안 2: Rapid Categorization (Go/No-Go)**")
print("```")
print("자극: 한 색 제시")
print("과제: 특정 범주(예: warm colors)에 속하면 Go, 아니면 No-Go")
print("가설: RDM overseparation → 범주 경계가 명확 → 빠른 반응")
print("```")
print()
print("**제안 3: Visual Search / Pop-out**")
print("```")
print("자극: 한 색의 distractor 중 다른 색 target")
print("과제: Target 빠르게 찾기")
print("가설: RDM overseparation 쌍 → target pop-out 강함")
print("```")

print("\n### 6. 현재 데이터의 재분석 — Forward Model Classification")
print()
print("**아이디어**: Forward model의 8-way classification 정확도 확인")
print("  - 우리 이미 가지고 있는 데이터!")
print("  - ridge_gcv decoder의 classification accuracy per color")
print("  - LOCO는 interpolation 측정, 하지만 같은 모델로 classification도 가능")
print()
print("**검증 가능**:")
print("```python")
print("# Pseudo-code")
print("for each subject:")
print("    for each color:")
print("        classification_acc = argmax(decoder prediction) == true_color")
print("        ")
print("# Hypothesis:")
print("# RDM overseparation 쌍의 constituent colors → 높은 classification accuracy")
print("# JND HYPO는 classification과 무관 (interpolation만 영향)")
print("```")

print("\n### 7. RDM의 재정의")
print()
print("| 기존 해석 | 문제점 | 새로운 해석 |")
print("|:---------|:------|:-----------|")
print("| RDM = 신경 거리 | JND와 해리 → 설명 불가 | RDM = 범주적 구분성 (categorical distinctiveness) |")
print("| Overseparation = 좋음 | HYPO와 모순 | Overseparation = 범주 구분 용이, 연속 표상 왜곡 |")
print("| RDM → 변별력 | 예측 실패 (33%) | RDM → categorical discrimination (검증 필요) |")
print()

print("### 8. 논문 전략")
print()
print("**Option 1: 추가 실험 없이 재해석 (현재 데이터 활용)**")
print("```")
print("- RDM overseparation = categorical separation (speculative)")
print("- Classification accuracy 분석 (이미 가능)")
print("- RSVP 8AFC 결과와 연결 (exploratory)")
print("- Discussion에서 same-different task 제안")
print("```")
print()
print("**Option 2: 파일럿 행동 실험 추가 (1-2주)**")
print("```")
print("- Same-different task (3-5 color pairs)")
print("- RDM overseparation 쌍 vs compression 쌍 비교")
print("- 빠른 검증 → stronger claim")
print("```")
print()
print("**Option 3: Forward model classification 분석 먼저 (1-2일)**")
print("```")
print("- 기존 LOCO 데이터 재분석")
print("- Per-color classification accuracy 계산")
print("- RDM overseparation → high classification accuracy 검증")
print("- 이게 성공하면 same-different 없이도 충분한 evidence")
print("```")

print("\n" + "="*90)
print("결론 및 제안")
print("="*90)
print("""
**핵심 발견**:
RDM overseparation과 JND HYPO의 해리는 두 지표가 **서로 다른 차원**을 측정하기 때문:
- RDM: Categorical distinctiveness (범주적 구분성)
- JND: Fine discriminability (연속적 변별력)

**즉시 실행 가능** (추가 실험 없이):
1. Forward model classification accuracy 분석 (우선!)
2. RSVP 8AFC와 RDM 관계 재분석
3. Discussion: Categorical vs continuous representation trade-off

**추가 실험 고려** (stronger evidence):
1. Same-different task (가장 직접적)
2. Rapid categorization
3. Visual search

**추천 순서**:
Step 1: Classification accuracy 분석 (1-2일)
Step 2: 결과 확인 후 추가 실험 필요성 판단
Step 3: 없어도 될 것 같으면 재해석으로 진행, 필요하면 same-different 파일럿
""")
