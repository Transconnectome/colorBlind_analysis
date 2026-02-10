# SRM Between-Subject Analysis: Preliminary Results

**Analysis Date**: 2026-02-06
**Results Directory**: `results/srm_between_subject/test_local_20260206_220129/`
**Status**: ⚠️ **PRELIMINARY** - Pending Procrustes-based validation

---

## Executive Summary

This report presents **preliminary results** from Beta-based Shared Response Mapping (SRM) for between-subject analysis comparing Healthy Controls (HC, n=6) vs Color Vision Deficient (CVD, n=3) subjects across 4 visual ROIs.

### Key Findings (Preliminary)

| ROI | HC vs CVD | p-value | Cohen's d | RDM Similarity (HC-HC) | Status |
|-----|-----------|---------|-----------|------------------------|--------|
| **V1** | Not significant | 0.309 | 0.85 | 0.259 ± 0.155 | ⚠️ Low similarity |
| **V2** | ✓ Significant | <0.001 | 6.68 | 0.446 ± 0.253 | ⚠️ Moderate similarity |
| **V3** | ✓ Significant | 0.002 | 3.71 | 0.195 ± 0.216 | ⚠️ Low similarity |
| **hV4** | Not significant | 0.553 | 0.49 | 0.031 ± 0.158 | ⚠️ Very low similarity |

### Critical Limitation

**RDM similarities across subjects are lower than expected**, indicating that the shared response space learned by SRM may not capture sufficient common variance across individuals. This suggests:

1. **Limited shared dimensions**: With only k=3-4 features (constrained by 8 color stimuli), SRM may be under-parameterized
2. **Individual variability**: High inter-subject differences in color representation
3. **Need for alternative approach**: Procrustes alignment may be more suitable for pairwise alignment

**Next Step**: Implement Procrustes-based between-subject alignment to complement SRM analysis.

---

## Method Overview

### Beta-Based SRM Approach

**Why Beta-based?**
- Only 8 color stimuli (8 samples)
- Traditional time-series SRM requires n_samples >> n_features
- Beta-based SRM: Average 6 runs → stable pattern estimates per color

**Configuration**:
```python
ROI-specific k values (k ≤ 8):
- V1: k=4 features
- V2: k=4 features
- V3: k=3 features
- hV4: k=4 features
```

**Data**:
- Source: Phase 1 Baseline (z-scored amplitudes)
- HC subjects: sub-01, sub-02, sub-03, sub-04, sub-05, sub-06
- CVD subjects: sub-08, sub-09, sub-10
- Excluded: sub-07 (HC outlier)

### Metrics Computed

1. **Procrustes Disparity**: Frobenius norm distance between patterns
   - HC-to-HC: Internal consistency of HC group
   - CVD-to-HC: Group difference
   - CVD-to-CVD: Internal consistency of CVD group

2. **RDM Similarity**: Spearman correlation between 8×8 RDMs
   - Measures structural similarity of color representation

3. **Statistical Tests**:
   - HC vs CVD: Independent t-test on disparities
   - CVD-CVD vs CVD-HC: Tests if CVD is internally consistent

---

## Detailed Results by ROI

### V1 (Primary Visual Cortex)

**SRM Configuration**: k=4 features, 6 HC + 3 CVD subjects

#### Disparity Results

| Metric | Mean ± SD | Range |
|--------|-----------|-------|
| HC-to-HC | 0.715 ± 0.178 | 0.419 - 0.938 |
| CVD-to-HC | 0.883 ± 0.216 | 0.635 - 1.161 |
| CVD-to-CVD | 1.070 ± 0.098 | 0.936 - 1.169 |

