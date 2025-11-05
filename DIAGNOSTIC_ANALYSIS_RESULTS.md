# Diagnostic Analysis Results - Critical Issues Found

**Date:** Based on job 64047
**Status:** ⚠️ **CRITICAL - Performance at Chance Level**

---

## Executive Summary

The diagnostic analysis reveals **severe issues** with the current pipeline. Classification accuracy is at **chance level (12.5%)** and correlation between standard GLM and deconvolution approaches is **essentially zero (-0.0007)**. This indicates fundamental problems that must be addressed before proceeding.

---

## 1. HRF Model Comparison Results

### Signal-to-Noise Ratios (SNR)

| HRF Model | Mean Beta | Std Beta | SNR | Status |
|-----------|-----------|----------|-----|--------|
| Glover | 2.13 | 51.85 | **0.041** | ⚠️ Very Poor |
| Glover + Derivative | 0.69 | 49.79 | **0.014** | 🔴 Critical |
| SPM | 2.00 | 77.71 | **0.026** | 🔴 Critical |
| FIR | - | - | **ERROR** | ❌ Failed |

### Critical Issues

1. **SNR < 0.05 for all models** - This is extremely low
   - Good fMRI studies typically have SNR > 0.2
   - Suggests either:
     - Poor data quality (motion, scanner issues)
     - Incorrect preprocessing
     - Weak task-related signal
     - Data already centered (see warnings)

2. **FIR model failed** - Contrast naming issue
   - The error suggests event names in TSV don't match expected format
   - Need to check event file structure

3. **High variance, low signal** - Standard deviation is 50-80x larger than mean
   - Indicates massive amount of noise relative to signal

### Recommendation

**❌ DO NOT USE the current data as-is**

Possible causes to investigate:
- Check if fMRIPrep data is already z-scored/centered
- Verify task timing and event files
- Check for excessive motion
- Verify stimulus presentation worked correctly

---

## 2. ROI Quality Assessment

### ROI Sizes and Overlap

| ROI | N Voxels | Volume (cm³) | Overlap with Functional Data | Status |
|-----|----------|--------------|------------------------------|--------|
| V1 | 511 | 4.09 | **37.2%** | ⚠️ Poor overlap |
| V2 | 310 | 2.48 | 58.7% | ⚠️ Small but OK |
| V3 | 89 | 0.71 | 69.7% | 🔴 Very small |
| hV4 | 55 | 0.44 | 69.1% | 🔴 Critically small |
| BrainMask | 230,768 | 1846.14 | 42.4% | ⚠️ Poor overlap |

### Critical Issues

1. **V1 has only 37.2% overlap** with functional data
   - 63% of ROI voxels have zero signal!
   - Indicates misalignment between Wang atlas and functional space
   - This is the **primary ROI** for color decoding - must be fixed

2. **V3 and hV4 are too small** (89 and 55 voxels)
   - Below minimum recommended size for decoding (~200 voxels)
   - Not enough voxels to capture population code
   - Will have poor generalization

3. **Only 42% of brain mask is active**
   - Suggests significant masking/dropout issues
   - Could be due to aggressive skull-stripping or coverage issues

### Recommendation

**🔧 MUST FIX ROI alignment before proceeding**

Actions needed:
1. Check Wang atlas transformation to MNI space
2. Verify functional data is in correct space (MNI152NLin2009cAsym)
3. Consider using probabilistic threshold > 50% for Wang atlas
4. May need to combine V1v+V1d+V2v+V2d into "early visual" ROI

---

## 3. Beta Estimate Comparison

### Standard GLM vs Deconvolution

```
Standard GLM:    mean = 0.52,  std = 37.02
Deconvolution:   mean = 1.83,  std = 7.48
Correlation:     r = -0.0007
```

### Critical Issues

1. **Correlation ≈ 0** between the two methods
   - They are producing completely different results
   - One (or both) is fundamentally wrong
   - This validates the concerns in ANALYSIS_RECOMMENDATIONS.md

2. **Standard GLM has higher variance** (std=37 vs std=7.5)
   - Suggests deconvolution is over-smoothing/averaging
   - Matches prediction that deconv destroys voxel-specific info

3. **Different means** (0.52 vs 1.83)
   - Not just a scaling difference - fundamentally different estimates
   - Indicates methodological incompatibility

### Recommendation

**❌ ABANDON deconvolution approach**
**✅ USE standard GLM** as recommended in ANALYSIS_RECOMMENDATIONS.md

---

## 4. Voxel Selection Impact

### Results

```
Total voxels in V1: 511
Classification accuracy with 500 voxels: 0.125 (12.5%)
```

### Critical Issues

1. **Accuracy = chance level** (12.5% for 8-way classification)
   - Model is learning nothing
   - Random guessing would achieve same performance
   - This is a **complete failure** of the current pipeline

