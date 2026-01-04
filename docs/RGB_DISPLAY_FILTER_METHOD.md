# RGB Display Filter Method: CVD Color Correction via Brain Pattern Transformation

**Date**: 2025-12-19
**Purpose**: Transform RGB stimuli to induce HC-like brain responses in CVD individuals
**Status**: Method design complete, awaiting implementation

---

## 1. Overview

### 1.1 Goal
Create an RGB display filter that transforms color stimuli such that when CVD individuals view the modified colors, their brain responses resemble those of healthy controls (HC).

```
RGB_original → CVD perception → CVD brain (distorted)
RGB_modified → CVD perception → CVD brain ≈ HC brain (normalized)
```

### 1.2 Key Insight
**Leverage Phase 2A brain-space filter** to guide RGB transformation:
- Phase 2A learned: CVD brain → HC-like brain transformation
- We reverse-engineer: What RGB input produces that HC-like brain response?

### 1.3 Pipeline Components
1. **Brain Filter (Phase 2A)**: CVD voxels → HC-like voxels
2. **Channel Encoder (W matrix)**: Voxels → Color channels (6D)
3. **Basis Functions**: Hue (circular) → Channel responses
4. **Inverse mapping**: Channels → Hue → RGB

---

## 2. Mathematical Framework

### 2.1 Forward Model (Human Vision)

**RGB Stimulus → Brain Response**:
```
RGB (3D) → Retina → LGN → V1/V2 Cortex → Voxel Pattern (n_voxels D)
```

**Measured**: 8 circular colors × CVD subjects
- Input: RGB stimuli (8, 3)
- Output: CVD voxel patterns (8, n_voxels)

### 2.2 Brain Filter (Phase 2A)

**CVD Brain → HC-like Brain**:
```python
F = Y @ A + b

where:
  Y: CVD voxel pattern (8, n_voxels)
  A: Transformation matrix (n_voxels, n_voxels)
  b: Bias vector (n_voxels,)
  F: Filtered (HC-like) voxel pattern (8, n_voxels)
```

**Learned via 3-component loss**:
```python
L = λ_mag × L_magnitude + λ_base × L_baseline + λ_struct × L_RDM

# Magnitude: Scale (L2 norm matching)
# Baseline: Translation (mean matching)
# RDM: Rotation/Shape (correlation-based structure)
```

→ **Geometric transformation similar to Procrustes alignment**

### 2.3 Channel Encoder (W Matrix)

**Voxels → Color Channels**:
```python
C = V @ W

where:
  V: Voxel pattern (8, n_voxels)
  W: Channel weights (n_voxels, 6)
  C: Channel responses (8, 6)
```

**6 Channels**: Idealized color-selective neurons
- Tuned to hues: 0°, 60°, 120°, 180°, 240°, 300°
- Learned from HC subjects (Procrustes-aligned space)

### 2.4 Basis Functions (Hue → Channels)

**Circular color encoding**:
```python
basis[h, i] = cos²(h - center_hue[i])  if cos > 0 else 0

where:
  h: hue angle (0-360°)
  i: channel index (0-5)
  center_hue = [0, 60, 120, 180, 240, 300]
```

**Properties**:
- Periodic (360° wraparound)
- Overlapping tuning curves
- Basis shape: (360, 6)

---

## 3. RGB Display Filter Algorithm

### 3.1 Complete Pipeline

```python
# ============================================================================
# Step 1: Measure CVD brain response to original RGB
# ============================================================================
CVD_raw = load_cvd_amplitudes(subject_id, roi)  # (8, n_voxels)
# Source: GLM beta values (z-scored) from fMRI experiment

# ============================================================================
# Step 2: Apply brain filter (Phase 2A)
# ============================================================================
A, b = load_phase2a_filter(subject_id, roi)  # Learned transformation
target_voxels = CVD_raw @ A + b  # (8, n_voxels)

# target_voxels: What CVD brain SHOULD produce (HC-like pattern)

# ============================================================================
# Step 3: Convert voxels to color channels
# ============================================================================
W = load_channel_encoder(roi)  # (n_voxels, 6)
target_channels = target_voxels @ W  # (8, 6)

# target_channels: Desired color-selective neuron responses

# ============================================================================
# Step 4: Inverse: Channels → Hue (using basis functions)
# ============================================================================
basis = create_basis_functions(n_channels=6)  # (360, 6)

# Pseudo-inverse approach (linear approximation)
basis_pinv = np.linalg.pinv(basis.T)  # (6, 360)
hue_weights = target_channels @ basis_pinv  # (8, 360)

# Find best-matching hue for each color
target_hue = np.argmax(hue_weights, axis=1)  # (8,)

# ============================================================================
# Step 5: Convert Hue → RGB
# ============================================================================
# Assume constant saturation & value (can be adjusted)
saturation = 1.0  # Full saturation
value = 1.0       # Full brightness

RGB_modified = np.zeros((8, 3))
for i in range(8):
    RGB_modified[i] = hsv_to_rgb(target_hue[i], saturation, value)

# ============================================================================
# Result: RGB_modified
# ============================================================================
# When CVD subject views RGB_modified:
#   → CVD perception → CVD brain ≈ target_voxels (HC-like)
```

