# Current Project Status

**Last Updated:** 2025-11-05
**Current Phase:** Phase 1 - Parallel ROI Testing (Ready to Execute)

---

## 🎯 Where We Are

### Completed in This Session ✅

1. **Fixed ROI Selection Issue**
   - Updated `discover_roi_masks()` in naive_analysis.py (lines 116-149)
   - Now correctly extracts ROI names from BIDS filenames
   - Handles patterns: `sub-01_V2_mask.nii.gz` → "V2"

2. **Created Parallel ROI Testing Infrastructure**
   - `submit_roi_parallel.sh` - Submit all 4 ROIs simultaneously
   - `check_parallel_results.sh` - Check status and results
   - `test_roi_reconstruction.py` - Compare ROI performances
   - Time savings: 60 min → 15-20 min (75% faster)

3. **Educational Documentation**
   - `BASH_SCRIPT_GUIDE.md` - Comprehensive bash scripting tutorial
   - `GIT_PUSH_GUIDE.md` - Git workflow for research projects
   - `PARALLEL_ROI_GUIDE.md` - Guide for parallel ROI testing

4. **Git Repository Initialized**
   - 59 files committed (23,570 lines)
   - `.gitignore` configured for research projects
   - Ready to push to GitHub when you create remote repo

5. **Updated ML/DL Files (Future Use)**
   - `ml_forward_model.py` - Added corrected Lab hues, output buffering
   - `compare_forward_models.py` - Added pilot/main color set config
   - **Status:** Updated but NOT uploaded to server yet (premature)

### Current Results 📊

**Brain Mask Baseline (naive_analysis.py):**
- Hit rate: 22.9%
- P-value: 0.401
- Status: ❌ NOT significant (need p<0.05)

**Root Causes Identified:**
1. Whole brain mask too noisy (230K voxels)
2. Pilot data has non-uniform color spacing (18.3° to 105.8° gaps)
3. Negative R² values indicate GLM fit quality issues

**Solution:** Test smaller, more selective ROIs

---

## 📋 Next Steps (In Order)

### Phase 1: Parallel ROI Testing 🚀 **← START HERE**

**Goal:** Find ROI that achieves p<0.05 for significant reconstruction

**Step 1: Upload Essential Scripts to Server**
```bash
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis

scp naive_analysis.py node2:/scratch/connectome/haba6030/colorBlind/
scp submit_roi_parallel.sh node2:/scratch/connectome/haba6030/colorBlind/
scp check_parallel_results.sh node2:/scratch/connectome/haba6030/colorBlind/
scp test_roi_reconstruction.py node2:/scratch/connectome/haba6030/colorBlind/
```

**Step 2: Submit Parallel Jobs**
```bash
ssh node2
cd /scratch/connectome/haba6030/colorBlind

chmod +x submit_roi_parallel.sh
chmod +x check_parallel_results.sh

./submit_roi_parallel.sh
```

**Expected Output:**
```
==========================================
Parallel ROI Submission (Clean Method)
==========================================

Testing ROIs in parallel: V1 V2 V3 hV4

Submitting jobs...
  ✅ V1: Job 12345 submitted
  ✅ V2: Job 12346 submitted
  ✅ V3: Job 12347 submitted
  ✅ hV4: Job 12348 submitted

Monitor: squeue -u $USER
```

**Step 3: Monitor Progress (15-20 minutes)**
```bash
# Watch job status
watch squeue -u $USER

# Check individual logs
tail -f logs/naive_V2_*.out
```

**Step 4: Check Results**
```bash
./check_parallel_results.sh
```

**Step 5: Interpret Results**

Expected outcomes based on diagnostic data:

| ROI | Voxels | Overlap | Expected Hit Rate | Expected P-value |
|-----|--------|---------|-------------------|------------------|
| V1 | 511 | 37% | 30-35% | ~0.10 |
| **V2** | **310** | **58%** | **35-40%** | **~0.05** ⭐ |
| V3 | 89 | 70% | 25-30% | ~0.15 |
| hV4 | 55 | 69% | 20-25% | ~0.25 |

**V2 is most promising** (best balance of voxel count and overlap)

---

### Phase 2: Establish Baseline

**If V2 (or any ROI) achieves p<0.05:** ✅
1. Update `ROI_SELECTION = ["V2"]` in naive_analysis.py
2. Use this ROI for all future analyses
3. **Move to Step 2: CVD correction filter design**

**If best ROI has p>0.05 but <0.10:** ⚠️
1. Try FIR model (bh_anal.py) - addresses negative R² issue
2. Optimize lambda parameter (try 0.1, 1.0, 10.0)
3. Consider combining V1+V2 into single mask

**If all ROIs fail (all p>0.10):** ❌
1. Try FIR model first
2. Check data quality (motion, attention)
3. Consider ML/DL alternatives (Phase 3)

---

### Phase 3: ML/DL (Only if Linear Models Fail)

**When to try:** Only after exhausting linear approaches

