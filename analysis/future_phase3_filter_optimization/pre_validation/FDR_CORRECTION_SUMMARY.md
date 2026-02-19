# FDR Correction Summary: Addressing Reviewer #2 Criticism 1

**Date**: 2026-02-19
**Analysis**: Benjamini-Hochberg FDR correction applied to B3 bootstrap results
**Status**: ✅ COMPLETE

---

## Executive Summary

Applied Benjamini-Hochberg FDR correction to address the **multiple comparisons catastrophe** identified by Reviewer #2. Testing 28 color pairs × 3 ROIs × 3 CVD subjects = 252 comparisons without correction led to inflated false positives.

### Key Results

| Metric | Before FDR | After Global FDR | Reduction |
|--------|-----------|------------------|-----------|
| **Total significant** | 121/252 (48.0%) | 37/252 (14.7%) | **69% reduction** |
| **sub-08 total** | 50/84 pairs | 28/84 pairs | 44% reduction |
| **sub-09 total** | 40/84 pairs | 8/84 pairs | 80% reduction |
| **sub-10 total** | 31/84 pairs | 1/84 pairs | 97% reduction |

### Filter Target Implications

**Original HIGH priority pairs** (filter_design_plan.md section 4.3): red-orange, orange-yellow, cyan-blue

| Subject | HIGH Surviving | MEDIUM Surviving | Total FDR-Surviving | Filter Recommendation |
|---------|---------------|------------------|---------------------|----------------------|
| **sub-08** | **3/9** | **3/9** | 28/84 | ✅ **STRONG** — Proceed with filter design |
| **sub-09** | **0/9** | **1/9** | 8/84 | ⚠️ **WEAK** — Marginal evidence; exploratory only |
| **sub-10** | **0/9** | **1/9** | 1/84 | ❌ **INSUFFICIENT** — No statistical basis for filter |

---

## Method Explanation

### Problem Statement

The original B3 bootstrap analysis tested **252 color-pair comparisons** (28 pairs × 3 ROIs × 3 subjects) and reported 121 as "significant" based on 95% bootstrap CIs excluding zero.

**Without multiple comparison correction**:
- Expected false positives under null: 252 × 0.05 = **12.6 false discoveries**
- Reported significant: 121 (48% of all tests)
- Likely inflated by ~10-15 false positives

This inflates the filter pair weights (section 4.3) and personalization strategy (section 4.4), potentially building the filter on noise.

### Solution: Benjamini-Hochberg FDR Correction

**Reference**: Benjamini, Y., & Hochberg, Y. (1995). Controlling the false discovery rate: a practical and powerful approach to multiple testing. *Journal of the Royal Statistical Society: Series B (Methodological)*, 57(1), 289-300.

**Method**:
1. Convert bootstrap z-scores to p-values using normal approximation: `p = 2 × (1 - Φ(|z|))`
2. Apply FDR correction at two levels:
   - **Within subject-ROI**: Controls FDR among 28 pairs per test (less conservative, appropriate for characterization)
   - **Global**: Controls FDR across all 252 tests (most conservative, appropriate for filter design)
3. Threshold: q = 0.05 (expected false discovery rate ≤ 5%)

**Implementation**: `scipy.stats.false_discovery_control(pvalues, method='bh')`

### Why Two Correction Levels?

| Level | Use Case | Trade-off |
|-------|----------|-----------|
| **Within-ROI FDR** | Characterization paper (each ROI is independent scientific question) | More power, but doesn't control family-wise error across ROIs |
| **Global FDR** | Filter design (making translational claims across all ROIs) | Most conservative, appropriate for high-stakes claims |

**For this project**: Use **global FDR** for filter target selection; report within-ROI FDR in supplementary materials.

---

## Detailed Results by Subject

### sub-08 (Deutan, Strongest Case)

| ROI | Raw Sig | FDR Within-ROI | FDR Global | Key Surviving Pairs |
|-----|---------|----------------|------------|---------------------|
| **V1** | 15/28 | 3/28 | 3/28 | red-yellow (z=5.14), yellow-purple (z=4.84) |
| **V2** | 17/28 | 12/28 | **11/28** | **orange-yellow (z=5.45)**, yellow-purple (z=13.87), blue-purple (z=6.15) |
| **V3** | 18/28 | 17/28 | **14/28** | red-green (z=7.85), **orange-yellow (z=5.16)**, yellow-purple (z=6.17) |

**HIGH priority pairs surviving global FDR**:
- **orange-yellow** (V2 z=5.45 p<0.0001, V3 z=5.16 p<0.0001) ✅ ROBUST
- **red-orange** (V3 z=3.74 p=0.0002) ✅ MODERATE
- cyan-blue: ❌ Does NOT survive global FDR

**MEDIUM priority pairs surviving**:
- **blue-purple** (V2 z=6.15 p<0.0001, V3 z=4.58 p<0.0001) ✅ ROBUST
- **red-green** (V3 z=7.85 p<0.0001) ✅ ROBUST
- red-magenta: ❌ Does NOT survive global FDR

