# Diagnostic Report: Analysis Problems After Directory Changes

**Date**: 2025-11-08
**Issue**: After editing file directories and codes, ROI voxel numbers increased and results deteriorated

---

## 🔴 Critical Problems Identified

### Problem 1: ROI Voxel Count Explosion

| Subject | ROI | GOOD Results (Pilot_final_logs) | BAD Results (troubleshoot) | Difference |
|---------|-----|--------------------------------|----------------------------|------------|
| P01 | V2 | **310 voxels** | **536 voxels** | +73% ❌ |
| 01 | V2 | N/A (should not exist) | **553 voxels** | Wrong subject! ❌ |
| P01 | V1 | **511 voxels** | Unknown | - |

**Impact**: More voxels = more noise = worse generalization!

---

### Problem 2: Novel Color Performance Degradation

| Subject | ROI | GOOD Results | BAD Results | Degradation |
|---------|-----|--------------|-------------|-------------|
| P01 | V2 | **52.4°** ✅ (42% better than chance) | **98.8°** ❌ (worse than chance 90°) | **+88%** |
| 01 | V2 | N/A | **86.25°** ❌ | Close to chance |

**Impact**: Model cannot generalize to novel colors anymore!

---

### Problem 3: Optimal Delay Detection Failure

| Subject | ROI | GOOD Results | BAD Results | Issue |
|---------|-----|--------------|-------------|-------|
| P01 | V2 | **5 TRs (7.5s)** ✅ Normal HRF peak | **7 TRs (10.5s)** ⚠️ | Delayed |
| 01 | V2 | N/A | **0 TRs (0s)** ❌ | USING ONSET! |

**Impact**: Wrong delay = extracting signal at wrong time = poor performance!

---

### Problem 4: Subject ID Confusion

**GOOD Setup** (from backup/fir_reconstruction_universal_hrf_BEST.py):
```python
from config import cfg  # Uses old config.py with SUB_ID = '01' (Pilot)
# Derivatives path: derivatives/sub-01/
```

**BAD Setup** (troubleshoot files):
```python
# NO import of config - paths hardcoded
SUBJECT_ID = args.subject  # Could be 'P01' or '01'
# Mixed naming conventions causing path issues
```

**Root Cause**:
- Old system used **sub-01** for PILOT data (inconsistent but working)
- New system tries to use **sub-P01** for PILOT and **sub-01** for test subjects
- ROI masks are being built in **wrong locations** or with **wrong reference images**

---

## 📊 Evidence Summary

### GOOD Results (What We Want to Restore)
**Location**: `logs/Pilot_final_logs/`
**Data**: Pilot subject (P01, but files named sub-01)
```
V2: 310 voxels, 52.4° novel error, 5 TRs optimal delay
V1: 511 voxels, 64.1° novel error, 5 TRs optimal delay
hV4: 55 voxels, 75.0° novel error, 5 TRs optimal delay
V3: 89 voxels, 133.0° novel error, 9 TRs optimal delay (failed)
```

### BAD Results (Current Troubleshoot)
**Location**: `troubleshoot/logs/`
**Data**: Mixed sub-P01 and sub-01 (wrong!)
```
sub-P01/V2: 536 voxels, 98.8° novel error, 7 TRs optimal delay
sub-01/V2: 553 voxels, 86.25° novel error, 0 TRs optimal delay ❌
```

---

## 🔍 Root Causes

### 1. **Config File Mismatch**
- **GOOD code** used `from config import cfg` → Old config.py with `SUB_ID = '01'`
- **BAD code** removed config import → Hardcoded paths with new naming

### 2. **Path Structure Changes**
```bash
# OLD (GOOD):
derivatives/sub-01/roi/sub-01_V2_mask.nii.gz  # Pilot data
derivatives/sub-01/fir_reconstruction/V2_universal_hrf/

# NEW (BAD - attempted):
derivatives/sub-P01/roi/sub-P01_V2_mask.nii.gz  # Pilot
derivatives/sub-01/roi/sub-01_V2_mask.nii.gz    # Test subject
```

### 3. **ROI Mask Building Issues**
Possible causes of voxel count increase:
- ❌ Using wrong reference functional image (different resolution)
- ❌ Not applying brain mask intersection
- ❌ Wrong atlas threshold (should be > 50)
- ❌ Resampling to wrong target space

### 4. **Optimal Delay Logic Error**
The 0 TRs result suggests:
- Code is not finding the HRF peak correctly
- Might be using argmin instead of argmax
- Or universal HRF computation is broken

---

## ✅ Solution Strategy

### Step 1: Restore Working Configuration

**Option A - Use Backup Code (RECOMMENDED)**
```bash
# Copy the BEST working code
cp backup/fir_reconstruction_universal_hrf_BEST.py fir_reconstruction_universal_hrf.py

# Ensure old config.py is correct
# config.py should have:
#   SUB_ID = 'P01' or '01' (for pilot)
#   PROJECT_DIR = local path or server path
```

**Option B - Fix Troubleshoot Code**
Need to fix in `troubleshoot/fir_reconstruction_universal_hrf.py`:
1. Restore proper subject ID handling (P01 → files as sub-01)
2. Fix optimal delay detection (should find peak, not onset)
3. Ensure ROI mask paths match the GOOD structure

---

### Step 2: Rebuild ROI Masks with Correct Settings

**Critical**: Must use EXACT same reference image as GOOD results