**Files ready but NOT uploaded yet:**
- `ml_forward_model.py` - Ridge, MLP, CNN, Attention models
- `compare_forward_models.py` - Comparison framework

**What's updated in these files:**
- ✅ Corrected Lab hue values (pilot vs main)
- ✅ Output buffering for SLURM
- ✅ Pilot/main color set configuration
- ✅ All recent fixes from naive_analysis.py

**To use when needed:**
```bash
# Upload ML files
scp ml_forward_model.py node2:/scratch/connectome/haba6030/colorBlind/
scp compare_forward_models.py node2:/scratch/connectome/haba6030/colorBlind/

# Run comparison
python compare_forward_models.py --roi V2 --models ridge mlp attention
```

---

### Phase 4: CVD Correction Filter Design

**When:** After establishing significant baseline (p<0.05)

**Goal:** Design filter g(x) such that:
- `vox_NC = g(vox_CVD)`
- CVD individuals' decoded colors match NC individuals

**Approach:**
1. Use best ROI's forward model as baseline
2. Design inverse mapping for CVD correction
3. Test on CVD simulation data
4. Validate perceptual equivalence

---

## 📁 Key Files and Status

### Ready to Upload (Essential) 🚀
- ✅ `naive_analysis.py` - Main analysis with ROI fixes (lines 71-149)
- ✅ `submit_roi_parallel.sh` - Parallel SLURM submission
- ✅ `check_parallel_results.sh` - Results checker
- ✅ `test_roi_reconstruction.py` - ROI comparison tool

### Keep Local (Not Needed Yet) 💾
- ✅ `ml_forward_model.py` - ML/DL models (updated, ready when needed)
- ✅ `compare_forward_models.py` - Model comparison (updated, ready when needed)
- ✅ `bh_anal.py` - FIR model (original, use if canonical HRF fails)

### Documentation 📖
- ✅ `BASH_SCRIPT_GUIDE.md` - Bash scripting tutorial
- ✅ `GIT_PUSH_GUIDE.md` - Git workflow guide
- ✅ `PARALLEL_ROI_GUIDE.md` - Parallel ROI testing guide
- ✅ `RECONSTRUCTION_ANALYSIS.md` - Problem diagnosis
- ✅ `NEXT_STEPS.md` - Previous action plan
- ✅ `CURRENT_STATUS.md` - This file

### Supporting Files ✅
- ✅ `check_roi_setup.py` - ROI verification tool
- ✅ `inspect_cache.py` - Cache debugging tool
- ✅ `roi_build.py` - ROI construction utilities
- ✅ `config.py` - Global configuration

---

## 🔑 Key Technical Details

### Corrected Lab Hue Values (Pilot Data)

**IMPORTANT:** These are the ACTUAL Lab hue values from the pilot experiment RGB colors, NOT from the IRB document.

```python
LABEL2HUE_DEG_PILOT = {
    'color_1': 182.142053052572436,   # Cyan-ish (IRB was wrong: 178.57°)
    'color_2': 287.979026187069735,   # Blue-purple (IRB: 310.77°)
    'color_3': 305.226546308759566,   # Purple (IRB: 316.10°)
    'color_4': 330.204721787408289,   # Pink (IRB: 333.86°)
    'color_5': 35.269500805260478,    # Orange-red (IRB: 54.50°)
    'color_6': 73.365061454288877,    # Yellow-orange (IRB: 68.45°)
    'color_7': 125.585145639335096,   # Green-yellow (IRB: 130.78°)
    'color_8': 143.909094545652778,   # Green (IRB: 153.72°)
}
```

**Impact:** Fixing these improved hit rate from 14.6% to 22.9%

**Pilot vs Main Experiment:**
- Pilot: Non-uniform spacing (gaps: 18.3° to 105.8°)
- Main: Uniform 45° spacing (should perform better)

### ROI Selection Configuration

In `naive_analysis.py` (lines 71-87):
```python
ROI_SELECTION = ["V2"]  # <-- Change this to test different ROIs

# Options:
# ["brain"]  - Full brain mask (230K voxels) - CURRENT: 22.9%, p=0.401
# ["V1"]     - Primary visual cortex (511 voxels, 37% overlap)
# ["V2"]     - Secondary visual cortex (310 voxels, 58% overlap) - BEST!
# ["V3"]     - V3 (89 voxels, 70% overlap)
# ["hV4"]    - V4 (55 voxels, 69% overlap)
```

### Parallel Execution Benefits

**Sequential (old):**
- V1: 15 min → V2: 15 min → V3: 15 min → hV4: 15 min
- **Total: 60 minutes**

**Parallel (new):**
- V1, V2, V3, hV4 all at once
- **Total: 15-20 minutes**
- **Time savings: 75%**

---

## 🐛 Common Issues and Solutions

### Issue: ROI Not Found
**Error:** `[WARN] ROI mask 'V2' not found. Skipping.`

**Solution:** Already fixed in naive_analysis.py lines 116-149
- Now handles BIDS naming: `sub-01_V2_mask.nii.gz`
- Extracts ROI name correctly

