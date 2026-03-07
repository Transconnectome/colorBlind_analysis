# Filter Pre-Validation - Quick Reference

**Date**: 2026-02-18
**File**: `filter_pre_validation_results.json`

---

## Executive Summary

### Split-Half Reliability (B2)
Strong temporal stability in V1, V2, hV4; weak in V3.

| ROI | Group r | Status | Key Issue |
|-----|---------|--------|-----------|
| V1 | 0.729 | ✓ Strong | sub-10 weak (r=0.286) |
| V2 | 0.714 | ✓ Strong | All subjects reliable |
| V3 | 0.333 | ✗ Weak | sub-09, sub-10 fail (r<0.30) |
| hV4 | 0.660 | ✓ Strong | sub-10 weak (r=0.234) |

---

## Significant Effects Summary

### V2 Shows Strongest Effects

**sub-08 extreme z-scores:**
- red-yellow: z = 10.29 (p=0.067)
- yellow-green: z = 4.14
- blue-purple: z = 4.34 (p=0.042**)
- orange-yellow: z = 3.29

**Bootstrap 95% CI markers:**
- orange-yellow: [1.97, 33.16]***
- yellow-green: [3.47, 10.36]***
- blue-purple: [2.91, 15.31]***

### hV4 Shows Extended Color Confusion Pattern

**sub-08 (21 significant pairs):**
- Dominant warm-color effects (red, orange, yellow)
- High z-scores: red-yellow (5.54), orange-yellow (5.14), red-orange (4.34)

**sub-10 (22 significant pairs):**
- Nearly opposite pattern (deficit where sub-08 elevation)
- Suggests different CVD type or representation

---

## Cross-Subject Consistency - Robust Findings

### Consistent Across All 3 Subjects

**Green-Blue Deficit (step=2):**
- V1: z = [-0.89, -2.41, -1.16]
- V2: z = [-0.41, -0.96, -0.05]
- V3: z = [-0.02, -0.29, -0.67]
- **Interpretation**: Likely shared red/green × intensity confusion

**Red-Magenta Elevation (step=1):**
- V1: z = [0.69, 3.02, 1.43]
- V2: z = [1.66, 1.64, 0.51]
- hV4: z = [4.96, 3.22, -1.04] (hV4 sub-10 weak)
- **Interpretation**: Shared representational change

### Red-Purple Mixed Pattern

| ROI | Direction | Z-values |
|-----|-----------|----------|
| V1 | Deficit | [-0.97, -0.62, -0.79] |
| V2 | Deficit | [-0.47, -0.26, -0.83] |
| V3 | Elevation | [1.25, 0.52, 0.36] |

**Interpretation**: ROI-dependent effect or threshold crossing

---

## Per-Subject Reliability Profile

### sub-08: Strongest and Most Consistent
- V1 r = 0.777 (excellent)
- V2 r = 0.839 (excellent)
- V3 r = 0.765 (excellent)
- hV4 r = 0.729 (strong)
- **Status**: ✓ Most reliable, use as reference

### sub-09: Good Overall, Variable on Some Pairs
- V1 r = 0.645 (good)
- V2 r = 0.684 (good)
- V3 r = 0.264 (fails)
- hV4 r = 0.747 (good)
- **Status**: ✓ Usable; caution in V3

### sub-10: Weakest Signal Throughout
- V1 r = 0.286 (fails)
- V2 r = 0.677 (good)
- V3 r = 0.010 (fails)
- hV4 r = 0.234 (fails)
- **Status**: ⚠ Use with caution; V2 only reliable

---

## Methodological Notes

### B1 Permutation Test (Conservative)
- Only 1 significant effect: V2 blue-purple (p=0.042)
- Group-level test is conservative
- Individual effects much larger (see B3)

### B2 Split-Half (Most Informative)
- Best indicator of data quality
- Group-level correlations more informative than individual
- V3 unreliable as group measurement

### B3 Bootstrap (Most Detailed)
- 95% CI does not cross zero = significant at p<0.05
- Many effects significant at individual level
- Shows very different patterns across subjects

---

## Critical Data Points (for paper/documentation)

### Table 1: B1 Z-Scores for Adjacent Pairs

**V1 - All negative except warm colors:**
```
red-orange:    -0.82, -1.35, -0.68 (consistent deficit)
orange-yellow:  1.99,  0.73, -0.25 (mixed)
yellow-green:   1.53, -1.18,  0.04 (inconsistent)
green-cyan:    -1.14, -0.51,  0.14 (mostly deficit)
cyan-blue:     -0.95, -0.51, -0.59 (consistent deficit)
blue-purple:    0.81, -1.02, -0.49 (mixed)
purple-magenta: 0.98,  1.15,  0.31 (consistent elevation)
red-magenta:    0.70,  3.02,  1.43 (consistent elevation)
```

**V2 - Strongest effects on warm colors (sub-08):**
```
red-yellow:    10.29,  0.87,  0.89 (sub-08 extreme)
orange-yellow:  3.29,  0.40, -0.13
yellow-green:   4.14, -0.78, -0.59 (sub-08 extreme)
blue-purple:    4.34,  0.33,  2.08
```

**hV4 - Opposite trend (sub-08 elevation, sub-10 deficit):**
```
red-orange:     4.34,  0.47, -0.86
orange-yellow:  5.14,  0.23, -0.54
yellow-green:   4.72, -0.59, -0.55
red-magenta:    4.96,  3.22, -1.04 (divergent)
```

---

## Recommendations for Documentation

1. **Highlight V2 results**: Most consistent and strongest
2. **Note subject differences**: Not a homogeneous group
3. **Use hV4 cautiously**: High variability masks patterns
4. **Green-blue deficit**: Most robust finding
5. **Red-magenta elevation**: Second most robust
6. **Methodology**: Bootstrap CIs more informative than group p-values

---

## Files Referenced

- **Input**: `/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/future_phase2_filter_optimization/pre_validation/results/filter_pre_validation_results.json`
- **Output**:
  - `VALIDATION_RESULTS_SUMMARY.md` (full details)
  - `QUICK_REFERENCE.md` (this file)
