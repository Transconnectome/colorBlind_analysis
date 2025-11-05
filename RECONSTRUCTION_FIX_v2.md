# Reconstruction Fix v2: Corrected Lab Hue Values

## 🔴 Problem Summary

**Reconstruction failed** (hit rate: 14.6%, p=0.523) while **classification succeeded** (70%, p<0.001).

## 🔍 Root Causes Identified

### **Bug #1: HSV Overwrite (Fixed in v1)**
Line 1145 was overwriting Lab hue with HSV hue values (up to 97.8° difference).

### **Bug #2: IRB vs Actual Lab Hue Mismatch (Fixed in v2)** ⭐ **NEW**

The IRB document Lab hue values **do NOT match** the actual Lab hue values of the RGB colors presented in the experiment!

| Color | IRB Hue (intended) | Actual Hue (presented) | Difference |
|-------|-------------------|------------------------|------------|
| color_1 | 178.57° | **182.14°** | 3.57° |
| color_2 | 310.77° | **287.98°** | **22.79°** ❌ |
| color_3 | 316.10° | **305.23°** | **10.87°** ❌ |
| color_4 | 333.86° | **330.20°** | 3.66° |
| color_5 | 54.50° | **35.27°** | **19.23°** ❌ |
| color_6 | 68.45° | **73.37°** | 4.92° |
| color_7 | 130.78° | **125.59°** | 5.20° |
| color_8 | 153.72° | **143.91°** | 9.81° |

**Critical Issue**: color_2, color_3, and color_5 differ by **10-23 degrees**!

---

## 📋 Analysis Method

### Step 1: Found Actual Stimulus File
The experiment file `colorBlind_pilotTest.py` shows the actual RGB values used:
```python
# Line 77-87 in colorBlind_pilotTest.py
COLOR_RGB = {
    'color_1': [-0.84,  0.20,  0.08],  # reddish
    'color_2': [-0.96, -0.24,  0.64],  # orange
    ...
}
```

### Step 2: Traced Color Presentation
```python
# Line 164: colorSpace='rgb' (PsychoPy RGB)
self.stim = visual.RadialStim(..., colorSpace='rgb', ...)

# Line 356: Direct RGB assignment
stim_color = COLOR_RGB[stim_label]

# Line 396: Color applied to stimulus
self.drawer.draw_patch(stim_color, radial_phase)
```

### Step 3: Computed Actual Lab Hue
```python
# compute_actual_lab_hue.py
PsychoPy RGB [-1, 1]
  → sRGB [0, 1]
  → CIELab (L, a, b)
  → hue = atan2(b, a)
```

**Result**: Actual Lab hue differs from IRB by up to **22.79°**!

---

## ✅ Solution Applied

### Updated `naive_analysis.py` (Lines 1090-1104)

**BEFORE (Incorrect - IRB values):**
```python
LABEL2HUE_DEG = {
    'color_1': float(178.5695366901941),  # IRB value
    'color_2': float(310.7676279123204),  # IRB value (22.79° off!)
    ...
}
```

**AFTER (Correct - Actual presented colors):**
```python
LABEL2HUE_DEG = {
    'color_1': float(182.142053052572436),   # Actual: 182.14° (IRB was 178.57°)
    'color_2': float(287.979026187069735),   # Actual: 287.98° (IRB was 310.77°)
    'color_3': float(305.226546308759566),   # Actual: 305.23° (IRB was 316.10°)
    'color_4': float(330.204721787408289),   # Actual: 330.20° (IRB was 333.86°)
    'color_5': float(35.269500805260478),    # Actual:  35.27° (IRB was  54.50°)
    'color_6': float(73.365061454288877),    # Actual:  73.37° (IRB was  68.45°)
    'color_7': float(125.585145639335096),   # Actual: 125.59° (IRB was 130.78°)
    'color_8': float(143.909094545652778),   # Actual: 143.91° (IRB was 153.72°)
}
```

---

## 🚀 Deployment Instructions

### **Step 1: Upload Fixed File**
```bash
scp naive_analysis.py node2:/scratch/connectome/haba6030/colorBlind/
```

