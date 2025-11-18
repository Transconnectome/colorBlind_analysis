### 4.3 Alternative: fir_reconstruction_zScore_voxelSelect.py

**File:** `/scratch/connectome/haba6030/colorBlind/fir_reconstruction_zScore_voxelSelect.py` (1,901 lines)

**Key Difference from zscore version:** Functional voxel selection after Z-score extraction

---

#### 4.3.1 UNIQUE FEATURE: Functional Voxel Selection

**⭐ NO SEPARATE FUNCTION - Direct implementation in main code flow**

The voxelSelect version is **IDENTICAL** to the zScore version (Section 4.2) except for this additional step inserted between Z-score extraction and PCA.

**Lines 625-684: Functional Voxel Selection (ACTUAL CODE)**

```python
# ============================================================================
# FUNCTIONAL VOXEL SELECTION (Color vs Gray, p < 0.01)
# ============================================================================

print(f"[5B/8] Functional voxel selection (|max_z| > {Z_THRESHOLD})")
print(f"  This implements: Anatomical ROI ∩ Functional Localizer")
sys.stdout.flush()

# ⭐ STEP 1: Compute max |z-score| across all 8 colors and all runs
# Purpose: Identify color-responsive voxels (Color vs Gray contrast)
max_abs_z_per_voxel = np.max(np.abs(all_betas), axis=(0, 1))  # (n_voxels,)
#                            ↑                   ↑      ↑
#                       all_betas shape:  (6 runs, 8 colors, n_voxels)
#                       Compute max across BOTH runs and colors
#                       Result: single max |z| value per voxel

# ⭐ STEP 2: Apply threshold
# Default: Z_THRESHOLD = 2.3 (p < 0.01, two-tailed)
selected_voxels_mask = max_abs_z_per_voxel > Z_THRESHOLD  # Boolean mask

# ⭐ STEP 3: Statistics BEFORE selection
n_voxels_anatomical = n_voxels
n_voxels_selected = selected_voxels_mask.sum()
selection_percentage = 100.0 * n_voxels_selected / n_voxels_anatomical

print(f"  Anatomical ROI voxels: {n_voxels_anatomical}")
print(f"  Functional threshold: |z| > {Z_THRESHOLD} (p < 0.01)")
print(f"  Selected voxels: {n_voxels_selected} ({selection_percentage:.1f}%)")
print(f"  Removed voxels: {n_voxels_anatomical - n_voxels_selected} ({100-selection_percentage:.1f}%)")
print()

# ⭐ STEP 4: Safety check - ensure minimum voxels for stable decoding
MIN_VOXELS_REQUIRED = 10  # Need at least 10 voxels for stable decoding

if n_voxels_selected < MIN_VOXELS_REQUIRED:
    print("=" * 80)
    print(f"ERROR: Insufficient voxels after functional selection!")
    print(f"  Selected: {n_voxels_selected} voxels")
    print(f"  Required: {MIN_VOXELS_REQUIRED} voxels minimum")
    print()
    print("Possible solutions:")
    print(f"  1. Lower z-threshold (current: {Z_THRESHOLD})")
    print(f"     Try: --z-threshold 1.96 (p < 0.05) or 1.64 (p < 0.10)")
    print(f"  2. Use larger anatomical ROI")
    print(f"  3. Use universal_hrf or zScore method (no voxel selection)")
    print()
    print(f"Voxel selection statistics:")
    print(f"  Max |z| range: [{max_abs_z_per_voxel.min():.2f}, {max_abs_z_per_voxel.max():.2f}]")
    print(f"  Voxels with |z| > 2.0: {(max_abs_z_per_voxel > 2.0).sum()}")
    print(f"  Voxels with |z| > 1.96: {(max_abs_z_per_voxel > 1.96).sum()}")
    print(f"  Voxels with |z| > 1.64: {(max_abs_z_per_voxel > 1.64).sum()}")
    print("=" * 80)
    sys.stdout.flush()
    sys.exit(1)

# ⭐ STEP 5: Statistics of SELECTED voxels
max_z_selected = max_abs_z_per_voxel[selected_voxels_mask]
print(f"  Selected voxel statistics:")
print(f"    Mean max |z|: {max_z_selected.mean():.2f} ± {max_z_selected.std():.2f}")
print(f"    Range max |z|: [{max_z_selected.min():.2f}, {max_z_selected.max():.2f}]")
print()
sys.stdout.flush()

# ⭐ STEP 6: Apply selection to data
all_betas = all_betas[:, :, selected_voxels_mask]  # (n_runs, n_colors, n_selected_voxels)
#           ↑ Filter all_betas to keep only selected voxels
#           ↑ This reduces the third dimension from n_voxels_anatomical to n_voxels_selected

n_voxels = n_voxels_selected  # Update voxel count for downstream analyses

print(f"  Data shape after selection: {all_betas.shape}")
print(f"  Updated n_voxels: {n_voxels}")
print()
sys.stdout.flush()
```

