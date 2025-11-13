# 🔄 Complete Restart Plan - Color Reconstruction Analysis
**Date:** 2025-11-09
**Status:** Fresh start from scratch
**Based on:** Pre-Nov 7th documentation and successful results in logs/final*

---

## 📋 Executive Summary

You previously achieved **~100% classification** and **<30° reconstruction error** using the `fir_reconstruction.py` pipeline with PCA(20). After directory reorganization caused file tracking issues, we're restarting from scratch with all lessons learned integrated.

### What We're Recreating:
✅ **Proven successful pipeline** from FIR_MODIFICATIONS_SUMMARY.md
✅ **All bug fixes** identified in bh_anal.py
✅ **Optimal parameters**: PCA(20), best-k voxel selection, correct Lab hues
✅ **Production-ready workflow** with parallel SLURM execution

---

## 🎯 Phase-by-Phase Plan

### Phase 1: Data Preparation & Preprocessing ⚙️

#### 1.1 Directory Structure Setup
**Server:** `node2:/scratch/connectome/haba6030/colorBlind`

```bash
# Expected structure
colorBlind/
├── ProbAtlas_v4/                    # Wang 2015 atlas
├── derivatives/
│   ├── sub-P01/                     # Pilot outputs
│   ├── sub-01/                      # Test subject 1
│   ├── sub-02/                      # Test subject 2
│   ├── sub-03/                      # Test subject 3
│   └── sub-04/                      # Test subject 4
├── fir_reconstruction.py            # Main pipeline (WINNER)
├── fir_reconstruction_universal_hrf.py  # Quick fix alternative
├── config.py                        # Configuration
├── roi_build.py                     # ROI utilities
└── run_*.sbatch                     # SLURM scripts
```

**Action Items:**
```bash
# 1. SSH to server
ssh haba6030@node2

# 2. Navigate to working directory
cd /scratch/connectome/haba6030/colorBlind

# 3. Verify raw data exists
ls /storage/connectome/haba6030/fmriprep_out/sub-P01/func/
ls /storage/connectome/haba6030/colorBlind_dataOct/sub-P01/func/

# 4. Create derivatives structure
mkdir -p derivatives/sub-{P01,01,02,03,04}/{roi,fir_reconstruction}
```

---

#### 1.2 fMRIPrep for Test Subjects
**Goal:** Preprocess sub-01 to sub-04 with IDENTICAL settings to pilot

**Pilot settings (MUST MATCH):**
```bash
fmriprep /data /out participant \
  --participant-label 01 \
  --fs-license-file /opt/freesurfer/license.txt \
  --output-spaces MNI152NLin2009cAsym:res-2 \
  --bold2t1w-dof 6 \
  --nthreads 16 \
  --mem-mb 16000 \
  -w /work
```

**Key parameters:**
- `--output-spaces MNI152NLin2009cAsym:res-2` (ONLY this space, res-2 REQUIRED)
- `--bold2t1w-dof 6` (same as pilot)
- No `--use-syn-sdc` if fieldmap exists
- Expected output: 97×115×97 voxels (2mm MNI)

**CRITICAL:** Verify pilot preprocessing first:
```bash
# Check pilot files exist
ls -lh /storage/connectome/haba6030/fmriprep_out/sub-P01/func/*res-2*preproc*
# Should show: sub-01_task-rsvp_run-{1-6}_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz

# Check dimensions
fslinfo /storage/.../sub-01_task-rsvp_run-1_*_res-2_desc-preproc_bold.nii.gz | grep dim
# Should show: dim1=97, dim2=115, dim3=97
```

**Status for test subjects:**
- sub-P01: ✅ Already preprocessed (pilot)
- sub-01: ⏳ Need to check if exists
- sub-02: ⏳ Need to check if exists
- sub-03: ⏳ Need to check if exists
- sub-04: ⏳ Need to check if exists

**Next Action:**
```bash
# Check which subjects already have fMRIPrep output
for sub in 01 02 03 04; do
    echo "=== sub-${sub} ==="
    ls /storage/connectome/haba6030/fmriprep_out/sub-${sub}/func/*res-2* 2>/dev/null | wc -l
done
```

---

### Phase 2: ROI Construction from Wang Atlas 🧠

