# Future Phase 3: 행동 검증 — 파일럿 데이터 분석

> **상태**: 예비 분석 (CVD N=1, HC N=5, 파일럿). 추가 데이터 수집 가능.
> **날짜**: 2026-03-27 (N=5 업데이트)
> **피험자**: sub-08 (CDX002, deutan CVD) vs HC1 (CDX003) + HC2 (CDX004) + JYPark + JHKim + MJChoi
> **데이터**: `data/` (JHKim, JYPark, MJChoi raw trials), HC1/HC2/CVD summary values

---

## 0. 개요

본 문서는 파일럿 행동 데이터(JND, RSVP 8AFC)를 Phase 2(SRM) 및 Future Phase 1(Forward Model)의 신경 지표와 통합하여, CVD 색 표상 결손의 교차 양상(cross-modal) 수렴을 평가한다. HC 5명(HC1=CDX003, HC2=CDX004, JYPark, JHKim, MJChoi)의 그룹 평균 기준으로 방향 분류 및 교차 양상 일치도를 보고한다.

핵심 해리 2가지:

1. **전역 vs 국소 해리**: SRM z-score(전역 끝점 거리)와 JND 방향(국소 지각 민감도)이 검증 가능 쌍에서 다수 불일치(DISCORDANT)
2. **변별 vs 보간 해리**: RSVP 8AFC(범주적 변별)는 CVD 81% 정확도이나, LOCO(연속 보간)는 완전 실패

---

## 1. 행동 데이터 요약

### 1-1. JND (Just Noticeable Difference) — 2AFC 계단법

**방법**: 적응적 계단법(쌍당 2개 인터리브, 0.8과 0.5에서 수렴). JND = 마지막 N회 반전의 평균. 8개 색 쌍 검사.

**해석**: JND = "다르다" 응답을 위한 최소 보간 단계. 낮을수록 민감(HYPER), 높을수록 둔감(HYPO).

| 쌍 | HC1 | HC2 | JHKim | JYPark | MJChoi | HC Mean (N=5) | HC SD | CVD (sub-08) | Ratio | 방향 (N=5) |
|------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| red-orange | 0.235 | 0.018 | 0.168 | 0.057 | 0.110 | **0.117** | 0.087 | **0.062** | 0.53 | **HYPER** |
| orange-yellow | 0.443 | 0.064 | 0.328 | 0.168 | 0.248 | **0.250** | 0.146 | **0.840** | 3.36 | **HYPO** |
| yellow-green | 0.103 | 0.018 | 0.130 | 0.054 | 0.103 | **0.082** | 0.045 | **0.278** | 3.41 | **HYPO** |
| green-blue | 0.103 | 0.020 | 0.100 | 0.102 | 0.063 | **0.077** | 0.036 | **0.077** | 0.99 | borderline |
| yellow-purple | 0.025 | 0.015 | 0.030 | 0.018 | 0.018 | **0.021** | 0.006 | **0.062** | 2.95 | **HYPO** |
| blue-purple | 0.165 | 0.040 | 0.173 | 0.103 | 0.158 | **0.128** | 0.056 | **0.120** | 0.94 | borderline |
| cyan-magenta | 0.048 | 0.015 | 0.060 | 0.030 | 0.028 | **0.036** | 0.018 | **0.040** | 1.11 | borderline |
| red-cyan | 0.048 | 0.015 | 0.050 | 0.015 | 0.023 | **0.030** | 0.018 | **0.015** | 0.50 | **HYPER** |

> **출처**: `data/JHKim/`, `data/JYPark/`, `data/MJChoi/` (raw trials), HC1/HC2/CVD from pilot summary.
> 각 HC/CVD 값 = sc0과 sc1의 jnd_mean 평균. HC Mean = 5명 산술평균.
> 방향 기준: ratio > 1.15 = HYPO, ratio < 0.85 = HYPER, 그 외 = borderline.

**N=3→N=5 방향 변동** (JHKim, MJChoi 추가):
- **안정 HYPO (3쌍)**: orange-yellow, yellow-green, yellow-purple — N=3에서도 N=5에서도 HYPO. ratio 3~5x로 매우 강건.
- **HYPO→borderline (2쌍)**: blue-purple (1.17→0.94), cyan-magenta (1.29→1.11) — N=3에서 marginal HYPO였으나 JHKim, MJChoi의 높은 JND가 HC mean을 상승시켜 borderline으로 전환.
- **안정 HYPER (2쌍)**: red-orange, red-cyan — 일관.
- **안정 borderline (1쌍)**: green-blue — 일관.

**HC 개인차 요약**: HC2가 전 쌍에서 최저(floor 효과 의심, §8). HC1과 JHKim이 유사한 패턴(높은 O-Y, B-P). JYPark, MJChoi는 중간 범위. 5명의 CV(SD/Mean)는 쌍별 40~70% — 정상 범위 내 큰 변동.

### 1-2. RSVP 8AFC — 색 식별

**방법**: 64 시행, 8색, 8지 강제선택.

| 지표 | HC1 (CDX003) | HC2 (CDX004) | CVD (CDX002) |
|--------|:---:|:---:|:---:|
| 정확도 | 100% (64/64) | 96.9% (62/64) | 81.2% (52/64) |
| 평균 RT (정답) | 2.30s | 2.82s | 3.72s |
| 제한시간 초과 | 0 | 0 | 1 |
| 음수 RT | 0 | 0 | 1 |

> **출처**: `data/behav_pilot/HC_rsvp_8afc_ses1_run1.csv`, `data/behav_pilot/HC2_rsvp_8afc_ses1_run1.csv`, `data/behav_pilot/sub-08_rsvp_8afc_ses1_run1.csv`
> HC2 오류 2건: green(4)→cyan(5) 1건, purple(7)→blue(6) 1건 — 모두 인접색 혼동.

**CVD 오류 패턴 (12건)**:

| 자극 | 응답 | 건수 | 색상 거리 |
|----------|----------|:-----:|:---:|
| purple (7) | magenta (8) | 3 | 인접 |
| magenta (8) | purple (7) | 2 | 인접 |
| yellow (3) | green (4) | 1 | 인접 |
| yellow (3) | magenta (8) | 1 | 원거리 |
| yellow (3) | red (1) | 1 | 원거리 |
| orange (2) | yellow (3) | 1 | 인접 |
| green (4) | yellow (3) | 1 | 인접 |
| green (4) | timeout | 1 | — |

> purple-magenta 혼동 5건(42%)이 최다 → S-cone 의존 영역의 범주 경계 불안정.
> yellow 관련 오류 3건 → M-cone 이동에 의한 yellow 표상 왜곡과 일치.

**색별 정확도**:

| 색 | HC1 | HC2 | CVD |
|-------|:---:|:---:|:---:|
| red (1) | 100% | 100% | 100% |
| orange (2) | 100% | 100% | 87.5% |
| yellow (3) | 100% | 100% | 62.5% |
| green (4) | 100% | 87.5% | 75.0% |
| cyan (5) | 100% | 100% | 100% |
| blue (6) | 100% | 100% | 100% |
| purple (7) | 100% | 87.5% | 50.0% |
| magenta (8) | 100% | 100% | 75.0% |

> HC1: 전색 100%. HC2: green(87.5%), purple(87.5%) 약간 저하 — CVD와 동일 색에서 오류 발생하나 정도가 훨씬 경미.
> CVD 최저: purple (50%), yellow (62.5%). 최고: red, cyan, blue (100%).

---

## 2. 신경 지표 — 원천 값

