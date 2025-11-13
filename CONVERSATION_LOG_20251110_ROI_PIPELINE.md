# Conversation Log - 2025-11-10: ROI Pipeline Development

## Session Overview
**Date**: November 10, 2025
**Topic**: Comprehensive ROI Pipeline with Parameter Grid Search
**Status**: Complete

---

## 1. Initial Requirements

### User Request
Create a comprehensive ROI construction pipeline that:
1. Combines Wang atlas ROI files (ventral, dorsal, left, right)
2. Transforms to functional space (MNI152NLin2009cAsym:res-2)
3. Tests all possible parameter combinations
4. Validates each combination with multiple metrics
5. Generates comprehensive visualizations

### Proposed Variables
- Threshold for probability maps
- Interpolation method
- Binarization options
- Brain mask intersection (EPI coverage)
- GM probseg intersection
- Subject-specific ROI intersection

---

## 2. Major Issues Discovered and Resolved

### Issue 1: Wang Atlas Threshold Scale ⚠️ CRITICAL
**Problem**: Initial code assumed Wang atlas probabilities were 0-1 scale
**Reality**: Wang atlas stores probabilities as 0-100 (percentage)
**Impact**: All thresholds were 100x too small!

**Before (WRONG)**:
```python
PARAM_GRID = {
    'threshold': [0.05, 0.1, 0.2, 0.3, 0.5],  # 0-1 scale
}
# This would select voxels with >0.5% probability (almost nothing!)
```

**After (CORRECT)**:
```python
PARAM_GRID = {
    'threshold': [5, 10, 20, 35, 50],  # 0-100 scale (percentage)
}
# Now correctly selects voxels with >5%, >10%, etc. probability
```

**Evidence from Past Code**:
```python
part_data = part_img.get_fdata()
part_mask = part_data > 50  # ← Uses 50, not 0.5!
```

### Issue 2: func vs epi_intersect Confusion
**Problem**: Initial implementation had both using the same mask
**Solution**: Clarified the difference and implemented correctly

**func (Anatomical Brain Mask)**:
- Source: `desc-brain_mask.nii.gz`
- Based on: T1w anatomical segmentation
- Includes: All brain tissue (even areas with signal dropout)
- Use case: Liberal masking

**epi_intersect (Actual Signal Coverage)**:
- Source: `boldref.nii.gz` (intensity-based)
- Based on: Actual EPI signal presence
- Excludes: Areas with no/weak signal (e.g., orbitofrontal cortex)
- Use case: Conservative masking (only analyzable voxels)

**Implementation**:
```python
if brain_mask_type == 'epi_intersect':
    # Use boldref intensity as mask
    intensity_threshold = np.percentile(brain_mask_data[brain_mask_data > 0], 1)
    brain_mask_data = (brain_mask_data > intensity_threshold).astype(np.float32)
```

### Issue 3: Affine Transformation Validity
**Question**: Is it appropriate to resample Wang atlas to functional space?
**Answer**: YES, validated by past code

**Why it's valid**:
1. Both are in MNI space (standard coordinate system)
2. Only difference is resolution (1mm vs 2mm)
3. Simple downsampling, not warping
4. Past code uses identical approach
5. `force_resample=True` and `copy_header=True` ensure proper handling

---

## 3. Features Added from Past Code

### Feature 1: GM Probseg Intersection
**Source**: fMRIPrep `*probseg*GM*.nii.gz`
**Threshold**: 35% GM probability (DEFAULT_GM_PROB_THRESHOLD = 0.35)
**Purpose**: Restrict ROI to gray matter only (exclude white matter, CSF)

**Implementation**:
```python
def apply_gm_probseg(self, roi_img):
    gm_probseg_path = self._get_gm_probseg()
    gm_resampled = image.resample_img(gm_img, ...)
    gm_mask = gm_data >= 0.35  # 35% threshold
    masked_data = roi_data * gm_mask
    return masked_img, metrics
```

**Parameter**: `use_gm_probseg: [True, False]`

### Feature 2: Subject-Specific ROI Intersection
**Source**: Subject's individual ROI masks in MNI space (if available)
**Purpose**: Intersection of atlas ROI with subject's own ROI

**Implementation**:
```python
def apply_subject_roi(self, roi_img, roi_name):
    subj_roi_path = self._get_subject_roi(roi_name)
    subj_resampled = image.resample_img(subj_roi_img, ...)
    masked_data = roi_data * subj_mask
    return masked_img, metrics
```

**Parameter**: `use_subject_roi: [True, False]`

---

## 4. Final Parameter Grid

```python
PARAM_GRID = {
    'threshold': [5, 10, 20, 35, 50],  # Wang atlas probability (%)
    'interpolation': ['nearest', 'linear'],  # Resampling method
    'binarize_after_resample': [True, False],  # Post-resample binarization
    'brain_mask_type': ['none', 'func', 'epi_intersect'],  # Brain masking
    'use_gm_probseg': [True, False],  # GM intersection
    'use_subject_roi': [True, False]  # Subject ROI intersection
}
```