#### 2.1 Wang Atlas to Subject Space
**Reference:** `roi_build.py` and `combine_atlas.py`

**ROI mappings (from CLAUDE.md):**
```python
# Wang (2015) atlas ROI definitions
V1:  roi1 (V1v) + roi2 (V1d)
V2:  roi3 (V2v) + roi4 (V2d)
V3:  roi5 (V3v) + roi6 (V3d)
hV4: roi7
VO1: roi8 (check atlas)
```

**Pipeline:**
```python
# Create combined ROI masks
python combine_atlas.py --subject P01 --output-dir derivatives/sub-P01/roi/

# Expected outputs:
# derivatives/sub-P01/roi/sub-P01_V1_mask.nii.gz
# derivatives/sub-P01/roi/sub-P01_V2_mask.nii.gz
# derivatives/sub-P01/roi/sub-P01_V3_mask.nii.gz
# derivatives/sub-P01/roi/sub-P01_hV4_mask.nii.gz
```

**Key parameters:**
- Probabilistic threshold: 25% (default from Wang atlas)
- Target space: MNI152NLin2009cAsym:res-2
- Resampling: Nearest neighbor for masks

**Validation:**
```bash
# Check voxel counts
fslstats derivatives/sub-P01/roi/sub-P01_V2_mask.nii.gz -V
# Expected: ~310 voxels (from previous results)

# Verify overlap with functional data
fslmaths sub-P01_V2_mask.nii.gz -mul bold_mean.nii.gz overlap_check.nii.gz
```

---

#### 2.2 ROI Visualization & QC
**Goal:** Verify ROIs are correctly positioned on visual cortex

**Method 1: Create overlay images**
```python
from nilearn import plotting
import nibabel as nib

# Load functional mean and ROI mask
func_img = nib.load('derivatives/sub-P01/func/sub-P01_task-rsvp_space-MNI_desc-mean_bold.nii.gz')
roi_mask = nib.load('derivatives/sub-P01/roi/sub-P01_V2_mask.nii.gz')

# Plot overlay
plotting.plot_roi(roi_mask, bg_img=func_img,
                  title='V2 ROI Overlay',
                  output_file='derivatives/sub-P01/roi/sub-P01_V2_overlay.png')
```

**Method 2: Check expected voxel counts**
```python
# From previous successful runs:
Expected_V1_voxels = 190-250
Expected_V2_voxels = 280-350
Expected_V3_voxels = 180-230
Expected_hV4_voxels = 100-150

# If counts are way off → check atlas alignment
```

---

### Phase 3: FIR Reconstruction Pipeline 🚀

#### 3.1 Pilot Test Run (V2 ROI)
**Goal:** Replicate ~100% classification, <30° reconstruction on pilot

**Command:**
```bash
# Upload latest code
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis
scp fir_reconstruction.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp config.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp run_fir_reconstruction_single.sbatch haba6030@node2:/scratch/connectome/haba6030/colorBlind/

# SSH to server
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind

# Test single ROI (V2) with PCA(20) - RECOMMENDED
sbatch --export=ROI=V2,USE_PCA=1,N_COMPONENTS=20 run_fir_reconstruction_single.sbatch
```

**Expected Output:**
```
derivatives/sub-P01/fir_reconstruction/V2/
├── log.txt                 # Detailed execution log
├── summary.csv             # Classification: ~100%, Reconstruction: <30°
├── results.pkl             # Full results pickle
└── figures/
    ├── V2_mean_hrf.png    # Universal HRF plot
    └── confusion_matrix.png
```

**Success Criteria:**
- ✅ Classification accuracy: ~100% (vs 12.5% chance)
- ✅ Reconstruction error: <30° (vs 90° chance)
- ✅ No errors in log.txt
- ✅ p < 0.05 for reconstruction

**If it fails:**
1. Check log.txt for errors
2. Verify ROI mask exists and has voxels
3. Verify functional data paths in config.py
4. Check event file format (.tsv with correct columns)

---

#### 3.2 Parallel Execution for All ROIs
**Goal:** Run V1, V2, V3, hV4, VO1 simultaneously

