# Supplementary: 필터 사전 검증 및 RDM 거리 지표 민감도 분석
> sub-08 (deutan) = 주 필터 후보 (FDR 32 pairs, split-half r=0.73-0.84 전 ROI); sub-10 = 피질 보상 성공 사례 (FDR 0 pairs). L-M 축 결핍 + S-cone 보상 패턴이 3명 CVD 일관. V2가 가장 견고한 ROI (group split-half r=0.733, B1 유일 유의 pair). Crossnobis는 80% 보수적 → 결과는 지표 의존적

## 목표
- CVD 피험자가 SRM 공유 공간에서 HC와 **색 쌍 수준**에서 신뢰할 수 있는 차이를 보이는지 검증
- 필터 설계 진행 전 통계적 기반 확보: (a) 그룹 수준 유의성 (B1), (b) 시간적 안정성 (B2), (c) 개인 수준 부트스트랩 신뢰구간 (B3)
- FDR 다중비교 보정 후 필터 타겟 색 쌍 선정
- RDM 거리 지표 (correlation vs crossnobis) 및 정규화 방법의 민감도 확인
- CIELab vs angular RDM 구조 진단 (원형 가정 점검)

---

## 피험자 및 데이터

| 항목 | 내용 |
|------|------|
| 피험자 | 10명 (HC 7명: sub-01~07, CVD 3명: sub-08 deutan, sub-09 protan, sub-10 deutan) |
| 입력 | Phase 1 Procrustes-aligned amplitudes (C010), shape (6, 8, n_voxels) |
| SRM | HC-only 학습 (7 HC), CVD는 SVD projection으로 HC 공간에 투영 |
| SRM k | V1=4, V2=4, V3=3, hV4=3 (7-fold LOSO mean rank aggregation) |
| 거리 지표 | Euclidean distance in k-dim SRM space (B1-B3); correlation distance, crossnobis distance (민감도 분석) |
| 색 쌍 | 8×8 RDM 상삼각 28 unique pairs |
| Pair z-score | (CVD distance − HC mean) / HC SD; 양수 = 과분리, 음수 = 혼동/압축 |
| 총 테스트 수 | B3: 336 비교 (3 CVD × 4 ROI × 28 pairs); FDR은 per-subject-ROI (28 tests 단위) |
| 제외 | sub-07 hV4 (16 voxels → NaN) → hV4 FDR 분석 제외 |

---

## 방법

### B1: Pair-Level Exhaustive Permutation Test
- 모든 C(10,3) = 120 가능한 HC/CVD 배정으로 그룹 순열 검정
- 순열마다 SRM 재학습 → 순환성 방지 (각 null 배정이 자체 공유 공간 획득)
- 양측 p-value per pair. 최소 달성 가능 p = 0.008 (120 순열 한계 → 매우 큰 효과만 유의)

### B2: Split-Half Stability
- 데이터를 전반부 (runs 1-3) / 후반부 (runs 4-6)로 분할
- 각 반에 SRM 별도 적합 → 교차 오염 방지
- 28-pair z-score 프로파일 간 Spearman 상관으로 시간적 안정성 평가
- 유의성: 순열 null (1,000회 무작위 pair 라벨 셔플) 대비 평가
- 높은 split-half reliability = 필터 설계에 적합한 안정적 왜곡 프로파일 (trait-like)

### B3: Bootstrap Confidence Intervals
- 1,000 bootstrap iterations: HC 피험자 복원 추출 → **매 반복 SRM 재학습**
- HC 표집 → SRM 학습 → 공유 공간 → 거리 계산 → z-score의 전체 불확실성 연쇄 포착
- 95% CI per pair per subject; CI가 0을 제외하면 유의
- SRM 재학습 없이는 CI가 불확실성을 과소 추정 (공유 공간을 고정으로 취급)

### FDR Correction (Benjamini-Hochberg)
- **Per-subject-ROI FDR** (q = 0.05): 28 pairs 단위로 보정 — 논문 최종 방법
- 계층적 데이터 구조 존중 (피험자별 CVD subtype, ROI별 노이즈 특성이 다름)
- 참고: Global FDR (252 tests = 3 subjects × 3 ROIs × 28 pairs, hV4 제외) → 37 생존. Per-subject-ROI (39 총) vs Global (37 총) 근사 일치 → 보정 전략에 강건

### 메트릭 민감도 분석
- 6 조건: {correlation, crossnobis} × {none, within-subject, pooled} 정규화
- Crossnobis: Ledoit-Wolf shrinkage로 노이즈 공분산 추정, C(6,2)=15 run pair 교차 검증, SRM 독립 지표
- 개인 비교: Crawford & Howell (1998) 수정 t-검정 (df=6, one-tailed)
- 수렴도: 조건 간 z-score Spearman 상관

