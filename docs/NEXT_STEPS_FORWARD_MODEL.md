# Phase 2: Forward Encoding Model & Individual Filter Development

**Date**: 2025-12-18
**Status**: Ready to begin
**Goal**: Create personalized color correction filters for each CVD subject

---

## Background

### Phase 1 Completion ✅

**Key finding**: Individual CVD subjects show statistically significant differences from HC super participant:
- **Sub-08 (Deuteranopia)**: T = 0.132 (V1), 0.178 (V2) - Largest effect
- **Sub-09 (Deuteranopia)**: T = 0.115 (V1), 0.113 (V2) - Moderate effect
- **Sub-10 (Protanomaly)**: T = 0.101 (V1), 0.117 (V2) - Moderate effect

**Implication**: Individual filters are feasible for all 3 CVD subjects! ✅

---

## Overall Strategy

### Big Picture

```
Phase 1: Brain-Space Difference (T)
  ✅ Discovered: CVD_brain - HC_brain = T (for each individual)

Phase 2: Forward Model (Stimulus → Brain)
  🔄 Learn: W such that Brain = f(Stimulus, W)

Phase 3: Inverse Transform (Brain → Stimulus)
  🎯 Compute: Stimulus_correction = g(T, W)

Phase 4: Deep Learning Filter (End-to-End)
  🚀 Optimize: Neural network for direct color correction
```

### Current Position

We have:
- **T_sub08**: Individual brain-space difference (8 colors × 429/233 voxels)
- **T_sub09**: Individual brain-space difference
- **T_sub10**: Individual brain-space difference
- **HC_super**: HC super participant brain patterns

We need:
- **Forward model**: Stimulus → Brain mapping
- **Inverse transform**: T_brain → T_stimulus
- **Color correction filter**: Applied to input images

---

## Phase 2: Forward Encoding Model

### Objective

Learn the mapping from **stimulus colors** → **brain voxel responses**

### Two Approaches

#### Option A: Basis Function Model (Simpler) ⭐ RECOMMENDED

**Method**: Linear model with color-tuned basis functions

```python
# 1. Define color basis functions
def gaussian_basis(color_angle, center, bandwidth):
    """Gaussian tuning curve centered at specific hue"""
    return exp(-((color_angle - center)^2) / (2 * bandwidth^2))

# 2. Create basis set
n_basis = 8  # One per stimulus color
basis_centers = [0, 45, 90, 135, 180, 225, 270, 315]  # deg
basis_bandwidth = 60  # deg (tuning width)

# 3. Fit weights for each voxel
for voxel in range(n_voxels):
    W[voxel, :] = fit_linear_model(
        X = basis_functions(stimulus_angles),
        y = brain_responses[:, voxel]
    )

# 4. Predict brain response
brain_predicted = W @ basis_functions(new_color)
```

**Advantages**:
- Simple, interpretable
- Works with small training data (8 colors)
- Follows Brouwer & Heeger 2009 approach
- Fast to compute

**Limitations**:
- Assumes linear color representation
- May not capture nonlinear effects

#### Option B: Neural Network (More complex)

**Method**: Deep learning model

```python
import torch.nn as nn

class ForwardModel(nn.Module):
    def __init__(self, n_voxels):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(3, 64),      # RGB input
            nn.ReLU(),
            nn.Linear(64, 128),
            nn.ReLU(),
            nn.Linear(128, n_voxels)  # Brain output
        )

    def forward(self, rgb):
        return self.encoder(rgb)

# Train on HC data
model.fit(stimulus_colors, hc_brain_responses)

# Predict for new color
brain_pred = model(new_color)
```

**Advantages**:
- Can capture nonlinear relationships
- More flexible

**Limitations**:
- Needs more training data (we only have 8 colors!)
- Risk of overfitting
- Less interpretable

**Recommendation**: Start with Option A (basis functions) for robustness.

---

## Phase 2 Implementation Plan

### Step 1: Prepare Data

**For HC super participant**:
```python
# Load HC aligned patterns
hc_patterns = load_hc_patterns(['03', '05', '06', '07'], roi='V1')
reference = hc_patterns[0]
hc_aligned = [procrustes_align(reference, p) for p in hc_patterns]
hc_super = np.mean(hc_aligned, axis=0)  # (8 colors, n_voxels)

# Stimulus colors (color wheel angles)
stimulus_angles = [0, 45, 90, 135, 180, 225, 270, 315]  # degrees
```

**For each CVD subject**:
```python
cvd_pattern = load_cvd_pattern(subject_id, roi='V1')
cvd_aligned = procrustes_align(reference, cvd_pattern)
T_individual = cvd_aligned - hc_super  # (8 colors, n_voxels)
```