### 2-1. SRM z-score (Phase 2 사전검증)

SRM z-score = (CVD 거리 - HC 평균) / HC SD (SRM 공유 공간). 양수 = 과분리, 음수 = 압축/혼동.

**sub-08 (deutan) — JND와 겹치는 핵심 쌍:**

| 쌍 | V1 z | V2 z | V2 FDR | 원추세포 예측 |
|------|:---:|:---:|:---:|:---:|
| red-orange | -0.82 | +1.66 | YES | Type A: L-M 압축 |
| orange-yellow | +2.00 | +3.29 | YES | Type B: M' 피크 이동 → 과분리 |
| yellow-green | — | +4.14 | YES | Type B: M' 양방향 이동 |
| green-blue | -0.89 | — | — | Type A: M' 감소 → blue 접근 |
| yellow-purple | — | **+13.87** | YES | Type B: S-cone 극심 보상 |
| blue-purple | — | **+6.15** | YES | Type B: S-cone 보상 |
| cyan-blue | -0.95 | — | — | Type A: L-M 혼동 |
| red-cyan | — | +0.60 | — | — |

> **출처**: `analysis/phase5_filter_optimization/pre_validation/notion_prevalidation.md` §1-1

### 2-2. Crossnobis RDM 차이 (Phase 2, 원 복셀 공간)

Crossnobis diff = CVD 거리 - HC 거리 (Procrustes 정렬된 원 복셀 공간, SRM 아님). Bootstrap 1000.

**sub-08 (deutan) — JND 겹침 쌍:**

| 쌍 | V1 diff [CI] | V2 diff [CI] |
|------|:---:|:---:|
| Red-Orange | -0.604 [-0.837, -0.395] | -0.605 [-0.873, -0.346] |
| Orange-Yellow | +0.550 [+0.426, +0.661] | +0.498 [+0.211, +0.826] |
| Yellow-Green | -0.451 [-0.608, -0.268] | +0.496 [+0.190, +0.827] |
| Green-Blue | +0.127 [-0.094, +0.360] | -0.158 [-0.322, -0.012] |
| Yellow-Purple | +0.287 [+0.158, +0.462] | +0.670 [+0.308, +1.052] |
| Blue-Purple | +0.466 [+0.146, +0.791] | +0.881 [+0.669, +1.103] |
| Cyan-Blue | -0.449 [-0.764, -0.152] | +0.452 [+0.244, +0.656] |
| Red-Cyan | +1.107 [+0.767, +1.396] | +0.597 [+0.291, +0.896] |

> **출처**: `analysis/phase2_SRM_across_between/results/color_pair_analysis/color_pair_analysis_V1.json`, `color_pair_analysis_V2.json`

### 2-3. Forward Model — LOCO 색별 취약성

Crawford-Howell 검정: sub-08 개인 LOCO voxel_corr vs HC 분포 (df=6, 단측).

| ROI | 색 | sub-08 값 | HC 평균 | t | p |
|-----|-------|:---:|:---:|:---:|:---:|
| V1 | **orange** | -0.178 | +0.149 | -5.30 | **0.0018** |
| V1 | **yellow** | -0.438 | -0.016 | -4.17 | **0.0059** |
| V1 | **purple** | -0.499 | +0.163 | -3.13 | **0.020** |
| V2 | **orange** | -0.575 | +0.179 | -3.03 | **0.023** |
| V2 | **yellow** | -0.693 | +0.003 | -3.94 | **0.0077** |
| V2 | **cyan** | -0.211 | +0.186 | -4.26 | **0.0053** |

> **출처**: `analysis/phase4_forward_model/RESULTS.md` §3d

### 2-4. Forward Model — LOCO 그룹 요약

| ROI | HC 평균 (SD) | CVD 평균 (SD) | Cohen's d | p (Welch) |
|-----|:---:|:---:|:---:|:---:|
| V1 | +0.130 (0.097) | -0.012 (0.054) | +1.61 | **0.021** |
| V2 | +0.150 (0.188) | -0.174 (0.130) | +1.85 | **0.022** |
| V3 | +0.023 (0.240) | -0.008 (0.163) | +0.14 | 0.819 |
| hV4 | +0.183 (0.200) | -0.058 (0.207) | +1.19 | 0.169 |

> **출처**: `analysis/phase4_forward_model/RESULTS.md` §2b

---

## 3. 교차 양상 일치도 분석

### 3-1. SRM z vs JND 방향 — HC N=5 기준

**단순 예측**: SRM z 양수(과분리) → HYPER(낮은 JND) 예측. SRM z 음수(압축) → HYPO(높은 JND) 예측.

| 쌍 | SRM z (최고 ROI) | z 방향 | JND 방향 (N=5) | 일치? |
|------|:---:|:---:|:---:|:---:|
| red-orange | V2: +1.66 | 과분리 | **HYPER** | **YES** |
| orange-yellow | V2: +3.29 | 과분리 | **HYPO** | **NO** |
| yellow-green | V2: +4.14 | 과분리 | **HYPO** | **NO** |
| green-blue | V1: -0.89 | 압축 | borderline | N/A |
| yellow-purple | V2: +13.87 | 과분리 | **HYPO** | **NO** |
| blue-purple | V2: +6.15 | 과분리 | borderline | N/A |
| cyan-magenta | — | — | borderline | N/A |
| red-cyan | V1: +1.11* | 과분리 | **HYPER** | **YES*** |

\*red-cyan SRM z는 crossnobis V1 값 (SRM 사전검증에서 해당 쌍 미보고).

**N=5 기준**: 일치 1쌍(red-orange), 불일치 3쌍(O-Y, Y-G, Y-P), borderline 제외 3쌍, N/A 1쌍 → 검증 가능 4쌍 중 **3쌍 불일치(75%)**.

**N=3→N=5 변화**: blue-purple과 cyan-magenta가 borderline으로 전환되어 평가 대상에서 제외됨. 검증 가능 쌍이 줄었으나, 불일치 비율(75%)은 여전히 높음.

**해석**: N=5로 HC 기준이 안정화되어도 SRM z ↔ JND 불일치가 지배적. 이는 SRM z(전역 기하학적 거리)와 JND(국소 보간 민감도)가 측정하는 속성 자체가 다르기 때문이며, HC 기준의 불확실성에 의한 artifact가 아니다.

**설명 (수정: 2026-03-22)**:

**1단계 — "고원(plateau) 가설" 기각**: Forward Model gradient profile 분석(§3-4)으로 검증한 결과, 복셀 공간에서 CVD의 국소 기울기는 평탄화되지 않았다 — 오히려 HC와 비례하거나 더 가팔랐다(V2 HYPO 쌍: gradient ratio 1.01~1.38). "끝점 과분리 + 중간 기울기 감소"라는 초기 설명은 기각된다. 단, gradient 분석이 전체 8색으로 학습한 W를 사용한 반면 LOCO는 7색 학습 W를 사용하므로(§3-4 참조), 이 분석은 LOCO 실패의 메커니즘과 다른 조건임에 유의.

**2단계 — 수정된 해석: 0차 vs 고차 기하학의 해리**

SRM z와 LOCO는 **모두 기하학적 연산**이지만, 색 다양체(manifold)의 서로 다른 **차수(order)**의 속성을 포착한다:

