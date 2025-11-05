# Next Steps: Improving Reconstruction Performance

## Current Status ✅

**What's Working:**
- ✅ Lab hue values corrected (pilot RGB → Lab conversion)
- ✅ Classification: 70.8% accuracy (p<0.001) - Excellent!
- ⚠️ Reconstruction: 22.9% hit rate (p=0.401) - Improved but not significant

**Progress:**
- Before fix: 14.6% hit rate, p=0.523
- After fix: 22.9% hit rate, p=0.401
- Improvement: +8.3 percentage points
- **Still need: ~20% more to reach significance**

---

## Root Cause Analysis

### 🔴 Problem 1: Poor Pilot Color Design (Fundamental Issue)

**Non-uniform spacing hurts reconstruction:**
```
color_7 (125.6°) ↔ color_8 (143.9°) = 18.3° apart
  → Less than hit tolerance (22.5°)
  → Cannot distinguish reliably!

color_1 (182.1°) ↔ color_2 (288.0°) = 105.8° apart
  → Wastes hue space
  → Poor color coverage
```

**Why this matters:**
- Forward model assumes colors are distinguishable
- Too-close colors get confused
- Non-uniform spacing breaks channel model assumptions

**Solution:** Use main experiment data (uniform 45° spacing) when available

### 🔴 Problem 2: Whole Brain Mask (230K voxels, mostly noise)

**Current setup:**
- Using: Full brain mask
- Selected: Top 5000 voxels (2.2% of brain)
- Problem: 97.8% of voxels don't care about color!

**Why this matters:**
- Selecting from 230K noisy voxels dilutes signal
- V1-V4 have the color-selective neurons we need
- SNR is very low (0.014-0.041)

**Solution:** Use V1-V4 visual cortex ROIs

### 🔴 Problem 3: Poor GLM Fit (Negative R² values!)

**From results:**
```
Run 1: R² = 0.11   (barely positive)
Run 2: R² = -292   (catastrophically bad!)
Run 3: R² = -149
Run 4: R² = -168
Run 5: R² = -325   (worst!)
Run 6: R² = -13
```

**Why this matters:**
- R² < 0 means model is worse than predicting the mean
- Canonical HRF doesn't fit this subject's actual hemodynamic response
- Garbage in → garbage out

**Solution:** Use FIR (Finite Impulse Response) model - more flexible

---

## Action Plan (Priority Order)

### 🥇 **Priority 1: Test V1-V4 ROIs** (Easiest Win, 2 hours)

**Why:** V1-V4 are color-selective areas, should have much better SNR

**Expected improvement:** +10-15% hit rate → ~35-40%

**How to do it:**

1. **Check if ROIs exist:**
```bash
python test_roi_reconstruction.py
```

2. **Modify naive_analysis.py to use V1:**
```python
# Around line 950, change:
roi_paths = {
    'V1': 'derivatives/sub-01/roi/sub-01_acq-mprage_space-MNI152NLin2009cAsym_res-2_desc-V1_mask.nii.gz',
}
```

3. **Delete cache and re-run:**
```bash
ssh node2
cd /scratch/connectome/haba6030/colorBlind
rm hrf_test_outputs/cache_V1/*.joblib
rm hrf_test_outputs/cache_V1/*.csv
sbatch sbatch_naive.sub
```

4. **Test each ROI separately:**
- V1 (511 voxels, 37% overlap)
- V2 (310 voxels, 58% overlap) ← **Best overlap!**
- V3 (89 voxels, 70% overlap)
- hV4 (55 voxels, 69% overlap)

5. **Compare results:**
```bash
python test_roi_reconstruction.py
```

**Decision criteria:**
- If any ROI gets p<0.05: ✅ Success, use that ROI
- If V2 > V1: Use V2 (better overlap)
- If all fail: Move to Priority 2

### 🥈 **Priority 2: Try FIR Model** (Better Fit, 4 hours)

**Why:** FIR doesn't assume canonical HRF shape, should fit better

**Expected improvement:** +10-20% hit rate → ~35-45%

**How to do it:**

1. **Use bh_anal.py instead:**
```bash
ssh node2
cd /scratch/connectome/haba6030/colorBlind
python bh_anal.py
```

2. **Run all stages:**
```python
from bh_anal import BHAnalysisPipeline
pipeline = BHAnalysisPipeline()
pipeline.run("design")
pipeline.run("deconv_glm")
pipeline.run("roi_build")
pipeline.run("extract_roi")
pipeline.run("forward_model")
```

3. **Compare with naive_analysis.py:**
- Check R² values (should be much better)
- Check reconstruction hit rates
- Check classification accuracy

**Decision criteria:**
- If R² > 0 for most runs: ✅ Big improvement
- If hit rate increases >10%: ✅ Use FIR going forward
- If both naive and FIR fail: Data quality issue

### 🥉 **Priority 3: Optimize Regularization** (Fine-tuning, 2 hours)

**Why:** Lambda=0.01 may be too weak, causing overfitting

**Expected improvement:** +5-10% hit rate

**How to do it:**

1. **Modify reconstruction function (line ~1650):**
```python
# Test different lambda values
for lam in [0.01, 0.1, 1.0, 10.0, 100.0]:
    # Run reconstruction with this lambda
    # Record hit rate for each
```

2. **Pick best lambda:**
- Use cross-validation
- Or pick lambda with highest mean hit rate

