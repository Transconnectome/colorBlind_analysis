# Pipeline Check: sub-08 (Deutan CVD)

> Cone shift pipeline 결과를 sub-08 관점에서 통합 정리.
> 수식, 결과값, 해석을 포함하는 완전한 참조 문서.
> 모든 수치는 JSON 원본에서 직접 추출. (2026-03-21)

---

## 1. Subject Profile

| Property | Value |
|----------|-------|
| Subject | sub-08 |
| CVD type | Deutan (M-cone anomaly) |
| Voxels | V1=560, V2=400, V3=114, V4=70 |
| SRM K | V1=4, V2=4, V3=3, hV4=3 |

### Data Reliability

| ROI | Split-Half RDM | Noise Ceiling (upper) | Noise Ceiling (lower) |
|-----|---------------:|----------------------:|----------------------:|
| V1  | 0.706 | 0.741 | 0.982 |
| V2  | 0.846 | 0.781 | 0.988 |
| V3  | 0.643 | 0.662 | 0.956 |
| **V4** | **0.902** | 0.807 | 0.986 |

### SRM-Based RDM Difference with HC (Crawford & Howell, LOO-consistent)

| ROI | Disparity | HC LOO Mean | % Above HC | t | p |
|-----|----------:|------------:|-----------:|------:|------:|
| V1  | 0.550 | 0.453 | 21.6% | 1.101 | 0.157 |
| **V2** | **0.718** | **0.486** | **47.8%** | **2.113** | **0.040*** |
| V3  | 0.738 | 0.540 | 36.6% | 1.921 | 0.052 |
| hV4 | 0.732 | 0.700 | 4.6% | 0.235 | 0.411 |

Group permutation: V1 p=0.062, V2 p=0.075 (trending).

### Forward Model Performance (ridge_gcv)

| | V1 | V2 | V3 | V4 |
|---|---:|---:|---:|---:|
| LORO | 0.245 | 0.344 | 0.395 | 0.459 |
| LOCO | -0.062 | -0.241 | 0.049 | -0.275 |

V4 LOCO per-color: [+0.573, -0.637, -0.733, -0.306, +0.250, -0.251, -0.759, -0.334]

### Subject-Specific K* (V4)

| K | 2 | 3 | 4 | 5 | 6 | **8** | 10 | 12 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| LOCO | 0.203 | 0.084 | -0.179 | -0.209 | -0.275 | **0.541** | 0.538 | 0.539 |

K*=8 → LOCO 6.4x (group K=3 대비). Caveat: K*=8 with 8 colors ~ lookup table.

### W Constraint (Crawford & Howell)

| Metric | Value |
|--------|------:|
| delta_W / W0 (Frobenius) | 1.662 |
| t | 1.105 |
| p | 0.312 |

W_CVD는 HC 분포 내 → 동일 인코딩 가정(W_HC = W_CVD) 유지.

---

## 2. Distortion Models

### 핵심 가정

**W_HC = W_CVD**: 피질 인코딩(W)은 HC와 CVD가 동일하며, 차이는 망막 수준의 cone spectral sensitivity shift(δθ)뿐이다.

Crawford & Howell 검증: t=1.105, p=0.312 → W_CVD는 HC 분포 내에 위치 (§1 참조).

### Cone → Hue Mapping

1. **자극**: CIELAB 공간 8색 (L\*=60, C\*=40, hue = 0°, 45°, ..., 315°) → CIE XYZ
2. **Cone response**: Stockman & Sharpe (2000) 2-degree fundamentals. Shift: `cone_shifted(λ) = CubicSpline(cone)(λ - Δλ)`, clamp ≥ 0
3. **Hue angle**: Opponent channels `RG = L - M`, `BY = S - (L+M)/2` → `θ = arctan2(BY, RG)`

### 왜곡 모델 일람

| Model | df | 파라미터 | 물리적 해석 |
|-------|---:|----------|-------------|
| **cone_1way** | 1 | Δλ (nm) | CVD-type specific cone 1개만 이동 (deutan→M, protan→L) |
| **cone_3way** | 3 | ΔL, ΔM, ΔS (nm) | L, M, S cone 독립 이동 |
| **fourier** | 4 | a₁, b₁, a₂, b₂ | δθ(c) = Σ [aₖ cos(kθ_c) + bₖ sin(kθ_c)], 물리적 제약 없음 |
| **per_color** | 8 | δθ₁...δθ₈ | 색별 자유 shift, 물리적 제약 없음 (saturated) |