### CIELab 진단
- Angular RDM vs CIELab RDM (a*b* Euclidean): Mantel test (10,000 순열)
- Persistent homology (H1, ripser): 원형 위상 구조 검정
- MDS stress curve (2D-7D): 내재 차원성 평가
- Isomap vs MDS: 비선형 구조 탐색
- Per-subject Mantel + ISC (inter-subject consistency)

---

## 결과

### B1: 그룹 수준 순열 검정 (Exhaustive, 120 permutations)

| ROI | 유의 pairs (p < 0.05) | 주요 pair |
|-----|----------------------|-----------|
| V1 | 0 | min p = 0.058 (red-magenta) |
| **V2** | **1** | **blue-purple p = 0.042** |
| V3 | 0 | — |
| hV4 | 0 | min p = 0.058 (red-magenta) |

> V2 blue-purple이 유일한 그룹 수준 유의 pair. 3명 CVD 모두 V2에서 blue-purple 거리 상승 → S-cone 보상 처리와 일치. 120 순열 한계로 검정력 본질적 제한; B3 bootstrap이 주요 개인 수준 증거 제공

### B2: Split-Half Reliability

| 피험자 | V1 | V2 | V3 | hV4 | 프로파일 |
|--------|------|------|------|------|----------|
| sub-08 (deutan) | 0.777* | 0.839* | 0.765* | 0.729* | 전 ROI 신뢰 |
| sub-09 (protan) | 0.645* | 0.684* | 0.264 | 0.747* | V3 불안정 |
| sub-10 (deutan) | 0.286 | 0.677* | 0.010 | 0.234 | V2만 유의 |
| **Group mean** | **0.569** | **0.733** | **0.346** | **0.570** | **V2 최고** |

*p < 0.05 (순열 null 대비)

> **sub-08**: 가장 안정적 CVD (r = 0.73-0.84 전 ROI) → 체계적이고 재현 가능한 왜곡 → 필터 설계 적합
> **sub-10**: V2에서만 유의 (r = 0.677) → 최소/보상된 CVD 표현형과 일치
> **V2**: 그룹 수준 최고 안정성 (r = 0.733) — Phase 2의 V2 최강 ROI 소견과 수렴

### B3: Bootstrap 유의 Pair 수 (CI가 0 제외)

| ROI | sub-08 | sub-09 | sub-10 |
|-----|--------|--------|--------|
| V1 | 15/28 | 17/28 | 8/28 |
| V2 | 17/28 | 13/28 | 10/28 |
| V3 | 18/28 | 10/28 | 13/28 |
| hV4 | 21/28 | 8/28 | 22/28 |

> sub-08: 전 ROI에 걸쳐 광범위 (15-21 sig pairs), hV4에서 최다 (21/28 = 75%)
> sub-09: V1 집중 (17/28) — Phase 2 개인 검정의 V1 p=0.007 소견과 일치
> sub-10: hV4에서 역설적 최대치 (22/28) 하지만 V1에서 최소 (8/28) → 약하지만 확산된 효과

### FDR 보정 결과 (Per-Subject-ROI, q = 0.05)

| 피험자 | V1 | V2 | V3 | hV4 | 합계 |
|--------|----|----|----|----|------|
| **sub-08** (deutan) | 3 | 12 | 17 | — | **32** |
| **sub-09** (protan) | 6 | 0 | 1 | — | **7** |
| sub-10 (deutan) | 0 | 0 | 0 | — | **0** |
| **합계** | **9** | **12** | **18** | **0** | **39** |

hV4는 sub-07의 16 voxels → NaN으로 FDR 분석에서 제외. Discovery rate: 39/252 = 15.5% (chance 5%의 약 3배)

> **sub-08**: 32 FDR pairs — V2 (12) + V3 (17)에 집중. 충분한 통계적 기반
> **sub-09**: 7 FDR pairs — V1에 6개 집중 (magenta 축), protan 특이적 피질 서명
> **sub-10**: 0 FDR pairs — sub-08과 동일 deutan 유전형이지만 피질 표상은 HC 범위 내 → 피질 보상 성공

> 참고: Global FDR (252 tests) → 37 생존 (sub-08: 30, sub-09: 7, sub-10: 0). Per-subject-ROI (39) vs Global (37)의 근접 일치 → 보정 전략에 강건

### 주요 인접 색 쌍 Bootstrap 95% CI