2. **Only 511 voxels in V1** (should have thousands)
   - Confirms ROI alignment problem
   - Insufficient data for robust decoding

3. **Cannot test higher k values**
   - Not enough voxels available
   - Indicates data scarcity issue

### Recommendation

**🛑 STOP** - Fix ROIs before testing voxel selection

---

## Root Cause Analysis

Based on all diagnostics, the **primary problems** are:

### 1. Data Centering Issue (High Priority)
The warnings indicate data might already be centered:
```
UserWarning: Mean values of 0 observed. The data have probably been centered.
```

**Likely cause:** fMRIPrep outputs are already preprocessed/normalized

**Solution:**
- Do NOT apply additional normalization in GLM
- Check fMRIPrep configuration
- May need to use raw BOLD instead of desc-preproc

### 2. ROI Misalignment (High Priority)
37% overlap in V1 is unacceptable

**Likely causes:**
- Wang atlas not properly transformed to subject space
- Using wrong template space
- Threshold too high for probabilistic atlas

**Solution:**
- Re-run roi_build.py with lower threshold (25% instead of 50%)
- Verify atlas is in same space as functional data
- Consider using subject-specific retinotopy if available

### 3. Poor Signal Quality (Medium Priority)
SNR < 0.05 across all HRF models

**Possible causes:**
- Weak stimulus contrast
- Poor subject attention
- Scanner noise
- Excessive motion

**Solution:**
- Check quality control metrics from fMRIPrep
- Review motion parameters
- Consider excluding high-motion volumes

---

## Immediate Action Plan

### Phase 1: Fix Data Loading (URGENT)

1. **Verify data is not already centered**
   ```python
   # Check mean of functional data
   import nibabel as nib
   func = nib.load('sub-01_task-rsvp_run-1_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz')
   data = func.get_fdata()
   print(f"Mean: {data.mean()}, Std: {data.std()}")

   # If mean ≈ 0, data is already centered - don't normalize again!
   ```

2. **Fix GLM to handle centered data**
   - Set `standardize=False` in GLM
   - Remove explicit centering/scaling

### Phase 2: Fix ROI Alignment (URGENT)

1. **Lower Wang atlas threshold**
   ```python
   # In roi_build.py
   threshold = 0.25  # Instead of 0.5
   ```

2. **Verify transformation**
   - Check that atlas and functional are in same space
   - Resample atlas to functional space (not vice versa)

3. **Create combined ROIs**
   - "Early visual": V1 + V2
   - "Ventral": V3 + V4
   - Use larger ROIs for more robust estimates

### Phase 3: Re-run Diagnostics

After fixes, expect to see:
- SNR > 0.2 (ideally > 0.5)
- V1 overlap > 80%
- V1 size > 2000 voxels
- Classification accuracy > 25% (above chance)

---

## Expected Performance After Fixes

| Metric | Current | Target | Good |
|--------|---------|--------|------|
| SNR | 0.01-0.04 | >0.2 | >0.5 |
| V1 overlap | 37% | >80% | >90% |
| V1 voxels | 511 | >2000 | >5000 |
| Classification | 12.5% | >25% | >50% |
| Correlation (Standard vs Deconv) | -0.0007 | N/A | N/A |

---

## Next Steps

### DO THIS FIRST ✅

1. Create `data_sanity_check.py` to verify data properties
2. Fix ROI alignment issue
3. Modify GLM to handle centered data
4. Re-run diagnostics to verify fixes

### DO NOT DO YET ❌

1. Do NOT proceed with ML/DL models
2. Do NOT run systematic testing
3. Do NOT implement CVD correction
4. Do NOT try fancy preprocessing

**Reason:** Fix fundamentals first. Fancy models won't help if data/ROIs are broken.

---

## Code Fixes Needed

### Priority 1: ROI Alignment

File: `roi_build.py`

- Lower probabilistic threshold to 25%
- Add verification that atlas matches functional space
- Create combined ROIs for robustness

### Priority 2: GLM Settings

File: `bh_anal.py` or create `fixed_glm_analysis.py`

- Set `standardize=False` if data already centered
- Use `hrf_model='glover'` (simplest first)
- Add `minimize_memory=False` for better performance

### Priority 3: Data Verification

Create new file: `data_sanity_check.py`

- Check data mean/std
- Verify event timing
- Check confound file structure
- Validate ROI-functional alignment

---

## Conclusion

The current pipeline has **fundamental data quality and alignment issues** that must be resolved before proceeding with any advanced analyses. The diagnostic successfully identified these problems - now we need to fix them systematically.

**DO NOT** proceed to Step 2 (ML/DL models) or CVD correction until these basics are working.

**Estimated time to fix:** 1-2 days of careful debugging and re-processing.
