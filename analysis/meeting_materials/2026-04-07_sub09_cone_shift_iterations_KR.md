# Sub-09 Protan Cone-Shift Pipeline — 모델 반복 시도 및 최종 제안

> **프로젝트**: Color Vision Deficiency Neural Representation Analysis
> **날짜**: 2026-04-07
> **대상**: Future Phase 2 — Cone-shift filter optimization (Gen-4/Gen-4.5)
> **피험자**: sub-09 (protan CVD), 비교 대상 sub-08 (deutan), sub-10 (normal trichromat)
> **ROI**: V1, V2, hV4
> **목표**: 개인 맞춤형 color filter 설계를 위한 stimulus-space warp parameter 도출

---

## 1. 배경 및 목표

### 1a. 핵심 문제

Sub-09 (protan CVD)의 신경 색 표상은 **혼합 패턴**을 보임:
- **Magenta-관련 색 쌍 확장** (ΔRDM > 0): magenta가 다른 색들로부터 더 멀어짐
- **Confusion 축 압축** (ΔRDM < 0): red-green, orange-cyan 쌍이 가까워짐

기존 1-DOF Machado cone-shift 모델로는 이 혼합 패턴을 설명할 수 없음:
- Machado는 **모든** L-M 관련 거리를 압축하는 방향으로만 작동
- Magenta 확장을 예측하지 못함

### 1b. Double Dissociation

| Subject | LOCO (per-color accuracy) | ΔRDM (pairwise geometry) |
|---------|---------------------------|--------------------------|
| **sub-08** (deutan) | ✓ p=0.033 (V1) | ✗ cosine=−0.34 (anti-correlation) |
| **sub-09** (protan) | ✗ p=0.112 (V1) | ✓ Spearman ρ=0.524, p=0.004 |

이 이중 해리(double dissociation)는 LOCO와 ΔRDM이 **상보적 기준**임을 시사:
- LOCO: 기능적 예측 능력 (per-color interpolation)
- ΔRDM: 기하학적 구조 (pairwise distance metric)

### 1c. 목표

Sub-09를 위한 2-DOF stimulus-space warp 모델 설계:
1. **Physiologically motivated**: retinal cone shift + cortical compensation
2. **Invertible**: 역변환 = 개인 맞춤형 color filter
3. **Low-DOF**: 2-3 parameters (overfitting 방지, n=1 subject)
4. **Mixed pattern compatible**: 동시에 expansion + compression 생성 가능

---

## 2. 모델 반복 시도 이력

### Iteration 0: Machado 1-DOF (Baseline)

**모델**: Δλ 하나로 L-cone spectral shift만 조정

```
L_shifted(λ) = α · L(λ − Δλ) + (1 − α) · k_L · M(λ)
```

**예측**:
- L-M 축 전반적 압축 (protan confusion line)
- Magenta는 약간 보존됨 (~+0.54 vulnerability)

**실제 sub-09 결과**:
- V1 best fit: Δλ=25-30 nm, Spearman ρ=0.524, p=0.004
- **하지만**: magenta pairs는 EXPANDED (+0.665 cyan-magenta)
- **방향 불일치**: magenta 예측 preserved, 관찰 anti-preserved (−0.24)

**실패 원인**:
- 1-DOF로는 혼합 패턴 불가능
- Cortical compensation 효과를 포착하지 못함

**비유**: 지진으로 모든 건물이 같은 방향으로 기울 것이라 예측했는데, 실제로는 어떤 건물은 왼쪽, 어떤 건물은 오른쪽으로 기울었음.

---

### Iteration 1: Machado + BY (Blue-Yellow) Gain

**모델**: Machado cone shift + Stockman opponent 공간에서 B-Y 축 gain

```
θ' = machado_shift(θ, Δλ)
by' = by_retinal × (1 + β)
rg' = rg_retinal
```

