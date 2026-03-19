# availability.md 결론의 근거: 테스트별 상세 해설

> **목적**: availability.md §1 테이블의 6개 테스트 + §4의 수렴 증거 3개를 수식과 코드 출처와 함께 해설

---

## 핵심 수학적 객체 정의

| 기호 | 정의 | 차원 |
|------|------|------|
| θ | 색상 각도 (0°~315°, 45° 간격 8색) | scalar |
| T_ψ(θ) | θ + a₁cos(θ) + b₁sin(θ) + a₂cos(2θ) + b₂sin(2θ) (Fourier 4-param 변환) | scalar |
| C(θ) | 6개 half-wave rectified cosine basis: [max(0, cos(θ-0°)), ..., max(0, cos(θ-300°))]ᵀ | ℝ⁶ |
| W₀ | HC group prior 인코딩 가중치 = (R_new @ A_g)ᵀ | n_voxels × 6 |
| d^ψ_ij | corr_dist(W₀ @ C(T_ψ(θᵢ)), W₀ @ C(T_ψ(θⱼ))) — 변환 후 예측 RDM 거리 | scalar ∈ [0,2] |
| μ_HC_ij | HC 평균 pairwise correlation distance (28 pairs) | scalar |

---

## Test 1: Step 3 — Pattern Level (T_ψ* ≈ identity?)

### 보고자 하는 바
Per-color 패턴 수준에서 T_ψ가 필요한지 확인. "CVD 개별 색 반응이 이미 HC와 일치하는가?"

### 수식
```
L_pattern(ψ) = Σᵢ₌₁⁸ ‖W₀ @ C(T_ψ(θᵢ)) − Ȳ_CVD(θᵢ)‖²
```
- Ȳ_CVD(θᵢ) = CVD 피험자의 run-averaged amplitude (6 runs 평균)
- 최적화 결과 ψ* ≈ 0 (max shift < 5°)이면 PASS

### 결과 해석
ψ* ≈ 0 → **개별 색 패턴은 이미 잘 맞음** → 문제는 패턴 수준이 아니라 **색 간 거리 구조(RDM)** 수준

### 코드
`future_phase2_filter_optimization/scripts/step3_filter_estimation.py` — `fit_model_A()` 함수 (Level 1 확인)
- 패턴 수준 loss: `utils_filter.py:loss_pattern()` (L198-227)
- 최적화: `step3_filter_estimation.py:fit_model_A()` (L107-111) — L-BFGS-B, maxiter=500
- 판정 기준: `near_identity = bool(max_shift_pattern < 5.0)` (L171)

---

## Test 2: Step 3 — RDM Level (Model A 개선?)

### 보고자 하는 바
RDM 수준에서 Fourier 변환 T_ψ가 CVD의 색 간 거리를 HC 방향으로 교정하는가?

### 수식 (3개 nested model)

**Model 0 (1 param)**: Physics-based cone shift
```
T₀(θ) = θ_equiv(θ, Δλ)    — cone shift 모델에서 유도된 등가 각도
```

**Model A (4 params)**: Fourier 변환 + 단조성 제약
```
L_RDM(ψ) = Σᵢ<ⱼ (d^ψ_ij − μ_HC_ij)² + λ·P_mono(T_ψ)

P_mono = Σ_{k} max(0, −dT_ψ/dθ|_{θ_k})²    (3600 sample points)
λ = 1000
```

**Model B (8 params)**: Per-color free shift
```
T_B(θᵢ) = θᵢ + δᵢ    (색별 독립 shift, 단조성 무제약)
```

### Nested model 비교 (F-test + AICc)
```
F = [(RSS_restricted − RSS_full) / Δdf] / [RSS_full / df_residual]
AICc = n·ln(RSS/n) + 2p + 2p(p+1)/(n−p−1)    (n=28 pairs)
```

### 결과
- Model A: in-sample 6-11% RSS 감소
- **BUT**: 3명 CVD 전부 **동일한 ψ*** = [-11.745, 1.485, -4.083, -12.526]
- → Optimizer가 subject-specific W₀ 차이를 활용 못함 = **basis artifact** → **FAIL**

