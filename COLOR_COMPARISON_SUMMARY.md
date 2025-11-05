# Color Comparison: IRB vs Pilot vs Main Experiment

## Executive Summary

**Critical Finding**: PILOT and MAIN experiments used **completely different colors**!

| Comparison | Max Difference | Status |
|------------|----------------|--------|
| Pilot vs Main | **62.98°** (color_2) | ❌ Different experiments |
| IRB vs Pilot | 22.79° (color_2) | ❌ IRB doesn't match pilot |
| IRB vs Main | 85.77° (color_2) | ❌ IRB doesn't match main |

---

## Experiment Designs

### **Pilot Experiment** (colorBlind_pilotTest.py)
- **Method**: Arbitrary RGB values in PsychoPy [-1, 1] space
- **Lab hue spacing**: Non-uniform (17.2° to 105.8° between adjacent colors)
- **Lab hue values**: [35.3°, 73.4°, 125.6°, 143.9°, 182.1°, 288.0°, 305.2°, 330.2°]
- **Lightness**: Varies (L*: 33.2 to 71.9)
- **Chroma**: Varies

```python
# Pilot RGB (PsychoPy colorSpace='rgb')
COLOR_RGB = {
    'color_1': [-0.84,  0.20,  0.08],  # reddish
    'color_2': [-0.96, -0.24,  0.64],  # orange
    'color_3': [-0.98, -0.80,  0.96],  # yellow
    'color_4': [ 0.60, -0.56,  0.52],  # greenish
    'color_5': [ 1.00, -0.48, -0.56],  # cyan
    'color_6': [ 0.90,  0.24, -0.90],  # blue
    'color_7': [-0.24,  0.20, -0.72],  # violet
    'color_8': [-0.90, -0.20, -0.70],  # pinkish
}
```

### **Main Experiment** (colorBlind_test.py) ✅ Proper Design
- **Method**: Lab color space directly (Brouwer & Heeger 2009)
- **Lab hue spacing**: Perfect uniform 45° intervals
- **Lab hue values**: **[0°, 45°, 90°, 135°, 180°, 225°, 270°, 315°]**
- **Lightness**: Constant (L* = 75)
- **Chroma**: Constant (radius = 40 in a*b* plane)

```python
# Main Lab values (converted to PsychoPy RGB via lab2rgb)
COLOR_LAB = {
    'color_1': [75, -40.0, 0.0],       # 0°: Red (→180° in standard notation)
    'color_2': [75, -28.28, -28.28],   # 45°: Orange (→225°)
    'color_3': [75, 0.0, -40.0],       # 90°: Yellow (→270°)
    'color_4': [75, 28.28, -28.28],    # 135°: Greenish (→315°)
    'color_5': [75, 40.0, 0.0],        # 180°: Cyan (→0°)
    'color_6': [75, 28.28, 28.28],     # 225°: Blue (→45°)
    'color_7': [75, 0.0, 40.0],        # 270°: Violet (→90°)
    'color_8': [75, -28.28, 28.28],    # 315°: Pinkish (→135°)
}
```

**Note**: The hue angles in the comments (0°, 45°, 90°...) represent the angle from the +a axis. Standard hue notation uses atan2(b,a), giving [180°, 225°, 270°, 315°, 0°, 45°, 90°, 135°].

---

## Detailed Comparison Table

| Color | IRB Hue | Pilot Hue | Main Hue | IRB-Pilot Δ | IRB-Main Δ | Pilot-Main Δ |
|-------|---------|-----------|----------|-------------|------------|--------------|
| color_1 | 178.57° | 182.14° | 180.00° | 3.57° | 1.43° | 2.14° |
| color_2 | 310.77° | 287.98° | 225.00° | **22.79°** | **85.77°** | **62.98°** |
| color_3 | 316.10° | 305.23° | 270.00° | 10.87° | **46.10°** | **35.23°** |
| color_4 | 333.86° | 330.20° | 315.00° | 3.66° | 18.86° | 15.20° |
| color_5 | 54.50° | 35.27° | 0.00° | **19.23°** | **54.50°** | **35.27°** |
| color_6 | 68.45° | 73.37° | 45.00° | 4.92° | 23.45° | **28.37°** |
| color_7 | 130.78° | 125.59° | 90.00° | 5.20° | **40.78°** | **35.59°** |
| color_8 | 153.72° | 143.91° | 135.00° | 9.81° | 18.72° | 8.91° |

---

## Why This Matters for Analysis

### **For Reconstruction (Forward Encoding Model)**
The reconstruction model uses **ground truth Lab hue angles** to compute hit rates:

```python
hit_rate = P(|predicted_hue - true_hue| < 22.5°)
```

**If you use the wrong hue values:**
- color_2 in pilot (287.98°) vs main (225.00°) = **62.98° difference**
- This is **2.8× larger than the hit tolerance (22.5°)**!
- Even a perfect model would show 0% hit rate

### **For Classification**
Classification uses **beta patterns (voxel activations)**, not hue angles → less affected by this issue. This explains why your classification was successful (70%) but reconstruction failed (14.6%).

---

## Correct Lab Hue Values for Analysis

### **For PILOT Data** (sub-01, what you're currently analyzing)