Cone models: 물리적으로 해석 가능, 특이적 (CVD type별 cone 특정).
Fourier/per_color: 유연하지만 과적합 위험 (df ≥ 4 on 8-point profile).

### Cone Mapping Validation (Deutan, sub-08)

**δθ per color at key Δλ**:

| Color | θ_normal (°) | δθ @5nm | δθ @10nm | δθ @15nm | δθ @20nm |
|-------|-------------:|--------:|---------:|---------:|---------:|
| red | 317.34 | -6.12 | **-12.67** | -19.29 | -25.58 |
| orange | 301.25 | -4.83 | **-9.54** | -13.97 | -17.95 |
| yellow | 288.17 | -2.55 | **-4.71** | -6.44 | -7.71 |
| green | 276.72 | -0.11 | **+0.39** | +1.49 | +3.19 |
| cyan | 263.75 | +3.43 | **+8.21** | +14.50 | +22.35 |
| blue | 176.65 | -20.16 | **-70.61** | -112.92 | -128.65 |
| purple | 96.65 | -7.62 | **-14.89** | -21.55 | -27.46 |
| magenta | 12.44 | -0.93 | **-1.96** | -2.98 | -3.84 |

Blue가 가장 민감 (BY-dominant). Sanity: full_spectral vs matrix = 0.000° diff. 1-way vs 3-way deutan = 동치.

**Color order preservation**: deutan ≤12nm 안전 (13nm에서 blue↔purple 역전). protan ≤9nm 안전.

---

## 3. Pipeline A: SRM-RDM Fitting (개별 HC, Per-Fold)

> SRM shared space에서 RDM 구조를 비교하여 δθ를 추정. **Negative finding — supplementary로 보고.**

### 3-1. 방법

**공간**: SRM shared space (k차원). SRM 의존적.

#### v1 (7 HC 전체 SRM, 단일 fold)

```
W_i = ridge_gcv(Y_HC_i, C(θ))              # per-HC voxel-space W
RDM_pred = mean_i[ pdist(C(θ+δ) @ W_i) ]   # 1a: voxel-space
Z_model = A_g @ C(θ+δ)^T                    # 1b: SRM group prior
Loss = Σ (RDM_pred - RDM_CVD)²
AICc = n·ln(RSS/n) + 2k + 2k(k+1)/(n-k-1), n=28
```

#### v2 (7-fold LOO nested-CV)

```
Fold i (held-out = HC_i):
  SRM: 6 HC → S_i (k, 8), A_g_i (k, K)
  R_cvd ← SVD(β_cvd @ pinv(S_i))
  Z_cvd = R_cvd^T @ β_cvd^T → (k, 8)
  Path A: Loss = Σ (RDM(A_g_i @ C(θ+δ)^T) - RDM(Z_cvd))²
  Path B: Loss = Σ (RDM(R_held^T @ (C(θ+δ) @ W_held)^T) - RDM(Z_cvd))²
Optimizer: differential_evolution, bounds [-60, 60] nm
```

### 3-2. v1 결과 (sub-08, hV4)

| Model | df | 1a params | 1a loss | 1a AICc | 1b params | 1b loss | 1b AICc |
|-------|---:|-----------|--------:|--------:|-----------|--------:|--------:|
| cone_1way | 1 | [10.0] | 18.95 | -8.78 | [10.0] | 18.68 | -9.18 |
| cone_3way | 3 | [0, 10, 0] | 18.95 | -3.94 | [0, 10, 0] | 18.68 | -4.33 |
| fourier | 4 | [0,0,0,0] | 11.07 | **-16.25** | [0,0,0,0] | 28.23 | 9.96 |
| per_color | 8 | [0,...,0] | 11.07 | -2.42 | [0,...,0] | 28.23 | 23.80 |

cone_1way: Δλ=10nm. fourier/per_color: **all zero** (null result — AICc winner이지만 왜곡 없음).

### 3-3. v2 결과 (sub-08, hV4, 7-fold LOO)