---

#### 4.3.2 Conceptual Overview

**Anatomical ROI ∩ Functional Localizer Approach (Brouwer & Heeger 2009)**

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Anatomical ROI (Wang 2015 atlas)                        │
│    → All V1/V2/V3/hV4 voxels in participant's brain        │
│    → Example: V2 = 235 voxels                              │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Functional Localizer (Color vs Gray)                    │
│    → For each voxel: max |z-score| across 8 colors         │
│    → Keep only: |z| > 2.3 (p < 0.01)                       │
│    → Example: 41 voxels pass threshold (17.4%)             │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Selected Voxels (Anatomical ∩ Functional)               │
│    → Only color-responsive voxels in anatomical ROI        │
│    → Removes ~78-85% of non-responsive voxels              │
│    → Reduces noise, improves computational efficiency       │
└─────────────────────────────────────────────────────────────┘
```

---

#### 4.3.3 Motivation for Voxel Selection

**Problem:** Not all anatomically-defined ROI voxels respond to color

**Solution:** Use functional localizer to identify color-responsive voxels

**Benefits:**
1. **Noise reduction:** Remove non-responsive voxels
2. **Computational efficiency:** 5-6x fewer voxels (235 → 41)
3. **B&H 2009 compliance:** Paper uses "Color vs Gray" contrast
4. **Biological validity:** Focus on functionally-relevant voxels

**Trade-offs:**
- Slightly worse reconstruction (+2.6° error)
- Risk of removing weakly-responsive voxels
- Need sufficient voxels for stable decoding (≥10)

---

#### 4.3.4 Command-Line Control

**Z-threshold parameter** (fir_reconstruction_zScore_voxelSelect.py):

```python
# Lines 169-173: Argument parser
parser.add_argument('--z-threshold', type=float, default=2.3,
                    help='Z-score threshold for voxel selection (default: 2.3, p<0.01)')
```

**Usage examples:**

```bash
# Default: p < 0.01 (two-tailed)
python fir_reconstruction_zScore_voxelSelect.py --roi V2 --z-threshold 2.3

# More lenient: p < 0.05 (two-tailed)
python fir_reconstruction_zScore_voxelSelect.py --roi V2 --z-threshold 1.96

# Very lenient: p < 0.10 (two-tailed)
python fir_reconstruction_zScore_voxelSelect.py --roi V2 --z-threshold 1.64
```

---

#### 4.3.5 Save Selection Mask

**Lines 686-697: Save selected voxels as NIfTI**

```python
# Save selection mask for visualization/quality control
selection_mask_data = np.zeros(roi_img.get_fdata().shape)

# Get voxel coordinates from original ROI
roi_coords = np.where(roi_img.get_fdata() > 0)

# Mark selected voxels with their max |z| value
for i in np.where(selected_voxels_mask)[0]:
    selection_mask_data[roi_coords[0][i], roi_coords[1][i], roi_coords[2][i]] = max_abs_z_per_voxel[i]