```python
# Check what reference was used for GOOD masks:
# - Resolution: 97×115×97 (2mm MNI with res-2)
# - Space: MNI152NLin2009cAsym
# - Atlas threshold: > 50
# - Brain mask: Applied intersection
```

**Action**:
1. Delete incorrect masks in `derivatives/sub-01/roi/` and `derivatives/sub-P01/roi/`
2. Rebuild using `backup/fir_reconstruction_universal_hrf_BEST.py` configuration
3. Verify voxel counts match: V2=310, V1=511, V3=89, hV4=55

---

### Step 3: Verify Analysis Pipeline

**Before running full analysis**:
```bash
# 1. Check ROI mask voxel counts
python check_voxel_count.py

# Expected output:
# sub-01_V2_mask.nii.gz: 310 voxels
# sub-01_V1_mask.nii.gz: 511 voxels
# sub-01_hV4_mask.nii.gz: 55 voxels
# sub-01_V3_mask.nii.gz: 89 voxels
```

```bash
# 2. Run single ROI test
python fir_reconstruction_universal_hrf.py --roi V2 --use-pca --n-components 20

# Expected output:
# N_voxels: 310
# Optimal_delay: 5 TRs
# Novel_error: ~52°
```

---

### Step 4: Correct File Organization

**Recommended Structure** (stick with OLD working convention):
```
derivatives/
└── sub-01/  # Pilot data (even though it's P01)
    ├── roi/
    │   ├── sub-01_V1_mask.nii.gz  (511 voxels)
    │   ├── sub-01_V2_mask.nii.gz  (310 voxels)
    │   ├── sub-01_V3_mask.nii.gz  (89 voxels)
    │   └── sub-01_hV4_mask.nii.gz (55 voxels)
    └── fir_reconstruction/
        └── V2_universal_hrf/
            └── summary.csv

└── sub-02/  # Test subject
    ├── roi/
    └── fir_reconstruction/

└── sub-03/  # Test subject
└── sub-04/  # Test subject
```

**Alternative** (new convention, requires full rewrite):
```
derivatives/
└── sub-P01/  # Pilot with P prefix
└── sub-01/   # Test subject 01
└── sub-02/   # Test subject 02
```

**RECOMMENDATION**: Stick with OLD convention to minimize changes!

---

## 🚀 Immediate Action Plan

### Action 1: Restore Working Code
```bash
# In your local directory
cp backup/fir_reconstruction_universal_hrf_BEST.py fir_reconstruction_universal_hrf.py

# Verify it imports config correctly
grep "from config import cfg" fir_reconstruction_universal_hrf.py
```

### Action 2: Check/Fix config.py
```python
# config.py should match the GOOD setup:
class Config:
    PROJECT_DIR = '/scratch/connectome/haba6030/colorBlind'  # Server
    SUB_ID = '01'  # For pilot (even though it's P01)
    TR = 1.5
    N_RUNS = 6
    VOLS_TO_DROP = 4
    N_COLORS = 8
```

### Action 3: Rebuild ROI Masks
```bash
# Delete potentially incorrect masks
rm -rf derivatives/sub-P01/  # If it exists
rm -rf derivatives/sub-01/roi/*  # Clear old masks

# Rebuild using working configuration
python build_roi_masks.py --subject 01

# Verify voxel counts
python check_voxel_count.py
```

### Action 4: Test Single ROI
```bash
# Run analysis on V2 (best ROI)
python fir_reconstruction_universal_hrf.py --roi V2 --use-pca --n-components 20

# Check output summary
cat derivatives/sub-01/fir_reconstruction/V2_universal_hrf/summary.csv
# Should show: 310 voxels, ~52° novel error, 5 TRs optimal delay
```

### Action 5: Create Clean Batch Files
Once verified locally, create server batch files:
```bash
# For pilot data
sbatch --export=ROI=V2 run_pilot_analysis.sbatch

# For test subjects (future)
sbatch --export=SUBJECT=02,ROI=V2 run_test_analysis.sbatch
```

---

## 📝 Files to Review/Fix

### Priority 1 - Restore These
1. ✅ **fir_reconstruction_universal_hrf.py** - Use backup version
2. ✅ **config.py** - Verify paths and SUB_ID
3. ✅ **roi_build.py** - Should be same (check threshold > 50)
4. ✅ **build_roi_masks.py** - Ensure uses correct reference image

### Priority 2 - Verify These
5. **run_all_subjects.sbatch** - Update for correct paths
6. **submit_all_subjects_all_rois.sh** - Update subject IDs
7. **check_voxel_count.py** - Make sure it checks right paths

### Priority 3 - Clean Up
8. Remove or archive troubleshoot folder once fixed
9. Document working configuration in CLAUDE.md
10. Create new backup of working state

---

## 🎯 Success Criteria

You'll know it's fixed when:
1. ✅ V2 ROI has exactly **310 voxels** (not 536 or 553)
2. ✅ Optimal delay is **5 TRs (7.5s)** (not 0 or 7)
3. ✅ Novel color error is **~52°** (not 86° or 99°)
4. ✅ Classification accuracy is **100%**
5. ✅ All paths use consistent naming (sub-01 for pilot)

---

## 📞 Next Steps

1. **Review this diagnostic** and confirm the analysis
2. **Choose restoration strategy** (Option A or B)
3. **Test locally** before uploading to server
4. **Create clean batch files** for one-shot execution
5. **Document** the working configuration to prevent future issues

---

**Last Updated**: 2025-11-08
**Status**: Problems identified, solution ready to implement