### 3.2 Key Assumptions

1. **Space Compatibility**:
   - Phase 2A filter output (pseudo-Procrustes aligned) is compatible with W matrix (exact Procrustes-aligned)
   - Justified by: RDM loss in Phase 2A mimics Procrustes geometric structure

2. **Channel Sufficiency**:
   - 6 color channels capture essential hue information
   - Basis functions span the perceptual color space

3. **HSV Representation**:
   - Primary correction in hue dimension
   - Saturation & value can be constant or optimized separately

4. **Linearity**:
   - Pseudo-inverse assumes linear relationship (basis → channels)
   - Valid for small perturbations around measured stimuli

---

## 4. Implementation Details

### 4.1 Data Requirements

**Inputs**:
1. CVD voxel patterns: `derivatives/.../baseline32_deob_determin/.../amplitudes_z.npy`
   - Shape: (n_runs, 8, n_voxels)
   - Processing: Average across runs

2. Phase 2A filter: `results/filters/models/optionD/.../A_matrix.npy`, `b_vector.npy`
   - A: (n_voxels, n_voxels)
   - b: (n_voxels,)

3. Channel encoder: `results/group_level/procrustes_reconstruction/{ROI}/W_common.npy`
   - Shape: (n_voxels, 6)
   - **Issue**: baseline81 W (429 voxels) ≠ baseline32 filter (356 voxels)
   - **Solution**: Train baseline32 W matrix OR wait for baseline81 filter

### 4.2 Voxel Count Alignment

**Current Status**:

| Pipeline | V1 Voxels | V2 Voxels | Status |
|----------|-----------|-----------|--------|
| Reconstruction W (baseline81) | 429 | 279 | ✓ Available |
| Phase 2A Filter (baseline32) | 356 | 172 | ✓ Complete |
| Phase 2A Filter (baseline81) | 429 | 279 | ⏳ Training |

**Options**:

**Option A**: Train baseline32 W matrix
- Pro: Use existing Phase 2A filter immediately
- Pro: Faster (no waiting)
- Con: Need to implement Procrustes reconstruction for baseline32

**Option B**: Wait for baseline81 filter
- Pro: Use existing W matrix
- Pro: More voxels (potentially better)
- Con: Waiting time (1+ hours, V2 especially slow)

**Recommendation**: **Option A** for quick validation, then upgrade to baseline81 if needed.

### 4.3 Code Structure