**Upload parallel script:**
```bash
scp run_fir_reconstruction_parallel.sbatch haba6030@node2:/scratch/connectome/haba6030/colorBlind/
```

**Execute:**
```bash
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind

# Run all ROIs in parallel
sbatch run_fir_reconstruction_parallel.sbatch

# Monitor jobs
squeue -u haba6030

# Check outputs in real-time
tail -f logs/fir_recon_*.out
```

**Expected Runtime:** 5-15 min per ROI (parallel)

**Combine Results:**
```bash
# After all jobs complete
cat derivatives/sub-P01/fir_reconstruction/*/summary.csv > all_roi_results.csv

# Download for analysis
scp haba6030@node2:/scratch/connectome/haba6030/colorBlind/all_roi_results.csv ./
```

---

### Phase 4: Validation & QC 📊

#### 4.1 Compare with Previous Results
**Reference:** logs/final* directory (lost but documented in MD files)

**Expected Performance (from FIR_MODIFICATIONS_SUMMARY.md):**

| ROI | Classification | Reconstruction | Status |
|-----|---------------|---------------|--------|
| V1 | ~100% | <20° | Best |
| V2 | ~100% | <30° | Good |
| V3 | ~100% | <35° | Good |
| hV4 | ~100% | <30° | Good |

**Validation Steps:**
```python
import pandas as pd

# Load results
results = pd.read_csv('all_roi_results.csv')

# Check classification
print(results[['ROI', 'Classification_accuracy']])
# All should be >> 12.5% chance (ideally ~100%)

# Check reconstruction
print(results[['ROI', 'Reconstruction_error_deg']])
# All should be << 90° chance (ideally <30°)

# Statistical significance
# p-values should be < 0.05
```

---

#### 4.2 Generate QC Visualizations
**From MEETING_NOTE_251106.md recommendations:**

```python
# 1. Confusion matrices (should be perfect diagonal)
# 2. Reconstruction polar plots (predicted vs true hues)
# 3. HRF curves per ROI (verify reasonable shape)
# 4. Z-score maps for each color (check spatial patterns)
# 5. ROI overlap with functional data
```

**Example visualization code:**
```python
import matplotlib.pyplot as plt
import numpy as np

# Load results pickle
import pickle
with open('derivatives/sub-P01/fir_reconstruction/V2/results.pkl', 'rb') as f:
    results = pickle.load(f)

# Plot confusion matrix
conf_mat = results['confusion_matrix']
plt.imshow(conf_mat, cmap='Blues')
plt.colorbar()
plt.xlabel('Predicted Color')
plt.ylabel('True Color')
plt.title('V2 Classification Confusion Matrix')
plt.savefig('V2_confusion.png')

# Plot reconstruction errors
errors = results['reconstruction_errors']
plt.hist(errors, bins=30)
plt.axvline(90, color='r', linestyle='--', label='Chance (90°)')
plt.xlabel('Reconstruction Error (degrees)')
plt.ylabel('Count')
plt.legend()
plt.title('V2 Reconstruction Error Distribution')
plt.savefig('V2_recon_errors.png')
```

---

### Phase 5: Key Lessons & Best Practices ⚡

#### From FIR_MODIFICATIONS_SUMMARY.md

**✅ DO:**
1. **Use PCA(20)** - Optimal parameter efficiency
   - Captures 85-90% variance
   - Reduces overfitting dramatically
   - Parameters: 140 vs 1,519 (10× reduction)

2. **Per-voxel FIR** - Better than universal HRF
   - 100% vs 95-98% accuracy
   - Captures voxel-specific dynamics

3. **Best-k voxel selection** - Use top 200 by z-score
   - Pre-filters noise
   - Improves signal-to-noise ratio

4. **Correct Lab hue values** - CRITICAL
   - Use actual RGB→Lab conversion from pilot data
   - Wrong hues → reconstruction always fails

5. **Leave-one-run-out CV** - Standard validation
   - 6 runs total, train on 5, test on 1

**❌ DON'T:**
1. **No PCA** → 54% accuracy (overfitting)
2. **Universal HRF** → Slight accuracy drop (95-98%)
3. **Hard feature selection (SelectKBest)** → Worse than PCA
4. **Too many PCA components** → Includes noise (>50)
5. **Too few PCA components** → Loses information (<10)