```python
LABEL2HUE_DEG = {
    'color_1': float(182.142053052572436),   # Actual pilot Lab hue
    'color_2': float(287.979026187069735),   # NOT 310.77° from IRB
    'color_3': float(305.226546308759566),   # NOT 316.10° from IRB
    'color_4': float(330.204721787408289),
    'color_5': float(35.269500805260478),    # NOT 54.50° from IRB
    'color_6': float(73.365061454288877),
    'color_7': float(125.585145639335096),
    'color_8': float(143.909094545652778),
}
```

**✅ Status**: Already updated in `naive_analysis.py` (v2 fix)

### **For MAIN Experiment Data** (when you analyze it in the future)

```python
LABEL2HUE_DEG = {
    'color_1': float(180.0),  # Perfect 45° spacing
    'color_2': float(225.0),
    'color_3': float(270.0),
    'color_4': float(315.0),
    'color_5': float(0.0),
    'color_6': float(45.0),
    'color_7': float(90.0),
    'color_8': float(135.0),
}
```

**⚠️ Important**: When you switch to analyzing main experiment data, you MUST update `LABEL2HUE_DEG` to these values!

---

## RGB Value Comparison

### Pilot RGB vs Main RGB (PsychoPy [-1, 1] scale)

| Color | Pilot RGB | Main RGB | Match? |
|-------|-----------|----------|--------|
| color_1 | [-0.840,  0.200,  0.080] | [-0.402,  0.602,  0.438] | ❌ No |
| color_2 | [-0.960, -0.240,  0.640] | [-0.744,  0.579,  0.848] | ❌ No |
| color_3 | [-0.980, -0.800,  0.960] | [ 0.027,  0.476,  1.000] | ❌ No |
| color_4 | [ 0.600, -0.560,  0.520] | [ 0.664,  0.321,  0.858] | ❌ No |
| color_5 | [ 1.000, -0.480, -0.560] | [ 0.987,  0.224,  0.459] | ❌ No |
| color_6 | [ 0.900,  0.240, -0.900] | [ 0.952,  0.284,  0.052] | ❌ No |
| color_7 | [-0.240,  0.200, -0.720] | [ 0.638,  0.431, -0.135] | ❌ No |
| color_8 | [-0.900, -0.200, -0.700] | [ 0.170,  0.550,  0.030] | ❌ No |

**All 8 colors are completely different!**

---

## Hue Spacing Analysis

### Main Experiment (Proper Brouwer & Heeger Design)
- **Intended**: [0°, 45°, 90°, 135°, 180°, 225°, 270°, 315°]
- **Actual**: [0°, 45°, 90°, 135°, 180°, 225°, 270°, 315°]
- **Spacing**: Perfect 45° intervals ✅

### Pilot Experiment (Non-uniform)
- **Hues**: [35.3°, 73.4°, 125.6°, 143.9°, 182.1°, 288.0°, 305.2°, 330.2°]
- **Spacing**: [38.1°, 52.2°, 18.3°, 38.2°, 105.8°, 17.2°, 25.0°, 65.1°]
- **Min spacing**: 17.2° ❌
- **Max spacing**: 105.8° ❌ (more than 2× expected!)

**Issues with pilot spacing:**
- Some colors too close (17.2°, 18.3°)
- Some colors too far apart (105.8°)
- Not optimal for color discrimination studies

---

## Why Did This Happen?

**Hypothesis**: The pilot experiment may have:
1. Used arbitrary RGB values without Lab color space conversion
2. Been designed before the final Brouwer & Heeger methodology was implemented
3. Had IRB documentation that described the **intended** main experiment design

**The main experiment** properly implements the Brouwer & Heeger (2009) method:
- Direct Lab color space specification
- Uniform 45° spacing
- Constant lightness and chroma

---

## Action Items

### ✅ Completed
1. Identified pilot vs main color differences
2. Updated `naive_analysis.py` with correct pilot Lab hue values
3. Created comparison script (`compare_all_colors.py`)

### 📋 TODO for Current Pilot Analysis
1. Deploy updated `naive_analysis.py` to server
2. Clear all cached results (classification + reconstruction)
3. Re-run analysis
4. Verify reconstruction hit rate improves to 40-60%

### 📋 TODO for Future Main Experiment Analysis
1. Create separate config file or script version for main experiment
2. Update `LABEL2HUE_DEG` to uniform [0°, 45°, 90°, ...] values
3. Update `COLOR_RGB` dictionary to match main experiment
4. Document which subjects used which experiment version

---

## References

**Experiment Files:**
- `colorBlind_pilotTest.py`: Pilot experiment (sub-01, non-uniform RGB)
- `colorBlind_test.py`: Main experiment (proper Lab color space)
- `naive_analysis.py`: Analysis script (updated for pilot)

**Analysis Scripts:**
- `compute_actual_lab_hue.py`: Compute Lab hue from RGB
- `compare_all_colors.py`: Compare all three color sets

**Methodology:**
- Brouwer, G. J., & Heeger, D. J. (2009). Decoding and reconstructing color from responses in human visual cortex. *Journal of Neuroscience*, 29(44), 13992-14003.
