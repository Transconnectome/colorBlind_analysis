# Color Filter Pipeline: Brain-to-Stimulus Transformation Plan

**Updated**: 2025-12-18 after Option A Robustness Verification

## 🎯 Ultimate Goal

```
External Stimulus → CVD Eye → CVD Brain → [Filter/Transform] → HC-like Brain → Correct Perception

Loss = distance(CVD_brain_filtered, HC_brain_mean)
→ Deep learning으로 이 loss를 최소화하는 filter 학습
```

---

## ✅ Current Status (Completed)

### Phase 1: Brain Space Analysis ✅

**Option 2D Results**:
- ✅ **Systematic CVD difference 발견**: T = CVD_mean - HC_mean
- ✅ **Magnitude**: RMS 0.507 (V1), 0.653 (V2)
- ✅ **Consistency**: 0.998 across CVD subjects
- ✅ **Color-specific**: Color 5 (red-green) largest difference

**Data**:
- HC_mean: (8 colors, 429 voxels V1 / 233 voxels V2)
- T: (8 colors, 429/233 voxels) - systematic difference
- Position difference (not pattern/RDM)

---

## 🚨 Critical Finding: Reference Bias (Option A Verification)

### Results Summary

| Reference | V1 T RMS | V2 T RMS | HC Disparity | CVD Disparity |
|-----------|----------|----------|--------------|---------------|
| **sub-02** | **0.509** | **0.656** | 0.946 | 0.942 |
| sub-03 | 0.082 | 0.087 | 0.970 | 0.950 |
| sub-05 | 0.082 | 0.081 | 0.956 | 0.943 |
| sub-06 | 0.088 | 0.081 | 0.957 | 0.928 |
| sub-07 | 0.074 | 0.075 | 0.955 | 0.947 |

**Statistics**:
- V1: CV = 102.7% 🚨
- V2: CV = 117.4% 🚨
- **Conclusion**: 🚨 **SENSITIVE to reference choice**

### Permutation Test

| ROI | Observed T | Null Mean | Null Std | p-value | Significant? |
|-----|------------|-----------|----------|---------|--------------|
| V1 | 0.509 | 0.136 | 0.143 | **0.046** | ✅ Yes (marginal) |
| V2 | 0.656 | 0.150 | 0.189 | **0.087** | ⚠️ No (p > 0.05) |

**Interpretation**:
- V1: Marginally significant (p = 0.046)
- V2: Not significant (p = 0.087)
- Small sample size (n=8) limits statistical power

---

## 🔍 Problem Analysis

### Issue 1: Sub-02 Bias

**Why is sub-02 special?**

Hypotheses:
1. **Sub-02가 HC의 outlier**
   - 다른 HC subjects와 매우 다름
   - Disparity 0.94-0.97 (거의 정렬 안 됨)

2. **Sub-02가 오히려 CVD에 가까움?**
   - CVD subjects와 비슷한 특성
   - 그래서 T가 크게 나옴

3. **Coordinate system issue**
   - Sub-02의 좌표계가 특이함
   - Procrustes alignment가 제대로 안 됨

### Issue 2: High Disparity (0.94-0.97)

**Normal Procrustes disparity**: 0.1-0.3 (Option 2B에서는 이랬음)

**Current disparity 0.94-0.97의 의미**:
- Procrustes가 거의 실패
- Alignment가 안 되고 있음
- 왜? 8 colors × n_voxels high-dimensional space에서?

### Issue 3: Reference-dependent T

**문제**:
- Sub-02 reference: T = 0.5-0.6 (큼)
- Others reference: T = 0.07-0.09 (작음)

**의미**:
- T가 reference에 의존
- "Systematic difference"가 실제로 systematic하지 않음
- 또는 sub-02가 문제

---

## 🛠️ Solutions & Next Steps

### Option 1: Exclude sub-02 (Recommended First Step)

**Action**:
```python
HC_SUBJECTS = ['03', '05', '06', '07']  # sub-02 제외
CVD_SUBJECTS = ['08', '09', '10']

# Re-run Option 2D
# New reference: sub-03
```

**Expected**:
- T magnitude reduced
- More consistent across references
- Better disparity values

**Pros**:
- ✅ Simple
- ✅ Quick to test
- ✅ 4 HC subjects still reasonable

**Cons**:
- ⚠️ Sample size reduced (5→4 HC)
- ⚠️ Need to justify exclusion

---

### Option 2: Average Across All References

