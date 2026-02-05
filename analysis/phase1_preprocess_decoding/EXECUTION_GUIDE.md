# Grid Factorial Experiment - Execution Guide

## Quick Start

This guide provides **copy-paste commands** for running the 36-condition factorial experiment.

---

## Phase 1: Verify Local Setup ✓ COMPLETED

All implementation files are ready:

```bash
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis

# Verify files exist
ls analysis/phase1_preprocess_decoding/utils/*.py
ls analysis/phase1_preprocess_decoding/fir_reconstruction_with_grid.py
ls analysis/phase1_preprocess_decoding/factorial_config.json
ls analysis/phase1_preprocess_decoding/run_factorial_grid.sbatch
ls analysis/phase1_preprocess_decoding/evaluate_all_conditions.py
```

**Expected output:**
```
utils/__init__.py
utils/crossnobis_ldw.py
utils/grid_resampling.py
utils/procrustes_normalized.py
utils/voxel_tracking.py
fir_reconstruction_with_grid.py
factorial_config.json
run_factorial_grid.sbatch
evaluate_all_conditions.py
```

---

## Phase 2: Upload to Server

### Step 1: Upload all files in one command

```bash
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis

scp analysis/phase1_preprocess_decoding/utils/*.py \
    analysis/phase1_preprocess_decoding/fir_reconstruction_with_grid.py \
    analysis/phase1_preprocess_decoding/factorial_config.json \
    analysis/phase1_preprocess_decoding/run_factorial_grid.sbatch \
    analysis/phase1_preprocess_decoding/evaluate_all_conditions.py \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/
```

### Step 2: Upload utils as a directory (alternative)

```bash
scp -r analysis/phase1_preprocess_decoding/utils \
       analysis/phase1_preprocess_decoding/fir_reconstruction_with_grid.py \
       analysis/phase1_preprocess_decoding/factorial_config.json \
       analysis/phase1_preprocess_decoding/run_factorial_grid.sbatch \
       analysis/phase1_preprocess_decoding/evaluate_all_conditions.py \
       haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/
```

---

## Phase 3: Test on Server (Interactive)

### Step 1: SSH to server

```bash
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind
```

### Step 2: Activate environment

```bash
conda activate nilearn
```

### Step 3: Test single condition (c01 - minimal processing)

```bash
python analysis/phase1_preprocess_decoding/fir_reconstruction_with_grid.py \
    --subject 01 \
    --roi V1 \
    --dataset method3_header_mi \
    --grid-resample no \
    --highpass 0 \
    --motion none \
    --drift none \
    --smooth 0 \
    --normalize-level none \
    --output-dir analysis/phase1_preprocess_decoding/results/grid_factorial/test_c01/sub-01/V1
```

**Expected runtime:** ~5-10 minutes

### Step 4: Verify test output

```bash
ls -lh analysis/phase1_preprocess_decoding/results/grid_factorial/test_c01/sub-01/V1/

# Expected files:
#   amplitudes_raw.npy
#   amplitudes_z.npy
#   voxel_coords.npy
#   grid_index.npy
#   qc.json
#   results.json
```

### Step 5: Test grid resampling (c12 - Baseline32-like with resampling)

```bash
python analysis/phase1_preprocess_decoding/fir_reconstruction_with_grid.py \
    --subject 01 \
    --roi V1 \
    --dataset method3_header_mi \
    --grid-resample yes \
    --highpass 0.01 \
    --motion cosine \
    --drift per_run \
    --smooth 0 \
    --normalize-level none \
    --output-dir analysis/phase1_preprocess_decoding/results/grid_factorial/test_c12/sub-01/V1
```

**Note:** `--motion cosine` = motion parameters + cosine drift (Baseline32 standard)

**Check for grid resampling messages in output:**
```
Grid resampling: Using run 1 as reference
  Reference shape: (...)
  Mask resampled and masker reinitialized
Grid resampling: Resampling run 2 to reference grid...
  Resampled: affine_match=True, shape_match=True
```

### Step 6: Monitor resource usage (optional)

```bash
# Profile single condition for memory/CPU
/usr/bin/time -v python analysis/phase1_preprocess_decoding/fir_reconstruction_with_grid.py \
    --subject 01 \
    --roi V1 \
    --dataset method3_header_mi \
    --grid-resample yes \
    --highpass 0.01 \
    --motion rp+cosine \
    --drift per_run \
    --output-dir analysis/phase1_preprocess_decoding/results/grid_factorial/profile_test/sub-01/V1 \
    > profile.log 2>&1

# Check peak memory usage
grep "Maximum resident set size" profile.log
# Typical: 8-12 GB
```

