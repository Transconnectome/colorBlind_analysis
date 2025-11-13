# Diagnostic Report v2: ROI Voxel Count & Performance Issues

**Date**: 2025-11-08
**Issue**: After code reorganization, ROI voxel counts increased and novel color performance degraded drastically

---

## 🎯 User Clarification

**Naming Convention (CORRECT)**:
- If `SUB_ID` starts with "P" (pilot): Files use prefix without "P"
  - `SUB_ID = "P01"` → Files are `sub-01_*` (in fMRIPrep)
  - But derivatives should be in `sub-P01/` to distinguish from test subject 01

**Examples**:
```
Pilot (P01):
  - fMRIPrep dir: /storage/.../fmriprep_out/sub-P01/
  - File names: sub-01_task-rsvp_*.nii.gz
  - Derivatives: derivatives/sub-P01/

Test Subject 01:
  - fMRIPrep dir: /storage/.../fmriprep_out/sub-01/
  - File names: sub-01_task-rsvp_*.nii.gz
  - Derivatives: derivatives/sub-01/
```

**The troubleshoot code HAD this logic correct!** So naming isn't the problem.

---

## 🔴 The REAL Problems

### Problem 1: ROI Voxel Count Explosion

| Subject | ROI | GOOD (Pilot_final_logs) | BAD (troubleshoot) | Increase |
|---------|-----|------------------------|-------------------|----------|
| P01 | V2 | **310 voxels** ✅ | **536 voxels** ❌ | +73% |
| 01 (test) | V2 | N/A | **553 voxels** ❌ | - |
| P01 | V1 | **511 voxels** ✅ | ? | - |

**Why this matters**: More voxels = diluted signal + more noise = worse generalization!

---

### Problem 2: Novel Color Performance Collapse

| Subject | ROI | GOOD | BAD | Impact |
|---------|-----|------|-----|--------|
| P01 | V2 | **52.4°** ✅ | **98.8°** ❌ | 88% worse (now worse than chance 90°) |
| 01 | V2 | - | **86.25°** ❌ | Close to chance |

**Catastrophic**: Model went from 42% better than chance → WORSE than chance!

---

### Problem 3: HRF Peak Detection Failure

| Subject | ROI | GOOD Delay | BAD Delay | Issue |
|---------|-----|-----------|-----------|-------|
| P01 | V2 | **5 TRs** (7.5s) ✅ | **7 TRs** (10.5s) ⚠️ | Too late |
| 01 | V2 | - | **0 TRs** (0s) ❌ | **ONSET! NOT PEAK!** |

**Critical**: Extracting beta at TR=0 (stimulus onset) instead of peak response!

---

## 🔍 Root Cause Analysis

### What Changed Between GOOD → BAD?

#### GOOD Setup (backup/fir_reconstruction_universal_hrf_BEST.py)
```python
from config import cfg  # Line 50

# ROI mask path
roi_path = f"derivatives/sub-{cfg.SUB_ID}/roi/sub-{cfg.SUB_ID}_{ROI_NAME}_mask.nii.gz"

# Reference image from config
ref_img = nib.load(config.get_func_img_path(1))
```

#### BAD Setup (troubleshoot/fir_reconstruction_universal_hrf.py)
```python
# NO config import - hardcoded everything

# Multiple path setups
FMRIPREP_BASE = "/storage/connectome/haba6030/fmriprep_out"
PILOT_DIR = "/storage/connectome/haba6030/colorBlind_dataOct"

if SUBJECT_ID == 'P01':
    FMRIPREP_DIR = f"{FMRIPREP_BASE}/sub-P01"
    FILE_PREFIX = "sub-01"
    DERIVATIVE_PREFIX = "sub-P01"
    ...
```

---

## 🧩 Hypothesis: Why Voxel Count Increased

### Possible Causes (in order of likelihood):

#### 1. **Different Reference Functional Image Used** ⭐ MOST LIKELY
```python
# GOOD: Used config.get_func_img_path(1)
# This ensured consistent reference across all ROI builds

# BAD: May have used different run or different resolution
# build_roi_masks.py might be picking a different reference
```

**Test**: Check if reference images have different shapes
- GOOD: Should be 97×115×97 (2mm MNI res-2)
- BAD: Might be different resolution or smoothing

---

