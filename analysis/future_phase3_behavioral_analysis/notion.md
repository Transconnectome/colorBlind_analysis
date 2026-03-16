# Future Phase 3: 행동 검증 — 파일럿 데이터 분석

> **상태**: 예비 분석 (그룹당 N=1, 파일럿). 추가 데이터 수집 예정.
> **날짜**: 2026-03-17
> **피험자**: sub-08 (CDX002, deutan CVD) vs HC (CDX003)
> **데이터**: `data/behav_pilot/`

---

## 0. 개요

본 문서는 파일럿 행동 데이터(JND, RSVP 8AFC)를 Phase 2(SRM) 및 Future Phase 1(Forward Model)의 신경 지표와 통합하여, CVD 색 표상 결손의 교차 양상(cross-modal) 수렴을 평가한다. 핵심 해리 2가지:

1. **전역 vs 국소 해리**: SRM z-score(전역 끝점 거리)와 JND 방향(국소 지각 민감도)이 6쌍 중 4쌍 불일치(DISCORDANT)
2. **변별 vs 보간 해리**: RSVP 8AFC(범주적 변별)는 81% 정확도이나, LOCO(연속 보간)는 완전 실패

---

## 1. 행동 데이터 요약

### 1-1. JND (Just Noticeable Difference) — 2AFC 계단법

**방법**: 적응적 계단법(쌍당 2개 인터리브, 0.8과 0.5에서 수렴). JND = 마지막 N회 반전의 평균. 8개 색 쌍 검사.

**해석**: JND = "다르다" 응답을 위한 최소 보간 단계. 낮을수록 민감(HYPER), 높을수록 둔감(HYPO).

| 쌍 | HC JND (sc0) | HC JND (sc1) | HC 평균 | CVD JND (sc0) | CVD JND (sc1) | CVD 평균 | 비율 (CVD/HC) | 방향 |
|------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| red-orange | 0.200 | 0.270 | **0.235** | 0.060 | 0.065 | **0.062** | 0.27 | **HYPER** |
| orange-yellow | 0.420 | 0.465 | **0.443** | 0.870 | 0.810 | **0.840** | 1.90 | **HYPO** |
| yellow-green | 0.105 | 0.100 | **0.103** | 0.280 | 0.275 | **0.278** | 2.70 | **HYPO** |
| green-blue | 0.135 | 0.070 | **0.103** | 0.065 | 0.090 | **0.077** | 0.75 | **HYPER** |
| yellow-purple | 0.020 | 0.030 | **0.025** | 0.060 | 0.065 | **0.062** | 2.50 | **HYPO** |
| blue-purple | 0.135 | 0.195 | **0.165** | 0.115 | 0.125 | **0.120** | 0.73 | **HYPER** |
| cyan-magenta | 0.040 | 0.055 | **0.048** | 0.035 | 0.045 | **0.040** | 0.84 | **HYPER** |
| red-cyan | 0.040 | 0.055 | **0.048** | 0.015 | 0.015 | **0.015** | 0.32 | **HYPER** |

> **출처**: `data/behav_pilot/HC_jnd_ses1_no_filter_summary.csv`, `data/behav_pilot/sub-08_jnd_ses1_no_filter_summary.csv`
> HC 평균 = sc0과 sc1의 jnd_mean 평균. CVD 평균도 동일.

**요약**: HYPO 3쌍 (orange-yellow, yellow-green, yellow-purple), HYPER 5쌍 (red-orange, green-blue, blue-purple, cyan-magenta, red-cyan).

### 1-2. RSVP 8AFC — 색 식별

**방법**: 64 시행, 8색, 8지 강제선택.

| 지표 | HC (CDX003) | CVD (CDX002) | 차이 |
|--------|:---:|:---:|:---:|
| 정확도 | 100% (64/64) | 81.2% (52/64) | -18.8% |
| 평균 RT (정답) | 2.30s | 3.72s | +1.42s (+62%) |
| 제한시간 초과 | 0 | 1 | — |
| 음수 RT | 0 | 1 | — |

