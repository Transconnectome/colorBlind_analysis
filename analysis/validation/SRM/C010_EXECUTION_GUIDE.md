# C010 Between-Subject SRM Analysis - Execution Guide

**Date:** 2026-02-09
**Analysis:** HC vs CVD comparison using C010+Procrustes data
**Novel Approach:** Dual pipeline comparing Raw-Averaged vs Procrustes-Averaged SRM

---

## Overview

This analysis adapts the SRM between-subject pipeline to use validated C010+Procrustes preprocessed data, comparing two SRM input methods:

1. **Raw-Averaged SRM**: Raw amplitudes → average runs → SRM
2. **Procrustes-Averaged SRM**: Procrustes-aligned amplitudes → average runs → SRM

**Hypothesis:** Procrustes-aligned data (RDM reliability 0.496 vs 0.042) should yield better shared response models and stronger HC-CVD separation.

---

## Data Requirements

### Input Data
- **Location (Local)**: `analysis/validation/preprocess_Check/full_dataset_C010_with_residuals/`
- **Location (Server)**: `/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010_hrf_analysis/`
- **Structure**:
  ```
  sub-{ID}/
    {ROI}/
      amplitudes_raw.npy          # (6, 8, n_voxels)
      amplitudes_procrustes.npy   # (6, 8, n_voxels)
  ```
- **Subjects**: HC (sub-01~07, n=7), CVD (sub-08~10, n=3)
- **ROIs**: V1, V2, V3, V4
- **SRM features (k)**: V1=4, V2=4, V3=3, V4=4

---

## Execution Methods

### Method 1: Local Execution (Recommended for Testing)

**Step 1: Resource Profiling (Optional but Recommended)**
```bash
cd analysis/validation/SRM
bash test_c010_srm_resources.sh
```

This measures peak memory and CPU usage to verify SLURM settings are appropriate.

**Step 2: Run All ROIs Locally**
```bash
cd analysis/validation/SRM
bash run_c010_between_subject_local.sh
```

**Expected output:**
- Results in `results/c010/TIMESTAMP/`
- 4 ROIs × 2 methods = 8 JSON files + 1 comparison per ROI
- Runtime: ~10-20 minutes per ROI (total ~40-80 minutes)

---

### Method 2: Server Execution (For Full Analysis)

**Step 1: Upload Scripts**
```bash
cd analysis/validation/SRM
bash upload_and_run_c010_srm.sh
```

This will:
1. Upload Python scripts and sbatch file
2. Check node availability (free memory)
3. Verify data paths
4. Prompt for job submission

**Step 2: Monitor Job**
```bash
# Check job status
ssh haba6030@node2 'squeue -u haba6030'

# Monitor logs (real-time)
ssh haba6030@node2 'tail -f /scratch/connectome/haba6030/colorBlind/analysis/validation/SRM/logs/c010_srm_*.out'

# Check all logs
ssh haba6030@node2 'cat /scratch/connectome/haba6030/colorBlind/analysis/validation/SRM/logs/c010_srm_*.out'
```

**Step 3: Download Results**
```bash
# Download all results
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/srm_c010_between_subject/TIMESTAMP/ ./results/c010/

# Or download specific files
scp haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/srm_c010_between_subject/TIMESTAMP/*.json ./results/c010/TIMESTAMP/
```

---

## SLURM Configuration

### Default (Conservative) Settings
```bash
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --array=1-4%2  # Max 2 concurrent tasks
```