#### 2. **Brain Mask Intersection Not Applied**
```python
# In roi_build.py line 127-142:
if os.path.exists(brain_mask_path):
    # Apply intersection
    combined = np.logical_and(roi_bool, brain_bool)
else:
    # Skip intersection - MORE VOXELS!
```

**Test**: Check if brain_mask was found in troubleshoot runs
- If brain mask missing → ROI includes non-brain voxels → Inflated count

---

#### 3. **Atlas Threshold Changed**
```python
# Both files show: part_mask = part_data > 50
# So threshold is same
```
**Not the cause** ✅

---

#### 4. **Resampling Interpolation**
```python
# Both use: interpolation='nearest'
```
**Not the cause** ✅

---

## 🔬 Specific Investigation Needed

### On Server, check:

1. **Compare reference images**:
```bash
# What was used for GOOD masks?
ls -lh /storage/.../fmriprep_out/sub-P01/func/*run-1*preproc_bold.nii.gz

# Check actual dimensions
fslinfo <reference_image.nii.gz>
# Should show: dim1=97, dim2=115, dim3=97
```

2. **Check brain mask availability**:
```bash
# Did brain mask exist when BAD masks were built?
ls -lh derivatives/sub-P01/anat/*brain_mask*
ls -lh /storage/.../fmriprep_out/sub-P01/anat/*brain_mask*
```

3. **Compare actual ROI masks**:
```bash
# GOOD mask (if still exists)
fslstats derivatives/sub-01/roi/sub-01_V2_mask.nii.gz -V
# Should show: 310

# BAD mask
fslstats derivatives/sub-P01/roi/sub-01_V2_mask.nii.gz -V
# Shows: 536 (why?)
```

4. **Check mask file timestamps**:
```bash
ls -lh --time-style=full-time derivatives/sub-*/roi/*V2_mask.nii.gz
# When were they created? Before or after code changes?
```

---

## 🎯 Solution: Restore & Fix

### Step 1: Identify Which Masks Are "GOOD"

```bash
# SSH to server
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind

# Check all V2 masks
python3 << EOF
import nibabel as nib
import glob

masks = glob.glob("derivatives/sub-*/roi/*V2_mask.nii.gz")
for m in sorted(masks):
    img = nib.load(m)
    n_vox = int((img.get_fdata() > 0).sum())
    shape = img.shape[:3]
    print(f"{m}: {n_vox} voxels, shape {shape}")
EOF
```

**Expected**:
- If you see `derivatives/sub-01/roi/sub-01_V2_mask.nii.gz: 310 voxels` → This is GOOD! Keep it!
- If you see `derivatives/sub-P01/roi/sub-01_V2_mask.nii.gz: 536 voxels` → This is BAD! Delete it!

---

### Step 2: Restore Good Masks (if lost)

If GOOD masks (310 voxels for V2) don't exist anymore:

```bash
# Backup BEST code has the correct logic
# Use it to rebuild

# Upload BEST version
scp backup/fir_reconstruction_universal_hrf_BEST.py \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/

# Also need correct config.py
# Check what config was used with BEST code
```

---

### Step 3: Fix Current Code (troubleshoot/)

**Three issues to fix in `troubleshoot/fir_reconstruction_universal_hrf.py`**:

#### Fix 1: Ensure Correct Reference Image
```python
# Around line 176-187 (load functional data)
# Make sure using res-2 files:
def get_func_path(subject_id, run):
    if subject_id == 'P01':
        fmriprep_dir = f"{FMRIPREP_BASE}/sub-P01"
        file_prefix = "sub-01"
    else:
        fmriprep_dir = f"{FMRIPREP_BASE}/sub-{subject_id}"
        file_prefix = f"sub-{subject_id}"

    # CRITICAL: Must include res-2 in pattern!
    pattern = f"{fmriprep_dir}/func/{file_prefix}_task-rsvp_run-{run}_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz"
    return pattern
```

#### Fix 2: Verify Brain Mask Path
In `troubleshoot/build_roi_masks.py`:
```python
def find_brain_mask_in_dir(fmriprep_dir):
    # Check both anat and func directories
    # Ensure it finds the res-2 brain mask

    # For pilot: /storage/.../sub-P01/anat/sub-01_*_res-2_desc-brain_mask.nii.gz
```

