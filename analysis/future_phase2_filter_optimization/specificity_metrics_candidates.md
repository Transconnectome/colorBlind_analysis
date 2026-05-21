# Specificity Metric Candidates — for HC vs CVD Separation Test

**Purpose**: 행동 / 신경 fit 의 argmin 이 CVD-distinct 인지, HC pool 과 구분되는지 평가하는 *statistical* metric 후보 정리. 우리 N=7 HC + N=2 CVD 제약 하에 valid 한 것들만.

**Use case**:
1. Equivalence test (behav-only argmin ≈ neural-only argmin) — *우리 paper 의 primary check*
2. CVD-vs-HC separation (CVD argmin 이 HC argmin pool 의 outlier 인가)
3. Robustness across subjects (sub-08 vs sub-09 의 argmin 안정성)

**Constraint**: HC FPR=100% under naive label permutation (project memory) → 새 metric 은 *baseline_ρ confound* 와 *small-n* 모두 통제해야.

---

## §1. Distance-based (descriptive)

### M1. Mahalanobis distance
- **Form**: $D_M(\hat{\theta}_{CVD}, \mu_{HC}) = \sqrt{(\hat{\theta}_{CVD} - \mu_{HC})^T \Sigma_{HC}^{-1} (\hat{\theta}_{CVD} - \mu_{HC})}$
- **Pros**: HC variability (Σ_HC) 자동 반영. Tregillus 의 sc t-test 와 유사한 정신.
- **Cons**: N=7 HC → Σ_HC 추정 unstable. Outlier (sub-04) sensitivity.
- **Use**: descriptive percentile reporting. p-value claim 보류.

### M2. Z-score normalized argmin distance
- **Form**: $z = (\hat{\theta}_{CVD} - \mu_{HC}) / \sigma_{HC}$
- **Pros**: 직관적, 표현 단순.
- **Cons**: 단변량 (β_s 와 β_c 분리 필요). 다변량 통합 시 M1 으로.
- **Use**: per-parameter reporting (β_s 와 β_c 별도).

### M3. Cosine similarity in parameter space
- **Form**: $\cos\theta = \frac{\hat{\theta}_{CVD} \cdot \mu_{HC}}{\|\hat{\theta}_{CVD}\| \|\mu_{HC}\|}$
- **Pros**: scale 무관, *direction* 강조.
- **Cons**: magnitude 정보 손실.
- **Use**: angular distortion direction 의 cross-subject consistency.

---

## §2. Permutation-based (frequentist null)

### P1. Label-permutation null (single-step)
- **Form**: HC vs CVD label shuffle → null distribution of (argmin distance). Observed CVD-HC distance vs null.
- **Pros**: 가장 표준. assumption-free.
- **Cons**: **우리 HC FPR=100% 이미 확인됨 — naive label perm 은 작동 안 함**.
- **Use**: ❌ 사용 안 함 (이미 검증 실패).

### P2. Baseline-corrected permutation
- **Form**: argmin 의 baseline_ρ confound 제거 후 permutation.
   - Step 1: baseline_ρ (HC LOO 결과) 를 covariate 로 regress out.
   - Step 2: residual 의 permutation null.
- **Pros**: project memory 의 baseline_ρ confound (corr=−0.894) 직접 통제.
- **Cons**: regression 가정 (linear), additional complexity.
- **Use**: HC FPR 의 baseline_ρ-corrected version 이 가능한지 검증용.

### P3. Full-grid permutation (selection-aware)
- **Form**: per-perm 1326 grid 의 argmin 재추출 → selection-corrected null.
- **Pros**: PI critique D1 의 정확한 답. Selection variance 직격.
- **Cons**: 비용 36h on node2.
- **Use**: ★ Primary frequentist test.

---

## §3. Bayesian (evidence-based)

### B1. Bayes factor BF₁₀ (alternative vs null)
- **Form**: M₁ = "CVD-distinct model", M₀ = "HC-pool model"; BF = $p(D|M_1) / p(D|M_0)$
- **Pros**: 가장 정확한 evidence 정량화. Equivalence (BF₀₁ > 3) 검정 자연스러움.
- **Cons**: prior 가정 (Cauchy / normal / uniform) 의 sensitivity.
- **Use**: ★ Primary Bayesian test. Equivalence test 의 핵심.