**Interpretation**: sub-08 shows strong, consistent anisotropic redistribution in V2/V3. Filter design should focus on:
1. **L-M axis restoration**: red-orange (increase separability)
2. **S-cone normalization**: orange-yellow, blue-purple (decrease over-separation)

**Filter recommendation**: ✅ **PROCEED** — Sufficient statistical basis with 28/84 pairs surviving global FDR.

---

### sub-09 (Protan, Weak Evidence)

| ROI | Raw Sig | FDR Within-ROI | FDR Global | Key Surviving Pairs |
|-----|---------|----------------|------------|---------------------|
| **V1** | 17/28 | 6/28 | **6/28** | cyan-magenta (z=4.08), red-magenta (z=3.52) |
| **V2** | 13/28 | 0/28 | 1/28 | orange-magenta (z=2.91, marginal) |
| **V3** | 10/28 | 1/28 | 1/28 | orange-magenta (z=3.32) |

**HIGH priority pairs surviving**: ❌ **NONE**

**MEDIUM priority pairs surviving**:
- red-magenta (V1 z=3.52 p=0.0004) — Only 1 pair in 1 ROI

**Interpretation**: sub-09 shows **protan-specific pattern** (cyan-magenta, orange-magenta elevations) that differs from the deutan profile, but most pairs do NOT survive global FDR. This suggests:
1. Either the effects are genuinely weaker in protan CVD (cortical compensation?)
2. Or n=1 protan subject is insufficient to detect consistent patterns

**Filter recommendation**: ⚠️ **MARGINAL** — Only 8/84 pairs survive. If filter is attempted, it should be:
- Framed as exploratory/pilot
- Focus on V1 magenta-axis over-separation (robust finding)
- Do NOT claim generalizability to protan CVD without additional subjects

---

### sub-10 (Deutan, Insufficient Evidence)

| ROI | Raw Sig | FDR Within-ROI | FDR Global | Key Surviving Pairs |
|-----|---------|----------------|------------|---------------------|
| **V1** | 8/28 | 0/28 | 0/28 | None |
| **V2** | 10/28 | 0/28 | 1/28 | blue-purple (z=2.86 p=0.0042, marginal) |
| **V3** | 13/28 | 0/28 | 0/28 | None |

**HIGH priority pairs surviving**: ❌ **NONE**

**MEDIUM priority pairs surviving**:
- blue-purple (V2 z=2.86) — Only 1 pair, marginally significant

**Interpretation**: sub-10 shows **NO reliable anisotropic redistribution** after FDR correction. This is consistent with:
1. Split-half reliability analysis (B2): r<0.30 in V1/hV4 (unreliable)
2. Crawford & Howell individual test: all p-values non-significant
3. Interpretation in filter_design_plan.md section 3.5: "effective cortical compensation"

**Filter recommendation**: ❌ **DO NOT PROCEED** — Only 1/84 pairs survives. sub-10 should be reported as a "compensation case study" rather than a filter candidate.

---

## Comparison to Original Priority Pairs

### Original Filter Pair Weights (filter_design_plan.md section 4.3)

| Priority | Pairs | Rationale (Original) | FDR-Corrected Status |
|----------|-------|---------------------|----------------------|
| **HIGH (w=3.0)** | red-orange, orange-yellow, cyan-blue | "3/3 CVD agree, z: -1.3 to -2.3" | ❌ **PARTIAL** — Only orange-yellow and red-orange survive (sub-08 only); cyan-blue does NOT |
| **MEDIUM (w=2.0)** | red-magenta, blue-purple, red-green | "2-3/3 CVD agree" | ✅ **PARTIAL** — blue-purple and red-green survive (sub-08); red-magenta marginal (sub-09 V1 only) |

### Revised Filter Pair Weights (Global FDR q=0.05)

**For sub-08 (only subject with sufficient evidence)**:

| Priority | Pairs | ROIs | FDR Evidence | Weight |
|----------|-------|------|--------------|--------|
| **HIGH** | orange-yellow | V2, V3 | z=5.16-5.45, p<0.0001 | 3.0 |
| **HIGH** | red-orange | V3 | z=3.74, p=0.0002 | 3.0 |
| **MEDIUM** | blue-purple | V2, V3 | z=4.58-6.15, p<0.0001 | 2.5 |
| **MEDIUM** | red-green | V3 | z=7.85, p<0.0001 | 2.5 |
| **MEDIUM** | red-yellow | V2, V3 | z=5.88-9.38, p<0.0001 | 2.0 |
| **MEDIUM** | yellow-purple | V1, V2, V3 | z=4.84-13.87, p<0.0001 | 2.0 |
| **LOW** | All other pairs | - | Not FDR-significant | 1.0 (preserve) |

**For sub-09 / sub-10**: Insufficient evidence for filter design. Report as characterization only.

---

## Implications for Reviewer Response

### What Changed

1. **Raw claim** (WRONG): "121/252 pairs show significant CVD-HC differences (48%)"
2. **FDR-corrected claim** (CORRECT): "37/252 pairs survive global FDR correction (14.7%)"

### Reviewer Persuasion Strategy

**Original vulnerability**: "With 336 tests and no MCP correction, ~17 false positives are expected. Your filter targets may be noise."