| Pair | ROI | sub-08 z [CI] | sub-09 z [CI] | sub-10 z [CI] |
|------|-----|---------------|---------------|---------------|
| red-orange | V1 | -0.82 [-2.5, -0.2]* | -1.35 [-3.3, -0.7]* | -0.68 [-2.2, +0.1] |
| orange-yellow | V1 | +2.00 [+1.3, +4.4]* | +0.73 [-0.8, +1.8] | -0.25 [-1.4, +0.7] |
| cyan-blue | V1 | -0.95 [-2.4, -0.4]* | -0.51 [-1.6, +0.4] | -0.59 [-1.9, -0.0]* |
| purple-magenta | V1 | +0.98 [+0.2, +1.9]* | +1.15 [+0.4, +2.1]* | +0.31 [-1.1, +1.2] |
| red-magenta | V1 | +0.69 [-0.3, +1.9] | +3.02 [+1.9, +6.9]* | +1.43 [-0.1, +3.5] |
| blue-purple | V2 | +4.34 [+2.9, +15.3]* | +0.33 [-0.9, +1.4] | +2.08 [+1.2, +7.9]* |
| orange-yellow | V2 | +3.29 [+2.0, +33.2]* | +0.40 [-0.4, +8.1] | -0.13 [-0.9, +3.0] |
| red-orange | V2 | +1.66 [+0.8, +3.7]* | +1.64 [+0.7, +4.0]* | +0.51 [-0.4, +2.1] |

*CI가 0을 제외. 비대칭 CI (예: sub-08 blue-purple V2: [+2.9, +15.3])는 HC 7명 복원 추출에서 특정 HC 과대 표집 시 극단 z-score 발생 → 하한이 상한보다 유의성 판단에 더 중요

### 피험자 간 일관 패턴

**L-M 축 결핍** (3명 CVD 동일 방향 = 음의 z-score, 혼동/압축):

| Pair | ROI | sub-08 | sub-09 | sub-10 | 기전 |
|------|-----|--------|--------|--------|------|
| red-orange | V1 | -0.82 | -1.35 | -0.68 | L-M 혼동 |
| cyan-blue | V1 | -0.95 | -0.51 | -0.59 | L-M 혼동 |
| green-blue | V1 | -0.89 | -2.41 | -1.16 | L-M 혼동 |

> L/M cone 민감도 저하 → 적-녹 차원의 피질 표상 압축. Protan, deutan 모두 공통

**S-cone 보상 상승** (3명 CVD 동일 방향 = 양의 z-score, 과분리):

| Pair | ROI | sub-08 | sub-09 | sub-10 | 기전 |
|------|-----|--------|--------|--------|------|
| red-magenta | V1 | +0.69 | +3.02 | +1.43 | S-cone 보상 |
| purple-magenta | V1 | +0.98 | +1.15 | +0.31 | S-cone 보상 |
| red-magenta | V2 | +1.66 | +1.64 | +0.51 | S-cone 보상 |
| blue-purple | V2 | +4.34 | +0.33 | +2.08 | S-cone 보상 (B1 p=0.042) |

> L-M 결핍 + S-cone 보상 이중 패턴이 광수용체 기반 CVD 기전과 일치: L-M opponency 저하를 S-cone 신호 강화로 부분 보상. sub-09 (protan) V1 red-magenta z=3.02, sub-08 (deutan) V2 blue-purple z=4.34로 subtype 특이적

### 계층적 증폭 (Correlation Distance Analysis)

| ROI | sub-08 sig pairs | sub-09 sig pairs | sub-10 sig pairs | Mean |delta| |
|-----|-----------------|-----------------|-----------------|--------------|
| V1 | 20/28 | 24/28 | 17/28 | 0.47-0.60 |
| V2 | 20/28 | 21/28 | 19/28 | 0.43-0.58 |
| V3 | 19/28 | 17/28 | 16/28 | 0.60-0.75 |
| hV4 | 26/28 | 19/28 | 12/28 | 0.63-0.75 |

> V1/V2 (mean |delta| = 0.43-0.60) → V3/hV4 (0.60-0.75): 고차 시각 영역이 개별 쌍 차이를 통합적 처리로 증폭. sub-08의 hV4 26/28은 광범위한 피질 재조직을 시사

### 메트릭 민감도: Correlation vs Crossnobis

| Metric | Normalization | Uncorrected p < 0.05 | FDR q < 0.05 |
|--------|---------------|---------------------|-------------|
| **Correlation** | None (baseline) | **15** | 0 |
| Correlation | Within | 16 | 0 |
| Correlation | Pooled | 15 | 0 |
| **Crossnobis** | None | **3** | 0 |
| Crossnobis | Within | 8 | 0 |
| Crossnobis | Pooled | 3 | 0 |

