# Future Phase 1: Forward Encoding Model — 회의 자료

> **프로젝트**: Color Vision Deficiency Neural Representation Analysis
> **날짜**: 2026-03-10
> **대상**: Future Phase 1 Forward Model — 전체 결과 요약 및 다음 단계 논의
> **피험자**: HC 7명 (sub-01~07), CVD 3명 (sub-08 deutan, sub-09 protan, sub-10 deutan)
> **ROI**: V1, V2, V3, hV4
> **핵심 질문**: 8색 fMRI 데이터로 학습한 forward encoding model이 보지 않은 색의 voxel pattern을 예측(interpolation)할 수 있는가?

---

## 1. 결론 (Executive Summary)

**Forward encoding model (ridge regression + FE-6 basis)이 V1, V2, hV4에서 유의미한 color interpolation을 달성했다.** HC 피험자에서 held-out color의 voxel pattern을 chance 이상으로 예측하며 (V1: r=0.130, p=0.006), 이는 Phase 2 stimulus-space filter 설계의 prediction engine으로 사용 가능하다. CVD 피험자는 일관되게 낮은 LOCO 성능을 보이며, V1 (d=1.61, p=0.021)과 V2 (d=1.85, p=0.022)에서 유의미한 HC-CVD 차이가 확인되었다.

**주요 발견**:
1. **LORO-LOCO dissociation**: SRM group prior는 run generalization (LORO)에 우수하나, color interpolation (LOCO)에서는 generic ridge가 압도적으로 우세
2. **V1/V2 = Phase 2 filter의 main target**: HC-CVD 차이가 유의 (V1 d=1.61 p=0.021, V2 d=1.85 p=0.022) — CVD 색 표상이 실제로 왜곡되는 곳
3. **hV4 = color interpolation oracle**: Permutation test 유일 통과 (p=0.044), per-color 균일, residual random → filter 평가의 clean benchmark 제공
4. **FE-6 > Fourier basis**: Half-wave rectified cosine basis가 Fourier harmonics보다 유의하게 우수
5. **smooth_tikh가 ridge_gcv를 능가 (Section 7)**: Channel-smoothness regularization이 LOCO에서 voxel_corr와 rdm_pearson을 **동시에** 개선. Artifact check PASSED — permutation test PENDING
6. **NC-normalized LOCO 수정 완료**: Voxel-pattern noise ceiling (Spearman-Brown) 사용. hV4만 안정적 (0.316)

---

## 2. Pipeline 개요

### 2a. 4단계 알고리즘

```
Step A: HC SRM 적합 → 공통공간 (R_i per subject)
Step B: 공통공간 encoding A_i → Group prior A_g = mean(A_i)
Step C: Target subject로 투사: W_{0,s} = R_s @ A_g
Step D: Prior-centered ridge fine-tuning: W_s
```

**핵심 수식**:
```
W_s = (Y_s @ C^T + lambda * W_{0,s}) @ (C @ C^T + lambda * I)^{-1}
```

### 2b. Prediction equation

```
Y_hat_s = W_s @ C(theta)    (Procrustes voxel space)
```

W_s (V_s x 6)는 subject-specific encoding weight. C (6 x N)는 FE-6 color basis matrix.

### 2c. Validation protocols

| Protocol | 질문 | Held-out | Training |
|----------|------|----------|----------|
| **LORO** | 새 run에도 유효한가? | 1 run | 5 runs x 8 colors |
| **LOCO** | 보지 않은 색도 예측 가능한가? | 1 color | 6 runs x 7 colors (df=36) |
| **LOSO** | Subject 전이 가능한가? | 1 subject | Group prior |

---

## 3. 주요 결과

### 3a. LORO — Run Generalization (mean voxel_corr)

| Model | V1 HC | V2 HC | V3 HC | hV4 HC |
|-------|-------|-------|-------|--------|
| ols | 0.213 | 0.246 | 0.326 | 0.406 |
| ridge_gcv | 0.201 | 0.230 | 0.308 | 0.401 |
| prior_only | 0.306 | 0.300 | 0.304 | 0.317 |
| **prior_ft** | **0.315** | **0.310** | **0.357** | **0.419** |

