# Cross-ROI Pipeline Availability Assessment (Revised)

> **Date**: 2026-03-19 (revised from 2026-03-17)
> **Context**: Step 3-5 RDM-matching filter NULL result 이후, 파이프라인 구조적 한계 분석 및 향후 방향 재설정
> **Revision note**: W₀ = (R_new @ A_g)ᵀ 의 식별불가능성(identifiability) 문제 반영. 기존 "cortical locus" 결론 약화, 방법론적 한계로 재해석.

---

## 1. Step 3-5 Null Result 요약

### 실험 결과

| Step | 테스트 | 결과 | 판정 |
|------|--------|------|:---:|
| Step 3 (Pattern) | T_ψ* ≈ identity? | ψ* ≈ 0 (모든 subject, 모든 ROI) | 예상대로 |
| Step 3 (RDM) | Model A 개선? | 6-11% in-sample, **BUT ψ* 3명 동일** | **FAIL** |
| Step 3 (Nested) | Model B > A > 0? | Model B = identity, A = basis artifact | **FAIL** |
| Step 4 (LOCO) | ≥5/8 folds 개선? | **0/8** positive folds (전원) | **FAIL** |
| Step 4 (Perm) | p < 0.05? | **p = 1.0** (전원) | **FAIL** |
| Step 5 (Rescue) | FDR pair ≥50% rescue? | sub-08 V2: 50% (경계), 나머지 0% | **경계/FAIL** |

### 근본 원인: 두 층위

#### 층위 1 — W₀ 구조의 식별불가능성 (structural confound)

W₀ = (R_new @ A_g)ᵀ 에서:
- **A_g** (k × K): HC 7명 평균 인코딩 규칙 — 순수 HC
- **R_new** (V_s × k): CVD subject의 SRM projection — CVD 데이터에서 학습

R_new는 `argmin ‖Y_CVDᵀ − R_new @ S_HC‖²`로 fitting되므로,
CVD의 망막 왜곡(Δθ)과 피질 왜곡(ΔW) **모두를 구분 없이 흡수**한다.

결과:
- `W₀ @ C(θ) ≈ Ȳ_CVD` (패턴 일치 = ZS ≈ LORO 결과)
- 이 "좋은 예측"은 R_new가 Δθ+ΔW를 보상했기 때문 (부분적으로 순환적)
- T_ψ(θ)를 추가하면 **이미 흡수된 Δθ를 이중 계산** → 과교정 또는 무효

**따라서 T_ψ 실패는 "자극 공간 교정 불가능"이 아니라 "이 모델 구조에서는 Δθ를 분리 추정할 수 없음"을 의미한다.**

#### 층위 2 — Basis 지배 (technical limitation, 여전히 유효)

층위 1과 독립적으로, `C(θ)`의 half-wave rectified cosine 구조가 RDM을 지배:
- θ를 수 도 이동해도 C(θ) 변화 미미 → W₀ @ C(T_ψ(θ))의 RDM 거의 불변
- ψ* 3명 동일 = optimizer가 subject-specific 정보를 활용 못함
- In-sample 6-11%도 LOCO에서 0/8 → basis artifact

---

## 2. Cross-ROI Pipeline이 같은 결과를 낼 이유

### 동일한 구조적 한계

| 구성 요소 | Step 3-5 (same-ROI) | Cross-ROI (제안) | 차이? |
|-----------|---------------------|------------------|:---:|
| Transform | T_ψ(θ) Fourier 4 params | T_ψ(θ) Fourier 4 params | 동일 |
| Prediction | W₀_ROI @ C(T_ψ(θ)) | W₀_V2 @ C(T_ψ(θ)) | ROI만 다름 |
| R_new 흡수 문제 | R_new가 Δθ+ΔW 흡수 | R_new_V2가 Δθ+ΔW 흡수 | **동일** |
| Basis 지배 | C(θ) 매끈 → RDM 불변 | C(θ) 매끈 → RDM 불변 | **동일** |

두 가지 한계 모두 ROI 선택과 무관하므로 cross-ROI 전환은 무의미.