**동기**:
- Tregillus et al. 2020: V2/V3에서 L-M 축 cortical compensation 관찰
- S-cone은 intact하므로 S-(L+M) gain으로 magenta 확장 가능?

**실패 원인 1: 축 불일치**

Stockman opponent 공간에서 magenta(c8) 좌표:
- **rg = cos(16.4°) ≈ 0.960** (R-G 축 우세)
- **by = sin(16.4°) ≈ 0.282** (B-Y 축 미미)

Magenta는 **L-M (R-G) 색**이지 S-(L+M) (B-Y) 색이 아님!

BY gain을 적용하면:
- Cyan (by=−0.90): 크게 이동
- Magenta (by=0.28): 거의 이동 안 함
- **결과**: cyan-magenta 거리 **감소** (관찰과 반대)

**실패 원인 2: CIELab b* ≠ Stockman S-(L+M)**

- CIELab b* (perceptual blue-yellow): 큐브루트 비선형 포함
- Stockman S-(L+M) (cone-opponent): 선형 조합

이 둘은 **다른 축**임 (Bujack et al. 2022, Brainard 2022 확인)

**비유**: GPS 좌표계에서 magenta를 움직이려 했는데, 위도를 건드렸더니 경도 우세 도시라 거의 안 움직였음.

---

### Iteration 2: Machado + RG (Red-Green) Overcompensation

**모델**: Machado + R-G 축 overcompensation (γ < −1)

```
rg' = rg_retinal + γ · (rg_retinal − rg_baseline),  where γ < −1
```

**동기**:
- Boehm et al. 2014: protan compensation gain ~3.5×
- γ = −1.5 → overcompensation, baseline을 넘어서 증폭

**예상 효과**:
- Magenta (high rg=0.96): deficit 발생 → overcompensation → rg' > 0.96 → 확장 ✓
- Red, Green (moderate rg): 양쪽 모두 zero에서 멀어짐 → 간격 확장

**실제 문제**:
- Red (rg=0.50) vs Green (rg=−0.06):
  - Machado: 둘 다 zero로 압축
  - Overcompensation: 둘 다 **원래 위치보다 멀어짐** → red-green 간격 **확장**
  - 하지만 관찰: red-green **압축** (ΔRDM = −0.286)

**실패 원인**: Uniform R-G overcompensation은 **모든** L-M 거리를 확장. 혼합 패턴 불가.

**비유**: 모든 스피커 볼륨을 동시에 2배로 올렸더니, 조용한 소리와 큰 소리의 **차이도** 2배가 됨 — 원하는 건 큰 소리만 더 키우기였는데.

---

### Iteration 3: Machado-Dilation (MD) — **최종 제안**

**모델**: Protan confusion axis endpoint 중심의 local hue dilation

```
θ'(c) = machado_shift(θ(c), Δλ) + β · cos(θ_base(c) − θ₀)
```

**Parameters**:
- **Δλ** ∈ [0, 20] nm: Machado cone shift (L-M compression 담당)
- **β** ∈ [0, 30°]: Dilation amplitude (magenta expansion 담당)
- **θ₀** ≈ 16° (고정): Protan confusion axis endpoint in Stockman space (L-M maximum, fitting 안 함)

**작동 원리**:

cos(θ − θ₀) 함수 값:
```
Color         θ_base    cos(θ−θ₀)    이동 방향
────────────────────────────────────────────────────
Magenta (c8)  16.4°     +1.00        +β  (최대)
Red     (c1)  299.9°    +0.24        +0.24β
Cyan    (c5)  243.9°    −0.67        −0.67β (반대!)
Blue    (c6)  142.6°    −0.60        −0.60β (반대!)
Green   (c4)  266.5°    −0.33        −0.33β
```

**Distance 변화**:
1. **Cyan-magenta**: magenta +β, cyan −0.67β → 간격 **+1.67β 확장** ✓
2. **Orange-magenta**: orange +0.04β, magenta +β → 간격 **+0.96β 확장** ✓
3. **Red-green**: Machado 압축이 우세 (−10°~−20°), dilation이 작은 확장 추가 (+0.57β), **순 압축** ✓