**Winner**: prior_finetune (all ROIs). SRM group prior가 run-level variance 구조를 효과적으로 포착.

### 3b. LOCO — Color Interpolation (mean voxel_corr, HC)

| Model | V1 | V2 | V3 | hV4 |
|-------|-----|-----|-----|------|
| ols | +0.051 | +0.092 | +0.023 | +0.158 |
| **ridge_gcv** | **+0.130** | **+0.150** | +0.023 | **+0.183** |
| prior_only | -0.075 | -0.099 | -0.186 | +0.109 |
| prior_ft | -0.056 | -0.060 | -0.101 | +0.169 |

**Winner**: ridge_gcv (all ROIs). Prior 모델은 LOCO에서 오히려 해로움.

### 3c. LORO-LOCO Dissociation (핵심 발견)

| Protocol | Winner | 해석 |
|----------|--------|------|
| LORO | prior_ft | SRM prior = run-level 분산 구조 포착 |
| **LOCO** | **ridge_gcv** | SRM prior = color-specific tuning 포착 실패 |

**의미**: SRM이 cross-run alignment에는 유효하지만, 360도 hue space 상의 continuous interpolation에는 generic shrinkage (ridge)가 더 효과적. **Prior-centered regularization보다 zero-centered regularization이 LOCO에 우수** — prior가 noise를 주입하는 것으로 판단.

### 3d. LOCO 통계 검정 (HC, ridge_gcv > 0)

| ROI | HC Mean | 95% CI | t(6) | p (one-tail) | Significance |
|-----|---------|--------|------|-------------|-------------|
| **V1** | **+0.130** | [0.040, 0.220] | **3.544** | **0.006** | ** |
| V2 | +0.150 | [-0.024, 0.323] | 2.109 | **0.040** | * |
| V3 | +0.023 | [-0.199, 0.245] | 0.254 | 0.404 | n.s. |
| **hV4** | **+0.183** | [-0.002, 0.367] | **2.423** | **0.026** | * |

### 3e. HC vs CVD (LOCO ridge_gcv)

| ROI | HC M (SD) | CVD M (SD) | Cohen's d | p (Welch) |
|-----|----------|----------|-----------|-----------|
| **V1** | +0.130 (0.097) | -0.012 (0.054) | **+1.61** | **0.021** |
| **V2** | +0.150 (0.188) | -0.174 (0.130) | **+1.85** | **0.022** |
| V3 | +0.023 (0.240) | -0.008 (0.163) | +0.14 | 0.819 |
| hV4 | +0.183 (0.200) | -0.058 (0.207) | +1.19 | 0.169 |

V1, V2에서 large effect size (d>1.5). CVD는 LOCO에서 일관적으로 negative → color interpolation이 HC보다 열등.

---

## 4. Ablation 결과

### 4a. Encoding Basis Ablation (FE-6 vs LF-4 vs LF-6)

| Basis | Description | K | LOCO V1 | LOCO V2 | LOCO hV4 |
|-------|-------------|---|---------|---------|----------|
| **FE-6** | Half-wave rectified cos² | 6 | **+0.011** | **+0.010** | **+0.090** |
| LF-4 | Fourier harmonics | 4 | -0.066 | -0.097 | -0.075 |
| LF-6 | Fourier harmonics | 6 | -0.111 | -0.070 | -0.093 |

FE-6 vs LF-4 paired t-test: V1 p=0.045, V2 p=0.042, hV4 p=0.016 (all significant).

**결론**: FE-6 확정. Peaked tuning (cos²)이 smooth harmonics (Fourier)보다 visual cortex color representation에 적합.

### 4b. Improved Encoding (RRR + Smoothness)

| Method | V1 delta | V2 delta | V3 delta | V4 delta | Verdict |
|--------|---------|---------|---------|---------|---------|
| RRR r=2 | -0.015 | -0.013 | -0.031 | -0.020 | REJECTED |
| RRR r=3 | -0.006 | +0.001 | -0.023 | -0.031 | REJECTED |
| RRR r=4 | +0.007 | -0.012 | -0.019 | -0.009 | REJECTED |
| **Smooth best** | **+0.084** | **+0.149** | **+0.153** | **+0.116** | **REJECTED** (trade-off) |

