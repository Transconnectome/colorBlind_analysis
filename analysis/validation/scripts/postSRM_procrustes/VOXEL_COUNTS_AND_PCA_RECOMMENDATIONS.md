# Voxel Counts & PCA Dimension Recommendations

**Date**: 2026-02-08
**Analysis**: Baseline results inspection

---

## ROI Voxel Count Summary

### V1 (Primary Visual Cortex)
```
sub-01: 354 voxels
sub-02: 378 voxels
sub-03: 300 voxels ← MINIMUM
sub-04: 397 voxels
sub-05: 429 voxels
sub-06: 429 voxels
sub-08: 388 voxels
sub-09: 387 voxels
sub-10: 429 voxels

Min: 300, Max: 429, Mean: 387
```

### V2 (Secondary Visual Cortex)
```
sub-01: 250 voxels
sub-02: 256 voxels
sub-03: 234 voxels ← MINIMUM
sub-04: 262 voxels
sub-05: 279 voxels
sub-06: 279 voxels
sub-08: 261 voxels
sub-09: 245 voxels
sub-10: 279 voxels

Min: 234, Max: 279, Mean: 260
```

### V3 (Ventral Visual Area)
```
sub-01: 52 voxels
sub-02: 50 voxels ← MINIMUM
sub-03: 57 voxels
sub-04: 58 voxels
sub-05: 58 voxels
sub-06: 58 voxels
sub-08: 58 voxels
sub-09: 58 voxels
sub-10: 58 voxels

Min: 50, Max: 58, Mean: 56
```

### hV4 (Human V4, Color-Selective)
```
sub-01: 57 voxels ← MINIMUM
sub-02: 67 voxels
sub-03: 70 voxels
sub-04: 70 voxels
sub-05: 70 voxels
sub-06: 70 voxels
sub-08: 70 voxels
sub-09: 70 voxels
sub-10: 70 voxels

Min: 57, Max: 70, Mean: 67
```

---

## Critical Constraint: PCA Maximum Dimensions

**PCA limitation**: Cannot exceed min(n_samples, n_features)

For our data:
- **n_samples** = 16 (8 colors × 2 splits: odd + even patterns concatenated for PCA fitting)
- **n_features** = n_voxels

**Effective limit**: `min(16, n_voxels)` per ROI

### Actual PCA Limits per ROI

```python
max_pca_components = {
    'V1':  16,  # Limited by n_samples, not voxels (300 available)
    'V2':  16,  # Limited by n_samples, not voxels (234 available)
    'V3':  16,  # Limited by n_samples, not voxels (50 available)
    'hV4': 16,  # Limited by n_samples, not voxels (57 available)
}
```

**Conclusion**: All ROIs are constrained by **n_samples=16**, not by voxel count!

---

## PCA Dimension Recommendations

### Grid Search Candidates (Revised)

Given the n_samples=16 constraint:

```python
pca_candidates = {
    'V1':  [5, 8, 10, 12, 15, 16],   # Explore full range up to maximum
    'V2':  [5, 8, 10, 12, 15, 16],
    'V3':  [5, 8, 10, 12, 15, 16],   # Same as others (not voxel-limited)
    'hV4': [5, 8, 10, 12, 15, 16],
}
```

**Rationale**:
- **n=5-8**: Dimensionality similar to SRM (k≤8), for comparison
- **n=10-12**: Mid-range, may balance variance vs. overfitting
- **n=15-16**: Maximum possible, captures all available variance

### Current Baseline (n=50) Issue

**Problem**: `n_components=50` is **invalid** for this dataset!

From `step1a_dimension_reduction_pca.py` line 57:
```python
n_components_actual = min(n_components, n_voxels, patterns_all.shape[0])
#                                                  ^^^^^^^^^^^^^^^ = 16
```

**What actually happens**:
- User specifies `--n-components 50`
- Code silently reduces to `n_components_actual = 16`
- All current results use **n=16**, not n=50!

**Verification needed**: Check `results/step1_pca/*/sub-*_metadata.json` to confirm actual components used.

---

## Explained Variance Analysis (TODO)

Need to check current results to see variance explained by different n_components:

```bash
# Check actual components used and variance explained
for roi in V1 V2 V3 hV4; do
    echo "=== $roi ==="
    python -c "
import json
import numpy as np
from pathlib import Path

roi_dir = Path('results/step1_pca/$roi')
if roi_dir.exists():
    metadata_files = list(roi_dir.glob('sub-*_metadata.json'))
    if metadata_files:
        with open(metadata_files[0]) as f:
            data = json.load(f)
        print(f\"Actual n_components: {data.get('n_components_actual', 'N/A')}\")
        print(f\"Cumulative variance: {data.get('cumulative_variance', 'N/A')}\")

        # Load explained variance
        ev_file = metadata_files[0].parent / metadata_files[0].name.replace('metadata.json', 'explained_variance.npy')
        if ev_file.exists():
            ev = np.load(ev_file)
            print(f\"First 5 PCs: {ev[:5]}\")
            print(f\"Cumulative at n=8: {ev[:8].sum():.4f}\")
            print(f\"Cumulative at n=12: {ev[:12].sum():.4f}\")
            print(f\"Cumulative at n=16: {ev.sum():.4f}\")
"
done
```

