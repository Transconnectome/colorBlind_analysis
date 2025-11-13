# 📍 Current Context Summary - November 9, 2025

**Purpose:** Quick resume point for color reconstruction analysis project
**Last Updated:** 2025-11-09
**Status:** Ready to execute ROI construction and analysis

---

## 🎯 Project Overview

**Goal:** Design CVD correction filter using fMRI-based color reconstruction
- **Phase 1 (Current):** Establish forward encoding model for NC subjects
- **Phase 2 (Future):** Design g(color) filter for CVD correction

**Method:** Brouwer & Heeger (2009) forward encoding model with modifications
- Per-voxel FIR instead of universal HRF
- PCA(20) for dimensionality reduction → **KEY to success!**
- Wang (2015) atlas for ROI definition

---

## ✅ What Was Achieved (Before Nov 7th)

### Successful Results (in logs/final* directory - now lost)

**V2 ROI Performance:**
- ✅ Classification: **~100%** accuracy (vs 12.5% chance)
- ✅ Reconstruction: **<30°** error (vs 90° chance)
- ✅ Statistical significance: **p < 0.001**
- ✅ Voxel count: **~310** voxels (optimal range: 280-350)

**Key Success Factors:**
1. **PCA(20 components)** - Reduced parameters from ~1,519 → ~140
   - Without PCA: 54% accuracy (overfitting)
   - With PCA(20): 100% accuracy ✅
2. **Per-voxel FIR** - Better than universal HRF (100% vs 95-98%)
3. **Correct Lab hue values** - From actual pilot RGB→Lab conversion
4. **Best-k voxel selection (200)** - Pre-filtering noise

**All ROIs Performance:**
| ROI | Voxels | Classification | Reconstruction |
|-----|--------|---------------|----------------|
| V2 | 310 | 100% | <20° |
| V1 | 220 | 100% | <25° |
| V3 | 200 | 100% | <30° |
| hV4 | 120 | 100% | <35° |

---

## 📂 Current Situation (Nov 9th)

### What Happened:
- Directory reorganization (scratch↔storage, folder renaming)
- Lost file tracking → can't find original logs/final* results
- BUT: **All methods documented in MD files (pre-Nov 7th)**

### What We're Doing:
- ✅ **Restarting from scratch** with proven methodology
- ✅ **All documentation prepared** (RESTART_PLAN, ROI_CONSTRUCTION_GUIDE, etc.)
- ✅ **Memories saved** for key information
- 🔄 **Ready to execute** step-by-step workflow

---

## 🗂️ Key Files Status

### Analysis Scripts (Ready ✅)
- `fir_reconstruction.py` - **Main winner pipeline**
  - Per-voxel FIR + PCA(20) + correct Lab hues
  - Command: `python fir_reconstruction.py --roi V2 --use-pca --n-components 20`

- `fir_reconstruction_universal_hrf.py` - Alternative (quick fix method)
  - Universal HRF approach, slightly lower performance

- `roi_build.py` - **ROI construction from Wang atlas**
  - Combines ventral/dorsal, left/right
  - Resamples to res-2 BOLD space
  - Function: `build_wang_rois(cfg)`

- `config.py` - Configuration
  - SUB_ID, paths, TR, N_RUNS
  - **CRITICAL:** Contains correct Lab hue values for pilot

- `visualize_roi_overlay.py` - **NEW: QC visualization**
  - Overlay ROI on BOLD images
  - Verify spatial alignment

### Documentation (Complete ✅)
- `RESTART_PLAN.md` - Complete 5-phase restart plan
- `ROI_CONSTRUCTION_GUIDE.md` - Detailed ROI building guide
- `COMPLETE_WORKFLOW.md` - **Step-by-step executable workflow** ⭐
- `QUICK_SERVER_WORKFLOW.md` - Quick reference with commands
- `FIR_MODIFICATIONS_SUMMARY.md` - Pre-Nov 7 documentation of all changes
- `MEETING_NOTE_251106.md` - Meeting notes with key decisions
- `METHOD_EVOLUTION.md` - Why methods changed

### SLURM Scripts (Ready ✅)
- `run_fir_reconstruction_single.sbatch` - Single ROI test
- `run_fir_reconstruction_parallel.sbatch` - All ROIs parallel

---

## 🔑 Critical Parameters (DO NOT CHANGE!)

### From Previous Success:

