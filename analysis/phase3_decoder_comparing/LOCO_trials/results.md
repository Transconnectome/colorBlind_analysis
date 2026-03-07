# LOCO Decoder Improvement — Results

## Phase 1: MDS Diagnostic (2026-03-04)

**목적**: LOCO Forward Encoding의 MAE ~70도 문제를 개선하기 위한 사전 진단. 8색의 신경 표상이 **원형 구조**를 형성하는지, 어떤 alignment이 이를 가장 잘 보존하는지 확인한다.

**데이터**: HC 7명의 group-mean RDM (correlation distance), 4 ROI × 3 alignment.

**Figures**: `results/mds_diagnostic/fig5_dashboard.png` ~ `fig10_pass_fail.png`

---

### 1.1 Kruskal Normalized Stress (2D MDS)

**지표 설명**: MDS(Multidimensional Scaling)는 고차원 RDM(Representational Dissimilarity Matrix)을 저차원 공간으로 투영하는 방법이다. **Stress**는 원래 거리와 MDS 투영 거리 사이의 불일치 정도를 측정한다.
- `Stress = sqrt( sum((d_orig - d_mds)^2) / sum(d_orig^2) )`
- **< 0.05**: 매우 좋은 적합 (excellent)
- **< 0.10**: 좋은 적합 (good) — 2D 해석이 신뢰할 만함
- **< 0.20**: 보통 적합 (fair) — 주요 구조는 보이지만 세부 왜곡 있음
- **> 0.20**: 나쁜 적합 (poor) — 2D로 부족, 더 높은 차원 필요

| ROI | Raw | Procrustes | SRM |
|-----|-----|------------|-----|
| V1  | 0.279 | 0.271 | 0.188 |
| V2  | 0.263 | 0.260 | 0.194 |
| V3  | 0.263 | 0.235 | **0.127** |
| hV4 | 0.240 | 0.220 | **0.084** |

**2D Stress < 0.10 통과**: hV4/SRM만 통과 (0.084)

**해석**:
- SRM이 모든 ROI에서 일관되게 가장 낮은 stress를 보임 (Raw, Procrustes 대비 30-60% 감소)
- 이는 SRM이 피험자 간 공유 분산만 추출하여 노이즈를 제거하기 때문
- **V3/SRM (0.127)과 hV4/SRM (0.084)이 가장 양호** — 이들 ROI에서 색상 표상이 저차원 구조를 형성함
- V1, V2는 2D에서 stress > 0.18로, 최소 3D 이상이 필요할 수 있음
- Raw와 Procrustes는 모두 > 0.22로, 고차원 voxel 공간의 노이즈가 MDS 해를 왜곡함

---

### 1.2 Circular Order Preservation (Spearman rank correlation)

**지표 설명**: MDS 2D 좌표에서 `arctan2(y, x)`로 각도를 추출한 후, 이 각도의 순위와 실제 hue 순서(0, 45, ..., 315도)의 순위 간 **Spearman rank correlation**을 계산한다. MDS는 좌우/상하 반전이 가능하므로 CW/CCW 방향 모두 테스트하여 더 높은 상관을 채택한다.
- **|r| > 0.8**: 원형 순서가 강하게 보존됨
- **|r| > 0.5**: 부분적 보존
- **|r| < 0.3**: 순서 보존 실패

| ROI | Raw | Procrustes | SRM |
|-----|-----|------------|-----|
| V1  | **0.786*** (p=.021) | 0.357 (p=.385) | 0.619 (p=.102) |
| V2  | -0.405 (p=.320) | -0.048 (p=.911) | -0.262 (p=.531) |
| V3  | -0.500 (p=.207) | **0.738*** (p=.037) | -0.619 (p=.102) |
| hV4 | 0.405 (p=.320) | 0.524 (p=.183) | 0.452 (p=.260) |

\* p < 0.05

**|rank r| > 0.8 통과**: 없음 (최대 V1/Raw = 0.786)

**해석**:
- **V1/Raw (r=0.786, p=0.021)**가 유일한 유의미 결과이자 최고 상관. 0.8에 근접하지만 미달.
- V3/Procrustes (r=0.738, p=0.037)도 유의미하지만, SRM에서는 -0.619로 방향이 반전됨
- V2는 모든 alignment에서 순서 보존이 거의 없음 (|r| < 0.41)
- hV4는 중간 수준 (r=0.4~0.5)이지만 유의미하지 않음
- **핵심**: 8색의 원형 순서가 신경 표상에서 **불완전하게** 보존됨. 인접 색상끼리는 유사하지만, 전체적인 원형 배열이 깨끗하게 유지되지는 않음

---

### 1.3 Mantel Test (Neural RDM vs Ideal Circular RDM)

**지표 설명**: Mantel test는 두 거리 행렬 간의 상관을 검정하는 비모수 방법이다. 신경 RDM의 상삼각 벡터와 이상적 원형 RDM (각도 차이 기반) 간의 **Spearman correlation**을 계산하고, 행/열 순열 (10,000회)로 p-value를 구한다.
- **r > 0.5, p < 0.05**: 신경 표상이 원형 구조와 유의미하게 일치
- **r > 0.3, p < 0.10**: 약한 경향
- **r ~ 0**: 원형 구조와 무관

이상적 원형 RDM: `d(i,j) = min(|θi - θj|, 360 - |θi - θj|) / 180`

| ROI | Raw | Procrustes | SRM |
|-----|-----|------------|-----|
| V1  | -0.050 (p=.528) | -0.058 (p=.604) | -0.295 (p=.926) |
| V2  | 0.010 (p=.426) | 0.077 (p=.319) | -0.005 (p=.503) |
| V3  | -0.083 (p=.688) | 0.044 (p=.392) | -0.120 (p=.685) |
| hV4 | **0.276** (p=.062) | -0.031 (p=.537) | -0.302 (p=.942) |

**r > 0.5, p < 0.05 통과**: 없음