**Method**:
```python
T_all = []
for ref_id in HC_SUBJECTS:
    T_ref = calculate_T(reference=ref_id)
    T_all.append(T_ref)

T_mean = np.mean(T_all, axis=0)  # Average T
T_std = np.std(T_all, axis=0)    # Uncertainty
```

**Pros**:
- ✅ Reference-independent
- ✅ More robust
- ✅ Confidence intervals

**Cons**:
- ⚠️ Sub-02 bias still affects mean
- ⚠️ High variance (CV > 100%)

---

### Option 3: Reference-free Method (Generalized Procrustes)

**Method**: Align all subjects simultaneously without picking a reference

```python
from sklearn.manifold import MDS

# Generalized Procrustes Analysis
def generalized_procrustes(patterns):
    # Iteratively find common space
    consensus = initialize_consensus(patterns)

    for iteration in range(max_iter):
        aligned = []
        for pattern in patterns:
            aligned.append(procrustes(consensus, pattern))

        consensus = mean(aligned)

    return consensus, aligned

hc_consensus, hc_aligned = generalized_procrustes(HC_patterns)
cvd_consensus, cvd_aligned = generalized_procrustes(CVD_patterns)

T = cvd_consensus - hc_consensus
```

**Pros**:
- ✅ No reference bias
- ✅ All subjects treated equally
- ✅ More principled

**Cons**:
- ⚠️ Complex implementation
- ⚠️ May still have same disparity issues

---

### Option 4: Individual-level Analysis (Fallback)

**If group-level fails completely**:

```python
# For each CVD subject
for cvd_id in ['08', '09', '10']:
    # Find best matching HC subject
    best_hc = find_best_match(cvd_id, HC_SUBJECTS)

    # Calculate individual T
    T_individual = CVD[cvd_id] - HC[best_hc]

    # Use for this CVD only
    filters[cvd_id] = create_filter(T_individual)
```

**Pros**:
- ✅ Personalized
- ✅ Avoids averaging problems

**Cons**:
- ⚠️ No generalization
- ⚠️ Need data for each CVD individual

---

## 📋 Revised Pipeline

### Phase 1A: Re-analyze without sub-02 ✨ **NEW**

**Files to modify**:
- `option2d_procrustes_cvd_comparison.py`
- Change: `HC_SUBJECTS = ['03', '05', '06', '07']`

**Run**:
1. Option 2D again
2. Check T magnitude
3. Reference robustness test
4. Permutation test

**Success criteria**:
- T RMS: 0.3-0.5 (moderate)
- CV < 50% (acceptable)
- Disparity < 0.5 (good alignment)
- p-value < 0.05 (both ROIs)

**Timeline**: 1-2 hours

---

### Phase 1B: Investigate sub-02 ✨ **NEW**

**Questions**:
1. Is sub-02 an outlier in HC group?
2. Sub-02 behavioral data 확인 (colorblind test 결과?)
3. Sub-02 brain activation patterns 시각화

**Methods**:
```python
# 1. Within-HC similarity
for subj in HC_SUBJECTS:
    similarity = correlate(subj, others_mean)
    print(f"sub-{subj}: {similarity}")

# 2. HC vs CVD similarity
for hc in HC_SUBJECTS:
    for cvd in CVD_SUBJECTS:
        similarity = correlate(hc, cvd)
        print(f"HC {hc} vs CVD {cvd}: {similarity}")
```

**Timeline**: 1 hour

---

### Phase 2: Forward Encoding Model (If Phase 1 succeeds)

**Goal**: Learn mapping from stimulus → brain response

#### Step 2A: Model Selection

**Option A: Basis Function Model** (Classical)
```python
# Basis functions: Gaussian tuning curves
def tuning_curve(color_angle, preferred_angle, bandwidth):
    return exp(-((color_angle - preferred_angle)**2) / (2*bandwidth**2))

# Forward model
B = [tuning_curve(angles, pref, bw) for pref in range(0, 360, 45)]
W = fit(brain_responses, B @ colors)
```

**Option B: Neural Network**
```python
class BrainPredictor(nn.Module):
    def __init__(self):
        self.encoder = nn.Sequential(
            nn.Linear(3, 128),  # RGB
            nn.ReLU(),
            nn.Linear(128, 256),
            nn.ReLU(),
            nn.Linear(256, 429),  # Voxels
        )

    def forward(self, stimulus_rgb):
        return self.encoder(stimulus_rgb)

# Train
model.train(stimuli_8colors, brain_responses)
```

