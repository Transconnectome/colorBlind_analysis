# Reconstruction Performance Analysis

## Current Results (After Lab Hue Fix)

### Summary
- **Classification**: 70.8% accuracy, p<0.001 ✅ (Still excellent)
- **Reconstruction**: 22.9% hit rate, p=0.401 ❌ (Improved but not significant)
- **Improvement**: +8.3 percentage points (14.6% → 22.9%)

### Per-Run Breakdown

| Run | Hit Rate | p-value | Status | Notes |
|-----|----------|---------|--------|-------|
| 1 | 12.5% | 0.615 | ❌ Poor | Below chance (12.5%) |
| 2 | 25.0% | 0.327 | ⚠️ Marginal | 2× chance level |
| 3 | **37.5%** | 0.083 | ⚠️ **Close!** | Nearly significant |
| 4 | **0.0%** | 1.000 | ❌ **Failed** | Worst run |
| 5 | **37.5%** | 0.072 | ⚠️ **Close!** | Nearly significant |
| 6 | 25.0% | 0.308 | ⚠️ Marginal | 2× chance level |

**Mean**: 22.9%, p=0.401

### Key Observations

1. **High Variability**: 0% to 37.5% between runs
2. **Some Promising Runs**: Runs 3 and 5 are close to significance
3. **One Catastrophic Run**: Run 4 has 0% hit rate
4. **Still Below Target**: Target is 40-60% with p<0.05

---

## Identified Problems

### 🔴 Problem 1: Poor Stimulus Design (Pilot Experiment)

**Color Spacing Issues:**
```
Pilot hues: [35.3°, 73.4°, 125.6°, 143.9°, 182.1°, 288.0°, 305.2°, 330.2°]
Spacing:    [38.1°, 52.2°, 18.3°,  38.2°,  105.8°, 17.2°,  25.0°,  65.1°]
```

**Problems:**
- **Too close**: color_7 (125.6°) and color_8 (143.9°) are only **18.3°** apart
  - This is less than the hit tolerance (22.5°)!
  - Model cannot distinguish them reliably
- **Too far**: color_1 (182.1°) and color_2 (288.0°) are **105.8°** apart
  - Wastes hue space
  - Reduces color coverage

**Impact on Reconstruction:**
- Colors that are too close get confused
- Non-uniform spacing makes channel model less effective
- Brouwer & Heeger (2009) used uniform 45° spacing for good reason!

### 🔴 Problem 2: Whole Brain Mask (Too Much Noise)

**Current Setup:**
- Using: Brain mask with 230,768 voxels
- Selected: Top 5000 voxels
- Coverage: Only 2.2% of brain

**Issues:**
- Most brain voxels don't respond to color
- Selecting from noisy voxels dilutes signal
- V1-V4 visual areas have the color-selective neurons

**Solution:**
- Use V1-V4 ROIs from Wang (2015) atlas
- V1: 511 voxels
- V2: 310 voxels
- V3: 89 voxels
- hV4: 55 voxels

### 🔴 Problem 3: Poor GLM Fit Quality

**From lines 59-65:**
```
Metrics summary:
 run  corr_obs_pred          R2  residual_RMSE
   1      -0.339576    0.109305       1.672390
   2       0.172884 -292.084432       9.956498
   3      -0.211384 -148.956115       7.891382
   4       0.248238 -168.286669       7.058651
   5       0.020989 -324.671742      11.915200
   6       0.092918  -12.770159       3.160725
```

**Problems:**
- **Negative R²**: Runs 2-6 have R² < 0 (model worse than mean!)
- **Low correlation**: Run 5 has r=0.02 (essentially zero)
- **High RMSE**: Runs 2, 3, 4, 5 have very high residuals

**Causes:**
- Canonical HRF may not fit subject's actual HRF
- Poor motion correction?
- Poor task timing alignment?

**Solution:**
- Try FIR (Finite Impulse Response) model
- This is what `bh_anal.py` uses
- More flexible, doesn't assume HRF shape

### 🔴 Problem 4: Regularization Too Weak

**Current lambda**: 0.01

**Issues:**
- Very small regularization
- May overfit to noise
- Especially problematic with poor GLM fit

**Solution:**
- Try lambda values: 0.1, 1.0, 10.0
- Cross-validate to find optimal lambda

---

## Recommended Solutions (Priority Order)

### ✅ Solution 1: Use V1-V4 ROIs Instead of Brain Mask (HIGH PRIORITY)

**Why:**
- V1-V4 are known color-selective areas
- Much cleaner signal than whole brain
- Fewer voxels = less noise

**How:**
```python
# In naive_analysis.py, change line ~950:
roi_paths = {
    'V1': 'derivatives/sub-01/roi/sub-01_acq-mprage_space-MNI152NLin2009cAsym_res-2_desc-V1_mask.nii.gz',
    'V2': 'derivatives/sub-01/roi/sub-01_acq-mprage_space-MNI152NLin2009cAsym_res-2_desc-V2_mask.nii.gz',
    'V3': 'derivatives/sub-01/roi/sub-01_acq-mprage_space-MNI152NLin2009cAsym_res-2_desc-V3_mask.nii.gz',
    'hV4': 'derivatives/sub-01/roi/sub-01_acq-mprage_space-MNI152NLin2009cAsym_res-2_desc-hV4_mask.nii.gz',
}
```