**해석**:
- **어떤 ROI/alignment에서도 유의미한 원형 구조가 검출되지 않음**
- hV4/Raw (r=0.276, p=0.062)만 marginal trending — 이는 hV4가 색상 선택성이 높은 ROI라는 선행연구와 부합
- SRM에서 음의 상관이 나타나는 것은 주목할 만함: SRM은 피험자 간 공유 분산을 추출하면서, 이 공유 구조가 단순 원형 배열과 다른 배치를 가질 수 있음
- **핵심**: 신경 RDM은 "이상적 원형(equidistant) 배열"과는 **다른** 색상 기하학을 가짐. 이는 LOCO에서 periodic kernel이 반드시 최적이 아닐 수 있음을 시사하나, 이상적 RDM이 equidistant가정(인접 색 모두 같은 거리)을 쓰므로 실제 cone-opponent 구조와 다를 수 있어 해석에 주의 필요

---

### 1.4 Shepard Plot R-squared (MDS Fit Quality)

**지표 설명**: Shepard diagram은 원래 RDM 거리(x축)와 MDS에서 복원된 유클리드 거리(y축) 간의 산점도이다. **R-squared**는 이 관계의 선형 적합도를 측정한다.
- `R2 = 1 - SS_res / SS_tot`
- **> 0.90**: MDS 해가 원래 거리를 매우 잘 복원
- **> 0.80**: 양호
- **< 0**: 매우 나쁨. MDS 해가 원래 거리를 완전히 왜곡 (평균으로 예측하는 것보다 못함)

| ROI | Raw | Procrustes | SRM |
|-----|-----|------------|-----|
| V1  | -11.95 | -6.73 | 0.734 |
| V2  | -6.13 | -5.20 | 0.677 |
| V3  | -4.54 | -2.65 | **0.876** |
| hV4 | -2.61 | -0.93 | **0.935** |

**R2 > 0.80 통과**: V3/SRM (0.876), hV4/SRM (0.935)

**해석**:
- **Raw와 Procrustes의 R2가 모두 대폭 음수** — 이는 고차원 voxel 공간(568 voxels)에서의 correlation distance가 2D MDS로 복원이 불가능함을 의미
- 반면 **SRM 공간(k=3~4)에서는 2D MDS가 원래 거리를 잘 복원** (R2 = 0.68~0.94)
- 이는 SRM이 이미 차원 축소를 수행하여 주요 구조만 남겼기 때문
- hV4/SRM (R2=0.935)이 최고: hV4의 색상 표상이 3차원 SRM 공간에서 거의 2D 평면 위에 놓임
- **핵심**: SRM alignment가 MDS 분석의 전제조건. Raw/Procrustes 데이터에 대한 2D MDS는 신뢰할 수 없음

---

### 1.5 Cross-Alignment Procrustes Disparity

**지표 설명**: 서로 다른 alignment 방법에서 얻은 2D MDS 해를 Procrustes 변환(회전, 스케일링, 반사)으로 최대한 정렬한 후 남은 불일치(disparity)를 측정한다. 낮을수록 두 alignment이 비슷한 MDS 구조를 생성함을 의미한다.
- **< 0.2**: 매우 유사한 MDS 구조
- **0.2~0.5**: 보통
- **> 1.0**: 상당히 다른 구조

| Comparison | V1 | V2 | V3 | hV4 |
|------------|----|----|----|----|
| Raw vs Procrustes | 1.672 | 0.682 | 1.100 | 1.008 |
| Raw vs SRM | 1.071 | 0.910 | 0.763 | 0.880 |
| **Procrustes vs SRM** | **0.504** | 1.040 | **0.175** | **0.178** |

**해석**:
- **V3와 hV4에서 Procrustes와 SRM이 매우 유사한 MDS 구조** (disparity 0.175, 0.178)
- 이는 이 ROI들에서 Procrustes alignment이 SRM과 비슷한 표상 구조를 포착함을 시사
- V1과 V2에서는 alignment 간 차이가 큼 — 피험자 간 voxel 대응의 불확실성이 높음
- **핵심**: V3/hV4에서는 alignment 선택에 덜 민감하지만, V1/V2에서는 SRM이 필수

---

### Phase 1 Decision Matrix

| Criterion | Threshold | Best Result | Pass? |
|-----------|-----------|-------------|-------|
| 2D Stress | < 0.10 | hV4/SRM = 0.084 | PASS (hV4/SRM만) |
| Circular Order | \|r\| > 0.80 | V1/Raw = 0.786 | FAIL (근접) |
| Shepard R2 | > 0.80 | hV4/SRM = 0.935 | PASS (V3/SRM, hV4/SRM) |
| Mantel r | > 0.5, p<0.05 | hV4/Raw = 0.276 | FAIL (전체) |

**전체 통과: 12개 ROI×Alignment 조합 중 hV4/SRM만 2/4 통과, V3/SRM이 1/4 통과. 나머지는 0/4.**

### Phase 1 Conclusion

**진단 결과: 원형 구조는 "약하고 불완전"하다.**

1. **SRM이 필수**: Raw/Procrustes에서는 MDS 자체가 신뢰할 수 없음 (Shepard R2 < 0). 이후 모든 분석은 SRM alignment 기반으로 진행해야 함.

2. **hV4가 최적 ROI**: 유일하게 2D stress < 0.1, Shepard R2 > 0.93을 달성. 색상 표상이 가장 저차원에서 안정적으로 존재.

3. **이상적 원형 배열은 기각**: Mantel test에서 모든 ROI가 실패 → 신경 RDM은 equidistant circular 배열과 유의미하게 유사하지 않음. 이는 실제 색상 표상이 cone-opponent 축에 의해 비등간격으로 배치될 수 있음을 시사.

4. **부분적 순서 보존**: V1/Raw에서 r=0.786 (p=0.021)으로 원형 순서가 부분적으로 보존되지만, threshold 미달.

