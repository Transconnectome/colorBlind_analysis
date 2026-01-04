# Hyperalignment Critical Issues Analysis

## Date: 2025-12-18
## Author: Response to critical user feedback

---

## 🚨 User's Critical Questions

1. **가정 위배는 없었나?**
2. **HC의 run 간 consistency는 고려하지 않나?**
3. **Hyperalignment의 개념 및 가정을 제대로 이해했나?**

**답변: 모두 정당한 우려입니다. 심각한 문제가 있습니다.**

---

## 1. Hyperalignment의 기본 가정 (Haxby et al., 2011)

### 원래 Hyperalignment의 전제조건

```python
# 원래 hyperalignment (movie watching)
Subject 1: [t=0, t=1, t=2, ..., t=1000]  # Timepoints
Subject 2: [t=0, t=1, t=2, ..., t=1000]  # Same timepoints

# 핵심 가정:
# 1. t=100에서 Subject 1과 Subject 2는 SAME stimulus를 보고 있음
# 2. Row index가 temporal/stimulus correspondence를 나타냄
# 3. Shared stimulus → Shared neural geometry
```

**가정:**

1. **Temporal/Stimulus Correspondence**
   - 모든 피험자의 row i = 같은 stimulus/event
   - Row alignment가 의미 있음

2. **Shared Representational Structure**
   - 같은 stimulus → 같은 neural pattern structure (다른 coordinate에서)
   - Rotation으로 align 가능

3. **Sufficient Observations**
   - T >> p 또는 적어도 T ≈ p
   - Rotation matrix estimation이 well-determined

4. **Stationarity**
   - 시간에 따른 systematic drift 없음
   - 또는 drift가 제거됨

---

## 2. 우리 데이터의 현실

### 2.1 데이터 구조

```python
# Subject 1
amplitudes = (6 runs, 8 colors, 429 voxels)

# 현재 구현에서 reshape
X_subject1 = amplitudes.reshape(48, 429)
# Row 0: Run 1, Color 1 (Red)
# Row 1: Run 1, Color 2 (Orange)
# ...
# Row 8: Run 2, Color 1 (Red)
# ...
# Row 47: Run 6, Color 8 (Magenta)

# Subject 2
X_subject2 = amplitudes.reshape(48, 429)
# Row 0: Run 1, Color 1 (Red)
# ...
```

### 2.2 문제 1: Temporal Correspondence 위배

**Subject 1의 Row 0 vs Subject 2의 Row 0:**

```
Subject 1, Row 0 = Run 1, Red trial
- 실제 시간: ~t=100 TRs (run 1 내 어느 시점)
- Trial 번호: Trial 5
- 자극 제시: 특정 Red 색상

Subject 2, Row 0 = Run 1, Red trial
- 실제 시간: ~t=95 TRs (다를 수 있음)
- Trial 번호: Trial 3
- 자극 제시: 같은 Red이지만 다른 trial

→ 같은 row지만 다른 time, 다른 trial!
```

**이것은 hyperalignment의 핵심 가정 위배입니다!**

원래 hyperalignment는:
```
Row i = 같은 영화 장면, 같은 시간
```

우리:
```
Row i = 같은 색, 하지만 다른 trial, 다른 시간, 다른 run
```

### 2.3 문제 2: Run Structure Ignored

```python
# Run 1의 Red와 Run 6의 Red는 다를 수 있음:
pattern[run=1, color=Red] ≠ pattern[run=6, color=Red]

# 이유:
# - Scanner drift
# - Attention changes
# - Fatigue
# - Learning effects
# - Random noise

# 하지만 현재 구현은 이들을 모두 독립적인 observation으로 취급!
```

**Run-to-run variability를 무시했습니다.**

### 2.4 문제 3: T < p (Underdetermined)

```
T = 48 observations
p = 429 voxels

T/p = 11.2% << 100%

Rotation matrix R ∈ R^(429 × 429)
Estimated from 48 × 429 data

→ Severely underdetermined!
→ Infinite solutions possible
→ Regularization helps but doesn't solve fundamental issue
```

### 2.5 문제 4: Within-Subject Variance

```python
# Color "Red"의 6 runs:
Red_run1, Red_run2, ..., Red_run6

# Variance:
# - Between-color variance: 우리가 원하는 신호
# - Within-color, between-run variance: 노이즈!

# 현재 구현은 이들을 구분하지 않음
```