---

## 3. Cross-ROI Prevalidation 결과의 독립적 가치

Prevalidation 결과는 **모델 구조와 무관한 기술적 사실**이므로 가치 유지:

| 결과 | 의미 | W₀ 의존? | 논문 위치 |
|------|------|:---:|----------|
| sub-08 V2↔hV4 r=0.878 | 왜곡이 시각 계층에 걸쳐 공유 | **아니오** (실측 RDM 비교) | Discussion |
| LOCO vulnerability → JND 방향 일치 | LOCO가 행동 예측에 유용 | ridge_gcv 의존 | Discussion |
| sub-10 무상관 (r=0.112) | 보상형 CVD 독립 확인 | **아니오** | Results |
| Level 2 FAIL (per-color 축약) | Pair-level ≠ color-level | **아니오** | Methods |

---

## 4. Null Result 재해석

### ~~기존 해석 (철회)~~

> ~~"CVD의 색 간 거리 왜곡은 자극 각도 재매핑으로 교정 불가능 → cortical locus"~~

### 수정된 해석

> "W₀ = (R_new @ A_g)ᵀ 구조에서 R_new가 망막 왜곡(Δθ)과 피질 왜곡(ΔW)을 구분 없이 흡수하므로, T_ψ(θ)를 추가하면 이중 계산이 발생한다. Step 3-5 null result는 **이 파이프라인이 Δθ를 식별할 수 없음**을 보여주며, 자극 공간 교정의 불가능성을 증명하지는 않는다."

### 수렴 증거 재평가

| 증거 | 기존 해석 | 수정 해석 | 강도 |
|------|----------|----------|:---:|
| ① Cone shift (Wilcoxon p<0.05) | 피질이 이미 보상 중 | **R_new가 Δθ 흡수 → 재적용 = 이중 계산.** "피질 보상" 주장은 R_new confound와 분리 불가 | **약화** |
| ② RDM filter (LOCO 0/8, p=1.0) | 자극 교정 불가 → cortical locus | **모델 구조상 Δθ 식별 불가.** T_ψ 실패 ≠ 자극 교정 원천 불가 | **약화** |
| ③ Cross-ROI 공유 (r=0.878) | 체계적 피질 왜곡 | **유효: 모델 무관 기술적 사실.** 실측 RDM 직접 비교 | **유지** |

### 확실히 말할 수 있는 것

1. **HC-CVD RDM gap 존재** — 모델 무관, 실측 데이터 직접 비교
2. **Gap은 V2~hV4에 걸쳐 체계적** — cross-ROI Spearman r=0.878
3. **W₀ + T_ψ 파이프라인은 Δθ와 ΔW를 분리할 수 없음** — 방법론적 한계
4. **Basis 함수 C(θ)가 RDM을 지배하여 T_ψ의 효과 범위 극히 제한적** — 기술적 한계

### 확실히 말할 수 없는 것

1. 왜곡의 원인이 망막(Δθ)인지 피질(ΔW)인지
2. 자극 공간 교정이 원천적으로 불가능한지

---

## 5. 새 파이프라인: 피질 통제 + 망막 왜곡 모델링

### 5-A. 핵심 전환

기존 W₀+T_ψ 파이프라인의 식별불가능성을 해결하는 새 접근:

```
기존 (실패):  W₀ = (R_new @ A_g)ᵀ + T_ψ   → R_new가 Δθ+ΔW 흡수 → T_ψ 이중계산
새 접근:      W_HC (순수 HC, 통제)  + δθ    → 피질 통제, 망막만 자유변수
```

**핵심 가정**:
1. HC-CVD 차이는 cone shift(δθ)에서만 발생, 피질 인코딩(W)은 동일
2. `voxel_CVD = W_HC × C(θ + δθ)` — W는 통제, δθ만 추정

**기존 한계 해결**:
- R_new 불사용 → Δθ 흡수 문제 없음
- δθ가 유일한 자유변수 → 식별 가능
- 가정이 틀리면 모델 적합도 자체가 나빠짐 → 자기검증적(self-validating)

