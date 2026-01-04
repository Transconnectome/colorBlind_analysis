# Robustness Validation Methods - Cross-Pipeline Analysis

**Date**: 2025-12-19
**Purpose**: Comprehensive documentation of robustness validation methodology across different preprocessing pipelines

---

## Table of Contents

1. [Overview](#1-overview)
2. [Validation Design](#2-validation-design)
3. [Procrustes Analysis](#3-procrustes-analysis)
4. [RDM Similarity](#4-rdm-similarity)
5. [Statistical Tests](#5-statistical-tests)
6. [Phase 1 Three Findings Validation](#6-phase-1-three-findings-validation)
7. [Interpretation Guidelines](#7-interpretation-guidelines)
8. [Implementation](#8-implementation)

---

## 1. Overview

### 1.1 Research Question

**Does voxel selection (32% vs 81% highest variance) affect**:
1. Procrustes disparity between CVD and HC?
2. Filter learning effectiveness?
3. Conclusions about CVD-HC differences?

### 1.2 Motivation

**Problem identified**:
- Phase 1 (baseline81): Procrustes disparity ~0.30
- Phase 2A (baseline32): Procrustes disparity ~1.0
- **Are these different phenomena or same effect with different scales?**

**Critical finding**:
- Different voxel selections yield different **absolute disparity values**
- BUT: Do **relative patterns** (HC consistency, CVD differences, filter effectiveness) remain robust?

### 1.3 Validation Strategy

**2×2 Cross-validation**:

|  | Phase 1 (Characterization) | Phase 2A (Filter Learning) |
|--|----------------------------|----------------------------|
| **baseline32** | ✅ Completed | ✅ Completed (original) |
| **baseline81** | ✅ Completed (original) | ⏳ In progress |

**Goal**: Show that **biological conclusions** are robust even when **numerical values** differ

---

## 2. Validation Design

### 2.1 Preprocessing Pipelines

**baseline32_deob_determin**:
- Voxel selection: Top 32% highest temporal variance
- V1: 356 voxels (aligned to 238-356 range)
- V2: 172 voxels (aligned to 172-185 range)
- Characteristic: **High variability**, captures individual differences

**baseline81_deob_determin**:
- Voxel selection: Top 81% highest temporal variance
- V1: 429 voxels (all subjects aligned)
- V2: 279 voxels (aligned to 233-279 range)
- Characteristic: **More stable**, includes shared patterns

**Common preprocessing**:
- Deoblique correction applied
- Deterministic (canonical) HRF
- 6 runs per subject
- Same ROI definitions (V1, V2 from atlas)

### 2.2 Cross-Validation Matrix

**Phase 1 (Characterization)**:
- **Original**: baseline81 → Disparity ~0.30
- **Validation**: baseline32 → Disparity ~1.0
- **Test**: Do THREE key findings hold?

**Phase 2A (Filter Learning)**:
- **Original**: baseline32 → Before ~1.0, After ~0.02
- **Validation**: baseline81 → Before ~0.30, After ~? (pending)
- **Test**: Does filter reduce disparity by similar percentage?

### 2.3 Comparison Metrics

| Metric | Purpose | Expected Result |
|--------|---------|-----------------|
| **Procrustes Disparity** | Quantify pattern difference | Scales with voxel selection, but relative patterns preserved |
| **RDM Similarity** | Measure structure preservation | Invariant to voxel selection (correlation-based) |
| **CVD/HC Ratio** | Relative difference magnitude | Consistent across pipelines (~3-4×) |
| **Filter Reduction %** | Effectiveness measure | Similar percentage (95-99%) regardless of initial disparity |

---

## 3. Procrustes Analysis

### 3.1 Ordinary Procrustes (Used Throughout)

**Definition**: Translation + Rotation (NO scaling)

**Algorithm**:
```python
def ordinary_procrustes(X, Y):
    """
    Align Y to X using translation + rotation only

    Args:
        X, Y: (n_points, n_dims) arrays

    Returns:
        disparity: normalized Frobenius norm
        Y_aligned: transformed Y
    """
    # Step 1: Center (remove translation)
    X_centered = X - X.mean(axis=0, keepdims=True)
    Y_centered = Y - Y.mean(axis=0, keepdims=True)

    # Step 2: Find optimal rotation
    M = Y_centered.T @ X_centered
    U, S, Vt = np.linalg.svd(M)
    R = U @ Vt  # Rotation matrix

    # Step 3: Apply transformation
    Y_aligned = Y_centered @ R + X.mean(axis=0, keepdims=True)

    # Step 4: Compute disparity
    disparity = np.linalg.norm(X - Y_aligned, ord='fro') / np.linalg.norm(X, ord='fro')

    return disparity, Y_aligned
```

**For fMRI patterns**:
- X, Y: (8, n_voxels) - 8 colors × n voxels
- Procrustes aligns in **8-dimensional color space**
- Each voxel is a dimension
- Colors are points in this space

**Disparity formula**:
```
disparity = ||X - Y_aligned||_F / ||X||_F
```

Where:
- ||·||_F: Frobenius norm
- Normalized by ||X||_F for scale-invariance
- Range: [0, ∞), typically [0, 2]

### 3.2 Why NOT scipy.spatial.procrustes()

**scipy includes scaling**:
```python
# scipy.spatial.procrustes ADDS scaling step
Y_aligned = (Y_centered @ R) * s + X.mean()  # s = scaling factor
```

**Problems with scaling**:
1. **Different disparity definition**: Uses trace(M) instead of Frobenius norm
2. **Scaling confounds magnitude differences**: Can artificially reduce disparity
3. **Inconsistent with Phase 1**: Original analysis used Ordinary Procrustes

**Comparison** (baseline32, sub-08 V1):
- Ordinary Procrustes: disparity = 0.938
- scipy (with scaling): disparity = 0.028
- **33× difference!**

### 3.3 Interpretation

**Disparity ranges**:

| Range | Interpretation |
|-------|----------------|
| 0.00 - 0.10 | Excellent match (filter after) |
| 0.10 - 0.30 | Good match (baseline81 CVD-HC) |
| 0.30 - 0.50 | Moderate difference |
| 0.50 - 1.00 | Large difference (baseline32 CVD-HC) |
| > 1.00 | Very large difference |

**Factors affecting disparity**:
1. **Voxel selection**: 32% → higher disparity, 81% → lower disparity
2. **Number of voxels**: More voxels → more degrees of freedom → higher potential disparity
3. **Signal-to-noise**: High-variance voxels → more individual variability

---

## 4. RDM Similarity

### 4.1 Computation

**Representational Dissimilarity Matrix (RDM)**:

```python
def compute_rdm(pattern):
    """
    pattern: (8, n_voxels)
    returns: (8, 8) symmetric dissimilarity matrix
    """
    from scipy.stats import spearmanr

    n_colors = 8
    rdm = np.zeros((n_colors, n_colors))

    for i in range(n_colors):
        for j in range(n_colors):
            if i != j:
                corr, _ = spearmanr(pattern[i], pattern[j])
                rdm[i, j] = 1 - corr
            else:
                rdm[i, j] = 0  # Self-dissimilarity = 0

    return rdm
```

**RDM Similarity** (between two patterns):

```python
def rdm_similarity(pattern1, pattern2):
    """
    Spearman correlation between upper triangles of RDMs
    """
    rdm1 = compute_rdm(pattern1)
    rdm2 = compute_rdm(pattern2)

    # Extract upper triangle (excluding diagonal)
    triu_idx = np.triu_indices(8, k=1)
    rdm1_vec = rdm1[triu_idx]
    rdm2_vec = rdm2[triu_idx]

    # Spearman correlation
    similarity, pval = spearmanr(rdm1_vec, rdm2_vec)

    return similarity, pval
```

### 4.2 Properties

**Magnitude-invariant**:
- Based on **Spearman correlation** (rank-based)
- Insensitive to scaling or additive shifts
- Captures **relative dissimilarity structure**

**Example**:
```
Pattern A: [1, 2, 3, 4]
Pattern B: [10, 20, 30, 40]  (10× scaling)

Spearman(A, B) = 1.0  (perfect correlation)
RDM(A, B) = 0  (perfect similarity)
```

**Interpretation**:

| RDM Similarity | Interpretation |
|----------------|----------------|
| 0.99 - 1.00 | Nearly identical structure (filter after) |
| 0.50 - 0.70 | Moderate similarity |
| 0.10 - 0.30 | Low similarity (baseline32 CVD-HC) |
| -0.30 - 0.10 | Very low or negative (severe distortion) |

### 4.3 Why Spearman (not Pearson)?

**Spearman advantages**:
1. **Rank-based**: Robust to outliers
2. **Non-parametric**: No distributional assumptions
3. **Magnitude-invariant**: 1-correlation is dissimilarity metric

**Example where Pearson fails**:
```
Color pair A: corr = 0.9
Color pair B: corr = 0.3

RDM[A] = 1 - 0.9 = 0.1 (similar)
RDM[B] = 1 - 0.3 = 0.7 (dissimilar)

Ranking preserved even if correlations scale differently
```

---

## 5. Statistical Tests

### 5.1 CVD Average Cancellation Test

**Hypothesis**:
- H0: CVD average pattern has no significant difference from HC
- H1: CVD average pattern differs from HC

**Method**: One-sample t-test on per-color L2 differences

```python
def test_cvd_average_cancellation(hc_mean, cvd_average):
    """
    Test if CVD average differs significantly from HC

    Returns:
        t_stat: t-statistic
        p_value: two-tailed p-value
    """
    # Per-color L2 norms
    l2_hc = np.linalg.norm(hc_mean, axis=1)      # (8,)
    l2_cvd_avg = np.linalg.norm(cvd_average, axis=1)  # (8,)

    # Differences
    l2_diffs = l2_cvd_avg - l2_hc  # (8,)

    # One-sample t-test (H0: mean difference = 0)
    from scipy.stats import ttest_1samp
    t_stat, p_value = ttest_1samp(l2_diffs, 0)

    return t_stat, p_value
```

**Interpretation**:
- **p > 0.05**: No significant difference → Cancellation effect confirmed
- **p < 0.05**: Significant difference → Cancellation incomplete

**Critical finding** (baseline comparison):
- baseline81: p = 0.095 (V1), 0.229 (V2) → Cancellation confirmed
- baseline32: p = 0.035 (V1), 0.007 (V2) → Cancellation incomplete
- **Voxel selection affects cancellation strength!**

### 5.2 HC-HC Consistency (Descriptive)

**No hypothesis test needed** - just report disparity statistics:

```python
# Pairwise Procrustes for all HC pairs
from itertools import combinations

hc_subjects = ['03', '05', '06', '07']
hc_pairs = list(combinations(hc_subjects, 2))  # 6 pairs

disparities = []
for subj1, subj2 in hc_pairs:
    disp, _ = ordinary_procrustes(
        hc_patterns[subj1],
        hc_patterns[subj2]
    )
    disparities.append(disp)

# Report mean ± SD
mean_disp = np.mean(disparities)
std_disp = np.std(disparities, ddof=1)

print(f"HC-HC consistency: {mean_disp:.3f} ± {std_disp:.3f} (n={len(disparities)})")
```

**Expected**:
- Low mean (< 0.3)
- Low variance (tight clustering)
- Demonstrates HC group homogeneity

---

## 6. Phase 1 Three Findings Validation

### 6.1 Finding 1: HC-HC Consistency

**Original (baseline81)**:
- V1: 0.089 ± 0.041
- V2: 0.119 ± 0.046
- **Interpretation**: HC subjects show consistent color representations

**Validation (baseline32)**:
- V1: 0.222 ± 0.038
- V2: 0.251 ± 0.039
- **Ratio**: 2.5× higher (expected due to higher variance voxels)

**Conclusion**:
- ✅ **Validated**: HC consistency maintained across pipelines
- Absolute values differ (scale effect)
- Relative homogeneity preserved (low SD/mean ratio)

### 6.2 Finding 2: CVD Individual-HC Differences

**Original (baseline81)**:
- V1: 0.304 ± 0.027
- V2: 0.298 ± 0.041
- **Interpretation**: CVD individuals differ from HC

**Validation (baseline32)**:
- V1: 1.013 ± 0.029
- V2: 1.063 ± 0.021
- **Ratio**: 3.3-3.6× higher

**Relative comparison** (CVD-HC / HC-HC):

| Pipeline | V1 Ratio | V2 Ratio |
|----------|----------|----------|
| baseline81 | 0.304 / 0.089 = **3.42×** | 0.298 / 0.119 = **2.50×** |
| baseline32 | 1.013 / 0.222 = **4.57×** | 1.063 / 0.251 = **4.23×** |

**Conclusion**:
- ✅ **Validated**: CVD individuals show 2.5-4.6× higher disparity than HC-HC
- Relative pattern preserved (CVD >> HC)
- Absolute values scale with voxel selection

### 6.3 Finding 3: CVD Average Cancellation ⚠️ CRITICAL DIFFERENCE

**Original (baseline81)**:
- V1: disparity = 0.121, p = 0.095 (ns)
- V2: disparity = 0.136, p = 0.229 (ns)
- **Interpretation**: Averaging cancels individual distortions

**Validation (baseline32)**:
- V1: disparity = 0.248, p = **0.035** ⚠️
- V2: disparity = 0.244, p = **0.007** ⚠️
- **Interpretation**: Averaging REDUCES disparity (75-77%) but residual remains significant

**Disparity reduction**:

| Pipeline | V1 Reduction | V2 Reduction |
|----------|--------------|--------------|
| baseline81 | 0.304 → 0.121 (**60%**) | 0.298 → 0.136 (**54%**) |
| baseline32 | 1.013 → 0.248 (**75%**) | 1.063 → 0.244 (**77%**) |

**Critical insight**:
- **Both pipelines show substantial reduction** when averaging
- **But statistical significance differs**:
  - baseline81: Residual is non-significant (complete cancellation)
  - baseline32: Residual remains significant (incomplete cancellation)

**Possible explanations**:
1. **Voxel subset sensitivity**: 32% captures more idiosyncratic variability
2. **Systematic vs random distortions**: Averaging cancels random, but systematic component persists
3. **Sample size (n=3)**: Small sample may not fully cancel all distortions

**Revised interpretation**:
- ✅ "CVD averaging **substantially reduces** disparity (60-77%)"
- ⚠️ "**Complete cancellation** depends on voxel selection"
- ⚠️ "Systematic distortions may persist in high-variance voxels"

---

## 7. Interpretation Guidelines

### 7.1 When Results Are Robust

**Criteria for robustness**:
1. ✅ **Relative patterns preserved**: CVD-HC ratio similar across pipelines
2. ✅ **Directional consistency**: Same group shows higher/lower disparity
3. ✅ **Biological conclusion unchanged**: CVD differs from HC in both pipelines

**Example (Finding 2)**:
- baseline81: CVD 3.4× higher disparity than HC-HC
- baseline32: CVD 4.6× higher disparity than HC-HC
- **Conclusion**: CVD-HC difference is **robust** (both show clear separation)

### 7.2 When Results Differ (Finding 3)

**When to report difference**:
1. ⚠️ **Statistical significance flips**: p > 0.05 → p < 0.05
2. ⚠️ **Effect size changes qualitatively**: 60% → 75% reduction (moderate difference)
3. ⚠️ **Interpretation requires nuance**: "Complete" vs "Substantial" cancellation

**Reporting strategy**:
1. **Report both findings**: baseline81 (original), baseline32 (validation)
2. **Explain scale effect**: Voxel selection affects absolute values
3. **Highlight agreement**: Both show substantial reduction
4. **Note disagreement**: Statistical significance differs
5. **Provide mechanistic explanation**: High-variance voxels → more systematic distortion

**Example reporting**:
> "CVD averaging substantially reduces disparity by 60-77% across pipelines. In baseline81 (81% voxels), the residual difference is non-significant (p > 0.05), suggesting nearly complete cancellation of individual distortions. However, in baseline32 (32% highest-variance voxels), the residual remains significant (p < 0.05), indicating that systematic distortions may persist in high-variability voxels. This suggests the cancellation effect is **partial** rather than **complete**, with strength modulated by voxel selection criteria."

### 7.3 Voxel Selection Effects

**General principle**:
- **32% (high variance)**: Captures individual differences, higher disparity
- **81% (broader selection)**: Includes stable shared patterns, lower disparity

**Analogy**:
- 32%: "Zoom in" to individual-specific signals
- 81%: "Zoom out" to population-average patterns

**Recommendation**:
- **For characterization**: Use multiple selections to test robustness
- **For filter learning**: Optimize for specific selection, then validate on other
- **For interpretation**: Focus on relative patterns, not absolute values

---

## 8. Implementation

### 8.1 Validation Scripts

**Phase 1 baseline32 validation**:
```
analysis/group_level/phase1_baseline32_validation.py       # CVD-HC disparity
analysis/group_level/phase1_baseline32_full_validation.py  # All three findings
```

**Outputs**:
```
results/group_level/phase1_baseline32_validation/
├── hc_hc_consistency.csv         # Finding 1
├── cvd_individual_differences.csv # Finding 2
├── cvd_average_analysis.csv      # Finding 3
├── procrustes_results.csv
└── rdm_comparison.csv
```

### 8.2 Key Functions

**Ordinary Procrustes**:
```python
def ordinary_procrustes(X, Y):
    """Compute disparity without scaling"""
    X_centered = X - X.mean(axis=0, keepdims=True)
    Y_centered = Y - Y.mean(axis=0, keepdims=True)
    M = Y_centered.T @ X_centered
    U, S, Vt = np.linalg.svd(M)
    R = U @ Vt
    Y_aligned = Y_centered @ R + X.mean(axis=0, keepdims=True)
    disparity = np.linalg.norm(X - Y_aligned, ord='fro') / np.linalg.norm(X, ord='fro')
    return disparity, Y_aligned
```

**RDM Similarity**:
```python
def compute_rdm_similarity(pattern1, pattern2):
    """Spearman correlation between RDMs"""
    rdm1 = compute_rdm(pattern1)
    rdm2 = compute_rdm(pattern2)
    triu_idx = np.triu_indices(8, k=1)
    similarity, pval = spearmanr(rdm1[triu_idx], rdm2[triu_idx])
    return similarity, pval
```

**CVD Average Test**:
```python
def test_cvd_average(hc_mean, cvd_patterns):
    """One-sample t-test for cancellation effect"""
    cvd_average = np.mean(cvd_patterns, axis=0)
    l2_hc = np.linalg.norm(hc_mean, axis=1)
    l2_cvd_avg = np.linalg.norm(cvd_average, axis=1)
    l2_diffs = l2_cvd_avg - l2_hc
    t_stat, p_value = ttest_1samp(l2_diffs, 0)
    return t_stat, p_value, cvd_average
```

### 8.3 Execution Example

```bash
# Full validation (all three findings)
python analysis/group_level/phase1_baseline32_full_validation.py

# Output:
# Finding 1: HC-HC consistency (6 pairwise comparisons)
# Finding 2: CVD individual-HC (3 CVD subjects)
# Finding 3: CVD average cancellation (t-test)
# Comparison with Phase 2A "Before Filtering"
```

---

## Appendix: Troubleshooting

### A.1 Common Issues

**Issue**: Disparity values don't match between scripts

**Causes**:
1. Using `scipy.spatial.procrustes()` (includes scaling)
2. Wrong normalization (||X - Y|| instead of ||X - Y|| / ||X||)
3. Different centering (row-wise vs column-wise)

**Solution**: Always use `ordinary_procrustes()` function from validation scripts

---

**Issue**: RDM similarity is negative

**Causes**:
1. Severe pattern distortion (rank-order reversed)
2. Noise dominates signal
3. Incorrect RDM computation (Pearson instead of Spearman)

**Solution**:
- Check data quality (SNR, preprocessing)
- Verify Spearman correlation usage
- Negative RDM similarity is valid (indicates anti-correlation)

---

**Issue**: CVD average test shows opposite result

**Causes**:
1. Different voxel alignments
2. Outlier subject (e.g., sub-08 has high structure distortion)
3. Small sample size (n=3) → p-value sensitive to single subject

**Solution**:
- Report both pipelines
- Check per-subject contributions
- Use effect size (disparity reduction %) in addition to p-value

---

## Appendix: Comparison Matrix (Final)

### Procrustes Disparity

|  | Phase 1 baseline81 | Phase 1 baseline32 | Phase 2A Before (baseline32) | Phase 2A After (baseline32) |
|--|--------------------|--------------------|------------------------------|------------------------------|
| **sub-08 V1** | 0.294 | 0.973 | 0.938 | 0.012 |
| **sub-09 V1** | 0.342 | 1.026 | 1.026 | 0.031 |
| **sub-10 V1** | 0.277 | 1.041 | 1.015 | 0.010 |
| **sub-08 V2** | 0.359 | 1.072 | 1.072 | 0.048 |
| **sub-09 V2** | 0.262 | 1.034 | 1.039 | 0.040 |
| **sub-10 V2** | 0.273 | 1.084 | 1.100 | 0.037 |

**Observations**:
- ✅ Phase 1 (baseline32) matches Phase 2A Before
- ✅ 3.3-3.6× scaling from baseline81 to baseline32
- ✅ Phase 2A After shows 95-99% reduction (robust filter effect)

---

**Document version**: 1.0
**Last updated**: 2025-12-19
**Author**: Robustness Validation Analysis Pipeline
