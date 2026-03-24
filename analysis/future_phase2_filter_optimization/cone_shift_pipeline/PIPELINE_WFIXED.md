# Cone-Shift Pipeline: W-Fixed 모델 구조 및 결과

> 2026-03-23. 피드백·수정·재실험용 기준 문서.

---

## 1. 목적

HC에게 인위적 cone shift(δθ)를 적용하여, CVD와 동일한 LOCO 보간 실패 패턴을 재현하는 δθ를 추정한다.

**핵심 가정**: W_CVD = W_HC (피질 인코딩 동일). 차이는 망막 입력 C(θ+δ)뿐.

---

## 2. 파이프라인 구조

파이프라인은 **두 단계**로 분리된다: (A) CVD target 생성, (B) HC simulation + fitting.

### 2-A. CVD Target 생성 (Phase 1 Forward Model 결과 재사용)

**출처**: `future_phase1_forward_model/results/validation/sub-{ID}_loco.json`

이것은 Phase 1에서 이미 계산된 결과이다. 각 CVD 피험자의 **진짜 LOCO** — 7색 학습, 1색 예측:

```
For each left-out color c (0..7):
    C_train = C(θ)[나머지 7색]             # (42, K) = 6runs × 7colors
    X_train = CVD_amplitudes[나머지 7색]    # (42, V_s)
    alpha = gcv_select_alpha(C_train, X_train)
    W_cvd = ridge(C_train, X_train, alpha)  # (K, V_s) — 7색으로만 학습
    Y_pred = C(θ)[c] @ W_cvd               # (1, V_s) — held-out 색 예측
    Y_actual = CVD_amplitudes[c].mean(runs) # (1, V_s) — 실제 반응
    cvd_target[c] = corr(Y_pred, Y_actual)  # voxel pattern correlation
```

**cvd_target의 의미**: 각 색에서의 보간 충실도.
- 양수: 이 색을 나머지 7색에서 보간 가능 → manifold가 이 지점에서 매끄러움
- 음수: 보간 실패 → 이 색이 manifold에서 이웃 대비 불규칙한 위치

**실제 값 (sub-08 deutan)**:
```
V1: [+0.13, -0.18, -0.44, -0.02, +0.46, +0.19, -0.50, -0.13]
V2: [+0.56, -0.58, -0.69, -0.40, -0.21, -0.25, -0.48, +0.12]
V4: [+0.57, -0.64, -0.73, -0.31, +0.25, -0.25, -0.76, -0.33]
```
→ V2/V4에서 orange(-0.58/-0.64), yellow(-0.69/-0.73), purple(-0.48/-0.76) 보간 실패.

### 2-B. HC Simulation: W-Fixed Cone Shift

**핵심**: HC의 W를 원래 C(θ)로 1회 학습 후 고정. δθ sweep 시 C(θ+δ)만 변경.

```
# Step 1: W 사전 계산 (1회)
For each HC subject:
    X_pooled = amp.reshape(-1, V_s)      # (48, V_s) = 6runs × 8colors
    C_pooled = tile(C(θ), (6, 1))         # (48, K)
    alpha = gcv_select_alpha(C_pooled, X_pooled)
    W_HC[subj] = ridge(C_pooled, X_pooled, alpha)  # (K, V_s) — 8색 전체 학습

# Step 2: δθ sweep
For each δθ:
    C_shifted = C(θ + δθ)                 # (8, K)
    For each HC subject:
        For each color c:
            Y_pred = C_shifted[c] @ W_HC[subj]       # (1, V_s)
            Y_actual = amp_HC[subj][:, c].mean(runs)  # (1, V_s)
            hc_vuln[subj][c] = corr(Y_pred, Y_actual)

    mean_hc_vuln = mean(hc_vuln, across 7 HCs)  # (8,)

# Step 3: Fitting
δθ* = argmax_δθ Spearman(mean_hc_vuln(δθ), cvd_target)
    → differential_evolution (gradient-free)

# Step 4: Permutation test
For all 8! = 40,320 permutations of cvd_target:
    null_rho = Spearman(mean_hc_vuln(δθ*), permuted_cvd_target)
p = (count(null_rho ≥ observed_rho) + 1) / (40,320 + 1)
```

