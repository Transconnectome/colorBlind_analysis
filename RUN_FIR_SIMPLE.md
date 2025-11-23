# Quick Start Guide: FIR-Only Analysis

## Overview
This pipeline tests 5 different strategies for using FIR amplitudes directly for color classification, without the two-stage GLM approach.

---

## Step 1: Upload Files to Server

```bash
# From your local machine
scp fir_per_run_simple.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp run_fir_simple.sbatch haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp analyze_fir_simple_results.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
```

---

## Step 2: Run Analysis on Server

```bash
# SSH to server
ssh haba6030@node2

# Navigate to project directory
cd /scratch/connectome/haba6030/colorBlind

# Make sure logs directory exists
mkdir -p logs

# Submit SLURM job (will test all strategies for 4 subjects × 4 ROIs)
sbatch run_fir_simple.sbatch
```

**What this runs:**
- 4 subjects: 01, 02, 03, 04
- 4 ROIs: V1, V2, V3, hV4
- 5 strategies: flatten, average, delay3, delay4, delay5
- Each strategy tested with/without PCA (n=6)
- **Total:** 4 subjects × 4 ROIs × 5 strategies × 2 PCA variants = 160 analyses

---

## Step 3: Monitor Progress

```bash
# Check job status
squeue -u haba6030

# Watch output logs (live update)
tail -f logs/fir_simple_*.out

# Check for errors
tail -f logs/fir_simple_*.err

# See all completed logs
ls -lh logs/fir_simple_*
```

---

## Step 4: Analyze Results (After Jobs Finish)

```bash
# Check what timestamps were created
ls derivatives/fir_simple/sub-01/

# Example: if you see "20250120_143022_V1_flatten/"
# The timestamp is: 20250120_143022

# Run analysis script with your timestamp
python analyze_fir_simple_results.py --timestamp 20250120_143022
```

This will create:
- `derivatives/fir_simple/summary/20250120_143022/`
  - Comparison tables (CSV)
  - Visualization plots (PNG)

---

## Step 5: Download Results

```bash
# From your local machine
# Replace TIMESTAMP with actual timestamp
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/fir_simple/summary/TIMESTAMP ./results_fir_simple/

# Optional: Download all individual results too
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/fir_simple ./all_fir_simple_results/
```

---

## Understanding the Strategies

| Strategy | Description | Features | When to Use |
|----------|-------------|----------|-------------|
| `flatten` | Use all 8 delays concatenated | voxels × 8 | Preserve full temporal info |
| `average` | Average across all delays | voxels | Summarize overall response |
| `delay3` | Use delay 3 only (4.5s) | voxels | Single timepoint, early peak |
| `delay4` | Use delay 4 only (6.0s) | voxels | Single timepoint, typical HRF peak |
| `delay5` | Use delay 5 only (7.5s) | voxels | Single timepoint, late peak |

---

## Expected Runtime

- **Per subject:** ~30-45 minutes (4 ROIs × 5 strategies × 2 PCA variants)
- **All 4 subjects (parallel):** ~30-45 minutes total
- **Analysis script:** ~2-5 minutes

---

## Troubleshooting

### Job fails immediately
```bash
# Check error log
cat logs/fir_simple_JOBID_ARRAYID.err

# Common issues:
# - ROI mask not found → Check derivatives/*/roi_pipeline/
# - Conda environment → Make sure 'nilearn' env exists
# - Memory → Should be fine with 16G
```

### No results found in analysis script
```bash
# List what was actually created
find derivatives/fir_simple -name "summary.json"

# Check if timestamp matches
ls derivatives/fir_simple/sub-01/
```

### Want to test just one subject/ROI first
```bash
# Run directly without SLURM (for testing)
conda activate nilearn

python fir_per_run_simple.py \
    --subject 01 \
    --roi V1 \
    --strategy flatten \
    --timestamp test_run
```

---

## Quick Results Check

```bash
# After jobs complete, quick accuracy check:
grep "Mean accuracy" logs/fir_simple_*.out | sort

# Or for a specific subject:
grep "Mean accuracy" logs/fir_simple_*_0.out  # Array ID 0 = 01
```

---

## Files Created by Pipeline

```
derivatives/fir_simple/
├── sub-01/                       # Subject 01 results
│   ├── TIMESTAMP_V1_flatten/
│   ├── TIMESTAMP_V1_flatten_pca6/
│   ├── TIMESTAMP_V1_average/
│   └── ... (40 total: 4 ROIs × 5 strategies × 2 PCA)
├── sub-02/                       # Subject 02 results
├── sub-03/                       # Subject 03 results
├── sub-04/                       # Subject 04 results
└── summary/
    └── TIMESTAMP/
        ├── all_results.csv
        ├── best_per_subject_roi.csv
        ├── strategy_averages.csv
        ├── strategy_comparison_heatmap.png
        ├── strategy_comparison_bars.png
        ├── strategy_comparison_by_subject.png
        └── strategy_comparison_by_roi.png
```

---

## What to Look For in Results

1. **Best overall strategy:**
   - Check `strategy_comparison_bars.png`
   - Read `best_per_subject_roi.csv`

2. **PCA effect:**
   - Compare with vs. without PCA in heatmap
   - Is PCA helping or hurting?

3. **Temporal information value:**
   - If `flatten` wins → temporal info matters
   - If `average` or single delay wins → temporal info redundant

4. **Optimal delay timing:**
   - If `delay4` (6.0s) wins → validates canonical HRF peak
   - If `delay3` or `delay5` wins → different HRF timing

5. **ROI differences:**
   - Do higher visual areas (hV4) need different strategy than V1?

---

## Next Steps After Results

Based on performance:

1. **If one strategy clearly wins:**
   - Use that strategy for downstream analysis
   - Consider refining it further

2. **If flatten performs best:**
   - Temporal information is important
   - Consider using FIR for final pipeline

3. **If average performs best:**
   - Temporal averaging sufficient
   - Could simplify to canonical HRF approach

4. **If specific delay wins:**
   - Single timepoint sufficient
   - Could use that delay as "optimal delay"

---

*For detailed methodology, see `logs/session_20250120_fir_only.md`*
