# Reorganized Output Structure Guide

## Overview

Results are now organized by **method-ROI pairs** instead of subject-based folders. This makes it much easier to compare:
- Different methods for the same ROI
- Different subjects within a method-ROI combination
- Performance across all conditions

---

## Directory Structure

### OLD STRUCTURE (Subject-based):
```
logs/TIMESTAMP/
  sub-01/
    fir_reconstruction_uni_hrf/
      zScore/
        V1_universal_hrf/
          log.txt
          results.pkl
          summary.csv
          figures/
            V1_confusion_matrix.png
            ...
```

### NEW STRUCTURE (Method-ROI-based):
```
logs/TIMESTAMP/
  zScore_V1/
    sub-01_log.txt
    sub-01_results.pkl
    sub-01_summary.csv
    sub-01_confusion_matrix.png
    sub-01_circular_color_space.png
    sub-01_V1_mask.nii.gz
    sub-02_log.txt
    sub-02_results.pkl
    ...
  zScore_V2/
    sub-01_log.txt
    ...
  voxelSelect_V1/
    sub-01_log.txt
    ...
```

---

## Implementation in Analysis Scripts

### Step 1: Import OutputManager

```python
from output_manager import OutputManager
import sys
```

### Step 2: Create OutputManager Instance

```python
# In your script (e.g., PERSUB_fir_reconstruction_universal_hrf.py)

# Parse arguments
args = parse_args()
SUBJECT_ID = args.subject
ROI_NAME = args.roi
METHOD_NAME = 'zScore'  # or 'voxelSelect', 'rawBeta', etc.

# Create output manager
om = OutputManager(
    subject_id=SUBJECT_ID,
    roi_name=ROI_NAME,
    method_name=METHOD_NAME,
    timestamp='20251117_1234',  # Use same timestamp for all subjects/ROIs in a batch
    create_dirs=True
)
```

### Step 3: Setup Dual Logging

```python
# OLD:
# output_dir = Path(f"logs/TEST/persub/sub-{SUBJECT_ID}/{ROI_NAME}_universal_hrf")
# output_dir.mkdir(parents=True, exist_ok=True)
# log_file = output_dir / "log.txt"
# sys.stdout = DualLogger(log_file)

# NEW:
sys.stdout = om.create_dual_logger()
sys.stderr = sys.stdout
```

### Step 4: Save Results

```python
# OLD:
# summary_csv_path = output_dir / "summary.csv"
# summary_df.to_csv(summary_csv_path, index=False)

# NEW:
summary_df.to_csv(om.get_summary_path(), index=False)
```

### Step 5: Save Figures

```python
# OLD:
# fig_dir = output_dir / "figures"
# fig_dir.mkdir(exist_ok=True)
# confusion_plot_path = fig_dir / f"{ROI_NAME}_confusion_matrix.png"
# plt.savefig(confusion_plot_path, dpi=150, bbox_inches='tight')

# NEW:
plt.savefig(om.get_figure_path('confusion_matrix.png'),
            dpi=150, bbox_inches='tight')
```

### Step 6: Save Pickle Results

```python
# OLD:
# results_pkl_path = output_dir / "results.pkl"
# with open(results_pkl_path, 'wb') as f:
#     pickle.dump(results, f)

# NEW:
with open(om.get_results_path(), 'wb') as f:
    pickle.dump(results, f)
```

### Step 7: Save Masks (if applicable)

```python
# OLD:
# mask_path = output_dir / f"{ROI_NAME}_functional_selection_mask.nii.gz"
# nib.save(mask_img, mask_path)

# NEW:
nib.save(mask_img, om.get_mask_path())
```

---

## Complete Conversion Example

### Before (old structure):
```python
# Setup output
output_dir = Path(f"logs/TEST/persub/sub-{SUBJECT_ID}/{ROI_NAME}_universal_hrf")
output_dir.mkdir(parents=True, exist_ok=True)
fig_dir = output_dir / "figures"
fig_dir.mkdir(exist_ok=True)

# Logging
log_file = output_dir / "log.txt"
sys.stdout = DualLogger(log_file)

# Save summary
summary_csv_path = output_dir / "summary.csv"
summary_df.to_csv(summary_csv_path, index=False)

# Save figures
confusion_plot_path = fig_dir / f"{ROI_NAME}_confusion_matrix.png"
plt.savefig(confusion_plot_path, dpi=150)

circular_plot_path = fig_dir / f"{ROI_NAME}_circular_color_space.png"
plt.savefig(circular_plot_path, dpi=150)

# Save results
results_pkl_path = output_dir / "results.pkl"
with open(results_pkl_path, 'wb') as f:
    pickle.dump(results, f)
```