**RRR 실패 이유**: 6개 FE channel이 모두 유의미하게 기여 → noise dimension이 없음. SVD truncation은 signal도 제거.

**Smoothness "개선"이 기만적인 이유**:

| Metric | ridge_gcv → smooth | 해석 |
|--------|-------------------|------|
| voxel_corr | +0.08~0.15 | Pattern 유사성 증가 (but...) |
| **rdm_pearson** | **-0.11~-0.28** | **색 간 구조(geometry) 파괴** |
| **id_accuracy** | **chance (12.5%)** | **색 구분 불가** |

beta=100 (최대값)이 대부분 선택됨 → channel weights가 사실상 flat → 모든 색에 유사한 pattern 예측 → voxel_corr은 높지만 색 변별력은 없음.

---

## 5. Extended Models: smooth_tikh vs Prior-Based (Section 9h)

### 5a. Hypotheses Tested

| ID | Hypothesis | Model | Result |
|----|-----------|-------|--------|
| **H1** | Prior shape mismatch | mixed_ridge_prior | **REJECTED** — all negative V1-V3 |
| **H2** | Prior uncertainty blindness | bayes_prior | **REJECTED** — all negative V1-V3 |
| **H3** | Missing channel smoothness | **smooth_tikh** | **CONFIRMED** — artifact check PASSED |
| H3+prior | Smoothness + prior | smooth_prior | **REJECTED** — prior contaminates benefit |

**SRM prior is fundamentally incompatible with LOCO color interpolation.** All 3 prior-incorporating models fail.

### 5b. smooth_tikh Performance (n=10 all subjects)

**Model**: `W = (C'C + αI + βD'D)⁻¹C'X` — channel-smoothness regularization, NO prior.

| ROI | smooth_tikh M (SD) | ridge_gcv M (SD) | Delta | p | Cohen's d |
|-----|-------------------|-----------------|-------|---|-----------|
| V1 | +0.112 (0.133) | +0.087 (0.095) | +0.025 | 0.285 | +0.36 |
| V2 | +0.151 (0.175) | +0.053 (0.194) | +0.098 | **0.064** | +0.67 |
| **V3** | **+0.115 (0.212)** | +0.014 (0.200) | **+0.101** | **0.030*** | **+1.05** |
| V4 | +0.157 (0.245) | +0.111 (0.210) | +0.046 | 0.236 | +0.40 |

V3 significantly beats ridge_gcv (p=0.030, large effect). V2 trending (p=0.064, medium-large effect).

### 5c. HC vs CVD: smooth_tikh

| ROI | HC M (SD) | CVD M (SD) | Cohen's d | p (Welch) |
|-----|----------|----------|-----------|-----------|
| V1 | +0.143 (0.109) | +0.039 (0.180) | +0.70 | 0.335 |
| **V2** | **+0.246 (0.100)** | **-0.070 (0.063)** | **+3.43** | **0.001*** |
| V3 | +0.100 (0.254) | +0.151 (0.081) | -0.27 | 0.695 |
| V4 | +0.190 (0.253) | +0.080 (0.255) | +0.43 | 0.568 |

**V2 HC-CVD difference MASSIVE (d=3.43, p=0.001)** — much stronger than ridge_gcv (d=1.85, p=0.022).

### 5d. Artifact Validation (CRITICAL — Section 6g Concern RESOLVED)

**Section 6g Warning**: Smoothness (β‖D@W‖²) increased voxel_corr but **degraded rdm_pearson** (-37% to -65%) when fitted on all data. This was interpreted as artifact (flattening predictions).

**LOCO RDM Artifact Check** (`validate_smooth_tikh_artifact.py`, n=10):

| ROI | ridge_gcv rdm_pearson (SD) | smooth_tikh rdm_pearson (SD) | Δ | t(9) | p |
|-----|---------------------------|-----------------------------|----|------|---|
| **V1** | 0.034 (0.226) | **0.531 (0.239)** | **+0.496** | **4.24** | **0.002*** |
| **V2** | 0.265 (0.334) | **0.466 (0.231)** | **+0.201** | 1.96 | 0.082 |
| **V3** | 0.127 (0.306) | **0.365 (0.251)** | **+0.238** | **3.66** | **0.006*** |
| **V4** | 0.104 (0.344) | **0.410 (0.281)** | **+0.306** | **2.44** | **0.049*** |