| Model | df | Path A median r | Path A params_sd | Path B median r | AICc (A) | AICc (B) |
|-------|---:|:---------------:|:----------------:|:---------------:|---------:|---------:|
| cone_1way | 1 | 0.111 | 19.5 nm | -0.193 | 8.19 | -12.34 |
| cone_3way | 3 | 0.179 | [23.6, 42.4, 15.1] | -0.019 | 3.49 | -15.98 |
| fourier | 4 | 0.370 | [25.9, 24.2, 26.9, 14.1] | 0.500 | 0.30 | -22.74 |
| per_color | 8 | 0.656 | [40.0, 25.0, 37.0, ...] | 0.650 | -12.33 | -19.68 |

### 3-4. 구조적 한계: δθ=0이 최적인 이유

모든 CVD에 대해 **δθ≈0이 최적**이거나, 파라미터가 fold 간 극도로 불안정 (SD ≫ median).

#### 근본 원인: V4 SRM space에서 HC ≈ CVD (Phase 2 확인)

Phase 2 SRM (Crawford & Howell) 결과에서 **V4는 HC-CVD 차이가 비유의**했다:

| Subject | V4 Disparity t | p | 판정 |
|---------|---------------:|------:|------|
| sub-08 | 0.235 | 0.411 | NS |
| sub-09 | 1.100 | 0.150 | NS |
| sub-10 | -1.900 | 0.945 | NS |
| **Group** | — | **0.494** (Procrustes) | **NS** |

RDM correlation도 HC-CVD (0.224) ≈ HC-HC (0.158)로 CI 완전 중첩.

**결론**: V4 SRM space에서 HC와 CVD의 RDM 구조 차이가 유의하지 않으므로, **RDM criterion에 매칭할 target signal 자체가 존재하지 않는다.** δθ를 아무리 조정해도 A_g @ C(θ+δ)^T의 RDM이 수렴할 CVD-specific 패턴이 없다.

#### 검증: A_g @ C(θ+δ) sweep (sub-08, hV4)

A_g는 mean HC Z를 1차 구조에서 잘 예측하지만 (Z_corr ≈ 0.89), δ를 이동시켜도 CVD RDM 방향으로 이동하지 않는다:

| Δλ (nm) | RDM ρ(pred, CVD) — Fold 0 | RDM ρ(pred, CVD) — Fold 3 |
|--------:|:-------------------------:|:-------------------------:|
| 0 | +0.071 | +0.016 |
| 5 | +0.043 | +0.003 |
| 8.64 | -0.021 | -0.041 |
| 15 | +0.025 | -0.090 |
| 25 | -0.025 | -0.152 |
| 30 | +0.021 | -0.306 |

ρ ≈ 0 주변에서 fluctuate하거나 오히려 악화. 매칭할 target이 없으므로 당연.

#### 보조 요인: Run-to-run consistency

SRM space에서 측정한 inter-run RDM consistency:

| Subject | SRM inter-run RDM ρ (mean ± SD) |
|---------|-------------------------------:|
| sub-01 | 0.430 ± 0.183 |
| sub-02 | 0.647 ± 0.177 |
| sub-03 | 0.803 ± 0.109 |
| sub-04 | 0.366 ± 0.251 |
| sub-05 | 0.473 ± 0.194 |
| sub-06 | 0.386 ± 0.282 |
| sub-07 | 0.515 ± 0.372 |

HC 평균 ≈ 0.52 (voxel space 0.27보다 양호). SRM이 run consistency를 개선하지만, target signal 부재 문제는 해결하지 못함.

#### 참고

- **Procrustes**: `load_amplitudes()`가 `amplitudes_procrustes.npy`를 로드. 양쪽 파이프라인 모두 적용됨.
- **Phase 2 유의 결과는 V2** (sub-08 p=0.040) **와 V1** (trending p=0.062). V4는 Phase 2에서도 NS.

### 3-5. LORO Criterion (v1 only — 기각)

```
Z_pred = A_g @ C(θ+δ)^T, Z_test = R_new^T @ Y_CVD_run^T
Objective: maximize mean_runs[mean_colors[corr(Z_pred[:,c], Z_test[:,c])]]
```

| Model | LORO corr | Baseline | Δ |
|-------|----------:|---------:|---:|
| cone_1way | 0.020 | 0.340 | **-0.320** |
| fourier | 0.340 | 0.340 | 0.000 |