**생리학적 해석**:
- **θ₀**: Protan confusion axis endpoint (L-M deficit가 가장 큰 지점)
  - Tregillus 2020: "compensation peaks on L-M cardinal axis"
  - Webster & Mollon 1997: adaptation normalizes variance along deficit axis
- **β > 0**: Cortical overcompensation이 **공간적으로 조정됨** — deficit peak에서 가장 강함
  - Boehm 2014: protan gain ~3.5× (β magnitude prior 제공)
  - Emery et al. 2021: compensation은 hue-angle dependent (localized warp 정당화)

**Filter (역함수)**:
```
θ_filter(c) ≈ θ_display(c) − β · cos(θ_display(c) − θ₀)
θ_original = machado_inverse(θ_filter, Δλ)
```

1차 근사 (small β에서 유효).

**비유**: 지진 진원지 근처 건물일수록 많이 기울고, 멀수록 덜 기울음. 하지만 반대편 건물은 **반대 방향**으로 기울어서, 진원지 건물과 반대편 건물 사이 **간격은 증가**.

---

## 3. 문헌적 근거

### 3a. Stimulus-Space Warp Framework

**새로운 접근**: "R_HC(f(x)) ≈ R_CVD(x)를 만족하는 f를 fitting" — 문헌에 없음
- Machado 2009: Forward simulation, inverse fitting 아님
- **우리 기여**: Machado를 역추정하여 neural RDM에서 shift 복원

**관련 선례**:
- Chapman et al. 2023: Attention이 representational geometry를 왜곡 (개념적 선례)
- Diedrichsen & Kriegeskorte 2017: Encoding model 비교를 위한 RSA framework (수학적 정당화)

### 3b. RDM Prediction from Design Matrix

**수학적 기반** (Diedrichsen & Kriegeskorte 2017):
- Encoding model: Y = C @ W + noise
- Predicted RDM: RDM_pred = f(C @ G @ C^T), where G is feature covariance
- 우리 접근: C를 C(Δλ, β)로 왜곡, RDM_pred와 RDM_obs 비교

**방법론적 개선** (문헌 기반):
- Walther et al. 2016: Cross-validated Mahalanobis distance 사용 (가장 reliable)
- Diedrichsen et al. 2020: WUC (whitened unbiased cosine) for RDM comparison (non-independence 보정)
- 현재: Correlation distance의 Spearman correlation → suboptimal이지만 단순함

### 3c. Opponent Process Compensation

**핵심 발견**:
- **Tregillus et al. 2020** (Current Biology, 35 citations):
  - V1은 L-M response REDUCED (예상된 deficit)
  - V2v/V3v는 L-M response NORMAL (완전 보상)
  - **함의**: V1은 raw cone-shift signal 유지, hV4는 보상됨 (우리 V1 LOCO 성공, hV4 실패와 일치)

- **Boehm et al. 2014** (JoV, 44 citations):
  - Protan sensitivity: 19% of normal
  - Perceptual difference: 67% of normal
  - **Gain: ~3.5×** (β magnitude prior 제공)

- **Emery et al. 2021** (Vision Research, 20 citations):
  - Compensation은 **부분적**이며 **hue-angle dependent**
  - Hue-scaling function shape이 개인마다 다름
  - **함의**: Uniform gain 실패, spatially-tuned warp 필요

### 3d. CIELab vs Stockman Space Mismatch

**중요한 이슈** (Bujack et al. 2022, Brainard 2022):
- CIELab b*는 cube-root nonlinearity 포함
- Stockman S-(L+M)은 linear cone combination
- **둘은 동일하지 않음**
- CIELab 좌표에서 cone shift 적용 → incorrect predicted ΔRDM

---

## 4. 평가 계획

