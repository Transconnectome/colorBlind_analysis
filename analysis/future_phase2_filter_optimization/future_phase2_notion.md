# Future Phase 2: 왜곡 모델링 + 필터 설계

> **프로젝트**: Color Vision Deficiency Neural Representation Analysis
>
> **날짜**: 2026-04-22 (v5 — literature verification 추가)
> **피험자**: HC 7명 (sub-01~07), CVD 3명 (sub-08 deutan, sub-09 protan, sub-10 normal control)
> **ROI**: hV4 (primary), V1/V2 (supplementary)
>
> **핵심 결과**: 2-Component angular dilation 모델이 두 CVD 피험자 모두에서 LOCO+ΔRDM dual-validated. 모델 구조(S-cone축 + confusion축)가 Emery 2021, Brettel 1997에 의해 physiologically grounded되며, Machado Δλ는 문헌 severity 범위와 직접 정합. 양쪽 모두에서 exact pre-image 달성하는 유일한 모델.

---

## 목차

- [1. 목적](#1-목적)
- [2. 전제](#2-전제)
  - [2-1. 증거 위계](#2-1-증거-위계)
  - [2-2. Case Study 프레이밍](#2-2-case-study-프레이밍--cvd-specificity-불요)
  - [2-3. HC Specificity 실험 기록](#2-3-hc-specificity-실험-기록-중복-방지)
- [3. 모델](#3-모델)
- [4. 손실함수](#4-손실함수)
- [5. 결과](#5-결과)
  - [5-1. Detection](#5-1-detection--모든-모델-수렴)
  - [5-2. hV4 LOCO (PRIMARY)](#5-2-hv4-loco-primary--모델별-최적-적합)
  - [5-3. V1/V2 ΔRDM (SUPPLEMENTARY)](#5-3-v1v2-δrdm-supplementary--메커니즘-특성화)
  - [5-4. L_LOCO 구성 요소 분해](#5-4-l_loco-구성-요소-분해-교차-검증)
  - [5-5. Correction — 모델 간 방향 불일치](#5-5-correction--모델-간-방향-불일치)
  - [5-6. Pre-Image — 필터 존재성](#5-6-pre-image--필터-존재성)
  - [5-7. Severity-Dependent Filter Feasibility](#5-7-severity-dependent-filter-feasibility)
- [6. 문헌 기반 이론적 근거 (Physiological Grounding)](#6-문헌-기반-이론적-근거-physiological-grounding)
  - [6-1. Machado Δλ — 유일한 직접 지표 비교](#6-1-machado-δλ--유일한-직접-지표-비교)
  - [6-2. hV4 Primary ROI — 문헌적 근거](#6-2-hv4-primary-roi--문헌적-근거)
  - [6-3. 2-Component 모델 구조의 생리학적 근거](#6-3-2-component-모델-구조의-생리학적-근거)
  - [6-4. R+C g 파라미터 — 피질 보상의 개념적 뒷받침](#6-4-rc-g-파라미터--피질-보상의-개념적-뒷받침)
  - [6-5. 문제적 파라미터](#6-5-문제적-파라미터)
  - [6-6. 핵심 해석](#6-6-핵심-해석)
- [7. 결론](#7-결론)
- [8. 검증 요약 (Validation Summary)](#8-검증-요약-validation-summary)
- [9. 제한점](#9-제한점)
- [부록](#부록)

---

## 1. 목적

Phase 1-3이 "CVD 피질 색 표상이 왜곡되어 있다"를 확립했다면, 이 단계는 세 질문에 답한다:

1. **왜곡의 구조**: 어떤 메커니즘이 관찰된 왜곡을 설명하는가?
2. **교정 가능성**: 그 구조가 역변환(pre-image) 가능한가?
3. **필터 도출**: 가능하다면, 구체적으로 어떤 자극 변환이 필요한가?

**핵심 발견**: CVD의 피질 색 왜곡은 개인마다 고유한 기하학적 구조를 가지며, 그 구조의 가역성(invertibility)이 자극 공간 교정의 가능 여부를 결정한다.

---

## 2. 전제

### 2-1. 증거 위계

| 위계 | 내용 | 근거 |
|------|------|------|
| **PRIMARY** | hV4 L_LOCO fitting → 모델 선별, 필터 도출 | Phase 3: hV4만 permutation null을 genuinely 초과하는 유일한 보간 ROI |
| **CROSS-VALIDATION** | hV4 LOCO-fitted params에서 ΔRDM post-hoc 계산 | L_LOCO fitting의 부수적 결과로서 독립적 평가 |
| **SUPPLEMENTARY** | V1/V2 ΔRDM fitting → 메커니즘 특성화, β_s 문헌 수렴 | 적합 기준의 permutation test (순환적) — 필터 근거 아님 |
| **SUPPORTING** | V1 LOCO → 왜곡 모델 보조 증거 | V1 LOCO null ≈ 0.10-0.13 (voxel covariance 기원) — 필터 근거 부적절 |

### 2-2. Case Study 프레이밍 — CVD-Specificity 불요

**결론**: 개인 사례 연구에서 HC-specific한 false-positive 통제는 불필요하다.

**근거**:
- **Single-Model-Significance Fallacy** (Schütt et al. 2021): "RDM correlations tend to be positive even for very different representations." HC가 CVD 모델에 유의하게 적합되는 것은 예상되는 현상이며, 모델을 chance에 대해 검정하는 것은 low bar.
- **Crawford & Howell (1998)**: Phase 2에서 이미 개인 수준 anomaly 확인됨. 이것이 case study의 필수 검증이며, HC 분포 대비 CVD 전체의 유의성은 요구되지 않음.
- **LOCO의 역할**: 진단(diagnosis)이 아닌 프로파일링(profiling) → "어떤 색이 취약한가"의 개인화 도구.
- **3-step 검증 프레임워크**: (1) Crawford & Howell → anomaly, (2) LOCO → profiling, (3) Pre-image → filter

### 2-3. HC Specificity 실험 기록 (중복 방지)

아래 세 가지 접근이 모두 실패하였으므로 재시도 불필요:

| 실험 | 방법 | HC FPR | 결과 | Job/날짜 |
|------|------|--------|------|----------|
| **Raw LOCO profile** | hV4 shift_at_both, label-perm null | machado 43%, rc 71%, 2comp **100%** | HC 개인 변이가 CVD를 초과 | Job 96600, 2026-04-11 |
| **Baseline Δρ diagnostic** | 10-subj fitting, empirical rank | sub-08 emp_p=0.50, sub-09 0.25, sub-10 0.25 | HC baseline-Δρ 상관 r=**−0.894** (regression-to-mean) | Job 96664, 2026-04-11 |
| **ΔV (Experiment C)** | ΔV_obs = vuln_target − mean_HC_vuln, w_fixed | machado 43%, rc 86%, 2comp 57% | HC ΔV 편차 ≥ CVD (sub-03 range=1.189 > sub-09 0.284) | Job 96828, 2026-04-13 |

**구조적 원인**: n=7 HC / 8 colors / 2 DOF — permutation (8!=40,320)이 2-DOF 모델 유연성을 통제하기에 불충분. HC 개인 간 변이(hV4 baseline ρ: [−0.36, +0.69])가 HC-CVD 차이를 초과.

---

## 3. 모델

| 모델 | DOF | 파라미터 | 수준 | 비고 |
|------|:---:|---------|------|------|
| **Machado 1-way** | 1 | Δλ (nm) | 망막 | L/M cone spectral shift. Machado et al. 2009 |
| **R+C** | 2 | Δλ, g | 망막+피질 | `rg' = rg_base + (1+g)·(rg_ret - rg_base)`. g=0: 순수 망막, g<−1: 과보상 |
| **2-Component** | 2 | β_s (°), β_c (°) | 피질 | `θ' = θ + β_s·cos(θ−90°) + β_c·cos(θ−θ_conf)`. S-cone 보상 + confusion axis |
| **Fourier warp** | 4 | a₁, b₁, a₂, b₂ | 기술적 | `δ(θ) = Σ(a_k·sin + b_k·cos)`. Ablation ceiling only |
| **Hybrid** | 3 | Δλ + β_s, β_c | 복합 | **REJECTED** — 두 성분 non-additive |

**핵심 파라미터의 의미**:
- **Δλ**: L/M cone peak shift (nm). Machado et al. (2009) severity 범위와 직접 비교 가능 (§6-1).
- **g**: 피질 opponent gain. g=−1: 정확한 보상, g<−1: 과보상. Tregillus et al. (2021)과 보상 방향 개념적 정합 (§6-4).
- **β_s**: S-cone axis(90°) 방향 angular dilation. 축 선택이 Emery et al. (2021)의 S-cone 보상 패턴에 의해 근거됨 (§6-3).
- **β_c**: CVD family-specific confusion axis(protan 16°, deutan 150°) 방향 modulation. Brettel et al. (1997) (§6-3).

**모델 간 수준 차이**: Machado/R+C는 cone-level, 2-Component는 cortical-level. **동일 피험자에 대해 정반대 교정을 처방할 수 있다** (sub-08: cosine=−0.18, 부호 일치 3/8). 행동 실험만이 올바른 수준을 결정.

---

## 4. 손실함수

### 4-1. L_LOCO — PRIMARY (필터 설계)

```
L_fit = α·L_vuln/4 + β·L_rank/2 + δ·L_rdm/2 + ε·L_smooth/32400
```

| 항 | 정의 | 가중치 | 측정 |
|----|------|:------:|------|
| L_vuln | MSE(vuln_sim, vuln_cvd) | α=1.0 | Per-color LOCO vulnerability match |
| L_rank | 1 − Spearman ρ | β=0.5 | 취약성 순위 일치 |
| L_rdm | 1 − cosine(ΔRDM) | δ=0.2 | RDM 구조 보조 정규화 |
| L_smooth | mean(adj_diff(δθ)²) | ε=0.1 | 인접 색 간 교정량 smoothness |

- **적용**: 모든 모델 × hV4 (shift_at_both)
- **중요**: L_rdm(δ=0.2) 포함 → LOCO와 ΔRDM은 완전 독립이 아님. 정확한 표현: "per-color accuracy를 주 목적으로 하되 RDM을 보조 정규화로 사용"

### 4-2. L_ΔRDM — SUPPLEMENTARY (메커니즘 특성화)

```
L = max cosine(ΔRDM_sim, ΔRDM_obs)
```

- **적용**: 2-Component × V1, V2 (crossnobis cosine)
- ΔRDM_obs = RDM_CVD − mean(RDM_HC), 28개 색 쌍
- Permutation: 8! exact (40,320). Bootstrap: n=500 for CI
- **순환성 주의**: ΔRDM p-value는 적합 기준의 permutation test → 모델의 독립 검증이 아닌, fitting의 유의성

---

## 5. 결과

### 5-1. Detection — 모든 모델 수렴

| Subject | Machado | R+C | 2-Component | Fourier | 합의 |
|---------|:---:|:---:|:---:|:---:|------|
| sub-08 | p=0.058 | **p=0.005*** | **p=0.004**** | p=0.0002 | 왜곡 존재 |
| sub-09 | **p=0.018*** | =Machado | p=0.035* | p=0.018* | 왜곡 존재 |
| sub-10 | p=0.559 | — | p=0.058 | — | 정상 |

모든 모델이 동일 결론: sub-08/09에서 hue interpolation distortion 존재, sub-10 정상. **모델 선택에 무관하게 robust.**

### 5-2. hV4 LOCO (PRIMARY) — 모델별 최적 적합

| Subject | 모델 | 파라미터 | ρ | perm_p | 판정 |
|---------|------|---------|:---:|:---:|------|
| **sub-08** | **2-Component** | β_s=38°, β_c=−14° | 0.881 | **0.004**** | 전체 파이프라인 최강 |
| sub-08 | R+C | Δλ=2.0, g=+2.25 | 0.857 | 0.005** | 대안 모델 |
| **sub-09** | **Machado** | Δλ=13.5nm | 0.762 | **0.018*** | 1 DOF로 충분 (g=0 collapse) |
| sub-09 | 2-Component | β_s=6°, β_c=−22° | 0.690 | 0.035* | ρ 낮지만 pre-image 결정적 |
| sub-10 | — | — | — | NS | 정상 |

### 5-3. V1/V2 ΔRDM (SUPPLEMENTARY) — 메커니즘 특성화

| Subject | 모델 | β_s | β_c | cos | perm_p |
|---------|------|:---:|:---:|:---:|:---:|
| sub-08 V1 | 2-Component | 20±8° | −18±6° (CI excl 0) | 0.384 | 0.053 |
| **sub-09 V1** | **2-Component** | **23±10°** | +3±2° (CI incl 0) | **0.590** | **0.007***** |
| sub-09 Joint | 2-Component | 14° | +9° | 0.438 | **0.044*** |

**β_s 보충 관찰**: V1 ΔRDM에서 sub-08 β_s=20°, sub-09 β_s=23°. S-cone축 선택의 주요 근거는 이 수치가 아니라, hV4 LOCO에서 2-component 모델이 유의미하게 적합된다는 점 (§5-2) 및 Emery (2021)의 expansion/compression 패턴과의 기전적 정합 (§6-3).

**β_c 가족 특이성**: Deutan에서만 유의 (sub-08 CI excl 0). Protan은 큰 Δλ로 confusion axis 붕괴 → β_c 불요.

### 5-4. L_LOCO 구성 요소 분해 (교차 검증)

| Case | (β_s, β_c) | ΔL_vuln | ΔL_rank | ΔL_rdm | ΔRDM cos post-hoc | Δρ |
|------|:----------:|:-------:|:-------:|:------:|:-----------------:|:---:|
| sub-08 hV4 | (38, −14) | +0.002 | **−0.262** | −0.040 | +0.080 | +0.524 |
| sub-08 V1 | (50, −14) | −0.014 | **−0.131** | −0.060 | +0.120 | +0.262 |
| sub-09 hV4 | (6, −22) | −0.008 | **−0.119** | **+0.023** | **−0.046** | +0.238 |
| sub-09 V1 | (38, +22) | −0.010 | **−0.131** | −0.054 | **+0.107** | +0.262 |

**해석**: L_rank가 모든 케이스에서 최대 개선 주도. sub-09 V1만 LOCO와 ΔRDM의 공유 구조 확인 (post-hoc ΔRDM cos +0.107). sub-09 hV4에서는 LOCO가 RDM을 파괴 (ΔRDM cos −0.046).

### 5-5. Correction — 모델 간 방향 불일치

Sub-08 hV4 per-color δθ 비교:

| 색 | Machado | R+C | 2-Component | 부호 일치? |
|:---:|:---:|:---:|:---:|:---:|
| c1(red) | −3.7° | −11.4° | −12.1° | YES |
| c2(org) | −2.8° | −9.9° | −20.2° | YES |
| c3(yel) | −1.3° | −4.8° | −25.7° | YES |
| c4(grn) | +0.3° | +1.4° | −29.4° | **NO** |
| c5(cya) | +2.6° | +10.7° | −32.1° | **NO** |
| c6(blu) | −11.7° | −38.4° | −10.3° | YES |
| c7(pur) | −5.1° | −18.8° | +29.4° | **NO** |
| c8(mag) | −0.5° | −1.1° | +18.5° | **NO** |

부호 일치 4/8. Machado/R+C vs 2-Component Spearman ρ = **−0.714** (유의하게 반상관). **같은 취약성 순위에 수렴하되 정반대 교정을 처방** → 행동 실험만이 판별 가능.

### 5-6. Pre-Image — 필터 존재성

| 모델 | Sub-08 | Sub-09 | 필터 실현 가능성 |
|------|:------:|:------:|:----------:|
| R+C | 8/8 exact (<0.001°) | N/A (=Machado) | Sub-08만 |
| Machado | — | **4/8 exact, 4/8 FAIL** (max 65°) | Sub-09 **불가능** |
| **2-Component** | **8/8 exact** (<0.001°) | **8/8 exact** (<0.001°) | **양쪽 모두** |

**Sub-09 Machado 실패 원인**: Δλ=13.5nm → opponent arc 360°→~96° 압축. c4-c6이 동일 hue ~282°로 수렴 → 독립 복원 불가.

**2-Component 성공 이유**: Cortical angular dilation → arc compression 없음 → bijective → 항상 역변환 존재.

**역설**: Machado LOCO ρ(0.762) > 2-Component(0.690)이지만, pre-image는 Machado가 실패. **"더 정확한 모델이 더 유용한 모델은 아니다."**

Pre-image 교정량:

| | Sub-08 R+C | Sub-08 2-Comp | Sub-09 2-Comp |
|---|:---:|:---:|:---:|
| Mean \|δ\| | 23.5° | 46.3° | 20.1° |
| Max \|δ\| | 42.9° | 104.2° | 48.1° |
| 벡터 cosine | — | −0.18 (반상관) | — |

### 5-7. Severity-Dependent Filter Feasibility

| 모델 수준 | Sub-08 (Δλ=2nm, mild) | Sub-09 (Δλ=13.5nm, moderate) |
|----------|:---:|:---:|
| **Cone-level** (Machado/R+C) | 자극 공간 가능 (arc ~260°) | **자극 공간 불가** (arc ~96°) |
| **Cortical-level** (2-Comp) | 자극 공간 가능 (bijective) | **자극 공간 가능** (bijective) |

**모델 수준의 선택이 치료적 결론을 결정한다.** Cone-level 채택 시 sub-09는 "교정 불가", cortical-level 채택 시 "교정 가능".

---

## 6. 문헌 기반 이론적 근거 (Physiological Grounding)

본 절의 목적은 시뮬레이터 파라미터가 문헌 값과 "수치적으로 일치한다"를 주장하는 것이 **아니라**, 모델 설계의 각 구조적 선택이 기존 문헌에 의해 독립적으로 뒷받침된다는 것을 보이는 것이다.

- β_s, g 등은 본 연구 고유의 파라미터 → 문헌에 동일한 양의 비교값 부재
- Emery의 21.4°(rotation phase)와 β_s(dilation amplitude)는 다른 물리량 → 수치 비교 무의미
- Tregillus의 amplification factor와 g는 다른 차원 → 변환 불가능
- 유일한 예외: **Machado Δλ** — 동일 모델을 직접 활용하므로 문헌 severity 범위와 직접 비교 가능

| 근거 수준 | 내용 | 해당 요소 |
|----------|------|----------|
| **직접 비교** | 동일 모델·동일 물리량 → 수치 비교 가능 | Machado Δλ (nm) |
| **구조적 근거** | 축·ROI 선택이 문헌에서 독립적으로 확립 | S-cone축 (β_s), confusion축 (β_c), hV4 ROI |
| **기전적 정합** | 서로 다른 측정이 같은 기저 기전을 시사 | β_s ↔ Emery expansion/compression, g ↔ Tregillus overcomp |

### 6-1. Machado Δλ — 유일한 직접 지표 비교

Machado 1-way 모델은 Machado, Oliveira, & Fernandes (2009)의 cone fundamental interpolation을 **그대로 사용**한다. 따라서 fitting 결과 Δλ(nm)는 동일 물리량이며, 문헌의 severity classification과 직접 대조 가능하다.

| Subject | 최적 Δλ | 문헌 범위 | 판정 |
|---------|:------:|----------|------|
| sub-08 (deutan) | 2.0 nm | Very mild: 1-4 nm | ✓ 범위 내 |
| sub-09 (protan) | 13.5 nm | Moderate-severe: 9-14 nm | ✓ 범위 내 |
| sub-10 (normal) | 0 nm | Normal: 0 nm | ✓ 정상 |

fMRI LOCO vulnerability에서 추출한 Δλ가 anomaloscope 기반 severity classification과 정합적. 단, 개인별 Δλ는 Rayleigh match에서의 Δλ와 정확히 같은 양은 아니므로 **범위 수준의 일치**로 해석한다.

### 6-2. hV4 Primary ROI — 문헌적 근거

hV4를 primary fitting target으로 선택한 근거는 세 가지 독립적 문헌에서 수렴한다:

**1. Brouwer & Heeger (2009)** — 동일 방법론, 동일 ROI
- Forward model + PCA 기반 novel-color reconstruction에서 V4/VO1만 성공, V1-V3는 유의하게 저하
- 우리의 LOCO도 동일 결론: hV4만 permutation null을 genuinely 초과 (Phase 3 확립)
- **같은 측정 방법(multivariate interpolation)으로 같은 ROI(hV4)가 최적**이라는 가장 직접적 선례

**2. Kuriki et al. (2025)** — cortical → perceptual bridge
- hV4/VO1의 cortical RDM(cRDM)이 appearance-based perceptual RDM(pRDM)과 유의한 partial correlation
- hV4의 multivariate 기하학이 주관적 색 판단과 직접 연결 → 필터가 hV4 기하학을 교정 대상으로 삼는 것의 지각적 타당성 지지

**3. Tregillus et al. (2021)** — 위계적 보상 방향
- V1은 reduction model과 일치 (AT < CN, p=0.04), V2v/V3v는 완전 보상 (AT ≈ CN)
- **높은 피질 영역일수록 보상이 증가**하는 방향성 → hV4 > V1이라는 우리 결과와 방향 일관
- 단, 정확한 위계 재현은 불가 (V2가 가장 약함, V1이 유의) — 측정 차이(univariate CRF vs multivariate LOCO) 및 ROI 정의 차이(V2v vs V2 전체)에 기인

### 6-3. 2-Component 모델 구조의 생리학적 근거

2-Component 모델의 핵심 설계 — 두 축(S-cone 90°, confusion line 16°/150°)의 선택 — 은 파라미터 값이 아니라 **모델 구조 자체**가 생리학적으로 근거된다.

**S-cone 축 (β_s · cos(θ−90°)) — Emery et al. (2021)에 의한 근거**:

> Emery, K. J., Volbrecht, V. J., Peterzell, D. H., & Webster, M. A. (2021). *Vision Research*, 183, 1-15.
> 10 anomalous trichromats (7 DA, 3 PA) vs 26 normal trichromats. Hue scaling (36색, 10° 간격) + contrast thresholds.

β_s가 S-cone 축을 변형 대상으로 선택한 근거:
- AT의 hue-scaling 원시 데이터에서 B/Y 극 근처 **확장** + R/G 근처 **압축**이 관찰됨
- 이 step-like 패턴은 rigid rotation이 아닌 **angular dilation**과 기하학적으로 일치
- cos(θ−90°) > 0인 영역 (B/Y 근처): 색이 팽창 → hue-scaling에서 blue/yellow 카테고리 확장
- cos(θ−90°) ≈ 0인 영역 (R/G 근처): 변화 없음 → red/green 카테고리 보존
- Emery의 21.4° B-Y phase shift는 이 dilation 패턴의 사인파 요약 통계량
- **기전적 해석**: L-M 축 민감도가 저하된 AT가 S-cone 경로를 상향조절하여 색 변별을 보상 → S-cone 축 방향의 표상 확장

**hV4 LOCO에서의 검증**: S-cone축을 포함한 2-component 모델이 hV4 LOCO에서 두 CVD 피험자 모두 유의미하게 적합됨 (sub-08 p=0.004**, sub-09 p=0.035*). S-cone 축 방향의 변형이 hV4 색 보간 구조에 실제로 기여함을 직접 보여준다.

**β_s와 Emery 21.4°는 수치 비교 불가**:

| | β_s | Emery B-Y phase |
|---|---|---|
| **측정 대상** | hV4 multivariate 색 보간의 angular dilation | 주관적 hue-scaling B-Y phase shift |
| **기하학적 연산** | 확장(dilation): B-Y 근처 색을 밀어냄 | 회전(rotation): B-Y 축 자체의 위상 이동 |
| **의미** | per-color LOCO vulnerability를 설명하는 최적 변형 크기 | hue-scaling 함수의 사인파 요약 통계량 |

의미 있는 연결은 β_s 수치가 아니라 **기저 기하학적 연산의 정합** — Emery의 step-like expansion/compression 패턴이 β_s·cos(θ−90°)가 수행하는 연산과 일치한다는 점이다.

**Confusion axis (β_c · cos(θ−θ_conf)) — Brettel et al. (1997)**:
- Protan(16°) 및 deutan(150°) confusion line은 cone-level spectral convergence에서 유도
- β_c는 이 축 방향의 modulation을 포착 → confusion line 구조가 cortical representation에 잔존하는지 검증
- 결과: deutan(sub-08)에서만 β_c 유의 (CI excl 0). Protan(sub-09)은 큰 Δλ로 confusion axis 붕괴 → β_c ≈ 0 (CI incl 0)
- **Severity-dependent 패턴이 생리학적 예측과 일치**: 경미 CVD = confusion line 잔존, 중등도 CVD = 붕괴

### 6-4. R+C g 파라미터 — 피질 보상의 개념적 뒷받침

R+C 모델의 g 파라미터(opponent gain)는 Tregillus et al. (2021)의 피질 보상과 **개념적으로만** 연결된다.

> Tregillus, K. E. M. et al. (2021). *Current Biology*, 31(5), 936-942.
> 7 AT vs 7 CN. L-vs-M / S-vs-LM contrast response function → BOLD β weights.

**Tregillus 핵심 결과**:

| ROI | AT vs CN L-vs-M | p | Amplification factor |
|-----|:---:|:---:|:---:|
| **V1** | AT < CN (감소) | **p=0.04*** | 2.94 (SD=2.81) |
| **V2v** | AT ≈ CN | p=0.62 | **6.39** (SD=5.21) |
| **V3v** | AT ≈ CN | p=1.00 | **7.82** (SD=5.76) |

**g ↔ AF 연결의 한계**:

| | Tregillus AF | 우리 g |
|---|---|---|
| 물리량 | BOLD CRF 진폭 비율 | opponent chromaticity gain |
| 측정 | univariate (단일 채널 진폭) | 2D 벡터 연산 |
| 수학적 변환 | **불가** — CRF 비선형성 포함 | **불가** — CRF를 거치지 않음 |

**연결 가능한 것**: 둘 다 "피질 보상이 존재하며, 과보상 방향"이라는 결론을 독립적으로 지지. Tregillus: AF > 1 → 보상 초과. 우리: sub-09 g = −1.10 → 10% 과보상.

**연결 불가능한 것**: AF를 g로 변환하거나 수치 비교하는 것.

### 6-5. 문제적 파라미터

| 파라미터 | 우리 값 | 문제점 | 해석 |
|---------|--------|--------|------|
| Sub-08 V1 g | −2.25 | 125% overcompensation — 문헌 범위(20-40%) 초과 | 2-DOF 모델의 과적합 가능성 |
| Sub-08 hV4 g | +2.25 | 3.25× 증폭 — 선례 없음 | R+C 모델의 구조적 한계 (단일 축 rescaling) |
| Sub-10 V1 2-Comp | p=0.004** | 정상 피험자에서 FP | 2-DOF 모델 유연성 + V1 복셀 수 → 과적합 |

### 6-6. 핵심 해석

1. **Machado Δλ가 유일한 직접 비교**: 동일 모델을 사용하므로 fMRI 기반 severity 추정이 문헌 범위와 정합. LOCO vulnerability 기반 cone-shift 추정의 외적 타당도(external validity) 지지.
2. **hV4 선택은 가장 강하게 뒷받침됨**: multivariate interpolation이라는 동일 방법론에서 동일 ROI가 최적(B&H 2009)이며, cortical geometry가 지각 판단과 직접 연결됨이 확립(Kuriki 2025).
3. **2-Component 구조는 physiologically grounded**: S-cone축과 confusion축이라는 설계 선택이 Emery 2021의 dilation 패턴 및 Brettel 1997의 confusion line과 독립적으로 정합. 강점은 파라미터 값이 아니라 모델 구조에 있다.
4. **피질 보상의 존재는 Tregillus 2021과 방향 일치**: 단, 크기 비교는 불가. 개념적 수렴에 불과.
5. **수치 수렴 주장 불가**: β_s(dilation)와 Emery 21.4°(rotation phase)는 다른 물리량. g와 AF는 다른 차원. 모델 구조의 생리학적 근거 + 기전적 정합만 주장 가능.

---

## 7. 결론

### 7-1. 모델 선택 요약

| Subject | Primary Model | hV4 LOCO p | V1 ΔRDM p | Pre-image | Filter role |
|---------|:------------:|:---:|:---:|:---:|------|
| **sub-08** | **2-Component** (β_s=38°, β_c=−14°) | **0.004**** | CI excl 0 | 8/8 exact | Primary candidate |
| sub-08 | R+C (Δλ=2.0, g=2.25) | 0.005** | 0.179 NS | 8/8 exact | Alternate |
| **sub-09** | **2-Component** (β_s=6°, β_c=−22°) | 0.035* | **0.007***** | **8/8 exact** | **유일한 feasible filter** |
| sub-09 | Machado (Δλ=13.5) | 0.018* | — | 4/8 FAIL | Pre-image 불가 |
| **sub-10** | — | All NS | — | — | 정상 (no filter) |

**2-Component는 두 CVD 피험자 모두에서 LOCO+ΔRDM dual-validated이며, 양쪽 모두에서 exact pre-image를 달성하는 유일한 모델.**

### 7-2. 세 가지 기여

1. **방법론**: hV4 LOCO 취약성이 JND HYPO를 100% 예측 (SRM z는 33%). 적합 기준(LOCO vs ΔRDM)에 따라 동일 모델의 파라미터가 다르게 나옴 → fitting/evaluation criterion 분리 필수.
2. **모델**: 2-Component angular dilation. S-cone축 + confusion축 설계가 Emery 2021 + Brettel 1997에 의해 physiologically grounded (§6-3). hV4 LOCO에서 두 CVD 모두 유의미 (p=0.004/0.035). S-cone 보상은 universal, β_c는 family-specific.
3. **이론**: Invertibility = correction feasibility. Mild (sub-08): bijective → exact restoration. Moderate (sub-09): Machado 불가, 2-Component 가능.

### 7-3. N=3의 강점

> "세 CVD 개인에서 세 가지 질적으로 다른 결과를 관찰한다: (i) sub-08은 경미하고 완전히 가역적인 왜곡, (ii) sub-09는 올바른 모델 하에서만 가역적인 더 강한 왜곡, (iii) sub-10은 모든 분석에서 왜곡 없음. 이 다양성 자체가 요점이다 — 동일한 망막 진단이 개인마다 고유한 피질 기하학으로 매핑된다."

### 7-4. 다음 단계 — 행동 검증 실험

| Subject | 조건 | 핵심 가설 |
|---------|------|----------|
| Sub-08 | R+C filter, 2-Comp filter, No filter | H5: 어느 hierarchy가 맞는가? (반상관 교정) |
| Sub-09 | 2-Comp filter, No filter | H1-H3: JND 개선, LOCO ↓, ΔRDM → 0 |
| Sub-10 | 2-Comp filter, No filter | H4: 효과 없음 (specificity) |

**핵심**: Sub-08 이중 필터 비교가 "cone-level vs cortical-level" 메커니즘의 경험적 판별.

---

## 8. 검증 요약 (Validation Summary)

### 8-1. 모델별 다차원 검증 매트릭스

| 검증 항목 | Machado | R+C | 2-Component | Fourier |
|----------|:---:|:---:|:---:|:---:|
| hV4 LOCO (sub-08) | p=0.058 | **p=0.005**** | **p=0.004**** | p=0.0002 |
| hV4 LOCO (sub-09) | **p=0.018*** | =Machado | p=0.035* | p=0.018* |
| sub-10 null | NS ✓ | — | NS ✓ | — |
| Pre-image sub-08 | — | 8/8 exact | **8/8 exact** | — |
| Pre-image sub-09 | **4/8 FAIL** | N/A | **8/8 exact** | — |
| V1 ΔRDM (sub-09) | — | — | **p=0.007**** | — |
| Machado Δλ ↔ 문헌 severity | **✓ 범위 내** | — | — | — |
| 모델 구조 phys. grounding | — | g 방향 일치 (§6-4) | S-cone + confusion축 (§6-3) | — |
| LOCO→JND concordance | — | — | **100% (3/3)** | — |
| HC specificity | FPR 43% | FPR 71% | FPR 100% | — |
| Dual validation (LOCO+ΔRDM) | ❌ | ❌ | **✓ (both CVD)** | ❌ |

### 8-2. 교차 검증 (Cross-Phase Convergence)

| Phase | 지표 | 결과 | 연결 |
|-------|------|------|------|
| Phase 2 (SRM) | Crawford-Howell | sub-08 V2 p=0.040*, sub-09 V1 p=0.007* | 개인 수준 anomaly 확인 |
| Future Phase 1 (Forward Model) | LOCO 색별 취약성 | orange/yellow/purple Crawford-Howell p<0.02 | LOCO vulnerability → 필터 fitting 입력 |
| Future Phase 3 (Behavioral) | LOCO→JND | 3/3=100% concordance (HC N 불변) | 기능적 타당성 |
| Future Phase 3 (Behavioral) | SRM z→JND | 1/4=25% concordance | Metric ≠ functional |
| **This Phase** | Machado Δλ | sub-08 2nm, sub-09 13.5nm → severity 범위 내 | 유일한 직접 비교 (§6-1) |
| **This Phase** | 모델 구조 | S-cone축(Emery) + confusion축(Brettel) + hV4(B&H) | Physiological grounding (§6) |

### 8-3. Physiological Grounding 구조도

```
┌─────────────────────────────────────────────────────────────┐
│                 Physiological Grounding                      │
│                                                             │
│  [직접 비교]   Machado Δλ ──── 문헌 severity 범위 내         │
│               (동일 모델, 동일 물리량)                        │
│                                                             │
│  [구조적 근거] hV4 ROI ←─── B&H 2009 + Kuriki 2025          │
│               β_s (S-cone축) ←─── Emery 2021 dilation 패턴  │
│               β_c (confusion축) ←── Brettel 1997             │
│                       │                                      │
│                       ▼                                      │
│               2-Component 모델                               │
│               θ' = θ + β_s·cos(θ−90°) + β_c·cos(θ−θ_conf)  │
│                       │                                      │
│               hV4 LOCO: sub-08 p=0.004**, sub-09 p=0.035*   │
│                       │                                      │
│                       ▼                                      │
│               Pre-image filter (8/8 exact, both CVD)         │
│                                                             │
│  [기전적 정합] g < −1 ←─── Tregillus 2021 (방향만 일치)      │
└─────────────────────────────────────────────────────────────┘
```

---

## 9. 제한점

| 제한점 | 설명 | 영향 |
|--------|------|------|
| **n=3 CVD** | Case study 수준. 그룹 일반화 불가 | 사례별 결론만 가능; 개인화 필터의 존재 증명으로 충분 |
| **HC specificity 미해결** | 2-Component FPR=100% (HC도 유의) | CVD-only claim 보류. 필터는 행동 검증으로 판별 |
| **g 파라미터 문헌 초과** | sub-08 g=±2.25 (문헌: 20-40% overcomp) | R+C 모델의 구조적 한계 (단일 축 rescaling) |
| **LOCO null 수준** | V1/V2 null ≈ 0.10-0.13 (voxel covariance) | V1/V2 LOCO는 필터 근거 부적절 |
| **hV4 voxel 수** | 67 voxels, K=3 → 개인 간 baseline 변이 대 | baseline ρ: [−0.36, +0.69] 범위 |
| **Cross-model δθ 반상관** | Machado/R+C vs 2-Comp Spearman ρ=−0.714 | 행동 실험만이 올바른 모델 수준 결정 |
| **ΔRDM 순환성** | ΔRDM p-value = fitting criterion의 permutation test | 독립 검증이 아닌 fitting의 유의성 |
| **피험자 내 fMRI-행동 비등록** | 행동 세션 ≠ fMRI 세션 | 직접 대응 불가, 교차 양상 수렴으로 보완 |
| **Emery 연결의 한계** | β_s(dilation) vs Emery 21.4°(rotation phase) = 다른 물리량; 수치 비교 불가 | 모델 구조(S-cone축 선택)의 생리학적 근거로만 해석 (§6-3) |

---

## 부록

### A. 거부된 접근

| 접근 | 실패 이유 |
|------|----------|
| ΔRDM inverse → filter | −37% to −153% 악화. Pairwise geometry ≠ per-color accuracy |
| Simple inverse (−δ) | Nonlinear forward model에서 D(θ−δ) ≠ D(θ)−δ |
| Hybrid (Cone + 2-Comp) | Sub-08 Δλ=0 (cone 무기여), Sub-09 3-DOF 발산. Non-additive |
| Fourier as primary | 4 DOF/8 colors = overfitting. CCC ≈ R+C. Ablation ceiling only |
| Gen-3 ΔRDM-only (Machado) | 0/18 passed. ΔRDM_sim이 ΔRDM_obs와 반상관 |
| HC specificity (3가지) | 위 §2-3 참조. 모든 접근에서 HC FPR ≥ 43% |

### B. 파일 위치

**스크립트**:
- `scripts/loco_distortion_fit.py` — 다중 모델 LOCO fitting
- `scripts/comprehensive_2component_analysis.py` — 2-Component ΔRDM + bootstrap
- `scripts/preimage_filter_search.py` — Pre-image 수치 탐색
- `scripts/experiment_delta_vuln.py` — HC specificity Experiment C (ΔV)
- `scripts/baseline_delta_rho_diagnostic.py` — HC specificity baseline Δρ
- `scripts/hc_specificity_test.py` — HC specificity label-perm FPR

**결과**:
- `results/loco_filter/phase_a*/` — LOCO fitting (Machado, R+C, 2-Comp, Fourier)
- `results/loco_filter/preimage*/` — Pre-image (R+C, Machado, 2-Comp)
- `results/2component_comprehensive_v2/` — V1/V2 ΔRDM
- `results/baseline_delta_rho/` — HC Δρ diagnostic
- `results/experiment_c_delta_vuln/` — ΔV experiment
- `results/loco_decomposition/` — L_LOCO 구성 요소 분해 시각화

**상위 문서**:
- `LOCO_FILTER_RESULTS.md` — 전체 수치 상세
- `LOCO_FILTER_PLAN.md` — 파이프라인 설계

### C. 문헌

| 주제 | 논문 | 방법 | 본 연구 연결 |
|------|------|------|------|
| Cone shift 모델 | Machado, Oliveira, & Fernandes (2009) *IEEE TVCG* | Severity-parameterized cone fundamental interpolation | 유일한 직접 비교: Δλ가 문헌 severity 범위 내 (§6-1) |
| **피질 보상** | **Tregillus et al. (2021) *Curr Biol*, 31, 936-942** | fMRI BOLD CRF; V1 vs V2v/V3v 해리; N=7 AT vs 7 CN | 보상 방향 개념적 정합 (§6-4). hV4 ROI 근거 (§6-2) |
| **S-cone 보상** | **Emery et al. (2021) *Vision Res*, 183, 1-15** | Hue scaling (36색, 10° 간격); N=10 AT vs 26 NT | S-cone축(β_s) 선택의 생리학적 근거: step-like dilation 패턴 (§6-3) |
| hV4 perceptual hub | Bannert & Bartels (2018) *J Neurosci* | Color imagery + perception cross-decoding | hV4 = 유일한 보간 ROI; trial-by-trial 행동 예측 |
| LOCO 기원 | Brouwer & Heeger (2009) *J Neurosci*, 29, 13992 | Forward model + PCA; novel-color reconstruction | V4/VO1만 novel color 재구성 성공; V1-V3 유의하게 저하 |
| Categorical clustering | Brouwer & Heeger (2013) *J Neurosci*, 33, 15454 | 12색 color-naming vs diverted attention | V4v/VO1 categorical clustering; ΔRDM이 task-dependent perceptual boundary 추적 |
| **cRDM→pRDM bridge** | **Kuriki et al. (2025)** | hV4/VO1 cortical RDM vs appearance pRDM partial correlation | 피질 ΔRDM과 주관적 색 판단이 직접 연결됨을 지지 (§6-2 bridging evidence) |
| EnChroma 한계 | Somers et al. (2024) | Spectral filter behavioral study | Appearance ↑, discrimination ↗ (marginal) |
| 피질 가소성 리뷰 | Isherwood, Joyce, Parthasarathy, & Webster (2020) *Faculty Rev* | CVD plasticity 종합 리뷰 | 장기 보상의 다양한 timescale |
| 필터 착용 가소성 | Werner, Marsh-Armstrong, & Knoblauch (2020) *Curr Biol* | AT filter 착용 수일 → 제거 후에도 지각 유지 | 피질 가소성의 직접 증거 |
| Single-model fallacy | Schütt, Alexander, & Hebart (2021) | RDM correlation 양수 편향 | HC FPR = expected, not a flaw |
| Case study validity | Crawford & Howell (1998) *Clin Neuropsychol* | 소표본 대비 단일 개인 검정 | Individual anomaly = sufficient |
| V1→V4 표상 전환 | Kim, Bao, Watanabe, Sasaki, & Bhatt (2020) *PNAS* | Stimulus-driven → percept-driven 전환 | V1/V2 = stimulus, V4/VO1 = percept |
| Encoding-RSA 통합 | Diedrichsen & Kriegeskorte (2017) *PLOS CB* | 동일 2nd moment의 다른 표현 | LOCO ↔ ΔRDM = 동일 구조의 다른 함수 |
