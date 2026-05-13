# smooth_tikh Paradox Analysis (RESOLVED — REJECTED)

> Date: 2026-03-11 (resolved: 2026-03-11)
> Question: Why does smooth_tikh improve multiple metrics but fail permutation test?
> **Answer: All "improvements" are driven by shared spatial covariance capture, not color signal. smooth_tikh REJECTED.**

---

## The Paradox

### What Improved ✅
1. **Voxel correlation (HC mean):**
   - V1: +0.143 (was +0.130 with ridge_gcv)
   - V2: +0.246 (was +0.150) — **Δ+0.096**
   - V3: +0.100 (was +0.023) — **Δ+0.077**
   - V4: +0.190 (was +0.183)

2. **RDM preservation (artifact check PASSED):**
   - V1 rdm_pearson: +0.531 (was +0.034) — **Δ+0.496, p=0.002***
   - V2 rdm_pearson: +0.457 (was +0.179) — Δ+0.278
   - V3 rdm_pearson: +0.398 (was +0.160) — **Δ+0.238, p=0.006***
   - V4 rdm_pearson: +0.410 (was +0.104) — **Δ+0.306, p=0.049***

3. **HC-CVD separation (V2):**
   - Cohen's d: 3.43 (was 1.85) — **much larger effect**
   - p-value: 0.001 (was 0.022)

### What Failed ❌
**Permutation test (10K shuffles):**
- V1: p=0.331 (null_mean=0.187, observed=0.189)
- V2: p=0.188 (null_mean=0.212, observed=0.216)
- V3: p=0.613 (null_mean=0.128, observed=0.125)
- V4: p=0.613 (null_mean=0.241, observed=0.239)

**All ROIs fail.** Observed ≈ null distribution mean.

---

## Root Cause Analysis

### Why voxel_corr Fails Permutation

**Hypothesis:** Voxel correlation captures TWO components:
1. **Color-discriminative signal** (what we want)
2. **Shared spatial structure** (nuisance variance)

**Shared spatial structure = baseline voxel covariance:**
- Some voxels are generally more active than others
- This pattern is present across ALL colors
- Smoothness penalty (β||DW||²) amplifies this shared structure

**Permutation test result:**
- Shuffling color labels destroys component #1 (color signal)
- But preserves component #2 (spatial covariance)
- smooth_tikh with β=100 → predictions become MORE similar to ANY pattern
- Result: High null baseline (~0.19-0.24, not zero)

**Mathematical view:**
```
voxel_corr(y_pred, y_actual) = corr(Ŵ@C, Y)
                              ≈ corr(shared_pattern, Y) + corr(color_pattern, Y)
                                [covariance component]     [signal component]
```

With shuffled labels:
- Color_pattern component → 0
- Shared_pattern component remains
- smooth_tikh increases the shared_pattern coefficient

### Why RDM Correlation DOES Improve

**Key insight:** RDM (Representational Dissimilarity Matrix) inherently removes mean patterns.

**RDM computation:**
```
RDM[i,j] = distance(pattern_i, pattern_j)
         = 1 - corr(pattern_i - mean, pattern_j - mean)
```

**Mean-centering removes the shared baseline** → RDM captures ONLY color-discriminative geometry.

**Why smooth_tikh helps RDM:**
- Smoothness constraint → better-shaped tuning curves
- In LOCO, each predicted pattern is independently interpolated
- Smooth tuning = more accurate color-specific structure
- RDM preserves this structure while removing baseline

**Artifact check validation:**
- Section 6g artifact (rdm ↓) was for ALL-DATA fitting (8 colors in both train and RDM)
- LOCO RDM uses 8 held-out predictions → each is an independent interpolation
- Result: rdm_pearson genuinely improves (V1 Δ+0.496, p=0.002)

---

## Why This Matters

### smooth_tikh IS Doing Something Right

1. **Color geometry is better preserved** (RDM evidence)
2. **HC-CVD separation is stronger** (d=3.43 vs 1.85 in V2)
3. **Tuning curves are smoother** (biologically plausible)

### But voxel_corr is the Wrong Metric

**Problem:** voxel_corr conflates signal with nuisance variance.