> Crossnobis는 correlation 대비 **80% 보수적** (15→3 uncorrected pairs). 교차 검증 Mahalanobis 거리 + 노이즈 정규화로 더 엄격하지만 제한된 데이터에서 노이즈도 큼. Crossnobis 3개 pair 모두 sub-08 소속 — sub-08이 전 분석에서 가장 강한 효과 일관

> 참고: 이 결과는 Crawford & Howell t-검정 사용 (bootstrap 아닌). FDR 0 생존은 통계 방법 차이, 오류 아님 (아래 Bootstrap vs Crawford & Howell 참조)

**수렴도 (Spearman r, correlation vs crossnobis z-scores):**

| ROI | sub-08 | sub-09 | sub-10 | Mean r |
|-----|--------|--------|--------|--------|
| V1 | 0.556** | 0.726*** | 0.413* | **0.565** |
| V2 | 0.349 | 0.715*** | 0.361 | 0.475 |
| V3 | 0.537** | 0.342 | 0.614*** | 0.498 |
| hV4 | 0.551** | 0.067 | 0.337 | 0.318 |

> V1 최강 수렴 (mean r=0.565), hV4 최약 (0.318). 중간 수렴 (r=0.3-0.7) → 두 지표가 일부 공유 분산 포착하지만 상당한 차이 존재

**정규화 민감도**: Pooled = no normalization과 동일 (HC 분산이 SRM 정렬로 이미 균질). Within-normalization은 순위 보존 (r ≈ 1.0) 하지만 marginal pairs의 유의성 경계 이동 (+1 pair for correlation). **정규화 불필요** → 현행 방법 검증

### Bootstrap vs Crawford & Howell 차이

| 방법 | 특징 | FDR 생존 | 용도 |
|------|------|---------|------|
| **Bootstrap** (B3) | HC 복원 추출 1,000회, 매 반복 SRM 재학습 | **39** (per-subject-ROI) | HC 간 변동성 포착 → 필터 사전 검증 |
| **Crawford & Howell** | 고정 HC 모수 (mean, SD 1회 계산), df=6 t-분포 | **0** | 보수적 단일 사례 검정 → 임상 진단 |

> Bootstrap z-score가 체계적으로 높음 (평균 차이 1.17, 최대 3.53). 예: sub-08 V1 red-yellow — Bootstrap z=5.14, p=2.72e-07 (FDR 유의) vs Crawford & Howell z=2.04, p=0.087 (미유의). Bootstrap은 HC 7명에서 "정상 기준" 정의의 불확실성을 적절히 포착 → 필터 관련 분석에 채택

### SRM 순환성 검증 (Criticism 2)

| 피험자 | ROI | SRM FDR pairs | Crossnobis FDR pairs | Spearman r | p |
|--------|-----|--------------|---------------------|-----------|---|
| sub-08 | V1 | 3/28 | 0/28 | 0.534 | 0.003 |
| sub-08 | V2 | 11/28 | 0/28 | 0.332 | 0.084 |
| sub-08 | V3 | 14/28 | 0/28 | 0.438 | 0.020 |
| sub-09 | V1 | 6/28 | 0/28 | 0.635 | <0.001 |
| sub-09 | V2 | 1/28 | 0/28 | 0.649 | <0.001 |
| sub-10 | V1 | 0/28 | 0/28 | 0.638 | <0.001 |
| sub-10 | V2 | 1/28 | 0/28 | 0.701 | <0.001 |

> Native voxel space (crossnobis)에서 **0 pairs FDR 생존** vs SRM에서 37-39 생존. 하지만 z-score 간 중간-강한 상관 (r=0.3-0.7, 8/9 subject-ROI에서 p<0.05) → SRM이 진짜 CVD-HC 분산 구조를 포착하되 k=3-4 차원 축소로 증폭. 통계적 유의성이 표상 공간 선택에 의존하는 것이 핵심 한계. "이방성 재분배"는 **공유 표상 기하학** 내 소견으로 재프레이밍

### CIELab vs Angular RDM 진단 (6개 분석)

Phase 1 MDS 진단에서 V1/V2가 4개 기준(stress, circular order, Shepard R², Mantel) 모두 실패. 이것이 **부적절한 참조 모델(equidistant angular) 때문인지**, 아니면 진정한 구조 부재인지 검증.

