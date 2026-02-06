# Server Execution Guide: Between-Subject Procrustes

## Quick Start

### Step 1: Upload Files to Server

```bash
# Upload modified preprocessing script and SLURM batch file (SINGLE LINE - NO LINE BREAKS)
scp analysis/validation/scripts/between_procrustes/fir_reconstruction_no_voxel_filtering.py analysis/validation/scripts/between_procrustes/run_preprocessing_unfiltered.sbatch haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/between_procrustes/
```

### Step 2: Run Preprocessing on Server

```bash
# SSH to server
ssh haba6030@node2

# Navigate to directory
cd /scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/between_procrustes

# Create logs directory
mkdir -p logs

# Submit SLURM job
sbatch run_preprocessing_unfiltered.sbatch

# Monitor progress
squeue -u haba6030
watch -n 10 'squeue -u haba6030'

# Check logs
tail -f logs/baseline_unfilt_*.log

# Check memory usage (in another terminal)
ssh node2 free -h
```

**Expected Output**:
- 9 array jobs (one per subject: sub-01 to sub-10, excluding sub-07)
- Each job processes 4 ROIs (V1, V2, V3, hV4)
- Total: 36 processing tasks (9 subjects × 4 ROIs)

**Expected Runtime**:
- ~2-3 hours per subject-ROI
- Total: ~8-12 hours for all jobs (with 4 concurrent jobs via `%4` limit)

### Step 3: Check Output

```bash
# Check output directory structure
ls -lh /scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/deoblique_v2/results/baseline_decoding/

# Should see: fixed_perRun_unfiltered/
# Inside: sub-01/, sub-02/, ..., sub-10/ (excluding sub-07)
# Inside each subject: V1/, V2/, V3/, hV4/
# Inside each ROI: amplitudes_z.npy, roi_mask.nii.gz, etc.

# Check voxel counts (verify reduced heterogeneity)
for subj in sub-{01..06} sub-{08..10}; do
    for roi in V1 V2 V3 hV4; do
        file="/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/deoblique_v2/results/baseline_decoding/fixed_perRun_unfiltered/$subj/$roi/amplitudes_z.npy"
        if [ -f "$file" ]; then
            python -c "import numpy as np; a=np.load('$file'); print(f'$subj $roi: {a.shape[2]} voxels')"
        fi
    done
done
```

**Expected Voxel Counts (V1)**:
- **Original** (with filtering): 129-429 voxels (wide range)
- **Modified** (no filtering): 200-450 voxels (narrower range, more overlap)

### Step 4: Download Results

```bash
# Download entire unfiltered baseline directory (SINGLE LINE - NO LINE BREAKS)
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/deoblique_v2/results/baseline_decoding/fixed_perRun_unfiltered /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase1_preprocess_decoding/deoblique_v2/results/baseline_decoding/
```

**Expected Download Size**: ~2-5 GB (depending on compression)

### Step 5: Run Between-Subject Analysis Locally

```bash
# Navigate to local directory
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/validation/scripts/between_procrustes

# Activate environment
conda activate nilearn

# Quick test with V1
python run_pipeline_local.py --roi V1 --test-mode

# Full analysis (all ROIs)
./run_local_all.sh
```

## Resource Monitoring

### Memory Profiling (Before Running Full Array Job)

```bash
# Test single subject first with memory profiling
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/between_procrustes

# Run single subject interactively with time profiling
/usr/bin/time -v python fir_reconstruction_no_voxel_filtering.py \
    --subject 01 \
    --roi V1 \
    --dataset deoblique_v2 \
    > test_output.log 2>&1

# Check output
cat test_output.log | grep -E "Maximum resident set size|Percent of CPU"
```

**Key Metrics**:
- **Maximum resident set size**: Peak memory usage (should be <30GB)
- **Percent of CPU**: CPU utilization (target: >80%)

### Monitoring During Execution

