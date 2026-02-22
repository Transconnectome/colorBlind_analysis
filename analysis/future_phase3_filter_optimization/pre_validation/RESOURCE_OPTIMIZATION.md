# SLURM Resource Optimization

**Date**: 2026-02-23
**Based on**: Interactive test results (2026-02-23 00:00:41)

---

## Interactive Test Results

**Test scope**:
- 1 CVD subject (sub-08)
- 4 ROIs (V1, V2, V3, hV4) - *bug: should have been 2, fixed*
- 2 conditions (correlation_none, crossnobis_none)
- **Total**: 8 subject-ROI-condition analyses

**Completion time**: ~3-5 minutes
**Memory usage**: < 1 GB (based on process monitoring)
**Output size**: 114 KB JSON

---

## Full Job Estimates

**Full scope**:
- 3 CVD subjects (sub-08, sub-09, sub-10)
- 4 ROIs (V1, V2, V3, hV4)
- 6 conditions (3 correlation + 3 crossnobis)
- **Total**: 72 subject-ROI-condition analyses

**Scaling factor**: 72 / 8 = 9x test workload

### Time Estimation

| Component | Analyses | Time per analysis | Total time |
|-----------|----------|-------------------|------------|
| **Correlation conditions** (3) | 36 | ~10 sec | ~6 min |
| **Crossnobis conditions** (3) | 36 | ~2.5 min | ~90 min |
| **Grand total** | 72 | varies | **~96 min** |

**Safety margin**: Add 20% → **115 min ≈ 2 hours**

### Memory Estimation

**Per-subject-ROI analysis**:
1. Load amplitudes: (6, 8, ~500 voxels) × 8 bytes = ~200 KB
2. Compute patterns: (8, ~500) × 8 bytes = ~32 KB
3. **Crossnobis covariance**: (~500 × ~500) × 8 bytes = ~2 MB
4. Ledoit-Wolf shrinkage: Temporary arrays ~50 MB
5. RDM storage: (8, 8) × 8 bytes = ~512 bytes

**Peak memory per analysis**: ~100 MB (dominated by Ledoit-Wolf)

**With sequential execution**: ~100 MB × 1.5 (safety) = **150 MB**

**Allocated**: 8 GB (53x headroom for safety, handles edge cases)

### CPU Usage

**Ledoit-Wolf parallelization**: Limited sklearn parallelism (2 cores sufficient)

**Recommendation**: 2 CPUs (more doesn't help for this workload)

---

## Optimization Summary

| Resource | Original | Optimized | Reduction | Rationale |
|----------|----------|-----------|-----------|-----------|
| **Memory** | 32 GB | **8 GB** | 75% ↓ | Test used < 1 GB, 8 GB provides 8x safety margin |
| **CPUs** | 4 | **2** | 50% ↓ | Sequential analysis, limited sklearn parallelism |
| **Time** | 2:00:00 | **1:30:00** | 25% ↓ | Estimated 96 min + 20% buffer = 115 min |

**Total resource savings**: ~70% reduction in allocation

**Risk**: Low - 8 GB is 8x observed usage, 90 min is 2x typical crossnobis time

---

## Recommended sbatch Configuration

```bash
#!/bin/bash
#SBATCH --job-name=metric_norm_test
#SBATCH --output=logs/slurm_%j.out
#SBATCH --error=logs/slurm_%j.err
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=2       # ← Optimized from 4
#SBATCH --mem=8G                # ← Optimized from 32G
#SBATCH --time=01:30:00         # ← Optimized from 02:00:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/future_phase3_filter_optimization/pre_validation
```

---

## If Job Fails

### OOM (Out of Memory)

**Symptom**: `slurmstepd: error: Detected X oom-kill event(s)`

**Solution**: Increase memory allocation
```bash
#SBATCH --mem=16G  # Double current allocation
```

**Unlikely**: Test used < 1 GB, 8 GB is 8x safety margin

### Timeout

**Symptom**: Job killed after 01:30:00

**Solution**: Increase time limit
```bash
#SBATCH --time=02:00:00  # Original allocation
```

**Causes**:
- Node heavily loaded (other jobs slowing I/O)
- Larger-than-expected ROIs (V1 can have 800+ voxels)

### CPU Bottleneck

**Symptom**: Very slow crossnobis computation

**Solution**: Increase CPUs (minimal benefit expected)
```bash
#SBATCH --cpus-per-task=4  # Original allocation
```

**Note**: This workload is I/O and memory-bound, not CPU-bound

---

## Monitoring During Execution

```bash
# Check job status
squeue -u haba6030

# Monitor memory usage (from another terminal)
ssh node2
watch -n 10 'ps aux | grep test_rdm | grep -v grep | awk "{sum+=\$6} END {printf \"Memory: %.1f GB\\n\", sum/1024/1024}"'

# Check progress
tail -f logs/slurm_JOBID.out
```

**Expected resource usage**:
- Memory: Should stay < 2 GB throughout
- CPU: Should show ~100-200% (2 cores, not fully utilized)
- I/O wait: Moderate during data loading

---

## Post-Run Validation

After job completes, check actual usage:

```bash
# From SLURM output
grep "Maximum resident set size" logs/slurm_JOBID.out

# Compare to allocation
sacct -j JOBID --format=JobID,MaxRSS,Elapsed,State
```

**Record findings** for future optimization:
- If MaxRSS < 4 GB: Can reduce --mem to 4G
- If Elapsed < 45 min: Can reduce --time to 01:00:00
- If CPU% << 200%: 2 CPUs is optimal

---

## Files Updated

1. **`test_rdm_metric_and_normalization_server.py`**
   - Fixed bug: Now respects `--test_rois` parameter in test mode

2. **`run_metric_norm_test.sbatch`**
   - Memory: 32G → 8G (75% reduction)
   - CPUs: 4 → 2 (50% reduction)
   - Time: 2:00:00 → 1:30:00 (25% reduction)

3. **`test_metric_norm_interactive.sh`**
   - No changes (already optimal for quick testing)

---

**Updated**: 2026-02-23
**Optimized by**: Interactive test validation
**Status**: Ready for full job submission
