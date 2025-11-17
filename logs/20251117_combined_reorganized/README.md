# Reorganized Analysis Results

## Directory Structure

This directory contains analysis results organized by **method-ROI pairs**.

### Folder Naming Convention
```
{METHOD}_{ROI}/
```

Where:
- **METHOD**: Analysis method (e.g., `zScore`, `voxelSelect`)
- **ROI**: Brain region (e.g., `V1`, `V2`, `V3`, `hV4`)

### File Naming Convention

Within each folder, files are prefixed by subject ID:
```
{SUBJECT}_{filetype}
```

Examples:
- `sub-01_log.txt` - Analysis log for subject 01
- `sub-01_results.pkl` - Pickle file with results
- `sub-01_summary.csv` - Summary statistics
- `sub-01_V1_mask.nii.gz` - ROI mask
- `sub-01_confusion_matrix.png` - Confusion matrix figure
- `sub-01_circular_color_space.png` - Circular color space figure
- `sub-01_reconstruction_per_run.png` - Per-run reconstruction
- `sub-01_universal_hrf.png` - HRF figure

### Available Comparisons

This structure makes it easy to:
1. **Compare methods** for a specific ROI (compare `zScore_V1/` vs `voxelSelect_V1/`)
2. **Compare subjects** within a method-ROI (all files in `zScore_V1/`)
3. **Compare ROIs** for a specific method (compare `zScore_V1/` vs `zScore_V2/`)

### Example Usage

To compare all subjects' performance in V1 using zscore:
```bash
ls zScore_V1/sub-*_summary.csv
```

To view all figures for sub-01 across all methods and ROIs:
```bash
find . -name "sub-01_*.png"
```

### Subject Groups
- **Non-CVD**: sub-01, sub-02
- **CVD**: sub-03, sub-04

---
Generated: 2025-11-17