**Response with FDR correction**:

> "We applied Benjamini-Hochberg FDR correction at q=0.05 across all 252 tests (28 pairs × 3 ROIs × 3 subjects). After global FDR correction, 37/252 pairs survive (14.7%), down from 121 raw significant. In sub-08 (deutan), the L-M axis deficit (red-orange) and S-cone compensations (orange-yellow, blue-purple) survive as robust, FDR-corrected findings with p<0.001. These pairs form the statistical basis for filter target weights.
>
> We acknowledge that sub-09 (protan, n=1) and sub-10 (compensated deutan, n=1) show insufficient FDR-surviving pairs (8/84 and 1/84, respectively). We therefore reframe the filter design as a **single-subject demonstration** (sub-08) with clear generalizability limits, rather than a group-level claim. The n=3 cross-subject consistency analysis is reported in supplementary materials for characterization purposes but does NOT drive filter parameterization."

### Updated Risk Assessment

| Risk | Before FDR | After FDR | Mitigation |
|------|-----------|-----------|------------|
| False positive filter targets | HIGH | LOW | Global FDR q=0.05 controls FDR at 5%; filter weights derived only from FDR-surviving pairs |
| n=3 generalizability claim | FATAL | ADDRESSABLE | Reframe as sub-08 single-subject demonstration; sub-09/sub-10 insufficient evidence acknowledged |
| Reviewers reject statistical rigor | HIGH | LOW | Standard FDR method (Benjamini & Hochberg, 1995); two-level correction strategy transparent |

---

## Next Steps

### 1. Update Filter Design Plan (filter_design_plan.md)

**Section 4.3 (Pair-Specific Weights)** — Replace table with FDR-corrected weights:

```markdown
| Priority | Pairs | Direction | Weight | FDR Evidence (sub-08) |
|----------|-------|-----------|--------|----------------------|
| HIGH | orange-yellow | Normalize (decrease) | 3.0 | V2/V3 z=5.16-5.45, p<0.0001 |
| HIGH | red-orange | Restore (increase) | 3.0 | V3 z=3.74, p=0.0002 |
| MEDIUM | blue-purple | Normalize (decrease) | 2.5 | V2/V3 z=4.58-6.15, p<0.0001 |
| MEDIUM | red-green | Restore (increase) | 2.5 | V3 z=7.85, p<0.0001 |
```

**Section 4.4 (Personalization Strategy)** — Update:

```markdown
| Subject | Filter strength | Statistical basis | Recommendation |
|---------|----------------|-------------------|----------------|
| sub-08 | Strong | 28/84 pairs FDR-significant | Primary filter prototype |
| sub-09 | Insufficient | 8/84 pairs FDR-significant | Characterization only |
| sub-10 | Insufficient | 1/84 pairs FDR-significant | Compensation case study |
```

### 2. Update METHODS_RESULTS_SUMMARY_FOR_PAPER.md

Add section:

```markdown
## Multiple Comparison Correction

All color-pair comparisons (28 pairs × 3 ROIs × 3 subjects = 252 tests) were corrected for multiple comparisons using Benjamini-Hochberg FDR correction (q=0.05). P-values were derived from bootstrap z-scores using normal approximation. We report both within-ROI FDR (appropriate for characterization) and global FDR (appropriate for filter target selection) in supplementary materials. Filter pair weights were derived exclusively from global FDR-surviving pairs.
```

### 3. Generate Supplementary Tables

- **Table S1**: Full 28-pair z-scores and FDR-corrected p-values for all subject-ROI combinations
- **Table S2**: Filter pair weights with FDR evidence (updated from section 4.3)
- **Table S3**: Comparison of raw vs. within-ROI FDR vs. global FDR

---

## Files Generated

| File | Description |
|------|-------------|
| `apply_fdr_correction.py` | Python script implementing FDR correction |
| `results/fdr_corrected/filter_pre_validation_fdr_corrected.json` | Complete FDR-corrected results (machine-readable) |
| `results/fdr_corrected/FDR_CORRECTION_REPORT.md` | Detailed human-readable report |
| `results/fdr_corrected/fdr_correction_impact.png` | Visualization: raw vs. FDR comparison |
| `results/fdr_corrected/filter_targets_fdr_surviving.png` | Visualization: filter targets by subject |
| `FDR_CORRECTION_SUMMARY.md` | This summary document |

---

## Conclusion

✅ **Criticism 1 RESOLVED**: Multiple comparison correction applied using standard Benjamini-Hochberg FDR method. The anisotropic redistribution finding in sub-08 survives as a robust, FDR-corrected result. Filter design can proceed for sub-08 with clear statistical justification, while sub-09 and sub-10 are reframed as insufficient evidence cases.

**Remaining criticisms to address**:
- **Criticism 2** (SRM circularity): Replicate pair-distance analysis in crossnobis space
- **Criticism 3** (No behavioral ground truth): Collect pairwise discrimination thresholds
- **Criticism 4** (n=3 mixed-subtype): Binomial test + power analysis
- **Criticism 5** (8-color overfitting): Fourier parameterization + LOCO validation
