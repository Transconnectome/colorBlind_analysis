# PCA Component Analysis Across 4 Test Subjects

**Analysis Date**: 2025-11-13

**Question**: Can we reduce PCA components from 20 to ~6 (as found in sub-01)?

---

## Components Required for 90% Variance

| ROI | sub-01 | sub-02 | sub-03 | sub-04 | Mean±SD | Consistency |
|-----|--------|--------|--------|--------|---------|-------------|
| V1 | 6 | 7 | 7 | 6 | 6.5±0.58 | ⚠ Variable |
| V2 | 6 | 7 | 6 | 6 | 6.2±0.50 | ⚠ Variable |
| V3 | 6 | 6 | 6 | 6 | 6.0±0.00 | ✓ Perfect |
| hV4 | 6 | 6 | 6 | 6 | 6.0±0.00 | ✓ Perfect |

## Overall Statistics

- **Mean**: 6.2 components
- **Range**: 6 - 7 components
- **Most common**: 6 components (81% of cases)

## Key Findings

### 1. Consistency Across Subjects

✓ **Excellent consistency** across subjects

**ROI-wise consistency**:

- **V1**: ⚠ Variable (6-7 components)
- **V2**: ⚠ Variable (6-7 components)
- **V3**: ✓ Perfect (all subjects need 6 components)
- **hV4**: ✓ Perfect (all subjects need 6 components)

### 2. Comparison with Current PCA-20

- **Current setting**: 20 components
- **Required for 90% variance**: 6.2 components
- **Overspecification**: 3.2× (using 223% more than needed)

### 3. Sample:Feature Ratio Improvement

With 40 training samples:

| Method | Features | Sample:Feature Ratio | Assessment |
|--------|----------|---------------------|------------|
| PCA-20 (current) | 20 | 2.0:1 | ⚠ Borderline (risk of overfitting) |
| PCA-7 (recommended) | 7 | 5.7:1 | ✓ Acceptable |
| PCA-6 (sub-01 finding) | 6 | 6.7:1 | ✓ Safe |
| PCA-3 (test) | 3 | 13.3:1 | ✓ Very safe |

**Recommendation**: Using 6-7 components would:
- ✓ Capture 90% of variance
- ✓ Improve sample:feature ratio from 2:1 to 5.7-6.7:1
- ✓ Reduce overfitting risk
- ✓ Maintain performance (based on sub-01 results)

## Recommendations

### Conservative Approach (Recommended)

**Use PCA-7** (maximum observed across all subjects)

- Covers all ROI×Subject combinations
- Captures ≥90% variance for all cases
- Still 3× more efficient than PCA-20
- Lower overfitting risk

### Aggressive Approach (For Testing)

**Use PCA-6** (most common value)

- Covers 81% of cases
- Maximal efficiency
- May need subject-specific adjustment for V1/V2 in some subjects

### Validation Test (Critical)

**Run PCA-3 test** to validate overfitting hypothesis

```bash
# If PCA-3 maintains >85% accuracy:
# → Signal is robust, current 100% is real
# → PCA-6 or PCA-7 is safe

# If PCA-3 drops to <70% accuracy:
# → PCA-20 is overfitting
# → Should use PCA-6 or PCA-7
```

## Subject-Specific Notes

### sub-01
- ✓ **Perfect consistency**: All ROIs need exactly 6 components

### sub-02
- ⚠ **V1, V2 need 7 components** (vs 6 for V3, hV4)
- Suggests slightly more complex signal structure in early visual areas

### sub-03
- ⚠ **V1 needs 7 components** (vs 6 for others)
- Similar pattern to sub-02

### sub-04
- ✓ **Perfect consistency**: All ROIs need exactly 6 components

---

## Conclusion

✅ **YES, the PCA-6 finding from sub-01 generalizes well to other subjects!**

- **81% of cases** can use 6 components
- **100% of cases** can use ≤7 components
- Current PCA-20 is likely **overspecified by 3×**

**Recommended action**: Switch to **PCA-7** (covers all cases) or **PCA-6** (covers most)

**Critical test**: Run PCA-3 validation to confirm signal robustness