---

## 3. HC simulation의 correlation이 측정하는 것

### 3-1. 구조적 비대칭

| | CVD target | HC simulation |
|---|---|---|
| **W 학습** | 7색 (left-out) | **8색 전체** (pooled) |
| **예측 입력** | C(θ)[c] (원래 basis) | C(θ+δ)[c] (shifted basis) |
| **비교 대상** | 자기 자신의 실제 반응 | 자기 자신의 실제 반응 |
| **측정** | "7색으로 이 색을 보간할 수 있나?" | "shifted input이 원래 반응을 재현하나?" |

### 3-2. HC correlation의 의미

δθ=0일 때: `C(θ)[c] @ W_HC = Y_pred ≈ Y_actual` → W가 8색 전체로 학습되었으므로 correlation ≈ 1.0 (in-sample).

δθ>0일 때: `C(θ+δ)[c] @ W_HC ≠ Y_actual` → shifted basis가 원래 반응과 불일치. **cone shift에 의해 가장 많이 왜곡되는 색에서 correlation이 가장 크게 떨어짐.**

즉, HC simulation의 vuln[c]는: "cone shift가 δθ일 때, 색 c의 예측이 얼마나 왜곡되는가?"

### 3-3. CVD target과의 매칭

**Fitting이 묻는 질문**: "HC에게 δθ를 적용했을 때 가장 왜곡되는 색의 순서(profile)가, CVD에서 보간이 가장 실패하는 색의 순서(profile)와 일치하는가?"

**Spearman ρ 사용 이유**: 절대값이 아닌 **순위**만 비교. CVD target과 HC simulation의 scale이 다르므로 (7색 학습 vs 8색 학습), 어떤 색이 더 취약한지의 **상대적 순서**만 매칭.

### 3-4. 비대칭에 대한 논의

CVD target은 진짜 LOCO (7색→1색), HC simulation은 8색-trained W에 shifted input.

이 비대칭의 물리적 근거:
- CVD의 실제 상황: cone shift 때문에 색 다양체가 왜곡되어 이웃에서 보간이 실패
- HC simulation: 정상 인코딩(W)에 왜곡된 입력(C(θ+δ))을 넣으면 어떤 색에서 불일치가 커지는지
- 두 연산이 같은 물리적 현상(cone shift → 색 표상 왜곡)의 **다른 측면**을 포착

**잠재적 문제**: 
- HC simulation에서 W가 8색 전체로 학습되어 있으므로, δθ=0에서 vuln ≈ 1.0 (ceiling). 
- 이는 CVD target (7색 학습, δθ=0에서도 vuln < 1.0)과 scale이 다르다. 
- Spearman이 이를 보정하나, profile shape 자체가 영향받을 수 있다. 
- 현재 파이프라인은, 정상인도 색약처럼 망막 이상 색들을 인지한다면, 이들 간의 원형 구조 소실하는지 확인. 

---

## 4. SRM 관련: 현재 파이프라인에서의 위치

### 4-1. 현 파이프라인에서 SRM이 하는 일

step0_precompute.py에서 SRM LOO precomputation을 수행:
- 6 HC → SRM 학습 → shared response S
- Group prior A_g = mean(R_j^T @ β_j^T)
- Held-out HC / CVD → SVD projection

이 결과는 **step1_fit_rdm_v2.py** (RDM criterion)에서 사용되나, 해당 criterion은 전 ROI 실패로 확정.

### 4-2. W-Fixed LOCO에서 SRM은 사용되지 않음

step1_fit_loco_v2.py는 SRM 데이터를 **전혀 로드하지 않음**. amplitudes_procrustes.npy만 직접 로드하여 voxel space에서 ridge_gcv.

### 4-3. SRM RDM Criterion: Voxel→SRM 접근 (수정 완료)

**문제 (구버전)**: A_g @ C(θ+δ)^T → SRM 공간에서 직접 prediction → voxel 정보 소실. A_g는 HC 평균이므로 개별 voxel-level 차이를 무시.