```python
# PCA Settings (MOST CRITICAL!)
USE_PCA = True
N_PCA_COMPONENTS = 20  # Sweet spot: 85-90% variance, no overfitting

# Voxel Selection
BEST_K_VOXELS = 200  # Top 200 by z-score

# Wang Atlas
THRESHOLD = 50  # 50% probability threshold (can adjust if voxel count off)

# Forward Model
RIDGE_ALPHA = 1.0  # Ridge regression regularization

# Lab Hue Values (Pilot - MUST USE THESE!)
LABEL2HUE_DEG_PILOT = {
    'color_1': 182.14,  # NOT 0°!
    'color_2': 287.98,  # NOT 45°!
    'color_3': 305.23,
    'color_4': 330.20,
    'color_5': 35.27,
    'color_6': 73.37,
    'color_7': 125.59,
    'color_8': 143.91,
}
```

**Why PCA(20) is critical:**
- Parameters: 140 (vs 1,519 without PCA)
- Ratio: 3.5:1 samples:parameters (vs 38:1)
- Performance: 100% (vs 54%)
- Explained variance: ~85-90%

---

## 🛣️ ROI Construction Method

### Wang Atlas ROI Mapping:
```python
V1  = roi1 (V1v) + roi2 (V1d)  # Ventral + Dorsal
V2  = roi3 (V2v) + roi4 (V2d)
V3  = roi5 (V3v) + roi6 (V3d)
hV4 = roi7
```

### Process:
1. Load Wang atlas parts (lh + rh for each dorsal/ventral)
2. Apply threshold: `mask = atlas_data > 50`
3. Combine with logical OR: ventral OR dorsal, left OR right
4. **Resample to res-2 BOLD space** (critical!)
   - Reference: `config.get_func_img_path(1)` (run-1 BOLD)
   - Method: nearest neighbor interpolation
   - Result: 97×115×97 voxels, same grid as BOLD
5. Optional: Brain mask intersection (for EPI coverage)
6. Optional: Subject MNI ROI intersection (for accuracy)

### Expected Voxel Counts:
- V1: 190-250
- **V2: 280-350** (optimal, most important!)
- V3: 180-230
- hV4: 100-150

**If counts are off:**
- Too few (<50): Lower threshold (50 → 25%)
- Too many (>500): Raise threshold (50 → 75%)

---

## 📍 Server Paths

### Data Locations:
```bash
# Server
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind

# fMRIPrep output (res-2 BOLD)
/storage/connectome/haba6030/fmriprep_out/sub-P01/func/
  → sub-01_task-rsvp_run-{1-6}_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz

# Event files
/storage/connectome/haba6030/colorBlind_dataOct/sub-P01/func/
  → sub-P01_task-rsvp_run-{1-6}_events.tsv

# Wang atlas
/scratch/connectome/haba6030/colorBlind/ProbAtlas_v4/subj_vol_all/
  → perc_VTPM_vol_roi{1-7}_{lh,rh}.nii.gz

# Output directory
/scratch/connectome/haba6030/colorBlind/derivatives/sub-P01/
  ├── roi/                    # ROI masks
  ├── fir_reconstruction/     # Analysis results
  └── ...
```

---

## 🚀 Next Immediate Steps (In Order)

### Step 1: Upload Files (Local → Server)
```bash
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis

scp roi_build.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp visualize_roi_overlay.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp fir_reconstruction.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp config.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp run_fir_reconstruction_single.sbatch haba6030@node2:/scratch/connectome/haba6030/colorBlind/
```

### Step 2: Verify Data Exists (Server)
```bash
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind
conda activate nilearn

# Check Wang atlas (expect 28 files)
ls ProbAtlas_v4/subj_vol_all/perc_VTPM_vol_roi*.nii.gz | wc -l

# Check BOLD images (expect 6 runs)
ls /storage/connectome/haba6030/fmriprep_out/sub-P01/func/*res-2*preproc* | wc -l

# Check event files (expect 6 runs)
ls /storage/connectome/haba6030/colorBlind_dataOct/sub-P01/func/*events.tsv | wc -l
```

### Step 3: Build ROI Masks
```bash
python roi_build.py
# Expected output: derivatives/sub-P01/roi/sub-P01_{V1,V2,V3,hV4}_mask.nii.gz
```

### Step 4: Visualize & Validate ⭐ **CRITICAL QC STEP**
```bash
python visualize_roi_overlay.py
# Output: derivatives/sub-P01/roi/qc_figures/*.png

# Download images (from local terminal)
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/sub-P01/roi/qc_figures/ ./roi_qc_check/
```

**Check overlay images:**
- [ ] ROIs in occipital cortex (back of brain)
- [ ] Left/right symmetric
- [ ] Inside brain (not extending outside)
- [ ] Overlapping with BOLD activation

### Step 5: Test V2 ROI (Most Important!)
```bash
# Direct execution (for debugging)
python fir_reconstruction.py --roi V2 --use-pca --n-components 20

# OR SLURM job
sbatch --export=ROI=V2,USE_PCA=1,N_COMPONENTS=20 run_fir_reconstruction_single.sbatch
```

