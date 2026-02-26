# RDM Metric and Normalization Sensitivity Report

**Date**: 20260222_215808
**HC subjects**: 7
**CVD subjects**: 3

---

## Summary: FDR-Significant Pairs by Condition

| Condition | V1 | V2 | V3 | hV4 | Total | Change from Baseline |
|-----------|----|----|----|----|-------|---------------------|
| Correlation + none | 0 | 0 | 0 | 0 | 0 | (baseline) |
| Correlation + within | 0 | 0 | 0 | 0 | 0 | 0 |
| Correlation + pooled | 0 | 0 | 0 | 0 | 0 | 0 |
| Crossnobis + none | 0 | 0 | 0 | 0 | 0 | 0 |
| Crossnobis + within | 0 | 0 | 0 | 0 | 0 | 0 |
| Crossnobis + pooled | 0 | 0 | 0 | 0 | 0 | 0 |

---

## Convergence: Correlation Between Conditions

Spearman correlation of z-scores between each condition and baseline (correlation + none):

| Condition | V1 r | V2 r | V3 r | hV4 r | Mean r | Interpretation |
|-----------|------|------|------|-------|--------|----------------|
| Correlation + within | nan | nan | nan | nan | nan | ❌ Very low (unreliable) |
| Correlation + pooled | nan | nan | nan | nan | nan | ❌ Very low (unreliable) |
| Crossnobis + none | nan | nan | nan | nan | nan | ❌ Very low (unreliable) |
| Crossnobis + within | nan | nan | nan | nan | nan | ❌ Very low (unreliable) |
| Crossnobis + pooled | nan | nan | nan | nan | nan | ❌ Very low (unreliable) |

---

## Pair Agreement: Baseline vs Alternative Conditions

Agreement rate: percentage of pairs with same FDR significance status (within-ROI q<0.05).

| Condition | Agreement | Disagreement | Rate | Interpretation |
|-----------|-----------|--------------|------|----------------|
| Correlation + within | 0 | 0 | 0.0% | ❌ Low agreement (results change) |
| Correlation + pooled | 0 | 0 | 0.0% | ❌ Low agreement (results change) |
| Crossnobis + none | 0 | 0 | 0.0% | ❌ Low agreement (results change) |
| Crossnobis + within | 0 | 0 | 0.0% | ❌ Low agreement (results change) |
| Crossnobis + pooled | 0 | 0 | 0.0% | ❌ Low agreement (results change) |

---

## Key Findings

### Q1: Does crossnobis method affect results?

**To be determined from results above:**
- If correlation r > 0.9 and agreement > 95%: Metric choice does NOT matter (robust)
- If correlation r = 0.7-0.9 and agreement 80-95%: Moderate sensitivity (report both)
- If correlation r < 0.7 or agreement < 80%: High sensitivity (metric choice matters)

### Q2: Does z-normalization affect results?

**To be determined from results above:**
- If within/pooled norm has similar total FDR pairs ±10%: Normalization does NOT matter
- If within/pooled norm differs >20%: Normalization affects results (variance matters)

---

## Recommendations

**Based on convergence analysis:**

1. **If crossnobis r > 0.9**: Use correlation distance (simpler, current method validated)
2. **If crossnobis r < 0.7**: Report both metrics or prefer crossnobis (more principled for fMRI)
3. **If z-norm changes FDR survivors >20%**: Use within-subject z-norm (accounts for baseline variance)
4. **If z-norm robust (agreement >95%)**: Keep current method (no norm, simpler to interpret)

**Full results**: `metric_norm_test_20260222_215808.json`
