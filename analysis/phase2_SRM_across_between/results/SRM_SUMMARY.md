# SRM Between-Subject Analysis: Quick Summary

**Date**: 2026-02-06
**Status**: ⚠️ **PRELIMINARY** - Pending Procrustes validation

---

## TL;DR

Beta-based SRM shows **significant HC-CVD differences in V2 and V3**, but **RDM similarities are too low** across all ROIs, suggesting SRM's shared response model may be inadequate for this dataset. **Procrustes-based alignment** is recommended as next step.

---

## Key Results Table

| ROI | HC-CVD Significant? | p-value | Cohen's d | HC-HC RDM Similarity | Recommendation |
|-----|---------------------|---------|-----------|----------------------|----------------|
| V1  | ❌ No | 0.309 | 0.85 | 0.259 ± 0.155 | Low similarity → Try Procrustes |
| V2  | ✅ Yes | <0.001 | **6.68** | 0.446 ± 0.253 | Strongest effect, but still low similarity |
| V3  | ✅ Yes | 0.002 | **3.71** | 0.195 ± 0.216 | Significant but low similarity |
| hV4 | ❌ No | 0.553 | 0.49 | 0.031 ± 0.158 | Very low similarity → Try Procrustes |

---

## Critical Issue: Low RDM Similarity

**Problem**: Even HC-HC pairs show low RDM correlations (r=0.03-0.45)

**What this means**:
- SRM's "shared response space" doesn't capture much common structure
- High individual variability in color representation
- k=3-4 features may be insufficient (constrained by 8 stimuli)

**Why it matters**:
- Low similarity → unreliable shared space
- CVD differences may be confounded with general low similarity
- Results may not reflect true HC-CVD differences

---

## Why Procrustes Is Needed

| Issue | SRM Limitation | Procrustes Advantage |
|-------|----------------|----------------------|
| **Dimensionality** | k ≤ 8 (constrained by n_stimuli) | Full voxel space (200-300 voxels) |
| **Heterogeneity** | Assumes shared CVD structure | Pairwise alignment (robust to heterogeneity) |
| **Similarity** | Requires good shared model | Direct pattern matching |
| **Baseline** | New method for this dataset | Already validated in Phase 1 |

---

## What SRM Did Find

### 1. V2 Shows Strongest CVD Effect
- CVD-to-HC disparity: 1.162 ± 0.102
- HC-to-HC disparity: 0.498 ± 0.097
- **Effect size d=6.68** (very large)
- **p<0.001** ✓

### 2. V3 Also Shows Significant Effect
- CVD-to-HC disparity: 1.148 ± 0.117
- HC-to-HC disparity: 0.729 ± 0.109
- **Effect size d=3.71** (large)
- **p=0.002** ✓

### 3. CVD Subjects Are Heterogeneous
- CVD-CVD RDM similarities: **negative** in V2 (-0.033) and V3 (-0.098)
- Suggests each CVD subject has unique representation
- Not a uniform group effect

---

## Next Steps (Priority Order)

### 🔴 **Priority 1: Procrustes Between-Subject Analysis**

**Why**: Addresses dimensionality constraint and low similarity issues

**Plan**:
1. Load Phase 1 baseline z-scored amplitudes
2. For each CVD subject: align to each HC subject via Procrustes
3. Compute CVD-HC disparities (18 pairs) vs HC-HC baseline (15 pairs)
4. Test: CVD-HC > HC-HC?

**Expected Timeline**: 1-2 days

**Script to create**: `evaluate_procrustes_between_subject.py`

### 🟡 **Priority 2: Validate SRM Findings with Procrustes**

If Procrustes confirms V2/V3 effects:
- ✓ SRM findings are valid despite low similarity
- Continue with color-specific analysis

If Procrustes contradicts:
- ⚠️ SRM false positives due to methodological issues
- Rely on Procrustes results

### 🟢 **Priority 3: (Optional) Improve SRM**

If time permits and Procrustes also shows issues:
- Try alternative validation (cross-validation on runs, not colors → allow k>8)
- Searchlight SRM (local voxel neighborhoods)
- PCA-based comparison (no SRM assumption)

---

## Files Generated

**Location**: `results/srm_between_subject/test_local_20260206_220129/`

**Per ROI** (V1, V2, V3, hV4):
- `{ROI}_srm_between_subject_results.json` - Numerical results
- `{ROI}_hc_cvd_disparity_comparison.png` - 3-group boxplot
- `{ROI}_rdm_similarity_matrix.png` - Subject similarity heatmap
- `{ROI}_color_space_all_subjects.png` - MDS color space grid
- `{ROI}_hc_vs_cvd_color_space_comparison.png` - HC vs CVD MDS

**Summary**:
- `SRM_BETWEEN_SUBJECT_PRELIMINARY_RESULTS.md` - Full report (this document's detailed version)
- `SRM_QUICK_SUMMARY.md` - This file

---

## Bottom Line

**SRM analysis is incomplete due to methodological constraints. Procrustes-based alignment is required before drawing final conclusions about HC-CVD differences in color representation.**

**Current status**: V2 and V3 show promising HC-CVD differences, but low RDM similarity undermines confidence in results.

**Recommendation**: Proceed with Procrustes analysis immediately. Treat SRM results as exploratory only.

---

*For detailed methodology, metrics, and interpretation, see: `SRM_BETWEEN_SUBJECT_PRELIMINARY_RESULTS.md`*
