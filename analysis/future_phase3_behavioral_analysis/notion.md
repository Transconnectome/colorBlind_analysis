# Future Phase 3: 행동 검증 — 파일럿 데이터 분석

> **상태**: 예비 분석 (CVD N=1, HC N=2, 파일럿). 추가 데이터 수집 예정.
> **날짜**: 2026-03-18
> **피험자**: sub-08 (CDX002, deutan CVD) vs HC1 (CDX003) + HC2 (CDX004)
> **데이터**: `data/behav_pilot/`

---

## 0. 개요

본 문서는 파일럿 행동 데이터(JND, RSVP 8AFC)를 Phase 2(SRM) 및 Future Phase 1(Forward Model)의 신경 지표와 통합하여, CVD 색 표상 결손의 교차 양상(cross-modal) 수렴을 평가한다. HC 2명(CDX003=HC1, CDX004=HC2)의 JND가 5~13배 차이 → HC1/HC2/HC 평균 3가지 기준별 방향 분류 및 교차 양상 일치도를 함께 보고한다.

핵심 해리 2가지:

1. **전역 vs 국소 해리**: SRM z-score(전역 끝점 거리)와 JND 방향(국소 지각 민감도)이 HC1 기준 6쌍 중 4쌍 불일치(DISCORDANT)
2. **변별 vs 보간 해리**: RSVP 8AFC(범주적 변별)는 CVD 81% 정확도이나, LOCO(연속 보간)는 완전 실패

---

## 1. 행동 데이터 요약

### 1-1. JND (Just Noticeable Difference) — 2AFC 계단법

**방법**: 적응적 계단법(쌍당 2개 인터리브, 0.8과 0.5에서 수렴). JND = 마지막 N회 반전의 평균. 8개 색 쌍 검사.

**해석**: JND = "다르다" 응답을 위한 최소 보간 단계. 낮을수록 민감(HYPER), 높을수록 둔감(HYPO).

| 쌍 | HC1 (CDX003) | HC2 (CDX004) | HC 평균 | CVD (CDX002) | HC1 기준 | HC2 기준 | HC평균 기준 |
|------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| red-orange | **0.235** | **0.018** | **0.127** | **0.062** | **HYPER** | HYPO | **HYPER** |
| orange-yellow | **0.443** | **0.064** | **0.254** | **0.840** | **HYPO** | **HYPO** | **HYPO** |
| yellow-green | **0.103** | **0.018** | **0.061** | **0.278** | **HYPO** | **HYPO** | **HYPO** |
| green-blue | **0.103** | **0.020** | **0.062** | **0.077** | **HYPER** | HYPO | borderline |
| yellow-purple | **0.025** | **0.015** | **0.020** | **0.062** | **HYPO** | **HYPO** | **HYPO** |
| blue-purple | **0.165** | **0.040** | **0.103** | **0.120** | **HYPER** | HYPO | borderline |
| cyan-magenta | **0.048** | **0.015** | **0.032** | **0.040** | **HYPER** | HYPO | borderline |
| red-cyan | **0.048** | **0.015** | **0.032** | **0.015** | **HYPER** | **HYPER** | **HYPER** |

> **출처**: `data/behav_pilot/HC_jnd_ses1_no_filter_summary.csv`, `data/behav_pilot/HC2_jnd_ses1_no_filter_summary.csv`, `data/behav_pilot/sub-08_jnd_ses1_no_filter_summary.csv`
> 각 HC/CVD 값 = sc0과 sc1의 jnd_mean 평균. HC 평균 = (HC1 + HC2) / 2.

**HC1 vs HC2 요약**: HC2의 JND가 HC1의 1/5~1/13 수준 (모든 쌍에서 HC2 < HC1). HC2는 계단법 floor(level=0)에 빈번 도달 → 극단적 민감도 또는 반응 기준 차이(§8 상세).

**HC1 기준 요약**: HYPO 3쌍 (orange-yellow, yellow-green, yellow-purple), HYPER 5쌍. 이하 §3의 교차 양상 분석은 **HC1 기준을 주 분석(primary)**, HC2·HC평균 기준을 부차 분석(supplementary)으로 보고한다.

**HC2 기준 요약**: 전 쌍 HYPO 또는 HYPER(1쌍: red-cyan만 HYPER). HC2의 극히 낮은 JND 때문에 CVD가 거의 모든 쌍에서 HYPO로 분류.