### 코드
`step3_filter_estimation.py` — `fit_model_A()` (L102-173), `fit_model_B()` (L176-222)
- RDM loss: `utils_filter.py:loss_rdm()` (L230-260) — 28-pair weighted squared error
- 단조성 penalty: `utils_filter.py:monotonicity_penalty()` (L144-167) — 3600 points, scale=1000
- 변환 함수: `utils_filter.py:T_psi()` (L37-53) — Fourier 4-param
- Multi-start: x0=zeros(4) + 5 random starts, seed=42 (L124-128)
- Nested 비교: `utils_filter.py:nested_model_comparison()` (L293-371) — F-test + AICc

---

## Test 3: Step 3 — Nested (Model B > A > 0?)

### 보고자 하는 바
모델 복잡도를 높이면(4→8 params) 추가 개선이 있는가?

### 수식
```
H₀: RSS_A = RSS_B (추가 4 params 불필요)
F = [(RSS_A − RSS_B) / 4] / [RSS_B / (28 − 8)]
```

### 결과
- Model B가 Model A와 동일 해로 수렴 = identity
- A가 B보다 나은 것이 아니라 **둘 다 basis geometry에 의해 제한됨** → **FAIL**

### 코드
`step3_filter_estimation.py` — `nested_model_comparison()` 호출 (L290-300)
- F-test: `utils_filter.py:nested_model_comparison()` (L333-361)
  - `f_stat = ((rss_r - rss_f) / df_diff) / (rss_f / df_resid)` (L347)
  - `p_value = 1 - f_dist.cdf(f_stat, df_diff, df_resid)` (L348)
- AICc: `n_obs * np.log(rss / n_obs) + 2*k + 2*k*(k+1)/(n_obs-k-1)` (L326-327)
- Preferred model: min(AICc) (L366-367)

---

## Test 4: Step 4 — LOCO Validation (≥5/8 folds 개선?)

### 보고자 하는 바
Step 3의 in-sample 개선이 **held-out color에 일반화**되는가? (과적합 vs 진짜 신호)

### 수식 (8-fold CV)
```
For fold f (held-out color c_f):
  Train pairs: C(7,2) = 21 pairs
  Test pairs: 7 pairs (c_f와 연관된 모든 pair)

  L_train(ψ) = Σ_{(i,j)∈train} w_ij · (d^ψ_ij − μ_HC_ij)² + λ·P_mono

  Improvement_f = 100 · (1 − Σ_test(d^ψ*_ij − μ_HC_ij)² / Σ_test(d^baseline_ij − μ_HC_ij)²)
```
- **Pass 기준**: ≥5/8 folds에서 Improvement > 0

### 결과
- **0/8** positive folds (모든 subject, 모든 ROI)
- in-sample 6-11%조차 일반화 실패 → basis artifact 확인 → **FAIL**

### 코드
`step4_validation.py` — `loco_fold()` (L77-162), `run_loco_validation()` (L165-184)
- Train/test split: `get_pair_indices_for_color()` (L57-74) — held_out color의 7 pairs 분리
- Train mask: `train_weights[train_pairs] = 1.0` (L96-97)
- Multi-start: x0=zeros(4) + 3 random, seed=42+held_out_color (L109-113)
- 판정: `robust = bool(n_positive >= 5)` (L179)

---

## Test 5: Step 4 — Permutation (p < 0.05?)

### 보고자 하는 바
관측된 RDM 개선이 우연 수준을 넘는가?

### 수식
```
For k ∈ {1..1000}:
  π_k = random_shuffle(subject_labels)  — HC/CVD 재배정
  Refit SRM, W₀, A_g on shuffled "HC"
  Fit T_ψ^k, compute Δ^k = (baseline_loss − filtered_loss)

p = #{Δ^k ≥ Δ_observed} / 1000
```

### 결과
- **p = 1.0** (전원) — 관측값이 null distribution 내 최저 수준
- Random label shuffle로도 동일 수준 → 진짜 신호 없음 → **FAIL**