```bash
# Terminal 1: Watch queue
watch -n 10 'squeue -u haba6030'

# Terminal 2: Monitor node2 memory
watch -n 10 'ssh node2 free -h'

# Terminal 3: Tail latest log
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/between_procrustes/logs
tail -f baseline_unfilt_*.log
```

## Troubleshooting

### Issue 1: Job Fails with OOM (Out of Memory)

**Symptom**: Log shows "Killed" or "oom-kill"

**Solution**:
```bash
# Increase memory in run_preprocessing_unfiltered.sbatch
#SBATCH --mem=64G  # Increase from 32G

# Reduce concurrent jobs
#SBATCH --array=1-9%2  # Reduce from %4 to %2
```

### Issue 2: Job Stuck in Queue

**Symptom**: `squeue` shows job in `PD` (pending) state

**Diagnosis**:
```bash
# Check job status
squeue -u haba6030 -o "%.18i %.9P %.8j %.8u %.2t %.10M %.6D %R"

# Check reason for pending
scontrol show job <JOB_ID>
```

**Common Reasons**:
- `Resources`: Node is busy
- `Priority`: Other jobs have higher priority
- `QOSMaxCpuPerUserLimit`: Too many CPUs requested

**Solution**:
```bash
# Reduce concurrent jobs
#SBATCH --array=1-9%2

# OR wait for node to free up
```

### Issue 3: Some Subjects Fail

**Symptom**: Logs show errors for specific subjects

**Diagnosis**:
```bash
# Check which subjects completed
for subj in sub-{01..06} sub-{08..10}; do
    file="/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/deoblique_v2/results/baseline_decoding/fixed_perRun_unfiltered/$subj/V1/amplitudes_z.npy"
    if [ -f "$file" ]; then
        echo "✓ $subj"
    else
        echo "✗ $subj"
    fi
done
```

**Solution**:
```bash
# Re-run failed subjects individually
python fir_reconstruction_no_voxel_filtering.py \
    --subject <FAILED_SUBJECT> \
    --roi V1 \
    --dataset deoblique_v2
```

### Issue 4: Wrong QOS Error

**Symptom**: `sbatch: error: Batch job submission failed: Invalid qos specification`

**Solution**: Check SLURM configuration in `run_preprocessing_unfiltered.sbatch`
```bash
# For node2 (CPU jobs):
#SBATCH --qos=shared
#SBATCH --nodelist=node2

# DO NOT use:
#SBATCH --partition=normal  # ❌ Invalid!
#SBATCH --qos=interactive   # ❌ Wrong for batch jobs!
```

## Verification Checklist

After preprocessing completes:

- [ ] All 9 subjects have output directories
- [ ] Each subject has 4 ROI directories (V1, V2, V3, hV4)
- [ ] Each ROI has `amplitudes_z.npy`, `roi_mask.nii.gz`, `results.json`
- [ ] Voxel count heterogeneity is reduced (check with script above)
- [ ] No error messages in logs
- [ ] Download completed successfully
- [ ] Local between-subject analysis runs without errors

## Expected Timeline

| Step | Duration | Notes |
|------|----------|-------|
| Upload files | 1 min | Fast network |
| Submit job | <1 min | Instant |
| Queue wait | 0-30 min | Depends on cluster load |
| Processing | 8-12 hours | 36 jobs with 4 concurrent |
| Download | 10-30 min | Depends on network |
| Local analysis | 20 min | All ROIs |
| **Total** | **9-14 hours** | Mostly unattended |

## Best Practices

1. **Test first**: Run single subject locally before full server job
2. **Profile memory**: Use `/usr/bin/time -v` to check resource usage
3. **Monitor actively**: Watch queue and logs during first hour
4. **Incremental download**: Download one subject first to verify format
5. **Backup originals**: Keep original filtered baseline results

## Contact

If you encounter issues:
1. Check logs in `logs/baseline_unfilt_*.log`
2. Review README.md for troubleshooting
3. Compare with original baseline script for reference
