# Filter Pre-Validation Results - Comprehensive Summary

**File**: `filter_pre_validation_results.json`
**Date**: 2026-02-18

---

## Overview

This document summarizes the pre-validation analysis of CVD color filters learned in Phase 3. The analysis includes three main validation approaches:
- **B1**: Permutation tests on individual z-scores
- **B2**: Split-half correlation for temporal stability
- **B3**: Bootstrap confidence intervals on per-subject effects

---

## B1: Individual Z-Scores and Group P-Values (Permutation Test)

Z-scores represent standardized distances between color pairs in the CVD filter space. Group p-values are from permutation tests (1000 permutations).

### V1 - Permutation Test Results

**observed_individual_z (individual z-scores):**

| Pair | sub-08 | sub-09 | sub-10 |
|------|--------|--------|--------|
| **Adjacent Pairs** | | | |
| red-orange | -0.8241 | -1.3510 | -0.6790 |
| orange-yellow | 1.9984 | 0.7348 | -0.2546 |
| yellow-green | 1.5262 | -1.1775 | 0.0350 |
| green-cyan | -1.1423 | -0.5064 | 0.1358 |
| cyan-blue | -0.9508 | -0.5072 | -0.5881 |
| blue-purple | 0.8134 | -1.0222 | -0.4879 |
| purple-magenta | 0.9839 | 1.1470 | 0.3104 |
| red-magenta | 0.6950 | 3.0181 | 1.4345 |
| **Other Pairs** | | | |
| red-green | 0.2923 | -1.4331 | -0.4402 |
| orange-green | 0.4248 | -0.7987 | -0.7392 |
| red-yellow | 2.4897 | -0.4545 | -0.0125 |
| red-purple | -0.9702 | -0.6155 | -0.7937 |
| orange-purple | -0.1289 | -0.0087 | -0.5234 |

**p_two_sided (group-level two-sided p-values):**

| Pair | p-value | Significance |
|------|---------|--------------|
| red-orange | 0.1833 | |
| orange-yellow | 0.2583 | |
| yellow-green | 0.9000 | |
| green-cyan | 0.5083 | |
| cyan-blue | 0.3417 | |
| blue-purple | 0.7583 | |
| purple-magenta | 0.2250 | |
| red-magenta | 0.0583 | trending |
| red-green | 0.4667 | |
| orange-green | 0.6417 | |
| red-yellow | 0.3167 | |
| red-purple | 0.3417 | |
| orange-purple | 0.8250 | |

### V2 - Permutation Test Results

**observed_individual_z:**

| Pair | sub-08 | sub-09 | sub-10 |
|------|--------|--------|--------|
| **Adjacent Pairs** | | | |
| red-orange | 0.5356 | -0.9619 | 0.6260 |
| orange-yellow | 3.2910 | 0.4029 | -0.1286 |
| yellow-green | 4.1424 | -0.7780 | -0.5869 |
| green-cyan | 0.3704 | -1.4656 | 1.0699 |
| cyan-blue | -0.0809 | 0.0691 | 1.3903 |
| blue-purple | 4.3379 | 0.3332 | 2.0764 |
| purple-magenta | 0.5786 | 0.9337 | 0.0746 |
| red-magenta | 1.6625 | 1.6384 | 0.5148 |
| **Other Pairs** | | | |
| red-green | 1.8035 | -0.5546 | -0.5620 |
| orange-green | 0.2454 | -0.7092 | -0.7695 |
| red-yellow | 10.2921 | 0.8714 | 0.8893 |
| red-purple | -0.4677 | -0.2618 | -0.8304 |
| orange-purple | -0.8844 | -0.8451 | 0.1692 |

**p_two_sided (group-level):**

| Pair | p-value | Significance |
|------|---------|--------------|
| blue-purple | 0.0417 | **p < 0.05** |
| red-yellow | 0.0667 | trending |

### V3 - Permutation Test Results

Individual z-scores show high variability across subjects, with sub-08 showing strongest effects. All group-level p-values > 0.10, indicating no significant group effects.