**수정된 접근 (구현 완료, 2026-03-23)**:
```
For each training HC_i:
  # 1. Voxel space에서 shifted 반응 예측
  Y_shifted = C(θ+δ) @ W_HC_i         # (8, V_s) — voxel space prediction

  # 2. 예측된 voxel 반응을 "새로운 피험자"로 취급, SVD projection
  R_shifted = SVD(Y_shifted @ pinv(S)) # SRM 투영 (CVD와 동일 방식)
  Z_shifted = R_shifted^T @ Y_shifted  # (k, 8) SRM space representation

  # 3. RDM 계산
  RDM_i = pdist(Z_shifted.T, 'correlation')

# 6 HC 평균 RDM vs Z_cvd RDM
loss = Σ(mean_RDM - cvd_RDM)²
```

**핵심 차이**: A_g를 bypass하고, voxel space → SRM space 매핑을 피험자별로 수행. prediction model이 생성한 voxel-level 왜곡이 SRM space까지 전파.

**Path B (보조)**: Voxel-space RDM 직접 비교. SRM 투영 없이 `C(θ+δ) @ W_HC → RDM` vs CVD voxel RDM.

### 4-4. 수정된 RDM 결과 (cone_1way)

| ROI | Subject | CVD | Path | Δλ median (nm) | SD | Spearman r | r range |
|-----|---------|-----|------|-----------------|-------|------------|---------|
| V1 | sub-08 | deutan | A(vox→srm) | 0.05 | 17.50 | **0.345** | -0.08~0.53 |
| V1 | sub-08 | deutan | B(voxel) | 0.08 | 0.21 | -0.091 | -0.21~0.05 |
| V1 | sub-09 | protan | A(vox→srm) | 2.72 | 25.27 | 0.171 | -0.25~0.39 |
| V1 | sub-09 | protan | B(voxel) | 0.01 | 0.00 | 0.230 | 0.14~0.31 |
| V2 | sub-08 | deutan | A(vox→srm) | 2.71 | 22.49 | -0.036 | -0.22~0.22 |
| V2 | sub-08 | deutan | B(voxel) | 0.49 | 21.09 | -0.201 | -0.26~-0.06 |
| V2 | sub-09 | protan | A(vox→srm) | 5.24 | 27.05 | -0.092 | -0.19~0.14 |
| V2 | sub-09 | protan | B(voxel) | 0.01 | 0.03 | -0.045 | -0.06~0.01 |
| V4 | sub-08 | deutan | A(vox→srm) | 55.39 | 26.84 | -0.116 | -0.19~0.08 |
| V4 | sub-08 | deutan | B(voxel) | 0.06 | 21.09 | -0.193 | -0.27~-0.06 |
| V4 | sub-09 | protan | A(vox→srm) | 5.44 | 17.22 | 0.008 | -0.18~0.12 |
| V4 | sub-09 | protan | B(voxel) | 0.06 | 0.02 | -0.101 | -0.12~-0.01 |
| — | sub-10 | normal | all | 43.76 | ~0 | ≈0 or neg | — |

**해석**:
1. **V1 sub-08 Path A (r=0.345)** 가 유일하게 양의 경향. 그러나 SD=17.50 → fold 불안정.
2. **전반적으로 RDM criterion은 실패** — Spearman r이 대부분 음수 또는 0 근처.
3. **원인**: SVD projection이 RDM 차이를 부분적으로 흡수. voxel→SRM 경로에서도 완전 보존 불가.
4. **LOCO criterion과 대비**: W-fixed LOCO에서 sub-08 V1 r=0.690, V2 r=0.643 → 10배 이상 강한 signal.
5. **결론**: cone_1way RDM criterion은 cone shift fitting에 부적합. LOCO가 유일한 유효 criterion.

### 4-5. 수정된 RDM 결과 (cone_3way, fourier)

fourier (df=4) Path A가 RDM에서 가장 강한 signal을 보임:

**fourier Path A (voxel→SRM)**:

| ROI | sub-08 (deutan) | sub-09 (protan) | sub-10 (normal) |
|-----|:-:|:-:|:-:|
| V1 | **r=0.804** | r=0.228 | r=0.205 |
| V2 | **r=0.556** | r=0.295 | r=0.318 |
| V4 | **r=0.604** | r=0.475 | r=0.532 |

**cone_3way Path A (voxel→SRM)**:

| ROI | sub-08 (deutan) | sub-09 (protan) | sub-10 (normal) |
|-----|:-:|:-:|:-:|
| V1 | **r=0.543** | r=0.124 | r=0.063 |
| V2 | r=0.052 | r=0.106 | r=0.024 |
| V4 | r=0.141 | r=0.305 | r=0.344 |

**해석**:
1. **V1 fourier Path A sub-08 (r=0.804)**: 전체 파이프라인에서 가장 높은 RDM 상관. 그러나 parameter SD 높고 (각 차원 7~13), V4 sub-10도 r=0.532 → specificity 의문.
2. **cone_3way V1**: sub-08 r=0.543 (양), sub-10 r=0.063 (null) → V1 한정으로 specificity 유지.
3. **공통 문제**: 모든 multimodel RDM에서 parameter SD >> parameter estimate → fold 불안정 지속.
4. **LOCO 결과와 비교**: RDM fourier의 r=0.804는 LOCO cone_1way의 r=0.690보다 높으나, RDM에는 permutation test 미적용 → 직접 비교 불가. 또한 LOCO에서 fourier는 sub-10 false positive (§5-5).

### 4-6. ΔRDM 접근: Basis-Response Mismatch 없는 RDM 비교 (2026-03-23)

#### 4-6-1. 동기

LOCO criterion은 CVD target (7색 학습 → 1색 보간)과 HC simulation (8색 전체 학습 W + shifted input)이 구조적으로 비대칭이다. 이 **basis-response mismatch**를 완전히 제거하면서 cone shift signal을 포착하는 대안이 필요.

기존 SRM-based RDM (§4-3~4-5)은 SRM alignment이 cone shift signal을 흡수하여 실패. ΔRDM은 **voxel-space에서 직접** 작동하므로 SRM을 완전히 bypass.

#### 4-6-2. 방법

**Simulation side** (HC에 cone shift 적용):
```
ΔRDM_sim(δ) = RDM( C(θ+δ) @ W_HC ) - RDM( C(θ) @ W_HC )
```
→ W는 1회 학습 후 고정. δθ에 따른 RDM 변화량만 추출.
→ baseline RDM (원형 색구조)이 상쇄되어 **순수 cone-shift distortion만 남음**.

**Observation side** (실제 CVD-HC 차이):
```
ΔRDM_obs = RDM_CVD - RDM_HC_mean
```
→ 관측된 HC-CVD 차이. HC 평균 RDM을 빼면 공유 색구조 제거.

**Fitting question**: ΔRDM_sim(δ*) ≈ ΔRDM_obs 가 되는 δ*는?

#### 4-6-3. 이중 거리 × 삼중 메트릭

**Distance metrics (RDM 구성)**:
1. **Correlation distance** (1 - Pearson r): scale-free, 표준적
2. **Crossnobis** (cross-validated Mahalanobis): 노이즈 정규화, run-level residual 기반 noise covariance

**Comparison metrics (ΔRDM_sim vs ΔRDM_obs 비교)**:
1. **Pearson r / cosine similarity**: 크기 민감 (1차)
2. **Spearman ρ**: 순위만 비교 (2차)
3. **Signed agreement rate**: n_pairs 중 부호 일치 비율 (보수적)

**Sanity checks**:
1. ΔRDM_obs가 구조를 가지는지 (mean, std, range, top pairs)
2. 혼동선 이론 예측: confusion pairs (red-green, orange-cyan, blue-magenta)에서 ΔRDM < 0 (closer)?
3. δθ sweep (0-60nm, step 5): metric이 δθ에 따라 단조적으로 변하는지?

#### 4-6-4. V1 결과 (correlation distance)

| Subject | CVD | Best δθ (Pearson) | Pearson r | p | Best δθ (Spearman) | Spearman ρ | p | Confusion closer |
|---------|-----|-------------------|-----------|-------|---------------------|------------|-------|------------------|
| **sub-09** | **protan** | **30nm** | **0.513** | **0.005*** | **25nm** | **0.524** | **0.004*** | **3/3** |
| sub-08 | deutan | 60nm | -0.127 | 0.520 | 0nm | -0.018 | 0.927 | 1/3 |
| sub-10 | normal | 0nm | 0.029 | 0.884 | 0nm | 0.078 | 0.694 | N/A |