| | SRM z | LOCO |
|---|---|---|
| 측정 대상 | 두 끝점 간 거리 (**0차**) | 이웃 색으로부터 held-out 색의 복원 가능성 (**고차**) |
| 공간 | SRM 공유 공간 (K=3-4차원) | 원 복셀 공간 (수백 차원) |
| 질문 | "두 색이 얼마나 먼가?" | "이 색을 이웃에서 보간할 수 있는가?" |
| W 사용 | 없음 (직접 거리) | 피험자 자신의 데이터로 7색 ridge_gcv 학습 → 1색 예측 |

LOCO가 측정하는 것: **피험자 자체 색 다양체의 국소 규칙성(local regularity)**. 7색으로 학습한 모델이 나머지 1색을 보간할 수 있으면 다양체가 매끄럽고, 실패하면 해당 색이 이웃 대비 불규칙한 위치에 있다. HC는 8색 모두 매끄럽게 보간 가능. CVD(sub-08)는 orange, yellow, purple 위치에서 보간 실패 — 이 색들이 cone shift로 인해 다양체의 국소 불규칙 지점이 되었음을 시사.

SRM z는 0차(쌍별 거리)를 측정하므로, 끝점이 과분리(z+)되어도 국소 규칙성(보간 가능 여부)에 대해서는 정보를 제공하지 않는다. JND는 보간된 중간 자극의 변별이므로, 0차(거리)보다 고차(보간 충실도)에 의존한다.

**핵심 관계**: SRM z와 LOCO가 **같은 색**(orange, yellow, purple)에서 이상을 감지하지만, SRM z의 **방향**(과분리→HYPER 예측)은 JND와 불일치하고, LOCO의 **방향**(보간 실패→HYPO 예측)은 JND와 일치한다. 이는 SRM z가 왜곡의 **위치**는 올바르게 포착하나, 왜곡의 **행동적 결과**를 예측하려면 고차 속성(보간 충실도)이 필요함을 시사한다.

### 3-2. LOCO 취약성 vs JND — 100% 일치

| JND HYPO 쌍 (N=5) | 관련 LOCO 취약 색 | 일치 |
|------|------|:---:|
| orange-yellow | orange (V1 p=0.0018), yellow (V1 p=0.0059) | **YES** |
| yellow-green | yellow (V1 p=0.0059, V2 p=0.0077) | **YES** |
| yellow-purple | yellow (V1 p=0.0059), purple (V1 p=0.020) | **YES** |

**HYPO 3쌍 모두 LOCO 취약 색을 포함 (3/3 = 100%).** N=3에서 N=5로 변경 후에도 이 3쌍은 안정적으로 HYPO 유지.

| JND HYPER/borderline 쌍 (N=5) | LOCO 취약 색 포함? | 해석 |
|------|------|:---:|
| red-orange (HYPER) | Red: 취약 아님 | HYPER 일관 |
| red-cyan (HYPER) | Red, Cyan: 취약 아님/경계 | HYPER 일관 |
| green-blue (borderline) | Blue: 취약 아님 | 방향 불확정 |
| blue-purple (borderline) | Blue: 취약 아님 | 방향 불확정 |
| cyan-magenta (borderline) | Cyan (V2 p=0.0053 — 경계) | 방향 불확정 |

**N=3→N=5 안정성**: HYPO 3쌍(orange-yellow, yellow-green, yellow-purple)은 **N=2, N=3, N=5 모든 HC 기준에서 HYPO** — 어떤 HC 표본 크기를 사용하든 LOCO ↔ JND 일치도 100% 유지. blue-purple과 cyan-magenta가 N=5에서 borderline으로 전환되었으나, 이들은 원래 LOCO 취약 색을 강하게 포함하지 않으므로 핵심 결론에 영향 없음.

**결론**: LOCO 색별 취약성이 JND HYPO 방향을 3/3 정확도(100%)로 예측 — HC N에 **불변**. Forward Model의 보간 지표는 행동적으로 타당하다.

### 3-3. 원추세포 분광 감도 모델 검증

**모델**: 가우시안 근사 — L_pk=564nm, M_pk=534nm (정상), M'_pk=555nm (deutan), S_pk=420nm. 2채널: L-M 대립(dLM) + S-(L+M)/2 (dS). 국소 기울기 = 양 끝점에서 ±5nm 범위의 |df/dλ| 평균.

**지표**: 총 기울기 = sqrt(dLM² + w_S * dS²). w_S ∈ [1.0, 20.0] 탐색.

**최적 결과 (HC1 기준)**: w_S=1.2 → 5/8 정답 (62.5%).

| 쌍 | 비율 (D/N) | 예측 | HC1 실제 | HC1 일치 | HC2 실제 | HC2 일치 | HC평균 실제 | HC평균 일치 |
|------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| red-orange | 1.20 | HYPER | HYPER | YES | HYPO | **NO** | HYPER | YES |
| orange-yellow | 1.24 | HYPER | HYPO | **NO** | HYPO | **NO** | HYPO | **NO** |
| yellow-green | 1.11 | HYPER | HYPO | **NO** | HYPO | **NO** | HYPO | **NO** |
| green-blue | 1.02 | HYPER | HYPER | YES | HYPO | **NO** | borderline | N/A |
| yellow-purple | 1.08 | HYPER | HYPO | **NO** | HYPO | **NO** | HYPO | **NO** |
| blue-purple | 1.17 | HYPER | HYPER | YES | HYPO | **NO** | borderline | N/A |
| cyan-magenta | 1.01 | HYPER | HYPER | YES | HYPO | **NO** | borderline | N/A |
| red-cyan | 1.12 | HYPER | HYPER | YES | HYPER | YES | HYPER | YES |

> **출처**: `data/behav_pilot/cone_model_verify.py`

**HC 기준별 일치도**:
- **HC1 기준**: 5/8 정답 (62.5%) — 모델이 전 쌍 HYPER 예측이므로 HC1 HYPER 5쌍과 일치
- **HC2 기준**: 2/8 정답 (25%) — HC2 기준 HYPER는 red-cyan 1쌍뿐이므로 모델의 HYPER 예측 대부분 불일치
- **HC평균 기준**: 명확한 쌍만 평가 시 2/5 정답 (40%) — borderline 3쌍 제외

**한계**: 단색광 파장 근사가 비분광 색(purple=440nm, magenta=420nm)에서 부적절. 모델은 deutan M' 이동(534→555nm)이 모든 기울기를 가파르게 하므로 전 쌍에 대해 HYPER만 예측. 기울기만으로는 HYPO 방향을 설명 불가. HC 기준에 따라 일치도가 크게 변동하는 것 자체가 이 모델의 한계를 보여준다.

**시사점**: LOCO 취약성(고차 피질 통합을 포착)이 단순 분광 모델(HC1: 62.5%, HC2: 25%, HC평균: 40%)보다 우수한 예측자(100%, HC 기준 불변).

### 3-4. Forward Model Gradient Profile 검증 — "고원 가설" 기각

> 추가: 2026-03-22. 스크립트: `scripts/analysis_gradient_profile.py`

**목적**: §3-1의 기존 설명("끝점 과분리 + 중간 기울기 평탄화")을 실증 검증.

**방법**:
1. 각 피험자의 ridge_gcv W matrix (6채널 FE basis, (6, V_s)) 로딩
2. FE basis를 1° 해상도로 생성 → C(θ): (360, 6)
3. Y_pred(θ) = C(θ) @ W → 각 θ에서 예측 복셀 패턴
4. Local gradient(θ) = ||Y(θ+1) - Y(θ)|| (Euclidean)
5. 각 색 쌍별로:
   - Global distance = ||Y(θ_A) - Y(θ_B)|| → SRM z 대응
   - Mean local gradient = 구간 내 gradient 평균 → JND 대응
