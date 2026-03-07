# Is Procrustes Valid? Critical Re-evaluation

## Date: 2025-12-18
## Question: "Procrustes는 괜찮?"

---

## 핵심 질문의 재정의

Run-to-run correlation이 ~0.01일 때, run averaging 후 Procrustes는 valid한가?

---

## 1. Procrustes vs Hyperalignment: 근본적 차이

### Procrustes의 Assumptions

```python
# Procrustes 입력:
X = (8 colors, 429 voxels)  # 8 color patterns
Y = (8 colors, 429 voxels)  # 8 color patterns (다른 subject)

# 목표:
# X와 Y의 8개 점(color patterns)을 기하학적으로 정렬

# 필요한 가정:
1. X와 Y가 같은 8개 색을 represent
2. 각 행이 하나의 color pattern
3. Geometric relationship (rotation) 존재

# 필요 없는 가정:
❌ Temporal correspondence (행 간 시간적 대응)
❌ T >> p
❌ Run structure
```

### Hyperalignment의 Assumptions (비교)

```python
# Hyperalignment 입력:
X = (T timepoints, p voxels)
Y = (T timepoints, p voxels)

# 필요한 가정:
1. ✅ Row i in X = Row i in Y (same stimulus at same time)
2. ✅ Temporal correspondence
3. ✅ T ≈ p or T > p (preferred)
4. ✅ Stationarity

# Procrustes는 이런 가정들이 필요 없음!
```

**핵심 차이:**

Procrustes는 **단순히 8개 점(color patterns)의 geometric alignment**!
- Temporal structure 필요 없음
- Run structure 필요 없음
- 그냥 "8개 색 패턴이 다른 좌표계에 있을 때, rotation으로 맞추기"

---

## 2. Run Averaging: Low Correlation의 의미 재해석

### 2.1 우리가 발견한 것

```
Run-to-run correlation: r ≈ 0.01
Within-color variance / Between-color variance: 0.88

→ 첫 반응: "Run averaging이 문제다!"
```

### 2.2 하지만 다시 생각해보면...

**Correlation이 낮다 ≠ Averaging이 나쁘다**

#### Scenario A: Random Noise 지배

```python
# 각 run의 측정:
pattern[run, color] = true_pattern[color] + noise[run]

# noise[run]은 independent (correlation = 0)

# Averaging:
pattern_avg[color] = mean(pattern[:, color])
                   = true_pattern[color] + mean(noise)
                   ≈ true_pattern[color]  # noise cancels out!

# SNR improvement:
SNR_single = σ_signal / σ_noise
SNR_avg = σ_signal / (σ_noise / √6) = √6 × SNR_single

→ ✅ Averaging은 여전히 유용! (SNR 2.45배 향상)
```

#### Scenario B: Systematic Run Effects

```python
# 각 run의 측정:
pattern[run, color] = true_pattern[color] + run_effect[run] + noise

# run_effect가 크면:
# - Run 간 correlation 낮아짐
# - Averaging 시 run_effect가 bias 유발

→ ⚠️ 이 경우 run effect 제거 필요
```

### 2.3 어떤 시나리오인가?

**검증 필요:**

```python
# 1. Run effects가 systematic한가?
# → Run 1~6의 전체 패턴에 trend가 있나?

# 2. Run-to-run variance의 성질?
# → Random noise vs systematic drift

# 3. Averaging 후 discriminability는?
# → Between-color structure가 보존되나?
```

---

## 3. 실증적 검증: Averaging 전/후 비교

### Test 1: Between-Color Discriminability

```python
# Run averaging 전
for run in runs:
    rdm_run = compute_rdm(amplitudes[run])  # (8, 8)
    discriminability_run = measure_structure(rdm_run)

# Run averaging 후
pattern_avg = amplitudes.mean(axis=0)  # (8, 429)
rdm_avg = compute_rdm(pattern_avg)
discriminability_avg = measure_structure(rdm_avg)

# 비교:
if discriminability_avg > mean(discriminability_runs):
    print("✅ Averaging improves structure")
else:
    print("❌ Averaging degrades structure")
```