```python
# File: scripts/compute_rgb_display_filter.py

import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt

def create_basis_functions(n_channels=6):
    """Create 6 idealized color channel basis functions"""
    hues = np.linspace(0, 360, n_channels, endpoint=False)
    basis = np.zeros((360, n_channels))

    for i, center_hue in enumerate(hues):
        for h in range(360):
            dist = np.abs(h - center_hue)
            if dist > 180:
                dist = 360 - dist
            response = np.cos(np.deg2rad(dist))
            if response > 0:
                basis[h, i] = response ** 2
            else:
                basis[h, i] = 0

    return basis

def channels_to_hue(channels, basis):
    """
    Convert channel responses to hue angles

    Args:
        channels: (n_colors, 6) - channel responses
        basis: (360, 6) - basis functions

    Returns:
        hue: (n_colors,) - hue angles in degrees
    """
    # Pseudo-inverse
    basis_pinv = np.linalg.pinv(basis.T)  # (6, 360)
    hue_weights = channels @ basis_pinv  # (n_colors, 360)

    # Find peak
    hue = np.argmax(hue_weights, axis=1)

    return hue

def hsv_to_rgb(h, s, v):
    """
    Convert HSV to RGB

    Args:
        h: hue (0-360)
        s: saturation (0-1)
        v: value (0-1)

    Returns:
        rgb: (r, g, b) in [0, 1]
    """
    h = h / 60.0
    c = v * s
    x = c * (1 - abs((h % 2) - 1))
    m = v - c

    if 0 <= h < 1:
        r, g, b = c, x, 0
    elif 1 <= h < 2:
        r, g, b = x, c, 0
    elif 2 <= h < 3:
        r, g, b = 0, c, x
    elif 3 <= h < 4:
        r, g, b = 0, x, c
    elif 4 <= h < 5:
        r, g, b = x, 0, c
    else:
        r, g, b = c, 0, x

    return np.array([r + m, g + m, b + m])

def compute_rgb_filter(subject_id, roi, baseline='baseline32'):
    """
    Main function to compute RGB display filter

    Args:
        subject_id: '08', '09', or '10'
        roi: 'V1' or 'V2'
        baseline: 'baseline32' or 'baseline81'

    Returns:
        RGB_original: (8, 3) - original stimuli
        RGB_modified: (8, 3) - modified stimuli
        results: dict with intermediate values
    """

    # 1. Load CVD voxel pattern
    pattern_dir = Path(f"results/group_level/phase2a_data_{baseline}/patterns")
    CVD_raw = np.load(pattern_dir / f"sub-{subject_id}" / f"{roi}_pattern.npy")

    # 2. Load Phase 2A filter
    model_dir = Path(f"results/filters/models_{baseline}/optionD")
    # Find timestamp directory
    timestamp_dirs = sorted(model_dir.glob("*"))
    latest = timestamp_dirs[-1]

    A = np.load(latest / f"sub-{subject_id}" / roi / "A_matrix.npy")
    b = np.load(latest / f"sub-{subject_id}" / roi / "b_vector.npy")

    # 3. Apply brain filter
    target_voxels = CVD_raw @ A + b

    # 4. Load W matrix
    W_path = Path(f"results/group_level/procrustes_reconstruction_{baseline}")
    W = np.load(W_path / roi / "W_common.npy")

    # 5. Convert to channels
    target_channels = target_voxels @ W

    # 6. Channels → Hue
    basis = create_basis_functions(6)
    target_hue = channels_to_hue(target_channels, basis)

    # 7. Hue → RGB
    RGB_modified = np.zeros((8, 3))
    for i in range(8):
        RGB_modified[i] = hsv_to_rgb(target_hue[i], s=1.0, v=1.0)

    # Original RGB
    RGB_original = np.array([
        [1.0, 0.0, 0.0],  # Red
        [1.0, 0.5, 0.0],  # Orange
        [1.0, 1.0, 0.0],  # Yellow
        [0.5, 1.0, 0.0],  # Chartreuse
        [0.0, 1.0, 0.0],  # Green
        [0.0, 1.0, 1.0],  # Cyan
        [0.0, 0.0, 1.0],  # Blue
        [1.0, 0.0, 1.0],  # Magenta
    ])

    results = {
        'CVD_raw': CVD_raw,
        'target_voxels': target_voxels,
        'target_channels': target_channels,
        'target_hue': target_hue,
        'original_hue': rgb_to_hue(RGB_original),
        'hue_shift': target_hue - rgb_to_hue(RGB_original),
    }

    return RGB_original, RGB_modified, results

def rgb_to_hue(rgb):
    """Convert RGB to hue angle"""
    hues = []
    for r, g, b in rgb:
        max_c = max(r, g, b)
        min_c = min(r, g, b)
        delta = max_c - min_c

        if delta == 0:
            h = 0
        elif max_c == r:
            h = 60 * (((g - b) / delta) % 6)
        elif max_c == g:
            h = 60 * (((b - r) / delta) + 2)
        else:
            h = 60 * (((r - g) / delta) + 4)

        hues.append(h)

    return np.array(hues)
```

---

## 5. Validation & Analysis

### 5.1 Predicted Outcomes

**For each CVD subject**:
1. **Hue shifts**: Quantify how much each color needs to shift
   - Example: Red → Red+15° for better discrimination from green

2. **Pattern consistency**: Check if shifts align with CVD type
   - Deuteranopia: Red-green confusion → expect shifts in 0-120° range
   - Protanomaly: Weaker red sensitivity → expect red enhancement

3. **Brain pattern verification**:
   - Compute: `RGB_modified → CVD perception → predicted_voxels`
   - Compare: `predicted_voxels` vs `target_voxels` (should match)

### 5.2 Visualization

**Figure 1: Color Wheel Transformation**
- Before: Original 8 colors (circular)
- After: Modified 8 colors
- Arrows showing hue shifts

**Figure 2: RGB Swatches**
- Side-by-side: Original | Modified
- For each of 8 colors