**Phase 2/3 진행 판단**:
- **진행함** — 이유:
  - (a) Ridge regularization은 원형 구조 여부와 무관하게 df 문제를 완화하므로 반드시 테스트
  - (b) GP의 periodic kernel은 실패할 수 있으나, Matern/RBF kernel 등 비원형 대안도 함께 테스트
  - (c) hV4/SRM에서는 2D 구조가 양호하므로, 최소 hV4에서는 GP가 작동할 가능성 있음
  - (d) Mantel test의 이상적 RDM이 equidistant 가정이라, 실제 cone-opponent 기반 비등간격 RDM과 비교하면 결과가 다를 수 있음

**Decision Tree 경로**: `Phase 1 MDS → 원형 구조? → 부분적 YES (hV4 only)` → **Phase 2 Ridge + Phase 3 GP (periodic + non-periodic 양쪽 테스트)**

---

## Phase 1b: Extended V1/V2 Diagnostic (2026-03-04)

**목적**: Phase 1에서 V1/V2 SRM이 4가지 기준 모두 실패했으나, V1/V2는 연구의 핵심 타겟 ROI이므로 **실패가 진정한 구조 부재인지 vs 부적절한 참조 모델(equidistant RDM) 때문인지** 심층 진단한다.

**핵심 가설**: Phase 1의 Mantel test는 equidistant circular RDM(8색 균등 간격)을 사용했으나, V1/V2는 생물학적으로 cone-opponent 축(L-M, S-LM)으로 색상을 인코딩한다. 실험 자극의 CIELab (a\*, b\*) 좌표가 실제로 비균등(인접 색 간 거리 범위 30.9~68.3, 최대/최소 = 2.2배)이므로, CIELab 기반 참조 RDM이 더 적합할 수 있다.

**데이터**: HC 7명의 group-mean RDM, SRM alignment, 4 ROI. Per-subject 분석은 HC 7명 + CVD 3명.

**스크립트**: `scripts/mds_extended_v1v2.py`
**Figures**: `results/mds_diagnostic/fig_ext1_*.png` ~ `fig_ext6_*.png`

---

### 1b.1 Analysis 1: Full Stress Curve (1-7D)

**지표 설명**: Phase 1에서는 2D stress만 보고했으나, SRM k=3~4이므로 고차원 임베딩에서 stress가 크게 감소할 수 있다. 1~7D까지의 전체 stress curve를 통해 "데이터가 실제로 몇 차원인가"를 확인한다.

| ROI | 1D | 2D | **3D** | **4D** | 5D | 6D | 7D | SRM k |
|-----|----|----|--------|--------|----|----|----|-------|
| V1 | 0.463 | 0.188 | 0.126 | **0.127** | 0.127 | 0.127 | 0.128 | k=4 |
| V2 | 0.463 | 0.194 | **0.097** | 0.098 | 0.099 | 0.099 | 0.099 | k=4 |
| V3 | 0.464 | 0.127 | **0.093** | 0.092 | 0.093 | 0.093 | 0.093 | k=3 |
| hV4 | 0.464 | 0.084 | **0.063** | 0.063 | 0.063 | 0.064 | 0.065 | k=3 |

**Stress < 0.10 도달 차원**: V2 3D (0.097), V3 2D (0.127→3D 0.093), hV4 2D (0.084). **V1은 7D에서도 0.128로 미달.**

**해석**:
- **V2**: 3D에서 stress=0.097로 0.10 임계값을 통과. 2D→3D 전이에서 급격한 감소 (0.194→0.097, 50% 감소). 3D 이후 plateau → **V2의 색상 구조는 3차원**
- **V1**: 3D에서 0.126까지 감소하나 0.10 미달, 그 이후 plateau (3D~7D 모두 ~0.127). **V1의 SRM k=4 공간에서는 체계적 색상 구조보다 노이즈가 지배적**
- hV4는 2D에서 이미 0.084로 최우수, V3도 3D에서 0.093
- **모든 ROI에서 3D 이후 stress가 plateau** → SRM이 이미 k차원으로 차원축소했으므로, k+1 이상의 MDS 차원은 정보 없음

> V1의 stress floor (~0.127)는 V2 (0.097), V3 (0.093), hV4 (0.063)보다 현저히 높음. V1 SRM 공간에 잔류 노이즈가 가장 많음을 시사.

---

### 1b.2 Analysis 2: CIELab-based Mantel Test (핵심 분석)

**지표 설명**: Phase 1에서 사용한 equidistant circular RDM(모든 인접 색 동일 거리) 대신, 실제 자극의 CIELab 좌표에서 유도한 참조 RDM 3종을 추가하여 총 4개 모델을 비교한다.

**4개 참조 모델**:
- **Equidistant**: `d(i,j) = min(|θi-θj|, 360-|θi-θj|)/180` (Phase 1과 동일)
- **CIELab(a\*,b\*)**: 실측 CIELab a\*, b\* 좌표 간 Euclidean 거리
- **a\*-only (L-M axis)**: cone-opponent L-M축만 사용 (a\* 좌표 1차원)
- **b\*-only (S-LM axis)**: cone-opponent S-(L+M)축만 사용 (b\* 좌표 1차원)

통계: 10,000회 순열, Bonferroni 보정 (4모델 × 4ROI = 16검정, α=0.003125)

| ROI | Equidistant | CIELab(a\*,b\*) | a\*-only (L-M) | b\*-only (S-LM) |
|-----|-------------|-----------------|----------------|-----------------|
| **V1** | r=-0.295 (p=.926) | r=-0.195 (p=.837) | r=-0.292 (p=.958) | r=-0.083 (p=.613) |
| **V2** | r=-0.005 (p=.503) | r=0.124 (p=.261) | **r=0.282 (p=.085)** | r=-0.130 (p=.721) |
| V3 | r=-0.120 (p=.685) | r=-0.014 (p=.489) | r=-0.165 (p=.785) | r=0.124 (p=.225) |
| hV4 | r=-0.302 (p=.942) | r=-0.308 (p=.966) | r=-0.249 (p=.936) | r=-0.085 (p=.572) |

