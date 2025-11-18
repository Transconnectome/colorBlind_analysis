# All Critical Issues with bh_anal.py

**Date:** 2025-11-06
**Status:** 🔴 MULTIPLE CRITICAL FLAWS - DO NOT USE

---

## 🚨 Problem #1: Universal HIRF (Already Identified)

**Lines 236-295**

### Issue
Averages HIRF across all voxels instead of using per-voxel estimates.

### Impact
Defeats the entire purpose of FIR - no better than canonical HRF.

**Status:** ❌ CRITICAL - renders FIR estimation useless

---

## 🚨 Problem #2: Wrong Hue Values for Reconstruction

**Lines 458-460, 469-470, 903-905**

### The Code

```python
def _label_indices_to_deg(self, idx_array):
    step = 360.0 / self.config.N_COLORS  # 360/8 = 45°
    return (idx_array.astype(float) * step) % 360.0
```

**This assumes:**
- color_1 = 0°
- color_2 = 45°
- color_3 = 90°
- color_4 = 135°
- etc.

**But pilot data actually has:**
```python
LABEL2HUE_DEG_PILOT = {
    'color_1': 182.14°,  # NOT 0°!
    'color_2': 287.98°,  # NOT 45°!
    'color_3': 305.23°,  # NOT 90°!
    'color_4': 330.20°,  # NOT 135°!
    'color_5': 35.27°,   # NOT 180°!
    'color_6': 73.37°,   # NOT 225°!
    'color_7': 125.59°,  # NOT 270°!
    'color_8': 143.91°,  # NOT 315°!
}
```

### Impact

**Reconstruction will fail completely!**

When comparing predicted hue to true hue (line 905):
```python
true_deg = self._label_indices_to_deg(y_test)  # ← WRONG values!
diff = self._circular_diff_deg(preds_idx, true_deg)
hit = float((diff <= tol_deg).mean())
```

Example error:
- True color_1 presented: Lab hue = **182.14°**
- bh_anal.py thinks it's: **0°**
- Difference: **182.14°** (WAY more than 22.5° tolerance)
- Result: **Always misses**, even with perfect reconstruction!

**This explains why reconstruction fails!**

---

## 🚨 Problem #3: Brittle ROI Name Extraction

**Line 382**

### The Code

```python
roi_name = os.path.basename(roi_file).split('_')[1]
```

### Issue

Assumes ROI name is always the second element after splitting by '_':
- `sub-01_V2_mask.nii.gz` → `['sub-01', 'V2', 'mask.nii.gz']` → `'V2'` ✅
- `sub-01_space-MNI_V2_mask.nii.gz` → `['sub-01', 'space-MNI', ...]` → `'space-MNI'` ❌

### Impact

Won't work with more complex BIDS filenames. May load wrong masks or crash.

**Status:** ⚠️ MODERATE - works for current simple filenames, but fragile

---

## 📊 Why bh_anal.py Results Would Be Wrong

### Compound Effect of Problems

