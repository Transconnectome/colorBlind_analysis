# Phase 2 Complete Metrics Analysis - Part 2: Data Comparison

---

## 📈 Part A: Condition Comparison (P0, P1, P2, P3)

### P0: C010 baseline (no confounds)

**N = 4 pairs**

#### Primary Metrics

| Metric | Mean ± SD | Min | Max | Status |
|--------|-----------|-----|-----|--------|
| Method Diff (Raw) | 0.301 ± 0.306 | 0.006 | 0.731 | ❌ High |
| RDM Reliability (Raw) | -0.040 ± 0.249 | -0.326 | 0.259 | ❌ Negative |
| Method Diff (Proc) | 0.126 ± 0.098 | 0.030 | 0.225 | ✅ Acceptable |
| RDM Reliability (Proc) | 0.302 ± 0.103 | 0.169 | 0.412 | ✅ Good |

#### Secondary Metrics

| Metric | Mean ± SD | Interpretation |
|--------|-----------|----------------|
| Temporal Autocorr | -0.199 ± 0.010 | ⚠️ Correlated |
| Drift Magnitude | 0.0027 ± 0.0001 | ✅ Acceptable |
| Procrustes Disparity | 0.0027 ± 0.0002 | ✅ Acceptable |

#### Per-Pair Breakdown

| Pair | Method Diff | RDM Rel (Raw) | RDM Rel (Proc) | Status |
|------|-------------|---------------|----------------|--------|
| sub-02_V1 | 0.226 | 0.259 | 0.282 | ⚠️ Moderate |
| sub-02_V2 | 0.731 | -0.326 | 0.169 | ❌ Negative Rel |
| sub-10_V1 | 0.006 | -0.135 | 0.412 | ✅✅ Excellent |
| sub-10_V2 | 0.242 | 0.040 | 0.346 | ⚠️ Moderate |

---

### P1: C010 + Motion/Tissue

**N = 4 pairs**

#### Primary Metrics

| Metric | Mean ± SD | Min | Max | Status |
|--------|-----------|-----|-----|--------|
| Method Diff (Raw) | 0.271 ± 0.255 | 0.031 | 0.501 | ⚠️ Moderate |
| RDM Reliability (Raw) | 0.148 ± 0.117 | -0.026 | 0.217 | ⚠️ Weak |
| Method Diff (Proc) | 0.148 ± 0.155 | 0.016 | 0.332 | ✅ Acceptable |
| RDM Reliability (Proc) | 0.280 ± 0.339 | -0.132 | 0.567 | ✅ Acceptable |

#### Secondary Metrics

| Metric | Mean ± SD | Interpretation |
|--------|-----------|----------------|
| Temporal Autocorr | -0.203 ± 0.005 | ❌ Strong drift |
| Drift Magnitude | 0.0027 ± 0.0001 | ✅ Acceptable |
| Procrustes Disparity | 0.0029 ± 0.0003 | ✅ Acceptable |

#### Per-Pair Breakdown

| Pair | Method Diff | RDM Rel (Raw) | RDM Rel (Proc) | Status |
|------|-------------|---------------|----------------|--------|
| sub-02_V1 | 0.071 | 0.215 | 0.547 | ✅ Good |
| sub-02_V2 | 0.031 | -0.026 | -0.132 | ✅✅ Excellent |
| sub-10_V1 | 0.501 | 0.186 | 0.137 | ❌ Poor |
| sub-10_V2 | 0.481 | 0.217 | 0.567 | ❌ Poor |

---

### P2: C010 + WM aCompCor

**N = 4 pairs**

#### Primary Metrics

| Metric | Mean ± SD | Min | Max | Status |
|--------|-----------|-----|-----|--------|
| Method Diff (Raw) | 0.291 ± 0.341 | 0.072 | 0.798 | ⚠️ Moderate |
| RDM Reliability (Raw) | -0.134 ± 0.190 | -0.369 | 0.074 | ❌ Negative |
| Method Diff (Proc) | 0.118 ± 0.075 | 0.013 | 0.173 | ✅ Acceptable |
| RDM Reliability (Proc) | 0.296 ± 0.229 | -0.028 | 0.509 | ✅ Acceptable |

#### Secondary Metrics

| Metric | Mean ± SD | Interpretation |
|--------|-----------|----------------|
| Temporal Autocorr | -0.197 ± 0.011 | ⚠️ Correlated |
| Drift Magnitude | 0.0027 ± 0.0001 | ✅ Acceptable |
| Procrustes Disparity | 0.0027 ± 0.0002 | ✅ Acceptable |

#### Per-Pair Breakdown

| Pair | Method Diff | RDM Rel (Raw) | RDM Rel (Proc) | Status |
|------|-------------|---------------|----------------|--------|
| sub-02_V1 | 0.072 | 0.074 | 0.509 | ⚠️ Moderate |
| sub-02_V2 | 0.798 | -0.369 | -0.028 | ❌ Negative Rel |
| sub-10_V1 | 0.179 | -0.190 | 0.338 | ❌ Negative Rel |
| sub-10_V2 | 0.114 | -0.053 | 0.366 | ❌ Negative Rel |

---

### P3: C010 + Motion/Tissue + WM aCompCor

**N = 4 pairs**

#### Primary Metrics

| Metric | Mean ± SD | Min | Max | Status |
|--------|-----------|-----|-----|--------|
| Method Diff (Raw) | 0.197 ± 0.173 | 0.038 | 0.351 | ✅ Good |
| RDM Reliability (Raw) | 0.080 ± 0.089 | -0.036 | 0.151 | ⚠️ Weak |
| Method Diff (Proc) | 0.076 ± 0.076 | 0.012 | 0.185 | ✅ Good |
| RDM Reliability (Proc) | 0.331 ± 0.304 | -0.032 | 0.654 | ✅ Good |

#### Secondary Metrics

| Metric | Mean ± SD | Interpretation |
|--------|-----------|----------------|
| Temporal Autocorr | -0.203 ± 0.005 | ❌ Strong drift |
| Drift Magnitude | 0.0027 ± 0.0001 | ✅ Acceptable |
| Procrustes Disparity | 0.0029 ± 0.0003 | ✅ Acceptable |

#### Per-Pair Breakdown

| Pair | Method Diff | RDM Rel (Raw) | RDM Rel (Proc) | Status |
|------|-------------|---------------|----------------|--------|
| sub-02_V1 | 0.056 | 0.149 | 0.654 | ⚠️ Moderate |
| sub-02_V2 | 0.038 | -0.036 | -0.032 | ✅✅ Excellent |
| sub-10_V1 | 0.351 | 0.056 | 0.210 | ❌ Poor |
| sub-10_V2 | 0.342 | 0.151 | 0.494 | ❌ Poor |

---