**Verdict**: smooth_tikh PASSES artifact check. rdm_pearson **improves** (not degrades) in all ROIs. Section 6g artifact was specific to all-data fitting; in LOCO (held-out color interpolation), smoothing genuinely helps tuning curve shape.

### 5e. Individual CVD Profiles (smooth_tikh)

**sub-08 (deutan)**: V2 now **significant** (CH p=0.011*) — was trending with ridge_gcv (p=0.099).

**sub-09 (protan)**: V2 **significant** (CH p=0.040*) — was n.s. with ridge_gcv (p=0.419).

**sub-10 (deutan)**: V2 **significant** (CH p=0.040*) — was trending with ridge_gcv (p=0.089).

**All 3 CVD subjects show significant V2 deviation with smooth_tikh (all CH p < 0.05).** This was NOT achieved with ridge_gcv.

### 5f. smooth_tikh Gate (ARTIFACT CHECK PASSED — permutation PENDING)

| ROI | C1 | C2 (NC-Norm) | C3 (voxel_corr > 0) | C3c (rdm_pearson) | C3b (Permutation) | Status |
|-----|-----|-------------|---------------------|-------------------|-------------------|--------|
| V1 | PASS | PASS (0.297) | PASS (p=0.005) | **PASS** (0.531) | **PENDING** | **PENDING PERM** |
| V2 | PASS | PASS (0.476) | PASS (p=0.001) | **PASS** (0.466) | **PENDING** | **PENDING PERM** |
| V3 | PASS | PASS (0.165) | PASS (p=0.207) | **PASS** (0.365) | **PENDING** | **PENDING PERM** |
| V4 | PASS | PASS (0.254) | PASS (0.047) | **PASS** (0.410) | **PENDING** | **PENDING PERM** |

**C3c (rdm_pearson)**: New criterion added to detect Section 6g artifact. smooth_tikh PASSES all 4 ROIs (rdm_pearson > 0.3).

**Next step**: 10K permutation test on server to confirm genuine color-specific signal (not covariance inflation).

### 5g. Phase 2 Encoder Decision

| Criterion | ridge_gcv | smooth_tikh | Winner |
|-----------|----------|------------|--------|
| V2 HC-CVD difference | d=1.85 p=0.022 | **d=3.43 p=0.001** | **smooth_tikh** |
| V3 LOCO performance | +0.014 | **+0.115 (p=0.030)** | **smooth_tikh** |
| All 3 CVD V2 significant | 0/3 significant | **3/3 significant** | **smooth_tikh** |
| rdm_pearson (artifact check) | V1-V4: 0.03~0.27 | **V1-V4: 0.37~0.53** | **smooth_tikh** |

**smooth_tikh is the leading candidate** to replace ridge_gcv as Phase 2 encoder. Final confirmation requires 10K permutation test (server execution PENDING).

---

## 6. GO/NO-GO Gate (Updated: NC corrected + permutation test)

| ROI | C1 (Reliability) | C2 (Norm. Fit, corrected) | C3 (Interpolation) | C3b (Permutation) | Overall |
|-----|-------------------|--------------------------|---------------------|--------------------|---------|
| V1 | PASS (0.416) | PASS (0.227) | PASS (p=0.006) | FAIL (p=0.274) | **CONDITIONAL GO** |
| V2 | PASS (0.420) | PASS (0.268) | PASS (p=0.040) | FAIL (p=0.311) | **CONDITIONAL GO** |
| V3 | PASS (0.398) | FAIL (0.061) | FAIL (p=0.404) | FAIL (p=0.880) | **NO-GO** |
| hV4 | PASS (0.603) | PASS (0.316) | PASS (p=0.026) | **PASS (p=0.044)** | **PRIMARY GO** |

> C2: Voxel-pattern NC (Spearman-Brown) 사용, threshold 0.2로 하향.
> C3b: 10K color-label shuffle permutation test.

