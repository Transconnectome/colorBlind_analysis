# FDR Correction Report: Filter Pre-Validation B3 Bootstrap Results

**Generated**: 20260219_165405

**Addresses**: Reviewer #2 Criticism 1 (Multiple comparisons catastrophe)

---

## Method: Benjamini-Hochberg FDR Correction

### Problem

Testing 28 color pairs × 4 ROIs × 3 CVD subjects = 336 comparisons without correction leads to ~17 false positives by chance (336 × 0.05)

### Solution

Benjamini-Hochberg FDR correction controls the expected proportion of false discoveries among all rejected hypotheses

**Reference**: Benjamini, Y., & Hochberg, Y. (1995). Controlling the false discovery rate: a practical and powerful approach to multiple testing. *Journal of the Royal Statistical Society: Series B (Methodological)*, 57(1), 289-300.

### Implementation Details

1. **P-value derivation**: Converted bootstrap z-scores to p-values using normal approximation: `p = 2 × (1 - Φ(|z|))` where Φ is the standard normal CDF.

2. **FDR correction levels**:
   - **Within subject-ROI**: 28 pairs per test (less conservative, detects ROI-specific effects)
   - **Global**: All 336 tests combined (most conservative, controls family-wise FDR)

3. **FDR threshold**: q = 0.05

---

## Overall Summary

| Metric | Count | Percentage |
|--------|-------|------------|
| Total tests | 252 | 100% |
| Significant (raw, no correction) | 121 | 48.0% |
| Significant (FDR within-ROI) | 39 | 15.5% |
| Significant (FDR global) | 37 | 14.7% |

**Key finding**: After global FDR correction, 37 out of 252 tests survive (14.7%), down from 121 raw significant (48.0%).

---

## Per-Subject Summary

### sub-08

| ROI | Raw Sig | FDR Within-ROI | FDR Global |
|-----|---------|----------------|------------|
| V1 | 15/28 | 3/28 | 3/28 |
| V2 | 17/28 | 12/28 | 11/28 |
| V3 | 18/28 | 17/28 | 14/28 |

### sub-09

| ROI | Raw Sig | FDR Within-ROI | FDR Global |
|-----|---------|----------------|------------|
| V1 | 17/28 | 6/28 | 6/28 |
| V2 | 13/28 | 0/28 | 1/28 |
| V3 | 10/28 | 1/28 | 1/28 |

### sub-10

| ROI | Raw Sig | FDR Within-ROI | FDR Global |
|-----|---------|----------------|------------|
| V1 | 8/28 | 0/28 | 0/28 |
| V2 | 10/28 | 0/28 | 1/28 |
| V3 | 13/28 | 0/28 | 0/28 |

---

## Filter Targets: Pairs Surviving Global FDR Correction

Original priority pairs from filter_design_plan.md section 4.3:
- **HIGH**: red-orange, orange-yellow, cyan-blue
- **MEDIUM**: red-magenta, blue-purple, red-green

### sub-08: 28 total pairs survive global FDR

**HIGH priority pairs (surviving)**:

| Pair | ROI | z-score | p-value |
|------|-----|---------|----------|
| orange-yellow | V2 | 5.45 | 0.0000 |
| red-orange | V3 | 3.74 | 0.0002 |
| orange-yellow | V3 | 5.16 | 0.0000 |

**MEDIUM priority pairs (surviving)**:

| Pair | ROI | z-score | p-value |
|------|-----|---------|----------|
| blue-purple | V2 | 6.15 | 0.0000 |
| red-green | V3 | 7.85 | 0.0000 |
| blue-purple | V3 | 4.58 | 0.0000 |

**OTHER extreme pairs** (|z| > 1.5, surviving global FDR):

| Pair | ROI | z-score | p-value |
|------|-----|---------|----------|
| yellow-purple | V2 | 13.87 | 0.0000 |
| red-yellow | V2 | 9.38 | 0.0000 |
| green-purple | V3 | 6.96 | 0.0000 |
| yellow-purple | V3 | 6.17 | 0.0000 |
| yellow-magenta | V3 | 6.11 | 0.0000 |
| red-yellow | V3 | 5.88 | 0.0000 |
| yellow-green | V2 | 5.47 | 0.0000 |
| red-cyan | V3 | 5.36 | 0.0000 |
| red-yellow | V1 | 5.14 | 0.0000 |
| yellow-purple | V1 | 4.84 | 0.0000 |

*(12 more pairs not shown)*

### sub-09: 8 total pairs survive global FDR

**HIGH priority pairs**: None survive global FDR ❌

**MEDIUM priority pairs (surviving)**:

| Pair | ROI | z-score | p-value |
|------|-----|---------|----------|
| red-magenta | V1 | 3.52 | 0.0004 |

**OTHER extreme pairs** (|z| > 1.5, surviving global FDR):

| Pair | ROI | z-score | p-value |
|------|-----|---------|----------|
| cyan-magenta | V1 | 4.08 | 0.0000 |
| orange-magenta | V1 | 3.71 | 0.0002 |
| green-magenta | V1 | 3.43 | 0.0006 |
| orange-magenta | V3 | 3.32 | 0.0009 |
| yellow-purple | V1 | -3.31 | 0.0009 |
| green-blue | V1 | -3.00 | 0.0027 |
| orange-magenta | V2 | 2.91 | 0.0036 |

### sub-10: 1 total pairs survive global FDR

**HIGH priority pairs**: None survive global FDR ❌

**MEDIUM priority pairs (surviving)**:

| Pair | ROI | z-score | p-value |
|------|-----|---------|----------|
| blue-purple | V2 | 2.86 | 0.0042 |

---

## Interpretation & Implications for Filter Design

✅ **Sufficient statistical basis**: 37 pairs survive global FDR across 3 subjects. Filter design can proceed with FDR-surviving pairs as targets.

**Recommendation**: Update filter pair weights (filter_design_plan.md section 4.3) to reflect only FDR-surviving pairs. Any pairs not surviving global FDR should be downweighted to w=1.0 (preserve) rather than 2.0-3.0 (target for correction).

---

## Method Comparison: Within-ROI vs Global FDR

| Approach | Pros | Cons | Use Case |
|----------|------|------|----------|
| **Within-ROI FDR** | Detects ROI-specific effects; More power; Appropriate if ROIs are independent questions | May miss familywise error control; Not appropriate for filter design across all ROIs | Characterization paper focusing on per-ROI patterns |
| **Global FDR** | Controls false discoveries across all tests; Most conservative; Appropriate for filter design | Lower power; May be overly conservative if ROIs truly independent | Filter design paper making translational claims |

**For this project**: Use **global FDR** for filter target selection (translational claims require stringent control). Report within-ROI FDR in supplementary materials for characterization purposes.