### **Step 2: Delete ALL Cached Results (CRITICAL!)**
```bash
ssh node2
cd /scratch/connectome/haba6030/colorBlind

# Delete classification cache (uses beta patterns, should be OK but refresh anyway)
rm hrf_test_outputs/cache_brain/classification_results.joblib
rm hrf_test_outputs/cache_brain/classification_results.csv

# Delete reconstruction cache (MUST delete - uses hue values)
rm hrf_test_outputs/cache_brain/reconstruction_results.joblib
rm hrf_test_outputs/cache_brain/reconstruction_results.csv
```

### **Step 3: Re-run Analysis**
```bash
sbatch sbatch_naive.sub
```

### **Step 4: Monitor Progress**
```bash
# Watch log in real-time
tail -f logs/naive_*.out

# Check for new Lab hue output
grep "Lab hue" logs/naive_*.out
```

---

## 📊 Expected Results

### Current Results (Broken):
```
Classification: 70% accuracy, p=0.001 ✅ (Good - not affected by hue)
Reconstruction: 14.6% hit rate, p=0.523 ❌ (Failed - affected by hue mismatch)
```

### Expected Results (Fixed):
```
Classification: 70% accuracy, p=0.001 ✅ (Should stay the same)
Reconstruction: 40-60% hit rate, p<0.05 ✅ (Should improve significantly!)
```

**Why this should work:**
- Classification uses beta patterns (voxel activation), not hue angles → unaffected
- Reconstruction uses hue angles as ground truth → now corrected
- The 22.79° mismatch in color_2 alone was larger than the hit tolerance (22.5°)!

---

## 🔬 Technical Details

### Why Lab Hue Matters for Reconstruction

**Forward Encoding Model:**
```
Training phase:
  C = f(H_true)  # Build channel response from TRUE Lab hue
  W = (X^T X)^-1 X^T B  # Learn voxel weights

Testing phase:
  C_pred = (W^T W)^-1 W^T B_test  # Predict channel response
  H_pred = argmax_h corr(C_pred, f(h))  # Find best-matching hue

Hit rate = P(|H_pred - H_true| < 22.5°)
```

**The Bug's Impact:**
- If `H_true` (ground truth) is wrong by 22.79°, predictions will NEVER hit
- Even a perfect model would fail if ground truth is shifted!

### Actual vs Intended Design

**Original Intention (Brouwer & Heeger 2009):**
- 8 colors uniformly spaced at 45° intervals: [0°, 45°, 90°, 135°, 180°, 225°, 270°, 315°]

**Pilot Experiment (Actual):**
- Non-uniform spacing: [35.27°, 73.37°, 125.59°, 143.91°, 182.14°, 287.98°, 305.23°, 330.20°]
- Spacing ranges from ~18° to ~105° between adjacent colors

---

## 📁 Files Modified

1. `naive_analysis.py` (lines 1090-1104): Updated LABEL2HUE_DEG with actual Lab hue values
2. `compute_actual_lab_hue.py` (NEW): Script to compute Lab hue from RGB
3. `RECONSTRUCTION_FIX_v2.md` (NEW): This documentation

---

## ✅ Checklist

- [x] Traced actual stimulus presentation in colorBlind_pilotTest.py
- [x] Computed actual Lab hue from presented RGB values
- [x] Identified 22.79° mismatch in color_2 (largest discrepancy)
- [x] Updated LABEL2HUE_DEG in naive_analysis.py
- [x] Created verification script (compute_actual_lab_hue.py)
- [ ] Upload to server
- [ ] Delete cached results (classification + reconstruction)
- [ ] Re-run analysis
- [ ] Verify reconstruction hit rate improves to 40-60%
- [ ] Extend to V1-V4 ROIs

---

## 🤔 Why Did This Happen?

**Hypothesis:** The IRB document may have listed the **intended** Lab hue values (possibly for a different RGB set or uniformly spaced design), but the actual experiment used different RGB values that map to different Lab hues.

The `compute_actual_lab_hue.py` script shows:
- IRB intended hues: Would correspond to different RGB values
- Actual presented hues: From the RGB values in colorBlind_pilotTest.py

**Solution:** Always compute ground truth from the **actual presented stimulus**, not from design documents!

---

## 📖 References

**Color Space Conversion:**
- scikit-image `color.rgb2lab()`: sRGB → CIELab conversion
- CIE 1976 L\*a\*b\* color space standard

**Forward Encoding Model:**
- Brouwer, G. J., & Heeger, D. J. (2009). Decoding and reconstructing color from responses in human visual cortex. *Journal of Neuroscience*, 29(44), 13992-14003.