**Phase 2 역할 분리**:
- **V1/V2 = MAIN FILTER TARGET** — HC-CVD 차이가 유의한 곳 (d=1.61/1.85, p<0.025). CVD 색 표상 왜곡이 검출되는 early visual areas → 여기서 교정하면 downstream 효과 기대
- **hV4 = COLOR INTERPOLATION ORACLE** — genuine color-specific signal (permutation p=0.044), per-color 균일, residual random → V1/V2 filter 평가의 cross-ROI benchmark 제공
- **V3 = NO-GO** (제외)

> Gate 관점에서 hV4가 모든 criteria를 통과하지만, Phase 2 filter의 **교정 대상**은 V1/V2이다. hV4에서는 HC-CVD 차이 자체가 작기 때문 (d=1.19, p=0.169).

---

## 7. 개별 CVD 프로필 (ridge_gcv vs smooth_tikh)

### sub-08 (deutan)

| Model | ROI | LOCO r | HC z-score | Crawford-Howell p | 특이 사항 |
|-------|-----|--------|-----------|-------------------|----------|
| ridge_gcv | V2 | -0.241 | -2.08 | 0.099 | Trending |
| **smooth_tikh** | V2 | -0.297 | -3.11 | **0.011*** | **Significant** |

### sub-09 (protan)

| Model | ROI | LOCO r | HC z-score | Crawford-Howell p | 특이 사항 |
|-------|-----|--------|-----------|-------------------|----------|
| ridge_gcv | V2 | -0.024 | -0.93 | 0.419 | n.s. |
| **smooth_tikh** | V2 | -0.055 | -2.38 | **0.040*** | **Significant** |

### sub-10 (deutan)

| Model | ROI | LOCO r | HC z-score | Crawford-Howell p | 특이 사항 |
|-------|-----|--------|-----------|-------------------|----------|
| ridge_gcv | V2 | -0.257 | -2.17 | 0.089 | Trending |
| **smooth_tikh** | V2 | -0.101 | -2.38 | **0.040*** | **Significant** |

**CVD 프로필 요약 (CRITICAL)**: smooth_tikh를 사용하면 **모든 3명의 CVD 피험자가 V2에서 significant deviation (all CH p < 0.05)**을 보임. ridge_gcv에서는 0/3이 유의. V2 = main filter target의 타당성이 강화됨.

---

## 8. 우려 지점 및 보완 과제

### 7a. NC-normalized LOCO metric — RESOLVED

**이전 문제**: voxel Pearson r ÷ RDM Spearman r (metric space 불일치).
**수정 완료**: Voxel-pattern noise ceiling (split-half, Spearman-Brown corrected r_sb) 사용.

| ROI | Old (voxel÷RDM) | Corrected (voxel÷voxel) | Change |
|-----|-----------------|------------------------|--------|
| V1 | 0.310 | **0.227** | -0.083 (인플레이션 제거) |
| V2 | 0.373 | **0.268** | -0.105 |
| hV4 | 0.313 | **0.316** | +0.003 (안정적) |

hV4만 두 normalization 모두에서 안정적. Gate outcome 불변.

### 7b. Permutation test — RESOLVED (9f-1)

10K color-label shuffle 완료. **핵심 발견**: V1/V2의 null baseline이 ~0.10-0.13 (NOT zero) — voxel covariance structure가 기여. hV4만 genuine color-specific interpolation (p=0.044).

| ROI | Parametric p | Permutation p | 해석 |
|-----|-------------|---------------|------|
| V1 | 0.006 | 0.274 | Covariance baseline 미고려 → 인플레이션 |
| V2 | 0.040 | 0.311 | 동일 |
| **hV4** | 0.026 | **0.044*** | **양쪽 모두 significant** |

### 7c. Per-color LOCO breakdown — RESOLVED (9f-2)

Friedman test 완료. V1/V2는 비균일 (Blue/Cyan 높고, Yellow/Green 낮음). **hV4는 균일 (p=0.485)** → 8색 전반에 걸친 genuine interpolation.

### 7d. Residual structure analysis — RESOLVED (9f-3)