### B2. Bayes factor for equivalence (BF₀₁)
- **Form**: 동일 BF 의 inverse. BF₀₁ > 3 → "evidence for equivalence".
- **Pros**: 사용자 #7 의 "같은지" 검정의 *frequentist-free* form.
- **Cons**: 동일.
- **Use**: ★ Behav-only ≈ Neural-only argmin equivalence 검정.

### B3. Posterior of effect size
- **Form**: Effect size δ 의 posterior distribution 의 credible interval.
- **Pros**: continuous 정량화.
- **Use**: secondary, supplementary.

---

## §4. Equivalence testing (frequentist)

### E1. TOST (Two One-Sided Test)
- **Form**: H₀ : |argmin_behav − argmin_neural| ≥ Δ (사전 정의). 2 one-sided t-test 동시 p < α.
- **Pros**: Frequentist 표준. journal 친화.
- **Cons**: Δ 의 *사전 정의* 어려움 (사전 등록 권장).
- **Use**: ★ Sameness 검정의 frequentist primary.

### E2. Confidence interval inclusion
- **Form**: Bootstrap CI of distance 가 [−Δ, Δ] 안에 포함.
- **Pros**: TOST 와 equivalent, 직관적 plot.
- **Use**: TOST 의 graphical complement.

### Δ 의 선택 권장
- HC pool 의 inter-subject variability (n=7 HC argmin 의 SD).
- 예: σ(β_s) ≈ 8°, σ(β_c) ≈ 6° → Δ ≈ √(8² + 6²) ≈ 10° equivalence band.
- 사전 등록 필요.

---

## §5. Multivariate classification (sample-size-aware)

### C1. LDA + LOO-CV
- **Form**: n=9 (7 HC + 2 CVD) 에 LDA fit, leave-one-out 정확도.
- **Pros**: small-n 에 robust. Binary classification 의 직접 검정.
- **Cons**: n=2 CVD → LOO-CV 의 CVD-side 검정력 약함.
- **Use**: ★ Emery k-means 의 *우리식 등가*.

### C2. Logistic regression with leave-one-subject-out
- **Form**: Subject 별 hold-out, posterior probability.
- **Pros**: continuous probability output.
- **Cons**: n=9 에 logistic overfit 위험.
- **Use**: secondary.

### C3. Silhouette score
- **Form**: 각 sample 의 within-cluster 와 between-cluster 평균 distance 의 ratio.
- **Pros**: descriptive cluster quality.
- **Cons**: assumption: clusters exist.
- **Use**: descriptive only.

---

## §6. 최종 권고 — Tier 구조

### Tier 1 (★ Primary, paper Methods 에 명시)
- **B1 / B2** Bayes factor (BF₁₀ for separation, BF₀₁ for equivalence)
- **E1** TOST for behav ≈ neural argmin equivalence
- **P3** Full-grid permutation null (selection-aware)
- **C1** LDA + LOO-CV (Emery 식 separation)

### Tier 2 (Supplementary, robustness)
- **M1** Mahalanobis distance (descriptive percentile)
- **M2** Per-parameter z-score (β_s, β_c 별도)
- **P2** Baseline-corrected permutation (HC FPR 의 root cause check)

### Tier 3 (보류)
- **P1** Naive label permutation (HC FPR=100% — 사용 불가)
- **C3** Silhouette (assumption 약함)

---

## §7. 사용자 결정 필요 사항

1. **Δ (equivalence band)** 의 사전 등록 — HC pool SD-derived (위 §4)? 또는 다른 정의?
2. **Bayes factor prior** — Cauchy (Jeffreys default) vs normal (informed)? Project memory 의 *경험적 prior* 사용 가능.
3. **Tier 1 모두 시행** 또는 일부?

---

## §8. References

- Tregillus 2021: sc one-sample t-test against 1 (우리 M1/B1 의 영감)
- Emery 2021: k-means cluster classification (우리 C1 의 영감)
- Bayes factor for equivalence: Rouder, Speckman, Sun, Morey, Iverson 2009
- TOST: Schuirmann 1987, Lakens 2017