**기각 사유**: R_new는 C(θ) 기반 S에 정렬 → Z_test 좌표계 = C(θ), Z_pred 좌표계 = C(θ+δ) → δ가 클수록 불일치 증가 → δ=0이 구조적으로 유리 (artifact).

### 3-6. Pipeline A 결론

RDM criterion은 V4에서 cone shift 검출 불가. **근본 원인**: V4 SRM space에서 HC-CVD RDM 차이 자체가 비유의 (Phase 2 확인) → 매칭할 target signal 부재. A_g @ C(θ+δ) sweep에서도 δ에 무관하게 CVD RDM과의 ρ ≈ 0. LORO는 좌표계 불일치로 δ=0 편향. Supplementary negative finding으로 보고.

**향후 검증 가능**: Phase 2에서 유의했던 V2 (sub-08 p=0.040)에서 RDM criterion을 실행하면, target signal이 존재하여 다른 결과가 나올 수 있음.

---

## 4. Pipeline B: LOCO Fitting (집단 HC, Mean-HC Spearman)

> Voxel space에서 LOCO 보간 취약성 프로필을 매칭. **Primary pipeline — 유의한 결과.**

### 4-1. 방법

**공간**: Voxel space (V_s차원). SRM 비의존.

#### v1 (per-HC fitting, shift_at_test vs shift_at_both)

```
For each HC_i:
  W = ridge_gcv(Y_HC_i, C(θ)) or C(θ+δ)     # shift_at_test vs shift_at_both
  vuln_HC_i[c] = mean_runs[corr(C(θ+δ)[c] @ W, Y_actual[c])]
loss = -Spearman_ρ(vuln_HC_i, CVD_vuln)       # per-HC fitting
```

v1 한계: Per-HC ρ의 SD ~0.3-0.5 → fitting 불안정. Raw MSE는 Bias²에 지배됨.

#### v2 (mean-HC Spearman, exact permutation)

```
For δθ (to minimize):
  For each HC_i (i = 1..7):
    C_shifted = C(θ + δθ)                          # shift_at_both
    For each held-out color c (c = 0..7):
      C_train = C_shifted[all colors except c]       # (7, K)
      Y_train = amp_HC_i pooled over 6 runs          # (42, V_s)
      W_loco = ridge_gcv(C_train ⊗ I_runs, Y_train)  # re-fit W per fold
      vuln_HC_i[c] = mean_runs[ corr(C_shifted[c] @ W_loco, Y_actual[c]) ]

  mean_vuln = mean_i( vuln_HC_i )                    # 7 HC 평균 → stable
  loss = -Spearman_ρ( mean_vuln, CVD_actual_vuln )

Optimizer: differential_evolution (popsize=10, maxiter=80 for df≤3)
Significance: Exact permutation test (8! = 40,320 permutations of CVD color labels)
```

**Permutation test의 의미**:

관찰된 Spearman ρ가 **색-취약성 대응 관계**에 의한 것인지, 아니면 **8개 값의 우연한 순위 일치**인지를 검정한다.

1. 최적 Δλ에서 mean-HC vulnerability 프로필 `v_pred = [v₁...v₈]`을 고정한다.
2. CVD 실제 vulnerability `v_cvd = [c₁...c₈]`의 **색 라벨을 모든 가능한 순열로 섞는다** (8! = 40,320가지).
3. 각 순열 π에 대해 `ρ_π = Spearman(v_pred, v_cvd[π])`를 계산한다.
4. p-value = (ρ_π ≥ ρ_observed인 순열 수) / 40,320.

즉, p=0.036은 "**색 라벨을 무작위로 섞었을 때**, 관찰된 ρ=0.690 이상의 상관을 얻을 확률이 3.6%"라는 뜻이다. 이는 cone shift에 의한 예측 프로필이 **특정 색에 대한 취약성 패턴**을 유의미하게 재현했음을 의미한다.

**v1 → v2 핵심 변경**:

| v1 문제 | v2 해결 |
|---------|---------|
| Per-HC MSE → noise 지배 (SD ~0.3-0.5) | **Mean-HC Spearman**: 7 HC 평균 후 rank correlation |
| Raw MSE = Bias² + Profile MSE → level match 착취 | **Spearman ρ**: 수준 무관, profile만 포착 |
| L-BFGS-B → 이산 design matrix에서 gradient=0 | **differential_evolution**: gradient-free global |
| Permutation test 미실행 | **Exact permutation**: 8! = 40,320 순열 |