---

## Phase 4: Submit Full Array Job (36 Conditions)

### Step 1: Create logs directory

```bash
mkdir -p /scratch/connectome/haba6030/colorBlind/logs
```

### Step 2: Submit array job

```bash
sbatch analysis/phase1_preprocess_decoding/run_factorial_grid.sbatch
```

**Expected output:**
```
Submitted batch job 123456
```

### Step 3: Monitor job progress

```bash
# Check queue status
squeue -u haba6030

# Watch specific job
watch -n 10 'squeue -u haba6030'

# Count completed conditions
watch -n 60 'ls analysis/phase1_preprocess_decoding/results/grid_factorial/ | grep "^c[0-9]" | wc -l'
# Expected: 36 when complete

# Check for failures
sacct -j JOBID --format=JobID,State,ExitCode | grep -v COMPLETED

# View live output (replace JOBID and TASKID)
tail -f logs/grid_factorial_JOBID_TASKID.out

# View errors
tail -f logs/grid_factorial_JOBID_TASKID.err
```

### Step 4: Check resource usage after completion

```bash
# Summary of all tasks
sacct -j JOBID --format=JobID,Elapsed,MaxRSS,State -X

# Detailed stats for specific task
sacct -j JOBID_TASKID --format=JobID,MaxRSS,Elapsed,State,ExitCode

# Average memory usage
sacct -j JOBID --format=MaxRSS -X | tail -n +3 | awk '{sum+=$1; n++} END {print "Average MaxRSS:", sum/n/1024, "MB"}'
```

**Expected values:**
- **Elapsed time:** 15-25 minutes per condition
- **MaxRSS:** 8-14 GB
- **ExitCode:** 0:0 (success)

### Step 5: Verify all 36 conditions completed

```bash
# List all conditions
ls analysis/phase1_preprocess_decoding/results/grid_factorial/ | grep "^c[0-9]" | sort

# Count outputs
ls analysis/phase1_preprocess_decoding/results/grid_factorial/c*/sub-01/V1/amplitudes_raw.npy | wc -l
# Expected: 36

# Check for missing conditions
for i in $(seq -f "%02g" 1 36); do
    dir="analysis/phase1_preprocess_decoding/results/grid_factorial/c${i}_*/sub-01/V1"
    if ! ls $dir/amplitudes_raw.npy 2>/dev/null; then
        echo "Missing: c${i}"
    fi
done
```

---

## Phase 5: Download Results (Local)

### Download all results

```bash
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis

# Download entire results directory
scp -r haba6030@node3:/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/results/grid_factorial \
    analysis/phase1_preprocess_decoding/results/
```

**Expected download size:** ~1-2 GB (depending on n_voxels)

**Download time:** 5-15 minutes (depending on network)

---

## Phase 6: Evaluate Results (Local)

### Step 1: Run evaluation pipeline

```bash
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase1_preprocess_decoding

conda activate nilearn  # Or your Python environment with numpy, scipy, scikit-learn

python evaluate_all_conditions.py
```

**Expected output:**
```
================================================================================
Grid Resampling Factorial Evaluation
================================================================================
Results directory: results/grid_factorial
Subject: 01
ROI: V1

Found 36 conditions

Evaluating: c01_no_hp0_none_none
  Loading data from results/grid_factorial/c01_no_hp0_none_none/sub-01/V1
    Shape: (6, 8, 1234)
    Computing RDM correlation...
    Computing RDM crossnobis...
    Computing decoding accuracy...
    Computing Procrustes disparity...
  Results:
    RDM correlation:  0.4532
    RDM crossnobis:   0.4532
    Shrinkage:        0.3245
    Decoding:         0.4896
    Procrustes:       1.2345
    Voxels:           1234

...

================================================================================
✅ Evaluation complete
   Successful: 36 / 36
   Failed: 0

Saved to: results/grid_factorial/evaluation_summary.json
================================================================================

Summary Statistics:

rdm_correlation:
  Mean:   0.5234
  Median: 0.5123
  Std:    0.0892
  Min:    0.3456
  Max:    0.6789

...
```

### Step 2: Visualize results