**가정의 경험적 근거**:
- Phase 1에서 HC의 W (ZS group prior)로 CVD voxel 반응을 일정 수준 예측 성공 (ZS ≈ LORO)
- 이는 피질 인코딩이 HC-CVD 간 유사함을 시사

**가정 검증: W 고정 가능 여부 (Red Team #1 대응)**:

검증을 위해 자유 W 피팅과 기존 W_HC 고정 모두 진행:

```
조건 (a) Constrained: W = W_HC (고정) + δθ fitting → δθ_constrained
조건 (b) Free:        W = ridge_gcv(Y_CVD, C(θ+δθ)) + δθ fitting → δθ_free, W_free
```

검증 방법 3가지:

```
검증 1: ΔW norm 비교
  ΔW = W_free − W_HC
  relative_norm = ‖ΔW‖_F / ‖W_HC‖_F
  → 작으면 (< 0.1) 피질 동일 가정 지지
  → 크면 피질 차이 존재 시사

검증 2: Constrained vs Free likelihood 비교
  LL_constrained = −Loss(δθ_constrained, W_HC)
  LL_free = −Loss(δθ_free, W_free)
  LR = 2 × (LL_free − LL_constrained)
  Δdf = n_voxels × K (W의 자유 파라미터 수)
  → χ² test 또는 AICc 비교
  → Free가 유의하게 우수하지 않으면 가정 방어

검증 3: δθ 수렴 + Permutation test
  r(δθ_constrained, δθ_free) → r > 0.9이면 수렴
  Permutation null: HC 7명에 대해 동일 절차 → ΔW 분포
  CVD의 ΔW가 HC 분포 내이면 가정 지지 (Crawford & Howell)
```

- LORO/LOCO 기준에서 자연스럽게 수행 가능 (기준 2,3의 W는 CVD 데이터에서 자유 추정)

### 5-B. 5개 왜곡 모델 비교

| 모델 | df | 설명 | 비고 |
|------|:---:|------|------|
| 1-way Cone Shift | 1 | 유전형 해당 cone만 이동 (Δλ nm) | Baseline, 물리 기반 |
| 3-way Cone Shift | 3 | L,M,S 세 cone의 peak λ 독립 이동 | 보상 표현 가능, 유력 |
| Fourier | 4 | a₁cos+b₁sin+a₂cos2+b₂sin2 | Smooth 가정, 색 간 연속성 제약 |
| Per-color Shift | 8 | T(θᵢ) = θᵢ + δᵢ (색별 독립 shift) | 무가정, Fourier와의 직접 비교 |
| Model-free Fourier | 8 | Fourier df=8 확장 (3차 항 추가) | Smooth 상한선, 과적합 위험 |

**모델 간 관계**:
- Nested: 1-way ⊂ 3-way (2개 cone 0 고정) → F-test 가능
- 동일 df 비교 (df=8): Per-color vs Model-free Fourier → 가정의 영향 직접 비교
  - Per-color: 색 간 독립 (인접색 관계 무시)
  - Fourier df=8: 연속 함수 (인접색 간 매끄러운 변화 강제)
  - **차이가 크면**: 연속성 가정의 적절성에 대한 증거
- Fourier(df=4) vs Per-color(df=8): 자유도 차이 → AICc로 parsimony 비교

**1차/2차 구분 (Red Team #2 대응)**:
- **1차 비교 (후보 모델)**: df ≤ 4 — 1-way, 3-way, Fourier
- **2차 참조 (상한선/대조군)**: df = 8 — Per-color, Model-free Fourier
  - LOCO 기준(8 folds)에서 df=8은 각 fold에 전용 파라미터 → 과적합 위험
  - 3기준 교차검증에서 자기방어: overfit δθ는 다른 기준에서 성능 하락 → 탐지 가능
  - 보고 시: "1차 모델의 성능 상한선"으로 위치

### 5-C. 3가지 피팅 기준 × 4모델 비교 설계

각 기준은 기존 결과와 동일한 분석 차원에서 진행:

#### 기준 1: Voxel-space RDM 매칭 (1차) + SRM RDM (2차)

**1차 타겟: voxel-space RDM (R_new 미사용, Red Team #4 대응)**:
```
For each HC subject i:
  W_i = ridge_gcv(Y_HC_i, C(θ))              # HC_i의 자체 voxel space
  RDM_i(δθ) = corr_dist(C(θ+δθ) @ W_i)      # shifted 예측의 RDM

RDM_HC_model(δθ) = mean_i[RDM_i(δθ)]         # HC 7명 모델 RDM 평균

RDM_CVD_actual = corr_dist(Ȳ_CVD)            # CVD native voxel space (R_new 미사용)

Loss_RDM = Σᵢ<ⱼ (RDM_HC_model(δθ)_ij − RDM_CVD_actual_ij)²
```

**논리**: CVD RDM에 모든 왜곡(Δθ+ΔW)이 포함되어 있어도 무방.
모델 쪽(W_HC)이 피질을 고정하고 δθ만으로 이 RDM을 재현하는 것이 목표.
δθ가 gap을 설명하면 → "망막 shift로 충분", 못 설명하면 → "피질 차이 존재".

**W 평균 문제 회피**: W(행렬)가 아닌 RDM(스칼라 28개)을 평균
**R_new 미사용**: 양쪽 모두 native voxel space에서 RDM 계산.
RDM은 각 subject 내부의 8색 간 correlation distance이므로 cross-space 비교 유효.

**2차 분석: SRM-space RDM**:
```
SRM_RDM_HC(δθ) = SRM 투사 후 동일 절차
SRM_RDM_CVD = corr_dist(R_new_jᵀ @ Y_CVD_jᵀ)
```
- 1차(voxel-space)와의 일치(ρ > 0.85) 확인용
- 기존 SRM 결과와의 연속성 유지

**검증**: 피팅에 사용하지 않은 LOCO vulnerability 프로필 재현 여부

#### 기준 2: ridge_gcv + Procrustes LORO (fitting + validation)

기존 LORO 결과와 동일한 차원에서 비교. Within-subject 접근.

**피팅**:
```
For CVD subject j (6-fold LORO):
  기존: W = ridge_gcv(Y_CVD_train, C(θ))         → r_baseline
  제안: W = ridge_gcv(Y_CVD_train, C(θ + δθ))    → r_shifted

Loss_LORO = −mean_folds[corr(Y_pred, Y_test)]   # 최대화 = 음수 최소화
```

**핵심**: CVD 자체 데이터 + 보정된 design matrix → R_new 불필요
δθ가 맞으면 C(θ+δθ)가 CVD의 "실제 입력"에 가까워 → W가 더 정확 → LORO 개선

**검증**: SRM RDM 일치 여부 + LOCO 실패 패턴

#### 기준 3: ridge_gcv + Procrustes LOCO (fitting + validation)

기존 LOCO 결과와 동일한 차원에서 비교. 보간 능력 직접 테스트.

**피팅**:
```
For CVD subject j (8-fold LOCO):
  기존: W = ridge_gcv(Y_CVD_7colors, C(θ_7))           → predict θ_held
  제안: W = ridge_gcv(Y_CVD_7colors, C(θ_7 + δθ_7))    → predict C(θ_held + δθ_held)

Loss_LOCO = −mean_folds[corr(Y_pred_held, Y_actual_held)]
```

**검증**: SRM RDM 일치 여부 + LORO 개선 여부

### 5-D. 전체 비교 매트릭스

```
                피팅 기준
                ┌──────────┬──────────┬──────────┐
                │ RDM(SRM) │ LORO     │ LOCO     │
   ┌────────────┼──────────┼──────────┼──────────┤
   │ 1-way  (1) │ fit+val  │ fit+val  │ fit+val  │
모 │ 3-way  (3) │ fit+val  │ fit+val  │ fit+val  │
델 │ Fourier(4) │ fit+val  │ fit+val  │ fit+val  │
   │ PerClr (8) │ fit+val  │ fit+val  │ fit+val  │
   │ FreeFr.(8) │ fit+val  │ fit+val  │ fit+val  │
   └────────────┴──────────┴──────────┴──────────┘

5 models × 3 fitting criteria × 3 CVD subjects = 45 fits
각 fit에 대해 나머지 2개 기준으로 cross-validation
```

**모델 선택 기준**:
- 같은 기준 내: AICc / F-test (nested models), LOCO CV (non-nested)
- 기준 간: 3개 기준에서 일관되게 우수한 모델 선택
- 최종: fitting 기준과 무관하게 동일 δθ가 나오면 → 강력한 수렴 증거

### 5-E. Cone → Hue Angle 매핑 (3-way 모델용)

**수학적 정의**:
```
CIELab(L*,a*,b*) → XYZ: 정확한 역공식 (CIE 정의)
XYZ → LMS:             M_stockman × [X,Y,Z]ᵀ (정확한 선형 변환)
```

**Shifted cone 응답 (broadband 자극)**:
```
정확한 방법 (full spectral integration):
  L_shifted = ∫ SPD_color(λ) × cone_L(λ − ΔL) dλ
  M_shifted = ∫ SPD_color(λ) × cone_M(λ − ΔM) dλ
  S_shifted = ∫ SPD_color(λ) × cone_S(λ − ΔS) dλ

근사 방법 (XYZ matrix re-estimation):
  M_new = lstsq(XYZ_cmf, shifted_cone_fundamentals)
  LMS_shifted = M_new × XYZ_color
```

**Opponent → Hue angle**:
```
(L_shifted, M_shifted, S_shifted) → (L−M, S−(L+M)/2) → arctan2(S_opp, LM_opp) → δθ
```

- Stockman & Sharpe (2000) cone fundamentals 기반
- 8색 각각의 CIELab 좌표 → 스펙트럼 → shifted cone 응답 → opponent → hue angle
- **검증 가능성**: 유전자형에서 Δλ 예측값과 fitting된 ΔL, ΔM, ΔS 비교

**Red Team #3 대응 — 근사 오차 검증**:
- CIELab→XYZ→LMS 변환 자체는 수학적으로 정확 (정의에 의해)
- Shifted cone에 대한 matrix 근사 오차 정량화 필요: full spectral integration과 비교
- 모니터 SPD 필요 (psychophysics 세팅에서 측정 가능)
- 기존 결과에서 color_order_preserved = false (sub-08) → 대폭 이동 시 비단조성 주의
- **구현 시 full spectral integration 우선 사용, matrix 방법은 검증용으로 병행**

**Cone→Hue 매핑 표현력 검증 (자극 색 표현 가능 여부 테스트)**:

매핑 함수가 실험 자극 8색을 충실히 표현하는지 사전 검증:

```
검증 1: Δθ vs Δλ 관계 curve
  For Δλ ∈ {0, 1, 2, ..., 40} nm:
    θ_shifted(Δλ) = cone_to_hue(Δλ)    # 8색 각각
    Δθ(Δλ) = θ_shifted − θ_original
  → Δλ-Δθ curve 8색 × 1 plot
  → 단조성, 비선형성, 색별 감도 차이 확인

검증 2: Error distribution (full spectral vs matrix 근사)
  For Δλ ∈ {0, 5, ..., 40} nm:
    Δθ_exact = full_spectral_integration(Δλ)
    Δθ_approx = matrix_method(Δλ)
    error = Δθ_exact − Δθ_approx
  → error distribution histogram + per-color breakdown
  → |error| < Y° 기준 설정 (e.g., < 2° for Δλ ≤ 20nm)

검증 3: Color-order preservation test
  For Δλ ∈ {0, 5, ..., 40} nm:
    θ_shifted = [θ₁+δθ₁, ..., θ₈+δθ₈]
    order_preserved = is_monotonic(θ_shifted)
  → 단조성 깨지는 임계 Δλ 보고
  → Pass 기준: 생물학적으로 타당한 범위(deutan ≤15nm, protan ≤40nm)에서 order 유지
```

### 5-F. 실행 순서

```
Step 1: Cone→Hue 매핑 함수 구현 + 표현력 검증
  ├─ Stockman cone fundamentals, 8색 스펙트럼, opponent 변환
  ├─ Full spectral integration 구현 (1차)
  ├─ Matrix 근사와 비교 → 오차 정량화
  ├─ 검증 1: Δθ vs Δλ 관계 curve (8색 × Δλ 0-40nm)
  ├─ 검증 2: Error distribution (full spectral vs matrix)
  └─ 검증 3: Color-order preservation test (임계 Δλ 보고)

Step 2: RDM 피팅 (기준 1) — 5개 모델 × 3 CVD
  ├─ Voxel-space RDM (1차 타겟, R_new 미사용)
  ├─ HC per-subject RDM(δθ) 계산 → 평균
  ├─ CVD 실측 voxel-space RDM과 비교 → δθ* 추정
  ├─ SRM-space RDM (2차) — voxel-space와의 일치 확인
  └─ AICc / F-test 모델 비교 (1차: df≤4, 2차: df=8 상한선)

Step 3: LORO/LOCO 피팅 (기준 2,3) — 5개 모델 × 3 CVD
  ├─ ridge_gcv + C(θ+δθ) within-subject 구현
  ├─ δθ* 추정
  ├─ 모델 비교
  └─ W 고정 가능 여부 검증 (피질 동일 가정)
     ├─ Constrained (W_HC 고정) vs Free (W 자유 추정) 병행
     ├─ ΔW norm: ‖W_free − W_HC‖_F / ‖W_HC‖_F < 0.1?
     ├─ Likelihood ratio test: Free가 유의하게 우수한가?
     └─ δθ 수렴: r(δθ_const, δθ_free) > 0.9? + permutation null

Step 4: Cross-validation + 종합 성능 평가
  ├─ RDM에서 fit한 δθ → LORO/LOCO 검증
  ├─ LORO에서 fit한 δθ → RDM/LOCO 검증
  ├─ LOCO에서 fit한 δθ → RDM/LORO 검증
  ├─ 3개 기준 수렴 여부 평가
  └─ 종합 성능 매트릭스: 모델(5) × 기준(3) × 검증(2) 보고

Step 5: HC LOCO 실패 재현 (최종 검증)
  ├─ 선택된 δθ를 HC 7명에 적용
  ├─ HC_shifted vulnerability ≈ CVD_actual vulnerability?
  ├─ Permutation null: 1000개 random hue shift → δθ*의 유의성 검증
  ├─ Matched pairs: voxel 수/baseline 성능 유사한 HC-CVD 쌍 비교
  └─ 성립 시: "CVD LOCO 실패 = cone shift 결과" 직접 증명

Step 6: 행동 실험 설계
  └─ δθ⁻¹ 필터 적용 JND + MRI
```

---

## 6. 출처

| 데이터 | 파일 |
|--------|------|
| Step 3 filter results (legacy) | `results/step3_filter/sub-{08,09,10}_filter_results.json` |
| Step 4 LOCO + permutation (legacy) | `results/step4_validation/sub-{08,09,10}_loco_validation.json` |
| Step 5 pairwise diagnostic (legacy) | `results/step5_pairwise/sub-{08,09,10}_pairwise_diagnostic.json` |
| Cross-ROI prevalidation | `loss_prevalidation/results/cross_roi_consistency.json` |
| Cone shift results | `future_phase1_forward_model/results/cone_shift/cone_shift_validation_results.json` |
| Phase 2 plan (legacy) | `PLAN.md` |
| W₀ 구축 코드 (legacy) | `scripts/step1_build_model.py` |
| T_ψ + loss 함수 (legacy) | `scripts/utils_filter.py` |
| SRM fitting | `future_phase1_forward_model/scripts/cone_shift_loco.py` |
| ridge_gcv LOCO/LORO | `future_phase1_forward_model/scripts/` |
