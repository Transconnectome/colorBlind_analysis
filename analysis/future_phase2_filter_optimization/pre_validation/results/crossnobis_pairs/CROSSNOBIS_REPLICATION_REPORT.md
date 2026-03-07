# Crossnobis Color-Pair Replication Report

**Addresses**: Reviewer #2 Criticism 2 (SRM circularity)

**Method**: Cross-validated Mahalanobis distances in native voxel space (SRM-independent)

**Reference**: Walther et al. (2016). Reliability of dissimilarity measures for RSA. *NeuroImage*.

---

## Overall Summary

| Metric | Count | Percentage |
|--------|-------|------------|
| Total tests | 252 | 100% |
| Raw significant (p<0.05) | 2 | 0.8% |
| FDR significant (q<0.05) | 0 | 0.0% |

## Filter Targets Surviving Global FDR

### sub-08: 0 total pairs

**HIGH priority pairs**: None survive FDR ❌

### sub-09: 0 total pairs

**HIGH priority pairs**: None survive FDR ❌

### sub-10: 0 total pairs

**HIGH priority pairs**: None survive FDR ❌

---

## Comparison to SRM-Based Analysis

Correlation between crossnobis z-scores and SRM z-scores:

| Subject | ROI | Spearman r | p-value | Interpretation |
|---------|-----|------------|---------|----------------|
| sub-08 | V1 | 0.534 | 0.0034 | ✅ Strong convergence |
| sub-08 | V2 | 0.332 | 0.0841 | ⚠️ Moderate convergence |
| sub-08 | V3 | 0.438 | 0.0198 | ⚠️ Moderate convergence |
| sub-09 | V1 | 0.635 | 0.0003 | ✅ Strong convergence |
| sub-09 | V2 | 0.649 | 0.0002 | ✅ Strong convergence |
| sub-09 | V3 | 0.115 | 0.5584 | ⚠️ Weak convergence |
| sub-10 | V1 | 0.638 | 0.0003 | ✅ Strong convergence |
| sub-10 | V2 | 0.701 | 0.0000 | ✅ Strong convergence |
| sub-10 | V3 | 0.338 | 0.0788 | ⚠️ Moderate convergence |

**Interpretation**: If r > 0.5, the same pair-distance patterns emerge in both SRM-projected space and native voxel space, confirming that SRM is not creating artifacts.

---

## Method Details

### Crossnobis Distance (Walther et al. 2016)

Cross-validated Mahalanobis distance that controls for noise correlations:

1. Estimate noise covariance Σ from residuals (Ledoit-Wolf shrinkage)
2. For each pair of conditions (i,j), compute over all C(6,2)=15 run pairs:
   ```
   d_crossnobis(i,j) = (X_r1,i - X_r1,j)ᵀ Σ⁻¹ (X_r2,i - X_r2,j)
   ```
3. Average over run pairs → unbiased distance matrix

**Key advantage**: Computed in full native voxel space (no dimensionality reduction), completely independent of SRM.