\* Bonferroni 보정 후 유의한 결과 없음

**해석**:
- **V2에서 a\*-only (L-M축) 모델이 가장 높은 상관** (r=0.282, raw p=0.085). Bonferroni 보정 후 유의하지 않으나, L-M cone-opponent 축이 V2 신경 표상 구조와 가장 잘 일치하는 경향
- **CIELab(a\*,b\*)가 equidistant보다 일관되게 개선**: V1 +0.101, V2 +0.128, V3 +0.106, hV4 -0.006. Phase 1의 equidistant RDM이 최적 참조 모델이 아니었음을 확인
- 그러나 **절대적 상관이 매우 약함** (모든 r < 0.3, 대부분 음수). CIELab 모델로도 신경 RDM의 기하학을 충분히 설명하지 못함
- V1은 모든 모델에서 음의 상관 → V1 SRM 표상이 어떤 참조 모델과도 체계적 관련이 없음
- hV4도 모든 모델에서 음의 상관 → Phase 1에서 2D stress가 좋았던 것과 대조적. 저차원 구조는 존재하나 색상 순서와 무관한 다른 차원(예: luminance)을 반영할 가능성

> **Q1 결론 (CIELab > equidistant?)**: 방향성은 있으나 유의하지 않음. **FAIL**. 다만 V2의 L-M축 경향(p=0.085)은 Phase 3 GP에서 cone-opponent informed kernel의 근거가 됨.

---

### 1b.3 Analysis 3: Persistent Homology (H1 Cycle Detection)

**지표 설명**: ripser 라이브러리로 Vietoris-Rips persistent homology를 계산하여, 신경 RDM에서 H1 (1차원 cycle = 고리) 위상 특징이 존재하는지 탐지한다. Max H1 lifetime이 귀무분포보다 유의미하게 긴지를 검정한다.

**귀무 모델 수정 이력**: 초판에서는 행/열 순열(permutation)을 사용했으나, 대칭 거리행렬의 행/열을 동일 순열로 치환하면 레이블만 바뀌고 거리 집합은 동일하게 유지되어 TDA가 불변(null_std=0, 모든 p=1.0). **수정된 귀무 모델**: R^k 단위 초구면(S^{k-1}) 위에 8개 랜덤 단위벡터를 생성하고, correlation distance RDM → ripser를 1,000회 반복. 이는 SRM 차원(k)과 거리 척도(correlation)를 일치시킨 "구조 없는" 점구름에 해당.

| ROI | H1 존재 | Max Lifetime | H1 개수 | p-value | null mean | null std | SRM k |
|-----|---------|-------------|---------|---------|-----------|----------|-------|
| **V1** | Yes | **0.448** | 2 | **0.150** | — | — | 4 |
| V2 | Yes | 0.156 | 1 | 0.553 | — | — | 4 |
| V3 | Yes | 0.035 | 2 | 0.629 | — | — | 3 |
| hV4 | Yes | 0.279 | 1 | 0.450 | — | — | 3 |

**해석**:

- **V1이 가장 persistent한 H1 cycle** (lifetime=0.448, p=0.150). 유의미하지 않으나 (p>0.05), 4개 ROI 중 가장 낮은 p-value. R^4에서 랜덤 8점보다 더 긴 고리를 형성하는 경향
- V2 (p=0.553), V3 (p=0.629), hV4 (p=0.450)는 모두 유의미하지 않음. 이들의 H1 lifetime이 랜덤 점구름 수준
- **V1의 역설적 결과**: 다른 모든 분석(stress, Mantel, Isomap)에서 구조 부재로 판정된 V1이 topology에서는 가장 낮은 p-value를 보임. 이는 V1의 8색 표상이 "원형 순서"는 아니지만 "고리 모양의 위상"은 부분적으로 가질 수 있음을 시사 — 순서가 뒤섞인 고리
- **모든 ROI에서 p>0.05**: H1 위상 구조에 대한 유의미한 증거 없음

> **Q2 결론 (H1 topology?)**: **FAIL** (모든 ROI p>0.05). 수정된 귀무 모델에서도 유의미한 원형 위상 부재. V1의 trending (p=0.150)은 참고 수준.

---

### 1b.4 Analysis 4: Higher-D MDS + PCA 2D Projection

**지표 설명**: 2D MDS가 너무 제약적일 수 있으므로, 3D/4D MDS를 수행한 후 PCA로 최적 2D 평면에 투영하여 circular order를 재검정한다. 고차원 MDS의 stress와 PCA 투영 후의 circular rho를 함께 보고한다.

| ROI | 2D stress | 2D rho | 3D stress | 3D rho | 3D rho p | 4D stress | 4D rho | 4D rho p |
|-----|-----------|--------|-----------|--------|----------|-----------|--------|----------|
| **V1** | 0.188 | 0.619 | 0.126 | 0.643 | .086 | 0.127 | 0.643 | .086 |
| **V2** | 0.194 | -0.262 | **0.097** | 0.357 | .385 | 0.098 | -0.024 | .955 |
| V3 | 0.127 | -0.619 | **0.093** | **-0.762** | **.028** | 0.092 | -0.238 | .570 |
| hV4 | 0.084 | 0.452 | **0.063** | -0.071 | .867 | 0.063 | 0.119 | .779 |

**Q3 통과 기준**: stress < 0.10 OR |rho| > 0.7

**해석**:
- **V2 3D**: stress=0.097 < 0.10 통과. 그러나 PCA 2D 투영 후 circular rho=0.357 (약함). **구조는 3D에 존재하나, 원형 배열은 아님**
- **V3 3D**: stress=0.093 < 0.10이면서 **rho=-0.762 (p=0.028)** — 4개 ROI 중 유일한 유의미한 circular order! PCA 분산 설명: 55.2% + 35.9% = 91.1%
  - 그러나 4D PCA에서는 rho=-0.238으로 급감 → **3D→PCA 2D가 최적 projection**, 4D는 노이즈 차원 추가
