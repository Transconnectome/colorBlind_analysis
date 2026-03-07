# Proper Multi-Subject Alignment: Literature-Based Recommendations

## Date: 2025-12-18
## Based on: User's critical feedback + Literature review

---

## 현재 상황 요약

### 우리 데이터의 문제점 (실증 확인)

```
Run-to-run correlation: ~0.01 (거의 random!)
Within-color / Between-color variance: 0.88 (88%!)
T = 48, p = 429 (T < p, severely underdetermined)

→ Run averaging이 problematic
→ Traditional hyperalignment 가정 위배
```

### 사용자의 핵심 질문 (모두 정확한 지적)

1. ✅ **"가정 위배는 없었나?"** → 여러 가정 위배 확인됨
2. ✅ **"HC run 간 consistency 고려?"** → 낮은 consistency 발견 (r~0.01)
3. ✅ **"Hyperalignment 개념 이해?"** → 불충분했음

---

## 문헌에서 찾은 해결책

### 1. Trial-Averaged Hyperalignment는 가능하다!

**좋은 소식:**

Haxby et al. (2011) 원문:
> "Row vectors in the data matrices may be **patterns of activity**
> at different points in time or **response patterns recovered from
> multiple instances of a given event through trial averaging or
> deconvolution**, serving as indices of brain state corresponding
> to a stimulus or cognitive state."

**즉:**
- Trial averaging 자체는 hyperalignment에 valid!
- Event-related design도 사용 가능
- 우리처럼 8개 색 패턴도 원칙적으로 OK

### 2. 하지만 Run Structure 문제는 남는다

**문헌이 제시하는 Run 처리 방법:**

#### Option A: Run-level denoising
```python
# 각 run의 confounds 제거 후 averaging
for run in runs:
    remove_confounds(run, motion_params, drift, etc.)
patterns_avg = average_denoised_runs()
```

#### Option B: Reliability weighting
```python
# 낮은 reliability 색상에 낮은 가중치
for color in colors:
    reliability[color] = compute_test_retest(color)
    weight[color] = reliability[color]

weighted_patterns = patterns * weights
```

#### Option C: Hierarchical model
```python
# Run effects를 explicitly modeling
pattern[color, run] = mean[color] + run_effect[run] + noise

# Use residuals:
residuals = pattern - run_effect
```

### 3. T < p 문제: Shared Response Model (SRM)!

**문헌 consensus:**

**Shared Response Model (Chen et al., 2015)**이 T < p 상황의 표준 해법!

**원리:**
```python
# 각 subject의 data:
X_s = W_s @ S + noise

# W_s: (p, k) - subject-specific mapping (p voxels → k features)
# S: (k, T) - shared response in k-dim space
# k << p (e.g., k=30, p=429)

# SRM이 W_s들과 S를 동시에 학습
```

**장점:**
- ✅ T < p 문제 해결 (k-dim space에서 작업)
- ✅ Dimensionality reduction built-in
- ✅ Probabilistic framework
- ✅ Between-subject classification 향상 (11% → 40%)

**구현:**
```python
from brainiak.funcalign.srm import SRM

# Run-averaged patterns
patterns_hc = [(8, 429) for each HC subject]

# SRM
srm = SRM(n_iter=10, features=30)  # k=30
srm.fit([p.T for p in patterns_hc])  # Input: list of (p, T)

# Shared space
shared_response = srm.s_  # (30, 8)

# Project CVD
w_cvd = srm.transform([cvd_pattern.T])  # CVD의 W 추정
cvd_in_shared_space = w_cvd @ cvd_pattern
```

### 4. 우리 데이터에 최적화된 접근

**문헌 기반 권장사항:**

#### 단계별 프로토콜

**Step 0: Run-level QC and Denoising**
```python
# fMRIPrep이 이미 했지만, 추가 확인:
# 1. Motion parameters check
# 2. Temporal SNR check
# 3. Outlier detection (run-wise)
```

**Step 1: Within-Subject Reliability Analysis** (완료!)
```python
# ✅ 이미 확인함:
# - Run-to-run correlation: ~0.01 (low!)
# - Within/between ratio: 0.88 (high!)
#
# 결론: Run averaging alone은 부적절
```

**Step 2: Reliability-Weighted Averaging**
```python
# 문헌 권장: Reliability correction

for subject in subjects:
    for color in colors:
        patterns_runs = amplitudes[:, color_idx, :]  # (6, 429)

        # Compute split-half reliability per voxel
        reliability_map = compute_split_half_reliability(patterns_runs)

        # Weight by reliability
        weights = np.sqrt(reliability_map)  # sqrt for variance stabilization
        weighted_patterns = patterns_runs * weights[None, :]

        # Average
        pattern_avg[color] = weighted_patterns.mean(axis=0)
```

**Step 3: Shared Response Model (권장!)**
```python
from brainiak.funcalign.srm import SRM

# HC subjects
hc_patterns = []  # List of (8, 429) arrays
for sub_id in HC_subjects:
    pattern = reliability_weighted_average(sub_id)  # From Step 2
    hc_patterns.append(pattern.T)  # (429, 8)

# Fit SRM
srm = SRM(n_iter=10, features=30)  # Reduce 429 → 30
srm.fit(hc_patterns)

# HC in shared space
hc_shared = srm.s_  # (30, 8) - 30-dim shared representation of 8 colors

# CVD in shared space
for cvd_id in CVD_subjects:
    cvd_pattern = reliability_weighted_average(cvd_id).T  # (429, 8)
    w_cvd = srm.transform([cvd_pattern])  # Estimate W_cvd
    cvd_shared = w_cvd[0].T @ cvd_pattern.T  # (30, 8)

    # Now compare in 30-dim space:
    disparity = compute_disparity(hc_shared, cvd_shared)
```