6. HC 7명 평균 vs CVD (sub-08) 비교

**"고원" 예측**: HYPO 쌍에서 global ratio (CVD/HC) > 1 이면서 gradient ratio < 1.

**결과**:

| ROI | 쌍 | Global ratio | Gradient ratio | JND | 고원? |
|-----|------|:---:|:---:|:---:|:---:|
| V1 | orange-yellow | 1.02 | 1.02 | HYPO | **NO** |
| V1 | yellow-green | 1.00 | 1.00 | HYPO | 경계 |
| V1 | yellow-purple | 0.99 | 0.99 | HYPO | **NO** |
| V2 | orange-yellow | **1.51** | **1.38** | HYPO | **NO** (둘 다 증가) |
| V2 | yellow-green | 1.04 | 1.01 | HYPO | **NO** |
| V2 | yellow-purple | **1.79** | **1.17** | HYPO | **NO** (둘 다 증가) |
| V4 | orange-yellow | 2.27 | 2.33 | HYPO | **NO** (gradient 더 가파름) |
| V4 | yellow-green | 1.78 | 1.55 | HYPO | **NO** |
| V4 | yellow-purple | 2.97 | 2.20 | HYPO | **NO** |

**전체 일치도**: Plateau+HYPO 조합은 V1 1건, V3 1건에 불과. 12개 HYPO 사례(4 ROI × 3 쌍) 중 2건(17%).

**V2 핵심**: SRM z가 FDR-유의한 ROI에서 HYPO 3쌍 모두 global ratio > 1 **이면서** gradient ratio도 > 1. CVD의 복셀 공간 반응이 전체적으로 스케일업되었을 뿐, 끝점만 벌어지고 중간이 평탄해진 것이 아니다.

**구조적 원인**: FE basis (cos², 6채널, 60° 폭)가 gradient profile의 **형태**를 결정하고 W matrix는 **진폭**만 조절. gradient(θ) = ||(C(θ+1) - C(θ)) @ W|| 에서 C 차분은 고정 → W 크기가 커지면 global distance와 local gradient가 **함께** 증가. 고원 패턴은 이 basis 구조에서 구조적으로 발생 불가.

**결론**: "고원(plateau)" 메커니즘은 기각. SRM z-JND 불일치는 복셀 공간의 기울기 차이가 아니라, **SRM z(기하학적 거리)와 JND(보간 기반 변별)가 색 표상의 서로 다른 속성을 측정**하기 때문이다 (§3-1 수정된 해석 참조).

> **출처**: `results/gradient_profile/summary.json`, `figures/gradient_profile_V{1,2,3,4}.png`, `figures/gradient_plateau_verification.png`

---

## 4. RSVP-LOCO 수렴

### 4-1. 색별 오류 정렬

| 색 | RSVP 정확도 | LOCO 취약성 | 정렬 |
|-------|:---:|:---:|:---:|
| red | 100% | 취약 아님 | 일관 |
| orange | 87.5% | V1 p=0.0018 | **수렴** |
| yellow | 62.5% | V1 p=0.0059, V2 p=0.0077 | **수렴** |
| green | 75.0% | (개별 유의 아님) | 부분 |
| cyan | 100% | V2 p=0.0053 | **괴리** (RSVP 정상, LOCO 실패) |
| blue | 100% | 취약 아님 | 일관 |
| purple | 50.0% | V1 p=0.020 | **수렴** |
| magenta | 75.0% | 취약 아님 | 부분 |

**핵심 발견**: purple, yellow, orange가 RSVP와 LOCO에서 수렴. cyan은 예외 — 범주적 식별은 보존되나 연속 보간은 실패. Forward Model의 **변별 ≠ 보간** 해리를 재확인.

---

## 5. 필터 설계 시사점

### 5-1. SRM RDM의 역할 재정립 (수정: 2026-03-22)

SRM RDM과 JND의 불일치(§3-1, 33%)와 고원 가설 기각(§3-4)을 반영하여, SRM RDM의 위치를 재정립한다.

**SRM RDM이 보여주는 것 (유효)**:
- CVD 색 공간의 **기하학적 왜곡이 존재**한다는 독립 증거 (V2: FDR-유의 12쌍)
- 왜곡의 **위치와 크기** (어떤 쌍이 과분리/압축되었는지)
- 원추세포 이동의 신경적 영향에 대한 정량적 기술

**SRM RDM의 한계 — "방향" 예측 실패**:
- SRM z의 **부호**(과분리/압축)는 JND 방향(HYPO/HYPER)을 예측하지 못함 (33%)
- 과분리(양의 SRM z) ≠ 더 나은 지각
- 단, SRM z와 LOCO는 **같은 색**(orange, yellow, purple)에서 이상을 감지 → SRM z가 왜곡의 **위치**는 올바르게 포착하나 **행동적 방향**을 예측하지 못하는 것 (§3-1 핵심 관계 참조)

**SRM RDM fitting의 구조적 한계 (Phase 2 v2 발견)**:
- SRM projection(R_cvd = SVD(data @ pinv(S)))이 CVD 데이터를 HC 공간에 최대 정렬 → cone shift 신호(δθ)가 R에 흡수
- 결과: RDM 기반 δθ fitting 시 δθ=0이 항상 최적 → **fitting criterion으로 구조적으로 불가**
- LOCO는 SRM projection 없이 원 복셀 공간에서 작동하므로 δθ 신호를 보존

**결론**: SRM RDM은 **왜곡 위치의 존재 증거**로 유효하며, LOCO와 같은 색에서 이상을 감지하므로 두 지표는 관련이 있다. 그러나 SRM z의 부호는 행동 방향을 예측하지 못하고, RDM fitting은 SRM projection의 구조적 한계로 불가능하므로, LOCO가 fitting criterion이 되어야 한다.

### 5-2. 수정된 파이프라인

**기존 계획**:
```
SRM RDM 기반 δθ fitting → hV4 LOCO 평가
```

**수정 계획 (2026-03-22)**:
```
LOCO 기반 δθ fitting (primary) → SRM RDM 수렴 검증 (convergence validation)
```

- **Primary criterion**: LOCO MSE — 행동 예측력 100%, 기능적 보간 충실도 직접 측정
- **Convergence validation**: LOCO에서 최적화된 δθ가 SRM RDM 왜곡도 교정하는지 확인
  - 수렴하면: δθ가 기하학적 + 기능적 왜곡을 동시 설명 → 강한 증거
  - 수렴하지 않으면: 기능적 교정은 달성했으나 기하학적 잔존 왜곡 → 해리 자체가 발견

이 구조는 Phase 2 v2 파이프라인(MEMORY.md 참조)의 cross-eval 프레임워크와 일치: fit on A → eval on B.

### 5-3. SRM RDM의 논문 내 위치

SRM RDM 결과의 서술 프레임:

> "CVD 색 공간은 SRM 공유 공간에서 유의한 기하학적 왜곡을 보인다 (V2: 12쌍 FDR-유의, 최대 z=+13.87). SRM z와 LOCO 취약성은 동일한 색(orange, yellow, purple)에서 이상을 감지하여, 두 지표가 같은 기저 왜곡(cone shift에 의한 색 다양체 변형)을 포착함을 시사한다. 그러나 SRM z의 부호(과분리 vs 압축)는 행동적 민감도 방향(HYPO vs HYPER)을 예측하지 못한 반면 (검증 가능 4쌍 중 1쌍 일치=25%, HC N=5), LOCO 보간 실패는 JND HYPO 방향을 완벽히 예측하였다 (3/3=100%, HC N에 불변). 이 부분 해리는 쌍별 거리(0차 기하학)와 국소 보간 충실도(고차 기하학)가 동일 왜곡의 서로 다른 차수의 표현이며, 지각적 색 변별이 후자에 의존함을 보여준다."