- **V1 3D/4D**: stress는 0.126~0.127로 개선되지만, rho는 0.643 (p=0.086)으로 거의 유의미하지 않음. 직접 2D (0.619)와 큰 차이 없음
- **hV4 3D**: stress=0.063으로 매우 좋지만 rho=-0.071. 저차원 구조는 원형이 아님

> **Q3 결론 (Higher-D 개선?)**: V2 **PASS** (3D stress < 0.10). V3도 PASS (rho=0.762). V1 **FAIL**. hV4 PASS (stress < 0.10).

---

### 1b.5 Analysis 5: Isomap vs MDS

**지표 설명**: MDS는 유클리드 거리만 보존하는 선형 임베딩이다. Isomap은 측지 거리(geodesic distance)를 사용하는 비선형 임베딩으로, 데이터가 곡면 manifold 위에 있을 때 더 좋은 결과를 산출한다. Isomap이 MDS보다 circular rho가 높으면, 비선형 manifold가 존재한다는 증거이며 GP에서 Matern kernel이 적합함을 시사한다.

| ROI | MDS rho | Isomap rho | Isomap n_neighbors | Isomap 우세? |
|-----|---------|------------|-------------------|-------------|
| **V1** | 0.619 | -0.476 | 3 | No |
| **V2** | -0.262 | **0.524** | 3 | **Yes** |
| V3 | -0.619 | -0.119 | 3 | No |
| hV4 | 0.452 | 0.048 | 3 | No |

**해석**:
- **V2에서만 Isomap이 MDS보다 우세** (rho: 0.524 vs -0.262). V2의 색상 표상이 **비선형 manifold** 위에 놓여 있음을 시사. 특히 MDS에서는 음의 상관(-0.262)이었으나 Isomap에서는 양의 상관(0.524)으로 반전 → 비선형 왜곡을 교정하면 원형 순서가 드러남
- V1, V3, hV4에서는 MDS가 Isomap보다 나음. 이 ROI들의 구조는 유클리드 공간에서 더 잘 표현됨
- V2의 Isomap 결과는 Q3 (3D stress < 0.10)과 함께, V2 표상이 "비선형 3D 구조"임을 지지

> **Q4 결론 (Isomap better?)**: V2 **PASS**. 나머지 **FAIL**.

---

### 1b.6 Analysis 6: Per-Subject V1/V2 Analysis

**지표 설명**: Group mean이 아닌 개인별 RDM에서 circularity, ISC, CIELab Mantel r을 계산하고, CIELab advantage (r_cielab - r_equidistant)로 CIELab 모델의 개인별 우위를 평가한다.

#### V1 Per-Subject

| Subject | Group | Circularity | ISC | CIELab r | Equi r | CIELab adv |
|---------|-------|-------------|-----|----------|--------|------------|
| sub-01 | HC | 1.92 | 0.731 | -0.153 | -0.216 | +0.063 |
| sub-02 | HC | 2.09 | **0.857** | -0.230 | -0.292 | +0.062 |
| sub-03 | HC | 1.90 | 0.466 | 0.020 | -0.078 | +0.099 |
| sub-04 | HC | 2.03 | 0.652 | -0.107 | -0.212 | **+0.105** |
| sub-05 | HC | 1.95 | 0.780 | -0.100 | -0.182 | +0.082 |
| sub-06 | HC | 1.91 | 0.421 | -0.264 | -0.266 | +0.001 |
| sub-07 | HC | 2.00 | 0.733 | -0.142 | -0.257 | **+0.115** |
| sub-08 | CVD | 1.85 | 0.667 | -0.125 | -0.137 | +0.012 |
| sub-09 | CVD | 1.93 | **0.252** | -0.379 | -0.266 | **-0.113** |
| sub-10 | CVD | 2.19 | 0.693 | -0.366 | -0.381 | +0.014 |

#### V2 Per-Subject

| Subject | Group | Circularity | ISC | CIELab r | Equi r | CIELab adv |
|---------|-------|-------------|-----|----------|--------|------------|
| sub-01 | HC | 1.81 | 0.677 | -0.027 | -0.094 | +0.067 |
| sub-02 | HC | 2.10 | 0.732 | 0.011 | -0.076 | +0.088 |
| sub-03 | HC | 1.67 | 0.271 | -0.036 | -0.167 | **+0.131** |
| sub-04 | HC | 1.86 | 0.460 | **0.261** | 0.026 | **+0.234** |
| sub-05 | HC | **1.28** | 0.427 | **0.485** | **0.461** | +0.024 |
| sub-06 | HC | 2.12 | 0.334 | -0.238 | -0.159 | -0.079 |
| sub-07 | HC | 1.61 | 0.600 | 0.148 | -0.047 | **+0.194** |
| sub-08 | CVD | 1.96 | 0.567 | 0.071 | -0.116 | **+0.187** |
| sub-09 | CVD | 1.97 | 0.366 | -0.072 | -0.161 | +0.089 |
| sub-10 | CVD | 2.23 | 0.521 | -0.197 | -0.242 | +0.045 |

**해석**:

1. **CIELab advantage가 일관되게 양수**: V1에서 10명 중 9명 양수 (median +0.063), V2에서 10명 중 9명 양수 (median +0.088). CIELab 모델이 equidistant보다 개인 수준에서도 일관되게 더 적합한 참조 모델임을 확인
   - 유일한 예외: sub-09 V1 (advantage = -0.113). sub-09는 V1 ISC도 최저 (0.252) → 이 피험자의 V1 SRM 표상이 전반적으로 비전형적

2. **V2에서 개인차가 매우 큼**: CIELab r이 -0.238 (sub-06) ~ 0.485 (sub-05). **sub-05가 눈에 띄게 높은 V2 색상 구조**를 보유 (circularity도 1.28로 원에 가장 가까움). sub-04도 r=0.261로 양수