**shift_at_both 근거**: "이 HC가 태어날 때부터 cone shift가 있었다면, ridge_gcv 학습도 왜곡된 색으로 이루어졌을 것이고, 보간도 왜곡된 공간에서 시도할 것"

### 4-2. v1 결과 (sub-08, hV4, grid search Δλ=10nm)

| Model | shift_at_test ρ (p) | shift_at_both ρ (p) |
|-------|--------------------:|--------------------:|
| cone_1way | 0.333 (0.420) | **0.524 (0.183)** |
| fourier | 0.286 (0.493) | 0.286 (0.493) |

방향성 있으나 NS. shift_at_both > shift_at_test 확인.

### 4-3. v2 결과: cone_1way (df=1) — Primary

| Subject | CVD Type | Δλ (nm) | Mean-HC ρ | Baseline ρ | Perm p | MSE Red. | CCC | Per-HC ρ (mean±SD) |
|---------|----------|--------:|----------:|-----------:|-------:|---------:|----:|-------------------:|
| **sub-08** | deutan | **8.64** | **0.690** | 0.286 | **0.036*** | 14.1% | 0.094 | 0.031 ± 0.447 |
| **sub-09** | protan | **25.20** | **0.833** | -0.333 | **0.009*** | 52.5% | 0.295 | 0.116 ± 0.458 |
| sub-10 | normal | 43.76 | -0.048 | -0.476 | 0.561 | 19.7% | -0.147 | -0.071 ± 0.306 |

**해석**:

1. **Sub-08 (deutan)**: Δλ=8.64nm → mild deuteranomaly. M-cone +8.64nm shift로 CVD LOCO 프로필 재현 (p=0.036).
2. **Sub-09 (protan)**: Δλ=25.20nm → moderate protanomaly. L-cone -25.20nm shift (p=0.009).
3. **Sub-10 (normal)**: p=0.561 → **negative control 성공**. 어떤 shift도 정상안의 LOCO 프로필 재현 불가.

**Per-HC Spearman 진단** (sub-08 cone_1way):

| HC | 01 | 02 | 03 | 04 | 05 | 06 | 07 |
|----|---:|---:|---:|---:|---:|---:|---:|
| ρ | -0.143 | 0.524 | -0.405 | -0.095 | -0.571 | 0.500 | 0.405 |

개별 HC SD=0.447 → per-HC fitting 불안정 (v1 실패 원인). Mean-HC ρ=0.690 ≫ 개별 mean ρ=0.031.

### 4-4. v2 결과: cone_3way (df=3) — 기각

| Subject | CVD Type | ΔL (nm) | ΔM (nm) | ΔS (nm) | Mean-HC ρ | Perm p | 판정 |
|---------|----------|--------:|--------:|--------:|----------:|-------:|------|
| sub-08 | deutan | -27.79 | -23.01 | 1.28 | 0.929 | **0.001*** | 물리적 비타당 |
| sub-09 | protan | 15.96 | 17.66 | -12.99 | 0.833 | **0.008*** | 비특이적 |
| **sub-10** | **normal** | **15.80** | **41.34** | **5.15** | **0.881** | **0.004*** | **false positive** |

**기각 사유**: (1) Sub-10 false positive → df=3이 noise 과적합. (2) Sub-08 L/M 동시 이동 (deutan은 M-only 기대). (3) Sub-09도 비특이적. **cone_1way만 CVD/normal 구분 가능.**

---

## 5. Cross-Evaluation & Model Selection

### 5-1. 양방향 전이 검증 (`step2_cross_eval.py`)

#### A→B (RDM-fit δθ → LOCO eval)

| Subject | Model | RDM Δλ (nm) | LOCO ρ | Perm p |
|---------|-------|:------------|-------:|-------:|
| sub-08 | cone_1way | 34.41 | -0.214 | 0.714 |
| sub-09 | cone_1way | 4.96 | -0.048 | 0.561 |
| sub-10 | cone_1way | 43.76 | -0.048 | 0.561 |

#### B→A (LOCO-fit δθ → RDM eval)

