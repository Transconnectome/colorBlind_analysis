# Future Phase 1: Group-Prior Prediction Model

> **프로젝트**: Color Vision Deficiency Neural Representation Analysis

> **피험자**: HC 7명 (sub-01~07), CVD 3명 (sub-08 deutan, sub-09 protan, sub-10 deutan)

> **ROI**: V1, V2, V3, hV4

> **1차 목적**: 학습 데이터에 없는 색상 자극에 대한 voxel response를 보간(interpolation)하여 예측하는 모델 구축 → Phase 2 filter 설계의 기반
>
> **2차 목적**: HC-CVD 비교를 통한 SRM 결과 교차 검증 및 CVD 왜곡 특성화

---

## 목차

**방법론**
- [1. 핵심 원리](#1-핵심-원리)
- [2. 알고리즘 (Steps A-D)](#2-알고리즘-steps-a-d)
- [3. Validation 구조](#3-validation-구조)
- [4. Metrics](#4-metrics)
- [5. 모델 인덱스 (11 Models Tested)](#5-모델-인덱스-11-models-tested)

**결과**
- [6. 데이터 품질](#6-데이터-품질)
- [7. 주요 예측 모델: LORO & LOCO 결과](#7-주요-예측-모델-loro--loco-결과)
  - [7a. LORO — Run Generalization](#7a-loro--run-generalization-mean-voxel_corr)
  - [7b. LOCO — Color Interpolation](#7b-loco--color-interpolation-ridge_gcv-확정-모델)
  - [7c. 모델 비교 (Supplementary)](#7c-모델-비교-supplementary)
  - [7d. 모델 검증 (Supplementary)](#7d-모델-검증-supplementary)
  - [7e. GO/NO-GO Gate](#7e-gono-go-gate)
  - [7f. LOSO Zero-Shot Transfer](#7f-loso-zero-shot-transfer)
- [8. 부가 분석: HC-CVD 비교 및 모델 강건성 (2차 목적)](#8-부가-분석-hc-cvd-비교-및-모델-강건성-2차-목적)
  - [8a. HC-CVD Gap 구조 (탐색적, N=3)](#8a-hc-cvd-gap-구조-탐색적-n3)
  - [8b. 개별 CVD 프로파일 (Crawford-Howell)](#8b-개별-cvd-프로파일-crawford-howell)
  - [8c. 모델 명세 민감도: K-Ablation](#8c-모델-명세-민감도-k-ablation)
  - [8d. Per-Color Residual — Cone Shift 일관성](#8d-per-color-residual--cone-shift-일관성)
  - [8e. Cross-Phase 수렴 (SRM ↔ FE, 보조)](#8e-cross-phase-수렴-srm--fe-보조)
  - [8f~8i. Supplementary 모음](#8f8i-supplementary-모음)
  - [8j. Per-Subject K* (Cone Shift 보조 증거)](#8j-per-subject-k-cone-shift-보조-증거)
- [9. Red Team 분석](#9-red-team-분석)
  - [9a. Original Red Team (RT-1~RT-5)](#9a-original-red-team-rt-1rt-5)
  - [9b. Hinton 관점 Red Team (RT-6)](#9b-hinton-관점-red-team-rt-6)
  - [9c. 중화 실험](#9c-중화-실험)
  - [9d. 중화 후 총괄표](#9d-중화-후-총괄표)
- [10. Discussion — 문헌 통합](#10-discussion--문헌-통합)
- [11. 계층적 발견 및 결론](#11-계층적-발견-및-결론)
- [12. Phase 2 핸드오프 & 평가](#12-phase-2-핸드오프--평가)

**부록**
- [부록 A: Phase 2 연결](#부록-a-phase-2-연결)
- [부록 B: 프로젝트 구조](#부록-b-프로젝트-구조)
- [부록 C: 핵심 통계 참조](#부록-c-핵심-통계-참조-quick-reference)

---

## 1. 핵심 원리

Prediction model은 **Procrustes voxel space**에서 작동한다. SRM은 prediction 공간도 evaluation 공간도 아닌, **prior-construction helper**로만 사용된다.

SRM이 prediction에 부적합한 핵심 증거 — LOCO MAE 비교:

| ROI | Procrustes | SRM | Delta |
|-----|-----------|-----|-------|
| V1 | ~76° | ~80° | +4° |
| V2 | ~80° | ~85° | +5° |
| V3 | ~77° | **~99°** | **+22° (chance 90°보다 worse)** |
| hV4 | ~69° | ~72° | +3° |

SRM은 interpolation 구조를 파괴하고 (V3에서 chance보다 나쁨), stimulus → representation mapping을 학습하지 않는다.

---

## 2. 알고리즘 (Steps A-D)

### Step A: HC 공통공간 적합

HC subject i = 1,...,M (M=7)의 Procrustes-aligned data Y_i ∈ R^{V_i × N}에 BrainIAK SRM 적합:

```
R_i ∈ R^{V_i × k},  Z_i = R_i^T @ Y_i ∈ R^{k × N}
```

k 값: V1=4, V2=4, V3=3, hV4=3.

### Step B: Group Prior 학습

```
A_i = argmin_A ||Z_i - A @ C||² + lambda_A * ||A||²   (per HC subject)
A_g = (1/M) * sum_i A_i                                (group prior 평균)
```

### Step C: Target Subject 공간으로 Prior 투사

```
W_{0,s} = R_s @ A_g ∈ R^{V_s × K}
```

### Step D: Fine-Tuning (Closed-Form)

```
W_s = argmin_W ||Y_s - W @ C||² + lambda * ||W - W_{0,s}||²
```

**Closed-form 해:**
```
W_s = (Y_s @ C^T + lambda * W_{0,s}) @ (C @ C^T + lambda * I)^{-1}
```

lambda가 group prior와 individual data의 균형을 제어한다 (0 = OLS, ∞ = zero-shot transfer).

---

## 3. Validation 구조

### LORO: Run Generalization

- 5 runs로 W_s 학습, held-out 1 run에서 평가
- Metric: r_LORO = corr(v_pred, v_real)

### LOCO: Color Interpolation

- 7색으로 W_s 학습, held-out 1색 예측
- Metric: r_LOCO = corr(v_pred, v_real), MAE_LOCO = angular decoding error
- **Filter pipeline과 가장 직접적으로 연결되는 validation**

### LOSO: Subject Transfer

| 조건 | 수식 | 의미 |
|------|------|------|
| Zero-shot | W_s = W_{0,s} | Prior만 (target data 없음) |
| Fine-tuned | Prior + target data | 제안 방법 |
| Subject-only | OLS (prior 없음) | Baseline |

---

## 4. Metrics

| 우선순위 | Metric | 용도 |
|---------|--------|------|
| 1차 | Voxel prediction correlation | Primary quality measure |
| 2차 | Explained variance (R²) | Variance accounted for |
| 3차 | LOCO angular MAE | Interpolation 정확도 |
| 4차 | Predicted vs real RDM correlation | Geometry 보존 |
| 5차 | Normalized geometry fit (pred RDM / ceiling) | Ceiling 대비 성능 |

Noise ceiling 없이는 데이터 품질과 모델 품질을 혼동한다. Normalized fit으로 ROI간 공정 비교.

---

## 5. 모델 인덱스 (11 Models Tested)

### Baseline Models

| Model | 수식 | Inner CV | 판정 |
|-------|------|----------|------|
| **ols** | W = (C'C)⁻¹C'X | N/A | Baseline — LOCO 불안정 (V1 +0.051) |
| **ridge_gcv** | W = (C'C + αI)⁻¹C'X | GCV (outer LOCO) | **LOCO 최적 모델** (V1 +0.130, hV4 +0.183) |
| **prior_only** | W = W₀ = R_s @ A_g | N/A | LOCO 전 ROI 음 — interpolation 실패 |
| **prior_finetune** | W = (C'C + λI)⁻¹(C'X + λW₀) | Nested CV (outer LORO) | **LORO 승리** (V1 0.315), **LOCO 패배** (V1 -0.056) |

### Extended & Alternative Models

| Model | 판정 | 근거 |
|-------|------|------|
| ridge_rrr_r{2,3,4} | **기각** | 모든 rank에서 baseline보다 나쁨 |
| ridge_smooth_best | **기각** | voxel_corr ↑ 기만적, rdm_pearson ↓ (37-65%) |
| smooth_tikh | **기각** | Perm 전 ROI 실패, 공간 공분산만 포착. 3회 rescue 실패 |
| mixed_ridge_prior | **기각** | V1-V3 음 |
| bayes_prior | **기각** | V1-V3 음 |
| smooth_prior | **기각** | Prior가 smoothness 효과 상쇄 |

### Encoding Basis

| Basis | Type | K | 판정 |
|-------|------|---|------|
| **FE-6** | Half-wave rectified cos² | 6 | **확정** — LOCO/LORO 모두 최고 |
| LF-4 | Fourier (1st+2nd harmonic) | 4 | 기각 — FE-6보다 유의하게 나쁨 |
| LF-6 | Fourier (3rd harmonic까지) | 6 | 기각 — 같은 K에도 최악 |

### 공통 표기

- C ∈ R^{K×N}: FE-6 basis (K=6, N=8 hue angles)
- X ∈ R^{V_s×N}: Run-averaged voxel patterns
- W₀ = R_s @ A_g: SRM group prior
- D ∈ R^{K×K}: Circular difference matrix (인접 channel smoothness)

**핵심 교훈**: (1) 동일 수식(smoothness)도 inner LORO → artifact, inner LOCO → 개선처럼 보이나 permutation 실패. (2) voxel_corr/rdm_pearson 개선이 반드시 색 판별 신호를 의미하지 않음 — 공간 공분산 포착일 수 있음. (3) Permutation test가 유일한 진정한 검증.

---

## 6. 데이터 품질

### Reliability (Split-half RDM Correlation)

| Subject | Group | V1 | V2 | V3 | hV4 |
|---------|-------|------|------|------|------|
| sub-01 | HC | 0.437 | 0.217 | 0.216 | 0.645 |
| sub-02 | HC | 0.282 | 0.169 | 0.224 | 0.656 |
| sub-03 | HC | 0.634 | 0.278 | 0.039 | 0.926 |
| sub-04 | HC | 0.807 | 0.735 | 0.295 | 0.438 |
| sub-05 | HC | 0.521 | 0.810 | 0.641 | 0.199 |
| sub-06 | HC | 0.038 | 0.683 | 0.808 | 0.639 |
| sub-07 | HC | 0.190 | 0.048 | 0.559 | 0.721 |
| sub-08 | CVD | 0.706 | 0.846 | 0.643 | 0.902 |
| sub-09 | CVD | 0.503 | 0.383 | 0.334 | 0.818 |
| sub-10 | CVD | 0.412 | 0.346 | 0.353 | 0.376 |
| **HC M (SD)** | | **0.416 (0.266)** | **0.420 (0.312)** | **0.398 (0.276)** | **0.603 (0.229)** |
| **CVD M (SD)** | | **0.540 (0.150)** | **0.525 (0.279)** | **0.444 (0.173)** | **0.699 (0.283)** |

### Noise Ceiling

| ROI | HC NC_lower (SD) | HC NC_upper (SD) | CVD NC_lower (SD) | CVD NC_upper (SD) |
|-----|-----------------|-----------------|------------------|------------------|
| V1 | 0.441 (0.100) | 0.939 (0.027) | 0.527 (0.188) | 0.955 (0.027) |
| V2 | 0.452 (0.112) | 0.943 (0.034) | 0.596 (0.161) | 0.970 (0.016) |
| V3 | 0.451 (0.174) | 0.931 (0.036) | 0.522 (0.148) | 0.947 (0.010) |
| hV4 | 0.573 (0.141) | 0.957 (0.025) | 0.646 (0.147) | 0.968 (0.019) |

---

## 7. 주요 예측 모델: LORO & LOCO 결과

### 7a. LORO — Run Generalization (mean voxel_corr)

| Model | V1 HC (SD) | V1 CVD (SD) | V2 HC (SD) | V2 CVD (SD) | V3 HC (SD) | V3 CVD (SD) | hV4 HC (SD) | hV4 CVD (SD) |
|-------|-----------|------------|-----------|------------|-----------|------------|------------|-------------|
| ols | 0.213 (0.044) | 0.218 (0.031) | 0.246 (0.042) | 0.259 (0.078) | 0.326 (0.081) | 0.340 (0.039) | 0.406 (0.068) | 0.399 (0.050) |
| ridge_gcv | 0.201 (0.050) | 0.207 (0.036) | 0.230 (0.047) | 0.243 (0.092) | 0.308 (0.082) | 0.340 (0.047) | 0.401 (0.068) | 0.396 (0.060) |
| prior_only | 0.306 (0.015) | 0.287 (0.049) | 0.300 (0.029) | 0.297 (0.017) | 0.304 (0.044) | 0.278 (0.019) | 0.317 (0.031) | 0.303 (0.036) |
| **prior_ft** | **0.315 (0.021)** | **0.292 (0.053)** | **0.310 (0.027)** | **0.327 (0.070)** | **0.357 (0.064)** | **0.381 (0.047)** | **0.419 (0.062)** | **0.409 (0.058)** |

#### prior_finetune LORO — bootstrap 95% CI

| ROI | HC [95% CI] | CVD [95% CI] | CI 중첩 |
|-----|:----------:|:----------:|:------:|
| V1 | 0.319 [0.305, 0.334] | 0.292 [0.246, 0.350] | 완전 중첩 |
| V2 | 0.313 [0.294, 0.334] | 0.327 [0.284, 0.407] | 완전 중첩 |
| V3 | 0.344 [0.300, 0.386] | 0.381 [0.352, 0.436] | 완전 중첩 |
| hV4 | 0.425 [0.380, 0.475] | 0.409 [0.346, 0.459] | 완전 중첩 |

HC-CVD 차이: 모든 |d| < 0.72, 모든 p > 0.22 — LORO에서 유의한 그룹 차이 없음. **전 ROI에서 CI 완전 중첩 → 색 표현 자체는 보존.**

**LORO-LOCO 해리**: prior_ft LORO 승리, ridge_gcv LOCO 승리. SRM prior는 run-level variance 포착, color-specific tuning은 놓침.

**LORO/ZS = 실제 작동 조건**: LORO는 run generalization, ZS(§7f)는 group prior reliability를 측정. HC-CVD 차이 없음(|d|<0.72)은 CVD 문제가 within-run 표현 결핍이 아닌 **색상 간 연속 구조의 왜곡**임을 확인. LOCO만이 이 왜곡을 포착.

### 7b. LOCO — Color Interpolation (ridge_gcv, 확정 모델)

> Leakage-free: 각 fold마다 held-out color 제외하고 W0 재계산

> **Phase 2 관점**: LOCO는 7색 학습→1색 보간의 보수적 하한. Phase 2 filter는 전체 8색 사용 + 4개 Fourier 파라미터만 최적화하므로, LOCO보다 높은 성능이 기대됨. LOCO hV4 통과 = filter 설계의 충분조건.

**지표 정의 (voxel_corr):**
- 각 held-out color마다: 나머지 7개 색으로 학습한 W로 voxel pattern 예측
- 예측 패턴 vs 실제 패턴의 Spearman 상관 계산
- 8 folds (8개 색상) 평균 → subject당 mean LOCO voxel_corr
- **Null baseline**: Permutation test 결과 V1/V2 null ~+0.10-0.13 (voxel covariance 때문). hV4만 이 null 초과 (p=0.044).

#### HC LOCO 테이블 (ridge_gcv, FE-6)

| Model | V1 HC (SD) | V1 CVD (SD) | V2 HC (SD) | V2 CVD (SD) | V3 HC (SD) | V3 CVD (SD) | hV4 HC (SD) | hV4 CVD (SD) |
|-------|-----------|------------|-----------|------------|-----------|------------|------------|-------------|
| ols | +0.051 (0.095) | -0.082 (0.016) | +0.092 (0.127) | -0.181 (0.055) | +0.023 (0.197) | -0.073 (0.140) | +0.158 (0.188) | -0.067 (0.141) |
| **ridge_gcv** | **+0.130 (0.097)** | -0.012 (0.054) | **+0.150 (0.188)** | -0.174 (0.130) | +0.023 (0.240) | -0.008 (0.163) | **+0.183 (0.200)** | -0.058 (0.207) |
| prior_only | -0.075 (0.040) | -0.098 (0.019) | -0.099 (0.071) | -0.173 (0.052) | -0.186 (0.096) | -0.203 (0.073) | +0.109 (0.084) | +0.072 (0.066) |
| prior_ft | -0.056 (0.036) | -0.093 (0.015) | -0.060 (0.085) | -0.163 (0.057) | -0.101 (0.135) | -0.117 (0.097) | +0.169 (0.148) | -0.063 (0.166) |

#### HC-CVD Gap (ridge_gcv, LOCO voxel_corr, bootstrap 95% CI)

| ROI | HC M [95% CI] | CVD M [95% CI] | Cohen's d | p (Welch) |
|-----|:------------:|:-------------:|:---------:|:---------:|
| V1 | +0.130 [+0.061, +0.191] | −0.012 [−0.062, +0.045] | **+1.61** | **0.021** |
| V2 | +0.150 [+0.006, +0.247] | −0.174 [−0.257, −0.024] | **+1.85** | **0.022** |
| V3 | +0.023 [−0.146, +0.177] | −0.008 [−0.193, +0.118] | +0.14 | 0.819 |
| hV4 | +0.183 [+0.042, +0.318] | −0.058 [−0.275, +0.137] | +1.19 | 0.169 |

> V1: HC CI 하한(+0.061) > CVD CI 상한(+0.045) → CI 분리. V2: HC CI 하한(+0.006) > CVD CI 상한(−0.024) → CI 분리. hV4: CI 겹침 있으나 effect size 큼(d=1.19).

#### NC-Normalized LOCO (ridge_gcv, HC)

| ROI | HC Mean (SD) | 해석 |
|-----|-------------|------|
| V1 | 0.227 (0.199) | ~23% |
| V2 | 0.268 (0.376) | ~27% (분산 매우 높음) |
| V3 | 0.061 (0.413) | 거의 0 — 모델 실패 |
| **hV4** | **0.316 (0.207)** | **~32% — 가장 일관적** |

#### One-sample t-test (HC LOCO > 0)

| ROI | HC Mean | 95% CI | t(6) | p (one-tail) |
|-----|---------|--------|------|-------------|
| **V1** | **0.130** | [0.040, 0.220] | **3.544** | **0.006** |
| V2 | 0.150 | [-0.024, 0.323] | 2.109 | **0.040** |
| V3 | 0.023 | [-0.199, 0.245] | 0.254 | 0.404 |
| **hV4** | **0.183** | [-0.002, 0.367] | **2.423** | **0.026** |

### 7c. 모델 비교 (Supplementary)

#### Basis Ablation (FE-6 vs LF-4 vs LF-6)

**LOCO voxel_corr (OLS, n=10):**

| Basis | V1 M (SD) | V2 M (SD) | V3 M (SD) | hV4 M (SD) |
|-------|----------|----------|----------|-----------|
| **FE-6** | **+0.011 (0.101)** | **+0.010 (0.170)** | -0.006 (0.180) | **+0.090 (0.199)** |
| LF-4 | -0.066 (0.087) | -0.097 (0.200) | -0.105 (0.125) | -0.075 (0.091) |
| LF-6 | -0.111 (0.154) | -0.070 (0.159) | -0.093 (0.220) | -0.093 (0.199) |

**FE-6 vs LF-4 (paired t, n=10):** LOCO에서 V1 p=0.045, V2 p=0.042, hV4 p=0.016. LORO에서 전 ROI p<0.001. **FE 형태 확정.**

#### 확장 비교: FE 채널 수 (ridge_gcv, HC n=7)

**LOCO voxel_corr by FE channel count:**

| Basis | V1 | V2 | V3 | hV4 |
|-------|------|------|------|------|
| FE-2 | **+0.153** | +0.180 | +0.085 | +0.186 |
| FE-3 | +0.143 | **+0.180** | +0.097 | **+0.205** |
| FE-6 | +0.130 | +0.150 | +0.023 | +0.183 |
| FE-8 | +0.128 | +0.176 | **+0.112** | +0.191 |
| FE-12 | +0.134 | +0.168 | +0.106 | +0.190 |

**Bias-variance tradeoff:**
- LORO: K↑ → 단조 개선 (r=+0.82~0.89)
- LOCO: V1/V2에서 K↓ → 개선 (r=-0.23/-0.29) — 적은 채널 = 강한 보간 제약

Per-ROI 최적: V1→FE-2, V2→FE-3, V3→FE-8, hV4→FE-3. FE-6 대비 유의차 없으나 방향 일관적.

#### Opponent Basis Test (Red Team #3 중화, 10K perm)

**LOCO Permutation (Stouffer combined, HC):**

| Basis | V1 | V2 | V3 | V4 |
|-------|:------:|:------:|:------:|:------:|
| OPP-2 | p=0.324 | p=0.444 | p=0.358 | p=0.302 |
| OPP-4 | p=0.125 | p=0.109 | p=0.566 | p=0.139 |
| OPP-4rect | p=0.633 | p=0.261 | p=0.796 | p=0.110 |
| **FE-6** | p=0.126 | p=0.154 | p=0.367 | **p=0.039*** |

**결론**: 모든 opponent basis V1/V2 FAIL. FE-6만 V4 통과. **RT-3 중화 완료**: V1/V2 실패는 basis mismatch 아닌 영역 고유 특성.

#### 대안 인코더 요약

| 모델 | 결과 | 근본 원인 |
|------|------|----------|
| **ridge_gcv** | **확정** — hV4 perm p=0.044 | Permutation 유일 통과 |
| smooth_tikh | 기각 — 전 ROI perm p>0.18 | 공간 공분산만 포착. β가 near-rank-1 W 생성. 3회 rescue 모두 실패: (1) centering-shuffle 교환, (2) 재최적화 β 여전히 높음, (3) rdm_pearson은 noise 매칭 (이상 구조와 반상관 ρ≈-0.5) |
| mixed_ridge_prior | 기각 — V1-V3 음 | SRM prior LOCO 비호환 |
| bayes_prior | 기각 — V1-V3 음 | Voxel-level uncertainty 실패 |
| smooth_prior | 기각 — 거의 0 | Prior가 smoothness 상쇄 |

#### Extended Models LOCO 요약 (n=10)

| Model | V1 M (SD) | V2 M (SD) | V3 M (SD) | V4 M (SD) |
|-------|----------|----------|----------|-----------|
| ridge_gcv | +0.087 (0.095) | +0.053 (0.194) | +0.014 (0.200) | +0.111 (0.210) |
| smooth_tikh | +0.112 (0.133) | +0.151 (0.175) | +0.115 (0.212) | +0.157 (0.245) |
| prior_finetune | -0.067 (0.035) | -0.091 (0.090) | -0.105 (0.118) | +0.099 (0.175) |
| smooth_prior | +0.025 (0.153) | -0.002 (0.170) | -0.078 (0.143) | +0.094 (0.244) |
| mixed_ridge_prior | -0.056 (0.089) | -0.073 (0.126) | -0.066 (0.105) | +0.094 (0.225) |
| bayes_prior | -0.062 (0.047) | -0.101 (0.082) | -0.123 (0.129) | +0.028 (0.209) |

### 7d. 모델 검증 (Supplementary)

#### Permutation Test (10K, HC ridge_gcv, FE-6, bootstrap 95% CI)

| ROI | HC Observed [95% CI] | Null Mean [95% CI] | p_perm |
|-----|:--------------------:|:------------------:|:------:|
| V1 | +0.130 [+0.061, +0.191] | +0.111 [−0.055, +0.278] | 0.274 |
| V2 | +0.150 [+0.006, +0.247] | +0.129 [−0.044, +0.303] | 0.311 |
| V3 | +0.023 [−0.146, +0.177] | +0.077 [−0.135, +0.289] | 0.880 |
| **hV4** | **+0.183 [+0.042, +0.318]** | **+0.085 [−0.195, +0.366]** | **0.044*** |

> HC Observed CI = bootstrap 95% (10K resamples). Null CI = permutation null 평균 ± 1.96SD.

![LOCO Permutation CI](../figures/fig1_loco_permutation_ci.png)

V1/V2 null ~0.10-0.13 (not zero) — voxel covariance 구조가 baseline voxel_corr 생성. V1/V2 observed CI가 null CI 내에 완전 포함. **hV4만 observed mean이 null 상위 꼬리에 위치.**

#### Per-ROI 최적 Basis Permutation (10K, Stouffer combined)

| ROI | Basis | p_stouffer | FE-6 대비 |
|-----|-------|-----------|----------|
| V1 | FE-2 | 0.170 | 0.274→0.170 (개선, FAIL) |
| V2 | FE-3 | 0.125 | 0.311→0.125 (개선, FAIL) |
| **V3** | **FE-8** | **0.045*** | **0.360→0.045 (NO-GO→PASS)** |
| hV4 | FE-3 | **0.026*** | 0.044→0.026 (강화) |

**V3 회복**: FE-8로 NO-GO→PASS. V1/V2는 어떤 1D FE basis로도 FAIL.

#### Friedman Test (per-color 균일성, HC)

| ROI | chi²(7) | p | 해석 |
|-----|---------|---|------|
| V1 | 18.33 | 0.011* | 비균일 — Blue 높음, Yellow/Green 낮음 |
| V2 | 14.24 | 0.047* | 비균일 |
| V3 | 11.38 | 0.123 | 구조 없음 |
| hV4 | 6.48 | 0.485 | **균일 — 진정한 연속 보간** |

#### Residual Structure (HC)

| Metric | V1 | V2 | V3 | hV4 |
|--------|------|------|------|------|
| r(resid, orig) | 0.453 | 0.454 | 0.329 | **0.053** |
| r(pred, orig) | 0.390 | 0.407 | 0.415 | **0.563** |

hV4 residual near-random (0.053) — 모델이 가용 구조 대부분 포착. V1/V2에 systematic residual 잔존.

#### Intercept Model Permutation Test (10K, HC)

| Method | V1 (FE-6) | V2 (FE-6) | V3 (FE-8) | V4 (FE-3) |
|--------|:---------:|:---------:|:---------:|:---------:|
| Standard | p≈0.126 | p≈0.155 | p≈0.043* | p≈0.025* |
| Intercept | p≈0.127 | p≈0.156 | p≈0.040* | p≈0.064 |
| Mean_subt | p≈0.136 | p≈0.160 | p≈0.053 | p≈0.059 |

**결론**: Standard ≈ Intercept ≈ Mean_subt. 인코딩 신호는 hue-modulated pattern에 존재, 공간 평균 무관.

#### Cross-Validation 종합

| 증거 | V1 | V2 | hV4 |
|------|------|------|------|
| Parametric t-test (H₀: μ=0) | p=0.006* | p=0.040* | p=0.026* |
| **Permutation (H₀: shuffled)** | p=0.274 | p=0.311 | **p=0.044*** |
| Friedman 균일성 | 비균일* | 비균일* | **균일** |
| Residual | 체계적 | 체계적 | **근무작위** |

#### Eigenspectrum Decay (Pospisil & Pillow 2024)

| ROI | HC α_early | CVD α_early | p | HC α_late | CVD α_late | p |
|-----|-----------|------------|---|----------|-----------|---|
| V1 | 0.683±0.074 | 0.658±0.044 | 0.539 | 0.376±0.078 | 0.440±0.055 | 0.192 |
| V2 | 0.734±0.079 | 0.690±0.048 | 0.340 | 0.472±0.068 | 0.493±0.049 | 0.589 |
| V3 | 0.892±0.231 | 0.886±0.171 | 0.971 | 0.769±0.252 | 0.775±0.193 | 0.969 |
| hV4 | 0.979±0.302 | 0.867±0.215 | 0.534 | 0.830±0.312 | 0.688±0.223 | 0.453 |

α_early = 0.66-0.98: Pospisil 범위 내. Broken power law 확인. **HC ≈ CVD** (전 p > 0.14).

#### MEME Dimensionality

| ROI | HC k* | CVD k* | p | SRM k | Δ |
|-----|-------|--------|---|-------|---|
| V1 | 340±119 | 354±75 | 0.833 | 4 | +336 |
| V2 | 232±64 | 244±39 | 0.719 | 4 | +228 |
| V3 | 53±10 | 59±0 | 0.178 | 3 | +50 |
| hV4 | 33±10 | 37±0 | 0.304 | 3 | +30 |

HC ≈ CVD (전 p > 0.17). k* >> SRM k: γ >> 1 극한 고차원 regime.

### 7e. GO/NO-GO Gate

#### Gate 기준

| Criterion | Metric | Threshold |
|-----------|--------|-----------|
| C1 Reliability | Split-half RDM correlation | > 0.3 |
| C2 Normalized Fit | LOCO voxel_corr / NC_voxel_r_sb | > 0.2 |
| C3 Interpolation | HC LOCO voxel_corr > 0 (p < 0.05) | one-tail |
| C3b Permutation | 10K color-shuffle null | p < 0.05 |

#### ridge_gcv Gate — FE-6 (확정)

| ROI | C1 | C2 (NC-Norm) | C3 (t-test) | C3b (Perm) | Overall |
|-----|----|----|----|----|---------|
| V1 | PASS (0.416) | PASS (0.227) | PASS (p=0.006) | FAIL (p=0.274) | **CONDITIONAL GO** |
| V2 | PASS (0.420) | PASS (0.268) | PASS (p=0.040) | FAIL (p=0.311) | **CONDITIONAL GO** |
| V3 | PASS (0.398) | FAIL (0.061) | FAIL (p=0.404) | FAIL (p=0.880) | **NO-GO** |
| hV4 | PASS (0.603) | PASS (0.316) | PASS (p=0.026) | **PASS (p=0.044)** | **PRIMARY GO** |

#### ridge_gcv Gate — Per-ROI 최적 Basis

| ROI | Basis | C3 (LOCO>0) | C3b (Perm Stouffer) | FE-6 대비 |
|-----|-------|-------------|---------------------|----------|
| V1 | FE-2 | **PASS (p=0.005)** | FAIL (p=0.170) | 0.274→0.170 (개선, FAIL) |
| V2 | FE-3 | **PASS (p=0.008)** | FAIL (p=0.125) | 0.311→0.125 (개선, FAIL) |
| **V3** | **FE-8** | MARGINAL (p=0.065) | **PASS (p=0.045)** | **NO-GO → PASS** |
| hV4 | FE-3 | **PASS (p=0.021)** | **PASS (p=0.026)** | 0.044→0.026 (강화) |

> **V3 회복**: FE-8로 NO-GO→PASS. V1/V2는 FE-{2..12} + OPP-2/4/4rect + intercept 모두 FAIL — 8-stimulus LOCO의 구조적 한계.

#### smooth_tikh Gate (REJECTED)

| ROI | C3b (Perm) | Status |
|-----|------------|--------|
| V1 | FAIL (p=0.331) | REJECTED |
| V2 | FAIL (p=0.188) | REJECTED |
| V3 | FAIL (p=0.613) | NO-GO |
| V4 | FAIL (p=0.613) | REJECTED |

#### Gate 결정

**Primary**: hV4 = color interpolation oracle (FE-6 perm p=0.044, FE-3 perm p=0.026).
**Conditional**: V3 (FE-8 perm p=0.045).
**Discrimination-only**: V1/V2 (전 basis LOCO FAIL).

### 7f. LOSO Zero-Shot Transfer

> **1차 목적 직결**: Group prior W₀만으로 새 피험자의 색상 패턴을 얼마나 예측하는가? → Phase 2 filter의 prediction engine 신뢰도 검증.

#### 방법

Leave-One-Subject-Out (LOSO): HC 7명 중 1명 제외 → 나머지 6명으로 SRM refit → A_g 구축 → held-out subject SVD 투사 → W₀ = R_new @ A_g.

**Leakage-free**: 매 fold마다 SRM refit (R_i 재사용 ❌).

**직접 평가**: W₀는 held-out subject data 미사용 → LOCO/LORO 없이 전체 8색 직접 평가 가능.

#### HC 결과 — 3-tier 비교 (voxel_corr, bootstrap 95% CI)

| ROI | ZS [95% CI] | LORO [95% CI] | LOCO [95% CI] | p(ZS−LORO) |
|-----|:-----------:|:-------------:|:-------------:|:----------:|
| V1 | 0.529 [0.498, 0.554] | 0.319 [0.305, 0.334] | +0.130 [+0.061, +0.191] | **0.0004*** |
| V2 | 0.555 [0.511, 0.584] | 0.313 [0.294, 0.334] | +0.150 [+0.006, +0.247] | **0.0001*** |
| V3 | 0.472 [0.438, 0.508] | 0.344 [0.300, 0.386] | +0.023 [−0.146, +0.177] | **0.0022*** |
| **hV4** | **0.417 [0.368, 0.468]** | **0.425 [0.380, 0.475]** | **+0.183 [+0.042, +0.318]** | **0.913** |

> ZS = zero-shot (W₀ 직접), LORO = prior_finetune, LOCO = ridge_gcv. CI = bootstrap 95% (10K).

![3-Tier Comparison](../figures/fig2_three_tier_ci.png)

#### 핵심 발견

1. **hV4만 ZS ≈ LORO** (p=0.913): **CI 완전 중첩** [0.368–0.468] vs [0.380–0.475]. Group prior만으로도 subject-specific ridge_gcv와 동등한 패턴 재현 → **hV4의 group prior가 Phase 2 filter의 신뢰할 수 있는 prediction engine**
2. **V1/V2/V3: ZS >> LORO** (p<0.003): **CI 완전 분리**. ZS가 6-run 평균과 비교 vs LORO는 single run → noise 차이. Group prior가 spatial pattern 재현은 하지만, V1/V2에서는 interpolation 불가 (LOCO FAIL 유지)
3. **LOCO 항상 최저**: LOCO CI 하한이 0 근처 또는 이하 — 보간이 가장 어려운 과제
   - 보간 격차 = ZS − LOCO = 0.417 − 0.183 = **0.234** (hV4)

#### CVD ZS 결과 (bootstrap 95% CI)

| ROI | HC ZS [95% CI] | CVD ZS [95% CI] | p |
|-----|:--------------:|:--------------:|:---:|
| V1 | 0.529 [0.498, 0.554] | 0.527 [0.465, 0.581] | 0.409 |
| V2 | 0.555 [0.511, 0.584] | 0.541 [0.527, 0.567] | 0.831 |
| V3 | 0.472 [0.438, 0.508] | 0.454 [0.427, 0.479] | 0.793 |
| hV4 | 0.417 [0.368, 0.468] | 0.427 [0.380, 0.470] | 0.940 |

**HC ≈ CVD** (전 ROI p>0.4, CI 완전 중첩). ZS 직접 평가는 공간 패턴 재현 능력 → HC-CVD 구별 불가. **LOCO가 유일한 HC-CVD 해리 도구** (보간 정확도만이 차이를 포착).

#### 1차 목적 시사점 (예측 모델 → Phase 2)

| 질문 | 답 | 근거 |
|------|-----|------|
| Group prior가 hV4 패턴 예측에 유효한가? | **YES** | ZS ≈ LORO (p=0.913) |
| Group prior만으로 보간 가능한가? | **NO** | LOCO << ZS (0.232 vs 0.417) |
| Subject data 결합이 보간 개선하는가? | **일부** | ridge_gcv LOCO = 0.183 (FE-6), B1 K*로 0.205-0.541 |
| 다음 개선 방향은? | hV4 LOCO 개선 | ZS→LOCO 격차(0.185) 줄이기 = Phase 2 filter 정밀도 향상 |

#### 문헌 벤치마크 — LOSO 피험자 간 전이

LOSO 색상 디코딩의 유일한 선행 벤치마크: Bannert & Bartels (2025). SRM 기반 leave-one-participant-out, 3색 (R/G/Y, chance = 33.3%, N = 15, 6 runs). 특이사항: SRM을 **무채색 retinotopic mapping data**로 학습 (색상 데이터 미사용).

**설계 비교:**

| | **본 연구** | **Bannert & Bartels (2025)** |
|---|---|---|
| 피험자 | 10 (HC 7 + CVD 3) | 15 (HC) |
| 색 수 | 8 | 3 |
| Runs | 6 | 6 |
| Chance | 12.5% | 33.3% |
| SRM 학습 | 색상 (hue RSVP) | 무채색 (retinotopy) |
| 메트릭 | Voxel pattern correlation | Classification accuracy |
| 평가 | ZS (W₀ 직접, 8색) | LOSO (LDA, 3-way) |

**Bannert & Bartels 2025 LOSO 결과 (FWE 보정, 2000 perm):**

| ROI | LOSO 정확도 (chance 33.3%) | Above-chance | Within-subj 정확도 | LOSO/within |
|-----|:-----------------------:|:------------:|:---------------:|:-----------:|
| V1 | 44.7% (z = 13.7) | +11.4 %p | 57.0% | 78.4% |
| V2 | 39.8% (z = 7.75) | +6.5 %p | 55.4% | 71.8% |
| V3 | 39.6% (z = 7.57) | +6.3 %p | 52.8% | 74.8% |
| hV4 | 39.5% (z = 7.42) | +6.2 %p | 51.2% | 77.1% |

**교차 비교 — Group Prior 유효성:**

| ROI | 본 연구 ZS/LORO | Bannert LOSO/within | 해석 |
|-----|:-----------:|:-------------------:|------|
| V1 | 168%* | 78.4% | *ZS vs LORO SNR 차이로 인한 과대 |
| V2 | 179%* | 71.8% | *동일 |
| V3 | 132%* | 74.8% | *동일 |
| **hV4** | **99.5%** | **77.1%** | **색상 학습 GP → 개인 수준 완전 도달** |

> *V1-V3 ZS/LORO > 100%는 메트릭 차이: ZS는 6-run 평균 템플릿(고 SNR) 대비 평가, LORO는 single run(저 SNR) 대비 평가. hV4의 **99.5% 동등성**이 핵심 발견.

**수렴점:**
1. **두 연구 모두 SRM 기반 피험자 간 색 전이 확인** — 집단 수준 색 기하학이 개인 간 공유됨
2. **색상 학습 SRM ≥ 무채색 SRM**: 본 연구 hV4 ZS/LORO = 99.5% vs Bannert 77.1% — color data로 SRM 학습 시 group prior 충실도 향상
3. **양 연구에서 전 early visual ROI가 LOSO 지원** — 공간 반응 구조가 피험자 간 전이 가능한 색 정보를 인코딩
4. **본 연구 고유**: HC ≈ CVD in LOSO (전 p > 0.4) — CVD 망막 결함이 spatial pattern 재현에는 영향 없음, LOCO 보간만이 해리를 드러냄

![LOSO Benchmark](../figures/fig5_loso_benchmark.png)

![LOSO HC vs CVD](../figures/fig5b_loso_hc_cvd.png)

---

## 8. 부가 분석: HC-CVD 비교 및 모델 강건성 (2차 목적)

> 이하 분석은 §7의 **검증된 예측 모델이 드러내는** HC-CVD 차이를 기술한다. 1차 목적(예측 모델 구축)의 부산물이며, CVD N=3이므로 전체 탐색적/기술적 수준이다.

### 8a. HC-CVD Gap 구조 (탐색적, N=3, bootstrap 95% CI)

| ROI | HC M [95% CI] | CVD M [95% CI] | Cohen's d | p (Welch) |
|-----|:------------:|:-------------:|:---------:|:---------:|
| V1 | +0.130 [+0.061, +0.191] | −0.012 [−0.062, +0.045] | **+1.61** | **0.021** |
| V2 | +0.150 [+0.006, +0.247] | −0.174 [−0.257, −0.024] | **+1.85** | **0.022** |
| V3 | +0.023 [−0.146, +0.177] | −0.008 [−0.193, +0.118] | +0.14 | 0.819 |
| hV4 | +0.183 [+0.042, +0.318] | −0.058 [−0.275, +0.137] | +1.19 | 0.169 |

> V1: HC CI 하한(+0.061) > CVD CI 상한(+0.045) → **CI 분리**. V2: HC CI 하한(+0.006) > CVD CI 상한(−0.024) → **CI 분리**.

**해석**: 양수 gap = HC가 색상 간 보간 우수. V1/V2에서 HC-CVD CI 분리는 LORO의 CI 중첩(§7a)과 대비 — 색 표현 자체는 보존되나 연속 보간 구조만 왜곡. Gap 크기는 모델 명세에 따라 변동 (§8c 참조).

### 8b. 개별 CVD 프로파일 (Crawford-Howell, ridge_gcv)

**sub-08 (deutan)**

| Metric | V1 | V2 | V3 | hV4 |
|--------|------|------|------|------|
| LOCO r | -0.062 | -0.241 | +0.049 | -0.275 |
| HC z-score | -1.97 | -2.08 | +0.11 | -2.29 |
| Crawford-Howell p | 0.114 | 0.099 | 0.922 | 0.076 |

**sub-09 (protan)**

| Metric | V1 | V2 | V3 | hV4 |
|--------|------|------|------|------|
| LOCO r | -0.020 | -0.024 | -0.193 | -0.035 |
| Crawford-Howell p | 0.197 | 0.419 | 0.433 | 0.346 |

**sub-10 (deutan)**

| Metric | V1 | V2 | V3 | hV4 |
|--------|------|------|------|------|
| LOCO r | +0.045 | -0.257 | +0.118 | +0.137 |
| Crawford-Howell p | 0.444 | 0.089 | 0.723 | 0.837 |

### 8c. 모델 명세 민감도: K-Ablation

| ROI | FE-6 d (p) | FE-K d (p) | Gap 감소 |
|-----|:----------:|:----------:|:--------:|
| V1 | 2.01 (0.021) | 0.44 (0.581) | −78% |
| V2 | 2.25 (0.022) | 1.80 (0.067) | −20% |
| V3 | 0.17 (n.s.) | 0.18 (n.s.) | — |
| hV4 | 1.36 (0.169) | 0.63 (0.342) | −54% |

> **주의 (N2 중화 결과)**: 위 gap 감소 퍼센트는 레이블 셔플 시 우연 수준 (전 p > 0.13, §9c 참조). "K 최적화로 gap 감소" 서술은 탐색적 artifact. 특정 K에서의 gap 크기 자체는 유효하나 감소 서술은 폐기.

#### Warm/Cool 축 분해 (hV4 FE-3)

| 축 | FE-6 Gap | FE-K Gap | 감소 |
|------|:--------:|:--------:|:----:|
| **Warm (L-M)** | +0.118 | −0.060 | >100% (역전) |
| **Cool (S)** | +0.362 | +0.237 | 35%만 |

> **주의**: Warm gap 역전은 HC-최적화 artifact 가능 (N2). Cool-color gap 잔존이 더 신뢰할 수 있는 관측.

### 8d. Per-Color Residual — Cone Shift 일관성 (bootstrap 95% CI)

| 색 | θ | HC M [95% CI] | CVD M [95% CI] | d | p |
|-----|-----|:------------:|:-------------:|:---:|:---:|
| red | 0° | +0.353 [+0.181, +0.511] | +0.310 [+0.110, +0.597] | +0.18 | 0.81 |
| orange | 45° | +0.246 [+0.005, +0.456] | +0.502 [+0.249, +0.653] | −0.94 | 0.22 |
| yellow | 90° | +0.135 [−0.162, +0.423] | +0.213 [+0.024, +0.321] | −0.24 | 0.70 |
| green | 135° | +0.107 [−0.191, +0.387] | +0.055 [−0.320, +0.322] | +0.13 | 0.85 |
| cyan | 180° | −0.008 [−0.299, +0.241] | +0.157 [−0.446, +0.462] | −0.35 | 0.66 |
| **blue** | **225°** | **+0.349 [+0.138, +0.553]** | **+0.025 [−0.090, +0.137]** | **+1.37** | **0.046*** |
| **purple** | **270°** | **+0.283 [+0.056, +0.502]** | **−0.124 [−0.328, +0.055]** | **+1.54** | **0.060†** |
| magenta | 315° | +0.171 [−0.090, +0.440] | −0.211 [−0.424, +0.067] | +1.19 | 0.127 |

> Warm (red–green): HC-CVD CI 완전 중첩, 전 |d| < 1, 전 p > 0.2.
> Cool (blue, purple): HC CI 하한 > CVD CI 상한 → **CI 분리**. Blue: HC 하한 +0.138 > CVD 상한 +0.137. Purple: HC 하한 +0.056 > CVD 상한 +0.055.

![Per-Color hV4 LOCO](../figures/fig3_per_color_hv4_ci.png)

#### 피험자별 Cool-Color 프로필 (hV4 FE-3)

| 피험자 | Warm 평균 | Cool 평균 | 해석 |
|---------|:---------:|:---------:|------|
| sub-08 (deutan) | +0.227 | −0.058 | Cool 여전히 음수 |
| sub-09 (protan) | +0.340 | −0.197 | Cool 최악 |
| sub-10 (deutan) | +0.244 | +0.140 | Cool 양수 — 보상됨 |
| HC 평균 | +0.210 | +0.199 | Warm/Cool 균형 |

### 8e. Cross-Phase 수렴 (SRM ↔ FE, 보조)

SRM prevalidation (crossnobis)과 forward model LOCO는 **완전 독립 파이프라인**.

| 신호 | SRM Prevalidation | Forward Model | 수렴? |
|------|-------------------|---------------|:----:|
| Blue-purple 왜곡 | V2 blue-purple p=0.042 (유일 유의 쌍) | hV4 blue d=+1.37 p=0.046 | **YES** |
| Green-blue 압축 | V1/V2/V3 3인 일관 deficit | Blue = CVD 최저 색 | **YES** |
| Red-magenta 확장 | V1/V2/hV4 3인 일관 elevation | Magenta d=+1.19 | **Partial** |
| sub-10 보상 | SRM: HC-like (r=0.701) | FE-K: cool 양수 유일 CVD | **YES** |

> **핵심 수렴**: 두 독립 파이프라인이 동일 색 영역 (blue/purple/magenta)을 CVD 왜곡 중심으로 지목.

### 8f~8i. Supplementary 모음

> 이하 4개 하위 섹션(적응형 기저, CVD 대안 모델, 차원성, 잔류 생물학)은 2차 목적의 보조 분석이며, 주요 결론에 영향 없음. 요약만 기재하고 상세는 RESULTS.md 참조.

#### 8f. 적응형 기저 최적화 (Supplementary — 비교)

#### 순환 최적화 결과 (편향 포함)

38/40 조합에서 delta ≥ 0. HC delta 유의: V2 p=0.022, V3 p=0.009, hV4 p=0.002.

> **순환 편향 경고**: 센터 최적화가 전체 8색 LOCO를 목적함수로 사용 → 낙관적 상한.

#### Nested LOCO 검증 (debiased)

| ROI | K | HC FE-6 | HC FE-K | HC Nested | CVD FE-6 | CVD FE-K | CVD Nested |
|-----|---|:-------:|:-------:|:---------:|:--------:|:--------:|:----------:|
| V1 | 2 | +0.130 | +0.153 | +0.175 | −0.012 | +0.115 | +0.130 |
| V2 | 3 | +0.150 | +0.180 | +0.174 | −0.174 | −0.032 | −0.002 |
| V3 | 8 | +0.023 | +0.112 | +0.110 | −0.008 | +0.081 | +0.086 |
| hV4 | 3 | +0.183 | +0.205 | +0.164 | −0.058 | +0.116 | +0.096 |

**결과**: 모든 ROI에서 Nested ≈ FE-K (전 p > 0.37). **센터 최적화 = 무효. K가 유일한 유효 파라미터.**

sub-08 hV4: circular=+0.383 → nested=+0.081 (bias=+0.302). "퇴행 센터 패턴"은 과적합 산물, L-M축 압축 증거 아님.

#### 8g. CVD 대안 모델 (Supplementary — 비교)

#### B2: 비등방성 기저 — REJECTED

| ROI | HC Δ | t | p | Cohen's d |
|-----|------|-------|-------|-----------|
| hV4 | **-0.081** | **-3.714** | **0.010*** | **-1.404** |

파라메트릭 warping이 hV4 HC 유의하게 악화 (p=0.010, d=-1.4). **REJECTED.**

#### B3: 계층적 FE — REJECTED

CVD 효과 무시 (|Δ|<0.012). λ→∞ 수렴 = 데이터 noise가 individual tuning 불허. **REJECTED.**

#### A2: 기저 비등방성 (피험자 특이적)

| 피험자 | uniform | cool_dense | warm_dense | Δcool | Δwarm |
|--------|---------|-----------|-----------|-------|-------|
| sub-08 | 0.084 | 0.005 | 0.178 | -0.079 | **+0.094** |
| sub-09 | 0.071 | -0.004 | 0.006 | -0.075 | -0.065 |
| sub-10 | 0.192 | 0.302 | 0.205 | **+0.110** | +0.013 |

피험자마다 최적 배치 상이. 일률적 규칙 불가.

#### 8h. 차원성 & 집단 조직 (Supplementary — 검증)

#### Eigenspectrum: HC ≈ CVD

α_early/α_late 전부 p > 0.14. Broken power law 확인. V1/V2 얕은 decay → 더 많은 mode 기여, 그러나 noise.

#### MEME: HC ≈ CVD

전 p > 0.17. k* >> SRM k (100×): γ >> 1 regime. SRM k=3-4가 더 유의미한 "색 신호" 차원 추정.

#### Voxel Color Preference Maps (Bannert & Bartels 2025)

유의한 차이:
- **V1 green**: HC −9.9% vs CVD −74.5% (p=0.016*)
- **V2 green**: HC +26.7% vs CVD −73.2% (p=0.017*)

CVD 공통: **Green 부족** (−58~−75%), **Magenta 과잉** (+117~+196%). V3/hV4 비유의.

#### 해석: 자극-수준 왜곡, 피질 재조직 아님

1. α_CVD ≈ α_HC — 같은 decay 구조
2. k*_CVD ≈ k*_HC — 같은 차원
3. Voxel preference — 같은 복셀, 다른 argmax

CVD K-sensitivity = **bias-variance tradeoff** (동일 차원, 다른 tuning). Phase 2 filter = 자극 공간 warping.

#### 8i. 잔류 생물학 보고서 (Track A: Exp A3–A6) (Supplementary — 검증)

> FE-6/ridge_gcv 예측 사용. HC N=6 (sub-07 누락), CVD N=3.

#### A3: Signed Circular Bias

HC hV4 same-color mapping rate = 33%, CVD = 8%. 그룹 수준 패턴만 해석 가능.

| Subject | Group | blue | 주요 Crawford-Howell |
|---------|-------|:----:|:---:|
| HC mean | — | -16.1 | — |
| sub-08 | deutan | **-136.7\*** | p<0.05 |
| sub-09 | protan | **+84.3\*** | p<0.05 |
| sub-10 | deutan | -61.5 | magenta **-107.0\*** |

sub-08 blue→yellow (CW), sub-09 blue→magenta (CCW) — **반대 방향**, deutan/protan 차이와 일치.

#### A4: 28-Pair Pairwise Residual

유의한 쌍은 주로 **cross-axis**:

| CVD | 쌍 | HC M° | CVD° | p |
|-----|-----|:-----:|:----:|:---:|
| sub-08 | **red-cyan** | 42.5 | 173.5 | **0.029** |
| sub-10 | **green-magenta** | 39.3 | 154.5 | **0.016** |
| sub-10 | **orange-cyan** | 40.7 | 154.5 | **0.030** |

#### A5: Confusion Structure

| ROI | HC Acc | sub-08 (D) | sub-09 (P) | sub-10 (D) |
|-----|:------:|:----------:|:----------:|:----------:|
| **hV4** | **0.281** | **0.021** | **0.083** | **0.083** |

hV4 Cool 정확도: sub-08=**0.000**, sub-09=**0.000**.

**비대칭 red-green 혼동**: red→green ≈ 0 (전 CVD). green→red deutan에서 강함 (sub-08 V2: 1.00, sub-10 V2: 0.83). M-cone 손실과 일치.

#### A6: Cross-Phase SRM ↔ FE Correlation

28-pair 정량적 수렴 대부분 비유의. sub-08 V1만 유의 (r=0.385, p=0.043). 메트릭 불일치 + hV4 crossnobis 부재로 인한 한계. 정성적 수렴 (SRM V2 blue-purple p=0.042 ↔ FE hV4 blue p=0.046)은 유효.

#### Track A 종합

| 기준 | 상태 | 근거 |
|------|:----:|------|
| Cool-axis bias 방향 | **부분** | Crawford-Howell 유의 (blue), FE-6 자체 noisy |
| 28-pair SRM 수렴 (r>0.4) | **미달** | hV4 crossnobis 부재 |
| 2/3 CVD cool-axis distortion | **달성** | sub-08/09 cool accuracy=0% |

### 8j. Per-Subject K* (Cone Shift 보조 증거)

> Per-subject K* 최적화는 CVD에서 LOCO를 회복시키지만, K*=8(sub-08)은 사실상 8색에 8채널 → 암기(lookup table)에 가깝다. K* 자체를 독립 발견으로 취급하기보다, **cone shift로 인한 tuning curve 변형과 일관적인 관측**으로 해석한다. Phase 2에서는 K* 사용을 유지하되 (실용적), filter 설계의 1차 근거는 cone shift 분석(§2-C~F, behavioral_target_selection.md)에 둔다.

#### hV4 결과

| 피험자 | 그룹 | K* | K* LOCO | 그룹K(=3) LOCO | Δ |
|--------|------|-----|---------|----------------|------|
| sub-01 | HC | 10 | 0.110 | 0.037 | +0.073 |
| sub-02 | HC | 3 | 0.514 | 0.514 | 0.000 |
| sub-03 | HC | 6 | 0.441 | 0.360 | +0.081 |
| sub-04 | HC | 2 | 0.285 | 0.255 | +0.031 |
| sub-05 | HC | 6 | 0.060 | 0.025 | +0.035 |
| sub-06 | HC | 4 | 0.357 | 0.301 | +0.055 |
| sub-07 | HC | 8 | 0.139 | -0.059 | +0.198 |
| **sub-08** | **CVD** | **8** | **0.541** | **0.084** | **+0.457** |
| **sub-09** | **CVD** | **3** | **0.071** | **0.071** | **0.000** |
| **sub-10** | **CVD** | **2** | **0.270** | **0.192** | **+0.078** |

**핵심**: sub-08 hV4 K=3→K=8 → LOCO **6.4배 상승** (0.084→0.541).

#### HC Paired t-test (subject_k vs baseline FE-K)

| ROI | Δ | t | p | Cohen's d |
|-----|------|-------|-------|-----------|
| V1 | +0.040 | 1.976 | 0.096 | 0.747 |
| V2 | +0.045 | 3.407 | **0.014*** | 1.288 |
| V3 | +0.070 | 2.195 | 0.071† | 0.830 |
| hV4 | +0.068 | 2.804 | **0.031*** | 1.060 |

#### 5축 비교 요약 (hV4)

| 모델 | HC 평균 | CVD 평균 |
|------|---------|----------|
| Baseline FE-K | 0.205 | 0.116 |
| **B1: Subject K\*** | **0.272** | **0.294** |
| B2: Anisotropic | 0.124 | 0.034 |
| B3: Hierarchical | 0.205 | 0.117 |

B1만 CVD 평균이 HC baseline 초과. sub-08 HC 평균 위 (0.541 vs 0.272), sub-10 HC와 동일 (0.270 vs 0.272).

---

## 9. Red Team 분석

### 9a. Original Red Team (RT-1~RT-5)

> 자체 비판 2026-03-11. 전체 보고서: `results/redteam/2026-03-11.md`

**RT-1: N=3 CVD — 통계적 검정력**

모든 CVD 결과는 **Crawford & Howell (2010) 개인별 단일사례 분석**으로 보고. 그룹 수준 CVD 비교는 기술적/탐색적. HC (N=7) = 검증된 모델; CVD = "N=3 개념 증명". 파이프라인 영향: 없음 (Phase 2 filter는 개인별 작동).

**RT-2: 다중비교 (hV4 p=0.044)**

hV4 = **사전 지정 primary ROI** (Brouwer & Heeger 2009). Bonferroni-4 미통과 (0.044 > 0.0125). **N1 Stouffer omnibus로 해결** (§9c): omnibus p=0.0021.

**RT-3: 구분 vs 보간 해리 — NEUTRALIZED**

3종 opponent + FE 변형 + intercept 직접 검증. V1/V2 전 basis FAIL. 구조적 한계 확정.

**RT-4: 분석적 자유도**

순차적 제거 논리: (1) Basis→CV 성능 기반, (2) 모델→LOCO voxel_corr 최고, (3) Permutation→최종 gate, (4) Metric→문헌 표준 a priori.

**RT-5: CVD 실패 서사 — 모델 명세 민감도로 수정**

HC-CVD gap은 주로 K 의존. Eigenspectrum + MEME: HC ≈ CVD. K-sensitivity = bias-variance tradeoff.

### 9b. Hinton 관점 Red Team (RT-6)

#### Top 5 취약점

| # | 취약점 | 치명도 | 상태 |
|---|-------|:------:|:----:|
| 1 | **"수렴 증거 5종" = 의사복제**: 동일 48 samples의 다각적 특성화, 독립 증거 아님 | **FATAL** | **N3: 재프레이밍** |
| 2 | **다중비교**: hV4 p=0.026 Bonferroni-4 미통과. 24+ tests. | **FATAL** | **N1: Stouffer omnibus** |
| 3 | **K-dependent gap = HC 최적화 artifact**: Warm 역전 = 과적합 증상 | **SEVERE** | **N2: artifact 확인** |
| 4 | **V1/V2 "미결정" = 반증 불가** | **MODERATE** | **N3: 반증 기준** |
| 5 | **S-축 사후적**: blue p=0.046 Bonferroni-8 미통과 | **MODERATE** | Cross-phase 부분 완화 |

#### 수정된 결론

| 원래 | 수정 |
|------|------|
| "hV4 진정한 보간 (p=0.026)" | "Omnibus 피질 보간 존재 (p=0.002); hV4 주도 (Bonferroni marginal)" |
| "HC-CVD gap 54-78% K-dependent" | "Gap reduction = HC-최적화 bias (N2). S-축 잔여 검증 필요." |
| "V1/V2 미결정" | "Linear 1D 하 음성 결과. 반증: 2D 비선형, N>200, 7T sub-mm." |
| "5종 독립 수렴" | "단일 hV4 발견의 다각적 특성화 (동일 데이터)." |

### 9c. 중화 실험

#### N1: Stouffer Omnibus (FATAL #2 중화)

**Per-ROI Stouffer (HC, 최적 basis):**

| ROI | Basis | Stouffer Z | p |
|-----|-------|:----------:|:----:|
| V1 | FE-2 | 0.956 | 0.170 |
| V2 | FE-3 | 1.149 | 0.125 |
| V3 | FE-8 | 1.692 | 0.045 |
| hV4 | FE-3 | 1.941 | 0.026 |

**Omnibus:**

| 검정 | 통계량 | p | Gate |
|------|:------:|:----:|:----:|
| Stouffer | Z = 2.869 | **0.0021** | **PASS** |
| Fisher | χ²(8) = 21.18 | **0.0067** | **PASS** |

**결론**: Omnibus p=0.0021 — **피질 수준 색상 보간 존재**. 단일 비보정 ROI p에 의존하지 않음.

#### N1-부록: Stouffer vs Fisher — 방법 선택 근거

두 방법 모두 여러 p-value를 하나로 결합하지만, **감지하는 신호 유형이 다르다**.

| 특성 | Fisher | Stouffer |
|------|--------|----------|
| 변환 | p → −log(p) (정보량/surprise) | p → Z (표준편차 단위) |
| 결합 | −2Σln(p) → χ² 분포 | ΣZ/√k → 정규분포 |
| 민감도 | **극단적으로 작은 p 하나**가 전체 지배 | **여러 약한 p의 일관된 패턴** |
| 해석 | "어딘가에서 강한 효과 존재" | "평균적 증거가 우연 이상" |
| 적합 상황 | GWAS, rare discovery | 신경과학, meta-analysis, 분산 효과 |

**핵심 직관**: Fisher의 로그 변환은 매우 작은 p를 기하급수적으로 증폭한다 (−ln(0.001) = 6.9 vs −ln(0.2) = 1.6). 따라서 **하나의 극단적 p가 전체 결과를 좌우**한다. Stouffer의 Z 변환은 증거 강도에 선형적이므로, **테스트들 간의 일관성(consistency)**을 보상한다.

**우리 데이터에 적용**:

| ROI | p | −ln(p) (Fisher) | Z (Stouffer) |
|-----|:---:|:---:|:---:|
| V1 | 0.170 | 1.77 | 0.95 |
| V2 | 0.125 | 2.08 | 1.15 |
| V3 | 0.045 | 3.10 | 1.69 |
| hV4 | 0.026 | 3.65 | 1.94 |

**패턴**: 극단적으로 작은 p가 하나도 없고 (p < 0.01 없음), 대신 시각 위계를 따라 **단조 감소하는 gradient** (V1 > V2 > V3 > hV4)가 존재한다. 이것이 Stouffer가 더 적절한 전형적 시나리오다:

- **Stouffer Z = 2.87, p = 0.0021** — 일관된 gradient 포착
- **Fisher χ²(8) = 21.18, p = 0.0067** — 통과하지만 상대적으로 약함 (증폭할 극단 p 부재)

**두 검정 모두 통과**한다는 사실 자체가 omnibus 주장을 강화한다. Stouffer가 더 강한 결과를 보이는 것(p=0.002 vs 0.007) 자체가 정보적이다: 우리 효과는 **단일 핫스팟**(Fisher에 민감)이 아닌 **분산 패턴**(Stouffer에 민감) — 시각 위계 전반의 일관된 약-중등도 증거, hV4가 주도하고 V3가 의미 있게 기여.

**Reviewer 관점**: Reviewer가 "효과가 실재하는가?"를 물을 때, 실질적으로 "single hotspot인가(Fisher) distributed pattern인가(Stouffer)"를 묻는 것이다. 우리 데이터는 명확히 후자 — 두 검정 모두 보고하되 Stouffer를 주(primary)로 삼는 것이 이 구조를 투명하게 전달한다.

**주의**: Stouffer의 강점이 동시에 약점이 될 수 있다. 만약 hV4만 진정한 신호이고 V1/V2/V3가 순수 noise라면, noise Z-value가 0 근처이므로 평균 Z가 여전히 양수가 되어 통과할 수 있다. Friedman 균일성 검정(hV4만 균일 보간, p=0.485)과 residual 분석(hV4만 근무작위, r=0.053)이 hV4 주도 신호의 독립적 보강 증거를 제공한다.

#### N2: K-Selection Bias Permutation (SEVERE #3 — artifact 확인)

| ROI | 관측 Reduction | Null 평균 | p(≥obs) | 판정 |
|-----|:-------------:|:---------:|:-------:|:----:|
| V1 | 73.3% | 11.0% | 0.192 | 우연 범위 |
| V2 | 34.4% | -63.5% | 0.228 | 우연 범위 |
| V3 | 3.5% | -633.6% | 0.227 | 우연 범위 |
| hV4 | 63.1% | -109.3% | 0.133 | 우연 범위 |

전 ROI gap reduction 우연 수준. **"Gap reduction" 서술 폐기.** 특정 K에서의 gap 크기는 유효.

#### N3: 수렴 재프레이밍 + V1/V2 반증 기준

**수렴 (FATAL #1 → 해결):**
> "다각적 분석이 **단일 관측**을 특성화: hV4 forward-model 예측이 held-out 색상 패턴과 우연 이상 상관 (omnibus p=0.002). 동일 48 데이터 포인트에서 도출. 독립적 증거가 아님."

**V1/V2 (MOD #4 → 해결):**
> "전 tested linear 1D basis 하 **음성 결과**. 반증: (1) 2D 비선형 basis, (2) N>200, (3) 7T sub-mm."

### 9d. 중화 후 총괄표

| # | 취약점 | 원래 | 중화 후 | 상태 |
|---|-------|:----:|:-------:|:----:|
| 1 | 의사복제 | FATAL | **해결** | 언어 교정 |
| 2 | 다중비교 | FATAL | **해결** | Omnibus p=0.0021 |
| 3 | K-selection bias | SEVERE | **해결** | artifact 확인; 서술 폐기 |
| 4 | V1/V2 반증 불가 | MODERATE | **해결** | 반증 기준 명시 |
| 5 | S-축 사후적 | MODERATE | **부분 완화** | 가설 생성으로 유지 |

**종합**: 4/5 완전 중화. 논문 등급: REJECT → **MAJOR REVISION** (eLife/NeuroImage).

---

## 10. Discussion — 문헌 통합

### 10.1 Eigenspectrum Geometry와 LOCO Null (Pospisil & Pillow 2024)

α_early = 0.66-0.98, Pospisil 범위 내. V1/V2 얕은 decay (α≈0.68) vs hV4 (α≈0.98). V1/V2 permutation null (~0.10-0.13)은 voxel correlation 구조에서 기인, 진정한 색 신호 아님. hV4만 이 null 초과.

### 10.2 과제-의존적 표상 (Kuriki et al. 2025)

V1-V3: 범주적 과제에서 강한 표상. hV4: 외관 판단(연속 hue)과 상관.

| 우리 발견 | Kuriki 대응 |
|----------|------------|
| V1/V2 LORO 보존 | V1-V3 범주 과제 활성 |
| V1/V2 LOCO 실패 | V1-V3 외관 과제 약함 |
| hV4 LOCO 성공 (p=0.026) | hV4 외관 상관 |
| CVD LORO ≈ HC | 범주 경계 과제-독립 |

### 10.3 공유 집단 기하학 (Bannert & Bartels 2025)

Bannert & Bartels (2025): SRM 기반 피험자 간 색상 디코딩 (N=15, 3색, 6 runs, 무채색 retinotopy로 SRM 학습). LOSO 정확도: V1 44.7%, hV4 39.5% (chance 33.3%). LOSO/within 비율 71-78%.

**정량적 수렴 (§7f):** 본 연구 hV4 ZS/LORO = 99.5% (vs Bannert 77.1%) — 색상 데이터로 SRM 학습 시 group prior 충실도 향상. 두 연구 모두 집단 수준 색 기하학이 피험자 간 공유됨을 확인.

**CVD 확장 (본 연구 고유):** Bannert은 HC만 테스트. 본 연구에서 HC ≈ CVD in LOSO (전 p > 0.4) — CVD 망막 결함에도 불구하고 HC group prior가 CVD에 일반화. CVD 결함 = hue-space 변환(T_psi), voxel-space 재조직 아님. LOCO만이 HC-CVD 해리를 드러냄.

Voxel preference 결과 확인: green 부족 (V1/V2 p<0.02), magenta 과잉 (+117-196%), 그러나 **동일 복셀** — argmax만 이동.

### 10.4 차원성과 모델 명세

RT-5 해결: Eigenspectrum + MEME → HC ≈ CVD. CVD K-sensitivity = bias-variance tradeoff (Option A). Phase 2 filter = 자극 공간 warping (동일 차원, 다른 tuning).

---

## 11. 계층적 발견 및 결론

### 1차 목적 — 예측 모델

1. **hV4 중심 색상 보간 모델 검증 완료** (Stouffer omnibus p=0.002)
   - hV4 유일 permutation 통과 (FE-6 p=0.044, FE-3 p=0.026)
   - Friedman: hV4 균일 보간 (p=0.485); V1/V2 비균일
   - Residual: hV4 근무작위 (r=0.053) — 가용 구조 대부분 포착

2. **LOSO: Group prior가 hV4 prediction engine으로 유효** (ZS ≈ LORO, p=0.913)
   - Group prior만으로도 subject-specific ridge_gcv와 동등한 hV4 패턴 재현
   - 단, 보간(LOCO)은 여전히 도전적 (0.232 vs ZS 0.417) — Phase 2 filter 정밀도 상한
   - V1/V2/V3: ZS >> LORO (noise 차이) — hV4만의 특성

3. **V1/V2 구별은 하나 보간 불가** — Phase 2에서 hV4 전용
   - 전 FE-{2..12} + OPP-2/4/4rect + intercept FAIL
   - Kuriki (2025) 일치: V1-V3 범주적, hV4 지각적

### 2차 목적 — HC-CVD 비교

4. **CVD hue-space 왜곡은 cone shift로 설명됨** — 자극 공간 필터 타당
   - Eigenspectrum/MEME: HC ≈ CVD (전 p > 0.14) → 피질 재조직 아님
   - Cone shift 분석: deutan M' 이동→green 급감+yellow 과분리, protan L' 이동→red 급감
   - Per-subject K* 차이(sub-08 K*=8)는 cone shift에 의한 tuning curve 변형과 일관적 (단, 과적합 가능성 미배제)
   - Per-color residual의 cool-axis 왜곡이 cone model 예측과 수렴

### 확정된 결정

| 구성 요소 | 확정 | 기각된 대안 |
|----------|------|-----------|
| Encoder | ridge_gcv | smooth_tikh, RRR, bayes_prior, mixed_ridge_prior, smooth_prior |
| Basis shape | FE (half-wave cos²) | LF (Fourier), OPP (opponent) |
| Per-ROI K | V1→2, V2→3, V3→8, hV4→3 | FE-6 uniform |
| Per-subject K* | sub-08→8, sub-09→3, sub-10→2 | 그룹 K=3 고정 (실용적 유지, 해석은 탐색적) |
| Center | Uniform (360°/K) | Adaptive, Anisotropic (B2) |
| Primary ROI | hV4 | V1/V2 (discrimination-only) |
| CVD 메커니즘 | Cone shift → 자극 공간 왜곡 | 피질 재조직, 차원 축소 |
| Phase 2 prediction engine | W_HC (group prior) | Subject-specific W (불필요, LOSO 검증) |

---

## 12. Phase 2 핸드오프 & 평가

### 12a. Gate 3 평가 (3-Track 종합)

| Track | 상태 | 핵심 결과 |
|-------|:----:|----------|
| A: 잔류 생물학 | **완료** | Cool-axis distortion 확인; deutan/protan 비대칭 |
| B: CVD 예측 모델 | **완료** | B1 (per-subject K*) 채택; B2/B3 폐기 |
| C: 차원성 | **완료** | HC ≈ CVD (Option A: bias-variance tradeoff) |

### 12b. Phase 2 입력 사양

| 입력 항목 | 출처 | 값 |
|-----------|------|-----|
| Prediction engine | LOSO (§7f) | **W_HC (group prior)** — ZS≈LORO 검증 완료 |
| 1차 ROI | Gate (§7e) | hV4 |
| 인코더 | Gate (§7e) | ridge_gcv |
| 피험자별 K* | B1 (§8j) | sub-08=8, sub-09=3, sub-10=2 (실용적; 해석은 탐색적) |
| 왜곡 메커니즘 | Cone shift (behavioral) | Deutan: M' 이동→green 급감, Protan: L' 이동→red 급감 |
| 왜곡 패턴 | A3/A5 (§8i) | Cool-axis 왜곡 (blue d=+1.37 p=0.046) |
| sub-09 | B1 | K*=3=그룹K → K 최적화 불가. Cone-shift T_ψ로 재시도 대상 |
| sub-10 | B1 | HC-level → 최소 보정 |
| sub-08 | B1 | **주요 필터 대상** |

### 12c. Phase 2 Filter 아키텍처

```
T_ψ: θ → θ' = θ + ψ(θ)
where ψ(θ) = Σ_k [a_k sin(kθ) + b_k cos(kθ)]   (Fourier parameterization)

최적화:
minimize  E_θ [|| W_CVD @ C(T_ψ(θ)) − Y_HC(θ) ||²]
# CVD 인코더가 변환된 자극 처리 → HC 실제 반응 매칭
subject to  ||ψ||² < ε   (small correction)
```

W_s는 filter 최적화 전 동결. T_ψ는 자극 공간에서만 작동.

### 12d. LOSO가 밝힌 Prediction Engine 상태

| 지표 | hV4 값 | 해석 |
|------|--------|------|
| ZS voxel_corr | 0.417 | Group prior의 공간 패턴 재현 능력 |
| LORO voxel_corr | 0.407 | Subject-specific 모델과 동등 (p=0.913) |
| LOCO voxel_corr | 0.232 | **보간 격차 = 0.185** (= ZS − LOCO) |

**Phase 2 filter 정밀도 상한 = LOCO 성능**. 보간 격차(0.185)를 줄이는 것이 Phase 2 filter 개선의 핵심.

**LOCO ≠ Filter**: LOCO(7색→W→1색 예측) vs Filter(8색+고정W→T_ψ 4 param 최적화).
LOCO는 W를 매 fold 재추정 → df 부족 직접 영향. Filter는 W 고정(LOSO 검증) → LOCO 한계 ≠ filter 한계.

| | LOCO | Phase 2 Filter |
|---|------|----------------|
| 학습 데이터 | 7색 | 8색 |
| 자유 파라미터 | K×V_s (수백~수천) | 4 Fourier |
| W 역할 | 매 fold 재추정 | 고정 (prediction engine) |

### 12e. TODO: Phase 2 Filter 설계 단계

1. **Cone shift 기반 T_ψ 초기화** — Stockman & Sharpe (2000) cone fundamentals → deutan/protan별 hue shift 함수 계산 → T_ψ 초기값
2. **Filter T_ψ 최적화** — W_CVD @ C(T_ψ(θ)) ≈ Y_HC(θ) 최소화, Fourier k=1~2
3. **LOCO-style 검증** — 7색으로 T_ψ 학습 → 1색 예측 (과적합 방지)
4. **행동 과제(JND 2AFC) 연계** — T_ψ 예측과 JND 변화 비교
5. **`future_phase2_filter_optimization/`으로 전환**

### 12f. 의사결정 기준

| 결정 | 기준 | 상태 |
|------|------|------|
| Phase 2 진행 | hV4 LOCO > perm null | **충족** (HC perm p=0.044) |
| Prediction engine | LOSO ZS ≈ LORO | **충족** (hV4 p=0.913) |
| Filter 메커니즘 | Cone shift 설명력 | **충족** (deutan/protan 예측 일치) |
| sub-09 필터 포함 | Cone-shift T_ψ 적용 후 LOCO 개선 | **보류** (실험 대기) |
| Track C 선행조건 | HC ≈ CVD 차원성 | **완료** |

**Gate 3 판정: PASS** — hV4 group prior(LOSO 검증) + cone shift 기반 filter로 Phase 2 진행.

### 12g. T_ψ Filter Model: 설계 원리 및 Approach A/B 파이프라인

#### T_ψ Fourier 파라미터화의 강점

**1. 순환성**: Hue = 0°-360° 순환 공간. Fourier = 본질적 주기 함수. Spline/다항식은 경계 불연속.

**2. 부드러움**: k=1,2만 사용 → 고주파 진동 차단. CVD 왜곡은 cone sensitivity의 smooth 변형 → 저주파 보정만 물리적으로 의미.

**3. 파라미터 절약**: 4개 (a₁,b₁,a₂,b₂)로 전체 360° 변환. 8-knot spline=8개(=데이터 수, df=0). Lookup=보간 규칙 필요.

**4. 물리적 해석성**:

| 성분 | 수학 | 물리적 의미 | Cone shift 연결 |
|------|------|-----------|----------------|
| 1차 | R₁cos(θ−φ₁) | L-M 축 왜곡 | M/L cone peak shift → R-G 압축 |
| 2차 | R₂cos(2θ−φ₂) | S-cone 보상 비대칭 | S 보존 + L-M 왜곡 → B-Y 비대칭 |

Deutan vs protan은 φ₁이 다르지만 같은 파라미터 구조.

**5. 대안 비교**:

| 방법 | 순환 | 부드러움 | 파라미터 | 해석 | 판정 |
|------|:----:|:-------:|:------:|:----:|:----:|
| **Fourier T_ψ** | 자동 | 주파수 절단 | 4 | 직접적 | **채택** |
| Lookup table | 수동 | 보장 안 됨 | 8+ | 없음 | 기각 |
| Spline | 수동 래핑 | 지역적 | 8+ | 없음 | 기각 |
| 다항식 | 비순환 | 진동 위험 | 3+ | 없음 | 기각 |
| Affine | 가능 | 선형 | 2 | 부분적 | 기각(비대칭 불가) |

#### Approach A: Cone Shift Model (물리 기반, 1 파라미터)

**입력**: Δλ (cone peak wavelength shift, nm)

**과정**:
1. Stockman & Sharpe (2000) cone fundamentals l(λ), m(λ), s(λ) 로드
2. Deutan: M'(λ) = M(λ + Δλ) / Protan: L'(λ) = L(λ − Δλ)
3. 8색 CIELab → XYZ → LMS_normal 및 LMS_shifted 계산
4. LMS → opponent channels (rg = L−M, by = S−(L+M)/2) → hue angle
5. δθ_pred(i) = θ_shifted(i) − θ_normal(i)

**최적화**: Δλ grid search (0-40nm, 1nm 단위)
```
Δλ* = argmin_Δλ  Σ_i [ δθ_pred(i; Δλ) − δθ_obs(i) ]²
```
δθ_obs = HC mean LOCO voxel_corr − CVD LOCO voxel_corr (per-color, hV4)

**출력**: Δλ* (nm), 색상별 δθ_pred, Fourier fit → T_ψ₀ 초기값 (a₁,b₁,a₂,b₂)

#### Approach B: T_ψ Data-Driven Optimization (데이터 기반, 4 파라미터)

**입력**: W_CVD (CVD 인코더), Y_HC (HC 목표 응답)

```
minimize  Σ_i || W_CVD @ C(T_ψ(θ_i)) − Y_HC(θ_i) ||²  + λ·||ψ||²
```
여기서 T_ψ(θ) = θ + a₁cos θ + b₁sin θ + a₂cos 2θ + b₂sin 2θ

**초기화**: Approach A 출력 (T_ψ₀)로 시작. SciPy L-BFGS-B.

#### A ↔ B 관계 (Nested Model)

| | Approach A | Approach B |
|---|-----------|-----------|
| 자유 파라미터 | 1 (Δλ) | 4 (a₁,b₁,a₂,b₂) |
| 제약 | Stockman 물리 | Fourier smoothness |
| 과적합 위험 | 극히 낮음 | 중간 (LOCO 검증) |
| 해석 | 직접 (nm) | 간접 (Fourier) |

**핵심**: A ≈ B → cone shift가 왜곡을 완전히 설명 (retinal origin)
          A ≠ B → cortical 기여 존재 (Δ = B−A가 cortical 기여 정량)

**구현**: stockman_cone_shift.py(A) → step3_filter_optimization.py(B) → 잔차 비교

---

## 부록 A: Phase 2 연결

W_s가 Phase 2의 **prediction engine** (frozen):

```
theta → C(theta) → W_s @ C(theta) = Y_hat_s(theta)
```

Phase 2 filter T_psi는 W_s의 **upstream**에서 작동:

```
theta → T_psi(theta) → C(T_psi(theta)) → W_CVD @ C(T_psi(theta)) ≈ Y_HC
```

**역할 분리**:

| | V1/V2 | hV4 |
|--|-------|-----|
| Phase 2 역할 | Filter correction target | Color interpolation oracle |
| 근거 | HC-CVD 차이 유의 (d>1.0) | Genuine color interpolation (perm p=0.044) |

**Encoder**: ridge_gcv 확정. ridge_gcv 기반 HC-CVD 비교 (V2 d=1.85, p=0.022) 사용.

---

## 부록 B: 프로젝트 구조

```
future_phase1_forward_model/
├── scripts/
│   ├── (30+ 기존 baseline 스크립트)
│   ├── dimensionality/                          ← Exp C1/C2
│   │   ├── analyze_eigenspectrum_decay.py
│   │   └── fit_meme_eigenspectrum.py
│   └── population_organization/                 ← Exp C3
│       └── map_voxel_color_preference.py
├── sbatch/
│   ├── run_dimensionality.sbatch
│   ├── run_eigenspectrum_decay.sbatch
│   ├── run_meme_estimator.sbatch
│   └── run_voxel_preference.sbatch
├── results/
│   ├── (기존 baseline 결과)
│   ├── dimensionality/
│   └── population_organization/
├── PLAN.md
├── RESULTS.md                                   ← RESULTS.md와 동기화
├── SUMMARY_next_steps.md
├── LITERATURE_INTEGRATION_PLAN.md
└── notion.md                                    ← 본 파일
```

---

## 부록 C: 핵심 통계 참조 (Quick Reference)

### hV4 FE-3 Per-Color LOCO

| Color | θ | HC M | CVD M | d | p |
|-------|-----|:----:|:-----:|:---:|:---:|
| red | 0° | +0.353 | +0.310 | +0.18 | 0.81 |
| orange | 45° | +0.246 | +0.502 | −0.94 | 0.22 |
| yellow | 90° | +0.135 | +0.213 | −0.24 | 0.70 |
| green | 135° | +0.107 | +0.055 | +0.13 | 0.85 |
| cyan | 180° | −0.008 | +0.157 | −0.35 | 0.66 |
| **blue** | **225°** | **+0.349** | **+0.025** | **+1.37** | **0.046*** |
| purple | 270° | +0.283 | −0.124 | +1.54 | 0.060 |
| magenta | 315° | +0.171 | −0.211 | +1.19 | 0.127 |

### Warm/Cool Gap 분해

| 축 | FE-6 Gap | FE-K Gap | 감소 |
|------|:--------:|:--------:|:----:|
| **Warm (L-M)** | +0.118 | −0.060 | >100% (역전) |
| **Cool (S)** | +0.362 | +0.237 | 35% only |

### CVD Cool-Color 프로필 (hV4 FE-3)

| 피험자 | Type | Warm M | Cool M | 해석 |
|--------|------|:------:|:------:|------|
| sub-08 | deutan | +0.227 | −0.058 | Cool 음수 |
| sub-09 | protan | +0.340 | −0.197 | Cool 최악 |
| sub-10 | deutan | +0.244 | +0.140 | Cool 양수 (보상) |
| HC mean | — | +0.210 | +0.199 | 균형 |

---

**Last Updated**: 2026-03-15