### 4a. Fitting 기준

**Primary**: ΔRDM cosine (V1, signal이 가장 강함)

```python
Grid search: Δλ ∈ [0, 20] nm (step=0.5), β ∈ [0, 30°] (step=1°)
각 (Δλ, β)에 대해:
    C_warped = get_design_matrix_md(Δλ, β, θ₀=16.4)
    Ŷ = C_warped @ W_HC
    ΔRDM_sim = RDM(Ŷ) − RDM(C_baseline @ W_HC)
    score = cosine(ΔRDM_sim, ΔRDM_obs)
```

**성공 기준**:
- ΔRDM cosine > 0.40 (Machado-only ~0.21, 상당한 개선)
- Signed agreement > 65% (18/28 pairs 방향 일치)

### 4b. Validation

| Criterion | Method | Success threshold |
|-----------|--------|-------------------|
| **Cross-criterion** | LOCO Spearman ρ on V1 | r > 0.50, p < 0.10 |
| **Held-out ROI** | hV4 LOCO transfer | Null보다 나음 |
| **Family specificity** | Protan fit > Deutan fit | ΔBIC > 6 |
| **Null specificity** | sub-10 (normal): β ≈ 0 | |95% CI| excludes 0 → FP |
| **BIC comparison** | MD vs Machado-only vs null | ΔBIC > 6 (strong evidence) |

### 4c. Robustness Checks

**Cross-ROI 일관성**:
- V1과 V2가 유사한 (Δλ, β)를 선호해야 함
- θ₀는 ROI 간 고정 (생리학적으로 결정됨)

**Permutation test**:
- 8! label permutation on ΔRDM cosine → p-value

**Bootstrap CI**:
- 1,000 iterations, HC subjects resampling → β 95% CI

---

## 5. 대안 전략 (MD 실패 시)

### 우선순위 1: Sub-09를 Negative Result로 수용

**조치**: Sub-08 (validated LOCO p=0.033)만 Phase 2 filter에 사용; sub-09는 "representation-level compensation model 필요"로 분류

**정당화**:
- Robinson et al. 2022: Compensation이 compressive nonlinearity 포함 가능
- Linear stimulus-space warp가 근본적으로 부적절
- n=1 subject, exploratory extension일 뿐

### 우선순위 2: Feature-Reweighted RSA

**모델** (Kaniuth & Hebart 2021):
- Parametric warp 대신 FE basis의 per-feature weights fitting
- 더 많은 DOF (K parameters)지만 data-driven

**Trade-off**: 더 높은 fitting power, filter 역변환 어려움

### 우선순위 3: PCM (Pattern Component Modeling)

**모델** (Diedrichsen & Yokoi 2017):
- Bayesian model comparison, W에 대해 적분
- 가정이 맞으면 RSA보다 강력

**Trade-off**: 더 많은 데이터 필요, 해석 어려움

---

## 6. 우려 지점 및 보완

### 6a. θ₀ = 16°가 A Priori인가 Data-Driven인가?

**우려**: θ₀가 magenta의 실제 위치와 일치 → circular reasoning?

**보완**:
- θ₀는 **CVD family**(protan vs deutan)에 의해 생리학적으로 결정됨
- Protan: L-cone affected → θ₀ at L-M maximum (≈ 16° in Stockman)
- Deutan: M-cone affected → θ₀ at different location
- **Sub-09 data에 fitting 안 함** — cone type에 의해서만 결정

**추가 validation**:
- Deutan sub-08은 다른 θ₀가 필요해야 함 → family specificity

### 6b. Linear Warp가 불충분할 수 있음

**우려**: Robinson et al. 2022가 compressive nonlinearity 시사

**보완**:
- MD는 1차(linear) 근사
- MD가 cosine > 0.40 달성 → linear가 이 데이터에 충분
- MD 실패 → nonlinearity 인정, future work로 제안

### 6c. n=1 Overfitting 위험