3. **ISC 범위**: V1 0.25~0.86, V2 0.27~0.73. ISC가 높을수록 group mean에 잘 맞으므로, 낮은 ISC 피험자(sub-03, sub-06)는 group-level 분석에서 신호를 희석시킬 수 있음

4. **HC vs CVD 패턴**:
   - V1: CVD sub-09의 ISC 최저 (0.252), CIELab advantage 유일한 음수. 나머지 CVD (sub-08, sub-10)는 HC 범위 내
   - V2: CVD 3명 모두 HC 범위 내. sub-08의 CIELab advantage (+0.187)는 HC 평균보다 높음

---

### Phase 1b Decision Matrix

| 질문 | 지표 | 통과 기준 | V1 | V2 | V3 | hV4 |
|------|------|----------|----|----|----|----|
| Q1: CIELab > equidistant? | Mantel r 차이 + p<0.05 (Bonf) | r_cielab > r_equi AND p<0.05 | FAIL | FAIL | FAIL | FAIL |
| Q2: H1 topology? | Persistence p | p < 0.05 | FAIL (p=.150) | FAIL (p=.553) | FAIL (p=.629) | FAIL (p=.450) |
| Q3: Higher-D 개선? | 3D/4D stress<0.10 OR \|rho\|>0.7 | 하나라도 | FAIL | **PASS** | **PASS** | **PASS** |
| Q4: Isomap 우세? | \|rho_iso\| > \|rho_mds\| | 차이 존재 | FAIL | **PASS** | FAIL | FAIL |
| **Total** | | 2+/4 = structured | **0/4** | **2/4** | **1/4** | **1/4** |

Q2: 랜덤 단위벡터 귀무 모델 사용 (S^{k-1} 위 균일분포, 1000회). V1이 가장 낮은 p=0.150이지만 유의미하지 않음.

### Verdict

| ROI | 판정 | 의미 |
|-----|------|------|
| **V1** | **UNSTRUCTURED** (0/4) | 진정한 구조 부재. k=4 SRM 공간에서 체계적 색상 기하학 없음 |
| **V2** | **STRUCTURED** (2/4) | 구조 존재. 3D 비선형 manifold 형태. CIELab-informed GP 가능 |
| V3 | MARGINAL (1/4) | 3D에서 유의미한 circular order (rho=0.762, p=0.028). 약한 증거 |
| hV4 | MARGINAL (1/4) | 저차원 구조 존재하나 원형이 아님. 다른 차원(luminance?) 반영 |

---

### Phase 1b Conclusion

**Phase 1의 V1/V2 실패는 부분적으로 참조 모델 문제였으나, V1은 진정한 구조 부재이고 V2에는 비선형 구조가 존재한다.**

#### 핵심 발견

1. **CIELab 참조 모델이 equidistant보다 일관되게 우수**: 개인 수준에서 V1 9/10명, V2 9/10명이 CIELab advantage 양수. 그러나 절대적 상관이 약하여 Mantel test 유의성 미달. → **equidistant RDM은 부적절한 참조 모델이지만, CIELab도 충분하지 않음**. 신경 표상은 단순한 물리적 색차보다 복잡한 기하학을 가짐.

2. **V2는 비선형 3차원 구조**: 3D stress < 0.10 (Q3)과 Isomap 우세 (Q4)가 수렴적으로 "V2에 비선형 manifold가 존재"함을 지지. 특히 V2의 L-M (a\*) 축 상관이 가장 높음 (r=0.282, p=0.085). → **V2에서 cone-opponent informed GP (Matern kernel)가 정당화됨**

3. **V1은 진정한 구조 부재**: 7D까지 stress floor ~0.127, 모든 참조 모델과 음의 상관, Isomap도 개선 없음. → **V1에서는 GP보다 cross-ROI prior (V2/V4→V1) 또는 비주기 kernel이 필요**

4. **V3에서 숨겨진 구조 발견**: 3D MDS→PCA 2D에서 rho=-0.762 (p=0.028)로 유의미한 circular order 검출. 직접 2D에서는 보이지 않았던 구조가 3D 공간에 존재. → V3도 GP 적용 대상으로 격상 가능

5. **Persistent homology 귀무 모델 수정 완료**: 원래 행/열 순열은 TDA 레이블 불변성으로 인해 무효(null_std=0)였음. **랜덤 단위벡터 귀무 모델**로 수정: R^k 초구면 위에 8개 랜덤 점을 생성하여 correlation distance RDM → ripser를 1,000회 반복. 수정 결과: 모든 ROI p>0.05로 유의미한 원형 위상 부재 확인. 단, V1이 가장 낮은 p=0.150 (역설적으로 다른 지표에서는 가장 구조가 없는 ROI).

---

### V2 구조 심층 해석: L-M 우세 3D 비선형 색채 다양체

#### 수렴적 증거 (Converging Evidence)

| 증거 | 수치 | 시사점 |
|------|------|--------|
| 3D stress < 0.10 (Q3) | 0.097 | 구조가 **3차원**에 존재 (2D에서는 0.194) |
| Isomap > MDS (Q4) | rho 0.524 vs -0.262 | 다양체에 **곡률**이 있음 (비선형) |
| a\*-only Mantel 최고 (Q1) | r=0.282, p=0.085 | **L-M cone-opponent 축**이 주 조직 차원 |
| b\*-only 음의 상관 | r=-0.130 | S-(L+M) 축은 V2 구조와 **무관하거나 반대** |
| CIELab(a\*,b\*) < a\*-only | r=0.124 < 0.282 | b\* 축을 추가하면 오히려 **적합도 하락** |

#### 구조 특성화

V2는 **L-M cone-opponent 축이 지배하는 3차원 비선형 다양체(warped manifold)**로 색상을 인코딩한다:

- **1차 축 (L-M)**: red-green 대비. V2 thin stripe의 double-opponent 세포가 주로 L-M 대비에 민감 (Derrington, Krauskopf & Lennie, 1984)
- **2-3차 축**: luminance 또는 L-M과 S-LM의 비선형 상호작용. 단순 CIELab b\*와 불일치
- **비선형성**: Isomap(측지 거리)이 MDS(유클리드 거리)보다 원형 순서를 잘 복원 → 색상이 **곡면 위에 배열**