### Step 2: Train Forward Model (Basis Function)

```python
def create_basis_functions(angles, n_basis=8, bandwidth=60):
    """
    Create Gaussian basis functions

    Args:
        angles: Stimulus color angles (in degrees)
        n_basis: Number of basis functions
        bandwidth: Tuning curve width (in degrees)

    Returns:
        basis: (n_colors, n_basis) matrix
    """
    centers = np.linspace(0, 360, n_basis, endpoint=False)
    basis = np.zeros((len(angles), n_basis))

    for i, angle in enumerate(angles):
        for j, center in enumerate(centers):
            # Handle circular distance
            diff = np.abs(angle - center)
            diff = min(diff, 360 - diff)
            basis[i, j] = np.exp(-(diff**2) / (2 * bandwidth**2))

    return basis

def fit_forward_model(hc_super, stimulus_angles):
    """
    Fit forward model: stimulus → brain

    Args:
        hc_super: (n_colors, n_voxels) HC super participant
        stimulus_angles: (n_colors,) color angles

    Returns:
        W: (n_voxels, n_basis) weight matrix
    """
    basis = create_basis_functions(stimulus_angles)  # (8, 8)

    # Fit weights for each voxel
    W = np.linalg.lstsq(basis, hc_super, rcond=None)[0].T  # (n_voxels, n_basis)

    return W, basis

# Train
W, basis = fit_forward_model(hc_super, stimulus_angles)

# Predict brain response for new color
def predict_brain(color_angle, W, basis_centers, bandwidth):
    basis_response = create_basis_functions([color_angle], len(basis_centers), bandwidth)
    brain_response = basis_response @ W.T  # (1, n_voxels)
    return brain_response[0]
```

### Step 3: Validate Forward Model

```python
# Leave-one-out cross-validation
for test_color_idx in range(8):
    # Train on 7 colors
    train_idx = [i for i in range(8) if i != test_color_idx]
    hc_train = hc_super[train_idx]
    angles_train = [stimulus_angles[i] for i in train_idx]

    W_cv = fit_forward_model(hc_train, angles_train)

    # Predict held-out color
    predicted = predict_brain(stimulus_angles[test_color_idx], W_cv, ...)
    actual = hc_super[test_color_idx]

    # Compute correlation
    r = np.corrcoef(predicted, actual)[0, 1]
    print(f"Color {test_color_idx}: r = {r:.3f}")

# Expected: r > 0.5 (decent prediction)
```

---

## Phase 3: Inverse Transform (Brain → Stimulus)

### Objective

Convert brain-space difference **T** to stimulus-space correction

### Method A: Analytical Inverse (Linear)

```python
def brain_to_stimulus_linear(T_brain, W):
    """
    Convert brain difference to stimulus difference

    Args:
        T_brain: (8, n_voxels) brain-space difference
        W: (n_voxels, n_basis) forward model weights

    Returns:
        T_stimulus: (8, n_basis) stimulus-space correction
    """
    # Pseudo-inverse: T_stimulus = T_brain @ W @ (W.T @ W)^-1
    W_pinv = np.linalg.pinv(W)  # (n_basis, n_voxels)
    T_stimulus = T_brain @ W_pinv.T  # (8, n_basis)

    return T_stimulus

# For each CVD
T_sub08_stimulus = brain_to_stimulus_linear(T_sub08_brain, W)
```

### Method B: Optimization-Based (Nonlinear)

```python
from scipy.optimize import minimize

def find_stimulus_correction(T_brain, W, initial_guess):
    """
    Find stimulus correction that produces observed brain difference

    Solve: argmin ||T_brain - forward(stimulus_corrected) + forward(stimulus_original)||^2
    """
    def loss(stimulus_correction):
        # Predicted brain difference from this stimulus correction
        brain_diff_pred = predict_brain(stimulus_original + stimulus_correction, W) - \
                          predict_brain(stimulus_original, W)

        # Match observed brain difference
        return np.sum((brain_diff_pred - T_brain)**2)

    result = minimize(loss, initial_guess, method='L-BFGS-B')
    return result.x

# For each color
for color_idx in range(8):
    correction = find_stimulus_correction(
        T_brain=T_sub08_brain[color_idx],
        W=W,
        initial_guess=np.zeros(n_basis)
    )
    print(f"Color {color_idx} correction: {correction}")
```

---

## Phase 4: Color Correction Filter

### Objective

Apply stimulus-space correction to create individual color filters

### Filter Types