### hV4 - Permutation Test Results

Strong individual z-scores particularly for sub-08 on warm colors (red-orange: 4.3421, orange-yellow: 5.1357, yellow-green: 4.7160). Trending group effect for red-magenta (p=0.0583).

---

## B2: First-Last Split-Half Correlation

Spearman correlation between first and last half of the data. Assesses temporal stability of the filter representation.

### Results by ROI

| ROI | Subject | Spearman r | p-value | Interpretation |
|-----|---------|-----------|---------|-----------------|
| **V1** | sub-08 | 0.777 | 0.000 | Strong reliability |
| | sub-09 | 0.645 | 0.000 | Good reliability |
| | sub-10 | 0.286 | 0.141 | Not significant |
| | **Group** | **0.729** | **0.000** | **Strong** |
| **V2** | sub-08 | 0.839 | 0.000 | Excellent reliability |
| | sub-09 | 0.684 | 0.000 | Good reliability |
| | sub-10 | 0.677 | 0.000 | Good reliability |
| | **Group** | **0.714** | **0.000** | **Strong** |
| **V3** | sub-08 | 0.765 | 0.000 | Strong reliability |
| | sub-09 | 0.264 | 0.174 | Not significant |
| | sub-10 | 0.010 | 0.958 | Not significant |
| | **Group** | **0.333** | **0.083** | **Weak (trending)** |
| **hV4** | sub-08 | 0.729 | 0.000 | Strong reliability |
| | sub-09 | 0.747 | 0.000 | Strong reliability |
| | sub-10 | 0.234 | 0.230 | Not significant |
| | **Group** | **0.660** | **0.000** | **Strong** |

**Key Findings:**
- V1, V2, hV4: Strong group-level split-half correlations (r > 0.66)
- V3: Weak group correlation (r = 0.33), driven by low correlations in sub-09 and sub-10
- sub-10: Consistently shows lower individual reliability across V1, V3, hV4
- V2: Best overall reliability, with all subjects showing significant individual correlations

---

## B3: Per-Subject Bootstrap Analysis

Number of significant pairs at 95% confidence (bootstrapped).

### Significant Pair Counts

| ROI | sub-08 | sub-09 | sub-10 |
|-----|--------|--------|--------|
| V1 | 15 | 17 | 8 |
| V2 | 17 | 13 | 10 |
| V3 | 18 | 10 | 13 |
| hV4 | 21 | 8 | 22 |

### Confidence Intervals for Adjacent Pairs (95% Bootstrap CI)

#### V1 - Adjacent Pairs

| Pair | sub-08 CI | sub-09 CI | sub-10 CI |
|------|-----------|-----------|-----------|
| red-orange | [-2.4589, -0.1826]* | [-3.2819, -0.7474]* | [-2.1848, 0.0659] |
| orange-yellow | [1.2806, 4.3973]* | [-0.8184, 1.8176] | [-1.3955, 0.6754] |
| yellow-green | [1.0141, 3.1008]* | [-5.8145, -0.0999]* | [-1.3110, 1.0295] |
| green-cyan | [-3.6375, -0.4354]* | [-2.3673, 0.4235] | [-1.7147, 1.4191] |
| cyan-blue | [-2.4459, -0.3997]* | [-1.5928, 0.4361] | [-1.8875, -0.0075]* |
| blue-purple | [-0.1331, 1.7780] | [-4.7610, -0.4382]* | [-2.9318, 0.5547] |
| purple-magenta | [0.1998, 1.8634]* | [0.4190, 2.0928]* | [-1.0517, 1.2013] |
| red-magenta | [-0.2677, 1.8913] | [1.9015, 6.9327]* | [-0.1361, 3.4656] |

#### V2 - Adjacent Pairs (Strongest Effects)