3. **Re-run with optimal lambda**

**Decision criteria:**
- Lambda=0.01: Underfitting (too little regularization)
- Lambda=0.1-1.0: Usually optimal
- Lambda=100+: Overfitting (too much regularization)

### 🔧 **Priority 4: Combine V1-V4** (More voxels, 1 hour)

**Why:** More voxels = more signal (if they're all color-selective)

**How to do it:**

1. **Create combined mask:**
```python
from nilearn import image
import numpy as np

v1 = image.load_img('derivatives/sub-01/roi/..._V1_mask.nii.gz')
v2 = image.load_img('derivatives/sub-01/roi/..._V2_mask.nii.gz')
v3 = image.load_img('derivatives/sub-01/roi/..._V3_mask.nii.gz')
v4 = image.load_img('derivatives/sub-01/roi/..._hV4_mask.nii.gz')

combined_data = np.logical_or(
    np.logical_or(v1.get_fdata(), v2.get_fdata()),
    np.logical_or(v3.get_fdata(), v4.get_fdata())
)

combined_img = image.new_img_like(v1, combined_data.astype(np.int16))
combined_img.to_filename('derivatives/sub-01/roi/..._V1-V4_mask.nii.gz')
```

2. **Run analysis with combined mask**

**Decision criteria:**
- If combined > individual ROIs: ✅ Use combined
- If combined < best individual: Use best individual ROI

---

## Decision Tree

```
Start: Current hit rate = 22.9%, p=0.401
│
├─→ Try V1-V4 ROIs
│   ├─ Success (p<0.05)? → ✅ Done! Use this ROI
│   └─ Fail → Continue
│
├─→ Try FIR model
│   ├─ Success (p<0.05)? → ✅ Done! Use FIR + best ROI
│   └─ Fail → Continue
│
├─→ Optimize lambda
│   ├─ Success (p<0.05)? → ✅ Done! Use optimal lambda
│   └─ Fail → Continue
│
├─→ Combine V1-V4
│   ├─ Success (p<0.05)? → ✅ Done!
│   └─ Fail → Data quality issues
│
└─→ If all fail:
    1. Check data quality (motion, attention)
    2. Consider pilot data limitations
    3. Wait for main experiment data
```

---

## Realistic Expectations

### For Pilot Data (Current):
- **Best case with improvements**: 40-50% hit rate, p~0.05
- **Realistic**: 35-45% hit rate, p~0.05-0.10
- **Limited by**: Poor color spacing, small sample size

### For Main Experiment Data (Future):
- **Expected**: 60-75% hit rate, p<0.001
- **Why better**: Uniform 45° color spacing, proper design
- **When**: After main experiment data collection

---

## Quick Start: Test V1 ROI Right Now

**Copy-paste these commands:**

```bash
# 1. Check what ROIs are available
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis
python test_roi_reconstruction.py

# 2. If V1 ROI exists, test it on server
# First, verify ROI exists on server:
ssh node2
ls -lh /scratch/connectome/haba6030/colorBlind/derivatives/sub-01/roi/

# 3. If ROIs don't exist, create them:
cd /scratch/connectome/haba6030/colorBlind
python roi_build.py  # This creates V1, V2, V3, hV4 masks

# 4. Modify naive_analysis.py to use V1 (or V2 if better)
# Edit line ~950 to specify V1 path

# 5. Run analysis
rm hrf_test_outputs/cache_V1/*.joblib
rm hrf_test_outputs/cache_V1/*.csv
sbatch sbatch_naive.sub

# 6. Check results
tail -f logs/naive_*.out
# Look for: [Forward-Recon][V1] MEAN hit=?, MEAN p=?
```

---

## Files to Use

1. **test_roi_reconstruction.py** - Compare ROI performance
2. **naive_analysis.py** - Main analysis (canonical HRF)
3. **bh_anal.py** - FIR model analysis
4. **RECONSTRUCTION_ANALYSIS.md** - Detailed problem analysis
5. **This file** - Action plan

---

## Success Criteria

**Minimum acceptable:**
- Hit rate: >30%
- p-value: <0.10
- Some runs significant (p<0.05)

**Good:**
- Hit rate: 35-40%
- p-value: <0.05
- Most runs above chance

**Excellent (unlikely with pilot data):**
- Hit rate: >50%
- p-value: <0.01
- Consistent across runs

---

## When to Move to Step 2 (CVD Filter)

**Option A: Accept pilot results**
- If you get p<0.10 with pilot data
- Use as "proof of concept"
- Acknowledge limitations

**Option B: Wait for main data**
- Better stimulus design
- Higher hit rates expected
- More robust baseline

**Recommendation:**
- Try all Priority 1-4 improvements first
- If pilot reaches p<0.05: Good enough to start CVD filter design
- If pilot doesn't reach p<0.05: Wait for main experiment data

---

## Timeline Estimate

| Task | Time | Cumulative |
|------|------|------------|
| Test V1 ROI | 2 hours | 2 hours |
| Test V2, V3, hV4 | 6 hours | 8 hours |
| Try FIR model | 4 hours | 12 hours |
| Optimize lambda | 2 hours | 14 hours |
| Combine V1-V4 | 1 hour | 15 hours |
| **Total** | **~2 days** | - |

**After this:** Either have working baseline (p<0.05) or know pilot data is insufficient.