**Data**:
- Input: 8 colors (RGB or angle)
- Output: Voxel activations (429 voxels V1)
- Training samples: 8 colors × 8 subjects = 64 samples

**Challenge**: Very limited data (only 8 colors!)

---

### Phase 3: Stimulus-level Transformation

**Goal**: Convert brain-space T to stimulus-space filter

#### Method A: Analytical (if linear model)

```python
# Learn W matrices
W_hc = learn_forward_model(HC_stimuli, HC_brain)
W_cvd = learn_forward_model(CVD_stimuli, CVD_brain)

# Invert to get stimulus transformation
# Brain: B = W @ S
# Want: W_cvd @ S_filtered = W_hc @ S
# Solution: S_filtered = pinv(W_cvd) @ W_hc @ S

T_stimulus = pinv(W_cvd) @ W_hc
```

**Assumption**: Linear relationship (may not hold!)

---

#### Method B: End-to-End Deep Learning (Recommended for final)

```python
class ColorCorrectionFilter(nn.Module):
    def __init__(self):
        # Color transformation network
        self.filter_net = nn.Sequential(
            nn.Linear(3, 64),   # RGB input
            nn.ReLU(),
            nn.BatchNorm1d(64),
            nn.Linear(64, 64),
            nn.ReLU(),
            nn.BatchNorm1d(64),
            nn.Linear(64, 3),   # RGB output
            nn.Sigmoid()        # Keep in [0,1]
        )

        # Pretrained brain predictor (frozen)
        self.brain_predictor = BrainPredictor()
        self.brain_predictor.eval()
        for param in self.brain_predictor.parameters():
            param.requires_grad = False

        # Target: HC brain mean
        self.register_buffer('hc_brain_target',
                           torch.tensor(HC_mean))  # (8, 429)

    def forward(self, stimulus_rgb, color_idx):
        # Apply filter
        filtered_rgb = self.filter_net(stimulus_rgb)

        # Predict CVD brain response
        cvd_brain_pred = self.brain_predictor(filtered_rgb)

        return filtered_rgb, cvd_brain_pred

    def compute_loss(self, filtered_rgb, cvd_brain_pred, color_idx):
        # Main loss: CVD brain → HC brain
        brain_loss = F.mse_loss(cvd_brain_pred,
                               self.hc_brain_target[color_idx])

        # Regularization: Don't change colors too much
        color_loss = F.l1_loss(filtered_rgb, stimulus_rgb)

        # Perceptual: Keep color wheel structure
        # ... (optional)

        return brain_loss + 0.1 * color_loss

# Training
filter_model = ColorCorrectionFilter()
optimizer = Adam(filter_model.filter_net.parameters(), lr=1e-3)

for epoch in range(1000):
    for color_idx, stimulus in enumerate(training_stimuli):
        filtered, brain_pred = filter_model(stimulus, color_idx)
        loss = filter_model.compute_loss(filtered, brain_pred, color_idx)

        loss.backward()
        optimizer.step()
```

**Data augmentation**:
```python
# Generate more training samples
# Interpolate between 8 colors
for i in range(8):
    for j in range(i+1, 8):
        alpha = np.random.uniform(0, 1)
        interpolated_color = alpha * colors[i] + (1-alpha) * colors[j]
        # Use brain predictor to get target
        target_brain = ...
```

---

### Phase 4: Validation & Testing

#### In-sample validation
```python
# Test on 8 original colors
for color_idx in range(8):
    stimulus_orig = colors[color_idx]
    stimulus_filtered = filter_model(stimulus_orig)

    # Measure brain distance reduction
    cvd_brain_orig = measure_brain(CVD_subject, stimulus_orig)
    cvd_brain_filtered = measure_brain(CVD_subject, stimulus_filtered)

    dist_before = distance(cvd_brain_orig, hc_brain_mean[color_idx])
    dist_after = distance(cvd_brain_filtered, hc_brain_mean[color_idx])

    improvement = (dist_before - dist_after) / dist_before * 100
    print(f"Color {color_idx}: {improvement:.1f}% improvement")
```

#### Out-of-sample validation
```python
# Test on new colors (not in training)
test_colors = generate_test_colors(n=16)  # Between training colors

for test_color in test_colors:
    filtered = filter_model(test_color)
    # Measure perceptual similarity to HC
```

#### Psychophysics experiment
```python
# Show filtered images to CVD subjects
# Ask: "Does this look more natural?"
# Compare to original
```

---

## 🎯 Decision Tree

### After Phase 1A (Re-run without sub-02)