### 코드
`step4_validation.py` — `run_permutation_test()` (L191-344)
- 전체 loop: 1000 shuffles (L249-324), seed=42 (L247)
- 각 permutation 내:
  1. Random partition 7 HC + 3 CVD (L254-256)
  2. SRM refit on permuted HC (L261-266)
  3. A_g rebuild (L275-281)
  4. W₀_perm for permuted CVD target (L284-288)
  5. Filter refit + improvement 계산 (L310-323)
- p-value: `np.mean(null_improvements >= observed_improvement)` (L330)

---

## Test 6: Step 5 — FDR Pair Rescue (≥50%?)

### 보고자 하는 바
SRM pre-validation에서 FDR 유의한 color pair를 filter가 교정하는가? (수렴 타당도)

### 수식
```
FDR pairs: Phase 1 SRM z-test에서 |z| > FDR threshold인 (i,j) 추출

For each FDR pair (i,j):
  e_base_ij = |d^baseline_ij − μ_HC_ij|     — 교정 전 오차
  e_filt_ij = |d^filtered_ij − μ_HC_ij|     — 교정 후 오차
  rescued = (e_filt < e_base)                — 개선 여부

Rescue fraction = Σ rescued / n_FDR_pairs
```
- **Pass 기준**: rescue fraction > 0.50

### 결과
- sub-08 V2: 6/12 = 50% (경계선, 50% > 50% 아님 → 기준 미달)
- 나머지: 0% → **경계/FAIL**
- 일부 pair는 87% error reduction이지만 다른 pair 악화로 상쇄

### 코드
`step5_pairwise_diagnostic.py` — `diagnose_pairs()` (L113-202), `load_fdr_pairs()` (L52-90)
- FDR pair 추출: `significant_fdr_within_roi` flag 확인 (L81)
- Rescue 판정: `rescued = filtered_error < baseline_error` (L164)
- 판정 기준: `rescue_above_50pct = bool(rescue_fraction > 0.5)` (L200) — strict greater-than

---

## 수렴 증거 1: Cone Shift 기각 (availability.md §4)

### 보고자 하는 바
망막 cone shift를 그대로 피질 예측에 적용하면 개선되는가? (원인 소재 검증)

### 수식
```
Y_pred_baseline = W_HC @ C(θ_original)     — 원래 각도로 예측
Y_pred_corrected = W_HC @ C(θ_equiv)       — cone shift 등가 각도로 예측

per_color_imp[i] = corr(Y_corrected[i], Y_CVD[i]) − corr(Y_baseline[i], Y_CVD[i])

Wilcoxon signed-rank test on per_color_imp (n=8)
H₀: median improvement = 0
```

### 결과
| Subject | Baseline r | Corrected r | Δ | Wilcoxon p |
|---------|:---:|:---:|:---:|:---:|
| sub-08 | 0.390 | 0.069 | **-0.321** | **0.023** |
| sub-09 | 0.495 | -0.080 | **-0.575** | **0.031** |
| sub-10 | 0.441 | 0.185 | **-0.257** | **0.023** |

- 3/3 유의하게 **악화** → cone shift를 재적용하면 예측이 깨짐
- **해석**: 피질이 이미 cone shift를 보상 중 → 이중 적용 = 과교정

### 코드
`future_phase1_forward_model/scripts/cone_shift_loco.py`
- W_HC 구축: `build_W_HC_for_cvd()` (L92-98) — `W_HC = (R_new @ A_g).T`
- 예측 평가: `evaluate_prediction()` (L105-161) — per-color voxel correlation
- Wilcoxon test: L293-298 — `wilcoxon(per_color_imp)` (scipy.stats)
- θ_equiv는 `cone_shift_validation_results.json`에서 로드 (L267-268)

---

## 수렴 증거 2: RDM Filter 기각 (= Step 3-5 종합)

### 보고자 하는 바
미세 각도 조정(T_ψ)으로 RDM geometry를 교정할 수 있는가?

### 근거 요약
- Step 3: ψ*가 basis artifact (3명 동일 해)
- Step 4: LOCO 0/8, permutation p=1.0
- Step 5: rescue ≤ 50%

### 결론
**T_ψ 메커니즘 자체의 한계** — `W₀ @ C(T_ψ(θ))`에서 θ를 수 도 이동해도 correlation distance RDM 변화 미미. Basis function C(θ)의 기하학이 RDM을 지배.

---