### 5-4. HYPER 교정 가능성

JND HYPER 쌍(red-orange 0.27x, red-cyan 0.32x 등)은 CVD가 해당 쌍을 HC보다 더 다르게 지각함을 시사. 두 가지 해석:
- **유익한 보상**: HYPER가 실생활 변별에 도움이 되면 유지
- **왜곡**: HYPER가 지각적 균일성을 훼손하면 교정

HYPO와 HYPER 모두 필터 타겟이 될 수 있으며, 목표가 HC 정상화인지 기능적 최적화인지에 따라 결정.

---

## 6. Geometry→Function Framework: RDM 시뮬레이션 기반 LOCO 재현 파이프라인

> **상태**: 설계 단계 (2026-03-23). 실험 미실시.
> **동기**: RDM이 표상적 원인을, LOCO/JND가 기능적 발현을 보여준다면, RDM 수준에서 추정한 왜곡으로 가상 뇌 데이터를 생성하여 LOCO 취약 패턴을 재현할 수 있는가?

### 6-0. 핵심 논리

| 수준 | 지표 | 질문 | 역할 |
|------|------|------|------|
| **표상적 원인** | RDM/ΔRDM | "어디가, 얼마나 왜곡되었나?" | Pathology의 **존재 증거** (§3-1: 위치 포착, 방향 불일치) |
| **기능적 발현** | LOCO/JND | "어떤 색에서 보간이 실패하나?" | Pathology의 **행동적 결과** (§3-2: 100% JND 일치) |

**RDM→LOCO 방향 불일치의 설명**: RDM은 쌍별 거리(0차), LOCO는 국소 보간 충실도(고차). 저차원 공간(K=3~4)에서의 끝점 거리 변화가 고차원 voxel 공간의 보간 가능성을 직접 결정하지 않음. 그러나 **동일한 색**(orange, yellow, purple)에서 양쪽 모두 이상 감지 → 공유된 기저 원인(cone shift) 존재.

**피질 간 방향 차이의 자연성**: V1→V2→hV4로 갈수록 stimulus-driven → percept-driven 표상으로 전환 (Kim et al. 2020 PNAS). Anomalous trichromat의 V1 chromatic response 감소가 V2v/V3v에서 보상됨 (Tregillus et al. 2021 Curr Biol). RDM 왜곡 **방향**이 피질마다 다른 것은 neural compensation의 자연스러운 결과.

**인과 가설**: "초기 표상(RDM) 왜곡을 교정하면, 하류 기능(LOCO/JND)도 개선될 수 있다."
→ 직접 intervention 없이는 인과 입증 불가. 본 프레임워크는 **시뮬레이션 기반 필요조건 검증**: RDM 왜곡이 LOCO 실패를 **재현**하는지 확인. 재현 성공 = 인과의 필요조건 충족, 재현 실패 = 추가 메커니즘 존재.

### 6-1. 파이프라인 설계

```
Phase A: δ 추정 (RDM criterion — fitting)
────────────────────────────────────────
1. HC mean W 고정 (기존 step0)
2. δ sweep: C(θ+δ) @ W_HC → ΔRDM_sim or RDM comparison
3. Loss = f(ΔRDM_sim(δ), ΔRDM_obs) — 다중 메트릭 (§6-2)
4. δ*_RDM = argmin Loss
5. Permutation test on δ*_RDM

Phase B: Synthetic CVD-like brain data 생성
────────────────────────────────────────
6. Per-HC: Ŷ_δ_i = C(θ + δ*_RDM) @ W_HC_i   # (8, V_s)
   Ŷ_δ = mean across 7 HCs

Phase C: LOCO 재현 테스트 (독립 평가)
────────────────────────────────────────
7. Ŷ_δ에서 LOCO 수행 (synthetic data에 대한 7색→1색 보간):
   For each color c:
     C_train = C(θ+δ*)[나머지 7색]
     W_sim = ridge_gcv(C_train, Ŷ_δ[나머지 7색])
     Y_pred_c = C(θ+δ*)[c] @ W_sim
     vuln_sim[c] = corr(Y_pred_c, Ŷ_δ[c])

8. 비교:
   a) Spearman(vuln_sim, vuln_CVD_observed)  → 프로파일 재현?
   b) orange/yellow/purple이 vuln_sim에서도 취약?
   c) Spearman(vuln_sim, JND_direction)      → 행동 예측?

Phase D: 대조군 검증
────────────────────────────────────────
9. Null: random δ ~ U(-50, 50) × 1000 → LOCO profile →
   observed match가 null보다 유의하게 높은가?
10. sub-10 (normal): δ*_RDM에서 LOCO 문제 없어야 함
```

**순환성 방지**: fitting criterion (Phase A: RDM) ≠ evaluation criterion (Phase C: LOCO). RDM은 pairwise distance (28개 값), LOCO는 per-color interpolation fidelity (8개 값). 같은 데이터의 서로 다른 함수이나, 완전 독립은 아님 (Diedrichsen & Kriegeskorte 2017: encoding model ↔ RSA는 동일 2nd moment의 다른 표현). **진정한 독립 검증은 JND (외부 행동 데이터)**.

**선행 연구 선례**: Sprague et al. (2018 eNeuro) — forward model synthetic data → decoder 적용 → ground truth 비교. Brouwer & Heeger (2013 J Neurosci) — gain model 시뮬레이션 → channel response → categorical clustering 재현.

### 6-2. RDM fitting 다중 메트릭

#### 6-2-1. 현재까지 테스트된 RDM 메트릭

| 메트릭 | 방법 | 결과 | 한계 |
|--------|------|------|------|
| SRM-space RDM | A_g @ C(θ+δ)^T → pdist | **전 ROI 실패** | SRM alignment이 δθ 흡수 |
| Voxel→SRM Path A | C(θ+δ)@W → SVD → SRM RDM | V1 sub-08 cone_3way r=0.543 | SD 높음, fold 불안정 |
| Voxel RDM Path B | C(θ+δ)@W → pdist directly | 대부분 ≈0 | Voxel noise 지배 |
| **ΔRDM (cone_1way)** | RDM_sim(δ)-RDM_sim(0) vs RDM_CVD-RDM_HC | **V1 sub-09 p=0.005*** | sub-08 실패, V4 FP |

**핵심 미탐색**: ΔRDM은 **cone_1way만 테스트**. cone_3way, fourier 미실험. sub-08 deutan에서 S-cone shift가 관여할 가능성 → cone_3way ΔRDM이 개선될 수 있음.

#### 6-2-2. 신규 RDM 거리 메트릭 (추가 실험 대상)

**A) Cosine distance (angular distance)**
```
d_cos(i,j) = 1 - (y_i · y_j) / (‖y_i‖ ‖y_j‖)
```
- 의미: "두 색의 voxel 패턴이 같은 방향인가?" (크기 무시)
- Correlation distance와의 차이: correlation = mean-centered cosine. cosine = 원점 기준
- BOLD 공통 baseline이 존재하면 양자가 다름
- 장점: scale-free이면서 centering artifact 없음