---

## 3. 원래 Hyperalignment 문헌 검토

### 3.1 Haxby et al. (2011) - Original Paper

**데이터:**
- Movie watching (Raiders of the Lost Ark)
- T = ~2,000 TRs
- p = ~500-1,000 voxels (ventral temporal cortex)
- **T > p** ✅

**핵심:**
- Temporal correspondence: t=100에서 모두 같은 장면
- Shared stimulus space
- **No run structure** - continuous movie

### 3.2 Guntupalli et al. (2020) - Modern Review

**Requirements:**
1. **Shared stimulus space** across subjects
2. **Sufficient samples**: T ≥ p recommended
3. **Temporal alignment**: Row i = same stimulus
4. **Stationary**: No systematic drift

### 3.3 Task-based Hyperalignment?

**문헌 검색 필요:**
- Task-based fMRI with hyperalignment?
- Trial-averaged vs trial-level?
- How to handle run structure?

**Known approaches:**
- **Event-related designs**: Use trial-level betas
- **Block designs**: Use condition-averaged responses
- **Within-subject averaging**: Remove run effects first

---

## 4. 우리 구현의 문제점 요약

| 가정 | Hyperalignment 요구 | 우리 데이터 | 위배? |
|------|-------------------|----------|------|
| **Temporal correspondence** | Row i = same stimulus at same time | Row i = same color, different trial/time | ❌ **YES** |
| **T ≥ p** | T should be ≥ p | T=48 << p=429 | ❌ **YES** |
| **Stationarity** | No run effects | 6 runs with potential drift | ⚠️ **Maybe** |
| **Shared stimulus** | All see same stimuli | Same colors (✓) but different trials | ⚠️ **Partial** |
| **Independence** | Observations independent | Runs are nested structure | ❌ **YES** |

---

## 5. 올바른 접근 방법들

### Option A: Run-Averaged Hyperalignment (가장 안전)

```python
# Step 1: Average across runs FIRST
for subject in subjects:
    amplitudes = load(subject)  # (6, 8, 429)
    color_patterns = amplitudes.mean(axis=0)  # (8, 429)

# Step 2: Hyperalignment on averaged patterns
# T = 8, p = 429
# Problem: T << p (severely underdetermined)

# Step 3: Use dimensionality reduction
from sklearn.decomposition import PCA
pca = PCA(n_components=50)  # Reduce p to 50
for subject in subjects:
    color_patterns_reduced = pca.fit_transform(color_patterns.T).T  # (8, 50)

# Now T=8, p=50 → Still T < p but better
```

**Pros:**
- ✅ Removes run-to-run variance
- ✅ Each row = one color (clean interpretation)
- ✅ No temporal correspondence assumption violated

**Cons:**
- ❌ Very small T (only 8)
- ❌ Requires heavy dimensionality reduction
- ❌ Loses information

### Option B: Procrustes on Run-Averaged (우리의 원래 방법)

```python
# This is what we did with Procrustes!
# Average across runs → (8, p)
# Pairwise alignment

# This is VALID because:
# - No temporal correspondence needed
# - Just geometric alignment of 8 color patterns
# - Well-understood assumptions
```

**이것이 왜 Procrustes를 썼던 이유입니다!**

### Option C: Shared Response Model (SRM)

```python
from brainiak.funcalign.srm import SRM

# SRM handles dimensionality reduction built-in
# Projects to shared latent space (k << p)

srm = SRM(n_iter=10, features=30)  # k=30 latent dimensions

# Input: list of (p, T) arrays
data_list = [subject_data.T for subject_data in subjects]
srm.fit(data_list)

# Get shared response
shared = srm.s_  # (k, T)

# Project new subject
w_new = srm.transform([new_subject.T])
```

**Pros:**
- ✅ Handles T < p
- ✅ Dimensionality reduction built-in
- ✅ Probabilistic framework

**Cons:**
- ⚠️ Still assumes temporal correspondence
- ⚠️ Complex model
- ⚠️ Harder to interpret

### Option D: Representational Similarity Analysis (RSA)

```python
# This is closest to what we should do!

# For each subject, compute RDM
rdm_subject = pdist(color_patterns, metric='correlation')  # (8, 8)

# Compare RDM structures (2nd-order comparison)
# No alignment needed!

# This is what Kriegeskorte recommends for this situation
```

