# Recovery Plan: Step-by-Step Guide

**Goal**: Restore working analysis pipeline with correct ROI voxel counts and good performance

---

## 🎯 Quick Summary

**Problem**: ROI masks have wrong voxel counts (310 → 536/553) causing poor performance (52° → 99°)

**Solution**: Find/restore GOOD masks, fix code, verify results, then scale up

---

## 📋 Step-by-Step Recovery

### STEP 1: Diagnose Current State (Server)

```bash
# Upload diagnostic script
scp diagnose_server.sh haba6030@node2:/scratch/connectome/haba6030/colorBlind/

# SSH to server
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind

# Make executable and run
chmod +x diagnose_server.sh
bash diagnose_server.sh > diagnostic_output.txt

# Review output
cat diagnostic_output.txt
```

**What to look for**:
- V2 mask with **310 voxels** = GOOD ✅
- V2 mask with **536 or 553 voxels** = BAD ❌

---

### STEP 2A: If GOOD Masks Exist → Preserve Them

```bash
# If you see: derivatives/sub-01/roi/sub-01_V2_mask.nii.gz: 310 voxels

# Create backup immediately!
mkdir -p GOOD_MASKS_BACKUP
cp -r derivatives/sub-01/roi/*.nii.gz GOOD_MASKS_BACKUP/

# List what you saved
ls -lh GOOD_MASKS_BACKUP/
python3 check_voxel_count.py GOOD_MASKS_BACKUP/*.nii.gz
```

---

### STEP 2B: If GOOD Masks Don't Exist → Rebuild Them

```bash
# Need to use the BEST working configuration

# First, upload backup code
scp backup/fir_reconstruction_universal_hrf_BEST.py \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/

# Check what config it needs
grep "from config import cfg" fir_reconstruction_universal_hrf_BEST.py

# Upload correct config if needed
scp config.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/

# Rebuild ROI masks
python build_roi_masks.py --subject 01  # Use '01' for pilot data

# Verify voxel counts
python check_voxel_count.py derivatives/sub-01/roi/*.nii.gz
```

**Expected output**:
```
sub-01_V1_mask.nii.gz: 511 voxels
sub-01_V2_mask.nii.gz: 310 voxels
sub-01_V3_mask.nii.gz: 89 voxels
sub-01_hV4_mask.nii.gz: 55 voxels
```

---

### STEP 3: Fix Current Analysis Code

**Choose ONE approach**:

#### Option A: Use Backup Code (Fastest)

```bash
# Simply use the proven working version
cp backup/fir_reconstruction_universal_hrf_BEST.py fir_reconstruction_universal_hrf.py

# Ensure config.py matches
# config.py should have SUB_ID = '01' for pilot

# Done!
```

#### Option B: Fix Troubleshoot Code

Edit `troubleshoot/fir_reconstruction_universal_hrf.py`:

**Fix 1**: Ensure using res-2 files (around line 200)
```python
# Current code loads data around line 176-200
# Make sure pattern includes res-2:
func_path = f"{FMRIPREP_DIR}/func/{FILE_PREFIX}_task-rsvp_run-{run}_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz"
```

**Fix 2**: Check universal HRF peak finding (around line 600-700)
```python
# Should be finding MAXIMUM (peak), not minimum or zero
optimal_delay_idx = np.argmax(universal_hrf_mean)  # Correct
# NOT: optimal_delay_idx = 0  # Wrong!
```

**Fix 3**: Verify PCA application happens BEFORE forward model

---

### STEP 4: Test Single ROI

```bash
# Activate conda environment
conda activate nilearn

# Run single test - Pilot V2 (best ROI)
python fir_reconstruction_universal_hrf.py \
    --subject P01 \
    --roi V2 \
    --use-pca \
    --n-components 20

# Check results
cat derivatives/sub-P01/fir_reconstruction/V2_universal_hrf/summary.csv
```

**SUCCESS Criteria**:
```csv
ROI,Method,N_voxels,Optimal_delay_TRs,...,Novel_color_error_deg
V2,universal_hrf,310,5,...,52.4
```

**FAILURE Indicators**:
- N_voxels ≠ 310 → Wrong ROI mask
- Optimal_delay_TRs = 0 → HRF peak detection broken
- Optimal_delay_TRs ≠ 5 → Using wrong reference or timing off
- Novel_color_error_deg > 90 → Model not generalizing

---

### STEP 5: If Test Failed → Debug

#### Debug 1: Check what ROI mask was loaded
```python
import nibabel as nib
import numpy as np

# Check what mask exists
mask_path = "derivatives/sub-P01/roi/sub-01_V2_mask.nii.gz"
mask = nib.load(mask_path)
n_vox = int(np.sum(mask.get_fdata() > 0))
print(f"Loaded mask has {n_vox} voxels")
print(f"Expected: 310 voxels")
```

#### Debug 2: Check universal HRF computation
Add print statements in code around line 600:
```python
print(f"Universal HRF shape: {universal_hrf_mean.shape}")
print(f"Universal HRF values: {universal_hrf_mean}")
print(f"Peak delay index: {np.argmax(universal_hrf_mean)}")
print(f"Peak value: {universal_hrf_mean.max()}")
```

Expected:
```
Universal HRF shape: (10,)
Universal HRF values: [0.05, 0.15, 0.35, 0.55, 0.78, 0.85, 0.65, 0.42, 0.25, 0.12]
Peak delay index: 5
Peak value: 0.85
```

