# CRITICAL ISSUE: Classification Failure

**Date:** 2025-11-06
**Status:** 🔴 CRITICAL - Investigating

---

## 🚨 Problem

User reports: **"Even classification doesn't work"**

This is concerning because:
- Classification was previously working (70% accuracy mentioned in earlier sessions)
- If basic classification fails, reconstruction will definitely fail
- Suggests fundamental data alignment or extraction issue

---

## 🔍 Likely Causes

### 1. **ROI-Functional Misalignment** (Most Likely)
- ROI masks in wrong coordinate space (native vs MNI)
- Affine matrices don't match
- ROI masks from different subject or template

**Check with:**
```bash
python quick_roi_check.py          # Fast visual check
python diagnose_roi_alignment.py   # Comprehensive diagnostic
```

### 2. **ROI Extraction Failing**
- NiftiMasker getting all zeros or NaNs
- ROI mask not overlapping with functional data
- Wrong masking threshold

### 3. **Data Quality Issues**
- Corrupted functional data
- Wrong functional files being read
- Preprocessing artifacts

### 4. **GLM/Analysis Issues**
- Wrong event timing
- TR mismatch
- Beta estimates all zero or invalid

---

## 🛠️ Diagnostic Steps

### Step 1: Quick Visual Check (5 minutes)

```bash
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis
python quick_roi_check.py
```

This will:
- Check affine/shape alignment
- Compute overlap percentages
- Show if ROI voxels have functional data
- Create visualization: `roi_quick_check.png`

**Look for:**
- ❌ "MISALIGNED" - coordinate space mismatch
- ❌ "POOR OVERLAP" - ROIs don't overlap with brain
- ❌ "MOSTLY ZEROS" - no functional signal in ROI
- ✅ "GOOD" - alignment is fine, issue elsewhere

---

### Step 2: Comprehensive Diagnostic (10 minutes)

```bash
python diagnose_roi_alignment.py
```

This will:
1. Find functional data and ROI masks
2. Check coordinate space compatibility
3. Check spatial overlap with brain mask
4. Test NiftiMasker extraction
5. Create detailed visualizations in `roi_diagnostics/`
6. Generate diagnostic report

**Review output:**
- Section [3/6]: Coordinate space compatibility
- Section [4/6]: Spatial overlap percentages
- Section [5/6]: Voxel extraction success/failure
- Section [6/6]: Visual overlays

---

### Step 3: Identify Root Cause

Based on diagnostic output:

#### If Coordinate Space Mismatch:

**Problem:** ROI affine ≠ Functional affine

**Solutions:**
1. Check `roi_build.py` - which template space is it using?
2. Check fMRIPrep outputs - are they in MNI space?
3. Re-run ROI construction with correct space:

```python
# In roi_build.py, ensure:
# - Atlas and functional data in same space (MNI152NLin2009cAsym)
# - Correct resampling if needed
```

#### If Poor Overlap (<80%):

**Problem:** ROI doesn't overlap well with functional brain mask

**Solutions:**
1. Check registration quality in fMRIPrep QC reports
2. Try lower probability threshold in ROI construction:
   ```python
   # In roi_build.py
   PROB_THRESHOLD = 0.1  # Instead of 0.25
   ```
3. Use different atlas or manual ROI tracing

#### If Extraction Returns Zeros:

**Problem:** Functional data is zero in ROI locations

**Solutions:**
1. Check if using correct functional runs
2. Verify GLM produced valid beta estimates
3. Check for preprocessing artifacts
4. Try different runs or subjects

---

## 🔧 Quick Fixes to Try

### Fix 1: Re-check ROI Selection

```bash
python check_roi_setup.py
```

Make sure ROI masks exist and are being found correctly.

### Fix 2: Manually Verify One ROI

```python
import nibabel as nib
import numpy as np

# Load functional data
func = nib.load("output/pilot/sub-01/func/sub-01_task-colorBlind_run-1_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz")
print(f"Func shape: {func.shape}")
print(f"Func affine:\n{func.affine}")

# Load ROI mask
roi = nib.load("derivatives/sub-01/roi/sub-01_V2_mask.nii.gz")
print(f"ROI shape: {roi.shape}")
print(f"ROI affine:\n{roi.affine}")

# Check alignment
print(f"Affines match: {np.allclose(func.affine, roi.affine)}")
print(f"Shapes match: {func.shape[:3] == roi.shape[:3]}")

# Check overlap
func_data = np.mean(func.get_fdata(), axis=3)
roi_data = roi.get_fdata()
roi_mask = roi_data > 0

brain_mask = func_data > 0
overlap = np.logical_and(roi_mask, brain_mask)
print(f"ROI voxels: {np.sum(roi_mask)}")
print(f"Overlap: {np.sum(overlap)} ({np.sum(overlap)/np.sum(roi_mask)*100:.1f}%)")

# Check values
roi_values = func_data[roi_mask]
print(f"Value range in ROI: [{roi_values.min()}, {roi_values.max()}]")
print(f"Non-zero voxels: {np.sum(roi_values != 0)} / {len(roi_values)}")
```

### Fix 3: Check Results Cache

The parallel jobs might have created cache files. Check what's in them:

```bash
python inspect_cache.py hrf_test_outputs/cache_V2/reconstruction_cache.joblib
```

Look for:
- Are beta estimates valid?
- Are observed/predicted arrays all zeros?
- Are there NaN values?

---

## 📊 Expected vs Actual

### Expected (from previous sessions):
- Classification: 70% accuracy
- Reconstruction: 22.9% hit rate (p=0.401)

### Actual (current issue):
- Classification: **Not working at all**
- Reconstruction: **Likely also failing**

This **regression** suggests:
1. Something changed in ROI construction
2. Wrong files being used
3. Coordinate space mismatch introduced

---

## 🎯 Resolution Checklist

- [ ] Run `quick_roi_check.py` - identify issue category
- [ ] Run `diagnose_roi_alignment.py` - detailed diagnostic
- [ ] Review `roi_diagnostics/` visualizations
- [ ] Identify root cause from diagnostic output
- [ ] Apply appropriate fix from solutions above
- [ ] Re-run single ROI test to verify fix:
  ```bash
  # Update ROI_SELECTION = ["V2"] in naive_analysis.py
  python naive_analysis.py  # Run locally first
  ```
- [ ] If local test works, retry parallel server jobs
- [ ] Verify classification works before expecting reconstruction

---

## 💡 Key Insight

**Classification is easier than reconstruction.**

If classification fails → fundamental data problem
If classification works but reconstruction fails → model/method problem

Since classification is failing, we must fix the fundamental data issue first before worrying about reconstruction or ML/DL alternatives.

---

## 📞 Next Steps

1. **FIRST:** Run diagnostic scripts to identify exact issue
2. **THEN:** Apply appropriate fix
3. **VERIFY:** Classification works (>60% accuracy expected)
4. **ONLY THEN:** Proceed with reconstruction testing

Do NOT upload to server until local testing shows classification working.

---

## 📝 Update CURRENT_STATUS.md After Resolution

Once issue is identified and fixed:
1. Document what went wrong
2. Document the fix applied
3. Update todo list
4. Resume parallel ROI testing

---

**Status: Awaiting diagnostic results**
**Priority: CRITICAL - blocks all other work**