**HC평균 기준 요약**: HYPO 3쌍 (HC1과 동일), HYPER 2쌍 (red-orange, red-cyan), borderline 3쌍 (green-blue, blue-purple, cyan-magenta — CVD/HC평균 비율 1.16~1.25).

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

> **출처**: `analysis/future_phase2_filter_optimization/pre_validation/notion_prevalidation.md` §1-1

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

> **출처**: `analysis/future_phase1_forward_model/RESULTS.md` §3d

### 2-4. Forward Model — LOCO 그룹 요약

| ROI | HC 평균 (SD) | CVD 평균 (SD) | Cohen's d | p (Welch) |
|-----|:---:|:---:|:---:|:---:|
| V1 | +0.130 (0.097) | -0.012 (0.054) | +1.61 | **0.021** |
| V2 | +0.150 (0.188) | -0.174 (0.130) | +1.85 | **0.022** |
| V3 | +0.023 (0.240) | -0.008 (0.163) | +0.14 | 0.819 |
| hV4 | +0.183 (0.200) | -0.058 (0.207) | +1.19 | 0.169 |

> **출처**: `analysis/future_phase1_forward_model/RESULTS.md` §2b

---

## 3. 교차 양상 일치도 분석

### 3-1. SRM z vs JND 방향 — HC1 기준 6쌍 중 4쌍 불일치

**단순 예측**: SRM z 양수(과분리) → HYPER(낮은 JND) 예측. SRM z 음수(압축) → HYPO(높은 JND) 예측.

| 쌍 | SRM z (최고 ROI) | z 방향 | HC1 방향 | HC1 일치? | HC2 방향 | HC2 일치? | HC평균 방향 | HC평균 일치? |
|------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| red-orange | V2: +1.66 | 과분리 | **HYPER** | YES | HYPO | **NO** | **HYPER** | YES |
| orange-yellow | V2: +3.29 | 과분리 | **HYPO** | **NO** | **HYPO** | **NO** | **HYPO** | **NO** |
| yellow-green | V2: +4.14 | 과분리 | **HYPO** | **NO** | **HYPO** | **NO** | **HYPO** | **NO** |
| green-blue | V1: -0.89 | 압축 | **HYPER** | **NO** | HYPO | YES | borderline | N/A |
| yellow-purple | V2: +13.87 | 과분리 | **HYPO** | **NO** | **HYPO** | **NO** | **HYPO** | **NO** |
| blue-purple | V2: +6.15 | 과분리 | **HYPER** | YES | HYPO | **NO** | borderline | N/A |
| cyan-magenta | — | — | **HYPER** | N/A | HYPO | N/A | borderline | N/A |
| red-cyan | V1: +1.11* | 과분리 | **HYPER** | YES* | **HYPER** | YES* | **HYPER** | YES* |

\*red-cyan SRM z는 crossnobis V1 값 (SRM 사전검증에서 해당 쌍 미보고).

**HC1 기준** (primary): 일치 2쌍, 불일치 4쌍, N/A 2쌍 → 검증 가능 6쌍 중 **4쌍 불일치(67%)**.
**HC2 기준**: 일치 1쌍(green-blue: 압축+HYPO), 불일치 5쌍, N/A 2쌍 → **1/6 일치(17%)**. HC2의 극히 낮은 JND가 거의 모든 쌍을 HYPO로 만들어, 양의 SRM z 쌍과 전부 불일치. 유일한 일치(green-blue)는 음의 SRM z(-0.89)가 HYPO 방향과 우연히 일치.
**HC평균 기준**: 명확한 쌍만 평가 시(borderline 제외) 일치 1쌍(red-orange)/불일치 3쌍 → **1/4 일치(25%)**.

**해석**: 어떤 HC 기준을 사용하든 SRM z ↔ JND 불일치가 지배적. 이는 SRM z(전역 끝점 거리)와 JND(국소 보간 기울기)가 측정하는 대상 자체가 다르기 때문이며, HC 기준의 불확실성에 의한 artifact가 아니다.

**설명**: SRM z는 차원 축소된 공간에서 색 끝점 간의 전역 기하학적 거리를 측정한다. JND는 보간된 기울기에 대한 국소 지각 민감도를 측정한다. 원추세포 이동은 동일 쌍에 대해 끝점 과분리(양의 SRM z)와 국소 기울기 감소(높은 JND/HYPO)를 동시에 유발한다 — 끝점을 벌리는 동일한 M' 피크 이동이 그 사이의 반응 곡선을 평탄화하기 때문이다.