**Scenario A: Success** (T RMS 0.3-0.5, CV < 50%, p < 0.05)
```
✅ Proceed to Phase 2
✅ Use HC subjects: 03, 05, 06, 07
✅ Reference: sub-03 (or average)
```

**Scenario B: Still high CV** (CV > 50%)
```
→ Try Option 3: Generalized Procrustes
→ Or Option 4: Individual-level analysis
```

**Scenario C: T too small** (RMS < 0.2)
```
→ CVD difference is subtle
→ May need more sensitive methods
→ Or individual-level approach
```

---

### After Phase 2 (Forward model)

**Scenario A: Good prediction** (R² > 0.5)
```
✅ Use analytical solution (Method A)
✅ Or fine-tune with deep learning (Method B)
```

**Scenario B: Poor prediction** (R² < 0.5)
```
→ Data augmentation
→ Use more complex model
→ Or skip to end-to-end deep learning directly
```

---

## 📊 Success Metrics

### Brain-level validation
- ✅ T magnitude: 0.3-0.5 RMS
- ✅ Reference CV: < 50%
- ✅ Permutation p: < 0.05
- ✅ Disparity: < 0.5

### Stimulus-level validation
- ✅ Brain distance reduction: > 50%
- ✅ Color naturalness: Subjective rating > 7/10
- ✅ Discrimination improvement: Psychophysics test

### Real-world validation
- ✅ Works on natural images
- ✅ Real-time processing possible
- ✅ Stable across lighting conditions

---

## 📝 Documentation Plan

### If successful
**Paper title**: "Deep Learning Color Correction for CVD Based on Neural Representation Alignment"

**Main contributions**:
1. Brain-based CVD characterization (T discovery)
2. Forward encoding model (stimulus → brain)
3. End-to-end filter learning (deep learning)
4. Validation on real CVD subjects

### If group-level fails
**Paper title**: "Individual Variability in Color Representations: Implications for CVD Correction"

**Main contributions**:
1. High individual variability in color representations
2. Reference-dependent systematic differences
3. Individual-level CVD characterization
4. Personalized filter approach

---

## ⏰ Timeline Estimate

### Phase 1A: Re-run without sub-02
- Code modification: 10 min
- Execution: 1 hour
- Analysis: 30 min
- **Total**: 2 hours

### Phase 1B: Investigate sub-02
- Analysis scripts: 30 min
- Visualization: 30 min
- **Total**: 1 hour

### Phase 2: Forward model
- Model implementation: 2-3 hours
- Training: 1 hour
- Validation: 1 hour
- **Total**: 4-5 hours

### Phase 3: Stimulus transformation
- Analytical solution: 2 hours
- Deep learning: 5-10 hours (including tuning)
- **Total**: 7-12 hours

### Phase 4: Validation
- In-sample: 1 hour
- Out-of-sample: 2 hours
- Psychophysics design: 5 hours
- **Total**: 8 hours

**Overall**: 22-28 hours (3-4 working days)

---

## 💡 Key Insights & Lessons

### What we learned
1. ✅ **CVD systematic difference exists** (Option 2D)
2. 🚨 **Reference choice is critical** (Verification)
3. ⚠️ **Sub-02 is special/problematic**
4. ⚠️ **High disparity suggests alignment issues**
5. ✅ **Permutation test validates V1** (marginal)

### What we need to clarify
1. ❓ Why is sub-02 different?
2. ❓ Why is disparity so high (0.94-0.97)?
3. ❓ Is Procrustes appropriate for this data?
4. ❓ Should we use different alignment method?

### Alternative approaches to consider
1. **Canonical Correlation Analysis (CCA)**
   - Find shared subspace
   - Less sensitive to coordinate systems

2. **Representational Similarity Analysis (RSA)**
   - Use RDM directly
   - Bypass Procrustes

3. **Multi-dimensional Scaling (MDS)**
   - Embed in low-D space
   - Compare embeddings

---

## 🔗 Related Documents

- `ORIGINAL_HYPOTHESIS_AND_GOAL.md` - Initial assumptions
- `OPTION2D_RESULTS_DETAILED_EXPLANATION.md` - Option 2D results
- `OPTION_A_METHODOLOGY_VERIFICATION.md` - Data leakage analysis
- `VERIFICATION_SUMMARY_KR.md` - Robustness verification summary

---

**Last Updated**: 2025-12-18
**Status**: Phase 1A ready to execute
**Next Action**: Re-run Option 2D without sub-02