## 수렴 증거 3: Cross-ROI 왜곡 공유

### 보고자 하는 바
V2와 hV4에서 동일 color pair가 왜곡되는가? (체계적 피질 왜곡의 증거)

### 수식
```
distortion_ROI(i,j) = d_CVD_ROI(i,j) − μ_HC_ROI(i,j)    — 28 pairs

Level 1: ρ = Spearman(distortion_V2, distortion_hV4)
Level 2: burden(c) = √(Σⱼ distortion(c,j)²)  →  Spearman(V2_burden, hV4_LOCO_corr)
Level 3: Spearman(JND_ratio, V2_distortion)    — 행동 데이터 (n=8 pairs)
```

### 결과
| Level | sub-08 r | sub-09 r | sub-10 r | 판정 |
|-------|:---:|:---:|:---:|:---:|
| 1 (28-pair) | **0.878** | 0.472 | 0.112 | **PASS** (sub-08) |
| 2 (8-color) | -0.214 | -0.167 | +0.333 | **FAIL** (전원) |
| 3 (JND) | 0.500 | — | — | Underpowered |

- Level 1 PASS: V2-hV4 pair 왜곡 프로필 공유 → **체계적 피질 왜곡**
- Level 2 FAIL: 28→8 집약 시 정보 손실 → pair-level 최적화 필요
- **해석**: 저차원 stimulus 조작(T_ψ)으로 해소 불가능한 multi-ROI 공유 왜곡

### 코드
`loss_prevalidation/scripts/check_cross_roi_consistency.py`
- Level 1: `run_level1()` (L176-225) — `spearmanr(v2_dist, hv4_dist)` per subject
- Level 2: `run_level2()` (L232-299) — `compute_distortion_burden()` (L163-169) per color → Spearman with LOCO
- Level 3: `run_level3()` (L306-383) — JND ratio vs V2 distortion (sub-08 only)
- Burden 정의: `float(np.sqrt(np.sum(distortion[idx] ** 2)))` (L169)

---

## 전체 논리 흐름도

```
① Cone shift 재적용 → 악화 (Wilcoxon p<0.05)
   → "피질이 이미 보상 중, 망막 shift 재적용 = 과교정"

② T_ψ(θ) Fourier 변환 → basis artifact + LOCO 0/8 + perm p=1.0
   → "미세 각도 조정으로는 RDM geometry 교정 불가"

③ V2↔hV4 동일 왜곡 → cross-ROI 체계적 피질 왜곡 확인
   → "저차원 stimulus 조작으로 해소 불가능"

⇒ 결론: CVD gap은 stimulus-space 교정 불가 → cortical locus
```

---

## 코드 파일 요약

| 테스트 | 파일 경로 | 핵심 함수 |
|--------|----------|----------|
| Step 3 (Pattern/RDM/Nested) | `future_phase2_filter_optimization/scripts/step3_filter_estimation.py` | `fit_model_A()`, `fit_model_B()`, `fit_model_0()` |
| Step 3 (모델 비교) | `future_phase2_filter_optimization/scripts/utils_filter.py` | `nested_model_comparison()` |
| Step 4 (LOCO) | `future_phase2_filter_optimization/scripts/step4_validation.py` | `run_loco_validation()`, `loco_fold()` |
| Step 4 (Permutation) | `future_phase2_filter_optimization/scripts/step4_validation.py` | `run_permutation_test()` |
| Step 5 (Rescue) | `future_phase2_filter_optimization/scripts/step5_pairwise_diagnostic.py` | `diagnose_pairs()`, `load_fdr_pairs()` |
| Cone shift | `future_phase1_forward_model/scripts/cone_shift_loco.py` | `evaluate_prediction()`, `build_W_HC_for_cvd()` |
| Cross-ROI | `loss_prevalidation/scripts/check_cross_roi_consistency.py` | `run_level1()`, `run_level2()`, `run_level3()` |
| 공통 유틸 | `future_phase2_filter_optimization/scripts/utils_filter.py` | `T_psi()`, `loss_rdm()`, `compute_predicted_rdm()` |
| 결과 JSON | `results/step{3,4,5}_*/sub-{08,09,10}_*.json` | — |