> 이는 "등간격 원"이 아니라, **L-M 축을 따라 늘어난 비등방적(anisotropic) 3D 다양체**에 해당. Phase 1의 equidistant 원형 가정이 실패한 직접적 원인.

#### GP 커널 전략

| 접근 | 커널 | 근거 |
|------|------|------|
| ~~Periodic (hue angle)~~ | ~~ExpSinSquared~~ | ~~등간격 원형 가정 → 기각됨~~ |
| **Anisotropic Matern (a\*, b\*)** | Matern(nu=2.5) with ARD | L-M 축에 짧은 lengthscale, S-LM 축에 긴 lengthscale |
| **Isomap features → GP** | RBF on Isomap 좌표 | 비선형 manifold 좌표를 입력으로 직접 사용 |

---

### V1 처리 전략: 음성 대조군 + Cross-ROI Prior

#### V1 구조 부재의 원인

V1의 0/4 실패는 방법론적 한계가 아닌 **생물학적 특성**을 반영한다:

- **Stress floor (~0.127)**: 7D까지도 plateau → SRM k=4 공유 차원에서 색상이 차지하는 분산이 미미
- **모든 Mantel r 음수**: 어떤 물리적 색 모델과도 체계적 관련 없음
- **Isomap도 실패**: 비선형 manifold도 부재

V1은 방향(orientation), 공간주파수(spatial frequency), 위상(phase) 등이 피험자 간 공유 분산의 대부분을 차지한다. SRM이 추출한 k=4 공유 차원에서 색상 신호가 **다른 feature들에 묻혀 있음(submerged)**. 개별 voxel은 cone contrast에 반응하지만, population 수준에서 일관된 색 공간을 형성하지 않는 **"sub-representational"** 상태이다.

#### 3단 처리 전략

| 전략 | 내용 | 과학적 의미 |
|------|------|-----------|
| **(1) 음성 대조군 유지** | V1을 분석에 포함하되 "구조 없음"을 보고 | 방법의 특이성(specificity) 검증 |
| **(2) Cross-ROI prior** | V2의 색채 기하학을 V1의 structural prior로 사용 | 계층적 색 처리 모델(V1→V2 feedforward) 검증 |
| **(3) 비주기 kernel** | RBF/Matern kernel (periodic 대신) | 원형 구조 없이 국소적 유사성만 포착 |

**핵심 논증**: V1의 "실패"는 논문에서 **가장 강력한 증거 중 하나**가 된다. GP 디코더가 V2/V3/hV4에서 baseline 대비 개선을 보이면서 V1에서는 개선이 없다면, 이는 GP가 noise를 fitting하는 것이 아니라 **실제 색상 기하학적 구조를 활용**하고 있음을 입증하는 **double dissociation**의 한 축이 된다:

- V2: 구조 있음 → GP 개선 있음 (positive)
- V1: 구조 없음 → GP 개선 없음 (negative control)

---

#### Phase 2/3 진행 전략 수정

| ROI | Phase 1 판정 | Phase 1b 판정 | GP 전략 |
|-----|------------|-------------|---------|
| V1 | 0/4 FAIL | 0/4 UNSTRUCTURED | **음성 대조군**. Cross-ROI prior 및 비주기 kernel (RBF/Matern) 테스트 |
| V2 | 0/4 FAIL → | **2/4 STRUCTURED** | **Anisotropic Matern kernel, L-M (a\*) 축 우선, Isomap 좌표 활용** |
| V3 | 1/4 partial | 1/4 MARGINAL (3D rho 유의미) | Periodic + Matern 양쪽 테스트 |
| hV4 | 2/4 partial | 1/4 MARGINAL | Periodic kernel (Phase 1에서 2D 구조 양호) |

---

## Strategic Direction Revision (2026-03-04)

### SRM 공간 한계 — Pre-validation 결과 종합

Phase 1b 결과와 `future_phase3_filter_optimization/pre_validation/notion.md`의 사전 검증을 종합하면, **SRM 공간은 연속 색 구조에 부적합**하다:

| 문제 | 증거 |
|------|------|
| V1 stress plateau | 7D까지 0.127 정체 (raw/procrustes는 dim 4-5에서 < 0.10 도달) |
| hV4 CIELab 부호 반전 | raw r=+0.402* → SRM r=-0.308. SRM 투영이 색 기하학 파괴 |
| CVD 범주 표상 이미 동등 | Cross-decoding 10/12 유의, LORO HC≈CVD (p=0.668) → SRM 필터 ≈ 항등변환 |
| 연속 보간에서 결손 | LOCO HC 69.4° vs CVD 87.4° (hV4, p=0.017) — Procrustes 공간에서 교정 가능 |
| SRM W matrix 빈약 | (k×8) = 24~32 params vs Procrustes (n_voxels×8) = 3,408+ params |

### 수정된 Phase 구조

```
Phase 2: Ridge (SRM LOCO)         ← 진행 (df 안정화 baseline, 빠름)
Phase 3: GP Matern (V2 SRM only)  ← 축소 (SRM ceiling 확인용 benchmark)
Phase 4: Procrustes Filter        ← ★ 주력 (notion.md 전략)
```

### Filter Architecture: SRM + Procrustes 상보적 역할

**피험자마다 voxel 수가 다르므로 cross-subject 비교에 SRM이 필수** (sub-01 V1: ~500 voxels vs sub-07 hV4: 16 voxels). Procrustes 공간에서 직접 W_HC mean을 구하거나 cross-subject 비교가 불가능하다.