#### From METHOD_EVOLUTION.md

**Key Insights:**
1. **PCA is not just dimensionality reduction** - it's also denoising
2. **Sweet spot: PCA(20)** - Too few loses info, too many adds noise
3. **Parameter efficiency > Model complexity** - Simple model + PCA > Complex model alone
4. **B&H 2009 has room for improvement** - Per-voxel FIR beats universal HRF

---

## 🛠️ File Checklist

### Core Analysis Files (Upload to Server)
- [x] `fir_reconstruction.py` - Main production pipeline
- [x] `fir_reconstruction_universal_hrf.py` - Alternative quick fix method
- [x] `config.py` - Configuration settings
- [x] `roi_build.py` - ROI construction utilities
- [x] `combine_atlas.py` - Atlas combination

### SLURM Scripts
- [x] `run_fir_reconstruction_single.sbatch` - Single ROI test
- [x] `run_fir_reconstruction_parallel.sbatch` - All ROIs parallel

### Configuration Files
- [x] `CLAUDE.md` - Project instructions
- [x] `config.py` - Subject IDs, paths, parameters

---

## 📝 Configuration Updates Needed

### In `config.py`:

```python
# Subject naming (CRITICAL - don't confuse!)
PILOT_SUB_ID = "P01"  # Pilot subject
TEST_SUB_IDS = ["01", "02", "03", "04"]  # Test subjects

# Color mappings
LABEL2HUE_DEG_PILOT = {
    'color_1': 182.14,  # CORRECT values from actual Lab conversion
    'color_2': 287.98,
    'color_3': 305.23,
    'color_4': 330.20,
    'color_5': 35.27,
    'color_6': 73.37,
    'color_7': 125.59,
    'color_8': 143.91,
}

LABEL2HUE_DEG_TEST = {
    # Regular 45° spacing for test subjects
    'color_1': 0,
    'color_2': 45,
    'color_3': 90,
    'color_4': 135,
    'color_5': 180,
    'color_6': 225,
    'color_7': 270,
    'color_8': 315,
}

# Optimal parameters (from FIR_MODIFICATIONS_SUMMARY.md)
USE_PCA = True
N_PCA_COMPONENTS = 20  # OPTIMAL sweet spot
BEST_K_VOXELS = 200    # For ROI analysis
RIDGE_ALPHA = 1.0      # For forward model

# Paths
FMRIPREP_DIR = "/storage/connectome/haba6030/fmriprep_out"
EVENT_DIR = "/storage/connectome/haba6030/colorBlind_dataOct"
DERIV_DIR = "/scratch/connectome/haba6030/colorBlind/derivatives"
ATLAS_DIR = "/scratch/connectome/haba6030/colorBlind/ProbAtlas_v4"
```

---

## 🚦 Execution Timeline

### Week 1: Setup & Preprocessing
**Day 1-2:**
- ✅ Verify directory structure
- ✅ Check pilot preprocessing quality
- ✅ Identify which test subjects need fMRIPrep

**Day 3-5:**
- 🔄 Run fMRIPrep for test subjects (if needed)
- 🔄 Build ROI masks from Wang atlas
- 🔄 Verify ROI overlays with functional data

### Week 2: Analysis Pipeline
**Day 1:**
- 🔄 Test fir_reconstruction.py on pilot V2 (single ROI)
- 🔄 Validate ~100% classification achieved

**Day 2-3:**
- 🔄 Run all ROIs in parallel for pilot
- 🔄 Generate QC visualizations
- 🔄 Compare with previous results (logs/final*)

**Day 4-5:**
- 🔄 Document any differences from previous results
- 🔄 Troubleshoot any issues
- 🔄 Prepare for test subjects

### Week 3: Test Subjects (if preprocessing ready)
- 🔄 Run pipeline on test subjects (sub-01 to sub-04)
- 🔄 Compare test subject regular spacing vs pilot irregular spacing
- 🔄 Validate forward model consistency across subjects

---

## 🔍 Troubleshooting Guide

### Common Issues & Solutions

**Issue 1: ROI has too few voxels**
```
Error: V4 ROI only has 15 voxels
```
**Solution:**
- Check Wang atlas threshold (try 20% instead of 25%)
- Verify atlas is correctly aligned to MNI space
- Consider using functional localizer instead