**해석**:
1. **sub-09 protan: LOCO에서 포착 못한 signal을 ΔRDM이 포착**
   - Pearson r=0.513 (p=0.005) at δθ=30nm → strong signal
   - Confusion pair 3/3 closer (red-green: -0.286, orange-cyan: -0.240, blue-magenta: -0.022) → **protan 이론과 완벽 일치**
   - Best δθ=25-35nm 범위 → V4 shift_at_both 결과 (Δλ=25.20nm)와 수렴
   - δθ=15nm 부터 Pearson p<0.05 유지 → broad plateau (robust)
2. **sub-08 deutan: ΔRDM V1에서 비유의 (모든 metric 음수)**
   - Confusion pairs 1/3만 closer → cone-shift 방향 예측 실패
   - LOCO에서는 V1 유의 (p=0.033) → **LOCO와 ΔRDM은 상보적**
3. **sub-10 정상: 완벽한 null**
   - δθ sweep 완전 flat (모든 δθ에서 동일 r=0.029, p=0.884)
   - Norm도 불변 → cone_1way가 sub-10에 적용 불가 (정상이므로)

#### 4-6-5. V1 결과 (crossnobis distance)

| Subject | CVD | Best δθ (Pearson) | Pearson r | p | Best δθ (Spearman) | Spearman ρ | p |
|---------|-----|-------------------|-----------|-------|---------------------|------------|-------|
| **sub-09** | **protan** | **10nm** | **0.496** | **0.007*** | **10nm** | **0.471** | **0.011*** |
| sub-08 | deutan | 60nm | -0.063 | 0.749 | 60nm | 0.130 | 0.511 |
| sub-10 | normal | 0nm | 0.346 | 0.071 | 0nm | 0.356 | 0.063 |

**특이사항**:
- sub-09: crossnobis도 유의하나, **baseline offset** 존재 (δθ=0에서 이미 r=0.459, p=0.014). δθ 증가에 따른 추가 개선이 미미 → crossnobis baseline이 이미 protan distortion pattern을 반영.
- sub-10: crossnobis에서 trending baseline (r=0.346, p=0.071), 그러나 δθ-invariant (모든 δθ에서 동일값). → **δθ-specific signal은 없으나 specificity 우려**.
- **결론**: correlation distance가 ΔRDM에 더 적합. crossnobis baseline offset가 해석을 복잡하게 함.

#### 4-6-6. V2 결과 (correlation distance)

| Subject | CVD | Best δθ (Pearson) | Pearson r | p | Best δθ (Spearman) | Spearman ρ | p | Confusion closer |
|---------|-----|-------------------|-----------|-------|---------------------|------------|-------|------------------|
| sub-09 | protan | 25nm | 0.287 | 0.139 | 45nm | 0.284 | 0.144 | 1/3 |
| sub-08 | deutan | 0nm | -0.062 | 0.755 | 0nm | -0.099 | 0.616 | 2/3 |
| sub-10 | normal | 0nm | 0.334 | 0.082 | 0nm | 0.338 | 0.078 | N/A |

**해석**:
1. **sub-09**: V1 대비 절반 수준 (V1 r=0.513 vs V2 r=0.287). NS이지만 방향 일치 (양의 상관, δθ=25nm).
2. **sub-08**: V1과 동일 패턴 — ΔRDM 비유의. LOCO에서는 V2 유의 (p=0.047).
3. **sub-10**: 완전 δθ-invariant (모든 δθ에서 r=0.334, p=0.082). Trending baseline이나 cone shift signal 아님.

#### 4-6-7. V4 결과 (correlation distance)

| Subject | CVD | Best δθ (Pearson) | Pearson r | p | Best δθ (Spearman) | Spearman ρ | p | Confusion closer |
|---------|-----|-------------------|-----------|-------|---------------------|------------|-------|------------------|
| sub-09 | protan | 60nm | 0.092 | 0.643 | 0nm | 0.044 | 0.825 | 1/3 |
| sub-08 | deutan | 60nm | 0.133 | 0.499 | 55nm | 0.151 | 0.443 | 2/3 |
| **sub-10** | **normal** | **0nm** | **0.420** | **0.026*** | **0nm** | **0.375** | **0.049*** | **N/A** |