1. **Universal HIRF (Problem #1):**
   - Beta estimates are poor (like canonical HRF)
   - Negative R² values
   - Noisy predictions

2. **Wrong hue values (Problem #2):**
   - Even if predictions were perfect
   - Comparing against wrong "ground truth"
   - Always scores as incorrect

3. **Combined result:**
   - Classification might work (doesn't use hue values)
   - Reconstruction will **always fail** (wrong comparison)
   - User sees poor results and blames everything else

---

## ✅ How simple_fir_test.py Avoids These

### Problem #1 (Universal HIRF)
**Solution:** Uses nilearn's FirstLevelModel with `hrf_model='fir'`
- Automatically does per-voxel FIR estimation
- No averaging across voxels

### Problem #2 (Wrong hue values)
**Solution:** Only tests classification, not reconstruction
- Classification uses color indices (0-7), not hue values
- If we add reconstruction, can use correct `LABEL2HUE_DEG_PILOT`

### Problem #3 (ROI extraction)
**Solution:** Uses explicit path from config
- `roi_path = f"derivatives/sub-{cfg.SUB_ID}/roi/sub-{cfg.SUB_ID}_{ROI_NAME}_mask.nii.gz"`
- No brittle parsing needed

---

## 🎯 Why naive_analysis.py Is Better (Despite Canonical HRF Issue)

### What naive_analysis.py does RIGHT

1. **Uses correct Lab hue values** (lines 1090-1104):
   ```python
   LABEL2HUE_DEG = {
       'color_1': float(182.142053052572436),  # ← CORRECT!
       'color_2': float(287.979026187069735),  # ← CORRECT!
       # ... etc
   }
   ```

2. **Per-voxel GLM fitting** (uses FirstLevelModel correctly)

3. **Proper ROI name extraction** (lines 116-149)

### What's wrong

1. **Uses canonical HRF** → negative R² values in some runs
   - But at least compares against correct hue values!

**Result:** Poor but not completely broken like bh_anal.py

---

## 📋 Summary Table

| Issue | bh_anal.py | naive_analysis.py | simple_fir_test.py |
|-------|-----------|-------------------|-------------------|
| Per-voxel HRF | ❌ Averages | ❌ Canonical | ✅ Per-voxel FIR |
| Correct hue values | ❌ Wrong (0°,45°,...) | ✅ Correct Lab | ✅ N/A (classification only) |
| ROI extraction | ⚠️ Brittle | ✅ Robust | ✅ Explicit path |
| Classification | ✅ Works | ✅ Works | ✅ Works |
| Reconstruction | ❌❌ Doubly broken | ⚠️ Poor (HRF issue) | - Not implemented yet |

---

## 🛠️ Recommendation

### Short Term: Test FIR with Classification

1. **Run simple_fir_test.py**
   - Tests if per-voxel FIR improves signal quality
   - Classification only (no hue value issues)
   - 5-10 minute runtime

2. **If classification improves (>20% accuracy):**
   - FIR works better than canonical HRF! ✅
   - Can build full reconstruction pipeline

3. **For reconstruction, must:**
   - Use per-voxel FIR (from simple_fir_test.py approach)
   - Use correct Lab hue values (from naive_analysis.py)
   - Combine best of both!

### Medium Term: Create Proper FIR Reconstruction

If `simple_fir_test.py` shows FIR helps, create:

**fir_reconstruction.py** that:
1. Uses nilearn's FIR model (per-voxel) ✅
2. Uses correct LABEL2HUE_DEG_PILOT ✅
3. Implements B&H forward model with proper hues ✅
4. Leave-one-run-out cross-validation ✅

### DO NOT Use

❌ **bh_anal.py** - Three critical flaws:
1. Universal HIRF (defeats FIR)
2. Wrong hue values (reconstruction always fails)
3. Brittle ROI extraction

---

## 🔧 If You Must Fix bh_anal.py

### Fix #1: Per-Voxel HIRF (Complex)

Replace lines 283-295 with per-voxel loop:
```python
# This requires complete redesign of the beta estimation
# Much easier to use nilearn's FIR instead
```

### Fix #2: Correct Hue Values (Simple)

Replace line 459-460:
```python
# OLD (wrong):
def _label_indices_to_deg(self, idx_array):
    step = 360.0 / self.config.N_COLORS
    return (idx_array.astype(float) * step) % 360.0

# NEW (correct):
def _label_indices_to_deg(self, idx_array):
    LABEL2HUE_DEG_PILOT = {
        0: 182.142053052572436,
        1: 287.979026187069735,
        2: 305.226546308759566,
        3: 330.204721787408289,
        4: 35.269500805260478,
        5: 73.365061454288877,
        6: 125.585145639335096,
        7: 143.909094545652778,
    }
    return np.array([LABEL2HUE_DEG_PILOT[int(i)] for i in idx_array])
```

### Fix #3: Robust ROI Extraction (Simple)

Replace line 382:
```python
# OLD (brittle):
roi_name = os.path.basename(roi_file).split('_')[1]

# NEW (robust):
filename = os.path.basename(roi_file)
# Look for ROI pattern in filename
for roi_pattern in ['V1', 'V2', 'V3', 'hV4', 'EarlyVisual', 'Ventral']:
    if f'_{roi_pattern}_' in filename or filename.startswith(f'{roi_pattern}_'):
        roi_name = roi_pattern
        break
else:
    roi_name = filename.split('_')[1]  # Fallback
```

**But honestly:** Just use the corrected approach (simple_fir_test.py + correct hues) instead of fixing three separate issues in bh_anal.py!

---

## 🎓 Key Lessons

1. **Code that runs ≠ correct code**
   - All three bugs produce output without errors
   - Only careful inspection reveals flaws

2. **Validate assumptions**
   - bh_anal.py assumes uniform hue spacing
   - But pilot data has non-uniform spacing
   - Always check against actual data!

3. **Compare with known-good implementation**
   - naive_analysis.py has correct hues (even if HRF is wrong)
   - Use it as reference for proper hue handling

4. **Test incrementally**
   - simple_fir_test.py tests just FIR improvement
   - Don't try to fix everything at once

---

**Status:** Three critical flaws identified
**Recommendation:** Use simple_fir_test.py + correct hues instead of bh_anal.py
**Next step:** Test if FIR improves classification, then build proper reconstruction pipeline

---

## 📝 Update for CURRENT_STATUS.md

After testing simple_fir_test.py:

**If FIR helps (classification >20%):**
- Create new script combining:
  - Per-voxel FIR from simple_fir_test.py
  - Correct Lab hues from naive_analysis.py
  - B&H forward model methodology

**If FIR doesn't help:**
- Problem is deeper (event timing, data quality, etc.)
- Investigate those issues first