**Statistical Test**:
- HC vs CVD: t=-1.098, p=0.309 (not significant)
- CVD-CVD vs CVD-HC: t=1.113, p=0.328 (not significant)
- Effect size (Cohen's d): 0.85

#### RDM Similarity

| Comparison | Mean ± SD | n_pairs |
|------------|-----------|---------|
| HC-HC | 0.259 ± 0.155 | 15 |
| CVD-CVD | 0.118 ± 0.089 | 3 |
| HC-CVD | 0.165 ± 0.255 | 18 |

**Interpretation**:
- ⚠️ Low RDM similarity (0.259 for HC-HC) indicates limited shared structure
- No significant HC-CVD difference in V1
- CVD subjects show lower internal consistency than HC

---

### V2 (Secondary Visual Cortex)

**SRM Configuration**: k=4 features, 6 HC + 3 CVD subjects

#### Disparity Results

| Metric | Mean ± SD | Range |
|--------|-----------|-------|
| HC-to-HC | 0.498 ± 0.097 | 0.341 - 0.633 |
| CVD-to-HC | **1.162 ± 0.102** | 1.039 - 1.289 |
| CVD-to-CVD | 1.214 ± 0.049 | 1.164 - 1.280 |

**Statistical Test**:
- HC vs CVD: t=-10.45, **p<0.001** ✓ **SIGNIFICANT**
- CVD-CVD vs CVD-HC: t=0.652, p=0.549 (not significant)
- Effect size (Cohen's d): **6.68** (very large effect)

#### RDM Similarity

| Comparison | Mean ± SD | n_pairs |
|------------|-----------|---------|
| HC-HC | 0.446 ± 0.253 | 15 |
| CVD-CVD | **-0.033 ± 0.066** | 3 |
| HC-CVD | 0.153 ± 0.201 | 18 |

**Interpretation**:
- ✓ **Strongest HC-CVD difference** across all ROIs
- ⚠️ **Negative CVD-CVD RDM similarity** suggests CVD subjects have very different color representations
- V2 may be critical locus for CVD effects on color processing
- However, moderate HC-HC similarity (0.446) still indicates SRM limitations

---

### V3 (Ventral Visual Area)

**SRM Configuration**: k=3 features, 6 HC + 3 CVD subjects

#### Disparity Results

| Metric | Mean ± SD | Range |
|--------|-----------|-------|
| HC-to-HC | 0.729 ± 0.109 | 0.617 - 0.959 |
| CVD-to-HC | **1.148 ± 0.117** | 0.982 - 1.233 |
| CVD-to-CVD | 1.187 ± 0.082 | 1.073 - 1.263 |

**Statistical Test**:
- HC vs CVD: t=-4.44, **p=0.002** ✓ **SIGNIFICANT**
- CVD-CVD vs CVD-HC: t=0.384, p=0.720 (not significant)
- Effect size (Cohen's d): **3.71** (large effect)

#### RDM Similarity

| Comparison | Mean ± SD | n_pairs |
|------------|-----------|---------|
| HC-HC | 0.195 ± 0.216 | 15 |
| CVD-CVD | **-0.098 ± 0.022** | 3 |
| HC-CVD | 0.068 ± 0.174 | 18 |

**Interpretation**:
- ✓ Significant HC-CVD difference with large effect size
- ⚠️ Low HC-HC similarity (0.195) and negative CVD-CVD similarity
- V3 shows CVD effects but poor shared response model
- Lowest k=3 features may be insufficient

---

### hV4 (Human V4, Color-Selective Area)

**SRM Configuration**: k=4 features, 6 HC + 3 CVD subjects

#### Disparity Results

| Metric | Mean ± SD | Range |
|--------|-----------|-------|
| HC-to-HC | 0.864 ± 0.173 | 0.666 - 1.108 |
| CVD-to-HC | 0.954 ± 0.194 | 0.714 - 1.190 |
| CVD-to-CVD | 1.099 ± 0.129 | 0.985 - 1.280 |

**Statistical Test**:
- HC vs CVD: t=-0.621, p=0.553 (not significant)
- CVD-CVD vs CVD-HC: t=0.847, p=0.429 (not significant)
- Effect size (Cohen's d): 0.49

#### RDM Similarity

| Comparison | Mean ± SD | n_pairs |
|------------|-----------|---------|
| HC-HC | 0.031 ± 0.158 | 15 |
| CVD-CVD | 0.029 ± 0.140 | 3 |
| HC-CVD | 0.120 ± 0.262 | 18 |

**Interpretation**:
- ⚠️ **Lowest RDM similarity across all groups** (near-zero)
- No significant HC-CVD difference in hV4 (unexpected)
- hV4 is traditionally color-selective, but SRM fails to find shared structure
- High individual variability in hV4 color representation

---

## Cross-ROI Comparison

### 1. Disparity Patterns

```
Mean CVD-to-HC Disparity (Lower = More Similar to HC):
V1:  0.883 ± 0.216  (not significant)
hV4: 0.954 ± 0.194  (not significant)
V3:  1.148 ± 0.117  **p=0.002**
V2:  1.162 ± 0.102  **p<0.001** ← LARGEST DIFFERENCE
```

**Hierarchy Pattern**:
- V2 and V3 show strongest CVD effects
- V1 and hV4 show no significant differences
- CVD impact peaks in mid-level visual areas

### 2. RDM Similarity Decline Across Hierarchy

```
Mean HC-HC RDM Similarity (Higher = Better Shared Model):
V2:  0.446 ± 0.253  (best, but still moderate)
V1:  0.259 ± 0.155
V3:  0.195 ± 0.216
hV4: 0.031 ± 0.158  (worst, near-zero)
```

**Critical Finding**:
- RDM similarity **declines sharply** up the visual hierarchy
- Even best case (V2) shows only moderate similarity (r=0.446)
- Suggests **SRM shared space may be inadequate** for capturing color representation

### 3. CVD Internal Consistency

```
CVD-CVD RDM Similarity:
V1:  0.118 ± 0.089   (weak positive)
hV4: 0.029 ± 0.140   (near-zero)
V2: -0.033 ± 0.066   (negative)
V3: -0.098 ± 0.022   (negative)
```

**Interpretation**:
- CVD subjects do NOT share common representation pattern
- Negative correlations in V2/V3 suggest **heterogeneous CVD representations**
- Each CVD subject may have unique color distortions

---

## Visualization Summary

Generated visualizations for each ROI:

### 1. Disparity Comparison Plots
**Files**: `{ROI}_hc_cvd_disparity_comparison.png`

Shows 3-group boxplots:
- HC-to-HC Reference (internal HC consistency)
- CVD-to-HC Reference (group difference)
- CVD-to-CVD Pairwise (internal CVD consistency)

**Key Observation**: CVD-to-CVD disparity is often **higher than CVD-to-HC**, indicating CVD subjects are more different from each other than from HC reference.

### 2. RDM Similarity Matrices
**Files**: `{ROI}_rdm_similarity_matrix.png`

Heatmaps showing pairwise RDM correlations (Spearman r) between all subjects.

**Key Observation**:
- Weak block structure (no clear HC/CVD clustering)
- Low overall correlations confirm limited shared structure

### 3. Color Space MDS Projections
**Files**:
- `{ROI}_color_space_all_subjects.png` (grid of all subjects)
- `{ROI}_hc_vs_cvd_color_space_comparison.png` (HC vs CVD average)

Projects 8-color RDMs to 2D using Multidimensional Scaling (MDS).

**Key Observation**:
- High variability in color space structure across subjects
- No consistent HC-CVD pattern in color geometry
- Some subjects show circular arrangements, others show linear/clustered patterns

---

## Technical Limitations and Concerns

### 1. Low RDM Similarity Across Subjects

**Problem**: Even HC-HC pairs show moderate-to-low RDM correlations (r=0.03-0.45)

**Possible Causes**:
- **Insufficient k**: Only 3-4 shared dimensions may be too few
- **High noise**: Beta estimates still contain substantial noise despite run averaging
- **True variability**: Individuals may genuinely have different color coding schemes
- **SRM assumption violation**: SRM assumes linear shared + individual orthogonal space, which may not hold for color

### 2. Constraint on k (k ≤ 8)

**Problem**: With 8 color stimuli, maximum k=8 features (theoretical), but practical limit even lower

**Impact**:
- Cannot capture high-dimensional color space
- Brouwer & Heeger (2013) used continuous hue space with many more stimuli
- Our discrete 8-color design fundamentally limits SRM applicability

### 3. CVD Heterogeneity

**Problem**: CVD subjects show negative RDM correlations in V2/V3

**Implications**:
- CVD is not a homogeneous group in neural representation
- Each subject may have different compensatory strategies
- Group-level SRM may not be appropriate for CVD

### 4. Small Sample Size

**Problem**: Only 3 CVD subjects → limited statistical power

**Impact**:
- CVD-CVD statistics unreliable (n=3 pairs only)
- Cannot assess CVD subtype differences (protanopia vs deuteranopia)
- Risk of false negatives

---

## Why Procrustes May Be Better

### SRM vs Procrustes: Key Differences

| Aspect | SRM | Procrustes |
|--------|-----|------------|
| **Assumption** | Linear shared + orthogonal individual space | Affine transformation between spaces |
| **Constraint** | k ≤ n_samples (k≤8 here) | No dimensionality constraint |
| **Optimization** | Group-level shared response | Pairwise alignment |
| **Robustness** | Sensitive to outliers | More robust pairwise |
| **Interpretability** | Shared dimensions | Direct pattern matching |

### Expected Advantages of Procrustes

1. **No k constraint**: Can work with full voxel space (200-300 voxels)
2. **Pairwise flexibility**: Each CVD-HC pair optimized independently
3. **Better for heterogeneous groups**: Doesn't assume shared CVD structure
4. **Established baseline**: Phase 1 already uses Procrustes successfully

### Proposed Procrustes Approach

**Strategy**:
1. For each CVD subject, align to **each HC subject** separately
2. Compute disparity for all CVD-HC pairs (3 CVD × 6 HC = 18 pairs)
3. Compare to HC-HC baseline (15 pairs: all pairwise combinations of 6 HC)
4. Test if CVD-HC disparity > HC-HC disparity

**Advantages**:
- Leverages full voxel dimensionality
- Doesn't require shared CVD model
- Consistent with existing Phase 1 analysis

---

## Tentative Conclusions (Pending Validation)

### What We Can Conclude (Preliminary)

1. **V2 and V3 show strongest CVD effects** in Procrustes disparity
   - Effect sizes: d=6.68 (V2), d=3.71 (V3)
   - Both p<0.01

2. **CVD representations are heterogeneous**
   - Low/negative CVD-CVD RDM correlations
   - High CVD-to-CVD disparities

3. **SRM shared model is weak across all ROIs**
   - HC-HC RDM similarities range 0.03-0.45
   - Indicates limited common structure

### What We CANNOT Conclude Yet

1. ❓ Whether CVD differs from HC in **shared representational structure**
   - SRM may simply be underpowered for this dataset

2. ❓ Which colors drive HC-CVD differences
   - Need color-specific analysis with better alignment

3. ❓ Whether results generalize
   - Small sample size (n=3 CVD)
   - Single task (8-color RSVP)

---

## Next Steps

### Immediate: Implement Procrustes-Based Between-Subject Analysis

**Plan**:
1. Load Phase 1 baseline z-scored amplitudes (before Procrustes)
2. For each CVD subject:
   - Align to each HC subject using Procrustes
   - Compute disparity
3. Compare CVD-HC disparities vs HC-HC baseline
4. Color-specific analysis: Which colors show largest differences?

**Expected Timeline**: 1-2 days

**Script to Create**: `evaluate_procrustes_between_subject.py`

### Secondary: Augment SRM Analysis

If Procrustes also shows low consistency:

1. **Try higher k values** with different validation approach
   - Use cross-validation on runs instead of colors
   - May allow k>8

2. **Alternative dimensionality reduction**
   - PCA on voxel patterns
   - Compare PC structure between HC and CVD

3. **Searchlight SRM**
   - Apply SRM locally within voxel neighborhoods
   - May capture local structure better

---

## Data Availability

### Result Files

**Location**: `/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/validation/scripts/results/srm_between_subject/test_local_20260206_220129/`

**Files per ROI** (V1, V2, V3, hV4):
- `{ROI}_srm_between_subject_results.json` - Numerical results
- `{ROI}_aligned_amplitudes.npy` - SRM-aligned patterns (for visualization)
- `{ROI}_hc_cvd_disparity_comparison.png` - Boxplot
- `{ROI}_rdm_similarity_matrix.png` - Heatmap
- `{ROI}_color_space_all_subjects.png` - MDS grid
- `{ROI}_hc_vs_cvd_color_space_comparison.png` - HC vs CVD MDS
- `{ROI}_log.txt` - Console output

### Code

**Scripts Used**:
- `evaluate_srm_between_subject.py` - Main analysis
- `visualize_color_space_per_subject.py` - MDS visualization
- `utils/srm_alignment.py` - Beta-based SRM implementation
- `run_srm_between_subject_local_test.sh` - Execution wrapper

**Git Status**: Local modifications, not yet committed

---

## References

**SRM Method**:
- Chen et al. (2015). A Reduced-Dimension fMRI Shared Response Model. NIPS.
- BrainIAK implementation: https://brainiak.org/

**Color Vision**:
- Brouwer & Heeger (2009). Decoding and Reconstructing Color from Responses in Human Visual Cortex. J Neurosci.
- Brouwer & Heeger (2013). Categorical Clustering of the Neural Representation of Color. J Neurosci.

**Procrustes**:
- Gower & Dijksterhuis (2004). Procrustes Problems. Oxford University Press.

---

## Appendix: Metric Definitions

### Procrustes Disparity
```
disparity = ||P - Q||_F / sqrt(n_colors × n_features)
```
where P, Q are patterns (n_colors × n_features) after optimal rotation/scaling alignment.

### RDM Similarity
```
RDM_ij = 1 - corr(pattern_i, pattern_j)  for all color pairs i,j
similarity = spearman_r(RDM_subject1, RDM_subject2)
```
Measures structural similarity of 8×8 color dissimilarity matrices.

### Cohen's d
```
d = (mean_CVD - mean_HC) / pooled_std
```
Effect size for group comparison.

---

**Report Status**: ⚠️ PRELIMINARY - Requires Procrustes validation
**Generated**: 2026-02-06
**Author**: Automated analysis pipeline
**Contact**: For questions about methodology or interpretation, review analysis scripts in `/analysis/validation/scripts/`