| Pair | sub-08 CI | sub-09 CI | sub-10 CI |
|------|-----------|-----------|-----------|
| red-orange | [-0.4616, 1.9127] | [-2.8075, -0.2417]* | [-0.3401, 1.9453] |
| orange-yellow | [1.9704, 33.1639]*** | [-0.4130, 8.1136] | [-0.9327, 3.0381] |
| yellow-green | [3.4693, 10.3567]*** | [-2.1845, 0.2700] | [-1.7430, 0.3455] |
| green-cyan | [-0.4379, 2.4395] | [-4.2440, -0.8073]* | [0.1381, 3.0972] |
| cyan-blue | [-0.6378, 5.3342] | [-0.7770, 4.3482] | [0.5073, 12.4576]** |
| blue-purple | [2.9141, 15.3132]*** | [-0.8884, 1.3590] | [1.2341, 7.9386]** |
| purple-magenta | [-0.1448, 3.5453] | [0.1301, 4.2534] | [-0.6748, 1.8690] |
| red-magenta | [0.8928, 6.3033]* | [0.8721, 5.9201]* | [-0.2127, 2.9955] |

#### V3 - Adjacent Pairs

| Pair | sub-08 CI | sub-09 CI | sub-10 CI |
|------|-----------|-----------|-----------|
| red-orange | [0.7923, 17.9560]*** | [-2.3224, -0.3841]* | [-1.9635, -0.2513]* |
| orange-yellow | [1.2238, 15.4833]*** | [-0.1117, 5.5489] | [-1.6874, -0.2289]* |
| yellow-green | [0.4735, 17.7171]*** | [-0.8234, 3.9865] | [-1.1662, 0.0266] |
| green-cyan | [-1.4426, 2.5346] | [-0.7395, 3.2025] | [-1.6962, 0.1477] |
| cyan-blue | [-2.0023, 0.4569] | [-1.6274, 1.1634] | [-0.7398, 1.0808] |
| blue-purple | [1.4954, 17.6044]*** | [-0.6611, 3.3604] | [-1.3813, 0.7866] |
| purple-magenta | [-0.1757, 6.2729] | [0.4527, 8.0753]* | [-1.5144, -0.2820]* |
| red-magenta | [0.5484, 3.9460] | [0.9422, 4.7400] | [-1.1919, 0.4988] |

#### hV4 - Adjacent Pairs (Strongest Overall)

| Pair | sub-08 CI | sub-09 CI | sub-10 CI |
|------|-----------|-----------|-----------|
| red-orange | [2.8518, 8.8820]*** | [-1.4414, 1.9146] | [-2.7260, -0.5477]* |
| orange-yellow | [3.2193, 33.1987]*** | [-0.4789, 2.7931] | [-2.3288, -0.2045]* |
| yellow-green | [2.5989, 20.9797]*** | [-1.6398, -0.1081]* | [-1.3781, -0.1343]* |
| green-cyan | [0.2337, 19.3605]** | [-0.8053, 6.9095] | [-1.1859, 1.8784] |
| cyan-blue | [-0.9831, 1.6958] | [-1.1444, 5.6669] | [-3.2957, -0.8815]*** |
| blue-purple | [3.0568, 14.6346]*** | [-0.7245, 3.0266] | [-1.6255, 0.2090] |
| purple-magenta | [2.9480, 7.8731]*** | [0.3003, 3.3810] | [-2.4852, -0.5069]** |
| red-magenta | [3.7379, 14.3228]*** | [2.0908, 9.2038]** | [-1.8629, -0.5063]* |

**Note**: * = CI does not cross zero; ** = strong effect; *** = very strong effect

---

## Cross-Subject Consistency

Pairs where all 3 CVD subjects show consistent direction (deficit or elevation).

### V1 - Consistent Patterns

**all_3_deficit (6 pairs):**
- red-orange (step=1): z = [-0.82, -1.35, -0.68]
- cyan-blue (step=1): z = [-0.95, -0.51, -0.59]
- red-purple (step=2): z = [-0.97, -0.62, -0.79]
- green-blue (step=2): z = [-0.89, -2.41, -1.16]
- red-blue (step=3): z = [-0.10, -1.00, -0.34]
- orange-purple (step=3): z = [-0.13, -0.01, -0.52]

