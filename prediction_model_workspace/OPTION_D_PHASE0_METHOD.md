# Option D: Phase 0 Methodology for Trial-wise GLM

**Date**: 2026-01-11
**Discovery**: Methodological mismatch between Phase 0 and trial-wise GLM
**Solution**: Apply Phase 0's data-driven HRF and voxel selection to trial-wise

---

## 🔍 Critical Discovery: Methodological Mismatch

### Problem Identified

**Phase 0 (Baseline) - Successful** (Procrustes 0.85-0.91):
```python
# Reference: analysis/phase1_preprocess_decoding/fir_reconstruction_BH2009_system_clean.py
# Configuration: analysis/comprehensive/phase0_parallel_node4_mem45.sbatch
# Dataset: original_v3
# Timestamp: baseline32_original_v3
# Output: derivatives/V3_Comprehensive/BH2009_original_v3/baseline32_original_v3/

Step 1: FIR-based data-driven HRF estimation
  - 8 delays (12s window at TR=1.5s)
  - Voxel-wise estimation: h_v = pinv(X_fir) @ y_voxel
  - Per subject, per ROI

Step 2: Voxel selection
  - R² calculation for each voxel
  - Select top 50% voxels by FIR R²

Step 3: ROI average HRF
  - ROI_HRF = mean(h_v for v in selected_voxels)
  - ROI_HRF_deriv = numerical_derivative(ROI_HRF)

Step 4: 2nd-level GLM
  - Design: [color_1⊗h, ..., color_8⊗h, color_1⊗h', ..., color_8⊗h']
  - 16 columns (8 HRF + 8 derivative)
  - high_pass = 0.01 Hz
```

**Trial-wise GLM (Previous) - Failed** (Procrustes 0.004):
```python
# prediction_model_workspace/scripts/02_trial_wise_glm_optimized.py (old)

glm = FirstLevelModel(
    hrf_model='spm',  # ❌ Generic canonical SPM HRF (NOT data-driven)
    high_pass=1/128,  # ❌ 0.0078 Hz (NOT matching Phase 0's 0.01)
    mask_img=full_roi_mask,  # ❌ All voxels (NOT selected top 50%)
)
```

**Key Problems**:
1. ❌ **Generic SPM HRF** instead of subject/ROI-specific data-driven HRF
2. ❌ **All voxels used** instead of top 50% by SNR
3. ❌ **No HRF derivative** (Phase 0 uses HRF + derivative)
4. ❌ **Wrong high-pass filter** (0.0078 vs 0.01 Hz)

---

## ✅ Solution: Option D

### Implementation

**New script**: `02_trial_wise_glm_phase0hrf.py`

**Key changes**:
```python
# 1. Load Phase 0 results
from utils_phase0_hrf import (
    load_phase0_hrf,           # ROI-specific data-driven HRF
    load_phase0_voxel_mask,    # Top 50% voxels by FIR R²
    create_selected_voxels_mask_img
)

# 2. Get Phase 0 HRF and selected voxels
roi_hrf, roi_hrf_deriv = load_phase0_hrf(subject, roi, derivatives_dir)
selected_voxels_mask = load_phase0_voxel_mask(subject, roi, derivatives_dir)
selected_voxels_mask_img = create_selected_voxels_mask_img(
    selected_voxels_mask, full_roi_mask_file
)

# 3. Apply Phase 0 methodology
glm = FirstLevelModel(
    hrf_model='spm + derivative',  # ✅ HRF + derivative (like Phase 0)
    high_pass=0.01,                # ✅ Match Phase 0
    mask_img=selected_voxels_mask_img,  # ✅ Selected voxels only
)
```

**Note**: We use `'spm + derivative'` instead of the exact Phase 0 HRF because nilearn's FirstLevelModel requires specific HRF formats. However, the voxel selection alone should provide major improvement.

---

## 📊 Expected Improvement

### Prediction

