# Native BOLD Space ROI Pipeline - Results Diagnosis

**Date**: 2025-01-04
**Analysis**: Batch job results from run_native_roi_pipeline.sbatch (Job ID: 70412)
**Total Jobs**: 28 (7 subjects × 4 ROIs)

---

## Executive Summary

**CRITICAL FINDING**: The native BOLD space ROI pipeline revealed that MNI→T1w transformation failures affect **6 out of 7 non-CVD subjects** and **2 out of 3 CVD subjects**.

**Success Rate**:
- **Complete pipeline success**: 1/28 (3.6%) - Only sub-02 V1
- **T1w transformation success**: 6/28 (21.4%)
- **Overall failure rate**: 96.4%

**Core Issue**: The hypothesis that "analysis can proceed in native functional space even if MNI is broken" is **NOT confirmed** - the MNI→T1w transformation itself is failing, preventing native space analysis.

---

## Detailed Results by Transformation Stage

### Stage 1: MNI → T1w Native Transformation

| Subject | V1 Status | V2 Status | V3 Status | hV4 Status | Notes |
|---------|-----------|-----------|-----------|------------|-------|
| sub-01  | ❌ 0 vox  | ❌ 0 vox  | ❌ 0 vox  | ❌ 0 vox   | Complete failure |
| sub-02  | ✅ 305K   | ✅ 367K   | ✅ 408K   | ✅ 165K    | **All ROIs successful** |
| sub-03  | ❌ 0 vox  | ❌ 0 vox  | ❌ 0 vox  | ❌ 0 vox   | Complete failure |
| sub-05  | ❌ 0 vox  | ❌ 0 vox  | ❌ 0 vox  | ❌ 0 vox   | Complete failure |
| sub-06  | ❌ 0 vox  | ❌ 0 vox  | ❌ 0 vox  | ❌ 0 vox   | Complete failure |
| sub-07  | ❌ 0 vox  | ❌ 0 vox  | ❌ 0 vox  | ❌ 0 vox   | Complete failure |
| sub-08  | ⚠️ 25M    | ❌ 0 vox  | ❌ 0 vox  | ✅ 183K    | Abnormally large V1 |

**Interpretation**:
- Only **sub-02** shows consistent successful transformations across all ROIs
- **sub-08** has partial success but V1 voxel count (25 million) is abnormally high (suggests transformation error)
- **5 subjects** (sub-01, 03, 05, 06, 07) have complete failure at this stage

### Stage 2: T1w → BOLD Native Transformation

For the 6 cases that passed Stage 1:

| Subject | ROI  | T1w Voxels | BOLD Voxels | Mask Voxels | Status |
|---------|------|------------|-------------|-------------|--------|
| sub-02  | V1   | 305,002    | 4,962       | 1,233       | ✅ SUCCESS |
| sub-02  | V2   | 366,907    | 0           | 0           | ❌ Failed |
| sub-02  | V3   | 408,416    | 0           | 0           | ❌ Failed |
| sub-02  | hV4  | 164,913    | 0           | 0           | ❌ Failed |
| sub-08  | V1   | 25,271,129 | 0           | 0           | ❌ Failed |
| sub-08  | hV4  | 182,701    | 0           | 0           | ❌ Failed |

**Interpretation**:
- Only **sub-02 V1** completed the full pipeline successfully (1,233 voxels in binary mask)
- The T1w→BOLD transformation is failing even when T1w transformation succeeds
- This suggests additional issues beyond MNI registration quality

---

## QC Image Analysis

**Generated QC Images**: 1/28
- Only `sub-02_V1_overlay.png` was successfully created

**Visual Inspection of sub-02 V1**:
- ⚠️ **WARNING**: ROI center is NOT in posterior occipital cortex
- Location: Y = -47.9mm (threshold for visual cortex: Y < -50mm)
- ROI appears to be located more anteriorly than expected for V1
- **Recommendation**: Manual inspection strongly recommended despite "success" status

---

## Root Cause Analysis

### 1. MNI→T1w Transformation Failures (Subjects 01, 03, 05, 06, 07)

**Possible Causes**:
- Broken or missing ANTs warp files (`*_from-MNI152NLin2009cAsym_to-T1w_mode-image_xfm.h5`)
- fMRIPrep registration quality issues (already documented in previous analyses)
- Incompatible atlas space vs. subject MNI space

**Evidence**:
- All jobs found the transform file (✓ in logs)
- ANTs command executed without errors
- Output produced 0 voxels (suggesting transformation produced empty image)

### 2. T1w→BOLD Transformation Failures (sub-02 V2/V3/hV4, sub-08 V1/hV4)

**Possible Causes**:
- BOLD reference image quality issues
- Missing or incorrect `boldref_to-T1w` transform files
- ROI falling outside BOLD field of view after transformation
- Threshold too high (>20) for probabilistic ROIs