#### Type 1: Hue Rotation Filter (Simplest)

```python
def create_hue_rotation_filter(T_stimulus):
    """
    Compute optimal hue shift for each color

    Args:
        T_stimulus: (8, n_basis) stimulus corrections

    Returns:
        hue_shifts: (8,) hue rotation in degrees for each stimulus color
    """
    hue_shifts = np.zeros(8)

    for i in range(8):
        # Find dominant correction direction
        basis_weights = T_stimulus[i]

        # Convert to hue shift (weighted average of basis centers)
        centers = np.linspace(0, 360, len(basis_weights), endpoint=False)
        hue_shifts[i] = np.sum(basis_weights * centers) / np.sum(np.abs(basis_weights))

    return hue_shifts

# Apply to image
def apply_hue_filter(image_rgb, hue_shifts, stimulus_angles):
    """
    Apply color correction to image

    For each pixel:
        1. Convert RGB → HSV
        2. Find nearest stimulus color
        3. Apply corresponding hue shift
        4. Convert back to RGB
    """
    image_hsv = rgb2hsv(image_rgb)

    for pixel in image_hsv:
        current_hue = pixel[0] * 360  # Convert to degrees

        # Find nearest stimulus color
        nearest_idx = np.argmin(np.abs(stimulus_angles - current_hue))

        # Apply hue shift
        pixel[0] = (current_hue + hue_shifts[nearest_idx]) % 360 / 360

    return hsv2rgb(image_hsv)
```

#### Type 2: RGB Transformation Matrix

```python
def create_rgb_transform(T_stimulus, stimulus_angles):
    """
    Learn 3×3 color transformation matrix

    For CVD: RGB_corrected = M @ RGB_original
    """
    # Convert T_stimulus to RGB space
    # Fit transformation matrix M
    # This is more complex but more general
    ...
```

#### Type 3: Deep Learning End-to-End ⭐ ULTIMATE GOAL

```python
import torch.nn as nn

class ColorCorrectionNetwork(nn.Module):
    def __init__(self):
        super().__init__()

        # Filter network
        self.filter_net = nn.Sequential(
            nn.Conv2d(3, 64, 3, padding=1),
            nn.ReLU(),
            nn.Conv2d(64, 64, 3, padding=1),
            nn.ReLU(),
            nn.Conv2d(64, 3, 3, padding=1)
        )

        # Frozen brain predictor
        self.brain_predictor = BrainPredictor(W)  # Forward model, frozen

    def forward(self, image_rgb):
        # Apply filter
        image_corrected = image_rgb + self.filter_net(image_rgb)

        # Predict brain response
        brain_response = self.brain_predictor(image_corrected)

        return image_corrected, brain_response

# Loss function
def loss_function(cvd_brain_filtered, hc_brain_target):
    """
    Loss = ||CVD_brain_filtered - HC_brain_target||^2

    Minimize distance between:
        - CVD's brain response to filtered image
        - HC's expected brain response
    """
    return torch.mean((cvd_brain_filtered - hc_brain_target)**2)

# Training
for epoch in range(n_epochs):
    for stimulus_color, cvd_brain, hc_brain in data:
        # Forward pass
        filtered_stimulus, cvd_brain_pred = model(stimulus_color)

        # Compute loss
        loss = loss_function(cvd_brain_pred, hc_brain)

        # Backward pass
        loss.backward()
        optimizer.step()
```

---

## Individual Filter Specifications

Based on Phase 1 results, each CVD needs different correction strength:

### Sub-08 (Deuteranopia) - Strong Correction

**Brain difference**:
- V1: T = 0.132 (2nd largest)
- V2: T = 0.178 (LARGEST overall)

**Filter characteristics**:
- Strong hue rotation needed
- Focus on V2-level correction (larger effect)
- May need separate V1 and V2 based filters

**Expected correction magnitude**: High (15-25° hue shift?)

### Sub-09 (Deuteranopia) - Moderate Correction

**Brain difference**:
- V1: T = 0.115
- V2: T = 0.113
- Consistent across ROIs

**Filter characteristics**:
- Moderate hue rotation
- Similar correction for V1 and V2
- Uniform across visual hierarchy

**Expected correction magnitude**: Moderate (10-15° hue shift?)

### Sub-10 (Protanomaly) - Moderate Correction

**Brain difference**:
- V1: T = 0.101 (smallest in V1)
- V2: T = 0.117 (larger in V2)

**Filter characteristics**:
- Smaller correction in early processing (V1)
- Larger correction needed in V2
- May indicate compensatory processing

**Expected correction magnitude**: Moderate (8-12° hue shift?)