**Pros:**
- ✅ No alignment assumptions
- ✅ Robust to coordinate differences
- ✅ Well-established for comparing representations

**Cons:**
- ❌ Loses 1st-order information (actual patterns)
- ❌ Can't do decoding/reconstruction

---

## 6. What We Should Have Done

### 올바른 순서:

1. **Literature Review First**
   - Hyperalignment assumptions
   - Task-based applications
   - T < p solutions

2. **Data Structure Analysis**
   - Run structure
   - Trial structure
   - Temporal correspondence

3. **Method Selection**
   - If T >> p and temporal correspondence: Hyperalignment
   - If T < p or no temporal correspondence: Procrustes or RSA
   - If dimensionality reduction needed: SRM

4. **Implementation**

### What We Actually Did:

1. ❌ Jumped to implementation
2. ❌ Assumed hyperalignment would work
3. ❌ Ignored run structure
4. ❌ Violated temporal correspondence

---

## 7. Can We Salvage This?

### 7.1 Is Our Current Implementation Valid?

**Answer: NO, not as "hyperalignment"**

But it might be doing something else:
```python
# What we're actually doing:
# "Multi-observation Procrustes alignment"

# Each subject has 48 pattern observations
# We find rotation that best aligns these 48 observations
# to the mean of other subjects' 48 observations

# This is NOT hyperalignment (no temporal correspondence)
# This IS generalized Procrustes (multiple observations)
```

### 7.2 Does It Make Sense?

**Maybe, but we need to interpret differently:**

```python
# Interpretation:
# "Find rotation that makes subject's distribution of
#  color×run observations match the group distribution"

# NOT:
# "Find shared representational space via temporal alignment"
```

### 7.3 Should We Use It for Deep Learning?

**Answer: Risky**

Problems:
- Run structure ignored → biased samples
- T < p → unstable rotations
- No theoretical justification for this exact setup

**Better approach:**
- Run-averaged Procrustes (our original)
- Or properly handle run structure

---

## 8. Recommended Path Forward

### Immediate Actions:

1. **STOP** claiming we're doing "hyperalignment"
   - We're not meeting the assumptions
   - Misleading terminology

2. **Literature search** on:
   - Task-based multi-subject alignment
   - Trial-averaged alignment methods
   - T < p solutions

3. **Re-analyze** with proper method:
   ```python
   Option 1: Run-averaged Procrustes (8 colors)
   Option 2: Run-level Procrustes with run-blocking
   Option 3: RSA (if we only care about structure)
   Option 4: Proper SRM with averaging
   ```

4. **Validate** run consistency:
   ```python
   # Check within-subject run-to-run correlation
   for color in colors:
       patterns = amplitudes[:, color_idx, :]  # (6, 429)
       corr_matrix = np.corrcoef(patterns)
       # If low correlation → run effects are large
       # If high correlation → averaging is justified
   ```

### Long-term:

1. Consult hyperalignment experts
2. Review task-based alignment literature
3. Consider alternative frameworks (RSA, encoding models)

---

## 9. Honest Assessment

### What Went Wrong:

1. **Insufficient literature review**
2. **Assumption checking skipped**
3. **Rushed to implementation**
4. **Ignored data structure**

### What We Learned:

1. **Hyperalignment ≠ any multi-subject alignment**
2. **Temporal correspondence is critical**
3. **T < p is a serious issue**
4. **Run structure matters**

### Moving Forward:

- Be more careful with method assumptions
- Literature review before implementation
- Validate assumptions with data
- Don't oversell what we're doing

---

## 10. Conclusion

**User's questions were 100% correct:**

1. ✅ **"가정 위배는 없었나?"** → YES, 여러 가정 위배
2. ✅ **"HC run 간 consistency 고려?"** → NO, 완전히 무시함
3. ✅ **"Hyperalignment 개념 이해?"** → NOT ENOUGH

**Recommendation:**

- **PAUSE** on hyperalignment approach
- **RETURN** to Procrustes with run-averaging
- **RESEARCH** proper task-based alignment methods
- **VALIDATE** assumptions before implementation

**For deep learning:**
- Use run-averaged Procrustes (proven, valid)
- Or develop proper hierarchical model
- Don't force hyperalignment where it doesn't fit
