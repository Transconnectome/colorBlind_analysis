# CVD Color Distortion Multi-Panel Figure

Publication-quality 3×4 panel figure showing CVD color representation distortions across anatomical and representational spaces.

## Overview

**Purpose:** Visualize how color vision deficiency (CVD) distorts neural color representations in visual cortex, showing the complete chain from stimulus → anatomy → surface → representation.

**Output:** High-resolution (300 DPI) figure with:
- **3 rows:** One per CVD subject (sub-08 Deutan, sub-09 Protan, sub-10 Deutan)
- **4 columns:**
  - A. Color wheel stimulus (8 isoluminant hues)
  - B. Glass brain with ROI activation
  - C. Posterior inflated cortical surface
  - D. RDM distortion bar plot (CVD - HC differences)

## Quick Start

### Generate V2 figure (strongest effects):
```bash
cd analysis/phase3_decoder_comparing/visualization
conda activate srm  # or nilearn

python create_cvd_distortion_figure.py --roi V2
```

### Generate all ROIs:
```bash
python create_cvd_distortion_figure.py --all-rois
```

## Output Location

```
analysis/phase3_decoder_comparing/visualization/cvd_distortion_figures/
├── cvd_distortion_figure_V1.png  (~15 MB, 6000×4800 px)
├── cvd_distortion_figure_V2.png
├── cvd_distortion_figure_V3.png
└── cvd_distortion_figure_hV4.png
```

## Panel Details

### Panel A: Color Wheel Stimulus
- **Visual:** 8 color patches arranged in circle at 45° intervals
- **Data source:** Hardcoded RGB values from `rdm_visualization.py`
- **Purpose:** Show experimental stimuli

### Panel B: Glass Brain
- **Visual:** Transparent brain (4 views: L/R/Y/Z) with ROI activation overlay
- **Data source:**
  - ROI mask: `analysis/roi_masks/.../sub-{ID}/roi_pipeline/{ROI}_mask_*.nii.gz`
  - Activation: RMS of amplitudes across runs and colors
- **Tool:** `nilearn.plotting.plot_glass_brain()`
- **Colormap:** Reds (0 to 95th percentile)

### Panel C: Posterior Inflated Surface
- **Visual:** Left hemisphere inflated surface (posterior view) with hot colormap
- **Data source:**
  - Surface: fsaverage5 inflated (auto-downloaded via nilearn)
  - Activation: RMS projected to surface via `vol_to_surf()`
  - ROI contours: Not implemented (optional future enhancement)
- **Tool:** `nilearn.plotting.plot_surf_stat_map()`
- **Colormap:** hot (shared scale across all 3 CVD subjects)

### Panel D: RDM Distortion Bars
- **Visual:** Horizontal bar plot of top 10 color pair distortions
- **Data source:**
  - CVD RDM: Computed from `amplitudes_procrustes.npy` using correlation distance
  - HC mean RDM: Average across 7 HC subjects
  - Difference: CVD - HC (positive = increased dissimilarity, negative = decreased)
- **Color coding:**
  - Red bars: CVD > HC (increased dissimilarity)
  - Blue bars: CVD < HC (decreased dissimilarity)
- **Expected patterns:**
  - Deutans (sub-08, sub-10): Red-Green confusion (decreased Red-Grn dissimilarity)
  - Protans (sub-09): Red-Cyan/Blue confusion

## Data Requirements

### Required files per subject:
```
analysis/phase1_preprocess_decoding/results/full_dataset_C010/
└── sub-{ID}/
    └── {ROI_dir}/
        └── amplitudes_procrustes.npy  # (6, 8, n_voxels)

analysis/roi_masks/method3_header_mi/method3_header_mi/
└── sub-{ID}/
    └── roi_pipeline/
        └── {ROI}_mask_thr50_intnearest_binTrue_maskfunc_gmTrue_subjFalse.nii.gz
```

**ROI directory mapping:** hV4 → V4 on disk

### Subjects:
- **CVD:** sub-08 (Deutan), sub-09 (Protan), sub-10 (Deutan)
- **HC:** sub-01 to sub-07 (for mean RDM computation)

## Dependencies

```python
numpy
matplotlib
nibabel
nilearn
scipy
```

Installed in conda environment: `srm` (local) or `nilearn` (server)

## Advanced Usage

### Custom output path:
```bash
python create_cvd_distortion_figure.py --roi V2 \
    --output ~/Desktop/v2_cvd_figure.png
```

### Debug single subject:
```python
from create_cvd_distortion_figure import load_subject_data, compute_rdm_from_amplitudes

# Test data loading
data = load_subject_data('sub-08', 'V2')
print(f"Amplitudes: {data['amplitudes'].shape}")
print(f"RMS range: [{data['rms_activation'].min()}, {data['rms_activation'].max()}]")

# Test RDM computation
rdm = compute_rdm_from_amplitudes(data['amplitudes'])
print(f"RDM shape: {rdm.shape}, diagonal: {np.diag(rdm)}")  # Should be ~0
```

## MATLAB Interactive Viewer (Optional)

For interactive 3D exploration of brain surfaces:

### 1. Prepare data:
```bash
cd analysis/matlab_viewers

# Single subject
python prepare_matlab_surface_data.py --subject sub-08 --roi V2

# All CVD subjects
python prepare_matlab_surface_data.py --all-cvd --roi V2
```

### 2. Launch MATLAB:
```matlab
cd /Users/jinilkim/.../analysis/matlab_viewers
interactive_surface_viewer('sub-08', 'V2')
```

### Features:
- **Mouse controls:** Rotate (left-drag), zoom (scroll), pan (right-drag)
- **UI buttons:**
  - Toggle ROI outline (cyan contour)
  - Cycle views (Posterior → Anterior → Dorsal → Ventral → Lateral)
  - Reset to posterior
  - Adjust surface transparency

### Requirements:
- MATLAB R2020b+ (tested on R2023a)
- GIFTI toolbox (from SPM12 or FieldTrip)
- Pre-prepared surface data (.mat files from Python script)

**Note:** fsaverage5 surface must be converted to GIFTI format. See `prepare_matlab_surface_data.py --export-surfaces` for instructions.

## Troubleshooting

### Error: "Amplitudes not found"
Check that C010 preprocessing completed for all subjects:
```bash
ls -lh analysis/phase1_preprocess_decoding/results/full_dataset_C010/sub-*/*/amplitudes_procrustes.npy
```

### Error: "Mask not found"
Verify ROI masks exist:
```bash
ls -lh analysis/roi_masks/method3_header_mi/method3_header_mi/sub-*/roi_pipeline/*_mask_*.nii.gz
```

### Surface plot looks wrong
- Check that `nilearn` is up to date: `conda update nilearn`
- Verify fsaverage5 downloaded: `~/.nilearn_data/fsaverage5/`
- Try deleting cached surfaces: `rm -rf ~/.nilearn_data/` and re-run

### RDM shows unexpected patterns
1. Verify HC subjects have valid data (check for sub-07 hV4 = 16 voxels issue)
2. Compute HC mean RDM manually and inspect:
   ```python
   from create_cvd_distortion_figure import compute_hc_mean_rdm
   hc_rdm = compute_hc_mean_rdm('V2')
   import matplotlib.pyplot as plt
   plt.imshow(hc_rdm, cmap='viridis')
   plt.colorbar()
   plt.title('HC Mean RDM V2')
   plt.savefig('debug_hc_rdm.png')
   ```

### Figure is too large / out of memory
Reduce DPI in script:
```python
# Line 374 in create_cvd_distortion_figure.py
fig = plt.figure(figsize=(20, 16), facecolor='white', dpi=150)  # Change to 100
# Line 441
plt.savefig(output_path, dpi=200, ...)  # Change to 150
```

## Scientific Interpretation

### Expected patterns by CVD type:

**Deutans (sub-08, sub-10):**
- M-cone deficiency
- Expect decreased dissimilarity: Red-Green, Yellow-Orange
- Expect increased dissimilarity: possible compensatory mechanisms

**Protans (sub-09):**
- L-cone deficiency
- Expect decreased dissimilarity: Red-Cyan, Red-Blue
- More severe than deutans (longer wavelength sensitivity loss)

### ROI differences:
- **V1:** Early visual cortex, cone-opponent signals preserved
- **V2:** Intermediate processing, stronger CVD effects (p=0.075 group, p=0.040 sub-08)
- **V3/hV4:** Higher-level, may show category-based compensation

## File Structure

```
analysis/phase3_decoder_comparing/visualization/
├── create_cvd_distortion_figure.py       # Main script
├── README_cvd_distortion_figure.md       # This file
└── cvd_distortion_figures/               # Output directory
    ├── cvd_distortion_figure_V1.png
    ├── cvd_distortion_figure_V2.png
    ├── cvd_distortion_figure_V3.png
    └── cvd_distortion_figure_hV4.png

analysis/matlab_viewers/
├── interactive_surface_viewer.m          # MATLAB viewer
├── prepare_matlab_surface_data.py        # Data preparation
├── surface_labels/                       # ROI masks (projected)
│   └── sub-{ID}/{ROI}_lh_label.mat
├── surface_data/                         # Functional data (projected)
│   └── sub-{ID}/{ROI}_rms.mat
└── freesurfer_surfaces/                  # fsaverage5 surfaces (GIFTI)
    └── fsaverage5/lh.inflated.gii
```

## References

**Statistical framework:**
- Crawford & Howell (1998) single-case comparisons
- HC-only SRM training to avoid circularity
- Leave-one-out for HC disparity estimates

**Visualization tools:**
- nilearn: Glass brain and surface plotting
- matplotlib: Multi-panel layout and bar plots
- MATLAB: Interactive 3D exploration (optional)

**Related scripts:**
- `analysis/validation/scripts/utils/rdm_visualization.py` - Color definitions
- `analysis/phase2_SRM_across_between/brain_mapping_utils.py` - Volume mapping
- `analysis/phase2_SRM_across_between/visualization/plot_brain_surfaces.py` - Glass brain patterns

## Author & Date

**Generated:** 2026-02-22
**Project:** colorBlind_analysis
**Analysis phase:** Phase 2 decoder comparison (RT-4 validation complete)
