# Complete Workflow - Commands to Run

This document provides all commands in the correct order to fix the analysis pipeline.

---

## Phase 1: Fix ROI Overlap Problem

### Step 1: Upload Files

```bash
# Upload ROI fix script
scp fix_roi_overlap.py node2:/scratch/connectome/haba6030/colorBlind/

# Upload SLURM script
scp sbatch_fix_roi.sub node2:/scratch/connectome/haba6030/colorBlind/
```

### Step 2: Submit ROI Fix Job

```bash
# SSH to server
ssh node2
cd /scratch/connectome/haba6030/colorBlind

# Submit job
sbatch sbatch_fix_roi.sub

# Check status
squeue -u $USER
```

**Expected runtime:** ~1-2 minutes

### Step 3: Monitor Progress

```bash
# Watch output (job ID will be shown after sbatch)
tail -f logs/fix_roi_XXXXX.out

# Or check when complete
cat logs/fix_roi_XXXXX.out
```

### Step 4: Download Results

```bash
# Download log to verify
scp 'node2:/scratch/connectome/haba6030/colorBlind/logs/fix_roi_*.out' ./logs/

# Download fixed ROI masks (if you want to inspect locally)
scp 'node2:/scratch/connectome/haba6030/colorBlind/derivatives/sub-01/roi/*_fixed_mask.nii.gz' ./derivatives/sub-01/roi/
```

---

## Phase 2: Re-run Diagnostic with Fixed ROIs

### Step 5: Submit Diagnostic Job

```bash
# Still on server
cd /scratch/connectome/haba6030/colorBlind

# Submit diagnostic
sbatch sbatch_diagnostic.sub

# Check status
squeue -u $USER
```

**Expected runtime:** ~15-20 minutes

### Step 6: Download Diagnostic Results

```bash
# On local machine
scp node2:/scratch/connectome/haba6030/colorBlind/derivatives/sub-01/diagnostic_report.txt ./diagnostic_report_AFTER_FIX.txt

scp 'node2:/scratch/connectome/haba6030/colorBlind/logs/diagnostic_*.out' ./logs/

scp 'node2:/scratch/connectome/haba6030/colorBlind/logs/diagnostic_*.err' ./logs/
```

### Step 7: Check if Performance Improved

Look for classification accuracy in the diagnostic output:

```bash
# Check locally
grep "Classification accuracy" diagnostic_report_AFTER_FIX.txt
```

**Expected results:**
- **Before fix:** 12.5% (chance level)
- **After fix:** Should be 25-40% (above chance!)

---

## Phase 3: If Accuracy Improved - Proceed to ML/DL

### Step 8: Upload ML/DL Scripts (if accuracy >25%)

```bash
# Upload model implementations
scp ml_forward_model.py node2:/scratch/connectome/haba6030/colorBlind/
scp compare_forward_models.py node2:/scratch/connectome/haba6030/colorBlind/

# Upload GPU-enabled SLURM script
scp sbatch_ml_comparison.sub node2:/scratch/connectome/haba6030/colorBlind/
```

### Step 9: Wait for GPU Availability

```bash
ssh node2

# Check if node3 (GPU node) is available
sinfo -n node3

# If available, submit job
cd /scratch/connectome/haba6030/colorBlind
sbatch sbatch_ml_comparison.sub

# Monitor
squeue -u $USER
```

**Expected runtime with GPU:** 30-60 minutes

### Step 10: Download ML/DL Results

```bash
# Download comparison results
scp 'node2:/scratch/connectome/haba6030/colorBlind/derivatives/sub-01/*_model_comparison.*' ./derivatives/sub-01/

# Download logs
scp 'node2:/scratch/connectome/haba6030/colorBlind/logs/ml_compare_*.out' ./logs/
```

---

## Quick Reference: All Commands in Sequence