**Specificity 실패**: sub-10 (정상)이 유의 (p=0.026). 완전 δθ-invariant임에도 ΔRDM_obs ↔ ΔRDM_sim(δ=0) 상관이 우연히 높음. V4에서 W의 alpha=0.1~1.0 (저정규화) → 예측 RDM이 noise에 영향받아 우연 상관 발생.

**V4 ΔRDM 사용 불가**: specificity 실패로 V4에서 ΔRDM criterion은 기각.

#### 4-6-8. 전체 Cross-ROI ΔRDM Summary (correlation distance)

| ROI | sub-08 (deutan) | sub-09 (protan) | sub-10 (정상) | Specificity |
|-----|:---:|:---:|:---:|:---:|
| **V1** | r=-0.127, p=0.520 | **r=0.513, p=0.005*** | r=0.029, p=0.884 | **OK** (perfect null) |
| **V2** | r=-0.062, p=0.755 | r=0.287, p=0.139 | r=0.334, p=0.082 | marginal (trending) |
| **V4** | r=0.133, p=0.499 | r=0.092, p=0.643 | **r=0.420, p=0.026*** | **FAIL** (false positive) |

#### 4-6-9. LOCO ↔ ΔRDM 상보성 (전 ROI)

**V1**:
| Criterion | sub-08 deutan | sub-09 protan | sub-10 normal |
|-----------|:---:|:---:|:---:|
| LOCO | **p=0.033*** | p=0.112 | p=0.167 |
| ΔRDM | p=0.520 | **p=0.005*** | p=0.884 |

**V2**:
| Criterion | sub-08 deutan | sub-09 protan | sub-10 normal |
|-----------|:---:|:---:|:---:|
| LOCO | **p=0.047*** | p=0.576 | p=0.562 |
| ΔRDM | p=0.755 | p=0.139 | p=0.082 |

**V4** (LOCO shift_at_both / ΔRDM specificity 실패):
| Criterion | sub-08 deutan | sub-09 protan | sub-10 normal |
|-----------|:---:|:---:|:---:|
| LOCO (legacy) | **p=0.036*** | **p=0.009*** | p=0.561 |
| ΔRDM | p=0.499 | p=0.643 | p=0.026* (FP) |

**핵심 결론**:
1. **LOCO와 ΔRDM은 완전히 상보적**: LOCO는 sub-08 deutan을 포착 (V1, V2), ΔRDM은 sub-09 protan을 포착 (V1 only).
2. **ΔRDM은 V1에서만 유효**: V2 NS, V4 specificity 실패.
3. **sub-08 deutan**: LOCO만이 유일한 유효 criterion (V1 p=0.033, V2 p=0.047).
4. **sub-09 protan**: ΔRDM V1 (p=0.005)과 LOCO V4-legacy (p=0.009)만 유의.
5. **가설**: deutan은 interpolation vulnerability (LOCO), protan은 pairwise geometry distortion (ΔRDM)이 주 표현형. 이는 M-cone vs L-cone shift의 색공간 내 영향 방향 차이와 관련될 수 있음.

#### 4-6-10. 스크립트

`scripts/diagnostic_delta_rdm.py`
```bash
conda activate srm
python scripts/diagnostic_delta_rdm.py --rois V1 V2 V4 --distances correlation
python scripts/diagnostic_delta_rdm.py --rois V1 --distances crossnobis  # V1만 (느림)
```

---

## 5. 현재 결과 (W-Fixed LOCO Only)

### 5-1. 전체 결과

| ROI | Subject | CVD | Δλ (nm) | Spearman r | Perm p | K | alpha |
|-----|---------|-----|---------|------------|--------|---|-------|
| **V1** | **sub-08** | deutan | **34.92** | **0.690** | **0.033*** | 4 | 10.0 |
| V1 | sub-09 | protan | 0.94 | 0.500 | 0.112 | 4 | 10.0 |
| V1 | sub-10 | normal | 23.06 | 0.405 | 0.167 | 4 | 10.0 |
| **V2** | **sub-08** | deutan | **3.87** | **0.643** | **0.047*** | 4 | 10.0 |
| V2 | sub-09 | protan | 23.76 | -0.071 | 0.576 | 4 | 10.0 |
| V2 | sub-10 | normal | 23.06 | -0.048 | 0.562 | 4 | 10.0 |
| V4 | sub-08 | deutan | 28.60 | 0.405 | 0.166 | 3 | 1.0 |
| V4 | sub-09 | protan | 48.88 | 0.190 | 0.334 | 3 | 1.0 |
| V4 | sub-10 | normal | 23.06 | -0.238 | 0.729 | 3 | 1.0 |

