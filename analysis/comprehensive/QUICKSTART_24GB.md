# Quick Start Guide: 24GB Memory Configuration

## Memory Allocation Summary

Based on diagnostic results from `diagnose_memory.sh`:

- **ROI Pipeline**: 0.29GB peak
- **Single ROI Baseline**: 5.99GB peak
- **24GB allocation**: Provides **4x safety buffer**

## Array Job Capacity

### Node2 (450GB free)
- 24GB × 15 concurrent = 360GB < 450GB ✓

### Node4 (176GB free)
- 24GB × 7 concurrent = 168GB < 176GB ✓

### Combined (node2,node4)
- Max 15 concurrent safely allocated across both nodes

## Safety Features

All sbatch files include OOM prevention:
- `--no-requeue`: Prevents infinite OOM loops
- `--open-mode=append`: Preserves logs during crashes

---

## How to Run

### 1. Upload Files to Server

```bash
# Upload new 24GB sbatch files
scp analysis/comprehensive/phase0_parallel_mem24.sbatch analysis/comprehensive/phase1to4_sequential_mem24.sbatch haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/comprehensive/
```

### 2. Run Phase 0 (Subject-Parallel Baseline Analysis)

```bash
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind
conda activate nilearn

# Submit Phase 0 array job (all 10 subjects in parallel)
sbatch analysis/comprehensive/phase0_parallel_mem24.sbatch
```

**Expected behavior:**
- Processes all 10 subjects in parallel (max 15 concurrent across node2+node4)
- Each subject: ROI building (0.3GB) + 4 ROIs baseline (6GB each) = ~24GB total
- Time: ~2-3 hours (1.5 min per ROI × 4 ROIs per subject)

### 3. Monitor Job Progress

```bash
# Check job status
squeue -u haba6030

# Example output:
# JOBID  PARTITION  NAME           USER      ST  TIME  NODES  NODELIST(REASON)
# 12345  shared     phase0_m3_24g  haba6030  R   5:23  1      node2
# 12346  shared     phase0_m3_24g  haba6030  R   5:23  1      node4

# Monitor memory usage (replace JOBID)
watch -n 10 'sstat -j JOBID --format=JobID,MaxRSS,AveCPU,NTasks | head -20'

# View live logs
tail -f logs/phase0_m3_24g_sub-01_12345.out
```

### 4. Check Results After Completion

```bash
# Check which subjects completed successfully
grep -r "✓ All ROIs completed successfully" logs/phase0_m3_24g_*.out

# Check for failures
grep -r "✗.*failed" logs/phase0_m3_24g_*.err

# List generated results
ls -lh analysis/phase1_preprocess_decoding/method3_header_mi/results/baseline_decoding/baseline32_method3_header_mi/
```

### 5. Run Phase 1-4 (Group-Level Analysis)

**IMPORTANT**: Only run after Phase 0 completes for all subjects!

```bash
# Submit Phase 1-4 sequential job
sbatch analysis/comprehensive/phase1to4_sequential_mem24.sbatch
```

---

## Troubleshooting

### If jobs fail with OOM:
```bash
# Check actual memory usage
sacct -j JOBID --format=JobID,MaxRSS,Elapsed,State

# If MaxRSS > 20GB, increase to 32GB and resubmit
```

### If jobs are pending:
```bash
# Check node availability
squeue -w node2,node4

# Check your quota
squeue -u haba6030
```

### Cancel jobs if needed:
```bash
# Cancel specific job
scancel JOBID

# Cancel all your jobs
scancel -u haba6030

# Cancel specific array tasks (e.g., only tasks 5-10)
scancel JOBID_5,JOBID_6,JOBID_7,JOBID_8,JOBID_9,JOBID_10
```

---

## Expected Output Structure

After successful completion:

```
analysis/
├── roi_masks/method3_header_mi/
│   ├── sub-01/roi_pipeline/  # ROI masks for each subject
│   │   ├── V1_mask_*.nii.gz
│   │   ├── V2_mask_*.nii.gz
│   │   ├── V3_mask_*.nii.gz
│   │   └── hV4_mask_*.nii.gz
│   ├── sub-02/roi_pipeline/
│   └── ...
│
├── phase1_preprocess_decoding/method3_header_mi/results/baseline_decoding/
│   └── baseline32_method3_header_mi/
│       ├── sub-01/
│       │   ├── V1/
│       │   │   ├── results.json
│       │   │   ├── amplitudes_*.npy
│       │   │   └── figures_*.png
│       │   ├── V2/
│       │   ├── V3/
│       │   └── hV4/
│       ├── sub-02/
│       └── ...
│
└── logs/
    ├── phase0_m3_24g_sub-01_*.out  # stdout logs
    └── phase0_m3_24g_sub-01_*.err  # stderr logs
```

---

## Performance Estimates

### Phase 0 (per subject, 4 ROIs sequential):
- ROI building: ~1.5 min
- V1 baseline: ~1.5 min
- V2 baseline: ~1.5 min
- V3 baseline: ~1.5 min
- hV4 baseline: ~1.5 min
- **Total per subject: ~7.5 min**

### Full Phase 0 (all 10 subjects):
- With 10 concurrent: ~7.5 min (ideal)
- With 15 concurrent: ~5 min (best case, if all subjects start simultaneously)

### Phase 1-4:
- Phase 1 (RDM): ~10 min
- Phase 2 (Procrustes): ~15 min
- Phase 3-4: TBD (depends on implementation)
- **Total: ~30-60 min**

---

## Configuration Files

- **phase0_parallel_mem24.sbatch**: Phase 0 with 24GB, max 15 concurrent
- **phase1to4_sequential_mem24.sbatch**: Phase 1-4 with 24GB

Both files use:
- Dataset: `method3_header_mi`
- Timestamp: `baseline32_method3_header_mi`
- OOM prevention: `--no-requeue`, `--open-mode=append`
- Multi-node: `--nodelist=node2,node4`
