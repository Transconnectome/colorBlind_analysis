# Nonlinear Forward Model - Complete Visualization Implementation

**Date**: 2025-11-18
**Topic**: Adding full visualizations to test_nonlinear_models_CORRECTED.py

---

## User Feedback

> "test_nonlinear를 봤는데 현재 visualEdits 폴더에 있는 파일과 다른 부분이 많은 거 같은데요. 특히 시각화 측면에서 수정된 건 거의 반영 안 되지 않았나요"

**Problem Identified:**
- test_nonlinear_models_CORRECTED.py: 610 lines (only 2 simple visualizations)
- visualize_Edits/fir_reconstruction_zScore.py: 1813 lines (comprehensive visualizations)
- Missing: HRF plots, Z-map matrix, PCA analysis, detailed reconstruction plots, circular color space

---

## Solution Approach

**Strategy**: Add visualizations efficiently
- **Model-independent visualizations**: Once only (HRF, Z-maps, PCA explained variance)
- **Model-specific visualizations**: Per model (reconstruction scatter, circular space)

This approach avoids duplication while maintaining all essential visualizations.

---

## Visualizations Added

### 1. Model-Independent (Computed Once)

#### ✅ HRF Visualization (lines 541-567 from baseline)
- **Content**:
  - Individual color HRFs (8 colors)
  - Universal HRF (bold average)
  - Optimal delay marker
- **Output**: `{ROI}_universal_hrf.png`
- **Location**: After FIR model fitting

#### ✅ Z-Map Visualizations (lines 617-822 from baseline)
**Triggered by**: `--save-zmaps` flag

**a) Individual z-maps** (8 NIfTI files + brain visualizations)
- Saved to: `zmaps/color_{1-8}_zmap.nii.gz`
- Brain plots: `color_{1-8}_zmap.png`

**b) Z-Map Matrix** (4-panel figure)
- Top-left: Raw z-scores (colors × voxels)
- Top-right: Sorted by peak color preference
- Bottom-left: Per-color z-score distribution (violin plots)
- Bottom-right: Voxel selectivity statistics (|z| > 2.3)
- **Output**: `{ROI}_zscores_matrix.png`

**c) Per-Color Top Voxels** (8-panel figure)
- Top 100 voxels per color
- Shows z-scores across all colors
- Highlights target color column
- **Output**: `{ROI}_top_voxels_per_color.png`

**d) Color Preference Wheel** (polar plot)
- Voxels plotted at preferred color angle
- Radius = |z-score|
- Red = excitatory, Blue = inhibitory
- Only selective voxels (|z| > 2.3)
- **Output**: `{ROI}_color_preference_wheel.png`

#### ✅ PCA Explained Variance (2-panel figure)
- **Content**:
  - Left: Individual component variance (bar plot, first 20 components)
  - Right: Cumulative explained variance (line plot)
  - Markers show current n_components setting
- **Output**: `{ROI}_pca_explained_variance.png`
- **Statistics**: Prints total variance explained by chosen n_components

### 2. Model-Specific (Per Model Loop)

#### ✅ Per-Run Reconstruction Scatter Plots (6-panel figure)
- **Content**:
  - One subplot per test run
  - True hue (x-axis) vs Reconstructed hue (y-axis)
  - Points colored by actual stimulus colors
  - Perfect reconstruction line (diagonal)
  - Error annotation per run
- **Output**: `{ROI}_{model}_reconstruction_per_run.png`
- **Generated for**: Each model (linear, rf, mlp)

#### ✅ Circular Color Space (2-panel figure)
**Left panel**: Training colors
- True colors at border (large markers)
- All 6 predictions per color (small markers, jittered)
- Position = predicted angle
- Color = true stimulus color
- Shows reconstruction consistency

**Right panel**: Novel colors placeholder
- Currently shows true colors only
- Note: "(Not computed for speed)"
- Can be implemented if needed with leave-one-color-out

- **Output**: `{ROI}_{model}_circular_color_space.png`
- **Generated for**: Each model (linear, rf, mlp)

### 3. Model Comparison (Unchanged)

These were already present:
- ✅ Bar plot with error bars (mean ± std)
- ✅ Boxplot per-run variability
- ✅ Statistical comparison (paired t-test)

---

## Code Structure

### File Size Comparison

```
Before: 610 lines  (basic visualizations only)
After:  1080 lines (full visualization suite)

Baseline: 1813 lines (visualize_Edits/fir_reconstruction_zScore.py)
```

**Efficiency**: ~60% of baseline size while including all essential visualizations

### Key Additions

**Lines 352-374**: Helper functions (lab2rgb_accurate, get_stimulus_color_rgb, circular_mean_deg)

**Lines 457-662**: Z-map visualizations block (if save_zmaps)
- Z-map saving (lines 457-488)
- 4-panel matrix (lines 490-571)
- 8-panel top voxels (lines 573-603)
- Polar preference wheel (lines 605-662)

**Lines 670-724**: PCA explained variance (if save_zmaps)

**Lines 823-940**: Model-specific visualizations (if save_zmaps)
- Per-run scatter (lines 828-863)
- Circular color space (lines 865-940)

---

## Usage

### Basic Run (No detailed visualizations)

```bash
python test_nonlinear_models_CORRECTED.py \
    --subject 01 \
    --roi V2 \
    --n-components 6 \
    --models linear rf mlp
```

**Output**:
- Summary CSV
- Results pickle
- Model comparison plot (bar + boxplot)

### Full Visualization Run (Recommended)

```bash
python test_nonlinear_models_CORRECTED.py \
    --subject 01 \
    --roi V2 \
    --n-components 6 \
    --models linear rf mlp \
    --save-zmaps
```