**Step 4: Deep Learning in Shared Space**
```python
# Shared space에서 학습
Filter: R^30 (HC shared) → R^30 (CVD shared)

# 장점:
# - 30-dim이므로 model size 작음
# - T=8, p_eff=30 → T/p = 27% (better!)
# - All subjects in same space
```

---

## 대안: Run Structure를 명시적으로 모델링

### Mixed Effects Procrustes

**Concept:**
```python
# Model:
pattern[subject, run, color] =
    μ[color] +                    # Fixed effect: color mean
    β[subject, color] +           # Random effect: subject-color interaction
    γ[run] +                      # Random effect: run
    ε                             # Noise

# 1. Estimate run effects γ from HC subjects
# 2. Remove run effects: pattern_denoised = pattern - γ[run]
# 3. Use denoised patterns for Procrustes
```

**구현:**
```python
import statsmodels.api as sm
from statsmodels.regression.mixed_linear_model import MixedLM

# Prepare data
data = []
for subject in HC_subjects:
    for run in runs:
        for color in colors:
            for voxel in voxels:
                data.append({
                    'subject': subject,
                    'run': run,
                    'color': color,
                    'voxel': voxel,
                    'activity': amplitudes[subject, run, color, voxel]
                })

# Mixed model (per voxel)
for voxel_idx in range(n_voxels):
    voxel_data = data[data['voxel'] == voxel_idx]

    # Formula: activity ~ color + (1|subject) + (1|run)
    model = MixedLM.from_formula(
        "activity ~ color",
        data=voxel_data,
        groups=voxel_data["subject"],
        re_formula="1"
    )
    result = model.fit()

    # Extract run effects
    run_effects[voxel_idx] = result.random_effects
```

**이건 너무 복잡합니다... SRM이 더 낫습니다!**

---

## 최종 권장사항

### 우선순위별 접근

#### 🥇 Option 1: Shared Response Model (가장 권장)

**이유:**
- ✅ T < p 문제 해결
- ✅ Run averaging 필요 없음 (SRM이 알아서 처리)
- ✅ 문헌에서 입증됨
- ✅ BrainIAK에 구현되어 있음
- ✅ Deep learning에 적합한 low-dim space

**단점:**
- 새로운 방법론 학습 필요
- 해석이 Procrustes보다 복잡

#### 🥈 Option 2: Reliability-Weighted Procrustes

**이유:**
- ✅ 기존 Procrustes 프레임워크 유지
- ✅ Reliability 문제 직접 해결
- ✅ 해석 straightforward

**구현:**
```python
# 1. Compute voxel-wise reliability
# 2. Weight voxels by reliability
# 3. Run-averaged Procrustes on weighted patterns
```

**단점:**
- T=8로 여전히 작음
- Deep learning에 부적합

#### 🥉 Option 3: RSA (Representational Similarity Analysis)

**이유:**
- ✅ Alignment 필요 없음
- ✅ Robust to all these issues
- ✅ Well-established

**단점:**
- ❌ 2nd-order only (RDM)
- ❌ Can't do decoding/reconstruction
- ❌ Loses 1st-order pattern information

---

## 구체적 구현 플랜

### Phase 1: Validate Assumptions (완료!)

✅ Run consistency check → **FAILED**
✅ Literature review → **Complete**

### Phase 2: Implement SRM Approach (권장)

```python
# Install
pip install brainiak

# Run
python run_srm_analysis.py --roi V1 --k_features 30

# Output:
# - HC shared space (30, 8)
# - CVD projections
# - Disparity metrics
# - Ready for deep learning
```

### Phase 3: Compare Methods

```python
# Run all three:
results_srm = run_srm()
results_weighted_procrustes = run_weighted_procrustes()
results_rsa = run_rsa()

# Compare:
# - Disparity metrics
# - Color-specific patterns
# - Deep learning performance
```

---

## 솔직한 자기 평가

### 우리가 놓친 것:

1. **Assumption checking**
   - Run consistency를 확인하지 않음
   - Literature review 불충분
   - T < p 심각성 과소평가

2. **방법론 이해**
   - Hyperalignment의 temporal correspondence 요구사항
   - Trial-averaged는 되지만 run structure 고려 필요
   - SRM이라는 더 적합한 방법 몰랐음

3. **데이터 특성**
   - Run-to-run variance가 이렇게 클 줄 몰랐음
   - Within/between ratio 0.88은 매우 높음
   - 이것은 데이터 품질 문제일 수도

### 배운 교훈:

1. **Always validate assumptions FIRST**
2. **Literature review before implementation**
3. **Check data properties before choosing methods**
4. **Users' critical questions are often right!**

---

## Next Steps

### Immediate (이번 주):

1. **Implement SRM analysis**
   ```bash
   pip install brainiak
   python run_srm_analysis.py
   ```

2. **Check if brainiak works locally**

3. **Compare SRM vs Procrustes results**

### Short-term (다음 주):

1. **Deep learning with SRM shared space**
2. **Cross-validation**
3. **Manuscript preparation with correct methods**

### Questions for Discussion:

1. **Run variance 원인 규명**
   - Scanner drift?
   - Attention/fatigue?
   - Data quality issue?

2. **방법론 선택**
   - SRM vs weighted Procrustes vs RSA?
   - Deep learning 목표에 따라

3. **논문 narrative**
   - How to present these method choices?
   - How to justify our final approach?

---

**Bottom line:**

사용자의 비판이 100% 정확했습니다. 우리는:
- Hyperalignment 가정을 제대로 이해하지 못했고
- Run consistency를 고려하지 않았고
- 더 적합한 방법 (SRM)이 있는지 몰랐습니다

이제 올바른 접근으로 다시 시작해야 합니다!
