# TODO: postSRM_procrustes Pipeline Enhancements

**Date**: 2026-02-08
**Status**: Planning Phase

---

## 🎯 Priority 1: PCA Dimension Grid Search

### Current Limitation
- PCA n_components fixed at 50 (default)
- Not optimized per ROI
- May lose information when voxel count > 50

### Proposed Enhancement

#### 1.1 Determine Maximum Dimension per ROI
```python
# For each ROI, find minimum voxel count across all subjects
max_n_components = {
    'V1': min([voxel_count_sub01_V1, ..., voxel_count_sub10_V1]),
    'V2': min([voxel_count_sub01_V2, ..., voxel_count_sub10_V2]),
    'V3': min([...]),
    'hV4': min([...])
}
```

**Rationale**:
- Procrustes requires same dimensionality across subjects
- Maximum safe dimension = minimum voxel count
- Avoids information loss for high-voxel subjects

#### 1.2 Grid Search Candidates
```python
# For each ROI, test multiple n_components
candidates = {
    'V1': [20, 30, 50, 75, 100, max_n_components['V1']],
    'V2': [20, 30, 50, 75, 100, max_n_components['V2']],
    'V3': [20, 30, 50, 75, 100, max_n_components['V3']],
    'hV4': [20, 30, 50, 75, 100, max_n_components['hV4']]
}
```

Filter: Remove candidates > max_n_components

#### 1.3 Selection Criterion
Evaluate each n_components by:
1. **Explained variance**: >80% cumulative variance
2. **RDM reliability**: Split-half correlation (Step 3)
3. **HC internal consistency**: Mean ISC within HC group (Step 4)
4. **Procrustes convergence**: Fewer iterations better (Step 2)

**Recommended metric**: RDM reliability (most direct measure of signal quality)

#### 1.4 Implementation Plan

**New Script**: `step0_determine_optimal_pca_dimensions.py`

```bash
# For each ROI, run full pipeline with multiple n_components
# Select optimal based on RDM reliability

python step0_determine_optimal_pca_dimensions.py \
    --roi V1 \
    --n-components-candidates 20 30 50 75 100 \
    --metric rdm_reliability \
    --output optimal_dimensions.json
```

**Output**:
```json
{
    "V1": {
        "optimal_n_components": 75,
        "max_possible": 129,
        "rdm_reliability": 0.78,
        "explained_variance": 0.92
    },
    "V2": {...},
    ...
}
```

**Timeline**: 2-3 days
**Priority**: High (may significantly improve results)

---

## 🎯 Priority 2: ANOVA Voxel Selection Grid Search

### Current Limitation
- ANOVA k fixed at 500 (default in step1b)
- Not optimized per ROI

### Proposed Enhancement

#### 2.1 Grid Search Candidates
```python
# Test multiple voxel selection sizes
anova_candidates = {
    'V1': [100, 200, 300, 500, min_voxel_count_V1],
    'V2': [100, 200, 300, 500, min_voxel_count_V2],
    'V3': [...],
    'hV4': [...]
}
```

#### 2.2 Selection Criterion
Same as PCA: RDM reliability

**Note**: ANOVA may be less critical since PCA is recommended (preserves geometry)

**Timeline**: 1-2 days
**Priority**: Medium

---

## 🎯 Priority 3: Within-Subject Procrustes Analysis

### Current Limitation
- Only between-subject analysis (HC template → all subjects)
- No within-subject run-to-run alignment

### Proposed Enhancement

#### 3.1 Within-Subject Procrustes
**Goal**: Align runs within each subject, similar to Phase 1 baseline

**Method**:
1. For each subject independently:
   - Use runs 1-5 as template (leave-one-run-out)
   - Align run 6 to template
   - Rotate through all 6 runs
2. Compute within-subject consistency metrics

#### 3.2 Expected Benefits
- Compare within-subject vs between-subject alignment quality
- Assess individual stability of color representation
- Identify subjects with high run-to-run variability

#### 3.3 Metrics to Compute
- **Within-subject RDM reliability**: Across runs (better than odd-even split)
- **Run-to-run disparity**: Procrustes distance between runs
- **Stability metric**: Coefficient of variation of disparities

#### 3.4 HC vs CVD Comparison
- **Hypothesis**: CVD may show higher within-subject variability
- Compare HC vs CVD within-subject stability

#### 3.5 Implementation Plan

**New Scripts**:
1. `step1_within_subject_pca.py` - PCA per subject per run
2. `step2_within_subject_procrustes.py` - LORO alignment
3. `step3_within_subject_rdms.py` - Run-wise RDMs
4. `step4_within_subject_metrics.py` - Stability metrics