### 5-2. 요약

- **유의**: sub-08 (deutan) V1 (p=0.033), V2 (p=0.047)
- **비유의**: sub-09 (protan) 전 ROI, sub-10 (normal) 전 ROI, sub-08 V4
- **정상 제어**: sub-10 전 ROI NS → 올바른 null

### 5-3. Per-HC Consistency (sub-08)

| ROI | HC mean r | HC range | Positive / Total |
|-----|-----------|----------|------------------|
| V1 | 0.163 | -0.36 ~ +0.76 | 4/7 |
| V2 | **0.367** | -0.07 ~ +0.64 | **6/7** |
| V4 | 0.127 | -0.36 ~ +0.62 | 4/7 |

V2가 가장 안정적 — HC 간 일관성 높음.

### 5-4. Δλ ROI 간 불일치

sub-08: V1=34.92nm, V2=3.87nm, V4=28.60nm → **서로 불일치**.

Cone shift는 망막 현상이므로 이론적으로 ROI-independent이어야 하나, 현재 결과는 이를 지지하지 않음.

### 5-5. Multi-Parameter 모델 결과 (cone_3way, fourier) — 과적합 진단

sub-09 protan 포착을 위해 df>1 모델 (cone_3way df=3, fourier df=4)을 테스트.

**W-Fixed LOCO 결과 (cone_3way, df=3)**:

| ROI | Subject | CVD | Spearman r | Perm p | Per-HC mean r |
|-----|---------|-----|------------|--------|---------------|
| V1 | sub-08 | deutan | 0.976 | 0.0004*** | 0.575 |
| V1 | sub-09 | protan | **1.000** | **0.0001***| **0.741** |
| V1 | **sub-10** | **normal** | **0.905** | **0.0029** | 0.418 |
| V2 | sub-08 | deutan | 0.905 | 0.0011** | 0.684 |
| V2 | sub-09 | protan | 0.548 | 0.0836 | 0.282 |
| V2 | sub-10 | normal | 0.452 | 0.1314 | 0.170 |
| V4 | sub-08 | deutan | 1.000 | 0.0001*** | 0.677 |
| V4 | sub-09 | protan | 0.310 | 0.2300 | 0.044 |
| V4 | **sub-10** | **normal** | **0.976** | **0.0002** | 0.435 |

**W-Fixed LOCO 결과 (fourier, df=4)**:

| ROI | Subject | CVD | Spearman r | Perm p | Per-HC mean r |
|-----|---------|-----|------------|--------|---------------|
| V1 | sub-08 | deutan | 0.929 | 0.0010** | 0.463 |
| V1 | sub-09 | protan | 0.929 | 0.0010** | 0.592 |
| V1 | **sub-10** | **normal** | **0.976** | **0.0002** | 0.721 |
| V2 | sub-08 | deutan | 1.000 | 0.0001*** | 0.313 |
| V2 | sub-09 | protan | 0.810 | 0.0114* | 0.429 |
| V2 | **sub-10** | **normal** | **0.786** | **0.0152** | 0.483 |
| V4 | sub-08 | deutan | 1.000 | 0.0001*** | 0.507 |
| V4 | sub-09 | protan | 1.000 | 0.0001*** | 0.629 |
| V4 | **sub-10** | **normal** | **0.976** | **0.0003** | 0.350 |

#### 과적합 진단: sub-10 (정상 대조군) False Positive

**핵심 문제**: cone_3way와 fourier 모두 sub-10 (정상)에서 유의 결과를 산출.

- cone_3way: V1 p=0.0029, V4 p=0.0002 → **FALSE POSITIVE**
- fourier: V1 p=0.0002, V2 p=0.0152, V4 p=0.0003 → **전 ROI FALSE POSITIVE**