**Expected output:**
```
[INFO] Classification accuracy: 100.0%
[SUCCESS] Reconstruction error: 18.5°
[SUCCESS] p-value < 0.001
```

### Step 6: If V2 Succeeds → All ROIs
```bash
sbatch run_fir_reconstruction_parallel.sbatch
```

---

## ✅ Success Criteria

### Minimum (Must Achieve):
- [ ] V2 ROI has 280-350 voxels
- [ ] V2 classification ~100%
- [ ] V2 reconstruction <30°
- [ ] p < 0.05

### Optimal (Target):
- [ ] All ROIs >90% classification
- [ ] All ROIs <35° reconstruction
- [ ] ROI overlays visually perfect

---

## 🔍 How to Validate Results

### After V2 Test:
```bash
# Check summary
cat derivatives/sub-P01/fir_reconstruction/V2/summary.csv

# Expected:
# ROI,N_voxels,Use_PCA,N_components,Classification_accuracy,Reconstruction_error_deg
# V2,310,True,20,1.0,18.5

# Check log for errors
less derivatives/sub-P01/fir_reconstruction/V2/log.txt
```

### Success Indicators:
- ✅ Classification_accuracy = 1.0 (100%)
- ✅ Reconstruction_error < 30°
- ✅ No ERROR messages in log.txt
- ✅ Figures generated without issues

### Failure Indicators:
- ❌ Classification < 70% → Check ROI overlay, PCA settings
- ❌ Reconstruction > 50° → Check Lab hue values, voxel count
- ❌ Errors in log → Check file paths, data availability

---

## 📊 Comparison with Previous Results

### If You Achieve Similar Performance:
| Metric | Previous (logs/final*) | Current | Status |
|--------|----------------------|---------|--------|
| V2 Voxels | ~310 | ??? | TBD |
| V2 Classification | 100% | ??? | TBD |
| V2 Reconstruction | <20° | ??? | TBD |

### Why This Matters:
- ✅ Same performance → methodology validated
- ✅ Can proceed to test subjects with confidence
- ✅ Foundation for CVD filter design established

---

## 💡 Troubleshooting Quick Reference

### Issue: ROI has too few voxels (<50)
```python
# Edit roi_build.py line 110
part_mask = part_data > 25  # Lower threshold
```

### Issue: ROI extends outside brain
→ Ensure brain mask intersection is active (check overlay)

### Issue: Classification poor (<70%)
→ Check: (1) PCA enabled, (2) Correct Lab hues, (3) ROI location

### Issue: Can't find BOLD images
→ Check config.py paths, verify SUB_ID = 'P01' for pilot

---

## 📚 Documents to Reference

**For execution:**
1. **COMPLETE_WORKFLOW.md** ⭐ Primary guide
2. QUICK_SERVER_WORKFLOW.md - Command reference

**For understanding:**
3. FIR_MODIFICATIONS_SUMMARY.md - Why PCA(20) critical
4. ROI_CONSTRUCTION_GUIDE.md - ROI details
5. MEETING_NOTE_251106.md - Previous decisions

**For troubleshooting:**
6. RESTART_PLAN.md - Full phase plan
7. METHOD_EVOLUTION.md - Method history

---

## 🎯 Final Reminders

### DO:
- ✅ Use PCA(20) - absolutely critical!
- ✅ Check overlay images before proceeding
- ✅ Start with V2 (most reliable)
- ✅ Validate voxel counts
- ✅ Use correct Lab hue values from config.py

### DON'T:
- ❌ Skip PCA (will get 54% accuracy)
- ❌ Skip overlay visualization (blind analysis)
- ❌ Use wrong Lab hues (uniform 0°,45°,90°...)
- ❌ Modify proven parameters without reason
- ❌ Proceed if V2 test fails

---

## 📞 When to Ask for Help

**Immediate:**
- ROI completely misplaced (not in occipital cortex)
- Voxel count < 50
- Classification < 30%
- Any CRITICAL ERROR in logs

**Review:**
- Voxel count outside expected range
- Classification 60-80%
- Reconstruction 30-50°

---

**Status:** Ready to execute ✅
**Next Action:** Step 1 - Upload files to server
**Expected Time:** 30-45 minutes total
**Primary Guide:** COMPLETE_WORKFLOW.md

**마지막 확인:** 모든 준비 완료! COMPLETE_WORKFLOW.md 따라 단계별로 실행하세요! 💪

---

**Document Created:** 2025-11-09
**Resume Point:** ROI construction (Step 3 in COMPLETE_WORKFLOW.md)
**Previous Success:** Documented in FIR_MODIFICATIONS_SUMMARY.md (Nov 6th)