**Expected improvement:**
- SNR should increase
- Less variability between runs
- Hit rate: 30-50%

### ✅ Solution 2: Try FIR Model (bh_anal.py) (HIGH PRIORITY)

**Why:**
- Doesn't assume canonical HRF shape
- More flexible, better fit
- This is what Brouwer & Heeger (2009) used

**How:**
```bash
# Use bh_anal.py instead of naive_analysis.py
python bh_anal.py
```

**Expected improvement:**
- Better R² values
- More stable estimates
- Hit rate: 35-55%

### ✅ Solution 3: Optimize Regularization (MEDIUM PRIORITY)

**Why:**
- Current lambda=0.01 may be too weak
- Need to balance bias-variance tradeoff

**How:**
```python
# In naive_analysis.py, line ~1650, try different lambdas:
for lam in [0.01, 0.1, 1.0, 10.0]:
    # Run reconstruction with each lambda
    # Pick best based on cross-validation
```

**Expected improvement:**
- More stable predictions
- Less overfitting
- Hit rate: +5-10%

### ✅ Solution 4: Increase Number of Voxels (LOW PRIORITY)

**Why:**
- Currently using top 5000 voxels
- Might be missing informative voxels

**How:**
```python
# Line ~1400, try:
k_voxels = 10000  # or 15000
```

**Expected improvement:**
- Marginal (+2-5%)
- Only if voxel selection is the bottleneck

### ⚠️ Solution 5: Switch to Main Experiment Data (LONG-TERM)

**Why:**
- Main experiment has proper uniform 45° color spacing
- Better stimulus design = better decoding
- This is the "proper" dataset

**How:**
1. Wait for main experiment data collection
2. Update LABEL2HUE_DEG to uniform [0°, 45°, 90°, ...]
3. Re-run analysis

**Expected improvement:**
- Hit rate: 50-70% (substantial!)
- This addresses the fundamental stimulus design problem

---

## Quick Action Plan

### **Immediate (Today)**

**Test 1: V1 ROI**
```bash
# Modify naive_analysis.py to use V1 mask
# Re-run with V1 only
```

**Test 2: Try different lambda**
```bash
# Modify lambda from 0.01 to 1.0
# Re-run reconstruction only (classification is fine)
```

### **Short-term (This Week)**

**Test 3: FIR model**
```bash
# Run bh_anal.py
# Compare results with naive_analysis.py
```

**Test 4: Combine V1-V4**
```bash
# Create combined V1-V4 mask
# Re-run analysis
```

### **Medium-term (Next Month)**

**Test 5: Advanced methods**
- Ridge regression with cross-validated lambda
- Different channel models (8, 16, or 32 channels)
- Non-linear forward models (neural networks)

---

## Diagnostic Checks

### Check 1: Are the V1-V4 ROIs valid?

From diagnostic_64047.out:
```
V1:  511 voxels, 37.2% overlap with data
V2:  310 voxels, 58.7% overlap with data
V3:   89 voxels, 69.7% overlap with data
hV4:  55 voxels, 69.1% overlap with data
```

**Issues:**
- V1 has low overlap (37.2%) - only 190 usable voxels
- Small ROIs (V3: 89, hV4: 55 voxels)

**Recommendation:**
- Start with V2 (best overlap at 58.7%)
- Combine V1+V2+V3 for more voxels
- Check ROI registration quality

### Check 2: GLM Quality by HRF Model

From diagnostic_64047.out:
```
glover:              SNR=0.0411
glover + derivative: SNR=0.0139
spm:                 SNR=0.0257
```

**Finding**: All HRF models have very low SNR (<0.05)

**Possible causes:**
1. Poor task design timing
2. Low signal quality in pilot data
3. Motion artifacts
4. Subject attention/compliance

**Recommendation:**
- Check motion parameters
- Check task timing alignment
- Consider data quality improvements

---

## Expected Timeline

| Solution | Time | Expected Hit Rate | p-value |
|----------|------|-------------------|---------|
| Current | - | 22.9% | 0.401 ❌ |
| + V1-V4 ROIs | 1 hour | 30-35% | 0.10-0.20 |
| + Optimized lambda | 2 hours | 35-40% | 0.05-0.15 |
| + FIR model | 4 hours | 40-50% | 0.02-0.10 |
| + Combined improvements | 1 day | 45-55% | <0.05 ✅ |
| + Main experiment data | Weeks-Months | 60-75% | <0.001 ✅ |

---

## Conclusion

**Current Status:**
- Lab hue fix helped (+8.3%) but not enough
- Fundamental issues remain:
  1. Poor pilot color spacing (stimulus design)
  2. Using whole brain instead of V1-V4
  3. Poor GLM fit (canonical HRF mismatch)
  4. Weak regularization

**Next Steps:**
1. ✅ **Try V1-V4 ROIs** (highest priority, easiest win)
2. ✅ **Try FIR model** (bh_anal.py)
3. ✅ **Optimize lambda**
4. ⚠️ **Long-term: Use main experiment data** (proper uniform color spacing)

**Realistic Expectation for Pilot Data:**
- With all improvements: 40-55% hit rate, p~0.05
- Won't reach 60-70% due to fundamental stimulus design issues
- Main experiment data will be much better!