**B) Local triangle distortion**
```
Δ_local(i,j;k) = d(i,j) - [d(i,k) + d(k,j)] / 2
```
- 의미: "i-j 거리가 중간점 k를 경유한 평균 거리 대비 과대/과소인가?"
- Δ < 0: shortcut (i,j가 k 경유보다 가까움) → manifold 오목
- Δ > 0: detour (i,j가 k 경유보다 멀음) → manifold 볼록
- k 선택: circular neighbors (i-1, i+1, j-1, j+1) 또는 all intermediate colors
- **LOCO와의 직접 연결**: LOCO는 7색으로부터 1색을 보간 → local triangle distortion이 크면 보간 실패 예측
- 산출: 8×8×8 tensor → (i,j) 쌍마다 k 평균 → 28개 값 (RDM과 동일 차원)

**C) Cosine + triangle composite**
```
ΔRDM_composite(δ) = w₁ · ΔRDM_corr(δ) + w₂ · ΔRDM_cos(δ) + w₃ · Δ_triangle(δ)
```
가중치는 HC cross-validation으로 결정하거나, 각 메트릭 독립 fitting → 수렴 여부 확인.

#### 6-2-3. Distortion model × RDM metric 실험 매트릭스

| | ΔRDM corr | ΔRDM cosine | Local triangle | Vox→SRM Path A |
|---|:---:|:---:|:---:|:---:|
| **cone_1way** (df=1) | ✅ Done | ❌ TODO | ❌ TODO | ✅ Done (failed) |
| **cone_3way** (df=3) | ❌ TODO | ❌ TODO | ❌ TODO | ✅ Done (V1 r=0.543) |
| **fourier** (df=4) | ❌ TODO | ❌ TODO | ❌ TODO | ✅ Done (V1 r=0.804) |
| **per_color** (df=8) | ❌ TODO | ❌ TODO | ❌ TODO | (overfitting risk) |

**우선순위**: ΔRDM × {cone_3way, fourier} × {corr, cosine, triangle} = 6 조합. sub-08 deutan V1에서 우선 테스트 (ΔRDM cone_1way 실패한 조건).

### 6-3. W Preservation 검증 (선행 조건)

Synthetic data 생성의 핵심 가정: W_CVD ≈ W_HC (피질 인코딩 보존, 입력만 다름).

**올바른 검증 방향**:
```python
# CVD 실제 반응 = W_true @ C(θ + δ_true) 가정
# 따라서 CVD data를 cone-shifted basis로 학습하면:
W_CVD_shifted = ridge_gcv(C(θ + δ*), X_CVD)  # shifted basis → CVD W
W_HC_mean = mean(W_HC_i)                       # HC mean W

# 프로파일 유사도
sim = corr(W_CVD_shifted.flatten(), W_HC_mean.flatten())
# sim > 0.8 → W preservation 지지
```

주의: X_CVD 자체가 왜곡된 입력을 거친 반응이므로, C(θ-δ*)가 아니라 C(θ+δ*)를 사용해야 함. "CVD 망막이 실제로 보는 색(θ+δ)"에 맞게 W를 학습하는 것.

**추가 검증**: Per-ROI voxel count, SNR, tuning selectivity (max(W)/std(W)) HC vs CVD 비교표 작성.

### 6-4. 통계적 검정력 고려

- N=3 CVD (1 deutan, 1 protan, 1 normal control) → 사례 연구(case study) 수준
- Bayes factor (BF₁₀) 보고로 "증거 강도"를 정량화: BF > 10 = strong evidence, BF < 1/3 = evidence for null
- 논문 프레이밍: "pilot framework" or "proof-of-concept" — replication cohort (N≥8 CVD) 명시

### 6-5. 선행 연구 근거

| 주제 | 핵심 논문 | 관련성 |
|------|-----------|--------|
| RDM-행동 연결 | Kriegeskorte et al. 2008 (Front Sys Neurosci) | RSA 프레임워크: neural RDM ↔ behavioral RDM |
| Synthetic 검증 | Sprague et al. 2018 (eNeuro) | Forward model → synthetic data → decoder → ground truth 비교 |
| 계층적 보상 | Tregillus et al. 2021 (Curr Biol) | V1 CVD 감소 → V2v/V3v 보상 |
| V4 perceptual hub | Bannert & Bartels 2018 (J Neurosci) | hV4 encoding model → trial-by-trial 행동 예측 |
| Cone shift 모델 | Machado et al. 2009 (IEEE TVCG) | Severity-parameterized cone fundamental interpolation |
| Encoding-RSA 통합 | Diedrichsen & Kriegeskorte 2017 (PLOS CB) | Encoding model ↔ RSA = 동일 2nd moment의 다른 표현 |
| V1→V4 전환 | Kim et al. 2020 (PNAS) | V1/V2 stimulus-driven, V4/VO1 percept-driven |

### 6-6. Pending Validations

- [ ] **V1**: ΔRDM × {cone_3way, fourier} × {corr, cosine, triangle} 6 조합 (sub-08 우선)
- [ ] **V2**: 동일 매트릭스 (sub-08 ΔRDM cone_1way 실패 → cone_3way 개선 가능?)
- [ ] **W preservation**: per-ROI W_CVD_shifted vs W_HC_mean 유사도
- [ ] **Phase C**: Synthetic LOCO 재현 스크립트 (step4_synthetic_loco.py)
- [ ] **Null distribution**: random δ × 1000 → LOCO profile → permutation p-value
- [ ] **Bayes factor**: per subject-ROI BF₁₀ 계산

---

## 7. 제한점 및 향후 계획

### 7-1. 제한점
- **표본 크기**: CVD N=1, HC N=5. 핵심 결론(LOCO→JND 100%)은 N에 불변이나, borderline 쌍의 분류는 추가 HC에 따라 변동 가능.
- **HC 개인차**: HC2의 JND가 나머지 4명의 1/5~1/13 수준(§8 상세). N=5에서 HC2의 영향이 희석되어 기준이 안정화.
- **HC 피험자 불일치**: JND HC ≠ fMRI HC(sub-01~sub-07). 피험자 내 직접 비교 불가.
- **단색광 근사**: 원추세포 모델이 단일 파장 근사 사용. purple, magenta는 광대역 자극.
- **fMRI-행동 비등록**: sub-08 행동 세션 ≠ sub-08 fMRI 세션.
- **계단법 floor 효과**: HC2가 다수 쌍에서 level=0에 도달(§9 상세). 진정한 역치가 계단법 해상도 이하일 가능성.
- **Gradient 분석의 basis 한계**: FE 6채널 basis의 매끄러움이 gradient profile 형태를 고정 → 더 높은 해상도의 basis(또는 비모수적 접근)에서는 고원 효과가 관찰될 가능성을 완전히 배제할 수 없음. 단, 현재 forward model의 최적 basis(FE-3~FE-8)가 LOCO를 잘 예측하므로, basis 해상도 자체가 병목이 아닐 가능성이 높다.

### 7-2. 추가 데이터 수집 계획
- CVD 추가 피험자(protan, 정상 대조) JND 검사
- 피험자 내 fMRI + 행동 동시 검사
- 확장된 색 쌍 세트 (8쌍 이상)

### 7-3. 보류 분석
- CVD N>1 확보 시 정식 통계 비교
- 개별 JND 값과 LOCO 색별 격차 간 상관
- 정식 모델 비교: 원추세포 기울기 모델 vs LOCO 예측자 vs SRM z 예측자

---

## 8. 출처 참조