**Evidence:**
- ridge_gcv V1 null_mean = 0.11 (not zero!)
- smooth_tikh V1 null_mean = 0.19 (even higher)
- These baselines reflect voxel covariance structure, not color signal

**Implication:**
- Permutation test with voxel_corr penalizes models that better capture spatial structure
- This is backwards — we want models that capture BOTH spatial AND color structure

---

## Proposed Solutions

### Strategy 1: Switch Primary Metric to RDM Correlation ⭐ *Simplest*

**Rationale:**
- RDM is baseline-invariant (mean-centered distances)
- smooth_tikh shows genuine RDM improvement (artifact check passed)
- RDM directly measures color-discriminative geometry

**Implementation:**
```python
# Phase 2 filter evaluation:
# Primary: RDM correlation (color geometry preservation)
# Secondary: voxel_corr (descriptive, but not gating)

def evaluate_filter(W, T_psi, Y_target):
    Y_pred = W @ C(T_psi(theta))

    # Primary metric
    rdm_pred = compute_rdm(Y_pred)
    rdm_actual = compute_rdm(Y_target)
    primary_score = spearmanr(rdm_pred, rdm_actual)

    # Secondary (descriptive)
    voxel_corr = mean([corr(Y_pred[:, c], Y_target[:, c]) for c in colors])

    return primary_score, voxel_corr
```

**Advantage:**
- No model modification needed
- Leverages smooth_tikh's actual strength (geometry preservation)
- Aligns metric with scientific question (color space structure)

**Validation:**
- Permutation test on RDM correlation (not voxel_corr)
- Expected: smooth_tikh should pass (RDM improvements are genuine)

---

### Strategy 2: Baseline-Corrected voxel_corr

**Idea:** Subtract the permutation null mean from observed values.

```python
# Compute permutation baseline per model/ROI
baseline_voxel_corr = null_mean_from_permutation_test

# Baseline-corrected metric
corrected_voxel_corr = observed_voxel_corr - baseline_voxel_corr
```

**Example (V1):**
- ridge_gcv: observed=0.130, null=0.11 → corrected=+0.020
- smooth_tikh: observed=0.189, null=0.187 → corrected=+0.002

**Interpretation:**
- ridge_gcv has +0.020 color-specific signal above baseline
- smooth_tikh has only +0.002 color-specific signal above baseline
- **Ridge wins** for color-discriminative signal

**Advantage:**
- Separates signal from nuisance variance
- Uses existing permutation infrastructure

**Disadvantage:**
- Requires permutation test for EVERY model × ROI (computationally expensive)
- Baseline correction might amplify noise

---

### Strategy 3: Partial Correlation (Control for Baseline Pattern)

**Idea:** Remove shared spatial pattern before computing voxel_corr.

```python
def partial_voxel_corr(Y_pred, Y_actual):
    # Estimate baseline pattern (mean across colors)
    baseline = Y_actual.mean(axis=0)  # (V_s,) shared pattern

    # Residuals after removing baseline
    Y_pred_res = Y_pred - baseline[np.newaxis, :]
    Y_actual_res = Y_actual - baseline[np.newaxis, :]

    # Correlation on residuals
    return mean([corr(Y_pred_res[c], Y_actual_res[c]) for c in colors])
```

**Advantage:**
- Directly targets color-specific variance
- No permutation test needed

**Disadvantage:**
- Mean pattern might not fully capture nuisance variance
- Might remove some legitimate signal if colors have different mean levels

---

### Strategy 4: Color-Contrast Encoding

**Idea:** Predict color DIFFERENCES, not absolute levels.

```python
# Instead of predicting Y ∈ R^{V_s × 8}
# Predict ΔY ∈ R^{V_s × 28} (pairwise differences)

def fit_contrast_model(W, C):
    # For all pairs of colors (i, j):
    for i, j in pairs:
        Y_contrast_ij = Y[:, i] - Y[:, j]
        C_contrast_ij = C[i] - C[j]
        # Fit: Y_contrast = W @ C_contrast
```

**Advantage:**
- Differences naturally remove baseline (like RDM)
- More robust to gain/offset variations

**Disadvantage:**
- Changes the entire modeling framework
- 28 contrasts vs 8 colors → higher dimensional

---

### Strategy 5: Discriminability-Based Objective

