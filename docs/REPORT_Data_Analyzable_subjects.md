# Analyzable Subjects Report

**Date**: 2025-12-12
**Analysis**: ROI Alignment Diagnostics (Jobs 67066-67143)
**Status**: Subject exclusion criteria determined

---

## 📊 Summary

### Analyzable Subjects (Total: 9/10)

**Non-CVD subjects**: sub-01, sub-02, sub-03, sub-05, sub-06, sub-07 (6 subjects)
**CVD subjects**: sub-08, sub-09, sub-10 (3 subjects)

### Excluded Subjects (Total: 1/10)

**sub-04**: No BOLD signal at V1 atlas location (to be recovered in future)

---

## 🔬 Diagnostic Results Summary

### Successfully Analyzed Subjects

| Subject | Group | V1 Overlap | Status | Notes |
|---------|-------|------------|--------|-------|
| sub-01 | Non-CVD | 100.0% | ✅ Works | Full overlap |
| sub-02 | Non-CVD | 18.7% | ✅ Works | Partial overlap |
| sub-03 | Non-CVD | 0% → 81.1% signal | ✅ Recoverable | BOLD signal exists, brain mask issue |
| sub-05 | Non-CVD | 71.1% | ✅ Works | Good overlap |
| sub-06 | Non-CVD | 93.9% | ✅ Works | Excellent overlap |
| sub-07 | Non-CVD | 96.9% | ✅ Works | Excellent overlap |
| sub-08 | CVD | 59.3% | ✅ Works | Moderate overlap |
| sub-09 | CVD | 0% → 81.7% signal | ✅ Recoverable | BOLD signal exists, brain mask issue |
| sub-10 | CVD | 0% → 64.3% signal | ✅ Recoverable | BOLD signal exists, brain mask issue |

### Excluded Subject

| Subject | Group | V1 Overlap | BOLD Signal | Status | Reason |
|---------|-------|------------|-------------|--------|--------|
| sub-04 | Non-CVD | 0% | 0% (zeros) | ❌ Excluded | No actual BOLD data at V1 location |

---

## 🎯 Root Cause Analysis

### Problem Identification

**Initial Issue**: 5/10 subjects (sub-02, 03, 04, 09, 10) had 0% V1 ROI overlap when using `brain_mask_type='func'`

**Diagnostic Process**:
1. Verified coordinate space consistency → All subjects in same space ✅
2. Checked atlas alignment → 2mm atlas properly aligned ✅
3. Examined functional brain masks → Too conservative, excluded posterior visual cortex ⚠️
4. Verified BOLD data masking → fMRIPrep output NOT pre-masked ✅
5. Checked BOLD signal at V1 locations → Signal exists in 4/5 subjects ✅

### Root Causes Identified

#### Primary Cause: fMRIPrep Functional Brain Mask Too Conservative

**Affected subjects**: sub-03, sub-09, sub-10

**Evidence**:
- Functional brain mask excludes V1 locations (mask=0 at all V1 voxels)
- BOLD signal DOES exist at V1 locations:
  - sub-03: 81.1% of V1 voxels have non-zero signal (Mean=49.17)
  - sub-09: 81.7% of V1 voxels have non-zero signal (Mean=4.88)
  - sub-10: 64.3% of V1 voxels have non-zero signal (Mean=7.77)

**Why this happens**:
- fMRIPrep brain mask based on temporal variance
- Posterior visual cortex may have lower baseline signal
- Conservative thresholding excludes valid brain tissue

**Solution**: Use `brain_mask_type='none'` to bypass functional brain mask

#### Secondary Cause: Actual BOLD Signal Absence

**Affected subject**: sub-04

**Evidence**:
- Functional brain mask excludes V1 (mask=0 at all V1 voxels)
- BOLD signal DOES NOT exist: All timepoints are exactly 0
- Unlike sub-03/09/10, no recoverable signal

**Likely causes**:
- Insufficient EPI coverage of posterior visual cortex
- Signal dropout in that region
- Acquisition/reconstruction issue

**Solution**: Currently not recoverable - exclude from analysis (future investigation needed)

---

## ✅ Solution Implementation

### Configuration Changes Required

```python
# roi_pipeline_selected_1202used.py
PARAM_GRID = {
    'threshold': [50],
    'interpolation': ['nearest'],
    'binarize_after_resample': [True],
    'brain_mask_type': ['none'],      # ✅ Already applied
    'use_gm_probseg': [False],        # ⚠️ Need to add
    'use_subject_roi': [False]
}
```

### Why These Settings Work

**`brain_mask_type='none'`**:
- Bypasses fMRIPrep functional brain mask
- Allows extraction of BOLD signal from all V1 atlas voxels
- fMRIPrep BOLD output is NOT pre-masked (verified)
- Signal exists at V1 locations (sub-03/09/10)

**`use_gm_probseg=False`**:
- Removes gray matter probability segmentation threshold
- Prevents additional voxel exclusion
- GM probseg may also be conservative in visual cortex

### Expected Results After Fix

**Current (with mask=func)**:
```
sub-03: V1 = 0 voxels (excluded by brain mask)
sub-09: V1 = 0 voxels (excluded by brain mask)
sub-10: V1 = 0 voxels (excluded by brain mask)
```

**After fix (with mask=none, no GM probseg)**:
```
sub-03: V1 ≈ 2,600 voxels (81% of 3,256)
sub-09: V1 ≈ 2,660 voxels (82% of 3,256)
sub-10: V1 ≈ 2,100 voxels (64% of 3,256)
```

---

## 📋 Next Steps

### Immediate Actions

1. **Modify ROI pipeline configuration**:
   - Add `use_gm_probseg: [False]` to PARAM_GRID
   - Keep `brain_mask_type: ['none']`

2. **Re-run ROI pipeline for recovered subjects**:
   ```bash
   for subj in 03 09 10; do
       sbatch run_roi_pipeline_selectedOnly.sbatch $subj 1
   done
   ```

3. **Verify voxel counts**:
   - Check log files for V1 voxel counts
   - Expected: 2,000-2,600 voxels per subject

4. **Proceed with baseline analysis** on 9 subjects:
   - Non-CVD: 01, 02, 03, 05, 06, 07
   - CVD: 08, 09, 10

### Future: Recover sub-04

**Investigation needed**:
1. Review original DICOM files for EPI coverage
2. Check fMRIPrep HTML report for registration quality
3. Examine raw BOLD signal across entire brain
4. Consider alternative preprocessing approaches
5. If irrecoverable, document as data quality exclusion

**Potential approaches**:
- Use less restrictive fMRIPrep settings
- Manual inspection of raw EPI coverage
- Alternative atlas registration methods
- Subject-specific ROI if sufficient signal exists elsewhere

---

## 📄 Related Documentation

- **Coordinate Space Diagnosis**: `logs/diagnostics/coordinate_space_diagnosis.txt`
- **Brain Mask Verification**: `logs/diagnostics/brain_mask_verification.txt`
- **BOLD Masking Check**: `logs/diagnostics/bold_masking_check.txt`
- **Alignment Report**: `ALIGNMENT_DIAGNOSTICS_FINAL_REPORT.md`
- **Main Project Guide**: `CLAUDE.md`
- **fMRIPrep Guide**: `docs/GUIDE_to_fMRIprep.md`
- **Analysis Guide**: `docs/GUIDE_to_classify_reconstruct.md`

---

**Report Generated**: 2025-12-12
**Status**: Subject exclusion criteria finalized ✅
**Next Milestone**: Baseline analysis with 9 subjects