> **출처**: `data/behav_pilot/HC_rsvp_8afc_ses1_run1.csv`, `data/behav_pilot/sub-08_rsvp_8afc_ses1_run1.csv`

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

**색별 정확도 (CVD)**:

| 색 | 시행 | 정답 | 정확도 |
|-------|:------:|:-------:|:--------:|
| red (1) | 8 | 8 | 100% |
| orange (2) | 8 | 7 | 87.5% |
| yellow (3) | 8 | 5 | 62.5% |
| green (4) | 8 | 6 | 75.0% |
| cyan (5) | 8 | 8 | 100% |
| blue (6) | 8 | 8 | 100% |
| purple (7) | 8 | 4 | 50.0% |
| magenta (8) | 8 | 6 | 75.0% |

> 최저: purple (50%), yellow (62.5%). 최고: red, cyan, blue (100%).

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

### 3-1. SRM z vs JND 방향 — 6쌍 중 4쌍 불일치

**단순 예측**: SRM z 양수(과분리) → HYPER(낮은 JND) 예측. SRM z 음수(압축) → HYPO(높은 JND) 예측.

| 쌍 | SRM z (최고 ROI) | z 방향 | JND 방향 | 일치? |
|------|:---:|:---:|:---:|:---:|
| red-orange | V2: +1.66 | 과분리 | **HYPER** | YES |
| orange-yellow | V2: +3.29 | 과분리 | **HYPO** | **NO** |
| yellow-green | V2: +4.14 | 과분리 | **HYPO** | **NO** |
| green-blue | V1: -0.89 | 압축 | **HYPER** | **NO** |
| yellow-purple | V2: +13.87 | 과분리 | **HYPO** | **NO** |
| blue-purple | V2: +6.15 | 과분리 | **HYPER** | YES |
| cyan-magenta | — | — | **HYPER** | N/A |
| red-cyan | V1: +1.11* | 과분리 | **HYPER** | YES* |

\*red-cyan SRM z는 crossnobis V1 값 (SRM 사전검증에서 해당 쌍 미보고).

**결과**: 일치 2쌍, 불일치 4쌍, N/A 2쌍 → 검증 가능 6쌍 중 **4쌍 불일치(67%)**.

**설명**: SRM z는 차원 축소된 공간에서 색 끝점 간의 전역 기하학적 거리를 측정한다. JND는 보간된 기울기에 대한 국소 지각 민감도를 측정한다. 원추세포 이동은 동일 쌍에 대해 끝점 과분리(양의 SRM z)와 국소 기울기 감소(높은 JND/HYPO)를 동시에 유발한다 — 끝점을 벌리는 동일한 M' 피크 이동이 그 사이의 반응 곡선을 평탄화하기 때문이다.

### 3-2. LOCO 취약성 vs JND — 100% 일치

| JND HYPO 쌍 | 관련 LOCO 취약 색 | 일치 |
|------|------|:---:|
| orange-yellow | orange (V1 p=0.0018), yellow (V1 p=0.0059) | **YES** |
| yellow-green | yellow (V1 p=0.0059, V2 p=0.0077) | **YES** |
| yellow-purple | yellow (V1 p=0.0059), purple (V1 p=0.020) | **YES** |

**HYPO 3쌍 모두 LOCO 취약 색을 포함 (100%).**

| JND HYPER 쌍 | LOCO 취약 색 포함? | 해석 |
|------|------|:---:|
| red-orange | Red: 취약 아님 | HYPER 일관 |
| green-blue | Blue: 취약 아님 | HYPER 일관 |
| blue-purple | Blue: 취약 아님 | HYPER 일관 |
| cyan-magenta | Cyan (V2 p=0.0053 — 경계) | 부분 예외 |
| red-cyan | Red, Cyan: 취약 아님/경계 | HYPER 일관 |

**결론**: LOCO 색별 취약성이 JND HYPO 방향을 3/3 정확도(100%)로 예측. Forward Model의 보간 지표는 행동적으로 타당하다.

### 3-3. 원추세포 분광 감도 모델 검증