**Idea:** Directly optimize for color discriminability, not voxel correlation.

```python
def fit_W_discriminative(C, X, alpha, beta):
    """
    Objective: Maximize between-color variance while minimizing within-color variance.

    Loss = -trace(W @ S_between @ W.T) / trace(W @ S_within @ W.T)
         + alpha*||W||^2 + beta*||D@W||^2

    where:
    S_between = between-color scatter matrix
    S_within = within-color (across-run) scatter matrix
    """
    # Similar to Linear Discriminant Analysis (LDA)
    # But with smoothness regularization
```

**Advantage:**
- Directly optimizes for color separability
- Less affected by baseline pattern

**Disadvantage:**
- Non-convex objective (iterative optimization)
- May sacrifice absolute prediction quality for discriminability

---

### Strategy 6: Two-Stage Smoothness

**Idea:** Apply smoothness only to color-discriminative components.

```python
# Stage 1: Fit baseline (captures shared structure)
W_baseline = fit_W_ridge(C, X, alpha)
Y_baseline = W_baseline @ C

# Stage 2: Fit deviations (color-specific)
Y_dev = X - Y_baseline
W_dev = fit_W_smooth_ridge(C, Y_dev, alpha, beta)  # smooth only deviations

# Final prediction
Y_pred = Y_baseline + W_dev @ C
```

**Advantage:**
- Separates baseline from color signal
- Smoothness applied only where it helps

**Disadvantage:**
- Unclear if Y_baseline properly captures all nuisance variance
- Two-stage fitting might not be optimal

---

## Rescue Attempts (ALL FAILED)

### Attempt 1: Condition-Centering ❌

**Hypothesis:** Model Y=WC has no intercept → W absorbs shared spatial pattern → β amplifies it. Per-run centering should fix.

**Result:** Per-run centering **commutes with color label shuffle** — `mean(amp[:, perm, :], axis=1) == mean(amp, axis=1)`. Cannot change the permutation test by construction. Confirmed empirically with identical p-values.

### Attempt 2: Re-Optimized Permutation ❌

**Hypothesis:** Fixed (α=0.01, β=100) selected on real data biases the null.

**Result:** Shuffled data selects β=1000 (45% of shuffles!) — even higher regularization. Smoothness helps fit ANY data, not just color signal.

### Attempt 3: RDM-Based Evaluation ❌

**Hypothesis:** RDM inherently removes baseline → would properly measure color geometry.

**Result:** RDM inspection reveals:
- **Actual data has NO ideal circular hue structure** (Spearman vs ideal ≈ 0 in all ROIs)
- smooth_tikh predicted RDM is **anti-correlated** with ideal (ρ ≈ -0.5)
- RDM distances extremely compressed (0.06-0.23 vs actual 0.66-1.49)
- rdm_pearson "improvement" = noise pattern-matching, NOT color geometry preservation

---

## Final Resolution

**smooth_tikh is REJECTED.** The paradox is fully resolved:

**ALL "improvements" were artifacts of spatial covariance capture:**
1. ✅ Higher voxel_corr → capturing shared spatial pattern (high null baseline proves this)
2. ✅ Higher rdm_pearson → compressed RDM matching actual noise structure (anti-correlated with ideal)
3. ✅ Stronger HC-CVD separation → group differences in spatial covariance, not color signal

**Root cause:** β=100 forces near-rank-1 W → predictions dominated by single spatial pattern shared across colors → no color-discriminative content.

---

## Key Insight (FINAL)

**The permutation test correctly identified smooth_tikh as capturing nuisance variance, not color signal.**

**voxel_corr is the correct metric. The permutation test is the correct test. smooth_tikh genuinely fails.**

**Decision: ridge_gcv confirmed as final encoder.**

---

## Completed

1. ✅ Document smooth_tikh permutation results in RESULTS.md
2. ✅ Condition-centering tested → commutes with permutation
3. ✅ Re-optimized permutation tested → null beta stays high
4. ✅ RDM structure inspected → no circular structure, rdm_pearson misleading
5. ✅ **Final decision: ridge_gcv confirmed, smooth_tikh REJECTED**
6. ✅ Updated RESULTS.md, notion.md, PLAN.md