**배경**: 실험 8색의 CIELab (a\*, b\*) 인접 거리가 30.9~68.3 (2.2배 비균등). Phase 1의 `ideal_circular_rdm()`은 모든 인접 쌍을 동일 거리로 가정.

**가설**: CIELab 기반 참조 RDM으로 교체하면 V1/V2 구조가 검출될 수 있음

#### Decision Framework

| ROI | Q1: CIELab > Angular | Q2: H1 Topology | Q3: Higher-D | Q4: Isomap > MDS | Verdict |
|-----|---------------------|-----------------|-------------|-----------------|---------|
| **V1** | FAIL (r=-0.195 vs -0.295, 둘 다 음수) | FAIL (p=1.0) | FAIL (stress=0.126, ρ=0.643) | FAIL (MDS 우세) | **UNSTRUCTURED (0/4)** |
| **V2** | FAIL (r=0.124, p=0.261) | FAIL (p=1.0) | **PASS** (3D stress=0.097) | **PASS** (Isomap ρ=0.524 > MDS 0.262) | **STRUCTURED (2/4)** |
| V3 | FAIL | — | — | — | UNSTRUCTURED (0/4) |
| hV4 | FAIL | — | — | — | UNSTRUCTURED (0/4) |

#### Analysis 1: Stress Curve (1-7D)

| ROI | Alignment | stress < 0.10 도달 차원 | 2D~7D stress |
|-----|----------|----------------------|-------------|
| V1 | raw | dim=5 | 0.498, 0.279, 0.174, 0.127, 0.098, 0.067, 0.031 |
| V1 | procrustes | dim=4 | 0.482, 0.271, 0.138, 0.096, 0.059, 0.036, 0.024 |
| V1 | **srm** | **>7 (plateau 0.127)** | 0.463, 0.188, 0.126, 0.127, 0.127, 0.127, 0.128 |
| V2 | srm | **dim=3** | 0.463, 0.194, 0.097, 0.098, 0.099, 0.099, 0.099 |
| hV4 | srm | dim=2 | 0.464, 0.084, ... |

> V1 SRM: dim=3 이후 stress가 0.127에서 **plateau** — 어떤 차원에서도 거리 구조를 복원 불가. **같은 V1 데이터**가 raw/procrustes에서는 dim=4~5에서 정상 도달 → SRM 투영이 거리 구조를 비가역적으로 손상

> V2 SRM: 3D에서 0.097 달성 — 3차원적 색 거리 구조 존재 (2D 부족)

#### Analysis 2: 참조 RDM 비교 (Mantel, 10,000 permutations)

4개 참조: Angular (equidistant), CIELab (a\*,b\*), a\*-only (L-M axis), b\*-only (S-LM axis). Bonferroni α = 0.05/16 = 0.003.

| ROI | Align | Angular r (p) | CIELab r (p) | a\*-only r (p) | b\*-only r (p) |
|-----|-------|--------------|-------------|---------------|---------------|
| V1 | srm | -0.295 (0.926) | -0.195 (0.837) | -0.292 (0.958) | -0.083 (0.613) |
| V2 | srm | -0.005 (0.503) | 0.124 (0.261) | **0.282 (0.085)** | -0.130 (0.721) |
| V3 | srm | -0.120 (0.685) | -0.014 (0.489) | -0.165 (0.785) | 0.124 (0.225) |
| hV4 | srm | -0.302 (0.942) | -0.308 (0.966) | -0.249 (0.936) | -0.085 (0.572) |
| **hV4** | **raw** | 0.276 (0.062) | **0.402 (0.018\*)** | 0.186 (0.171) | 0.075 (0.321) |

> **V1 SRM**: 4개 모델 **모두 음의 상관**. 지각적으로 가까운 색이 neural RDM에서 오히려 먼 패턴 → 의미 있는 색 기하학 부재

> **V2 SRM**: a\*-only (L-M axis) r=0.282 (p=0.085, trend) — V2의 L-M cone opponent selectivity와 일치 (Gegenfurtner, 2003)

> **hV4**: raw 공간 CIELab r=0.402\* → SRM 후 r=-0.308 (부호 반전). **SRM 투영이 원래 존재하던 CIELab 구조를 파괴**

#### Analysis 3: Persistent Homology (H1)

| ROI | Max H1 lifetime | p-value | 판정 |
|-----|----------------|---------|------|
| V1 | 0.448 | 1.000 | 원형 위상 없음 |
| V2 | 0.156 | 1.000 | 원형 위상 없음 |

> p=1.0 = 1,000개 랜덤 RDM **전부**가 관측값 이상의 H1 lifetime 생성. H1 feature가 noise 수준