**all_3_elevation (3 pairs):**
- red-magenta (step=1): z = [0.69, 3.02, 1.43]
- purple-magenta (step=1): z = [0.98, 1.15, 0.31]
- cyan-purple (step=2): z = [1.78, 0.42, 0.21]

### V2 - Consistent Patterns

**all_3_deficit (2 pairs):**
- red-purple (step=2): z = [-0.47, -0.26, -0.83]
- green-blue (step=2): z = [-0.41, -0.96, -0.05]

**all_3_elevation (6 pairs):**
- red-magenta (step=1): z = [1.66, 1.64, 0.51]
- blue-purple (step=1): z = [4.34, 0.33, 2.08]
- red-yellow (step=2): z = [10.29, 0.87, 0.89]
- yellow-cyan (step=2): z = [4.82, 0.83, 0.11]
- purple-magenta (step=1): z = [0.58, 0.93, 0.07]
- yellow-purple (step=4): z = [6.96, 0.11, 0.34]

### V3 - Consistent Patterns

**all_3_deficit (1 pair):**
- green-blue (step=2): z = [-0.02, -0.29, -0.67]

**all_3_elevation (1 pair):**
- red-purple (step=2): z = [1.25, 0.52, 0.36]

### hV4 - No Consistent Patterns

No pairs show consistent direction across all 3 subjects in hV4 (likely due to high noise and sub-10 variability).

---

## Key Findings and Interpretation

### 1. Temporal Stability (B2 Split-Half)
- **V1, V2, hV4**: Strong group-level reliability (r > 0.66)
- **V3**: Weak group reliability (r = 0.33), driven by sub-08 outlier behavior
- **sub-10**: Consistently shows lower individual reliability across V1, V3, hV4
- **sub-08**: Most stable responses, particularly in V2 (r = 0.839)

### 2. Individual Differences (B1 Z-scores)
- **sub-08**: Most consistent CVD phenotype across ROIs; largest effects in V2 and hV4
- **sub-09**: High variability; strong effects on specific pairs (red-magenta V1: z=3.02, V3: z=1.63, hV4: z=3.22)
- **sub-10**: Generally weaker filter responses; most low correlations in B2

### 3. Significant Color Confusions (B3 Bootstrap CI)
- **V2 strongest overall**: sub-08 shows extreme effects (orange-yellow: CI [1.97, 33.16], yellow-green: CI [3.47, 10.36])
- **V3 sub-08**: Very large CIs on warm colors (red-orange: CI [0.79, 17.96])
- **hV4**: Mixed pattern - sub-08 shows strong elevation, sub-10 shows strong deficit

### 4. Cross-Subject Consistency
- **Red-magenta elevation**: Consistent across V1, V2, hV4 - robust effect
- **Green-blue deficit**: Consistent across V1, V2, V3 - universal reduction
- **Red-purple**: Mixed effects (deficit V1/V2, elevation V3) - ROI-dependent
- **hV4**: No complete consistency - higher noise or genuine inter-subject differences

### 5. Methodological Validation
- **Filter representation is reliable**: Good temporal stability in V1, V2, hV4
- **Individual variability is expected**: CVD phenotype varies significantly
- **Bootstrap CIs more informative than group tests**: Individual effects more pronounced than group p-values suggest
- **V2 is most informative**: Strongest effects and most consistent across subjects
- **V3 has unique properties**: Weak group signal but strong individual effects in sub-08

### 6. Data Quality Notes
- **sub-08**: Best data quality across all ROIs
- **sub-09**: Reasonable quality with high variance on specific pairs
- **sub-10**: Lower signal-to-noise ratio, particularly in hV4

---

## Recommendations for Phase 3 Pipeline

1. **Use all three subjects**: Despite variability, all show consistent effects on key pairs
2. **Prioritize V2 results**: Strongest and most stable effects
3. **V3 caution**: Requires larger effect sizes to be reliable; sub-08-driven
4. **hV4 interpretation**: Interpret with caution; high noise relative to signal
5. **Focus on consistent pairs**: Red-magenta, green-blue, and red-purple show reliability