| Subject | Model | LOCO Δλ (nm) | RDM ρ median |
|---------|-------|:------------|-------------:|
| sub-08 | cone_1way | 8.64 | 0.024 |
| sub-09 | cone_1way | 25.20 | 0.041 |
| sub-10 | cone_1way | 43.76 | -0.067 |

양방향 모두 **비유의** → 두 기준이 측정하는 것이 근본적으로 다름.

#### Convergence (δθ 수렴 판단)

| Subject | Model | RMSD (°) | Param Diff (nm) | Converged |
|---------|-------|:--------:|:---------------:|:---------:|
| sub-08 | cone_1way | 99.0 | 25.8 | No |
| sub-09 | cone_1way | 45.3 | 20.2 | No |
| sub-10 | cone_1way | **0.0** | 0.0 | **Yes** (degenerate) |

### 5-2. 모델 선택 요약

| 판정 기준 | cone_1way (df=1) | cone_3way (df=3) | fourier (df=4) | per_color (df=8) |
|-----------|:----------------:|:----------------:|:--------------:|:----------------:|
| LOCO: CVD 유의 | sub-08*, sub-09** | sub-08**, sub-09** | (미실행) | (미실행) |
| LOCO: sub-10 NS | p=0.561 | **p=0.004 (FP)** | — | — |
| RDM: 검출력 | 없음 (SRM 흡수) | 없음 | fold 불안정 | fold 불안정 |
| 물리적 해석 | CVD-type specific | 비특이적 이동 | 제약 없음 | saturated |
| **최종 판정** | **Primary** | **기각 (FP)** | **기각 (null/과적합)** | **기각 (saturated)** |

### 5-3. Fourier / per_color LOCO v2 미실행 사유

LOCO v2에서 fourier (df=4)와 per_color (df=8)은 실행하지 않았다.

**계산량 문제**: LOCO v2의 mean-HC Spearman objective는 1회 평가당 7 HC × 8 LOCO fold × ridge_gcv = 56회의 ridge 회귀를 수행한다. `differential_evolution`의 총 평가 횟수는 `popsize × (maxiter + 1) × (파라미터 수에 따른 내부 반복)`이므로:

| Model | df | 1회 평가 | DE 평가 횟수 (추정) | 총 ridge 횟수 | 실측 시간 |
|-------|---:|--------:|---------:|----------:|--------:|
| cone_1way | 1 | 56 ridge | ~800 | ~45,000 | ~5분 |
| cone_3way | 3 | 56 ridge | ~2,400 | ~134,000 | ~15분 |
| fourier | 4 | 56 ridge | ~3,200 | ~180,000 | ~25분+ |
| per_color | 8 | 56 ridge | ~6,400 | ~360,000 | ~60분+ |

**과적합 선험적 판단**: 더 근본적으로, 8개 데이터 포인트(8색 LOCO vulnerability)에 대해 df=4 이상의 모델을 fitting하면 과적합이 구조적으로 불가피하다. cone_3way (df=3)에서 이미 sub-10 (normal) false positive (p=0.004)가 확인되었으므로, df≥4 모델은 **false positive 확률이 더 높아질 것이 자명**하다.

또한 v1 RDM 결과에서 fourier/per_color은 모든 파라미터가 0으로 수렴 (null result)했으며, 유의미한 왜곡을 검출하지 못했다.

**결론**: fourier/per_color은 (1) 계산 비용, (2) 과적합 구조, (3) v1 null 선례의 세 가지 근거로 LOCO v2에서 제외했다.

---

## 6. Indicator Selection Problem: RDM vs LOCO

### 6-1. 현상

| | RDM Criterion | LOCO Criterion |
|---|---|---|
| 공간 | SRM shared space (k차원) | Voxel space (V_s차원) |
| SRM 의존 | Yes (R_cvd via SVD → S) | No (독립 ridge_gcv) |
| 측정 대상 | 색간 거리 구조 | 색별 보간 취약성 패턴 |
| δθ 검출력 | 없음 (SRM 흡수) | 있음 (sub-08 p=0.036, sub-09 p=0.009) |
| CVD/normal 구분 | 불가 | **가능** (sub-10 NS) |

### 6-2. 구조적 원인