### Total Combinations
```
4 ROIs × 5 thresholds × 2 interpolations × 2 binarize × 3 brain_mask × 2 GM × 2 subject
= 4 × 5 × 2 × 2 × 3 × 2 × 2
= 4 × 240
= 960 combinations!
```

### Expected Runtime
```
960 combinations × ~1.5 min/combination = 1440 minutes = 24 hours
```
**Recommendation**: May need to reduce parameter space or run in batches

---

## 5. Processing Pipeline

### Step-by-Step Flow
```
1. Load Wang atlas files (4 files for V1/V2/V3, 2 for hV4)
   ↓
2. Combine probabilities (union, take maximum)
   ↓
3. Apply threshold (5%, 10%, 20%, 35%, or 50%)
   ↓
4. Resample to functional space (nearest or linear)
   ↓
5. Binarize (optional, >0.5 threshold)
   ↓
6. Apply brain mask (none, func, or epi_intersect)
   ↓
7. Apply GM probseg (optional, if use_gm_probseg=True)
   ↓
8. Apply subject ROI (optional, if use_subject_roi=True)
   ↓
9. Validate (compute metrics)
   ↓
10. Visualize (4 images per combination)
    ↓
11. Save mask file
```

### Outputs per Combination
1. **NIfTI mask**: `ROI_mask_thr5_intnearest_binTrue_masknone_gmFalse_subjFalse.nii.gz`
2. **Glass brain plot**: Brain-wide view
3. **Functional overlay**: On boldref
4. **Anatomical overlay**: On T1w
5. **Probability histogram**: Distribution + threshold line

### Metrics Collected
- `n_voxels`: Final voxel count
- `original_voxels`: Before brain masking
- `masked_voxels`: After brain masking
- `overlap_ratio`: Proportion retained
- `gm_overlap_ratio`: GM intersection ratio
- `subj_roi_overlap_ratio`: Subject ROI intersection ratio
- `shape_match`: Boolean (expected shape match)
- `affine_match`: Boolean (affine matrix match)
- `coverage_pct`: Percentage of total brain volume

---

## 6. Comparison with Past Code

### Similarities ✅
| Feature | Past Code | New Code | Match |
|---------|-----------|----------|-------|
| Atlas threshold | `> 50` | `[5, 10, 20, 35, 50]` | ✅ (includes 50) |
| Interpolation | `'nearest'` | `['nearest', 'linear']` | ✅ (includes nearest) |
| Brain mask intersection | ✅ | ✅ | ✅ |
| GM probseg (35%) | ✅ | ✅ (optional) | ✅ |
| Subject ROI | ✅ | ✅ (optional) | ✅ |
| force_resample | `True` | `True` | ✅ |
| copy_header | `True` | `True` | ✅ |
| Resample to func space | ✅ | ✅ | ✅ |

### Differences (Improvements)
| Feature | Past Code | New Code | Benefit |
|---------|-----------|----------|---------|
| Thresholds tested | 1 (50%) | 5 (5-50%) | Explore sensitivity |
| Interpolation | 1 (nearest) | 2 (nearest, linear) | Compare methods |
| Binarization | Implicit | Explicit parameter | Control precision |
| Brain mask types | 1 (func) | 3 (none, func, epi) | Coverage analysis |
| GM probseg | Always on | Optional parameter | Test impact |
| Subject ROI | Always on (if avail) | Optional parameter | Test impact |
| **Total combinations** | **1** | **960** | **Comprehensive** |

---

## 7. Key Technical Decisions

### Decision 1: Resample Atlas → Functional (Not Vice Versa)
**Rationale**:
- Standard neuroimaging practice
- Past code validates this approach
- Functional space is target analysis space
- Atlas transformation is one-time cost

### Decision 2: 0-100 Scale for Thresholds
**Evidence**: Past code uses `> 50`, not `> 0.5`
**Validation**: Wang atlas documentation confirms percentage storage

### Decision 3: EPI Coverage from boldref Intensity
**Rationale**:
- No dedicated EPI coverage mask in fMRIPrep
- boldref intensity indicates signal presence
- 1st percentile threshold excludes noise
- More conservative than anatomical mask

### Decision 4: Optional GM/Subject ROI
**Rationale**:
- Test impact of each intersection separately
- Not all subjects may have these available
- Allows comparison: with vs without

---

## 8. Files Modified

### 1. `roi_pipeline_comprehensive.py`
**Changes**:
- ✅ Fixed threshold scale (0-1 → 0-100)
- ✅ Added `use_gm_probseg` parameter
- ✅ Added `use_subject_roi` parameter
- ✅ Implemented `_get_gm_probseg()` method
- ✅ Implemented `_get_subject_roi()` method
- ✅ Implemented `apply_gm_probseg()` method
- ✅ Implemented `apply_subject_roi()` method
- ✅ Updated `run_single_combination()` signature
- ✅ Updated `run_all_combinations()` parameter iteration
- ✅ Added `force_resample=True`, `copy_header=True`
- ✅ Updated param_str to include all parameters

