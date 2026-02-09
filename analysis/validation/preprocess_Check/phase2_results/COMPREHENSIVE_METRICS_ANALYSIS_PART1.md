# Phase 2 Complete Metrics Analysis

**Date**: 2026-02-08
**Experiment**: 2×2 Factorial (Motion/Tissue × WM aCompCor) on C010 baseline
**Test Data**: 4 pairs (sub-02, sub-10 × V1, V2) × 4 conditions = 16 measurements

---

## 📊 Metrics Explanation

### **1. Noise Ceiling Method Difference (Raw)**

- **Variable**: `raw_method_diff`
- **Formula**: `|random_split_reliability - oddeven_split_reliability|`
- **Observed Range**: 0.006 to 0.798

**Interpretation**:
  - **Primary metric** for temporal drift detection
  - Measures inconsistency between random and temporally-ordered splits
  - High value = temporal drift inflates reliability estimates
  - Low value = stable, drift-free measurements

**Target**: **< 0.05** (excellent), **< 0.20** (good), **< 0.30** (acceptable)

**Interpretation Guide**:
  - < 0.05: ✅ Excellent - minimal drift
  - 0.05-0.20: ✅ Good - acceptable drift
  - 0.20-0.30: ⚠️ Moderate - some drift present
  - > 0.30: ❌ High - significant drift

---

### **2. Random Split-Half Reliability**

- **Variable**: `raw_random`
- **Formula**: `spearmanr(RDM_half1, RDM_half2)` from random run splits
- **Observed Range**: -0.371 to 0.283

**Interpretation**:
  - RDM consistency across random subsets of runs
  - Averaged over 100 random splits with Spearman-Brown correction
  - Positive = consistent representational structure
  - Negative = no consistent structure (noise or artifacts)

**Target**: **> 0.3** (acceptable), **> 0.5** (good)

**Interpretation Guide**:
  - > 0.5: ✅ Strong reliability
  - 0.3-0.5: ✅ Moderate reliability
  - 0.1-0.3: ⚠️ Weak reliability
  - < 0.0: ❌ Negative (noise/artifacts)

---

### **3. Odd/Even Split-Half Reliability**

- **Variable**: `raw_oddeven`
- **Formula**: `spearmanr(RDM_odd, RDM_even)` from odd [0,2,4] vs even [1,3,5] runs
- **Observed Range**: -1.169 to 0.412

**Interpretation**:
  - Temporally balanced reliability estimate
  - Should match random split if no temporal drift
  - Divergence from random = temporal drift present
  - Diedrichsen et al. (2016) deterministic split method

**Target**: **Similar to random split** (difference < 0.05)

**Interpretation Guide**:
  - |odd-random| < 0.05: ✅ No drift
  - |odd-random| 0.05-0.20: ⚠️ Moderate drift
  - |odd-random| > 0.20: ❌ Strong drift

---

### **4. RDM Reliability (Raw)**

- **Variable**: `raw_rdm_reliability`
- **Formula**: `mean([random, oddeven])` - average of both split methods
- **Observed Range**: -0.369 to 0.259

**Interpretation**:
  - Overall measure of RDM consistency
  - Combines random and odd/even reliability
  - Negative values indicate no consistent structure
  - Used as quality indicator for downstream analyses

**Target**: **> 0.2** (minimum), **> 0.4** (good)

**Interpretation Guide**:
  - > 0.4: ✅ Good reliability
  - 0.2-0.4: ✅ Acceptable
  - 0.0-0.2: ⚠️ Weak
  - < 0.0: ❌ No structure (noise)

---

### **5. Procrustes Method Difference**

- **Variable**: `proc_method_diff`
- **Formula**: `|random - oddeven|` after Procrustes alignment
- **Observed Range**: 0.012 to 0.332

**Interpretation**:
  - Drift remaining after removing geometric differences
  - Procrustes removes rotation, reflection, scaling between runs
  - Lower than raw = geometric drift was present
  - Still high = non-geometric (e.g., amplitude) drift

**Target**: **< 0.10** (good), **< 0.20** (acceptable)

**Interpretation Guide**:
  - proc < raw: ✅ Geometric drift removed
  - proc ≈ raw: ⚠️ Non-geometric drift
  - proc > raw: ❌ Alignment failed

---

### **6. Procrustes RDM Reliability**

- **Variable**: `proc_rdm_reliability`
- **Formula**: RDM reliability after Procrustes alignment
- **Observed Range**: -0.132 to 0.654

**Interpretation**:
  - Structural consistency independent of geometry
  - Higher than raw = geometric noise was present
  - Ceiling for alignment methods (Procrustes, SRM)
  - Indicates potential benefit of geometric alignment

**Target**: **> raw_rdm_reliability** (alignment helps)

**Interpretation Guide**:
  - proc >> raw (+0.3): ✅ Strong alignment benefit
  - proc > raw (+0.1): ✅ Moderate benefit
  - proc ≈ raw: ⚠️ Limited benefit
  - proc < raw: ❌ Alignment harmful

---

### **7. Temporal Autocorrelation (lag-1)**

- **Variable**: `temporal_autocorr`
- **Formula**: `mean(corr(run_i, run_i+1))` across consecutive runs
- **Observed Range**: -0.210 to -0.185

**Interpretation**:
  - Correlation between consecutive run patterns
  - Negative = opposite patterns across time (drift)
  - Close to zero = independent runs (ideal)
  - Positive = similar patterns (good or drift)

**Target**: **Close to 0** (independent runs)

**Interpretation Guide**:
  - -0.1 to +0.1: ✅ Independent runs
  - < -0.2: ❌ Strong drift (opposite patterns)
  - > +0.3: ⚠️ Strong correlation (check drift)

---

### **8. Linear Drift Magnitude**

- **Variable**: `drift_magnitude`
- **Formula**: `mean(|slope|)` of linear fit across runs per voxel
- **Observed Range**: 0.0025 to 0.0028

**Interpretation**:
  - Average strength of linear trend per voxel
  - Measures systematic increase/decrease over time
  - Higher = stronger temporal drift
  - Independent of drift direction (absolute value)

**Target**: **< 0.003** (low drift)

**Interpretation Guide**:
  - < 0.002: ✅ Minimal drift
  - 0.002-0.003: ✅ Acceptable
  - > 0.003: ⚠️ Noticeable drift

---

### **9. Procrustes Disparity**

- **Variable**: `procrustes_disparity`
- **Formula**: `sum((X_aligned - Y)^2)` - sum of squared residuals
- **Observed Range**: 0.0024 to 0.0033

**Interpretation**:
  - Geometric dissimilarity between run patterns
  - Lower = more similar geometry across runs
  - High disparity = unstable geometry
  - Quality indicator for alignment success

**Target**: **< 0.003** (stable geometry)

**Interpretation Guide**:
  - < 0.0025: ✅ Stable geometry
  - 0.0025-0.0035: ✅ Acceptable
  - > 0.0035: ⚠️ Unstable geometry

---