**Execution**:
```bash
# Example: sub-01, V1
python step1_within_subject_pca.py --subject 01 --roi V1 --n-components 50

# LORO Procrustes (6 folds)
python step2_within_subject_procrustes.py --subject 01 --roi V1

# RDM per run
python step3_within_subject_rdms.py --subject 01 --roi V1

# Stability metrics
python step4_within_subject_metrics.py --roi V1  # All subjects
```

**Output**:
```
results/within_subject/
├── V1/
│   ├── sub-01_run_stability.json
│   │   {
│   │     "mean_disparity": 0.25,
│   │     "std_disparity": 0.08,
│   │     "rdm_reliability_runs": 0.82,
│   │     "stability_score": 0.91
│   │   }
│   ├── within_vs_between_comparison.json
│   └── hc_vs_cvd_stability_statistics.json
```

**Timeline**: 3-4 days
**Priority**: Medium-High (provides complementary validation)

#### 3.6 Within vs Between Comparison
Compare metrics:
- Within-subject stability (run variability)
- Between-subject HC-CVD differences (group effects)

**Key Question**: Are CVD differences larger than run-to-run noise?

---

## 📊 Expected Improvements Summary

| Enhancement | Impact | Effort | Priority |
|-------------|--------|--------|----------|
| **PCA dimension grid search** | High (may improve reliability by 20-30%) | Medium (2-3 days) | **High** |
| **ANOVA grid search** | Medium (comparison method) | Low (1-2 days) | Medium |
| **Within-subject analysis** | High (validates between-subject findings) | Medium-High (3-4 days) | Medium-High |

---

## 🚀 Implementation Roadmap

### Phase 1: PCA Optimization (Week 1)
1. Create `step0_determine_optimal_pca_dimensions.py`
2. Run grid search for all ROIs locally (test on V1 first)
3. Select optimal n_components per ROI
4. Re-run full pipeline with optimal dimensions
5. Compare with n_components=50 baseline

### Phase 2: Within-Subject Analysis (Week 2)
1. Implement within-subject scripts (steps 1-4)
2. Run locally for all subjects, all ROIs
3. Compute stability metrics
4. Compare with between-subject results

### Phase 3: ANOVA Comparison (Optional)
1. Grid search for ANOVA k values
2. Compare PCA vs ANOVA methods

---

## 🔍 Validation Criteria

### Success Metrics
1. **PCA optimization**:
   - RDM reliability increases by >10%
   - Explained variance >85%
   - HC-CVD separation improves (larger effect size)

2. **Within-subject analysis**:
   - Within-subject stability high (reliability >0.7)
   - Between-subject HC-CVD differences > within-subject noise
   - CVD shows lower stability than HC (hypothesis)

### Failure Criteria (Reconsider Approach)
1. PCA optimization shows no improvement → May indicate fundamental signal quality issue
2. Within-subject variability > between-subject differences → Need higher SNR data
3. CVD stability same as HC → CVD differences are representational, not noisy

---

## 📚 References

**PCA for fMRI**:
- Brouwer & Heeger (2009). Preserves geometry via orthogonal transformation
- Cumulative variance threshold: 80-90% standard

**Within-Subject Reliability**:
- Guntupalli et al. (2018). Leave-one-run-out for stability assessment
- Correlation-based reliability: Split-half vs run-wise

**Dimension Selection**:
- Bro & Smilde (2014). Cross-validation for component selection
- Explained variance plateau as heuristic

---

## ✅ Checklist Before Starting

- [ ] Determine min voxel counts per ROI (check baseline results)
- [ ] Confirm baseline data has all 6 runs per subject
- [ ] Verify current pipeline runs successfully with n_components=50
- [ ] Allocate compute resources (grid search is compute-intensive)
- [ ] Set up parallel execution (SLURM array jobs for server)

---

## 💡 Notes

- **Grid search cost**: ~6 n_components × 4 ROIs = 24 full pipeline runs
  - Estimate: 2-3 hours per run on server → 48-72 hours total
  - Parallelize with SLURM array jobs

- **Within-subject compatibility**: Can run in parallel with current between-subject pipeline (different output directories)

- **Dimension selection literature**: Most studies use 50-100 PCs for fMRI, but optimal varies by SNR and ROI size

---

**Status**: ⏳ TODO - Awaiting approval to proceed
**Next Step**: Determine min voxel counts and create `step0_determine_optimal_pca_dimensions.py`