#### Debug 3: Check functional data loading
```python
print(f"First func image shape: {func_imgs[0].shape}")
print(f"Expected: (X, Y, Z, T) where X×Y×Z = 97×115×97")
```

---

### STEP 6: Once Verified → Create Batch Files

Create `run_pilot_all_rois.sbatch`:
```bash
#!/bin/bash
#SBATCH --job-name=pilot_rois
#SBATCH --output=logs/pilot_%A_%a.out
#SBATCH --error=logs/pilot_%A_%a.err
#SBATCH --time=4:00:00
#SBATCH --mem=32G
#SBATCH --cpus-per-task=4
#SBATCH --nodelist=node2
#SBATCH --array=0-3

# ROI names
ROIS=(V1 V2 V3 hV4)
ROI=${ROIS[$SLURM_ARRAY_TASK_ID]}

echo "Processing Pilot subject, ROI: $ROI"

# Activate environment
source ~/.bashrc
conda activate nilearn

# Run analysis
python fir_reconstruction_universal_hrf.py \
    --subject P01 \
    --roi $ROI \
    --use-pca \
    --n-components 20

echo "Completed: $ROI"
```

Then for test subjects:
```bash
#!/bin/bash
# run_test_subject.sbatch
#SBATCH --job-name=test_sub
#SBATCH --output=logs/sub%A_%a.out
#SBATCH --time=4:00:00
#SBATCH --mem=32G
#SBATCH --cpus-per-task=4
#SBATCH --nodelist=node2

# Usage: sbatch --export=SUBJECT=02,ROI=V2 run_test_subject.sbatch

source ~/.bashrc
conda activate nilearn

echo "Processing Subject: $SUBJECT, ROI: $ROI"

# Build ROI mask if needed
python build_roi_masks.py --subject $SUBJECT

# Check if mask exists
ROI_MASK="derivatives/sub-${SUBJECT}/roi/sub-${SUBJECT}_${ROI}_mask.nii.gz"
if [ ! -f "$ROI_MASK" ]; then
    echo "ERROR: ROI mask not found: $ROI_MASK"
    exit 1
fi

# Run analysis
python fir_reconstruction_universal_hrf.py \
    --subject $SUBJECT \
    --roi $ROI \
    --use-pca \
    --n-components 20

echo "Completed"
```

---

### STEP 7: Execute Full Analysis

```bash
# Run pilot (all 4 ROIs in parallel)
sbatch run_pilot_all_rois.sbatch

# Monitor
squeue -u haba6030

# Once pilot done, run test subjects
for subj in 02 03 04; do
    for roi in V1 V2 V3 hV4; do
        sbatch --export=SUBJECT=$subj,ROI=$roi run_test_subject.sbatch
    done
done
```

---

### STEP 8: Download & Summarize Results

```bash
# Download from server
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/sub-*/fir_reconstruction \
    /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/results/

# Or download logs
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/logs/sub-* \
    /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/logs/

# Summarize
python summarize_all_subjects.py
```

---

## ✅ Success Verification

After recovery, you should see:

### Pilot (P01) Results:
| ROI | Voxels | Delay | Novel Error | Status |
|-----|--------|-------|-------------|--------|
| V2 | 310 | 5 TRs | ~52° | ✅ Best |
| V1 | 511 | 5 TRs | ~64° | ✅ Good |
| hV4 | 55 | 5 TRs | ~75° | ✅ OK |
| V3 | 89 | 9 TRs | ~133° | ❌ Expected fail |

### All numbers match original good results!

---

## 🚨 Troubleshooting

### Issue: Still getting 536 voxels after rebuild

**Possible causes**:
1. Wrong reference image being used
2. Brain mask intersection not applied
3. Using different atlas threshold

**Solution**:
```bash
# Check build_roi_masks.py carefully
# Add debug prints to see what reference is being used
python build_roi_masks.py --subject P01 2>&1 | tee roi_build_debug.log
grep "reference" roi_build_debug.log
```

---

### Issue: Optimal delay still shows 0 TRs

**Cause**: HRF peak finding logic is broken

**Solution**:
```python
# In fir_reconstruction_universal_hrf.py
# Find the universal HRF computation section
# Add explicit check:

print(f"DEBUG: Universal HRF mean = {universal_hrf_mean}")
optimal_delay_idx = int(np.argmax(universal_hrf_mean))
print(f"DEBUG: Optimal delay index = {optimal_delay_idx}")
print(f"DEBUG: Optimal delay TRs = {FIR_DELAYS[optimal_delay_idx]}")
```

---

### Issue: Novel error still >90°

**Check**:
1. Are you using the correct color mapping (pilot vs test)?
2. Is PCA being applied correctly?
3. Is leave-one-color-out validation working?

---

## 📞 Summary

1. **Diagnose**: Run diagnose_server.sh
2. **Preserve**: Save any GOOD masks (310 voxels)
3. **Fix**: Use backup code or fix troubleshoot code
4. **Test**: Single ROI, verify 310 voxels, 5 TRs, 52° error
5. **Scale**: Batch process all subjects/ROIs
6. **Verify**: Check all results match expected values

**Key metric**: V2 with 310 voxels, 52° novel error = SUCCESS!