**Evidence**:
- Jobs stopped/hung after "BOLD-native ROI created: 0 voxels"
- No completion of Step 5 (binary mask creation)
- Log files truncated (45-51 lines vs. 148 for success)

---

## Implications for Analysis Plan

### Original Hypothesis
> "MNI가 깨져 있어도, native functional에서는 분석이 성립하는가?"
> (Can analysis proceed in native functional space even if MNI is broken?)

### Answer
**NO - The MNI→T1w transformation is the bottleneck**, not the final MNI normalization step.

The pipeline tested:
```
MNI Atlas ROI → T1w native → BOLD native
```

But the failure occurs at the **first step** (MNI→T1w), which still depends on fMRIPrep's MNI registration quality.

### Why This Matters
- **Cannot bypass MNI issues**: Native space analysis still requires working MNI→T1w transforms
- **Hyperalignment/Procrustes still viable**: These methods don't need ROI transformation, only functional data alignment
- **Alternative approach needed**: Either fix fMRIPrep registration or use functional localizer for ROI definition

---

## Recommendations

### Immediate Actions

1. **Verify sub-02 V1 ROI location**
   ```bash
   # View the QC image
   open native_roi_report/images/sub-02_V1_overlay.png
   ```
   - Check if ROI is actually in visual cortex despite Y > -50mm warning
   - If location is acceptable, proceed with functional analysis for sub-02 V1 only

2. **Investigate why only sub-02 succeeded**
   ```bash
   # Compare sub-02 vs sub-03 transform files
   ls -lh /storage/connectome/haba6030/fmriprep_out_original_v3/sub-02/anat/*xfm*
   ls -lh /storage/connectome/haba6030/fmriprep_out_original_v3/sub-03/anat/*xfm*

   # Check fMRIPrep HTML reports for registration quality
   ```

3. **Test lower threshold for binary mask**
   - Current threshold: 20 (very high for probabilistic atlas)
   - Try threshold: 5 or 10
   - This might recover sub-02 V2/V3/hV4 and sub-08 hV4

### Alternative Approaches

#### Option A: Fix fMRIPrep Registration
- Re-run fMRIPrep with different registration settings
- Use --force-syn flag for more robust normalization
- Try different template (fsaverage instead of MNI)

#### Option B: Functional Localizer
- Use functional contrast (color > gray) to define ROIs in native space
- Combine with anatomical constraints (calcarine sulcus location)
- No dependence on MNI registration at all

#### Option C: Surface-Based Analysis
- Use fMRIPrep's surface outputs (fsaverage space)
- Wang atlas is available in surface format
- Better anatomical correspondence than volume registration

#### Option D: Proceed with Working Cases Only
- Use sub-02 V1 (and possibly others after threshold adjustment)
- Limited to subjects with successful transformations
- Not suitable for group-level analysis

---

## Next Steps for Travel Review

### 1. Visual QC Checklist
- [ ] Open `native_roi_report/native_roi_report.html`
- [ ] Examine sub-02 V1 overlay image
- [ ] Determine if ROI location is acceptable despite Y > -50mm

### 2. Decision Points

**If sub-02 V1 ROI location is acceptable:**
- Proceed with functional analysis for sub-02 V1 only
- Document as proof-of-concept for native space approach
- Plan re-run with lower threshold to recover more ROIs

**If sub-02 V1 ROI location is NOT acceptable:**
- Native space approach via MNI transformation is not viable
- Pivot to Alternative Approach B (Functional Localizer) or C (Surface-Based)

### 3. Questions to Answer During Review

1. Why did only sub-02 succeed? What's different about this subject's fMRIPrep output?
2. Is the threshold=20 too conservative? Would threshold=10 work better?
3. Should we abandon volume-based analysis entirely and use surface-based?
4. Can we use functional localizer instead of anatomical atlas?

---

## Files for Offline Review

All files are in `native_roi_report/`:
- **native_roi_report.html** - Interactive report with all visualizations
- **results_summary.csv** - Tabular results
- **logs_summary.csv** - Job status summary
- **images/sub-02_V1_overlay.png** - Only successful QC image
- **logs/** - All 28 SLURM job logs for detailed debugging

---

## Conclusion

The native BOLD space ROI pipeline has **largely failed** due to broken MNI→T1w transformations in fMRIPrep output. This is the same underlying issue affecting MNI-space analysis.

**Key Insight**: The problem is not "can we work in native space?" but rather "can we transform atlas ROIs to individual anatomy?" The answer appears to be **no** for most subjects with the current fMRIPrep outputs.

**Path Forward**: Consider functional localizer or surface-based approaches that don't depend on volume-based MNI transformations.