**Figure 3: Hue Shift Bar Chart**
- X-axis: 8 colors
- Y-axis: Hue shift (degrees)
- Separate plots per subject/ROI

**Figure 4: Brain Pattern Validation**
- Target voxels (from filter)
- Predicted voxels (from RGB_modified)
- Correlation & RMSE

---

## 6. Limitations & Future Work

### 6.1 Current Limitations

1. **8 Stimuli Only**:
   - Filter learned from 8 circular colors
   - Generalization to arbitrary colors uncertain

2. **HSV Simplification**:
   - Assumes constant saturation & value
   - Real correction may need S/V adjustment

3. **Linear Inverse**:
   - Pseudo-inverse is linear approximation
   - True human vision is nonlinear

4. **Space Compatibility Assumption**:
   - Assumes filtered voxels ≈ Procrustes-aligned space
   - Empirical validation needed

### 6.2 Extensions

**A. Full RGB Optimization**:
```python
# Instead of hue-only, optimize full RGB
for i in range(8):
    RGB_modified[i] = argmin_{rgb} [
        ||predict_voxels(rgb) - target_voxels[i]||^2  # Brain match
        + λ_perceptual * perceptual_loss(rgb, RGB_original[i])  # Naturalness
        + λ_smooth * ||rgb - RGB_original[i]||^2  # Smoothness
    ]
```

**B. Interpolation for Arbitrary Colors**:
- Train continuous mapping: RGB → Channels
- Use Gaussian process or neural network
- Requires more training data

**C. Personalized Tuning**:
- Individual-specific saturation/value
- Adaptive based on severity
- Real-time fMRI neurofeedback

**D. Behavioral Validation**:
- Implement as real display filter
- Measure color discrimination accuracy
- Compare: original vs modified stimuli

---

## 7. Expected Results (Hypothetical)

### 7.1 Example: sub-08 (Deuteranopia) V1

**Original RGB** → **Modified RGB** (Hue shift):
- Red (0°) → Red-Orange (+15°)
- Orange (30°) → Yellow-Orange (+10°)
- Yellow (60°) → Yellow (+5°)
- Chartreuse (90°) → Chartreuse (0°)
- Green (120°) → Cyan-Green (+10°)
- Cyan (180°) → Cyan (+5°)
- Blue (240°) → Blue (0°)
- Magenta (300°) → Magenta (0°)

**Interpretation**:
- Red-green confusion zone (0-120°): Shifts increase separation
- Blue-yellow zone (180-300°): Minimal shifts (less affected)

### 7.2 Quantitative Metrics

**Brain Pattern Similarity**:
- Target voxels (from filter) vs Predicted voxels (from RGB_modified)
- Expected: Correlation > 0.95, RMSE < 0.1

**Hue Shift Statistics**:
- Mean absolute shift: 5-15° (moderate correction)
- Max shift: 20-30° (red-green boundary)

**RDM Preservation**:
- Original RDM (CVD) vs Modified RDM (predicted)
- Expected: Closer to HC RDM structure

---

## 8. Implementation Timeline

### Phase 1: Data Preparation (Current)
- [x] Phase 2A filter training (baseline32)
- [ ] Phase 2A filter training (baseline81) - in progress
- [ ] W matrix training (baseline32) - **RECOMMENDED NEXT**

### Phase 2: Algorithm Implementation
- [ ] Implement `compute_rgb_display_filter.py`
- [ ] Test on single subject (sub-08 V1)
- [ ] Validate intermediate outputs

### Phase 3: Full Analysis
- [ ] Run all subjects × ROIs (3 × 2 = 6 combinations)
- [ ] Generate visualizations
- [ ] Statistical analysis

### Phase 4: Validation
- [ ] Brain pattern verification
- [ ] Cross-subject consistency
- [ ] CVD-type specific patterns

---

## 9. References & Related Work

### Internal Documents
- `docs/PHASE2A_FILTER_METHODS.md` - Filter learning methodology
- `results/filters/PHASE2A_FILTER_LEARNING_RESULTS.md` - Training results
- `docs/RGB_DISPLAY_FILTER_DISCUSSION.md` - Design discussion

### Key Papers
- Brouwer & Heeger (2009): Color reconstruction from fMRI
- Procrustes analysis in neuroscience
- CVD correction algorithms

---

**Document Status**: Design complete, ready for implementation
**Next Step**: Train baseline32 W matrix OR wait for baseline81 filter
**Contact**: Claude Code assistance session 2025-12-19