**우려**: 28 pairs에 2 DOF, 하지만 실제로는 8 colors → effective DOF ≈ 7

**보완**:
- Cross-validation: V1에서 fit, V2에서 validate (독립 ROI)
- BIC가 extra DOF에 penalty
- Permutation test가 null distribution 제공
- Sub-10 (normal)과 비교: β ≈ 0이어야 함

---

## 7. 다음 단계

### 7a. 구현

**생성할 스크립트**:
1. `get_design_matrix_md(delta_lambda, beta, theta_0)`: MD warp function
2. `fit_md_model_grid_search.py`: Grid search (Δλ, β), best params 출력
3. `validate_md_cross_roi.py`: V1 fit → V2 validation
4. `validate_md_family_specificity.py`: Protan vs deutan θ₀

**출력**: `results/md_model_sub09/best_params.json`, `figures/md_fit_visualization.png`

### 7b. 일정

- Day 1: MD warp + grid search 구현
- Day 2: Sub-09 V1 fitting, V2 validation
- Day 3: Family specificity (sub-08 deutan), null check (sub-10)
- Day 4: 성공 시 filter specification 생성

---

## 8. 요약 테이블

| Model | DOF | Sub-09 ΔRDM fit | Mixed pattern? | Filter invertible? | 결론 |
|-------|-----|-----------------|----------------|-------------------|------|
| **Machado** | 1 | ρ=0.524, p=0.004 | ✗ (compression only) | ✓ | FAIL (방향 불일치) |
| **BY gain** | 2 | — | ✗ (axis mismatch) | ✓ | FAIL (magenta 거의 안 움직임) |
| **RG overcompensation** | 2 | — | ✗ (uniform expansion) | ✓ | FAIL (red-green 확장) |
| **MD (Machado-Dilation)** | 2 | **TBD** | ✓ (해석적으로 호환) | ✓ | **PROMISING** |

**핵심 통찰**: MD만이 요구되는 혼합 패턴 (magenta expansion + confusion compression)을 생성하면서 동시에 생리학적 해석과 filter 역변환 가능성을 유지함.

---

## 참고 문헌

### 핵심 문헌

1. **Tregillus et al. 2020** — "Color compensation in anomalous trichromats assessed with fMRI"
   - *Current Biology*, 35 citations
   - V1 deficit, V2v/V3v full compensation 직접 측정

2. **Diedrichsen & Kriegeskorte 2017** — "Representational models: A common framework"
   - *PLoS Computational Biology*, 304 citations
   - RSA framework for encoding model comparison

3. **Boehm et al. 2014** — "Compensation for red-green contrast loss"
   - *Journal of Vision*, 44 citations
   - Protan gain ~3.5× 정량화

4. **Emery et al. 2021** — "Color perception and compensation assessed with hue scaling"
   - *Vision Research*, 20 citations
   - Hue-angle dependent compensation, 개인차 큼

5. **Bujack et al. 2022** — "The non-Riemannian nature of perceptual color space"
   - *PNAS*, 33 citations
   - CIELab는 큰 색차에서 부정확

6. **Robinson et al. 2022** — "Nonlinear cortical encoding predicts enhanced McCollough effects"
   - *Vision Research*, 4 citations
   - Compressive nonlinearity in compensation

### 방법론적 개선 제안

7. **Walther et al. 2016** — "Reliability of dissimilarity measures for MVPA"
   - *NeuroImage*, 506 citations
   - Cross-validated Mahalanobis distance 권장

8. **Diedrichsen et al. 2020** — "Comparing representational geometries using WUC"
   - *Neurons, Behavior, Data Analysis, and Theory*, 42 citations
   - RDM 비교에 WUC 사용 권장

9. **Kaniuth & Hebart 2021** — "Feature-reweighted RSA"
   - *NeuroImage*, 41 citations
   - Feature reweighting으로 model-brain correspondence 개선