#### Fix 3: Check Universal HRF Peak Finding
Around line 600-700 (universal HRF computation):
```python
# Make sure finding PEAK (argmax), not onset (would be argmin or 0)
optimal_delay_idx = np.argmax(universal_hrf_mean)  # Should be argmax!

# NOT:
# optimal_delay_idx = 0  # Wrong!
# optimal_delay_idx = np.argmin(...)  # Wrong!
```

---

### Step 4: Clean Rebuild

```bash
# On server
cd /scratch/connectome/haba6030/colorBlind

# Remove BAD masks
rm -rf derivatives/sub-P01/roi/  # If these are the bad ones

# If derivatives/sub-01/roi/ has GOOD masks (310 voxels), keep them!
# Otherwise rebuild:

# Rebuild with corrected code
python build_roi_masks.py --subject P01

# Verify voxel counts
python check_voxel_count.py derivatives/sub-*/roi/*_mask.nii.gz
```

**Expected output**:
```
sub-01_V2_mask.nii.gz: 310 voxels  ✅
sub-01_V1_mask.nii.gz: 511 voxels  ✅
sub-01_V3_mask.nii.gz: 89 voxels   ✅
sub-01_hV4_mask.nii.gz: 55 voxels  ✅
```

---

### Step 5: Test Analysis

```bash
# Run single test with corrected setup
python fir_reconstruction_universal_hrf.py --subject P01 --roi V2 --use-pca --n-components 20

# Check results
cat derivatives/sub-P01/fir_reconstruction/V2_universal_hrf/summary.csv
```

**Expected**:
```csv
ROI,Method,N_voxels,Optimal_delay_TRs,Use_PCA,N_components,Classification_accuracy,Reconstruction_error_deg,Novel_color_error_deg
V2,universal_hrf,310,5,True,20,1.0,4.1,52.4
```

**NOT**:
```csv
V2,universal_hrf,536,7,True,20,1.0,?,98.8  ❌
```

---

## 📋 Diagnosis Checklist (To Run on Server)

```bash
#!/bin/bash
echo "=== ROI MASK DIAGNOSTIC ==="

echo -e "\n1. Check all ROI mask voxel counts:"
for mask in derivatives/sub-*/roi/*_mask.nii.gz; do
    if [ -f "$mask" ]; then
        python3 -c "import nibabel as nib; img=nib.load('$mask'); print(f'{mask}: {int((img.get_fdata()>0).sum())} voxels')"
    fi
done

echo -e "\n2. Check reference functional image shapes:"
for func in /storage/connectome/haba6030/fmriprep_out/sub-*/func/*run-1*res-2*preproc_bold.nii.gz; do
    if [ -f "$func" ]; then
        python3 -c "import nibabel as nib; img=nib.load('$func'); print(f'{func}: shape {img.shape[:3]}')"
    fi
done

echo -e "\n3. Check brain mask availability:"
for mask in /storage/connectome/haba6030/fmriprep_out/sub-*/anat/*res-2*brain_mask.nii.gz; do
    if [ -f "$mask" ]; then
        echo "Found: $mask"
    fi
done

echo -e "\n4. Compare with expected values:"
echo "Expected: V2=310, V1=511, V3=89, hV4=55"
```

---

## 🎯 Next Actions

### Immediate (Local):
1. ✅ Read this diagnostic
2. ⏳ Prepare fixed code versions
3. ⏳ Create diagnostic script above

### On Server:
4. Run diagnostic checklist
5. Identify which masks are GOOD (310 vox) vs BAD (536 vox)
6. If GOOD masks exist → Use them, delete BAD
7. If GOOD masks lost → Rebuild using backup code
8. Verify one analysis run produces correct results
9. Then scale to all subjects/ROIs

---

## 💡 Key Insights

1. **Naming convention was NOT the problem** - troubleshoot code handled P01→sub-01 correctly
2. **ROI building process changed** - different reference image or missing brain mask intersection
3. **Voxel count is critical** - 310 (good) vs 536 (bad) explains performance drop
4. **HRF peak detection may be broken** - TR=0 suggests using onset not peak
5. **Original GOOD masks might still exist** in `derivatives/sub-01/roi/` - check first before rebuilding!

---

**Priority**: Find and preserve GOOD masks (310 voxels) if they still exist on server!