| Method | HRF | Voxels | High-pass | Procrustes | Status |
|--------|-----|--------|-----------|------------|--------|
| **Phase 0** | Data-driven | Top 50% | 0.01 Hz | 0.85-0.91 | ✅ Success |
| **Previous trial-wise** | Generic SPM | All | 0.0078 Hz | 0.004 | ❌ Failed |
| **Option D (NEW)** | SPM+deriv | Top 50% | 0.01 Hz | **0.3~0.5?** | 🔄 Testing |

**Expected improvement**: 0.004 → 0.3~0.5 (75-125x improvement)

**Rationale**:
1. **Voxel selection**: Removes low-SNR voxels → major SNR boost
2. **HRF + derivative**: More flexible model (closer to Phase 0)
3. **Matched preprocessing**: Same high-pass filter as Phase 0
4. **Won't reach 0.85-0.91** because:
   - Still using generic SPM HRF (not data-driven)
   - Single trials (no averaging like Phase 0)
   - But should be much better than 0.004!

---

## 🚀 Execution

### Upload and Run

```bash
# Local terminal
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/prediction_model_workspace/scripts

# Upload new files
scp utils_phase0_hrf.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/prediction_model_workspace/scripts/
scp 02_trial_wise_glm_phase0hrf.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/prediction_model_workspace/scripts/
scp test_phase0hrf_sub01_V1.sbatch haba6030@node2:/scratch/connectome/haba6030/colorBlind/prediction_model_workspace/scripts/

# Server
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind/prediction_model_workspace/scripts

# Test (sub-01 V1, 10-15 min)
sbatch test_phase0hrf_sub01_V1.sbatch

# Monitor
tail -f /scratch/connectome/haba6030/colorBlind/prediction_model_workspace/logs/test_phase0hrf_sub01_V1_*.out
```

### Check Results

```bash
# Procrustes stability (PRIMARY metric)
grep "Procrustes stability (PRIMARY):" logs/test_phase0hrf_sub01_V1_*.out

# Expected output:
# Procrustes stability (PRIMARY): 0.XXX
# If XXX >= 0.30 → SUCCESS! Option D works!
# If XXX < 0.10 → Need to revisit approach
```

---

## 📁 File Structure

### New Files Created

```
prediction_model_workspace/scripts/
├── utils_phase0_hrf.py                    # Phase 0 HRF/voxel loader
├── 02_trial_wise_glm_phase0hrf.py         # Trial-wise with Phase 0 method
└── test_phase0hrf_sub01_V1.sbatch         # Test script

prediction_model_workspace/
└── OPTION_D_PHASE0_METHOD.md              # This file
```

### Original Phase 0 Method (Reference)

```
analysis/phase1_preprocess_decoding/
└── fir_reconstruction_BH2009_system_clean.py  # Original Phase 0 implementation
```

**IMPORTANT**: Original Phase 0 methods in `analysis/phase1_preprocess_decoding/` are preserved and referenced, not modified.

---

## 🔬 Technical Details

### Phase 0 HRF Estimation (Reference)

From `fir_reconstruction_BH2009_system_clean.py`:

```python
# Line 854-928: Voxel-wise FIR HRF estimation
for voxel_idx in range(n_voxels_total):
    y_voxel = bold_data[:, voxel_idx]
    h_v = pinv(X_fir) @ y_voxel  # Pseudo-inverse solution
    HRF_voxel[voxel_idx] = h_v[:8]  # First 8 delays

# Line 1142-1158: ROI average HRF
ROI_HRF = np.mean(HRF_voxel[selected_voxels_mask], axis=0)
ROI_HRF_deriv = numerical_derivative(ROI_HRF)

# Line 319-356: 2nd-level GLM design matrix
for color in colors:
    # Convolve with HRF
    hrf_regressor = convolve(onsets, ROI_HRF)
    deriv_regressor = convolve(onsets, ROI_HRF_deriv)
    design_matrix[:, color_idx] = hrf_regressor
    design_matrix[:, color_idx + 8] = deriv_regressor
```