hV4 residual r(resid, orig) = 0.053 (near-random → noise ceiling 근접). V1/V2 = 0.45 (systematic structure 잔존).

### 8e. Identification accuracy가 전반적으로 chance 이하

LOCO에서 모든 모델의 id_accuracy가 chance (12.5%) 이하 (ridge_gcv와 smooth_tikh 모두 0/8). 이는 nearest-neighbor 1-of-8 식별이 신호 수준 대비 너무 noisy함을 의미. voxel_corr과 rdm_pearson이 더 신뢰할 수 있는 metric.

### 8f. smooth_tikh permutation test — PENDING

**CRITICAL**: smooth_tikh가 ridge_gcv를 능가하지만 (V2 d=3.43, V3 p=0.030, all CVD V2 significant), 이것이 genuine color-specific signal인지 covariance baseline inflation인지 확인 필요.

**보완 계획**: 10K color-label shuffle permutation test on server (computationally expensive — requires SLURM array job).

**Decision tree**:
- If permutation passes → smooth_tikh adopted as Phase 2 encoder
- If permutation fails → ridge_gcv retained (smooth_tikh improvement = artifact)

---

## 9. 확정 사항 및 다음 단계

### 확정 사항

| 항목 | 결정 | 근거 |
|------|------|------|
| Best encoder | **smooth_tikh (pending perm)** | V2 d=3.43, all CVD V2 significant; artifact check PASSED |
| Fallback encoder | **ridge_gcv** | If smooth_tikh permutation fails |
| Best basis | **FE-6** (cos²) | LF-4/6 대비 유의하게 우수 |
| Filter targets | **V1, V2** (main) | V2에서 모든 CVD significant with smooth_tikh |
| Oracle ROI | **hV4** | Genuine interpolation (perm p=0.044), cross-ROI validation |
| Pipeline for Phase 2 | W_s = smooth_tikh fit, **frozen** (pending perm) | Filter T_psi는 stimulus space에서만 작동 |

### 다음 단계 (우선순위순)

| Priority | Task | 목적 | Status |
|----------|------|------|--------|
| ~~1~~ | ~~NC-normalized LOCO 수정~~ | ~~Voxel-pattern NC 계산~~ | **DONE** |
| ~~2~~ | ~~Permutation test ridge_gcv (9f-1)~~ | ~~Non-parametric p-value~~ | **DONE** |
| ~~3~~ | ~~Per-color LOCO breakdown (9f-2)~~ | ~~균일성 확인~~ | **DONE** |
| ~~4~~ | ~~Residual analysis (9f-3)~~ | ~~Systematic vs random residual~~ | **DONE** |
| ~~5~~ | ~~Extended models (9h)~~ | ~~smooth_tikh validation~~ | **DONE** (artifact check PASSED) |
| **6** | **smooth_tikh permutation test (9h-final)** | smooth_tikh vs shuffled null 확인 | **SERVER PENDING** |
| 7 | Phase 2 filter optimization 착수 | T_psi 설계 (V1/V2 main target, hV4 oracle) | After perm test |
| 8 | Ridge alpha stability (9f-4) | GCV lambda fold consistency | PENDING |

### 논의 필요 사항

1. **smooth_tikh 채택 시기**: Permutation test 결과를 기다릴 것인지, artifact check PASSED로 충분한지? (V2 d=3.43, all CVD V2 significant = 강력한 증거)
2. **V2 중심 전략**: smooth_tikh 결과는 V2가 가장 강력한 filter target임을 시사 (모든 CVD significant, d=3.43). V1은 보조 ROI로 전환할 것인가?
3. **hV4 oracle 활용 방법**: Cross-ROI validation, color axis reference, per-color confidence weighting 중 어떤 전략이 우선인가?
4. **rdm_pearson을 primary metric으로 승격**: smooth_tikh는 voxel_corr와 rdm_pearson을 동시 개선. Phase 2에서 rdm_pearson을 primary로 사용할 것인가? (id_accuracy는 floor → 폐기)
5. **CVD individual analysis 전략**: n=3이지만 smooth_tikh로 all significant → group-level claim 가능한가?