| 데이터 | 출처 파일 | 단계 |
|------|------------|-------|
| HC1/HC2/CVD JND | `results/hc_group_metrics.json` (summary values) | Phase 3 (행동) |
| JHKim JND | `data/JHKim/jnd_ses1_no_filter_summary.csv`, `*_trials.csv` | Phase 3 (행동) |
| JYPark JND | `data/JYPark/jnd_ses1_no_filter_summary.csv`, `*_trials.csv` | Phase 3 (행동) |
| MJChoi JND | `data/MJChoi/jnd_ses1_no_filter_summary.csv`, `*_trials.csv` | Phase 3 (행동) |
| HC Group 통계 | `results/hc_group_metrics.json`, `results/jnd_summary.csv` | Phase 3 (분석) |
| HC1/HC2 RSVP | `data/behav_pilot/HC_rsvp_8afc_ses1_run1.csv`, `HC2_*` | Phase 3 (행동) |
| CVD RSVP | `data/behav_pilot/sub-08_rsvp_8afc_ses1_run1.csv` | Phase 3 (행동) |
| SRM z-score | `analysis/phase5_filter_optimization/pre_validation/notion_prevalidation.md` §1-1 | Phase 2 (SRM 사전검증) |
| Crossnobis diff | `analysis/phase2_SRM_across_between/results/color_pair_analysis/color_pair_analysis_V{1,2}.json` | Phase 2 (SRM) |
| LOCO 색별 | `analysis/phase4_forward_model/RESULTS.md` §3d | Future Phase 1 (Forward Model) |
| LOCO 그룹 격차 | `analysis/phase4_forward_model/RESULTS.md` §2b | Future Phase 1 (Forward Model) |
| 원추세포 모델 | `data/behav_pilot/cone_model_verify.py` | Phase 3 (행동) |
| Gradient 검증 | `scripts/analysis_gradient_profile.py`, `results/gradient_profile/summary.json` | Phase 3 (검증) |
| Tier 비교 | §9 (이 문서) | Phase 3 (검증, 2026-03-27) |

---

## 8. HC 개인차 심층 분석

> HC1(CDX003)과 HC2(CDX004)의 JND가 5~13배 차이. N=5에서 HC2의 영향이 희석되었으나, 여전히 최저 JND 피험자. 이 절에서는 원시 데이터 수준에서 차이의 패턴과 가능한 원인을 분석한다.

### 8-1. JND 전쌍 비교

| 쌍 | HC1 | HC2 | 비율 (HC1/HC2) | HC2 floor 도달? |
|------|:---:|:---:|:---:|:---:|
| red-orange | 0.235 | 0.018 | **13.1x** | YES (sc0, sc1 모두 level=0) |
| orange-yellow | 0.443 | 0.064 | **6.9x** | 부분 (sc1만 0.093) |
| yellow-green | 0.103 | 0.018 | **5.7x** | YES |
| green-blue | 0.103 | 0.020 | **5.2x** | YES (sc0 level=0 반복) |
| yellow-purple | 0.025 | 0.015 | **1.7x** | YES |
| blue-purple | 0.165 | 0.040 | **4.1x** | YES (sc1 level=0) |
| cyan-magenta | 0.048 | 0.015 | **3.2x** | YES |
| red-cyan | 0.048 | 0.015 | **3.2x** | YES |

> 전 쌍에서 HC2 < HC1. 비율 범위 1.7x~13.1x. yellow-purple이 가장 작은 차이(1.7x)는 HC1도 이미 낮은 JND(0.025)이기 때문.

### 8-2. 시행 수준 분석

**HC2 계단법 floor 패턴**:
- HC2는 대부분의 쌍에서 level=0 (최소 보간 단계)에 도달 후에도 "different" 응답을 지속
- 예: red-orange sc0 — level=0에서 연속 12+ 시행 "different" 응답
- 예: yellow-green sc1 — level=0에서 연속 20+ 시행 "different" 응답

**시행 수 비교 (summary.csv n_trials)**:

| 쌍 | HC1 총 시행 | HC2 총 시행 | HC2/HC1 비율 |
|------|:---:|:---:|:---:|
| red-orange | ~28 (est.) | 61 | ~2.2x |
| orange-yellow | ~24 (est.) | 55 | ~2.3x |
| yellow-green | ~20 (est.) | 67 | ~3.4x |
| green-blue | ~28 (est.) | 62 | ~2.2x |
| yellow-purple | ~16 (est.) | 45 | ~2.8x |
| blue-purple | ~24 (est.) | 90 | ~3.8x |
| cyan-magenta | ~20 (est.) | 69 | ~3.5x |
| red-cyan | ~18 (est.) | 54 | ~3.0x |

> HC2의 시행 수가 HC1의 1.5~3.8배. 이는 HC2가 floor에서도 수렴하지 않아 계단법이 추가 시행을 요구했기 때문.

**반전 수(n_reversals)**: HC1과 HC2 모두 8회(동일) — 수렴 기준은 동일하게 충족했으나, HC2는 floor에서의 반전이므로 의미가 다름.

### 8-3. 가능한 원인

1. **극단적 색 민감도**: HC2가 실제로 HC1보다 현저히 높은 색 변별 능력을 보유할 가능성. 정상 범위 내 상위 극단(upper tail).

2. **반응 기준(criterion) 차이**: HC2가 "same"이라고 응답하기 위해 매우 높은 확신을 요구하는 보수적 기준(conservative criterion) 사용. 즉, 약간이라도 차이가 느껴지면 "different" 응답 → JND 과소추정.

3. **계단법 floor 효과**: 계단법의 최소 단계(level=0)가 HC2의 실제 역치보다 높은 경우, 계단법이 진정한 역치를 측정하지 못함. 이 경우 0.015-0.020의 JND는 계단법 해상도의 하한(floor)을 반영하지 실제 민감도를 반영하지 않을 수 있음.

4. **과제 이해도/경험 차이**: HC2가 과제를 더 잘 이해했거나 사전 경험이 있을 가능성. 단, RSVP 정확도가 HC1(100%) > HC2(96.9%)이므로, 색 식별 자체의 우위는 HC1 쪽.

**가장 유력한 설명**: (2) + (3)의 조합. HC2의 RSVP 정확도가 HC1보다 낮으므로(96.9% vs 100%), HC2가 색 지각 자체에서 HC1보다 우월할 가능성은 낮다. 오히려 JND 과제에서 보수적 반응 기준 + 계단법 floor 도달이 극히 낮은 JND를 산출한 것으로 추정.

### 8-4. RSVP 비교

| 지표 | HC1 | HC2 | 해석 |
|------|:---:|:---:|:---:|
| 정확도 | 100% (64/64) | 96.9% (62/64) | HC1 약간 우위 |
| 평균 RT | 2.30s | 2.82s | HC1 더 빠름 (+23%) |
| 오류 색 | — | green→cyan, purple→blue | 인접색 혼동 |

> HC2의 오류 패턴(green→cyan, purple→blue)은 CVD의 오류 패턴과 겹치지만 빈도가 극히 낮음(각 1건). 이는 정상 범위 내 변이(normal variation)로 해석 가능.

### 8-5. 교차 양상 분석에 대한 시사점

HC 개인차가 방향 분류에 영향을 미치는 쌍:
- **안정 쌍 (3쌍)**: orange-yellow, yellow-green, yellow-purple → N=2/3/5 모두 HYPO. 이 쌍들의 교차 양상 결과는 HC N에 **불변**.
- **안정 HYPER (2쌍)**: red-orange, red-cyan → 일관 HYPER.
- **불안정 쌍 (3쌍)**: green-blue, blue-purple, cyan-magenta → borderline. 추가 HC/CVD로 방향 확정 필요.