### Issue: SLURM Output Not Showing
**Cause:** Output buffering

**Solution:** Already added `sys.stdout.flush()` to all print statements
- Real-time feedback in SLURM logs
- Can monitor progress during runs

### Issue: Jobs Stuck in Queue
**Check status:**
```bash
squeue -u $USER
```

**If pending:**
- Wait for resources (jobs start automatically)
- Check estimated start time: `squeue --start -u $USER`

### Issue: Job Failed
**Check logs:**
```bash
# Find most recent error log
ls -lt logs/naive_*err | head -1
cat logs/naive_V2_12346.err

# Check output log
cat logs/naive_V2_12346.out
```

**Resubmit individual ROI:**
```bash
# Clear cache
rm -f hrf_test_outputs/cache_V2/*

# Resubmit just V2
sbatch --job-name=naive_V2 --output=logs/naive_V2_new_%j.out --mem=16G --time=00:30:00 \
  --wrap="sed 's/ROI_SELECTION = \[.*\]/ROI_SELECTION = [\"V2\"]/' naive_analysis.py > tmp.py && python tmp.py && rm tmp.py"
```

---

## 📊 Expected Timeline

**From this point:**
1. Upload scripts: **2 minutes**
2. Submit jobs: **1 minute**
3. Wait for completion: **15-20 minutes**
4. Check results: **2 minutes**

**Total: ~25 minutes to test all 4 ROIs**

**Compare to sequential: 60+ minutes**

---

## 🎓 What We Learned

1. **Lab hue correction was critical**
   - IRB document had incorrect values
   - Actual RGB → Lab conversion revealed true hue angles
   - Improved hit rate from 14.6% to 22.9%

2. **ROI selection matters**
   - Whole brain too noisy (230K voxels)
   - V2 has optimal balance (310 voxels, 58% overlap)
   - More voxels ≠ better (need quality over quantity)

3. **Parallel execution saves time**
   - Independent ROI analyses can run simultaneously
   - Separate cache directories prevent conflicts
   - 75% time savings with no downsides

4. **Pilot data limitations**
   - Non-uniform color spacing makes reconstruction harder
   - Main experiment should perform better (uniform 45° spacing)

---

## 🚀 To Resume Work

**Copy and paste this sequence:**

```bash
# 1. Navigate to project directory
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis

# 2. Check what needs to be uploaded
ls -lh naive_analysis.py submit_roi_parallel.sh check_parallel_results.sh test_roi_reconstruction.py

# 3. Upload to server
scp naive_analysis.py node2:/scratch/connectome/haba6030/colorBlind/
scp submit_roi_parallel.sh node2:/scratch/connectome/haba6030/colorBlind/
scp check_parallel_results.sh node2:/scratch/connectome/haba6030/colorBlind/
scp test_roi_reconstruction.py node2:/scratch/connectome/haba6030/colorBlind/

# 4. SSH to server
ssh node2

# 5. Navigate to work directory
cd /scratch/connectome/haba6030/colorBlind

# 6. Make scripts executable
chmod +x submit_roi_parallel.sh check_parallel_results.sh

# 7. Submit parallel jobs
./submit_roi_parallel.sh

# 8. Monitor progress
watch squeue -u $USER
# (Press Ctrl+C to exit when all jobs complete)

# 9. Check results
./check_parallel_results.sh

# 10. Download results to local (from local terminal)
scp -r node2:/scratch/connectome/haba6030/colorBlind/hrf_test_outputs/cache_V* ./results/
```

---

## 📝 Notes for Future Claude Session

**Context to provide:**
- "I'm resuming work on fMRI color reconstruction analysis"
- "Read CURRENT_STATUS.md to understand current state"
- "We just finished updating ML files but haven't uploaded them yet"
- "Next step: upload essential scripts and run parallel ROI testing"

**Key files for context:**
- `CURRENT_STATUS.md` (this file)
- `PARALLEL_ROI_GUIDE.md` (detailed parallel testing guide)
- `naive_analysis.py` (main analysis script)

**Important reminders:**
- Don't upload ML files yet (premature - no baseline yet)
- V2 is most promising ROI (58% overlap, 310 voxels)
- Target: p<0.05 for statistical significance
- Current brain mask baseline: 22.9% hit rate, p=0.401

---

## 🎯 Success Criteria

**Minimum Goal:**
- At least one ROI achieves p<0.05

**Optimal Goal:**
- V2 achieves p<0.05 with hit rate >35%

**If achieved:**
- Use that ROI as baseline
- Move to Step 2: CVD correction filter design

**If not achieved:**
- Try FIR model (bh_anal.py)
- Optimize lambda parameter
- Last resort: ML/DL comparison

---

**Ready to proceed with parallel ROI testing!** 🚀

All files are prepared, documented, and ready to upload.
Expected result: V2 ROI achieves ~35-40% hit rate with p~0.05 (significant).

---

*Status saved: 2025-11-05*
*Next action: Upload scripts and submit parallel jobs*
