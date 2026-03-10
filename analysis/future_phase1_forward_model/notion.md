# Future Phase 1: Group-Prior Prediction Model

> **프로젝트**: Color Vision Deficiency Neural Representation Analysis
> **날짜**: 2026-03-10 (정리: 2026-03-11)
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
| **smooth_tikh** | W = (C'C + αI + βD'D)⁻¹C'X | **Inner LOCO** | H3 (smoothness) | **Leading candidate** — artifact check 통과, perm 대기 |
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

**핵심 교훈**: 동일 수식(smoothness)도 inner LORO → artifact, inner LOCO → genuine improvement. Inner CV 목적 함수가 결정적.

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

**FE-6 vs LF-4 (paired t, n=10):** LOCO에서 V1 p=0.045, V2 p=0.042, hV4 p=0.016. LORO에서 전 ROI p<0.001. **FE-6 확정.**

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

Section 18 artifact이 LOCO에 적용되지 않는 이유: all-data fitting에서는 train-test 겹침으로 β=100이 모든 예측을 평탄화 → rdm_pearson ↓. LOCO에서는 각 예측이 held-out 색에 대한 독립 보간 → smoothing이 tuning curve를 genuinely 개선 → rdm_pearson ↑.

---

## 7. GO/NO-GO Gate

### Gate 기준

| Criterion | Metric | Threshold |
|-----------|--------|-----------|
| C1 Reliability | Split-half RDM correlation | > 0.3 |
| C2 Normalized Fit | LOCO voxel_corr / NC_voxel_r_sb | > 0.2 |
| C3 Interpolation | HC LOCO voxel_corr > 0 (p < 0.05) | one-tail |
| C3b Permutation | 10K color-shuffle null | p < 0.05 |

### ridge_gcv Gate (확정)

| ROI | C1 | C2 (NC-Norm) | C3 (t-test) | C3b (Perm) | Overall |
|-----|----|----|----|----|---------|
| V1 | PASS (0.416) | PASS (0.227) | PASS (p=0.006) | FAIL (p=0.274) | **CONDITIONAL GO** |
| V2 | PASS (0.420) | PASS (0.268) | PASS (p=0.040) | FAIL (p=0.311) | **CONDITIONAL GO** |
| V3 | PASS (0.398) | FAIL (0.061) | FAIL (p=0.404) | FAIL (p=0.880) | **NO-GO** |
| hV4 | PASS (0.603) | PASS (0.316) | PASS (p=0.026) | **PASS (p=0.044)** | **PRIMARY GO** |

### smooth_tikh Gate (permutation 대기)

| ROI | C1 | C2 (NC-Norm) | C3 (LOCO > 0) | C3c (rdm_pearson) | C3b (Perm) | Status |
|-----|----|----|----|----|----|----|
| V1 | PASS (0.416) | PASS (0.297) | PASS (p=0.007) | PASS (0.531) | PENDING | **PENDING PERM** |
| V2 | PASS (0.420) | PASS (0.475) | PASS (p<0.001) | PASS (0.457) | PENDING | **PENDING PERM** |
| V3 | PASS (0.397) | FAIL (0.185) | FAIL (p=0.170) | PASS (0.398) | PENDING | NO-GO |
| V4 | PASS (0.603) | PASS (0.254) | PASS (p=0.047) | PASS (0.410) | PENDING | **PENDING PERM** |

**Decision**: hV4 = **primary ROI** (유일하게 permutation 통과). V1/V2 = **conditional/supportive**. V3 = excluded.

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

---

## 9. 핵심 발견 및 결정

### 발견

1. **LORO-LOCO 해리**: SRM prior는 run-level variance를 포착하지만 color-specific tuning은 놓침. prior_ft LORO 승리, LOCO 패배.
2. **ridge_gcv = 현재 최적 LOCO 모델**: HC mean positive across V1/V2/hV4.
3. **FE-6 basis 확정**: Fourier basis 가설 기각 (half-wave cos²이 peaked tuning에 우수).
4. **hV4만 genuine color interpolation**: Permutation p=0.044, per-color uniform, residual near-random. V1/V2는 covariance baseline (~0.11)에 의해 인플레이션.
5. **HC-CVD LOCO gap**: V1 d=1.61 (p=0.021), V2 d=1.85 (p=0.022). CVD의 altered representation 확인.
6. **Prior 자체가 LOCO와 비호환**: H1(shape), H2(uncertainty) 모두 기각 — 구조적 한계.
7. **smooth_tikh는 genuine improvement**: Artifact check 통과 (rdm_pearson ↑). Inner LOCO CV가 결정적 차이.
8. **smooth_tikh로 V2 HC-CVD 효과 극대화**: d=3.43 (p=0.001), 3명 CVD 모두 V2에서 유의미한 일탈.
9. **V3 전면 제외**: 모든 gate criteria FAIL.

### 확정된 결정

1. **Encoder**: ridge_gcv (현재). smooth_tikh = leading candidate (permutation test 후 최종 결정).
2. **Basis**: FE-6 확정.
3. **Prior ablations (9a)**: BLOCKED — prerequisite 미충족.
4. **RRR/Smoothness (9g)**: 기각됨 — 기만적 개선.
5. **Phase 2 역할 분리**: V1/V2 = filter correction target (HC-CVD 차이 유의), hV4 = color interpolation oracle.

### 대기 중

- [ ] smooth_tikh 10K permutation test (`run_smooth_tikh_perm.sbatch`)
  - 통과 → smooth_tikh 채택 (Phase 2 encoder)
  - 실패 → ridge_gcv 유지

---

## 10. Phase 2 연결

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

**smooth_tikh 채택 시 기대 효과**: V2 HC-CVD d=3.43 (2배 증가), NC-normalized 30%→48%, 3명 CVD 모두 V2 유의 (CH p<0.05).
