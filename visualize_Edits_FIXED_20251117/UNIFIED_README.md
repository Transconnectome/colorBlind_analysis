# UNIFIED Analysis Scripts

This directory contains three UNIFIED analysis scripts with all changes integrated:

## Three Main Changes Integrated:

### CHANGE 1: Output Directory Structure
- **OLD**: `derivatives/{timestamp}/{subject}/fir_reconstruction_uni_hrf/{method}/{ROI}/...`
- **NEW**: `logs/{timestamp}/{method}_{ROI}/sub-{ID}_...`
- Uses `OutputManager` class for consistent file naming

### CHANGE 2: PCA with Leave-One-Run-Out CV  
- Each fold fits PCA independently on training set only
- Prevents data leakage
- Reports mean ± std across folds

### CHANGE 3: Accurate Lab→RGB Color Conversion
- Uses actual CIELab values from stimuli
- Proper `lab_to_rgb()` conversion (via skimage.color.lab2rgb)
- Replaces HSV approximation with accurate colors
- Applied to all circular plots and polar visualizations

## Available Scripts:

### 1. UNIFIED_fir_reconstruction_universal_hrf.py
- **Method**: Beta-based (effect_size)
- **Voxels**: All voxels in anatomical ROI
- **Output**: `logs/{timestamp}/universal_hrf_{ROI}/`

### 2. UNIFIED_fir_reconstruction_zScore.py  
- **Method**: Z-score based (statistical weighting)
- **Voxels**: All voxels in anatomical ROI
- **Output**: `logs/{timestamp}/zScore_{ROI}/`
- **Difference from universal_hrf**: Uses z-scores instead of betas

### 3. UNIFIED_fir_reconstruction_zScore_voxelSelect.py
- **Method**: Z-score based with functional voxel selection
- **Voxels**: Only voxels with mean |z| > threshold (default: 2.3)
- **Output**: `logs/{timestamp}/voxelSelect_{ROI}/`
- **Difference from zScore**: Adds voxel selection step

## Usage:

```bash
# Universal HRF (Beta-based)
python UNIFIED_fir_reconstruction_universal_hrf.py \
    --subject 01 \
    --roi V1 \
    --use-pca \
    --n-components 20 \
    --timestamp 20251117_120000

# Z-score based
python UNIFIED_fir_reconstruction_zScore.py \
    --subject 01 \
    --roi V1 \
    --use-pca \
    --n-components 20 \
    --timestamp 20251117_120000

# Z-score with voxel selection
python UNIFIED_fir_reconstruction_zScore_voxelSelect.py \
    --subject 01 \
    --roi V1 \
    --use-pca \
    --n-components 6 \
    --z-threshold 2.3 \
    --timestamp 20251117_120000
```

## Output Structure:

```
logs/
└── 20251117_120000/
    ├── universal_hrf_V1/
    │   ├── sub-01_log.txt
    │   ├── sub-01_results.pkl
    │   ├── sub-01_summary.csv
    │   ├── sub-01_confusion_matrix.png
    │   ├── sub-01_polar_reconstruction.png
    │   └── sub-01_circular_color_space.png
    ├── zScore_V1/
    │   └── [same files as above]
    └── voxelSelect_V1/
        └── [same files as above]
```

## Key Features:

- ✅ Consistent output structure across all methods
- ✅ Accurate color representation in figures
- ✅ No data leakage in PCA (leave-one-run-out CV)
- ✅ Subject-prefixed filenames for multi-subject analysis
- ✅ Timestamp-based versioning for reproducibility

Date: 2025-11-17