### CVD Type Considerations

**Deuteranopia (Sub-08, 09)**: Green cone absent
- Expected confusion: Red-green axis
- Filter should enhance red-green discrimination
- May need to shift greens toward more discriminable hues

**Protanomaly (Sub-10)**: Red cone deficient (not absent)
- Partial red-green weakness
- Less severe correction needed
- May benefit from contrast enhancement rather than pure hue shift

---

## Implementation Timeline

### Week 1: Forward Model Development
- [ ] Implement basis function model
- [ ] Train on HC super participant (V1, V2)
- [ ] Validate with cross-validation
- [ ] Test prediction accuracy

### Week 2: Inverse Transform & Filter Creation
- [ ] Implement analytical inverse (Method A)
- [ ] Compute T_stimulus for each CVD
- [ ] Create hue rotation filters (Type 1)
- [ ] Test on synthetic stimuli

### Week 3: Filter Validation
- [ ] Apply filters to original experimental stimuli
- [ ] Predict corrected brain responses
- [ ] Compare with target HC responses
- [ ] Measure filter effectiveness

### Week 4: Deep Learning (if needed)
- [ ] Implement end-to-end neural network (Type 3)
- [ ] Train with brain-based loss function
- [ ] Compare with analytical approach
- [ ] Optimize filter parameters

---

## Success Criteria

### Forward Model
- ✅ Cross-validation r > 0.5 (decent prediction)
- ✅ Can reconstruct held-out colors

### Inverse Transform
- ✅ T_stimulus makes sense (interpretable hue shifts)
- ✅ Predicted brain correction matches observed T

### Color Filter
- ✅ Reduces CVD brain difference by >50%
- ✅ Brings CVD brain response closer to HC
- ✅ Preserves perceptual naturalness

### Psychophysical Validation (Future)
- ✅ CVD subjects report improved color discrimination
- ✅ Behavioral testing shows better performance
- ✅ Preference over generic CVD filters

---

## Alternative Approaches

### If Forward Model Struggles

**Problem**: Only 8 training colors may be insufficient

**Solutions**:
1. **Transfer learning**: Use pre-trained visual models
2. **Data augmentation**: Interpolate between training colors
3. **Regularization**: Strong priors on color tuning curves
4. **Simpler model**: Direct T_brain → hue shift mapping

### If Individual Variability Too High

**Problem**: Filters don't generalize across CVD subjects

**Solutions**:
1. **Hybrid approach**: Combine individual + group filters
2. **Adaptive filtering**: Real-time adjustment based on feedback
3. **Multiple filter options**: Let user choose preferred version

---

## Key Questions to Answer

1. **Does the forward model generalize?**
   - Can we predict brain responses to novel colors?
   - Does it work for both V1 and V2?

2. **Is T_stimulus interpretable?**
   - Do we see expected red-green shifts?
   - Different for deuteranopia vs protanomaly?

3. **Does the filter improve brain responses?**
   - CVD_filtered closer to HC_target?
   - Quantifiable improvement?

4. **Can we validate psychophysically?**
   - Collect behavioral data with filtered stimuli
   - Measure discrimination improvement

---

## Resources Needed

### Code
- `analysis/forward_model/train_forward_model.py`
- `analysis/forward_model/inverse_transform.py`
- `analysis/forward_model/create_filters.py`
- `analysis/forward_model/validate_filters.py`

### Data
- HC super participant patterns (V1, V2)
- Individual CVD patterns (V1, V2)
- T matrices (already computed)
- Original stimulus specifications

### Validation
- Test images (natural scenes, Ishihara plates)
- Behavioral testing protocol
- Psychophysical experiments (future)

---

## Expected Outcomes

### Best Case Scenario ✅
- Forward model works well (r > 0.7)
- T_stimulus clearly interpretable
- Filters show measurable improvement
- Ready for psychophysical testing

### Moderate Case ⚠️
- Forward model moderate (r = 0.4-0.6)
- T_stimulus noisy but usable
- Filters show some improvement
- Need refinement before testing

### Challenging Case ❌
- Forward model poor (r < 0.4)
- T_stimulus uninterpretable
- Filters don't improve responses
- Need alternative approach (simpler model or more data)

---

## Next Immediate Steps

1. **Create forward model training script**
2. **Test on HC super participant (V1)**
3. **Validate with cross-validation**
4. **Compute T_stimulus for Sub-08 (largest effect)**
5. **Create prototype hue rotation filter**
6. **Test on experimental stimuli**
7. **Measure improvement**

**Ready to proceed?** Let's start with Step 1: Forward Model Implementation!