#### Analysis 4: Higher-D MDS + PCA Best 2D

| ROI | Dim | Stress | Shepard R² | Circular ρ (p) |
|-----|-----|--------|-----------|---------------|
| V1 | 2D | 0.188 | 0.734 | 0.619 (0.102) |
| V1 | 3D | 0.126 | 0.880 | 0.643 (0.086) |
| V1 | 4D | 0.127 | 0.878 | 0.643 (0.086) |
| V2 | 2D | 0.194 | 0.677 | -0.262 (0.531) |
| V2 | **3D** | **0.097** | **0.919** | 0.357 (0.385) |
| V2 | 4D | 0.098 | 0.918 | -0.024 (0.955) |

> V1: 3D→4D에서 개선 없음. warm/cool 이분법 정도의 약한 구조만 존재

> V2: 3D Shepard R²=0.919 (거리 복원 우수) but circular ρ=0.357 (ns) → **구조는 있되 원형이 아님**

#### Analysis 5: Isomap vs MDS (SRM, HC mean)

| ROI | MDS ρ (p) | Isomap ρ (p) | 우승 |
|-----|----------|-------------|------|
| V1 | 0.619 (0.102) | -0.476 (0.233) | MDS |
| V2 | -0.262 (0.531) | **0.524 (0.183)** | **Isomap** |

> V2에서 Isomap이 MDS보다 circular order를 2배 더 잘 복원 → 비선형 manifold 존재. Filter 설계 시 Matern kernel / Isomap embedding 고려 가치

#### Analysis 6: Per-Subject V1/V2 (SRM)

| Subject | Group | V1 CIELab r | V2 CIELab r | V1 ISC | V2 ISC |
|---------|-------|------------|------------|--------|--------|
| sub-01 | HC | -0.153 | -0.027 | 0.783 | 0.817 |
| sub-02 | HC | -0.230 | 0.011 | 0.879 | 0.824 |
| sub-03 | HC | 0.020 | -0.036 | 0.610 | 0.402 |
| sub-04 | HC | -0.107 | 0.261 | 0.716 | 0.599 |
| **sub-05** | HC | -0.100 | **0.485\*** | 0.853 | 0.577 |
| sub-06 | HC | -0.264 | -0.238 | 0.592 | 0.565 |
| sub-07 | HC | -0.142 | 0.148 | 0.834 | 0.736 |
| sub-08 | CVD | -0.125 | 0.071 | 0.667 | 0.567 |
| sub-09 | CVD | -0.379 | -0.072 | **0.252** | **0.366** |
| sub-10 | CVD | -0.366 | -0.197 | 0.693 | 0.521 |

> V2의 약한 trend는 **sub-05 한 명에 의해 주도**될 가능성 (유일한 유의 피험자)

> sub-09 (protan) ISC 최저 (V1=0.252, V2=0.366) → HC 공통 패턴에서 가장 이탈

---

### 필터 공간 분석: SRM vs Procrustes

#### 핵심 질문: SRM 공간에서 HC-CVD 패턴 매칭 필터가 가능한가?

**가능하다 — 단, discrete matching에 한정.** HC와 CVD가 동일 SRM 공간에 투영되므로, "CVD의 색 A 패턴 ≈ HC의 색 B 패턴"을 찾는 lookup table 방식은 유효함. 이 접근은 색 기하학을 가정하지 않으므로 위 진단 결과와 충돌하지 않음.

Phase 2 cross-decoding이 이미 이 방식을 검증:

| ROI | sub-08 acc | sub-09 acc | sub-10 acc |
|-----|-----------|-----------|-----------|
| V1 | **1.000** | 0.875 | **1.000** |
| V2 | 0.750 | 0.875 | **1.000** |
| V3 | 0.625 | 0.750 | 0.875 |
| hV4 | 0.375 | 0.625 | 0.375 |

> 10/12 검정 유의 (p<0.001) → SRM 공간에서 HC 패턴으로 CVD 색 매칭 가능

**그러나 역설**: cross-decoding 정확도가 높다 = CVD 패턴이 **올바른 HC 패턴과 이미 일치** = SRM 필터는 대부분 **항등 변환(identity)**에 가까움. Phase 2 LORO (HC 0.635 vs CVD 0.665, p=0.668)에서도 확인: CVD의 범주적 색 표상은 HC와 동등.

**진짜 CVD 결손**은 8개 범주 **사이**의 연속적 보간에서 나타남:

| 과제 | 측정 대상 | HC vs CVD | SRM 필터 교정 가능? |
|------|----------|----------|-------------------|
| LORO (classification) | 8개 범주 분류 | HC ≈ CVD (p=0.668) | 교정 불필요 (이미 동등) |
| LOCO (interpolation) | 연속 색조 보간 | HC 69.4° vs CVD 87.4° (hV4, p=0.017\*) | **불가** (SRM에 연속 구조 부재) |

> ⚠️ SRM discrete matching 필터: 가능하지만 교정 효과 미미 (범주 수준은 이미 동등)
>
> ✅ Procrustes continuous 필터: CVD의 실제 결손(연속 보간 왜곡)을 교정 가능

#### Procrustes 공간이 필터에 적합한 5가지 근거

| 기준 | Procrustes | SRM | 근거 |
|------|-----------|-----|------|
| ① 연속 색 거리 보존 | ✅ stress 정상 (dim=4~5) | ❌ V1 plateau, hV4 부호 반전 | 이번 진단 |
| ② 개인 voxel-level 정보 | ✅ 수백 voxel 유지 | ❌ k=3~4로 99% 축소 | FE W matrix 차원 |
| ③ 보간 과제 최적성 | ✅ LOCO HC MAE 69.4° (hV4) | ❌ LOCO +2.8~22.3° 페널티 | Phase 2 LOCO |
| ④ W matrix 풍부성 | ✅ (568×6)=3,408 params | ❌ (4×6)=24 params | 개인차 식별 불가 |
| ⑤ 변환의 수학적 특성 | ✅ isometry (거리 완전 보존) | ❌ 투영 (정보 손실) | 강체 변환 정의 |

> **결론**: 필터는 Procrustes 공간에서 FE W matrix 변환 (W_CVD → W_HC)으로 구축.
> SRM은 cross-decoding 검증 도구로는 유효하나, 필터 operating space로는 부적합.

#### ROI별 필터 Prior 전략

| ROI | 기하학적 Prior | 근거 | 대안 |
|-----|--------------|------|------|
| V1 | **불가** | 0/4, 모든 참조 음의 r | W 변환 + Group Prior (+4.3%) |
| V2 | **L-M axis 제한적** | a\*-only trend (p=0.085), Isomap 우세 | Matern kernel, Group Prior (+8.3%) |
| V3 | Procrustes 직접 사용 | 원래 Procrustes 우세 ROI | 표준 접근 |
| hV4 | **CIELab kernel (Procrustes 공간)** | raw CIELab r=0.402\* | 유일한 기하학 확인 ROI |

---

## 핵심 해석

1. **sub-08 = 주 필터 후보** — FDR 32 pairs (V1=3, V2=12, V3=17), split-half r=0.73-0.84 전 ROI, L-M 결핍 + S-cone 극심한 과보상 (yellow-purple V2 z=13.87). 필터 설계를 위한 충분한 통계적 기반
2. **sub-09 = protan 특이적 서명** — V1 magenta 축 과분리 (cyan-magenta z=4.08, red-magenta z=3.52)가 deutan S-cone 패턴과 구별됨. FDR 7 pairs (V1에 6개 집중) → 탐색적 필터 가능
3. **sub-10 = 피질 보상 성공 사례** — FDR 0 pairs, 낮은 split-half reliability (V1/V3/hV4 r=0.01-0.29), Phase 2 Crawford & Howell 전 ROI 비유의. sub-08과 동일 deutan 유전형이지만 피질 표상은 HC 범위 내 → 필터 불가, 사례 연구로 보고
4. **V2 = 가장 견고한 ROI** — 그룹 split-half r=0.733 최고, B1 유일 유의 pair (blue-purple p=0.042), S-cone 보상 효과 최강 (sub-08 blue-purple z=4.34). Phase 2의 V2 7/7 LOSO folds + 양쪽 split-half 유의와 수렴
5. **계층적 증폭** — V1/V2 (mean |delta|=0.43-0.60) → V3/hV4 (0.60-0.75). sub-08 FDR pairs도 V1(3) → V2(12) → V3(17) 누적. 고차 영역이 단일 쌍 차이를 통합 처리로 증폭 — Zeki et al. (1991) 계층적 색 표상 모델과 일치
6. **메트릭 의존적 결과** — Crossnobis가 correlation 대비 80% 보수적 (15→3 uncorrected). Native voxel space에서도 0 FDR 생존. 중간 수렴 (r=0.3-0.7)으로 공유 기저 신호 존재하지만 SRM이 k=3-4 차원 축소로 증폭. 통계적 유의성이 표상 공간에 의존 → 행동 검증이 궁극적 판단 기준

---

## 필터 전략 요약