---

## Comparison with SRM Findings

### SRM Results (from `srm/results/SRM_SUMMARY.md`)

SRM used k=3-4 features (constrained by 8 color stimuli):
- **V1**: k=4, RDM similarity 0.259 ± 0.155
- **V2**: k=4, RDM similarity 0.446 ± 0.253
- **V3**: k=3, RDM similarity 0.195 ± 0.216
- **hV4**: k=4, RDM similarity 0.031 ± 0.158

**Key issue**: Very low RDM reliability

### Expected Procrustes-PCA Improvement

With n_components=8-16 (vs SRM k=3-4):
- **More dimensions**: 2-4× more features than SRM
- **Better variance capture**: Likely >90% cumulative variance
- **Preserved geometry**: PCA orthogonal (vs SRM may distort)

**Hypothesis**: RDM reliability should increase to >0.5 (vs 0.03-0.45 in SRM)

---

## Grid Search Strategy

### Recommended Approach

**Option 1: Full Grid Search (Thorough)**
```python
# Test all 6 candidates × 4 ROIs = 24 runs
candidates = [5, 8, 10, 12, 15, 16]

for roi in ['V1', 'V2', 'V3', 'hV4']:
    for n in candidates:
        run_full_pipeline(roi, n_components=n)
        evaluate_rdm_reliability()
```

**Compute cost**: ~24 runs × 30 min = 12 hours (parallelized on server)

**Option 2: Coarse-to-Fine (Efficient)**
```python
# Phase 1: Test [5, 10, 16] to find general trend
coarse_candidates = [5, 10, 16]

# Phase 2: Refine around optimal
# If optimal at n=10, test [8, 10, 12]
# If optimal at n=16, done
# If optimal at n=5, test [5, 8] (unlikely)
```

**Compute cost**: ~12-15 runs total (6-8 hours)

### Selection Criterion

**Primary metric**: Split-half RDM reliability (from Step 3)
- Computed for each subject
- Mean across HC subjects as quality metric
- Higher reliability → better dimension choice

**Secondary metrics**:
1. Explained variance (>80% preferred)
2. HC internal consistency (ISC from Step 4)
3. Procrustes convergence speed (Step 2)

**Decision rule**:
```python
optimal_n = argmax(mean_hc_rdm_reliability[n_components])

# With minimum variance constraint
if explained_variance[optimal_n] < 0.80:
    warn("Low variance, consider increasing n_components")
```

---

## Within-Subject Analysis Constraints

For within-subject Procrustes (TODO from main TODO file):

**Challenge**: Even more limited samples per subject
- **Between-subject PCA**: Fits on 16 patterns (8 colors × 2 splits × all subjects)
- **Within-subject PCA**: Must fit on **single subject** data

**Options**:

### Option 1: Run-Concatenated PCA
```python
# Fit PCA on all 6 runs concatenated
patterns_all_runs = amplitudes_z  # (6 runs, 8 colors, n_voxels)
patterns_2d = patterns_all_runs.reshape(-1, n_voxels)  # (48, n_voxels)

# n_samples = 48 → can use higher n_components!
max_n_components_within = min(48, n_voxels)
```

**V1**: min(48, 300) = 48 ✓ Much better!
**V2**: min(48, 234) = 48 ✓
**V3**: min(48, 50) = 48 ✓
**hV4**: min(48, 57) = 48 ✓

### Option 2: Per-Run PCA (Not Recommended)
```python
# Fit PCA separately on each run
# n_samples = 8 (colors) → max n_components = 8

# Too restrictive, similar to SRM limitation
```

**Recommendation**: Use run-concatenated PCA for within-subject analysis

---

## Action Items

### Immediate
1. ✅ Verify actual n_components used in current results (check metadata.json)
2. ✅ Check explained variance curves to see if n=16 is sufficient
3. ⏳ Decide on grid search strategy (full vs coarse-to-fine)

### Short-term (This Week)
1. Implement `step0_determine_optimal_pca_dimensions.py`
2. Run grid search on V1 first (validation)
3. If promising, run all ROIs
4. Compare optimal n vs current n=16

### Medium-term (Next Week)
1. Implement within-subject pipeline with n_components=48
2. Compare within-subject vs between-subject results

---

## Expected Outcomes

### Best Case
- Optimal n_components found (likely 12-16 range)
- RDM reliability >0.6 (vs SRM 0.03-0.45)
- Clear HC-CVD separation in V2/V3 (validates SRM findings)
- Within-subject analysis confirms stability

### Worst Case
- No improvement with different n_components → Data quality issue
- RDM reliability still low (<0.4) → May need different approach
- Within-subject variability too high → Need more runs or better SNR

### Most Likely
- Moderate improvement in reliability (0.4-0.6 range)
- Optimal n_components = 12-16 (near maximum)
- V2/V3 show robust HC-CVD effects (as SRM suggested)
- Some subjects show high within-subject variability

---

**Status**: ✅ Voxel counts determined, ready for grid search implementation
**Next Step**: Check current results to verify actual n_components used