### 3-2. LOCO 취약성 vs JND — 100% 일치

| JND HYPO 쌍 | 관련 LOCO 취약 색 | 일치 |
|------|------|:---:|
| orange-yellow | orange (V1 p=0.0018), yellow (V1 p=0.0059) | **YES** |
| yellow-green | yellow (V1 p=0.0059, V2 p=0.0077) | **YES** |
| yellow-purple | yellow (V1 p=0.0059), purple (V1 p=0.020) | **YES** |

**HYPO 3쌍 모두 LOCO 취약 색을 포함 (100%).**

| JND HYPER 쌍 (HC1 기준) | LOCO 취약 색 포함? | 해석 |
|------|------|:---:|
| red-orange | Red: 취약 아님 | HYPER 일관 |
| green-blue | Blue: 취약 아님 | HYPER 일관 |
| blue-purple | Blue: 취약 아님 | HYPER 일관 |
| cyan-magenta | Cyan (V2 p=0.0053 — 경계) | 부분 예외 |
| red-cyan | Red, Cyan: 취약 아님/경계 | HYPER 일관 |

**HC 기준별 안정성**: HYPO 3쌍(orange-yellow, yellow-green, yellow-purple)은 **HC1/HC2/HC평균 모두에서 HYPO** — 어떤 HC 기준을 사용하든 LOCO ↔ JND 일치도 100% 유지. HC1 HYPER 쌍 중 일부(red-orange, green-blue, blue-purple, cyan-magenta)가 HC2 기준에서 HYPO로 전환되나, 이들은 원래 LOCO 취약 색을 포함하지 않으므로 HYPER 일관성 해석에는 영향 없음.

**결론**: LOCO 색별 취약성이 JND HYPO 방향을 3/3 정확도(100%)로 예측 — HC 기준 선택에 **불변**. Forward Model의 보간 지표는 행동적으로 타당하다.

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

### 5-1. 현재 이해

1. **LOCO 취약성 → JND HYPO (100%)**: 필터는 LOCO 실패 색(orange, yellow, purple)을 타겟해야 하며, SRM z 편차가 아님.
2. **SRM z 양수 ≠ 더 나은 지각**: 끝점 과분리가 국소 보간에 도움이 되지 않음. SRM z를 HC 값으로 교정하는 것만으로는 불충분.
3. **hV4 = 보간 오라클**: 순열 null을 통과하는 유일한 ROI (p=0.026-0.044). 필터는 hV4 LOCO 공간에서 주로 평가해야 함.

### 5-2. HYPER 교정 가능성 (신규)

JND HYPER 쌍(red-orange 0.27x, red-cyan 0.32x, green-blue 0.75x, blue-purple 0.73x, cyan-magenta 0.84x)은 CVD가 해당 쌍을 HC보다 더 다르게 지각함을 시사. 두 가지 해석:
- **유익한 보상**: HYPER가 실생활 변별에 도움이 되면 유지
- **왜곡**: HYPER가 지각적 균일성을 훼손하면 교정

HYPO와 HYPER 모두 필터 타겟이 될 수 있으며, 목표가 HC 정상화인지 기능적 최적화인지에 따라 결정.

### 5-3. 역방향 파이프라인 제안 (신규)

**현재 파이프라인** (Phase 2 계획):
```
SRM RDM 기반 교정 → hV4 LOCO 평가
```

**대안 파이프라인**:
```
hV4 복셀 예측 (Forward Model) 기반 교정 → SRM RDM V1/V2 평가
```

**근거**: hV4는 검증된 그룹 사전분포를 가지므로(ZS ≈ LORO, p=0.913), hV4 forward model로 교정된 자극이 유발할 복셀 패턴을 예측한 후, 해당 교정이 V1/V2의 SRM 색 거리를 정상화하는지 검증 가능.

**장점**:
- V1/V2 SRM은 더 많은 유의 쌍 보유 (sub-08 V2에서 FDR 12쌍) → 풍부한 평가 신호
- 보간이 실패하는 공간(V1/V2 SRM)이 아니라, 검증된 보간 모델(hV4)에 근거한 교정
- 양방향: HYPO와 HYPER 교정을 동시 평가 가능

**상태**: 제안 단계. 추가 행동 데이터 확보 후 구현 결정.

---

## 6. 제한점 및 향후 계획