**Total peak usage:** 32GB (well within node2's 450GB free)

### When to Adjust Settings

**After running `test_c010_srm_resources.sh`, adjust if needed:**

| Peak Memory | Recommended --mem | Max Concurrent | Total Peak |
|-------------|-------------------|----------------|------------|
| < 8GB       | 16G               | 2              | 32GB       |
| 8-12GB      | 24G               | 2              | 48GB       |
| > 12GB      | 32G               | 2              | 64GB       |

**Always verify node availability before submission:**
```bash
ssh node2 free -h
squeue -w node2
```

---

## Visualization

After analysis completes, generate visualizations:

```bash
cd analysis/validation/SRM

# Specify the results directory
python visualize_srm_c010_between_subject.py --results-dir results/c010/TIMESTAMP/
```

**Outputs** (saved to `results/c010/TIMESTAMP/visualizations/`):
1. `{ROI}_dual_disparity_comparison.png` - Raw vs Procrustes SRM side-by-side
2. `{ROI}_hc_cvd_boxplot.png` - 3-group comparison (HC-HC, CVD-HC, CVD-CVD)
3. `summary_raw_vs_procrustes.png` - Overall method comparison
4. `summary_hc_cvd_separation.png` - Group differences with significance

---

## Expected Outputs

### Per ROI (4 ROIs × 3 files = 12 files)
```
results/c010/TIMESTAMP/
├── V1_raw_srm_results.json
├── V1_procrustes_srm_results.json
├── V1_dual_comparison.json
├── V2_raw_srm_results.json
├── V2_procrustes_srm_results.json
├── V2_dual_comparison.json
... (V3, V4)
```

### Visualizations (8 files)
```
results/c010/TIMESTAMP/visualizations/
├── V1_dual_disparity_comparison.png
├── V1_hc_cvd_boxplot.png
... (V2, V3, V4)
├── summary_raw_vs_procrustes.png
└── summary_hc_cvd_separation.png
```

---

## Validation Checklist

✅ **Before Running:**
- [ ] C010 data exists at expected path
- [ ] BrainIAK installed (`pip install brainiak`)
- [ ] Conda environment activated (`conda activate nilearn`)
- [ ] Resource profiling completed (server only)

✅ **After Running:**
- [ ] All 4 ROIs completed successfully
- [ ] JSON files contain valid results (no NaN values)
- [ ] Both pipelines executed (raw + procrustes)
- [ ] Visualizations generated without errors

✅ **Quality Checks:**
- [ ] HC-CVD disparity larger than HC-HC disparity
- [ ] p-values reasonable (not all significant or all n.s.)
- [ ] Cohen's d effect sizes match expectations (V2, V3 should be large)
- [ ] Procrustes vs Raw comparison shows expected direction

---

## Troubleshooting

### Issue: "C010 data not found"
**Solution:** Verify data path exists:
```bash
# Local
ls analysis/validation/preprocess_Check/full_dataset_C010_with_residuals/sub-01/V1/

# Server
ssh node2 'ls /scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010_hrf_analysis/sub-01/V1/'
```

### Issue: "BrainIAK not available"
**Solution:** Install BrainIAK:
```bash
conda activate nilearn
pip install brainiak
```

### Issue: SLURM job fails with OOM (Out of Memory)
**Solution:**
1. Check actual memory usage in logs
2. Increase `--mem` in sbatch file (e.g., 24G or 32G)
3. Reduce concurrency `--array=1-4%1` (run sequentially)
4. Verify no other jobs are running on the node

### Issue: Different voxel counts between subjects
**Expected:** This is normal! SRM handles heterogeneous voxel counts by mapping to common low-dimensional space (k << v).

### Issue: Visualizations fail with "no display"
**Solution:** Visualization script uses `Agg` backend (non-interactive). Should work on server. If issues persist, run locally after downloading results.

---

## Next Steps

1. **Review Results:** Check `C010_BETWEEN_SUBJECT_RESULTS.md` for interpretation
2. **Compare to Previous:** How do C010 results compare to Baseline32?
3. **Winner Method:** Which averaging method (Raw vs Procrustes) performs better?
4. **Clinical Interpretation:** Do HC-CVD differences replicate with higher quality data?

---

## Contact

For questions or issues:
- Check logs in `logs/c010_srm_*.err` for error messages
- Review plan document for rationale and expected outcomes
- Verify data paths and SLURM configuration match this guide