```python
import json
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

# Load results
with open('results/grid_factorial/evaluation_summary.json') as f:
    results = json.load(f)

# Convert to DataFrame
df = pd.DataFrame.from_dict(results, orient='index')

# Parse condition names into factors
df['grid_resample'] = df.index.str.extract(r'_(yes|no)_')[0]
df['highpass'] = df.index.str.extract(r'_hp(\d+)_')[0]
df['motion'] = df.index.str.extract(r'_(none|rp|rpcosine)_')[0]
df['drift'] = df.index.str.extract(r'_(none|perrun|2ndlevel)$')[0]

# Create visualization
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Factor effects on RDM correlation
sns.boxplot(x='grid_resample', y='rdm_correlation', data=df, ax=axes[0,0])
axes[0,0].set_title('Effect of Grid Resampling', fontsize=12, fontweight='bold')
axes[0,0].set_ylabel('RDM Correlation')

sns.boxplot(x='highpass', y='rdm_correlation', data=df, ax=axes[0,1])
axes[0,1].set_title('Effect of Highpass Filter', fontsize=12, fontweight='bold')
axes[0,1].set_ylabel('RDM Correlation')

sns.boxplot(x='motion', y='rdm_correlation', data=df, ax=axes[1,0])
axes[1,0].set_title('Effect of Motion Confounds', fontsize=12, fontweight='bold')
axes[1,0].set_ylabel('RDM Correlation')

sns.boxplot(x='drift', y='rdm_correlation', data=df, ax=axes[1,1])
axes[1,1].set_title('Effect of Drift Modeling', fontsize=12, fontweight='bold')
axes[1,1].set_ylabel('RDM Correlation')

plt.tight_layout()
plt.savefig('results/grid_factorial/factor_effects_rdm_correlation.png', dpi=150)
print("Saved: results/grid_factorial/factor_effects_rdm_correlation.png")

# Find best condition
best_idx = df['rdm_crossnobis'].idxmax()
print(f"\nBest condition (by RDM crossnobis): {best_idx}")
print(df.loc[best_idx])

# Compare grid resampling effect
print("\n" + "="*80)
print("Grid Resampling Effect:")
print("="*80)
for metric in ['rdm_correlation', 'rdm_crossnobis', 'decoding_accuracy', 'procrustes_disparity']:
    no_resample = df[df['grid_resample'] == 'no'][metric].mean()
    yes_resample = df[df['grid_resample'] == 'yes'][metric].mean()
    diff = yes_resample - no_resample

    print(f"\n{metric}:")
    print(f"  no:  {no_resample:.4f}")
    print(f"  yes: {yes_resample:.4f}")
    print(f"  Δ:   {diff:+.4f}")
    
```

---

## Troubleshooting

### Problem: Array job fails immediately

**Check:**
```bash
# View error log
cat logs/grid_factorial_JOBID_1.err

# Common issues:
# - Config file not found → verify upload
# - Python not found → check conda activate
# - Import error → verify utils/ directory uploaded
```

### Problem: Some conditions fail (exit code != 0)

**Diagnose:**
```bash
# Find failed tasks
sacct -j JOBID --format=JobID,State,ExitCode | grep FAILED

# Check specific task error
cat logs/grid_factorial_JOBID_TASKID.err
```

**Common causes:**
- **Exit 137:** Out of memory → increase `--mem` in sbatch
- **Exit 1:** Python error → check error log for traceback
- **Exit 2:** File not found → verify dataset paths

### Problem: Grid resampling not working

**Check output logs for:**
```
Grid resampling: Using run 1 as reference
  Reference shape: (...)
```

If missing, verify:
- `--grid-resample yes` in command
- `GRID_RESAMPLE` variable set correctly
- No errors during mask resampling

---

## Expected Timeline

| Phase | Duration | Wall Time |
|-------|----------|-----------|
| Local setup | 0 min | ✓ Done |
| Upload to server | 2 min | 2 min |
| Interactive testing | 20 min | 22 min |
| Array job (36 tasks) | 15-25 min/task | **12-18 hours** |
| Download results | 10 min | 12-18 hr 10 min |
| Evaluation | 30-60 min | 12-18 hr 40 min |
| Visualization | 30 min | 12-19 hr 10 min |

**Total active work:** ~2 hours (excluding array job wait time)
**Total wall time:** ~12-19 hours (including parallelized array job)

---

## Success Checklist

- [ ] All 36 condition directories exist
- [ ] All amplitudes_raw.npy files present (36 files)
- [ ] All qc.json files present (36 files)
- [ ] evaluation_summary.json generated
- [ ] At least 1 condition achieves RDM > 0.6
- [ ] Grid resampling conditions show voxel_correspondence=True
- [ ] No NaN/Inf values in any metric
- [ ] Factor effect visualizations created

---

## Next Steps After Completion

1. **Identify best configuration** from evaluation results
2. **Run best config on all subjects** (sub-01 through sub-10)
3. **Test on other ROIs** (V2, V3, V4)
4. **Document production pipeline** with recommended settings
5. **Update CLAUDE.md** with new baseline settings

---

**Ready to execute!** Start with Phase 2 (Upload to Server).
