# How to Test Different ROIs with naive_analysis.py

## What Changed

I've updated `naive_analysis.py` to make it easy to switch between ROIs:

1. **Added clear ROI selection** at the top (line 71-87)
2. **Added derivatives/sub-01/roi to search path** (where Wang atlas ROIs are)
3. **Improved ROI name extraction** (e.g., "V1" from "sub-01_..._desc-V1_mask.nii.gz")

## Quick Start: Test V2 ROI (Best Overlap at 58.7%)

### Step 1: Edit naive_analysis.py

Open `naive_analysis.py` and change line 87:

```python
# FROM:
ROI_SELECTION = ["brain"]  # <-- CHANGE THIS LINE TO TEST DIFFERENT ROIs

# TO:
ROI_SELECTION = ["V2"]  # <-- CHANGE THIS LINE TO TEST DIFFERENT ROIs
```

### Step 2: Upload to Server

```bash
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis
scp naive_analysis.py node2:/scratch/connectome/haba6030/colorBlind/
```

### Step 3: Delete Cache and Run

```bash
ssh node2
cd /scratch/connectome/haba6030/colorBlind

# Create cache directory
mkdir -p hrf_test_outputs/cache_V2

# Delete any old V2 cache
rm -f hrf_test_outputs/cache_V2/*

# Run analysis
sbatch sbatch_naive.sub
```

### Step 4: Monitor Progress

```bash
# Watch the log
tail -f logs/naive_*.out

# Look for these key lines:
# [INFO] Available ROI masks:
#   - brain: ...
#   - V1: derivatives/sub-01/roi/...
#   - V2: derivatives/sub-01/roi/...  <-- Should appear!
#   ...
# [INFO] Loading ROI mask: ...desc-V2_mask.nii.gz
# [Forward-Recon][V2] Run 1: hit=?, p=?, ...
# [Forward-Recon][V2] MEAN hit=?, MEAN p=?
```

### Step 5: Check Results

```bash
# After completion, check the results
python test_roi_reconstruction.py

# Or just look at the CSV:
cat hrf_test_outputs/cache_V2/reconstruction_results.csv
```

---

## Test All ROIs

### Test V1:
```python
ROI_SELECTION = ["V1"]
```
- 511 voxels total
- 190 usable (37% overlap)
- Expected: ~30-35% hit rate

### Test V2: (RECOMMENDED - Best overlap!)
```python
ROI_SELECTION = ["V2"]
```
- 310 voxels total
- 182 usable (58% overlap)
- Expected: ~35-40% hit rate

### Test V3:
```python
ROI_SELECTION = ["V3"]
```
- 89 voxels total
- 62 usable (70% overlap)
- Expected: ~25-30% hit rate (fewer voxels)

### Test hV4:
```python
ROI_SELECTION = ["hV4"]
```
- 55 voxels total
- 38 usable (69% overlap)
- Expected: ~20-25% hit rate (very few voxels)

### Test Combined Early Visual Cortex:
```python
ROI_SELECTION = ["V1", "V2", "V3", "hV4"]
```
- Combined voxels from all areas
- More signal but also more variability
- Expected: ~35-45% hit rate

---

## Troubleshooting

### Error: "ROI mask 'V2' not found"

**Check if ROIs exist:**
```bash
ssh node2
cd /scratch/connectome/haba6030/colorBlind
ls -lh derivatives/sub-01/roi/
```

**If directory doesn't exist, create ROIs:**
```bash
# Check if roi_build.py exists
ls -l roi_build.py

# If it exists, run it:
python roi_build.py

# This should create V1, V2, V3, hV4 masks in derivatives/sub-01/roi/
```

**If roi_build.py doesn't exist:**
```bash
# Check config.py for Wang atlas path
grep -i "wang\|atlas" config.py

# Make sure ProbAtlas_v4 directory exists
ls -lh ProbAtlas_v4/
```

### Error: "No module named 'nilearn.maskers'"

```bash
# Activate correct environment
conda activate nilearn

# Or check Python version
which python
python -c "import nilearn; print(nilearn.__version__)"
```

### ROI shows 0 voxels or very few voxels

Check the ROI mask quality:
```bash
# Use nilearn or FSLeyes to inspect the mask
python -c "
from nilearn import image
img = image.load_img('derivatives/sub-01/roi/..._V2_mask.nii.gz')
print(f'Non-zero voxels: {(img.get_fdata() > 0).sum()}')
"
```

---

## Expected Results by ROI

| ROI | Voxels | Overlap | Current (brain) | Expected |
|-----|--------|---------|-----------------|----------|
| brain | 230,768 | 42% | 22.9%, p=0.401 ❌ | Baseline |
| V1 | 511 | 37% | Not tested | 30-35% |
| **V2** | **310** | **58%** | **Not tested** | **35-40%** ⭐ |
| V3 | 89 | 70% | Not tested | 25-30% |
| hV4 | 55 | 69% | Not tested | 20-25% |
| V1-V4 | ~965 | ~50% | Not tested | 35-45% |

**Goal:** Hit rate >30%, p-value <0.05

---

## What to Do After Testing

### If V2 reaches p<0.05: ✅ SUCCESS!
```
→ Use V2 ROI for all future analyses
→ Move to Step 2: CVD correction filter design
→ Document in paper: "V2 showed significant reconstruction (hit=X%, p<0.05)"
```

### If V2 improves but doesn't reach p<0.05: ⚠️ PARTIAL SUCCESS
```
→ Try Priority 2: FIR model (bh_anal.py)
→ Try Priority 3: Optimize lambda
→ Combine improvements
```

### If no ROI reaches p<0.05: ❌ NEED ALTERNATIVE APPROACH
```
→ Try FIR model (bh_anal.py) - addresses negative R² issue
→ Switch to main experiment data (uniform color spacing)
→ Consider data quality issues (motion, attention)
```

---

## Quick Reference: What Line to Change

**Location:** `naive_analysis.py`, line 87

**Options:**
```python
ROI_SELECTION = ["brain"]                    # Baseline (22.9%, p=0.401)
ROI_SELECTION = ["V1"]                       # Test V1
ROI_SELECTION = ["V2"]                       # Test V2 (RECOMMENDED)
ROI_SELECTION = ["V3"]                       # Test V3
ROI_SELECTION = ["hV4"]                      # Test hV4
ROI_SELECTION = ["V1", "V2", "V3", "hV4"]   # Combined
```

**That's it! Just change one line, upload, and run.**

---

## Timeline

- Edit + upload: 2 minutes
- Delete cache: 1 minute
- Run analysis: 10-15 minutes per ROI
- Check results: 2 minutes

**Total per ROI: ~15-20 minutes**

**Test all 4 ROIs (V1, V2, V3, hV4): ~1.5 hours**

---

## After Testing

Use `test_roi_reconstruction.py` to see all results in one table:

```bash
python test_roi_reconstruction.py > roi_comparison_results.txt
cat roi_comparison_results.txt
```

This will show:
```
SUMMARY: Reconstruction Performance by ROI
ROI      Hit Rate  p-value  Significant  Status
brain    0.229     0.401    No           ❌
V1       0.312     0.123    No           ⚠️
V2       0.375     0.042    Yes          ✅  <-- Success!
V3       0.265     0.234    No           ❌
hV4      0.198     0.456    No           ❌
```

**Start with V2 - it has the best overlap and highest chance of success!** 🎯
