# Comprehensive Analysis: 4 Test Subjects (01-04)

Analysis Date: 2025-11-13

---

## 1. Temporal Dynamics: Optimal Delay Consistency

### Optimal Delay (TRs) by ROI and Subject

| ROI | sub-01 | sub-02 | sub-03 | sub-04 | Mean±SD | CV (%) | Consistency |
|-----|--------|--------|--------|--------|---------|--------|-------------|
| V1 | - | - | - | - | 4.0±1.2 | 28.9% | ★☆☆ |
| V2 | - | - | - | - | 2.0±0.8 | 40.8% | ★★☆ |
| V3 | - | - | - | - | 2.8±1.0 | 34.8% | ★★☆ |
| hV4 | - | - | - | - | 3.0±1.6 | 54.4% | ☆☆☆ |

### Optimal Delay (seconds, TR=1.5s)

| ROI | Mean±SD (s) | Range (s) |
|-----|-------------|----------|
| V1 | 6.00±1.73 | 4.5-7.5 |
| V2 | 3.00±1.22 | 1.5-4.5 |
| V3 | 4.12±1.44 | 3.0-6.0 |
| hV4 | 4.50±2.45 | 1.5-7.5 |

### Hierarchical Pattern

ROI order by mean delay (early → late):

- **V2**: 2.0 TRs (3.0s)
- **V3**: 2.8 TRs (4.1s)
- **hV4**: 3.0 TRs (4.5s)
- **V1**: 4.0 TRs (6.0s)

✗ **Deviates from expected hierarchy**

- Expected: V1 → V2 → V3 → hV4
- Observed: V2 → V3 → hV4 → V1

---

## 2. PCA Optimization

### Components Required for 90% Variance

| ROI | sub-01 | sub-02 | sub-03 | sub-04 | Mean±SD | Consistency |
|-----|--------|--------|--------|--------|---------|-------------|
| V1 | 6 | 7 | 7 | 6 | 6.5±0.58 | ⚠ Variable |
| V2 | 6 | 7 | 6 | 6 | 6.2±0.50 | ⚠ Variable |
| V3 | 6 | 6 | 6 | 6 | 6.0±0.00 | ✓ Perfect |
| hV4 | 6 | 6 | 6 | 6 | 6.0±0.00 | ✓ Perfect |

**Overall**: 6.2±0.40 components (range: 6-7)

### Explained Variance by ROI

| ROI | N Subjects | Mean Expl. Var. | Range |
|-----|------------|-----------------|-------|
| V1 | 4 | 100.0% ± 0.0% | 100.0% - 100.0% |
| V2 | 4 | 100.0% ± 0.0% | 100.0% - 100.0% |
| V3 | 4 | 100.0% ± 0.0% | 100.0% - 100.0% |
| hV4 | 4 | 100.0% ± 0.0% | 100.0% - 100.0% |

✓ **PCA components sufficient** (≥90% variance explained with current PCA-20)

### PCA Efficiency Analysis

**Current setting**: 20 components (100% variance)
**Required for 90% variance**: 6.2 components

**Overspecification**: 3.2× (223% excess)

**Sample:Feature Ratio with 40 training samples**:

| Method | Features | Sample:Feature | Assessment |
|--------|----------|---------------|------------|
| PCA-20 (current) | 20 | 2.0:1 | ⚠ Borderline (overfitting risk) |
| PCA-7 (recommended) | 7 | 5.7:1 | ✓ Acceptable |
| PCA-6 (most common) | 6 | 6.7:1 | ✓ Safe |
| PCA-3 (validation test) | 3 | 13.3:1 | ✓ Very safe |

**Key Finding**: ✅ PCA-6 finding from sub-01 **generalizes to other subjects**
- **81% of cases** (13/16) need only 6 components
- **100% of cases** need ≤7 components
- V3 and hV4 show perfect consistency (all subjects = 6)
- V1 and V2 show slight variability (6-7 components)

**Recommendation**: Switch to **PCA-7** (covers all subjects) or **PCA-6** (covers 81%)

---

## 3. Z-Score Statistics: ROI Consistency

### Voxel Selectivity (|z| > 2.3, p < 0.01)

| ROI | N Subjects | % Selective Voxels | Consistency |
|-----|------------|-------------------|-------------|
| V1 | 4 | 15.5% ± 2.8% (11.6-18.2%) | ★★☆ |
| V2 | 4 | 14.7% ± 6.7% (7.7-23.8%) | ★☆☆ |
| V3 | 4 | 18.7% ± 8.9% (12.6-31.7%) | ★☆☆ |
| hV4 | 4 | 22.2% ± 5.4% (15.5-27.5%) | ★★☆ |

### Hierarchical Pattern (Selectivity)

ROI order by selectivity (high → low):

- **hV4**: 22.2% selective voxels
- **V3**: 18.7% selective voxels
- **V1**: 15.5% selective voxels
- **V2**: 14.7% selective voxels

⚠ **Unexpected pattern** (late visual area most selective)

---

## 4. Performance Summary

### Classification Accuracy

| ROI | Mean | Perfect (n/4) |
|-----|------|---------------|
| V1 | 100.0% | 4/4 |
| V2 | 100.0% | 4/4 |
| V3 | 100.0% | 4/4 |
| hV4 | 100.0% | 4/4 |

### Reconstruction Error (degrees)

| ROI | Mean±SD | Range | Best Subject |
|-----|---------|-------|-------------|
| V1 | 1.97° ± 1.72° | 0.88° - 4.50° | sub-1 |
| V2 | 1.97° ± 1.06° | 1.25° - 3.50° | sub-2 |
| V3 | 1.84° ± 0.21° | 1.62° - 2.12° | sub-4 |
| hV4 | 3.41° ± 0.57° | 2.75° - 4.00° | sub-2 |

### Novel Color Error (degrees)

| ROI | Mean±SD | Range | Best Subject |
|-----|---------|-------|-------------|
| V1 | 83.16° ± 19.37° | 55.00° - 99.25° | sub-1 |
| V2 | 82.19° ± 24.39° | 58.62° - 116.00° | sub-3 |
| V3 | 78.22° ± 31.31° | 49.88° - 122.62° | sub-2 |
| hV4 | 89.44° ± 23.03° | 65.75° - 109.62° | sub-2 |

---

## Key Findings

### 1. Temporal Dynamics

- ⚠ **Variable HRF timing** across subjects (CV: 28-54%)
- ⚠ **Unexpected hierarchy**: V2 earliest (3.0s), V1 latest (6.0s)

### 2. PCA Optimization (Critical Discovery)

- ✅ **PCA-6 finding from sub-01 generalizes**: 81% of cases need only 6 components for 90% variance
- ⚠ **Current PCA-20 is 3.2× overspecified** (223% excess)
- ⚠ **Poor sample:feature ratio**: 2.0:1 with PCA-20 (overfitting risk)
- ✓ **Recommended**: Switch to PCA-7 (5.7:1 ratio) or PCA-6 (6.7:1 ratio)
- **Perfect consistency**: V3 and hV4 always need 6 components
- **Slight variability**: V1 and V2 need 6-7 components

### 3. Classification Performance

- ✓ **Excellent classification** (100% of ROI×Subject combinations achieve 100%)
- ⚠ **Likely overfitting** given poor sample:feature ratio

### 4. Reconstruction Accuracy

- **Best ROI**: V3 (1.84° mean error)
- ✓ **Excellent reconstruction** (<5° error for trained colors)
- ❌ **Poor generalization**: 78-89° error for novel colors (near chance level of 90°)

