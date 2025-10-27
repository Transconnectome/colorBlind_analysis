# ColorBlind Analysis Summary

## Overview
This document summarizes the key analysis steps and decisions in implementing the Brouwer & Heeger (2009) color decoding pipeline.

## 1. GLM Analysis (2025-10-24 09:00 AM)

### Implementation Details
- **Model**: Finite Impulse Response (FIR) GLM
- **HRF Model**: Glover (canonical)
- **Parameters**:
  - TR: 2.0s
  - Scans: 288
  - Conditions: 8 colors
  - Motion regressors: 6

### Key Decisions
1. Used deconvolution approach following Dale (1999)
2. Included motion parameters as nuisance regressors
3. Generated separate design matrices per run

## 2. ROI Processing (2025-10-24 11:00 AM)

### Implementation Details
- **Atlas**: Wang probabilistic atlas
- **ROIs**: V1, V2, V3, hV4
- **Resolution**:
  - Original: 182×218×182
  - Resampled: 97×115×97

### Technical Steps
1. Load probabilistic ROI masks
2. Resample to functional resolution
3. Apply probability threshold
4. Generate binary masks

## 3. Beta Extraction (2025-10-24 02:00 PM)

### Implementation Details
- **Input**: 4D beta maps (8 colors × 97×115×97)
- **Output**: Color response matrices (8 colors × n_voxels)
- **Process**:
  1. Load beta maps
  2. Apply ROI masks
  3. Reshape to 2D matrices
  4. Store per ROI

### Quality Control
- Shape validation at each step
- Empty mask detection
- Dimension consistency checks

## Next Steps

### Forward Modeling
- Implement basis function encoding
- Set up cross-validation
- Add classification testing

### Visualization
- Add quality control plots
- Generate ROI overlap views
- Plot color response patterns

## Technical Notes

### Data Structure
```
derivatives/
  └── sub-01/
      └── func/
          ├── beta_maps.nii.gz
          └── design_matrices/
```

### Key Functions
- `run_deconv_glm()`: GLM analysis
- `run_roi_build()`: ROI processing
- `run_extract_roi()`: Beta extraction

## References
1. Brouwer & Heeger (2009)
2. Dale (1999) - Deconvolution
3. Wang et al. - Probabilistic atlas