**Issue 2: Classification below 100%**
```
V2 classification: 65%
```
**Solution:**
- Ensure PCA is enabled: `USE_PCA=1, N_COMPONENTS=20`
- Check if correct Lab hues are used (LABEL2HUE_DEG_PILOT)
- Verify voxel selection is working (should have ~200 voxels)

**Issue 3: Reconstruction error too high**
```
V2 reconstruction: 75° error
```
**Solution:**
- Check forward model regularization (RIDGE_ALPHA)
- Verify channel definitions are correct (6 channels, 60° spacing)
- Ensure hue values match actual pilot data

**Issue 4: Memory errors**
```
SLURM: Out of memory
```
**Solution:**
```bash
# Increase memory in sbatch
#SBATCH --mem=64G  # Default was 32G
```

---

## 📚 Reference Documents

**Must-read before starting:**
1. `FIR_MODIFICATIONS_SUMMARY.md` - Complete history of modifications
2. `MEETING_NOTE_251106.md` - Meeting notes with key decisions
3. `FIR_RECONSTRUCTION_GUIDE.md` - User guide for pipeline
4. `METHOD_EVOLUTION.md` - Why methods changed
5. `PAPER_COMPARISON.md` - How results compare to B&H 2009

**SLURM job management:**
```bash
# Submit job
sbatch script.sbatch

# Check status
squeue -u haba6030

# Cancel job
scancel <job_id>

# View output
tail -f logs/fir_recon_*.out

# Check completed jobs
sacct -u haba6030 --format=JobID,JobName,State,Elapsed
```

---

## ✅ Success Criteria

### Minimum Goals:
- [ ] ROI masks created for all visual areas (V1-V4, hV4)
- [ ] Pilot subject achieves ~100% classification on V2
- [ ] Pilot subject achieves <30° reconstruction error on V2
- [ ] Results match previous logs/final* performance

### Optimal Goals:
- [ ] All ROIs (V1, V2, V3, hV4) achieve ~100% classification
- [ ] All ROIs achieve <35° reconstruction error
- [ ] Pipeline runs successfully on test subjects
- [ ] QC visualizations generated and validated

### Stretch Goals:
- [ ] Compare PCA vs no-PCA performance
- [ ] Test different PCA component numbers (10, 20, 30)
- [ ] Implement leave-one-color-out validation
- [ ] Compare universal HRF vs per-voxel FIR methods

---

## 🎯 Next Phase: CVD Filter Design

**Only after baseline established:**
1. Validate f_NC consistency across NC subjects
2. Collect CVD subject data
3. Train W_CVD for CVD forward model
4. Optimize g filter using composite loss
5. Test perceptual equivalence

**Prerequisites:**
- ✅ Significant reconstruction (p<0.05) on all ROIs
- ✅ Multiple NC subjects with similar f
- ⏸️ CVD subject data collected

---

## 💾 Backup Strategy

**To avoid losing work again:**

```bash
# Regular backups to OneDrive
rsync -avz haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/ \
    /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/derivatives_backup/

# Git commits for code changes
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis
git add fir_reconstruction.py config.py *.sbatch
git commit -m "Working pipeline - $(date +%Y-%m-%d)"
git push

# Weekly full backup
tar -czf colorBlind_backup_$(date +%Y%m%d).tar.gz derivatives/
```

---

## 📞 When to Ask for Help

**Immediate help needed if:**
- ❌ ROI masks are empty or misaligned
- ❌ Classification accuracy < 30% (worse than naive baseline)
- ❌ Reconstruction error > 90° (chance level)
- ❌ Memory/compute errors persist after fixes

**Discussion needed if:**
- ⚠️ Classification 60-80% (good but not 100%)
- ⚠️ Reconstruction 30-50° (above chance but not as good as before)
- ⚠️ Results differ significantly from previous logs/final*

---

**Prepared by:** Claude Code
**Date:** 2025-11-09
**Status:** Ready to execute
**First Action:** Verify directory structure and data availability on server

**다시 화이팅! 이번엔 체계적으로 백업하면서 진행해요! 💪**