**Lines changed**: ~150 additions/modifications

### 2. `run_roi_pipeline.sbatch`
**Changes**:
- ✅ Changed `python` → `python -u` (unbuffered output)
- ✅ Confirmed no `#SBATCH --partition` line

### 3. `analyze_roi_results.py`
**Changes**:
- ✅ Fixed `plt.close(fig)` memory leak
- ✅ Added `plt.clf()` after closes

---

## 9. Expected Results Structure

```
derivatives/pilot/sub-01/roi_pipeline_YYYYMMDD_HHMMSS/
├── results_summary.csv              # All 960 combinations × 4 ROIs = 3840 rows
├── results_full.json               # Full details
├── COMPARISON_REPORT.md            # Auto-generated report
├── comparison_plots/
│   └── voxel_count_comparison.png
├── figures/
│   ├── V1/  (960 configs × 4 images = 3840 images)
│   ├── V2/  (960 configs × 4 images = 3840 images)
│   ├── V3/  (960 configs × 4 images = 3840 images)
│   └── hV4/ (960 configs × 4 images = 3840 images)
├── V1_mask_*.nii.gz  (960 files)
├── V2_mask_*.nii.gz  (960 files)
├── V3_mask_*.nii.gz  (960 files)
└── hV4_mask_*.nii.gz (960 files)

Total files: 3840 + 3840 + 960×4 = ~19,680 files
Total size: ~20-50 GB (estimated)
```

---

## 10. Recommendations

### For Current Run
1. ✅ Use updated code with corrected threshold scale
2. ✅ Monitor log output: `tail -f logs/roi_pipeline_*.out`
3. ⚠️ Consider reducing parameter space if runtime is issue:
   - Option A: Fewer thresholds `[10, 20, 35, 50]` (4 instead of 5)
   - Option B: Only nearest interpolation (halves combinations)
   - Option C: Skip GM/Subject ROI initially (divides by 4)

### Suggested Reduced Grid for Testing
```python
PARAM_GRID_REDUCED = {
    'threshold': [20, 35, 50],  # 3 values (medium coverage)
    'interpolation': ['nearest'],  # 1 value (standard)
    'binarize_after_resample': [True],  # 1 value (standard)
    'brain_mask_type': ['func', 'epi_intersect'],  # 2 values
    'use_gm_probseg': [False, True],  # 2 values
    'use_subject_roi': [False, True]  # 2 values
}
# Total: 4 ROIs × 3 × 1 × 1 × 2 × 2 × 2 = 96 combinations
# Runtime: ~2.5 hours
```

### For Analysis
1. Load `results_summary.csv`
2. Group by ROI and compare:
   - Voxel counts across thresholds
   - Effect of GM probseg (compare `use_gm_probseg=True` vs `False`)
   - Effect of subject ROI (compare `use_subject_roi=True` vs `False`)
   - Effect of brain mask type (none vs func vs epi_intersect)
3. Identify optimal combination per ROI
4. Verify with visualizations

### For Future Work
1. Consider Bayesian optimization instead of grid search
2. Add parallel processing (multiple ROIs simultaneously)
3. Add early stopping if certain combinations clearly fail
4. Cache intermediate results (resampled atlas, brain masks)

---

## 11. Questions for User

### Resolved ✅
- [x] Wang atlas threshold scale (confirmed 0-100)
- [x] func vs epi_intersect difference (clarified)
- [x] Affine transformation validity (validated)
- [x] Past code comparison (matched)

### For Discussion
- [ ] Is 960 combinations too many? Reduce parameter space?
- [ ] Priority order: Which parameters most important to test?
- [ ] Should GM probseg and subject ROI be mandatory or optional?
- [ ] Target use case: Pilot only or all subjects?

---

## 12. Next Steps

### Immediate (Ready to Run)
```bash
# 1. Upload updated code
scp roi_pipeline_comprehensive.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp run_roi_pipeline.sbatch haba6030@node2:/scratch/connectome/haba6030/colorBlind/

# 2. Execute
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind
sbatch run_roi_pipeline.sbatch P01 1

# 3. Monitor
tail -f logs/roi_pipeline_*.out
```

### After Completion
1. Download results
2. Run `analyze_roi_results.py`
3. Review optimal configurations
4. Apply best settings to all subjects

---

## 13. Code Verification Checklist

- [x] Threshold values corrected (0-100 scale)
- [x] Past code features implemented (GM, subject ROI)
- [x] All parameters added to PARAM_GRID
- [x] run_single_combination() signature updated
- [x] run_all_combinations() iteration updated
- [x] create_visualizations() param_str updated
- [x] Save filename includes all parameters
- [x] Metrics include all intersection ratios
- [x] force_resample=True added
- [x] copy_header=True added
- [x] Python unbuffered output (-u flag)
- [x] Memory leaks fixed (plt.close(fig))

---

## Session End
**Status**: Complete
**Outcome**: Comprehensive ROI pipeline ready for execution
**Files Ready**: `roi_pipeline_comprehensive.py`, `run_roi_pipeline.sbatch`