```
[SRM: 필수 인프라 — 타겟 정의 + 그룹 비교]
  HC Procrustes amplitudes → SRM (W_i^T × X) → k-dim 공유 공간
  HC mean pattern (k-dim) = 타겟
  CVD 편차 식별 (z-score, FDR pairs)

[Procrustes: 개인 해상도 — 필터 적용]
  SRM HC 타겟 → W_i × S_HC → 개인 voxel 공간 타겟 (역투영)
  개인 voxel 공간에서 FE W_CVD → W_HC-like 변환 학습
  ※ n_voxels × 8 파라미터 → 풍부한 개인차 포착

[양방향 브릿지: SRM projection W_i]
  voxel → SRM:  S = W_i^T × X_proc    (그룹 비교용)
  SRM → voxel:  X̂_proc = W_i × S      (타겟 역투영용)
```

**핵심**: SRM은 "검증 전용"이 아니라 **타겟 정의와 그룹 비교의 필수 인프라**. Procrustes는 SRM을 대체하는 것이 아니라, SRM projection W_i를 브릿지로 하여 **개인 voxel 수준 해상도**를 제공한다.

| 역할 | SRM | Procrustes |
|------|-----|-----------|
| 그룹 비교 | **필수** (voxel 수 통일) | 불가 (차원 불일치) |
| HC mean 타겟 | **필수** (k-dim mean) | 불가 |
| 필터 파라미터 | 제한적 (k×8 = 24-32) | **풍부** (n_voxels×8 = 3,408+) |
| 연속 색 거리 | 부분 보존 (V2만 structured) | 보존 |
| 개인 필터 적용 | 가능하나 해상도 부족 | **최적** |

### Periodic Kernel 기각 근거

| 근거 | 수치 |
|------|------|
| Mantel test (equidistant) 전 ROI 실패 | 최고 r=hV4/Raw 0.276 (p=0.062), 유의 없음 |
| CIELab 비균등성 | 인접 거리 30.9~68.3 (2.2배), equidistant 가정 기각 |
| H1 persistent homology 전 ROI 실패 | 최저 p=V1 0.150, 원형 위상 부재 |
| Per-subject circular order | \|rho\| > 0.8 달성 피험자 없음 |

**결론**: ExpSinSquared(periodic) kernel은 전제 조건(등간격 원형 배열)을 충족하지 않음. V2에서 Anisotropic Matern만 benchmark으로 테스트.

---

## Phase 2: Ridge Regularization

*(서버 실행 대기 중 — df 안정화 baseline)*

**목적**: Ridge가 SRM LOCO의 df=1 문제를 얼마나 완화하는지 확인. 주력 방법이 아닌 **baseline delta 기록용**.

### 2.1 Fixed Alpha Grid (MAE in degrees)
| Subject | ROI | OLS | a=0.001 | a=0.01 | a=0.1 | a=1 | a=10 | a=100 | a=1000 |
|---------|-----|-----|---------|--------|-------|-----|------|-------|--------|
|         |     |     |         |        |       |     |      |       |        |

### 2.2 Nested CV (best alpha per fold)
| Subject | ROI | OLS MAE | Ridge MAE | Best alpha | Delta |
|---------|-----|---------|-----------|------------|-------|
|         |     |         |           |            |       |

### Phase 2 Decision
- Ridge improvement > 5deg: [ ]
- Rationale:

---

## Phase 3: GP Matern — V2 Benchmark Only

*(서버 실행 대기 중 — SRM ceiling 확인용)*

**목적**: V2 SRM 공간에서 Anisotropic Matern GP의 LOCO 개선 상한 확인. Periodic kernel은 기각됨.

**범위**: V2 only (유일한 STRUCTURED ROI, 2/4). V1은 음성 대조군으로 포함 가능.

### 3.1 GP Matern (V2, Anisotropic ARD)
| Subject | ROI | FE_OLS | GP_Matern | Delta | Note |
|---------|-----|--------|-----------|-------|------|
|         | V2  |        |           |       | L-M lengthscale < S-LM |
|         | V1  |        |           |       | Negative control |

### 3.2 GP + FE Mean Function (V2)
| Subject | ROI | GP_Matern | GP+FE_mean | Delta |
|---------|-----|-----------|------------|-------|
|         | V2  |           |            |       |

### Phase 3 Decision
- GP Matern V2 improvement vs Ridge: [ ]
- SRM-space ceiling established: [ ]
- Rationale:

---

## Phase 4: Procrustes Filter (★ Main Path)

**이 phase의 상세 결과는 `analysis/future_phase3_filter_optimization/`에 기록됨.**

Procrustes 공간에서 FE W matrix 변환으로 CVD 색 표상 교정. SRM은 검증 전용.

### 4.1 Filter Design
- **SRM 역할**: HC mean 타겟 정의 + 그룹 비교 (필수 인프라, voxel 수 차이 해결)
- **Procrustes 역할**: 개인 voxel 수준 필터 적용 (n_voxels × 8 파라미터)
- **브릿지**: SRM projection W_i — SRM 타겟을 개인 voxel 공간으로 역투영
- **Target subjects**: sub-08 (FDR 32 pairs), sub-09 (FDR 7 pairs)

### 4.2 Comparison: SRM vs Procrustes Filter
| Metric | SRM (Phase 2-3) | Procrustes (Phase 4) |
|--------|-----------------|---------------------|
| LOCO MAE (HC) | | |
| LOCO MAE (CVD) | | |
| Filter Delta | | |
| W params | k×8 = 24-32 | n_voxels×8 = 3,408+ |

### Phase 4 Decision
- Procrustes > SRM: [ ]
- Best ROI: [ ]
- Filter candidate: [ ]

---

## Final Summary

| Method | Space | HC MAE | CVD MAE | Delta | Note |
|--------|-------|--------|---------|-------|------|
| FE_OLS (baseline) | SRM | | | | Current LOCO |
| Ridge | SRM | | | | Phase 2 — df stabilization |
| GP Matern (V2) | SRM | | | | Phase 3 — SRM ceiling |
| **Procrustes FE** | **Proc** | | | | **Phase 4 — main path** |
| Procrustes + Filter | Proc | | | | Phase 4 — corrected CVD |
