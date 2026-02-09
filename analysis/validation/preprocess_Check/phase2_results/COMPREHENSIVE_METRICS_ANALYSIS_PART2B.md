# Phase 2 Complete Metrics Analysis - Part 2B: Subject Comparison

---

## sub-02 Analysis

**Data**: 8 measurements (2 ROIs × 4 conditions)

### Overall Performance Across Conditions

| Condition | Avg Method Diff | Avg RDM Reliability | Best ROI | Status |
|-----------|----------------|---------------------|----------|--------|
| P0 | 0.479 | -0.033 | V1 | ❌ Poor |
| P1 | 0.051 | 0.094 | V2 | ✅ Good |
| P2 | 0.435 | -0.147 | V1 | ❌ Poor |
| P3 | 0.047 | 0.056 | V2 | ✅ Excellent |

### sub-02 V1: Condition Effects

| Condition | Method Diff | Random | Odd/Even | RDM Rel | Proc Rel | Interpretation |
|-----------|-------------|--------|----------|---------|----------|----------------|
| P0 | 0.226 | 0.186 | 0.412 | 0.259 | 0.282 | ⚠️ Moderate drift |
| P1 | 0.071 | 0.283 | 0.354 | 0.215 | 0.547 | ✅ Good quality |
| P2 | 0.072 | 0.067 | 0.139 | 0.074 | 0.509 | ⚠️ Moderate drift |
| P3 | 0.056 | 0.203 | 0.259 | 0.149 | 0.654 | ⚠️ Moderate drift |

**P0 → P3 Change:**

- Method Diff: 0.226 → 0.056 (+75.4%)
- RDM Reliability: 0.259 → 0.149 (-0.111)
- Proc Reliability: 0.282 → 0.654 (+0.372)

**Conclusion**: ✅ **Good improvement** - substantial method diff reduction

---

### sub-02 V2: Condition Effects

| Condition | Method Diff | Random | Odd/Even | RDM Rel | Proc Rel | Interpretation |
|-----------|-------------|--------|----------|---------|----------|----------------|
| P0 | 0.731 | -0.234 | -0.966 | -0.326 | 0.169 | ❌ Negative reliability |
| P1 | 0.031 | -0.023 | -0.054 | -0.026 | -0.132 | ❌ Negative reliability |
| P2 | 0.798 | -0.371 | -1.169 | -0.369 | -0.028 | ❌ Negative reliability |
| P3 | 0.038 | -0.037 | -0.075 | -0.036 | -0.032 | ❌ Negative reliability |

**P0 → P3 Change:**

- Method Diff: 0.731 → 0.038 (+94.9%)
- RDM Reliability: -0.326 → -0.036 (+0.290)
- Proc Reliability: 0.169 → -0.032 (-0.201)

**Conclusion**: ✅✅ **Strong improvement** - both method diff and reliability improved

---

## sub-10 Analysis

**Data**: 8 measurements (2 ROIs × 4 conditions)

### Overall Performance Across Conditions

| Condition | Avg Method Diff | Avg RDM Reliability | Best ROI | Status |
|-----------|----------------|---------------------|----------|--------|
| P0 | 0.124 | -0.047 | V1 | ✅ Good |
| P1 | 0.491 | 0.201 | V2 | ❌ Poor |
| P2 | 0.147 | -0.122 | V2 | ✅ Good |
| P3 | 0.347 | 0.104 | V2 | ❌ Poor |

### sub-10 V1: Condition Effects

| Condition | Method Diff | Random | Odd/Even | RDM Rel | Proc Rel | Interpretation |
|-----------|-------------|--------|----------|---------|----------|----------------|
| P0 | 0.006 | -0.305 | -0.311 | -0.135 | 0.412 | ❌ Negative reliability |
| P1 | 0.501 | -0.187 | 0.314 | 0.186 | 0.137 | ❌ High drift |
| P2 | 0.179 | -0.290 | -0.469 | -0.190 | 0.338 | ❌ Negative reliability |
| P3 | 0.351 | -0.244 | 0.107 | 0.056 | 0.210 | ❌ High drift |

**P0 → P3 Change:**

- Method Diff: 0.006 → 0.351 (-5783.9%)
- RDM Reliability: -0.135 → 0.056 (+0.191)
- Proc Reliability: 0.412 → 0.210 (-0.201)

**Conclusion**: ✅ **Measurement quality improved** - reliability increased despite higher method diff

---

### sub-10 V2: Condition Effects

| Condition | Method Diff | Random | Odd/Even | RDM Rel | Proc Rel | Interpretation |
|-----------|-------------|--------|----------|---------|----------|----------------|
| P0 | 0.242 | -0.165 | 0.077 | 0.040 | 0.346 | ⚠️ Moderate drift |
| P1 | 0.481 | -0.125 | 0.356 | 0.217 | 0.567 | ❌ High drift |
| P2 | 0.114 | -0.227 | -0.112 | -0.053 | 0.366 | ❌ Negative reliability |
| P3 | 0.342 | -0.080 | 0.262 | 0.151 | 0.494 | ❌ High drift |

**P0 → P3 Change:**

- Method Diff: 0.242 → 0.342 (-41.5%)
- RDM Reliability: 0.040 → 0.151 (+0.111)
- Proc Reliability: 0.346 → 0.494 (+0.148)

**Conclusion**: ✅ **Measurement quality improved** - reliability increased despite higher method diff

---