### Test 2: Classification Performance

```python
# Single-run classification
for run in runs:
    acc_run = classify_colors(amplitudes[run])

# Average-pattern classification
pattern_avg = amplitudes.mean(axis=0)
acc_avg = classify_colors(pattern_avg)

# 비교:
if acc_avg > mean(acc_runs):
    print("✅ Averaging improves classification")
```

### Test 3: Run Effect Detection

```python
# PCA on all runs concatenated
data_all_runs = amplitudes.reshape(6*8, 429)
pca = PCA(n_components=10)
pca.fit(data_all_runs)

# Check if PC1 or PC2 codes for run number
run_labels = [1,1,1,1,1,1,1,1, 2,2,2,2,2,2,2,2, ...]
for pc_idx in range(10):
    corr = pearsonr(pca.components_[pc_idx], run_labels)
    if corr > 0.5:
        print(f"⚠️ PC{pc_idx} codes for run effect")
```

---

## 4. Procrustes의 Validity: T vs p 문제

### 4.1 문제 정의

```
Procrustes after averaging:
T = 8 colors
p = 429 voxels (or 279 after feature selection)

T << p (severely underdetermined)

→ 이것이 문제인가?
```

### 4.2 Procrustes의 T vs p

**중요한 깨달음:**

```python
# Procrustes solves:
min_R ||X - Y @ R||^2
subject to R.T @ R = I

# Optimization은 다음을 통해:
M = Y.T @ X  # (p, p) cross-covariance
U, S, Vt = svd(M)
R = U @ Vt

# SVD는 M의 structure에서 작동
# M = Y.T @ X에서:
# - Y.T: (p, T) = (429, 8)
# - X: (T, p) = (8, 429)
# - M: (p, p) = (429, 429)

# 문제:
# Y.T @ X의 rank ≤ min(p, T) = 8

→ M은 rank-8 matrix (429차원 중 8차원만 정보)
→ SVD의 427개 특이값은 0
→ Rotation이 underdetermined!
```

**이것은 심각한 문제입니다!**

### 4.3 문헌에서의 해법

**Regularization:**

```python
# Ridge regularization
M = Y.T @ X + λ * I

# 또는 low-rank approximation
U, S, Vt = svd(Y.T @ X)
S_reg = S.copy()
S_reg[S < threshold] = threshold  # Floor small singular values
M_reg = U @ diag(S_reg) @ Vt
```

**우리가 이미 하고 있는 것:**
```python
# hyperalignment_core.py에서:
M = X.T @ Y + self.regularization * np.eye(X.shape[1])
# regularization = 0.01
```

✅ 이미 regularization 하고 있음!

---

## 5. Feature Selection의 영향

### 5.1 원래 데이터

```
Before feature selection:
(6 runs, 8 colors, 429 voxels)

After run averaging:
(8 colors, 429 voxels)

T/p = 8/429 = 1.9%
```

### 5.2 Feature Selection 후

```
After feature selection (ANOVA):
(8 colors, 279 voxels)  # or ~100-200 depending on threshold

T/p = 8/279 = 2.9%
or T/p = 8/150 = 5.3%

→ 여전히 T << p
```

### 5.3 대안: 더 Aggressive한 Feature Selection

```python
# Option 1: Top-k voxels
k = 50  # T/p = 8/50 = 16% (better!)
top_voxels = select_top_k_voxels(amplitudes, k=50)

# Option 2: PCA
pca = PCA(n_components=20)  # T/p = 8/20 = 40% (much better!)
patterns_pca = pca.fit_transform(patterns_avg.T).T

# Option 3: Use T > p criterion
# Need T ≥ p → need p ≤ 8
# But p=8은 너무 적음...
```

---

## 6. 실제 성능 확인: 원래 Procrustes 결과

### 우리의 이전 결과를 다시 보면