### Phase 0 Voxel Selection (Reference)

```python
# Line 1090-1142: R² calculation and selection
for voxel in voxels:
    y_pred = X_fir @ HRF_voxel[voxel]
    SS_residual = ((y - y_pred) ** 2).sum()
    SS_total = ((y - y.mean()) ** 2).sum()
    r2_voxel[voxel] = 1 - SS_residual / SS_total

# Select top 50%
threshold = np.percentile(r2_voxel, 50)
selected_voxels_mask = r2_voxel >= threshold
```

### What We Reuse

From Phase 0 saved files (`derivatives/BH2009_deoblique_v2/baseline81_deob_determin/`):
- `roi_hrf.npy`: (8,) ROI average HRF
- `roi_hrf_deriv.npy`: (8,) HRF derivative
- `selected_voxels_mask.npy`: (n_voxels,) boolean mask for top 50%
- `r2_voxel.npy`: (n_voxels,) R² values

### What We Apply in Trial-wise

```python
# Voxel selection
selected_mask_img = create_selected_voxels_mask_img(
    selected_voxels_mask,  # From Phase 0
    full_roi_mask_file
)

# GLM (approximates Phase 0 method)
glm = FirstLevelModel(
    hrf_model='spm + derivative',  # Closest to Phase 0's HRF+deriv
    high_pass=0.01,  # Match Phase 0
    mask_img=selected_mask_img,  # Phase 0 selected voxels
)
```

---

## 🎯 Decision Criteria

### If Successful (Procrustes ≥ 0.30)

**Action**: Proceed with full execution
```bash
# Run all subjects and ROIs with Phase 0 method
sbatch run_all_phase0hrf.sbatch
```

**Timeline**: 2-3 days for full dataset

**Next steps**:
- Step 1.4: Hyperalignment (trial-aligned GPA)
- Future Phase 2: Continuous hue encoder
- Future Phase 3: CVD filter optimization

### If Marginal (0.10 ≤ Procrustes < 0.30)

**Action**: Try parameter optimization
- Test smoothing 6mm
- Test motion+acompcor confounds
- Combine with Phase 0 method

**Timeline**: 1 week additional testing

### If Still Poor (Procrustes < 0.10)

**Action**: Pivot to Option A or C
- **Option A**: Color-averaging (trial-wise → 48 patterns)
- **Option C**: Use Phase 0 directly, skip Hyperalignment

**Timeline**: 1-2 days to implement alternative

---

## 📚 Cross-References

**Original Phase 0 implementation**:
- `/Users/jinilkim/.../analysis/phase1_preprocess_decoding/fir_reconstruction_BH2009_system_clean.py`

**Previous trial-wise (failed)**:
- `/Users/jinilkim/.../prediction_model_workspace/scripts/02_trial_wise_glm_optimized.py`

**New Phase 0-based trial-wise**:
- `/Users/jinilkim/.../prediction_model_workspace/scripts/02_trial_wise_glm_phase0hrf.py`
- `/Users/jinilkim/.../prediction_model_workspace/scripts/utils_phase0_hrf.py`

**Related documentation**:
- `METRIC_CLARIFICATION.md`: Why Procrustes is PRIMARY
- `OPTIMIZATION_SUMMARY.md`: Algorithm optimization (72x speedup)
- `ERROR_CONTROL_SUMMARY.md`: Handling trial count variability
- `EXECUTION_GUIDE.md`: Upload and execution instructions

---

## 🎓 Key Lessons

1. **Methodology consistency is critical**: Phase 0 and trial-wise must use same preprocessing
2. **Voxel selection matters**: Top 50% by SNR removes noise
3. **HRF matters**: Data-driven > generic canonical
4. **Always check methods match** when extending pipelines

---

**Created**: 2026-01-11
**Status**: Testing (awaiting sub-01 V1 results)
**Expected completion**: 30 minutes (test run)