**원인**: 8-point profile (8색) matching에서 df=3~4 자유도면 어떤 noise pattern이든 높은 Spearman ρ 달성 가능. Permutation test는 "관측 ρ > 무작위 순열 ρ" 여부만 검정하므로, 최적화가 충분한 자유도로 높은 ρ를 확보하면 귀무가설이 기각됨.

**결론**:
1. **cone_1way (df=1)만 유효** — 유일하게 sub-10에서 correct null을 유지
2. cone_3way/fourier는 sub-09도 포착하지만 **specificity 상실**
3. sub-09 protan 포착 실패는 모델 복잡도 부족이 아니라 **cone_1way의 물리적 한계** (M-cone shift만 모델링, L-cone shift 미포함)
4. protan 포착을 위해서는 df 증가가 아닌 **모델 구조 자체의 변경** 필요 (예: L-cone 특이적 1-parameter shift)

---

## 6. 미해결 구조적 문제

### 6-1. CVD target vs HC simulation의 비대칭 (§3-4)

CVD: 7색 LOCO. HC: 8색 전체 학습 + shifted input.
→ 동일한 연산이 아님. Profile matching (Spearman)으로 보정하고 있으나, shape 자체가 달라질 가능성.

**가능한 수정**: HC simulation도 진짜 LOCO로 변경 (7색 학습, 1색 예측, W 매번 재학습) — 단, 이는 legacy (shift_at_both)와 동일해짐.

### 6-2. SRM RDM criterion (§4-3, §4-4) — 구현 완료, 실패 확인

A_g bypass → voxel prediction → SVD projection → RDM 비교. **구현 완료 (2026-03-23)**.
결과: 전 ROI에서 Spearman r ≈ 0 → RDM criterion은 cone shift fitting에 부적합.
SVD projection이 cone shift에 의한 voxel-level RDM 차이를 부분적으로 흡수하는 것이 근본 원인.

### 6-3. sub-09 (protan) 포착: LOCO 불가, ΔRDM V1 가능 (§4-6, §5-5)

**LOCO**: W-fixed cone_1way에서 protan signal 없음. cone_3way/fourier는 포착하나 sub-10 false positive.

**ΔRDM**: V1 correlation distance에서 sub-09 protan **유의** (r=0.513, p=0.005). Confusion pair 3/3 일치. Best δθ=25-35nm → V4 LOCO-legacy (25.20nm)과 수렴.

**현재 status**:
- sub-08 deutan → **LOCO** (V1 p=0.033, V2 p=0.047)
- sub-09 protan → **ΔRDM V1** (p=0.005) + LOCO V4-legacy (p=0.009)
- sub-10 normal → 두 criterion 모두 correct null (V1 LOCO p=0.167, V1 ΔRDM p=0.884)

**미해결**:
1. ΔRDM이 V1에서만 작동하는 이유 (V2/V4 NS)
2. LOCO와 ΔRDM의 CVD-type 특이성의 물리적 근거
3. ΔRDM V4 sub-10 false positive (p=0.026) — alpha가 낮아 noise 영향?

### 6-4. Δλ의 물리적 해석

V1=34.92nm vs V2=3.87nm — 어느 것이 "진짜" cone shift인가? 둘 다 유의하나 값이 10배 차이.

---

## 7. 파이프라인 파일

| 파일 | 역할 |
|------|------|
| `step0_precompute.py` | SRM LOO precomputation (현재 RDM용, 향후 수정 대상) |
| `step1_fit_loco_v2.py` | **Primary**: W-fixed LOCO cone shift fitting |
| `step1_fit_rdm_v2.py` | RDM criterion (실패, 향후 §4-3 방식으로 수정 가능) |
| `step2_cross_eval.py` | Within-ROI cross-evaluation |
| `step2b_cross_roi_eval.py` | Between-ROI cross-evaluation |
| `step3_summary_v2.py` | V4 summary figures |
| `step3_cross_roi_summary.py` | Cross-ROI summary |
| `diagnostic_srm_baseline.py` | SRM A_g prediction quality 진단 |
| `diagnostic_delta_rdm.py` | ΔRDM sanity check (§4-6), dual distance × triple metric |
