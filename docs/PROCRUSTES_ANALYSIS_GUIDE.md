# Procrustes Analysis 완전 가이드

## 목차

1. [Procrustes Analysis란?](#1-procrustes-analysis란)
2. [수학적 정의](#2-수학적-정의)
3. [무엇을 측정하는가?](#3-무엇을-측정하는가)
4. [당신의 결과 해석](#4-당신의-결과-해석)
5. [시각화로 이해하기](#5-시각화로-이해하기)
6. [RDM Correlation과의 차이](#6-rdm-correlation과의-차이)
7. [논문에서 어떻게 쓰나](#7-논문에서-어떻게-쓰나)

---

## 1. Procrustes Analysis란?

### 기원

**Procrustes (프로크루스테스)**: 그리스 신화의 강도
- 여행자를 침대에 맞추기 위해 키를 잘라내거나 늘림
- **Procrustes analysis**: 두 데이터 세트를 "맞추기" 위해 변환

### 개념

**핵심 아이디어:**
```
두 점 구름(point clouds)이 있을 때,
하나를 다른 하나에 최적으로 맞추면
얼마나 비슷한가?
```

**허용하는 변환:**
1. **회전 (Rotation)**: 좌표계 회전
2. **크기 조정 (Scaling)**: 전체 크기 변경
3. **이동 (Translation)**: 중심점 이동
4. **반사 (Reflection)**: 거울상 (선택적)

**측정:**
- 최적 변환 후 남은 차이 = **Disparity**
- 1 - Disparity = **Stability** (0~1 scale)

---

## 2. 수학적 정의

### Input

두 행렬:
```
X: (n_points, n_dimensions) = (8 colors, 429 voxels)
Y: (n_points, n_dimensions) = (8 colors, 429 voxels)
```

### 알고리즘

```
Step 1: Center (translation)
X_centered = X - mean(X)
Y_centered = Y - mean(Y)

Step 2: Scale (normalization)
X_norm = X_centered / ||X_centered||
Y_norm = Y_centered / ||Y_centered||

Step 3: Find optimal rotation R
Minimize: ||X_norm - Y_norm @ R||²
Solution: SVD(X_norm.T @ Y_norm)

Step 4: Apply transform
Y_transformed = Y_norm @ R

Step 5: Compute disparity
disparity = sum((X_norm - Y_transformed)²) / n_points
```

### Output

- **Disparity** (d): 0~1
  - 0 = perfect match
  - 1 = completely different

- **Stability** (s = 1 - d): 0~1
  - 1 = perfect match
  - 0 = completely different

---

## 3. 무엇을 측정하는가?

### ✅ 고려하는 것: Pattern Geometry (기하학적 구조)

#### 1. **Relative positions (상대적 위치)**
```python
# 8 colors in voxel space
Red:    [v1, v2, ..., v429]
Blue:   [v1', v2', ..., v429']
...

# Question:
# - Red와 Blue 사이의 거리는 Half 1과 Half 2에서 비슷한가?
# - Red, Blue, Yellow가 만드는 삼각형 모양은 비슷한가?
```

**측정:**
- Pairwise distances 보존
- Angular relationships 보존
- Cluster structure 보존

#### 2. **Shape of the point cloud (점 구름의 모양)**
```
8 colors = 8 points in 429-dimensional space

Question:
이 8개 점들이 만드는 전체 "모양"이
Half 1과 Half 2에서 비슷한가?
```

**예시 (2D):**
```
Half 1:     ●  ●          Half 2:  ●  ●
             ●   ●                 ●  ●
            ●   ●                  ● ●
             ● ●                   ●●

Shape: 비슷함 (약간 회전/크기만 다름)
Procrustes: High stability
```

#### 3. **Activation patterns (간접적)**
```python
# Each color = activation pattern across voxels
Red:  [활성화 패턴 in 429 voxels]
Blue: [활성화 패턴 in 429 voxels]

# Procrustes가 이 패턴들 간의
# geometric relationships을 측정
```

**중요:**
- 개별 voxel values를 직접 비교 ❌
- Voxel patterns이 만드는 geometry 비교 ✅

### ❌ 무시하는 것: 좌표계 차이

#### 1. **Rotation (회전)**
```
Half 1: Red=[1,0], Blue=[0,1]
Half 2: Red=[0,1], Blue=[1,0]  # 90도 회전

→ Disparity ≈ 0 (회전만 다르므로)
→ Stability ≈ 1 (본질적으로 같은 구조)
```

#### 2. **Scaling (크기)**
```
Half 1: Red=[1.0, 0.5]
Half 2: Red=[2.0, 1.0]  # 2배 크기

→ Normalize하므로 무시
→ 상대적 관계만 중요
```

#### 3. **Translation (이동)**
```
Half 1: center at [0, 0]
Half 2: center at [10, 10]

→ Center를 제거하므로 무시
→ 중심 기준 상대적 위치만 중요
```

---

## 4. 당신의 결과 해석

### 결과 요약

| ROI | Procrustes Stability | RDM Correlation | 해석 |
|-----|---------------------|-----------------|------|
| **V1** | **0.83** ✅ | -0.04 ❌ | 좌표계만 다름 |
| **V2** | **0.82** ✅ | -0.07 ❌ | 좌표계만 다름 |
| V3 | 0.64 ⚠️ | -0.01 ❌ | 약간 불안정 |
| hV4 | 0.53 ⚠️ | -0.01 ❌ | 불안정 |

### V1, V2 해석: 매우 흥미로운 발견!

#### Procrustes 0.83의 의미

**1. Pattern geometry가 매우 안정적**
```
Half 1 (첫 3 runs):
- 8 colors의 상대적 위치
- Colors 간 거리 관계
- Cluster 구조

Half 2 (나머지 3 runs):
- 회전/크기 조정 후 → 거의 동일!
- 83% 일치

→ 색 표상의 기하학적 구조가 보존됨
```

**2. Activation patterns이 일관됨**
```python
# 각 color는 429 voxels의 activation pattern
# 이 패턴들 간의 relationships이 일관됨

Red-Blue relationship: preserved
Yellow-Green relationship: preserved
All pairwise relationships: preserved (83%)
```

**3. 좌표계만 다를 뿐**
```
피험자 A의 V1: 색 정보를 좌표계 A로 표현
피험자 B의 V1: 색 정보를 좌표계 B로 표현

내용은 같지만 표현 방식이 다름
→ "번역"하면 같은 내용

Procrustes = 이 번역 가능성 측정
0.83 = 매우 잘 번역됨
```

#### RDM Correlation -0.04의 의미

**1. 직접 비교는 안됨**
```
좌표계 변환 없이 직접 비교
→ Correlation 낮음 (음수 또는 0)

예시:
피험자 A: Red=[1,0], Blue=[0,1]
피험자 B: Red=[0,1], Blue=[1,0]

직접 correlation: -1 또는 0
```

**2. 하지만 문제 아님**
```
낮은 RDM correlation ≠ 나쁜 데이터
낮은 RDM correlation + 높은 Procrustes = 좌표계 문제
→ SRM으로 해결 가능!
```

### 통합 해석: Scenario C

```
✅ Procrustes stability 높음 (0.83)
❌ RDM correlation 낮음 (-0.04)

= Scenario C: Individual coordinate systems differ
```

**의미:**
1. ✅ 각 피험자는 일관된 색 정보 가짐
2. ✅ Pattern geometry 안정적
3. ⚠️ 하지만 다른 "좌표계" 사용
4. ✅ SRM으로 정렬 가능

**비유:**
```
같은 내용을 다른 언어로 쓴 것
- 내용: 일관됨 (Procrustes 높음)
- 표현: 다름 (RDM corr 낮음)
- 해결: 번역기 (SRM)
```

---

## 5. 시각화로 이해하기

### 개념 시각화

![Procrustes Concept](../results/group_level/visualizations/procrustes_concept.png)

**Panel 설명:**

**상단 왼쪽: Half 1 원본**
- 8 colors in 2D space
- 첫 3 runs의 평균 패턴

**상단 중간: Half 2 회전**
- 나머지 3 runs의 평균 패턴
- 약간 회전되고 노이즈 추가

**상단 오른쪽: 정렬 전 비교**
- 직접 overlay
- 일치하지 않음
- RDM correlation 낮음의 이유

**하단 왼쪽: Procrustes 정렬 후**
- 최적 회전/크기 조정 적용
- 거의 일치!
- 검은 점선 = 남은 차이

**하단 중간: 거리 비교**
- Bar plot: 정렬 전 vs 후
- 파란 막대 (정렬 후) 훨씬 작음

**하단 오른쪽: 요약 통계**
- Procrustes stability
- Disparity
- RDM correlation
- 해석

### ROI 비교 시각화

![ROI Comparison](../results/group_level/visualizations/procrustes_roi_comparison.png)

**Panel 설명:**

**상단 왼쪽: ROI별 Procrustes Stability**
- Boxplot + scatter points
- V1, V2: 매우 높음 (0.8+)
- V3, hV4: 중간/낮음

**상단 오른쪽: ROI별 RDM Correlation**
- 모든 ROI에서 낮음
- 하지만 Procrustes 높으면 괜찮음

**하단 왼쪽: Procrustes vs RDM Scatter**
- 각 점 = 한 피험자의 한 ROI
- 노란 박스 영역 = 당신의 V1, V2
  - High Procrustes, Low RDM → SRM 필요

**하단 오른쪽: Summary Table**
- ROI별 평균값
- Color coding:
  - Green: > 0.8 (매우 좋음)
  - Yellow: 0.6-0.8 (보통)
  - Red: < 0.6 (낮음)

---

## 6. RDM Correlation과의 차이

### 비교표

| 특징 | RDM Correlation | Procrustes Stability |
|------|----------------|---------------------|
| **측정 대상** | 색 간 거리 (직접) | 패턴 geometry (변환 후) |
| **변환 허용** | ❌ 없음 | ✅ 회전, 크기, 이동 |
| **좌표계 민감도** | ⚠️ 매우 민감 | ✅ 불변 |
| **해석** | 직접 일치도 | 구조적 유사도 |
| **당신의 V1** | -0.04 (낮음) | 0.83 (높음) |

### 언제 각각 사용하나?

#### RDM Correlation

**사용 시기:**
- 직접 비교가 의미있을 때
- 좌표계가 같다고 가정할 때
- 최종 alignment 후 평가

**당신의 경우:**
```
Before SRM: Low (-0.04)
→ 직접 비교 불가

After SRM (예상): High (0.5-0.7)
→ SRM 성공 지표
```

#### Procrustes Stability

**사용 시기:**
- Individual consistency 평가
- 좌표계 차이 무시하고 싶을 때
- SRM 필요성 진단

**당신의 경우:**
```
Procrustes 0.83 → 개인 내 일관성 높음
+ RDM -0.04 → 하지만 좌표계 다름
= SRM 필요!
```

### 수학적 차이

#### RDM Correlation

```python
# Step 1: Compute RDMs (no transformation)
RDM1 = 1 - corrcoef(Half1)  # (8, 8)
RDM2 = 1 - corrcoef(Half2)  # (8, 8)

# Step 2: Vectorize upper triangle
vec1 = RDM1[upper_triangle]  # 28 pairwise distances
vec2 = RDM2[upper_triangle]  # 28 pairwise distances

# Step 3: Correlation
corr = spearman(vec1, vec2)

# No transformation applied!
```

#### Procrustes Stability

```python
# Step 1: Center and normalize
Half1_norm = (Half1 - mean) / norm
Half2_norm = (Half2 - mean) / norm

# Step 2: Find optimal rotation
R = find_optimal_rotation(Half1_norm, Half2_norm)

# Step 3: Apply transformation
Half2_aligned = Half2_norm @ R

# Step 4: Measure residual
disparity = sum((Half1_norm - Half2_aligned)²) / n_colors
stability = 1 - disparity

# Transformation IS applied!
```

### 시각적 비교

```
Original patterns:
Half 1:  ●  ●  ●        Half 2:  ●  ●
          ●   ●                 ●  ●
         ●   ●                  ● ●
          ● ●                   ●●

RDM correlation:
직접 비교 → mismatch → low correlation

Procrustes:
1. Rotate Half 2 ↻
2. Scale Half 2 ×1.1
3. Now aligned! → high stability
```

---

## 7. 논문에서 어떻게 쓰나

### Method Section

```markdown
### Within-Subject Reliability Analysis

To assess the stability of individual color representations,
we computed split-half reliability using Procrustes analysis
(Gower, 1975).

For each subject and ROI, we divided runs into two halves
and computed the mean activation pattern for each of the
8 colors (resulting in two 8×N_voxels matrices, where N_voxels
is the number of voxels in that ROI).

Procrustes analysis measures the geometric similarity between
two point clouds by finding the optimal rotation, scaling, and
translation that minimizes the sum of squared differences.
The resulting disparity (d) quantifies the residual difference
after optimal alignment, with Procrustes stability defined as
s = 1 - d.

High Procrustes stability (s > 0.8) indicates that the
geometric structure of color representations is preserved
across runs, even if the absolute voxel-wise patterns differ
due to rotations in representational space (Haxby et al., 2011).

We compared Procrustes stability with traditional RDM correlation
to distinguish between coordinate system differences (high
Procrustes, low RDM correlation) and true instability (low both).
```

### Results Section

```markdown
### Individual Color Representations are Geometrically Stable

Procrustes analysis revealed high geometric stability of color
representations in early visual cortex (V1: 0.83 ± 0.03,
V2: 0.82 ± 0.03), indicating that the structural relationships
among colors were highly consistent across independent runs
(Figure X).

In contrast, traditional RDM correlation was near zero
(V1: -0.04 ± 0.19, V2: -0.07 ± 0.22), suggesting substantial
differences in representational coordinate systems across runs.

This dissociation—high geometric stability but low direct
correspondence—indicates that while individual subjects maintain
consistent color representational geometries, these geometries
are embedded in different coordinate systems. This pattern
motivates the use of Shared Response Modeling (Chen et al., 2015)
to align individual coordinate systems before group-level analysis.

Higher visual areas showed reduced stability (V3: 0.64 ± 0.11,
hV4: 0.53 ± 0.11), potentially reflecting lower voxel counts
and greater individual variability in these regions.
```

### Figure Legend

```markdown
Figure X. Geometric Stability of Color Representations

(A) Procrustes stability for each subject and ROI. Each point
represents one subject. Boxes show median and quartiles. Dashed
lines indicate thresholds for high (>0.8) and moderate (>0.6)
stability.

(B) RDM correlation for comparison. Note the dissociation: high
Procrustes stability but low RDM correlation in V1 and V2.

(C) Scatter plot of Procrustes stability vs. RDM correlation.
The yellow quadrant (high Procrustes, low RDM) indicates
coordinate system differences, which can be addressed through
alignment methods like SRM. Most V1 and V2 data points fall
in this quadrant.

(D) Conceptual illustration of Procrustes analysis. Two sets
of 8 colors (Half 1 and Half 2) are shown in a 2D PCA projection
before and after optimal alignment. While direct comparison
shows mismatch, Procrustes alignment reveals nearly identical
geometric structure (stability = 0.83).
```

### Discussion Section

```markdown
### Coordinate System Variability Despite Stable Geometry

Our finding of high Procrustes stability (V1: 0.83, V2: 0.82)
coupled with low RDM correlation challenges the interpretation
that low between-run consistency reflects unstable color
representations. Instead, this dissociation suggests that
individuals maintain highly consistent color representational
geometries, but these geometries are expressed in different
coordinate systems across measurements.

This aligns with recent perspectives emphasizing the importance
of representational geometry over absolute activation patterns
(Kriegeskorte & Wei, 2021). The high Procrustes stability
indicates that the essential structure—which colors are similar,
which are distinct, and how they cluster in neural space—is
preserved, even when voxel-wise patterns appear different.

The observed coordinate system variability likely reflects
multiple factors: (1) slight differences in head position
across sessions, (2) physiological state changes affecting
overall signal magnitude, and (3) natural fluctuations in
the relative engagement of neural populations within V1 and V2.
Critically, these sources of variability affect the coordinate
system but not the underlying representational geometry.

This insight guided our analytical approach: rather than
treating low RDM correlation as a failure of replication, we
employed Shared Response Modeling to align coordinate systems
before group-level analysis.
```

---

## 요약: Key Takeaways

### 1. Procrustes는 무엇을 측정하나?

✅ **Pattern geometry (기하학적 구조)**
- 8 colors의 상대적 위치
- Colors 간 거리 관계
- Cluster 구조
- **회전/크기/이동 후** 얼마나 비슷한가

❌ **Absolute voxel values (절대값)**
- 개별 voxel의 정확한 activation
- 좌표계 자체

### 2. 당신의 결과 (V1, V2)

```
Procrustes: 0.83 ✅
→ 매우 안정적인 색 표상!
→ Pattern geometry 보존!

RDM correlation: -0.04 ❌
→ 하지만 좌표계만 다름
→ 내용은 같음!

결론: SRM 필요!
```

### 3. 왜 중요한가?

**이론적:**
- 색 정보가 distributed pattern에 있음을 확인
- Individual variability의 성격 이해
- Coordinate system vs content 구분

**실용적:**
- SRM 필요성의 근거
- Low RDM correlation을 올바르게 해석
- V1, V2 데이터 품질 확인

### 4. 다음 단계

```
1. ✅ Procrustes 높음 확인 (0.83)
2. → SRM 실행
3. → RDM correlation 향상 기대 (0.5-0.7)
4. → 공통 color geometry 발견!
```

---

## References

**Procrustes Analysis:**
- Gower, J. C. (1975). Generalized procrustes analysis. *Psychometrika*, 40(1), 33-51.
- Ten Berge, J. M. F. (1977). Orthogonal procrustes rotation for two or more matrices. *Psychometrika*, 42(2), 267-276.

**응용 in Neuroscience:**
- Haxby, J. V., et al. (2011). A common, high-dimensional model of the representational space in human ventral temporal cortex. *Neuron*, 72(2), 404-416.
- Guntupalli, J. S., et al. (2016). A model of representational spaces in human cortex. *Cerebral Cortex*, 26(6), 2919-2934.

**Representational Geometry:**
- Kriegeskorte, N., & Wei, X. X. (2021). Neural tuning and representational geometry. *Nature Reviews Neuroscience*, 22(11), 703-718.

**SRM:**
- Chen, P. H., et al. (2015). A reduced-dimension fMRI shared response model. *NIPS*, 28.
- Bannert, M. M., & Bartels, A. (2023). Shared neural codes for visual and semantic color representations. *eLife*, 12, e81344.

---

## Appendix: 코드 예시

### Python Implementation

```python
from scipy.spatial import procrustes
import numpy as np

# Input: two sets of 8 colors × N voxels
half1 = amplitudes[half1_runs].mean(axis=0)  # (8, N)
half2 = amplitudes[half2_runs].mean(axis=0)  # (8, N)

# Procrustes analysis
mtx1, mtx2_aligned, disparity = procrustes(half1, half2)

# Results
stability = 1 - disparity
print(f"Procrustes stability: {stability:.3f}")
print(f"Disparity: {disparity:.3f}")

# Visualization
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA

# Project to 2D for visualization
pca = PCA(n_components=2)
half1_2d = pca.fit_transform(half1)
half2_2d = pca.transform(half2)

# Procrustes on 2D
mtx1_2d, mtx2_2d_aligned, _ = procrustes(half1_2d, half2_2d)

# Plot
plt.figure(figsize=(10, 5))

# Before alignment
plt.subplot(121)
plt.scatter(half1_2d[:, 0], half1_2d[:, 1], label='Half 1')
plt.scatter(half2_2d[:, 0], half2_2d[:, 1], label='Half 2')
plt.legend()
plt.title('Before Alignment')

# After alignment
plt.subplot(122)
plt.scatter(mtx1_2d[:, 0], mtx1_2d[:, 1], label='Half 1')
plt.scatter(mtx2_2d_aligned[:, 0], mtx2_2d_aligned[:, 1], label='Half 2 (aligned)')
for i in range(8):
    plt.plot([mtx1_2d[i, 0], mtx2_2d_aligned[i, 0]],
            [mtx1_2d[i, 1], mtx2_2d_aligned[i, 1]], 'k--', alpha=0.3)
plt.legend()
plt.title(f'After Alignment (stability={stability:.3f})')

plt.tight_layout()
plt.show()
```

---

**작성일:** 2025-12-17
**작성자:** Analysis Team
**데이터:** sub-02, 03, 05, 06, 07 (V1, V2, V3, hV4)