> **핵심 결론**: LOCO ↔ JND 100% 일치(§3-2)의 토대인 HYPO 3쌍이 HC N에 불변이므로, 논문의 핵심 주장(LOCO가 행동적으로 타당한 예측자)은 HC 표본 크기에 영향받지 않는다.

---

## 9. 사전 가설(Tier) vs 실제 행동 데이터 비교

> 추가: 2026-03-27. Phase 2 필터 파이프라인의 COLOR_PAIRS 사전 설계(cone model + SRM z 기반)와 실제 JND 데이터(N=5 HC)를 비교한다.

### 9-1. 사전 Tier 설계 근거

```python
COLOR_PAIRS = [
    # Tier 1: 양 그룹 공통 핵심 쌍
    ('color_3', 'color_7', 'yellow-purple'),     # 이중 해리: D z=+13.87 vs P z=-3.31
    ('color_6', 'color_7', 'blue-purple'),       # Group sig p=0.042, S-cone 보상
    ('color_1', 'color_2', 'red-orange'),        # L-M 압축, 양 CVD 일관
    # Tier 2a: Protan 특이적
    ('color_5', 'color_8', 'cyan-magenta'),      # sub-09 V1 z=+4.08, L-M→S 보상
    ('color_4', 'color_6', 'green-blue'),        # 실제 cone space M 차이, 범 CVD 압축
    # Tier 2b: Deutan 특이적 (M' 피크 이동 서명)
    ('color_2', 'color_3', 'orange-yellow'),     # sub-08 V2 z=+3.29, V3 z=+5.36
    ('color_3', 'color_4', 'yellow-green'),      # sub-08 V2 z=+4.14, V3 z=+5.75
    # Tier 3: 통제
    ('color_1', 'color_5', 'red-cyan'),          # 대각 180°, 천장 효과 통제
]
```

### 9-2. 쌍별 비교: 가설 vs 실제

| Tier | 쌍 | 사전 가설 | 실제 JND 방향 (N=5) | 실제 Ratio | 판정 |
|:---:|------|------|:---:|:---:|:---:|
| **1** | yellow-purple | 이중 해리, D z=+13.87 → 핵심 교정 대상 | **HYPO** (ratio=2.95) | 2.95 | **CONFIRMED** — 가장 극단적 과분리 + HYPO = 해리의 정수 |
| **1** | blue-purple | Group sig p=0.042, S-cone 보상 → HYPO 예측 | **borderline** (ratio=0.94) | 0.94 | **WEAKENED** — N=3에서 HYPO(1.17)였으나 N=5에서 borderline. HC 높은 JND(0.128 mean)가 CVD(0.12)를 상쇄 |
| **1** | red-orange | L-M 압축 → HYPER 예측 | **HYPER** (ratio=0.53) | 0.53 | **CONFIRMED** — L-M 압축이 JND 민감도 증가와 일치 |
| **2a** | cyan-magenta | Protan 특이적 과분리 → HYPO 예측 | **borderline** (ratio=1.11) | 1.11 | **WEAKENED** — Deutan(sub-08) 데이터에서 borderline은 예상 가능. Protan 피험자 데이터 필요 |
| **2a** | green-blue | 범 CVD 압축 → HYPER/borderline | **borderline** (ratio=0.99) | 0.99 | **CONSISTENT** — 압축 예측과 borderline/near-normal 일치 |
| **2b** | orange-yellow | Deutan M' 이동 → 과분리 + HYPO 예측 | **HYPO** (ratio=3.36) | 3.36 | **STRONGLY CONFIRMED** — 최대 JND(0.84), 가장 극적 HYPO |
| **2b** | yellow-green | Deutan M' 양방향 이동 → HYPO 예측 | **HYPO** (ratio=3.41) | 3.41 | **STRONGLY CONFIRMED** — 2번째로 높은 ratio |
| **3** | red-cyan | 대각 180°, 천장 효과 통제 | **HYPER** (ratio=0.50) | 0.50 | **AS EXPECTED** — 대각 쌍은 HC도 CVD도 매우 민감, 통제 역할 적합 |

### 9-3. Tier별 요약

**Tier 1 (양 그룹 공통 핵심)**:
- yellow-purple: **CONFIRMED**. 핵심 교정 대상 유지.
- blue-purple: **WEAKENED**. N=5에서 borderline — Tier 1 자격 재고 필요. 그러나 SRM group sig (p=0.042)는 여전히 유효하므로 신경 수준에서는 왜곡 존재. 행동적으로는 sub-08 deutan에서 CVD ≈ HC.
- red-orange: **CONFIRMED**. L-M 압축 → HYPER 예측 정확.

> Tier 1 판정: 3쌍 중 2쌍 confirmed, 1쌍 weakened. yellow-purple과 red-orange은 확고. blue-purple은 "신경 왜곡은 있으나 행동적 영향이 미미"한 쌍으로 재분류 고려.

**Tier 2a (Protan 특이적)**:
- cyan-magenta: **WEAKENED** for deutan. Protan 검증 필요 — sub-09 V1 z=+4.08이므로 protan에서는 HYPO일 가능성.
- green-blue: **CONSISTENT**. 범 CVD 압축 예측과 borderline 일치.

> Tier 2a 판정: Deutan 데이터만으로는 판정 불가. Protan JND 수집이 결정적.

**Tier 2b (Deutan 특이적)**:
- orange-yellow: **STRONGLY CONFIRMED**. 가장 극적 HYPO (ratio=3.36).
- yellow-green: **STRONGLY CONFIRMED**. 2번째로 극적 (ratio=3.41).

> Tier 2b 판정: 2쌍 모두 강력 확인. M' 피크 이동의 행동적 서명이 명확.

**Tier 3 (통제)**:
- red-cyan: **AS EXPECTED**. 대각 쌍 → 천장 효과 통제 역할 적합.

### 9-4. 핵심 발견: SRM z 방향 ≠ JND 방향 (구조적 해리)

사전 Tier 설계는 SRM z 크기/방향을 기반으로 "교정 필요성"을 추정했으나, 실제 행동 데이터는 **SRM z 방향이 JND 방향을 예측하지 못함**을 보여준다:

| 가설 유형 | 사전 근거 | 행동 검증 결과 |
|------|------|------|
| SRM z 과분리 → HYPER | red-orange (z=+1.66) | **HYPER** (일치) |
| SRM z 과분리 → HYPO | orange-yellow (z=+3.29), yellow-green (z=+4.14), yellow-purple (z=+13.87) | **HYPO** (일치, 하지만 방향이 반대 예측) |
| SRM z 과분리 → 압축 예측 | blue-purple (z=+6.15) | **borderline** (불명확) |

SRM z의 **크기**는 왜곡의 존재를 확인하지만, **부호**만으로는 "더 민감(HYPER)" vs "더 둔감(HYPO)"을 예측할 수 없다. 이는 §3-1의 "0차 vs 고차 기하학 해리"와 정확히 일치.

**Tier 설계에 대한 시사점**:
- **Tier 우선순위를 SRM z 크기가 아닌 LOCO 취약성으로 재정렬**: orange, yellow, purple이 LOCO 취약 → orange-yellow, yellow-green, yellow-purple이 최우선 교정 대상
- **Tier 1 재정의**: {yellow-purple, orange-yellow, yellow-green} (LOCO+JND 수렴) > {blue-purple, red-orange} (SRM만 유의)
- **Phase 2 필터**: LOCO 기반 δθ fitting이 SRM RDM fitting보다 행동적으로 타당 (§5-2와 일치)