```bash
# ========================================
# LOCAL: Upload ROI fix
# ========================================
scp fix_roi_overlap.py node2:/scratch/connectome/haba6030/colorBlind/
scp sbatch_fix_roi.sub node2:/scratch/connectome/haba6030/colorBlind/

# ========================================
# SERVER: Run ROI fix
# ========================================
ssh node2
cd /scratch/connectome/haba6030/colorBlind
sbatch sbatch_fix_roi.sub
# Wait ~2 minutes
cat logs/fix_roi_*.out  # Verify success

# ========================================
# SERVER: Re-run diagnostic
# ========================================
sbatch sbatch_diagnostic.sub
squeue -u $USER
# Wait ~15-20 minutes
exit

# ========================================
# LOCAL: Download and check results
# ========================================
scp node2:/scratch/connectome/haba6030/colorBlind/derivatives/sub-01/diagnostic_report.txt ./diagnostic_report_AFTER_FIX.txt
grep "accuracy" diagnostic_report_AFTER_FIX.txt

# ========================================
# IF ACCURACY IMPROVED (>25%):
# Upload and run ML/DL comparison
# ========================================
scp ml_forward_model.py compare_forward_models.py sbatch_ml_comparison.sub node2:/scratch/connectome/haba6030/colorBlind/

ssh node2
cd /scratch/connectome/haba6030/colorBlind
sbatch sbatch_ml_comparison.sub
# Wait for GPU availability and job completion (~30-60 min)
exit

# Download ML results
scp 'node2:/scratch/connectome/haba6030/colorBlind/derivatives/sub-01/*_model_comparison.*' ./derivatives/sub-01/
```

---

## Troubleshooting

### If ROI fix fails
```bash
# Check error log
cat logs/fix_roi_*.err

# Common issues:
# - Missing ROI files: Check derivatives/sub-01/roi/ directory exists
# - Missing functional data: Verify output/pilot/sub-01/func/ exists
```

### If diagnostic still shows chance performance
```bash
# Check what went wrong:
cat logs/diagnostic_*.out | grep -A 5 "accuracy"

# Possible issues:
# - ROI fix didn't work (check fixed masks were created)
# - Deeper preprocessing problem
# - Need to implement motion scrubbing
```

### If GPU node unavailable
```bash
# Option 1: Wait for node3
squeue  # Check who's using node3
# Contact admin if needed

# Option 2: Run on CPU (slower but works)
# Edit sbatch_ml_comparison.sub:
# Change: --nodelist=node3 -> --nodelist=node2
# Remove: --gres=gpu:1
# Increase time: -t 3:00:00 -> -t 8:00:00
```

---

## Expected Timeline

| Phase | Task | Duration |
|-------|------|----------|
| 1 | Upload files | 2 min |
| 1 | Fix ROI overlap | 2 min |
| 2 | Re-run diagnostic | 15-20 min |
| 2 | Download & analyze | 2 min |
| 3 | Upload ML/DL scripts | 2 min |
| 3 | Run ML/DL (GPU) | 30-60 min |
| 3 | Download & analyze | 5 min |
| **Total** | | **~60-90 min** |

---

## Success Criteria

### After ROI Fix
- ✅ All fixed ROI masks created (`*_fixed_mask.nii.gz`)
- ✅ V1 shows 190 voxels (100% active)
- ✅ Classification accuracy >25% (above chance)

### After ML/DL Comparison
- ✅ All models complete LOOCV
- ✅ Comparison plots generated
- ✅ Best model identified with R² and accuracy metrics
- ✅ Ready to proceed to CVD correction filter design

---

## What Files Will Be Created

### After ROI Fix
```
derivatives/sub-01/roi/
├── sub-01_V1_fixed_mask.nii.gz
├── sub-01_V2_fixed_mask.nii.gz
├── sub-01_V3_fixed_mask.nii.gz
├── sub-01_hV4_fixed_mask.nii.gz
├── sub-01_BrainMask_fixed_mask.nii.gz
├── sub-01_EarlyVisual_fixed_mask.nii.gz
├── sub-01_Ventral_fixed_mask.nii.gz
└── sub-01_functional_mask.nii.gz
```

### After ML/DL Comparison
```
derivatives/sub-01/
├── V1_model_comparison.pkl
├── V1_model_comparison.png
├── V2_model_comparison.pkl
├── V2_model_comparison.png
├── ... (for each ROI)
```

---

Ready to start? Begin with **Phase 1, Step 1** above!
