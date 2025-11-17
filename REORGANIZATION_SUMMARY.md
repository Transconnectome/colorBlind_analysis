# Results Reorganization Summary

**Date:** November 17, 2025
**Task:** Reorganize analysis results from subject-based to method-ROI-based structure

---

## What Was Done

### 1. ✅ Reorganized Existing Results

**Script:** `reorganize_results.py`

**Action:** Converted two log directories from old to new structure:
- `logs/20251117_021334/` (zscore) → `logs/20251117_021334_reorganized/`
- `logs/20251117_021329/` (voxelSelect) → `logs/20251117_021329_reorganized/`
- Combined into: `logs/20251117_combined_reorganized/`

**Results:**
- 8 method-ROI folders created (4 ROIs × 2 methods)
- 228 files reorganized total
- All files renamed with subject prefix

**New Directory Structure:**
```
logs/20251117_combined_reorganized/
├── README.md
├── zScore_V1/
│   ├── sub-01_log.txt
│   ├── sub-01_results.pkl
│   ├── sub-01_summary.csv
│   ├── sub-01_confusion_matrix.png
│   ├── sub-01_circular_color_space.png
│   ├── sub-01_reconstruction_per_run.png
│   ├── sub-01_universal_hrf.png
│   ├── sub-02_log.txt
│   ├── ...
├── zScore_V2/
├── zScore_V3/
├── zScore_hV4/
├── voxelSelect_V1/
├── voxelSelect_V2/
├── voxelSelect_V3/
└── voxelSelect_hV4/
```

---

### 2. ✅ Created Output Management System

**File:** `output_manager.py`

**Purpose:** Unified output path management for new structure

**Key Features:**
- Automatic directory creation
- Subject-prefixed filenames
- ROI prefix removal from figures
- Dual logging (terminal + file)
- Clean API for all file types

**Usage Example:**
```python
from output_manager import OutputManager

om = OutputManager(
    subject_id='01',
    roi_name='V1',
    method_name='zScore',
    timestamp='20251117_1234'
)

# Save files
sys.stdout = om.create_dual_logger()
df.to_csv(om.get_summary_path())
plt.savefig(om.get_figure_path('confusion_matrix'))
pickle.dump(results, open(om.get_results_path(), 'wb'))
```

---

### 3. ✅ Created Documentation

**Files Created:**

1. **`REORGANIZED_STRUCTURE_GUIDE.md`**
   - Complete guide to new structure
   - Conversion instructions
   - Benefits and use cases
   - File type reference

2. **`CONVERSION_EXAMPLE.py`**
   - Working example script
   - Side-by-side OLD vs NEW comparison
   - Batch processing examples
   - Successfully tested

3. **`REORGANIZATION_SUMMARY.md`** (this file)
   - Overview of all changes
   - Quick reference

4. **`README.md`** files in each reorganized folder
   - Explains folder structure
   - File naming conventions
   - Subject groups

---

## Comparison: OLD vs NEW

### Directory Structure

| Aspect | OLD (Subject-based) | NEW (Method-ROI-based) |
|--------|-------------------|----------------------|
| **Top level** | `logs/TIMESTAMP/sub-01/` | `logs/TIMESTAMP/zScore_V1/` |
| **Grouping** | By subject | By method-ROI pair |
| **File prefix** | None (in separate folders) | `sub-01_` |
| **Figure folder** | `figures/` subfolder | Same level as other files |
| **ROI in filename** | `V1_confusion_matrix.png` | `confusion_matrix.png` |

### Path Examples

| File Type | OLD | NEW |
|-----------|-----|-----|
| **Log** | `logs/T/sub-01/fir.../zScore/V1.../log.txt` | `logs/T/zScore_V1/sub-01_log.txt` |
| **Summary** | `logs/T/sub-01/.../summary.csv` | `logs/T/zScore_V1/sub-01_summary.csv` |
| **Figure** | `logs/T/sub-01/.../figures/V1_confusion.png` | `logs/T/zScore_V1/sub-01_confusion.png` |

---

## Benefits of New Structure

### 1. **Easier Method Comparison**
```bash
# Compare all V1 results across methods
ls logs/TIMESTAMP/zScore_V1/sub-*_summary.csv
ls logs/TIMESTAMP/voxelSelect_V1/sub-*_summary.csv
```

### 2. **Easier Subject Comparison**
```bash
# View all subjects for one method-ROI
cd logs/TIMESTAMP/zScore_V1/
cat sub-*_summary.csv
```

### 3. **Simplified Analysis**
```python
# Load all results for a method-ROI pair
import pandas as pd
from pathlib import Path

method_roi_dir = Path('logs/TIMESTAMP/zScore_V1')
all_summaries = pd.concat([
    pd.read_csv(f) for f in method_roi_dir.glob('sub-*_summary.csv')
])
```