### sub-08 (Deutan): 14 pairs (V1=3, V2=11)

| 영역 | 주요 타겟 | z-score | 방향 | 기전 |
|------|----------|---------|------|------|
| V2 | yellow-purple | +13.87 | 정상화 ↓ | S-cone 극심한 보상 |
| V2 | red-yellow | +9.38 | 정상화 ↓ | S-cone 과의존 |
| V2 | blue-purple | +6.15 | 정상화 ↓ | S-cone 과분리 |
| V2 | orange-yellow | +5.45 | 정상화 ↓ | S-cone 보상 |
| V1 | red-yellow | +5.14 | 정상화 ↓ | S-cone 과의존 |

**필터 목표**: S-cone 축 과분리 감소 + L-M 분리도 복원. Fourier 4-파라미터 제약 + LORO CV

### sub-09 (Protan): 7 pairs (V1=6, V2=1)

| 영역 | 주요 타겟 | z-score | 방향 | 기전 |
|------|----------|---------|------|------|
| V1 | cyan-magenta | +4.08 | 정상화 ↓ | S+M cone 보상 |
| V1 | orange-magenta | +3.71 | 정상화 ↓ | Magenta 축 상승 |
| V1 | red-magenta | +3.52 | 정상화 ↓ | L-cone 결핍 보상 |
| V1 | yellow-purple | -3.31 | 복원 ↑ | 과소분리 (protan 특이) |

**필터 목표**: Magenta 축 정상화 + 일부 cool-color 분리도 복원. Deutan과 보상 축이 다름 (magenta vs yellow-purple)

### sub-10 (Deutan, 보상 성공): 0 pairs → 필터 불가

- 사례 연구로 보고 ("피질 보상 성공" — 동일 유전형, 다른 피질 서명)
- 행동 데이터로 보상 검증 예정

### 행동 검증 기준
- r > 0.5 (SRM 거리 ↔ JND 역치) → 필터 진행
- r < 0.3 → characterization only 논문으로 전환
- 0.3 < r < 0.5 → 탐색적 필터 + 불확실성 인정

---

## 제한점

| 제한점 | 설명 |
|--------|------|
| Bootstrap 증폭 | Bootstrap z-score가 Crawford & Howell보다 체계적으로 높음 (평균 차이 1.17). FDR 39 생존은 HC 간 변동성 효과 포착이며 독립 재현이 아님 |
| Crossnobis 비재현 | Native voxel space에서 0/252 FDR 생존. SRM 공간에서만 효과 검출 → 결과가 표상 의존적 |
| sub-10 해석 모호 | 피질 보상 vs 불충분한 SNR 구별 불가. 행동 검증 (JND 역치) 필요 |
| n = 3 CVD | 그룹 검정 저검정력, CI 넓음. sub-08 V2 blue-purple CI [+2.9, +15.3]. 인과 해석 불가 |
| hV4 제외 | sub-07의 16 voxels → NaN. hV4 correlation distance 결과 (sub-08 26/28) 해석 주의 |
| 넓은 비대칭 CI | HC 7명 복원 추출 + SRM 재학습 변동성 → 일부 CI 극단적 (sub-08 orange-yellow V2: [+2.0, +33.2]). 하한이 유의성 판단에 더 유효 |
| B1 검정력 한계 | 120 순열 → 최소 p = 0.008. 그룹 수준 검출은 매우 큰 효과에 제한 |
| 신경-물리 비대응 | Mantel test 전 ROI 비유의 + persistent homology 원형 구조 기각 → 8 이산 색 자극의 신경 기하학이 물리적 hue circle을 따르지 않음 |

---

## References
- Benjamini, Y., & Hochberg, Y. (1995). Controlling the false discovery rate: a practical and powerful approach to multiple testing. *J Royal Statistical Society: Series B*, 57(1), 289-300.
- Crawford, J. R., & Howell, D. C. (1998). Comparing an individual's test score against norms derived from small samples. *Clinical Neuropsychologist*, 12(4), 482-486.
- Walther, A., et al. (2016). Reliability of dissimilarity measures for multi-voxel pattern analysis. *NeuroImage*, 137, 188-200.
- Zeki, S., et al. (1991). A direct demonstration of functional specialization in human visual cortex. *J Neuroscience*, 11(3), 641-649.
- Chen, P. H., et al. (2015). A reduced-dimension fMRI shared response model. *NIPS*.
- Brouwer, G. J., & Heeger, D. J. (2009). Decoding and reconstructing color from responses in human visual cortex. *J Neuroscience*, 29(44), 13992-14003.
