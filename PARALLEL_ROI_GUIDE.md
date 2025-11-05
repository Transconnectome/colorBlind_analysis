# Parallel ROI Testing Guide

## Why Run in Parallel?

**Sequential (old way):**
- V1: 15 min → V2: 15 min → V3: 15 min → hV4: 15 min = **60 minutes total**

**Parallel (new way):**
- V1, V2, V3, hV4 all at once = **15-20 minutes total** ⚡

**Benefits:**
- 75% time savings
- Independent analyses (no conflicts)
- Separate cache directories for each ROI
- Easy to compare results

---

## Method 1: Simple Parallel Submission (RECOMMENDED)

This is the cleanest approach - uploads one script and submits 4 jobs.

### Step 1: Upload Files

```bash
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis

# Upload the analysis script and parallel submission script
scp naive_analysis.py node2:/scratch/connectome/haba6030/colorBlind/
scp submit_roi_parallel.sh node2:/scratch/connectome/haba6030/colorBlind/
scp check_parallel_results.sh node2:/scratch/connectome/haba6030/colorBlind/
scp test_roi_reconstruction.py node2:/scratch/connectome/haba6030/colorBlind/
```

### Step 2: Submit All Jobs

```bash
ssh node2
cd /scratch/connectome/haba6030/colorBlind

# Make scripts executable
chmod +x submit_roi_parallel.sh
chmod +x check_parallel_results.sh

# Submit all 4 ROI jobs at once
./submit_roi_parallel.sh
```

**Expected output:**
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

==========================================
Submitted 4 jobs
==========================================

Job IDs: 12345 12346 12347 12348

Monitor progress:
  squeue -u $USER
```

### Step 3: Monitor Progress

```bash
# Watch all jobs
squeue -u $USER

# Or use watch (updates every 2 seconds)
watch squeue -u $USER

# Check individual log files
tail -f logs/naive_V2_*.out
tail -f logs/naive_V1_*.out
```

### Step 4: Check Results

```bash
# After all jobs complete (15-20 minutes)
./check_parallel_results.sh
```

**Example output:**
```
==========================================
Results Summary
==========================================

ROI: V1
----------------------------------------
✅ Results found: hrf_test_outputs/cache_V1/reconstruction_results.csv

Run-by-run results:
  Run 1: hit=0.125, p=0.615
  Run 2: hit=0.250, p=0.327
  ...
  Run 6: hit=0.250, p=0.308

  MEAN: hit=0.312, p=0.123 ⚠️  Nearly significant

ROI: V2
----------------------------------------
✅ Results found: hrf_test_outputs/cache_V2/reconstruction_results.csv

Run-by-run results:
  Run 1: hit=0.375, p=0.083
  Run 2: hit=0.500, p=0.021
  ...
  Run 6: hit=0.375, p=0.083

  MEAN: hit=0.375, p=0.042 ✅ SIGNIFICANT!

...
```

---

## Method 2: Manual Parallel (More Control)

If you want more control, you can submit jobs manually:

### Create separate scripts for each ROI:

```bash
# On server
cd /scratch/connectome/haba6030/colorBlind

# Create V1 script
sed 's/ROI_SELECTION = \[.*\]/ROI_SELECTION = ["V1"]/' naive_analysis.py > naive_V1.py

# Create V2 script
sed 's/ROI_SELECTION = \[.*\]/ROI_SELECTION = ["V2"]/' naive_analysis.py > naive_V2.py

# Create V3 script
sed 's/ROI_SELECTION = \[.*\]/ROI_SELECTION = ["V3"]/' naive_analysis.py > naive_V3.py