### 4. **Better Organization**
- Related analyses grouped together
- No nested subject directories
- Consistent file naming
- Easier to navigate

### 5. **Batch Processing**
```bash
# Run all subjects with same timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

for SUBJECT in 01 02 03 04; do
    for ROI in V1 V2 V3 hV4; do
        python script.py \
            --subject $SUBJECT \
            --roi $ROI \
            --method zScore \
            --timestamp $TIMESTAMP
    done
done
```

---

## How to Use

### For Existing Results
1. Run reorganization script:
   ```bash
   python3 reorganize_results.py
   ```

2. Results appear in `*_reorganized/` directories

### For New Analyses

1. Add import to your script:
   ```python
   from output_manager import OutputManager
   ```

2. Create OutputManager:
   ```python
   om = OutputManager(
       subject_id=args.subject,
       roi_name=args.roi,
       method_name='zScore',
       timestamp=args.timestamp
   )
   ```

3. Replace all save paths:
   ```python
   # OLD: summary_df.to_csv(output_dir / "summary.csv")
   # NEW:
   summary_df.to_csv(om.get_summary_path())
   ```

4. See `CONVERSION_EXAMPLE.py` for complete example

---

## File Reference

### Standard Files
| Pattern | Description |
|---------|-------------|
| `sub-{ID}_log.txt` | Analysis log |
| `sub-{ID}_results.pkl` | Pickled results |
| `sub-{ID}_summary.csv` | Summary statistics |

### Figures
| Pattern | Description |
|---------|-------------|
| `sub-{ID}_confusion_matrix.png` | Confusion matrix |
| `sub-{ID}_circular_color_space.png` | Color space plot |
| `sub-{ID}_reconstruction_per_run.png` | Per-run reconstruction |
| `sub-{ID}_universal_hrf.png` | HRF curve |
| `sub-{ID}_polar_reconstruction.png` | Polar plot |
| `sub-{ID}_error_distribution.png` | Error histogram |

### Optional Files
| Pattern | Description |
|---------|-------------|
| `sub-{ID}_{ROI}_mask.nii.gz` | ROI mask (voxel selection) |
| `sub-{ID}_color_{N}_zmap.nii.gz` | Z-map for color N |

---

## Next Steps

### To Modify Existing Analysis Scripts:

1. **Add import:**
   ```python
   from output_manager import OutputManager
   ```

2. **Replace output setup:**
   ```python
   # OLD: 50+ lines of path setup
   # NEW: 6 lines
   om = OutputManager(
       subject_id=SUBJECT_ID,
       roi_name=ROI_NAME,
       method_name=METHOD_NAME,
       timestamp=args.timestamp
   )
   sys.stdout = om.create_dual_logger()
   ```

3. **Update all save calls:**
   - `om.get_summary_path()`
   - `om.get_results_path()`
   - `om.get_figure_path('confusion_matrix')`
   - `om.get_mask_path()`

4. **Test with example:**
   ```bash
   python3 CONVERSION_EXAMPLE.py --subject 01 --roi V1
   ```

### Recommended Priority:

1. ✅ **DONE:** Reorganize existing results
2. ✅ **DONE:** Create OutputManager
3. ✅ **DONE:** Test with example
4. **TODO:** Update main analysis scripts:
   - `troubleshoot/PERSUB_fir_reconstruction_universal_hrf.py`
   - Any other scripts that save results

---

## Summary

### What Changed:
- Directory structure: Subject-based → Method-ROI-based
- File naming: No prefix → `sub-{ID}_` prefix
- Organization: Nested folders → Flat structure
- Access: OutputManager API for all paths

### What Stayed Same:
- File formats (CSV, PNG, PKL, NII.GZ)
- Data content
- Analysis logic
- File contents

### Key Benefit:
**Much easier to compare results across subjects, methods, and ROIs!**

---

## Files Created

1. `reorganize_results.py` - Reorganization script
2. `output_manager.py` - Output path manager
3. `CONVERSION_EXAMPLE.py` - Working example
4. `REORGANIZED_STRUCTURE_GUIDE.md` - Complete guide
5. `REORGANIZATION_SUMMARY.md` - This file
6. `logs/*/README.md` - Per-directory documentation

---

## Questions?

See:
- `REORGANIZED_STRUCTURE_GUIDE.md` for detailed instructions
- `CONVERSION_EXAMPLE.py` for working code
- `output_manager.py` for API documentation

---

**Status:** ✅ Complete and tested
**Date:** 2025-11-17