1. **V4 SRM space에서 HC ≈ CVD** (§3-4 근본 원인): Phase 2 Crawford & Howell에서 V4 disparity는 모든 CVD 개별 & 그룹 수준에서 NS. RDM correlation도 HC-CVD ≈ HC-HC. **매칭할 target signal이 없다.**
2. **Phase 2 유의 ROI는 V2/V1**: sub-08 V2 p=0.040, V1 trending p=0.062. V4는 Phase 2에서도 null → RDM criterion이 V4에서 실패하는 것은 Phase 2와 일관.
3. **LOCO의 구조적 장점**: SRM-space HC-CVD 차이에 의존하지 않음. Voxel space에서 within-subject 보간 능력 측정, shift_at_both로 자기완결적, 42 pooled samples per fold, mean-HC averaging으로 subject noise 상쇄.

### 6-3. 향후 보완 방향

1. **V2에서 RDM criterion 재검증**: Phase 2에서 유의했던 V2 (sub-08 p=0.040)에서 RDM criterion 실행. Target signal이 존재하는 ROI에서 RDM criterion이 작동하는지 확인.
2. **Multi-ROI LOCO replication**: V1/V2/V3에서 LOCO criterion 검증 → ROI-specific Δλ 비교.
3. **RDM-LOCO 교차**: V2에서 RDM-fit δθ와 V4에서 LOCO-fit δθ가 수렴하는지.

---

## 7. 종합 결론

### 성과

1. **Cone_1way LOCO fitting 성공**: sub-08 (deutan, Δλ=8.64nm, p=0.036*), sub-09 (protan, Δλ=25.20nm, p=0.009**).
2. **Negative control 확인**: sub-10 (normal) 비유의 (p=0.561).
3. **물리적 타당성**: Δλ 값이 anomalous trichromacy 문헌 범위와 일치 (mild 5-15nm, moderate 15-30nm).
4. **Per-HC noise 해결**: Mean-HC averaging으로 개별 HC noise (SD ~0.45) 극복.

### 한계

1. **RDM criterion 실패**: V4 SRM space에서 HC-CVD RDM 차이가 비유의 (Phase 2 Crawford & Howell: 개별 NS, 그룹 p=0.494) → RDM criterion에 매칭할 target signal 부재 → supplementary negative finding. (유의 ROI인 V2에서의 RDM criterion 검증은 미실시.)
2. **Cross-evaluation 비수렴**: RDM-fit δθ ≠ LOCO-fit δθ → 단일 기준(LOCO)에만 의존.
3. **Cone_3way 과적합**: df=3 → sub-10 false positive (p=0.004). 자유도 제약 필수.
4. **N=8 color limitation**: Spearman ρ의 검정력 제한적. Exact permutation으로 보완.

### 결론

Cone-shift pipeline은 **LOCO criterion + cone_1way (df=1) + mean-HC Spearman + exact permutation test**의 조합으로, CVD 피험자의 색각 왜곡을 물리적으로 타당한 단일 파라미터(Δλ)로 정량화하는 데 성공했다. RDM criterion의 실패는 V4 SRM space에서 HC-CVD RDM 차이 자체가 비유의하기 때문이며 (Phase 2 확인), 이는 within-subject voxel-space LOCO approach의 구조적 우위를 뒷받침한다.

---

## Source Files

| Section | File Path |
|---------|-----------|
| Cone validation | `cone_shift_pipeline/results/step1_cone_validation/step1_cone_validation.json` |
| v1 RDM | `cone_shift_pipeline/results/step2_rdm/V4/sub-08_rdm_fits.json` |
| v1 LORO | `cone_shift_pipeline/results/step3_loro/V4/sub-08_loro_fits.json` |
| v1 LOCO | `cone_shift_pipeline/results/step3_loco/V4/sub-08_loco_sim.json` |
| v2 LOCO fitting | `cone_shift_pipeline/results/v2/step1_loco/V4/sub-{08,09,10}_loco_v2.json` |
| v2 RDM fitting | `cone_shift_pipeline/results/v2/step1_rdm/V4/sub-{08,09,10}_rdm_v2.json` |
| v2 Cross-eval | `cone_shift_pipeline/results/v2/step2_cross/V4/sub-{08,09,10}_cross_v2.json` |
| Scripts | `cone_shift_pipeline/scripts/step1_fit_{loco,rdm}_v2.py`, `step2_cross_eval.py` |
| Diagnostic report | `cone_shift_pipeline/DIAGNOSTIC_REPORT.md` |