# Create hV4 script
sed 's/ROI_SELECTION = \[.*\]/ROI_SELECTION = ["hV4"]/' naive_analysis.py > naive_hV4.py
```

### Clear caches:

```bash
rm -f hrf_test_outputs/cache_V1/*
rm -f hrf_test_outputs/cache_V2/*
rm -f hrf_test_outputs/cache_V3/*
rm -f hrf_test_outputs/cache_hV4/*
```

### Submit jobs:

```bash
# Submit V1
sbatch --job-name=naive_V1 --output=logs/naive_V1_%j.out --mem=16G --time=00:30:00 \
  --wrap="python naive_V1.py"

# Submit V2
sbatch --job-name=naive_V2 --output=logs/naive_V2_%j.out --mem=16G --time=00:30:00 \
  --wrap="python naive_V2.py"

# Submit V3
sbatch --job-name=naive_V3 --output=logs/naive_V3_%j.out --mem=16G --time=00:30:00 \
  --wrap="python naive_V3.py"

# Submit hV4
sbatch --job-name=naive_hV4 --output=logs/naive_hV4_%j.out --mem=16G --time=00:30:00 \
  --wrap="python naive_hV4.py"
```

---

## Troubleshooting

### Jobs stuck in queue (PD status)?

**Check queue:**
```bash
squeue -u $USER
```

**If pending:**
- Wait for resources to become available
- Jobs will start automatically when nodes are free

### One job failed?

**Check the log:**
```bash
# Find the failed job log
ls -lt logs/naive_*err | head -1
cat logs/naive_V2_12346.err

# Check output log too
cat logs/naive_V2_12346.out
```

**Resubmit just that ROI:**
```bash
# Clear cache
rm -f hrf_test_outputs/cache_V2/*

# Resubmit
sbatch --job-name=naive_V2 --output=logs/naive_V2_new_%j.out --mem=16G --time=00:30:00 \
  --wrap="sed 's/ROI_SELECTION = \[.*\]/ROI_SELECTION = [\"V2\"]/' naive_analysis.py > tmp.py && python tmp.py && rm tmp.py"
```

### Cache conflicts?

Each ROI uses a separate cache directory:
- V1: `hrf_test_outputs/cache_V1/`
- V2: `hrf_test_outputs/cache_V2/`
- V3: `hrf_test_outputs/cache_V3/`
- hV4: `hrf_test_outputs/cache_hV4/`

**No conflicts should occur!**

### Out of memory?

If jobs fail with OOM (out of memory):

**Increase memory:**
```bash
# Edit submit_roi_parallel.sh
# Change: #SBATCH --mem=16G
# To:     #SBATCH --mem=32G
```

---

## Expected Results

Based on diagnostic data:

| ROI | Voxels | Overlap | Baseline (brain) | Expected | Best Case |
|-----|--------|---------|------------------|----------|-----------|
| V1 | 511 | 37% | 22.9%, p=0.401 | 30-35% | p~0.10 |
| **V2** | **310** | **58%** | 22.9%, p=0.401 | **35-40%** | **p<0.05** ⭐ |
| V3 | 89 | 70% | 22.9%, p=0.401 | 25-30% | p~0.15 |
| hV4 | 55 | 69% | 22.9%, p=0.401 | 20-25% | p~0.25 |

**Most likely outcome:**
- V2 reaches or approaches significance (p~0.05)
- V1 shows improvement but not significant
- V3, hV4 have too few voxels

---

## What to Do After

### If V2 reaches p<0.05: ✅ SUCCESS!

```bash
# Use V2 for all future analyses
# Update naive_analysis.py permanently:
ROI_SELECTION = ["V2"]

# Move to Step 2: CVD correction filter design
```

### If V2 improves but p>0.05: ⚠️ TRY MORE

**Priority order:**
1. Try FIR model (bh_anal.py) - should improve fit quality
2. Optimize lambda (try 0.1, 1.0, 10.0)
3. Combine V1+V2 into single mask

### If all ROIs fail: ❌ NEED ALTERNATIVE

**Options:**
1. Try FIR model (addresses negative R² issue)
2. Check data quality (motion, attention)
3. Wait for main experiment data (better color spacing)

---

## Quick Reference Commands

```bash
# Upload scripts
scp naive_analysis.py submit_roi_parallel.sh check_parallel_results.sh test_roi_reconstruction.py node2:/scratch/connectome/haba6030/colorBlind/

# Submit all jobs
ssh node2
cd /scratch/connectome/haba6030/colorBlind
chmod +x *.sh
./submit_roi_parallel.sh

# Monitor
watch squeue -u $USER

# Check results
./check_parallel_results.sh

# Download results
scp -r node2:/scratch/connectome/haba6030/colorBlind/hrf_test_outputs/cache_V* ./results/
```

---

## Timeline

- Upload: 2 min
- Submit: 1 min
- **Run (parallel): 15-20 min** ⚡
- Check results: 2 min

**Total: ~25 minutes for all 4 ROIs!**

Compare to sequential: 60+ minutes

---

## Files Created

1. `submit_roi_parallel.sh` - Submit all ROI jobs
2. `check_parallel_results.sh` - Check results after completion
3. `run_all_rois_parallel.sh` - Alternative method (creates separate scripts)
4. `PARALLEL_ROI_GUIDE.md` - This guide

**Start with Method 1 (submit_roi_parallel.sh) - it's the simplest!** 🚀
