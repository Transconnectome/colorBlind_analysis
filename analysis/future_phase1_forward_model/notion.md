# Future Phase 1: Group-Prior Prediction Model

> **프로젝트**: Color Vision Deficiency Neural Representation Analysis
> **날짜**: 2026-03-10 (정리: 2026-03-11, smooth_tikh 결론: 2026-03-11, 적응 기저: 2026-03-12, per-color residual: 2026-03-13)
> **피험자**: HC 7명 (sub-01~07), CVD 3명 (sub-08 deutan, sub-09 protan, sub-10 deutan)
> **ROI**: V1, V2, V3, hV4
> **목적**: HC group prior를 활용한 subject-specific forward encoding model W_s 학습 및 검증

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

### Encoding Improvement (Section 9g)

| Model | 수식 | Inner CV | 판정 |
|-------|------|----------|------|
| **ridge_rrr_r{2,3,4}** | SVD truncation of W | Inner LORO | **기각** — 모든 rank에서 baseline보다 나쁨 |
| **ridge_smooth_best** | W = (C'C + αI + βD'D)⁻¹C'X | Inner LORO | **기각** — voxel_corr ↑ 기만적, rdm_pearson ↓ (37-65%) |

### Extended Models (Section 9h)

| Model | 수식 | Inner CV | 가설 | 판정 |
|-------|------|----------|------|------|
| **smooth_tikh** | W = (C'C + αI + βD'D)⁻¹C'X | **Inner LOCO** | H3 (smoothness) | **기각** — perm 전 ROI 실패, 공간 공분산만 포착 |
| **mixed_ridge_prior** | W = (C'C + (α+λ)I)⁻¹(C'X + λW₀) | Inner LOCO | H1 (shape) | **기각** — V1-V3 음 |
| **bayes_prior** | w_v = (C'C + diag(γ/σ²_v))⁻¹(C'x_v + Λ_v w₀_v) | Inner LOCO | H2 (uncertainty) | **기각** — V1-V3 음 |
| **smooth_prior** | W = (C'C + αD'D + λI)⁻¹(C'X + λW₀) | Inner LOCO | H3+prior | **기각** — prior가 smoothness 효과 상쇄 |

### Encoding Basis (Section 9c)

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
- Inner LORO: run-held-out, Inner LOCO: color-held-out

**핵심 교훈**: (1) 동일 수식(smoothness)도 inner LORO → artifact, inner LOCO → 개선처럼 보이나 permutation 실패. (2) voxel_corr/rdm_pearson 개선이 반드시 색 판별 신호를 의미하지 않음 — 공간 공분산 포착일 수 있음. (3) Permutation test가 유일한 진정한 검증.

---

## 6. 주요 결과

### 6a. Reliability (Data Quality)

Split-half RDM correlation:

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

Noise Ceiling:

| ROI | HC NC_lower (SD) | HC NC_upper (SD) | CVD NC_lower (SD) | CVD NC_upper (SD) |
|-----|-----------------|-----------------|------------------|------------------|
| V1 | 0.441 (0.100) | 0.939 (0.027) | 0.527 (0.188) | 0.955 (0.027) |
| V2 | 0.452 (0.112) | 0.943 (0.034) | 0.596 (0.161) | 0.970 (0.016) |
| V3 | 0.451 (0.174) | 0.931 (0.036) | 0.522 (0.148) | 0.947 (0.010) |
| hV4 | 0.573 (0.141) | 0.957 (0.025) | 0.646 (0.147) | 0.968 (0.019) |

### 6b. Baseline LORO (mean voxel_corr)

| Model | V1 HC (SD) | V1 CVD (SD) | V2 HC (SD) | V2 CVD (SD) | V3 HC (SD) | V3 CVD (SD) | hV4 HC (SD) | hV4 CVD (SD) |
|-------|-----------|------------|-----------|------------|-----------|------------|------------|-------------|
| ols | 0.213 (0.044) | 0.218 (0.031) | 0.246 (0.042) | 0.259 (0.078) | 0.326 (0.081) | 0.340 (0.039) | 0.406 (0.068) | 0.399 (0.050) |
| ridge_gcv | 0.201 (0.050) | 0.207 (0.036) | 0.230 (0.047) | 0.243 (0.092) | 0.308 (0.082) | 0.340 (0.047) | 0.401 (0.068) | 0.396 (0.060) |
| prior_only | 0.306 (0.015) | 0.287 (0.049) | 0.300 (0.029) | 0.297 (0.017) | 0.304 (0.044) | 0.278 (0.019) | 0.317 (0.031) | 0.303 (0.036) |
| **prior_ft** | **0.315 (0.021)** | **0.292 (0.053)** | **0.310 (0.027)** | **0.327 (0.070)** | **0.357 (0.064)** | **0.381 (0.047)** | **0.419 (0.062)** | **0.409 (0.058)** |

HC-CVD 차이: 모든 |d| < 0.72, 모든 p > 0.22 — LORO에서 유의한 그룹 차이 없음.

### 6c. Baseline LOCO — Clean (mean voxel_corr)

> Leakage-free: 각 fold마다 held-out color 제외하고 W0 재계산

| Model | V1 HC (SD) | V1 CVD (SD) | V2 HC (SD) | V2 CVD (SD) | V3 HC (SD) | V3 CVD (SD) | hV4 HC (SD) | hV4 CVD (SD) |
|-------|-----------|------------|-----------|------------|-----------|------------|------------|-------------|
| ols | +0.051 (0.095) | -0.082 (0.016) | +0.092 (0.127) | -0.181 (0.055) | +0.023 (0.197) | -0.073 (0.140) | +0.158 (0.188) | -0.067 (0.141) |
| **ridge_gcv** | **+0.130 (0.097)** | -0.012 (0.054) | **+0.150 (0.188)** | -0.174 (0.130) | +0.023 (0.240) | -0.008 (0.163) | **+0.183 (0.200)** | -0.058 (0.207) |
| prior_only | -0.075 (0.040) | -0.098 (0.019) | -0.099 (0.071) | -0.173 (0.052) | -0.186 (0.096) | -0.203 (0.073) | +0.109 (0.084) | +0.072 (0.066) |
| prior_ft | -0.056 (0.036) | -0.093 (0.015) | -0.060 (0.085) | -0.163 (0.057) | -0.101 (0.135) | -0.117 (0.097) | +0.169 (0.148) | -0.063 (0.166) |

**LORO-LOCO 해리**: prior_ft가 LORO 승리, ridge_gcv가 LOCO 승리. SRM prior는 run-level variance를 포착하지만 color-specific tuning은 놓침.

### 6d. LOCO 통계 검정 (HC, ridge_gcv)

**One-sample t-test (LOCO > 0):**

| ROI | HC Mean | 95% CI | t(6) | p (one-tail) |
|-----|---------|--------|------|-------------|
| **V1** | **0.130** | [0.040, 0.220] | **3.544** | **0.006** |
| V2 | 0.150 | [-0.024, 0.323] | 2.109 | **0.040** |
| V3 | 0.023 | [-0.199, 0.245] | 0.254 | 0.404 |
| **hV4** | **0.183** | [-0.002, 0.367] | **2.423** | **0.026** |

### 6e. Basis Ablation 결과

**LOCO voxel_corr (OLS, n=10):**

| Basis | V1 M (SD) | V2 M (SD) | V3 M (SD) | hV4 M (SD) |
|-------|----------|----------|----------|-----------|
| **FE-6** | **+0.011 (0.101)** | **+0.010 (0.170)** | -0.006 (0.180) | **+0.090 (0.199)** |
| LF-4 | -0.066 (0.087) | -0.097 (0.200) | -0.105 (0.125) | -0.075 (0.091) |
| LF-6 | -0.111 (0.154) | -0.070 (0.159) | -0.093 (0.220) | -0.093 (0.199) |

**FE-6 vs LF-4 (paired t, n=10):** LOCO에서 V1 p=0.045, V2 p=0.042, hV4 p=0.016. LORO에서 전 ROI p<0.001. **FE 형태 확정.**

#### 확장 비교: FE 채널 수 (ridge_gcv, HC n=7, 2026-03-11)

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

**Permutation (10K, Stouffer combined, per-ROI optimal basis):**

| ROI | Basis | p_stouffer | FE-6 대비 |
|-----|-------|-----------|----------|
| V1 | FE-2 | 0.170 | 0.274→0.170 (개선, FAIL) |
| V2 | FE-3 | 0.125 | 0.311→0.125 (개선, FAIL) |
| **V3** | **FE-8** | **0.045*** | **0.360→0.045 (NO-GO→PASS)** |
| hV4 | FE-3 | **0.026*** | 0.044→0.026 (강화) |

**핵심**: V3 실패는 basis 선택 문제였음 (FE-8로 회복). V1/V2는 어떤 1D FE basis로도 fail.

**HC-CVD gap의 basis 의존성:** V1 FE-2에서 CVD=+0.115 (양수!), d=1.76→0.40. HC-CVD 차이의 상당 부분이 basis mismatch에 기인.

#### Opponent Basis Test (Red Team #3 중화, 10K perm, 2026-03-11)

**질문**: V1/V2 LOCO 실패가 FE basis 선택 문제인가? DKL 2D opponent-channel basis로 검증.

**테스트 basis:**

| Basis | Type | K | 설계 |
|-------|------|:-:|------|
| OPP-2 | Raw opponent | 2 | [cos(θ), sin(θ)] |
| OPP-4 | Opponent + quadrature | 4 | [cos(θ), sin(θ), cos(2θ), sin(2θ)] |
| OPP-4rect | Half-wave rectified | 4 | [cos⁺, cos⁻, sin⁺, sin⁻] |
| FE-6 | Fourier encoding (기준) | 6 | Half-wave rectified cos² |

**LOCO Permutation (Stouffer combined, HC):**

| Basis | V1 | V2 | V3 | V4 |
|-------|:------:|:------:|:------:|:------:|
| OPP-2 | p=0.324 | p=0.444 | p=0.358 | p=0.302 |
| OPP-4 | p=0.125 | p=0.109 | p=0.566 | p=0.139 |
| OPP-4rect | p=0.633 | p=0.261 | p=0.796 | p=0.110 |
| **FE-6** | p=0.126 | p=0.154 | p=0.367 | **p=0.039*** |

**HC LOCO Mean (observed / null):**

| Basis | V1 | V2 | V3 | V4 |
|-------|:---:|:---:|:---:|:---:|
| OPP-2 | -.041/-.055 | -.047/-.062 | -.042/-.047 | -.042/-.058 |
| OPP-4 | -.054/-.091 | -.074/-.104 | -.118/-.075 | -.045/-.097 |
| OPP-4rect | +.099/+.113 | +.157/+.127 | +.054/+.090 | +.167/+.103 |
| FE-6 | +.144/+.111 | +.169/+.129 | +.063/+.077 | +.181/+.085 |

**결론:**
1. **모든 opponent basis가 V1/V2에서 FAIL** — p < 0.05 달성 불가
2. **FE-6만이 V4에서 유일하게 통과** (p=0.039)
3. OPP-2 (K=2): LOCO 전 ROI 음수 — 심각한 underfit
4. OPP-4rect: null이 양수로 부풀림 — 판별력 없음
5. **Red Team #3 중화 완료**: V1/V2 실패는 basis mismatch가 아님 — V4만 통과하는 해리(dissociation)는 진짜 영역적(regional) 특성

### 6f. Metric Reinforcement (9f)

**Permutation test (10K color-label shuffles, HC ridge_gcv):**

| ROI | Observed | Null Mean | p_perm |
|-----|---------|-----------|--------|
| V1 | 0.130 | 0.109 | 0.274 |
| V2 | 0.150 | 0.130 | 0.311 |
| V3 | 0.023 | 0.078 | 0.880 |
| **hV4** | **0.183** | **0.080** | **0.044*** |

V1/V2의 null이 ~0.10-0.13 (not zero) — voxel covariance structure가 baseline voxel_corr을 생성. **hV4만이 covariance baseline을 유의하게 초과.**

**Friedman test (per-color uniformity, HC):**

| ROI | chi²(7) | p | 해석 |
|-----|---------|---|------|
| V1 | 18.33 | 0.011* | 비균일 — Blue 높음, Yellow/Green 낮음 |
| V2 | 14.24 | 0.047* | 비균일 |
| V3 | 11.38 | 0.123 | 구조 없음 |
| hV4 | 6.48 | 0.485 | **균일 — 진정한 연속 보간** |

**Residual structure (HC):**

| Metric | V1 | V2 | V3 | hV4 |
|--------|------|------|------|------|
| r(resid, orig) | 0.453 | 0.454 | 0.329 | **0.053** |
| r(pred, orig) | 0.390 | 0.407 | 0.415 | **0.563** |

hV4 residual이 near-random (0.053) — 모델이 가용 구조 대부분 포착. V1/V2에는 systematic residual 잔존.

#### Intercept Model Permutation Test (10K, HC, 2026-03-11)

**질문**: 공유 공간 평균(intercept)이 LOCO 성능 또는 null을 부풀리는가?

3가지 방법 비교:
- **Standard**: Y = W @ C (기존 ridge_gcv)
- **Intercept**: Y = W_color @ C + b (평가 시 deviation만: corr(C_test @ W_color, Y_real - b))
- **Mean_subt**: (Y - mean(Y)) = W @ C (mean 사전 제거)

**Stouffer Combined p-values (per-ROI optimal basis):**

| Method | V1 (FE-6) | V2 (FE-6) | V3 (FE-8) | V4 (FE-3) |
|--------|:---------:|:---------:|:---------:|:---------:|
| Standard | p≈0.126 | p≈0.155 | p≈0.043* | p≈0.025* |
| Intercept | p≈0.127 | p≈0.156 | p≈0.040* | p≈0.064 |
| Mean_subt | p≈0.136 | p≈0.160 | p≈0.053 | p≈0.059 |

**결론:**
1. **Standard ≈ Intercept ≈ Mean_subt** — 모든 ROI에서 거의 동일한 p-값
2. V1/V2는 어떤 방법으로도 유의하지 않음
3. Intercept null 중심이 ~-0.035 (standard ~+0.05-0.10) — intercept가 공유 신호 흡수
4. **p-값은 변하지 않음** — 인코딩 신호는 hue-modulated pattern에 있고, 공간 평균이 아님

### 6g. Extended Models (9h) — LOCO voxel_corr (n=10)

| Model | V1 M (SD) | V2 M (SD) | V3 M (SD) | V4 M (SD) |
|-------|----------|----------|----------|-----------|
| ridge_gcv | +0.087 (0.095) | +0.053 (0.194) | +0.014 (0.200) | +0.111 (0.210) |
| prior_finetune | -0.067 (0.035) | -0.091 (0.090) | -0.105 (0.118) | +0.099 (0.175) |
| **smooth_tikh** | **+0.112 (0.133)** | **+0.151 (0.175)** | **+0.115 (0.212)** | **+0.157 (0.245)** |
| smooth_prior | +0.025 (0.153) | -0.002 (0.170) | -0.078 (0.143) | +0.094 (0.244) |
| mixed_ridge_prior | -0.056 (0.089) | -0.073 (0.126) | -0.066 (0.105) | +0.094 (0.225) |
| bayes_prior | -0.062 (0.047) | -0.101 (0.082) | -0.123 (0.129) | +0.028 (0.209) |

smooth_tikh만이 모든 ROI에서 양의 LOCO. Prior 기반 3개 모델은 V1-V3 모두 음.

**smooth_tikh vs ridge_gcv (paired t, n=10):**

| ROI | Δ | t(9) | p | Cohen's d |
|-----|------|------|---|-----------|
| V1 | +0.025 | 1.136 | 0.285 | +0.359 |
| V2 | +0.099 | 2.115 | 0.064 | +0.669 |
| **V3** | **+0.102** | **2.574** | **0.030** | **+0.814** |
| V4 | +0.046 | 1.271 | 0.236 | +0.402 |

**Artifact check (LOCO rdm_pearson, smooth_tikh vs ridge_gcv, n=10):**

| ROI | ridge_gcv (SD) | smooth_tikh (SD) | Δ | t(9) | p |
|-----|---------------|-----------------|------|------|---|
| **V1** | 0.034 (0.226) | **0.531 (0.239)** | **+0.496** | **4.24** | **0.002*** |
| V2 | 0.179 (0.282) | **0.457 (0.230)** | +0.278 | 1.97 | 0.081 |
| **V3** | 0.160 (0.200) | **0.398 (0.207)** | **+0.238** | **3.58** | **0.006*** |
| **hV4** | 0.104 (0.281) | **0.410 (0.180)** | **+0.306** | **2.27** | **0.049*** |

> **⚠️ rdm_pearson 재해석 (2026-03-11):** rdm_pearson "개선"은 기만적. RDM 구조 검사 결과: (1) 실제 데이터에 이상적 원형 색조 구조 없음 (Spearman vs ideal ≈ 0), (2) smooth_tikh 예측 RDM은 이상 구조와 반상관 (ρ ≈ -0.5), (3) 예측 RDM 거리가 극도로 압축 (0.06-0.23). 높은 rdm_pearson은 압축된 RDM이 실제 데이터의 noise 구조와 매칭된 것. §9d 참조.

### 6h. 적응형 기저 최적화 (Section 9k-1, 2026-03-12)

#### 목적과 검정 질문

- **질문**: "CVD LOCO 실패가 고정 기저 불일치 때문인가, 뇌 표상 왜곡 때문인가?"
- **방법**: FE 기저 센터를 피험자 × ROI별로 자유 최적화 → LOCO voxel_corr 비교
- **t-test**: Paired one-sample t-test (delta = adaptive − fixed, H₀: delta = 0)
  → "적응 기저가 고정 기저보다 유의하게 개선하는가?"

#### Fixed vs Adaptive LOCO voxel_corr (per-ROI optimal K)

| Subject | Group | V1(K=2) F/A/Δ | V2(K=3) F/A/Δ | V3(K=8) F/A/Δ | hV4(K=3) F/A/Δ |
|---------|-------|---------------|---------------|---------------|----------------|
| sub-01 | HC | +0.135/+0.147/+0.012 | +0.052/+0.156/+0.104 | +0.222/+0.280/+0.058 | +0.040/+0.132/+0.093 |
| sub-02 | HC | +0.040/+0.142/+0.102 | +0.286/+0.312/+0.026 | +0.104/+0.190/+0.086 | +0.511/+0.554/+0.043 |
| sub-03 | HC | +0.162/+0.187/+0.025 | +0.202/+0.230/+0.029 | +0.045/+0.085/+0.041 | +0.363/+0.466/+0.103 |
| sub-04 | HC | +0.182/+0.303/+0.121 | +0.209/+0.333/+0.124 | +0.074/+0.133/+0.059 | +0.256/+0.338/+0.083 |
| sub-05 | HC | +0.309/+0.305/−0.005 | +0.356/+0.378/+0.022 | +0.423/+0.439/+0.016 | +0.026/+0.088/+0.062 |
| sub-06 | HC | −0.005/+0.025/+0.030 | −0.061/+0.049/+0.111 | −0.269/−0.090/+0.179 | +0.313/+0.382/+0.070 |
| sub-07 | HC | +0.251/+0.255/+0.004 | +0.236/+0.237/+0.001 | +0.043/+0.129/+0.087 | −0.059/+0.130/+0.188 |
| sub-08 | CVD | +0.179/+0.267/+0.088 | +0.003/**+0.265**/+0.262 | +0.192/+0.295/+0.102 | +0.067/**+0.383**/+0.316 |
| sub-09 | CVD | +0.018/+0.036/+0.018 | +0.065/+0.125/+0.060 | +0.032/+0.080/+0.048 | +0.079/+0.147/+0.068 |
| sub-10 | CVD | +0.149/+0.149/+0.000 | −0.166/−0.030/+0.136 | +0.203/+0.225/+0.022 | +0.198/+0.283/+0.085 |
| **HC M (SD)** | | +0.153(0.102)/+0.195(0.094) | +0.183(0.132)/+0.242(0.105) | +0.092(0.193)/+0.167(0.152) | +0.207(0.193)/+0.299(0.170) |
| **CVD M (SD)** | | +0.115(0.070)/+0.151(0.094) | −0.032(0.098)/+0.120(0.120) | +0.143(0.078)/+0.200(0.089) | +0.115(0.059)/+0.271(0.097) |

#### Delta 통계 (paired t-test: adaptive − fixed vs 0)

| ROI | K | HC Delta M (SD) | t(6) | p | 개선 |
|-----|---|----------------|------|---|------|
| V1 | 2 | +0.041 (0.046) | 2.194 | 0.071 | 6/7 |
| **V2** | **3** | **+0.059 (0.047)** | **3.081** | **0.022*** | **7/7** |
| **V3** | **8** | **+0.075 (0.048)** | **3.805** | **0.009*** | **7/7** |
| **hV4** | **3** | **+0.092 (0.044)** | **5.151** | **0.002*** | **7/7** |

CVD 개별 delta (n=3, 그룹 검정 불가):

| Subject | V1 | V2 | V3 | hV4 |
|---------|------|------|------|------|
| sub-08 (deutan) | +0.088 | **+0.262** | +0.102 | **+0.316** |
| sub-09 (protan) | +0.018 | +0.060 | +0.048 | +0.068 |
| sub-10 (deutan) | +0.000 | +0.136 | +0.022 | +0.085 |

#### 최적화된 센터 패턴

**sub-08 퇴행 패턴**: V2와 hV4에서 최적 센터가 [0°, 180°, 359°] → 사실상 K=2로 수렴. L-M축 압축(deuteranopia) 증거 — 단일 대립축(red-cyan)이 가용 구조 대부분을 포착.

**HC도 비균등 센터에서 개선**: 고정 FE가 정상 색각에서도 최적이 아님 (hV4 HC delta=+0.092, p=0.002).

#### 순환 편향 경고

> **편향**: 센터 최적화가 전체 8색 LOCO를 목적함수로 사용 → 테스트 색이 센터 선택에 간접 영향. 성능 수치는 **낙관적 상한**. Nested LOCO (Section 4b)에서 unbiased 검증 예정.

#### 핵심 발견

1. **38/40 조합에서 delta ≥ 0** — 거의 보편적 개선 (순환 최적화 하)
2. V2/V3/hV4 HC delta 유의 (모두 p < 0.025); V1 추세 (p=0.071)
3. **sub-08 (deutan)**: 순환 최적화 하 극적 개선 — §6i에서 debiasing 후 무효화
4. 순환 편향 → §6i nested LOCO에서 해결

### 6i. Nested LOCO 검증 (Section 9k-2, 2026-03-12)

#### 목적

§6h의 센터 최적화는 8색 전체 LOCO를 목적함수로 사용 → 순환 편향. Nested (이중) LOCO로 debiasing:

```
외부 fold (8-fold): 1색 hold out for evaluation
  └── 내부 최적화 (7-fold): 나머지 7색으로 센터 최적화
  └── 외부 평가: 최적 센터 + 7색 W → held-out 색 예측
```

3가지 조건 비교: (1) Fixed FE-6, (2) Fixed FE-K (per-ROI optimal), (3) Nested Adaptive

#### 결과: 3-Way 비교 (mean LOCO voxel_corr)

| ROI | K | HC FE-6 | HC FE-K | HC Nested | CVD FE-6 | CVD FE-K | CVD Nested |
|-----|---|:-------:|:-------:|:---------:|:--------:|:--------:|:----------:|
| V1 | 2 | +0.130 | +0.153 | +0.175 | −0.012 | +0.115 | +0.130 |
| V2 | 3 | +0.150 | +0.180 | +0.174 | −0.174 | −0.032 | −0.002 |
| V3 | 8 | +0.023 | +0.112 | +0.110 | −0.008 | +0.081 | +0.086 |
| hV4 | 3 | +0.183 | +0.205 | +0.164 | −0.058 | +0.116 | +0.096 |

#### HC Paired t-test: Nested vs Fixed

모든 ROI에서 Nested ≈ FE-K (delta ≈ 0, 모든 p>0.37). **센터 최적화 = 효과 없음.** hV4는 오히려 adaptive가 나쁜 추세 (delta=−0.041, p=0.075).

#### 과대추정 확인 (Circular vs Nested, HC Mean)

| ROI | Circular | Nested | Bias |
|-----|:--------:|:------:|:----:|
| V1 | +0.195 | +0.175 | +0.020 |
| V2 | +0.242 | +0.174 | +0.068 |
| V3 | +0.167 | +0.110 | +0.056 |
| hV4 | +0.299 | +0.164 | **+0.135** |

sub-08 hV4: circular=+0.383 → nested=+0.081 (bias=**+0.302**). §6h의 "L-M축 압축 증거"는 과적합 산물로 무효화.

#### HC-CVD Gap 분해: 모델 명세별

| ROI | FE-6 d (p) | FE-K d (p) | Gap 감소 |
|-----|:----------:|:----------:|:--------:|
| V1 | 2.01 (0.021) | 0.44 (0.581) | **−78%** |
| V2 | 2.25 (0.022) | 1.80 (0.067) | −20% |
| V3 | 0.17 (n.s.) | 0.18 (n.s.) | — |
| hV4 | 1.36 (0.169) | 0.63 (0.342) | **−54%** |

→ **K 선택이 HC-CVD LOCO gap의 54-78%를 설명.** FE-6 과모수화 문제.

#### 핵심 결론

1. **센터 최적화 = 무효.** 유일한 유효 파라미터는 K (채널 수).
2. **§6h 순환 결과 무효화**: sub-08 "퇴행 센터" = 과적합 산물.
3. **HC-CVD gap 대부분 모델 명세 의존적**: 적절한 K 선택으로 gap 대폭 감소.
4. **잔여 gap** (hV4 d=0.63, p=0.342): n=3 CVD에서 underpowered → Phase 2 filter 타겟.

### 6j. Per-Color Residual 분석 & Cross-Phase 수렴 (Section 9k-3, 2026-03-13)

#### 목적

FE-K 적용 후 남는 HC-CVD gap을 **색별로 분해**하여 어떤 색이 잔여 gap을 주도하는지 확인. Phase 2 SRM prevalidation과의 **독립적 수렴**을 검증.

#### Per-Color LOCO voxel_corr — hV4 FE-3 (Welch t, HC n=7 vs CVD n=3)

| 색 | θ | HC M (SD) | CVD M (SD) | d | p |
|-----|-----|-----------|-----------|:---:|:---:|
| red | 0° | +0.353 (0.225) | +0.310 (0.255) | +0.18 | 0.81 |
| orange | 45° | +0.246 (0.316) | +0.502 (0.224) | −0.94 | 0.22 |
| yellow | 90° | +0.135 (0.422) | +0.213 (0.167) | −0.24 | 0.70 |
| green | 135° | +0.107 (0.427) | +0.055 (0.338) | +0.13 | 0.85 |
| cyan | 180° | −0.008 (0.401) | +0.157 (0.524) | −0.35 | 0.66 |
| **blue** | **225°** | **+0.349 (0.315)** | **+0.025 (0.114)** | **+1.37** | **0.046*** |
| purple | 270° | +0.283 (0.319) | −0.124 (0.196) | +1.54 | 0.060† |
| magenta | 315° | +0.171 (0.384) | −0.211 (0.246) | +1.19 | 0.127 |

#### Warm/Cool 축 분해

| 축 | FE-6 Gap | FE-K Gap | 감소 |
|------|:--------:|:--------:|:----:|
| **Warm (L-M)** | +0.118 | **−0.060** | **>100% (역전)** |
| **Cool (S)** | +0.362 | **+0.237** | **35%만 감소** |

→ K 최적화로 warm-color gap 완전 소멸. Cool-color gap은 원래의 65% 잔존 = **잔여 생물학 후보**.

#### 피험자별 Cool-Color 프로필 (hV4 FE-3)

| 피험자 | Warm 평균 | Cool 평균 | 해석 |
|---------|:---------:|:---------:|------|
| sub-08 (deutan) | +0.227 | −0.058 | Cool 여전히 음수 |
| sub-09 (protan) | +0.340 | −0.197 | Cool 최악 |
| sub-10 (deutan) | +0.244 | +0.140 | Cool 양수 — 보상됨 |
| HC 평균 | +0.210 | +0.199 | Warm/Cool 균형 |

#### Cross-Phase 수렴: SRM Prevalidation ↔ Forward Model

SRM prevalidation (crossnobis pairwise distance)과 forward model LOCO는 **완전히 독립적 파이프라인**.

| 신호 | SRM Prevalidation (Phase 2) | Forward Model (Phase F1) | 수렴? |
|------|---------------------------|------------------------|:----:|
| Blue-purple 왜곡 | V2 blue-purple p=0.042 (유일한 유의 쌍) | hV4 blue d=+1.37 p=0.046 | **YES** |
| Green-blue 압축 | V1/V2/V3 3인 일관 deficit | Blue = CVD 최저 색 | **YES** |
| Red-magenta 확장 | V1/V2/hV4 3인 일관 elevation | Magenta d=+1.19 | **Partial** |
| sub-10 보상 | SRM: HC-like (crossnobis r=0.701) | FE-K: cool 양수 유일 CVD | **YES** |

→ **핵심 수렴**: SRM에서 유일한 유의 group pair (V2 blue-purple p=0.042)와 FE에서 유일한 유의 per-color gap (hV4 blue p=0.046)이 **동일 색 영역**을 지목.

#### 핵심 결론

1. 잔여 gap은 **S-축 특이적**: blue (d=+1.37), purple (d=+1.54)가 주도.
2. Warm gap은 **완전한 모델 명세 산물**: FE-3에서 역전.
3. **Cross-phase 수렴 확인**: 두 독립 파이프라인이 blue/purple/magenta를 CVD 왜곡 중심으로 지목.
4. **Phase 2 filter 함의**: T_ψ(θ)는 θ ∈ [180°, 315°] (cool/S-축)에 집중, warm 영역은 최소 보정.

---

## 7. GO/NO-GO Gate

### Gate 기준

| Criterion | Metric | Threshold |
|-----------|--------|-----------|
| C1 Reliability | Split-half RDM correlation | > 0.3 |
| C2 Normalized Fit | LOCO voxel_corr / NC_voxel_r_sb | > 0.2 |
| C3 Interpolation | HC LOCO voxel_corr > 0 (p < 0.05) | one-tail |
| C3b Permutation | 10K color-shuffle null | p < 0.05 |

### ridge_gcv Gate — FE-6 (확정)

| ROI | C1 | C2 (NC-Norm) | C3 (t-test) | C3b (Perm) | Overall |
|-----|----|----|----|----|---------|
| V1 | PASS (0.416) | PASS (0.227) | PASS (p=0.006) | FAIL (p=0.274) | **CONDITIONAL GO** |
| V2 | PASS (0.420) | PASS (0.268) | PASS (p=0.040) | FAIL (p=0.311) | **CONDITIONAL GO** |
| V3 | PASS (0.398) | FAIL (0.061) | FAIL (p=0.404) | FAIL (p=0.880) | **NO-GO** |
| hV4 | PASS (0.603) | PASS (0.316) | PASS (p=0.026) | **PASS (p=0.044)** | **PRIMARY GO** |

### ridge_gcv Gate — Per-ROI 최적 Basis (2026-03-11 추가)

| ROI | Basis | C3 (LOCO>0) | C3b (Perm Stouffer) | FE-6 대비 변화 |
|-----|-------|-------------|---------------------|--------------|
| V1 | FE-2 | **PASS (p=0.005)** | FAIL (p=0.170) | 0.274→0.170 (개선, FAIL) |
| V2 | FE-3 | **PASS (p=0.008)** | FAIL (p=0.125) | 0.311→0.125 (개선, FAIL) |
| **V3** | **FE-8** | MARGINAL (p=0.065) | **PASS (p=0.045)** | **NO-GO → PASS** |
| hV4 | FE-3 | **PASS (p=0.021)** | **PASS (p=0.026)** | 0.044→0.026 (강화) |

> **V3 회복**: FE-8로 V3가 NO-GO→PASS. V1/V2는 FE-{2..12} + OPP-2/4/4rect + intercept model 모두 FAIL — 8-stimulus LOCO의 구조적 한계 확인 (basis mismatch 아님).

### smooth_tikh Gate (REJECTED)

| ROI | C1 | C2 (NC-Norm) | C3 (LOCO > 0) | C3c (rdm_pearson) | C3b (Perm) | Status |
|-----|----|----|----|----|----|----|
| V1 | PASS (0.416) | PASS (0.297) | PASS (p=0.007) | ~~PASS~~ 기만적 | **FAIL (p=0.331)** | **REJECTED** |
| V2 | PASS (0.420) | PASS (0.475) | PASS (p<0.001) | ~~PASS~~ 기만적 | **FAIL (p=0.188)** | **REJECTED** |
| V3 | PASS (0.397) | FAIL (0.185) | FAIL (p=0.170) | ~~PASS~~ 기만적 | **FAIL (p=0.613)** | NO-GO |
| V4 | PASS (0.603) | PASS (0.254) | PASS (p=0.047) | ~~PASS~~ 기만적 | **FAIL (p=0.613)** | **REJECTED** |

> **C3c (rdm_pearson) 소급 무효화**: RDM 검사 결과 실제 데이터에 원형 색조 구조가 없고, smooth_tikh 예측 RDM은 이상적 원형 구조와 **반상관** (ρ ≈ -0.5). rdm_pearson "개선"은 noise 패턴 매칭에 불과.

**Decision**: hV4 = **primary ROI** (FE-6 perm p=0.044). V3 = **conditional** (FE-8 perm p=0.045). V1/V2 = **discrimination-only** (LOCO 전 basis FAIL 확인 — FE, OPP, intercept 모두). **smooth_tikh 전면 기각.**

---

## 8. HC-CVD 비교

### Group Comparison (ridge_gcv, LOCO)

| ROI | HC M (SD) | CVD M (SD) | Cohen's d | p (Welch) |
|-----|----------|----------|-----------|-----------|
| V1 | +0.130 (0.097) | -0.012 (0.054) | **+1.61** | **0.021** |
| V2 | +0.150 (0.188) | -0.174 (0.130) | **+1.85** | **0.022** |
| V3 | +0.023 (0.240) | -0.008 (0.163) | +0.14 | 0.819 |
| hV4 | +0.183 (0.200) | -0.058 (0.207) | +1.19 | 0.169 |

### Group Comparison (smooth_tikh, LOCO)

| ROI | HC M (SD) | CVD M (SD) | Cohen's d | p (Welch) |
|-----|----------|----------|-----------|-----------|
| V1 | +0.143 (0.109) | +0.039 (0.180) | +0.80 | 0.429 |
| **V2** | **+0.246 (0.100)** | **-0.070 (0.063)** | **+3.43** | **0.001** |
| V3 | +0.100 (0.254) | +0.151 (0.081) | -0.23 | 0.641 |
| V4 | +0.190 (0.253) | +0.080 (0.255) | +0.43 | 0.568 |

smooth_tikh로 V2 HC-CVD 효과 크기 거의 2배 (d=1.85 → d=3.43).

### Individual CVD Profiles (ridge_gcv)

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
| HC z-score | -1.55 | -0.93 | -0.90 | -1.09 |
| Crawford-Howell p | 0.197 | 0.419 | 0.433 | 0.346 |

**sub-10 (deutan)**

| Metric | V1 | V2 | V3 | hV4 |
|--------|------|------|------|------|
| LOCO r | +0.045 | -0.257 | +0.118 | +0.137 |
| HC z-score | -0.88 | -2.17 | +0.40 | -0.23 |
| Crawford-Howell p | 0.444 | 0.089 | 0.723 | 0.837 |

### Individual CVD Profiles (smooth_tikh)

**sub-08 (deutan)**: V2 **significant** (CH p=0.011) — ridge_gcv에서는 trending (0.099)
**sub-09 (protan)**: V2 **significant** (CH p=0.039) — ridge_gcv에서는 ns (0.419)
**sub-10 (deutan)**: V2 **significant** (CH p=0.040) — ridge_gcv에서는 trending (0.089)

**핵심**: smooth_tikh로 3명 CVD **모두** V2에서 HC 대비 유의미한 일탈 (모두 CH p < 0.05).

> **⚠️ 주의 (2026-03-11):** smooth_tikh의 HC-CVD 분리 효과(d=3.43)는 공간 공분산 포착에 의한 것으로, 진정한 색 판별 신호가 아님. smooth_tikh가 기각되었으므로 이 효과는 분석에 사용할 수 없음. ridge_gcv 기반 V2 HC-CVD d=1.85 (p=0.022)가 유효한 결과.

---

## 9. smooth_tikh 조사 결과 (REJECTED)

### 9a. Permutation Test — 고정 파라미터 (10K shuffles, HC)

| ROI | Observed | Null Mean | p_perm |
|-----|---------|-----------|--------|
| V1 | 0.189 | 0.187 | 0.331 |
| V2 | 0.216 | 0.212 | 0.188 |
| V3 | 0.125 | 0.128 | 0.613 |
| V4 | 0.239 | 0.241 | 0.613 |

**전 ROI 실패.** Observed ≈ null mean — 공간 공분산만 포착, 색 신호 아님.

### 9b. 구제 시도 1: Condition-Centering

Per-run condition centering (각 run 내 8색 평균 제거)은 color label shuffle와 **교환 가능(commute)**:

```
mean(amp[:, perm, :], axis=1) == mean(amp, axis=1)  # 셔플 순서 무관
```

따라서 centering은 permutation test 결과를 **변경할 수 없음**. 실증 확인: 동일한 p-값 (예: sub-02 hV4 p=0.015, centered/uncentered 동일).

### 9c. 구제 시도 2: 재최적화 Permutation

셔플마다 (α, β)를 inner LOCO-CV로 재선택하는 방법 시도.

결과 (5 perms, sub-02 hV4):
- Null beta 분포: **β=1000이 45%** (가장 많음), β=0 26%, β=100 9%
- 셔플 데이터에서도 높은 β가 선호됨 — 정규화가 noise 적합에도 유리
- 관측값도 하락: 0.172 (고정 0.239에서)
- Delta (obs - null_mean) ≈ -0.007 — 여전히 유의하지 않음

### 9d. RDM 구조 검사

**실제 데이터 vs 이상적 원형 구조 (Spearman, HC mean):**

| ROI | Actual vs Ideal | 해석 |
|-----|----------------|------|
| V1 | -0.008 | 원형 구조 없음 |
| V2 | +0.044 | 원형 구조 없음 |
| hV4 | +0.004 | 원형 구조 없음 |

**smooth_tikh 예측 vs 이상적 원형 구조:**

| ROI | Predicted vs Ideal | 해석 |
|-----|-------------------|------|
| V1 | **-0.624** | 이상 구조와 반상관 |
| V2 | **-0.580** | 이상 구조와 반상관 |
| hV4 | **-0.442** | 이상 구조와 반상관 |

**RDM 거리 압축:** smooth_tikh 예측 RDM 거리 0.06–0.23 (실제 0.66–1.49 대비 극도로 압축).

**rdm_pearson "개선" 재해석:** 높은 rdm_pearson (V1=0.531)은 smooth_tikh의 압축/평탄 RDM이 실제 데이터의 **비원형 noise 구조**와 패턴 매칭된 것. 진정한 색 기하학 보존이 아님.

### 9e. smooth_tikh 최종 결론

| 접근법 | 발견 | 실패 이유 |
|--------|------|-----------|
| 고정 파라미터 permutation | 전 p > 0.18 | 공간 공분산이 voxel_corr 지배 |
| Condition-centering | Shuffle과 교환 | 구조적으로 permutation 변경 불가 |
| 재최적화 permutation | Null beta ≥ observed | Smoothness가 noise 적합에도 유리 |
| RDM 기반 평가 | 이상 구조와 반상관 | rdm_pearson 개선은 noise 패턴 매칭 |

**근본 원인:** β=100이 near-rank-1 W를 생성 (모든 열 거의 동일) → 예측이 단일 공간 패턴에 지배됨 → 높은 voxel_corr, 높은 rdm_pearson, 그러나 색 판별 내용 없음.

---

## 10. 핵심 발견 및 결정

### 발견

1. **LORO-LOCO 해리**: SRM prior는 run-level variance를 포착하지만 color-specific tuning은 놓침. prior_ft LORO 승리, LOCO 패배.
2. **ridge_gcv = 확정된 최적 LOCO 모델**: HC mean positive across V1/V2/hV4. smooth_tikh 기각 후 유일한 선택지.
3. **FE 형태 확정, 채널 수는 ROI 의존**: Fourier basis 기각 (half-wave cos²이 peaked tuning에 우수). 최적 K: V1→2, V2→3, V3→8, hV4→3.
4. **Bias-variance tradeoff**: LORO는 K↑로 단조 개선 (r=+0.82~0.89). LOCO는 V1/V2에서 K↓가 유리 (r=-0.23/-0.29). 적은 채널 = 강한 보간 제약 = overfitting 방지.
5. **V3 회복: FE-8로 NO-GO → PASS**: Permutation p=0.360→0.045. V3 실패는 basis 선택 문제였음.
6. **V1/V2: 모든 basis에서 LOCO FAIL**: FE-{2..12} + OPP-2/4/4rect 모두 permutation FAIL. Intercept model도 변화 없음. 8-stimulus LOCO의 구조적 해상도 한계 확인 (Red Team #3 중화 완료).
7. **hV4 genuine color interpolation**: Permutation p=0.044 (FE-6), p=0.026 (FE-3). Per-color uniform, residual near-random.
8. **HC-CVD gap은 K 의존적이며 축 특이적 (§6i-6j 업데이트)**: 총량: V1 d=2.01→0.44 (−78%), hV4 d=1.36→0.63 (−54%). Per-color 분해: warm(L-M) gap **역전** (>100%), cool(S) gap **65% 잔존**. Blue d=+1.37 p=0.046, purple d=+1.54 p=0.060.
9. **잔여 gap은 S-축 특이적**: FE-K 후 잔여 gap은 blue/purple/magenta에 집중. 센터 최적화 = 무효. Phase 2 filter 타겟: θ ∈ [180°, 315°].
10. **Cross-phase 수렴 확인 (§6j)**: SRM prevalidation (V2 blue-purple p=0.042, 유일한 유의 쌍) ↔ FE (hV4 blue p=0.046, 유일한 유의 per-color gap). 독립 파이프라인이 동일 색 영역 지목.
11. **Prior 자체가 LOCO와 비호환**: H1(shape), H2(uncertainty) 모두 기각 — 구조적 한계.
12. **smooth_tikh 전면 기각**: Permutation 실패 + 3가지 구제 시도 모두 실패 + RDM "개선" 기만적.
13. **실제 데이터에 이상적 원형 색조 구조 없음**: 전 ROI에서 Spearman vs ideal ≈ 0.
14. **Opponent basis 전 ROI FAIL**: OPP-2/4/4rect 모두 V1/V2 permutation 실패 → V4만 통과하는 해리는 진짜 영역적 특성 (basis mismatch 아님).
15. **Intercept model 무효**: 공유 공간 평균 제거해도 p-값 불변 → 인코딩 신호는 hue-modulated pattern에 존재.

### 확정된 결정

1. **Encoder**: **ridge_gcv 확정**. smooth_tikh 기각.
2. **Basis**: FE 형태 확정. Per-ROI 최적: V1→FE-2, V2→FE-3, V3→FE-8, hV4→FE-3/FE-6. Paired t-test로 유의차 없으나 방향 일관적.
3. **V3 상태 변경**: NO-GO → **CONDITIONAL** (FE-8 basis로 permutation 통과 시).
4. **Phase 2 역할 분리**: hV4 = primary oracle (perm PASS). V3 = conditional (FE-8). V1/V2 = discrimination-only (LOCO 전 basis FAIL 확인).
5. **Prior ablations (9a)**: BLOCKED — prerequisite 미충족.
6. **RRR/Smoothness (9g)**: 기각됨 — 기만적 개선.
7. **smooth_tikh (9h-9i)**: 기각됨 — 공간 공분산 포착, 색 신호 아님.

### 완료됨

- [x] smooth_tikh 10K permutation test → **전 ROI 실패**
- [x] Condition-centering 시도 → **교환 문제로 불가**
- [x] 재최적화 permutation 시도 → **null beta 여전히 높음**
- [x] RDM 구조 검사 → **원형 구조 없음, rdm_pearson 기만적**
- [x] **최종 결정: ridge_gcv 확정**
- [x] FE 채널 수 비교 (FE-2~12) → V3 회복, V1/V2 1D 한계 확인
- [x] Per-ROI optimal basis permutation → V3 FE-8 PASS, hV4 FE-3 강화
- [x] Opponent basis test (OPP-2/4/4rect, 10K) → **V1/V2 전 basis FAIL — Red Team #3 중화**
- [x] Intercept model permutation test (10K) → **Standard ≈ Intercept — p-값 불변**
- [x] Per-color residual 분석 (§6j) → **blue d=1.37 p=0.046, warm gap 역전, cool gap 65% 잔존**
- [x] Cross-phase 수렴 검증 (§6j) → **SRM V2 blue-purple p=0.042 ↔ FE hV4 blue p=0.046 수렴 확인**
- [x] Red Team 대응 → **#3 완전 중화, #1/#2/#4 문서화, #5 부분 대응** (§12)

### 대기 중

- [ ] notion.md / RESULTS.md 정리 (중복 제거, 구조 개편)
- [ ] Phase 2 사전등록 (Red Team #4 대응)

---

## 12. Red Team 대응

> 자체 비판 2026-03-11 수행. 전체 보고서: `results/redteam/2026-03-11.md`

### RT-1. 통계적 검정력 (N=3 CVD) — FATAL→MITIGATED

**비판:** N=3 CVD로 그룹 수준 추론 불가. Welch t-test (df~4-5) 불안정, 효과크기 부풀림.

**대응 — Case Study 프레이밍:**
- 모든 CVD 결과는 **Crawford & Howell (2010) 개인별 단일사례 분석**으로 보고
- 그룹 수준 CVD 비교 (Welch t-test)는 **기술적/탐색적** 보고, 확인적 아님
- HC 그룹 결과 (N=7) = 검증된 모델; CVD 적용 = "N=3 개념 증명"
- 확정적 CVD 그룹 주장에 필요한 최소 표본: 그룹당 N≥12 (d=0.8, α=0.05, power=0.80)
- CVD-CVD RDM 상관 (0.276 > HC-HC 0.158): **기술적 관찰**로만 보고

**파이프라인 영향:** 없음. Phase 2 filter는 개인별 작동; 그룹 수준 CVD 추론 불필요.

### RT-2. 다중비교 보정 (hV4 p=0.044) — FATAL→MITIGATED

**비판:** 4 ROI 검정; Bonferroni 기준 0.0125; hV4 p=0.044 탈락. HC-CVD hV4 voxel_corr p=0.169가 결과를 약화시킨다는 주장.

**반박 — HC-CVD 비교는 인코더 검증과 무관:**

Permutation test는 *"HC forward model이 진정한 색 보간 신호를 포착하는가?"*를 검정. 이는 HC-only 모델 검증. HC-CVD voxel_corr (p=0.169)는 *"HC와 CVD의 LOCO 성능이 다른가?"*로 완전히 다른 질문. 인코더 검증에 그룹 비교가 필요하지 않음. "Cross-pipeline cherry-picking" 비판도 부적절: Phase 1 permutation = 인코더 검증, Phase 3 LOCO MAE = 디코더 기반 그룹 차이 — 서로 다른 질문에 답하는 별도 파이프라인.

**대응 — 사전 지정 Primary ROI + 수렴 증거:**

**hV4가 primary hypothesis인 사전 근거:**
1. **선행연구**: Brouwer & Heeger (2009)가 V4/VO1을 novel-color reconstruction 부위로 확인
2. **데이터 품질**: 최고 noise ceiling (HC 0.702), 최고 split-half reliability (HC 0.603)
3. **생물학적 근거**: hV4의 hue-selective neuron이 FE-6 원형 basis와 가장 호환

**보정 결과:**
- hV4 = **primary** (미보정 p=0.044; FE-3: p=0.026)
- V1/V2/V3 = **secondary/exploratory** (보고 시 명시)
- Bonferroni 4 ROI: hV4 FE-6 p=0.044 > 0.0125 → **미통과** (명시)
- FDR (BH) per-ROI optimal: hV4 FE-3 q=0.104 → **미통과** (명시)

**수렴 증거 (permutation p-value와 독립):**

| 증거 | V1/V2 | hV4 |
|------|-------|-----|
| Permutation | FAIL | p=0.044* |
| Friedman 균일성 | 비균일* | **균일** (p=0.485) |
| Residual 구조 | 체계적 (r=0.45) | **근무작위** (r=0.053) |
| NC-normalized fit | 0.23/0.27 | **0.32** |
| Noise ceiling | 0.47/0.51 | **0.70** |

### RT-3. 구분 vs 보간 해리 — NEUTRALIZED

**비판:** 사후 합리화; 대안 basis 미검증.

**결과:** 3종 opponent basis (OPP-2/4/4rect) + FE 채널 변형 (FE-2~12) + intercept 모델 직접 검증. **V1/V2에서 모든 basis FAIL.** FE-6만이 V4에서 유일하게 통과 (p=0.039).

해리는 **8-stimulus LOCO의 V1/V2 구조적 해상도 한계**로 확정. Basis mismatch 아님. 전체 결과: §6e (Opponent Basis Test).

### RT-4. 분석적 자유도 — ADDRESSED

**비판:** 8 모델 × 3 basis × 4 ROI × 6 metric; 하나만 p=0.044.

**대응 — 순차적 제거 논리:**

1. **Basis 선택**: FE-6 > LF-4 > LF-6, paired LOCO CV 기반 (p=0.045/0.042/0.016). Permutation p-value 참조하지 않음.
2. **모델 선택**: ridge_gcv = LOCO voxel_corr 최고. smooth_tikh는 permutation에서 **독립적으로 기각**.
3. **Permutation**: 사전 선택된 모델/basis 조합에 대한 **최종 검증 gate**. 모델/basis 선택에 관여하지 않음.
4. **Metric 선택**: voxel_corr = forward encoding 문헌 표준 (B&H 2009). Parametric → permutation 전환은 "원하는 패턴" 때문이 아니라, voxel covariance가 non-zero baseline 생성 → H₀: μ=0이 부적절하기 때문.

**Phase 2 사전등록:** Phase 2 실행 전 계획.

### RT-5. "CVD 실패 = 데이터" 서사 — Model Comparison으로 수정 (§4b 이후)

**비판:** 반증 불가; CVD reliability가 HC보다 높아 "왜곡" 서사와 모순.

**수정된 프레이밍 — 모델 비교:**

1. **"실패 = 데이터" → "모델 명세 민감도"로 수정:**
   - HC-CVD gap은 **주로 K 의존**: V1 d=2.01→0.44 (−78%), hV4 d=1.36→0.63 (−54%)
   - 센터 최적화 = 효과 없음 (nested LOCO, §4b 확인)
   - FE-6의 큰 gap = 과모수화: K=6, 8자극 → df=1, CVD 표상에 불충분
   - **재프레이밍**: FE-6 하의 CVD LOCO 실패 = 모델 선택 문제, 반드시 생물학적 결함 아님

2. **높은 CVD reliability 해명:**
   - Reliability (0.699 > 0.603) = 패턴이 런 간 일관되게 재현
   - "모델 명세 요구가 다름"과 양립 가능 — reliability는 안정성 측정, 모델 적합도 아님

3. **이전 반증 예측 — 해결됨:**
   - ~~Adaptive basis: CVD center가 L-M 축 압축 보이면 → basis mismatch 확인~~
   - **결과 (§4b)**: Debiasing 후 adaptive center ≈ uniform. sub-08 "degenerate [0,180,359]°" = 과적합 산물
   - **새로운 검증 가능한 질문**: CVD K-sensitivity가 모델 선택 문제(bias-variance)인지 vs 진정한 차원 축소인지? 필요: (a) PCA 유효 차원 분석, (b) SNR 통제 시뮬레이션, (c) 행동 데이터 상관

4. **남은 취약점 — K-sensitivity 해석:**
   - CVD가 HC보다 K 감소에서 더 많은 이득 → 두 가지 설명:
     - (A) 모델 선택: FE-6이 모든 피험자에게 과모수화; CVD가 표상 차이로 더 영향 받음
     - (B) 생물학: CVD의 유효 색 차원이 진정으로 적음
   - 현재 데이터 (n=3 CVD)로 A/B 구분 불가
   - **중화 필요**: PCA (8색 패턴), 또는 행동 데이터 (Farnsworth-Munsell) 상관

5. **Phase 2 filter 정합성:**
   - `W_s @ C(T_psi(θ))`: HC W_s (hV4, FE-3, ridge_gcv) 사용
   - 적절한 K에서 T_psi는 **더 작은 잔여갭** 교정 (d=0.63 vs d=1.36)
   - hV4 RDM HC≈CVD (p=0.559) → T_psi는 단조(순서 보존) 변환

---

## 11. Phase 2 연결

W_s가 Phase 2의 **prediction engine** (frozen):

```
theta → C(theta) → W_s @ C(theta) = Y_hat_s(theta)
```

Phase 2 filter T_psi는 W_s의 **upstream**에서 작동:

```
theta → T_psi(theta) → C(T_psi(theta)) → W_s @ C(T_psi(theta))
```

W_s는 filter optimization 시작 전에 고정. Filter T_psi는 stimulus space에서만 작동하며 W_s를 수정하지 않음.

**역할 분리**:

| | V1/V2 | hV4 |
|--|-------|-----|
| Phase 2 역할 | Filter correction target | Color interpolation oracle |
| 근거 | HC-CVD 차이 유의 (d>1.0) | Genuine color interpolation (perm p=0.044) |
| 활용 | Filter 적용 대상 | Cross-ROI validation, color axis reference |

**Encoder**: ridge_gcv 확정. smooth_tikh 기각되었으므로 ridge_gcv 기반 HC-CVD 비교 (V2 d=1.85, p=0.022) 사용.