```python
# Phase 2b results (Procrustes-based)
# Group-level classification & reconstruction

# 이미 수행한 분석:
# 1. Pairwise Procrustes alignment (HC-CVD)
# 2. Disparity metrics
# 3. Color-specific distortions
# 4. Statistical significance tests

# 결과가 의미 있었나?
# → 이것을 확인해야!
```

**검증 필요:**
1. Classification accuracy가 chance level보다 유의하게 높은가?
2. CVD vs HC disparity가 일관된 패턴을 보이는가?
3. Color-specific effects가 생리학적으로 타당한가?

---

## 7. 결론: Procrustes는 괜찮은가?

### ✅ Procrustes는 기본적으로 Valid

**이유:**

1. **Temporal correspondence 불필요**
   - 8개 color patterns의 geometric alignment
   - Run structure와 무관
   - Hyperalignment의 문제들이 여기엔 해당 없음

2. **Run averaging의 목적이 다름**
   - SNR 향상: √6 배 (random noise cancellation)
   - 더 robust한 color representation
   - Low correlation ≠ averaging is bad

3. **Regularization 이미 적용**
   - T < p 문제를 ridge regularization으로 완화
   - λ = 0.01

### ⚠️ 하지만 주의사항

1. **T << p 문제는 여전히**
   - T/p = 2.9% (279 voxels)
   - Rotation이 underdetermined
   - 해법:
     * Stronger regularization
     * More aggressive feature selection
     * PCA preprocessing

2. **Run consistency 낮음**
   - r ≈ 0.01은 우려스러움
   - 원인 규명 필요:
     * Random noise (OK)
     * Systematic run effects (문제)
   - 검증 필요:
     * Averaging 전/후 discriminability
     * Classification performance

3. **Deep learning에는 여전히 부적합**
   - T=8은 너무 적음
   - 48 samples (run-level) 사용 불가 (run correlation 0)
   - SRM이 더 나음

### 📋 실증 검증 필요

**즉시 확인해야 할 것:**

```python
# 1. Run averaging 효과
check_averaging_improves_structure()

# 2. Run effects 존재 여부
check_systematic_run_effects()

# 3. 원래 Procrustes 결과의 validity
validate_previous_procrustes_results()

# 4. Feature selection threshold 최적화
optimize_feature_selection_for_procrustes()
```

---

## 8. 최종 답변

### "Procrustes는 괜찮?"

**조건부 YES:**

✅ **Procrustes 자체는 valid:**
- Run averaging 후 8 color patterns에 적용
- Temporal correspondence 필요 없음
- Geometric alignment으로서 타당함

⚠️ **하지만 개선 필요:**
- Run averaging의 효과 검증
- Run effects 확인 및 제거
- Feature selection 최적화 (T/p ratio 향상)
- Regularization 조정

❌ **Deep learning에는 부적합:**
- T=8은 너무 적음
- SRM 또는 다른 방법 필요

### 권장 순서:

1. **Run consistency 원인 규명**
   ```python
   python check_run_effects.py
   # - Random noise vs systematic drift?
   # - Scanner-related vs cognitive?
   ```

2. **Run averaging 효과 검증**
   ```python
   python validate_averaging.py
   # - Discriminability 향상?
   # - Classification accuracy?
   ```

3. **Procrustes 최적화**
   ```python
   # - Feature selection threshold
   # - Regularization strength
   # - PCA preprocessing
   ```

4. **원래 결과 재검증**
   ```python
   # Phase 2b 결과가 robust한가?
   ```

5. **Deep learning에는 SRM 사용**
   ```python
   # Procrustes: group comparison, statistics
   # SRM: deep learning, prediction
   ```

---

**Bottom line:**

Procrustes는 hyperalignment보다 **훨씬 더 적합**합니다!
- 가정이 덜 restrictive
- Run structure 문제 회피
- T < p도 regularization으로 완화 가능

하지만 run averaging의 효과를 검증하고,
필요하면 run effects 제거 후 사용해야 합니다.
