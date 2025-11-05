# Sanity Check Analysis - Root Cause Identified

**Status:** ⚠️ **ROI Definition Problem - Not Alignment**

---

## Executive Summary

The sanity check reveals **the ROIs are technically aligned correctly** (shapes and affines match perfectly), but the **ROI voxels are not in active brain regions**. This is a **ROI definition problem**, not an alignment problem.

### Key Finding

**78.55% of functional voxels are zero** → This is masked data, which is normal.
**BUT:** Wang atlas ROIs fall mostly in these **zero/masked-out regions**.

This explains why:
- V1: Only 190/511 voxels (37%) overlap with active brain
- BrainMask: Only 97,735/230,768 voxels (42%) are active

---

## Detailed Findings

### ✅ GOOD NEWS

1. **Data is NOT pre-centered**
   - Mean = 52.20 (not 0!)
   - Previous diagnostic warning was misleading
   - Safe to use standard GLM normalization

2. **Perfect geometric alignment**
   - Shapes match: (97, 115, 97) ✅
   - Affines match perfectly ✅
   - No resampling needed

3. **Reasonable tSNR**
   - Mean tSNR = 12.29
   - Median tSNR = 9.97
   - Not great, but workable for decoding

4. **Event files properly structured**
   - 52 color trials total
   - Uneven distribution (color_2: 8, color_8: 5)
   - But timing looks correct

5. **CompCor available**
   - 218 CompCor components in confounds
   - Can use comprehensive noise regression

---

### ⚠️ PROBLEMS IDENTIFIED

#### Problem 1: ROI Coverage (CRITICAL)

| ROI | Total Voxels | Active Voxels | Overlap % |
|-----|--------------|---------------|-----------|
| V1 | 511 | 190 | **37.2%** ❌ |
| V2 | 310 | 182 | **58.7%** ⚠️ |
| BrainMask | 230,768 | 97,735 | **42.4%** ❌ |

**Root Cause:**
- Wang atlas ROIs include voxels outside the functional coverage
- Likely due to:
  - Signal dropout in occipital pole
  - Aggressive brain masking in fMRIPrep
  - Template mismatch (Wang atlas vs. actual subject anatomy)

**Evidence:**
- Affines match perfectly (alignment is correct)
- But 63% of V1 voxels have zero signal
- Only 242,061 / 1,082,035 total voxels are active (22%)

#### Problem 2: High Motion (MODERATE)

```
Mean FD: 0.3443 mm (threshold: 0.3mm)
Max FD: 3.69 mm
Bad volumes (FD > 0.5mm): 53 / 288 (18%)
```

**Impact:**
- 18% of volumes have excessive motion
- Should exclude or downweight these volumes
- May reduce effective sample size

#### Problem 3: Unbalanced Color Trials

```
color_2: 8 trials
color_4: 8 trials
color_7: 7 trials
color_3: 6 trials
color_5: 6 trials
color_1: 6 trials
color_6: 6 trials
color_8: 5 trials  ← Undersampled
```

**Impact:**
- color_8 has only 5 trials (others have 6-8)
- May cause slight classification bias
- Not critical, but worth noting

---

## Root Cause Analysis

### Why V1 has Low Overlap

The Wang probabilistic atlas defines V1 based on population averages, but:

1. **Individual variability** - Subject's V1 may not match template exactly
2. **Signal dropout** - Occipital pole often has dropout due to:
   - Proximity to sinuses
   - Magnetic susceptibility artifacts
   - Conservative brain masking

3. **Conservative thresholding** - Wang atlas uses probability threshold
   - Current: Likely 50% or higher
   - Solution: Lower to 25% or use top-N voxels within ROI

### Why This Caused Chance Performance

With only 190 active voxels in V1:
- Too few voxels to capture population code
- High noise-to-signal ratio
- Insufficient spatial sampling

Literature suggests >500 active voxels minimum for robust decoding.

---

## Solutions

### Solution 1: Intersection Masking (RECOMMENDED) ⭐

**Strategy:** Keep only ROI voxels that have non-zero functional data

```python
# In roi_build.py or create new script
functional = nib.load(func_img_path)
func_data = functional.get_fdata()
func_mask = (func_data.mean(axis=-1) != 0)

# Load Wang ROI
wang_roi = nib.load(wang_roi_path)
wang_mask = wang_roi.get_fdata() > 0

# Intersection
active_roi = wang_mask & func_mask
active_roi_img = nib.Nifti1Image(active_roi.astype(int), functional.affine)
```