# Save as NIfTI
selection_mask_img = nib.Nifti1Image(selection_mask_data, roi_img.affine, roi_img.header)
selection_mask_path = f"{OUTPUT_DIR}/selected_voxels_mask.nii.gz"
nib.save(selection_mask_img, selection_mask_path)
print(f"Saved selection mask: {selection_mask_path}")
```

**Output file:** `derivatives/{timestamp}/sub-{ID}/zScore/{ROI}_universal_hrf/selected_voxels_mask.nii.gz`

- **Values:** Max |z-score| for selected voxels, 0 for excluded voxels
- **Purpose:** Visualize which voxels were selected (overlay on anatomical image)

---

#### 4.3.6 Performance Comparison (From Results)

**Overall Statistics (4 subjects × 4 ROIs = 16 configurations):**

| Method | Avg N_voxels | Classification Acc | Reconstruction Error (deg) | Novel Color Error (deg) |
|--------|--------------|-------------------|---------------------------|------------------------|
| **zscore** (all voxels) | 235.0 ± 185.9 | 1.00 ± 0.00 | 20.19 ± 23.64 | 84.88 ± 25.40 |
| **voxelSelect** (|z|>2.3) | 41.4 ± 29.9 | 1.00 ± 0.00 | 22.81 ± 20.65 | 91.17 ± 25.38 |

**Key Observations:**
- ✅ **5.7× fewer voxels** (235 → 41)
- ✅ **Perfect classification** maintained (100%)
- ⚠️ **Slightly worse reconstruction** (+2.6°, still good)
- ⚠️ **Slightly worse novel colors** (+6.3°, both poor)

**Trade-off:** Dramatic voxel reduction with minimal performance loss!

---

#### 4.3.7 Best Configurations

**Top 3 Lowest Reconstruction Errors (voxelSelect):**

1. **sub-01, V2:** 2.38° (⭐ BEST OVERALL across all methods!)
2. **sub-02, V1:** 4.25°
3. **sub-04, V2:** 8.63°

**Top 3 Lowest Novel Color Errors (voxelSelect):**

1. **sub-03, V2:** 49.63°
2. **sub-04, V2:** 55.13°
3. **sub-01, V2:** 63.50°

**Insight:** V2 shows excellent performance with voxelSelect method

---

#### 4.3.8 When to Use voxelSelect vs zscore

**Use voxelSelect when:**
- ✅ Computational efficiency is important
- ✅ ROI has many non-responsive voxels
- ✅ Sufficient color-responsive voxels exist (>10)
- ✅ Replicating B&H 2009 exactly

**Use zscore (all voxels) when:**
- ✅ Maximum reconstruction accuracy needed
- ✅ Small ROIs (e.g., hV4 with <50 voxels)
- ✅ Uncertain about voxel responsiveness
- ✅ Worried about removing weakly-responsive voxels

---

#### 4.3.9 Remaining Pipeline (IDENTICAL to Section 4.2)

After voxel selection (line 684), the pipeline continues EXACTLY as in `fir_reconstruction_zScore.py`:

1. **PCA** (lines 699-760) - Same as Section 4.2.6
2. **Classification** (lines 1204-1277) - Same as Section 4.2.7
3. **Reconstruction** (lines 1320-1454) - Same as Section 4.2.8
4. **Novel Color Reconstruction** (lines 1466-1554) - Same as Section 4.2.9
5. **Visualization** (lines 763-1202, 1557-1901) - Same as Section 4.2.10

**Key Point:** The only difference is the reduced number of voxels (n_voxels) used in these analyses.

---

#### 4.3.10 Output Directory Structure

**Different naming to distinguish from zscore version:**

```
derivatives/
└── {timestamp}/
    └── sub-{01|02|03|04}/
        └── zScore/  # ⭐ Same parent folder as zscore version
            └── {ROI_NAME}_universal_hrf/
                ├── selected_voxels_mask.nii.gz  # ⭐ NEW: Selection mask
                ├── all_zscores.npy              # (6, 8, n_selected_voxels)
                ├── universal_hrf_mean.npy
                ├── optimal_delay.txt
                ├── classification_results.csv
                ├── reconstruction_results.csv
                ├── novel_reconstruction_results.csv
                └── figures/
                    ├── 1_universal_hrf.png
                    ├── 2_zscore_matrix_full.png
                    ├── 3_pca_components.png
                    └── 4_reconstruction_results.png
```

**Note:** Output files are in same `zScore/` directory but in separate ROI-specific subdirectories, making it easy to compare zscore vs voxelSelect results.

---

#### 4.3.11 Typical Voxel Selection Statistics

**Example: sub-01, V2, z-threshold=2.3**

```
[5B/8] Functional voxel selection (|max_z| > 2.3)
  This implements: Anatomical ROI ∩ Functional Localizer

  Anatomical ROI voxels: 235
  Functional threshold: |z| > 2.3 (p < 0.01)
  Selected voxels: 41 (17.4%)
  Removed voxels: 194 (82.6%)

  Selected voxel statistics:
    Mean max |z|: 3.85 ± 1.12
    Range max |z|: [2.31, 8.42]

  Data shape after selection: (6, 8, 41)
  Updated n_voxels: 41
```

**Interpretation:**
- Started with 235 voxels (anatomical V2)
- 41 voxels significantly respond to color (|z| > 2.3)
- Removed 82.6% of non-responsive voxels
- Selected voxels have strong color responses (mean |z| = 3.85)

---

### Summary: voxelSelect Method

**What it adds:**
- Functional voxel selection (Color vs Gray, p < 0.01)
- Implemented directly in code flow (lines 625-684)
- Command-line control via `--z-threshold` parameter
- Selection mask saved for quality control

**Performance:**
- 5.7× fewer voxels than zscore method
- Minimal reconstruction error increase (+2.6°)
- Perfect classification maintained
- Best individual result: sub-01, V2 = 2.38° reconstruction

**Files referenced:** `/scratch/connectome/haba6030/colorBlind/fir_reconstruction_zScore_voxelSelect.py` (1,901 lines)