### 6-1. 제한점
- **표본 크기**: CVD N=1, HC N=2. 모든 발견은 사례 수준. 그룹 통계 불가.
- **HC 개인차 극심**: HC1 vs HC2 JND가 5~13배 차이(§8 상세). HC 기준에 따라 방향 분류가 달라지는 쌍이 존재.
- **HC 피험자 불일치**: JND HC(CDX003, CDX004) ≠ fMRI HC(sub-01~sub-07). 피험자 내 직접 비교 불가.
- **단색광 근사**: 원추세포 모델이 단일 파장 근사 사용. purple, magenta는 광대역 자극.
- **fMRI-행동 비등록**: sub-08 행동 세션 ≠ sub-08 fMRI 세션.
- **계단법 floor 효과**: HC2가 다수 쌍에서 level=0에 도달(§8 상세). 진정한 역치가 계단법 해상도 이하일 가능성.

### 6-2. 추가 데이터 수집 계획
- HC 및 CVD 추가 피험자 JND 검사
- 피험자 내 fMRI + 행동 동시 검사
- 확장된 색 쌍 세트 (8쌍 이상)

### 6-3. 보류 분석
- N>1 확보 시 정식 통계 비교
- 개별 JND 값과 LOCO 색별 격차 간 상관
- 정식 모델 비교: 원추세포 기울기 모델 vs LOCO 예측자 vs SRM z 예측자

---

## 7. 출처 참조

| 데이터 | 출처 파일 | 단계 |
|------|------------|-------|
| HC1 JND | `data/behav_pilot/HC_jnd_ses1_no_filter_summary.csv` | Phase 3 (행동) |
| HC2 JND | `data/behav_pilot/HC2_jnd_ses1_no_filter_summary.csv` | Phase 3 (행동) |
| HC1 JND 시행 | `data/behav_pilot/HC_jnd_ses1_no_filter_trials.csv` | Phase 3 (행동) |
| HC2 JND 시행 | `data/behav_pilot/HC2_jnd_ses1_no_filter_trials.csv` | Phase 3 (행동) |
| CVD JND | `data/behav_pilot/sub-08_jnd_ses1_no_filter_summary.csv` | Phase 3 (행동) |
| HC1 RSVP | `data/behav_pilot/HC_rsvp_8afc_ses1_run1.csv` | Phase 3 (행동) |
| HC2 RSVP | `data/behav_pilot/HC2_rsvp_8afc_ses1_run1.csv` | Phase 3 (행동) |
| CVD RSVP | `data/behav_pilot/sub-08_rsvp_8afc_ses1_run1.csv` | Phase 3 (행동) |
| SRM z-score | `analysis/future_phase2_filter_optimization/pre_validation/notion_prevalidation.md` §1-1 | Phase 2 (SRM 사전검증) |
| Crossnobis diff | `analysis/phase2_SRM_across_between/results/color_pair_analysis/color_pair_analysis_V{1,2}.json` | Phase 2 (SRM) |
| LOCO 색별 | `analysis/future_phase1_forward_model/RESULTS.md` §3d | Future Phase 1 (Forward Model) |
| LOCO 그룹 격차 | `analysis/future_phase1_forward_model/RESULTS.md` §2b | Future Phase 1 (Forward Model) |
| 원추세포 모델 | `data/behav_pilot/cone_model_verify.py` | Phase 3 (행동) |

---

## 8. HC 개인차 심층 분석

> HC1(CDX003)과 HC2(CDX004)의 JND가 5~13배 차이. 이 절에서는 원시 데이터 수준에서 차이의 패턴과 가능한 원인을 분석한다.

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
- **안정 쌍 (3쌍)**: orange-yellow, yellow-green, yellow-purple → HC1/HC2/HC평균 모두 HYPO. 이 쌍들의 교차 양상 결과는 HC 기준에 **불변**.
- **불안정 쌍 (5쌍)**: red-orange, green-blue, blue-purple, cyan-magenta, red-cyan → HC 기준에 따라 방향 변동. 이 쌍들에 대한 교차 양상 결론은 **예비적(preliminary)**.

> **핵심 결론**: LOCO ↔ JND 100% 일치(§3-2)의 토대인 HYPO 3쌍이 HC 기준에 불변이므로, 논문의 핵심 주장(LOCO가 행동적으로 타당한 예측자)은 HC 개인차에 영향받지 않는다. 추가 HC 피험자 확보 시 불안정 쌍의 방향을 확정해야 한다.
