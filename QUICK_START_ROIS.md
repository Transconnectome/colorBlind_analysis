# Quick Start: Test V1-V4 ROIs for Reconstruction

## Step 1: Upload Fixed Scripts to Server

```bash
# From your local machine:
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis

scp test_roi_reconstruction.py node2:/scratch/connectome/haba6030/colorBlind/
scp inspect_cache.py node2:/scratch/connectome/haba6030/colorBlind/
```

## Step 2: Run Inspection Script

```bash
ssh node2
cd /scratch/connectome/haba6030/colorBlind

# This will show what's in the current brain mask cache
python inspect_cache.py
```

**Expected output:**
```
Found: ./hrf_test_outputs/cache_brain/reconstruction_results.joblib
✅ Found 'all_hits' and 'all_ps' keys (standard structure)
   Number of runs: 6
   Per-run details:
     Run 1: hit_rate=0.125, p_value=0.615, threshold=0.375
     Run 2: hit_rate=0.250, p_value=0.327, threshold=0.375
     ...
   Mean hit rate: 0.229
   Mean p-value:  0.401
```

## Step 3: Test ROI Comparison

```bash
# This will check which ROIs exist and show their results
python test_roi_reconstruction.py
```

**Expected output:**
```
Checking ROI availability...
  ✅ V1: derivatives/sub-01/roi/...
  ✅ V2: derivatives/sub-01/roi/...
  ...
  ❌ brain: (results for brain mask already computed)

SUMMARY: Reconstruction Performance by ROI
ROI      Hit Rate  p-value  Significant  Status
brain    0.229     0.401    No           ❌
V1       N/A       N/A      N/A          ⏳  (need to run)
V2       N/A       N/A      N/A          ⏳  (need to run)
...
```

## Step 4: Check if ROIs Exist

```bash
# Check if ROI masks have been created
ls -lh derivatives/sub-01/roi/
```

**If ROIs don't exist:**
```bash
# Create them using roi_build.py
python roi_build.py
```

**If roi_build.py doesn't exist, check config:**
```bash
# Look in your project for ROI generation scripts
ls -l *.py | grep roi
```

## Step 5: Run Analysis with V2 ROI (Best Overlap)

V2 has the best overlap (58.7%) according to diagnostic results.

**Method A: Modify naive_analysis.py directly**

Edit `naive_analysis.py` around line 950:

```python
# Change from:
roi_paths = {
    'brain': 'output/pilot/sub-01/anat/sub-01_acq-mprage_space-MNI152NLin2009cAsym_res-2_desc-brain_mask.nii.gz',
}

# To:
roi_paths = {
    'V2': 'derivatives/sub-01/roi/sub-01_acq-mprage_space-MNI152NLin2009cAsym_res-2_desc-V2_mask.nii.gz',
}
```

**Method B: Create a new script variant**

```bash
# Make a copy for testing
cp naive_analysis.py naive_analysis_v2.py

# Edit naive_analysis_v2.py to use V2 ROI
# ... (same change as Method A)
```

## Step 6: Delete Cache and Run

```bash
# Make sure cache directory exists
mkdir -p hrf_test_outputs/cache_V2

# Delete any old V2 cache (if exists)
rm -f hrf_test_outputs/cache_V2/*.joblib
rm -f hrf_test_outputs/cache_V2/*.csv

# Run analysis
sbatch sbatch_naive.sub

# Or if using the variant:
# sbatch sbatch_naive_v2.sub
```

## Step 7: Monitor Progress

```bash
# Watch log file in real-time
tail -f logs/naive_*.out

# Look for these key lines:
# [INFO] Running ROI-dependent analyses for 'V2' mask
# [Forward-Recon][V2] Run 1: hit=?, p=?, ...
# [Forward-Recon][V2] MEAN hit=?, MEAN p=?
```

## Step 8: Check Results

```bash
# After analysis completes, run comparison again
python test_roi_reconstruction.py
```

**Expected output:**
```
SUMMARY: Reconstruction Performance by ROI
ROI      Hit Rate  p-value  Significant  Status
brain    0.229     0.401    No           ❌
V2       0.350     0.085    No           ⚠️  (better but still not significant)
```

## Step 9: Test Other ROIs

If V2 doesn't reach significance (p<0.05), try:

**Test V1:**
```bash
# Edit naive_analysis.py to use V1
# Delete cache: rm -f hrf_test_outputs/cache_V1/*
# Run: sbatch sbatch_naive.sub
```

**Test V3:**
```bash
# Edit naive_analysis.py to use V3
# Delete cache: rm -f hrf_test_outputs/cache_V3/*
# Run: sbatch sbatch_naive.sub
```

**Test hV4:**
```bash
# Edit naive_analysis.py to use hV4
# Delete cache: rm -f hrf_test_outputs/cache_hV4/*
# Run: sbatch sbatch_naive.sub
```

## Step 10: Compare All Results

After testing multiple ROIs:

```bash
python test_roi_reconstruction.py > roi_comparison.txt
cat roi_comparison.txt
```

This will show a nice table comparing all ROIs tested.

---

## Troubleshooting

### Error: "ROI masks not found"

**Solution:**
```bash
# Create ROIs using roi_build.py
python roi_build.py

# Or check the Wang atlas path in config
grep "ProbAtlas" config.py
```

### Error: "Module not found"

**Solution:**
```bash
# Activate the correct conda environment
conda activate nilearn

# Or check which Python you're using
which python
python --version
```

### ROI has too few voxels

From diagnostic results:
- V1: 511 voxels (190 usable)
- V2: 310 voxels (182 usable) ← Best!
- V3: 89 voxels (62 usable) ← Small
- hV4: 55 voxels (38 usable) ← Very small

**If V2 doesn't work, try combining ROIs:**

Create combined V1+V2 mask:
```python
from nilearn import image
import numpy as np

v1 = image.load_img('derivatives/sub-01/roi/..._V1_mask.nii.gz')
v2 = image.load_img('derivatives/sub-01/roi/..._V2_mask.nii.gz')

combined_data = np.logical_or(v1.get_fdata(), v2.get_fdata())
combined_img = image.new_img_like(v1, combined_data.astype(np.int16))
combined_img.to_filename('derivatives/sub-01/roi/..._V1-V2_mask.nii.gz')
```

---

## Success Criteria

**Good Result:**
- Hit rate: >30%
- p-value: <0.10
- Better than brain mask (0.229, p=0.401)

**Excellent Result:**
- Hit rate: >35%
- p-value: <0.05 ✅ Significant!
- Some individual runs with p<0.05

**If No ROI Reaches p<0.05:**
- Move to Step 2: Try FIR model (bh_anal.py)
- Or accept pilot data limitations
- Wait for main experiment data

---

## Expected Timeline

- Step 1-3: 10 minutes (upload, inspect, check)
- Step 4-5: 20 minutes (create ROIs if needed, modify script)
- Step 6-7: 15 minutes per ROI (run analysis)
- Testing all 4 ROIs: ~1.5 hours total

**After this:** You'll know which ROI (if any) gives significant reconstruction!