**Output**:
- All basic outputs PLUS:
- Universal HRF plot
- 8 z-map NIfTI files
- 8 z-map brain visualizations
- Z-score matrix (4-panel)
- Top voxels per color (8-panel)
- Color preference wheel
- PCA explained variance
- Per model: reconstruction scatter (6-panel)
- Per model: circular color space (2-panel)

**Total figures**: ~16-20 PNG files (depending on number of models)

---

## Comparison with visualize_Edits Baseline

### Included Visualizations ✅

| Visualization | visualize_Edits | test_nonlinear_CORRECTED | Notes |
|--------------|-----------------|--------------------------|-------|
| **HRF plot** | ✅ | ✅ | Universal HRF + individual colors |
| **Z-map matrix** | ✅ | ✅ | 4-panel (raw, sorted, distribution, selectivity) |
| **Top voxels per color** | ✅ | ✅ | 8-panel heatmaps |
| **Color preference wheel** | ✅ | ✅ | Polar plot |
| **PCA explained variance** | ✅ (detailed, 4-panel) | ✅ (simplified, 2-panel) | Simplified but sufficient |
| **Per-run reconstruction** | ✅ | ✅ | 6-panel scatter plots |
| **Circular color space** | ✅ | ✅ | Training colors (novel optional) |
| **Model comparison** | ❌ | ✅ | NEW: Bar + boxplot + stats |

### Omitted Visualizations (Rationale)

| Visualization | Reason for Omission |
|--------------|---------------------|
| **PCA component loadings** | Not essential for model comparison, can add if needed |
| **PCA color space (PC1-PC3)** | Less informative than reconstruction plots |
| **Detailed PCA robustness** | Leave-one-run-out variance already shown in results |
| **Classification confusion matrix** | Focus is on reconstruction, not classification |

**Design principle**: Include visualizations that help understand model performance differences, omit those that are model-independent technical details.

---

## File Organization

```
derivatives/{timestamp}/sub-{ID}/zScore_NONLINEAR/{ROI}_universal_hrf/
├── log.txt                                    # Execution log
├── summary.csv                                # Model comparison table
├── results.pkl                                # Detailed results (pickle)
├── figures/                                   # All visualizations
│   ├── V2_universal_hrf.png                  # HRF plot
│   ├── color_1_zmap.png                      # Brain z-map (×8)
│   ├── ...
│   ├── V2_zscores_matrix.png                 # 4-panel z-score matrix
│   ├── V2_top_voxels_per_color.png           # 8-panel top voxels
│   ├── V2_color_preference_wheel.png         # Polar plot
│   ├── V2_pca_explained_variance.png         # 2-panel PCA
│   ├── V2_linear_reconstruction_per_run.png  # 6-panel (per model)
│   ├── V2_linear_circular_color_space.png    # 2-panel (per model)
│   ├── V2_rf_reconstruction_per_run.png      # 6-panel (per model)
│   ├── V2_rf_circular_color_space.png        # 2-panel (per model)
│   ├── V2_mlp_reconstruction_per_run.png     # 6-panel (per model)
│   ├── V2_mlp_circular_color_space.png       # 2-panel (per model)
│   └── model_comparison.png                   # Bar + boxplot
└── zmaps/                                     # Z-map NIfTI files
    ├── color_1_zmap.nii.gz
    ├── ...
    └── color_8_zmap.nii.gz
```

---

## Testing Checklist

### Local Testing (Optional)

```bash
python test_nonlinear_models_CORRECTED.py \
    --subject 01 \
    --roi V2 \
    --n-components 6 \
    --models linear \
    --save-zmaps
```

**Verify**:
- [ ] Log file created
- [ ] Summary CSV with 1 row (linear)
- [ ] Model comparison plot (bar + boxplot)
- [ ] figures/ directory with ~9 PNG files
- [ ] zmaps/ directory with 8 NIfTI files

### Server Testing (Recommended)

**Upload**:
```bash
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis

scp -r forward_models haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp test_nonlinear_models_CORRECTED.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp run_test_nonlinear_CORRECTED.sh haba6030@node2:/scratch/connectome/haba6030/colorBlind/
```

**Run**:
```bash
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind

# Edit SBATCH script to add --save-zmaps
nano run_test_nonlinear_CORRECTED.sh  # Add --save-zmaps to python command

sbatch run_test_nonlinear_CORRECTED.sh
```

**Check**:
```bash
squeue -u haba6030
tail -f logs/test_nonlinear_corrected_*.out
```

**Download**:
```bash
# Find timestamp
ssh haba6030@node2 "ls -lrt /scratch/connectome/haba6030/colorBlind/derivatives/"

# Download results
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/{TIMESTAMP}/ ~/Desktop/
```

---

## Summary of Changes

**Issue**: Visualization coverage was incomplete (~33% of baseline)

**Solution**: Added comprehensive visualization suite matching visualize_Edits

**Result**:
- File size: 610 → 1080 lines (+470 lines, +77%)
- Visualization coverage: 2 plots → 16-20 plots (800-1000% increase)
- Efficiency: 60% of baseline size, 100% essential visualizations

**Key improvements**:
1. ✅ Full z-map analysis (matrix, top voxels, preference wheel)
2. ✅ PCA explained variance visualization
3. ✅ Model-specific reconstruction plots (scatter + circular)
4. ✅ Proper color rendering (CIELab → RGB conversion)
5. ✅ Efficient structure (model-independent once, model-specific per loop)

---

## Next Steps

1. **Test on server** with `--save-zmaps` flag
2. **Verify all visualizations** are generated correctly
3. **Compare results** across models (Linear vs RF vs MLP)
4. **If successful**, consider integrating into main visualize_Edits pipeline

---

**Date completed**: 2025-11-18
**Status**: Ready for testing
**Files updated**: test_nonlinear_models_CORRECTED.py (1080 lines)