### After (new structure):
```python
from output_manager import OutputManager

# Setup output manager
om = OutputManager(
    subject_id=SUBJECT_ID,
    roi_name=ROI_NAME,
    method_name='zScore',
    timestamp='20251117_1234'
)

# Logging
sys.stdout = om.create_dual_logger()

# Save summary
summary_df.to_csv(om.get_summary_path(), index=False)

# Save figures
plt.savefig(om.get_figure_path('confusion_matrix'), dpi=150)
plt.savefig(om.get_figure_path('circular_color_space'), dpi=150)

# Save results
with open(om.get_results_path(), 'wb') as f:
    pickle.dump(results, f)
```

---

## Batch Processing Example

For SLURM batch jobs processing multiple subjects:

```python
# generate_sbatch.py
import os
from datetime import datetime

# Use same timestamp for entire batch
TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')

subjects = ['01', '02', '03', '04']
rois = ['V1', 'V2', 'V3', 'hV4']
method = 'zScore'

for subject in subjects:
    for roi in rois:
        cmd = f"""python analysis_script.py \\
            --subject {subject} \\
            --roi {roi} \\
            --method {method} \\
            --timestamp {TIMESTAMP}
        """
        # Submit to SLURM or run locally
```

This ensures all results from the same batch go into the same timestamp directory, making comparison easier.

---

## Reorganizing Existing Results

If you have old results in subject-based structure:

```bash
# Run the reorganization script
python3 reorganize_results.py
```

This will:
1. Scan existing log directories
2. Reorganize into method-ROI structure
3. Rename files with subject prefixes
4. Create combined directory
5. Generate README files

---

## Benefits of New Structure

### 1. Easy Method Comparison
```bash
# Compare all subjects' V1 performance across methods
ls logs/TIMESTAMP/zScore_V1/sub-*_summary.csv
ls logs/TIMESTAMP/voxelSelect_V1/sub-*_summary.csv
```

### 2. Easy Subject Comparison
```bash
# Compare all subjects in one method-ROI
cd logs/TIMESTAMP/zScore_V1/
cat sub-*_summary.csv
```

### 3. Easy ROI Comparison
```bash
# Compare V1 vs V2 for zscore method
diff logs/TIMESTAMP/zScore_V1/ logs/TIMESTAMP/zScore_V2/
```

### 4. Simplified Analysis
```python
# Load all results for a method-ROI pair
import pandas as pd
from pathlib import Path

method_roi_dir = Path('logs/TIMESTAMP/zScore_V1')
all_summaries = []

for csv_file in method_roi_dir.glob('sub-*_summary.csv'):
    df = pd.read_csv(csv_file)
    all_summaries.append(df)

combined = pd.concat(all_summaries, ignore_index=True)
```

---

## File Types Reference

| File Pattern | Description |
|--------------|-------------|
| `sub-{ID}_log.txt` | Analysis log with all output |
| `sub-{ID}_results.pkl` | Pickled results dictionary |
| `sub-{ID}_summary.csv` | Summary statistics table |
| `sub-{ID}_{ROI}_mask.nii.gz` | ROI mask (voxel selection) |
| `sub-{ID}_confusion_matrix.png` | Classification confusion matrix |
| `sub-{ID}_circular_color_space.png` | Circular color visualization |
| `sub-{ID}_reconstruction_per_run.png` | Per-run reconstruction errors |
| `sub-{ID}_universal_hrf.png` | HRF curve |
| `sub-{ID}_polar_reconstruction.png` | Polar reconstruction plot |
| `sub-{ID}_error_distribution.png` | Error histogram |
| `sub-{ID}_color_{N}_zmap.nii.gz` | Z-map for color N (optional) |

---

## Integration with Existing Scripts

To update your existing analysis scripts:

1. Add `from output_manager import OutputManager` at the top
2. Replace output directory creation with `om = OutputManager(...)`
3. Replace all file save paths with `om.get_*_path()` methods
4. Remove manual `figures/` subdirectory creation (not needed)
5. Remove ROI prefix from figure filenames (handled automatically)

See `output_manager.py` for complete API documentation.

---

Generated: 2025-11-17