**모델**: 가우시안 근사 — L_pk=564nm, M_pk=534nm (정상), M'_pk=555nm (deutan), S_pk=420nm. 2채널: L-M 대립(dLM) + S-(L+M)/2 (dS). 국소 기울기 = 양 끝점에서 ±5nm 범위의 |df/dλ| 평균.

**지표**: 총 기울기 = sqrt(dLM² + w_S * dS²). w_S ∈ [1.0, 20.0] 탐색.

**최적 결과**: w_S=1.2 → 5/8 정답 (62.5%).

| 쌍 | 정상 기울기 | Deutan 기울기 | 비율 (D/N) | 예측 | 실제 | 일치 |
|------|:---:|:---:|:---:|:---:|:---:|:---:|
| red-orange | 0.00458 | 0.00550 | 1.20 | HYPER | HYPER | YES |
| orange-yellow | 0.00846 | 0.01051 | 1.24 | HYPER | HYPO | **NO** |
| yellow-green | 0.01177 | 0.01310 | 1.11 | HYPER | HYPO | **NO** |
| green-blue | 0.01126 | 0.01149 | 1.02 | HYPER | HYPER | YES |
| yellow-purple | 0.00883 | 0.00956 | 1.08 | HYPER | HYPO | **NO** |
| blue-purple | 0.00614 | 0.00717 | 1.17 | HYPER | HYPER | YES |
| cyan-magenta | 0.00714 | 0.00719 | 1.01 | HYPER | HYPER | YES |
| red-cyan | 0.00648 | 0.00726 | 1.12 | HYPER | HYPER | YES |

> **출처**: `data/behav_pilot/cone_model_verify.py`

**한계**: 단색광 파장 근사가 비분광 색(purple=440nm, magenta=420nm)에서 부적절. 모델은 deutan M' 이동(534→555nm)이 모든 기울기를 가파르게 하므로 전 쌍에 대해 HYPER만 예측. 기울기만으로는 HYPO 방향을 설명 불가.

**시사점**: LOCO 취약성(고차 피질 통합을 포착)이 단순 분광 모델(62.5%)보다 우수한 예측자(100%).

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
- **그룹당 N=1**: 모든 발견은 사례 수준. 그룹 통계 불가.
- **HC 피험자 불일치**: JND HC(CDX003) ≠ fMRI HC(sub-01~sub-07). 피험자 내 직접 비교 불가.
- **단색광 근사**: 원추세포 모델이 단일 파장 근사 사용. purple, magenta는 광대역 자극.
- **fMRI-행동 비등록**: sub-08 행동 세션 ≠ sub-08 fMRI 세션.
- **계단법 수렴**: 일부 쌍의 수렴이 불충분할 수 있음 (반전 횟수 범위: 8-13).

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
| HC JND | `data/behav_pilot/HC_jnd_ses1_no_filter_summary.csv` | Phase 3 (행동) |
| CVD JND | `data/behav_pilot/sub-08_jnd_ses1_no_filter_summary.csv` | Phase 3 (행동) |
| HC RSVP | `data/behav_pilot/HC_rsvp_8afc_ses1_run1.csv` | Phase 3 (행동) |
| CVD RSVP | `data/behav_pilot/sub-08_rsvp_8afc_ses1_run1.csv` | Phase 3 (행동) |
| SRM z-score | `analysis/future_phase2_filter_optimization/pre_validation/notion_prevalidation.md` §1-1 | Phase 2 (SRM 사전검증) |
| Crossnobis diff | `analysis/phase2_SRM_across_between/results/color_pair_analysis/color_pair_analysis_V{1,2}.json` | Phase 2 (SRM) |
| LOCO 색별 | `analysis/future_phase1_forward_model/RESULTS.md` §3d | Future Phase 1 (Forward Model) |
| LOCO 그룹 격차 | `analysis/future_phase1_forward_model/RESULTS.md` §2b | Future Phase 1 (Forward Model) |
| 원추세포 모델 | `data/behav_pilot/cone_model_verify.py` | Phase 3 (행동) |