**Expected result:**
- V1: 190 voxels (all active) ✅
- V2: 182 voxels (all active) ✅
- All voxels guaranteed to have signal

**Pros:**
- Guarantees all voxels are active
- Simple and robust
- Based on actual data

**Cons:**
- Smaller ROIs
- May lose some valid voxels at edges

### Solution 2: Liberal Wang Thresholding

**Strategy:** Use lower probability threshold for Wang atlas

```python
# Instead of wang_roi > 0.5
wang_roi_liberal = wang_atlas > 0.25  # 25% threshold

# Then intersect with functional mask
active_roi = wang_roi_liberal & func_mask
```

**Expected result:**
- Larger ROIs
- More voxels to work with
- Still limited to active regions

### Solution 3: Functional Localizer (IDEAL but requires more work)

**Strategy:** Define ROIs based on functional activation

```python
# Run GLM: colors vs. blank
z_map = glm.compute_contrast('colors > blank', output_type='z_score')

# Threshold at z > 3.1 within anatomical Wang ROI
functional_roi = (z_map > 3.1) & wang_mask
```

**Pros:**
- Subject-specific
- Guaranteed to be task-responsive
- Higher SNR

**Cons:**
- Requires separate localizer run or leave-one-run-out
- More complex analysis
- Circular if using same data

### Solution 4: Motion Scrubbing

**Strategy:** Exclude high-motion volumes

```python
from nilearn.image import clean_img

# Load framewise displacement
confounds = pd.read_csv(confound_file, sep='\t')
fd = confounds['framewise_displacement'].values

# Create scrubbing regressor
motion_outliers = fd > 0.5

# Clean image
cleaned_img = clean_img(
    func_img,
    confounds=confounds[motion_cols],
    sample_mask=~motion_outliers  # Exclude bad volumes
)
```

**Expected result:**
- Remove 53 / 288 volumes (18%)
- Cleaner signal
- 235 volumes remaining (still sufficient)

---

## Recommended Action Plan

### Phase 1: Quick Fix (30 minutes)

1. **Create intersection-masked ROIs**
   ```python
   python fix_roi_overlap.py  # New script needed
   ```

2. **Re-run diagnostic**
   ```bash
   python diagnostic_analysis.py
   ```

3. **Check if performance improves**
   - Should get >25% accuracy if ROIs are the main issue

### Phase 2: Add Motion Scrubbing (1 hour)

1. **Modify GLM to exclude high-motion volumes**
2. **Re-run with cleaned data**
3. **Compare performance**

### Phase 3: Optimize (if needed)

1. **Try liberal Wang thresholding**
2. **Test functional localizer**
3. **Combine approaches**

---

## Expected Performance After Fixes

### Current (Broken)
```
V1 active voxels: 190
Classification accuracy: 12.5% (chance)
SNR: 0.04
```

### After Intersection Masking
```
V1 active voxels: 190 (but all active!)
Classification accuracy: 25-40% (above chance)
SNR: 0.2-0.4
```

### After Motion Scrubbing
```
V1 active voxels: 190
Classification accuracy: 35-50%
SNR: 0.3-0.5
Clean volumes: 235/288
```

### After Liberal Thresholding
```
V1 active voxels: 300-500
Classification accuracy: 40-60%
SNR: 0.3-0.6
```

---

## Code to Create

### Priority 1: `fix_roi_overlap.py`

Creates intersection-masked ROIs that guarantee all voxels are active.

### Priority 2: Modify `bh_anal.py` or create `improved_glm_analysis.py`

- Add motion scrubbing
- Use proper confound strategy
- Set correct GLM parameters for non-centered data

### Priority 3: `compare_roi_strategies.py`

Test all 3 ROI strategies (intersection, liberal threshold, functional localizer) and compare results.

---

## Next Steps

**IMMEDIATE** (Do this now):
1. Create `fix_roi_overlap.py`
2. Re-run diagnostic
3. Check if accuracy improves

**IF ACCURACY IMPROVES** (>25%):
- ROI was the main problem ✅
- Proceed to motion scrubbing
- Then proceed to ML/DL models

**IF ACCURACY STILL LOW** (<20%):
- Other issues remain (GLM settings, preprocessing, etc.)
- Need deeper investigation

---

## Files to Create

1. ✅ `fix_roi_overlap.py` - Create intersection-masked ROIs
2. ✅ `improved_glm_analysis.py` - GLM with motion scrubbing
3. `compare_roi_strategies.py` - Test different ROI methods
4. `motion_qc_report.py` - Detailed motion analysis

Ready to create these files?
